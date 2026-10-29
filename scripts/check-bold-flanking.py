#!/usr/bin/env python3
r"""太字の `**` が、CommonMark の flanking の規則で開け閉めできない形を検出する。

    python3 scripts/check-bold-flanking.py

なぜ必要か（#525。決めた値は #537）: **`**` の片側が句読点で、反対側が文字だと、CommonMark
（GitHub の描画）はそれを太字の開き・閉じとして扱わない。** `X**「…」**Y` は太字にならず、
`**` が字のまま残る——あるいは、残った `**` が別の `**` と組んで、意図しない範囲が太字になる。
**手で直す周が 3 度続き（#496・#516・#519）、どの周も一部しか見つけていなかった。**
#519 の後にも、`*` を残さない形の崩れが 4 箇所残っていた（#522〜#524）。

## 何を見るか

`plugins/` の下の Markdown（`*.md`）。段落（空行・見出し・リストの項・表の行・引用の始まり・区切り線・フェンスなどで区切る）ごとに、
`*` がちょうど 2 つ並んだ区切り（`**`）を前から順に拾い、**1 つ目を開き、2 つ目を閉じ**……と
著者の意図どおりに組んだとみなして、それぞれが CommonMark の規則で開け閉めできるかを見る:

- **開き**は left-flanking でなければならない——後ろが空白でなく、かつ
  「後ろが句読点でない」か「前が空白か句読点」。`X**「` は前が文字で後ろが句読点なので開けない。
- **閉じ**は right-flanking でなければならない——前が空白でなく、かつ
  「前が句読点でない」か「後ろが空白か句読点」。`」**Y` は前が句読点で後ろが文字なので閉じられない。

**句読点は ASCII の記号と Unicode の一般カテゴリ P**（cmark-gfm——GitHub の描画——の定義）。
**空白は空白・タブ・改行と一般カテゴリ Zs**。行頭・行末は空白として扱う。

## 何を守り、何を守らないか

守る:

- **開きの `**` が開けない形を落とす**（`X**「…」**`）。
- **閉じの `**` が閉じられない形を落とす**（`**「…」**Y`）。
- **対にならない `**` を落とす**——段落の中の `**` が奇数なら、最後の 1 つは字のまま残る。
- **段落をまたいで組まない**——空行・見出し（`#` と setext の `===` `---`）・リストの項・表の行で区切る（区切らないと、
  前の段落の閉じ忘れが後ろの段落の組み方を全部ずらす）。
- **段落の中では行をまたいで組む**——このリポジトリの本文は、太字を行の途中で折り返している。
- **`***`（太字の斜体）も太字の区切りとして数える**——数えないと、それより後ろの組み方が
  1 つずつずれる（`SKILL.md` の `***リポジトリで*…**` で実際にずれた）。
- **コードフェンスとコードスパンの中は見ない**——フェンスは開いたのと同じ字で、同じ長さ以上の列で閉じる（`markdown_fences.py`
  と同じ規則）。**ただし `markdown_fences.py` は使わない**——容れ物（引用の深さ・リストの項）を持たないので、
  引用の中のフェンスや、フェンスの中の `> ```` を正しく読めない（#525 の 2 パス目の関門が示した。#537 の手段からの逸脱）。
- **コードスパンの両端のバッククォートは句読点として残す**——GitHub の描画でも `**` の隣の
  バッククォートは句読点として数えられる（`X**` + コードスパン + `**Y` は崩れる。#519 が直した形）。
- **バックスラッシュで逃がした `*` は数えない**（`\**` の `\*` は字の `*` で、区切りではない）。
- **frontmatter（先頭の `---` から次の `---` まで）は見ない**——Markdown として描かれない。
- **免除は行ごとに印で名指しさせる**——その行に `bold-flanking-ok: <理由>` を書くと、
  **その行の崩れだけ**が免除される。**理由の無い印は効かない。** 本文に見せたくなければ
  HTML のコメント（`<!-- bold-flanking-ok: 理由 -->`）に書く。
- **免除の印もコードの外だけを拾う**——コードスパン・フェンスの中に例として書いた印は効かない。
- **崩れの無い行に置いた免除の印を落とす**——直したあとに残った印は、次に同じ行が崩れたときに
  黙って通してしまうので、残させない。**行だけの HTML のコメントに書いた印も拾って落とす**（その行に崩れは無いので効かない）。
- **`plugins/` に Markdown が 1 本も無ければ落とす**——何も見ていない検査を緑にしない。
- **コードスパンは段落の中でだけ組む**——閉じないバッククォートが後ろの段落を飲み込んで、崩れを黙って隠さない
  （ファイル全体で組んだ最初の版は、#519 の前の `SKILL.md` で崩れ 23 個のうち 21 個を見落とした）。
- **引用は深さで読む**——段落より深い引用（`>` が増える行）は段落を割り込む。浅い行・引用でない行は、
  ブロックの始まりでなければ段落の続き（lazy continuation）として組む。引用が終わると、中で開いたフェンスと
  コメントのブロックも閉じる。
- **リストの項は中身の桁で読む**——項の中の行（中身の桁まで字下げした行）は項の中として読み、字下げの浅い行は
  ブロックの始まり（項の印・区切り線・フェンス・コメント・見出し）なら項を閉じ、そうでなければ続きとして組む。
  **段落を割り込める項は、空でない `-` `*` `+` と、空でない `1.`（`1)`）だけ**——段落の途中の `2.` から始まる行は続きである。
  項を閉じて現れた項の印は、番号や種類によらず次の項として区切る。
- **区切り線（`***` `---` `___`）と、行頭の `<!--` で始まる HTML のコメントのブロックは段落の本文として見ない**
  ——引用・リストの項の中でも。GitHub はどちらも Markdown の本文として描かない（区切り線の `***` を対にならない `**` と数えない）。
  コメントのブロックは `<!--` から数えて最初の `-->` で閉じる（`<!-->` は同じ行で閉じる）。
- **フェンスとコメントのブロックは、文書の順に、先に始まったほうが勝つ**——コメントの中の ``` はフェンスを開かず、
  フェンスの中の `<!--` や `> ```` はコメントやフェンスを始めない。
- **段落の中の HTML のコメントは中身だけを伏せ、`<!--` と `-->` は句読点として残す**——`**…**<!-- 印 -->` の
  `**` の隣は `<` で、GitHub でも句読点である（伏せた字を文字と数えると、免除の印を置いた行が崩れて見える）。
- **段落の中のコメントとコードスパンは前から順に、先に始まったほうが勝つ**——コメントの中のバッククォートはスパンを開かない
  （開かせると、後ろの本物のバッククォートまでを伏せて崩れを隠す）。
- **インデントしたコードブロック（段落の外で、容れ物から 4 つ以上字下げした行）は見ない**——段落の中の字下げした行は続きとして組む。
- **表は区切りの行（`--- | ---`）で見分ける**——先頭の `|` があってもなくても、`|` で始まる行も段落の行として読み、区切りの行が来たら
  **段落の最後の行を見出しの行にして**（前の行は段落として残す）、見出しの行と以降の行を 1 行ずつの段落にする（GitHub と同じ。#562）。
  **見出しの行と区切りの行のセルの数が違えば表にしない**（外側の `|` と `\|` は数えない。`|` だけの行はセルを持たない）。
  **段落の続き（lazy continuation——浅い引用・項の字下げが足りない）の区切りの行は表を開かない**（`> a | b⏎--- | ---` は引用の段落）。
  **段落の途中の区切りの形の行は見出しの行にしない**——表を開けなかった区切りの行で、GitHub もそれを見出しにしない（`text⏎|---|---|⏎|---|---|`）。
- **表の行は `|` が無くても表の行として組む**——表は空行か、ブロックの始まり（見出し・引用・リストの項（番号も空の項も問わない）・フェンス・
  コメント・区切り線・インデントしたコード）か、容れ物が変わる（引用の深さが変わる・項の外へ出る）まで続く。GitHub と同じく、段落の続き
  （lazy continuation）にはならず、`===` の行や行だけのインライン HTML も表の行である（#562。#525 の狭いパスが示した穴）。
- **エラーの抜粋は元の行から切り出す**——判定はコードスパンとコメントの中身を伏せた文字列で行うが、抜粋は同じ位置で
  ファイルの元の行（引用の `>` も含む）から切る。伏せ字（`x` の並び）を見せない（#564。#525 の `/code-review` 1 パス目 CR1-9）。

守らない:

- **`__`・`*` 1 つ（斜体）・`*` が 4 つ以上の並び**——見るのは `*` が 2 つか 3 つ（`***` は太字の斜体）の区切りだけ。
  **これらが同じ段落に混ざると、CommonMark の実際の組み方とこの検査の組み方がずれうる。**
- **著者の意図が「前から順に組む」でない形**——`**` を字のまま見せたい段落（コードスパンに
  入れていない）は、組み方を推測できないので、崩れとして出る（免除の印で名指しする）。
- **リンクの URL・自動リンク・HTML の属性の中の `**`**——段落の本文として数える。
- **行頭の `<!--` で始まる行の、`-->` より後ろに書いた本文**——GitHub は行ごと HTML のブロックとして字のまま描くが、
  この検査は行ごと見ない（`**` が字のまま見えても落とさない）。
- **タブの字下げ・項の印の後ろの 5 つ以上の空白・リストの項の中の引用**——容れ物の桁は空白で数える近似である。
- **表のセルをまたいで組んだ形**——表は 1 行を 1 段落として組む。セルごとには分けない。
- **HTML のブロック（`<div>` など）で表を終わらせない**——コメントのほかの HTML のブロックを持たない。
- **一般カテゴリ S の記号**（`→` `×` など ASCII 以外の記号）を句読点として扱わない——cmark-gfm と同じ。
  **CommonMark 0.31 は S も句読点に数える**ので、新しい版の描画器とは判定がずれうる。
- **`plugins/` の外**（`docs/`・`CLAUDE.md`・計画ファイル）——#537 で、最初の対象を `plugins/` に決めた。
- **これは「描画が崩れていない」の証明ではない。** **`**` の開け閉めという、実際に 3 度起きた
  1 つの形の検査**である。
"""

from __future__ import annotations

import pathlib
import re
import string
import sys
import unicodedata


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET_DIR = "plugins"

# 免除。**理由を名指しさせる**——理由の無い印は効かない。HTML のコメントの閉じは理由に含めない。
EXEMPT = re.compile(r"bold-flanking-ok:[ \t]*((?:(?!-->)\S)(?:(?!-->).)*)")

# 行の頭の容れ物（引用の `>`）。1 つずつ剥がして深さを数える。
QUOTE_MARK = re.compile(r" {0,3}>[ ]?")
# リストの項（容れ物の中で見る）。`(印の前の空白, 印, 印の後ろの空白, 中身)`。
BULLET = re.compile(r"( {0,3})([-*+])(?:([ \t]+)(.*)|$)")
ORDERED = re.compile(r"( {0,3})(\d{1,9})[.)](?:([ \t]+)(.*)|$)")
HEADING = re.compile(r" {0,3}#{1,6}(?:[ \t]|$)")
# 区切り線（`***` `---` `___`・空白を挟んでもよい）。段落の本文ではない。
THEMATIC = re.compile(r" {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
# setext の下線（段落の直後の `===` `---`）。段落を見出しにして終わらせる。
SETEXT = re.compile(r" {0,3}(?:=+|-+)[ \t]*$")
FENCE_OPEN = re.compile(r" {0,3}(`{3,}(?=[^`]*$)|~{3,})")
# 行頭の `<!--` は HTML のブロックを始め、`-->` を含む行で終わる——中は Markdown として描かれない。
COMMENT_BLOCK = re.compile(r" {0,3}<!--")
# 表の区切りの行（`--- | ---`・`|:--|--:|`）。直前の 1 行が見出しの行になる。
TABLE_DELIM = re.compile(r" {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")

ASCII_PUNCT = set(string.punctuation)


def is_space(char: str | None) -> bool:
    """行頭・行末（`None`）も空白として扱う。"""
    if char is None:
        return True
    return char in " \t\n\r\f" or unicodedata.category(char) == "Zs"


def is_punct(char: str | None) -> bool:
    if char is None:
        return False
    return char in ASCII_PUNCT or unicodedata.category(char).startswith("P")


def left_flanking(before: str | None, after: str | None) -> bool:
    if is_space(after):
        return False
    return not is_punct(after) or is_space(before) or is_punct(before)


def right_flanking(before: str | None, after: str | None) -> bool:
    if is_space(before):
        return False
    return not is_punct(before) or is_space(after) or is_punct(after)


def strip_frontmatter(text: str) -> str:
    """先頭の `---` から次の `---` までを空行にする（行数を保つ）。"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    for end in range(1, len(lines)):
        if lines[end].strip() == "---":
            return "\n".join([""] * (end + 1) + lines[end + 1:])
    return text


def mask_inline(text: str) -> tuple[str, str]:
    """段落の中のコードスパンと HTML のコメントを伏せる。`(区切りを数える本文, 免除の印を拾う本文)` を返す。

    **前から順に、先に始まったほうが勝つ**（CommonMark の規則）——コメントの中のバッククォートはスパンを開かず、
    コードスパンの中の `<!--` はコメントを開かない。
    - **コードスパン**は中身を `x` に置き換え、**両端のバッククォートは残す**（句読点として数える）。
      開きの列と**同じ長さの**列で閉じる。閉じが無ければ字のまま。どちらの本文でも伏せる（中の印は効かない）。
    - **HTML のコメント**は中身だけを `x` に置き換え、**`<!--` と `-->` は残す**（`<` `>` は句読点）。
      免除の印はコメントに書くので、印を拾う本文では伏せない。
    逃がした字（`\\`` など）は何も開かない。改行は残す（行の位置を保つ）。
    """
    runs_out, marks_out = list(text), list(text)
    i, n = 0, len(text)
    while i < n:
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if text.startswith("<!--", i):
            close = text.find("-->", i + 4)
            if close < 0:
                i += 4
                continue
            for p in range(i + 4, close):
                if runs_out[p] != "\n":
                    runs_out[p] = "x"
            i = close + 3
            continue
        if char != "`":
            i += 1
            continue
        j = i
        while j < n and text[j] == "`":
            j += 1
        run = j - i
        k, close = j, -1
        while k < n:
            if text[k] != "`":
                k += 1
                continue
            m = k
            while m < n and text[m] == "`":
                m += 1
            if m - k == run:
                close = k
                break
            k = m
        if close < 0:
            i = j
            continue
        for p in range(j, close):
            if runs_out[p] != "\n":
                runs_out[p] = marks_out[p] = "x"
        i = close + run
    return "".join(runs_out), "".join(marks_out)


def quote_depth(line: str, limit: int | None = None) -> tuple[int, int]:
    """行の頭の引用の印を最大 `limit` 個剥がし、`(深さ, 剥がした字数)` を返す。"""
    depth, pos = 0, 0
    while limit is None or depth < limit:
        m = QUOTE_MARK.match(line, pos)
        if not m:
            break
        depth, pos = depth + 1, m.end()
    return depth, pos


def indent_of(text: str) -> int:
    return len(text) - len(text.lstrip(" "))


def cells(row: str) -> int:
    """表の行のセルの数。外側の `|` と、逃がした `\\|` は区切りに数えない。"""
    text = row.strip()
    parts = re.split(r"(?<!\\)\|", text)
    if text.startswith("|"):
        parts = parts[1:]
    if parts == [""]:
        return 0  # `|` だけの行はセルを持たない（GitHub は表にしない）
    if len(parts) > 1 and re.search(r"(?<!\\)\|$", text):
        parts = parts[:-1]
    return len(parts)


def is_delim(text: str) -> bool:
    """表の区切りの行の形か（`|` を含むもの）。"""
    return "|" in text and TABLE_DELIM.match(text) is not None


def item_of(inner: str):
    """リストの項なら `(順序つきか, 番号, 中身が空か, 中身の始まる桁)` を返す。"""
    m = BULLET.match(inner) or ORDERED.match(inner)
    if not m:
        return None
    ordered = m.re is ORDERED
    body = m.group(4) or ""
    gap = len(m.group(3) or "")
    marker_end = m.end(2) if not ordered else m.start(3) if m.group(3) is not None else len(inner)
    content = marker_end + (gap if 1 <= gap <= 4 else 1)
    return ordered, (m.group(2) if ordered else ""), not body.strip(), content


def blocks(lines: list[str]):
    """段落ごとに `(先頭の行番号, [行, …])` を、本文でない行の免除の印の行番号と一緒に返す。

    **1 行ずつ、文書の順に** 容れ物（引用の深さ・リストの項の中身の桁）と、開いているフェンス・HTML のコメントの
    ブロック・表を持ちながら読む——別々の段で剥がすと、段の順番が CommonMark の読み方とずれる
    （1 パス目の指摘対応の版は、フェンスの中の `> ```` でフェンスを閉じ、コメントの中の ``` でフェンスを開いた）。
    段落の行は、引用の印を同じ数の空白に置き換えて返す（`> **太字**` の `**` の前は行頭＝空白）。
    """
    out: list[tuple[int, list[str]]] = []
    marks: list[int] = []
    para: list[str] = []
    para_start = para_depth = 0
    lists: list[int] = []  # 開いているリストの項の、中身の始まる桁（引用を剥がした後の桁）
    fence = None  # (字, 長さ, 引用の深さ, リストの桁)
    comment = None  # 引用の深さ
    table = None  # 開いている表の容れ物 (引用の深さ, 開いているリストの項の数)
    last = ""  # 段落の最後の行の、容れ物を剥がした本文（表の見出しの行の候補）

    def flush():
        nonlocal para
        if para:
            out.append((para_start, para))
        para = []

    for lineno, line in enumerate(lines, 1):
        if fence is not None:
            char, length, depth, base = fence
            got, pos = quote_depth(line, depth)
            rest = line[pos:]
            if got < depth or (rest.strip() and indent_of(rest) < base):
                fence = None  # 容れ物が終わればフェンスも閉じる
            else:
                if re.match(rf" {{0,3}}{re.escape(char)}{{{length},}}[ \t]*$", rest[base:] if len(rest) >= base else rest):
                    fence = None
                continue
        if comment is not None:
            got, pos = quote_depth(line, comment)
            if got < comment:
                comment = None
            else:
                if EXEMPT.search(line):
                    marks.append(lineno)
                if "-->" in line[pos:]:
                    comment = None
                continue

        depth, pos = quote_depth(line)
        content = line[pos:]
        shown = " " * pos + content
        if not content.strip():
            flush()
            table = None
            continue

        # 新しい引用（段落より深い）は段落を割り込む。浅い行は続き（lazy continuation）として下で扱う。
        if para and depth > para_depth:
            flush()

        indent = indent_of(content)
        popped = False
        stripped = content[indent:]
        starts_block = any(r.match(stripped) for r in (THEMATIC, FENCE_OPEN, COMMENT_BLOCK, HEADING)) \
            or item_of(stripped) is not None
        while lists and indent < lists[-1]:
            if para and not starts_block:
                break  # 項の中の段落の続き（lazy continuation）。ブロックの始まりなら項を閉じる（別の種類のリストの項でも）
            lists.pop()
            popped = True
        base = lists[-1] if lists and indent >= lists[-1] else 0
        inner = content[base:] if indent >= base else content.lstrip(" ")
        lazy = bool(lists) and indent < lists[-1]

        if table is not None:
            # 表は空行・ブロックの始まり・容れ物の変化で終わる。それ以外の行は `|` が無くても表の行（#562）
            if (depth, len(lists)) != table or item_of(inner) is not None or indent_of(inner) >= 4 \
                    or any(r.match(inner) for r in (THEMATIC, FENCE_OPEN, COMMENT_BLOCK, HEADING)):
                table = None
            else:
                out.append((lineno, [shown]))
                continue

        if THEMATIC.match(inner):  # 区切り線（段落の直後の `---` は setext の下線——どちらも段落を終わらせる）
            flush()
            continue
        if para and not lazy and SETEXT.match(inner):
            flush()
            continue

        item = None if lazy else item_of(inner)
        if item is not None:
            ordered, number, empty, offset = item
            if para and not popped and (empty or (ordered and number != "1")):
                item = None  # 空の項と `1.` 以外の番号の項は、段落を割り込めない
        if item is not None:
            flush()
            lists.append(base + offset)
            inner = inner[offset:] if len(inner) >= offset else ""
            if THEMATIC.match(inner):
                continue
            if not inner.strip():
                continue

        fence_open = FENCE_OPEN.match(inner)
        if fence_open:
            flush()
            run = fence_open.group(1)
            fence = (run[0], len(run), depth, lists[-1] if lists else 0)
            continue
        if COMMENT_BLOCK.match(inner):
            flush()
            if EXEMPT.search(line):
                marks.append(lineno)
            if "-->" not in inner[inner.index("<!--"):]:
                comment = depth
            continue
        if not para and indent_of(inner) >= 4:
            continue  # インデントしたコードブロック
        if HEADING.match(inner):
            flush()
            out.append((lineno, [shown]))
            continue
        if para and not lazy and depth == para_depth and "|" in inner and TABLE_DELIM.match(inner) \
                and cells(last) == cells(inner) and not (len(para) > 1 and is_delim(last)):
            # 区切りの行（段落の続きでないもの）は、段落の最後の行を見出しの行にして表を開く（#562）。
            # 段落の途中の区切りの形の行は、表を開けなかった区切りの行で、見出しの行にならない（GitHub と同じ）
            head = para.pop()
            flush()
            out.append((lineno - 1, [head]))
            table = (depth, len(lists))
            continue
        if not para:
            para_start, para_depth = lineno, depth
        para.append(shown)
        last = inner
    flush()
    return out, marks


def runs(text: str):
    """逃がしていない `*` の並びのうち、太字の区切りを含むもの（2 つか 3 つ）の `(位置, 長さ)` を返す。

    **3 つ（`***`）は太字と斜体を同時に開け閉めする**ので、太字の区切りとして数える——
    数えないと、それより後ろの組み方が 1 つずつずれる（`SKILL.md` の `***リポジトリで*…**` で実際にずれた）。
    """
    i, n = 0, len(text)
    while i < n:
        char = text[i]
        if char == "\\":
            i += 2  # 逃がした字（`\*`）は区切りにならない
            continue
        if char != "*":
            i += 1
            continue
        j = i
        while j < n and text[j] == "*":
            j += 1
        if j - i in (2, 3):
            yield i, j - i
        i = j


def scan(text: str) -> tuple[list[tuple[int, str, str]], list[int]]:
    """崩れ `(行番号, 理由, 断片)` の一覧と、使われなかった免除の印の行番号を返す。"""
    found_blocks, comment_marks = blocks(strip_frontmatter(text).split("\n"))

    problems: list[tuple[int, str, str]] = []
    # 本文でない行（HTML のコメントのブロック）に書いた印も拾う——その行に崩れは無いので、残った印として落ちる。
    exempt: set[int] = set(comment_marks)
    # **段落を先に切り、コードスパンは段落の中でだけ組む**——コードスパンは段落をまたがない。
    # ファイル全体で組むと、閉じない 1 つのバッククォートが後ろの段落を全部飲み込み、崩れが黙って消える
    # （#519 の前の `SKILL.md` で、301 行の入れ子のバッククォートが 135 行を飲み、崩れ 23 個のうち 21 個が見えなくなった）。
    source = text.split("\n")
    for start, block in found_blocks:
        joined, marks = mask_inline("\n".join(block))
        # 抜粋は元の行から切る（#564）——伏せ字（`x`）を見せない。段落の行は元のファイルの連続した行で、
        # 引用の印を同じ数の空白に置き換えただけなので長さが同じ——伏せ字の文字列と同じ位置で切れる。
        original = "\n".join(source[start - 1:start - 1 + len(block)])
        exempt.update(start + row for row, line in enumerate(marks.split("\n")) if EXEMPT.search(line))
        offsets = [0]
        for line in block:
            offsets.append(offsets[-1] + len(line) + 1)
        found = list(runs(joined))
        for index, (pos, length) in enumerate(found):
            before = joined[pos - 1] if pos > 0 else None
            after = joined[pos + length] if pos + length < len(joined) else None
            row = next(r for r in range(len(block)) if offsets[r + 1] > pos)
            lineno = start + row
            fragment = original[max(0, pos - 6):pos + 8].replace("\n", "⏎")
            if index % 2 == 0:
                if index == len(found) - 1:
                    reason = "対になる `**` が段落の中に無い（字のまま残る）"
                elif not left_flanking(before, after):
                    reason = "開きの `**` が開けない（前が文字で、後ろが句読点）" if is_punct(after) \
                        else "開きの `**` が開けない（後ろが空白）"
                else:
                    continue
            elif not right_flanking(before, after):
                reason = "閉じの `**` が閉じられない（前が句読点で、後ろが文字）" if is_punct(before) \
                    else "閉じの `**` が閉じられない（前が空白）"
            else:
                continue
            problems.append((lineno, reason, fragment))

    hit = {lineno for lineno, _, _ in problems}
    kept = [p for p in problems if p[0] not in exempt]
    unused = sorted(exempt - hit)
    return kept, unused


def targets(root: pathlib.Path):
    base = root / TARGET_DIR
    if not base.is_dir():
        return
    for path in sorted(base.rglob("*.md")):
        if path.is_file():
            yield path.relative_to(root), path


def main(argv=None) -> int:
    root = pathlib.Path(argv[0]) if argv else REPO_ROOT
    problems = []
    unused_marks = []
    checked = 0
    for rel, path in targets(root):
        checked += 1
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            problems.append((rel, 0, f"読めない（{exc.__class__.__name__}）", ""))
            continue
        found, unused = scan(text)
        problems.extend((rel, lineno, reason, fragment) for lineno, reason, fragment in found)
        unused_marks.extend((rel, lineno) for lineno in unused)

    if checked == 0:
        print(f"ERROR: {TARGET_DIR}/ の下に Markdown が 1 本も無い——何も見ていない", file=sys.stderr)
        return 1

    if problems or unused_marks:
        if problems:
            print("ERROR: 太字の `**` が CommonMark の規則で開け閉めできません:", file=sys.stderr)
            for rel, lineno, reason, fragment in problems:
                print(f"ERROR:   {rel}:{lineno}: {reason}: …{fragment}…", file=sys.stderr)
        if unused_marks:
            print("ERROR: 崩れの無い行に免除の印（bold-flanking-ok:）が残っています:", file=sys.stderr)
            for rel, lineno in unused_marks:
                print(f"ERROR:   {rel}:{lineno}", file=sys.stderr)
        print("ERROR:", file=sys.stderr)
        print("ERROR: `**` の外側（句読点の側ではなく文字の側）に空白を足すと直る（#496・#516・#519）。",
              file=sys.stderr)
        print("ERROR: わざと崩した例なら、その行に `<!-- bold-flanking-ok: <理由> -->` を書くこと（#537）。",
              file=sys.stderr)
        return 1

    print(f"太字の flanking の検査: 問題なし（{TARGET_DIR}/ の Markdown {checked} 本を走査）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
