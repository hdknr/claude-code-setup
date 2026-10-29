#!/usr/bin/env python3
"""`child-cycle.py`（cruise の周を `claude -p` の子プロセスで回す起動口と要約。#491）の回帰テスト。

    python3 scripts/test-child-cycle.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/cruise/scripts/`）。`test-parent-issue.py` と同じ形——
**`dev-loop` はどのリポジトリでも使えるプラグイン**なので、本体は対象リポジトリの `scripts/` に在ることを当てにできない。

**このテストは実環境を触らず、本物の `claude` を起こさない。** 毎回テンポラリに本物の git リポジトリと worktree を作り、
`PATH` の先頭に置いた偽の `claude`（受けた引数・cwd・セッション・標準入力を記録し、試料の stream-json を出す）で当てる
（`assert_not_real_repo` が対象の場所を担保する）。**本物の `claude` の出力の形は見ない**——試料の鍵は
2.1.312 の実測（`references/child-process.md` の「確かめた範囲」）に合わせてある。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が緑であること。本体の docstring の「守る」の行数だけ変異を当て
（**テスト自身に数えさせる**）、終了コードも docstring の表と突き合わせる。
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "child-cycle.py"
LEDGER = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "ledger.py"
NAME = "issue-50"
BRIEF = "あなたは cruise の子である。\n台帳を書かない。\n終わったら親が -p /dev-loop:dev-loop 5 を起こす。\n"  # 別の番号を含む（P1-R8）

failures: list[str] = []

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys, time
with open(os.path.join(os.environ["FAKE_HOME"], "claude-rec-%d.json" % os.getpid()), "w") as f:
    json.dump({"argv": sys.argv[1:], "cwd": os.getcwd(), "sid": os.getsid(0), "stdin": sys.stdin.read()}, f)
src = os.environ.get("FAKE_CLAUDE_OUTPUT")
if src:
    sys.stdout.write(open(src).read())
    sys.stdout.flush()
time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "0")))
"""

INIT = {"type": "system", "subtype": "init", "permissionMode": "auto", "session_id": "s-1",
        "plugins": [{"name": "spec-loop", "version": "0.26.0"}, {"name": "dev-loop", "version": "1.63.6"}]}


def result(turns=1, **extra):
    base = {"type": "result", "subtype": "success", "is_error": False, "num_turns": turns, "total_cost_usd": 0.02,
            "api_error_status": None, "permission_denials": [],
            "subagent_stats": {"spawned": 1, "completed": 1, "killed": {"parent": 0, "user": 0, "system": 0}}}
    base.update(extra)
    return base


def say(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


# 背景の体を待った子は、体の通知の後で result を計 3 つ並べて出し、最後は空（ターン 0・文が空）だった（probe2 の行の順）
FIXTURES = {
    "済んだ（result が 3 つ）": [INIT, say("背景の体を待つ"), say("最後の報告: PR #9"), result(3), result(1), result(0, result="")],
    "最後の result が API の誤り": [INIT, result(3), result(1, api_error_status=529)],
    "result が無い": [INIT, say("途中"), "壊れた行"],
    "成功でない": [INIT, result(5, subtype="error_max_turns", is_error=True)],
    "拒否された操作": [INIT, result(2, permission_denials=[{"tool_name": "Bash", "tool_input": {"command": "git push"}}])],
    "殺された体": [INIT, result(2, subagent_stats={"spawned": 1, "completed": 0, "killed": {"parent": 1, "user": 0, "system": 0}})],
    "利用上限の拒否": [INIT, {"type": "rate_limit_event", "rate_limit_info": {"status": "rejected", "rateLimitType": "seven_day",
                                                                         "resetsAt": 1793269200}}, result(1)],
    "長い文": [INIT, say("あ" * 5000), result(1)],
    "上限が近いだけ": [INIT, {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "rateLimitType": "five_hour"}},
                 {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed_warning", "rateLimitType": "seven_day"}}, result(1)],
}

MUTATIONS = {
    "子を切り離さない": [("start_new_session=True", "start_new_session=False")],
    "子の標準入力を閉じない": [("stdin=subprocess.DEVNULL, ", "")],
    "cwd をメインの作業ツリーにしない": [("cwd=main_tree, stdin", "cwd=None, stdin")],
    "許可モードを既定に任せる": [('launch.add_argument("--permission-mode", required=True)',
                         'launch.add_argument("--permission-mode", default="auto")')],
    "bypassPermissions を拒まない": [('REFUSED_MODES = ("bypassPermissions",)', "REFUSED_MODES = ()")],
    "委譲文の {{ と空を拒まない": [('    if not brief.strip():', '    if False:'), ('    if "{{" in brief:', '    if False:')],
    "走っている子がいても 2 体目を起こす": [('        if is_running(meta["pid"], number):', '        if False:')],
    "起こせなかった記録を残す": [("            leftover.unlink(missing_ok=True)", "            pass")],
    "claude でない pid も走っていると読む": [('    if not any(Path(t).name == "claude" for t in tokens[:2]):\n        return False\n', '')],
    "コマンド全体から番号を探す": [('    return at >= 0 and tokens[at + 1:at + 3] == ["/dev-loop:dev-loop", str(number)]',
                        '    return re.search(rf"/dev-loop:dev-loop {number}(\\s|$)", proc.stdout) is not None')],
    "最初の result を読む": [('last = summary["results"][-1]', 'last = summary["results"][0]'),
                       ('last = results[-1]', 'last = results[0]')],
    "result が無くても済んだと読む": [('return ["result が無い"]', "return []")],
    "要確認の印を見ない": [("    if problems:", "    if False:")],
    "上限が近いだけでも拒否と読む": [('(None, "allowed", "allowed_warning")', '(None,)')],
    "要約の行を切り詰めない": [('return text if len(text) <= limit else text[: limit - 1] + "…"', "return text")],
}


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"child_{id(script)}_{script.stat().st_mtime_ns}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.LEDGER = LEDGER  # 変異の写しはテンポラリにあるので、台帳の場所の決め方は本物を読ませる
    return mod


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def isolate_env(home: Path) -> None:
    """`GIT_*` を外し、`HOME` と git の設定を差し替え、偽の `claude` を `PATH` の先頭に置く——本物の `claude` には届かない。"""
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[key]
    home.mkdir()
    (home / "gitconfig").write_text("[user]\n\temail = t@example.invalid\n\tname = t\n", encoding="utf-8")
    (home / "bin").mkdir()
    fake = home / "bin" / "claude"
    fake.write_text(FAKE_CLAUDE, encoding="utf-8")
    fake.chmod(0o755)
    # **本物の claude が在る PATH の項を外す**——偽物を実行できなくした試料で、後ろの本物に落ちないように
    # （一度、偽物の実行権を外した試料が本物の claude を起こした）
    rest = [p for p in os.environ["PATH"].split(os.pathsep) if p and not os.access(os.path.join(p, "claude"), os.X_OK)]
    os.environ.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
                      FAKE_HOME=str(home), PATH=os.pathsep.join([str(home / "bin"), *rest]))


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def run(mod, argv, chdir):
    """**cwd を渡さずに、プロセスの cwd を移して呼ぶ**——子の cwd がどこから決まるかを見るため。"""
    out, err = io.StringIO(), io.StringIO()
    before = os.getcwd()
    os.chdir(chdir)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = mod.main(argv)
            except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
                return ("例外", type(exc).__name__, "")
    finally:
        os.chdir(before)
    return (rc, out.getvalue(), err.getvalue())


def wait_for(pred, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.05)
    return False


def dead_pid() -> int:
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc.pid


def write_stream(path: Path, events) -> None:
    path.write_text("".join((e if isinstance(e, str) else json.dumps(e, ensure_ascii=False)) + "\n" for e in events),
                    encoding="utf-8")


def plant(main: Path, number: int, pid: int, events, tag: str) -> None:
    """起動口を通さずに記録を置く（終わった子の要約を当てるため）。"""
    d = main / ".claude" / "plans" / f"cruise-{NAME}-children"
    d.mkdir(parents=True, exist_ok=True)
    out = d / f"{number}-{tag}.jsonl"
    write_stream(out, events)
    (d / f"{number}-{tag}.err").write_text("", encoding="utf-8")
    (d / f"{number}-{tag}.json").write_text(json.dumps({"pid": pid, "out": str(out), "err": str(d / f"{number}-{tag}.err")}),
                                            encoding="utf-8")


def stop(pid) -> None:
    with contextlib.suppress(OSError):
        os.kill(pid, signal.SIGKILL)


def scenario(mod, tmp: Path, tag: str) -> dict:
    """全試料を 1 本のリポジトリで走らせ、観測を辞書で返す。**変異の前後で同じ関数を使う。**"""
    o: dict = {}
    home = Path(os.environ["FAKE_HOME"])
    for rec in home.glob("claude-rec-*.json"):
        rec.unlink()
    main = tmp / f"repo-{tag}"
    main.mkdir()
    assert_not_real_repo(main)
    git(main, "init", "-q", "-b", "main")
    git(main, "commit", "-q", "--allow-empty", "-m", "init")
    wt = main / ".claude" / "worktrees" / "w"
    git(main, "worktree", "add", "-q", str(wt), "-b", "issue/50-x")
    sub = wt / "sub"
    sub.mkdir()
    brief = main / ".claude" / "plans" / "brief-50.md"
    brief.parent.mkdir(parents=True, exist_ok=True)
    brief.write_text(BRIEF, encoding="utf-8")
    children = main / ".claude" / "plans" / f"cruise-{NAME}-children"
    started: list[int] = []
    try:
        # 起こす（走り続ける子）
        os.environ.pop("FAKE_CLAUDE_OUTPUT", None)
        os.environ["FAKE_CLAUDE_SLEEP"] = "30"
        t0 = time.time()
        # 親の標準入力に中身を置く——子が継げば読める（P1-R4）
        r, w = os.pipe()
        os.write(w, b"PARENT-INPUT")
        os.close(w)
        saved = os.dup(0)
        os.dup2(r, 0)
        os.close(r)
        try:
            rc, out, err = run(mod, ["launch", NAME, "50", "--brief", str(brief), "--permission-mode", "auto",
                                     "--model", "haiku", "--allowed-tools", "Bash(git status)", "Agent"], sub)
        finally:
            os.dup2(saved, 0)
            os.close(saved)
        o["launch の戻りが速い"] = time.time() - t0 < 5
        m = re.search(r"pid (\d+)", str(out))
        pid = int(m.group(1)) if m else None
        if pid:
            started.append(pid)
        rec_path = home / f"claude-rec-{pid}.json"
        o["launch"] = rc
        rec = json.loads(rec_path.read_text(encoding="utf-8")) if pid and wait_for(rec_path.exists) and wait_for(
            lambda: rec_path.stat().st_size > 0) else {}
        o["引数"] = rec.get("argv")
        o["cwd"] = rec.get("cwd")
        o["別のセッション"] = rec.get("sid") is not None and rec.get("sid") != os.getsid(0)
        o["標準入力は空"] = rec.get("stdin")
        agent = re.search(r"^台帳の agent: claude-p:(.+)$", str(out), re.M)
        o["記録の場所"] = (Path(agent.group(1)).parent == children and Path(agent.group(1)).exists()) if agent else False
        o["worktree に書かない"] = sorted(p.name for p in sub.parent.iterdir())
        # 走っている間
        o["status(走っている)"] = run(mod, ["status", NAME, "50"], main)[0]
        o["2 体目"] = run(mod, ["launch", NAME, "50", "--brief", str(brief), "--permission-mode", "auto"], main)[0]
        o["2 体目の後の記録の数"] = len(list(children.glob("50-*.json")))
        # 番号の境界: #50 が走っていても #5 は走っていない
        plant(main, 5, pid or dead_pid(), [INIT, result(1)], "z")
        o["#5 は走っていない"] = run(mod, ["status", NAME, "5"], main)[0]
        if pid:
            stop(pid)
            wait_for(lambda: run(mod, ["status", NAME, "50"], main)[0] != 1)
        o["status(止めた後)"] = run(mod, ["status", NAME, "50"], main)[0]

        # 起こして、出力を出して終わる子（端から端まで）
        stream = tmp / f"stream-{tag}.jsonl"
        write_stream(stream, FIXTURES["済んだ（result が 3 つ）"])
        os.environ["FAKE_CLAUDE_OUTPUT"] = str(stream)
        os.environ["FAKE_CLAUDE_SLEEP"] = "0"
        rc, out, _ = run(mod, ["launch", NAME, "51", "--brief", str(brief), "--permission-mode", "dontAsk"], main)
        m = re.search(r"pid (\d+)", str(out))
        if m:
            started.append(int(m.group(1)))
        wait_for(lambda: run(mod, ["status", NAME, "51"], main)[0] != 1)
        o["端から端"] = run(mod, ["status", NAME, "51"], main)[:2]

        # 拒む
        os.environ.pop("FAKE_CLAUDE_OUTPUT", None)
        bad = main / ".claude" / "plans" / "brief-bad.md"
        bad.write_text("Issue #{{issue}}\n", encoding="utf-8")
        empty = main / ".claude" / "plans" / "brief-empty.md"
        empty.write_text(" \n", encoding="utf-8")
        o["{{ が残る"] = run(mod, ["launch", NAME, "52", "--brief", str(bad), "--permission-mode", "auto"], main)[0]
        o["空の委譲文"] = run(mod, ["launch", NAME, "52", "--brief", str(empty), "--permission-mode", "auto"], main)[0]
        o["委譲文が無い"] = run(mod, ["launch", NAME, "52", "--brief", str(main / "none.md"), "--permission-mode", "auto"], main)[0]
        o["bypassPermissions"] = run(mod, ["launch", NAME, "52", "--brief", str(brief), "--permission-mode", "bypassPermissions"], main)[0]
        o["許可モードなし"] = run(mod, ["launch", NAME, "52", "--brief", str(brief)], main)[0]
        o["選べない許可モード"] = run(mod, ["launch", NAME, "52", "--brief", str(brief), "--permission-mode", "yolo"], main)[0]
        o["拒んだ後の #52 の記録"] = sorted(p.name for p in children.glob("52-*"))
        o["引数"] = (o["引数"], run(mod, ["status", NAME, "0"], main)[0], run(mod, ["status", "a/b", "1"], main)[0])

        # 起こせない（claude が実行できない）
        fake = home / "bin" / "claude"
        fake.chmod(0o644)
        try:
            if shutil.which("claude") is not None:  # 本物に落ちるなら、起こさずに止める
                raise AssertionError(f"実行できる claude が PATH に残っている: {shutil.which('claude')}")
            o["起こせない"] = run(mod, ["launch", NAME, "53", "--brief", str(brief), "--permission-mode", "auto"], main)[0]
        finally:
            fake.chmod(0o755)
        o["起こせなかった記録"] = sorted(p.name for p in children.glob("53-*"))

        # 判定できない
        o["記録が無い"] = run(mod, ["status", NAME, "99"], main)[0]
        outside = tmp / f"outside-{tag}"
        outside.mkdir()
        o["git の外"] = run(mod, ["status", NAME, "50"], outside)[0]

        # 終わった子の要約（試料ごと）
        for i, (name, events) in enumerate(FIXTURES.items()):
            number = 60 + i
            plant(main, number, dead_pid(), events, "a")
            rc, out, _ = run(mod, ["status", NAME, str(number)], main)
            o[f"要約 {name}"] = (rc, out)
        # pid が居ても claude でなければ走っていない
        sleeper = subprocess.Popen(["sleep", "30"])
        started.append(sleeper.pid)
        plant(main, 80, sleeper.pid, [INIT, result(1)], "a")
        o["claude でない pid"] = run(mod, ["status", NAME, "80"], main)[0]
        # claude でないが、-p の引数がその Issue のもの（P1-V2）
        imposter = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", "-p", "/dev-loop:dev-loop", "81"])
        started.append(imposter.pid)
        plant(main, 81, imposter.pid, [INIT, result(1)], "a")
        o["-p を持つが claude でない pid"] = run(mod, ["status", NAME, "81"], main)[0]
    finally:
        for pid in started:
            stop(pid)
    return o


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t).resolve()
        isolate_env(tmp / "home")
        mod = load()
        o = scenario(mod, tmp, "correct")
        main_tree = tmp / "repo-correct"

        print("起こす（L1・L3）")
        check("launch は 0 で、子の終わりを待たずに戻る", o["launch"] == 0 and o["launch の戻りが速い"])
        check("引数: -p にスラッシュコマンド・stream-json・verbose・名指しした許可モード・委譲文・モデル・最後に --allowedTools",
              o["引数"][0] == ["-p", "/dev-loop:dev-loop 50", "--output-format", "stream-json", "--verbose",
                              "--permission-mode", "auto", "--append-system-prompt", BRIEF, "--model", "haiku",
                              "--allowedTools", "Bash(git status)", "Agent"])
        check("worktree のサブディレクトリから呼んでも、子の cwd はメインの作業ツリー", o["cwd"] == str(main_tree))
        check("子は新しいセッション（親から切り離す）", o["別のセッション"])
        check("子の標準入力は閉じている（空）", o["標準入力は空"] == "")
        check("記録は台帳の隣（.claude/plans/cruise-<名前>-children/）に在り、その場所を出す", o["記録の場所"])
        check("worktree の中には書かない", o["worktree に書かない"] == [".git", "sub"])

        print("\n走っている間（L2・S1）")
        check("status は 1", o["status(走っている)"] == 1)
        check("同じ Issue の 2 体目は 3 で、記録を増やさない", o["2 体目"] == 3 and o["2 体目の後の記録の数"] == 1)
        check("#50 の子の pid でも、#5 の記録からは走っていない（委譲文に「-p /dev-loop:dev-loop 5」があっても）", o["#5 は走っていない"] != 1)
        check("止めた子は走っていない（result が無いので 3）", o["status(止めた後)"] == 3)
        check("pid が居ても claude でなければ走っていない", o["claude でない pid"] == 0)
        check("-p /dev-loop:dev-loop 81 を持っていても claude でなければ走っていない", o["-p を持つが claude でない pid"] == 0)

        print("\n拒む（L2）")
        check("{{ が残る委譲文は 3", o["{{ が残る"] == 3)
        check("空の委譲文は 3", o["空の委譲文"] == 3)
        check("無い委譲文は 3", o["委譲文が無い"] == 3)
        check("bypassPermissions は 3", o["bypassPermissions"] == 3)
        check("許可モードなし・選べない許可モードは 2", (o["許可モードなし"], o["選べない許可モード"]) == (2, 2))
        check("拒んだら記録を残さない", o["拒んだ後の #52 の記録"] == [])
        check("番号が 0・名前に区切りは 2", o["引数"][1:] == (2, 2))
        check("claude を起こせなければ 4 で、記録を残さない", o["起こせない"] == 4 and o["起こせなかった記録"] == [])
        check("記録が無い・git の外は 4", (o["記録が無い"], o["git の外"]) == (4, 4))

        print("\n要約（S2〜S5）")
        rc, out = o["端から端"]
        check("端から端: 終わった子は 0", rc == 0)
        check("result を 3 つ数え、最後の result（ターン 0）を読む", "result: 3 個 ／ 最後: success・is_error=False・ターン 0" in str(out))
        check("dev-loop の版・許可モード・セッションを出す", "dev-loop の版: 1.63.6 ／ 許可モード: auto ／ セッション: s-1" in str(out))
        check("最後の文は最後の assistant の文（最後の result の文は空）", "最後の文: 最後の報告: PR #9" in str(out))
        expected = {"済んだ（result が 3 つ）": 0, "最後の result が API の誤り": 3, "result が無い": 3, "成功でない": 3,
                    "拒否された操作": 3, "殺された体": 3, "利用上限の拒否": 3, "長い文": 0, "上限が近いだけ": 0}
        for name, code in expected.items():
            check(f"{name} は {code}", o[f"要約 {name}"][0] == code)
        check("拒否された操作の道具の名前を出す", "拒否された操作: Bash" in o["要約 拒否された操作"][1])
        check("利用上限の種類を出す", "利用上限: rejected（seven_day" in o["要約 利用上限の拒否"][1])
        check("読めなかった行を数える", "読めなかった行: 1" in o["要約 result が無い"][1])
        check("長い文を切り詰める（要約は 1500 文字未満）", len(o["要約 長い文"][1]) < 1500)

        print("\n終了コードが docstring の表と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", table, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_RUNNING, mod.EXIT_USAGE, mod.EXIT_REJECTED, mod.EXIT_UNKNOWN}
        check(f"表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)

        print("\n変異テスト（壊したのに緑なら失格）")
        for name, pairs in MUTATIONS.items():
            mutated = source
            missing = [n for n, _ in pairs if n not in mutated]
            if missing:
                check(f"変異を当てる先がある: {name}: {missing}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d = tmp / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "child-cycle.py"
            broken.write_text(mutated, encoding="utf-8")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**（test-parent-issue.py と同じ）
            try:
                mutant = load(broken)
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, tmp, f"mut-{abs(hash(name))}")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            # **最初の launch が通らない変異は「殺せた」ではなく「当てられなかった」**——一度、変異の写しが
            # 台帳の決め方を読めずに全部の launch が 4 になり、12 件とも違う理由で「殺せた」と出た
            if got.get("launch") != 0:
                check(f"変異の最初の launch が通る（当てられなかった）: {name}: {got.get('launch')}", False)
                continue
            got_cmp = {k: v for k, v in got.items() if k not in ("cwd",)}
            want_cmp = {k: v for k, v in o.items() if k not in ("cwd",)}
            # cwd はリポジトリごとに違うので、メインの作業ツリーからの相対で比べる
            rel = lambda v, tag: None if v is None else os.path.relpath(v, tmp / tag)
            same_cwd = rel(got.get("cwd"), f"repo-mut-{abs(hash(name))}") == rel(o.get("cwd"), "repo-correct")
            check(f"変異を殺せる: {name}", not (same_cwd and normalize(got_cmp) == normalize(want_cmp)))

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [l for l in body.splitlines() if l.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("子プロセスの起動口と要約のテスト: すべて合格")
    return 0


def normalize(obs: dict) -> dict:
    """リポジトリごとに違うパスと pid を、観測から外す（変異の前後で比べるため）。"""
    out = {}
    for key, value in obs.items():
        text = json.dumps(value, ensure_ascii=False, default=str)
        text = re.sub(r"/[^\s\"']*?/repo-[^/\s\"']+", "<repo>", text)
        text = re.sub(r"pid \d+", "pid N", text)
        text = re.sub(r"\d{8}T\d{12}Z", "<時刻>", text)
        out[key] = text
    return out


if __name__ == "__main__":
    raise SystemExit(main())
