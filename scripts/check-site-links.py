#!/usr/bin/env python3
"""公開サイトへの絶対リンクが、リポジトリ**全体**で解決するかを検査する。

CI（`.github/workflows/docs.yml`）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-site-links.py

なぜ必要か（#97）: このリポジトリは「**ここには書かない。〇〇を正とする**」という形で
複製を 1 箇所に寄せている。**その形は指し先が実在して初めて意味を持つ。**

**指し先の実在を見る仕組みは、あるにはあった**——`check-plugin-versions.py` が
配布物（`plugins/` の `.md`）からのリンクを見ていた。**だが範囲がそこだけだった。**
実測では、リポジトリ全体の絶対リンク 30 件のうち**検査されていたのは 17 件で、
残り 13 件（`CLAUDE.md`・`scripts/`・`docs/`・`README.md`）は無検査**だった。

**無検査の範囲で実際に壊れた。** #95 で `scripts/token-metrics.py` と `CLAUDE.md` から
設計ドキュメントへリンクを張り、**その指し先の節に、指すと書いた内容が無かった**
（レビューが読んで見つけた）。同じ周で、**`{ #id }` を admonition のタイトルに置いて
アンカーが付かない**事故も起きている（#94 と合わせて 2 度）。

**この検査が守らないもの**——ここが穴である:

| 守らないもの | なぜ |
| --- | --- |
| **相対リンク** | `mkdocs build --strict` が `docs/` の中を見る。ただし**`docs/` の外から張った相対リンクは誰も見ていない** |
| **指し先に「指すと書いた内容」があるか** | 見るのは**アンカーが実在するか**だけ。**節の中身は読まない**——#95 で壊れたのはまさにここで、`#miscount` は実在したが `#75` の話が無かった |
| **リンクを張らずに文章で指すこと** | 「`SKILL.md` の手順 6 を正とする」のようにリンクが無ければ、拾いようがない |
| **外部サイトへのリンク** | このサイトの絶対 URL だけを見る |

つまりこれは「**指し先が実在する**」の検査であって、
「**指し先が正しい**」の検査ではない。

標準ライブラリのみ。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_links import broken_links  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

# 走査しない場所。**ビルド成果物と作業メモを見ない。**
SKIP_DIRS = {".git", "site", ".venv", "node_modules", "__pycache__", ".claude"}

# 走査する拡張子。**`.md` だけにしない**——#95 のリンクは `.py` の docstring にあった。
SUFFIXES = {".md", ".py", ".yml", ".yaml", ".json"}


def sources(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.suffix not in SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def main() -> int:
    if not DOCS_DIR.is_dir():
        print(f"ERROR: docs/ が見つからない: {DOCS_DIR}", file=sys.stderr)
        return 1

    failures = 0
    checked = 0
    for source in sources(REPO_ROOT):
        problems = broken_links(source, DOCS_DIR)
        checked += 1
        for problem in problems:
            print(f"ERROR: {source.relative_to(REPO_ROOT)}: {problem}", file=sys.stderr)
            failures += 1

    if failures:
        print("", file=sys.stderr)
        print("指し先が実在しないリンクがあります（#97）。", file=sys.stderr)
        return 1

    print(f"公開サイトへのリンクの検査: 問題なし（{checked} ファイルを走査）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
