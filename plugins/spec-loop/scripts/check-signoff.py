#!/usr/bin/env python3
"""2 つのサインオフのタグの時点で `docs/shared/` が一致するかを照合する（提案書の関門）。

usage: python3 check-signoff.py [--repo <正本リポジトリ>] [--req <タグ>] [--budget <タグ>]

**タグの命名と照合の決まりの正は `references/signoff-tags.md` である**（このプラグインの中にある）。
下の定数（タグの接頭辞・番号の書式・比べる場所）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-check-signoff.py` が突き合わせて見る**。

- タグを指定しなければ、**`<n>` を数として比べて最大のもの**を使う（`v10` は `v9` より新しい）。
  **命名に合わないタグ（`req-signoff-v3-fix`・`req-signoff-v03`）は数えない。**
- **どちらかの時点で `docs/shared/` にファイルが 1 つも無ければ、一致とは言わない（2）。**
  比べる中身が無くても `git diff --quiet` は 0 を返すので、それを「一致」と読まない。
- **LLM に判断させないための照合**なので、判定はすべて `git` の出力から決める。

終了コード:

- 0: 一致する（2 つの承認は同じ `docs/shared/` を見ていた）
- 1: 一致しない（違うファイルを全部出す）
- 2: 照合していない——git でない・git が無い・タグが無い／片方しか無い・指定したタグが無い／命名に合わない・
  どちらかの時点で `docs/shared/` が無い

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う（`git` は要る）。

**この照合が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **タグを付け直していないか** | 付け直した後の状態しか見えない。`references/signoff-tags.md` の「付け直さない」は運用で守る |
| **誰がタグを付けたか** | 署名を検査しない。タグを付けられる人を絞るのはリポジトリの権限 |
| **`docs/shared/` の外**（`requirements/`・`feasibility/`） | 2 つの承認が共通に見るのは `shared/` だけ（`references/tree.md`） |
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REQ_PREFIX = "req-signoff"
BUDGET_PREFIX = "budget-signoff"
# `<n>` は 1 から始まる整数（先頭に 0 を付けない）
VERSION = r"v([1-9][0-9]*)"
SHARED = "docs/shared/"


class Unjudged(Exception):
    """照合していない（終了コード 2）。"""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    except OSError as e:
        raise Unjudged(f"git を起動できない（{e.strerror}）。照合していない")


def tag_pattern(prefix: str) -> re.Pattern[str]:
    return re.compile(rf"{re.escape(prefix)}-{VERSION}")


def latest(names: list[str], prefix: str) -> str | None:
    pattern = tag_pattern(prefix)
    numbered = [(int(m.group(1)), name) for name in names if (m := pattern.fullmatch(name))]
    return max(numbered)[1] if numbered else None


def commit_of(repo: Path, tag: str) -> str:
    result = git(repo, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}")
    if result.returncode != 0:
        raise Unjudged(f"タグ {tag} が無い（またはコミットを指していない）。照合していない")
    return result.stdout.strip()


def shared_files(repo: Path, commit: str, tag: str) -> list[str]:
    result = git(repo, "ls-tree", "-r", "--name-only", commit, "--", SHARED)
    if result.returncode != 0:
        raise Unjudged(f"{tag} の {SHARED} を読めない: {result.stderr.strip()}。照合していない")
    files = [line for line in result.stdout.splitlines() if line]
    if not files:
        raise Unjudged(f"{tag} の時点に {SHARED} のファイルが 1 つも無い。比べる中身が無いので照合していない")
    return files


def resolve(repo: Path, req: str | None = None, budget: str | None = None) -> tuple[int, list[str], dict[str, str]]:
    """(終了コード, 出力する行, {"req": タグ, "budget": タグ, "req_commit": SHA, "budget_commit": SHA, "top": 根}) を返す。

    提案書の生成（`build-proposal.py`）もこの関数で照合する。
    """
    try:
        top = git(repo, "rev-parse", "--show-toplevel")
        if top.returncode != 0 or not top.stdout.strip():
            raise Unjudged(f"{repo}: git の作業ツリーでない。照合していない")
        # パス指定（`docs/shared/`）は cwd から解決されるので、サブディレクトリを渡されても根で走らせる
        repo = Path(top.stdout.strip())
        listed = git(repo, "tag", "--list")
        if listed.returncode != 0:
            raise Unjudged(f"タグを読めない: {listed.stderr.strip()}。照合していない")
        names = listed.stdout.split()
        chosen = {}
        for key, prefix, given in (("req", REQ_PREFIX, req), ("budget", BUDGET_PREFIX, budget)):
            if given is not None:
                if not tag_pattern(prefix).fullmatch(given):
                    raise Unjudged(f"指定したタグ {given!r} が命名（{prefix}-v<n>）に合わない。照合していない")
                chosen[key] = given
            else:
                found = latest(names, prefix)
                if found is None:
                    raise Unjudged(f"{prefix}-v<n> のタグが 1 つも無い。照合していない")
                chosen[key] = found
        info = dict(chosen, top=str(repo))
        for key in ("req", "budget"):
            info[f"{key}_commit"] = commit_of(repo, chosen[key])
        for key in ("req", "budget"):
            shared_files(repo, info[f"{key}_commit"], chosen[key])
    except Unjudged as e:
        return 2, [str(e)], {}

    pair = f"{info['req']}（{info['req_commit'][:7]}）と {info['budget']}（{info['budget_commit'][:7]}）"
    diff = git(repo, "diff", "--name-status", info["req_commit"], info["budget_commit"], "--", SHARED)
    if diff.returncode != 0:
        return 2, [f"{SHARED} を比べられない: {diff.stderr.strip()}。照合していない"], {}
    changed = [line for line in diff.stdout.splitlines() if line]
    if changed:
        lines = [f"一致しない: {pair} で {SHARED} が違う（{len(changed)} 件）"]
        lines += [f"    {line}" for line in changed]
        lines.append("2 つの承認は別の範囲を見ていた。どちらかを取り直す（references/signoff-tags.md）")
        return 1, lines, info
    return 0, [f"一致する: {pair} の {SHARED} は同じ"], info


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument("--req")
    parser.add_argument("--budget")
    args = parser.parse_args(argv)
    code, lines, _ = resolve(args.repo, args.req, args.budget)
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
