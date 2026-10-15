#!/usr/bin/env python3
"""プラグインの中身を変えたのに version を上げていない差分（と、下げた差分）を検出する。

usage: python3 scripts/check-version-bump.py <base-ref>

CI（.github/workflows/plugins.yml）が PR で呼ぶ。ローカルでも実行できる:

    python3 scripts/check-version-bump.py origin/main

なぜ必要か: version を据え置いたまま中身だけ変えると、インストール済みクライアントの
キャッシュが更新を検知できず旧内容を使い続ける（#33 で実際に発生し、#36 の作業中に観測された）。

判定の線引き:

- **base の先端より版が下がった → エラー**（#253。「変わったか」ではなく「上がったか」を見る。
  作業中に別の PR が base の版を先に上げると、据え置いたブランチは**マージで版を下げる**。
  インストール済みクライアントは版の変化で更新を検知しているので、下げると更新が届かないおそれがある）
- **版を比較できない**（`X.Y.Z` の数字 3 つでない）→ **エラー**（黙って OK にしない）
- 挙動に影響する変更（skills/ commands/ agents/ plugin.json 等）で bump 無し → **エラー**
- README.md だけの変更で bump 無し → **警告**（typo 修正で CI を落とさない）
- 新規プラグイン（base に plugin.json が無い）→ 対象外

標準ライブラリのみ。git はサブプロセスで呼ぶ。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

MANIFEST = ".claude-plugin/plugin.json"
# bump 無しでも警告に留めるファイル名（プラグインルート直下のみ）
WARN_ONLY = {"README.md"}
# 比較できる版の形。prerelease は使っていないので受け付けない（比較不能としてエラー）。
# `\d` にしない——全角の「１」のような Unicode の数字にも当たり、int() も通してしまう
VERSION_RE = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")

errors: list[str] = []
warnings: list[str] = []


def git(*args: str) -> tuple[int, str]:
    """git を呼んで (returncode, stdout) を返す。stderr は捨てる。"""
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    return proc.returncode, proc.stdout


def changed_files(base: str) -> list[str]:
    code, out = git("diff", "--name-only", f"{base}...HEAD")
    if code != 0:
        print(f"git diff が失敗しました（base={base}）。fetch-depth を確認してください。")
        sys.exit(2)
    return [line for line in out.splitlines() if line.strip()]


def manifest_at(ref: str, plugin: str) -> str | None:
    """指定 ref における plugin.json の中身。ファイルが無ければ None。

    **「無い」と「在るが版が読めない」を分ける**——後者を新規プラグイン扱いにすると、
    版の欠落・壊れた JSON が黙って OK になる。
    """
    code, out = git("show", f"{ref}:plugins/{plugin}/{MANIFEST}")
    return out if code == 0 else None


def version_in(text: str) -> tuple[bool, object]:
    """plugin.json の中身から version を取る。(JSON として読めたか, version)。"""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False, None
    if not isinstance(data, dict):
        return False, None
    return True, data.get("version")


def parse_version(version: object) -> tuple[int, int, int] | None:
    """`X.Y.Z` を数値の組にする。比較できなければ None。

    **文字列のまま比べない**——`"1.38.10" < "1.38.9"` になる。
    """
    if not isinstance(version, str):
        return None
    match = VERSION_RE.fullmatch(version)
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def current_version(plugin: str) -> str | None:
    path = Path("plugins") / plugin / MANIFEST
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("version")
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    base = sys.argv[1]

    # プラグインごとに、触られたファイルを集める
    touched: dict[str, list[str]] = {}
    for path in changed_files(base):
        parts = path.split("/")
        if len(parts) < 2 or parts[0] != "plugins":
            continue
        touched.setdefault(parts[1], []).append("/".join(parts[2:]))

    if not touched:
        print("プラグイン配下に変更はありません。bump チェックはスキップします。")
        return 0

    for plugin, files in sorted(touched.items()):
        base_manifest = manifest_at(base, plugin)
        if base_manifest is None:
            print(f"{plugin}: 新規プラグイン（base に plugin.json が無い）。対象外")
            continue
        readable, base_version = version_in(base_manifest)
        if not readable:
            errors.append(f"{plugin}: base の plugins/{plugin}/{MANIFEST} が読めない")
            continue

        head_version = current_version(plugin)
        if head_version is None:
            errors.append(f"{plugin}: plugins/{plugin}/{MANIFEST} が読めない")
            continue

        base_key = parse_version(base_version)
        head_key = parse_version(head_version)
        if base_key is None or head_key is None:
            errors.append(
                f"{plugin}: version を比較できない（base={base_version!r} / "
                f"head={head_version!r}）。X.Y.Z の形で書く"
            )
            continue

        if head_key < base_key:
            errors.append(
                f"{plugin}: version が {base_version} -> {head_version} に下がっている。"
                f"base の先端を取り込み、{base_version} より上げる"
                f"（plugin.json / marketplace.json / SKILL.md 本文の 3 箇所）"
            )
            continue

        if head_key > base_key:
            print(f"{plugin}: version {base_version} -> {head_version}。OK")
            continue

        # bump が無い。挙動に影響する変更が含まれるかで重み付けする
        significant = [f for f in files if f not in WARN_ONLY]
        listing = ", ".join(sorted(files)[:5])
        if significant:
            errors.append(
                f"{plugin}: 中身を変えたのに version が {base_version} のまま "
                f"（変更: {listing}）。CLAUDE.md「プラグインの更新」のとおり "
                f"plugin.json / marketplace.json / SKILL.md 本文の 3 箇所を上げる"
            )
        else:
            warnings.append(
                f"{plugin}: {listing} のみの変更で version が {base_version} のまま。"
                "配布物なので、内容が変わったなら bump を検討する"
            )

    for message in warnings:
        print(f"::warning::{message}")
    for message in errors:
        print(f"::error::{message}")

    if errors:
        print(f"\nversion bump 漏れが {len(errors)} 件あります。")
        return 1
    print("\nversion bump のチェック: 問題なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
