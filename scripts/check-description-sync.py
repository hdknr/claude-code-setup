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
別目的の文章で、カタログの紹介文より長く引数の説明も含む。**一致させるほうが誤り**になる。

代わりに**共変（co-change）**を見る:

    1 つのプラグインが持つ description スロットのうち、どれかが変更されたら、
    存在する残りのスロットも同じ差分の中で変更されていること。

#60 で起きた 2 件はどちらも「片側だけ変わった」形なので、これで両方とも捕まる。
逆に、description を 1 つも触っていない差分には反応しないので、無関係な PR を落とさない。

判定の線引き:

- スロットが 1 つしか無いプラグイン → 比較相手がいないので対象外
- 新規プラグイン（base に plugin.json が無い）→ 対象外
- スキルが複数あるプラグイン → **全スキルの frontmatter を個別のスロットとして扱う**
  （代表を決められないため。1 つでも取り残されたらエラー）
- `main` への直接 push では base が曖昧なので判定できない。**PR のときだけ**実行する

**読めないものは、黙って対象外にしない（fail-closed）。** 初版はここが甘く、検証で
4 つの抜け道が見つかった:

| すり抜けた形 | 初版の挙動 | 現在 |
| --- | --- | --- |
| `description` キーを**削除**する | スロットごと比較から消えて無検知 | **キーの有無も値として比較**する（削除は「変更」） |
| `plugin.json` の JSON を壊す | 例外を握り潰してスロットが消える | **エラー** |
| `marketplace.json` の JSON を壊す | カタログ全体のチェックが無効化 | **エラー**（1 箇所の構文ミスで全体が黙るのが最悪） |
| `SKILL.md` の frontmatter が読めない | （初版からエラー） | エラー |

**「読めないからスキップ」は、書式を崩した瞬間にチェックが無言で外れるということ**で、
このスクリプトが防ごうとしている失敗そのものになる。

なお **marketplace からエントリを丸ごと削除**した場合は、既存の
`scripts/check-plugin-versions.py` が「plugins/ に存在するがカタログに載っていない」で
検出するので、ここでは重複して見ない。

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


class Unreadable:
    """JSON / frontmatter を解析できなかったことを表す番兵。

    「読めない」を None（＝キーが無い）と同じ扱いにすると、**書式を崩した瞬間に
    そのスロットが比較から消えてチェックが無言で外れる**。区別して必ずエラーにする。
    """

    __slots__ = ()

    def __repr__(self) -> str:  # デバッグ出力用
        return "<解析不能>"


UNREADABLE = Unreadable()

# スロットの値の型。str は description 本体、None は「キーが無い」、UNREADABLE は解析不能。
# None を独立した値として扱うので、**キーの削除も「変更」として検出される**。
SlotValue = "str | None | Unreadable"


def catalog_descriptions(ref: str) -> dict[str, object] | Unreadable | None:
    """marketplace.json から {プラグイン名: description（無ければ None）} を作る。

    ファイルが無ければ None、JSON として壊れていれば UNREADABLE を返す。
    **壊れているのを {} で代用してはならない**——1 箇所の構文ミスで、カタログ全体の
    共変チェックが黙って無効化される（検証で実際に見つかった、最も深刻な抜け道）。
    """
    text = show(ref, MARKETPLACE)
    if text is None:
        return None
    try:
        catalog = json.loads(text)
    except json.JSONDecodeError:
        return UNREADABLE
    result: dict[str, object] = {}
    for entry in catalog.get("plugins", []):
        if isinstance(entry, dict) and "name" in entry:
            result[entry["name"]] = entry.get("description")
    return result


def manifest_description(ref: str, plugin: str) -> object:
    """plugin.json の description。無ければ None、壊れていれば UNREADABLE。

    ファイル自体が無い場合は、区別のために FileNotFoundError 相当として
    "missing" 文字列ではなく専用の戻り値を使わず、呼び出し側が show() で先に確認する。
    """
    text = show(ref, f"plugins/{plugin}/.claude-plugin/plugin.json")
    if text is None:
        return UNREADABLE  # 呼び出し側が存在確認済みなので、ここに来たら異常
    try:
        return json.loads(text).get("description")
    except json.JSONDecodeError:
        return UNREADABLE


def skill_paths(ref: str, plugin: str) -> list[str]:
    """指定 ref に存在する、そのプラグインの SKILL.md をすべて返す。"""
    code, out = git("ls-tree", "-r", "--name-only", ref, f"plugins/{plugin}/skills/")
    if code != 0:
        return []
    return sorted(line for line in out.splitlines() if line.endswith("/SKILL.md"))


def slots(ref: str, plugin: str, catalog: dict[str, object]) -> dict[str, object] | None:
    """指定 ref における、そのプラグインの description スロット一覧。

    plugin.json が存在しなければ None（新規／削除されたプラグイン扱い）。

    値は str（description 本体）・None（キーが無い）・UNREADABLE（解析不能）の 3 種。
    **None を独立した値として持つのが要点**——スロットごと落とすと、
    キーを削除するだけでチェックをすり抜けられる。
    """
    manifest_path = f"plugins/{plugin}/.claude-plugin/plugin.json"
    if show(ref, manifest_path) is None:
        return None

    found: dict[str, object] = {}
    if plugin in catalog:
        found[MARKETPLACE] = catalog[plugin]
    found[manifest_path] = manifest_description(ref, plugin)

    for path in skill_paths(ref, plugin):
        text = show(ref, path)
        if text is None:
            continue
        description = parse_frontmatter_description(text)
        found[path] = UNREADABLE if description is None else description
    return found


def report_unreadable(ref: str, plugin: str, found: dict[str, object]) -> bool:
    """解析できないスロットがあればエラーに積む。1 つでもあれば True。"""
    bad = sorted(slot for slot, value in found.items() if isinstance(value, Unreadable))
    for slot in bad:
        errors.append(
            f"{plugin}: {ref} の {slot} から description を読めない。"
            "書式を確認する（読めないままだと、このチェックが無言で外れる）"
        )
    return bool(bad)


def describe(value: object) -> str:
    """エラーメッセージ用に、スロットの値を短く表す。"""
    if isinstance(value, Unreadable):
        return "解析不能"
    if value is None:
        return "キー無し"
    return "あり"


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

    base_catalog = catalog_descriptions(base)
    head_catalog = catalog_descriptions("HEAD")

    for ref, catalog in ((base, base_catalog), ("HEAD", head_catalog)):
        if isinstance(catalog, Unreadable):
            print(
                f"::error::{ref} の {MARKETPLACE} を JSON として解析できません。"
                "壊れたまま通すと、カタログ全体の共変チェックが黙って無効になります"
            )
            return 1
    if base_catalog is None or head_catalog is None:
        print(f"{MARKETPLACE} が見つかりません。description のチェックはスキップします。")
        return 0

    plugins = sorted(set(base_catalog) | set(head_catalog))
    if not plugins:
        print("カタログにプラグインがありません。description のチェックはスキップします。")
        return 0

    # (プラグイン名, 変更ありスロットの整形済み説明, 変更なしスロット名)
    drifted: list[tuple[str, list[str], list[str]]] = []

    for plugin in plugins:
        before = slots(base, plugin, base_catalog)
        after = slots("HEAD", plugin, head_catalog)

        if before is None or after is None:
            print(f"{plugin}: 新規または削除されたプラグイン。対象外")
            continue

        # 解析できないスロットは、比較の前にエラーにする（fail-closed）
        bad = report_unreadable(base, plugin, before)
        bad = report_unreadable("HEAD", plugin, after) or bad
        if bad:
            continue

        shared = sorted(set(before) & set(after))
        # 両方の ref で「キー無し」のスロットは、そもそもスロットではない
        shared = [s for s in shared if not (before[s] is None and after[s] is None)]
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
            drifted.append(
                (
                    plugin,
                    [
                        f"{slot}（{describe(before[slot])} → {describe(after[slot])}）"
                        for slot in changed
                    ],
                    unchanged,
                )
            )

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
