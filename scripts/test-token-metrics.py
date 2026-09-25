#!/usr/bin/env python3
"""`token-metrics.py` の回帰テスト。

    python3 scripts/test-token-metrics.py

**このテストは実環境を触らない。** 毎回テンポラリに偽の `projects` ツリーを作り、
そこだけを対象にする（`assert_not_real_home` がそれを担保する）。
本体は実ホームの `~/.claude/projects` を既定にするので、**歯止めが無いと、
テストが利用者のトランスクリプトを読んで通ってしまう**——通っても「歯止めが効く」の
証明にならない。

**変異テストを含む。** 検査本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
「正しい入力で緑」だけでは、**何も検査しない実装でも通る**。

**本体は CI から呼ばないが、このテストは CI で回す。** `test-export-diagrams.py` が
同じ形——本体（`export-diagrams.py`）は CI から呼ばないが、テストは `docs.yml` で回っている。
**歯止めが「置いてあるが何も見ていない」状態に退化するのを防ぐ**のがテストの役目なので、
本体が手動でもテストは自動で回す。
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "token-metrics.py"
REAL_HOME_PROJECTS = Path(os.path.expanduser("~")) / ".claude" / "projects"

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"tm_{script.parent.parent.name}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_home(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_HOME_PROJECTS.resolve(), "テストが実ホームの projects を対象にしている"
    assert not str(resolved).startswith(str(REAL_HOME_PROJECTS.resolve()) + os.sep), (
        "テストの対象が実ホームの projects の内側にある"
    )
    # 両側を resolve() してから比べる（macOS の /var → /private/var）。
    tmp_root = Path(tempfile.gettempdir()).resolve()
    assert resolved.is_relative_to(tmp_root), "テストの対象がテンポラリの外にある"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def usage(inp=0, cw=0, cr=0, out=0, *, iterations=True):
    u = {
        "input_tokens": inp,
        "cache_creation_input_tokens": cw,
        "cache_read_input_tokens": cr,
        "output_tokens": out,
    }
    if iterations:
        # **本物と同じ形**: 各要素がトップレベルと同じ数字を再掲している。
        u["iterations"] = [dict(u)]
    return u


def line(model="claude-opus-5", day="2026-09-15", u=None, tool=None, msg_id=None,
         time="10:00:00", is_sub=False):
    message = {"model": model}
    if msg_id is not None:
        # **本物は必ず `id` を持つ。** 同じ id の行が複数あり、各行が usage を再掲する。
        message["id"] = msg_id
    if u is not None:
        message["usage"] = u
    if tool is not None:
        message["content"] = [tool]
    return json.dumps({"type": "assistant", "timestamp": f"{day}T{time}.000Z",
                       "message": message}, ensure_ascii=False)


def skill_use(name):
    return {"type": "tool_use", "name": "Skill", "input": {"skill": name}}


def agent_use(subagent_type):
    return {"type": "tool_use", "name": "Agent", "input": {"subagent_type": subagent_type}}


def user_line(text, day="2026-09-15", time="09:59:00", as_list=False):
    """user メッセージの行。スラッシュ起動の観測に要る。"""
    content = [{"type": "text", "text": text}] if as_list else text
    return json.dumps({"type": "user", "timestamp": f"{day}T{time}.000Z",
                       "message": {"role": "user", "content": content}},
                      ensure_ascii=False)


def slash(number="10856", name="/dev-loop:dev-loop"):
    """本物と同じ起動形のテキスト。"""
    args = f"<command-args>{number}</command-args>" if number is not None else ""
    return (f"<command-message>dev-loop</command-message>\n"
            f"<command-name>{name}</command-name>\n{args}")


def make_tree(root: Path, files: dict[str, list[str]]) -> None:
    assert_not_real_home(root)
    for rel, lines in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- 経過時間（`--elapsed`、#169） ---

def ev_row(kind, time, day="2026-09-15", uuid=None, **fields):
    """経過時間の試料の 1 行。**形は #168 の親セッションの実物に合わせてある。**"""
    row = {"type": kind, "timestamp": f"{day}T{time}.000Z", **fields}
    if uuid is not None:
        row["uuid"] = uuid
    return json.dumps(row, ensure_ascii=False)


def ev_assistant(time, *, stop="tool_use", uses=(), text=None, mid=None, **kw):
    content = [{"type": "tool_use", "id": i, "name": n, "input": a} for i, n, a in uses]
    if text is not None:
        content.append({"type": "text", "text": text})
    # **usage を持たせる**——`main` はレコードが 0 件だと集計の前に帰る。
    message = {"role": "assistant", "model": "claude-opus-5", "stop_reason": stop,
               "content": content, "usage": usage(inp=1)}
    if mid is not None:
        message["id"] = mid
    return ev_row("assistant", time, message=message, **kw)


def ev_result(time, tool_id, status=None, background=None, **kw):
    fields = {"message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tool_id, "content": "ok"}]}}
    if status is not None:
        fields["toolUseResult"] = {"status": status}
        if background is not None:
            fields["toolUseResult"]["background"] = background
    return ev_row("user", time, **fields, **kw)


def ev_user(time, text, *, meta=False, **kw):
    fields = {"message": {"role": "user", "content": text}}
    if meta:
        fields["isMeta"] = True
    return ev_row("user", time, **fields, **kw)


def task_notification(tool_id):
    return (f"<task-notification>\n<task-id>a1</task-id>\n<tool-use-id>{tool_id}</tool-use-id>\n"
            f"<status>completed</status>\n</task-notification>")


def teammate(name, body):
    return (f'Another Claude session sent a message:\n<teammate-message teammate_id="{name}" '
            f'color="blue">\n{body}\n</teammate-message>')


VERIFIER = {"subagent_type": "dev-loop:dev-loop-verifier"}


def elapsed_tree() -> dict[str, list[str]]:
    """経過時間の試料。**各行が、下の変異のどれかを殺すのに要る**（コメントに対応を書く）。"""
    s1 = [
        # **時刻が逆順の 2 行**——並べ替えない変異に要る（実物の先頭がこの形だった）。
        ev_assistant("10:00:10", uses=[
            ("q1", "AskUserQuestion", {}),
            # **起動形と食い違う `Skill` の引数**——優先順を入れ替える変異に要る。
            ("sk1", "Skill", {"skill": "dev-loop:dev-loop", "args": "501"})]),
        ev_user("10:00:00", slash("500")),
        ev_result("10:05:10", "q1"),                                  # 人間待ち 300 秒
        ev_assistant("10:05:20", uses=[
            ("v1", "Agent", {**VERIFIER, "name": "ver-1", "run_in_background": True}),
            ("r1", "Skill", {"skill": "code-review"})]),
        ev_result("10:05:21", "v1", status="teammate_spawned"),
        # **`forked` ＋ `background`**——裏の印を落とす変異に要る。
        ev_result("10:05:22", "r1", status="forked", background=True),
        ev_assistant("10:05:30", stop="end_turn", text="待ちます"),
        # **`isMeta` の行**——人間の発言と数える変異に要る。
        ev_user("10:06:00", "Base directory for this skill: …", meta=True),
        ev_user("10:15:30", task_notification("r1")),                # 通知待ち 600 秒・レビュー 610 秒
        ev_assistant("10:15:40", stop="end_turn", text="了解"),
        # **idle 通知が報告より先に来る**——idle を報告と数える変異に要る。
        ev_user("10:20:40", teammate("ver-1", '{"type":"idle_notification"}')),
        ev_assistant("10:20:50", stop="end_turn", text="まだ"),
        # **同じ tool-use-id の 2 度目の通知を `attachment` の経路で**——最初の報告で
        # 止めない変異と、その経路を落とす変異の両方に要る
        # （実物で `queued_command` に載るのは task-notification だけで、teammate は 0 件）。
        ev_row("attachment", "10:25:00", attachment={
            "type": "queued_command", "prompt": task_notification("r1")}),
        ev_user("10:30:50", teammate("ver-1", "反証 0 件")),        # Verifier 1530 秒
        # **タイムスタンプの無い行**——境界にしない。
        json.dumps({"type": "attachment", "attachment": {"type": "queued_command",
                                                         "prompt": task_notification("r1")}}),
        # **前景の Verifier**——前景の結果で終わる形。
        ev_assistant("10:31:00", uses=[("v2", "Agent", VERIFIER)]),
        ev_result("10:33:00", "v2", status="completed"),              # 関門 120 秒
        # **報告の来ない Verifier**——0 秒で数える変異に要る。
        ev_assistant("10:33:10", uses=[("v3", "Agent", {**VERIFIER, "name": "ver-3"}),
                                       ("v4", "Agent", {**VERIFIER, "name": "ver-4"})]),
        ev_result("10:33:11", "v3", status="async_launched"),
        ev_result("10:33:12", "v4", status="async_launched"),
        ev_assistant("10:33:20", stop="end_turn", text="待ちます"),
        # **報告の本文が idle 通知の `result` にしか無い形**（#92 の周の実物）
        # ——idle 通知を一律に捨てる変異に要る。
        ev_user("10:35:00", teammate(
            "ver-4", '{"type":"idle_notification","from":"ver-4","result":"反証 0 件"}')),
        ev_assistant("10:35:10", stop="end_turn", text="届きました"),
        ev_user("10:40:00", "続けて"),                                 # 人間待ち 290 秒
        ev_assistant("10:40:05", stop="end_turn", text="はい"),
    ]
    # **`/clear` 後のセッション。起動形は素のテキスト＋`Skill`**（#168 の実物の形）
    # ——`Skill` の引数から番号を取らない変異に要る。
    s2 = [
        ev_user("11:00:00", "/dev-loop 500", uuid="u1"),
        ev_assistant("11:00:05", uses=[("sk2", "Skill", {"skill": "dev-loop:dev-loop",
                                                         "args": "500"})], uuid="u2"),
        ev_result("11:00:06", "sk2", uuid="u3"),
        ev_assistant("11:00:10", stop="end_turn", text="ok", uuid="u4"),
    ]
    # **fork でコピーされたセッション**——`uuid` で畳まない変異に要る。
    s3 = s2 + [ev_user("11:00:20", "more", uuid="u5"),
               ev_assistant("11:00:30", stop="end_turn", text="ok", uuid="u6")]
    # **並行して動いた 2 セッション（`uuid` を共有しない）**——負の「セッション外」を出す変異に要る。
    p1 = [ev_user("12:00:00", slash("600")), ev_assistant("12:30:00", stop="end_turn", text="a")]
    p2 = [ev_user("12:00:00", slash("600")), ev_assistant("12:30:00", stop="end_turn", text="b")]
    # **日を跨ぐ周**——`--since` の切り落としに要る。
    over = [ev_user("23:50:00", slash("700")),
            ev_row("assistant", "00:10:00", day="2026-09-16", message={
                "role": "assistant", "model": "claude-opus-5", "stop_reason": "end_turn",
                "usage": usage(inp=1), "content": [{"type": "text", "text": "x"}]})]
    # **番号の取れない周**——件数を出さない変異に要る。
    nonum = [ev_assistant("13:00:00", uses=[("sk3", "Skill", {"skill": "dev-loop:dev-loop"})]),
             ev_assistant("13:00:05", stop="end_turn", text="?")]
    # **1 パス目の `/code-review` が実物で示した 3 形**（#169）。手で数えた値:
    # モデル 40・人間待ち 720・通知待ち 1200（合計 1960 = 14:00:00〜14:32:40）。
    s4 = [
        ev_user("14:00:00", slash("800")),
        # **API エラーで切れた応答**（`stop_sequence`）——`end_turn` だけを止まったと読む変異に要る。
        ev_assistant("14:00:10", stop="stop_sequence", text="API Error: 401"),
        ev_user("14:10:10", "続けて"),                                   # 人間待ち 600 秒
        # **人間 → 人間**——人間待ちに入れない変異に要る。
        ev_user("14:12:10", "もう 1 つ"),                                # 人間待ち 120 秒
        ev_assistant("14:12:20", stop="end_turn", text="待ちます"),
        # **`<tool-use-id>` を持たない再通知を `attachment` の経路で**——落とす変異に要る。
        ev_row("attachment", "14:22:20", attachment={
            "type": "queued_command",
            "prompt": "<task-notification>\n<task-id>b1</task-id>\n<status>completed</status>\n"
                      "</task-notification>"}),                           # 通知待ち 600 秒
        ev_assistant("14:22:30", stop="end_turn", text="まだ"),
        # **`isMeta` で届くサブエージェントの引き渡し**——境界にしない変異に要る。
        ev_user("14:32:30", 'Another Claude session sent a message:\n<agent-message from="b1">\n'
                            "[Subagent hand-back] 反証 0 件\n</agent-message>", meta=True),  # 通知待ち 600 秒
        ev_assistant("14:32:40", stop="end_turn", text="届きました"),
    ]
    # **2 パス目の `/code-review` が実物で示した 2 形**（#169）。手で数えた値:
    # モデル 400・道具 1・通知待ち 899（合計 1300 = 15:00:00〜15:21:40）。
    # 関門 ver-5 は 310 秒（15:00:30 起動 → 引き渡し）で、910 秒（あとの idle 通知）ではない。
    s5 = [
        ev_user("15:00:00", slash("810")),
        # **1 つの応答が 2 行に分かれ、先の行が `end_turn` を名乗る**——
        # 同じ応答の次の行を「止まった後」と読む変異に要る（モデル 30 秒）。
        ev_assistant("15:00:00", stop="end_turn", text="考え中", mid="m1"),
        ev_assistant("15:00:30", uses=[("v5", "Agent", {**VERIFIER, "name": "ver-5"})],
                     mid="m1"),
        ev_result("15:00:31", "v5", status="teammate_spawned"),         # 道具 1 秒
        ev_assistant("15:00:40", stop="end_turn", text="待ちます"),    # モデル 9 秒
        # **引き渡しが `attachment` で届き、それが最初の報告**（実物: `c73a0b7a…` 5329 行目）
        # ——引き渡しを報告と数えない変異に要る（関門が 910 秒になり、ここが境界でなくなる）。
        ev_row("attachment", "15:05:40", attachment={
            "type": "queued_command",
            "prompt": '<agent-message from="ver-5">\n反証 0 件\n</agent-message>'}),  # 通知待ち 300 秒
        ev_assistant("15:05:41", stop="end_turn", text="届きました"),  # モデル 1 秒
        ev_user("15:15:40", teammate(
            "ver-5", '{"type":"idle_notification","from":"ver-5","result":"反証 0 件"}')),  # 通知待ち 599 秒
        ev_assistant("15:21:40", stop="end_turn", text="ok"),          # モデル 360 秒（通知 → assistant）
    ]
    # **3 パス目の `/code-review` が実物で示した 3 形**（#169）。手で数えた値:
    # モデル 310・人間待ち 595（合計 905 = 16:00:00〜16:15:05）。
    # 関門 r6 は報告なし（failed の通知は報告ではない）。
    s6 = [
        ev_user("16:00:00", slash("820")),
        ev_assistant("16:00:05", uses=[("r6", "Skill", {"skill": "code-review"}),
                                       ("q6", "AskUserQuestion", {})]),  # モデル 5 秒
        ev_result("16:00:06", "r6", status="forked", background=True),  # 人間待ち 1 秒（答え待ち）
        # **答えを待っている間に通知が来る**——通知で答え待ちを切る変異に要る。
        # **しかもその通知は failed**——failed を報告と数える変異に要る。
        ev_user("16:05:00", "<task-notification>\n<task-id>c6</task-id>\n<tool-use-id>r6</tool-use-id>\n"
                            "<status>failed</status>\n</task-notification>"),  # 人間待ち 294 秒
        ev_result("16:10:00", "q6"),                                  # 人間待ち 300 秒
        # **圧縮の要約**（`isMeta` を持たない）——人間の発言と数える変異に要る。
        ev_user("16:15:00", "This session is being continued from a previous conversation …",
                isCompactSummary=True),
        ev_assistant("16:15:05", stop="end_turn", text="続けます"),  # モデル 305 秒（要約は境界でない）
    ]
    # **4 パス目の関門が示した 4 形**（#169）。手で数えた値:
    # モデル 28・道具 2・通知待ち 600・その他 10（合計 640 = 17:00:00〜17:10:40）。
    # 関門 r7 は報告なし（killed）、r8 は 625 秒（連結された完了通知）。
    s7 = [
        ev_user("17:00:00", slash("830")),
        ev_assistant("17:00:05", uses=[("r7", "Skill", {"skill": "code-review"}),
                                       ("r8", "Skill", {"skill": "code-review"})]),  # モデル 5 秒
        ev_result("17:00:06", "r7", status="forked", background=True),  # 道具 1 秒
        ev_result("17:00:07", "r8", status="forked", background=True),  # 道具 1 秒
        ev_assistant("17:00:10", stop="end_turn", text="待ちます"),     # モデル 3 秒
        # **`message.id` の無い 2 行**——`None == None` を同じ応答と読む変異に要る（その他 10 秒）。
        ev_assistant("17:00:20", stop="end_turn", text="まだ"),
        # **前置きの後に埋まった killed の通知**——killed を報告と数える変異と、
        # 途中に埋まった通知を人間の発言にする変異に要る（通知待ち 300 秒）。
        ev_user("17:05:20", "前置き\n<task-notification>\n<task-id>c7</task-id>\n"
                            "<tool-use-id>r7</tool-use-id>\n<status>killed</status>\n</task-notification>"),
        ev_assistant("17:05:30", stop="end_turn", text="待ちます"),     # モデル 10 秒
        # **連結された完了通知**——`status` が複数だと報告と数えない変異に要る（通知待ち 300 秒）。
        ev_user("17:10:30", task_notification("r8") + "\n" + task_notification("r8")),
        ev_assistant("17:10:40", stop="end_turn", text="届きました"),   # モデル 10 秒
    ]
    # **`/clear` で割った周の前のセッションが丸ごと `--since` の外**——
    # 残ったセッションだけで完結した周に見せる変異に要る。
    early1 = [ev_user("10:00:00", slash("900"), day="2026-09-14"),
              ev_assistant("10:01:00", stop="end_turn", text="a", day="2026-09-14")]
    early2 = [ev_user("10:00:00", slash("900"), day="2026-09-16"),
              ev_assistant("10:01:00", stop="end_turn", text="b", day="2026-09-16")]
    # **サブエージェント**——親の分割に混ぜる変異に要る（混ぜると s1 の長さが伸びる）。
    sub = [ev_user("09:00:00", "sub"), ev_assistant("12:00:00", stop="end_turn", text="x")]
    return {"repo-e/s1.jsonl": s1, "repo-e/s2.jsonl": s2, "repo-e/s3.jsonl": s3,
            "repo-e/p1.jsonl": p1, "repo-e/p2.jsonl": p2, "repo-e/over.jsonl": over,
            "repo-e/nonum.jsonl": nonum, "repo-e/s4.jsonl": s4, "repo-e/s5.jsonl": s5, "repo-e/s6.jsonl": s6, "repo-e/s7.jsonl": s7,
            "repo-e/early1.jsonl": early1, "repo-e/early2.jsonl": early2,
            "repo-e/s1/subagents/agent-x.jsonl": sub}


def observe_elapsed(module, root: Path):
    """経過時間の振る舞いを全部観測する（**秒のまま**——出力は分に丸めるので、そこだけ見ると
    差が消える変異がある）。"""
    try:
        events, issue_map = {}, {}
        records, dev, _, _ = module.scan(root, False, events, issue_map)
        seen = {}
        for key in sorted(events):
            seen[key] = (len(events[key]), module.partition(events[key]),
                         sorted(module.gates(events[key]), key=repr))
        issues = (sorted((r.session, r.issue) for r in records), sorted(issue_map.items()))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            for argv in (["--elapsed"], ["--elapsed", "--since", "2026-09-16"]):
                module.main(["--projects", str(root)] + argv)
        return seen, issues, buf.getvalue()
    except Exception as exc:  # noqa: BLE001
        return ("例外", type(exc).__name__)


def test_elapsed(base: Path, mod) -> None:
    print("経過時間（--elapsed、#169）")
    root = base / "elapsed"
    make_tree(root, elapsed_tree())
    events, issue_map = {}, {}
    records, dev, _, _ = mod.scan(root, False, events, issue_map)
    s1 = events[("repo-e", "s1")]
    parts = mod.partition(s1)
    # 手で数えた値（`elapsed_tree` のコメント）。
    check("区分が手で数えた値に一致する",
          parts == {"model": 91.0, "tool": 124.0, "human": 590.0, "notify": 1600.0,
                    "other": 0.0})
    check("区分の合計がセッションの長さに等しい（10:00:00〜10:40:05）",
          sum(parts.values()) == 2405.0)
    check("止まり方・人間→人間・id の無い通知・引き渡しを分ける（s4）",
          mod.partition(events[("repo-e", "s4")])
          == {"model": 40.0, "tool": 0.0, "human": 720.0, "notify": 1200.0, "other": 0.0})
    s5 = events[("repo-e", "s5")]
    check("分かれた応答・attachment の引き渡しを分ける（s5）",
          mod.partition(s5) == {"model": 400.0, "tool": 1.0, "human": 0.0, "notify": 899.0,
                                "other": 0.0})
    check("引き渡しが最初の報告なら、そこで関門が終わる（ver-5 は 310 秒）",
          mod.gates(s5) == [("verifier", 310.0)])
    s6 = events[("repo-e", "s6")]
    check("答え待ちの間の通知・圧縮の要約を分ける（s6）", mod.partition(s6) == {"model": 310.0, "tool": 0.0, "human": 595.0, "notify": 0.0, "other": 0.0})
    check("failed の通知は報告ではない（r6 は報告なし）", mod.gates(s6) == [("review", None)])
    s7 = events[("repo-e", "s7")]
    check("id の無い行・埋まった killed・連結された完了通知を分ける（s7）",
          mod.partition(s7) == {"model": 28.0, "tool": 2.0, "human": 0.0, "notify": 600.0,
                                "other": 10.0})
    check("killed は報告ではなく、連結された完了通知は報告（r7 なし・r8 625 秒）",
          sorted(mod.gates(s7), key=repr) == sorted([("review", None), ("review", 625.0)], key=repr))
    got = sorted(mod.gates(s1), key=repr)
    check("関門: レビュー 610 秒・Verifier 1530 秒と 120 秒と 110 秒・報告なし 1",
          got == sorted([("review", 610.0), ("verifier", 1530.0), ("verifier", 120.0),
                         ("verifier", 110.0), ("verifier", None)], key=repr))
    check("コピーされた行を 2 度数えない（s3 は自分の 2 行だけ）",
          len(events[("repo-e", "s3")]) == 2)
    check("サブエージェントを親の分割に入れない",
          not any(k[1] == "agent-x" for k in events) and ("repo-e", "s1") in events
          and min(e[0] for e in s1).endswith("10:00:00.000Z"))
    issue = {k[1]: v for k, v in issue_map.items()}
    check("起動形の番号が Skill の引数より優先", issue.get("s1") == "500")
    check("素のテキスト＋Skill の周も番号が取れる", issue.get("s2") == "500")
    check("レコードの番号もセッションの番号と同じ",
          {r.session: r.issue for r in records if r.session == "s2"} == {"s2": "500"})
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.main(["--projects", str(root), "--elapsed"])
    out = buf.getvalue()
    check("割った周を 1 行に束ねる（3 セッション）", "| #500 | 3 |" in out)
    check("並行したセッションは『重なり』と出す", "重なり 30" in out)
    check("番号の取れないセッションの件数を出す", "束ねられなかったセッション: 1 件" in out)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.main(["--projects", str(root), "--elapsed", "--since", "2026-09-16"])
    check("--since が周の途中に落ちたら出さず、件数を出す", "先頭が範囲外" in buf.getvalue()
          and "#700" not in buf.getvalue())
    check("前のセッションが丸ごと範囲外の周も出さない", "#900" not in buf.getvalue()
          and "先頭が範囲外の周 2 件" in buf.getvalue())

    source = SCRIPT.read_text(encoding="utf-8")
    mutants = {
        "isMeta の行を人間の発言と数える": (
            '    if row.get("isMeta"):',
            '    if False:'),
        "isMeta の引き渡しを境界にしない": (
            '        if kind == "user" and any("<agent-message " in t for t in user_texts(message)):',
            '        if False:'),
        "引き渡しを報告と数えない（attachment の引き渡しも境界でなくなる）": (
            '    mates |= set(AGENT_MESSAGE.findall(text))',
            '    pass'),
        "同じ応答の次の行を止まった後と読む": (
            '        if ended and cur[1] == "assistant" and prev[2].get("id") and cur[2].get("id") == prev[2]["id"]:',
            '        if False:'),
        "failed の通知を報告と数える": (
            '    if "<task-notification>" in text and set(NOTIFY_STATUS.findall(text)) <= {"completed"}:',
            '    if "<task-notification>" in text:'),
        "failed だけを報告から外す（killed を報告と数える）": (
            '    if "<task-notification>" in text and set(NOTIFY_STATUS.findall(text)) <= {"completed"}:',
            '    if "<task-notification>" in text and "failed" not in NOTIFY_STATUS.findall(text):'),
        "連結された完了通知を報告と数えない": (
            '    if "<task-notification>" in text and set(NOTIFY_STATUS.findall(text)) <= {"completed"}:',
            '    if "<task-notification>" in text and NOTIFY_STATUS.findall(text) in ([], ["completed"]):'),
        "途中に埋まった通知を人間の発言にする": (
            '            or ("<task-notification>" in text and bool(NOTIFY_TOOL_USE.search(text))))',
            '            )'),
        "id の無い行どうしを同じ応答と読む": (
            '        if ended and cur[1] == "assistant" and prev[2].get("id") and cur[2].get("id") == prev[2]["id"]:',
            '        if ended and cur[1] == "assistant" and cur[2].get("id") == prev[2].get("id"):'),
        "圧縮の要約を境界にする": (
            '    if row.get("isCompactSummary"):',
            '    if False:'),
        "答え待ちを通知で切る": (
            '        if asking:\n            category = "human"',
            '        if asking and cur[1] == "result" and asking & set(cur[2]["ids"]):\n            category = "human"'),
        "止まっていた状態を通知で切る（通知 → 通知がその他）": (
            '        waiting = ended or (prev[1] == "notify" and waiting)',
            '        waiting = ended'),
        "end_turn だけを止まったと読む": (
            '{"idle": message.get("stop_reason") != "tool_use",',
            '{"idle": message.get("stop_reason") == "end_turn",'),
        "人間 → 人間を人間待ちにしない": (
            '        elif prev[1] == "human" and cur[1] == "human":',
            '        elif False:'),
        "attachment の id の無い通知を落とす": (
            '        if ids or mates or _looks_notified(prompt):',
            '        if ids or mates:'),
        "丸ごと範囲外のセッションで周に印を付けない": (
            '    for k in early & cycles.keys():',
            '    for k in ():'),
        "idle 通知を報告と数える": (
            "    return isinstance(notice, dict) and bool(notice.get(\"result\"))",
            "    return True"),
        "idle 通知を一律に捨てる（result の報告を落とす）": (
            "    return isinstance(notice, dict) and bool(notice.get(\"result\"))",
            "    return False"),
        "attachment の経路の通知を落とす": (
            '        if not isinstance(attachment, dict) or attachment.get("type") != "queued_command":',
            '        if True:'),
        "並べ替えずに区間を作る": (
            '    ordered = sorted(events, key=lambda e: e[0])\n    totals',
            '    ordered = list(events)\n    totals'),
        "AskUserQuestion の待ちを人間待ちにしない": (
            '        if asking:\n            category = "human"',
            '        if False:\n            category = "human"'),
        "裏で起動した結果を関門の終わりと読む": (
            '            if kind == "result" and body["ids"].get(tool_id) is False:',
            '            if kind == "result" and tool_id in body["ids"]:'),
        "forked＋background を裏の印と読まない": (
            '    return status in BACKGROUND_STATUSES or (status == "forked" and bool(result.get("background")))',
            '    return status in BACKGROUND_STATUSES'),
        "報告の無い関門を 0 秒で数える": (
            '        out.append((gate, _seconds(start, end) if end else None))',
            '        out.append((gate, _seconds(start, end) if end else 0.0))'),
        "コピーされた行を畳まない": (
            '                if not (isinstance(row_id, str) and row_id in seen_rows):',
            '                if True:'),
        "サブエージェントを親の分割に入れる": (
            '            if events is not None and not is_sub:',
            '            if events is not None:'),
        "Skill の引数から番号を取らない": (
            '                        number = issue_number(str(args.get("args") or ""))',
            '                        number = None'),
        "Skill の引数を起動形より優先する": (
            '        return (session_issue.get(key) or session_issue_skill.get(key)',
            '        return (session_issue_skill.get(key) or session_issue.get(key)'),
        "経過時間の番号をレコードから引く（usage の無いセッションが落ちる）": (
            '            issues[key] = issue_for(key)',
            '            pass'),
        "負の『セッション外』をそのまま出す": (
            '        outside_cell = fmt_minutes(outside) if outside >= 0 else',
            '        outside_cell = fmt_minutes(outside) if True else'),
        "周の途中に落ちた --since を切り落とさない": (
            '        if since and first[:10] < since:\n            g["truncated"] = True',
            '        if False:\n            g["truncated"] = True'),
        "丸ごと範囲外の周を落とさない": (
            '            continue  # 丸ごと範囲外。',
            '            pass'),
        "teammate の名前で報告を当てない": (
            '(tool_id in body["ids"] or (mate and mate in body["mates"])):',
            '(tool_id in body["ids"]):'),
        "最初の報告で止めない": (
            '            if end:\n                break',
            '            if False:\n                break'),
        "束ねられなかった件数を出さない": (
            '    if unmerged:\n        lines.append(f"**Issue 番号が取れず束ねられなかったセッション: {unmerged} 件**"\n'
            '                     f"（この表には出していない）")\n    return "\\n".join(lines)\n\n\ndef render_per_cycle',
            '    if False:\n        lines.append(f"**Issue 番号が取れず束ねられなかったセッション: {unmerged} 件**"\n'
            '                     f"（この表には出していない）")\n    return "\\n".join(lines)\n\n\ndef render_per_cycle'),
    }
    correct = observe_elapsed(mod, root)
    check("陽性対照: 正しい実装は例外を出さない", correct[0] != "例外")
    for name, (old, new) in mutants.items():
        assert source.count(old) == 1, f"変異の対象が 1 箇所でない: {name}"
        mroot = base / ("elapsed-mutant-" + str(abs(hash(name)) % 10**6))
        assert_not_real_home(mroot)
        (mroot / "scripts").mkdir(parents=True, exist_ok=True)
        mscript = mroot / "scripts" / "token-metrics.py"
        mscript.write_text(source.replace(old, new), encoding="utf-8")
        check(f"変異を殺せる: {name}", observe_elapsed(load(mscript), root) != correct)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tm-test-") as tmp:
        base = Path(tmp)
        mod = load()

        print("加重の式")
        w, cr = mod.weighted_tokens(usage(inp=100, cw=200, cr=1000, out=10))
        # 100*1 + 200*1.25 + 1000*0.1 + 10*5 = 100 + 250 + 100 + 50 = 500
        check("加重が式どおり", w == 500.0)
        check("cache read を別に返す", cr == 1000)

        print("iterations を二重計上しない")
        u = usage(inp=100, cw=200, cr=1000, out=10)
        check("iterations がある入力を使っている", "iterations" in u)
        w2, _ = mod.weighted_tokens(u)
        check("iterations があっても加重が変わらない", w2 == 500.0)

        print("トップレベルが全部 0 で iterations に実数があるとき")
        # **実データに 2 件あった**（同じリクエストの重複）。cache read だけで
        # 約 100 万トークン。**トップレベルだけ読むと丸ごと落ちる**（#95 のレビューが発見）。
        u = {
            "input_tokens": 0, "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0, "output_tokens": 0,
            "iterations": [{"input_tokens": 2, "cache_creation_input_tokens": 545,
                            "cache_read_input_tokens": 996796, "output_tokens": 3070}],
        }
        w, cr = mod.weighted_tokens(u)
        # 2*1 + 545*1.25 + 996796*0.1 + 3070*5 = 2 + 681.25 + 99679.6 + 15350
        check("iterations から拾う", abs(w - 115712.85) < 0.01)
        check("cache read も iterations から取る", cr == 996796)

        print("トップレベルに値があれば iterations を足さない")
        w2, _ = mod.weighted_tokens(usage(inp=100, cw=200, cr=1000, out=10))
        check("二重計上しない（500 のまま）", w2 == 500.0)
        # **キーごとに大きいほうを採る。**「全部 0 のときだけ iterations を見る」だと、
        # 1 フィールドでも実数があると残りを落とした（#95 のレビュー）。
        u3 = usage(inp=100)
        u3["iterations"] = [{"input_tokens": 999999}]
        w3, _ = mod.weighted_tokens(u3)
        check("キーごとに大きいほうを採る", w3 == 999999.0)
        # 部分的に 0 のとき、iterations にしかない残りを落とさない。
        u4 = {"input_tokens": 0, "cache_creation_input_tokens": 0,
              "cache_read_input_tokens": 0, "output_tokens": 5,
              "iterations": [{"input_tokens": 1000, "cache_read_input_tokens": 500000,
                              "output_tokens": 5}]}
        w4, _ = mod.weighted_tokens(u4)
        # 1000*1 + 500000*0.1 + 5*5 = 1000 + 50000 + 25
        check("部分的に 0 でも残りを拾う", w4 == 51025.0)
        # iterations が 2 要素の再掲でも倍にしない。
        u5 = {"input_tokens": 0, "cache_creation_input_tokens": 0,
              "cache_read_input_tokens": 0, "output_tokens": 0,
              "iterations": [{"input_tokens": 100}, {"input_tokens": 100}]}
        w5, _ = mod.weighted_tokens(u5)
        check("iterations が複数要素でも足さない", w5 == 100.0)
        # **トップレベルが上回る側**も固定する。これが無いと「`iterations` だけ見る」
        # 変異が生き残る（#95 の 3 パス目）。`max` の**両側**を押さえる。
        u6 = {"input_tokens": 500, "cache_creation_input_tokens": 0,
              "cache_read_input_tokens": 0, "output_tokens": 0,
              "iterations": [{"input_tokens": 1}]}
        w6, _ = mod.weighted_tokens(u6)
        check("トップレベルが大きければそちらを採る", w6 == 500.0)

        print("レコードはあるが加重が 0 でも落ちない")
        root = base / "zero"
        make_tree(root, {"repo-a/s.jsonl": [line(u=usage())]})
        check("ゼロ除算にならない", mod.main(["--projects", str(root)]) == 0)

        print("1 応答が複数行に書かれるとき（message.id で畳む）")
        # **実データの支配的な形。** 行ごとに足すと 7 割ほど膨らんでいた
        # （率は設計 §8.3 の訂正を正とする。**ここに数字を書かない**——増えると古くなる）。
        root = base / "msgid"
        make_tree(root, {
            "repo-a/s.jsonl": [line(u=usage(out=1), msg_id="m1"),
                               line(u=usage(out=1), msg_id="m1"),
                               line(u=usage(out=207), msg_id="m1")],
        })
        records, _, _, _ = mod.scan(root)
        check("同じ id の 3 行を 1 件に畳む", len(records) == 1)
        # 育っていく形なので最大（207*5）を採る。
        check("畳むときに最大を採る", records[0].weighted == 1035.0)

        print("id が違えば別々に数える")
        root = base / "msgid2"
        make_tree(root, {
            "repo-a/s.jsonl": [line(u=usage(out=10), msg_id="m1"),
                               line(u=usage(out=10), msg_id="m2")],
        })
        records, _, _, _ = mod.scan(root)
        check("別の id は畳まない", len(records) == 2)

        print("id が無ければそのまま数える")
        root = base / "noid"
        make_tree(root, {"repo-a/s.jsonl": [line(u=usage(out=10)), line(u=usage(out=10))]})
        records, _, _, _ = mod.scan(root)
        check("id が無ければ落とさずに数える", len(records) == 2)

        print("ファイルを跨いでも同じ id なら畳む")
        # **`message.id` は API が採番するので、ファイルを跨いでも同一の応答**。
        # セッションを fork / resume すると履歴がコピーされ、同じ応答が別ファイルにも入る
        # （実測で数 % 過大になっていた）。**初版はファイル単位で畳んでおり、
        # このテストが「別物として数える」を正しい挙動として固定していた**（#95 の 2 パス目）。
        root = base / "msgid3"
        make_tree(root, {
            "repo-a/s1.jsonl": [line(u=usage(out=10), msg_id="m1")],
            "repo-a/s2.jsonl": [line(u=usage(out=10), msg_id="m1")],
        })
        records, _, _, _ = mod.scan(root)
        check("跨ファイルの同名 id を 1 件に畳む", len(records) == 1)
        check("帰属は先に出会ったファイル", records[0].session == "s1")

        print("消費量は最大・帰属は最も古いレコード")
        # **2 つは別の基準で決まる。** 消費量は育ちきった値（最大）、帰属は最初に
        # 消費した側。**走査順では帰属を決められない**——セッション id は UUID で
        # 時刻を持たず、実測で「走査順の先頭が最も古いファイル」は 0 件だった
        # （#95 の 3 パス目。docstring は「先に出会ったほう」と書いていたが、
        # それは**コピー側に約 7 割착地していた**）。
        root = base / "msgid4"
        make_tree(root, {
            # s2 が**先に**走査される（アルファベット順では s1 が先なので、
            # 名前で「古い」を決められないことを示すために日付を逆にしてある）。
            "repo-a/s1.jsonl": [line(day="2026-09-16", u=usage(out=1), msg_id="m1")],
            "repo-a/s2.jsonl": [line(day="2026-09-15", u=usage(out=207), msg_id="m1")],
        })
        records, _, _, _ = mod.scan(root)
        check("消費量は最大を採る", records[0].weighted == 1035.0)
        check("帰属は古いほうのセッション", records[0].session == "s2")
        check("日付も古いほうを採る", records[0].day == "2026-09-15")

        print("サブエージェントを取りこぼさない")
        root = base / "sub"
        make_tree(root, {
            "repo-a/sess1.jsonl": [line(u=usage(inp=1000))],
            "repo-a/sess1/subagents/agent1.jsonl": [line(u=usage(inp=3000))],
        })
        records, _, _, _ = mod.scan(root)
        check("親とサブエージェントの両方を拾う", len(records) == 2)
        check("サブエージェント分の加重が入っている",
              sum(r.weighted for r in records) == 4000.0)
        check("サブエージェントに印が付く", sum(1 for r in records if r.is_sub) == 1)
        check("サブエージェントも親セッションに属する",
              {r.session for r in records} == {"sess1"})

        print("`<synthetic>` を除外する")
        root = base / "syn"
        make_tree(root, {
            "repo-a/s.jsonl": [line(u=usage(inp=1000)),
                               line(model="<synthetic>", u=usage(inp=0))],
        })
        records, _, _, _ = mod.scan(root)
        check("synthetic のレコードを数えない", len(records) == 1)

        print("dev-loop の周を判定する")
        root = base / "dl"
        make_tree(root, {
            "repo-a/plain.jsonl": [line(u=usage(inp=10))],
            "repo-a/viaskill.jsonl": [line(u=usage(inp=10), tool=skill_use("dev-loop:dev-loop"))],
            "repo-a/viaagent.jsonl": [line(u=usage(inp=10),
                                           tool=agent_use("dev-loop:dev-loop-verifier"))],
            "repo-a/bare.jsonl": [line(u=usage(inp=10), tool=skill_use("dev-loop"))],
            "repo-a/other.jsonl": [line(u=usage(inp=10), tool=skill_use("code-review"))],
        })
        _, dev, _, _ = mod.scan(root)
        sessions = {s for _, s in dev}
        check("Skill 経由（名前空間つき）を拾う", "viaskill" in sessions)
        check("Skill 経由（素の名前）を拾う", "bare" in sessions)
        check("Agent 経由を拾う", "viaagent" in sessions)
        check("無関係なセッションを拾わない", "plain" not in sessions and "other" not in sessions)

        print("worktree の扱い")
        root = base / "wt"
        make_tree(root, {
            "repo-a/s.jsonl": [line(u=usage(inp=10))],
            "repo-a--claude-worktrees-issue-1/s.jsonl": [line(u=usage(inp=10))],
        })
        records, _, _, _ = mod.scan(root)
        check("既定では worktree を別リポジトリとして数える",
              len({r.repo for r in records}) == 2)
        records, _, _, _ = mod.scan(root, merge_worktrees=True)
        check("--merge-worktrees で元のリポジトリに寄せる",
              {r.repo for r in records} == {"repo-a"})

        print("壊れた入力で落ちない")
        root = base / "broken"
        make_tree(root, {
            "repo-a/s.jsonl": ["{壊れた JSON", "", "null", '{"type":"assistant"}',
                               '{"type":"assistant","message":{"usage":"文字列"}}',
                               line(u=usage(inp=10))],
        })
        records, _, unreadable, broken = mod.scan(root)
        check("壊れた行を飛ばして生き残る", len(records) == 1)
        check("読めなかったファイルは 0 件", unreadable == 0)
        # **壊れた行は数える。** 初版は 0 をアサートして「黙って落とす」を固定していた。
        check("壊れた行を数えている", broken == 2)

        print("読めないファイルがあっても落ちない")
        # **`_iter_rows` はジェネレータなので、`path.open()` は最初の `next()` まで動かない。**
        # 呼び出し側の `try` で囲んでも捕まらず、**読めないファイル 1 つで全体が落ちた**
        # （#95 の 3 パス目。性能修正のときに入った）。**`unreadable` を 0 としか
        # アサートしていなかったので、テストも通り抜けていた。**
        root = base / "unreadable"
        make_tree(root, {
            "repo-a/ok.jsonl": [line(u=usage(inp=10))],
            "repo-a/locked.jsonl": [line(u=usage(inp=999))],
        })
        locked = root / "repo-a" / "locked.jsonl"
        locked.chmod(0o000)
        try:
            records, _, unreadable, _ = mod.scan(root)
            check("読めないファイルで落ちない", True)
            check("読めるファイルは数える", len(records) == 1)
            check("読めなかった件数を返す", unreadable == 1)
            check("終了コードは 0（報告して続ける）",
                  mod.main(["--projects", str(root)]) == 0)
        except OSError:
            check("読めないファイルで落ちない", False)
        finally:
            locked.chmod(0o644)

        print("usage の在処を型で絞らない")
        root = base / "type"
        make_tree(root, {
            "repo-a/s.jsonl": [json.dumps({"type": "将来の型", "timestamp": "2026-09-15T10:00:00Z",
                                           "message": {"model": "m", "usage": usage(inp=10)}})],
        })
        records, _, _, _ = mod.scan(root)
        check("assistant 以外でも usage があれば拾う", len(records) == 1)

        print("出力の数字そのものを固定する（絶対的な検査）")
        # **変異ハーネスだけでは足りない。** あれは `observe(correct)` と
        # `observe(mutant)` を比べる**差分比較**なので、**元から在る欠陥は両側に
        # 継承されて見えない**（#95 の 3 パス目のレビューが、26 変異中 15 件の生存と、
        # `render_weekly` / `render_split` / `main` が丸ごと無検査であることを実証した）。
        # **§8.3 に載せる数字を作るのは `--split`** なので、ここは期待値で固定する。
        root = base / "numbers"
        make_tree(root, {
            # dev-loop の周: 2 セッション・3 レコード。
            #   d1: 1000 + (cr=200000 → 20000) = 21000、d2: 2000
            "repo-a/d1.jsonl": [line(u=usage(inp=1000, cr=200000), tool=skill_use("dev-loop")),
                                line(u=usage(inp=2000))],
            "repo-a/d2.jsonl": [line(u=usage(inp=3000), tool=skill_use("dev-loop"))],
            # それ以外: 1 セッション・1 レコード。
            "repo-a/o1.jsonl": [line(u=usage(inp=4000))],
        })
        records, dev, _, _ = mod.scan(root)
        check("レコード数", len(records) == 4)
        check("加重の合計", sum(r.weighted for r in records) == 30000.0)

        split = mod.render_split(records, dev)
        # dev-loop: 2 セッション・26000（21000+2000+3000）・26000/30000 = 87%・3 req / 2 セ = 1
        # それ以外: 1 セッション・4000・13%・1 req / 1 セ = 1
        check("--split の dev-loop 行", "| dev-loop を回した周 | 2 | 0 | 87% | 1 |" in split)
        check("--split のそれ以外の行", "| それ以外 | 1 | 0 | 13% | 1 |" in split)
        # **比率の分母が全体であること**を、合計が 100% になることで固定する。
        check("--split の比率が合計 100%",
              sum(int(cell.strip().rstrip("%"))
                  for row in split.splitlines()[2:]
                  for cell in [row.split("|")[4]]) == 100)

        weekly = mod.render_weekly(records, dev)
        # 2026-09-15 は ISO 2026-W38。**セッションは 3**（d1 が 2 レコードを持つ）で、
        # うち 2 つが dev-loop。平均文脈 = 200000 / 4 レコード = 50000 → 50k。
        # **レコード数とセッション数が違うことを、この 1 行が押さえている**
        # ——「セッションをレコードで数える」変異はここで落ちる。
        check("週次の行", "| 2026-W38 | 3 | 2 | 0 | 87% | 50k |" in weekly)

        print("集計の出力")
        root = base / "render"
        make_tree(root, {
            "repo-a/s1.jsonl": [line(day="2026-09-15", u=usage(inp=1000, cr=100000)),
                                line(day="2026-09-15", u=usage(inp=1000, cr=100000),
                                     tool=skill_use("dev-loop"))],
            "repo-b/s2.jsonl": [line(day="2026-09-08", u=usage(inp=1000))],
        })
        records, dev, _, _ = mod.scan(root)
        weekly = mod.render_weekly(records, dev)
        check("週次に 2 つの ISO 週が出る",
              "2026-W37" in weekly and "2026-W38" in weekly)
        per_cycle = mod.render_per_cycle(records, dev)
        check("周ごとに dev-loop の周だけ出る",
              "repo-a" in per_cycle and "repo-b" not in per_cycle)

        print("起点（floor）")
        root = base / "floor"
        make_tree(root, {
            # 同じ周の 2 レコード。**あとの行のほうが文脈が大きい**ので、
            # 「最も古いほう」を採れているかが分かる。
            "repo-a/s1.jsonl": [line(day="2026-09-15", time="09:00:00",
                                     u=usage(cr=40000, cw=1000), tool=skill_use("dev-loop")),
                                line(day="2026-09-15", time="11:00:00",
                                     u=usage(cr=90000))],
            # **サブエージェントは親と別の起点を持つ。親より「先」に置く。**
            # あとに置くと、除外していなくても親の最古レコードが勝つので、
            # **検査が何も見ていない状態になる**（最初そう書いて変異が生き残った）。
            # 委譲先のレコードは**親と同じセッション id の下**に入り、
            # 親の最古レコードは畳み込みで**別セッションへ帰属しうる**ので、
            # 時刻の前後は保証されない。
            "repo-a/s1/subagents/a.jsonl": [line(day="2026-09-15", time="08:00:00",
                                                 u=usage(cr=100))],
        })
        records, dev, _, _ = mod.scan(root)
        floors = mod.session_floors(records)
        first_seen, floor = floors[("repo-a", "s1")]
        # 40000 + 1000。**cache write を足す**——1 回目は write として課金されるので、
        # cache read だけで取ると周の最初のリクエストが 0 になる。
        check("起点は cache read + cache write", floor == 41000)
        check("起点は最も古いレコードから取る", first_seen.endswith("T09:00:00.000Z"))
        check("サブエージェントは起点の候補にしない",
              ("repo-a", "s1/subagents/a") not in floors
              and all(not key[1].startswith("s1/sub") for key in floors))
        check("context_tokens は input を足さない",
              mod.context_tokens({"input_tokens": 500, "cache_read_input_tokens": 3,
                                  "cache_creation_input_tokens": 2}) == 5)

        # **タイムスタンプの無いレコードは候補にしない。** 空文字は文字列順で最小に
        # なるので、候補に入れると黙って先頭に立つ。
        no_ts = mod.Record("2026-09-15", "repo-x", "s9", False, "claude-opus-5",
                           1.0, 0, "", 999999)
        with_ts = mod.Record("2026-09-15", "repo-x", "s9", False, "claude-opus-5",
                             1.0, 0, "2026-09-15T10:00:00.000Z", 7000)
        check("タイムスタンプの無いレコードは起点にしない",
              mod.session_floors([no_ts, with_ts])[("repo-x", "s9")][1] == 7000)

        check("起点比は加重が 0 なら None", mod.floor_share(1000, 10, 0) is None)
        check("起点比は req が 0 なら None", mod.floor_share(1000, 0, 5.0) is None)
        check("起点比は起点が 0 なら None", mod.floor_share(0, 10, 5.0) is None)
        # 1000 × 10 × 0.1 / 500 = 200%。**100% を超える値をそのまま返す**
        # ——丸めて隠すと、先頭が切れた周を見逃す。
        check("起点比は 100% を超えてもそのまま返す",
              abs(mod.floor_share(1000, 10, 500.0) - 200.0) < 1e-9)

        per_cycle = mod.render_per_cycle(records, dev)
        check("周ごとの表に起点の列が出る", "| 起点 | 起点比 |" in per_cycle)
        check("周ごとの表に起点の値が出る", "| 41k |" in per_cycle)

        # **先頭が絞り込みで切られた周は、起点も起点比も出さない。**
        # 絞り込む前の floors を渡し、絞ったレコードだけで描かせる。
        cut = [r for r in records if not r.timestamp.endswith("T09:00:00.000Z")]
        cut_out = mod.render_per_cycle(cut, dev, floors)
        check("先頭が範囲外の周は起点を出さない", "先頭が範囲外" in cut_out)
        check("先頭が範囲外の周は起点比を出さない",
              "起点が占める割合" not in cut_out)

        print("main() の終了コード")
        root = base / "main"
        make_tree(root, {"repo-a/s.jsonl": [line(u=usage(inp=10))]})
        check("走査できれば 0", mod.main(["--projects", str(root)]) == 0)
        missing = base / "なにもない"
        check("走査先が無ければ非ゼロ", mod.main(["--projects", str(missing)]) == 1)

        print("変異テスト（壊したのに緑なら失格）")
        print("スラッシュ起動の検出（#108）")
        check("起動形からコマンド名と引数を取る",
              mod.slash_command(slash("10856")) == ("dev-loop:dev-loop", "10856"))
        # **本文も role=user で載る。** タグが無いテキストを見ると、
        # 本文を読んだだけの周まで dev-loop になる。
        check("command-name タグが無い本文は起動形でない",
              mod.slash_command("本文に dev-loop と書いてあるだけ") is None)
        check("引数の無い起動でも起動形として取れる",
              mod.slash_command(slash(None))[0] == "dev-loop:dev-loop")
        check("Issue 番号は最初の数字の連なり", mod.issue_number("10856") == "10856")
        # **`0` で代用しない。** 束ねられなかったことを呼び出し側が判別できる必要がある。
        check("番号が取れなければ None（0 で代用しない）", mod.issue_number("") is None)
        check("worktree 名から番号を拾う",
              mod.worktree_issue("r--claude-worktrees-issue-10856-x") == "10856")
        check("issue- の形でない worktree 名は None",
              mod.worktree_issue("r--claude-worktrees-testing-md") is None)
        check("user_texts は assistant のテキストを返さない",
              list(mod.user_texts({"role": "assistant",
                                   "content": [{"type": "text", "text": slash()}]})) == [])
        check("user_texts は str の content を返す",
              list(mod.user_texts({"role": "user", "content": "x"})) == ["x"])

        print("スラッシュ起動の周と Issue 束ね（#108）")
        iroot = base / "issues"
        make_tree(iroot, {
            # **Verifier を呼ばない周**——現状の 2 経路では検出できない。
            "repo-i/a.jsonl": [user_line(slash("777")),
                               line(day="2026-09-15", time="10:00:00", u=usage(cr=10000))],
            # **同じ Issue の 2 セッション目**（割れた周）。
            "repo-i/b.jsonl": [user_line(slash("777"), time="11:00:00"),
                               line(day="2026-09-15", time="11:00:00", u=usage(cr=20000))],
            # **本文に dev-loop があるだけの周**——dev-loop に数えてはいけない。
            "repo-i/body.jsonl": [user_line("# dev-loop スキル\n本文"),
                                  line(day="2026-09-15", u=usage(inp=5))],
            # **引数の無い起動**——周ではあるが束ねられない。
            "repo-i/noarg.jsonl": [user_line(slash(None), time="12:00:00"),
                                   line(day="2026-09-15", time="12:00:00", u=usage(inp=6))],
            # **worktree フォールバック**——起動形が無く、ディレクトリ名に番号がある。
            "repo-i--claude-worktrees-issue-999-x/w.jsonl": [
                line(day="2026-09-15", u=usage(inp=7), tool=skill_use("dev-loop"))],
            # **起動形とディレクトリ名が食い違う**——起動形が勝つこと。
            "repo-i--claude-worktrees-issue-111-x/conflict.jsonl": [
                user_line(slash("222"), time="13:00:00"),
                line(day="2026-09-15", time="13:00:00", u=usage(inp=8))],
            # **サブエージェント**——親の Issue を継ぐこと。
            "repo-i/a/subagents/v.jsonl": [line(day="2026-09-15", u=usage(inp=9))],
        })
        irec, idev, _, _ = mod.scan(iroot)
        check("スラッシュ起動が Verifier を呼ばなくても周になる",
              ("repo-i", "a") in idev)
        check("本文に dev-loop があるだけでは周にならない",
              ("repo-i", "body") not in idev)
        issue_of = {(r.repo, r.session): r.issue for r in irec}
        check("起動形から Record に Issue が付く", issue_of[("repo-i", "a")] == "777")
        check("引数の無い起動は Issue が付かない", issue_of[("repo-i", "noarg")] is None)
        check("worktree 名がフォールバックになる",
              issue_of[("repo-i--claude-worktrees-issue-999-x", "w")] == "999")
        # **起動形が正。** ディレクトリ名は補助なので、食い違ったら起動形を採る。
        check("起動形が worktree 名より優先される",
              issue_of[("repo-i--claude-worktrees-issue-111-x", "conflict")] == "222")
        check("サブエージェントも親の Issue を継ぐ",
              [r.issue for r in irec if r.is_sub and r.session == "a"] == ["777"])

        per_issue = mod.render_per_issue(irec, idev)
        check("Issue の列が出る", "| Issue | セッション |" in per_issue)
        # **2 セッションが 1 行になる**のがこの表の目的。
        check("同じ Issue の 2 セッションが 1 行になる",
              per_issue.count("| #777 |") == 1)
        check("セッション数の列に 2 が出る", "| #777 | 2 |" in per_issue)
        check("割れている周の件数が出る", "割れている周 1 件" in per_issue)
        # **束ねられなかったものを黙って落とさない。**
        check("束ねられなかったセッションの件数が出る",
              "束ねられなかったセッション: 1 件" in per_issue)
        check("束ねられなかった Issue は行に出ない", "#None" not in per_issue)

        print("起点比の基準（#108 の訂正）")
        # **サブエージェントを含めると 1.65 倍に出た。** 親の req だけを渡す。
        check("起点比は req が増えれば増える",
              mod.floor_share(1000, 20, 5.0) > mod.floor_share(1000, 10, 5.0))
        fl_rec, fl_dev, _, _ = mod.scan(iroot)
        floors = mod.session_floors(fl_rec)
        check("サブエージェントは起点の候補にならない（親の値が残る）",
              floors[("repo-i", "a")][1] == 10000)
        per_cycle_i = mod.render_per_cycle(fl_rec, fl_dev)
        # 親 1 req・起点 10000・加重 1000*0.1=100 → 10000*1*0.1/100 = 100%
        check("起点比が親リクエストだけで計算される", "| 100% |" in per_cycle_i)

        # chmod したファイルは、テンポラリを消す前に戻す（消せなくなるため）。
        locked_paths: list[Path] = []
        source = SCRIPT.read_text(encoding="utf-8")
        mutants = {
            "iterations を足す（二重計上になるはず）": (
                "        out[key] = best",
                "        out[key] = sum((i.get(key) or 0) for i in its if isinstance(i, dict))",
            ),
            "iterations を見ない（取りこぼすはず）": (
                "    nested = _from_iterations(usage)",
                "    nested = {}",
            ),
            "message.id で畳まない（1 応答を複数回数えるはず）": (
                "            previous = by_id.get(message_id)",
                "            records.append(record)\n            previous = record\n"
                "            by_id.pop(message_id, None)\n            previous = None",
            ),
            "畳むときに消費量を更新しない（途中経過のまま残るはず）": (
                "            if record.weighted > previous.weighted:",
                "            if False:",
            ),
            "帰属を古いほうに寄せない（走査順のまま残るはず）": (
                "            if record.timestamp and (not previous.timestamp\n"
                "                                     or record.timestamp < previous.timestamp):",
                "            if False:",
            ),
            "起点に cache write を足さない（周の先頭が 0 になるはず）": (
                '    return int((effective.get("cache_read_input_tokens") or 0)\n'
                '               + (effective.get("cache_creation_input_tokens") or 0))',
                '    return int(effective.get("cache_read_input_tokens") or 0)',
            ),
            "サブエージェントを起点の候補にする（委譲先の起点に置き換わるはず）": (
                "        if r.is_sub or not r.timestamp:",
                "        if not r.timestamp:",
            ),
            "タイムスタンプの無いレコードを起点の候補にする": (
                "        if r.is_sub or not r.timestamp:",
                "        if r.is_sub and False:",
            ),
            "起点を最も古いレコードから取らない（走査順のままになるはず）": (
                "        if current is None or r.timestamp < current[0]:",
                "        if True:",
            ),
            "先頭が絞り込みで切られた周を印にしない（100% 超が出るはず）": (
                '        truncated = bool(first_seen) and bool(b["first"]) and b["first"] > first_seen',
                "        truncated = False",
            ),
            "起点比の集計を中央値でなく平均にする": (
                'f"**起点が占める割合: 中央値 {statistics.median(shares):.0f}%**"',
                'f"**起点が占める割合: 中央値 {sum(shares) / len(shares):.0f}%**"',
            ),
            "起点を絞り込みの後に作る（周の途中を起点と呼ぶはず）": (
                "    floors = session_floors(records)\n    if args.since:",
                "    if args.since:",
            ),
            "壊れた行を数えない": (
                '            if problem == "broken":\n'
                "                broken_lines += 1\n                continue",
                '            if problem == "broken":\n                continue',
            ),
            "壊れた行を JSON でないと判定しない": (
                '                if not isinstance(row, dict):\n'
                '                    yield None, "broken"',
                '                if not isinstance(row, dict):\n'
                '                    yield row, None',
            ),
            "読めないファイルを数えない": (
                '            if problem == "unreadable":\n'
                "                unreadable += 1\n                continue",
                '            if problem == "unreadable":\n                continue',
            ),
            "開く失敗を呼び出し側に投げる（全体が落ちるはず）": (
                '    try:\n        handle = path.open(encoding="utf-8", errors="replace")\n'
                '    except OSError:\n        yield None, "unreadable"\n        return',
                '    handle = path.open(encoding="utf-8", errors="replace")',
            ),
            "サブエージェントを見ない（取りこぼすはず）": (
                'for path in sorted(projects_root.rglob("*.jsonl")):',
                'for path in sorted(projects_root.glob("*/*.jsonl")):',
            ),
            "synthetic を除外しない": (
                "            if model in SYNTHETIC_MODELS:\n                continue",
                "            if False:\n                continue",
            ),
            "Agent 経由の判定をやめる": (
                "                elif name in AGENT_TOOLS:",
                "                elif False:",
            ),
            "旧版の Task を見ない": (
                'AGENT_TOOLS = ("Agent", "Task")',
                'AGENT_TOOLS = ("Agent",)',
            ),
            "Skill の command フォールバックを落とす": (
                '                    skill = args.get("skill") or args.get("command") or ""',
                '                    skill = args.get("skill") or ""',
            ),
            "--since の不等号を反転": (
                "        records = [r for r in records if r.day >= args.since]",
                "        records = [r for r in records if r.day <= args.since]",
            ),
            "--repo の絞りをやめる": (
                "        records = [r for r in records if args.repo in r.repo]",
                "        records = [r for r in records if True]",
            ),
            "--list-repos で worktree を寄せない": (
                "        if args.merge_worktrees:\n"
                "            # **集計と同じ粒度で見せる。**",
                "        if False:\n"
                "            # **集計と同じ粒度で見せる。**",
            ),
            "--split の req/セッションを総数にする": (
                "        per_session = len(rows) // len(sessions) if sessions else 0",
                "        per_session = len(rows)",
            ),
            # **レビューが「生存する」と実証した変異**（3 パス目）。差分比較のオラクルでは
            # 殺せず、上の「出力の数字そのものを固定する」検査のほうで落ちる。
            "--split の比率の分母を 1 にする": (
                "    total = sum(r.weighted for r in records) or 1",
                "    total = 1",
            ),
            "週次でセッションをレコード数で数える": (
                '        n_sessions = len(b["sessions"])',
                "        n_sessions = b[\"requests\"]",
            ),
            "週次で文脈を足さない": (
                '        bucket["ctx"] += r.cache_read',
                '        bucket["ctx"] += 0',
            ),
            "週次で dev-loop の加重を全体にする": (
                "        dev_weighted = sum(r.weighted for r in records\n"
                "                           if iso_week(r.day) == week\n"
                "                           and (r.repo, r.session) in dev_loop_sessions)",
                "        dev_weighted = b['weighted']",
            ),
            "iterations だけを見る（トップレベルが大きい側を落とすはず）": (
                "    return {key: max(top.get(key, 0), nested.get(key, 0)) for key in WEIGHTS}",
                "    return {key: nested.get(key, 0) for key in WEIGHTS}",
            ),
            "iso_week を暦年で切る": (
                "    year, week, _ = d.isocalendar()",
                "    year, week = d.year, d.isocalendar()[1]",
            ),
            "fmt_m を切り捨てにする": (
                '    return f"{value / 1_000_000:.0f}"',
                '    return str(int(value / 1_000_000))',
            ),
            "跨ファイルの畳み込みをファイル単位に戻す": (
                "        repo, session, is_sub = session_of(path, projects_root, merge_worktrees)",
                "        by_id = {}\n"
                "        repo, session, is_sub = session_of(path, projects_root, merge_worktrees)",
            ),
            # --- #108 で足した変異 ---
            '束ねられなかったセッションの件数を出さない（黙って落ちるはず）': (
                '    if unmerged:\n        # **束ねられなかったものを黙って落とさない。**',
                '    if False:\n        # **束ねられなかったものを黙って落とさない。**',
            ),
            'スラッシュ起動を検出しない（手順 5 まで周が無いはず）': (
                '                dev_loop_sessions.add((repo, session))\n                number = issue_number(args)',
                '                number = issue_number(args)',
            ),
            'タグではなく本文から名前を探す（#101 の落とし穴に戻るはず）': (
                '    name = SLASH_NAME.search(text)',
                '    name = re.search(r"([^\\s]*dev-loop[^\\s]*)", text)',
            ),
            'Issue 番号が取れないとき 0 で代用する': (
                '    return found.group(0) if found else None',
                '    return found.group(0) if found else "0"',
            ),
            'worktree 名を起動形より優先する': (
                '        return (session_issue.get(key) or session_issue_skill.get(key)\n'
                '                or session_issue_fallback.get(key))',
                '        return (session_issue_fallback.get(key) or session_issue.get(key)\n'
                '                or session_issue_skill.get(key))',
            ),
            'Issue で束ねない（セッションのままにするはず）': (
                '        g = per_issue[(key[0], number)]',
                '        g = per_issue[(key[0], number, key[1])]',
            ),
            '起点をセッションごとに合計しない（1 つ分になるはず）': (
                '            g["floor_req"] += floor * b["requests"]',
                '            g["floor_req"] = floor * b["requests"]',
            ),
            'セッション数を列に出さない': (
                '| {g[\'sessions\']} | {g[\'requests\']} "',
                '| {g[\'requests\']} "',
            ),
            '起点比にサブエージェントも数える（1.65 倍に出るはず）': (
                '        if not r.is_sub:\n            b["parent"] += 1',
                '        b["parent"] += 1',
            ),
            'user のテキストで role を見ない（assistant の言及も拾うはず）': (
                '    if message.get("role") != "user":\n        return',
                '    if False:\n        return',
            ),
            "加重の係数を 1 にする": (
                '    "output_tokens": 5.0,',
                '    "output_tokens": 1.0,',
            ),
        }
        for name, (old, new) in mutants.items():
            assert source.count(old) == 1, f"変異の対象が 1 箇所でない: {name}"
            mroot = base / ("mutant-" + str(abs(hash(name)) % 10**6))
            assert_not_real_home(mroot)
            (mroot / "scripts").mkdir(parents=True, exist_ok=True)
            mscript = mroot / "scripts" / "token-metrics.py"
            mscript.write_text(source.replace(old, new), encoding="utf-8")
            tree = mroot / "projects"
            top_zero = {
                "input_tokens": 0, "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0, "output_tokens": 0,
                "iterations": [{"input_tokens": 7, "cache_creation_input_tokens": 0,
                                "cache_read_input_tokens": 0, "output_tokens": 0}],
            }
            # **変異木は「殺したい変異が触るデータ」を全部持っていなければならない。**
            # 2 パス目のレビューが、同じ木で 21 変異を試して **12 件の生存**を実証した
            # ——木に該当データが無いだけで、実装は正しいのに検査されていなかった。
            two_iters = {
                "input_tokens": 0, "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0, "output_tokens": 0,
                "iterations": [{"input_tokens": 50}, {"input_tokens": 50}],
            }
            make_tree(tree, {
                "repo-a/s.jsonl": [line(u=usage(inp=100, cw=200, cr=1000, out=10)),
                                   line(model="<synthetic>", u=usage(inp=0)),
                                   # **トップレベルが全部 0 で iterations に実数**——
                                   # この 1 行が無いと「iterations を見ない」変異が殺せない。
                                   line(u=top_zero),
                                   # **iterations が 2 要素の再掲**——足す変異を殺すのに要る。
                                   line(u=two_iters),
                                   # **同じ message.id の重複行**（usage が育つ形）——
                                   # 畳む判定の変異 2 件は、これが無いと殺せない。
                                   line(u=usage(out=1), msg_id="msg_dup"),
                                   line(u=usage(out=207), msg_id="msg_dup"),
                                   # **壊れた行**——数えない変異を殺すのに要る。
                                   # パースできない行と、**JSON だが dict でない行**の両方。
                                   "{壊れた JSON",
                                   "[1, 2, 3]",
                                   # **`fmt_m` の丸めを効かせる大きな値**（1.5M 級）。
                                   line(u=usage(out=300000)),
                                   # **`--since` の境界**と**ISO 年 ≠ 暦年の日**
                                   # （2027-01-01 は ISO では 2026-W53）。
                                   line(day="2026-09-01", u=usage(inp=13)),
                                   line(day="2027-01-01", u=usage(inp=14))],
                "repo-a/s/subagents/a.jsonl": [line(u=usage(inp=3000))],
                # **判定の経路ごとに別セッションへ置く。** 同じファイルに全部入れると、
                # 1 つの経路を落としても**別の経路がそのセッションを dev と判定して**
                # 変異が生き残る（最初にそう書いて 3 件取り逃した）。
                "repo-a/via-agent.jsonl": [line(u=usage(inp=10),
                                                tool=agent_use("dev-loop-verifier"))],
                "repo-a/via-task.jsonl": [line(u=usage(inp=11),
                                               tool={"type": "tool_use", "name": "Task",
                                                     "input": {"subagent_type":
                                                               "dev-loop-verifier"}})],
                "repo-a/via-command.jsonl": [line(u=usage(inp=12),
                                                  tool={"type": "tool_use", "name": "Skill",
                                                        "input": {"command": "dev-loop"}})],
                # **worktree**——`--list-repos` の `--merge-worktrees` 変異に要る。
                "repo-a--claude-worktrees-x/s.jsonl": [line(u=usage(inp=15))],
                # **2 セッション目**——`--split` の `req/セッション` の割り算に要る
                # （1 群 1 セッションだと商が変わらず、変異が生き残る）。
                "repo-a/s2.jsonl": [line(u=usage(inp=16), tool=skill_use("dev-loop"))],
                # **読めないファイル**——OSError まわりの変異に要る（下で chmod する）。
                "repo-a/locked.jsonl": [line(u=usage(inp=17))],
                # **跨ファイルの同一 id で、走査順とタイムスタンプが逆**——
                # 帰属を古いほうに寄せる判定は、これが無いと殺せない。
                "repo-a/t1.jsonl": [line(day="2026-09-16", u=usage(inp=18), msg_id="mx")],
                "repo-a/t2.jsonl": [line(day="2026-09-15", u=usage(inp=19), msg_id="mx")],
                # **cache_read を持つレコード**——週次の平均文脈の変異に要る。
                "repo-a/ctx.jsonl": [line(u=usage(cr=500000))],
                # **起点の変異に要る木。** 同じ周に**時刻の違う 2 レコード**があり、
                # **サブエージェントが親より小さい文脈**を持ち、
                # **`--since` が周の途中に落ちる**（先頭 09-14 / 続き 09-16）。
                "repo-a/floor.jsonl": [line(day="2026-09-14", time="08:00:00",
                                            u=usage(cr=40000, cw=1000),
                                            tool=skill_use("dev-loop")),
                                       line(day="2026-09-16", time="08:00:00",
                                            u=usage(cr=800000))],
                "repo-a/floor/subagents/a.jsonl": [line(day="2026-09-14", time="07:30:00",
                                                       u=usage(cr=100))],
                # **タイムスタンプを持たないレコード**——空文字は文字列順で最小に
                # なるので、候補に入れると黙って先頭に立つ。これが無いと
                # 「タイムスタンプ無しを候補にする」変異が殺せない。
                "repo-a/floor4.jsonl": [json.dumps(
                    {"type": "assistant",
                     "message": {"model": "claude-opus-5", "id": "no_ts",
                                 "usage": {"input_tokens": 0,
                                           "cache_creation_input_tokens": 0,
                                           "cache_read_input_tokens": 777000,
                                           "output_tokens": 0},
                                 "content": [skill_use("dev-loop")]}},
                    ensure_ascii=False),
                    line(day="2026-09-14", time="08:00:00", u=usage(cr=5000))],
                # **起点比が周ごとに違う木**——中央値と平均が一致すると、
                # 「中央値を平均にする」変異が生き残る。3 周で 100% / 50% / 1 割弱にする。
                "repo-a/floor2.jsonl": [line(day="2026-09-14", time="08:00:00",
                                             u=usage(cr=10000), tool=skill_use("dev-loop")),
                                        line(day="2026-09-14", time="09:00:00",
                                             u=usage(cr=10000))],
                "repo-a/floor3.jsonl": [line(day="2026-09-14", time="08:00:00",
                                             u=usage(cr=10000), tool=skill_use("dev-loop")),
                                        line(day="2026-09-14", time="09:00:00",
                                             u=usage(cr=30000))],
                # **スラッシュ起動の周（#108）。** `Skill` の tool_use も
                # Verifier も持たない——**この 2 ファイルが無いと、スラッシュ検出を
                # 落とす変異が「出力が変わらない」で生き残る**。
                # **同じ Issue を 2 セッションに置く**（割れた周）。これが無いと
                # 「Issue で束ねない」変異が殺せない。
                "repo-a/slash1.jsonl": [user_line(slash("555"), day="2026-09-14",
                                                  time="07:00:00"),
                                        line(day="2026-09-14", time="08:00:00",
                                             u=usage(cr=20000, cw=500))],
                "repo-a/slash2.jsonl": [user_line(slash("555"), day="2026-09-14",
                                                  time="09:00:00"),
                                        line(day="2026-09-14", time="09:30:00",
                                             u=usage(cr=60000))],
                # **本文だけの周**——`<command-name>` の条件を外す変異に要る。
                "repo-a/slashbody.jsonl": [user_line("# dev-loop スキル 本文",
                                                     day="2026-09-14"),
                                           line(day="2026-09-14", u=usage(inp=21))],
                # **引数の無い起動**——`or "0"` で代用する変異に要る。
                "repo-a/slashnoarg.jsonl": [user_line(slash(None), day="2026-09-14",
                                                      time="07:10:00"),
                                            line(day="2026-09-14", time="07:20:00",
                                                 u=usage(inp=22))],
                # **起動形とディレクトリ名が食い違う**——優先順を入れ替える変異に要る。
                "repo-a--claude-worktrees-issue-888-x/conf.jsonl": [
                    user_line(slash("999"), day="2026-09-14", time="07:40:00"),
                    line(day="2026-09-14", time="07:50:00", u=usage(inp=23))],
                # **content が list の user 行**——str だけを見る変異に要る。
                "repo-a/slashlist.jsonl": [user_line(slash("666"), day="2026-09-14",
                                                     time="07:05:00", as_list=True),
                                           line(day="2026-09-14", time="07:06:00",
                                                u=usage(inp=24))],
                # **assistant の text に起動形が書かれた行**——`role` を見ない変異に要る。
                # この会話が実際にそうだった（応答の中で起動形を引用した）。
                "repo-a/assistant-mentions.jsonl": [json.dumps(
                    {"type": "assistant", "timestamp": "2026-09-14T07:15:00.000Z",
                     "message": {"model": "claude-opus-5", "role": "assistant",
                                 "usage": {"input_tokens": 25,
                                           "cache_creation_input_tokens": 0,
                                           "cache_read_input_tokens": 0,
                                           "output_tokens": 0},
                                 "content": [{"type": "text", "text": slash("444")}]}},
                    ensure_ascii=False)],
                # **トップレベルが iterations を上回るレコード**——`max` の片側に要る。
                "repo-a/topbig.jsonl": [line(u={"input_tokens": 500,
                                                "cache_creation_input_tokens": 0,
                                                "cache_read_input_tokens": 0,
                                                "output_tokens": 0,
                                                "iterations": [{"input_tokens": 1}]})],
            })
            (tree / "repo-a" / "locked.jsonl").chmod(0o000)
            locked_paths.append(tree / "repo-a" / "locked.jsonl")
            correct = load()
            mutated = load(mscript)
            # **`scan()` の 3 つだけを比べると、`main()` / `render_*` / `iso_week` /
            # `fmt_m` の変異が全部生き残る**（#95 のレビューが 12 変異中 8 件の生存を実証）。
            # **出力そのものを比べる**——CLI が返すものが最終的な成果物なので、
            # そこが変わらない変異は「殺せていない」と言うべきである。
            def observe(module):
                # **例外も振る舞いの違いとして数える。** 変異体が落ちるなら、
                # それは「正しい実装と区別がついた」＝殺せたということである。
                # 捕まえないと、テスト全体が変異体の例外で止まる。
                try:
                    return _observe(module)
                except Exception as exc:  # noqa: BLE001
                    return ("例外", type(exc).__name__)

            def _observe(module):
                rec, dev, unread, broke = module.scan(tree)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    for argv in ([], ["--per-cycle"], ["--split"],
                                 ["--since", "2026-09-15"], ["--list-repos"],
                                 # **周の途中に落ちる `--since` と `--per-cycle` の
                                 # 組み合わせ**——起点の切り落とし判定はここでしか見えない。
                                 ["--per-cycle", "--since", "2026-09-16"],
                                 # **Issue 束ね（#108）。** 呼ばないと
                                 # `render_per_issue` の変異が全部生き残る。
                                 ["--per-issue"],
                                 ["--per-issue", "--since", "2026-09-16"],
                                 # **絞りと寄せも呼ぶ。** 呼ばない引数の変異は
                                 # 「出力が変わらない」ので全部生き残る。
                                 ["--repo", "worktrees"], ["--merge-worktrees"],
                                 ["--list-repos", "--merge-worktrees"]):
                        module.main(["--projects", str(tree)] + argv)
                # **帰属も観測する。** 件数・加重・出力だけを見ていると、
                # 「どのセッションに計上したか」を変える変異が生き残る
                # （#95 の 3 パス目で実際に 1 件生き残った）。
                # **`issue` も帰属である。** 入れないと「番号の付け方」を変える変異が
                # 出力に出ないかぎり生き残る（#108）。
                attribution = sorted((r.session, r.day, r.repo, r.is_sub, r.issue)
                                     for r in rec)
                return (len(rec), sum(r.weighted for r in rec), dev, unread, broke,
                        attribution, buf.getvalue())

            check(f"変異を殺せる: {name}", observe(correct) != observe(mutated))

        for locked_path in locked_paths:
            locked_path.chmod(0o644)

        test_elapsed(base, mod)

        print("実環境を対象にしない歯止め")
        try:
            assert_not_real_home(REAL_HOME_PROJECTS)
        except AssertionError:
            check("実ホームの projects を対象にすると落ちる", True)
        else:
            check("実ホームの projects を対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("トークン集計のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
