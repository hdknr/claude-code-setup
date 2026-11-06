#!/usr/bin/env python3
r"""重い検査・アプリの起動を、同じリポジトリでは決めた本数ずつ順番待ちにして走らせる（#493）。

    python3 <このスキルの base ディレクトリ>/scripts/run-serial.py [--timeout <秒>] -- <コマンド> [引数 …]
    python3 <このスキルの base ディレクトリ>/scripts/run-serial.py holders     # 持ち主を出すだけ（#898）

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
- **コードブロック（` ``` `・`~~~` を 3 つ以上。CommonMark の規則——字下げが空白 3 つまでの、同じ文字で同じ数以上だけの行で閉じ、後ろには空白とタブしか置けない。
  バッククォートの印の後ろにバッククォートがある行は始まりでない）と HTML コメント（`<!-- … -->`）の中の行は宣言に数えない**——例示や外した行で枠が増えない。
  コメントは行の途中で始まっても外す。ただし**コードブロックの開き行の後ろ（情報文字列）の `<!--` はコメントでなく**、
  **段落の中で始まって閉じないコメントは、コードブロックの開き行で終わる**（CommonMark ではコードブロックが段落を割り込む）。
  段落の中のコメントでないのは、行頭（空白 3 つまで。リストや引用の印の直後を含む）で始まったコメントと、その行で開き直したコメント、
  行頭のコメントを `-->` で閉じた行で開き直したコメント——どれもコードブロックの開き行で終わらない（GitHub は後ろを隠す）。
  行は改行（`\n`・`\r\n`・`\r`）でだけ分ける。先頭の BOM は 1 つだけ読み飛ばす。
  **同じ読み方の写しが `../../dev-loop/scripts/check-unattended-env.py`（同じ `.claude/dev-loop.md` を読む）と `parent-issue.py` にあり、
  リポジトリの `scripts/test-fence-copies.py` が同じ試料の表で突き合わせる**（#758・#759・#760）。
- 読むのは**メインの作業ツリー**の `.claude/dev-loop.md`（共通ディレクトリ `--git-common-dir` が `.git` ならその親）。
  **worktree の中の写しは読まない**——周ごとにブランチの写しが違うと、同じリポジトリで枠の数が食い違う。
  メインの作業ツリーが決まらない（`--separate-git-dir`・サブモジュール・bare）なら宣言は読まず 1。
- 枠のファイルは共通ディレクトリの下の `dev-loop-serial/slot-<k>.lock`（`k` は 0 から `N-1`）。**枠は `fcntl.flock` の排他で、
  持ったプロセスが終われば（異常終了でも）外れる。** 持っている間はファイルに pid・場所・コマンド・始めた時刻を書き、待つ側がそれを出す。

## 期限（#897）

**枠を取ってからコマンドが走ってよいのは `--timeout <秒>`（1 以上の整数。7 桁まで）まで。渡さなければ既定の `DEFAULT_TIMEOUT`（3600 秒）。**
待っている時間は数えない。期限を過ぎたら、コマンドとその子孫（`bash -c` の下のプロセスなど。`ps` で親子をたどる）に SIGTERM を送り、
`GRACE`（10 秒）待っても残るもの（猶予のあいだに生まれた子孫を数え直して足す）に SIGKILL を送ってから、枠を返して **124** で終わる——`run-serial: 期限切れ` で始まる行が言う。
**期限切れは緑ではない**（コマンドは走りきっていない）。

- **#839**: トンネル越しの写しが切れた接続を待ったまま枠を約 45 分握り、並行の他の周の重いテストと当の周の関門が全部待ちになった。
- **既定の 3600 秒は、このリポジトリの `check-all.py`（全部の歯止め）を順番待ちの中で回した実測（#897 の計画ファイル）に余裕を持たせた値**である
  ——cruise は終える前に main の先端でこれを流す（cruise の `SKILL.md` §6）ので、既定で切ってはならない。
  **アプリを開いたまま確かめるなど、もっと長く走るものは `--timeout` で延ばす。**

## 呼び出し元が居なくなった待ち手（#897）

**枠を待っているあいだに、起動したときの親（`os.getppid()`）が変わったら、枠を取らずに終わる（125。走らせていない）。**
#839 では、呼び出した `Bash` の上限で親のシェルが先に終わった待ち手が、PPID=1 の孤児として待ち続けた——枠が空いて走っても、結果を読む者がいない。
**見るのは待っているあいだだけ**——枠を取った後に親が居なくなったコマンドは、期限まで走る。

## 持ち主の表示（#898）

**待たされたら、走っているもの（枠の持ち主）を 1 つ 1 行で出し、待っているあいだ `REPORT`（60 秒）ごとに出し直す。** 1 行に出すのは
pid・場所・コマンド・**経過**（枠を取ってから。始めた時刻も）・**出力の最終更新**で、出力が `STALL`（600 秒）以上増えていない持ち主は
行末に `止まっている疑い` と出す。**疑いを出すだけで、止めない——止めるのは期限だけ（上の「期限」）。**

- **#839**: 写しが切れた接続を待ったまま枠を握っていたことに、待っている側も cruise の親も 1 回の見張りぶん気づけなかった（見ていたのはコミットの時刻とファイルの更新だけ）。
- **出力の最終更新**は、枠を取ったラッパーの標準出力・標準エラー（コマンドが継ぐ）が**通常のファイル**なら、そのパス（macOS は `F_GETPATH`、Linux は `/proc/self/fd`）と
  `st_dev`・`st_ino` を枠のファイルの記録に足しておき、見る側がそのファイルの `st_mtime`（2 つあれば新しいほう）を読む。
  cruise の形（`… > "$OUT" 2>&1`。`references/parallel.md`）はファイルなので当たる。**パイプ・端末・`/dev/null` は「分からない」と言い、疑いを出さない。**
- **`STALL` の 600 秒は、このリポジトリの `check-all.py` を順番待ち越しに回したときの出力の間隔の実測（#898 の計画ファイル）に余裕を持たせた値**である
  ——ふつうの重い検査が疑いと出ないように。
- **`holders` の口**: `run-serial.py holders` は、持ち主を標準出力に 1 回だけ出して 0 で終わる（無ければ `走っているものは無い`）。cruise の親の見張りが同じものを読むための口で、
  **枠を取らず（`flock` も掛けない）、何も書き換えない**（枠のディレクトリが無ければ作らない）。引数を足すと 2。
- 見るのは枠のディレクトリの `slot-<k>.lock` の全部（宣言の本数に依らない）。記録の pid が居ないもの（走り終えて記録だけ残ったもの）は出さない。

## 終了コード

| 値 | 意味 |
| --- | --- |
| コマンドの終了コード | 走らせた。シグナルで終わったら 128 + シグナルの番号、コマンドが見つからなければ 127 |
| 124 | **期限切れ**——走らせたが、期限を過ぎたので止めた（上の「期限」） |
| 125 | **走らせていない**——枠を決められなかった（git が使えない・リポジトリの外・枠のファイルを開けない）か、待っているあいだに呼び出し元が居なくなった |
| 2 | 走らせていない——`--` の後ろにコマンドが無い・`--timeout` の値が 1 以上の整数（7 桁まで）でない・`--` の前に知らない引数がある・`holders` の後ろに引数がある |

**124・125・2 は、コマンドがその値を返したときとは出力で見分ける**（`run-serial:` で始まる行が理由を言う）。

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
- ラッパー自身が SIGTERM・SIGHUP・SIGINT を受けても、コマンドが終わるまで枠を離さない。SIGTERM・SIGHUP はコマンドに渡す
- SIGINT はコマンドに渡さない——端末の Ctrl-C（プロセスグループ全体への SIGINT）で、コマンドに 2 度届かない（#739）
- コードブロックは、空白 3 つまでで字下げした行で閉じる
- コードブロックは、開いた印とちょうど同じ数の行で閉じる
- コードブロックは、後ろに空白とタブ以外の文字がある行（` ``` x`）では閉じない
- コードブロックは、タブで字下げした行では閉じない（タブは 4 桁に数える。#743）
- コードブロックは、後ろに空白とタブ以外の空白文字（全角の空白など）がある行では閉じない（#743）
- 行は改行でだけ分ける——`\x0b`・`\u2028` などの後ろを別の行（閉じ行）と読まない（#743）
- `\x0c`（改ページ）の後ろも別の行と読まない（#758）
- バッククォートの印の後ろにバッククォートがある行（` ```a`b `）はコードブロックを始めない（#743）
- 空白 4 つ以上で字下げした印の行はコードブロックを始めない
- 行の途中の印はコードブロックを始めない
- `~~~` の印でもコードブロックを始める
- HTML コメントの中の印はコードブロックを始めない
- 開き行は元の行で見る——コメントの後ろの印（`<!-- -->```）・コメントで区切ったバッククォートの情報文字列（`` ```a<!--`--> ``）では始めない
- 情報文字列の `<!--` はコメントの始まりと読まない（`` ```<!-- `` はコードブロックの始まり）
- 段落の中で始まって閉じないコメントの後ろの行でも、印の行はコードブロックを始める（`memo <!--` の次の ` ``` `。#758）
- 先頭の BOM を外して読む
- 先頭の BOM は 1 つだけ外す——続く BOM は行に残り、書式に合わない行として 1 と言う（#758）
- `-->` で閉じた行頭のコメントの残りで開き直したコメントは、行頭のコメントのまま読む——コードブロックの開き行で終わらない（`<!--` の次の `--> x <!--`。GitHub は後ろを隠す。#758）
- リストや引用の印の直後で始まるコメント（`- <!--`・`> <!--`）は行頭のコメントとして読む——コードブロックの開き行で終わらない（GitHub は後ろを隠す。#758）
- 期限（`--timeout`、無ければ既定）を過ぎたコマンドを止めて、枠を返す——待っていた別の呼び出しが走り出す（#897）
- 期限切れは 124 を返す——止めたコマンドの終了コード（シグナルの 128 + 番号）を返さない（#897）
- 期限切れは `run-serial: 期限切れ` で始まる行で言う（#897）
- 期限切れで止めるとき、コマンドの子孫（`bash -c` の下のプロセス）まで止める（#897）
- 期限切れで SIGTERM を受けても終わらないものは、猶予（`GRACE`）の後に SIGKILL で止める（#897）
- 待っているあいだに呼び出し元（起動したときの親）が居なくなったら、枠を取らずに 125 で終わり、そう言う（#897）
- `--timeout` の値が 1 以上の整数（7 桁まで）でない・`--` の前に知らない引数があるなら、走らせずに 2 を返す（#897）
- `--timeout` を渡さなければ、既定（`DEFAULT_TIMEOUT`。上の「期限」の値）の期限を掛ける（#897）
- 入れ子で呼ばれても（枠を取らずに走らせるときも）、同じ期限を掛ける（#897）
- 期限切れの猶予のあいだに子孫が起こした子も、猶予の後にまだ生きている子孫からたどって止める——コマンドが先に終わっていても（#897 の 2 パス目）
- 待たされているあいだ、`REPORT` 秒ごとに持ち主を出し直す（#898）
- 持ち主ごとに、枠を取ってからの経過時間を出す（#898）
- 持ち主ごとに、出力の最終更新（標準出力・標準エラーが通常のファイルなら、その `st_mtime`）を出す（#898）
- 出力が `STALL` 秒以上増えていない持ち主に `止まっている疑い` と出す（#898）
- 出力が `STALL` 秒の内に増えた持ち主には `止まっている疑い` と出さない（#898）
- 出力の最終更新が分からない持ち主（出力がファイルでない）には `止まっている疑い` と出さない（#898）
- `holders` は持ち主を 1 回だけ出して 0 で終わる——枠を取らない（枠が全部ふさがっていても待たない）（#898）
- `holders` は枠のディレクトリが無ければ作らない（#898）
- `holders` は枠のファイルに書かない（#898）
- 枠のファイルに残った記録のうち、pid が居ないもの（走り終えたもの）は持ち主として出さない（#898）

守らない:
- 別のリポジトリ・別のマシンの実行とは数えない
- 順番待ちを通さずに走ったもの（周の言語モデルの体そのもの・これを通さない検査）は数えない
- 走っている側が固まったら、待つ側は走っている側の期限まで待つ（待つ側自身の待ち時間に上限は無い——前に並ぶ全部の期限の和まで待ちうる）
- 期限は枠を取ってから数える——待っている時間は数えない
- 期限切れで止める子孫は、期限を過ぎた時点に `ps` で親子をたどれたものと、猶予の後にまだ生きているもの（コマンドと先に数えた子孫）から
  たどれたものだけ——自分で親を離れた（デーモン化した）プロセス・親が先に終わって init に移った後に生まれた子・
  別のユーザーのプロセスは止めない。`ps` が使えなければコマンドだけを止め、そう言う
- 期限切れで止めた子孫が使っていたもの（一時ファイル・ポート・リモートの接続）は片付けない
- 呼び出し元を見るのは待っているあいだだけ——枠を取った後に呼び出し元が居なくなっても、コマンドは期限まで走る
- 呼び出し元は「起動したときの親の pid（`os.getppid()`）が変わったか」で見る——起動したときから親が 1 のもの（親が居なくなっても 1 のまま）は見分けない。
  親が生きたまま結果を読まなくなった（親のシェルが出力を捨てた）ものも見分けない
- コマンドが残したバックグラウンドのプロセスは、コマンドが終わった後は枠を持たない（枠のファイルは子に継承しない）
- 宣言を信頼するかは見ない（枠を増やすのは負荷を緩めるだけで、権限は広げない）
- 宣言を変えた時点で走っているもの（減らす前の枠の番号を持つもの）は数えない
- ラッパーが SIGKILL で殺されたら、枠は外れ、コマンドは走り続ける（捕まえられないシグナル）
- ラッパーにだけ送った SIGINT（`kill -INT <ラッパーの pid>`）はコマンドに届かない——コマンドを止めるなら、ラッパーに SIGTERM を送るか、プロセスグループに SIGINT を送る
- プロセスグループ全体に送った SIGTERM・SIGHUP は、コマンドに 2 度届く（直接と、ラッパーの転送）——ラッパーの pid だけに送られたときに止まらなくなるので、渡すのをやめない
- コマンドを起こしてからシグナルの扱いを置くまでの間に届いたシグナルは、ラッパーを既定の動き（終わる）にする
- 入れ子の印（環境変数）はコマンドの子孫すべてに渡る——コマンドが残したバックグラウンドのプロセスが後で順番待ちを呼ぶと、待たずに走る
- 入れ子の印は 1 つのリポジトリしか持たない——別のリポジトリをはさんで同じリポジトリへ戻る入れ子（A → B → A）は、枠 1 なら固まる
- 待つ側の順番（公平性）は決めない——枠が空いたときに先に見た側が取る
- 出力の最終更新が分かるのは、ラッパーの標準出力・標準エラーが通常のファイルのときだけ——パイプ・端末・`/dev/null` へ出すものは分からない。
  コマンドが中で別のファイルに書き直すもの（`bash -c 'x > f'`）は、そのファイルでなくラッパーの出力を見る。パスを取れない（`F_GETPATH` も `/proc` も無い）環境でも分からない
- `止まっている疑い` は出力の時刻だけで決める——出力をため込む（バッファする）コマンドは走っていても疑いと出ることがあり、出力を出し続けながら進まないもの（同じ行を繰り返す）は疑わない
- 古い版（1.100.0 まで）の run-serial が持つ枠は、出力のファイルを記録しないので、出力の最終更新は分からない（経過は出す）
- 経過は記録の始めた時刻（秒まで）から数える——時計を合わせ直すとずれる
- 居なくなった pid は `kill -0` で見る——pid が再利用された記録・ゾンビの記録は持ち主として出る
- `holders` が読むあいだに持ち主が替わると、古い記録か新しい記録のどちらかを出す（書きかけで読めなければ出さない）
- CommonMark の全部は写さない——段落を切るほかの行（空行・見出し・リスト）は、行の途中で始まったコメントを終わらせない（コメントのまま外す。宣言は増えない側）。
  行頭のコメントは `-->` を含む行で閉じるまで続く（その行の後ろで開き直した `<!--` も、閉じるまでコメント）。`<!-->`・`<!--->` は閉じたコメントと読まない

標準ライブラリのみ。POSIX（`fcntl`）が要る——macOS と Linux。
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import signal
import stat
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ENV = "DEV_LOOP_SERIAL_HELD"
CANNOT = 125
USAGE = 2
NOT_FOUND = 127
TIMED_OUT = 124
DEFAULT_TIMEOUT = 3600
GRACE = 10.0
TIMEOUT_VALUE = re.compile(r"[0-9]{1,7}")
POLL = 0.5
REPORT = 60.0
STALL = 600
HOLDERS = "holders"
SLOT = re.compile(r"slot-([0-9]+)\.lock")
DECL = re.compile(r"^並行の検査:[ \t]*(.*?)[ \t]*$")
NEWLINE = re.compile(r"\r\n|\r|\n")
DIGITS = re.compile(r"[0-9]{1,6}")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
COMMENT_BLOCK = re.compile(r"(?: {0,3}(?:[-*+]|[0-9]{1,9}[.)])[ \t]+| {0,3}>[ \t]?)* {0,3}<!--")  # 行頭（空白 3 つまで・リストや引用の印の直後）で始まるコメント。それ以外は段落の中のコメント（#758）


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
    """コードブロックの閉じ行か（CommonMark）: 字下げは空白 3 つまで（タブは 4 桁に数えるので、タブの字下げでは閉じない）、
    開いた印と同じ文字を同じ数以上、後ろには空白とタブだけ（全角の空白などは置けない）。"""
    body = line.lstrip(" ")
    if len(line) - len(body) > 3:
        return False
    run = len(body) - len(body.lstrip(char))
    return run >= width and not body[run:].strip(" \t")


def opens(line: str) -> tuple[str, int] | None:
    """コードブロックの開き行か（CommonMark）。開くなら (印の文字, 数)。バッククォートの印の後ろ（情報文字列）にバッククォートがあれば開かない。"""
    opened = FENCE.match(line)
    if not opened:
        return None
    mark = opened.group(1)
    if mark[0] == "`" and "`" in line[opened.end():]:
        return None
    return mark[0], len(mark)


def declared_lines(text: str) -> list[str]:
    """コードブロックと HTML コメントの外の行。先頭の BOM は 1 つだけ外す。

    コードブロックは、開いた印（` ``` `・`~~~` を 3 つ以上）と同じ文字で、同じ数以上だけの行で閉じる（CommonMark の規則。`closes`・`opens`）。
    行は改行（`\n`・`\r\n`・`\r`）でだけ分ける——`str.splitlines` は `\x0b`・`\x0c`・`\u2028` などでも分けるので使わない。
    HTML コメントは、コメントの外で始まった行のどこで始まっても、閉じるまで（行をまたいでも）外す。ただし
    コードブロックの開き行はコメントを探さない（行の後ろの `<!--` は情報文字列）。段落の中で始まって閉じないコメントは、
    コードブロックの開き行で終わる——CommonMark ではコードブロックが段落を割り込む。段落の中かは、コメントの外で始まった行なら
    行頭（リストや引用の印の直後を含む。`COMMENT_BLOCK`）で始まるかで、コメントの中で始まった行で開き直したなら、その行のコメントを継ぐ。"""
    lines: list[str] = []
    fence: tuple[str, int] | None = None
    comment = inline = False
    for line in NEWLINE.split(text.removeprefix("\ufeff")):
        if fence:
            char, width = fence
            if closes(line, char, width):
                fence = None
            continue
        # 開き行は元の行で見る（コメントの外で始まった行と、段落の中のコメントの後ろの行）——コメントを外した残りで見ると、
        # `<!-- -->```` を行頭の印と読み、`` ```a<!--`--> `` の情報文字列のバッククォートを見落とす。開いた行はコメントを探さない
        # ——行の後ろの `<!--` は情報文字列。段落の中のコメントは、開き行で終わる（コードブロックが段落を割り込む）
        opened = None if comment and not inline else opens(line)
        if opened:
            fence, comment = opened, False
            continue
        kept, rest, started = "", line, comment
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
                    # 行の途中で開き直したコメントは、その行が始まったときのコメントの種類を継ぐ（`-->` で閉じた行頭のコメントの残りは
                    # まだ行頭のコメント——GitHub は `<!--\n--> x <!--` の後ろを隠す）。コメントの外で始まった行だけ、行頭かで決める
                    inline = inline if started else not COMMENT_BLOCK.match(line)
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


def span(seconds: float) -> str:
    """秒数を「N 分 M 秒」で言う。"""
    whole = max(0, int(seconds))
    return f"{whole // 60} 分 {whole % 60} 秒" if whole >= 60 else f"{whole} 秒"


def last_output(info: dict, now: float) -> tuple[float | None, str]:
    """持ち主の出力の最終更新。(時刻, 言うこと)。分からなければ時刻は None。

    記録の `outputs`（持ち主の標準出力・標準エラーのうち通常のファイル）を `stat` し、同じファイル（`st_dev`・`st_ino`）の `st_mtime` の新しいほう。"""
    outputs = info.get("outputs")
    if not isinstance(outputs, list):
        return None, "出力の最終更新は分からない（記録に出力のファイルが無い——古い版の run-serial）"
    if not outputs:
        return None, "出力の最終更新は分からない（出力がファイルでない——パイプ・端末など）"
    times, paths = [], []
    for out in outputs:
        try:
            st = os.stat(out["path"])
        except (OSError, KeyError, TypeError, ValueError):
            continue
        if (st.st_dev, st.st_ino) == (out.get("dev"), out.get("ino")):
            times.append(st.st_mtime)
            paths.append(str(out["path"]))
    if not times:
        return None, "出力の最終更新は分からない（出力のファイルが消えた・置き換わった）"
    newest = max(times)
    return newest, f"出力の最終更新 {span(now - newest)} 前（{', '.join(paths)}）"


def describe(info: dict, now: float) -> str:
    """持ち主 1 つを 1 行で: pid・場所・コマンド・経過・出力の最終更新。出力が `STALL` 秒以上増えていなければ「止まっている疑い」。"""
    parts = [f"pid {info.get('pid')}", str(info.get("cwd")), str(info.get("command"))]
    started = info.get("started")
    try:
        begun = datetime.strptime(started, "%Y-%m-%dT%H:%M:%S%z").timestamp()
    except (TypeError, ValueError):
        parts.append(f"経過は分からない（始めた時刻 {started!r} が読めない）")
    else:
        parts.append(f"経過 {span(now - begun)}（{started} から）")
    updated, said = last_output(info, now)
    parts.append(said)
    line = "・".join(parts)
    if updated is not None and now - updated >= STALL:
        line += f"——止まっている疑い（出力が {span(STALL)} 以上増えていない）"
    return line


def slot_files(lockdir: Path) -> list[Path]:
    """枠のディレクトリの `slot-<k>.lock` を k の順に（宣言の本数に依らない——減らす前の枠で走っているものも見える）。"""
    try:
        names = os.listdir(lockdir)
    except OSError:
        return []
    found = [(int(m.group(1)), lockdir / name) for name in names if (m := SLOT.fullmatch(name))]
    return [path for _, path in sorted(found)]


def holders(lockdir: Path) -> list[str]:
    """いま走っているもの（枠の持ち主）を 1 つ 1 行で。記録の pid が居ないもの（走り終えて記録だけ残ったもの）は出さない。読むだけで、何も書かない。"""
    now = time.time()
    found = []
    for path in slot_files(lockdir):
        try:
            info = json.loads(path.read_text(encoding="utf-8") or "{}")
        except (OSError, ValueError):
            continue
        if not isinstance(info, dict) or not info:
            continue
        pid = info.get("pid")
        if type(pid) is not int or pid <= 0 or not alive(pid):
            continue
        found.append(describe(info, now))
    return found


def show_holders() -> int:
    """`holders` の口: 持ち主を標準出力に 1 回だけ出して終わる。枠を取らず、枠のディレクトリを作らない。"""
    common = common_dir(Path.cwd())
    if common is None:
        say("枠を決められない（git の共通ディレクトリが決まらない）")
        return CANNOT
    running = holders(common / "dev-loop-serial")
    print("\n".join(running) if running else "走っているものは無い", flush=True)
    return 0


def acquire(lockdir: Path, slots: int, parent: int) -> int | None:
    """枠を 1 つ取って fd を返す。取れるまで待つ。待っているあいだに起動したときの親（`parent`）が居なくなったら、取らずに None。"""
    waited = reported = None
    while True:
        if os.getppid() != parent:
            say(f"呼び出し元（pid {parent}）が居なくなった——枠を取らずに終わる（走らせていない）")
            return None
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
        now = time.monotonic()
        if waited is None or now - reported >= REPORT:
            if waited is None:
                waited, head = now, f"待っている（同じリポジトリで同時に {slots} 本まで）。走っているもの:"
            else:
                head = f"まだ待っている（{span(now - waited)}）。走っているもの:"
            reported = now
            running = holders(lockdir)
            say(head + ("" if running else " （読めなかった）"))
            for line in running:
                say(f"  {line}")
        time.sleep(POLL)


def fd_path(fd: int) -> str | None:
    """開いているファイルのパス（macOS は `F_GETPATH`、Linux は `/proc/self/fd`）。取れなければ None。"""
    getpath = getattr(fcntl, "F_GETPATH", None)
    try:
        if getpath is not None:
            return os.fsdecode(fcntl.fcntl(fd, getpath, bytes(1024)).split(b"\0", 1)[0]) or None
        return os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        return None


def output_files() -> list[dict]:
    """自分の標準出力・標準エラー（コマンドが継ぐ）のうち、通常のファイルのもの。パス・`st_dev`・`st_ino`。"""
    found: list[dict] = []
    for fd in (1, 2):
        try:
            st = os.fstat(fd)
        except OSError:
            continue
        if not stat.S_ISREG(st.st_mode) or any((o["dev"], o["ino"]) == (st.st_dev, st.st_ino) for o in found):
            continue
        path = fd_path(fd)
        try:
            same = os.stat(path) if path else None
        except OSError:
            same = None
        if same is not None and (same.st_dev, same.st_ino) == (st.st_dev, st.st_ino):
            found.append({"path": path, "dev": st.st_dev, "ino": st.st_ino})
    return found


def record(fd: int, command: list[str]) -> None:
    info = {"pid": os.getpid(), "cwd": os.getcwd(), "command": " ".join(command),
            "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "outputs": output_files()}
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, json.dumps(info, ensure_ascii=False).encode("utf-8"))


def descendants(*roots: int) -> list[int] | None:
    """`roots` の子孫の pid（`ps` の親子をたどる）。`ps` が使えなければ None。"""
    try:
        proc = subprocess.run(["ps", "-A", "-o", "pid=", "-o", "ppid="], capture_output=True, text=True, check=False)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    children: dict[int, list[int]] = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            children.setdefault(int(parts[1]), []).append(int(parts[0]))
    found, stack = [], list(roots)
    while stack:
        for child in children.get(stack.pop(), []):
            if child not in found:
                found.append(child)
                stack.append(child)
    return found


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def signal_all(pids: list[int], signum: int) -> None:
    for pid in pids:
        try:
            os.kill(pid, signum)
        except (ProcessLookupError, PermissionError):
            pass


def stop(proc: subprocess.Popen) -> None:
    """期限切れのコマンドとその子孫を止める。SIGTERM を送り、`GRACE` 秒待って残るものに SIGKILL を送る。

    子孫は先に数えておく——コマンドが先に終わると、子孫は親を離れて（init に移って）たどれなくなる。"""
    tree = descendants(proc.pid)
    if tree is None:
        say("子孫を数えられない（`ps` が使えない）——コマンドだけを止める")
        tree = []
    targets = [proc.pid, *tree]
    signal_all(targets, signal.SIGTERM)
    end = time.monotonic() + GRACE
    while time.monotonic() < end:
        if proc.poll() is not None and not any(alive(pid) for pid in tree):
            break
        time.sleep(0.05)
    # 猶予のあいだに生まれた子孫も数え直す——コマンドが先に終わっていても、まだ生きている子孫（SIGTERM で子を起こす孫など）からたどる
    living = [pid for pid in targets if (pid == proc.pid and proc.poll() is None) or (pid != proc.pid and alive(pid))]
    targets += [pid for pid in (descendants(*living) if living else []) or [] if pid not in targets]
    left = [pid for pid in targets if (pid == proc.pid and proc.poll() is None) or (pid != proc.pid and alive(pid))]
    if left:
        say(f"SIGTERM の後 {GRACE:.0f} 秒で終わらなかった pid {', '.join(map(str, left))} を SIGKILL で止める")
        signal_all(left, signal.SIGKILL)
    proc.wait()


def run(command: list[str], env: dict[str, str], timeout: int) -> int:
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

    def hold(_signum, _frame):
        """SIGINT は渡さない——端末の Ctrl-C はプロセスグループ全体に届き、コマンドも直接受け取るので、渡すと 2 度になる（#739）。
        受けても終わらずに待つ（枠を持ったまま）。"""

    previous = {s: signal.signal(s, forward) for s in (signal.SIGTERM, signal.SIGHUP)}
    previous[signal.SIGINT] = signal.signal(signal.SIGINT, hold)
    try:
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            say(f"期限切れ（{timeout} 秒を過ぎた）——コマンドとその子孫を止めて、枠を返す。走りきっていない")
            stop(proc)
            return TIMED_OUT
    finally:
        for s, handler in previous.items():
            signal.signal(s, handler)
    return 128 - code if code < 0 else code


def options(argv: list[str]) -> tuple[list[str], int] | None:
    """(コマンド, 期限の秒数)。使い方に合わなければ言って None。"""
    usage = "使い方: run-serial.py [--timeout <秒>] -- <コマンド> [引数 …]（持ち主を出すだけなら run-serial.py holders）"
    if "--" not in argv or not argv[argv.index("--") + 1:]:
        say(usage)
        return None
    head, command = argv[:argv.index("--")], argv[argv.index("--") + 1:]
    timeout = DEFAULT_TIMEOUT
    while head:
        arg = head.pop(0)
        if arg == "--timeout" and head:
            value = head.pop(0)
        elif arg.startswith("--timeout="):
            value = arg.split("=", 1)[1]
        elif arg == "--timeout":
            say(f"`--timeout` に値が無い——{usage}")
            return None
        else:
            say(f"知らない引数 {arg!r}——{usage}")
            return None
        if not TIMEOUT_VALUE.fullmatch(value) or int(value) < 1:
            say(f"`--timeout` の値 {value!r} は 1 以上の整数（7 桁まで）でない——走らせていない")
            return None
        timeout = int(value)
    return command, timeout


def main(argv: list[str]) -> int:
    parent = os.getppid()
    if argv[:1] == [HOLDERS]:
        if argv[1:]:
            say(f"`{HOLDERS}` は引数を取らない（{argv[1]!r}）——使い方: run-serial.py holders")
            return USAGE
        return show_holders()
    parsed = options(argv)
    if parsed is None:
        return USAGE
    command, timeout = parsed

    common = common_dir(Path.cwd())
    if common is None:
        say("枠を決められない（git の共通ディレクトリが決まらない）——走らせていない")
        return CANNOT
    lockdir = common / "dev-loop-serial"

    env = dict(os.environ)
    if os.environ.get(ENV) == str(lockdir):
        return run(command, env, timeout)

    text, unreadable = declaration(common)
    if unreadable:
        say(unreadable)
    slots, note = slots_from(text)
    if note:
        say(note)
    try:
        lockdir.mkdir(exist_ok=True)
        fd = acquire(lockdir, slots, parent)
        if fd is None:
            return CANNOT
        record(fd, command)
    except OSError as exc:
        say(f"枠を決められない（{exc}）——走らせていない")
        return CANNOT
    env[ENV] = str(lockdir)
    try:
        return run(command, env, timeout)
    finally:
        os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
