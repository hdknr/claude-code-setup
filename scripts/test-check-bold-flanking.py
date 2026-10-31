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
    # 表の行（区切りの行のある表）で区切る。区切りの行の無い `|` の行は GitHub では 1 つの段落（#562）。
    "split-table.md": "| 前の **閉じ忘れ | x |\n|---|---|\n| **太字** | y |\n",
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
    # 守る 23: 引用の段落の続き（lazy continuation）の `|` の行・`|` だけの行は見出しの行にならない（#562 の 1 パス目の Verifier）。
    'table-lazy-header.md': '> q\n| a | b |\n|---|---|\nfoo **x\nbar** y\n',
    'table-bare-pipe.md': '|\n|---|\nfoo **x\nbar** y\n',
    # 守る 23: 隣の項の行は見出しの行にならない・段落の続きの区切りの行は表を開かない（#562 の 1 パス目の /code-review）。
    'table-sibling-items.md': '- | a | b |\n- |---|---|\n  foo **x\n  bar** y\n',
    'table-lazy-delim.md': '> a | b\n--- | ---\nfoo **x\nbar** y\n',
    # 守る 23・24: 2 パス目の関門が示した形（#562）。`|` の行も段落の行として読み、区切りの行で段落の最後の行を見出しにする。
    # 段落の続き（lazy）の区切りの行は表を開かず、段落の続きの見出しの行は区切りの行が容れ物の中なら表になる。どれも GitHub の描画（gfm）と一致を確かめた。
    'table-lazy-chain-quote.md': '> note\n| x |\n| a | b |\n|---|---|\nfoo **x\nbar** y\n',
    'table-lazy-chain-item.md': '- | a | b |\n|---|---|\n|---|---|\nfoo **x\nbar** y\n',
    'table-lazy-chain-nolead.md': '> note\n| x |\na | b\n--- | ---\nfoo **x\nbar** y\n',
    'table-lazy-header-item.md': '- q\n| a | b |\n  |---|---|\n  foo **x\n  bar** y\n',
    'table-lazy-header-quote.md': '> q\n| a | b |\n> |---|---|\n> foo **x\n> bar** y\n',
    'table-end-blank.md': '| a | b |\n|---|---|\n| 1 | 2 |\n\nfoo **x\nbar** y\n',
    'table-lazy-delim-item.md': '- a | b\n--- | ---\n  foo **x\n  bar** y\n',
    'table-lazy-delim-quote-lead.md': '> | a | b |\n|---|---|\nfoo **x\nbar** y\n',
    'table-lazy-delim-item-lead.md': '- | a | b |\n|---|---|\nfoo **x\nbar** y\n',
    'table-delim-in-para.md': 'text\n|---|---|\n|---|---|\nfoo **x\nbar** y\n',
    'table-para-nolead.md': 'text\na | b\n--- | ---\nfoo **x\nbar** y\n',
    'table-para-last-line.md': 'text\n| a | b | c |\n| a | b |\n|---|---|\nfoo **x\nbar** y\n',
    'table-header-nopipe.md': 'x\n|---|\nfoo **x\nbar** y\n',
    # 守る 23: 段落の続き（lazy）の区切りの形の行は表を試さないので「開けなかった」にならず、それを見出しにして容れ物の中の区切りの行が
    # 表を開く（#580。#562 の狭いパス NP-1）。区切りの行が開けなかった段落では、直前でなくてももう開かない・印は段落ごとに戻る。
    # どれも GitHub の描画（gfm）と判定が一致し、変更前の検査では lazy の 3 本が崩れ無し・table-refused-apart が 5・6 行目で一致しないことを確かめた（#580 の周）。
    'table-lazy-delim-header-quote.md': '> q\n|---|---|\n> |---|---|\n> foo **x\n> bar** y\n',
    'table-lazy-delim-header-item.md': '- q\n|---|---|\n  |---|---|\n  foo **x\n  bar** y\n',
    'table-lazy-delim-header-nested.md': '>> q\n> |---|---|\n>> |---|---|\n>> foo **x\n>> bar** y\n',
    'table-refused-apart.md': 'x\n|---|---|\ny | z\n|---|---|\nfoo **x\nbar** y\n',
    'table-refused-next-para.md': 'text\n|---|---|\n\na | b\n--- | ---\nfoo **x\nbar** y\n',
    # 守る 23: 4 桁以上（タブを含めて）字下げした区切りの形の行は表を試さない——開かず、開けなかったことにもならない（#580 の /code-review 1 パス目）。
    # どれも GitHub の描画（gfm）と一致を確かめた。indented-delim-later は字下げを見ない版で崩れ無し、indented-delim は main でも 3・4 行目（誤検出）だった。
    'table-indented-delim-later.md': 'x\n    ---|---\ny | z\n---|---\nfoo **x\nbar** y\n',
    'table-tab-delim-later.md': 'x\n\t---|---\ny | z\n---|---\nfoo **x\nbar** y\n',
    'table-indented-delim.md': 'a | b\n    --- | ---\nfoo **x\nbar** y\n',
    # 守る 23: 字下げの桁の境界と、容れ物の印の直後のタブ・見出しで切れた段落（#580 の /code-review 2 パス目）。どれも GitHub の描画（gfm）と一致を確かめた。
    # 3 桁の字下げは表を試す。引用の印・項の中身の桁の後ろのタブは行の頭から数えて 4 桁に届かない（タブを容れ物の後ろから数えた版は見逃し・誤検出した）。
    'table-delim-indent-3.md': 'a | b\n   --- | ---\nfoo **x\nbar** y\n',
    'table-delim-quote-tab.md': '> a | b\n>\t--- | ---\n> foo **x\n> bar** y\n',
    # `>⇥ ---` は 3 桁（印の後ろの空白 1 桁をタブから使う）で表を試す。`>⇥  ---` は 4 桁で試さない（GitHub は段落で太字）。
    'table-delim-quote-tab-space.md': '> a | b\n>\t --- | ---\n> foo **x\n> bar** y\n',
    'table-delim-item-tab.md': '- a | b\n  \t--- | ---\n  foo **x\n  bar** y\n',
    'table-refused-quote-tab.md': '> x\n> \t---|---\n> y | z\n> ---|---\n> foo **x\n> bar** y\n',
    'table-refused-heading-next.md': 'x\n|---|---|\n# h\na | b\n--- | ---\nfoo **x\nbar** y\n',
    # 守る 23: `|` の無い区切りの行も 1 列の表を開き、開けなければ「開けなかった」に数える（#581。#562 の狭いパス NP-2・NP-3）。
    # どれも GitHub の描画（gfm）と判定が一致し、変更前の検査では pipeless の 4 本が崩れ無し・pipeless-refused が 5・6 行目で一致しないことを確かめた（#581 の周）。
    # pipeless-then-pipe（Issue の 2 つ目の形）・lazy・indent-4 は変更前も一致する（表を試さない行と、`|--|` を表の行に読む形の回帰の試料）。
    'table-pipeless-center.md': 'a\n:--:\nfoo **x\nbar** y\n',
    'table-pipeless-right.md': 'a\n--:\nfoo **x\nbar** y\n',
    'table-pipeless-left.md': 'a\n:-\nfoo **x\nbar** y\n',
    'table-pipeless-indent-3.md': 'a\n   :--:\nfoo **x\nbar** y\n',
    'table-pipeless-refused.md': 'a | b\n:---\nc | d\n--- | ---\nfoo **x\nbar** y\n',
    'table-pipeless-then-pipe.md': 'a\n:--:\n|--|\nfoo **x\nbar** y\n',
    'table-pipeless-lazy.md': '> a\n:--:\nfoo **x\nbar** y\n',
    'table-pipeless-indent-4.md': 'a\n    :--:\nfoo **x\nbar** y\n',
    # 守る 4・23: 容れ物の中でタブで字下げした `-` だけの行も、4 桁に届かなければ setext の下線で段落を終わらせる——表にも段落の続きにもしない。
    # GitHub は `<h2>**a</h2>` と `b**` に分け、`**` は字のまま（1・3 行目）。main と 2 パス目の前（87eed09）は段落の続きとして組んで崩れ無し（見逃し）、
    # 1 パス目の形（93bd951）は表と読んだ。setext-refused は下線で段落が終わるので、下線の前の `:--` の「開けなかった」が後ろの表に残らない
    # （GitHub は c|d の表で 6・7 行目。87eed09 は崩れ無し）。コロンがあれば同じ字下げでも 1 列の表（tab-item-colon。main は見逃し）。
    # どれも GitHub の描画（gfm）と一致を確かめた（#581 の 1・2 パス目の /code-review）。
    'table-pipeless-setext-tab-item.md': '- **a\n  \t--\n  b**\n',
    'table-pipeless-setext-tab-quote.md': '> **a\n>\t---\n> b**\n',
    'table-pipeless-setext-refused.md': '> a | b\n> :--\n>\t--\n> c | d\n> --- | ---\n> foo **x\n> bar** y\n',
    'table-pipeless-tab-item-colon.md': '- a\n  \t:--:\n  foo **x\n  bar** y\n',
    # #525 の狭いパスで素通りした変異を殺す試料（#563）。どれも GitHub の描画（gfm）と判定が一致することを確かめた（#563 の周）。
    # 守る 7: info にバッククォートを含む ``` はフェンスではない（段落。GitHub は 2 行目の `**` を字のまま描く）。
    'fence-info-backtick.md': '``` `a`\nX**「例」**Y\n',
    # 守る 18: `___` も区切り線（段落を割る。GitHub は `**x` と `b**` を字のまま描く）。
    'thematic-underscore.md': 'a **x\n___\nb** c\n',
    # 守る 4・16: 4 つ字下げした `#` `>` は見出し・引用を始めない（段落の続き。GitHub は 1 つの太字に組む）。
    'heading-indent.md': '本文 **x\n    # y** z\n',
    'quote-indent.md': '本文 **x\n    > y** z\n',
    # 守る 13: 複数行のコメントのブロックの本文行に書いた印も、残った印として落とす。
    'comment-body-mark.md': '<!--\nbold-flanking-ok: 古い印\n-->\n',
    # 守る 17: 項の印の後ろに空白が 5 つ以上なら、中身は印の 1 つ後ろから始まり、残りはインデントしたコード（GitHub はコードとして描く）。
    'item-wide-gap.md': '-     X**「例」**Y\n',
    # 守る 16: 引用が終わると、中で開いたコメントのブロックも閉じる——4 行目は段落（行頭が `<!--` でない）。
    # GitHub は閉じないコメントの後ろを生の HTML の `-->` まで見せないが、段落の中のコメントの後ろの `**「例」**W` は字のまま見える。
    'quote-comment-closed.md': '> <!--\n> x\n\nZ <!-- c --> **「例」**W\n',
    # #563 の /code-review 1 パス目 CR1-1〜3 が素通りを示した変異を殺す試料（#605）。どれも GitHub の描画（gfm）と判定が一致することを確かめた（#623 の周）。
    # 守る 17: 項の印の後ろの空白が 4 つ（境界の下側）なら、中身はその後ろから始まる——空行のあとの 6 つ字下げは項の中の段落（GitHub は崩れを描く）。
    'item-gap-4.md': '-    a\n\n      X**「例」**Y\n',
    # 守る 7: info のバッククォートの制限は ``` のフェンスだけ——`~~~` のフェンスは開く（GitHub はコードとして描く）。
    'fence-tilde-info-backtick.md': '~~~ `a`\nX**「例」**Y\n~~~\n',
    # 守る 16: コメントが開いたまま、空行でない行で引用が終わる——3 行目は引用の外の段落（GitHub は `**「例」**W` を字のまま描く）。
    'quote-comment-lazy-end.md': '> <!--\n> x\nZ <!-- c --> **「例」**W\n',
    # 守らない（#606）: 引用・リストの項の中で閉じ忘れたコメントの後ろ。GitHub は `-->` までを描かない（4 行目は画面に出ない）が、
    # 検査は容れ物の終わりでコメントを閉じて 4 行目を崩れとする——今の振る舞いを残す（要確認 #607）。リストの項の形は main では崩れ無しだった
    # （項の終わりでコメントを閉じていなかった。引用と同じ読み方にそろえた。#623 の周）。
    'quote-comment-unclosed.md': '> <!--\n> x\n\nX**「例」**Y\n\n-->\n',
    'list-comment-unclosed.md': '- <!--\n  x\n\nX**「例」**Y\n\n-->\n',
    # 守る 27: タブは桁で数える（#623）。`>` の直後のタブと先頭の `|` の区切りの行は表（main は見逃し）／表のあとのタブの字下げは
    # インデントしたコード（main は表の行と読んで誤検出）／タブだけで字下げした項の中の区切りの行は表（main は段落の続きと読んで見逃し）。
    # どれも GitHub の描画（gfm）と一致を確かめ、main では一致しないことを確かめた（#623 の周）。
    'table-quote-tab-lead.md': '> a | b\n>\t|---|---\n> foo **x\n> bar** y\n',
    'table-end-tab-code.md': 'a | b\n--- | ---\n\tfoo **x\n\tbar** y\n',
    'table-tab-item.md': '- a | b\n\t--- | ---\n  foo **x\n  bar** y\n',
    # 守る 27: `>` の直後でないタブからは 1 桁も落とさない——2 桁のタブと空白 2 つで 4 桁の字下げなので、区切りの形の行は表を試さない
    # （GitHub は段落で太字。#624 の NP-1——どのタブからも 1 桁落とす変異が殺せなかった）。
    'table-tab-not-quote-item.md': '- a | b\n  \t  --- | ---\n  foo **x\n  bar** y\n',
    'table-tab-not-quote-quote.md': '> a | b\n> \t  --- | ---\n> foo **x\n> bar** y\n',
    # 守る 16: リストの項の中の引用の表（#624 の NP-2。main は見逃し）／4 桁字下げした `>` は引用を続けない——段落の続きなので表を試さない
    # ／引用の段落のあとの `2.` は段落の続きではなく新しいリスト（main は段落の続きと読んで見逃し）。どれも GitHub の描画（gfm）と一致を確かめた。
    'table-quote-in-list.md': '- > a | b\n  > --- | ---\n  > foo **x\n  > bar** y\n',
    'quote-indent-cont.md': '> a | b\n    > --- | ---\n> foo **x\n> bar** y\n',
    'quote-then-ordered.md': '> a **x\n2. y** z\n',
    # 守る 17: 字下げの浅い見出しは項を閉じる（段落の続きにならない。GitHub は `a **x` と `h** y` に分けて字のまま描く）。
    # list-fence はこの役をしない——段落の続きに組んだ ``` もコードスパンとして伏せられ、判定が変わらない（#623 の周）。
    'list-heading-ends.md': '- a **x\n# h** y\n',
    # #581 の狭いパス NP-1〜3（#624 の追記。要確認 #639）。どれも GitHub の描画（gfm）と一致を確かめた（#623 の周）。
    # 守る 4: 4 桁字下げした `---` と段落の続き（lazy）の `===` は setext の下線ではない（GitHub は 1 つの太字に組む）。
    'setext-indent-4.md': '**a\n    ---\nb**\n',
    'setext-lazy.md': '- **a\n===\nb**\n',
    # 守る 27: タブで字下げした項の中の `---` は下線で段落を終わらせる（GitHub は `<h2>**a</h2>` と `b**`。main は見逃し）。
    'setext-tab-item.md': '- **a\n\t---\n  b**\n',
    # 守る 26: `*` の並びだけの行は区切りに数えない（GitHub は `**a`〜`b**` を 1 つの太字に組む。main は 2・3 行目を誤検出）。
    'stars-line-tab.md': '**a\n\t***\nb**\n',
    'stars-line-pair.md': '**a\n**\nb**\n',
    # 1 パス目の関門（#623 の周）の指摘を守る試料。どれも GitHub の描画（gfm）と一致を確かめた。
    # 守る 16: リストの項の中身の桁は外の容れ物の本文から数える——後の行の `>` の位置がずれると項に当たらず、段落の続きになる（Verifier R1。
    # 1 パス目の版は行の頭からの桁で持って項に当て、`===` を下線・`--- | ---` を表と読んだ。main は一致）。引用の中の項の表は表（項に当たる）。
    'quote-item-shifted-setext.md': '> - a **x\n  > ===\n  > y** z\n',
    'quote-item-shifted-delim.md': '>- a | b\n>  --- | ---\n>  foo **x\n>  bar** y\n',
    'table-item-in-quote.md': '> - a | b\n>   --- | ---\n>   foo **x\n>   bar** y\n',
    # 守る 23: 段落の続き（lazy）の見出しの行の頭の字下げは空のセルを 1 つ足す（Verifier R2。字下げの無い形と非 lazy の形は表。
    # main もタブの無い形を表と読んで誤検出していた）。
    'table-lazy-header-indent.md': '> bar\n  |---|\n> |---|\n> foo **x\ny** z\n',
    'table-lazy-header-indent-tab.md': '> \tbar\n  |---|\n> \t|---|\n> foo **x\ny** z\n',
    'table-lazy-header-indent-3col.md': '> bar\n  |a|b\n> --- | --- | ---\n> foo **x\ny** z\n',
    # 守る 26: `*` の並びだけの行の空白は CommonMark の空白（`is_space`）で数える——`\v` は空白ではない（/code-review CR1-5。GitHub は 2 行目で閉じ、`b**` が字のまま）。
    'stars-line-vt.md': '**a\n\x0b**\nb**\n',
    # 守る 16: 容れ物の中のフェンスは容れ物の本文の頭から閉じる（CR1-2）／タブで字下げした項の中のフェンス（守る 27）。
    'quote-fence-closes.md': '> ~~~\n> x\n> ~~~\n> X**「例」**Y\n',
    'item-fence-tab.md': '- ~~~\n\t**x\n\t~~~\n  X**「例」**Y\n',
    # 守る 16: 印の無い空行は引用（と中の項）を閉じる——次の `>` の行は新しい引用で、4 つ字下げはインデントしたコード（CR1-7）。
    'quote-blank-closes.md': '> - a\n\n>     X**「例」**Y\n',
    # 2 パス目の関門（#623 の周）の指摘を守る試料。どれも GitHub の描画（gfm）と一致を確かめた。
    # 守る 16: 3 段の項——項の中身の桁は外の項の中身から積み上げる（V2-1。GitHub は `<h2>a **x</h2>` と `y**`）。
    'item-nested-3.md': '- - - a **x\n      ---\n      y**\n',
    # 守る 17: 区切り線の形（`- - -`）は項を始めない——区切り線のあとの 4 つ字下げはインデントしたコード（V2-2。GitHub は崩れ無し）。
    'item-thematic-not-item.md': '  a\n- - -  \n    x** y\n',
    # #667 の試料。どれも GitHub の描画（gfm）と一致を確かめた（#667 の周）。
    # 守る 4: 空行は空白とタブだけの行——U+3000・NBSP・`\v`・`\f` だけの行は段落の行（GitHub は 1 つの太字。main は 1・3 行目を誤検出）。
    'blank-ideographic.md': '**a\n\u3000\nb**\n',
    'blank-nbsp.md': '**a\n\u00a0\nb**\n',
    'blank-vt.md': '**a\n\x0b\nb**\n',
    'blank-ff.md': '**a\n\x0c\nb**\n',
    'blank-quote-ideographic.md': '> **a\n> \u3000\n> b**\n',
    # 項の中で字下げの足りない U+3000 の行は空行として項に当たらず、段落の続き（main は 1・3 行目を誤検出）
    'blank-item-ideographic.md': '- **a\n\u3000\n  b**\n',
    # 段落の無いところの、字下げの無い U+3000 の行は項に当たらず、項を閉じる——後ろの 4 つ字下げはインデントしたコード
    # （GitHub は崩れ無し。main は項の中の段落と読んで 5 行目を誤検出。上の試料はこの形を殺せない——段落が開いていれば続きになるので）
    'blank-item-closes.md': '- a\n\n\u3000\n\n    X**「例」**Y\n',
    # U+3000 の行は段落を始める——次の 4 つ字下げした行はインデントしたコードでなく続き（main は 3 行目を誤検出）
    'blank-ideographic-then-indent.md': '\u3000\n    **x\ny**\n',
    # 対照: 空白とタブだけの行・CRLF の空行は段落を切る（GitHub は段落を分け、`**` が字のまま）
    'blank-space-tab.md': '**a\n \t \nb**\n',
    'blank-crlf.md': '**a\r\n\r\nb**\r\n',
    # 中身が U+3000・NBSP だけの項は空の項でなく、段落を割り込む（GitHub は段落と項。main は見逃し）
    'item-ideographic-interrupts.md': 'a **x\n- \u3000\ny** z\n',
    'item-nbsp-ordered-interrupts.md': 'a **x\n1. \u00a0\ny** z\n',
    # 表の見出しの行の U+3000 はセルの中身——1 列の表（GitHub は段落 `a **x` と表。`**` は字のまま）
    'table-header-ideographic.md': 'a **x\n\u3000\n|-|\ny** z\n',
    # 守る 17: 割り込める番号は値で比べる——`01.` `001)` は割り込み、`00.` `02.` は割り込まない（main は `01.` `001)` を見逃し）
    'ordered-01-interrupts.md': 'a **x\n01. y** z\n',
    'ordered-001-paren-interrupts.md': 'a **x\n001) y** z\n',
    'ordered-00-continues.md': 'a **x\n00. y** z\n',
    'ordered-02-continues.md': 'a **x\n02. y** z\n',
    # 1 パス目の関門（#667 の周）の指摘を守る試料。どれも GitHub の描画（gfm）と一致を確かめた。
    # 守る 4: 表の行末の `\v`・`\f` は空白として剥がす（GitHub は 1 列・2 列の表。1 パス目の版は見逃し、main は一致）。
    # 行末の U+3000・NBSP と行の頭の `\v` はセルの中身で、表にならない（GitHub は 1 つの太字。main は 1・4 行目を誤検出）
    'table-row-vt-end.md': 'a **x\n|a|\x0b\n|-|\ny** z\n',
    'table-row-ff-end.md': 'a **x\n|a|b|\x0c\n|-|-|\ny** z\n',
    'table-row-vt-lead.md': 'a **x\n\x0b|a|\n|-|\ny** z\n',
    'table-row-ideographic-end.md': 'a **x\n|a|\u3000\n|-|\ny** z\n',
    # 2 パス目の関門（#667 の周）の指摘を守る試料。どれも GitHub の描画（gfm）と一致を確かめた。
    # 守る 4: `\v`・`\f` だけの見出しの行は 1 つのセル——表を開く（GitHub は段落と 1 列の表。2 パス目の版は見逃し、main は一致）。
    # `|\v` は表にならない（GitHub は 1 つの太字。1 パス目の版は (1, 4) の誤検出）
    'table-header-vt.md': 'a **x\n\x0b\n|-|\ny** z\n',
    'table-header-ff-spaced.md': 'a **x\n \x0c \n|-|\ny** z\n',
    'table-header-pipe-vt.md': 'a **x\n|\x0b\n|-|\ny** z\n',
    # 守る 4: 容れ物の印の直後の U+3000 も段落を始める——次の 4 つ字下げした行は続き（GitHub は引用の中の 1 つの太字。main は 3 行目を誤検出）
    'quote-ideographic-then-indent.md': '> \u3000\n    **x\ny**\n',
    # 守る 17: 番号は ASCII の数字だけ——全角の `１.`・アラビア・インドの `١.` は項でない（GitHub は 1 つの太字。1 パス目の版は誤検出）
    'ordered-fullwidth-continues.md': 'a **x\n\uff11. y** z\n',
    'ordered-arabic-indic-continues.md': 'a **x\n\u0661. y** z\n',
    # #648 の狭いパス NP-1〜3（要確認 #661 で、後の周で足すと決めた）。検査の答えは main から GitHub と同じで、殺すのは変異。
    # 守る 16: 3 段の項の中身の桁（`- - a` の内側は 4 桁）——1 桁足りずに積むと `===` を下線と読む（GitHub は 1 つの太字）
    'item-nested-setext-cont.md': '- - a **x\n   ===\n   y**\n',
    # 守る 17: `* * *` も区切り線で、項を始めない——区切り線のあとの 4 つ字下げはインデントしたコード（GitHub は崩れ無し）
    'item-thematic-star.md': '  a\n* * *  \n    x** y\n',
    # 守る 17: 容れ物を開いた直後の区切り線も項を始めない（引用の直後・項の直後。GitHub はどちらも区切り線とインデントしたコード）
    'quote-thematic-after-open.md': 'a\n> - - -\n>     x** y\n',
    'item-thematic-after-open.md': 'a\n1. * * *\n       x** y\n',
    # エラーの抜粋（#564）——どの行も、抜粋の窓（`**` の前 6 字・後ろ 8 字）に伏せる範囲（コードスパン・コメントの中身）が入る。
    # frontmatter の後ろ・段落・引用（窓が行頭の `>` に届く）・コメント・リストの項・見出し・表の見出しの行と表の行・行をまたぐ段落。
    # 抜粋そのものは EXCERPTS で見る。
    "excerpt.md": (
        "---\ntitle: t\n---\n"
        "ab `code` X**「y」\n\n"
        "> `c`X**「y」\n\n"
        "> q <!-- cm --> X**「y」\n\n"
        "- `li`X**「y」\n\n"
        "# `hd`X**「y」\n\n"
        "| `th`X**「y」 | b |\n"
        "| --- | --- |\n"
        "| `td`X**「y」 | d |\n\n"
        "`c1`\nX**「y」\n\n"
        ">\t`ab` X**「y」\n\n"
        "- a\n\t`cd` X**「y」\n"),
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
    'table-lazy-header.md': ((), ()),
    'table-bare-pipe.md': ((), ()),
    'table-sibling-items.md': ((), ()),
    'table-lazy-delim.md': ((), ()),
    'table-lazy-chain-quote.md': ((), ()),
    'table-lazy-chain-item.md': ((), ()),
    'table-lazy-chain-nolead.md': ((), ()),
    'table-lazy-header-item.md': ((4, 5), ()),
    'table-lazy-header-quote.md': ((4, 5), ()),
    'table-end-blank.md': ((), ()),
    'table-lazy-delim-item.md': ((), ()),
    'table-lazy-delim-quote-lead.md': ((), ()),
    'table-lazy-delim-item-lead.md': ((), ()),
    'table-delim-in-para.md': ((), ()),
    'table-para-nolead.md': ((4, 5), ()),
    'table-para-last-line.md': ((5, 6), ()),
    'table-header-nopipe.md': ((3, 4), ()),
    'table-lazy-delim-header-quote.md': ((4, 5), ()),
    'table-lazy-delim-header-item.md': ((4, 5), ()),
    'table-lazy-delim-header-nested.md': ((4, 5), ()),
    'table-refused-apart.md': ((), ()),
    'table-refused-next-para.md': ((6, 7), ()),
    'table-indented-delim-later.md': ((5, 6), ()),
    'table-tab-delim-later.md': ((5, 6), ()),
    'table-indented-delim.md': ((), ()),
    'table-delim-indent-3.md': ((3, 4), ()),
    'table-delim-quote-tab.md': ((3, 4), ()),
    'table-delim-quote-tab-space.md': ((3, 4), ()),
    'table-delim-item-tab.md': ((3, 4), ()),
    'table-refused-quote-tab.md': ((), ()),
    'table-refused-heading-next.md': ((6, 7), ()),
    'table-pipeless-center.md': ((3, 4), ()),
    'table-pipeless-right.md': ((3, 4), ()),
    'table-pipeless-left.md': ((3, 4), ()),
    'table-pipeless-indent-3.md': ((3, 4), ()),
    'table-pipeless-refused.md': ((), ()),
    'table-pipeless-then-pipe.md': ((4, 5), ()),
    'table-pipeless-lazy.md': ((), ()),
    'table-pipeless-indent-4.md': ((), ()),
    'table-pipeless-setext-tab-item.md': ((1, 3), ()),
    'table-pipeless-setext-tab-quote.md': ((1, 3), ()),
    'table-pipeless-setext-refused.md': ((6, 7), ()),
    'table-pipeless-tab-item-colon.md': ((3, 4), ()),
    'fence-info-backtick.md': ((2, 2), ()),
    'thematic-underscore.md': ((1, 3), ()),
    'heading-indent.md': ((), ()),
    'quote-indent.md': ((), ()),
    'comment-body-mark.md': ((), (2,)),
    'item-wide-gap.md': ((), ()),
    'quote-comment-closed.md': ((4,), ()),
    'item-gap-4.md': ((3, 3), ()),
    'fence-tilde-info-backtick.md': ((), ()),
    'quote-comment-lazy-end.md': ((3,), ()),
    'quote-comment-unclosed.md': ((4, 4), ()),
    'list-comment-unclosed.md': ((4, 4), ()),
    'table-quote-tab-lead.md': ((3, 4), ()),
    'table-end-tab-code.md': ((), ()),
    'table-tab-item.md': ((3, 4), ()),
    'table-tab-not-quote-item.md': ((), ()),
    'table-tab-not-quote-quote.md': ((), ()),
    'table-quote-in-list.md': ((3, 4), ()),
    'quote-indent-cont.md': ((), ()),
    'quote-then-ordered.md': ((1, 2), ()),
    'list-heading-ends.md': ((1, 2), ()),
    'setext-indent-4.md': ((), ()),
    'setext-lazy.md': ((), ()),
    'setext-tab-item.md': ((1, 3), ()),
    'stars-line-tab.md': ((), ()),
    'stars-line-pair.md': ((), ()),
    'quote-item-shifted-setext.md': ((), ()),
    'quote-item-shifted-delim.md': ((), ()),
    'table-item-in-quote.md': ((3, 4), ()),
    'table-lazy-header-indent.md': ((), ()),
    'table-lazy-header-indent-tab.md': ((), ()),
    'table-lazy-header-indent-3col.md': ((4, 5), ()),
    'stars-line-vt.md': ((3,), ()),
    'quote-fence-closes.md': ((4, 4), ()),
    'item-fence-tab.md': ((4, 4), ()),
    'quote-blank-closes.md': ((), ()),
    'item-nested-3.md': ((1, 3), ()),
    'item-thematic-not-item.md': ((), ()),
    'blank-ideographic.md': ((), ()),
    'blank-nbsp.md': ((), ()),
    'blank-vt.md': ((), ()),
    'blank-ff.md': ((), ()),
    'blank-quote-ideographic.md': ((), ()),
    'blank-item-ideographic.md': ((), ()),
    'blank-item-closes.md': ((), ()),
    'blank-ideographic-then-indent.md': ((), ()),
    'blank-space-tab.md': ((1, 3), ()),
    'blank-crlf.md': ((1, 3), ()),
    'item-ideographic-interrupts.md': ((1, 3), ()),
    'item-nbsp-ordered-interrupts.md': ((1, 3), ()),
    'table-header-ideographic.md': ((1, 4), ()),
    'ordered-01-interrupts.md': ((1, 2), ()),
    'ordered-001-paren-interrupts.md': ((1, 2), ()),
    'ordered-00-continues.md': ((), ()),
    'ordered-02-continues.md': ((), ()),
    'table-row-vt-end.md': ((1, 4), ()),
    'table-row-ff-end.md': ((1, 4), ()),
    'table-row-vt-lead.md': ((), ()),
    'table-row-ideographic-end.md': ((), ()),
    'table-header-vt.md': ((1, 4), ()),
    'table-header-ff-spaced.md': ((1, 4), ()),
    'table-header-pipe-vt.md': ((), ()),
    'quote-ideographic-then-indent.md': ((), ()),
    'ordered-fullwidth-continues.md': ((), ()),
    'ordered-arabic-indic-continues.md': ((), ()),
    'item-nested-setext-cont.md': ((), ()),
    'item-thematic-star.md': ((), ()),
    'quote-thematic-after-open.md': ((), ()),
    'item-thematic-after-open.md': ((), ()),
    "excerpt.md": ((4, 6, 8, 10, 12, 14, 16, 19, 21, 24), ()),
    "clean.md": ((), ()),
}

# 期待: `excerpt.md` の抜粋（行番号, 抜粋）。**元の行の字**が出る——伏せ字（`x`）でも、引用の印を置き換えた空白でもない（#564）。
EXCERPTS = (
    (4, "ode` X**「y」"),
    (6, "> `c`X**「y」"),
    (8, " --> X**「y」"),
    (10, " `li`X**「y」"),
    (12, " `hd`X**「y」"),
    (14, " `th`X**「y」 | "),
    (16, " `td`X**「y」 | "),
    (19, "`c1`⏎X**「y」"),
    # タブを含む行（引用の印の直後・項の中）。抜粋はタブを開いた行からではなく元の行から切る（#623 の /code-review 1 パス目 CR1-3）
    (21, "`ab` X**「y」"),
    (24, "`cd` X**「y」"),
)


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
        if path.name == "excerpt.md":
            out["excerpt"] = tuple((lineno, fragment) for lineno, _, fragment in found)
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
        "        if is_blank(text[at:]):\n            flush()",
        "        if False:\n            flush()"),
    "見出しで区切らない": (4,
        "        if HEADING.match(inner):",
        "        if False:"),
    "setext の下線で区切らない": (4,
        "        if para and SETEXT.match(inner):",
        "        if False:"),
    "容れ物が変わっても段落を区切らない": (4,
        "        if matched < len(stack) or new:\n            flush()",
        "        if matched < len(stack) or new:\n            pass"),
    "行ごとに組む": (5,
        "        para.append(shown)\n        last, lazy_last = inner, False\n    flush()",
        "        para.append(shown)\n        flush()\n        last, lazy_last = inner, False\n    flush()"),
    "三つの並びを数えない": (6,
        "        if j - i in (2, 3):",
        "        if j - i == 2:"),
    "フェンスを開かない": (7,
        "        if fence_open:",
        "        if False:"),
    "短い列でもフェンスを閉じる": (7,
        'rf" {{0,3}}{re.escape(fence[0])}{{{fence[1]},}}[ \\t]*$"',
        'rf" {{0,3}}{re.escape(fence[0])}{{3,}}[ \\t]*$"'),
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
        "            quote = QUOTE_MARK.match(text, pos)\n",
        "            quote = None if para and not maybe_lazy else QUOTE_MARK.match(text, pos)\n"),
    "浅い引用の行でも区切る": (16,
        "        maybe_lazy = bool(para) and matched < len(stack)\n",
        '        maybe_lazy = bool(para) and matched < len(stack) and ">" not in stack[matched:]\n'),
    "引用が終わってもフェンスを閉じない": (16,
        "            if matched < len(stack):\n                fence = None",
        "            if False:\n                fence = None"),
    "項の中の続きを認めない": (17,
        "        maybe_lazy = bool(para) and matched < len(stack)\n",
        '        maybe_lazy = bool(para) and matched < len(stack) and all(c == ">" for c in stack[matched:])\n'),
    "ブロックの始まりでも段落の続きにする": (17,
        "        if maybe_lazy and not new and not any(r.match(inner) for r in starts):",
        "        if maybe_lazy and not new:"),
    "どの項でも段落を割り込む": (17,
        '            if para and not maybe_lazy and not new and (empty or (ordered and number != 1)):',
        "            if False:"),
    "項を閉じた印も割り込みの規則で見る": (17,
        '            if para and not maybe_lazy and not new and (empty or (ordered and number != 1)):',
        '            if para and not new and (empty or (ordered and number != 1)):'),
    "項の中身の桁で読まない": (17,
        "            at += container\n",
        "            at += indent_of(text[at:])\n"),
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
        '{{{fence[1]},}}[ \\t]*$", text[at:]):',
        '{{{fence[1]},}}[ \\t]*$", text[at:].lstrip("> ")):'),
    "コメントの中の行もブロックとして読む": (19,
        "                    comment = False\n                continue",
        "                    comment = False"),
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
    "表を見分けない": (23,
        "        if para and indent_of(inner) < 4 and TABLE_DELIM",
        "        if False and indent_of(inner) < 4 and TABLE_DELIM"),
    "見出しの行を段落の最初の行にする": (23,
        "            if not refused and header_cells(last, lazy_last) == cells(inner):",
        "            if not refused and cells(para[0]) == cells(inner):"),
    "表を開けなかった段落で、あとの区切りの行が表を開く": (23,
        "            if not refused and header_cells(last, lazy_last) == cells(inner):",
        "            if header_cells(last, lazy_last) == cells(inner):"),
    # #580 の前の形——直前の行が区切りの形なら開けなかったとみなす近似。段落の続き（lazy）の行も数えて表を見逃し、
    # 開けなかった区切りの行が直前でなければ忘れて表を開く
    "前の行が区切りの形なら見出しの行にしない（#580 の前の形）": (23,
        "            if not refused and header_cells(last, lazy_last) == cells(inner):",
        '            if not (len(para) > 1 and "|" in last and TABLE_DELIM.match(last)) and header_cells(last, lazy_last) == cells(inner):'),
    "字下げした区切りの形の行でも表を試す": (23,
        "        if para and indent_of(inner) < 4 and TABLE_DELIM",
        "        if para and TABLE_DELIM"),
    "字下げの上限を 3 桁にする": (23,
        "        if para and indent_of(inner) < 4 and TABLE_DELIM",
        "        if para and indent_of(inner) < 3 and TABLE_DELIM"),
    "開けなかった印を段落ごとに戻さない": (23,
        "            para_start = lineno\n            refused = False",
        "            para_start = lineno"),
    # 段落の続き（lazy）の区切りの形の行は表を試さない——試すと、引用・項の段落の続きの `--- | ---` で表を開いてしまう（#562・#580）
    "段落の続き（lazy）の区切りの行で表を開く": (23,
        "            para.append(shown)  # 段落の続き（lazy continuation）。容れ物は閉じない\n",
        "            if TABLE_DELIM.match(inner) and cells(last) == cells(inner):\n"
        "                head = para.pop()\n"
        "                flush()\n"
        "                out.append((lineno - 1, [head]))\n"
        "                table = True\n"
        "                del stack[matched:]\n"
        "                continue\n"
        "            para.append(shown)\n"),
    # #581 の前の形——区切りの行に `|` を要る。pipeless の 4 本と tab-item-colon（見逃しに戻る）、pipeless-refused（誤検出に戻る）が殺す
    "区切りの行に | を要る（#581 の前の形）": (23,
        "< 4 and TABLE_DELIM.match(inner):",
        '< 4 and "|" in inner and TABLE_DELIM.match(inner):'),
    # #581 の前の形——setext の下線を、タブを開かない行（容れ物の印の後ろのタブが残る）で見る。setext-refused が殺す
    "setext の下線でタブを数えない（#581 の前の形）": (4,
        "        if para and SETEXT.match(inner):",
        '        if para and SETEXT.match(line.lstrip(" >")):'),
    "セルの数を見ない": (23,
        "    return len(parts)",
        "    return 1"),
    "逃がした | もセルの区切りに数える": (23,
        '    parts = re.split(r"(?<!\\\\)\\|", text)',
        '    parts = re.split(r"\\|", text)'),
    "空行で表を終わらせない": (24,
        "            flush()\n            table = False\n            del stack[matched:]",
        "            flush()\n            del stack[matched:]"),
    "| の無い行を表の行にしない": (24,
        "                out.append((lineno, [shown]))\n                continue",
        "                table = False"),
    "ブロックの始まりで表を終わらせない": (24,
        "indent_of(inner) < 4 and not any(r.match(inner) for r in starts):\n                out.append",
        "indent_of(inner) < 4:\n                out.append"),
    "項・引用の始まりで表を終わらせない": (24,
        "            if matched == len(stack) and not new and indent_of(inner) < 4",
        "            if matched == len(stack) and indent_of(inner) < 4"),
    "インデントしたコードで表を終わらせない": (24,
        "and not new and indent_of(inner) < 4 and not any",
        "and not new and not any"),
    "容れ物の変化で表を終わらせない": (24,
        "            if matched == len(stack) and not new and",
        "            if not new and"),
    "抜粋を伏せ字から切る": (25,
        '            fragment = original[max(0, pos - 6):pos + 8].replace("\\n", "⏎")',
        '            fragment = joined[max(0, pos - 6):pos + 8].replace("\\n", "⏎")'),
    "抜粋を引用の印を空白にした行から切る": (25,
        '        original = "\\n".join(source[start - 1:start - 1 + len(block)])',
        '        original = "\\n".join(block)'),
    # #525 の狭いパスで素通りした変異（#563）。「区切りの行のあとで表を開かない」は #562 の表の試料が、「引用の印の字下げに上限を置かない」は
    # 容れ物を積む形にしてから quote-indent-cont（#623 の段）だけが殺し、ほかは上の SAMPLES の #563 の段の試料が殺す。
    "info にバッククォートがあってもフェンスを開く": (7,
        'FENCE_OPEN = re.compile(r" {0,3}(`{3,}(?=[^`]*$)|~{3,})")',
        'FENCE_OPEN = re.compile(r" {0,3}(`{3,}|~{3,})")'),
    "_ の区切り線を見ない": (18,
        'THEMATIC = re.compile(r" {0,3}([-*_])',
        'THEMATIC = re.compile(r" {0,3}([-*])'),
    "区切りの行のあとで表を開かない": (23,
        "                table = True\n                continue",
        "                table = False\n                continue"),
    "見出しの字下げに上限を置かない": (4,
        'HEADING = re.compile(r" {0,3}#{1,6}',
        'HEADING = re.compile(r" *#{1,6}'),
    # 新しい引用を開く側は字下げ 4 桁未満で止まるので、続きの行の `>` の字下げを見る quote-indent-cont が殺す（#623 の周）
    "引用の印の字下げに上限を置かない": (16,
        'QUOTE_MARK = re.compile(r" {0,3}>[ ]?")',
        'QUOTE_MARK = re.compile(r" *>[ ]?")'),
    "コメントのブロックの本文行の印を拾わない": (13,
        "                if EXEMPT.search(line):\n                    marks.append(lineno)\n",
        ""),
    "項の印の後ろの空白を上限なく中身の桁に数える": (17,
        "    content = marker_end + (gap if 1 <= gap <= 4 else 1)",
        "    content = marker_end + (gap if 1 <= gap else 1)"),
    "引用が終わってもコメントのブロックを閉じない": (16,
        "            if matched < len(stack):\n                comment = False",
        "            if False:\n                comment = False"),
    # #563 の /code-review 1 パス目 CR1-1〜3 が素通りを示した変異（#605）。上の SAMPLES の #605 の段の試料が殺す。
    "項の印の後ろの空白を 3 つまでしか中身の桁に数えない": (17,
        "    content = marker_end + (gap if 1 <= gap <= 4 else 1)",
        "    content = marker_end + (gap if 1 <= gap <= 3 else 1)"),
    "~~~ のフェンスにも info のバッククォートの制限を掛ける": (7,
        'FENCE_OPEN = re.compile(r" {0,3}(`{3,}(?=[^`]*$)|~{3,})")',
        'FENCE_OPEN = re.compile(r" {0,3}((?:`{3,}|~{3,})(?=[^`]*$))")'),
    "空行でしか、引用の終わりでコメントのブロックを閉じない": (16,
        "            if matched < len(stack):\n                comment = False",
        "            if matched < len(stack) and not text.strip():\n                comment = False"),
    # #623・#624 の形（タブの桁・リストの項の中の引用・`*` の並びだけの行）と、#581 の狭いパス NP-1〜3。上の SAMPLES の同じ段の試料が殺す。
    "タブを桁に開かない": (27,
        '    if "\\t" not in line:\n        return line',
        "    if True:\n        return line"),
    "タブを桁の位置によらず 4 桁に開く": (27,
        '        out += " " * (4 - len(out) % 4) if char == "\\t" else char',
        '        out += " " * 4 if char == "\\t" else char'),
    "引用の印の直後のタブから空白 1 桁を使わない": (27,
        '        out += " " * (4 - len(out) % 4) if char == "\\t" else char',
        '        out += " " * (4 - len(out) % 4 + out.endswith(">")) if char == "\\t" else char'),
    # #624 の NP-1——#580 の `width_at` の「`>` の直後のタブだけ 1 桁落とす」を「どのタブでも」に変えた変異を、いまの形に写したもの
    "引用の印の直後でないタブからも 1 桁落とす（#624 の NP-1）": (27,
        '        out += " " * (4 - len(out) % 4) if char == "\\t" else char',
        '        out += " " * (4 - len(out) % 4 - (not out.endswith(">"))) if char == "\\t" else char'),
    # #581 の NP-2 の形——容れ物の桁を、タブを開かない行の字の数で当てる
    "容れ物をタブを開かない行で当てる（#581 の NP-2）": (27,
        "        matched, at = match_containers(text, stack)",
        "        matched, at = match_containers(line, stack)"),
    # #624 の NP-2 の形——容れ物を「引用が外、リストの項が内」の順にしか積まない（main の形）
    "リストの項の中で引用を開かない（#624 の NP-2）": (16,
        "            quote = QUOTE_MARK.match(text, pos)\n",
        '            quote = None if any(c != ">" for c in stack[:matched] + new) else QUOTE_MARK.match(text, pos)\n'),
    "`*` の並びだけの行も区切りに数える（#581 の NP-3）": (26,
        '            if bare[row] != "*" * length:',
        "            if True:"),
    "段落の続きでも setext の下線にする（#581 の NP-1）": (4,
        "        if maybe_lazy and not new and not any(r.match(inner) for r in starts):",
        "        if maybe_lazy and not new and not SETEXT.match(inner) and not any(r.match(inner) for r in starts):"),
    "setext の下線の字下げに上限を置かない（#581 の NP-1）": (4,
        'SETEXT = re.compile(r" {0,3}(?:=+|-+)[ \\t]*$")',
        'SETEXT = re.compile(r" *(?:=+|-+)[ \\t]*$")'),
    # 1 パス目の関門（#623 の周）の指摘を守る変異。上の SAMPLES の同じ段の試料が殺す。
    # 項の中身の桁を、外の容れ物の本文からでなく行の頭からの桁で積む（積む側だけ）。R1 の元の形（1 パス目の版は積む側と当てる側の 2 箇所の組）
    # ではない——1 箇所の置き換えでは R1 を再現できず、この変異を殺すのは table-item-in-quote だけ。R1 の再発そのものは
    # quote-item-shifted-* の期待が捕まえる（#623 の 2 パス目の /code-review CR2-4）
    "項の中身の桁を行の頭からの桁で積む": (16,
        "            new.append(offset)\n",
        "            new.append(pos + offset)\n"),
    "段落の続きの見出しの行の字下げをセルに数えない（#623 の Verifier R2）": (23,
        '    extra = lazy and row[:1] == " " and row.lstrip(" ").startswith("|")',
        "    extra = False"),
    "`*` の並びだけの行の空白を str.strip で剥がす（#623 の CR1-5）": (26,
        '        bare = ["".join(c for c in row if not is_space(c)) for row in joined.split("\\n")]',
        '        bare = ["".join(c for c in row if c.strip()) for row in joined.split("\\n")]'),
    "容れ物の中のフェンスを行の頭から閉じる（#623 の CR1-2）": (16,
        '{{{fence[1]},}}[ \\t]*$", text[at:]):',
        '{{{fence[1]},}}[ \\t]*$", text):'),
    # 2 パス目の関門（#623 の周）の指摘を守る変異。上の SAMPLES の同じ段の試料が殺す。
    "項の中身の桁を積み上げない（#623 の V2-1）": (16,
        "            at += container\n",
        "            at = container\n"),
    "区切り線の形でも項を始める（#623 の V2-2）": (17,
        "            item = None if THEMATIC.match(text[pos:]) else item_of(text[pos:])",
        "            item = item_of(text[pos:])"),
    "空行で印の無い引用を閉じない（#623 の CR1-7）": (16,
        "            del stack[matched:]  # 空行は",
        "            pass  # 空行は"),
    "抜粋の行をタブを開いた行から作る（#623 の CR1-3）": (25,
        '        shown = " " * start + line[start:]',
        '        shown = " " * pos + text[pos:]'),
    # #667 の変異。上の SAMPLES の #667 の段の試料が殺す。
    # 空行の判定を `str.strip` に戻す（main の形）——U+3000・NBSP・`\v`・`\f` だけの行を空行と読む。呼ぶ場所ごとに分けて壊す
    "空行を str.strip で判定する（#667）": (4,
        "        if is_blank(text[at:]):\n            flush()",
        "        if not text[at:].strip():\n            flush()"),
    "容れ物の空行を str.strip で判定する（#667）": (4,
        "        elif not is_blank(text[at:]):",
        "        elif text[at:].strip():"),
    "空の項を str.strip で判定する（#667）": (4,
        "is_blank(body), content",
        "not body.strip(), content"),
    "中身の無い行を str.strip で判定する（#667）": (4,
        "        if is_blank(inner):",
        "        if not inner.strip():"),
    "表の行の端を str.strip で剥がす（#667）": (4,
        '    text = row.lstrip(" \\t").rstrip(" \\t\\v\\f") or row.strip(" \\t")',
        "    text = row.strip()"),
    # 1 パス目の版の形——行末の `\v`・`\f` を剥がさない（#667 の /code-review 1 パス目 CR1-1）
    "表の行末の \\v \\f を剥がさない（#667 の CR1-1）": (4,
        '    text = row.lstrip(" \\t").rstrip(" \\t\\v\\f") or row.strip(" \\t")',
        '    text = row.strip(" \\t") or row.strip(" \\t")'),
    # 2 パス目の版の形——`\v`・`\f` だけの見出しの行を剥がしてセル 0 にする（#667 の 2 パス目 CR2-1）
    "\\v \\f だけの見出しの行を剥がして空にする（#667 の CR2-1）": (4,
        ' or row.strip(" \\t")\n',
        '\n'),
    # 容れ物の印の直後の中身だけ `str.strip` で空と読む（A1 の経路 (d)。#667 の 2 パス目 CR2-2）
    "容れ物の印の直後の中身を str.strip で判定する（#667 の CR2-2）": (4,
        "        if is_blank(inner):",
        "        if is_blank(inner) or (bool(new) and not inner.strip()):"),
    # 番号に ASCII でない数字も当てる（#667 の CR1-2）——`１.` が値 1 として段落を割り込む
    "番号に ASCII でない数字も当てる（#667 の CR1-2）": (17,
        "([0-9]{1,9})[.)]",
        "(\\d{1,9})[.)]"),
    # 割り込める番号を文字列 `"1"` と比べる（main の形）——`01.` `001)` が割り込まない
    "割り込める番号を文字列で比べる（#667）": (17,
        "(int(m.group(2)) if ordered else 0)",
        '((1 if m.group(2) == "1" else 2) if ordered else 0)'),
    # #648 の狭いパスの変異（要確認 #661 で後で直すと決めた）。Verifier が設計した形
    "項の中身の桁を 1 桁足りずに積む（#648 の狭いパス NP-1）": (16,
        "            at += container\n",
        "            at += max(container - 1, 0)\n"),
    "`* * *` を項として開く（#648 の狭いパス NP-2）": (17,
        "            item = None if THEMATIC.match(text[pos:]) else item_of(text[pos:])",
        '            item = None if THEMATIC.match(text[pos:]) and text[pos:].lstrip()[:1] == "-" else item_of(text[pos:])'),
    "容れ物を開いた直後の区切り線を項として開く（#648 の狭いパス NP-3）": (17,
        "            item = None if THEMATIC.match(text[pos:]) else item_of(text[pos:])",
        "            item = None if THEMATIC.match(text[pos:]) and not new else item_of(text[pos:])"),
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

        print("\nエラーの抜粋（元の行から切る。#564）")
        got = dict(correct.get("excerpt", ()))
        for lineno, fragment in EXCERPTS:
            check(f"excerpt.md:{lineno} の抜粋が {fragment!r}（伏せ字でない）", got.get(lineno) == fragment)
        check("excerpt.md の抜粋が期待と 1 対 1", tuple(correct.get("excerpt", ())) == EXCERPTS)

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
