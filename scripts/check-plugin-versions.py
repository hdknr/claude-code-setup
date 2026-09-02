#!/usr/bin/env python3
"""マーケットプレイスカタログとプラグインの整合をチェックする。

CI（.github/workflows/plugins.yml）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-plugin-versions.py

検証する内容:

1. marketplace.json の構造 — 必須キーの有無、名前の重複、source の指す先が実在するか
2. version の一致 — marketplace.json のエントリと plugin.json が同じ値か
3. SKILL.md 本文の版表記 — `<!-- skill-version: X -->` が plugin.json と同じ値か
4. 公開サイトへの絶対リンク — 指すページとアンカーが docs/ に実在するか
5. 取りこぼし — plugins/ にあるのにカタログに載っていないプラグイン

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
import re
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
    check_site_links(name, source_dir)
    if plugin_version is not None and plugin_version != catalog_version:
        fail(
            f"{name}: version が一致しない — "
            f"marketplace.json={catalog_version} / plugin.json={plugin_version}。"
            "CLAUDE.md「プラグインの更新」のとおり 3 箇所（marketplace.json / plugin.json / SKILL.md）を揃える"
        )

    return source_dir.name


SKILL_VERSION_MARKER = "<!-- skill-version: "
SKILL_VERSION_VISIBLE = "**このスキルの版: "
# 可視テキストは行頭のこの形だけを認める。`> ` は行頭にあって初めて引用になるので、
# 散文の途中に同じ文字列があっても数えないため。
# **コメントでの無効化を防いでいるのはこれではなく、下のコメント除去のほう。**
VISIBLE_PREFIX = "> " + SKILL_VERSION_VISIBLE


def skill_files(source_dir: Path) -> list[Path]:
    """そのプラグインが持つ SKILL.md を**すべて**返す。

    **レイアウトを推測しない。** スキルの置き場所は 1 通りではない——`skills/<name>/` の他に、
    単一スキルなら**プラグインルート直下**でよいし、`plugin.json` の `skills` フィールドで
    **任意のパスを指定**することもできる（この環境の `impeccable` が実際に使っている）。

    レイアウトを列挙して判定すると、**知らない形が黙って無検査になる**。実際、初版は
    `skills/` しか見ずルート直下を落とし、次の版はその 2 つしか見ず `skills` フィールドを
    落とした——**同じ失敗を 2 回**やっている。

    そこで**探索をやめて全部拾う**。プラグイン配下の `SKILL.md` を再帰的に集めれば、
    レイアウトを知らなくても取りこぼさない。多めに拾う方向の誤りは「版を書け」と
    言われるだけなので、**見逃しより安全**。

    **ただし「漏れない」とまでは言えない。** 限界を 2 つ承知して使う:

    - `rglob` は**シンボリックリンクのディレクトリには入らない**（Python の既定）。
      リンク越しにしか辿れないスキルは検査されない。このリポジトリの `plugins/` に
      symlink は無いが、置けば静かに免除される。
    - **配布物以外まで拾う。** ハーネス別のミラーやベンダーツリーを同梱するプラグインだと、
      本来のスキルの何倍も引っかかる（上で挙げた `impeccable` は 216 個の `SKILL.md` を
      持ち、実体は `./.claude/skills` の 18 個だけ）。**このスクリプトはこのリポジトリの
      CI であって汎用ツールではない**ので現状は許容しているが、そういう構成のプラグインを
      足すなら除外の仕組みが要る。
    """
    return sorted(source_dir.rglob("SKILL.md"))


def strip_fences(text: str) -> str:
    """コードフェンスの中身を落とす（``` と ~~~ の両方）。

    フェンス内の記載は読者に「版」として見えないので、それを根拠に合格させると
    可視テキストを検査する意味が無くなる。逆に、**規約を例示しているだけの
    フェンス**を数えると「2 個ある」で誤って落ちる（`CLAUDE.md` がまさにその例を載せている）。

    **同じ文字で、開いたのと同じ長さ以上でしか閉じない**（Markdown の規則）。長さを見ないと、
    4 個の ` で開いた囲み——**まさに ``` を含む例を載せるときの書き方**——が内側の ``` で
    閉じてしまい、例が本文に漏れて「2 個ある」と誤検出する。

    行数を保つため、落とした行は空行に置き換える。
    """
    out: list[str] = []
    fence: str | None = None
    for line in text.split("\n"):
        marker = line.lstrip()
        run = ""
        for char in ("`", "~"):
            if marker.startswith(char * 3):
                run = marker[: len(marker) - len(marker.lstrip(char))]
                break
        if fence is None:
            if run:
                fence = run
                out.append("")
                continue
        elif run and run[0] == fence[0] and len(run) >= len(fence):
            fence = None
            out.append("")
            continue
        out.append("" if fence else line)
    return "\n".join(out)


def extract_versions(text: str) -> tuple[list[str], list[str]]:
    """SKILL.md 本文から (コメントの版, 可視テキストの版) を取り出す。

    **「読者に見えない部分を先に落としてから探す」** 方式にしてある。行ごとの場当たり判定は、
    塞ぐたびに別の書式が出てきた——単一行の `<!-- ... -->` を塞いだら**複数行の**囲みが
    残り、``` を塞いだら `~~~` が残った。しかも実際のマーカーは 5 行のブロック引用なので、
    **無効化する現実的な方法は複数行の囲みのほう**で、塞いでいたのは起きにくい側だった。

    順序が要点:

    1. **フェンスを落とす**（``` と `~~~`）。例示のためのフェンスを数えないため
    2. **コメントの版はここで拾う**（マーカー自体が HTML コメントなので、落とす前に）
    3. **HTML コメントを落とす**（複数行にまたがるものも）
    4. **可視テキストの版を拾う** — 行頭が `> **このスキルの版: ` のものだけ

    **1 行に複数あっても数える。** 1 行 1 件しか拾わないと、同じ行に古い版を並べて残せる。
    """
    body = strip_fences(text)

    # コメント側も**行頭のみ**を認める。行の途中まで拾うと、規約を説明する散文
    # （`` 版は `<!-- skill-version: X -->` と書く `` ）や 4 字下げの例示を
    # 「本物が 2 個ある」と誤検出する。可視テキスト側と同じ扱いに揃えた。
    comments = [
        match.group(1).strip()
        for line in body.split("\n")
        if line.startswith(SKILL_VERSION_MARKER)
        for match in re.finditer(re.escape(SKILL_VERSION_MARKER) + r"(.*?)-->", line)
    ]

    # コメント（複数行にまたがるものを含む）を落としてから、可視テキストを探す
    uncommented = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    visible = [
        match.group(1).strip()
        for line in uncommented.split("\n")
        if line.startswith(VISIBLE_PREFIX)
        for match in re.finditer(re.escape(SKILL_VERSION_VISIBLE) + r"(.*?)\*\*", line)
    ]
    return comments, visible


def check_placement(plugin: str, skill: Path, text: str) -> None:
    """版の記載が**冒頭にある**ことを確かめる。

    この記載の役目は「起動して読まれたときに目に入る」こと（#63 の不変条件 1-a）。
    400 行の末尾に置いても検査は通ってしまうが、**それでは目的を果たさない**。
    「最初の `##` 見出しより前」を条件にする——本物はどれも `# 見出し` の直後にある。
    """
    body = strip_fences(text)
    lines = body.split("\n")
    section = next(
        (i for i, line in enumerate(lines) if line.startswith("## ")), len(lines)
    )
    for label, prefix in (("コメント", SKILL_VERSION_MARKER), ("可視テキスト", VISIBLE_PREFIX)):
        positions = [i for i, line in enumerate(lines) if line.startswith(prefix)]
        if positions and positions[0] >= section:
            fail(
                f"{plugin}: {rel(skill)} の版の{label}が最初の見出し節より後ろにある。"
                "**読まれたときに目に入る**ことが目的なので、冒頭の見出しの直後に置く（#63）"
            )


def check_skill_versions(plugin: str, source_dir: Path, version: str) -> None:
    """そのプラグインの全 SKILL.md 本文に、plugin.json と同じ版が書かれているか。

    **コメントと可視テキストの両方を見る。** コメント（`<!-- skill-version: X -->`）は
    機械が読む印だが、**古いキャッシュに気づかせる役目を負っているのは可視テキストのほう**
    （`> **このスキルの版: X**`）である。コメントだけ検査すると、実際に目に入る側が
    ずれても緑のまま通る——レビューで再現された。守りたいものを守る。

    SKILL.md を 1 つも持たないプラグイン（`commands/` だけ等）は検査対象なし。
    持っているのに記載が無ければ**エラー**にする（fail-closed）。
    """
    for skill in skill_files(source_dir):
        text = skill.read_text(encoding="utf-8")
        comments, visible = extract_versions(text)
        check_placement(plugin, skill, text)

        for label, found, hint in (
            ("コメント", comments, f"`{SKILL_VERSION_MARKER}{version} -->`"),
            ("可視テキスト", visible, f"`{VISIBLE_PREFIX}{version}**`（行頭から）"),
        ):
            if not found:
                fail(
                    f"{plugin}: {rel(skill)} に版の{label}が無い。{hint} を見出しの直後に置く"
                    "（古いキャッシュが読まれたときに気づく手掛かり。#63）"
                )
            elif len(found) > 1:
                fail(f"{plugin}: {rel(skill)} に版の{label}が {len(found)} 個ある。1 つにする")
            elif found[0] != version:
                fail(
                    f"{plugin}: {rel(skill)} の版の{label}が {found[0]} で "
                    f"plugin.json の {version} と一致しない。版を上げたら本文の記載も直す"
                )


SITE_PREFIX = "https://hdknr.github.io/claude-code-setup/"


def check_site_links(plugin: str, source_dir: Path) -> None:
    """配布物から公開サイトへの絶対リンクが、実際に解決するかを見る。

    **mkdocs はこれを検証できない。** `SKILL.md` や `README.md` は `docs_dir` の外にあるので
    mkdocs が読まないし、絶対 URL は仮に読んでも検証対象外である。
    つまり `strict: true` にしても**ここだけは守られていない**。

    #61 / #64 の周で、規範の根拠を設計ドキュメントへ移して本文からはリンクだけを残した。
    リンクが切れると**移した先に辿り着けなくなる**ので、機械的に見る。
    """
    for source in sorted(source_dir.rglob("*.md")):
        for line in source.read_text(encoding="utf-8").split("\n"):
            index = 0
            while True:
                index = line.find(SITE_PREFIX, index)
                if index == -1:
                    break
                # `<...>` の自動リンク・`[...](...)`・素の URL のいずれも取れるように、
                # URL に現れない文字で切る
                url = re.split(r"[\s)>\]」）]", line[index:])[0].rstrip(".,、。")
                index += len(SITE_PREFIX)

                rest = url[len(SITE_PREFIX) :]
                page, _, fragment = rest.partition("#")
                page = page.strip("/")
                target = REPO_ROOT / "docs" / f"{page}.md"
                if not target.is_file():
                    target = REPO_ROOT / "docs" / page / "index.md"
                if not target.is_file():
                    fail(
                        f"{plugin}: {rel(source)} のリンク {url} が指すページが docs/ に無い"
                    )
                    continue
                if fragment and f"{{ #{fragment} }}" not in target.read_text(encoding="utf-8"):
                    fail(
                        f"{plugin}: {rel(source)} のリンク {url} のアンカー #{fragment} が "
                        f"{rel(target)} に無い。見出しに `{{ #{fragment} }}` を付ける"
                        "（絶対 URL なので mkdocs は検証しない）"
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
