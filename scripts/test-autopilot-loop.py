#!/usr/bin/env python3
"""`autopilot-loop.py`（spec-loop の autopilot の外側のループ。#850）の回帰テスト。

    python3 scripts/test-autopilot-loop.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-autopilot-ledger.py` と同じ形。

**このテストは実環境を触らず、本物の `claude` を起こさない。** 毎回テンポラリに本物の git リポジトリと worktree を作り、
台帳は**本物の `autopilot-ledger.py`** で作る（`assert_not_real_repo` が対象の場所を担保する）。`PATH` の先頭に偽の `claude`（受けた引数・cwd・
環境の `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`・`CLAUDE_CODE_OAUTH_TOKEN` を記録し、試料の筋書きどおりに本物の台帳のスクリプトで台帳を書き換え、
決めた行を標準出力・標準エラーに出して、決めた終了コードで終わる）と偽の `osascript`（受けた本文を記録する）、長期トークンの起動口を回すための
偽の `security`（決まった値を返す——本物のキーチェーンに届かない）・偽の `uname`（`Darwin` と答える）を置く。
**本物の `claude` が在る `PATH` の項は外す**——偽物が実行できなくても本物に落ちない。使用量の上限の待ちは本体の `pause` を差し替えて、
**待った秒数を記録するだけで眠らない**。

**写しの突き合わせ**: `notify`・`stop_child` は cruise の `outer-loop.py` の写しである（本体の docstring）——2 つのソースが同じことも見る
（陽性対照として、1 文字変えた写しで「違う」と出ることも見る）。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が緑であること。本体の docstring の「守る」の行数だけ変異を当て
（**テスト自身に数えさせる**）、終了コードも docstring の表と突き合わせる。
"""
import ast
import concurrent.futures
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
SCRIPT = REAL_REPO / "plugins" / "spec-loop" / "scripts" / "autopilot-loop.py"
LEDGER = REAL_REPO / "plugins" / "spec-loop" / "scripts" / "autopilot-ledger.py"
CRUISE_LOOP = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "outer-loop.py"
LONG_TOKEN = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "launch-with-long-token.sh"
COPIED = ("notify", "stop_child")
TOKEN = "fake-long-token-850"
CONTROL = "（陽性対照）"

failures: list[str] = []

# 偽の claude: 起動を記録し、筋書き（FAKE_PLAN の版ごとの起動の並び。尽きたら最後の要素を繰り返す）どおりに台帳を書き換え、行を出す
FAKE_CLAUDE = r"""#!/usr/bin/env python3
import json, os, re, signal, subprocess, sys, time
home = os.environ["FAKE_HOME"]
prompt = sys.argv[sys.argv.index("-p") + 1]
version = re.search(r"autopilot (\d+)", prompt).group(1)
log = os.path.join(home, "claude-%s.jsonl" % version)
n = sum(1 for _ in open(log)) if os.path.exists(log) else 0
with open(log, "a") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
                        "bg": os.environ.get("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"),
                        "token": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"),
                        "stdin": sys.stdin.read() if sys.stdin else None}) + "\n")
if n >= 60:  # 暴走の歯止め——正しい本体はどの試料でも 20 回を超えない。上限を外した変異で試料が終わらないのを、台帳を止めて終わらせる（観測は 3 になって違う）
    subprocess.run([os.environ["FAKE_PY"], os.environ["FAKE_LEDGER"], "set", version, "status=stopped", "reason=暴走", "next=試料"],
                   check=True, capture_output=True)
    sys.exit(0)
plan = json.load(open(os.environ["FAKE_PLAN"]))[version]
step = plan[min(n, len(plan) - 1)]
for args in step.get("ledger", []):
    subprocess.run([os.environ["FAKE_PY"], os.environ["FAKE_LEDGER"], *args], check=True, capture_output=True)
if step.get("corrupt"):
    out = subprocess.run([os.environ["FAKE_PY"], os.environ["FAKE_LEDGER"], "path", version],
                         check=True, capture_output=True, text=True).stdout.strip()
    open(out, "w").write("{壊れた")
reset = int(time.time()) + step.get("reset_in", 0)
for line in step.get("stdout", []):
    print(line.replace("RESET", str(reset)))
for line in step.get("stderr", []):
    print(line.replace("RESET", str(reset)), file=sys.stderr)
sys.stdout.flush()
if step.get("hang"):  # SIGTERM を受けたら印を書いて終わる（後始末の代わり）
    def on_term(*_):
        open(os.path.join(home, "term-%s" % version), "w").close()
        sys.exit(143)
    signal.signal(signal.SIGTERM, on_term)
if step.get("kill_parent"):  # 外側のループ（このテストのプロセス）にシグナルを送る
    os.kill(os.getppid(), getattr(signal, step["kill_parent"]))
if step.get("hang"):
    time.sleep(step.get("sleep", 30))
sys.exit(step.get("rc", 0))
"""

FAKE_OSASCRIPT = r"""#!/usr/bin/env python3
import json, os, sys
with open(os.path.join(os.environ["FAKE_HOME"], "notify.jsonl"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
"""

# 偽の security: `find-generic-password … -w` に決まった値を返す（本物のキーチェーンに届かない）
FAKE_SECURITY = "#!/bin/sh\ncase \" $* \" in *\" -w \"*) echo " + TOKEN + " ;; esac\nexit 0\n"
FAKE_UNAME = "#!/bin/sh\necho Darwin\n"


def ev(kind, **kw):
    return json.dumps({"type": kind, **kw})


def rejected(**kw):
    return ev("rate_limit_event", rate_limit_info={"status": "rejected", "rateLimitType": "five_hour", **kw})


MUTATIONS = {
    "止まった・判定できないでも起こす": [
        ("        if code == 3:\n", "        if code == 99:\n"),
        ('        if code != 0:\n            return EXIT_UNKNOWN, f"判定できなかった（status: {code}）"\n', "")],
    "台帳のファイルのまま比べる": [
        ('def progress(version):\n    code, out = ledger("progress", version)\n    return out if code == 0 else None\n',
         'def progress(version):\n    code, out = ledger("path", version)\n    return Path(out.strip()).read_bytes() if code == 0 else None\n')],
    "progress を読めなくても続ける": [("    return out if code == 0 else None\n", '    return out if code == 0 else ""\n')],
    "前進なしで止めない": [("            if stalls >= args.max_stalls:\n", "            if False:\n")],
    "前進で前進なしの数を戻さない": [("        else:\n            stalls = 0\n", "        else:\n            pass\n")],
    "起動の上限で止めない": [("        if launches >= args.max_launches:\n", "        if False:\n")],
    "同じ状態の上限で止めない": [("        if seen.get(before, 0) >= args.max_same_state:\n", "        if False:\n")],
    "claude の失敗で止めない": [("        if rc != 0:\n", "        if rc is None:\n")],
    "上限を claude の失敗と読む": [("        if limited:\n", "        if False:\n")],
    "解除の時刻に余白を足さない": [("                wait = max(0.0, reset - time.time()) + LIMIT_MARGIN\n",
                                 "                wait = max(0.0, reset - time.time())\n")],
    "時刻が読めないとき待たない": [("                wait = args.limit_wait\n", "                wait = 0\n")],
    "解除が遠くても待つ": [("            if wait > args.max_limit_wait:\n", "            if False:\n")],
    "上限の起動を同じ状態に数える": [
        ("        rc, files = launch(args, main_tree, logs, launches)\n",
         "        rc, files = launch(args, main_tree, logs, launches)\n        seen[before] = seen.get(before, 0) + 1\n"),
        ("        seen[before] = seen.get(before, 0) + 1\n        if after == before:\n", "        if after == before:\n")],
    "allowed_warning を上限と読む": [('OK_LIMIT_STATUSES = (None, "allowed", "allowed_warning")', 'OK_LIMIT_STATUSES = (None, "allowed")')],
    "最初の rate_limit_event で決める": [
        ('                last_event = event.get("rate_limit_info") or {}\n',
         '                last_event = last_event if last_event else (event.get("rate_limit_info") or {})\n')],
    "済んだときは通知しない": [("    notify(line)\n", "    if code != EXIT_DONE:\n        notify(line)\n")],
    "cwd をメインの作業ツリーにしない": [("cwd=main_tree, stdin", "cwd=None, stdin")],
    "上限 0 を置かない": [('    env[BG_CEILING] = "0"\n', "    pass\n")],
    "追記を渡さない": [('           "--append-system-prompt", APPEND, *args.extra]', "           *args.extra]")],
    "stream-json で起こさない": [('"--output-format", "stream-json", "--verbose",\n', "\n")],
    "--claude の先頭の語だけ使う": [('    cmd = [*args.claude_cmd, "-p"', '    cmd = [args.claude_cmd[0], "-p"')],
    "先頭 0 の版を通す": [('r"[1-9][0-9]*", args.version', 'r"[0-9]+", args.version')],
    "無視させられたシグナルにもハンドラを置く": [("\n             if signal.getsignal(s) != signal.SIG_IGN}", "}")],
    "中断でいきなり SIGKILL": [("        proc.terminate()\n", "        proc.kill()\n")],
    "写しを書き換える": [("        proc.wait(timeout=GRACE)\n", "        proc.wait(timeout=GRACE + 0)\n")],
}


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"autoloop_{id(script)}_{script.stat().st_mtime_ns}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.LEDGER = LEDGER  # 変異の写しはテンポラリにあるので、台帳は本物の autopilot-ledger.py で読む
    return mod


def functions(source: str) -> dict:
    tree = ast.parse(source)
    return {n.name: ast.get_source_segment(source, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in COPIED}


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
    """`GIT_*`・先に使われる認証を外し、`HOME` と git の設定を差し替え、偽物を `PATH` の先頭に置く。"""
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[key]
    for key in ("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"):
        os.environ.pop(key, None)
    home.mkdir()
    (home / "gitconfig").write_text("[user]\n\temail = t@example.invalid\n\tname = t\n", encoding="utf-8")
    (home / "bin").mkdir()
    for name, body in (("claude", FAKE_CLAUDE), ("osascript", FAKE_OSASCRIPT), ("security", FAKE_SECURITY), ("uname", FAKE_UNAME)):
        fake = home / "bin" / name
        fake.write_text(body, encoding="utf-8")
        fake.chmod(0o755)
    rest = [p for p in os.environ["PATH"].split(os.pathsep) if p and not os.access(os.path.join(p, "claude"), os.X_OK)]
    os.environ.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
                      FAKE_HOME=str(home), FAKE_PY=sys.executable, FAKE_LEDGER=str(LEDGER),
                      PATH=os.pathsep.join([str(home / "bin"), *rest]))


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def ledger(root, *args):
    return subprocess.run([sys.executable, str(LEDGER), *args], cwd=root, capture_output=True, text=True).returncode


def run(mod, argv, chdir):
    """**cwd を渡さずに、プロセスの cwd を移して呼ぶ**——`claude` の cwd がどこから決まるかを見るため。"""
    out, err = io.StringIO(), io.StringIO()
    before = os.getcwd()
    os.chdir(chdir)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                rc = mod.main(argv)
            except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
                return ("例外", type(exc).__name__)
    finally:
        os.chdir(before)
    last = (out.getvalue().strip().splitlines() or [""])[-1]
    return (rc, last)


def records(home: Path, version: int) -> list:
    path = home / f"claude-{version}.jsonl"
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def notes(home: Path) -> list:
    path = home / "notify.jsonl"
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def scenario(mod, tmp: Path, tag: str) -> dict:
    """全試料を 1 本のリポジトリで走らせ、観測を辞書で返す。**変異の前後で同じ関数を使う。**"""
    home = Path(os.environ["FAKE_HOME"])
    root = tmp / f"repo-{tag}"
    assert_not_real_repo(root)
    root.mkdir()
    git(root, "init", "-q")
    (root / "README").write_text("x\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "init")
    wt = root / ".claude" / "worktrees" / "w"
    git(root, "worktree", "add", "-q", str(wt), "-b", "w")
    (wt / "sub").mkdir()
    for f in [*home.glob("claude-*.jsonl"), *home.glob("notify.jsonl"), *home.glob("term-*")]:
        f.unlink()

    o = {}
    # 写しの突き合わせ（この関数に渡された本体のソースで見る）
    mine, theirs = functions(Path(mod.__file__).read_text(encoding="utf-8")), functions(CRUISE_LOOP.read_text(encoding="utf-8"))
    o["写しが一致する"] = {name: mine.get(name) == theirs.get(name) and mine.get(name) is not None for name in COPIED}

    waits: list = []

    def record_pause(seconds):
        waits.append(seconds)
    mod.pause = record_pause

    def make(v, **sets):
        assert ledger(root, "init", str(v)) == 0
        if sets:
            assert ledger(root, "set", str(v), *[f"{k}={val}" for k, val in sets.items()]) == 0

    def stage(v, s):
        return ["set", str(v), f"stage={s}"]

    def done(v):
        return ["set", str(v), "phase=done", "status=done"]

    plan = {}
    plan_path = tmp / f"plan-{tag}.json"
    os.environ["FAKE_PLAN"] = str(plan_path)

    def go(key, v, argv, chdir=root):
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        before, w0 = len(notes(home)), len(waits)
        r = run(mod, [str(v), *argv], chdir)
        r = (r[0], r[1].replace(str(root), "<root>"))
        o[key] = (r, len(records(home, v)), len(notes(home)) - before)
        o[key + " 待ち"] = waits[w0:]

    # A1: 起動のたびに 1 段進め、最後に done → 0。足す引数を渡す・worktree のサブディレクトリから呼ぶ・利用者の上限を上書きする
    make(1)
    plan["1"] = [{"ledger": [stage(1, "round1")]}, {"ledger": [stage(1, "fix1")]}, {"ledger": [done(1)]}]
    os.environ["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"] = "600000"
    go("A1 前進して済む", 1, ["--", "--model", "sonnet"], chdir=wt / "sub")
    del os.environ["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"]
    rec = records(home, 1)
    o["A1 引数"] = [r["argv"] for r in rec]
    o["A1 cwd"] = [os.path.relpath(r["cwd"], root) for r in rec]
    o["A1 上限"] = [r["bg"] for r in rec]
    o["A1 標準入力"] = [r["stdin"] for r in rec]
    o["A1 出力の置き場"] = sorted(p.suffix for p in (root / ".claude" / "plans" / "spec-autopilot-v1-loop").iterdir())

    # A2: 時刻だけを書き換える（同じ段を書き直す——updated だけ変わる）→ 前進なし 2 回で 6。台帳のファイルは変わっている（陽性対照）
    make(2)
    plan["2"] = [{"ledger": [stage(2, "planner")]}]
    path2 = root / ".claude" / "plans" / "spec-autopilot-v2.json"
    snap = path2.read_bytes()
    time.sleep(1.1)  # updated は秒の粒度——同じ秒に書くと陽性対照が成り立たない
    go("A2 時刻だけ", 2, [])
    o["A2 ファイルは変わった"] = path2.read_bytes() != snap

    # A3: 前進なしと前進が交互 → 続けてではないので止まらず、済む（0）
    make(3)
    plan["3"] = [{"ledger": [stage(3, "planner")]}, {"ledger": [stage(3, "round1")]}, {"ledger": [stage(3, "round1")]},
                 {"ledger": [stage(3, "fix1")]}, {"ledger": [done(3)]}]
    go("A3 交互", 3, [])

    # A4: 前進が続くが起動の上限 2 回 → 7
    make(4)
    plan["4"] = [{"ledger": [stage(4, s)]} for s in ("round1", "fix1", "round2", "narrow")]
    go("A4 起動の上限", 4, ["--max-launches", "2"])

    # A5: 段を行き来させる（planner ↔ fix1）→ progress は毎回変わるが、同じ状態から 3 回で 9（#858 の C1-5）
    make(5)
    plan["5"] = [{"ledger": [stage(5, "fix1")]}, {"ledger": [stage(5, "planner")]}] * 10
    go("A5 行き来", 5, [])

    # A6: エージェントが周の途中で stopped を書く → 次の判定で 3（起動 1）
    make(6)
    plan["6"] = [{"ledger": [["set", "6", "status=stopped", "reason=マージが拒まれた", "next=許可を足す"]]}]
    go("A6 止まる", 6, [])

    # A7: 最初から stopped（phase は spec-review のまま——#790 の形）→ 起こさずに 3
    make(7, status="stopped", reason="権限", next="許可")
    plan["7"] = [{"ledger": [done(7)]}]
    go("A7 最初から止まっている", 7, [])

    # A8: 最初から done → 起こさずに 0
    make(8, phase="done", status="done")
    plan["8"] = [{}]
    go("A8 済んでいる", 8, [])

    # A9: 台帳が無い → 4。起こさない
    plan["9"] = [{}]
    go("A9 台帳が無い", 9, [])

    # A10: claude が 1 で終わり、上限の印が無い → 8（起動 1）
    make(10)
    plan["10"] = [{"rc": 1, "stdout": [ev("result", subtype="error_during_execution", is_error=True, result="何か")]}]
    go("A10 claude が失敗", 10, [])

    # A11: claude を起こせない → 8
    make(11)
    go("A11 claude が無い", 11, ["--claude", str(tmp / "no-such-claude")])

    # A12: 使用量の上限（rate_limit_event の resetsAt）→ 解除＋余白まで待って再開し、済む（0）
    make(12)
    plan["12"] = [{"rc": 1, "reset_in": 1000, "stdout": [rejected().replace('}}', ', "resetsAt": RESET}}')]}, {"ledger": [done(12)]}]
    go("A12 上限（resetsAt）", 12, [])

    # A13: 上限の文言だけ（時刻なし）→ --limit-wait 秒待つ
    make(13)
    plan["13"] = [{"rc": 1, "stdout": ["Claude AI usage limit reached. Try again later."]}, {"ledger": [done(13)]}]
    go("A13 上限（時刻なし）", 13, ["--limit-wait", "123"])

    # A14: result の 429 → 上限（時刻なし）
    make(14)
    plan["14"] = [{"rc": 1, "stdout": [ev("result", subtype="error_during_execution", is_error=True, api_error_status=429, result="x")]},
                  {"ledger": [done(14)]}]
    go("A14 上限（429）", 14, ["--limit-wait", "77"])

    # A15: 標準エラーの `usage limit reached|<epoch>` → その時刻まで
    make(15)
    plan["15"] = [{"rc": 1, "reset_in": 500, "stderr": ["Claude AI usage limit reached|RESET"]}, {"ledger": [done(15)]}]
    go("A15 上限（文言の時刻）", 15, [])

    # A16: 解除が遠い（10 日後）→ 待たずに 10
    make(16)
    plan["16"] = [{"rc": 1, "reset_in": 864000, "stdout": [rejected().replace('}}', ', "resetsAt": RESET}}')]}, {"ledger": [done(16)]}]
    go("A16 解除が遠い", 16, [])

    # A17: allowed_warning は上限ではない → 8
    make(17)
    plan["17"] = [{"rc": 1, "stdout": [ev("rate_limit_event", rate_limit_info={"status": "allowed_warning", "resetsAt": 1})]}]
    go("A17 allowed_warning", 17, [])

    # A18: アシスタントの文に「usage limit reached」→ 上限と読まない → 8
    make(18)
    plan["18"] = [{"rc": 1, "stdout": [ev("assistant", message={"content": [{"type": "text", "text": "#790 は usage limit reached で止まった"}]})]}]
    go("A18 アシスタントの文", 18, [])

    # A19: 拒まれた後に allowed に戻った → 最後で決める → 8
    make(19)
    plan["19"] = [{"rc": 1, "stdout": [rejected(resetsAt=1), ev("rate_limit_event", rate_limit_info={"status": "allowed"})]}]
    go("A19 最後は allowed", 19, [])

    # A20: 上限の起動は前進なしにも同じ状態にも数えない（上限 1 でも 2 回の上限を越えて済む）
    make(20)
    plan["20"] = [{"rc": 1, "stdout": ["usage limit reached"]}, {"rc": 1, "stdout": ["usage limit reached"]}, {"ledger": [done(20)]}]
    go("A20 上限は数えない", 20, ["--max-same-state", "1", "--max-stalls", "1", "--limit-wait", "0"])

    # A21: 上限が続いても起動の上限で止まる → 7
    make(21)
    plan["21"] = [{"rc": 1, "stdout": ["usage limit reached"]}]
    go("A21 上限が続く", 21, ["--max-launches", "3", "--limit-wait", "0"])

    # A22: 待ちの中の中断 → 130 と通知
    make(22)
    plan["22"] = [{"rc": 1, "stdout": ["usage limit reached"]}]

    def interrupt_pause(_seconds):
        raise KeyboardInterrupt
    mod.pause = interrupt_pause
    try:
        go("A22 待ちの中の中断", 22, [])
    finally:
        mod.pause = record_pause

    # A23: 起動の中の中断・A24: ループの中の例外
    make(23)
    make(24)
    real_launch = mod.launch

    def interrupt(*_):
        raise KeyboardInterrupt

    def boom(*_):
        raise RuntimeError("試料")
    try:
        mod.launch = interrupt
        go("A23 中断", 23, [])
        mod.launch = boom
        go("A24 例外", 24, [])
    finally:
        mod.launch = real_launch

    # A25: claude の実行中に SIGTERM → claude にまず SIGTERM を送り、後始末（印）を待つ
    make(25)
    plan["25"] = [{"hang": True, "kill_parent": "SIGTERM"}]
    go("A25 中断で claude に SIGTERM", 25, [])
    o["A25 claude が SIGTERM を受けた"] = (home / "term-25").exists()
    o["SIGTERM の扱いを戻した"] = signal.getsignal(signal.SIGTERM) == signal.SIG_DFL

    # A26: nohup の形——SIGHUP を無視させて起動し、起動中に SIGHUP が届く → 無視したまま回り、済む（0）
    make(26)
    plan["26"] = [{"ledger": [done(26)], "kill_parent": "SIGHUP"}]
    saved_hup = signal.signal(signal.SIGHUP, signal.SIG_IGN)
    try:
        go("A26 SIGHUP を無視させて起動", 26, [])
        o["A26 SIGHUP は無視のまま"] = signal.getsignal(signal.SIGHUP) == signal.SIG_IGN
    finally:
        signal.signal(signal.SIGHUP, saved_hup)

    # A27: 長期トークンの起動口（本物の launch-with-long-token.sh・偽の security）越しに起こす → claude がトークンと同じ引数を受ける
    make(27)
    plan["27"] = [{"ledger": [done(27)]}]
    go("A27 長期トークン", 27, ["--claude", f"bash {LONG_TOKEN}"])
    o["A27 受けたもの"] = [(r["token"], r["argv"][:2]) for r in records(home, 27)]

    # A28: --prompt で起こす文を置き換える
    make(28)
    plan["28"] = [{"ledger": [done(28)]}]
    go("A28 起こす文", 28, ["--prompt", "/spec-loop:autopilot 28 --absent"])
    o["A28 文"] = [r["argv"][1] for r in records(home, 28)]

    # A29: 起動の後に台帳が壊れる → progress を読めずに 4
    make(29)
    plan["29"] = [{"corrupt": True}]
    go("A29 壊れる", 29, [])

    # A30: 引数が違う → 2。通知しない
    go("A30 引数", 30, ["--max-same-state", "0"])
    limit = sys.get_int_max_str_digits()
    for key, argv in (("先頭 0", ["01"]), ("0", ["0"]), ("番号でない", ["abc"]), ("ASCII でない", ["²"]),
                      ("桁が多すぎる", ["1" * (limit + 1)]), ("負の待ち", ["1", "--limit-wait", "-1"]),
                      ("空の文", ["1", "--prompt", " "]), ("語に分けられない --claude", ["1", "--claude", "a'b"]),
                      ("上限 0", ["1", "--max-launches", "0"])):
        o[f"A30 {key}"] = run(mod, argv, root)[0]
    o["A30 上限ちょうどの桁数（台帳が無いので 4）"] = run(mod, ["1" * limit], root)[0]
    o["A30 通知の数"] = len(notes(home))
    return o


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test-autopilot-loop-")).resolve()  # macOS の /var は /private/var——git と cwd が返す形にそろえる
    saved_env = dict(os.environ)
    try:
        isolate_env(tmp / "home")
        mod = load()
        print("正しい本体")
        o = scenario(mod, tmp, "correct")
        a = lambda key: o[key]  # noqa: E731
        res = lambda key: a(key)[0][0]  # noqa: E731
        check("A1 前進が続けば済むまで回し、0 で止まる（起動 3・通知 1）", res("A1 前進して済む") == 0 and a("A1 前進して済む")[1:] == (3, 1))
        check("A1 claude の引数は -p・/spec-loop:autopilot 1・stream-json・追記・足す引数",
              all(r == ["-p", "/spec-loop:autopilot 1", "--output-format", "stream-json", "--verbose",
                        "--append-system-prompt", mod.APPEND, "--model", "sonnet"] for r in a("A1 引数")))
        check("A1 worktree のサブディレクトリから呼んでも cwd はメインの作業ツリー", a("A1 cwd") == [".", ".", "."])
        check("A1 利用者の上限 600000 を 0 で上書きする", a("A1 上限") == ["0", "0", "0"])
        check("A1 標準入力は閉じている（空）", a("A1 標準入力") == ["", "", ""])
        check("A1 出力は台帳の隣に起動ごとに残る（.out・.err が 3 つずつ）", a("A1 出力の置き場") == [".err"] * 3 + [".out"] * 3)
        check("A2 時刻だけ書き換える claude は前進なしで、2 回で 6", res("A2 時刻だけ") == 6 and a("A2 時刻だけ")[1:] == (2, 1))
        check("A2 台帳のファイルは変わっていた（陽性対照）", a("A2 ファイルは変わった"))
        check("A3 続けてでない前進なしでは止まらず 0（起動 5）", res("A3 交互") == 0 and a("A3 交互")[1:] == (5, 1))
        check("A4 起動の上限 2 回で 7", res("A4 起動の上限") == 7 and a("A4 起動の上限")[1:] == (2, 1))
        check("A5 段の行き来は同じ状態から 3 回で 9（起動 6）", res("A5 行き来") == 9 and a("A5 行き来")[1:] == (6, 1))
        check("A6 周の途中で stopped を書けば 3（起動 1）で、理由が止まった行に出る",
              res("A6 止まる") == 3 and a("A6 止まる")[1:] == (1, 1) and "マージが拒まれた" in a("A6 止まる")[0][1])
        check("A7 最初から stopped なら phase に依らず起こさずに 3", res("A7 最初から止まっている") == 3 and a("A7 最初から止まっている")[1:] == (0, 1))
        check("A8 最初から done なら起こさずに 0", res("A8 済んでいる") == 0 and a("A8 済んでいる")[1:] == (0, 1))
        check("A9 台帳が無ければ起こさずに 4", res("A9 台帳が無い") == 4 and a("A9 台帳が無い")[1:] == (0, 1))
        check("A10 上限の印の無い失敗は 8（起動 1）", res("A10 claude が失敗") == 8 and a("A10 claude が失敗")[1:] == (1, 1))
        check("A11 claude を起こせなければ 8", res("A11 claude が無い") == 8 and a("A11 claude が無い")[2] == 1)
        w12 = a("A12 上限（resetsAt） 待ち")
        check("A12 rate_limit_event の上限は解除＋60 秒待って再開し、0（起動 2）",
              res("A12 上限（resetsAt）") == 0 and a("A12 上限（resetsAt）")[1:] == (2, 1) and len(w12) == 1 and 1050 <= w12[0] <= 1061)
        check("A13 時刻の無い上限は --limit-wait 秒待って 0", res("A13 上限（時刻なし）") == 0 and a("A13 上限（時刻なし） 待ち") == [123])
        check("A14 result の 429 は上限で、--limit-wait 秒待って 0", res("A14 上限（429）") == 0 and a("A14 上限（429） 待ち") == [77])
        w15 = a("A15 上限（文言の時刻） 待ち")
        check("A15 標準エラーの `limit reached|<epoch>` の時刻＋60 秒待って 0",
              res("A15 上限（文言の時刻）") == 0 and len(w15) == 1 and 550 <= w15[0] <= 561)
        check("A16 解除が遠ければ待たずに 10（起動 1・待ち 0）",
              res("A16 解除が遠い") == 10 and a("A16 解除が遠い")[1:] == (1, 1) and a("A16 解除が遠い 待ち") == [])
        check("A17 allowed_warning は上限でなく 8", res("A17 allowed_warning") == 8 and a("A17 allowed_warning 待ち") == [])
        check("A18 アシスタントの文の「usage limit reached」は上限でなく 8", res("A18 アシスタントの文") == 8 and a("A18 アシスタントの文 待ち") == [])
        check("A19 最後の rate_limit_event が allowed なら上限でなく 8", res("A19 最後は allowed") == 8 and a("A19 最後は allowed 待ち") == [])
        check("A20 上限の起動は前進なし・同じ状態に数えず 0（起動 3・待ち 2）",
              res("A20 上限は数えない") == 0 and a("A20 上限は数えない")[1:] == (3, 1) and a("A20 上限は数えない 待ち") == [0, 0])
        check("A21 上限が続いても起動の上限 3 回で 7", res("A21 上限が続く") == 7 and a("A21 上限が続く")[1:] == (3, 1))
        check("A22 待ちの中の中断は 130 で通知する", res("A22 待ちの中の中断") == 130 and a("A22 待ちの中の中断")[2] == 1)
        check("A23 起動の中の中断は 130 で通知する", res("A23 中断") == 130 and a("A23 中断")[2] == 1)
        check("A24 ループの中の例外は 4 で通知する", res("A24 例外") == 4 and a("A24 例外")[2] == 1)
        check("A25 claude の実行中の SIGTERM は 130 で通知し、claude にまず SIGTERM を送る",
              res("A25 中断で claude に SIGTERM") == 130 and "SIGTERM" in a("A25 中断で claude に SIGTERM")[0][1]
              and a("A25 中断で claude に SIGTERM")[2] == 1 and a("A25 claude が SIGTERM を受けた"))
        check("シグナルの扱いを終わったら戻す", a("SIGTERM の扱いを戻した"))
        check("A26 SIGHUP を無視させて起動すれば、届いても回り続けて 0（起動 1）",
              res("A26 SIGHUP を無視させて起動") == 0 and a("A26 SIGHUP を無視させて起動")[1:] == (1, 1) and a("A26 SIGHUP は無視のまま"))
        check("A27 長期トークンの起動口越しに、claude がトークンと -p の引数を受けて 0",
              res("A27 長期トークン") == 0 and a("A27 受けたもの") == [(TOKEN, ["-p", "/spec-loop:autopilot 27"])])
        check("A28 --prompt で起こす文を置き換える", res("A28 起こす文") == 0 and a("A28 文") == ["/spec-loop:autopilot 28 --absent"])
        check("A29 起動の後に progress を読めなければ 4", res("A29 壊れる") == 4 and "progress を読めない" in a("A29 壊れる")[0][1])
        check("A30 引数が違えば 2 で通知しない", res("A30 引数") == 2 and a("A30 引数")[1:] == (0, 0)
              and all(a(f"A30 {k}") == 2 for k in ("先頭 0", "0", "番号でない", "ASCII でない", "桁が多すぎる", "負の待ち",
                                                   "空の文", "語に分けられない --claude", "上限 0")))
        check("A30 int() の上限ちょうどの桁数は通る（台帳が無いので 4）", a("A30 上限ちょうどの桁数（台帳が無いので 4）") == 4)
        check("止まった行に版と理由が出る", a("A2 時刻だけ")[0][1].startswith("autopilot の外側のループ: 止まった（v2: 前進なしが続けて 2 回"))
        body = notes(Path(os.environ["FAKE_HOME"]))
        check("通知の本文は argv で渡す（スクリプトに埋め込まない）",
              bool(body) and all(n[0] == "-e" and "autopilot" not in n[1] and n[2].startswith("autopilot の外側のループ: 止まった") for n in body))
        check(f"写し {', '.join(COPIED)} が cruise の outer-loop.py と一致する", all(a("写しが一致する").values()))

        print("\n写しの突き合わせの陽性対照")
        theirs = functions(CRUISE_LOOP.read_text(encoding="utf-8"))
        changed = functions(SCRIPT.read_text(encoding="utf-8").replace("proc.terminate()", "proc.terminate( )"))
        check("1 文字変えた写しは「違う」と出る", changed["stop_child"] != theirs["stop_child"])

        print("\n終了コードが docstring の表と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", table, re.M)}
        defined = {getattr(mod, n) for n in dir(mod) if n.startswith("EXIT_")}
        check(f"表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)

        print("\n変異テスト（壊したのに緑なら失格）")
        # 1 つの試料の組に 40 秒ほど掛かるので、変異ごとに別のプロセス（`--observe`）で並列に観測する。各プロセスは自分のテンポラリと環境を持つ
        jobs = {}
        for name, pairs in MUTATIONS.items():
            mutated = source
            missing = [n for n, _ in pairs if n not in mutated]
            if missing:
                check(f"変異を当てる先がある: {name}: {missing}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement, 1)
            d = tmp / f"mut-{len(jobs)}"
            d.mkdir()
            broken = d / "autopilot-loop.py"
            broken.write_text(mutated, encoding="utf-8")
            jobs[name] = broken
        # 陽性対照: 壊さない本体を同じ経路で観測し、このプロセスの観測と一致すること（観測の経路そのものが差を作らない）
        jobs[CONTROL] = SCRIPT
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, os.cpu_count() or 1)) as pool:
            results = dict(zip(jobs, pool.map(lambda item: observe_in_process(*item, saved_env), enumerate(jobs.values()))))
        expected = normalize(o)
        control = results.pop(CONTROL)
        check("陽性対照: 壊さない本体を別のプロセスで観測しても同じ", control == expected)
        for name, got in results.items():
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**
            if got == "load-error":
                check(f"変異を読み込める（当てられなかった）: {name}", False)
            elif got is None:
                check(f"変異を観測できる（当てられなかった）: {name}", False)
            else:
                check(f"変異を殺せる: {name}", got != expected)

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
    finally:
        os.environ.clear()
        os.environ.update(saved_env)
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("autopilot の外側のループのテスト: すべて合格")
    return 0


def normalize(o: dict):
    """比べる形にする——時刻に依る値（待ちの秒数・解除の時刻）を、本体の約束に照らした印に置き換え、JSON の往復でそろえる。"""
    out = dict(o)
    for key, lo, hi in (("A12 上限（resetsAt） 待ち", 1050, 1061), ("A15 上限（文言の時刻） 待ち", 550, 561)):
        out[key] = [lo <= w <= hi for w in o.get(key, [])]
    text = json.dumps(out, ensure_ascii=False, sort_keys=True, default=str)
    text = re.sub(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", "<時刻>", text)
    text = re.sub(r"待ち \d+ 秒", "待ち <秒> 秒", text)
    return json.loads(text)


def observe_in_process(index: int, script: Path, env: dict):
    """別のプロセスで `--observe` を走らせ、正規化した観測を返す。読み込めなければ "load-error"、観測できなければ None。"""
    out = Path(tempfile.mkdtemp(prefix="test-autopilot-loop-obs-")).resolve() / "o.json"
    try:
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--observe", str(script), str(out)],
                           env=env, capture_output=True, text=True, timeout=900)
        if r.returncode == 3:
            return "load-error"
        if r.returncode != 0 or not out.exists():
            return None
        return json.loads(out.read_text(encoding="utf-8"))
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    finally:
        shutil.rmtree(out.parent, ignore_errors=True)


def observe(script: Path, out: Path) -> int:
    """`--observe`: この本体（変異の写しを含む）で全試料を走らせ、正規化した観測を書く。変異で例外になれば、その例外を観測として書く。"""
    tmp = Path(tempfile.mkdtemp(prefix="test-autopilot-loop-w-")).resolve()
    try:
        isolate_env(tmp / "home")
        try:
            mod = load(script)
        except Exception:
            return 3
        try:
            got = normalize(scenario(mod, tmp, "w"))
        except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
            got = {"例外": type(exc).__name__}
        out.write_text(json.dumps(got, ensure_ascii=False), encoding="utf-8")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--observe"]:
        sys.exit(observe(Path(sys.argv[2]), Path(sys.argv[3])))
    sys.exit(main())
