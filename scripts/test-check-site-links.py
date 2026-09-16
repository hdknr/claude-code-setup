#!/usr/bin/env python3
"""`check-site-links.py` の回帰テスト。

    python3 scripts/test-check-site-links.py

**このテストは実環境を触らない。** 毎回テンポラリに偽リポジトリを作り、そこだけを対象にする
（`assert_not_real_repo` がそれを担保する）。

**変異テストを含む。** 検査本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
「正しい入力で緑」だけでは、**何も検査しない実装でも通る**。
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "check-site-links.py"
HELPER = REAL_REPO / "scripts" / "site_links.py"
SITE = "https://hdknr.github.io/claude-code-setup/"

failures: list[str] = []


def assert_not_real_repo(root: Path) -> None:
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの対象が実リポジトリの内側にある"
    )
    tmp_root = Path(tempfile.gettempdir()).resolve()
    assert root.resolve().is_relative_to(tmp_root), "テストの対象がテンポラリの外にある"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def build(root: Path, files: dict[str, str], *, script_text: str | None = None) -> None:
    """偽リポジトリを作る。`files` は docs/ とそれ以外を混ぜて渡してよい。"""
    assert_not_real_repo(root)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / SCRIPT.name).write_text(
        script_text if script_text is not None else SCRIPT.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    shutil.copy(HELPER, root / "scripts" / HELPER.name)
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / SCRIPT.name)],
        cwd=root, capture_output=True, text=True,
    )


DOC = "# 設計\n\n## 検証 { #verify }\n\n本文。\n"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="csl-test-") as tmp:
        base = Path(tmp)

        print("正常系")
        root = base / "ok"
        build(root, {
            "docs/plugins/design.md": DOC,
            "CLAUDE.md": f"[設計]({SITE}plugins/design/#verify) を見ること。\n",
        })
        check("実在するアンカーは通る", run(root).returncode == 0)

        print("壊れたアンカーを捕まえる")
        root = base / "bad-anchor"
        build(root, {
            "docs/plugins/design.md": DOC,
            "CLAUDE.md": f"[設計]({SITE}plugins/design/#missing) を見ること。\n",
        })
        proc = run(root)
        check("存在しないアンカーで落ちる", proc.returncode != 0)
        check("アンカー名を理由に出す", "#missing" in proc.stderr)

        print("壊れたページを捕まえる")
        root = base / "bad-page"
        build(root, {
            "docs/plugins/design.md": DOC,
            "CLAUDE.md": f"[設計]({SITE}plugins/nowhere/#verify)\n",
        })
        check("存在しないページで落ちる", run(root).returncode != 0)

        print("`plugins/` の外も見る（既存の検査が見ていなかった範囲）")
        # **これがこの検査を足した理由。** `check-plugin-versions.py` は
        # `plugins/` 配下しか見ておらず、実測で 30 件中 13 件が無検査だった。
        for label, rel in (
            ("CLAUDE.md", "CLAUDE.md"),
            ("scripts/ の Python", "scripts/some-tool.py"),
            ("docs/ の中", "docs/guide.md"),
            ("README.md", "README.md"),
        ):
            root = base / f"scope-{rel.replace('/', '-')}"
            build(root, {
                "docs/plugins/design.md": DOC,
                rel: f'"""[設計]({SITE}plugins/design/#missing)"""\n',
            })
            check(f"{label} のリンクも見る", run(root).returncode != 0)

        print("走査しない場所")
        root = base / "skip"
        build(root, {
            "docs/plugins/design.md": DOC,
            "site/plugins/index.html": f"[設計]({SITE}plugins/design/#missing)\n",
            ".claude/plans/issue-1.md": f"[設計]({SITE}plugins/design/#missing)\n",
        })
        check("site/ と .claude/ は見ない", run(root).returncode == 0)

        print("URL の切れ目")
        root = base / "boundary"
        cases = "\n".join([
            f"`{SITE}plugins/design/#verify`",
            f"（{SITE}plugins/design/#verify）",
            f"<{SITE}plugins/design/#verify>",
            f"{SITE}plugins/design/#verify。次の文",
            f"**{SITE}plugins/design/#verify**",
            f'"{SITE}plugins/design/#verify"',
            f"| {SITE}plugins/design/#verify |",
        ])
        build(root, {"docs/plugins/design.md": DOC, "CLAUDE.md": cases})
        proc = run(root)
        check("囲みや区切りで誤検出しない", proc.returncode == 0)

        print("サイトのルートだけのリンクは検査しない")
        root = base / "root-link"
        build(root, {
            "docs/plugins/design.md": DOC,
            "mkdocs.yml": f"site_url: {SITE}\n",
        })
        check("site_url は通る", run(root).returncode == 0)

        print("index.md 形式のページも解決する")
        root = base / "index-form"
        build(root, {
            "docs/plugins/index.md": DOC,
            "CLAUDE.md": f"[設計]({SITE}plugins/#verify)\n",
        })
        check("<page>/index.md を見つける", run(root).returncode == 0)

        print("見出し行の id だけを数える")
        root = base / "prose-id"
        build(root, {
            # **本文に `{ #x }` と書いてあるだけ**のものを数えると、
            # 存在しないアンカーへのリンクを通してしまう。
            "docs/plugins/design.md": "# 設計\n\n書き方: `{ #ghost }`\n\n## 節 { #verify }\n",
            "CLAUDE.md": f"[設計]({SITE}plugins/design/#ghost)\n",
        })
        check("散文中の `{ #x }` を本物として数えない", run(root).returncode != 0)

        print("admonition のタイトルの id は数えない")
        root = base / "admonition"
        build(root, {
            # **#94 と #95 で 2 度踏んだ形。** admonition のタイトルに `{ #id }` を
            # 書いても id 属性は付かない。**拾ってしまうと、死んだリンクを通す。**
            "docs/plugins/design.md": '# 設計\n\n!!! note "注記 { #ghost }"\n    本文\n',
            "CLAUDE.md": f"[設計]({SITE}plugins/design/#ghost)\n",
        })
        check("admonition のタイトルを見出しとして数えない", run(root).returncode != 0)

        print("変異テスト（壊したのに緑なら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        helper = HELPER.read_text(encoding="utf-8")
        mutants = {
            "壊れたアンカーを報告しない": (
                source,
                helper.replace(
                    'problems.append(\n                f"リンク {url} のアンカー #{fragment} が "',
                    'pass\n            _unused = (\n                f"リンク {url} のアンカー #{fragment} が "'),
            ),
            "`plugins/` だけを見る": (
                source.replace('SUFFIXES = {".md", ".py", ".yml", ".yaml", ".json"}',
                               'SUFFIXES = {".md"}')
                      .replace("for path in sorted(root.rglob(\"*\")):",
                               "for path in sorted((root / 'plugins').rglob('*')):"),
                helper,
            ),
            "見出し以外の id も数える": (
                source,
                helper.replace(
                    'HEADING_ID = re.compile(r"^#{1,6}\\s.*\\{\\s*#([A-Za-z0-9_-]+)\\s*\\}\\s*$")',
                    'HEADING_ID = re.compile(r".*\\{\\s*#([A-Za-z0-9_-]+)\\s*\\}")'),
            ),
            "終了コードを 0 に固定する": (
                source.replace("        return 1\n\n    print(f\"公開サイト",
                               "        return 0\n\n    print(f\"公開サイト"),
                helper,
            ),
        }
        for name, (mut_source, mut_helper) in mutants.items():
            mroot = base / ("mutant-" + str(abs(hash(name)) % 10**6))
            build(mroot, {
                # **本文に `{ #missing }` を置く。** これが無いと「見出し以外の id も
                # 数える」変異を殺せない——変異体が拾うものが木に無いため。
                "docs/plugins/design.md": DOC + "\n書き方: `{ #missing }` のように書く。\n",
                "CLAUDE.md": f"[設計]({SITE}plugins/design/#missing)\n",
            }, script_text=mut_source)
            (mroot / "scripts" / HELPER.name).write_text(mut_helper, encoding="utf-8")
            # 正しい実装はこの入力で落ちる。変異体が落ちなければ殺せていない。
            check(f"変異を殺せる: {name}", run(mroot).returncode == 0)

        print("実環境を対象にしない歯止め")
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
    print("サイトリンク検査のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
