#!/usr/bin/env python3
"""`check-alloy.py`（spec-loop の Alloy の確かめ。#922）の回帰テスト。

    python3 scripts/test-check-alloy.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-tlc.py` と同じ形。

**このテストは実環境を触らない。** 正本リポジトリはテンポラリに作り、Alloy は**偽物**（`PATH` に置かず絶対パスで呼ぶスクリプト）で当てる。
偽の Alloy は Alloy 6.2.0 の `exec` の結果の行の形（`00. run   someA … SAT`）を標準エラーに出し、本物と同じくモデルの隣に `<名前>/` を作る——
**本物の Alloy の出力の形は見ない**（本体の docstring の「守らない」）。`PATH` の先頭には、`command -v alloy` で見つかる偽の `alloy` を置く——
呼び方の行が無いときに探しに行かないことを見るため。**引数なし・`gui` の形は、偽物でも本物でも走らせない**——走ったら印を書く偽物で「走らせない」を見る。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに観測がそろったままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が期待どおりであること（下の「正しい本体」）。本体の docstring の「守る」の行数と変異の数が等しいことを、
テスト自身が数えて見る。終了コードの表と定数、書き方の行が README・スキル・Formal Checker に書かれていることも見る。
"""
import contextlib
import importlib.util
import io
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
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPT = PLUGIN / "scripts" / "check-alloy.py"
TLC = PLUGIN / "scripts" / "check-tlc.py"

failures: list[str] = []
SYSTEM_TMP = Path(tempfile.gettempdir()).resolve()  # テストが `tempfile.tempdir` を差し替える前の値

# 本体の docstring の「守る」の各行に 1 つずつ。(探す文字列, 置き換え) の組
MUTATIONS = {
    "command -v で探す": [("    if call is None:\n        return EXIT_MISSING,",
                         "    if call is None and shutil.which(\"alloy\"):\n        call = \"alloy exec\"\n        check_form(call)\n"
                         "    if call is None:\n        return EXIT_MISSING,"),
                        ("import argparse\n", "import argparse\nimport shutil\n")],
    "exec の無い・gui の在る呼び方を走らせる": [("        if call is not None:\n            check_form(call)\n", "        pass\n")],
    "クォートの中の gui を見ない": [('    if any("gui" in word.split() for word in words):\n', '    if "gui" in words:\n')],
    "シェルの組み立てを見ない": [("    if special:\n", "    if False:\n")],
    "先頭の語の = を見ない": [('    if words and "=" in words[0]:\n', "    if False:\n")],
    "先頭の許可の一覧を見ない": [("    if not (head == HEAD_JAVA or HEAD_ALLOY in head.lower()):\n", "    if False:\n")],
    "通るモデルの終了コードを見ない": [("        if rc != 0:\n", "        if False:\n")],
    "到達できることを見ない": [('GOOD_EXPECT = {("run", "someA"): "SAT", ', "GOOD_EXPECT = {")],
    "成り立つ性質の反例を見ない": [(', ("check", "emptyOrNot"): "UNSAT"}', "}")],
    "違反するモデルを見ない": [("        missed = unmet(BROKEN_EXPECT, out)\n        if missed:\n",
                         "        missed = unmet(BROKEN_EXPECT, out)\n        if False:\n")],
    "BOM を外さない": [('    text = text.removeprefix("\\ufeff")\n', "")],
    "同じ行が 2 行でも先頭を使う": [("    if len(calls) > 1:\n", "    if False:\n")],
    "呼び方が空を見ない": [("    if calls and not calls[0]:\n", "    if False:\n")],
    "読めない CLAUDE.md を書いていないと読む": [('        raise Unknown(f"{path} を読めない: {e}")\n', '        return None, f"{path} を読めない: {e}"\n')],
    "headless を足さない": [('    env["JAVA_TOOL_OPTIONS"] = ', '    env["UNUSED"] = ')],
    "時間切れで止めない": [("        out, _ = proc.communicate(timeout=timeout)\n", "        out, _ = proc.communicate()\n")],
    "正本で走らせる": [("cwd=workdir,", "cwd=None,")],
    # 信号と回収（#1600）——観測は子のプロセスで取る（下の `signals`）
    "信号で片付けない": [("        TLC.catch_signals(saved)\n", "        pass\n")],
    "起こす間に信号を待たせない": [("    mask = signal.pthread_sigmask(signal.SIG_BLOCK, TLC.SIGNALS)\n", "    mask = signal.pthread_sigmask(signal.SIG_BLOCK, ())\n")],
    "Alloy に待たせた信号を引き継ぐ": [(", preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, mask))", ")")],
    "待っている間の例外・時間切れの枝の途中の信号で Alloy を止めない": [("        if proc.returncode is None:\n            TLC.with_group(proc, signal.SIGKILL)\n",
                                                   "        if False:\n            TLC.with_group(proc, signal.SIGKILL)\n")],
    "片付けの途中の信号の後に消し直さない": [("    TLC.sweep(PREFIX)  # 片付け", "    pass  # 片付け")],
    "起動時に回収しない": [("    for line in TLC.reclaim_lines(*TLC.reclaim(PREFIX)):\n        print(line, file=sys.stderr)\n", "")],
    "Alloy のグループを記録しない": [("        group = TLC.record_group(tmp)", "        group = None")],
    "信号の扱いを戻さない": [("        TLC.restore_signals(saved)\n", "        pass\n")],
    # 2 パス目の指摘（#1600）
    "戻す入口の信号を受けない": [("    except TLC.Interrupted as stop:  # 信号の扱いを戻す入口", "    except ZeroDivisionError as stop:  # 信号の扱いを戻す入口")],
    "書けない標準エラーで終了コードを変える": [("    TLC.say(f\"確かめていない: 信号 {signal.Signals(stop.signum).name} で止められた（Alloy を止め、一時ディレクトリを消した）\")",
                                     "    print(f\"確かめていない: 信号 {signal.Signals(stop.signum).name} で止められた（Alloy を止め、一時ディレクトリを消した）\", file=sys.stderr)")],
}
PREFIX = "spec-loop-check-alloy-"


def fake_alloy(probe_run="SAT", probe_check="UNSAT", broken_check="SAT", probe_rc=0, marker=False):
    """偽の Alloy。最後の引数（モデルのファイル）で振る舞いを決め、本物と同じく作業ディレクトリに `<名前>/` を作り、結果の行を標準エラーに出す。"""
    return f"""#!/bin/sh
for a in "$@"; do f="$a"; done
{'touch "$MARKER"' if marker else ':'}
[ -n "$ENVLOG" ] && printf '%s\\n' "$JAVA_TOOL_OPTIONS" > "$ENVLOG"
case "$f" in
  Probe.als) mkdir -p Probe && touch Probe/receipt.json
    printf '00. run   someA                    0    1/1     {probe_run}\\n01. check emptyOrNot               0       {probe_check}\\n' >&2; exit {probe_rc};;
  Broken.als) mkdir -p Broken && touch Broken/receipt.json
    printf '00. check alwaysEmpty              0    1/1     {broken_check}\\n' >&2; exit 0;;
esac
echo "unknown model: $f" >&2
exit 1
"""


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_{id(path)}_{path.stat().st_mtime_ns}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(SYSTEM_TMP), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def write_exe(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def make_tools(base: Path) -> dict:
    """偽の Alloy と、通らない形の呼び方。どれも絶対パスで呼ぶ（`PATH` の `alloy` とは別）。"""
    tools = base / "tools"
    tools.mkdir(parents=True)
    t = {
        "good": write_exe(tools / "fake-alloy", fake_alloy()),
        # 何にでも「反例なし」と言う（違反するモデルでも）
        "never-ce": write_exe(tools / "never-ce-alloy", fake_alloy(broken_check="UNSAT")),
        # 何にでも「反例あり」と言う（成り立つ性質でも）
        "always-ce": write_exe(tools / "always-ce-alloy", fake_alloy(probe_check="SAT")),
        # 何も許さない（到達できない）
        "unreachable": write_exe(tools / "unreachable-alloy", fake_alloy(probe_run="UNSAT")),
        # 結果の行は出すが終了コードが 0 でない
        "bad-rc": write_exe(tools / "bad-rc-alloy", fake_alloy(probe_rc=3)),
        # 起動しても Alloy でない（jar の場所が違う、の形）
        "broken": write_exe(tools / "broken-alloy", "#!/bin/sh\necho 'Error: Unable to access jarfile /nowhere/alloy.jar' >&2\nexit 1\n"),
        # 走ったら印を書く（走らせないことを見る）。中身は通る偽物
        "marker": write_exe(tools / "marker-alloy", fake_alloy(marker=True)),
        # 時間切れ（子のプロセスも残す——プロセスグループで止めないと出力の管が閉じない）
        "slow": write_exe(tools / "slow-alloy", "#!/bin/sh\nsleep 20 &\nwait\n"),
        # 自分の pid を書いて眠る（信号・SIGKILL の試料。#1600）
        "sleepy": write_exe(tools / "sleepy-alloy", f"#!{sys.executable}\nimport os, signal, time\n"
                            "open(os.environ['ALLOY_MASK'], 'w').write(str(sorted(int(s) for s in signal.pthread_sigmask(signal.SIG_BLOCK, []))))\n"
                            "open(os.environ['ALLOY_PID'], 'w').write(str(os.getpid()))\ntime.sleep(60)\n"),
        # 先頭が java の通る偽物（`java -jar <jar> exec` の形の陽性対照）
        "java": write_exe(tools / "java", fake_alloy(marker=True)),
        # 空白を含むパスの通る偽物（クォートはシェルの組み立てに数えない）
        "spaced": write_exe(tools / "fake alloy", fake_alloy(marker=True)),
    }
    # PATH の先頭に置く `alloy`（command -v で見つかる、通る偽物）
    pathdir = base / "pathbin"
    pathdir.mkdir()
    write_exe(pathdir / "alloy", fake_alloy())
    t["pathdir"] = pathdir
    return t


def snapshot(root: Path):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


def run(mod, argv):
    """(終了コード, 標準出力)。"""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            rc = mod.main(argv)
        except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
            return ("例外", type(exc).__name__)
    return rc, out.getvalue()


# 片付けの途中に信号が届く形——本体を読み込み、最初の `shutil.rmtree`（TemporaryDirectory の片付け）の入口で自分に SIGTERM を送ってから本体を走らせる
IN_CLEANUP = """import importlib.util, os, shutil, signal, sys
spec = importlib.util.spec_from_file_location("check_alloy", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
real, fired = shutil.rmtree, []
def rmtree(*a, **k):
    if not fired:
        fired.append(1)
        os.kill(os.getpid(), signal.SIGTERM)
    return real(*a, **k)
shutil.rmtree = rmtree
sys.exit(module.main(sys.argv[2:]))
"""

POPEN_WINDOW = """import importlib.util, os, signal, subprocess, sys, time
spec = importlib.util.spec_from_file_location("check_alloy", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
real = subprocess.Popen
class Popen(real):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        open(sys.argv[2], "w").write(str(self.pid))
        # 偽の検査器が起きて pid を書くまで待ってから送る——起きる前に作業ディレクトリが消えると、偽物は自分で死に（読めない・閉じた管に書いて SIGPIPE）、残る形と区別できない（実測の交絡）
        for _ in range(300):
            if os.path.exists(os.environ["ALLOY_PID"]):
                break
            time.sleep(0.02)
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(0.01)
subprocess.Popen = Popen
sys.exit(module.main(sys.argv[3:]))
"""


# 信号の扱いを戻す入口（待たせる前）に届く形——本体を読み込み、`restore_signals` を「自分に SIGTERM を送ってから本物を呼ぶ」ものに包む（#1600 の 2 パス目の CR2-1）
RESTORE_ENTRY = """import importlib.util, os, signal, sys
spec = importlib.util.spec_from_file_location("check_alloy", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
real = module.TLC.restore_signals
def restore_signals(saved):
    os.kill(os.getpid(), signal.SIGTERM)
    return real(saved)
module.TLC.restore_signals = restore_signals
sys.exit(module.main(sys.argv[2:]))
"""

# 時間切れの枝で止める前に届く形——本体の `run_model` を時間切れ 1 秒で眠る検査器に当て、最初の `with_group`（止める呼び出し）の入口で自分に SIGTERM を送る（#1600 の 2 パス目の V2-R1）
TIMEOUT_BRANCH = """import importlib.util, os, signal, sys, tempfile
spec = importlib.util.spec_from_file_location("check_alloy", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
real, fired = module.TLC.with_group, []
def with_group(proc, sig):
    if not fired:
        fired.append(1)
        open(sys.argv[2], "w").write(str(proc.pid))
        os.kill(os.getpid(), signal.SIGTERM)
    return real(proc, sig)
module.TLC.with_group = with_group
saved = module.TLC.current_signals()
try:
    module.TLC.catch_signals(saved)
    module.run_model("sleep 30 #", tempfile.mkdtemp(), "M", 1)
    print("信号が上がらない")
except module.TLC.Interrupted as stop:
    print("Interrupted", stop.signum)
finally:
    module.TLC.restore_signals(saved)
"""


# `sh -c` の最後のコマンドを exec しない sh（Linux の dash）では、検査器は sh の子で、sh が待たせ方を解いてから起こすことがあり、検査器の待たせ方を見ても引き継いだかが分からない（PR #1627 の CI）。
# 本体を読み込み、`/bin/sh -c` に渡す文字列の頭に `exec ` を足して、検査器を Popen の子そのものにしてから本体を走らせる
EXEC_SHELL = """import importlib.util, subprocess, sys
spec = importlib.util.spec_from_file_location("check_alloy", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
real = subprocess.Popen
class Popen(real):
    def __init__(self, args, *a, **k):
        if isinstance(args, list) and args[:2] == ["/bin/sh", "-c"]:
            args = [*args[:2], "exec " + args[2], *args[3:]]
        super().__init__(args, *a, **k)
subprocess.Popen = Popen
sys.exit(module.main(sys.argv[2:]))
"""


def dead_pid() -> int:
    proc = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True, text=True, check=True)
    pid = int(proc.stdout)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return pid
    raise AssertionError(f"終わったはずのプロセス {pid} が居る（pid の再使用）——試料を組めない")


def gone(pid: int) -> bool:
    for _ in range(100):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    with contextlib.suppress(ProcessLookupError):
        os.killpg(os.getpgid(pid), signal.SIGKILL)  # 偽の Alloy を置き去りにしない
    return False


def wait_pid(path: Path) -> int | None:
    for _ in range(300):
        if path.is_file() and path.read_text().strip():
            return int(path.read_text())
        time.sleep(0.05)
    return None


def signals(script: Path, work: Path, tools: dict) -> dict:
    """信号と回収（#1600）を子のプロセスで観測する。**観測にはテンポラリのパスと pid を入れない。**"""
    tmpdir = work / "sigtmp"
    tmpdir.mkdir()
    root = work / "sigrepo"
    root.mkdir()
    pid_file = work / "alloy.pid"
    mask_file = work / "alloy.mask"
    env = {**os.environ, "TMPDIR": str(tmpdir), "ALLOY_PID": str(pid_file), "ALLOY_MASK": str(mask_file)}

    def left():
        return sorted(p.name for p in tmpdir.iterdir() if p.name.startswith(PREFIX))

    def wipe():
        for p in tmpdir.iterdir():
            shutil.rmtree(p, ignore_errors=True)
        if pid_file.exists():
            pid_file.unlink()

    o = {}
    # 1. Alloy が走っている間の SIGTERM
    (root / "CLAUDE.md").write_text(f"Alloy の呼び方: {tools['sleepy']} exec\n", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "-I", str(script), str(root)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            env=env, cwd=work, preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL))
    pid = wait_pid(pid_file)
    if pid is None:
        proc.kill()
        proc.communicate()
        o["信号: SIGTERM"] = "偽の Alloy が起動しなかった"
    else:
        proc.send_signal(signal.SIGTERM)
        try:
            out, _ = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
        o["信号: SIGTERM"] = (proc.returncode, "信号" in out, gone(pid), left(), mask_file.read_text() if mask_file.is_file() else None)
    wipe()
    # 1a. 検査器を Popen の子そのものにした形（上の EXEC_SHELL）で、Alloy が待たせた信号を引き継がずに起きるか
    (root / "CLAUDE.md").write_text(f"Alloy の呼び方: {tools['sleepy']} exec\n", encoding="utf-8")
    wrapper = work / "exec_shell.py"
    wrapper.write_text(EXEC_SHELL, encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "-I", str(wrapper), str(script), str(root)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            env=env, cwd=work, preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL))
    pid = wait_pid(pid_file)
    if pid is None:
        proc.kill()
        proc.communicate()
        o["信号: 検査器の待たせ方"] = "偽の Alloy が起動しなかった"
    else:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
        o["信号: 検査器の待たせ方"] = (proc.returncode, gone(pid), mask_file.read_text() if mask_file.is_file() else None)
    wipe()
    # 1b. 起こした直後（Popen の中）の SIGTERM——Popen が子を起こした後・返る前に信号を送り、関数を 1 つ呼んで待っていない信号の例外をその場で上げさせる
    wrapper = work / "popen.py"
    wrapper.write_text(POPEN_WINDOW, encoding="utf-8")
    group_file = work / "popen.pid"
    run_ = subprocess.run([sys.executable, "-I", str(wrapper), str(script), str(group_file), str(root)], capture_output=True, text=True, env=env,
                          cwd=work, timeout=120, preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL))
    group_alive = None
    if group_file.is_file():
        time.sleep(0.2)
        try:
            os.killpg(int(group_file.read_text()), 0)
            group_alive = True
            os.killpg(int(group_file.read_text()), signal.SIGKILL)
        except ProcessLookupError:
            group_alive = False
    o["信号: 起こした直後"] = (run_.returncode, group_alive, left())
    wipe()
    # 1c. 時間切れの枝で止める前の SIGTERM——抜ける前に Alloy のグループを止めるか
    wrapper = work / "timeout_branch.py"
    wrapper.write_text(TIMEOUT_BRANCH, encoding="utf-8")
    group_file = work / "timeout.pid"
    run_ = subprocess.run([sys.executable, "-I", str(wrapper), str(script), str(group_file)], capture_output=True, text=True, env=env,
                          cwd=work, timeout=120, preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL))
    group_alive = None
    if group_file.is_file():
        time.sleep(0.2)
        try:
            os.killpg(int(group_file.read_text()), 0)
            group_alive = True
            os.killpg(int(group_file.read_text()), signal.SIGKILL)
        except ProcessLookupError:
            group_alive = False
    o["信号: 時間切れの枝"] = (run_.stdout.strip(), group_alive)
    wipe()
    # 1d. 信号の扱いを戻す入口の SIGTERM（通る偽物で）——143 で、トレースバックの 1 にしない
    (root / "CLAUDE.md").write_text(f"Alloy の呼び方: {tools['good']} exec\n", encoding="utf-8")
    wrapper = work / "restore_entry.py"
    wrapper.write_text(RESTORE_ENTRY, encoding="utf-8")
    run_ = subprocess.run([sys.executable, "-I", str(wrapper), str(script), str(root)], capture_output=True, text=True, env=env, cwd=work, timeout=120,
                          preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL))
    o["信号: 戻す入口"] = (run_.returncode, "Traceback" in run_.stderr, left())
    wipe()
    # 1e. 標準エラーが書けない（読む側を閉じた管）ときの SIGHUP——129 で、120 にしない
    (root / "CLAUDE.md").write_text(f"Alloy の呼び方: {tools['sleepy']} exec\n", encoding="utf-8")
    read_end, write_end = os.pipe()
    proc = subprocess.Popen([sys.executable, "-I", str(script), str(root)], stdout=subprocess.PIPE, stderr=write_end, text=True,
                            env=env, cwd=work, preexec_fn=lambda: signal.signal(signal.SIGHUP, signal.SIG_DFL))
    os.close(write_end)
    pid = wait_pid(pid_file)
    os.close(read_end)
    if pid is None:
        proc.kill()
        proc.communicate()
        o["信号: 書けない標準エラー"] = "偽の Alloy が起動しなかった"
    else:
        proc.send_signal(signal.SIGHUP)
        try:
            proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
        o["信号: 書けない標準エラー"] = (proc.returncode, gone(pid), left())
    wipe()
    # 2. 片付けの途中の信号（通る偽物で）
    (root / "CLAUDE.md").write_text(f"Alloy の呼び方: {tools['good']} exec\n", encoding="utf-8")
    wrapper = work / "in_cleanup.py"
    wrapper.write_text(IN_CLEANUP, encoding="utf-8")
    run_ = subprocess.run([sys.executable, "-I", str(wrapper), str(script), str(root)], capture_output=True, text=True, env=env, cwd=work, timeout=120,
                          preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL))
    o["信号: 片付けの途中"] = (run_.returncode, left())
    wipe()
    # 3. 回収（持ち主の居ない pid つきだけを消す）
    dead = dead_pid()
    names = {"持ち主が居ない": f"{PREFIX}{dead}-abcd1234", "持ち主が居る": f"{PREFIX}{os.getpid()}-abcd1234",
             "古い名前": f"{PREFIX}zzflmv9r", "ほかの頭": f"spec-loop-formal-rerun-{dead}-abcd1234"}
    for name in names.values():
        (tmpdir / name).mkdir()
    run_ = subprocess.run([sys.executable, "-I", str(script), str(root)], capture_output=True, text=True, env=env, cwd=work, timeout=120)
    o["回収"] = (run_.returncode, {why: (tmpdir / name).exists() for why, name in names.items()},
                "持ち主の居ない一時ディレクトリを消した" in run_.stderr)
    wipe()
    # 4. SIGKILL の後に Alloy が走っている間は消さずに言い、止まった後の起動が消す
    (root / "CLAUDE.md").write_text(f"Alloy の呼び方: {tools['sleepy']} exec\n", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "-I", str(script), str(root)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, cwd=work)
    pid = wait_pid(pid_file)
    proc.kill()
    proc.wait()
    (root / "CLAUDE.md").write_text(f"Alloy の呼び方: {tools['good']} exec\n", encoding="utf-8")
    if pid is None:
        o["SIGKILL の後に Alloy が走っている"] = "偽の Alloy が起動しなかった"
    else:
        first = subprocess.run([sys.executable, "-I", str(script), str(root)], capture_output=True, text=True, env=env, cwd=work, timeout=120)
        kept = len(left()) == 1 and "まだ書いている" in first.stderr
        with contextlib.suppress(ProcessLookupError):
            os.killpg(os.getpgid(pid), signal.SIGKILL)  # 偽物の pid はグループの番号とは限らない——Linux の sh（dash）は `sh -c` の最後のコマンドを exec しないことがある（PR #1627 の CI）
        stopped = gone(pid)
        subprocess.run([sys.executable, "-I", str(script), str(root)], capture_output=True, text=True, env=env, cwd=work, timeout=120)
        o["SIGKILL の後に Alloy が走っている"] = (kept, stopped, left())
    wipe()
    return o


def scenario(mod, base: Path, tag: str) -> dict:
    """1 つの本体に全試料を当て、観測を辞書で返す。**観測にはテンポラリのパスを入れない。**"""
    work = base / tag
    assert_not_real_repo(work.parent)
    tools = make_tools(work)
    root = work / "repo"
    root.mkdir()
    md = root / "CLAUDE.md"
    marker = work / "ran"
    envlog = work / "envlog"
    os.environ["MARKER"] = str(marker)
    # 走らせる場所を正本にしておく——本体が一時ディレクトリで走らせなければ、偽の Alloy の <名前>/ が正本に残る
    os.chdir(root)
    o = {}

    def case(text):
        """(終了コード, 呼び方が走ったか, 正本が変わらなかったか)。"""
        if text is None:
            if md.exists():
                md.unlink()
        elif isinstance(text, bytes):
            md.write_bytes(text)
        else:
            md.write_text(text, encoding="utf-8")
        if marker.exists():
            marker.unlink()
        before = snapshot(root)
        rc, out = run(mod, [str(root)])
        return rc, marker.exists(), snapshot(root) == before

    def call_line(name, extra=" exec"):
        return f"Alloy の呼び方: {tools[name]}{extra}\n"

    o["CLAUDE.md が無い"] = case(None)
    o["呼び方の行が無い（PATH に alloy が在る）"] = case("# 正本\n\nほかの行だけ\n")
    o["通る呼び方"] = case("# 正本\n" + call_line("good", " exec -q"))
    o["通る呼び方（走ったら印）"] = case(call_line("marker"))
    o["exec の無い呼び方"] = case(call_line("marker", ""))
    o["gui の呼び方"] = case(call_line("marker", " gui"))
    o["exec と gui の両方"] = case(call_line("marker", " exec gui"))
    o["exec が 1 語の一部"] = case(call_line("marker", "-exec"))
    o["クォートの中の gui"] = case(call_line("marker", " exec 'x gui'"))
    o["シェルの組み立て（||）"] = case(f"Alloy の呼び方: {tools['marker']} exec || {tools['marker']}\n")
    o["シェルの組み立て（# の後ろの exec）"] = case(f"Alloy の呼び方: {tools['marker']} # exec\n")
    o["シェルの組み立て（; の後ろの exec）"] = case(f"Alloy の呼び方: {tools['marker']}; : exec\n")
    o["組み込みの exec で始まる（ラッパーの本文の形）"] = case(f"Alloy の呼び方: exec {tools['marker']}\n")
    o["シェルで始まる（sh -c）"] = case(f"Alloy の呼び方: sh -c '{tools['marker']}' exec\n")
    o["空白を含むパスをクォートで囲む"] = case(f"Alloy の呼び方: '{tools['spaced']}' exec\n")
    o["先頭が java"] = case(f"Alloy の呼び方: {tools['java']} -Dx=1 -jar /opt/alloy.jar exec\n")
    o["ブレースの展開"] = case(f"Alloy の呼び方: {tools['marker']} {{gui,}} exec\n")
    o["組み込みの trap で始まる"] = case(f"Alloy の呼び方: trap {tools['marker']} EXIT exec\n")
    o["別のシェルで始まる（tcsh -c）"] = case(f"Alloy の呼び方: tcsh -c {tools['marker']} exec\n")
    o["環境変数の代入で始まる"] = case(f"Alloy の呼び方: FOO=1 exec {tools['marker']}\n")
    o["! で始まる"] = case(f"Alloy の呼び方: ! exec {tools['marker']}\n")
    o["名前に alloy を含む代入で始まる"] = case(f"Alloy の呼び方: ALLOY=1 exec {tools['marker']}\n")
    o["値に alloy を含む代入で始まる"] = case(f"Alloy の呼び方: X=alloy exec {tools['marker']}\n")
    o["通らない呼び方"] = case(call_line("broken"))
    o["何にでも反例なし"] = case(call_line("never-ce"))
    o["何にでも反例あり"] = case(call_line("always-ce"))
    o["到達できない"] = case(call_line("unreachable"))
    o["結果の行は出すが終了コードが 0 でない"] = case(call_line("bad-rc"))
    o["フェンスの中だけ"] = case("例:\n\n```text\n" + call_line("good") + "```\n")
    o["BOM つきの 1 行目"] = case("\ufeff" + call_line("good"))
    o["全角のコロンの呼び方"] = case(call_line("good").replace("Alloy の呼び方:", "Alloy の呼び方："))
    o["呼び方が 2 行"] = case(call_line("good") + call_line("broken"))
    md.write_text("Alloy の呼び方:   \n", encoding="utf-8")
    rc, out = run(mod, [str(root)])
    o["呼び方が空"] = (rc, "空" in out)
    o["読めない CLAUDE.md（UTF-8 でない）"] = case(b"\xff\xfe\x00Alloy\n")
    os.environ["ENVLOG"] = str(envlog)
    os.environ["JAVA_TOOL_OPTIONS"] = "-Xmx64m"
    case(call_line("good"))
    o["走らせる環境の JAVA_TOOL_OPTIONS"] = envlog.read_text(encoding="utf-8").strip() if envlog.exists() else None
    del os.environ["ENVLOG"], os.environ["JAVA_TOOL_OPTIONS"]
    saved = mod.PROBE_TIMEOUT
    mod.PROBE_TIMEOUT = 1
    start = time.monotonic()
    rc = case(call_line("slow"))
    o["時間切れ"] = (rc, "早い" if time.monotonic() - start < 10 else "遅い")
    mod.PROBE_TIMEOUT = saved
    o["引数なし"] = run(mod, [])[0]
    # 前の試料の main（変異なら戻さない）の扱いを、テストの既定に戻してから比べる
    defaults = {signal.SIGTERM: signal.SIG_DFL, signal.SIGINT: signal.default_int_handler, signal.SIGHUP: signal.SIG_DFL}
    for sig, handler in defaults.items():
        signal.signal(sig, handler)
    md.write_text(call_line("good"), encoding="utf-8")
    run(mod, [str(root)])
    o["main の後に信号の扱いが戻る"] = all(signal.getsignal(sig) == handler for sig, handler in defaults.items())
    for sig, handler in defaults.items():
        signal.signal(sig, handler)
    o.update(signals(Path(mod.__file__), work, tools))
    md.write_text(call_line("good"), encoding="utf-8")
    o["出力（通る）"] = run(mod, [str(root)])[1].replace(str(tools["good"]), "<alloy>")
    md.unlink()
    o["出力（無い）"] = run(mod, [str(root)])[1].replace(str(root), "<root>")
    os.chdir(base)
    return o


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test-check-alloy-")).resolve()
    saved_env = dict(os.environ)
    cwd = os.getcwd()
    try:
        mod = load_module(SCRIPT, "calloy")
        # 同じプロセスで呼ぶ main の回収が利用者の `$TMPDIR` を見ないように（#1600）
        (tmp / "tmpdir").mkdir()
        tempfile.tempdir = str(tmp / "tmpdir")
        tools_probe = make_tools(tmp / "path-probe")
        os.environ["PATH"] = f"{tools_probe['pathdir']}{os.pathsep}{os.environ.get('PATH', '')}"
        os.environ.pop("JAVA_TOOL_OPTIONS", None)
        check("陽性対照: PATH の先頭の偽の alloy が command -v で見つかる", shutil.which("alloy") == str(tools_probe["pathdir"] / "alloy"))
        print("正しい本体")
        o = scenario(mod, tmp, "correct")
        ok, missing, unknown = (0, False, True), (1, False, True), (4, False, True)
        check("CLAUDE.md が無い: 1", o["CLAUDE.md が無い"] == missing)
        check("呼び方の行が無い: PATH に alloy が在っても 1（command -v で探さない）", o["呼び方の行が無い（PATH に alloy が在る）"] == missing)
        check("通る呼び方（PATH に無い絶対パス・exec の後に引数）: 0", o["通る呼び方"] == ok)
        check("通る呼び方は走らせる: 0 で印がある（陽性対照）", o["通る呼び方（走ったら印）"] == (0, True, True))
        check("exec の無い呼び方（引数なしの形）: 4 で走らせない", o["exec の無い呼び方"] == unknown)
        check("gui の呼び方: 4 で走らせない", o["gui の呼び方"] == unknown and o["exec と gui の両方"] == unknown)
        check("exec が 1 語の一部: 4 で走らせない", o["exec が 1 語の一部"] == unknown)
        check("クォートの中の gui: 4 で走らせない", o["クォートの中の gui"] == unknown)
        check("シェルの組み立て（||・# の後ろ・; の後ろの exec）: 4 で走らせない",
              all(o[k] == unknown for k in ("シェルの組み立て（||）", "シェルの組み立て（# の後ろの exec）", "シェルの組み立て（; の後ろの exec）")))
        check("組み込みの exec で始まる・sh -c で始まる: 4 で走らせない",
              o["組み込みの exec で始まる（ラッパーの本文の形）"] == unknown and o["シェルで始まる（sh -c）"] == unknown)
        check("空白を含むパスをクォートで囲んだ呼び方: 0 で走らせる（陽性対照）", o["空白を含むパスをクォートで囲む"] == (0, True, True))
        check("先頭が java の呼び方（-D の = を含む）: 0 で走らせる（陽性対照）", o["先頭が java"] == (0, True, True))
        check("名前・値に alloy を含む環境変数の代入で始まる（ALLOY=1・X=alloy）: 4 で走らせない",
              o["名前に alloy を含む代入で始まる"] == unknown and o["値に alloy を含む代入で始まる"] == unknown)
        check("ブレースの展開（{gui,}）: 4 で走らせない", o["ブレースの展開"] == unknown)
        check("先頭が trap・tcsh -c・環境変数の代入・!: 4 で走らせない",
              all(o[k] == unknown for k in ("組み込みの trap で始まる", "別のシェルで始まる（tcsh -c）", "環境変数の代入で始まる", "! で始まる")))
        check("通らない呼び方: 1", o["通らない呼び方"] == missing)
        check("何にでも反例なしと言う呼び方: 1（陽性対照）", o["何にでも反例なし"] == missing)
        check("何にでも反例ありと言う呼び方: 1", o["何にでも反例あり"] == missing)
        check("到達できない呼び方: 1", o["到達できない"] == missing)
        check("結果の行は出すが終了コードが 0 でない: 1", o["結果の行は出すが終了コードが 0 でない"] == missing)
        check("フェンスの中の行は読まない（check-tlc.py の読み方）: 1", o["フェンスの中だけ"] == missing)
        check("BOM つきの 1 行目の行を読む: 0", o["BOM つきの 1 行目"] == ok)
        check("全角のコロンの行も読む: 0", o["全角のコロンの呼び方"] == ok)
        check("呼び方が 2 行: 4", o["呼び方が 2 行"] == unknown)
        check("呼び方が空: 4 で、空と言う", o["呼び方が空"] == (4, True))
        check("読めない CLAUDE.md: 4", o["読めない CLAUDE.md（UTF-8 でない）"] == unknown)
        check("走らせる環境の JAVA_TOOL_OPTIONS に headless を足し、前の値を残す",
              o["走らせる環境の JAVA_TOOL_OPTIONS"] == "-Xmx64m -Djava.awt.headless=true")
        check("時間切れ: 1 で、子のプロセスを待たずに早く返る", o["時間切れ"] == (missing, "早い"))
        check("引数なし: 2", o["引数なし"] == 2)
        check("信号: Alloy が走っている間の SIGTERM で 143・信号と言う・Alloy を止める・一時ディレクトリを残さない（#1600）",
              o["信号: SIGTERM"] == (143, True, True, [], "[]"))
        check("信号: 検査器を Popen の子そのものにした形（sh が exec する形）で、Alloy は待たせた信号を引き継がずに起きる", o["信号: 検査器の待たせ方"] == (143, True, "[]"))
        check("信号: 起こした直後（Popen の中）の SIGTERM でも 143 で Alloy を残さない", o["信号: 起こした直後"] == (143, False, []))
        check("信号: 片付けの途中の SIGTERM でも 143 で一時ディレクトリを残さない", o["信号: 片付けの途中"] == (143, []))
        check("信号: 時間切れの枝で止める前の SIGTERM でも、抜ける前に Alloy のグループを止める（#1600 の 2 パス目）",
              o["信号: 時間切れの枝"] == ("Interrupted 15", False))
        check("信号: 信号の扱いを戻す入口の SIGTERM でも 143 で、トレースバックを出さない", o["信号: 戻す入口"] == (143, False, []))
        check("信号: 標準エラーが書けない（読む側を閉じた管）ときの SIGHUP でも 129 で Alloy を残さない", o["信号: 書けない標準エラー"] == (129, True, []))
        check("回収: 持ち主の居ない pid つきだけを消し、居るもの・古い名前・ほかの頭は消さない",
              o["回収"] == (0, {"持ち主が居ない": False, "持ち主が居る": True, "古い名前": True, "ほかの頭": True}, True))
        check("SIGKILL の後に Alloy が走っている間は消さずに言い、止まった後の起動が消す", o["SIGKILL の後に Alloy が走っている"] == (True, True, []))
        check("main の後に信号の扱いが戻る", o["main の後に信号の扱いが戻る"] is True)
        check("出力（通る）は呼び方を名指しする", "Alloy が在る: 呼び方 `<alloy> exec`" in o["出力（通る）"])
        check("出力（無い）は用意のしかたと書く行を出す", "Alloy の呼び方: <コマンド> exec" in o["出力（無い）"]
              and "command -v" in o["出力（無い）"])

        print("\n終了コードの表・書き方の行が、docstring・README・スキル・Formal Checker と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        exits = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", exits, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_MISSING, mod.EXIT_USAGE, mod.EXIT_UNKNOWN}
        check(f"終了コードの表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)
        table = source.split("## 正本の `CLAUDE.md` に書く行")[1].split("## ")[0]
        check("docstring の表に行の頭がある", f"`{mod.CALL_KEY} <コマンド>`" in table)
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        front = readme.split("## 前提")[1].split("\n## ")[0]
        example = re.search(rf"^{re.escape(mod.CALL_KEY)} (.+)$", front, re.M)
        check("README の「前提」が呼び方の行を、写せる形（行頭）で、exec を含めて書く",
              example is not None and "exec" in example.group(1).split() and "gui" not in example.group(1).split())
        check("README の「前提」が Alloy の jar を挙げる", "alloy.jar" in front)
        spec_review = (PLUGIN / "skills" / "spec-review" / "SKILL.md").read_text(encoding="utf-8")
        check("spec-review が check-alloy.py で確かめる", "scripts/check-alloy.py" in spec_review)
        check("spec-review が Alloy を「版かヘルプ」で呼ばない・command -v で探さない",
              "版かヘルプ" not in spec_review and re.search(r"Alloy[^\n]*無ければ `command -v` で探す", spec_review) is None)
        formal = (PLUGIN / "agents" / "formal-checker.md").read_text(encoding="utf-8")
        check("Formal Checker が呼び方の行を名指しし、引数なし・gui の形を禁じる",
              f"`{mod.CALL_KEY}`" in formal and "引数なし" in formal and "`gui`" in formal)
        check("Formal Checker が、渡された呼び方でも exec の無い形を走らせないと書く",
              re.search(r"渡された呼び方でも、語 `exec` が無い", formal) is not None)
        check("spec-review が、check-alloy.py が 0 のときだけ呼び方を Formal Checker に渡す",
              "`check-alloy.py` が 0 を返したときだけ** `Alloy の呼び方:`" in spec_review)
        autopilot_check = (PLUGIN / "scripts" / "autopilot-check.py").read_text(encoding="utf-8")
        check("autopilot の点検の一覧に check-alloy.py が入る（各起動が spec-review の手順 3 で呼ぶ）",
              re.search(r"SPEC_REVIEW_SCRIPTS = \([^)]*\"check-alloy\.py\"", autopilot_check) is not None)

        print("\n変異テスト（壊したのに観測がそろったままなら失格）")
        for i, (name, pairs) in enumerate(MUTATIONS.items()):
            mutated = source
            absent = [n for n, _ in pairs if n not in mutated]
            if absent:
                check(f"変異を当てる先がある: {name}: {absent}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d = tmp / f"mut-{i}"
            d.mkdir()
            broken = d / "check-alloy.py"
            broken.write_text(mutated, encoding="utf-8")
            shutil.copy(TLC, d / "check-tlc.py")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**
            try:
                mutant = load_module(broken, "mut")
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, d, "s")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", got != o)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)
    finally:
        tempfile.tempdir = None
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(saved_env)
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Alloy の確かめのテスト: すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
