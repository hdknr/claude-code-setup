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
**空行（段落を切る行）はこれより狭く、空白とタブだけの行**である（CommonMark と同じ。改行は読むときに `\n` にそろう）。

## 何を守り、何を守らないか

守る:

- **開きの `**` が開けない形を落とす**（`X**「…」**`）。
- **閉じの `**` が閉じられない形を落とす**（`**「…」**Y`）。
- **対にならない `**` を落とす**——段落の中の `**` が奇数なら、最後の 1 つは字のまま残る。
- **段落をまたいで組まない**——空行・見出し（`#` と setext の `===` `---`）・リストの項・表の行で区切る（区切らないと、
  前の段落の閉じ忘れが後ろの段落の組み方を全部ずらす）。**空行は空白とタブだけの行**——U+3000・NBSP・`\v`・`\f` だけの行は
  段落の行で、段落を切らない。中身がそれらの字だけの項は空の項ではない。表の行の頭のそれらの字と、行末の U+3000・NBSP はセルの中身で、
  行末の `\v`・`\f` は空白として剥がす（GitHub と同じ。#667）。
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
- **容れ物（引用・リストの項）は入れ子の順に読む**——行の頭から、開いている容れ物を外から順に当てる（引用は `>`、
  リストの項は中身の桁までの字下げ）。段落より深い引用（`>` が増える行）は段落を割り込む。当たらない容れ物のある行は、
  段落が開いていてブロックの始まりでなければ段落の続き（lazy continuation）として組む。容れ物が終わると、中で開いたフェンスと
  コメントのブロックも閉じる。**リストの項の中の引用も同じ**——`- > a | b⏎  > --- | ---` は項の中の引用の表である（#624）。
- **リストの項は中身の桁で読む**——項の中の行（中身の桁まで字下げした行）は項の中として読み、字下げの浅い行は
  ブロックの始まり（項の印・引用・区切り線・フェンス・コメント・見出し）なら項を閉じ、そうでなければ続きとして組む。
  **段落を割り込める項は、空でない `-` `*` `+` と、空でない番号が 1 の項だけ**——番号は値で比べる（`1.` `01.` `001)` は割り込む。#667）。
  段落の途中の `2.`・`00.` から始まる行は続きである。
  項を閉じて現れた項の印は、番号や種類によらず次の項として区切る。項の印の後ろに空白が 5 つ以上あれば、中身は印の 1 つ後ろから始まり、
  残りはインデントしたコードとして読む（GitHub と同じ。#563）。
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
  **区切りの行は `|` が無くてもよい**——`a⏎:--:` は 1 列の表である。**`|` もコロンも無い `---` は表にしない**——容れ物の中でタブで
  字下げした `>⇥---` でも setext の下線である（GitHub と同じ。#581）。
  **見出しの行と区切りの行のセルの数が違えば表にしない**（外側の `|` と `\|` は数えない。`|` だけの行はセルを持たない）。
  **段落の続き（lazy continuation——浅い引用・項の字下げが足りない）の区切りの行は表を開かない**（`> a | b⏎--- | ---` は引用の段落）。
  **段落の中で区切りの行が表を開けなかったら、その段落ではもう表を開かない**——GitHub と同じ（`text⏎|---|---|⏎|---|---|`・
  `x⏎|---|---|⏎y | z⏎|---|---|`）。**段落の続き（lazy）の区切りの形の行は表を試さないので、開けなかったことにならない**——その行を
  見出しにして、容れ物の中の区切りの行が表を開く（`> q⏎|---|---|⏎> |---|---|`。#580。#562 の狭いパス NP-1）。
  **容れ物から 4 桁以上（タブを含めて）字下げした区切りの形の行も表を試さない**——表を開かず、開けなかったことにもならない（GitHub と同じ）。
  **段落の続き（lazy）の見出しの行は、頭の字下げのあとの `|` を外側の `|` に数えない**——頭に空のセルが 1 つ増える（GitHub と同じ。
  `> q⏎  |---|⏎> |---|` は表にならず、`> q⏎  |a|b⏎> --- | --- | ---` は 3 列の表。#623）。
- **表の行は `|` が無くても表の行として組む**——表は空行か、ブロックの始まり（見出し・引用・リストの項（番号も空の項も問わない）・フェンス・
  コメント・区切り線・インデントしたコード）か、容れ物が変わる（引用の深さが変わる・項の外へ出る）まで続く。GitHub と同じく、段落の続き
  （lazy continuation）にはならず、`===` の行や行だけのインライン HTML も表の行である（#562。#525 の狭いパスが示した穴）。
- **エラーの抜粋は元の行から切り出す**——判定はコードスパンとコメントの中身を伏せた文字列で行うが、抜粋は同じ位置で
  ファイルの元の行（引用の `>` も含む。タブはタブのまま）から切る。伏せ字（`x` の並び）を見せない（#564。#525 の `/code-review` 1 パス目 CR1-9）。
- **`*` が 2 つか 3 つ並んだだけの行は、区切りに数えない**——段落の続きの行（4 桁以上字下げした `***`・`**` だけの行）の並びは
  前後が空白なので開きにも閉じにもならず、GitHub は字のまま描いて、前後の太字の組み方を変えない
  （`**a⏎⇥***⏎b**` は太字。数えると 2・3 行目を崩れと誤る。#624。#581 の狭いパス NP-3）。
- **タブは桁で数える**——行の頭から 4 桁ごとの位置まで進む（CommonMark と同じ）。引用の印の直後のタブは、印の後ろの空白 1 桁を
  そこから使う（`>⇥--- | ---` は 2 桁の字下げ）。ほかのタブは減らさない。容れ物の桁（リストの項の中身の桁・印の後ろの空白）・
  インデントしたコード・区切り線・見出しの下線・表の区切りの行と表の終わり、どれも同じ数え方である
  （`- a | b⏎⇥--- | ---` は項の中の表、`a | b⏎--- | ---⏎⇥foo` の 3 行目はインデントしたコード。#623・#624。#581 の狭いパス NP-2）。

守らない:

- **`__`・`*` 1 つ（斜体）・`*` が 4 つ以上の並び**——見るのは `*` が 2 つか 3 つ（`***` は太字の斜体）の区切りだけ。
  **これらが同じ段落に混ざると、CommonMark の実際の組み方とこの検査の組み方がずれうる。**
- **著者の意図が「前から順に組む」でない形**——`**` を字のまま見せたい段落（コードスパンに
  入れていない）は、組み方を推測できないので、崩れとして出る（免除の印で名指しする）。
- **リンクの URL・自動リンク・HTML の属性の中の `**`**——段落の本文として数える。
- **行頭の `<!--` で始まる行の、`-->` より後ろに書いた本文**——GitHub は行ごと HTML のブロックとして字のまま描くが、
  この検査は行ごと見ない（`**` が字のまま見えても落とさない）。
- **引用・リストの項の中で閉じ忘れた `<!--` の後ろの本文**——GitHub は容れ物が終わっても生の `<!--` を閉じず、次の `-->` までの本文を
  画面に描かない。この検査は容れ物の終わりでコメントのブロックも閉じたものとして読むので、**画面に出ない行の崩れを落とすことがある**
  （`> <!--⏎> x⏎⏎X**「例」**Y` の 4 行目。#606。閉じ忘れそのものが誤りで、落ちれば気づける——要確認 #607 で今のままと決めた）。
- **`*` が 2 つか 3 つ並んだだけの行の `**`**——字のまま描かれるが落とさない（守るの「区切りに数えない」）。
- **表のセルをまたいで組んだ形**——表は 1 行を 1 段落として組む。セルごとには分けない。
- **HTML のブロック（`<div>` など）で表を終わらせない**——コメントのほかの HTML のブロックを持たない。
- **一般カテゴリ S の記号**（`→` `×` など ASCII 以外の記号）を句読点として扱わない——cmark-gfm と同じ。
  **CommonMark 0.31 は S も句読点に数える**ので、新しい版の描画器とは判定がずれうる。
- **`plugins/` の外**（`docs/`・`CLAUDE.md`・計画ファイル）——#537 で、最初の対象を `plugins/` に決めた。
- **これは「描画が崩れていない」の証明ではない。** **`**` の開け閉めという、実際に 3 度起きた
  1 つの形の検査**である。
"""

from __future__ import annotations

import bisect
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
# 番号は ASCII の数字だけ（CommonMark と同じ）——`\d` は全角の `１` なども当たり、値が 1 になって段落を割り込む（#667）
ORDERED = re.compile(r"( {0,3})([0-9]{1,9})[.)](?:([ \t]+)(.*)|$)")
HEADING = re.compile(r" {0,3}#{1,6}(?:[ \t]|$)")
# 区切り線（`***` `---` `___`・空白を挟んでもよい）。段落の本文ではない。
THEMATIC = re.compile(r" {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
# setext の下線（段落の直後の `===` `---`）。段落を見出しにして終わらせる。
SETEXT = re.compile(r" {0,3}(?:=+|-+)[ \t]*$")
FENCE_OPEN = re.compile(r" {0,3}(`{3,}(?=[^`]*$)|~{3,})")
# 行頭の `<!--` は HTML のブロックを始め、`-->` を含む行で終わる——中は Markdown として描かれない。
COMMENT_BLOCK = re.compile(r" {0,3}<!--")
# 表の区切りの行（`--- | ---`・`|:--|--:|`・`|` の無い `:--:`）。直前の 1 行が見出しの行になる。
# `|` もコロンも無い `---` は、段落の直後なら先に setext の下線として読む（`blocks` の順。タブの字下げも桁で数える）。
TABLE_DELIM = re.compile(r" {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")

ASCII_PUNCT = set(string.punctuation)


def is_space(char: str | None) -> bool:
    """行頭・行末（`None`）も空白として扱う。"""
    if char is None:
        return True
    return char in " \t\n\r\f" or unicodedata.category(char) == "Zs"


def is_blank(text: str) -> bool:
    """空行か——空白とタブだけの行（CommonMark と同じ。CRLF は `read_text` が `\\n` にそろえるので、行に `\\r` は残らない）。

    `str.strip()` で判定しない——U+3000・NBSP・`\\v`・`\\f` まで剥がして、段落の行を空行と読む（#667。#623 の /code-review 2 パス目 CR2-1）。
    """
    return not text.strip(" \t")


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


def indent_of(text: str) -> int:
    return len(text) - len(text.lstrip(" "))


def expand_tabs(line: str) -> str:
    """構造（容れ物・字下げ・ブロックの始まり）の判定に使う行。タブを、**行の頭から** 4 桁ごとの位置まで進む空白に開く。

    CommonMark と同じ数え方である。引用の印 `>` の直後のタブは、開いた空白の 1 つ目を `QUOTE_MARK` が
    印の後ろの任意の空白として剥がす——「印の直後のタブは、印の後ろの空白 1 桁をそこから使う」と同じ結果になる
    （`>⇥---` は 2 桁の字下げ）。**ほかのタブは 1 桁も減らさない**（`- a⏎  ⇥  ---` の区切りの形の行は 4 桁の字下げ。#624）。
    """
    if "\t" not in line:
        return line
    out = ""
    for char in line:
        out += " " * (4 - len(out) % 4) if char == "\t" else char
    return out


def source_index(line: str, column: int) -> int:
    """`expand_tabs(line)` の桁 `column` が、元の行の何文字目に当たるか（タブの途中なら、そのタブの後ろ）。"""
    col = 0
    for index, char in enumerate(line):
        if col >= column:
            return index
        col += 4 - col % 4 if char == "\t" else 1
    return len(line)


def match_containers(text: str, stack: list) -> tuple[int, int]:
    """開いている容れ物を外から順に行の頭へ当て、`(当たった数, 本文の始まる桁)` を返す。

    引用（`">"`）は印で当たり、リストの項は中身の桁までの字下げか空行で当たる（CommonMark と同じ）。リストの項の中身の桁は、
    **外の容れ物の本文の始まりから数える**——行の頭からではない（`> - a⏎  > ===` の 2 行目は、`>` の位置がずれるので項に当たらない。#623 の Verifier 1 パス目）。
    """
    at = 0
    for count, container in enumerate(stack):
        if container == ">":
            quote = QUOTE_MARK.match(text, at)
            if not quote:
                return count, at
            at = quote.end()
        elif not is_blank(text[at:]):
            if indent_of(text[at:]) < container:
                return count, at
            at += container
    return len(stack), at


def cells(row: str) -> int:
    """表の行のセルの数。外側の `|` と、逃がした `\\|` は区切りに数えない。"""
    # 頭は空白とタブだけ、行末は `\v` `\f` も剥がす（cmark-gfm と同じ）。U+3000・NBSP はセルの中身（#667）
    text = row.lstrip(" \t").rstrip(" \t\v\f")
    parts = re.split(r"(?<!\\)\|", text)
    if text.startswith("|"):
        parts = parts[1:]
    if parts == [""]:
        return 0  # `|` だけの行はセルを持たない（GitHub は表にしない）
    if len(parts) > 1 and re.search(r"(?<!\\)\|$", text):
        parts = parts[:-1]
    return len(parts)


def header_cells(row: str, lazy: bool) -> int:
    """見出しの行の候補のセルの数。段落の続き（lazy）の行は頭の字下げを本文に残すので、字下げのあとの `|` は外側の `|` にならず、
    頭に空のセルが 1 つ増える（GitHub と同じ。`> q⏎  |a|b⏎> --- | --- | ---` は 3 列の表、`> q⏎  |---|⏎> |---|` は表にならない。
    #623 の Verifier 1 パス目 R2——main から食い違っていた）。"""
    extra = lazy and row[:1] == " " and row.lstrip(" ").startswith("|")
    return cells(row) + extra


def item_of(inner: str):
    """リストの項なら `(順序つきか, 番号の値, 中身が空か, 中身の始まる桁)` を返す。番号は値で持つ（`01.` は 1。#667）。"""
    m = BULLET.match(inner) or ORDERED.match(inner)
    if not m:
        return None
    ordered = m.re is ORDERED
    body = m.group(4) or ""
    gap = len(m.group(3) or "")
    marker_end = m.end(2) if not ordered else m.start(3) if m.group(3) is not None else len(inner)
    content = marker_end + (gap if 1 <= gap <= 4 else 1)
    return ordered, (int(m.group(2)) if ordered else 0), is_blank(body), content


def blocks(lines: list[str]):
    """段落ごとに `(先頭の行番号, [行, …])` を、本文でない行の免除の印の行番号と一緒に返す。

    **1 行ずつ、文書の順に** 容れ物（引用とリストの項を、外から順に積んだもの）と、開いているフェンス・HTML のコメントの
    ブロック・表を持ちながら読む——別々の段で剥がすと、段の順番が CommonMark の読み方とずれる
    （1 パス目の指摘対応の版は、フェンスの中の `> ```` でフェンスを閉じ、コメントの中の ``` でフェンスを開いた）。
    構造の判定はタブを桁に開いた行で行う（`expand_tabs`）。段落の行は、容れ物の印（引用の `>`・リストの項の印）を
    同じ数の空白に置き換えた元の行を返す（`> **太字**` の `**` の前は行頭＝空白。字の数は元の行と同じ）。
    """
    out: list[tuple[int, list[str]]] = []
    marks: list[int] = []
    para: list[str] = []
    para_start = 0
    stack: list = []  # 開いている容れ物（外から順）。引用は ">"、リストの項は中身の始まる桁（外の容れ物の本文の始まりから）
    fence = None  # (字, 長さ)。開いている間、容れ物は変わらない
    comment = False  # 開いている HTML のコメントのブロック
    table = False  # 開いている表（容れ物が変われば終わる）
    last = ""  # 段落の最後の行の、容れ物を剥がした本文（表の見出しの行の候補）
    lazy_last = False  # 段落の最後の行が段落の続き（lazy）か
    refused = False  # この段落で、区切りの行が表を開けなかったか（GitHub はその段落でもう表を開かない）
    starts = (THEMATIC, FENCE_OPEN, COMMENT_BLOCK, HEADING)  # 段落の続き（lazy）を許さないブロックの始まり

    def flush():
        nonlocal para
        if para:
            out.append((para_start, para))
        para = []

    for lineno, line in enumerate(lines, 1):
        text = expand_tabs(line)
        matched, at = match_containers(text, stack)
        if fence is not None:
            if matched < len(stack):
                fence = None  # 容れ物が終わればフェンスも閉じる
            else:
                if re.match(rf" {{0,3}}{re.escape(fence[0])}{{{fence[1]},}}[ \t]*$", text[at:]):
                    fence = None
                continue
        if comment:
            if matched < len(stack):
                comment = False  # 容れ物が終わればコメントのブロックも閉じる
            else:
                if EXEMPT.search(line):
                    marks.append(lineno)
                if "-->" in text[at:]:
                    comment = False
                continue

        if is_blank(text[at:]):
            flush()
            table = False
            del stack[matched:]  # 空行は、印の無い引用を閉じる（リストの項は空行では閉じない）
            continue

        # 当たった容れ物の中で、新しい容れ物（引用・リストの項）を開く。段落の続きになりうる行（容れ物の一部が当たらず、
        # 段落が開いている）では、項は段落を割り込まない——割り込みの規則が掛かるのは、段落と同じ容れ物の中の行だけ
        maybe_lazy = bool(para) and matched < len(stack)
        new: list = []
        pos = at
        while indent_of(text[pos:]) < 4:
            quote = QUOTE_MARK.match(text, pos)
            if quote:
                new.append(">")
                pos = quote.end()
                continue
            item = None if THEMATIC.match(text[pos:]) else item_of(text[pos:])
            if item is None:
                break
            ordered, number, empty, offset = item
            if para and not maybe_lazy and not new and (empty or (ordered and number != 1)):
                break  # 空の項と、番号の値が 1 でない項は、段落を割り込めない（`01.` は割り込む。#667）
            new.append(offset)
            pos += offset
        inner = text[pos:]
        start = source_index(line, pos)
        shown = " " * start + line[start:]

        if maybe_lazy and not new and not any(r.match(inner) for r in starts):
            para.append(shown)  # 段落の続き（lazy continuation）。容れ物は閉じない
            last, lazy_last = inner, True
            continue

        if table:
            # 表は空行・ブロックの始まり・容れ物の変化で終わる。それ以外の行は `|` が無くても表の行（#562）
            if matched == len(stack) and not new and indent_of(inner) < 4 and not any(r.match(inner) for r in starts):
                out.append((lineno, [shown]))
                continue
            table = False
        if matched < len(stack) or new:
            flush()  # 容れ物が終わる・始まる行は段落を終わらせる（深くなる引用・項の印）
            del stack[matched:]
            stack.extend(new)
        if is_blank(inner):
            continue  # 中身の無い項・引用の印だけの行

        if THEMATIC.match(inner):  # 区切り線（段落の直後の `---` は setext の下線——どちらも段落を終わらせる）
            flush()
            continue
        if para and SETEXT.match(inner):
            # 段落と同じ容れ物の中の行だけ（段落の続き（lazy）は上で終わっている）。字下げはタブを含めて桁で数える（#581）
            flush()
            continue
        fence_open = FENCE_OPEN.match(inner)
        if fence_open:
            flush()
            run = fence_open.group(1)
            fence = (run[0], len(run))
            continue
        if COMMENT_BLOCK.match(inner):
            flush()
            if EXEMPT.search(line):
                marks.append(lineno)
            if "-->" not in inner[inner.index("<!--"):]:
                comment = True
            continue
        if not para and indent_of(inner) >= 4:
            continue  # インデントしたコードブロック
        if HEADING.match(inner):
            flush()
            out.append((lineno, [shown]))
            continue
        if para and indent_of(inner) < 4 and TABLE_DELIM.match(inner):
            # `|` は要らない——`a⏎:--:` は 1 列の表（#581）。`|` もコロンも無い `---` は、上で setext の下線として先に終わっている
            # 区切りの行（段落と同じ容れ物の中の行）は、段落の最後の行を見出しの行にして表を開く（#562）。
            # 開けなければ、その段落ではもう開かない（GitHub と同じ）。段落の続き（lazy）と 4 桁以上字下げした
            # 区切りの形の行はここに来ない——表を試さないので、開けなかったことにならない（#580）
            if not refused and header_cells(last, lazy_last) == cells(inner):
                head = para.pop()
                flush()
                out.append((lineno - 1, [head]))
                table = True
                continue
            refused = True
        if not para:
            para_start = lineno
            refused = False
        para.append(shown)
        last, lazy_last = inner, False
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
        offsets = [0]  # 各行の頭の位置（狭義の増加）。run の行は二分探索で 1 度だけ引く——run ごとに頭から探さない（#667。#623 の CR1-8）
        for line in block:
            offsets.append(offsets[-1] + len(line) + 1)
        # `*` の並びだけの行は区切りに数えない——前後が空白で開きにも閉じにもならず、組み方を変えない（#624。#581 の NP-3）。
        # 空白は `is_space` で数える——`str.strip()` は `\v` など CommonMark が空白に数えない字まで剥がす（#623 の /code-review 1 パス目）
        bare = ["".join(c for c in row if not is_space(c)) for row in joined.split("\n")]
        found = []
        for pos, length in runs(joined):
            row = bisect.bisect_right(offsets, pos) - 1
            if bare[row] != "*" * length:
                found.append((pos, length, row))
        for index, (pos, length, row) in enumerate(found):
            before = joined[pos - 1] if pos > 0 else None
            after = joined[pos + length] if pos + length < len(joined) else None
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
