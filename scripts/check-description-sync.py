#!/usr/bin/env python3
"""プラグインの description を「片側だけ」直した差分を検出する。

usage: python3 scripts/check-description-sync.py <base-ref>

CI（.github/workflows/plugins.yml）が PR で呼ぶ。ローカルでも実行できる:

    python3 scripts/check-description-sync.py origin/main

なぜ必要か（#62）: プラグインの description は 3 箇所に複製されている。

    1. .claude-plugin/marketplace.json          — カタログ
    2. plugins/<dir>/.claude-plugin/plugin.json — マニフェスト
    3. plugins/<dir>/skills/<skill>/SKILL.md の frontmatter — **常時ロードされる要約**

3 番目が効くのは、**本文を読む前の判断材料**になるからで、置き去りにすると
**古い規範が先に読まれる**。#59 / PR #60 の周では、本文が「達成不能だから」と否定した文言を
要約が掲げ続ける状態が実際に生じた。しかも同じ同期漏れが**向きを変えて 2 回**起きている
（本文＋frontmatter を直して JSON が残る → JSON を直して frontmatter が残る）。

**判定は「3 つが同一か」ではない。** frontmatter は「いつこのスキルを起動するか」を書く
別目的の文章で、カタログの紹介文より長く引数の説明も含む。**一致させるほうが誤り**になる。

代わりに**共変（co-change）**を見る:

    1 つのプラグインが持つ description スロットのうち、どれかが変更されたら、
    残りのスロットも同じ差分の中で変更されていること。

#60 で起きた 2 件はどちらも「片側だけ変わった」形なので、これで両方とも捕まる。
逆に、description を 1 つも触っていない差分には反応しないので、無関係な PR を落とさない。

## 設計の芯 — 「無い」を落とさない

このチェックが破られる形は 1 つに集約される。**「読めない」「無い」をスロットごと
比較から落とすと、差分も一緒に消えて無検知になる。**

初版はここが甘く、レビューを重ねるたびに**同じ欠陥が次元を変えて**出てきた:

| 次元 | すり抜けた形 | 現在 |
| --- | --- | --- |
| **値** | `description` キーを削除する | キーの有無も値として比較（削除＝変更） |
| **値** | `plugin.json` / `marketplace.json` の JSON を壊す | エラー（構文ミス 1 箇所で全体が黙るのが最悪） |
| **値** | YAML の書式を変える（`>+`、`|` の後ろのコメント、複数行スカラー…） | **値を解釈するのをやめた**（下記） |
| **キー** | スキルのディレクトリ名を変える | 両側の**和集合**で比較（片側にしか無いスロットは「変更」） |
| **キー** | プラグインのディレクトリ名を変える | スロット ID にディレクトリ名を含めない／ディレクトリは **ref ごとに解決** |
| **キー** | カタログの `name` と実ディレクトリ名を食い違わせる | `source` だけを見る（`name` にフォールバックしない） |
| **キー** | `./plugins/./demo` のような書き方で解決に失敗させる | パスを正規化してから判定する |
| **収集** | 非 ASCII のパスが `ls-tree` で C クォートされる | `-z` で受け取る |
| **収集** | サブディレクトリから実行すると相対パスになる | `--full-tree` を付ける |

**スロットは「両側の積集合」ではなく「和集合」で数える。** 片側にしか存在しない
スロットは、欠けている側を「無い」という値として比較する。

**そして値を解釈しない。** frontmatter の description は、YAML として解釈せず
**フィールドの生テキストをそのまま比較**する。ここは 3 周続けて解釈漏れで穴が開いた
場所で、塞ぐたびに次の書式が出てきた。**解釈しなければ解釈漏れも起きない。**
代償として、折り返し位置を変えただけ・クォートを付けただけでも「変更」になるが、
**見逃すより誤検出するほうが安全**であり、どちらも「常時ロードされる要約に手を入れた」
ことに変わりはない。

判定の線引き:

- 新規／削除されたプラグイン（`plugin.json` が片方の ref にしか無い）→ 対象外
- **スキルの追加・削除・改名は「変更」として数える。** プラグインの守備範囲が変われば
  カタログの紹介文も見直す対象になるため。見直し不要と判断したなら trailer を使う
- `main` への直接 push では base が曖昧なので判定できない。**PR のときだけ**実行する

**marketplace からエントリを丸ごと削除**した場合は、和集合比較にしたことで
ここでも「あり → ファイル自体が無い」として検出される（既存の
`scripts/check-plugin-versions.py` も別の理由で落とすので、二重に見えることになる）。
**`source` が指すディレクトリが存在しない**場合と、**`source` キーが無い**場合は、
`check-plugin-versions.py` の担当なのでここでは対象外にする。

どうしても片側だけ直したい場合（カタログの typo 修正など）は、コミットメッセージの
**末尾に trailer として**書く（行頭から。引用文の中では効かない）:

    Skip-description-sync: カタログの typo 修正のみ。要約の内容は変わらない

**理由は必須**で、履歴に残るのでレビューで追える。既定では **PR 全体に効く**ので、
**プラグインを 1 つに絞りたいときは名前を前置する**:

    Skip-description-sync: dev-loop: スキルを 1 つ足しただけで、紹介文は変えない

絞らないと、1 つの逃げ道で**他のプラグインの同期漏れまで一緒に通る**。

標準ライブラリのみ。git はサブプロセスで呼ぶ。
"""

from __future__ import annotations

import json
import posixpath
import re
import subprocess
import sys

MARKETPLACE = ".claude-plugin/marketplace.json"
# マニフェストのスロット ID。プラグインのディレクトリ名は含めない（改名で免除されるのを防ぐ）
MANIFEST_SLOT = ".claude-plugin/plugin.json"
TRAILER_KEY = "Skip-description-sync"

# YAML の block scalar 指示子（`>` `|` に桁数と chomping が付きうる）
BLOCK_INDICATOR = re.compile(r"^[|>][0-9]*[+-]?$")

errors: list[str] = []


class Sentinel:
    """スロットの「値ではない状態」を表す番兵。

    **`None` や「スロットを消す」で代用してはならない。** 消えたスロットは差分も
    一緒に消えるので、無検知の抜け道になる（この設計の芯）。
    """

    __slots__ = ("label",)

    def __init__(self, label: str) -> None:
        self.label = label

    def __repr__(self) -> str:
        return self.label


UNREADABLE = Sentinel("解析不能")
MISSING = Sentinel("ファイル自体が無い")
NO_KEY = Sentinel("キー無し")


def git(*args: str) -> tuple[int, str]:
    """git を呼んで (returncode, stdout) を返す。stderr は捨てる。"""
    proc = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def show(ref: str, path: str) -> str | None:
    """指定 ref のファイル内容。存在しなければ None。"""
    code, out = git("show", f"{ref}:{path}")
    return out if code == 0 else None


def frontmatter_description_source(text: str) -> str | Sentinel:
    """SKILL.md の frontmatter から、description フィールドの**生テキスト**を切り出す。

    **値を解釈しない。** ここは 3 周続けて「YAML の解釈漏れ」で穴が開いた場所である:

    - 未知の block 指示子（`>+` `>2`）を*値そのもの*として返し、スロットが定数に固定される
    - 指示子の後ろに YAML コメント（`| # note`）が付くと同じことが起きる
    - クォート無しの複数行プレーンスカラーで継続行が落ちる
    - クォートが同じ行で閉じない場合も同様

    どれも「解釈できなかった分を落とす → 差分も消える」という同じ形で、
    **塞ぐたびに次の書式が出てくる**。YAML の全書式を自前で正しく解釈するのは割に合わない。

    そこで**解釈をやめる**。`description:` の行から、次のトップレベルキー（列 0 から始まる行）
    または frontmatter の終わりまでの**行をそのまま連結して返す**。
    比較したいのは「要約が書き換わったか」であって、YAML としての値ではない。

    この設計は**保守的な側に倒れる**——折り返し位置を変えただけ・クォートを付けただけでも
    「変更」になる。見逃すより誤検出するほうが安全であり、実際その 2 つも
    「常時ロードされる要約に手を入れた」ことに変わりはない。

    `description:` が無い、frontmatter が無い場合は UNREADABLE（fail-closed）。
    """
    if not text.startswith("---\n"):
        return UNREADABLE
    end = text.find("\n---", 4)
    if end == -1:
        return UNREADABLE
    lines = text[4:end].split("\n")

    for index, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        block = [line]
        for cont in lines[index + 1 :]:
            # 列 0 から始まる非空行 = 次のトップレベルキー
            if cont.strip() and not cont[0].isspace():
                break
            block.append(cont)
        # 末尾の空行は書式の揺れなので落とす（意味を持たない）
        while block and not block[-1].strip():
            block.pop()
        return "\n".join(block)
    return UNREADABLE


def load_catalog(ref: str) -> dict[str, dict[str, object]] | Sentinel | None:
    """marketplace.json から {プラグイン名: {description, source}} を作る。

    ファイルが無ければ None、JSON として壊れていれば UNREADABLE。
    **壊れているのを {} で代用してはならない**——1 箇所の構文ミスで、カタログ全体の
    共変チェックが黙って無効化される（レビューで見つかった最も深刻な抜け道）。
    """
    text = show(ref, MARKETPLACE)
    if text is None:
        return None
    try:
        catalog = json.loads(text)
    except json.JSONDecodeError:
        return UNREADABLE
    if not isinstance(catalog, dict):
        return UNREADABLE
    entries = catalog.get("plugins")
    if not isinstance(entries, list):
        return UNREADABLE

    result: dict[str, dict[str, object]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or "name" not in entry:
            continue
        value = entry.get("description", NO_KEY)
        result[entry["name"]] = {
            "description": value if isinstance(value, (str, Sentinel)) else NO_KEY,
            "source": entry.get("source"),
        }
    return result


def plugin_dir(source: object) -> str | None:
    """カタログの source からプラグインのディレクトリ名を得る。

    `name` がディレクトリ名と一致する保証は無い（レビューで見つかった抜け道）ので、
    **source だけを見る**。`name` にフォールバックすると、まさにその仮定が復活する。
    `source` が無い／文字列でないカタログは `check-plugin-versions.py` が
    「必須キーが無い」で落とすので、ここでは対象外にしてよい。

    **パスは正規化してから判定する。** `./plugins/./demo` のような書き方を
    「解釈できないから対象外」にすると、`check-plugin-versions.py` 側は通るのに
    こちらだけ黙って免除される——「落とすと差分も消える」の同じ形になる。
    正規化の結果 `plugins/<dir>` にならないもの（`plugins/../evil` で外に出る、
    絶対パス、階層が深い）だけを対象外にする。
    """
    if not isinstance(source, str) or source.startswith("/"):
        return None
    normalized = posixpath.normpath(source)
    prefix = "plugins/"
    if not normalized.startswith(prefix):
        return None
    rest = normalized[len(prefix) :]
    return rest if rest and "/" not in rest else None


def manifest_value(ref: str, directory: str) -> str | Sentinel:
    """plugin.json の description。ファイルが無ければ MISSING、壊れていれば UNREADABLE。"""
    text = show(ref, f"plugins/{directory}/.claude-plugin/plugin.json")
    if text is None:
        return MISSING
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return UNREADABLE
    if not isinstance(data, dict):
        return UNREADABLE
    value = data.get("description", NO_KEY)
    return value if isinstance(value, (str, Sentinel)) else NO_KEY


def skill_paths(ref: str, directory: str) -> list[tuple[str, str]]:
    """そのプラグインの SKILL.md を (スロット ID, リポジトリ内のパス) で返す。

    **スロット ID にプラグインのディレクトリ名を含めない**（`skills/<name>/SKILL.md`）。
    含めると、**プラグインのディレクトリを改名しただけで全スロットの ID が変わり**、
    「新規または削除されたプラグイン」として丸ごと免除される——スキルの改名で塞いだのと
    同じ穴の、プラグイン階層版になる。

    `-z` と `--full-tree` が要る:

    - `-z` 無しだと `core.quotePath` の既定で**非 ASCII のパスが C クォートされ**、
      `endswith("/SKILL.md")` に一致せずスロットが消える。日本語のディレクトリ名は、
      このリポジトリでは十分ありうる。
    - `--full-tree` 無しだと**カレントディレクトリ相対**になる。docstring と CLAUDE.md は
      ローカル実行を案内しているので、サブディレクトリから走らせると SKILL.md の
      スロットが全部消えたまま JSON 側だけ比較され、**沈黙が正常な合格に見える**。
    """
    prefix = f"plugins/{directory}/"
    code, out = git(
        "ls-tree", "-r", "-z", "--name-only", "--full-tree", ref, f"{prefix}skills/"
    )
    if code != 0:
        return []
    return sorted(
        (path[len(prefix) :], path)
        for path in out.split("\0")
        if path.endswith("/SKILL.md") and path.startswith(prefix)
    )


def slots(
    ref: str, name: str, directory: str, catalog: dict[str, dict[str, object]]
) -> dict[str, object]:
    """指定 ref における、そのプラグインの description スロット一覧。

    キーは**プラグインのディレクトリ名に依存しない安定した ID**（上記参照）。
    値は str（生テキスト）・NO_KEY・MISSING・UNREADABLE のいずれか。
    **スロットを落とさない**のが要点で、「無い」も比較可能な値として持つ。
    """
    entry = catalog.get(name)
    found: dict[str, object] = {
        MARKETPLACE: entry["description"] if entry else MISSING,
        MANIFEST_SLOT: manifest_value(ref, directory),
    }
    for skill_id, path in skill_paths(ref, directory):
        text = show(ref, path)
        found[skill_id] = UNREADABLE if text is None else frontmatter_description_source(text)
    return found


def describe(value: object) -> str:
    """エラーメッセージ用に、スロットの値を短く表す。"""
    return value.label if isinstance(value, Sentinel) else "あり"


def skip_reasons(base: str) -> dict[str | None, str]:
    """コミットメッセージの trailer から {対象プラグイン名 or None: 理由} を作る。

    **git の trailer 解釈に任せる**（行頭・末尾段落）。初版は「行を strip して前方一致」
    だったため、**過去のメッセージを引用しただけの行でもチェックが無効化**できた。

    値を `<プラグイン名>: <理由>` の形にすると、**そのプラグインだけ**に効く。
    プラグイン名を書かなければ PR 全体に効く——スキルを 1 つ足しただけの周で、
    **他のプラグインの同期漏れまで一緒に通す**のを避けたいときは名前を書く。
    """
    code, out = git(
        "log", f"--format=%(trailers:key={TRAILER_KEY},valueonly)", f"{base}..HEAD"
    )
    if code != 0:
        return {}
    found: dict[str | None, str] = {}
    for line in out.splitlines():
        value = line.strip()
        if not value:
            continue
        target: str | None = None
        head, sep, rest = value.partition(":")
        if sep and rest.strip() and " " not in head.strip():
            target, value = head.strip(), rest.strip()
        found.setdefault(target, value)
    return found


def resolve_base(ref: str) -> str | None:
    """比較の基点。分岐元（merge-base）を使う。

    `check-version-bump.py` が `{base}...HEAD` を使うのに合わせる。2 つの先端を直接
    比べると、**base 側が進んだ分まで「このブランチの変更」に見えて**誤検出する。
    """
    code, _ = git("rev-parse", "--verify", f"{ref}^{{commit}}")
    if code != 0:
        return None
    code, out = git("merge-base", ref, "HEAD")
    return out.strip() if code == 0 and out.strip() else ref


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    base = resolve_base(sys.argv[1])
    if base is None:
        print(f"base ref '{sys.argv[1]}' を解決できません。fetch-depth を確認してください。")
        return 2

    base_catalog = load_catalog(base)
    head_catalog = load_catalog("HEAD")
    for ref, catalog in ((base, base_catalog), ("HEAD", head_catalog)):
        if isinstance(catalog, Sentinel):
            print(
                f"::error::{ref} の {MARKETPLACE} を JSON として解析できません。"
                "壊れたまま通すと、カタログ全体の共変チェックが黙って無効になります"
            )
            return 1
    if base_catalog is None and head_catalog is None:
        print(f"{MARKETPLACE} が両方の ref に見つかりません。チェックはスキップします。")
        return 0
    if base_catalog is None or head_catalog is None:
        missing = base if base_catalog is None else "HEAD"
        print(
            f"::error::{missing} に {MARKETPLACE} がありません。"
            "片側にしか無い状態を「対象外」にすると、カタログを消すだけでチェックが黙ります"
        )
        return 1
    assert isinstance(base_catalog, dict) and isinstance(head_catalog, dict)

    names = sorted(set(base_catalog) | set(head_catalog))
    if not names:
        print("カタログにプラグインがありません。description のチェックはスキップします。")
        return 0

    drifted: list[tuple[str, list[str], list[str]]] = []

    for name in names:
        # **ディレクトリは ref ごとに解決する。** HEAD の source だけで両方を見ると、
        # プラグインのディレクトリを改名した周に base 側が MISSING になり、
        # 「新規または削除されたプラグイン」として**丸ごと免除**される。
        dirs = {
            ref: plugin_dir((catalog.get(name) or {}).get("source"))
            for ref, catalog in ((base, base_catalog), ("HEAD", head_catalog))
        }
        usable = [d for d in dirs.values() if d is not None]
        if not usable:
            print(f"{name}: source がリポジトリ内のプラグインを指していません。対象外")
            continue

        before = slots(base, name, dirs[base] or usable[0], base_catalog)
        after = slots("HEAD", name, dirs["HEAD"] or usable[-1], head_catalog)

        if before[MANIFEST_SLOT] is MISSING or after[MANIFEST_SLOT] is MISSING:
            print(f"{name}: 新規または削除されたプラグイン。対象外")
            continue

        every = sorted(set(before) | set(after))

        # 解析できないスロットは、比較の前にエラーにする（fail-closed）
        unreadable = [
            slot
            for slot in every
            if before.get(slot) is UNREADABLE or after.get(slot) is UNREADABLE
        ]
        if unreadable:
            for slot in unreadable:
                errors.append(
                    f"{name}: {slot} から description を読めません。"
                    "書式を確認してください（読めないままだと、このチェックが無言で外れます）"
                )
            continue

        # **積集合ではなく和集合。** 片側にしか無いスロットは「無い」を値として比較する
        # （スキルを改名すると両方のキーが消える、という抜け道を塞ぐ）
        changed = [s for s in every if before.get(s, MISSING) != after.get(s, MISSING)]
        unchanged = [s for s in every if s not in changed]

        if not changed:
            print(f"{name}: description に変更なし。OK")
        elif not unchanged:
            print(f"{name}: description を {len(changed)} 箇所すべてで更新。OK")
        else:
            drifted.append(
                (
                    name,
                    [
                        f"{s}（{describe(before.get(s, MISSING))} → {describe(after.get(s, MISSING))}）"
                        for s in changed
                    ],
                    unchanged,
                )
            )

    if drifted:
        reasons = skip_reasons(base)
        for name, changed, unchanged in drifted:
            reason = reasons.get(name, reasons.get(None))
            if reason is not None:
                print(
                    f"::warning::{name}: description が片側だけ変わっていますが、"
                    f"{TRAILER_KEY} が指定されています（理由: {reason}）"
                )
                continue
            errors.append(
                f"{name}: description が**片側だけ**変わっています。"
                f" 変更あり: {', '.join(changed)} ／ 変更なし: {', '.join(unchanged)}"
            )

    # ::error:: は 1 行しか注釈にならないので、1 件 1 行に畳む
    for message in errors:
        print(f"::error::{message}")

    if errors:
        print(
            "\n3 箇所は一致させる必要はありませんが、**どれかを直したら残りも点検**してください。\n"
            "とくに SKILL.md の frontmatter は常時ロードされる要約なので、置き去りにすると\n"
            "古い規範が先に読まれます（#59 / PR #60 で 2 回発生）。\n"
            f"片側だけで正しい場合は、コミットメッセージの末尾に `{TRAILER_KEY}: <理由>` を書きます。"
        )
        print(f"\ndescription の同期漏れが {len(errors)} 件あります。")
        return 1
    print("\ndescription 同期のチェック: 問題なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
