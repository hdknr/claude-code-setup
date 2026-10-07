#!/usr/bin/env python3
"""`run-dev-loop-evals.py` の回帰テスト。

    python3 scripts/test-run-dev-loop-evals.py

**このテストは `claude` を起こさない。** 本体のモジュール属性 `subprocess` を、呼ばれたら失格にする
偽物に差し替えてから当てる（**課金される経路を、テストが黙って踏まないため**）。
**本物のプラグインも複製しない**——テンポラリに偽のリポジトリ（`plugins/dev-loop/evals/…`）を作り、
本体の `REPO` / `PLUGIN` をそこへ向ける。

**試料の trace は合成である。** #183 の実行（`/private/tmp/e-LqmttA`）と**同じ形**——`xcrun` の雑音に
挟まれた `Preparing worktree …`——を作って当てる。**実物は CI に持ち込めない**（リポジトリの外）。

**変異テストを含む。** 本体の docstring の「守る」の行数だけ変異を当て、
**壊したのに観測が変わらなければ失格**とする。行を足したら変異も足す。
**観測は一時ディレクトリのパスを含まない形に正規化する**——含めると、**何も変えない変異でも
観測が変わり、全部「殺せた」になる**（1 パス目の `/code-review` が実測した）。だから
**無変更の本体を別のディレクトリで観測して一致すること**と、**コメントだけ変えた変異が殺せないこと**を
陽性対照として先に見る。
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
  - name: ran-find-cycle
    type: transcript_matches
  - name: no-new-worktree
    type: file_exists
  - name: no-new-branch
    type: file_exists
    path: ".git/refs/heads/**"
    exists: false
"""
REAL = "resume-no-new-worktree"
CTL = "control-created-worktree"
CTL_OK = {"ran-find-cycle": False, "no-new-worktree": False, "no-new-branch": False}
REAL_OK = {"ran-find-cycle": True, "no-new-worktree": True, "no-new-branch": True}

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
    case = root / "plugins" / "dev-loop" / "evals" / REAL
    case.mkdir(parents=True)
    (case / "case.yaml").write_text(case_yaml, encoding="utf-8")
    (case / "scaffold.sh").write_text("#!/bin/sh\ngit init -q .\n", encoding="utf-8")
    stale = root / "plugins" / "dev-loop" / "evals" / "results" / "old"
    stale.mkdir(parents=True)
    # 前の実行の残り。ケースに数えたら「報告に無いケース」が出る
    (stale / "case.yaml").write_text(case_yaml.replace(f"name: {REAL}", "name: stale"), encoding="utf-8")
    return root


def fake_worktree(main: Path) -> Path:
    """main/.git（ディレクトリ）と、その worktree（.git はファイル）を作り、worktree を返す。"""
    gitdir = main / ".git" / "worktrees" / "w"
    gitdir.mkdir(parents=True)
    (gitdir / "commondir").write_text("../..\n", encoding="utf-8")
    wt = fake_repo(main / ".claude" / "worktrees" / "w")
    (wt / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    return wt


def point(mod, repo: Path) -> None:
    mod.REPO = repo
    mod.PLUGIN = repo / "plugins" / "dev-loop"


def trace(path: Path, calls: list[tuple]) -> str:
    lines = []
    for i, call in enumerate(calls):
        cmd, out = call[0], call[1]
        tool = call[2] if len(call) > 2 else "Bash"
        is_error = call[3] if len(call) > 3 else False
        parent = call[4] if len(call) > 4 else None  # Agent の中の呼び出し（#183 の本物の trace の形）
        lines.append(json.dumps({"parent_tool_use_id": parent, "message": {"content": [
            {"type": "tool_use", "id": f"t{i}", "name": tool, "input": {"command": cmd}}]}}))
        lines.append(json.dumps({"parent_tool_use_id": parent, "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "content": out, "is_error": is_error}]}}))
    lines.append("not json")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


def run(graders: dict[str, bool], tp: str | None, **extra) -> dict:
    return {"graders": [{"name": n, "passed": p, "scored": True} for n, p in graders.items()],
            "tracePath": tp, "error": None, **extra}


def aggregate(path: Path, cases, **top) -> Path:
    body = {"claudeVersion": "2.1.291", "costUsd": 1.5, "durationSeconds": 160, "partial": False, **top}
    body["cases"] = cases if not isinstance(cases, list) else \
        [{"name": n, "arms": {"with": r}} for n, r in cases]
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def attempt(fn, *args):
    try:
        return fn(*args)
    except Exception as e:  # 観測としては「落ちた」を記録する
        return f"raised:{type(e).__name__}"


def observe(mod, tmp: Path) -> dict:
    """本体の観測を 1 つの dict にまとめる。**tmp のパスは "<T>" に置き換える**。"""
    tmp.mkdir(parents=True)
    obs: dict = {}
    repo = fake_repo(tmp / "repo")
    point(mod, repo)
    plugin = attempt(mod.build, tmp / "out")
    if isinstance(plugin, Path):
        src = repo / "plugins" / "dev-loop" / "evals" / REAL
        ctl = plugin / "evals" / CTL
        obs["files"] = sorted(p.name for p in ctl.iterdir())
        a = (src / "case.yaml").read_text().splitlines()
        b = (ctl / "case.yaml").read_text().splitlines()
        obs["diff"] = [(x, y) for x, y in zip(a, b) if x != y] + [len(a) - len(b)]
        obs["results_copied"] = (plugin / "evals" / "results").exists()
    else:
        obs["build"] = plugin

    def refused(out: Path) -> str:
        r = attempt(mod.build, out)
        return "built" if isinstance(r, Path) else ("refused" if r == "raised:ValueError" else r)
    obs["inside"] = refused(repo / "sub")
    obs["twice"] = refused(tmp / "out")
    prompt = '  prompt: "/dev-loop:dev-loop 7"'
    for label, yaml in (("dup", CASE_YAML + '  prompt: "again"\n'),
                        ("zero", CASE_YAML.replace(prompt + "\n", "")),
                        ("block", CASE_YAML.replace(prompt, "  prompt: >-\n    /dev-loop:dev-loop 7")),
                        ("quoted", CASE_YAML.replace(prompt, '  prompt: "/dev-loop:dev-loop\n    7"')),
                        ("plain", CASE_YAML.replace(prompt, "  prompt: /dev-loop:dev-loop\n    7")),
                        ("nextline", CASE_YAML.replace(prompt, '  prompt:\n    "/dev-loop:dev-loop 7"'))):
        point(mod, fake_repo(tmp / label, yaml))
        obs[label] = refused(tmp / f"out-{label}")
    wt = fake_worktree(tmp / "main")
    point(mod, wt)
    obs["main"] = refused(tmp / "main" / "evals-tmp")
    obs["beside"] = refused(tmp / "beside")
    point(mod, repo)

    good = trace(tmp / "good.jsonl", [
        ("git worktree add .claude/worktrees/issue-7-again -b issue/7-again",
         NOISE + "\nPreparing worktree (new branch 'issue/7-again')\n" + NOISE + "\nHEAD is now at edfb64d init"),
    ])
    real = trace(tmp / "real.jsonl", [("python3 find-cycle.py 7", "exit=1"), ("git status", NOISE),
                                     ("", "report", "Agent"),
                                     ("git branch --list sub-agent-only", "x", "Bash", False, "t2")])
    broken = trace(tmp / "broken.jsonl", [("git log", "git: can't exec '/usr/local/bin/git'"),
                                          ("gh pr view", "zsh: command not found: gh"),
                                          ("rm -rf x", "Permission to use Bash has been denied"),
                                          ("git status", "git: can't exec '/usr/local/bin/git'\na\nb\nc")])
    denied = trace(tmp / "denied.jsonl", [("git worktree add x", "Permission to use Bash with command x", "Bash", True)])
    exp = mod.expectations(mod.real_cases(mod.PLUGIN))
    ok = [(REAL, [run(REAL_OK, real)]), (CTL, [run(CTL_OK, good)])]
    scenarios = {
        "ok": (ok, {}),
        "mismatch": ([ok[0], (CTL, [run(dict(CTL_OK, **{"no-new-branch": True}), good)])], {}),
        "missing": ([ok[0]], {}),
        "undefined": (ok + [("extra-case", [run({"x": False}, real)])], {}),
        "runs0": ([(REAL, []), ok[1]], {}),
        "nogradr": ([ok[0], (CTL, [run({"ran-find-cycle": False}, good)])], {}),
        "partial": (ok, {"partial": True}),
        "skipped": ([(REAL, [run(REAL_OK, real, skippedPaidGraders=True)]), ok[1]], {}),
        "unscored": ([(REAL, [{"graders": [{"name": n, "passed": True, "scored": n != "ran-find-cycle"}
                                           for n in REAL_OK], "tracePath": real, "error": None}]), ok[1]], {}),
        "structure": ("x", {}),
        "notrace": ([(REAL, [run(REAL_OK, str(tmp / "nope.jsonl"))]), ok[1]], {}),
        "error": ([(REAL, [run(REAL_OK, real, error="timeout")]), ok[1]], {}),
        "suspect": ([(REAL, [run(REAL_OK, broken)]), ok[1]], {}),
        "denied": ([(REAL, [run(REAL_OK, denied)]), ok[1]], {}),
        "offtarget": ([ok[0], (CTL, [run(dict(CTL_OK, **{"ran-find-cycle": True}), good)])], {}),
        "realgradr": ([(REAL, [run({"ran-find-cycle": True}, real)]), ok[1]], {}),
        "extragradr": ([ok[0], (CTL, [run(dict(CTL_OK, **{"no-new-tag": True}), good)])], {}),
    }
    for name, (cases, top) in scenarios.items():
        obs[name] = attempt(mod.summarize, aggregate(tmp / f"{name}.json", cases, **top), exp)
    obs["unreadable"] = attempt(mod.summarize, tmp / "absent.json", exp)
    # case.yaml から grader を 1 つも拾えなかった（書式が変わった）ときも、報告の grader 0 件を緑にしない
    obs["graders0"] = attempt(mod.summarize, aggregate(tmp / "graders0.json", [(REAL, [run({}, real)]), ok[1]]),
                              mod.expectations({REAL: []}))
    # パスを正規化する（tmp は呼び出しごとに違う）
    return json.loads(json.dumps(obs, default=str).replace(str(tmp.resolve()), "<T>").replace(str(tmp), "<T>"))


# 「守る」1 行 → その行を外す変異（1 つ以上）
MUTATIONS = {
    "scaffold を写さない":
        [("shutil.copytree(src, dst)", 'shutil.copytree(src, dst, ignore=shutil.ignore_patterns("scaffold.sh"))')],
    "差し替える行が 1 つでなくても組む":
        [("if len(hits) != 1:", "if len(hits) == 0:"), ("if len(hits) != 1:", "if len(hits) > 1:")],
    "次の行に続く値でも組む":
        [("if following.strip() and indent(following) > indent(m.group(0)):", "if False:")],
    "この作業ツリーの中にも組む": [("if out == root or root in out.parents:", "if out == root and False:")],
    "メインの作業ツリーを守らない": [("roots.append(common.parent)", "pass")],
    "期待違いでも 0": [("code = max(code, 1)", "code = code")],
    "報告に無いケースを見ない": [("code = 2  # 報告に無いケース", "pass")],
    "未定義のケースを黙って捨てる": [("code = 2  # 未定義のケース", "pass")],
    "run 0 件を見ない": [("code = 2  # run 0 件", "pass")],
    "grader 0 件を見ない": [("code = 2  # grader 0 件", "pass")],
    "results/ の下もケースに数える": [('if "results" in y.relative_to(evals).parts:', "if False:")],
    "期待した grader が無くても見ない":
        [("code = 2  # 期待した grader が無い", "pass"),
         ("exp: dict[str, dict[str, bool | None]] = {n: {g: True for g in gs} for n, gs in cases.items()}",
          "exp: dict[str, dict[str, bool | None]] = {n: {} for n, gs in cases.items()}")],
    "未定義の grader を黙って合格扱いにする": [("code = 2  # 未定義の grader", "pass")],
    "partial を見ない": [("code = 2  # partial", "pass")],
    "skippedPaidGraders を見ない": [("code = 2  # skippedPaidGraders", "pass")],
    "scored: false を見ない": [("code = 2  # 採点されていない", "pass")],
    "構造違いで Traceback": [("except (AttributeError, TypeError, KeyError, ValueError) as e:",
                            "except ZeroDivisionError as e:")],
    "trace を読めなくても見ない": [("code = 2  # trace を読めない", "pass")],
    "実行エラーを数えない": [("code = 2  # 実行エラー", "pass")],
    "目的外も一致に数える": [("elif want is None:", "elif False:")],
    "雑音を除かない": [("if any(p.search(ln) for p in NOISE):", "if False:")],
    "測定不成立の候補に印を付けない":
        [('flag = " ← **測定不成立の候補**" if', 'flag = "" if'),
         ('    re.compile(r"command not found"),\n', ""),
         ('    re.compile(r"has been denied"),\n', ""),
         ("if any(p.search(ln) for ln in kept[:-TAIL] for p in SUSPECT):", "if False:")],
    "Agent の中の Bash を親に混ぜる": [('sidechain = o.get("parent_tool_use_id") is not None', "sidechain = False")],
    "is_error に印を付けない": [('if is_error else ""', 'if False else ""')],
}


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        source = SCRIPT.read_text(encoding="utf-8")
        correct = observe(load(), tmp / "correct")

        print("陽性対照（観測が判別していること）")
        check("無変更の本体を別のディレクトリで観測すると一致する", observe(load(), tmp / "again") == correct)
        noop = tmp / "noop" / SCRIPT.name
        noop.parent.mkdir()
        noop.write_text(source.replace("# 陽性対照。", "# 陽性対照（無変更の変異）。", 1), encoding="utf-8")
        check("コメントだけ変えた変異は殺せない", observe(load(noop), tmp / "noop-obs") == correct)

        print("\n対照を組む")
        check("対照は本物のケースを丸ごと写す（case.yaml と scaffold.sh）",
              correct.get("files") == ["case.yaml", "scaffold.sh"])
        diff = correct.get("diff", [])
        check("違うのは name と prompt の 2 行だけ",
              len(diff) == 3 and diff[0] == ["name: resume-no-new-worktree", f"name: {CTL}"]
              and diff[1][0] == '  prompt: "/dev-loop:dev-loop 7"' and "git worktree add" in diff[1][1]
              and diff[2] == 0)
        check("results/ は写さない", correct.get("results_copied") is False)
        check("この作業ツリーの中には組まない", correct["inside"] == "refused")
        check("worktree から走らせたとき、メインの作業ツリーの中にも組まない", correct["main"] == "refused")
        check("worktree から走らせても、外になら組む", correct["beside"] == "built")
        check("空でない出力先には組まない", correct["twice"] == "refused")
        check("prompt の行が 2 つあれば組まない", correct["dup"] == "refused")
        check("prompt の行が無ければ組まない", correct["zero"] == "refused")
        for key, label in (("block", "ブロックスカラー"), ("quoted", "複数行の引用符つき scalar"),
                           ("plain", "複数行の plain scalar"), ("nextline", "次の行に書いた値")):
            check(f"prompt が{label}なら組まない", correct[key] == "refused")

        print("\n要約")
        text, code = correct["ok"]
        check("全部期待どおりなら 0", code == 0)
        check("雑音を除き、判別の行を出す", "Preparing worktree (new branch 'issue/7-again')" in text
              and "xcrun_db" not in text and "既知の雑音 4 行を除いた" in text)
        check("雑音だけの出力はそう言う", "雑音のみ 2 行" in text)
        check("Agent の回数を出し、Agent の中の Bash は親に混ぜない",
              "Bash 2 回・Agent 1 回" in text and "Agent の中の Bash 1 回" in text
              and "sub-agent-only" not in text)
        check("results/ の下の case.yaml はケースに数えない", "stale" not in text)
        check("目的外は一致に数えない", "| ran-find-cycle | 不合格 | — | 目的外 |" in text)
        check("期待違いは 1", correct["mismatch"][1] == 1 and "期待と違う" in correct["mismatch"][0])
        for key, label in (("missing", "報告に無いケース"), ("undefined", "期待が定義されていないケース"),
                           ("runs0", "run 0 件"), ("graders0", "grader 0 件"),
                           ("nogradr", "期待した grader が報告に無い"), ("partial", "partial"),
                           ("skipped", "skippedPaidGraders"), ("unscored", "scored: false"),
                           ("structure", "構造が想定と違う aggregate"), ("notrace", "trace が読めない"),
                           ("error", "実行エラー"), ("realgradr", "本物のケースの grader の欠落"),
                           ("extragradr", "期待が定義されていない grader")):
            check(f"{label} は 2", isinstance(correct[key], list) and correct[key][1] == 2)
        check("aggregate が読めなければ 2", correct["unreadable"][1] == 2)
        sus = correct["suspect"][0]
        check("can't exec・command not found・has been denied のどれにも印を付ける（緑のままでも）",
              all(f"{x} ← **測定不成立の候補**" in sus for x in ("/usr/local/bin/git'", "gh", "denied"))
              and correct["suspect"][1] == 0)
        check("表示しなかった行の測定不成立の候補もそう言う", "表示しなかった行にもある" in sus)
        check("is_error に印を付ける", "is_error（測定不成立の候補）" in correct["denied"][0])
        check("目的外の grader が合格に変わっても 0", correct["offtarget"][1] == 0)

        print("\n変異テスト（壊したのに観測が変わらなければ失格）")
        for i, (name, muts) in enumerate(MUTATIONS.items()):
            for j, (needle, replacement) in enumerate(muts):
                label = name if len(muts) == 1 else f"{name}（{j + 1}/{len(muts)}）"
                if source.count(needle) != 1:
                    check(f"変異を当てる先が 1 箇所: {label}", False)
                    continue
                broken = tmp / f"mut-{i}-{j}" / SCRIPT.name
                broken.parent.mkdir()
                broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
                check(f"変異を殺せる: {label}", observe(load(broken), tmp / f"obs-{i}-{j}") != correct)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異の組が {len(MUTATIONS)} 組",
              len(promises) == len(MUTATIONS))

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
