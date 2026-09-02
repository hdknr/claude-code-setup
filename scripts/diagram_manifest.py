#!/usr/bin/env python3
"""`diagrams/exports.json` を読み書きする両方のスクリプトが共有する定義。

`check-diagram-freshness.py`（検査）と `export-diagrams.py`（書き出し）は、
**同じ指紋の式**と**同じ収集規則**を使う必要がある。片方だけ直すと、検査が緑なのに
書き出しは古い（またはその逆）状態が生まれる——このリポジトリで最も繰り返している
事故の形（#60・#62）がそのまま当てはまるので、式は 1 箇所にだけ置く。

標準ライブラリのみ。実行するものではない（import される）。
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

MANIFEST_NAME = "exports.json"

# 拾うのは `.drawio` だけ。`diagrams/icons/` の素材 SVG は drawio に base64 で
# 埋め込まれる素材で、書き出しの source ではない（拡張子で自然に除外される）。
SOURCE_SUFFIX = ".drawio"

# 書き出しとして受け付ける形式。
ALLOWED_SUFFIXES = {".svg", ".png"}

# JSON にコメントは書けないので、`_comment` だけをトップレベルの予約キーとして許す。
RESERVED_KEYS = {"_comment"}

# リポジトリ全体を走査するときに降りないディレクトリ。生成物・依存・履歴。
# **ドットで始まるディレクトリは全部飛ばす**——`.claude/worktrees/` には他の周の作業ツリーが
# 丸ごと入っており、そこの `diagrams/` を「diagrams/ の外にある」と誤検出してしまう。
SKIP_DIR_NAMES = {"site", "node_modules", "__pycache__"}


def walk_drawio(top: Path) -> list[Path]:
    """`top` 以下の `.drawio` を集める。大文字小文字を区別せず、symlink も辿る。

    `Path.rglob` を使わない理由が 2 つある。どちらも**黙って収集から落ちる**形:

    - `rglob("*.drawio")` は**大文字小文字を区別する**（macOS の大文字小文字を区別しない
      ファイルシステム上でも）。`UP.DRAWIO` は収集から丸ごと外れ、未登録エラーにもならない。
      CI は ext4 なので、git 上でも別ファイルとして共存できる。
    - Python 3.13 以降、`**` は**シンボリックリンクのディレクトリに再帰しない**
      （`diagrams/linked/` の中が落ちる）。

    symlink を辿るのでループを踏みうる。実パスで訪問済みを覚えて打ち切る。
    """
    found: list[Path] = []
    visited: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(top, followlinks=True):
        real = os.path.realpath(dirpath)
        if real in visited:
            dirnames[:] = []
            continue
        visited.add(real)
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")
        ]
        for name in filenames:
            if name.lower().endswith(SOURCE_SUFFIX):
                found.append(Path(dirpath) / name)
    return found


def fingerprint(source: Path, output: str, scale: object) -> str:
    """書き出しの**前提すべて**をまとめた指紋。

    **ソースの内容だけでは足りない。** 書き出しは `output`（どこに・どの形式で）と
    `scale`（どの倍率で）にも依存する。ソースのハッシュだけを記録していると、
    **マニフェストの `scale` を 2 → 4 に書き換えても指紋は変わらない**ので、
    検査は緑のまま書き出しは 2 倍で据え置かれる（#50 のレビューで指摘された経路）。
    `scale` がマニフェストにあるのは、まさにそれが成果物を変えるからである
    （`mobile-remote-control` は既定倍率だと 824x383、`--scale 2` で 1646x763）。

    区切りに `\\0` を挟むのは、隣り合う要素の境界を曖昧にしないため
    （`output` の末尾と `scale` の先頭がくっついて別の組と同じ列になるのを防ぐ）。
    """
    digest = hashlib.sha256()
    digest.update(source.read_bytes())
    digest.update(b"\0")
    digest.update(output.encode("utf-8"))
    digest.update(b"\0")
    # `None`（既定倍率）と `1` を別物として扱う。CLI に `--scale` を渡すかどうかが違う。
    digest.update(repr(scale).encode("utf-8"))
    return digest.hexdigest()
