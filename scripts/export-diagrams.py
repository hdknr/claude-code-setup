#!/usr/bin/env python3
"""drawio を書き出し、書き出しの前提の指紋を `diagrams/exports.json` に書き戻す。

    python3 scripts/export-diagrams.py                    # マニフェストにある全件
    python3 scripts/export-diagrams.py architecture        # 名前を指定（拡張子は不要）
    python3 scripts/export-diagrams.py diagrams/flowchart.drawio   # パスでも指定できる

なぜ 1 本のスクリプトにするか（#50）: `scripts/check-diagram-freshness.py` は
**書き出しの前提の指紋を記録として**持つ方式なので、「書き出す」と「指紋を更新する」の
**2 手になった瞬間に、片方だけ忘れる新しい失敗モードが生まれる**——忘れ物を 1 つ増やしただけになる。
書き出しの成功を待って指紋を書き戻すことで、**手で指紋を書く手順を残さない**。

**書き出しが失敗したら指紋は更新しない。** 指紋だけ進むと、検査は緑なのに書き出しは
古いままという、この方式で唯一検出できない状態を自分で作ることになる。失敗の判定は
**終了コード・出力の実在・mtime・中身が形式として読めること**の 4 つを全部見る——
どれか 1 つでも落とすと、そこから記録だけが進む（#50 の周の検証で実際に踏んだ:
終了コードを見ていなかったため、**壊れたファイルを吐いて落ちる CLI** を成功と誤判定した）。
さらに**失敗したら書き出しを元に戻す**ので、壊れたファイルが残ることもない。

draw.io CLI は GUI アプリに同梱されている。macOS の既定の場所を見るが、環境変数
`DRAWIO` で差し替えられる（Linux なら `DRAWIO=drawio`、`xvfb-run` 越しなら
`DRAWIO="xvfb-run -a drawio"` のように空白区切りでも渡せる）。

**このスクリプトは macOS でしか動作確認していない**（#50 の周）。他の OS では
`DRAWIO` を指定した上で、書き出し結果を目で確かめること。

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagram_manifest import (  # noqa: E402
    MANIFEST_NAME,
    RESERVED_KEYS,
    fingerprint,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = REPO_ROOT / "diagrams"
MANIFEST = DIAGRAMS_DIR / MANIFEST_NAME

DEFAULT_DRAWIO = "/Applications/draw.io.app/Contents/MacOS/draw.io"

# mtime の粒度が 1 秒のファイルシステムや、時刻がずれたネットワークマウントでは、
# 「書き出した直後の mtime」が開始時刻より前に見えることがある。1 秒だけ許す。
MTIME_TOLERANCE_SECONDS = 1


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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


def looks_like(output: Path) -> str | None:
    """書き出しが**その形式として読める**か。読めなければ理由を返す。

    終了コードと mtime だけでは、**壊れたファイル・空のファイルを吐いて落ちた**場合を
    弾けない。中身を軽く見て、明らかに書き出しになっていないものを落とす。
    """
    data = output.read_bytes()
    if not data:
        return "空のファイル"
    if output.suffix.lower() == ".png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "PNG のシグネチャが無い"
    elif b"<svg" not in data[:4096]:
        return "`<svg` が見つからない"
    return None


def export_one(key: str, entry: dict, command: list[str]) -> bool:
    """1 件書き出す。成功したかどうかを返す。

    **失敗したら、書き出しを元に戻す。** 壊れたファイルを吐いて落ちる CLI に既存の
    正しい書き出しを潰させると、記録は据え置かれても**書き出しは壊れたまま**になる。
    """
    source = REPO_ROOT / key
    output = REPO_ROOT / entry["output"]
    fmt = output.suffix.lstrip(".")

    cmd = [*command, "--export", "--format", fmt, "--output", str(output)]
    scale = entry.get("scale")
    if scale is not None:
        cmd += ["--scale", str(scale)]
    cmd.append(str(source))

    output.parent.mkdir(parents=True, exist_ok=True)
    previous = output.read_bytes() if output.is_file() else None

    def reject(reason: str, proc: subprocess.CompletedProcess[str] | None = None) -> bool:
        print(f"  失敗: {reason}")
        if proc is not None:
            detail = (proc.stdout + proc.stderr).strip()
            if detail:
                print(f"    {detail[-400:]}")
        if previous is None:
            output.unlink(missing_ok=True)
        else:
            output.write_bytes(previous)
        print(f"    {entry['output']} は書き出し前の状態に戻した")
        return False

    started = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        print(f"  失敗: draw.io CLI が見つからない（{command[0]}）。DRAWIO で指定する")
        return False
    except subprocess.TimeoutExpired:
        return reject("draw.io CLI がタイムアウトした")

    # **終了コードを見る。** これを落とすと、**書き出してから非ゼロで終了する**CLI
    # （部分書き込み後のクラッシュ等）を成功と誤判定し、記録だけが進む——この方式で
    # 唯一検出できない状態（記録は新しいのに書き出しは古い／壊れている）を自分で作ることになる。
    if proc.returncode != 0:
        return reject(f"draw.io CLI が非ゼロ終了した（rc={proc.returncode}）", proc)

    # **終了コードだけでも足りない。** GUI アプリ同梱の CLI は、書き出さずに 0 を返すことがある。
    if not output.is_file():
        return reject("書き出しが作られなかった（rc=0）", proc)
    if output.stat().st_mtime < started - MTIME_TOLERANCE_SECONDS:
        return reject("書き出しが更新されていない（rc=0）", proc)
    broken = looks_like(output)
    if broken is not None:
        return reject(f"書き出しが壊れている（{broken}）", proc)
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
        # **成功してから**指紋を進める。失敗した分は記録を据え置くので、
        # 次の check で「書き出していない」として落ちる。
        entry["fingerprint"] = fingerprint(REPO_ROOT / key, entry["output"], entry.get("scale"))

    save_manifest(manifest)

    if failed:
        print(f"\n{len(failed)} 件失敗（記録は据え置いた）: {', '.join(failed)}")
        return 1
    print(f"\n{len(targets)} 件書き出し、{rel(MANIFEST)} を更新した")
    print("python3 scripts/check-diagram-freshness.py で確認する")
    return 0


if __name__ == "__main__":
    sys.exit(main())
