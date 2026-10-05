#!/usr/bin/env python3
"""dev-loop の再開の周で worktree／ブランチを作り直した回数を、トランスクリプトから数える。

    python3 scripts/count-resume-recreations.py               # 手元の全リポジトリ
    python3 scripts/count-resume-recreations.py --anonymize   # リポジトリ名を伏せる（共有用）
    python3 scripts/count-resume-recreations.py --since 2026-09-01

**CI からは呼ばない**（`token-metrics.py`・`collect-guard-rejections.py` と同じ扱い）——
入力が `~/.claude/projects` にあり、**リポジトリの外**で、利用者ごとに違うため。
**LLM は使わない。** 標準ライブラリのみ。

なぜ必要か（#184）: #181 の Eval では、**合成した状況で #96 型の失敗が起きなかった**
（#96 修正前の版でも、現在のモデルは worktree を作らなかった）。実際の条件ごと落ちている
可能性があるので、**dev-loop を実際に回したトランスクリプト**に当てて、
**定期的に調べる価値があるかを数字で決める。**

**#96 型**とは、**再開の周で、既にある周の worktree に入らずに新しく作ること**——
周のコミットを 1 つも持たない worktree で実装をやり直し、**止まらないので気づけない。**

## 何を数えるか

- **区間**——dev-loop の起動 1 回から、**同じセッションの次の起動まで**。
  起動は **スラッシュ起動（`<command-name>`）と `Skill` の tool_use の 2 形**を見る
  （**`token-metrics.py` の `slash_command` と同じ規則の写し**。**共有モジュールにしていない**——
  あちらはトークンの会計で、こちらは区間と出力を見る。規則を変えるなら両方）。
- **周**——（リポジトリ, Issue 番号）。リポジトリは起動したレコードの `cwd` から
  `/.claude/worktrees/` より前を取る（**worktree を寄せる**）。
- **再開の区間（母数）**——同じ周の **2 区間目以降**（起動の時刻順）。
- **find-cycle が当てただけの区間**——1 区間目だが、その区間で走らせた `find-cycle.py` が
  **「当たったものがある」と出力した**もの。**母数に混ぜず、別の列に出す。**
    - **#184 の Issue 本文は「`find-cycle.py` を走らせた周」を再開に数えていたが、それは誤り**——
      **1.30.0 以降は新規の周も最初に `find-cycle.py` を走らせる**ので、ほぼ全区間が再開になる
      （実データで、この周自身の起動が「発生」に出た）。**見るのは走らせたことではなく判定の出力。**
    - **判定の出力でも、まだ母数にはできない**——find-cycle は**部分一致**で当てる（自分でもそう警告する）。
      実データで当たった 1 区間目を読むと、**別の Issue の番号を含むコミットに当たっていた新規の周**が混ざっていた。
- **作成の信号**——**出力側（終了状態に近いもの）**で取る:
    - `EnterWorktree` の結果が `Created worktree at` で始まる（`name` 付きでも引数なしでも）。
      **`Entered`・`Resumed` は既存に入っただけなので数えない。**
    - `git worktree add`（`prepare-worktree.sh` を含む）を走らせた `Bash` の出力に
      **行頭の `Preparing worktree (`** がある。
    - `checkout -b` / `switch -c` を走らせた `Bash` の出力に `Switched to a new branch` がある。
  **`Bash` の 2 つはコマンドと出力の両方を見る**——出力だけだと、
  **そのリポジトリのテストが一時リポジトリで作った worktree** や、ログを `cat` しただけの行まで
  数える。**コマンドだけだと、失敗した `git worktree add`（`fatal`）まで数える。**
- **発生**——**再開の区間で作成の信号が 1 つ以上出たもの。**

## 0 件を「起きなかった」と読まないために

**新規の区間（周の 1 区間目）の作成率を併記する。** 新規の周は worktree を作るのが
正常なので、**ここが 0 なら検出器が信号を拾えていない**（形式が変わった・置き場所が違う）。
**新規の区間の作成が 0 件なら、終了コード 3 で終わる**——**新規の区間そのものが 0 の場合も**
（番号なし・再開だけの範囲、狭い `--since`。対照が取れていない）。発生 0 件は、
**母数と、この作成率が併せて出ているときだけ**「起きなかった」と読める。

## 何を守り、何を守らないか

守る:

- **履歴のコピーによる偽の再開**——fork / `--resume` は履歴を別ファイルに写すので、
  **同じ起動が 2 つ現れて 2 区間目（＝再開）に見える。** レコードの `uuid` で畳む。
- **失敗した作成の計上**——`Bash` の信号はコマンドと出力の**両方**を要る（上記）。
- **既存に入った `EnterWorktree` の計上**——`Created worktree at` だけを作成と読む。
- **起動形の取りこぼし**——`Skill` の tool_use も起動として数える。
- **版の取りこぼし**——バナー（`skill-version`）が無ければキャッシュのパスの版を使い、
  **どちらも無ければ「不明」に入れる**（黙って落とさない）。
- **find-cycle を読んだだけの区間の計上**——`python3 …find-cycle.py` で走らせ、
  **行頭の「当たったものがある」**が出たものだけを数える（ソースを `grep` した出力にも同じ文字列が出る）。
- **find-cycle の誤ヒットによる母数の膨張**——当てただけの区間は母数と別の列に出す。
- **別の起動への誤帰属**——作成の信号は、**同じファイルの直前の起動**に帰属させる。
- **0 件の読み違え**——新規の区間の作成が 0 なら非ゼロ終了（上記）。
- **番号なしの区間の新規への混入**——引数なしの起動は周に束ねられないので、
  新規にも再開にも数えず別に出す（引数なしで入り直した再開が、作成率の分母に入らない）。

守らない:

| 守らないもの | なぜ |
| --- | --- |
| **起動せずに会話の続きで次の Issue を回した周** | 区間にならない（`token-metrics.py` の #175 と同じ限界） |
| **サブエージェントの中の作成** | main-chain のファイル（`<project>/<session>.jsonl`）だけを見る |
| **出力を持たない作成**（`git branch <名前>`） | 出力側の信号が無い |
| **再開の定義が正しいか** | 「同じ番号の 2 区間目」は、**閉じた周の後追いの起動も再開に数える**——そこで作り直すのは正常でありうる。**発生は #96 型の候補であって、#96 型の件数ではない** |
| **「うち作成済みの周」が #96 型であること** | 前の区間で作っていても、**マージして畳んだあとの後追い**なら作り直すのが正しい。worktree が**作成時点でまだ在ったか**は見ていない |
| **区間の終わり** | 次の起動までを同じ区間と読む。**dev-loop の外の作業も入る** |

## 出力について

**出すのは集計と識別子（リポジトリ名・Issue 番号・セッション id の先頭・時刻）だけ。**
**コマンド・本文・パスは出さない**——トランスクリプトには他のリポジトリのコード・
Issue 本文が入っており、**このリポジトリは公開**である。
**PR・Issue に貼るなら `--anonymize`**（リポジトリ名を `R1`… に置き換え、発生の一覧から
Issue 番号とセッション id を外す）。

**トランスクリプトの中身は信頼できない入力として扱う**——**何も実行しない。数えるだけ。**
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

SLASH_NAME = re.compile(r"<command-name>\s*/?([^<\s]+)")
SLASH_ARGS = re.compile(r"<command-args>([^<]*)</command-args>")
BANNER = re.compile(r"skill-version:\s*(\d+\.\d+\.\d+)")
CACHE_VERSION = re.compile(r"Base directory for this skill:\s*\S*/dev-loop/(\d+\.\d+\.\d+)/")
PREPARING = re.compile(r"^Preparing worktree \(", re.MULTILINE)
WORKTREE_ADD = re.compile(r"worktree\s+add|prepare-worktree\.sh")
NEW_BRANCH_CMD = re.compile(r"checkout\s+-[bB]\b|switch\s+(-c|--create)\b")
WORKTREE_SEP = "/.claude/worktrees/"
# find-cycle.py を**走らせた**コマンドと、「再開の周」と判定したときの出力（終了コード 1 の行）。
# **どちらも形を要る**——ソースを `grep` / `sed` した出力にも同じ文字列が現れる（#184 の周で実際に誤検出した）。
FIND_CYCLE_RUN = re.compile(r"python3?\s+\S*find-cycle\.py")
FIND_CYCLE_HIT = re.compile(r"^\*\*当たったものがある。", re.MULTILINE)
FIND_CYCLE_MISS = re.compile(r"^\*\*5 本とも当たらなかった", re.MULTILINE)


def is_dev_loop(name: str) -> bool:
    """`dev-loop` と `<plugin>:dev-loop` を起動と読む。`dev-loop-verifier` は読まない。"""
    return name.split(":")[-1] == "dev-loop"


def issue_number(args: str) -> str | None:
    """引数から Issue 番号を取る。URL なら `issues/` の後、それ以外は最初の数字の連なり。

    **URL を先に見る**——`https://github.com/org-2/repo/issues/10902` の最初の数字は `2` である。
    **取れなければ None**（近い周に寄せない。番号なしとして別に数える）。
    """
    found = re.search(r"issues/(\d+)", args or "") or re.search(r"(\d+)", args or "")
    return found.group(1) if found else None


def repo_of(cwd: str | None) -> str:
    if not cwd:
        return "?"
    return cwd.split(WORKTREE_SEP, 1)[0]


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def invocation(base: dict, ident: str, args: str) -> dict:
    return {**base, "id": ident, "issue": issue_number(args), "version": None,
            "find_cycle_in_skill": None, "find_cycle": None}


def scan_file(path: pathlib.Path, stats: collections.Counter):
    """1 ファイルから (起動の一覧, 作成の一覧) を返す。作成は直前の起動の id を持つ。"""
    invocations, creations = [], []
    tools = {}
    current = None
    session = path.stem
    try:
        handle = open(path, encoding="utf-8", errors="replace")
    except OSError:
        stats["unreadable"] += 1
        return invocations, creations
    with handle:
        for line in handle:
            try:
                rec = json.loads(line)
            except ValueError:
                stats["broken"] += 1
                continue
            if not isinstance(rec, dict):
                continue
            msg = rec.get("message") or {}
            content = msg.get("content")
            uuid = rec.get("uuid") or f"{session}:{stats['lines']}"
            stats["lines"] += 1
            base = {"session": session, "ts": rec.get("timestamp") or "", "cwd": rec.get("cwd")}
            blocks = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
            for i, block in enumerate(blocks):
                if not isinstance(block, dict):
                    continue
                kind = block.get("type")
                if msg.get("role") == "user" and kind == "text":
                    text = block.get("text") or ""
                    name = SLASH_NAME.search(text)
                    if name and is_dev_loop(name.group(1)):
                        args = SLASH_ARGS.search(text)
                        current = invocation(base, f"{uuid}#{i}", args.group(1) if args else "")
                        invocations.append(current)
                    elif current is not None and ("skill-version" in text or "Base directory for this skill" in text):
                        version = BANNER.search(text) or CACHE_VERSION.search(text)
                        if version and current["version"] is None:
                            current["version"] = version.group(1)
                        if current["find_cycle_in_skill"] is None:
                            current["find_cycle_in_skill"] = "find-cycle.py" in text
                elif kind == "tool_use":
                    name, inp = block.get("name"), block.get("input") or {}
                    tools[block.get("id")] = (name, inp)
                    if name == "Skill" and is_dev_loop(str(inp.get("skill", ""))):
                        current = invocation(base, f"{uuid}#{i}", str(inp.get("args", "")))
                        invocations.append(current)
                elif kind == "tool_result" and current is not None:
                    name, inp = tools.get(block.get("tool_use_id"), (None, {}))
                    out = text_of(block.get("content"))
                    command = str(inp.get("command", ""))
                    if name == "Bash" and FIND_CYCLE_RUN.search(command):
                        verdict = "hit" if FIND_CYCLE_HIT.search(out) else ("miss" if FIND_CYCLE_MISS.search(out) else "other")
                        if current["find_cycle"] != "hit":
                            current["find_cycle"] = verdict
                    signal = None
                    if name == "EnterWorktree" and out.startswith("Created worktree at"):
                        signal = "EnterWorktree"
                    elif name == "Bash" and WORKTREE_ADD.search(command) and PREPARING.search(out):
                        signal = "worktree add"
                    elif name == "Bash" and NEW_BRANCH_CMD.search(command) and "Switched to a new branch" in out:
                        signal = "new branch"
                    if signal:
                        creations.append({**base, "id": f"{uuid}#{i}", "invocation": current["id"], "signal": signal})
    return invocations, creations


def collect(root: pathlib.Path, since: str | None = None):
    """全ファイルを走査し、区間の一覧と統計を返す。"""
    stats = collections.Counter()
    invocations, creations = {}, {}
    for path in sorted(root.glob("*/*.jsonl")):
        stats["files"] += 1
        invs, crs = scan_file(path, stats)
        for inv in invs:
            if inv["id"] in invocations:
                stats["duplicate_invocations"] += 1
                continue
            invocations[inv["id"]] = inv
        for cr in crs:
            creations.setdefault(cr["id"], cr)
    signals = collections.defaultdict(list)
    for cr in creations.values():
        signals[cr["invocation"]].append(cr["signal"])
    by_cycle = collections.defaultdict(list)
    for inv in invocations.values():
        inv["repo"] = repo_of(inv["cwd"])
        inv["signals"] = signals.get(inv["id"], [])
        if inv["issue"] is not None:
            by_cycle[(inv["repo"], inv["issue"])].append(inv)
    for invs in by_cycle.values():
        invs.sort(key=lambda x: x["ts"])
        created_before = False
        for n, inv in enumerate(invs):
            inv["ordinal"] = n
            inv["created_before"] = created_before
            created_before = created_before or bool(inv["signals"])
    segments = []
    for inv in invocations.values():
        inv.setdefault("ordinal", None)
        inv.setdefault("created_before", False)
        # **2 つの再開を混ぜない。** find-cycle は部分一致で当てる（`#11` が `#110` に当たる）ので、
        # 1 区間目で当たったものには**新規の周が多く混ざる**（#184 の周で実データを読んで確かめた）。
        # 番号なしは周に束ねないので、どちらの再開にもしない（集計と発生の一覧を食い違わせない）。
        inv["resume"] = (None if inv["issue"] is None else "2+" if inv["ordinal"]
                         else "find-cycle" if inv["find_cycle"] == "hit" else None)
        if since and inv["ts"] < since:
            continue
        segments.append(inv)
    segments.sort(key=lambda x: x["ts"])
    return segments, stats


def version_bucket(seg) -> str:
    version = seg["version"] or "不明"
    fc = {True: "find-cycle 有", False: "find-cycle 無", None: "本文なし"}[seg["find_cycle_in_skill"]]
    return f"{version} / {fc}"


def summarize(segments, key):
    rows = collections.defaultdict(lambda: collections.Counter(cycles=set()))
    for seg in segments:
        row = rows[key(seg)]
        row["segments"] += 1
        if seg["issue"] is not None:
            row["cycles"].add((seg["repo"], seg["issue"]))
        if seg["issue"] is None:
            # **番号なしは新規に混ぜない。** 引数なしで入り直した再開でありうるので、
            # 新規の区間の作成率（検出器の対照）と終了コード 3 の判定を濁らせる（#184 の 1 パス目）。
            row["no_issue"] += 1
        elif seg["resume"] == "2+":
            row["resume"] += 1
            row["recreated"] += bool(seg["signals"])
            row["recreated_twice"] += bool(seg["signals"]) and seg["created_before"]
        elif seg["resume"] == "find-cycle":
            row["fc_resume"] += 1
            row["fc_recreated"] += bool(seg["signals"])
        else:
            row["new"] += 1
            row["new_created"] += bool(seg["signals"])
    return rows


def render(segments, stats, anonymize=False) -> tuple[str, int]:
    names = {}
    for seg in segments:
        names.setdefault(seg["repo"], f"R{len(names) + 1}" if anonymize else pathlib.PurePath(seg["repo"]).name)
    lines = [f"走査: {stats['files']} ファイル（読めない {stats['unreadable']}・壊れた行 {stats['broken']}・"
             f"コピーで畳んだ起動 {stats['duplicate_invocations']}）",
             f"区間: {len(segments)}（番号なし {sum(s['issue'] is None for s in segments)}）", ""]
    def table(title, rows, label):
        out = [title, "", f"| {label} | 周 | 区間 | 新規の区間 | うち作成あり | 再開（2 区間目以降） | 発生 | うち作成済みの周 "
               "| find-cycle が当てただけ | 発生 |", "| --- " * 10 + "|"]
        for k in sorted(rows):
            r = rows[k]
            out.append(f"| {k} | {len(r['cycles'])} | {r['segments']} | {r['new']} | {r['new_created']} | "
                       f"{r['resume']} | {r['recreated']} | {r['recreated_twice']} | "
                       f"{r['fc_resume']} | {r['fc_recreated']} |")
        return out

    lines += table("## リポジトリ別", summarize(segments, lambda s: names[s["repo"]]), "リポジトリ")
    lines += [""]
    lines += table("## 版別（バナー／キャッシュのパスの版 / 読み込んだ本文に find-cycle.py があるか）",
                   summarize(segments, version_bucket), "版")
    total = summarize(segments, lambda s: "全体")["全体"]
    lines += ["", "## 判定", ""]
    status = 0
    if not total["new_created"]:
        # 新規の区間が 0 でも対照は取れていない（番号なし・再開だけの範囲。狭い --since）。0 で終わらない。
        lines.append(f"**検出できていない**: 新規の区間が {total['new']} で、作成の信号が 0 件。"
                     "対照が取れないので、発生 0 件を「起きなかった」と読まないこと。")
        status = 3
    else:
        lines.append(f"新規の区間の作成: {total['new_created']} / {total['new']}（検出器が信号を拾えていることの対照）")
        lines.append(f"再開（2 区間目以降）の区間（母数）: {total['resume']}・発生: {total['recreated']}"
                     f"（うち前の区間で既に作っていた周: {total['recreated_twice']}）")
        lines.append(f"find-cycle が当てただけの区間: {total['fc_resume']}・発生: {total['fc_recreated']}"
                     "（**部分一致の誤ヒットを含む**——母数として読まない）")
        lines.append(f"番号なしの区間: {total['no_issue']}（周に束ねられないので、新規にも再開にも数えない）")
    hits = [s for s in segments if s["resume"] and s["signals"]]
    if hits:
        lines += ["", "## 発生の一覧", ""]
        for s in hits:
            ident = "" if anonymize else f" #{s['issue']} {s['session'][:8]}"
            why = "find-cycle が当てた" if not s["ordinal"] else f"{(s['ordinal'] or 0) + 1} 区間目"
            twice = "・既に作成済み" if s["created_before"] else ""
            lines.append(f"- {names[s['repo']]}{ident} {s['ts'][:16]} {why}{twice} 版 {s['version'] or '不明'}: "
                         + ", ".join(sorted(set(s["signals"]))))
    return "\n".join(lines) + "\n", status


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.home() / ".claude" / "projects",
                        help="トランスクリプトの置き場所（既定: ~/.claude/projects）")
    parser.add_argument("--since", help="この時刻（ISO・UTC）以降に起動した区間だけ数える。周の順番は全期間で決める")
    parser.add_argument("--anonymize", action="store_true", help="リポジトリ名を伏せ、発生の一覧から識別子を外す")
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        print(f"置き場所が無い: {args.root}", file=sys.stderr)
        return 2
    segments, stats = collect(args.root, args.since)
    text, status = render(segments, stats, args.anonymize)
    sys.stdout.write(text)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
