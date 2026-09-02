#!/usr/bin/env python3
"""drawio を編集したのに書き出しを更新していない状態を検出する（`--check` 相当）。

CI（.github/workflows/docs.yml）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-diagram-freshness.py

なぜ必要か（#50）: このリポジトリは drawio を編集したら SVG／PNG を書き出し直す必要がある
（CLAUDE.md「図表の更新」）。しかし**書き出し忘れは差分を見ても気づけない**——書き出しは
差分に現れないので「変えていない」と見える。`makemigrations --check` に相当するもの、つまり
**再生成せずに乖離を検出して非ゼロ終了する手段**が無いことが、そもそも見落としの原因になる。

検証する内容:

1. マニフェスト（`diagrams/exports.json`）が読めること — 壊れていれば落ちる（fail-closed）
2. 取りこぼし — `diagrams/**/*.drawio` にあるのにマニフェストに載っていない source
3. 死んだエントリ — マニフェストにあるのに実在しない source
4. 書き出しの実在 — `output` が指すファイルがあるか
5. **鮮度** — 記録された sha256 が、いまの source の sha256 と一致するか
6. エントリの形 — 必須キーの欠落・**未知キー**・sha256 の桁・scale の値・`output` の重複

**なぜバイト比較（再生成して `git diff --exit-code`）ではないか。** 実測（#50 の周）で、
13 件を書き出し直したら **6 件だけがバイト一致**した。残りは**寸法は一致するがバイトが数十だけ
違う**（例: `architecture.svg` は 922x642 で一致、453602B vs 453646B）。2026-02 に書き出した分は
古い drawio 版で作られており、埋め込みフォントのサブセットが変わっている。
つまりバイト比較は**偽陽性になる**。CI に draw.io CLI（+ xvfb）を入れても解決しない。
そこで**ソースのハッシュを書き出しの記録として持つ**方式にした。

**この方式の限界を明示しておく。** 検出できるのは「drawio を編集してマニフェストも触っていない」
場合である。**マニフェストのハッシュだけ手で書き換えて実際には書き出さない**のは検出できない。
だから `scripts/export-diagrams.py` が**書き出しとハッシュ更新を一手で**やる——手でハッシュを
書く手順を残さないことが、この限界に対する実際の歯止めになる。

**未知キーもエラーにする。** `sha265` のような綴り間違いを黙って無視すると、**検査が無言で
外れる**（鮮度を見ていないのに緑）。歯止めは「落として黙って免除する」形で破られる（#62）。

標準ライブラリのみで動かす。draw.io CLI は呼ばない（CI に GUI アプリを入れないため）。
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = REPO_ROOT / "diagrams"
MANIFEST = DIAGRAMS_DIR / "exports.json"

# `diagrams/icons/` はブランドアイコンの素材（SVG）で、drawio に base64 で埋め込まれている。
# source ではないので、拾うのは `*.drawio` だけにする（拡張子で自然に除外される）。
SOURCE_GLOB = "*.drawio"

ALLOWED_KEYS = {"output", "scale", "sha256", "note"}
ALLOWED_SUFFIXES = {".svg", ".png"}
SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")

# JSON にコメントは書けないので、`_comment` だけをトップレベルの予約キーとして許す。
# **これ以外の非 `.drawio` キーはエラーにする**——`diagrams/foo.drawi` のような綴り間違いが
# 「未登録の source」ではなく「余分なキー」として現れたときに気づけるようにする。
RESERVED_KEYS = {"_comment"}

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def rel(path: Path) -> str:
    """リポジトリ相対のパス表記。エラーメッセージをコピペで辿れるようにする。"""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict | None:
    """マニフェストを読む。読めなければ errors に積んで None を返す（fail-closed）。"""
    try:
        with MANIFEST.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        fail(f"{rel(MANIFEST)} が存在しない（書き出しの宣言が無いと鮮度を検査できない）")
        return None
    except json.JSONDecodeError as exc:
        fail(f"{rel(MANIFEST)} が JSON として不正: {exc}")
        return None
    if not isinstance(data, dict):
        fail(f"{rel(MANIFEST)} のトップレベルはオブジェクトである必要がある")
        return None
    return data


def resolve_source(key: str) -> Path | None:
    """マニフェストのキー（リポジトリ相対の source パス）を検証して絶対パスにする。"""
    if not isinstance(key, str) or not key:
        fail(f"マニフェストのキーが文字列でない: {key!r}")
        return None
    if key.startswith("/") or ".." in Path(key).parts:
        fail(f"マニフェストのキー {key!r} は不正（絶対パス・親参照は使えない）")
        return None
    path = REPO_ROOT / key
    if path.suffix != ".drawio":
        fail(f"マニフェストのキー {key!r} が `.drawio` で終わっていない")
        return None
    try:
        path.relative_to(DIAGRAMS_DIR)
    except ValueError:
        fail(f"マニフェストのキー {key!r} が {rel(DIAGRAMS_DIR)}/ の外を指している")
        return None
    return path


def check_entry(key: str, entry: object, outputs_seen: dict[str, str]) -> None:
    """1 エントリを検証する。source の実在は呼び出し側が確認済み。"""
    if not isinstance(entry, dict):
        fail(f"{key} のエントリがオブジェクトでない")
        return

    unknown = sorted(set(entry) - ALLOWED_KEYS)
    if unknown:
        # 綴り間違いを黙って無視すると、鮮度を見ていないのに緑になる。
        fail(f"{key} のエントリに未知のキー {unknown}（使えるのは {sorted(ALLOWED_KEYS)}）")

    if "output" not in entry:
        fail(f"{key} のエントリに `output` が無い（書き出さないなら `output: null` と書く）")
        return

    output = entry["output"]

    if output is None:
        # 「書き出しが無い」を**宣言された状態**にする。黙って空にしておくと
        # 「書き出し忘れ」と区別できない。
        if not entry.get("note"):
            fail(f"{key} は `output: null` だが `note` が無い（書き出さない理由を書く）")
        for forbidden in ("sha256", "scale"):
            if forbidden in entry:
                fail(f"{key} は `output: null` なのに `{forbidden}` を持っている")
        return

    if not isinstance(output, str) or not output:
        fail(f"{key} の `output` が文字列でない: {output!r}")
        return
    if output.startswith("/") or ".." in Path(output).parts:
        fail(f"{key} の `output` {output!r} は不正（絶対パス・親参照は使えない）")
        return

    output_path = REPO_ROOT / output
    if output_path.suffix not in ALLOWED_SUFFIXES:
        fail(f"{key} の `output` の拡張子が {sorted(ALLOWED_SUFFIXES)} ではない: {output}")
    if not output_path.is_file():
        fail(f"{key} の書き出し {output} が存在しない")

    if output in outputs_seen:
        # 同じ出力を 2 つの source が指すと、片方を書き出しただけで両方が緑に見える。
        fail(f"{key} と {outputs_seen[output]} が同じ書き出し {output} を指している")
    else:
        outputs_seen[output] = key

    if "scale" in entry:
        scale = entry["scale"]
        if isinstance(scale, bool) or not isinstance(scale, (int, float)) or scale <= 0:
            fail(f"{key} の `scale` が正の数でない: {scale!r}")

    if "sha256" not in entry:
        fail(f"{key} のエントリに `sha256` が無い（書き出し時点の source のハッシュ）")
        return
    recorded = entry["sha256"]
    if not isinstance(recorded, str) or not SHA256_RE.fullmatch(recorded):
        fail(f"{key} の `sha256` が 64 桁の小文字 hex でない: {recorded!r}")
        return

    actual = sha256_of(REPO_ROOT / key)
    if actual != recorded:
        fail(
            f"{key} を編集して {output} を書き出し直していない"
            f"（記録 {recorded[:12]}… / 実際 {actual[:12]}…）。"
            f"`python3 scripts/export-diagrams.py {Path(key).stem}` で書き出す"
        )


def main() -> int:
    manifest = load_manifest()
    if manifest is None:
        report()
        return 1

    if not DIAGRAMS_DIR.is_dir():
        fail(f"{rel(DIAGRAMS_DIR)} が存在しない")
        report()
        return 1

    # **レイアウトを列挙せず、全部拾ってから照合する。** 列挙で判定すると知らない形が残る
    # （#63 の周で SKILL.md の検査が同じ穴を繰り返した）。
    found = {rel(path) for path in DIAGRAMS_DIR.rglob(SOURCE_GLOB) if path.is_file()}

    declared = set(manifest) - RESERVED_KEYS
    for key in sorted(declared - found):
        path = resolve_source(key)
        if path is not None and not path.is_file():
            fail(f"{key} がマニフェストにあるが実在しない（削除したならエントリも消す）")

    for key in sorted(found - declared):
        fail(
            f"{key} が {rel(MANIFEST)} に未登録"
            "（書き出すなら output を、書き出さないなら `output: null` と `note` を書く）"
        )

    outputs_seen: dict[str, str] = {}
    for key in sorted(found & declared):
        check_entry(key, manifest[key], outputs_seen)

    report(checked=len(found & declared))
    return 1 if errors else 0


def report(checked: int = 0) -> None:
    if errors:
        print(f"図の鮮度チェックで {len(errors)} 件の問題が見つかりました:\n")
        for message in errors:
            print(f"  - {message}")
        print("")
    else:
        print(f"図の鮮度チェック: 問題なし（{checked} 件の drawio を検査）")


if __name__ == "__main__":
    sys.exit(main())
