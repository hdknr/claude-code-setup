#!/usr/bin/env python3
"""正本リポジトリに、MkDocs の雛形（`templates/mkdocs/`）を写す。

    python3 init-mkdocs.py [<正本リポジトリの根>] [--dry-run]

根を省くと今のディレクトリ。どこに何を置くかの決まりは `references/tree.md` の「ドキュメントのツール」を正とする。

- **`mkdocs.yml` か `mkdocs.yaml` が既にあれば、何も写さない**（プロジェクトの設定が先にある。MkDocs はどちらも読む）。
- `mkdocs.yml` は最後に写す——途中で書けずに止まっても、直して再実行すれば残りが写る。
- 無ければ、雛形のファイルのうち**行き先に無いものだけ**を写す。**在るファイルは 1 バイトも変えない**——
  `pyproject.toml`・`.gitignore` が在れば触らず、足りない依存・無視する行を出力で示す（足すかどうかは人が決める）。
- 行き先がシンボリックリンクなら（壊れていても）「在る」とみなす。書くときは排他的に作る（確かめた後に
  別の誰かが作っていても上書きしない）。一時ファイルに書き切ってからリンクで置くので、途中で書けなくても切れたファイルは残らない。
  リンクを作れないファイルシステム（FAT32 など）では行き先を排他的に作って直に書き、途中で書けなければそれを消す
  （消すのにも失敗したらそう出力する。消せなかったときと、プロセスが殺されたときは切れたファイルが残りうる）。
- `--dry-run` は何を写すかを示すだけで、何も書かない。
- 雛形の `gitignore` は `.gitignore` として写す（プラグインの中で本物の `.gitignore` として効かないように名前を変えてある）。

終了コード: 0 写した・写すものが無い ／ 2 根がディレクトリでない・雛形が読めない・書けない（行き先の親がファイルのときを含む）。
"""

from __future__ import annotations

import argparse
import errno
import os
import sys
import tempfile
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "mkdocs"
CONFIG = "mkdocs.yml"
# MkDocs が設定として読む名前（この順に探す）。どれかが在れば、プロジェクトの設定が先にある
CONFIG_NAMES = ("mkdocs.yml", "mkdocs.yaml")
# 雛形の中の名前 → 行き先の名前（書いていないものは同じ名前）
RENAMES = {"gitignore": ".gitignore"}
# pyproject.toml が在って写さなかったときに、無ければ示す依存
DEPENDENCIES = ("mkdocs", "mkdocs-material")
# os.link がこれで失敗したら、リンクを作れないファイルシステムとみなして直に書く（権限・容量の不足は含めない）
NO_LINK = {errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV, errno.EMLINK, errno.ENOSYS}
UMASK = os.umask(0)
os.umask(UMASK)


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


def place(dest: Path, data: bytes) -> bool:
    """`data` を `dest` に置く。既にあれば置かずに False。途中で書けなければ例外で、`dest` は作らない
    （一時ファイルに書き切ってからリンクで置く——切れたファイルが残ると、再実行が「既にある」と読んで直らない）。
    リンクを作れないファイルシステム（FAT32 など）では `dest` を排他的に作って直に書く（`place_directly`）。"""
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=f".{dest.name}.")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, 0o666 & ~UMASK)  # mkstemp は 0600 で作る——素の open で作ったのと同じ権限にする
        try:
            os.link(tmp, dest)  # 在れば失敗する（排他）
        except FileExistsError:
            return False
        except OSError as e:
            if e.errno not in NO_LINK:
                raise
            return place_directly(dest, data)
        return True
    finally:
        os.unlink(tmp)


def place_directly(dest: Path, data: bytes) -> bool:
    """リンクを作れないときの退路。`dest` を排他的に作って書き、途中で書けなければ自分が作った `dest` を消して例外。
    **消すのにも失敗したとき（そう出力する）と、プロセスが殺されたとき（SIGKILL・電源断）は切れたファイルが残りうる**
    ——リンクの経路には無い弱さ。"""
    try:
        f = dest.open("xb")
    except FileExistsError:
        return False
    try:
        with f:
            f.write(data)
    except BaseException:
        try:
            dest.unlink()  # 排他的に作ったのは自分なので、他人のファイルは消さない
        except OSError as e:
            print(f"{dest}: 書きかけを消せなかった（{e.strerror}）。消してから再実行する", file=sys.stderr)
        raise  # 消せても消せなくても、書けなかった理由のほうを上げる
    return True


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
                if not place(dest, data):
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
