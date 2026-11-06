#!/usr/bin/env python3
"""`cleanup-cycle.py` の回帰テスト（#823）。

    python3 scripts/test-cleanup-cycle.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/cruise/scripts/`。`test-merge-pr.py` と同じ形）。

**このテストは実環境を触らない。** 偽の `gh` を `PATH` の先頭に置き（**本物の GitHub に 1 度も届かない**）、
`git` は本物をテンポラリのリポジトリ（bare の `origin` と、その複製のメインの作業ツリー）にだけ当てる（`assert_not_real_repo` が担保する）。
**偽の `gh` が呼ばれたことも見る**——呼ばれていなければ、本物が走ったかもしれない。

**試料の形はハーネスの実物ではない**——隔離木は `git worktree add` で `agent-<id>`・`worktree-agent-<id>` の名前に作り、
PR の版に `checkout --detach` してロックした（#823 の Issue が書く tfs-stocks の残骸の形）。ハーネスが作る木の実物とは突き合わせていない。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**「守る」の行数と変異の数が 1 対 1 か**は、**テスト自身が数える。**
**陽性対照**: 壊さない本体で全試料が期待どおりになることを先に見る（そこで落ちれば変異の結果は読まない）。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "cleanup-cycle.py"

failures: list[str] = []

FAKE_GH = r'''#!/usr/bin/env python3
"""偽の gh。シナリオ（JSON）に従って答え、呼ばれた引数を記録する。"""
import json, os, sys
scn = json.load(open(os.environ["FAKE_GH_SCENARIO"], encoding="utf-8"))
with open(os.environ["FAKE_GH_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
args = sys.argv[1:]
if scn.get("fail_all"):
    print("gh: something went wrong", file=sys.stderr); sys.exit(1)
if args[:2] == ["pr", "view"]:
    print(json.dumps(scn["prs"][args[2]]))
elif args[:2] == ["pr", "list"]:
    print(json.dumps(scn.get("list", [])))
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
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return res.stdout


def commit(cwd: Path, name: str) -> str:
    (cwd / name).write_text(name + "\n", encoding="utf-8")
    git(cwd, "add", "-A")
    git(cwd, "commit", "-qm", name)
    return git(cwd, "rev-parse", "HEAD").strip()


WT = ".claude/worktrees"


def make_repo(root: Path) -> dict:
    """2 つの周（PR 1・PR 2）の木とブランチを持つリポジトリ。"""
    origin = root / "origin.git"
    main = root / "main"
    main.mkdir(parents=True)
    assert_not_real_repo(main)
    git(root, "init", "-q", "--bare", "-b", "main", str(origin))
    git(main, "init", "-q", "-b", "main")
    git(main, "config", "user.email", "t@example.invalid")
    git(main, "config", "user.name", "t")
    (main / ".git" / "info" / "exclude").write_text(".claude/\n", encoding="utf-8")
    commit(main, "README.md")
    git(main, "remote", "add", "origin", str(origin))
    git(main, "push", "-q", "-u", "origin", "main")
    git(main, "remote", "set-head", "origin", "main")
    w = main / WT
    # 周 1: 作業木・隔離木（PR の版に detached・ロック）・木の無い worktree-agent（先端が PR のコミット）
    git(main, "worktree", "add", "-q", str(w / "issue-1"), "-b", "issue/1-a")
    c1 = commit(w / "issue-1", "a.txt")
    git(w / "issue-1", "push", "-q", "origin", "issue/1-a")
    git(main, "worktree", "add", "-q", str(w / "agent-aaa"), "-b", "worktree-agent-aaa")
    git(w / "agent-aaa", "checkout", "-q", "--detach", c1)
    git(main, "worktree", "lock", "--reason", "claude agent agent-aaa (pid 1)", str(w / "agent-aaa"))
    git(main, "branch", "worktree-agent-ccc", c1)
    # 周 2（並行する別の周）: 作業木と隔離木
    git(main, "worktree", "add", "-q", str(w / "issue-2"), "-b", "issue/2-b")
    c2 = commit(w / "issue-2", "b.txt")
    git(w / "issue-2", "push", "-q", "origin", "issue/2-b")
    git(main, "worktree", "add", "-q", str(w / "agent-bbb"), "-b", "worktree-agent-bbb")
    git(w / "agent-bbb", "checkout", "-q", "--detach", c2)
    # どの周のものか決められない: main の先端にいる隔離木・先端が main の worktree-agent
    git(main, "worktree", "add", "-q", str(w / "agent-eee"), "-b", "worktree-agent-eee")
    git(main, "branch", "worktree-agent-ddd", "main")
    # .claude/worktrees の外に置いた専用の木（PR 1 の版にいる）
    git(main, "worktree", "add", "-q", "--detach", str(root / "deploy"), c1)
    return {"main": main, "origin": origin, "c1": c1, "c2": c2, "root": root}


def pr_view(head_ref: str, sha: str, state: str = "MERGED") -> dict:
    return {"state": state, "headRefName": head_ref, "headRefOid": sha, "commits": [{"oid": sha}]}


def state_of(r: dict) -> dict:
    main = r["main"]
    wts = set()
    for line in git(main, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            p = Path(line[len("worktree "):]).resolve()
            wts.add(str(p.relative_to(r["root"].resolve())))
    branches = set(git(main, "for-each-ref", "--format=%(refname:short)", "refs/heads/").split())
    remote = git(r["root"], "--git-dir", str(r["origin"]), "for-each-ref", "--format=%(refname) %(objectname)")
    tracking = git(main, "for-each-ref", "--format=%(refname) %(objectname)", "refs/remotes/")
    return {"wts": wts, "branches": branches, "remote": remote + tracking}


def run_case(base: Path, name: str, script: Path, *, prepare=None, scn=None, numbers=("1",),
             cwd_rel=None, sub="cycle") -> dict:
    root = base / name
    r = make_repo(root)
    if prepare:
        prepare(r)
    s = scn(r) if scn else {"prs": {"1": pr_view("issue/1-a", r["c1"]), "2": pr_view("issue/2-b", r["c2"])}}
    before = state_of(r)
    bin_dir = root / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text(FAKE_GH, encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    scn_path = root / "scenario.json"
    scn_path.write_text(json.dumps(s), encoding="utf-8")
    log = root / "gh.log"
    env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
               FAKE_GH_SCENARIO=str(scn_path), FAKE_GH_LOG=str(log))
    cwd = r["main"] / cwd_rel if cwd_rel else r["main"]
    rcs, out = [], ""
    for n in numbers:
        args = [sub, n] if sub == "cycle" else [sub]
        res = subprocess.run([sys.executable, str(script), *args], cwd=str(cwd), env=env,
                             capture_output=True, text=True)
        rcs.append(res.returncode)
        out += res.stdout + res.stderr
    after = state_of(r)
    calls = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    return {"rc": rcs[-1], "rcs": rcs, "out": out, "calls": calls, "before": before, **after}


MWT = "main/" + WT  # state_of の木は試料の根からの相対（メインの作業ツリーは main）
ALL_WTS = {"main", f"{MWT}/issue-1", f"{MWT}/agent-aaa", f"{MWT}/issue-2", f"{MWT}/agent-bbb", f"{MWT}/agent-eee", "deploy"}
CYCLE1_WTS = {f"{MWT}/issue-1", f"{MWT}/agent-aaa"}
CYCLE1_BRANCHES = {"issue/1-a", "worktree-agent-aaa", "worktree-agent-ccc"}
OTHERS = {"issue/2-b", "worktree-agent-bbb", "worktree-agent-ddd", "worktree-agent-eee", "main"}


def untracked(rel):
    def f(r):
        (r["main"] / WT / rel / "scratch.txt").write_text("x\n", encoding="utf-8")
    return f


def hidden_untracked(r):
    git(r["main"] / WT / "agent-aaa", "config", "status.showUntrackedFiles", "no")
    untracked("agent-aaa")(r)


def modified(r):
    (r["main"] / WT / "issue-1" / "a.txt").write_text("changed\n", encoding="utf-8")


def unpushed(r):
    commit(r["main"] / WT / "issue-1", "c.txt")


def removed_then_unpushed(r):
    commit(r["main"] / WT / "issue-1", "c.txt")
    git(r["main"], "worktree", "remove", str(r["main"] / WT / "issue-1"))


def dir_gone(r):
    shutil.rmtree(r["main"] / WT / "issue-1")


def not_merged(r):
    return {"prs": {"1": pr_view("issue/1-a", r["c1"], state="OPEN")}}


def remotes_scn(r):
    for b in ("chore/x", "chore/y", "chore/z"):
        git(r["main"], "push", "-q", "origin", f"main:refs/heads/{b}")
    git(r["main"], "fetch", "-q", "origin")
    return {"list": [{"headRefName": "issue/1-a", "state": "MERGED"},
                     {"headRefName": "issue/2-b", "state": "CLOSED"}, {"headRefName": "issue/2-b", "state": "OPEN"},
                     {"headRefName": "chore/y", "state": "CLOSED"},
                     {"headRefName": "chore/z", "state": "CLOSED"}, {"headRefName": "chore/z", "state": "MERGED"}]}


# 名前: (run_case の引数, rc, 在るべき木, 無いべき木, 在るべきブランチ, 無いべきブランチ, 出力に含む語…)
CASES = {
    "1 周を片付ける（ロック・detached の隔離木と木の無い worktree-agent を消し、他の周・外の木は残す）": (
        dict(), 0, ALL_WTS - CYCLE1_WTS, CYCLE1_WTS, OTHERS, CYCLE1_BRANCHES, "消した: worktree"),
    "未追跡がある隔離木は残し、未コミットと名指しする": (
        dict(prepare=untracked("agent-aaa")), 4, {f"{MWT}/agent-aaa"}, {f"{MWT}/issue-1"},
        {"worktree-agent-aaa"}, {"issue/1-a", "worktree-agent-ccc"}, "未コミットの変更", "agent-aaa"),
    "status.showUntrackedFiles=no でも未追跡を見る": (
        dict(prepare=hidden_untracked), 4, {f"{MWT}/agent-aaa"}, set(), set(), set(), "未コミットの変更"),
    "追跡しているファイルの変更がある作業木は残す": (
        dict(prepare=modified), 4, {f"{MWT}/issue-1"}, {f"{MWT}/agent-aaa"}, {"issue/1-a"}, set(), "未コミットの変更"),
    "push していないコミットにいる作業木は残す": (
        dict(prepare=unpushed), 4, {f"{MWT}/issue-1"}, {f"{MWT}/agent-aaa"}, {"issue/1-a"}, set(),
        "PR にも既定ブランチにも無い"),
    "木を消した後のブランチに PR に無いコミットがあれば、ブランチを残す": (
        dict(prepare=removed_then_unpushed), 4, set(), {f"{MWT}/agent-aaa"}, {"issue/1-a"}, {"worktree-agent-aaa"},
        "ブランチ issue/1-a"),
    "ディレクトリを手で消した作業木も、記録とブランチを消す": (
        dict(prepare=dir_gone), 0, set(), CYCLE1_WTS, OTHERS, CYCLE1_BRANCHES, "prune"),
    "MERGED でなければ何も消さない": (
        dict(scn=not_merged), 3, ALL_WTS, set(), CYCLE1_BRANCHES | OTHERS, set(), "OPEN"),
    "メインの作業ツリーの外から呼んだら何も消さない": (
        dict(cwd_rel=f"{WT}/issue-1"), 5, ALL_WTS, set(), CYCLE1_BRANCHES | OTHERS, set()),
    "gh が失敗したら判定できなかった（何も消さない）": (
        dict(scn=lambda r: {"fail_all": True}), 7, ALL_WTS, set(), CYCLE1_BRANCHES | OTHERS, set(), "判定できなかった"),
    "2 周を順に片付けると、両方の周の木もブランチも残らない": (
        dict(numbers=("1", "2")), 0, {"main", f"{MWT}/agent-eee", "deploy"},
        CYCLE1_WTS | {f"{MWT}/issue-2", f"{MWT}/agent-bbb"},
        {"main", "worktree-agent-ddd", "worktree-agent-eee"}, CYCLE1_BRANCHES | {"issue/2-b", "worktree-agent-bbb"}),
    "remotes: 本数と PR の状態ごとの内訳（OPEN → MERGED → CLOSED・PR なし・既定ブランチは数えない）": (
        dict(scn=remotes_scn, sub="remotes"), 0, ALL_WTS, set(), CYCLE1_BRANCHES | OTHERS, set(),
        "5 本——OPEN 1・MERGED 2・CLOSED 1・PR なし 1", "既定ブランチ main は数えていない"),
}


def run_all(base: Path, script: Path) -> dict:
    return {name: run_case(base, f"c{i}", script, **kw) for i, (name, (kw, *_)) in enumerate(CASES.items())}


def as_expected(name: str, r: dict) -> bool:
    _, rc, wt_in, wt_out, br_in, br_out, *said = CASES[name]
    return (r["rc"] == rc and wt_in <= r["wts"] and not (wt_out & r["wts"])
            and br_in <= r["branches"] and not (br_out & r["branches"])
            and r["remote"] == r["before"]["remote"]
            and all(t in r["out"] for t in said))


MUTATIONS = {
    # 守る 1: MERGED でない周では何も消さない
    "MERGED を見ない": ('if state != "MERGED":', "if False:"),
    # 守る 2: メインの作業ツリーの外から呼ばれたら何も消さない
    "呼んだ場所を見ない": ("if not in_main_worktree():", "if False:"),
    # 守る 3: この周のものと決められない木を消さない
    "どの木も周のものと読む": ('return wt["branch"] == head_ref or wt["head"] in oids', "return True"),
    # 守る 4: .claude/worktrees の外の木を消さない
    "場所を見ない": ("return Path(path).resolve().is_relative_to(root.resolve())", "return True"),
    # 守る 5: 未コミットの変更がある木は消さず、名指しする
    "未コミットを見ない": ("            if dirty:\n", "            if False:\n"),
    # 守る 6: HEAD が PR にも既定ブランチにも無い木を消さない
    "木の HEAD を見ない": ('if not safe(wt["head"], oids, ref):', "if False:"),
    # 守る 7: ロックされた木も消せる
    "unlock しない": ('if wt["locked"]:', "if False:"),
    # 守る 8: ブランチは先端が PR か既定ブランチに含まれるものだけ消す
    "ブランチの先端を見ない": ("if not safe(sha, oids, ref):", "if False:"),
    # 守る 9: 消すブランチは候補だけ
    "どのブランチも候補にする": ("if name not in candidates:", 'if name == "main":'),
    # 守る 10: ブランチを消す前に prune する
    "prune しない": ('        git(["worktree", "prune"])\n', "        pass\n"),
    # 守る 11: リモートのブランチに触らない
    "リモートのブランチを消す": ('res = run(["git", "branch", "-D", name])',
                         'res = run(["git", "push", "-q", "origin", "--delete", name])'),
    # 守る 12: 判定できなかったことを片付けたと答えない
    "判定できなかったを片付けたと答える": ('            print(f"  それまでに消した: {d}")\n        return 7',
                              '            print(f"  それまでに消した: {d}")\n        return 0'),
    # 守る 13: remotes は PR の無いブランチを「PR なし」に数える
    "PR の無いブランチを CLOSED に数える": ('if s in states), "PR なし")', 'if s in states), "CLOSED")'),
    # 守る 14: remotes は OPEN → MERGED → CLOSED の順で 1 つに数える
    "状態の順を逆にする": ('STATE_ORDER = ("OPEN", "MERGED", "CLOSED")', 'STATE_ORDER = ("CLOSED", "MERGED", "OPEN")'),
}

REMOTES = "remotes: 本数と PR の状態ごとの内訳（OPEN → MERGED → CLOSED・PR なし・既定ブランチは数えない）"
ONE = "1 周を片付ける（ロック・detached の隔離木と木の無い worktree-agent を消し、他の周・外の木は残す）"
KILLS = {
    "MERGED を見ない": ["MERGED でなければ何も消さない"],
    "呼んだ場所を見ない": ["メインの作業ツリーの外から呼んだら何も消さない"],
    "どの木も周のものと読む": [ONE],
    "場所を見ない": [ONE],
    "未コミットを見ない": ["未追跡がある隔離木は残し、未コミットと名指しする", "status.showUntrackedFiles=no でも未追跡を見る",
                          "追跡しているファイルの変更がある作業木は残す"],
    "木の HEAD を見ない": ["push していないコミットにいる作業木は残す"],
    "unlock しない": [ONE],
    "ブランチの先端を見ない": ["木を消した後のブランチに PR に無いコミットがあれば、ブランチを残す"],
    "どのブランチも候補にする": [ONE],
    "prune しない": ["ディレクトリを手で消した作業木も、記録とブランチを消す"],
    "リモートのブランチを消す": [ONE],
    "判定できなかったを片付けたと答える": ["gh が失敗したら判定できなかった（何も消さない）"],
    "PR の無いブランチを CLOSED に数える": [REMOTES],
    "状態の順を逆にする": [REMOTES],
}


def docstring(source: str) -> str:
    return source.split('"""')[1]


def main() -> int:
    source = SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        print("陽性対照: 壊さない本体で、全試料が期待どおりか")
        good = run_all(base / "good", SCRIPT)
        for name, r in good.items():
            check(f"{name}: rc={r['rc']}（期待 {CASES[name][1]}）", as_expected(name, r))
            if not as_expected(name, r):
                print("    " + r["out"].replace("\n", "\n    "))
        check("偽の gh が呼ばれている（本物の gh に届いていない）", bool(good[ONE]["calls"]))
        check("2 周の試料は 2 回とも 0", good["2 周を順に片付けると、両方の周の木もブランチも残らない"]["rcs"] == [0, 0])
        check("試料の前に、周 1 の木とブランチが在った（空振りでない）",
              CYCLE1_WTS <= good[ONE]["before"]["wts"] and CYCLE1_BRANCHES <= good[ONE]["before"]["branches"])
        check("試料の origin に周のブランチが在った（リモートを消さないことが空振りでない）",
              "refs/heads/issue/1-a" in good[ONE]["before"]["remote"])

        print("\n変異（壊したのに緑なら失格）")
        if failures:
            print("  陽性対照が落ちているので、変異の結果は読まない")
        else:
            for i, (mname, (old, new)) in enumerate(MUTATIONS.items()):
                check(f"変異の当て先が 1 箇所だけ在る: {mname}", source.count(old) == 1)
                mutant = base / f"mutant{i}" / "cleanup-cycle.py"
                mutant.parent.mkdir(parents=True)
                mutant.write_text(source.replace(old, new, 1), encoding="utf-8")
                for j, t in enumerate(KILLS[mname]):
                    r = run_case(base / f"mutant{i}", f"case-{j}", mutant, **CASES[t][0])
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
        codes_src = {int(n) for n in re.findall(r"\breturn (\d+)\b", body)}
        check(f"一覧 {sorted(codes_doc)} が本体 {sorted(codes_src)} と一致", codes_doc == codes_src)
        check("試料が 0・2 以外の全終了コードを当てている（2 は下で当てる）",
              {c[1] for c in CASES.values()} >= codes_src - {2})

        print("\n引数の誤りは 2")
        for argv in (["cycle", "abc"], ["cycle"], []):
            r = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True, cwd=tmp)
            check(f"{argv} で rc=2（実際 {r.returncode}）", r.returncode == 2)

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
    print("cleanup-cycle.py のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
