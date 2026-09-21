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

    root/scripts/subject.py       変異を当てられる側（`KEEP` を含む）
    root/scripts/subject_test.py  `red`。`KEEP` が残っていれば 0、消えていれば 1
    root/scripts/always_red.py    陽性対照を落とすための、常に 1 を返すコマンド
    root/claims.md                マーカー（フェンスの中に 1 つ紛れ込ませてある）
    root/.git/                    **複製に持ち込まれてはならないもの**

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


SUBJECT = "# KEEP\n# HARMLESS\n# TWICE\n# TWICE\n"

SUBJECT_TEST = (
    "import pathlib, sys\n"
    'sys.exit(0 if "KEEP" in pathlib.Path("scripts/subject.py").read_text() else 1)\n'
)

ALWAYS_RED = "import sys\nsys.exit(1)\n"

RED = "python3 scripts/subject_test.py"


def marker(**spec) -> str:
    return "mutation-claim: " + json.dumps(spec, ensure_ascii=False)


def build(root: Path) -> None:
    """判定の 3 つが全部出そろう偽のツリーを作る。"""
    assert_not_real_repo(root)
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "subject.py").write_text(SUBJECT, encoding="utf-8")
    (root / "scripts" / "subject_test.py").write_text(SUBJECT_TEST, encoding="utf-8")
    (root / "scripts" / "always_red.py").write_text(ALWAYS_RED, encoding="utf-8")
    # **複製に持ち込まれてはならないもの。** 実物の worktree では `.git` は
    # **本体を指すファイル**だが、除外の対象という点は同じ。
    (root / ".git").mkdir()
    (root / ".git" / "HEAD").write_text("ref: refs/heads/fake\n", encoding="utf-8")

    subject = "scripts/subject.py"
    lines = [
        "# 主張の一覧",
        "",
        marker(file=subject, old="KEEP", new="GONE", red=RED),
        "",
        marker(file=subject, old="HARMLESS", new="HARMLESS2", red=RED),
        "",
        marker(file=subject, old="TWICE", new="X", red=RED),
        "",
        marker(file=subject, old="NOWHERE", new="X", red=RED),
        "",
        marker(file=subject, old="KEEP", new="GONE", red="python3 scripts/always_red.py"),
        "",
        marker(file="../outside.txt", old="KEEP", new="GONE", red=RED),
        "",
        # **必須のキーは全部あって、余計なキーが 1 つだけある形。**
        # **これが無いと「未知のキーを拒否する」変異が殺せない**
        # ——足りないキーの側で先に落ちてしまい、区別がつかない。
        'mutation-claim: {"file": "scripts/subject.py", "old": "KEEP", "new": "GONE", '
        f'"red": "{RED}", "why": "余計なキー"}}',
        "",
        "書式の例はフェンスに入れる:",
        "",
        "```text",
        marker(file=subject, old="KEEP", new="GONE", red=RED),
        "```",
        "",
    ]
    (root / "claims.md").write_text("\n".join(lines), encoding="utf-8")


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
        "    if hits != 1:",
        "    if hits == 0:"),
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
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "tree"
        root.mkdir()
        build(root)
        only_na = Path(tmp) / "only-not-applied"
        only_na.mkdir()
        build_only_not_applied(only_na)

        mod = load()
        rc, out = observe(mod, root)
        got = verdicts(out)
        rc_na, out_na = observe(mod, only_na)

        print("3 つの判定が出そろうか")
        check("主張どおりなら『確認』", got.get("claims.md:3") == "確認")
        check("変異を当てても緑なら『緑のまま』", got.get("claims.md:5") == "緑のまま")
        check("`old` が 2 箇所なら『当てられなかった』",
              got.get("claims.md:7") == "当てられなかった")
        check("`old` が 0 箇所なら『当てられなかった』",
              got.get("claims.md:9") == "当てられなかった")
        check("陽性対照が通らなければ『当てられなかった』",
              got.get("claims.md:11") == "当てられなかった")
        check("退避先の外を指していれば『当てられなかった』",
              got.get("claims.md:13") == "当てられなかった")

        print("\n書式")
        check("未知のキーがあれば拒否する", "知らないキー: ['why']" in out)
        check("フェンスの中のマーカーは拾わない", "claims.md:21" not in out)
        check("集めた件数を必ず出す", "変異の主張: 7 件" in out)

        print("\n終了コードと、緑との区別")
        check("確認できないものがあれば非ゼロ", rc == 1)
        check("『当てられなかった』だけでも非ゼロ", rc_na == 1)
        check("『当てられなかった』は緑ではないと明記する",
              "は緑ではない" in out_na)

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
            # **2 つのツリーの両方で観測する。** 「当てられなかった」だけのツリーが
            # 無いと、守る 5 の変異が殺せない。
            changed = (observe(bad, root) != (rc, out)) or (observe(bad, only_na) != (rc_na, out_na))
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
