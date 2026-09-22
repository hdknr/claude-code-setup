#!/usr/bin/env python3
"""`check-all.py` の回帰テスト。

    python3 scripts/test-check-all.py

**このテストは実環境を書き換えない。** 集約の挙動はテンポラリに作った偽スクリプトだけを
対象にする（`assert_not_real_repo` がそれを担保する）。**収録漏れの検査だけは実リポジトリを
読む**——**そこが検査の対象そのもの**だからで、**読むだけで書かない。**

**変異テストを含む。** 形は「**契約**を 1 組の表明として書き、**本体を 1 箇所ずつ壊して、
その契約が破れることを要求する**」。**壊したのに契約が保たれるなら、その契約は
その箇所を見ていない**ので失格とする。

**この runner の壊れ方は「落とす」である**——登録から 1 本落とす・落ちたのに数えない・
飛ばしたのに黙っている。**契約はその 3 つに対応させてある。**

**変異は 2 組ある**——`MUTANTS` は `check-all.py`（集約）に、`SCAN_MUTANTS` は
**このファイルの中の判別**（CI の yaml の読み方）に当てる。**後者は自分自身を壊す。**

## CI の走査が、何を守り、何を守らないか（#155）

守る:

- **`check-all.py` に収録したスクリプトが、CI の yaml に `run:` として書かれているか。**
- **コメントアウトされたステップを「走っている」と数えない**——
  **`# - run: …` も `"run:" in l` を満たすので、素の行走査では素通しだった。**
- **「そもそも無い」と「コメントアウトされている」を分けて報告する**
  ——**どちらも「CI では走らない」だが、ステップを足すのと `#` を外すのでは直し方が違う。**
  **分けられるのは、コメントの側に `run:` と名前が*揃っている*ときだけ**（下の「守らない」）。
- **行末コメントの中の名前を、生きた名前として数えない。**
- **`check-X.py` が `test-check-X.py` に覆い隠されない**（#136 で 6 本が隠れていた）。
- **引用符の中の `#` で切らない**——切ると、その後ろの名前が落ちて「無い」と誤報する。
- **語の途中のアポストロフィで引用符を開かない**——開くと**行末まで閉じず、
  コメントが丸ごと「生きている」側に入る**（`run: echo don't  # python3 scripts/x.py`）。
  **これは偽陰性で、#155 の欠陥と同じ向きである**——`/code-review` の 1 パス目が実測で見つけた。

守らない:

- **「CI で実際に走った」の証明ではない。** 見ているのは**記述**だけで、
  **ジョブやステップの `if:` 条件・`continue-on-error`・ステップ内での失敗握り潰し**は
  見ていない。**言えるのは「走る形で書かれている」まで。**
- **コメントの側に `run:` が無い無効化は、コメント側として拾えない。**
  3 つの形がある——**(a)** `# run:` の次の行に `#   python3 scripts/x.py` と割った形、
  **(b)** コメントアウトした `run: |` のブロック、
  **(c)** **行末で殺した形**（`run: echo skip  # python3 scripts/x.py`。
  `run:` が生きている側に残る）。
  **いずれも「そもそも無い」側に出るので赤にはなるが、案内する直し方が
  「ステップを足す」になる**——**`#` を外せば済むのに。**
  **(c) を「コメントアウト」と数えないのは意図的である**——
  **行末の注記に名前が出ているだけの行と、構文で区別できない**
  （上の「行末コメントの中の名前を、生きた名前として数えない」と同じ行の形）。
- **`run: |` `run: >-` のブロック本文で呼ばれたスクリプトは拾わない**（`run:` を含む行だけを見るため）。
  **向きは偽陽性**（在るのに「無い」と言う）で、**黙って素通しする #155 の欠陥とは逆**。
  **該当は現在 0 件。**
- **ワークフローファイルごと消す・`on:` を変える**——**`*.yml` を読むだけなので、
  そのファイルが実際に起動するかは見ていない。**
- **`*.yaml`（拡張子違い）は読まない。**
- **引用符の中の `\\"` のような退避は解さない**——そこで閉じたと見なす。
  **向きは偽陽性**（在るのに「無い」と言う）なので、**黙って素通しはしない。**
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "scripts"
TARGET = SCRIPTS / "check-all.py"

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


def assert_not_real_repo(root: Path) -> None:
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの対象が実リポジトリの内側にある"
    )
    tmp_root = Path(tempfile.gettempdir()).resolve()
    assert root.resolve().is_relative_to(tmp_root), "テストの対象がテンポラリの外にある"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_main(mod, argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["check-all.py", *argv]
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
    finally:
        sys.argv = old
    return rc, buf.getvalue()


# ------------------------------------------------------------- 偽の scripts/
def build_fake(root: Path) -> Path:
    """偽の scripts/ を作り、そこに置いた check-all.py のパスを返す。"""
    assert_not_real_repo(root)
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ok-a.py").write_text("print('a ok')\n")
    (scripts / "ok-b.py").write_text("print('b ok')\n")
    (scripts / "ok-c.py").write_text("print('c ok')\n")
    (scripts / "bad.py").write_text("import sys; print('BOOM-GUARD'); sys.exit(1)\n")
    (scripts / "bad-test.py").write_text("import sys; print('BOOM-TEST'); sys.exit(1)\n")
    (scripts / "needs-base.py").write_text("print('base ok')\n")
    target = scripts / "check-all.py"
    target.write_text(TARGET.read_text())
    return target


def wire(mod, root: Path, *, bad_guard: bool, bad_test: bool) -> None:
    mod.SCRIPTS = root / "scripts"
    mod.GUARDS = [("ok-a.py", [], False), ("ok-c.py", [], False),
                  ("needs-base.py", [], True)]
    mod.TESTS = ["ok-b.py"]
    if bad_guard:
        # **ok-c.py より前**に挟む。後ろに通る歯止めが無いと、
        # 「最初の失敗で止める」変異を契約が捕まえられない（実際に一度そうなった）。
        # **この主張は機械で当ててある**（#151）——後ろに回すと、この回帰テストが赤くなる。
        # mutation-claim: {"file": "scripts/test-check-all.py", "old": "GUARDS.insert(1, (\"bad.py\"", "new": "GUARDS.append((\"bad.py\"", "red": "python3 scripts/test-check-all.py"}
        mod.GUARDS.insert(1, ("bad.py", [], False))
    if bad_test:
        mod.TESTS.append("bad-test.py")


# ------------------------------------------------------------------- 契約
# **本体を壊したときに、少なくとも 1 つが破れなければならない。**
def contract(target: Path, root: Path, tag: str) -> list[tuple[str, bool]]:
    got: list[tuple[str, bool]] = []

    # 1) 全部通る。base は解決できない → base を要する 1 本は SKIP。
    mod = load(target, f"{tag}_pass")
    wire(mod, root, bad_guard=False, bad_test=False)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("全部通れば rc=0", rc == 0),
        ("飛ばしたものを数えて出す", "飛ばし 1" in out),
        ("飛ばしたことを黙らない", "飛ばしたものは回していない" in out),
        ("SKIP でも残りは回る", "OK   ok-b.py" in out),
    ]

    # 2) 歯止めだけが落ちる
    mod = load(target, f"{tag}_badguard")
    wire(mod, root, bad_guard=True, bad_test=False)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("歯止めが落ちたら rc=1", rc == 1),
        ("歯止めの失敗を名指しする", "落ちたもの: bad.py" in out),
        ("歯止めが落ちても後続の歯止めを回す", "OK   ok-c.py" in out),
        ("歯止めが落ちても回帰テストを回す", "OK   ok-b.py" in out),
        ("歯止めの失敗の出力を見せる", "BOOM-GUARD" in out),
    ]

    # 3) 回帰テストだけが落ちる（歯止めとは別の経路で数えている）
    mod = load(target, f"{tag}_badtest")
    wire(mod, root, bad_guard=False, bad_test=True)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("回帰テストが落ちたら rc=1", rc == 1),
        ("回帰テストの失敗を名指しする", "落ちたもの: bad-test.py" in out),
        ("回帰テストの失敗の出力を見せる", "BOOM-TEST" in out),
        ("回帰テストの失敗を 1 件と数える", "失敗 1" in out),
    ]

    # 4) --guards-only は回帰テストを飛ばし、そのことを出す
    mod = load(target, f"{tag}_guardsonly")
    wire(mod, root, bad_guard=False, bad_test=False)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz", "--guards-only"])
    got += [
        ("--guards-only で回帰テストを回さない", "OK   ok-b.py" not in out),
        ("--guards-only でも飛ばしたことを出す", "飛ばしたものは回していない" in out),
    ]
    return got


def contract_with_base(target: Path, root: Path, tag: str) -> list[tuple[str, bool]]:
    """base が解決できるなら、base を要する検査も回る。"""
    mod = load(target, f"{tag}_base")
    wire(mod, root, bad_guard=False, bad_test=False)
    rc, out = run_main(mod, ["--base", "HEAD"])
    return [
        ("base が解決できれば飛ばさない", "飛ばし 0" in out),
        ("base を要する検査が回る", "OK   needs-base.py" in out),
        ("base ありでも全部通れば rc=0", rc == 0),
    ]


# ---------------------------------------------------------------- 収録漏れ
def load_target():
    """`check-all.py` をモジュールとして読む。**宣言そのものを見るため。**"""
    spec = importlib.util.spec_from_file_location("check_all_target", TARGET)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_registry_covers_every_script() -> None:
    """実リポジトリを読む。`scripts/` に検査を足して登録し忘れたら落とす。"""
    src = TARGET.read_text()
    guards = sorted(
        p.name for p in SCRIPTS.glob("check-*.py") if p.name != "check-all.py"
    ) + ["skill-metrics.py"]
    tests = sorted(
        p.name for p in SCRIPTS.glob("test-*.py") if p.name != "test-check-all.py"
    )
    missing_g = [n for n in guards if f'"{n}"' not in src]
    missing_t = [n for n in tests if f'"{n}"' not in src]
    check(f"歯止めを全部収録している（{len(guards)} 本）", not missing_g)
    if missing_g:
        print(f"       収録漏れ: {missing_g}")
    check(f"回帰テストを全部収録している（{len(tests)} 本）", not missing_t)
    if missing_t:
        print(f"       収録漏れ: {missing_t}")


# ------------------------------------------------------ yaml のコメント判別
NAME_RE = re.compile(r"scripts/([A-Za-z0-9_.-]+\.py)")


def opens_quote(line: str, i: int) -> bool:
    """引用符が**値の先頭に立っているときだけ**、引用符として開く。

    **語の途中のアポストロフィ（`echo don't`）で開いてはならない。**
    開くと**閉じないまま行末まで走り、その行のコメントが丸ごと「生きている」側に入る**
    ——**`run: echo don't  # python3 scripts/check-foo.py` が「走っている」と数えられる。**
    **向きは偽陰性で、#155 が閉じようとしている欠陥そのものである。**
    **`/code-review` の 1 パス目が、実際の `plugins.yml` で赤にならないことを示して見つけた**
    ——**歯止めを足した当人が、同じ型の穴を別の場所に作っていた**（#136 と同じ形）。
    """
    return i == 0 or line[i - 1] in " \t:"


def split_comment(line: str) -> tuple[str, str]:
    """yaml の 1 行を「生きている部分」と「コメントの部分」に割る。

    **`#` がコメントを始めるのは、行頭か、直前が空白のときだけ**（`a#b` は値の一部）。
    **引用符の中の `#` はコメントではない**——そこで切ると、**後ろに書かれた
    スクリプト名が落ちて「CI に無い」と誤報する**。向きは偽陽性（在るのに「無い」）なので
    #155 の欠陥とは逆だが、**誤報には違いない。**
    """
    quote = ""
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'" and opens_quote(line, i):
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i], line[i:]
    return line, ""


def scan_ci_runs(ci: str) -> tuple[set[str], set[str]]:
    """CI の yaml から `run:` に現れるスクリプト名を拾い、**2 つに分けて**返す。

    返すのは `(生きている, コメントアウトされている)`。**分けるのが要点**で、
    「**そもそも無い**」と「**コメントアウトされている**」は**直し方が違う**
    ——前者はステップを足す、後者は `#` を外す。**どちらも「CI では走らない」。**

    **`run:` を含む行だけを見る**のは元のままで（`- name:` のラベルに名前が出ているだけの
    行を数えないため）、**判定をその行の*生きている部分*に限る**のが #155 の修正である。
    """
    live: set[str] = set()
    commented: set[str] = set()
    for raw in ci.split("\n"):
        code, comment = split_comment(raw)
        if "run:" in code:
            live |= set(NAME_RE.findall(code))
        if "run:" in comment:
            commented |= set(NAME_RE.findall(comment))
    return live, commented


def test_ci_runs_every_registered_script() -> None:
    """実リポジトリを読む。**`check-all.py` に在るのに CI の yaml に無い**なら落とす。

    **`check-all.py` は CI から呼ばない**（`CLAUDE.md` のとおり、どれが落ちたか UI に
    出すため各スクリプトを個別ステップにしている）。**だから収録と CI 登録は別の作業**で、
    **片方だけ済ませると、そのテストは手元でしか走らない。**

    **照合は名前単位で行う（必須の注意）。** **素の部分文字列一致では、`check-X.py` が
    `test-check-X.py` に覆い隠される**——**最初そう書いて、2 パス目の Verifier に
    「6 本が隠れる」と反証された。** **歯止めを足した当人が、同じ型の盲点を作っていた。**

    **上の `test_registry_covers_every_script` はこの向きを見ていなかった**——
    「`scripts/` に在るのに `check-all.py` に無い」は見るが、
    「`check-all.py` に在るのに CI に無い」は見ない。**実際に 2 本が漏れていた**
    （`test-find-cycle.py` は #136 段 1 から、`test-collect-guard-rejections.py` は
    #122 から。**どちらも手元では緑、CI では 1 度も走っていなかった**）。
    **手順 5 の Verifier が見つけた**（#136 の全段に掛けた回）。

    **コメントアウトされたステップを「走っている」と数えない（#155）。**
    元の実装は `"run:" in l` を満たす行から名前を拾っていたので、
    **`# - run: python3 scripts/check-foo.py` も条件を満たしていた**
    ——**CI のステップをコメントアウトしても、この検査は緑のまま**だった。
    **コメントアウトは、上の 2 本が出荷された状態に戻る最短経路である。**

    **この主張は、実際に当てて確かめる**——`plugins.yml` の生きたステップを 1 つ
    コメントアウトすると、このテストが赤になる（**陽性対照は、変異の前に緑であることで取る**）:

    mutation-claim: {"file": ".github/workflows/plugins.yml", "old": "        run: python3 scripts/check-duplicate-counts.py", "new": "        # run: python3 scripts/check-duplicate-counts.py", "red": "python3 scripts/test-check-all.py"}
    """
    workflows = REAL_REPO / ".github" / "workflows"
    # **ファイルの境界に改行を挟む。** **素の連結では、末尾に改行の無い yaml が
    # 1 本混ざった時点で、そのファイルの最終行と次のファイルの先頭行が 1 行に繋がる**
    # ——**判別は行単位なので、繋がった側のコメントが生きた側を飲み込む。**
    # **いまは全ファイルが改行で終わっているので実害は無い**（手順 5 の Verifier が確認）。
    ci = "\n".join(f.read_text() for f in sorted(workflows.glob("*.yml")))
    # **正規表現でソースから拾わない。** **名前に数字や下線が入る・引用符が変わる・
    # 変数から組み立てる**といった変更で `registered` が静かに空になり、
    # **「0 本を検査して OK」**になる（`/code-review` が指摘。#136）。
    # **モジュールを読んで、宣言そのものを見る。**
    mod = load_target()
    registered = sorted({name for name, _, _ in mod.GUARDS} | set(mod.TESTS))
    check("収録の一覧が空でない（空振りしない）", len(registered) > 0)
    # **素の部分文字列一致にしない。** `check-X.py` は **`test-check-X.py` の部分文字列**
    # なので、**`check-X.py` の CI ステップを消しても、`test-` 版が残っていれば隠れる**
    # ——**実測で 6 本が覆い隠されていた**（#136 の 2 パス目で Verifier が指摘）。
    # **`scripts/` の直後から行末・空白までを 1 つの名前として照合する**（`NAME_RE`）。
    live, commented = scan_ci_runs(ci)
    # **2 つに分けて報告する（#155）。** どちらも「CI では走らない」だが、
    # **ステップを足すのと `#` を外すのでは直し方が違う。**
    absent = [n for n in registered if n not in live and n not in commented]
    disabled = [n for n in registered if n not in live and n in commented]
    check(f"収録したものが CI の yaml に在る（{len(registered)} 本）", not absent)
    if absent:
        print(f"       CI の yaml に無い: {absent}")
        print("       **ステップを足す。** 手元では緑でも、CI では 1 度も走らない。")
    check("収録したものの CI ステップが生きている（コメントアウトされていない）", not disabled)
    if disabled:
        print(f"       コメントアウトされている: {disabled}")
        print("       **`#` を外す。** 手元では緑でも、CI では 1 度も走らない。")


# ------------------------------------------------------------------ 変異
MUTANTS = {
    "歯止めが落ちても failed に積まない": (
        "            failed.append(label)\n", "            pass\n"),
    "回帰テストが落ちても failed に積まない": (
        "                failed.append(name)\n", "                pass\n"),
    "失敗があっても 0 を返す": ("        return 1\n", "        return 0\n"),
    "落ちたものの出力を見せない": (
        "        print(out.rstrip())\n", "        pass\n"),
    "飛ばしたことを黙る": (
        '        print("**飛ばしたものは回していない。** '
        '手元の緑をそのまま「全部緑」と報告しない。")\n',
        "        pass\n"),
    "最初の失敗で止める": ("            logs.append((label, out))\n",
                           "            logs.append((label, out))\n            break\n"),
}


# ------------------------------------------------- 判別の契約（合成試料）
# **実物の yaml では、この経路は永久に空振りする**——`.github/workflows/` に
# **コメントアウトされたステップは 1 件も無い**（#155 の時点で 0 件）。
# **試料のほうに、経路を全部踏ませる。**
SAMPLE_CI = """\
jobs:
  probe:
    steps:
      - name: 生きたステップ
        run: python3 scripts/check-live.py

      # - name: 止めたステップ
      #   run: python3 scripts/check-dead.py

      - name: scripts/check-label-only.py のラベルにだけ名前がある
        run: echo ok

      - name: 行末にコメント
        run: python3 scripts/check-live2.py  # scripts/check-trailing.py は別

      - name: 名前が覆い隠される
        run: python3 scripts/test-check-mask.py

      - name: 引用符の中の `#`
        run: "echo 'PR #155' && python3 scripts/check-quoted.py"

      - name: 語の途中のアポストロフィ
        run: echo don't  # python3 scripts/check-apostrophe.py

      # - name: 名前と run: を別の行に割って止めたステップ（**守らない**）
      #   run:
      #     python3 scripts/check-dead-split.py

      - name: 常に偽の条件（**守らない**——記述しか見ていない）
        if: false
        run: python3 scripts/check-killed-by-if.py

      - name: ブロックで呼ぶ（**守らない**——`run:` を含む行だけを見る）
        run: |
          python3 scripts/check-in-block.py
"""
# **この試料そのものについての主張も、機械で当てる**——
# **コメントアウトされたステップを抜くと、「それと分かる形で拾う」契約が空振りする**
# （#151 が言う「試料についての主張」。**書いた時点から一度も実行されない**のを避ける）:
# mutation-claim: {"file": "scripts/test-check-all.py", "old": "      #   run: python3 scripts/check-dead.py\n", "new": "", "red": "python3 scripts/test-check-all.py"}


def scan_contract(scan) -> list[tuple[str, bool]]:
    """**判別の契約。** 各行が `SAMPLE_CI` のどれかの経路に対応している。

    **陽性側も取る**——「拾わない」だけを並べると、**もともと空の集合**と区別がつかない
    （**陰性だけの対照は対照ではない**）。
    """
    live, commented = scan(SAMPLE_CI)
    seen = live | commented
    return [
        ("生きたステップを拾う（陽性対照）", "check-live.py" in live),
        ("コメントアウトされたステップを、生きている側に数えない",
         "check-dead.py" not in live),
        ("コメントアウトされたステップを、それと分かる形で拾う",
         "check-dead.py" in commented),
        ("`- name:` のラベルだけの名前は拾わない", "check-label-only.py" not in seen),
        ("行末コメントの中の名前は拾わない（その行の生きた名前は拾う）",
         "check-trailing.py" not in seen and "check-live2.py" in live),
        ("`check-X.py` が `test-check-X.py` に覆い隠されない",
         "check-mask.py" not in seen and "test-check-mask.py" in live),
        ("引用符の中の `#` で切らない", "check-quoted.py" in live),
        # **こちらは逆向き**——上は「早く切りすぎない」、これは「切り損ねない」。
        # **片側だけ試料に置くと、切り損ねる欠陥を契約が判別できない**
        # （`/code-review` 1 パス目の指摘。**実際にこの向きの穴が残っていた**）。
        ("語の途中のアポストロフィで引用符を開かない", "check-apostrophe.py" not in seen),
        # **守らないものも契約に書く**——**限界を機械で見える形に留める**ため。
        # **黙って射程が変わったら、docstring の「守らない」と食い違ったまま緑になる。**
        ("名前と `run:` が別の行に割れたコメントアウトは、コメント側として拾えない（守らない）",
         "check-dead-split.py" not in seen),
        ("`if:` で止めたステップは、生きているものとして数える（守らない）",
         "check-killed-by-if.py" in live),
        ("`run: |` のブロック本文は拾わない（守らない）", "check-in-block.py" not in seen),
    ]


# ------------------------------------------------------------ 判別の変異
# **この battery は*自分自身*を壊す**ので、**当て先を数える範囲から辞書自身を外す**
# ——**辞書に書いた文字列も「その文字列の出現」なので、素に数えると必ず 2 箇所になり、
# 「当て先が 1 箇所」の検査が全件落ちる。**
SELF_SRC = Path(__file__).resolve().read_text()
CODE_ONLY = SELF_SRC.split("\nSCAN_MUTANTS")[0]

SCAN_MUTANTS = {
    "コメントの始まりを見ない": (
        '        elif ch == "#" and (i == 0 or line[i - 1] in ',
        '        elif False and (i == 0 or line[i - 1] in '),
    "引用符を見ない": ("        elif ch in ", "        elif False and ch in "),
    "語の途中でも引用符を開く": (
        r'    return i == 0 or line[i - 1] in " \t:"', "    return True"),
    "生きている側とコメント側を取り違える": (
        "            return line[:i], line[i:]",
        "            return line[i:], line[:i]"),
    "`run:` の行に限らない": ('        if "run:" in code:', "        if True:"),
    "コメント側を集めない": ('        if "run:" in comment:', "        if False:"),
    "`test-` を剥がして照合する（覆い隠しが戻る）": (
        r'NAME_RE = re.compile(r"scripts/([A-Za-z0-9_.-]+\.py)")',
        r'NAME_RE = re.compile(r"scripts/(?:test-)?([A-Za-z0-9_.-]+\.py)")'),
}


def main() -> int:
    print("収録漏れ（実リポジトリを読むだけ）:")
    test_registry_covers_every_script()
    test_ci_runs_every_registered_script()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        print("契約（本体そのまま——全部通らなければならない）:")
        target = build_fake(root / "real")
        for name, ok in contract(target, root / "real", "real"):
            check(name, ok)

        repo = root / "withbase"
        target = build_fake(repo)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-q", "--allow-empty", "-m", "init"], check=True)
        for name, ok in contract_with_base(target, repo, "wb"):
            check(name, ok)

        print("判別（合成試料——全部通らなければならない）:")
        for name, ok in scan_contract(scan_ci_runs):
            check(name, ok)

        print("判別の変異（1 箇所ずつ壊す——契約が破れなければ失格）:")
        # **切れていなければ、当て先は必ず 2 箇所になって全件落ちる。**
        # **6 件の「当て先が 1 箇所」より、切れていないことを 1 行で言うほうが速い。**
        check("当て先を数える範囲が、辞書の手前で切れている", CODE_ONLY != SELF_SRC)
        for i, (name, (old, new)) in enumerate(SCAN_MUTANTS.items()):
            if CODE_ONLY.count(old) != 1:
                check(f"変異 `{name}` の当て先が 1 箇所", False)
                continue
            d = root / f"scan{i}"
            assert_not_real_repo(d)
            d.mkdir()
            p = d / "scanned.py"
            # **辞書より前に 1 箇所しか無いことを上で確かめてある**ので、
            # **最初の 1 件だけ置き換えれば、当たるのは判別の本体である。**
            p.write_text(SELF_SRC.replace(old, new, 1))
            broken = [n for n, ok in scan_contract(load(p, f"scanned{i}").scan_ci_runs)
                      if not ok]
            check(f"変異 `{name}` を契約が捕まえる", bool(broken))
            if not broken:
                print("       壊したのに契約が全部通った")

        print("変異（1 箇所ずつ壊す——契約が破れなければ失格）:")
        src = TARGET.read_text()
        for i, (name, (old, new)) in enumerate(MUTANTS.items()):
            if src.count(old) != 1:
                check(f"変異 `{name}` の当て先が 1 箇所", False)
                continue
            d = root / f"mut{i}"
            t = build_fake(d)
            t.write_text(src.replace(old, new))
            broken = [n for n, ok in contract(t, d, f"m{i}") if not ok]
            check(f"変異 `{name}` を契約が捕まえる", bool(broken))
            if not broken:
                print("       壊したのに契約が全部通った")

    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


if __name__ == "__main__":
    sys.exit(main())
