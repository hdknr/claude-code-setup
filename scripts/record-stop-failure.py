#!/usr/bin/env python3
"""`StopFailure` の hook。止まったその場で、手元のファイルに 1 行残して通知を出す。

    python3 scripts/record-stop-failure.py < 入力の JSON

**hook として登録して使う**（登録の手順は `docs/usage/usage-limit-stop-hook.md`。**登録は利用者が行う**）。
**CI からは呼ばない**——書く先が利用者の `~/.claude` にある。テストだけ回す。標準ライブラリのみ。

なぜ必要か（#468）: #456（利用上限の自動継続の陽性対照）は**上限を狙って起こせない**。気づかなければ記録は埋もれ、
止まったときに人間が「継続」と打てば陽性対照にならない。**止まった時点を残し、そのとき利用者に知らせる。**
**自動継続が起きたかは、この hook は知らない**——`count-usage-limit-resumes.py` で後から数える。
記録があることが「数える時が来た」の合図になる。

`StopFailure` は「API のエラー（rate limit・認証の失敗など）でターンが終わったとき、`Stop` の代わりに発火する。
fire-and-forget——hook の出力と終了コードは無視される」（本体 2.1.311 の文字列）。だから**落ちても誰も気づかない**。

書く先: `$HOME/.claude/usage-limit-stops.jsonl`（`LOG`）に 1 行 1 件で追記する。1 行に書くのは:

- `time`（UTC）・`hook_event_name`・`session_id`・`error`——文字列のときだけ、先頭 `SHORT` 文字まで（それ以外は `null`）
- `cwd_hash`——`cwd` の SHA-256 の先頭 12 文字（同じ場所の停止を束ねるため。**生の値は書かない**）
- `error_details`——文字列のときだけ、先頭 `DETAILS` 文字まで
- 読めなかったときは `time` と `unreadable`（理由だけ。**入力の値は書かない**）

守る:

- `last_assistant_message` の値を、記録にも通知にも出さない
- `cwd` の生の値を、記録にも通知にも出さない
- `error_details` は先頭 `DETAILS` 文字まで
- `error`・`session_id`・`hook_event_name` は先頭 `SHORT` 文字まで
- 文字列でない値（辞書など）は書かない
- JSON でない・オブジェクトでない入力で例外を出さず、`unreadable` の 1 行を残す
- `error` が無い入力でも例外を出さず、`unreadable` の 1 行を残す
- 前の行を消さずに追記する（`~/.claude` が無ければ作る）
- 書けない文字（対にならないサロゲート）が来ても記録は残る
- 通知が失敗しても（`osascript` が無い・失敗する・引数にできない値）記録は残り、0 で終わる
- 上限らしい `error`（`LIMIT`）なら、通知に「『継続』と打たずにリセットまで待つ」（#456）を添える
- 上限らしくない `error` には「待て」を添えない（認証の失敗などに待っても直らない）

守らない:

- **`StopFailure` が利用上限で実際に発火すること・`error` がどの値になるか**——確かめていない
  （上限を狙って起こせない）。本体 2.1.311 は `billing_error` を「usage limit reached — check plan」、
  `rate_limit` を「rate limited — wait and retry」に対応づけているので、`LIMIT` は両方を持つ。
  **だから matcher で絞らずに登録する**（docs の手順）。**記録が無いことは「発火しない」の証拠にならない**（hook が壊れていても無い）
- **待ちの間に何回発火するか**——確かめていない。束ねるのは `count-usage-limit-resumes.py` の側
- **書けないとき（`HOME` が書き込めない等）に知らせること**——fire-and-forget なので伝える先が無い。0 で終わる
- **通知が実際に見えること**——`osascript` が 0 で終わったかまで。macOS の通知の設定で出ないことがある。
  `osascript` の無い環境（macOS 以外）では通知を出さない
- **`cwd_hash` から `cwd` を戻せないこと**——塩を入れていないので、既知のパスなら辞書で戻せる。ファイルは手元にしか無い
"""

from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

LOG = Path(".claude") / "usage-limit-stops.jsonl"
DETAILS = 200
SHORT = 100
LIMIT = ("rate_limit", "billing_error")
WAIT = "止まっても「継続」と打たずに、リセットまで待ってください（#456 の陽性対照のため）"


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def text(value, limit):
    """文字列なら先頭 `limit` 文字、それ以外は `None`（辞書などの中身を書かない）。"""
    return value[:limit] if isinstance(value, str) else None


def parse(raw: bytes) -> dict:
    """入力から記録の 1 行を作る。読めなければ理由だけの行を返す。"""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return {"time": now(), "unreadable": "JSON として読めない"}
    if not isinstance(data, dict):
        return {"time": now(), "unreadable": "JSON のオブジェクトでない"}
    if not isinstance(data.get("error"), str):
        return {"time": now(), "unreadable": "error が無い"}
    row = {"time": now(), "hook_event_name": text(data.get("hook_event_name"), SHORT),
           "session_id": text(data.get("session_id"), SHORT), "error": text(data["error"], SHORT)}
    cwd = data.get("cwd")
    if isinstance(cwd, str):
        row["cwd_hash"] = hashlib.sha256(cwd.encode("utf-8")).hexdigest()[:12]
    details = text(data.get("error_details"), DETAILS)
    if details is not None:
        row["error_details"] = details
    return row


def append(row: dict) -> None:
    path = Path.home() / LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        # ASCII に逃がす——対にならないサロゲートは UTF-8 で書けない
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def notify(row: dict) -> None:
    if not shutil.which("osascript"):
        return
    error = row.get("error") or "入力を読めなかった"
    limit = error in LIMIT
    title = "Claude Code が止まりました（利用上限かもしれません）" if limit else "Claude Code が止まりました"
    body = f"{error}。{WAIT}" if limit else error
    # 値は argv で渡す（AppleScript の文字列に埋め込まない）
    script = ("on run argv\n"
              "display notification (item 1 of argv) with title (item 2 of argv)\n"
              "end run")
    subprocess.run(["osascript", "-e", script, body, title],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)


def main() -> int:
    try:
        row = parse(sys.stdin.buffer.read())
    except Exception:  # noqa: BLE001 — fire-and-forget。何が来ても落ちない
        row = {"time": now(), "unreadable": "入力を読めない"}
    try:
        append(row)
    except Exception:  # noqa: BLE001 — 書けなくても通知は出す
        pass
    try:
        notify(row)
    except Exception:  # noqa: BLE001 — 通知の失敗（NUL を含む引数など）でも 0 で終わる
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
