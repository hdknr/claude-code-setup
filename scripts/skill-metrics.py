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

SKILL = Path("plugins/dev-loop/skills/dev-loop/SKILL.md")
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


def render(total: int, preamble: int, rows: list[tuple[str, int, int]]) -> str:
    """生成ブロックの中身を組み立てる。

    **節名も出す。** 行数とマーカー数が同じまま見出しだけ変わる編集を
    落とすため（受入基準の経路 4）。
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
    # **節名は 1 つずつ鉤括弧で囲む。** 節名自体が「・」を含むことがある
    # （実在: 「待ち時間・定時処理は別スキル」）ので、区切りに「・」を使うと
    # **何節あるのか読めなくなる**。
    ranked = sorted(rows, key=lambda r: r[1], reverse=True)
    top = ranked[:2]
    top_names = "と".join(f"「{head.lstrip('# ').strip()}」" for head, _, _ in top)
    # **同点のときは名指しを避ける。** `sorted` は安定なので、2 位と 3 位が同じ行数だと
    # **文書順の片方だけ**を黙って選ぶ——それを「最も大きい」と書くと検証できない主張になる。
    tied = len(ranked) > len(top) and ranked[len(top) - 1][1] == ranked[len(top)][1]
    if len(top) < 2:
        head_line = f"**節は {len(top)} つしかない**（{top_names}）。"
    elif tied:
        head_line = (
            f"**行数が最も大きいのは {top_names} だが、同じ行数の節が他にもある**"
            "——順位は下表で確かめること。"
        )
    else:
        head_line = f"**行数が最も大きい 2 節は {top_names}**。"
    out += [
        "",
        head_line
        + f"**`（必須）` を含まない節は {without_marker} 行＝全体の "
        f"{without_marker / total * 100:.1f}%** で、"
        f"これが「切り出せる上限」の側に振れた値である"
        f"（印を付けていない必須文は数に入らないため）。",
        "",
        "<small>この表と上下の段落は `scripts/skill-metrics.py` が生成している。"
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
    block = render(total, preamble, rows)
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
