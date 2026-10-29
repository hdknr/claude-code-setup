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
        "        if not body:\n            if current:",
        "        if False:\n            if current:"),
    "見出し・表の行で区切らない": (4,
        '        single = bool(HEADING.match(body)) or body.startswith("|")',
        "        single = False"),
    "リストの項で区切らない": (4,
        "        if current and (single or item or enters_quote):",
        "        if current and (single or enters_quote):"),
    "行ごとに組む": (5,
        "        if single:\n            yield start, current",
        "        if True:\n            yield start, current"),
    "三つの並びを数えない": (6,
        "        if j - i in (2, 3):",
        "        if j - i == 2:"),
    "フェンスを剥がさない": (7,
        '    plain = blank_non_paragraphs(strip_fences("\\n".join(bodies)).split("\\n"))',
        "    plain = blank_non_paragraphs(bodies)"),
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
        '    bodies, quoted = unquote(strip_frontmatter(text).split("\\n"))',
        '    bodies, quoted = unquote(text.split("\\n"))'),
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
    "何も見ていなくても緑": (14,
        "    if checked == 0:",
        "    if False:"),
    "コードスパンをファイル全体で組む": (15,
        "    for start, block in blocks(plain, quoted):",
        '    for start, block in blocks(mask_inline("\\n".join(plain))[0].split("\\n"), quoted):'),
    "引用の始まりで区切らない": (16,
        "        enters_quote = is_quote and not quoted[lineno - 2]",
        "        enters_quote = False"),
    "どの番号でも段落を割り込む": (17,
        '        item = bool(BULLET.match(body)) or bool(ordered and (ordered.group(1) == "1" or in_list))',
        "        item = bool(BULLET.match(body)) or bool(ordered)"),
    "隣の番号の項を区切らない": (17,
        '        item = bool(BULLET.match(body)) or bool(ordered and (ordered.group(1) == "1" or in_list))',
        '        item = bool(BULLET.match(body)) or bool(ordered and ordered.group(1) == "1")'),
    "区切り線を本文として見る": (18,
        "        if THEMATIC.match(out[i]):",
        "        if False:"),
    "コメントのブロックを本文として見る": (18,
        "        if COMMENT_BLOCK.match(out[i]):",
        "        if False:"),
    "引用の中のフェンスを剥がさない": (19,
        '        bodies.append(" " * len(prefix) + line[len(prefix):])',
        "        bodies.append(line)"),
    "コメントの区切りごと伏せる": (20,
        "            for p in range(i + 4, close):",
        "            for p in range(i, close + 3):"),
    "コメントを伏せない": (20,
        "            for p in range(i + 4, close):\n                if runs_out[p] != \"\\n\":\n                    runs_out[p] = \"x\"",
        "            for p in range(i + 4, close):\n                pass"),
    "コメントを見ない（バッククォートが勝つ）": (21,
        '        if text.startswith("<!--", i):',
        "        if False:"),
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
            # 共有モジュールを同じ場所から読めるようにする
            (d / "markdown_fences.py").write_text(
                (REAL_REPO / "scripts" / "markdown_fences.py").read_text(encoding="utf-8"),
                encoding="utf-8")
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
