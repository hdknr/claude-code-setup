#!/usr/bin/env python3
"""ローカルのトランスクリプトからトークン使用量を集計する。

**CI からは呼ばない**（`export-diagrams.py` と同じ扱い）——入力が
`~/.claude/projects/` にあり、**リポジトリの外**で、利用者ごとに違うため。
手で実行する:

    python3 scripts/token-metrics.py                 # 週次の推移
    python3 scripts/token-metrics.py --per-cycle     # dev-loop の周ごと
    python3 scripts/token-metrics.py --since 2026-09-01 --repo taihei-epm-server

なぜ必要か（#95）: #92 で「1 周の重さ（ターン数 × 文脈）を減らす」規範を入れたが、
**効果を測る手段がリポジトリに無かった**。#92 の計測は手作業で、**再現手順が散文でしか
残っていない**。受入基準のうち「トークンが実際に減ること」は**未証明**として人間レビューに
回したが、**データが溜まった時点で測れる状態を作っておかないと、未証明が回収されない**。

**#92 の計測値そのものは再計算しない。** あれは
[設計 §8.3](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#session-split)
に凍結した 2026-09-15 時点の実測で、**ここで数え直すと同じ量に 2 つの公式な数ができる**
（#94 で実際にやって直した）。このスクリプトが出すのは**今の値**である。

## 数え方

**加重トークン ＝ `in + cacheW×1.25 + cacheR×0.1 + out×5`。**
#92 が使った換算をそのまま置いている。**請求と突き合わせていない**ので、
**保証されるのは「#92 と同じ式である」ことだけ**で、**それが課金と一致するかは別問題**。

**この式は 2 箇所にある。** 実装はここ（`WEIGHTS`）だけだが、
**設計 §8.3 にも #92 時点の記録として同じ式が載っている**。あちらは
「#92 の数字がどう作られたか」の記録なので消せない——消すと表の意味が読めなくなる。
**比率が変わったら両方直すこと。**「1 箇所だけに置いた」と書きたくなるが、
**実際には 2 箇所あるので、そう書けば嘘になる**（#94 で同じ形を 6 回やった）。

## 落とし穴（どれも実測で確かめた）

| 落とし穴 | どうしているか |
| --- | --- |
| **サブエージェントの取りこぼし** | 使用量は `<project>/<session>/subagents/*.jsonl` に分かれて入る。`*/*.jsonl` だけ見ると落ちる（割合は設計 §8.3 を見ること——**ここに数字を書かない**） |
| **`usage.iterations` の二重計上** | 各要素が**トップレベルと同じ数字を再掲**している。実測 1,698 件すべてで一致し、要素が 2 つ以上のものは 0 件だった。**トップレベルだけ読む** |
| **`<synthetic>` モデル** | 実測で**全件 0 トークン**（62/62）。足しても数は変わらないが**件数の分母が狂う**ので除外する |
| **`grep dev-loop` で周を判定する** | **使えない**——`MEMORY.md` の記載に当たって全件ヒットする。`Skill` の `skill` と `Agent` の `subagent_type` を見る |
| **読めないファイル** | 件数を**報告に出す**。黙って 0 にしない |
| **`--repo` の部分一致が広すぎる** | `--list-repos` で**実際に何にマッチするかを先に見る**。実測で `taihei-epm` は **7 ディレクトリ**に当たった |
| **worktree が別プロジェクトとして記録される** | `<repo>--claude-worktrees-<name>` という別ディレクトリになる。**同じリポジトリの作業なのに別々に数えられる**。寄せたいなら `--merge-worktrees` |

**`usage` の在処を型で絞らない。** 実測では `assistant` にしか無いが、
`message.usage` の有無で拾えば、将来ほかの型に付いても落ちない。

## #92 の数字を再現するものではない

設計 §8.3 の表と**突き合わせたが、一致しなかった**。完全な名前で絞ると
**セッション数と dev-loop 周の数は合う**のに、**加重トークンは合わない**（2026-W37 で
472M 対 637M）。**原因は特定していない**——#92 側がどの範囲で数えたか（`-web` や `-ui` を
含めたか・worktree を含めたか・日付を UTC で切ったか）が**散文にしか残っていない**ためで、
**まさにこのスクリプトが無かったことの帰結**である。

**だから「#92 を再現した」とは書かない。** 言えるのは、**今後は同じ式で before/after が
取れる**ことだけ。§8.3 の表は 2026-09-15 時点の記録として**そのまま置く**。

標準ライブラリのみ。
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import sys

# 加重の式。**実装はここだけ。ただし設計 §8.3 にも #92 時点の記録として同じ式がある**
# （docstring の「数え方」を見ること）。**変えるなら両方。**
WEIGHTS = {
    "input_tokens": 1.0,
    "cache_creation_input_tokens": 1.25,
    "cache_read_input_tokens": 0.1,
    "output_tokens": 5.0,
}

# 実消費ではないモデル。実測で全件 0 トークンだった。
SYNTHETIC_MODELS = {"<synthetic>"}

# `/dev-loop` を回した周の判定に使う印。**名前の部分一致で見る**
# （プラグイン経由だと `dev-loop:dev-loop`、素のスキルだと `dev-loop`）。
DEV_LOOP_SKILL = "dev-loop"
DEV_LOOP_AGENT = "dev-loop-verifier"

AGENT_TOOLS = ("Agent", "Task")

# worktree はプロジェクトディレクトリとして**別扱いで記録される**
# （`<repo>--claude-worktrees-<name>`）。同じリポジトリの作業なのに別々に数えられる。
WORKTREE_MARKER = "--claude-worktrees-"


class Record:
    """1 レコード分の集計値。"""

    __slots__ = ("day", "repo", "session", "is_sub", "model", "weighted", "raw", "cache_read")

    def __init__(self, day, repo, session, is_sub, model, weighted, raw, cache_read):
        self.day = day
        self.repo = repo
        self.session = session
        self.is_sub = is_sub
        self.model = model
        self.weighted = weighted
        self.raw = raw
        self.cache_read = cache_read


def weighted_tokens(usage: dict) -> tuple[float, int, int]:
    """(加重, 生の合計, cache read) を返す。

    **`iterations` は読まない。** 各要素がトップレベルと同じ数字を持っているので、
    足すと二重計上になる。
    """
    weighted = 0.0
    raw = 0
    for key, factor in WEIGHTS.items():
        value = usage.get(key) or 0
        if not isinstance(value, (int, float)):
            continue
        weighted += value * factor
        raw += int(value)
    cache_read = usage.get("cache_read_input_tokens") or 0
    return weighted, raw, int(cache_read) if isinstance(cache_read, (int, float)) else 0


def session_of(path: pathlib.Path, projects_root: pathlib.Path,
                merge_worktrees: bool = False) -> tuple[str, str, bool]:
    """(リポジトリ名, セッション id, サブエージェントか) を返す。

    レイアウトは 2 通り:
      <projects>/<repo>/<session>.jsonl
      <projects>/<repo>/<session>/subagents/<name>.jsonl
    """
    rel = path.relative_to(projects_root)
    parts = rel.parts
    repo = parts[0] if parts else "?"
    if merge_worktrees and WORKTREE_MARKER in repo:
        repo = repo.split(WORKTREE_MARKER, 1)[0]
    is_sub = "subagents" in parts
    if is_sub:
        session = parts[1] if len(parts) > 2 else path.stem
    else:
        session = path.stem
    return repo, session, is_sub


def tool_uses(message: dict):
    """message の content から tool_use ブロックを取り出す。"""
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            yield block


def scan(projects_root: pathlib.Path, merge_worktrees: bool = False):
    """(レコード列, dev-loop を回したセッション, 読めなかったファイル数) を返す。"""
    records: list[Record] = []
    dev_loop_sessions: set[tuple[str, str]] = set()
    unreadable = 0

    for path in sorted(projects_root.rglob("*.jsonl")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            unreadable += 1
            continue
        repo, session, is_sub = session_of(path, projects_root, merge_worktrees)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(row, dict):
                continue
            message = row.get("message")
            if not isinstance(message, dict):
                continue

            for block in tool_uses(message):
                name = block.get("name")
                args = block.get("input")
                if not isinstance(args, dict):
                    continue
                if name == "Skill":
                    skill = args.get("skill") or args.get("command") or ""
                    if isinstance(skill, str) and DEV_LOOP_SKILL in skill:
                        dev_loop_sessions.add((repo, session))
                elif name in AGENT_TOOLS:
                    subagent = args.get("subagent_type") or ""
                    if isinstance(subagent, str) and DEV_LOOP_AGENT in subagent:
                        dev_loop_sessions.add((repo, session))

            usage = message.get("usage")
            if not isinstance(usage, dict):
                continue
            model = message.get("model") or "?"
            if model in SYNTHETIC_MODELS:
                continue
            weighted, raw, cache_read = weighted_tokens(usage)
            day = (row.get("timestamp") or "")[:10]
            records.append(Record(day, repo, session, is_sub, model,
                                  weighted, raw, cache_read))

    return records, dev_loop_sessions, unreadable


def iso_week(day: str) -> str:
    try:
        d = dt.date.fromisoformat(day)
    except ValueError:
        return "?"
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def fmt_m(value: float) -> str:
    return f"{value / 1_000_000:.0f}"


def render_weekly(records, dev_loop_sessions) -> str:
    weeks = collections.defaultdict(lambda: {
        "weighted": 0.0, "sessions": set(), "dev": set(), "requests": 0, "ctx": 0,
    })
    for r in records:
        bucket = weeks[iso_week(r.day)]
        bucket["weighted"] += r.weighted
        bucket["sessions"].add((r.repo, r.session))
        bucket["requests"] += 1
        bucket["ctx"] += r.cache_read
        if (r.repo, r.session) in dev_loop_sessions:
            bucket["dev"].add((r.repo, r.session))

    lines = ["| ISO週 | セッション | うち dev-loop | 加重(M) | dev-loop 比 | 平均文脈 |",
             "|---|---|---|---|---|---|"]
    for week in sorted(weeks):
        b = weeks[week]
        n_sessions = len(b["sessions"])
        n_dev = len(b["dev"])
        dev_weighted = sum(r.weighted for r in records
                           if iso_week(r.day) == week
                           and (r.repo, r.session) in dev_loop_sessions)
        ratio = f"{100 * dev_weighted / b['weighted']:.0f}%" if b["weighted"] else "–"
        ctx = b["ctx"] // b["requests"] if b["requests"] else 0
        lines.append(f"| {week} | {n_sessions} | {n_dev} | {fmt_m(b['weighted'])} "
                     f"| {ratio} | {ctx // 1000}k |")
    return "\n".join(lines)


def render_per_cycle(records, dev_loop_sessions) -> str:
    per = collections.defaultdict(lambda: {"weighted": 0.0, "requests": 0, "ctx": 0, "day": ""})
    for r in records:
        key = (r.repo, r.session)
        if key not in dev_loop_sessions:
            continue
        b = per[key]
        b["weighted"] += r.weighted
        b["requests"] += 1
        b["ctx"] += r.cache_read
        if not b["day"] or (r.day and r.day < b["day"]):
            b["day"] = r.day

    if not per:
        return "dev-loop を回した周は見つかりませんでした。"

    lines = ["| 日 | リポジトリ | req | 加重(M) | 平均文脈 |", "|---|---|---|---|---|"]
    for (repo, _session), b in sorted(per.items(), key=lambda kv: kv[1]["day"]):
        ctx = b["ctx"] // b["requests"] if b["requests"] else 0
        lines.append(f"| {b['day']} | {repo} | {b['requests']} "
                     f"| {fmt_m(b['weighted'])} | {ctx // 1000}k |")

    total_req = sum(b["requests"] for b in per.values())
    total_ctx = sum(b["ctx"] for b in per.values())
    lines.append("")
    lines.append(f"**{len(per)} 周・平均 {total_req // len(per)} req/周・"
                 f"平均文脈 {(total_ctx // total_req) // 1000 if total_req else 0}k**")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--projects", default=None,
                        help="走査するディレクトリ（既定: ~/.claude/projects）")
    parser.add_argument("--since", default=None, help="この日以降だけ（YYYY-MM-DD）")
    parser.add_argument("--repo", default=None, help="この文字列を含むリポジトリだけ")
    parser.add_argument("--per-cycle", action="store_true",
                        help="週次ではなく dev-loop の周ごとに出す")
    parser.add_argument("--merge-worktrees", action="store_true",
                        help="worktree を元のリポジトリに寄せる")
    parser.add_argument("--list-repos", action="store_true",
                        help="--repo が実際に何にマッチするかを見る（集計しない）")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.projects) if args.projects else (
        pathlib.Path(os.path.expanduser("~")) / ".claude" / "projects")
    if not root.is_dir():
        print(f"ERROR: 走査先が見つからない: {root}", file=sys.stderr)
        return 1

    # **絞る前に、何に当たるかを見せる。** 部分一致は広すぎることがあり、
    # 実測で `taihei-epm` は 7 ディレクトリに当たった。**気づかないまま集計すると、
    # 数字が合わない理由が分からなくなる**（#95 の周で実際に踏んだ）。
    if args.list_repos:
        names = sorted({p.name for p in root.iterdir() if p.is_dir()})
        if args.repo:
            names = [n for n in names if args.repo in n]
        for name in names:
            mark = " ← worktree" if WORKTREE_MARKER in name else ""
            print(f"{name}{mark}")
        print(f"\n{len(names)} 件が一致"
              + (f"（`{args.repo}` で絞った）" if args.repo else ""))
        return 0

    records, dev_loop_sessions, unreadable = scan(root, args.merge_worktrees)
    if args.since:
        records = [r for r in records if r.day >= args.since]
    if args.repo:
        records = [r for r in records if args.repo in r.repo]
        dev_loop_sessions = {k for k in dev_loop_sessions if args.repo in k[0]}

    if not records:
        print("該当するレコードがありませんでした。")
        return 0

    sub = sum(1 for r in records if r.is_sub)
    sub_weighted = sum(r.weighted for r in records if r.is_sub)
    total_weighted = sum(r.weighted for r in records)

    print(render_per_cycle(records, dev_loop_sessions) if args.per_cycle
          else render_weekly(records, dev_loop_sessions))
    print()
    print(f"レコード {len(records)} 件（うちサブエージェント {sub} 件＝"
          f"加重の {100 * sub_weighted / total_weighted:.0f}%）。"
          f"加重合計 {fmt_m(total_weighted)}M。")
    # **読めなかったファイルは黙って 0 にしない。**
    if unreadable:
        print(f"⚠ 読めなかったファイル: {unreadable} 件（集計から落ちている）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
