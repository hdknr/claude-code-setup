#!/usr/bin/env python3
"""プラグインの中身を変えたのに version を上げていない差分を検出する。

usage: python3 scripts/check-version-bump.py <base-ref>

CI（.github/workflows/plugins.yml）が PR で呼ぶ。ローカルでも実行できる:

    python3 scripts/check-version-bump.py origin/main

なぜ必要か: version を据え置いたまま中身だけ変えると、インストール済みクライアントの
キャッシュが更新を検知できず旧内容を使い続ける（#33 で実際に発生し、#36 の作業中に観測された）。

判定の線引き:

- 挙動に影響する変更（skills/ commands/ agents/ plugin.json 等）で bump 無し → **エラー**
- README.md だけの変更で bump 無し → **警告**（typo 修正で CI を落とさない）
- 新規プラグイン（base に plugin.json が無い）→ 対象外

標準ライブラリのみ。git はサブプロセスで呼ぶ。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MANIFEST = ".claude-plugin/plugin.json"
# bump 無しでも警告に留めるファイル名（プラグインルート直下のみ）
WARN_ONLY = {"README.md"}

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


def version_at(ref: str, plugin: str) -> str | None:
    """指定 ref における plugin.json の version。無ければ None。"""
    code, out = git("show", f"{ref}:plugins/{plugin}/{MANIFEST}")
    if code != 0:
        return None
    try:
        return json.loads(out).get("version")
    except json.JSONDecodeError:
        return None


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
        base_version = version_at(base, plugin)
        if base_version is None:
            print(f"{plugin}: 新規プラグイン（base に plugin.json が無い）。対象外")
            continue

        head_version = current_version(plugin)
        if head_version is None:
            errors.append(f"{plugin}: plugins/{plugin}/{MANIFEST} が読めない")
            continue

        if head_version != base_version:
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
