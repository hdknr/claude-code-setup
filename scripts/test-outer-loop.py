#!/usr/bin/env python3
"""`outer-loop.py`（cruise を外から繰り返し起こすループ。#791）の回帰テスト。

    python3 scripts/test-outer-loop.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/cruise/scripts/`）。`test-child-cycle.py` と同じ形——
**`dev-loop` はどのリポジトリでも使えるプラグイン**なので、本体は対象リポジトリの `scripts/` に在ることを当てにできない。

**このテストは実環境を触らず、本物の `claude` を起こさない。** 毎回テンポラリに本物の git リポジトリと worktree を作り、
台帳は**本物の `ledger.py`** で作る（`assert_not_real_repo` が対象の場所を担保する）。`PATH` の先頭に偽の `claude`（受けた引数・cwd・
環境の `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` を記録し、試料の筋書きどおりに本物の `ledger.py` で台帳を書き換えて、決めた終了コードで終わる）と
偽の `osascript`（受けた本文を記録する）を置く。**本物の `claude` が在る `PATH` の項は外す**——偽物が実行できなくても本物に落ちない。

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
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "outer-loop.py"
LEDGER = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "ledger.py"

failures: list[str] = []

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

FAKE_OSASCRIPT = r"""#!/usr/bin/env python3
import json, os, sys
with open(os.path.join(os.environ["FAKE_HOME"], "notify.jsonl"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
"""

MUTATIONS = {
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
}


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"outer_{id(script)}_{script.stat().st_mtime_ns}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.LEDGER = LEDGER  # 変異の写しはテンポラリにあるので、台帳は本物の ledger.py で読む
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
    tmp = Path(tempfile.mkdtemp(prefix="test-outer-loop-")).resolve()  # macOS の /var は /private/var——git と cwd が返す形にそろえる
    saved_env = dict(os.environ)
    try:
        isolate_env(tmp / "home")
        mod = load()
        print("正しい本体")
        o = scenario(mod, tmp, "correct")
        a = lambda key: o[key]  # noqa: E731
        check("S1 前進が続けば済むまで回し、0 で止まる（起動 2・通知 1）", a("S1 前進して済む")[0][0] == 0 and a("S1 前進して済む")[1:] == (2, 1))
        check("S1 claude の引数は -p・/dev-loop:cruise 50 --absent・追記・足す引数",
              all(r[:3] == ["-p", "/dev-loop:cruise 50 --absent", "--append-system-prompt"] and r[4:] == ["--model", "sonnet"]
                  and r[3] == mod.APPEND for r in a("S1 引数")))
        check("S1 worktree のサブディレクトリから呼んでも cwd はメインの作業ツリー", a("S1 cwd") == [".", "."])
        check("S1 利用者の上限 600000 を 0 で上書きする", a("S1 上限") == ["0", "0"])
        check("S2 note だけの起動は前進なしで、2 回で 6", a("S2 note だけ")[0][0] == 6 and a("S2 note だけ")[1:] == (2, 1))
        check("S2 台帳のファイルは変わっていた（陽性対照）", a("S2 ファイルは変わった"))
        check("S2 --absent を渡さなければ付けない", a("S2 引数") == ["/dev-loop:cruise 51", "/dev-loop:cruise 51"])
        check("S2 環境に無い上限も 0 にする", a("S2 上限") == ["0", "0"])
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
        check("止まった行に親と理由が出る", a("S2 note だけ")[0][1].startswith("外側のループ: 止まった（issue-51: 前進なしが続けて 2 回"))
        body = notes(Path(os.environ["FAKE_HOME"]))
        check("通知の本文は argv で渡す（スクリプトに埋め込まない）",
              bool(body) and all(n[0] == "-e" and "issue-" not in n[1] and n[2].startswith("外側のループ: 止まった") for n in body))

        print("\n終了コードが docstring の表と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", table, re.M)}
        defined = {mod.EXIT_DONE, mod.EXIT_USAGE, mod.EXIT_WAITING, mod.EXIT_UNKNOWN, mod.EXIT_STALLED,
                   mod.EXIT_LIMIT, mod.EXIT_CLAUDE, mod.EXIT_INTERRUPTED}
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
            broken = d / "outer-loop.py"
            broken.write_text(mutated, encoding="utf-8")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**
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
            # 止まった行には試料ごとのリポジトリのパスが入らないよう伏せてある——そのまま比べる
            check(f"変異を殺せる: {name}", got != o)

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


if __name__ == "__main__":
    sys.exit(main())
