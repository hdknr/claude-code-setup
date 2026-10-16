#!/usr/bin/env python3
"""`check-signoff.py`（2 つのサインオフのタグの照合）の回帰テスト。

    python3 scripts/test-check-signoff.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-spec-exit.py` と同じ形。

見るもの:

1. **比べる場所（v1〜v<n> の `shared/` と v2〜v<n> の `removed.csv`）が食い違うタグの組で非ゼロ（1）**——
   中身の違い・追加・削除・**前の版の `shared/` だけ**・**`removed.csv` だけ**の違い。
2. **一致する組を通す**（陽性対照。比べる場所の外だけ違う組も一致）。
3. **「最新」を数で選ぶ**（`-10` > `-9`）・**命名に合わないタグ（旧い `req-signoff-v<n>` を含む）を数えない**・
   指定したタグで照合する・**版を省けば作業中の版（番号の最大）**・`--version` で版を選ぶ。
4. **照合できない形を 0 にしない（2）**——タグが無い・片方だけ・指定したタグが無い／命名に合わない／**別の版のもの**・
   どちらかの時点に比べる場所が無い（**両方に無いときも**——`git diff` は差分なしを返す。**旧い構成のタグも**）・
   タグがコミットを指さない・git でない・**作業ツリーの版が決まりに反する／1 つも無い**・`--version` が版の番号でない。
5. **本体の定数が `references/signoff-tags.md` と一致する**（写しのずれ）。
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
TARGET = "check-signoff.py"
REFERENCE = PLUGIN / "references" / "signoff-tags.md"

QA_A = "No,起票元\nQ-001,要求確定\n"
QA_B = "No,起票元\nQ-001,要求確定\nQ-002,開発\n"

# 試料の作り方: 手順の列。("w", パス, 中身) 書く／("rm", パス) 消す／("c",) commit／("t", 名前) 軽量タグ／
# ("ta", 名前) 注釈つきタグ／("tt", 名前) ツリーを指すタグ。None なら git でないディレクトリ
Steps = list[tuple[str, ...]] | None
SHARED = "docs/v1/shared/qa.csv"
SHARED2 = "docs/v2/shared/qa.csv"
REMOVED2 = "docs/v2/removed.csv"
R1, B1 = "v1/req-signoff-1", "v1/budget-signoff-1"
R2, B2 = "v2/req-signoff-1", "v2/budget-signoff-1"

# (名前, 手順, 引数, 期待する終了コード, 出力に含まれるべき文字列)
CASES: list[tuple[str, Steps, list[str], int, str]] = [
    ("一致", [("w", SHARED, QA_A), ("c",), ("t", R1),
              ("w", "docs/v1/feasibility/schedule.csv", "x\n"), ("c",), ("t", B1)],
     [], 0, f"一致する: {R1}"),
    ("同じコミットの 2 つのタグ", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     [], 0, "一致する"),
    ("中身が違う", [("w", SHARED, QA_A), ("c",), ("t", R1),
                  ("w", SHARED, QA_B), ("c",), ("t", B1)],
     [], 1, "M\tdocs/v1/shared/qa.csv"),
    ("ファイルの追加", [("w", SHARED, QA_A), ("c",), ("t", R1),
                    ("w", "docs/v1/shared/nfr.csv", "a\n"), ("c",), ("t", B1)],
     [], 1, "A\tdocs/v1/shared/nfr.csv"),
    ("ファイルの削除", [("w", SHARED, QA_A), ("w", "docs/v1/shared/nfr.csv", "a\n"), ("c",), ("t", R1),
                    ("rm", "docs/v1/shared/nfr.csv"), ("c",), ("t", B1)],
     [], 1, "D\tdocs/v1/shared/nfr.csv"),
    # 文字列順なら -9 が最新になり、-9 の中身（QA_A）と budget（QA_B）が食い違う
    ("最新を数で選ぶ", [("w", SHARED, QA_A), ("c",), ("t", "v1/req-signoff-9"),
                     ("w", SHARED, QA_B), ("c",), ("t", "v1/req-signoff-10"), ("t", B1)],
     [], 0, "一致する: v1/req-signoff-10"),
    # 古い budget-signoff-1 は一致するが、最新の -2 は食い違う
    ("新しい予算のタグが違う", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1),
                         ("w", SHARED, QA_B), ("c",), ("t", "v1/budget-signoff-2")],
     [], 1, "v1/budget-signoff-2"),
    ("命名に合わないタグを数えない", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1),
                               ("w", SHARED, QA_B), ("c",), ("t", "v1/req-signoff-2-fix"), ("t", "v1/req-signoff-02"),
                               ("t", "req-signoff-v2"), ("t", "v01/req-signoff-3")],
     [], 0, f"一致する: {R1}"),
    ("指定したタグで照合", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1),
                       ("w", SHARED, QA_B), ("c",), ("t", "v1/req-signoff-2")],
     ["--req", R1], 0, f"一致する: {R1}"),
    ("注釈つきタグ", [("w", SHARED, QA_A), ("c",), ("ta", R1), ("ta", B1)],
     [], 0, "一致する"),
    ("サブディレクトリから", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     ["--repo", "docs"], 0, "一致する"),
    ("タグが無い", [("w", SHARED, QA_A), ("c",)], [], 2, "v1/req-signoff-<k> のタグが 1 つも無い"),
    ("予算のタグだけ無い", [("w", SHARED, QA_A), ("c",), ("t", R1)], [], 2,
     "v1/budget-signoff-<k> のタグが 1 つも無い"),
    ("指定したタグが無い", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     ["--req", "v1/req-signoff-5"], 2, "タグ v1/req-signoff-5 が無い"),
    ("指定が命名に合わない", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     ["--budget", R1], 2, "命名（v1/budget-signoff-<k>）に合わない"),
    # 作業中の版は v2。v1 のタグを渡しても組にしない
    ("指定が別の版", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R1), ("t", B1), ("t", R2), ("t", B2)],
     ["--req", R1, "--budget", B1], 2, "版 v2 の命名"),
    ("片方の時点に shared が無い", [("w", "README.md", "x\n"), ("c",), ("t", R1),
                               ("w", SHARED, QA_A), ("c",), ("t", B1)],
     [], 2, f"{R1} の時点に docs/v1/shared/ のファイルが 1 つも無い"),
    # 両方に無いと git diff は「差分なし」を返す——それを一致と読まない（作業ツリーには v1 を置く）
    ("両方に shared が無い", [("w", "README.md", "x\n"), ("c",), ("t", R1), ("t", B1), ("w", SHARED, QA_A)],
     [], 2, "ファイルが 1 つも無い"),
    # 版に分ける前の構成でタグを付け、あとで docs/v1/ へ移した——旧いタグの時点には比べる場所が無い
    ("旧い構成の時点のタグ", [("w", "docs/shared/qa.csv", QA_A), ("c",), ("t", R1), ("t", B1),
                         ("rm", "docs/shared/qa.csv"), ("w", SHARED, QA_A), ("c",)],
     [], 2, "ファイルが 1 つも無い"),
    ("タグがツリーを指す", [("w", SHARED, QA_A), ("c",), ("tt", R1), ("t", B1)],
     [], 2, "コミットを指していない"),
    ("git でない", None, [], 2, "作業ツリーでない"),
    # ---- 版
    ("作業中の版", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R1), ("t", B1), ("t", R2), ("t", B2)],
     [], 0, f"一致する: {R2}"),
    ("前の版の shared だけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                             ("w", SHARED, QA_B), ("c",), ("t", B2)],
     [], 1, "M\tdocs/v1/shared/qa.csv"),
    ("removed.csv だけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                            ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-001,不要\n"), ("c",), ("t", B2)],
     [], 1, "A\tdocs/v2/removed.csv"),
    ("範囲の外だけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                       ("w", "docs/v2/requirements/a.md", "x\n"), ("c",), ("t", B2)],
     [], 0, "v1〜v2 の shared/ と removed.csv は同じ"),
    # 作業中の版は v2 だがタグは v1 にしかない。v1 の範囲に v2 は入らない
    ("版を指定", [("w", SHARED, QA_A), ("c",), ("t", R1), ("w", SHARED2, QA_A), ("c",), ("t", B1)],
     ["--version", "1"], 0, f"一致する: {R1}"),
    ("版を省くと作業中の版のタグを探す", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1), ("w", SHARED2, QA_A), ("c",)],
     [], 2, "v2/req-signoff-<k> のタグが 1 つも無い"),
    ("作業ツリーの版が決まりに反する", [("w", "docs/v02/shared/qa.csv", QA_A), ("c",), ("t", R1), ("t", B1)],
     [], 2, "版が決まりに反する"),
    ("作業ツリーに版が無い", [("w", "README.md", "x\n"), ("c",), ("t", R1), ("t", B1)],
     [], 2, "版（v1 など）が 1 つも無い"),
    ("--version が番号でない", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     ["--version", "01"], 2, "版の番号"),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("最新を文字列で選ぶ", "numbered = [(int(m.group(1)), name)", "numbered = [(m.group(1), name)", "最新を数で選ぶ"),
    ("命名を前方一致で見る", "if (m := pattern.fullmatch(name))", "if (m := pattern.match(name))",
     "命名に合わないタグを数えない"),
    ("先頭の 0 を許す", 'NUMBER = r"([1-9][0-9]*)"', 'NUMBER = r"([0-9]+)"', "命名に合わないタグを数えない"),
    ("最古を選ぶ", "return max(numbered)[1]", "return min(numbered)[1]", "新しい予算のタグが違う"),
    ("shared が空でも照合する", "    if not files:\n        raise Unjudged", "    if False:\n        raise Unjudged",
     "両方に shared が無い"),
    ("根で走らせない", "        repo = Path(top.stdout.strip())\n", "", "サブディレクトリから"),
    ("差分を見ない", "    if changed:", "    if False:", "中身が違う"),
    ("比べる場所を絞らない", 'info["budget_commit"], "--", *paths)', 'info["budget_commit"])', "一致"),
    ("前の版を範囲に含めない", "for i in range(1, version + 1)]", "for i in range(version, version + 1)]",
     "前の版の shared だけ違う"),
    ("removed.csv を範囲に含めない", "    return paths + [", "    return paths or [", "removed.csv だけ違う"),
    ("指定の命名を見ない", "if not tag_pattern(prefix, version).fullmatch(given):", "if False:", "指定が命名に合わない"),
    ("タグの版を見ない", 'rf"v{version}/{re.escape(prefix)}-{NUMBER}"', 'rf"v[0-9]+/{re.escape(prefix)}-{NUMBER}"',
     "指定が別の版"),
    ("作業中の版を最小にする", "return found[-1][0]", "return found[0][0]", "作業中の版"),
    ("--version を渡さない", "resolve(args.repo, args.req, args.budget, args.version)",
     "resolve(args.repo, args.req, args.budget)", "版を指定"),
    ("作業ツリーの版の誤りを見ない", '    if problems:\n        raise Unjudged("作業ツリーの版が',
     '    if False:\n        raise Unjudged("作業ツリーの版が', "作業ツリーの版が決まりに反する"),
    ("作業ツリーに版が無いのを見ない", "    if not found:\n", "    if False:\n", "作業ツリーに版が無い"),
    ("コミットに剥がさない", 'f"refs/tags/{tag}^{{commit}}"', 'f"refs/tags/{tag}"', "タグがツリーを指す"),
    ("git でないのを見ない", "if top.returncode != 0 or not top.stdout.strip():", "if False:", "git でない"),
    ("タグ無しを見ない", "if found is None:", "if False:", "タグが無い"),
    # `git diff` 自体が失敗する分岐（`if diff.returncode != 0`）は、手前の検査（コミットを指すか・
    # shared を読めるか）を通った後には作れなかったので、変異を置いていない（殺せると主張しない）
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


def build_repo(root: Path, steps: Steps, env: dict[str, str]) -> None:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    (root / "docs").mkdir()
    if steps is None:
        return
    run_git(root, env, "init", "-q", "-b", "main")
    for step in steps:
        kind = step[0]
        if kind == "w":
            path = root / step[1]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(step[2], encoding="utf-8")
            run_git(root, env, "add", "-A")
        elif kind == "rm":
            run_git(root, env, "rm", "-q", step[1])
        elif kind == "c":
            run_git(root, env, "commit", "-q", "--allow-empty", "-m", "step")
        elif kind == "t":
            run_git(root, env, "tag", step[1])
        elif kind == "ta":
            run_git(root, env, "tag", "-a", "-m", "signoff", step[1])
        elif kind == "tt":
            run_git(root, env, "tag", step[1], "HEAD^{tree}")


def run_all(scripts: Path, work: Path, env: dict[str, str]) -> dict[str, tuple[int, str]]:
    results = {}
    for index, (name, steps, args, _, _) in enumerate(CASES):
        root = work / f"case{index}"
        build_repo(root, steps, env)
        args = [str(root / a) if prev == "--repo" else a for prev, a in zip([""] + args, args)]
        if "--repo" not in args:
            args = ["--repo", str(root), *args]
        proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), *args],
                              capture_output=True, text=True, cwd=work, env=env)
        results[name] = (proc.returncode, proc.stdout + proc.stderr)
    return results


def as_expected(name: str, result: tuple[int, str]) -> bool:
    expected = next(case for case in CASES if case[0] == name)
    return result[0] == expected[3] and expected[4] in result[1]


NUMBER_WORDS = {"1 から始まる整数": r"([1-9][0-9]*)"}


def constant(source: str, name: str) -> str | None:
    found = re.search(rf'^{name} = r?"([^"]+)"$', source, flags=re.MULTILINE)
    return found.group(1) if found else None


def reference_mismatches(source: str, markdown: str) -> list[str]:
    problems = []
    prefixes = re.findall(r"^\| [^|]+ \| `v<n>/([a-z-]+)-<k>` \|", markdown, flags=re.MULTILINE)
    actual = [constant(source, k) for k in ("REQ_PREFIX", "BUDGET_PREFIX")]
    if prefixes != actual:
        problems.append(f"タグの接頭辞 {prefixes} ≠ 本体 {actual}")
    word = re.search(r"`<k>` は (.+?)で、", markdown)
    if NUMBER_WORDS.get(word.group(1) if word else "") != constant(source, "NUMBER"):
        problems.append(f"番号の決まり {word and word.group(1)!r} ≠ 本体 {constant(source, 'NUMBER')!r}")
    place = re.search(r"比べる場所は `([^`/]+)/v1/([^`]+)`〜`[^`]+` と `[^`/]+/v2/([^`]+)`〜", markdown)
    expected = (constant(source, "DOCS"), constant(source, "SHARED"), constant(source, "REMOVED"))
    if (place.groups() if place else None) != expected:
        problems.append(f"比べる場所 {place and place.groups()!r} ≠ 本体 {expected!r}")
    return problems


REFERENCE_MUTATIONS: list[tuple[str, str, str]] = [
    ("予算のタグの接頭辞", "| `v<n>/budget-signoff-<k>` |", "| `v<n>/budget-approval-<k>` |"),
    ("番号の決まり", "`<k>` は 1 から始まる整数で、", "`<k>` は 0 から始まる整数で、"),
    ("比べる場所（shared）", "比べる場所は `docs/v1/shared/`〜", "比べる場所は `docs/v1/common/`〜"),
    ("比べる場所（removed.csv）", "と `docs/v2/removed.csv`〜", "と `docs/v2/deleted.csv`〜"),
]


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    if shutil.which("git") is None:
        print("git が無いので走らせていない（緑ではない）", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="signoff-test-") as tmp:
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
        check("本体の定数が references/signoff-tags.md と一致しない", not problems, "; ".join(problems))
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
            mutated_results = run_all(mutated, tmp_path / f"mutwork{index}", env)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）",
                  not as_expected(killer, mutated_results[killer]), mutated_results[killer][1][-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
