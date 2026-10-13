#!/usr/bin/env python3
r"""スキルの中の指し先（`references/…` `prompts/…` `scripts/…`）が実在するかを見る。

    python3 scripts/check-skill-pointers.py

なぜ必要か（#136）: **`SKILL.md` を大きく圧縮した設計は、本文に書いた
いくつかの相対パスだけで繋がっている。**
**圧縮率は書かない**——**手で書いた派生の数字は次の編集で古くなる**
（実際、`docs/plans/issue-136.md` の同じ数字を 1 度古くした）。 条件が立ったときに
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
あわせて**散文の指し先**（`上の「X」` と `` `references/x.md` の「X」 ``）の X が、
**指したファイルの本文にあるか**を確かめる（#205）。

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
- **`../` で始まる指し先も拾うこと**——**複数のスキルが共有するものはプラグイン直下に
  置く**（spec-loop の `references/` と `scripts/`。#216）。スキルからは
  `../../references/qa-csv.md` の形で指すので、**ここを拾わないと、
  共有の決まりへの指し先が 1 つも検査されない。**
  **`../` の後ろは `references/` などに限らない**——`../../../dev-loop/…` のように
  **名前の付いたディレクトリを通って外へ出る形も拾う**（限ると、外へ出る指し先ほど
  見えなくなる。#216 の `/code-review` が実測で示した）。
- **`../` で始まる指し先が、そのプラグインのディレクトリの中に収まること**——
  **外へ出る指し先は、実在しても落とす。** プラグインはキャッシュに単独で降りるので、
  **プラグインの外はインストール先に無い**（このリポジトリの `scripts/` を指した
  つもりの記述が、ここで緑になってはならない）。
- **プラグインの境界は `plugins/<name>/` であって `plugins/` ではないこと**——
  **隣のプラグインを指したら、実在しても落とす**（隣のプラグインもインストール先には
  無い。境界を 1 段上げても、リポジトリの直下まで出る試料だけでは緑のままだった）。
- **途中で 1 度でもプラグインの外へ出た指し先は、戻ってきても落とすこと**——
  `../../../spec-loop/references/…` は**リポジトリでは自分のプラグインに戻って実在する**が、
  **インストール先ではプラグインの上のディレクトリの名前が違う**（`<market>/spec-loop/<版>/`）
  ので実在しない。**行き着く先だけを見ると緑になる**（#216 の 2 パス目の `/code-review` が
  実測で示した）。**だから字面で 1 段ずつ辿り、プラグインの根より上に出た時点で落とす。**
- **symlink の先がプラグインの外なら、字面が中に収まっていても落とすこと**——
  `references/x.md` が隣のプラグインへの symlink だと、**字面を辿るだけでは外へ出ない**。
  **字面の検査と `resolve()` の検査は別の形を捕まえる**ので、片方で他方を代えない
  （**一度 2 つを 1 本の変異で同時に外しており、`resolve()` 側だけを外しても
  どのテストも落ちなかった**。#230）。
- **散文の指し先 `上の「X」` `下の「X」` の X が、同じファイルにあること**（#205）——
  **節を `references/` へ移したあと、`SKILL.md` に残った「下の『改名の…』項」が
  どこも指していなかった。** パスの形をしていないので、上の検査はどれも見ていなかった。
- **`の` と `「` の間で折り返した散文の指し先も拾うこと**——**本文は 1 行の幅で折り返す**
  ので、`下の` ／ `「X」` が 2 行に分かれる。**拾わないと、直したはずの指し先が
  機械の外に残る**（#205 の 1 パス目の `/code-review` が、S1・S5・S6 で実測で示した）。
- **散文の指し先も、フェンスの中は見ないこと**——コード例の中の書き方は主張ではない
  （囲まれた相対パスと同じ）。
- **`` `references/x.md` の「X」`` `` `SKILL.md` 手順 4 の「X」`` の X が、指したファイルにあること**
  ——**移した先を名指しする書き方**である。**拾うのはスキルの中の Markdown だけ**
  （`CLAUDE.md` の「X」は対象リポジトリのものを指している）。
- **指し先そのものの文字列は数えないこと**——X は指し先の中に必ず書いてあるので、
  **数えると、どこも指していない指し先が自分を見つけて緑になる。**
- **『』と「」、太字・バッククォート・空白（改行を含む）の違いを同一視すること**——
  **指し先は入れ子を『』で書き、本文は「」で書く。** 寄せないと正しい指し先が全部落ちる。

守らない:

- **指し先に「指すと書いた内容」があるか**——**実在するかまで**である
  （`check-site-links.py` と同じ限界）。
- **散文の中の指し先**——**バッククォートで囲まれていない**「参照ファイル」のような
  書き方は拾えない。**拾うのは、パスの形をしたものだけ。**
- **散文の指し先の、X を「」で書いていない形**——「上項」「直前の項」
  「上の `EnterWorktree` の項」は**名指ししていないので、照合する相手が無い。**
  **項を指すなら「」で文言を引く**（#205 で手順 4 の指し先をこの形に直した）。
- **散文の指し先の向き**——「上の」と書いて実物が下にあっても落とさない。
  **見るのはファイルの中にあるかまで。**
- **X が項の見出しか、本文の一部か**——**本文のどこかに同じ文言があれば緑になる。**
  **言い換えた X は落ちる**（文言どおりに引くこと）。
- **`SKILL.md` の外から張られた指し先**——`CLAUDE.md` や設計ドキュメントが
  スキルの中を指しても、ここでは見ていない。
- **起動行の中の、名前の付いたディレクトリを通る `../`**——起動行は
  `…/scripts/x` の形しか拾わないので、`python3 ../../../dev-loop/scripts/x.py` は
  **`scripts/x.py` としてスキルからの相対で解決される**（無ければ「実在しない」で落ちるが、
  **同じ名前がスキルの中にあると緑になる**）。
- **使われていないファイル**——**指されていない `references/*.md` があっても落とさない**
  （置いてすぐ指す周と、先に置く周を区別できないため）。
- **スキルの `scripts/` と、対象リポジトリの `scripts/` の区別**——**付かない。**
  **`dev-loop` は両方に言及する**（対象リポジトリの `check-all.py` を走らせる案内がある）。
  **すべての `scripts/…` をスキルからの相対で解決する**ので、
  **対象リポジトリのパスを囲んで書くと、正しい記述なのに落ちる。**
  **いまは囲み方でたまたま避けている**——**これは設計ではなく偶然である**
  （3 パス目の `/code-review` が指摘）。
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from markdown_fences import strip_fences  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# `` `references/resume.md` `` のように囲まれた相対パスだけを拾う。
POINTER = re.compile(r"`((?:references|prompts|scripts)/[\w./-]+)`")
# `../` で始まる囲まれた相対パス（プラグイン直下の共有物を指す形。#216）。
# **`../` の後ろを `references/` などに限らない**——限ると、`../../../dev-loop/…` のように
# **外へ出る指し先ほど拾えない**。
PARENT = re.compile(r"`((?:\.\./)+[\w.-][\w./-]*)`")


def leaves_plugin(skill: pathlib.Path, plugin: pathlib.Path, rel: str) -> bool:
    """`rel` を `skill` から字面で 1 段ずつ辿り、途中で 1 度でも `plugin` の外へ出たら真。

    **行き着く先だけを見ない**——外へ出て名前で戻る形（`../../../spec-loop/…`）は、
    行き着く先がプラグインの中でもインストール先では実在しない。
    **symlink は辿らない**（字面だけ）。symlink の先が外かどうかは、呼ぶ側が
    `resolve()` で別に見る。
    """
    depth = len(skill.relative_to(plugin).parts)
    for part in pathlib.PurePosixPath(rel).parts:
        if part == "..":
            depth -= 1
            if depth < 0:
                return True
        elif part != ".":
            depth += 1
    return False


def skill_dirs(root: pathlib.Path):
    """`plugins/*/skills/*/` を返す。**スキルを名前で固定しない。**"""
    for plugin in sorted((root / "plugins").glob("*")):
        for skill in sorted((plugin / "skills").glob("*")):
            if (skill / "SKILL.md").is_file():
                yield skill


# **フェンスの中の起動行**。`bash …/scripts/x.sh` `python3 …/scripts/x.py` の形。
# **ここを見ないと、いちばん壊れて困る指し先を 1 つも検査しない**
# ——**実際の起動はすべてコードブロックの中にある**（`/code-review` が指摘。#136）。
INVOCATION = re.compile(r"(?:bash|sh|python3?)\s+.*?((?:\.\./)*scripts/[\w.-]+)")
# **`\S*?` にしない。** 起動行のパスには `<このスキルの base ディレクトリ>` のような
# **空白を含む占位子**が挟まる。**`\S*?` では跨げず、1 件も拾わなかった**（実測）。

# **散文の指し先**（#205）。「」の中に『』や「」を 1 段だけ入れ子にできる。
# **行をまたいで書かれる**ので、行ごとではなく本文全体に当てる。
# **`の` と `「` の間の改行も跨ぐ**（`\s*`）——**跨がないと、`の` で折り返した指し先が
# 1 件も拾われない**（#205 の 1 パス目の `/code-review`。直したはずの S1・S5・S6 がそうだった）。
QUOTED = r"「((?:[^「」]|「[^「」]*」)+)」"
NO = r"の\s*"
# `上の「X」` / `下の「X」` —— **X は同じファイルの中にあるはず。**
PROSE = re.compile(r"[上下]" + NO + QUOTED)
# `` `references/resume.md` の「X」 `` / `` `SKILL.md` 手順 4 の「X」 `` —— X は指したファイルにあるはず。
# **スキルの中の Markdown だけ**を拾う（`CLAUDE.md` は対象リポジトリのものを指している）。
XREF = re.compile(
    r"`(SKILL\.md|(?:references|prompts)/[\w.-]+\.md)`\s*(?:手順\s*\d+\s*)?" + NO + QUOTED)


def normalize(text: str) -> str:
    """太字・バッククォート・空白（改行を含む）を外し、『』を「」に寄せる。

    **指し先は『』で入れ子を書き、本文は「」で書く**（「」の中に「」を書けないため）。
    **寄せないと、正しい指し先が全部落ちる。**
    """
    return re.sub(r"[*`\s]", "", text).replace("『", "「").replace("』", "」")


def body_without_pointers(text: str) -> str:
    """指し先そのものを消した本文（正規化済み）。

    **消さないと、指し先が自分自身を見つけて緑になる**——X は指し先の中に必ず書いてある。
    """
    return normalize(XREF.sub("", PROSE.sub("", text)))


def prose_pointers_in(path: pathlib.Path, skill: pathlib.Path):
    """散文の指し先を (行番号, 説明, X が指した先にあるか) で返す。

    **フェンスの中は見ない**——コード例の中の書き方は主張ではない。
    """
    raw = path.read_text(encoding="utf-8")
    prose = strip_fences(raw)
    own = body_without_pointers(raw)
    for m in PROSE.finditer(prose):
        lineno = prose.count("\n", 0, m.start()) + 1
        yield (lineno, f"{m.group(0)}（このファイルに無い）",
               normalize(m.group(1)) in own)
    for m in XREF.finditer(prose):
        target = skill / m.group(1)
        if not target.is_file():
            continue  # 実在しないことは囲まれた指し先の検査が言う
        lineno = prose.count("\n", 0, m.start()) + 1
        yield (lineno, f"{m.group(0)}（{m.group(1)} に無い）",
               normalize(m.group(2)) in body_without_pointers(
                   target.read_text(encoding="utf-8")))


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
        for m in PARENT.finditer(line):
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
        plugin = skill.parent.parent
        for path in targets:
            files += 1
            for lineno, rel in pointers_in(path):
                checked += 1
                if not (skill / rel).exists():
                    problems.append((path.relative_to(root), lineno, rel))
                elif (leaves_plugin(skill, plugin, rel)
                      or not (skill / rel).resolve().is_relative_to(plugin.resolve())):
                    problems.append((path.relative_to(root), lineno, f"{rel}（プラグインの外）"))
            for lineno, what, found in prose_pointers_in(path, skill):
                checked += 1
                if not found:
                    problems.append((path.relative_to(root), lineno, what))

    if problems:
        print("ERROR: スキルの中の指し先が実在しません:", file=sys.stderr)
        for rel_path, lineno, target in problems:
            print(f"ERROR:   {rel_path}:{lineno} → {target}", file=sys.stderr)
        print("ERROR:", file=sys.stderr)
        print("ERROR: **指し先はスキルのディレクトリからの相対で書く。**"
              "プラグイン直下の共有物は `../../` で指す。プラグインの外は指せない。", file=sys.stderr)
        print("ERROR: 名前を変えたなら、指している側も直すこと（#136）。", file=sys.stderr)
        print("ERROR: 散文の指し先（上の「X」・`references/x.md` の「X」）は、"
              "X を指した先の文言どおりに書く。節を移したなら、移した先を名指しする（#205）。",
              file=sys.stderr)
        return 1

    print(f"スキルの中の指し先の検査: 問題なし"
          f"（{files} ファイル / 指し先 {checked} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
