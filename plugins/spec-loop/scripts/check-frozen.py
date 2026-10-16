#!/usr/bin/env python3
"""リリースした版（凍結した版）が直されていないかを確かめる。

usage: python3 check-frozen.py [--repo <正本リポジトリ>]

**決まりの正は `references/versions.md` である**（このプラグインの中にある）。
下の定数（リリースのタグの命名・版の置き場所）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-check-frozen.py` が突き合わせて見る**。

- 命名に合うタグ `release-v<n>`（`n` は 1 以上・先頭に 0 を付けない）ごとに、**タグの時点と HEAD で
  `docs/v<n>/` が同じか**（`git diff --name-status`）と、**作業ツリーに `docs/v<n>/` の未コミット・未追跡の変更が
  無いか**（`git status --porcelain --untracked-files=all`）を見る。**命名に合わないタグ（`release-v02`・`release-v2-fix`）は数えない。**
- **タグの時点に `docs/v<n>/` のファイルが 1 つも無ければ、凍結の確かめようが無い（2）**——比べる中身が無くても
  `git diff` は「差分なし」を返すので、それを「直されていない」と読まない。
- **リリースのタグが 1 つも無ければ 0**（凍結した版が無い）。出力もそう言う。
- 判定はすべて `git` の出力から決める。

終了コード:

- 0: 凍結した版は直されていない（凍結した版が無いときも 0。出力で区別する）
- 1: 直されている（違うファイルを版ごとに全部出す）
- 2: 判定していない——git でない・git が無い・HEAD が無い・タグの時点に `docs/v<n>/` が無い

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う（`git` は要る）。
CI で走らせるなら、タグを取得できるよう履歴をすべて取る（GitHub Actions なら `actions/checkout` に `fetch-depth: 0`）。

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **リリースのタグを付け直していないか** | 付け直した後の状態しか見えない。「付け直さない」は運用で守る |
| **リリースのタグを付け忘れた版** | タグが無い版は凍結していない扱い。どの版をリリースしたかは人間が決める |
| **`.gitignore` で無視したファイル** | git が見ないものは比べられない |
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

RELEASE = re.compile(r"release-v([1-9][0-9]*)")
DOCS = "docs"


class Unjudged(Exception):
    """判定していない（終了コード 2）。"""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    except OSError as e:
        raise Unjudged(f"git を起動できない（{e.strerror}）。判定していない")


def releases(names: list[str]) -> list[tuple[int, str]]:
    """命名に合うリリースのタグ（版の番号の順）。"""
    return sorted((int(m.group(1)), name) for name in names if (m := RELEASE.fullmatch(name)))


def check(repo: Path) -> tuple[int, list[str]]:
    try:
        top = git(repo, "rev-parse", "--show-toplevel")
        if top.returncode != 0 or not top.stdout.strip():
            raise Unjudged(f"{repo}: git の作業ツリーでない。判定していない")
        # パス指定（`docs/v1/`）は cwd から解決されるので、サブディレクトリを渡されても根で走らせる
        repo = Path(top.stdout.strip())
        head = git(repo, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
        if head.returncode != 0:
            raise Unjudged("HEAD が無い（コミットが 1 つも無い）。判定していない")
        listed = git(repo, "tag", "--list")
        if listed.returncode != 0:
            raise Unjudged(f"タグを読めない: {listed.stderr.strip()}。判定していない")
        found = releases(listed.stdout.split())
        if not found:
            return 0, ["凍結した版が無い（release-v<n> のタグが 1 つも無い）。確かめるものが無い"]

        changed: list[str] = []
        for number, tag in found:
            path = f"{DOCS}/v{number}/"
            commit = git(repo, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}")
            if commit.returncode != 0:
                raise Unjudged(f"タグ {tag} がコミットを指していない。判定していない")
            sha = commit.stdout.strip()
            files = git(repo, "ls-tree", "-r", "--name-only", sha, "--", path)
            if files.returncode != 0:
                raise Unjudged(f"{tag} の {path} を読めない: {files.stderr.strip()}。判定していない")
            if not [line for line in files.stdout.splitlines() if line]:
                raise Unjudged(f"{tag} の時点に {path} のファイルが 1 つも無い。比べる中身が無いので判定していない")
            diff = git(repo, "diff", "--name-status", sha, "HEAD", "--", path)
            status = git(repo, "status", "--porcelain", "--untracked-files=all", "--", path)
            for result, what in ((diff, "比べられない"), (status, "作業ツリーを読めない")):
                if result.returncode != 0:
                    raise Unjudged(f"{tag} の {path} を{what}: {result.stderr.strip()}。判定していない")
            lines = [f"    コミット済み: {line}" for line in diff.stdout.splitlines() if line]
            lines += [f"    作業ツリー:   {line}" for line in status.stdout.splitlines() if line]
            if lines:
                changed.append(f"{path} が {tag}（{sha[:7]}）から直されている（{len(lines)} 件）")
                changed += lines
    except Unjudged as e:
        return 2, [str(e)]

    names = "・".join(tag for _, tag in found)
    if changed:
        return 1, changed + ["リリースした版は直さない。変えたいことは作業中の版に差分として置く（references/versions.md）"]
    return 0, [f"凍結した版は直されていない（{names}）"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", type=Path)
    args = parser.parse_args(argv)
    code, lines = check(args.repo)
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
