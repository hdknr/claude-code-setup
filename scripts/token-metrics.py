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

**このスクリプトが出すのは今の値**で、
[設計 §8.3](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#session-split)
の表を書き換えるものではない（あちらは 2026-09-15 時点の記録）。
**ただし、突き合わせた結果あちらの誤りが分かった**——下の「§8.3 の表は…」を見ること。

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
| **1 応答が複数行に書かれる** | 各行が**同じ `message.id` と同じ `usage`** を再掲する。**行ごとに足すと 7 割ほど膨らむ**（率は設計 §8.3 の訂正を見ること）。`message.id` ごとに畳んで**最大を採る**（`output_tokens` が育っていく形があるため） |
| **同じ応答が複数ファイルに入る** | セッションを fork / resume すると**履歴がコピーされる**。`message.id` は API が採番するので**ファイルを跨いでも同一の応答**である。ファイル単位で畳むと数 % 過大になるので、**走査全体で畳む**。帰属は**先に出会ったほう**（コピーされた側が消費したわけではない） |
| **サブエージェントの取りこぼし** | 使用量は `<project>/<session>/subagents/*.jsonl` に分かれて入る。`*/*.jsonl` だけ見ると落ちる（割合は設計 §8.3 を見ること——**ここに数字を書かない**） |
| **`usage.iterations` の二重計上** | 各要素が**トップレベルと同じ数字を再掲**している。**足すと倍になる**ので、既定ではトップレベルだけ読む |
| **その逆——`iterations` にしか実数が無い** | **トップレベルが 0 のレコードが実在する**（全件走査で 2 件。**同じリクエストの重複**で、cache read だけで約 100 万トークン）。**トップレベルだけ読むと丸ごと落ちる**ので、**キーごとに大きいほうを採る**（`effective_usage`） |
| **`<synthetic>` モデル** | 実測で**全件 0 トークン**。足しても数は変わらないが**件数の分母が狂う**ので除外する |
| **レコードはあるのに加重が 0** | 上の 0 トークンのレコードだけが絞り込みに残ると起きる。**割り算にガードを置く**（置き忘れて落ちた） |
| **`grep dev-loop` で周を判定する** | **使えない**——`MEMORY.md` の記載に当たって全件ヒットする。`Skill` の `skill` と `Agent` の `subagent_type` を見る |
| **読めないファイル・壊れた行** | どちらも件数を**報告に出す**。黙って 0 にしない——実データに壊れた行が実在し、**そのうち何行かは `"usage"` を含んでいた** |
| **`--repo` の部分一致が広すぎる** | `--list-repos` で**実際に何にマッチするかを先に見る**（実測で、短い名前が 7 件に当たったことがある。**数は増えるのでここに書かない**）。**値が `-` で始まるなら `--repo=...` と書く**（そうしないと argparse が引数として解釈する） |
| **worktree が別プロジェクトとして記録される** | `<repo>--claude-worktrees-<name>` という別ディレクトリになる。**同じリポジトリの作業なのに別々に数えられる**。寄せたいなら `--merge-worktrees` |
| **日と週の境目が UTC** | タイムスタンプは全件 `…Z`。`--since` と ISO 週の境界は **UTC で切られる**ので、JST の朝 9 時前の作業は**前日**に入る。週単位の before/after を見るときに効く |
| **1 つの会話が複数の「周」に見える** | 周はセッション id で数えるが、**worktree を移ると別セッションになる**。`/dev-loop` を 1 本の会話で複数 Issue に回すと、**`--per-cycle` の行数が実際の周より多く出る**。`--merge-worktrees` はリポジトリ名を寄せるだけで、**セッションは寄せない**（寄せると別々の周まで 1 つになる）。**「1 周あたり req」は上限ではなく下限として読むこと** |

**`usage` の在処を型で絞らない。** 実測では `assistant` にしか無いが、
`message.usage` の有無で拾えば、将来ほかの型に付いても落ちない。

**具体的な件数をここに書かない。** データは増えるので、**書いた瞬間から古くなる**
（#94 で同じ形を繰り返した）。**数えたければ走らせること**——落とし穴の形は変わらないが、
**母数は毎回変わる**。上の表で数字を出しているのは「2 件」だけで、これは
**性質が変わる境目**（0 件なら規則が要らない）なので残してある。

## 設計 §8.3 の表は過大である

**このスクリプトを作る過程で、#92 の数字の誤りが分かった。**
**どの数字がどれだけ影響を受けるかは
[§8.3 の訂正](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/#miscounted-rows)
を正とする**（ここに再掲しない）。

**対照を取って確かめた。** 同じ母集団に対して**畳むかどうかだけを変えて**比べると、
**畳まない側が §8.3 の表とほぼ一致する**。つまり **#92 の集計も 1 応答を複数行として
数えていた**。期間・リポジトリの絞り方・式の違いでは、**セッション数が一致したまま
行数に比例する量だけがずれる**という形を説明できない。

**§8.3 の表は書き換えない**（2026-09-15 時点の記録なので）。訂正はあちらに置く。

**言えることと言えないことを分ける。** 「1 周が重い」という #92 の結論は**比率の話**で、
比率はほとんど動かないのでそのまま成り立つ。誤っていたのは**絶対値のほう**である。

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

    __slots__ = ("day", "repo", "session", "is_sub", "model", "weighted", "cache_read")

    def __init__(self, day, repo, session, is_sub, model, weighted, cache_read):
        self.day = day
        self.repo = repo
        self.session = session
        self.is_sub = is_sub
        self.model = model
        self.weighted = weighted
        self.cache_read = cache_read


def _from_iterations(usage: dict) -> dict:
    """`iterations` から 1 件分の数字を取り出す（要素が無ければ空）。

    **足さない。** `iterations` の各要素は**同じ応答のスナップショット**で、
    トップレベルと同じ数字を再掲している。足すと倍になる——
    実測では要素が 2 つ以上のものは 0 件だが、**形として再掲だと分かっているものを
    足す実装にしておくと、要素が増えた瞬間に静かに倍になる**（#95 のレビュー）。
    だから**キーごとに最大を採る**（育っていく形なら最後が最大になる）。
    """
    its = usage.get("iterations")
    if not isinstance(its, list) or not its:
        return {}
    out = {}
    for key in WEIGHTS:
        best = 0
        for item in its:
            if not isinstance(item, dict):
                continue
            value = item.get(key) or 0
            if isinstance(value, (int, float)) and value > best:
                best = value
        out[key] = best
    return out


def effective_usage(usage: dict) -> dict:
    """実際に消費された数字を返す。

    **既定はトップレベル。`iterations` は足さない**——各要素がトップレベルと同じ数字を
    再掲しているので、足すと二重計上になる。

    **ただし「トップレベルが 0 で `iterations` には実数がある」レコードが実在する。**
    実測で 2 件（2026-08-17）あり、cache read だけで約 100 万トークンあった
    （**2 件は同じリクエストの重複**で、別々の消費ではない）。
    **トップレベルだけ読むと丸ごと取りこぼす**——#95 のレビューが見つけた。
    **二重計上を避ける規則が、逆向きに取りこぼしを作っていた**ことになる。

    **キーごとに大きいほうを採る。** 最初は「トップレベルが*全部* 0 のときだけ
    `iterations` を見る」にしていたが、**1 フィールドでも実数があると残りを落とした**
    （`output` だけ埋まっていて `cache_read` が `iterations` にしか無い形）。
    現データに該当は無いが、**「全部 0」という条件は形の保証ではない**。
    """
    top = {}
    for key in WEIGHTS:
        value = usage.get(key) or 0
        top[key] = value if isinstance(value, (int, float)) else 0
    nested = _from_iterations(usage)
    if not nested:
        return top
    return {key: max(top.get(key, 0), nested.get(key, 0)) for key in WEIGHTS}


def weighted_tokens(usage: dict) -> tuple[float, int]:
    """(加重, cache read) を返す。"""
    effective = effective_usage(usage)
    weighted = 0.0
    for key, factor in WEIGHTS.items():
        weighted += (effective.get(key) or 0) * factor
    return weighted, int(effective.get("cache_read_input_tokens") or 0)


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
    """(レコード列, dev-loop を回したセッション, 読めなかったファイル数, 壊れた行数) を返す。

    **1 応答が複数行に書かれ、各行が同じ `usage` を再掲する。**
    `message.id` が同じ行を 1 リクエストとして畳まないと、**加重が 7 割ほど膨らむ**
    （率は設計 §8.3 の訂正を見ること）。**#95 のレビューが見つけた**——
    実装の初版は行ごとに足しており、**出した数字がすべて過大だった**。

    畳むときは**最大を採る**。再掲は同じ値のこともあるが、**`output_tokens` が
    `1 → 1 → 207` のように育っていく形**もある。
    最後の行が最大になるので、最大を採れば最終状態を拾える。
    （実測では「最後 ≠ 最大」は 0 件なので、どちらでも同じ値になる。
    **最大のほうが安全側**なので最大にしてある。）
    """
    records: list[Record] = []
    dev_loop_sessions: set[tuple[str, str]] = set()
    unreadable = 0
    broken_lines = 0
    # **`message.id` は API が採番するので、ファイルを跨いでも同一の応答を指す。**
    # セッションを fork / resume すると履歴がコピーされ、**同じ応答が別ファイルにも入る**
    # （実測で 2,175 件。モデルが食い違うものは 0 件）。ファイル単位で畳むと
    # **加重が 2.8% 過大**になる——#95 の 2 パス目のレビューが見つけた。
    # 帰属は**最初に出会ったファイル**（`sorted` で走るので決定的）。コピーされた側が
    # 消費したわけではないので、そちらには数えない。
    by_id: dict[str, Record] = {}

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
                # **黙って落とさない。** 実データに壊れた行が実在する
                # （文字化けしたファイルも `errors="replace"` でここに来る）。
                broken_lines += 1
                continue
            if not isinstance(row, dict):
                broken_lines += 1
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
            weighted, cache_read = weighted_tokens(usage)
            day = (row.get("timestamp") or "")[:10]
            record = Record(day, repo, session, is_sub, model, weighted, cache_read)
            message_id = message.get("id")
            if not isinstance(message_id, str) or not message_id:
                # id が無ければ畳めない。**そのまま数える**（落とすより過大のほうがまし）。
                records.append(record)
                continue
            previous = by_id.get(message_id)
            if previous is None or record.weighted > previous.weighted:
                by_id[message_id] = record

    records.extend(by_id.values())
    return records, dev_loop_sessions, unreadable, broken_lines


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


def render_split(records, dev_loop_sessions) -> str:
    """dev-loop を回した周とそれ以外に分ける（設計 §8.3 の表と同じ形）。

    **この形で出すのは、before/after を同じ切り口で比べるため**である。
    §8.3 の表は 2026-09-15 時点の記録なので、**同じ範囲・同じ式で取り直して初めて
    比較になる**。
    """
    groups = {"dev-loop を回した周": [], "それ以外": []}
    for r in records:
        key = ("dev-loop を回した周" if (r.repo, r.session) in dev_loop_sessions
               else "それ以外")
        groups[key].append(r)

    lines = ["| 区分 | セッション | 加重(M) | 比率 | リクエスト/セッション |",
             "|---|---|---|---|---|"]
    total = sum(r.weighted for r in records) or 1
    for name, rows in groups.items():
        sessions = {(r.repo, r.session) for r in rows}
        weighted = sum(r.weighted for r in rows)
        per_session = len(rows) // len(sessions) if sessions else 0
        lines.append(f"| {name} | {len(sessions)} | {fmt_m(weighted)} "
                     f"| {100 * weighted / total:.0f}% | {per_session} |")
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
    parser.add_argument("--split", action="store_true",
                        help="dev-loop を回した周とそれ以外に分けて出す（設計 §8.3 と同じ形）")
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
    # 実測で、短い名前が 7 件に当たったことがある。**気づかないまま集計すると、
    # 数字が合わない理由が分からなくなる**（#95 の周で実際に踏んだ）。
    if args.list_repos:
        names = sorted({p.name for p in root.iterdir() if p.is_dir()})
        if args.merge_worktrees:
            # **集計と同じ粒度で見せる。** 見せる粒度が集計と違うと、
            # 「絞る前に何に当たるか見る」ための機能が用を成さない（#95 のレビュー）。
            names = sorted({n.split(WORKTREE_MARKER, 1)[0] for n in names})
        if args.repo:
            names = [n for n in names if args.repo in n]
        for name in names:
            mark = " ← worktree" if WORKTREE_MARKER in name else ""
            print(f"{name}{mark}")
        print(f"\n{len(names)} 件が一致"
              + (f"（`{args.repo}` で絞った）" if args.repo else ""))
        return 0

    records, dev_loop_sessions, unreadable, broken = scan(root, args.merge_worktrees)
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

    if args.split:
        print(render_split(records, dev_loop_sessions))
    elif args.per_cycle:
        print(render_per_cycle(records, dev_loop_sessions))
    else:
        print(render_weekly(records, dev_loop_sessions))
    print()
    # **割り算にガードを置く。** レコードはあるのに加重が 0 のことがある——
    # 実測で、トップレベルの usage が全部 0 のレコードが実在した。絞り込みの結果
    # それだけが残ると、ガードが無ければ ZeroDivisionError で落ちる（#95 のレビューが
    # 実データで再現させた）。`render_*` の割り算は守ってあったのに、ここだけ抜けていた。
    sub_ratio = f"{100 * sub_weighted / total_weighted:.0f}%" if total_weighted else "–"
    print(f"レコード {len(records)} 件（うちサブエージェント {sub} 件＝"
          f"加重の {sub_ratio}）。加重合計 {fmt_m(total_weighted)}M。")
    # **読めなかったものは黙って 0 にしない。** ファイルだけでなく**行**も数える
    # ——実データに壊れた行が実在し、そのうち何行かは `"usage"` を含んでいた（#95）。
    if unreadable:
        print(f"⚠ 読めなかったファイル: {unreadable} 件（集計から落ちている）")
    if broken:
        print(f"⚠ JSON として読めなかった行: {broken} 行（集計から落ちている）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
