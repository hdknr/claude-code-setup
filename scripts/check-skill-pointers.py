#!/usr/bin/env python3
r"""スキルの中の指し先（`references/…` `prompts/…` `scripts/…`）が実在するかを見る。

    python3 scripts/check-skill-pointers.py

なぜ必要か（#136）: **`SKILL.md` を 29% 圧縮した設計は、本文に書いた
いくつかの相対パスだけで繋がっている。** 条件が立ったときに
`references/resume.md` を読め、委譲文は `prompts/verifier.md` を使え、
探索は `scripts/find-cycle.py` を走らせろ——**どれも文字列である。**

**1 文字ずれても、誰も気づかない。** `check-site-links.py` は
**公開サイトへの絶対 URL しか解決しない**ので、この種の指し先は見ていなかった。
**`CLAUDE.md` が「『〇〇を正とする』と書け。リンクの形で書けば機械でも見られる」と
言っているのに、スキルの中の指し先だけが機械の外にあった**
（**この周の `/code-review` が指摘した**）。

## 何を見るか

**スキルのディレクトリの中の Markdown**（`SKILL.md` と `references/*.md`、
`prompts/*.md`）に現れる **`references/…` `prompts/…` `scripts/…` という形の相対パス**を
拾い、**そのスキルのディレクトリからの相対で実在するか**を確かめる。

## 何を守り、何を守らないか

守る:

- **指し先のファイルが実在すること**——無ければ落とす。
- **バッククォートで囲まれた指し先を拾うこと**——このリポジトリの書き方である。
- **フェンスの中は見ないこと**（囲まれた相対パスについて）——コード例の中のパスは主張ではない。
- **フェンスの中の起動行は見ること**——`bash …/scripts/x.sh` の形。
  **実際の起動はすべてコードブロックの中にあり、そこが壊れると手順が動かない。**
  **一度ここを見ておらず、`prepare-worktree.sh` は「スキルのどこからも指されていない」
  状態だった**（`/code-review` が指摘）。
- **スキルを固定しないこと**——`plugins/*/skills/*/` を走査するので、
  **プラグインが増えても手で足さなくてよい。**

守らない:

- **指し先に「指すと書いた内容」があるか**——**実在するかまで**である
  （`check-site-links.py` と同じ限界）。
- **散文の中の指し先**——**バッククォートで囲まれていない**「参照ファイル」のような
  書き方は拾えない。**拾うのは、パスの形をしたものだけ。**
- **`SKILL.md` の外から張られた指し先**——`CLAUDE.md` や設計ドキュメントが
  スキルの中を指しても、ここでは見ていない。
- **使われていないファイル**——**指されていない `references/*.md` があっても落とさない**
  （置いてすぐ指す周と、先に置く周を区別できないため）。
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from markdown_fences import strip_fences  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `` `references/resume.md` `` のように囲まれた相対パスだけを拾う。
POINTER = re.compile(r"`((?:references|prompts|scripts)/[\w./-]+)`")


def skill_dirs(root: pathlib.Path):
    """`plugins/*/skills/*/` を返す。**スキルを名前で固定しない。**"""
    for plugin in sorted((root / "plugins").glob("*")):
        for skill in sorted((plugin / "skills").glob("*")):
            if (skill / "SKILL.md").is_file():
                yield skill


# **フェンスの中の起動行**。`bash …/scripts/x.sh` `python3 …/scripts/x.py` の形。
# **ここを見ないと、いちばん壊れて困る指し先を 1 つも検査しない**
# ——**実際の起動はすべてコードブロックの中にある**（`/code-review` が指摘。#136）。
INVOCATION = re.compile(r"(?:bash|sh|python3?)\s+.*?(scripts/[\w.-]+)")
# **`\S*?` にしない。** 起動行のパスには `<このスキルの base ディレクトリ>` のような
# **空白を含む占位子**が挟まる。**`\S*?` では跨げず、1 件も拾わなかった**（実測）。


def pointers_in(path: pathlib.Path):
    """そのファイルにある指し先を (行番号, パス) で返す。

    **2 種類を拾う:**

    - **散文の中の、囲まれた相対パス**（`` `references/resume.md` `` など）。
      **フェンスの中は見ない**——コード例の中のパスは主張ではない。
    - **フェンスの中の起動行**（`bash …/scripts/x.sh`）。**こちらはフェンスの中だけを見る**
      ——**実際の起動はすべてコードブロックの中にあり、そこが壊れると手順が動かない。**
    """
    raw = path.read_text(encoding="utf-8")
    stripped = strip_fences(raw)
    for lineno, line in enumerate(stripped.split("\n"), 1):
        for m in POINTER.finditer(line):
            yield lineno, m.group(1)
    # **フェンスの中だけ**を見る（`strip_fences` は行数を保って空行にするので、
    # 素の本文と突き合わせれば「フェンスの中だった行」が分かる）。
    for lineno, (raw_line, bare) in enumerate(
            zip(raw.split("\n"), stripped.split("\n")), 1):
        if bare.strip() or not raw_line.strip():
            continue
        for m in INVOCATION.finditer(raw_line):
            yield lineno, m.group(1)


def main(argv=None) -> int:
    root = pathlib.Path(argv[0]) if argv else REPO_ROOT
    problems = []
    checked = files = 0
    for skill in skill_dirs(root):
        targets = [skill / "SKILL.md"]
        for sub in ("references", "prompts"):
            targets += sorted((skill / sub).glob("*.md"))
        for path in targets:
            files += 1
            for lineno, rel in pointers_in(path):
                checked += 1
                if not (skill / rel).exists():
                    problems.append((path.relative_to(root), lineno, rel))

    if problems:
        print("ERROR: スキルの中の指し先が実在しません:", file=sys.stderr)
        for rel_path, lineno, target in problems:
            print(f"ERROR:   {rel_path}:{lineno} → {target}", file=sys.stderr)
        print("ERROR:", file=sys.stderr)
        print("ERROR: **指し先はスキルのディレクトリからの相対で書く。**", file=sys.stderr)
        print("ERROR: 名前を変えたなら、指している側も直すこと（#136）。", file=sys.stderr)
        return 1

    print(f"スキルの中の指し先の検査: 問題なし"
          f"（{files} ファイル / 指し先 {checked} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
