#!/usr/bin/env python3
r"""複数 Issue を回すときの台帳（依存グラフと状態）を、ファイルに持って読み書きする。

    python3 <このスキルの base ディレクトリ>/scripts/ledger.py init <名前>
    python3 <…>/ledger.py add  <名前> <番号> [--deps 12,13] [--title 題] [--origin 出所]
    python3 <…>/ledger.py set  <名前> <番号> 鍵=値 [鍵=値 …]
    python3 <…>/ledger.py group <名前> <代表> <番号> [<番号> …]
    python3 <…>/ledger.py lines <名前> 項目=値 [項目=値 …] --source 出所
    python3 <…>/ledger.py user-ops <名前> [コマンド …] --source 出所
    python3 <…>/ledger.py show <名前>
    python3 <…>/ledger.py next <名前>
    python3 <…>/ledger.py path <名前>

**いつ使い、いつ書き換え、どう再開するかは `references/ledger.md` を正とする**
（このスキルと同じ場所にある）。ここにあるのは台帳の形と、このスクリプトが守るものである。

## なぜ在るのか（#390）

#389 の周では、依存のある 17 件を利用者不在で回すために、親が scratchpad に Markdown の台帳を置き、
状態が動くたびに書き換えて、30 分おきのタイマーがそれを読んで再開した。**台帳が親の文脈にしか無いと、
圧縮とセッションの終わりで消える**——「モデルは忘れる、リポジトリは忘れない」を複数 Issue の層にも当てる。
**scratchpad もセッションと一緒に消える**ので、置き場所はメインの作業ツリーの `.claude/plans/` にする。

## 台帳の場所

`<メインの作業ツリー>/.claude/plans/cruise-<名前>.json`。**メインの作業ツリーにいれば
`git rev-parse --show-toplevel`、worktree の中なら共通ディレクトリ（`--git-common-dir`）が `.git` ならその親、
そうでなければ共通ディレクトリの `core.worktree`（サブモジュール）から決め、どれでも決まらなければ 4。
共通ディレクトリが bare なら、メインの作業ツリーは無いので 4**
——worktree の中から走らせても同じファイルを指す（worktree の `.claude/plans/` は周を畳むと一緒に消える）。
**共通ディレクトリの親を無条件に使わない**——`--separate-git-dir` のリポジトリとサブモジュールで外に書く。

## 台帳の形

```json
{"format": 1, "name": "<名前>", "issues": [
  {"number": 12, "title": "", "deps": [], "state": "todo",
   "pr": "", "branch": "", "worktree": "", "agent": "", "base": "", "note": "", "decisions": "", "origin": "", "group": "", "updated": "<UTC>"}
],
 "lines": {"values": {"仕様の穴": "推奨で決めて起票"}, "source": "<出所>", "updated": "<UTC>"},
 "user_ops": {"commands": ["gh workflow run infra-apply.yml"], "source": "<出所>", "updated": "<UTC>"}}
```

`user_ops` は**利用者が自分で打つと決めた操作**（#466）で、無くてもよい。cruise の起動時の点検で
**止まりうる操作**（`check-unattended-env.py`）を見せ、利用者が「その操作だけ自分で打つ」を選んだものを置く。
**周はそれを打たずに `await` で止め、依存しない次の周へ進む**——どう使うかは `references/ledger.md` を正とする。
`lines` と同じく置き換えで、出所の無い値を書かない。

`lines` は**利用者が確かめた線**（#458）で、無くてもよい（無い台帳はこれまでどおり読む）。
**項目と値は `LINES` だけ**——意味は `references/absent-lines.md` の「線と既定」と `references/fix-line.md`
（`直す線`）と `references/found-lines.md`（`周の途中の課題`。#464）を正とし、
`scripts/test-ledger.py` が `LINES` を `absent-lines.md` の表と、`直す線` は `SKILL.md` 手順 3 と、`周の途中の課題` は
`found-lines.md` と突き合わせる（`fix-line.md` は見ていない）。**`本番反映` は項目に無い**（広げられない）。
**どこから来た値を `lines` に書いてよいか（出所）は `references/absent-lines.md` の「線を広げられるのは利用者だけ」を正とする**
——このスクリプトは出所を確かめない（`--source` に書かれた文字列を残すだけ）。

**`show` は、線に `マージ` があるとき、出所に印 `配布を見せて確かめた` があるかを「配布の確認」の行で出す**（#507）。
印の効き方は `references/absent-lines.md` の「`ドキュメントとプラグインの配布`」を正とする。**「あり」と読むのは区切った形だけ**——
印の前が出所の先頭か `（` `、` `・` `＋` `: ` `：`、後ろが出所の終わりか `——` か、`）`（1 つ以上）とその後ろの出所の終わり・`＋`・`（`。
例: `利用者の確認（起動時・2026-10-27T09:07:27Z、配布を見せて確かめた）` と、#474 の台帳に実際にある
`…＋利用者の確認（再開時・2026-10-28T23:56:17Z）: 配布を見せて確かめた——main へのマージが…` はあり、
`利用者の確認（起動時）、配布を見せて確かめた、とは言えない` はなし。
**`）` の後ろにつなげるのは `＋` と `（` だけ**——`）、`・`）。`・`）——` などでつなぐと「なし」（#681）。
**`lines` は、印のある出所を `マージ` の線と一緒にしか書かない**（#681）——線の無いまま印だけ残ると、あとで線を足したときに古い印が効く。

**状態**（`set state=` に渡せるのはこれだけ）:

| 状態 | 意味 |
| --- | --- |
| `todo` | 未着手 |
| `impl` | 実装中（worktree がある） |
| `gate` | 関門（Verifier・`/code-review`）を回している |
| `pr` | PR を出し、マージを待っている |
| `merged` | マージ済み（**依存先として「済んだ」と読むのはこれだけ**） |
| `blocked` | 止まっている（人間の判断待ち・BLOCKED） |
| `await` | 利用者の操作待ち（#466）——止まりうる操作（権限の拒否・`user_ops`）を利用者が打つのを待つ。打つコマンドは `note` に。**依存先としては「済んでいない」と読む** |
| `dropped` | 取り下げ（依存先としては「済んでいない」と読む） |

**鍵**（`set` に渡せるのはこれだけ）: `state` `title` `deps` `pr` `branch` `worktree` `agent` `base` `note` `decisions` `origin` `group`。
`deps` はカンマ区切りの番号（空にすると依存なし）。`decisions` はその周が推奨で決めて起票した `要確認` Issue の番号
（カンマ区切り。`references/absent-lines.md` の「`仕様の穴 = 推奨で決めて起票`」）。
`origin` は**周の途中で見つかって台帳に足した行の出所**（どの周のどの関門のどのパスの行か。#464）で、親 Issue から作った行は空。
**空でない行が「cruise の途中で生まれた行」である**——足し方と、cruise を終えるときの扱いは `references/found-lines.md` を正とする。
`group` は**まとめ**（#641）——その行が入ったまとめの**代表の番号**（文字列）で、まとめに入っていない行は空（欄が無い台帳もこれまでどおり読む）。

## まとめ（#641）

**同じファイルを触る複数の行を、1 つの周・1 つの PR で回すための束**である。いつ・何をまとめるかは cruise の
`../cruise/references/grouping.md` を正とする（このスキルの base ディレクトリからの相対）。ここにあるのは台帳の上の振る舞いだけ:

- **作るのは `group <名前> <代表> <番号>…` だけ**——代表を含めて 2 件以上（代表だけなら引数が違うので 2）の、`todo` でどのまとめにも入っていない行を束ね、各行の `group` に代表の番号を書く。
  **前の周の在り処（`pr` `branch` `worktree` `agent` `base`）を持ったままの行は拒む**（#665）——消すのは呼ぶ側（実物で確かめてから `set`）。
- **`set` の `state` `pr` `branch` `worktree` `agent` `base`（周の在り処）は、まとめの全行に書く**——`note` `title` `deps` `decisions` `origin` はその行だけ。
- **抜けるのは `set <番号> group=`**（空だけを渡せる）。**同じ呼び出しの `state` などは、抜けた後のその行だけに効く**——落ちた行を戻す形
  （まとめの PR のマージの後に `set <番号> group= state=todo pr= branch= worktree= agent= base=`。いつ・どの順で戻すかは grouping.md の「マージの後」——
  抜けた後に輪になる順は拒む）。**代表は、他の行が残るあいだは抜けられない。**
- **`show` は、まとめに入ったまま `merged` で `note` が `落ちた:` で始まる行を名指しする**——マージの後の手順（代表に `merged` を書く→落ちた行を戻す）の
  途中で止まった跡である（#665）。戻すかは実物（Issue・PR）で確かめてから（`references/ledger.md` の「どう再開するか」）。
- **`next` はまとめを 1 行で出す**——代表を先頭に、残りを台帳の順に空白で区切る。**全行が着手できるときだけ**出し、行を個別には出さない。
  **まとめの中の依存は済んだと読む**（一緒にマージされるので）。まとめの無い台帳の出力は 1 行 1 番号のまま。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 通った（`next` で着手できるものが 0 件でも 0） |
| 2 | 引数が違う（名前の形・番号の形・`鍵=値` の形・`group` に代表のほかの番号が無い） |
| 3 | 操作を拒んだ——**台帳は 1 バイトも変えていない**（まとめを 1 つと数えた循環・在る台帳への `init`・台帳に無い Issue・2 度目の `add`・決まった一覧に無い状態や鍵・依存の誤り・`decisions` が番号でない・`LINES` に無い線の項目や値・同じ項目を 2 度・出所が空・出所のある行の依存が空・まとめに入れられない行（`todo` でない・別のまとめに入っている・同じ番号を 2 度・前の周の在り処を持ったまま）・`set group=` に空でない値や空白だけの値・他の行が残るまとめから代表を抜く・まとめの状態をそろえなくする操作・`マージ` の線の無い出所の印） |
| 4 | 判定できなかった（git の外・メインの作業ツリーを決められない・台帳が無い・JSON が読めない・形が違う・**中身が崩れている**（循環・無い依存先・同じ番号が 2 つ）・台帳を書けなかった）。**「着手できるものなし」とは答えていない** |

## 何を守り、何を守らないか

守る:

- **台帳の場所は cwd に依らない**——メインの作業ツリーでも、worktree の中やそのサブディレクトリでも、同じ絶対パスを指す。
- **`--separate-git-dir` のリポジトリ（先の名前が `.git` でないもの）とサブモジュールと bare リポジトリの worktree でも、
  作業ツリーの外に書かない**——worktree の中からメインの作業ツリーを決められなければ 4。
- **在る台帳を `init` で上書きしない。**
- **決まった一覧に無い状態・鍵を拒む**——綴りを誤った状態を書くと、`next` の判定から黙って外れる。
- **依存の誤り（台帳に無い依存先・自己依存・循環）を、`add` でも `set deps=` でも拒む**——循環があると、どの Issue も永遠に着手できない。
- **`next` は「未着手で、依存がすべてマージ済み」のものだけを出す**——依存が PR 中・止まっている・取り下げなら出さない。
- **読めない台帳を「空」と読まない**——壊れた JSON・形の違う台帳（真偽値の番号・`format` が int の 1 でない・
  決まった一覧に無い欄・ファイル名と違う `name` を含む）・無い台帳・読む権限の無い台帳は 4 で止まり、書き換えない。
- **ファイルの上で中身の崩れた台帳（循環・無い依存先・同じ番号が 2 つ）に答えない**——手で直した台帳でも、
  `next` に答えさせず、`set`・`add` を「拒んだ」（3）とも言わずに 4 で止まる。
- **書けなかったときに、表に無い終了コードで終えない**——書けない・読めない・名前が長すぎる・`.claude/plans` がファイルなら 4
  （**在るかを確かめる段も含む**——`Path.exists()` は Python 3.13 以前で権限や名前の長さの誤りを例外で返す）。
- **台帳の名前にパスの区切りと先頭のドットを許さない**——`.claude/plans/` の外に書かない。
- **拒んだ操作では台帳を変えない**——全体を検査してから一時ファイルに書き、`os.replace` で置き換える。
- **`LINES` に無い線の項目・値を書かない**——`lines` でも、手で直した台帳の `load` でも（後者は 4）。
  **`本番反映` は項目に無いので、どの値でも拒む。**
- **`origin` も文字列だけ**——手で直した台帳で文字列でなければ 4。`origin` を持たない台帳はこれまでどおり読む。
- **`add --origin` に空を渡したら拒む**——空にすると「周の途中で足した行」の集計から外れる。
  **`--origin` を渡し忘れた `add` は見分けられない**——親 Issue から作る行と同じ形なので、足す手順（`references/found-lines.md`）が守る。
- **`set origin=` で空にするのも拒む**——同じ理由。
- **`add --origin` に `--deps` が無ければ拒む**——無いと元の周のマージより先に `next` に出る。
  **依存が*元の周*かどうかは見ない**——番号の意味を知らない。
- **`set` で、出所を持ち依存が空の行を作らない**——同じ理由。出所を持つ行の `deps=` で依存を消すのも、
  依存の空の行に `origin=` で出所を後付けするのも拒む（同じ呼び出しで両方を渡したら、渡した後の値で見る）。
- **`user_ops` も出所の無い値を書かない**——`--source` が空・空のコマンド・同じコマンドを 2 度は拒む。置き換えで、渡さなければ空になる。
  手で直した台帳で形が違えば 4。`user_ops` を持たない台帳はこれまでどおり読む。
- **`await` の行は `next` に出さず、それに依存する行も出さない**——操作が済むまで、依存する周は始めない。
- **`lines` は出所の無い値を書かない**——`--source` が空なら拒む。**`lines` は置き換えで、渡さなかった項目は消える**
  ——前の確認の値が、確かめ直した後に黙って残らない。
- **`show` の「配布の確認」は、出所の印を区切った形でだけ「あり」と出す**——印を含む否定文（`…、配布を見せて確かめた、とは言えない`・
  `配布を見せて確かめたとは言えない`）を「あり」と読まない。配布を起こすマージは revert しても戻らないので、誤って通る側に倒さない。
- **`lines` は、区切った印のある出所を `マージ` の線と一緒にしか書かない**（#681）——線の無いまま印が残ると、あとで `マージ` の線を足すとき
  出所を写した親の書き直しで、確かめ直していない印が効く（cruise `SKILL.md` §2 の 1 の「印の扱い」）。
- **`group` は `todo` の行だけをまとめる**——進行中・止まった行を引き込むと、その行の worktree と PR を持ったまま別の周に入る。
- **`group` は別のまとめに入った行を引き込まない**——1 つの行が 2 つの周に入る。
- **`group` は前の周の在り処（`pr` `branch` `worktree` `agent` `base`）を持ったままの行をまとめない**（#665）——まとめの行は状態と在り処がそろう前提なので、
  代表に書かれない鍵の古い値が 1 行だけに残り、`show` が別の周の PR や worktree を出す。**消さずに拒む**——まだ在る worktree・PR を指すかは実物を見ないと分からない。
- **代表は自分のまとめに入っている**——代表が抜けた（`set <代表> group=` で他の行が残る）・代表が台帳に無い台帳を作らない
  （手で直した台帳なら 4）。
- **`group` は番号の文字列だけ**——空白を剥がさない（`" 1"` を通すと、検査は 1 つのまとめと読み、`next`・`set` は別のまとめと読む）。手で直した台帳なら 4。
- **まとめを 1 つの節点と数えた循環を拒む**——行ごとには循環が無くても、まとめの外の行を経てまとめに戻る依存（10 ← 11 ← 12 で 10 と 12 をまとめる）は、
  そのまとめを永遠に着手させない。`group` でも、まとめの行への `set deps=` でも拒む（手で直した台帳なら 4）。
- **`group` は同じ番号を 2 度受け付けない**——代表を後ろにもう 1 度書いた形も。
- **まとめの行は状態がそろう**——`set` の周の在り処（`state` ほか）はまとめの全行に書く。
- **状態のそろわないまとめを持つ台帳は崩れている**——手で直した台帳なら 4 で、`next` に答えない。
- **`next` はまとめを、全行が着手できるときだけ 1 行で出す**——1 行だけ着手できても出さない（残りを置いて周を始めない）。
- **まとめの中の依存は済んだと読む**——読まないと、中に依存のあるまとめが永遠に出ない。
- **`set group=` は抜けるだけ**——空でない値を拒む（まとめに入れるのは `group` で、件数と状態を確かめてから）。
- **`set group=` に空白だけの値を渡したら、空白だけと言って拒む**（#665）——剥がさずに通すと「group が番号でない」と言い、抜けるつもりの呼び手が原因を取り違える。
- **抜けた行に同じ呼び出しで渡した `state` などは、その行だけに効く**——抜ける前のまとめに伝えると、落ちた 1 件を戻すつもりで全行を戻す。
  **抜けても、周の在り処（`pr` `branch` `worktree` `agent` `base`）は自分では消さない**——消すのは呼ぶ側
  （戻すなら同じ呼び出しで `pr= branch= worktree= agent= base=` を渡す。手順は `../cruise/references/grouping.md`）。
- **`show` は、まとめに入ったまま `merged` で `note` が `落ちた:` で始まる行を名指しする**（#665）——マージの後に代表へ `merged` を書いてから
  落ちた行を戻すまでの間で止まると、落ちた行は `merged` のまま `next` にも「進行中」にも出ず、直されないまま済んだことになる。
- **`group` は、入れる行の `note` の `落ちた:` を `前に落ちた:` に書き換える**（#665）——前のまとめで落ちて戻した行は `note` に理由を残す決まりなので、
  そのまま新しいまとめに入れてマージすると、落ちていないのに名指しされ、cruise の終わりの行も出なくなる。理由の文は残す。
- **名指しした行があるあいだは「すべてマージ済みか取り下げ」と出さない**（#665）——cruise はその行で終えるので、出すと直していない行を済んだと報告して終える。

守らない:

- **落ちた行の名指しが正しいか**——`note` の文字とまとめの欄だけで見る。`group` を通さずに `set … note=落ちた: …` を書いたままマージした行は名指しし、
  `note` を `落ちた:` で始めずに落とした行は名指ししない。実物（Issue が開いているか・まとめの PR の `Refs`）は再開する側が見る（`references/ledger.md`）。
- **戻す順**——1 行ずつ抜けた後に輪になる順は拒む（3。台帳は変えない）が、輪にならない順を自分では選ばない（`../cruise/references/grouping.md` の「マージの後」）。

- **複数のセッションからの同時書き込み**——`os.replace` なので半端なファイルは残らないが、後勝ちで片方の更新が消えうる。
  台帳を書くのは親 1 体である（`references/ledger.md`）。
- **状態の遷移の順序**——やり直し・取り下げで逆行が正当に起きるので縛らない。
- **台帳と実物（PR・worktree・ブランチ）が一致しているか**——書いてある値を出すだけで、`gh` も `git worktree` も見ない。
  再開する側が実物で確かめる（`references/ledger.md`）。
- **`lines` の値の出所が本当に利用者か**——`--source` の文字列を残すだけで、確かめない（出所の決まりは `references/absent-lines.md`）。
- **区切った形で書いた否定**（`（配布を見せて確かめた）（ではない）`・`: 配布を見せて確かめた——とは言えない` など）——形しか見ないので「あり」と出す。
  出所を書くのは親で、書き方は cruise の `SKILL.md` §1・§2 にある。**守るのは、印を含む文を書いたときに誤って通らないことまで。**
- **stacked な周**（依存が PR 中で、その上に積んで先に始める）——`next` には出さない（#392）。
- **`--separate-git-dir` の先が `.git` という名前のリポジトリ**——worktree の中から、その git-dir の親を
  メインの作業ツリーと読む（作業ツリーの外に書く）。**git 自身がこの配置を通常のリポジトリと区別しない**
  （`git worktree list` の先頭も同じ値を返す）ので、ここからは見分けられない（#390 の 2 パス目）。
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

STATES = ("todo", "impl", "gate", "pr", "merged", "blocked", "await", "dropped")
KEYS = ("state", "title", "deps", "pr", "branch", "worktree", "agent", "base", "note", "decisions", "origin", "group")
TEXT_KEYS = ("title", "pr", "branch", "worktree", "agent", "base", "note", "decisions", "origin", "group")
# まとめの全行に書く鍵（周の在り処）。ほかの鍵はその行だけ
SHARED_KEYS = ("state", "pr", "branch", "worktree", "agent", "base")
# 周の在り処（状態を除く）。まとめに入れる行は全部空であること（#665）
PLACE_KEYS = ("pr", "branch", "worktree", "agent", "base")
# まとめの PR で落ちた行の note の書き出し（grouping.md の「まとめの周」）
DROPPED_NOTE = "落ちた:"
# まとめに入れ直した行の、前のまとめで落ちた理由（名指しの対象から外す）
PREV_DROPPED_NOTE = "前に落ちた:"
# 線の項目と、宣言できる値（既定を含む）。意味は references/absent-lines.md・fix-line.md・found-lines.md を正とする
LINES = {
    "直す線": ("既定", "広げる"),
    "仕様の穴": ("止まる", "推奨で決めて起票"),
    "実機確認": ("止まる", "Refs でマージ"),
    "マージ": ("止まる", "関門を通ればマージ"),
    "周の途中の課題": ("外に出す", "台帳に足して直す"),
}
# 線の出所の印（#489）。効き方は references/absent-lines.md の「`ドキュメントとプラグインの配布`」を正とする。
# 印は区切った形でだけ「あり」と読む（#507）——前が出所の先頭か「（」「、」「・」「＋」「: 」「：」、後ろが出所の終わりか「——」か、
# 「）」（1 つ以上）とその後ろの出所の終わり・「＋」・「（」。「: 」と「——」は #474 の台帳に実際にある出所の形（互換）。部分一致にすると、印を含む否定文（「…確かめた、とは言えない」）でも通る
DIST_MARK = "配布を見せて確かめた"
DIST_MARK_RE = re.compile(r"(?:\A|[（、・＋]|: |：)" + DIST_MARK + r"(?:）+(?=\Z|[＋（])|——|\Z)")
ISSUE_FIELDS = {"number", "updated", *KEYS}
DONE = "merged"
NAME_RE = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._-]*")
FORMAT = 1

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_REJECTED = 3
EXIT_UNKNOWN = 4


class Refused(Exception):
    """操作を拒んだ（台帳は変えていない）。"""


class Unknown(Exception):
    """判定できなかった。"""


class Usage(Exception):
    """引数が違う。"""


def _git(cwd, *args):
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise Unknown(f"git を起動できなかった: {exc}") from exc
    return proc.stdout.strip() if proc.returncode == 0 else ""


def main_worktree(cwd=None):
    """メインの作業ツリーの絶対パス。**worktree の中からでも同じ値を返す。**

    **共通ディレクトリの親を無条件に使わない**——`--separate-git-dir` のリポジトリとサブモジュールでは、
    共通ディレクトリが作業ツリーの直下に無い（`git worktree list` の先頭も同じ誤りを返す）。
    """
    lines = _git(cwd, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir").splitlines()
    if len(lines) != 2:
        raise Unknown("git のリポジトリの中ではない（場所を決められない）")
    git_dir, common = Path(lines[0]), Path(lines[1])
    if _git(cwd, "--git-dir", str(common), "config", "--bool", "core.bare") == "true":
        # bare の worktree: 共通ディレクトリが `<dir>/.git` でも、その親は作業ツリーではない
        raise Unknown(f"bare リポジトリで、メインの作業ツリーが無い（共通ディレクトリ: {common}）")
    if git_dir == common:  # メインの作業ツリーにいる
        top = _git(cwd, "rev-parse", "--show-toplevel")
        if not top:
            raise Unknown("作業ツリーの外にいる（場所を決められない）")
        return Path(top)
    if common.name == ".git":
        return common.parent
    worktree = _git(cwd, "--git-dir", str(common), "config", "--get", "core.worktree")
    if worktree:  # サブモジュール: 共通ディレクトリの設定が作業ツリーを持つ
        return (common / worktree).resolve()
    raise Unknown(f"worktree の中から、メインの作業ツリーを決められない（共通ディレクトリ: {common}）")


def ledger_path(name, cwd=None):
    if not NAME_RE.fullmatch(name):
        raise Usage(f"台帳の名前が違う: {name!r}（英数字・`_`・`-`・`.` のみ。先頭のドットと区切りは不可）")
    return main_worktree(cwd) / ".claude" / "plans" / f"cruise-{name}.json"


def parse_number(text, error=None):
    if not re.fullmatch(r"[1-9][0-9]*", text.strip()):
        raise (error or Usage)(f"Issue 番号が違う: {text!r}")
    return int(text.strip())


def parse_deps(text, error=None):
    return [parse_number(t, error) for t in text.split(",") if t.strip()]


def check_line(key, value):
    if key not in LINES:
        raise Refused(f"決まった一覧に無い線 {key!r}（{', '.join(LINES)}。本番反映は広げられない）")
    if value not in LINES[key]:
        raise Refused(f"{key} に宣言できない値 {value!r}（{' / '.join(LINES[key])}）")


def check_user_ops(commands, source):
    if not source.strip():
        raise Refused("出所が空（--source に、誰がいつ決めたかを書く）")
    if any(not c.strip() for c in commands):
        raise Refused("空のコマンドがある")
    if len(commands) != len(set(commands)):
        raise Refused("同じコマンドを 2 度渡した")


def exists(path):
    """**`Path.exists()`／`is_file()` を使わない**——Python 3.13 以前は権限・名前の長さの誤りを例外で返し、
    3.14 は False を返す（権限の無いことを「無い」と言う）。無いときだけ False、他は判定できなかった。"""
    try:
        path.stat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise Unknown(f"台帳の在り処を確かめられない: {path}: {exc}") from exc
    return True


def load(path):
    if not exists(path):
        raise Unknown(f"台帳が無い: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Unknown(f"台帳を読めない: {path}: {exc}") from exc
    # `format` は int の 1 だけ——`true == 1`・`1.0 == 1` が通るので型も見る
    if (not isinstance(data, dict) or not {"format", "name", "issues"} <= set(data) <= {"format", "name", "issues", "lines", "user_ops"}
            or type(data["format"]) is not int or data["format"] != FORMAT
            or data["name"] != path.name[len("cruise-"):-len(".json")] or not isinstance(data["issues"], list)):
        raise Unknown(f"台帳の形が違う: {path}")
    for issue in data["issues"]:
        if (not isinstance(issue, dict) or not set(issue) <= ISSUE_FIELDS or not is_number(issue.get("number"))
                or issue.get("state") not in STATES or not isinstance(issue.get("deps"), list)
                or not all(is_number(d) for d in issue["deps"])
                or not all(isinstance(issue.get(k, ""), str) for k in (*TEXT_KEYS, "updated"))):
            raise Unknown(f"台帳の形が違う: {path}: {issue!r}")
    if "lines" in data:
        lines = data["lines"]
        if (not isinstance(lines, dict) or set(lines) != {"values", "source", "updated"}
                or not isinstance(lines["values"], dict)
                or not all(isinstance(lines[k], str) for k in ("source", "updated"))):
            raise Unknown(f"台帳の線の形が違う: {path}: {lines!r}")
    if "user_ops" in data:
        ops = data["user_ops"]
        if (not isinstance(ops, dict) or set(ops) != {"commands", "source", "updated"}
                or not isinstance(ops["commands"], list) or not all(isinstance(c, str) for c in ops["commands"])
                or not all(isinstance(ops[k], str) for k in ("source", "updated"))):
            raise Unknown(f"台帳の利用者が打つ操作の形が違う: {path}: {ops!r}")
    # **ファイルの上で既に崩れている台帳は、拒んだ（3）ではなく判定できなかった（4）**——
    # 引数が悪いのではないので、3 と答えると原因を取り違える。`next` に答えさせてもいけない
    try:
        validate(data)
    except Refused as exc:
        raise Unknown(f"台帳の中身が崩れている: {path}: {exc}") from exc
    return data


def is_number(value):
    # bool は int の部分型なので、`true` を番号として通さないよう分けて見る
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def validate(data):
    """台帳全体の整合。**書き込む前に必ず通す。**"""
    for key, value in data.get("lines", {}).get("values", {}).items():
        check_line(key, value)
    if "lines" in data and not data["lines"]["source"].strip():
        raise Refused("線の出所が空")
    if "user_ops" in data:
        check_user_ops(data["user_ops"]["commands"], data["user_ops"]["source"])
    for issue in data["issues"]:
        parse_deps(issue.get("decisions", ""), Refused)
    numbers = [i["number"] for i in data["issues"]]
    if len(numbers) != len(set(numbers)):
        raise Refused("同じ Issue が 2 度ある")
    known = set(numbers)
    members = {}
    for issue in data["issues"]:
        if issue.get("group", ""):
            # 空白を剥がさない——" 1" を通すと、検査は 1 つのまとめと読み、`units`・`set` は別のまとめと読む
            if not re.fullmatch(r"[1-9][0-9]*", issue["group"]):
                raise Refused(f"#{issue['number']}: group が番号でない {issue['group']!r}")
            members.setdefault(int(issue["group"]), []).append(issue)
    for head, rows in members.items():
        if head not in known or find(data, head).get("group") != str(head):
            raise Refused(f"まとめ #{head}: 代表が台帳に無いか、代表が自分のまとめに入っていない")
        if len({r["state"] for r in rows}) != 1:
            raise Refused(f"まとめ #{head}: 行の状態がそろっていない（" + ", ".join(f"#{r['number']}={r['state']}" for r in rows) + "）")
    graph = {}
    for issue in data["issues"]:
        if issue["state"] not in STATES:
            raise Refused(f"#{issue['number']}: 決まった一覧に無い状態 {issue['state']!r}（{', '.join(STATES)}）")
        for dep in issue["deps"]:
            if dep == issue["number"]:
                raise Refused(f"#{dep}: 自分自身に依存している")
            if dep not in known:
                raise Refused(f"#{issue['number']}: 依存先 #{dep} が台帳に無い（先に add する）")
        graph[issue["number"]] = issue["deps"]
    find_cycle(graph)
    # まとめを 1 つの節点と数えた循環（まとめの中の依存は数えない）——行ごとには循環が無くても、
    # まとめの外の行を経てまとめに戻る依存があると、そのまとめは永遠に着手できない
    node = {i["number"]: int(i["group"]) if i.get("group") else i["number"] for i in data["issues"]}
    contracted = {n: set() for n in node.values()}
    for issue in data["issues"]:
        contracted[node[issue["number"]]].update(node[d] for d in issue["deps"] if node[d] != node[issue["number"]])
    find_cycle(contracted)


def find_cycle(graph):
    """循環: 深さ優先で、いま辿っている途中の節点に戻ったら循環。"""
    visiting, done = set(), set()

    def visit(n, path):
        if n in done:
            return
        if n in visiting:
            cycle = path[path.index(n):] + [n]
            raise Refused("依存が循環している: " + " → ".join(f"#{c}" for c in cycle))
        visiting.add(n)
        for d in graph[n]:
            visit(d, path + [n])
        visiting.discard(n)
        done.add(n)

    for n in graph:
        visit(n, [])


def save(path, data):
    validate(data)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    except OSError as exc:  # 書けない・名前が長すぎる・`.claude/plans` がファイル
        raise Unknown(f"台帳を書けなかった（台帳は変えていない）: {path}: {exc}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except OSError as exc:
        Path(tmp).unlink(missing_ok=True)
        raise Unknown(f"台帳を書けなかった（台帳は変えていない）: {path}: {exc}") from exc
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find(data, number):
    for issue in data["issues"]:
        if issue["number"] == number:
            return issue
    raise Refused(f"#{number} は台帳に無い（先に add する）")


def ready(data):
    """着手できる Issue: 未着手で、依存がすべてマージ済み（まとめの中の依存は済んだと読む）。行ごとに見る。"""
    state = {i["number"]: i["state"] for i in data["issues"]}
    group = {i["number"]: i.get("group", "") for i in data["issues"]}
    return [i for i in data["issues"]
            if i["state"] == "todo"
            and all(state.get(d) == DONE or (i.get("group", "") and group.get(d) == i["group"]) for d in i["deps"])]


def units(data):
    """着手できる周の並び。まとめに入っていない行は 1 件ずつ、まとめは全行が着手できるときだけ 1 つ（代表が先頭）。"""
    can = {i["number"] for i in ready(data)}
    out, seen = [], set()
    for i in data["issues"]:
        g = i.get("group", "")
        if not g:
            if i["number"] in can:
                out.append([i])
            continue
        if g in seen:
            continue
        seen.add(g)
        rows = [r for r in data["issues"] if r.get("group", "") == g]
        if all(r["number"] in can for r in rows):
            head = int(g)
            out.append(sorted(rows, key=lambda r: r["number"] != head))
    return out


def cmd_init(path, name):
    if exists(path):
        raise Refused(f"台帳は既に在る（上書きしない）: {path}")
    save(path, {"format": FORMAT, "name": name, "issues": []})
    print(path)


def cmd_add(path, number, deps, title, origin=None):
    if origin is not None and not origin.strip():
        raise Refused("--origin が空（渡すなら、どの周のどの関門のどのパスの行かを書く）")
    if origin is not None and not deps:
        raise Refused("--origin を渡すなら --deps に元の周を書く（無いと元の周のマージより先に next に出る）")
    data = load(path)
    if any(i["number"] == number for i in data["issues"]):
        raise Refused(f"#{number} は既に台帳に在る（変えるなら set）")
    entry = {"number": number, "title": title or "", "deps": deps, "state": "todo",
             **{k: "" for k in TEXT_KEYS if k != "title"}, "origin": origin or "", "updated": now()}
    data["issues"].append(entry)
    save(path, data)
    print(f"#{number} を足した（依存: {', '.join(f'#{d}' for d in deps) or 'なし'}"
          + (f"・出所: {origin}" if origin else "") + "）")


def cmd_set(path, number, pairs):
    # `鍵=値` を先に読む——Issue を先に引くと、台帳に無い Issue への形の誤りが 2 ではなく 3 になる
    changes = {}
    for pair in pairs:
        if "=" not in pair:
            raise Usage(f"`鍵=値` の形ではない: {pair!r}")
        key, value = pair.split("=", 1)
        if key not in KEYS:
            raise Refused(f"決まった一覧に無い鍵 {key!r}（{', '.join(KEYS)}）")
        if key == "deps":
            changes[key] = parse_deps(value)
        elif key == "decisions":
            changes[key] = ",".join(map(str, parse_deps(value, Refused)))
        elif key == "origin" and not value.strip():
            raise Refused("origin を空にしない（空にすると、cruise を終えるときの「周の途中で足した行」から外れる）")
        elif key == "group" and value.strip():
            raise Refused("set group= に渡せるのは空だけ（抜ける）。まとめに入れるのは group で")
        elif key == "group" and value and not value.strip():
            raise Refused(f"set group= に空白だけの値 {value!r} を渡した——抜けるなら `group=` と空で渡す")
        else:
            changes[key] = value
    data = load(path)
    issue = find(data, number)
    after = {**issue, **changes}
    if ("deps" in changes or "origin" in changes) and after.get("origin") and not after["deps"]:
        raise Refused(f"#{number} を出所があって依存の無い行にしない（元の周のマージより先に next に出る）")
    issue.update(changes)
    issue["updated"] = now()
    # まとめの全行に周の在り処を書く——抜けた行は、抜けた後の値（空）で見るので、その行だけに効く
    shared = {k: v for k, v in changes.items() if k in SHARED_KEYS}
    others = [i for i in data["issues"] if i is not issue and issue.get("group", "") and i.get("group", "") == issue["group"]]
    if shared:
        for other in others:
            other.update(shared)
            other["updated"] = issue["updated"]
    save(path, data)
    print(f"#{number}: " + ", ".join(f"{k}={v}" for k, v in changes.items())
          + (f"（まとめ #{issue['group']} の " + ", ".join(f"#{o['number']}" for o in others) + " にも）" if shared and others else ""))


def cmd_group(path, head, numbers):
    rows = [head, *numbers]
    if len(rows) != len(set(rows)):  # 代表を後ろにもう 1 度書いた形も含めて
        raise Refused("同じ番号を 2 度渡した")
    data = load(path)
    issues = [find(data, n) for n in rows]
    for issue in issues:
        if issue["state"] != "todo":
            raise Refused(f"#{issue['number']} は todo でない（{issue['state']}）——進行中・止まった行はまとめない")
        if issue.get("group", ""):
            raise Refused(f"#{issue['number']} は既にまとめ #{issue['group']} に入っている")
        stale = [f"{k}={issue[k]}" for k in PLACE_KEYS if issue.get(k, "")]
        if stale:
            raise Refused(f"#{issue['number']} は前の周の在り処（{', '.join(stale)}）を持ったまま——実物で済んだことを確かめ、"
                          f"`ledger.py set {path.name[len('cruise-'):-len('.json')]} {issue['number']} "
                          + " ".join(f"{k}=" for k in PLACE_KEYS) + "` で消してからまとめる")
    stamp = now()
    for issue in issues:
        issue["group"] = str(head)
        # 前のまとめで落ちて戻した行の「落ちた:」を残すと、このまとめがマージされたとき落ちた行と名指しされる（#665）
        if issue.get("note", "").startswith(DROPPED_NOTE):
            issue["note"] = PREV_DROPPED_NOTE + issue["note"][len(DROPPED_NOTE):]
        issue["updated"] = stamp
    save(path, data)
    print(f"まとめ #{head}: " + ", ".join(f"#{n}" for n in rows))


def has_dist_mark(source):
    """出所に印 `配布を見せて確かめた` が区切った形で入っているか（形は DIST_MARK_RE の上のコメント）。"""
    return DIST_MARK_RE.search(source.strip()) is not None


def cmd_lines(path, pairs, source):
    values = {}
    for pair in pairs:
        if "=" not in pair:
            raise Usage(f"`項目=値` の形ではない: {pair!r}")
        key, value = (t.strip() for t in pair.split("=", 1))
        if key in values:
            raise Refused(f"{key} を 2 度渡した")
        check_line(key, value)
        values[key] = value
    if not source.strip():
        raise Refused("出所が空（--source に、誰がいつ確かめたかを書く）")
    if has_dist_mark(source) and "マージ" not in values:
        raise Refused(f"出所に印 `{DIST_MARK}` があるのに `マージ` の線を渡していない——印は `マージ` の線と一緒にだけ書く"
                      "（線を外すなら印も外す。cruise SKILL.md §2 の 1 の「印の扱い」）")
    data = load(path)
    data["lines"] = {"values": values, "source": source, "updated": now()}
    save(path, data)
    print("線: " + (", ".join(f"{k} = {v}" for k, v in values.items()) or "なし（宣言と既定に従う）"))


def cmd_user_ops(path, commands, source):
    commands = [c.strip() for c in commands]
    check_user_ops(commands, source)
    data = load(path)
    data["user_ops"] = {"commands": commands, "source": source, "updated": now()}
    save(path, data)
    print("利用者が打つ操作: " + (", ".join(commands) or "なし"))


def cmd_show(path):
    data = load(path)
    print(f"台帳: {path}")
    if "lines" in data:
        lines = data["lines"]
        print("確かめた線（出所: {}・{}）: {}".format(
            lines["source"], lines["updated"],
            ", ".join(f"{k} = {v}" for k, v in lines["values"].items()) or "なし（宣言と既定に従う）"))
        if "マージ" in lines["values"]:
            print(f"配布の確認（マージの線の出所の印 `{DIST_MARK}`）: "
                  + ("あり" if has_dist_mark(lines["source"]) else "なし"))
    else:
        print("確かめた線: 無い（宣言と既定に従う）")
    if data.get("user_ops", {}).get("commands"):
        ops = data["user_ops"]
        print("利用者が打つ操作（出所: {}・{}）: {}".format(ops["source"], ops["updated"], ", ".join(ops["commands"])))
    print()
    print("| # | 状態 | 依存 | PR | ブランチ | worktree | 実装役 | 関門の起点 | メモ | 要確認 | 出所 | まとめ | 更新 |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for i in data["issues"]:
        deps = ", ".join(f"#{d}" for d in i["deps"]) or "-"
        cells = [f"#{i['number']} {i.get('title', '')}".strip(), i["state"], deps,
                 *(i.get(k, "") or "-" for k in ("pr", "branch", "worktree", "agent", "base", "note", "decisions", "origin")),
                 f"#{i['group']}" if i.get("group") else "-", i.get("updated", "")]
        print("| " + " | ".join(str(c) for c in cells) + " |")
    going = [i for i in data["issues"] if i["state"] in ("impl", "gate", "pr", "blocked", "await")]
    can = units(data)
    started = {r["number"] for u in can for r in u}
    waiting = [i for i in data["issues"] if i["state"] == "todo" and i["number"] not in started]
    print()
    print("進行中（実物で確かめてから続ける）: " + (", ".join(f"#{i['number']}({i['state']})" for i in going) or "なし"))
    print("着手できる: " + (", ".join(f"#{u[0]['number']}" + (
        "（まとめ: " + ", ".join(f"#{r['number']}" for r in u[1:]) + "）" if len(u) > 1 else "") for u in can) or "なし"))
    print("依存待ち: " + (", ".join(f"#{i['number']}" for i in waiting) or "なし"))
    awaiting = [i for i in data["issues"] if i["state"] == "await"]
    print("利用者の操作待ち: " + (", ".join(f"#{i['number']}（{i.get('note') or 'note が空'}）" for i in awaiting) or "なし"))
    found = [i for i in data["issues"] if i.get("origin") and i["state"] not in (DONE, "dropped")]
    if any(i.get("origin") for i in data["issues"]):
        print("周の途中で足した行のうち済んでいないもの: "
              + (", ".join(f"#{i['number']}({i['state']})" for i in found) or "なし"))
    stranded = [i for i in data["issues"]
                if i["state"] == DONE and i.get("group") and i.get("note", "").startswith(DROPPED_NOTE)]
    if stranded:
        print("落ちたのにまとめの中で merged のまま（マージの後に戻していない。Issue と PR を実物で確かめてから戻す）: "
              + ", ".join(f"#{i['number']}" for i in stranded))
    heads = sorted({i["group"] for i in data["issues"] if i.get("group")}, key=int)
    if heads:
        print("まとめ: " + "; ".join(
            f"#{h}（{find(data, int(h))['state']}）= " + ", ".join(
                f"#{i['number']}" for i in data["issues"] if i.get("group") == h) for h in heads))
    if data["issues"] and all(i["state"] in (DONE, "dropped") for i in data["issues"]) and not stranded:
        print("すべてマージ済みか取り下げ")


def cmd_next(path):
    data = load(path)
    for unit in units(data):
        print(" ".join(str(i["number"]) for i in unit))


def build_parser():
    p = argparse.ArgumentParser(description="複数 Issue の台帳（依存グラフと状態）")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("init", "show", "next", "path"):
        sub.add_parser(name).add_argument("name")
    a = sub.add_parser("add")
    a.add_argument("name")
    a.add_argument("number")
    a.add_argument("--deps", default="")
    a.add_argument("--title", default="")
    a.add_argument("--origin", default=None)
    g = sub.add_parser("group")
    g.add_argument("name")
    g.add_argument("head")
    g.add_argument("numbers", nargs="+")
    s = sub.add_parser("set")
    s.add_argument("name")
    s.add_argument("number")
    s.add_argument("pairs", nargs="+")
    ln = sub.add_parser("lines")
    ln.add_argument("name")
    ln.add_argument("pairs", nargs="*")
    ln.add_argument("--source", required=True)
    uo = sub.add_parser("user-ops")
    uo.add_argument("name")
    uo.add_argument("commands", nargs="*")
    uo.add_argument("--source", required=True)
    return p


def main(argv=None, cwd=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    try:
        path = ledger_path(args.name, cwd)
        if args.cmd == "init":
            cmd_init(path, args.name)
        elif args.cmd == "add":
            cmd_add(path, parse_number(args.number), parse_deps(args.deps), args.title, args.origin)
        elif args.cmd == "set":
            cmd_set(path, parse_number(args.number), args.pairs)
        elif args.cmd == "group":
            cmd_group(path, parse_number(args.head), [parse_number(n) for n in args.numbers])
        elif args.cmd == "lines":
            cmd_lines(path, args.pairs, args.source)
        elif args.cmd == "user-ops":
            cmd_user_ops(path, args.commands, args.source)
        elif args.cmd == "show":
            cmd_show(path)
        elif args.cmd == "next":
            cmd_next(path)
        elif args.cmd == "path":
            print(path)
    except Usage as exc:
        print(f"引数が違う: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except Refused as exc:
        print(f"拒んだ（台帳は変えていない）: {exc}", file=sys.stderr)
        return EXIT_REJECTED
    except Unknown as exc:
        print(f"判定できなかった: {exc}", file=sys.stderr)
        return EXIT_UNKNOWN
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
