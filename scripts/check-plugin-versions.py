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
6. description の一致 — marketplace.json のエントリと plugin.json が同じ値か（#224。
   SKILL.md の frontmatter は比べない——そちらは check-description-sync.py が共変を見る）
7. 判定役の agent 定義 — `agents/` の下の `*.md` が**許可リストの `tools:` を持ち、
   読み取りと `Bash` 以外を 1 つも列挙せず、`model:` を書いていない**か（#217。
   何を守り何を守らないかは `check_agents` の docstring を正とする）

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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from markdown_fences import strip_fences  # noqa: E402

from site_links import broken_links  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = REPO_ROOT / "plugins"

REQUIRED_CATALOG_KEYS = ("name", "owner", "plugins")
REQUIRED_ENTRY_KEYS = ("name", "source", "version")

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(path: Path) -> dict | None:
    """JSON を読む。壊れていれば errors に積んで None を返す。

    **JSON として正しくてもオブジェクトでなければ壊れている側に倒す**——
    呼ぶ側は `.get()` するので、`[]` や `"x"` を通すと AttributeError でクラッシュする（#224）。
    """
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        fail(f"{rel(path)} が存在しない")
        return None
    except json.JSONDecodeError as exc:
        fail(f"{rel(path)} が JSON として不正: {exc}")
        return None
    if not isinstance(data, dict):
        fail(f"{rel(path)} がオブジェクトでない（{type(data).__name__}）")
        return None
    return data


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
    check_agents(name, source_dir)
    if plugin_version is not None and plugin_version != catalog_version:
        fail(
            f"{name}: version が一致しない — "
            f"marketplace.json={catalog_version} / plugin.json={plugin_version}。"
            "CLAUDE.md「プラグインの更新」のとおり 3 箇所（marketplace.json / plugin.json / SKILL.md）を揃える"
        )
    check_description(entry, manifest)

    return source_dir.name


def check_description(entry: dict, manifest: dict) -> None:
    """marketplace.json と plugin.json の description が同じ値かを見る（#224）。

    **base を見ない。** `check-description-sync.py` は共変を base との diff で見るので、
    base に無い（新規の）プラグインは定義上見られない——#215 の周でそこを素通りした。
    ここは 1 つのツリーだけで判定するので、新規も既存も同じに見える。

    **キーが無いことも値として比べる**（片側だけ消した形を落とさない。`null` とも区別する）。
    **型も比べる——入れ子の中まで**（`json.dumps` の文字列で比べるので `1` と `true` と `1.0` が分かれる）。
    両側とも無ければ一致として通す——description を必須にするのはこの検査の役目ではない。
    **正規化しない**（空白の違いも食い違いとして出す）。
    SKILL.md の frontmatter は別目的の文章なので比べない（共変は check-description-sync.py）。
    """
    missing = object()
    catalog = entry.get("description", missing)
    plugin = manifest.get("description", missing)
    # Python では 1 == True == 1.0 が成り立ち、入れ子の [1] == [True] も成り立つ。
    # JSON の表記で比べれば型が入れ子まで分かれる（キーの順序は意味を持たないので揃える）
    def canonical(value: object) -> object:
        return value if value is missing else json.dumps(value, sort_keys=True)

    if canonical(catalog) == canonical(plugin):
        return

    def show(value: object) -> str:
        return "（キーが無い）" if value is missing else json.dumps(value, ensure_ascii=False)

    fail(
        f"{entry['name']}: description が一致しない — "
        f"marketplace.json={show(catalog)} / plugin.json={show(plugin)}。"
        "CLAUDE.md「description は 3 箇所にある」のとおり JSON の 2 箇所は同じ値に揃える"
    )


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


def check_site_links(plugin: str, source_dir: Path) -> None:
    """配布物から公開サイトへの絶対リンクが、実際に解決するかを見る。

    **mkdocs はこれを検証できない。** `SKILL.md` や `README.md` は `docs_dir` の外にあるので
    mkdocs が読まないし、絶対 URL は仮に読んでも検証対象外である。
    つまり `strict: true` にしても**ここだけは守られていない**。

    #61 / #64 の周で、規範の根拠を設計ドキュメントへ移して本文からはリンクだけを残した。
    リンクが切れると**移した先に辿り着けなくなる**ので、機械的に見る。

    **リンク先の見出しには明示 id を付ける**のがこのリポジトリの約束（上記の理由）。
    """
    for source in sorted(source_dir.rglob("*.md")):
        for problem in broken_links(source, REPO_ROOT / "docs"):
            fail(f"{plugin}: {rel(source)} の{problem}")


# 判定役（検証・レビュー）の agent が持ってよいツール。**許可リストで持つ**——
# 禁止のほうを列挙すると、`NotebookEdit` や MCP の書き込みツールのように知らない名前が素通りする。
AGENT_ALLOWED_TOOLS = ("Read", "Grep", "Glob", "Bash")


def agent_frontmatter(text: str) -> dict[str, str] | None:
    """agent 定義の frontmatter を {キー: 値} で返す。無い・閉じていなければ None。

    **行頭のキーだけ**を拾う。値が空で次の行から `- 名前` が続く形（YAML のリスト）は、
    カンマ区切りに直して返す。

    **読めない形は `ValueError` にする（拾い損ねて通さない）**——行頭にあるのに `キー: 値` の形で
    読めない行（`model : x`・`"model": x` のように YAML としては有効なキー）と、
    **同じキーが 2 回ある**定義（後勝ちで読むと `tools: Write` を後ろの行で隠せる）。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        match = re.match(r"([A-Za-z_][\w-]*):(?:\s+(.*))?$", line)
        if match:
            key = match.group(1)
            if key in fields:
                raise ValueError(f"キー {key}: が 2 回ある")
            fields[key] = (match.group(2) or "").strip()
        elif line.strip() and not line[0].isspace() and not line.startswith("#"):
            raise ValueError(f"キー: 値 の形で読めない行がある: {line.strip()}")
        elif key is not None and re.match(r"\s+-\s*\S", line):
            item = line.strip()[1:].strip()
            fields[key] = f"{fields[key]}, {item}" if fields[key] else item
    return None


def check_agents(plugin: str, source_dir: Path) -> None:
    """判定役の agent 定義が、書く手段を持たないかを見る（#217）。

    **対象はプラグインの中の、`agents` という名前のディレクトリの直下にある `*.md` すべて。**
    このリポジトリの agent は**どれも判定役**（dev-loop の Verifier、spec-loop の 3 役）である。
    書き込みが要る agent を足すなら、**この検査を意図して変える**——黙って免除しない。

    守るもの:

    - **`tools:` が無い（空の）定義を落とす。** 書かなければ**全ツールを継承する**。
    - **`tools:` が `AGENT_ALLOWED_TOOLS` 以外を 1 つでも含めば落とす**（許可リストで判定する。
      `Bash(…)` のような絞り込みは、括弧の前の名前で見る。`*` や MCP の名前も落ちる）。
    - **`model:` を書いた定義を落とす。** 固定すると、呼び出し側の「実装とは別のティア」を
      黙って破る（実装と同じティアの周が出る）。ティアは呼び出し時の引数で選ぶ。
    - **frontmatter を読めない定義を落とす**——`キー: 値` の形でない行頭の行と、重複したキー
      （`agent_frontmatter`）。拾い損ねたキーは検査をすり抜けるので、読めないものは通さない。

    守らないもの:

    - **`Bash` は書ける**（`>` のリダイレクト）。証拠を出すために残している——
      **構造で密閉できるのはここまで**で、残りは agent の本文の指示に頼る。
    - **`plugin.json` の `agents` で別の場所を指した定義**は見ない（このリポジトリは使っていない）。
    - **呼び出し側が `model` を実際に渡したか**は見ない（スキルの本文の規定に頼る）。
    """
    for path in sorted(source_dir.rglob("*.md")):
        if path.parent.name != "agents":
            continue
        try:
            fields = agent_frontmatter(path.read_text(encoding="utf-8"))
        except ValueError as error:
            fail(f"{plugin}: {rel(path)} の frontmatter を読めない（{error}）。読めない定義は通さない")
            continue
        if fields is None:
            fail(f"{plugin}: {rel(path)} に frontmatter が無い（閉じていない）。agent 定義として読めない")
            continue
        if not fields.get("tools"):
            fail(
                f"{plugin}: {rel(path)} に tools: が無い。書かなければ全ツールを継承する——"
                f"判定役は許可リスト（{', '.join(AGENT_ALLOWED_TOOLS)}）で書く"
            )
        else:
            names = [item.strip().split("(", 1)[0].strip() for item in fields["tools"].split(",")]
            extra = [name for name in names if name not in AGENT_ALLOWED_TOOLS]
            if extra:
                fail(
                    f"{plugin}: {rel(path)} の tools: に判定役が持ってはならないツールがある: "
                    f"{', '.join(extra)}（許してよいのは {', '.join(AGENT_ALLOWED_TOOLS)} だけ）"
                )
        if "model" in fields:
            fail(
                f"{plugin}: {rel(path)} が model: を書いている。固定すると「実装とは別のティア」を"
                "黙って破る——ティアは呼び出し時の model 引数で選ぶ"
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
