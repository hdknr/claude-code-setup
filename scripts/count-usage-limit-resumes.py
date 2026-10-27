#!/usr/bin/env python3
"""利用上限で止まったあと、何で続いたかをトランスクリプトから数える。

    python3 scripts/count-usage-limit-resumes.py               # 手元の全リポジトリ
    python3 scripts/count-usage-limit-resumes.py --anonymize   # リポジトリ名を伏せる（共有用）
    python3 scripts/count-usage-limit-resumes.py --since 2026-10-01 --tz Asia/Tokyo

**CI からは呼ばない**（`count-resume-recreations.py` と同じ扱い）——入力が `~/.claude/projects` にあり、
**リポジトリの外**で、利用者ごとに違うため。**LLM は使わない。** 標準ライブラリのみ。

なぜ必要か（#454）: `check-unattended-env.py` は `autoContinueAtUsageLimit` が**入っているか**しか見ない。
**上限のあとに実際に続いたか**は、どこでも測っていなかった。不在の cruise が上限で止まったまま
戻らないなら、タイマーを保険に張る必要がある——**それを決める材料を数字で出す。**

## 何を数えるか

- **停止**——上限で止まったことの記録。**2 つの形を見る**:
    - `error == "rate_limit"` の `assistant` のレコード（`quotaLimits.resetsAt` に予告の時刻、
      `quotaLimits.rateLimitType` に上限の種類を持つ）
    - `system`／`informational` の予告 `Usage limit reached …`（`continuing automatically at <時刻>` を持てば
      **自動継続の待ちを張った**記録）
  **`rate_limit` のレコードを持たず予告だけの停止がある**（#454 の周で実データに 1 件。
  前者だけを数えると、その停止のあとの自動継続が丸ごと落ちる）。
- **待ち**——停止を畳んだもの。**同じファイルの中で、次の 2 つは 1 つの待ちに畳む**:
    - 続けて並んだ停止の記録（間に入力も応答も来ていない。`rate_limit` のレコードと予告は同時に出る）
    - **予告の時刻が同じ停止**（2 分の幅）——待ちの間に通知が来て応答し、また上限に当たる形が多い
- **窓**——待ちの最初の停止から、**同じファイルの、予告の時刻が違う次の停止まで**（無ければ記録の終わりまで）。
  **ただし予告の時刻から `LATE`（30 分）より後に来た自動継続は、窓に入れない**——自動継続は予告の時刻に発火する
  （#454 の周の実データで +1 分）ので、それより遅いものは記録の無い別の停止のものと読む。
- **最初に来たもの**——窓の中で最初の入力か応答（#454 の Issue 本文の表と同じ切り口）:

  | 分類 | 何で決めるか |
  | --- | --- |
  | 自動継続 | `origin.kind == "auto-continuation"`。**`origin` が無い記録だけ**、文言（`AUTO_TEXTS`）で読む |
  | 人間の入力 | `origin.kind == "human"`。`origin` が無ければ `<` で始まらない本文（`isMeta`・`isCompactSummary` を除く） |
  | ローカルコマンド | 本文が `<local-command-caveat>`・`<command-name>`・`<bash-input>`・`<local-command-stdout>` で始まる |
  | `origin.kind` の名前 | それ以外の `origin`（`task-notification`・`peer`・`coordinator`……。**タイマーもここに名前で出る**） |
  | その他の入力 | `origin` が無く `<` で始まる本文（`<task-notification>` など）か、`isMeta`・`isCompactSummary` の記録 |
  | 応答が続いた | 入力より先に `assistant` の応答が来た |
  | 記録の終わり | 窓の中に何も来なかった |

  **ローカルコマンドを先に見る**——人間が打ったスラッシュコマンドは `origin.kind == "human"` を持つ。
- **行方**——窓の中で**最初に来た自動継続・人間の入力・ローカルコマンド**で決める（通知は続けた主体に数えない
  ——通知に応答しても、上限の中ならまた止まる）:

  | 行方 | 条件 |
  | --- | --- |
  | 自動継続 | 自動継続が先に来た |
  | 予告より前に人間 | 人間の入力かローカルコマンドが、**予告の時刻より前に**来た |
  | 予告の後に人間が先 | 同じく、予告の時刻以降（または予告の時刻が不明）に来た |
  | 取り消し | どれも来ず、`Automatic continue cancelled` がある |
  | 続かなかった | どれも来なかった |

- **予告の時刻**——**`resetsAt` を優先し**、無ければ予告の表示（`at 6:40pm`）を `--tz` の時間帯で読む
  （**予告の時刻以降で最初のその時刻**。日付をまたぐ）。差は、行方を決めたものの時刻から引く。
- **停止の記録を持たない自動継続**——窓の外に来た自動継続（ファイルの最初の停止より前か、予告の時刻から
  `LATE` より後）。**落とさずに別の列で数える。** 同じ `uuid` がどれかの待ちの窓に入っていれば数えない（コピー）。

## 0 件を「止まらなかった」と読まないために

**停止が 0 件なら終了コード 3 で終わる。** 形式が変わって検出器が拾えていないのと、
本当に止まらなかったのとは、出力からは区別できない。

## 何を守り、何を守らないか

守る:

- **自動継続を `origin` で決める**——人間が同じ文言を打っても人間の入力（`origin.kind == "human"`）。
- **人間の「継続」を自動継続と読まない**——`origin.kind == "human"` は人間の入力に入れる。
- **`origin` の無い記録は 2 つの文言の両方で読む**——リセットより早く使えるようになったときの文言もある。
- **ローカルコマンドを人間の入力に混ぜない**——`origin.kind == "human"` でも本文の印を先に見る。
- **`origin` の無い `isMeta`・`isCompactSummary` を人間の入力と読まない**——本体が差し込んだ記録である。
- **`tool_result` だけの `user` レコードを入力と読まない**——道具の結果であって、続けた主体ではない。
- **履歴のコピーによる二重計上**——fork / `--resume` は履歴を別ファイルに写すので、
  待ちの最初のレコードの `uuid` で畳む。
- **コピーの窓が短くても、長いほうを使う**——どちらのファイルを先に読むかで行方が変わらない。
- **同じ自動継続を、待ちの中と停止の記録を持たない側の両方に数えない**——コピーにその記録だけが写ることがある。
- **続けて並んだ停止の記録を 1 つの待ちに畳む**——予告の時刻が取れない停止でも。
- **予告の時刻が同じ停止を 1 つの待ちに畳む**——間に通知と応答が挟まっても。
- **予告だけの停止を落とさない**——`rate_limit` のレコードを持たない停止がある。
- **最初に来たものの後の自動継続を拾う**——窓は次の待ちまで。
- **停止の記録を持たない自動継続を落とさない**——別の列で数える。
- **予告の時刻から `LATE` より後の自動継続を、その待ちのものと読まない**——停止の記録を持たない側に数える。
- **予告の時刻は `resetsAt` を先に使う**——表示の時刻は時間帯に依る。
- **表示の時刻を `--tz` の時間帯で読む**——UTC で読むと、時間帯の差だけ予告の時刻がずれる。
- **表示の時刻が日付をまたぐ**——予告より前の時刻なら翌日。
- **取り消しを数える**——`Automatic continue cancelled`。
- **予告より前に来た人間を、予告の後の人間と分ける**——前者は自動継続に機会が無かった待ち。
- **上限の種類を出す**——張らなかった待ちが、どの上限で止まったか。
- **`--since` より前の停止を数えない**——狭くして 0 件なら、下の終了コード 3 になる。
- **0 件の読み違え**——停止が 0 件なら終了コード 3。
- **`--anonymize` で識別子を出さない**——リポジトリ名とセッションを持つ待ちの一覧を出さない。

守らない:

| 守らないもの | なぜ |
| --- | --- |
| **設定が効いたか** | 設定の履歴はトランスクリプトに残らない。**「待ちを張った」は本体がそう表示したことであって、どの層の設定から来たかは分からない** |
| **待たなかった理由**（課金の種類・機能フラグ・上限の種類） | 記録に残らない。`~/.claude.json` の今の値は過去の停止の時点の値ではない。**上限の種類は出すが、それが理由かは見ていない** |
| **サブエージェントの中の停止** | main-chain のファイル（`<project>/<session>.jsonl`）だけを見る——続けるのは親のセッションなので |
| **「予告より前に人間」が待ちを取り消したか** | 待ちを止めたのか、止まった後に打たれたのかは記録から分けられない |
| **タイマーが張られていたか** | タイマーが打った入力は `origin.kind` の名前で出るが、**その名前を確かめた実物は無い**（手元に 0 件） |
| **`origin` を持たない版で文言が同じであること** | 手元の自動継続はすべて `origin` を持つ（#454 の周） |
| **表示の時刻の時間帯** | 表示は記録した端末の時間帯。**`--tz` が違えば差がずれる**（`resetsAt` がある待ちには効かない） |
| **別のセッションの待ち** | 同じ上限に複数のセッションが当たると、それぞれ 1 つの待ちに数える（上限の回数ではない） |

## 出力について

**出すのは集計と識別子（リポジトリ名・セッション id の先頭・時刻）だけ。**
**本文・コマンド・パスは出さない**——トランスクリプトには他のリポジトリのコード・Issue 本文が入っており、
**このリポジトリは公開**である。**PR・Issue に貼るなら `--anonymize`。**

**トランスクリプトの中身は信頼できない入力として扱う**——**何も実行しない。数えるだけ。**
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import pathlib
import re
import sys
import zoneinfo

AUTO_KIND = "auto-continuation"
HUMAN_KIND = "human"
AUTO_TEXTS = (
    "Your claude.ai usage limit has reset. Continue the task",
    "Your claude.ai usage is available again before the usage-limit reset. Continue the task",
)
LOCAL_MARKS = ("<local-command-caveat>", "<command-name>", "<bash-input>", "<local-command-stdout>")
STOP_NOTICE = "Usage limit reached"
ARMED = re.compile(r"continuing automatically at (\d{1,2})(?::(\d{2}))?\s*(am|pm)", re.IGNORECASE)
CANCELLED = "Automatic continue cancelled"
LATE = datetime.timedelta(minutes=30)
WORKTREE_SEP = "/.claude/worktrees/"

AUTO = "自動継続"
HUMAN = "人間の入力"
LOCAL = "ローカルコマンド"
OTHER = "その他の入力"
REPLY = "応答が続いた"
END = "記録の終わり"

FATE_AUTO = "自動継続"
FATE_BEFORE = "予告より前に人間"
FATE_AFTER = "予告の後に人間が先"
FATE_CANCELLED = "取り消し"
FATE_NONE = "続かなかった"
FATES = (FATE_AUTO, FATE_BEFORE, FATE_AFTER, FATE_CANCELLED, FATE_NONE)


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def only_tool_results(content) -> bool:
    return (isinstance(content, list) and bool(content)
            and all(isinstance(b, dict) and b.get("type") == "tool_result" for b in content))


def classify(rec: dict) -> str:
    """`user` レコード 1 件を分類する。**`origin` を先に見る**（文言は `origin` の無い記録だけ）。"""
    text = text_of((rec.get("message") or {}).get("content")).lstrip()
    origin = rec.get("origin")
    kind = origin.get("kind") if isinstance(origin, dict) else None
    if kind == AUTO_KIND:
        return AUTO
    if kind is None and text.startswith(AUTO_TEXTS):
        return AUTO
    if text.startswith(LOCAL_MARKS):
        return LOCAL
    if kind == HUMAN_KIND:
        return HUMAN
    if kind is not None:
        return str(kind)
    if rec.get("isMeta") or rec.get("isCompactSummary"):
        return OTHER
    return OTHER if text.startswith("<") else HUMAN


def parse_ts(value) -> datetime.datetime | None:
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def shown_reset(notice: str, at: datetime.datetime, tz) -> datetime.datetime | None:
    """予告の表示（`at 6:40pm`）を、予告の時刻以降で最初のその時刻として読む。"""
    found = ARMED.search(notice)
    if not found or at is None:
        return None
    hour = int(found.group(1)) % 12 + (12 if found.group(3).lower() == "pm" else 0)
    local = at.astimezone(tz)
    reset = local.replace(hour=hour, minute=int(found.group(2) or 0), second=0, microsecond=0)
    if reset < local:
        reset += datetime.timedelta(days=1)
    return reset.astimezone(datetime.timezone.utc)


def repo_of(cwd: str | None) -> str:
    if not cwd:
        return "?"
    return cwd.split(WORKTREE_SEP, 1)[0]


def new_stop(rec: dict, session: str, uuid: str) -> dict:
    return {"id": uuid, "session": session, "ts": rec.get("timestamp") or "", "repo": repo_of(rec.get("cwd")),
            "reset": None, "shown_reset": None, "limit": None, "armed": False, "cancelled": False, "inputs": [], "autos": []}


def reset_of(stop):
    return stop["reset"] or stop["shown_reset"]


def same_wait(stop, reset) -> bool:
    """予告の時刻が同じなら同じ待ち（表示は分までなので 2 分の幅で比べる）。"""
    known = reset_of(stop)
    return known is not None and reset is not None and abs((known - reset).total_seconds()) < 120


def scan_file(path: pathlib.Path, stats: collections.Counter, tz):
    """1 ファイルから (停止の一覧, 停止の記録を持たない自動継続の一覧) を返す。"""
    stops, orphans = [], []
    stop = None
    session = path.stem
    try:
        handle = open(path, encoding="utf-8", errors="replace")
    except OSError:
        stats["unreadable"] += 1
        return stops, orphans
    with handle:
        for line in handle:
            try:
                rec = json.loads(line)
            except ValueError:
                stats["broken"] += 1
                continue
            if not isinstance(rec, dict):
                continue
            uuid = rec.get("uuid") or f"{session}:{stats['lines']}"
            stats["lines"] += 1
            kind = rec.get("type")
            at = parse_ts(rec.get("timestamp"))
            notice = str(rec.get("content") or "") if kind == "system" else ""
            is_limit = kind == "assistant" and rec.get("error") == "rate_limit"
            if is_limit or notice.startswith(STOP_NOTICE):
                quota = (rec.get("quotaLimits") or {}) if is_limit else {}
                epoch = quota.get("resetsAt")
                reset = (datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)
                         if isinstance(epoch, (int, float)) else None)
                shown = shown_reset(notice, at, tz)
                # 続けて並んだ停止の記録（間に入力も応答も来ていない）と、予告の時刻が同じ停止は 1 つの待ちに畳む
                # ——待ちの間に通知が来て応答し、また上限に当たる形が多い（#454 の周の実データ）。
                if stop is None or (stop["inputs"] and not same_wait(stop, reset or shown)):
                    stop = new_stop(rec, session, uuid)
                    stops.append(stop)
                stop["reset"] = stop["reset"] or reset
                stop["limit"] = stop["limit"] or quota.get("rateLimitType")
                if ARMED.search(notice):
                    stop["armed"] = True
                    stop["shown_reset"] = stop["shown_reset"] or shown
                continue
            if notice.startswith(CANCELLED) and stop is not None:
                stop["cancelled"] = True
                continue
            if kind == "user":
                content = (rec.get("message") or {}).get("content")
                if only_tool_results(content):
                    continue
                label = classify(rec)
            elif kind == "assistant":
                label = REPLY
            else:
                continue
            # 予告の時刻から LATE より後の自動継続は、この待ちのものではない（記録の無い別の停止のもの）
            late = (label == AUTO and stop is not None and at is not None and reset_of(stop) is not None
                    and at > reset_of(stop) + LATE)
            if stop is None or late:
                if label == AUTO:
                    orphans.append({"id": uuid, "session": session, "ts": rec.get("timestamp") or "",
                                    "repo": repo_of(rec.get("cwd"))})
                continue
            stop["inputs"].append((label, at))
            if label == AUTO:
                stop["autos"].append(uuid)
    return stops, orphans


def settle(stop) -> dict:
    """窓の入力から、最初に来たもの・自動継続・待ちの行方を決める。"""
    inputs, reset = stop["inputs"], reset_of(stop)
    stop["first"], stop["first_ts"] = inputs[0] if inputs else (END, None)
    stop["auto_ts"] = next((at for label, at in inputs if label == AUTO), None)
    resumer = next(((label, at) for label, at in inputs if label in (AUTO, HUMAN, LOCAL)), None)
    stop["resumer_ts"] = resumer[1] if resumer else None
    if resumer and resumer[0] == AUTO:
        stop["fate"] = FATE_AUTO
    elif resumer and reset is not None and resumer[1] is not None and resumer[1] < reset:
        stop["fate"] = FATE_BEFORE
    elif resumer:
        stop["fate"] = FATE_AFTER
    else:
        stop["fate"] = FATE_CANCELLED if stop["cancelled"] else FATE_NONE
    return stop


def collect(root: pathlib.Path, since: str | None = None, tz=datetime.timezone.utc):
    """全ファイルを走査し、(待ちの一覧, 停止の記録を持たない自動継続の一覧, 統計) を返す。"""
    stats = collections.Counter()
    stops, orphans = {}, {}
    windowed = set()
    for path in sorted(root.glob("*/*.jsonl")):
        stats["files"] += 1
        found, lone = scan_file(path, stats, tz)
        for s in found:
            windowed.update(s["autos"])
            if s["id"] in stops:
                stats["duplicate_stops"] += 1
                # コピーは途中で切れていることがある——読む順に依らず、窓の長いほうを使う
                if len(s["inputs"]) <= len(stops[s["id"]]["inputs"]):
                    continue
            stops[s["id"]] = settle(s)
        for o in lone:
            orphans.setdefault(o["id"], o)
    keep = sorted((s for s in stops.values() if not since or s["ts"] >= since), key=lambda s: s["ts"])
    lone = sorted((o for o in orphans.values() if o["id"] not in windowed and (not since or o["ts"] >= since)),
                  key=lambda o: o["ts"])
    return keep, lone, stats


def minutes(later, reset) -> str:
    if later is None or reset is None:
        return "–"
    return f"{(later - reset).total_seconds() / 60:+.0f}"


def render(stops, orphans, stats, anonymize=False) -> tuple[str, int]:
    lines = [f"走査: {stats['files']} ファイル（読めない {stats['unreadable']}・壊れた行 {stats['broken']}・"
             f"コピーで畳んだ待ち {stats['duplicate_stops']}）",
             f"待ち: {len(stops)}・停止の記録を持たない自動継続: {len(orphans)}", ""]
    if not stops:
        lines.append("**検出できていない**: 停止が 0 件。形式が変わって拾えていないのと区別できないので、"
                     "「止まらなかった」と読まないこと。")
        return "\n".join(lines) + "\n", 3
    months = sorted({s["ts"][:7] for s in stops} | {o["ts"][:7] for o in orphans}) + ["全体"]

    def rows_of(month):
        return [s for s in stops if month == "全体" or s["ts"][:7] == month]

    lines += ["## 待ちの行方（月ごと）", "",
              "**張った待ち**（予告が `continuing automatically at` を持つ）を、何で続いたかで分ける。"
              "**「予告より前に人間」は、自動継続が発火する前に人間かローカルコマンドが来たもの**——"
              "待ちを取り消したのか、止まった後に打たれたのかは分けられない。", "",
              "| 月 | 待ち | 張った | " + " | ".join(FATES) + " | 張らなかった待ちで自動継続 | 停止の記録を持たない自動継続 |",
              "| --- " * (5 + len(FATES)) + "|"]
    for month in months:
        rows = rows_of(month)
        armed = [s for s in rows if s["armed"]]
        fates = collections.Counter(s["fate"] for s in armed)
        lone = sum(1 for o in orphans if month == "全体" or o["ts"][:7] == month)
        unarmed_auto = sum(1 for s in rows if not s["armed"] and s["fate"] == FATE_AUTO)
        lines.append(f"| {month} | {len(rows)} | {len(armed)} | " + " | ".join(str(fates[f]) for f in FATES)
                     + f" | {unarmed_auto} | {lone} |")
    unarmed = collections.Counter(s["limit"] or "不明" for s in stops if not s["armed"])
    if unarmed:
        lines += ["", "張らなかった待ちの上限の種類（`quotaLimits.rateLimitType`）: "
                  + "・".join(f"{k} {v}" for k, v in sorted(unarmed.items()))]
    labels = [AUTO, HUMAN, LOCAL, OTHER, REPLY, END]
    labels += sorted({s["first"] for s in stops} - set(labels))
    lines += ["", "## 最初に来たもの（月ごと。#454 の Issue 本文の表と同じ切り口）", "",
              "| 月 | " + " | ".join(labels) + " |", "| --- " * (1 + len(labels)) + "|"]
    for month in months:
        firsts = collections.Counter(s["first"] for s in rows_of(month))
        lines.append(f"| {month} | " + " | ".join(str(firsts[x]) for x in labels) + " |")
    autos = [s for s in stops if s["auto_ts"] is not None and reset_of(s) is not None]
    if autos:
        diffs = sorted((s["auto_ts"] - reset_of(s)).total_seconds() / 60 for s in autos)
        lines += ["", f"自動継続の、予告の時刻からの差（分）: 最小 {diffs[0]:+.0f}・中央 "
                      f"{diffs[len(diffs) // 2]:+.0f}・最大 {diffs[-1]:+.0f}（{len(diffs)} 件）"]
    if not anonymize:
        lines += ["", "## 待ちの一覧", "",
                  "| 時刻 | リポジトリ | セッション | 上限 | 張った | 行方 | 最初に来たもの | 続いた時刻の予告からの差（分） |",
                  "| --- " * 8 + "|"]
        for s in stops:
            lines.append(f"| {s['ts'][:16]} | {pathlib.PurePath(s['repo']).name} | {s['session'][:8]} | {s['limit'] or '不明'} | "
                         f"{'張った' if s['armed'] else '–'} | {s['fate']} | {s['first']} | "
                         f"{minutes(s['resumer_ts'], reset_of(s))} |")
        for o in orphans:
            lines.append(f"| {o['ts'][:16]} | {pathlib.PurePath(o['repo']).name} | {o['session'][:8]} | – | – | "
                         f"停止の記録を持たない自動継続 | – | – |")
    return "\n".join(lines) + "\n", 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.home() / ".claude" / "projects",
                        help="トランスクリプトの置き場所（既定: ~/.claude/projects）")
    parser.add_argument("--since", help="この時刻（ISO・UTC）以降の停止だけ数える")
    parser.add_argument("--tz", help="予告の表示の時刻を読む時間帯（IANA 名。既定はこの端末の時間帯）")
    parser.add_argument("--anonymize", action="store_true", help="リポジトリ名を伏せ、停止の一覧を出さない")
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        print(f"置き場所が無い: {args.root}", file=sys.stderr)
        return 2
    try:
        tz = zoneinfo.ZoneInfo(args.tz) if args.tz else datetime.datetime.now().astimezone().tzinfo
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        print(f"時間帯が読めない: {args.tz}", file=sys.stderr)
        return 2
    stops, orphans, stats = collect(args.root, args.since, tz)
    text, status = render(stops, orphans, stats, args.anonymize)
    sys.stdout.write(text)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
