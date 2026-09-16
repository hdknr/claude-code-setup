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
FENCES = REAL_REPO / "scripts" / "markdown_fences.py"
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
    # **依存モジュールも持っていく。** 忘れると ModuleNotFoundError で落ち、
    # 「落ちた」ことは分かるが理由が検査内容とずれる。
    shutil.copy(FENCES, root / "scripts" / FENCES.name)
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

        print("フェンスの中の { #id } は数えない")
        root = base / "fenced-id"
        build(root, {
            # **コード例の中の見出し風の行**。#97 の 1 パス目のレビューが、
            # docstring が「コード例は数えない」と書いているのに数えていたと指摘した。
            "docs/plugins/design.md": "# 設計\n\n```\n## 例 { #ghost }\n```\n\n## 本物 { #real }\n",
            "CLAUDE.md": f"[設計]({SITE}plugins/design/#ghost)\n",
        })
        check("フェンス内の id を本物として数えない", run(root).returncode != 0)

        print("attr_list の追加クラスを認識する")
        root = base / "attr-list"
        build(root, {
            # `{ #verify .no-toc }` は Material の定石。**`}` が直後に来ることを
            # 要求すると、正しいアンカーを「無い」と言って落ちる**（誤検出）。
            "docs/plugins/design.md": "# 設計\n\n## 節 { #verify .no-toc }\n",
            "CLAUDE.md": f"[設計]({SITE}plugins/design/#verify)\n",
        })
        check("クラス付きの id を認識する", run(root).returncode == 0)

        print("文末の約物を URL に含めない")
        root = base / "trailing"
        build(root, {
            "docs/plugins/design.md": DOC,
            # ASCII の `.` は**境界にできない**（ドメインにもパスにも出る）。
            # **末尾からだけ削る**。
            "CLAUDE.md": f"See {SITE}plugins/design/#verify.\n"
                         f"Also {SITE}plugins/design/#verify, and more\n",
        })
        check("末尾のピリオドとカンマで誤検出しない", run(root).returncode == 0)

        print("読めないファイルを黙って飛ばさない")
        root = base / "unreadable"
        build(root, {"docs/plugins/design.md": DOC})
        # 復号できないバイト列。**壊れたリンクを含むのに「問題なし」で通っていた。**
        (root / "CLAUDE.md").write_bytes(
            f"[設計]({SITE}plugins/design/#missing)\n".encode() + b"\xff\xfe\n")
        proc = run(root)
        check("読めないファイルで落ちる", proc.returncode != 0)
        check("読めなかったことを理由に出す", "読めなかった" in proc.stderr)

        print("指し先のページが読めないとき")
        root = base / "bad-target"
        build(root, {"CLAUDE.md": f"[設計]({SITE}plugins/design/#verify)\n"})
        (root / "docs" / "plugins").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "plugins" / "design.md").write_bytes(b"# \xff\xfe\n")
        proc = run(root)
        check("トレースバックで止まらない", "Traceback" not in proc.stderr)
        check("読めないページを理由として出す", proc.returncode != 0)

        print(".claude/commands は見る（追跡された配布物）")
        root = base / "claude-commands"
        build(root, {
            "docs/plugins/design.md": DOC,
            ".claude/commands/release.md": f"[設計]({SITE}plugins/design/#missing)\n",
        })
        check(".claude/commands/ のリンクも見る", run(root).returncode != 0)

        print(".claude/plans と .claude/worktrees は見ない（作業メモ）")
        root = base / "claude-plans"
        build(root, {
            "docs/plugins/design.md": DOC,
            ".claude/plans/issue-1.md": f"[設計]({SITE}plugins/design/#missing)\n",
            ".claude/worktrees/x/CLAUDE.md": f"[設計]({SITE}plugins/design/#missing)\n",
        })
        check("作業メモは見ない", run(root).returncode == 0)

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
                    'HEADING_ID = re.compile(r"^#{1,6}\\s.*\\{\\s*#([A-Za-z0-9_-]+)(?:\\s[^}]*)?\\}\\s*$")',
                    'HEADING_ID = re.compile(r".*\\{\\s*#([A-Za-z0-9_-]+)(?:\\s[^}]*)?\\}")'),
            ),
            "フェンスを落とさない": (
                source,
                helper.replace("for line in strip_fences(text).split",
                               "for line in text.split"),
            ),
            "末尾の約物を落とさない": (
                source,
                helper.replace(".rstrip(TRAILING_PUNCT)", ""),
            ),
            "読めないファイルを黙って飛ばす": (
                source,
                helper.replace(
                    'return [f"ファイルを読めなかったので検査できていない（{type(exc).__name__}）"]',
                    "return []"),
            ),
            "attr_list のクラスを認識しない": (
                source,
                helper.replace(
                    'HEADING_ID = re.compile(r"^#{1,6}\\s.*\\{\\s*#([A-Za-z0-9_-]+)(?:\\s[^}]*)?\\}\\s*$")',
                    'HEADING_ID = re.compile(r"^#{1,6}\\s.*\\{\\s*#([A-Za-z0-9_-]+)\\s*\\}\\s*$")'),
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
                # **変異が触るデータを全部置く。** 木に該当が無い変異は、実装が正しく
                # なくても生き残る（#95 で 26 変異中 15 件が生存した）。
                "docs/plugins/design.md": (
                    DOC
                    # 見出し以外の id（「見出し以外も数える」変異用）
                    + "\n書き方: `{ #missing }` のように書く。\n"
                    # フェンス内の id（「フェンスを落とさない」変異用）
                    + "\n```\n## 例 { #fenced }\n```\n"
                    # クラス付きの id（「attr_list を認識しない」変異用）
                    + "\n## 別の節 { #classed .no-toc }\n"
                ),
                "CLAUDE.md": (
                    # **本文の id へのリンク**——「見出し以外も数える」変異はこれを
                    # 通してしまう（正しい実装は落とす）。
                    f"[設計]({SITE}plugins/design/#missing)\n"
                    # **フェンス内の id へのリンク**——「フェンスを落とさない」変異は
                    # これを通してしまう。
                    f"[例]({SITE}plugins/design/#fenced)\n"
                    # 末尾の約物（「約物を落とさない」変異用）
                    f"See {SITE}plugins/design/#real.\n"
                    # クラス付きへのリンク
                    f"[別]({SITE}plugins/design/#classed)\n"
                ),
            }, script_text=mut_source)
            # 読めないファイル（「黙って飛ばす」変異用）。**正しい実装はこれで落ちる。**
            (mroot / "broken.md").write_bytes(
                f"[設計]({SITE}plugins/design/#missing)\n".encode() + b"\xff\xfe\n")
            (mroot / "scripts" / HELPER.name).write_text(mut_helper, encoding="utf-8")
            # **終了コードだけを見ない。** 木にいくつも壊れた入力を置いてあるので、
            # 正しい実装も変異体もどちらも落ちる。**出力を比べる**——変異が挙動を
            # 変えていれば、報告されるリンクの集合が変わる（#95 で学んだ形）。
            build(croot := (mroot.parent / (mroot.name + "-control")), {}, script_text=None)
            shutil.copytree(mroot, croot, dirs_exist_ok=True)
            (croot / "scripts" / SCRIPT.name).write_text(
                SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
            (croot / "scripts" / HELPER.name).write_text(
                HELPER.read_text(encoding="utf-8"), encoding="utf-8")
            correct, mutated = run(croot), run(mroot)
            same = (correct.returncode == mutated.returncode
                    and sorted(correct.stderr.split("\n")) == sorted(mutated.stderr.split("\n")))
            check(f"変異を殺せる: {name}", not same)

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
