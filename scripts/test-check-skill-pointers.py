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
        'INVOCATION = re.compile(r"(?:bash|sh|python3?)\\s+.*?(scripts/[\\w.-]+)")',
        'INVOCATION = re.compile(r"(?!x)x")'),
    # 守る 3: フェンスの中を見ないこと（囲まれた相対パスについて）
    "フェンスを剥がさない": (
        "    stripped = strip_fences(raw)",
        "    stripped = raw"),
    # 守る 4: スキルを固定しないこと
    "スキルを名前で固定する": (
        '    for plugin in sorted((root / "plugins").glob("*")):',
        '    for plugin in sorted((root / "plugins").glob("dev-loop")):'),
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
                          or mutant.main([str(invoked)]) != 0)
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
