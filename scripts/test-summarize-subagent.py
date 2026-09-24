#!/usr/bin/env python3
"""`summarize-subagent.py` の回帰テスト。

    python3 scripts/test-summarize-subagent.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）。
`scripts/` ではない——**`dev-loop` はどのリポジトリでも使えるスキル**なので
（`test-find-cycle.py` と同じ形）。

**このテストは実環境を読まない。** 本体の既定の探し先は `~/.claude/projects` なので、
**毎回 `--projects-dir` かパスでテンポラリの合成 transcript を渡し**、
渡す先がテンポラリの中であることを `assert_in_tmp` で担保する。
**既定のまま走らせると、実物の transcript に当たって通ってしまう**——通っても判別の証明にならない。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。

**主張とテストを 1 対 1 にする。** 本体の docstring の「守る」の行数だけ変異を当てる
（**テスト自身に数えさせる**）。
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "summarize-subagent.py"
TMP = Path(tempfile.gettempdir()).resolve()
LONG_CMD = "echo " + "x" * 200
TOOL_OUTPUT = "TOOL_OUTPUT_MUST_NOT_APPEAR"

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def assert_in_tmp(p: Path) -> None:
    resolved = p.resolve()
    assert resolved.is_relative_to(TMP), f"テンポラリの外を対象にしている: {resolved}"
    assert not resolved.is_relative_to((Path.home() / ".claude").resolve()), "実環境を対象にしている"


def ts(sec: int) -> str:
    return f"2026-09-23T03:{sec // 60:02d}:{sec % 60:02d}.000Z"


def assistant(sec, blocks, stop=None):
    return {"type": "assistant", "timestamp": ts(sec),
            "message": {"role": "assistant", "content": blocks, "stop_reason": stop}}


def tool_use(sec, tid, command, **extra):
    return assistant(sec, [{"type": "tool_use", "id": tid, "name": "Bash",
                            "input": {"command": command, **extra}}], stop="tool_use")


def tool_result(sec, tid, tur=None):
    return {"type": "user", "timestamp": ts(sec), "toolUseResult": tur or {"stdout": TOOL_OUTPUT},
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tid, "content": TOOL_OUTPUT}]}}


def notification(sec, task_id, status="completed"):
    body = (f"<task-notification>\n<task-id>{task_id}</task-id>\n<tool-use-id>x</tool-use-id>\n"
            f"<status>{status}</status>\n<summary>done</summary>\n</task-notification>")
    return {"type": "attachment", "timestamp": ts(sec),
            "attachment": {"type": "queued_command", "prompt": body}}


def write(path: Path, rows) -> Path:
    assert_in_tmp(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return path


def stalled_rows():
    """#168 の形: 前景 1 本・指定 1 本（完了あり）・自動 1 本（完了なし）・報告を書き終えている。"""
    return [
        tool_use(0, "t1", "git status"),
        tool_result(1, "t1"),
        tool_use(10, "t2", "pytest -q", run_in_background=True),
        tool_result(11, "t2", {"stdout": "", "backgroundTaskId": "bspec"}),
        tool_use(20, "t3", "find / -maxdepth 6 -iname pkg"),
        tool_result(140, "t3", {"stdout": "", "backgroundTaskId": "bauto", "timedOutAfterMs": 120000}),
        notification(200, "bspec"),
        tool_use(210, "t4", LONG_CMD),
        tool_result(211, "t4"),
        assistant(300, [{"type": "text", "text": "## 検証結果\n反証 0 件"}], stop="end_turn"),
    ]


def midway_rows():
    """途中の text（道具の前置き）で終わっていない周: end_turn の text が無い。"""
    return [
        assistant(0, [{"type": "text", "text": "まず差分を見ます"}]),
        tool_use(1, "t1", "git diff"),
        tool_result(2, "t1"),
        assistant(3, [{"type": "text", "text": "次にテストを回します"}]),
    ]


def run(script: Path, *args) -> tuple[int, str]:
    for a in args:
        if a.startswith("/"):
            assert_in_tmp(Path(a))
    proc = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True,
                          check=False, cwd=TMP)
    return proc.returncode, proc.stdout + proc.stderr


def observe(script: Path, fixtures: dict) -> dict:
    rc, out = run(script, str(fixtures["stalled"]))
    auto_line = next((l for l in out.splitlines() if l.strip().startswith("bauto")), "")
    spec_line = next((l for l in out.splitlines() if l.strip().startswith("bspec")), "")
    rc_mid, out_mid = run(script, str(fixtures["midway"]))
    rc_amb, out_amb = run(script, "dup", "--projects-dir", str(fixtures["projects"]))
    rc_one, out_one = run(script, "agent-solo", "--projects-dir", str(fixtures["projects"]))
    return {
        "rc": rc,
        "バックグラウンドの本数": next((l for l in out.splitlines() if l.startswith("バックグラウンドに回った")), ""),
        "自動の行": ("自動" in auto_line, "120 秒" in auto_line),
        "指定の行": "指定" in spec_line,
        "自動の完了": "完了の記録なし" in auto_line,
        "指定の完了": "完了の記録あり（completed" in spec_line,
        "報告": "書き終えた記録がある" in out,
        "途中の周": ("書き終えた記録が無い" in out_mid, rc_mid),
        "曖昧な ID": (rc_amb, "2 件以上" in out_amb),
        "1 件の ID": (rc_one, "書き終えた記録がある" in out_one),
        "長いコマンドの全文": LONG_CMD in out,
        "道具の出力": TOOL_OUTPUT in out,
        "最長の行": max(len(l) for l in out.splitlines()),
    }


MUTATIONS = {
    # 守る 1: 判定は結果の backgroundTaskId で行う（入力フラグで代用すると自動を取りこぼす）
    "入力フラグで判定する": (
        '                if isinstance(tur, dict) and tur.get("backgroundTaskId"):',
        '                if isinstance(tur, dict) and (c["input"] or {}).get("run_in_background"):'),
    # 守る 2: 指定と自動を区別する
    "全部を指定と出す": (
        '    return "指定" if inp.get("run_in_background") else "自動"',
        '    return "指定"'),
    # 守る 3: 記録が無いものを完了に数えない
    "記録が無くても完了とする": (
        '        rec = done.get(c["bg"])',
        '        rec = done.get(c["bg"]) or ("completed", None)'),
    # 守る 4: end_turn の text だけを報告と読む
    "途中の text を報告と読む": (
        '                if msg.get("stop_reason") == "end_turn":',
        '                if True:'),
    # 守る 5: 2 件以上当たったら選ばない
    "先頭の 1 件を選ぶ": (
        "    if len(hits) > 1:",
        "    if False:"),
    # 守る 6: コマンドを短く切る
    "コマンドを切らない": (
        '    return s if len(s) <= CMD_WIDTH else s[: CMD_WIDTH - 1] + "…"',
        "    return s"),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp).resolve()
        assert_in_tmp(tmpdir)
        projects = tmpdir / "projects"
        fixtures = {
            "stalled": write(tmpdir / "stalled" / "agent-stalled.jsonl", stalled_rows()),
            "midway": write(tmpdir / "midway" / "agent-midway.jsonl", midway_rows()),
            "projects": projects,
        }
        write(projects / "p1" / "s1" / "subagents" / "agent-dup.jsonl", stalled_rows())
        write(projects / "p2" / "s2" / "subagents" / "agent-dup.jsonl", stalled_rows())
        write(projects / "p1" / "s1" / "subagents" / "agent-solo.jsonl", stalled_rows())

        correct = observe(SCRIPT, fixtures)

        print("#168 の形（前景・指定・自動）を判別する")
        check("rc=0", correct["rc"] == 0)
        check("バックグラウンドは 2 本（指定 1 ／ 自動 1）",
              "2 本（指定 1 ／ 自動 1）" in correct["バックグラウンドの本数"])
        check("入力に無いのに回ったものを「自動」と出し、打ち切りの秒数を添える", correct["自動の行"] == (True, True))
        check("run_in_background を指定したものを「指定」と出す", correct["指定の行"])

        print("\n完了の記録を突き合わせる")
        check("通知のある task-id は「完了の記録あり」", correct["指定の完了"])
        check("通知の無い task-id は「完了の記録なし」", correct["自動の完了"])

        print("\n報告を書き終えたかは end_turn の text で言う")
        check("end_turn の text があれば「書き終えた記録がある」", correct["報告"])
        check("前置きの text しか無ければ「書き終えた記録が無い」", correct["途中の周"] == (True, 0))

        print("\nID の解決")
        check("2 件以上当たったら rc=2 で選ばない", correct["曖昧な ID"] == (2, True))
        check("1 件なら agent- 接頭辞つきでも解決する", correct["1 件の ID"] == (0, True))
        rc, _ = run(SCRIPT, "none", "--projects-dir", str(projects))
        check("見つからなければ rc=2", rc == 2)
        empty = write(tmpdir / "empty" / "agent-empty.jsonl", [])
        rc, _ = run(SCRIPT, str(empty))
        check("JSON の行が無ければ rc=2", rc == 2)

        print("\n集計だけを出す")
        check("長いコマンドの全文を出さない", not correct["長いコマンドの全文"])
        check("道具の出力を出さない", not correct["道具の出力"])
        check(f"最長の行が 200 文字未満（実測 {correct['最長の行']}）", correct["最長の行"] < 200)

        print("\n変異テスト（壊したのに緑なら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}", False)
                continue
            d = tmpdir / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "summarize-subagent.py"
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            check(f"変異を殺せる: {name}", observe(broken, fixtures) != correct)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [l for l in body.splitlines() if l.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件",
              len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_in_tmp(Path.home() / ".claude" / "projects")
        except AssertionError:
            check("~/.claude/projects を対象にすると落ちる", True)
        else:
            check("~/.claude/projects を対象にすると落ちる", False)

    if failures:
        print(f"\n{len(failures)} 件失敗")
        return 1
    print("\nすべて通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
