#!/usr/bin/env python3
r"""太字の `**` が、CommonMark の flanking の規則で開け閉めできない形を検出する。

    python3 scripts/check-bold-flanking.py

なぜ必要か（#525。決めた値は #537）: **`**` の片側が句読点で、反対側が文字だと、CommonMark
（GitHub の描画）はそれを太字の開き・閉じとして扱わない。** `X**「…」**Y` は太字にならず、
`**` が字のまま残る——あるいは、残った `**` が別の `**` と組んで、意図しない範囲が太字になる。
**手で直す周が 3 度続き（#496・#516・#519）、どの周も一部しか見つけていなかった。**
#519 の後にも、`*` を残さない形の崩れが 4 箇所残っていた（#522〜#524）。

## 何を見るか

`plugins/` の下の Markdown（`*.md`）。段落（空行・見出し・リストの項・表の行で区切る）ごとに、
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

守らない:

- **`__`・`*` 1 つ（斜体）・`*` が 4 つ以上の並び**——見るのは `*` が 2 つか 3 つ（`***` は太字の斜体）の区切りだけ。
  **これらが同じ段落に混ざると、CommonMark の実際の組み方とこの検査の組み方がずれうる。**
- **著者の意図が「前から順に組む」でない形**——`**` を字のまま見せたい段落（コードスパンに
  入れていない）は、組み方を推測できないので、崩れとして出る（免除の印で名指しする）。
- **リンクの URL・自動リンク・HTML の属性の中の `**`**——段落の本文として数える。
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
LIST_ITEM = re.compile(r"(?:[-*+]|\d+[.)])(?:[ \t]|$)")
HEADING = re.compile(r"#{1,6}(?:[ \t]|$)")
QUOTE = re.compile(r"[ \t]*(?:>[ \t]?)*")

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


def mask_code_spans(text: str) -> str:
    """コードスパンの中身を `x` に置き換える。**両端のバッククォートは残す**（句読点として数える）。

    開きのバッククォートの列と、**同じ長さの**列で閉じる（CommonMark の規則）。閉じが無ければ字のまま。
    逃がしたバッククォート（`\\``）はスパンを開かない。改行は残す（行の位置を保つ）。
    """
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        char = text[i]
        if char == "\\":
            i += 2
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
            if out[p] != "\n":
                out[p] = "x"
        i = close + run
    return "".join(out)


def mask_html_comments(text: str) -> str:
    """HTML のコメントの中身を `x` に置き換える（改行は残す）。免除の印を書く場所である。"""
    return re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", "x", m.group(0)), text, flags=re.S)


def blocks(lines: list[str]):
    """段落ごとに `(先頭の行番号, [行, …])` を返す。行番号は 1 始まり。"""
    current: list[str] = []
    start = 0
    for lineno, line in enumerate(lines, 1):
        body = line[QUOTE.match(line).end():]
        if not body.strip():
            if current:
                yield start, current
            current = []
            continue
        single = bool(HEADING.match(body)) or body.startswith("|")
        if current and (single or LIST_ITEM.match(body)):
            yield start, current
            current = []
        if not current:
            start = lineno
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
    plain = strip_fences(strip_frontmatter(text)).split("\n")

    problems: list[tuple[int, str, str]] = []
    exempt: set[int] = set()
    # **段落を先に切り、コードスパンは段落の中でだけ組む**——コードスパンは段落をまたがない。
    # ファイル全体で組むと、閉じない 1 つのバッククォートが後ろの段落を全部飲み込み、崩れが黙って消える
    # （#519 の前の `SKILL.md` で、301 行の入れ子のバッククォートが 135 行を飲み、崩れ 23 個のうち 21 個が見えなくなった）。
    for start, block in blocks(plain):
        code_free = mask_code_spans("\n".join(block))
        lines = code_free.split("\n")
        exempt.update(start + row for row, line in enumerate(lines) if EXEMPT.search(line))
        joined = mask_html_comments(code_free)
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
