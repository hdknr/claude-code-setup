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
    v = seq[min(i, len(seq) - 1)]
    if v == "FAIL":  # この読みだけ gh が失敗する
        print("gh: something went wrong", file=sys.stderr); sys.exit(1)
    return v
if scn.get("fail_all"):
    print("gh: something went wrong", file=sys.stderr); sys.exit(1)
if args[:2] == ["pr", "view"]:
    fields = args[args.index("--json") + 1]
    if fields == "state":
        print(json.dumps({"state": nxt("after", scn.get("after", ["MERGED"]))}))
    elif fields == "commits":
        print(json.dumps({"commits": scn.get("commits", [{"oid": "c" * 40}])}))
    else:
        print(json.dumps(nxt("view", scn["view"])))
elif args[:2] == ["pr", "merge"]:
    rc = scn.get("merge_rc", 0)
    if rc:
        print("merge failed", file=sys.stderr)
    elif scn.get("merge_drop"):  # 点検のあとで worktree に未追跡を置き、撤去を失敗させる
        open(scn["merge_drop"], "w").write("late\n")
    sys.exit(rc)
elif args[:2] == ["repo", "view"]:
    name = scn.get("default", "main")
    if name == "FAIL":
        print("gh: something went wrong", file=sys.stderr); sys.exit(1)
    print(json.dumps({"defaultBranchRef": {"name": name}}))
elif args[:2] == ["pr", "list"]:
    out = scn.get("lowers", []) if "--head" in args else scn.get("merged", [])
    if out == "FAIL":
        print("gh: something went wrong", file=sys.stderr); sys.exit(1)
    print(json.dumps(out))
elif args[0] == "api" and "/compare/" in args[1]:
    ahead = scn.get("ahead", 0)
    if ahead == "FAIL":
        print("gh: something went wrong", file=sys.stderr); sys.exit(1)
    print(json.dumps({"ahead_by": ahead}))
elif args[0] == "api" and "--paginate" in args and args[2].endswith("/timeline"):
    rows = scn.get("timeline", [])
    if rows == "FAIL":
        print("gh: something went wrong", file=sys.stderr); sys.exit(1)
    print("\n".join(r if isinstance(r, str) else "\t".join(r) for r in rows))
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


def pr(sha: str, mergeable="MERGEABLE", checks=None, state="OPEN", draft=False, base="main") -> dict:
    if checks is None:
        checks = [{"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS"},
                  {"__typename": "StatusContext", "context": "ci/legacy", "state": "SUCCESS"}]
    return {"state": state, "isDraft": draft, "baseRefName": base, "mergeable": mergeable, "headRefName": BRANCH,
            "headRefOid": sha, "statusCheckRollup": checks,
            "closingIssuesReferences": [{"number": 42, "url": ISSUE_URL}]}


def run_case(base: Path, name: str, script: Path, make_view, *, lock=True, after=None, issues=None,
             merge_rc=0, fail_all=False, prepare=None, cwd_in_wt=False, timeout="5",
             merge_drop=False, default=None, **gh) -> dict:
    root = base / name
    main, wt, sha = make_repo(root, lock=lock)
    if prepare:
        prepare(main, wt)
    # 試料の "HEAD" は、この試料の head の SHA に置き換える（commits の oid と timeline の commit_id）
    gh = json.loads(json.dumps(gh).replace('"HEAD"', json.dumps(sha)))
    scn = {"view": make_view(sha), "merge_rc": merge_rc, "fail_all": fail_all, **gh}
    if after:
        scn["after"] = after
    if issues:
        scn["issues"] = issues
    if default:
        scn["default"] = default
    if merge_drop:
        scn["merge_drop"] = str(wt / "late.txt")
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
    # 待っている間に head が動く（UNKNOWN の間は別の SHA）——マージに渡すのは、待って見た最後の SHA
    return [pr("1" * 40, mergeable="UNKNOWN"), pr("1" * 40, mergeable="UNKNOWN"), pr(sha)]


def with_closing(closing):
    def make(sha):
        p = pr(sha)
        p["closingIssuesReferences"] = closing
        return [p]
    return make


def without(key):
    def make(sha):
        p = pr(sha)
        del p[key]
        return [p]
    return make


def untracked_hidden(main, wt):
    git(main, "config", "status.showUntrackedFiles", "no")
    (wt / "dirty.txt").write_text("d\n", encoding="utf-8")


LOWER = {"number": 41, "baseRefName": "main", "headRefName": "issue/41-lower", "isCrossRepository": False}


def CHANGED(at):
    return ["base_ref_changed", at, ""]


def FORCED(at, commit="HEAD"):
    return ["head_ref_force_pushed", at, commit]


def started(at):
    return [{"__typename": "CheckRun", "name": "check", "status": "COMPLETED", "conclusion": "SUCCESS",
             "startedAt": at},
            {"__typename": "StatusContext", "context": "ci/legacy", "state": "SUCCESS", "startedAt": at}]


def running_then(sha):
    running = [{"__typename": "CheckRun", "name": "check", "status": "IN_PROGRESS", "conclusion": None}]
    return [pr(sha, checks=running), pr(sha)]


CASES = {
    # 名前: (試料の引数, 期待する rc, マージが呼ばれるか, worktree が残るか[, 出力に要る文字列])
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
    "未追跡を隠す設定（showUntrackedFiles=no）でも見る": (
        dict(make_view=lambda s: [pr(s)], prepare=untracked_hidden), 6, False, True),
    "マージが失敗したら worktree を残す": (dict(make_view=lambda s: [pr(s)], merge_rc=1), 8, True, True),
    "merge が 0 でも MERGED にならなければ 8・worktree を残す": (
        dict(make_view=lambda s: [pr(s)], after=["OPEN"]), 8, True, True),
    "マージの後に gh が失敗したら判定できなかった（worktree を残す）": (
        dict(make_view=lambda s: [pr(s)], after=["FAIL"]), 7, True, True),
    "Issue の状態が読めなければ判定できなかった": (
        dict(make_view=lambda s: [pr(s)], issues={ISSUE_URL: ["FAIL"]}), 7, True, False),
    "閉じる Issue の形が読めなければマージしない": (dict(make_view=with_closing([None])), 7, False, True),
    "閉じる Issue の欄が無ければマージしない": (dict(make_view=without("closingIssuesReferences")), 7, False, True),
    "閉じる Issue の欄が null ならマージしない": (dict(make_view=with_closing(None)), 7, False, True),
    "state が無ければ判定できなかった": (dict(make_view=without("state")), 7, False, True),
    "isDraft が無ければ判定できなかった": (dict(make_view=without("isDraft")), 7, False, True),
    "CheckRun の conclusion が無ければ判定できなかった": (dict(make_view=lambda s: [pr(s, checks=[
        {"__typename": "CheckRun", "name": "check", "status": "COMPLETED"}])]), 7, False, True),
    "StatusContext の state が無ければ判定できなかった": (dict(make_view=lambda s: [pr(s, checks=[
        {"__typename": "StatusContext", "context": "ci"}])]), 7, False, True),
    "Issue が閉じなければ 9": (dict(make_view=lambda s: [pr(s)], issues={ISSUE_URL: ["OPEN"]}), 9, True, False),
    "撤去が失敗して Issue が閉じなければ 9・撤去の失敗を出す": (
        dict(make_view=lambda s: [pr(s)], merge_drop=True, issues={ISSUE_URL: ["OPEN"]}), 9, True, True,
        "worktree を撤去できなかった"),
    "撤去が失敗して Issue が読めなければ 7・撤去の失敗を出す": (
        dict(make_view=lambda s: [pr(s)], merge_drop=True, issues={ISSUE_URL: ["FAIL"]}), 7, True, True,
        "worktree を撤去できなかった"),
    "下がマージされたのに base が下のブランチのままならマージしない（積んだ周）": (
        dict(make_view=lambda s: [pr(s, base="issue/41-lower")], lowers=[LOWER], ahead=2),
        10, False, True, "載せ替えていない"),
    "base が既定ブランチでなくても、積んでいなければマージする（develop・#426）": (
        dict(make_view=lambda s: [pr(s, base="develop")]), 0, True, False),
    "base を head にするマージ済み PR があっても、その base に入っていればマージする": (
        dict(make_view=lambda s: [pr(s, base="develop")], lowers=[dict(LOWER, headRefName="develop")], ahead=0),
        0, True, False),
    "fork の同名ブランチのマージ済み PR は下の周と読まない": (
        dict(make_view=lambda s: [pr(s, base="develop")], lowers=[dict(LOWER, isCrossRepository=True)], ahead=2),
        0, True, False),
    "base が付け替わっても下の元のコミットがあればマージしない（#427 R4）": (
        dict(make_view=lambda s: [pr(s)], commits=[{"oid": "a" * 40}, {"oid": "b" * 40}],
             merged=[{"number": 41, "commits": [{"oid": "a" * 40}]}]), 10, False, True, "載せ替えていない"),
    "base に別のマージ済み PR があっても、コミットを共有しなければマージする": (
        dict(make_view=lambda s: [pr(s)], commits=[{"oid": "b" * 40}],
             merged=[{"number": 41, "commits": [{"oid": "a" * 40}]}]), 0, True, False),
    # 本物の GitHub（#427）の PR #4 の形: force push → 付け替え → 検査はその後に始まったが base_ref は前の base
    "付け替えより前に届いた head は、検査が後に始まっていてもマージしない（#427 R1）": (
        dict(make_view=lambda s: [pr(s, checks=started("2026-10-26T04:19:21Z"))],
             timeline=[FORCED("2026-10-26T04:19:15Z"), CHANGED("2026-10-26T04:19:16Z")],
             commits=[{"oid": "HEAD", "committedDate": "2026-10-26T04:19:14Z"}]), 11, False, True, "push し直す"),
    "付け替えの後のコミットならマージする": (
        dict(make_view=lambda s: [pr(s)], timeline=[CHANGED("2026-10-26T04:19:16Z")],
             commits=[{"oid": "HEAD", "committedDate": "2026-10-26T04:20:00Z"}]), 0, True, False),
    "付け替えの後の force push なら、古い日付のコミットでもマージする": (
        dict(make_view=lambda s: [pr(s)],
             timeline=[CHANGED("2026-10-26T04:19:16Z"), FORCED("2026-10-26T04:19:30Z")],
             commits=[{"oid": "HEAD", "committedDate": "2026-10-26T04:00:00Z"}]), 0, True, False),
    "別の head への force push は、届いた時刻に数えない": (
        dict(make_view=lambda s: [pr(s)],
             timeline=[CHANGED("2026-10-26T04:19:16Z"), FORCED("2026-10-26T04:19:30Z", "d" * 40)],
             commits=[{"oid": "HEAD", "committedDate": "2026-10-26T04:19:14Z"}]), 11, False, True),
    "自動の付け替えも付け替えに数える": (
        dict(make_view=lambda s: [pr(s)],
             timeline=[["automatic_base_change_succeeded", "2026-10-26T04:09:54Z", ""]],
             commits=[{"oid": "HEAD", "committedDate": "2026-10-26T04:08:00Z"}]), 11, False, True),
    "付け替えが無ければ head の時刻を見ない": (
        dict(make_view=lambda s: [pr(s)], timeline=[FORCED("2026-10-26T04:19:15Z")]), 0, True, False),
    "timeline が読めなければ判定できなかった": (
        dict(make_view=lambda s: [pr(s)], timeline="FAIL"), 7, False, True),
    "timeline の行の形が読めなければ判定できなかった": (
        dict(make_view=lambda s: [pr(s)], timeline=["base_ref_changed 2026-10-26T04:19:16Z"]), 7, False, True),
    "付け替えがあって head が commits に無ければ判定できなかった": (
        dict(make_view=lambda s: [pr(s)], timeline=[CHANGED("2026-10-26T04:19:16Z")]), 7, False, True),
    "compare が読めなければ判定できなかった": (
        dict(make_view=lambda s: [pr(s, base="issue/41-lower")], lowers=[LOWER], ahead="FAIL"), 7, False, True),
    "マージ済みの PR の一覧が読めなければ判定できなかった": (
        dict(make_view=lambda s: [pr(s)], merged="FAIL"), 7, False, True),
    "既定ブランチが main でなくても、base が既定ブランチならマージする": (
        dict(make_view=lambda s: [pr(s, base="master")], default="master"), 0, True, False),
    "既定ブランチが読めなければマージしない": (dict(make_view=lambda s: [pr(s)], default="FAIL"), 7, False, True),
    "baseRefName が無ければ判定できなかった": (dict(make_view=without("baseRefName")), 7, False, True),
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
    _, rc, merged, wt_left, *said = CASES[name]
    return (r["rc"] == rc and bool(r["merges"]) == merged and r["wt_exists"] == wt_left
            and all(t in r["out"] for t in said))


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
    # 守る 5: 下の周がマージされたのに base が下のブランチのまま
    "下のブランチがその base に入っているかを見ない": ('if ahead > 0:', 'if False:'),
    # 守る 6: base を既定ブランチでないことだけで止めない（#426）
    "base が既定ブランチでなければ止める": (
        'reason = unrebased(number, base, default)',
        'reason = unrebased(number, base, default) or (base != default and "base が既定ブランチでない")'),
    # 守る 7: base が付け替わっても載せ替えていない（#427 R4）
    "マージ済みの元のコミットを見ない": ('if shared:', 'if False:'),
    # 守る 8: 付け替えの後に回っていない検査（#427 R1）
    "付け替えの後の検査かを見ない": ('if stale:', 'if False:'),
    # 守る 6: 見ていないコミットをマージしない
    "--match-head-commit を渡さない": (
        '"--squash", "--match-head-commit", head_sha]', '"--squash"]'),
    # 守る 7: 未コミットを持つ worktree
    "未コミットを見ない": ('if git(["status", "--porcelain", "--untracked-files=all"], cwd=str(path)).strip():',
                          'if False:'),
    # 守る 8: push していない worktree
    "push を見ない": ('if local != head_sha:', 'if False:'),
    # 守る 9: 自分が中にいる worktree
    "cwd を見ない": ('if here == path.resolve():', 'if False:'),
    # 守る 10: ロックされた worktree も撤去できる
    "unlock しない": ('if wt["locked"]:', 'if False:'),
    # 守る 11: MERGED を確かめるまで worktree を残す（撤去をマージの前に移す）
    "撤去をマージの前に置く": (
        '        res = run(["gh", "pr", "merge"',
        '        remove_worktree(wt) if wt and not wt["main"] else None\n        res = run(["gh", "pr", "merge"'),
    # 守る 12: 閉じるはずの Issue を確かめる
    "Issue が閉じたかを見ない": ('if wait_for(closed, a.interval, a.settle):', 'if True:'),
    # 守る 13: 判定できなかったことを時間切れと答えない
    "判定できなかったを時間切れと答える": ('        return 7\n', '        return 5\n'),
    # 守る 14: 7 でも済んでいないことを出す
    "7 で済んでいないことを出さない": ('        for pr_ in problems:\n            print(f"  済んでいないこと',
                                 '        for pr_ in []:\n            print(f"  済んでいないこと'),
}

# 変異ごとに、赤になるはずの試料（陽性対照で緑だったものに限って読む）
KILLS = {
    "UNKNOWN を読めない値として扱う": ["UNKNOWN の後に MERGEABLE（ロック済み worktree）"],
    "検査 0 本を通過と読む": ["検査が 0 本なら時間切れ"],
    "CheckRun の失敗を見ない": ["CheckRun の失敗で止まる"],
    "CONFLICTING を見ない": ["衝突していれば止まる"],
    "下のブランチがその base に入っているかを見ない": ["下がマージされたのに base が下のブランチのままならマージしない（積んだ周）"],
    "base が既定ブランチでなければ止める": ["base が既定ブランチでなくても、積んでいなければマージする（develop・#426）",
                               "base を head にするマージ済み PR があっても、その base に入っていればマージする"],
    "マージ済みの元のコミットを見ない": ["base が付け替わっても下の元のコミットがあればマージしない（#427 R4）"],
    "付け替えの後の検査かを見ない": ["付け替えより前に届いた head は、検査が後に始まっていてもマージしない（#427 R1）",
                          "自動の付け替えも付け替えに数える"],
    "--match-head-commit を渡さない": [],  # 引数で見る（下）
    "未コミットを見ない": ["未コミットがあればマージしない", "未追跡を隠す設定（showUntrackedFiles=no）でも見る"],
    "push を見ない": ["push していなければマージしない"],
    "cwd を見ない": ["cwd が worktree の中ならマージしない"],
    "unlock しない": ["UNKNOWN の後に MERGEABLE（ロック済み worktree）"],
    "撤去をマージの前に置く": ["マージが失敗したら worktree を残す",
                       "merge が 0 でも MERGED にならなければ 8・worktree を残す"],
    "Issue が閉じたかを見ない": ["Issue が閉じなければ 9"],
    "判定できなかったを時間切れと答える": ["gh が失敗したら判定できなかった",
                            "マージの後に gh が失敗したら判定できなかった（worktree を残す）"],
    "7 で済んでいないことを出さない": ["撤去が失敗して Issue が読めなければ 7・撤去の失敗を出す"],
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
            _, rc, merged, wt_left, *_ = CASES[name]
            check(f"{name}: rc={r['rc']}（期待 {rc}）・マージ {bool(r['merges'])}・worktree 残る {r['wt_exists']}",
                  as_expected(name, r))
        happy = good["UNKNOWN の後に MERGEABLE（ロック済み worktree）"]
        check("偽の gh が呼ばれている（本物の gh に届いていない）", bool(happy["calls"]))
        check("squash で、待って見た head の SHA を --match-head-commit に渡す", merge_args_ok(happy))
        check("UNKNOWN の間に読み直している（pr view が 3 回以上）",
              sum(1 for c in happy["calls"] if c[:2] == ["pr", "view"] and c[-1] not in ("state", "commits")) >= 3)
        check("base と head が変わらない間は積んだ周の判定を引き直さない（commits を 1 回だけ読む）",
              sum(1 for c in good["検査が走っている間は待つ"]["calls"]
                  if c[:2] == ["pr", "view"] and c[-1] == "commits") == 1)
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
