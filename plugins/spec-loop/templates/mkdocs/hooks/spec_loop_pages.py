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
- 描くものを足すときは、描画関数を書いて `RENDERERS` に足す。
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
QA_COLUMNS = ["No", "起票元", "質問", "選択肢", "回答", "反映先", "状態", "費用への影響"]
QA_DONE = "反映済み"
QA_NO_ANSWER = "未回答"
QA_OPTION_SEPARATOR = " / "

MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]#|])")


def text(value: str) -> str:
    """セル・本文に置く文字。HTML と Markdown の記号をエスケープし、改行を <br> にする。"""
    escaped = html.escape(value.replace("\r\n", "\n").replace("\r", "\n"), quote=False)
    return MARKDOWN_SPECIAL.sub(r"\\\1", escaped).replace("\n", "<br>")


def anchor(version: int, number: str) -> str:
    return f"v{version}-{number.lower()}"


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
        return [dict(zip(QA_COLUMNS, row + [""] * (len(QA_COLUMNS) - len(row)))) for row in reader if row]


def qa_section(version: int, rows: list[dict[str, str]]) -> list[str]:
    done = sum(row["状態"] == QA_DONE for row in rows)
    pending = len(rows) - done
    answered = sum(row["状態"] != QA_DONE and row["回答"] != QA_NO_ANSWER for row in rows)
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
        out += [f"### {text(row['No'])} {{#{anchor(version, row['No'])}}}", "", text(row["質問"]), ""]
        out += [f"- {text(option)}" for option in row["選択肢"].split(QA_OPTION_SEPARATOR)]
        out += ["", "| 項目 | 内容 |", "| --- | --- |"]
        out += [f"| {name} | {text(row[name])} |" for name in ("回答", "反映先", "状態", "起票元")]
        out.append("")
        if row["費用への影響"].strip():
            out += ['!!! note "費用への影響"', "", f"    {text(row['費用への影響'])}", ""]
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


def on_page_markdown(markdown: str, page, config, files) -> str:
    docs_dir = Path(config["docs_dir"])

    def replace(match: re.Match) -> str:
        name = match.group("name")
        renderer = RENDERERS.get(name)
        if renderer is None:
            return problem(f"{page.file.src_path}: 知らない印 `spec-loop: {name}`（知っているのは {', '.join(RENDERERS)}）")
        return renderer(docs_dir)

    return MARKER.sub(replace, markdown)
