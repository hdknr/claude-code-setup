#!/usr/bin/env python3
r"""サブエージェント 1 体分の transcript を集計し、何に時間を使い、何が残っているかを出す。

    python3 <このスキルの base ディレクトリ>/scripts/summarize-subagent.py <agent ID | agent-*.jsonl のパス>
    python3 ... <agent ID> --projects-dir <dir>    # 探す先を差し替える（既定は ~/.claude/projects）

**置き場所に理由がある。** `dev-loop` は**どのリポジトリでも使えるスキル**なので、
**対象リポジトリの `scripts/` に置かない**（`find-cycle.py` と同じ）。

## なぜ要るか（#168）

親の側には `This agent has not reported yet: it is waiting on its own background work` としか
見えない。**検証がまだ続いているのか、書き終えた報告がバックグラウンドのジョブに止められて
いるだけなのか**を、外から区別できない。前者なら待つ、後者なら**再実行すると同じ検証を
もう一度払う**。**transcript をそのまま読むと文脈が溢れる**ので、集計だけを出す。

## 読み方

- **バックグラウンドに回った呼び出し**を「指定」（入力に `run_in_background`）と
  「自動」（入力に無いのに回った——**Bash の既定のタイムアウトで回る**）に分けて出す。
- 各呼び出しに**完了の記録**（`<task-notification>`）があるかを出す。
- 最後に、**報告を書き終えた記録があるか**を出す。

**どうするか（待つ・止める・再実行する）は、このスクリプトは決めない**——`SKILL.md` 手順 5 を正とする。

## 何を守り、何を守らないか

守る:

- **バックグラウンドの判定は、結果の `toolUseResult.backgroundTaskId` で行う**——入力の
  `run_in_background` だけを見ると、**タイムアウトで自動的に回ったものを取りこぼす**（#168 の `find /`）。
- **「指定」と「自動」を区別する**——入力に `run_in_background` が無いのに ID が付いたものを「自動」と出す。
- **完了の記録を task-id で突き合わせる**——**記録が無いものを「完了」に数えない。**
- **「報告を書き終えた」は、`stop_reason` が `end_turn` の assistant text があるときだけ言う**
  ——**途中の text（道具の前置き）を報告と読まない。** **最後の text でも判定しない**——
  実物（#168）では **+25 分に報告を書き終え**、ジョブの完了通知で子が起こされて
  **+97 分に短い引き渡しの text** を書いていた。最後の text で判定すると、書き終えた時刻が消える。
- **ID から探して 2 件以上当たったら、選ばずに並べて非ゼロで終わる。**
- **コマンドは短く切り、道具の出力は 1 行も出さない**——**親の文脈に積まないための道具である。**

守らない:

- **完了の記録が無いジョブが、いまも走っているか。** 実測で、開始 99 件のうち 29 件に完了の記録が
  無かったが、**その理由は特定していない**。だから**「完了の記録が無い」までしか言わない。**
- **ジョブの出力。** `output-file` は一時ディレクトリにあり、セッションと一緒に消える。
- **親の transcript**（main-chain）。サブエージェント 1 体分だけを見る。

終了コード: **0** 集計した ／ **2** 入力を解決できない（見つからない・2 件以上当たった・読めない）。
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# 1 つの通知の中だけで task-id と status を組にする（隣の通知の status を拾わない）
NOTIFY = re.compile(
    r"<task-id>([^<\\]+)</task-id>(?:(?!</task-notification>).)*?<status>([^<\\]+)</status>", re.S)
CMD_WIDTH = 60


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_offset(start, ts):
    if start is None or ts is None:
        return "+?"
    sec = int((ts - start).total_seconds())
    return f"+{sec // 60}:{sec % 60:02d}"


def fmt_dur(a, b):
    if a is None or b is None:
        return "    ?"
    sec = (b - a).total_seconds()
    return f"{sec:4.0f}s" if sec < 600 else f"{sec / 60:4.0f}m"


def short(s):
    s = " ".join(str(s).split())
    return s if len(s) <= CMD_WIDTH else s[: CMD_WIDTH - 1] + "…"


def describe_input(inp):
    if not isinstance(inp, dict):
        return ""
    for key in ("command", "description", "file_path", "pattern", "prompt"):
        if key in inp:
            return short(inp[key])
    return ""


def resolve(target, projects_dir):
    """ID かパスを 1 つの transcript に解決する。(path, エラー文) を返す。"""
    p = Path(target)
    if p.suffix == ".jsonl":
        return (p, None) if p.is_file() else (None, f"ファイルが無い: {p}")
    agent_id = target[len("agent-"):] if target.startswith("agent-") else target
    hits = sorted(projects_dir.glob(f"*/*/subagents/agent-{agent_id}.jsonl"))
    if not hits:
        return None, f"見つからない: agent-{agent_id}.jsonl（探した先: {projects_dir}）"
    if len(hits) > 1:
        listing = "\n".join(f"  {h}" for h in hits)
        return None, f"2 件以上当たった。選ばない——パスで指定すること:\n{listing}"
    return hits[0], None


def load(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append((json.loads(line), line))
            except json.JSONDecodeError:
                continue
    return rows


def summarize(rows):
    calls = {}              # tool_use id -> dict
    order = []
    done = {}               # task id -> (status, ts)
    finals = []             # end_turn の text: (ts, 文字数)
    last_assistant = None   # (kind, ts)  kind: "text" / "tool_use"
    first_ts = None
    last_ts = None
    for r, raw in rows:
        ts = parse_ts(r.get("timestamp"))
        if ts is not None:
            first_ts = first_ts or ts
            last_ts = ts
        if "task-notification" in raw:
            for m in NOTIFY.finditer(raw):
                done.setdefault(m.group(1), (m.group(2), ts))
        msg = r.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        if r.get("type") == "assistant":
            kinds = [b.get("type") for b in content if isinstance(b, dict)]
            text = "".join(str(b.get("text", "")) for b in content
                           if isinstance(b, dict) and b.get("type") == "text").strip()
            if "tool_use" in kinds:
                last_assistant = ("tool_use", ts)
            elif text:
                last_assistant = ("text", ts)
                if msg.get("stop_reason") == "end_turn":
                    finals.append((ts, len(text)))
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                calls[b.get("id")] = {"name": b.get("name"), "input": b.get("input"),
                                      "start": ts, "end": None, "bg": None, "timeout": None}
                order.append(b.get("id"))
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                c = calls[b["tool_use_id"]]
                c["end"] = ts
                tur = r.get("toolUseResult")
                if isinstance(tur, dict) and tur.get("backgroundTaskId"):
                    c["bg"] = tur["backgroundTaskId"]
                    c["timeout"] = tur.get("timedOutAfterMs")
    return calls, order, done, finals, last_assistant, first_ts, last_ts


def bg_kind(c):
    if not c["bg"]:
        return ""
    inp = c["input"] if isinstance(c["input"], dict) else {}
    return "指定" if inp.get("run_in_background") else "自動"


def report(path, rows):
    calls, order, done, finals, last_assistant, first_ts, last_ts = summarize(rows)
    out = [f"transcript: {path}",
           f"記録 {len(rows)} 行 ／ 道具の呼び出し {len(order)} 回 ／ "
           f"最初 {first_ts.isoformat() if first_ts else '?'} ／ 最後 {fmt_offset(first_ts, last_ts)}",
           "",
           "   経過  所要  道具        BG    内容"]
    for cid in order:
        c = calls[cid]
        out.append(f"{fmt_offset(first_ts, c['start']):>7} {fmt_dur(c['start'], c['end'])}  "
                   f"{str(c['name'])[:10]:<10}  {bg_kind(c):<4}  {describe_input(c['input'])}")

    bgs = [calls[cid] for cid in order if calls[cid]["bg"]]
    out += ["", f"バックグラウンドに回った呼び出し: {len(bgs)} 本"
                f"（指定 {sum(bg_kind(c) == '指定' for c in bgs)} ／ 自動 {sum(bg_kind(c) == '自動' for c in bgs)}）"]
    missing = []
    for c in bgs:
        rec = done.get(c["bg"])
        extra = f"（{c['timeout'] // 1000} 秒で打ち切られて回った）" if isinstance(c["timeout"], int) else ""
        if rec:
            state = f"完了の記録あり（{rec[0]}、{fmt_offset(first_ts, rec[1])}）"
        else:
            state = "**完了の記録なし**"
            missing.append(c)
        out.append(f"  {c['bg']}  {bg_kind(c)}{extra}  {state}  {describe_input(c['input'])}")

    out.append("")
    if finals:
        listing = " ／ ".join(f"{fmt_offset(first_ts, t)}（{n} 文字）" for t, n in finals)
        out.append(f"報告: **書き終えた記録がある**（end_turn の text: {listing}）")
    else:
        last = (f"最後の assistant 記録は {last_assistant[0]}、{fmt_offset(first_ts, last_assistant[1])}"
                if last_assistant else "assistant の記録が無い")
        out.append(f"報告: 書き終えた記録が無い（end_turn の text が無い。{last}）")
    if missing:
        out.append(f"完了の記録が無いバックグラウンドのジョブ: {len(missing)} 本"
                   "——**いまも走っているとは限らない**（記録されない理由を特定していない）")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", help="agent ID（agent- の接頭辞は有っても無くても）か、agent-*.jsonl のパス")
    ap.add_argument("--projects-dir", type=Path, default=Path.home() / ".claude" / "projects")
    args = ap.parse_args(argv)
    path, err = resolve(args.target, args.projects_dir)
    if err:
        print(err, file=sys.stderr)
        return 2
    try:
        rows = load(path)
    except OSError as e:
        print(f"読めない: {path}: {e}", file=sys.stderr)
        return 2
    if not rows:
        print(f"読めない: {path}: JSON の行が 1 つも無い", file=sys.stderr)
        return 2
    print(report(path, rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
