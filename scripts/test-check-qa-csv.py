#!/usr/bin/env python3
"""`check-qa-csv.py` の回帰テスト。

    python3 scripts/test-check-qa-csv.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`scripts/` ではない——
**spec-loop は正本リポジトリ（このリポジトリとは別）で使うプラグイン**なので、
スキルが自分の base ディレクトリから呼べる場所に置く（`test-find-cycle.py` と同じ形）。

見るもの:

1. **決まりに反する `qa.csv` を、反した理由つきで落とす**（1 種類ずつ）。
2. **決まりどおりの `qa.csv` を通す**（陽性対照。検査が厳しすぎて記事の例すら落とすのを防ぐ）。
3. **本体の定数が `references/qa-csv.md` の表と一致する**——決まりの正は `references/` で、
   本体の定数はその写しである。**写しがずれたらここで落ちる。** `references/qa-csv.md` の
   「例」のブロックも本体に通す（決まりの文書が、自分の例で決まりを破っていないか）。
4. **リポジトリの外で単体で動く**——本体だけを一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに全部の試料が期待どおりなら失格**とする。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、
穴が無くても緑になるので）。
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPT = PLUGIN / "scripts" / "check-qa-csv.py"
REFERENCE = PLUGIN / "references" / "qa-csv.md"
# 移す手順を指す側（本体の `MIGRATION` と MkDocs のフックの `QA_MIGRATION`）と、指される側（#345）
HOOK = PLUGIN / "templates" / "mkdocs" / "hooks" / "spec_loop_pages.py"
REFERENCES = PLUGIN / "references"

HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
# 前の形（spec-loop 0.17.0 まで）の見出し——推奨の 2 列が無い
OLD_HEADER = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
GOOD_ROWS = (
    "Q-001,要求確定（決定表）,割引は A・B のどちらにしますか？,A: 割引なし / B: 3% 割引,A,差をはっきりさせる,A（業務部が回答）,決定表 4 行目,反映済み,\n"
    "Q-002,仕様レビュー（Red Team）,通信が切れたら？,A: 取り消す / B: 残す,B,問い合わせを減らす,未回答,—,確認中,\n"
    "Q-005,実現性・コスト,夜間は止めてよいか,A: 止まってよい / B: 24 時間,A,月額が半分,未回答,—,確認中,B は月額が約 2 倍\n"
    "Q-010,開発,上限を超えたら？,A: 拒否 / B: 切り詰める / C: 警告だけ,C,止めずに気づける,B（開発が仮置き）,—,確認中,\n"
    "Q-011,要求確定,上限は？,A: なし / B: 5000 円,なし,見積り待ち,A（暫定で採用。業務部 2026-10-21 の指示）,決定表 7 行目,暫定反映,\n"
)
# 記事（要求仕様書作成ループ）の Q&A 表の 6 行。記事の表は 2 つに分かれており、
# Q-005・Q-006 の表には `回答`・`反映先`・`状態` の列が無いので `未回答`・`—`・`確認中` で埋めた。
# Q-001 の `10,000` は区切りのコンマを含むので引用符で囲んだ。記事に推奨は無いので `推奨` は `なし`（理由に「記事に推奨が無い」）。
# それ以外は記事の文のまま。
ARTICLE_ROWS = (
    'Q-001,要求確定（決定表）,"シルバー会員で 10,000 円未満のとき、割引は A・B のどちらにしますか？",'
    "A: 割引なし（0%） / B: 3% 割引,なし,記事に推奨が無い,A（業務部が回答）,決定表 4 行目,反映済み,\n"
    "Q-002,仕様レビュー（Red Team）,決済の途中で通信が切れたとき、注文は A・B のどちらで扱いますか？,"
    "A: 取り消す / B: 「決済待ち」で残し、後で再開できる,なし,記事に推奨が無い,未回答,—,確認中,\n"
    "Q-003,仕様レビュー（Domain Checker）,割引後の金額に 1 円未満の端数が出たら、A・B のどちらで丸めますか？,"
    "A: 切り捨て / B: 四捨五入,なし,記事に推奨が無い,未回答,—,確認中,\n"
    "Q-004,仕様レビュー（形式検査・Z3 の反例）,クーポンを使うと「注文額の 60% 以上」の下限を割るとき、A・B のどちらにしますか？,"
    "A: 下限の金額で止める / B: この条件ではクーポンを使えなくする,なし,記事に推奨が無い,未回答,—,確認中,\n"
    "Q-005,実現性・コスト（運用費の見積り）,夜間（0〜6 時）のシステム停止について、A・B のどちらにしますか？,"
    "A: 夜間は止まってよい / B: 24 時間稼働させる,なし,記事に推奨が無い,未回答,—,確認中,"
    "B は冗長構成が要り、月額が A の約 2 倍、開発は 2 週間増える（仮の値）\n"
    "Q-006,実現性・コスト（運用費の見積り）,注文データを検索できる期間は、A・B のどちらにしますか？,"
    "A: 直近 1 年（それ以前はアーカイブ） / B: 全期間,なし,記事に推奨が無い,未回答,—,確認中,B は保管と検索の費用が年ごとに増える（仮の値）\n"
)


def row(**over: str) -> str:
    """決まりどおりの 1 行を作り、指定した列だけ差し替える。"""
    base = {
        "No": "Q-001", "起票元": "要求確定", "質問": "どちらにしますか？",
        "選択肢": "A: する / B: しない", "推奨": "A", "推奨の理由": "手間が少ない", "回答": "未回答", "反映先": "—",
        "状態": "確認中", "費用への影響": "",
    }
    base.update(over)
    return ",".join(base.values()) + "\n"


# (名前, 中身（str は UTF-8 で書く。bytes はそのまま）, 期待する終了コード, 出力に含まれるべき文字列)
CASES: list[tuple[str, str | bytes, int, str]] = [
    # --- 陽性対照 ---
    ("決まりどおり", HEADER + GOOD_ROWS, 0, "OK（5 行）"),
    ("記事の Q-001〜Q-006", HEADER + ARTICLE_ROWS, 0, "OK（6 行）"),
    ("番号が 4 桁", HEADER + row(No="Q-1000"), 0, "OK（1 行）"),
    ("BOM 付き（Excel）", ("﻿" + HEADER + GOOD_ROWS), 0, "OK（5 行）"),
    ("空行は飛ばす", HEADER + GOOD_ROWS + "\n,,,,,,,,,\n", 0, "OK（5 行）"),
    ("セルの中の改行（引用符つき）",
     HEADER + 'Q-001,要求確定,"1 行目\n2 行目",A: x / B: y,A,理由,未回答,—,確認中,\n', 0, "OK（1 行）"),
    ("セルの中の U+2028（Web から貼った文）", HEADER + row(質問="1 文目 2 文目"), 0, "OK（1 行）"),
    ("費用への影響は空でよい", HEADER + row(), 0, "OK（1 行）"),
    ("費用付きの質問に費用への影響", HEADER + row(起票元="実現性・コスト（運用費）", 費用への影響="B は月額が約 2 倍"), 0,
     "OK（1 行）"),
    # --- 読めない（中身を検査していない） ---
    ("空のファイル", "", 2, "空のファイル"),
    ("UTF-8 でない", HEADER.encode("cp932"), 2, "UTF-8 として読めない"),
    # --- 見出し ---
    ("列が欠けている", HEADER.replace(",費用への影響", "") + row(), 1, "見出し行が決まりと違う"),
    ("列の順序が違う", HEADER.replace("回答,反映先", "反映先,回答") + row(), 1, "見出し行が決まりと違う"),
    ("余分な列", HEADER.replace("\n", ",備考\n") + row(), 1, "見出し行が決まりと違う"),
    ("前の形の見出し（推奨の列が無い）", OLD_HEADER + "Q-001,要求確定,質問,A: x / B: y,未回答,—,確認中,\n", 1,
     "移す手順は references/tree.md の「Q&A 表を移す」"),
    # --- 推奨 ---
    ("推奨しない（なし と理由）", HEADER + row(推奨="なし", 推奨の理由="事実の確認"), 0, "OK（1 行）"),
    ("推奨が 3 つ目の選択肢", HEADER + row(選択肢="A: x / B: y / C: z", 推奨="C"), 0, "OK（1 行）"),
    ("推奨が空", HEADER + row(推奨=""), 1, "`推奨` が空（推奨しないなら `なし`）"),
    ("推奨の理由が空", HEADER + row(推奨の理由=""), 1, "`推奨の理由` が空"),
    ("なしでも理由が空", HEADER + row(推奨="なし", 推奨の理由=" "), 1, "`推奨の理由` が空"),
    ("推奨が選択肢に無いラベル", HEADER + row(推奨="C"), 1, "`推奨` が選択肢のラベルでも `なし` でもない"),
    ("推奨が選択肢の文", HEADER + row(推奨="する"), 1, "`推奨` が選択肢のラベルでも `なし` でもない"),
    ("推奨が小文字のラベル", HEADER + row(推奨="a"), 1, "`推奨` が選択肢のラベルでも `なし` でもない"),
    ("推奨に空白が付く", HEADER + row(推奨="A "), 1, "`推奨` が選択肢のラベルでも `なし` でもない"),
    # --- 内部の層（ファイルの名前が qa-dev.csv） ---
    ("内部: 決まりどおり", HEADER + row(No="D-001", 回答="B（開発 山田 2026-10-22）", 反映先="spec/jobs.md", 状態="反映済み")
     + row(No="D-002"), 0, "OK（2 行）"),
    ("内部: 番号が Q-", HEADER + row(No="Q-001"), 1, "`No` が `D-001` の形でない"),
    ("内部: 暫定反映", HEADER + row(No="D-001", 回答="A（暫定）", 反映先="spec/a.md", 状態="暫定反映"), 1,
     "内部の表で `暫定反映` は使わない"),
    ("内部: 推奨の決まりも同じ", HEADER + row(No="D-001", 推奨=""), 1, "`推奨` が空"),
    ("共有: 番号が D-", HEADER + row(No="D-001"), 1, "`No` が `Q-001` の形でない"),
    # --- 行 ---
    ("行の列数が違う", HEADER + "Q-001,要求確定,質問,A: x / B: y,A,理由,未回答,—,確認中\n", 1, "列の数が 9"),
    ("番号の書式", HEADER + row(No="Q-1"), 1, "`No` が `Q-001` の形でない"),
    ("番号が 2 桁", HEADER + row(No="Q-01"), 1, "`No` が `Q-001` の形でない"),
    ("番号が全角数字", HEADER + row(No="Q-００１"), 1, "`No` が `Q-001` の形でない"),
    ("番号の後ろに余計な文字", HEADER + row(No="Q-001x"), 1, "`No` が `Q-001` の形でない"),
    ("番号の重複", HEADER + row() + row(), 1, ":3: `No` が 2 行目と重複"),
    ("未知の起票元", HEADER + row(起票元="営業"), 1, "`起票元` が決まりに無い"),
    ("未知の起票元（括弧つき）", HEADER + row(起票元="営業（電話）"), 1, "`起票元` が決まりに無い"),
    ("起票元の括弧が半角", HEADER + row(起票元="要求確定(決定表)"), 1, "`起票元` が決まりに無い"),
    ("起票元の括弧が閉じていない", HEADER + row(起票元="要求確定（決定表"), 1, "`起票元` が決まりに無い"),
    ("起票元の括弧が空", HEADER + row(起票元="要求確定（）"), 1, "`起票元` が決まりに無い"),
    ("費用付きの質問で費用への影響が空", HEADER + row(起票元="実現性・コスト"), 1,
     "起票元が `実現性・コスト` なのに `費用への影響` が空"),
    ("費用付きの質問（括弧つき）で費用への影響が空白だけ", HEADER + row(起票元="実現性・コスト（運用費）", 費用への影響=" "), 1,
     "起票元が `実現性・コスト` なのに `費用への影響` が空"),
    ("選択肢が足りない", HEADER + row(選択肢="A: する"), 1, "選択肢が 2 つ未満"),
    ("選択肢の形", HEADER + row(選択肢="する / しない"), 1, "`A: …` の形でない"),
    ("選択肢のラベルが小文字", HEADER + row(選択肢="a: する / b: しない"), 1, "`A: …` の形でない"),
    ("選択肢のラベルが 2 字", HEADER + row(選択肢="AB: する / B: しない"), 1, "`A: …` の形でない"),
    ("選択肢のコロンの後に空白が無い", HEADER + row(選択肢="A:する / B: しない"), 1, "`A: …` の形でない"),
    ("選択肢の文が空", HEADER + row(選択肢="A:  / B: しない"), 1, "`A: …` の形でない"),
    ("選択肢のラベル重複", HEADER + row(選択肢="A: する / A: しない"), 1, "ラベルが重複"),
    ("未知の状態", HEADER + row(状態="回答済み"), 1, "`状態` が決まりに無い"),
    ("反映済みなのに未回答", HEADER + row(状態="反映済み", 反映先="決定表 1 行目"), 1, "`反映済み` なのに `回答` が無い"),
    ("反映済みなのに未回答（後ろに空白）", HEADER + row(状態="反映済み", 回答="未回答 ", 反映先="決定表 1 行目"), 1,
     "`反映済み` なのに `回答` が無い"),
    ("反映済みなのに反映先が無い", HEADER + row(状態="反映済み", 回答="A"), 1, "`反映済み` なのに `反映先` が無い"),
    ("反映済みなのに反映先が無い（前に空白）", HEADER + row(状態="反映済み", 回答="A", 反映先=" —"), 1,
     "`反映済み` なのに `反映先` が無い"),
    ("暫定反映なのに未回答", HEADER + row(状態="暫定反映", 反映先="決定表 1 行目"), 1, "`暫定反映` なのに `回答` が無い"),
    ("暫定反映なのに反映先が無い", HEADER + row(状態="暫定反映", 回答="A（推奨案を暫定で採用）"), 1,
     "`暫定反映` なのに `反映先` が無い"),
    ("回答が空", HEADER + row(回答=""), 1, "`回答` が空（まだなら `未回答`）"),
    ("反映先が空", HEADER + row(反映先=""), 1, "`反映先` が空（まだなら `—`）"),
    ("質問が空", HEADER + row(質問=""), 1, "`質問` が空"),
    # 1 行に 2 つ反していて、後のほうも出る（`No` の検査が先に走る）
    ("全部を出す（最初の 1 件で止めない）", HEADER + row(No="X", 状態="?"), 1, "`状態` が決まりに無い"),
]

# 本体を 1 箇所ずつ壊す。(名前, 壊す前, 壊した後, それを殺すはずの試料)
# **殺すはずの試料が期待どおりでなくなること**まで見る——別の試料で偶然落ちたのを
# 「殺せた」と数えないため。
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("見出しを見ない", "if header != COLUMNS:", "if False:", "列の順序が違う"),
    ("状態を見ない", 'row["状態"] not in STATES', "False", "未知の状態"),
    ("反映済みの回答を見ない", 'if row["回答"].strip() in ("", NO_ANSWER):', "if False:", "反映済みなのに未回答"),
    ("反映済みの反映先を見ない", 'if row["反映先"].strip() in ("", NO_TARGET):', "if False:", "反映済みなのに反映先が無い"),
    ("選択肢の数を見ない", "if len(options) < MIN_OPTIONS:", "if False:", "選択肢が足りない"),
    ("選択肢を 1 つから許す", "MIN_OPTIONS = 2", "MIN_OPTIONS = 1", "選択肢が足りない"),
    ("選択肢の形を見ない", r'OPTION = re.compile(rf"(?P<label>{OPTION_LABEL}): \S.*")',
     r'OPTION = re.compile(r"(?P<label>.?).*")', "選択肢の形"),
    ("ラベルに小文字を許す", 'OPTION_LABEL = "[A-Z]"', 'OPTION_LABEL = "[A-Za-z]"', "選択肢のラベルが小文字"),
    ("ラベルに 2 字を許す", 'OPTION_LABEL = "[A-Z]"', 'OPTION_LABEL = "[A-Z]+"', "選択肢のラベルが 2 字"),
    ("コロンの後の空白を見ない", r'}): \S.*")', r'}):\s*\S.*")', "選択肢のコロンの後に空白が無い"),
    ("選択肢の文の空を許す", r'}): \S.*")', r'}): .*")', "選択肢の文が空"),
    ("起票元の括弧を半角でも許す",
     'SOURCE = re.compile(rf"(?P<name>[^{DETAIL_OPEN}]+)(?:{DETAIL_OPEN}.+{DETAIL_CLOSE})?")',
     'SOURCE = re.compile(r"(?P<name>[^（(]+)(?:[（(].+[）)])?")', "起票元の括弧が半角"),
    ("起票元を前方一致で見る", 'SOURCE.fullmatch(row["起票元"])', 'SOURCE.match(row["起票元"])', "起票元の括弧が閉じていない"),
    ("起票元の空の括弧を許す", "{DETAIL_OPEN}.+{DETAIL_CLOSE}", "{DETAIL_OPEN}.*{DETAIL_CLOSE}", "起票元の括弧が空"),
    ("ラベルの重複を見ない", "if len(set(labels)) != len(labels):", "if False:", "選択肢のラベル重複"),
    ("番号の書式を見ない", 'not number.fullmatch(row["No"])', "False", "番号の書式"),
    ("番号を 2 桁から許す", r'NUMBER = re.compile(r"Q-[0-9]{3,}")', r'NUMBER = re.compile(r"Q-[0-9]{2,}")', "番号が 2 桁"),
    ("番号を 3 桁までにする", r'NUMBER = re.compile(r"Q-[0-9]{3,}")', r'NUMBER = re.compile(r"Q-[0-9]{3}")', "番号が 4 桁"),
    ("番号を Unicode の数字で見る", r'NUMBER = re.compile(r"Q-[0-9]{3,}")', r'NUMBER = re.compile(r"Q-\d{3,}")',
     "番号が全角数字"),
    ("番号を前方一致で見る", 'not number.fullmatch(row["No"])', 'not number.match(row["No"])', "番号の後ろに余計な文字"),
    ("反映済みの回答の空白を落とさない", 'if row["回答"].strip() in ("", NO_ANSWER):',
     'if row["回答"] in ("", NO_ANSWER):', "反映済みなのに未回答（後ろに空白）"),
    ("反映済みの反映先の空白を落とさない", 'if row["反映先"].strip() in ("", NO_TARGET):',
     'if row["反映先"] in ("", NO_TARGET):', "反映済みなのに反映先が無い（前に空白）"),
    ("暫定反映の回答を見ない", "REFLECTED = (DONE, PROVISIONAL)", "REFLECTED = (DONE,)", "暫定反映なのに未回答"),
    ("番号の重複を見ない", 'if row["No"] in seen:', "if False:", "番号の重複"),
    ("推奨のラベルを見ない",
     'elif row["推奨"].strip() and row["推奨"] != NO_RECOMMENDATION and row["推奨"] not in labels:', "elif False:",
     "推奨が選択肢に無いラベル"),
    ("推奨を空白を落として比べる", 'and row["推奨"] not in labels:', 'and row["推奨"].strip() not in labels:', "推奨に空白が付く"),
    ("なしを許さない", 'and row["推奨"] != NO_RECOMMENDATION', "", "推奨しない（なし と理由）"),
    ("内部の層を見ない", "return path.name == INTERNAL_NAME", "return False", "内部: 番号が Q-"),
    ("内部の番号を Q- にする", r'INTERNAL_NUMBER = re.compile(r"D-[0-9]{3,}")', r'INTERNAL_NUMBER = re.compile(r"Q-[0-9]{3,}")',
     "内部: 決まりどおり"),
    ("内部で暫定反映を許す", "elif internal and row[\"状態\"] in INTERNAL_FORBIDDEN:", "elif False:", "内部: 暫定反映"),
    ("前の形の見出しで手順を指さない", 'if "推奨" not in header:', "if False:", "前の形の見出し（推奨の列が無い）"),
    ("起票元を見ない", 'm["name"] not in SOURCES', "False", "未知の起票元"),
    ("空のセルを見ない", "if column not in MAY_BE_EMPTY and not row[column].strip():", "if False:", "質問が空"),
    ("列の数を見ない", "if len(fields) != len(COLUMNS):", "if False:", "行の列数が違う"),
    ("BOM を剥がさない", 'encoding="utf-8-sig"', 'encoding="utf-8"', "BOM 付き（Excel）"),
    ("空のファイルを 2 にしない", "if not text.strip():", "if False:", "空のファイル"),
    ("UTF-8 でないのを 2 にしない", 'return 2, [f"{path}: UTF-8', 'return 1, [f"{path}: UTF-8', "UTF-8 でない"),
    ("費用への影響の空を許さない", 'MAY_BE_EMPTY = {"費用への影響"}', "MAY_BE_EMPTY = set()", "費用への影響は空でよい"),
    ("費用付きの質問の空を見ない", 'elif m["name"] == COST_SOURCE and not row["費用への影響"].strip():', "elif False:",
     "費用付きの質問で費用への影響が空"),
    ("費用付きの質問の空白を落とさない", 'and not row["費用への影響"].strip():', 'and not row["費用への影響"]:',
     "費用付きの質問（括弧つき）で費用への影響が空白だけ"),
    ("費用付きの質問を起票元の詳細ごと比べる", 'elif m["name"] == COST_SOURCE', 'elif row["起票元"] == COST_SOURCE',
     "費用付きの質問（括弧つき）で費用への影響が空白だけ"),
    # 引用符つきの改行は `splitlines()` でも壊れない（csv が繋ぎ直す）ので、殺すのは U+2028 の試料
    ("splitlines で割る", 'csv.reader(io.StringIO(text, newline=""))', "csv.reader(text.splitlines())",
     "セルの中の U+2028（Web から貼った文）"),
    ("最初の 1 件で止める", "for problem in check_row(row, internal):", "for problem in check_row(row, internal)[:1]:",
     "全部を出す（最初の 1 件で止めない）"),
]

# 番号 → 内部の層か（`is_internal_number`。層を番号で決めるのはここだけ——#353）
NUMBER_LAYERS = [("D-001", True), ("D-1234", True), ("Q-001", False), ("D-01", False), ("D-001x", False),
                 ("d-001", False), ("", False)]
NUMBER_MUTATIONS = [
    ("番号の層を見ない（常に共有）", "return INTERNAL_NUMBER.fullmatch(number) is not None", "return False"),
    ("番号の層を入れ替える", "return INTERNAL_NUMBER.fullmatch(number) is not None",
     "return INTERNAL_NUMBER.fullmatch(number) is None"),
    ("番号の先頭だけ見る", "return INTERNAL_NUMBER.fullmatch(number) is not None", "return INTERNAL_NUMBER.match(number) is not None"),
]

# 行 → 暫定の行か（`is_provisional`。暫定を決めるのはここだけで、`状態` だけを見る——#404）。
# `回答` の書き方は答えを変えない: #403 の否定の書き方も、#366 の実データの形（`反映済み`＋「暫定で採用」）も確定の行
PROVISIONAL_ROWS = [
    ("暫定反映", "A（暫定で採用。業務部 2026-10-21 の指示）", True),
    ("暫定反映", "A（業務部 2026-10-21 の指示）", True),
    (" 暫定反映 ", "A", True),
    ("反映済み", "A（推奨案を暫定で採用。開発側の指示）", False),
    ("反映済み", "A を暫定で採用します（業務部の確認待ち）", False),
    ("反映済み", "A（暫定で採用していない）", False),
    ("反映済み", "A（暫定で採用されなかった B は取り下げ）", False),
    ("反映済み", "A（暫定で採用しなければ間に合わない）", False),
    ("反映済み", "A（業務部が回答）", False),
    ("確認中", "B（暫定で採用の予定）", False),
    ("確認中", "未回答", False),
]
PROVISIONAL_MUTATIONS = [
    ("暫定を見ない", 'return row["状態"].strip() == PROVISIONAL', "return False"),
    ("反映済みも暫定にする", 'return row["状態"].strip() == PROVISIONAL',
     'return row["状態"].strip() in (PROVISIONAL, DONE)'),
    ("文言の一致に戻す", 'return row["状態"].strip() == PROVISIONAL',
     'return row["状態"].strip() == PROVISIONAL or (row["状態"].strip() == DONE and "暫定で採用" in row["回答"])'),
    ("状態の空白を落とさない", 'return row["状態"].strip() == PROVISIONAL', 'return row["状態"] == PROVISIONAL'),
]

# 暫定の判別を読む側（#404）。どれも `is_provisional` を呼び、`暫定反映` を自分で比べない——
# 判別を状態だけにしたので、写しに戻しても挙動は同じ（変異が挙動では殺せない）。だから構造で見る
READERS = {"build-proposal.py": "qa.is_provisional(", "qa-to-pptx.py": "qa.is_provisional(",
           "check-spec-exit.py": "pptx.qa.is_provisional(", "scaffold.py": "qa.is_provisional(",
           "check-signoff.py": "qa.is_provisional("}
# `PROVISIONAL` と状態を比べる形（`==`・`!=`・`in`）と、状態の名前の文字列
COMPARES = re.compile(r"""(?:[=!]=|\bin\b)[^\n#]*\bPROVISIONAL\b|\bPROVISIONAL\b\s*[=!]=|["']暫定反映["']""")
HOOK_JUDGE = '    return row["状態"].strip() == QA_PROVISIONAL\n'
READER_MUTATIONS = [
    ("scaffold を写しに戻す", "scaffold.py", "if qa.is_provisional(row)]",
     'if row["状態"].strip() == qa.PROVISIONAL]'),
    ("照合を写しに戻す", "check-signoff.py", "if qa.is_provisional(row)]",
     'if row["状態"].strip() == qa.PROVISIONAL]'),
    ("条件 1 を写しに戻す", "check-spec-exit.py", "if pptx.qa.is_provisional(row)]",
     'if row["状態"].strip() == pptx.qa.PROVISIONAL]'),
    ("資料を写しに戻す（文字列で）", "qa-to-pptx.py", 'mark = "（暫定）" if qa.is_provisional(row) else ""',
     'mark = "（暫定）" if row["状態"].strip() == "暫定反映" else ""'),
    ("提案書を写しに戻す（in で）", "build-proposal.py", "provisional = [r for r in qa_rows if qa.is_provisional(r)]",
     'provisional = [r for r in qa_rows if r["状態"].strip() in (qa.PROVISIONAL,)]'),
    ("フックを写しの外で比べる", HOOK.name, "provisional = sum(qa_is_provisional(row) for row in rows)",
     'provisional = sum(row["状態"] == QA_PROVISIONAL for row in rows)'),
]


def provisional_mismatches(mod) -> list[str]:
    return [f"{state!r}・{answer!r} → {mod.is_provisional({'状態': state, '回答': answer})}（期待: {want}）"
            for state, answer, want in PROVISIONAL_ROWS if mod.is_provisional({"状態": state, "回答": answer}) != want]


def reader_sources() -> dict[str, str]:
    sources = {p.name: p.read_text(encoding="utf-8") for p in sorted((PLUGIN / "scripts").glob("*.py"))}
    sources[HOOK.name] = HOOK.read_text(encoding="utf-8")
    return sources


def reader_problems(sources: dict[str, str]) -> list[str]:
    problems = [f"{name}: {call} を呼んでいない" for name, call in READERS.items() if call not in sources.get(name, "")]
    for name, text in sources.items():
        if name == SCRIPT.name:
            continue
        if name == HOOK.name:
            # フックは写しを 1 つだけ持つ（`qa_is_provisional`）。比べてよいのはその本体の 1 行だけ
            if HOOK_JUDGE not in text:
                problems.append(f"{name}: qa_is_provisional の本体（状態だけで決める 1 行）が無い")
            rest = text.replace(HOOK_JUDGE, "", 1)
            if re.search(r"(?:[=!]=|\bin\b)[^\n#]*\bQA_PROVISIONAL\b|\bQA_PROVISIONAL\b\s*[=!]=", rest):
                problems.append(f"{name}: qa_is_provisional の外で暫定を比べている")
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if COMPARES.search(line):
                problems.append(f"{name}:{number}: 暫定を is_provisional を通さずに比べている: {line.strip()}")
    return problems


# `references/tree.md の「X」`（バッククォートで囲んだ形も）。X は指した先の見出し
POINTER = re.compile(r"references/(?P<file>[\w.-]+\.md)`? の「(?P<heading>[^」]+)」")
HEADING = re.compile(r"#{1,6} (?P<text>.+)")
# 指される側を崩す——見出しを改名すると、指す側が古くなったことを検査が言う（陽性対照は崩す前に緑であること）
POINTER_MUTATIONS = [("tree.md の見出しを改名する", "tree.md", "\n## Q&A 表を移す\n", "\n## Q&A 表の移し方\n")]

failures: list[str] = []


def number_layer_mismatches(mod) -> list[str]:
    return [f"{number!r} → {mod.is_internal_number(number)}（期待: {want}）"
            for number, want in NUMBER_LAYERS if mod.is_internal_number(number) != want]


HOOK_CONSTANT = re.compile(r'^QA_MIGRATION = "(?P<value>[^"]*)"$', re.M)


def pointer_sources(mod, hook: str | None = None) -> dict[str, str]:
    """指す側の文字列。本体は定数、フックは定数とソース全体（docstring も見る）。

    フックの定数は単独でも数える——ソース全体だけだと、docstring の指し先が当たる限り、
    定数が別のファイルを指していても緑になる。
    """
    hook = HOOK.read_text(encoding="utf-8") if hook is None else hook
    constant = HOOK_CONSTANT.search(hook)
    return {"check-qa-csv.py の MIGRATION": mod.MIGRATION,
            f"{HOOK.name} の QA_MIGRATION": constant["value"] if constant else "",
            HOOK.name: hook}


# 定数が指すべき先——実在する別の見出し（`references/qa-csv.md の「層」` など）を指しても、移す手順ではない
MIGRATION_TARGET = ("tree.md", "Q&A 表を移す")


def pointer_mismatches(sources: dict[str, str], references: dict[str, str]) -> list[str]:
    problems = []
    for where, text in sources.items():
        found = list(POINTER.finditer(text))
        if not found:
            problems.append(f"{where}: 移す手順への指し先が無い")
        if where != HOOK.name and found and (found[0]["file"], found[0]["heading"]) != MIGRATION_TARGET:
            problems.append(f"{where}: 移す手順（references/{MIGRATION_TARGET[0]} の「{MIGRATION_TARGET[1]}」）を指していない")
        for m in found:
            markdown = references.get(m["file"])
            if markdown is None:
                problems.append(f"{where}: references/{m['file']} が無い")
                continue
            # 「層 — 共有の表と内部の表」は「層」で指す（` — ` の前が見出しの名前）
            headings = {name for line in markdown.splitlines() if (h := HEADING.fullmatch(line))
                        for name in (h["text"].strip(), h["text"].split(" — ", 1)[0].strip())}
            if m["heading"] not in headings:
                problems.append(f"{where}: references/{m['file']} に見出し「{m['heading']}」が無い")
    return problems


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{(' — ' + detail) if detail else ''}")
        failures.append(name)


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), f"試料がテンポラリの外: {resolved}"
    assert not resolved.is_relative_to(REAL_REPO), "試料が実リポジトリの内側にある"


def load(script: Path):
    spec = importlib.util.spec_from_file_location(f"qa_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_case(root: Path, index: int, content: str | bytes, internal: bool = False) -> Path:
    # 内部の層の試料は、層を決めるファイルの名前（qa-dev.csv）で書く
    path = root / f"case-{index}" / "qa-dev.csv" if internal else root / f"case-{index}.csv"
    assert_in_tmp(path)
    path.parent.mkdir(exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def run_case(mod, path: Path) -> tuple[int, str]:
    """本体の `check` を呼ぶ。**例外は「期待どおりでない」として扱う**（変異で壊れる形の 1 つ）。"""
    try:
        code, lines = mod.check(path)
    except Exception as e:  # noqa: BLE001 — 変異の結果を観測するため
        return -1, f"{type(e).__name__}: {e}"
    return code, "\n".join(lines)


def matches(result: tuple[int, str], expected_code: int, expected_text: str) -> bool:
    code, out = result
    return code == expected_code and expected_text in out


def table_keys(markdown: str, heading: str) -> list[str]:
    """`## <heading>` の直後の表から、1 列目のバッククォートの中身を順に返す。"""
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", markdown, re.S | re.M)
    if not m:
        return []
    keys = []
    for line in m.group(1).splitlines():
        cell = re.match(r"\|\s*`([^`]+)`\s*\|", line)
        if cell:
            keys.append(cell.group(1))
    return keys


def column_cells(markdown: str) -> dict[str, list[str]]:
    """「列」の表を {列名: [書くもの, 空のとき]} で返す。"""
    m = re.search(r"^## 列\n(.*?)(?=^## |\Z)", markdown, re.S | re.M)
    cells: dict[str, list[str]] = {}
    for line in (m.group(1).splitlines() if m else []):
        parts = [p.strip() for p in line.strip().strip("|").split(" | ")]
        key = re.fullmatch(r"`([^`]+)`", parts[0]) if parts else None
        if key and len(parts) == 3:
            cells[key.group(1)] = parts[1:]
    return cells


def first_code(text: str, pattern: str) -> str | None:
    """`pattern` の `{}` の位置にあるバッククォートの中身を返す（空白はそのまま）。"""
    m = re.search(pattern.replace("{}", "`([^`]+)`"), text)
    return m.group(1) if m else None


def reference_mismatches(mod, markdown: str) -> list[str]:
    problems = []
    for heading, constant in (("列", mod.COLUMNS), ("起票元", mod.SOURCES), ("状態", mod.STATES)):
        keys = table_keys(markdown, heading)
        if keys != list(constant):
            problems.append(f"「{heading}」の表 {keys} ≠ 本体 {list(constant)}")

    # 反映した状態と、暫定の状態（「状態」の表の下と「暫定の回答」の節）
    reflected = re.search(r"仕様に反映した状態は `([^`]+)` と `([^`]+)` の 2 つ", markdown)
    if set(reflected.groups() if reflected else ()) != set(mod.REFLECTED):
        problems.append(f"反映した状態 {reflected and reflected.groups()!r} ≠ 本体 {mod.REFLECTED!r}")
    provisional = first_code(markdown, "`状態` は {}。")
    if provisional != mod.PROVISIONAL:
        problems.append(f"暫定の状態 {provisional!r} ≠ 本体 {mod.PROVISIONAL!r}")

    # 暫定の行の判別（「暫定の行の判別」。状態だけで決める——#404）
    judged = first_code(markdown, "`状態` が {} の行だけを、暫定の行として扱う")
    if judged != mod.PROVISIONAL:
        problems.append(f"暫定の行の判別の状態 {judged!r} ≠ 本体 {mod.PROVISIONAL!r}")

    # 「列」の表のセルに書いた決まりと、本体の写し
    cells = column_cells(markdown)
    write, empty = (lambda c: cells.get(c, ["", ""])[0]), (lambda c: cells.get(c, ["", ""])[1])
    may_be_empty = {c for c in cells if "空でよい" in empty(c)}
    if may_be_empty != set(mod.MAY_BE_EMPTY):
        problems.append(f"空でよい列 {sorted(may_be_empty)} ≠ 本体 {sorted(mod.MAY_BE_EMPTY)}")
    cost_source = first_code(empty("費用への影響"), "起票元が {} の行は空を許さない")
    if cost_source != mod.COST_SOURCE:
        problems.append(f"費用付きの質問の起票元 {cost_source!r} ≠ 本体 {mod.COST_SOURCE!r}")
    for column, constant in (("回答", mod.NO_ANSWER), ("反映先", mod.NO_TARGET)):
        marker = first_code(empty(column), "まだなら {}")
        if marker != constant:
            problems.append(f"`{column}` の「まだ無い」の印 {marker!r} ≠ 本体 {constant!r}")
    digits = re.search(r"`Q-` に (\d+) 桁以上", write("No"))
    expected = rf"Q-[0-9]{{{digits.group(1)},}}" if digits else None
    if expected != mod.NUMBER.pattern:
        problems.append(f"番号の書式 {expected!r} ≠ 本体 {mod.NUMBER.pattern!r}")
    internal_prefix = first_code(write("No"), "内部の表は {}（")
    internal_expected = expected.replace("Q-", internal_prefix, 1) if expected and internal_prefix else None
    if internal_expected != mod.INTERNAL_NUMBER.pattern:
        problems.append(f"内部の番号の書式 {internal_expected!r} ≠ 本体 {mod.INTERNAL_NUMBER.pattern!r}")
    none_marker = first_code(write("推奨"), "推奨しないなら {}（")
    if none_marker != mod.NO_RECOMMENDATION:
        problems.append(f"推奨しない印 {none_marker!r} ≠ 本体 {mod.NO_RECOMMENDATION!r}")
    internal_path = first_code(markdown, "\\| 内部 \\| {}（番号")
    if (internal_path or "").rsplit("/", 1)[-1] != mod.INTERNAL_NAME:
        problems.append(f"内部の表の名前 {internal_path!r} ≠ 本体 {mod.INTERNAL_NAME!r}")
    forbidden = re.findall(r"内部の表では \*\*`([^`]+)` を使わない", markdown)
    if set(forbidden) != set(mod.INTERNAL_FORBIDDEN):
        problems.append(f"内部の表で使わない状態 {forbidden!r} ≠ 本体 {sorted(mod.INTERNAL_FORBIDDEN)!r}")
    separator = first_code(write("選択肢"), "の形を {} で")
    if separator != mod.OPTION_SEPARATOR:
        problems.append(f"選択肢の区切り {separator!r} ≠ 本体 {mod.OPTION_SEPARATOR!r}")
    count = re.search(r"で (\d+) つ以上つなぐ", write("選択肢"))
    if (int(count.group(1)) if count else None) != mod.MIN_OPTIONS:
        problems.append(f"選択肢の数 {count and count.group(1)!r} ≠ 本体 {mod.MIN_OPTIONS!r}")
    # 言葉で書いた決まりは、言葉 → 本体の値の対応（下の 2 つの辞書）で突き合わせる。
    # 決まりの言葉が変わると対応に無いので None になり、不一致として見える。
    label = re.search(r"ラベルは(.+?)で、", write("選択肢"))
    if LABEL_WORDS.get(label.group(1) if label else "") != mod.OPTION_LABEL:
        problems.append(f"選択肢のラベル {label and label.group(1)!r} ≠ 本体 {mod.OPTION_LABEL!r}")
    bracket = re.search(r"詳細は(.+?)で添えて", write("起票元"))
    if BRACKET_WORDS.get(bracket.group(1) if bracket else "") != (mod.DETAIL_OPEN, mod.DETAIL_CLOSE):
        problems.append(f"起票元の括弧 {bracket and bracket.group(1)!r} ≠ 本体 {(mod.DETAIL_OPEN, mod.DETAIL_CLOSE)!r}")
    return problems


LABEL_WORDS = {"英大文字 1 字": "[A-Z]"}
BRACKET_WORDS = {"全角括弧": ("（", "）")}


# references/qa-csv.md を 1 箇所ずつ崩す。どれも突き合わせで不一致として見えなければならない
# （突き合わせが空振りしていないことの陽性対照）。
REFERENCE_MUTATIONS: list[tuple[str, str, str]] = [
    ("状態の表の 1 行", "| `反映済み` |", "| 反映済み |"),
    ("反映した状態", "仕様に反映した状態は `暫定反映` と", "仕様に反映した状態は `確認中` と"),
    ("暫定の状態", "`状態` は `暫定反映`。", "`状態` は `確認中`。"),
    ("暫定の行の判別の状態", "`状態` が `暫定反映` の行だけを、", "`状態` が `反映済み` の行だけを、"),
    ("空でよい列", "| 費用に関わらない質問は空でよい。", "| 費用に関わらない質問も空を許さない。"),
    ("費用付きの質問の起票元", "**起票元が `実現性・コスト` の行は", "**起票元が `開発` の行は"),
    ("回答の「まだ無い」の印", "まだなら `未回答` と書く", "まだなら `未定` と書く"),
    ("反映先の「まだ無い」の印", "まだなら `—` と書く", "まだなら `-` と書く"),
    ("番号の桁", "`Q-` に 3 桁以上の数字", "`Q-` に 4 桁以上の数字"),
    # ` | ` に崩すと表の行が割れて「欠落」で赤になり、値の比較を確かめられない
    ("選択肢の区切り", "の形を ` / ` で", "の形を ` ; ` で"),
    ("選択肢の数", "で 2 つ以上つなぐ", "で 3 つ以上つなぐ"),
    ("選択肢のラベル", "ラベルは英大文字 1 字で、", "ラベルは英字 1 字で、"),
    ("起票元の括弧", "詳細は全角括弧で添えて", "詳細は半角括弧で添えて"),
    ("内部の番号", "内部の表は `D-`（", "内部の表は `E-`（"),
    ("推奨しない印", "推奨しないなら `なし`（", "推奨しないなら `—`（"),
    ("内部の表の名前", "| 内部 | `docs/v<n>/spec/qa-dev.csv`（番号", "| 内部 | `docs/v<n>/spec/qa-internal.csv`（番号"),
    ("内部の表で使わない状態", "内部の表では **`暫定反映` を使わない**", "内部の表では **`確認中` を使わない**"),
]


def reference_example(markdown: str, heading: str = "例") -> str | None:
    m = re.search(rf"^## {re.escape(heading)}\n.*?```csv\n(.*?)```", markdown, re.S | re.M)
    return m.group(1) if m else None


def main() -> int:
    mod = load(SCRIPT)
    reference = REFERENCE.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = [write_case(root, i, content, name.startswith("内部:")) for i, (name, content, _, _) in enumerate(CASES)]

        print("1・2. 試料（陽性対照を含む）")
        for (name, _, code, text), path in zip(CASES, paths):
            result = run_case(mod, path)
            check(name, matches(result, code, text), f"終了 {result[0]}: {result[1]!r}")

        print("3. references/qa-csv.md との一致")
        problems = reference_mismatches(mod, reference)
        check("決まりの表が本体の定数と一致する", not problems, "; ".join(problems))
        for name, before, after in REFERENCE_MUTATIONS:
            if reference.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {reference.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(mod, reference.replace(before, after))))
        example = reference_example(reference)
        check("「例」のブロックがある", example is not None)
        if example is not None:
            result = run_case(mod, write_case(root, 900, example))
            check("「例」が決まりを破っていない", result[0] == 0, result[1])
        internal = reference_example(reference, "内部の表の例")
        check("「内部の表の例」のブロックがある", internal is not None)
        if internal is not None:
            result = run_case(mod, write_case(root, 901, internal, internal=True))
            check("「内部の表の例」が決まりを破っていない", result[0] == 0, result[1])

        print("4. リポジトリの外で単体で動く")
        alone = root / "alone"
        alone.mkdir()
        copied = alone / "check-qa-csv.py"
        shutil.copy(SCRIPT, copied)
        assert_in_tmp(copied)
        good, bad = paths[0], paths[CASES.index(next(c for c in CASES if c[0] == "未知の状態"))]
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        ok = subprocess.run([sys.executable, "-I", str(copied), str(good)], cwd=alone, env=env,
                            capture_output=True, text=True)
        ng = subprocess.run([sys.executable, "-I", str(copied), str(bad)], cwd=alone, env=env,
                            capture_output=True, text=True)
        check("決まりどおりなら 0", ok.returncode == 0, ok.stderr)
        check("反していれば 1 で、理由を stderr に出す", ng.returncode == 1 and "`状態`" in ng.stderr, ng.stderr)
        usage = subprocess.run([sys.executable, "-I", str(copied)], cwd=alone, env=env,
                               capture_output=True, text=True)
        check("引数が無ければ 2 で使い方を出す", usage.returncode == 2 and "usage:" in usage.stderr, usage.stderr)

        print("4b. 番号から層を決める（is_internal_number）")
        problems = number_layer_mismatches(mod)
        check("番号の層が期待どおり", not problems, "; ".join(problems))

        print("4b'. 暫定の行の判別（is_provisional。状態だけで決め、回答の文言は見ない——#404）")
        problems = provisional_mismatches(mod)
        check("暫定の判別が期待どおり（否定・肯定の書き方を含む）", not problems, "; ".join(problems))
        sources = reader_sources()
        problems = reader_problems(sources)
        check("読む側が全部 is_provisional を通す（写しを持たない）", not problems, "; ".join(problems))
        for name, file, before, after in READER_MUTATIONS:
            if sources[file].count(before) != 1:
                check(f"崩すと見える: {name}", False, f"崩す箇所が {sources[file].count(before)} 回現れる")
                continue
            check(f"崩すと見える: {name}", bool(reader_problems({**sources, file: sources[file].replace(before, after)})))

        print("4c. 移す手順への指し先が references/ の見出しにある")
        references = {p.name: p.read_text(encoding="utf-8") for p in REFERENCES.glob("*.md")}
        sources = pointer_sources(mod)
        problems = pointer_mismatches(sources, references)
        check("指し先の見出しが実在する", not problems, "; ".join(problems))
        check("フックの定数 QA_MIGRATION を単独の指し先として数える", bool(sources[f"{HOOK.name} の QA_MIGRATION"]))
        hook = HOOK.read_text(encoding="utf-8")
        before = 'QA_MIGRATION = "spec-loop の references/tree.md の「Q&A 表を移す」"'
        if hook.count(before) != 1:
            check("崩すと不一致になる: フックの定数を別のファイルに向ける", False, f"崩す箇所が {hook.count(before)} 回現れる")
        else:
            # 実在する別の見出しに向ける——見出しの実在だけを見る検査では緑のまま（#353 の 2 パス目）
            broken = hook.replace(before, 'QA_MIGRATION = "spec-loop の references/qa-csv.md の「層」"')
            check("崩すと不一致になる: フックの定数を別のファイルに向ける",
                  bool(pointer_mismatches(pointer_sources(mod, broken), references)))
        for name, file, before, after in POINTER_MUTATIONS:
            if references[file].count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {references[file].count(before)} 回現れる")
                continue
            broken = {**references, file: references[file].replace(before, after)}
            check(f"崩すと不一致になる: {name}", bool(pointer_mismatches(sources, broken)))

        print("5. 変異テスト")
        source = SCRIPT.read_text(encoding="utf-8")
        by_name = {name: (code, text, path) for (name, _, code, text), path in zip(CASES, paths)}
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届く: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            broken = root / f"mutant-{index}.py"
            broken.write_text(source.replace(before, after), encoding="utf-8")
            assert_in_tmp(broken)
            mutant = load(broken)
            code, text, path = by_name[killer]
            check(f"変異を殺せる: {name}（{killer}）", not matches(run_case(mutant, path), code, text))
        for index, (name, before, after) in enumerate(NUMBER_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届く: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            broken = root / f"number-mutant-{index}.py"
            broken.write_text(source.replace(before, after), encoding="utf-8")
            assert_in_tmp(broken)
            check(f"変異を殺せる: {name}（番号の層）", bool(number_layer_mismatches(load(broken))))
        for index, (name, before, after) in enumerate(PROVISIONAL_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届く: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            broken = root / f"provisional-mutant-{index}.py"
            broken.write_text(source.replace(before, after), encoding="utf-8")
            assert_in_tmp(broken)
            check(f"変異を殺せる: {name}（暫定の判別）", bool(provisional_mismatches(load(broken))))
        broken = root / "pointer-mutant.py"
        broken.write_text(source.replace('MIGRATION = "references/tree.md の「Q&A 表を移す」"',
                                         'MIGRATION = "references/tree.md の「Q&A 表を直す」"'), encoding="utf-8")
        assert_in_tmp(broken)
        check("変異を殺せる: 本体の指し先を無い見出しにする",
              bool(pointer_mismatches(pointer_sources(load(broken)), references)))

    print()
    if failures:
        print(f"FAIL: {len(failures)} 件")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(NUMBER_MUTATIONS) + len(PROVISIONAL_MUTATIONS) + len(READER_MUTATIONS) + 1} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
