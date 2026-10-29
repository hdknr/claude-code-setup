#!/usr/bin/env python3
r"""太字の `**` が、CommonMark の flanking の規則で開け閉めできない形を検出する。

    python3 scripts/check-bold-flanking.py

なぜ必要か（#525。決めた値は #537）: **`**` の片側が句読点で、反対側が文字だと、CommonMark
（GitHub の描画）はそれを太字の開き・閉じとして扱わない。** `X**「…」**Y` は太字にならず、
`**` が字のまま残る——あるいは、残った `**` が別の `**` と組んで、意図しない範囲が太字になる。
**手で直す周が 3 度続き（#496・#516・#519）、どの周も一部しか見つけていなかった。**
#519 の後にも、`*` を残さない形の崩れが 4 箇所残っていた（#522〜#524）。

## 何を見るか

`plugins/` の下の Markdown（`*.md`）。段落（空行・見出し・リストの項・表の行・引用の始まりで区切る）ごとに、
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
- **段落をまたいで組まない**——空行・見出し・リストの項・表の行で区切る（区切らないと、
  前の段落の閉じ忘れが後ろの段落の組み方を全部ずらす）。
- **段落の中では行をまたいで組む**——このリポジトリの本文は、太字を行の途中で折り返している。
- **`***`（太字の斜体）も太字の区切りとして数える**——数えないと、それより後ろの組み方が
  1 つずつずれる（`SKILL.md` の `***リポジトリで*…**` で実際にずれた）。
- **コードフェンスとコードスパンの中は見ない**（フェンスは `markdown_fences.py`）。
- **コードスパンの両端のバッククォートは句読点として残す**——GitHub の描画でも `**` の隣の
  バッククォートは句読点として数えられる（`X**` + コードスパン + `**Y` は崩れる。#519 が直した形）。
- **バックスラッシュで逃がした `*` は数えない**（`\**` の `\*` は字の `*` で、区切りではない）。
- **frontmatter（先頭の `---` から次の `---` まで）は見ない**——Markdown として描かれない。
- **免除は行ごとに印で名指しさせる**——その行に `bold-flanking-ok: <理由>` を書くと、
  **その行の崩れだけ**が免除される。**理由の無い印は効かない。** 本文に見せたくなければ
  HTML のコメント（`<!-- bold-flanking-ok: 理由 -->`）に書く。
- **免除の印もコードの外だけを拾う**——コードスパン・フェンスの中に例として書いた印は効かない。
- **崩れの無い行に置いた免除の印を落とす**——直したあとに残った印は、次に同じ行が崩れたときに
  黙って通してしまうので、残させない。
- **`plugins/` に Markdown が 1 本も無ければ落とす**——何も見ていない検査を緑にしない。
- **コードスパンは段落の中でだけ組む**——閉じないバッククォートが後ろの段落を飲み込んで、崩れを黙って隠さない
  （ファイル全体で組んだ最初の版は、#519 の前の `SKILL.md` で崩れ 23 個のうち 21 個を見落とした）。
- **引用の始まりで段落を区切る**——引用は段落を割り込む。引用でない行が引用の段落に続くのは続き（lazy continuation）として組む。
- **番号つきの項が段落を割り込めるのは `1.`（`1)`）だけ**——段落の途中で `2.` から始まる行は本文の続きである。
  リストの項で始まった段落では、次の番号の行は隣の項として区切る。
- **区切り線（`***` `---` `___`）と、行頭の `<!--` で始まる HTML のコメントのブロックは段落の本文として見ない**
  ——GitHub はどちらも Markdown の本文として描かない（区切り線の `***` を対にならない `**` と数えない）。
- **引用の中のフェンスも剥がす**——`>` を剥がしてからフェンスを探す。
- **段落の中の HTML のコメントは中身だけを伏せ、`<!--` と `-->` は句読点として残す**——`**…**<!-- 印 -->` の
  `**` の隣は `<` で、GitHub でも句読点である（伏せた字を文字と数えると、免除の印を置いた行が崩れて見える）。
- **コメントとコードスパンは前から順に、先に始まったほうが勝つ**——コメントの中のバッククォートはスパンを開かない
  （開かせると、後ろの本物のバッククォートまでを伏せて崩れを隠す）。

守らない:

- **`__`・`*` 1 つ（斜体）・`*` が 4 つ以上の並び**——見るのは `*` が 2 つか 3 つ（`***` は太字の斜体）の区切りだけ。
  **これらが同じ段落に混ざると、CommonMark の実際の組み方とこの検査の組み方がずれうる。**
- **著者の意図が「前から順に組む」でない形**——`**` を字のまま見せたい段落（コードスパンに
  入れていない）は、組み方を推測できないので、崩れとして出る（免除の印で名指しする）。
- **リンクの URL・自動リンク・HTML の属性の中の `**`**——段落の本文として数える。
- **行頭の `<!--` で始まる行の、`-->` より後ろに書いた本文**——GitHub は行ごと HTML のブロックとして字のまま描くが、
  この検査は行ごと見ない（`**` が字のまま見えても落とさない）。
- **インデントしたコードブロック**（4 つの空白で始まる行）——段落の本文として数える。
- **表のセルをまたいで組んだ形**——表は 1 行を 1 段落として組む。セルごとには分けない。
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from markdown_fences import strip_fences  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET_DIR = "plugins"

# 免除。**理由を名指しさせる**——理由の無い印は効かない。HTML のコメントの閉じは理由に含めない。
EXEMPT = re.compile(r"bold-flanking-ok:[ \t]*((?:(?!-->)\S)(?:(?!-->).)*)")

# 段落を始める行（引用の `>` を剥がしたあとに見る）。見出し・表の行は 1 行で段落が終わる。
BULLET = re.compile(r"[-*+](?:[ \t]|$)")
ORDERED = re.compile(r"(\d{1,9})[.)](?:[ \t]|$)")
HEADING = re.compile(r"#{1,6}(?:[ \t]|$)")
QUOTE = re.compile(r"[ \t]*(?:>[ \t]?)*")
# 区切り線（`***` `---` `___`・空白を挟んでもよい）と setext の下線。段落の本文ではない。
THEMATIC = re.compile(r" {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
# 行頭の `<!--` は HTML のブロックを始め、`-->` を含む行で終わる——中は Markdown として描かれない。
COMMENT_BLOCK = re.compile(r" {0,3}<!--")

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


def unquote(lines: list[str]) -> tuple[list[str], list[bool]]:
    """引用の `>` を同じ数の空白に置き換えた行と、引用の行かどうかを返す（字の位置を保つ）。

    CommonMark は引用の印を剥がしてから中を読むので、`> **太字**` の `**` の前は行頭（空白）である。
    """
    bodies, quoted = [], []
    for line in lines:
        prefix = QUOTE.match(line).group(0)
        bodies.append(" " * len(prefix) + line[len(prefix):])
        quoted.append(">" in prefix)
    return bodies, quoted


def blank_non_paragraphs(lines: list[str]) -> list[str]:
    """HTML のコメントのブロックと区切り線を空行にする（行数を保つ）。どちらも段落の本文ではない。"""
    out = list(lines)
    i = 0
    while i < len(out):
        if COMMENT_BLOCK.match(out[i]):
            head = out[i].index("<!--") + 4
            j = i
            while j < len(out) and "-->" not in (out[j][head:] if j == i else out[j]):
                j += 1
            for k in range(i, min(j, len(out) - 1) + 1):
                out[k] = ""
            i = j + 1
            continue
        if THEMATIC.match(out[i]):
            out[i] = ""
        i += 1
    return out


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


def blocks(lines: list[str], quoted: list[bool]):
    """段落ごとに `(先頭の行番号, [行, …])` を返す。行番号は 1 始まり。

    区切るのは: 空行・見出し・表の行（どちらも 1 行で終わる）・リストの項・引用の始まり。
    **番号つきの項が段落を割り込めるのは `1.` だけ**（CommonMark）——ただしリストの項で始まった段落では、
    次の番号の行は隣の項である。**引用でない行が引用の段落に続くのは、割り込みではなく続き**（lazy continuation）。
    """
    current: list[str] = []
    start = 0
    in_list = False
    for lineno, (line, is_quote) in enumerate(zip(lines, quoted), 1):
        body = line.lstrip()
        if not body:
            if current:
                yield start, current
            current = []
            continue
        single = bool(HEADING.match(body)) or body.startswith("|")
        ordered = ORDERED.match(body)
        item = bool(BULLET.match(body)) or bool(ordered and (ordered.group(1) == "1" or in_list))
        enters_quote = is_quote and not quoted[lineno - 2]
        if current and (single or item or enters_quote):
            yield start, current
            current = []
        if not current:
            start = lineno
            in_list = bool(BULLET.match(body) or ordered)
        current.append(line)
        if single:
            yield start, current
            current = []
    if current:
        yield start, current


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
    bodies, quoted = unquote(strip_frontmatter(text).split("\n"))
    plain = blank_non_paragraphs(strip_fences("\n".join(bodies)).split("\n"))

    problems: list[tuple[int, str, str]] = []
    exempt: set[int] = set()
    # **段落を先に切り、コードスパンは段落の中でだけ組む**——コードスパンは段落をまたがない。
    # ファイル全体で組むと、閉じない 1 つのバッククォートが後ろの段落を全部飲み込み、崩れが黙って消える
    # （#519 の前の `SKILL.md` で、301 行の入れ子のバッククォートが 135 行を飲み、崩れ 23 個のうち 21 個が見えなくなった）。
    for start, block in blocks(plain, quoted):
        joined, marks = mask_inline("\n".join(block))
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
            fragment = joined[max(0, pos - 6):pos + 8].replace("\n", "⏎")
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
