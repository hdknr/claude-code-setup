#!/usr/bin/env python3
"""必須マーカー `（必須）` が `SKILL.md` の外に漏れていないかを検出する。

CI（.github/workflows/plugins.yml）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-norm-markers.py

なぜ必要か（#94）: dev-loop の規範は `SKILL.md`・`plugins/dev-loop/README.md`・
`docs/plugins/dev-loop-design.md`・カタログ JSON・frontmatter に**分散していた**。
規範を 1 つ足すたびに全部へ届かせる必要がある。

**経緯（#75 で決めたのに複製が増え続けたこと・その実測）は設計ドキュメント §8.1
（`#miscount`）を正とする。ここに書かない**——**話を 2 箇所に置くのが、
そもそもこのスクリプトが直そうとしている形**である。

検証する内容:

    `（必須）` は原本（`SKILL.md`）にしか書けない。

例外は 2 つだけで、**どちらも位置ではなく形で判定する**（節番号で判定すると、
節を並べ替えたときに黙って壊れる）:

1. **バッククォートに囲まれている** — `` `（必須）` `` のように**マーカー自体を論じている**
   場合。設計ドキュメント §8.2 が「数えているのは丸括弧で囲んだ `（必須）` だけ」と
   書いているのがこれで、これは規範の複製ではない。
2. **`skill-metrics` の生成ブロックの中** — `scripts/skill-metrics.py` が `SKILL.md` を
   測って書き込む表。節名に `（必須）` を含む節があれば、そのまま表に出る。

**この検査が守らないもの**——ここが穴である。`check-diagram-freshness.py` と同じく、
**何を守らないかを書いておかないと、緑であることが安心の根拠に化ける**:

| 守らないもの | なぜ |
| --- | --- |
| **マーカーを持たない規範の複製** | 数えているのは `（必須）` という文字列だけ。`**太字**` で書いた規範は通る。**#94 で `README.md` から外した規範はほとんどがこの形で、この検査では捕まらなかった** |
| **Markdown 以外のファイル** | **走査するのは `*.md` だけ**である。`.claude-plugin/marketplace.json` と `plugins/<name>/.claude-plugin/plugin.json` の `description`、`.github/workflows/*.yml` のコメントは**一度も見ていない**。どれも現に規範を持っており、**緑であることは「全入口が守られている」を意味しない**（#94 のレビューが指摘） |
| **規範の*内容*が食い違うこと** | 同じ規範が 2 箇所にあって中身が違っても、マーカーが片方だけなら通る |
| **原本の中の重複** | `SKILL.md` の中で同じ規範を 2 度書いても通る（#92 で実際に起きた） |
| **ポインタの指し先が実在するか** | 「`SKILL.md` の手順 6 を正とする」と書いて手順 6 に何も無くても通る |
| **フェンスの中の記載** | `strip_fences` で落としている。例示のためのコードブロックを数えると、**規約を例示しただけで落ちる**（`skill-metrics.py` と同じ扱い） |
| **他のプラグインの `SKILL.md`** | 原本は dev-loop の 1 本だけなので、`plugins/cmux/` などがマーカーを使うと**このスクリプトが誤ったエラーメッセージを出す**（「dev-loop の原本へ移せ」と言う）。**そうなったら ORIGIN を「プラグインごとの原本」に一般化すること**——いまは dev-loop 以外がマーカーを使っていないので単数にしてある |
| **`skill-metrics` の開始印を他のファイルに貼ること** | どのファイルでも生成ブロックとして扱うので、**貼れば以降が全部免除される**。印を偽装する動機がある状況は想定していない |
| **1 行にバッククォートが奇数個ある場合** | 閉じ忘れた囲みが**後続の正常な囲みと対になり**、間の素のマーカーが引用扱いで消える（`` `閉じ忘れ （必須） そして `本物` ``）。**見逃す向き**である。正しく直すにはインラインの構文解析が要り、**行単位の正規表現では原理的に取れない**。閉じ忘れ自体が壊れた Markdown なので、そちらを直すのが筋 |

つまりこれは**「規範が漏れていない」の証明ではなく、「最も強い印が漏れていない」の検査**である。
それでも置く価値があるのは、**`（必須）` を付ける行為が「これは規範だ」という著者の自己申告**
だからで、**申告した規範が原本の外に出ることだけは機械で止まる**。
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from markdown_fences import strip_fences  # noqa: E402

MARKER = "（必須）"

# 原本。ここにだけマーカーを書いてよい。
ORIGIN = "plugins/dev-loop/skills/dev-loop/SKILL.md"

# 走査する先。**ここを増やし忘れると、増やした先が黙って対象外になる**ので、
# 「拾いすぎて落とす」側に倒して .md を全部見る（除外は下の SKIP_DIRS だけ）。
SKIP_DIRS = {".git", "site", ".venv", "node_modules", "__pycache__", ".claude"}

GENERATED_BEGIN = "<!-- skill-metrics:begin -->"
GENERATED_END = "<!-- skill-metrics:end -->"

# インラインコード。**2 つ直した跡が入っている。**
#
# 1. 最初はマーカーを含む囲みだけを拾う形（`` `[^`]*（必須）[^`]*` ``）にしていたが、
#    **2 つの囲みの間に素のマーカーがある行を見逃した**——`` `A` は（必須）で `B` `` という、
#    このリポジトリでは**ごく普通の書き方**である。最初の囲みの閉じと次の囲みの開きが
#    1 つの囲みとして一致し、**間の素のマーカーごと消えていた**。
#    だから「マーカーを含む囲み」ではなく**すべての囲みを落としてから**マーカーを探す。
# 2. ところが単純な `` `[^`]*` `` にしたら、今度は**二重バッククォートの囲みを誤検出した**
#    （`` ``（必須）`` `` が違反になる）。開きの 2 本目を「空の囲み」として食ってしまい、
#    間のマーカーが素のまま残るため。**見逃しを直して誤検出を作った**形で、
#    どちらも #94 のレビューが再現例つきで見つけている。
#
# だから**開いた本数と同じ本数で閉じる**（Markdown の規則）。`markdown_fences.py` が
# フェンスに対して長さを見ているのと同じ理由で、**インラインでも長さを見ないと壊れる**。
#
# **後方参照と遅延量指定子だけで書く。** 最初は `(?!\1)` を挟んで
# `` (`+)(?:(?!\1)[\s\S])*?\1 `` としていたが、**この否定先読みは何も足していなかった**
# ——2,541 通りの文字列で判定差が 0 件だった。**冗長な条件は変異として殺せない**ので、
# 「テストが 6 件ある」の中身が 1 つ空になる（#94 のレビューが指摘）。
# 落とせる条件は落として、**残った条件が全部テストで固定されている状態**にする。
CODE_SPAN = re.compile(r"(`+)[\s\S]*?\1")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def markdown_files(root: Path) -> list[Path]:
    out = []
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        out.append(path)
    return out


def violations(root: Path) -> list[tuple[str, int, str]]:
    """(相対パス, 行番号, 行の中身) を返す。"""
    found = []
    for path in markdown_files(root):
        rel = path.relative_to(root).as_posix()
        if rel == ORIGIN:
            continue
        in_generated = False
        # **フェンスの中は数えない。** `skill-metrics.py` と `check-plugin-versions.py` が
        # 同じことをしており、**式が 2 箇所にあると片方だけ緑になる**ので共有モジュールを使う
        # （揃えなかったときに何が起きたかは `main()` のコメントに 1 箇所だけ書いてある）。
        # `strip_fences` は**行数を保って空行に置き換える**ので、行番号はずれない。
        stripped = strip_fences(path.read_text(encoding="utf-8")).splitlines()
        for lineno, line in enumerate(stripped, 1):
            if GENERATED_BEGIN in line:
                in_generated = True
            elif GENERATED_END in line:
                in_generated = False
            if MARKER not in line or in_generated:
                continue
            # **インラインコードを全部落としてから**、まだ残っているかを見る。
            # **「1 つでも引用されていれば見逃す」ではない**——同じ行に引用と素の
            # マーカーが混在したら、素のほうを捕まえる必要がある。
            if MARKER in CODE_SPAN.sub("", line):
                found.append((rel, lineno, line.strip()))
    return found


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    origin = root / ORIGIN
    if not origin.exists():
        fail(f"原本が見つからない: {ORIGIN}")
        fail("原本を移動したなら、このスクリプトの ORIGIN も直すこと。")
        return 1

    found = violations(root)
    if found:
        fail(f"`{MARKER}` が原本（{ORIGIN}）の外にあります:")
        for rel, lineno, line in found:
            fail(f"  {rel}:{lineno}: {line[:100]}")
        fail("")
        fail("規範の本体は原本にだけ置き、他の箇所からは指すこと（#75 / #94）。")
        fail(f"マーカー自体を論じたいなら、バッククォートで囲んで `{MARKER}` と書く。")
        return 1

    total = len(markdown_files(root))
    # **ここも `strip_fences` を通す。** 素で数えると `skill-metrics.py` が報告する数と
    # 食い違い、**同じ量に 2 つの公式な数**ができる（#94 で実際に 70 対 69 になった）。
    #
    # **ただし完全には揃っていない。** `skill-metrics.py` は**節ごとに数えて前書きを除く**が、
    # ここはファイル全体を数える。いま一致するのは、**たまたま前書き（frontmatter と
    # 版のバナー）にマーカーが無いから**にすぎない。frontmatter の `description` に
    # マーカーが入れば、また食い違う。**この数は参考値**であって、
    # **節ごとの正は `skill-metrics.py` の生成ブロック**である。
    count = strip_fences((root / ORIGIN).read_text(encoding="utf-8")).count(MARKER)
    print(f"必須マーカーの検査: 問題なし"
          f"（{total} 件の Markdown を検査。原本に {count} 個・参考値）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
