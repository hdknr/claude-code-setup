#!/usr/bin/env python3
"""`check-duplicate-counts.py` の回帰テスト。

    python3 scripts/test-check-duplicate-counts.py

**このテストは実環境を触らない。** 毎回テンポラリに偽のツリーを作り、そこだけを対象にする
（`assert_not_real_repo` がそれを担保する）。本体は既定でこのリポジトリ自身を走査するので、
**歯止めが無いと、テストが実リポジトリを見て通ってしまう。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**「守る」の行数と変異の数が 1 対 1 か**は、**テスト自身が数える。**

**実際に起きた欠陥を母集団に入れてある。** `docs/plans/issue-122.md` の `525f3e6` 時点で
**同じ語句に「1 つ」と「2 つ」が同居していた**形を、そのまま試料にしている
——**作り話ではなく、このリポジトリが実際に踏んだ形である。**

## このファイル自身が免除されている

**試料は、この検査が捕まえる形そのもの**なので、**置いた瞬間に自分で落ちた。**
**免除の仕組みの実演として、そのまま残してある**（本体の docstring と同じ形）。

dup-counts-ok: 残る課題
"""
import importlib.util
import os
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "check-duplicate-counts.py"

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"cdc_{id(script)}", script)
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


# **実際に起きた形**（`docs/plans/issue-122.md` の `525f3e6`）。
REAL_DEFECT = """# 計画

    - **揃わなかったものが 1 つ**: **git の版**（macOS 2.54.0 / 像 2.39.5）。

**揃わなかったものが 2 つある**（一度「git の版だけ」と書いて、反証された）:
"""

FENCED_ONLY = """# 例

```bash
echo "歯止めが 8 本"
echo "歯止めが 21 本"
```
"""

EXEMPTED = REAL_DEFECT + "\ndup-counts-ok: 揃わなかったもの\n"

# **免除した語句と、していない語句が同居する形。**
# **これが無いと「免除を語句で絞らない」変異が殺せない**——
# 免除つきの試料に語句が 1 つしか無いと、全部免除しても結果が変わらない。
EXEMPT_PLUS_DEFECT = REAL_DEFECT + """
**残る課題が 3 件**ある。

**残る課題が 5 件**に増えた。

dup-counts-ok: 揃わなかったもの
"""

# **フェンスの中に免除を書いた形。** **効いてはならない**——
# **コード例として見せた免除がファイル全体に効くと、「黙ってファイル全体を免除しない」
# という約束に反する。** **免除だけフェンスを剥がしていなかった**のを直した跡で、
# **その直しに回帰テストが無いと 2 パス目の Verifier に反証された。**
FENCED_EXEMPTION = """# 免除の書き方の例

**揃わなかったものが 1 つ**。

**揃わなかったものが 2 つ**。

書き方はこう:

```markdown
dup-counts-ok: 揃わなかったもの
```
"""

OTHER_PHRASE = """# 別の語句なら当たらない

**歯止めが 8 本**ある。

**回帰テストが 12 本**ある。
"""


def write(root: Path, name: str, body: str) -> None:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def observe(mod, root: Path) -> dict:
    """本体の判定をまとめて観測する。"""
    out = {}
    for path in sorted(root.glob("*.md")):
        hits = mod.scan(path.read_text(encoding="utf-8"))
        out[path.name] = tuple(sorted((p, u, tuple(sorted(n))) for (p, u), n in hits.items()))
    return out


MUTATIONS = {
    # 守る 1: 同じファイルの中の自己矛盾
    "食い違いを見ない": (
        "    return {key: nums for key, nums in found.items() if len(nums) > 1}",
        "    return {}"),
    # 守る 2: 強調の中の数
    "強調を落とさない": (
        '        plain = line.replace("**", "")',
        "        plain = line"),
    # 守る 3: フェンスの中を数えない
    "フェンスを剥がさない": (
        "    stripped = strip_fences(text)",
        "    stripped = text"),
    # 守る 4: 免除は語句を名指しさせる
    "免除を語句で絞らない": (
        "            if phrase in exempt:",
        "            if exempt:"),
    # 守る 5: 免除もフェンスの外だけを拾う
    "免除をフェンスごと拾う": (
        "    exempt = set(EXEMPT.findall(stripped))",
        "    exempt = set(EXEMPT.findall(text))"),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "tree"
        root.mkdir()
        assert_not_real_repo(root)
        write(root, "defect.md", REAL_DEFECT)
        write(root, "fenced.md", FENCED_ONLY)
        write(root, "exempt.md", EXEMPTED)
        write(root, "other.md", OTHER_PHRASE)
        write(root, "mixed.md", EXEMPT_PLUS_DEFECT)
        write(root, "fenced-exempt.md", FENCED_EXEMPTION)

        mod = load()
        correct = observe(mod, root)

        print("実際に起きた欠陥を捕まえるか")
        check("同じ語句に 1 と 2 が混在していたら出す",
              correct["defect.md"] == (("揃わなかったもの", "つ", ("1", "2")),))
        check("フェンスの中だけなら出さない", correct["fenced.md"] == ())
        check("語句を名指しした免除があれば出さない", correct["exempt.md"] == ())
        check("語句が違えば出さない", correct["other.md"] == ())
        check("免除は名指しした語句だけに効く（他の語句は出る）",
              correct["mixed.md"] == (("残る課題", "件", ("3", "5")),))
        check("フェンスの中に書いた免除は効かない",
              correct["fenced-exempt.md"] == (("揃わなかったもの", "つ", ("1", "2")),))

        print("\n終了コード")
        check("欠陥があれば非ゼロ", mod.main([str(root)]) == 1)
        clean = Path(tmp) / "clean"
        clean.mkdir()
        assert_not_real_repo(clean)
        write(clean, "ok.md", OTHER_PHRASE)
        check("欠陥が無ければ 0", mod.main([str(clean)]) == 0)

        print("\n変異テスト（壊したのに緑なら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}", False)
                continue
            d = Path(tmp) / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "check-duplicate-counts.py"
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            # 共有モジュールを同じ場所から読めるようにする
            (d / "markdown_fences.py").write_text(
                (REAL_REPO / "scripts" / "markdown_fences.py").read_text(encoding="utf-8"),
                encoding="utf-8")
            try:
                mutated = observe(load(broken), root)
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", mutated != correct)

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
    print("件数の食い違いの検査のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
