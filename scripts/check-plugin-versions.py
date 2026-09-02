#!/usr/bin/env python3
"""マーケットプレイスカタログとプラグインの整合をチェックする。

CI（.github/workflows/plugins.yml）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-plugin-versions.py

検証する内容:

1. marketplace.json の構造 — 必須キーの有無、名前の重複、source の指す先が実在するか
2. version の一致 — marketplace.json のエントリと plugin.json が同じ値か
3. SKILL.md 本文の版表記 — `<!-- skill-version: X -->` が plugin.json と同じ値か
4. 取りこぼし — plugins/ にあるのにカタログに載っていないプラグイン

なぜ必要か: version を据え置いたまま中身だけ変えると、インストール済みクライアントの
キャッシュが更新を検知できず旧内容のスキルを使い続ける（#33 で実際に発生）。
片方の version だけ上げても同じことが起きるため、機械的に止める。

**ただし version bump だけでは届かない**（#63）。利用者のマーケットプレイスのクローンが
導入時のコミットで凍結していると、**カタログを読み直すまで version の変化自体が見えない**。
そこで SKILL.md の本文にも版を書き、**古いキャッシュが読まれたら版が目に入る**ようにした。
本文の版が plugin.json とずれると意味が無いので、ここで一致を強制する。
記載が無い場合も**エラーにする**（fail-closed）——「書いていないからスキップ」は、
書き忘れた瞬間にチェックが無言で外れるということ。

標準ライブラリのみで動かす。リモートスキーマは取得しない（ネットワーク依存で壊れるため、
ローカルで完結する構造検証で代替する）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = REPO_ROOT / "plugins"

REQUIRED_CATALOG_KEYS = ("name", "owner", "plugins")
REQUIRED_ENTRY_KEYS = ("name", "source", "version")

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(path: Path) -> dict | None:
    """JSON を読む。壊れていれば errors に積んで None を返す。"""
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        fail(f"{rel(path)} が存在しない")
    except json.JSONDecodeError as exc:
        fail(f"{rel(path)} が JSON として不正: {exc}")
    return None


def rel(path: Path) -> str:
    """リポジトリルートからの相対パスにして読みやすくする。"""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def check_catalog_structure(catalog: dict) -> list[dict]:
    """カタログの必須キーを見て、検査対象のエントリ一覧を返す。"""
    for key in REQUIRED_CATALOG_KEYS:
        if key not in catalog:
            fail(f"{rel(MARKETPLACE)} に必須キー '{key}' が無い")

    entries = catalog.get("plugins")
    if not isinstance(entries, list):
        fail(f"{rel(MARKETPLACE)} の 'plugins' が配列でない")
        return []

    seen: set[str] = set()
    valid: list[dict] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            fail(f"{rel(MARKETPLACE)} plugins[{index}] がオブジェクトでない")
            continue

        label = entry.get("name", f"plugins[{index}]")
        missing = [key for key in REQUIRED_ENTRY_KEYS if key not in entry]
        if missing:
            fail(f"{label}: marketplace.json に必須キーが無い: {', '.join(missing)}")
            continue

        if entry["name"] in seen:
            fail(f"{entry['name']}: marketplace.json にエントリが重複している")
            continue
        seen.add(entry["name"])
        valid.append(entry)

    return valid


def check_entry(entry: dict) -> str | None:
    """1 エントリを検査し、対応する plugins/ 配下のディレクトリ名を返す。"""
    name = entry["name"]
    source_dir = (REPO_ROOT / entry["source"]).resolve()

    if not source_dir.is_dir():
        fail(f"{name}: source '{entry['source']}' が指すディレクトリが無い")
        return None

    manifest_path = source_dir / ".claude-plugin" / "plugin.json"
    manifest = load_json(manifest_path)
    if manifest is None:
        return source_dir.name

    if manifest.get("name") != name:
        fail(
            f"{name}: plugin.json の name が '{manifest.get('name')}' で "
            f"marketplace.json の '{name}' と一致しない"
        )

    catalog_version = entry["version"]
    plugin_version = manifest.get("version")
    if plugin_version is None:
        fail(f"{name}: {rel(manifest_path)} に version が無い")
    else:
        check_skill_versions(name, source_dir, plugin_version)
    if plugin_version is not None and plugin_version != catalog_version:
        fail(
            f"{name}: version が一致しない — "
            f"marketplace.json={catalog_version} / plugin.json={plugin_version}。"
            "CLAUDE.md「プラグインの更新」のとおり 2 箇所を同じ値に揃える"
        )

    return source_dir.name


SKILL_VERSION_MARKER = "<!-- skill-version: "


def check_skill_versions(plugin: str, source_dir: Path, version: str) -> None:
    """そのプラグインの全 SKILL.md 本文に、plugin.json と同じ版が書かれているか。

    スキルを持たないプラグイン（`commands/` だけ等）は検査対象なし——それは正しい状態。
    スキルがあるのに版の記載が無ければ**エラー**にする（fail-closed）。
    """
    skills_dir = source_dir / "skills"
    if not skills_dir.is_dir():
        return
    for skill in sorted(skills_dir.glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        marked = [
            line for line in text.split("\n") if line.startswith(SKILL_VERSION_MARKER)
        ]
        if not marked:
            fail(
                f"{plugin}: {rel(skill)} の本文に版の記載が無い。"
                f"`{SKILL_VERSION_MARKER}{version} -->` を見出しの直後に置く"
                "（古いキャッシュが読まれたときに気づく唯一の手掛かり。#63）"
            )
            continue
        if len(marked) > 1:
            fail(f"{plugin}: {rel(skill)} に版の記載が {len(marked)} 個ある。1 つにする")
            continue
        found = marked[0][len(SKILL_VERSION_MARKER) :].split("-->")[0].strip()
        if found != version:
            fail(
                f"{plugin}: {rel(skill)} の版が {found} で plugin.json の {version} と一致しない。"
                "版を上げたら本文の記載も直す"
            )


def check_uncatalogued(catalogued: set[str]) -> None:
    """plugins/ にあるのにカタログに載っていないものを検出する。"""
    if not PLUGINS_DIR.is_dir():
        return
    for child in sorted(PLUGINS_DIR.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if not (child / ".claude-plugin" / "plugin.json").is_file():
            continue
        if child.name not in catalogued:
            fail(
                f"{child.name}: plugins/ に存在するが marketplace.json に載っていない"
                "（載せないなら意図を README に書く）"
            )


def main() -> int:
    catalog = load_json(MARKETPLACE)
    if catalog is None:
        report()
        return 1

    entries = check_catalog_structure(catalog)
    catalogued = {name for name in (check_entry(entry) for entry in entries) if name}
    check_uncatalogued(catalogued)

    report(checked=len(entries))
    return 1 if errors else 0


def report(checked: int = 0) -> None:
    if errors:
        print(f"プラグインの整合チェックで {len(errors)} 件の問題が見つかりました:\n")
        for message in errors:
            print(f"  - {message}")
        print("")
    else:
        print(f"プラグインの整合チェック: 問題なし（{checked} 件のエントリを検査）")


if __name__ == "__main__":
    sys.exit(main())
