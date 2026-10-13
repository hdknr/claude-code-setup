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
import importlib.util
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

PLAIN = """# デモ

参照ファイル references/resume.md を読む（囲んでいないので拾わない）。
"""


def observe(mod, root: Path) -> dict:
    return {"rc": mod.main([str(root)])}


MUTATIONS = {
    # 守る 1: 指し先のファイルが実在すること
    "実在を見ない": ('                if not (skill / rel).exists():', '                if False:'),
    # 守る 2: 囲まれた指し先を拾うこと
    "囲みを見ない": (
        'POINTER = re.compile(r"`((?:references|prompts|scripts)/[\\w./-]+)`")',
        'POINTER = re.compile(r"(?!x)x")'),
    # 守る 3b: フェンスの中の起動行は見ること
    "起動行を見ない": (
        'INVOCATION = re.compile(r"(?:bash|sh|python3?)\\s+.*?((?:\\.\\./)*scripts/[\\w.-]+)")',
        'INVOCATION = re.compile(r"(?!x)x")'),
    # 守る 3: フェンスの中を見ないこと（囲まれた相対パスについて）
    "フェンスを剥がさない": (
        "    stripped = strip_fences(raw)",
        "    stripped = raw"),
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
        "                elif (leaves_plugin(skill, plugin, rel)\n"
        "                      or not (skill / rel).resolve().is_relative_to(plugin.resolve())):",
        "                elif False:"),
    # 守る 7: プラグインの境界は `plugins/<name>/` であること
    "境界を `plugins/` に上げる": (
        "        plugin = skill.parent.parent\n",
        "        plugin = skill.parent.parent.parent\n"),
    # 守る 8: 途中で 1 度でもプラグインの外へ出た指し先は、戻ってきても落とすこと
    "行き着く先だけを見る": (
        "                elif (leaves_plugin(skill, plugin, rel)",
        "                elif (False"),
    # 守る 9: symlink の先がプラグインの外なら落とすこと（#230。上の 2 つと別に外す）
    "symlink の先を見ない": (
        "                      or not (skill / rel).resolve().is_relative_to(plugin.resolve())):",
        "                      or False):"),
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
    "手順 N を挟んだ形を拾わない": (
        "`\\s*(?:手順\\s*\\d+\\s*)?\" + NO + QUOTED)",
        "`\\s*\" + NO + QUOTED)"),
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

        def symlink_tree(name: str, target: str) -> Path:
            """`references/x.md` を `target`（`references/` からの相対）への symlink にした木。"""
            d = parent_tree(name, SYMLINKED)
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
        check("X が同じファイルの移した先の名指しの中にしか無ければ落とす",
              observe(mod, xref_masked)["rc"] == 1)
        check("移した先が X を指し先の中にしか持っていなければ落とす",
              observe(mod, target_masked)["rc"] == 1)

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
                          or mutant.main([str(xref_masked)]) != 1
                          or mutant.main([str(target_masked)]) != 1)
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
