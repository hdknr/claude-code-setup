#!/usr/bin/env python3
"""`check-spec-exit.py` の回帰テスト。

    python3 scripts/test-check-spec-exit.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-qa-csv.py` と同じ形。

見るもの:

1. **条件 1 を満たさない形を、理由つきで落とす**（仕様に反映した状態でない行・未決定の印・列検査を通らない表）。
   **暫定反映の行は止めない**（資料に載る行とは別の定義。#325）。
2. **満たす形を通す**（陽性対照。`未定義` や `mastodon` のような印でない語で落ちないこと）。
   **形式検査のモデル（仕様のディレクトリの中の `formal/`）の中の印は見ない**（#908。接頭辞だけ同じ `formalx.md` の印は見る。
   モデルだけでは仕様のファイルが 1 つも無いのと同じ）。
3. **判定できない形を 0 にしない**（仕様のディレクトリが無い・空・Q&A 表が読めない・読めた仕様がどれも中身が空。
   **中身のあるファイルが横にあれば、空のファイルでは止めない**——#291）。
4. **0 で終わっても「抜けた」とは言わない**——出力に「条件 2〜5 は判定していない」が出る。
5. **本体の定数が `references/spec-exit.md` の「未決定の印」の表と一致する**（写しのずれ）。
3'. **想定外の例外（128KB 超のセルの `csv.Error`）も 2 で、トレースバックの 1 にしない**。`-OO`（docstring が無い）で
   引数なしに呼んでも使い方の誤りとして 2（#286）。
7. **テストケースの番号の重複を 1 で落とす**（#1297）——同じファイル・別のファイルで同じ番号が 2 回以上出たら、番号と出た場所（`ファイル:行`）を全部名指しする。
   重複の無い仕様・先頭のセル以外の言及・コードブロックの中・形の外の識別子（連番 `1`・数字の無い名前）・`.md` 以外・形式検査のモデルは数えない（陰性対照）。
   **後の版が同じファイルを置き換えたのは重複に数えない**（`merge-versions.py` で重ねた全体に当てる。別のファイルに同じ番号を置けば 1）。
   **番号の形が `references/spec-exit.md` の「テストケースの番号の重複」と一致する**（写しのずれ）。
   **テストケースの節（`#` の見出しの末尾がテストケースの語。小見出しの下を含む）の中では、見出しが `ID`・`No`・`項番` の表も読み、節の外では読まない**（#1333。`ID_HEADER`・`SECTION_HEADER` の写しも突き合わせる）。
   **節を閉じるのは段落の直後の下線（`===`・`---`。項の中の段落なら項の中身の桁まで字下げした下線）だけで、区切りの線・中身が段落の箇条書きの項と引用の続きの行・HTML の塊・4 字下げのコードの直後の `---` では閉じない**（#1379。CommonMark の段落の続き。閉じる形——複数行の段落・段落を割り込めない行・中身が段落でない項と引用の後・項の中身の桁の下線——は陰性対照。CommonMark の参照は pandoc で確かめた形）。
8. **「呼ぶ側の分岐」の行が 8 分岐のどれかに触れていなければ 1 で落とし、行と欠けた分岐を名指しする**（#1340）——見出し・項目の行・表の行・表の見出しの 4 つの形・
   まとめて書く書き方・行ごと該当なしは通し、組の名前だけ（`量: …`）・組に無い述語・別の節を指す書き方（「…と同じ」）・空の文は触れないと読む。
   **表の行のうちほかの行を指す案内は、鉤括弧の名指しか「節」「参照」「下」の語を伴うものだけで、`呼ぶ側の分岐` の語を含む書きかけの行はほかに行があっても名指す**（#1389）。
   **組と分岐の表が `references/spec-exit.md` の「呼ぶ側の分岐の行の形」と、分岐の名前が `references/spec-ir.md` の分岐の名前の表と一致する**（写しのずれ）。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、
穴が無くても緑になるので）。
"""
from __future__ import annotations

import ast
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-spec-exit.py"
REFERENCE = PLUGIN / "references" / "spec-exit.md"

HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
DONE_ROW = "Q-001,仕様レビュー（Red Team）,通信が切れたら？,A: 取り消す / B: 残す,A,理由,A（業務部が回答）,spec/order.md,反映済み,\n"
OPEN_ROW = "Q-002,仕様レビュー（Domain Checker）,端数は？,A: 切り捨て / B: 四捨五入,A,理由,未回答,—,確認中,\n"
# 回答はあるが未反映——これも仕様に反映した状態でない
ANSWERED_ROW = "Q-003,仕様レビュー（Formal Checker）,上限は？,A: 拒否 / B: 切り詰める,B,理由,B（業務部が回答）,—,確認中,\n"
# 暫定の回答で反映した——仕様には反映済みなので条件 1 を止めない（#325）
PROVISIONAL_ROW = "Q-005,仕様レビュー（Red Team）,上限は？,A: なし / B: 5000 円,A,理由,A（業務部 2026-10-21 の指示）,spec/order.md,暫定反映,\n"
# `反映済み` で `回答` に「暫定で採用」と書いた行（#366 の実データの形）。暫定は状態だけで決まる——暫定に数えない（#404）
WORDED_ROW = "Q-006,仕様レビュー（Red Team）,返品は？,A: 可 / B: 不可,A,理由,A（推奨案を暫定で採用。開発側の指示）,spec/order.md,反映済み,\n"
BAD_ROW = "Q-004,仕様レビュー,選択肢が 1 つ,A: これだけ,A,理由,未回答,—,確認中,\n"
# 内部の Q&A 表（spec/qa-dev.csv）の行。質問の文に印の語（未定）を入れておく——表は印として数えない（#339）
INTERNAL_DONE = "D-001,仕様レビュー（Red Team）,上限が未定のときの再試行の間隔は,A: 10 秒 / B: 60 秒,B,呼び出しの上限,B（開発 2026-10-22）,spec/order.md,反映済み,\n"
INTERNAL_OPEN = "D-002,仕様レビュー（Red Team）,ワーカーを分けるか,A: 分ける / B: 分けない,B,費用,未回答,—,確認中,\n"
CLEAN_SPEC = "# 注文\n\n未定義の状態に遷移しない。\nmastodon のような語も、TODOS も印ではない。\n"

# テストケースの番号の重複（#1297）。表の行の先頭のセルが番号
CASE_HEAD = "| テストケース | 入力 | 期待 |\n| --- | --- | --- |\n"
CASE_TABLE = "# 注文\n\n" + CASE_HEAD + "| F1-5a | 1 | 通る |\n| F1-5b | 2 | 拒否 |\n"
DUP = "重複"

# 呼ぶ側の分岐の行の揃い（#1340）。見出しの形の行で、8 分岐に 1 行ずつ触れる
CALLER_ITEMS = ["- 入力が欠ける: 「データ欠落」と表示する", "- 入力が遅れる: 「取得中」と表示する", "- 入力の順が崩れる: 該当なし（1 回で届く）",
                "- 呼ぶ処理が失敗する: 「再計算待ち」と表示する", "- 呼ぶ処理がやり直される: 該当なし（呼ばない）",
                "- 呼ぶ処理が再起動する: 該当なし（呼ばない）", "- 量が上限を超える: 「上限」と表示する", "- 量が重なる: 該当なし（1 件ずつ）"]
CALLER_HEAD = "## 受注\n\n### 呼ぶ側の分岐\n\n"
CALLER_FULL = CALLER_HEAD + "\n".join(CALLER_ITEMS) + "\n"
# まとめて書く書き方（組の名前に分岐を並べる）
CALLER_GROUPED = ["- 入力が欠ける・遅れる・順が崩れる: 該当なし（1 回で届く）", "- 呼ぶ処理が失敗する・やり直される・再起動する: 該当なし（呼ばない）",
                  "- 量が上限を超える・重なる: 該当なし（1 件ずつ）"]
CALLER_TABLE_HEAD = "| 項目 | 書くもの |\n| --- | --- |\n"
GAP = "触れていない"

def after_case_table(middle: str) -> dict[str, str]:
    """テストケースの節の ID の表（F1-1）の後ろに `middle` を置き、同じ番号の ID の表を続けた仕様（#1379）。
    節を閉じていなければ 2 つ目の表も数えて重複（1）、閉じていれば数えずに 0。"""
    table = "| ID | 手順 |\n| --- | --- |\n"
    return {"order.md": "## テストケース\n\n" + table + "| F1-1 | a |\n\n" + middle + table + "| F1-1 | b |\n"}


# (名前, qa.csv の中身（None なら作らない）, {仕様の相対パス: 中身}（None ならディレクトリを作らない）,
#  期待する終了コード, 出力に含まれるべき文字列)
CASES: list[tuple[str, str | bytes | None, dict[str, str | bytes] | None, int, str]] = [
    ("満たす", HEADER + DONE_ROW, {"order.md": CLEAN_SPEC}, 0, "条件 2〜5 は判定していない"),
    ("見出しだけの表", HEADER, {"order.md": CLEAN_SPEC}, 0, "条件 1 を満たす"),
    ("確認中の行", HEADER + DONE_ROW + OPEN_ROW, {"order.md": CLEAN_SPEC}, 1, "Q-002: 状態が 確認中"),
    ("暫定反映は止めない", HEADER + DONE_ROW + PROVISIONAL_ROW, {"order.md": CLEAN_SPEC}, 0,
     "暫定反映の行（仕様には反映済み・利用者の確認待ち）: 1 件"),
    ("文言だけ暫定の反映済みは暫定に数えない", HEADER + DONE_ROW + WORDED_ROW, {"order.md": CLEAN_SPEC}, 0,
     "暫定反映の行（仕様には反映済み・利用者の確認待ち）: 0 件"),
    ("暫定反映と確認中", HEADER + PROVISIONAL_ROW + OPEN_ROW, {"order.md": CLEAN_SPEC}, 1, "Q-002: 状態が 確認中"),
    ("回答はあるが未反映", HEADER + ANSWERED_ROW, {"order.md": CLEAN_SPEC}, 1, "Q-003: 状態が 確認中"),
    ("列検査を通らない表", HEADER + BAD_ROW, {"order.md": CLEAN_SPEC}, 1, "列検査を通らない"),
    ("TBD", HEADER, {"order.md": CLEAN_SPEC + "リトライ回数は TBD。\n"}, 1, "order.md:5: 未決定の印 TBD"),
    ("小文字の todo", HEADER, {"order.md": "- todo: 上限\n"}, 1, "未決定の印 todo"),
    ("日本語に挟まれた TODO", HEADER, {"order.md": "割引はTODOとする\n"}, 1, "未決定の印 TODO"),
    ("未定", HEADER, {"order.md": "割引: 未定\n"}, 1, "未決定の印 未定"),
    ("未定義と未定が同じ行", HEADER, {"order.md": "未定義の値は未定\n"}, 1, "未決定の印 未定"),
    ("要確認", HEADER, {"order.md": "端数（要確認）\n"}, 1, "未決定の印 要確認"),
    ("入れ子のファイル", HEADER, {"order.md": CLEAN_SPEC, "rules/rules.py": "# TODO 下限\n"}, 1,
     "rules.py:1: 未決定の印 TODO"),
    # 形式検査のモデル（formal/）は仕様から書き起こした写し——記録の「置いた前提」に未決定のことを書いてよい（#908）
    ("形式検査のモデルの中の印は見ない", HEADER, {"order.md": CLEAN_SPEC, "formal/order/README.md": "置いた前提: 端数は未定\n",
                                           "formal/order/Order.tla": "\\* TODO 下限\n"}, 0, "条件 1 を満たす"),
    # 陽性対照: 接頭辞だけ同じ formalx.md は仕様のファイル
    ("formal と接頭辞だけ同じファイルの印は見る", HEADER, {"order.md": CLEAN_SPEC, "formalx.md": "下限は TBD\n"}, 1,
     "formalx.md:1: 未決定の印 TBD"),
    ("formal という名前のファイルの印は見る", HEADER, {"order.md": CLEAN_SPEC, "formal": "下限は TBD\n"}, 1,
     "formal:1: 未決定の印 TBD"),
    # 形式検査のモデルだけでは仕様を書いたことにならない
    ("形式検査のモデルだけ", HEADER, {"formal/order/Order.tla": "---- MODULE Order ----\n"}, 2, "ファイルが 1 つも無い"),
    ("印が無い行の後ろに印", HEADER, {"order.md": CLEAN_SPEC, "flow.md": "a\nb\nc TBD\n"}, 1, "flow.md:3"),
    ("読めないファイルは件数を出して通す", HEADER, {"order.md": CLEAN_SPEC, "fig.png": b"\x89PNG\xff\xfe"}, 0,
     "見なかったファイル（読めない・UTF-8 でない）: 1 件"),
    # 見ていない仕様を「印 0 件」と言わない（UTF-16 で書いた仕様の TBD を見落として 0 にしていた）
    ("図以外に読めない仕様", HEADER, {"order.md": "割引は TBD\n".encode("utf-16")}, 2, "図以外に読めないファイルが 1 件"),
    # 読める別ファイルが混ざっても同じ（全部読めないときだけ 2 にしていた）
    ("読めない仕様と読める README", HEADER,
     {"order.md": "割引は TBD\n".encode("utf-16"), "README.md": "目次\n"}, 2, "図以外に読めないファイルが 1 件"),
    # ASCII だけの UTF-16 は UTF-8 として復号できてしまう（NUL は有効）。NUL で読めない側に数える
    ("BOM の無い ASCII の UTF-16", HEADER, {"a.md": "Status: TBD\n".encode("utf-16-le")}, 2,
     "図以外に読めないファイルが 1 件"),
    ("図だけ", HEADER, {"fig.png": b"\x89PNG\xff\xfe"}, 2, "どの仕様も読めなかった"),
    # 読めないファイルがあっても、印が見つかれば満たさないことは確か
    ("読めない仕様と印のある仕様", HEADER,
     {"order.md": "割引は TBD\n".encode("utf-16"), "flow.md": "TODO\n"}, 1, "flow.md:1: 未決定の印 TODO"),
    # 全角の英字は IGNORECASE では半角にならない
    ("全角の ＴＢＤ", HEADER, {"order.md": "仕様はＴＢＤ。\n"}, 1, "未決定の印 TBD"),
    ("ドット始まりは見ない", HEADER, {"order.md": CLEAN_SPEC, ".cache/x.md": "TODO\n"}, 0, "条件 1 を満たす"),
    ("内部の表の確認中は止める", HEADER + DONE_ROW, {"order.md": CLEAN_SPEC, "qa-dev.csv": HEADER + INTERNAL_OPEN}, 1,
     "D-002: 状態が 確認中"),
    ("内部の表の反映済みは通す（文の印は数えない）", HEADER + DONE_ROW,
     {"order.md": CLEAN_SPEC, "qa-dev.csv": HEADER + INTERNAL_DONE}, 0, "条件 1 を満たす"),
    ("内部の表が列検査を通らない", HEADER, {"order.md": CLEAN_SPEC, "qa-dev.csv": HEADER + DONE_ROW}, 1,
     "`No` が `D-S-001` の形でない"),
    ("内部の表が読めない", HEADER, {"order.md": CLEAN_SPEC, "qa-dev.csv": b"\xff\xfe\x00"}, 2, "内部の Q&A 表を読めない"),
    ("内部の表だけでは仕様が無い", HEADER, {"qa-dev.csv": HEADER + INTERNAL_DONE}, 2, "ファイルが 1 つも無い"),
    ("入れ子の qa-dev.csv は仕様のファイル", HEADER, {"order.md": CLEAN_SPEC, "sub/qa-dev.csv": "未定\n"}, 1, "未決定の印 未定"),
    ("仕様のディレクトリが無い", HEADER, None, 2, "ディレクトリが無い"),
    ("仕様が空", HEADER, {}, 2, "ファイルが 1 つも無い"),
    ("ドット始まりしか無い", HEADER, {".keep": ""}, 2, "ファイルが 1 つも無い"),
    # 見た仕様に中身が 0 なら、書いていない仕様と同じ（#217 の狭いパス N1。#291）
    ("空のファイルだけ", HEADER, {"a.md": b""}, 2, "読めた仕様がどれも中身が空（1 ファイル）"),
    ("空白と改行だけのファイル", HEADER, {"a.md": " \n\t\n\u3000\n"}, 2, "読めた仕様がどれも中身が空（1 ファイル）"),
    ("BOM だけのファイル", HEADER, {"a.md": b"\xef\xbb\xbf"}, 2, "読めた仕様がどれも中身が空（1 ファイル）"),
    ("空のファイルと図", HEADER, {"a.md": b"", "fig.png": b"\x89PNG\xff\xfe"}, 2, "読めた仕様がどれも中身が空（1 ファイル）"),
    # 中身のある仕様が 1 つでもあれば、横の空のファイルでは止めない（空のファイルが 1 つでもあれば 2、ではない）
    ("空のファイルと中身のある仕様", HEADER, {"a.md": b"", "order.md": CLEAN_SPEC}, 0, "条件 1 を満たす"),
    # 反映が残る行が別にあれば、満たさないことは確か（1 を優先）
    ("空のファイルと確認中の行", HEADER + OPEN_ROW, {"a.md": b""}, 1, "Q-002: 状態が 確認中"),
    # テストケースの番号の重複（#1297）。表の見出しの先頭のセルが `ケース`・`テスト` を含む表の、データ行の先頭のセルが番号。order.md の 6 行目が `F1-5b`
    ("番号の重複が無い表（陰性対照）", HEADER, {"order.md": CASE_TABLE}, 0, "条件 1 を満たす"),
    ("同じファイルの重複", HEADER, {"order.md": CASE_TABLE + "| F1-5b | 3 | 拒否 |\n"}, 1,
     "order.md:6: テストケースの番号 F1-5b が 2 か所で重複"),
    ("同じファイルの重複は後ろの場所も名指しする", HEADER, {"order.md": CASE_TABLE + "| F1-5b | 3 | 拒否 |\n"}, 1, "order.md:7）"),
    ("別のファイルの重複", HEADER, {"order.md": CASE_TABLE, "flow.md": CASE_HEAD + "| F1-5b | 9 | 通る |\n"}, 1, "flow.md:3"),
    ("別のファイルの重複は先のファイルの場所も名指しする", HEADER,
     {"order.md": CASE_TABLE, "flow.md": CASE_HEAD + "| F1-5b | 9 | 通る |\n"}, 1, "order.md:6"),
    ("3 か所の重複", HEADER, {"order.md": CASE_TABLE + "| F1-5b | 3 | 拒否 |\n| F1-5b | 4 | 拒否 |\n"}, 1, "3 か所で重複"),
    ("入れ子のディレクトリとの重複", HEADER, {"order.md": CASE_TABLE, "rules/flow.md": CASE_HEAD + "| F1-5b | 9 | 通る |\n"}, 1, "flow.md:3"),
    ("重複と未決定の印の両方を出す", HEADER, {"order.md": CASE_TABLE + "| F1-5b | 3 | TBD |\n"}, 1, "未決定の印 TBD"),
    ("等幅の飾りを外して数える", HEADER, {"order.md": CASE_TABLE, "flow.md": CASE_HEAD + "| `F1-5b` | 9 | 通る |\n"}, 1, "flow.md:3"),
    ("強調の飾りを外して数える", HEADER, {"order.md": CASE_TABLE, "flow.md": CASE_HEAD + "| **F1-5b** | 9 | 通る |\n"}, 1, "flow.md:3"),
    ("アンダースコアの飾りを外して数える", HEADER, {"order.md": CASE_TABLE, "flow.md": CASE_HEAD + "| _F1-5b_ | 9 | 通る |\n"}, 1, "flow.md:3"),
    ("全角の英数字とハイフンを半角にそろえて数える", HEADER,
     {"order.md": CASE_TABLE, "flow.md": CASE_HEAD + "| Ｆ１－５ｂ | 9 | 通る |\n"}, 1, "flow.md:3"),
    ("決定表の行の番号もテストケースの表の先頭のセルなら数える", HEADER,
     {"order.md": CASE_HEAD + "| R-F10 | 9999 | 0 |\n", "flow.md": CASE_HEAD + "| R-F10 | 10000 | 500 |\n"}, 1, "テストケースの番号 R-F10"),
    ("英語の見出しでも数える", HEADER,
     {"order.md": "| Test Case | in |\n|---|---|\n| F1-5b | 1 |\n", "flow.md": "| TC | in |\n|:--|--:|\n| F1-5b | 2 |\n"}, 1, "flow.md:3"),
    ("末尾の `|` が無い行も表の行", HEADER, {"order.md": CASE_TABLE, "flow.md": CASE_HEAD + "  | F1-5b\n"}, 1, "flow.md:3"),
    # テストケースの表でない表は数えない（Verifier 1 パス目の R1）
    ("Q&A の番号を引く表は数えない", HEADER,
     {"order.md": "| 質問 | 内容 |\n| --- | --- |\n| Q-001 | 割引しない |\n", "flow.md": "| 質問 | 内容 |\n| --- | --- |\n| Q-001 | 通知しない |\n"}, 0,
     "条件 1 を満たす"),
    ("決定表の行の番号を並べた表は数えない", HEADER,
     {"order.md": "| 決定表の行 | 入力 | 期待 |\n| --- | --- | --- |\n| R-F10 | 9999 | 0 |\n| R-F10 | 10000 | 500 |\n"}, 0, "条件 1 を満たす"),
    ("ユースケースの表は数えない", HEADER,
     {"order.md": "| ユースケース | 内容 |\n| --- | --- |\n| UC-01 | a |\n", "flow.md": "| ユースケース | 内容 |\n| --- | --- |\n| UC-01 | b |\n"}, 0, "条件 1 を満たす"),
    ("テスト環境・Latest の表は数えない", HEADER,
     {"order.md": "| テスト環境 | a |\n| --- | --- |\n| ENV-1 | a |\n\n| Latest | a |\n| --- | --- |\n| R-1 | a |\n",
      "flow.md": "| テスト環境 | a |\n| --- | --- |\n| ENV-1 | b |\n\n| Latest | a |\n| --- | --- |\n| R-1 | b |\n"}, 0, "条件 1 を満たす"),
    ("見出しが ID・No の表は読まない（見逃しの限界）", HEADER,
     {"order.md": "| ID | 手順 |\n| --- | --- |\n| TC-001 | a |\n| TC-001 | b |\n", "flow.md": "| No | 手順 |\n| --- | --- |\n| TC-001 | c |\n"}, 0,
     "条件 1 を満たす"),
    # テストケースの節（直前の見出しが CASE_HEADER に当たる）の ID・No・項番の表は読む（#1333）
    ("テストケースの節の ID の表は読む", HEADER,
     {"order.md": "## テストケース\n\n| ID | 手順 |\n| --- | --- |\n| TC-001 | a |\n| TC-001 | b |\n"}, 1, "テストケースの番号 TC-001"),
    ("テストケースの節の No. の表も読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "### テストケース\n| No. | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("テストケースの節の項番の表も読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "### テストケース\n| 項番 | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("テストケースの節の小文字の id の表も読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "## テストケース\n| id | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("テストケースの節の強調した ID の表も読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "## テストケース\n| **ID** | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("全角の節の見出しもそろえて読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "## ＴＣ\n| ID | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("小見出しの下も節の中", HEADER,
     {"order.md": "## テストケース\n\n### 正常系\n\n| ID | 手順 |\n| --- | --- |\n| F1-1 | a |\n\n#### 境界\n\n### 異常系\n\n| ID | 手順 |\n| --- | --- |\n| F1-1 | b |\n"}, 1,
     "テストケースの番号 F1-1"),
    ("浅い見出しで節を抜ける", HEADER,
     {"order.md": "### テストケース\n\n" + CASE_HEAD + "| F1-1 | a | b |\n\n## 質問\n\n| ID | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0,
     "条件 1 を満たす"),
    ("末尾が一覧の節の見出しも読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "## F2 のテストケース一覧\n| ID | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("括弧書きの付いた節の見出しも読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "## TC（注文）\n| ID | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("テストケースの語で終わらない見出しは節でない", HEADER,
     {"order.md": "## テストケースの前提となるマスタ\n\n| ID | 名前 |\n| --- | --- |\n| M-001 | a |\n| M-001 | b |\n"}, 0, "条件 1 を満たす"),
    ("下線の見出しで節を閉じる", HEADER,
     {"order.md": "## テストケース\n\n" + CASE_HEAD + "| F1-1 | a | b |\n\n質問\n----\n\n| ID | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0,
     "条件 1 を満たす"),
    ("飾りと末尾のコロンを外した節の見出しも読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "## **テストケース**:\n| ID | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("閉じの # を外した節の見出しも読む", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "## テストケース ##\n| ID | 手順 |\n| --- | --- |\n| F1-5b | c |\n"}, 1, "flow.md:4"),
    ("区切りの線では節を閉じない", HEADER,
     {"order.md": "## テストケース\n\n| ID | 手順 |\n| --- | --- |\n| F1-1 | a |\n\n---\n\n| ID | 手順 |\n| --- | --- |\n| F1-1 | b |\n\n***\n\n| ID | 手順 |\n| --- | --- |\n| F1-1 | c |\n"}, 1,
     "3 か所で重複"),
    # 段落の直後でない区切りの線は節を閉じない——段落かどうかを CommonMark の段落の続きに合わせる（#1379）。
    # 区切りの線の後ろの ID の表も数えて 2 か所の重複になれば、節を閉じていない
    ("本文の後に続く 2 本目の区切りの線では節を閉じない", HEADER, after_case_table("本文\n\n---\n---\n\n"), 1, "2 か所で重複"),
    ("間に空行のある 2 本の区切りの線でも節を閉じない", HEADER, after_case_table("本文\n\n---\n\n---\n\n"), 1, "2 か所で重複"),
    ("*** の直後の区切りの線では節を閉じない", HEADER, after_case_table("本文\n\n***\n---\n\n"), 1, "2 か所で重複"),
    ("箇条書きの直後の区切りの線では節を閉じない", HEADER, after_case_table("- a\n---\n\n"), 1, "2 か所で重複"),
    ("番号つきの項の直後の区切りの線では節を閉じない", HEADER, after_case_table("1. a\n---\n\n"), 1, "2 か所で重複"),
    ("箇条書きの続きの行の後の区切りの線では節を閉じない", HEADER, after_case_table("- a\n続き\n---\n\n"), 1, "2 か所で重複"),
    ("段落を割り込んだ箇条書きの後の区切りの線では節を閉じない", HEADER, after_case_table("本文\n- a\n---\n\n"), 1, "2 か所で重複"),
    ("引用の直後の区切りの線では節を閉じない", HEADER, after_case_table("> a\n---\n\n"), 1, "2 か所で重複"),
    ("引用の続きの行の後の区切りの線では節を閉じない", HEADER, after_case_table("> a\n続き\n---\n\n"), 1, "2 か所で重複"),
    ("HTML コメントの直後の区切りの線では節を閉じない", HEADER, after_case_table("<!-- c -->\n---\n\n"), 1, "2 か所で重複"),
    ("複数行の HTML コメントの直後の区切りの線では節を閉じない", HEADER, after_case_table("<!--\nc\n-->\n---\n\n"), 1, "2 か所で重複"),
    ("HTML コメントの中の本文と線では節を閉じない", HEADER, after_case_table("<!--\n本文\n---\n-->\n\n"), 1, "2 か所で重複"),
    ("空行を挟んだ pre の中の本文と線では節を閉じない", HEADER, after_case_table("<pre>\n\n本文\n---\n</pre>\n\n"), 1, "2 か所で重複"),
    ("処理命令の直後の区切りの線では節を閉じない", HEADER, after_case_table("<?php x ?>\n---\n\n"), 1, "2 か所で重複"),
    ("宣言の直後の区切りの線では節を閉じない", HEADER, after_case_table("<!DOCTYPE html>\n---\n\n"), 1, "2 か所で重複"),
    ("CDATA の直後の区切りの線では節を閉じない", HEADER, after_case_table("<![CDATA[x]]>\n---\n\n"), 1, "2 か所で重複"),
    ("段落を割り込んだ div の中の本文と線では節を閉じない", HEADER, after_case_table("本文\n<div>\n本文\n---\n\n"), 1, "2 か所で重複"),
    ("タグだけの行の直後の区切りの線では節を閉じない", HEADER, after_case_table("<span>\n---\n\n"), 1, "2 か所で重複"),
    ("4 字下げのコードの直後の区切りの線では節を閉じない", HEADER, after_case_table("    code\n---\n\n"), 1, "2 か所で重複"),
    ("タブで字下げしたコードの直後の区切りの線では節を閉じない", HEADER, after_case_table("  \tcode\n---\n\n"), 1, "2 か所で重複"),
    # 段落の直後の下線は今までどおり節を閉じる（#1379 の陰性対照）
    ("複数行の段落の下線で節を閉じる", HEADER, after_case_table("本文\n続き\n---\n\n"), 0, "条件 1 を満たす"),
    ("4 字下げの続きの行を持つ段落の下線で節を閉じる", HEADER, after_case_table("本文\n    続き\n---\n\n"), 0, "条件 1 を満たす"),
    ("引用の後に空行を挟んだ段落の下線で節を閉じる", HEADER, after_case_table("> a\n\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    ("コードの後の段落の下線で節を閉じる", HEADER, after_case_table("    code\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    ("1 でない番号の行は段落を割り込まない", HEADER, after_case_table("本文\n2. a\n---\n\n"), 0, "条件 1 を満たす"),
    ("空の項は段落を割り込まない", HEADER, after_case_table("本文\n*\n---\n\n"), 0, "条件 1 を満たす"),
    ("タグだけの行は段落を割り込まない", HEADER, after_case_table("本文\n<span>\n---\n\n"), 0, "条件 1 を満たす"),
    ("HTML の塊の後に空行を挟んだ段落の下線で節を閉じる", HEADER, after_case_table("<div>\n\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    ("閉じた HTML コメントの後の段落の下線で節を閉じる", HEADER, after_case_table("<!-- c -->\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    ("フェンスの後の段落の下線で節を閉じる", HEADER, after_case_table("- a\n```\nx\n```\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    ("小見出しの後の段落の下線で節を閉じる", HEADER, after_case_table("- a\n### 小\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    # 2 パス目の指摘（#1379）——中身が段落でない項・引用の後は新しい段落、項の中の桁を空行をまたいで持つ
    ("空行の後の項の外の区切りの線では節を閉じない", HEADER, after_case_table("- a\n\n  b\n---\n\n"), 1, "2 か所で重複"),
    ("空の項の次の行の項の中身の段落の下線で節を閉じる", HEADER, after_case_table("-\n    code\n  ---\n\n"), 0, "条件 1 を満たす"),
    # 狭いパスの指摘（#1379）——空の項の後の空行で項を閉じる・同じ行で入れ子になった項の桁を積む
    ("空の項の後の空行で項を閉じる（字下げの段落と線では閉じない）", HEADER, after_case_table("-\n\n    a\n    ---\n\n"), 1, "2 か所で重複"),
    ("空の項の後の空行で項を閉じる（段落の下線で閉じる）", HEADER, after_case_table("-\n\n  a\nb\n---\n\n"), 0, "条件 1 を満たす"),
    ("同じ行で入れ子になった項の中身の桁の下線で節を閉じる", HEADER, after_case_table("- - x\n    ---\n\n"), 0, "条件 1 を満たす"),
    ("同じ行で入れ子になった項の中身の桁に届かない線では節を閉じない", HEADER, after_case_table("- - x\n  ---\n\n"), 1, "2 か所で重複"),
    ("HTML コメントの閉じの行の後の区切りの線では節を閉じない", HEADER, after_case_table("<!--\n本文\n-->\n---\n\n"), 1, "2 か所で重複"),
    ("見出しで始まる引用の後の段落の下線で節を閉じる", HEADER, after_case_table("> ###### 注記\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    ("区切りの線で始まる項の後の段落の下線で節を閉じる", HEADER, after_case_table("- ***\nb\n---\n\n"), 0, "条件 1 を満たす"),
    ("引用で始まる項の後の続きの行と線では節を閉じない", HEADER, after_case_table("- > q\nb\n  ---\n\n"), 1, "2 か所で重複"),
    ("HTML で始まる項の中の本文と線では節を閉じない", HEADER, after_case_table("- <div>\n  b\n  ---\n\n"), 1, "2 か所で重複"),
    ("項の外の行で項の中の HTML の塊を閉じる", HEADER, after_case_table("- <div>\nb\n本文\n   ---\n\n"), 0, "条件 1 を満たす"),
    ("3 段目の項の中身の桁に届かない下線では節を閉じない", HEADER, after_case_table("- a\n  - b\n    - c\n    ---\n\n"), 1, "2 か所で重複"),
    ("空行の後の項の中の字下げの段落の下線で節を閉じる", HEADER, after_case_table("- a\n\n    b\n  ---\n\n"), 0, "条件 1 を満たす"),
    ("項の外のタグだけの行は HTML の塊を始める", HEADER, after_case_table("  - b\n<span>\n    ---\n\n"), 1, "2 か所で重複"),
    ("タブで字下げした項の中の下線で節を閉じる", HEADER, after_case_table("- a\n\t---\n\n"), 0, "条件 1 を満たす"),
    ("コードで始まる項の後の字下げの段落の下線で節を閉じる", HEADER, after_case_table("-     code\n\tcode\n  ---\n\n"), 0, "条件 1 を満たす"),
    ("空の引用の行の後の段落の下線で節を閉じる", HEADER, after_case_table("> a\n>\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    ("空の項の後の段落の下線で節を閉じる", HEADER, after_case_table("-\n本文\n---\n\n"), 0, "条件 1 を満たす"),
    ("項の中身の桁まで字下げした下線で節を閉じる", HEADER, after_case_table("- a\n  ---\n\n"), 0, "条件 1 を満たす"),
    ("番号つきの項の中身の桁まで字下げした下線で節を閉じる", HEADER, after_case_table("1. a\n   ---\n\n"), 0, "条件 1 を満たす"),
    ("項の続きの行の後の中身の桁の下線で節を閉じる", HEADER, after_case_table("- a\nb\n  ---\n\n"), 0, "条件 1 を満たす"),
    ("入れ子の項の中身の桁に届かない下線では節を閉じない", HEADER, after_case_table("- a\n  - b\n  ---\n\n"), 1, "2 か所で重複"),
    ("印の後ろの空白まで中身の桁に数える", HEADER, after_case_table("-   a\n  ---\n\n"), 1, "2 か所で重複"),
    ("コードで始まる項の後の下線では節を閉じない", HEADER, after_case_table("-     code\n  ---\n\n"), 1, "2 か所で重複"),
    ("== の下線の見出しでも節を閉じる", HEADER,
     {"order.md": "## テストケース\n\n" + CASE_HEAD + "| F1-1 | a | b |\n\n質問\n===\n\n| ID | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0,
     "条件 1 を満たす"),
    ("テストケースの節の外の ID の表は読まない", HEADER,
     {"order.md": "## 質問\n\n| ID | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0, "条件 1 を満たす"),
    ("次の見出しで節を引き継がない", HEADER,
     {"order.md": "## テストケース\n\n" + CASE_HEAD + "| F1-1 | a | b |\n\n## 質問\n\n| ID | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0,
     "条件 1 を満たす"),
    ("テストケースの節でも ID・No でない見出しの表は読まない", HEADER,
     {"order.md": "## テストケース\n\n| 質問 | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0, "条件 1 を満たす"),
    ("ID で始まるだけの見出しの表は読まない", HEADER,
     {"order.md": "## テストケース\n\n| ID番号 | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0, "条件 1 を満たす"),
    ("# の後に空白の無い行は見出しでない", HEADER,
     {"order.md": "#テストケース\n| ID | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0, "条件 1 を満たす"),
    ("4 字下げの # は見出しでない", HEADER,
     {"order.md": "    ## テストケース\n| ID | 内容 |\n| --- | --- |\n| Q-001 | a |\n| Q-001 | b |\n"}, 0, "条件 1 を満たす"),
    ("コードブロックの中の見出しは節を変えない", HEADER,
     {"order.md": "## テストケース\n\n```\n## 質問\n```\n\n| ID | 内容 |\n| --- | --- |\n| TC-001 | a |\n| TC-001 | b |\n"}, 1,
     "テストケースの番号 TC-001"),
    ("見出しは先頭のセルだけを見る", HEADER,
     {"order.md": "| No | テストケース内容 |\n| --- | --- |\n| F1-5b | a |\n", "flow.md": "| No | テストケース内容 |\n| --- | --- |\n| F1-5b | b |\n"}, 0,
     "条件 1 を満たす"),
    ("`TC-1` の形も番号（各表が振り直すと重複）", HEADER,
     {"order.md": CASE_HEAD + "| TC-1 | a |\n", "flow.md": CASE_HEAD + "| TC-1 | b |\n"}, 1, "テストケースの番号 TC-1"),
    ("フェンスは見出しの状態を消す", HEADER, {"order.md": CASE_TABLE + "```\nx\n```\n| F1-5b | 9 | 通る |\n"}, 0, "条件 1 を満たす"),
    ("3 字下げのフェンスも開く", HEADER, {"order.md": CASE_TABLE + "\n   ```\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n   ```\n"}, 0, "条件 1 を満たす"),
    ("長いフェンスで閉じる", HEADER, {"order.md": CASE_TABLE + "\n```\nx\n````\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n"}, 1, "order.md:13"),
    ("見出し行の先頭のセルは番号に数えない", HEADER,
     {"order.md": "| テストケース F1-5b | 入力 |\n| --- | --- |\n| F1-5a | 1 |\n", "flow.md": "| テストケース |\n| --- |\n| F1-5b |\n"}, 0,
     "条件 1 を満たす"),
    ("縦の表の見出し行が番号の形でも数えない", HEADER,
     {"order.md": CASE_TABLE, "flow.md": "| F1-5b | |\n| --- | --- |\n| 入力 | 1 |\n"}, 0, "条件 1 を満たす"),
    ("区切りの行が無い表は数えない", HEADER, {"order.md": "| テストケース | 入力 |\n| F1-5b | 1 |\n\n| テストケース | 入力 |\n| F1-5b | 2 |\n"}, 0, "条件 1 を満たす"),
    ("表が切れたら見出しを引き継がない", HEADER,
     {"order.md": CASE_TABLE + "\n| F1-5b | 1 |\n"}, 0, "条件 1 を満たす"),
    ("行頭が `|` でない行は数えない", HEADER, {"order.md": CASE_HEAD + "xF1-5b\nxF1-5b\n"}, 0, "条件 1 を満たす"),
    ("本文での言及は重複に数えない", HEADER, {"order.md": CASE_TABLE + "\nF1-5b を参照。F1-5b は拒否する。\n"}, 0, "条件 1 を満たす"),
    ("先頭のセル以外は数えない", HEADER, {"order.md": "| テストケース | TC |\n| --- | --- |\n| 1 | F1-5b |\n| 2 | F1-5b |\n"}, 0, "条件 1 を満たす"),
    ("表ごとに振り直す連番は数えない", HEADER, {"order.md": CASE_HEAD + "| 1 | a |\n| 2 | b |\n\n" + CASE_HEAD + "| 1 | c |\n| 2 | d |\n"}, 0,
     "条件 1 を満たす"),
    ("数字の無い名前は番号に数えない", HEADER, {"order.md": CASE_HEAD + "| Case-Id | a |\n\n" + CASE_HEAD + "| Case-Id | b |\n"}, 0, "条件 1 を満たす"),
    ("番号の後ろに字が続くセルは番号に数えない", HEADER, {"order.md": CASE_HEAD + "| F1-5b（境界） | a |\n| F1-5b（境界） | b |\n"}, 0, "条件 1 を満たす"),
    ("大文字小文字の違う番号は別の番号", HEADER, {"order.md": CASE_HEAD + "| F1-5b | a |\n| F1-5B | b |\n"}, 0, "条件 1 を満たす"),
    ("コードブロックの中は数えない", HEADER, {"order.md": CASE_TABLE + "\n```\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n```\n"}, 0, "条件 1 を満たす"),
    ("チルダのコードブロックの中も数えない", HEADER, {"order.md": CASE_TABLE + "\n~~~\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n~~~\n"}, 0, "条件 1 を満たす"),
    ("コードブロックの後ろは数える", HEADER, {"order.md": CASE_TABLE + "\n```\nx\n```\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n"}, 1, "order.md:13"),
    ("長いフェンスは短いフェンスで閉じない", HEADER, {"order.md": CASE_TABLE + "\n````\n```\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n````\n"}, 0, "条件 1 を満たす"),
    ("種類の違うフェンスでは閉じない", HEADER, {"order.md": CASE_TABLE + "\n```\n~~~\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n```\n"}, 0, "条件 1 を満たす"),
    ("情報文字列の付いたフェンスでは閉じない", HEADER, {"order.md": CASE_TABLE + "\n```\n```python\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n```\n"}, 0, "条件 1 を満たす"),
    ("字下げの深いフェンスは開かない", HEADER, {"order.md": CASE_TABLE + "\n    ```\n" + CASE_HEAD + "| F1-5b | 9 | 通る |\n"}, 1, "order.md:11"),
    (".md 以外のファイルは数えない", HEADER, {"order.md": CASE_TABLE, "rules.txt": CASE_HEAD + "| F1-5b | 9 | 通る |\n"}, 0, "条件 1 を満たす"),
    ("形式検査のモデルの番号は数えない", HEADER, {"order.md": CASE_TABLE, "formal/order/README.md": CASE_HEAD + "| F1-5b | 9 |\n"}, 0, "条件 1 を満たす"),
    ("内部の表の番号は数えない", HEADER + DONE_ROW,
     {"order.md": CASE_TABLE, "qa-dev.csv": HEADER + INTERNAL_DONE}, 0, "条件 1 を満たす"),
    # 呼ぶ側の分岐の行の揃い（#1340）
    ("呼ぶ側の分岐: 8 分岐に触れた見出しの行は通す", HEADER, {"order.md": CALLER_FULL}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 見出しの行の欠けを名指しする", HEADER, {"order.md": CALLER_HEAD + "\n".join(CALLER_ITEMS[:-1]) + "\n"}, 1,
     "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 1 分岐に触れていない（量が重なる）"),
    ("呼ぶ側の分岐: まとめて書く書き方は通す", HEADER, {"order.md": CALLER_HEAD + "\n".join(CALLER_GROUPED) + "\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 別の組の分岐の名前を並べてもよい", HEADER,
     {"order.md": CALLER_HEAD + "- 入力が欠ける・遅れる・順が崩れる・呼ぶ処理が失敗する・やり直される・再起動する・量が上限を超える・重なる: 該当なし（x）\n"}, 0,
     "条件 1 を満たす"),
    ("呼ぶ側の分岐: 組の名前だけの項目は触れない", HEADER,
     {"order.md": CALLER_HEAD + "\n".join(CALLER_GROUPED[:2]) + "\n- 量: 100 件まで\n"}, 1,
     "（量が上限を超える・量が重なる）——分岐ごとに見せるものか「該当なし」と理由を書く。読めない分岐の書き方（組の名前だけ・組に無い述語。どの分岐にも触れない）: 量"),
    ("呼ぶ側の分岐: 組に無い述語は触れない", HEADER,
     {"order.md": CALLER_HEAD + "\n".join(CALLER_GROUPED[1:]) + "\n- 入力が欠ける・壊れる: 該当なし\n"}, 1, "どの分岐にも触れない）: 入力が欠ける・壊れる"),
    ("呼ぶ側の分岐: 別の節を指す書き方は認めない", HEADER, {"order.md": CALLER_HEAD + "[価格照会書を出力する] と同じ\n"}, 1,
     "8 分岐のうち 8 分岐に触れていない（入力が欠ける・入力が遅れる・入力の順が崩れる・呼ぶ処理が失敗する・呼ぶ処理がやり直される・呼ぶ処理が再起動する・量が上限を超える・量が重なる）"
     "——分岐ごとに見せるものか「該当なし」と理由を書く。別の節を指す書き方（「…と同じ」）は認めない"),
    ("呼ぶ側の分岐: 項目の行の行ごと該当なしは通す", HEADER, {"order.md": "## 純粋な計算\n\n- 呼ぶ側の分岐: 該当なし（純粋な計算）\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 見出しの行の中身が該当なしで始まれば行ごと該当なし", HEADER, {"order.md": CALLER_HEAD + "該当なし（純粋な計算）\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 項目の行の欠けを名指しする", HEADER, {"order.md": "## 受注\n\n- 呼ぶ側の分岐:\n  " + CALLER_GROUPED[0] + "\n"}, 1,
     "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 5 分岐に触れていない（呼ぶ処理が失敗する・呼ぶ処理がやり直される・呼ぶ処理が再起動する・量が上限を超える・量が重なる）"),
    ("呼ぶ側の分岐: 項目の行は空行の後の分岐の項目も読む", HEADER,
     {"order.md": "## 受注\n\n- 呼ぶ側の分岐:\n\n  " + CALLER_GROUPED[0] + "\n\n  " + "\n  ".join(CALLER_GROUPED[1:]) + "\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 項目の行は空行の後の本文で終わる", HEADER,
     {"order.md": "## 受注\n\n- 呼ぶ側の分岐:\n  " + CALLER_GROUPED[0] + "\n\n本文の段落。\n\n" + "\n".join(CALLER_GROUPED[1:]) + "\n"}, 1,
     "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 5 分岐に触れていない"),
    ("呼ぶ側の分岐: 表の行の <br> で分けた項目を読む", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | " + "<br>".join(item[2:] for item in CALLER_GROUPED) + " |\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 表の行の欠けを名指しする", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | " + "<br>".join(item[2:] for item in CALLER_GROUPED[:2]) + " |\n"}, 1,
     "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 2 分岐に触れていない（量が上限を超える・量が重なる）"),
    ("呼ぶ側の分岐: 見出しの下の分岐の表を読む", HEADER,
     {"order.md": CALLER_HEAD + "| 分岐 | 見せるもの |\n| --- | --- |\n" + "".join(f"| {item[2:].split(': ')[0]} | {item[2:].split(': ')[1]} |\n" for item in CALLER_ITEMS)},
     0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 空の文の項目は触れない", HEADER, {"order.md": CALLER_HEAD + "\n".join(CALLER_ITEMS[:-1]) + "\n- 量が重なる:\n"}, 1,
     "1 分岐に触れていない（量が重なる）"),
    ("呼ぶ側の分岐: コードブロックの中の行は見ない", HEADER, {"order.md": "## 受注\n\n```\n### 呼ぶ側の分岐\n- 入力が欠ける: x\n```\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 全角のコロンと強調の飾りを外して読む", HEADER,
     {"order.md": "## 受注\n\n- **呼ぶ側の分岐**：\n" + "\n".join("  - **" + item[2:].replace(": ", "**：") for item in CALLER_ITEMS[:-1]) + "\n"}, 1,
     "1 分岐に触れていない（量が重なる）"),
    ("呼ぶ側の分岐: 行と読まない書き方は見ない（限界）", HEADER, {"order.md": "## 受注\n\n呼ぶ側の分岐は次のとおり。\n- 入力が欠ける: x\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 次の見出しで行を閉じる", HEADER,
     {"order.md": CALLER_HEAD + CALLER_GROUPED[0] + "\n\n### 測る値\n\n" + "\n".join(CALLER_GROUPED[1:]) + "\n"}, 1, "5 分岐に触れていない"),
    ("呼ぶ側の分岐: 次の行の始まりで中身を閉じる", HEADER,
     {"order.md": CALLER_FULL + "- 呼ぶ側の分岐:\n  " + CALLER_GROUPED[0] + "\n"}, 1, "order.md:13: 呼ぶ側の分岐の行が 8 分岐のうち 5 分岐"),
    ("呼ぶ側の分岐: 2 つの行をそれぞれ名指しする", HEADER,
     {"order.md": CALLER_HEAD + CALLER_GROUPED[0] + "\n\n## 出荷\n\n- 呼ぶ側の分岐:\n  " + CALLER_GROUPED[2] + "\n"}, 1, "order.md:9: 呼ぶ側の分岐の行が 8 分岐のうち 6 分岐"),
    # 1 パス目の指摘で足した試料（#1340）
    ("呼ぶ側の分岐: 中身の途中の該当なしは行ごと該当なしでない", HEADER, {"order.md": CALLER_HEAD + "- 入力が欠ける: a\n該当なし以外は書いていない\n"}, 1,
     "8 分岐のうち 7 分岐に触れていない"),
    ("呼ぶ側の分岐: 列見出しが呼ぶ側の分岐の表を読む", HEADER,
     {"order.md": "## 受注\n\n| 呼ぶ側の分岐 | 見せるもの |\n| --- | --- |\n" + "".join(f"| {item[2:].split(': ')[0]} | {item[2:].split(': ')[1]} |\n" for item in CALLER_ITEMS)},
     0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 列見出しの表の欠けを名指しする", HEADER,
     {"order.md": "## 受注\n\n| 呼ぶ側の分岐 | 見せるもの |\n| --- | --- |\n" + "".join(f"| {item[2:].split(': ')[0]} | {item[2:].split(': ')[1]} |\n" for item in CALLER_ITEMS[:-1])},
     1, "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 1 分岐に触れていない（量が重なる）"),
    ("呼ぶ側の分岐: 中身のコードブロックを挟んでも行を閉じない", HEADER,
     {"order.md": CALLER_HEAD + CALLER_ITEMS[0] + "\n\n```\n例\n```\n\n" + "\n".join(CALLER_ITEMS[1:]) + "\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 分岐の項目の文が別の節を指せば触れない", HEADER,
     {"order.md": CALLER_HEAD + "\n".join(item.split(": ")[0] + ": [価格照会書を出力する] と同じ" for item in CALLER_GROUPED) + "\n"}, 1,
     "8 分岐のうち 8 分岐に触れていない（入力が欠ける・入力が遅れる・入力の順が崩れる・呼ぶ処理が失敗する・呼ぶ処理がやり直される・呼ぶ処理が再起動する・量が上限を超える・量が重なる）"
     "——分岐ごとに見せるものか「該当なし」と理由を書く。別の節を指す書き方（「…と同じ」）は認めない"),
    ("呼ぶ側の分岐: 文の途中の「と同じ」は別の節を指す書き方でない", HEADER,
     {"order.md": CALLER_HEAD + "\n".join(CALLER_ITEMS[:-1]) + "\n- 量が重なる: 入力は画面と同じ形式で 1 件ずつ受ける\n"}, 0, "条件 1 を満たす"),
    # 2 パス目の指摘で足した試料（#1340）
    ("呼ぶ側の分岐: 最初でない該当なしの文は行ごと該当なしでない", HEADER,
     {"order.md": CALLER_HEAD + "見せるものは別途決める。\n該当なし（純粋な計算）\n"}, 1, "8 分岐のうち 8 分岐に触れていない"),
    ("呼ぶ側の分岐: 見出しの下の表の見出しの形の表はその行の中身", HEADER,
     {"order.md": CALLER_HEAD + "| 呼ぶ側の分岐 | 見せるもの |\n| --- | --- |\n" + "".join(f"| {item[2:].split(': ')[0]} | a |\n" for item in CALLER_GROUPED)}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 表の見出しの形の行ごと該当なし", HEADER, {"order.md": "| 呼ぶ側の分岐 | 見せるもの |\n| --- | --- |\n| 該当なし | 純粋な計算 |\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 該当なしで始まる文があっても分岐の項目を数える", HEADER,
     {"order.md": CALLER_HEAD + "該当なしの分岐には理由を書く。\n\n" + CALLER_ITEMS[0] + "\n"}, 1, "8 分岐のうち 7 分岐に触れていない"),
    ("呼ぶ側の分岐: 名指しの無い「と同じ」は触れる", HEADER,
     {"order.md": CALLER_HEAD + "\n".join(CALLER_ITEMS[:4]) + "\n- 呼ぶ処理がやり直される: 結果は 1 回目と同じ\n" + "\n".join(CALLER_ITEMS[5:]) + "\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 文の途中の名指しの「と同じ」も触れない", HEADER,
     {"order.md": CALLER_HEAD + "\n".join(CALLER_ITEMS[1:]) + "\n- 入力が欠ける: [価格照会書を出力する] と同じ（該当なし）\n"}, 1, "1 分岐に触れていない（入力が欠ける）"),
    ("呼ぶ側の分岐: チェックボックスの行と項目を読む", HEADER,
     {"order.md": "- [x] 呼ぶ側の分岐:\n" + "\n".join("  - [x] " + item[2:] for item in CALLER_ITEMS[:-1]) + "\n"}, 1, "order.md:1: 呼ぶ側の分岐の行が 8 分岐のうち 1 分岐に触れていない（量が重なる）"),
    ("呼ぶ側の分岐: 表の行のセルごとの項目を読む", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | " + " | ".join(item[2:] for item in CALLER_GROUPED) + " |\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: ほかの行を指す表の行は数えない", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 下の「呼ぶ側の分岐」の節 |\n\n" + CALLER_FULL}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: ほかに行が無ければ案内の表の行も名指す", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 下の「呼ぶ側の分岐」の節 |\n"}, 1, "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 8 分岐"),
    ("呼ぶ側の分岐: 節の番号の付いた見出しも読む", HEADER, {"order.md": "### 3.2 呼ぶ側の分岐\n\n" + CALLER_ITEMS[0] + "\n"}, 1, "order.md:1: 呼ぶ側の分岐の行が 8 分岐のうち 7 分岐"),
    # 狭いパスの指摘で足した試料（#1340）
    ("呼ぶ側の分岐: 鉤括弧の引用の後に文が続けば触れる", HEADER,
     {"order.md": CALLER_HEAD + "\n".join(CALLER_ITEMS[:-1]) + "\n- 量が重なる: 「エラー画面」と同じ画面を出す\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: リンクで名指した先と同じも触れない", HEADER,
     {"order.md": CALLER_HEAD + "\n".join(CALLER_ITEMS[:-1]) + "\n- 量が重なる: [出荷](ship.md) と同じ\n"}, 1, "1 分岐に触れていない（量が重なる）"),
    ("呼ぶ側の分岐: 書きかけの表の行はほかに行があっても名指す", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 後で書く |\n\n" + CALLER_FULL}, 1, "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 8 分岐"),
    # #1389: 「呼ぶ側の分岐」の語を含む書きかけの表の行を案内と読まない。案内は鉤括弧の名指しか「節」「参照」「下」の語を伴うものだけ
    ("呼ぶ側の分岐: 語を含む書きかけの表の行もほかに行があっても名指す", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 呼ぶ側の分岐は後で書く |\n\n" + CALLER_FULL}, 1, "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 8 分岐"),
    ("呼ぶ側の分岐: 下書きの表の行は案内でなく名指す", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 呼ぶ側の分岐は下書き |\n\n" + CALLER_FULL}, 1, "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 8 分岐"),
    ("呼ぶ側の分岐: 語の無い参照先の書きかけの表の行は名指す", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 参照先は後で決める |\n\n" + CALLER_FULL}, 1, "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 8 分岐"),
    ("呼ぶ側の分岐: 二重鉤括弧で名指す表の行は数えない", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 『呼ぶ側の分岐』のとおり |\n\n" + CALLER_FULL}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 節を伴って名指す表の行は数えない", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 呼ぶ側の分岐の節を見よ |\n\n" + CALLER_FULL}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 参照を伴って名指す表の行は数えない", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 呼ぶ側の分岐を参照 |\n\n" + CALLER_FULL}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 下を伴って名指す表の行は数えない", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 呼ぶ側の分岐は下に書く |\n\n" + CALLER_FULL}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: ほかに行が無ければ語を伴う案内の表の行も名指す", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 呼ぶ側の分岐を参照 |\n"}, 1, "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 8 分岐"),
    ("呼ぶ側の分岐: 欠けた表の行はほかに行があっても名指す", HEADER,
     {"order.md": CALLER_TABLE_HEAD + "| 呼ぶ側の分岐 | 入力が欠ける: a（ほかは下の「呼ぶ側の分岐」の節で後で） |\n\n" + CALLER_FULL}, 1, "order.md:3: 呼ぶ側の分岐の行が 8 分岐のうち 7 分岐"),
    ("呼ぶ側の分岐: .md 以外のファイルの行は見ない", HEADER, {"order.md": CLEAN_SPEC, "rules.txt": CALLER_HEAD + CALLER_GROUPED[0] + "\n"}, 0, "条件 1 を満たす"),
    ("呼ぶ側の分岐: 形式検査のモデルの行は見ない", HEADER, {"order.md": CLEAN_SPEC, "formal/order/README.md": CALLER_HEAD + CALLER_GROUPED[0] + "\n"}, 0,
     "条件 1 を満たす"),
    ("Q&A 表が無い", None, {"order.md": CLEAN_SPEC}, 2, "Q&A 表を読めない"),
    ("Q&A 表が UTF-8 でない", b"\xff\xfe\x00", {"order.md": CLEAN_SPEC}, 2, "Q&A 表を読めない"),
    # 想定外の例外（128KB 超のセルの csv.Error）も 2 で、トレースバックの 1 にしない（#286）
    ("巨大なセル", HEADER + OPEN_ROW.replace("端数は？", "x" * 200_000), {"order.md": CLEAN_SPEC}, 2,
     "想定外の例外で止まった（Error: field larger"),
]

CELL = 'unicodedata.normalize("NFKC", stripped[1:].split("|", 1)[0]).strip().strip("`*_ ")'  # 番号のセルを読む行（本体）

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("反映済みでない行を見ない", "for row in table_rows:", "for row in []:", "確認中の行"),
    ("内部の表を読まない", "if internal_path.exists()", "if False", "内部の表の確認中は止める"),
    ("内部の表を印の走査に入れる", "        if path == root / pptx.qa.INTERNAL_NAME:", "        if False:",
     "内部の表の反映済みは通す（文の印は数えない）"),
    ("どこの qa-dev.csv も外す", "        if path == root / pptx.qa.INTERNAL_NAME:", "        if path.name == pptx.qa.INTERNAL_NAME:",
     "入れ子の qa-dev.csv は仕様のファイル"),
    ("形式検査のモデルを印の走査に入れる", '        if versions.is_formal("spec/" + path.relative_to(root).as_posix()):', "        if False:",
     "形式検査のモデルの中の印は見ない"),
    ("接頭辞で形式検査のモデルを外す", '        if versions.is_formal("spec/" + path.relative_to(root).as_posix()):',
     '        if path.relative_to(root).parts[0].startswith("formal"):', "formal と接頭辞だけ同じファイルの印は見る"),
    # 最初の段の名前だけで外すと、`formal` という名前のファイル（ディレクトリでない）も外れる（#908 の 1 パス目の CR5）
    ("最初の段の名前で外す", '        if versions.is_formal("spec/" + path.relative_to(root).as_posix()):',
     '        if path.relative_to(root).parts[0] == "formal":', "formal という名前のファイルの印は見る"),
    ("内部の読めない表を 2 にしない", "    if internal_code == 2:", "    if False:", "内部の表が読めない"),
    ("暫定反映を反映した状態に数えない", "not in pptx.qa.REFLECTED", "!= pptx.qa.DONE", "暫定反映は止めない"),
    ("資料に載る行で数える", "not in pptx.qa.REFLECTED", "not in ()", "暫定反映は止めない"),
    ("暫定の件数を出さない", "if pptx.qa.is_provisional(row)]", "if False]", "暫定反映は止めない"),
    ("列検査の失敗を見ない", "        if table_code:\n            problems += table_lines", "        if False:\n            problems += table_lines",
     "列検査を通らない表"),
    ("読めない表を 2 にしない", "if code == 2:", "if False:", "Q&A 表が無い"),
    ("大文字・小文字を区別する", "re.compile(\"|\".join(parts), re.IGNORECASE)", "re.compile(\"|\".join(parts))",
     "小文字の todo"),
    ("英字の印を部分一致で当てる", "        if marker.isascii():", "        if False:", "満たす"),
    ("英字の印の前の境界を広げる", r'rf"(?<![A-Za-z0-9_]){re.escape(marker)}(?![A-Za-z0-9_])"',
     r'rf"\b{re.escape(marker)}(?![A-Za-z0-9_])"', "日本語に挟まれた TODO"),
    ("未定義を伏せない", "            line = line.replace(word, \"\\0\" * len(word))", "            pass", "満たす"),
    ("伏せたら行ごと飛ばす", "            line = line.replace(word, \"\\0\" * len(word))",
     "            line = \"\" if word in line else line", "未定義と未定が同じ行"),
    ("ディレクトリが無くても進む", "    if not spec_dir.is_dir():", "    if False:", "仕様のディレクトリが無い"),
    ("空の仕様を通す", "    if not files:", "    if False:", "仕様が空"),
    ("図だけでも通す", "    if len(unread) == len(files):", "    if False:", "図だけ"),
    ("空の仕様のファイルだけでも通す", "    if len(blank) == len(files) - len(unread):", "    if False:", "空のファイルだけ"),
    ("図を数えて空の仕様を通す", "    if len(blank) == len(files) - len(unread):", "    if len(blank) == len(files):",
     "空のファイルと図"),
    ("空のファイルが 1 つでもあれば止める", "    if len(blank) == len(files) - len(unread):", "    if blank:",
     "空のファイルと中身のある仕様"),
    ("空白だけを空に数えない", "        if not text.strip():", "        if not text:", "空白と改行だけのファイル"),
    ("空の判定を印より先に見る", "    if problems:\n        return 1",
     "    if problems and not blank:\n        return 1", "空のファイルと確認中の行"),
    ("図以外の読めないファイルも通す", "    if not_figures:", "    if False:", "読めない仕様と読める README"),
    ("NUL を含むファイルも読む", '        if "\\0" in text:', "        if False:", "BOM の無い ASCII の UTF-16"),
    ("全角を正規化しない", '        line = unicodedata.normalize("NFKC", line)\n', "", "全角の ＴＢＤ"),
    ("読めないファイルを印より先に見る", "    if problems:\n        return 1",
     "    if problems and not unread:\n        return 1", "読めない仕様と印のある仕様"),
    ("ドット始まりも見る", "        if any(part.startswith(\".\") for part in path.relative_to(root).parts):",
     "        if False:", "ドット始まりは見ない"),
    ("入れ子を見ない", 'root.rglob("*")', 'root.glob("*")', "入れ子のファイル"),
    ("行番号を 0 から数える", "enumerate(text.splitlines(), start=1)", "enumerate(text.splitlines())", "TBD"),
    ("TBD を印から外す", 'MARKERS = ("TBD", "TODO", "未定", "要確認")', 'MARKERS = ("TODO", "未定", "要確認")', "TBD"),
    ("満たしても但し書きを出さない", '        "**これだけでは抜けていない**——条件 2〜5 は判定していない（references/spec-exit.md）",\n',
     "", "満たす"),
    # テストケースの番号の重複（#1297）
    ("番号の行を 0 から数える", "enumerate(text.splitlines(), 1)", "enumerate(text.splitlines(), 0)", "同じファイルの重複"),
    ("番号の重複を数えない", "    problems += duplicate_numbers(numbers)\n", "    problems += []\n", "同じファイルの重複"),
    ("1 か所の番号も重複に数える", "        if len(where) < 2:", "        if len(where) < 1:", "番号の重複が無い表（陰性対照）"),
    ("ファイルごとに数える", "numbers.setdefault(case, []).append((path, number))", "numbers.setdefault(f\"{path}:{case}\", []).append((path, number))",
     "別のファイルの重複"),
    ("最初の場所だけ名指しする", '        spots = "、".join(f"{path}:{line}" for path, line in where)',
     '        spots = f"{where[0][0]}:{where[0][1]}"', "同じファイルの重複は後ろの場所も名指しする"),
    ("先頭のセルでなく最後のセルを見る", CELL,
     'unicodedata.normalize("NFKC", stripped.rstrip("|").rsplit("|", 1)[-1]).strip().strip("`*_ ")', "先頭のセル以外は数えない"),
    ("飾りを外さない", CELL, 'unicodedata.normalize("NFKC", stripped[1:].split("|", 1)[0]).strip()', "等幅の飾りを外して数える"),
    ("強調だけ外さない", '.strip().strip("`*_ ")', '.strip().strip("`_ ")', "強調の飾りを外して数える"),
    ("アンダースコアだけ外さない", '.strip().strip("`*_ ")', '.strip().strip("`* ")', "アンダースコアの飾りを外して数える"),
    ("全角を半角にそろえない", CELL, 'stripped[1:].split("|", 1)[0].strip().strip("`*_ ")', "全角の英数字とハイフンを半角にそろえて数える"),
    ("数字を要らない形にする", " and any(ch.isdigit() for ch in cell)", "", "数字の無い名前は番号に数えない"),
    ("セルの一部だけ番号に当たれば数える", "CASE_NUMBER_RE.fullmatch(cell)", "CASE_NUMBER_RE.match(cell)", "番号の後ろに字が続くセルは番号に数えない"),
    ("大文字小文字をそろえる", "found.append((number, cell, stripped))", "found.append((number, cell.lower(), stripped))", "大文字小文字の違う番号は別の番号"),
    ("コードブロックの中も数える", "        if fence is not None:\n", "        if False:\n", "コードブロックの中は数えない"),
    ("チルダのコードブロックを開かない", "FENCE = re.compile(r\"^ {0,3}(`{3,}|~{3,})\")", "FENCE = re.compile(r\"^ {0,3}(`{3,})\")",
     "チルダのコードブロックの中も数えない"),
    ("コードブロックを閉じない", "                fence = None\n            continue\n", "                pass\n            continue\n",
     "コードブロックの後ろは数える"),
    ("閉じのフェンスの長さを見ない", " and len(opened.group(1)) >= len(fence)", "", "長いフェンスは短いフェンスで閉じない"),
    ("閉じのフェンスの種類を見ない", "opened.group(1)[0] == fence[0] and ", "", "種類の違うフェンスでは閉じない"),
    ("閉じのフェンスの情報文字列を見ない", ' and not line.strip(" `~")', "", "情報文字列の付いたフェンスでは閉じない"),
    ("深い字下げのフェンスも開く", 'FENCE = re.compile(r"^ {0,3}', 'FENCE = re.compile(r"^ *', "字下げの深いフェンスは開かない"),
    (".md 以外も数える", '        if path.suffix == ".md":', "        if True:", ".md 以外のファイルは数えない"),
    ("形の外の識別子も番号に数える", 'CASE_NUMBER = r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+"', 'CASE_NUMBER = r"[A-Za-z0-9][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*"',
     "表ごとに振り直す連番は数えない"),
    ("見出しを見ずに全部の表を数える", "        if counting and CASE_NUMBER_RE", "        if CASE_NUMBER_RE", "Q&A の番号を引く表は数えない"),
    ("見出し行も数える", "is not None))\n            previous = None\n",
     "is not None))\n            previous = None\n"
     "            if counting:\n                found.append((number, \"F1-5b\"))\n", "見出し行の先頭のセルは番号に数えない"),
    ("区切りの行が無くても数える", "        if counting and CASE_NUMBER_RE", "        if (counting or (previous and CASE_HEADER.search(previous))) and CASE_NUMBER_RE",
     "区切りの行が無い表は数えない"),
    ("見出しの語を `テストケース` だけにする", r'CASE_HEADER = re.compile(r"\btest ?cases?\b|テストケース|\bcase ?(?:id|no\.?|number)\b|ケース(?:番号|ID|No)|テスト(?:番号|ID|No)|\btc\b", re.IGNORECASE)', 'CASE_HEADER = re.compile(r"テストケース")',
     "英語の見出しでも数える"),
    ("見出しの大文字小文字を区別する", r'CASE_HEADER = re.compile(r"\btest ?cases?\b|テストケース|\bcase ?(?:id|no\.?|number)\b|ケース(?:番号|ID|No)|テスト(?:番号|ID|No)|\btc\b", re.IGNORECASE)', r'CASE_HEADER = re.compile(r"\btest ?cases?\b|テストケース|\bcase ?(?:id|no\.?|number)\b|ケース(?:番号|ID|No)|テスト(?:番号|ID|No)|\btc\b")',
     "英語の見出しでも数える"),
    ("見出しの語を部分一致で広げる", r'CASE_HEADER = re.compile(r"\btest ?cases?\b|テストケース|\bcase ?(?:id|no\.?|number)\b|ケース(?:番号|ID|No)|テスト(?:番号|ID|No)|\btc\b", re.IGNORECASE)', 'CASE_HEADER = re.compile(r"ケース|テスト|case|test", re.IGNORECASE)',
     "ユースケースの表は数えない"),
    ("見出しを行全体で探す", "        previous = cell\n    return found", "        previous = stripped\n    return found", "見出しは先頭のセルだけを見る"),
    ("フェンスの字下げを 2 字までにする", 'FENCE = re.compile(r"^ {0,3}', 'FENCE = re.compile(r"^ {0,2}', "3 字下げのフェンスも開く"),
    ("閉じのフェンスを同じ長さだけにする", "len(opened.group(1)) >= len(fence)", "len(opened.group(1)) == len(fence)", "長いフェンスで閉じる"),
    # テストケースの節の ID・No・項番の表（#1333）
    ("節の ID の表を読まない", "\n                                                 or (section is not None and ID_HEADER.fullmatch(previous) is not None))",
     ")", "テストケースの節の ID の表は読む"),
    ("節を見ずに ID の表を読む", "(section is not None and ID_HEADER.fullmatch(previous) is not None)", "(ID_HEADER.fullmatch(previous) is not None)",
     "テストケースの節の外の ID の表は読まない"),
    ("次の見出しで節を変えない", "            if section is None or level <= section:", "            if section is None:", "次の見出しで節を引き継がない"),
    ("小見出しで節を抜ける", "            if section is None or level <= section:", "            if True:", "小見出しの下も節の中"),
    ("浅い見出しで節を抜けない", "            if section is None or level <= section:", "            if section is None or level == section:", "浅い見出しで節を抜ける"),
    ("節の見出しを部分一致で読む", '                section = level if SECTION_HEADER.search(title) else None', '                section = level if CASE_HEADER.search(title) else None',
     "テストケースの語で終わらない見出しは節でない"),
    ("節の見出しの一覧を許さない", r'(?:\s*一覧)?', '', "末尾が一覧の節の見出しも読む"),
    ("節の見出しの括弧書きを許さない", r'\s*(?:[(（][^()（）]*[)）])?$", re.IGNORECASE)', r'$", re.IGNORECASE)', "括弧書きの付いた節の見出しも読む"),
    ("ID の見出しを前方一致で読む", "ID_HEADER.fullmatch(previous)", 're.match(r"(?i)id|no|項番", previous)', "ID で始まるだけの見出しの表は読まない"),
    ("ID の見出しの大文字小文字を区別する", r'ID_HEADER = re.compile(r"^(?:id|no\.?|項番)$", re.IGNORECASE)', r'ID_HEADER = re.compile(r"^(?:ID|no\.?|項番)$")',
     "テストケースの節の小文字の id の表も読む"),
    ("No. を読まない", r'ID_HEADER = re.compile(r"^(?:id|no\.?|項番)$", re.IGNORECASE)', r'ID_HEADER = re.compile(r"^(?:id|no|項番)$", re.IGNORECASE)',
     "テストケースの節の No. の表も読む"),
    ("項番を読まない", r'ID_HEADER = re.compile(r"^(?:id|no\.?|項番)$", re.IGNORECASE)', r'ID_HEADER = re.compile(r"^(?:id|no\.?)$", re.IGNORECASE)',
     "テストケースの節の項番の表も読む"),
    ("# の後の空白を要らなくする", r'HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]|$)")', r'HEADING = re.compile(r"^ {0,3}(#{1,6})")',
     "# の後に空白の無い行は見出しでない"),
    ("深い字下げの # も見出しにする", r'HEADING = re.compile(r"^ {0,3}(#', r'HEADING = re.compile(r"^ *(#', "4 字下げの # は見出しでない"),
    ("節の見出しをそろえない", 'title = unicodedata.normalize("NFKC", line.strip().strip("#"))', 'title = (line.strip().strip("#"))',
     "全角の節の見出しもそろえて読む"),
    ("== の下線を見ない", r'UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)', r'UNDERLINE = re.compile(r"^ {0,3}(?:-+)', "== の下線の見出しでも節を閉じる"),
    # 段落の続き（#1379）。`prose` を戻す変異——区切りの線・箇条書きと引用・HTML の塊・4 字下げのコードを段落と読む
    ("表の行でなくても数える", '        if not stripped.startswith("|"):\n            previous, counting = None, False\n            if not stripped or in_html:',
     '        if False:\n            previous, counting = None, False\n            if not stripped or in_html:', "行頭が `|` でない行は数えない"),
    ("表が切れても見出しを引き継ぐ", "            previous, counting = None, False\n            if not stripped or in_html:", "            previous = None\n            if not stripped or in_html:",
     "表が切れたら見出しを引き継がない"),
    ("フェンスを開いても見出しの状態を残す", "            previous, counting, prose = None, False, False  # HTML の塊", "            previous, prose = None, False  # HTML の塊",
     "フェンスは見出しの状態を消す"),
    ("下線で節を閉じない", "        if underline:\n            section = None\n", "        if underline:\n            pass\n", "下線の見出しで節を閉じる"),
    ("空行の後の区切りの線でも節を閉じる", "            if prose and para_col != QUOTED and width >= para_col and UNDERLINE",
     "            if para_col != QUOTED and width >= para_col and UNDERLINE", "区切りの線では節を閉じない"),
    ("区切りの線を段落と読む", '    if THEMATIC.match(rest):\n        return "thematic"\n', '    if False:\n        return "thematic"\n', "本文の後に続く 2 本目の区切りの線では節を閉じない"),
    ("HTML の塊の中を段落と読む", "            if not stripped or in_html:\n                prose = False\n", "            if not stripped:\n                prose = False\n",
     "HTML コメントの閉じの行の後の区切りの線では節を閉じない"),
    ("箇条書きを見ない", "    item = LIST_ITEM.match(rest)\n    if item:\n", "    item = LIST_ITEM.match(rest)\n    if False:\n", "箇条書きの直後の区切りの線では節を閉じない"),
    ("引用を見ない", '    if QUOTE.match(rest):\n        return "quote"', '    if False:\n        return "quote"', "引用の直後の区切りの線では節を閉じない"),
    ("項の続きの行を段落の始まりと読む", "            elif lazy:\n                pass\n", "            elif lazy:\n                prose, para_col = True, base\n",
     "箇条書きの続きの行の後の区切りの線では節を閉じない"),
    ("引用の段落も下線を取る", "prose, para_col = quoted_paragraph(rest), QUOTED", "prose, para_col = quoted_paragraph(rest), 0", "引用の続きの行の後の区切りの線では節を閉じない"),
    ("4 字下げのコードを段落と読む", '        return None if prose else "code"', "        return None", "4 字下げのコードの直後の区切りの線では節を閉じない"),
    ("段落の中の 4 字下げもコードと読む", '        return None if prose else "code"', '        return "code"', "4 字下げの続きの行を持つ段落の下線で節を閉じる"),
    ("空の中身も段落の始まりと読む", "    return block_kind(content, False) is None", '    return block_kind(content, False) in (None, "blank")', "空の引用の行の後の段落の下線で節を閉じる"),
    ("空の項の中身を空でなくする", '        return marker + 1, True, ""\n', '        return marker + 1, True, "x"\n', "空の項の後の段落の下線で節を閉じる"),
    ("引用の中身を見ずに段落と読む", '    return starts_paragraph(content[1:] if content.startswith(" ") else content)', "    return bool(content.strip())",
     "見出しで始まる引用の後の段落の下線で節を閉じる"),
    ("項の中身を見ずに段落と読む", "                prose, para_col = starts_paragraph(content), column\n", "                prose, para_col = bool(content.strip()), column\n",
     "区切りの線で始まる項の後の段落の下線で節を閉じる"),
    ("項の中身の桁の下線を見ない", "UNDERLINE.match(line.expandtabs(4)[para_col:]):", "UNDERLINE.match(line.expandtabs(4)[para_col:]) and para_col == 0:",
     "項の中身の桁まで字下げした下線で節を閉じる"),
    ("中身の桁に届かない下線も項の下線にする", "and width >= para_col and UNDERLINE", "and UNDERLINE", "箇条書きの続きの行の後の区切りの線では節を閉じない"),
    ("中身の桁を印の幅と 1 桁にする", "    column = marker + (spaces if spaces <= 4 else 1)\n", "    column = marker + 1\n", "印の後ろの空白まで中身の桁に数える"),
    ("タブを 1 桁に数える", "            width += 4 - width % 4", "            width += 1", "タブで字下げした項の中の下線で節を閉じる"),
    ("空行で項を閉じる", "            if not stripped or in_html:\n                prose = False\n",
     "            if not stripped or in_html:\n                prose, items = False, (items if stripped else [])\n", "空行の後の項の中の字下げの段落の下線で節を閉じる"),
    ("深い入れ子の項の桁を見ない", "            base = max([0] + [column for column in items if column <= width])", "            base = 0",
     "3 段目の項の中身の桁に届かない下線では節を閉じない"),
    ("空の項の後の空行で項を閉じない", "        if not stripped and was_empty and items:\n            items.pop()", "        if not stripped and was_empty and items:\n            pass",
     "空の項の後の空行で項を閉じる（字下げの段落と線では閉じない）"),
    ("空の項の行の印を立てない", "                fresh_empty = empty\n", "                fresh_empty = False\n", "空の項の後の空行で項を閉じる（段落の下線で閉じる）"),
    ("同じ行の入れ子の項を積まない", '                while not empty and block_kind(content, False) == "item":', "                while False:",
     "同じ行で入れ子になった項の中身の桁の下線で節を閉じる"),
    ("同じ行の入れ子の項の桁を足さない", "                    column += inner\n", "", "同じ行で入れ子になった項の中身の桁に届かない線では節を閉じない"),
    ("空の項も段落を割り込む", "        if inside and (empty", "        if inside and (False", "空の項は段落を割り込まない"),
    ("1 でない番号の項も段落を割り込む", " or (item.group(2) is not None and int(item.group(2)) != 1)", "", "1 でない番号の行は段落を割り込まない"),
    ("段落の容れ物の外でも割り込めない形を段落の続きにする", "                inside = prose and base >= para_col and para_col != QUOTED\n",
     "                inside = prose\n", "項の外のタグだけの行は HTML の塊を始める"),
    ("空行で HTML の塊を閉じない", "((html[0] is None and not stripped) or", "((False) or", "HTML の塊の後に空行を挟んだ段落の下線で節を閉じる"),
    ("項の外の行で HTML の塊を閉じない", " or (stripped and indent_width(line) < html[1]))", ")", "項の外の行で項の中の HTML の塊を閉じる"),
    ("HTML で始まる項の中身を塊にしない", '                if block_kind(content, False) == "html":', "                if False:", "HTML で始まる項の中の本文と線では節を閉じない"),
    ("引用で始まる項の中身を引用にしない", '                if block_kind(content, False) == "quote":', "                if False:", "引用で始まる項の後の続きの行と線では節を閉じない"),
    ("*** を区切りの線と読まない", r'THEMATIC = re.compile(r"^ {0,3}([-*_])', r'THEMATIC = re.compile(r"^ {0,3}([-_])', "*** の直後の区切りの線では節を閉じない"),
    ("番号つきの項を見ない", r'LIST_ITEM = re.compile(r"^( {0,3}(?:[-+*]|(\d{1,9})[.)]))(?:[ \t]|$)")', r'LIST_ITEM = re.compile(r"^( {0,3}(?:[-+*]))(?:[ \t]|$)()")',
     "番号つきの項の直後の区切りの線では節を閉じない"),
    ("タグだけの行も段落を割り込む", "        if opening.match(line) and (interrupts or not prose):", "        if opening.match(line):", "タグだけの行は段落を割り込まない"),
    ("閉じの形で HTML の塊を閉じない", "            html = None  # 閉じの形の行までが塊", "            pass  # 閉じの形の行までが塊",
     "閉じた HTML コメントの後の段落の下線で節を閉じる"),
    ("pre を HTML の塊と読まない", r'(re.compile(r"^ {0,3}<(?:pre|script|style|textarea)', r'(re.compile(r"^ {0,3}<(?:never|script|style|textarea)',
     "空行を挟んだ pre の中の本文と線では節を閉じない"),
    ("HTML コメントを HTML の塊と読まない", r'(re.compile(r"^ {0,3}<!--")', r'(re.compile(r"^ {0,3}<!--never")', "HTML コメントの直後の区切りの線では節を閉じない"),
    ("処理命令を HTML の塊と読まない", r'(re.compile(r"^ {0,3}<\?")', r'(re.compile(r"^ {0,3}<\?never")', "処理命令の直後の区切りの線では節を閉じない"),
    ("宣言を HTML の塊と読まない", r'(re.compile(r"^ {0,3}<![A-Za-z]")', r'(re.compile(r"^ {0,3}<!never[A-Za-z]")', "宣言の直後の区切りの線では節を閉じない"),
    ("CDATA を HTML の塊と読まない", r'(re.compile(r"^ {0,3}<!\[CDATA\[")', r'(re.compile(r"^ {0,3}<!never\[CDATA\[")', "CDATA の直後の区切りの線では節を閉じない"),
    ("div を段落を割り込める塊と読まない", "dialog|dir|div|dl", "dialog|dir|dl", "段落を割り込んだ div の中の本文と線では節を閉じない"),
    ("タグだけの行を HTML の塊と読まない", r'(re.compile(r"^ {0,3}(?:<[A-Za-z]', r'(re.compile(r"^ {0,3}(?:<never[A-Za-z]', "タグだけの行の直後の区切りの線では節を閉じない"),
    ("節の見出しの飾りを外さない", '.strip(" `*_").rstrip(":：").strip(" `*_")', "", "飾りと末尾のコロンを外した節の見出しも読む"),
    ("節の見出しの閉じの # を外さない", 'title = unicodedata.normalize("NFKC", line.strip().strip("#"))', 'title = unicodedata.normalize("NFKC", line.strip()[len(heading.group(1)):])', "閉じの # を外した節の見出しも読む"),
    # 呼ぶ側の分岐の行の揃い（#1340）
    ("呼ぶ側の分岐の揃いを見ない", "            problems += caller_problems(path, text)\n", "            pass\n", "呼ぶ側の分岐: 見出しの行の欠けを名指しする"),
    ("見出しの形を行と読まない", '        return ("見出し", "") if _bare(title) == CALLER_LABEL else None', "        return None",
     "呼ぶ側の分岐: 見出しの行の欠けを名指しする"),
    ("表の形を行と読まない", '        return ("表", "|".join(cells[1:])) if _bare(cells[0]) == CALLER_LABEL else None', "        return None",
     "呼ぶ側の分岐: 表の行の欠けを名指しする"),
    ("項目の行の形を読まない", '    if rest.startswith(":"):\n        return "項目", rest[1:].strip()', '    if False:\n        return "項目", rest[1:].strip()',
     "呼ぶ側の分岐: 項目の行の欠けを名指しする"),
    ("組の名前だけを組の全部に読む", "        if current is None:\n            return set(), True\n",
     "        if current is None:\n            return {name for name in CALLER_BRANCHES if name.startswith(piece)}, False\n",
     "呼ぶ側の分岐: 組の名前だけの項目は触れない"),
    ("組に無い述語を飛ばして読む", "        if not names:\n            return set(), True\n", "        if not names:\n            continue\n",
     "呼ぶ側の分岐: 組に無い述語は触れない"),
    ("別の組の分岐の名前で組を変えない", "                current, piece = (group, preds), piece[len(group) + 1:]\n                break",
     "                if current is None:\n                    current, piece = (group, preds), piece[len(group) + 1:]\n                break",
     "呼ぶ側の分岐: 別の組の分岐の名前を並べてもよい"),
    ("別の節の添え書きを出さない", '            line += "。別の節を指す書き方（「…と同じ」）は認めない——この機能の分岐を書く"', "            pass",
     "呼ぶ側の分岐: 別の節を指す書き方は認めない"),
    ("読めない書き方を名指ししない", "            line += f\"。読めない分岐の書き方", "            line += f\"。分岐の書き方",
     "呼ぶ側の分岐: 組の名前だけの項目は触れない"),
    ("行ごと該当なしを読まない", "                if leading and plain.startswith(CALLER_NONE):\n                    whole_none = True",
     "                if leading and plain.startswith(CALLER_NONE):\n                    pass", "呼ぶ側の分岐: 項目の行の行ごと該当なしは通す"),
    ("中身の途中の該当なしでも行ごと該当なしにする", "                if leading and plain.startswith(CALLER_NONE):", "                if plain.startswith(CALLER_NONE):",
     "呼ぶ側の分岐: 最初でない該当なしの文は行ごと該当なしでない"),
    ("空の文も触れたと読む", "            elif text_of:\n", "            else:\n", "呼ぶ側の分岐: 空の文の項目は触れない"),
    ("分岐の項目の文の別の節を触れたと読む", "            elif REFERS.search(text_of):\n                refers = True", "            elif False:\n                refers = True",
     "呼ぶ側の分岐: 分岐の項目の文が別の節を指せば触れない"),
    ("列見出しの表を読まない", 'if kind == "表" and follow < len(lines) and SEPARATOR.fullmatch(lines[follow].strip()):',
     'if False:', "呼ぶ側の分岐: 列見出しが呼ぶ側の分岐の表を読む"),
    ("中身のコードブロックで行を閉じる", "                if fenced:\n                    inner = fenced.group(1)\n                    follow += 1\n                    continue\n",
     "                if fenced:\n                    break\n", "呼ぶ側の分岐: 中身のコードブロックを挟んでも行を閉じない"),
    ("空行で項目の行を必ず閉じる", "if ahead >= len(lines) or not _is_branch_item(lines[ahead]):", "if True:",
     "呼ぶ側の分岐: 項目の行は空行の後の分岐の項目も読む"),
    ("空行の後の本文も項目の行に入れる", "if ahead >= len(lines) or not _is_branch_item(lines[ahead]):", "if ahead >= len(lines):",
     "呼ぶ側の分岐: 項目の行は空行の後の本文で終わる"),
    ("次の見出しで行を閉じない", '                if HEADING.match(unicodedata.normalize("NFKC", nxt)):\n                    break',
     '                if HEADING.match(unicodedata.normalize("NFKC", nxt)):\n                    pass', "呼ぶ側の分岐: 次の見出しで行を閉じる"),
    ("次の行の始まりで中身を閉じない", "                if nested is not None:\n                    break", "                if nested is not None:\n                    pass",
     "呼ぶ側の分岐: 次の行の始まりで中身を閉じる"),
    ("表の <br> で分けない", "for piece in BREAK.split(entry))", "for piece in [entry])", "呼ぶ側の分岐: 表の行の <br> で分けた項目を読む"),
    ("見出しの下の表の見出しを別の行にする", "                    body, follow = _table_body(lines, follow + 2)\n                    content += body\n                    continue\n",
     "                    break\n", "呼ぶ側の分岐: 見出しの下の表の見出しの形の表はその行の中身"),
    ("表の見出し行のセルも中身に入れる", "            content, follow = _table_body(lines, follow + 1)", "            content, follow = _table_body(lines, follow)",
     "呼ぶ側の分岐: 表の見出しの形の行ごと該当なし"),
    ("分岐の項目があっても行ごと該当なしにする", "        whole_none = whole_none and not labelled\n", "",
     "呼ぶ側の分岐: 該当なしで始まる文があっても分岐の項目を数える"),
    ("名指しの無い「と同じ」も別の節と読む", "(?:\\]\\([^)]*\\)|[\\]」』])\\s*と同じ", "と同じ",
     "呼ぶ側の分岐: 名指しの無い「と同じ」は触れる"),
    ("後ろの括弧書きを許さない", "\\s*(?:[。.]|[（(][^）)]*[）)])?$", "$", "呼ぶ側の分岐: 文の途中の名指しの「と同じ」も触れない"),
    ("名指しの後に文が続いても別の節と読む", "\\s*(?:[。.]|[（(][^）)]*[）)])?$", "", "呼ぶ側の分岐: 鉤括弧の引用の後に文が続けば触れる"),
    ("リンクの名指しを読まない", "(?:\\]\\([^)]*\\)|[\\]」』])", "[\\]」』]", "呼ぶ側の分岐: リンクで名指した先と同じも触れない"),
    ("書きかけの表の行も案内と読む", " and CALLER_POINTER.search(own) is not None\n", "\n", "呼ぶ側の分岐: 書きかけの表の行はほかに行があっても名指す"),
    ("語を含む書きかけの表の行も案内と読む（#1389 の前の判定）", " and CALLER_POINTER.search(own) is not None\n", " and CALLER_LABEL in own\n",
     "呼ぶ側の分岐: 語を含む書きかけの表の行もほかに行があっても名指す"),
    ("鉤括弧の名指しを案内と読まない", "[「『]{CALLER_LABEL}[」』]|", "", "呼ぶ側の分岐: 二重鉤括弧で名指す表の行は数えない"),
    ("二重鉤括弧を案内の名指しと読まない", "[「『]{CALLER_LABEL}[」』]", "「{CALLER_LABEL}」", "呼ぶ側の分岐: 二重鉤括弧で名指す表の行は数えない"),
    ("節の語を案内と読まない", "(?:節|参照|", "(?:参照|", "呼ぶ側の分岐: 節を伴って名指す表の行は数えない"),
    ("参照の語を案内と読まない", "節|参照|下", "節|下", "呼ぶ側の分岐: 参照を伴って名指す表の行は数えない"),
    ("下の語を案内と読まない", "|下(?!書)))", ")))", "呼ぶ側の分岐: 下を伴って名指す表の行は数えない"),
    ("下書きの下も案内と読む", "下(?!書)", "下", "呼ぶ側の分岐: 下書きの表の行は案内でなく名指す"),
    ("語があれば呼ぶ側の分岐を名指さなくても案内と読む", "|(?=.*{CALLER_LABEL})(?=", "|(?=", "呼ぶ側の分岐: 語の無い参照先の書きかけの表の行は名指す"),
    ("分岐の項目のある表の行も案内と読む", "        pointer = kind == \"表\" and not labelled and ", "        pointer = kind == \"表\" and ",
     "呼ぶ側の分岐: 欠けた表の行はほかに行があっても名指す"),
    ("チェックボックスを外さない", "(?:\\[[ xX]\\]\\s+)?", "", "呼ぶ側の分岐: チェックボックスの行と項目を読む"),
    ("表の行をセルごとに分けない", '            content = [cell for cell in own.split("|") if cell.strip()]', "            content = [own]",
     "呼ぶ側の分岐: 表の行のセルごとの項目を読む"),
    ("案内の表の行も行に数える", "    if any(not row[4] for row in rows):\n", "    if False:\n", "呼ぶ側の分岐: ほかの行を指す表の行は数えない"),
    ("ほかに行が無くても案内の表の行を外す", "    if any(not row[4] for row in rows):\n", "    if True:\n", "呼ぶ側の分岐: ほかに行が無ければ案内の表の行も名指す"),
    ("見出しの節の番号を外さない", '        title = re.sub(r"^[0-9]+(?:\\.[0-9]+)*\\.?\\s+", "", _bare(title))', "        pass",
     "呼ぶ側の分岐: 節の番号の付いた見出しも読む"),
    ("呼ぶ側の分岐のコードブロックの中も読む",
     "        if fence:\n            if fence_closes(opened, fence, line):\n                fence = None\n            at += 1\n            continue\n        if opened:\n            fence = opened.group(1)\n            at += 1\n            continue\n",
     "", "呼ぶ側の分岐: コードブロックの中の行は見ない"),
    ("飾りを外さない", '    return text.strip().strip("*`_ ").strip()', "    return text.strip()", "呼ぶ側の分岐: 全角のコロンと強調の飾りを外して読む"),
    ("項目の全角のコロンを畳まない", '    text = unicodedata.normalize("NFKC", line).strip()\n    if text.startswith("|"):\n        if SEPARATOR',
     '    text = line.strip()\n    if text.startswith("|"):\n        if SEPARATOR', "呼ぶ側の分岐: 全角のコロンと強調の飾りを外して読む"),
    (".md 以外の行も見る", "                numbers.setdefault(case, []).append((path, number))\n            if callers:\n                problems += caller_problems(path, text)\n",
     "                numbers.setdefault(case, []).append((path, number))\n        if callers:\n            problems += caller_problems(path, text)\n", "呼ぶ側の分岐: .md 以外のファイルの行は見ない"),
    ("想定外の例外を 2 に寄せない", "    except Exception as e:  # 想定外の例外も「判定していない」（2）",
     "    except ImportError as e:  # 想定外の例外も「判定していない」（2）", "巨大なセル"),
]

# -OO（docstring が無い）で引数なしに呼んでも、使い方の誤りとして 2（#286）。(名前, 壊す前, 壊した後)
OO_MUTATIONS = [("-OO で docstring が無いと落ちる", "__doc__.splitlines()[2] if __doc__ else", "__doc__.splitlines()[2] if True else")]


def oo_problems(scripts: Path, cwd: Path) -> list[str]:
    proc = subprocess.run([sys.executable, "-I", "-OO", str(scripts / TARGET)], capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 2 or "usage:" not in proc.stderr or "Traceback" in proc.stderr:
        return [f"-OO の引数なし: 終了 {proc.returncode}: {proc.stderr[-300:]!r}"]
    return []

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def build_case(root: Path, qa: str | bytes | None, spec: dict[str, str | bytes] | None) -> tuple[Path, Path]:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    qa_path = root / "qa.csv"
    if isinstance(qa, bytes):
        qa_path.write_bytes(qa)
    elif qa is not None:
        qa_path.write_text(qa, encoding="utf-8")
    spec_dir = root / "spec"
    if spec is not None:
        spec_dir.mkdir()
        for rel, body in spec.items():
            path = spec_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(body, bytes):
                path.write_bytes(body)
            else:
                path.write_text(body, encoding="utf-8")
    return qa_path, spec_dir


def run_all(scripts: Path, work: Path, only: str | None = None) -> dict[str, tuple[int, str]]:
    """試料を全部回し、名前 → (終了コード, 出力)。
    `only` を渡せば、その名前の試料**だけ**を回す（変異の回。#494）——判定に使うのはその試料の結果だけで、他の試料は試料ごとに別の場所で
    別のプロセスとして回るので結果に効かない。場所の名前（`case<番号>`）は全部を回す形と同じ。
    """
    results = {}
    for index, (name, qa, spec, _, _) in enumerate(CASES):
        if only is not None and name != only:
            continue
        qa_path, spec_dir = build_case(work / f"case{index}", qa, spec)
        proc = subprocess.run(
            [sys.executable, "-I", str(scripts / TARGET), str(qa_path), str(spec_dir)],
            capture_output=True, text=True, cwd=work,
        )
        results[name] = (proc.returncode, proc.stdout + proc.stderr)
    return results


def as_expected(name: str, result: tuple[int, str]) -> bool:
    expected = next(case for case in CASES if case[0] == name)
    return result[0] == expected[3] and expected[4] in result[1] and "Traceback" not in result[1]


def reference_markers(markdown: str) -> tuple[list[str], list[str]]:
    """「未決定の印」の節の表のセルと、「印に当たらない」と書いた語を返す。"""
    section = markdown.split("## 未決定の印", 1)[1].split("\n## ", 1)[0]
    markers = re.findall(r"^\| `([^`]+)` \|$", section, flags=re.MULTILINE)
    not_markers = re.findall(r"\*\*`([^`]+)` は印に当たらない\*\*", section)
    return markers, not_markers


# 判別の本体（`check-qa-csv.py` の `is_provisional`）を壊す——条件 1 は写しを持たずにそれを読む（#404）
CHECKER = "check-qa-csv.py"
CHECKER_MUTATIONS: list[tuple[str, str, str, str]] = [
    ("判別の本体で暫定を見ない", 'return row["状態"].strip() == PROVISIONAL', "return False", "暫定反映は止めない"),
    ("判別の本体を文言の一致に戻す", 'return row["状態"].strip() == PROVISIONAL',
     'return row["状態"].strip() == PROVISIONAL or (row["状態"].strip() == DONE and "暫定で採用" in row["回答"])',
     "文言だけ暫定の反映済みは暫定に数えない"),
]


def reference_case_number(markdown: str) -> str | None:
    """「テストケースの番号の重複」の節の「番号の形」（`CASE_NUMBER`）の正規表現。"""
    section = markdown.split("### テストケースの番号の重複", 1)[1].split("\n## ", 1)[0].split("\n### ", 1)[0] \
        if "### テストケースの番号の重複" in markdown else ""
    found = re.search(r"\*\*番号の形\*\*（`CASE_NUMBER`）: `([^`]+)`", section)
    return found.group(1) if found else None


def reference_caller_groups(markdown: str) -> list[tuple[str, str]]:
    """「呼ぶ側の分岐の行の形」の組と分岐の表の行（組, 分岐を `・` で並べた文）。"""
    if "#### 呼ぶ側の分岐の行の形" not in markdown:
        return []
    section = markdown.split("#### 呼ぶ側の分岐の行の形", 1)[1].split("\n### ", 1)[0]
    table = section.split("| 組 | 分岐（組の名前に続ける形） |", 1)[1] if "| 組 | 分岐（組の名前に続ける形） |" in section else ""
    return re.findall(r"^ *\| ([^|`]+?) \| ([^|`]+?) \|$", table.split("\n\n", 1)[0], flags=re.MULTILINE)[1:]


def reference_branch_names(markdown: str) -> list[str]:
    """spec-ir.md の「分岐の名前」の表のセル。"""
    section = markdown.split("### 分岐の名前", 1)[1].split("\n## ", 1)[0] if "### 分岐の名前" in markdown else ""
    return re.findall(r"^\| `([^`]+)` \|$", section, flags=re.MULTILINE)


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("check_spec_exit_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def merged_cases(scripts: Path, work: Path) -> list[tuple[str, int, str, int, str]]:
    """(名前, 実際の終了コード, 出力, 期待する終了コード, 出力に含まれるべき文字列)。版（`docs/v<n>/`）を `merge-versions.py` で重ねた全体に当てる。
    後の版が同じファイルを置き換えたら重複でない。別のファイルに同じ番号を置けば前の版の行が残るので重複（#1297）。"""
    table_v2 = CASE_TABLE.replace("| 2 | 拒否 |", "| 3 | 拒否 |")
    samples = [
        ("後の版が同じファイルを置き換えた（番号は同じ）", {"v1/spec/order.md": CASE_TABLE, "v2/spec/order.md": table_v2}, 0, "条件 1 を満たす"),
        ("後の版が別のファイルに同じ番号を置いた", {"v1/spec/order.md": CASE_TABLE, "v2/spec/flow.md": CASE_HEAD + "| F1-5b | 9 | 通る |\n"}, 1,
         "テストケースの番号 F1-5b が 2 か所で重複"),
        ("後の版が同じファイルを置き換え、前の版の番号を別のファイルへ移した",
         {"v1/spec/order.md": CASE_TABLE, "v2/spec/order.md": "# 注文\n\n" + CASE_HEAD + "| F9-1 | 1 |\n", "v2/spec/flow.md": CASE_HEAD + "| F1-5b | 9 | 通る |\n"},
         0, "条件 1 を満たす"),
    ]
    results = []
    for index, (name, files, code, needle) in enumerate(samples):
        docs = work / f"merge{index}" / "docs"
        assert_in_tmp(docs)
        for version in ("v1", "v2"):
            (docs / version / "shared").mkdir(parents=True)
            (docs / version / "shared" / "qa.csv").write_text(HEADER, encoding="utf-8")
        for rel, body in files.items():
            path = docs / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        out = docs.parent / "out"
        merge = subprocess.run([sys.executable, "-I", str(scripts / "merge-versions.py"), str(docs), str(out)],
                               capture_output=True, text=True, cwd=work)
        if merge.returncode != 0:
            results.append((name, merge.returncode, merge.stdout + merge.stderr, code, needle))
            continue
        proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), str(out / "shared" / "qa.csv"), str(out / "spec")],
                              capture_output=True, text=True, cwd=work)
        results.append((name, proc.returncode, proc.stdout + proc.stderr, code, needle))
    return results


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="spec-exit-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        results = run_all(scripts, tmp_path / "work")
        for name, result in results.items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result[0]} {result[1][-300:]}")

        # references との突き合わせ
        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        markers, not_markers = reference_markers(reference)
        code_markers = re.search(r"^MARKERS = (\(.*\))$", source, flags=re.MULTILINE)
        code_not = re.search(r"^NOT_MARKERS = (\(.*\))$", source, flags=re.MULTILINE)
        check("本体に MARKERS が見つからない", code_markers is not None)
        check("本体に NOT_MARKERS が見つからない", code_not is not None)
        if code_markers and code_not:
            check("MARKERS が references/spec-exit.md の表と違う",
                  list(ast.literal_eval(code_markers.group(1))) == markers, f"{code_markers.group(1)} vs {markers}")
            check("NOT_MARKERS が references/spec-exit.md と違う",
                  list(ast.literal_eval(code_not.group(1))) == not_markers, f"{code_not.group(1)} vs {not_markers}")
        check("references から印を 1 つも読めない（読み方が壊れている）", len(markers) >= 2, str(markers))

        # 番号の形（#1297）
        code_number = re.search(r'^CASE_NUMBER = r"(.*)"$', source, flags=re.MULTILINE)
        ref_number = reference_case_number(reference)
        code_header = re.search(r'^CASE_HEADER = re.compile\(r"(.*)", re.IGNORECASE\)$', source, flags=re.MULTILINE)
        check("本体に CASE_HEADER が見つからない", code_header is not None)
        if code_header:
            check("CASE_HEADER が references/spec-exit.md と違う", f"`{code_header.group(1)}`" in reference, code_header.group(1))
        code_id = re.search(r'^ID_HEADER = re.compile\(r"(.*)", re.IGNORECASE\)$', source, flags=re.MULTILINE)
        check("本体に ID_HEADER が見つからない", code_id is not None)
        if code_id:
            check("ID_HEADER が references/spec-exit.md と違う", f"`ID_HEADER`: `{code_id.group(1)}`" in reference, code_id.group(1))
        code_section = re.search(r'^SECTION_HEADER = re.compile\(r"(.*)", re.IGNORECASE\)$', source, flags=re.MULTILINE)
        check("本体に SECTION_HEADER が見つからない", code_section is not None)
        if code_section:
            check("SECTION_HEADER が references/spec-exit.md と違う", f"`SECTION_HEADER`。大文字小文字を区別しない）に当たる見出しから" in reference
                  and f": `{code_section.group(1)}`（" in reference, code_section.group(1))
        check("本体に CASE_NUMBER が見つからない", code_number is not None)
        check("references/spec-exit.md の「テストケースの番号の重複」に番号の形が見つからない", ref_number is not None)
        if code_number and ref_number:
            check("CASE_NUMBER が references/spec-exit.md と違う", code_number.group(1) == ref_number, f"{code_number.group(1)} vs {ref_number}")
        broken_number = reference.replace("`[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+`", "`[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+`")
        check("番号の形の写しを崩しても不一致にならない", reference_case_number(broken_number) != ref_number)

        # 呼ぶ側の分岐の行の形（#1340）——組と分岐の表は spec-exit.md、分岐の名前の表は spec-ir.md が原本
        spec_ir = (PLUGIN / "references" / "spec-ir.md").read_text(encoding="utf-8")
        module = load_module(SCRIPTS / TARGET)
        groups = reference_caller_groups(reference)
        code_groups = [(group, "・".join(f"{particle}{predicate}" for particle, predicate in preds)) for group, preds in module.CALLER_GROUPS]
        check("CALLER_GROUPS が references/spec-exit.md の「呼ぶ側の分岐の行の形」の組と分岐の表と違う", code_groups == groups, f"{code_groups} vs {groups}")
        check("references から組と分岐を読めない（読み方が壊れている）", len(groups) == 3, str(groups))
        ir_names = reference_branch_names(spec_ir)
        check("CALLER_BRANCHES が references/spec-ir.md の分岐の名前の表と違う", list(module.CALLER_BRANCHES) == ir_names and len(ir_names) == 8,
              f"{module.CALLER_BRANCHES} vs {ir_names}")
        check("組と分岐の写しを崩しても不一致にならない",
              reference_caller_groups(reference.replace("| 量 | が上限を超える・が重なる |", "| 量 | が上限を超える |")) != groups)
        check("CALLER_LABEL が references/spec-exit.md の行の形の見出しと違う", f"`### {module.CALLER_LABEL}`" in reference, module.CALLER_LABEL)

        # check(callers=False) は揃いを見ない（scaffold.py の前の版の時点の --upto。#1340 の 1 パス目の指摘）
        gap_dir = tmp_path / "callers-off"
        (gap_dir / "spec").mkdir(parents=True)
        (gap_dir / "qa.csv").write_text(HEADER, encoding="utf-8")
        (gap_dir / "spec" / "order.md").write_text(CALLER_HEAD + CALLER_GROUPED[0] + "\n", encoding="utf-8")
        on_code, _ = module.check(gap_dir / "qa.csv", gap_dir / "spec")
        off_code, _ = module.check(gap_dir / "qa.csv", gap_dir / "spec", callers=False)
        check("check(callers=False) が呼ぶ側の分岐の揃いを見ている／既定で見ていない", on_code == 1 and off_code == 0, f"{on_code} {off_code}")

        # 版を重ねた全体（#1297）
        for name, got, output, want, needle in merged_cases(scripts, tmp_path / "mergework"):
            check(f"重ねた全体の試料が期待どおりでない: {name}", got == want and needle in output and "Traceback" not in output,
                  f"exit={got} {output[-300:]}")

        # 突き合わせ自体の陽性対照: 写しを崩すと不一致になる
        broken = reference.replace("| `要確認` |", "| `要検討` |")
        check("references の写しを崩しても不一致にならない", reference_markers(broken)[0] != markers)

        # 変異テスト
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            mutated_results = run_all(mutated, tmp_path / f"mutwork{index}", only=killer)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）",
                  not as_expected(killer, mutated_results[killer]), mutated_results[killer][1][-300:])

        checker = (SCRIPTS / CHECKER).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(CHECKER_MUTATIONS):
            count = checker.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"checker-mut{index}")
            (mutated / CHECKER).write_text(checker.replace(before, after), encoding="utf-8")
            mutated_results = run_all(mutated, tmp_path / f"checker-mutwork{index}", only=killer)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）",
                  not as_expected(killer, mutated_results[killer]), mutated_results[killer][1][-300:])

        problems = oo_problems(scripts, tmp_path)
        check("-OO の引数なしで使い方の誤り（2）にならない", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(OO_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"oo-mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}", bool(oo_problems(mutated, tmp_path)))

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(CHECKER_MUTATIONS) + len(OO_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
