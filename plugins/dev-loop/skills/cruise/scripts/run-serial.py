#!/usr/bin/env python3
r"""重い検査・アプリの起動を、同じリポジトリでは決めた本数ずつ順番待ちにして走らせる（#493）。

    python3 <このスキルの base ディレクトリ>/scripts/run-serial.py -- <コマンド> [引数 …]

**いつ通すか（cruise の周が、どのコマンドをこれ越しに走らせるか）は `references/parallel.md` を正とする**
（このスキルと同じ場所にある）。ここにあるのは枠の数え方と、このスクリプトが守るものである。

## なぜ在るのか（#493）

cruise の親が 7 体のサブエージェントを並行に走らせ、各体がこのリポジトリの `check-all.py` をほぼ同時に起こした。
`check-all.py` は 1 本で CPU の数だけ並列に回り、中の `check-mutation-claims.py` はさらに並列に子を起こす——掛け算になり、
**負荷の平均が 217（10 コア）**、時間で待ち合わせるテストが時間切れで落ちうる状態になった（#509 では 300 秒の時間切れ）。
対象リポジトリによっては、同時に起こしたアプリがポート・データベースを奪い合い、**別の周のテストとデータが混ざる**。

## 枠

**同じリポジトリ（worktree をまたいで）で、同時に走らせるのは `N` 本まで。** `N` はメインの作業ツリーの `.claude/dev-loop.md` の
宣言 1 行で決める:

```
並行の検査: 2
```

- **宣言が無ければ 1**（安全側）。**ファイルが在るのに読めない（UTF-8 でない・権限）・値が 1 以上の整数（6 桁まで）でない・行が 2 本以上・`並行の検査` を含むのに上の形に合わない行
  （全角のコロン・字下げ・箇条書きの印など）があるなら 1 として扱い、そう言う。**
- **コードブロック（` ``` `・`~~~` を 3 つ以上。字下げが空白 3 つまでの、同じ文字で同じ数以上の行で閉じる——CommonMark の規則）と HTML コメント（`<!-- … -->`。行の途中で始まっても）の中の行は宣言に数えない**——例示や外した行で枠が増えない。
  先頭の BOM は読み飛ばす。
- 読むのは**メインの作業ツリー**の `.claude/dev-loop.md`（共通ディレクトリ `--git-common-dir` が `.git` ならその親）。
  **worktree の中の写しは読まない**——周ごとにブランチの写しが違うと、同じリポジトリで枠の数が食い違う。
  メインの作業ツリーが決まらない（`--separate-git-dir`・サブモジュール・bare）なら宣言は読まず 1。
- 枠のファイルは共通ディレクトリの下の `dev-loop-serial/slot-<k>.lock`（`k` は 0 から `N-1`）。**枠は `fcntl.flock` の排他で、
  持ったプロセスが終われば（異常終了でも）外れる。** 持っている間はファイルに pid・場所・コマンド・始めた時刻を書き、待つ側がそれを出す。

## 終了コード

| 値 | 意味 |
| --- | --- |
| コマンドの終了コード | 走らせた。シグナルで終わったら 128 + シグナルの番号、コマンドが見つからなければ 127 |
| 125 | **走らせていない**——枠を決められなかった（git が使えない・リポジトリの外・枠のファイルを開けない） |
| 2 | 走らせていない——`--` の後ろにコマンドが無い |

**125 と 2 は、コマンドがその値を返したときとは出力で見分ける**（`run-serial:` で始まる行が理由を言う）。

## 入れ子

**順番待ちの中から、同じリポジトリの順番待ちを呼んだら、待たずにそのまま走らせる**——環境変数 `DEV_LOOP_SERIAL_HELD` に
枠のディレクトリを入れて子に渡し、同じ値なら枠を取らない（自分の持っている枠を待って固まらない）。

## 守る／守らない

守る:
- 同じリポジトリでは、worktree をまたいで、枠の本数（宣言、無ければ 1）を超えて同時に走らせない
- 待たされたら、待っていることと、いま走っているもの（pid・場所・コマンド）を出力で言う
- 走らせたコマンドの終了コードをそのまま返す（シグナルは 128 + 番号）
- 入れ子で呼ばれたら（同じリポジトリの枠を持つ順番待ちの子孫）、待たずにそのまま走らせる
- 枠を決められなければ、コマンドを走らせずに 125 を返す
- 宣言が 1 以上の整数（6 桁まで）でない・2 行以上・`並行の検査` を含むのに書式に合わない行がある・宣言のファイルが在るのに読めないなら、1 として扱い、そう言う
- コードブロックと HTML コメントの中の行は宣言に数えない
- コードブロックは、空白 4 つ以上で字下げした行では閉じない（CommonMark の閉じ行でない）
- コードブロックは、開いた印と別の文字（` ``` ` に対する `~~~`）の行では閉じない
- 宣言の行末の HTML コメントは外して読む（`並行の検査: 3 <!-- メモ -->` は 3）
- ラッパー自身が SIGTERM・SIGHUP・SIGINT を受けても、コマンドに渡して、コマンドが終わるまで枠を離さない

守らない:
- 別のリポジトリ・別のマシンの実行とは数えない
- 順番待ちを通さずに走ったもの（周の言語モデルの体そのもの・これを通さない検査）は数えない
- 走っている側が固まったら、待つ側はいつまでも待つ（時間切れは無い）
- コマンドが残したバックグラウンドのプロセスは、コマンドが終わった後は枠を持たない（枠のファイルは子に継承しない）
- 宣言を信頼するかは見ない（枠を増やすのは負荷を緩めるだけで、権限は広げない）
- 宣言を変えた時点で走っているもの（減らす前の枠の番号を持つもの）は数えない
- ラッパーが SIGKILL で殺されたら、枠は外れ、コマンドは走り続ける（捕まえられないシグナル）
- 入れ子の印（環境変数）はコマンドの子孫すべてに渡る——コマンドが残したバックグラウンドのプロセスが後で順番待ちを呼ぶと、待たずに走る
- 入れ子の印は 1 つのリポジトリしか持たない——別のリポジトリをはさんで同じリポジトリへ戻る入れ子（A → B → A）は、枠 1 なら固まる
- 待つ側の順番（公平性）は決めない——枠が空いたときに先に見た側が取る

標準ライブラリのみ。POSIX（`fcntl`）が要る——macOS と Linux。
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ENV = "DEV_LOOP_SERIAL_HELD"
CANNOT = 125
USAGE = 2
NOT_FOUND = 127
POLL = 0.5
DECL = re.compile(r"^並行の検査:[ \t]*(.*?)[ \t]*$")
DIGITS = re.compile(r"[0-9]{1,6}")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")


def say(message: str) -> None:
    print(f"run-serial: {message}", file=sys.stderr, flush=True)


def common_dir(cwd: Path) -> Path | None:
    """共通ディレクトリ（worktree をまたいで同じ）。決まらなければ None。"""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    out = proc.stdout.strip()
    if proc.returncode != 0 or not out:
        return None
    return Path(out)


def closes(line: str, char: str, width: int) -> bool:
    """コードブロックの閉じ行か（CommonMark）: 字下げは空白 3 つまで、開いた印と同じ文字だけを同じ数以上（後ろの空白は可）。"""
    indent = len(line) - len(line.lstrip(" "))
    body = line.strip()
    return indent <= 3 and len(body) >= width and set(body) == {char}


def declared_lines(text: str) -> list[str]:
    """コードブロックと HTML コメントの外の行。先頭の BOM は外す。

    コードブロックは、開いた印（` ``` `・`~~~` を 3 つ以上）と同じ文字で、同じ数以上だけの行で閉じる（CommonMark の規則）。
    HTML コメントは行のどこで始まっても、閉じるまで（行をまたいでも）外す。"""
    lines: list[str] = []
    fence: tuple[str, int] | None = None
    comment = False
    for line in text.lstrip("\ufeff").splitlines():
        stripped = line.strip()
        if fence:
            char, width = fence
            if closes(line, char, width):
                fence = None
            continue
        kept, rest = "", line
        while rest:
            if comment:
                end = rest.find("-->")
                if end < 0:
                    rest = ""
                else:
                    comment, rest = False, rest[end + 3:]
            else:
                start = rest.find("<!--")
                if start < 0:
                    kept, rest = kept + rest, ""
                else:
                    kept, comment, rest = kept + rest[:start], True, rest[start + 4:]
        opened = FENCE.match(kept)
        if opened and not comment:
            fence = (opened.group(1)[0], len(opened.group(1)))
            continue
        if kept.strip():
            lines.append(kept)
    return lines


def slots_from(text: str | None) -> tuple[int, str | None]:
    """宣言から枠の本数を決める。(本数, 言うこと)。"""
    if text is None:
        return 1, None
    lines = declared_lines(text)
    values = [m.group(1) for line in lines if (m := DECL.match(line))]
    odd = [line for line in lines if "並行の検査" in line and not DECL.match(line)]
    if odd:
        return 1, f"`並行の検査` の行が書式に合わない（{odd[0].strip()!r}）——1 として扱う"
    if not values:
        return 1, None
    if len(values) > 1:
        return 1, f"`並行の検査:` の行が {len(values)} 本ある——1 として扱う"
    value = values[0]
    if not DIGITS.fullmatch(value) or int(value) < 1:
        shown = value if len(value) <= 20 else value[:20] + "…"
        return 1, f"`並行の検査:` の値 {shown!r} は 1 以上の整数（6 桁まで）でない——1 として扱う"
    return int(value), None


def declaration(common: Path) -> tuple[str | None, str | None]:
    """メインの作業ツリーの `.claude/dev-loop.md`。(中身, 言うこと)。無ければ (None, None)、在るのに読めなければ言う。"""
    if common.name != ".git":
        return None, None
    path = common.parent / ".claude" / "dev-loop.md"
    try:
        return path.read_text(encoding="utf-8"), None
    except FileNotFoundError:
        return None, None
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"`{path}` を読めない（{exc.__class__.__name__}）——宣言は 1 として扱う"


def holders(lockdir: Path, slots: int) -> list[str]:
    found = []
    for k in range(slots):
        try:
            info = json.loads((lockdir / f"slot-{k}.lock").read_text(encoding="utf-8") or "{}")
        except (OSError, ValueError):
            continue
        if isinstance(info, dict) and info:
            found.append(f"pid {info.get('pid')}・{info.get('cwd')}・{info.get('command')}（{info.get('started')} から）")
    return found


def acquire(lockdir: Path, slots: int) -> int:
    """枠を 1 つ取って fd を返す。取れるまで待つ。"""
    waited = None
    while True:
        for k in range(slots):
            fd = os.open(lockdir / f"slot-{k}.lock", os.O_RDWR | os.O_CREAT, 0o644)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(fd)
                continue
            if waited is not None:
                say(f"{time.monotonic() - waited:.1f} 秒待って枠を取った")
            return fd
        if waited is None:
            waited = time.monotonic()
            running = holders(lockdir, slots)
            say(f"待っている（同じリポジトリで同時に {slots} 本まで）。走っているもの: "
                + ("; ".join(running) if running else "（読めなかった）"))
        time.sleep(POLL)


def record(fd: int, command: list[str]) -> None:
    info = {"pid": os.getpid(), "cwd": os.getcwd(), "command": " ".join(command),
            "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, json.dumps(info, ensure_ascii=False).encode("utf-8"))


def run(command: list[str], env: dict[str, str]) -> int:
    try:
        proc = subprocess.Popen(command, env=env)
    except FileNotFoundError:
        say(f"コマンドが見つからない: {command[0]}")
        return NOT_FOUND
    except OSError as exc:
        say(f"コマンドを起動できない: {exc}")
        return NOT_FOUND
    def forward(signum, _frame):
        try:
            proc.send_signal(signum)
        except ProcessLookupError:
            pass

    previous = {s: signal.signal(s, forward) for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)}
    try:
        code = proc.wait()
    finally:
        for s, handler in previous.items():
            signal.signal(s, handler)
    return 128 - code if code < 0 else code


def main(argv: list[str]) -> int:
    if "--" not in argv or not argv[argv.index("--") + 1:]:
        say("使い方: run-serial.py -- <コマンド> [引数 …]")
        return USAGE
    command = argv[argv.index("--") + 1:]

    common = common_dir(Path.cwd())
    if common is None:
        say("枠を決められない（git の共通ディレクトリが決まらない）——走らせていない")
        return CANNOT
    lockdir = common / "dev-loop-serial"

    env = dict(os.environ)
    if os.environ.get(ENV) == str(lockdir):
        return run(command, env)

    text, unreadable = declaration(common)
    if unreadable:
        say(unreadable)
    slots, note = slots_from(text)
    if note:
        say(note)
    try:
        lockdir.mkdir(exist_ok=True)
        fd = acquire(lockdir, slots)
        record(fd, command)
    except OSError as exc:
        say(f"枠を決められない（{exc}）——走らせていない")
        return CANNOT
    env[ENV] = str(lockdir)
    try:
        return run(command, env)
    finally:
        os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
