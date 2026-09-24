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
（**テスト自身に数えさせる**）。**1 行に主張を 2 つ書かない**——変異は 1 行に 1 つなので、
2 つ目の主張には変異が当たらない（2 パス目の `/code-review` で、部分主張の変異が 10 件生き残った）。
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
REPORT = "## 検証結果\nREPORT_BODY 反証 0 件\n" + "詳細。" * 60
HANDBACK = "HANDBACK_BODY"
HANDBACK2 = "HANDBACK2_BODY"
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


def event(task_id):
    """Monitor の途中経過。<status> を持たない。"""
    return f"<task-notification>\n<task-id>{task_id}</task-id>\n<event>line</event>\n</task-notification>"


def queued(sec, prompt):
    return {"type": "attachment", "timestamp": ts(sec),
            "attachment": {"type": "queued_command", "prompt": prompt}}


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
        # Monitor の監視（キーが taskId）。途中経過の event だけが届き、完了は届かない
        assistant(170, [{"type": "tool_use", "id": "t9", "name": "Monitor",
                         "input": {"description": "wait", "command": "tail -f log", "timeout_ms": 600000}}],
                  stop="tool_use"),
        tool_result(171, "t9", {"taskId": "bmon", "timeoutMs": 600000, "persistent": False}),
        queued(180, event("bmon")),
        # 1 つの attachment に通知が 2 つ
        queued(200, notice("bspec", "completed") + notice("bkill", "killed")),
        # bauto2: 途中経過（status なし）のあとで、completed が user の発言（SYSTEM NOTIFICATION）で届く
        queued(205, event("bauto2")),
        {"type": "user", "timestamp": ts(230),
         "message": {"role": "user", "content": "[SYSTEM NOTIFICATION]\n" + notice("bauto2", "completed")}},
        # 道具の結果に、bauto の通知の文面が写り込んでいる（出力ファイルを cat した）
        tool_use(210, "t6", "cat /tmp/tasks/bauto.output"),
        tool_result(211, "t6", content=notice("bauto", "completed")),
        # 道具の入力（assistant の行）に、bmon の通知の文面が写り込んでいる
        tool_use(212, "t10", "echo '" + notice("bmon", "completed") + "'"),
        tool_result(213, "t10"),
        # 印の陽性と陰性: 狭い探索・URL の & には付けない
        tool_use(214, "t11", "find ~/.venv/lib -name site-packages"),
        tool_result(215, "t11"),
        tool_use(216, "t12", "curl 'https://api.example/issues?labels=x&state=open'"),
        tool_result(217, "t12"),
        tool_use(218, "t13", "sleep 5 & wait"),
        tool_result(219, "t13"),
        tool_use(220, "t14", "find ~ -name pkg"),
        tool_result(221, "t14"),
        assistant(222, [{"type": "text", "text": PREAMBLE}]),
        tool_use(223, "t7", "git diff"),
        tool_result(224, "t7"),
        # 最後の報告の stop_reason が end_turn ではない（実測で 46 件ある形）。いちばん長い text
        assistant(300, [{"type": "text", "text": REPORT}], stop=None),
        tool_use(310, "t8", None, name="SendMessage", to="team-lead", message=HANDBACK),
        tool_result(311, "t8"),
        tool_use(312, "t15", None, name="SubagentHandback", message=HANDBACK2),
        tool_result(313, "t15"),
        # 報告のあとで子が起こされて短い text を重ねる（報告と引き渡しが新しい 6 件の窓から出る）
        *[assistant(400 + i, [{"type": "text", "text": f"短い {i}"}]) for i in range(6)],
        # 最後の text の stop_reason が stop_sequence（実測で 29 件ある形）
        assistant(410, [{"type": "text", "text": "STOPSEQ_TEXT"}], stop="stop_sequence"),
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
    auto, auto2, spec, kill, mon = (line_of(out, h) for h in ("bauto ", "bauto2", "bspec", "bkill", "bmon"))
    says = [l for l in out.splitlines() if "文字  " in l]
    report_line = next((l for l in says if "REPORT_BODY" in l), "")
    report_no = report_line.split(".")[0].strip() if report_line else "0"

    def cmd(needle):
        return next((l for l in out.splitlines() if needle in l and "Bash" in l), "")

    p = str(fx["projects"])
    checks = [
        ("rc=0", rc == 0),
        ("バックグラウンドは 5 本（指定 2 ／ 自動 2 ／ 監視 1）", "5 本（指定 2 ／ 自動 2 ／ 監視 1）" in out),
        ("入力に無いのに回ったもの（timedOutAfterMs あり）を「自動」と出す", " 自動" in auto),
        ("timedOutAfterMs が無くても、入力に指定が無ければ「自動」と出す", " 自動" in auto2),
        ("指定したものを「指定」と出す", " 指定" in spec),
        ("Monitor の taskId を「監視」として数える", " 監視" in mon),
        ("attachment の通知で「完了の記録あり」", "完了の記録あり（completed" in spec),
        ("user の発言（SYSTEM NOTIFICATION）の通知も拾う", "完了の記録あり（completed" in auto2),
        ("道具の結果に写った通知は完了に数えない", "完了の記録なし" in auto),
        ("道具の入力に写った通知・途中経過の event は完了に数えない", "完了の記録なし" in mon),
        ("同じ行の 2 つ目の通知も、自分の status で拾う", "完了の記録あり（killed" in kill),
        ("stop_reason が None の報告も並べる", bool(report_line)),
        ("stop_reason が stop_sequence の text も並べる", any("STOPSEQ_TEXT" in l for l in says)),
        ("SendMessage の引き渡しを並べる", any("引き渡し" in l and "HANDBACK_BODY" in l for l in says)),
        ("SubagentHandback の引き渡しを並べる", any("引き渡し" in l and HANDBACK2 in l for l in says)),
        ("判定しないことを明示する", "判定しない" in out),
        ("コマンドの途中の find / に印を付ける", "[find /]" in auto),
        ("find ~ に印を付ける", "[find ~]" in cmd("find ~ -name")),
        ("狭い探索（find ~/.venv/...）には印を付けない", "[find ~]" not in cmd("find ~/.venv")),
        ("URL の & には印を付けない", "[&]" not in cmd("curl")),
        ("バックグラウンドの & に印を付ける", "[&]" in cmd("sleep 5 &")),
        ("長いコマンドの全文を出さない", FIND_CMD not in out),
        ("コマンドの尾を出す", "| head -5" in auto),
        ("道具の出力を出さない", TOOL_OUTPUT not in out),
    ]
    rc, out = run(script, str(fx["stalled"]), "--text", report_no)
    checks += [
        ("--text は報告の全文を出す", rc == 0 and "REPORT_BODY" in out and "詳細。" * 60 in out),
        ("--text は指定した 1 件だけを出す", PREAMBLE not in out and HANDBACK not in out),
        ("--text の番号が上に範囲外なら rc=2", run(script, str(fx["stalled"]), "--text", "99")[0] == 2),
        ("--text 0 は rc=2（末尾から数えない）", run(script, str(fx["stalled"]), "--text", "0")[0] == 2),
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
    # 守る 1: Bash は結果の backgroundTaskId で判定する
    "入力フラグで判定する": (
        '                if isinstance(tur, dict) and tur.get("backgroundTaskId"):',
        '                if isinstance(tur, dict) and (c["input"] or {}).get("run_in_background"):'),
    # 守る 2: Monitor は taskId で数える
    "Monitor を数えない": (
        '                elif isinstance(tur, dict) and c["name"] == "Monitor" and tur.get("taskId"):',
        "                elif False:"),
    # 守る 3: 自動は「ID あり・指定なし」で決める（timedOutAfterMs で決めない）
    "timedOutAfterMs で自動を決める": (
        '    return "指定" if inp.get("run_in_background") else "自動"',
        '    return "自動" if c["timeout"] else "指定"'),
    # 守る 4: user の発言（SYSTEM NOTIFICATION）からも拾う
    "user の発言を見ない": (
        "        if isinstance(content, str):\n            return content",
        '        if isinstance(content, str):\n            return ""'),
    # 守る 5: 道具の結果・入力からは拾わない
    "どの行からも通知を拾う": (
        '    if r.get("type") == "attachment":\n        return json.dumps(r.get("attachment"), ensure_ascii=False)',
        "    if True:\n        return json.dumps(r, ensure_ascii=False)"),
    # 守る 6: 1 つの通知の中でだけ組にする
    "行全体で 1 組だけ拾う": (
        "        for block in NOTIFICATION.findall(notification_text(r)):",
        "        for block in [notification_text(r)] if '<task-notification>' in notification_text(r) else []:"),
    # 守る 7: status の無い通知は完了に数えない
    "途中経過を完了に数える": (
        "            if tid and status:\n"
        "                done.setdefault(tid.group(1).strip(), (status.group(1).strip(), ts))",
        "            if tid:\n"
        '                done.setdefault(tid.group(1).strip(), (status.group(1).strip() if status else "?", ts))'),
    # 守る 8: stop_reason で絞らない
    "stop_sequence を落とす": (
        "            if text:\n",
        '            if text and msg.get("stop_reason") in ("end_turn", None):\n'),
    # 守る 9: SubagentHandback・SendMessage の両方を引き渡しとして並べる
    "SubagentHandback を見ない": (
        'HANDBACK = ("SubagentHandback", "SendMessage")',
        'HANDBACK = ("SendMessage",)'),
    # 守る 10: 引き渡しは窓から外れても出す
    "引き渡しを窓に任せる": (
        '    picked |= {i for i, s in enumerate(says, 1) if s["kind"] == "引き渡し"}',
        "    picked |= set()"),
    # 守る 11: いちばん長い text も窓から外れても出す
    "最長の text を窓に任せる": (
        "        picked.add(max(texts)[1])",
        "        pass"),
    # 守る 12: 2 件以上当たったら選ばない
    "先頭の 1 件を選ぶ": (
        "    if len(hits) > 1:",
        "    if False:"),
    # 守る 13: 禁じられた形に印を付ける（頭だけに切ると本体が隠れる）
    "印を付けない": (
        '        marks = "".join(f"[{f}]" for f in flags(inp["command"]))',
        '        marks = ""'),
    # 守る 14: 印は禁じた形だけに付ける
    "印を広く付ける": (
        '    ("find ~", re.compile(r"\\bfind\\s+(~|\\$HOME)/?(\\s|$)")),\n'
        '    ("&", re.compile(r"(^|\\s)&(\\s|$)")),',
        '    ("find ~", re.compile(r"\\bfind\\s+(~|\\$HOME)")),\n'
        '    ("&", re.compile(r"(?<![&|>0-9])&(?![&>])")),'),
    # 守る 15: --text は 1 件だけ
    "--text で全部を出す": (
        '        print(says[args.text - 1]["text"])',
        '        print("\\n".join(s["text"] for s in says))'),
    # 守る 16: --text の範囲外（0 と負を含む）は非ゼロ
    "--text の下限を見ない": (
        "        if not 1 <= args.text <= len(says):",
        "        if not args.text <= len(says):"),
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
            meta = d / f"agent-{agent}.meta.json"
            assert_in_tmp(meta)
            meta.write_text(json.dumps({"name": "verifier", "teamName": team}), encoding="utf-8")

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
