#!/usr/bin/env python3
r"""ある Issue の周が既に始まっているかを探し、当たったものを全部出す。

    python3 <このスキルの base ディレクトリ>/scripts/find-cycle.py <issue-number>

**置き場所に理由がある。** `dev-loop` は**どのリポジトリでも使えるスキル**なので、
**対象リポジトリの `scripts/` に置いてはならない**——そこに在るとは限らない。
**スキルと一緒に配られる場所**（スキルの base ディレクトリの下）に置く。
**一度 `scripts/find-cycle.py` に置いて PR に出し、マージ後に気づいた**（#136）。

`SKILL.md` の「途中から再開する周」が散文で書いていた探索を、**走らせる形にした**。
**判定はしない**——**当たったものを並べ、どれで再開するかは読んだ側が決める。**

## なぜスクリプトなのか（#136）

**散文のままだと、読む前に通り過ぎる。** #96 では、規約どおりの 2 パスだけ空振りして
**2 本目の worktree を作って実装をやり直した**。#110 では、探索の前提（ブランチ名に
番号が入っていること）が崩れる経路が 4 パスかけて見つかった。
**分岐が増えるたびに散文が伸び、伸びるほど読まれなくなる。**

**そして、この探索には循環がある**——**「自分が再開しているか」を知る前に、
それを知る方法を読む必要がある。** スクリプトなら、**読む前に答えが出る。**

## 探す経路（5 本。どれも落とさない）

| # | 探し方 | これが無いと何を見落とすか |
| --- | --- | --- |
| 1 | `docs/plans` `.claude/plans` を**再帰**・**パスの部分一致** | `issue-96/plan.md` のように**番号がディレクトリ名の側にある**配置（`-name` では当たらない） |
| 2 | `git worktree list` を**全件** | **ランダム名で作られた worktree**（番号でも名前でも絞れない） |
| 3 | `git branch --all` の**部分一致** | 畳んだあとに残ったブランチ。**`--all` でリモートも見る** |
| 4 | `git log --all --diff-filter=A --name-only -- '*issue-<n>*'` | **worktree もブランチも無いが、計画ファイルがコミットされている**周 |
| 5 | `git log --all --grep '#<n>'` | **計画ファイルを gitignore した**周（`Fixes #<n>` の規約に乗る） |

## 何を守り、何を守らないか

守る:

- **5 本を必ず全部走らせる**——**1 本当たっても残りを省かない。**
  **同じ Issue に 2 本以上当たることがある**（前の周の畳み残しと今回の分）ので、
  **全部見せないと選べない。**
- **部分一致の広さを隠さない**——`*96*` は `issue-960` にも `issue-1962` にも当たる。
  **当たったものをそのまま出す**（スクリプトが 1 つに決め打ちしない）。
- **リポジトリの root を自分で解決する**——相対パスに頼らないので、**どの cwd から
  走らせても同じ結果**になる。
- **「1 件も当たらなかった」と「探せなかった」を区別する**——後者は非ゼロで終わる。

守らない:

- **どれで再開するかの判断**——**出すだけ**である。計画ファイルの「周の在り処」と
  突き合わせて決めるのは読んだ側で、**記録が無ければ人間に訊く**（`SKILL.md`）。
- **`git` が無い環境**——`git` が失敗した経路は「失敗」として出す。**空と混ぜない。**
- **番号に依らない探索**——**5 本のうち 2〜5 は番号かブランチ名に乗っている。**
  **番号を含まない名前で作られ、コミットにも `#<n>` が無い周は、経路 2（全件表示）
  でしか見えない。**
- **当たったものが本当にその Issue のものか**——**部分一致なので、確かめるのは読んだ側。**
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PLAN_DIRS = ("docs/plans", ".claude/plans")


def repo_root(start=None):
    """リポジトリの root を返す。**cwd に依存しない**ための入口。"""
    out = run(["git", "rev-parse", "--show-toplevel"], cwd=start)
    if out.ok and out.text:
        return Path(out.text.splitlines()[0])
    return None


class Result:
    """1 本の探索の結果。**空と失敗を混ぜない。**"""

    def __init__(self, ok, text, error=""):
        self.ok = ok
        self.text = text
        self.error = error

    @property
    def lines(self):
        return [l for l in self.text.splitlines() if l.strip()]


def run(cmd, cwd=None):
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except OSError as exc:
        return Result(False, "", str(exc))
    if proc.returncode != 0:
        return Result(False, proc.stdout, proc.stderr.strip() or f"終了コード {proc.returncode}")
    return Result(True, proc.stdout)


def find_plans(root, number):
    """経路 1: 計画ファイル。**パスの部分一致で、再帰的に。**"""
    hits, missing = [], []
    for rel in PLAN_DIRS:
        base = root / rel
        if not base.is_dir():
            missing.append(rel)
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and number in str(path.relative_to(root)):
                hits.append(str(path.relative_to(root)))
    return hits, missing


def find_worktrees(root):
    """経路 2: worktree を**全件**。番号でも名前でも絞らない。"""
    res = run(["git", "worktree", "list"], cwd=root)
    return res


def find_branches(root, number):
    """経路 3: ブランチの部分一致。**`--all` でリモートも見る。**"""
    return run(["git", "branch", "--all", "--list", f"*{number}*"], cwd=root)


def find_plan_commits(root, number):
    """経路 4: 計画ファイルを追加したコミット。**`--name-only` を落とさない。**"""
    return run(["git", "log", "--all", "--diff-filter=A", "--name-only", "--format=",
                "--", f"*issue-{number}*"], cwd=root)


def find_issue_commits(root, number):
    """経路 5: コミットメッセージに `#<n>`。**部分一致なので広い。**"""
    return run(["git", "log", "--all", "--grep", f"#{number}", "--oneline"], cwd=root)


def report(number, root):
    """5 本を全部走らせて出す。**1 本当たっても残りを省かない。**"""
    print(f"Issue #{number} の周を探す（リポジトリ: {root}）\n")

    hit_any = False
    failures = []

    plans, missing_dirs = find_plans(root, number)
    print(f"[1] 計画ファイル（{' / '.join(PLAN_DIRS)} を再帰・パスの部分一致）")
    if plans:
        hit_any = True
        for p in plans:
            print(f"      {p}")
    else:
        print("      当たらなかった")
    for rel in missing_dirs:
        print(f"      （{rel} は存在しない）")

    wt = find_worktrees(root)
    print("\n[2] worktree（全件。番号でも名前でも絞っていない）")
    if not wt.ok:
        failures.append(("worktree list", wt.error))
        print(f"      **探せなかった**: {wt.error}")
    else:
        for line in wt.lines:
            mark = " ←" if number in line else ""
            print(f"      {line}{mark}")
        if any(number in l for l in wt.lines):
            hit_any = True

    br = find_branches(root, number)
    print(f"\n[3] ブランチ（`--all` で `*{number}*` に部分一致）")
    if not br.ok:
        failures.append(("branch --all", br.error))
        print(f"      **探せなかった**: {br.error}")
    elif br.lines:
        hit_any = True
        for line in br.lines:
            print(f"      {line.strip()}")
    else:
        print("      当たらなかった")

    pc = find_plan_commits(root, number)
    print(f"\n[4] 計画ファイルを追加したコミット（`*issue-{number}*`）")
    if not pc.ok:
        failures.append(("log --diff-filter=A", pc.error))
        print(f"      **探せなかった**: {pc.error}")
    elif pc.lines:
        hit_any = True
        for line in sorted(set(pc.lines)):
            print(f"      {line}")
    else:
        print("      当たらなかった")

    ic = find_issue_commits(root, number)
    print(f"\n[5] コミットメッセージに `#{number}`（部分一致。`#11` は `#110` にも当たる）")
    if not ic.ok:
        failures.append(("log --grep", ic.error))
        print(f"      **探せなかった**: {ic.error}")
    elif ic.lines:
        hit_any = True
        for line in ic.lines[:10]:
            print(f"      {line}")
        if len(ic.lines) > 10:
            print(f"      …ほか {len(ic.lines) - 10} 件")
    else:
        print("      当たらなかった")

    print()
    if failures:
        print("**探せなかった経路がある。「新規の周」と判定してはならない。**")
        for name, err in failures:
            print(f"  - {name}: {err}")
        return 2
    if hit_any:
        print("**当たったものがある。** どれで再開するかは、計画ファイルの「周の在り処」と")
        print("突き合わせて決めること。**記録が無ければ人間に訊く**——新しそうなほうで代用しない。")
        print("**部分一致なので、当たったものが本当にこの Issue のものかを確かめてから入ること。**")
        return 1
    print("**5 本とも当たらなかった。新規の周として始めてよい。**")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("issue", help="Issue 番号（数字だけ）")
    parser.add_argument("--root", help="リポジトリの root（既定: cwd から解決）")
    args = parser.parse_args(argv)

    if not re.fullmatch(r"\d+", args.issue):
        print(f"Issue 番号は数字だけで指定する: {args.issue!r}", file=sys.stderr)
        return 2

    root = Path(args.root) if args.root else repo_root()
    if root is None or not root.is_dir():
        print("リポジトリの root を解決できなかった。--root で指定すること。", file=sys.stderr)
        return 2

    return report(args.issue, root)


if __name__ == "__main__":
    sys.exit(main())
