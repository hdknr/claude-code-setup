#!/usr/bin/env python3
"""確定した仕様の中間表現（`spec_ir.json`）から、dev-loop に渡すものを作る。

usage: python3 scaffold.py [--repo <正本リポジトリ>] [--check [--upto <n>] | --dry-run [--upto <n>] | --red-check [--in-progress]] [--provisional]
                           [--bundle F-001,F-002]...

作るもの（置き場所の正は `references/tree.md`）:

- `scaffold/openapi.json`・`scaffold/types.py`・`scaffold/tests/test_<機能>.py`（Red テスト）・`scaffold/perf/perf_<機能>.py`（性能テスト。`nfr` を持つ機能だけ）——**commit する契約**
- `build/scaffold/issues/<機能の id>.md` と `issues.json`——**Issue の本文**（登録はスクリプトの外。`gh` を呼ばない）。`--bundle` でまとめた機能は
  `bundle-<機能の id>-<機能の id>.md` の 1 件（下の「まとめた本文」）
- `build/scaffold/issues/proposals.md`——**課題一覧（案）**（#855。Issue の本文ではない。登録しない——下の「呼ぶ側の分岐」）

**形の正は `references/spec-ir.md`（中間表現）と `references/handoff-issue.md`（Issue の本文）である**
（このプラグインの中にある）。下の定数（メソッド・型・番号の形・印・節）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-scaffold.py` が突き合わせて見る**。

**入力は、正本の版（`docs/v1/`・`docs/v2/`…）を重ね合わせた全体である**（決まりは `references/versions.md`）。
同梱の `merge-versions.py` の `merge` で**メモリ上で**重ね（同じ入力から、`merge-versions.py docs build/merged` が書くのと
同じバイト）、一時ディレクトリに置いて当てる。**`build/merged/` には書かない。** 重ね合わせが決まりに反すれば 1
（JSON として読めない版を含む）、`docs/` が無い・版が読めない・どの版にも中間表現が無ければ 2。

**契約（`scaffold/`）は全体から作り、Issue の本文は変わった機能だけに作る。** 作業中の版 v<n> の全体と v<n-1> の全体を
機能の `id` で比べ（同梱の `diff-versions.py` の `compare_maps`）、**追加・変更・削除**の機能ごとに本文を 1 件作る。
**変わっていない機能の本文は作らない**（前の版の Issue がある）。v1 だけなら全部が追加。
ケースの変化は**Red テストが実行する中身**（入力・期待・`operation.id`・期待にある項目の出力の型・`impl_module`）で決める——
題だけの違い・`integer` を `number` に広げただけの違い・項目の `nullable` を足した・外しただけの違いは変化に数えない（前の版の実装は落ちない）。
**`impl_module` を変えた版では、残る機能も全部が変更になる**（どの Red テストも前の版の実装を探せない）。**前の版の中間表現も決まり（`references/spec-ir.md`）に当て、反すれば分けずに 1。**
**前の版の時点で `反映済み` でない Q&A（`確認中`・`暫定反映`。共有・内部とも）が残れば、中間表現が指しているかに依らず、
後の版で確定しても止め**、v<n-1> を scaffold できていないことを名指しする（#335・#358。手当ては
`references/versions.md` の「前の版の時点が崩れていたら」）。**ただし前の版が凍結していれば（`release-v<n-1>`）止めない**
——直せないので v<n-1> の時点を信じず、v<n> の機能を全部追加にし、v<n> で消した機能の撤去の本文は作らない（そう出力する。#357）。
凍結を見るのはこのときだけで、`git` を起動できない・浅い clone なら判定しない（2）。**タグがあるだけでは凍結と読まない**
——`check-frozen.py` がタグの後に直されたと言えば止め（1）、判定できなければ 2。前の版に中間表現が無くても Q&A の状態は見る。

**呼ばれる機能（`called_by`。#609）**: 機能が他の機能から呼ばれる判定の関数なら、中間表現の `called_by` に呼ぶ機能を書く。
**呼ぶ機能が重ね合わせた全体の中間表現に無ければ 1**（形の誤り・自分自身・循環も 1）。v2 以降で `called_by` を持つ機能が追加・変更され、
**呼ぶ機能がどれも追加・変更されていなければ、止めずに名指しで知らせる**（0）。Issue の本文の `## 仕様` には呼ぶ機能の id と題を書く。
**`called_by` を書かない機能は入口と読む**——書き起こす側が関数を入口と偽れば通る（決まりの正は `references/spec-ir.md` の「呼ばれる機能」）。

**作らないもの（`out_of_scope`。#851）**: 本文の `## 作らないもの` に、中間表現の機能の `out_of_scope` に挙げた範囲の外の行を、
範囲の文書（`spec/scope.md`）の「範囲の外」の節から**原文のまま**写す（表の行なら表の見出しの 2 行を付ける）。「次の版の候補」を含む行は
`### 次の版の候補` に分ける。**挙げた行が節に原文のまま無い（範囲の文書・節が無い・表の見出しや区切りの行を挙げた）なら 1**——
どの行がその機能に関わるかは書き起こす側の判断で、機械は原文が在ることだけを見る
（決まりの正は `references/handoff-issue.md` の「作らないもの」と `references/spec-ir.md` の「作らないもの」）。

**性能の要求（`nfr`。#852）**: 中間表現の機能の `nfr` に、重ね合わせた全体の `shared/nfr.csv` の性能の行の `No` を書く。
**指した行が無い・2 行ある・性能の行の形（列・指標・上限・単位 `ms`・条件・根拠。`references/nfr.md`）に反するなら 1**——指していない行は見ない。
`nfr` を持つ機能だけ、性能テスト `scaffold/perf/perf_<機能>.py`（契約。実装をケースの入力で 1 回ずつ呼び、1 回の時間から指標を出して上限と比べる）を作り、
本文の `### 性能予算` に行の数字と性能テストを書く。持たない機能の性能予算は「要求なし」（既定の原則）。**性能テストは負荷を再現しない**ので、
Red テストの表（受入基準）にも `--red-check` にも入れない（決まりの正は `references/nfr.md` と `references/spec-ir.md` の「性能の要求」）。

**呼ぶ側の分岐（`branches`。#855）と課題一覧（案）**: 中間表現の機能の `branches` に、仕様チェックリストの「呼ぶ側の分岐」の 8 分岐ごとの
見せるもの（`shows`）か該当なし（`none`）を、**機能の `source` の原文の 1 行**で書く（行ごと該当なしは `none` だけ）。**原文が `source` に無い・
分岐の名前でない・形が決まりに反する・呼ばれる関数（`called_by` を持つ機能）に書いたなら 1**——その行がその分岐を決めているかは書き起こす側の判断。
書く生成は `build/scaffold/issues/proposals.md`（課題一覧（案））も作る——v<n> で追加・変更した入口の機能（`impl_module` を変えただけのものを除く）ごとに 1 案で、
**未決定事項**（`branches` に無い分岐）・**受入基準の雛形**（見せるものの原文のチェックボックス）・**作らないもの**（本文の `## 作らないもの` と同じ中身）を付ける。
**未決定事項があっても止めない**（案は登録しないので。件数を出す）。案を登録するか・未決定事項を spec-review に戻すかは `scaffold` スキルの手順 7
（決まりの正は `references/spec-ir.md` の「呼ぶ側の分岐」）。

**仕様の基準コミット（#874）**: 本文の `## 仕様` に、正本リポジトリで本文を生成した時点の HEAD とそのコミットの日時を
`- 基準コミット: ` の行で書く——dev-loop が周の頭で、その後の変化が仕様の前提（既存のシステム）を崩していないかを点検する
（dev-loop の `references/spec-gap.md`）。**git の作業ツリーの根でない・コミットが無い・git を起動できないなら止めずに**
`記録していない（理由）` と書き、出力でも知らせる（0）。生成の時刻は書かない（同じ HEAD から同じバイト）
（決まりの正は `references/handoff-issue.md` の「基準コミット」）。

**仮回答（`--provisional`。#875）**: 既定では Q&A 表に `暫定反映` の行が 1 つでも残れば止める（#325。下の守らないものの表）。
**利用者が仮回答のまま開発へ渡すと決めたときだけ**、`--provisional` を付けて通す——中間表現の `qa`（機能・ケース）が `暫定反映` の行を
指してよくなり、依存する本文の `## 仕様` に `- 仮回答: ` の行（依存する暫定の No）を、受入基準の表の Q&A の列で暫定の No に `（暫定）` を付ける
（依存しない本文は変わらない）。**どの機能・ケースの `qa` からも指されない `暫定反映` の行が残れば、旗があっても止める（1）**——
その仮回答がどの Issue に効くかを本文に書けない。前の版の時点の判定でも、前の版の中間表現が指す `暫定反映` を崩れに数えない（前の版は同じ旗で作れる状態にある（実際に作ったかは見ない——旗の無い周でも、前の版を作ったかは見ていない））。
旗は全部のモード（`--check`・`--dry-run`・`--red-check`）で受け付ける。作り直す範囲は、登録した本文から同梱の `rebuild-scope.py` で引く
（決まりの正は `references/handoff-issue.md` の「仮回答の印」）。

**まとめた本文（`--bundle`。#876）**: 既定は **1 機能の変化 = Issue 1 件**。`--bundle F-001,F-002`（繰り返せる）で名指しした機能を 1 件の本文にまとめる——
1 行目は同じ handoff の印、2 行目にまとめた印、機能のチェックリストに続けて、**機能 1 件の本文から 1 行目を外した部分**を `---` の行で区切って並べる
（部分ごとに印・節・指紋・sha256 が残る）。`issues.json` の項目は `feature` の代わりに `features` を持つ。**名指しした機能が、この版で本文を作る機能でない・
変化（追加・変更・撤去）が揃わない・1 件だけ・重複・まとめると依存が循環するなら 2**（引数の誤り）。同じモジュール・同じデプロイ経路かは見ない——
中間表現に無く、選ぶのは scaffold を回す人（決まりの正は `references/handoff-issue.md` の「まとめた本文」）。
**依存の連鎖**: `issues.json` の項目は、依存があるときだけ `depends`（依存先の機能の id）を持つ——呼ぶ機能（`called_by` に挙がった入口）の Issue は、
呼ばれる機能の Issue に依存する。番号は登録の後にしか無いので、cruise の親 Issue の書式（`- [ ] #N (depends: #M)`）で出すのは同梱の
`parent-checklist.py`（登録した Issue の一覧から引く）。

**生成の前に、自分で関門を通す**——`check-spec-exit.py` の条件 1（仕様に反映した状態でない Q&A・未決定の印が 0 件）を呼び、
通らなければ 1 バイトも書かない。**条件 2〜5 は判定しない**（判定役の報告で決まる。`scaffold` の本文）。
**全部を組み立ててから書く**ので、入力の誤りで途中で落ちて一部だけ書くことはない。
**書き込みそのもの（ファイルシステム）が途中で失敗すると、`scaffold/` は一部だけ書かれうる**——そのときも
**Issue の本文は書く前に消してある**（古い本文を登録させない）ので、契約の乖離は `--check` が言う。

**実装のモジュールは中間表現の `impl_module` が決める**（省けば `spec_impl`）——引数では渡さない。
引数で渡すと、作り直すたびに指定を繰り返さなければ黙って別のモジュールになり、
`--check` は検査する相手（置いてある Red テスト）からそれを読むしかなくなる。

- `--check`: 書かずに、置いてある `scaffold/` が今の入力から作るものと同じかを確かめる（鮮度）。
  **消した機能の Red テスト・`nfr` を外した機能の性能テストが残っていても古いと言う**（生成の印のあるファイルだけを数える）。
  **バイトで比べる**（改行の違いも古いと言う——Issue の本文の sha256 はバイトの指紋なので）。
- `--dry-run`: 関門と中間表現の検査（前の版との分け方を含む）だけをして、何も書かず何も消さない。
- `--upto <n>`: v<n> までを重ねた全体に当てる（`--check`・`--dry-run` でだけ使える）。**差分の周を始める前に、前の版の
  時点の `scaffold/` が新しいか**を `--check --upto <n-1>` で確かめるのに使う（`references/versions.md`）。
  **書く生成では断る**——古い版の契約を置くと、作業中の版の Issue が指すものと食い違う。
- `--red-check`: 置いてある `scaffold/` が新しいことを確かめてから、Red テストを正本リポジトリの根で走らせ、
  **回帰のケースは緑で、追加・変更のケースは前の版か作業中の版のどちらかの期待を満たすか**を見る。
  **Red テストと受入基準は、実装が前の版の状態にあることを前提にしない**（#294）——**前の版（v<n-1>）の全体から
  Red テストを一時ディレクトリに作り、同じ実装に当てて確かめる**。追加・変更のケースごとに:
    - 作業中の版で失敗し、前の版で緑（か前の版に無い）: 期待どおり（Red）
    - 作業中の版で緑で、前の版でも緑（か前の版に無い）: **0 のまま名指しで知らせる**（もう緑——前の版の実装がもう
      満たし、Red テストはこの変化を判別しない。#281）
    - 作業中の版で緑で、前の版で失敗: **実装は前の版の状態に無い**（1）。`--in-progress` なら実装済みとして数える（#282）
    - どちらでも失敗: 前の版の仕様とも食い違う（1）。`--in-progress` なら**作りかけの実装の誤りを先に挙げる**（同じく 1。
      作り直しでは実装はもう前の版の状態に無いはずなので。#300）。**ただしどちらの版でも「未実装」で落ちるなら、実装が無いだけで
      期待どおり（Red）**——片方の版だけ「未実装」（関数の改名など）なら、もう片方の期待を満たしていないので 1
    - **エラー**（失敗でも緑でもない）: もう一方の版のテストが緑なら、**その版の「失敗」と同じに読む**（入力の名前や
      形を変える変更では、呼び出しの形が合わない側の版のテストが呼び出しで落ちる）。そうでなければ 1——前の版の側なら
      「前の版の状態を判定できない」と言う（乖離とは言い切らない。扱いは scaffold `SKILL.md` 手順 4）。
      **飛ばされた**テストはどちらの版でも 1——前の版の側なら、作業中の版のテストが緑でも「前の版の状態を判定できない」と言う
  **実装が無い**（どのテストも「未実装」で落ちる）なら、期待が全部失敗のとき（v1・追加だけ）は判定でき、
  そうでなければ**回帰を判定していない**（2）。テストを書き換えない・何も書かない。
- `--provisional`: 上の「仮回答」。利用者がそう決めたときだけ付ける。
- `--bundle F-001,F-002`: 上の「まとめた本文」。書く生成と `--dry-run` でだけ使える（`--check`・`--red-check` は本文を作らない）。
- `--in-progress`: `--red-check` と一緒にだけ使う。**作り直しの経路**（この版の Issue を登録し、実装が始まっている）で、
  追加・変更のケースが作業中の版の期待をもう満たしていても止めない。

終了コード:

- 0: 作った（`--check` なら新しい・`--dry-run` なら作れる・`--red-check` なら期待どおり）
- 1: 作らなかった——版の重ね合わせが決まりに反する・関門の条件 1 を満たさない・中間表現（前の版のものを含む）が決まりに
  反する（全部を 1 行ずつ出す）・前の版の時点が崩れている（凍結していない、または凍結したのに直されている）・`--check` で古い・`--red-check` で期待と違う（名指しする）。**Issue の本文の前の出力は消す**
  （古い本文を登録させない。`--check`・`--dry-run`・`--red-check` では消さない）
- 2: 判定していない——引数の誤り（書く生成・`--red-check` に `--upto`、`--red-check` の無い `--in-progress`、無い版の `--upto`、`--bundle` の形・
  まとめ方の誤り（上の「まとめた本文」）・`--check`・`--red-check` との組み合わせを含む）・`docs/` が無い／版が 1 つも無い／
  版が読めない・関門が判定していない・中間表現が無い・Red テストを走らせられない・実装が無く回帰を判定できない・
  前の版の時点が崩れていて凍結しているかを判定できない（`git` を起動できない・浅い clone・`check-frozen.py` が 2）・
  予期しない失敗（書き込みの失敗・128KB を超えるセルの `csv.Error` を含む）。書く生成では前の Issue の本文は消す。
  **ただし引数を解釈する前・判定の外で上がった想定外の例外は、入口が 2 にするだけで本文を消さない**（書く生成かが決まっていない。#286）

**`scaffold/` は失敗しても消さない**——commit 済みの契約で、古ければ `--check` が言う。

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う（`git` は、前の版の時点が崩れていて
凍結しているかを見るときだけ要る）。

**この生成が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **中間表現が仕様と意味で一致するか** | 書き起こしは判断（`scaffold` の仕事）。出所（`source` の実在・Q&A が `反映済み`・ケースの `ref` の番号が原文に在ること。#465）までを見る。`暫定反映` の行が表に残れば、指していなくても止める（`--provisional` のときは、どこからも指されない行だけ止める） |
| **`--provisional` で、暫定の行に依存する機能・ケースを中間表現が漏れなく指しているか** | 指しているかは書き起こしの判断。機械が止めるのは、どこからも指されない暫定の行だけ。指し漏らした機能の本文には印が付かない |
| **登録済みの本文の仮回答の印が、いまの Q&A 表の状態と同じか** | 本文は生成した時点の写し。利用者が確かめた後も印は残る——いまの状態の正は Q&A 表（dev-loop の `spec-gap.md`） |
| **Red テストが仕様のケースを漏れなく持つか** | 中間表現に書いたケースだけが生成される。漏れは書き起こしの側で見る |
| **Python 以外の言語の型・テスト** | OpenAPI から対象リポジトリの道具で作る |
| **Issue を登録したか・登録した本文が同じか** | 登録はスクリプトの外（`gh issue create --body-file` に、生成した本文をそのまま渡す） |
| **変わった API（メソッド・パス）を Red テストが捕まえるか** | Red テストは関数を呼ぶ。メソッド・パスだけの変更は本文に前の版の API を書くが、ケースの変化には数えない |
| **`--red-check` が回した実装が、開発のリポジトリの実装か** | 走らせるのは正本リポジトリの根で読み込める実装。開発のリポジトリが別なら、そこで回すかは `CLAUDE.md` が決める |
| **タグを取らずに履歴だけ全部取った clone で、前の版が凍結しているか**（`--no-tags`） | 浅くないので、タグが無いことと見分けられない（`check-frozen.py` と同じ）。凍結していないと読み、崩れた前の版で止まる |
| **基準コミットが、仕様を書いた人の見ていた既存のシステムと同じか** | 書くのは生成した時点の HEAD。作業ツリーの commit していない変更は入らず、仕様を書いてから生成までに入ったコミットとも見分けない |
| **基準コミットから後の変化が仕様の前提を崩したか** | 本文に時点を残すだけ。点検は dev-loop の周の頭（dev-loop の `references/spec-gap.md`） |
| **`--bundle` でまとめた機能が、同じモジュール・同じ受入基準・同じデプロイ経路か** | 中間表現はデプロイ経路を持たず、`impl_module` は全体で 1 つ。機械が見るのは変化が揃うことだけで、選ぶのは scaffold を回す人 |
| **撤去の順（呼ぶ側を変えてから撤去する）** | `depends` は今の版の `called_by` から作る。撤去の機能は前の版の `called_by` しか持たないので、依存に出さない |
| **もう緑の追加・変更が、中間表現の書き起こしの誤りか** | 前の版の実装がもう満たすケースは名指しで知らせるだけ（0）。Red テストがその変化を判別しないのが誤りかは意味の問題で、`scaffold` スキルの手順 4 で利用者に示す |
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import keyword
import math
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 置き場所（`references/tree.md`・`references/versions.md` の写し）
DOCS = "docs"
# 重ね合わせた全体の置き場所（`merge-versions.py docs build/merged` が書く場所。このスクリプトは書かない）
MERGED_DIR = "build/merged"
# 撤去の本文が指す、前の版 v<n-1> の全体の置き場所（`build/merged/` を前の版で上書きさせない）
PREVIOUS_DIR = "build/merged-v{}"
# 重ね合わせた全体の根からのパス
QA_PATH = "shared/qa.csv"
SPEC_DIR = "spec"
IR_PATH = "spec/spec_ir.json"
OUT_DIR = "scaffold"
ISSUES_DIR = "build/scaffold/issues"

# `references/spec-ir.md` の写し
IR_VERSION = 1
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
TYPES = ("string", "integer", "number", "boolean")
# `\d` は全角や他の文字体系の数字にも合うので使わない（`check-qa-csv.py` と同じ理由）
FEATURE_ID = re.compile(r"F-[0-9]{3,}")
NAME = re.compile(r"[a-z][a-z0-9_]*")
ERROR_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
# 正常時の出力の項目に使えない名前（失敗の形 `{"error": …}` と見分けられないため）
RESERVED_OUTPUT = "error"
DEFAULT_IMPL_MODULE = "spec_impl"
# 引数を持たないメソッド（入力はクエリに載せる）
NO_BODY = ("GET", "DELETE")
# パスの変数（`/items/{id}`）。中身は `input` の項目名でなければならない
PATH_VAR = re.compile(r"\{([^{}]*)\}")

# `references/handoff-issue.md` の写し
HANDOFF_MARKER = "<!-- spec-loop-handoff: v3 -->"
FEATURE_MARKER = "<!-- spec-loop-feature: {} -->"
CHANGE_MARKER = "<!-- spec-loop-change: {}; base={} -->"
ADD, MODIFY, REMOVE = "add", "modify", "remove"
NO_BASE = "none"
SECTIONS = ("## 仕様", "## 受入基準", "## Red テスト", "## Q&A の回答", "## 作らないもの", "## 仕様の穴を見つけたら")
# `## 作らないもの` の小見出し（#851）
NOT_BUILT = ("### 範囲の外", "### 次の版の候補", "### 性能予算")
# 範囲の外の行のうち、次の版で受け持つ候補の印（`references/spec-scope.md` の「範囲の文書」の写し）
NEXT_VERSION = "次の版の候補"
# 性能の要求を渡していない機能の既定（`references/nfr.md` の「既定の原則」）
NO_PERFORMANCE_BUDGET = ("要求なし——この Issue は性能の要求（数字のある予算）を渡していない。"
                         "速さのための最適化（キャッシュ・並列化・索引の追加など）をしない。最適化は、計測で予算を超えたと示せたときだけ。")
# ケースの変化（受入基準の表の `変化` の列）
CASE_ADDED, CASE_CHANGED, CASE_KEPT, CASE_REMOVED = "追加", "変更", "回帰", "削除"
# Red テストが「実装が無い」で落ちたときの文言の頭（生成する Red テストの `self.fail` と同じ）
MISSING = "未実装: "
# 実装の状態についての前提（#294）。scaffold の `SKILL.md`・`handoff-issue.md`・dev-loop の `spec-gap.md` は
# この 2 つをそのまま持つ（`scripts/test-scaffold.py` が突き合わせる）。本文は `KEPT_GREEN` を持つ
PREMISE = "Red テストと受入基準は、実装が前の版の状態にあることを前提にしない"
KEPT_GREEN = "周の前に緑だった Red テストが、周の後も緑のままであること"
# 仕様の基準コミット（#874。`references/handoff-issue.md` の「基準コミット」の写し）——本文の `## 仕様` の行の頭と、
# 記録できなかったときの文言。dev-loop の `spec-gap.md` もこの 2 つをそのまま持つ（`scripts/test-scaffold.py` が突き合わせる）
BASE_COMMIT = "- 基準コミット: "
BASE_UNRECORDED = "記録していない"
# 仮回答の印（#875。`references/handoff-issue.md` の「仮回答の印」の写し）——本文の `## 仕様` の行の頭と、受入基準の表の
# Q&A の列で `暫定反映` の No に付ける印。`rebuild-scope.py` と dev-loop の `spec-gap.md` もこの 2 つをそのまま持つ
# （`scripts/test-scaffold.py`・`scripts/test-rebuild-scope.py` が突き合わせる）
PROVISIONAL_LINE = "- 仮回答: "
PROVISIONAL_CELL = "（暫定）"
# まとめた本文（#876。`references/handoff-issue.md` の「まとめた本文」の写し）——2 行目の印・ファイル名・部分の区切り。
# dev-loop の `spec-gap.md` も印をそのまま持つ（`scripts/test-scaffold.py` が突き合わせる）
BUNDLE_MARKER = "<!-- spec-loop-bundle: {} -->"
BUNDLE_FILE = "bundle-{}.md"
BUNDLE_RULE = "---"
# コミットの名前（SHA-1 の 40 桁か SHA-256 の 64 桁）
COMMIT_ID = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")

# 生成したファイルの印。**これを持つファイルだけを、消してよい・古いと言ってよい生成物に数える**
GENERATED = "spec-loop scaffold が生成（手で直さない。spec_ir.json を直して作り直す）"

PY_TYPES = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}
# 項目に null を許す印（`"nullable": true`。`references/spec-ir.md` の「項目」の写し）
NULLABLE = "nullable"
# 機能を呼ぶ機能の id の配列（任意。`references/spec-ir.md` の「呼ばれる機能」。#609）
CALLED_BY = "called_by"
# 機能に関わる範囲の外の行の原文の配列（任意。`references/spec-ir.md` の「作らないもの」。#851）
OUT_OF_SCOPE = "out_of_scope"
# 機能に効く性能の要求の行の `No` の配列（任意。`references/spec-ir.md` の「性能の要求」。#852）
NFR = "nfr"
# 呼ぶ側の分岐の書き起こし（任意。`references/spec-ir.md` の「呼ぶ側の分岐」。#855）——分岐の名前 → 見せるもの（`shows`）か
# 該当なし（`none`）。行ごと該当なしは `none` だけ。分岐の名前は `references/spec-ir.md` の分岐の表の写し
BRANCHES_KEY = "branches"
SHOWS = "shows"
NONE = "none"
BRANCHES = ("入力が欠ける", "入力が遅れる", "入力の順が崩れる", "呼ぶ処理が失敗する", "呼ぶ処理がやり直される", "呼ぶ処理が再起動する", "量が上限を超える", "量が重なる")
# 課題一覧（案）——Issue の本文と同じ場所に置く（`references/tree.md` の「生成物の置き場所」。#855）
PROPOSALS = "proposals.md"
# 性能の要求の表（重ねた全体の中の場所）と、その列・指標・単位（`references/nfr.md` の写し）
NFR_PATH = "shared/nfr.csv"
NFR_COLUMNS = ("No", "対象", "指標", "上限", "単位", "条件", "根拠")
NFR_ID = re.compile(r"N-[0-9]{3,}")
METRICS = ("p50", "p95", "p99", "最大")
NFR_UNIT = "ms"
# 上限（正の数。生成する性能テストにそのまま Python の数として書くので、この形だけを許す——先頭の 0 の付いた整数部 `0300` は Python の数にならず、
# 4300 桁を超える整数は Python が読まない。整数部は 9 桁・小数部は 6 桁まで）
LIMIT = re.compile(r"(0|[1-9][0-9]{0,8})(\.[0-9]{1,6})?")
# 性能テストの置き場所（`scaffold/` の中）と、1 回のテストで実装を呼ぶ回数
PERF_DIR = "perf"
PERF_CALLS = 200


class Unjudged(Exception):
    """判定していない（2）。"""


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


spec_exit = _load("check_spec_exit", "check-spec-exit.py")
qa = spec_exit.pptx.qa
versions = _load("merge_versions", "merge-versions.py")
# 内部の層の Q&A 表の、重ねた全体の中の場所（`merge-versions.py` のもの。写さない——#353）
INTERNAL_QA_PATH = versions.INTERNAL_QA_PATH
# 範囲の文書の置き場所と「範囲の外」の節の読み方は `build-proposal.py` のもの（写さない——#851）
proposal = _load("build_proposal", "build-proposal.py")
SCOPE_PATH = proposal.SCOPE_PATH
# 比べ方は `diff-versions.py` のもの（`compare_maps` は純粋な関数。重ねるのはこのスクリプトの `versions`）
diffs = _load("diff_versions", "diff-versions.py")
# リリースのタグの命名は `check-frozen.py` のもの（`releases`。写さない）
frozen = _load("check_frozen", "check-frozen.py")


def merged(path: str) -> str:
    """重ね合わせた全体の中のパスを、利用者が開ける形（`build/merged/…`）で書く。"""
    return f"{MERGED_DIR}/{path}"


# ---------------------------------------------------------------- 中間表現を検査する

def one_line(value) -> bool:
    """空でない 1 行の文字列か（生成するコードのコメントと表のセルに載せるので、制御文字を許さない）。"""
    return (isinstance(value, str) and value.strip() != ""
            and not any(unicodedata.category(c) == "Cc" for c in value))


def module_name(value) -> bool:
    return isinstance(value, str) and all(NAME.fullmatch(part) and not keyword.iskeyword(part)
                                          for part in value.split("."))


def surrogates(obj, where: str = "spec_ir.json") -> list[str]:
    """孤立したサロゲート（`"\\ud800"` は JSON として読めるが UTF-8 で書けない）を、キーと値の全部から探す。

    **書く途中で落ちて契約を切り詰めないため**、生成より前に、どの文字列にも許さない。
    """
    if isinstance(obj, str):
        return [f"{where}: UTF-8 で書けない文字（孤立したサロゲート）を含む"] if any(
            unicodedata.category(c) == "Cs" for c in obj) else []
    if isinstance(obj, dict):
        found = []
        for key, value in obj.items():
            found += surrogates(key, f"{where}（キー）") + surrogates(value, f"{where}.{key}")
        return found
    if isinstance(obj, list):
        return [p for i, v in enumerate(obj) for p in surrogates(v, f"{where}[{i}]")]
    return []


def keys_problem(where: str, obj, required: set[str], optional: set[str] = frozenset()) -> list[str]:
    if not isinstance(obj, dict):
        return [f"{where}: オブジェクトでない"]
    problems = []
    for key in sorted(required - obj.keys()):
        problems.append(f"{where}: `{key}` が無い")
    for key in sorted(obj.keys() - required - optional):
        problems.append(f"{where}: 決まりに無いキー `{key}`（書いても生成物に現れない）")
    return problems


def nullable(field) -> bool:
    """項目が null を許すか（`"nullable": true`）。書いていない項目は今までどおり null を拒む。"""
    return isinstance(field, dict) and field.get(NULLABLE) is True


def value_fits(kind: str, value) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        # `NaN`・`Infinity` は JSON として読めてしまうが、値として比べられない。
        # 整数は `math.isfinite` に渡さない——桁が大きいと float に直せず OverflowError で落ちる
        if isinstance(value, bool):
            return False
        return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))
    return isinstance(value, bool)


def check_fields(where: str, fields, at_least_one: bool, output: bool) -> list[str]:
    if not isinstance(fields, dict):
        return [f"{where}: オブジェクトでない"]
    problems = []
    if at_least_one and not fields:
        problems.append(f"{where}: 項目が 1 つも無い")
    for name, field in fields.items():
        at = f"{where}.{name}"
        if not NAME.fullmatch(name) or keyword.iskeyword(name):
            problems.append(f"{at}: 項目名の形に反する（英小文字で始まり英小文字・数字・_、Python の予約語でない）")
        if output and name == RESERVED_OUTPUT:
            problems.append(f"{at}: 正常時の出力に `{RESERVED_OUTPUT}` は使えない（失敗の形と見分けられない）")
        found = keys_problem(at, field, {"type"}, {"enum", NULLABLE})
        if found:
            problems += found
            continue
        if field["type"] not in TYPES:
            problems.append(f"{at}: 型 `{field['type']}` は決まりに無い（{' / '.join(TYPES)}）")
            continue
        # `false` は省くのと同じ意味になる——同じ意味の書き方を 2 つ作ると、機能の指紋が違う値になる
        if NULLABLE in field and field[NULLABLE] is not True:
            problems.append(f"{at}: `{NULLABLE}` は true だけを書く（null を許さないなら省く）")
        if "enum" in field:
            enum = field["enum"]
            if not isinstance(enum, list) or not enum:
                problems.append(f"{at}: enum は 1 つ以上の値の配列")
            elif not all(value_fits(field["type"], v) for v in enum):
                problems.append(f"{at}: enum の値が型 {field['type']} でない")
            # `json.dumps` の文字列で比べると `1` と `1.0` を別の値と数える
            elif any(a == b for i, a in enumerate(enum) for b in enum[i + 1:]):
                problems.append(f"{at}: enum の値が重複している")
    return problems


def check_values(where: str, values, fields: dict) -> list[str]:
    """`values` が `fields` の項目をちょうど全部、その型と enum で持つか（`nullable` の項目の `null` は型も enum も見ない）。"""
    if not isinstance(values, dict):
        return [f"{where}: オブジェクトでない"]
    problems = []
    for name in sorted(fields.keys() - values.keys()):
        problems.append(f"{where}: 項目 `{name}` が無い")
    for name in sorted(values.keys() - fields.keys()):
        problems.append(f"{where}: 決まりに無い項目 `{name}`")
    for name in sorted(values.keys() & fields.keys()):
        field, value = fields[name], values[name]
        if not isinstance(field, dict) or field.get("type") not in TYPES:
            continue  # 項目の定義の誤りは別に出ている
        if value is None and nullable(field):
            continue  # null は enum に書かない（enum の値は型に合うものだけ）
        if not value_fits(field["type"], value):
            problems.append(f"{where}.{name}: 型 {field['type']} でない（{json.dumps(value, ensure_ascii=False)}）")
        elif isinstance(field.get("enum"), list) and value not in field["enum"]:
            problems.append(f"{where}.{name}: enum に無い値（{json.dumps(value, ensure_ascii=False)}）")
    return problems


def check_qa_refs(where: str, refs, answered: dict[str, dict[str, str]], provisional: bool = False) -> list[str]:
    """`provisional`（`--provisional`。#875）なら `暫定反映` の行も指してよい——本文に仮回答の印を付けて渡す。"""
    if not isinstance(refs, list):
        return [f"{where}: 配列でない"]
    problems = []
    for no in refs:
        # 共有の表（`Q-`）と内部の表（`D-`）の番号。どちらの表の行も根拠に指せる（`references/spec-ir.md`。#339）。
        # 番号の形は `check-qa-csv.py` の定数を読む——起票元の印（#278）を写さない
        if not isinstance(no, str) or not (qa.NUMBER.fullmatch(no) or qa.is_internal_number(no)):
            problems.append(f"{where}: Q&A の No の形に反する（{no!r}）")
        elif no not in answered:
            problems.append(f"{where}: {no} は Q&A 表に無い")
        elif (state := answered[no]["状態"].strip()) != qa.DONE and not (provisional and qa.is_provisional(answered[no])):
            problems.append(f"{where}: {no} は状態が {state}（{qa.DONE}"
                            + (f"・{qa.PROVISIONAL}" if provisional else "") + " でない）")
    if len(set(map(str, refs))) != len(refs):
        problems.append(f"{where}: Q&A の No が重複している")
    return problems


def check_source(where: str, sources, whole: Path) -> list[str]:
    """`whole` は重ね合わせた全体の根。`source` はそこからのパス（`spec/order.md`）。"""
    if not isinstance(sources, list) or not sources:
        return [f"{where}: 仕様のファイルの配列（1 つ以上）でない"]
    problems = []
    spec_root = (whole / SPEC_DIR).resolve()
    for rel in sources:
        if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
            problems.append(f"{where}: 重ね合わせた全体の根からの相対パスでない（{rel!r}）")
            continue
        path = (whole / rel).resolve()
        if spec_root not in path.parents:
            problems.append(f"{where}: {rel} は {SPEC_DIR}/ の中に無い")
        elif any(part.startswith(".") for part in path.relative_to(spec_root).parts):
            # `check-spec-exit.py` は `.` で始まる場所を走査しない——そこを指すと未決定の印が関門を素通りする
            problems.append(f"{where}: {rel} は `.` で始まる場所にある（関門が未決定の印を見ない）")
        elif rel == IR_PATH or path == (whole / IR_PATH).resolve():
            problems.append(f"{where}: {rel} は中間表現そのもの（仕様の原文を指す）")
        elif not path.is_file():
            problems.append(f"{where}: {rel} が無い")
    return problems


def check_ref(where: str, ref, sources, whole: Path) -> list[str]:
    """ケースの `ref`——仕様の中でそのケースの元になった行の番号（決定表の `R-F10`・テストケースの `F1-5b` など。#465）。
    機能の `source` の原文のどれかに、前後に英数字・`_`・`-` が続かない形で現れなければ断る（別の番号の一部は数えない）。
    英数字には全角の英数字も含める（`R-F10ａ` は別の番号）。後ろに `.`・`/`・`:` と数字が続く形（`R-F10.1`・`R-F10/2`）も別の番号とみなし、
    数字で始まる `ref` は前に英数字と `.`・`/`・`:` が付く形（`R-F10.1` の `1`）を別の番号の一部とみなす——
    `R-F10.`（文末）・`R-F10.md`・`R-F10/R-F11` の `R-F11` は在ることにする。
    **値（入力・期待）が仕様と一致するかは見ない**——仕様の表の書式は spec-loop の決まりに無い。"""
    if not isinstance(ref, str) or not one_line(ref) or ref != ref.strip():
        return [f"{where}: 仕様の中の番号（1 行・前後に空白なし）でない: {ref!r}"]
    sub = r"(?<![A-Za-z0-9Ａ-Ｚａ-ｚ０-９][./:])" if ref[:1].isdigit() else ""
    pattern = re.compile(rf"(?<![A-Za-z0-9_\-Ａ-Ｚａ-ｚ０-９]){sub}{re.escape(ref)}(?![A-Za-z0-9_\-Ａ-Ｚａ-ｚ０-９]|[./:][0-9])")
    spec_root = (whole / SPEC_DIR).resolve()
    for rel in sources if isinstance(sources, list) else []:
        # 読むのは check_source が通す原文だけ（全体の根からの相対・spec/ の中）——外のファイルを読まない
        if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
            continue
        path = (whole / rel).resolve()
        if not path.is_relative_to(spec_root):
            continue
        try:
            if path.is_file() and pattern.search(path.read_text(encoding="utf-8")):
                return []
        except (OSError, UnicodeDecodeError, ValueError):
            continue  # 読めない原文は source の検査と未決定の印の関門が言う
    return [f"{where}: {ref} が仕様の原文（source）のどこにも無い——書き起こしの誤りか、仕様の後からの修正とのずれ"]


def path_vars(path: str) -> list[str]:
    return PATH_VAR.findall(path)


def check_path_vars(where: str, path: str, fields: dict, templates: dict[str, str]) -> list[str]:
    problems = []
    if "{" in PATH_VAR.sub("", path) or "}" in PATH_VAR.sub("", path):
        problems.append(f"{where}: 波括弧が対になっていない: {path!r}")
    names = path_vars(path)
    for name in sorted(set(names)):
        if name not in fields:
            problems.append(f"{where}: パスの変数 {{{name}}} が operation.input の項目に無い")
        if names.count(name) > 1:
            problems.append(f"{where}: パスの変数 {{{name}}} が重複している")
        if name in fields and nullable(fields[name]):
            problems.append(f"{where}: パスの変数 {{{name}}} は {NULLABLE} にできない（パスの値は null にならない）")
    # OpenAPI では変数の名前だけが違うパスは同じパスなので、並べると無効になる（メソッドが違っても）
    template = PATH_VAR.sub("{}", path)
    if templates.setdefault(template, path) != path:
        problems.append(f"{where}: {path} は {templates[template]} と変数の名前だけが違う（OpenAPI では同じパス）")
    return problems


def check_ir(ir, whole: Path, answered: dict[str, dict[str, str]], path_rules: bool = True,
             provisional: bool = False) -> list[str]:
    """`path_rules` が偽なら、パスの変数の決まり（#289）を当てない——前の版の中間表現だけ（#319。`classify`）。
    `provisional`（`--provisional`。#875）なら、`qa` が `暫定反映` の行を指してよい。"""
    problems = surrogates(ir)
    if problems:
        return problems + ["孤立したサロゲートを含む中間表現は、ほかの規則を見ない"]
    problems = keys_problem("spec_ir.json", ir, {"spec_ir_version", "title", "features"}, {"impl_module"})
    if problems and not isinstance(ir, dict):
        return problems
    # `1.0 == True == 1` なので、値ではなく型ごと見る
    if type(ir.get("spec_ir_version")) is not int or ir.get("spec_ir_version") != IR_VERSION:
        problems.append(f"spec_ir.json: spec_ir_version が {IR_VERSION} でない")
    if "impl_module" in ir and not module_name(ir["impl_module"]):
        problems.append(f"spec_ir.json: impl_module がモジュール名の形に反する: {ir['impl_module']!r}")
    if "title" in ir and not one_line(ir["title"]):
        problems.append("spec_ir.json: title が空か、1 行でない")
    features = ir.get("features")
    if not isinstance(features, list) or not features:
        problems.append("spec_ir.json: features が 1 つ以上の配列でない")
        return problems

    feature_ids, operation_ids, routes, case_ids = set(), set(), set(), set()
    templates = {}  # 変数の名前を消したパス → 最初に使ったパス
    type_names = {}  # pascal(operation.id) → 最初に使った operation.id
    for index, feature in enumerate(features):
        where = f"features[{index}]"
        found = keys_problem(where, feature, {"id", "title", "source", "qa", "operation", "cases"},
                             {CALLED_BY, OUT_OF_SCOPE, NFR, BRANCHES_KEY})
        if found:
            problems += found
            if not isinstance(feature, dict):
                continue
        fid = feature.get("id")
        if not isinstance(fid, str) or not FEATURE_ID.fullmatch(fid):
            problems.append(f"{where}: id の形に反する（F- に 3 桁以上の数字）: {fid!r}")
            fid = None
        elif fid in feature_ids:
            problems.append(f"{where}: id {fid} が重複している")
        else:
            feature_ids.add(fid)
            where = fid
        if "title" in feature and not one_line(feature["title"]):
            problems.append(f"{where}: title が空か、1 行でない")
        if "source" in feature:
            problems += check_source(f"{where}.source", feature["source"], whole)
        if "qa" in feature:
            problems += check_qa_refs(f"{where}.qa", feature["qa"], answered, provisional)
        if OUT_OF_SCOPE in feature:
            problems += check_out_of_scope(f"{where}.{OUT_OF_SCOPE}", feature[OUT_OF_SCOPE], whole)
        if NFR in feature:
            problems += check_nfr(f"{where}.{NFR}", feature[NFR], whole)
        if BRANCHES_KEY in feature:
            problems += check_branches(f"{where}.{BRANCHES_KEY}", feature, whole)

        op = feature.get("operation")
        fields_in, fields_out, errors = {}, {}, []
        if "operation" in feature:
            found = keys_problem(f"{where}.operation", op, {"id", "method", "path", "input", "output"}, {"errors"})
            problems += found
            if isinstance(op, dict):
                oid = op.get("id")
                if not isinstance(oid, str) or not NAME.fullmatch(oid) or keyword.iskeyword(oid):
                    problems.append(f"{where}.operation.id: 形に反する（英小文字で始まり英小文字・数字・_、Python の予約語でない）: {oid!r}")
                elif oid in operation_ids:
                    problems.append(f"{where}.operation.id: {oid} が重複している")
                elif pascal(oid) in type_names:
                    # `a_1` と `a1`・`foo_bar` と `foo__bar` は別の id だが、型の名前が同じになり上書きし合う
                    problems.append(f"{where}.operation.id: {oid} は {type_names[pascal(oid)]} と"
                                    f"同じ型の名前 {pascal(oid)}Input / {pascal(oid)}Output になる")
                else:
                    operation_ids.add(oid)
                    type_names[pascal(oid)] = oid
                method, path = op.get("method"), op.get("path")
                if method not in METHODS:
                    problems.append(f"{where}.operation.method: 決まりに無い（{' / '.join(METHODS)}）: {method!r}")
                if not isinstance(path, str) or not path.startswith("/") or not one_line(path):
                    problems.append(f"{where}.operation.path: / で始まる 1 行でない: {path!r}")
                # メソッドが決まりに無い（配列など）なら入口の重複は見ない——組にできず TypeError で落ちる
                elif method in METHODS and (method, path) in routes:
                    problems.append(f"{where}.operation: {method} {path} が重複している")
                elif method in METHODS:
                    routes.add((method, path))
                if "input" in op:
                    problems += check_fields(f"{where}.operation.input", op["input"], False, False)
                    fields_in = op["input"] if isinstance(op["input"], dict) else {}
                if path_rules and isinstance(path, str) and path.startswith("/") and one_line(path):
                    problems += check_path_vars(f"{where}.operation.path", path, fields_in, templates)
                if "output" in op:
                    problems += check_fields(f"{where}.operation.output", op["output"], True, True)
                    fields_out = op["output"] if isinstance(op["output"], dict) else {}
                errors = op.get("errors", [])
                if not isinstance(errors, list):
                    problems.append(f"{where}.operation.errors: 配列でない")
                    errors = []
                else:
                    for name in errors:
                        if not isinstance(name, str) or not ERROR_NAME.fullmatch(name):
                            problems.append(f"{where}.operation.errors: 名前の形に反する: {name!r}")
                    if len(set(map(str, errors))) != len(errors):
                        problems.append(f"{where}.operation.errors: 重複している")

        cases = feature.get("cases")
        if "cases" in feature and (not isinstance(cases, list) or not cases):
            problems.append(f"{where}.cases: 1 つ以上の配列でない")
            continue
        for cindex, case in enumerate(cases or []):
            at = f"{where}.cases[{cindex}]"
            found = keys_problem(at, case, {"id", "title", "input"}, {"expected", "error", "qa", "ref"})
            if found:
                problems += found
                if not isinstance(case, dict):
                    continue
            cid = case.get("id")
            if not isinstance(cid, str) or fid is None or not re.fullmatch(rf"{re.escape(fid)}-C[0-9]+", cid):
                problems.append(f"{at}: id の形に反する（<機能の id>-C<数字>）: {cid!r}")
            elif cid in case_ids:
                problems.append(f"{at}: id {cid} が重複している")
            else:
                case_ids.add(cid)
                at = cid
            if "title" in case and not one_line(case["title"]):
                problems.append(f"{at}: title が空か、1 行でない")
            if "input" in case:
                problems += check_values(f"{at}.input", case["input"], fields_in)
            if ("expected" in case) == ("error" in case):
                problems.append(f"{at}: expected と error のちょうど片方だけを書く")
            elif "expected" in case:
                problems += check_values(f"{at}.expected", case["expected"], fields_out)
            elif case["error"] not in errors:
                problems.append(f"{at}.error: operation.errors に無い: {case['error']!r}")
            if "qa" in case:
                problems += check_qa_refs(f"{at}.qa", case["qa"], answered, provisional)
            if "ref" in case:
                problems += check_ref(f"{at}.ref", case["ref"], feature.get("source"), whole)
    return problems + check_called_by(features)


# 表の区切りの行（`| --- | :-: |`・先頭の `|` の無い `--- | ---`）。**`|` を 1 つ以上含む**——単独の `---`（水平線）は区切りと読まない
TABLE_SEPARATOR = re.compile(r"\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?|\|\s*:?-+:?\s*\|")


def scope_rows(text: str) -> list[tuple[str, tuple[str, str] | None]] | None:
    """範囲の文書の「範囲の外」の節の行と、その行が表の行なら表の見出しの 2 行（見出しと区切り）。節が無ければ None。

    行は前後の空白を落とした原文で、範囲の文書での並びの順。**空の行・見出しの行・表の見出しと区切りの行は行に数えない**。
    **表は、`|` を含む行の次の行が区切りの行（`| --- |`・`--- | ---`）であるところから始まり**、`|` を含む空でない行が続くあいだ続く
    （先頭の `|` の無い表も表と読む。区切りの行の無い `|` の行の並びは表ではなく、ふつうの行）。
    """
    body = proposal.out_of_scope(text)
    if body is None:
        return None
    lines = [line.strip() for line in body]
    rows: list[tuple[str, tuple[str, str] | None]] = []
    header: tuple[str, str] | None = None  # 続いている表の見出しの 2 行
    index = 0
    while index < len(lines):
        line = lines[index]
        if header is not None and line and "|" in line:
            rows.append((line, header))
            index += 1
            continue
        header = None
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if "|" in line and "-" in following and TABLE_SEPARATOR.fullmatch(following):
            header = (line, following)
            index += 2
            continue
        if line and not proposal.heading_level(line):
            rows.append((line, None))
        index += 1
    return rows


def check_out_of_scope(where: str, picked, whole: Path) -> list[str]:
    """機能の `out_of_scope`（#851。`references/spec-ir.md` の「作らないもの」）。

    **挙げた行が、範囲の文書の「範囲の外」の節に原文のまま在ること**だけを見る——その機能に関わるかは書き起こす側の判断。
    """
    if not isinstance(picked, list) or not picked:
        return [f"{where}: 範囲の外の行の原文の 1 つ以上の配列でない"]
    problems = []
    if any(not isinstance(row, str) or not one_line(row) or row != row.strip() for row in picked):
        problems.append(f"{where}: 前後に空白の無い 1 行の文字列でない行がある")
    if len(set(map(str, picked))) != len(picked):
        problems.append(f"{where}: 重複している")
    if problems:
        return problems
    path = whole / SCOPE_PATH
    if not path.is_file():
        return [f"{where}: 範囲の文書 {merged(SCOPE_PATH)} が無い"]
    try:
        rows = scope_rows(path.read_bytes().decode("utf-8-sig"))
    except UnicodeDecodeError:
        return [f"{where}: 範囲の文書 {merged(SCOPE_PATH)} を UTF-8 として読めない"]
    if rows is None:
        return [f"{where}: 範囲の文書 {merged(SCOPE_PATH)} に見出しに「{proposal.OUT_OF_SCOPE}」を含む節が無い"]
    present = {text for text, _ in rows}
    return [f"{where}: 範囲の文書の「{proposal.OUT_OF_SCOPE}」の節に、この行が原文のまま無い"
            f"（表の見出し・区切りの行は挙げない）: {row!r}" for row in picked if row not in present]


def nfr_rows(text: str) -> tuple[list[str] | None, dict[str, list[tuple[dict[str, str], int]]]]:
    """性能の要求の表の (見出しの列, {No: [(行, セルの数), …]})。表が空なら見出しは None。空の行は数えない。"""
    table = list(csv.reader(io.StringIO(text)))
    if not table:
        return None, {}
    header = [cell.strip() for cell in table[0]]
    found: dict[str, list[tuple[dict[str, str], int]]] = {}
    for cells in table[1:]:
        if not any(cell.strip() for cell in cells):
            continue
        row = {name: (cells[i].strip() if i < len(cells) else "") for i, name in enumerate(header)}
        found.setdefault(row.get("No", ""), []).append((row, len(cells)))
    return header, found


def nfr_row_problems(row: dict[str, str], width: int) -> list[str]:
    """性能の行の形（`references/nfr.md` の「列」と「指標」）。"""
    problems = []
    if width != len(NFR_COLUMNS):
        problems.append(f"列の数が見出しと違う（{width} 列）")
    for name in ("対象", "条件", "根拠"):
        if not one_line(row.get(name, "")):
            problems.append(f"{name} が空か、1 行でない")
    if row.get("指標") not in METRICS:
        problems.append(f"指標が {'・'.join(METRICS)} のどれでもない: {row.get('指標')!r}")
    limit = row.get("上限", "")
    if not LIMIT.fullmatch(limit) or float(limit) <= 0:
        problems.append(f"上限が正の数の形でない（整数部は先頭に 0 を付けない 9 桁まで・小数部は 6 桁まで）: {limit!r}")
    if row.get("単位") != NFR_UNIT:
        problems.append(f"単位が {NFR_UNIT} でない: {row.get('単位')!r}")
    return problems


def check_nfr(where: str, refs, whole: Path) -> list[str]:
    """機能の `nfr`（#852。`references/spec-ir.md` の「性能の要求」）。**指した行だけ**を見る。"""
    if not isinstance(refs, list) or not refs:
        return [f"{where}: 性能の要求の行の No の 1 つ以上の配列でない"]
    problems = [f"{where}: No の形に反する（N- に 3 桁以上の数字）: {no!r}"
                for no in refs if not isinstance(no, str) or not NFR_ID.fullmatch(no)]
    if len(set(map(str, refs))) != len(refs):
        problems.append(f"{where}: 重複している")
    if problems:
        return problems
    path = whole / NFR_PATH
    # 綴りどおりの名前で在ること——大文字小文字を区別しないファイルシステムでは `NFR.csv` も開けるが、生成は重ねた結果を綴りどおりに引く
    if not path.is_file() or path.name not in {child.name for child in path.parent.iterdir()}:
        return [f"{where}: 性能の要求の表 {merged(NFR_PATH)} が無い"]
    try:
        header, found = nfr_rows(path.read_bytes().decode("utf-8-sig"))
    except UnicodeDecodeError:
        return [f"{where}: 性能の要求の表 {merged(NFR_PATH)} を UTF-8 として読めない"]
    if header != list(NFR_COLUMNS):
        return [f"{where}: 性能の要求の表 {merged(NFR_PATH)} の見出しの行が {','.join(NFR_COLUMNS)} でない"]
    for no in refs:
        rows = found.get(no, [])
        if len(rows) != 1:
            problems.append(f"{where}: 性能の要求の表 {merged(NFR_PATH)} に {no} の行が"
                            + ("無い" if not rows else f" {len(rows)} 行ある"))
            continue
        problems += [f"{where}: {no}: {problem}" for problem in nfr_row_problems(*rows[0])]
    return problems


def source_lines(sources, whole: Path) -> set[str] | None:
    """機能の `source` の原文の行（前後の空白を落とした）。`source` が配列でなければ None（`check_source` が言う）。

    読むのは `check_ref` と同じく、重ね合わせた全体の `spec/` の中の相対パスだけ——外のファイルを読まない。読めない原文は飛ばす。
    """
    if not isinstance(sources, list):
        return None
    lines: set[str] = set()
    spec_root = (whole / SPEC_DIR).resolve()
    for rel in sources:
        if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
            continue
        path = (whole / rel).resolve()
        if not path.is_relative_to(spec_root):  # spec/ の外は読まない
            continue
        try:
            if path.is_file():
                lines |= {line.strip() for line in path.read_bytes().decode("utf-8-sig").splitlines()}
        except (OSError, UnicodeDecodeError, ValueError):
            continue  # 読めない原文は source の検査と未決定の印の関門が言う
    return lines


def check_branches(where: str, feature: dict, whole: Path) -> list[str]:
    """呼ぶ側の分岐（#855。`references/spec-ir.md` の「呼ぶ側の分岐」）。

    分岐の名前（`BRANCHES`）→ `{"shows": 見せるもの}` か `{"none": 該当なしの理由}`。行ごと該当なしは `{"none": …}` だけ。
    **値は仕様の原文の 1 行**——機能の `source` のどれかに、前後の空白を落として一致する行が在ること**だけ**を見る
    （その行がその分岐を決めているかは書き起こす側の判断）。**呼ばれる関数（`called_by` を持つ機能）には書かない**——分岐は呼ぶ入口に書く。
    """
    branches = feature[BRANCHES_KEY]
    if CALLED_BY in feature:
        return [f"{where}: 呼ばれる関数（{CALLED_BY} を持つ機能）には書かない——呼ぶ側の分岐は、呼ぶ入口の機能に書く"]
    if not isinstance(branches, dict) or not branches:
        return [f"{where}: 分岐の名前から {{\"{SHOWS}\": 原文}} か {{\"{NONE}\": 原文}} への 1 つ以上のオブジェクトでない"]
    problems, texts = [], []
    if NONE in branches:
        if len(branches) != 1:
            return [f"{where}: 行ごとの該当なし（{NONE}）と分岐を一緒に書いている"]
        texts.append((f"{where}.{NONE}", branches[NONE]))
    else:
        for name, value in branches.items():
            if name not in BRANCHES:
                problems.append(f"{where}: 分岐の名前でない（{' / '.join(BRANCHES)}）: {name!r}")
            elif not isinstance(value, dict) or len(value) != 1 or next(iter(value)) not in (SHOWS, NONE):
                problems.append(f"{where}.{name}: {{\"{SHOWS}\": 原文}} か {{\"{NONE}\": 原文}} のどちらか 1 つでない")
            else:
                key = next(iter(value))
                texts.append((f"{where}.{name}.{key}", value[key]))
    good = []
    for at, text in texts:
        if not isinstance(text, str) or not one_line(text) or text != text.strip():
            problems.append(f"{at}: 前後に空白の無い 1 行の文字列でない")
        else:
            good.append((at, text))
    lines = source_lines(feature.get("source"), whole)
    if lines is None:
        return problems
    return problems + [f"{at}: 仕様の原文（source）に、この行が原文のまま無い: {text!r}" for at, text in good if text not in lines]


def check_called_by(features: list) -> list[str]:
    """呼ばれる機能の `called_by`（#609。`references/spec-ir.md` の「呼ばれる機能」）。

    **呼ぶ機能は、重ね合わせた全体の中間表現に在る機能でなければならない**——関数だけを書き起こして、それを呼ぶ入口
    （API・画面・バッチ）がどの機能にも無いまま Issue にする形を止める。呼ぶ関係は循環しない（循環すると、どの機能も入口にならない）。
    **書き起こす側が関数を入口と偽れば（`called_by` を書かなければ）通る**——欄は任意で、機械は申告の整合だけを見る。
    """
    problems, graph = [], {}
    ids = {f.get("id") for f in features if isinstance(f, dict)}
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or CALLED_BY not in feature:
            continue
        fid = feature.get("id")
        where = f"{fid if isinstance(fid, str) and FEATURE_ID.fullmatch(fid) else f'features[{index}]'}.{CALLED_BY}"
        callers = feature[CALLED_BY]
        if not isinstance(callers, list) or not callers:
            problems.append(f"{where}: 呼ぶ機能の id の 1 つ以上の配列でない")
            continue
        good = []
        for caller in callers:
            if not isinstance(caller, str) or not FEATURE_ID.fullmatch(caller):
                problems.append(f"{where}: id の形に反する（F- に 3 桁以上の数字）: {caller!r}")
            elif caller == fid:
                problems.append(f"{where}: 自分自身 {caller} を呼ぶ機能に挙げている")
            elif caller not in ids:
                problems.append(f"{where}: 呼ぶ機能 {caller} が中間表現に無い——呼ぶ入口（API・画面・バッチ）も機能として"
                                "書き起こす。仕様が呼ぶ側を書いていなければ、仕様が確定していない（spec-review に戻す）")
            else:
                good.append(caller)
        if len(set(map(str, callers))) != len(callers):
            problems.append(f"{where}: 重複している")
        if isinstance(fid, str):
            graph[fid] = good
    # 呼ぶ関係の循環——辿った先に、呼ばれない機能（入口）が無い
    state: dict[str, int] = {}  # 1: 辿っている途中・2: 済んだ

    def visit(node: str) -> str | None:
        state[node] = 1
        for nxt in graph.get(node, []):
            if state.get(nxt) == 1:
                return nxt
            if nxt not in state and (found := visit(nxt)):
                return found
        state[node] = 2
        return None

    for node in sorted(graph):
        if node not in state and (looped := visit(node)):
            problems.append(f"{looped}.{CALLED_BY}: 呼ぶ関係が循環している（辿った先に、呼ばれない入口の機能が無い）")
    return problems


# ---------------------------------------------------------------- 入力を読む

def read_answered(path: Path) -> dict[str, dict[str, str]]:
    """Q&A 表の全行を No で引けるようにする（関門を通った後に呼ぶので、表は検査済み）。"""
    return parse_answered(path.read_text(encoding="utf-8-sig"))


def parse_answered(text: str) -> dict[str, dict[str, str]]:
    """Q&A 表の中身を No → 行にする（`read_answered` と同じ。重ねた全体のバイトからも読む）。"""
    reader = csv.reader(io.StringIO(text, newline=""))
    next(reader)
    rows = {}
    for fields in reader:
        if any(f.strip() for f in fields):
            row = dict(zip(qa.COLUMNS, fields))
            rows[row["No"].strip()] = row
    return rows


# dataclass は使わない——importlib で読み込むと sys.modules に無く、dataclass が落ちる（`diff-versions.py` と同じ）
class Loaded:
    """重ね合わせた全体から読んだもの。"""

    def __init__(self, ir: dict, raw: bytes, answered: dict, number: int, docs: Path, scope: bytes | None = None,
                 nfr: bytes | None = None) -> None:
        self.ir = ir
        self.provisional = False  # `--provisional`（#875）——前の版の時点の判定にも同じ旗を当てる（`classify`）
        self.scope = scope  # 範囲の文書（`spec/scope.md`）のバイト。無ければ None
        self.nfr = nfr  # 性能の要求の表（`shared/nfr.csv`）のバイト。無ければ None
        self.raw = raw  # 中間表現のバイト（本文の指紋は機能単位なので、これ全体の sha256 は使わない。#290）
        self.answered = answered  # Q&A の行（No → 行）
        self.number = number  # 重ねた最後の版の番号
        self.docs = docs


def load(repo: Path, upto: int | None = None, provisional: bool = False) -> tuple[int, list[str], Loaded | None]:
    """(終了コード, 出力する行, 読んだもの) を返す。

    `docs/` の版を**メモリ上で**重ね合わせ（`merge-versions.py` の `merge`。同じバイト）、一時ディレクトリに書いて、
    関門・中間表現の検査をそこに当てる。**`build/merged/` には書かない**——`--check`・`--dry-run` は何も書かない。
    `upto` を渡せば v<upto> までを重ねる（無い版なら判定しない）。`provisional` は `--provisional`（`read_whole`。#875）。
    """
    docs = repo / DOCS
    if not docs.is_dir():
        raise Unjudged(f"{docs}: ディレクトリが無い（版は {DOCS}/v1/ から置く。references/versions.md）")
    # 版が 1 つも無い（版に分ける前の構成）は、決まりに反するのではなく移していない——判定しない
    probe: list[str] = []
    try:
        if not versions.find_versions(docs, probe) and not probe:
            raise Unjudged(f"{docs}: 版（v1 など）が 1 つも無い（版に分ける前の構成なら "
                           "references/versions.md の「移し方」で移す）。判定していない")
    except versions.Unreadable as exc:
        raise Unjudged(f"{exc}。重ね合わせていない")
    try:
        problems, found, _, rendered = versions.merge(docs, upto)
    except versions.Unreadable as exc:
        raise Unjudged(f"{exc}。重ね合わせていない")
    except RecursionError:
        # 版の中間表現の入れ子が深すぎて JSON として読めない（`merge-versions.py` は捕まえない）
        raise Unjudged("版の中間表現を読めない（入れ子が深すぎる）。重ね合わせていない")
    if problems:
        return 1, problems + ["版の重ね合わせが決まりに反する（references/versions.md）。生成しない"], None
    if IR_PATH not in rendered:
        raise Unjudged(f"重ね合わせた全体に {IR_PATH} が無い（どの版にも中間表現が無い）。判定していない")
    code, lines, ir, answered = read_whole(rendered, gate=True, provisional=provisional)
    if code:
        return code, lines, None
    number = upto if upto is not None else len(found)
    loaded = Loaded(ir, rendered[IR_PATH], answered, number, docs, rendered.get(SCOPE_PATH), rendered.get(NFR_PATH))
    loaded.provisional = provisional
    return 0, [], loaded


def read_whole(rendered: dict[str, bytes], gate: bool, provisional: bool = False) -> tuple[int, list[str], dict | None, dict]:
    """重ね合わせた全体を一時ディレクトリに置き、(終了コード, 出力する行, 中間表現, Q&A の行) を返す。

    `gate` なら関門（条件 1）も当てる——前の版の全体には当てない。**前の版がその時点で関門を通ったとは限らない**が、
    通っていない（`反映済み` でない Q&A が残る）前の版は、ここに来る前に `classify` が Q&A の状態を直接見て止める
    （凍結していれば信じずに全部を追加にする。#361）。ここに来る前の版は Q&A が全部 `反映済み` で、残る条件 1 の
    未決定の印は、印の決まりが版をまたいで変わりうるので前の版には当てない。
    パスの変数の決まりも前の版には当てない（#319）——#289 より前の scaffold が通した版は、凍結していれば直せず、
    前の版の中間表現からは OpenAPI を作らない（ケースの比較・前の版の Red テスト・Issue の本文の前の版を指す行にしか使わない）。

    **`provisional`（`--provisional`。#875）なら、`暫定反映` の行が残っても止めず、中間表現から指してよい**——
    ただし `gate` のとき、**どの機能・ケースの `qa` からも指されない `暫定反映` の行が残れば止める**（1）。
    指していなければ、その仮回答がどの Issue に効くかを本文に書けない（止めていた理由そのもの。#325）。
    """
    with tempfile.TemporaryDirectory() as tmp:
        whole = Path(tmp)
        for rel, data in rendered.items():
            versions.put(whole / rel, data)

        def shown(lines: list[str]) -> list[str]:
            # 一時ディレクトリの名前ではなく、利用者が `merge-versions.py` で作れる場所で言う
            return [line.replace(str(whole), MERGED_DIR) for line in lines]

        if gate:
            code, lines = spec_exit.check(whole / QA_PATH, whole / SPEC_DIR)
            if code:
                return code, shown(lines) + ["関門（仕様レビューを抜ける条件 1）を通らない。生成しない"], None, {}
        raw = rendered[IR_PATH]
        try:
            ir = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            raise Unjudged(f"{merged(IR_PATH)}: 中間表現を読めない（{exc.__class__.__name__}: {exc}）")
        answered = {}
        for path in (QA_PATH, INTERNAL_QA_PATH):
            if (whole / path).is_file():
                answered.update(read_answered(whole / path))
        if gate:
            # 暫定の回答は利用者が確かめていない。scaffold の経路はサインオフの照合を通らないので、
            # 中間表現が指すかどうかに依らず、残っていれば止める——指さない機能の仕様にも反映されている（抜ける条件 1 とは別の定義。#325）
            held = [no for no, row in answered.items() if qa.is_provisional(row)]
            if held and not provisional:
                return 1, shown([f"{no}: 状態が {qa.PROVISIONAL}（利用者の確認待ち）" for no in held]) + [
                    f"{merged(QA_PATH)} に {qa.PROVISIONAL} の行が {len(held)} 件残る。"
                    "利用者に確かめてもらうまで生成しない（/spec-loop:req-loop）"], None, {}
        problems = check_ir(ir, whole, answered, path_rules=gate, provisional=provisional)
        if gate and provisional and not problems:
            cited = cited_qa(ir)
            uncited = [no for no in held if no not in cited]
            if uncited:
                return 1, shown([f"{no}: 状態が {qa.PROVISIONAL}（利用者の確認待ち）なのに、中間表現のどの機能・ケースの qa からも"
                                 "指していない" for no in uncited]) + [
                    f"--provisional でも、指していない {qa.PROVISIONAL} の行が {len(uncited)} 件残る——その仮回答がどの Issue に"
                    "効くかを本文に書けない。効く機能・ケースの qa から指すか、利用者に確かめてもらう（/spec-loop:req-loop）。"
                    "生成しない"], None, {}
    if problems:
        return 1, problems + [f"中間表現が決まりに反する（{len(problems)} 件）。生成しない"], None, {}
    return 0, [], ir, answered


def cited_qa(ir: dict) -> set[str]:
    """中間表現の機能とケースの `qa` が指す No の全部（検査を通った後に呼ぶ）。"""
    return {no for f in features_of(ir) for no in f["qa"] + [n for c in f["cases"] for n in c.get("qa", [])]}


# ---------------------------------------------------------------- 生成する

def pascal(name: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in name.split("_") if part)


def literal(values: dict) -> str:
    return "{" + ", ".join(f"{k!r}: {values[k]!r}" for k in sorted(values)) + "}"


def schema_of(field: dict) -> dict:
    out = {"type": field["type"]}
    if "enum" in field:
        out["enum"] = field["enum"]
    if nullable(field):
        # JSON Schema の enum は null を拒むので、`type` に足すだけでなく enum にも足す
        out["type"] = [field["type"], "null"]
        if "enum" in field:
            out["enum"] = field["enum"] + [None]
    return out


def object_schema(fields: dict) -> dict:
    return {"type": "object", "required": sorted(fields), "additionalProperties": False,
            "properties": {name: schema_of(fields[name]) for name in sorted(fields)}}


def features_of(ir: dict) -> list[dict]:
    return sorted(ir["features"], key=lambda f: f["id"])


def openapi(ir: dict) -> str:
    paths, schemas = {}, {}
    for feature in features_of(ir):
        op = feature["operation"]
        base = pascal(op["id"])
        schemas[f"{base}Input"] = object_schema(op["input"])
        schemas[f"{base}Output"] = object_schema(op["output"])
        entry = {"operationId": op["id"], "summary": f"{feature['id']}: {feature['title']}"}
        in_path = path_vars(op["path"])
        rest = {name: op["input"][name] for name in op["input"] if name not in in_path}
        parameters = [{"name": name, "in": "path", "required": True, "schema": schema_of(op["input"][name])}
                      for name in in_path]
        if op["method"] in NO_BODY:
            parameters += [{"name": name, "in": "query", "required": True, "schema": schema_of(rest[name])}
                           for name in sorted(rest)]
        if parameters or op["method"] in NO_BODY:
            entry["parameters"] = parameters
        if op["method"] not in NO_BODY and rest:
            # パスの変数はボディに重ねない——変数を持たない入口は前と同じく入力の型そのものを指す
            body = f"{base}Input" if not in_path else f"{base}Body"
            if in_path:
                schemas[body] = object_schema(rest)
            entry["requestBody"] = {"required": True, "content": {"application/json": {
                "schema": {"$ref": f"#/components/schemas/{body}"}}}}
        responses = {"200": {"description": "正常", "content": {"application/json": {
            "schema": {"$ref": f"#/components/schemas/{base}Output"}}}}}
        if op.get("errors"):
            schemas[f"{base}Error"] = {"type": "object", "required": ["error"], "additionalProperties": False,
                                       "properties": {"error": {"type": "string", "enum": op["errors"]}}}
            responses["400"] = {"description": "失敗", "content": {"application/json": {
                "schema": {"$ref": f"#/components/schemas/{base}Error"}}}}
        entry["responses"] = responses
        paths.setdefault(op["path"], {})[op["method"].lower()] = entry
    doc = {
        "openapi": "3.1.0",
        "info": {"title": ir["title"], "version": f"spec-ir-{IR_VERSION}",
                 "description": GENERATED},
        "paths": {path: paths[path] for path in sorted(paths)},
        "components": {"schemas": {name: schemas[name] for name in sorted(schemas)}},
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def py_type(field: dict) -> str:
    if "enum" in field:
        name = "Literal[" + ", ".join(repr(v) for v in field["enum"]) + "]"
    else:
        name = PY_TYPES[field["type"]]
    return name + " | None" if nullable(field) else name


def typed_dict(name: str, fields: dict) -> list[str]:
    lines = [f"class {name}(TypedDict):"]
    lines += [f"    {field}: {py_type(fields[field])}" for field in sorted(fields)] or ["    pass"]
    return lines + ["", ""]


def types_py(ir: dict) -> str:
    lines = [f"# {GENERATED}", f"# {ir['title']} の入出力の型", "from __future__ import annotations", "",
             "from typing import Literal, TypedDict", "", ""]
    for feature in features_of(ir):
        op = feature["operation"]
        base = pascal(op["id"])
        lines.append(f"# {feature['id']}: {feature['title']}")
        lines += typed_dict(f"{base}Input", op["input"])
        lines += typed_dict(f"{base}Output", op["output"])
        if op.get("errors"):
            lines += typed_dict(f"{base}Error", {"error": {"type": "string", "enum": op["errors"]}})
    return "\n".join(lines).rstrip("\n") + "\n"


def case_order(case: dict) -> tuple[int, str]:
    # `int()` は桁が多すぎると ValueError で落ちる——桁数と文字列で数の順に並べる
    digits = case["id"].rsplit("C", 1)[1].lstrip("0")
    return len(digits), digits


def test_file(feature: dict) -> str:
    return f"test_{feature['id'].lower().replace('-', '_')}.py"


def test_method(case: dict) -> str:
    return f"test_{case['id'].lower().replace('-', '_')}"


def test_class(feature: dict) -> str:
    return "Test" + feature["id"].replace("-", "")


def output_types(op: dict) -> dict:
    """正常時の出力の項目と、失敗の形（`error`）の型。Red テストが値と一緒に型を見るのに使う。"""
    types = {name: field["type"] for name, field in op["output"].items()}
    types[RESERVED_OUTPUT] = "string"
    return types


# 生成するテスト（Red テストと性能テスト）が実装を探す関数と、無いときの失敗（`MISSING` で始まる）——2 つのテストで同じ
IMPLEMENTATION = (
    "def implementation():",
    "    try:",
    "        module = importlib.import_module(IMPL_MODULE)",
    "    except ModuleNotFoundError as exc:",
    "        if exc.name is not None and (exc.name == IMPL_MODULE or IMPL_MODULE.startswith(exc.name + \".\")):",
    "            return None",
    "        raise",
    "    return getattr(module, OPERATION, None)",
)
MISSING_FAIL = "            self.fail(f\"未実装: {IMPL_MODULE}.{OPERATION} が無い\")"


def red_test(feature: dict, impl_module: str) -> str:
    op = feature["operation"]
    # null を許す出力の項目。無い機能の Red テストは、`nullable` を足す前と 1 バイトも変えない（既存の `scaffold/` を古くしない）
    allow_null = sorted(name for name, field in op["output"].items() if nullable(field))
    lines = [
        f"# {GENERATED}",
        f"# {feature['id']}: {feature['title']} の Red テスト",
        f"# 実装は `{impl_module}` モジュールの `{op['id']}(**input) -> dict`。失敗は {{\"error\": \"<名前>\"}} を返す。",
        "# 実装が無ければ、エラーではなく失敗になる。",
        "from __future__ import annotations",
        "",
        "import importlib",
        "import unittest",
        "",
        f"IMPL_MODULE = {impl_module!r}",
        f"OPERATION = {op['id']!r}",
        f"OUTPUT_TYPES = {literal(output_types(op))}",
        *([f"NULLABLE = {tuple(allow_null)!r}"] if allow_null else []),
        "",
        "",
        "def type_fits(kind, value):",
        "    # `assertEqual` は `True == 1 == 1.0` を等しいと見るので、型は別に見る",
        "    if isinstance(value, bool):",
        "        return kind == \"boolean\"",
        "    if kind == \"integer\":",
        "        return isinstance(value, int)",
        "    if kind == \"number\":",
        "        return isinstance(value, (int, float))",
        "    if kind == \"string\":",
        "        return isinstance(value, str)",
        "    return False",
        "",
        "",
        *IMPLEMENTATION,
        "",
        "",
        f"class {test_class(feature)}(unittest.TestCase):",
        "    def call(self, given):",
        "        function = implementation()",
        "        if function is None:",
        MISSING_FAIL,
        "        return function(**given)",
        "",
        "    def check(self, given, expected):",
        "        actual = self.call(given)",
        "        self.assertEqual(actual, expected)",
        "        for name, value in actual.items():",
        *(["            if value is None and name in NULLABLE:", "                continue"] if allow_null else []),
        "            self.assertTrue(type_fits(OUTPUT_TYPES[name], value),",
        "                            f\"{name}: 型が {OUTPUT_TYPES[name]} でない（{value!r}）\")",
    ]
    for case in sorted(feature["cases"], key=case_order):
        expected = case["expected"] if "expected" in case else {"error": case["error"]}
        refs = "・".join(case.get("qa", []))
        lines += [
            "",
            f"    # {case['id']}: {case['title']}" + (f"（{refs}）" if refs else ""),
            f"    def {test_method(case)}(self):",
            f"        self.check({literal(case['input'])}, {literal(expected)})",
        ]
    lines += ["", "", "if __name__ == \"__main__\":", "    unittest.main()"]
    return "\n".join(lines) + "\n"


def perf_file(feature: dict) -> str:
    return f"perf_{feature['id'].lower().replace('-', '_')}.py"


def performance(loaded: "Loaded", feature: dict) -> list[dict[str, str]]:
    """機能の `nfr` が指す性能の行（指した順）。検査（`check_nfr`）を通った後なので、行は 1 つずつ在る。"""
    if not feature.get(NFR):
        return []
    _, found = nfr_rows(loaded.nfr.decode("utf-8-sig"))
    return [found[no][0][0] for no in feature[NFR]]


def perf_test(feature: dict, rows: list[dict[str, str]], impl_module: str) -> str:
    """性能テスト（`references/nfr.md` の「Issue と性能テストに写す」）。**負荷は再現しない**——1 回ずつ呼んで時間を測る。"""
    op = feature["operation"]
    inputs = [case["input"] for case in sorted(feature["cases"], key=case_order)]
    lines = [
        f"# {GENERATED}",
        f"# {feature['id']}: {feature['title']} の性能テスト（{merged(NFR_PATH)} の " + "・".join(feature[NFR]) + "）",
        f"# 実装 `{impl_module}` の `{op['id']}(**input)` を、ケースの入力で 1 回ずつ {PERF_CALLS} 回呼び、1 回の時間（{NFR_UNIT}）から指標を出して上限と比べる。",
        "# 条件の負荷（同時の呼び出し）は再現しない——緑でも、負荷の下で上限を守る証明にはならない。受入基準（Red テスト）ではない。",
        "from __future__ import annotations",
        "",
        "import importlib",
        "import math",
        "import time",
        "import unittest",
        "",
        f"IMPL_MODULE = {impl_module!r}",
        f"OPERATION = {op['id']!r}",
        "INPUTS = [" + ", ".join(literal(given) for given in inputs) + "]",
        f"CALLS = {PERF_CALLS}",
        "",
        "",
        *IMPLEMENTATION,
        "",
        "",
        "def indicator(metric, took):",
        "    # 1 回の時間の並びから指標を出す。p50・p95・p99 は小さいほうから数えた順位（nearest-rank）",
        "    ordered = sorted(took)",
        "    if metric == \"最大\":",
        "        return ordered[-1]",
        "    rank = math.ceil(int(metric[1:]) * len(ordered) / 100)",
        "    return ordered[rank - 1]",
        "",
        "",
        f"class {'Perf' + feature['id'].replace('-', '')}(unittest.TestCase):",
        "    def took(self):",
        "        function = implementation()",
        "        if function is None:",
        MISSING_FAIL,
        "        took = []",
        "        for index in range(CALLS):",
        "            given = INPUTS[index % len(INPUTS)]",
        "            start = time.perf_counter()",
        "            function(**given)",
        "            took.append((time.perf_counter() - start) * 1000)",
        "        return took",
    ]
    for row in rows:
        no, metric, limit = row["No"], row["指標"], row["上限"]
        lines += [
            "",
            f"    # {no}: {row['対象']}（{row['条件']}。根拠: {row['根拠']}）",
            f"    def test_{no.lower().replace('-', '_')}(self):",
            f"        value = indicator({metric!r}, self.took())",
            f"        self.assertLessEqual(value, {limit}, f\"{metric} が {{value:.3f}} {NFR_UNIT} で、上限 {limit} {NFR_UNIT} を超えた（{no}）\")",
        ]
    lines += ["", "", "if __name__ == \"__main__\":", "    unittest.main()"]
    return "\n".join(lines) + "\n"


def sha256(data: str | bytes) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def fingerprint(feature: dict) -> str:
    """機能の指紋（`references/handoff-issue.md` の「機能の指紋で固定する」）。

    中間表現の中の機能のオブジェクトだけの sha256——**関係の無い機能を直しても変わらない**（全体の sha256 は変わる。#290）。
    **dev-loop の `scripts/spec-fingerprint.py` が同じ式の写しを持つ**（プラグインの外を相対パスで指せないため）——
    一致は `scripts/test-scaffold.py` が両方を走らせて見る。
    """
    return sha256(json.dumps(feature, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def cell(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("|", "\\|").replace("\n", "<br>")


def qa_rows(refs: set[str], answered: dict, where: str) -> list[str]:
    if not refs:
        return ["この機能が根拠にした Q&A は無い。"]
    lines = ["| No | 質問 | 回答 | 反映先 |", "| --- | --- | --- | --- |"]
    for no in sorted(refs, key=qa.number_order):
        row = answered[no]
        lines.append(f"| {no} | {cell(row['質問'])} | {cell(row['回答'])} | {cell(row['反映先'])} |")
    return lines + ["", f"（{where}から写した。）"]


# ---------------------------------------------------------------- 前の版と比べる

class Change:
    """Issue の本文 1 件になる機能の変化。"""

    def __init__(self, kind: str, feature: dict, before: dict | None = None) -> None:
        self.kind = kind  # ADD / MODIFY / REMOVE
        self.feature = feature  # この版の機能（削除なら前の版の機能）
        self.before = before  # 前の版の機能（変更・削除）
        self.reason = ""  # 削除の理由（removed.csv）


class Before:
    """前の版（v<n-1>）の全体から読んだもの。v1 なら空。"""

    def __init__(self, answered: dict | None = None, impl_module: str = DEFAULT_IMPL_MODULE, ir: dict | None = None) -> None:
        self.answered = answered or {}
        self.impl_module = impl_module
        self.ir = ir or {"features": []}
        self.trusted = True  # 凍結した前の版が崩れていて信じなかったなら False（全部を追加にした。#357）


# 前の版の時点が崩れていたときの手当ての原本（見出しは `scripts/test-scaffold.py` が `versions.md` と突き合わせる）
BROKEN_REMEDY = "references/versions.md の「前の版の時点が崩れていたら」"


def unsettled_qa(rendered: dict[str, bytes], provisional: bool = False) -> list[tuple[str, str]]:
    """重ねた全体の Q&A（共有・内部）のうち、状態が `反映済み` でない行の (No, 状態)。
    `provisional`（`--provisional`。#875）なら、**その版の中間表現が指す** `暫定反映` の行は数えない——前の版は同じ旗で作れる状態にある（実際に作ったかは見ない——旗の無い周でも、前の版を作ったかは見ていない）。
    **指されない `暫定反映` の行は数える**——旗があってもその版は作れていない（`read_whole` が止める。1 パス目の指摘）。"""
    cited = cited_loosely(rendered.get(IR_PATH)) if provisional else set()
    found = []
    for path in (QA_PATH, INTERNAL_QA_PATH):
        if path in rendered:
            rows = parse_answered(rendered[path].decode("utf-8-sig"))
            found += [(no, row["状態"].strip()) for no, row in rows.items()
                      if row["状態"].strip() != qa.DONE and not (provisional and qa.is_provisional(row) and no in cited)]
    return found


def cited_loosely(raw: bytes | None) -> set[str]:
    """前の版の中間表現が `qa` で指す No（検査の前に読むので、形が崩れていれば読めた分だけ。読めなければ空）。"""
    try:
        ir = json.loads(raw.decode("utf-8")) if raw is not None else {}
    except (UnicodeDecodeError, ValueError, RecursionError):
        return set()
    found = set()
    for feature in ir.get("features", []) if isinstance(ir, dict) and isinstance(ir.get("features"), list) else []:
        if not isinstance(feature, dict):
            continue
        cases = feature.get("cases") if isinstance(feature.get("cases"), list) else []
        for refs in [feature.get("qa")] + [c.get("qa") for c in cases if isinstance(c, dict)]:
            if isinstance(refs, list):
                found |= {no for no in refs if isinstance(no, str)}
    return found


def released(repo: Path, number: int) -> tuple[str | None, list[str]]:
    """(v<number> を凍結したリリースのタグの名前, 凍結した版が直されていればその行)。タグが無ければ (None, [])
    （`references/versions.md` の「凍結」）。**タグがあれば `check-frozen.py` の `check` で確かめる**——タグの後に直した版・
    タグの時点に版が無いタグを、凍結していて直せないと読まない（直されていれば行を返して 1、判定できなければ 2）。

    **git の作業ツリーの根でなければ None**——タグを持てない（根が別なら、そのタグは根の `docs/` を指す。
    `check-frozen.py` も根の `docs/` を見る）。**git を起動できない・浅い clone なら判定しない**（タグが見えないのを
    「凍結していない」と読まない）。
    """
    def git(*args: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        except OSError as exc:
            raise Unjudged(f"git を起動できない（{exc.strerror}）。v{number} が凍結しているかを判定していない")

    top = git("rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != repo.resolve():
        return None, []
    shallow = git("rev-parse", "--is-shallow-repository")
    if shallow.returncode != 0 or shallow.stdout.strip() != "false":
        raise Unjudged(f"浅い clone か確かめられない・浅い clone である（タグがそろっていない）。"
                       f"v{number} が凍結しているかを判定していない")
    listed = git("tag", "--list")
    if listed.returncode != 0:
        raise Unjudged(f"タグを読めない: {listed.stderr.strip()}。v{number} が凍結しているかを判定していない")
    tag = next((tag for n, tag in frozen.releases(listed.stdout.split()) if n == number), None)
    if tag is None:
        return None, []
    # タグがあるだけでは信じない——タグの時点の `docs/v<n>/` と今が同じかは `check-frozen.py` が決める（写さない）。
    # 確かめるのは v<number> だけ——他の版のタグの状態で、この版の凍結を決めない（#361 の 2 パス目）
    code, lines = frozen.check(repo, only=number)
    if code == 2:
        raise Unjudged(f"{lines[0]}（check-frozen.py）。v{number} が凍結しているかを判定していない")
    return tag, (lines[:-1] if code else [])


def base_commit(repo: Path) -> tuple[str, str | None]:
    """(本文の `## 仕様` に書く基準コミットの行, 記録できなかった理由。記録したなら None)（#874）。

    **基準コミットは、正本リポジトリで本文を生成した時点の HEAD** とそのコミットの日時（`%cI`）である——
    仕様を書いた人が見ていた既存のシステムの時点を表す（仕様そのものの時点は、機能の指紋と Red テストの sha256 が表す。
    生成 → commit → 登録の順なので、生成の時点の仕様はふつう未コミットである）。**生成の時刻は書かない**（同じ HEAD から
    同じバイト）。**git の作業ツリーの根でない・コミットが無い・git を起動できないなら止めない**——`記録していない（理由）` と書く。

    - **git は `merge-versions.py` の `run_git` で呼ぶ**——リポジトリの場所を指す環境変数（`GIT_DIR` など）を外す（フックの中で
      引き継ぐと別のリポジトリの HEAD を書く。#874 の 1 パス目）。
    - **根でなければ記録しない**（`released` と同じ）——根が別なら、その HEAD は外側のリポジトリのもので、dev-loop の点検が
      除くパス（根の `docs/`・`scaffold/`）も正本のものでない。
    - **理由は決まった文言だけ**（git の出力を写さない）——本文は公開のリポジトリに登録されうる。
    - **署名の表示（`log.showSignature`）を切って読む**——利用者の設定で出力の頭に署名の検証が混ざると、コミットが読めない。
    """
    def git(*args: str) -> tuple[int, str]:
        proc = versions.run_git(repo, *args)
        return proc.returncode, proc.stdout.decode("utf-8", "replace")

    try:
        # 根かどうかは git に訊く（`--show-cdup` が空なら根）——パスを比べると、大文字小文字を区別しない FS で綴りの違う
        # `--repo` を根でないと読む（#874 の 2 パス目）
        code, where = git("rev-parse", "--is-inside-work-tree", "--show-cdup")
        inside, _, cdup = where.partition("\n")
        if code != 0 or inside.strip() != "true":
            reason = "正本リポジトリが git の作業ツリーでない"
        elif cdup.strip():
            reason = "正本リポジトリが git の作業ツリーの根でない"
        else:
            code, head = git("-c", "log.showSignature=false", "log", "-1", "--format=%H%n%cI", "HEAD")
            found = head.split("\n") if code == 0 else []
            if len(found) >= 2 and COMMIT_ID.fullmatch(found[0]) and found[1]:
                return (f"{BASE_COMMIT}`{found[0]}`（コミットの日時 {found[1]}。正本リポジトリで本文を生成した時点の HEAD"
                        "——dev-loop は周の頭で、この後の変化が仕様の前提を崩していないかを点検する）"), None
            reason = "正本リポジトリの HEAD のコミットを読めない（コミットが無い）"
    except OSError as exc:
        reason = f"git を起動できない（{exc.strerror}）"
    return f"{BASE_COMMIT}{BASE_UNRECORDED}（{reason}）——この Issue からは、仕様を書いた後の変化を辿れない", reason


def classify(loaded: Loaded) -> tuple[int, list[str], list[Change], Before]:
    """(終了コード, 出力する行, 変化, 前の版) を返す。v<n> の全体と v<n-1> の全体を機能の `id` で比べる。

    **先に前の版の Q&A の状態を見る**——`反映済み` でない行が残れば（中間表現が指しているかに依らない）、
    凍結していなければ 1、凍結していれば止めずに全部を追加にして知らせる（0。#361）。
    前の版の中間表現も決まりに当てる——反すると、ケースの変化を Red テストの中身で比べられない（1）。
    **パスの変数の決まりだけは当てない**（`read_whole`。#319）。
    """
    number = loaded.number
    now = {f["id"]: f for f in features_of(loaded.ir)}
    if number == 1:
        return 0, [], [Change(ADD, f) for f in now.values()], Before()
    try:
        problems, found, _, rendered = versions.merge(loaded.docs, number - 1)
    except versions.Unreadable as exc:
        raise Unjudged(f"{exc}。前の版（v{number - 1}）を重ね合わせていない")
    if problems:
        return 1, problems + [f"前の版（v{number - 1}）の全体を重ねられない。生成しない"], [], Before()
    reasons = diffs.removal_reasons(found[number - 1][1])
    # 前の版の時点が崩れている——`反映済み` でない Q&A が残れば、v<n-1> の scaffold は作れていない（確認中は条件 1、
    # 暫定反映は held で止まる）。中間表現が指しているかに依らず、前の版に中間表現が無くても、状態を直接見る（#335・#358）
    unsettled = unsettled_qa(rendered, loaded.provisional)
    if unsettled:
        out = [f"v{number - 1} の時点の {no}: 状態が {state}（{qa.DONE} でない）" for no, state in unsettled]
        tag, edited = released(loaded.docs.parent, number - 1)
        if edited:
            return 1, out + edited + [f"v{number - 1} は凍結しているのに直されている。直した分を {tag} の時点に戻してから"
                                      "作る（凍結した版を信じてよいかが決まらない）。生成しない"], [], Before()
        if tag is None:
            out.append(f"v{number - 1} の時点では {qa.DONE} でない Q&A が残り、v{number - 1} の scaffold は作れていない"
                       f"（`--check --upto {number - 1}` が 0 にならない）。v{number} の差分を測る土台が無い"
                       f"——{BROKEN_REMEDY}")
            if not loaded.provisional and not unsettled_qa(rendered, provisional=True):
                # 残るのが前の版の中間表現が指す暫定の行だけ——前の版を `--provisional` で作ったなら旗で通る（#875 の 2 パス目）
                out.append(f"残るのは v{number - 1} の中間表現が指す {qa.PROVISIONAL} の行だけ——v{number - 1} を --provisional で"
                           "作ったなら、利用者のその指示のもとで --provisional を付けて作る（付けるのは利用者の指示があるときだけ）")
            out.append(f"前の版（v{number - 1}）の時点が崩れているので、機能を追加・変更・削除に分けない。生成しない")
            return 1, out, [], Before()
        # 凍結した版は直せない——v<n-1> の時点を信じず、全部を追加にする（変わらない機能の Issue も渡る。#357）
        dropped = sorted(key for kind, key in reasons if kind == versions.KIND_FEATURE)
        out.append(f"v{number - 1} は {tag} で凍結していて直せない。v{number - 1} の時点を信じず、v{number} の機能を"
                   f"全部 {ADD} として本文を作る——{BROKEN_REMEDY}")
        if dropped:
            out.append(f"v{number} で消した機能（{'・'.join(dropped)}）の撤去の本文は作らない（比べる前の版を信じないので）")
        distrusted = Before()
        distrusted.trusted = False
        return 0, out, [Change(ADD, f) for _, f in sorted(now.items())], distrusted
    before_ir, before = {"features": []}, Before()
    if IR_PATH in rendered:
        code, lines, before_ir, answered = read_whole(rendered, gate=False, provisional=loaded.provisional)
        if code:
            out = [f"v{number - 1} の時点の {line}" for line in lines[:-1]]
            out.append(f"前の版（v{number - 1}）の中間表現が決まりに反するので、機能を追加・変更・削除に分けない。生成しない")
            return 1, out, [], Before()
        before = Before(answered, before_ir.get("impl_module", DEFAULT_IMPL_MODULE), before_ir)
    kinds = {diffs.ADDED: ADD, diffs.CHANGED: MODIFY, diffs.REMOVED: REMOVE}
    old = {f["id"]: f for f in features_of(before_ir)}
    changes = []
    for diff in diffs.compare_maps(old, now):
        kind = kinds[diff.status]
        change = Change(kind, diff.before if kind == REMOVE else diff.after, diff.before)
        change.reason = reasons.get((versions.KIND_FEATURE, diff.key), "")
        changes.append(change)
    if before.impl_module != loaded.ir.get("impl_module", DEFAULT_IMPL_MODULE):
        # 実装のモジュールが変わると、機能が同じでも Red テストは全部、前の版の実装を探せずに失敗する
        moved = {c.feature["id"] for c in changes}
        changes += [Change(MODIFY, f, old[key]) for key, f in now.items() if key in old and key not in moved]
    return 0, callers_unchanged(changes, number), sorted(changes, key=lambda c: c.feature["id"]), before


def callers_unchanged(changes: list[Change], number: int) -> list[str]:
    """呼ばれる機能だけが変わり、呼ぶ機能がどれも変わっていない——止めずに知らせる行（#609）。

    関数の中だけの直しはありうるので止めない。**呼ぶ入口の振る舞いも変わるのに、仕様がその入口の変化を書いていない**
    （v2 の差分に呼ぶ側が無い）なら、呼ぶ側の課題がどの Issue にも載らない——だから名指しする。
    """
    changed = {c.feature["id"] for c in changes if c.kind in (ADD, MODIFY)}
    lines = []
    for change in sorted(changes, key=lambda c: c.feature["id"]):
        callers = change.feature.get(CALLED_BY) or []
        if change.kind in (ADD, MODIFY) and callers and not changed & set(callers):
            lines.append(f"{change.feature['id']} は v{number} で {change.kind} だが、呼ぶ機能（{'・'.join(callers)}）は"
                         f" v{number} で変わっていない——呼ぶ入口の振る舞いも変わるなら、仕様にその入口の変化を書き、"
                         "中間表現でも変える（変わらないなら、このままでよい）")
    return lines


# 前の版の型で通った値は、広げた型にも合う（`type_fits`）——広げただけでは前の版の実装は落ちない
WIDENED = {("integer", "number")}


def behavior(feature: dict, case: dict, impl_module: str) -> tuple[str, ...]:
    """そのケースの Red テストが実行する中身のうち、型を除いたもの（題・コメントは入れない）。"""
    op = feature["operation"]
    expected = case["expected"] if "expected" in case else {"error": case["error"]}
    return impl_module, op["id"], literal(case["input"]), literal(expected)


def case_changed(before: dict, old: dict, impl_before: str, feature: dict, case: dict, impl_now: str) -> bool:
    """前の版で通った実装の上で、このケースの Red テストが失敗しうるか。

    型を見るのは期待にある項目だけ——Red テストは `actual == expected` のあとで `actual` の項目の型を見るので、
    期待に無い出力の項目・失敗のケースの `error` 以外の型は、そのケースの結果を変えない。
    """
    if behavior(before, old, impl_before) != behavior(feature, case, impl_now):
        return True
    was, now = output_types(before["operation"]), output_types(feature["operation"])
    expected = case["expected"] if "expected" in case else {"error": case["error"]}
    return any(was.get(name) != now.get(name) and (was.get(name), now.get(name)) not in WIDENED for name in expected)


def case_changes(change: Change, impl_now: str, impl_before: str) -> tuple[list[tuple[str, dict]], list[dict]]:
    """([(変化, ケース)], 消したケース) を返す。並びはケースの番号の順。"""
    cases = sorted(change.feature["cases"], key=case_order)
    if change.kind == REMOVE:
        return [(CASE_REMOVED, c) for c in cases], []
    if change.kind == ADD:
        return [(CASE_ADDED, c) for c in cases], []
    old = {c["id"]: c for c in change.before["cases"]}
    rows = []
    for case in cases:
        if case["id"] not in old:
            rows.append((CASE_ADDED, case))
        elif case_changed(change.before, old[case["id"]], impl_before, change.feature, case, impl_now):
            rows.append((CASE_CHANGED, case))
        else:
            rows.append((CASE_KEPT, case))
    ids = {case["id"] for case in cases}
    return rows, sorted((c for c in change.before["cases"] if c["id"] not in ids), key=case_order)


def test_name(feature: dict, case: dict) -> str:
    return f"{test_class(feature)}.{test_method(case)}"


def test_id(feature: dict, case: dict) -> str:
    """`unittest` が `scaffold/tests` から見つけたときの名前（モジュール.クラス.メソッド）。"""
    return f"{test_file(feature)[:-3]}.{test_name(feature, case)}"


def red_cases(rows: list[tuple[str, dict]]) -> list[dict]:
    """前の版の実装の上で失敗しうるケース（追加・変更）。"""
    return [case for status, case in rows if status in (CASE_ADDED, CASE_CHANGED)]


# ---------------------------------------------------------------- Issue の本文

def issue_title(change: Change, number: int) -> str:
    title = f"{change.feature['id']}: {change.feature['title']}"
    if change.kind == MODIFY:
        return f"{title}（v{number} で変更）"
    if change.kind == REMOVE:
        return f"{title}（v{number} で撤去）"
    return title


def issue_body(change: Change, loaded: Loaded, contract: dict[str, str], before: Before, base_line: str) -> str:
    feature, number = change.feature, loaded.number
    impl_now = loaded.ir.get("impl_module", DEFAULT_IMPL_MODULE)
    impl = before.impl_module if change.kind == REMOVE else impl_now
    op = feature["operation"]
    base = pascal(op["id"])
    names = [f"`{base}Input`", f"`{base}Output`"] + ([f"`{base}Error`"] if op.get("errors") else [])
    tfile = f"{OUT_DIR}/tests/{test_file(feature)}"
    rows, gone = case_changes(change, impl_now, before.impl_module)
    previous = f"v{number - 1}"
    kind_text = {
        ADD: "追加（v1 の機能）" if number == 1 else f"追加（v{number} で足した機能）",
        MODIFY: f"変更（{previous} の時点から v{number} で変えた機能）",
        REMOVE: f"削除（v{number} で消した機能。理由: {cell(change.reason)}）",
    }[change.kind]
    command = f"merge-versions.py {DOCS} {MERGED_DIR} --upto {number}"
    old_dir = PREVIOUS_DIR.format(number - 1)
    old_command = f"merge-versions.py {DOCS} {old_dir} --upto {number - 1}"
    lines = [
        HANDOFF_MARKER,
        FEATURE_MARKER.format(feature["id"]),
        CHANGE_MARKER.format(change.kind, previous if number > 1 else NO_BASE),
        "",
        "この Issue は spec-loop の `scaffold` が、確定した仕様から生成した。**本文を手で直さない。**",
        "",
        SECTIONS[0],
        "",
        f"- 機能: `{feature['id']}` {feature['title']}",
        f"- 変化: {kind_text}",
        base_line,
    ]
    if change.kind == REMOVE:
        lines += [
            f"- 中間表現（{previous} の時点）: `{old_dir}/{IR_PATH}` の `{feature['id']}`"
            f"（機能の指紋: `{fingerprint(feature)}`）——v{number} の `{merged(IR_PATH)}` にはこの機能が無い",
            f"- 仕様の原文（{previous} の時点）: " + "・".join(f"`{old_dir}/{s}`" for s in feature["source"]),
        ]
    else:
        lines += [
            f"- 中間表現: `{merged(IR_PATH)}` の `{feature['id']}`（機能の指紋: `{fingerprint(feature)}`）",
            "- 仕様の原文: " + "・".join(f"`{merged(s)}`" for s in feature["source"]),
        ]
    lines.append(f"- `{MERGED_DIR}/` は正本の版（`{DOCS}/v1/`…）を v{number} まで重ね合わせた全体で、commit しない——spec-loop の"
                 f" `{command}` で作る（**版を指定する**——後の版を足しても同じバイトになる）")
    if change.kind == REMOVE:
        lines.append(f"- `{old_dir}/` は {previous} までを重ね合わせた全体で、同じく commit しない——`{old_command}` で作る")
    if change.kind == REMOVE:
        lines += [f"- 撤去する API: `{op['method']} {op['path']}`（`operationId`: `{op['id']}`。`{OUT_DIR}/openapi.json` から消えた）",
                  "- 消えた型: " + "・".join(names) + f"（`{OUT_DIR}/types.py` から消えた）"]
    else:
        lines += [f"- API: `{op['method']} {op['path']}`（`{OUT_DIR}/openapi.json` の `operationId`: `{op['id']}`）",
                  f"- 型: `{OUT_DIR}/types.py` の " + "・".join(names)]
        old_op = change.before["operation"] if change.kind == MODIFY else None
        if old_op and (old_op["method"], old_op["path"], old_op["id"]) != (op["method"], op["path"], op["id"]):
            lines.append(f"- {previous} の API: `{old_op['method']} {old_op['path']}`（`operationId`: `{old_op['id']}`）")
        if feature.get(CALLED_BY):
            titles = {f["id"]: f["title"] for f in features_of(loaded.ir)}
            lines.append("- 呼ぶ機能: " + "・".join(f"`{c}` {cell(titles[c])}" for c in feature[CALLED_BY])
                         + "（この機能を呼ぶ入口の機能。この Issue は呼ぶ側の配線を含まない）")
    refs = set(feature["qa"]) | {no for _, case in rows for no in case.get("qa", [])}
    # 仮回答の印（#875）——`--provisional` で通した `暫定反映` の行に依存する本文だけ。依存しなければ 1 バイトも変わらない。
    # **撤去の本文には付けない**——作るものが無く、前の版の時点の状態で印を付けると、生成した時点で確定した行にも付く（1 パス目の指摘）
    held = [] if change.kind == REMOVE else sorted((no for no in refs if qa.is_provisional(loaded.answered[no])),
                                                   key=qa.number_order)
    if held:
        lines.append(f"{PROVISIONAL_LINE}" + "・".join(held) + f"（状態 `{qa.PROVISIONAL}`——利用者がまだ確かめていない回答で作った。"
                     "回答が変わったら、この Issue と、下の受入基準のうちその No を根拠にするケース"
                     "（ケースに無ければ機能全体）を作り直す。いまの状態の正は Q&A 表）")
    lines += ["", SECTIONS[1], ""]
    if change.kind == REMOVE:
        lines += [
            f"**この機能の実装（モジュール `{impl}` の関数 `{op['id']}`）を撤去し、{KEPT_GREEN}。**",
            "撤去した関数を呼ぶ箇所を残さない。下のケースの振る舞いは、もう求めない。",
            "同じ版で足した・変えたほかの機能のケースは、まだ実装されずに失敗していてよい——撤去の周はそれを緑にしない。",
        ]
    else:
        lines += [
            "**下の Red テストがすべて緑になること。** テストを書き換えて緑にしない——テストが仕様と食い違うと思ったら、",
            "それは仕様の穴である（下の「仕様の穴を見つけたら」）。",
        ]
        if change.kind == MODIFY:
            lines += [
                f"**`{CASE_KEPT}` のケースも緑であること**——前の版の実装の上で失敗しうるのは",
                f"`{CASE_ADDED}`・`{CASE_CHANGED}` のケースだけである。**ほかの機能は、{KEPT_GREEN}**",
                "（同じ版で足した・変えたほかの機能のケースは、この周の前に失敗していてよい）。",
            ]
    lines += ["", "| ケース | 変化 | 確かめること | Red テスト | Q&A |", "| --- | --- | --- | --- | --- |"]
    for status, case in rows:
        test = f"—（`{tfile}` ごと消した）" if change.kind == REMOVE else f"`{test_name(feature, case)}`"
        lines.append(f"| `{case['id']}` | {status} | {cell(case['title'])} | {test} | "
                     + ("・".join(no + (PROVISIONAL_CELL if no in held else "") for no in case.get("qa", [])) or "—")
                     + " |")
    if gone:
        lines += ["", f"{CASE_REMOVED}したケース（Red テストから外した。その振る舞いはもう求めない）: "
                  + "・".join(f"`{c['id']}` {cell(c['title'])}" for c in gone)]
    lines += ["", SECTIONS[2], ""]
    if change.kind == REMOVE:
        lines += [
            f"- 消したファイル: `{tfile}`（`scaffold.py` が消した。この機能の Red テストはもう無い）",
            "- 回帰（正本リポジトリの根で、撤去の前と後に回す。前に緑だったテストが後も緑であること）:",
            "",
            "```bash",
            f"python3 -m unittest discover -s {OUT_DIR}/tests",
            "```",
        ]
    else:
        red = red_cases(rows)
        lines += [
            f"- ファイル: `{tfile}`（sha256: `{sha256(contract[f'tests/{test_file(feature)}'])}`）",
            f"- 実装を置く場所: モジュール `{impl}` の関数 `{op['id']}(**input) -> dict`"
            "（失敗は `{\"error\": \"<名前>\"}` を返す）",
            "- 回し方（正本リポジトリの根で）:",
            "",
            "```bash",
            f"python3 -m unittest discover -s {OUT_DIR}/tests -p {test_file(feature)}",
            "```",
            "",
        ]
        if change.kind == ADD:
            lines.append("実装が無い状態では、ケースの数だけ失敗する。")
        else:
            lines += [f"前の版の実装の上で失敗しうるのは `{CASE_ADDED}`・`{CASE_CHANGED}` のケース（{len(red)} 件）だけで"
                      "（前の版の実装がもう満たすものは緑）、"
                      f"`{CASE_KEPT}` のケース（{len(rows) - len(red)} 件）は緑である。ほかの機能を含む回帰は",
                      f"`python3 -m unittest discover -s {OUT_DIR}/tests` で見る。"]
    lines += ["", SECTIONS[3], ""]
    # 内部の層の行（`D-`）を指していれば、写した元に内部の表も挙げる（#339）
    tables = "・".join(f"`{merged(path)}`" for path in
                       (QA_PATH, *([INTERNAL_QA_PATH] if any(qa.is_internal_number(no) for no in refs) else [])))
    if change.kind == REMOVE:
        lines += qa_rows(refs, before.answered, f"{previous} の時点の {tables} ")
    else:
        lines += qa_rows(refs, loaded.answered, f"生成した時点の {tables} ")
    lines += ["", SECTIONS[4], ""] + not_built(change, loaded, contract)
    lines += [
        "",
        SECTIONS[5],
        "",
        f"**実装で決めない。** 作業中の版の Q&A 表（`{DOCS}/v<n>/{QA_PATH}`）に起票元 `開発` で起票して、要求側に差し戻す。",
        "手順は dev-loop の `references/spec-gap.md` にある。",
    ]
    if change.kind == REMOVE:
        lines.append(f"**`{old_command}` で作った `{old_dir}/{IR_PATH}` での機能の指紋が上と違うか、"
                     f"`{command}` で作った `{merged(IR_PATH)}` にこの機能が残っているなら、"
                     "この Issue は手元の仕様と別の時点のもの**——")
    else:
        lines.append("**上のコマンドで作った手元の中間表現の機能の指紋か Red テストの sha256 が上と違うなら、"
                     "この Issue は手元の仕様と別の時点のもの**——")
    lines.append("実装に入らず、同じく差し戻す。")
    return "\n".join(lines) + "\n"


def not_built(change: Change, loaded: Loaded, contract: dict[str, str]) -> list[str]:
    """`## 作らないもの` の節の中身（#851。`references/handoff-issue.md` の「作らないもの」）。"""
    if change.kind == REMOVE:
        return ["撤去の Issue なので、作るものは無い——消した機能の代わりを作らない。"]
    picked = set(change.feature.get(OUT_OF_SCOPE, []))
    # 検査（`check_out_of_scope`）を通った後なので、挙げた行は節に在り、文書は読める
    rows = scope_rows(loaded.scope.decode("utf-8-sig")) if picked else []
    chosen, seen = [], set()
    for text, header in rows:
        if text in picked and text not in seen:
            seen.add(text)
            chosen.append((text, header))
    lines = ["受入基準に結びつかないものを作らない。下に挙げたものは、この機能では作らない。"]
    groups = ((NOT_BUILT[0], [r for r in chosen if NEXT_VERSION not in r[0]], "範囲の外の行"),
              (NOT_BUILT[1], [r for r in chosen if NEXT_VERSION in r[0]], NEXT_VERSION))
    for heading, group, what in groups:
        lines += ["", heading, ""]
        if not group:
            lines.append(f"この機能に関わるとして写した{what}は無い（無いことは、ほかのものを作ってよいという意味ではない）。")
            continue
        for index, (text, header) in enumerate(group):
            # 表の行は同じ表の行と続けて並べ、表が変わる・表でない行は空の行で区切る（表でない行どうしが 1 段落に繋がらないように）
            if index and (header is None or header != group[index - 1][1]):
                lines.append("")
            if header is not None and (index == 0 or header != group[index - 1][1]):
                lines += list(header)
            lines.append(text)
        lines += ["", f"（範囲の文書 `{merged(SCOPE_PATH)}` の「{proposal.OUT_OF_SCOPE}」の節から、原文のまま写した。）"]
    lines += ["", NOT_BUILT[2], ""] + budget(change.feature, loaded, contract)
    return lines


def budget(feature: dict, loaded: Loaded, contract: dict[str, str]) -> list[str]:
    """`### 性能予算` の中身（#852。`references/nfr.md` の「Issue と性能テストに写す」）。`nfr` が無ければ既定の原則。"""
    rows = performance(loaded, feature)
    if not rows:
        return [NO_PERFORMANCE_BUDGET]
    pfile = f"{OUT_DIR}/{PERF_DIR}/{perf_file(feature)}"
    lines = [f"この機能の性能の要求（`{merged(NFR_PATH)}` の行から写した）:", "",
             "| No | 対象 | 指標 | 上限 | 条件 | 根拠 |", "| --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| {row['No']} | {cell(row['対象'])} | {row['指標']} | {row['上限']} {NFR_UNIT} | "
                     f"{cell(row['条件'])} | {cell(row['根拠'])} |")
    lines += [
        "",
        "**予算の中なら、速さのための最適化をしない。** 最適化は、性能テストか計測で予算を超えたと示せたときだけ。",
        "",
        f"- 性能テスト: `{pfile}`（sha256: `{sha256(contract[f'{PERF_DIR}/{perf_file(feature)}'])}`）"
        f"——実装をケースの入力で 1 回ずつ {PERF_CALLS} 回呼び、1 回の時間から指標を出して上限と比べる",
        "- 回し方（正本リポジトリの根で）:",
        "",
        "```bash",
        f"python3 -m unittest discover -s {OUT_DIR}/{PERF_DIR} -p {perf_file(feature)}",
        "```",
        "",
        "- **性能テストは `条件` の負荷（同時の呼び出し）を再現しない**——緑でも、負荷の下で上限を守る証明にはならない。"
        "負荷の下で守るかは、負荷試験・本番の計測で確かめる。",
        "- **性能テストは受入基準（上の Red テストの表）ではない**——最適化してよいかを決める計測の道具である。",
    ]
    return lines


def proposal_changes(changes: list[Change]) -> list[Change]:
    """課題一覧（案）に載せる変化——追加・変更した入口の機能（`called_by` を持たない機能）。呼ばれる関数・撤去は載せない。

    **`impl_module` を変えただけで変更になった機能（機能のオブジェクトは前の版と同じ）も載せない**——Issue の本文は作るが
    （Red テストが前の版の実装を探せない）、結線の課題は変わっていない。凍結した前の版を信じずに全部を追加にしたときは、
    変わったかを決められないので全部に載せる（本文と同じ。#357）。
    """
    return [c for c in changes if c.kind in (ADD, MODIFY) and not c.feature.get(CALLED_BY)
            and not (c.kind == MODIFY and c.before == c.feature)]


def undecided(feature: dict) -> list[str]:
    """呼ぶ側の分岐のうち、中間表現の `branches` に書き起こしていないもの（行ごと該当なしなら無い）。"""
    branches = feature.get(BRANCHES_KEY) or {}
    return [] if NONE in branches else [name for name in BRANCHES if name not in branches]


def proposals(changes: list[Change], loaded: Loaded, contract: dict[str, str]) -> str:
    """課題一覧（案）（#855。`references/spec-ir.md` の「呼ぶ側の分岐」）。案は登録しない——登録は利用者が決める。

    案ごとに、未決定事項（呼ぶ側の分岐のうち `branches` に無いもの）・受入基準の雛形（見せるものが決まった分岐の原文）・
    作らないもの（元の機能の本文の `## 作らないもの` と同じ中身を、小見出しを 1 段下げて）を付ける。
    """
    entries = proposal_changes(changes)
    lines = [
        "# 課題一覧（案）",
        "",
        "scaffold が Issue にする機能（Red テストつき）の、**Red テストの外に残る呼ぶ側の結線**の課題の案。"
        f"v{loaded.number} で追加・変更した入口の機能（`{CALLED_BY}` を持たない機能。`impl_module` を変えただけで変更になった機能を除く）ごとに 1 案を置き、"
        "呼ぶ側の分岐（spec-loop の `references/spec-exit.md` の仕様チェックリストの行）を中間表現の"
        f" `{BRANCHES_KEY}` から写す。",
        "",
        "**scaffold はこの案を登録しない**——登録するかは利用者が決める。"
        "**未決定事項のある案は、登録の前に `/spec-loop:spec-review` に戻す**（決まっていないことを実装で決めさせない）。",
    ]
    if not entries:
        lines += ["", f"案は無い——v{loaded.number} で追加・変更した入口の機能（`impl_module` を変えただけのものを除く）が無い。"]
    for change in entries:
        feature = change.feature
        branches = feature.get(BRANCHES_KEY) or {}
        fid = feature["id"]
        lines += [
            "", f"## {fid}: {feature['title']} の結線", "",
            f"- 元の機能: `{fid}`（Issue の本文 `{fid}.md`・変化 `{change.kind}`）——その Red テストは関数の振る舞いを確かめる。"
            "この案は Red テストの外に残る呼ぶ側の結線を受け持つ",
            "- 仕様の原文: " + "・".join(f"`{merged(s)}`" for s in feature["source"]),
            "", "### 未決定事項", "",
        ]
        missing = undecided(feature)
        if missing:
            lines += [f"- {name}: 中間表現の `{BRANCHES_KEY}` に書き起こしていない——仕様が決めていれば書き起こし、"
                      "決めていなければ `/spec-loop:spec-review` に戻す" for name in missing]
        else:
            lines.append("無い（呼ぶ側の分岐は、どれも仕様が決めている）。")
        lines += ["", "### 受入基準の雛形", ""]
        if NONE in branches:
            lines.append(f"呼ぶ側の分岐は行ごと該当なし（仕様の原文: {branches[NONE]}）——結線で見せるものは無い。")
        else:
            shown = [(name, branches[name][SHOWS]) for name in BRANCHES if SHOWS in branches.get(name, {})]
            absent = [(name, branches[name][NONE]) for name in BRANCHES if NONE in branches.get(name, {})]
            lines += [f"- [ ] {name}: {text}" for name, text in shown]
            if not shown:
                lines.append("見せるものが決まった分岐は無い" + ("（上の未決定事項を先に決める）。" if missing else "——どの分岐も該当なし。"))
            if absent:
                lines += ["", "該当なしの分岐（仕様の原文）:", ""] + [f"- {name}: {text}" for name, text in absent]
        lines += [
            "",
            f"- [ ] {KEPT_GREEN}（元の機能 `{fid}` の Red テストを含む）",
            "",
            "上の分岐に Red テストは無い——見せるものの確かめ方（結合テスト・実機確認）は、この案を登録した Issue の周が決める。",
            "",
            "### 作らないもの",
            "",
        ]
        # 元の機能の本文の `## 作らないもの` と同じ中身。小見出し（`### 範囲の外` など）を 1 段下げる
        lines += [f"#{line}" if line in NOT_BUILT else line for line in not_built(change, loaded, contract)]
    return "\n".join(lines) + "\n"


def render_contract(loaded: Loaded) -> dict[str, str]:
    """{`scaffold/` からの相対パス: 中身} を返す。契約は全体から作る（変わっていない機能も）。

    性能テストは `nfr` を持つ機能だけ（#852）——持たない中間表現の契約は、`nfr` を足す前と 1 バイトも変わらない。
    """
    ir = loaded.ir
    impl_module = ir.get("impl_module", DEFAULT_IMPL_MODULE)
    contract = {"openapi.json": openapi(ir), "types.py": types_py(ir)}
    for feature in features_of(ir):
        contract[f"tests/{test_file(feature)}"] = red_test(feature, impl_module)
        rows = performance(loaded, feature)
        if rows:
            contract[f"{PERF_DIR}/{perf_file(feature)}"] = perf_test(feature, rows, impl_module)
    return contract


def parse_bundles(values: list[str]) -> tuple[list[list[str]], str | None]:
    """`--bundle` の値（`F-001,F-002`）を機能の id の組に分ける（#876）。形の誤りなら ([], 理由)。組の中は id の順に並べる。"""
    bundles: list[list[str]] = []
    seen: set[str] = set()
    for value in values:
        ids = value.split(",")
        if not all(FEATURE_ID.fullmatch(i) for i in ids):
            return [], f"--bundle {value!r}: 機能の id（F- に 3 桁以上の数字）をカンマで区切って並べる（空白を入れない）"
        if len(ids) < 2:
            return [], f"--bundle {value!r}: まとめるには機能を 2 件以上並べる"
        if len(set(ids)) != len(ids) or seen & set(ids):
            return [], f"--bundle {value!r}: 同じ機能を 2 度並べている（1 つの機能は 1 つの組にだけ入れる）"
        seen |= set(ids)
        bundles.append(sorted(ids))
    return sorted(bundles), None


def group_changes(changes: list[Change], bundles: list[list[str]]) -> tuple[list[list[Change]], list[str]]:
    """変化を Issue 1 件ずつの組に分ける（#876）。**`--bundle` が無ければ 1 機能 = 1 件**（既定）。

    まとめてよいのは、この版で本文を作る機能で、変化（追加・変更・撤去）が揃うものだけ——受入基準の形が変化で決まるので。
    同じモジュール・同じデプロイ経路かは中間表現から決められず、選ぶのは scaffold を回す人である（見ない）。
    まとめた結果の依存（`dependencies`）が循環すれば使えない——cruise の親 Issue が拒む。(組, 問題) を返す。
    """
    by_id = {c.feature["id"]: c for c in changes}
    problems = []
    for ids in bundles:
        absent = [i for i in ids if i not in by_id]
        if absent:
            problems.append(f"--bundle {','.join(ids)}: {'・'.join(absent)} はこの版で本文を作る機能でない（中間表現に無いか、"
                            "前の版から変わっていない）")
        elif len({by_id[i].kind for i in ids}) != 1:
            kinds = "・".join(f"{i} は {by_id[i].kind}" for i in ids)
            problems.append(f"--bundle {','.join(ids)}: 変化が揃わない（{kinds}）——受入基準の形が違うのでまとめない")
    if problems:
        return [], problems
    bundled = {i: ids for ids in bundles for i in ids}
    groups, done = [], set()
    for change in changes:
        fid = change.feature["id"]
        if fid not in done:
            ids = bundled.get(fid, [fid])
            groups.append([by_id[i] for i in ids])
            done |= set(ids)
    order = cycle_in(groups, dependencies(groups))
    if order:
        problems.append(f"--bundle でまとめると依存が循環する（{' → '.join(order)}）——呼ぶ機能と呼ばれる機能を、別々の組に"
                        "互い違いに入れている。組み方を変える")
    return groups, problems


def dependencies(groups: list[list[Change]]) -> list[list[str]]:
    """組ごとの依存先の機能の id（#876）——**呼ぶ機能（入口）の組は、呼ばれる機能（関数）の組に依存する**（`called_by`）。

    同じ組の中の依存と、撤去の機能（前の版の `called_by` しか持たない）は数えない。この版で本文を作らない機能への依存も数えない
    （その機能は前の版の Issue で作ってある）。
    """
    owner = {c.feature["id"]: index for index, group in enumerate(groups) for c in group}
    found: list[set[str]] = [set() for _ in groups]
    for index, group in enumerate(groups):
        for change in group:
            if change.kind == REMOVE:
                continue
            for caller in change.feature.get(CALLED_BY, []):
                at = owner.get(caller)
                if at is not None and at != index and groups[at][0].kind != REMOVE:
                    found[at].add(change.feature["id"])
    return [sorted(ids) for ids in found]


def cycle_in(groups: list[list[Change]], depends: list[list[str]]) -> list[str]:
    """組の依存の循環を、組の頭の機能の id の並びで返す（無ければ空）。"""
    owner = {c.feature["id"]: index for index, group in enumerate(groups) for c in group}
    edges = [sorted({owner[fid] for fid in ids}) for ids in depends]
    state: dict[int, int] = {}
    path: list[int] = []

    def visit(node: int) -> list[int]:
        state[node] = 1
        path.append(node)
        for nxt in edges[node]:
            if state.get(nxt) == 1:
                return path[path.index(nxt):] + [nxt]
            if nxt not in state and (loop := visit(nxt)):
                return loop
        state[node] = 2
        path.pop()
        return []

    for node in range(len(groups)):
        if node not in state and (loop := visit(node)):
            return ["・".join(c.feature["id"] for c in groups[i]) for i in loop]
    return []


def bundle_title(group: list[Change], number: int) -> str:
    title = "・".join(c.feature["id"] for c in group) + ": " + "／".join(c.feature["title"] for c in group)
    if group[0].kind == MODIFY:
        return f"{title}（v{number} で変更）"
    if group[0].kind == REMOVE:
        return f"{title}（v{number} で撤去）"
    return title


def bundle_body(group: list[Change], bodies: dict[str, str]) -> str:
    """まとめた本文（#876。`references/handoff-issue.md` の「まとめた本文」）。

    **部分は機能 1 件の本文から 1 行目（handoff の印）を外したもの**——印・節・機能の指紋・Red テストの sha256 がそのまま残るので、
    読む側（dev-loop の `spec-gap.md`・`rebuild-scope.py`）は部分ごとに機能 1 件の読み方を当てる。
    """
    ids = [c.feature["id"] for c in group]
    head = [
        HANDOFF_MARKER,
        BUNDLE_MARKER.format("・".join(ids)),
        "",
        "この Issue は spec-loop の `scaffold` が、確定した仕様から生成した。**本文を手で直さない。**",
        f"scaffold を回した人が、{len(ids)} 件の機能（変化はどれも `{group[0].kind}`）を 1 件にまとめた（`scaffold.py --bundle`）。"
        f"下に機能ごとの部分が `{BUNDLE_RULE}` の行で区切って並び、どの部分も機能 1 件の本文から 1 行目の印を外したもの——"
        "部分ごとに印・節・機能の指紋・Red テストの sha256 を持つ。**部分ごとに読み、確かめる。受入基準は、全部の部分の受入基準を合わせたものである。**",
        "",
    ] + [f"- [ ] `{c.feature['id']}` {cell(c.feature['title'])}" for c in group]
    return "\n".join(head) + "\n" + "".join(f"\n{BUNDLE_RULE}\n\n{bodies[fid].split(chr(10), 1)[1]}" for fid in ids)


def feature_bodies(changes: list[Change], loaded: Loaded, contract: dict[str, str], before: Before, base: str) -> dict[str, str]:
    """{機能の id: 機能 1 件の本文}。`base` は基準コミットの行（`base_commit`）。"""
    return {c.feature["id"]: issue_body(c, loaded, contract, before, base) for c in changes}


def render_issues(changes: list[Change], groups: list[list[Change]], bodies: dict[str, str], loaded: Loaded,
                  contract: dict[str, str], before: Before) -> dict[str, str]:
    """{Issue の本文のファイル名: 中身} を返す。本文は変わった機能だけで、`groups` の組 1 つが Issue 1 件（既定は 1 機能 = 1 件）。

    `issues.json` の項目は、まとめた組なら `feature` の代わりに `features` を持ち、依存があるときだけ `depends` を持つ（#876）。
    """
    impl_now = loaded.ir.get("impl_module", DEFAULT_IMPL_MODULE)
    issues, index = {}, []

    def red(change: Change) -> list[str]:
        rows, _ = case_changes(change, impl_now, before.impl_module)
        return [] if change.kind == REMOVE else [test_name(change.feature, c) for c in red_cases(rows)]

    for group, depends in zip(groups, dependencies(groups)):
        if len(group) == 1:
            change = group[0]
            fid = change.feature["id"]
            issues[f"{fid}.md"] = bodies[fid]
            entry = {"feature": fid, "title": issue_title(change, loaded.number), "change": change.kind,
                     "body": f"{fid}.md", "red": red(change)}
        else:
            ids = [c.feature["id"] for c in group]
            name = BUNDLE_FILE.format("-".join(ids))
            issues[name] = bundle_body(group, bodies)
            entry = {"features": ids, "title": bundle_title(group, loaded.number), "change": group[0].kind,
                     "body": name, "red": [test for c in group for test in red(c)]}
        if depends:
            entry["depends"] = depends
        index.append(entry)
    issues["issues.json"] = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    issues[PROPOSALS] = proposals(changes, loaded, contract)
    return issues


# ---------------------------------------------------------------- Red の状態を見る

# 子のプロセスで走らせる——実装を読み込むのは正本リポジトリの根（`python3 -m unittest discover` と同じ）
DRIVER = r'''
import json
import sys
import unittest

outcomes = {}


class Result(unittest.TestResult):
    def addSuccess(self, test):
        outcomes[test.id()] = "pass"

    def addFailure(self, test, err):
        outcomes[test.id()] = "missing" if str(err[1]).startswith(sys.argv[2]) else "fail"

    def addError(self, test, err):
        outcomes[test.id()] = "error"

    def addSkip(self, test, reason):
        outcomes[test.id()] = "skip"

    def addExpectedFailure(self, test, err):
        outcomes[test.id()] = "skip"

    def addUnexpectedSuccess(self, test):
        outcomes[test.id()] = "pass"


unittest.defaultTestLoader.discover(sys.argv[1], top_level_dir=sys.argv[1]).run(Result())
print("\n" + json.dumps(outcomes, ensure_ascii=False))
'''
RED_TIMEOUT = 600


def run_tests(repo: Path, tests: Path) -> dict:
    """`tests` の Red テストを正本リポジトリの根で走らせ、{テストの名前: 結果} を返す。走らせられなければ ValueError など。"""
    # -B: 正本リポジトリに __pycache__ を書かない（`--red-check` は何も書かない）
    proc = subprocess.run([sys.executable, "-B", "-c", DRIVER, str(tests), MISSING], cwd=repo,
                          capture_output=True, text=True, timeout=RED_TIMEOUT)
    outcomes = json.loads(proc.stdout.rstrip("\n").rsplit("\n", 1)[-1])
    if proc.returncode != 0 or not isinstance(outcomes, dict):
        raise ValueError(proc.stderr[-400:])
    return outcomes


def previous_outcomes(repo: Path, before: Before) -> dict:
    """前の版（v<n-1>）の全体の Red テストを、同じ実装に当てた結果。v1 なら空。

    **`scaffold/` には書かない**——一時ディレクトリに作って走らせる（`--red-check` は何も書かない）。
    """
    features = features_of(before.ir)
    if not features:
        return {}
    with tempfile.TemporaryDirectory(prefix="scaffold-previous-") as tmp:
        tests = Path(tmp) / "tests"
        tests.mkdir()
        for feature in features:
            (tests / test_file(feature)).write_text(red_test(feature, before.impl_module), encoding="utf-8")
        return run_tests(repo, tests)


def red_check(repo: Path, loaded: Loaded, changes: list[Change], before: Before, in_progress: bool) -> int:
    """ケースごとに、作業中の版の Red テストと前の版の Red テストの結果を並べて、実装の状態を見る。

    **実装が前の版の状態にあることを前提にしない**（`PREMISE`）——前の版の Red テストを同じ実装に当てて確かめる。
    `in_progress`: 作り直しの経路。追加・変更のケースは、前の版と作業中の版のどちらの期待を満たしてもよい。
    """
    impl_now = loaded.ir.get("impl_module", DEFAULT_IMPL_MODULE)
    red = set()
    for change in changes:
        if change.kind != REMOVE:
            rows, _ = case_changes(change, impl_now, before.impl_module)
            red |= {test_id(change.feature, case) for case in red_cases(rows)}
    expected = [test_id(f, c) for f in features_of(loaded.ir) for c in sorted(f["cases"], key=case_order)]
    try:
        outcomes = run_tests(repo, Path(OUT_DIR) / "tests")
        previous = previous_outcomes(repo, before)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Red テストを走らせられない（{exc.__class__.__name__}: {exc}）。判定していない", file=sys.stderr)
        return 2
    green = [t for t in expected if t not in red]
    if expected and green and all(outcomes.get(t) == "missing" for t in expected):
        print(f"実装が無い（どの Red テストも「{MISSING.strip()}」で失敗した）。回帰のケース {len(green)} 件を判定していない"
              f"——前の版の実装を読み込める場所で走らせる", file=sys.stderr)
        return 2
    problems, failing, satisfied, done = [], [], [], []
    for name in expected:
        got, was = outcomes.get(name), previous.get(name)
        if name in red:
            # 入力の名前や形を変える変更では、呼び出しの形が合わない側の版の Red テストはエラーで落ちる
            # ——もう一方の版のテストが緑なら、エラーはその版の「失敗」と同じに読む
            if got == "error" and was == "pass":
                got = "fail"
            elif was == "error" and got == "pass":
                was = "fail"
        if got is None:
            problems.append(f"{name}: 走らなかった")
        elif got in ("error", "skip"):
            problems.append(f"{name}: {'エラー' if got == 'error' else '飛ばされた'}（失敗でも緑でもない）")
        elif name not in red:
            if got != "pass":
                problems.append(f"{name}: {CASE_KEPT}のケースなのに失敗した")
        elif was in ("error", "skip"):
            problems.append(f"{name}: 前の版の Red テストが{'エラー' if was == 'error' else '飛ばされた'}"
                            "（前の版の状態を判定できない）")
        elif got != "pass" and was not in (None, "pass") and (got, was) != ("missing", "missing"):
            # どちらの版でも「実装が無い」は食い違いではない——片方だけなら、もう片方の期待を満たしていない
            # 作り直しでは、実装はもう前の版の状態に無いはず——食い違いはたいてい作りかけの実装の誤り（#300）
            problems.append(f"{name}: {CASE_ADDED}・{CASE_CHANGED}のケースが、前の版の期待も作業中の版の期待も満たさない"
                            + ("（作りかけの実装の誤りか、前の版の仕様とも食い違う）" if in_progress
                               else "（前の版の仕様とも食い違う）"))
        elif got != "pass":
            failing.append(name)
        elif was in (None, "pass"):
            satisfied.append(name)
        elif in_progress:
            done.append(name)
        else:
            problems.append(f"{name}: 前の版の期待を満たさず、作業中の版の期待をもう満たす——実装は前の版の状態に無い"
                            "（この版をもう実装し始めた作り直しなら --in-progress）")
    for line in problems:
        print(line, file=sys.stderr)
    if problems:
        print(f"Red の状態が期待と違う（{len(problems)} 件）", file=sys.stderr)
        return 1
    for name in satisfied:
        print(f"もう緑: {name}（{CASE_ADDED}・{CASE_CHANGED}のケースを、前の版の実装がもう満たす——"
              "Red テストはこの変化を判別しない。中間表現が仕様のとおりかを確かめる）")
    summary = (f"Red の状態は期待どおり: 失敗 {len(failing)} 件（{CASE_ADDED}・{CASE_CHANGED}）・"
               f"緑 {len(green)} 件（{CASE_KEPT}）")
    if satisfied:
        summary += f"・もう緑 {len(satisfied)} 件（{CASE_ADDED}・{CASE_CHANGED}。前の版の実装がもう満たす）"
    if in_progress:
        summary += f"・実装済み {len(done)} 件（{CASE_ADDED}・{CASE_CHANGED}。作り直しの経路）"
    print(summary)
    return 0


# ---------------------------------------------------------------- 書く・比べる

def generated_tests(out: Path) -> set[str]:
    """`scaffold/tests/` の Red テストと `scaffold/perf/` の性能テストのうち、生成の印を持つもの（`tests/<名前>`・`perf/<名前>`）。"""
    found = set()
    for folder, pattern in (("tests", "test_*.py"), (PERF_DIR, "perf_*.py")):
        tests = out / folder
        if not tests.is_dir():
            continue
        for path in tests.glob(pattern):
            try:
                head = path.read_text(encoding="utf-8").split("\n", 1)[0]
            except (OSError, UnicodeDecodeError):
                continue
            if GENERATED in head:
                found.add(f"{folder}/{path.name}")
    return found


def stale(out: Path, contract: dict[str, str]) -> list[str]:
    problems = []
    for rel, text in contract.items():
        path = out / rel
        try:
            current = path.read_bytes()
        except OSError:
            problems.append(f"{OUT_DIR}/{rel}: 無い（生成していない）")
            continue
        # 文字列で読むと改行が正規化され、CRLF に書き換えたものを新しいと言う
        if current != text.encode("utf-8"):
            problems.append(f"{OUT_DIR}/{rel}: 今の入力から作るものと違う（古い・手で直した）")
    for rel in sorted(generated_tests(out) - contract.keys()):
        problems.append(f"{OUT_DIR}/{rel}: " + ("性能の要求（nfr）を指す機能に無い性能テストが残っている" if rel.startswith(f"{PERF_DIR}/")
                                               else "中間表現に無い機能の Red テストが残っている"))
    return problems


def clear_issues(repo: Path) -> None:
    path = repo / ISSUES_DIR
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def write(repo: Path, contract: dict[str, str], issues: dict[str, str]) -> None:
    # **1 つ目のファイルに触る前に、全部をバイトにする**——符号化で落ちるなら、何も書かないうちに落ちる
    contract_bytes = {rel: text.encode("utf-8") for rel, text in contract.items()}
    issue_bytes = {name: text.encode("utf-8") for name, text in issues.items()}
    # **契約に触る前に前の Issue の本文を消す**——書き込みが途中で失敗しても、古い本文が新しい契約と並ばない
    clear_issues(repo)
    out = repo / OUT_DIR
    for rel in sorted(generated_tests(out) - contract.keys()):
        (out / rel).unlink()
    for rel, data in contract_bytes.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    target = repo / ISSUES_DIR
    target.mkdir(parents=True)
    for name, data in issue_bytes.items():
        (target / name).write_bytes(data)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--upto")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--red-check", action="store_true")
    parser.add_argument("--in-progress", action="store_true")
    parser.add_argument("--provisional", action="store_true")
    parser.add_argument("--bundle", action="append", default=[])
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    if args.bundle and (args.check or args.red_check):
        # 本文を作らないモードでは、まとめ方を見る相手が無い——受け付けると、何も確かめていないのに通ったと読める
        print("--bundle は書く生成か --dry-run と一緒にだけ使う（--check・--red-check は Issue の本文を作らない）", file=sys.stderr)
        return 2
    repo = Path(args.repo)
    writing = not (args.check or args.dry_run or args.red_check)
    if args.upto is not None:
        if not re.fullmatch(r"[1-9][0-9]*", args.upto):
            print("--upto には 1 以上の整数を渡す", file=sys.stderr)
            return 2
        if not (args.check or args.dry_run):
            # 古い版の契約を置くと、作業中の版の Issue が指すものと食い違う
            print("--upto は --check か --dry-run と一緒にだけ使う（書く生成・--red-check は作業中の版に当てる）",
                  file=sys.stderr)
            return 2
        args.upto = int(args.upto)
    if args.in_progress and not args.red_check:
        print("--in-progress は --red-check と一緒にだけ使う（作り直しの経路で Red の状態を見る）", file=sys.stderr)
        return 2
    if not repo.is_dir():
        print(f"{repo}: ディレクトリが無い。判定していない", file=sys.stderr)
        return 2
    args.bundle, problem = parse_bundles(args.bundle)
    if problem:
        # 書く生成なら前の本文を消す（2 の決まり）——まとめ方の誤りで止まっても、古い本文を登録させない
        return fail(repo, writing, 2, [problem])
    try:
        return run(repo, args, writing)
    except Exception as exc:  # 予期しない失敗も「作らなかった」(1) と区別し、古い Issue の本文を残さない
        lines = [f"予期しない失敗（{exc.__class__.__name__}: {exc}）。判定していない"]
        if writing:
            try:
                clear_issues(repo)
                lines.append(f"前の Issue の本文（{ISSUES_DIR}/）は消した。"
                             f"{OUT_DIR}/ は一部だけ書かれたかもしれない——--check で確かめる")
            except OSError as again:
                lines.append(f"前の Issue の本文（{ISSUES_DIR}/）を消せなかった（{again}）——登録しないこと")
        for line in lines:
            print(line, file=sys.stderr)
        return 2


def fail(repo: Path, writing: bool, code: int, lines: list[str]) -> int:
    if writing:
        clear_issues(repo)
        lines = lines + [f"前の Issue の本文（{ISSUES_DIR}/）は消した"]
    for line in lines:
        print(line, file=sys.stderr)
    return code


def run(repo: Path, args, writing: bool) -> int:
    try:
        code, lines, loaded = load(repo, args.upto, args.provisional)
    except Unjudged as exc:
        code, lines = 2, [str(exc)]
    if code:
        return fail(repo, writing, code, lines)

    contract = render_contract(loaded)
    features = len(loaded.ir["features"])
    cases = sum(len(f["cases"]) for f in loaded.ir["features"])
    if args.check:
        problems = stale(repo / OUT_DIR, contract)
        for line in problems:
            print(line, file=sys.stderr)
        if problems:
            print(f"{OUT_DIR}/ が古い（{len(problems)} 件）。scaffold.py で作り直す", file=sys.stderr)
            return 1
        print(f"{OUT_DIR}/ は新しい（v{loaded.number} まで・機能 {features} 件・ケース {cases} 件）")
        return 0

    try:
        code, lines, changes, before = classify(loaded)
    except Unjudged as exc:
        code, lines = 2, [str(exc)]
    if code:
        return fail(repo, writing, code, lines)
    for line in lines:
        # 止めずに知らせること（凍結した前の版を信じなかった。#357・呼ぶ機能が変わっていない。#609）
        print(line)
    if args.red_check:
        problems = stale(repo / OUT_DIR, contract)
        if problems:
            for line in problems:
                print(line, file=sys.stderr)
            print(f"{OUT_DIR}/ が古い（{len(problems)} 件）。作り直してから Red の状態を見る", file=sys.stderr)
            return 1
        return red_check(repo, loaded, changes, before, args.in_progress)
    groups, problems = group_changes(changes, args.bundle)
    if problems:
        # 引数の誤り（2）——まとめ方は中間表現ではなく引数が決める（#876）
        return fail(repo, writing, 2, problems + ["--bundle のまとめ方が使えない。生成しない（判定していない）"])
    base, unrecorded = base_commit(repo)
    bodies = feature_bodies(changes, loaded, contract, before, base)
    issues = render_issues(changes, groups, bodies, loaded, contract, before)
    marked = sorted(fid for fid, body in bodies.items() if PROVISIONAL_LINE in body)
    if marked:
        # 止めない（#875）——`--provisional` で通した仮回答に依存する本文を名指しする
        print(f"仮回答（{qa.PROVISIONAL}）に依存する本文 {len(marked)} 件（{'・'.join(marked)}）——本文の `## 仕様` の"
              f" `{PROVISIONAL_LINE.strip()}` の行と、受入基準の表の `{PROVISIONAL_CELL}` で印を付けた。"
              "利用者が確かめたら rebuild-scope.py で作り直す範囲を引く")
    if unrecorded:
        # 止めない（#874）——本文の `## 仕様` に「記録していない」と書き、ここでも知らせる
        print(f"基準コミットを{BASE_UNRECORDED}（{unrecorded}）——本文の `## 仕様` にそう書く")
    counted = "・".join(f"{kind} {sum(1 for c in changes if c.kind == kind)}" for kind in (ADD, MODIFY, REMOVE))
    summary = (f"機能 {features} 件・ケース {cases} 件。Issue の本文 {len(changes)} 件（{counted}）。"
               f"v{loaded.number - 1} から変わっていない機能の本文は作らない" if loaded.number > 1 and before.trusted else
               f"機能 {features} 件・ケース {cases} 件。Issue の本文 {len(changes)} 件（{counted}）")
    if len(groups) != len(changes):
        # 件数は機能の変化で数える（既定と同じ）。まとめたなら、Issue にする本文の数を足して言う（#876）
        merged_groups = [g for g in groups if len(g) > 1]
        summary += (f"。--bundle で {sum(len(g) for g in merged_groups)} 件の機能を {len(merged_groups)} 件の本文にまとめ、"
                    f"登録する本文は {len(groups)} 件")
    if args.dry_run:
        print(f"作れる（{summary}）。何も書いていない")
        return 0
    write(repo, contract, issues)
    print(f"作った: {OUT_DIR}/ と {ISSUES_DIR}/（{summary}）")
    entries = proposal_changes(changes)
    print(f"課題一覧（案）: {ISSUES_DIR}/{PROPOSALS}（案 {len(entries)} 件・未決定事項 "
          f"{sum(len(undecided(c.feature)) for c in entries)} 件）——scaffold は案を登録しない。"
          "未決定事項のある案は、登録の前に spec-review に戻す")
    print("**条件 2〜5 は判定していない**——spec-review が「抜けた」と報告したことを確かめてから登録する")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
