#!/usr/bin/env python3
"""Q&A 表（`qa.csv`）から、レビュー会用の PPTX を作る。

usage: python3 qa-to-pptx.py <qa.csv> <出力.pptx> [--title <表紙の題>] [--subtitle <表紙の副題>]

**載せるのは、利用者にまだ見せる行だけ**——`状態` が `check-qa-csv.py` の
`DONE` でない行である（状態の意味は `references/qa-csv.md` を正とする）。回答待ち・回答はあるが未反映の行に加えて、
**暫定の回答で反映した行（`PROVISIONAL`）も載る**——確認してもらうため。
**状態の名前を列挙して絞らない**——決まりに状態が増えても、確認が残っている行を黙って落とさない。
表紙・一覧・1 問 1 枚の順に並べる。**表紙の件数と各問の回答の見出しは、未反映と暫定で分ける**
（暫定の行を「未反映」と書かない——仕様には反映済みなので）。

**列の決まりは同じディレクトリの `check-qa-csv.py` から読み込む**（定数を写さない）。
決まりの正は `references/qa-csv.md` である（このプラグインの中にある）。
**列検査を通らない表からは作らない**——検査と同じ出力を出して 1 で終わる。

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う
（`zipfile` と XML の文字列で OOXML を直接書く）。

**出力は入力と引数だけで決まる**（zip の時刻を固定し、日付を埋め込まない）。
日付を表紙に入れたいなら `--subtitle` で渡す。

終了コード:

- 0: 作った（載せた質問の数を、回答待ち・未反映と暫定に分けて出す）
- 1: 列検査を通らない（**出力は作らない。既存の出力にも触らない**）
- 2: 引数の誤り・表が読めない・**出力先が入力の表と同じファイル**（**同上**）
- 3: 出力を書けなかった（**既存の出力は残る**——一時ファイルに書いてから置き換える）

出力先の親ディレクトリが無ければ作る（既定の出力先 `build/req-loop/` は、
初回には無いのがふつうである。`references/tree.md`）。

**この生成が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **文字がスライドからはみ出さないこと** | 文字の幅を測る手段が標準ライブラリに無い。枠には自動縮小の指定を付けるが、効くかはアプリ次第 |
| **見た目の作り込み**（配色・ロゴ・テンプレート） | 形式の指定は対象リポジトリの `CLAUDE.md` に任せる（`references/tree.md`） |
| **すべてのアプリで開けること** | 確かめたのは macOS の PowerPoint と LibreOffice だけ |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_qa_csv", HERE / "check-qa-csv.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


qa = _load_checker()


# 16:9（EMU）
SLIDE_W, SLIDE_H = 12192000, 6858000
MARGIN = 457200
INDEX_PER_SLIDE = 10
ZIP_TIME = (1980, 1, 1, 0, 0, 0)

# XML 1.0 に書けない文字（タブ・改行・復帰を除く制御文字など）
INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")

NS = (
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
)
DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "application/vnd.openxmlformats-officedocument"


# ---------------------------------------------------------------- 表を読む

def read_rows(path: Path) -> tuple[int, list[str], list[dict[str, str]]]:
    """(終了コード, 出力する行, 全部の行) を返す。検査を通らなければ行は空。

    `check-spec-exit.py` もこの関数で読む（絞り方は向こうが決める——載せる行と、反映が残っている行は別の定義）。
    """
    code, lines = qa.check(path)
    if code:
        return code, lines, []
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""))
    next(reader)
    rows = []
    for fields in reader:
        if not any(f.strip() for f in fields):
            continue
        rows.append(dict(zip(qa.COLUMNS, fields)))
    return 0, lines, rows


def read_pending(path: Path) -> tuple[int, list[str], list[dict[str, str]]]:
    """(終了コード, 出力する行, `DONE` でない行＝資料に載せる行) を返す。検査を通らなければ行は空。"""
    code, lines, rows = read_rows(path)
    return code, lines, [row for row in rows if row["状態"].strip() != qa.DONE]


def provisional(row: dict[str, str]) -> bool:
    return row["状態"].strip() == qa.PROVISIONAL


# ---------------------------------------------------------------- XML の部品

def clean(text: str) -> str:
    return escape(INVALID_XML.sub("", text))


def paragraph(text: str, size: int, bold: bool = False, indent: int = 0) -> str:
    ppr = f'<a:pPr marL="{indent}"/>' if indent else ""
    b = ' b="1"' if bold else ""
    if not text:
        return f'<a:p>{ppr}<a:endParaRPr lang="ja-JP" sz="{size}"/></a:p>'
    return (f'<a:p>{ppr}<a:r><a:rPr lang="ja-JP" sz="{size}"{b} dirty="0"/>'
            f'<a:t>{clean(text)}</a:t></a:r></a:p>')


def split_lines(text: str) -> list[str]:
    """改行だけで割る。**`str.splitlines()` は使わない**——U+2028 や垂直タブでも割るので、
    Web から貼った質問が段落に化ける（`check-qa-csv.py` が `csv` に渡す前に避けている罠と同じ）。"""
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def lines_of(text: str, size: int, bold: bool = False, indent: int = 0) -> list[str]:
    """セルの中の改行は段落に分ける（`<a:t>` の中の改行は表示されない）。"""
    return [paragraph(t, size, bold, indent) for t in split_lines(text)]


def textbox(shape_id: int, name: str, x: int, y: int, w: int, h: int, paras: list[str]) -> str:
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        '<p:txBody><a:bodyPr wrap="square" anchor="t"><a:normAutofit/></a:bodyPr><a:lstStyle/>'
        + "".join(paras) + "</p:txBody></p:sp>"
    )


GROUP = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
         '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
         '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')


def slide(title: list[str], body: list[str]) -> str:
    w = SLIDE_W - 2 * MARGIN
    shapes = textbox(2, "Title", MARGIN, MARGIN, w, 1000000, title)
    if body:
        shapes += textbox(3, "Body", MARGIN, MARGIN + 1100000, w, SLIDE_H - 2 * MARGIN - 1100000, body)
    return (DECL + f"<p:sld {NS}><p:cSld><p:spTree>{GROUP}{shapes}</p:spTree></p:cSld>"
            "<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>")


# ---------------------------------------------------------------- スライドの中身

def cover(title: str, subtitle: str, rows: list[dict[str, str]]) -> str:
    settled = sum(provisional(row) for row in rows)
    body = lines_of(f"回答待ち・未反映の質問: {len(rows) - settled} 件", 2400)
    body += lines_of(f"暫定の回答（反映済み・確認待ち）: {settled} 件", 2400)
    if subtitle:
        body = lines_of(subtitle, 2000) + body
    return slide(lines_of(title, 4000, bold=True), body)


def index_slides(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return [slide(lines_of("一覧", 3200, bold=True), lines_of("載せる質問はありません", 2000))]
    chunks = [rows[i:i + INDEX_PER_SLIDE] for i in range(0, len(rows), INDEX_PER_SLIDE)]
    out = []
    for n, chunk in enumerate(chunks, 1):
        head = "一覧" if len(chunks) == 1 else f"一覧（{n}/{len(chunks)}）"
        body = []
        for row in chunk:
            first = split_lines(row["質問"])[0]
            mark = "（暫定）" if provisional(row) else ""
            body += lines_of(f"{row['No']}{mark}  {first}", 1600)
        out.append(slide(lines_of(head, 3200, bold=True), body))
    return out


def question_slide(row: dict[str, str]) -> str:
    title = lines_of(f"{row['No']}（{row['起票元']}）", 2800, bold=True)
    body = lines_of(row["質問"], 2200, bold=True) + [paragraph("", 1200)]
    for option in row["選択肢"].split(qa.OPTION_SEPARATOR):
        body += lines_of(option.strip(), 2000, indent=342900)
    if row["費用への影響"].strip():
        body += [paragraph("", 1200)] + lines_of(f"費用への影響: {row['費用への影響']}", 1600)
    if provisional(row):
        body += [paragraph("", 1200)] + lines_of(f"暫定の回答（反映済み・確認待ち）: {row['回答']}", 1600)
        body += lines_of(f"反映先: {row['反映先']}", 1600)
    elif row["回答"].strip() != qa.NO_ANSWER:
        body += [paragraph("", 1200)] + lines_of(f"回答（未反映）: {row['回答']}", 1600)
    return slide(title, body)


# ---------------------------------------------------------------- パッケージ

THEME = (
    DECL + '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="spec-loop">'
    '<a:themeElements><a:clrScheme name="spec-loop">'
    '<a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
    '<a:dk2><a:srgbClr val="1F2937"/></a:dk2><a:lt2><a:srgbClr val="F3F4F6"/></a:lt2>'
    '<a:accent1><a:srgbClr val="2563EB"/></a:accent1><a:accent2><a:srgbClr val="DC2626"/></a:accent2>'
    '<a:accent3><a:srgbClr val="16A34A"/></a:accent3><a:accent4><a:srgbClr val="CA8A04"/></a:accent4>'
    '<a:accent5><a:srgbClr val="7C3AED"/></a:accent5><a:accent6><a:srgbClr val="0891B2"/></a:accent6>'
    '<a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink>'
    '</a:clrScheme><a:fontScheme name="spec-loop">'
    '<a:majorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
    '<a:minorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
    '</a:fontScheme><a:fmtScheme name="spec-loop">'
    '<a:fillStyleLst>' + '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>' * 3 + '</a:fillStyleLst>'
    '<a:lnStyleLst>' + '<a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>' * 3
    + '</a:lnStyleLst>'
    '<a:effectStyleLst>' + '<a:effectStyle><a:effectLst/></a:effectStyle>' * 3 + '</a:effectStyleLst>'
    '<a:bgFillStyleLst>' + '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>' * 3 + '</a:bgFillStyleLst>'
    '</a:fmtScheme></a:themeElements></a:theme>'
)

MASTER = (
    DECL + f"<p:sldMaster {NS}><p:cSld>"
    '<p:bg><p:bgPr><a:solidFill><a:schemeClr val="bg1"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
    f"<p:spTree>{GROUP}</p:spTree></p:cSld>"
    '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
    'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
    '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
    '<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="3200"/></a:lvl1pPr></p:titleStyle>'
    '<p:bodyStyle><a:lvl1pPr><a:defRPr sz="2000"/></a:lvl1pPr></p:bodyStyle>'
    '<p:otherStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:otherStyle></p:txStyles>'
    "</p:sldMaster>"
)

LAYOUT = (
    DECL + f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank">'
    f"<p:spTree>{GROUP}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>"
)


def rels(items: list[tuple[str, str]]) -> str:
    body = "".join(
        f'<Relationship Id="rId{i}" Type="{t}" Target="{target}"/>'
        for i, (t, target) in enumerate(items, 1)
    )
    return (DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + body + "</Relationships>")


def package(slides: list[str], title: str) -> list[tuple[str, str]]:
    """(zip の中のパス, 中身) を、書く順に返す。"""
    n = len(slides)
    types = (
        DECL + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'<Override PartName="/ppt/presentation.xml" ContentType="{CT}.presentationml.presentation.main+xml"/>'
        f'<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="{CT}.presentationml.slideMaster+xml"/>'
        f'<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="{CT}.presentationml.slideLayout+xml"/>'
        f'<Override PartName="/ppt/theme/theme1.xml" ContentType="{CT}.theme+xml"/>'
        f'<Override PartName="/ppt/presProps.xml" ContentType="{CT}.presentationml.presProps+xml"/>'
        f'<Override PartName="/ppt/viewProps.xml" ContentType="{CT}.presentationml.viewProps+xml"/>'
        f'<Override PartName="/ppt/tableStyles.xml" ContentType="{CT}.presentationml.tableStyles+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        f'<Override PartName="/docProps/app.xml" ContentType="{CT}.extended-properties+xml"/>'
        + "".join(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="{CT}.presentationml.slide+xml"/>'
                  for i in range(1, n + 1))
        + "</Types>"
    )
    root_rels = rels([
        (f"{REL}/officeDocument", "ppt/presentation.xml"),
        ("http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
        (f"{REL}/extended-properties", "docProps/app.xml"),
    ])
    fixed = [
        (f"{REL}/slideMaster", "slideMasters/slideMaster1.xml"),
        (f"{REL}/presProps", "presProps.xml"),
        (f"{REL}/viewProps", "viewProps.xml"),
        (f"{REL}/theme", "theme/theme1.xml"),
        (f"{REL}/tableStyles", "tableStyles.xml"),
    ]
    pres_rels = rels(fixed + [(f"{REL}/slide", f"slides/slide{i}.xml") for i in range(1, n + 1)])
    sld_ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{len(fixed) + i}"/>' for i in range(1, n + 1))
    presentation = (
        DECL + f'<p:presentation {NS} saveSubsetFonts="1">'
        '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        f"<p:sldIdLst>{sld_ids}</p:sldIdLst>"
        f'<p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}"/><p:notesSz cx="6858000" cy="9144000"/>'
        "</p:presentation>"
    )
    core = (
        DECL + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<dc:title>{clean(title)}</dc:title><dc:creator>spec-loop req-loop</dc:creator></cp:coreProperties>"
    )
    app = (
        DECL + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        f"<Application>spec-loop</Application><Slides>{n}</Slides></Properties>"
    )
    layout_rel = rels([(f"{REL}/slideLayout", "../slideLayouts/slideLayout1.xml")])
    parts = [
        ("[Content_Types].xml", types),
        ("_rels/.rels", root_rels),
        ("docProps/core.xml", core),
        ("docProps/app.xml", app),
        ("ppt/presentation.xml", presentation),
        ("ppt/_rels/presentation.xml.rels", pres_rels),
        ("ppt/presProps.xml", DECL + f"<p:presentationPr {NS}/>"),
        ("ppt/viewProps.xml", DECL + f"<p:viewPr {NS}/>"),
        ("ppt/tableStyles.xml", DECL + '<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                                       'def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>'),
        ("ppt/theme/theme1.xml", THEME),
        ("ppt/slideMasters/slideMaster1.xml", MASTER),
        ("ppt/slideMasters/_rels/slideMaster1.xml.rels",
         rels([(f"{REL}/slideLayout", "../slideLayouts/slideLayout1.xml"), (f"{REL}/theme", "../theme/theme1.xml")])),
        ("ppt/slideLayouts/slideLayout1.xml", LAYOUT),
        ("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
         rels([(f"{REL}/slideMaster", "../slideMasters/slideMaster1.xml")])),
    ]
    for i, body in enumerate(slides, 1):
        parts.append((f"ppt/slides/slide{i}.xml", body))
        parts.append((f"ppt/slides/_rels/slide{i}.xml.rels", layout_rel))
    return parts


def build(rows: list[dict[str, str]], title: str, subtitle: str) -> list[tuple[str, str]]:
    slides = [cover(title, subtitle, rows)] + index_slides(rows) + [question_slide(r) for r in rows]
    return package(slides, title)


def write(parts: list[tuple[str, str]], out: Path) -> None:
    """一時ファイルに書いてから置き換える（途中で失敗しても既存の出力は残る）。"""
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out.parent, prefix=f".{out.name}.", suffix=".tmp")
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for name, body in parts:
                info = zipfile.ZipInfo(name, date_time=ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, body.encode("utf-8"))
        os.replace(tmp, out)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------- 入口

def parse(argv: list[str]) -> tuple[Path, Path, str, str] | None:
    args, opts = [], {"--title": "レビュー会の確認事項", "--subtitle": ""}
    it = iter(argv)
    for a in it:
        if a in opts:
            value = next(it, None)
            if value is None:
                return None
            opts[a] = value
        elif a.startswith("--"):
            return None
        else:
            args.append(a)
    if len(args) != 2:
        return None
    return Path(args[0]), Path(args[1]), opts["--title"], opts["--subtitle"]


def main(argv: list[str]) -> int:
    parsed = parse(argv)
    if parsed is None:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    src, out, title, subtitle = parsed
    # **出力先が入力の表そのものなら書かない**——置き換えで正本の表が PPTX になり、戻せない。
    if out.exists() and src.exists() and out.samefile(src):
        print(f"{out}: 入力の表と同じファイルなので書かない", file=sys.stderr)
        return 2
    code, lines, rows = read_pending(src)
    if code:
        for line in lines:
            print(line, file=sys.stderr)
        print(f"{src}: 列検査を通らないので PPTX を作らない", file=sys.stderr)
        return code
    try:
        write(build(rows, title, subtitle), out)
    except OSError as e:
        print(f"{out}: 書けない（{e.strerror}）。既存の出力には触っていない", file=sys.stderr)
        return 3
    settled = sum(provisional(row) for row in rows)
    print(f"{out}: 質問 {len(rows)} 件を載せた（回答待ち・未反映 {len(rows) - settled} 件・暫定の回答 {settled} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
