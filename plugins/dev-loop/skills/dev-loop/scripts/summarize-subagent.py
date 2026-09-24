#!/usr/bin/env python3
r"""サブエージェント 1 体分の transcript を集計し、何に時間を使い、何が残っているかを出す。

    python3 <このスキルの base ディレクトリ>/scripts/summarize-subagent.py <agent ID | 名前[@チーム] | agent-*.jsonl のパス>
    python3 ... <同上> --text <N>              # 並べた発言のうち N 番だけを全文で出す
    python3 ... <同上> --projects-dir <dir>    # 探す先を差し替える（既定は ~/.claude/projects）

**置き場所に理由がある。** `dev-loop` は**どのリポジトリでも使えるスキル**なので、
**対象リポジトリの `scripts/` に置かない**（`find-cycle.py` と同じ）。

## なぜ要るか（#168）

親の側には `This agent has not reported yet: it is waiting on its own background work` としか
見えない。**検証がまだ続いているのか、書き終えた報告がバックグラウンドのジョブに止められて
いるだけなのか**を、外から区別できない。前者なら待つ、後者なら**再実行すると同じ検証を
もう一度払う**。**transcript をそのまま読むと文脈が溢れる**ので、集計だけを出す。

## 読み方

- **道具の呼び出し**を時刻・所要つきで並べ、**バックグラウンドに回ったもの**を
  「指定」（入力に `run_in_background`）と「自動」（入力に無いのに回った——**タイムアウトで回る**）に分ける。
  **コマンドは頭と尾だけ**を出し、**委譲文が禁じている形**（`find /` など）には印を付ける。
- 回った各呼び出しに**完了の記録**（`<task-notification>`）があるかを出す。
- **子の発言**（assistant の text と、`SubagentHandback`・`SendMessage` の引き渡し）を、経過・`stop_reason`・
  文字数・冒頭つきで並べる。**報告を書き終えたかどうかは、並べたものを読んで親が判断する**
  ——`--text <N>` で 1 件だけ全文を出せる。

**どうするか（待つ・再実行する）は、このスクリプトは決めない**——`SKILL.md` 手順 5 を正とする。

## 何を守り、何を守らないか

守る:

- **バックグラウンドの判定は、結果の `toolUseResult.backgroundTaskId` で行う**——入力の
  `run_in_background` だけを見ると、**タイムアウトで自動的に回ったものを取りこぼす**（#168 の `find /`）。
- **「自動」は「ID あり・入力に指定なし」で決める**——`timedOutAfterMs` は表示に留め、判定には使わない
  （**印が片方消えたときに黙って「指定」へ落ちる**）。
- **完了の記録は、通知の行（`attachment` と、道具の結果を含まない user の発言）からだけ拾う**
  ——**道具の結果や入力に通知の文面が写っていても、完了とは数えない**（子が自分の出力ファイルを
  `cat` すると写る）。
- **task-id と status は、1 つの `<task-notification>` の中でだけ組にする**——隣の通知の status を拾わない。
- **「報告を書き終えたか」を判定しない。発言は `stop_reason` で絞らずに並べる**——実測で、
  最後の報告の `stop_reason` は `end_turn` とは限らず（`None`・`stop_sequence` がある）、
  逆に `end_turn` の text が「ジョブの完了を待ちます」だけのこともあり、
  報告の本体が `SubagentHandback`・`SendMessage` で渡されて text は定型文だけのこともある。
- **ID・名前から探して 2 件以上当たったら、選ばずに並べて非ゼロで終わる。**
- **道具の出力は 1 行も出さず、コマンドは頭と尾だけ出す。禁じられた形には印を付ける**
  ——**頭だけに切ると、止めている本体（`… ; find / …`）が隠れる**（#168 の実物 2 件とも）。
- **`--text <N>` は、指定した 1 件だけを出す**——**親の文脈に積まないための道具である。**

守らない:

- **完了の記録が無いジョブが、いまも走っているか。** 実測で、開始 99 件のうち 29 件に完了の記録が
  無かったが、**その理由は特定していない**。だから**「完了の記録が無い」までしか言わない。**
- **ジョブを止められるか。** 止め方も、止めたあとで報告が渡るかも確かめていない。
- **ジョブの出力。** `output-file` は一時ディレクトリにあり、セッションと一緒に消える。
- **親の transcript**（main-chain）。サブエージェント 1 体分だけを見る。
- **印の網羅。** 印を付けるのは下の `FLAGS` にある形だけで、禁じられた操作の全部ではない。

終了コード: **0** 集計した ／ **2** 入力を解決できない（見つからない・2 件以上当たった・読めない・
`--text` の番号が範囲外）。
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

NOTIFICATION = re.compile(r"<task-notification>(.*?)</task-notification>", re.S)
TASK_ID = re.compile(r"<task-id>([^<]+)</task-id>")
STATUS = re.compile(r"<status>([^<]+)</status>")
# 委譲文（prompts/verifier.md）が禁じている形のうち、コマンドの文字列から見えるもの
FLAGS = [
    ("find /", re.compile(r"\bfind\s+/(\s|$)")),
    ("find ~", re.compile(r"\bfind\s+(~|\$HOME)")),
    ("&", re.compile(r"(?<![&|>0-9])&(?![&>])")),
    ("nohup", re.compile(r"\bnohup\b")),
    ("docker", re.compile(r"\bdocker\s+(run|compose|start)\b")),
]
# 報告を親に渡す道具（実測: 非同期の子は SubagentHandback、teammate は SendMessage）
HANDBACK = ("SubagentHandback", "SendMessage")
HEAD, TAIL = 40, 25
PREVIEW = 50
SHOW_TEXTS = 6


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


def one_line(s):
    return " ".join(str(s).split())


def short(s):
    s = one_line(s)
    return s if len(s) <= HEAD + TAIL + 3 else f"{s[:HEAD]} … {s[-TAIL:]}"


def flags(command):
    return [name for name, pat in FLAGS if pat.search(str(command))]


def describe_input(inp):
    if not isinstance(inp, dict):
        return ""
    if "command" in inp:
        marks = "".join(f"[{f}]" for f in flags(inp["command"]))
        return (marks + " " if marks else "") + short(inp["command"])
    for key in ("description", "file_path", "pattern", "message", "prompt"):
        if key in inp:
            return short(inp[key])
    return ""


def resolve(target, projects_dir):
    """ID・名前・パスを 1 つの transcript に解決する。(path, エラー文) を返す。"""
    p = Path(target)
    if p.suffix == ".jsonl":
        return (p, None) if p.is_file() else (None, f"ファイルが無い: {p}")
    name, _, team = target.partition("@")
    agent_id = name[len("agent-"):] if name.startswith("agent-") else name
    hits = sorted(projects_dir.glob(f"*/*/subagents/agent-{agent_id}.jsonl"))
    if not hits:
        for meta in sorted(projects_dir.glob("*/*/subagents/agent-*.meta.json")):
            try:
                m = json.loads(meta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if m.get("name") == name and (not team or m.get("teamName") == team):
                jsonl = meta.with_name(meta.name[: -len(".meta.json")] + ".jsonl")
                if jsonl.is_file():
                    hits.append(jsonl)
    if not hits:
        return None, f"見つからない: {target}（探した先: {projects_dir}）"
    if len(hits) > 1:
        listing = "\n".join(f"  {h}" for h in hits)
        return None, f"2 件以上当たった。選ばない——パスか「名前@チーム」で指定すること:\n{listing}"
    return hits[0], None


def load(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def notification_text(r):
    """通知が届く行だけから文面を返す。道具の結果・入力は見ない。"""
    if r.get("type") == "attachment":
        return json.dumps(r.get("attachment"), ensure_ascii=False)
    if r.get("type") == "user":
        content = (r.get("message") or {}).get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list) and not any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return "".join(str(b.get("text", "")) for b in content if isinstance(b, dict))
    return ""


def summarize(rows):
    calls = {}          # tool_use id -> dict
    order = []
    done = {}           # task id -> (status, ts)
    says = []           # 子の発言: {"kind", "ts", "stop", "text"}
    first_ts = last_ts = None
    for r in rows:
        ts = parse_ts(r.get("timestamp"))
        if ts is not None:
            first_ts = first_ts or ts
            last_ts = ts
        for block in NOTIFICATION.findall(notification_text(r)):
            tid, status = TASK_ID.search(block), STATUS.search(block)
            if tid:
                done.setdefault(tid.group(1).strip(), (status.group(1).strip() if status else "?", ts))
        msg = r.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        if r.get("type") == "assistant":
            text = "".join(str(b.get("text", "")) for b in content
                           if isinstance(b, dict) and b.get("type") == "text").strip()
            if text:
                says.append({"kind": "text", "ts": ts, "stop": msg.get("stop_reason"), "text": text})
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                inp = b.get("input")
                calls[b.get("id")] = {"name": b.get("name"), "input": inp,
                                      "start": ts, "end": None, "bg": None, "timeout": None}
                order.append(b.get("id"))
                if b.get("name") in HANDBACK and isinstance(inp, dict):
                    says.append({"kind": "引き渡し", "ts": ts, "stop": None,
                                 "text": str(inp.get("message", ""))})
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                c = calls[b["tool_use_id"]]
                c["end"] = ts
                tur = r.get("toolUseResult")
                if isinstance(tur, dict) and tur.get("backgroundTaskId"):
                    c["bg"] = tur["backgroundTaskId"]
                    c["timeout"] = tur.get("timedOutAfterMs")
    return calls, order, done, says, first_ts, last_ts


def bg_kind(c):
    if not c["bg"]:
        return ""
    inp = c["input"] if isinstance(c["input"], dict) else {}
    return "指定" if inp.get("run_in_background") else "自動"


def report(path, rows):
    calls, order, done, says, first_ts, last_ts = summarize(rows)
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
    missing = 0
    for c in bgs:
        rec = done.get(c["bg"])
        extra = f"（{c['timeout'] // 1000} 秒で回った）" if isinstance(c["timeout"], int) else ""
        if rec:
            state = f"完了の記録あり（{rec[0]}、{fmt_offset(first_ts, rec[1])}）"
        else:
            state = "**完了の記録なし**"
            missing += 1
        out.append(f"  {c['bg']}  {bg_kind(c)}{extra}  {state}  {describe_input(c['input'])}")
    if missing:
        out.append(f"  → 完了の記録が無いもの {missing} 本——**いまも走っているとは限らない**"
                   "（記録されない理由を特定していない）")

    shown = says[-SHOW_TEXTS:]
    out += ["", f"子の発言: {len(says)} 件（新しい {len(shown)} 件。全文は --text <番号>）"]
    for i, s in enumerate(says, 1):
        if s not in shown:
            continue
        stop = f"stop={s['stop']}" if s["kind"] == "text" else ""
        preview = one_line(s["text"])[:PREVIEW]
        out.append(f"  {i:>3}. {fmt_offset(first_ts, s['ts']):>7}  {s['kind']:<4} {stop:<16} "
                   f"{len(s['text']):>6} 文字  {preview}")
    if not says:
        out.append("  （無い）")
    out.append("**報告を書き終えたかは判定しない**——文字数と冒頭を見て、要るものだけ --text で読む。")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target", help="agent ID・名前[@チーム]・agent-*.jsonl のパスのどれか")
    ap.add_argument("--text", type=int, metavar="N", help="子の発言の N 番だけを全文で出す")
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
    if args.text is not None:
        says = summarize(rows)[3]
        if not 1 <= args.text <= len(says):
            print(f"番号が範囲外: {args.text}（発言は {len(says)} 件）", file=sys.stderr)
            return 2
        print(says[args.text - 1]["text"])
        return 0
    print(report(path, rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
