"""spec-loop の表示用ページを作る MkDocs のフック（spec-loop の雛形。init-mkdocs.py が写した）。

ページに印 `<!-- spec-loop: <名前> -->` を書くと、`on_page_markdown` がその場所を描画関数の出力に置き換える。
**正本は CSV のまま**——ページに表を書き写さない。標準ライブラリだけで動く（正本リポジトリへ写されて単独で動く）。

| 印 | 描くもの |
| --- | --- |
| `qa` | 各版の `docs/v<n>/shared/qa.csv` を、版ごとの節に（件数・一覧・質問ごとの詳細。推奨の選択肢と理由も） |

**描くのは共有の層の表だけ**——内部の層の表（`docs/v<n>/spec/qa-dev.csv`）は描かない（開発者が決めて記録するもの。
spec-loop の `references/qa-csv.md` の「層」）。

- **版は重ね合わせない。** v2 で同じ `No` の行を置いて問い直した質問は、v1 と v2 の両方の節に出る。
  アンカーは `v<n>-q-001` の形で、版をまたいで一意。
- **読めない表・見出しが列名と違う表・知らない印は、警告を出し、ページにも注意書きを置く。**
  警告は `mkdocs` のロガーに出すので、`mkdocs build --strict` は落ちる（黙って空の表を出さない）。
- **列の決まりの検査はしない**——それは spec-loop の `check-qa-csv.py` の仕事。ここが見るのは見出しの行だけ。
  **推奨の列が無い見出しは前の形（spec-loop 0.17.0 まで）の表**で、警告に移す手順の指し先を添える。
  逆に、前の形のフック（推奨の列を知らない）は新しい表を「見出しが違う」で警告する——どちらでも黙って崩れた表は出ない。
  **フックを新しくする手順は spec-loop の `references/tree.md` の「Q&A 表を移す」**。
- セルの文字は HTML と Markdown の記号をエスケープし、改行は `<br>` にする（表を壊さない）。
  **CSV の文字は表のセルにだけ置く**——段落や箇条書きに置くと、行頭の `!!! `・字下げ・`1. ` がブロックの記法に読まれる。
- 描くものを足すときは、描画関数を書いて `RENDERERS` に足す。

**本文の Q&A の番号（`Q-008`）は、Q&A 表のページ（`qa.md`）のアンカーへのリンクにする**（正本は番号のまま。
決まりは spec-loop の `references/qa-csv.md` の「本文での番号」）。`on_page_content` が**描いた後の HTML** に掛けるので、
描画関数が描いた表のセルにも掛かる。

- **書き換えるのは HTML の文字だけ**（タグ・属性・コメントは変えない）。次の要素の中は変えない:
  見出し（`h1`〜`h6`）・コード（`pre`・`code`・`kbd`・`samp`）・リンク（`a`）・`script`・`style`・`textarea`・`title`。
  **Markdown を読み直さない**——見出しかコードかリンクかは、MkDocs（Python-Markdown と拡張）が描いた結果で決まる
  （アドモニション・箇条書き・引用の中も、字下げのコードブロックも、生の HTML も同じ扱いになる）。
- リンク先は MkDocs の `File.url_relative_to` で作る（`use_directory_urls` に従う）。
- 版は、`docs/v<n>/` の下のページなら `v1`〜`v<n>` のうち、版の外のページならすべての版のうち、
  **その番号を持つ最も新しい版**（版は重ね合わせないので、問い直していない番号は前の版の節にしか無い）。
- **リンクにする版の Q&A 表に無い番号はリンクにせず警告する**（打ち間違いを拾う）。版の下のページなら、
  その版より新しい版にだけある番号もここに入る。読めない表の番号は数えない（表の警告は Q&A 表のページで出る）。
- Q&A 表のページ（`qa` の印を持つページ）と、`qa.md` の無いサイトは変えない。
"""

from __future__ import annotations

import csv
import html
import logging
import re
from pathlib import Path

log = logging.getLogger("mkdocs.hooks.spec_loop_pages")

MARKER = re.compile(r"<!--\s*spec-loop:\s*(?P<name>[A-Za-z0-9_-]+)\s*-->")
VERSION = re.compile(r"v[1-9][0-9]*")

# spec-loop の references/qa-csv.md の列（check-qa-csv.py の COLUMNS と同じ。写しなので、テストが突き合わせる）
QA_COLUMNS = ["No", "起票元", "質問", "選択肢", "推奨", "推奨の理由", "回答", "反映先", "状態", "費用への影響"]
QA_DONE = "反映済み"
QA_PROVISIONAL = "暫定反映"
QA_NO_ANSWER = "未回答"
QA_NO_RECOMMENDATION = "なし"
QA_MIGRATION = "spec-loop の references/tree.md の「Q&A 表を移す」"
QA_OPTION_SEPARATOR = " / "

QA_PAGE = "qa.md"
# 起票元ごとの番号の印（`Q-S-001`。#278）。印の無い前の形の番号（`Q-001`）もリンクにする
QA_MARKS = "RSFD"
QA_NUMBER = re.compile(rf"(?<![A-Za-z0-9_-])Q-(?:[{QA_MARKS}]-)?[0-9]{{3,}}(?![A-Za-z0-9_-])")
# HTML の、文字でないもの: コメント・CDATA・宣言と処理命令・タグ（属性の値の中の > で切らない）。group(1) は終わりの /、group(2) は要素名
MARKUP = re.compile(r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<[!?][^>]*>"
                    r"|<(/?)([A-Za-z][A-Za-z0-9-]*)(?:\"[^\"]*\"|'[^']*'|[^'\">])*>", re.DOTALL)
# 中の文字を変えない要素
UNLINKED = {"a", "code", "pre", "kbd", "samp", "script", "style", "textarea", "title", "h1", "h2", "h3", "h4", "h5", "h6"}
# Q&A 表のページ（on_page_markdown が印を見て記録し、on_page_content が飛ばす）
qa_pages: set[str] = set()
MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]{}#|])")
ANCHOR_UNSAFE = re.compile(r"[^a-z0-9_-]+")


def text(value: str) -> str:
    """セル・本文に置く文字。HTML と Markdown の記号をエスケープし、改行を <br> にする。"""
    escaped = html.escape(value.replace("\r\n", "\n").replace("\r", "\n"), quote=False)
    return MARKDOWN_SPECIAL.sub(r"\\\1", escaped).replace("\n", "<br>")


def anchor(version: int, number: str) -> str:
    """見出しの `{#…}` とリンクの `(#…)` に置く名前。使えない文字は `-` にする（空白・`}` で属性が割れないように）。"""
    return f"v{version}-" + ANCHOR_UNSAFE.sub("-", number.lower())


def versions(docs_dir: Path) -> list[tuple[int, Path]]:
    found = []
    for entry in docs_dir.iterdir():
        if VERSION.fullmatch(entry.name) and entry.is_dir():
            found.append((int(entry.name[1:]), entry))
    return sorted(found)


def problem(message: str) -> str:
    log.warning("spec-loop: %s", message)
    return f'!!! warning "表示できない"\n\n    {text(message)}\n'


def read_qa(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != QA_COLUMNS:
            hint = f"。推奨の列が無い——前の形の表なら、移す手順は {QA_MIGRATION}" if header and "推奨" not in header else ""
            raise ValueError(f"見出しの行が列名（{','.join(QA_COLUMNS)}）と違う: {header}{hint}")
        # 空白だけの行は空行として読み飛ばす（check-qa-csv.py と同じ）
        return [dict(zip(QA_COLUMNS, row + [""] * (len(QA_COLUMNS) - len(row))))
                for row in reader if any(cell.strip() for cell in row)]


def qa_is_provisional(row: dict[str, str]) -> bool:
    """暫定の行か——check-qa-csv.py の is_provisional の写し（状態だけで決め、回答の文言は見ない。テストが試料で突き合わせる）。"""
    return row["状態"].strip() == QA_PROVISIONAL


def qa_section(version: int, rows: list[dict[str, str]]) -> list[str]:
    # 状態は前後の空白を落として比べる——qa_is_provisional と揃える（片方だけ落とすと 3 つの件数が食い違う）
    done = sum(row["状態"].strip() == QA_DONE for row in rows)
    # 暫定の回答で反映した行は、反映済みでも確認中でもない（仕様には反映済み・利用者の確認待ち）
    provisional = sum(qa_is_provisional(row) for row in rows)
    pending = len(rows) - done - provisional
    answered = sum(row["状態"].strip() != QA_DONE and not qa_is_provisional(row) and row["回答"].strip() not in ("", QA_NO_ANSWER)
                   for row in rows)
    out = [f"## v{version}", "",
           f"確認中 {pending} 件（うち回答あり・未反映 {answered} 件）・暫定反映 {provisional} 件・反映済み {done} 件", ""]
    if not rows:
        return out + ["質問はまだ無い。", ""]
    out += ["| No | 質問 | 推奨 | 回答 | 状態 |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        out.append(f"| [{text(row['No'])}](#{anchor(version, row['No'])}) | {text(row['質問'])} "
                   f"| {text(row['推奨'])} | {text(row['回答'])} | {text(row['状態'])} |")
    out.append("")
    for row in rows:
        recommended = row["推奨"].strip()
        options = "<br>".join(f"**{text(option)}**（推奨）" if option.split(":", 1)[0].strip() == recommended
                              else text(option) for option in row["選択肢"].split(QA_OPTION_SEPARATOR))
        reason = "推奨なし" if recommended == QA_NO_RECOMMENDATION else "推奨の理由"
        out += [f"### {text(row['No'])} {{#{anchor(version, row['No'])}}}", "",
                "| 項目 | 内容 |", "| --- | --- |", f"| 質問 | {text(row['質問'])} |", f"| 選択肢 | {options} |",
                f"| {reason} | {text(row['推奨の理由'])} |"]
        out += [f"| {name} | {text(row[name])} |" for name in ("回答", "反映先", "状態", "起票元")]
        if row["費用への影響"].strip():
            out.append(f"| 費用への影響 | {text(row['費用への影響'])} |")
        out.append("")
    return out


def render_qa(docs_dir: Path) -> str:
    out: list[str] = []
    for version, root in versions(docs_dir):
        path = root / "shared" / "qa.csv"
        if not path.is_file():
            continue
        try:
            rows = read_qa(path)
        except (OSError, UnicodeDecodeError, csv.Error, ValueError) as e:
            out += [problem(f"{path.relative_to(docs_dir)}: {e}"), ""]
            continue
        out += qa_section(version, rows)
    if not out:
        return "Q&A 表（`docs/v<n>/shared/qa.csv`）はまだ無い。\n"
    return "\n".join(out)


RENDERERS = {
    "qa": render_qa,
}


def qa_numbers(docs_dir: Path) -> list[tuple[int, set[str]]]:
    """版ごとの Q&A 表の番号。読めない表は空（警告は Q&A 表のページを描くときに出る）。"""
    found = []
    for version, root in versions(docs_dir):
        path = root / "shared" / "qa.csv"
        if path.is_file():
            try:
                # 空白を落とさない——Q&A 表のアンカーも落とさずに作るので、落とすとリンクがアンカーに当たらない（警告に回す）
                found.append((version, {row["No"] for row in read_qa(path)}))
            except (OSError, ValueError, csv.Error):  # UnicodeDecodeError は ValueError の子
                found.append((version, set()))
    return found


def link_numbers(content: str, src_path: str, target: str, docs_dir: Path) -> str:
    """描いた HTML の文字の中の Q&A の番号を、`target`（Q&A 表のページの URL）のアンカーへのリンクにする。"""
    top = src_path.split("/", 1)[0]
    limit = int(top[1:]) if VERSION.fullmatch(top) and "/" in src_path else None
    tables = [(version, numbers) for version, numbers in qa_numbers(docs_dir) if limit is None or version <= limit]
    scope = (f"v1〜v{limit} のどの版" if limit is not None else "どの版") + "の Q&A 表"
    unknown: list[str] = []

    def link(match: re.Match) -> str:
        number = match.group(0)
        version = next((version for version, numbers in reversed(tables) if number in numbers), None)
        if version is None:
            if number not in unknown:
                unknown.append(number)
            return number
        return f'<a href="{html.escape(target + "#" + anchor(version, number))}">{number}</a>'

    out, last = [], 0
    inside = {name: 0 for name in UNLINKED}  # 開いている要素の数（入れ子・閉じ忘れの多い HTML でも数で追う）
    for match in MARKUP.finditer(content):
        between = content[last:match.start()]
        out += [between if any(inside.values()) else QA_NUMBER.sub(link, between), match.group(0)]
        last = match.end()
        name = (match.group(2) or "").lower()
        if name in inside and not match.group(0).endswith("/>"):
            inside[name] = max(inside[name] - 1, 0) if match.group(1) else inside[name] + 1
    between = content[last:]
    out.append(between if any(inside.values()) else QA_NUMBER.sub(link, between))
    for number in unknown:
        log.warning("spec-loop: %s: %s は %sにも無いので、リンクにしない（読めない表は数えない）",
                    src_path, number, scope)
    return "".join(out)


def page_path(page) -> str:
    return getattr(page.file, "src_uri", page.file.src_path).replace("\\", "/")


def on_page_markdown(markdown: str, page, config, files) -> str:
    docs_dir = Path(config["docs_dir"])

    def replace(match: re.Match) -> str:
        name = match.group("name")
        renderer = RENDERERS.get(name)
        if renderer is None:
            return problem(f"{page.file.src_path}: 知らない印 `spec-loop: {name}`（知っているのは {', '.join(RENDERERS)}）")
        return renderer(docs_dir)

    if any(match.group("name") == "qa" for match in MARKER.finditer(markdown)):
        qa_pages.add(page_path(page))
    else:
        qa_pages.discard(page_path(page))
    return MARKER.sub(replace, markdown)


def on_page_content(content: str, page, config, files) -> str:
    src_path = page_path(page)
    qa = files.get_file_from_path(QA_PAGE)
    if src_path in qa_pages or qa is None:
        return content
    return link_numbers(content, src_path, qa.url_relative_to(page.file), Path(config["docs_dir"]))
