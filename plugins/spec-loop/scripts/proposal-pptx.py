#!/usr/bin/env python3
"""提案書・仕様書の PPTX の既定のデザイン（#1289）。**実行しない**——`build-proposal.py` が読み込む（`--pptx`）。

決裁者にそのまま渡せる体裁にするため、Markdown を見出しごとに流し込むのをやめ、**材料（表・手書き部分・図）から枚を組む**:

- **手書き部分**: 太字の見出しの行ごとにカードにし、同じ枚のカードは**収まる範囲でいちばん大きい同じ文字の大きさ**にそろえる
  （3 枚は横 3 列、4 枚は 2 × 2、5・6 枚は 3 列 × 2 段）。スライドでは参照の括弧（Q&A の番号・ファイルのパス）を外す（全文は `proposal.md`）。
- **費用**: 開発費と運用費を別のページにし、行が増えたら**枚数で受ける**（重ねない・見切れさせない）。根拠は計算式だけを出し、
  内部の番号だけの根拠は出さず（`—`）、式が長すぎる行は根拠を出さずに「全文は proposal.md」と書く。
- **期間**: ガントチャートを図形で描く（工程名の列・棒の横に日付・月の見出し・休みの網掛け・節目の ◆）。**工程の表の枚は作らない**（日付が図に載る）。
- **利用者と決めたこと**: 全件は別紙の表（`decisions.xlsx`）に出し、提案書には**概要の 1 枚**（件数・推奨どおりか・起票元・テーマごとの件数）と、
  **範囲を決めた質問の 1 枚**（質問と選んだ選択肢の中身を大きく）だけを載せる。
- **図**（仕様書）: SVG を PNG にして載せる（`rsvg-convert`。環境変数 `SPEC_LOOP_RSVG` で別の道具に差し替えられる）。drawio の代わりの文字
  （`Text is not SVG - cannot display`）は PNG にするときに消す（正本の SVG は変えない）。**見出しはファイル名ではなく、図の中の名前か読める名前**にする。
  道具が無ければ図を載せず、その旨を 1 枚に書き、呼び出し元が標準エラーに知らせる（確かめられていないことを隠さない）。
- **仕様書**: 範囲の外は理由だけにし、ファイルの一覧は場所ごとの件数と主なファイルの 1 枚にまとめ、値の無い規模の行は出さない。

**省略記号（`…`）で文字を切らない**——入りきらない文は、行を増やす・文字を小さくする・枚を分けるで受ける。文字の寸法は
`char_em`（全角を 1、半角を 0.6 前後の em と見積る）と行の高さの係数 `LINE_HEIGHT` で見積もる——**見積りであって、描画した結果ではない**
（描画して確かめるのは `check-pptx-render.py`）。標準ライブラリだけを使う。同じ材料から同じバイトを作る（時刻を書かない）。

**守らないもの**: PowerPoint で開けること・フォントの違いによる折り返しのずれ（見積りに余裕を持たせるだけ）・社のデザイン
（差し替えは `build-proposal.py` の `--pptx-script`。`references/tree.md` の「PPTX のデザインと指示」）。
"""

from __future__ import annotations

import importlib.util
import io
import os
import re
import shutil
import struct
import subprocess
import unicodedata
import zipfile
from datetime import date, timedelta
from pathlib import Path
from html import unescape
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pptx = _load("qa_to_pptx", "qa-to-pptx.py")
qa = pptx.qa

W, H = pptx.SLIDE_W, pptx.SLIDE_H
MARGIN = 457200
CY0 = 1130000            # 内容の上端（題の下）
CY1 = H - 380000         # 内容の下端（ページ番号の上）
CONTENT_W = W - 2 * MARGIN
LINE_HEIGHT = 1.42       # 1 行の高さ = 文字の大きさ × この値（日本語のフォントの行間に余裕を持たせた見積り）
SAFETY = 0.94            # 折り返しの幅に掛ける余裕
INSET_X, INSET_Y = 72000, 36000
CARD_SIZES = (24, 22, 20, 18, 16, 14, 12)
CARD_MIN = 12            # カードの文字の最小（これを割るなら枚を分ける）
MAX_CARDS = 6

DARK, ACCENT, GREY, LIGHT, BORDER = "1F2937", "2563EB", "6B7280", "F3F4F6", "D1D5DB"
BAR, MILESTONE, WHITE = "4A7BD0", "D0794A", "FFFFFF"

SPEC_RSVG_ENV = "SPEC_LOOP_RSVG"
DRAWIO_ALT = "Text is not SVG - cannot display"
PNG_WIDTH = 1800

# ---------------------------------------------------------------- 文字の寸法の見積り


def char_em(ch: str) -> float:
    if ch == " ":
        return 0.32
    code = ord(ch)
    if code < 0x80:
        return 0.62 if ch.isupper() or ch.isdigit() else 0.55
    if 0xFF61 <= code <= 0xFF9F:
        return 0.55
    width = unicodedata.east_asian_width(ch)
    return 1.0 if width in "WFA" else 0.6


WORD = re.compile(r"[A-Za-z0-9_.,:;/+\-%#@&'\"<>=*~|\\$!?]+|\s|.", re.S)


def text_width_pt(text: str, size: float) -> float:
    return sum(char_em(c) for c in text) * size


def lines_needed(text: str, size: float, width_pt: float) -> int:
    """`text` を幅 `width_pt` の箱に `size` pt で入れたときの行数（改行で割った段落ごとの合計）。"""
    width_pt = max(width_pt * SAFETY, size)
    total = 0
    for para in text.replace("\r\n", "\n").split("\n"):
        if not para:
            total += 1
            continue
        count, line = 1, 0.0
        for token in WORD.findall(para):
            w = sum(char_em(c) for c in token) * size
            if line + w <= width_pt:
                line += w
                continue
            if token.isspace():
                continue
            if line == 0 or w > width_pt:
                for c in token:
                    cw = char_em(c) * size
                    if line + cw > width_pt and line > 0:
                        count += 1
                        line = 0.0
                    line += cw
            else:
                count += 1
                line = w
        total += count
    return total


def emu_pt(emu: int) -> float:
    return emu / 12700


def pt_emu(pt: float) -> int:
    return int(pt * 12700)


# ---------------------------------------------------------------- 参照の括弧を外す

ID = re.compile(r"\b[A-Z](?:-[A-Z])?-\d{3,}\b")
PATH = re.compile(r"`?(?:[\w.\-]+/)+[\w.\-]*\.[A-Za-z0-9]{1,6}`?|`?(?:[\w.\-]+/)+`?|`[\w.\-]+\.(?:md|csv|svg|json|drawio|bpmn|html|py)`")
ANSWER_OF = re.compile(r"の回答\s*[A-Z]?")
OPEN, CLOSE = "（(", "）)"
FILLER = set("、,・/／と　 \t")


def only_refs(inner: str) -> bool:
    """括弧の中身が、番号・パス・「の回答 B」と区切りだけか。"""
    rest = ANSWER_OF.sub("", PATH.sub("", ID.sub("", inner)))
    return bool(ID.search(inner) or PATH.search(inner)) and all(c in FILLER for c in rest)


def balanced_groups(text: str):
    """(開き, 閉じ) の位置（閉じは含む）を、外側のものから順に返す（入れ子は外側だけ）。"""
    depth, start = 0, -1
    for i, c in enumerate(text):
        if c in OPEN:
            if depth == 0:
                start = i
            depth += 1
        elif c in CLOSE and depth:
            depth -= 1
            if depth == 0:
                yield start, i


def strip_refs(text: str, extra: list | None = None) -> str:
    """スライドに出す文から、参照の括弧（番号・パスだけの括弧）を外す。**中身が参照だけでない括弧は残す**
    （暫定の断り書きなど。`Q-R-002（暫定の回答。…）` の番号は、括弧が続くときだけ外す）。"""
    out, last = [], 0
    for start, end in balanced_groups(text):
        inner = text[start + 1:end]
        if only_refs(inner):
            out.append(text[last:start].rstrip())
            last = end + 1
    out.append(text[last:])
    text = "".join(out)
    text = re.sub(ID.pattern + r"(?=[（(])", "", text)
    for pattern in extra or []:
        text = pattern.sub("", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


INLINE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def plain(text: str, extra: list | None = None) -> str:
    """Markdown の印（太字・バッククォート・リンク）を外し、参照の括弧を外した 1 行。"""
    text = INLINE_LINK.sub(r"\1", text)
    text = text.replace("**", "").replace("`", "")
    return strip_refs(text, extra)


def basis_text(raw: str, width_pt: float, size: float, max_lines: int = 2) -> tuple[str, str]:
    """費用の根拠をスライドに出す形にする。(出す文, 種類) で、種類は `formula`（計算式など）・`none`（番号だけ）・`long`（長すぎる）。"""
    text = strip_refs(raw.replace("`", ""))  # 先に参照だけの括弧を外す（番号を消してからだと「（ と ）」が残る）
    text = ANSWER_OF.sub(" ", ID.sub(" ", text))
    text = re.sub(r"\s+", " ", text).strip(" 、,・/／と　")
    if raw.strip() == "" or len(re.sub(r"[\s、,・/／と　（）()]", "", text)) < 2:
        return "", "none"
    if lines_needed(text, size, width_pt) > max_lines:
        return "", "long"
    return text, "formula"


# ---------------------------------------------------------------- 図形の部品


def rgb(color: str) -> str:
    return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'


def run(text: str, size: float, bold: bool = False, color: str | None = None) -> str:
    b = ' b="1"' if bold else ""
    return (f'<a:r><a:rPr lang="ja-JP" sz="{int(size * 100)}"{b} dirty="0">{rgb(color) if color else ""}</a:rPr>'
            f"<a:t>{pptx.clean(text)}</a:t></a:r>")


def para(text: str, size: float, bold: bool = False, color: str | None = None, align: str = "l",
         bullet: bool = False, level: int = 0, before: float = 0) -> str:
    """1 段落。改行を含む文は呼び出し側で段落に分ける。"""
    attrs = f' algn="{align}"' if align != "l" else ""
    if bullet:
        attrs += f' marL="{228600 + level * 228600}" indent="-228600"'
    body = f'<a:spcBef><a:spcPts val="{int(before * 100)}"/></a:spcBef>' if before else ""
    body += '<a:buFont typeface="Arial"/><a:buChar char="•"/>' if bullet else "<a:buNone/>"
    ppr = f"<a:pPr{attrs}>{body}</a:pPr>"
    if not text:
        return f'<a:p>{ppr}<a:endParaRPr lang="ja-JP" sz="{int(size * 100)}"/></a:p>'
    return f"<a:p>{ppr}{run(text, size, bold, color)}</a:p>"


def paras(text: str, size: float, **kw) -> list[str]:
    return [para(t, size, **kw) for t in pptx.split_lines(text)]


class Slide:
    def __init__(self) -> None:
        self.xml: list[str] = []
        self.count = 1
        self.images: list[bytes] = []

    def nid(self) -> int:
        self.count += 1
        return self.count

    def box(self, x: int, y: int, w: int, h: int, body: list[str], fill: str | None = None, line: str | None = None,
            anchor: str = "t", geom: str = "rect", name: str = "Text", ins: tuple[int, int] = (INSET_X, INSET_Y)) -> None:
        i = self.nid()
        fill_xml = rgb(fill) if fill else "<a:noFill/>"
        line_xml = f'<a:ln w="9525">{rgb(line)}</a:ln>' if line else "<a:ln><a:noFill/></a:ln>"
        self.xml.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{name} {i}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>{fill_xml}{line_xml}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="{ins[0]}" tIns="{ins[1]}" rIns="{ins[0]}" bIns="{ins[1]}" anchor="{anchor}">'
            f"<a:noAutofit/></a:bodyPr><a:lstStyle/>{''.join(body) or para('', 1000)}</p:txBody></p:sp>")

    def rect(self, x: int, y: int, w: int, h: int, fill: str, geom: str = "rect", name: str = "Shape") -> None:
        self.box(x, y, w, h, [], fill=fill, geom=geom, name=name)

    def title(self, text: str, size: float = 26) -> None:
        self.box(MARGIN, 260000, CONTENT_W, 640000, paras(text, size, bold=True, color=DARK), anchor="ctr", name="Title")
        self.rect(MARGIN, 930000, CONTENT_W, 22860, ACCENT, name="Rule")

    def table(self, x: int, y: int, col_w: list[int], rows: list[list[dict]], row_h: list[int]) -> None:
        i = self.nid()
        grid = "".join(f'<a:gridCol w="{w}"/>' for w in col_w)
        trs = []
        for cells, h in zip(rows, row_h):
            tcs = []
            for cell in cells:
                body = []
                for t in pptx.split_lines(cell["text"]) or [""]:
                    body.append(para(t, cell["size"], bold=cell.get("bold", False), color=cell.get("color", DARK),
                                     align=cell.get("align", "l")))
                edge = "".join(f'<a:{s} w="6350">{rgb(BORDER)}</a:{s}>' for s in ("lnL", "lnR", "lnT", "lnB"))
                fill = rgb(cell["fill"]) if cell.get("fill") else "<a:noFill/>"
                tcs.append(f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>{"".join(body)}</a:txBody>'
                           f'<a:tcPr marL="{INSET_X}" marR="{INSET_X}" marT="{INSET_Y}" marB="{INSET_Y}" anchor="ctr">{edge}{fill}</a:tcPr></a:tc>')
            trs.append(f'<a:tr h="{h}">{"".join(tcs)}</a:tr>')
        self.xml.append(
            f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{i}" name="Table {i}"/><p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/>'
            f'</p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{sum(col_w)}" cy="{sum(row_h)}"/></p:xfrm>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"/>'
            f"<a:tblGrid>{grid}</a:tblGrid>{''.join(trs)}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>")

    def picture(self, png: bytes, x: int, y: int, w: int, h: int, descr: str) -> None:
        i = self.nid()
        self.images.append(png)
        rid = f"rId{len(self.images) + 1}"
        self.xml.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{i}" name="Picture {i}" descr="{pptx.attribute(descr)}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/><a:ext cx="{int(w)}" cy="{int(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    def render(self, extra: list[str] | None = None) -> str:
        return (pptx.DECL + f"<p:sld {pptx.NS}><p:cSld><p:spTree>{pptx.GROUP}{''.join(self.xml + (extra or []))}</p:spTree></p:cSld>"
                "<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>")


class Deck:
    def __init__(self, title: str) -> None:
        self.title = title
        self.slides: list[Slide] = []

    def add(self, slide: Slide) -> Slide:
        self.slides.append(slide)
        return slide

    def parts(self) -> list[tuple[str, str | bytes]]:
        total = len(self.slides)
        rendered = []
        for number, slide in enumerate(self.slides, 1):
            footer = Slide()  # 何度呼んでも同じ（スライドには足さない）。表紙に番号は付けない
            footer.count = slide.count
            if number > 1:
                footer.box(W - MARGIN - 1200000, H - 330000, 1200000, 260000,
                           [para(f"{number} / {total}", 10, color=GREY, align="r")], name="Page")
            rendered.append(slide.render(footer.xml))
        parts = pptx.package(rendered, self.title)
        has_images = any(s.images for s in self.slides)
        out: list[tuple[str, str | bytes]] = []
        media: list[tuple[str, bytes]] = []
        serial = 0
        for name, body in parts:
            m = re.fullmatch(r"ppt/slides/_rels/slide(\d+)\.xml\.rels", name)
            if name == "[Content_Types].xml" and has_images:
                body = body.replace('<Default Extension="xml"', '<Default Extension="png" ContentType="image/png"/><Default Extension="xml"', 1)
            elif m and self.slides[int(m[1]) - 1].images:
                extra = ""
                for k, png in enumerate(self.slides[int(m[1]) - 1].images, 2):
                    serial += 1
                    media.append((f"ppt/media/image{serial}.png", png))
                    extra += f'<Relationship Id="rId{k}" Type="{pptx.REL}/image" Target="../media/image{serial}.png"/>'
                body = body.replace("</Relationships>", extra + "</Relationships>")
            out.append((name, body))
        return out + media


# ---------------------------------------------------------------- 表（行の高さを見積もって枚を割る）


def cell_height(text: str, size: float, width_emu: int) -> int:
    lines = lines_needed(text, size, emu_pt(width_emu - 2 * INSET_X))
    return int(lines * size * LINE_HEIGHT * 12700) + 2 * INSET_Y


def table_slides(title: str, columns: list[str], rows: list[list[str]], fracs: list[float] | None = None,
                 aligns: list[str] | None = None, size: float = 12, bold_last: bool = False, note: str | None = None) -> list[Slide]:
    """表を、行の高さを見積もって枚に割る（見出しの行は枚ごとに繰り返す）。入りきらない行は次の枚へ送り、文字は切らない。"""
    n = len(columns)
    fracs = fracs or [1 / n] * n
    aligns = aligns or ["l"] * n
    col_w = [int(CONTENT_W * f / sum(fracs)) for f in fracs]
    top = CY0 + (330000 if note else 0)
    avail = CY1 - top

    def heights(sz: float) -> tuple[int, list[int]]:
        head = max(cell_height(c, sz, w) for c, w in zip(columns, col_w))
        return head, [max(cell_height(c, sz, w) for c, w in zip(r, col_w)) for r in rows]

    while True:
        head_h, row_h = heights(size)
        if size <= 9 or not row_h or max(row_h) + head_h <= avail:
            break
        size -= 1  # 1 行だけで枚に収まらないときは文字を小さくする
    pages: list[list[int]] = [[]]
    used = head_h
    for index, h in enumerate(row_h):
        if pages[-1] and used + h > avail:
            pages.append([])
            used = head_h
        pages[-1].append(index)
        used += h
    slides = []
    for number, page in enumerate(pages, 1):
        slide = Slide()
        slide.title(title if len(pages) == 1 else f"{title}（{number}/{len(pages)}）")
        if note:
            slide.box(MARGIN, CY0 - 20000, CONTENT_W, 330000, paras(note, 12, color=GREY), name="Note")
        cells = [[{"text": c, "size": size, "bold": True, "fill": LIGHT} for c in columns]]
        for index in page:
            last = bold_last and index == len(rows) - 1
            cells.append([{"text": c, "size": size, "align": a, "bold": last, "fill": LIGHT if last else None}
                          for c, a in zip(rows[index], aligns)])
        slide.table(MARGIN, top, col_w, cells, [head_h] + [row_h[i] for i in page])
        slides.append(slide)
    if not rows:
        slide = Slide()
        slide.title(title)
        slide.box(MARGIN, CY0, CONTENT_W, 600000, paras("（ありません）", 18, color=GREY))
        slides = [slide]
    return slides


# ---------------------------------------------------------------- カード（手書き部分）

Card = dict  # {"heading": str | None, "lines": [(level, text, bullet)]}


def card_height(card: Card, size: float, width_emu: int) -> int:
    inner = emu_pt(width_emu - 2 * 91440)
    total = 0.0
    if card["heading"]:
        total += lines_needed(card["heading"], size * 1.08, inner) * size * 1.08 * LINE_HEIGHT
    for level, text, bullet in card["lines"]:
        width = inner - (18 + level * 18 if bullet else 0)
        total += size * 0.3 + lines_needed(text, size, width) * size * LINE_HEIGHT
    return int(total * 12700) + 2 * 72000


def grid_for(count: int) -> tuple[int, int]:
    return {1: (1, 1), 2: (2, 1), 3: (3, 1), 4: (2, 2), 5: (3, 2), 6: (3, 2)}[count]


def best_size(cards: list[Card], area_h: int) -> float | None:
    cols, rows = grid_for(len(cards))
    gap = 140000
    w = (CONTENT_W - gap * (cols - 1)) // cols
    h = (area_h - gap * (rows - 1)) // rows
    for size in CARD_SIZES:
        if all(card_height(c, size, w) <= h for c in cards):
            return size
    return None


def split_card(card: Card, area_h: int) -> list[Card]:
    """1 枚でも最小の文字の大きさで収まらないカードを、箇条の途中で 2 つに割る（続きに見出しを付ける）。"""
    lines = card["lines"]
    if len(lines) < 2:
        return [card]
    mid = len(lines) // 2
    head = {"heading": card["heading"], "lines": lines[:mid]}
    tail = {"heading": (card["heading"] + "（続き）") if card["heading"] else None, "lines": lines[mid:]}
    return [head, tail]


def place_cards(cards: list[Card], area_h: int) -> list[tuple[list[Card], float]]:
    """カードを枚に割り、(その枚のカード, 文字の大きさ) の並びにする。同じ枚のカードは同じ文字の大きさ。"""
    out: list[tuple[list[Card], float]] = []
    queue = list(cards)
    while queue:
        placed = False
        for floor in (14, CARD_MIN):
            for k in range(min(MAX_CARDS, len(queue)), 0, -1):
                size = best_size(queue[:k], area_h)
                if size is not None and size >= floor:
                    out.append((queue[:k], size))
                    queue = queue[k:]
                    placed = True
                    break
            if placed:
                break
        if not placed:
            parts = split_card(queue[0], area_h)
            if len(parts) == 1:  # 割れない（1 行だけで収まらない）なら、最小の文字で 1 枚に置く
                out.append(([queue[0]], CARD_MIN))
                queue = queue[1:]
            else:
                queue = parts + queue[1:]
    return out


def card_slide(title: str, cards: list[Card], size: float, area_h: int | None = None) -> Slide:
    slide = Slide()
    slide.title(title)
    cols, rows = grid_for(len(cards))
    gap = 140000
    area_h = area_h or CY1 - CY0
    w = (CONTENT_W - gap * (cols - 1)) // cols
    h = (area_h - gap * (rows - 1)) // rows
    for index, card in enumerate(cards):
        x = MARGIN + (index % cols) * (w + gap)
        y = CY0 + (index // cols) * (h + gap)
        body = []
        if card["heading"]:
            body += paras(card["heading"], size * 1.08, bold=True, color=ACCENT)
        for level, text, bullet in card["lines"]:
            body += [para(t, size, bullet=bullet, level=level, before=size * 0.3, color=DARK) for t in pptx.split_lines(text)]
        slide.box(x, y, w, h, body, fill="F8FAFC", line=BORDER, ins=(91440, 72000), name="Card")
    return slide


BULLET = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$")
COMMENT = re.compile(r"<!--.*?-->", re.S)


def parse_hand(hand: list[tuple[str, str]], extra: list | None = None) -> list[tuple[str, list[Card]]]:
    """手書き部分（`proposal/*.md`）を (節の題, カードの並び) にする。節は `#`・`##` の見出し、カードは太字の見出しの行。"""
    sections: list[tuple[str, list[Card]]] = []

    def start_card(heading: str | None) -> None:
        sections[-1][1].append({"heading": heading, "lines": []})

    for name, body in hand:
        text = COMMENT.sub("", body)
        fence = None
        for raw in pptx.split_lines(text):
            line = raw.rstrip()
            if fence is None and pptx.MARKDOWN_FENCE.match(line):
                fence = pptx.MARKDOWN_FENCE.match(line).group(1)[0]
                continue
            if fence is not None:
                if set(line.strip()) == {fence}:
                    fence = None
                    continue
            if fence is None and (line.startswith("# ") or line.startswith("## ")):
                sections.append((plain(line.split(" ", 1)[1], extra), []))
                continue
            if not line.strip() or pptx.MARKDOWN_TABLE_RULE.fullmatch(line.strip()):
                continue
            if not sections:
                sections.append((Path(name).stem, []))
            cards = sections[-1][1]
            quote = pptx.MARKDOWN_QUOTE.match(line) if line.startswith(">") else None
            content = line[quote.end():] if quote else line
            bold = pptx.MARKDOWN_BOLD_LINE.fullmatch(content) if fence is None else None
            if bold:
                start_card(plain(bold.group(1), extra))
                continue
            if content.startswith("#"):
                start_card(plain(content.lstrip("#"), extra))
                continue
            if not cards:
                start_card(None)
            if content.lstrip().startswith("|"):
                shown, bullet, level = pptx.markdown_row(content), False, 0
            else:
                m = BULLET.match(content)
                if m:
                    shown, bullet, level = m.group(2), True, min(len(m.group(1)) // 4, 2)
                else:
                    shown, bullet, level = content.strip(), False, 0
            shown = plain(shown, extra)
            if shown:
                cards[-1]["lines"].append((level, shown, bullet))
    return [(title, [c for c in cards if c["heading"] or c["lines"]]) for title, cards in sections if cards]


def hand_slides(hand: list[tuple[str, str]], extra: list | None = None) -> list[Slide]:
    slides = []
    for title, cards in parse_hand(hand, extra):
        placed = place_cards(cards, CY1 - CY0)
        for number, (chunk, size) in enumerate(placed, 1):
            slides.append(card_slide(title if len(placed) == 1 else f"{title}（{number}/{len(placed)}）", chunk, size))
    return slides


# ---------------------------------------------------------------- 表紙・費用・期間


def cover(title: str, lines: list[str]) -> Slide:
    slide = Slide()
    slide.rect(0, 0, W, H, DARK, name="Background")
    slide.rect(MARGIN, 3250000, 1400000, 45720, ACCENT, name="Rule")
    slide.box(MARGIN, 1700000, CONTENT_W, 1450000, paras(title, 40, bold=True, color=WHITE), anchor="b", name="Title")
    body: list[str] = []
    for line in lines:
        body += paras(line, 16, color="D1D5DB")
    slide.box(MARGIN, 3450000, CONTENT_W, 2200000, body, name="Subtitle")
    return slide


def money(value: int) -> str:
    return f"{value:,}"


def cost_slides(estimate: list[dict[str, str]], categories: list[str], md_name: str) -> list[Slide]:
    """開発費・運用費を区分ごとに別のページにする。根拠は計算式だけ（番号だけ・長すぎる根拠は出さない）。"""
    fracs = [0.42, 0.17, 0.41]
    basis_w = emu_pt(int(CONTENT_W * fracs[2]) - 2 * INSET_X)
    slides: list[Slide] = []
    for category in categories:
        rows = [r for r in estimate if r["区分"] == category]
        if not rows:
            continue
        body, long_seen = [], False
        for r in rows:
            text, kind = basis_text(r["根拠"], basis_w, 11)
            if kind == "long":
                text, long_seen = f"（根拠は {md_name} を見る）", True
            body.append([plain(r["項目"]), money(int(r["金額"])), text or "—"])
        total = sum(int(r["金額"]) for r in rows)
        body.append(["合計", money(total), ""])
        note = f"{category}の合計 {money(total)} 円" + ("。根拠が長い行の全文は " + md_name if long_seen else "")
        slides += table_slides(category, ["項目", "金額（円）", "根拠"], body, fracs, ["l", "r", "l"], size=12, bold_last=True, note=note)
    return slides


def gantt_slides(schedule: list[dict[str, str]]) -> list[Slide]:
    spans = [(date.fromisoformat(r["開始"]), date.fromisoformat(r["終了"])) for r in schedule]
    first, last = min(s for s, _ in spans), max(e for _, e in spans)
    days = (last - first).days + 1
    label_size, date_size = 10, 9
    widest = max(text_width_pt(r["工程"], label_size) for r in schedule)
    label_w = min(max(pt_emu(widest * 1.06) + 2 * INSET_X + 30000, 1500000), 3700000)
    chart_x0 = MARGIN + label_w + 60000
    chart_x1 = W - MARGIN
    per_day = (chart_x1 - chart_x0) / days
    header_h = 330000

    def x_of(day: date) -> int:
        return int(chart_x0 + (day - first).days * per_day)

    def date_text(s: date, e: date) -> str:
        return f"{s.month}/{s.day}" if s == e else f"{s.month}/{s.day}〜{e.month}/{e.day}"

    heights = []
    for r in schedule:
        lines = lines_needed(r["工程"], label_size, emu_pt(label_w - 2 * INSET_X))
        heights.append(max(int(lines * label_size * LINE_HEIGHT * 12700) + 2 * INSET_Y + 20000, 260000))
    avail = CY1 - CY0 - header_h
    pages: list[list[int]] = [[]]
    used = 0
    for i, h in enumerate(heights):
        if pages[-1] and used + h > avail:
            pages.append([])
            used = 0
        pages[-1].append(i)
        used += h

    months: list[tuple[date, date]] = []
    day = first
    while day <= last:
        end = (date(day.year + (day.month == 12), day.month % 12 + 1, 1) - timedelta(days=1))
        months.append((day, min(end, last)))
        day = end + timedelta(days=1)

    def month_labels() -> list[tuple[date, date, str, int]]:
        """(開始, 終了, 文字, 使える幅 EMU)。月ごとの見出しが全部収まる水準（年月・月・年）を選ぶ。使える幅は次の見出しまで。"""
        for level in (0, 1, 2):
            labels = []
            for index, (s, e) in enumerate(months):
                if level == 0:
                    text = f"{s.year}年{s.month}月" if index == 0 or s.month == 1 else f"{s.month}月"
                elif level == 1:
                    text = f"{s.month}月"
                else:
                    text = f"{s.year}年" if s.month == 1 or index == 0 else ""
                if len(months) > 1 and index in (0, len(months) - 1) and (e - s) < timedelta(days=10):
                    text = ""  # 端の短い月（数日）の見出しは書かない。隣の月の見出しに被せない
                labels.append([s, e, text, 0])
            starts = [i for i, l in enumerate(labels) if l[2]]
            for k, i in enumerate(starts):
                nxt = x_of(labels[starts[k + 1]][0]) if k + 1 < len(starts) else chart_x1
                labels[i][3] = nxt - x_of(labels[i][0])
            fits = all(text_width_pt(l[2], 10) * 12700 + 60000 <= l[3] for l in labels if l[2])
            if fits:
                return [tuple(l) for l in labels]
        return [(s, e, "", 0) for s, e in months]

    labels = month_labels()
    slides = []
    for number, page in enumerate(pages, 1):
        slide = Slide()
        slide.title(f"期間（{first.isoformat()} 〜 {last.isoformat()}）" if len(pages) == 1
                    else f"期間（{number}/{len(pages)}）")
        top = CY0
        body_top = top + header_h
        body_h = sum(heights[i] for i in page)
        # 休みの網掛け（土日）
        d = first
        while d <= last:
            if d.weekday() == 5:
                span = 2 if d + timedelta(days=1) <= last else 1
                slide.rect(x_of(d), body_top, max(int(per_day * span), 3000), body_h, LIGHT, name="Weekend")
                d += timedelta(days=span)
            elif d.weekday() == 6:
                slide.rect(x_of(d), body_top, max(int(per_day), 3000), body_h, LIGHT, name="Weekend")
                d += timedelta(days=1)
            else:
                d += timedelta(days=1)
        # 月の見出しと境目
        for s, e, text, room in labels:
            x = x_of(s)
            slide.rect(x, top, 6350, header_h + body_h, BORDER, name="MonthLine")
            if text:
                slide.box(x, top, max(int(room), 1), header_h,
                          [para(text, 10, bold=True, color=DARK)], anchor="ctr", name="Month", ins=(30000, 0))
        slide.rect(MARGIN, body_top, CONTENT_W, 6350, BORDER, name="HeaderRule")
        y = body_top
        for i in page:
            r, (s, e), h = schedule[i], spans[i], heights[i]
            slide.box(MARGIN, y, label_w, h, paras(r["工程"], label_size, color=DARK), anchor="ctr", name="Label")
            x0, x1 = x_of(s), max(x_of(e) + per_day, x_of(s) + 40000)
            text = date_text(s, e)
            tw = pt_emu(text_width_pt(text, date_size)) + 2 * INSET_X + 20000
            if s == e:
                size = int(min(h * 0.6, 200000))
                cx = int(x_of(s) + per_day / 2)
                slide.rect(cx - size // 2, y + (h - size) // 2, size, size, MILESTONE, geom="diamond", name="Milestone")
                x0, x1 = cx - size // 2, cx + size // 2
            else:
                slide.rect(int(x0), y + h // 4, int(x1 - x0), h // 2, BAR, geom="roundRect", name="Bar")
            if x1 + tw <= chart_x1 + 150000:
                slide.box(int(x1), y, tw, h, [para(text, date_size, color=DARK)], anchor="ctr", name="Date", ins=(INSET_X // 2, 0))
            elif x0 - tw >= chart_x0 - 150000:
                slide.box(int(x0 - tw), y, tw, h, [para(text, date_size, color=DARK, align="r")], anchor="ctr", name="Date", ins=(INSET_X // 2, 0))
            else:
                slide.box(int(x0), y, int(x1 - x0), h, [para(text, date_size, color=WHITE, align="ctr")], anchor="ctr", name="Date", ins=(0, 0))
            slide.rect(MARGIN, y + h, CONTENT_W, 3175, BORDER, name="RowRule")
            y += h
        slides.append(slide)
    return slides


# ---------------------------------------------------------------- 利用者と決めたこと

OVERVIEW_ITEMS = ("counts", "recommend", "origin", "theme")
SCOPE_WORDS = re.compile(r"範囲|作らない|対象外|スコープ")
LABEL = re.compile(r"^([A-Z])(?:[\s（(:：]|$)")


def answer_label(row: dict[str, str]) -> str | None:
    m = LABEL.match(row["回答"].strip())
    return m.group(1) if m else None


def origin_of(row: dict[str, str]) -> str:
    return re.split(r"[（(]", row["起票元"].strip())[0] or "—"


def theme_of(row: dict[str, str]) -> str:
    target = row["反映先"].strip()
    if target in ("", "—"):
        return "未反映"
    if "決定表" in target:
        return "決定表（業務ルール）"
    if "feasibility" in target or "見積" in target or "schedule" in target:
        return "費用・期間"
    if "requirements" in target or "要求" in target:
        return "要求"
    if "spec" in target or "仕様" in target:
        return "仕様"
    return "その他"


def count_lines(values: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return [f"{k}: {n} 件" for k, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def overview_slides(rows: list[dict[str, str]], items: tuple[str, ...], appendix: bool) -> list[Slide]:
    done = [r for r in rows if r["状態"].strip() == qa.DONE]
    provisional = [r for r in rows if qa.is_provisional(r)]
    pending = [r for r in rows if r["状態"].strip() != qa.DONE and not qa.is_provisional(r)]
    cards: list[Card] = []
    if "counts" in items:
        cards.append({"heading": "件数", "lines": [(0, f"決定: {len(done)} 件", True),
                                                   (0, f"暫定（利用者に未確認）: {len(provisional)} 件", True),
                                                   (0, f"未決定: {len(pending)} 件", True),
                                                   (0, f"合計: {len(rows)} 件", True)]})
    if "recommend" in items:
        same = sum(1 for r in done if answer_label(r) is not None and answer_label(r) == qa_recommended(r))
        none = sum(1 for r in done if qa_recommended(r) is None)
        cards.append({"heading": "推奨どおりか（決定の内訳）",
                      "lines": [(0, f"推奨どおり: {same} 件", True), (0, f"推奨と違う: {len(done) - same - none} 件", True),
                                (0, f"推奨なしの質問: {none} 件", True)]})
    if "origin" in items:
        cards.append({"heading": "起票元ごとの件数", "lines": [(0, t, True) for t in count_lines([origin_of(r) for r in rows])]})
    if "theme" in items:
        cards.append({"heading": "テーマごとの件数（反映先）", "lines": [(0, t, True) for t in count_lines([theme_of(r) for r in rows])]})
    if not cards:
        return []
    slide_title = "利用者と決めたことの概要"
    out = []
    area_h = CY1 - CY0 - (420000 if appendix else 0)
    for chunk, size in place_cards(cards, area_h):
        out.append(card_slide(slide_title, chunk, size, area_h))
    if out and appendix:
        out[0].box(MARGIN, H - 760000, CONTENT_W, 330000,
                   paras("質問・選択肢・推奨・回答・反映先の全件は、別紙の表（decisions.xlsx）にある。", 12, color=GREY), name="Note")
    return out


def qa_recommended(row: dict[str, str]) -> str | None:
    return pptx.recommended(row)


def scope_rows(rows: list[dict[str, str]], numbers: list[str] | None, match: str | None) -> list[dict[str, str]]:
    done = [r for r in rows if r["状態"].strip() == qa.DONE]
    if numbers is not None:
        by_no = {r["No"].strip(): r for r in done}
        return [by_no[n] for n in numbers if n in by_no]
    pattern = re.compile(match) if match else SCOPE_WORDS
    return [r for r in done if "scope.md" in r["反映先"] or pattern.search(r["質問"])]


def option_text(row: dict[str, str]) -> str:
    label = answer_label(row)
    for option in row["選択肢"].split(qa.OPTION_SEPARATOR):
        option = option.strip()
        m = qa.OPTION.fullmatch(option)
        if m and m["label"] == label:
            return option
    return row["回答"].strip()


def scope_slides(rows: list[dict[str, str]], numbers: list[str] | None, match: str | None, extra: list | None) -> list[Slide]:
    chosen = scope_rows(rows, numbers, match)
    if not chosen:
        return []
    cards = []
    for r in chosen:
        question = plain(pptx.split_lines(r["質問"])[0], extra)
        mark = "推奨どおり" if answer_label(r) == qa_recommended(r) else ("推奨と違う" if qa_recommended(r) else "推奨なし")
        cards.append({"heading": question, "lines": [(0, "決めたこと: " + plain(option_text(r), extra), False), (0, f"（{mark}）", False)]})
    placed = place_cards(cards, CY1 - CY0)
    return [card_slide("何を作り、何を作らないか" if len(placed) == 1 else f"何を作り、何を作らないか（{n}/{len(placed)}）", chunk, size)
            for n, (chunk, size) in enumerate(placed, 1)]


def decisions_xlsx(rows: list[dict[str, str]]) -> bytes:
    """全件の別紙（xlsx）。質問・選択肢・推奨・回答・反映先ほか。標準ライブラリだけで書き、同じ材料から同じバイトを作る。"""
    columns = ["No", "状態", "起票元", "質問", "選択肢", "推奨", "推奨の理由", "回答", "反映先", "費用への影響"]
    widths = [12, 12, 18, 48, 48, 8, 36, 28, 22, 28]

    def col(i: int) -> str:
        return chr(ord("A") + i)

    def cell(ref: str, text: str, style: int) -> str:
        return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{pptx.clean(text)}</t></is></c>'

    body = ["<row r=\"1\">" + "".join(cell(f"{col(i)}1", c, 1) for i, c in enumerate(columns)) + "</row>"]
    for n, row in enumerate(rows, 2):
        state = "暫定" if qa.is_provisional(row) else row["状態"].strip()
        values = {**row, "状態": state}
        body.append(f'<row r="{n}">' + "".join(cell(f"{col(i)}{n}", values[c].strip(), 2) for i, c in enumerate(columns)) + "</row>")
    sheet = (pptx.DECL + '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
             "<cols>" + "".join(f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths)) + "</cols>"
             "<sheetData>" + "".join(body) + "</sheetData></worksheet>")
    styles = (pptx.DECL + '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<fonts count="2"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><name val="Arial"/></font></fonts>'
              '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
              '<fill><patternFill patternType="solid"><fgColor rgb="FFF3F4F6"/></patternFill></fill></fills>'
              '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
              '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
              '<cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
              '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>'
              '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs>'
              "</styleSheet>")
    ct = "application/vnd.openxmlformats-officedocument.spreadsheetml"
    parts = [
        ("[Content_Types].xml", pptx.DECL + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
         '<Default Extension="xml" ContentType="application/xml"/>'
         f'<Override PartName="/xl/workbook.xml" ContentType="{ct}.sheet.main+xml"/>'
         f'<Override PartName="/xl/worksheets/sheet1.xml" ContentType="{ct}.worksheet+xml"/>'
         f'<Override PartName="/xl/styles.xml" ContentType="{ct}.styles+xml"/></Types>'),
        ("_rels/.rels", pptx.rels([(f"{pptx.REL}/officeDocument", "xl/workbook.xml")])),
        ("xl/workbook.xml", pptx.DECL + '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
         'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
         '<sheets><sheet name="決定事項" sheetId="1" r:id="rId1"/></sheets></workbook>'),
        ("xl/_rels/workbook.xml.rels", pptx.rels([(f"{pptx.REL}/worksheet", "worksheets/sheet1.xml"), (f"{pptx.REL}/styles", "styles.xml")])),
        ("xl/worksheets/sheet1.xml", sheet),
        ("xl/styles.xml", styles),
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in parts:
            info = zipfile.ZipInfo(name, date_time=pptx.ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, text.encode("utf-8"))
    return buffer.getvalue()


# ---------------------------------------------------------------- 図（SVG → PNG）

DRAWIO_LINK = re.compile(r'<a\b[^>]*svg-export-text-problems[^>]*>.*?</a>', re.S)
DRAWIO_TEXT = re.compile(r"<text\b[^>]*>[^<]*" + re.escape(DRAWIO_ALT) + r"[^<]*</text>", re.S)
GENERIC_NAMES = {"page-1", "page1", "ページ-1", "ページ1", "untitled", ""}
FIGURE_STEMS = {"er": "データモデル（ER 図）", "architecture": "構成図", "flow": "業務フロー", "bpmn": "業務フロー"}
FIGURE_PREFIXES = (("wireframe-", "画面: "), ("screen-", "画面: "), ("flow-", "業務フロー: "), ("er-", "データモデル: "), ("seq-", "シーケンス: "))


def strip_drawio_alt(svg: str) -> str:
    """drawio の書き出しが付ける「Text is not SVG - cannot display」を消す（PNG にするときだけ。正本の SVG は変えない）。"""
    return DRAWIO_TEXT.sub("", DRAWIO_LINK.sub("", svg))


def svg_to_png(svg: bytes) -> bytes | None:
    """SVG を PNG にする。道具（`rsvg-convert`・環境変数 `SPEC_LOOP_RSVG` で差し替え）が無い・失敗したら None。"""
    command = os.environ.get(SPEC_RSVG_ENV) or shutil.which("rsvg-convert")
    if not command:
        return None
    text = strip_drawio_alt(svg.decode("utf-8", "replace")).encode("utf-8")
    try:
        done = subprocess.run([command, "-f", "png", "-w", str(PNG_WIDTH), "--background-color", "white"],
                              input=text, capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 and done.stdout.startswith(b"\x89PNG") and len(done.stdout) >= 24 else None


def png_size(png: bytes) -> tuple[int, int]:
    return struct.unpack(">II", png[16:24])


def drawio_title_cell(text: str) -> str | None:
    """drawio の図に「title」のセル（`data-cell-id="title"`）があれば、その文字（図の中の名前）。"""
    i = text.find('data-cell-id="title"')
    if i < 0:
        return None
    segment = text[i:i + 6000]
    segment = segment.split("<image", 1)[0]
    for pattern in (r"<div[^>]*>([^<>]+)</div>", r"<text[^>]*>([^<>]+)</text>"):
        for m in re.finditer(pattern, segment):
            value = unescape(m.group(1)).strip()
            if value and value != DRAWIO_ALT:
                return value
    return None


def figure_title(path: str, svg: bytes) -> str:
    """図の見出し。図の中の名前（`<title>`・drawio のページ名）があればそれ、無ければファイル名から読める名前を作る。"""
    text = svg.decode("utf-8", "replace")
    m = re.search(r"<title[^>]*>([^<]+)</title>", text)
    if m and m.group(1).strip().lower() not in GENERIC_NAMES:
        return m.group(1).strip()
    m = re.search(r'<diagram\b[^>]*\bname=(?:"|&quot;)([^"&]+)', text)
    if m and m.group(1).strip().lower() not in GENERIC_NAMES:
        return m.group(1).strip()
    named = drawio_title_cell(text)
    if named:
        return named
    stem = Path(path).name
    for suffix in (".drawio.svg", ".bpmn.svg", ".svg"):
        if stem.lower().endswith(suffix):
            stem = stem[:-len(suffix)]
            break
    if stem.lower() in FIGURE_STEMS:
        return FIGURE_STEMS[stem.lower()]
    for prefix, label in FIGURE_PREFIXES:
        if stem.lower().startswith(prefix):
            return label + stem[len(prefix):].replace("-", " ").replace("_", " ")
    return stem.replace("-", " ").replace("_", " ") or "図"


def figure_slides(figures: list[tuple[str, bytes]]) -> tuple[list[Slide], list[str]]:
    """(図の枚, 載せられなかった図のパス)。PNG にできない図は載せず、まとめて 1 枚に書く。"""
    slides, failed = [], []
    for path, svg in figures:
        png = svg_to_png(svg)
        if png is None:
            failed.append(path)
            continue
        slide = Slide()
        slide.title(figure_title(path, svg))
        pw, ph = png_size(png)
        aw, ah = CONTENT_W, CY1 - CY0
        scale = min(aw / pw, ah / ph)
        w, h = int(pw * scale), int(ph * scale)
        slide.picture(png, MARGIN + (aw - w) // 2, CY0 + (ah - h) // 2, w, h, figure_title(path, svg))
        slides.append(slide)
    return slides, failed


# ---------------------------------------------------------------- 提案書・仕様書の組み立て


class Options:
    """正本の `CLAUDE.md` の指示から `build-proposal.py` の引数で渡される値。"""

    def __init__(self, appendix: bool = True, scope_slide: bool = True, scope_questions: list[str] | None = None,
                 scope_match: str | None = None, overview: tuple[str, ...] = OVERVIEW_ITEMS, strip: list | None = None) -> None:
        self.appendix, self.scope_slide, self.scope_questions = appendix, scope_slide, scope_questions
        self.scope_match, self.overview, self.strip = scope_match, overview, strip or []


def change_slides(changes: dict, extra: list | None) -> list[Slide]:
    """前の版からの変更（v2 以降）。集計の表と、種類ごとの表（番号の列は出さない。ファイルは場所ごとの件数）。"""
    columns, rows = changes["summary"]
    slides = table_slides(changes["title"], columns, rows, size=14)
    for kind, cols, body in changes["details"]:
        if cols and cols[0] in ("パス",):
            slides += file_summary_slides(f"{kind}（{len(body)} 件）", [r[0] for r in body], extra, note="変化の内訳は proposal.md・spec.md を見る")
            continue
        keep = [i for i, c in enumerate(cols) if c not in ("No", "id", "鍵") and any(r[i] != "—" for r in body)]
        slides += table_slides(f"{changes['title']}: {kind}", [cols[i] for i in keep],
                               [[plain(r[i], extra) for i in keep] for r in body], size=12)
    return slides


def file_summary_slides(title: str, paths: list[str], extra: list | None = None, note: str | None = None) -> list[Slide]:
    groups: dict[str, list[str]] = {}
    for p in paths:
        parts = p.split("/")
        key = "/".join(parts[:2]) if len(parts) > 2 else parts[0]
        groups.setdefault(key, []).append(parts[-1])
    rows = []
    for key in sorted(groups):
        names = groups[key]
        main = "、".join(names[:3]) + (f" ほか {len(names) - 3} 件" if len(names) > 3 else "")
        rows.append([key, str(len(names)), main])
    return table_slides(title, ["場所", "件数", "主なファイル"], rows, [0.3, 0.1, 0.6], ["l", "r", "l"], size=12, note=note)


def out_of_scope_slides(lines: list[str] | None, extra: list | None) -> list[Slide]:
    """範囲の外。表なら列を残して根拠・理由の列を理由だけにし、表でなければ 1 件 1 行の表にする。"""
    if not lines:
        return []
    table = [pptx.markdown_row(l).split(" ／ ") for l in lines if l.strip().startswith("|") and not pptx.MARKDOWN_TABLE_RULE.fullmatch(l.strip())]
    if table:
        head, *body = table
        reasoning = [i for i, c in enumerate(head) if re.search(r"根拠|理由", c)]
        rows = [[reason_only(c, extra) if i in reasoning else plain(c, extra) for i, c in enumerate(r)] for r in body]
        rows = [r + [""] * (len(head) - len(r)) for r in rows if any(r)]
        return table_slides("範囲の外", [plain(c) for c in head], rows, size=13) if rows else []
    items = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        m = BULLET.match(text)
        items.append(reason_only(m.group(2) if m else text, extra))
    items = [i for i in items if i]
    return table_slides("範囲の外", ["範囲の外とした場面と理由"], [[i] for i in items], size=13) if items else []


def reason_only(text: str, extra: list | None = None) -> str:
    """範囲の外の行から、理由だけを残す（「既定の線（…）」の括りを外して中身を残し、レビューの経緯の文と番号を落とす）。"""
    t = plain(text, extra)
    t = re.sub(r"既定の線[（(]([^）)]*)[）)]", r"\1", t)
    keep = [s for s in re.split(r"(?<=。)", t) if not re.search(r"レビュー|経緯|判定役|Red Team|Domain Checker|Formal Checker|指摘", s)]
    t = "".join(keep).strip() or t.strip()
    t = re.sub(r"\s*" + ID.pattern, "", t)
    return re.sub(r"[（(]\s*[）)]", "", t).strip(" 、,")


def proposal_deck(ctx: dict, categories: list[str], opts: Options, md_name: str) -> tuple[list[tuple[str, str | bytes]], list[str]]:
    deck = Deck(ctx["title"])
    deck.add(cover(ctx["title"], [f"版 v{ctx['version']}", "この提案書は生成物で、決裁者の承認の記録ではありません。"]))
    for s in hand_slides(ctx["hand"], opts.strip):
        deck.add(s)
    if ctx.get("purposes"):
        cols = ["種類", "誰の課題か", "内容", "成功の判定"]
        rows = [[kind, plain(r[2], opts.strip), plain(r[3], opts.strip), plain(r[4], opts.strip)]
                for r, kind in zip(ctx["purposes"], ctx["purpose_kinds"])]
        for s in table_slides("目的と成功の判定", cols, rows, [0.1, 0.2, 0.4, 0.3], size=12):
            deck.add(s)
    if ctx.get("changes"):
        for s in change_slides(ctx["changes"], opts.strip):
            deck.add(s)
    rows = ctx["qa"]
    for s in overview_slides(rows, opts.overview, opts.appendix):
        deck.add(s)
    if opts.scope_slide:
        for s in scope_slides(rows, opts.scope_questions, opts.scope_match, opts.strip):
            deck.add(s)
    provisional = [r for r in rows if qa.is_provisional(r)]
    pending = [r for r in rows if r["状態"].strip() != qa.DONE and not qa.is_provisional(r)]
    prov_title = f"{ctx['provisional_lead']}利用者にまだ確かめていない決定（{len(provisional)} 件）"
    if provisional:
        for s in table_slides(prov_title, ["質問", "回答"], [[plain(r["質問"], opts.strip), plain(r["回答"], opts.strip)] for r in provisional], [0.6, 0.4], size=12,
                              note="暫定で採った回答で、利用者の合意ではない。"):
            deck.add(s)
    else:
        s = Slide()
        s.title(prov_title)
        s.box(MARGIN, CY0, CONTENT_W, 600000, paras("（ありません）", 20, color=GREY))
        deck.add(s)
    if pending:
        for s in table_slides(f"承認の時点で未決定の質問（{len(pending)} 件）", ["質問", "費用への影響"],
                              [[plain(r["質問"], opts.strip), plain(r["費用への影響"], opts.strip) or "—"] for r in pending], [0.65, 0.35], size=12):
            deck.add(s)
    for s in cost_slides(ctx["estimate"], categories, md_name):
        deck.add(s)
    for s in gantt_slides(ctx["schedule"]):
        deck.add(s)
    return deck.parts(), []


def spec_deck(ctx: dict, opts: Options) -> tuple[list[tuple[str, str | bytes]], list[str]]:
    """(部品, PNG にできなかった図のパス)。"""
    deck = Deck(ctx["title"])
    deck.add(cover(ctx["title"], [f"版 v{ctx['version']}", "この仕様書は生成物で、決裁者の承認の記録ではありません。"]))
    for s in hand_slides(ctx["hand"], opts.strip):
        deck.add(s)
    scale = [[plain(name.replace("`", ""), opts.strip), value] for name, value in ctx["scale"] if not value.startswith("—")]
    for s in table_slides("規模", ["もの", "数"], scale, [0.7, 0.3], ["l", "r"], size=14):
        deck.add(s)
    figs, failed = figure_slides(ctx["figures"])
    if figs:
        for s in figs:
            deck.add(s)
    if failed:
        s = Slide()
        s.title("構成の図")
        s.box(MARGIN, CY0, CONTENT_W, 1400000,
              paras(f"図 {len(failed)} 枚は、SVG を PNG にする道具（rsvg-convert）が無いので載せていない。spec.md で見る。", 18, color=DARK))
        deck.add(s)
    notes = ([[plain(p.replace("`", "")), "書き出し（.svg）が無いので載せていない"] for p in ctx.get("missing", [])]
             + [[plain(line.replace("`", "")), "載せているが、書き出しが今のソースと合わない（仕様書（spec.md）の図にも載せている）"] for line in ctx.get("stale", [])])
    if notes:
        for s in table_slides("構成の図の注意", ["図", "状況"], notes, [0.5, 0.5], size=12):
            deck.add(s)
    if ctx["features"]:
        for s in table_slides("機能の一覧", ["機能"], [[plain(t, opts.strip) or fid] for fid, t in ctx["features"]], size=13):
            deck.add(s)
    if ctx.get("decision"):
        head, *body = ctx["decision"]
        size = 12 if len(head) <= 5 else 10
        for s in table_slides("決定表", head, body, size=size):
            deck.add(s)
    for s in out_of_scope_slides(ctx.get("out_of_scope"), opts.strip):
        deck.add(s)
    if ctx.get("changes"):
        for s in change_slides(ctx["changes"], opts.strip):
            deck.add(s)
    if ctx["files"]:
        for s in file_summary_slides("仕様と要求のファイル", ctx["files"], opts.strip, note="全部のパスは spec.md を見る"):
            deck.add(s)
    return deck.parts(), failed
