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

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したら check が 1 つ以上落ちること**を見る
（**観測の差ではなく、落ちた check で数える**——差があるだけでは、その主張を守っている証明にならない）。

**主張とテストを 1 対 1 にする。** 本体の docstring の「守る」の行数だけ変異を当てる
（**テスト自身に数えさせる**）。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "summarize-subagent.py"
TMP = Path(tempfile.gettempdir()).resolve()
TOOL_OUTPUT = "TOOL_OUTPUT_MUST_NOT_APPEAR"
FIND_CMD = "cd /work/" + "y" * 80 + " && find / -name pkg 2>/dev/null | head -5"
REPORT = "## 検証結果\nREPORT_BODY 反証 0 件"
HANDBACK = "HANDBACK_BODY"
PREAMBLE = "まず差分を見ます"


def assert_in_tmp(p: Path) -> None:
    resolved = p.resolve()
    assert resolved.is_relative_to(TMP), f"テンポラリの外を対象にしている: {resolved}"
    assert not resolved.is_relative_to((Path.home() / ".claude").resolve()), "実環境を対象にしている"


def ts(sec: int) -> str:
    return f"2026-09-23T03:{sec // 60:02d}:{sec % 60:02d}.000Z"


def assistant(sec, blocks, stop=None):
    return {"type": "assistant", "timestamp": ts(sec),
            "message": {"role": "assistant", "content": blocks, "stop_reason": stop}}


def tool_use(sec, tid, command, name="Bash", **extra):
    inp = {"command": command, **extra} if name == "Bash" else extra
    return assistant(sec, [{"type": "tool_use", "id": tid, "name": name, "input": inp}], stop="tool_use")


def tool_result(sec, tid, tur=None, content=TOOL_OUTPUT):
    return {"type": "user", "timestamp": ts(sec), "toolUseResult": tur or {"stdout": content},
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tid, "content": content}]}}


def notice(task_id, status):
    return (f"<task-notification>\n<task-id>{task_id}</task-id>\n<tool-use-id>x</tool-use-id>\n"
            f"<status>{status}</status>\n<summary>done</summary>\n</task-notification>")


def write(path: Path, rows) -> Path:
    assert_in_tmp(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return path


def stalled_rows():
    """#168 の形を全部入れた 1 体分。"""
    return [
        tool_use(0, "t1", "git status"),
        tool_result(1, "t1"),
        # 指定して回した → 完了の通知あり
        tool_use(10, "t2", "pytest -q", run_in_background=True),
        tool_result(11, "t2", {"stdout": "", "backgroundTaskId": "bspec"}),
        # 自動で回った（timedOutAfterMs あり）。止めている本体はコマンドの途中にある
        tool_use(20, "t3", FIND_CMD),
        tool_result(140, "t3", {"stdout": "", "backgroundTaskId": "bauto", "timedOutAfterMs": 120000}),
        # 自動で回った（timedOutAfterMs が無い形）
        tool_use(150, "t4", "sleep 999"),
        tool_result(151, "t4", {"stdout": "", "backgroundTaskId": "bauto2"}),
        # 指定して回した → 同じ通知の中で別の status を持つ
        tool_use(160, "t5", "make long", run_in_background=True),
        tool_result(161, "t5", {"stdout": "", "backgroundTaskId": "bkill"}),
        # 1 つの attachment に通知が 2 つ
        {"type": "attachment", "timestamp": ts(200),
         "attachment": {"type": "queued_command", "prompt": notice("bspec", "completed") + notice("bkill", "killed")}},
        # 道具の結果に、bauto の通知の文面が写り込んでいる（出力ファイルを cat した）
        tool_use(210, "t6", "cat /tmp/tasks/bauto.output"),
        tool_result(211, "t6", content=notice("bauto", "completed")),
        assistant(220, [{"type": "text", "text": PREAMBLE}]),
        tool_use(221, "t7", "git diff"),
        tool_result(222, "t7"),
        # 最後の報告の stop_reason が end_turn ではない（実測で 46 件ある形）
        assistant(300, [{"type": "text", "text": REPORT}], stop=None),
        tool_use(310, "t8", None, name="SendMessage", to="team-lead", message=HANDBACK),
        tool_result(311, "t8"),
    ]


def run(script: Path, *args) -> tuple[int, str]:
    for a in args:
        if a.startswith("/"):
            assert_in_tmp(Path(a))
    proc = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True,
                          check=False, cwd=TMP)
    return proc.returncode, proc.stdout + proc.stderr


def line_of(out: str, head: str) -> str:
    return next((l for l in out.splitlines() if l.strip().startswith(head)), "")


def evaluate(script: Path, fx: dict) -> list[tuple[str, bool]]:
    """(check の名前, 通ったか) を並べる。本体にも変異にも同じものを当てる。"""
    rc, out = run(script, str(fx["stalled"]))
    auto, auto2, spec, kill = (line_of(out, h) for h in ("bauto ", "bauto2", "bspec", "bkill"))
    says = [l for l in out.splitlines() if "文字  " in l]
    p = str(fx["projects"])
    checks = [
        ("rc=0", rc == 0),
        ("バックグラウンドは 4 本（指定 2 ／ 自動 2）", "4 本（指定 2 ／ 自動 2）" in out),
        ("入力に無いのに回ったもの（timedOutAfterMs あり）を「自動」と出す", " 自動" in auto),
        ("timedOutAfterMs が無くても、入力に指定が無ければ「自動」と出す", " 自動" in auto2),
        ("指定したものを「指定」と出す", " 指定" in spec),
        ("通知のある task-id は「完了の記録あり」", "完了の記録あり（completed" in spec),
        ("道具の結果に写った通知は完了に数えない", "完了の記録なし" in auto),
        ("同じ行の 2 つ目の通知も、自分の status で拾う", "完了の記録あり（killed" in kill),
        ("stop_reason が end_turn でない報告も並べる", any("REPORT_BODY" in l for l in says)),
        ("前置きの text も並べる（判定しない）", any(PREAMBLE in l for l in says)),
        ("SendMessage の引き渡しを並べる", any("引き渡し" in l and HANDBACK in l for l in says)),
        ("判定しないことを明示する", "判定しない" in out),
        ("コマンドの途中の find / に印を付ける", "[find /]" in auto),
        ("長いコマンドの全文を出さない", FIND_CMD not in out),
        ("コマンドの尾を出す", "| head -5" in auto),
        ("道具の出力を出さない", TOOL_OUTPUT not in out),
    ]
    rc, out = run(script, str(fx["stalled"]), "--text", "2")
    checks += [
        ("--text 2 は報告の全文を出す", rc == 0 and "REPORT_BODY" in out),
        ("--text は指定した 1 件だけを出す", PREAMBLE not in out and HANDBACK not in out),
        ("--text の番号が範囲外なら rc=2", run(script, str(fx["stalled"]), "--text", "99")[0] == 2),
    ]
    checks += [
        ("同じ名前が 2 件あれば rc=2 で選ばない",
         (lambda r: r[0] == 2 and "2 件以上" in r[1])(run(script, "verifier", "--projects-dir", p))),
        ("名前@チームで 1 件に絞れる", run(script, "verifier@t1", "--projects-dir", p)[0] == 0),
        ("agent ID で解決する", run(script, "aaa", "--projects-dir", p)[0] == 0),
        ("agent- の接頭辞つきでも解決する", run(script, "agent-aaa", "--projects-dir", p)[0] == 0),
        ("見つからなければ rc=2", run(script, "none", "--projects-dir", p)[0] == 2),
        ("JSON の行が無ければ rc=2", run(script, str(fx["empty"]))[0] == 2),
    ]
    return checks


MUTATIONS = {
    # 守る 1: 判定は結果の backgroundTaskId で行う
    "入力フラグで判定する": (
        '                if isinstance(tur, dict) and tur.get("backgroundTaskId"):',
        '                if isinstance(tur, dict) and (c["input"] or {}).get("run_in_background"):'),
    # 守る 2: 自動は「ID あり・指定なし」で決める（timedOutAfterMs で決めない）
    "timedOutAfterMs で自動を決める": (
        '    return "指定" if inp.get("run_in_background") else "自動"',
        '    return "自動" if c["timeout"] else "指定"'),
    # 守る 3: 通知の行からだけ拾う
    "どの行からも通知を拾う": (
        '    if r.get("type") == "attachment":\n        return json.dumps(r.get("attachment"), ensure_ascii=False)',
        '    if True:\n        return json.dumps(r, ensure_ascii=False)'),
    # 守る 4: 1 つの通知の中でだけ組にする
    "行全体で 1 組だけ拾う": (
        "        for block in NOTIFICATION.findall(notification_text(r)):",
        "        for block in [notification_text(r)] if '<task-notification>' in notification_text(r) else []:"),
    # 守る 5: stop_reason で絞らない
    "end_turn の text だけを並べる": (
        "            if text:\n",
        '            if text and msg.get("stop_reason") == "end_turn":\n'),
    # 守る 6: 2 件以上当たったら選ばない
    "先頭の 1 件を選ぶ": (
        "    if len(hits) > 1:",
        "    if False:"),
    # 守る 7: 禁じられた形に印を付ける（頭だけに切ると本体が隠れる）
    "印を付けない": (
        '        marks = "".join(f"[{f}]" for f in flags(inp["command"]))',
        '        marks = ""'),
    # 守る 8: --text は 1 件だけ
    "--text で全部を出す": (
        '        print(says[args.text - 1]["text"])',
        '        print("\\n".join(s["text"] for s in says))'),
}


def main() -> int:
    failures: list[str] = []

    def check(name: str, cond: bool) -> None:
        print(f"  {'ok  ' if cond else 'FAIL'} {name}")
        if not cond:
            failures.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp).resolve()
        assert_in_tmp(tmpdir)
        projects = tmpdir / "projects"
        fx = {
            "stalled": write(tmpdir / "stalled" / "agent-stalled.jsonl", stalled_rows()),
            "empty": write(tmpdir / "empty" / "agent-empty.jsonl", []),
            "projects": projects,
        }
        for proj, agent, team in (("p1/s1", "aaa", "t1"), ("p2/s2", "bbb", "t2")):
            d = projects / proj / "subagents"
            write(d / f"agent-{agent}.jsonl", stalled_rows())
            write(d / f"agent-{agent}.meta.json", [])
            (d / f"agent-{agent}.meta.json").write_text(
                json.dumps({"name": "verifier", "teamName": team}), encoding="utf-8")

        print("本体")
        for name, ok in evaluate(SCRIPT, fx):
            check(name, ok)

        print("\n変異テスト（壊したのに check が 1 つも落ちなければ失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}", False)
                continue
            d = tmpdir / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "summarize-subagent.py"
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            fell = [n for n, ok in evaluate(broken, fx) if not ok]
            check(f"変異を殺せる: {name}（落ちた check: {fell[0] if fell else 'なし'}）", bool(fell))

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
