#!/usr/bin/env python3
r"""`check-mutation-claims.py` の回帰テスト。

    python3 scripts/test-check-mutation-claims.py

**このテストは実環境を触らない。** 毎回テンポラリに偽のツリーを作り、そこだけを対象にする
（`assert_not_real_repo` がそれを担保する）。本体は既定でこのリポジトリ自身を走査し、
**さらに複製を作って子プロセスを起こす**ので、**歯止めが無いと、テストが実リポジトリを
まるごと複製して回してしまう。**

**例外が 1 つある**——**実リポジトリにマーカーが 1 件以上あること**だけは実リポジトリを読む。
**「マーカーが 1 件も無い状態は緑になる」を本体が守らない**と宣言しているので、
**そこを塞ぐのはこちら側の仕事**である。**読むだけで書かない。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに観測が変わらなければ失格**とする。
**「守る」の行数と変異の数が 1 対 1 か**は、**テスト自身が数える。**

## 偽のツリーの作り

**本体が起こす `red` コマンドまで偽物にする。** 実在のテストを呼ぶと、
**このテストが落ちた理由が「本体の欠陥」なのか「呼ばれた側の都合」なのか分からなくなる。**

**何をどこに作るかは `run_all()` と `build*()` を正とする**——**ここに一覧を置かない。**
**一度ここに一覧を置き、2 パス続けて「不足している」と反証された**
（1 度目は 4 件、直した次のパスでさらに 3 件と、変異ループが毎回作る木が抜けていた）
——**木は編集のたびに増えるので、写した一覧は必ず古くなる。**

**ただし 1 つだけ、木ではないので `build*()` から読めないものがある**——
`<TMPDIR>/cmc-escape-<pid>.txt` は**退避先の外**に置く的で、
**`../` で指しても触られてはならない**ことを確かめるためにある（`escape_target()`）。

dup-counts-ok: 変異
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "check-mutation-claims.py"

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


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"cmc_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def marker(**spec) -> str:
    return "mutation-claim: " + json.dumps(spec, ensure_ascii=False)


RED = "python3 scripts/subject_test.py"

# **`# SENTINEL` を指すマーカーを、subject.py 自身の中に置く。**
# **これが無いと「マーカー自身の行を数えない」変異が殺せない**
# ——**マーカーと対象が別ファイルだと、数えても数えなくても結果が同じ。**
SUBJECT = (
    "# KEEP\n"
    "# HARMLESS\n"
    "# TRAILING\n"
    "# BLIND\n"
    "# FLAKY\n"
    "# WARM\n"
    "# PHASE\n"
    "# ROT\n"
    "# TWICE\n"
    "# TWICE\n"
    "# SENTINEL\n"
    "# " + marker(file="scripts/subject.py", old="# SENTINEL", new="# GONE", red=RED) + "\n"
)

# **行そのものが残っているかで見る。** 部分一致だと、マーカー行に含まれる
# `# SENTINEL` を拾ってしまい、変異を当てても緑のままになる。
SUBJECT_TEST = (
    "import pathlib, sys\n"
    'text = pathlib.Path("scripts/subject.py").read_text()\n'
    # **中身に依存する値を出す。** **これが無いと「出力が変わらない」の試料が作れない**
    # ——出力が常に空だと、**本物の「緑のまま」と見分けがつかない。**
    'print("subject bytes:", len(text))\n'
    'lines = text.splitlines()\n'
    'sys.exit(0 if ("# KEEP" in lines and "# SENTINEL" in lines) else 1)\n'
)

# **中身を一切見ないコマンド。** 変異を当てても出力が 1 バイトも変わらないので、
# **「主張が偽」と断定してはならない**形の試料になる（守る 13）。
BLIND_TEST = 'print("blind ok")\n'

# **中身を見ないまま 0 で終わり、しかも出力が実行ごとに変わるコマンド**（守る 16 / #156）。
# **守る 13 が効かない形**——**変異と無関係に出力が変わる**ので「出力が変わらない」の
# 判別を素通りし、**「主張が偽」と断定されてしまう。**
# **時刻や乱数ではなく、数える**——**試料が確率で揺れると、
# 落ちたのが本体のせいか試料のせいか分からなくなる。**
# **数が増えるのは 1 つの退避先の中だけである**（カウンタは退避先の中に置くので、
# `main()` を呼ぶたびに 1 から振り出しになる）。**要るのはそれで足りる**
# ——**同じ退避先の中で 2 回の実行が違う出力を返せばよい。**
# **「テスト全体で単調増加する」とは書かない**（1 パス目の `/code-review` が、
# **範囲を書いていないので誤読されると指摘した**）。
FLAKY_TEST = (
    "import pathlib\n"
    'p = pathlib.Path("flaky-count.txt")\n'
    'n = (int(p.read_text()) + 1) if p.exists() else 1\n'
    'p.write_text(str(n))\n'
    'print("走った回数:", n)\n'
)

# **2 段階の準備をする `red`**（守る 16 / #156）。**1 度目と 2 度目で別の出力を出し、
# 3 度目から落ち着く。** **判定は一切しない**ので、変異は見逃されている（＝主張が偽ではなく、
# **観測できない**）。**離れた回どうしを比べると、準備の段差を「変異のせい」と読んで
# `緑のまま` になる**——**2 パス目の `/code-review` が、それを退行として実測した。**
TWO_PHASE_TEST = (
    "import pathlib\n"
    'p = pathlib.Path("phase-count.txt")\n'
    'n = (int(p.read_text()) + 1) if p.exists() else 1\n'
    'p.write_text(str(n))\n'
    'print("phase1" if n == 1 else ("phase2" if n == 2 else "steady"))\n'
)

# **途中から非ゼロになる `red`**（守る 16 / #156）。**3 度目以降で落ちるようになる。**
# **当て直した対照が緑であることを要求しないと、揃っているだけで「主張が偽」と読む。**
# **出力も 2 段階にする**——**そうしないと `out == base_out` の早期の分岐で止まり、
# 当て直しの経路まで届かない**（**そう書いた試料を 1 度置いて、自分で反証した**）。
ROTTED_TEST = (
    "import pathlib, sys\n"
    'p = pathlib.Path("rot-count.txt")\n'
    'n = (int(p.read_text()) + 1) if p.exists() else 1\n'
    'p.write_text(str(n))\n'
    'print("phase1" if n == 1 else ("phase2" if n == 2 else "steady"))\n'
    "sys.exit(1 if n >= 3 else 0)\n"
)

ALWAYS_RED = "import sys\nsys.exit(1)\n"


def escape_test_body() -> str:
    """**退避先の外の的を読んで出力する。**

    **これが無いと、守る 8 の変異が「理由の文字列」でしか死なない**
    ——`judge()` は `finally` で必ず復元するので、**テストから的の中身を見ても
    いつも元に戻っている**（2 パス目の `/code-review` が実測で指摘した）。
    **的を `red` の中から読めば、書き換えが*飛行中に*出力として現れる。**
    """
    return ("import pathlib\n"
            f'print(pathlib.Path("../{escape_target().name}").read_text())\n')

# **閉じ忘れたフェンスの後ろにマーカーがある形。**
# **黙って 0 件にせず「読めない」と言わせる。**
# **フェンス記号を組み立てる。** リテラルで書くと、**この*ソース*が
# 閉じ忘れたフェンスを持つファイルになり、自分の中のマーカーが読めなくなる**
# ——置いた瞬間に自分で踏んだ。
_FENCE = "`" * 3
FENCED_BROKEN = (
    "# 閉じ忘れ\n\n"
    + _FENCE + "bash\n"
    + 'echo "このフェンスは閉じていない"\n\n'
    + marker(file="scripts/subject.py", old="# KEEP", new="# GONE", red=RED) + "\n"
)


def escape_target() -> Path:
    """**退避先の外**に置く的。`make_sandbox` は `mkdtemp()` を使うので親は TMPDIR。"""
    return Path(tempfile.gettempdir()).resolve() / f"cmc-escape-{os.getpid()}.txt"


ESCAPE_BODY = "# KEEP\n"


def build(root: Path) -> tuple[dict[str, int], int]:
    """判定が全部出そろう偽のツリーを作る。(名前→行番号, マーカー総数) を返す。"""
    assert_not_real_repo(root)
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "subject.py").write_text(SUBJECT, encoding="utf-8")
    (root / "scripts" / "subject_test.py").write_text(SUBJECT_TEST, encoding="utf-8")
    (root / "scripts" / "always_red.py").write_text(ALWAYS_RED, encoding="utf-8")
    (root / "scripts" / "blind_test.py").write_text(BLIND_TEST, encoding="utf-8")
    (root / "scripts" / "flaky_test.py").write_text(FLAKY_TEST, encoding="utf-8")
    (root / "scripts" / "warm_test.py").write_text(WARM_TEST, encoding="utf-8")
    (root / "scripts" / "two_phase_test.py").write_text(TWO_PHASE_TEST, encoding="utf-8")
    (root / "scripts" / "rotted_test.py").write_text(ROTTED_TEST, encoding="utf-8")
    (root / "scripts" / "escape_test.py").write_text(
        escape_test_body(), encoding="utf-8")
    (root / "fenced-broken.md").write_text(FENCED_BROKEN, encoding="utf-8")
    # **複製に持ち込まれてはならないもの。** 実物の worktree では `.git` は
    # **本体を指すファイル**だが、除外の対象という点は同じ。
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/fake\n", encoding="utf-8")

    subject = "scripts/subject.py"
    entries: list[tuple[str, str]] = [
        ("good", marker(file=subject, old="# KEEP", new="# GONE", red=RED)),
        ("noop", marker(file=subject, old="# HARMLESS", new="# HARMLESS2", red=RED)),
        ("twice", marker(file=subject, old="# TWICE", new="# X", red=RED)),
        ("missing", marker(file=subject, old="NOWHERE", new="X", red=RED)),
        ("badbase", marker(file=subject, old="# KEEP", new="# GONE",
                           red="python3 scripts/always_red.py")),
        ("escape", marker(file=f"../{escape_target().name}", old="# KEEP",
                          new="# GONE", red="python3 scripts/escape_test.py")),
        # **出力が 1 バイトも変わらない形**（守る 13）。**緑だが「主張が偽」とは言えない。**
        ("blind", marker(file=subject, old="# BLIND", new="# BLIND2",
                         red="python3 scripts/blind_test.py")),
        # **0 で終わる SKIP で、しかも出力が実行ごとに変わる形**（守る 16 / #156）。
        # **守る 13 が効かない**——**変異と無関係に出力が変わる**ので、
        # **これが無いと「主張が偽」と断定される。**
        ("flaky", marker(file=subject, old="# FLAKY", new="# FLAKY2",
                         red="python3 scripts/flaky_test.py")),
        # **初回だけ副作用がある `red` で、本物の「主張が偽」**（守る 16 / #156）。
        # **比較相手をキャッシュした 1 度目にすると、ここが倒しすぎで落ちる。**
        ("warm", marker(file=subject, old="# WARM", new="# WARM2",
                        red="python3 scripts/warm_test.py")),
        # **2 段階の準備をする `red`**（守る 16 / #156）。**離れた回どうしを比べると
        # `緑のまま` になる**——**前の版で入れた退行を、ここで押さえる。**
        ("twophase", marker(file=subject, old="# PHASE", new="# PHASE2",
                            red="python3 scripts/two_phase_test.py")),
        # **途中から非ゼロになる `red`**（守る 16 / #156）。
        # **当て直した対照が緑であることを要求しないと「主張が偽」と読む。**
        ("rotted", marker(file=subject, old="# ROT", new="# ROT2",
                          red="python3 scripts/rotted_test.py")),
        # **必須のキーは全部あって、余計なキーが 1 つだけある形。**
        # **これが無いと「未知のキーを拒否する」変異が殺せない**
        # ——足りないキーの側で先に落ちてしまい、区別がつかない。
        # mutation-claim: {"file": "scripts/test-check-mutation-claims.py", "old": ", \"why\": \"余計なキー\"", "new": "", "red": "python3 scripts/test-check-mutation-claims.py"}
        ("unknown", 'mutation-claim: {"file": "scripts/subject.py", "old": "# KEEP", '
                    f'"new": "# GONE", "red": "{RED}", "why": "余計なキー"}}'),
        # **行末に注記が続く形。** **これが無いと「行のどこに置いても拾う」変異が殺せない。**
        ("trailing", marker(file=subject, old="# TRAILING", new="# TRAILING2", red=RED)
                     + "  （行末に注記がある形）"),
    ]

    lines = ["# 主張の一覧", ""]
    where: dict[str, int] = {}
    for name, text in entries:
        lines.append(text)
        where[name] = len(lines)  # 1 始まり
        lines.append("")
    lines += ["書式の例はフェンスに入れる:", "", "```text",
              marker(file=subject, old="# KEEP", new="# GONE", red=RED), "```", ""]
    (root / "claims.md").write_text("\n".join(lines), encoding="utf-8")
    # claims.md の 8 件 ＋ subject.py の中の 1 件（fenced-broken.md はファイル単位で broken）
    return where, len(entries) + 1 + 1


# **決定的に判定するが、初回だけ余計な行を出すコマンド**（守る 16 / #156）。
# **比較相手をキャッシュした 1 度目にすると、1 度目だけが永久に他と違う**ので、
# **本物の「主張が偽」まで `当てられなかった` に落ちる**——**I2 が禁じている倒しすぎ。**
# **`# WARM` の有無は見ない**ので、そこへの変異は正しく見逃される（＝主張が偽）。
WARM_TEST = (
    "import pathlib, sys\n"
    'c = pathlib.Path("warm-cache.txt")\n'
    "if not c.exists():\n"
    '    c.write_text("x")\n'
    '    print("キャッシュを作りました")\n'
    'text = pathlib.Path("scripts/subject.py").read_text()\n'
    'print("subject bytes:", len(text))\n'
    'sys.exit(0 if "# KEEP" in text.splitlines() else 1)\n'
)

# **3 度目だけ止まるコマンド**（守る 16 / #156）。**1・2 度目は素直に 0 で終わり、
# 陽性対照の当て直し（＝通算 3 度目）だけが打ち切られる。**
# **`TIMEOUT` を一律に縮めても、この形は作れない**——**1 度目が先に打ち切られ、
# `base_rc != 0` の側で止まってしまう**（実測で確かめた）。
HANG_TEST = (
    "import pathlib, time\n"
    'p = pathlib.Path("hang-count.txt")\n'
    'n = (int(p.read_text()) + 1) if p.exists() else 1\n'
    'p.write_text(str(n))\n'
    "if n >= 3:\n"
    "    time.sleep(3600)\n"
    'print("走った回数:", n)\n'
)

# **打ち切りを待つ秒数。** **短いほどテストが速いが、遅い機械で 1・2 度目まで
# 打ち切られると、この試料は別の分岐に落ちて主張を実演しなくなる。**
HANG_TIMEOUT = 10


def build_hang(root: Path) -> int:
    """**陽性対照の 2 度目だけが走らない**木を作る。マーカーの行番号を返す。

    **これが無いと「走らなかったことを『非決定的』と言わない」変異が殺せない**
    ——**判定はどちらも `当てられなかった` なので、理由を見ないと区別がつかない。**

    **主張はちょうど 1 件にする**——**`SUBJECT` は自分の中にマーカーを 1 つ持ち、
    その `red` はこの木が書かない `subject_test.py` を指す**ので、**そのまま使うと
    迷子の主張が 1 件混じる**（**すぐ下の `build_early_exit()` が同じ危険を書いているのに、
    同じ差分で踏んだ**。2 パス目の `/code-review` が指摘した）。
    """
    assert_not_real_repo(root)
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "subject.py").write_text("# FLAKY\n", encoding="utf-8")
    (root / "scripts" / "hang_test.py").write_text(HANG_TEST, encoding="utf-8")
    text = marker(file="scripts/subject.py", old="# FLAKY", new="# FLAKY2",
                  red="python3 scripts/hang_test.py")
    (root / "claims.md").write_text("# 主張\n\n" + text + "\n", encoding="utf-8")
    return 3  # 1 始まり（見出し・空行・マーカー）


def build_early_exit(root: Path) -> None:
    """**早期の分岐（出力が変わらない）で倒れる主張だけ**を持つ木。

    **これが無いと「追加の実行は倒れる直前だけ」（I5）を何も押さえられない**
    ——**当て直しのブロックを上に持ち上げても、判定は 1 つも変わらない。**

    **`確認` で終わる木では判別できない**——**そちらは持ち上げた位置より *前* で返る**ので、
    **持ち上げても回数が動かない**（**そう書いた検査を 1 度置いて、自分で反証した**）。

    **主張はちょうど 1 件にする**——**`SUBJECT` は自分の中にマーカーを 1 つ持つ**ので、
    **そのまま使うと 2 件になり、数えた回数が何の回数か言えなくなる。**
    """
    assert_not_real_repo(root)
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "subject.py").write_text("# BLIND\n", encoding="utf-8")
    (root / "scripts" / "blind_test.py").write_text(BLIND_TEST, encoding="utf-8")
    (root / "claims.md").write_text(
        marker(file="scripts/subject.py", old="# BLIND", new="# BLIND2",
               red="python3 scripts/blind_test.py") + "\n",
        encoding="utf-8")


def build_only_not_applied(root: Path) -> None:
    """**「当てられなかった」だけ**が出るツリー。

    **これが無いと「当てられなかったを緑と区別する」変異が殺せない**
    ——「緑のまま」が同居していると、そちらだけで非ゼロになってしまう。
    """
    assert_not_real_repo(root)
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "subject.py").write_text(SUBJECT, encoding="utf-8")
    (root / "scripts" / "subject_test.py").write_text(SUBJECT_TEST, encoding="utf-8")
    (root / "claims.md").write_text(
        marker(file="scripts/subject.py", old="NOWHERE", new="X", red=RED) + "\n",
        encoding="utf-8")


def observe(mod, root: Path) -> tuple[int, str]:
    """本体の判定をまとめて観測する。**判定と理由の両方を見る。**"""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = mod.main([str(root)])
    except Exception as exc:  # noqa: BLE001 — 変異で落ちるのは「殺せた」と数える
        return -1, f"{type(exc).__name__}"
    return rc, buf.getvalue()


def observe_leak(mod, leak_root: Path, parent: Path) -> dict:
    """**退避先の消し残し**を観測する（守る 14 / #157）。

    **これは出力に出ない副作用なので、`observe` では殺せない**
    ——**観測の側を足さないと、変異ループが「畳まない」変異を素通りさせる。**

    **安全弁は 2 つあり、どちらの倒れ方でも残しうる**ので両方当てる。
    **正常系も併せて見る**——**`try` を広げすぎて*返すべき退避先まで畳む*変異**は、
    落ちる側だけ見ていても殺せない。

    **中断（`BaseException`）も当てる**——**これが無いと `except Exception:` へ狭めても
    どの観測も変わらない**（上の 3 つはどれも `RuntimeError` ＝ `Exception` で落ちる）。
    **一度これを落としたまま「P5 は `BaseException` で受けて守っている」と経路表に書き、
    2 パス目の `/code-review` に「散文だけで、実行されない主張だ」と反証された。**

    **`.resolve()` が落ちる形も当てる**——**これが無いと `try` の開始位置を
    `mkdtemp` の前に戻しても、どの観測も動かない**（上の 4 つはどれも
    `.resolve()` の *後* で落ちる）。**3 パス目の `/code-review` が
    「P5 とまったく同じ『散文だけ』の状態が P10 に残っている」と実測で反証した**
    ——**revert しても完全に緑のまま、実際には 1 件漏れていた。**

    **返すのは辞書である**（タプルではない）。**要素数を数えた言葉を書かないため**
    ——**「定数の 5-tuple にする」と書いた 2 行の下で実際は 7 要素になり、
    3 パス目の `/code-review` に反証された。** **キーで対応が読めれば、数は要らない。**

    **退避先の親を 2 つとも試料の中に閉じ込める**ので、
    **実 `$TMPDIR` は汚さない**（それは別の検査が端から端まで見る）。
    """
    assert_not_real_repo(leak_root)
    (leak_root / ".git").mkdir(exist_ok=True)
    (leak_root / "scripts").mkdir(parents=True, exist_ok=True)
    (leak_root / "scripts" / "subject.py").write_text("# leak\n", encoding="utf-8")
    parent.mkdir(exist_ok=True)

    def left(where: Path) -> int:
        return len(list(where.glob("mutation-claims-*")))

    def fell(call) -> str:
        try:
            call()
        except BaseException as exc:  # noqa: BLE001 — 落ち方の *名前* だけを観測する
            return type(exc).__name__
        return "落ちなかった"

    keep_tempdir = tempfile.tempdir
    try:
        # **P1: 退避先が原本の内側**——`copytree` の *前* に落ちる。
        tempfile.tempdir = str(leak_root)
        inside = fell(lambda: mod.make_sandbox(leak_root))
        inside_left = left(leak_root)

        # **P2: `.git` が残っている**——`copytree` の *後* に落ちる。**#157 を起こした当の道。**
        tempfile.tempdir = str(parent)
        keep_ignore = mod._ignore
        mod._ignore = lambda _dir, _names: []
        try:
            dotgit = fell(lambda: mod.make_sandbox(leak_root))
        finally:
            mod._ignore = keep_ignore
        dotgit_left = left(parent)

        # **P5: 中断**——`copytree` の最中に `KeyboardInterrupt` が届いた形。
        # **`Exception` では捕まらない**ので、**`except Exception:` に狭めるとここだけ残る。**
        keep_copytree = mod.shutil.copytree

        def interrupted(*_a, **_k):
            raise KeyboardInterrupt("probe: 中断")

        mod.shutil.copytree = interrupted
        try:
            stopped = fell(lambda: mod.make_sandbox(leak_root))
        finally:
            mod.shutil.copytree = keep_copytree
        stopped_left = left(parent)

        # **P10: `.resolve()` が落ちる**——**`mkdtemp()` は既に作っているのに、
        # 解決に失敗すると後始末を通らずに抜けうる形だった。**
        # **最初の 1 回だけ落とす**——`make_sandbox` は `root` の側でも呼ぶので、
        # 全部落とすと「どこで落ちたか」が判別できない。
        calls = {"n": 0}
        keep_resolve = pathlib.Path.resolve

        def flaky(self, *a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("probe: resolve が落ちた")
            return keep_resolve(self, *a, **k)

        pathlib.Path.resolve = flaky
        try:
            unresolved = fell(lambda: mod.make_sandbox(leak_root))
        finally:
            pathlib.Path.resolve = keep_resolve
        unresolved_left = left(parent)

        # **正常系は畳まない**——退避先が返り、中身が入っている。
        normal: tuple = ()
        try:
            box = mod.make_sandbox(leak_root)
            normal = (box.is_dir(), (box / "scripts" / "subject.py").is_file())
            shutil.rmtree(box, ignore_errors=True)
        except BaseException as exc:  # noqa: BLE001
            normal = (type(exc).__name__,)
    finally:
        tempfile.tempdir = keep_tempdir
        for stray in list(leak_root.glob("mutation-claims-*")) + list(parent.glob("mutation-claims-*")):
            shutil.rmtree(stray, ignore_errors=True)
    return {"inside": inside, "inside_left": inside_left,
            "dotgit": dotgit, "dotgit_left": dotgit_left,
            "stopped": stopped, "stopped_left": stopped_left,
            "unresolved": unresolved, "unresolved_left": unresolved_left,
            "normal": normal}


def snapshot(mod, root: Path, only_na: Path, missing: Path,
             leak_root: Path, leak_parent: Path) -> tuple:
    """4 つの観測を、まとめて 1 つにする。

    **どれが欠けても殺せない変異がある。**
    """
    return (
        observe(mod, root),
        # **これが無いと「当てられなかったを緑と数える」変異が殺せない。**
        # **`new` は構造を壊さない形にする。** 消してしまうとタプルのアリティが変わり、
        # **変異ループに入る前に `ValueError` で落ちる**——**赤くはなるが、
        # 主張（この木が無いと守る 5 が殺せない）を 1 度も実演しない空の「確認」**になる
        # （2 パス目の `/code-review` が実測で指摘した）。
        # mutation-claim: {"file": "scripts/test-check-mutation-claims.py", "old": "        observe(mod, only_na),", "new": "        observe(mod, root),", "red": "python3 scripts/test-check-mutation-claims.py"}
        observe(mod, only_na),
        # **これが無いと「対象の木が無くても通す」変異が殺せない。**
        observe(mod, missing),
        # **これが無いと「退避先を畳まない」変異が殺せない**（#157）。
        # **後始末は出力を 1 バイトも変えない**ので、上の 3 つはどれも同じ観測を返す。
        # **`new` は *観測の形* まで保つ**——**`observe(mod, root)` への差し替えでは
        # 足りない。** あれが返すのは別の形なので、**下の `leak[…]` を読むところで落ち、
        # 変異ループに入る前に終わる**——**赤くはなるが、主張（この観測が無いと
        # 守る 14 が殺せない）を 1 度も実演しない空の「確認」**になる。
        # **一度これを `observe(mod, root)` で書き、`/code-review` が実測で反証した**
        # ——**すぐ上の `only_na` の項がまさにその形を警告しているのに、同じ差分の中で踏んだ。**
        # **だから、キーをそのまま持つ定数の辞書にする**——**形を変えずに、観測だけ殺す。**
        # mutation-claim: {"file": "scripts/test-check-mutation-claims.py", "old": "        observe_leak(mod, leak_root, leak_parent),", "new": "        {\"inside\": \"RuntimeError\", \"inside_left\": 0, \"dotgit\": \"RuntimeError\", \"dotgit_left\": 0, \"stopped\": \"KeyboardInterrupt\", \"stopped_left\": 0, \"unresolved\": \"OSError\", \"unresolved_left\": 0, \"normal\": (True, True)},", "red": "python3 scripts/test-check-mutation-claims.py"}
        observe_leak(mod, leak_root, leak_parent),
    )


def verdicts(out: str) -> dict[str, str]:
    """出力を「当てた先 → 判定」にほぐす。並び順には依存しない。"""
    got: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] in ("確認", "緑のまま", "当てられなかった"):
            got[parts[1].rstrip(":")] = parts[0]
    return got


MUTATIONS = {
    # 守る 1: 散文の主張を機械で当てる
    "主張を集めない": (
        "            claims.append(Claim(str(rel), lineno, spec))",
        "            pass"),
    # 守る 2: 退避先に `.git` を持ち込まない
    "`.git` を複製に持ち込む": (
        "    return [n for n in names if n in SKIP_DIRS]",
        "    return []"),
    # 守る 3: 陽性対照を必須にする
    "陽性対照を見ない": (
        "    if base_rc != 0:",
        "    if False:"),
    # 守る 4: 変異はちょうど 1 箇所に当てる
    "当てる先が 1 箇所かを見ない": (
        "    if len(at) != 1:",
        "    if len(at) == 0:"),
    # 守る 5: 「当てられなかった」を緑と区別する
    "当てられなかったを緑と数える": (
        "    if counts[STILL_GREEN] or counts[NOT_APPLIED]:",
        "    if counts[STILL_GREEN]:"),
    # 守る 6: フェンスの中のマーカーは拾わない
    "フェンスを剥がさない": (
        "        for lineno, line in enumerate(strip_fences(text).split(\"\\n\"), 1):",
        "        for lineno, line in enumerate(text.split(\"\\n\"), 1):"),
    # 守る 7: 未知のキーを拒否する
    "未知のキーを通す": (
        "            if missing or unknown:",
        "            if missing:"),
    # 守る 8: 書き込む先が退避先の内側であることを確かめる
    "退避先の外を指していても当てる": (
        "    if target != box and not str(target).startswith(str(box) + \"/\"):",
        "    if False:"),
    # 守る 9: 行のどこに置いたマーカーも拾う
    "行末でなければ拾わない": (
        "MARKER = re.compile(r\"mutation-claim:\\s*(\\{.*\\})\")",
        "MARKER = re.compile(r\"mutation-claim:\\s*(\\{.*\\})\\s*$\")"),
    # 守る 10: 閉じ忘れたフェンスを「読めない」と報告する
    "閉じ忘れたフェンスを黙って飲む": (
        "            if fence is not None:",
        "            if False:"),
    # 守る 11: マーカー自身の行は数えない
    "マーカー自身の行も数える": (
        "        if not any(start <= i < end for start, end in spans):",
        "        if True:"),
    # 守る 12: 対象の木が無ければ落とす
    "対象の木が無くても通す": (
        "    if not root.is_dir():",
        "    if False:"),
    # 守る 13: 出力が変わらない緑を「主張が偽」と断定しない
    "出力が変わらなくても主張が偽と断定する": (
        "    if out == base_out:",
        "    if False:"),
    # 守る 14: 退避先は、作った関数が自分で畳む（#157）
    "落ちたときに退避先を畳まない": (
        "    except BaseException:\n"
        "        shutil.rmtree(created, ignore_errors=True)\n"
        "        raise",
        "    except BaseException:\n"
        "        raise"),
    # 守る 15: 中断されたときも畳む（#157）
    "中断を捕まえない（`Exception` に狭める）": (
        "    except BaseException:\n        shutil.rmtree(created",
        "    except Exception:\n        shutil.rmtree(created"),
    # 守る 16: 走るたびに結果が揺れる `red` では「主張が偽」と断定しない（#156）
    "当て直した 2 回の揺れを見ない": (
        "    if first != second:",
        "    if False:"),
}


def main() -> int:
    escape = escape_target()
    escape.write_text(ESCAPE_BODY, encoding="utf-8")
    try:
        return run_all(escape)
    finally:
        escape.unlink(missing_ok=True)


def run_all(escape: Path) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "tree"
        root.mkdir()
        where, total_markers = build(root)
        only_na = Path(tmp) / "only-not-applied"
        only_na.mkdir()
        build_only_not_applied(only_na)
        missing = Path(tmp) / "does-not-exist"
        leak_root = Path(tmp) / "leak-tree"
        leak_root.mkdir()
        leak_parent = Path(tmp) / "leak-parent"
        hang = Path(tmp) / "hang"
        hang.mkdir()
        hang_line = build_hang(hang)
        early = Path(tmp) / "early-exit"
        early.mkdir()
        build_early_exit(early)

        mod = load()
        base = snapshot(mod, root, only_na, missing, leak_root, leak_parent)
        (rc, out), (rc_na, out_na), (rc_missing, _), leak = base
        got = verdicts(out)

        print("3 つの判定が出そろうか")
        check("主張どおりなら『確認』", got.get(f"claims.md:{where['good']}") == "確認")
        check("変異を当てても緑なら『緑のまま』",
              got.get(f"claims.md:{where['noop']}") == "緑のまま")
        check("`old` が 2 箇所なら『当てられなかった』",
              got.get(f"claims.md:{where['twice']}") == "当てられなかった")
        check("`old` が 0 箇所なら『当てられなかった』",
              got.get(f"claims.md:{where['missing']}") == "当てられなかった")
        check("陽性対照が通らなければ『当てられなかった』",
              got.get(f"claims.md:{where['badbase']}") == "当てられなかった")

        print("\n退避先の外は触らない")
        check("退避先の外を指していれば『当てられなかった』",
              got.get(f"claims.md:{where['escape']}") == "当てられなかった")
        # **的の中身をここで見ても意味が無い。** `judge()` は `finally` で必ず復元するので、
        # **テストから見るときには常に元に戻っている**（`/code-review` が飛行中の中身を
        # 観測して示した）。**だから的は `red` の出力として見る**——上の判定がそれである。

        check("出力が 1 バイトも変わらなければ『当てられなかった』（守る 13）",
              got.get(f"claims.md:{where['blind']}") == "当てられなかった")
        # **守る 13 が効かない形**——**出力が変異と無関係に変わるので素通りする**（#156）。
        check("出力が実行ごとに変わる `red` でも『当てられなかった』（守る 16）",
              got.get(f"claims.md:{where['flaky']}") == "当てられなかった")
        # **2 つの『当てられなかった』を、理由で読み分けられること。**
        check("その理由が『出力が変わらない』と区別して出る（守る 16）",
              "変異を戻して 2 度走らせても同じ結果にならない" in out)
        # **初回だけ副作用がある `red` で、本物の「主張が偽」を倒しすぎないこと**（I2）。
        # **比較相手をキャッシュした 1 度目にすると、ここが `当てられなかった` に落ちる。**
        check("初回だけ副作用がある `red` でも『緑のまま』（倒しすぎない・守る 16）",
              got.get(f"claims.md:{where['warm']}") == "緑のまま")
        # **離れた回どうしを比べると、準備の段差を「変異のせい」と読む**（守る 16）。
        check("2 段階の準備をする `red` は『当てられなかった』（守る 16）",
              got.get(f"claims.md:{where['twophase']}") == "当てられなかった")
        check("その理由は『変異の有無で結果が変わらない』（守る 16）",
              "変異の有無で結果が変わらない" in out)
        # **揃っているだけでは陽性対照にならない**（守る 16）。
        check("当て直しで非ゼロになる `red` は『当てられなかった』（守る 16）",
              got.get(f"claims.md:{where['rotted']}") == "当てられなかった")
        check("その理由は『当て直しでは緑でない』（守る 16）",
              "陽性対照が当て直しでは緑でない" in out)
        # **走らなかったことを「非決定的だ」と言わない**（守る 16）。
        # **判定はどちらも `当てられなかった` なので、理由を見ないと黙って通る。**
        # **`TIMEOUT` を一律に縮めても、この経路には入れない**——**1 度目の陽性対照が
        # 先に打ち切られ、`base_rc != 0` の側で止まる。** **3 度目だけを止める試料が要る。**
        hang_mod = load()
        hang_mod.TIMEOUT = HANG_TIMEOUT
        _, out_hang = observe(hang_mod, hang)
        got_hang = verdicts(out_hang)
        check("2 度目が走らなければ『当てられなかった』（守る 16）",
              got_hang.get(f"claims.md:{hang_line}") == "当てられなかった")
        check("その理由は『揺れている』ではなく『走らなかった』（守る 16）",
              "陽性対照の当て直しが走らなかった" in out_hang
              and "変異を戻して 2 度走らせても同じ結果にならない" not in out_hang)

        print("\n追加の実行は、倒れる直前でしか起きない（I5）")
        # **配置を何も押さえていなかった**——**当て直しのブロックを
        # `out == base_out` の *上* に持ち上げても、全部緑のままだった**
        # （1 パス目の `/code-review` が実測で指摘した）。**だから回数を数える。**
        counted = load()
        calls = {"n": 0}
        real_run = counted.run

        def counting(command, cwd):
            calls["n"] += 1
            return real_run(command, cwd)

        counted.run = counting
        observe(counted, early)
        # **陽性対照 1 回 ＋ 変異 1 回。** 当て直しの 2 回は走らない。
        # **早期の分岐で倒れる主張で数える**——**`確認` で終わる主張は、
        # 当て直しより *前* で返るので、持ち上げても回数が動かない。**
        check(f"早期に倒れる主張では `red` が 2 回だけ走る（{calls['n']} 回）",
              calls["n"] == 2)

        print("\n書式")
        check("未知のキーがあれば拒否する", "知らないキー: ['why']" in out)
        check("行末に注記が続いてもマーカーを拾う",
              got.get(f"claims.md:{where['trailing']}") == "緑のまま")
        # **行番号を手で書かない。** 試料に 1 行足すたびにずれる（実際にずれた）。
        sentinel_line = SUBJECT.split("\n").index(
            [l for l in SUBJECT.split("\n") if "mutation-claim:" in l][0]) + 1
        check("マーカー自身の行は数えない（同じファイルの中を指せる）",
              got.get(f"scripts/subject.py:{sentinel_line}") == "確認")
        check("閉じ忘れたフェンスは黙って飲まず『読めない』と言う",
              "fenced-broken.md" in out and "閉じ忘れたフェンス" in out)
        check("フェンスの中のマーカーは拾わない", f"変異の主張: {total_markers} 件" in out)

        print("\n終了コードと、緑との区別")
        check("確認できないものがあれば非ゼロ", rc == 1)
        check("『当てられなかった』だけでも非ゼロ", rc_na == 1)
        check("『当てられなかった』は緑ではないと明記する", "は緑ではない" in out_na)
        check("対象の木が無ければ非ゼロ", rc_missing == 1)

        print("\n退避先")
        box = mod.make_sandbox(root)
        try:
            check("退避先はテンポラリの中（原本の外）",
                  box.is_relative_to(Path(tempfile.gettempdir()).resolve())
                  and not str(box).startswith(str(root.resolve()) + os.sep))
            check("退避先に `.git` が 1 つも無い", not list(box.rglob(".git")))
            check("退避先に中身は入っている", (box / "scripts" / "subject.py").is_file())
        finally:
            shutil.rmtree(box, ignore_errors=True)

        print("\n落ちたときに退避先を消し残さない（守る 14・15 / #157）")
        check("退避先が原本の内側なら落ちる（`copytree` の前）",
              leak["inside"] == "RuntimeError")
        check("その落ち方で退避先が残らない", leak["inside_left"] == 0)
        check("`.git` が残っていれば落ちる（`copytree` の後・#157 を起こした道）",
              leak["dotgit"] == "RuntimeError")
        check("その落ち方でも退避先が残らない", leak["dotgit_left"] == 0)
        # **これが無いと `except Exception:` へ狭めてもどの観測も変わらない**（守る 15）。
        check("中断（`KeyboardInterrupt`）でも落ちる", leak["stopped"] == "KeyboardInterrupt")
        check("中断でも退避先が残らない（`Exception` では捕まらない）",
              leak["stopped_left"] == 0)
        # **これが無いと、後始末の開始位置を `mkdtemp` の前に戻しても観測が動かない。**
        check("`.resolve()` が落ちても投げ直す", leak["unresolved"] == "OSError")
        check("`.resolve()` が落ちても退避先が残らない", leak["unresolved_left"] == 0)
        # **落ちる側だけ見ていると、`try` を広げすぎて*返すべき退避先まで畳む*形を見逃す。**
        check("正常系では退避先を返し、中身が入っている", leak["normal"] == (True, True))

        check("原本を書き換えていない",
              (root / "scripts" / "subject.py").read_text(encoding="utf-8") == SUBJECT)

        print("\n変異テスト（壊したのに観測が変わらなければ失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}", False)
                continue
            d = Path(tmp) / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "check-mutation-claims.py"
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            (d / "markdown_fences.py").write_text(
                (REAL_REPO / "scripts" / "markdown_fences.py").read_text(encoding="utf-8"),
                encoding="utf-8")
            try:
                bad = load(broken)
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            changed = snapshot(bad, root, only_na, missing, leak_root, leak_parent) != base
            # **変異が的を書き換えたまま終わることがある**（復元は `judge` の中だけ）。
            # **次の変異の観測を汚さないよう、毎回戻す。**
            if escape.read_text(encoding="utf-8") != ESCAPE_BODY:
                escape.write_text(ESCAPE_BODY, encoding="utf-8")
            check(f"変異を殺せる: {name}", changed)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [l for l in body.splitlines() if l.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件",
              len(promises) == len(MUTATIONS))

        print("\n実リポジトリにマーカーが在るか（ここだけ実リポジトリを読む）")
        # **本体は「マーカーが 1 件も無い状態は緑になる」と宣言している。**
        # **宣言した穴を塞ぐのはこちら側**——**件数は書かない**（書くと写しになる）。
        real_claims, real_broken = mod.collect(REAL_REPO)
        check("実リポジトリに主張が 1 件以上ある", len(real_claims) + len(real_broken) > 0)
        check("実リポジトリの主張は全部読めている（書式の壊れが無い）", not real_broken)

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

        print("\n端から端まで — #157 の再現を、別プロセスで当てる")
        # **#157 を起こしたのは変異 2（`.git` を複製に持ち込む）を当てた回**で、
        # **本体は `copytree` の後で落ち、呼ぶ側の `finally` に入らないまま抜けた。**
        # **その再現をそのまま、別プロセスとして走らせる。**
        #
        # **`$TMPDIR` を隔離する（必須）。** **実 `$TMPDIR` を数える形は採らない**
        # ——**同じ置き場所を、入れ子で走る同じスクリプト自身が使う**ので、
        # **判定が外の事情で揺れる**（実測: `check-mutation-claims.py` を 2 回回して
        # **1 回目は走行中に 1 件増え、2 回目は 6 件増えた**。**直接実行では 0 件**）。
        # **揺れる数を受入条件にすると、赤も緑も意味を持たない。**
        iso = Path(tmp) / "iso-tmp"
        iso.mkdir()
        mut_dir = Path(tmp) / "mut-dotgit"
        mut_dir.mkdir()
        needle, replacement = MUTATIONS["`.git` を複製に持ち込む"]
        mutated = mut_dir / "check-mutation-claims.py"
        mutated.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
        (mut_dir / "markdown_fences.py").write_text(
            (REAL_REPO / "scripts" / "markdown_fences.py").read_text(encoding="utf-8"),
            encoding="utf-8")
        proc = subprocess.run([sys.executable, str(mutated), str(root)],
                              env=dict(os.environ, TMPDIR=str(iso)),
                              capture_output=True, text=True, check=False)
        # **陽性対照を先に見る（必須）。** **「残っていない」は、子が退避先まで
        # 辿り着かなかった場合も同じ形で出る**——**実測で、後始末を戻した（欠陥あり）うえに
        # `markdown_fences.py` を置き忘れて import で死なせても、この検査は緑だった**
        # （`/code-review` が反証した）。**通るはずの形が通ることを併せて見る。**
        said = proc.stdout + proc.stderr
        check("子は安全弁まで辿り着いて落ちた（陽性対照）",
              proc.returncode != 0 and "退避先に .git が残っている" in said)
        # **数えている場所が合っているかも見る（必須）。** **辿り着いたことは、
        # *ここ*を数えてよいことを意味しない**——**`TMPDIR` のキーを 1 文字打ち間違えるだけで、
        # 子は実 `$TMPDIR` に作り、`iso` は永久に空になる**（`0 件` で緑のまま）。
        # **実測で再現された**（2 パス目の `/code-review`。**打ち間違い＋後始末を外した状態で、
        # この検査は緑のまま、実 `$TMPDIR` に 2 件漏れた**）。
        # **子の `RuntimeError` は退避先のパスを名乗る**ので、そこで確かめる。
        check("子の退避先は、隔離した TMPDIR の中にあった", str(iso.resolve()) in said)
        strays = list(iso.glob("mutation-claims-*"))
        check(f"変異 2 を当てた実行が退避先を残さない（{len(strays)} 件）", not strays)

    if failures:
        print(f"\nFAILED: {len(failures)} 件")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\n変異主張の検査のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
