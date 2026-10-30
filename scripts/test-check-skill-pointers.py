#!/usr/bin/env python3
"""`check-skill-pointers.py` の回帰テスト。

    python3 scripts/test-check-skill-pointers.py

**このテストは実環境を触らない。** 毎回テンポラリに偽のスキルツリーを作り、そこだけを
対象にする（`assert_not_real_repo` がそれを担保する）。本体は既定でこのリポジトリを
走査するので、**歯止めが無いと、テストが実リポジトリを見て通ってしまう。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**「守る」の行数と変異の数が 1 対 1 か**は、**テスト自身が数える。**

**実際に起きた欠陥を母集団に入れてある**——`references/guard-rejections.md` が
`scripts/collect-guard-rejections.py` を指していたが、**あれはリポジトリの `scripts/` に
あり、スキルの中には無い。** **この歯止めを置いた瞬間に捕まった。**
"""
import contextlib
import importlib.util
import io
import os
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "check-skill-pointers.py"

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"csp_{id(script)}", script)
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


def make_skill(root: Path, *, body: str, files: dict[str, str]) -> Path:
    skill = root / "plugins" / "demo" / "skills" / "demo"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(body, encoding="utf-8")
    for rel, text in files.items():
        p = skill / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return skill


GOOD = """# デモ

条件が立ったら `references/resume.md` を読む。
委譲文は `prompts/verifier.md` を使う。
探索は `scripts/find-cycle.py` を走らせる。
"""

BROKEN = GOOD.replace("references/resume.md", "references/typo.md")

# **フェンスの中にも囲まれた指し先を置く。** 囲んでいないと `POINTER` が拾わないので、
# **「フェンスを剥がさない」変異が殺せない**（最初そうなっていた）。
FENCED = """# デモ

```markdown
指し先の書き方の例: `references/never-exists.md`
上の「どこにも無い項」
```

本文の指し先は `references/resume.md` だけ。
"""

# **フェンスの中の起動行。** **実際の起動はすべてコードブロックの中にある**ので、
# **ここを見ないと、いちばん壊れて困る指し先を 1 つも検査しない。**
# **占位子に空白が入る**（`<このスキルの base ディレクトリ>`）ことも試料に入れてある
# ——**`\S*?` では跨げず、1 件も拾わなかった**（実測）。
INVOKED_OK = """# デモ

```bash
bash <このスキルの base ディレクトリ>/scripts/find-cycle.py 42
```
"""

INVOKED_BROKEN = INVOKED_OK.replace("find-cycle.py", "find-cycle-typo.py")

# **プラグイン直下の共有物**（#216）。spec-loop の `req-loop` は `references/` と `scripts/` を
# スキルの中ではなくプラグイン直下に持ち、`../../` で指す。散文と起動行の両方を置く
# ——**片方だけだと、`POINTER` か `INVOCATION` の片方の前置を外す変異が殺せない。**
PARENT_OK = """# デモ

決まりは `../../references/qa.md` を正とする。

```bash
python3 <このスキルの base ディレクトリ>/../../scripts/check.py docs/qa.csv
```
"""

PARENT_BROKEN = PARENT_OK.replace("references/qa.md", "references/qa-typo.md")

# **実在するが、プラグインの外**。インストール先には無いので落とす。
ESCAPE = """# デモ

検査は `../../../../scripts/repo-only.py` を使う。
"""

# **隣のプラグイン**。名前の付いたディレクトリを通って外へ出る形で、これも実在するが落とす。
# **リポジトリの直下まで出る `ESCAPE` だけでは、境界を `plugins/` に 1 段上げた変異が緑のまま**
# だった（#216 の `/code-review` が実測）。
SIBLING = """# デモ

隣の決まりは `../../../other/README.md` を見る。
"""

# **一度プラグインの外へ出て、自分のプラグインの名前で戻る**。リポジトリでは実在するが、
# インストール先ではプラグインの上の名前が違うので実在しない。**行き着く先だけを見ると緑**
# だった（#216 の 2 パス目の `/code-review` が実測）。
ROUNDTRIP = """# デモ

決まりは `../../../demo/references/qa.md` を正とする。
"""

# **字面はスキルの中、実体は symlink の先**（#230）。字面を辿る `leaves_plugin` では外へ出ないので、
# **`resolve()` 側だけが捕まえる**。**この試料が無いと、`resolve()` 側だけを外す変異が殺せない**
# （Issue #230 の陽性対照: 変異を入れてもテストは振る舞いの検査がすべて合格だった）。
SYMLINKED = """# デモ

詳しくは `references/x.md` を見る。
"""

# **プラグインの外へ出る指し先に「X」が付いた形**（#574）——エラーはパスの検査の「プラグインの外」の 1 つだけ。
# **Issue の形（名指しあり）・名指し無し・字面は中で symlink の先が外**の 3 つを置く。「X」は外のファイルにも無い節にする
# ——在る節だと、外でも照合する変異で 2 つ目のエラーが出ず、変異が殺せない。修正前の版はどれも 2 つ出した（#542 の `/code-review`）。
OUTSIDE_OWNED = "# デモ\n\n読み方は other の `../../../other/README.md` の「無い節」を正とする。\n"
OUTSIDE_PLAIN = "# デモ\n\n読み方は `../../../other/README.md` の「無い節」を正とする。\n"
OUTSIDE_SYMLINKED = "# デモ\n\n詳しくは `references/x.md` の「無い節」を見る。\n"
# **外へ出て自分のプラグインの名前で戻る形**（字面でだけ外。`resolve()` の先は中）にも「X」を付ける——無いと、「X」の経路の判定から
# 字面の半分（`leaves_plugin`）だけを落とす変異が素通りする（#574 の 1 パス目の Verifier と `/code-review`）。
OUTSIDE_ROUNDTRIP = "# デモ\n\n決まりは `../../../demo/references/qa.md` の「無い節」を正とする。\n"
# **パスの検査が拾わないファイル名だけの指し先は、symlink の先が外でも照合する**（#574）——飛ばすとエラーが 0 になる。
# スキルの `SKILL.md` から、隣のプラグインへの symlink `o.md`（スキルのディレクトリ）を `` `o.md` `` で指す。**`SKILL.md` から書く**——
# 同じディレクトリがスキルのディレクトリなので `skill / rel` が実体になり、`/` を見ずに外かを判定する変異（`rel != "SKILL.md"`）で
# 結果が変わる。プラグイン直下から書くと `skill / rel` は実在しないファイルを指し、その変異が素通りした（#574 の 2 パス目の `/code-review`）。
BARE_OUTSIDE_REF = "# 決まり\n\n層は `o.md` の「無い節」を正とする。\n"
# **`SKILL.md` の symlink の先が外**の形も置く——**この試料が無いと、`/` を見ずに外かを判定する変異（守る 28d）が殺せない**
# （ファイル名だけの試料が殺すのは `rel != "SKILL.md"` の形の変異で、28d の変異は `SKILL.md` の側でしか結果が変わらない）。
SKILL_OUTSIDE_REF = "# r\n\n本体は `SKILL.md` の「無い節」を見る。\n"

# **散文の指し先**（#205）。**『』と本文の「」・太字・バッククォート・改行の違いを同一視する**ことを
# 試料に入れる——**揃えた書き方だけだと、正規化を外す変異が殺せない。** 太字とバッククォートは
# **X の途中に**置く（端に置くと、外さなくても部分一致で見つかる。2 パス目の `/code-review` が実測）。
PROSE_OK = """# デモ

**ここで「肯定的な確認」を
走らせる（必須）。**

不一致なら下の「ここで『肯定的な確認』を走らせる」の項へ戻る。
改名は `references/resume.md` の「改名の『コマンド』で分岐する」の項を読む。

**改名は** `git branch -m` で行う。

上の「改名は git branch -m で行う」とおり。`SKILL.md` 手順 4 の「改名は git branch -m で行う」も同じ。

```markdown
フェンスの中の書き方の例: 上の「どこにも無い項」
```
"""
PROSE_RESUME = "# 再開\n\n**改名の「コマンド」で\n分岐する（必須）**\n"

# **X が指し先の中にしか無い**——Issue #205 の `SKILL.md:464` と同じ形。
PROSE_BROKEN = """# デモ

不一致なら下の「改名のコマンドは『いまブランチの上にいるか』で分岐する」項へ進む。
"""

# **移した先を名指ししたが、その先に無い。**
XREF_BROKEN = """# デモ

改名は `references/resume.md` の「改名の『コマンド』で分岐する」の項を読む。
"""

# **`の` と `「` の間で折り返した指し先**——#205 の 1 パス目で S1・S5・S6 がこの形だった。
PROSE_SPLIT_BROKEN = """# デモ

不一致なら下の
「どこにも無い項」へ進む。
"""
XREF_SPLIT_BROKEN = """# デモ

改名は `references/resume.md` の
「どこにも無い項」を読む。
"""

# **`手順 N` を挟んだ形で、その先に無い**（#205 の 2 パス目の `/code-review`）。
STEP_BROKEN = """# デモ

詳しくは `SKILL.md` 手順 4 の「どこにも無い項」を見る。
"""

# **ファイルの名前の無い `手順 N の「X」`**（#655。#646 の 2 パス目の `/code-review` CR2-5——dev-loop の `SKILL.md` の項の文言を書き換えても、
# その項を `手順 6 の「…」` で指す 3 本が残ったまま緑だった）。書き手を `SKILL.md`・スキルの `references/`・`prompts/` に置き、どれも
# スキルの `SKILL.md` の項を指す（`の` と `「` の間の折り返し・『』も越える）。**`上の手順 N` は書いたファイルの中の項を指す**——
# `SKILL.md` に無い項にして、`SKILL.md` で照合すると落ちるようにする（守る 14c の変異を殺す）。**プラグイン直下の書き手**はどの `SKILL.md`
# かが決まらないので照合しない（守らない）——無い項を指して 0 を見る。**ほかの持ち主の名指し**は免除する（名指しを外した対照は 1）。
# 変異は免除の判定の文字列（`line_start`）をこの形のときだけ空にする（#600 の交絡を避ける）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if m.group(1) is None else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
STEP_BARE_SKILL = """# デモ

**手で「直す」項**

詳しくは手順 2 の
「手で『直す』項」を見る。
"""
STEP_BARE_REF = "# r\n\n**ローカルの項**\n\n詳しくは手順 2 の「手で『直す』項」を見る。上の手順 1 の「ローカルの項」も見る。\n"
STEP_BARE_PROMPT = "# p\n\n直し方は手順 2 の「手で『直す』項」を使う。\n"
STEP_BARE_PLUGIN_REF = "# a\n\n手順 2 の「どこにも無い項」は、プラグイン直下からは照合しない。\n"
STEP_BARE_OWNED = "# o\n\n読み方は other の手順 3 の「other にしか無い項」を正とする。\n"
# **1 本ずつ壊す**——`SKILL.md` の項（3 つの書き手が指す）／`上の手順 N` の項／指し先の中にしか無い X／名指しを外す。
STEP_BARE_SKILL_BROKEN = STEP_BARE_SKILL.replace("**手で「直す」項**", "**手で「直した」項**")
STEP_BARE_REF_LOCAL_BROKEN = STEP_BARE_REF.replace("**ローカルの項**", "**ローカルの節**")
STEP_BARE_SKILL_SELF = STEP_BARE_SKILL + "\n手順 9 の「自分の中にしか無い項」を見る。\n"
STEP_BARE_OWNED_PLAIN = STEP_BARE_OWNED.replace("other の手順", "手順")

# **X が、同じファイルの移した先の名指しの中にしか無い**——本文には無い。
XREF_MASKED = """# デモ

改名は `references/resume.md` の「改名の『コマンド』で分岐する」の項を読む。
不一致なら下の「改名の『コマンド』で分岐する」項へ進む。
"""

# **移した先が、X を元のファイルへの指し先の中にしか持っていない**——項はどこにも無い。
TARGET_MASKED = """# デモ

**戻り先の項**

詳しくは `references/resume.md` の「戻り先の項」を読む。
"""
TARGET_MASKED_RESUME = "# 再開\n\n`SKILL.md` の「戻り先の項」を見る。\n"

# **プラグイン直下**（#332）。判定役の定義と共有の決まりは、プラグインの根からの相対で書く。
# スキルからは `../../references/qa.md` の「X」で節を指す。**ほかの持ち主の名指し**も置く
# ——**置かないと、名指しを解決する変異が殺せない**（#332 の実物: spec-loop の `qa-csv.md`・`handoff-issue.md`）。
PLUGIN_SKILL = "# デモ\n\n区分は `../../references/qa.md` の「振り分けの区分」を正とする。\n"
PLUGIN_AGENT = "# 判定役\n\n区分は `references/qa.md` の「振り分けの区分」の名前で書く。\n"
PLUGIN_REF = """# 決まり

## 振り分けの区分

規定の本体は other の `references/spec-gap.md`。
同じ式の写しは other のスキルの `scripts/fp.py` にあり、このリポジトリの `scripts/test-x.py` が見る。
読み方は other の `references/qa.md` の「other にしか無い節」を正とする。
本体はother の `references/spec-gap.md`（名前の直前が日本語の文字でも名指し）。
"""
# **最後の行**は「X」の照合の免除を当てる——`references/qa.md` はこのプラグインにも在り、
# **X はこちらに無い**ので、**免除しなければ落ちる**（#332 の 1 パス目の `/code-review`）。
# **名指しが前の行にある**——免除しない（落ちる側）。
PLUGIN_REF_WRAPPED = PLUGIN_REF + "\n読み方は other の\n`references/qa.md` の「other にしか無い節」を正とする。\n"
# **大文字小文字だけ違う自分の名前**——macOS の FS では `Demo` のディレクトリが「在る」ことになる。
PLUGIN_REF_CASE = PLUGIN_REF + "\n自分の決まりは Demo の `references/missing.md` にある。\n"
# **名前の前が区切りでない**——`foo/other` はプラグインの名指しではない。
PLUGIN_REF_PATHLIKE = PLUGIN_REF + "\n詳細は foo/other の `references/missing.md` にある。\n"
PLUGIN_REF_DOTTED = PLUGIN_REF + "\n詳細は foo.other の `references/missing.md` にある。\n"
# **名指しが同じ行の前のほうにある**——指し先の直前ではないので免除しない（#332 の 2 パス目）。
PLUGIN_REF_EARLY = PLUGIN_REF + "\nother の規定と同じく、自分の `references/missing.md` を見る。\n"
# **`../../` の移した先の名指しで、その先に無い**——#332 の再現（spec-review の「振り分けの区分」）。
PLUGIN_SKILL_BROKEN = PLUGIN_SKILL.replace("振り分けの区分", "壊した区分")
# **判定役の定義の移した先の名指しで、その先に無い**——#332 の再現（red-team の「振り分けの区分」）。
PLUGIN_AGENT_BROKEN = PLUGIN_AGENT.replace("振り分けの区分", "壊した区分")
# **自分の名前と、プラグインでない名前の名指し**は免除しない。無いファイルを指しているので落ちるはず。
PLUGIN_REF_OWN = PLUGIN_REF + "\n自分の決まりは demo の `references/missing.md` にある。\n"
PLUGIN_REF_UNKNOWN = PLUGIN_REF + "\n詳細は spec の `references/missing.md` にある。\n"

# **`../` の後ろに名前の付いたディレクトリを通る移した先の名指し**（#503）——同じプラグインの隣のスキルの節を指す。
# **#484 の実物**: dev-loop `SKILL.md` の `` `../cruise/SKILL.md` の「4. 周を回す」 `` と、cruise の
# `` `../dev-loop/references/x.md` の「X」 ``。`SKILL.md`・`references/`・`prompts/` と、`手順 N` を挟んで
# `の`／`「` で折り返す形を 1 本ずつ置く。
# **壊れた試料は、どれも指し先を 1 本だけ壊す**——1 本の試料が先の行で落ちると、後ろの行の形を拾わなくなる変異が
# 殺せない（#503 の 1 パス目の `/code-review` が、`手順 N`・折り返しの形だけを拾わなくする変異で全合格のままだと実測で示した）。
SIBLING_XREF_OK = """# デモ

入り方は `../sib/SKILL.md` の「4. 周を回す」を正とする。
線は `../sib/references/x.md` の「隣の『節』」を正とする。
文面は `../sib/prompts/p.md` の「渡す文面」を使う。
閉じ方は `../sib/SKILL.md` 手順 5 の
「5. 周を閉じる」を見る。
"""
SIBLING_SKILL = "# 隣\n\n## 4. 周を回す\n\n## 5. 周を閉じる\n\n## 6. 参照から指す節\n\n## 7. 文面から指す節\n"
# **書く側も `SKILL.md` だけにしない**——スキルの `references/*.md` と `prompts/*.md` も、スキルのディレクトリから
# 解決して照合する（#503 の 2 パス目の `/code-review` が、ファイルの場所から解決する変異と `prompts/` を走査しない変異で
# 全合格のままだと実測で示した）。
SIBLING_SRC_REF = "# r\n\n入り方は `../sib/SKILL.md` の「6. 参照から指す節」を見る。\n"
SIBLING_SRC_PROMPT = "# q\n\n入り方は `../sib/SKILL.md` の「7. 文面から指す節」を見る。\n"
SIBLING_REF = "# x\n\n## 隣の「節」\n"
SIBLING_PROMPT = "# p\n\n## 渡す文面\n"
# **#484 の `/code-review` 2 パス目の再現**——隣のスキルの見出しを書き換えた（1 行目の指し先だけが壊れる）。
SIBLING_SKILL_BROKEN = SIBLING_SKILL.replace("4. 周を回す", "4. 周を束ねる")
SIBLING_REF_BROKEN = SIBLING_REF.replace("隣の「節」", "隣の「別の節」")
SIBLING_PROMPT_BROKEN = SIBLING_PROMPT.replace("渡す文面", "送る文面")
# **`手順 N` を挟んで折り返した指し先だけが壊れる。**
SIBLING_STEP_BROKEN = SIBLING_SKILL.replace("5. 周を閉じる", "5. 周を畳む")
# **ほかの持ち主の名指しが前に付いた `../` の指し先**（#542）——`../` の先は自分のプラグインなので、名指しがあっても照合する。
# **#503 の `/code-review` 2 パス目（CR2-5）の実物の形**: spec-loop の中の `` dev-loop の `../req-loop/SKILL.md` の「壊れた節」 ``。
# **名指しの名前は木にプラグインのディレクトリとして置く**——置くと `<名前> の`・`<名前> のスキルの` が持ち主の名指しと読まれる。
# **名前は `SIBLING_OWNER` の 1 つから作る**——試料・陽性対照・`sibling_tree` の `mkdir` が別々に名前を持つと、試料の名前だけがずれたとき
# 陽性対照は緑のまま、試料は名指しと読まれずに空振りする（#575 の 1 パス目の `/code-review`）。
# **置かなくても、`../` に名指しの免除を掛ける変異（28b）は殺せる**——`このリポジトリの` の試料は、名前のディレクトリに依らず名指しと読まれる
# （#575。#542 の 2 パス目の `/code-review` CR2-1——以前ここは「置かないと殺せない」と書いていた）。
# **置かないと素通りするのは、名前のディレクトリに依る形（`<名前> の`・`<名前> のスキルの`）の名指しだけ `../` でも免除する変異である**
# ——名前が名指しと読まれないので、`SIBLING_OWNED_BROKEN`・`SIBLING_OWNED_SKILL_BROKEN` は免除に届かないまま 1 で落ちる。
# **だから同じ木で `<名前> の` が持ち主と読まれることを見る**（下の `SIBLING_OWNER_READ`）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "        rel = m.group(1) or (path.name if m.group(0)[0] in \"上下\" else \"SKILL.md\")\n", "new": "        rel = m.group(1) or (path.name if m.group(0)[0] in \"上下\" else \"SKILL.md\")\n        _b = prose[line_start: m.start()]\n        if rel.startswith(\"../\") and owned_elsewhere(_b, plugin) and \"このリポジトリ\" not in _b and \"のスキル\" not in _b:\n            continue\n", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "        rel = m.group(1) or (path.name if m.group(0)[0] in \"上下\" else \"SKILL.md\")\n", "new": "        rel = m.group(1) or (path.name if m.group(0)[0] in \"上下\" else \"SKILL.md\")\n        _b = prose[line_start: m.start()]\n        if rel.startswith(\"../\") and owned_elsewhere(_b, plugin) and \"のスキル\" in _b:\n            continue\n", "red": "python3 scripts/test-check-skill-pointers.py"}
SIBLING_OWNER = "other"
SIBLING_OWNED_OK = SIBLING_XREF_OK + f"\n読み方は {SIBLING_OWNER} の `../sib/SKILL.md` の「5. 周を閉じる」を正とする。\n"
SIBLING_OWNED_BROKEN = SIBLING_XREF_OK + f"\n読み方は {SIBLING_OWNER} の `../sib/SKILL.md` の「壊れた節」を正とする。\n"
# **名指しの形を 3 つとも置く**——`<名前> の`・`<名前> のスキルの`・`このリポジトリの`。1 つの形だけ免除を残す変異
# （`このリポジトリ` か `のスキル` が前にあれば `../` でも免除する）は、`<名前> の` の試料だけでは殺せない（#542 の 1 パス目の `/code-review`）。
SIBLING_OWNED_SKILL_OK = SIBLING_XREF_OK + f"\n読み方は {SIBLING_OWNER} のスキルの `../sib/SKILL.md` の「5. 周を閉じる」を正とする。\n"
SIBLING_OWNED_SKILL_BROKEN = SIBLING_XREF_OK + f"\n読み方は {SIBLING_OWNER} のスキルの `../sib/SKILL.md` の「壊れた節」を正とする。\n"
SIBLING_OWNED_REPO_OK = SIBLING_XREF_OK + "\n読み方は このリポジトリの `../sib/SKILL.md` の「5. 周を閉じる」を正とする。\n"
SIBLING_OWNED_REPO_BROKEN = SIBLING_XREF_OK + "\n読み方は このリポジトリの `../sib/SKILL.md` の「壊れた節」を正とする。\n"
# **陽性対照: この木で `<名前> の` が持ち主の名指しと読まれる**（#575）——`../` で始まらない指し先は名指しで「X」の照合を免除するので、
# X が指した先（スキルの `references/r.md`）に無くても 0 で終わる。**`sibling_tree` の `mkdir` を消すと 1 になる。**
# **名指しを外した対照は 1 で落ちる**——陽性対照の 0 が、名指しの免除から来ていて、指し先がほかの理由で照合されないからではないことを見る。
SIBLING_OWNER_READ = SIBLING_XREF_OK + f"\n区分は {SIBLING_OWNER} の `references/r.md` の「{SIBLING_OWNER} にしか無い節」を正とする。\n"
SIBLING_OWNER_PLAIN = SIBLING_OWNER_READ.replace(f"{SIBLING_OWNER} の `references/r.md`", "`references/r.md`")
# **スキルの `references/*.md`・`prompts/*.md` から指した節だけが壊れる。**
SIBLING_SRC_REF_BROKEN = SIBLING_SKILL.replace("6. 参照から指す節", "6. 参照から指す項")
SIBLING_SRC_PROMPT_BROKEN = SIBLING_SKILL.replace("7. 文面から指す節", "7. 文面から指す項")

# **ディレクトリの付かないファイル名の移した先の名指し**（#541）——書いたファイルと同じディレクトリのファイルを指す。
# **#503 の `/code-review` 2 パス目の実物**: spec-loop のプラグイン直下の `references/` の `` `qa-csv.md` の「X」 ``。
# **書く側を 2 つ置く**——スキルの `references/` から隣のファイルを、プラグイン直下の `references/` から隣のファイルを
# （`の` と `「` の間で折り返し、『』で入れ子にして）。**スキルのディレクトリから解決する変異（守る 25d）は、プラグイン直下の側の
# 試料（`bare_plugin_broken`）だけでも殺せる**——プラグイン直下のファイルの「スキルのディレクトリ」はプラグインの根で、`references/` の
# 隣のファイルはそこに無い（#555。以前ここは「スキルの `references/` の側が無いと殺せない」と書いていたが、スキルの側の試料を壊さない版の
# テストでもその変異は赤だった）。**スキルの `references/` の側の試料（`bare_skill_broken`）も消さない**——書き手がスキルの側のときだけ
# スキルのディレクトリから解決する変異は、プラグイン直下の側の試料では殺せない。その変異を殺すのは `bare_skill_broken`・`bare_near`・
# `owned_bare_plain`（どれもスキルの `references/` から書いた木。#601 の 2 パス目の関門が当てた）。
# **同じディレクトリに無いファイル名**（cruise の `` `resume.md` ``・dev-loop の `` `qa-csv.md` `` の形）も置く——照合しない（守らない）。
# **スキルの `references/` から、同じディレクトリに無くスキルのディレクトリには在る名前（`t.md`）を指す試料を、別の木（`bare_near`）に置く**（#556 の N1）——
# 上の木に混ぜると、`t.md` を照合してしまう変異（25d など）で `bare_skill_broken`・`bare_plugin_broken` が `t.md` の行のせいで 1 になり、
# 壊した節で落ちたのかが見分けられなくなる（#601 の 1 パス目の Verifier）。
# 同じディレクトリに無いときスキルのディレクトリに戻って解決する変異は、この行を照合して落ちる。`SKILL.md` から書いた `resume.md` は
# スキルのディレクトリにも無いので、その変異でも照合されず区別できなかった（#541 の狭いパスの N1）。
# **変異は `SKILL.md` を戻り先から外す**——外さないと、テストの変異の表の 25f（`SKILL.md` もファイル名だけの形で解決する）と重なって
# `SKILL.md` が `skill / rel` に戻り、25f が生き残ってテストが赤になる。そのときは `t.md` の行を消しても赤のままで、この主張が行を留めない
# （#601 の 1 パス目の `/code-review`）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "same_dir.get(rel)  #", "new": "same_dir.get(rel) or (None if rel == \"SKILL.md\" else skill / rel)  #", "red": "python3 scripts/test-check-skill-pointers.py"}
# **`bare_near` の木には、書き手を `prompts/*.md` とプラグイン直下の `references/*.md` にも置く**（#655。#601 の 2 パス目の `/code-review` CR2-3
# ——書き手がスキルの `references/` だけで、N1 を書き手が `prompts/` のとき・プラグイン直下のときだけに当てる変異が素通りした）。
# プラグイン直下の書き手の「スキルのディレクトリ」はプラグインの根なので、`t.md` をプラグインの根にも置く（戻り先に在れば照合して 1 になる）。
# 変異は上と同じく `SKILL.md` を戻り先から外す（25f と重ならない）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "same_dir.get(rel)  #", "new": "same_dir.get(rel) or (skill / rel if path.parent.name == \"prompts\" and rel != \"SKILL.md\" else None)  #", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "same_dir.get(rel)  #", "new": "same_dir.get(rel) or (skill / rel if skill == plugin and rel != \"SKILL.md\" else None)  #", "red": "python3 scripts/test-check-skill-pointers.py"}
BARE_SKILL = "# デモ\n\n再開は `resume.md` の「どこにも無い節」を見る（同じディレクトリに無いので照合しない）。\n"
BARE_SRC_REF = "# r\n\n区分は `s.md` の「スキルの隣の節」を正とする。\n"
BARE_NEAR_REF = "# r\n\n隣に無い `t.md` の「どこにも無い節」は照合しない（スキルのディレクトリに同じ名前があっても）。\n"
# **`references/` から `SKILL.md` へ戻る指し先**（#556 の N2。守る 25f）——ファイル名だけの形と同じく同じディレクトリから解決する変異では、
# `references/` に `SKILL.md` が無いので照合されず、節が無くても 0 になる。**節が在る木（0）と無い木（1）を置く**——0 の木は、
# 無い木の 1 が `SKILL.md` の節の照合から来ていることの対照。
# **書き手を `prompts/*.md` にも置く**（#655。#601 の 1 パス目の Verifier V1-3——書き手が `prompts/` のときだけ同じディレクトリから
# 解決する変異は、#601 の対照 `owned_src_prompt_plain` だけが殺していた）。**書き手ごとに無い木を分ける**——1 つの木に混ぜると、片方の
# 書き手だけに当てた変異でも、もう片方の行で 1 になり見分けられない。
BACK_SKILL = "# デモ\n\n## 戻る節\n"
BACK_REF = "# b\n\n本体は `SKILL.md` の「戻る節」を見る。\n"
BARE_DST_REF = "# s\n\n## スキルの隣の節\n"
BARE_PLUGIN_REF = "# 決まり\n\n層は `qa.md` の\n「プラグインの隣の『節』」を正とする。\n"
BARE_PLUGIN_QA = "# qa\n\n## プラグインの隣の「節」\n"
# **1 本ずつ壊す**——スキルの `references/` から指した節だけ／プラグイン直下から指した節だけ。
BARE_DST_REF_BROKEN = BARE_DST_REF.replace("スキルの隣の節", "スキルの隣の項")
BARE_PLUGIN_QA_BROKEN = BARE_PLUGIN_QA.replace("プラグインの隣の「節」", "プラグインの隣の「項」")
# **大文字小文字だけ違うファイル名**——同じディレクトリに文字どおりには無いので照合しない（0）。
# **macOS の FS では `QA.md` が `qa.md` に「在る」ことになる**（#541 の 1 パス目の `/code-review`）。
BARE_PLUGIN_REF_CASE = BARE_PLUGIN_REF + "\n大文字の `QA.md` の「どこにも無い節」は照合しない。\n"

# **持ち主の名前が付いた、`../` で始まらない指し先の「X」は照合しない**——その免除は `references/x.md` の形（`PLUGIN_REF`）の
# ほかに `SKILL.md`・`prompts/x.md`・ファイル名だけの形にも掛かる。**3 つの形にも試料を置く**（#573。#542 の 1 パス目の
# `/code-review` CR1-1——`references/x.md` の試料だけでは、免除をほかの形から外す変異がどの検査も通った）。
# **指した先は自分のプラグインに実在し、X はそこに無い**——実在しなければ照合が飛ぶので、免除を外しても 0 のままで変異が殺せない。
# **ファイル名だけの形はスキルの `references/` から隣のファイルを指す**——`SKILL.md` から書いて隣のファイルをスキルのディレクトリに置いても
# 同じく見分けられる（元は 0、免除を外す変異は 1、名指しを外した対照は 1。#603 で確かめた）。指した先は走査の対象でなくても読むので、
# 以前ここに書いていた「`SKILL.md` から書くと、隣に置くファイルが走査の外になる」は理由にならない（#573 の 1 パス目の `/code-review` CR1-4）。
# **形ごとに名指しを外した対照を置く**（どれも 1 で落ちる）——対照が無いと、指し先が解決されずに照合が飛んでいても通る木は 0 のまま。
# 変異は免除を判定する文字列（`line_start`）を形ごとに空にする——`if not rel.startswith("../") and owned_elsewhere(…)` の行を書き換えると、
# 既存の変異の当て先が消えて、試料と関係なく赤になる（当て先が 1 箇所あるかの検査が落ちる）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if m.group(1) == \"SKILL.md\" else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if m.group(1).startswith(\"prompts/\") else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if \"/\" not in m.group(1) and m.group(1) != \"SKILL.md\" else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# **`` `SKILL.md` 手順 N の「X」 `` の形も置く**（#602。#573 の 1 パス目の `/code-review` CR1-3——`手順` を含む形だけ免除を外す変異が素通りした）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if \"手順\" in m.group(0) else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# **囲まれた指し先（パスの検査）の免除も、書き手が `SKILL.md` とスキルの `references/*.md` の木に置く**（#655。#601 の 1 パス目の
# `/code-review` CR1-3——試料は書き手が `agents/`・`prompts/`・プラグイン直下の `references/` だけで、書き手が `SKILL.md`・スキルの
# `references/` のときだけ免除を外す変異が素通りした）。**`prompts/…` の形で先が無い指し先も置く**（CR1-5——`OWNED_SKILL` の
# `` `prompts/p.md` `` は先が在るので、`prompts/` の形だけ免除を外す変異が素通りした）。先はどれも自分のプラグインに無い。
# 変異は `pointers_in` の免除の行に当てる——その行は変異の表の当て先ではない（`prose_pointers_in` の側は `line_start` に当てる）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "            if not owned_elsewhere(line[:m.start()], plugin):", "new": "            if path.name == \"SKILL.md\" or not owned_elsewhere(line[:m.start()], plugin):", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "            if not owned_elsewhere(line[:m.start()], plugin):", "new": "            if (path.parent.name == \"references\" and path.parent.parent != plugin) or not owned_elsewhere(line[:m.start()], plugin):", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "            if not owned_elsewhere(line[:m.start()], plugin):", "new": "            if m.group(1).startswith(\"prompts/\") or not owned_elsewhere(line[:m.start()], plugin):", "red": "python3 scripts/test-check-skill-pointers.py"}
OWNED_SKILL = """# デモ

入り方は other の `SKILL.md` の「other にしか無い節」を正とする。
文面は other の `prompts/p.md` の「other にしか無い節」を使う。
閉じ方は other の `SKILL.md` 手順 5 の「other にしか無い節」を見る。
規定は other の `references/gap.md` を正とする。
手引きは other の `prompts/gap.md` を使う。
"""
OWNED_PROMPT = "# p\n"
OWNED_SRC_REF = ("# r\n\n区分は other の `s.md` の「other にしか無い節」を正とする。\n"
                 "規定は other の `references/gap.md` を正とする。\n")
OWNED_DST_REF = "# s\n"
# **対照は 1 本ずつ名指しを外す**——ほかの形は免除されたまま。`SKILL.md` の 2 行（素の形と `手順 N` の形）も 1 行ずつ外す。
OWNED_SKILL_PLAIN = OWNED_SKILL.replace("other の `SKILL.md` の", "`SKILL.md` の")
OWNED_STEP_PLAIN = OWNED_SKILL.replace("other の `SKILL.md` 手順", "`SKILL.md` 手順")
OWNED_PROMPT_PLAIN = OWNED_SKILL.replace("other の `prompts/p.md`", "`prompts/p.md`")
OWNED_BARE_PLAIN = OWNED_SRC_REF.replace("other の `s.md`", "`s.md`")
OWNED_SKILL_PATH_PLAIN = OWNED_SKILL.replace("other の `references/gap.md`", "`references/gap.md`")
OWNED_PROMPT_PATH_PLAIN = OWNED_SKILL.replace("other の `prompts/gap.md`", "`prompts/gap.md`")
OWNED_SRC_REF_PATH_PLAIN = OWNED_SRC_REF.replace("other の `references/gap.md`", "`references/gap.md`")
# **書き手のファイルも 2 つ足す**——プラグイン直下の `agents/*.md` とスキルの `prompts/*.md`（#601。#573 の 1 パス目の `/code-review` CR1-2
# ——書き手が `SKILL.md`・スキルの `references/`・プラグイン直下の `references/` だけで、書き手が `agents/` のときだけ免除を外す変異が素通りした）。
# **各書き手に、「X」の照合の免除と、囲まれた指し先（パスの検査）の免除の 2 行を置く**——免除は `prose_pointers_in` と `pointers_in` の
# 2 箇所にあり、書き手ごとに外す変異はどちらにも書ける。指した先は自分のプラグインに在り（`references/qa.md`・`SKILL.md`）X はそこに無く、
# 囲まれた指し先（`references/gap.md`）は自分のプラグインに無い——**どちらも、免除を外せば 1 で落ちる**。
# **行ごとに名指しを外した対照を置く**（どれも 1 で落ちる。上と同じ理由）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if path.parent.name == \"agents\" else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if path.parent.name == \"prompts\" else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "            if not owned_elsewhere(line[:m.start()], plugin):", "new": "            if path.parent.name == \"agents\" or not owned_elsewhere(line[:m.start()], plugin):", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "            if not owned_elsewhere(line[:m.start()], plugin):", "new": "            if path.parent.name == \"prompts\" or not owned_elsewhere(line[:m.start()], plugin):", "red": "python3 scripts/test-check-skill-pointers.py"}
OWNED_AGENT = ("# 判定役\n\n区分は other の `references/qa.md` の「other にしか無い節」を正とする。\n"
               "規定は other の `references/gap.md` を正とする。\n")
OWNED_PLUGIN_QA = "# qa\n"
OWNED_SRC_PROMPT = ("# q\n\n入り方は other の `SKILL.md` の「other にしか無い節」を見る。\n"
                    "規定は other の `references/gap.md` を正とする。\n")
OWNED_AGENT_PLAIN = OWNED_AGENT.replace("other の `references/qa.md`", "`references/qa.md`")
OWNED_AGENT_PATH_PLAIN = OWNED_AGENT.replace("other の `references/gap.md`", "`references/gap.md`")
OWNED_SRC_PROMPT_PLAIN = OWNED_SRC_PROMPT.replace("other の `SKILL.md`", "`SKILL.md`")
OWNED_SRC_PROMPT_PATH_PLAIN = OWNED_SRC_PROMPT.replace("other の `references/gap.md`", "`references/gap.md`")
# **名指しの書き方も 3 つとも置く**——`<名前> の`（上）・`<名前> のスキルの`・`このリポジトリの`（#600。#573 の 1 パス目の
# `/code-review` CR1-1——`other の` の試料だけでは、ほかの 2 つの書き方だけ免除を外す変異がどの検査も通った）。
# **`SKILL.md`・`prompts/x.md`・ファイル名だけの形は上と同じ指し先**で、違うのは名指しの書き方だけ——その指し先が解決されて照合される
# ことは上の `OWNED_*_PLAIN` が見ている。**この試料が免除に届いていること**は、下の変異（その書き方だけ免除を外す）で 0 から 1 に変わることで見る。
# **`references/x.md` の形も足す**——`other の` のその形は `PLUGIN_REF` が持つが、ほかの 2 つの書き方は持たず、
# 書き方と `references/` の形の両方で免除を外す変異が素通りした（#600 の周で著者が当てた）。指した先 `references/r.md` は実在し、
# X はそこの指し先の中にしか無い（指し先は照合の前に消す）。**この行（`OWNED_REFS_LINE`）は上の試料に無い**ので、上の `OWNED_*_PLAIN`
# はこの行の名指しを外さない——**名指しを外した対照 `OWNED_REFS_PLAIN` を別に置く**（1 で落ちる。#603 の追記。#600 の `/code-review` CR1-2）。
# 変異は上と同じく `line_start` を書き方ごとに空にする（免除の行を書き換えると、当て先が 1 箇所あるかの検査が試料と関係なく落ちる）。
# **書き方ごとに `references/` の形だけ免除を外す変異も当てる**（下の 3・4 本目）——書き方ごとに全部の形の免除を外す 1・2 本目は、
# `OWNED_REFS_LINE` を空にしてもほかの形の試料で赤のままなので、この行を留めない。3・4 本目は `OWNED_REFS_LINE` を空にすると素通りする
# （そのため `OWNED_REFS_PLAIN` は `OWNED_REFS_LINE` から作らず、行を別に書く——作ると、空にしたとき対照のほうが先に落ち、
# 主張は「当てられなかった」になって行を留めない。#601 の 1 パス目の `/code-review`）
# （#603 の追記。#600 の `/code-review` CR1-1）。
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if \"このリポジトリ\" in prose[prose.rfind(\"\\n\", 0, m.start()) + 1:m.start()] else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if \"のスキル\" in prose[prose.rfind(\"\\n\", 0, m.start()) + 1:m.start()] else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if m.group(1).startswith(\"references/\") and \"このリポジトリ\" in prose[prose.rfind(\"\\n\", 0, m.start()) + 1:m.start()] else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
# mutation-claim: {"file": "scripts/check-skill-pointers.py", "old": "line_start = prose.rfind(\"\\n\", 0, m.start()) + 1", "new": "line_start = m.start() if m.group(1).startswith(\"references/\") and \"のスキル\" in prose[prose.rfind(\"\\n\", 0, m.start()) + 1:m.start()] else prose.rfind(\"\\n\", 0, m.start()) + 1", "red": "python3 scripts/test-check-skill-pointers.py"}
OWNED_REFS_LINE = "区分は other の `references/r.md` の「other にしか無い節」を正とする。\n"
OWNED_REFS_PLAIN = OWNED_SKILL + "区分は `references/r.md` の「other にしか無い節」を正とする。\n"
OWNED_SKILL_NAMED = (OWNED_SKILL + OWNED_REFS_LINE).replace("other の `", "other のスキルの `")
OWNED_SRC_REF_NAMED = OWNED_SRC_REF.replace("other の `", "other のスキルの `")
OWNED_SKILL_REPO = (OWNED_SKILL + OWNED_REFS_LINE).replace("other の `", "このリポジトリの `")
OWNED_SRC_REF_REPO = OWNED_SRC_REF.replace("other の `", "このリポジトリの `")

PLAIN = """# デモ

参照ファイル references/resume.md を読む（囲んでいないので拾わない）。
"""


def observe(mod, root: Path) -> dict:
    return {"rc": mod.main([str(root)])}


def errors(mod, root: Path) -> int:
    """指し先ごとのエラーの行（`ERROR:   <ファイル>:<行> → …`）の数。**終了コードだけでは 1 つと 2 つを分けられない**（#574）。"""
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        mod.main([str(root)])
    return sum(1 for line in err.getvalue().splitlines() if line.startswith("ERROR:   "))


MUTATIONS = {
    # 守る 1: 指し先のファイルが実在すること
    "実在を見ない": ('            if not (base / rel).exists():', '            if False:'),
    # 守る 2: 囲まれた指し先を拾うこと
    "囲みを見ない": (
        'POINTER = re.compile(r"`((?:references|prompts|scripts)/[\\w./-]+)`")',
        'POINTER = re.compile(r"(?!x)x")'),
    # 守る 3: フェンスの中を見ないこと（囲まれた相対パスについて）
    "フェンスを剥がさない": (
        "    stripped = strip_fences(raw)",
        "    stripped = raw"),
    # 守る 3b: フェンスの中の起動行は見ること
    "起動行を見ない": (
        'INVOCATION = re.compile(r"(?:bash|sh|python3?)\\s+.*?((?:\\.\\./)*scripts/[\\w.-]+)")',
        'INVOCATION = re.compile(r"(?!x)x")'),
    # 守る 4: スキルを固定しないこと
    "スキルを名前で固定する": (
        '    for plugin in sorted((root / "plugins").glob("*")):',
        '    for plugin in sorted((root / "plugins").glob("dev-loop")):'),
    # 守る 5: `../` で始まる指し先も拾うこと
    "`../` の前置を拾わない": (
        'PARENT = re.compile(r"`((?:\\.\\./)+[\\w.-][\\w./-]*)`")',
        'PARENT = re.compile(r"(?!x)x")'),
    # 守る 6: `../` の指し先がプラグインの中に収まること
    "プラグインの外を見逃す": (
        "            elif outside_plugin(base, plugin, rel):",
        "            elif False:"),
    # 守る 7: プラグインの境界は `plugins/<name>/` であること
    "境界を `plugins/` に上げる": (
        "        plugin = skill.parent.parent\n",
        "        plugin = skill.parent.parent.parent\n"),
    # 守る 8: 途中で 1 度でもプラグインの外へ出た指し先は、戻ってきても落とすこと
    "行き着く先だけを見る": (
        "    return (leaves_plugin(base, plugin, rel)",
        "    return (False"),
    # 守る 9: symlink の先がプラグインの外なら落とすこと（#230。上の 2 つと別に外す）
    "symlink の先を見ない": (
        "            or not (base / rel).resolve().is_relative_to(plugin.resolve()))",
        "            or False)"),
    # 守る 10: 散文の指し先 `上の「X」` の X が同じファイルにあること（#205）
    "散文の指し先を見ない": (
        "               normalize(m.group(1)) in own)",
        "               True)"),
    # 守る 11: `の` と `「` の間で折り返した散文の指し先も拾うこと
    "折り返した指し先を拾わない": (
        'NO = r"の\\s*"',
        'NO = r"の"'),
    # 守る 12: 散文の指し先も、フェンスの中は見ないこと
    "散文の指し先でフェンスを剥がさない": (
        "    prose = strip_fences(raw)",
        "    prose = raw"),
    # 守る 13: `references/x.md` の「X」の X が指したファイルにあること
    "移した先の名指しを見ない": (
        "               normalize(m.group(2)) in body_without_pointers(",
        "               True or body_without_pointers("),
    # 守る 14: `手順 N` を挟んだ形も拾うこと
    # （#655 で `XREF` にファイルの名前の無い選択肢を足したので、当て先は 1 つ目の選択肢の `手順 N` だけにした。
    # 外すと `` `../sib/SKILL.md` 手順 5 の「X」 `` が名前の無い形として自分の `SKILL.md` で照合され、`sibling_ok` が落ちる）
    "手順 N を挟んだ形を拾わない": (
        'r"\\s*(?:手順\\s*\\d+\\s*)?|',
        'r"\\s*|'),
    # 守る 14b: ファイルの名前の無い `手順 N の「X」` も拾い、X がスキルの `SKILL.md` にあること（#655）
    "ファイルの名前の無い `手順 N` を拾わない": (
        '|(?:[上下]の\\s*)?手順\\s*\\d+\\s*)" + NO',
        ')" + NO'),
    # 守る 14c: `上の手順 N の「X」`・`下の手順 N の「X」` は、書いたファイルの中を見ること（#655）
    "`上の手順 N` も `SKILL.md` で照合する": (
        'path.name if m.group(0)[0] in "上下" else "SKILL.md"',
        '"SKILL.md"'),
    # 守る 15: 指し先そのものの文字列は数えないこと
    "指し先が自分を見つける": (
        '    return normalize(XREF.sub("", PROSE.sub("", text)))',
        '    return normalize(XREF.sub("", text))'),
    # 守る 16: 移した先の名指しの文字列も数えないこと
    "移した先の名指しを本文に数える": (
        '    return normalize(XREF.sub("", PROSE.sub("", text)))',
        '    return normalize(PROSE.sub("", text))'),
    # 守る 17: 指した先の照合でも、そこの指し先の文字列は数えないこと
    "指した先の指し先を数える": (
        "               normalize(m.group(2)) in body_without_pointers(",
        "               normalize(m.group(2)) in normalize("),
    # 守る 18: 『』と「」の違いを同一視すること
    "『』を寄せない": (
        '.replace("『", "「").replace("』", "」")', ""),
    # 守る 19: 太字の違いを同一視すること
    "太字を外さない": ('re.sub(r"[*`\\s]"', 're.sub(r"[`\\s]"'),
    # 守る 20: バッククォートの違いを同一視すること
    "バッククォートを外さない": ('re.sub(r"[*`\\s]"', 're.sub(r"[*\\s]"'),
    # 守る 21: 空白（改行を含む）の違いを同一視すること
    "空白を外さない": ('re.sub(r"[*`\\s]"', 're.sub(r"[*`]"'),
    # 守る 23: プラグイン直下の `agents/*.md` と `references/*.md` も見ること（#332）
    "プラグイン直下を見ない": (
        '        for sub in ("agents", "references"):',
        '        for sub in ():'),
    # 守る 24: プラグイン直下のファイルの指し先は、プラグインの根から解決すること
    "プラグイン直下をファイルの場所から解決する": (
        "                yield plugin, plugin, path",
        "                yield path.parent, plugin, path"),
    # 守る 25: `../` で始まる移した先の名指しも拾うこと
    "`../` の移した先の名指しを拾わない": (
        '|(?:\\.\\./)+[\\w.-][\\w./-]*\\.md)`"',
        ')`"'),
    # 守る 25b: `../` の後ろに名前の付いたディレクトリを通る移した先の名指しも拾うこと（#503）
    "`../` の後ろを references/・prompts/ に限る": (
        '(?:\\.\\./)+[\\w.-][\\w./-]*\\.md)`"',
        '(?:\\.\\./)+(?:references|prompts)/[\\w.-]+\\.md)`"'),
    # 守る 25c: ディレクトリの付かないファイル名の移した先の名指しも拾うこと（#541）
    "ファイル名だけの指し先を拾わない": (
        "|[\\w.-]+\\.md|(?:\\.\\./)+", "|(?:\\.\\./)+"),
    # 守る 25d: ファイル名だけの指し先は、書いたファイルと同じディレクトリから解決すること（#541）
    "ファイル名だけの指し先をスキルのディレクトリから解決する": (
        "    same_dir = {p.name: p for p in path.parent.iterdir()}",
        "    same_dir = {p.name: p for p in skill.iterdir()}"),
    # 守る 25e: ファイル名だけの指し先は、ディレクトリの中の名前と文字どおりに比べること
    # **変異は大文字小文字を無視して名前から実体を引く形にする**——実体（`qa.md`）に届くので、大文字小文字を区別する FS
    # （Linux の CI）でも照合して 1 になる。**名前の照合だけを緩めて `path.parent / rel` を開く形では、Linux で `QA.md` が
    # 無くて飛ぶので殺せない**（#541 の 2 パス目の `/code-review` が `docker run python:3.12-slim` で示した）。
    "ファイル名だけの指し先の大文字小文字を無視する": (
        "            target = same_dir.get(rel)",
        "            target = next((q for n, q in same_dir.items() if n.lower() == rel.lower()), None)"),
    # 守る 25f: スキルの中のどのファイルから書いた `SKILL.md` の指し先も、スキルのディレクトリから解決すること（#556 の N2）
    "`SKILL.md` も書いたファイルと同じディレクトリから解決する": (
        '        if "/" not in rel and rel != "SKILL.md":',
        '        if "/" not in rel:'),
    # 守る 26: ほかの持ち主を名指しした指し先は解決しないこと
    "ほかの持ち主の名指しを解決する": (
        "    m = OWNER.search(before)",
        "    m = None"),
    # 守る 27: 自分の名前や、プラグインでない名前の名指しは解決すること
    "どの名指しも免除する": (
        "    return name != plugin.name and name in names",
        "    return True"),
    # 守る 28: 「X」の照合でも、ほかの持ち主を名指しした指し先は照合しないこと
    "「X」の照合でほかの持ち主の名指しを照合する": (
        "        if not rel.startswith(\"../\") and owned_elsewhere(prose[line_start:m.start()], plugin):\n            continue",
        "        if False:\n            continue"),
    # 守る 28b: `../` で始まる移した先の名指しは、ほかの持ち主の名指しがあっても「X」を照合すること（#542）
    "`../` の「X」にも名指しの免除を掛ける": (
        "        if not rel.startswith(\"../\") and owned_elsewhere(",
        "        if owned_elsewhere("),
    # 守る 28c: プラグインの外へ出る指し先の「X」は照合しないこと（#574）
    "外の指し先でも「X」を照合する": (
        "        if \"/\" in rel and outside_plugin(skill, plugin, rel):\n            continue",
        "        if False:\n            continue"),
    # 守る 28d: パスの検査が拾わない `SKILL.md` とファイル名だけの指し先は、外でも「X」を照合すること（#574）
    "`SKILL.md` も外なら「X」を照合しない": (
        "        if \"/\" in rel and outside_plugin(skill, plugin, rel):",
        "        if outside_plugin(skill, plugin, rel):"),
    # 守る 29: 名指しは同じ行だけを見ること
    "前の行の名指しで免除する": (
        "prose[line_start:m.start()]",
        "prose[max(0, m.start() - 40):m.start()]"),
    # 守る 30: プラグイン名は文字どおりに比べること（FS に依らず殺せるよう、大文字小文字を無視する形で当てる）
    "プラグイン名の大文字小文字を無視する": (
        "    return name != plugin.name and name in names",
        "    return name != plugin.name and name.lower() in {n.lower() for n in names}"),
    # 守る 31: 名前の前が区切りであること
    "名前の前の区切りを見ない": (
        r"(?<![A-Za-z0-9_/.-])([A-Za-z0-9_-]+)", r"([A-Za-z0-9_-]+)"),
    # 守る 32: 名前の直前が日本語の文字でも、名指しと読むこと
    "区切りを \\w で書く": (
        r"(?<![A-Za-z0-9_/.-])", r"(?<![\w/.-])"),
    # 守る 33: 名指しは指し先の直前だけを見ること
    "名指しを行の前のほうでも拾う": (
        r'(?:\s*のスキル)?)\s*の\s*$")', r'(?:\s*のスキル)?)\s*の")'),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        good = base / "good"
        assert_not_real_repo(good)
        make_skill(good, body=GOOD, files={
            "references/resume.md": "# 再開\n",
            "prompts/verifier.md": "# 委譲文\n",
            "scripts/find-cycle.py": "# script\n",
        })

        mod = load()
        print("正しい入力")
        check("指し先が全部実在すれば 0", observe(mod, good)["rc"] == 0)

        broken = base / "broken"
        assert_not_real_repo(broken)
        make_skill(broken, body=BROKEN, files={
            "references/resume.md": "# 再開\n",
            "prompts/verifier.md": "# 委譲文\n",
            "scripts/find-cycle.py": "# script\n",
        })
        print("\n壊れた指し先")
        check("1 文字ずれたら非ゼロ", observe(mod, broken)["rc"] == 1)

        fenced = base / "fenced"
        assert_not_real_repo(fenced)
        make_skill(fenced, body=FENCED, files={"references/resume.md": "# 再開\n"})
        invoked = base / "invoked"
        assert_not_real_repo(invoked)
        make_skill(invoked, body=INVOKED_OK, files={"scripts/find-cycle.py": "# s\n"})
        broken_inv = base / "invoked-broken"
        assert_not_real_repo(broken_inv)
        make_skill(broken_inv, body=INVOKED_BROKEN, files={"scripts/find-cycle.py": "# s\n"})
        print("\nフェンスの中の起動行")
        check("実在する起動行は通す", observe(mod, invoked)["rc"] == 0)
        check("壊れた起動行を捕まえる（空白を含む占位子ごしでも）",
              observe(mod, broken_inv)["rc"] == 1)

        def parent_tree(name: str, body: str) -> Path:
            d = base / name
            assert_not_real_repo(d)
            make_skill(d, body=body, files={})
            plugin = d / "plugins" / "demo"
            (plugin / "references").mkdir(parents=True, exist_ok=True)
            (plugin / "references" / "qa.md").write_text("# 決まり\n", encoding="utf-8")
            (plugin / "scripts").mkdir(parents=True, exist_ok=True)
            (plugin / "scripts" / "check.py").write_text("# s\n", encoding="utf-8")
            (d / "scripts").mkdir(parents=True, exist_ok=True)
            (d / "scripts" / "repo-only.py").write_text("# s\n", encoding="utf-8")
            (d / "plugins" / "other").mkdir(parents=True, exist_ok=True)
            (d / "plugins" / "other" / "README.md").write_text("# 隣\n", encoding="utf-8")
            return d

        parent_ok = parent_tree("parent-ok", PARENT_OK)
        parent_broken = parent_tree("parent-broken", PARENT_BROKEN)
        escape = parent_tree("escape", ESCAPE)
        sibling = parent_tree("sibling", SIBLING)
        roundtrip = parent_tree("roundtrip", ROUNDTRIP)
        print("\nプラグイン直下の共有物（`../`）")
        check("`../../` の指し先が実在すれば通す（散文と起動行）", observe(mod, parent_ok)["rc"] == 0)
        check("`../../` の指し先の綴り誤りを捕まえる", observe(mod, parent_broken)["rc"] == 1)
        check("プラグインの外を指したら、実在しても落とす", observe(mod, escape)["rc"] == 1)
        check("隣のプラグインを指したら、実在しても落とす", observe(mod, sibling)["rc"] == 1)
        check("外へ出て名前で戻る指し先は、実在しても落とす", observe(mod, roundtrip)["rc"] == 1)

        def symlink_tree(name: str, target: str, body: str = SYMLINKED) -> Path:
            """`references/x.md` を `target`（`references/` からの相対）への symlink にした木。"""
            d = parent_tree(name, body)
            (d / "plugins" / "other" / "references").mkdir(parents=True, exist_ok=True)
            (d / "plugins" / "other" / "references" / "o.md").write_text("# 隣\n", encoding="utf-8")
            link = d / "plugins" / "demo" / "skills" / "demo" / "references" / "x.md"
            link.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(target, link)
            return d

        # Issue #230 の木そのもの（隣のプラグインへ）と、プラグインの中に留まる対照
        symlink_out = symlink_tree("symlink-out", "../../../../other/references/o.md")
        symlink_in = symlink_tree("symlink-in", "../../../references/qa.md")
        print("\nsymlink（字面は中、実体は先）")
        check("symlink の先がプラグインの外なら、字面が中でも落とす",
              observe(mod, symlink_out)["rc"] == 1)
        check("symlink の先がプラグインの中なら通す", observe(mod, symlink_in)["rc"] == 0)

        outside_owned = parent_tree("outside-owned", OUTSIDE_OWNED)
        outside_plain = parent_tree("outside-plain", OUTSIDE_PLAIN)
        outside_roundtrip = parent_tree("outside-roundtrip", OUTSIDE_ROUNDTRIP)
        outside_symlinked = symlink_tree("outside-symlinked", "../../../../other/references/o.md", OUTSIDE_SYMLINKED)
        bare_outside = parent_tree("bare-outside", BARE_OUTSIDE_REF)
        (bare_outside / "plugins" / "other" / "references").mkdir(parents=True, exist_ok=True)
        (bare_outside / "plugins" / "other" / "references" / "o.md").write_text("# 隣\n", encoding="utf-8")
        os.symlink("../../../other/references/o.md", bare_outside / "plugins" / "demo" / "skills" / "demo" / "o.md")
        skill_outside = parent_tree("skill-outside", "# デモ\n")
        (skill_outside / "plugins" / "other" / "SKILL.md").write_text("# 隣\n", encoding="utf-8")
        skill_md = skill_outside / "plugins" / "demo" / "skills" / "demo" / "SKILL.md"
        skill_md.unlink()
        os.symlink("../../../other/SKILL.md", skill_md)
        (skill_md.parent / "references").mkdir(parents=True, exist_ok=True)
        (skill_md.parent / "references" / "r.md").write_text(SKILL_OUTSIDE_REF, encoding="utf-8")
        print("\nプラグインの外へ出る指し先の「X」（#574）")
        check("名指しの付いた外への `../` の「X」は、エラー 1 つ（プラグインの外）で落とす（#542 の CR1-3 の再現）",
              observe(mod, outside_owned)["rc"] == 1 and errors(mod, outside_owned) == 1)
        check("外へ出て名前で戻る `../` の「X」も、エラー 1 つで落とす（字面でだけ外）",
              observe(mod, outside_roundtrip)["rc"] == 1 and errors(mod, outside_roundtrip) == 1)
        check("名指しの無い外への `../` の「X」も、エラー 1 つで落とす",
              observe(mod, outside_plain)["rc"] == 1 and errors(mod, outside_plain) == 1)
        check("symlink の先が外の `references/x.md` の「X」も、エラー 1 つで落とす",
              observe(mod, outside_symlinked)["rc"] == 1 and errors(mod, outside_symlinked) == 1)
        check("ファイル名だけの指し先は、symlink の先が外でも「X」を照合して落とす（パスの検査が拾わない）",
              observe(mod, bare_outside)["rc"] == 1 and errors(mod, bare_outside) == 1)
        check("`SKILL.md` も、symlink の先が外でも「X」を照合して落とす（パスの検査が拾わない）",
              observe(mod, skill_outside)["rc"] == 1 and errors(mod, skill_outside) == 1)

        def prose_tree(name: str, body: str, resume: str) -> Path:
            d = base / name
            assert_not_real_repo(d)
            make_skill(d, body=body, files={"references/resume.md": resume})
            return d

        prose_ok = prose_tree("prose-ok", PROSE_OK, PROSE_RESUME)
        prose_broken = prose_tree("prose-broken", PROSE_BROKEN, PROSE_RESUME)
        xref_broken = prose_tree("xref-broken", XREF_BROKEN, "# 再開\n")
        prose_split = prose_tree("prose-split", PROSE_SPLIT_BROKEN, PROSE_RESUME)
        xref_split = prose_tree("xref-split", XREF_SPLIT_BROKEN, PROSE_RESUME)
        print("\n散文の指し先（#205）")
        check("X が本文にあれば通す（『』・太字・改行の違いを越えて。フェンスの中は見ない）",
              observe(mod, prose_ok)["rc"] == 0)
        check("X が指し先の中にしか無ければ落とす（#205 の形）",
              observe(mod, prose_broken)["rc"] == 1)
        check("移した先を名指しして、その先に無ければ落とす",
              observe(mod, xref_broken)["rc"] == 1)
        check("`の` と `「` の間で折り返しても、無ければ落とす（同じファイル）",
              observe(mod, prose_split)["rc"] == 1)
        check("`の` と `「` の間で折り返しても、無ければ落とす（移した先）",
              observe(mod, xref_split)["rc"] == 1)
        step_broken = prose_tree("step-broken", STEP_BROKEN, PROSE_RESUME)
        xref_masked = prose_tree("xref-masked", XREF_MASKED, PROSE_RESUME)
        target_masked = prose_tree("target-masked", TARGET_MASKED, TARGET_MASKED_RESUME)
        check("`手順 N` を挟んだ形でも、無ければ落とす", observe(mod, step_broken)["rc"] == 1)
        check("`` `SKILL.md` 手順 N の「X」 `` を、ファイルの名前の無い形として 2 度拾わない（エラー 1 つ。#655）",
              errors(mod, step_broken) == 1)

        def step_tree(name: str, *, skill: str = STEP_BARE_SKILL, ref: str = STEP_BARE_REF,
                      owned: str = STEP_BARE_OWNED) -> Path:
            d = base / name
            assert_not_real_repo(d)
            (d / "plugins" / "other").mkdir(parents=True, exist_ok=True)  # 名指しの名前をプラグインとして置く
            make_skill(d, body=skill, files={
                "references/r.md": ref, "references/o.md": owned, "prompts/p.md": STEP_BARE_PROMPT})
            (d / "plugins" / "demo" / "references").mkdir(parents=True, exist_ok=True)
            (d / "plugins" / "demo" / "references" / "a.md").write_text(STEP_BARE_PLUGIN_REF, encoding="utf-8")
            return d

        step_bare_ok = step_tree("step-bare-ok")
        step_bare_broken = step_tree("step-bare-broken", skill=STEP_BARE_SKILL_BROKEN)
        step_bare_local_broken = step_tree("step-bare-local-broken", ref=STEP_BARE_REF_LOCAL_BROKEN)
        step_bare_self = step_tree("step-bare-self", skill=STEP_BARE_SKILL_SELF)
        step_bare_owned_plain = step_tree("step-bare-owned-plain", owned=STEP_BARE_OWNED_PLAIN)
        check("ファイルの名前の無い `手順 N の「X」` は、X が `SKILL.md` に在れば通す（書き手が `SKILL.md`・`references/`・`prompts/`。"
              "`上の手順 N` は書いたファイル。プラグイン直下と名指しの付いた形は照合しない。#655）",
              observe(mod, step_bare_ok)["rc"] == 0)
        check("ファイルの名前の無い `手順 N の「X」` は、`SKILL.md` の項を書き換えたら落とす（#646 の CR2-5 の再現。#655）",
              observe(mod, step_bare_broken)["rc"] == 1 and errors(mod, step_bare_broken) == 3)
        check("`上の手順 N の「X」` は、書いたファイルの項を書き換えたら落とす（#655）",
              observe(mod, step_bare_local_broken)["rc"] == 1)
        check("ファイルの名前の無い `手順 N の「X」` の X が指し先の中にしか無ければ落とす（#655）",
              observe(mod, step_bare_self)["rc"] == 1)
        check("名指しを外したファイルの名前の無い `手順 N の「X」` は照合して落とす（対照。#655）",
              observe(mod, step_bare_owned_plain)["rc"] == 1)
        check("X が同じファイルの移した先の名指しの中にしか無ければ落とす",
              observe(mod, xref_masked)["rc"] == 1)
        check("移した先が X を指し先の中にしか持っていなければ落とす",
              observe(mod, target_masked)["rc"] == 1)

        def plugin_tree(name: str, *, skill: str = PLUGIN_SKILL, agent: str = PLUGIN_AGENT,
                        ref: str = PLUGIN_REF) -> Path:
            d = base / name
            assert_not_real_repo(d)
            make_skill(d, body=skill, files={})
            plugin = d / "plugins" / "demo"
            for rel, text in (("agents/judge.md", agent), ("references/qa.md", ref)):
                (plugin / rel).parent.mkdir(parents=True, exist_ok=True)
                (plugin / rel).write_text(text, encoding="utf-8")
            (d / "plugins" / "other").mkdir(parents=True, exist_ok=True)
            return d

        plugin_ok = plugin_tree("plugin-ok")
        plugin_skill_broken = plugin_tree("plugin-skill-broken", skill=PLUGIN_SKILL_BROKEN)
        plugin_agent_broken = plugin_tree("plugin-agent-broken", agent=PLUGIN_AGENT_BROKEN)
        plugin_own = plugin_tree("plugin-own", ref=PLUGIN_REF_OWN)
        plugin_unknown = plugin_tree("plugin-unknown", ref=PLUGIN_REF_UNKNOWN)
        plugin_wrapped = plugin_tree("plugin-wrapped", ref=PLUGIN_REF_WRAPPED)
        plugin_case = plugin_tree("plugin-case", ref=PLUGIN_REF_CASE)
        plugin_pathlike = plugin_tree("plugin-pathlike", ref=PLUGIN_REF_PATHLIKE)
        plugin_dotted = plugin_tree("plugin-dotted", ref=PLUGIN_REF_DOTTED)
        plugin_early = plugin_tree("plugin-early", ref=PLUGIN_REF_EARLY)
        print("\nプラグイン直下（#332）")
        check("判定役と共有の決まりの指し先が実在すれば通す（ほかの持ち主の名指しは解決しない）",
              observe(mod, plugin_ok)["rc"] == 0)
        check("`../../references/x.md` の「X」が、その先に無ければ落とす",
              observe(mod, plugin_skill_broken)["rc"] == 1)
        check("判定役の定義の `references/x.md` の「X」が、その先に無ければ落とす",
              observe(mod, plugin_agent_broken)["rc"] == 1)
        check("自分の名前の名指しは免除しない", observe(mod, plugin_own)["rc"] == 1)
        check("プラグインでない名前の名指しは免除しない", observe(mod, plugin_unknown)["rc"] == 1)
        check("前の行の名指しでは「X」の照合を免除しない", observe(mod, plugin_wrapped)["rc"] == 1)
        check("大文字小文字だけ違う自分の名前は免除しない", observe(mod, plugin_case)["rc"] == 1)
        check("名前の前が区切りでなければ免除しない", observe(mod, plugin_pathlike)["rc"] == 1)
        check("名前の前が `.` でも免除しない", observe(mod, plugin_dotted)["rc"] == 1)
        check("同じ行の前のほうの名指しでは免除しない", observe(mod, plugin_early)["rc"] == 1)

        def sibling_tree(name: str, *, sib: str = SIBLING_SKILL, ref: str = SIBLING_REF,
                         prompt: str = SIBLING_PROMPT, body: str = SIBLING_XREF_OK) -> Path:
            d = base / name
            assert_not_real_repo(d)
            # mutation-claim: {"file": "scripts/test-check-skill-pointers.py", "old": "            (d / \"plugins\" / SIBLING_OWNER).mkdir(parents=True, exist_ok=True)  # 名指しの名前を持ち主と読ませる（#542・#575）\n", "new": "", "red": "python3 scripts/test-check-skill-pointers.py"}
            (d / "plugins" / SIBLING_OWNER).mkdir(parents=True, exist_ok=True)  # 名指しの名前を持ち主と読ませる（#542・#575）
            make_skill(d, body=body, files={
                "references/r.md": SIBLING_SRC_REF, "prompts/q.md": SIBLING_SRC_PROMPT})
            sib_dir = d / "plugins" / "demo" / "skills" / "sib"
            (sib_dir / "references").mkdir(parents=True, exist_ok=True)
            (sib_dir / "SKILL.md").write_text(sib, encoding="utf-8")
            (sib_dir / "references" / "x.md").write_text(ref, encoding="utf-8")
            (sib_dir / "prompts").mkdir(parents=True, exist_ok=True)
            (sib_dir / "prompts" / "p.md").write_text(prompt, encoding="utf-8")
            return d

        sibling_ok = sibling_tree("sibling-xref-ok")
        sibling_skill_broken = sibling_tree("sibling-skill-broken", sib=SIBLING_SKILL_BROKEN)
        sibling_ref_broken = sibling_tree("sibling-ref-broken", ref=SIBLING_REF_BROKEN)
        sibling_prompt_broken = sibling_tree("sibling-prompt-broken", prompt=SIBLING_PROMPT_BROKEN)
        sibling_step_broken = sibling_tree("sibling-step-broken", sib=SIBLING_STEP_BROKEN)
        sibling_src_ref_broken = sibling_tree("sibling-src-ref-broken", sib=SIBLING_SRC_REF_BROKEN)
        sibling_src_prompt_broken = sibling_tree("sibling-src-prompt-broken", sib=SIBLING_SRC_PROMPT_BROKEN)
        sibling_owned_ok = sibling_tree("sibling-owned-ok", body=SIBLING_OWNED_OK)
        sibling_owned_broken = sibling_tree("sibling-owned-broken", body=SIBLING_OWNED_BROKEN)
        sibling_owned_skill_ok = sibling_tree("sibling-owned-skill-ok", body=SIBLING_OWNED_SKILL_OK)
        sibling_owned_skill_broken = sibling_tree("sibling-owned-skill-broken", body=SIBLING_OWNED_SKILL_BROKEN)
        sibling_owned_repo_ok = sibling_tree("sibling-owned-repo-ok", body=SIBLING_OWNED_REPO_OK)
        sibling_owned_repo_broken = sibling_tree("sibling-owned-repo-broken", body=SIBLING_OWNED_REPO_BROKEN)
        sibling_owner_read = sibling_tree("sibling-owner-read", body=SIBLING_OWNER_READ)
        sibling_owner_plain = sibling_tree("sibling-owner-plain", body=SIBLING_OWNER_PLAIN)
        print("\n隣のスキルを通る `../` の移した先の名指し（#503）")
        check("隣のスキルの節が在れば通す（`手順 N`・折り返し・『』を越えて）",
              observe(mod, sibling_ok)["rc"] == 0)
        check("隣のスキルの `SKILL.md` の見出しを書き換えたら落とす（#484 の再現）",
              observe(mod, sibling_skill_broken)["rc"] == 1)
        check("隣のスキルの `references/x.md` の節を書き換えたら落とす",
              observe(mod, sibling_ref_broken)["rc"] == 1)
        check("隣のスキルの `prompts/x.md` の節を書き換えたら落とす",
              observe(mod, sibling_prompt_broken)["rc"] == 1)
        check("`手順 N` を挟んで折り返した隣のスキルの指し先も、その先に無ければ落とす",
              observe(mod, sibling_step_broken)["rc"] == 1)
        check("スキルの `references/*.md` から隣のスキルを指した節が無ければ落とす（スキルのディレクトリから解決）",
              observe(mod, sibling_src_ref_broken)["rc"] == 1)
        check("スキルの `prompts/*.md` から隣のスキルを指した節が無ければ落とす",
              observe(mod, sibling_src_prompt_broken)["rc"] == 1)
        check("ほかの持ち主の名指しが付いた `../` の指し先も、節が在れば通す（#542）",
              observe(mod, sibling_owned_ok)["rc"] == 0)
        check("ほかの持ち主の名指しが付いた `../` の指し先も、節が無ければ落とす（#503 の CR2-5 の再現。#542）",
              observe(mod, sibling_owned_broken)["rc"] == 1)
        check("`<名前> のスキルの` の名指しが付いた `../` の指し先も、節が在れば通し、無ければ落とす（#542）",
              observe(mod, sibling_owned_skill_ok)["rc"] == 0
              and observe(mod, sibling_owned_skill_broken)["rc"] == 1)
        check("`このリポジトリの` の名指しが付いた `../` の指し先も、節が在れば通し、無ければ落とす（#542）",
              observe(mod, sibling_owned_repo_ok)["rc"] == 0
              and observe(mod, sibling_owned_repo_broken)["rc"] == 1)
        check("この木で `other の` が持ち主の名指しと読まれる（陽性対照。`../` で始まらない指し先の「X」を照合しない。#575）",
              observe(mod, sibling_owner_read)["rc"] == 0)
        check("名指しを外した同じ指し先は照合して落とす（対照）", observe(mod, sibling_owner_plain)["rc"] == 1)

        def bare_tree(name: str, *, dst: str = BARE_DST_REF, qa: str = BARE_PLUGIN_QA,
                      ref: str = BARE_PLUGIN_REF) -> Path:
            d = base / name
            assert_not_real_repo(d)
            make_skill(d, body=BARE_SKILL, files={"references/r.md": BARE_SRC_REF, "references/s.md": dst})
            refs = d / "plugins" / "demo" / "references"
            refs.mkdir(parents=True, exist_ok=True)
            (refs / "a.md").write_text(ref, encoding="utf-8")
            (refs / "qa.md").write_text(qa, encoding="utf-8")
            return d

        bare_ok = bare_tree("bare-ok")
        bare_skill_broken = bare_tree("bare-skill-broken", dst=BARE_DST_REF_BROKEN)
        bare_plugin_broken = bare_tree("bare-plugin-broken", qa=BARE_PLUGIN_QA_BROKEN)
        bare_case = bare_tree("bare-case", ref=BARE_PLUGIN_REF_CASE)
        bare_near = base / "bare-near"
        assert_not_real_repo(bare_near)
        make_skill(bare_near, body="# デモ\n", files={
            "references/r.md": BARE_NEAR_REF, "prompts/q.md": BARE_NEAR_REF, "t.md": "# t\n"})
        for rel, text in (("references/a.md", BARE_NEAR_REF), ("t.md", "# t\n")):  # プラグイン直下の書き手（#655）
            (bare_near / "plugins" / "demo" / rel).parent.mkdir(parents=True, exist_ok=True)
            (bare_near / "plugins" / "demo" / rel).write_text(text, encoding="utf-8")
        print("\nディレクトリの付かないファイル名の移した先の名指し（#541）")
        check("同じディレクトリの節が在れば通す（折り返し・『』を越えて。同じディレクトリに無いファイル名は照合しない）",
              observe(mod, bare_ok)["rc"] == 0)
        check("スキルの `references/` から隣のファイルを指した節が無ければ落とす（同じディレクトリから解決）",
              observe(mod, bare_skill_broken)["rc"] == 1)
        check("プラグイン直下の `references/` から隣のファイルを指した節が無ければ落とす（#503 の CR2-3 の再現）",
              observe(mod, bare_plugin_broken)["rc"] == 1)
        check("大文字小文字だけ違うファイル名は照合しない（文字どおりに比べる。OS に依らない）",
              observe(mod, bare_case)["rc"] == 0)
        check("同じディレクトリに無いファイル名は、スキルのディレクトリに同じ名前があっても照合しない"
              "（#556 の N1。書き手がスキルの `references/`・`prompts/`・プラグイン直下の `references/` でも。#655）",
              observe(mod, bare_near)["rc"] == 0)

        def owned_tree(name: str, *, skill: str = OWNED_SKILL, ref: str = OWNED_SRC_REF,
                       agent: str = OWNED_AGENT, prompt: str = OWNED_SRC_PROMPT) -> Path:
            d = base / name
            assert_not_real_repo(d)
            (d / "plugins" / "other").mkdir(parents=True, exist_ok=True)  # 名指しの名前をプラグインとして置く
            make_skill(d, body=skill, files={
                "prompts/p.md": OWNED_PROMPT, "prompts/q.md": prompt,
                "references/r.md": ref, "references/s.md": OWNED_DST_REF})
            plugin = d / "plugins" / "demo"
            (plugin / "agents").mkdir(parents=True, exist_ok=True)
            (plugin / "agents" / "judge.md").write_text(agent, encoding="utf-8")
            (plugin / "references").mkdir(parents=True, exist_ok=True)
            (plugin / "references" / "qa.md").write_text(OWNED_PLUGIN_QA, encoding="utf-8")
            return d

        owned_ok = owned_tree("owned-ok")
        owned_skill_plain = owned_tree("owned-skill-plain", skill=OWNED_SKILL_PLAIN)
        owned_step_plain = owned_tree("owned-step-plain", skill=OWNED_STEP_PLAIN)
        owned_prompt_plain = owned_tree("owned-prompt-plain", skill=OWNED_PROMPT_PLAIN)
        owned_bare_plain = owned_tree("owned-bare-plain", ref=OWNED_BARE_PLAIN)
        owned_refs_plain = owned_tree("owned-refs-plain", skill=OWNED_REFS_PLAIN)
        owned_agent_plain = owned_tree("owned-agent-plain", agent=OWNED_AGENT_PLAIN)
        owned_agent_path_plain = owned_tree("owned-agent-path-plain", agent=OWNED_AGENT_PATH_PLAIN)
        owned_src_prompt_plain = owned_tree("owned-src-prompt-plain", prompt=OWNED_SRC_PROMPT_PLAIN)
        owned_src_prompt_path_plain = owned_tree("owned-src-prompt-path-plain", prompt=OWNED_SRC_PROMPT_PATH_PLAIN)
        owned_skill_path_plain = owned_tree("owned-skill-path-plain", skill=OWNED_SKILL_PATH_PLAIN)
        owned_prompt_path_plain = owned_tree("owned-prompt-path-plain", skill=OWNED_PROMPT_PATH_PLAIN)
        owned_src_ref_path_plain = owned_tree("owned-src-ref-path-plain", ref=OWNED_SRC_REF_PATH_PLAIN)
        owned_named = owned_tree("owned-named", skill=OWNED_SKILL_NAMED, ref=OWNED_SRC_REF_NAMED)
        owned_repo = owned_tree("owned-repo", skill=OWNED_SKILL_REPO, ref=OWNED_SRC_REF_REPO)
        print("\n持ち主の名前による「X」の照合の免除の形（#573）")
        check("持ち主の名前が付いた `SKILL.md`（`手順 N` の形を含む）・`prompts/x.md`・ファイル名だけの指し先は、"
              "X が自分の先に無くても照合しない（書き手が `agents/*.md`・`prompts/*.md` でも。囲まれた指し先も、"
              "書き手が `SKILL.md`・スキルの `references/*.md` でも、`prompts/…` の形でも解決しない。#655）",
              observe(mod, owned_ok)["rc"] == 0)
        check("`<名前> のスキルの` の名指しでも、同じ 3 つの形（`SKILL.md` は `手順 N` の形を含む）と `references/x.md` の指し先は照合しない（#600）",
              observe(mod, owned_named)["rc"] == 0)
        check("`このリポジトリの` の名指しでも、同じ 3 つの形（`SKILL.md` は `手順 N` の形を含む）と `references/x.md` の指し先は照合しない（#600）",
              observe(mod, owned_repo)["rc"] == 0)
        check("名指しを外した `SKILL.md` の指し先は照合して落とす（対照）", observe(mod, owned_skill_plain)["rc"] == 1)
        check("名指しを外した `SKILL.md` 手順 N の指し先は照合して落とす（対照。#602）", observe(mod, owned_step_plain)["rc"] == 1)
        check("名指しを外した `prompts/x.md` の指し先は照合して落とす（対照）", observe(mod, owned_prompt_plain)["rc"] == 1)
        check("名指しを外したファイル名だけの指し先は照合して落とす（対照）", observe(mod, owned_bare_plain)["rc"] == 1)
        check("名指しを外した `references/x.md` の指し先は照合して落とす（対照。#603）", observe(mod, owned_refs_plain)["rc"] == 1)
        check("`SKILL.md` から書いた、名指しを外した囲まれた指し先は解決して落とす（対照。#655）",
              observe(mod, owned_skill_path_plain)["rc"] == 1)
        check("名指しを外した `prompts/…` の囲まれた指し先は解決して落とす（対照。#655）",
              observe(mod, owned_prompt_path_plain)["rc"] == 1)
        check("スキルの `references/*.md` から書いた、名指しを外した囲まれた指し先は解決して落とす（対照。#655）",
              observe(mod, owned_src_ref_path_plain)["rc"] == 1)
        check("`agents/*.md` から書いた、名指しを外した「X」の指し先は照合して落とす（対照。#601）",
              observe(mod, owned_agent_plain)["rc"] == 1)
        check("`agents/*.md` から書いた、名指しを外した囲まれた指し先は解決して落とす（対照。#601）",
              observe(mod, owned_agent_path_plain)["rc"] == 1)
        check("スキルの `prompts/*.md` から書いた、名指しを外した「X」の指し先は照合して落とす（対照。#601）",
              observe(mod, owned_src_prompt_plain)["rc"] == 1)
        check("スキルの `prompts/*.md` から書いた、名指しを外した囲まれた指し先は解決して落とす（対照。#601）",
              observe(mod, owned_src_prompt_path_plain)["rc"] == 1)

        def back_tree(name: str, skill: str, writers=("references/b.md",)) -> Path:
            d = base / name
            assert_not_real_repo(d)
            make_skill(d, body=skill, files={w: BACK_REF for w in writers})
            return d

        back_ok = back_tree("back-ok", BACK_SKILL, ("references/b.md", "prompts/c.md"))
        back_broken = back_tree("back-broken", "# デモ\n")
        back_prompt_broken = back_tree("back-prompt-broken", "# デモ\n", ("prompts/c.md",))
        print("\n`references/` から `SKILL.md` へ戻る指し先（#556 の N2）")
        check("スキルの `references/`・`prompts/` から `SKILL.md` の節を指し、節が在れば通す", observe(mod, back_ok)["rc"] == 0)
        check("スキルの `references/` から `SKILL.md` の節を指し、節が無ければ落とす（スキルのディレクトリから解決）",
              observe(mod, back_broken)["rc"] == 1)
        check("スキルの `prompts/` から `SKILL.md` の節を指し、節が無ければ落とす（スキルのディレクトリから解決。#655）",
              observe(mod, back_prompt_broken)["rc"] == 1)

        print("\nフェンスと散文")
        check("フェンスの中の指し先は見ない", observe(mod, fenced)["rc"] == 0)

        plain = base / "plain"
        assert_not_real_repo(plain)
        make_skill(plain, body=PLAIN, files={})
        check("囲んでいない指し先は拾わない（守らないと明記した範囲）",
              observe(mod, plain)["rc"] == 0)

        print("\n変異テスト（壊したのに緑なら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}", False)
                continue
            d = base / f"mut-{abs(hash(name))}"
            (d / "scripts").mkdir(parents=True)
            (d / "scripts" / "check-skill-pointers.py").write_text(
                source.replace(needle, replacement, 1), encoding="utf-8")
            (d / "scripts" / "markdown_fences.py").write_text(
                (SCRIPT.parent / "markdown_fences.py").read_text(encoding="utf-8"),
                encoding="utf-8")
            try:
                mutant = load(d / "scripts" / "check-skill-pointers.py")
                # **壊れた木で非ゼロにならない**か、**フェンスの木で非ゼロになる**なら殺せた
                killed = (mutant.main([str(broken)]) != 1
                          or mutant.main([str(fenced)]) != 0
                          or mutant.main([str(broken_inv)]) != 1
                          or mutant.main([str(invoked)]) != 0
                          or mutant.main([str(parent_ok)]) != 0
                          or mutant.main([str(parent_broken)]) != 1
                          or mutant.main([str(escape)]) != 1
                          or mutant.main([str(sibling)]) != 1
                          or mutant.main([str(roundtrip)]) != 1
                          or mutant.main([str(symlink_out)]) != 1
                          or mutant.main([str(symlink_in)]) != 0
                          or mutant.main([str(prose_ok)]) != 0
                          or mutant.main([str(prose_broken)]) != 1
                          or mutant.main([str(xref_broken)]) != 1
                          or mutant.main([str(prose_split)]) != 1
                          or mutant.main([str(xref_split)]) != 1
                          or mutant.main([str(step_broken)]) != 1
                          or errors(mutant, step_broken) != 1
                          or mutant.main([str(step_bare_ok)]) != 0
                          or mutant.main([str(step_bare_broken)]) != 1
                          or mutant.main([str(step_bare_local_broken)]) != 1
                          or mutant.main([str(step_bare_self)]) != 1
                          or mutant.main([str(step_bare_owned_plain)]) != 1
                          or mutant.main([str(xref_masked)]) != 1
                          or mutant.main([str(target_masked)]) != 1
                          or mutant.main([str(plugin_ok)]) != 0
                          or mutant.main([str(plugin_skill_broken)]) != 1
                          or mutant.main([str(plugin_agent_broken)]) != 1
                          or mutant.main([str(plugin_own)]) != 1
                          or mutant.main([str(plugin_unknown)]) != 1
                          or mutant.main([str(plugin_wrapped)]) != 1
                          or mutant.main([str(plugin_case)]) != 1
                          or mutant.main([str(plugin_pathlike)]) != 1
                          or mutant.main([str(plugin_dotted)]) != 1
                          or mutant.main([str(plugin_early)]) != 1
                          or mutant.main([str(sibling_ok)]) != 0
                          or mutant.main([str(sibling_skill_broken)]) != 1
                          or mutant.main([str(sibling_ref_broken)]) != 1
                          or mutant.main([str(sibling_prompt_broken)]) != 1
                          or mutant.main([str(sibling_step_broken)]) != 1
                          or mutant.main([str(sibling_src_ref_broken)]) != 1
                          or mutant.main([str(sibling_src_prompt_broken)]) != 1
                          or mutant.main([str(sibling_owned_ok)]) != 0
                          or mutant.main([str(sibling_owned_broken)]) != 1
                          or mutant.main([str(sibling_owned_skill_ok)]) != 0
                          or mutant.main([str(sibling_owned_skill_broken)]) != 1
                          or mutant.main([str(sibling_owned_repo_ok)]) != 0
                          or mutant.main([str(sibling_owned_repo_broken)]) != 1
                          or mutant.main([str(sibling_owner_read)]) != 0
                          or mutant.main([str(sibling_owner_plain)]) != 1
                          or mutant.main([str(bare_ok)]) != 0
                          or mutant.main([str(bare_skill_broken)]) != 1
                          or mutant.main([str(bare_plugin_broken)]) != 1
                          or mutant.main([str(bare_case)]) != 0
                          or mutant.main([str(bare_near)]) != 0
                          or mutant.main([str(owned_ok)]) != 0
                          or mutant.main([str(owned_skill_plain)]) != 1
                          or mutant.main([str(owned_prompt_plain)]) != 1
                          or mutant.main([str(owned_bare_plain)]) != 1
                          or mutant.main([str(owned_named)]) != 0
                          or mutant.main([str(owned_repo)]) != 0
                          or mutant.main([str(owned_step_plain)]) != 1
                          or mutant.main([str(owned_refs_plain)]) != 1
                          or mutant.main([str(owned_agent_plain)]) != 1
                          or mutant.main([str(owned_agent_path_plain)]) != 1
                          or mutant.main([str(owned_src_prompt_plain)]) != 1
                          or mutant.main([str(owned_src_prompt_path_plain)]) != 1
                          or mutant.main([str(owned_skill_path_plain)]) != 1
                          or mutant.main([str(owned_prompt_path_plain)]) != 1
                          or mutant.main([str(owned_src_ref_path_plain)]) != 1
                          or mutant.main([str(back_ok)]) != 0
                          or mutant.main([str(back_broken)]) != 1
                          or mutant.main([str(back_prompt_broken)]) != 1
                          or errors(mutant, outside_owned) != 1
                          or errors(mutant, outside_plain) != 1
                          or errors(mutant, outside_roundtrip) != 1
                          or errors(mutant, outside_symlinked) != 1
                          or errors(mutant, bare_outside) != 1
                          or errors(mutant, skill_outside) != 1)
            except Exception:
                killed = True
            check(f"変異を殺せる: {name}", killed)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [l for l in body.splitlines() if l.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件",
              len(promises) == len(MUTATIONS))

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
    print("スキルの指し先の検査のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
