#!/usr/bin/env python3
"""必須マーカー `（必須）` が `SKILL.md` の外に漏れていないかを検出する。

CI（.github/workflows/plugins.yml）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-norm-markers.py

なぜ必要か（#94）: dev-loop の規範は `SKILL.md`・`plugins/dev-loop/README.md`・
`docs/plugins/dev-loop-design.md`・カタログ JSON・frontmatter に**分散していた**。
規範を 1 つ足すたびに全部へ届かせる必要がある。

#75 で「落とせない／落としてよいの列挙は `SKILL.md` にしか置かない」と決めていたが、
**その規約を見張る仕組みが無かった**ので、決めたあとも複製が増え続けた。
**宣言は検査ではない。**

**経緯と実測は設計ドキュメント §8.1（`#miscount`）を正とする。ここに数字を書かない**
——数字を 2 箇所に置くのが、そもそもこのスクリプトが直そうとしている形である。

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
| **マーカーを持たない規範の複製** | 数えているのは `（必須）` という文字列だけ。`**太字**` で書いた規範は通る。#94 で `README.md` から外した 39 行は、ほとんどがこの形だった——**この検査では捕まらなかった** |
| **規範の*内容*が食い違うこと** | 同じ規範が 2 箇所にあって中身が違っても、マーカーが片方だけなら通る |
| **原本の中の重複** | `SKILL.md` の中で同じ規範を 2 度書いても通る（#92 で実際に起きた） |
| **ポインタの指し先が実在するか** | 「`SKILL.md` の手順 6 を正とする」と書いて手順 6 に何も無くても通る |
| **フェンスの中の記載** | `strip_fences` で落としている。例示のためのコードブロックを数えると、**規約を例示しただけで落ちる**（`skill-metrics.py` と同じ扱い） |

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

# バッククォートに囲まれたマーカー（マーカー自体を論じている）。
QUOTED = re.compile(r"`[^`]*" + re.escape(MARKER) + r"[^`]*`")


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
        # 同じことをしており、**式が 2 箇所にあると片方だけ緑になる**ので共有モジュールを使う。
        # 揃えないと、同じ量に対して**2 つの公式な数**ができる——実際、揃える前は
        # `skill-metrics.py` が 69、こちらが 70 を報告していた（`SKILL.md` の bash 例の
        # コメントに 1 個ある分）。`strip_fences` は**行数を保って空行に置き換える**ので、
        # 行番号はずれない。
        stripped = strip_fences(path.read_text(encoding="utf-8")).splitlines()
        for lineno, line in enumerate(stripped, 1):
            if GENERATED_BEGIN in line:
                in_generated = True
            elif GENERATED_END in line:
                in_generated = False
            if MARKER not in line or in_generated:
                continue
            # バッククォートに囲まれた分を取り除いてから、まだ残っているかを見る。
            # **「1 つでも引用されていれば見逃す」ではない**——同じ行に引用と素の
            # マーカーが混在したら、素のほうを捕まえる必要がある。
            if MARKER in QUOTED.sub("", line):
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
    # 食い違い、**同じ量に 2 つの公式な数**ができる。
    count = strip_fences((root / ORIGIN).read_text(encoding="utf-8")).count(MARKER)
    print(f"必須マーカーの検査: 問題なし"
          f"（{total} 件の Markdown を検査。原本に {count} 個）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
