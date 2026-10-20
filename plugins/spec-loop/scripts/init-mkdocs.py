#!/usr/bin/env python3
"""正本リポジトリに、MkDocs の雛形（`templates/mkdocs/`）を写す。

    python3 init-mkdocs.py [<正本リポジトリの根>] [--dry-run]

根を省くと今のディレクトリ。どこに何を置くかの決まりは `references/tree.md` の「ドキュメントのツール」を正とする。

- **`mkdocs.yml` か `mkdocs.yaml` が既にあれば、何も写さない**（プロジェクトの設定が先にある。MkDocs はどちらも読む）。
- `mkdocs.yml` は最後に写す——途中で書けずに止まっても、直して再実行すれば残りが写る。
- 無ければ、雛形のファイルのうち**行き先に無いものだけ**を写す。**在るファイルは 1 バイトも変えない**——
  `pyproject.toml`・`.gitignore` が在れば触らず、足りない依存・無視する行を出力で示す（足すかどうかは人が決める）。
- 行き先がシンボリックリンクなら（壊れていても）「在る」とみなす。書くときは排他的に作る（確かめた後に
  別の誰かが作っていても上書きしない）。
- `--dry-run` は何を写すかを示すだけで、何も書かない。
- 雛形の `gitignore` は `.gitignore` として写す（プラグインの中で本物の `.gitignore` として効かないように名前を変えてある）。

終了コード: 0 写した・写すものが無い ／ 2 根がディレクトリでない・雛形が読めない・書けない（行き先の親がファイルのときを含む）。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "mkdocs"
CONFIG = "mkdocs.yml"
# MkDocs が設定として読む名前（この順に探す）。どれかが在れば、プロジェクトの設定が先にある
CONFIG_NAMES = ("mkdocs.yml", "mkdocs.yaml")
# 雛形の中の名前 → 行き先の名前（書いていないものは同じ名前）
RENAMES = {"gitignore": ".gitignore"}
# pyproject.toml が在って写さなかったときに、無ければ示す依存
DEPENDENCIES = ("mkdocs", "mkdocs-material")


def template_files() -> list[tuple[Path, str]]:
    """(雛形のファイル, 根からの行き先) を名前の順に。ただし `mkdocs.yml` は最後に
    （途中で失敗したとき、「設定が在るので何も写さない」で再実行が止まらないように）。"""
    files = []
    for path in sorted(TEMPLATE.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(TEMPLATE).as_posix()
        files.append((path, RENAMES.get(rel, rel)))
    return sorted(files, key=lambda item: item[1] == CONFIG)


def missing_ignores(dest: Path, source: Path) -> list[str]:
    try:
        have = {line.strip() for line in dest.read_text(encoding="utf-8").splitlines()}
    except (OSError, UnicodeDecodeError):
        return []
    return [line for line in source.read_text(encoding="utf-8").splitlines() if line.strip() and line.strip() not in have]


def missing_dependencies(dest: Path) -> list[str]:
    try:
        content = dest.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return [name for name in DEPENDENCIES if f'"{name}' not in content and f"'{name}" not in content]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="正本リポジトリに MkDocs の雛形を写す（在るファイルは変えない）")
    parser.add_argument("root", nargs="?", default=".", help="正本リポジトリの根（既定は今のディレクトリ）")
    parser.add_argument("--dry-run", action="store_true", help="何を写すかを示すだけで、何も書かない")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"{root}: ディレクトリでない", file=sys.stderr)
        return 2
    try:
        files = template_files()
    except OSError as e:
        print(f"{TEMPLATE}: 雛形が読めない（{e.strerror}）", file=sys.stderr)
        return 2
    if not files:
        print(f"{TEMPLATE}: 雛形が無い", file=sys.stderr)
        return 2

    for name in CONFIG_NAMES:
        if os.path.lexists(root / name):
            print(f"{root / name} が既にある。何も写さない（プロジェクトの設定に従う）")
            return 0

    verb = "写す（--dry-run なので書かない）" if args.dry_run else "写した"
    wrote: list[str] = []
    kept: list[str] = []
    for source, rel in files:
        dest = root / rel
        if os.path.lexists(dest):
            kept.append(rel)
            continue
        if not args.dry_run:
            try:
                data = source.read_bytes()
                # 親の名前がファイル・壊れたリンクなら mkdir は FileExistsError を出す——下の「既にある」と混ぜない
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with dest.open("xb") as f:
                        f.write(data)
                except FileExistsError:
                    kept.append(rel)  # 確かめた後に別の誰かが作った
                    continue
            except OSError as e:
                print(f"{dest}: 書けない（{e.strerror}）。写したもの: {', '.join(wrote) or 'なし'}", file=sys.stderr)
                return 2
        wrote.append(rel)

    for rel in wrote:
        print(f"{verb}: {rel}")
    for rel in kept:
        print(f"既にあるので触らない: {rel}")
        if rel == ".gitignore":
            lines = missing_ignores(root / rel, TEMPLATE / "gitignore")
            if lines:
                print(f"  .gitignore に無い行（足すなら手で）: {' '.join(lines)}")
        elif rel == "pyproject.toml":
            names = missing_dependencies(root / rel)
            if names:
                print(f"  pyproject.toml に無い依存（足すなら手で。mkdocs は 2 未満に）: {' '.join(names)}")
    if not wrote:
        print("写すものは無かった")
    return 0


if __name__ == "__main__":
    sys.exit(main())
