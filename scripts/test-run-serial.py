#!/usr/bin/env python3
"""`run-serial.py`（重い検査・アプリの起動の順番待ち。#493）の回帰テスト。

    python3 scripts/test-run-serial.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/cruise/scripts/run-serial.py`）——
cruise はどのリポジトリでも使うので、対象リポジトリの `scripts/` に在ることを当てにできない（`test-find-cycle.py` と同じ形）。

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリ（と、その worktree）を作り、そこだけを対象にする
（`assert_not_real_repo`）。本体は cwd から共通ディレクトリを決めるので、歯止めが無いと**このリポジトリの `.git` に枠を作る**。

**時間で判定しない。** 「同時に走った」「待った」は、走らせるコマンド自身が書く印のファイルと、待つ側の出力で決める——
負荷の高いとき（まさに #493 の状況）でも結果が変わらないように。待ちの上限（`LIMIT`）は、変異で固まったときに打ち切るためだけにある。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、壊したのに緑のままなら失格とする。
**本体の docstring の「守る」の行数と変異の数が等しいことを、テスト自身が数える。**
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "run-serial.py"
LIMIT = 30.0

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def build_repo(root: Path, decl: str | None) -> Path:
    """偽のリポジトリと worktree 1 本。宣言はメインの作業ツリーにだけ置く（worktree の写しとは違う値にする）。"""
    root.mkdir(parents=True)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "t")
    (root / "README.md").write_text("x\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    wt = root.parent / (root.name + "-wt")
    git(root, "worktree", "add", "-q", str(wt), "-b", "wt")
    if decl is not None:
        (root / ".claude").mkdir()
        (root / ".claude" / "dev-loop.md").write_text(decl, encoding="utf-8")
    # worktree の写しには逆の値を置く——本体がこちらを読めば、結果が変わる
    (wt / ".claude").mkdir()
    (wt / ".claude" / "dev-loop.md").write_text("並行の検査: 5\n", encoding="utf-8")
    assert_not_real_repo(root)
    assert_not_real_repo(wt)
    return wt


# 走らせるコマンド: 印 <名前>.start を書き、<名前>.go が現れるまで待ち（相手が来るのを待つ役なら <相手>.start を待つ）、
# <名前>.end を書く。待ちは LIMIT で打ち切る（打ち切ったら <名前>.timeout を書く）。
WORKER = r"""
import sys, time, pathlib, signal
d, name, wait_for = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if len(sys.argv) > 5 and sys.argv[5] == "ignore-term":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)   # ラッパーから渡された SIGTERM でも終わらない役
(d / f"{name}.start").write_text(str(time.time()))
end = time.time() + float(sys.argv[4])
while not (d / wait_for).exists():
    if time.time() > end:
        (d / f"{name}.timeout").write_text("")
        break
    time.sleep(0.05)
(d / f"{name}.end").write_text(str(time.time()))
"""


def launch(script: Path, cwd: Path, cmd: list[str], err: Path, env: dict | None = None) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, str(script), "--", *cmd], cwd=cwd,
                            stdout=subprocess.DEVNULL, stderr=open(err, "w"), env=env)


def wait_until(cond, procs=(), limit=LIMIT) -> bool:
    end = time.time() + limit
    while time.time() < end:
        if cond():
            return True
        if procs and all(p.poll() is not None for p in procs):
            return cond()
        time.sleep(0.05)
    return False


def finish(*procs: subprocess.Popen) -> list[int | None]:
    codes = []
    for p in procs:
        try:
            codes.append(p.wait(timeout=LIMIT))
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            codes.append(None)
    return codes


def observe_serial(script: Path, tmp: Path, tag: str, decl: str | None = None, sigterm: bool = False) -> dict:
    """枠 1 になるはずの宣言（既定は宣言なし）で、メインの作業ツリーと worktree から 1 本ずつ起こす。

    `sigterm` なら、A が走り出したあと A の*ラッパー*に SIGTERM を送ってから B を起こす
    （A のコマンドは SIGTERM を無視して走り続ける役）——ラッパーが枠を離せば B が先に始まる。"""
    root = tmp / f"{tag}-serial"
    wt = build_repo(root, decl)
    marks = tmp / f"{tag}-serial-marks"
    marks.mkdir()
    worker = tmp / f"{tag}-worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    err_a, err_b = marks / "a.err", marks / "b.err"
    # A は go を待つ。B は A の後なら go を待たずに済むよう、自分の go として A.end を待つ
    extra = ["ignore-term"] if sigterm else []
    a = launch(script, root, [sys.executable, str(worker), str(marks), "a", "go", "10", *extra], err_a)
    started = wait_until(lambda: (marks / "a.start").exists(), [a])
    if sigterm:
        a.send_signal(signal.SIGTERM)
        time.sleep(0.3)  # 変異では、この間にラッパーが終わって枠が外れる（緑のときは何も起きない）
    # B は worktree の*サブディレクトリ*から起こす——cwd が worktree の根でなくても同じ枠になること
    sub = wt / "sub"
    sub.mkdir()
    b = launch(script, sub, [sys.executable, str(worker), str(marks), "b", "a.end", "10"], err_b)
    said = wait_until(lambda: "待っている" in err_b.read_text(encoding="utf-8")
                      or (marks / "b.start").exists(), [b], limit=10)
    b_early = (marks / "b.start").exists() and not (marks / "a.end").exists()
    (marks / "go").write_text("")
    codes = finish(a, b)
    text_b = err_b.read_text(encoding="utf-8")
    said_one = "1 として扱う" in err_a.read_text(encoding="utf-8") + text_b
    return {
        "1 として扱うと言った": said_one,
        "A が走った": started,
        "B は A が終わるまで始めなかった": not b_early and (marks / "b.start").exists(),
        "B が待っていると言った": said and "待っている" in text_b,
        "B が A を名指しした": f"pid {a.pid}" in text_b,
        "終了コード": codes,
    }


def observe_parallel(script: Path, tmp: Path, tag: str) -> dict:
    """宣言 `並行の検査: 2` で、2 本が互いの始まりを待つ——同時に走れなければ時間切れになる。"""
    root = tmp / f"{tag}-par"
    wt = build_repo(root, "# 追補\n並行の検査: 2\n")
    marks = tmp / f"{tag}-par-marks"
    marks.mkdir()
    worker = tmp / f"{tag}-pworker.py"
    worker.write_text(WORKER, encoding="utf-8")
    a = launch(script, root, [sys.executable, str(worker), str(marks), "a", "b.start", "10"], marks / "a.err")
    b = launch(script, wt, [sys.executable, str(worker), str(marks), "b", "a.start", "10"], marks / "b.err")
    codes = finish(a, b)
    return {
        "2 本が同時に走った": not (marks / "a.timeout").exists() and not (marks / "b.timeout").exists()
        and (marks / "a.end").exists() and (marks / "b.end").exists(),
        "終了コード": codes,
    }


def run_once(script: Path, cwd: Path, cmd: list[str], env=None, limit=LIMIT) -> tuple[int | None, str]:
    try:
        proc = subprocess.run([sys.executable, str(script), "--", *cmd], cwd=cwd, capture_output=True,
                              text=True, timeout=limit, env=env)
    except subprocess.TimeoutExpired:
        return None, "（時間切れ）"
    return proc.returncode, proc.stderr


def observe_codes(script: Path, tmp: Path, tag: str) -> dict:
    root = tmp / f"{tag}-codes"
    build_repo(root, None)
    py = sys.executable
    seven, _ = run_once(script, root, [py, "-c", "import sys; sys.exit(7)"])
    zero, _ = run_once(script, root, [py, "-c", "pass"])
    term, _ = run_once(script, root, [py, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"])
    missing, err_missing = run_once(script, root, ["/no/such/command-i493"])
    usage, _ = run_once(script, root, [])
    return {"7": seven, "0": zero, "SIGTERM": term, "見つからない": missing,
            "見つからないと言う": "見つからない" in err_missing, "コマンドなし": usage}


def observe_nested(script: Path, tmp: Path, tag: str) -> dict:
    root = tmp / f"{tag}-nested"
    build_repo(root, None)
    mark = tmp / f"{tag}-nested.done"
    inner = [sys.executable, str(script), "--", sys.executable, "-c",
             f"open({str(mark)!r}, 'w').write('x')"]
    code, _ = run_once(script, root, inner, limit=10)
    return {"入れ子が固まらずに走った": code == 0 and mark.exists()}


def observe_cannot(script: Path, tmp: Path, tag: str) -> dict:
    outside = tmp / f"{tag}-outside"
    outside.mkdir()
    assert_not_real_repo(outside)
    mark = tmp / f"{tag}-outside.ran"
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(tmp), GIT_DIR=str(outside / "no-such-git-dir"))
    code, err = run_once(script, outside, [sys.executable, "-c", f"open({str(mark)!r}, 'w').write('x')"], env=env)
    return {"125": code == 125, "走らせていない": not mark.exists(), "理由を言う": "走らせていない" in err}


DECLS = {
    # 読めない宣言は 1 として扱い、そう言う（実効の枠が 1 であることまで見る——メッセージだけでは見ない）
    "0": ("並行の検査: 0\n", True),
    "abc": ("並行の検査: abc\n", True),
    "2 行": ("並行の検査: 2\n並行の検査: 3\n", True),
    "全角のコロン": ("並行の検査：2\n", True),
    "箇条書き": ("- 並行の検査: 2\n", True),
    # コードブロックと HTML コメントの中は宣言でない——枠は 1 のまま（言うことは無い）
    "コードブロックの中": ("例:\n```\n並行の検査: 2\n```\n", False),
    "HTML コメントの中": ("<!--\n並行の検査: 2\n-->\n", False),
}


def observe_decl(script: Path, tmp: Path, tag: str) -> dict:
    out = {}
    for i, (label, (decl, _)) in enumerate(DECLS.items()):
        got = observe_serial(script, tmp, f"{tag}-d{i}", decl=decl)
        out[label] = (got["B は A が終わるまで始めなかった"], got["1 として扱うと言った"], got["終了コード"])
    return out


def observe_sigterm(script: Path, tmp: Path, tag: str) -> dict:
    got = observe_serial(script, tmp, f"{tag}-term", sigterm=True)
    return {"ラッパーに SIGTERM を送っても B は A が終わるまで始めなかった": got["B は A が終わるまで始めなかった"]}


MUTATIONS = {
    # 守る 1: 枠の本数を超えて同時に走らせない
    "枠を取らずに走らせる": (
        "                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)",
        "                pass"),
    # 守る 2: 待っていることと走っているものを言う
    "待っていると言わない": (
        "            say(f\"待っている（同じリポジトリで同時に {slots} 本まで）。走っているもの: \"\n"
        "                + (\"; \".join(running) if running else \"（読めなかった）\"))",
        "            pass"),
    # 守る 3: 終了コードをそのまま返す
    "終了コードを捨てる": (
        "    return 128 - code if code < 0 else code",
        "    return 0"),
    # 守る 4: 入れ子は待たずに走らせる
    "入れ子でも枠を取る": (
        "    if os.environ.get(ENV) == str(lockdir):",
        "    if False:"),
    # 守る 5: 枠を決められなければ走らせない
    "決められなくても走らせる": (
        "        say(\"枠を決められない（git の共通ディレクトリが決まらない）——走らせていない\")\n        return CANNOT",
        "        return run(command, dict(os.environ))"),
    # 守る 6: 宣言が読めない値なら 1（言うだけでなく、実効の枠が 1）
    "読めない値で 1 と言いつつ 3 本にする": (
        "        return 1, f\"`並行の検査:` の値 {value!r} は 1 以上の整数でない——1 として扱う\"",
        "        return 3, f\"`並行の検査:` の値 {value!r} は 1 以上の整数でない——1 として扱う\""),
    # 守る 7: コードブロックと HTML コメントの中は数えない
    "コードブロックの中の行を数える": (
        '        if stripped.startswith(("```", "~~~")):',
        "        if False:"),
    # 守る 8: ラッパーがシグナルを受けても、コマンドが終わるまで枠を離さない
    "ラッパーがシグナルで先に終わる": (
        "    previous = {s: signal.signal(s, forward) for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)}",
        "    previous = {}"),
}


OBSERVERS = {
    "serial": observe_serial, "parallel": observe_parallel, "codes": observe_codes, "nested": observe_nested,
    "cannot": observe_cannot, "decl": observe_decl, "sigterm": observe_sigterm,
}

# 変異ごとに当てる観測（全部を当てると、待ちの上限で止まる観測が重なって数分かかる）。
# **観測を絞っても判定は「正しい本体の同じ観測と違うか」で、どれを当てるかは変異の狙いで決める。**
MUTATION_PROBE = {
    "枠を取らずに走らせる": ("serial",),
    "待っていると言わない": ("serial",),
    "終了コードを捨てる": ("codes",),
    "入れ子でも枠を取る": ("nested",),
    "決められなくても走らせる": ("cannot",),
    "読めない値で 1 と言いつつ 3 本にする": ("decl",),
    "コードブロックの中の行を数える": ("decl",),
    "ラッパーがシグナルで先に終わる": ("sigterm",),
}


def observe_all(script: Path, tmp: Path, tag: str, only=None) -> dict:
    return {k: f(script, tmp, tag) for k, f in OBSERVERS.items() if only is None or k in only}


def judge(o: dict) -> None:
    s = o["serial"]
    print("枠 1（宣言なし）: メインの作業ツリーと worktree の 2 本")
    check("A が走った", s["A が走った"])
    check("B は A が終わるまで始めなかった（worktree をまたいで同じ枠）", s["B は A が終わるまで始めなかった"])
    check("B が待っていると言った", s["B が待っていると言った"])
    check("B が走っているもの（A の pid）を名指しした", s["B が A を名指しした"])
    check("両方 0 で終わった", s["終了コード"] == [0, 0])
    print("\n宣言 `並行の検査: 2`（worktree の写しの 5 は読まない）")
    check("2 本が同時に走った", o["parallel"]["2 本が同時に走った"])
    check("両方 0 で終わった", o["parallel"]["終了コード"] == [0, 0])
    c = o["codes"]
    print("\n終了コード")
    check("7 を返すコマンドで 7", c["7"] == 7)
    check("0 を返すコマンドで 0", c["0"] == 0)
    check("SIGTERM で終わったら 143", c["SIGTERM"] == 143)
    check("見つからないコマンドで 127", c["見つからない"] == 127)
    check("見つからないと言う", c["見つからないと言う"])
    check("コマンドが無ければ 2", c["コマンドなし"] == 2)
    print("\n入れ子")
    check("入れ子が固まらずに走った", o["nested"]["入れ子が固まらずに走った"])
    print("\n枠を決められないとき")
    k = o["cannot"]
    check("125 を返す", k["125"])
    check("コマンドを走らせていない", k["走らせていない"])
    check("走らせていないと言う", k["理由を言う"])
    print("\n読めない宣言・コードブロックと HTML コメントの中の宣言では、実効の枠が 1")
    for label, (serial, said, codes) in o["decl"].items():
        check(f"{label}: B は A が終わるまで始めなかった", serial)
        check(f"{label}: 両方 0 で終わった", codes == [0, 0])
        if DECLS[label][1]:
            check(f"{label}: 1 として扱うと言う", said)
        else:
            check(f"{label}: 何も言わない（宣言ではない）", not said)
    print("\nラッパー自身へのシグナル")
    for name, ok in o["sigterm"].items():
        check(name, ok)


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t).resolve()
        assert_not_real_repo(tmp)
        correct = observe_all(SCRIPT, tmp, "ok")
        judge(correct)

        print("\n変異テスト（壊したのに緑なら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for i, (name, (needle, replacement)) in enumerate(MUTATIONS.items()):
            if needle not in source:
                check(f"変異を当てる先がある: {name}", False)
                continue
            mdir = tmp / f"mut{i}"
            mdir.mkdir()
            mutated = mdir / "run-serial.py"
            mutated.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            only = MUTATION_PROBE[name]
            got = observe_all(mutated, tmp, f"m{i}", only)
            check(f"変異を殺せる: {name}", got != {k: correct[k] for k in only})

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件",
              len(promises) == len(MUTATIONS))

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
    print("順番待ちのテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
