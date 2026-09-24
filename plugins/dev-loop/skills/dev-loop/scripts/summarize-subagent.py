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
いるだけなのか**を、親の画面からは区別できない。**transcript をそのまま読むと文脈が溢れる**ので、
集計だけを出す。

## 読み方

- **道具の呼び出し**を時刻・所要つきで並べ、**バックグラウンドに回ったもの**を
  「指定」（入力に `run_in_background`）・「自動」（入力に無いのに回った——**タイムアウトで回る**）・
  「監視」（`Monitor`）に分ける。**コマンドは頭と尾だけ**を出す。**道具の出力は 1 行も出さない。**
- 回った各呼び出しに**完了の記録**（`<task-notification>`）があるかを出す。
- **子の発言**（assistant の text と、`SubagentHandback`・`SendMessage` の引き渡し）を、経過・`stop_reason`・
  文字数・冒頭つきで並べる。**報告を書き終えたかどうかは、並べたものを読んで親が判断する**
  ——`--text <N>` で 1 件だけ全文を出せる。

**どうするか（待つ・再実行する）は、このスクリプトは決めない**——`SKILL.md` 手順 5 を正とする。

## 何を守り、何を守らないか

**1 行に 1 つの主張だけを書く**——テストは 1 行に 1 つの変異を当てるので、2 つ目の主張は無検査になる
（`/code-review` の 1〜3 パス目で、この形の生き残りが毎回見つかった）。

守る:

- **Bash のバックグラウンドは、結果の `toolUseResult.backgroundTaskId` で判定する**——入力の
  `run_in_background` だけを見ると、**タイムアウトで自動的に回ったものを取りこぼす**（#168 の `find /`）。
- **`Monitor` の監視は、結果の `taskId` でバックグラウンドとして数える**——キーが違うので、
  `backgroundTaskId` だけを見ると**監視が 1 本も見えない**（実物で 19 件）。
- **Bash の「自動」は「ID あり・入力に指定なし」で決める**——`timedOutAfterMs` では決めない
  （**印が片方消えたときに黙って「指定」へ落ちる**）。
- **`timedOutAfterMs` があれば、打ち切りの秒数を添える。**
- **完了の記録は、`attachment` と user の発言（SYSTEM NOTIFICATION の形）の両方から拾う**
  ——実物（#168）では **+96:13 の完了が user の発言で届いていた**。
- **道具の結果と assistant の行（道具の入力）からは、完了の記録を拾わない**——子が自分の出力ファイルを
  `cat` すると、通知の文面が写る。
- **task-id と status は、1 つの `<task-notification>` の中でだけ組にする**——隣の通知の status を拾わない。
- **`<status>` の無い通知（`Monitor` の途中経過の `<event>`）は、完了に数えない**——実物で、
  途中経過のあとに `completed` が来る task-id が 12 件ある。
- **発言は `stop_reason` で絞らずに並べる**——実測で、最後の報告の `stop_reason` は `end_turn` とは限らない
  （`None`・`stop_sequence` がある）。逆に `end_turn` の text が「ジョブの完了を待ちます」だけのこともある。
- **`SubagentHandback` の引き渡しを発言として並べる**——報告の本体がそちらで渡され、
  text は定型文だけのことがある（#168 の実物 2 件）。
- **`SendMessage` の引き渡しを発言として並べる**——teammate はこちらで報告を渡す。
- **`SendMessage` の本体は、`message` が空なら `content` から取る**——実物に `message: null` の形がある。
- **引き渡しは、新しい順の窓から外れても全部出す**——報告のあとで子が起こされて短い text を重ねると、
  **報告が窓の外に押し出される**（#168 の実物の形）。
- **いちばん長い text も、窓から外れても出す**——引き渡しの道具を使わずに text で報告した子のために。
- **agent ID で探して 2 件以上当たったら、選ばずに並べて非ゼロで終わる。**
- **名前で探して 2 件以上当たったら、選ばずに並べて非ゼロで終わる**——同名の teammate は別のセッションにもいる。
- **コマンドは頭と尾を出す**——**頭だけに切ると、止めている本体（`… ; find / …`）が隠れる**（#168 の実物 2 件とも）。
- **`--text <N>` は、指定した 1 件だけを出す**——**親の文脈に積まないための道具である。**
- **`--text 0` は非ゼロで終わる**——末尾から数えて黙って返さない。
- **`--text` の負の番号は非ゼロで終わる**——同上。

守らない:

- **「報告を書き終えたか」。** 判定する印が見つからなかった（上の `stop_reason` の行）。並べて親が読む。
- **完了の記録が無いジョブが、いまも走っているか。** 実測で、開始 99 件のうち 29 件に完了の記録が
  無かったが、**その理由は特定していない**。だから**「完了の記録が無い」までしか言わない。**
- **`completed` が「子の仕事が終わった」ことか。** status は**ジョブの**状態である。
- **user の発言に、通知の文面が*引用*されている場合**（親が転送した・委譲文が例に挙げた）。
  **本物の通知と区別しない**——実物では 0 件だった（**起きたら完了と誤って数える**）。
- **`SendMessage` の宛先。** 親以外への `SendMessage` も引き渡しとして並ぶ。
- **ジョブを止められるか。** 止め方も、止めたあとで報告が渡るかも確かめていない。
- **`Agent` など、Bash と `Monitor` 以外の道具が起こしたバックグラウンドの仕事。**
- **どの呼び出しが委譲文の禁止に当たるか。** 印を付けていた版があったが、**`&` の印が実物 64 件中 60 件で
  誤検出**し、推測を足すたびに別の誤検出が見つかったので**外した**（#168 の 3 パス目）。コマンドの頭と尾を読んで親が判断する。
- **ジョブの出力。** `output-file` は一時ディレクトリにあり、セッションと一緒に消える。
- **親の transcript**（main-chain）。サブエージェント 1 体分だけを見る。

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


def describe_input(inp):
    if not isinstance(inp, dict):
        return ""
    for key in ("command", "description", "file_path", "pattern", "message", "prompt"):
        if inp.get(key):
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
    """通知が届く行だけから文面を返す。道具の結果（tool_result）・入力（assistant の行）は見ない。"""
    if r.get("type") == "attachment":
        return json.dumps(r.get("attachment"), ensure_ascii=False)
    if r.get("type") == "user":
        content = (r.get("message") or {}).get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # tool_result のブロックは type が text ではないので、ここで落ちる
            return "".join(str(b.get("text", "")) for b in content
                           if isinstance(b, dict) and b.get("type") == "text")
    return ""


def handback_text(inp):
    """引き渡しの本体。SendMessage は message が空で content に本体を持つことがある。"""
    return str(inp.get("message") or inp.get("content") or "")


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
            if tid and status:
                done.setdefault(tid.group(1).strip(), (status.group(1).strip(), ts))
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
                    says.append({"kind": "引き渡し", "ts": ts, "stop": None, "text": handback_text(inp)})
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in calls:
                c = calls[b["tool_use_id"]]
                c["end"] = ts
                tur = r.get("toolUseResult")
                if isinstance(tur, dict) and tur.get("backgroundTaskId"):
                    c["bg"] = tur["backgroundTaskId"]
                    c["timeout"] = tur.get("timedOutAfterMs")
                elif isinstance(tur, dict) and c["name"] == "Monitor" and tur.get("taskId"):
                    c["bg"] = tur["taskId"]
    return calls, order, done, says, first_ts, last_ts


def bg_kind(c):
    if not c["bg"]:
        return ""
    if c["name"] == "Monitor":
        return "監視"
    inp = c["input"] if isinstance(c["input"], dict) else {}
    return "指定" if inp.get("run_in_background") else "自動"


def pick_says(says):
    """見せる発言の番号: 新しい SHOW_TEXTS 件・引き渡しの全部・最長の text。"""
    picked = set(range(max(1, len(says) - SHOW_TEXTS + 1), len(says) + 1))
    picked |= {i for i, s in enumerate(says, 1) if s["kind"] == "引き渡し"}
    texts = [(len(s["text"]), i) for i, s in enumerate(says, 1) if s["kind"] == "text"]
    if texts:
        picked.add(max(texts)[1])
    return picked


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
    count = {k: sum(bg_kind(c) == k for c in bgs) for k in ("指定", "自動", "監視")}
    out += ["", f"バックグラウンドに回った呼び出し: {len(bgs)} 本"
                f"（指定 {count['指定']} ／ 自動 {count['自動']} ／ 監視 {count['監視']}）"]
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

    shown = pick_says(says)
    out += ["", f"子の発言: {len(says)} 件（新しい {SHOW_TEXTS} 件 ＋ 引き渡し ＋ 最長の text。"
                "全文は --text <番号>）"]
    for i, s in enumerate(says, 1):
        if i not in shown:
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
        if args.text == 0:
            print("番号が範囲外: 0（1 から数える）", file=sys.stderr)
            return 2
        if args.text < 0:
            print(f"番号が範囲外: {args.text}（負の番号は使えない）", file=sys.stderr)
            return 2
        if args.text > len(says):
            print(f"番号が範囲外: {args.text}（発言は {len(says)} 件）", file=sys.stderr)
            return 2
        print(says[args.text - 1]["text"])
        return 0
    print(report(path, rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
