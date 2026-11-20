#!/usr/bin/env python3
"""`git commit` に検証の印（`Verified:` のトレーラー）があるかを見る、任意の PreToolUse hook（#1192）。

**このプラグインは hook を登録しない**（`hooks.json` を持たない）。入れるのは利用者で、`settings.json` の PreToolUse に
このスクリプトを書く（書き方は `references/verification-trailer.md`）。**登録しなければ何も起きない**——既定は off。

## 使い方

- **hook として（引数なし）**: stdin に PreToolUse の JSON（`tool_name`・`tool_input.command`・`cwd`）を受ける。
  Bash の `git commit` だけを見て、コミットメッセージに `Verified:` の行があるかを数える。
  モードは**メインの作業ツリー**の `.claude/dev-loop.md`（worktree の中の写しは読まない。周のブランチが自分のモードを変えられないように）の `検証の関門: off|observe|enforce` の行（既定 `off`）で決まる。
  - `off`: 何もしない（記録もしない）。
  - `observe`: 通す（終了コード 0）。「止めていたはず」を記録に 1 行残す。
  - `enforce`: 満たさないコミットを止める（終了コード 2 と、直し方を stderr に出す）。
- `status`: いま効いているモードと逃げ道、設定の誤りを出す。読むだけ。
- `report`: 記録を数える（通した・止めていたはず・止めた、と理由ごと）。**止めていたはずの 1 件ずつを出す**——
  誤検知かどうかを判定するのは人間である（このスクリプトは判定しない）。

## 満たす条件（`Verified:` の行）

`Verified: <手段>[,<手段>…]`（手段は `tests`・`gates`・`verify`・`code-review`）か、`Verified: none (<理由>)`。
**満たさない形**: 行が無い（`missing`）・手段が上に無い／空（`malformed`）・`none` に理由が無い（`none_without_reason`）・
**逃げ道が `なし` のとき `none` そのもの**（`none_not_allowed`）。
逃げ道は `検証の関門の逃げ道: 理由を書けば通す|なし`（既定 `理由を書けば通す`）。

## 記録の置き場所

`git rev-parse --git-common-dir` の下の `dev-loop-gate.jsonl`（全 worktree で共有。リポジトリの外に出ないので commit されない）。
`DEV_LOOP_GATE_LOG` で差し替えられる（テスト用）。

## 守ること

- **hook として、判定できないときは通す**（stdin が JSON でない・`git` が使えない・設定の誤り）。**`enforce` でもそう**——
  hook は壊れても止めない側に倒す（止めると利用者の作業を巻き込む）。**だから `enforce` は保証ではない**（下）。
- **設定の誤り（値が表に無い・同じ行が 2 本以上）は `off`**。止める側に倒さない。誤りは `status` が名指しする。
- **コードフェンスと HTML コメントの中の行は設定として読まない。**
- 記録に書くのは、時刻・モード・結果・理由・cwd・コマンドの**先頭 120 文字**だけ。メッセージ全文は書かない。

## 守らないこと

- **`Verified:` の中身が事実かは見ない。** 手段を名乗っているか（形）しか見ない。**どの関門を通したかの突き合わせは
  `check-gates.py`**（計画ファイルの記録と履歴）で、これは別。
- **hook が動かない環境では何も止まらない**（python3 が無い・hook が登録されていない・Claude Code が hook を読まない）。
  **このスクリプトは、本物の Claude Code に登録して発火させた検証をしていない**——テストは hook の stdin を
  真似て呼ぶ（`scripts/test-commit-gate.py`）。stdin の鍵と終了コード 2 の意味は公式の説明に従った。
- **`git commit` を直接呼ばない形**（`git` の別名・スクリプトの中のコミット・IDE のコミット）は見ない。
- `-C`／`-c`（メッセージの再利用）と、エディタを開くコミットはメッセージを読めず、`missing` になる。
- `--amend` でメッセージを渡さないときは、直前のコミットのメッセージを読む。
- **同じセッションで 2 回止めたら次は通す、という逃げ道は採っていない**（セッションの状態を持つ必要がある）。

終了コード（hook）: 0 通す／2 止める（enforce のみ）。`status`・`report`: 0 表示した／3 記録が無い（`report`）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

MODES = ("off", "observe", "enforce")
ESCAPES = ("理由を書けば通す", "なし")
DEFAULT_MODE = "off"
DEFAULT_ESCAPE = "理由を書けば通す"
METHODS = ("tests", "gates", "verify", "code-review")

GIT_COMMIT = re.compile(
    r"(?:^|[;&|\n(]|\s)git(?:\s+(?:-C\s+\S+|-c\s+\S+|--[\w-]+(?:=\S+)?))*\s+commit\b"
)
TRAILER = re.compile(r"^[ \t]*Verified:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
NONE_FORM = re.compile(r"^none(?:[ \t]*[(（](.*)[)）])?$")
FENCE = re.compile(r"^[ \t]*(```|~~~)")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
HEAD_LEN = 120

GUIDE = (
    "コミットメッセージの最後の段落に検証の印を付けてください: "
    "`Verified: tests,gates,verify,code-review` のうち実際に回したもの、"
    "回していなければ `Verified: none (理由)`。"
)


def strip_noise(text: str) -> str:
    """コードフェンスと HTML コメントの中を消す（そこに書いた設定の行は設定ではない）。"""
    text = COMMENT.sub("", text)
    out, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def read_setting(text: str, key: str, allowed: tuple[str, ...], default: str) -> tuple[str, str | None]:
    """`<key>: <値>` の行を読む。(値, 誤りの説明)。誤りは既定に倒す。"""
    pat = re.compile(rf"^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
    values = pat.findall(strip_noise(text))
    if not values:
        return default, None
    if len(values) > 1:
        return default, f"`{key}:` の行が {len(values)} 本ある（1 本にまとめる）"
    if values[0] not in allowed:
        return default, f"`{key}:` の値 {values[0]!r} は {' / '.join(allowed)} のどれでもない"
    return values[0], None


def git(cwd: str, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def load_config(cwd: str) -> tuple[str, str, list[str]]:
    """(モード, 逃げ道, 誤りの一覧)。.claude/dev-loop.md が無ければ既定。"""
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common or Path(common).name != ".git":
        return DEFAULT_MODE, DEFAULT_ESCAPE, ["メインの作業ツリーが決まらない（.git でない共通ディレクトリ）ので設定を読まない"]
    path = Path(common).parent / ".claude" / "dev-loop.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_MODE, DEFAULT_ESCAPE, []
    mode, e1 = read_setting(text, "検証の関門", MODES, DEFAULT_MODE)
    esc, e2 = read_setting(text, "検証の関門の逃げ道", ESCAPES, DEFAULT_ESCAPE)
    errors = [e for e in (e1, e2) if e]
    return mode, esc, errors


def commit_message_text(command: str, cwd: str) -> str:
    """判定に使うメッセージの文面。コマンド全体（-m・ヒアドキュメント）＋ -F のファイル＋ amend の直前のメッセージ。"""
    text = command
    for m in re.finditer(r"(?:-F|--file)(?:=|\s+)(\S+)", command):
        p = Path(m.group(1).strip("'\""))
        p = p if p.is_absolute() else Path(cwd) / p
        try:
            text += "\n" + p.read_text(encoding="utf-8")
        except OSError:
            pass
    has_msg = re.search(r"(?:^|\s)(?:-[a-zA-Z]*m\b|--message\b|-F\b|--file\b)", command) or "<<" in command
    if re.search(r"--amend\b", command) and (not has_msg or "--no-edit" in command):
        prev = git(cwd, "log", "-1", "--format=%B")
        if prev:
            text += "\n" + prev
    return text


def judge(text: str, escape: str) -> str | None:
    """満たさない理由の名前。満たせば None。"""
    found = TRAILER.findall(text)
    if not found:
        return "missing"
    value = found[-1].rstrip("\"'").strip()
    m = NONE_FORM.match(value)
    if m:
        if not (m.group(1) or "").strip():
            return "none_without_reason"
        return "none_not_allowed" if escape == "なし" else None
    tokens = [t.strip() for t in value.split(",")]
    if all(t in METHODS for t in tokens):
        return None
    return "malformed"


def log_path(cwd: str) -> Path | None:
    env = os.environ.get("DEV_LOOP_GATE_LOG")
    if env:
        return Path(env)
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common) / "dev-loop-gate.jsonl" if common else None


def write_log(cwd: str, record: dict) -> None:
    p = log_path(cwd)
    if p is None:
        return
    try:
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"検証の関門: 記録を書けなかった（{exc}）", file=sys.stderr)


def hook() -> int:
    try:
        data = json.load(sys.stdin)
        command = data["tool_input"]["command"]
        tool = data.get("tool_name", "Bash")
        cwd = data.get("cwd") or os.getcwd()
    except (ValueError, KeyError, TypeError):
        return 0  # 判定できないときは通す
    if tool != "Bash" or not isinstance(command, str):
        return 0
    if not GIT_COMMIT.search(command) or "--dry-run" in command:
        return 0
    mode, escape, errors = load_config(cwd)
    if mode == "off":
        return 0
    reason = judge(commit_message_text(command, cwd), escape)
    action = "pass" if reason is None else ("would_stop" if mode == "observe" else "stopped")
    write_log(cwd, {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "mode": mode, "action": action,
        "reason": reason, "cwd": cwd, "command_head": command[:HEAD_LEN],
    })
    if action == "stopped":
        print(f"検証の関門（enforce）: コミットを止めた（{reason}）。{GUIDE}", file=sys.stderr)
        return 2
    return 0


def status(project: str) -> int:
    mode, escape, errors = load_config(project)
    print(f"検証の関門: {mode}（既定 {DEFAULT_MODE}）／逃げ道: {escape}（既定 {DEFAULT_ESCAPE}）")
    for e in errors:
        print(f"設定の誤り（既定に倒した）: {e}")
    return 0


def report(log: str | None, since: str | None, cwd: str) -> int:
    p = Path(log) if log else log_path(cwd)
    if p is None or not p.exists():
        print("検証の関門: 記録が無い")
        return 3
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if since and r.get("ts", "") < since:
            continue
        rows.append(r)
    counts: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for r in rows:
        counts[r.get("action", "?")] = counts.get(r.get("action", "?"), 0) + 1
        if r.get("reason"):
            reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    print(f"検証の関門の記録: {len(rows)} 件（{p}）")
    print("  結果: " + "・".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print("  理由: " + ("・".join(f"{k} {v}" for k, v in sorted(reasons.items())) or "なし"))
    stops = [r for r in rows if r.get("action") in ("would_stop", "stopped")]
    for r in stops:
        print(f"  [{r.get('action')}] {r.get('ts')} {r.get('reason')} — {r.get('command_head')}")
    print("誤検知かは、上の 1 件ずつを人が見て決める（このスクリプトは判定しない）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")
    sp = sub.add_parser("status")
    sp.add_argument("--project", default=os.getcwd())
    rp = sub.add_parser("report")
    rp.add_argument("--log")
    rp.add_argument("--since", help="ISO 時刻（これ以降の記録だけ数える）")
    rp.add_argument("--project", default=os.getcwd())
    args = ap.parse_args()
    if args.cmd == "status":
        return status(args.project)
    if args.cmd == "report":
        return report(args.log, args.since, args.project)
    return hook()


if __name__ == "__main__":
    sys.exit(main())
