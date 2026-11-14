#!/usr/bin/env python3
"""依存の定義・lockfile・取得経路の設定を触ったのに、計画で申告していない周を赤くする（#996）。

    python3 <このスキルの base ディレクトリ>/scripts/check-deps-declared.py <base> [--plan <計画ファイル>]

**周が PR を作る前に、worktree を cwd にして素の 1 行で呼ぶ**（`SKILL.md` 手順 6。終了コードで分岐する）。
`<base>` は周の base（計画ファイルの「周の在り処」の SHA）。**main を取り込んだ後は、`SKILL.md` 手順 4 の式（`git merge-base <切った元の参照> HEAD`）を当て直した SHA を渡す**
——記録した古い SHA のままだと、main が足した依存のファイルがこの周の変更に見えて 1 になる。

## なぜ要るか

Verifier と `/code-review` は差分を受入基準に照らして読むが、**追加された包そのものが正規のものか**
（タイポスクワッティング・乗っ取られた正規の包・公開直後の悪性の版）は見ない——差分の上では `package.json` の 1 行と
lockfile の更新にしか見えない。**周が依存を足したことを計画に申告させ、申告した周だけに Verifier の包ごとの表を求める**
（`references/dependencies.md`）。**申告せずに足した周は、その表を求める経路に乗らない**——だから黙って足したら赤くする。

## 読むもの

- **差分**: `git diff --name-only --no-renames <base>`（**2 点**——未コミットの変更も入る）と、未追跡のファイル
  （`git ls-files --others --exclude-standard`）。消したファイルも入る。
- **依存のファイル**: パスの最後の要素が `DEPENDENCY_FILES` のどれかに当たるもの（置き場所は問わない——モノレポの下の階層も当たる）。
  依存の定義・lockfile のほかに、**取得経路の設定**（`.npmrc` など）も入る——レジストリの向き先を変えるのも、足す包を変えるのと同じ重さである。
- **計画ファイル**: `--plan`、無ければブランチ名 `issue/<n>-…` から `docs/plans/issue-<n>.md`・`.claude/plans/issue-<n>.md`。
  CI の detached HEAD では `GITHUB_HEAD_REF`・`GITHUB_REF_NAME` を先に見る。
- **宣言**: 計画ファイルの行頭の `依存の追加・更新: あり`（箇条書きの `- ` は前に置いてよい。コードフェンスの中は数えない）。
  **書き方の原本は `references/dependencies.md`**。

## 終了コード

- **0**: 依存のファイルが差分に無い、または宣言が `あり`（宣言が `あり` なら、Verifier に表を求めることを出力で言う）
- **1**: 依存のファイルが差分にあるのに、宣言が無い・`あり` でない・2 本以上ある
- **2**: 判定できない——git が失敗した、または依存のファイルが差分にあるのに計画ファイルが見つからない（**緑ではない**）

## 何を守り、何を守らないか

守る:

- **依存のファイルが差分にあれば、宣言が `あり` でない限り 0 にしない**——`なし`・別の値・2 本以上・フェンスの中だけ、のどれも 1
- **計画が見つからないとき、依存のファイルがあれば 0 にしない**（2）
- **未コミットの変更・未追跡のファイル・消したファイル・下の階層の依存のファイル・非 ASCII の名前のディレクトリの下の依存のファイルを落とさない**
- **依存のファイルが差分に無ければ、宣言の有無に依らず 0**——宣言だけで赤くしない

守らない:

- **宣言の真偽**——`あり` と書けば通る。足した包が安全かは Verifier の表が見る（`references/dependencies.md`）
- **`触る:` のパターンの名前**——判定は差分だけ。依存のファイルを `触る:` に書いても、差分に現れるまでは何も言わない
- **`DEPENDENCY_FILES` に無い名前**——ここに無い生態系の依存のファイル・独自の名前の requirements（`deps/base.in`・一覧に無い用途の `<用途>-requirements.txt` など）は見えない。**文書を拾わないために絞っている**——見るのは `requirements*.txt`・`requirements*.in`・`constraints.txt`・`constraints.in`・版の番号（数字で始まる形）か、Python の版を表す接頭辞（`py`・`python`・`pypy`・`pyodide`）の直後に数字が続く形（`constraints-py38.txt`・`constraints_python3.12.txt`）か、決まった用途の付いた `constraints-<…>.txt`・`.in`（区切りは `-` か `_`。`constraints-pyproject-notes.txt` のように接頭辞の直後が数字でないものは見ない）・決まった用途の `<用途>-requirements.txt`・`<用途>_requirements.txt` と、文書のディレクトリ（`docs`・`spec` など）の下でない `requirements/` の中の `.txt`・`.in`
- **差分の中身**——lockfile のどの包が増えたかは読まない（増えた包は Verifier が差分から数える）

標準ライブラリのみ。
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

# `<用途>-requirements.txt`・`constraints-<用途>.txt` の用途の名前（決まった名前だけ——文書を拾わない。#996 の NF1・D-R7）
REQUIREMENT_USES = ("dev", "test", "tests", "ci", "build", "docs", "lint", "base", "local", "prod", "production", "optional")

# `constraints-py38.txt`・`constraints-python312.txt` の Python の版の接頭辞（直後に数字が続くときだけ——`constraints-pyproject-notes.txt` を拾わない。#1012）
PYTHON_VERSION_PREFIXES = ("py", "python", "pypy", "pyodide")

# 依存の定義・lockfile・取得経路の設定（パスの最後の要素で照合する。glob）。
# `check-unattended-env.py` の「依存の取得経路」もここを読む——一覧を 2 箇所に置かない。
DEPENDENCY_FILES = {
    "npm": ("package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml",
            "pnpm-workspace.yaml", "yarn.lock", "bun.lock", "bun.lockb"),
    "python": ("pyproject.toml", "uv.lock", "poetry.lock", "Pipfile", "Pipfile.lock",
               "requirements*.txt", "requirements*.in", "constraints.txt", "constraints.in", "setup.py", "setup.cfg",
               # constraints は版の番号か決まった用途の名前の付いたものだけ——`constraints-analysis.txt` のような文書を拾わない（#996 の D-R7）
               *(f"constraints{sep}[0-9]*.{ext}" for sep in ("-", "_") for ext in ("txt", "in")),
               # Python の版を英字の接頭辞で書いたもの（FreeCAD-addons の `constraints-py38.txt`・cibuildwheel の `constraints-pyodide313.txt`。#1012）
               *(f"constraints{sep}{py}[0-9]*.{ext}" for py in PYTHON_VERSION_PREFIXES for sep in ("-", "_") for ext in ("txt", "in")),
               # `<用途>-requirements.txt` は決まった用途の名前だけ——`product-requirements.txt` のような文書を拾わない（#996 の NF1）
               *(f"{use}{sep}requirements.{ext}" for use in REQUIREMENT_USES for sep in ("-", "_") for ext in ("txt", "in")),
               *(f"constraints{sep}{use}.{ext}" for use in REQUIREMENT_USES for sep in ("-", "_") for ext in ("txt", "in"))),
    "go": ("go.mod", "go.sum"),
    "rust": ("Cargo.toml", "Cargo.lock"),
    "ruby": ("Gemfile", "Gemfile.lock", "*.gemspec"),
    "php": ("composer.json", "composer.lock"),
    "取得経路の設定": (".npmrc", ".yarnrc", ".yarnrc.yml", "bunfig.toml", "uv.toml", "pip.conf"),
}

DECLARE = re.compile(r"^(?:[-*]\s+)?依存の追加・更新:\s*(.*?)\s*$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
PLAN_TEMPLATES = ("docs/plans/issue-{}.md", ".claude/plans/issue-{}.md")


# `requirements/base.txt` の形（ディレクトリの名前が requirements で、中の .txt・.in）も Python の依存のファイルに数える。
# **ただし文書のディレクトリの下の `requirements/` は数えない**——`docs/requirements/overview.txt` は要求の文書である（#996 の NF1）
REQUIREMENTS_DIR_SUFFIXES = (".txt", ".in")
DOC_DIRS = ("docs", "doc", "documentation", "spec", "specs")


def ecosystem_of(path: str) -> str | None:
    """依存のファイルなら生態系（`DEPENDENCY_FILES` の鍵）、そうでなければ None。"""
    parts = path.split("/")
    name = parts[-1]
    for eco, pats in DEPENDENCY_FILES.items():
        if any(fnmatch.fnmatchcase(name, pat) for pat in pats):
            return eco
    if (len(parts) >= 2 and parts[-2] == "requirements" and name.endswith(REQUIREMENTS_DIR_SUFFIXES)
            and not any(d.lower() in DOC_DIRS for d in parts[:-2])):
        return "python"
    return None


def is_dependency_file(path: str) -> bool:
    return ecosystem_of(path) is not None


def dependency_files(paths) -> list[str]:
    return sorted({p for p in paths if is_dependency_file(p)})


def declarations(text: str) -> list[str]:
    """計画ファイルの宣言の値を、出てきた順に返す。**コードフェンスの中は数えない。**"""
    values: list[str] = []
    fence = None
    for line in text.splitlines():
        m = FENCE.match(line)
        if m:
            mark = m.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence) and not line.strip()[len(mark):].strip():
                fence = None
            continue
        if fence is not None:
            continue
        d = DECLARE.match(line)
        if d:
            values.append(d.group(1))
    return values


def judge(paths, plan_text: str | None) -> tuple[int, list[str], str]:
    """(終了コード, 依存のファイル, 理由)。`check-plan-scope.py` もこれを読む（式を 1 箇所に置く）。

    `plan_text` が None なら計画が見つからなかった。"""
    deps = dependency_files(paths)
    if not deps:
        return 0, deps, "依存のファイルは差分に無い"
    if plan_text is None:
        return 2, deps, "依存のファイルが差分にあるのに、計画ファイルが見つからない——申告を判定できない（緑ではない）"
    values = declarations(plan_text)
    if not values:
        return 1, deps, "計画に `依存の追加・更新: あり` の行が無い"
    if len(values) > 1:
        return 1, deps, f"計画に `依存の追加・更新:` の行が {len(values)} 本ある（1 本だけ置く）"
    if values[0] != "あり":
        return 1, deps, f"計画の宣言が `あり` でない（`{values[0]}`）"
    return 0, deps, "計画に `依存の追加・更新: あり` がある——Verifier に包ごとの表を求める（references/dependencies.md）"


def git(*args: str) -> tuple[int, str]:
    # core.quotePath=false: 非 ASCII のパスを "\343…" と引用符で包ませない（包むと最後の要素が名前に当たらない）
    proc = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def changed_paths(base: str) -> list[str] | None:
    rc1, diff = git("diff", "--name-only", "--no-renames", base)
    rc2, untracked = git("ls-files", "--others", "--exclude-standard")
    if rc1 != 0 or rc2 != 0:
        return None
    return [line for line in (diff + untracked).splitlines() if line.strip()]


def branch_name() -> str:
    for env in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        v = os.environ.get(env, "").strip()
        if v and v != "HEAD":
            return v
    rc, out = git("rev-parse", "--abbrev-ref", "HEAD")
    name = out.strip() if rc == 0 else ""
    return "" if name == "HEAD" else name


def find_plan(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = root / p
        return p if p.is_file() else None
    m = re.match(r"^issue/(\d+)", branch_name())
    if not m:
        return None
    for template in PLAN_TEMPLATES:
        p = root / template.format(m.group(1))
        if p.is_file():
            return p
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="依存のファイルを触る周が計画で申告しているか（#996）")
    ap.add_argument("base", help="周の base（SHA か参照）")
    ap.add_argument("--plan", help="計画ファイル（既定: ブランチ名 issue/<n>-… から引く）")
    opts = ap.parse_args(argv)

    rc, top = git("rev-parse", "--show-toplevel")
    paths = changed_paths(opts.base) if rc == 0 else None
    if paths is None:
        print(f"git で差分を取れなかった（base: {opts.base}）——判定していない（緑ではない）。")
        return 2
    root = Path(top.strip())
    plan = find_plan(root, opts.plan)
    plan_text = None
    if plan is not None:
        try:
            plan_text = plan.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"計画ファイル {plan} を読めなかった: {e}——判定していない（緑ではない）。")
            return 2
    code, deps, reason = judge(paths, plan_text)
    print(f"計画: {plan if plan else '(見つからない)'} / 差分: {len(paths)} ファイル / 依存のファイル: {len(deps)}")
    for d in deps:
        print(f"  - {d}")
    print(reason)
    if code == 1:
        print("依存を追加・更新するなら、計画ファイルに `依存の追加・更新: あり` を 1 行書く——"
              "書き方と、その周で増える手順（Verifier の表・不在の周）は references/dependencies.md を正とする。")
    return code


if __name__ == "__main__":
    sys.exit(main())
