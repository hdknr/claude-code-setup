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
from collections.abc import Callable
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
#
# **どの名前も、飛ばす理由が個別にある。** 「ドットで始まるものは全部」のような広い規則は
# 使わない——`.github/` や `.claude-plugin/` は**追跡されている**ので、そこに置かれた drawio は
# 報告されるべきである（広い規則にしていたときは報告されなかった）。
SKIP_DIR_NAMES = {
    ".git",  # 履歴。中に drawio 状のオブジェクトがあっても source ではない
    ".venv",  # 依存
    "site",  # mkdocs のビルド出力
    "node_modules",  # 依存
    "__pycache__",  # 生成物
}

# `top` からの相対パスで飛ばすもの。名前だけでは狙い撃ちできないもの。
SKIP_REL_PATHS = {
    # 他の周の作業ツリーが丸ごと入っている。そこの `diagrams/` を
    # 「diagrams/ の外にある」と誤検出してしまう（gitignore 済みでもある）。
    os.path.join(".claude", "worktrees"),
}


def walk_drawio(
    top: Path,
    *,
    skip_noise: bool = False,
    on_error: Callable[[OSError], None] | None = None,
) -> list[Path]:
    """`top` 以下の `.drawio` を集める。大文字小文字を区別せず、symlink も辿る。

    `Path.rglob` を使わない理由が 2 つある。どちらも**黙って収集から落ちる**形:

    - `rglob("*.drawio")` は**大文字小文字を区別する**（macOS の大文字小文字を区別しない
      ファイルシステム上でも）。`UP.DRAWIO` は収集から丸ごと外れ、未登録エラーにもならない。
      CI は ext4 なので、git 上でも別ファイルとして共存できる。
    - Python 3.13 以降、`**` は**シンボリックリンクのディレクトリに再帰しない**
      （`diagrams/linked/` の中が落ちる）。

    symlink を辿るのでループを踏みうる。実パスで訪問済みを覚えて打ち切る。

    `skip_noise` は**リポジトリ全体を走査するときだけ** True にする。
    **`diagrams/` の中では何も飛ばさない**——飛ばした場所は「収集されず、範囲の外としても
    報告されない」二重の死角になる（`diagrams/node_modules/x.drawio` が実際にそうだった）。
    守りたいディレクトリの中に、見ない場所を作ってはならない。

    `on_error` を渡さないと、**一覧できないディレクトリは黙って収集から落ちる**
    （`os.walk` の既定は例外を捨てる）。呼び出し側は必ず渡して、エラーとして報告すること。
    """
    found: list[Path] = []
    visited: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(top, followlinks=True, onerror=on_error):
        real = os.path.realpath(dirpath)
        if real in visited:
            dirnames[:] = []
            continue
        visited.add(real)
        if skip_noise:
            dirnames[:] = [
                d
                for d in dirnames
                if d not in SKIP_DIR_NAMES
                and os.path.relpath(os.path.join(dirpath, d), top) not in SKIP_REL_PATHS
            ]
        for name in filenames:
            if name.lower().endswith(SOURCE_SUFFIX):
                found.append(Path(dirpath) / name)
    return found


def normalize_scale(scale: object) -> object:
    """`2` と `2.0` を同じ状態にする。

    指紋にも `--scale` の引数にも**同じ正規化を通す**。通していないと、マニフェストの
    `"scale": 2` を `2.0` と書き換えただけで（書き出しは 1 ビットも変わらないのに）
    「書き出し直していない」と報告される。安全側の誤検知ではあるが、**診断が嘘になる**し、
    意味の無い書き出しを強いる。
    """
    if isinstance(scale, float) and scale.is_integer():
        return int(scale)
    return scale


def fingerprint(source: Path, output: str, scale: object, output_file: Path) -> str:
    """書き出しの**前提と結果**をまとめた指紋。4 つを混ぜる。

    | 混ぜるもの | これが無いと何が見えなくなるか |
    | --- | --- |
    | ソースの内容 | 図を編集して書き出し忘れた（本来の目的） |
    | `output`（パス文字列） | 書き出し先を別の実在ファイルに向け替えた |
    | `scale` | **マニフェストの倍率だけ書き換えた**（2 → 4 でも指紋が変わらない） |
    | **書き出しの内容** | **書き出しそのものが壊れた・書き換えられた** |

    `scale` がマニフェストにあるのは、まさにそれが成果物を変えるからである
    （`mobile-remote-control` は既定倍率だと 824x383、`--scale 2` で 1646x763）。

    **書き出しの内容を混ぜるのが要点。** 前提だけを記録していると、`output` の中身が
    壊れても（悪いマージ、ディスク障害、書き出しの途中でのクラッシュ）検査は緑のままになる
    ——マニフェストを 1 文字も触る必要がないので、「指紋を手で書き換えない」という歯止めも
    効かない。#50 の 2 パス目の検証で、正しい SVG を無関係なゴミで上書きしても
    「問題なし」と出ることが実証された。**「鮮度」は前提と結果の対応であって、前提だけではない。**

    区切りに `\\0` を挟むのは、隣り合う要素の境界を曖昧にしないため
    （`output` の末尾と `scale` の先頭がくっついて別の組と同じ列になるのを防ぐ）。
    """
    digest = hashlib.sha256()
    digest.update(source.read_bytes())
    digest.update(b"\0")
    digest.update(output.encode("utf-8"))
    digest.update(b"\0")
    # `None`（既定倍率）と `1` は別物として扱う。CLI に `--scale` を渡すかどうかが違う。
    # `2` と `2.0` は `normalize_scale` で同じにしてある（JSON の書き方の差で
    # 意味の無い書き出しを強いないため）。
    digest.update(repr(normalize_scale(scale)).encode("utf-8"))
    digest.update(b"\0")
    digest.update(output_file.read_bytes())
    return digest.hexdigest()
