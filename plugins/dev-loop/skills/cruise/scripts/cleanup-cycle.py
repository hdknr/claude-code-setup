#!/usr/bin/env python3
"""cruise の周を閉じるときに、その周が作った worktree とローカルブランチだけを片付ける。リモートのブランチは数えるだけ。

    python3 <このスキルの base ディレクトリ>/scripts/cleanup-cycle.py cycle <PR 番号>
    python3 <このスキルの base ディレクトリ>/scripts/cleanup-cycle.py remotes

**いつ呼ぶかは cruise の `SKILL.md` §4 の 4（`cycle`）と §6（`remotes`）を正とする**（#823）。
cwd のリポジトリに対して走る（`gh` も `git` も cwd から解決する）。**メインの作業ツリーから呼ぶ。**

## なぜ在るのか（#823）

spin-dd/tfs-stocks で cruise を回した後、メインの作業ツリーに Verifier・`/code-review` の隔離木（`.claude/worktrees/agent-*`）が 28 本、
周の作業木が 4 本、`worktree-agent-*` が 31 本、`issue/*` などが 24 本残っていた。`merge-pr.py` は PR の head の worktree だけを撤去し、
ブランチは消さない（squash したブランチは git から見て未マージなので）。SessionStart のフックは worktree の数だけ警告を出し、
次の周は生きている木と残骸を見分けられない。**周を閉じた時点なら、どれがその周のものかを PR から決められる。**

## `cycle <PR 番号>`: その周のものと決める式

PR（台帳のその行の `pr`）を `gh pr view --json state,headRefName,headRefOid,commits` で読み、**PR のコミット**（`commits` と `headRefOid`）を集める。

- **worktree**: `<メインの作業ツリー>/.claude/worktrees/` の下にあり、ブランチが PR の head のブランチか、HEAD が PR のコミットの 1 つ。
- **ローカルブランチ**: PR の head のブランチ・消した worktree のブランチ・消した worktree の名前に `worktree-` を付けたもの
  （隔離木 `agent-<id>` のブランチ `worktree-agent-<id>`）・先端が PR のコミットの `worktree-agent-*`。

**消す条件**: worktree は未コミットの変更が無く（未追跡を含む）、HEAD が PR のコミットか既定ブランチに含まれる。
ブランチは先端が PR のコミットか既定ブランチに含まれる。**既定ブランチ**は `refs/remotes/origin/HEAD` → `origin/main` → `origin/master` の順に決める
（手元の追跡参照。取り直さない）。順は worktree を消す → `git worktree prune` → ブランチを消す。

## 何を守るか

- **PR が `MERGED` でない周では、何も消さない**——閉じていない周の木を消すと、続きの作業を失う。
- **メインの作業ツリーの外から呼ばれたら、何も消さない**——自分が中にいる木を消しうる。
- **この周のものと決められない worktree を消さない**——ブランチが PR の head でも、HEAD が PR のコミットでもない木（並行する周・別のセッションの木。
  main の先端にいる隔離木も、どの周のものか決められないので残す）。
- **`.claude/worktrees/` の外の worktree を消さない**——メインのツリーの外に決まった名前で置いた専用の木（`tfs-stocks-deploy` など）は、PR のコミットにいても残す。
- **未コミットの変更（未追跡を含む。`status.showUntrackedFiles` に依らない）がある worktree は消さず、未コミットだと名指しする**——親が台帳と終える報告に載せる。
- **HEAD が PR のコミットでも既定ブランチに含まれるのでもない worktree を消さない**——push していないコミットにいる。
- **ロックされた worktree も消せる**——unlock してから `git worktree remove`（**`--force` は使わない**）。未コミットの木は unlock する前に残す。
- **ブランチは、先端が PR のコミットか既定ブランチに含まれるものだけ消す**——判定に `git branch --merged` を使わない（squash では出ない）。
- **消すブランチは上の式の候補だけ**——先端が main にいるだけの `worktree-agent-*` は、どの周のものか決められないので残す。
- **木を消した後、ブランチを消す前に `git worktree prune` する**——ディレクトリだけ消えた木の記録が残ると、そのブランチを git が消させない。
- **リモートのブランチと PR に触らない**——`push`・`fetch`・`gh pr close` を呼ばない。外から見える操作なので、`remotes` で数えて報告に載せるだけ。
- **判定できなかったことを、片付けた・残したと答えない**——`gh` や `git` が失敗した・出力が読めないなら 7。それまでに消したものは出力に出す。
- **`remotes` は、`origin` の追跡ブランチの本数と、PR の状態ごとの内訳を出し、PR の無いブランチを「PR なし」に数える**——既定ブランチは数えずに名前を出す。
- **`remotes` は、1 本のブランチに PR が複数あれば OPEN → MERGED → CLOSED の順で 1 つに数える**——開いている PR があるブランチを、閉じたものに数えない。

## 終了コード

- **0**: 片付けた（残したもの無し。消すものが 0 件でも 0）。`remotes` は数えた
- **2**: 引数の誤り
- **3**: PR が `MERGED` でない（何も消していない）
- **4**: 残したものがある——未コミット・PR にも既定ブランチにも無いコミット・撤去の失敗（**残りは片付けた。残したものは出力が名指しする**）
- **5**: メインの作業ツリーの外から呼んだ（何も消していない）
- **7**: 判定できなかった——`gh` や `git` が失敗した・出力が読めない（**それまでに消したものは出力が言う**）

## 何を守らないか

- **この周のものかを、PR のコミットだけで決める**——PR のコミットにいない隔離木（main の先端で作られ、そのまま使われた木）は、この周のものでも残る。
  先端が main にいるだけの `worktree-agent-*` も残る。**残った本数は出力の「この周のものと決められない」が言う。**
- **周の体が作った木の一覧を持たない**——台帳にも記録しない。別の周の PR の版を開いた木（レビューで他の PR を見た隔離木）は、その周の片付けで消える。
- **同じ PR のコミットを開いている、別のセッションの木も消す**——未コミットの変更が無ければ。動いている体の木かは見ない（ロックも外す）。
- **`gh pr view` の `commits` は GitHub の上限（250 件）まで**——それより多いコミットの PR は、古いコミットにいる木を決められない。
- **ignore されたファイルは見ない**——`git worktree remove` は ignore されたファイルを持つ木を消す（`.env` など）。`merge-pr.py` と同じ。
- **既定ブランチは手元の追跡参照で見る**——取り直さないので、古ければ「含まれる」と言えずに残す側に倒れる。
- **`remotes` は最後に取った時点の追跡参照を数える**——`fetch --prune` していなければ、消えたブランチも数える。
- **`remotes` が読む PR は `gh pr list --state all --limit 1000` まで**——当たった件数が上限なら、そう出す。fork から出た PR の head の名前が重なっても見分けない。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PR_LIMIT = 1000
STATE_ORDER = ("OPEN", "MERGED", "CLOSED")


class Undetermined(Exception):
    pass


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except OSError as e:
        raise Undetermined(f"{cmd[0]} を起動できなかった: {e}") from e


def git(args: list[str], cwd: str | None = None) -> str:
    res = run(["git", *args], cwd=cwd)
    if res.returncode != 0:
        raise Undetermined(f"git {' '.join(args)} が失敗した: {res.stderr.strip()}")
    return res.stdout


def gh_json(args: list[str]):
    res = run(["gh", *args])
    if res.returncode != 0:
        raise Undetermined(f"gh {' '.join(args)} が失敗した: {res.stderr.strip()}")
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise Undetermined(f"gh {' '.join(args)} の出力が JSON でない: {e}") from e


def in_main_worktree() -> bool:
    out = git(["rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"]).splitlines()
    if len(out) != 2:
        raise Undetermined("git rev-parse の出力が読めない")
    return out[0] == out[1]


def worktrees() -> list[dict]:
    """`git worktree list --porcelain` の各木。先頭はメインの作業ツリー。"""
    blocks, cur = [], {}
    for line in git(["worktree", "list", "--porcelain"]).splitlines() + [""]:
        if not line:
            if cur:
                blocks.append(cur)
            cur = {}
            continue
        key, _, value = line.partition(" ")
        cur[key] = value
    out = []
    for b in blocks:
        if "worktree" not in b:
            raise Undetermined("git worktree list の出力に worktree の行が無い")
        branch = b.get("branch", "")
        out.append({"path": b["worktree"], "head": b.get("HEAD", ""),
                    "branch": branch[len("refs/heads/"):] if branch.startswith("refs/heads/") else "",
                    "locked": "locked" in b, "prunable": "prunable" in b})
    if not out:
        raise Undetermined("git worktree list が 1 本も返さない")
    return out


def default_ref() -> str | None:
    res = run(["git", "symbolic-ref", "-q", "refs/remotes/origin/HEAD"])
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    for ref in ("refs/remotes/origin/main", "refs/remotes/origin/master"):
        if run(["git", "rev-parse", "-q", "--verify", ref]).returncode == 0:
            return ref
    return None


def contained(sha: str, ref: str | None) -> bool:
    if not ref or not sha:
        return False
    res = run(["git", "merge-base", "--is-ancestor", sha, ref])
    if res.returncode in (0, 1):
        return res.returncode == 0
    raise Undetermined(f"git merge-base --is-ancestor {sha[:12]} {ref} が失敗した: {res.stderr.strip()}")


def safe(sha: str, oids: set[str], ref: str | None) -> bool:
    return sha in oids or contained(sha, ref)


def ours(wt: dict, head_ref: str, oids: set[str]) -> bool:
    return wt["branch"] == head_ref or wt["head"] in oids


def under(path: str, root: Path) -> bool:
    return Path(path).resolve().is_relative_to(root.resolve())


def cmd_cycle(number: str) -> int:
    done: list[str] = []
    try:
        if not in_main_worktree():
            print("メインの作業ツリーの外から呼ばれた——何も消していない（メインの作業ツリーから呼ぶ）")
            return 5
        pr = gh_json(["pr", "view", number, "--json", "state,headRefName,headRefOid,commits"])
        try:
            state, head_ref = pr["state"], pr["headRefName"]
            oids = {c["oid"] for c in pr["commits"]} | {pr["headRefOid"]}
        except (KeyError, TypeError) as e:
            raise Undetermined(f"gh pr view の出力の形が違う: {e}") from e
        if state != "MERGED":
            print(f"PR #{number} は {state}——周は閉じていないので、何も消していない")
            return 3
        ref = default_ref()
        print(f"PR #{number}（{head_ref}）の周を片付ける。既定ブランチ: {ref or '決められない（PR のコミットだけで判定する）'}")
        all_wts = worktrees()
        main_path = Path(all_wts[0]["path"])
        root = main_path / ".claude" / "worktrees"
        kept: list[str] = []
        untouched = 0
        removed: list[dict] = []
        pruned: list[str] = []
        for wt in all_wts[1:]:
            if not ours(wt, head_ref, oids):
                untouched += 1
                continue
            if not under(wt["path"], root):
                print(f"  触っていない: worktree {wt['path']}（.claude/worktrees の外）")
                continue
            if wt["prunable"] or not Path(wt["path"]).is_dir():
                removed.append(wt)  # ディレクトリが無い——下の prune が記録を消す
                pruned.append(wt["path"])
                continue
            dirty = git(["status", "--porcelain", "--untracked-files=all"], cwd=wt["path"]).splitlines()
            if dirty:
                kept.append(f"worktree {wt['path']}（未コミットの変更 {len(dirty)} 件）")
                continue
            if not safe(wt["head"], oids, ref):
                kept.append(f"worktree {wt['path']}（HEAD {wt['head'][:12]} が PR にも既定ブランチにも無い）")
                continue
            if wt["locked"]:
                res = run(["git", "worktree", "unlock", wt["path"]])
                if res.returncode != 0:
                    kept.append(f"worktree {wt['path']}（unlock に失敗した: {res.stderr.strip()}）")
                    continue
            res = run(["git", "worktree", "remove", wt["path"]])
            if res.returncode != 0:
                kept.append(f"worktree {wt['path']}（git worktree remove に失敗した: {res.stderr.strip()}）")
                continue
            removed.append(wt)
            done.append(f"worktree {wt['path']}")
            print(f"  消した: worktree {wt['path']}")
        git(["worktree", "prune"])
        for path in pruned:
            done.append(f"worktree の記録 {path}")
            print(f"  消した: worktree の記録 {path}（ディレクトリが無かった。prune）")
        candidates = {head_ref} | {w["branch"] for w in removed if w["branch"]} | \
                     {"worktree-" + Path(w["path"]).name for w in removed}
        heads = {}
        for line in git(["for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads/"]).splitlines():
            name, _, sha = line.partition(" ")
            heads[name] = sha
        for name, sha in heads.items():
            if name.startswith("worktree-agent-") and sha in oids:
                candidates.add(name)
        untouched_branches = 0
        for name in sorted(heads):
            sha = heads[name]
            if name not in candidates:
                if name.startswith("worktree-agent-"):
                    untouched_branches += 1
                continue
            if not safe(sha, oids, ref):
                kept.append(f"ブランチ {name}（先端 {sha[:12]} が PR にも既定ブランチにも無い）")
                continue
            res = run(["git", "branch", "-D", name])
            if res.returncode != 0:
                kept.append(f"ブランチ {name}（git branch -D に失敗した: {res.stderr.strip()}）")
                continue
            done.append(f"ブランチ {name}")
            print(f"  消した: ブランチ {name}")
        print(f"この周のものと決められない: worktree {untouched} 本・worktree-agent-* のブランチ {untouched_branches} 本（触っていない）")
        print("リモートのブランチと PR には触っていない（`remotes` で数える）")
        if kept:
            for k in kept:
                print(f"  残した: {k}")
            print(f"残したもの {len(kept)} 件——台帳のこの周の行の note に「片付けで残した: …」と書いて、終える報告で渡す")
            return 4
        print("片付けた（残したもの無し）")
        return 0
    except Undetermined as e:
        print(f"判定できなかった: {e}")
        for d in done:
            print(f"  それまでに消した: {d}")
        return 7


def cmd_remotes() -> int:
    try:
        ref = default_ref()
        default = ref.rsplit("/", 1)[-1] if ref else ""
        names = [n for n in git(["for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/"]).splitlines()
                 if n and n not in ("origin", "origin/HEAD")]
        prs = gh_json(["pr", "list", "--state", "all", "--limit", str(PR_LIMIT), "--json", "headRefName,state"])
        try:
            by_head: dict[str, set[str]] = {}
            for p in prs:
                by_head.setdefault(p["headRefName"], set()).add(p["state"])
        except (KeyError, TypeError) as e:
            raise Undetermined(f"gh pr list の出力の形が違う: {e}") from e
    except Undetermined as e:
        print(f"判定できなかった: {e}")
        return 7
    counts = {s: 0 for s in STATE_ORDER} | {"PR なし": 0}
    for n in names:
        branch = n[len("origin/"):]
        if branch == default:
            continue
        states = by_head.get(branch, set())
        kind = next((s for s in STATE_ORDER if s in states), "PR なし")
        counts[kind] += 1
    total = sum(counts.values())
    detail = "・".join(f"{k} {v}" for k, v in counts.items())
    print(f"リモートのブランチ（origin。最後に取った時点）: {total} 本——{detail}"
          + (f"（既定ブランチ {default} は数えていない）" if default else ""))
    if len(prs) >= PR_LIMIT:
        print(f"PR を {PR_LIMIT} 件まで読んだ——それより古い PR の状態は内訳に入っていない")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="cruise の周の worktree とローカルブランチを片付ける")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cycle")
    c.add_argument("number")
    sub.add_parser("remotes")
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if a.cmd == "cycle":
        if not a.number.isascii() or not a.number.isdigit():
            print(f"PR 番号が数字でない: {a.number}")
            return 2
        return cmd_cycle(a.number)
    return cmd_remotes()


if __name__ == "__main__":
    sys.exit(main())
