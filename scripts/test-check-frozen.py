#!/usr/bin/env python3
"""`check-frozen.py`（リリースした版が直されていないか）の回帰テスト。

    python3 scripts/test-check-frozen.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-signoff.py` と同じ形。

見るもの:

1. **凍結した版を直したら非ゼロ（1）**——コミット済みの変更・追加・削除・**未コミットの変更**・**未追跡のファイル**。
   **リリースしていない版（作業中の版）を直すのは通す。**
2. **直していなければ通す**（陽性対照）。**リリースのタグが無ければ 0 で、そう言う。**
3. **命名に合わないリリースのタグ（`release-v02`・`release-v2-fix`）は数えない。**
4. **判定できない形を 0 にしない（2）**——タグの時点に `docs/v<n>/` が無い・タグがコミットを指さない・
   HEAD が無い・git でない・**浅い clone**（`actions/checkout` の既定。タグが見えない——
   同じ元からの深い clone では判定できることを陽性対照にする）。
4'. **想定外の例外も 2 で、トレースバックの 1 にしない。`-OO`（docstring が無い）で引数なしに呼んでも想定外の例外にならない**（#286）。
   **想定外の例外を作る入力は無い**——読むのは git の出力だけで、CSV も JSON も読まない。`subprocess.run` を差し替えて作る。
5. **本体の定数が `references/versions.md` と一致する**（写しのずれ）。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料の git リポジトリはすべて一時ディレクトリに作り、
`HOME` と `GIT_CONFIG_GLOBAL` を差し替えて利用者の git 設定を読まない。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-frozen.py"
REFERENCE = PLUGIN / "references" / "versions.md"

QA = "docs/v1/shared/qa.csv"
QA2 = "docs/v2/shared/qa.csv"

# 手順: ("w", パス, 中身) 書いて add／("wu", パス, 中身) 書くだけ（未追跡・未ステージ）／("rm", パス)／("c",) commit／
# ("t", 名前) タグ／("tt", 名前) ツリーを指すタグ。None なら git でないディレクトリ。[] なら init だけ（HEAD が無い）
Steps = list[tuple[str, ...]] | None
RELEASED = [("w", QA, "a\n"), ("c",), ("t", "release-v1")]

# (名前, 手順, 期待する終了コード, 出力に含まれるべき文字列)
CASES: list[tuple[str, Steps, int, str]] = [
    ("直していない", RELEASED + [("w", QA2, "b\n"), ("c",)], 0, "凍結した版は直されていない（release-v1）"),
    ("タグが無い", [("w", QA, "a\n"), ("c",)], 0, "凍結した版が無い"),
    ("作業中の版を直す", RELEASED + [("w", QA2, "b\n"), ("c",), ("w", QA2, "c\n"), ("c",), ("wu", QA2, "d\n")],
     0, "直されていない"),
    ("コミット済みの変更", RELEASED + [("w", QA, "x\n"), ("c",)], 1, "コミット済み: M\tdocs/v1/shared/qa.csv"),
    ("コミット済みの追加", RELEASED + [("w", "docs/v1/spec/a.md", "x\n"), ("c",)], 1, "A\tdocs/v1/spec/a.md"),
    ("コミット済みの削除", RELEASED + [("rm", QA), ("w", QA2, "b\n"), ("c",)], 1, "D\tdocs/v1/shared/qa.csv"),
    ("未コミットの変更", RELEASED + [("wu", QA, "x\n")], 1, "作業ツリー:"),
    ("未追跡のファイル", RELEASED + [("wu", "docs/v1/spec/new.md", "x\n")], 1, "docs/v1/spec/new.md"),
    ("2 つ目の版だけ直す", RELEASED + [("w", QA2, "b\n"), ("c",), ("t", "release-v2"), ("w", QA2, "x\n"), ("c",)],
     1, "docs/v2/ が release-v2"),
    ("命名に合わないタグを数えない", RELEASED + [("w", QA2, "b\n"), ("c",), ("t", "release-v02"), ("t", "release-v2-fix"),
                                         ("w", QA2, "x\n"), ("c",)], 0, "直されていない（release-v1）"),
    ("サブディレクトリから", RELEASED + [("w", QA, "x\n"), ("c",), ("arg", "--repo", "docs")], 1, "直されている"),
    ("タグの時点に版が無い", [("w", "README.md", "x\n"), ("c",), ("t", "release-v1"), ("w", QA, "a\n"), ("c",)],
     2, "release-v1 の時点に docs/v1/ のファイルが 1 つも無い"),
    ("タグがツリーを指す", [("w", QA, "a\n"), ("c",), ("tt", "release-v1")], 2, "コミットを指していない"),
    # actions/checkout の既定（--depth=1・タグなし）で取った clone——タグが見えないのを「凍結した版が無い」と読まない
    ("浅い clone", RELEASED + [("w", QA, "x\n"), ("c",), ("shallow",)], 2, "浅い clone である"),
    # 陽性対照: 同じ元から履歴とタグをすべて取った clone は判定できる（浅いかどうかの検査が clone そのものを拒まない）
    ("深い clone", RELEASED + [("w", QA, "x\n"), ("c",), ("deep",)], 1, "直されている"),
    ("HEAD が無い", [], 2, "HEAD が無い"),
    ("git でない", None, 2, "作業ツリーでない"),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("命名を前方一致で見る", "if (m := RELEASE.fullmatch(name))", "if (m := RELEASE.match(name))", "命名に合わないタグを数えない"),
    ("先頭の 0 を許す", 'RELEASE = re.compile(r"release-v([1-9][0-9]*)")', 'RELEASE = re.compile(r"release-v([0-9]+)")',
     "命名に合わないタグを数えない"),
    ("コミット済みの差分を見ない", 'lines = [f"    コミット済み: {line}" for line in diff.stdout.splitlines() if line]',
     "lines = []", "コミット済みの変更"),
    ("作業ツリーを見ない", 'lines += [f"    作業ツリー:   {line}" for line in status.stdout.splitlines() if line]',
     "lines += []", "未コミットの変更"),
    ("未追跡を見ない", '"--untracked-files=all", ', '"--untracked-files=no", ', "未追跡のファイル"),
    ("版の外まで比べる", 'diff = git(repo, "diff", "--name-status", sha, "HEAD", "--", path)',
     'diff = git(repo, "diff", "--name-status", sha, "HEAD")', "直していない"),
    ("どの版も v1 と比べる", 'path = f"{DOCS}/v{number}/"', 'path = f"{DOCS}/v1/"', "2 つ目の版だけ直す"),
    ("空の版を判定する", "            if not [line for line in files.stdout.splitlines() if line]:",
     "            if False:", "タグの時点に版が無い"),
    ("根で走らせない", "        repo = Path(top.stdout.strip())\n", "", "サブディレクトリから"),
    ("コミットに剥がさない", 'f"refs/tags/{tag}^{{commit}}"', 'f"refs/tags/{tag}"', "タグがツリーを指す"),
    ("HEAD を見ない", '            raise Unjudged("HEAD が無い', '            pass  # ("HEAD が無い', "HEAD が無い"),
    ("git でないのを見ない", "if top.returncode != 0 or not top.stdout.strip():", "if False:", "git でない"),
    ("直していても 0", "    if changed:\n", "    if False:\n", "コミット済みの変更"),
    ("浅い clone を見ない", '        if shallow.stdout.strip() == "true":\n', "        if False:\n", "浅い clone"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def sandbox_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_DATE="2026-01-01T00:00:00Z", GIT_COMMITTER_DATE="2026-01-01T00:00:00Z")
    return env


def run_git(repo: Path, env: dict[str, str], *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com",
                    "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                   check=True, capture_output=True, env=env)


def build_repo(root: Path, steps: Steps, env: dict[str, str]) -> list[str]:
    """試料を作り、本体に渡す追加の引数を返す。"""
    assert_in_tmp(root)
    root.mkdir(parents=True)
    (root / "docs").mkdir()
    if steps is None:
        return []
    run_git(root, env, "init", "-q", "-b", "main")
    extra: list[str] = []
    for step in steps:
        kind = step[0]
        if kind in ("w", "wu"):
            path = root / step[1]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(step[2], encoding="utf-8")
            if kind == "w":
                run_git(root, env, "add", "-A")
        elif kind == "rm":
            run_git(root, env, "rm", "-q", step[1])
        elif kind == "c":
            run_git(root, env, "commit", "-q", "-m", "step")
        elif kind == "t":
            run_git(root, env, "tag", step[1])
        elif kind == "tt":
            run_git(root, env, "tag", step[1], "HEAD^{tree}")
        elif kind in ("shallow", "deep"):
            # 作った履歴を元にして clone し直す（浅い: actions/checkout の既定と同じ --depth=1・タグなし）
            source = root.with_name(root.name + "-src")
            root.rename(source)
            options = ["--depth=1", "--no-tags"] if kind == "shallow" else []
            subprocess.run(["git", "clone", "-q", *options, f"file://{source}", str(root)],
                           check=True, capture_output=True, env=env)
        elif kind == "arg":
            extra += [step[1], str(root / step[2])]  # ("arg", "--repo", 根からのパス)
    return extra


def run_all(scripts: Path, work: Path, env: dict[str, str], only: str | None = None) -> dict[str, tuple[int, str]]:
    """試料を全部回し、名前 → (終了コード, 出力)。
    `only` を渡せば、その名前の試料**だけ**を回す（変異の回。#494）——判定に使うのはその試料の結果だけで、他の試料は試料ごとに別の場所で
    別のプロセスとして回るので結果に効かない。場所の名前（`case<番号>`）は全部を回す形と同じ。
    """
    results = {}
    for index, (name, steps, _, _) in enumerate(CASES):
        if only is not None and name != only:
            continue
        root = work / f"case{index}"
        args = build_repo(root, steps, env) or ["--repo", str(root)]
        proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), *args],
                              capture_output=True, text=True, cwd=work, env=env)
        results[name] = (proc.returncode, proc.stdout + proc.stderr)
    return results


def as_expected(name: str, result: tuple[int, str]) -> bool:
    expected = next(case for case in CASES if case[0] == name)
    return result[0] == expected[2] and expected[3] in result[1]


def reference_mismatches(source: str, markdown: str) -> list[str]:
    """`versions.md` の「リリースは git のタグ `release-v<n>`」と、比べる場所 `docs/v<n>/` が本体と合うか。"""
    problems = []
    tag = re.search(r"リリースは git のタグ `([a-z-]+)v<n>` で示す", markdown)
    code = re.search(r'^RELEASE = re\.compile\(r"([a-z-]+)v\(\[1-9\]\[0-9\]\*\)"\)$', source, flags=re.MULTILINE)
    if (tag.group(1) if tag else None) != (code.group(1) if code else None):
        problems.append(f"リリースのタグ {tag and tag.group(1)!r} ≠ 本体 {code and code.group(1)!r}")
    docs = re.search(r"^- \*\*版は `([^`]+)/` 直下の `v<n>`\*\*", markdown, flags=re.MULTILINE)
    code_docs = re.search(r'^DOCS = "([^"]+)"$', source, flags=re.MULTILINE)
    if (docs.group(1) if docs else None) != (code_docs.group(1) if code_docs else None):
        problems.append(f"版の置き場所 {docs and docs.group(1)!r} ≠ 本体 {code_docs and code_docs.group(1)!r}")
    return problems


REFERENCE_MUTATIONS: list[tuple[str, str, str]] = [
    ("リリースのタグ", "リリースは git のタグ `release-v<n>` で示す", "リリースは git のタグ `ship-v<n>` で示す"),
    ("版の置き場所", "**版は `docs/` 直下の `v<n>`**", "**版は `spec/` 直下の `v<n>`**"),
]


# 想定外の例外は 2・-OO（docstring が無い）で引数なしに呼んでも想定外の例外にならない（#286）。(名前, 壊す前, 壊した後)
OO_MUTATIONS = [
    ("想定外の例外を 2 に寄せない", "    except Exception as e:  # 想定外の例外も「判定していない」（2）",
     "    except ImportError as e:  # 想定外の例外も「判定していない」（2）"),
    ("-OO で docstring が無いと落ちる", "description=__doc__.splitlines()[0] if __doc__ else None",
     "description=__doc__.splitlines()[0] if True else None"),
]
# 想定外の例外を作る入力はこの本体に無い（読むのは git の出力だけで、CSV も JSON も読まない）。
# だから `subprocess.run` を差し替えて ValueError を投げさせ、入口（`__main__`）から走らせる
UNEXPECTED_RUNNER = """
import runpy, subprocess, sys
def run(*args, **kwargs):
    raise ValueError("試料")
subprocess.run = run
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def oo_problems(scripts: Path, cwd: Path, env: dict[str, str]) -> list[str]:
    problems = []
    proc = subprocess.run([sys.executable, "-I", "-OO", str(scripts / TARGET)], capture_output=True, text=True,
                          cwd=cwd, env=env)
    output = proc.stdout + proc.stderr
    if proc.returncode != 2 or "想定外の例外" in output or "Traceback" in output:
        problems.append(f"-OO の引数なし: 終了 {proc.returncode}: {output[-300:]!r}")
    proc = subprocess.run([sys.executable, "-I", "-c", UNEXPECTED_RUNNER, str(scripts / TARGET)], capture_output=True,
                          text=True, cwd=cwd, env=env)
    output = proc.stdout + proc.stderr
    if proc.returncode != 2 or "想定外の例外で止まった（ValueError: 試料）" not in output or "Traceback" in output:
        problems.append(f"想定外の例外: 終了 {proc.returncode}: {output[-300:]!r}")
    return problems


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    if shutil.which("git") is None:
        print("git が無いので走らせていない（緑ではない）", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="frozen-test-") as tmp:
        tmp_path = Path(tmp)
        home = tmp_path / "home"
        home.mkdir()
        env = sandbox_env(home)
        scripts = copy_scripts(tmp_path / "scripts")
        results = run_all(scripts, tmp_path / "work", env)
        for name, result in results.items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result[0]} {result[1][-300:]}")

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        problems = reference_mismatches(source, reference)
        check("本体の定数が references/versions.md と一致しない", not problems, "; ".join(problems))
        for name, before, after in REFERENCE_MUTATIONS:
            if reference.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {reference.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(source, reference.replace(before, after))))

        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            mutated_results = run_all(mutated, tmp_path / f"mutwork{index}", env, only=killer)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）",
                  not as_expected(killer, mutated_results[killer]), mutated_results[killer][1][-300:])

        (tmp_path / "oo").mkdir()  # git でない場所——引数なしは今のディレクトリを見るので 2
        problems = oo_problems(scripts, tmp_path / "oo", env)
        check("想定外の例外・-OO の引数なしで 2 にならない", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(OO_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"oo-mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}", bool(oo_problems(mutated, tmp_path / "oo", env)))

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(OO_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
