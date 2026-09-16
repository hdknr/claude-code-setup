#!/usr/bin/env python3
"""公開サイトへの絶対リンクが、リポジトリ**全体**で解決するかを検査する。

CI（`.github/workflows/docs.yml`）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-site-links.py

なぜ必要か（#97）: このリポジトリは「**ここには書かない。〇〇を正とする**」という形で
複製を 1 箇所に寄せている。**その形は指し先が実在して初めて意味を持つ。**

**指し先の実在を見る仕組みは、あるにはあった**——`check-plugin-versions.py` が
配布物（`plugins/` の `.md`）からのリンクを見ていた。**だが範囲がそこだけだった。**
`CLAUDE.md` と `scripts/` の docstring から張ったリンクは、**誰も見ていなかった**。

（**何件が無検査だったかをここに書かない。** 一度書いたが、**書いた時点の数が
実装の途中の状態を指しており、同じコミットの中で再現しなくなっていた**
——#97 の 1 パス目のレビューが数え直して見つけた。**数えたければ走らせること。**）

**無検査の範囲で実際に壊れた。** #95 で `scripts/token-metrics.py` と `CLAUDE.md` から
設計ドキュメントへリンクを張り、**その指し先の節に、指すと書いた内容が無かった**
（レビューが読んで見つけた）。同じ周で、**`{ #id }` を admonition のタイトルに置いて
アンカーが付かない**事故も起きている（#94 と合わせて 2 度）。

**この検査が守らないもの**——ここが穴である:

| 守らないもの | なぜ |
| --- | --- |
| **相対リンク** | `mkdocs build --strict` が `docs/` の中を見る。ただし**`docs/` の外から張った相対リンクは誰も見ていない** |
| **走査する拡張子の外** | 見るのは `SUFFIXES` に挙げた拡張子だけ。**「リポジトリ全体」と書いてあっても、拡張子の無いファイルや挙げていない形式は見ていない**（#97 の 1 パス目で `.sh` と `.toml` の抜けを指摘された） |
| **作業メモ** | `.claude/plans/` と `.claude/worktrees/` は見ない（どちらも gitignore 済み） |
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
#
# **`.claude/` を丸ごと外さない。** `.claude/commands/` は**追跡されている配布物**で、
# そこにも公開ページへのリンクが書かれうる。外すのは**作業メモと worktree だけ**
# （どちらも gitignore 済み）。**最初は `.claude/` ごと外していた**
# ——#97 の 1 パス目のレビューが、`.claude/commands/release.md` が無検査だと指摘した。
SKIP_DIRS = {".git", "site", ".venv", "node_modules", "__pycache__"}
SKIP_PATHS = (".claude/plans", ".claude/worktrees")

# 走査する拡張子。**`.md` だけにしない**——#95 のリンクは `.py` の docstring にあった。
# **`.sh` と `.toml` も見る**（配布するスクリプトと設定にも書ける）。
SUFFIXES = {".md", ".py", ".yml", ".yaml", ".json", ".sh", ".toml", ".txt"}


def sources(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.suffix not in SUFFIXES:
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.as_posix().startswith(SKIP_PATHS):
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
