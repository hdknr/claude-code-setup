#!/usr/bin/env python3
r"""spec-loop の autopilot（#789）を外から繰り返し起こすループ（外側のループ。#850）。台帳（`autopilot-ledger.py`。#848）の `status` が
`running` のあいだだけ `claude -p` を 1 回ずつ起こし、使用量の上限に当たったら解除の時刻まで待って起こし直す。

    python3 <spec-loop の根>/scripts/autopilot-loop.py <版> [--max-launches 20] [--max-stalls 2] [--max-same-state 3] \
        [--limit-wait 1800] [--max-limit-wait 21600] [--claude claude] [--prompt "/spec-loop:autopilot <版>"] [-- <claude に足す引数> …]

長期トークン（#584）で起こすなら、dev-loop の起動口を `--claude` に渡す——`--claude "bash <dev-loop の skills/dev-loop>/scripts/launch-with-long-token.sh"`
（アカウントを分けるなら起動口の決まりどおり `… launch-with-long-token.sh --account <名前>`）。起動口は受けた引数をそのまま `claude` に渡す。

## なぜ在るのか（#789・#790）

#789 の試作の外側のループ（手で書いた bash）は、`phase` が `done`・`stopped` のときだけ終わる作りで、エージェントが止まったことを `status` に書いても気づかず、
前進を台帳のファイルのハッシュで見ていたので、時刻と回数を書き換えるだけの起動を前進と数え、**約 15 時間・約 1,900 回 `claude -p` を空回りさせた**（#790）。
このループは、起こすかを台帳の `status` の 1 欄だけで決め（`autopilot-ledger.py status` の終了コード）、前進を進捗の欄（`autopilot-ledger.py progress`）だけで比べる。

**cruise の外側のループ（dev-loop の `skills/cruise/scripts/outer-loop.py`。#791）を写した形だが、import も相対パスでの呼び出しもしない**——spec-loop だけを
入れた利用者に dev-loop が在るとは限らず、プラグインをまたいで相対パスで指せない（`autopilot-ledger.py` の `main_worktree` の写しと同じ理由）。
**写しは `notify`・`stop_child` の 2 関数だけ**で、元とずれないことを `scripts/test-autopilot-loop.py`（リポジトリの根）が関数のソースを突き合わせて見る。
ループの本体は、cruise に無い止め方（同じ状態での起動の上限・使用量の上限の待ち）を持つので写しにしていない。

## 1 回の起動

台帳 `<版>`（このスクリプトの隣の `autopilot-ledger.py`）について、

1. `autopilot-ledger.py status <版>` を走らせる。**0（`running`）のときだけ続ける**——3（`stopped`）・5（`done`）・4（判定できない）・表に無い値では起こさずに止まる。
2. `autopilot-ledger.py progress <版>`（`phase`・`cycle`・`stage`・`commit` だけの 1 行。`updated` などを含まない）を控える。
3. 起動の総数が `--max-launches` に達していれば、起こさずに止まる。**同じ `progress` から起こした起動（使用量の上限で終わったものを除く）が `--max-same-state` 回に
   達していれば、起こさずに止まる**——段を行き来させる（A→B→A→B…）起動は毎回 `progress` が変わって前進なしに数えられないので、こちらで止める（#858 の C1-5）。
4. メインの作業ツリー（台帳の場所——`autopilot-ledger.py path` から）を cwd に、標準入力を閉じて

       <--claude> -p <--prompt> --output-format stream-json --verbose --append-system-prompt <追記> [<足す引数> …]

   を起こし、終わるのを待つ。標準出力と標準エラーは台帳の隣の `spec-autopilot-v<版>-loop/` に起動ごとのファイルで残す（使用量の上限を読むため）。
   環境には **`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`** を置く——`-p` はターンを閉じた後の背景のタスクを上限の時間しか待たずに止める（#633。
   cruise の `outer-loop.py` と同じ。0 で止めずに待つことは測っていない）。利用者の環境に別の値があっても 0 で上書きし、上書きしたことを出す。
   **追記（`APPEND`）は、非対話の起動の決まりを渡す**——`status` が `running` でなければ何もせず台帳も書き換えずに終える・進めるのは次の 1 単位まで
   （#790 の直し方の「ループが終われなかったときの二重の歯止め」）。原本は入口のスキル（#849）で、追記は短く指すだけにする。
5. **出力に使用量の上限の印があれば**（下の「上限の読み方」）、解除の時刻に `LIMIT_MARGIN` 秒（既定 60）を足した時刻まで待って（時刻が読めなければ
   `--limit-wait` 秒）、1 に戻る。待つ時間が `--max-limit-wait` 秒を超えるなら待たずに止まる（週の上限で何日も黙って待たない）。
   **上限の起動は、前進なしにも同じ状態の回数にも数えない**（前進があれば前進なしの数を 0 に戻す）。**起動の総数には数える**——上限が続いても無限には回らない。
6. 上限の印が無く、`claude` が 0 以外で終わった・起こせなかったら止まる（ログインの期限切れなどで、何も進めずにすぐ終わる起動を繰り返さない）。
7. もう一度 `progress` を取り、2 と同じなら「前進なし」を 1 つ数える。**続けて `--max-stalls` 回になったら止まる**。変わっていれば数を 0 に戻す。

止まるときは、理由を標準出力の最後の行に出し、**通知する**（`osascript` が在れば macOS の通知。本文は argv で渡し、AppleScript の文字列に埋め込まない）。

### 上限の読み方

出力（標準出力と標準エラー）の各行を JSON として読めれば、

- `type` が `rate_limit_event` の**最後の 1 つ**の `rate_limit_info.status` が `allowed`・`allowed_warning`・無し以外なら上限。`resetsAt`（UNIX 秒）が数なら解除の時刻。
- `type` が `result` で `api_error_status` が 429 なら上限。`is_error` が真なら、その `result` の文も下の文言で読む。
- `type` が `assistant` で `error` が `rate_limit` の行（トランスクリプトの記録の形）なら上限。`quotaLimits.resetsAt` が数なら解除の時刻。
  **ほかの `type` の `error` は見ない**（`api_retry` のような途中の再試行の印）。

JSON として読めない行は、文言 `usage limit reached`・`hit your limit`（大文字小文字を区別しない）で上限と読み、どちらの後ろでも `|<10 桁の数>` が続けば解除の時刻とする。
**「limit reached」だけの文（`spending limit reached` など）は上限と読まない。** **JSON の中のアシスタントの文は読まない**——文が #790 のことを語っただけで上限と読まない。

**`claude` が 0 で終わり、最後の `result` が `is_error` でなければ、上の印があっても上限と読まない**——最後まで走りきった起動で、途中の再試行の印で待たない。
解除の時刻に使うのは数だけで、真偽値・NaN は読めないものとして扱う。**ミリ秒のように桁の多い値・無限・float に収まらない整数は、遠い時刻として読み、待ちが長すぎるので 10 で止まる**（単位は測っていない）。
**`rate_limit_event` で上限と決まったときは、解除の時刻もその event の `resetsAt` だけから読む**（無ければ読めない）——前の行の別の上限の時刻を引き継がない。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 済んだ——`status` が 5（`done`） |
| 2 | 引数が違う（版の形——正の整数で先頭に 0 を付けない・桁が `int()` の上限を超える・上限が 1 未満・待ちが負・`--claude` を語に分けられない・`--prompt` が空）。**通知しない**（引数を読む前に止まる） |
| 3 | 止まった——`status` が 3（`stopped`）。理由と利用者に頼むことは `autopilot-ledger.py status <版>` の出力（止まった行にも写す） |
| 4 | 判定できなかった——`status` が 4 か表に無い値・`progress` が 0 以外・台帳の場所を決められない・出力の置き場を作れない・ループの中の予期しない例外。**「済んだ」とも「止まった」とも答えていない** |
| 6 | 前進なし——`progress` の変わらない起動が続けて `--max-stalls` 回 |
| 7 | 起動の上限——`--max-launches` 回起こした後も `status` が 0 |
| 8 | `claude` が 0 以外で終わった（使用量の上限と読めない）・起こせなかった |
| 9 | 同じ状態での起動の上限——同じ `progress` から（使用量の上限で終わらなかった）起動を `--max-same-state` 回起こした（段の行き来） |
| 10 | 使用量の上限の解除が遠い——待つ時間が `--max-limit-wait` 秒を超える |
| 130 | 中断された（Ctrl-C・SIGTERM・SIGHUP。待ちの中も。起動時に無視させられていたシグナルは除く） |

## 何を守り、何を守らないか

守る:

- **`status` が 0 のときだけ `claude` を起こす**——起動の前に毎回見て、3・4・5・表に無い値では起こさずに止まる（`phase` は見ない。#790）。
- **前進は `progress` で比べる**——台帳のファイルのまま比べない（`updated` だけの書き換えを前進に数えない）。
- **`progress` を読めなければ止まる（4）**——読めない要約を「前進なし」「前進あり」のどちらにも数えない。
- **前進なしの起動が続けて `--max-stalls` 回になったら止まる。**
- **前進があったら、前進なしの数を 0 に戻す**——続けてでない前進なしで止めない。
- **起動の総数が `--max-launches` に達したら、起こさずに止まる**——使用量の上限で終わった起動も数える。
- **同じ `progress` から起こした起動が `--max-same-state` 回に達したら、起こさずに止まる**——段の行き来で前進なしに掛からない空回りを止める（#858 の C1-5）。
- **上限の印が無いまま `claude` が 0 以外で終わった・起こせなかったら止まる。**
- **出力に使用量の上限の印があれば、`claude` の失敗にせず、待ってから次の判定に戻る。**
- **解除の時刻が読めれば、その時刻に `LIMIT_MARGIN` 秒を足した時刻まで待つ。**
- **解除の時刻が読めなければ `--limit-wait` 秒待つ。**
- **待つ時間が `--max-limit-wait` 秒を超えるなら、待たずに止まる（10）。**
- **上限で終わった起動は、前進なしに数えない。**
- **上限で終わった起動は、同じ状態の回数に数えない。**
- **上限で終わった起動でも、前進があれば前進なしの数を 0 に戻す。**
- **トランスクリプトの形（`error` が `rate_limit` のアシスタントの行）では `quotaLimits.resetsAt` を解除の時刻に読む。**
- **JSON でない行は `usage limit reached`・`hit your limit` だけを上限と読む**——「limit reached」だけの文（`spending limit reached` など）を上限と読まない。
- **`|<10 桁>` は、どちらの文言の後ろでも解除の時刻に読む。**
- **`claude` が 0 で終わり、最後の `result` が成功なら上限と読まない**——途中の再試行の印（`api_retry` など）で待たない。
- **解除の時刻が時刻として表せない値（ミリ秒など）でも、例外にせず 10 で止まる。**
- **解除の時刻が float に収まらない整数でも、例外にせず 10 で止まる。**
- **`quotaLimits` が辞書でなくても例外にせず、時刻の読めない上限と読む。**
- **`rate_limit_event` で上限と決まったら、解除の時刻はその event からだけ読む**——前の行の別の上限の時刻を引き継がない。
- **上限と読めない失敗は、`progress` を読む前に 8 で止まる**——台帳が読めなくても `claude` の失敗の理由を隠さない。
- **`allowed_warning` の `rate_limit_event` と、JSON の中のアシスタントの文の「usage limit」を上限と読まない。**
- **`rate_limit_event` は最後の 1 つで決める**——途中で拒まれて後で `allowed` に戻った起動を上限と読まない。
- **引数を読めた後の止まるすべての経路で通知する**——済んだ・止まった・判定できない・前進なし・起動の上限・同じ状態の上限・`claude` の失敗・解除が遠い・
  中断（`claude` の実行中も待ちの中も）・ループの中の予期しない例外。
- **`claude` の cwd はメインの作業ツリー**——worktree の中・サブディレクトリから呼んでも同じ。
- **`claude` の環境に `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` を置く**——利用者の環境に無くても、別の値があっても（上書きしたと出す）。
- **`--append-system-prompt` で追記（`APPEND`）を渡す。**
- **`--output-format stream-json --verbose` を付けて起こす**——上限を `rate_limit_event`・`result` で読むため。
- **`--claude` に渡したコマンドに、`-p` と同じ引数を渡す**——長期トークンの起動口（`launch-with-long-token.sh`）を挟んでも、`claude` が同じ引数を受ける。
- **版は正の整数だけで、先頭の 0 と桁が `int()` の上限を超える値を 2 で拒む**——台帳と同じ形（`autopilot-ledger.py` が `03` を拒むので、ここで別の台帳を指さない）。
- **起動時に無視させられていた SIGTERM・SIGHUP（`nohup` の SIGHUP など。SIG_IGN）にはハンドラを置かない**——無視したまま回り続ける（cruise の `outer-loop.py` と同じ。#820）。
- **中断されたら、`claude` にまず SIGTERM を送って `GRACE` 秒（既定 10）終わるのを待ち、終わらなければ SIGKILL で止める**——`claude` を残したまま終わらない。
- **`notify`・`stop_child` は cruise の `outer-loop.py` の写しで、ソースが一致する**（テストが突き合わせる）。

守らない:

- **本物の `claude -p` が使用量の上限で何を出して終わるか**——上の「上限の読み方」は、cruise の `references/child-process.md` の表 3（子の出力に `rate_limit_event` と
  `result` の `api_error_status` が載る。試しでは `allowed` しか見ていない）と、トランスクリプトの記録の形（`scripts/count-usage-limit-resumes.py`）から決めた想定である。
  上限は狙って作れないので、本物で確かめていない。**読めなかった上限は `claude` の失敗（8）として止まって通知する**——空回りはしないが、待って再開もしない。
- **表示の時刻（`resets 6pm` など）を読むこと**——時間帯に依るので読まず、`--limit-wait` 秒待つ。
- **入口（#849）の名前・引数と、入口が追記に従うか**——既定の `--prompt` は #789 の例の名前で、入口が決まったら `--prompt` で合わせる。
  入口が `stopped` で台帳を書き換えない・1 単位で止めることは、このループからは確かめない（止めるのは `status` と `progress` の判定）。
- **台帳と実物（コミット・PR）が一致しているか**——`status` も `progress` も台帳の値だけで決める（`autopilot-ledger.py` の「守らない」）。
- **通知が見えること**——`osascript` が 0 で終わったかも見ない。`osascript` の無い環境（macOS 以外）では通知を出さない（理由は標準出力に出る）。
- **1 回の起動の長さ**——`claude` を待つだけで、時間で打ち切らない。
- **`claude` の版・許可モード・モデル・認証**——足す引数（`--` の後ろ）と `--claude` で利用者が決める。長期トークンの起動口が読めない（キーチェーンに無い）なら、起動口が
  0 以外で終わるので 8 で止まる。
- **同じ台帳を回すループ・対話のセッションが他に走っていないか**——台帳を書くのは 1 体である。
- **出力の置き場（`spec-autopilot-v<版>-loop/`）を消すこと・大きさ**——起動ごとにファイルが増える。
"""

import argparse
import datetime
import json
import math
import os
import re
import signal
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "autopilot-ledger.py"
BG_CEILING = "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"
GRACE = 10  # 中断のとき claude の後始末を待つ秒数（過ぎたら SIGKILL）
LIMIT_MARGIN = 60  # 解除の時刻のあと、起こし直すまでに足す秒数
# 非対話の起動の決まり（#850）。原本は入口のスキル（#849）——ここは #790 の二重の歯止めを短く渡すだけ
APPEND = (
    "この起動は spec-loop の autopilot の外側のループ（autopilot-loop.py）が起こした非対話の起動で、利用者は応答しない（#850）。"
    "台帳（autopilot-ledger.py）の status が running でなければ、何もせず、台帳も書き換えずに終える。"
    "進めるのは台帳の次の 1 単位までにする。進められないなら、確かめた回数・時刻・「変わらず」を台帳に書かずに終える"
    "——止まるなら status=stopped と reason・next を書く。"
)
TITLE = "spec-loop の autopilot の外側のループが止まりました"
OK_LIMIT_STATUSES = (None, "allowed", "allowed_warning")
LIMIT_TEXT = re.compile(r"usage limit reached|hit your limit", re.IGNORECASE)
LIMIT_EPOCH = re.compile(r"(?:usage limit reached|hit your limit)\|(\d{10})\b", re.IGNORECASE)

EXIT_DONE = 0
EXIT_USAGE = 2
EXIT_STOPPED = 3
EXIT_UNKNOWN = 4
EXIT_STALLED = 6
EXIT_LIMIT = 7
EXIT_CLAUDE = 8
EXIT_SAME_STATE = 9
EXIT_LIMIT_FAR = 10
EXIT_INTERRUPTED = 130


def ledger(*args):
    """(終了コード, 標準出力)。起こせなければ (None, 理由)。"""
    try:
        r = subprocess.run([sys.executable, str(LEDGER), *args], capture_output=True, text=True)
    except OSError as exc:
        return None, f"autopilot-ledger.py を起こせない: {exc}"
    if r.stderr:
        sys.stderr.write(r.stderr)
    return r.returncode, r.stdout


def progress(version):
    code, out = ledger("progress", version)
    return out if code == 0 else None


def notify(body):
    if not shutil.which("osascript"):
        return
    # 値は argv で渡す（AppleScript の文字列に埋め込まない）
    script = ("on run argv\n"
              "display notification (item 1 of argv) with title (item 2 of argv)\n"
              "end run")
    try:
        subprocess.run(["osascript", "-e", script, body, TITLE],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def pause(seconds):
    """使用量の上限の解除を待つ（テストが差し替える）。"""
    time.sleep(seconds)


def epoch(value):
    """解除の時刻（UNIX 秒）を float で。読めなければ None（数でない・真偽値・NaN）。無限と float に収まらない整数は無限（遠い時刻）。"""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except OverflowError:  # 桁の多すぎる整数——例外にせず遠い時刻として読む
        return math.inf
    return None if math.isnan(value) else value


def shown(reset):
    """解除の時刻の表示。表せない値（ミリ秒で桁が多い、など）でも例外にしない。"""
    try:
        return f"解除 {datetime.datetime.fromtimestamp(reset, datetime.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
    except (ValueError, OverflowError, OSError):
        return f"解除 {reset}（時刻として表せない）"


def read_limit(paths, rc):
    """(上限か, 解除の時刻（UNIX 秒）か None)。出力のファイルを読む。"""
    limited, reset, last_event, last_result = False, None, None, None
    for path in paths:
        try:
            lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                event = json.loads(line)
            except ValueError:
                event = None
            if not isinstance(event, dict):
                if LIMIT_TEXT.search(line):
                    limited = True
                    m = LIMIT_EPOCH.search(line)
                    if m:
                        reset = int(m.group(1))
                continue
            kind = event.get("type")
            if kind == "rate_limit_event":
                last_event = event.get("rate_limit_info") or {}
            elif kind == "result":
                last_result = event
                if event.get("api_error_status") == 429:
                    limited = True
                text = event.get("result")
                if event.get("is_error") and isinstance(text, str) and LIMIT_TEXT.search(text):
                    limited = True
                    m = LIMIT_EPOCH.search(text)
                    if m:
                        reset = int(m.group(1))
            elif kind == "assistant" and event.get("error") == "rate_limit":
                limited = True
                quota = event.get("quotaLimits")
                at = epoch(quota.get("resetsAt")) if isinstance(quota, dict) else None
                if at is not None:
                    reset = at
    if isinstance(last_event, dict) and last_event.get("status") not in OK_LIMIT_STATUSES:
        limited = True
        reset = epoch(last_event.get("resetsAt"))  # 上限を決めた event の時刻だけ——前の別の上限の時刻を引き継がない
    if rc == 0 and isinstance(last_result, dict) and not last_result.get("is_error"):
        return False, None  # 最後まで走りきった起動——途中の再試行の印で待たない
    return limited, reset


def launch(args, main_tree, logs, n):
    """(終了コード か None, 出力のファイルの組)。"""
    cmd = [*args.claude_cmd, "-p", args.prompt, "--output-format", "stream-json", "--verbose",
           "--append-system-prompt", APPEND, *args.extra]
    env = dict(os.environ)
    if env.get(BG_CEILING) not in (None, "0"):
        print(f"{BG_CEILING}={env[BG_CEILING]} を 0 で上書きした")
    env[BG_CEILING] = "0"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out, err = logs / f"{n:03d}-{stamp}.out", logs / f"{n:03d}-{stamp}.err"
    print(f"起こす: {shlex.join(cmd[:3])} …（cwd: {main_tree}・出力: {out}）", flush=True)
    proc = None
    try:
        with open(out, "wb") as fo, open(err, "wb") as fe:
            proc = subprocess.Popen(cmd, cwd=main_tree, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe, env=env)
            return proc.wait(), (out, err)
    except OSError as exc:
        print(f"claude を起こせない: {exc}", file=sys.stderr)
        return None, (out, err)
    except BaseException:  # 中断（Ctrl-C・SIGTERM・SIGHUP）——`subprocess.run` のようにいきなり SIGKILL にしない
        if proc is not None:
            stop_child(proc)
        raise


def stop_child(proc):
    """claude に SIGTERM を送り、`GRACE` 秒待っても終わらなければ SIGKILL。"""
    try:
        proc.terminate()
    except OSError:
        pass
    try:
        proc.wait(timeout=GRACE)
    except BaseException:  # 時間切れ・待つあいだの 2 度目の中断——claude を残して終わらない
        proc.kill()
        proc.wait()


def run_loop(args):
    """(終了コード, 理由)。"""
    code, out = ledger("path", args.version)
    if code != 0:
        return EXIT_UNKNOWN, f"台帳の場所を決められない（autopilot-ledger.py path: {code}）"
    path = Path(out.strip())
    main_tree = path.parent.parent.parent
    logs = path.with_name(path.stem + "-loop")
    try:
        logs.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return EXIT_UNKNOWN, f"出力の置き場を作れない（{logs}: {exc}）"
    launches = stalls = 0
    seen = {}
    while True:
        code, out = ledger("status", args.version)
        print(f"status: {code} {out.strip()}", flush=True)
        if code == 5:
            return EXIT_DONE, f"済んだ（{out.strip()}）"
        if code == 3:
            return EXIT_STOPPED, f"止まった（{' '.join(out.split())}）"
        if code != 0:
            return EXIT_UNKNOWN, f"判定できなかった（status: {code}）"
        before = progress(args.version)
        if before is None:
            return EXIT_UNKNOWN, "判定できなかった（progress を読めない）"
        if launches >= args.max_launches:
            return EXIT_LIMIT, f"起動の上限 {args.max_launches} 回に達した（status は running のまま）"
        if seen.get(before, 0) >= args.max_same_state:
            return EXIT_SAME_STATE, f"同じ状態（{before.strip()}）から {seen[before]} 回起こした（{launches} 回起動）"
        launches += 1
        rc, files = launch(args, main_tree, logs, launches)
        limited, reset = read_limit(files, rc) if rc is not None else (False, None)
        if not limited and rc != 0:  # progress を読む前に——台帳が読めなくても失敗の理由を隠さない
            return EXIT_CLAUDE, f"claude が失敗した（{rc if rc is not None else '起こせない'}・{launches} 回目の起動）"
        after = progress(args.version)
        if after is None:
            return EXIT_UNKNOWN, "判定できなかった（progress を読めない）"
        if limited:
            if after != before:
                stalls = 0
            if reset is not None:
                wait = max(0.0, reset - time.time()) + LIMIT_MARGIN
                why = shown(reset)
            else:
                wait = args.limit_wait
                why = "解除の時刻を読めない"
            if wait > args.max_limit_wait:
                return EXIT_LIMIT_FAR, f"使用量の上限の解除が遠い（{why}・待ち {wait:.0f} 秒 > {args.max_limit_wait} 秒・{launches} 回目の起動）"
            print(f"使用量の上限（{why}）——{int(wait)} 秒待つ", flush=True)
            pause(wait)
            continue
        seen[before] = seen.get(before, 0) + 1
        if after == before:
            stalls += 1
            print(f"前進なし（続けて {stalls} 回）", flush=True)
            if stalls >= args.max_stalls:
                return EXIT_STALLED, f"前進なしが続けて {stalls} 回（{launches} 回目の起動）"
        else:
            stalls = 0


def build_parser():
    p = argparse.ArgumentParser(description="spec-loop の autopilot を外から繰り返し起こすループ（#850）")
    p.add_argument("version", help="autopilot で回している版の番号（docs/v<n>/ の n）")
    p.add_argument("--max-launches", type=int, default=20, help="起動の総数の上限（既定 20）")
    p.add_argument("--max-stalls", type=int, default=2, help="前進なしが続けてこの回数で止まる（既定 2）")
    p.add_argument("--max-same-state", type=int, default=3, help="同じ progress から起こす回数の上限（既定 3）")
    p.add_argument("--limit-wait", type=int, default=1800, help="上限の解除の時刻が読めないとき待つ秒数（既定 1800）")
    p.add_argument("--max-limit-wait", type=int, default=21600, help="これより長く待つなら止まる（秒。既定 21600）")
    p.add_argument("--claude", default="claude", help="claude を起こすコマンド（既定 claude。長期トークンなら起動口）")
    p.add_argument("--prompt", default=None, help="起こす文（既定 /spec-loop:autopilot <版>）")
    return p


class Interrupted(Exception):
    """SIGTERM・SIGHUP を受けた。"""


def _on_signal(signum, _frame):
    raise Interrupted(signal.Signals(signum).name)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    # `--` の後ろは claude に足す引数。argparse に任せない——Python 3.11 以前は、位置引数の後に選択肢があると `--` の後ろを拒む
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    head = argv[:argv.index("--")] if "--" in argv else argv
    try:
        args = build_parser().parse_args(head)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else 0
    args.extra = extra
    try:
        args.claude_cmd = shlex.split(args.claude)
    except ValueError:
        args.claude_cmd = []
    # ASCII の数字だけで、先頭の 0 を付けない（台帳と同じ形）。桁が `int()` の上限（`sys.get_int_max_str_digits()`。0 は上限なし）を超えるものも拒む
    limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
    if (not re.fullmatch(r"[1-9][0-9]*", args.version) or (limit and len(args.version) > limit)
            or args.max_launches < 1 or args.max_stalls < 1 or args.max_same_state < 1
            or args.limit_wait < 0 or args.max_limit_wait < 0 or not args.claude_cmd
            or (args.prompt is not None and not args.prompt.strip())):
        print("引数が違う: 版は正の整数（先頭に 0 を付けない）、上限は 1 以上、待ちは 0 以上、--claude は語に分けられるコマンド、--prompt は空でない",
              file=sys.stderr)
        return EXIT_USAGE
    if args.prompt is None:
        args.prompt = f"/spec-loop:autopilot {args.version}"
    # **起動時に無視させられていたら（`nohup` の SIGHUP など。SIG_IGN）置かない**——上書きすると、無視させて起動した側の意図を破って止まる（#820 と同じ）
    saved = {s: signal.signal(s, _on_signal) for s in (signal.SIGTERM, signal.SIGHUP)
             if signal.getsignal(s) != signal.SIG_IGN}
    try:
        code, reason = run_loop(args)
    except KeyboardInterrupt:
        code, reason = EXIT_INTERRUPTED, "中断された"
    except Interrupted as exc:
        code, reason = EXIT_INTERRUPTED, f"中断された（{exc}）"
    except Exception as exc:  # noqa: BLE001 — どの経路でも通知する（守る）
        code, reason = EXIT_UNKNOWN, f"判定できなかった（予期しない例外: {type(exc).__name__}: {exc}）"
    finally:
        for s, h in saved.items():
            signal.signal(s, h)
    line = f"autopilot の外側のループ: 止まった（v{args.version}: {reason}）"
    print(line, flush=True)
    notify(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
