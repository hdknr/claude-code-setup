#!/usr/bin/env python3
"""2 つのサインオフのタグの時点で、版の共有の範囲が一致するかを照合する（提案書の関門）。

usage: python3 check-signoff.py [--repo <正本リポジトリ>] [--version <n>] [--req <タグ>] [--budget <タグ>]

**タグの命名と照合の決まりの正は `references/signoff-tags.md` である**（このプラグインの中にある）。
下の定数（タグの接頭辞・番号の書式・比べる場所）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-check-signoff.py` が突き合わせて見る**。
**版の見つけ方は同梱の `merge-versions.py` の `find_versions` を使う**（写しを作らない。決まりは `references/versions.md`）。

- タグは `v<n>/req-signoff-<k>`・`v<n>/budget-signoff-<k>`。**`--version` を省けば、作業ツリーの作業中の版
  （`docs/` の版で番号が最大のもの）のタグだけを数える。**
- タグを指定しなければ、**`<k>` を数として比べて最大のもの**を使う（`-10` は `-9` より新しい）。
  **命名に合わないタグ（`v2/req-signoff-3-fix`・`v2/req-signoff-03`・旧い `req-signoff-v3`）は数えない。**
  **指定したタグが別の版のものなら照合しない（2）**——別の版の承認を組にしない。
- **比べる場所は `docs/v1/shared/`〜`docs/v<n>/shared/` と `docs/v2/removed.csv`〜`docs/v<n>/removed.csv`**
  （v<n> の時点の共有の範囲は、前の版の `shared/` と、行を消す `removed.csv` にも依る）。
- **どちらかの時点で比べる場所にファイルが 1 つも無ければ、一致とは言わない（2）。**
  比べる中身が無くても `git diff --quiet` は 0 を返すので、それを「一致」と読まない。
- **LLM に判断させないための照合**なので、判定はすべて `git` の出力から決める。

終了コード:

- 0: 一致する（2 つの承認は同じ共有の範囲を見ていた）
- 1: 一致しない（違うファイルを全部出す）
- 2: 照合していない——git でない・git が無い・作業ツリーの版が決まりに反する／1 つも無い（`--version` を省いたとき）・
  タグが無い／片方しか無い・指定したタグが無い／命名に合わない／別の版のもの・
  どちらかの時点で比べる場所にファイルが無い（旧い構成のタグを含む）

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う（`git` は要る）。

**この照合が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **タグを付け直していないか** | 付け直した後の状態しか見えない。`references/signoff-tags.md` の「付け直さない」は運用で守る |
| **誰がタグを付けたか** | 署名を検査しない。タグを付けられる人を絞るのはリポジトリの権限 |
| **共有の範囲の外**（`requirements/`・`feasibility/`） | 2 つの承認が共通に見るのは `shared/` だけ（`references/tree.md`） |
| **タグの時点の版の並びが決まりに反するか** | 照合するのは比べる場所の中身だけ。版の並びは作業ツリーで `merge-versions.py` が見る |
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

REQ_PREFIX = "req-signoff"
BUDGET_PREFIX = "budget-signoff"
# `<n>`（版）と `<k>`（回数）は 1 から始まる整数（先頭に 0 を付けない）
NUMBER = r"([1-9][0-9]*)"
DOCS = "docs"
SHARED = "shared/"
REMOVED = "removed.csv"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


versions = _load("merge_versions", "merge-versions.py")


class Unjudged(Exception):
    """照合していない（終了コード 2）。"""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    except OSError as e:
        raise Unjudged(f"git を起動できない（{e.strerror}）。照合していない")


def tag_pattern(prefix: str, version: int) -> re.Pattern[str]:
    return re.compile(rf"v{version}/{re.escape(prefix)}-{NUMBER}")


def scope(version: int) -> list[str]:
    """比べる場所（版 1〜n の `shared/` と、版 2〜n の `removed.csv`）。"""
    paths = [f"{DOCS}/v{i}/{SHARED}" for i in range(1, version + 1)]
    return paths + [f"{DOCS}/v{i}/{REMOVED}" for i in range(2, version + 1)]


def working_version(repo: Path) -> int:
    """作業ツリーの作業中の版（番号の最大）。"""
    problems: list[str] = []
    docs = repo / DOCS
    if not docs.is_dir():
        raise Unjudged(f"作業ツリーに {DOCS}/ が無い。照合していない")
    try:
        found = versions.find_versions(docs, problems)
    except versions.Unreadable as e:
        raise Unjudged(f"{e}。照合していない")
    if problems:
        raise Unjudged("作業ツリーの版が決まりに反する（references/versions.md）: "
                       + " / ".join(problems) + "。照合していない")
    if not found:
        raise Unjudged(f"作業ツリーの {DOCS}/ に版（v1 など）が 1 つも無い。照合していない")
    return found[-1][0]


def latest(names: list[str], prefix: str, version: int) -> str | None:
    pattern = tag_pattern(prefix, version)
    numbered = [(int(m.group(1)), name) for name in names if (m := pattern.fullmatch(name))]
    return max(numbered)[1] if numbered else None


def commit_of(repo: Path, tag: str) -> str:
    result = git(repo, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}")
    if result.returncode != 0:
        raise Unjudged(f"タグ {tag} が無い（またはコミットを指していない）。照合していない")
    return result.stdout.strip()


def shared_files(repo: Path, commit: str, tag: str, paths: list[str]) -> list[str]:
    result = git(repo, "ls-tree", "-r", "--name-only", commit, "--", *paths)
    where = f"{paths[0]}（ほか {len(paths) - 1} 箇所）" if len(paths) > 1 else paths[0]
    if result.returncode != 0:
        raise Unjudged(f"{tag} の {where} を読めない: {result.stderr.strip()}。照合していない")
    files = [line for line in result.stdout.splitlines() if line]
    if not files:
        raise Unjudged(f"{tag} の時点に {where} のファイルが 1 つも無い。比べる中身が無いので照合していない")
    return files


def resolve(repo: Path, req: str | None = None, budget: str | None = None,
            version: int | None = None) -> tuple[int, list[str], dict]:
    """(終了コード, 出力する行, {"req": タグ, "budget": タグ, "req_commit": SHA, "budget_commit": SHA,
    "top": 根, "version": 版}) を返す。

    提案書の生成（`build-proposal.py`）もこの関数で照合する。
    """
    try:
        top = git(repo, "rev-parse", "--show-toplevel")
        if top.returncode != 0 or not top.stdout.strip():
            raise Unjudged(f"{repo}: git の作業ツリーでない。照合していない")
        # パス指定（`docs/v1/shared/`）は cwd から解決されるので、サブディレクトリを渡されても根で走らせる
        repo = Path(top.stdout.strip())
        if version is None:
            version = working_version(repo)
        listed = git(repo, "tag", "--list")
        if listed.returncode != 0:
            raise Unjudged(f"タグを読めない: {listed.stderr.strip()}。照合していない")
        names = listed.stdout.split()
        chosen = {}
        for key, prefix, given in (("req", REQ_PREFIX, req), ("budget", BUDGET_PREFIX, budget)):
            if given is not None:
                if not tag_pattern(prefix, version).fullmatch(given):
                    raise Unjudged(f"指定したタグ {given!r} が版 v{version} の命名"
                                   f"（v{version}/{prefix}-<k>）に合わない。照合していない")
                chosen[key] = given
            else:
                found = latest(names, prefix, version)
                if found is None:
                    raise Unjudged(f"v{version}/{prefix}-<k> のタグが 1 つも無い。照合していない")
                chosen[key] = found
        paths = scope(version)
        info = dict(chosen, top=str(repo), version=version)
        for key in ("req", "budget"):
            info[f"{key}_commit"] = commit_of(repo, chosen[key])
        for key in ("req", "budget"):
            shared_files(repo, info[f"{key}_commit"], chosen[key], paths)
    except Unjudged as e:
        return 2, [str(e)], {}

    pair = f"{info['req']}（{info['req_commit'][:7]}）と {info['budget']}（{info['budget_commit'][:7]}）"
    where = f"v1〜v{version} の {SHARED}" + (f" と {REMOVED}" if version > 1 else "")
    diff = git(repo, "diff", "--name-status", info["req_commit"], info["budget_commit"], "--", *paths)
    if diff.returncode != 0:
        return 2, [f"{where} を比べられない: {diff.stderr.strip()}。照合していない"], {}
    changed = [line for line in diff.stdout.splitlines() if line]
    if changed:
        lines = [f"一致しない: {pair} で {where} が違う（{len(changed)} 件）"]
        lines += [f"    {line}" for line in changed]
        lines.append("2 つの承認は別の範囲を見ていた。どちらかを取り直す（references/signoff-tags.md）")
        return 1, lines, info
    return 0, [f"一致する: {pair} の {where} は同じ"], info


def positive(text: str) -> int:
    """`--version` の値（1 以上・先頭に 0 を付けない）。"""
    if not re.fullmatch(NUMBER, text):
        raise argparse.ArgumentTypeError(f"{text!r} は版の番号（1 以上・先頭に 0 を付けない）でない")
    return int(text)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument("--version", type=positive)
    parser.add_argument("--req")
    parser.add_argument("--budget")
    args = parser.parse_args(argv)
    code, lines, _ = resolve(args.repo, args.req, args.budget, args.version)
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
