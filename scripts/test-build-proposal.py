#!/usr/bin/env python3
"""`build-proposal.py`（照合が通ったときだけ提案書を作る）の回帰テスト。

    python3 scripts/test-build-proposal.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。照合そのものの分岐は
`scripts/test-check-signoff.py` が見る。ここで見るのは**生成の側が照合に従うこと**:

1. **照合が通らないとき、提案書を作らない**——一致しない（1）・照合していない（2）。
   **前に作った提案書とガントチャートも消す**（古いものを今のものと取り違えないため）。
2. **承認したタグの時点の中身から作る**——承認の後に直した見積り・Q&A 表は入らない。
   `docs/feasibility/` は `budget-signoff`、`docs/shared/` は `req-signoff` の時点。
3. **材料が欠けた・決まりに反するときも作らない**——手書き部分が無い・見積りが無い・見積りが決まりに反する。
4. **作れるときは作る**（陽性対照）——決定事項・未決定の質問・費用の合計・期間・ガントチャートが載り、
   手書き部分がファイル名の順に並ぶ。**同じ入力から同じバイト。**
5. **承認の記録を持たない**——「承認済み」と書かない。

**このテストは実環境を触らない。** 試料の git リポジトリはすべて一時ディレクトリに作り、
`HOME` と `GIT_CONFIG_GLOBAL` を差し替える。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "build-proposal.py"

QA = "docs/shared/qa.csv"
SCHEDULE = "docs/feasibility/schedule.csv"
ESTIMATE = "docs/feasibility/estimate.csv"
QA_HEAD = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
QA_ROWS = (
    "Q-001,要求確定,割引は？,A: なし / B: 3%,A（業務部が回答）,決定表 4 行目,反映済み,\n"
    "Q-005,実現性・コスト,夜間は止めてよいか,A: 止まってよい / B: 24 時間,未回答,—,確認中,B は月額が約 2 倍\n"
)
SCHEDULE_CSV = "No,工程,開始,終了,前提\nT-001,要件定義,2026-11-02,2026-11-27,\nT-002,基本設計,2026-11-30,2026-12-25,T-001\n"


def estimate(amount: str) -> str:
    return f"No,区分,項目,金額,根拠\nE-001,開発費,画面の開発,{amount},12 画面\nE-002,運用費（月額）,サーバ,120000,Q-005\n"


BASE = [("w", QA, QA_HEAD + QA_ROWS), ("w", SCHEDULE, SCHEDULE_CSV), ("w", ESTIMATE, estimate("4800000")),
        ("w", "docs/proposal/02-recommendation.md", "## 推奨案\n\n案 B を推す。\n"),
        ("w", "docs/proposal/01-background.md", "## 背景と目的\n\n受注を自動化する。\n"), ("c",)]
SIGNED = BASE + [("t", "req-signoff-v1"), ("t", "budget-signoff-v1")]


class Result:
    def __init__(self, code: int, output: str, text: str | None, svg: bool, again: str | None):
        self.code, self.output, self.text, self.svg, self.again = code, output, text, svg, again


def made(r: Result) -> bool:
    return r.code == 0 and r.text is not None and r.svg


def not_made(code: int) -> Callable[[Result], bool]:
    return lambda r: r.code == code and r.text is None and not r.svg and "提案書は作っていない" in r.output


# (名前, 手順, 前の出力を置くか, 判定)
CASES: list[tuple[str, list[tuple[str, ...]], bool, Callable[[Result], bool]]] = [
    ("作れるときは作る", SIGNED, False,
     lambda r: made(r) and "## 主な決定事項" in r.text and "| Q-001 | 割引は？ |" in r.text
     and "| 開発費 | 4,800,000 |" in r.text and "| 運用費（月額） | 120,000 |" in r.text
     and "2026-11-02 〜 2026-12-25" in r.text and "![ガントチャート](gantt.svg)" in r.text),
    ("未決定の質問を載せる", SIGNED, False,
     lambda r: made(r) and "承認の時点で未決定の質問（1 件）" in r.text and "| Q-005 |" in r.text),
    ("手書き部分はファイル名の順", SIGNED, False,
     lambda r: made(r) and 0 < r.text.find("## 背景と目的") < r.text.find("## 推奨案")),
    ("同じ入力から同じバイト", SIGNED, False, lambda r: made(r) and r.text == r.again),
    ("承認の記録を持たない", SIGNED, False, lambda r: made(r) and "承認済み" not in r.text and "承認の記録ではありません" in r.text),
    # 予算のタグは見積りを直した後、作業ツリーはさらにその後に直している
    ("承認したタグの時点の見積り", BASE + [("t", "req-signoff-v1"), ("w", ESTIMATE, estimate("5000000")), ("c",),
                                    ("t", "budget-signoff-v1"), ("w", ESTIMATE, estimate("9999999")), ("c",)], False,
     lambda r: made(r) and "5,000,000" in r.text and "9,999,999" not in r.text and "4,800,000" not in r.text),
    ("承認の後に直した Q&A 表は入らない", SIGNED + [("w", QA, QA_HEAD + QA_ROWS.replace("割引は？", "割引は本当に？")), ("c",)],
     False, lambda r: made(r) and "割引は？" in r.text and "割引は本当に？" not in r.text),
    ("一致しないと作らない", BASE + [("t", "req-signoff-v1"), ("w", QA, QA_HEAD), ("c",), ("t", "budget-signoff-v1")],
     False, not_made(1)),
    ("前の提案書を消す", BASE + [("t", "req-signoff-v1"), ("w", QA, QA_HEAD), ("c",), ("t", "budget-signoff-v1")],
     True, lambda r: not_made(1)(r) and r.output.count("前に作った出力を消した") == 2),
    ("照合していないと作らない", BASE, True, not_made(2)),
    ("見積りが決まりに反すると作らない", BASE[:2] + [("w", ESTIMATE, estimate('"4,800,000"'))] + BASE[3:]
     + [("t", "req-signoff-v1"), ("t", "budget-signoff-v1")], False, not_made(1)),
    ("見積りが無いと作らない", [s for s in SIGNED if s[:2] != ("w", ESTIMATE)], False,
     lambda r: not_made(1)(r) and "承認の時点に無い" in r.output),
    ("手書き部分が無いと作らない", [s for s in SIGNED if not (len(s) > 1 and s[1].startswith("docs/proposal/"))], False,
     lambda r: not_made(1)(r) and "手書き部分" in r.output),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("照合を見ない", "    if code:\n        raise Stop(code, lines)\n", "    if False:\n        raise Stop(code, lines)\n",
     "一致しないと作らない"),
    ("見積りを作業ツリーから読む", 'show(top, info["budget_commit"], info["budget"], ESTIMATE_PATH)',
     '(top / ESTIMATE_PATH).read_text(encoding="utf-8")', "承認したタグの時点の見積り"),
    ("見積りを要求のタグの時点で読む", 'show(top, info["budget_commit"], info["budget"], ESTIMATE_PATH)',
     'show(top, info["req_commit"], info["budget"], ESTIMATE_PATH)', "承認したタグの時点の見積り"),
    ("Q&A 表を作業ツリーから読む", 'show(top, info["req_commit"], info["req"], QA_PATH)',
     '(top / QA_PATH).read_text(encoding="utf-8")', "承認の後に直した Q&A 表は入らない"),
    ("前の出力を消さない", "            stale.unlink()\n", "            pass\n", "前の提案書を消す"),
    ("手書き部分を逆順に並べる", 'sorted(hand_dir.glob("*.md"))', 'sorted(hand_dir.glob("*.md"), reverse=True)',
     "手書き部分はファイル名の順"),
    ("手書きが無くても作る", "    if not hand:\n", "    if False:\n", "手書き部分が無いと作らない"),
    ("表の検査を見ない", "    if problems:\n        raise Stop(1, problems)", "    if False:\n        raise Stop(1, problems)",
     "見積りが決まりに反すると作らない"),
    ("未決定の質問を載せない", "    if pending:\n", "    if False:\n", "未決定の質問を載せる"),
    ("区分ごとに合計しない", "sum(int(r['金額']) for r in estimate if r['区分'] == c)", "sum(int(r['金額']) for r in estimate)",
     "作れるときは作る"),
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


def build_repo(root: Path, steps: list[tuple[str, ...]], env: dict[str, str]) -> None:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    run_git(root, env, "init", "-q", "-b", "main")
    for step in steps:
        if step[0] == "w":
            path = root / step[1]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(step[2], encoding="utf-8")
            run_git(root, env, "add", "-A")
        elif step[0] == "c":
            run_git(root, env, "commit", "-q", "--allow-empty", "-m", "step")
        elif step[0] == "t":
            run_git(root, env, "tag", step[1])


def generate(scripts: Path, root: Path, out: Path, env: dict[str, str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), "--repo", str(root), "--out", str(out)],
                          capture_output=True, text=True, cwd=root, env=env)
    return proc.returncode, proc.stdout + proc.stderr


def run_case(scripts: Path, root: Path, steps, stale: bool, env: dict[str, str]) -> Result:
    build_repo(root, steps, env)
    out = root / "build" / "proposal" / "proposal.md"
    if stale:
        out.parent.mkdir(parents=True)
        out.write_text("古い提案書\n", encoding="utf-8")
        (out.parent / "gantt.svg").write_text("<svg/>", encoding="utf-8")
    code, output = generate(scripts, root, out, env)
    text = out.read_text(encoding="utf-8") if out.is_file() else None
    svg = (out.parent / "gantt.svg").is_file()
    again_out = root / "build" / "again" / "proposal.md"
    generate(scripts, root, again_out, env)
    again = again_out.read_text(encoding="utf-8") if again_out.is_file() else None
    return Result(code, output, text, svg, again)


def run_all(scripts: Path, work: Path, env: dict[str, str]) -> dict[str, Result]:
    return {name: run_case(scripts, work / f"case{i}", steps, stale, env)
            for i, (name, steps, stale, _) in enumerate(CASES)}


def as_expected(name: str, result: Result) -> bool:
    return next(case for case in CASES if case[0] == name)[3](result)


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    if shutil.which("git") is None:
        print("git が無いので走らせていない（緑ではない）", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="proposal-test-") as tmp:
        tmp_path = Path(tmp)
        home = tmp_path / "home"
        home.mkdir()
        env = sandbox_env(home)
        scripts = copy_scripts(tmp_path / "scripts")
        for name, result in run_all(scripts, tmp_path / "work", env).items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result.code} {result.output[-300:]}")

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            killer_case = next(case for case in CASES if case[0] == killer)
            result = run_case(mutated, tmp_path / f"mutwork{index}", killer_case[1], killer_case[2], env)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result.output[-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
