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

    root/scripts/subject.py       変異を当てられる側（マーカーを 1 つ自分の中に持つ）
    root/scripts/subject_test.py  `red`。`# KEEP` と `# SENTINEL` の行が両方残っていれば 0
    root/scripts/always_red.py    陽性対照を落とすための、常に 1 を返すコマンド
    root/scripts/blind_test.py    中身を見ない `red`。**出力が変わらない緑**を作る
    root/scripts/escape_test.py   **退避先の外**の的を読んで出力する `red`
    root/claims.md                マーカー（フェンスの中に 1 つ紛れ込ませてある）
    root/fenced-broken.md         閉じ忘れたフェンスの後ろにマーカーがある形
    root/.git/                    **複製に持ち込まれてはならないもの**
    <TMPDIR>/cmc-escape-<pid>.txt **退避先の外**。`../` で指しても触られてはならない

dup-counts-ok: 変異
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
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


def snapshot(mod, root: Path, only_na: Path, missing: Path) -> tuple:
    """3 つの木を、まとめて 1 つの観測にする。

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

        mod = load()
        base = snapshot(mod, root, only_na, missing)
        (rc, out), (rc_na, out_na), (rc_missing, _) = base
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
            import shutil
            shutil.rmtree(box, ignore_errors=True)
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
            changed = snapshot(bad, root, only_na, missing) != base
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

    if failures:
        print(f"\nFAILED: {len(failures)} 件")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\n変異主張の検査のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
