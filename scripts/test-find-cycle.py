#!/usr/bin/env python3
"""`find-cycle.py` の回帰テスト。

    python3 scripts/test-find-cycle.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）。
`scripts/` ではない——**`dev-loop` はどのリポジトリでも使えるスキル**で、
**`scripts/find-cycle.py` は他のリポジトリには存在しない。**
**スキルが自分の base ディレクトリから呼べる場所に置く。**

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリを作り、そこだけを
対象にする（`assert_not_real_repo` がそれを担保する）。本体は cwd からリポジトリを
解決するので、**歯止めが無いと、テストがこのリポジトリ自身を探して通ってしまう**
——通っても「探索が効く」の証明にならない。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。

**主張とテストを 1 対 1 にする。** 本体の docstring の「守る」の行数だけ変異を当てる。
行を足したら変異も足す（`test-collect-guard-rejections.py` と同じ形で、**テスト自身に
数えさせる**）。
"""
import importlib.util
import os
import subprocess
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "find-cycle.py"

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"fc_{id(script)}", script)
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


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def build_repo(root: Path, number="42") -> None:
    """偽のリポジトリ。**計画ファイルは番号をディレクトリ名の側に置く**
    ——`-name`（basename のみ）では当たらない配置で、#96 が実際に踏んだ形。"""
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "t")
    (root / "README.md").write_text("x\n", encoding="utf-8")
    plans = root / "docs" / "plans" / f"issue-{number}"
    plans.mkdir(parents=True)
    (plans / "plan.md").write_text("# 計画\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", f"feat: 何かする (#{number})")


def observe(mod, root: Path, number="42", script: Path = SCRIPT) -> dict:
    """出力・終了コード・**経路ごとの結果**をまとめて観測する。

    **出力の文字列だけで判定しない。** 経路 1 と経路 4 は**同じパス文字列を出す**ので、
    「`issue-42/plan.md` が出力に在るか」では**どちらが当てたか判別できない**
    （最初そう書いて、変異が 1 つ生き残った）。**経路 1 の戻り値を直接見る。**

    **`cwd` からの root 解決は、`report()` を呼ぶ限り 1 度も走らない**——
    あれは `main()` の中だけにある。**だからスクリプトを素で起動して別に観測する。**
    """
    import contextlib, io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.report(number, root)
    out = buf.getvalue()
    plans, _ = mod.find_plans(root, number)
    proc = subprocess.run(["python3", str(script), number], cwd=root,
                          capture_output=True, text=True)
    return {
        "rc": rc,
        "経路 1 の当たり": tuple(plans),
        "経路の見出し": sum(out.count(f"[{i}]") for i in range(1, 6)),
        "失敗の申告": "探せなかった" in out,
        "cwd から起動した rc": proc.returncode,
    }


MUTATIONS = {
    # 守る 1: 5 本を必ず全部走らせる
    "1 本当たったら打ち切る": (
        "    plans, missing_dirs = find_plans(root, number)",
        "    plans, missing_dirs = find_plans(root, number)\n    if plans:\n        return 1"),
    # 守る 2: 部分一致の広さを隠さない（basename だけで照合すると取り逃す）
    "basename だけで照合する": (
        "            if path.is_file() and number in str(path.relative_to(root)):",
        "            if path.is_file() and number in path.name:"),
    # 守る 3: リポジトリの root を自分で解決する
    "root を cwd で代用する": (
        '    out = run(["git", "rev-parse", "--show-toplevel"], cwd=start)',
        '    out = Result(False, "")\n    _ = start'),
    # 守る 4: 空と失敗を区別する
    "失敗を空として扱う": (
        '    if proc.returncode != 0:\n        return Result(False, proc.stdout, proc.stderr.strip() or f"終了コード {proc.returncode}")',
        '    if proc.returncode != 0:\n        return Result(True, "")'),
}

MUTATION_PROBE = {
    # cwd 解決の変異は `--root` を渡さない経路でしか効かない
    "root を cwd で代用する": "main",
    # 失敗の申告は、git を壊した木でしか効かない
    "失敗を空として扱う": "brokengit",
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        repo = tmpdir / "repo"
        assert_not_real_repo(repo)
        build_repo(repo)

        mod = load()
        correct = observe(mod, repo)

        print("正しい入力での探索")
        check("番号がディレクトリ名の側にある計画ファイルに当たる",
              correct["経路 1 の当たり"] == ("docs/plans/issue-42/plan.md",))
        check("cwd からリポジトリの root を解決して起動できる",
              correct["cwd から起動した rc"] == 1)
        check("5 本の経路をすべて出す", correct["経路の見出し"] == 5)
        check("当たったので rc=1", correct["rc"] == 1)
        check("失敗の申告は出ていない", not correct["失敗の申告"])

        print("\n当たらない周は新規と答える")
        empty = tmpdir / "empty"
        assert_not_real_repo(empty)
        build_repo(empty, number="7")
        got = observe(mod, empty, "999")
        check("1 件も当たらなければ rc=0", got["rc"] == 0)
        check("それでも 5 本すべてを出す", got["経路の見出し"] == 5)

        print("\n探せなかった経路があれば「新規」と答えない")
        broken = tmpdir / "brokengit"
        broken.mkdir()
        (broken / "docs").mkdir()
        assert_not_real_repo(broken)
        got = observe(mod, broken, "42")
        check("git が使えない木では rc=2", got["rc"] == 2)
        check("探せなかったことを申告する", got["失敗の申告"])

        print("\n引数の検査")
        check("数字以外の Issue 番号は rc=2", mod.main(["abc"]) == 2)

        print("\n変異テスト（壊したのに緑なら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        probes = {"main": repo, "brokengit": broken}
        for name, (needle, replacement) in MUTATIONS.items():
            if needle not in source:
                check(f"変異を当てる先がある: {name}", False)
                continue
            d = tmpdir / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken_script = d / "find-cycle.py"
            broken_script.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            target = probes.get(MUTATION_PROBE.get(name, "main"), repo)
            base = correct if target is repo else observe(mod, target, "42")
            try:
                # **素起動も変異したスクリプトで行う**——既定のままだと本体を起動して
                # しまい、`cwd` からの root 解決の変異が観測に現れない。
                mutated = observe(load(broken_script), target, "42", script=broken_script)
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", mutated != base)

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
    print("周の探索のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
