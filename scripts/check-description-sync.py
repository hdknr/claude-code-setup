#!/usr/bin/env python3
"""プラグインの description を「片側だけ」直した差分を検出する。

usage: python3 scripts/check-description-sync.py <base-ref>

CI（.github/workflows/plugins.yml）が PR で呼ぶ。ローカルでも実行できる:

    python3 scripts/check-description-sync.py origin/main

なぜ必要か（#62）: プラグインの description は 3 箇所に複製されている。

    1. .claude-plugin/marketplace.json      — カタログ
    2. plugins/<name>/.claude-plugin/plugin.json — マニフェスト
    3. plugins/<name>/skills/<skill>/SKILL.md の frontmatter — **常時ロードされる要約**

3 番目が効くのは、**本文を読む前の判断材料**になるからで、置き去りにすると
**古い規範が先に読まれる**。#59 / PR #60 の周では、本文が「達成不能だから」と否定した文言を
要約が掲げ続ける状態が実際に生じた。しかも同じ同期漏れが**向きを変えて 2 回**起きている
（本文＋frontmatter を直して JSON が残る → JSON を直して frontmatter が残る）。

**判定は「3 つが同一か」ではない。** frontmatter は「いつこのスキルを起動するか」を書く
別目的の文章で、カタログの紹介文より長く引数の説明も含む。実際 `dev-loop` は
frontmatter 397 字に対して JSON は 147 字で、**一致させるほうが誤り**になる。

代わりに**共変（co-change）**を見る:

    1 つのプラグインが持つ description スロットのうち、どれかが変更されたら、
    存在する残りのスロットも同じ差分の中で変更されていること。

#60 で起きた 2 件はどちらも「片側だけ変わった」形なので、これで両方とも捕まる。
逆に、description を 1 つも触っていない差分には反応しないので、無関係な PR を落とさない。

判定の線引き:

- スロットが 1 つしか無いプラグイン → 比較相手がいないので対象外
- 新規プラグイン（base に plugin.json が無い）→ 対象外
- **frontmatter を解析できない → エラー**（fail-closed）。「読めないからスキップ」は
  #60 が潰した fail-open そのものなので、黙って通さない
- スキルが複数あるプラグイン → **全スキルの frontmatter を個別のスロットとして扱う**
  （代表を決められないため。1 つでも取り残されたらエラー）
- `main` への直接 push では base が曖昧なので判定できない。**PR のときだけ**実行する

どうしても片側だけ直したい場合（カタログの typo 修正など）は、コミットメッセージに
trailer を書く:

    Skip-description-sync: カタログの typo 修正のみ。要約の内容は変わらない

**理由は必須**で、履歴に残るのでレビューで追える。

標準ライブラリのみ。git はサブプロセスで呼ぶ。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

MARKETPLACE = ".claude-plugin/marketplace.json"
TRAILER = "Skip-description-sync:"

errors: list[str] = []


def git(*args: str) -> tuple[int, str]:
    """git を呼んで (returncode, stdout) を返す。stderr は捨てる。"""
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def show(ref: str, path: str) -> str | None:
    """指定 ref のファイル内容。存在しなければ None。"""
    code, out = git("show", f"{ref}:{path}")
    return out if code == 0 else None


def parse_frontmatter_description(text: str) -> str | None:
    """SKILL.md の YAML frontmatter から description を取り出す。

    PyYAML に依存しないよう、このリポジトリで実際に使っている 2 つの形だけを読む:
    1 行で書く形と、`>` の折り畳みブロック。折り畳みは 1 スペースで連結して 1 行に畳む。

    読めなければ None を返す。**呼び出し側はこれをエラーとして扱うこと**——
    「読めないから対象外」にすると、書式を崩した瞬間にチェックが無言で外れる。
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    front = text[4:end]

    lines = front.split("\n")
    for index, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        inline = line[len("description:") :].strip()
        if inline and inline not in (">", "|", ">-", "|-"):
            return inline
        # 折り畳みブロック: インデントが続く限り拾う
        collected: list[str] = []
        for cont in lines[index + 1 :]:
            if cont.strip() and not cont.startswith(" "):
                break
            collected.append(cont.strip())
        joined = " ".join(part for part in collected if part)
        return joined or None
    return None


def catalog_descriptions(text: str | None) -> dict[str, str]:
    """marketplace.json の中身から {プラグイン名: description} を作る。"""
    if text is None:
        return {}
    try:
        catalog = json.loads(text)
    except json.JSONDecodeError:
        return {}
    result: dict[str, str] = {}
    for entry in catalog.get("plugins", []):
        if isinstance(entry, dict) and "name" in entry and "description" in entry:
            result[entry["name"]] = entry["description"]
    return result


def manifest_description(text: str | None) -> str | None:
    if text is None:
        return None
    try:
        return json.loads(text).get("description")
    except json.JSONDecodeError:
        return None


def skill_paths(ref: str, plugin: str) -> list[str]:
    """指定 ref に存在する、そのプラグインの SKILL.md をすべて返す。"""
    code, out = git("ls-tree", "-r", "--name-only", ref, f"plugins/{plugin}/skills/")
    if code != 0:
        return []
    return sorted(line for line in out.splitlines() if line.endswith("/SKILL.md"))


def slots(ref: str, plugin: str, catalog: dict[str, str]) -> dict[str, str] | None:
    """指定 ref における、そのプラグインの description スロット一覧。

    plugin.json が無ければ None（新規プラグイン扱い）。
    frontmatter が解析できないスロットは、値の代わりに番兵を入れてエラーにする。
    """
    manifest = manifest_description(
        show(ref, f"plugins/{plugin}/.claude-plugin/plugin.json")
    )
    if manifest is None and show(ref, f"plugins/{plugin}/.claude-plugin/plugin.json") is None:
        return None

    found: dict[str, str] = {}
    if plugin in catalog:
        found[MARKETPLACE] = catalog[plugin]
    if manifest is not None:
        found[f"plugins/{plugin}/.claude-plugin/plugin.json"] = manifest

    for path in skill_paths(ref, plugin):
        text = show(ref, path)
        if text is None:
            continue
        description = parse_frontmatter_description(text)
        if description is None:
            errors.append(
                f"{plugin}: {path} の frontmatter から description を読めない。"
                "書式を確認する（読めないままだと、このチェックが無言で外れる）"
            )
            continue
        found[path] = description
    return found


def skip_requested(base: str) -> str | None:
    """コミットメッセージに Skip-description-sync trailer があれば、その理由を返す。"""
    code, out = git("log", "--format=%B", f"{base}..HEAD")
    if code != 0:
        return None
    for line in out.splitlines():
        stripped = line.strip()
        if stripped.startswith(TRAILER):
            reason = stripped[len(TRAILER) :].strip()
            if reason:
                return reason
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    base = sys.argv[1]

    code, _ = git("rev-parse", "--verify", f"{base}^{{commit}}")
    if code != 0:
        print(f"base ref '{base}' を解決できません。fetch-depth を確認してください。")
        return 2

    base_catalog = catalog_descriptions(show(base, MARKETPLACE))
    head_catalog = catalog_descriptions(show("HEAD", MARKETPLACE))

    plugins = sorted(set(base_catalog) | set(head_catalog))
    if not plugins:
        print("カタログにプラグインがありません。description のチェックはスキップします。")
        return 0

    drifted: list[tuple[str, list[str], list[str]]] = []

    for plugin in plugins:
        before = slots(base, plugin, base_catalog)
        after = slots("HEAD", plugin, head_catalog)

        if before is None or after is None:
            print(f"{plugin}: 新規または削除されたプラグイン。対象外")
            continue

        shared = sorted(set(before) & set(after))
        if len(shared) < 2:
            print(f"{plugin}: description スロットが {len(shared)} 個。比較相手がいないので対象外")
            continue

        changed = [slot for slot in shared if before[slot] != after[slot]]
        unchanged = [slot for slot in shared if before[slot] == after[slot]]

        if not changed:
            print(f"{plugin}: description に変更なし。OK")
        elif not unchanged:
            print(f"{plugin}: description を {len(changed)} 箇所すべてで更新。OK")
        else:
            drifted.append((plugin, changed, unchanged))

    if drifted:
        reason = skip_requested(base)
        for plugin, changed, unchanged in drifted:
            if reason is not None:
                print(
                    f"::warning::{plugin}: description が片側だけ変わっているが、"
                    f"Skip-description-sync が指定されている（理由: {reason}）"
                )
                continue
            errors.append(
                f"{plugin}: description が**片側だけ**変わっている。\n"
                f"      変更あり: {', '.join(changed)}\n"
                f"      変更なし: {', '.join(unchanged)}\n"
                "      3 箇所は一致させる必要はないが、**どれかを直したら残りも点検する**。\n"
                "      とくに SKILL.md の frontmatter は常時ロードされる要約なので、"
                "置き去りにすると古い規範が先に読まれる（#59 / PR #60 で 2 回発生）。\n"
                f"      片側だけで正しい場合は、コミットメッセージに "
                f"`{TRAILER} <理由>` を書く"
            )

    for message in errors:
        print(f"::error::{message}")

    if errors:
        print(f"\ndescription の同期漏れが {len(errors)} 件あります。")
        return 1
    print("\ndescription 同期のチェック: 問題なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
