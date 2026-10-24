#!/usr/bin/env python3
"""`merge-pr.py` の回帰テスト。

    python3 scripts/test-merge-pr.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）。
**`dev-loop` はどのリポジトリでも使うスキル**なので、対象リポジトリの `scripts/` に在ることを当てにできない
（`test-find-cycle.py` と同じ形）。

**このテストは実環境を触らない。** 偽の `gh` を `PATH` の先頭に置き（**本物の GitHub に 1 度も届かない**）、
`git` は本物をテンポラリのリポジトリにだけ当てる（`assert_not_real_repo` が担保する）。
**偽の `gh` が呼ばれたことも見る**——呼ばれていなければ、本物が走ったかもしれない。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**「守る」の行数と変異の数が 1 対 1 か**は、**テスト自身が数える。**
**陽性対照**: 壊さない本体で全試料が期待どおりになることを先に見る（そこで落ちれば変異の結果は読まない）。
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "merge-pr.py"

failures: list[str] = []

FAKE_GH = r'''#!/usr/bin/env python3
"""偽の gh。シナリオ（JSON）に従って答え、呼ばれた引数を記録する。"""
import json, os, sys
scn_path = os.environ["FAKE_GH_SCENARIO"]
scn = json.load(open(scn_path, encoding="utf-8"))
with open(os.environ["FAKE_GH_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
args = sys.argv[1:]
counts_path = scn_path + ".counts"
counts = json.load(open(counts_path)) if os.path.exists(counts_path) else {}
def nxt(key, seq):
    i = counts.get(key, 0)
    counts[key] = i + 1
    json.dump(counts, open(counts_path, "w"))
    return seq[min(i, len(seq) - 1)]
if scn.get("fail_all"):
    print("gh: something went wrong", file=sys.stderr); sys.exit(1)
if args[:2] == ["pr", "view"]:
    fields = args[args.index("--json") + 1]
    if fields == "state":
        print(json.dumps({"state": nxt("after", scn.get("after", ["MERGED"]))}))
    else:
        print(json.dumps(nxt("view", scn["view"])))
elif args[:2] == ["pr", "merge"]:
    rc = scn.get("merge_rc", 0)
    if rc:
        print("merge failed", file=sys.stderr)
    sys.exit(rc)
elif args[:2] == ["issue", "view"]:
    print(json.dumps({"state": nxt("issue:" + args[2], scn.get("issues", {}).get(args[2], ["CLOSED"]))}))
else:
    print("unexpected: " + " ".join(args), file=sys.stderr); sys.exit(99)
'''


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def git(cwd, *args) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout


BRANCH = "issue/42-sample"
ISSUE_URL = "https://example.invalid/o/r/issues/42"


def make_repo(root: Path, lock: bool = True) -> tuple[Path, Path, str]:
    """メインの作業ツリーと、PR のブランチを持つ worktree。(main, wt, head の SHA)。"""
    main = root / "main"
    main.mkdir(parents=True)
    assert_not_real_repo(main)
    git(main, "init", "-q", "-b", "main")
    git(main, "config", "user.email", "t@example.invalid")
    git(main, "config", "user.name", "t")
    (main / "README.md").write_text("x\n", encoding="utf-8")
    git(main, "add", "-A")
    git(main, "commit", "-qm", "init")
    wt = main / ".claude" / "worktrees" / "issue-42"
    git(main, "worktree", "add", "-q", str(wt), "-b", BRANCH)
    (wt / "a.txt").write_text("a\n", encoding="utf-8")
    git(wt, "add", "-A")
    git(wt, "commit", "-qm", "feat")
    if lock:
        git(main, "worktree", "lock", "--reason", "claude agent agent-abc (pid 1)", str(wt))
    return main, wt, git(wt, "rev-parse", "HEAD").strip()


def pr(sha: str, mergeable="MERGEABLE", checks=None, state="OPEN", draft=False) -> dict:
    if checks is None:
        checks = [{"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"},
                  {"__typename": "StatusContext", "context": "ci/legacy", "state": "SUCCESS"}]
    return {"state": state, "isDraft": draft, "mergeable": mergeable, "headRefName": BRANCH,
            "headRefOid": sha, "statusCheckRollup": checks,
            "closingIssuesReferences": [{"number": 42, "url": ISSUE_URL}]}


def run_case(base: Path, name: str, script: Path, make_view, *, lock=True, after=None, issues=None,
             merge_rc=0, fail_all=False, prepare=None, cwd_in_wt=False, timeout="5") -> dict:
    root = base / name
    main, wt, sha = make_repo(root, lock=lock)
    if prepare:
        prepare(main, wt)
    scn = {"view": make_view(sha), "merge_rc": merge_rc, "fail_all": fail_all}
    if after:
        scn["after"] = after
    if issues:
        scn["issues"] = issues
    bin_dir = root / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text(FAKE_GH, encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    scn_path = root / "scenario.json"
    scn_path.write_text(json.dumps(scn), encoding="utf-8")
    log = root / "gh.log"
    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
               FAKE_GH_SCENARIO=str(scn_path), FAKE_GH_LOG=str(log))
    res = subprocess.run([sys.executable, str(script), "42", "--interval", "0.05",
                          "--timeout", timeout, "--settle", "0.5"],
                         cwd=str(wt if cwd_in_wt else main), env=env, capture_output=True, text=True)
    calls = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    merges = [c for c in calls if c[:2] == ["pr", "merge"]]
    return {"rc": res.returncode, "out": res.stdout + res.stderr, "calls": calls, "merges": merges,
            "wt_exists": wt.is_dir(), "sha": sha}


def unknown_then(sha):
    return [pr(sha, mergeable="UNKNOWN"), pr(sha, mergeable="UNKNOWN"), pr(sha)]


def running_then(sha):
    running = [{"__typename": "CheckRun", "name": "check", "status": "IN_PROGRESS", "conclusion": None}]
    return [pr(sha, checks=running), pr(sha)]


CASES = {
    # 名前: (試料の引数, 期待する rc, マージが呼ばれるか, worktree が残るか)
    "UNKNOWN の後に MERGEABLE（ロック済み worktree）": (dict(make_view=unknown_then), 0, True, False),
    "検査が走っている間は待つ": (dict(make_view=running_then), 0, True, False),
    "UNKNOWN のまま時間切れ": (dict(make_view=lambda s: [pr(s, mergeable="UNKNOWN")], timeout="0.3"), 5, False, True),
    "検査が走り続けて時間切れ": (dict(make_view=lambda s: [pr(s, checks=[
        {"__typename": "StatusContext", "context": "ci", "state": "PENDING"}])], timeout="0.3"), 5, False, True),
    "検査が 0 本なら時間切れ": (dict(make_view=lambda s: [pr(s, checks=[])], timeout="0.3"), 5, False, True),
    "CheckRun の失敗で止まる": (dict(make_view=lambda s: [pr(s, checks=[
        {"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "FAILURE"}])]), 3, False, True),
    "StatusContext の失敗で止まる": (dict(make_view=lambda s: [pr(s, checks=[
        {"__typename": "StatusContext", "context": "ci", "state": "ERROR"}])]), 3, False, True),
    "衝突していれば止まる": (dict(make_view=lambda s: [pr(s, mergeable="CONFLICTING")]), 4, False, True),
    "未コミットがあればマージしない": (dict(make_view=lambda s: [pr(s)],
        prepare=lambda m, w: (w / "dirty.txt").write_text("d\n")), 6, False, True),
    "push していなければマージしない": (dict(make_view=lambda s: [pr("0" * 40)]), 6, False, True),
    "cwd が worktree の中ならマージしない": (dict(make_view=lambda s: [pr(s)], cwd_in_wt=True), 6, False, True),
    "マージが失敗したら worktree を残す": (dict(make_view=lambda s: [pr(s)], merge_rc=1), 8, True, True),
    "Issue が閉じなければ 9": (dict(make_view=lambda s: [pr(s)], issues={ISSUE_URL: ["OPEN"]}), 9, True, False),
    "PR が MERGED にならなければ 9": (dict(make_view=lambda s: [pr(s)], after=["OPEN"]), 9, True, False),
    "OPEN でなければ何もしない": (dict(make_view=lambda s: [pr(s, state="MERGED")]), 2, False, True),
    "draft なら何もしない": (dict(make_view=lambda s: [pr(s, draft=True)]), 2, False, True),
    "gh が失敗したら判定できなかった": (dict(make_view=lambda s: [pr(s)], fail_all=True), 7, False, True),
    "検査の型が読めなければ判定できなかった": (dict(make_view=lambda s: [pr(s, checks=[
        {"__typename": "Mystery", "name": "x"}])]), 7, False, True),
}


def run_all(base: Path, script: Path) -> dict:
    return {name: run_case(base, f"c{i}", script, **kw)
            for i, (name, (kw, *_)) in enumerate(CASES.items())}


def as_expected(name: str, r: dict) -> bool:
    _, rc, merged, wt_left = CASES[name]
    return r["rc"] == rc and bool(r["merges"]) == merged and r["wt_exists"] == wt_left


MUTATIONS = {
    # 守る 1: UNKNOWN で止まらない
    "UNKNOWN を読めない値として扱う": (
        'if mergeable not in ("MERGEABLE", "UNKNOWN"):', 'if mergeable not in ("MERGEABLE",):'),
    # 守る 2: 検査が 0 本なら通過と読まない
    "検査 0 本を通過と読む": ('return "none", []', 'return "pass", []'),
    # 守る 3: 失敗した検査で止める
    "CheckRun の失敗を見ない": ('elif c.get("conclusion") not in CHECK_PASS:', 'elif False:'),
    # 守る 4: 衝突していればマージしない
    "CONFLICTING を見ない": ('if mergeable == "CONFLICTING":', 'if False:'),
    # 守る 5: 見ていないコミットをマージしない
    "--match-head-commit を渡さない": (
        '"--squash", "--match-head-commit", head_sha]', '"--squash"]'),
    # 守る 6: 未コミットを持つ worktree
    "未コミットを見ない": ('if git(["status", "--porcelain"], cwd=str(path)).strip():', 'if False:'),
    # 守る 7: push していない worktree
    "push を見ない": ('if local != head_sha:', 'if False:'),
    # 守る 8: 自分が中にいる worktree
    "cwd を見ない": ('if here == path.resolve():', 'if False:'),
    # 守る 9: ロックされた worktree も撤去できる
    "unlock しない": ('if wt["locked"]:', 'if False:'),
    # 守る 10: マージが失敗したら worktree を残す（撤去をマージの前に移す）
    "撤去をマージの前に置く": (
        '    res = run(["gh", "pr", "merge"',
        '    remove_worktree(wt) if wt and not wt["main"] else None\n    res = run(["gh", "pr", "merge"'),
    # 守る 11: 閉じるはずの Issue を確かめる
    "Issue が閉じたかを見ない": ('if wait_for(closed, a.interval, a.settle):', 'if True:'),
    # 守る 12: 判定できなかったことを時間切れと答えない
    "判定できなかったを時間切れと答える": ('        return 7\n', '        return 5\n'),
}

# 変異ごとに、赤になるはずの試料（陽性対照で緑だったものに限って読む）
KILLS = {
    "UNKNOWN を読めない値として扱う": ["UNKNOWN の後に MERGEABLE（ロック済み worktree）"],
    "検査 0 本を通過と読む": ["検査が 0 本なら時間切れ"],
    "CheckRun の失敗を見ない": ["CheckRun の失敗で止まる"],
    "CONFLICTING を見ない": ["衝突していれば止まる"],
    "--match-head-commit を渡さない": [],  # 引数で見る（下）
    "未コミットを見ない": ["未コミットがあればマージしない"],
    "push を見ない": ["push していなければマージしない"],
    "cwd を見ない": ["cwd が worktree の中ならマージしない"],
    "unlock しない": ["UNKNOWN の後に MERGEABLE（ロック済み worktree）"],
    "撤去をマージの前に置く": ["マージが失敗したら worktree を残す"],
    "Issue が閉じたかを見ない": ["Issue が閉じなければ 9"],
    "判定できなかったを時間切れと答える": ["gh が失敗したら判定できなかった"],
}


def merge_args_ok(r: dict) -> bool:
    return any(c[:4] == ["pr", "merge", "42", "--squash"] and "--match-head-commit" in c
               and c[c.index("--match-head-commit") + 1] == r["sha"] for c in r["merges"])


def docstring(source: str) -> str:
    return source.split('"""')[1]


def main() -> int:
    source = SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        print("陽性対照: 壊さない本体で、全試料が期待どおりか")
        good = run_all(base / "good", SCRIPT)
        for name, r in good.items():
            _, rc, merged, wt_left = CASES[name]
            check(f"{name}: rc={r['rc']}（期待 {rc}）・マージ {bool(r['merges'])}・worktree 残る {r['wt_exists']}",
                  as_expected(name, r))
        happy = good["UNKNOWN の後に MERGEABLE（ロック済み worktree）"]
        check("偽の gh が呼ばれている（本物の gh に届いていない）", bool(happy["calls"]))
        check("squash で、待って見た head の SHA を --match-head-commit に渡す", merge_args_ok(happy))
        check("UNKNOWN の間に読み直している（pr view が 3 回以上）",
              sum(1 for c in happy["calls"] if c[:2] == ["pr", "view"] and c[-1] != "state") >= 3)
        check("ブランチを消さない（--delete-branch を渡さない）",
              all("--delete-branch" not in c and "-d" not in c for c in happy["merges"]))

        print("\n変異（壊したのに緑なら失格）")
        if failures:
            print("  陽性対照が落ちているので、変異の結果は読まない")
        else:
            for i, (mname, (old, new)) in enumerate(MUTATIONS.items()):
                check(f"変異の当て先が 1 箇所だけ在る: {mname}", source.count(old) == 1)
                mutant = base / f"mutant{i}" / "merge-pr.py"
                mutant.parent.mkdir(parents=True)
                mutant.write_text(source.replace(old, new, 1), encoding="utf-8")
                targets = KILLS[mname]
                if not targets:
                    r = run_case(base / f"mutant{i}", "case", mutant, make_view=lambda s: [pr(s)])
                    check(f"{mname} → 赤", not merge_args_ok(r))
                    continue
                for t in targets:
                    kw = CASES[t][0]
                    r = run_case(base / f"mutant{i}", f"case-{targets.index(t)}", mutant, **kw)
                    check(f"{mname} → 赤（{t}）", not as_expected(t, r))

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        doc = docstring(source)
        section = doc.split("## 何を守るか")[1].split("## 終了コード")[0]
        promises = len([l for l in section.splitlines() if l.startswith("- ")])
        check(f"「守る」{promises} 行に対して変異が {len(MUTATIONS)} 件", promises == len(MUTATIONS))

        print("\n終了コードの一覧が本体と一致するか")
        codes_doc = {int(n) for n in re.findall(r"^- \*\*(\d+)\*\*:", doc.split("## 終了コード")[1]
                                                 .split("## 何を守らないか")[0], re.M)}
        body = source.split('"""', 2)[2]
        codes_src = {int(n) for n in re.findall(r"\breturn (\d+)\b", body)} | \
                    {int(n) for n in re.findall(r"sys\.exit\((\d+)\)", body)}
        check(f"一覧 {sorted(codes_doc)} が本体 {sorted(codes_src)} と一致", codes_doc == codes_src)
        check("試料が 0 以外の全終了コードを当てている（1 は引数の誤り）",
              {c[1] for c in CASES.values()} | {1} >= codes_src - {0})

        print("\n引数の誤りは 1")
        r = subprocess.run([sys.executable, str(SCRIPT), "abc"], capture_output=True, text=True, cwd=tmp)
        check(f"数字でない PR 番号で rc=1（実際 {r.returncode}）", r.returncode == 1)
        r = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=tmp)
        check(f"引数なしで rc=1（実際 {r.returncode}）", r.returncode == 1)

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("merge-pr.py のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
