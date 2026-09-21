#!/usr/bin/env python3
r"""同じファイルの中で、同じ語句に違う数が付いていないかを検出する。

    python3 scripts/check-duplicate-counts.py

なぜ必要か（#138）: `CLAUDE.md` は**「〇〇を正とする」と書け**を規約にしているが、
**同じ列挙や件数が複数箇所に書かれていることを検出する歯止めが 1 本も無かった。**

**#122 の周は、この型で 3 パス目を回せずに人間レビューへ回った。**
揃わなかった交絡の件数を `SKILL.md`・計画ファイルの複数節・スクリプトのヘッダ・
Issue のコメントに同時に書いており、**「1 つ」→「2 つ」→「3 つ」と直すたびに、
直し残した写しが次の関門に見つかった。** 2 つの関門の指摘のうち **6 件がこの型**だった。

## 何を見るか

**同じファイルの中で、同じ語句に違う数が付いている**ところを探す。

    155 行: **揃わなかったものが 1 つ**: **git の版**（…）
    175 行: **揃わなかったものが 2 つある**（一度「git の版だけ」と書いて…）

**これは実際に起きた形である**（`docs/plans/issue-122.md` の `525f3e6` 時点）。
**この歯止めを当てると、その 1 コミットでちょうど 1 件発火し、修正後は止まる。**

## 何を守り、何を守らないか

守る:

- **同じファイルの中の自己矛盾**——同じ語句に違う数が付いていたら落とす。
- **強調の中の数**——`**2 つ**` のように囲まれていても見る（このリポジトリの地の文は
  強調だらけで、**見ないと実物にほとんど当たらない**）。
- **フェンスの中を数えない**——コード例の中の数は文章の主張ではない。
- **免除は語句を名指しさせる**——`dup-counts-ok: <語句>` をファイルに書くと、
  **その語句だけ**免除される。**黙ってファイル全体を免除しない。**
- **免除もフェンスの外だけを拾う**——**コード例として見せた免除は効かない。**
  **数のほうはフェンスを剥がしているのに、免除だけ剥がしていなかった**
  （`/code-review` が指摘し、**その直しに回帰テストが無いと 2 パス目の Verifier に
  重ねて反証された**）。

守らない:

- **ファイルをまたぐ重複**——**言い回しが違うと当たらない。** 実際 #122 では、
  計画ファイルの「揃わなかったもの」とスクリプトの「揃っていないもの」が
  同じことを述べていたが、**この検査は別物として扱う。**
- **表の行数とずれた範囲参照**（`P1〜P9` と書いてあるのに表が 10 行ある形）。
  **一度これも規則にしようとして、やめた**——**「P10 は P1〜P9 には無かった」という
  過去についての正しい記述と、文面で区別できない。** 実測で、現在の main に
  **3 件当たって 3 件とも誤検出**だった。**再発明しないこと。**
- **語句が違う同じ主張**——「歯止めが 8 本」と「検査が 21 個」は当たらない。
- **数を伴わない重複**——列挙そのものが 2 箇所にある形は見ていない。
- **これは「重複が無い」の証明ではない。** **「同じ語句に違う数が付いた」という、
  実際に起きた 1 つの形の検査**である。

## この docstring 自身が免除されている

**上の実例は、まさにこの検査が捕まえる形そのもの**なので、**書いた瞬間に自分で落ちた。**
**免除の仕組みの実演として、そのまま残してある。**

dup-counts-ok: 揃わなかったもの
"""

import pathlib
import re
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from markdown_fences import strip_fences  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "site", ".venv", "node_modules", "__pycache__", ".claude"}
SUFFIXES = {".md", ".py", ".sh", ".json", ".yml", ".yaml", ".toml"}

# 「<語句>が N つ」。**語句は 2〜12 字**（長すぎると文をまたぐ）。
# **強調の `**` は落としてから当てる**ので、ここでは見なくてよい。
COUNTED = re.compile(r"([^\s。、|（）`「」]{2,12}?)\s*(?:が|は)\s*(\d+)\s*(つ|件|個|本|箇所)")

# 免除。**語句を名指しさせる。**
EXEMPT = re.compile(r"dup-counts-ok:\s*(\S+)")


def scan(text: str) -> dict:
    """(語句, 単位) → {数: [(行, 断片)]} のうち、**数が 2 種以上あるもの**を返す。"""
    stripped = strip_fences(text)
    # **免除もフェンスを剥がしてから拾う。** 生の本文から拾うと、
    # **コード例として見せた免除がファイル全体に効いてしまう**
    # ——**「黙ってファイル全体を免除しない」という約束に反する。**
    # **数のほうはフェンスを剥がしているのに、免除だけ剥がしていなかった**
    # （`/code-review` が指摘。#136）。
    exempt = set(EXEMPT.findall(stripped))
    found = defaultdict(lambda: defaultdict(list))
    for lineno, line in enumerate(stripped.split("\n"), 1):
        plain = line.replace("**", "")
        for m in COUNTED.finditer(plain):
            phrase, number, unit = m.group(1), m.group(2), m.group(3)
            if phrase in exempt:
                continue
            found[(phrase, unit)][number].append((lineno, m.group(0)))
    return {key: nums for key, nums in found.items() if len(nums) > 1}


def targets(root: pathlib.Path):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file() and path.suffix in SUFFIXES:
            yield rel, path


def main(argv=None) -> int:
    root = pathlib.Path(argv[0]) if argv else REPO_ROOT
    problems = []
    checked = 0
    for rel, path in targets(root):
        checked += 1
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for (phrase, unit), numbers in scan(text).items():
            problems.append((rel, phrase, unit, numbers))

    if problems:
        print("ERROR: 同じファイルの中で、同じ語句に違う数が付いています:", file=sys.stderr)
        for rel, phrase, unit, numbers in problems:
            print(f"ERROR:   {rel}: 「{phrase}…{unit}」に {sorted(numbers)} が混在", file=sys.stderr)
            for number in sorted(numbers):
                lineno, fragment = numbers[number][0]
                print(f"ERROR:     {lineno}: {fragment}", file=sys.stderr)
        print("ERROR:", file=sys.stderr)
        print("ERROR: 件数は 1 箇所にだけ書き、残りはそこを指すこと（#138）。", file=sys.stderr)
        print("ERROR: 数え方が違うだけで両方正しいなら、"
              "`dup-counts-ok: <語句>` をそのファイルに書いて理由を添えること。", file=sys.stderr)
        return 1

    print(f"件数の食い違いの検査: 問題なし（{checked} ファイルを走査）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
