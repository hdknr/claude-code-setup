#!/usr/bin/env python3
"""drawio を編集したのに書き出しを更新していない状態を検出する（`--check` 相当）。

CI（.github/workflows/docs.yml）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-diagram-freshness.py

なぜ必要か（#50）: このリポジトリは drawio を編集したら SVG／PNG を書き出し直す必要がある
（CLAUDE.md「図表の更新」）。しかし**書き出し忘れは差分を見ても気づけない**——書き出しは
差分に現れないので「変えていない」と見える。`makemigrations --check` に相当するもの、つまり
**再生成せずに乖離を検出して非ゼロ終了する手段**が無いことが、そもそも見落としの原因になる。

検証する内容:

1. マニフェスト（`diagrams/exports.json`）が読めること — 壊れていれば落ちる（fail-closed）。
   **キーの重複も弾く**（`json` の既定は後勝ちで、先のエントリが黙って消える）
2. 取りこぼし — `diagrams/` 以下にあるのにマニフェストに載っていない source。
   収集は**大文字小文字を区別せず、symlink のディレクトリも辿る**（`diagram_manifest` を参照）
3. 収集範囲の外 — `diagrams/` の外に置かれた drawio（置いた本人にも気づく機会が無い）
4. 死んだエントリ — マニフェストにあるのに実在しない source
5. 書き出しの実在 — `output` が指すファイルがあるか
6. **鮮度** — 記録された指紋が、いまの書き出しの前提（ソースの内容・`output`・`scale`）と一致するか
7. エントリの形 — 必須キーの欠落・**未知キー**・指紋の桁・scale の値・
   `output` の正規形と**実パスでの重複**（symlink や `./` で同じファイルを 2 度指せない）

**なぜバイト比較（再生成して `git diff --exit-code`）ではないか。** 実測（#50 の周）で、
書き出しのある 12 件を書き出し直したら **6 件だけがバイト一致**した。残りは**寸法は一致するのに
バイトが違う**（`architecture.svg` は 922x642 で一致して 453602B vs 453646B、
`mobile-remote-control.png` は 1646x763 で一致して 3 バイト差）。
**原因は 1 つに特定できていない**——drawio の版・環境・埋め込む資源のどれが効いているかは
確かめていない。確かめたのは「**同じソースから同じ引数で書き出してもバイトは一致しない**」
という事実だけで、それだけでバイト比較は偽陽性になると言える。
CI に draw.io CLI（+ xvfb）を入れても解決しないので、入れていない。

**この方式の限界を明示しておく。** 検出できるのは「前提を変えてマニフェストも触っていない」
場合である。**マニフェストの指紋だけ手で書き換えて実際には書き出さない**のは検出できない。
だから `scripts/export-diagrams.py` が**書き出しと指紋の更新を一手で**やる——手で指紋を
書く手順を残さないことが、この限界に対する実際の歯止めになる。

**未知キーもエラーにする。** `fingerprnt` のような綴り間違いを黙って無視すると、**検査が無言で
外れる**（鮮度を見ていないのに緑）。歯止めは「落として黙って免除する」形で破られる（#62）。

標準ライブラリのみで動かす。draw.io CLI は呼ばない（CI に GUI アプリを入れないため）。
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagram_manifest import (  # noqa: E402
    ALLOWED_SUFFIXES,
    MANIFEST_NAME,
    RESERVED_KEYS,
    SOURCE_SUFFIX,
    fingerprint,
    walk_drawio,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = REPO_ROOT / "diagrams"
MANIFEST = DIAGRAMS_DIR / MANIFEST_NAME

ALLOWED_KEYS = {"output", "scale", "fingerprint", "note"}
FINGERPRINT_RE = re.compile(r"\A[0-9a-f]{64}\Z")

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def rel(path: Path) -> str:
    """リポジトリ相対のパス表記。エラーメッセージをコピペで辿れるようにする。"""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """JSON のキーの重複を検出する。

    `json.load` の既定は**後勝ちで、先のエントリが黙って消える**。同じ source の
    エントリを 2 つ書いたときに片方が無言で無効になるのは、この歯止めが最も避けたい形
    （「落として黙って免除する」）なので、読む時点で弾く。
    """
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            fail(f"{rel(MANIFEST)} にキー {key!r} が 2 回ある（先に書いたほうが黙って消える）")
        seen.add(key)
    return dict(pairs)


def load_manifest() -> dict | None:
    """マニフェストを読む。読めなければ errors に積んで None を返す（fail-closed）。"""
    try:
        with MANIFEST.open(encoding="utf-8") as fh:
            data = json.load(fh, object_pairs_hook=no_duplicate_keys)
    except FileNotFoundError:
        fail(f"{rel(MANIFEST)} が存在しない（書き出しの宣言が無いと鮮度を検査できない）")
        return None
    except OSError as exc:
        # `diagrams/` がディレクトリでない等。`FileNotFoundError` だけを捕まえていると
        # ここが**素の例外で落ちる**——非ゼロで終わるので事故にはならないが、
        # 理由が読めない。fail-closed のまま理由を出す。
        fail(f"{rel(MANIFEST)} を読めない: {exc}")
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
    if not key:
        fail("マニフェストに空のキーがある")
        return None
    if key.startswith("/") or ".." in Path(key).parts:
        fail(f"マニフェストのキー {key!r} は不正（絶対パス・親参照は使えない）")
        return None
    if key != os.path.normpath(key):
        # `diagrams/./one.drawio` のような書き方を許すと、**同じ source を別表記で指せる**。
        # 収集側は正規形の名前で数えるので、別表記のキーは照合から外れて
        # 「実在するのに検査されない」状態を作る。正規形だけを受け付ける。
        fail(
            f"マニフェストのキー {key!r} が正規形でない"
            f"（`{os.path.normpath(key)}` と書く）"
        )
        return None
    path = REPO_ROOT / key
    if path.suffix.lower() != SOURCE_SUFFIX:
        fail(f"マニフェストのキー {key!r} が `.drawio` で終わっていない")
        return None
    try:
        path.relative_to(DIAGRAMS_DIR)
    except ValueError:
        fail(f"マニフェストのキー {key!r} が {rel(DIAGRAMS_DIR)}/ の外を指している")
        return None
    return path


def check_entry(key: str, entry: object, outputs_seen: dict[str, tuple[str, str]]) -> None:
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
        for forbidden in ("fingerprint", "scale"):
            if forbidden in entry:
                fail(f"{key} は `output: null` なのに `{forbidden}` を持っている")
        return

    if not isinstance(output, str) or not output:
        fail(f"{key} の `output` が文字列でない: {output!r}")
        return
    if output.startswith("/") or ".." in Path(output).parts:
        fail(f"{key} の `output` {output!r} は不正（絶対パス・親参照は使えない）")
        return
    if output != os.path.normpath(output):
        # `docs/images/./one.svg` のような書き方を許すと、**同じファイルを別表記で指せる**ので
        # 下の重複検出をすり抜ける。正規形だけを受け付ける。
        fail(
            f"{key} の `output` {output!r} が正規形でない"
            f"（`{os.path.normpath(output)}` と書く）"
        )
        return

    output_path = REPO_ROOT / output
    if output_path.suffix.lower() not in ALLOWED_SUFFIXES:
        fail(f"{key} の `output` の拡張子が {sorted(ALLOWED_SUFFIXES)} ではない: {output}")
    if not output_path.is_file():
        fail(f"{key} の書き出し {output} が存在しない")

    # **突き合わせは実パスで行う。** 文字列比較だと、片方を symlink にするだけで
    # 「同じファイルを 2 つの source が指す」状態をすり抜けられる。
    identity = os.path.realpath(output_path)
    if identity in outputs_seen:
        # 同じ出力を 2 つの source が指すと、片方を書き出しただけで両方が緑に見える。
        other, other_output = outputs_seen[identity]
        via = "" if other_output == output else f"（{other_output} と同じファイル）"
        fail(f"{key} と {other} が同じ書き出し {output}{via} を指している")
    else:
        outputs_seen[identity] = (key, output)

    scale = entry.get("scale")
    if "scale" in entry:
        if isinstance(scale, bool) or not isinstance(scale, (int, float)) or scale <= 0:
            fail(f"{key} の `scale` が正の数でない: {scale!r}")
            return

    if "fingerprint" not in entry:
        fail(f"{key} のエントリに `fingerprint` が無い（書き出し時点の前提の指紋）")
        return
    recorded = entry["fingerprint"]
    if not isinstance(recorded, str) or not FINGERPRINT_RE.fullmatch(recorded):
        fail(f"{key} の `fingerprint` が 64 桁の小文字 hex でない: {recorded!r}")
        return

    actual = fingerprint(REPO_ROOT / key, output, scale)
    if actual != recorded:
        # 指紋はソースの内容・`output`・`scale` をまとめたものなので、どれが変わっても落ちる。
        fail(
            f"{key} の書き出しの前提（ソースの内容・`output`・`scale`）が記録と違う"
            f"——{output} を書き出し直していない"
            f"（記録 {recorded[:12]}… / 実際 {actual[:12]}…）。"
            f"`python3 scripts/export-diagrams.py {Path(key).stem}` で書き出す"
        )


def check_sources_outside_diagrams(found_in_diagrams: set[str]) -> None:
    """`diagrams/` の外に置かれた drawio を見つける。

    マニフェストは `diagrams/` 以下だけを数え上げる。だから **`docs/` などに drawio を
    置くと、鮮度が一切見られない**——未登録エラーにもならないので、置いた本人にも
    気づく機会が無い。「収集範囲の外」は最も静かな抜け道なので、範囲の外を明示的に禁じる。
    """
    for path in walk_drawio(REPO_ROOT):
        name = rel(path)
        if name in found_in_diagrams:
            continue
        fail(
            f"{name} が {rel(DIAGRAMS_DIR)}/ の外にある"
            "（ここに置くと鮮度を検査できない。diagrams/ に移す）"
        )


def main() -> int:
    manifest = load_manifest()
    if manifest is None:
        report()
        return 1

    # `diagrams/` が無ければマニフェストも読めないので、ここに到達した時点で存在している
    # （`MANIFEST` は `DIAGRAMS_DIR` の中にある）。存在確認の分岐は**到達不能なので置かない**
    # ——テストできない分岐は、あとから「何も見ていない」に退化しても気づけない。

    # **レイアウトを列挙せず、全部拾ってから照合する。** 列挙で判定すると知らない形が残る
    # （#63 の周で SKILL.md の検査が同じ穴を繰り返した）。
    found = {rel(path) for path in walk_drawio(DIAGRAMS_DIR)}

    check_sources_outside_diagrams(found)

    declared = set(manifest) - RESERVED_KEYS
    for key in sorted(declared - found):
        path = resolve_source(key)
        if path is None:
            continue  # 理由は resolve_source が積んでいる
        if not path.is_file():
            fail(f"{key} がマニフェストにあるが実在しない（削除したならエントリも消す）")
        else:
            # **実在するのに収集できていない。** 何もしないと、そのエントリは
            # 鮮度の検査に一度も回らないまま緑になる（「落として黙って免除する」形）。
            # 現在の収集規則で到達できない置き方が残っていたら、ここで止める。
            fail(f"{key} は実在するのに収集できていない（収集規則から漏れている）")

    for key in sorted(found - declared):
        fail(
            f"{key} が {rel(MANIFEST)} に未登録"
            "（書き出すなら output を、書き出さないなら `output: null` と `note` を書く）"
        )

    checked = sorted(found & declared)
    outputs_seen: dict[str, tuple[str, str]] = {}
    for key in checked:
        check_entry(key, manifest[key], outputs_seen)

    report(checked=len(checked))
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
