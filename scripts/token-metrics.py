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

**この式は 3 箇所にある。** 数えると:

1. **実装** — このファイルの `WEIGHTS`
2. **この段落** — 読む人のための再掲
3. **設計 §8.3** — #92 時点の記録。「#92 の数字がどう作られたか」なので消せない
   （消すと表の意味が読めなくなる）

ほかに `test-token-metrics.py` の検算コメントにも係数が出るが、あれは
**係数を変えればテストが落ちる**ので、黙って古くなる類ではない。

**比率が変わったら 1〜3 を全部直すこと。**「1 箇所だけに置いた」と書きたくなるが、
**実際には 3 箇所あるので、そう書けば嘘になる**（#94 で同じ形を 6 回やり、
**この docstring でも一度「2 箇所」と数え違えた**——レビューが 3 箇所目を見つけた）。

## 落とし穴（どれも実測で確かめた）

| 落とし穴 | どうしているか |
| --- | --- |
| **サブエージェントの取りこぼし** | 使用量は `<project>/<session>/subagents/*.jsonl` に分かれて入る。`*/*.jsonl` だけ見ると落ちる（割合は設計 §8.3 を見ること——**ここに数字を書かない**） |
| **`usage.iterations` の二重計上** | 各要素が**トップレベルと同じ数字を再掲**している。**足すと倍になる**ので、既定ではトップレベルだけ読む |
| **その逆——`iterations` にしか実数が無い** | **トップレベルが全部 0 のレコードが実在する**（全件走査で 2 件。片方は cache read だけで約 100 万トークン）。**トップレベルだけ読むと丸ごと落ちる**ので、**全部 0 のときに限り `iterations` を見る**（`effective_usage`） |
| **`<synthetic>` モデル** | 実測で**全件 0 トークン**。足しても数は変わらないが**件数の分母が狂う**ので除外する |
| **レコードはあるのに加重が 0** | 上の 0 トークンのレコードだけが絞り込みに残ると起きる。**割り算にガードを置く**（置き忘れて落ちた） |
| **`grep dev-loop` で周を判定する** | **使えない**——`MEMORY.md` の記載に当たって全件ヒットする。`Skill` の `skill` と `Agent` の `subagent_type` を見る |
| **読めないファイル** | 件数を**報告に出す**。黙って 0 にしない |
| **`--repo` の部分一致が広すぎる** | `--list-repos` で**実際に何にマッチするかを先に見る**。実測で `taihei-epm` は **7 ディレクトリ**に当たった |
| **worktree が別プロジェクトとして記録される** | `<repo>--claude-worktrees-<name>` という別ディレクトリになる。**同じリポジトリの作業なのに別々に数えられる**。寄せたいなら `--merge-worktrees` |
| **1 つの会話が複数の「周」に見える** | 周はセッション id で数えるが、**worktree を移ると別セッションになる**。`/dev-loop` を 1 本の会話で複数 Issue に回すと、**`--per-cycle` の行数が実際の周より多く出る**。`--merge-worktrees` はリポジトリ名を寄せるだけで、**セッションは寄せない**（寄せると別々の周まで 1 つになる）。**「1 周あたり req」は上限ではなく下限として読むこと** |

**`usage` の在処を型で絞らない。** 実測では `assistant` にしか無いが、
`message.usage` の有無で拾えば、将来ほかの型に付いても落ちない。

**具体的な件数をここに書かない。** データは増えるので、**書いた瞬間から古くなる**
（#94 で同じ形を繰り返した）。**数えたければ走らせること**——落とし穴の形は変わらないが、
**母数は毎回変わる**。上の表で数字を出しているのは「2 件」だけで、これは
**性質が変わる境目**（0 件なら規則が要らない）なので残してある。

## #92 の数字を再現するものではない

設計 §8.3 の表と**突き合わせたが、一致しなかった**。完全な名前で絞ると
**セッション数（25）と dev-loop 周の数（12）は合う**のに、**加重トークンは合わない**
（2026-W37 で 472M 対 637M）。

**探したうえで特定できていない。** 試したのは、リポジトリ名の絞り方（部分一致／完全な名前）・
`--merge-worktrees` の有無・絞らない全体。**どれも 637M にならなかった**
（worktree を寄せても 472M のまま＝この期間の worktree 分は元々別リポジトリに出ていない）。
**#92 側がどの範囲で数えたのかが散文にしか残っていない**以上、
**こちらから当てにいく手段が無い**——**まさにこのスクリプトが無かったことの帰結**である。

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

# 加重の式。**実装はここだけだが、式そのものは 3 箇所にある**
# （docstring の「数え方」に一覧がある）。**変えるなら全部。**
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


def _sum_iterations(usage: dict) -> dict:
    """`iterations` の各キーを足した辞書を返す（要素が無ければ空）。"""
    its = usage.get("iterations")
    if not isinstance(its, list) or not its:
        return {}
    out = {}
    for key in WEIGHTS:
        total = 0
        for item in its:
            if not isinstance(item, dict):
                continue
            value = item.get(key) or 0
            if isinstance(value, (int, float)):
                total += value
        out[key] = total
    return out


def effective_usage(usage: dict) -> dict:
    """実際に消費された数字を返す。

    **既定はトップレベル。`iterations` は足さない**——各要素がトップレベルと同じ数字を
    再掲しているので、足すと二重計上になる（実測 151,922 件中 151,920 件がこの形）。

    **ただし「トップレベルが全部 0 で `iterations` には実数がある」レコードが実在する。**
    実測で 2 件（2026-08-17）あり、片方は cache read だけで 996,796 トークンあった。
    **トップレベルだけ読むと、これを丸ごと取りこぼす**——#95 のレビューが見つけた。
    **二重計上を避ける規則が、逆向きに取りこぼしを作っていた**ことになる。

    だから**トップレベルが全部 0 のときに限り `iterations` を見る**。
    どちらか一方しか使わないので、**二重計上にはならない**。
    """
    top = {}
    for key in WEIGHTS:
        value = usage.get(key) or 0
        top[key] = value if isinstance(value, (int, float)) else 0
    if any(top.values()):
        return top
    return _sum_iterations(usage) or top


def weighted_tokens(usage: dict) -> tuple[float, int, int]:
    """(加重, 生の合計, cache read) を返す。"""
    effective = effective_usage(usage)
    weighted = 0.0
    raw = 0
    for key, factor in WEIGHTS.items():
        value = effective.get(key) or 0
        weighted += value * factor
        raw += int(value)
    return weighted, raw, int(effective.get("cache_read_input_tokens") or 0)


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
    # **割り算にガードを置く。** レコードはあるのに加重が 0 のことがある——
    # 実測で、トップレベルの usage が全部 0 のレコードが実在した。絞り込みの結果
    # それだけが残ると、ガードが無ければ ZeroDivisionError で落ちる（#95 のレビューが
    # 実データで再現させた）。`render_*` の割り算は守ってあったのに、ここだけ抜けていた。
    sub_ratio = f"{100 * sub_weighted / total_weighted:.0f}%" if total_weighted else "–"
    print(f"レコード {len(records)} 件（うちサブエージェント {sub} 件＝"
          f"加重の {sub_ratio}）。加重合計 {fmt_m(total_weighted)}M。")
    # **読めなかったファイルは黙って 0 にしない。**
    if unreadable:
        print(f"⚠ 読めなかったファイル: {unreadable} 件（集計から落ちている）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
