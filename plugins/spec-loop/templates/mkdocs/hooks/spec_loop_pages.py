"""spec-loop の表示用ページを作る MkDocs のフック（spec-loop の雛形。init-mkdocs.py が写した）。

ページに印 `<!-- spec-loop: <名前> -->` を書くと、`on_page_markdown` がその場所を描画関数の出力に置き換える。
**正本は CSV のまま**——ページに表を書き写さない。標準ライブラリだけで動く（正本リポジトリへ写されて単独で動く）。

| 印 | 描くもの |
| --- | --- |
| `qa` | 各版の `docs/v<n>/shared/qa.csv` を、版ごとの節に（件数・一覧・質問ごとの詳細） |

- **版は重ね合わせない。** v2 で同じ `No` の行を置いて問い直した質問は、v1 と v2 の両方の節に出る。
  アンカーは `v<n>-q-001` の形で、版をまたいで一意。
- **読めない表・見出しが列名と違う表・知らない印は、警告を出し、ページにも注意書きを置く。**
  警告は `mkdocs` のロガーに出すので、`mkdocs build --strict` は落ちる（黙って空の表を出さない）。
- **列の決まりの検査はしない**——それは spec-loop の `check-qa-csv.py` の仕事。ここが見るのは見出しの行だけ。
- セルの文字は HTML と Markdown の記号をエスケープし、改行は `<br>` にする（表を壊さない）。
  **CSV の文字は表のセルにだけ置く**——段落や箇条書きに置くと、行頭の `!!! `・字下げ・`1. ` がブロックの記法に読まれる。
- 描くものを足すときは、描画関数を書いて `RENDERERS` に足す。

**本文の Q&A の番号（`Q-008`）は、Q&A 表のページ（`qa.md`）のアンカーへのリンクにする**（正本は番号のまま。
決まりは spec-loop の `references/qa-csv.md` の「本文での番号」）。印を展開した後に掛けるので、描画関数が描いた表のセルにも掛かる。

- 版は、`docs/v<n>/` の下のページなら `v1`〜`v<n>` のうち、版の外のページならすべての版のうち、
  **その番号を持つ最も新しい版**（版は重ね合わせないので、問い直していない番号は前の版の節にしか無い）。
- **どの版の Q&A 表にも無い番号はリンクにせず警告する**（打ち間違いを拾う）。
- 置き換えないところ: 見出し・フェンス・インラインのコード・`[…]` の中と直後の `(…)`・HTML のタグとコメント・
  自動リンク・URL・Q&A 表のページ（`qa` の印を持つページ）。`qa.md` が無ければ何もしない。
- **字下げ（4 文字）のコードブロックは見分けない**——アドモニションや箇条書きの続きと区別できないので、中の番号もリンクになる。
  コードはフェンスで書く。
"""

from __future__ import annotations

import csv
import html
import logging
import posixpath
import re
from pathlib import Path

log = logging.getLogger("mkdocs.hooks.spec_loop_pages")

MARKER = re.compile(r"<!--\s*spec-loop:\s*(?P<name>[A-Za-z0-9_-]+)\s*-->")
VERSION = re.compile(r"v[1-9][0-9]*")

# spec-loop の references/qa-csv.md の列（check-qa-csv.py の COLUMNS と同じ。写しなので、テストが突き合わせる）
QA_COLUMNS = ["No", "起票元", "質問", "選択肢", "回答", "反映先", "状態", "費用への影響"]
QA_DONE = "反映済み"
QA_NO_ANSWER = "未回答"
QA_OPTION_SEPARATOR = " / "

QA_PAGE = "qa.md"
QA_NUMBER = re.compile(r"(?<![A-Za-z0-9_-])Q-[0-9]{3,}(?![A-Za-z0-9_])")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
ATX_HEADING = re.compile(r" {0,3}#{1,6}(?:[ \t]|$)")
SETEXT_UNDERLINE = re.compile(r" {0,3}(?:=+|-+)[ \t]*$")
# 番号を置き換えない範囲（行をまたぐのは空行までの段落の中だけ）。順に: インラインのコード・HTML のコメント・<a> の中・
# タグと自動リンク・[…] と直後の (…) か […]・URL
PROTECTED = re.compile(
    r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)"
    r"|<!--.*?-->"
    r"|<a\b.*?</a>"
    r"|<[A-Za-z/!][^>]*>"
    r"|(?<!\\)!?\[(?:\\.|[^\]\\])*\](?:\([^)]*\)|\[[^\]]*\])?"
    r"|https?://\S+",
    re.DOTALL | re.IGNORECASE)
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
            raise ValueError(f"見出しの行が列名（{','.join(QA_COLUMNS)}）と違う: {header}")
        # 空白だけの行は空行として読み飛ばす（check-qa-csv.py と同じ）
        return [dict(zip(QA_COLUMNS, row + [""] * (len(QA_COLUMNS) - len(row))))
                for row in reader if any(cell.strip() for cell in row)]


def qa_section(version: int, rows: list[dict[str, str]]) -> list[str]:
    done = sum(row["状態"] == QA_DONE for row in rows)
    pending = len(rows) - done
    answered = sum(row["状態"] != QA_DONE and row["回答"].strip() not in ("", QA_NO_ANSWER) for row in rows)
    out = [f"## v{version}", "",
           f"確認中 {pending} 件（うち回答あり・未反映 {answered} 件）・反映済み {done} 件", ""]
    if not rows:
        return out + ["質問はまだ無い。", ""]
    out += ["| No | 質問 | 回答 | 状態 |", "| --- | --- | --- | --- |"]
    for row in rows:
        out.append(f"| [{text(row['No'])}](#{anchor(version, row['No'])}) | {text(row['質問'])} "
                   f"| {text(row['回答'])} | {text(row['状態'])} |")
    out.append("")
    for row in rows:
        options = "<br>".join(text(option) for option in row["選択肢"].split(QA_OPTION_SEPARATOR))
        out += [f"### {text(row['No'])} {{#{anchor(version, row['No'])}}}", "",
                "| 項目 | 内容 |", "| --- | --- |", f"| 質問 | {text(row['質問'])} |", f"| 選択肢 | {options} |"]
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
                found.append((version, {row["No"].strip() for row in read_qa(path)}))
            except (OSError, ValueError, csv.Error):  # UnicodeDecodeError は ValueError の子
                found.append((version, set()))
    return found


def link_numbers(markdown: str, src_path: str, docs_dir: Path) -> str:
    """本文の Q&A の番号を Q&A 表のアンカーへのリンクにする（置き換えないところはモジュールの docstring）。"""
    if not (docs_dir / QA_PAGE).is_file():
        return markdown
    top = src_path.split("/", 1)[0]
    limit = int(top[1:]) if VERSION.fullmatch(top) and "/" in src_path else None
    tables = [(version, numbers) for version, numbers in qa_numbers(docs_dir) if limit is None or version <= limit]
    target = posixpath.relpath(QA_PAGE, posixpath.dirname(src_path) or ".")
    unknown: list[str] = []

    def link(match: re.Match) -> str:
        number = match.group(0)
        version = next((version for version, numbers in reversed(tables) if number in numbers), None)
        if version is None:
            if number not in unknown:
                unknown.append(number)
            return number
        return f"[{number}]({target}#{anchor(version, number)})"

    def paragraph(lines: list[str]) -> str:
        block = "".join(lines)
        out, last = [], 0
        for match in PROTECTED.finditer(block):
            out += [QA_NUMBER.sub(link, block[last:match.start()]), match.group(0)]
            last = match.end()
        out.append(QA_NUMBER.sub(link, block[last:]))
        return "".join(out)

    lines = markdown.splitlines(keepends=True)
    out: list[str] = []
    pending: list[str] = []
    fence = ""
    for index, line in enumerate(lines):
        if fence:
            out.append(line)
            closing = FENCE.match(line)
            if closing and closing.group(1)[0] == fence[0] and len(closing.group(1)) >= len(fence) \
                    and not line[closing.end():].strip():
                fence = ""
            continue
        opening = FENCE.match(line)
        following = lines[index + 1] if index + 1 < len(lines) else ""
        # 空行でも段落を切る（閉じない ` が次の段落の ` と組まないように）
        if opening or not line.strip() or ATX_HEADING.match(line) or SETEXT_UNDERLINE.match(following):
            out.append(paragraph(pending))
            pending = []
            out.append(line)
            fence = opening.group(1) if opening else ""
            continue
        pending.append(line)
    out.append(paragraph(pending))
    for number in unknown:
        log.warning("spec-loop: %s: %s はどの版の Q&A 表にも無いので、リンクにしない", src_path, number)
    return "".join(out)


def on_page_markdown(markdown: str, page, config, files) -> str:
    docs_dir = Path(config["docs_dir"])

    def replace(match: re.Match) -> str:
        name = match.group("name")
        renderer = RENDERERS.get(name)
        if renderer is None:
            return problem(f"{page.file.src_path}: 知らない印 `spec-loop: {name}`（知っているのは {', '.join(RENDERERS)}）")
        return renderer(docs_dir)

    src_path = getattr(page.file, "src_uri", page.file.src_path).replace("\\", "/")
    is_qa_page = any(match.group("name") == "qa" for match in MARKER.finditer(markdown))
    markdown = MARKER.sub(replace, markdown)
    return markdown if is_qa_page else link_numbers(markdown, src_path, docs_dir)
