#!/usr/bin/env python3
"""drawio を書き出し、そのソースのハッシュを `diagrams/exports.json` に書き戻す。

    python3 scripts/export-diagrams.py                    # マニフェストにある全件
    python3 scripts/export-diagrams.py architecture        # 名前を指定（拡張子は不要）
    python3 scripts/export-diagrams.py diagrams/flowchart.drawio   # パスでも指定できる

なぜ 1 本のスクリプトにするか（#50）: `scripts/check-diagram-freshness.py` は
**ソースのハッシュを書き出しの記録として**持つ方式なので、「書き出す」と「ハッシュを更新する」の
**2 手になった瞬間に、片方だけ忘れる新しい失敗モードが生まれる**——忘れ物を 1 つ増やしただけになる。
書き出しの成功を待ってハッシュを書き戻すことで、**手でハッシュを書く手順を残さない**。

**書き出しが失敗したらハッシュは更新しない。** ハッシュだけ進むと、検査は緑なのに書き出しは
古いままという、この方式で唯一検出できない状態を自分で作ることになる。

draw.io CLI は GUI アプリに同梱されている。macOS の既定の場所を見るが、環境変数
`DRAWIO` で差し替えられる（Linux なら `DRAWIO=drawio`、`xvfb-run` 越しなら
`DRAWIO="xvfb-run -a drawio"` のように空白区切りでも渡せる）。

**このスクリプトは macOS でしか動作確認していない**（#50 の周）。他の OS では
`DRAWIO` を指定した上で、書き出し結果を目で確かめること。

標準ライブラリのみ。
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = REPO_ROOT / "diagrams"
MANIFEST = DIAGRAMS_DIR / "exports.json"

DEFAULT_DRAWIO = "/Applications/draw.io.app/Contents/MacOS/draw.io"
RESERVED_KEYS = {"_comment"}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def drawio_command() -> list[str]:
    """draw.io CLI の起動コマンド。`DRAWIO` で差し替えられる。"""
    raw = os.environ.get("DRAWIO", DEFAULT_DRAWIO)
    return shlex.split(raw)


def load_manifest() -> dict:
    with MANIFEST.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_manifest(manifest: dict) -> None:
    """キーの並びを保ったまま書き戻す（差分を読めるようにするため）。"""
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    MANIFEST.write_text(text, encoding="utf-8")


def resolve_targets(manifest: dict, args: list[str]) -> list[str] | None:
    """引数をマニフェストのキーに解決する。解決できなければ None。"""
    declared = [key for key in manifest if key not in RESERVED_KEYS]

    malformed = [key for key in declared if not isinstance(manifest[key], dict)]
    if malformed:
        # 形の検証は check スクリプトの仕事。ここで落ちるより、そちらの診断に回す。
        print(f"エラー: エントリの形が不正: {', '.join(malformed)}")
        print("python3 scripts/check-diagram-freshness.py で診断する")
        return None

    if not args:
        # 全件モードでは `output: null` を黙って飛ばす（書き出さないと宣言済みなので）。
        return [key for key in declared if manifest[key].get("output") is not None]

    by_stem = {Path(key).stem: key for key in declared}
    targets: list[str] = []
    for arg in args:
        key = arg if arg in by_stem.values() else by_stem.get(Path(arg).stem)
        if key is None:
            print(f"エラー: {arg} は {rel(MANIFEST)} に無い。候補: {', '.join(sorted(by_stem))}")
            return None
        if manifest[key].get("output") is None:
            # 名指しされたときは黙って飛ばさない。宣言と要求が食い違っている。
            print(
                f"エラー: {key} は `output: null`（書き出さないと宣言されている）。"
                f"書き出すならまずマニフェストの宣言を直す"
            )
            return None
        if key not in targets:
            targets.append(key)
    return targets


def export_one(key: str, entry: dict, command: list[str]) -> bool:
    """1 件書き出す。成功したかどうかを返す。"""
    source = REPO_ROOT / key
    output = REPO_ROOT / entry["output"]
    fmt = output.suffix.lstrip(".")

    cmd = [*command, "--export", "--format", fmt, "--output", str(output)]
    scale = entry.get("scale")
    if scale is not None:
        cmd += ["--scale", str(scale)]
    cmd.append(str(source))

    started = time.time()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        print(f"  失敗: draw.io CLI が見つからない（{command[0]}）。DRAWIO で指定する")
        return False
    except subprocess.TimeoutExpired:
        print("  失敗: draw.io CLI がタイムアウトした")
        return False

    # **終了コードだけを信じない。** GUI アプリ同梱の CLI は、書き出さずに 0 を返すことがある。
    # 書き出しが「今回」更新されたことまで確かめる。
    if not output.is_file():
        print(f"  失敗: {entry['output']} が作られなかった（rc={proc.returncode}）")
        print(f"    {(proc.stdout + proc.stderr).strip()[-400:]}")
        return False
    if output.stat().st_mtime < started:
        print(f"  失敗: {entry['output']} が更新されていない（rc={proc.returncode}）")
        print(f"    {(proc.stdout + proc.stderr).strip()[-400:]}")
        return False
    return True


def main() -> int:
    manifest = load_manifest()
    targets = resolve_targets(manifest, sys.argv[1:])
    if targets is None:
        return 1
    if not targets:
        print("書き出す対象がない")
        return 0

    command = drawio_command()
    failed: list[str] = []
    for key in targets:
        entry = manifest[key]
        print(f"{key} -> {entry['output']}")
        if not export_one(key, entry, command):
            failed.append(key)
            continue
        # **成功してから**ハッシュを進める。失敗した分は記録を据え置くので、
        # 次の check で「書き出していない」として落ちる。
        entry["sha256"] = sha256_of(REPO_ROOT / key)

    save_manifest(manifest)

    if failed:
        print(f"\n{len(failed)} 件失敗（記録は据え置いた）: {', '.join(failed)}")
        return 1
    print(f"\n{len(targets)} 件書き出し、{rel(MANIFEST)} を更新した")
    print("python3 scripts/check-diagram-freshness.py で確認する")
    return 0


if __name__ == "__main__":
    sys.exit(main())
