#!/usr/bin/env python3
"""`check-bold-flanking.py` の回帰テスト。

    python3 scripts/test-check-bold-flanking.py

**このテストは実環境を触らない。** 毎回テンポラリに偽のツリー（`plugins/` を持つ）を作り、そこだけを対象にする
（`assert_not_real_repo` がそれを担保する）。本体は既定でこのリポジトリ自身を走査するので、
**歯止めが無いと、テストが実リポジトリを見て通ってしまう。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに結果が変わらなければ失格**とする。
**本体の「守る」の各行に、変異が 1 つ以上当たっているか**は、**テスト自身が数える**
（変異はどの「守る」を壊すかを番号で持つ）。

**実際に起きた崩れを試料に入れてある。** #519 が直した `SKILL.md` の行と、この周（#525）が直した
spec-loop の `agents/` の行を、直す前の形のまま置いている——**作り話ではなく、このリポジトリが実際に踏んだ形である。**
**どの試料も、GitHub の描画（`gh api -X POST /markdown`、`mode=gfm`）で崩れる・崩れないを確かめてある**（#525 の周）。
"""
import contextlib
import importlib.util
import io
import os
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "check-bold-flanking.py"

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"cbf_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


# 試料。名前 → 本文。期待は下の EXPECTED（行番号の組）で持つ。
SAMPLES = {
    # **実際に起きた形**（#519 が直す前の `SKILL.md`）——中央の `」**と**「` が組み、`と` 1 字だけが太字になった。
    "real-519.md": "手順 5 の**「実行されない主張は、関門に当てさせる」**と**「緑を疑う」**を、そのまま渡す。\n",
    # **実際に起きた形**（この周が直す前の spec-loop の `agents/red-team.md` 7・19 行）。
    "real-525.md": (
        "あなたは**仕様の批判役（Red Team）**です。\n"
        "\n"
        "  振り分けの案を**「範囲の外として記録する」「実装に渡す」**にして 1 行で挙げる。\n"),
    # 守る 1: 開けない（前が文字・後ろが句読点）。閉じは句読点の両側なので閉じられる。
    "open.md": "これは**「例」**、と書く。\n",
    # 守る 2: 閉じられない（前が句読点・後ろが文字）。
    "close.md": "これは **（例）**です。\n",
    # 守る 3: 対にならない（開ける形だが、相手が無い）。
    "unpaired.md": "前の **閉じ忘れ だけがある。\n",
    # 守る 4: 段落をまたいで組まない（空行・見出し・表の行・リストの項）。
    "split-blank.md": "前の段落の **閉じ忘れ\n\n次の段落の **太字** です。\n",
    "split-heading.md": "本文の **閉じ忘れ\n## 見出しの **太字** だ\n",
    "split-table.md": "| 前の **閉じ忘れ | x |\n| **太字** | y |\n",
    "split-list.md": "- 項目の **閉じ忘れ\n- 次の **太字** だ\n",
    # 守る 5: 段落の中では行をまたいで組む（崩れていない）。
    "multiline.md": "行を **またぐ\n太字** です。\n",
    # 守る 6: `***` も区切りとして数える（崩れていない。#519 の後の SKILL.md 869 行の形）。
    "triple.md": "- ***リポジトリで*走らせた、\n  報告に書かせる。**\n",
    # 守る 7: フェンス・コードスパンの中は見ない（崩れていない）。
    # **バッククォートを持たない `~~~` のフェンスを置く**——``` のフェンスだけだと、コードスパンを伏せる処理が
    # フェンスの行どうしを 1 つのスパンとして組んで中身を伏せてしまい、フェンスを剥がさなくても緑になる（変異が殺せない）。
    "code.md": (
        "例:\n\n~~~\nこれは**「例」**です。\n~~~\n\n"
        "```markdown\nこれは**「例」**です。\n```\n\n"
        "~~~~\n```\nX**「例」**Y\n```\n~~~~\n\n"
        "本文の `X**「例」**Y` と ``X**`「例」`**Y`` は字のまま。\n"),
    # 守る 8: コードスパンの隣のバッククォートは句読点（崩れる。#519 が直した形）。
    "backtick.md": "これは**`code`**です。\n",
    # 守る 9: 逃がした `*` は数えない（崩れていない——字の `*` と、`*` 1 つが残るだけ）。
    "escape.md": "字のまま \\** 見せる。\n",
    # 守る 10: frontmatter は見ない。
    "frontmatter.md": "---\nname: x\ndescription: これは**「例」**です。\n---\n\n本文の **太字** だ。\n",
    # 守る 11: 免除は行ごと・理由が要る。2 行目は免除、4 行目は免除していない、6 行目は理由の無い印。
    "exempt.md": (
        "わざと崩す **「例」**だ <!-- bold-flanking-ok: 崩れる形の例 -->\n"
        "\n"
        "免除していない **「例」**だ。\n"
        "\n"
        "理由の無い印 **「例」**だ <!-- bold-flanking-ok: -->\n"),
    # 守る 12: コードスパンの中に書いた印は効かない。
    "exempt-in-code.md": "崩れる **「例」**だ。印の例は `bold-flanking-ok: 例` と書く。\n",
    # 守る 13: 崩れの無い行の印は落とす。
    "exempt-unused.md": "崩れていない **「例」** だ <!-- bold-flanking-ok: 古い印 -->\n",
    # 守る 15: コードスパンは段落の中でだけ組む——1 段落目の閉じないバッククォートが 3 段落目まで飲み込まない。
    # **実際に起きた形**（#519 の前の `SKILL.md` 301 行の入れ子のバッククォートが 135 行を飲み、崩れ 21 個が見えなくなった）。
    "span-per-block.md": "閉じない `バッククォート\n\n次の段落の **「例」**だ。\n\n最後の `code` だ。\n",
    # 守る 16: 引用の始まりで区切る（#525 の /code-review 1 パス目 CR1-3。GitHub は 1 行目だけ `**` を字のまま残す）。
    "quote-start.md": "前の **閉じ忘れ\n> 引用の **太字** だ\n",
    # 守る 17: `2.` は段落を割り込まない（CR1-4。GitHub は 1 つの太字に組む）／リストの中の `2.` は隣の項。
    "ordered-cont.md": "本文 **太字\n2. 続き** だ\n",
    "ordered-items.md": "1. 項目の **閉じ忘れ\n2. 次の **太字** だ\n",
    # 守る 18: 区切り線・コメントのブロックは本文ではない（Verifier 1 パス目・CR1-2。GitHub は <hr> とコメントにする）。
    "hr-comment.md": "本文。\n\n***\n\n<!--\n古い例\n\nこれは**「a」**b\n-->\n\n次の **太字** だ。\n",
    # 守る 19: 引用の中のフェンス（CR1-7。GitHub はコードとして描く）。
    "quote-fence.md": "> ~~~\n> X**「例」**Y\n> ~~~\n",
    # 守る 20: コメントの区切りは句読点（CR1-1。GitHub は太字に組む）。
    "comment-edge.md": "これは **「例」**<!-- note --> だ。\n\n前 <!-- note -->**「例」** だ。\n\n中の <!-- **x --> は見ない **太字** だ。\n",
    # 守る 21: コメントの中のバッククォートはスパンを開かない（CR1-5。GitHub は `**` を字のまま残す）。
    "comment-backtick.md": "本文 <!-- ` --> X**「例」**Y `z`\n",
    # 守る 16: 引用の深さ——深くなる引用は割り込む（2 パス目 CR）／浅い行は続き（lazy）／引用が終わればフェンスも閉じる（2 パス目 V-R1）。
    # どれも GitHub の描画（gfm）と判定が一致することを確かめた（#525 の 2 パス目の指摘対応）。
    'quote-deeper.md': '> a **b\n>> c** d\n',
    'quote-lazy.md': '> a **b\nc\n> d** e\n',
    'quote-fence-unclosed.md': '> ~~~\n> code\n\ntext X**「b」**Y\n',
    # 守る 17: リストの項——項の中の続き（lazy）／ブロックの始まりは項を閉じる／`2.`・空の項は段落を割り込まない／項を閉じた印は次の項。
    # どれも GitHub の描画（gfm）と判定が一致することを確かめた（#525 の 2 パス目の指摘対応）。
    'list-lazy.md': '- 項目の **太字\n続き** だ\n',
    # 続きの行のあとも項は開いたまま——空行のあとの 4 つ字下げは項の中の段落で、コードではない（GitHub は崩れを描く）。
    'list-lazy-then-item.md': '- a\nlazy\n\n    X**「例」**Y\n',
    'list-fence.md': '- 項目 **太字** の\n続き\n```\nコード\n```\n\n本文 X**「例」**Y\n',
    'ordered-empty.md': '本文 **x\n1.\ny** z\n',
    'list-sibling.md': '1. a\n\n   b **x\n2. y** z\n',
    'list-icode.md': '- a\n\n      コード **x\n\n本文 **太字** だ\n',
    # 守る 18: 区切り線・コメントのブロック（引用・リストの中でも。`<!-->` は同じ行で閉じる）。
    # どれも GitHub の描画（gfm）と判定が一致することを確かめた（#525 の 2 パス目の指摘対応）。
    'nested-hr.md': '> > 本文\n> >\n> > ***\n\n- ***\n',
    'nested-comment.md': '> > <!--\n> > x\n> >\n> > **「a」**b\n> > -->\n',
    'comment-short.md': '<!-->\n本文 X**「例」**Y\n\n-->\n',
    # 守る 19: フェンスとコメントのブロックは先に始まったほうが勝つ（2 パス目 V-R2・CR）。
    # どれも GitHub の描画（gfm）と判定が一致することを確かめた（#525 の 2 パス目の指摘対応）。
    'fence-quote-line.md': '```md\n> ```\nX**「b」**Y\n```\n\nafter\n',
    'comment-fence.md': '<!--\n```\n-->\n\nこれは**「例」**です。\n',
    # 守る 22: インデントしたコードブロックは見ない／段落の中の字下げした ``` は続き。
    # どれも GitHub の描画（gfm）と判定が一致することを確かめた（#525 の 2 パス目の指摘対応）。
    'indented-code.md': '本文。\n\n    X**「例」**Y\n',
    'indented-fence-line.md': '本文 **太字\n    ```\nコード** だ\n',
    # 守る 23・4: 先頭の `|` が無い表・setext の見出しで区切る（2 パス目 CR）。
    # どれも GitHub の描画（gfm）と判定が一致することを確かめた（#525 の 2 パス目の指摘対応）。
    'table-nolead.md': 'a **x | b\n--- | ---\nc | d** e\n',
    'setext.md': 'Title **x\n===\nnext** y\n',
    # 守る 7: 長いフェンスは短い列で閉じない。守る 13: 行だけのコメントの印も残った印として落とす（2 パス目 V-R3）。
    # どれも GitHub の描画（gfm）と判定が一致することを確かめた（#525 の 2 パス目の指摘対応）。
    'long-fence.md': '````\n```\nX**「例」**Y\n```\n````\n',
    'own-line-mark.md': '崩れていない **太字** だ。\n<!-- bold-flanking-ok: 古い印 -->\n',
    # 守る 23・24: 先頭が `|` の表も見分け、表のあとの `|` の無い行を表の行として組む（#562。#525 の狭いパス NP-1）。
    # 表の行なら `foo **x`・`bar** y` は 1 行ずつで `**` が字のまま、表が終わっていれば 2 行の段落で太字になる。
    # どれも GitHub の描画（gfm）と判定が一致し、変更前の検査では表の行の 7 本と見出しの 1 本が一致しないことを確かめた（#562 の周）。
    'table-lead-row.md': '| a | b |\n|---|---|\n| 1 | 2 |\nfoo **x\nbar** y\n',
    'table-lead-quote.md': '> | a | b |\n> |---|---|\n> | 1 | 2 |\n> foo **x\n> bar** y\n',
    'table-lead-list.md': '- | a | b |\n  |---|---|\n  | 1 | 2 |\n  foo **x\n  bar** y\n',
    'table-one-col.md': '| a |\n| - |\nfoo **x\nbar** y\n',
    'table-delim-noouter.md': '| a | b |\n--- | ---\nfoo **x\nbar** y\n',
    'table-after-para.md': 'text\n| a | b |\n|---|---|\nfoo **x\nbar** y\n',
    'table-row-kinds.md': '| a | b |\n|---|---|\n| 1 | 2 |\n===\n<b>x</b>\n   foo **x\nbar** y\n',
    # 守る 24: 表は空行・ブロックの始まり・容れ物の変化で終わる（そのあとは段落）。先頭の `|` が無い表も同じ（変更前は見出しで終わらず誤検出した）。
    'table-end-heading.md': 'a | b\n--- | ---\nc | d\n# h\nfoo **x\nbar** y\n',
    'table-end-item.md': '| a | b |\n|---|---|\n| 1 | 2 |\n2. i\nfoo **x\nbar** y\n',
    'table-end-fence.md': '| a | b |\n|---|---|\n| 1 | 2 |\n~~~\nfoo **x\nbar** y\n',
    'table-end-comment.md': '| a | b |\n|---|---|\n| 1 | 2 |\n<!-- c -->\nfoo **x\nbar** y\n',
    'table-end-hr.md': '| a | b |\n|---|---|\n| 1 | 2 |\n***\nfoo **x\nbar** y\n',
    'table-end-quote.md': '| a | b |\n|---|---|\n| 1 | 2 |\n> q\nfoo **x\nbar** y\n',
    'table-end-indent.md': '| a | b |\n|---|---|\n| 1 | 2 |\n    code\nfoo **x\nbar** y\n',
    'table-end-quote-out.md': '> | a | b |\n> |---|---|\n> | 1 | 2 |\nfoo **x\nbar** y\n',
    'table-end-list-out.md': '- | a | b |\n  |---|---|\n  | 1 | 2 |\nfoo **x\nbar** y\n',
    # 守る 23: 見出しの行と区切りの行のセルの数が違う・逃がした `\|`・あいだに空行——どれも GitHub は表にしない。
    'table-cells-differ.md': '| a | b |\n|---|\nfoo **x\nbar** y\n',
    'table-cells-escaped.md': '| a \\| b |\n|---|---|\nfoo **x\nbar** y\n',
    'table-header-apart.md': '| a | b |\n\n|---|---|\nfoo **x\nbar** y\n',
    # 崩れていない形（誤検出しない）——句読点の両側・空白の外側・引用・表のセル・GitHub が句読点と見ない記号。
    "clean.md": (
        "# 見出しの **太字**\n\n"
        "本文の **「括弧」** と、**（丸括弧）**、そして**文字だけ**の太字。\n"
        "> 引用の **太字** と **「括弧」** だ。\n\n"
        "| **セル** | **「括弧」** |\n"
        "| --- | --- |\n\n"
        "これは**→矢印**です。\n"),
}

# 期待: 名前 → (崩れの行番号の組, 使われなかった印の行番号の組)
EXPECTED = {
    "real-519.md": ((1, 1, 1, 1), ()),
    "real-525.md": ((1, 3, 3), ()),
    "open.md": ((1,), ()),
    "close.md": ((1,), ()),
    "unpaired.md": ((1,), ()),
    "split-blank.md": ((1,), ()),
    "split-heading.md": ((1,), ()),
    "split-table.md": ((1,), ()),
    "split-list.md": ((1,), ()),
    "multiline.md": ((), ()),
    "triple.md": ((), ()),
    "code.md": ((), ()),
    "backtick.md": ((1, 1), ()),
    "escape.md": ((), ()),
    "frontmatter.md": ((), ()),
    "exempt.md": ((3, 5), ()),
    "exempt-in-code.md": ((1,), ()),
    "exempt-unused.md": ((), (1,)),
    "span-per-block.md": ((3,), ()),
    "quote-start.md": ((1,), ()),
    "ordered-cont.md": ((), ()),
    "ordered-items.md": ((1,), ()),
    "hr-comment.md": ((), ()),
    "quote-fence.md": ((), ()),
    "comment-edge.md": ((), ()),
    "comment-backtick.md": ((1, 1), ()),
    'quote-deeper.md': ((1, 2), ()),
    'quote-lazy.md': ((), ()),
    'quote-fence-unclosed.md': ((4, 4), ()),
    'list-lazy.md': ((), ()),
    'list-lazy-then-item.md': ((4, 4), ()),
    'list-fence.md': ((7, 7), ()),
    'ordered-empty.md': ((), ()),
    'list-sibling.md': ((3, 4), ()),
    'list-icode.md': ((), ()),
    'nested-hr.md': ((), ()),
    'nested-comment.md': ((), ()),
    'comment-short.md': ((2, 2), ()),
    'fence-quote-line.md': ((), ()),
    'comment-fence.md': ((5, 5), ()),
    'indented-code.md': ((), ()),
    'indented-fence-line.md': ((), ()),
    'table-nolead.md': ((1, 3), ()),
    'setext.md': ((1, 3), ()),
    'long-fence.md': ((), ()),
    'own-line-mark.md': ((), (2,)),
    'table-lead-row.md': ((4, 5), ()),
    'table-lead-quote.md': ((4, 5), ()),
    'table-lead-list.md': ((4, 5), ()),
    'table-one-col.md': ((3, 4), ()),
    'table-delim-noouter.md': ((3, 4), ()),
    'table-after-para.md': ((4, 5), ()),
    'table-row-kinds.md': ((6, 7), ()),
    'table-end-heading.md': ((), ()),
    'table-end-item.md': ((), ()),
    'table-end-fence.md': ((), ()),
    'table-end-comment.md': ((), ()),
    'table-end-hr.md': ((), ()),
    'table-end-quote.md': ((), ()),
    'table-end-indent.md': ((), ()),
    'table-end-quote-out.md': ((), ()),
    'table-end-list-out.md': ((), ()),
    'table-cells-differ.md': ((), ()),
    'table-cells-escaped.md': ((), ()),
    'table-header-apart.md': ((), ()),
    "clean.md": ((), ()),
}


def write(root: Path, name: str, body: str) -> None:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def observe(mod, tree: Path, empty: Path, clean: Path) -> dict:
    """本体の判定をまとめて観測する。"""
    out = {}
    for path in sorted((tree / "plugins").glob("*.md")):
        found, unused = mod.scan(path.read_text(encoding="utf-8"))
        out[path.name] = (tuple(lineno for lineno, _, _ in found), tuple(unused))
    # 本体の出力は読まない（終了コードだけを見る）。出すと試料の数だけ端末が埋まる。
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        out["exit:tree"] = mod.main([str(tree)])
        out["exit:empty"] = mod.main([str(empty)])
        out["exit:clean"] = mod.main([str(clean)])
    return out


# 変異: 名前 → (壊す「守る」の番号, 当てる先, 置き換え)。番号は本体の docstring の「守る」の順。
MUTATIONS = {
    "開きを見ない": (1,
        "                elif not left_flanking(before, after):",
        "                elif False:"),
    "閉じを見ない": (2,
        "            elif not right_flanking(before, after):",
        "            elif False:"),
    "対にならないを見ない": (3,
        "                if index == len(found) - 1:",
        "                if False:"),
    "空行で区切らない": (4,
        "        if not content.strip():\n            flush()",
        "        if False:\n            flush()"),
    "見出しで区切らない": (4,
        "        if HEADING.match(inner):",
        "        if False:"),
    "setext の下線で区切らない": (4,
        "        if para and not lazy and SETEXT.match(inner):",
        "        if False:"),
    "リストの項で区切らない": (4,
        "        if item is not None:\n            flush()",
        "        if item is not None:\n            pass"),
    "行ごとに組む": (5,
        "        para.append(shown)",
        "        para.append(shown)\n        flush()"),
    "三つの並びを数えない": (6,
        "        if j - i in (2, 3):",
        "        if j - i == 2:"),
    "フェンスを開かない": (7,
        "        if fence_open:",
        "        if False:"),
    "短い列でもフェンスを閉じる": (7,
        'rf" {{0,3}}{re.escape(char)}{{{length},}}[ \\t]*$"',
        'rf" {{0,3}}{re.escape(char)}{{3,}}[ \\t]*$"'),
    "コードスパンを伏せない": (7,
        '                runs_out[p] = marks_out[p] = "x"',
        "                pass"),
    "バッククォートごと伏せる": (8,
        "        for p in range(j, close):",
        "        for p in range(i, close + run):"),
    "逃がした字を飛ばさない": (9,
        "            i += 2  # 逃がした字（`\\*`）は区切りにならない",
        "            i += 1"),
    "frontmatter を剥がさない": (10,
        '    found_blocks, comment_marks = blocks(strip_frontmatter(text).split("\\n"))',
        '    found_blocks, comment_marks = blocks(text.split("\\n"))'),
    "免除をファイル全体に効かせる": (11,
        "    kept = [p for p in problems if p[0] not in exempt]",
        "    kept = [] if exempt else problems"),
    "理由の無い印も効かせる": (11,
        '        exempt.update(start + row for row, line in enumerate(marks.split("\\n")) if EXEMPT.search(line))',
        '        exempt.update(start + row for row, line in enumerate(marks.split("\\n")) if "bold-flanking-ok:" in line)'),
    "印をコードの中からも拾う": (12,
        '        joined, marks = mask_inline("\\n".join(block))',
        '        joined, marks = mask_inline("\\n".join(block))[0], "\\n".join(block)'),
    "残った印を見ない": (13,
        "    unused = sorted(exempt - hit)",
        "    unused = []"),
    "行だけのコメントの印を拾わない": (13,
        "    exempt: set[int] = set(comment_marks)",
        "    exempt: set[int] = set()"),
    "何も見ていなくても緑": (14,
        "    if checked == 0:",
        "    if False:"),
    "コードスパンを段落をまたいで組む": (15,
        "    for start, block in found_blocks:",
        "    for start, block in [(found_blocks[0][0], [l for _, b in found_blocks for l in b])] if found_blocks else []:"),
    "深くなる引用で区切らない": (16,
        "        if para and depth > para_depth:\n            flush()",
        "        if False:\n            flush()"),
    "浅い引用の行でも区切る": (16,
        "        if para and depth > para_depth:\n            flush()",
        "        if para and depth != para_depth:\n            flush()"),
    "引用が終わってもフェンスを閉じない": (16,
        "            if got < depth or (rest.strip() and indent_of(rest) < base):",
        "            if rest.strip() and indent_of(rest) < base:"),
    "項の中の続きを認めない": (17,
        "            if para and not starts_block:\n                break",
        "            if False:\n                break"),
    "ブロックの始まりでも項を閉じない": (17,
        "        starts_block = any(r.match(stripped) for r in (THEMATIC, FENCE_OPEN, COMMENT_BLOCK, HEADING)) \\\n            or item_of(stripped) is not None",
        "        starts_block = item_of(stripped) is not None"),
    "どの項でも段落を割り込む": (17,
        '            if para and not popped and (empty or (ordered and number != "1")):',
        "            if False:"),
    "項を閉じた印も割り込みの規則で見る": (17,
        '            if para and not popped and (empty or (ordered and number != "1")):',
        '            if para and (empty or (ordered and number != "1")):'),
    "項の中身の桁で読まない": (17,
        '        inner = content[base:] if indent >= base else content.lstrip(" ")',
        '        inner = content.lstrip(" ")'),
    "区切り線を本文として見る": (18,
        "        if THEMATIC.match(inner):  #",
        "        if False:  #"),
    "コメントのブロックを本文として見る": (18,
        "        if COMMENT_BLOCK.match(inner):",
        "        if False:"),
    "コメントの閉じを <!-- の後ろから探す": (18,
        '            if "-->" not in inner[inner.index("<!--"):]:',
        '            if "-->" not in inner[inner.index("<!--") + 4:]:'),
    "フェンスの中の行の引用を剥がす": (19,
        "            got, pos = quote_depth(line, depth)",
        "            got, pos = quote_depth(line)\n            got = max(got, depth)"),
    "コメントの中の行もブロックとして読む": (19,
        "                    comment = None\n                continue",
        "                    comment = None"),
    "コメントの区切りごと伏せる": (20,
        "            for p in range(i + 4, close):",
        "            for p in range(i, close + 3):"),
    "コメントを伏せない": (20,
        '            for p in range(i + 4, close):\n                if runs_out[p] != "\\n":\n                    runs_out[p] = "x"',
        "            for p in range(i + 4, close):\n                pass"),
    "コメントを見ない（バッククォートが勝つ）": (21,
        '        if text.startswith("<!--", i):',
        "        if False:"),
    "インデントしたコードを見る": (22,
        "        if not para and indent_of(inner) >= 4:\n            continue",
        "        if False:\n            continue"),
    "先頭の | が無い表を見分けない": (23,
        '            if para and len(para) == 1 and "|" in para[0] and cells(para[0]) == cells(inner):',
        "            if False:"),
    "先頭の | がある表を見分けない": (23,
        "            if not para and header is not None and header[:3] == (lineno - 1, depth, len(lists)) \\\n"
        "                    and cells(header[3]) == cells(inner):",
        "            if False:"),
    "見出しの行が直前でなくても表にする": (23,
        "header[:3] == (lineno - 1, depth, len(lists))",
        "header[1:3] == (depth, len(lists))"),
    "セルの数を見ない": (23,
        "    return len(parts)",
        "    return 1"),
    "逃がした | もセルの区切りに数える": (23,
        '    parts = re.split(r"(?<!\\\\)\\|", text)',
        '    parts = re.split(r"\\|", text)'),
    "| の無い行を表の行にしない": (24,
        "                out.append((lineno, [shown]))\n                continue",
        "                table = None"),
    "ブロックの始まりで表を終わらせない": (24,
        "or any(r.match(inner) for r in (THEMATIC, FENCE_OPEN, COMMENT_BLOCK, HEADING)):",
        "or False:"),
    "項で表を終わらせない": (24,
        "item_of(inner) is not None or indent_of(inner) >= 4",
        "False or indent_of(inner) >= 4"),
    "インデントしたコードで表を終わらせない": (24,
        "item_of(inner) is not None or indent_of(inner) >= 4",
        "item_of(inner) is not None or False"),
    "容れ物の変化で表を終わらせない": (24,
        "            if (depth, len(lists)) != table or",
        "            if False or"),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "tree"
        empty = Path(tmp) / "empty"
        clean = Path(tmp) / "clean"
        for root in (tree, empty, clean):
            root.mkdir()
            assert_not_real_repo(root)
        for name, body in SAMPLES.items():
            write(tree / "plugins", name, body)
        (empty / "plugins").mkdir()
        write(clean / "plugins" / "x" / "skills", "SKILL.md", SAMPLES["clean.md"])
        # `plugins/` の外は見ない——ここに崩れを置いても clean は緑のまま
        write(clean / "docs", "page.md", SAMPLES["open.md"])

        mod = load()
        correct = observe(mod, tree, empty, clean)

        print("試料ごとの判定（崩れの行番号・残った印の行番号）")
        for name, expected in EXPECTED.items():
            check(f"{name}: {expected}", correct.get(name) == expected)
        check("試料と期待が 1 対 1", set(SAMPLES) == set(EXPECTED))

        print("\n終了コード")
        check("崩れがあれば 1", correct["exit:tree"] == 1)
        check("plugins/ に Markdown が無ければ 1（何も見ていない）", correct["exit:empty"] == 1)
        check("崩れが無ければ 0（plugins/ の外の崩れは見ない）", correct["exit:clean"] == 0)

        print("\n変異テスト（壊したのに結果が変わらなければ失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (_, needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}", False)
                continue
            d = Path(tmp) / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "check-bold-flanking.py"
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            try:
                mutated = observe(load(broken), tree, empty, clean)
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", mutated != correct)

        print("\n「守る」の各行に変異が当たっているか（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [l for l in body.splitlines() if l.startswith("- ")]
        covered = {number for number, _, _ in MUTATIONS.values()}
        check(f"本体の「守る」{len(promises)} 行のすべてに変異がある（当たっている番号 {sorted(covered)}）",
              covered == set(range(1, len(promises) + 1)))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("太字の flanking の検査のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
