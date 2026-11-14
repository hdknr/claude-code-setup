#!/usr/bin/env python3
"""`check-deps-declared.py` の回帰テスト（#996）。

    python3 scripts/test-check-deps-declared.py            # 変異は既定で 4 つまで同時に当てる
    python3 scripts/test-check-deps-declared.py --jobs 1   # 変異を 1 つずつ当てる（check-all.py --jobs 1 が渡す）

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）——`test-find-cycle.py` と同じ形で、
**`dev-loop` はどのリポジトリでも使えるスキル**なので。

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリを作り、そこだけを対象にする（`assert_not_real_repo`）。

**変異テストを含む。** 本体の docstring の「守る」の各行に変異を 1 つ以上当て、**壊したのに契約が保たれるなら失格**とする。
**変異の前に、元の本体で全部緑であること（陽性対照）を見る。**
**変異の回は最初に破れた契約で止め、変異どうしは別々のプロセスで同時に当てる**（#1021。理由は `MUTANT_JOBS_MAX` の上）。

あわせて、**Verifier の委譲文（`prompts/verifier.md`）の依存の差し込みが、表の欄を全部名指していること**と、
**`references/dependencies.md` が未検証の扱いを持つこと**を見る（受入基準 V1・V2）——欄を 1 つ落とすと赤。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop"
SCRIPT = SKILL_DIR / "scripts" / "check-deps-declared.py"
VERIFIER = SKILL_DIR / "prompts" / "verifier.md"
DEPS_DOC = SKILL_DIR / "references" / "dependencies.md"
# Verifier の表の欄（`prompts/verifier.md` が正。Issue #996 の受入基準 2 の 5 つと、名前の近い包）
TABLE_COLUMNS = ("名前", "版", "公開日", "公開者", "インストールスクリプトの有無", "名前の近い有名な包")

failures: list[str] = []

PLAN = """# 計画

## 変更範囲

触る:

- `src/`
"""


def check(name: str, cond: bool) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


def assert_not_real_repo(root: Path) -> None:
    r = root.resolve()
    assert r != REAL_REPO and not str(r).startswith(str(REAL_REPO) + os.sep), "テストが実リポジトリを対象にしている"
    assert r.is_relative_to(Path(tempfile.gettempdir()).resolve()), "テストの対象がテンポラリの外にある"


def git(root: Path, *args: str) -> str:
    # 親の GIT_*（hook の中の GIT_DIR など）を引き継ぐと、`-C root` でも偽のリポジトリではなくそちらに書く（#1028）
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-C", str(root), *args],
                          check=True, capture_output=True, text=True, env=env).stdout


def repo(root: Path, *, plan: str | None = PLAN, branch: str = "issue/7-demo",
         base_files: dict[str, str] | None = None) -> str:
    """偽のリポジトリを作り、base の SHA を返す。計画ファイルは base の後のコミットに置く（周の形）。"""
    assert_not_real_repo(root)
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    # コミットの後の `git maintenance run --auto` は切り離して走り、`.git/objects/maintenance.lock` を作っては消す——
    # 雛形を複製する `copytree` がその途中に当たると落ちる（#1028）。`.git/config` に書くので複製にも写る
    git(root, "config", "maintenance.auto", "false")
    git(root, "config", "gc.auto", "0")
    files = {"seed.txt": "seed\n", **(base_files or {})}
    for rel, body in files.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD").strip()
    git(root, "switch", "-q", "-c", branch)
    if plan is not None:
        p = root / "docs" / "plans" / "issue-7.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(plan)
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "plan")
    return base


# **土台のリポジトリは形ごとに 1 度だけ作り、複製する**（#1021）——契約 1 回で 40 近い土台を作り、1 つに `git` を 5〜6 回
# 起こしていた（1 つ 0.33 秒）。土台の形は `repo` の引数だけで決まるので、同じ引数なら中身（コミットの SHA まで）が同じ複製で足りる。
# 置き場はプロセスごとに分ける（変異の作業者は別プロセスで、同じ一時ディレクトリの下に作る）。
_TEMPLATES: dict[tuple, tuple[Path, str]] = {}


def fresh_repo(d: Path, *, plan: str | None = PLAN, branch: str = "issue/7-demo",
               base_files: dict[str, str] | None = None) -> str:
    """`repo(d, ...)` と同じリポジトリを、土台の複製で作って base の SHA を返す。"""
    assert_not_real_repo(d)
    key = (plan, branch, tuple(sorted((base_files or {}).items())))
    if key not in _TEMPLATES:
        tpl = d.parent.parent / f"tpl-{os.getpid()}" / str(len(_TEMPLATES))
        _TEMPLATES[key] = (tpl, repo(tpl, plan=plan, branch=branch, base_files=base_files))
    tpl, base = _TEMPLATES[key]
    shutil.copytree(tpl, d, symlinks=True)
    return base


def put(root: Path, rel: str, body: str = "x\n", commit: bool = False) -> None:
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(body)
    if commit:
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "work")


def run(script: Path, root: Path, *args: str, env: dict | None = None) -> tuple[int, str]:
    e = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    e.pop("GITHUB_HEAD_REF", None)
    e.pop("GITHUB_REF_NAME", None)
    e.update(env or {})
    proc = subprocess.run([sys.executable, str(script), *args], cwd=root, env=e,
                          capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def contract(script: Path, tmp: Path, tag: str) -> Iterator[tuple[str, bool]]:
    """契約を 1 ケースずつ当てて `(名前, 通ったか)` を出す。**逐次に評価する**ので、変異の回は最初に破れたところで止められる（#1021）。"""
    n = [0]

    def fresh(**kw) -> tuple[Path, str]:
        n[0] += 1
        d = tmp / f"{tag}{n[0]}"
        return d, fresh_repo(d, **kw)

    # 1) コミットした package.json・宣言なし → 1、名指す
    d, base = fresh()
    put(d, "package.json", "{}\n", commit=True)
    rc, out = run(script, d, base)
    yield from [("申告せずに足した依存のファイルで 1", rc == 1),
            ("依存のファイルを名指す", "package.json" in out),
            ("申告の書き方を案内する", "依存の追加・更新: あり" in out)]

    # 2) 宣言 `あり` → 0（陽性対照）
    d, base = fresh(plan=PLAN + "\n依存の追加・更新: あり\n")
    put(d, "package.json", "{}\n", commit=True)
    rc, out = run(script, d, base)
    yield from [("宣言が `あり` なら 0", rc == 0), ("`あり` なら Verifier の表を案内する", "Verifier" in out)]

    # 3) 箇条書きの宣言も数える
    d, base = fresh(plan=PLAN + "\n- 依存の追加・更新: あり\n")
    put(d, "package.json", "{}\n", commit=True)
    rc, _ = run(script, d, base)
    yield from [("箇条書きの `- 依存の追加・更新: あり` も宣言", rc == 0)]

    # 4) `なし`・別の値・2 本以上・フェンスの中だけ → 1
    for label, extra in (("`なし`", "\n依存の追加・更新: なし\n"),
                         ("別の値", "\n依存の追加・更新: あり（予定）\n"),
                         ("2 本以上", "\n依存の追加・更新: あり\n依存の追加・更新: あり\n"),
                         ("フェンスの中だけ", "\n```text\n依存の追加・更新: あり\n```\n")):
        d, base = fresh(plan=PLAN + extra)
        put(d, "uv.lock", commit=True)
        rc, _ = run(script, d, base)
        yield from [(f"宣言が{label}なら 1", rc == 1)]

    # 5) 未コミットの変更（追跡しているファイル）・未追跡・下の階層・消した・取得経路の設定 → 1
    d, base = fresh(base_files={"web/app/package.json": "{}\n"})
    put(d, "web/app/package.json", '{"dependencies": {"a": "1"}}\n')  # コミットしない
    rc, out = run(script, d, base)
    yield from [("未コミットの変更（下の階層の package.json）で 1", rc == 1 and "web/app/package.json" in out)]

    d, base = fresh()
    put(d, "svc/requirements-dev.txt")  # 未追跡のまま
    rc, out = run(script, d, base)
    yield from [("未追跡の requirements-dev.txt で 1", rc == 1 and "svc/requirements-dev.txt" in out)]

    d, base = fresh(base_files={"yarn.lock": "x\n"})
    (d / "yarn.lock").unlink()
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "rm")
    rc, out = run(script, d, base)
    yield from [("消した yarn.lock で 1", rc == 1 and "yarn.lock" in out)]

    for rel in ("requirements/base.txt", "dev-requirements.txt", "constraints.txt", "svc/requirements/base.in",
                "requirements-dev.in", "docs/requirements.txt", "constraints-3.8.txt", "constraints-dev.txt",
                "dev_requirements.txt", "docs/constraints.txt", "constraints.in", "ci_requirements.in",
                # Python の版の英字の接頭辞（#1012。FreeCAD-addons・cibuildwheel に在る形）
                "constraints/constraints-py38.txt", "constraints_python3.12.txt", "constraints-pyodide313.in",
                "constraints-pypy3.10.txt"):
        d, base = fresh()
        put(d, rel, commit=True)
        rc, _ = run(script, d, base)
        yield from [(f"{rel} で 1", rc == 1)]
    # 負の試料（#996 の NF1）——依存でない文書を拾わない
    for rel in ("docs/product-requirements.txt", "docs/requirements/overview.txt", "requirements/README.md",
                "docs/constraints-list.txt", "spec/requirements/functional.in", "notes/constraints-analysis.txt",
                "constraints_overview.txt", "constraints-pyproject-notes.txt", "constraints-python-notes.txt"):
        d, base = fresh()
        put(d, rel, commit=True)
        rc, _ = run(script, d, base)
        yield from [(f"文書 {rel} は依存のファイルに数えない（0）", rc == 0)]

    d, base = fresh()
    put(d, "サービス/package.json", "{}\n", commit=True)
    rc, out = run(script, d, base)
    yield from [("非 ASCII の名前のディレクトリの下の package.json で 1", rc == 1 and "サービス/package.json" in out)]

    d, base = fresh()
    put(d, ".npmrc", "registry=https://example.invalid/\n", commit=True)
    rc, _ = run(script, d, base)
    yield from [("取得経路の設定（.npmrc）を触ったら 1", rc == 1)]

    # 6) 依存のファイルが無い → 宣言の有無に依らず 0
    d, base = fresh()
    put(d, "src/a.py", commit=True)
    rc, _ = run(script, d, base)
    yield from [("依存のファイルが無ければ、宣言が無くても 0", rc == 0)]

    # 7) 計画が見つからない: 依存のファイルがあれば 2、無ければ 0
    d, base = fresh(plan=None, branch="feature/x")
    put(d, "go.mod", commit=True)
    rc, out = run(script, d, base)
    yield from [("計画が見つからず依存のファイルがあれば 2", rc == 2 and "緑ではない" in out)]
    d, base = fresh(plan=None, branch="feature/x")
    put(d, "src/a.py", commit=True)
    rc, _ = run(script, d, base)
    yield from [("計画が見つからず依存のファイルも無ければ 0", rc == 0)]

    # 8) --plan で名指す・detached でも GITHUB_HEAD_REF から当てる
    d, base = fresh(branch="feature/x", plan=None)
    put(d, "notes/plan.md", PLAN + "\n依存の追加・更新: あり\n")
    put(d, "Cargo.lock", commit=True)
    rc, _ = run(script, d, base, "--plan", "notes/plan.md")
    yield from [("--plan で名指した計画の宣言を読む", rc == 0)]
    d, base = fresh()
    put(d, "Gemfile.lock", commit=True)
    git(d, "switch", "-q", "--detach", "HEAD")
    rc, out = run(script, d, base, env={"GITHUB_HEAD_REF": "issue/7-demo"})
    yield from [("detached でも GITHUB_HEAD_REF から計画を当てる", rc == 1 and "issue-7.md" in out)]

    # 9) git が失敗（存在しない base）→ 2
    d, base = fresh()
    rc, out = run(script, d, "no-such-ref")
    yield from [("git が失敗したら 2", rc == 2)]


MUTATIONS = {
    # 守る: 宣言が `あり` でない限り 0 にしない
    "宣言の値を見ない": ('    if values[0] != "あり":\n', "    if False:\n"),
    "2 本以上を通す": ("    if len(values) > 1:\n", "    if False:\n"),
    "フェンスの中も数える": ("        if fence is not None:\n            continue\n", ""),
    "箇条書きの宣言を数えない": (r'DECLARE = re.compile(r"^(?:[-*]\s+)?依存の追加・更新:\s*(.*?)\s*$")',
                                 r'DECLARE = re.compile(r"^依存の追加・更新:\s*(.*?)\s*$")'),
    # 守る: 計画が見つからないとき、依存のファイルがあれば 0 にしない
    "計画が見つからなければ 0": ('        return 2, deps, "依存のファイルが差分にあるのに',
                                '        return 0, deps, "依存のファイルが差分にあるのに'),
    "git の失敗を 0 にする": ('        print(f"git で差分を取れなかった（base: {opts.base}）——判定していない（緑ではない）。")\n        return 2\n',
                             '        return 0\n'),
    # 守る: 未コミット・未追跡・消した・下の階層を落とさない
    "未追跡を見ない": ("    return [line for line in (diff + untracked).splitlines() if line.strip()]\n",
                       "    return [line for line in diff.splitlines() if line.strip()]\n"),
    "3 点で取る（未コミットを見ない）": ('    rc1, diff = git("diff", "--name-only", "--no-renames", base)\n',
                                       '    rc1, diff = git("diff", "--name-only", "--no-renames", f"{base}...HEAD")\n'),
    "非 ASCII のパスを引用符で包ませる": ('["git", "-c", "core.quotePath=false", *args]', '["git", *args]'),
    "requirements/ の下を見ない": ('    if (len(parts) >= 2 and parts[-2] == "requirements"', '    if (False and parts[-2] == "requirements"'),
    "requirements/ を入れ子で見ない": ('parts[-2] == "requirements" and name', 'parts[0] == "requirements" and name'),
    "requirements/ の下の .in を見ない": ('REQUIREMENTS_DIR_SUFFIXES = (".txt", ".in")', 'REQUIREMENTS_DIR_SUFFIXES = (".txt",)'),
    "requirements/ の下の何でも数える": ("and name.endswith(REQUIREMENTS_DIR_SUFFIXES)", "and True"),
    "文書のディレクトリの下の requirements/ も数える": ("            and not any(d.lower() in DOC_DIRS for d in parts[:-2])):", "            ):"),
    "constraints の版の番号の形を見ない": ('*(f"constraints{sep}[0-9]*.{ext}"', '*(f"constraints{sep}[0-9]*.no{ext}"'),
    "constraints の名前を広げる（文書を拾う）": ('"constraints.txt", "constraints.in", "setup.py"', '"constraints*.txt", "constraints*.in", "setup.py"'),
    "constraints の Python の版の接頭辞を見ない": ('*(f"constraints{sep}{py}[0-9]*.{ext}"', '*(f"constraints{sep}{py}[0-9]*.no{ext}"'),
    "Python の版の接頭辞の後ろに何でも許す（文書を拾う）": ('f"constraints{sep}{py}[0-9]*.{ext}"', 'f"constraints{sep}{py}*.{ext}"'),
    "Python の版の接頭辞で下線区切りを見ない": ('for py in PYTHON_VERSION_PREFIXES for sep in ("-", "_")', 'for py in PYTHON_VERSION_PREFIXES for sep in ("-",)'),
    "Python の版の接頭辞で .in を見ない": ('{py}[0-9]*.{ext}" for py in PYTHON_VERSION_PREFIXES for sep in ("-", "_") for ext in ("txt", "in")',
                                         '{py}[0-9]*.{ext}" for py in PYTHON_VERSION_PREFIXES for sep in ("-", "_") for ext in ("txt",)'),
    **{f"Python の版の接頭辞 {py} を見ない": ('PYTHON_VERSION_PREFIXES = ("py", "python", "pypy", "pyodide")',
                                         "PYTHON_VERSION_PREFIXES = (" + ", ".join(f'"{q}"' for q in ("py", "python", "pypy", "pyodide") if q != py) + ")")
       for py in ("py", "python", "pypy", "pyodide")},
    "constraints.in を見ない": ('"constraints.txt", "constraints.in", "setup.py"', '"constraints.txt", "setup.py"'),
    "下線区切りの用途の名前を見ない": ('f"{use}{sep}requirements.{ext}" for use in REQUIREMENT_USES for sep in ("-", "_")',
                                    'f"{use}{sep}requirements.{ext}" for use in REQUIREMENT_USES for sep in ("-",)'),
    "名前に requirements を含む何でも数える": ('               "requirements*.txt", "requirements*.in",', '               "*requirements*.txt", "*requirements*.in",'),
    "下の階層を見ない": ("    name = parts[-1]\n", "    name = path\n"),
    "消したファイルを見ない": ('    rc1, diff = git("diff", "--name-only", "--no-renames", base)\n',
                              '    rc1, diff = git("diff", "--name-only", "--no-renames", "--diff-filter=d", base)\n'),
    # 守る: 依存のファイルが無ければ 0
    "依存のファイルが無くても宣言を求める": ("    if not deps:\n        return 0, deps,", "    if False:\n        return 0, deps,"),
}


def static_checks() -> None:
    print("委譲文と規定（V1・V2）:")
    text = VERIFIER.read_text(encoding="utf-8")
    start = text.find("依存を追加・更新する周なら")
    section = text[start:start + 3000] if start >= 0 else ""
    check("verifier.md に依存の差し込みがある", bool(section))
    header = next((ln for ln in section.splitlines() if ln.strip().startswith("| 名前")), "")
    cells = [c.strip() for c in header.strip().strip("|").split("|")]
    for col in TABLE_COLUMNS:
        check(f"依存の差し込みの表の見出しの行が欄「{col}」を持つ", col in cells)
    check("依存の差し込みが公開者を _npmUser で取らせる", "_npmUser" in section)
    check("依存の差し込みがインストールスクリプトを install 系で判定させる",
          all(k in section for k in ("preinstall", "postinstall")))
    check("依存の差し込みが包を入れないよう言う", "入れないで" in section)
    doc = DEPS_DOC.read_text(encoding="utf-8")
    check("dependencies.md が未検証の扱いを持つ", "未検証" in doc)
    check("dependencies.md が宣言の行を書く", "依存の追加・更新: あり" in doc)


# **変異は別々のプロセスで同時に当て、最初に破れた契約で止める**（#1021）——直列に契約を 31 回（陽性対照 1 回・変異 30 個）
# 全部当てていて、2026-11-14 の負荷の高い `check-all.py` の中で 30 分近く終わらず、全体の律速になっていた。
# 変異の判定は「1 件でも破れたか」なので、止めても判定は変わらない。**陽性対照は止めずに全部を見る。**
# **`--jobs N` で絞る**——`check-all.py` が入れ子として親の半分を渡す（`NESTED`）。上限は `test-ledger.py` と同じ 4。
MUTANT_JOBS_MAX = max(1, min(4, os.cpu_count() or 1))
MUTANT_JOBS = MUTANT_JOBS_MAX
pool_sizes: list[int] = []


class _MutantPool(concurrent.futures.ProcessPoolExecutor):
    """変異の作業者のプール。**渡された作業者の数を `pool_sizes` に残す**（`--pool-size` が出す）。"""

    def __init__(self, max_workers, **kwargs):
        pool_sizes.append(max_workers)
        super().__init__(max_workers, **kwargs)


def _kill_one(job: tuple[int, str, str]) -> bool:
    """作業者で変異を 1 つ当て、契約が 1 件でも破れたら True。**最初に破れたところで止める。**"""
    i, mutated, tmp = job
    mutant = Path(tmp) / f"mutant{i}.py"
    mutant.write_text(mutated, encoding="utf-8")
    return any(not ok for _, ok in contract(mutant, Path(tmp) / f"m{i}", f"m{i}"))


def kill_mutations(mutations: dict[str, tuple[str, str]], src: str, tmp: Path) -> None:
    order, jobs = [], []  # order: (変異の名前, jobs の番号。当てる先が 1 箇所でなければ None)
    for i, (name, (old, new)) in enumerate(mutations.items()):
        if src.count(old) != 1:
            order.append((name, None))
            continue
        order.append((name, len(jobs)))
        jobs.append((i, src.replace(old, new), str(tmp)))
    with _MutantPool(max_workers=MUTANT_JOBS, mp_context=multiprocessing.get_context("spawn")) as pool:
        results = list(pool.map(_kill_one, jobs))
    for name, k in order:  # 出力は変異の宣言順（終わった順ではない）
        if k is None:
            check(f"変異 `{name}` の当て先が 1 箇所", False)
        else:
            check(f"変異 `{name}` を契約が捕まえる", results[k])


def check_pool_size() -> None:
    """自分を `--jobs N --pool-size` で起こし、プールに渡した作業者の数が `min(N, 上限)` かを見る
    （`test-ledger.py` の #762 と同じ形——受けた `--jobs` を使わなくても、遅く・速くなるだけで緑のままなので）。"""
    for asked in (1, 99):
        want = min(asked, MUTANT_JOBS_MAX)
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--jobs", str(asked), "--pool-size"],
                              capture_output=True, text=True, timeout=120)
        got = proc.stdout.strip()
        check(f"--jobs {asked} で変異のプールに渡す作業者は {want}（出力: {got or '空'}・終了コード {proc.returncode}）",
              proc.returncode == 0 and got == str(want))


def main() -> int:
    global MUTANT_JOBS
    parser = argparse.ArgumentParser(description="check-deps-declared.py の回帰テスト")
    parser.add_argument("--jobs", type=int, default=MUTANT_JOBS_MAX,
                        help=f"変異を同時に当てるプロセスの数（既定と上限: {MUTANT_JOBS_MAX}。1 で 1 つずつ）")
    parser.add_argument("--pool-size", action="store_true",
                        help="変異のプールに渡す作業者の数を出して終わる（試料の中で使う）")
    opts = parser.parse_args()
    if opts.jobs < 1:
        parser.error(f"--jobs は 1 以上: {opts.jobs}")
    MUTANT_JOBS = min(opts.jobs, MUTANT_JOBS_MAX)
    if opts.pool_size:
        with tempfile.TemporaryDirectory() as tmp:
            # 変異を当てる経路そのもの（`kill_mutations`）でプールを作る——変異が 0 件なので作業者は起きない
            kill_mutations({}, "", Path(tmp))
        print(pool_sizes[-1] if pool_sizes else "")
        return 0

    static_checks()
    print("変異の作業者の数:")
    check_pool_size()
    src = SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        print("陽性対照（元の本体——全部通らなければならない）:")
        for name, ok in contract(SCRIPT, root / "real", "r"):
            check(name, ok)
        print("変異（1 箇所ずつ壊す——契約が破れなければ失格）:")
        kill_mutations(MUTATIONS, src, root)
    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


if __name__ == "__main__":
    sys.exit(main())
