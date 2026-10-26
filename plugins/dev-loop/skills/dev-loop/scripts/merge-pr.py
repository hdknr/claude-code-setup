#!/usr/bin/env python3
"""PR をマージする手続きを 1 本にする——CI を待ち、worktree を点検し、squash し、後を片付けて確かめる。

    python3 <このスキルの base ディレクトリ>/scripts/merge-pr.py <PR 番号> [--interval 秒] [--timeout 秒] [--settle 秒]

**マージすると決めた後の手続きだけ**を担う（#389）。**マージしてよいかは決めない**
——承認は人間か、人間が許した範囲の判断である（`SKILL.md` 手順 7）。
cwd のリポジトリに対して走る（`gh` も `git` も cwd から解決する）。**メインの作業ツリーから呼ぶ。**

## なぜスクリプトなのか

**#389 の周で、親が手で書いたマージのスクリプトが 2 つの罠を踏んだ**:

- **別の PR をマージした直後、`mergeable` が `UNKNOWN` を返した**（GitHub が計算し直している間の値）。
  **即時判定のスクリプトはそこで止まった（2 回）。** 待って読み直せば `MERGEABLE` になる。
- **`Agent` の `isolation: worktree` が作る worktree はロックされている。**
  `git worktree remove` が `locked working tree … claude agent …` で失敗し、
  未コミット・push を確かめてから `git worktree unlock` が要った。

## 何を守るか

- **`UNKNOWN` で止まらない**——`mergeable` が `UNKNOWN` の間は、期限まで待って読み直す。
- **CI が全部通るまでマージしない**——走っている検査があれば待つ。**検査が 0 本なら通過と読まない**
  （`CONFLICTING` の PR は `no checks reported` で CI が 1 本も走っていなかった。`CLAUDE.md`）。
- **失敗した検査があれば、期限を待たずに止める**——`CheckRun` は `conclusion`、`StatusContext` は `state` で読む。
- **衝突していればマージしない**——`CONFLICTING` は待っても直らない。
- **base が既定ブランチでない PR をマージしない**——積んだ周（stacked）の PR は下の周のブランチを base にしている。
  下を squash してもそのブランチは残る（下の「ブランチを消さない」）ので、**載せ替えずにマージすると上の変更は
  既定ブランチではなく下のブランチへ入り、止まらない**（#392。載せ替えは `references/stacked.md`）。
- **見ていないコミットをマージしない**——待って確かめた head の SHA を `--match-head-commit` に渡す。
- **未コミットの変更を持つ worktree のブランチをマージしない**——撤去で失う。
  未追跡は `status.showUntrackedFiles` の設定に依らず見る（`no` だと見落とし、撤去で黙って消える）。
- **push していない worktree のブランチをマージしない**——worktree の HEAD と PR の head の SHA を突き合わせる。
- **自分が中にいる worktree を撤去しようとしない**——cwd がその worktree の中なら、マージの前に止める。
- **ロックされた worktree も撤去できる**——unlock してから `git worktree remove`（**`--force` は使わない**）。
- **`MERGED` を確かめるまで worktree を残す**——撤去はその後に置く（点検はマージの前に済ませる）。
  `gh pr merge` が 0 で終わっても `MERGED` とは限らない（マージキューに入っただけのことがある）。
- **閉じるはずの Issue が閉じたかを確かめる**——`closingIssuesReferences` の各 Issue が `CLOSED` になるまで待つ。
- **判定できなかったことを、通った・時間切れ・閉じないと答えない**——`gh` や `git` が失敗した・
  出力の形が読めないなら、**マージの前でも後でも** 7 で止める。
- **7 で止めても、済んでいないことを黙らない**——それまでに積んだ撤去の失敗などは、7 の出力にも出す。

## 終了コード

- **0**: マージした（worktree を撤去し、閉じるはずの Issue が閉じた）
- **1**: 引数の誤り
- **2**: PR が `OPEN` でない・draft である（何もしていない）
- **3**: 失敗した検査がある（マージしていない）
- **4**: 衝突している（マージしていない）
- **5**: 時間切れ——期限までに CI が通りきらない・`UNKNOWN` のまま・検査が 0 本（マージしていない）
- **6**: worktree が撤去できる状態にない——未コミット・push していない・cwd がその中（マージしていない）
- **7**: 判定できなかった——`gh` や `git` が失敗した・出力が読めない（**どの段かと、マージ・撤去が
  済んだかは出力が言う**。`MERGED` を確かめられないまま 7 になったときは worktree を残している）
- **8**: マージできなかった——`gh pr merge` が失敗した・0 で終わったのに期限までに `MERGED` にならない
  （worktree は残っている）
- **9**: **マージはした**（`MERGED` を確かめた）が、後片付けか確かめが済んでいない——
  worktree を撤去できなかった・閉じるはずの Issue が閉じない
- **10**: PR の base が既定ブランチでない——積んだ周を載せ替えていない（マージしていない。
  `references/stacked.md` の「下の周がマージされたら」）

## 何を守らないか

- **ブランチを消さない**——squash したブランチは git から見て未マージなので `git branch -d` が通らず、
  `-D` は破壊的である。ローカルもリモートも残す。
- **本物の `gh` の出力形はテストしていない**——テストは偽の `gh` で当てる（形は gh 2.92.0 の
  `gh pr view --json` で 1 度見ただけ）。
- **必須の検査と任意の検査を分けない**——`statusCheckRollup` の全部を見る。任意の検査が落ちても止まる。
- **`Refs` で開けたままにした Issue は確かめない**——閉じるはずのもの（`closingIssuesReferences`）だけ。
- **head ブランチがメインの作業ツリーにあるときは撤去しない**——点検（未コミット・push）だけ当てる。
- **ignore されたファイルは点検しない**——撤去で失う（`.env` など）。見ると `.venv` や `__pycache__` を
  持つふつうの worktree が撤去できなくなる。
- **呼んだ側のセッションの cwd は見ない**——見るのはこのスクリプトの cwd だけ。`cd` してから呼べば素通りする。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PR_FIELDS = "state,isDraft,baseRefName,mergeable,headRefName,headRefOid,closingIssuesReferences,statusCheckRollup"

CHECK_PASS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
STATUS_PENDING = {"PENDING", "EXPECTED"}


class Undetermined(Exception):
    """`gh` や `git` が失敗した・出力が読めない。"""


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except OSError as e:
        raise Undetermined(f"{cmd[0]} を起動できなかった: {e}") from e


def gh_json(args: list[str]) -> dict:
    res = run(["gh", *args])
    if res.returncode != 0:
        raise Undetermined(f"gh {' '.join(args)} が失敗した（rc={res.returncode}）: {res.stderr.strip()}")
    try:
        data = json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise Undetermined(f"gh {' '.join(args)} の出力が JSON として読めない: {e}") from e
    if not isinstance(data, dict):
        raise Undetermined(f"gh {' '.join(args)} の出力がオブジェクトでない")
    return data


def git(args: list[str], cwd: str | None = None) -> str:
    res = run(["git", *args], cwd=cwd)
    if res.returncode != 0:
        raise Undetermined(f"git {' '.join(args)} が失敗した（rc={res.returncode}）: {res.stderr.strip()}")
    return res.stdout


def view_pr(number: str) -> dict:
    return gh_json(["pr", "view", number, "--json", PR_FIELDS])


def default_branch() -> str:
    data = gh_json(["repo", "view", "--json", "defaultBranchRef"])
    ref = data.get("defaultBranchRef")
    name = ref.get("name") if isinstance(ref, dict) else None
    if not isinstance(name, str) or not name:
        raise Undetermined(f"既定ブランチが読めない: {ref!r}")
    return name


def classify_checks(rollup) -> tuple[str, list[str]]:
    """検査を `pass` / `pending` / `fail` / `none` に分ける。2 つ目は名指しする検査。"""
    if not isinstance(rollup, list):
        raise Undetermined("statusCheckRollup が配列でない")
    if not rollup:
        return "none", []
    failed, pending = [], []
    for c in rollup:
        if not isinstance(c, dict):
            raise Undetermined(f"検査の形が読めない: {c!r}")
        kind = c.get("__typename")
        name = c.get("name") or c.get("context") or "(名前なし)"
        if kind == "CheckRun":
            if not isinstance(c.get("status"), str):
                raise Undetermined(f"検査の status が読めない: {c!r}")
            if c.get("status") != "COMPLETED":
                pending.append(name)
            elif not isinstance(c.get("conclusion"), str):
                raise Undetermined(f"検査の conclusion が読めない: {c!r}")
            elif c.get("conclusion") not in CHECK_PASS:
                failed.append(f"{name}（{c.get('conclusion')}）")
        elif kind == "StatusContext":
            state = c.get("state")
            if not isinstance(state, str):
                raise Undetermined(f"検査の state が読めない: {c!r}")
            if state in STATUS_PENDING:
                pending.append(name)
            elif state != "SUCCESS":
                failed.append(f"{name}（{state}）")
        else:
            raise Undetermined(f"検査の型が読めない: {kind!r}")
    if failed:
        return "fail", failed
    if pending:
        return "pending", pending
    return "pass", []


def wait_until_ready(number: str, default: str, interval: float, timeout: float) -> tuple[int, dict]:
    """CI が全部通り、`MERGEABLE` になるまで待つ。(終了コード, 最後に読んだ PR)。0 なら進んでよい。"""
    deadline = time.monotonic() + timeout
    while True:
        pr = view_pr(number)
        if not isinstance(pr.get("state"), str) or not isinstance(pr.get("isDraft"), bool):
            raise Undetermined(f"state・isDraft が読めない: {pr.get('state')!r}・{pr.get('isDraft')!r}")
        if pr.get("state") != "OPEN":
            print(f"PR #{number} は {pr.get('state')} である。何もしない。", file=sys.stderr)
            return 2, pr
        if pr.get("isDraft"):
            print(f"PR #{number} は draft である。何もしない。", file=sys.stderr)
            return 2, pr
        base = pr.get("baseRefName")
        if not isinstance(base, str) or not base:
            raise Undetermined(f"baseRefName が読めない: {base!r}")
        if base != default:
            print(f"PR #{number} の base は {base} で、既定ブランチ {default} でない（積んだ周を載せ替えていない）。"
                  "マージしない。", file=sys.stderr)
            return 10, pr
        mergeable = pr.get("mergeable")
        checks, names = classify_checks(pr.get("statusCheckRollup"))
        if checks == "fail":
            print(f"失敗した検査がある: {', '.join(names)}。マージしない。", file=sys.stderr)
            return 3, pr
        if mergeable == "CONFLICTING":
            print("衝突している（CONFLICTING）。マージしない。", file=sys.stderr)
            return 4, pr
        if mergeable not in ("MERGEABLE", "UNKNOWN"):
            raise Undetermined(f"mergeable が読めない: {mergeable!r}")
        if checks == "pass" and mergeable == "MERGEABLE":
            return 0, pr
        waiting = []
        if mergeable == "UNKNOWN":
            waiting.append("mergeable が UNKNOWN（計算中）")
        if checks == "pending":
            waiting.append(f"走っている検査: {', '.join(names)}")
        if checks == "none":
            waiting.append("検査が 0 本（まだ始まっていないか、走っていない）")
        if time.monotonic() >= deadline:
            print(f"時間切れ（{timeout:g} 秒）: {' / '.join(waiting)}。マージしない。", file=sys.stderr)
            return 5, pr
        print(f"待つ: {' / '.join(waiting)}")
        time.sleep(interval)


def find_worktree(branch: str) -> dict | None:
    """head ブランチを持つ worktree。`main` はメインの作業ツリーかどうか。"""
    out = git(["worktree", "list", "--porcelain"])
    blocks, cur = [], {}
    for line in out.splitlines():
        if not line:
            if cur:
                blocks.append(cur)
            cur = {}
            continue
        key, _, value = line.partition(" ")
        cur[key] = value
    if cur:
        blocks.append(cur)
    for i, b in enumerate(blocks):
        if b.get("branch") == f"refs/heads/{branch}":
            if "worktree" not in b:
                raise Undetermined("git worktree list の出力に worktree の行が無い")
            return {"path": b["worktree"], "head": b.get("HEAD", ""),
                    "locked": "locked" in b, "main": i == 0}
    return None


def inspect_worktree(wt: dict, head_sha: str) -> list[str]:
    """マージの前の点検。撤去できない理由の一覧（空なら撤去できる）。"""
    reasons = []
    path = Path(wt["path"])
    if not path.is_dir():
        raise Undetermined(f"worktree のディレクトリが無い: {path}（git worktree prune を検討）")
    if git(["status", "--porcelain", "--untracked-files=all"], cwd=str(path)).strip():
        reasons.append(f"未コミットの変更がある: {path}")
    local = git(["rev-parse", "HEAD"], cwd=str(path)).strip()
    if local != head_sha:
        reasons.append(f"worktree の HEAD {local[:12]} が PR の head {head_sha[:12]} と違う（push していないか、古い）")
    if not wt["main"]:
        here = Path(git(["rev-parse", "--show-toplevel"]).strip()).resolve()
        if here == path.resolve():
            reasons.append(f"cwd が撤去する worktree の中にある: {path}（メインの作業ツリーから呼ぶ）")
    return reasons


def remove_worktree(wt: dict) -> str | None:
    """撤去する。失敗の理由（成功なら None）。"""
    path = wt["path"]
    if wt["locked"]:
        res = run(["git", "worktree", "unlock", path])
        if res.returncode != 0:
            return f"unlock に失敗した: {res.stderr.strip()}"
    res = run(["git", "worktree", "remove", path])
    if res.returncode != 0:
        return f"git worktree remove に失敗した: {res.stderr.strip()}"
    return None


def wait_for(fn, interval: float, timeout: float) -> bool:
    """`fn` が真になるまで待つ。期限の最後の読みが `Undetermined` なら、偽ではなくそれを投げる。"""
    deadline = time.monotonic() + timeout
    while True:
        try:
            if fn():
                return True
            err = None
        except Undetermined as e:
            err = e
        if time.monotonic() >= deadline:
            if err:
                raise err
            return False
        time.sleep(interval)


def closing_refs(pr: dict) -> list[str]:
    """閉じるはずの Issue。形が読めなければ、マージの前に `Undetermined`。"""
    closing = pr.get("closingIssuesReferences")
    if not isinstance(closing, list):
        raise Undetermined(f"closingIssuesReferences が配列でない: {closing!r}")
    refs = []
    for issue in closing:
        ref = (issue.get("url") or issue.get("number")) if isinstance(issue, dict) else None
        if not ref:
            raise Undetermined(f"closingIssuesReferences の要素が読めない: {issue!r}")
        refs.append(str(ref))
    return refs


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"引数の誤り: {message}", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str]) -> int:
    p = Parser(description="PR を待ってから squash マージし、worktree を片付けて確かめる。")
    p.add_argument("number", help="PR 番号")
    p.add_argument("--interval", type=float, default=30, help="読み直す間隔（秒）")
    p.add_argument("--timeout", type=float, default=3600, help="CI と mergeable を待つ期限（秒）")
    p.add_argument("--settle", type=float, default=300, help="マージの後、MERGED と Issue の CLOSED を待つ期限（秒）")
    a = p.parse_args(argv)
    if not a.number.isdigit():
        p.error(f"PR 番号が数字でない: {a.number!r}")

    done = []  # 判定できなかったときに、どこまで済んだかを言う
    problems = []  # 同じく、済んでいないことを言う
    try:
        rc, pr = wait_until_ready(a.number, default_branch(), a.interval, a.timeout)
        if rc:
            return rc
        head_sha = pr.get("headRefOid") or ""
        branch = pr.get("headRefName") or ""
        if not head_sha or not branch:
            raise Undetermined("headRefOid / headRefName が読めない")
        closing = closing_refs(pr)
        print(f"CI は全部通り、MERGEABLE である。head: {branch} @ {head_sha[:12]}")

        wt = find_worktree(branch)
        if wt:
            reasons = inspect_worktree(wt, head_sha)
            if reasons:
                for r in reasons:
                    print(f"**撤去できない**: {r}", file=sys.stderr)
                print("マージしない。", file=sys.stderr)
                return 6
            where = "メインの作業ツリー（撤去しない）" if wt["main"] else wt["path"]
            print(f"worktree を点検した: {where}{'（ロックされている）' if wt['locked'] else ''}")
        else:
            print(f"ブランチ {branch} を持つ worktree は無い。")

        res = run(["gh", "pr", "merge", a.number, "--squash", "--match-head-commit", head_sha])
        if res.returncode != 0:
            print(f"マージに失敗した（rc={res.returncode}）: {res.stderr.strip()}", file=sys.stderr)
            print("worktree は残してある。", file=sys.stderr)
            return 8
        done.append(f"gh pr merge は 0 で終わった（{head_sha[:12]}）が、MERGED はまだ確かめていない。worktree は残してある")

        def merged() -> bool:
            return gh_json(["pr", "view", a.number, "--json", "state"]).get("state") == "MERGED"

        if not wait_for(merged, a.interval, a.settle):
            print(f"gh pr merge は 0 で終わったが、PR #{a.number} が {a.settle:g} 秒で MERGED にならない"
                  "（マージキューに入っただけかもしれない）。worktree は残してある。", file=sys.stderr)
            return 8
        done[-1] = f"PR #{a.number} を squash マージした（{head_sha[:12]}・MERGED を確かめた）"
        print(f"{done[-1]}。")

        if wt and not wt["main"]:
            err = remove_worktree(wt)
            if err:
                problems.append(f"worktree を撤去できなかった（{wt['path']}）: {err}")
            else:
                done.append(f"worktree を撤去した: {wt['path']}")
                print(done[-1])
        print(f"ブランチ {branch} は消していない（squash したブランチは git branch -d が通らない）。")

        if not closing:
            print("閉じるはずの Issue は無い（closingIssuesReferences が空）。")
        for ref in closing:
            def closed(ref=ref) -> bool:
                return gh_json(["issue", "view", ref, "--json", "state"]).get("state") == "CLOSED"

            if wait_for(closed, a.interval, a.settle):
                print(f"Issue が閉じた: {ref}")
            else:
                problems.append(f"Issue が閉じない（{a.settle:g} 秒）: {ref}")
    except Undetermined as e:
        print(f"**判定できなかった**: {e}", file=sys.stderr)
        for d in done:
            print(f"  済んだこと: {d}", file=sys.stderr)
        for pr_ in problems:
            print(f"  済んでいないこと: {pr_}", file=sys.stderr)
        return 7

    if problems:
        print("**マージはした**が、済んでいないことがある:", file=sys.stderr)
        for pr_ in problems:
            print(f"  - {pr_}", file=sys.stderr)
        return 9
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
