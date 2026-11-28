#!/usr/bin/env python3
r"""TLC（TLA+ のモデル検査器）が、正本リポジトリの `CLAUDE.md` に書いた呼び方で使えるかを確かめる（#912）。

    python3 <spec-loop の根>/scripts/check-tlc.py <正本リポジトリの根> [--autopilot]

**読むだけ**——正本リポジトリにも設定にも書かない。モデルは一時ディレクトリに書いて走らせ、終わったら消す。

## なぜ在るのか（#912）

業務フロー（並行・リトライ・取り消し）を形式検査の対象に選んだのに TLC が無いと、spec-review は判定役を 1 体も起動せず、
用意してから呼び直すか、用意せずに進める（業務フローは判定できなかったになり、その回は抜けない）かを訊く。
TLC はふつう `tla2tools.jar` で入れるので `command -v` では見つからず（#368 の残課題 CR4）、入っているのに「無い」として止まりえた。
**TLC は spec-loop の既定で必須の前提**であり（README の「前提」）、**呼び方は正本の `CLAUDE.md` に書く**。
spec-review の確かめ（手順 3）と autopilot の起動時の点検はこのスクリプトで確かめ、Formal Checker は同じ呼び方を使う。

## 正本の `CLAUDE.md` に書く行

**正本リポジトリの根の `CLAUDE.md` に、行頭から 1 行ずつ書く**（このスクリプトがここを原本として読む。README・スキルはここを指す）:

| 行 | 意味 |
| --- | --- |
| `TLC の呼び方: <コマンド>` | TLC を起動するコマンド。**後ろにモデルのファイル（`<名前>.tla`。設定は同じ名前の `.cfg`）を足し、モデルのディレクトリで `sh` に渡す**。例: `TLC の呼び方: java -cp /opt/tla/tla2tools.jar tlc2.TLC` |
| `業務フローの形式検査: しない` | 業務フローを一度も形式検査しない案件が、TLC を必須から外す宣言。値は `しない` だけ |

- **コードフェンス（` ``` `・`~~~`）の中の行は読まない**——例として書いた行を宣言と読まない。フェンスの開け閉めは CommonMark のとおり
  （同じ文字の 3 つ以上で開き、同じ文字で、開きと同じか長い、info string の無い行で閉じる。4 つのバッククォートの中の 3 つは閉じない）。
- **先頭の BOM は外して読む。**
- **コロンは半角（`:`）でも全角（`：`）でもよい**——日本語の入力で全角になりやすい。
- **同じ行を 2 行以上書かない・外す宣言の値は `しない` だけ・呼び方を空にしない**——どれも「判定できない」（4）。
- **外す宣言が古くなっても（後の版で業務フローを対象に選んだ）守らせる仕組みは無い**——spec-review が対象を選んだときに
  このスクリプトを（`--autopilot` なしで）呼び、TLC が無ければ今のとおり判定役を起動せずに訊く。

### 呼び方に足すオプション（重いモデル。#1339）

呼び方の行は、このスクリプト・Formal Checker・`check-formal-rerun.py`・`formal-statechart.py`・dev-loop の `formal-sync.py`（`check-formal-rerun.py` を読み込んで、対象ごとに保存したモデルとコードのモデルを走らせる）が**同じ 1 行を共有する**。モデルが重いときに足してよいものと、足すと何が変わるか:

| 足すもの | 書く場所 | 変わること |
| --- | --- | --- |
| `-XX:+UseParallelGC`・`-Xmx<量>`（ヒープ） | `java` と `-cp` の間 | 速さとメモリのためのもの。手元の TLC 2.19 で、`-Xmx2g -fpmem 0.5` を足した 3 回は反例のトレースと状態数が足さない回と同じだった——**ただし 356 状態の小さいモデルで、メモリが足りなくなる大きさではない**（大きいモデルで結果が変わらないことは確かめていない）。`-XX:+UseParallelGC` は足さない形と比べていない |
| `-fpmem <割合>`（TLC のヘルプでは「探索済みの状態の指紋に回す、物理メモリに対する割合」。0.0 と 1.0 の間。既定 0.25） | `tlc2.TLC` の後ろ | 同上。**`-Xmx` と合わせて物理メモリを超えないようにする**——指紋の分がヒープの外なら、両方の和が物理メモリを超えうる（ヒープの内か外かは確かめていない） |
| `-workers <数>` か `-workers auto` | `tlc2.TLC` の後ろ | **書かなくてよい**——ワーカーの数は、スクリプトと Formal Checker が検査の種類ごとに後ろに足す（下の「ワーカーの数と指紋」。#1602）。書いたら、判定だけが要る検査はその値で走り、反例の経路・状態グラフが要る検査は `-workers 1` で上書きされる |

#1339 の測り方（上の表と、下の「ワーカーの数と指紋」の #1339 の行）: **確かめたのはこの 1 つのモデル・この機械（28 コア）・各 3〜8 回だけ**——ほかの形で反例が最短でなくなるかは確かめていない。
状態グラフ（`-dump dot,actionlabels`）は、TLC が指紋の多項式を回ごとに選ぶので、`-fp 0` で固定して比べた——違反のある 2 つの小さいモデル（24・25 本の遷移）を `-continue` つきで
`-workers 1` と `-workers 8` で 6〜8 回ずつ走らせ、どれも同じ中身だった。**大きいモデルや別の形で辺が欠けないことは確かめていない**（別の形で欠けたという報告がある——#1339 の PR）。
**モデルそのものを軽くする手（構成を小さくする・`CONSTRAINT`・抽象化）と、使わない手（SYMMETRY・VIEW・`-simulate`）は Formal Checker の「検査が重いとき」を正とする**（プラグイン直下の `agents/formal-checker.md`）。

### ワーカーの数と指紋（#1602。ここが原本）

**TLC は既定で 1 ワーカーで走る**（#1602 の実案件で `with 1 worker on 15 cores`。`PROPERTY` を持つ本体が、1 ワーカーで 44 秒・`-workers auto` で 6 秒だった——Issue の実測）。
呼び方の行に `-workers` を書かせると、利用者は反例のトレースが揺れるのを嫌って書かないか、書くことに気づかない。そこで**呼び方の行はそのままにして、走らせる側が検査の種類ごとに後ろに足す**:

| 検査 | 結果に要るもの | 足すもの（呼び方の後ろ・モデルのファイルの前） |
| --- | --- | --- |
| 本体・陽性対照・到達の確かめ（`check-formal-rerun.py`・それを読み込む dev-loop の `formal-sync.py`・正本の CI・Formal Checker） | 判定と状態数 | `for_verdict`——呼び方に `-workers` の語が無ければ `-workers auto`。**有れば足さない**（利用者が CPU を絞るために書いた値を使う） |
| 本体の反例のトレース（Formal Checker が反例を取り直す回の `トレース` と `-dumpTrace json`）・状態グラフ（`formal-statechart.py` と Formal Checker の図の対応の `-dump`） | 経路・グラフ | `for_trace`——**呼び方に何があっても** `-workers 1 -fp 0` |
| この CLI の確かめ（2 つの小さいモデル） | 呼び方が通るか | 足さない（呼び方の行のまま） |

`check-formal-rerun.py` は反例を取り直さない——判定だけを出し、反例の行（出力の終わり）は複数ワーカーの回のものである（回ごとに変わりうる）。

- **#1339 の行**: 手元の TLC 2.19 で、最短の反例が多数あるモデルを 8 回ずつ走らせ、`-workers 1` は 8 回とも同じトレース、`-workers 8` は 5 種類（長さはどれも同じ）だった——Formal Checker の `トレース`（Red テストになる）と `formal-statechart.py` の最初の反例の経路が回ごとに揺れるので、経路の要る検査は 1 ワーカーにする。
- **後ろに足した値が使われる**——手元の TLC 2.19（tla2tools v1.7.4）で、`-workers auto -workers 1` は 1 worker、`-workers 1 -workers auto` は 28 workers、`-workers 1 -workers 3` は 3 workers、
  `-fp 5 -fp 0` は fp 0、`-fp 0 -fp 5` は fp 5 で走った（2026-11-28。出力の `with <n> worker(s)`・`with fp <n>` の行）。
- **`-fp 0` も足すのは、時相の性質の反例（lasso）が 1 ワーカーでも回ごとに変わるから**——TLC は指紋の多項式を回ごとに選ぶ（`with fp <n> and seed …` の行）。手元の TLC 2.19 で、時相の性質を破るモデル（6,561 状態）を
  1 ワーカーで 3 回走らせると 3 回とも違うトレース（状態の並び）で、`-fp 0` を足すと 3 回とも同じだった（`-workers auto -fp 0` は 3 回で 2 種類）。
  不変条件の反例（幅優先で最短）は 1 ワーカーなら `-fp` を足さなくても 3 回とも同じで、`-workers auto` は 3 回とも違った（331 状態の小さいモデル。最短の反例が多数ある形）。
- **判定と、状態空間を全部たどった回（反例で止まらない回）の状態数は、ワーカーの数で変わらなかった**——同じ機械で各 3 回: `PROPERTY` を持ち反例の無いモデル（456,976 状態）は 1 ワーカーも `-workers auto`（28）もどれも `No error has been found`・456,976 状態、
  時相の性質を破るモデル（陽性対照）はどれも `Temporal properties were violated.`・6,561 状態、不変条件を破るモデル（陽性対照）はどれも `is violated`。
  **反例で止まった回の状態数はワーカーの数で変わる**（不変条件の反例で 1 ワーカーは 3 回とも 331、`-workers auto` は 216・296・280——最初の違反で止まるまでにたどった数）。判定と終了コードには使わない（`check-formal-rerun.py` の重さの注記）。
- **確かめたのは TLC 2.19・この機械（28 コア）・小さいモデル 3 つ・各 3 回だけ**——ほかの版・大きいモデルで後の値が使われること・1 ワーカーと `-fp 0` でトレースが揺れないことは確かめていない。

## 確かめ方

呼び方で 2 つの小さいモデルを一時ディレクトリで検査させる:

1. **通るモデル**——終了コードが 0 で、出力に `No error has been found` が出れば通った。
2. **違反するモデル（陽性対照）**——出力に `is violated` が出れば通った（終了コードは見ない）。
   **何にでも「エラーなし」と言う呼び方を「在る」と読まない**ためである。

**`command -v` では探さない**——呼び方の行が無ければ、`PATH` に `tlc` が在っても「無い」（1）。探し方を呼び方の 1 つに揃えるためである。

- **`--autopilot` なし**（spec-review の手順 3。業務フローを対象に選んだときに呼ぶ）: 外す宣言が有っても呼び方を確かめる（宣言が古いと出す）。
- **`--autopilot`**（autopilot が Formal Checker を起こす段の始め）: 外す宣言が有れば確かめずに 0（呼び方を走らせない）。無ければ確かめる。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 呼び方が通った（`--autopilot` では、外す宣言が有って確かめなかったときも） |
| 1 | TLC が無い——呼び方の行が無い（`CLAUDE.md` が無いを含む）か、呼び方が通らない（時間切れを含む） |
| 2 | 引数が違う |
| 4 | 判定できなかった——`CLAUDE.md` を読めない、同じ宣言が 2 行以上、外す宣言の値が `しない` でない、呼び方が空 |

## 一時ディレクトリと信号の部品（#1600）

`check-formal-rerun.py`・`check-alloy.py` が読み込んで使う（**ここが原本**。`formal-statechart.py` は #1594 の同じ形の写しを自前で持つ）。
検査器を一時ディレクトリで走らせるスクリプトが、止められても `$TMPDIR` に一時ディレクトリと検査器（java）を残さないための部品である。このスクリプトの CLI（`probe`）は使わない。

- **名前**: `owned_dir(<頭>)` は `<頭><pid>-<乱字 8 文字>` の一時ディレクトリを作る（`tempfile.TemporaryDirectory`。抜けたら消す）。
- **信号**: `catch_signals(current_signals() の値)` は SIGTERM・SIGINT・SIGHUP を例外 `Interrupted`（`BaseException` の子——途中の `except Exception` に呑ませず、`with` の片付けまで上げる）にする。
  **親が無視にした信号は無視のまま**（`nohup` の SIGHUP・`&` の SIGINT）。1 回目を受けたら全部を無視にする（片付けの途中で止めない）。`restore_signals()` で入れる前に戻す。
  入れるのは呼ぶ側の `try` の中で（入れた直後の信号を `try` の外で上げない）。`restore_signals` は戻す途中の信号を待たせ、戻した後の扱いで受ける。
  **`restore_signals` の入口（待たせる前）に届いた 1 回目は `Interrupted` として呼ぶ側の `finally` から上がる**——呼ぶ側はもう 1 つ外の `try` で受け、片付けて `restore_signals` を呼び直す（1 回目の後は全部を無視にしているので、呼び直しは止まらない）。
  止められたことを言う 1 行は `say` で書く——標準エラーが書けなくても（SIGHUP の後の閉じた端末）128+信号の終了コードを変えない。
  例外が `run_model` の待ちの中で起きれば、`run_model` が検査器のプロセスグループを止めてから上げる（時間切れの枝で止める前に届いた信号でも、`finally` で止める）。`run_model` は起こしてから止められる所に入るまで（`Popen` の中を含む）信号を待たせ、検査器には待たせた分を引き継がない。
- **消し直し**: `sweep(<頭>)` は自分の pid の `<頭><pid>-*` を消す——片付け（`TemporaryDirectory` の削除）の途中に届いた信号で、削除が途切れていることがある。
- **回収**: `reclaim(<頭>)` は、名前が `<頭><pid>-<乱字 8 文字>` の形どおりで、その pid のプロセスが居ないもの（SIGKILL で片付けが走らなかった残り）を消す。
  その中に `record_group` で記録した検査器のプロセスグループ（`GROUP_FILE`）がまだ居れば・記録が読めなければ、消さずに返す（`reclaim_lines` が言う行を作る）。

| 守ること | 破る形 |
| --- | --- |
| 回収は、名前が形どおり（pid は先頭が 0 でない半角の 10 進・乱字は英小文字・数字・`_` のちょうど 8 文字・後ろに余分が無い）で、持ち主の pid が居ないものだけ | 並行する実行の作業中のディレクトリ・ほかの頭のもの・pid の無い古い名前・手で作った名前を消す |
| 持ち主が居るか分からない（権限）pid は居るほうに倒す | 別の利用者の実行のディレクトリを消す |
| 記録した検査器のグループがまだ居れば・記録が読めなければ（権限・ASCII でない・数字でない・0 以下）消さない | 走り続ける検査器の書くファイルを見えなくして「消した」と言う |
| 親が無視にした信号は無視のまま、ほかは `Interrupted` にし、1 回目の後は全部を無視する | `nohup` で起こした実行が端末を閉じただけで止まる・片付けの途中の 2 回目で止まる |
| `restore_signals` で入れる前の扱いに戻し、戻す途中の信号は戻した後の扱いで受ける | 同じプロセスで呼んだ後も、信号が例外のまま残る・戻す途中の信号が捕まえられずに 1 で終わる |
| `run_model` は、起こしてから止められる所に入るまで（`Popen` の中を含む）信号を待たせ、検査器には待たせた分を引き継がない | 起こした直後に届いた信号で、検査器を止めずに抜ける・検査器が SIGTERM を受けられない |
| `run_model` は、時間切れ・例外の枝の途中に届いた信号でも、抜ける前に検査器のプロセスグループを止める | 時間切れの直後（止める前）に届いた信号で、検査器を止めずに抜ける |
| `say` は、標準エラーが書けなくても例外を上げず、終わるときの書き出しも失敗させない | SIGHUP の後に端末が閉じていると、128+信号ではなく 120 で終わる |

## 何を守り、何を守らないか

守る:

- **呼び方の行が無い正本を 0 にしない**——`--autopilot` でも、外す宣言が無ければ 1。
- **通るモデルを通さない呼び方を 0 にしない**——終了コードが 0 でないか、`No error has been found` が出なければ 1。
- **違反するモデルで違反を出さない呼び方を 0 にしない**——何にでも「エラーなし」と言う呼び方は 1（陽性対照）。
- **`command -v` で探さない**——呼び方の行が無ければ、`PATH` に `tlc` が在っても 1。
- **コードフェンスの中の行を宣言と読まない。**
- **フェンスを閉じるのは、同じ文字で開きと同じか長い、info string の無い行だけ**——4 つのバッククォートの中の 3 つや、` ```bash ` の行で閉じない。
- **先頭の BOM を外して読む**——BOM つきで保存した `CLAUDE.md` の 1 行目の宣言を落とさない。
- **全角のコロンの行も読む**——`TLC の呼び方：`・`業務フローの形式検査：` を「行が無い」と読まない。
- **同じ宣言が 2 行以上なら 4**——どれを使うかを決めない。
- **外す宣言の値が `しない` でなければ 4**——近い値（`無し`・`しない（v2 から）`）で外さない。
- **`--autopilot` で外す宣言が有れば、呼び方を走らせずに 0。**
- **`--autopilot` が無ければ、外す宣言が有っても呼び方を確かめる**——spec-review は対象を選んだときに呼ぶ。
- **読めない `CLAUDE.md` を「書いていない」と読まない**——4。
- **時間切れで待ち続けない**——1 回の検査を `PROBE_TIMEOUT` 秒で止め（プロセスグループごと）、1。
- **正本リポジトリに書かない**——モデルは一時ディレクトリに書いて、そこで走らせる。
- **判定だけが要る検査の呼び方は、呼び方に `-workers` が無ければ後ろに `-workers auto` を足す**（`for_verdict`）——利用者の設定なしで 1 ワーカーに落ちない。
- **呼び方に `-workers` の語があれば、判定だけが要る検査に足さない**（`for_verdict`）——利用者の値を上書きしない。
- **トレース・状態グラフが要る検査の呼び方は、呼び方に何があっても後ろに `-workers 1 -fp 0` を足す**（`for_trace`）——呼び方の `-workers auto` で経路が揺れない。

守らない:

- **HTML コメント（`<!-- -->`）の中の行も読む**——コメントで消した宣言を消えたと読まない。
- **TLC の版による出力の違い**——判定に使う 2 つの文字列（`No error has been found`・`is violated`）と 2 つのモデルは、
  TLC 2.19（`tla2tools.jar` v1.7.4）で確かめた（#912 の周。モデルが通り、違反するモデルで `Error: Invariant Inv is violated.` と終了コード 12）。
  ほかの版は確かめていない。**回帰テストは偽の TLC で当てる**ので、モデルの中身（TLC が意味解析で落とす書き方）はテストでは見えない。
- **呼び方が、Formal Checker が書く大きいモデルを検査できるか**（メモリ・時間・モジュール）——小さいモデル 2 つを検査できることだけを見る。
- **呼び方の安全**——正本の `CLAUDE.md` に書いた文字列をそのまま `sh` で走らせる（正本の `CLAUDE.md` は利用者が書くもので、Formal Checker も同じ文字列を走らせる）。
- **子孫のプロセスが自分で別のプロセスグループに移ったとき**——時間切れで止めるのはプロセスグループまで。
- **Alloy**——#912 の範囲の外。
"""

import argparse
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

# CommonMark のコードフェンス: 字下げ 3 つまで・同じ文字（` か ~）が 3 つ以上・後ろは info string
FENCE_RE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
CALL_KEY = "TLC の呼び方:"
OPT_OUT_KEY = "業務フローの形式検査:"
OPT_OUT_VALUE = "しない"
PROBE_TIMEOUT = 120

# 標準モジュール（Naturals など）を EXTENDS しない形にする——算術の `-` は Naturals が無いと意味解析で落ちる（本物の TLC 2.19 で確かめた）
GOOD_MODEL = ("Probe", "---- MODULE Probe ----\nVARIABLE x\nInit == x = FALSE\nNext == x' = ~x\nInv == x \\in BOOLEAN\n====\n")
BROKEN_MODEL = ("Broken", "---- MODULE Broken ----\nVARIABLE x\nInit == x = FALSE\nNext == x' = ~x\nInv == x = FALSE\n====\n")
MODEL_CFG = "INIT Init\nNEXT Next\nINVARIANT Inv\n"
GOOD_MARK = "No error has been found"
BROKEN_MARK = "is violated"

# ワーカーの数（#1602。docstring の「ワーカーの数と指紋」）——判定だけが要る検査は複数、反例の経路・状態グラフが要る検査は 1 で指紋も固定
WORKERS_OPTION = "-workers"
VERDICT_WORKERS = "auto"
TRACE_WORKERS = "1"
FP_OPTION = "-fp"
TRACE_FP = "0"

EXIT_OK = 0
EXIT_MISSING = 1
EXIT_USAGE = 2
EXIT_UNKNOWN = 4


class Unknown(Exception):
    """判定できなかった（4）。"""


def read_declarations(root):
    """正本の `CLAUDE.md` の宣言。(呼び方 or None, 外すか, 注記)。`CLAUDE.md` が無ければ (None, False, 注記)。"""
    path = Path(root) / "CLAUDE.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None, False, f"{path} が無い"
    except (OSError, ValueError) as e:
        raise Unknown(f"{path} を読めない: {e}")
    text = text.removeprefix("\ufeff")
    found = scan_declarations(text, (CALL_KEY, OPT_OUT_KEY))
    calls, opt_outs = found[CALL_KEY], found[OPT_OUT_KEY]
    if len(calls) > 1:
        raise Unknown(f"`{CALL_KEY}` の行が {len(calls)} 行ある（どれを使うか決めない）")
    if len(opt_outs) > 1:
        raise Unknown(f"`{OPT_OUT_KEY}` の行が {len(opt_outs)} 行ある")
    if opt_outs and opt_outs[0] != OPT_OUT_VALUE:
        raise Unknown(f"`{OPT_OUT_KEY}` の値が `{OPT_OUT_VALUE}` でない: {opt_outs[0]!r}")
    if calls and not calls[0]:
        raise Unknown(f"`{CALL_KEY}` の呼び方が空")
    note = "" if calls else f"{path} に `{CALL_KEY}` の行が無い"
    return (calls[0] if calls else None), bool(opt_outs), note


def scan_declarations(text, keys):
    """コードフェンスの外で、行頭が `keys` のどれか（コロンは半角か全角）の行の後ろ。{鍵: [値（前後の空白を外す）…]}。

    `check-alloy.py` もこれで読む（写さない。#922）。
    """
    found = {key: [] for key in keys}
    fence = None  # 開いているフェンスの (文字, 長さ)
    for line in text.splitlines():
        m = FENCE_RE.fullmatch(line)
        if fence is None:
            # バッククォートのフェンスの info string にバッククォートは置けない（CommonMark）
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence = (m.group(1)[0], len(m.group(1)))
                continue
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and not m.group(2).strip():
                fence = None
            continue
        for key in keys:
            value = after_key(line, key)
            if value is not None:
                found[key].append(value.strip())
                break
    return found


def after_key(line, key):
    """行頭が `key`（コロンは半角か全角）なら、その後ろ。違えば None。"""
    for k in (key, key[:-1] + "："):
        if line.startswith(k):
            return line[len(k):]
    return None


def run_model(call, workdir, name, timeout, started=None):
    """呼び方でモデル 1 つを検査させる。(終了コード or None（時間切れ・起動できない）, 出力)。
    `started` があれば、起こした直後にそのプロセス（別のセッションのリーダー。pid がプロセスグループの番号）を渡して呼ぶ。"""
    # 起こしてから止められる所（下の try）に入るまで——Popen の中を含む——に届いた信号を待たせる（#1600）。子には待たせた分を引き継がない
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)
    try:
        proc = subprocess.Popen(["/bin/sh", "-c", f"{call} {name}.tla"], cwd=workdir, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, errors="replace",
                                start_new_session=True, preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, mask))
    except BaseException as e:
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        if isinstance(e, OSError):
            return None, f"起動できない: {e}"
        raise
    try:
        if started is not None:
            started(proc)
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)  # 待たせた信号はここで届き、下の枝で検査器を止める
        out, _ = proc.communicate(timeout=timeout)
        return proc.returncode, out
    except subprocess.TimeoutExpired:
        with_group(proc, signal.SIGKILL)
        out, _ = proc.communicate()
        return None, (out or "") + f"\n（{timeout} 秒で時間切れ）"
    finally:
        # 待っている間の例外（信号を例外にした呼び出し元の formal-statechart.py・Ctrl-C。#1594）でも、時間切れの枝で止める前に届いた信号（#1600 の 2 パス目）でも、
        # 別のセッションで起こした TLC を置き去りにしない——枝の中で上がった例外は兄弟の except に入らないので、finally で止める
        if proc.returncode is None:
            with_group(proc, signal.SIGKILL)
            proc.wait()
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)  # started が上げた例外の枝でも解く


def with_group(proc, sig):
    try:
        os.killpg(proc.pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


# 一時ディレクトリと信号の部品（#1600。docstring の「一時ディレクトリと信号の部品」が原本）
SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
# 一時ディレクトリに書く、いま走らせている検査器のプロセスグループの番号（SIGKILL の後も検査器は別のセッションで走り続ける）
GROUP_FILE = ".tool-group"
UNREADABLE = -1  # 記録を読み出せない——プロセスグループの番号にはならない値


class Interrupted(BaseException):
    """信号で止められた。`Exception` の子にしない——途中の `except Exception` に呑ませず、`with` の片付けまで上げる。"""

    def __init__(self, signum):
        super().__init__(signum)
        self.signum = signum


def _on_signal(signum, frame):
    for sig in SIGNALS:  # 2 回目は無視する——片付けの途中で止めない
        signal.signal(sig, signal.SIG_IGN)
    raise Interrupted(signum)


def current_signals():
    """いまの扱い（`catch_signals` と `restore_signals` に渡す）。入れる前に取り、入れるのは呼ぶ側の try の中で——入れた直後の信号を try の外で上げない。"""
    return {sig: signal.getsignal(sig) for sig in SIGNALS}


def catch_signals(saved):
    """SIGTERM・SIGINT・SIGHUP を `Interrupted` にする（`saved` で親が無視にしていたものは無視のまま）。"""
    for sig, old in saved.items():
        if old is not signal.SIG_IGN:  # 親が無視にしたもの（`nohup` の SIGHUP・`&` の SIGINT）は無視のまま
            signal.signal(sig, _on_signal)


def restore_signals(saved):
    # 戻す途中に届いた信号は待たせ、戻した後の扱いで受ける——1 つ目を戻した後の 2 つ目で `Interrupted` を try の外に上げない
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)
    try:
        for sig, old in saved.items():
            signal.signal(sig, signal.SIG_DFL if old is None else old)
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, mask)


def say(message):
    """信号で止められたことを標準エラーに 1 行言う。書けなくても（SIGHUP の後の閉じた端末・読み手の居ない管）終了コードを変えない。"""
    try:
        print(message, file=sys.stderr, flush=True)
    except OSError:
        sys.stderr = None  # 終わるときの書き出しでも失敗させない——失敗すると Python は 120 で終わる


def owned_pattern(prefix):
    # この版が作る形だけを丸ごと（pid は先頭が 0 でない 10 進、乱字は `tempfile` の英小文字・数字・`_` のちょうど 8 文字）。`\d`・前方だけの一致は作っていない名前まで消す
    return re.compile(re.escape(prefix) + r"([1-9][0-9]*)-[a-z0-9_]{8}")


def owned_dir(prefix):
    """`<頭><pid>-<乱字 8 文字>` の一時ディレクトリ（抜けたら消す）。"""
    return tempfile.TemporaryDirectory(prefix=f"{prefix}{os.getpid()}-")


def record_group(directory):
    """`run_model` の `started` に渡す——起こした検査器のプロセスグループを一時ディレクトリに書く。"""
    return lambda proc: (Path(directory) / GROUP_FILE).write_text(str(proc.pid), encoding="utf-8")


def sweep(prefix):
    """自分の pid の `<頭><pid>-*` を消す（片付けの途中に届いた信号で、削除が途切れていることがある）。"""
    for path in Path(tempfile.gettempdir()).glob(f"{prefix}{os.getpid()}-*"):
        shutil.rmtree(path, ignore_errors=True)


def alive(pid):
    """そのプロセスが居るか。分からない（権限・範囲の外）は居るほうに倒す。"""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except (OSError, OverflowError):
        return True
    return True


def running_group(path):
    """そのディレクトリに書いた検査器のプロセスグループが、まだ居ればその番号。記録が無ければ None、読めなければ `UNREADABLE`。"""
    try:
        raw = (path / GROUP_FILE).read_bytes()
    except FileNotFoundError:
        return None
    except OSError:  # 権限などで読めない
        return UNREADABLE
    try:
        group = int(raw.decode("ascii").strip())
    except ValueError:  # ASCII でない（UnicodeDecodeError も ValueError）・数字でない
        return UNREADABLE
    if group < 1:  # 0 は自分のグループ、負は別の意味の宛先——グループの番号ではない
        return UNREADABLE
    try:
        os.killpg(group, 0)
    except PermissionError:  # 別の利用者のグループが居る
        return group
    except (OSError, OverflowError):
        return None
    return group


def reclaim(prefix, base=None):
    """持ち主の pid が居ない `<頭><pid>-…` を消す（SIGKILL の残り）。(消したディレクトリ, 消さなかった (ディレクトリ, グループ))。"""
    base = Path(tempfile.gettempdir()) if base is None else Path(base)
    owned = owned_pattern(prefix)
    gone, kept = [], []
    try:
        entries = sorted(base.iterdir())
    except OSError:
        return gone, kept
    for path in entries:
        found = owned.fullmatch(path.name)
        if not found or path.is_symlink() or not path.is_dir():
            continue
        if int(found.group(1)) == os.getpid() or alive(int(found.group(1))):
            continue
        group = running_group(path)
        if group is not None:  # 持ち主が SIGKILL されても検査器は走り続け、ここに書いている——消しても空かず見えなくなるだけなので、消さずに言う
            kept.append((path, group))
            continue
        shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            gone.append(path)
    return gone, kept


def reclaim_lines(gone, kept):
    """回収の結果を言う行（標準エラーに出す）。"""
    lines = [f"持ち主の居ない一時ディレクトリを消した: {path}" for path in gone]
    for path, group in kept:
        if group == UNREADABLE:
            lines.append(f"持ち主の居ない一時ディレクトリだが、検査器のプロセスグループの記録（{GROUP_FILE}）が読めない（権限か、書かない中身）ので消していない: {path}"
                         f"（検査器が走っていないことを確かめてから手で消す）")
        else:
            lines.append(f"持ち主の居ない一時ディレクトリだが、検査器（プロセスグループ {group}）がまだ書いているので消していない: {path}"
                         f"（止めるなら kill -9 -{group}。止めた後の起動が消す）")
    return lines


def probe(call, timeout=None):
    """呼び方が TLC として通るか。(通ったか, 説明)。"""
    timeout = PROBE_TIMEOUT if timeout is None else timeout
    with tempfile.TemporaryDirectory(prefix="spec-loop-check-tlc-") as tmp:
        for name, body in (GOOD_MODEL, BROKEN_MODEL):
            (Path(tmp) / f"{name}.tla").write_text(body, encoding="utf-8")
            (Path(tmp) / f"{name}.cfg").write_text(MODEL_CFG, encoding="utf-8")
        rc, out = run_model(call, tmp, GOOD_MODEL[0], timeout)
        if rc != 0 or GOOD_MARK not in out:
            return False, f"通るモデルを通さなかった（終了コード {rc}）: {tail(out)}"
        rc, out = run_model(call, tmp, BROKEN_MODEL[0], timeout)
        if BROKEN_MARK not in out:
            return False, f"違反するモデルで違反を出さなかった（終了コード {rc}。TLC として検査していない）: {tail(out)}"
    return True, "通るモデルを通し、違反するモデルで違反を出した"


def has_workers(call):
    """呼び方の行に `-workers` の語があるか（利用者がワーカーの数を決めている）。"""
    try:
        words = shlex.split(call)
    except ValueError:  # 閉じていない引用符——語の区切りだけで見る
        words = call.split()
    return WORKERS_OPTION in words


def for_verdict(call):
    """判定だけが要る検査（本体・陽性対照）の呼び方。利用者が `-workers` を書いていなければ `-workers auto` を後ろに足す。"""
    return call if has_workers(call) else f"{call} {WORKERS_OPTION} {VERDICT_WORKERS}"


def for_trace(call):
    """反例の経路・状態グラフが要る検査の呼び方。呼び方に何があっても後ろに `-workers 1 -fp 0` を足す（TLC は後の値を使う）。"""
    return f"{call} {WORKERS_OPTION} {TRACE_WORKERS} {FP_OPTION} {TRACE_FP}"


def tail(out, n=3):
    lines = [line for line in (out or "").splitlines() if line.strip()]
    return " / ".join(lines[-n:]) if lines else "（出力なし）"


def judge(root, autopilot=False):
    """(終了コード, 出力の行, 外す宣言で確かめなかったか)。"""
    try:
        call, opt_out, note = read_declarations(root)
    except Unknown as e:
        return EXIT_UNKNOWN, [f"判定できなかった: {e}"], False
    if opt_out and autopilot:
        return EXIT_OK, [f"`{OPT_OUT_KEY} {OPT_OUT_VALUE}` の宣言がある——TLC を確かめていない（必須から外している）"], True
    lines = []
    if opt_out:
        lines.append(f"注記: `{OPT_OUT_KEY} {OPT_OUT_VALUE}` と宣言しているが、業務フローを対象に選んだなら宣言が古い")
    if call is None:
        return EXIT_MISSING, lines + [f"TLC が無い: {note}（`command -v` では探さない）",
                                      f"用意のしかた: Java と `tla2tools.jar` を置き、正本の `CLAUDE.md` に `{CALL_KEY} <コマンド>` を書く"
                                      f"（業務フローを形式検査しない案件なら `{OPT_OUT_KEY} {OPT_OUT_VALUE}`）"], False
    ok, detail = probe(call)
    if not ok:
        return EXIT_MISSING, lines + [f"TLC が無い: 呼び方 `{call}` が通らない——{detail}"], False
    return EXIT_OK, lines + [f"TLC が在る: 呼び方 `{call}`——{detail}"], False


def main(argv=None):
    p = argparse.ArgumentParser(description="TLC が正本の CLAUDE.md の呼び方で使えるかを確かめる（読むだけ）")
    p.add_argument("root", type=Path, help="正本リポジトリの根（CLAUDE.md の在る場所）")
    p.add_argument("--autopilot", action="store_true", help="外す宣言が有れば確かめない（autopilot が Formal Checker を起こす段の始め）")
    try:
        args = p.parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    code, lines, _ = judge(args.root, args.autopilot)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
