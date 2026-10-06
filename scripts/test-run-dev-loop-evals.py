#!/usr/bin/env python3
"""`run-dev-loop-evals.py` の回帰テスト。

    python3 scripts/test-run-dev-loop-evals.py

**このテストは `claude` を起こさない。** 本体の `subprocess.run` を、呼ばれたら失格にする偽物に
差し替えてから当てる（**課金される経路を、テストが黙って踏まないため**）。
**本物のプラグインも複製しない**——テンポラリに偽のリポジトリ（`plugins/dev-loop/evals/…`）を作り、
本体の `REPO` / `PLUGIN` をそこへ向ける。

**試料の trace は合成である。** #183 の実行（`/private/tmp/e-LqmttA`）と**同じ形**——`xcrun` の雑音に
挟まれた `Preparing worktree …`——を作って当てる。**実物は CI に持ち込めない**（リポジトリの外）。

**変異テストを含む。** 本体の docstring の「守る」の行数だけ変異を当て、
**壊したのに観測が変わらなければ失格**とする。行を足したら変異も足す。
"""
import importlib.util
import json
import tempfile
import types
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "run-dev-loop-evals.py"
NOISE = ("git: error: couldn't create cache file '/var/folders/x/T/xcrun_db-abc' (errno=Operation not permitted)\n"
         "2026-10-06 15:48:19.250 xcodebuild[88991:47706270]  DVTFilePathFSEvents: Failed to start fs event stream.")
CASE_YAML = """schema_version: "1.1"
name: resume-no-new-worktree
description: x
execution:
  prompt: "/dev-loop:dev-loop 7"
  max_turns: 25
context:
  scaffold_script: scaffold.sh
graders:
  - name: no-new-branch
    type: file_exists
    path: ".git/refs/heads/**"
    exists: false
"""

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"rde_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def forbidden(*a, **k):
        raise AssertionError("テストが subprocess.run を呼んだ（claude を起こしうる）")
    # モジュールの属性を差し替える（標準の subprocess そのものは触らない）
    mod.subprocess = types.SimpleNamespace(run=forbidden)
    return mod


def check(name: str, cond: bool) -> None:
    print(("  OK  " if cond else "  NG  ") + name)
    if not cond:
        failures.append(name)


def fake_repo(root: Path, case_yaml: str = CASE_YAML) -> Path:
    case = root / "plugins" / "dev-loop" / "evals" / "resume-no-new-worktree"
    case.mkdir(parents=True)
    (case / "case.yaml").write_text(case_yaml, encoding="utf-8")
    (case / "scaffold.sh").write_text("#!/bin/sh\ngit init -q .\n", encoding="utf-8")
    (root / "plugins" / "dev-loop" / "evals" / "results" / "old").mkdir(parents=True)
    return root


def point(mod, repo: Path) -> None:
    mod.REPO = repo
    mod.PLUGIN = repo / "plugins" / "dev-loop"


def trace(path: Path, calls: list[tuple[str, str]]) -> str:
    lines = []
    for i, (cmd, out) in enumerate(calls):
        lines.append(json.dumps({"message": {"content": [
            {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": {"command": cmd}}]}}))
        lines.append(json.dumps({"message": {"content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "content": out}]}}))
    lines.append("not json")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def run(graders: dict[str, bool], tp: str | None, error=None) -> dict:
    return {"graders": [{"name": n, "passed": p} for n, p in graders.items()],
            "tracePath": tp, "error": error}


def aggregate(path: Path, cases: list[tuple[str, list[dict]]]) -> Path:
    path.write_text(json.dumps({"claudeVersion": "2.1.291", "costUsd": 1.5, "durationSeconds": 160,
                                "cases": [{"name": n, "arms": {"with": r}} for n, r in cases]}),
                    encoding="utf-8")
    return path


def observe(mod, tmp: Path) -> dict:
    """本体の観測を 1 つの dict にまとめる（変異で何かが変われば失格を逃れる）。"""
    obs: dict = {}
    repo = fake_repo(tmp / "repo")
    point(mod, repo)
    try:
        plugin = mod.build(tmp / "out")
        src = repo / "plugins" / "dev-loop" / "evals" / "resume-no-new-worktree"
        ctl = plugin / "evals" / "control-created-worktree"
        obs["files"] = sorted(p.name for p in ctl.iterdir())
        a = (src / "case.yaml").read_text().splitlines()
        b = (ctl / "case.yaml").read_text().splitlines()
        obs["diff"] = [(x, y) for x, y in zip(a, b) if x != y] + [len(a) - len(b)]
        obs["results_copied"] = (plugin / "evals" / "results").exists()
    except ValueError as e:
        obs["build"] = str(e)
    for label, out in (("inside", repo / "sub"), ("twice", tmp / "out")):
        try:
            mod.build(out)
            obs[label] = "built"
        except ValueError:
            obs[label] = "refused"
    dup = fake_repo(tmp / "dup", CASE_YAML + '  prompt: "again"\n')
    point(mod, dup)
    try:
        mod.build(tmp / "out-dup")
        obs["dup"] = "built"
    except ValueError:
        obs["dup"] = "refused"
    point(mod, repo)

    good = trace(tmp / "good.jsonl", [
        ("git worktree add .claude/worktrees/issue-7-again -b issue/7-again",
         NOISE + "\nPreparing worktree (new branch 'issue/7-again')\n" + NOISE + "\nHEAD is now at edfb64d init"),
    ])
    real = trace(tmp / "real.jsonl", [("python3 find-cycle.py 7", "exit=1"), ("git status", NOISE)])
    broken = trace(tmp / "broken.jsonl", [("git log", "git: can't exec '/usr/local/bin/git'")])
    exp = mod.expectations(["resume-no-new-worktree"])
    ctl_ok = {"ran-find-cycle": False, "no-new-worktree": False, "no-new-branch": False}
    real_ok = {"ran-find-cycle": True, "no-new-worktree": True, "no-new-branch": True}
    scenarios = {
        "ok": [("resume-no-new-worktree", [run(real_ok, real)]),
               ("control-created-worktree", [run(ctl_ok, good)])],
        "mismatch": [("resume-no-new-worktree", [run(real_ok, real)]),
                     ("control-created-worktree", [run(dict(ctl_ok, **{"no-new-branch": True}), good)])],
        "missing": [("resume-no-new-worktree", [run(real_ok, real)])],
        "notrace": [("resume-no-new-worktree", [run(real_ok, str(tmp / "nope.jsonl"))]),
                    ("control-created-worktree", [run(ctl_ok, good)])],
        "error": [("resume-no-new-worktree", [run(real_ok, real, error="timeout")]),
                  ("control-created-worktree", [run(ctl_ok, good)])],
        "suspect": [("resume-no-new-worktree", [run(real_ok, broken)]),
                    ("control-created-worktree", [run(ctl_ok, good)])],
        "offtarget": [("resume-no-new-worktree", [run(real_ok, real)]),
                      ("control-created-worktree", [run(dict(ctl_ok, **{"ran-find-cycle": True}), good)])],
    }
    for name, cases in scenarios.items():
        obs[name] = mod.summarize(aggregate(tmp / f"{name}.json", cases), exp)
    obs["unreadable"] = mod.summarize(tmp / "absent.json", exp)[1]
    return obs


MUTATIONS = {
    "scaffold を写さない":
        ("shutil.copytree(src, dst)", 'shutil.copytree(src, dst, ignore=shutil.ignore_patterns("scaffold.sh"))'),
    "差し替える行が 2 つでも組む": ("if len(hits) != 1:", "if len(hits) == 0:"),
    "リポジトリの中にも組む": ("if out == repo or repo in out.parents:", "if False:"),
    "期待違いでも 0": ("code = max(code, 1)", "code = code"),
    "報告に無いケースを見ない": ("if name not in seen:", "if False:"),
    "trace を読めなくても続ける":
        ("                code = 2\n                continue", "                continue"),
    "実行エラーを数えない": ("                out.append(f\"\\n**実行エラー**: {run['error']}\")\n                code = 2",
                             "                out.append(f\"\\n**実行エラー**: {run['error']}\")"),
    "目的外も一致に数える": ("if want is None:", "if False:"),
    "雑音を除かない": ("if any(p.search(ln) for p in NOISE):", "if False:"),
    "測定不成立の候補に印を付けない": ('flag = " ← **測定不成立の候補**" if', 'flag = "" if'),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        correct = observe(load(), tmp / "correct")

        print("対照を組む")
        check("対照は本物のケースを丸ごと写す（case.yaml と scaffold.sh）",
              correct.get("files") == ["case.yaml", "scaffold.sh"])
        check("違うのは name と prompt の 2 行だけ",
              [d for d in correct.get("diff", [])[:-1]] ==
              [("name: resume-no-new-worktree", "name: control-created-worktree"),
               ('  prompt: "/dev-loop:dev-loop 7"', correct["diff"][1][1])]
              and correct["diff"][-1] == 0 and "git worktree add" in correct["diff"][1][1])
        check("results/ は写さない", correct.get("results_copied") is False)
        check("リポジトリの中には組まない", correct["inside"] == "refused")
        check("空でない出力先には組まない", correct["twice"] == "refused")
        check("prompt の行が 2 つあれば組まない", correct["dup"] == "refused")

        print("\n要約")
        text, code = correct["ok"]
        check("全部期待どおりなら 0", code == 0)
        check("雑音を除き、判別の行を出す", "Preparing worktree (new branch 'issue/7-again')" in text
              and "xcrun_db" not in text and "既知の雑音 4 行を除いた" in text)
        check("雑音だけの出力はそう言う", "雑音のみ 2 行" in text)
        check("目的外は一致に数えない", "| ran-find-cycle | 不合格 | — | 目的外 |" in text)
        check("期待違いは 1", correct["mismatch"][1] == 1 and "期待と違う" in correct["mismatch"][0])
        check("報告に無いケースは 2", correct["missing"][1] == 2
              and "`control-created-worktree` が報告に無い" in correct["missing"][0])
        check("trace が読めなければ 2", correct["notrace"][1] == 2)
        check("実行エラーは 2", correct["error"][1] == 2)
        check("aggregate が読めなければ 2", correct["unreadable"] == 2)
        check("can't exec に印を付ける（緑のままでも）",
              "測定不成立の候補" in correct["suspect"][0] and correct["suspect"][1] == 0)
        check("目的外の grader が合格に変わっても 0", correct["offtarget"][1] == 0)

        print("\n変異テスト（壊したのに観測が変わらなければ失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for i, (name, (needle, replacement)) in enumerate(MUTATIONS.items()):
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所: {name}", False)
                continue
            broken = tmp / f"mut-{i}" / SCRIPT.name
            broken.parent.mkdir()
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            check(f"変異を殺せる: {name}", observe(load(broken), tmp / f"obs-{i}") != correct)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n課金する経路を踏まない歯止め")
        try:
            load().subprocess.run(["claude"])
        except AssertionError:
            check("subprocess.run を呼ぶと落ちる", True)
        else:
            check("subprocess.run を呼ぶと落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("dev-loop の Eval の実行と要約のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
