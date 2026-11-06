#!/usr/bin/env python3
"""`run-serial.py`（重い検査・アプリの起動の順番待ち。#493）の回帰テスト。

    python3 scripts/test-run-serial.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/cruise/scripts/run-serial.py`）——
cruise はどのリポジトリでも使うので、対象リポジトリの `scripts/` に在ることを当てにできない（`test-find-cycle.py` と同じ形）。

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリ（と、その worktree）を作り、そこだけを対象にする
（`assert_not_real_repo`）。本体は cwd から共通ディレクトリを決めるので、歯止めが無いと**このリポジトリの `.git` に枠を作る**。

**時間で判定しない。** 「同時に走った」「待った」は、走らせるコマンド自身が書く印のファイルと、待つ側の出力で決める——
負荷の高いとき（まさに #493 の状況）でも結果が変わらないように。待ちの上限（`LIMIT`）は、変異で固まったときに打ち切るためだけにある。
**例外は期限（#897）の観測**——期限（`--timeout 3`）そのものは時間だが、判定は印（終了コード・`期限切れ` の行・孫が居るか・B の印）で決める。
**呼び出し元が居なくなった待ち手（#897）**は、中間のプロセスが run-serial を起こして先に終わる形で作る（親を失った run-serial はこのテストの子でないので、
居なくなったかを `kill -0` で見る）。終了コード 125 は、本体を読み込んで `os.getppid` を差し替えた `main` で見る。
**既定の期限と入れ子の期限**は、本体を読み込んで `run` を差し替えた `main` が渡す期限で見る（3600 秒を待たない。#897 の 1 パス目）。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、壊したのに判定（`check`）が 1 つも落ちなければ失格とする——
**観測の値が正しい本体と違うだけでは「見つけた」に数えない**（#745。値が違っても判定が通るなら、そのテストは壊れたコードで緑になる）。
**本体の docstring の「守る」の行数と変異の数が等しいことを、テスト自身が数える。**
"""
from __future__ import annotations

import ast
import os
import re
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


def check(name: str, cond: bool, sink: list[str] | None = None, quiet: bool = False) -> None:
    if not quiet:
        print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        (failures if sink is None else sink).append(name)


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def build_repo(root: Path, decl: str | bytes | None) -> Path:
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
        target = root / ".claude" / "dev-loop.md"
        if isinstance(decl, bytes):
            target.write_bytes(decl)
        else:
            target.write_text(decl, encoding="utf-8")
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
    for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(s, signal.SIG_IGN)   # ラッパーから渡されたシグナルでも終わらない役
(d / f"{name}.start").write_text(str(time.time()))
end = time.time() + float(sys.argv[4])
while not (d / wait_for).exists():
    if time.time() > end:
        (d / f"{name}.timeout").write_text("")
        break
    time.sleep(0.05)
(d / f"{name}.end").write_text(str(time.time()))
"""


def launch(script: Path, cwd: Path, cmd: list[str], err: Path, env: dict | None = None,
           opts: tuple[str, ...] = ()) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, str(script), *opts, "--", *cmd], cwd=cwd,
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


def observe_serial(script: Path, tmp: Path, tag: str, decl: str | bytes | None = None, sig: int | None = None) -> dict:
    """枠 1 になるはずの宣言（既定は宣言なし）で、メインの作業ツリーと worktree から 1 本ずつ起こす。

    `sig` を渡すと、A が走り出したあと A の*ラッパー*にそのシグナルを送ってから B を起こす
    （A のコマンドはシグナルを無視して走り続ける役）——ラッパーが枠を離せば B が先に始まる。"""
    root = tmp / f"{tag}-serial"
    wt = build_repo(root, decl)
    marks = tmp / f"{tag}-serial-marks"
    marks.mkdir()
    worker = tmp / f"{tag}-worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    err_a, err_b = marks / "a.err", marks / "b.err"
    # A は go を待つ。B は A の後なら go を待たずに済むよう、自分の go として A.end を待つ
    extra = ["ignore-term"] if sig else []
    a = launch(script, root, [sys.executable, str(worker), str(marks), "a", "go", "10", *extra], err_a)
    started = wait_until(lambda: (marks / "a.start").exists(), [a])
    if sig:
        a.send_signal(sig)
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


PARALLEL_DECLS = {
    "宣言 2": "# 追補\n並行の検査: 2\n",
    # 宣言の行末の HTML コメントは外して読む——2 本のまま（コメントの前を捨てれば 1 本になり、互いを待って時間切れ）
    "行末に HTML コメントのある宣言 2": "並行の検査: 2 <!-- メモ -->\n",
}


def observe_parallel(script: Path, tmp: Path, tag: str) -> dict:
    return {label: observe_parallel_one(script, tmp, f"{tag}-p{i}", decl)
            for i, (label, decl) in enumerate(PARALLEL_DECLS.items())}


def observe_parallel_one(script: Path, tmp: Path, tag: str, decl: str) -> dict:
    """宣言 `並行の検査: 2` で、2 本が互いの始まりを待つ——同時に走れなければ時間切れになる。"""
    root = tmp / f"{tag}-par"
    wt = build_repo(root, decl)
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


def run_once(script: Path, cwd: Path, cmd: list[str], env=None, limit=LIMIT,
             opts: tuple[str, ...] = ()) -> tuple[int | None, str]:
    try:
        proc = subprocess.run([sys.executable, str(script), *opts, "--", *cmd], cwd=cwd, capture_output=True,
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
    # コマンド自身が 124 を返したとき——期限切れとは出力の行で見分ける（#897）
    own124, err_own124 = run_once(script, root, [py, "-c", "import sys; sys.exit(124)"])
    # `--timeout` の値と `--` の前の引数が使い方に合わなければ、走らせずに 2（#897）
    bad = {}
    for label, opts in (("--timeout 0", ("--timeout", "0")), ("--timeout abc", ("--timeout", "abc")),
                        ("--timeout=-5", ("--timeout=-5",)), ("--timeout の値なし", ("--timeout",)),
                        ("知らない引数", ("--bogus",))):
        mark = tmp / f"{tag}-codes-bad{len(bad)}.ran"
        code, err = run_once(script, root, [py, "-c", f"open({str(mark)!r}, 'w').write('x')"], opts=opts)
        bad[label] = (code, mark.exists(), "run-serial:" in err)
    good_mark = tmp / f"{tag}-codes-good.ran"
    good, _ = run_once(script, root, [py, "-c", f"open({str(good_mark)!r}, 'w').write('x')"], opts=("--timeout=30",))
    return {"7": seven, "0": zero, "SIGTERM": term, "見つからない": missing,
            "見つからないと言う": "見つからない" in err_missing, "コマンドなし": usage,
            "自分で 124": own124, "自分で 124 のとき期限切れと言わない": "期限切れ" not in err_own124,
            "使い方に合わない": bad, "--timeout=30 で走った": good == 0 and good_mark.exists()}


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
    "7 桁の値": ("並行の検査: 1234567\n", True),
    "長いコードブロックの中": ("````md\n```\n並行の検査: 2\n```\n````\n", False),
    "行の途中で始まる HTML コメントの中": ("メモ <!--\n並行の検査: 2\n-->\n", False),
    # ファイルが在るのに読めない（UTF-8 でない）——黙って 1 にしない
    # コードブロックの閉じ行は CommonMark のとおり（#740・#741）——字下げした行・別の文字の行では閉じない
    "空白 4 つで字下げした閉じ行": ("```\n    ```\n並行の検査: 2\n```\n", False),
    "別の文字の閉じ行": ("```\n~~~\n並行の検査: 2\n```\n", False),
    "UTF-8 でない": ("並行の検査: 2\n".encode("utf-8") + b"\xff\xfe\n", True),
}


def observe_decl(script: Path, tmp: Path, tag: str) -> dict:
    out = {}
    for i, (label, (decl, _)) in enumerate(DECLS.items()):
        got = observe_serial(script, tmp, f"{tag}-d{i}", decl=decl)
        out[label] = (got["B は A が終わるまで始めなかった"], got["1 として扱うと言った"], got["終了コード"])
    return out


# `slots_from` を直に当てる試料（#740・#741・#743・#745・#739・#758 の Issue に書いた形のまま。見出しのコメントがどの Issue の形か）。
# 期待値は正しい本体の値（judge が見る）。宣言の値が 8 なら「閉じない・始める」側（宣言はコードブロックの中で、1 のまま）、
# 3 なら「閉じる・始めない」側（宣言は外で、3 と読む）。例外は「BOM が 2 つ」だけ——3 を書式に合わない行として読み、1 と言う。
# 3 つの写し（run-serial・check-unattended-env・parent-issue）の突き合わせは `scripts/test-fence-copies.py` が持つ（ここは run-serial だけ）。
PARSE_SAMPLES = {
    "字下げした ``` の後ろの例示": ("```\n    ```\n並行の検査: 8\n```", (1, None)),
    "~~~ の後ろの例示": ("```\n~~~\n並行の検査: 8\n```", (1, None)),
    "行末の HTML コメント": ("並行の検査: 3 <!-- メモ -->", (3, None)),
    # #743: 閉じ行の判定を CommonMark に合わせた 3 形
    "タブで字下げした閉じ行": ("```\n\t```\n並行の検査: 8\n```", (1, None)),
    "後ろに全角の空白のある閉じ行": ("```\n```\u3000\n並行の検査: 8\n```", (1, None)),
    "後ろに \\x0b のある閉じ行": ("```\n```\x0b\n並行の検査: 8\n```", (1, None)),
    "バッククォートを含む情報文字列": ("```a`b\n並行の検査: 3", (3, None)),
    # #745: わざと壊しても通ってしまった 7 形と BOM
    "空白 3 つで字下げした閉じ行": ("```\n   ```\n並行の検査: 3", (3, None)),
    "開いた印とちょうど同じ数の閉じ行": ("````\n````\n並行の検査: 3", (3, None)),
    "後ろに文字のある閉じ行": ("```\n``` x\n並行の検査: 8\n```", (1, None)),
    "空白 4 つで字下げした開き": ("    ```\n並行の検査: 3", (3, None)),
    "行の途中の開き": ("メモ ```\n並行の検査: 3", (3, None)),
    "~~~ の開き": ("~~~\n並行の検査: 8\n~~~", (1, None)),
    "コメントの中の開き": ("<!--\n```-->\n並行の検査: 3", (3, None)),
    "先頭の BOM": ("\ufeff並行の検査: 3", (3, None)),
    # #739 の 1 パス目: 開き行は元の行で見る（コメントを外した残りで見ない）
    "コメントの後ろの印": ("<!-- -->```\n並行の検査: 3", (3, None)),
    "コメントで区切ったバッククォートの情報文字列": ("```a<!--`-->\n並行の検査: 3", (3, None)),
    "情報文字列の <!--": ("```<!--\n-->\n並行の検査: 8\n```", (1, None)),
    "情報文字列の <!-- で始めたコードブロックの後ろ": ("```<!--\n```\n並行の検査: 3", (3, None)),
    # #758: \x0c で行を分けない・段落の途中のコメントの後ろの印・BOM は 1 つだけ外す
    # dup-counts-ok: BOM （「1 つだけ外す」は外す数、試料の「2 つ」は置いた数で、別のものを数えている）
    "後ろに \\x0c のある閉じ行": ("```\n```\x0c\n並行の検査: 8\n```", (1, None)),
    "段落の途中のコメントの後ろの印": ("memo <!--\n```\n-->\n並行の検査: 8", (1, None)),
    # #758 の周の /code-review 1 パス目: 行頭のコメントを閉じた行で開き直したコメントは行頭のコメントのまま（GitHub は後ろを隠す）
    "行頭のコメントを閉じた行で開き直したコメント": ("<!--\n--> x <!--\n```\n```\n並行の検査: 8\n-->", (1, None)),
    # #758 の周の /code-review 2 パス目: リストや引用の印の直後のコメントは行頭のコメント（GitHub は後ろを隠す）
    "リストの印の直後のコメント": ("- <!--\n```\n```\n並行の検査: 8\n-->", (1, None)),
    "BOM が 2 つ": ("\ufeff\ufeff並行の検査: 3",
                   (1, f"`並行の検査` の行が書式に合わない（{chr(0xfeff) + '並行の検査: 3'!r}）——1 として扱う")),
}


def observe_parse(script: Path, tmp: Path, tag: str) -> dict:
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"rs_{tag}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {label: mod.slots_from(text) for label, (text, _) in PARSE_SAMPLES.items()}


# SIGINT と SIGTERM を数えるコマンド: pid を書き、受けたシグナルを 1 行ずつ log に足し、SIGTERM を受けたら終わる（LIMIT で打ち切る）。
COUNTER = r"""
import os, sys, time, pathlib, signal
d = pathlib.Path(sys.argv[1])
def note(signum, _frame):
    with open(d / "log", "a") as f:
        f.write(("INT" if signum == signal.SIGINT else "TERM") + "\n")
signal.signal(signal.SIGINT, note)
signal.signal(signal.SIGTERM, note)
(d / "pid").write_text(str(os.getpid()))
end = time.time() + float(sys.argv[2])
while time.time() < end:
    if "TERM" in ((d / "log").read_text() if (d / "log").exists() else ""):
        break
    time.sleep(0.05)
"""


def observe_sigint(script: Path, tmp: Path, tag: str) -> dict:
    """SIGINT がコマンドに何度届くか（#739）。終わらせる合図に、最後にラッパーへ SIGTERM を送る（ラッパーが渡す）。

    - グループ: ラッパーを独立のプロセスグループで起こし、`os.killpg` でグループ全体に SIGINT を送る（端末の Ctrl-C と同じ配り方）。
    - ずらし: コマンドに直に SIGINT を送り、受けたのを見てからラッパーに SIGINT を送る——グループへの配りを時間をずらして作る。
      グループに同時に届くと、ラッパーの転送とコマンドへの直接の SIGINT は 1 つに重なりうる（標準のシグナルは数を持たない）ので、
      転送の 2 度目は「ずらし」で見る。ラッパーは SIGINT を SIGTERM より先に扱う（番号の順）ので、転送があれば SIGTERM より前に log に載る。"""
    out = {}
    for label, group in (("グループ", True), ("ずらし", False)):
        root = tmp / f"{tag}-int{int(group)}"
        build_repo(root, None)
        marks = tmp / f"{tag}-int{int(group)}-marks"
        marks.mkdir()
        counter = tmp / f"{tag}-int{int(group)}-counter.py"
        counter.write_text(COUNTER, encoding="utf-8")
        proc = subprocess.Popen([sys.executable, str(script), "--", sys.executable, str(counter), str(marks), str(LIMIT)],
                                cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=group)
        log = marks / "log"
        ints = lambda: (log.read_text().split() if log.exists() else []).count("INT")
        if wait_until(lambda: (marks / "pid").exists() and (marks / "pid").read_text().strip(), [proc]):
            if group:
                os.killpg(proc.pid, signal.SIGINT)
            else:
                os.kill(int((marks / "pid").read_text()), signal.SIGINT)
                if wait_until(lambda: ints() >= 1, [proc], limit=10):
                    proc.send_signal(signal.SIGINT)
            if wait_until(lambda: ints() >= 1, [proc], limit=10):
                proc.send_signal(signal.SIGTERM)
        code = finish(proc)[0]
        out[label] = {"log": log.read_text().split() if log.exists() else [], "終了コード": code}
    return out


def observe_sigterm(script: Path, tmp: Path, tag: str) -> dict:
    out = {}
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        got = observe_serial(script, tmp, f"{tag}-sig{int(sig)}", sig=sig)
        out[f"ラッパーに {sig.name} を送っても B は A が終わるまで始めなかった"] = got["B は A が終わるまで始めなかった"]
    return out


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# 期限切れで止められる孫: `bash -c "<これ>; :"` の下で走る（`; :` があるので bash は exec せず、これは run-serial の孫になる）。
# pid を <d>/gc.pid に、始まりの印を <d>/a.start に書き、GC_LIMIT 秒走ったら <d>/a.timeout を書いて終わる（止められなかった印）。
# 第 3 引数が ignore-term なら SIGTERM を無視する（SIGKILL でしか止まらない役）。late-child なら SIGTERM を受けたときに子（`sleep`）を起こし、
# その pid を <d>/late.pid に書いて走り続ける（猶予のあいだに生まれた子孫の役。#897 の 2 パス目）。
GRANDCHILD = r"""
import os, sys, time, pathlib, signal, subprocess
d = pathlib.Path(sys.argv[1])
if len(sys.argv) > 2 and sys.argv[2] == "ignore-term":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
if len(sys.argv) > 2 and sys.argv[2] == "late-child":
    def on_term(_s, _f):
        child = subprocess.Popen(["sleep", "30"])
        (d / "late.pid").write_text(str(child.pid))
    signal.signal(signal.SIGTERM, on_term)
(d / "gc.pid").write_text(str(os.getpid()))
(d / "a.start").write_text("")
end = time.time() + 20
while time.time() < end:
    time.sleep(0.05)
(d / "a.timeout").write_text("")
"""
TIMEOUT_SECONDS = "3"


def observe_timeout(script: Path, tmp: Path, tag: str, mode: str = "plain") -> dict:
    """A を `--timeout 3` で起こし、孫（`bash -c` の下）が期限まで走り続ける。B は worktree から起こして待たせる（#897）。

    判定は印で決める——A の終了コード・出力、孫が居るか、B が待っていると言って走りきったか。期限の 3 秒は、
    B が A の走っているあいだに並ぶための余裕で、判定には使わない。"""
    root = tmp / f"{tag}-to-{mode}"
    wt = build_repo(root, None)
    marks = tmp / f"{tag}-to-{mode}-marks"
    marks.mkdir()
    gc = tmp / f"{tag}-to-{mode}-gc.py"
    gc.write_text(GRANDCHILD, encoding="utf-8")
    worker = tmp / f"{tag}-to-{mode}-worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    err_a, err_b = marks / "a.err", marks / "b.err"
    inner = f"{sys.executable} {gc} {marks} {({'kill': 'ignore-term', 'late': 'late-child'}).get(mode, 'x')}; :"
    a = launch(script, root, ["bash", "-c", inner], err_a, opts=("--timeout", TIMEOUT_SECONDS))
    started = wait_until(lambda: (marks / "gc.pid").exists() and (marks / "gc.pid").read_text().strip(), [a])
    gc_pid = int((marks / "gc.pid").read_text()) if started else None
    b = launch(script, wt, [sys.executable, str(worker), str(marks), "b", "a.start", "10"], err_b)
    code_a, code_b = finish(a, b)
    gone = gc_pid is not None and wait_until(lambda: not alive(gc_pid), limit=5)
    late_text = (marks / "late.pid").read_text().strip() if (marks / "late.pid").exists() else ""
    late_pid = int(late_text) if late_text.isdigit() else None
    late_gone = late_pid is not None and wait_until(lambda: not alive(late_pid), limit=5)
    for pid in (gc_pid, late_pid):
        if pid is not None and alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)   # 変異で残った孫・その子を片付ける（観測には使わない）
            except ProcessLookupError:
                pass
    text_a, text_b = err_a.read_text(encoding="utf-8"), err_b.read_text(encoding="utf-8")
    return {
        "孫が走った": started,
        "A は 124": code_a == 124,
        "A の終了コード": code_a,
        "A が期限切れと言った": any(line.startswith("run-serial: 期限切れ") for line in text_a.splitlines()),
        "孫が止まった": gone and not (marks / "a.timeout").exists(),
        "B が待っていると言った": "待っている" in text_b,
        "B が走りきった": (marks / "b.end").exists() and code_b == 0,
        "SIGKILL と言った": "SIGKILL" in text_a,
        "猶予のあいだに生まれた子が止まった": late_gone,
    }


def observe_timeout_kill(script: Path, tmp: Path, tag: str) -> dict:
    return observe_timeout(script, tmp, tag, mode="kill")


def observe_timeout_late(script: Path, tmp: Path, tag: str) -> dict:
    return observe_timeout(script, tmp, tag, mode="late")


# 呼び出し元の役: run-serial を子として起こし（コマンドは B）、その pid を書き、待っていると言うのを見てから終わる——run-serial は親を失う
MIDDLE = r"""
import subprocess, sys, pathlib, time
script, cwd, marks, worker = sys.argv[1:5]
d = pathlib.Path(marks)
w = subprocess.Popen([sys.executable, script, "--", sys.executable, worker, marks, "b", "b.go-never", "1"],
                     cwd=cwd, stdout=subprocess.DEVNULL, stderr=open(d / "w.err", "w"))
(d / "w.pid").write_text(str(w.pid))
end = time.time() + 10
while "待っている" not in (d / "w.err").read_text() and time.time() < end:
    time.sleep(0.05)
"""


def observe_orphan(script: Path, tmp: Path, tag: str) -> dict:
    """A が枠を持つあいだに、呼び出し元の役が W（run-serial）を起こして終わる。W は枠を取らずに終わるはず（#897）。

    W は親を失った後はこのテストの子ではないので、終了コードは読めない——居なくなったかを `kill -0` で見る。
    終了コード（125）は、本体を読み込んで `os.getppid` を差し替えた `main` で見る（同じ判定の、もう 1 つの観測点）。"""
    root = tmp / f"{tag}-orphan"
    wt = build_repo(root, None)
    marks = tmp / f"{tag}-orphan-marks"
    marks.mkdir()
    worker = tmp / f"{tag}-orphan-worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    middle = tmp / f"{tag}-orphan-middle.py"
    middle.write_text(MIDDLE, encoding="utf-8")
    a = launch(script, root, [sys.executable, str(worker), str(marks), "a", "go", "20"], marks / "a.err")
    wait_until(lambda: (marks / "a.start").exists(), [a])
    mid = subprocess.Popen([sys.executable, str(middle), str(script), str(wt), str(marks), str(worker)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finish(mid)
    said_wait = "待っている" in (marks / "w.err").read_text(encoding="utf-8")
    w_pid = int((marks / "w.pid").read_text()) if (marks / "w.pid").exists() else None
    gone = w_pid is not None and wait_until(lambda: not alive(w_pid), limit=10)
    (marks / "go").write_text("")
    finish(a)
    # 変異では W が枠を取って B を走らせる——その印を待つ（正しい本体では来ない）
    b_ran = wait_until(lambda: (marks / "b.start").exists(), limit=5 if gone else 15)
    text_w = (marks / "w.err").read_text(encoding="utf-8")

    import contextlib
    import importlib.util
    import io
    spec = importlib.util.spec_from_file_location(f"rs_orphan_{tag}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mark = tmp / f"{tag}-orphan-inproc.ran"
    real_getppid, here = os.getppid, os.getcwd()
    calls = iter([4242])     # 起動したときの親は 4242、それ以降は 1（親が居なくなった）
    os.getppid = lambda: next(calls, 1)
    try:
        os.chdir(root)
        with contextlib.redirect_stderr(io.StringIO()) as said:
            code = mod.main(["--", sys.executable, "-c", f"open({str(mark)!r}, 'w').write('x')"])
    finally:
        os.getppid = real_getppid
        os.chdir(here)
    return {
        "W が待っていると言った": said_wait,
        "W が枠を取らずに終わった": gone and not b_ran,
        "W が呼び出し元が居ないと言った": "呼び出し元" in text_w,
        "main は 125": code == 125,
        "main は走らせていない": not mark.exists(),
        "main は呼び出し元が居ないと言った": "呼び出し元" in said.getvalue(),
    }


def observe_deadline(script: Path, tmp: Path, tag: str) -> dict:
    """`main` が `run` に渡す期限（#897）。本体を読み込み、`run` を差し替えて受け取った期限を記録する——期限の秒数だけ待たずに、
    既定の経路（`--timeout` なし）と入れ子の経路（枠を取らずに走らせる）の期限を見る。既定の値は docstring の「期限」の節から読む。"""
    import contextlib
    import importlib.util
    import io
    root = tmp / f"{tag}-deadline"
    build_repo(root, None)
    spec = importlib.util.spec_from_file_location(f"rs_deadline_{tag}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    documented = re.search(r"既定の `DEFAULT_TIMEOUT`（([0-9]+) 秒）", mod.__doc__ or "")
    got: list = []
    mod.run = lambda command, env, timeout: got.append(timeout) or 0
    lockdir = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=root,
                             capture_output=True, text=True, check=False).stdout.strip() + "/dev-loop-serial"
    here, saved = os.getcwd(), os.environ.pop(mod.ENV, None)
    out = {}
    try:
        os.chdir(root)
        with contextlib.redirect_stderr(io.StringIO()):
            for label, argv, nested in (("既定", ["--", "true"], False), ("--timeout 7", ["--timeout", "7", "--", "true"], False),
                                        ("入れ子・既定", ["--", "true"], True), ("入れ子・--timeout 5", ["--timeout", "5", "--", "true"], True)):
                if nested:
                    os.environ[mod.ENV] = lockdir
                else:
                    os.environ.pop(mod.ENV, None)
                got.clear()
                code = mod.main(argv)
                out[label] = (code, list(got))
    finally:
        os.chdir(here)
        os.environ.pop(mod.ENV, None)
        if saved is not None:
            os.environ[mod.ENV] = saved
    out["docstring の既定"] = int(documented.group(1)) if documented else None
    out["DEFAULT_TIMEOUT"] = getattr(mod, "DEFAULT_TIMEOUT", None)
    return out


# 持ち主の役（#898）: 1 行出して <名前>.start を書き、go が現れるまで待つ。`tick` なら待つあいだ出力を出し続ける（出力が進む持ち主）、
# `quiet` なら最初の 1 行の後は何も出さない（出力が止まった持ち主）。
TICKER = r"""
import sys, time, pathlib
d, name, mode = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
print(f"{name} を始めた", flush=True)
(d / f"{name}.start").write_text("")
end = time.time() + 60
while not (d / "go").exists() and time.time() < end:
    if mode == "tick":
        print("進んでいる", flush=True)
    time.sleep(0.1)
"""

# 本体を読み込み、`STALL`・`REPORT` を差し替えて `main` を呼ぶ起動口——600 秒・60 秒を待たずに、止まっている疑いと出し直しを見る（#898）
LAUNCHER = r"""
import importlib.util, sys
spec = importlib.util.spec_from_file_location("rs_launched", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.STALL, mod.REPORT = float(sys.argv[2]), float(sys.argv[3])
sys.exit(mod.main(sys.argv[4:]))
"""
HOLDER_STALL = "3"
HOLDER_REPORT = "1"


def lockdir_state(lockdir: Path) -> dict | None:
    """枠のディレクトリの中身（名前 → 中身・`st_mtime_ns`）。ディレクトリが無ければ None。"""
    if not lockdir.exists():
        return None
    return {f.name: (f.read_bytes(), f.stat().st_mtime_ns) for f in sorted(lockdir.iterdir())}


def report_blocks(text: str) -> list[dict[str, str]]:
    """待ち手の出力を、持ち主を出した塊（`走っているもの:` の行から次のそれまで）ごとに {"pid N": 行} にする。"""
    blocks: list[dict[str, str]] = []
    for line in text.splitlines():
        if "走っているもの:" in line:
            blocks.append({})
        elif blocks and (m := re.match(r"run-serial:   (pid [0-9]+)・", line)):
            blocks[-1][m.group(1)] = line
    return blocks


def by_pid(text: str) -> dict[str, str]:
    """`holders` の口の出力を {"pid N": 行} にする。"""
    return {m.group(1): line for line in text.splitlines() if (m := re.match(r"(pid [0-9]+)・", line))}


def observe_holders(script: Path, tmp: Path, tag: str) -> dict:
    """枠 3 を、出力が止まった持ち主 S・出力が進む持ち主 T・出力がファイルでない持ち主 U でふさぎ、待ち手 W と `holders` の口が出すものを読む（#898）。

    `STALL` は 3 秒・`REPORT` は 1 秒に差し替える（`LAUNCHER`）。判定は出力の行で決め、W は S に疑いが出た塊を見る。"""
    import importlib.util
    root = tmp / f"{tag}-holders"
    wt = build_repo(root, "並行の検査: 3\n")
    marks = tmp / f"{tag}-holders-marks"
    marks.mkdir()
    ticker = tmp / f"{tag}-ticker.py"
    ticker.write_text(TICKER, encoding="utf-8")
    launcher = tmp / f"{tag}-launcher.py"
    launcher.write_text(LAUNCHER, encoding="utf-8")
    worker = tmp / f"{tag}-holders-worker.py"
    worker.write_text(WORKER, encoding="utf-8")
    lockdir = Path(subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=root,
                                  capture_output=True, text=True, check=False).stdout.strip()) / "dev-loop-serial"
    held = {}
    for name, mode, to_file in (("s", "quiet", True), ("t", "tick", True), ("u", "quiet", False)):
        out = open(marks / f"{name}.out", "w") if to_file else subprocess.DEVNULL
        err = open(marks / f"{name}.err", "w") if to_file else subprocess.DEVNULL
        held[name] = subprocess.Popen([sys.executable, str(script), "--", sys.executable, str(ticker), str(marks), name, mode],
                                      cwd=root, stdout=out, stderr=err)
    all_started = wait_until(lambda: all((marks / f"{n}.start").exists() for n in held), list(held.values()))
    pid = {n: f"pid {p.pid}" for n, p in held.items()}
    w_err = marks / "w.err"
    w = subprocess.Popen([sys.executable, str(launcher), str(script), HOLDER_STALL, HOLDER_REPORT,
                          "--", sys.executable, str(worker), str(marks), "w", "w.go-never", "1"],
                         cwd=wt, stdout=subprocess.DEVNULL, stderr=open(w_err, "w"))

    def flagged_block() -> dict[str, str] | None:
        for block in report_blocks(w_err.read_text(encoding="utf-8")):
            if "止まっている疑い" in block.get(pid["s"], ""):
                return block
        return None

    wait_until(lambda: flagged_block() is not None, [w], limit=20)
    block = flagged_block() or {}
    w_text = w_err.read_text(encoding="utf-8")
    before = lockdir_state(lockdir)
    try:
        h = subprocess.run([sys.executable, str(launcher), str(script), HOLDER_STALL, HOLDER_REPORT, "holders"], cwd=wt,
                           capture_output=True, text=True, timeout=10)
        h_code, h_out = h.returncode, h.stdout
    except subprocess.TimeoutExpired:
        h_code, h_out = None, ""
    after = lockdir_state(lockdir)
    w_ran_early = (marks / "w.start").exists()
    (marks / "go").write_text("")
    codes = finish(*held.values(), w)
    # 走り終えた後: 枠のファイルには記録が残るが、pid は居ない
    done = subprocess.run([sys.executable, str(script), "holders"], cwd=root, capture_output=True, text=True, timeout=LIMIT)
    # 枠のディレクトリがまだ無いリポジトリ
    fresh = tmp / f"{tag}-holders-fresh"
    build_repo(fresh, None)
    fresh_dir = Path(subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=fresh,
                                    capture_output=True, text=True, check=False).stdout.strip()) / "dev-loop-serial"
    f = subprocess.run([sys.executable, str(script), "holders"], cwd=fresh, capture_output=True, text=True, timeout=LIMIT)
    extra = subprocess.run([sys.executable, str(script), "holders", "x"], cwd=fresh, capture_output=True, text=True, timeout=LIMIT)

    spec = importlib.util.spec_from_file_location(f"rs_holders_{tag}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    doc = mod.__doc__ or ""
    stall_doc = re.search(r"`STALL`（([0-9]+) 秒）", doc)
    report_doc = re.search(r"`REPORT`（([0-9]+) 秒）", doc)
    hp = by_pid(h_out)
    s_out = str((marks / "s.out").resolve())
    return {
        "S・T・U が走った": all_started,
        "W の出力": w_text,
        "W が出し直した（持ち主を出した塊の数）": len(report_blocks(w_text)),
        "W: S に疑いが出た塊": block,
        "holders の終了コード": h_code,
        "holders の出力": hp,
        "holders の前後で枠のディレクトリが同じ": before is not None and before == after,
        "W は持ち主が居るあいだ走らなかった": not w_ran_early,
        "pid": pid,
        "S の出力のパス": s_out,
        "終了コード": codes,
        "走り終えた後の holders": (done.returncode, done.stdout.strip()),
        "枠のディレクトリが無いときの holders": (f.returncode, f.stdout.strip(), fresh_dir.exists()),
        "holders に引数": (extra.returncode, extra.stderr),
        "docstring の STALL": int(stall_doc.group(1)) if stall_doc else None,
        "docstring の REPORT": int(report_doc.group(1)) if report_doc else None,
        "STALL": getattr(mod, "STALL", None),
        "REPORT": getattr(mod, "REPORT", None),
    }


MUTATIONS = {
    # 注釈 `# 守る N: <文言>` は、本体の docstring の「守る」の N 行目の書き出し（「- 」の後ろ）と同じ文言にする——
    # main がこの並び・番号・文言を本体と突き合わせる（#758。番号を手で追うと違う行に着いた）
    # 守る 1: 同じリポジトリでは、worktree をまたいで、枠の本数
    "枠を取らずに走らせる": (
        "                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)",
        "                pass"),
    # 守る 2: 待たされたら、待っていることと
    "待っていると言わない": (
        "            say(head + (\"\" if running else \" （読めなかった）\"))\n"
        "            for line in running:\n"
        "                say(f\"  {line}\")",
        "            pass"),
    # 守る 3: 走らせたコマンドの終了コードをそのまま返す
    "終了コードを捨てる": (
        "    return 128 - code if code < 0 else code",
        "    return 0"),
    # 守る 4: 入れ子で呼ばれたら
    "入れ子でも枠を取る": (
        "    if os.environ.get(ENV) == str(lockdir):",
        "    if False:"),
    # 守る 5: 枠を決められなければ、コマンドを走らせずに 125 を返す
    "決められなくても走らせる": (
        "        say(\"枠を決められない（git の共通ディレクトリが決まらない）——走らせていない\")\n        return CANNOT",
        "        return run(command, dict(os.environ), timeout)"),
    # 守る 6: 宣言が 1 以上の整数（6 桁まで）でない
    "読めない値で 1 と言いつつ 3 本にする": (
        "        return 1, f\"`並行の検査:` の値 {shown!r} は 1 以上の整数（6 桁まで）でない——1 として扱う\"",
        "        return 3, f\"`並行の検査:` の値 {shown!r} は 1 以上の整数（6 桁まで）でない——1 として扱う\""),
    # 守る 7: コードブロックと HTML コメントの中の行は宣言に数えない
    "コードブロックの中の行を数える": (
        "        opened = None if comment and not inline else opens(line)",
        "        opened = None"),
    # 守る 8: コードブロックは、空白 4 つ以上で字下げした行では閉じない
    "字下げした行でも閉じる": (
        "    if len(line) - len(body) > 3:",
        "    if False:"),
    # 守る 9: コードブロックは、開いた印と別の文字
    "別の文字の行でも閉じる": (
        "    run = len(body) - len(body.lstrip(char))",
        "    run = len(body) - len(body.lstrip(\"`~\"))"),
    # 守る 10: 宣言の行末の HTML コメントは外して読む
    "コメントの前のテキストを捨てる": (
        "                    kept, comment, rest = kept + rest[:start], True, rest[start + 4:]",
        "                    kept, comment, rest = \"\", True, rest[start + 4:]"),
    # 守る 11: ラッパー自身が SIGTERM・SIGHUP・SIGINT を受けても
    "ラッパーがシグナルで先に終わる": (
        "    previous = {s: signal.signal(s, forward) for s in (signal.SIGTERM, signal.SIGHUP)}\n"
        "    previous[signal.SIGINT] = signal.signal(signal.SIGINT, hold)",
        "    previous = {}"),
    # 守る 12: SIGINT はコマンドに渡さない
    "SIGINT もコマンドに渡す": (
        "    previous[signal.SIGINT] = signal.signal(signal.SIGINT, hold)",
        "    previous[signal.SIGINT] = signal.signal(signal.SIGINT, forward)"),
    # 守る 13: コードブロックは、空白 3 つまでで字下げした行で閉じる
    "空白 3 つの字下げの閉じ行で閉じない": (
        "    if len(line) - len(body) > 3:",
        "    if len(line) - len(body) > 2:"),
    # 守る 14: コードブロックは、開いた印とちょうど同じ数の行で閉じる
    "同じ数の閉じ行で閉じない": (
        "    return run >= width and not body[run:].strip(\" \\t\")",
        "    return run > width and not body[run:].strip(\" \\t\")"),
    # 守る 15: コードブロックは、後ろに空白とタブ以外の文字がある行
    "後ろに文字のある行でも閉じる": (
        "    return run >= width and not body[run:].strip(\" \\t\")",
        "    return run >= width"),
    # 守る 16: コードブロックは、タブで字下げした行では閉じない
    "タブの字下げの行でも閉じる": (
        "    body = line.lstrip(\" \")",
        "    body = line.lstrip(\" \\t\")"),
    # 守る 17: コードブロックは、後ろに空白とタブ以外の空白文字
    "後ろの全角の空白を許す": (
        "    return run >= width and not body[run:].strip(\" \\t\")",
        "    return run >= width and not body[run:].strip()"),
    # 守る 18: 行は改行でだけ分ける
    "改行以外の区切りでも行を分ける": (
        "    for line in NEWLINE.split(text.removeprefix(\"\\ufeff\")):",
        "    for line in text.removeprefix(\"\\ufeff\").splitlines():"),
    # 守る 19: `\x0c`（改ページ）の後ろも別の行と読まない
    "\\x0c でも行を分ける": (
        "NEWLINE = re.compile(r\"\\r\\n|\\r|\\n\")",
        "NEWLINE = re.compile(r\"\\r\\n|\\r|\\n|\\x0c\")"),
    # 守る 20: バッククォートの印の後ろにバッククォートがある行
    "バッククォートを含む情報文字列でも始める": (
        "    if mark[0] == \"`\" and \"`\" in line[opened.end():]:",
        "    if False:"),
    # 守る 21: 空白 4 つ以上で字下げした印の行はコードブロックを始めない
    "空白 4 つの字下げでも始める": (
        "FENCE = re.compile(r\" {0,3}(`{3,}|~{3,})\")",
        "FENCE = re.compile(r\" {0,4}(`{3,}|~{3,})\")"),
    # 守る 22: 行の途中の印はコードブロックを始めない
    "行の途中の印でも始める": (
        "    opened = FENCE.match(line)",
        "    opened = FENCE.search(line)"),
    # 守る 23: `~~~` の印でもコードブロックを始める
    "~~~ で始めない": (
        "FENCE = re.compile(r\" {0,3}(`{3,}|~{3,})\")",
        "FENCE = re.compile(r\" {0,3}(`{3,})\")"),
    # 守る 24: HTML コメントの中の印はコードブロックを始めない
    "コメントの中の印で始める": (
        "        opened = None if comment and not inline else opens(line)",
        "        opened = opens(line)"),
    # 守る 25: 開き行は元の行で見る
    "開き行をコメントを外した残りで見る": (
        "        if kept.strip():\n            lines.append(kept)",
        "        if not comment and opens(kept):\n            fence = opens(kept)\n            continue\n"
        "        if kept.strip():\n            lines.append(kept)"),
    # 守る 26: 情報文字列の `<!--` はコメントの始まりと読まない
    "情報文字列の <!-- をコメントと読む": (
        "        opened = None if comment and not inline else opens(line)",
        "        opened = None if comment and not inline or \"<!--\" in line else opens(line)"),
    # 守る 27: 段落の中で始まって閉じないコメントの後ろの行でも
    "段落の中のコメントの後ろの印で始めない": (
        "        opened = None if comment and not inline else opens(line)",
        "        opened = None if comment else opens(line)"),
    # 守る 28: 先頭の BOM を外して読む
    "BOM を外さない": (
        "    for line in NEWLINE.split(text.removeprefix(\"\\ufeff\")):",
        "    for line in NEWLINE.split(text):"),
    # 守る 29: 先頭の BOM は 1 つだけ外す
    "続く BOM も外す": (
        "    for line in NEWLINE.split(text.removeprefix(\"\\ufeff\")):",
        "    for line in NEWLINE.split(text.lstrip(\"\\ufeff\")):"),
    # 守る 30: `-->` で閉じた行頭のコメントの残りで開き直したコメントは
    "開き直したコメントの種類を行頭かだけで決める": (
        "                    inline = inline if started else not COMMENT_BLOCK.match(line)",
        "                    inline = not COMMENT_BLOCK.match(line)"),
    # 守る 31: リストや引用の印の直後で始まるコメント
    "リストや引用の印の後ろのコメントを段落の中と読む": (
        "COMMENT_BLOCK = re.compile(r\"(?: {0,3}(?:[-*+]|[0-9]{1,9}[.)])[ \\t]+| {0,3}>[ \\t]?)* {0,3}<!--\")",
        "COMMENT_BLOCK = re.compile(r\" {0,3}<!--\")"),
    # 守る 32: 期限（`--timeout`、無ければ既定）を過ぎたコマンドを止めて、枠を返す
    "期限を見ない": (
        "            code = proc.wait(timeout=timeout)",
        "            code = proc.wait()"),
    # 守る 33: 期限切れは 124 を返す
    "期限切れで止めたコマンドの終了コードを返す": (
        "            return TIMED_OUT",
        "            return 128 - proc.returncode if proc.returncode < 0 else proc.returncode"),
    # 守る 34: 期限切れは `run-serial: 期限切れ` で始まる行で言う
    "期限切れと言わない": (
        "            say(f\"期限切れ（{timeout} 秒を過ぎた）",
        "            say(f\"止めた（{timeout} 秒を過ぎた）"),
    # 守る 35: 期限切れで止めるとき、コマンドの子孫
    "子孫を止めない": (
        "    tree = descendants(proc.pid)\n    if tree is None:",
        "    tree = []\n    if tree is None:"),
    # 守る 36: 期限切れで SIGTERM を受けても終わらないものは
    "SIGKILL に上げない": (
        "        signal_all(left, signal.SIGKILL)",
        "        pass"),
    # 守る 37: 待っているあいだに呼び出し元（起動したときの親）が居なくなったら
    "呼び出し元を見ない": (
        "        if os.getppid() != parent:",
        "        if False:"),
    # 守る 38: `--timeout` の値が 1 以上の整数（7 桁まで）でない
    "期限の値を確かめない": (
        "        if not TIMEOUT_VALUE.fullmatch(value) or int(value) < 1:",
        "        if False:"),
    # 守る 39: `--timeout` を渡さなければ、既定
    "既定の期限を掛けない": (
        "    timeout = DEFAULT_TIMEOUT\n    while head:",
        "    timeout = None\n    while head:"),
    # 守る 40: 入れ子で呼ばれても
    "入れ子では期限を掛けない": (
        "        return run(command, env, timeout)\n\n    text",
        "        return run(command, env, None)\n\n    text"),
    # 守る 41: 期限切れの猶予のあいだに子孫が起こした子も
    "猶予の後に数え直さない": (
        "    targets += [pid for pid in (descendants(*living) if living else []) or [] if pid not in targets]",
        "    pass"),
    # 守る 42: 待たされているあいだ、`REPORT` 秒ごとに持ち主を出し直す
    "持ち主を出し直さない": (
        "        if waited is None or now - reported >= REPORT:",
        "        if waited is None:"),
    # 守る 43: 持ち主ごとに、枠を取ってからの経過時間を出す
    "経過を出さない": (
        "        parts.append(f\"経過 {span(now - begun)}（{started} から）\")",
        "        pass"),
    # 守る 44: 持ち主ごとに、出力の最終更新
    "出力のファイルを記録しない": (
        "\"outputs\": output_files()}",
        "\"outputs\": []}"),
    # 守る 45: 出力が `STALL` 秒以上増えていない持ち主に
    "止まっている疑いを出さない": (
        "    if updated is not None and now - updated >= STALL:",
        "    if False:"),
    # 守る 46: 出力が `STALL` 秒の内に増えた持ち主には
    "出力が進んでいても疑う": (
        "    if updated is not None and now - updated >= STALL:",
        "    if updated is not None and now - updated >= 0:"),
    # 守る 47: 出力の最終更新が分からない持ち主（出力がファイルでない）には
    "分からない持ち主も疑う": (
        "    if updated is not None and now - updated >= STALL:",
        "    if updated is None or now - updated >= STALL:"),
    # 守る 48: `holders` は持ち主を 1 回だけ出して 0 で終わる
    "holders が枠を取る": (
        "    running = holders(common / \"dev-loop-serial\")\n    print(",
        "    acquire(common / \"dev-loop-serial\", 1, os.getppid())\n    running = holders(common / \"dev-loop-serial\")\n    print("),
    # 守る 49: `holders` は枠のディレクトリが無ければ作らない
    "holders が枠のディレクトリを作る": (
        "    running = holders(common / \"dev-loop-serial\")\n    print(",
        "    (common / \"dev-loop-serial\").mkdir(exist_ok=True)\n    running = holders(common / \"dev-loop-serial\")\n    print("),
    # 守る 50: `holders` は枠のファイルに書かない
    "holders が枠のファイルに書く": (
        "            info = json.loads(path.read_text(encoding=\"utf-8\") or \"{}\")\n        except (OSError, ValueError):\n            continue\n        if not isinstance(info, dict) or not info:\n            continue\n        pid",
        "            path.touch()\n            info = json.loads(path.read_text(encoding=\"utf-8\") or \"{}\")\n        except (OSError, ValueError):\n            continue\n        if not isinstance(info, dict) or not info:\n            continue\n        pid"),
    # 守る 51: 枠のファイルに残った記録のうち、pid が居ないもの
    "居なくなった pid も出す": (
        "        if type(pid) is not int or pid <= 0 or not alive(pid):",
        "        if type(pid) is not int or pid <= 0:"),
}

OBSERVERS = {
    "serial": observe_serial, "parallel": observe_parallel, "codes": observe_codes, "nested": observe_nested,
    "cannot": observe_cannot, "decl": observe_decl, "sigterm": observe_sigterm, "parse": observe_parse,
    "sigint": observe_sigint, "timeout": observe_timeout, "timeout-kill": observe_timeout_kill, "orphan": observe_orphan,
    "deadline": observe_deadline, "timeout-late": observe_timeout_late, "holders": observe_holders,
}

# 変異ごとに当てる観測（全部を当てると、待ちの上限で止まる観測が重なって数分かかる）。
# **観測を絞っても、見つけたかは「その観測の判定（`judge`）が 1 つでも落ちたか」で決める**（#745）。どれを当てるかは変異の狙いで決める。
MUTATION_PROBE = {
    "枠を取らずに走らせる": ("serial",),
    "待っていると言わない": ("serial",),
    "終了コードを捨てる": ("codes",),
    "入れ子でも枠を取る": ("nested",),
    "決められなくても走らせる": ("cannot",),
    "読めない値で 1 と言いつつ 3 本にする": ("decl",),
    "コードブロックの中の行を数える": ("decl",),
    "ラッパーがシグナルで先に終わる": ("sigterm",),
    "字下げした行でも閉じる": ("parse", "decl"),
    "別の文字の行でも閉じる": ("parse", "decl"),
    "コメントの前のテキストを捨てる": ("parse", "parallel"),
    "SIGINT もコマンドに渡す": ("sigint",),
    "空白 3 つの字下げの閉じ行で閉じない": ("parse",),
    "同じ数の閉じ行で閉じない": ("parse",),
    "後ろに文字のある行でも閉じる": ("parse",),
    "タブの字下げの行でも閉じる": ("parse",),
    "後ろの全角の空白を許す": ("parse",),
    "改行以外の区切りでも行を分ける": ("parse",),
    "バッククォートを含む情報文字列でも始める": ("parse",),
    "空白 4 つの字下げでも始める": ("parse",),
    "行の途中の印でも始める": ("parse",),
    "~~~ で始めない": ("parse",),
    "コメントの中の印で始める": ("parse",),
    "開き行をコメントを外した残りで見る": ("parse",),
    "情報文字列の <!-- をコメントと読む": ("parse",),
    "BOM を外さない": ("parse",),
    "\\x0c でも行を分ける": ("parse",),
    "段落の中のコメントの後ろの印で始めない": ("parse",),
    "続く BOM も外す": ("parse",),
    "開き直したコメントの種類を行頭かだけで決める": ("parse",),
    "リストや引用の印の後ろのコメントを段落の中と読む": ("parse",),
    "期限を見ない": ("timeout",),
    "期限切れで止めたコマンドの終了コードを返す": ("timeout",),
    "期限切れと言わない": ("timeout",),
    "子孫を止めない": ("timeout",),
    "SIGKILL に上げない": ("timeout-kill",),
    "呼び出し元を見ない": ("orphan",),
    "期限の値を確かめない": ("codes",),
    "既定の期限を掛けない": ("deadline",),
    "入れ子では期限を掛けない": ("deadline",),
    "猶予の後に数え直さない": ("timeout-late",),
    "持ち主を出し直さない": ("holders",),
    "経過を出さない": ("holders",),
    "出力のファイルを記録しない": ("holders",),
    "止まっている疑いを出さない": ("holders",),
    "出力が進んでいても疑う": ("holders",),
    "分からない持ち主も疑う": ("holders",),
    "holders が枠を取る": ("holders",),
    "holders が枠のディレクトリを作る": ("holders",),
    "holders が枠のファイルに書く": ("holders",),
    "居なくなった pid も出す": ("holders",),
}


def observe_all(script: Path, tmp: Path, tag: str, only=None) -> dict:
    return {k: f(script, tmp, tag) for k, f in OBSERVERS.items() if only is None or k in only}


def judge(o: dict, sink: list[str] | None = None, quiet: bool = False) -> None:
    """観測に判定を当てる。`o` にある観測だけを見る（変異では絞った観測だけ）。落ちた判定は `sink`（無ければ全体の失敗）に足す。"""
    def ck(name: str, cond: bool) -> None:
        check(name, cond, sink, quiet)

    def head(text: str) -> None:
        if not quiet:
            print(text)

    if "serial" in o:
        s = o["serial"]
        head("枠 1（宣言なし）: メインの作業ツリーと worktree の 2 本")
        ck("A が走った", s["A が走った"])
        ck("B は A が終わるまで始めなかった（worktree をまたいで同じ枠）", s["B は A が終わるまで始めなかった"])
        ck("B が待っていると言った", s["B が待っていると言った"])
        ck("B が走っているもの（A の pid）を名指しした", s["B が A を名指しした"])
        ck("両方 0 で終わった", s["終了コード"] == [0, 0])
    if "parallel" in o:
        head("\n宣言 `並行の検査: 2`（worktree の写しの 5 は読まない）")
        for label, got in o["parallel"].items():
            ck(f"{label}: 2 本が同時に走った", got["2 本が同時に走った"])
            ck(f"{label}: 両方 0 で終わった", got["終了コード"] == [0, 0])
    if "codes" in o:
        c = o["codes"]
        head("\n終了コード")
        ck("7 を返すコマンドで 7", c["7"] == 7)
        ck("0 を返すコマンドで 0", c["0"] == 0)
        ck("SIGTERM で終わったら 143", c["SIGTERM"] == 143)
        ck("見つからないコマンドで 127", c["見つからない"] == 127)
        ck("見つからないと言う", c["見つからないと言う"])
        ck("コマンドが無ければ 2", c["コマンドなし"] == 2)
        ck("コマンド自身が 124 を返したら 124", c["自分で 124"] == 124)
        ck("コマンド自身の 124 では期限切れと言わない（期限切れと出力で見分けられる）", c["自分で 124 のとき期限切れと言わない"])
        for label, (code, ran, said) in c["使い方に合わない"].items():
            ck(f"{label}: 2 を返し、走らせず、理由を言う（{code}・走った {ran}）", code == 2 and not ran and said)
        ck("--timeout=30 なら走らせる", c["--timeout=30 で走った"])
    if "nested" in o:
        head("\n入れ子")
        ck("入れ子が固まらずに走った", o["nested"]["入れ子が固まらずに走った"])
    if "cannot" in o:
        head("\n枠を決められないとき")
        k = o["cannot"]
        ck("125 を返す", k["125"])
        ck("コマンドを走らせていない", k["走らせていない"])
        ck("走らせていないと言う", k["理由を言う"])
    if "decl" in o:
        head("\n読めない宣言・コードブロックと HTML コメントの中の宣言では、実効の枠が 1")
        for label, (serial, said, codes) in o["decl"].items():
            ck(f"{label}: B は A が終わるまで始めなかった", serial)
            ck(f"{label}: 両方 0 で終わった", codes == [0, 0])
            if DECLS[label][1]:
                ck(f"{label}: 1 として扱うと言う", said)
            else:
                ck(f"{label}: 何も言わない（宣言ではない）", not said)
    if "parse" in o:
        head("\n`slots_from` を直に当てる（#740・#741・#743・#745・#739・#758 の形）")
        for label, got in o["parse"].items():
            ck(f"{label}: {PARSE_SAMPLES[label][1]}", got == PARSE_SAMPLES[label][1])
    if "sigterm" in o:
        head("\nラッパー自身へのシグナル")
        for name, ok in o["sigterm"].items():
            ck(name, ok)
    if "sigint" in o:
        head("\nSIGINT はコマンドに 1 度だけ届く（#739）")
        for label, got in o["sigint"].items():
            ck(f"{label}: コマンドが受けたのは SIGINT 1 回と、終わらせる SIGTERM（{got['log']}）", got["log"] == ["INT", "TERM"])
            ck(f"{label}: 0 で終わった", got["終了コード"] == 0)
    for key, title in (("timeout", "期限（`--timeout 3`）を過ぎたコマンドの孫（`bash -c` の下）が走り続ける（#897）"),
                       ("timeout-kill", "同じ形で、孫が SIGTERM を無視する（#897）"),
                       ("timeout-late", "同じ形で、孫が SIGTERM を受けて子を起こし、走り続ける（#897 の 2 パス目）")):
        if key in o:
            t = o[key]
            head(f"\n{title}")
            ck("孫が走った", t["孫が走った"])
            ck(f"A は 124 で終わった（{t['A の終了コード']}）", t["A は 124"])
            ck("A が `run-serial: 期限切れ` の行で言った", t["A が期限切れと言った"])
            ck("孫が止まった（自分の上限まで走っていない）", t["孫が止まった"])
            ck("B が待っていると言った", t["B が待っていると言った"])
            ck("B が枠を取って走りきった", t["B が走りきった"])
            if key == "timeout-late":
                ck("猶予のあいだに孫が起こした子も止まった", t["猶予のあいだに生まれた子が止まった"])
            if key in ("timeout-kill", "timeout-late"):
                ck("SIGKILL で止めたと言った", t["SIGKILL と言った"])
            else:
                ck("SIGTERM で終わったので SIGKILL とは言わない", not t["SIGKILL と言った"])
    if "deadline" in o:
        d = o["deadline"]
        default = d["docstring の既定"]
        head(f"\n`main` が `run` に渡す期限（#897。docstring の既定 {default} 秒）")
        ck("docstring の「期限」の節に既定の秒数がある", default is not None)
        ck(f"DEFAULT_TIMEOUT が docstring の既定と同じ（{d['DEFAULT_TIMEOUT']}）", d["DEFAULT_TIMEOUT"] == default)
        for label, want in (("既定", default), ("--timeout 7", 7), ("入れ子・既定", default), ("入れ子・--timeout 5", 5)):
            code, got = d[label]
            ck(f"{label}: 期限 {want} で走らせた（{got}・{code}）", code == 0 and got == [want])
    if "orphan" in o:
        r = o["orphan"]
        head("\n呼び出し元が居なくなった待ち手（#897）")
        ck("W が待っていると言った", r["W が待っていると言った"])
        ck("W が枠を取らずに終わった（A の後に B が走らなかった）", r["W が枠を取らずに終わった"])
        ck("W が呼び出し元が居ないと言った", r["W が呼び出し元が居ないと言った"])
        ck("親が変わった main は 125", r["main は 125"])
        ck("親が変わった main はコマンドを走らせていない", r["main は走らせていない"])
        ck("親が変わった main は呼び出し元が居ないと言う", r["main は呼び出し元が居ないと言った"])
    if "holders" in o:
        h = o["holders"]
        pid = h["pid"]
        head(f"\n持ち主の表示（#898。STALL {HOLDER_STALL} 秒・REPORT {HOLDER_REPORT} 秒に差し替え）: 出力が止まった S・進む T・ファイルでない U")
        ck("docstring の「持ち主の表示」に STALL と REPORT の秒数がある", h["docstring の STALL"] is not None and h["docstring の REPORT"] is not None)
        ck(f"STALL が docstring と同じ（{h['STALL']}・{h['docstring の STALL']}）", h["STALL"] == h["docstring の STALL"])
        ck(f"REPORT が docstring と同じ（{h['REPORT']}・{h['docstring の REPORT']}）", h["REPORT"] == h["docstring の REPORT"])
        ck("S・T・U が走った", h["S・T・U が走った"])
        ck(f"W が持ち主を出し直した（塊 {h['W が出し直した（持ち主を出した塊の数）']} 個）", h["W が出し直した（持ち主を出した塊の数）"] >= 2)
        ck("W: 待っていると言った", "待っている" in h["W の出力"])
        for label, lines in (("W", h["W: S に疑いが出た塊"]), ("holders", h["holders の出力"])):
            s_line, t_line, u_line = (lines.get(pid[n], "") for n in "stu")
            ck(f"{label}: S・T・U を 1 行ずつ出した", all((s_line, t_line, u_line)))
            ck(f"{label}: 各行にコマンドと経過を出した",
               all("ticker.py" in x and re.search(r"・経過 [0-9]+ (?:秒|分)", x) for x in (s_line, t_line, u_line)))
            ck(f"{label}: S・T の行に出力の最終更新を出した（S は出力のファイルを名指し）",
               all(re.search(r"・出力の最終更新 [0-9]+ (?:秒|分).* 前（", x) for x in (s_line, t_line)) and h["S の出力のパス"] in s_line)
            ck(f"{label}: 出力が止まった S に止まっている疑い", "止まっている疑い" in s_line)
            ck(f"{label}: 出力が進む T には疑いを出さない", bool(t_line) and "止まっている疑い" not in t_line)
            ck(f"{label}: 出力がファイルでない U は分からないと言い、疑いを出さない",
               "出力の最終更新は分からない（出力がファイルでない" in u_line and "止まっている疑い" not in u_line)
        ck(f"holders: 待たずに 0 で終わった（{h['holders の終了コード']}）", h["holders の終了コード"] == 0)
        ck("holders: 前後で枠のディレクトリの中身（名前・中身・更新時刻）が同じ", h["holders の前後で枠のディレクトリが同じ"])
        ck("W は持ち主が居るあいだ走らず、全部 0 で終わった", h["W は持ち主が居るあいだ走らなかった"] and h["終了コード"] == [0, 0, 0, 0])
        code, out = h["走り終えた後の holders"]
        ck(f"走り終えた後の holders: 記録が残っていても居ない pid は出さない（{code}・{out!r}）", code == 0 and out == "走っているものは無い")
        code, out, made = h["枠のディレクトリが無いときの holders"]
        ck(f"枠のディレクトリが無いときの holders: 0 で終わり、作らない（{code}・{out!r}・作った {made}）",
           code == 0 and out == "走っているものは無い" and not made)
        code, err = h["holders に引数"]
        ck(f"holders に引数を足すと 2 を返し、理由を言う（{code}）", code == 2 and "holders" in err)


def annotations(test_source: str) -> list[tuple[str, int, str]]:
    """MUTATIONS の注釈を (変異の名前, 守るの番号, 文言) で並べる。注釈の直後の `    "<名前>": (` の行を、その注釈の変異とする。"""
    block = test_source.split("\nMUTATIONS = {\n", 1)[1].split("\n}\n", 1)[0]
    found, pending = [], None
    for line in block.splitlines():
        m = re.match(r"    # 守る (\d+): (.+)$", line)
        if m:
            pending = (int(m.group(1)), m.group(2))
            continue
        m = re.match(r'    "(.+)": \($', line)
        if m and pending:
            found.append((ast.literal_eval(f'"{m.group(1)}"'), *pending))
            pending = None
    return found


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t).resolve()
        assert_not_real_repo(tmp)
        correct = observe_all(SCRIPT, tmp, "ok")
        judge(correct)

        print("\n変異テスト（壊したのに判定が 1 つも落ちなければ失格）")
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
            fell: list[str] = []
            try:
                judge(observe_all(mutated, tmp, f"m{i}", only), fell, quiet=True)
            except Exception as exc:  # 例外は判定の失敗ではない——見つけたと数えず、当てられなかったとして落とす（#745）
                check(f"変異を当てられた: {name}（観測が例外で止まった: {exc.__class__.__name__}）", False)
                continue
            check(f"変異を殺せる: {name}" + (f"（落ちた判定 {len(fell)} 件。最初: {fell[0]}）" if fell else ""), bool(fell))

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件",
              len(promises) == len(MUTATIONS))

        print("\n変異の注釈（# 守る N: <文言>）が、本体の「守る」の N 行目と並び・番号・文言で合うか（#758）")
        notes = annotations(Path(__file__).read_text(encoding="utf-8"))
        check("注釈が変異ごとに 1 つ・変異と同じ順", [name for name, _, _ in notes] == list(MUTATIONS))
        check("番号が 1 から順に並ぶ", [n for _, n, _ in notes] == list(range(1, len(notes) + 1)))
        for name, n, words in notes:
            check(f"守る {n}（{name}）の文言が本体の {n} 行目の書き出し",
                  0 < n <= len(promises) and promises[n - 1][2:].startswith(words))

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
