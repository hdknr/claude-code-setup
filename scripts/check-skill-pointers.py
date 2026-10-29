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
`prompts/*.md`）と、**プラグイン直下の Markdown**（`agents/*.md` と `references/*.md`。#332）に
現れる **`references/…` `prompts/…` `scripts/…` という形の相対パス**を拾い、
**スキルのディレクトリ（プラグイン直下のファイルならプラグインの根）からの相対で実在するか**を確かめる。
あわせて**散文の指し先**（`上の「X」` と `` `references/x.md` の「X」 ``・`` `x.md` の「X」 ``）の X が、
**指したファイルの本文にあるか**を確かめる（#205・#541）。

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
  ——**移した先を名指しする書き方**である。**拾うのはスキルの中とプラグイン直下の Markdown だけ**
  （`CLAUDE.md` の「X」は対象リポジトリのものを指している）。
- **`手順 N` を挟んだ形（`` `SKILL.md` 手順 4 の「X」 ``）も拾うこと**——
  `references/` から `SKILL.md` へ戻る指し先はこの形で書く（#205 の 2 パス目の `/code-review`）。
- **指し先そのものの文字列は数えないこと**——X は指し先の中に必ず書いてあるので、
  **数えると、どこも指していない指し先が自分を見つけて緑になる。**
- **移した先の名指しの文字列も数えないこと**——`下の「X」` の X が、同じファイルの
  `` `references/x.md` の「X」 `` の中にしか無ければ、それは本文に無い。
- **指した先の照合でも、そこの指し先の文字列は数えないこと**——移した先が X を
  **元のファイルへの指し先の中にしか**持っていなければ、項はどこにも無い。
- **『』と「」の違いを同一視すること**——**指し先は入れ子を『』で書き、本文は「」で書く。**
  寄せないと正しい指し先が全部落ちる。
- **太字の違いを同一視すること**——本文は項の一部だけを `**` で囲む。
- **バッククォートの違いを同一視すること**——本文はコマンド名を囲み、指し先は囲まないことがある。
- **空白（改行を含む）の違いを同一視すること**——本文は 1 行の幅で折り返す。
- **プラグイン直下の `agents/*.md` と `references/*.md` も見ること**（#332）——spec-loop は
  判定役の定義と共有の決まりをここに置く。**見ないと、そこの指し先がすべて機械の外にある**
  （#329 の 2 パス目の `/code-review` が、節の名前を 3 つ壊しても緑のままだと実測で示した）。
- **プラグイン直下のファイルの指し先は、プラグインの根から解決すること**——
  `agents/red-team.md` の `references/spec-scope.md` は、プラグイン直下の `references/` を指している。
- **`../` で始まる移した先の名指し（`` `../../references/x.md` の「X」 ``）も拾うこと**（#332）——
  **スキルから共有の決まりの節を指す書き方である。** 拾わないと、パスの実在は見ても節の名前は見ない。
- **`../` の後ろに名前の付いたディレクトリを通る移した先の名指し（`` `../cruise/SKILL.md` の「X」 ``
  `` `../dev-loop/references/x.md` の「X」 ``）も拾うこと**（#503）——**同じプラグインの隣のスキルの節を指す書き方である。**
  `../` の後ろを `references/`・`prompts/` に限ると、パスの実在は見ても節の名前は見ない
  （#484 の 2 パス目の `/code-review` が、cruise の見出しを書き換えても緑のままだと実測で示した）。
- **ディレクトリの付かないファイル名の移した先の名指し（`` `qa-csv.md` の「X」 ``）も拾うこと**（#541）——
  **同じディレクトリの決まりを指す書き方である**（spec-loop のプラグイン直下の `references/` が多く使う）。
  拾わないと、指した先の見出しを書き換えても緑のままだった（#503 の 2 パス目の `/code-review`）。
- **ファイル名だけの指し先は、書いたファイルと同じディレクトリから解決すること**——スキルの
  `references/r.md` の `` `s.md` `` は `references/s.md` を指す。スキルのディレクトリ（プラグイン直下ならプラグインの根）から
  解決すると、`references/` の中の指し先がどれも「無い」になって照合されない。**`` `SKILL.md` `` はこれまでどおりスキルのディレクトリから解決する。**
- **ほかの持ち主を名指しした指し先は解決しないこと**——`` dev-loop の `references/spec-gap.md` ``
  `` dev-loop のスキルの `scripts/x.py` `` `` このリポジトリの `scripts/x.py` `` は、
  **このプラグインのファイルではない**。解決すると、正しい記述なのに落ちる。
- **自分の名前や、プラグインでない名前の名指しは解決すること**——`` spec-loop の `references/x.md` ``
  （spec-loop の中で）は自分のファイルである。**名指しの免除はプラグインのディレクトリ名と
  「このリポジトリ」に限る**（限らないと、`の` で終わる語の後ろの指し先がすべて免除される）。
- **「X」の照合でも、ほかの持ち主を名指しした指し先は照合しないこと**——
  `` dev-loop の `references/spec-gap.md` の「X」 `` の X は dev-loop のファイルにある。
- **名指しは同じ行だけを見ること**——前の行の `dev-loop の` で、次の行の指し先を免除しない
  （囲まれた指し先と「X」の照合で揃える）。
- **プラグイン名は文字どおりに比べること**——大文字小文字を区別しない FS でも、
  `Spec-loop の` を `spec-loop` とは読まない（読むと、OS で結果が変わる）。
- **名前の前が区切りであること**——`foo/dev-loop の` `foo.dev-loop の` はプラグインの名指しではない。
- **名前の直前が日本語の文字でも、名指しと読むこと**——`本体はdev-loop の` も名指しである
  （区切りを `\w` で書くと、日本語の文字が区切りでなくなる。#332 の 2 パス目）。
- **名指しは指し先の直前だけを見ること**——`` dev-loop の規定と同じく、自分の `references/x.md` ``
  の `references/x.md` は自分のファイルである（同じ行の前のほうの名指しで免除しない）。

守らない:

- **指し先に「指すと書いた内容」があるか**——**実在するかまで**である
  （`check-site-links.py` と同じ限界）。
- **パスの形をしていない、ファイルへの指し先**——**バッククォートで囲まれていない**
  「参照ファイル」のような書き方は拾えない。**ファイルを指すなら、パスの形で囲んで書く**
  （項を指す散文の指し先は、上の「守る」のとおり `上の「X」` の形だけ拾う）。
- **散文の指し先の、X を「」で書いていない形**——「上項」「直前の項」
  「上の `EnterWorktree` の項」は**名指ししていないので、照合する相手が無い。**
  **項を指すなら「」で文言を引く**（#205 で手順 4 の指し先をこの形に直した）。
- **散文の指し先の向き**——「上の」と書いて実物が下にあっても落とさない。
  **見るのはファイルの中にあるかまで。**
- **X が項の見出しか、本文の一部か**——**本文のどこかに同じ文言があれば緑になる。**
  **言い換えた X は落ちる**（文言どおりに引くこと）。
- **プラグインの外から張られた指し先**——`CLAUDE.md` や設計ドキュメントが
  スキルの中を指しても、ここでは見ていない。
- **起動行の中の、名前の付いたディレクトリを通る `../`**——起動行は
  `…/scripts/x` の形しか拾わないので、`python3 ../../../dev-loop/scripts/x.py` は
  **`scripts/x.py` としてスキルからの相対で解決される**（無ければ「実在しない」で落ちるが、
  **同じ名前がスキルの中にあると緑になる**）。
- **ほかの持ち主を名指しした指し先が、その持ち主のところに実在するか**——解決しないだけで、
  **名指しした先（dev-loop のスキル・このリポジトリ）は見ない。**
- **名指しが同じ行に無い形**——免除を判定するのは**指し先の直前の文字列**である。
  `dev-loop の` ／ `` `references/x.md` `` と行をまたぐと、囲まれた指し先は免除されない
  （落ちる側に倒れる）。
- **名指しの免除は、囲まれた指し先（`references/…` `prompts/…` `scripts/…`）と「X」の照合だけ**——
  `../` で始まる指し先とフェンスの中の起動行は、名指しがあっても解決する（落ちる側に倒れる）。
- **プラグイン直下のファイルから、自分のスキルの中を指す形**——`` <自分の名前> のスキルの `scripts/x.py` ``
  は自分の名前なので免除されず、プラグインの根から解決されて落ちる（落ちる側に倒れる）。
- **プラグイン直下のファイルからの `` `SKILL.md` の「X」 ``**——プラグインの根に `SKILL.md` は無く、
  どのスキルを指すかが決まらないので照合しない。
- **ファイル名だけの指し先が、書いたファイルと同じディレクトリに無いとき**——**照合せず、実在も見ない**（#541）。
  **別のディレクトリを指していることがある**——cruise の `SKILL.md` の `` `resume.md` `` は dev-loop スキルの `references/` を、
  dev-loop の `references/spec-gap.md` の `` `qa-csv.md` `` は spec-loop のプラグインの `references/` を指す。
  **どこを指すかが字面から決まらないので、照合する相手が無い。** 照合させたいなら `` `../dev-loop/references/resume.md` `` のようにパスで書く。
  **同じディレクトリのファイルを改名すると、その指し先も照合されなくなる**（落ちる側に倒れない）。
- **使われていないファイル**——**指されていない `references/*.md` があっても落とさない**
  （置いてすぐ指す周と、先に置く周を区別できないため）。
- **名指しの無い、スキルの `scripts/` と対象リポジトリの `scripts/` の区別**——**付かない。**
  **`dev-loop` は両方に言及する**（対象リポジトリの `check-all.py` を走らせる案内がある）。
  **名指しの無い `scripts/…` はスキル（プラグイン直下ならプラグインの根）からの相対で解決する**ので、
  **対象リポジトリのパスを名指し無しで囲んで書くと、正しい記述なのに落ちる。**
  **囲むなら `` このリポジトリの `scripts/x.py` `` と名指しする**（#332。上の「守る」）。
  **名指しの無い箇所は、いまは囲み方でたまたま避けている**——**これは設計ではなく偶然である**
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


def targets_in(root: pathlib.Path):
    """見るファイルを (解決の起点, プラグイン, ファイル) で返す。

    **スキルの中**（`SKILL.md`・`references/*.md`・`prompts/*.md`）はスキルのディレクトリから、
    **プラグイン直下**（`agents/*.md`・`references/*.md`）はプラグインの根から解決する
    ——判定役の定義と共有の決まりは `references/x.md` をプラグインの根からの相対で書く（#332）。
    """
    for skill in skill_dirs(root):
        plugin = skill.parent.parent
        yield skill, plugin, skill / "SKILL.md"
        for sub in ("references", "prompts"):
            for path in sorted((skill / sub).glob("*.md")):
                yield skill, plugin, path
    for plugin in sorted(p for p in (root / "plugins").iterdir() if p.is_dir()):
        for sub in ("agents", "references"):
            for path in sorted((plugin / sub).glob("*.md")):
                yield plugin, plugin, path


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
# **スキルの中とプラグイン直下の Markdown だけ**を拾う（`CLAUDE.md` は対象リポジトリのものを指している）。
# **`../` で始まる形は、後ろを `references/`・`prompts/` に限らない**（#503）——限ると、
# `` `../cruise/SKILL.md` の「X」 `` のように隣のスキルを通る指し先の X を照合しない（`PARENT` と同じ理由）。
# **ディレクトリの付かないファイル名も拾う**（#541）——`` `qa-csv.md` の「X」 `` は、書いたファイルと同じディレクトリの
# ファイルを指す（解決は `prose_pointers_in`）。
XREF = re.compile(
    r"`(SKILL\.md|(?:references|prompts)/[\w.-]+\.md|[\w.-]+\.md|(?:\.\./)+[\w.-][\w./-]*\.md)`"
    r"\s*(?:手順\s*\d+\s*)?" + NO + QUOTED)
# **ほかの持ち主を名指しした指し先**（`dev-loop の` `dev-loop のスキルの` `このリポジトリの`）。
# **このプラグインからの相対では解決しない**——spec-loop のプラグイン直下の決まりは、
# dev-loop やこのリポジトリのファイルを名前で指す（#332）。名前はプラグインのディレクトリ名に限る。
# **名前の前は区切り**——`foo/dev-loop の` の `dev-loop` を名前と読まない（読むと、プラグインでない名指しが免除される）。
# **区切りを `\w` で書かない**——`\w` は日本語の文字も含むので、`本体はdev-loop の` が名指しでなくなる。
# **末尾の `$` を外さない**——外すと、同じ行の前のほうの名指しで、後ろの自分の指し先が免除される。
OWNER = re.compile(r"(?:このリポジトリ|(?<![A-Za-z0-9_/.-])([A-Za-z0-9_-]+)(?:\s*のスキル)?)\s*の\s*$")


def owned_elsewhere(before: str, plugin: pathlib.Path) -> bool:
    """指し先の直前の文字列 `before` が、ほかの持ち主を名指ししているか。"""
    m = OWNER.search(before)
    if not m:
        return False
    if m.group(1) is None:
        return True  # このリポジトリ
    name = m.group(1)
    # **`(plugin.parent / name).is_dir()` にしない**——大文字小文字を区別しない FS（macOS）では
    # `Spec-loop` が `spec-loop` に当たり、自分の名前が「ほかの持ち主」になる。名前は文字どおりに比べる。
    names = {p.name for p in plugin.parent.iterdir() if p.is_dir()}
    return name != plugin.name and name in names


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


def prose_pointers_in(path: pathlib.Path, skill: pathlib.Path, plugin: pathlib.Path):
    """散文の指し先を (行番号, 説明, X が指した先にあるか) で返す。

    **フェンスの中は見ない**——コード例の中の書き方は主張ではない。
    `skill` は指し先を解決する起点（プラグイン直下のファイルならプラグインの根）。
    """
    raw = path.read_text(encoding="utf-8")
    prose = strip_fences(raw)
    own = body_without_pointers(raw)
    for m in PROSE.finditer(prose):
        lineno = prose.count("\n", 0, m.start()) + 1
        yield (lineno, f"{m.group(0)}（このファイルに無い）",
               normalize(m.group(1)) in own)
    for m in XREF.finditer(prose):
        # **名指しを見るのは同じ行だけ**——囲まれた指し先（`pointers_in`）と揃える。
        # 前の行まで見ると、行をまたいだ名指しが免除される（docstring は「落ちる側」と書いている）。
        line_start = prose.rfind("\n", 0, m.start()) + 1
        if owned_elsewhere(prose[line_start:m.start()], plugin):
            continue
        rel = m.group(1)
        # **ファイル名だけの指し先は、書いたファイルと同じディレクトリから解決する**（#541）。
        # **そこに無ければ照合しない**——別のディレクトリ・別のプラグインを指していることがあり、どこかが決まらない
        # （docstring の「守らない」）。`SKILL.md` はこれまでどおりスキルのディレクトリから。
        target = (path.parent if "/" not in rel and rel != "SKILL.md" else skill) / rel
        if not target.is_file():
            continue  # 実在しないことは囲まれた指し先の検査が言う（ファイル名だけの形は見ない）
        lineno = prose.count("\n", 0, m.start()) + 1
        yield (lineno, f"{m.group(0)}（{m.group(1)} に無い）",
               normalize(m.group(2)) in body_without_pointers(
                   target.read_text(encoding="utf-8")))


def pointers_in(path: pathlib.Path, plugin: pathlib.Path):
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
            if not owned_elsewhere(line[:m.start()], plugin):
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
    for base, plugin, path in targets_in(root):
        files += 1
        for lineno, rel in pointers_in(path, plugin):
            checked += 1
            if not (base / rel).exists():
                problems.append((path.relative_to(root), lineno, rel))
            elif (leaves_plugin(base, plugin, rel)
                  or not (base / rel).resolve().is_relative_to(plugin.resolve())):
                problems.append((path.relative_to(root), lineno, f"{rel}（プラグインの外）"))
        for lineno, what, found in prose_pointers_in(path, base, plugin):
            checked += 1
            if not found:
                problems.append((path.relative_to(root), lineno, what))

    if problems:
        print("ERROR: プラグインの中の指し先が実在しません:", file=sys.stderr)
        for rel_path, lineno, target in problems:
            print(f"ERROR:   {rel_path}:{lineno} → {target}", file=sys.stderr)
        print("ERROR:", file=sys.stderr)
        print("ERROR: **指し先はスキルのディレクトリからの相対で書く。**"
              "プラグイン直下の共有物は `../../` で指す。プラグインの外は指せない。", file=sys.stderr)
        print("ERROR: プラグイン直下の `agents/*.md` と `references/*.md` は、"
              "プラグインの根からの相対で書く（#332）。", file=sys.stderr)
        print("ERROR: 名前を変えたなら、指している側も直すこと（#136）。", file=sys.stderr)
        print("ERROR: 散文の指し先（上の「X」・`references/x.md` の「X」）は、"
              "X を指した先の文言どおりに書く。節を移したなら、移した先を名指しする（#205）。",
              file=sys.stderr)
        return 1

    print(f"プラグインの中の指し先の検査: 問題なし"
          f"（{files} ファイル / 指し先 {checked} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
