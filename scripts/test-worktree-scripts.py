#!/usr/bin/env python3
"""`prepare-worktree.sh` と `check-pr-preconditions.sh` の回帰テスト。

    python3 scripts/test-worktree-scripts.py

**本体は `scripts/` に無い。** `plugins/dev-loop/skills/dev-loop/scripts/` にある
——**`dev-loop` はどのリポジトリでも使うスキル**で、**対象リポジトリの `scripts/` に
在ることを当てにできない**（**段 1 でここを間違えて PR に出し、マージ後に気づいた**）。

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリを作り、そこだけを
対象にする（`assert_not_real_repo` がそれを担保する）。
**本体は `git rev-parse` で自分のいるリポジトリを解決する**ので、
**歯止めが無いと、テストがこのリポジトリに worktree を作ってしまう。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**「守る」の行数と変異の数が 1 対 1 か**は、**テスト自身が数える。**

**散文では検証できなかった分岐を、ここで初めて検証している**——
`SKILL.md` 手順 4 の入場手順は **#96 / #110 / #113 で繰り返し穴が見つかった**のに、
**テストが 1 本も無かった**（#136）。
"""
import os
import subprocess
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts"
PREPARE = SKILL_SCRIPTS / "prepare-worktree.sh"
PRECOND = SKILL_SCRIPTS / "check-pr-preconditions.sh"

failures: list[str] = []


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


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def make_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    assert_not_real_repo(root)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "t")
    (root / "README.md").write_text("x\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    return root


def run(script: Path, cwd: Path, *args):
    return subprocess.run(["bash", str(script), *args], cwd=cwd, capture_output=True, text=True)


def observe(prepare: Path, precond: Path, base: Path) -> dict:
    """両スクリプトの分岐をまとめて観測する。**1 回の観測で 1 つの偽リポジトリを使い切る。**"""
    repo = make_repo(base / "repo")
    first = run(prepare, repo, "42", "sample")
    again = run(prepare, repo, "42", "sample")
    bad_num = run(prepare, repo, "abc", "x")
    wt = repo / ".claude" / "worktrees" / "issue-42"
    out = {
        "新規で作れる": first.returncode,
        # **出力も観測する。** 終了コードとファイルシステムだけ見ていると、
        # **「確認の材料を出す」という約束の変異が殺せない**（最初そうなっていた）。
        "確認の材料が出ている": ("ブランチ: issue/42-sample" in first.stdout
                                and "起点:" in first.stdout),
        "2 回目は断る": again.returncode,
        "数字以外は断る": bad_num.returncode,
        "作られた場所": wt.is_dir(),
        "切られたブランチ": git(wt, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if wt.is_dir() else "",
    }
    if wt.is_dir():
        out["前提条件: 一致"] = run(precond, wt, "issue/42-sample").returncode
        out["前提条件: 不一致"] = run(precond, wt, "issue/999-other").returncode
    out["前提条件: メイン"] = run(precond, repo).returncode
    # **別の worktree の中から走らせる。** 相対パスだと**そこに入れ子で生える**ので、
    # **メインの作業ツリーから走らせる観測だけでは、その変異を殺せない。**
    if wt.is_dir():
        run(prepare, wt, "43", "nested")
        out["入れ子で生えていない"] = not (wt / ".claude" / "worktrees" / "issue-43").exists()
        out["別 worktree からでも規約の場所"] = (
            repo / ".claude" / "worktrees" / "issue-43").is_dir()
    # **サブディレクトリから走らせる。** `--git-dir` は絶対、`--git-common-dir` は
    # **相対で返ることがあり、その相対は cwd を起点にする。**
    # **トップレベルからの観測だけでは、この 2 つの実バグが両方とも素通りした**
    # ——前提条件が**メインの作業ツリーで rc=0** を返し、入場が**リポジトリの外**に
    # worktree を作ろうとしていた（`/code-review` が指摘。#136）。
    deep = repo / "sub" / "deep"
    deep.mkdir(parents=True, exist_ok=True)
    out["前提条件: メインのサブディレクトリ"] = run(precond, deep).returncode
    sub_res = run(prepare, deep, "77", "nested-sub")
    out["サブから作った場所がリポジトリの中"] = (
        repo / ".claude" / "worktrees" / "issue-77").is_dir()
    out["サブから作ってもリポジトリの外に作らない"] = not (
        repo.parent / ".claude").exists()
    out["サブから作った rc"] = sub_res.returncode

    # **git が使えない木では「判定できなかった」と答える**（「メインにいる」ではない）。
    nogit = base / "nogit"
    nogit.mkdir(parents=True, exist_ok=True)
    out["前提条件: git 無し"] = run(precond, nogit).returncode
    # **入場の側も、見られなかったときに作らないことを見る。**
    # **これが無いと「見られなくても作る」変異が殺せない**（観測が無いため）。
    out["入場: git 無し"] = run(prepare, nogit, "88", "nogit").returncode
    out["入場: git 無しでも作らない"] = not (nogit / ".claude").exists()

    # detached を作って見分けられるか
    if wt.is_dir():
        sha = git(wt, "rev-parse", "HEAD").stdout.strip()
        git(wt, "checkout", "-q", "--detach", sha)
        out["前提条件: detached"] = run(precond, wt, "issue/42-sample").returncode
    return out


MUTATIONS = {
    # 守る 1: 先に見る（再開の周を新規として踏み潰さない）
    "先に見ずに作る": (PREPARE,
        'if [ -n "$EXISTING_WT" ] || [ -n "$EXISTING_BR" ]; then',
        'if false; then'),
    # 守る 2: 絶対パスで作る
    "相対パスで作る": (PREPARE,
        'PATH_ABS="${MAIN}/.claude/worktrees/issue-${NUMBER}"',
        'PATH_ABS=".claude/worktrees/issue-${NUMBER}"'),
    # 守る 3: 規約どおりの名前で切る
    "命名規約を外す": (PREPARE,
        'BRANCH="issue/${NUMBER}-${SLUG}"',
        'BRANCH="worktree-${SLUG}"'),
    # 守る 4: 肯定的な確認の材料を出す
    "確認の材料を出さない": (PREPARE,
        'echo "ブランチ: ${ACTUAL_BRANCH}"',
        'true'),
    # --- check-pr-preconditions.sh の 守る 4 行 ---
    # 守る 1: worktree にいるか
    "worktree 判定をしない": (PRECOND,
        'if [ "$GIT_DIR" = "$COMMON_DIR" ]; then',
        'if false; then'),
    # 守る 2: 正しい worktree にいるか
    "ブランチを突き合わせない": (PRECOND,
        'if [ -n "$EXPECTED" ] && [ "$BRANCH" != "$EXPECTED" ]; then',
        'if false; then'),
    # 守る 3: detached を見分ける
    "detached を見分けない": (PRECOND,
        'if ! git symbolic-ref -q HEAD >/dev/null; then',
        'if false; then'),
    # 守る 4: 終了コードで区別する
    "終了コードを一律にする": (PRECOND,
        '  exit 3\nfi',
        '  exit 1\nfi'),
    # 守る 5: 判定できなかったことを「メインにいる」と答えない
    "判定できなくても答える": (PRECOND,
        '  exit 4\nfi',
        '  GIT_DIR=""; COMMON_DIR=""\nfi'),
    # 守る 6（prepare）: 判定できなかったことを「当たらなかった」と答えない
    # **root の守りを壊すと、背後の守りが終了コード 6 で受け止める**ので観測が変わる。
    "見られなくても作る": (PREPARE,
        '  exit 5\nfi\nMAIN=',
        '  COMMON="$(pwd)/.git"\nfi\nMAIN='),
    # 守る 7（prepare）: 相対パスを cwd 起点で解決する（= 絶対で取る）
    "相対のまま root 起点で解決する": (PREPARE,
        'MAIN="$(cd "$(dirname "$COMMON")" && pwd -P)"',
        'MAIN="$(cd "$(git rev-parse --show-toplevel)/$(dirname "$(git rev-parse --git-common-dir)")" && pwd -P)"'),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        correct = observe(PREPARE, PRECOND, base / "correct")

        print("prepare-worktree.sh")
        check("新規の周では作れる（rc=0）", correct["新規で作れる"] == 0)
        check("同じ番号が在れば断る（rc=3）", correct["2 回目は断る"] == 3)
        check("数字以外の番号を断る（rc=2）", correct["数字以外は断る"] == 2)
        check("規約どおりの場所に作る", correct["作られた場所"])
        check("規約どおりの名前で切る", correct["切られたブランチ"] == "issue/42-sample")
        check("確認の材料（ブランチ名と起点）を出力する", correct["確認の材料が出ている"])
        check("別の worktree から走らせても入れ子で生えない", correct["入れ子で生えていない"])
        check("別の worktree から走らせても規約の場所に作る",
              correct["別 worktree からでも規約の場所"])

        print("\ncheck-pr-preconditions.sh")
        check("worktree でブランチも一致なら通す（rc=0）", correct["前提条件: 一致"] == 0)
        check("ブランチが違えば止める（rc=2）", correct["前提条件: 不一致"] == 2)
        check("メインの作業ツリーなら止める（rc=1）", correct["前提条件: メイン"] == 1)
        check("detached を見分ける（rc=3）", correct["前提条件: detached"] == 3)
        check("メインの**サブディレクトリ**でも止める（rc=1）",
              correct["前提条件: メインのサブディレクトリ"] == 1)
        check("判定できなければ「メインにいる」とは答えない（rc=4）",
              correct["前提条件: git 無し"] == 4)
        check("入場も、見られなければ作らない（rc=5）", correct["入場: git 無し"] == 5)
        check("入場は、見られなければ何も作らない", correct["入場: git 無しでも作らない"])
        check("サブディレクトリから作ってもリポジトリの中",
              correct["サブから作った場所がリポジトリの中"])
        check("サブディレクトリから作ってもリポジトリの外に作らない",
              correct["サブから作ってもリポジトリの外に作らない"])

        print("\n変異テスト（壊したのに緑なら失格）")
        for name, (script, needle, replacement) in MUTATIONS.items():
            source = script.read_text(encoding="utf-8")
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}", False)
                continue
            d = base / f"mut-{abs(hash(name))}"
            (d / "scripts").mkdir(parents=True)
            for original in (PREPARE, PRECOND):
                body = original.read_text(encoding="utf-8")
                if original == script:
                    body = body.replace(needle, replacement, 1)
                (d / "scripts" / original.name).write_text(body, encoding="utf-8")
            try:
                mutated = observe(d / "scripts" / PREPARE.name,
                                  d / "scripts" / PRECOND.name, d / "tree")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", mutated != correct)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        promises = 0
        for script in (PREPARE, PRECOND):
            body = script.read_text(encoding="utf-8")
            section = body.split("## 何を守るか")[1].split("## 何を守らないか")[0]
            promises += len([l for l in section.splitlines() if l.startswith("# - ")])
        check(f"2 本の「守る」{promises} 行に対して変異が {len(MUTATIONS)} 件",
              promises == len(MUTATIONS))

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
    print("worktree スクリプトのテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
