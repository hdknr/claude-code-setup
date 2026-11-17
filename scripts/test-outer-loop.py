#!/usr/bin/env python3
"""`outer-loop.py`（cruise を外から繰り返し起こすループ。#791）の回帰テスト。

    python3 scripts/test-outer-loop.py
    python3 scripts/test-outer-loop.py --jobs 1    # 陽性対照と変異を 1 つずつ（check-all.py --jobs 1 が渡す）

**本体はプラグインの中にある**（`plugins/dev-loop/skills/cruise/scripts/`）。`test-child-cycle.py` と同じ形——
**`dev-loop` はどのリポジトリでも使えるプラグイン**なので、本体は対象リポジトリの `scripts/` に在ることを当てにできない。

**このテストは実環境を触らず、本物の `claude` を起こさない。** 毎回テンポラリに本物の git リポジトリと worktree を作り、
台帳は**本物の `ledger.py`** で作る（`assert_not_real_repo` が対象の場所を担保する）。`PATH` の先頭に偽の `claude`（受けた引数・cwd・
環境の `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` を記録し、試料の筋書きどおりに本物の `ledger.py` で台帳を書き換えて、決めた終了コードで終わる）と
偽の `osascript`（受けた本文を記録する）を置く。**本物の `claude` が在る `PATH` の項は外す**——偽物が実行できなくても本物に落ちない。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が緑であること。本体の docstring の「守る」の行数だけ変異を当て
（**テスト自身に数えさせる**）、終了コードも docstring の表と突き合わせる。

**速さ**（#1052）: 本体のままの回をこのプロセスで 1 回走らせて全部の check を当てた後、**陽性対照（壊さない本体）と変異の全部を、
別々のプロセス（`--observe`）で同時に観測する**（`--jobs` で絞る。上限 4。`--jobs 1` で 1 つずつ）。`scenario()` は `os.environ`・
偽の `HOME` の記録・シグナルの扱いを書き換えるので、スレッドではなくプロセスで分ける——各プロセスは自分のテンポラリで `isolate_env` を通り
（偽の `claude` を `PATH` の先頭に置き、本物の `claude` が在る項を外す）、そこで本体を読み込む。形は `test-autopilot-loop.py` の `--observe`。
観測はテンポラリのパスを伏せ、JSON の往復でそろえてから比べる。**陽性対照が、このプロセスの観測と一致しなければ失格**
——観測の経路そのものが差を作っていれば、変異の「違う」は殺せた証拠にならない。
本体のままの回をプールと同時に走らせないのは、`--jobs 1` で直列にするため。

守らないもの:

- **`--jobs` を受けた回のプールの大きさ**は `--pool-size` の経路で見る（`test-parallel-stop.py` と同じ形）。本当の回のプールの数は見ない。
- **観測のプロセスの中の時間切れ**（1 本 1800 秒）は、負荷で延びた回と止まった回を分けない——どちらも「当てられなかった」で失格にする。
"""
import argparse
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
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "outer-loop.py"
LEDGER = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "ledger.py"
CHILD_CYCLE = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "child-cycle.py"

failures: list[str] = []

JOBS_MAX = max(1, min(4, os.cpu_count() or 1))  # 同時に観測するプロセスの数の上限（test-parallel-stop.py と同じ）
JOBS = JOBS_MAX
pool_sizes: list[int] = []  # プールに渡した作業者の数（`--pool-size` が出す）
CONTROL = "（陽性対照: 壊さない本体）"
OBSERVE_TIMEOUT = 1800

# 偽の claude: 起動を記録し、筋書き（FAKE_PLAN の親ごとの起動の並び。尽きたら最後の要素を繰り返す）どおりに台帳を書き換える
FAKE_CLAUDE = r"""#!/usr/bin/env python3
import json, os, re, signal, subprocess, sys, time
home = os.environ["FAKE_HOME"]
parent = re.match(r"/dev-loop:cruise (\d+)", sys.argv[2]).group(1)
log = os.path.join(home, "claude-%s.jsonl" % parent)
n = sum(1 for _ in open(log)) if os.path.exists(log) else 0
with open(log, "a") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
                        "bg": os.environ.get("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS")}) + "\n")
plan = json.load(open(os.environ["FAKE_PLAN"]))[parent]
step = plan[min(n, len(plan) - 1)]
for args in step.get("ledger", []):
    subprocess.run([os.environ["FAKE_PY"], os.environ["FAKE_LEDGER"], *args], check=True, capture_output=True)
# 費用（#992）: 本物の -p と同じく、stream-json を頼まれたときだけ JSON の行を出す
streamed = "--output-format" in sys.argv and sys.argv[sys.argv.index("--output-format") + 1] == "stream-json"
if streamed:
    for line in step.get("stdout", []):
        print(line)
    if "cost" in step:
        print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "total_cost_usd": step["cost"]}))
    sys.stdout.flush()
# 子プロセスの周の記録（child-cycle.py と同じ置き場と形）。finished は終わった子・running は claude の名前で走る子
if step.get("children"):
    path = subprocess.run([os.environ["FAKE_PY"], os.environ["FAKE_LEDGER"], "path", "issue-" + parent],
                          check=True, capture_output=True, text=True).stdout.strip()
    kids = os.path.join(os.path.dirname(path), "cruise-issue-%s-children" % parent)
    os.makedirs(kids, exist_ok=True)
    for i, kid in enumerate(step["children"]):
        number = 700 + i
        if kid.get("running"):
            p = subprocess.Popen([os.environ["FAKE_PY"], os.path.join(home, "child-bin", "claude"), "-p", "/dev-loop:dev-loop", str(number)],
                                 start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(os.path.join(home, "running-pids"), "a") as f:
                f.write("%d\n" % p.pid)
        else:
            p = subprocess.Popen(["true"])
            p.wait()
        base = os.path.join(kids, "%d-2026%04d" % (number, n))
        with open(base + ".jsonl", "w") as f:
            for line in kid.get("stdout", []):
                f.write(line + "\n")
        json.dump({"pid": p.pid, "number": number, "out": base + ".jsonl"}, open(base + ".json", "w"))
if step.get("corrupt"):
    out = subprocess.run([os.environ["FAKE_PY"], os.environ["FAKE_LEDGER"], "path", "issue-" + parent],
                         check=True, capture_output=True, text=True).stdout.strip()
    open(out, "w").write("{壊れた")
if step.get("hang"):  # SIGTERM を受けたら印を書いて終わる（後始末の代わり）。ignore_term なら無視する
    def on_term(*_):
        open(os.path.join(home, "term-%s" % parent), "w").close()
        sys.exit(143)
    signal.signal(signal.SIGTERM, signal.SIG_IGN if step.get("ignore_term") else on_term)
if step.get("kill_parent"):  # 外側のループ（このテストのプロセス）にシグナルを送る
    os.kill(os.getppid(), getattr(signal, step["kill_parent"]))
if step.get("hang"):
    time.sleep(step.get("sleep", 30))
    open(os.path.join(home, "survived-%s" % parent), "w").close()  # SIGKILL されていれば書かれない
sys.exit(step.get("rc", 0))
"""

# 走っている子の代わり: `ps` に `… /claude -p /dev-loop:dev-loop <番号>` と出て、しばらく居る
# FAKE_RELEASE のファイルが現れたら（その試料だけ）早く終わる
FAKE_CHILD = ("#!/usr/bin/env python3\nimport os, time\nr = os.environ.get(\"FAKE_RELEASE\")\nend = time.time() + 120\n"
              "while time.time() < end and not (r and os.path.exists(r)):\n    time.sleep(0.05)\n")

FAKE_OSASCRIPT = r"""#!/usr/bin/env python3
import json, os, sys
with open(os.path.join(os.environ["FAKE_HOME"], "notify.jsonl"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
"""

MUTATIONS = {
    "窓を常に渡す": [("*([] if args.window is None else child_cycle().window_flag(args.window)), ", '"--autocompact", "400000", ')],
    "窓の範囲を検査しない": [("child_cycle().parse_window(args.autocompact_window)", '(lambda t: int(t.rstrip("kK") or 0) * (1000 if t[-1:] in "kK" else 1))(args.autocompact_window)')],
    "環境変数に上書きされても言わない": [("window_override_note(args.window, os.environ)", "window_override_note(args.window, {})")],
    "人待ち・判定できないでも起こす": [
        ("        if code == 3:\n", "        if code == 99:\n"),
        ('        if code != 0:\n            return EXIT_UNKNOWN, f"判定できなかった（status: {code}）"\n', "")],
    "台帳のファイルのまま比べる": [
        ('def progress(name):\n    code, out = ledger("progress", name)\n    return out if code == 0 else None\n',
         'def progress(name):\n    code, out = ledger("path", name)\n    return Path(out.strip()).read_bytes() if code == 0 else None\n')],
    "progress を読めなくても続ける": [("    return out if code == 0 else None\n", '    return out if code == 0 else ""\n')],
    "前進なしで止めない": [("            if stalls >= args.max_stalls:\n", "            if False:\n")],
    "前進で前進なしの数を戻さない": [("        else:\n            stalls = 0\n", "        else:\n            pass\n")],
    "起動の上限で止めない": [("        if launches >= args.max_launches:\n", "        if False:\n")],
    "claude の失敗で止めない": [("        if rc != 0:\n", "        if rc is None:\n")],
    "済んだときは通知しない": [("    notify(line)\n", "    if code != EXIT_DONE:\n        notify(line)\n")],
    "cwd をメインの作業ツリーにしない": [("cwd=main_tree, stdin", "cwd=None, stdin")],
    "上限 0 を置かない": [('    env[BG_CEILING] = "0"\n', "    pass\n")],
    "追記を渡さない": [('"--append-system-prompt", APPEND, ', "")],
    "番号を 18 桁までに狭める": [(r'r"0*([1-9][0-9]*)"', r'r"0*([1-9][0-9]{0,17})"')],
    "int() の上限を超える番号を拒まない": [("(limit and len(number.group(1)) > limit)", "False")],
    "--absent を常に付ける": [('(" --absent" if args.absent else "")', '" --absent"')],
    "無視させられたシグナルにもハンドラを置く": [("\n             if signal.getsignal(s) != signal.SIG_IGN}", "}")],
    "中断でいきなり SIGKILL": [("        proc.terminate()\n", "        proc.kill()\n")],
    "時間切れでも SIGKILL しない": [("        proc.kill()\n        proc.wait()\n", "        proc.wait()\n")],
    "stream-json で起こさない": [('"--output-format", "stream-json", "--verbose",\n', "\n")],
    "最初の result で読む": [("            last = event\n", "            last = last or event\n")],
    "読めない起動を 0 と数える": [("        if cost is None:\n            self.missing.append(n)\n        else:\n            self.known += cost\n",
                                "        self.known += cost or 0.0\n")],
    "真偽値を費用と読む": [("    if not isinstance(value, (int, float)) or isinstance(value, bool):\n",
                         "    if not isinstance(value, (int, float)):\n")],
    "負・有限でない値を費用と読む": [("    return value if math.isfinite(value) and value >= 0 else None\n", "    return value\n")],
    "float に収まらない整数で落ちる": [("    try:\n        value = float(value)\n    except OverflowError:  # 桁の多すぎる整数——例外にせず読めないものとして扱う\n        return None\n",
                                     "    value = float(value)\n")],
    "起こせなかった起動も数える": [("        if rc is not None:\n            costs.add(", "        if True:\n            costs.add(")],
    "ちょうど上限なら起こす": [("            if costs.total() >= args.max_total_usd:\n", "            if costs.total() > args.max_total_usd:\n")],
    "費用を取れなくても上限があれば止めない": [("            if costs.unknown():\n", "            if False:\n")],
    "上限が無くても費用を取れなければ止める": [("        if args.max_total_usd is not None:\n            costs.children",
                                         "        if True:\n            costs.children")],
    "子の費用を数えない": [("            known += cost\n            counted += 1\n", "            counted += 1\n")],
    "起動時に在った子の記録も数える": [("        if meta_path.name in seen:\n            continue\n", "")],
    "走っている子を取れなかったと数える": [("                running.append(label)\n                continue\n",
                                          "                missing.append(label)\n                continue\n")],
    "止まった行に費用を出さない": [('    line += f" 費用: {args.costs.summary()}"\n', "")],
    "中断した起動を数えない": [("            costs.add(launches, None)\n            raise\n", "            raise\n")],
    "止まった行の子を数え直さない": [("    costs.rescan = lambda: child_costs(children, seen)\n", "")],
    "上限の直前に子を数え直さない": [("            costs.children = child_costs(children, seen)  # 前の起動の後に走りきった子も入れて判定する\n", "")],
    "費用の上限を済んだの判定より先に見る": [('        code, out = ledger("status", name)\n        print(f"status:',
                                         '        if args.max_total_usd is not None and costs.total() >= args.max_total_usd:\n            return EXIT_BUDGET, "x"\n'
                                         '        code, out = ledger("status", name)\n        print(f"status:')],
}


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"outer_{id(script)}_{script.stat().st_mtime_ns}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.LEDGER = LEDGER  # 変異の写しはテンポラリにあるので、台帳は本物の ledger.py で読む
    mod.CHILD_CYCLE = CHILD_CYCLE  # 子の記録の読み方も本物の child-cycle.py から
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
    """`GIT_*` を外し、`HOME` と git の設定を差し替え、偽の `claude`・`osascript` を `PATH` の先頭に置く。"""
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[key]
    os.environ.pop("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS", None)
    home.mkdir()
    (home / "gitconfig").write_text("[user]\n\temail = t@example.invalid\n\tname = t\n", encoding="utf-8")
    (home / "bin").mkdir()
    for name, body in (("claude", FAKE_CLAUDE), ("osascript", FAKE_OSASCRIPT)):
        fake = home / "bin" / name
        fake.write_text(body, encoding="utf-8")
        fake.chmod(0o755)
    (home / "child-bin").mkdir()
    (home / "child-bin" / "claude").write_text(FAKE_CHILD, encoding="utf-8")  # PATH には置かない
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


def records(home: Path, parent: int) -> list:
    path = home / f"claude-{parent}.jsonl"
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
    (root / ".claude" / "plans").mkdir(parents=True, exist_ok=True)
    # 親ごとの記録を、試料ごとのリポジトリで分ける
    for f in [*home.glob("claude-*.jsonl"), *home.glob("notify.jsonl"), *home.glob("term-*"), *home.glob("survived-*")]:
        f.unlink()

    def make(parent, rows):
        """rows: (番号, 状態)。本物の ledger.py で作る。"""
        name = f"issue-{parent}"
        assert ledger(root, "init", name) == 0
        for n, state in rows:
            assert ledger(root, "add", name, str(n)) == 0
            if state != "todo":
                assert ledger(root, "set", name, str(n), f"state={state}") == 0

    def merge(parent, n):
        return {"ledger": [["set", f"issue-{parent}", str(n), "state=merged", f"pr=#{n}0"]]}

    def touch(parent, n):
        """進めずに note だけ書き直す（`updated` も変わる）。"""
        return {"ledger": [["set", f"issue-{parent}", str(n), "note=確かめたが変わらず"]]}

    plan = {}
    o = {}
    # 偽の claude だけが PATH に在る（並列の観測のプロセスでも同じこと——陽性対照の一致で見る。#1052）
    o["PATH の claude"] = ["<偽物>" if p == str(home / "bin") else p
                          for p in os.environ["PATH"].split(os.pathsep) if p and os.access(os.path.join(p, "claude"), os.X_OK)]
    plan_path = tmp / f"plan-{tag}.json"
    os.environ["FAKE_PLAN"] = str(plan_path)

    def go(key, parent, argv, chdir=root, mod_=None):
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        before = len(notes(home))
        r = run(mod_ or mod, [str(parent), *argv], chdir)
        r = (r[0], r[1].replace(str(root), "<root>"))
        o[key] = (r, len(records(home, parent)), len(notes(home)) - before)

    # S1: 起動のたびに 1 行ずつ merged にする → 済んだ（0）。--absent と足す引数を渡す・worktree のサブディレクトリから呼ぶ・利用者の上限を上書きする
    make(50, [(1, "todo"), (2, "todo")])
    plan["50"] = [merge(50, 1), merge(50, 2)]
    os.environ["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"] = "600000"
    go("S1 前進して済む", 50, ["--absent", "--", "--model", "sonnet"], chdir=wt / "sub")
    del os.environ["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"]
    rec = records(home, 50)
    o["S1 引数"] = [r["argv"] for r in rec]
    o["S1 cwd"] = [os.path.relpath(r["cwd"], root) for r in rec]
    o["S1 上限"] = [r["bg"] for r in rec]

    # S2: note だけ書き直す起動 → 前進なし 2 回で止まる（6）。ファイルは変わっている（陽性対照）。--absent を渡さない
    make(51, [(1, "todo")])
    plan["51"] = [touch(51, 1)]
    path51 = root / ".claude" / "plans" / "cruise-issue-51.json"
    snap = path51.read_bytes()
    go("S2 note だけ", 51, [])
    o["S2 ファイルは変わった"] = path51.read_bytes() != snap
    o["S2 引数"] = [r["argv"][1] for r in records(home, 51)]
    o["S2 上限"] = [r["bg"] for r in records(home, 51)]

    # W: auto-compact の窓（#1167）。渡したときだけ --autocompact <トークン数>（追記の後・足す引数の前）。環境変数があれば効かないと言う。拒むのは起動の前（通知もしない）
    def go_out(key, parent, argv, env=None):
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        before = len(notes(home))
        os.environ.pop("CLAUDE_CODE_AUTO_COMPACT_WINDOW", None)
        os.environ.update(env or {})
        out_, err_ = io.StringIO(), io.StringIO()
        saved_cwd = os.getcwd()
        os.chdir(root)
        try:
            with contextlib.redirect_stdout(out_), contextlib.redirect_stderr(err_):
                try:
                    rc_ = mod.main([str(parent), *argv])
                except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
                    rc_ = ("例外", type(exc).__name__)
        finally:
            os.chdir(saved_cwd)
            os.environ.pop("CLAUDE_CODE_AUTO_COMPACT_WINDOW", None)
        o[key] = {"rc": rc_, "lines": [l for l in out_.getvalue().splitlines() if "窓" in l], "stderr": err_.getvalue().strip()[:60],
                  "argv": [r["argv"] for r in records(home, parent)], "notify": len(notes(home)) - before}

    make(180, [(1, "todo"), (2, "todo")])
    plan["180"] = [merge(180, 1), merge(180, 2)]
    go_out("W1 窓 400k", 180, ["--autocompact-window", "400k", "--", "--model", "sonnet"])
    make(181, [(1, "todo"), (2, "todo")])
    plan["181"] = [merge(181, 1), merge(181, 2)]
    go_out("W2 窓と環境変数", 181, ["--autocompact-window", "1M"], {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "300000"})
    make(182, [(1, "todo")])
    plan["182"] = [merge(182, 1)]
    go_out("W3 窓なしと環境変数", 182, [], {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "300000"})
    # W5: 拒んだ起動は、台帳があっても出力の置き場を作らない（検査は起動の前）
    make(183, [(1, "todo")])
    plan["183"] = [merge(183, 1)]
    go_out("W5 台帳ありで拒む", 183, ["--autocompact-window", "99999"])
    o["W5 出力の置き場"] = (root / ".claude" / "plans" / "cruise-issue-183-loop").exists()
    for i, bad in enumerate(("400", "99999", "1000001", "4e5", "", "-1", "１００k", "400kk")):
        go_out(f"W4 拒む {bad!r}", 90, ["--autocompact-window", bad])

    # S3: 前進なしと前進が交互 → 続けてではないので止まらず、済む（0）
    make(52, [(1, "todo"), (2, "todo"), (3, "todo")])
    plan["52"] = [touch(52, 1), merge(52, 1), touch(52, 2), merge(52, 2), touch(52, 3), merge(52, 3)]
    go("S3 交互", 52, [])

    # S4: 前進が続くが上限 2 回 → 7
    make(53, [(i, "todo") for i in range(1, 6)])
    plan["53"] = [merge(53, i) for i in range(1, 6)]
    go("S4 上限", 53, ["--max-launches", "2"])

    # S5: claude が 1 で終わる → 8（1 回で止まる）
    make(54, [(1, "todo")])
    plan["54"] = [dict(merge(54, 1), rc=1)]
    go("S5 claude が失敗", 54, [])

    # S6: claude を起こせない → 8
    make(58, [(1, "todo")])
    go("S6 claude が無い", 58, ["--claude", str(tmp / "no-such-claude")])

    # S7: 人待ちだけ（blocked）→ 3。起こさない
    make(55, [(1, "blocked")])
    plan["55"] = [merge(55, 1)]
    go("S7 人待ち", 55, [])

    # S8: 台帳が無い → 4。起こさない
    plan["56"] = [{}]
    go("S8 台帳が無い", 56, [])

    # S9: 最初から済んでいる → 0。起こさない
    make(57, [(1, "merged")])
    plan["57"] = [{}]
    go("S9 済んでいる", 57, [])

    # S10: 起動の後に台帳が壊れる → progress を読めずに 4
    make(59, [(1, "todo")])
    plan["59"] = [{"corrupt": True}]
    go("S10 壊れる", 59, [])

    # S11: 中断（Ctrl-C）→ 130 と通知
    make(60, [(1, "todo")])
    real_launch = mod.launch

    def interrupt(*_):
        raise KeyboardInterrupt
    mod.launch = interrupt
    try:
        go("S11 中断", 60, [])
    finally:
        mod.launch = real_launch

    # S13: SIGTERM → 130 と通知
    make(62, [(1, "todo")])

    def term(*_):
        os.kill(os.getpid(), signal.SIGTERM)
    mod.launch = term
    try:
        go("S13 SIGTERM", 62, [])
    finally:
        mod.launch = real_launch

    # S14: ループの中の予期しない例外 → 4 と通知
    make(63, [(1, "todo")])

    def boom(*_):
        raise RuntimeError("試料")
    mod.launch = boom
    try:
        go("S14 例外", 63, [])
    finally:
        mod.launch = real_launch
    o["SIGTERM の扱いを戻した"] = signal.getsignal(signal.SIGTERM) == signal.SIG_DFL

    # S15: nohup の形——SIGHUP を無視させて起動し、起動中に SIGHUP が届く → 無視したまま回り、済む（0）。#820 と同じ（R2-1）
    make(64, [(1, "todo")])
    plan["64"] = [dict(merge(64, 1), kill_parent="SIGHUP")]
    saved_hup = signal.signal(signal.SIGHUP, signal.SIG_IGN)
    try:
        go("S15 SIGHUP を無視させて起動", 64, [])
        o["S15 SIGHUP は無視のまま"] = signal.getsignal(signal.SIGHUP) == signal.SIG_IGN
    finally:
        signal.signal(signal.SIGHUP, saved_hup)

    # S16: claude の実行中に SIGTERM → claude にまず SIGTERM を送り、後始末（印）を待つ（R2-2）
    make(65, [(1, "todo")])
    plan["65"] = [{"hang": True, "kill_parent": "SIGTERM"}]
    go("S16 中断で claude に SIGTERM", 65, [])
    o["S16 claude が SIGTERM を受けた"] = (home / "term-65").exists()

    # S17: claude が SIGTERM を無視する → GRACE 秒で SIGKILL（3 秒眠った後の印が書かれない）
    make(66, [(1, "todo")])
    plan["66"] = [{"hang": True, "ignore_term": True, "kill_parent": "SIGTERM", "sleep": 3}]
    saved_grace, mod.GRACE = mod.GRACE, 0.5
    try:
        go("S17 SIGTERM を無視する claude", 66, [])
    finally:
        mod.GRACE = saved_grace
    o["S17 claude は残らない"] = not (home / "survived-66").exists()

    # ---- 費用（#992）----
    def cost_step(parent, n, cost, **kw):
        return dict(merge(parent, n), cost=cost, **kw)

    # C1: 1 起動 0.5 ドル・上限 1.0 → 2 回でちょうど上限 → 3 回目を起こさずに 11（行が 1 つ残っている）
    make(70, [(1, "todo"), (2, "todo"), (3, "todo")])
    plan["70"] = [cost_step(70, i, 0.5) for i in (1, 2, 3)]
    go("C1 ちょうど上限", 70, ["--max-total-usd", "1.0"])

    # C2: 上限の下で済む → 0。台帳の progress と台帳のファイルに費用が入らない（陽性対照: 止まった行には出る）
    make(71, [(1, "todo"), (2, "todo")])
    plan["71"] = [cost_step(71, i, 0.25) for i in (1, 2)]
    go("C2 上限の下で済む", 71, ["--max-total-usd", "10"])
    prog = subprocess.run([sys.executable, str(LEDGER), "progress", "issue-71"], cwd=root, capture_output=True, text=True)
    o["C2 progress"] = (prog.returncode, prog.stdout)
    # 台帳のファイルは更新時刻を持つので、そのまま観測に入れない（変異の比べ合いが時刻で必ず違ってしまう）——判定だけ入れる
    o["C2 台帳のファイルに費用が無い"] = not re.search(r"cost|費用|0\.25|0\.5", (root / ".claude" / "plans" / "cruise-issue-71.json").read_text(encoding="utf-8"))
    o["C2 正規表現の陽性対照"] = bool(re.search(r"cost|費用|0\.25|0\.5", "合計 $0.50"))

    # C3: 費用の出ない起動（result が無い）・上限あり → 1 回で 12。C4: 同じ筋書き・上限なし → 止めずに済み、数を出す
    make(72, [(1, "todo"), (2, "todo")])
    plan["72"] = [merge(72, 1), merge(72, 2)]
    go("C3 取れない・上限あり", 72, ["--max-total-usd", "100"])
    make(73, [(1, "todo"), (2, "todo")])
    plan["73"] = [merge(73, 1), cost_step(73, 2, 0.75)]
    go("C4 取れない・上限なし", 73, [])

    # C5: 最後の result だけで読む——前の result に費用があっても、最後に無ければ取れない（上限ありで 12）
    make(74, [(1, "todo"), (2, "todo")])
    first = json.dumps({"type": "result", "total_cost_usd": 3.0})
    last = json.dumps({"type": "result", "subtype": "success"})
    plan["74"] = [dict(merge(74, 1), stdout=[first, last]), merge(74, 2)]
    go("C5 最後の result", 74, ["--max-total-usd", "100"])

    # C6: 真偽値・負・NaN・float に収まらない整数・文字列は費用と読まない（上限なし——4 回とも取れない）
    make(75, [(i, "todo") for i in range(1, 6)])
    weird = ["true", "-1.5", "NaN", "9" * 400, '"0.5"']
    plan["75"] = [dict(merge(75, i), stdout=['{"type": "result", "total_cost_usd": %s}' % v]) for i, v in enumerate(weird, 1)]
    go("C6 読めない値", 75, [])

    # C7: 子プロセスの周——ループの前に在った記録（100 ドル）は数えない。終わった子 0.4・費用の無い子・走っている子
    make(76, [(1, "todo")])
    kids = root / ".claude" / "plans" / "cruise-issue-76-children"
    kids.mkdir(parents=True)
    old = subprocess.Popen(["true"])
    old.wait()
    (kids / "1-old.jsonl").write_text(json.dumps({"type": "result", "total_cost_usd": 100}) + "\n", encoding="utf-8")
    (kids / "1-old.json").write_text(json.dumps({"pid": old.pid, "number": 1, "out": str(kids / "1-old.jsonl")}), encoding="utf-8")
    child_ok = {"stdout": [json.dumps({"type": "result", "total_cost_usd": 0.4})]}
    child_none = {"stdout": [json.dumps({"type": "assistant", "message": {}})]}
    plan["76"] = [cost_step(76, 1, 0.1, children=[child_ok, child_none, {"running": True}])]
    go("C7 子の費用", 76, [])

    # C8: 上限あり・終わった子は費用あり・走っている子 → 走っている子では止めずに済む（0）
    make(77, [(1, "todo"), (2, "todo")])
    plan["77"] = [cost_step(77, 1, 0.1, children=[child_ok, {"running": True}]), cost_step(77, 2, 0.1)]
    go("C8 走っている子では止めない", 77, ["--max-total-usd", "100"])
    pids = home / "running-pids"
    if pids.exists():
        for line in pids.read_text(encoding="utf-8").split():
            with contextlib.suppress(OSError):
                os.kill(int(line), signal.SIGKILL)
        pids.unlink()

    # C10: 最後の起動で済み、合計もちょうど上限 → 済んだが先で 0
    make(79, [(1, "todo"), (2, "todo")])
    plan["79"] = [cost_step(79, i, 0.5) for i in (1, 2)]
    go("C10 済んだのが先", 79, ["--max-total-usd", "1.0"])

    # C11: 起動 1 の後は走っていた子（5 ドル）が、次の判定の前に走りきる → 上限 3 で 2 回目を起こさずに 11
    make(78, [(1, "todo"), (2, "todo")])
    release = tmp / f"release-{tag}"
    os.environ["FAKE_RELEASE"] = str(release)
    child_late = {"running": True, "stdout": [json.dumps({"type": "result", "total_cost_usd": 5.0})]}
    plan["78"] = [cost_step(78, 1, 0.1, children=[child_late]), cost_step(78, 2, 0.1)]
    real_ledger, calls = mod.ledger, {"status": 0}

    def ledger_releasing(*args):
        if args[:1] == ("status",):
            calls["status"] += 1
            if calls["status"] == 2:  # 起動 1 の後の判定の前に、子を走りきらせる
                release.touch()
                pid = int((home / "running-pids").read_text(encoding="utf-8").split()[-1])
                for _ in range(200):
                    try:
                        os.kill(pid, 0)
                    except OSError:
                        break
                    time.sleep(0.05)
        return real_ledger(*args)
    mod.ledger = ledger_releasing
    try:
        go("C11 走りきった子を次の判定に入れる", 78, ["--max-total-usd", "3"])
    finally:
        mod.ledger = real_ledger
        del os.environ["FAKE_RELEASE"]

    # C12: 上限なし・起動の後は走っていた子（5 ドル）が、済んだの判定の前に走りきる → 止まった行は数え直した内訳
    make(80, [(1, "todo")])
    release2 = tmp / f"release2-{tag}"
    os.environ["FAKE_RELEASE"] = str(release2)
    plan["80"] = [cost_step(80, 1, 0.1, children=[child_late])]
    calls["status"] = 0
    release = release2
    mod.ledger = ledger_releasing
    try:
        go("C12 止まった行は数え直す", 80, [])
    finally:
        mod.ledger = real_ledger
        del os.environ["FAKE_RELEASE"]

    # C9: 上限の値が違う → 2
    for key, value in (("0", "0"), ("負", "-1"), ("nan", "nan"), ("inf", "inf"), ("数でない", "abc")):
        o[f"C9 上限 {key}"] = run(mod, ["70", "--max-total-usd", value], root)[0]

    # S12: 引数が違う → 2。通知しない
    go("S12 引数", 61, ["--max-stalls", "0"])
    o["S12 番号でない"] = run(mod, ["abc"], root)[0]
    o["S12 ASCII でない数字"] = run(mod, ["²"], root)[0]
    o["S12 0 は番号でない"] = run(mod, ["00"], root)[0]
    o["S12 0 の多すぎる番号"] = run(mod, ["0" * 5000 + "57"], root)[0]  # int() に通せば例外になる長さ
    o["S12 桁の多すぎる番号"] = run(mod, ["1" + "0" * 5000], root)[0]
    # 18/19 桁の境目と int() の上限の境目。台帳が無いので、番号の検査を通れば 4、拒めば 2
    limit = sys.get_int_max_str_digits()
    o["S12 18 桁"] = run(mod, ["1" * 18], root)[0]
    o["S12 19 桁"] = run(mod, ["1" * 19], root)[0]
    o["S12 上限ちょうどの桁数"] = run(mod, ["0" * 30 + "1" * limit], root)[0]
    o["S12 上限を 1 超える桁数"] = run(mod, ["1" * (limit + 1)], root)[0]
    o["S12 先頭 0 の番号"] = run(mod, ["057"], root)  # 台帳 issue-57 は済んでいる（S9）→ 起こさずに 0
    o["S12 語に分けられない --claude"] = run(mod, ["50", "--claude", "a'b"], root)[0]
    return o


def main() -> int:
    global JOBS
    parser = argparse.ArgumentParser(description="outer-loop.py（cruise の外側のループ）の回帰テスト")
    parser.add_argument("--jobs", type=int, default=JOBS_MAX,
                        help=f"陽性対照と変異を同時に観測するプロセスの数（既定と上限: {JOBS_MAX}。1 で 1 つずつ）")
    parser.add_argument("--pool-size", action="store_true", help="プールに渡す作業者の数を出して終わる（試料の中で使う）")
    opts = parser.parse_args()
    if opts.jobs < 1:
        parser.error(f"--jobs は 1 以上: {opts.jobs}")
    JOBS = min(opts.jobs, JOBS_MAX)
    if opts.pool_size:
        run_observations([], {})  # 当てる経路そのもの（`run_observations`）でプールを作る——当てるものが 0 件なので作業者は起きない
        print(pool_sizes[-1] if pool_sizes else "")
        return 0

    print("作業者の数:")
    check("--jobs をプールに渡す（1 なら 1・99 なら上限）", check_pool_size())

    tmp = Path(tempfile.mkdtemp(prefix="test-outer-loop-")).resolve()  # macOS の /var は /private/var——git と cwd が返す形にそろえる
    saved_env = dict(os.environ)
    try:
        isolate_env(tmp / "home")
        mod = load()
        print("正しい本体")
        began = time.monotonic()
        o = scenario(mod, tmp, "correct")
        print(f"  （本体のままの回 {time.monotonic() - began:.1f} 秒）")
        a = lambda key: o[key]  # noqa: E731
        check("PATH で実行できる claude は偽物だけ（本物の claude が在る項を外した）", a("PATH の claude") == ["<偽物>"])
        check("S1 前進が続けば済むまで回し、0 で止まる（起動 2・通知 1）", a("S1 前進して済む")[0][0] == 0 and a("S1 前進して済む")[1:] == (2, 1))
        check("S1 claude の引数は -p・/dev-loop:cruise 50 --absent・stream-json・追記・足す引数",
              all(r == ["-p", "/dev-loop:cruise 50 --absent", "--output-format", "stream-json", "--verbose",
                        "--append-system-prompt", mod.APPEND, "--model", "sonnet"] for r in a("S1 引数")))
        check("S1 出力は台帳の隣に起動ごとに残る（.out・.err が 2 つずつ）",
              sorted(p.suffix for p in (tmp / "repo-correct" / ".claude" / "plans" / "cruise-issue-50-loop").iterdir()) == [".err"] * 2 + [".out"] * 2)
        check("S1 worktree のサブディレクトリから呼んでも cwd はメインの作業ツリー", a("S1 cwd") == [".", "."])
        check("S1 利用者の上限 600000 を 0 で上書きする", a("S1 上限") == ["0", "0"])
        check("S2 note だけの起動は前進なしで、2 回で 6", a("S2 note だけ")[0][0] == 6 and a("S2 note だけ")[1:] == (2, 1))
        check("S2 台帳のファイルは変わっていた（陽性対照）", a("S2 ファイルは変わった"))
        check("S2 --absent を渡さなければ付けない", a("S2 引数") == ["/dev-loop:cruise 51", "/dev-loop:cruise 51"])
        check("S2 環境に無い上限も 0 にする", a("S2 上限") == ["0", "0"])
        print("\nauto-compact の窓（#1167）")
        w1 = a("W1 窓 400k")
        check("W1 --autocompact-window 400k は --autocompact 400000 を追記の後・足す引数の前に足し、窓を 1 度出す",
              w1["rc"] == 0 and w1["argv"] and all(r == ["-p", "/dev-loop:cruise 180", "--output-format", "stream-json", "--verbose",
                                                         "--append-system-prompt", mod.APPEND, "--autocompact", "400000", "--model", "sonnet"]
                                                    for r in w1["argv"])
              and len(w1["argv"]) == 2 and w1["lines"] == ["auto-compact の窓: 400000 トークンを --autocompact で渡す（起こす claude 1 つにだけ効く）"])
        w2 = a("W2 窓と環境変数")
        check("W2 環境変数が設定されていれば、効かないと 1 度言う（それでも渡す）",
              len(w2["argv"]) == 2 and w2["argv"][0][-2:] == ["--autocompact", "1000000"] and len(w2["lines"]) == 2
              and "窓 1000000 は効かない: 環境変数 CLAUDE_CODE_AUTO_COMPACT_WINDOW='300000'" in w2["lines"][1])
        w3 = a("W3 窓なしと環境変数")
        check("W3 窓を渡していなければ、環境変数があっても何も言わず、--autocompact を足さない",
              w3["lines"] == [] and w3["argv"] and all("--autocompact" not in r for r in w3["argv"]))
        check("W5 台帳があっても、拒んだ起動は 2 で、出力の置き場を作らず、claude を起こさない",
              a("W5 台帳ありで拒む")["rc"] == 2 and a("W5 台帳ありで拒む")["argv"] == [] and a("W5 出力の置き場") is False)
        bads = {k: v for k, v in o.items() if k.startswith("W4 拒む")}
        check("W4 範囲の外・書式の誤りは起動の前に 2 で拒み、claude を起こさず、通知もしない",
              len(bads) == 8 and all(v["rc"] == 2 and v["argv"] == [] and v["notify"] == 0 and "--autocompact-window" in v["stderr"] for v in bads.values()))
        check("S3 続けてでない前進なしでは止まらず 0（起動 6）", a("S3 交互")[0][0] == 0 and a("S3 交互")[1:] == (6, 1))
        check("S4 上限 2 回で 7", a("S4 上限")[0][0] == 7 and a("S4 上限")[1:] == (2, 1))
        check("S5 claude が 1 で終われば 8（起動 1）", a("S5 claude が失敗")[0][0] == 8 and a("S5 claude が失敗")[1:] == (1, 1))
        check("S6 claude を起こせなければ 8", a("S6 claude が無い")[0][0] == 8 and a("S6 claude が無い")[2] == 1)
        check("S7 人待ちだけなら起こさずに 3", a("S7 人待ち")[0][0] == 3 and a("S7 人待ち")[1:] == (0, 1))
        check("S8 台帳が無ければ起こさずに 4", a("S8 台帳が無い")[0][0] == 4 and a("S8 台帳が無い")[1:] == (0, 1))
        check("S9 最初から済んでいれば起こさずに 0", a("S9 済んでいる")[0][0] == 0 and a("S9 済んでいる")[1:] == (0, 1))
        check("S10 起動の後に progress を読めなければ 4（理由は progress）",
              a("S10 壊れる")[0][0] == 4 and "progress を読めない" in a("S10 壊れる")[0][1] and a("S10 壊れる")[1:] == (1, 1))
        check("S11 中断は 130 で通知する", a("S11 中断")[0][0] == 130 and a("S11 中断")[2] == 1)
        check("S12 引数が違えば 2 で通知しない", a("S12 引数")[0][0] == 2 and a("S12 引数")[1:] == (0, 0) and a("S12 番号でない") == 2)
        check("S13 SIGTERM は 130 で通知する", a("S13 SIGTERM")[0][0] == 130 and "SIGTERM" in a("S13 SIGTERM")[0][1] and a("S13 SIGTERM")[2] == 1)
        check("S14 ループの中の例外は 4 で通知する", a("S14 例外")[0][0] == 4 and a("S14 例外")[2] == 1)
        check("シグナルの扱いを終わったら戻す", a("SIGTERM の扱いを戻した"))
        check("S12 ASCII でない数字（²）は 2", a("S12 ASCII でない数字") == 2)
        check("S12 語に分けられない --claude は 2", a("S12 語に分けられない --claude") == 2)
        check("S12 0 は 2", a("S12 0 は番号でない") == 2)
        check("S12 0 を 5000 個前に置いた 57 も例外でなく 57 と読む（0）", a("S12 0 の多すぎる番号") == 0)
        check("S12 桁の多すぎる番号は例外でなく 2", a("S12 桁の多すぎる番号") == 2)
        check("S12 18 桁・19 桁の番号は検査を通る（台帳が無いので 4）", a("S12 18 桁") == 4 and a("S12 19 桁") == 4)
        check("S12 int() の上限ちょうどの桁数は通り（4）、1 桁超えると 2",
              a("S12 上限ちょうどの桁数") == 4 and a("S12 上限を 1 超える桁数") == 2)
        check("S12 先頭 0 の 057 は 57 と読む（狭いパスの後退を戻す）",
              a("S12 先頭 0 の番号")[0] == 0 and "issue-57:" in a("S12 先頭 0 の番号")[1])
        check("S15 SIGHUP を無視させて起動すれば、届いても回り続けて 0（起動 1）",
              a("S15 SIGHUP を無視させて起動")[0][0] == 0 and a("S15 SIGHUP を無視させて起動")[1:] == (1, 1))
        check("S15 終わった後も SIGHUP は無視のまま", a("S15 SIGHUP は無視のまま"))
        check("S16 claude の実行中の SIGTERM は 130 で通知する", a("S16 中断で claude に SIGTERM")[0][0] == 130
              and "SIGTERM" in a("S16 中断で claude に SIGTERM")[0][1] and a("S16 中断で claude に SIGTERM")[1:] == (1, 1))
        check("S16 claude にまず SIGTERM を送り、後始末を待つ", a("S16 claude が SIGTERM を受けた"))
        check("S17 SIGTERM を無視する claude は GRACE 秒で SIGKILL（130）",
              a("S17 SIGTERM を無視する claude")[0][0] == 130 and a("S17 claude は残らない"))
        line = lambda key: a(key)[0][1]  # noqa: E731
        check("C1 ちょうど上限で 3 回目を起こさずに 11（起動 2・通知 1）・合計を出す",
              a("C1 ちょうど上限")[0][0] == 11 and a("C1 ちょうど上限")[1:] == (2, 1)
              and "費用の上限 $1.00 に達した" in line("C1 ちょうど上限") and "費用: 取れた分の合計 $1.00・起動 2 回のうち取れなかった 0 回" in line("C1 ちょうど上限"))
        check("C2 上限の下なら済むまで回して 0・合計 $0.50", a("C2 上限の下で済む")[0][0] == 0 and "合計 $0.50" in line("C2 上限の下で済む"))
        check("C2 progress の出力に費用が入らない", a("C2 progress")[0] == 0 and a("C2 progress")[1].strip() != ""
              and not re.search(r"cost|費用|0\.25|0\.5", a("C2 progress")[1]))
        check("C2 台帳のファイルに費用が入らない（正規表現は費用の文に当たる——陽性対照）", a("C2 台帳のファイルに費用が無い") and a("C2 正規表現の陽性対照"))
        check("C3 上限があり費用を取れない起動があれば、次を起こさずに 12（起動 1）",
              a("C3 取れない・上限あり")[0][0] == 12 and a("C3 取れない・上限あり")[1:] == (1, 1)
              and "取れなかった 1 回（1 回目）" in line("C3 取れない・上限あり"))
        check("C4 上限が無ければ止めずに済み、取れなかった数を出す（0 と合計しない）",
              a("C4 取れない・上限なし")[0][0] == 0 and "合計 $0.75・起動 2 回のうち取れなかった 1 回（1 回目）" in line("C4 取れない・上限なし"))
        check("C5 最後の result に費用が無ければ取れない（前の result の値を使わない）",
              a("C5 最後の result")[0][0] == 12 and "合計 $0.00" in line("C5 最後の result"))
        check("C6 真偽値・負・NaN・巨大な整数・文字列は費用と読まない（5 回とも取れない）",
              a("C6 読めない値")[0][0] == 0 and "合計 $0.00・起動 5 回のうち取れなかった 5 回" in line("C6 読めない値"))
        check("C7 子の費用を足し、ループの前の記録は数えない・走っている子は入れない",
              a("C7 子の費用")[0][0] == 0
              and "合計 $0.50・起動 1 回のうち取れなかった 0 回・子 3 体のうち取れなかった 1 体・走っている 1 体" in line("C7 子の費用"))
        check("C8 上限があっても走っている子では止めない（0）", a("C8 走っている子では止めない")[0][0] == 0
              and "走っている 1 体" in line("C8 走っている子では止めない"))
        check("C9 上限が 0・負・nan・inf・数でないなら 2", all(o[f"C9 上限 {k}"] == 2 for k in ("0", "負", "nan", "inf", "数でない")))
        check("C10 最後の起動で済めば、合計がちょうど上限でも 0", a("C10 済んだのが先")[0][0] == 0 and "合計 $1.00" in line("C10 済んだのが先"))
        check("C11 前の起動の後に走りきった子の費用で、次を起こさずに 11（起動 1）",
              a("C11 走りきった子を次の判定に入れる")[0][0] == 11 and a("C11 走りきった子を次の判定に入れる")[1:] == (1, 1)
              and "合計 $5.10" in line("C11 走りきった子を次の判定に入れる"))
        check("C12 止まった行の子の内訳は止まる直前に数え直す（0・合計 $5.10・走っている 0 体）",
              a("C12 止まった行は数え直す")[0][0] == 0 and "合計 $5.10" in line("C12 止まった行は数え直す")
              and "走っている 0 体" in line("C12 止まった行は数え直す"))
        check("S11 中断した起動は取れなかった起動に数える", "起動 1 回のうち取れなかった 1 回（1 回目）" in line("S11 中断"))
        check("S6 起こせなかった起動は費用の起動に数えない", "起動 0 回" in line("S6 claude が無い"))
        check("止まった行に親と理由が出る", a("S2 note だけ")[0][1].startswith("外側のループ: 止まった（issue-51: 前進なしが続けて 2 回"))
        body = notes(Path(os.environ["FAKE_HOME"]))
        check("通知の本文は argv で渡す（スクリプトに埋め込まない）",
              bool(body) and all(n[0] == "-e" and "issue-" not in n[1] and n[2].startswith("外側のループ: 止まった") for n in body))

        print("\n終了コードが docstring の表と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", table, re.M)}
        defined = {mod.EXIT_DONE, mod.EXIT_USAGE, mod.EXIT_WAITING, mod.EXIT_UNKNOWN, mod.EXIT_STALLED,
                   mod.EXIT_LIMIT, mod.EXIT_CLAUDE, mod.EXIT_BUDGET, mod.EXIT_COST_UNKNOWN, mod.EXIT_INTERRUPTED}
        check(f"表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)

        print("\n変異テスト（壊したのに緑なら失格）")
        # 陽性対照と変異を、別々のプロセス（`--observe`）で同時に観測する（#1052）。各プロセスは自分のテンポラリと環境を持つ
        jobs: dict[str, Path] = {}
        for name, pairs in MUTATIONS.items():
            mutated = source
            missing = [n for n, _ in pairs if n not in mutated]
            if missing:
                check(f"変異を当てる先がある: {name}: {missing}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d = tmp / f"mut-{len(jobs)}"
            d.mkdir()
            broken = d / "outer-loop.py"
            broken.write_text(mutated, encoding="utf-8")
            jobs[name] = broken
        # 陽性対照: 壊さない本体を同じ経路で観測し、このプロセスの観測と一致すること（観測の経路そのものが差を作らない）
        jobs = {CONTROL: SCRIPT, **jobs}
        print(f"  陽性対照と変異 {len(jobs) - 1} 本を {JOBS} 並列で観測する")
        began = time.monotonic()
        results = run_observations(list(jobs.values()), saved_env)
        wall = time.monotonic() - began
        expected = normalize(o, tmp)
        (control, secs) = results[0]
        check(f"陽性対照: 壊さない本体を別のプロセスで観測しても同じ（{secs:.1f} 秒）", control == expected)
        for name, (got, secs) in zip(list(jobs)[1:], results[1:]):
            # **読み込めない・観測できない変異は「殺せた」ではなく「当てられなかった」**
            if got == "load-error":
                check(f"変異を読み込める（当てられなかった）: {name}", False)
            elif got is None:
                check(f"変異を観測できる（当てられなかった）: {name}（{secs:.1f} 秒）", False)
            else:
                check(f"変異を殺せる: {name}（{secs:.1f} 秒）", got != expected)
        print(f"  （観測の全体 {wall:.1f} 秒・{JOBS} 並列）")

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
    print("外側のループのテスト: すべて合格")
    return 0


def normalize(o: dict, tmp: Path):
    """比べる形にする——テンポラリのパスを伏せ、JSON の往復でそろえる（別のプロセスの観測は tuple が list になって返る）。"""
    text = json.dumps(o, ensure_ascii=False, sort_keys=True, default=str).replace(str(tmp), "<tmp>")
    return json.loads(text)


class _ObservePool(concurrent.futures.ThreadPoolExecutor):
    """観測のプロセスを起こす作業者のプール。**渡された作業者の数を `pool_sizes` に残す**（`--pool-size` が出す）。

    作業者はスレッドだが、観測そのものは作業者ごとに起こす別のプロセス（`--observe`）で走る——同時に走る観測は `JOBS` 本まで。"""

    def __init__(self, max_workers, **kwargs):
        pool_sizes.append(max_workers)
        super().__init__(max_workers, **kwargs)


def run_observations(scripts: list[Path], env: dict) -> list[tuple]:
    """`scripts` を `JOBS` 個の作業者で観測し、渡した順に (観測, 秒) を返す（終わった順ではない）。"""
    with _ObservePool(max_workers=JOBS) as pool:
        return list(pool.map(lambda script: observe_in_process(script, env), scripts))


def check_pool_size() -> bool:
    """自分を `--jobs N --pool-size` で起こし、プールに渡した作業者の数が `min(N, 上限)` かを見る
    （`test-parallel-stop.py` と同じ形——受けた `--jobs` を使わなくても、遅く・速くなるだけで緑のままなので）。"""
    ok = True
    for asked in (1, 99):
        want = min(asked, JOBS_MAX)
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--jobs", str(asked), "--pool-size"],
                              capture_output=True, text=True, timeout=120)
        got = proc.stdout.strip()
        good = proc.returncode == 0 and got == str(want)
        print(f"  {'OK  ' if good else 'FAIL'} --jobs {asked} でプールに渡す作業者は {want}（出力: {got or '空'}・終了コード {proc.returncode}）")
        ok = ok and good
    return ok


def observe_in_process(script: Path, env: dict) -> tuple:
    """別のプロセスで `--observe` を走らせ、(正規化した観測, 秒) を返す。観測は、読み込めなければ "load-error"、観測できなければ None。

    `env` は `isolate_env` の前の環境——子は自分のテンポラリで `isolate_env` を通ってから本体を読み込む。"""
    out = Path(tempfile.mkdtemp(prefix="test-outer-loop-obs-")).resolve() / "o.json"
    start = time.monotonic()
    try:
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--observe", str(script), str(out)],
                           env=env, capture_output=True, text=True, timeout=OBSERVE_TIMEOUT)
        if r.returncode == 3:
            return "load-error", time.monotonic() - start
        if r.returncode != 0 or not out.exists():
            return None, time.monotonic() - start
        return json.loads(out.read_text(encoding="utf-8")), time.monotonic() - start
    except (OSError, subprocess.SubprocessError, ValueError):
        return None, time.monotonic() - start
    finally:
        shutil.rmtree(out.parent, ignore_errors=True)


def observe(script: Path, out: Path) -> int:
    """`--observe`: この本体（変異の写しを含む）で全試料を走らせ、正規化した観測を書く。変異で例外になれば、その例外を観測として書く。

    試料の名前（`correct`）は本体のままの回と同じにする——リポジトリのパスはテンポラリを伏せれば同じ形になる。"""
    tmp = Path(tempfile.mkdtemp(prefix="test-outer-loop-w-")).resolve()
    try:
        isolate_env(tmp / "home")
        try:
            mod = load(script)
        except Exception:
            return 3
        try:
            got = normalize(scenario(mod, tmp, "correct"), tmp)
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
