#!/usr/bin/env python3
"""`SKILL.md` の節構造を測り、設計ドキュメントの生成ブロックに書き込む。

usage:
    python3 scripts/skill-metrics.py            # 生成ブロックを書き込む
    python3 scripts/skill-metrics.py --check    # 書き込まず、古ければ非ゼロ終了

CI（`.github/workflows/docs.yml`）が `--check` で呼ぶ。

## なぜ要るか（#78）

`docs/plugins/dev-loop-design.md` の §8.2 は、**判断を測定値だけで正当化している節**である
（#74: 「dev-loop を分割しない」）。20 個以上の数字が `SKILL.md` の節構造に依存していて、
**`SKILL.md` を編集すると黙って古くなる。差分にも現れない。**

これは #50 / #72 で塞いだのと同じ形——drawio を直して書き出しを忘れても差分には出ない。
違うのは**頻度**で、直近 3 か月に `SKILL.md` を触った 15 コミットのうち **13 が行数を
動かしている**。だから「指紋がずれたら手で直せ」では**税が重すぎる**。

**そこで数字そのものを生成する。** 手で直す箇所がゼロになり、古くなりようがない。

## 式を 1 箇所に置く

`diagram_manifest.py` を分けたのは、生成（`export-diagrams.py`）と検査
（`check-diagram-freshness.py`）が**別のスクリプト**だったからで、式が 2 箇所にあると
片方だけ緑になる。**ここは 1 本が両方をやる**ので、式は自然に 1 箇所にしかない
（`--check` は「書き込む代わりに比べる」だけ）。**この構造を崩さないこと。**

## 節の切り方（`SKILL.md` 自身が宣言している規約と同じ）

- 節は**見出し行を含み、次の見出しの直前まで**。
- **`###` は親の `##` に畳まない。**
- **最初の見出しより前**（frontmatter・タイトル・バナー等）は節の外＝「前書き」。

この規約は `SKILL.md` の §8.2 冒頭にも書いてある。**実際に、畳むかどうかで数字が変わる**
——#74 の周で、検証者が `###` を親に畳んだために誤った反証を出した。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from markdown_fences import strip_fences, unclosed_fence  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

SKILL_DIR = Path("plugins/dev-loop/skills/dev-loop")
SKILL = SKILL_DIR / "SKILL.md"
# **起点に載らない分**（#136）。**規範としては原本の一部**である。
#
# - `references/` — **条件が立った周だけが読む**（再開の周など）。
# - `prompts/` — **委譲するときに読む**。条件ではなく用途で分かれている。
#
# **どちらも `SKILL.md` とは別に数える。** 混ぜると、**節を移しただけで「減った」と
# 読める数字**が出る——内容は 1 行も減っていないのに。
LAZY_DIRS = ("references", "prompts")


def lazy_files(root: Path) -> list[Path]:
    """起点に載らないファイルを返す。**無ければ空**（この仕組みを使っていないリポジトリ）。"""
    out = []
    for name in LAZY_DIRS:
        base = root / SKILL_DIR / name
        if base.is_dir():
            out += [(name, p) for p in sorted(base.glob("*.md"))]
    return out
DOC = Path("docs/plugins/dev-loop-design.md")

BEGIN = "<!-- skill-metrics:begin -->"
END = "<!-- skill-metrics:end -->"

# 節の見出しとして数えるもの。`#`（タイトル）は数えない——1 つしかなく、
# 節ではないため。`####` 以下は `SKILL.md` に存在しない。
HEADING = re.compile(r"^#{2,3} ")

# 「必須」の印。**`（必須）` だけを数える。**
#
# 初版は `**必須**` も数えていたが、**実際には 0 回しか現れない**
# （「手順 4・6 でも使われている」とコメントに書いたのは、確かめずに書いた誤り。
# `/code-review` に指摘されて実測した）。**幻の印を数える式は、読む人に
# 「両方の表記を拾っている」と誤解させる**ので消した。
#
# **`必須` という語は、この印以外の形でも出てくる**——地の文
# （「必須要件は互いに掛け算になる」等）や見出しの一部。**それらは数えない。**
# **ここに実数を書かない**——`SKILL.md` を直すたびに古くなる手書きの派生値になり、
# このスクリプトが無くそうとしているものそのものになる（実際、初版のコメントに
# 書いた 2 つの数字のうち 1 つが既に誤っていた）。現在の値は生成ブロックにある。
#
# **だから「マーカーが無い節」＝「必須要件が無い節」ではない。**
# 設計ドキュメント §8.2 はこの区別を明記している。
MARKERS = ("（必須）",)


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def sections(text: str) -> tuple[int, int, list[tuple[str, int, int]]]:
    """(総行数, 前書きの行数, [(見出し, 行数, 必須マーカー数)]) を返す。

    **末尾の改行で 1 行ずれないよう `rstrip("\\n")` してから数える**
    （`wc -l` と一致させる）。ここがずれると全部の数字がずれる。
    """
    lines = text.rstrip("\n").split("\n")
    total = len(lines)
    # **フェンスの中は数えない。** 例示のためのコードブロックに `##` や `（必須）` が
    # 入っていると、幻の節や幻のマーカーが表に出る——実際に `SKILL.md` の bash フェンス内の
    # `（必須）` を計上しており、**手順 1 が二重に数えられ、合計が 1 多かった**。
    # （**ここにも実数を書かない**。現在の値は生成ブロックにある。）
    # `strip_fences` は**行数を保って空行に置き換える**ので、行数の計算には影響しない。
    joined = "\n".join(lines)
    # **閉じ忘れたフェンスの上では測らない。** 閉じていないフェンスは以降を全部
    # 飲み込むので、**そこから後ろの節が表から丸ごと消える**（実測で 2 節が消え、
    # 1 節が 12 行を飲んだ）。`--check` は赤くなるが**作り直せば緑になる**ので、
    # 鮮度では守れない——**測る前に落とす。**
    fence = unclosed_fence(joined)
    if fence is not None:
        fail(
            f"{SKILL}: コードフェンス（{fence}）が閉じられていない。"
            "閉じないと以降の節が測定から消えるので、直してから走らせること"
        )
    stripped = strip_fences(joined).split("\n")
    heads = [i for i, line in enumerate(stripped) if HEADING.match(line)]
    if not heads:
        fail(f"{SKILL}: 見出しが 1 つも無い。節の切り方を確認すること")

    rows: list[tuple[str, int, int]] = []
    for index, start in enumerate(heads):
        end = heads[index + 1] if index + 1 < len(heads) else total
        body = "\n".join(stripped[start:end])
        count = sum(body.count(marker) for marker in MARKERS)
        rows.append((lines[start], end - start, count))
    return total, heads[0], rows


def render(total: int, preamble: int, rows: list[tuple[str, int, int]],
           refs: list[tuple[str, int, int]] | None = None) -> str:
    """生成ブロックの中身を組み立てる。

    **節名も出す。** 行数とマーカー数が同じまま見出しだけ変わる編集を
    落とすため（受入基準の経路 4）。

    **`references/` を別に出す（#136）。** 混ぜると、**節を `references/` に移しただけで
    「減った」と読める数字が出る**——**内容は 1 行も減っていないのに。**
    設計 §8.2 は**この数字だけで判断を正当化している**ので、
    **「起点に載る分」と「遅延分」を分けないと、論証の前提が黙って入れ替わる。**
    """
    with_marker = sum(n for _, n, m in rows if m)
    without_marker = sum(n for _, n, m in rows if not m)
    markers = sum(m for _, _, m in rows)

    out = [
        BEGIN,
        "",
        f"**`SKILL.md` は {total} 行**（うち前書き {preamble} 行は節の外）。"
        f"**`（必須）` は {markers} 個**あり、"
        f"**それを含む節が {with_marker} 行＝全体の {with_marker / total * 100:.0f}%**、"
        f"含まない節が {without_marker} 行。",
        "",
        "| 節 | 行 | `（必須）` |",
        "| --- | --- | --- |",
    ]
    for head, n, m in rows:
        name = head.lstrip("# ").strip().replace("|", r"\|")
        out.append(f"| {name} | {n} | {m if m else '—'} |")
    if refs:
        ref_lines = sum(n for _, n, _ in refs)
        ref_markers = sum(m for _, _, m in refs)
        out += [
            "",
            f"**このほかに、起点に載らないファイルが {len(refs)} 本・{ref_lines} 行**"
            f"（`（必須）` {ref_markers} 個）**ある。** "
            f"**これは起点に載らない**——**要るときだけ読む**"
            f"（`references/` は条件が立った周だけ、`prompts/` は委譲するとき）。 "
            f"**規範としては原本の一部で、上の表とは足し算の関係にある**"
            f"（合わせて {total + ref_lines} 行・`（必須）` {markers + ref_markers} 個）。",
            "",
            "| 起点に載らないファイル | 行 | `（必須）` |",
            "| --- | --- | --- |",
        ]
        for name, n, m in refs:
            out.append(f"| {name} | {n} | {m if m else '—'} |")

    out += [
        "",
        "<small>この表と上の段落は `scripts/skill-metrics.py` が生成している。"
        "**手で書き換えない**——`SKILL.md` を編集したら "
        "`python3 scripts/skill-metrics.py` で作り直す（CI が `--check` で見ている）。</small>",
        "",
        END,
    ]
    return "\n".join(out)


def splice(doc: str, block: str) -> str:
    """生成ブロックを差し替える。マーカーが無ければ落とす。

    **「無い」を黙って通さない。** マーカーを消すだけで検査が素通りするなら、
    それは歯止めになっていない（#50 の周で繰り返した失敗の形）。

    **マーカーは「その行がマーカーだけ」であることを要求する。** 単なる文字列一致だと、
    **散文の中でマーカーに言及しただけで 2 個に数えてしまう**——実際にこの周で踏んだ
    （節の説明文に `<!-- skill-metrics:begin -->` と書いたら検査が落ちた）。
    行全体で見れば、コード span 内の言及と本物を区別できる。
    """
    # **ドキュメント側の閉じ忘れも落とす。** `SKILL.md` 側だけ守っていたのは
    # **非対称**だった。§8.2 より前のどこかでフェンスを閉じ忘れると、**本物の
    # マーカーごと飲み込まれ**、「消してしまったなら戻すこと」という**誤誘導**が出る
    # ——誰も消していないのに。
    fence = unclosed_fence(doc)
    if fence is not None:
        fail(
            f"{DOC}: コードフェンス（{fence}）が閉じられていない。"
            "閉じないと生成ブロックのマーカーごと飲み込まれるので、直してから走らせること"
        )
    lines = doc.split("\n")
    # **ドキュメント側のフェンスも落としてから数える。** §8.2 は**生成ブロックそのものを
    # 説明する節**なので、将来そこに**例示としてマーカーを書く**ことは十分ありうる
    # （`CLAUDE.md` は版バナーでまさにその書き方をしており、`strip_fences` が
    # 存在する理由がそれである）。落とさないと「マーカーが 2 組ある」で落ち、しかも
    # **「手で消した場合は戻すこと」という案内が誤誘導になる**——何も消していないので。
    scan = strip_fences(doc).split("\n")
    begins = [i for i, line in enumerate(scan) if line.strip() == BEGIN]
    ends = [i for i, line in enumerate(scan) if line.strip() == END]
    if len(begins) != 1 or len(ends) != 1:
        fail(
            f"{DOC}: 生成ブロックのマーカーが 1 組ではない"
            f"（開始 {len(begins)} 個、終了 {len(ends)} 個）。"
            "消してしまったなら戻すこと。フェンスの外に 1 組だけ置く"
        )
    if ends[0] < begins[0]:
        fail(f"{DOC}: 生成ブロックの終了マーカーが開始より前にある")
    return "\n".join(lines[: begins[0]] + block.split("\n") + lines[ends[0] + 1 :])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="書き込まず、生成ブロックが現在の SKILL.md と一致するかだけ見る",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="リポジトリのルート（テスト用。既定はこのスクリプトの親の親）",
    )
    args = parser.parse_args()

    skill_path = args.root / SKILL
    doc_path = args.root / DOC
    for path in (skill_path, doc_path):
        if not path.is_file():
            fail(f"{path} が無い")

    total, preamble, rows = sections(skill_path.read_text(encoding="utf-8"))
    # `references/` は**ファイル 1 本を 1 行**として数える（節ではなくファイル単位）。
    # **起点に載らない分なので、上の表とは別に出す。**
    refs = []
    for dirname, path in lazy_files(args.root):
        text = path.read_text(encoding="utf-8").rstrip("\n")
        # **本体と同じ数え方にする**——フェンスの中は数えない（`sections` と同じ）。
        stripped = strip_fences(text)
        refs.append((f"{dirname}/{path.name}", len(text.split("\n")),
                     sum(stripped.count(m) for m in MARKERS)))
    block = render(total, preamble, rows, refs)
    doc = doc_path.read_text(encoding="utf-8")
    updated = splice(doc, block)

    if args.check:
        if updated != doc:
            print(
                f"{DOC} の生成ブロックが {SKILL} と一致しません。\n"
                "`python3 scripts/skill-metrics.py` で作り直してコミットしてください。",
                file=sys.stderr,
            )
            print(
                # **「マーカー」と呼ばない。** 生成ブロックの `<!-- ... -->` も
                # マーカーと呼んでおり、**テストが両者を区別できなくなる**
                # ——実際に、マーカー検査を外した破壊がこの行のせいで
                # 「検出した」ように見えていた（偶然の一致）。
                f"（現在の測定: {total} 行 / 前書き {preamble} 行 / "
                f"節 {len(rows)} 個 / `（必須）` {sum(m for _, _, m in rows)} 個）",
                file=sys.stderr,
            )
            return 1
        print(f"生成ブロックは最新です（{SKILL}: {total} 行 / 節 {len(rows)} 個）")
        return 0

    if updated == doc:
        print(f"変更なし（{SKILL}: {total} 行 / 節 {len(rows)} 個）")
        return 0
    doc_path.write_text(updated, encoding="utf-8")
    print(f"{DOC} の生成ブロックを更新しました（{SKILL}: {total} 行 / 節 {len(rows)} 個）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
