#!/usr/bin/env python3
"""`check-design-csv.py`（システム設計書の成果物の表の検査。#957）の回帰テスト。

    python3 scripts/test-check-design-csv.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-feasibility-csv.py` と同じ形。

見るもの:

1. **決まりに反する形を、理由つきで落とす（1）**——見出し（順・物理設計の列を足す）・列の数・id の形・重複（id・エンティティと項目・
   id と順番）・決まった値（種類・必須・向き・ヘッダー・権限の可否）・順番・レイアウトの id が一覧に無い（一覧が無いときも）・帳票名・
   権限一覧の見出し（1 列目・ロールが無い・重複）と操作の重複・非機能要求の種類の上限と単位・No の形と重複・見出し・
   目的の表（#1154）の見出し・列の数・id の形と重複・種類ごとに空にする欄・上位が目的でない／表に無い・機能の id の形・機能一覧に無い id（一覧が無いときも）・`なし` の混在。
   関係者の表（#1161）の見出し・列の数・id の形と重複・名前の重複・役割と合意の値（区切り・`なし` を役割に書く）・同じ値の重ね・合意の `なし` の混在。
2. **決まりどおりの形を通す**（陽性対照。BOM・空でよい欄が空・性能の行とほかの語の行は崩れていても見ない）。
3. **4 つを分けて出す**——形式の違反（1）・表が無い（止めない。0）・必須の欄が空（3）・未決定の印（3。全角も）。
   **未決定の印のあるセルを値の違反に数えない**。違反と未決定が両方あれば 1 で、両方の見出しを出す。
   **目的の表の結び付けの欠け**（目的を測る指標が無い・目的を指さない機能・機能一覧があるのに指標の機能が空）も 3。
   機能一覧が無ければ指標の機能は空でよい（0）。
3a. **回答者の照合を報告し、終了コードに数えない**（#1161）——表に無い・答える範囲が `なし`・括弧から読めない回答を出す。表にある人・`未回答`・暫定の行は出さない。
   範囲が未決定の人は答える人に数える。関係者の表が決まりに反する・無いなら照らさない。Q&A 表の見出しが違えば照らさないと出す。
4. **中身を検査していない形を 0 にしない（2）**——UTF-8 でない・空のファイル・ファイルでない・ディレクトリが無い・引数の誤り・
   想定外の例外（128KB 超のセルの `csv.Error`）・`-OO` で引数なし。
5. **本体の定数が `references/tree.md` の「システム設計書の成果物」と `references/nfr.md` の「性能のほかの種類」の表と一致する**（写しのずれ。
   目的の表は列・決める人・id の接頭辞と種類・種類ごとに書く列・`機能` の区切りと `なし`。関係者の表は列・決める人・id の接頭辞・役割と合意の値・区切りと `なし`）。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-design-csv.py"
TREE = PLUGIN / "references" / "tree.md"
NFR_REF = PLUGIN / "references" / "nfr.md"

F = "requirements/features.csv"
E = "requirements/entities.csv"
IO = "requirements/io.csv"
L = "requirements/io-layout.csv"
R = "requirements/reports.csv"
RO = "requirements/roles.csv"
J = "requirements/jobs.csv"
N = "shared/nfr.csv"
P = "requirements/purposes.csv"
S = "shared/stakeholders.csv"
Q = "shared/qa.csv"

F_HEAD = "id,名前,種類,関係\n"
E_HEAD = "エンティティ,項目,意味,型,必須,保管期間\n"
IO_HEAD = "id,名前,向き,相手,形式,文字コード,区切り,ヘッダー,契機\n"
L_HEAD = "id,順番,項目,型,桁,必須,意味\n"
R_HEAD = "id,帳票名,順番,項目,意味,書式\n"
RO_HEAD = "操作,管理者,担当者\n"
J_HEAD = "id,名前,契機,周期,失敗したときの扱い\n"
N_HEAD = "No,対象,指標,上限,単位,条件,根拠\n"
P_HEAD = "id,上位,誰の課題か,内容,成功の判定,機能\n"
P_GOAL = "G-001,,受注の担当者,受注の入力の手間を減らす,,\n"
P_OK = (P_GOAL + "K-001,G-001,,1 件の受注の入力にかかる時間,5 分から 2 分以下に,F-001・F-002\n"
        "K-002,G-001,,入力の誤り,月 3 件以下,なし\n")
S_HEAD = "id,名前,役割,関心事,答える範囲,合意\n"
S_OK = ("P-001,業務部長,利用者・決裁者,受注の入力の手間,受注の業務ルール,要求確定・決裁\n"
        "P-002,経理部,予算責任者,開発費と運用費,なし,予算\n"
        "P-003,倉庫システムの担当,連携先,在庫の連携のファイル,IO-001,なし\n")
Q_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"


def qa_rows(*answers: tuple[str, str]) -> str:
    """共有の Q&A 表の試料。(回答, 状態) ごとに 1 行（番号は Q-R-001 から）。"""
    return Q_HEAD + "".join(f"Q-R-{i:03d},要求確定,質問,A: x / B: y,A,理由,{answer},{'—' if answer == '未回答' else '決定表 1 行目'},{state},\n"
                            for i, (answer, state) in enumerate(answers, start=1))


def stakeholders(body: str = S_OK, qa: str | None = None) -> dict:
    """関係者の表の試料（#1161）。`qa` があれば共有の Q&A 表も置く。ほかの表は置かない。"""
    files = {S: S_HEAD + body}
    if qa is not None:
        files[Q] = qa
    return files


GOOD = {
    F: F_HEAD + "F-001,注文の受付,API,flows/受注.svg\nF-002,注文の一覧,画面,\n",
    E: E_HEAD + "注文,注文番号,注文を一意に示す番号,文字列,はい,7 年\n注文,メモ,自由記述,文字列,いいえ,7 年\n",
    IO: IO_HEAD + "IO-001,受注の取り込み,入力,販売管理,CSV,Shift_JIS,カンマ,あり,毎日 6 時\n",
    L: L_HEAD + "IO-001,1,注文番号,文字列,10,はい,注文番号\nIO-001,2,金額,数,,いいえ,税込の金額\n",
    R: R_HEAD + "RP-001,月次売上,1,月,対象の月,YYYY/MM\nRP-001,月次売上,2,売上,税込の合計,\n",
    RO: RO_HEAD + "注文の取り消し,可,不可\n注文の受付,可,可\n",
    J: J_HEAD + "J-001,売上の締め,毎日 23 時,毎日,翌朝に担当者へ通知する\n",
    N: N_HEAD + "N-001,割引,p95,300,ms,ピーク 50 req/s,実測\n"
    "N-002,注文の受付,可用性,99.9,%,月の稼働で,契約\n"
    "N-003,日次のバックアップ,保管期間,30,日,バックアップの世代として,監査\n"
    "N-004,注文のデータベース,バックアップ,1,日,毎日,監査\n"
    "N-005,顧客の個人情報,セキュリティ,暗号化して保存する,,保存するすべて,社内規程\n"
    # 性能の行とほかの語の行は見ない（崩れていても止めない）
    "N-006,検索,p99,abc,秒,,\n"
    "N-007,x,稼働率,,,,\n",
}


def good(**changes) -> dict:
    """GOOD の表を差し替える（値 None なら置かない）。キーは表の短い名前。"""
    names = {"F": F, "E": E, "IO": IO, "L": L, "R": R, "RO": RO, "J": J, "N": N}
    files = dict(GOOD)
    for key, value in changes.items():
        rel = names[key]
        if value is None:
            files.pop(rel, None)
        else:
            files[rel] = value
    return files


def nfr(row: str) -> dict:
    return good(N=N_HEAD + row + "\n")


def purposes(body: str, features: str | None = None) -> dict:
    """目的の表の試料（#1154）。機能一覧は GOOD のもの（F-001・F-002）か `features`（"" なら置かない）。ほかの表は置かない。"""
    files = {P: P_HEAD + body}
    feature_list = GOOD[F] if features is None else features
    if feature_list:
        files[F] = feature_list
    return files


# (名前, 置く表（パス → 中身。bytes はそのまま・"<dir>" はディレクトリ）, 引数（None なら根）, 期待する終了コード, 出力に含まれるべき文字列, 含まれてはならない文字列)
CASES: list[tuple[str, dict | None, list[str] | None, int, str, str]] = [
    ("決まりどおり", GOOD | {P: P_HEAD + P_OK, S: S_HEAD + S_OK}, None, 0, "OK（requirements/features.csv（2 行）", "表が無い"),
    ("BOM 付き", {rel: "﻿" + body for rel, body in GOOD.items()}, None, 0, "OK（", "見出しの行"),
    ("表が無いだけ", {F: GOOD[F]}, None, 0, "表が無い（9 件）", "成果物の表が 1 つも無い"),
    ("表が 1 つも無い", {}, None, 0, "成果物の表が 1 つも無い", ""),
    # ---- 形式の違反
    ("見出しの順が違う", good(F="id,種類,名前,関係\nF-001,API,a,\n"), None, 1, "見出しの行が決まりと違う", "決まりに無い列"),
    ("物理設計の列を足す", good(E="エンティティ,項目,意味,型,必須,保管期間,インデックス\n注文,番号,a,文字列,はい,7 年,あり\n"), None, 1,
     "決まりに無い列（インデックス）", ""),
    ("列の数", good(F=F_HEAD + "F-001,a,API\n"), None, 1, "requirements/features.csv:2: 列の数が 3", ""),
    ("id の形", good(F=F_HEAD + "F-01,a,API,\n"), None, 1, "id が F- に 3 桁以上の数字の形でない: 'F-01'", ""),
    ("id の重複", good(F=F_HEAD + "F-001,a,API,\nF-001,b,画面,\n"), None, 1, "id が 2 行目と重複: F-001", ""),
    ("種類の値", good(F=F_HEAD + "F-001,a,帳票,\n"), None, 1, "種類 が 画面・API・バッチ・ファイル連携 のどれでもない: '帳票'", ""),
    ("必須の値", good(E=E_HEAD + "注文,番号,a,文字列,必要,7 年\n"), None, 1, "必須 が はい・いいえ のどれでもない", ""),
    ("エンティティと項目の重複", good(E=E_HEAD + "注文,番号,a,文字列,はい,7 年\n注文,番号,b,文字列,はい,7 年\n"), None, 1,
     "エンティティ・項目 が 2 行目と重複: 注文 / 番号", ""),
    ("向きの値", good(IO=IO_HEAD + "IO-001,a,双方向,b,CSV,UTF-8,カンマ,あり,c\n"), None, 1, "向き が 入力・出力 のどれでもない", ""),
    ("ヘッダーの値", good(IO=IO_HEAD + "IO-001,a,入力,b,CSV,UTF-8,カンマ,有,c\n"), None, 1, "ヘッダー が あり・なし のどれでもない", ""),
    ("入出力の id の形", good(IO=IO_HEAD + "IO-1,a,入力,b,CSV,UTF-8,カンマ,あり,c\n"), None, 1, "id が IO- に 3 桁以上", ""),
    ("レイアウトの id が一覧に無い", good(L=L_HEAD + "IO-002,1,a,文字列,,はい,b\n"), None, 1,
     "id IO-002 が入出力の一覧（requirements/io.csv）に無い", ""),
    ("レイアウトだけあって一覧が無い", good(IO=None), None, 1, "を照らす入出力の一覧（requirements/io.csv）が無い・読めない", ""),
    ("順番が 0", good(L=L_HEAD + "IO-001,0,a,文字列,,はい,b\n"), None, 1, "順番 が正の整数でない: '0'", ""),
    ("順番が小数", good(R=R_HEAD + "RP-001,a,1.5,b,c,\n"), None, 1, "順番 が正の整数でない: '1.5'", ""),
    ("順番の重複", good(L=L_HEAD + "IO-001,1,a,文字列,,はい,b\nIO-001,1,c,文字列,,はい,d\n"), None, 1,
     "id・順番 が 2 行目と重複: IO-001 / 1", ""),
    # 別のファイルなら同じ順番でよい（陽性対照）
    ("別のファイルの同じ順番", good(IO=GOOD[IO] + "IO-002,b,出力,c,CSV,UTF-8,カンマ,なし,d\n",
                           L=L_HEAD + "IO-001,1,a,文字列,,はい,b\nIO-002,1,c,文字列,,はい,d\n"), None, 0, "OK（", ""),
    ("帳票名が違う", good(R=R_HEAD + "RP-001,月次売上,1,a,b,\nRP-001,月次の売上,2,c,d,\n"), None, 1,
     "帳票 RP-001 の帳票名が 2 行目と違う", ""),
    ("ジョブの id の形", good(J=J_HEAD + "J-1,a,b,c,d\n"), None, 1, "id が J- に 3 桁以上", ""),
    ("権限の 1 列目が違う", good(RO="機能,管理者\nx,可\n"), None, 1, "見出しの行が「操作,<ロール>,<ロール>…」", ""),
    ("権限のロールが無い", good(RO="操作\nx\n"), None, 1, "（ロールは 1 つ以上）でない", ""),
    ("権限のロールの重複", good(RO="操作,管理者,管理者\nx,可,可\n"), None, 1, "ロール '管理者' が 2 列目と重複", ""),
    ("権限のロール名が空", good(RO="操作,管理者,\nx,可,可\n"), None, 1, "3 列目のロール名が空", ""),
    ("種類の行の No が後ろの性能の行と重複", nfr("N-001,a,可用性,99,%,b,c\nN-001,a,p95,300,ms,b,c"), None, 1,
     "shared/nfr.csv:2: No が後ろの行と重複: N-001", ""),
    ("権限の可否の値", good(RO=RO_HEAD + "x,○,不可\n"), None, 1, "管理者 の可否が 可・不可 のどれでもない: '○'", ""),
    ("権限の操作の重複", good(RO=RO_HEAD + "x,可,可\nx,可,不可\n"), None, 1, "操作 が 2 行目と重複: x", ""),
    ("権限の列の数", good(RO=RO_HEAD + "x,可\n"), None, 1, "requirements/roles.csv:2: 列の数が 2", ""),
    ("可用性が 100 を超える", nfr("N-001,a,可用性,100.5,%,b,c"), None, 1, "可用性 の上限が 0 より大きく 100 以下の数でない: '100.5'", ""),
    ("可用性が 0", nfr("N-001,a,可用性,0,%,b,c"), None, 1, "可用性 の上限が 0 より大きく 100 以下の数でない: '0'", ""),
    ("可用性が 100 ちょうど", nfr("N-001,a,可用性,100,%,b,c"), None, 0, "OK（", ""),
    ("可用性の単位", nfr("N-001,a,可用性,99.9,％,b,c"), None, 1, "可用性 の単位が % のどれでもない: '％'", ""),
    ("保管期間が小数", nfr("N-001,a,保管期間,1.5,年,b,c"), None, 1, "保管期間 の上限が正の整数でない: '1.5'", ""),
    ("保管期間の単位", nfr("N-001,a,保管期間,1,週,b,c"), None, 1, "保管期間 の単位が 日・月・年 のどれでもない: '週'", ""),
    ("バックアップの単位", nfr("N-001,a,バックアップ,1,年,b,c"), None, 1, "バックアップ の単位が 時間・日 のどれでもない: '年'", ""),
    ("セキュリティに単位", nfr("N-001,a,セキュリティ,暗号化する,ms,b,c"), None, 1, "セキュリティ の単位は空にする", ""),
    ("種類の行の No の形", nfr("N-1,a,可用性,99,%,b,c"), None, 1, "No が N- に 3 桁以上の数字の形でない: 'N-1'", ""),
    ("種類の行の No が性能の行と重複", nfr("N-001,a,p95,1,ms,b,c\nN-001,a,可用性,99,%,b,c"), None, 1,
     "shared/nfr.csv:3: No が 2 行目と重複: N-001", ""),
    ("非機能要求の見出し", good(N="No,対象,指標,上限,単位,条件,理由\nN-001,a,可用性,99,%,b,c\n"), None, 1, "見出しの行が決まりと違う", ""),
    ("非機能要求の見出しの指標の位置で種類を探す", good(N="No,指標,対象,上限,単位,条件,根拠\nN-001,可用性,a,99,%,b,c\n"), None, 1,
     "見出しの行が決まりと違う", ""),
    # 種類の行の無い表の見出しは見ない（性能の行とほかの語の行は、この検査の外。scaffold の関門を変えない）
    ("種類の行の無い非機能要求の見出しは見ない", good(N="No,対象,指標,上限,単位,条件,理由\nN-001,a,p95,300,ms,b,c\n"), None, 0, "OK（", "見出しの行"),
    ("種類の行の列の数", nfr("N-001,a,可用性,99,%,b"), None, 1, "shared/nfr.csv:2: 列の数が 6", ""),
    # ---- 決まっていない欄（3）
    ("読めない非機能要求", good(N=b"\x82\xa0No\n"), None, 2, "shared/nfr.csv: UTF-8 として読めない", ""),
    ("未決定の印", good(E=E_HEAD + "注文,番号,a,文字列,はい,未定\n"), None, 3, "未決定の印（1 件）:\n  requirements/entities.csv:2: 保管期間 に未決定の印（未定）", "形式の違反（"),
    ("全角の未決定の印", good(IO=IO_HEAD + "IO-001,a,入力,b,CSV,ＴＢＤ,カンマ,あり,c\n"), None, 3, "文字コード に未決定の印（TBD）", ""),
    ("値の決まった欄の未決定の印", good(F=F_HEAD + "F-001,a,要確認,\n"), None, 3, "種類 に未決定の印（要確認）", "どれでもない"),
    ("必須の欄が空", good(J=J_HEAD + "J-001,a,b,,d\n"), None, 3, "必須の欄が空（1 件）:\n  requirements/jobs.csv:2: 周期 が空", "形式の違反（"),
    ("空でよい欄が空", good(L=L_HEAD + "IO-001,1,a,文字列,,はい,b\n"), None, 0, "OK（", "が空"),
    ("一覧の id が未決定ならレイアウトの id も未決定", good(IO=IO_HEAD + "TBD,受注の取り込み,入力,販売管理,CSV,UTF-8,カンマ,あり,毎日\n"), None, 3,
     "id IO-001 が入出力の一覧（requirements/io.csv）に無い（一覧に id の決まっていない行がある）", "形式の違反（"),
    ("権限の可否が未決定", good(RO=RO_HEAD + "x,可,TBD\n"), None, 3, "担当者 の可否 に未決定の印（TBD）", "どれでもない"),
    ("種類の行の根拠が空", nfr("N-001,a,可用性,99,%,b,"), None, 3, "shared/nfr.csv:2: 根拠 が空", ""),
    ("種類の行の上限が未決定", nfr("N-001,a,保管期間,未定,年,b,c"), None, 3, "上限 に未決定の印（未定）", "正の整数でない"),
    ("違反と未決定が両方", good(F=F_HEAD + "F-01,a,API,\n", J=J_HEAD + "J-001,a,b,,d\n"), None, 1, "必須の欄が空（1 件）", ""),
    # ---- 判定していない（2）
    # ---- 目的の表（#1154）
    ("目的の表: 決まりどおり", purposes(P_OK), None, 0, "requirements/purposes.csv（3 行）", "目的を指さない"),
    ("目的の表: 見出し", purposes(P_OK) | {P: "id,上位,内容,誰の課題か,成功の判定,機能\n" + P_OK}, None, 1,
     "requirements/purposes.csv:1: 見出しの行が決まりと違う", ""),
    ("目的の表: 列の数", purposes(P_GOAL + "K-001,G-001,,a,b\n"), None, 1, "requirements/purposes.csv:3: 列の数が 5", ""),
    ("目的の表: id の形", purposes(P_OK.replace("K-002", "K-02")), None, 1, "id が G-（目的）か K-（指標）に 3 桁以上の数字の形でない: 'K-02'", ""),
    ("目的の表: id の重複", purposes(P_OK + P_GOAL), None, 1, "requirements/purposes.csv:5: id が 2 行目と重複: G-001", ""),
    ("目的の表: 目的の行に成功の判定", purposes(P_OK.replace("受注の入力の手間を減らす,,", "受注の入力の手間を減らす,半分に,")), None, 1,
     "目的の行に 成功の判定 を書いた（指標の行だけに書く）: '半分に'", ""),
    ("目的の表: 指標の行に誰の課題か", purposes(P_OK.replace("K-002,G-001,,", "K-002,G-001,営業,")), None, 1,
     "指標の行に 誰の課題か を書いた（目的の行だけに書く）: '営業'", ""),
    ("目的の表: 上位が目的でない", purposes(P_OK.replace("K-002,G-001", "K-002,K-001")), None, 1, "上位 K-001 が目的（G-）の行でない", ""),
    ("目的の表: 上位が表に無い", purposes(P_OK.replace("K-002,G-001", "K-002,G-009")), None, 1, "上位 G-009 が表の目的に無い", ""),
    ("目的の表: id の決まっていない行があれば上位は未決定", purposes(P_OK.replace("K-002,G-001", "K-002,G-009") + "未定,,営業,b,,\n"), None, 3,
     "上位 G-009 が表に無い（表に id の決まっていない行がある）", "が表の目的に無い"),
    ("目的の表: 機能が機能一覧に無い", purposes(P_OK.replace("なし", "F-009")), None, 1,
     "機能 F-009 が機能一覧（requirements/features.csv）に無い", ""),
    ("目的の表: 機能の区切り", purposes(P_OK.replace("F-001・F-002", "F-001、F-002")), None, 1, "機能 の値が機能一覧の id（F- に 3 桁以上の数字）でない", ""),
    ("目的の表: なしと id を混ぜる", purposes(P_OK.replace(",なし", ",なし・F-001")), None, 1, "機能 に なし と機能の id を混ぜた", ""),
    ("目的の表: 機能一覧が無いのに機能を書く", purposes(P_OK, features=""), None, 1,
     "機能 の id を照らす機能一覧（requirements/features.csv）が無い・読めない", ""),
    ("目的の表: 機能一覧が無ければ機能は空でよい", purposes(P_OK.replace("F-001・F-002", ""), features=""), None, 0, "requirements/purposes.csv（3 行）",
     "機能 が空"),
    ("目的の表: 機能一覧があれば機能が空は未決定", purposes(P_OK.replace("F-001・F-002", "")), None, 3,
     "requirements/purposes.csv:3: 機能 が空（どの機能も動かさない指標", ""),
    ("目的の表: 目的を指さない機能", purposes(P_OK.replace("F-001・F-002", "F-001")), None, 3,
     "requirements/purposes.csv: 機能一覧の F-002 が、どの指標の 機能 にも無い（目的を指さない機能", "F-001 が、どの指標"),
    ("目的の表: 目的を測る指標が無い", purposes(P_OK + "G-002,,営業,見積りを早く出す,,\n"), None, 3,
     "requirements/purposes.csv:5: 目的 G-002 を測る指標（上位が G-002 の K- の行）が無い", "目的 G-001"),
    ("目的の表: 空にする欄の未決定の印", purposes(P_OK.replace("受注の入力の手間を減らす,,", "受注の入力の手間を減らす,未定,")), None, 3,
     "requirements/purposes.csv:2: 成功の判定 に未決定の印（未定）", "を書いた"),
    ("目的の表: 必須の欄が空", purposes(P_OK.replace(",受注の担当者,", ",,")), None, 3, "requirements/purposes.csv:2: 誰の課題か が空", ""),
    ("目的の表: 機能の未決定の印", purposes(P_OK.replace("F-001・F-002", "未定")), None, 3, "requirements/purposes.csv:3: 機能 に未決定の印（未定）", ""),
    ("目的の表: 印と並べた決まった id は結び付けに数える", purposes(P_OK.replace("F-001・F-002", "F-001・未定")), None, 3,
     "requirements/purposes.csv:3: 機能 に未決定の印（未定）", "機能一覧の F-001 が"),
    ("目的の表: 一覧の id が未決定なら機能の id も未決定", purposes(P_OK.replace("なし", "F-009"), features=GOOD[F] + "TBD,x,API,\n"), None, 3,
     "機能 F-009 が機能一覧（requirements/features.csv）に無い（一覧に id の決まっていない行がある）", ""),
    # ---- 関係者の表（#1161）
    ("関係者の表: 決まりどおり", stakeholders(), None, 0, "OK（shared/stakeholders.csv（3 行））", "回答者の照合"),
    ("関係者の表: 見出し", {S: "id,役割,名前,関心事,答える範囲,合意\nP-001,利用者,業務部長,a,b,なし\n"}, None, 1,
     "shared/stakeholders.csv:1: 見出しの行が決まりと違う", ""),
    ("関係者の表: 列の数", stakeholders("P-001,業務部長,利用者,a,b\n"), None, 1, "shared/stakeholders.csv:2: 列の数が 5", ""),
    ("関係者の表: id の形", stakeholders(S_OK.replace("P-002", "P-02")), None, 1, "id が P- に 3 桁以上の数字の形でない: 'P-02'", ""),
    ("関係者の表: id の重複", stakeholders(S_OK.replace("P-002", "P-001")), None, 1, "shared/stakeholders.csv:3: id が 2 行目と重複: P-001", ""),
    ("関係者の表: 名前の重複", stakeholders(S_OK.replace("経理部", "業務部長")), None, 1, "shared/stakeholders.csv:3: 名前 が 2 行目と重複: 業務部長", ""),
    ("関係者の表: 役割の値", stakeholders(S_OK.replace("予算責任者,", "担当者,")), None, 1,
     "役割 の値が 利用者・予算責任者・決裁者・連携先 のどれでもない: '担当者'", ""),
    ("関係者の表: 役割になしを書く", stakeholders(S_OK.replace("予算責任者,", "なし,")), None, 1,
     "役割 の値が 利用者・予算責任者・決裁者・連携先 のどれでもない: 'なし'", ""),
    ("関係者の表: 役割の重ね", stakeholders(S_OK.replace("利用者・決裁者", "利用者・利用者")), None, 1, "役割 に同じ値を重ねた: '利用者・利用者'", ""),
    ("関係者の表: 合意の値", stakeholders(S_OK.replace(",予算\n", ",承認\n")), None, 1, "合意 の値が 要求確定・予算・決裁 のどれでもない: '承認'", ""),
    ("関係者の表: 合意の区切り", stakeholders(S_OK.replace("要求確定・決裁", "要求確定、決裁")), None, 1,
     "合意 の値が 要求確定・予算・決裁 のどれでもない: '要求確定、決裁'", ""),
    ("関係者の表: 合意になしとほかを混ぜる", stakeholders(S_OK.replace(",予算\n", ",予算・なし\n")), None, 1, "合意 に なし とほかの値を混ぜた", ""),
    ("関係者の表: 名前に区切りの文字", stakeholders(S_OK.replace("経理部", "総務・経理部")), None, 1,
     "shared/stakeholders.csv:3: 名前 に '・' を使った（承認の行の区切りと回答の括弧に使う文字）: 総務・経理部", ""),
    ("関係者の表: 名前に括弧", stakeholders(S_OK.replace("経理部", "情報システム部（IT）")), None, 1, "名前 に '（'・'）' を使った", ""),
    ("回答者: Q&A 表の巨大なセルでも終了コードを変えない", stakeholders(qa=Q_HEAD + "Q-R-001,要求確定,質問,A: x / B: y,A," + "x" * 200_000 + ",A（業務部長が回答）,a,反映済み,\n"),
     None, 0, "shared/qa.csv: CSV として読めない", "想定外の例外"),
    ("関係者の表: 必須の欄が空", stakeholders(S_OK.replace("開発費と運用費", "")), None, 3, "shared/stakeholders.csv:3: 関心事 が空", ""),
    ("関係者の表: 未決定の印", stakeholders(S_OK.replace("受注の業務ルール", "未定")), None, 3, "shared/stakeholders.csv:2: 答える範囲 に未決定の印（未定）", ""),
    ("回答者: 表に無い", stakeholders(qa=qa_rows(("A（業務部長が回答）", "反映済み"), ("A（営業部が回答）", "反映済み"))), None, 0,
     "shared/qa.csv:3: Q-R-002 の回答者 営業部 が関係者の表（shared/stakeholders.csv）の名前に無い", "Q-R-001"),
    ("回答者: 答える範囲がなし", stakeholders(qa=qa_rows(("A（経理部が回答）", "確認中"))), None, 0,
     "Q-R-001 の回答者 経理部 は関係者の表で答える範囲が なし", ""),
    ("回答者: 括弧から読めない", stakeholders(qa=qa_rows(("A（業務部長）", "反映済み"))), None, 0,
     "Q-R-001 の回答から答えた人を読めない（括弧を `<関係者の名前>が回答` で始める）: 'A（業務部長）'", ""),
    ("回答者: 表にある人は出さない", stakeholders(qa=qa_rows(("A（業務部長が回答）", "反映済み"), ("B（業務部長が確認）", "反映済み"),
                                                          ("A（倉庫システムの担当が回答。モック requirements/mocks/a.html）", "反映済み"))), None, 0,
     "OK（shared/stakeholders.csv（3 行））", "回答者の照合"),
    ("回答者: 未回答と暫定は見ない", stakeholders(qa=qa_rows(("未回答", "確認中"), ("A（暫定で採用。営業部 2026-10-21 の指示）", "暫定反映"))), None, 0,
     "OK（", "回答者の照合"),
    ("回答者: 範囲が未決定の人は答える人に数える", stakeholders(S_OK.replace("受注の業務ルール", "未定"), qa_rows(("A（業務部長が回答）", "反映済み"))), None, 3,
     "答える範囲 に未決定の印（未定）", "回答者の照合"),
    ("回答者: 表が決まりに反するなら照らさない", stakeholders(S_OK.replace("P-002", "P-02"), qa_rows(("A（営業部が回答）", "反映済み"))), None, 1,
     "shared/stakeholders.csv が決まりに反する・読めないので、回答者を照らしていない", "営業部 が関係者の表"),
    ("回答者: Q&A 表の見出しが違えば照らさない", stakeholders(qa=Q_HEAD.replace("推奨,推奨の理由,", "") + "Q-001,要求確定,a,A: x / B: y,A（営業部が回答）,b,反映済み,\n"),
     None, 0, "shared/qa.csv: 見出しの行が決まりと違う——回答者を照らしていない", "営業部"),
    ("回答者: 関係者の表が無ければ照らさない", {Q: qa_rows(("A（営業部が回答）", "反映済み"))}, None, 0, "成果物の表が 1 つも無い", "回答者の照合"),
    ("UTF-8 でない", good(F=(F_HEAD + "F-001,注文,API,\n").encode("cp932")), None, 2, "requirements/features.csv: UTF-8 として読めない", ""),
    ("空のファイル", good(F=""), None, 2, "requirements/features.csv: 空のファイル", ""),
    ("ファイルでない", good(F="<dir>"), None, 2, "requirements/features.csv: ファイルでない", ""),
    ("ディレクトリが無い", {}, ["無い"], 2, "ディレクトリが無い", ""),
    ("引数が無い", {}, [], 2, "usage:", ""),
    ("巨大なセル", good(F=F_HEAD + "F-001," + "x" * 200_000 + ",API,\n"), None, 2, "想定外の例外で止まった（Error: field larger", ""),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("一覧の未決定の id を見ない", '            elif row["id"].strip() not in listed and context.get(IO_LIST + "#pending"):',
     "            elif False:", "一覧の id が未決定ならレイアウトの id も未決定"),
    ("見出しを見ない", "    if header == expected:\n        return True", "    if True:\n        return True", "見出しの順が違う"),
    ("物理設計の列を名指ししない", "    if extra:", "    if False:", "物理設計の列を足す"),
    ("列の数を見ない", "        if len(fields) != len(expected):", "        if False:", "列の数"),
    ("決まった値を見ない", "            if allowed and value not in allowed:", "            if False:", "種類の値"),
    ("id の形を見ない", '                if not re.fullmatch(re.escape(ID_PREFIX[rel]) + r"[0-9]{3,}", value):', "                if False:", "id の形"),
    ("重複を見ない", "            if key in seen:", "            if False:", "id の重複"),
    ("順番を見ない", "            if column == ORDER_COLUMN and not POSITIVE_INTEGER.fullmatch(value):", "            if False:", "順番が 0"),
    ("順番を 0 も許す", 'POSITIVE_INTEGER = re.compile(r"[1-9][0-9]{0,8}")', 'POSITIVE_INTEGER = re.compile(r"[0-9]{1,9}")', "順番が 0"),
    ("レイアウトの id を照らさない", '            elif row["id"].strip() not in listed:', "            elif False:", "レイアウトの id が一覧に無い"),
    ("一覧が無いレイアウトを通す", "            if listed is None:", "            if False:", "レイアウトだけあって一覧が無い"),
    ("帳票名を照らさない", "            if rid in names and names[rid][0] != name:", "            if False:", "帳票名が違う"),
    ("権限の 1 列目を見ない", "    if not header or header[0] != ROLES_FIRST or len(header) < 2:", "    if not header or len(header) < 2:", "権限の 1 列目が違う"),
    ("ロールの重複を見ない", "        if role.strip() in roles:", "        if False:", "権限のロールの重複"),
    ("空のロール名を未決定に数える", "        if not role.strip():\n", "        if False:\n", "権限のロール名が空"),
    ("後ろの重複を見ない", "            elif counts.get(number, 0) > 1:", "            elif False:", "種類の行の No が後ろの性能の行と重複"),
    ("権限の可否を見ない", "                    and value.strip() not in ROLES_VALUES:", "                    and False:", "権限の可否の値"),
    ("権限の列の数を見ない", "        if len(fields) != len(header):", "        if False:", "権限の列の数"),
    ("可用性の範囲を見ない", " and 0 < float(value) <= 100)", ")", "可用性が 100 を超える"),
    ("可用性の 0 を許す", " and 0 < float(value) <= 100)", " and 0 <= float(value) <= 100)", "可用性が 0"),
    ("保管期間の整数を見ない", '            if kind in ("保管期間", "バックアップ") and not POSITIVE_INTEGER.fullmatch(value):', "            if False:", "保管期間が小数"),
    ("単位を見ない", '            if cell_state(report, where, "単位", unit, False) and unit.strip() not in units:', "            if False:", "保管期間の単位"),
    ("セキュリティの単位を見ない", '        elif cell_state(report, where, "単位", unit, True):', "        elif False:", "セキュリティに単位"),
    ("種類の行の No を見ない", "            if not NFR_NUMBER.fullmatch(number):", "            if False:", "種類の行の No の形"),
    ("種類の行の No の重複を見ない", "            elif numbers.get(number) != line:", "            elif False:", "種類の行の No が性能の行と重複"),
    ("種類の行の必須を見ない", "        for column in NFR_REQUIRED:", "        for column in ():", "種類の行の根拠が空"),
    ("種類の行が無くても見出しを見る", "        if not any(len(fields) > at and fields[at].strip() in NFR_KINDS for _, fields in rows):",
     "        if False:", "種類の行の無い非機能要求の見出しは見ない"),
    ("見出しの指標の位置を使わない", '        at = header.index("指標") if "指標" in header else NFR_COLUMNS.index("指標")',
     '        at = NFR_COLUMNS.index("指標")', "非機能要求の見出しの指標の位置で種類を探す"),
    ("性能の行も種類の行として見る", '        if row["指標"].strip() in NFR_KINDS:', "        if True:", "決まりどおり"),
    ("未決定の印を見ない", "    hits = markers(value)", "    hits = []", "未決定の印"),
    ("未決定の印を値の決まりに当てる", "        report.undecided.append(f\"{where}: {column} に未決定の印（{'・'.join(hits)}）: {value.strip()!r}\")\n        return False",
     "        report.undecided.append(f\"{where}: {column} に未決定の印（{'・'.join(hits)}）: {value.strip()!r}\")", "値の決まった欄の未決定の印"),
    ("空の欄を数えない", '            report.empty.append(f"{where}: {column} が空")', "            pass", "必須の欄が空"),
    ("空でよい欄も数える", "MAY_BE_EMPTY = {\n    FEATURES: {\"関係\"},\n    IO_LAYOUT: {\"桁\"},", "MAY_BE_EMPTY = {\n    FEATURES: {\"関係\"},\n    IO_LAYOUT: set(),", "空でよい欄が空"),
    ("未決定を 0 にする", "        if self.empty or self.undecided:", "        if False:", "未決定の印"),
    ("表が無いのを止める", "        if self.violations:\n            return 1", "        if self.violations or self.missing:\n            return 1", "表が無いだけ"),
    ("読めない表を 2 にしない", "        if self.unreadable and (strict_nfr or", "        if False and (strict_nfr or", "UTF-8 でない"),
    ("単体の検査で読めない非機能要求を 2 にしない", "def check(root: Path, strict_nfr: bool = True)", "def check(root: Path, strict_nfr: bool = False)",
     "読めない非機能要求"),
    ("ファイルでないものを無い表と読む", "        if path.exists():", "        if False:", "ファイルでない"),
    # ---- 目的の表（#1154）
    ("目的の表を検査しない", "    check_purposes(root, report, context)", "    pass", "目的の表: 決まりどおり"),
    ("空にする欄の未決定の印を違反にする", "            if markers(row[column]):\n", "            if False:\n", "目的の表: 空にする欄の未決定の印"),
    ("目的の表の見出しを見ない", "    if not check_columns(report, PURPOSES, header, PURPOSES_COLUMNS):\n        return",
     "    if False:\n        return", "目的の表: 見出し"),
    ("目的の表の列の数を見ない", "        if len(fields) != len(PURPOSES_COLUMNS):", "        if False:", "目的の表: 列の数"),
    ("目的の表の id を 1 桁から許す", 'PURPOSE_ID = re.compile(r"([GK]-)[0-9]{3,}")', 'PURPOSE_ID = re.compile(r"([GK]-)[0-9]{1,}")', "目的の表: id の形"),
    ("目的の表の id の重複を見ない", "            elif value in seen:\n                report.violations.append(f\"{where}: id が",
     "            elif False:\n                report.violations.append(f\"{where}: id が", "目的の表: id の重複"),
    ("種類ごとに空にする欄を見ない", "            elif row[column].strip():\n                other", "            elif False:\n                other",
     "目的の表: 目的の行に成功の判定"),
    ("種類ごとに書く欄の空を見ない", '            if column != "機能":\n                cell_state', "            if False:\n                cell_state",
     "目的の表: 必須の欄が空"),
    ("上位が指標でも通す", "            elif value in seen:\n                report.violations.append(f\"{where}: 上位",
     "            elif False:\n                report.violations.append(f\"{where}: 上位", "目的の表: 上位が目的でない"),
    ("上位が表に無くても通す", '                report.violations.append(f"{where}: 上位 {value} が表の目的に無い")', "                pass",
     "目的の表: 上位が表に無い"),
    ("id の決まっていない行があっても上位を違反にする", "            elif pending:", "            elif False:",
     "目的の表: id の決まっていない行があれば上位は未決定"),
    ("機能一覧が無いのに書いた id を通す", '            if cell_state(report, where, "機能", value, True) and value.strip() != PURPOSE_NONE:',
     "            if False:", "目的の表: 機能一覧が無いのに機能を書く"),
    ("機能一覧が無くても機能の空を数える", 'cell_state(report, where, "機能", value, True)', 'cell_state(report, where, "機能", value, False)',
     "目的の表: 機能一覧が無ければ機能は空でよい"),
    ("機能の空を数えない", "        if not value.strip():\n            report.empty.append", "        if False:\n            report.empty.append",
     "目的の表: 機能一覧があれば機能が空は未決定"),
    ("なしの混在を見ない", "        if PURPOSE_NONE in items:", "        if False:", "目的の表: なしと id を混ぜる"),
    ("機能の id の形を見ない", "            if not FEATURE_ID.fullmatch(item):", "            if False:", "目的の表: 機能の区切り"),
    ("機能の id を機能一覧に照らさない", '                report.violations.append(f"{where}: 機能 {item} が機能一覧（{FEATURES}）に無い")', "                pass",
     "目的の表: 機能が機能一覧に無い"),
    ("一覧の未決定の id を機能の照合で見ない", "            elif features_pending:", "            elif False:", "目的の表: 一覧の id が未決定なら機能の id も未決定"),
    ("目的を測る指標を見ない", "    for goal in sorted(goals - measured):", "    for goal in []:", "目的の表: 目的を測る指標が無い"),
    ("印と並べた決まった id を結び付けに数えない", "            covered.update(item.strip() for item in value.split(PURPOSE_SEPARATOR) if item.strip() in features)\n",
     "", "目的の表: 印と並べた決まった id は結び付けに数える"),
    ("目的を指さない機能を見ない", "        for feature in sorted(features - covered):", "        for feature in []:", "目的の表: 目的を指さない機能"),
    # ---- 関係者の表（#1161）
    ("関係者の表を検査しない", "    answers = check_stakeholders(root, report)", "    answers = None", "関係者の表: 決まりどおり"),
    ("関係者の表の見出しを見ない", "    if not check_columns(report, STAKEHOLDERS, header, STAKEHOLDERS_COLUMNS):\n        return None",
     "    if False:\n        return None", "関係者の表: 見出し"),
    ("関係者の表の列の数を見ない", "        if len(fields) != len(STAKEHOLDERS_COLUMNS):", "        if False:", "関係者の表: 列の数"),
    ("関係者の表の id を 1 桁から許す", 'STAKEHOLDER_ID = re.compile(r"P-[0-9]{3,}")', 'STAKEHOLDER_ID = re.compile(r"P-[0-9]{1,}")', "関係者の表: id の形"),
    ("関係者の表の id の重複を見ない", "            elif value in ids:", "            elif False:", "関係者の表: id の重複"),
    ("名前の重複を見ない", "            elif name in names:", "            elif False:", "関係者の表: 名前の重複"),
    ("役割と合意の値を見ない", "                if item not in allowed:", "                if False:", "関係者の表: 役割の値"),
    ("役割になしを許す", '("役割", STAKEHOLDER_ROLES, None)', '("役割", STAKEHOLDER_ROLES, STAKEHOLDER_NONE)', "関係者の表: 役割になしを書く"),
    ("同じ値の重ねを見ない", "            if len(set(items)) != len(items):", "            if False:", "関係者の表: 役割の重ね"),
    ("合意のなしの混在を見ない", "            if none is not None and none in items:", "            if False:", "関係者の表: 合意になしとほかを混ぜる"),
    ("関心事の空を数えない", '        cell_state(report, where, "関心事", row["関心事"], False)', '        cell_state(report, where, "関心事", row["関心事"], True)',
     "関係者の表: 必須の欄が空"),
    ("回答者を照らさない", "        check_respondents(root, report, answers)", "        pass", "回答者: 表に無い"),
    ("答える範囲のなしを見ない", "        elif not answers[who]:", "        elif False:", "回答者: 答える範囲がなし"),
    ("読めない回答者を名指ししない", "        if who is None:", "        if False:", "回答者: 括弧から読めない"),
    ("未回答と暫定も照らす", "        if answer == qa.NO_ANSWER or qa.is_provisional(row):", "        if False:", "回答者: 未回答と暫定は見ない"),
    ("範囲が未決定の人を答えない人に数える", '            answers[name] = not (scope and row["答える範囲"].strip() == STAKEHOLDER_NONE)',
     '            answers[name] = scope and row["答える範囲"].strip() != STAKEHOLDER_NONE', "回答者: 範囲が未決定の人は答える人に数える"),
    ("違反のある表で照らす", "    return answers if len(report.violations) == before else None", "    return answers", "回答者: 表が決まりに反するなら照らさない"),
    ("Q&A 表の見出しを見ない", "    if not rows or rows[0] != qa.COLUMNS:", "    if not rows:", "回答者: Q&A 表の見出しが違えば照らさない"),
    ("名前の文字を見ない", "            if used:\n", "            if False:\n", "関係者の表: 名前に区切りの文字"),
    ("名前の括弧を見ない", 'STAKEHOLDER_NAME_FORBIDDEN = ("・", "（", "）")', 'STAKEHOLDER_NAME_FORBIDDEN = ("・",)', "関係者の表: 名前に括弧"),
    ("Q&A 表の CSV の誤りを報告に寄せない", "    except csv.Error as e:\n        # 128KB", "    except ValueError as e:\n        # 128KB",
     "回答者: Q&A 表の巨大なセルでも終了コードを変えない"),
    ("回答者の照合を終了コードに数える", "        if self.empty or self.undecided:", "        if self.empty or self.undecided or self.respondents:", "回答者: 表に無い"),
]

# -OO（docstring が無い）で引数なしに呼んでも、使い方の誤りとして 2（#286）。(名前, 壊す前, 壊した後)
OO_MUTATIONS = [("-OO で docstring が無いと落ちる", "__doc__.splitlines()[2] if __doc__ else", "__doc__.splitlines()[2] if True else")]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def run_one(scripts: Path, root: Path, files: dict, args: list[str] | None) -> tuple[int, str]:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if body == "<dir>":
            path.mkdir()
        elif isinstance(body, bytes):
            path.write_bytes(body)
        else:
            path.write_text(body, encoding="utf-8")
    argv = [str(root)] if args is None else args
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), *argv], capture_output=True, text=True, cwd=root)
    return proc.returncode, proc.stdout + proc.stderr


def run_all(scripts: Path, work: Path, only: str | None = None) -> dict[str, tuple[int, str]]:
    return {name: run_one(scripts, work / f"case{i}", files, args) for i, (name, files, args, _, _, _) in enumerate(CASES)
            if only is None or name == only}


def as_expected(name: str, result: tuple[int, str]) -> bool:
    _, _, _, code, text, absent = next(case for case in CASES if case[0] == name)
    return result[0] == code and text in result[1] and not (absent and absent in result[1]) and "Traceback" not in result[1]


def oo_problems(scripts: Path, cwd: Path) -> list[str]:
    proc = subprocess.run([sys.executable, "-I", "-OO", str(scripts / TARGET)], capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 2 or "usage:" not in proc.stderr or "Traceback" in proc.stderr:
        return [f"-OO の引数なし: 終了 {proc.returncode}: {proc.stderr[-300:]!r}"]
    return []


def section(markdown: str, heading: str) -> str:
    """`heading` で始まる見出しの行から、次の同じか上の水準の見出しまで。"""
    level = len(heading) - len(heading.lstrip("#"))
    start = markdown.index(heading)
    rest = markdown[start + len(heading):]
    found = re.search(rf"^#{{1,{level}}} ", rest, flags=re.MULTILINE)
    return rest[:found.start()] if found else rest


def rows_of(text: str) -> list[list[str]]:
    """表の本文の行（見出しと区切りを除く）のセル。1 列目がバッククォートで囲まれた行だけ。"""
    return [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in text.splitlines() if re.match(r"^\| `[^`]+` \|", line)]


def constant(source: str, name: str):
    found = re.search(rf"^{name} = (.+)$", source, flags=re.MULTILINE)
    return ast.literal_eval(found.group(1)) if found else None


def reference_mismatches(module, tree: str, nfr_md: str) -> list[str]:
    """本体の定数が references の表と一致するか（写しのずれ）。`module` は読み込んだ本体。"""
    problems = []
    design = section(tree, "## システム設計書の成果物")
    for rel, columns in module.COLUMNS.items():
        heading = next((line for line in design.splitlines() if line.startswith("### ") and f"（`{rel}`）" in line), None)
        if heading is None:
            problems.append(f"{rel}: tree.md に節が無い")
            continue
        rows = rows_of(section(design, heading))
        names = [row[0].strip("`") for row in rows]
        if names != columns:
            problems.append(f"{rel}: 列が違う（tree.md {names} ／ 本体 {columns}）")
            continue
        if any(len(row) != 3 or row[2] not in ("利用者", "連携先") for row in rows):
            problems.append(f"{rel}: 「決める人」の列が利用者か連携先でない行がある")
        empty = {row[0].strip("`") for row in rows if "空でよい" in row[1]}
        if empty != module.MAY_BE_EMPTY.get(rel, set()):
            problems.append(f"{rel}: 空でよい列が違う（tree.md {sorted(empty)} ／ 本体 {sorted(module.MAY_BE_EMPTY.get(rel, set()))}）")
        for row in rows:
            column = row[0].strip("`")
            listed = re.match(r"^((?:`[^`]+`・)+`[^`]+`)(?: の(?:どれか|どちらか))?(?:。|$)", row[1])
            values = tuple(re.findall(r"`([^`]+)`", listed.group(1))) if listed else None
            if values != module.VALUES.get((rel, column)):
                problems.append(f"{rel} の {column}: 決まった値が違う（tree.md {values} ／ 本体 {module.VALUES.get((rel, column))}）")
            prefix = re.match(r"^`([A-Z]+-)` に 3 桁以上の数字", row[1])
            if (prefix.group(1) if prefix else None) != (module.ID_PREFIX.get(rel) if column == "id" else None):
                problems.append(f"{rel} の {column}: 番号の接頭辞が違う（tree.md {prefix and prefix.group(1)} ／ 本体 {module.ID_PREFIX.get(rel)}）")
    roles = next((line for line in design.splitlines() if line.startswith("### ") and f"（`{module.ROLES}`）" in line), None)
    if roles is None:
        problems.append(f"{module.ROLES}: tree.md に節が無い")
    else:
        body = section(design, roles)
        if f"1 列目の見出しは `{module.ROLES_FIRST}`" not in body:
            problems.append(f"権限一覧の 1 列目（{module.ROLES_FIRST}）が tree.md に無い")
        if "・".join(f"`{v}`" for v in module.ROLES_VALUES) + " のどちらか" not in body:
            problems.append(f"権限一覧のセルの値（{module.ROLES_VALUES}）が tree.md と違う")
    tables = [rel for line in design.splitlines() if line.startswith("### ")
              for rel in re.findall(r"（`((?:requirements|shared)/[^`]+\.csv)`）", line)]
    if sorted(tables) != sorted(module.ALL_TABLES):
        problems.append(f"成果物の表の一覧が違う（tree.md {sorted(tables)} ／ 本体 {sorted(module.ALL_TABLES)}）")
    problems += purpose_mismatches(module, design)
    problems += stakeholder_mismatches(module, design)
    kinds = {}
    for row in rows_of(section(nfr_md, "## 性能のほかの種類"))[1:]:  # 1 行目は見出し（`指標`・`上限`・`単位`）
        kinds[row[0].strip("`")] = () if row[2] == "空にする" else tuple(re.findall(r"`([^`]+)`", row[2]))
    if kinds != module.NFR_KINDS:
        problems.append(f"非機能要求の種類が違う（nfr.md {kinds} ／ 本体 {module.NFR_KINDS}）")
    columns = [row[0].strip("`") for row in rows_of(section(nfr_md, "## 列").split("\n### ", 1)[0])]
    if columns != module.NFR_COLUMNS:
        problems.append(f"非機能要求の列が違う（nfr.md {columns} ／ 本体 {module.NFR_COLUMNS}）")
    return problems


def purpose_mismatches(module, design: str) -> list[str]:
    """目的の表（#1154）の定数が tree.md の「目的と成功の判定」と一致するか。"""
    heading = next((line for line in design.splitlines() if line.startswith("### ") and f"（`{module.PURPOSES}`）" in line), None)
    if heading is None:
        return [f"{module.PURPOSES}: tree.md に節が無い"]
    body = section(design, heading)
    rows = rows_of(body)
    problems = []
    names = [row[0].strip("`") for row in rows]
    if names != module.PURPOSES_COLUMNS:
        return [f"{module.PURPOSES}: 列が違う（tree.md {names} ／ 本体 {module.PURPOSES_COLUMNS}）"]
    if any(len(row) != 3 or row[2] != "利用者" for row in rows):
        problems.append(f"{module.PURPOSES}: 「決める人」が利用者でない行がある")
    kinds = dict(re.findall(r"(目的|指標)は `([A-Z]+-)`", rows[0][1]))
    if {prefix: kind for kind, prefix in kinds.items()} != module.PURPOSE_KINDS:
        problems.append(f"{module.PURPOSES}: id の接頭辞と種類が違う（tree.md {kinds} ／ 本体 {module.PURPOSE_KINDS}）")
    own = {prefix: tuple(row[0].strip("`") for row in rows if row[1].startswith(f"{kind}の行だけ"))
           for prefix, kind in module.PURPOSE_KINDS.items()}
    if own != module.PURPOSE_OWN:
        problems.append(f"{module.PURPOSES}: 種類ごとに書く列が違う（tree.md {own} ／ 本体 {module.PURPOSE_OWN}）")
    feature = rows[-1][1]
    if f"`{module.PURPOSE_SEPARATOR}` で区切って" not in feature or f"`{module.PURPOSE_NONE}` とだけ書く" not in feature:
        problems.append(f"{module.PURPOSES}: 機能 の区切り（{module.PURPOSE_SEPARATOR}）か動かさない値（{module.PURPOSE_NONE}）が tree.md と違う")
    return problems


def stakeholder_mismatches(module, design: str) -> list[str]:
    """関係者の表（#1161）の定数が tree.md の「関係者の表」と一致するか。"""
    heading = next((line for line in design.splitlines() if line.startswith("### ") and f"（`{module.STAKEHOLDERS}`）" in line), None)
    if heading is None:
        return [f"{module.STAKEHOLDERS}: tree.md に節が無い"]
    rows = {row[0].strip("`"): row for row in rows_of(section(design, heading))}
    if list(rows) != module.STAKEHOLDERS_COLUMNS:
        return [f"{module.STAKEHOLDERS}: 列が違う（tree.md {list(rows)} ／ 本体 {module.STAKEHOLDERS_COLUMNS}）"]
    problems = []
    if any(len(row) != 3 or row[2] != "利用者" for row in rows.values()):
        problems.append(f"{module.STAKEHOLDERS}: 「決める人」が利用者でない行がある")
    prefix = re.match(r"^`([A-Z]+-)` に 3 桁以上の数字", rows["id"][1])
    if not prefix or module.STAKEHOLDER_ID.pattern != prefix.group(1) + "[0-9]{3,}":
        problems.append(f"{module.STAKEHOLDERS}: id の形が違う（tree.md {prefix and prefix.group(1)} ／ 本体 {module.STAKEHOLDER_ID.pattern}）")
    roles = re.match(r"^((?:`[^`]+`・)+`[^`]+`) のどれか", rows["役割"][1])
    if tuple(re.findall(r"`([^`]+)`", roles.group(1)) if roles else ()) != module.STAKEHOLDER_ROLES:
        problems.append(f"{module.STAKEHOLDERS}: 役割の値が違う（本体 {module.STAKEHOLDER_ROLES}）")
    if tuple(re.findall(r"`([^`]+)`（", rows["合意"][1])) != module.STAKEHOLDER_AGREEMENTS:
        problems.append(f"{module.STAKEHOLDERS}: 合意の値が違う（tree.md {re.findall(r'`([^`]+)`（', rows['合意'][1])} ／ 本体 {module.STAKEHOLDER_AGREEMENTS}）")
    separator = f"`{module.STAKEHOLDER_SEPARATOR}` で区切って"
    if separator not in rows["役割"][1] or separator not in rows["合意"][1]:
        problems.append(f"{module.STAKEHOLDERS}: 区切り（{module.STAKEHOLDER_SEPARATOR}）が tree.md と違う")
    if "・".join(f"`{char}`" for char in module.STAKEHOLDER_NAME_FORBIDDEN) + " を使わない" not in rows["名前"][1]:
        problems.append(f"{module.STAKEHOLDERS}: 名前に使わない文字（{module.STAKEHOLDER_NAME_FORBIDDEN}）が tree.md と違う")
    if f"要らないなら `{module.STAKEHOLDER_NONE}`" not in rows["合意"][1] or f"答えないなら `{module.STAKEHOLDER_NONE}`" not in rows["答える範囲"][1]:
        problems.append(f"{module.STAKEHOLDERS}: 無いことの値（{module.STAKEHOLDER_NONE}）が tree.md と違う")
    return problems


# references を崩すと不一致になる（突き合わせが空振りでないこと）。(名前, ファイル, 崩す前, 崩した後)
REFERENCE_MUTATIONS = [
    ("機能一覧の列を消す", "tree", "| `関係` | 関係する画面", "| 関係 | 関係する画面"),
    ("種類の値を足す", "tree", "`画面`・`API`・`バッチ`・`ファイル連携` のどれか", "`画面`・`API`・`バッチ`・`ファイル連携`・`帳票` のどれか"),
    ("空でよいを外す", "tree", "決まらない形式なら空でよい", "決まらない形式なら書かない"),
    ("決める人を崩す", "tree", "| `相手` | 誰と（どのシステム・部署と）やり取りするか | 連携先 |", "| `相手` | 誰と（どのシステム・部署と）やり取りするか | 開発者 |"),
    ("接頭辞を変える", "tree", "| `id` | `J-` に 3 桁以上の数字", "| `id` | `JOB-` に 3 桁以上の数字"),
    ("権限の値を変える", "tree", "セルは `可`・`不可` のどちらか", "セルは `○`・`×` のどちらか"),
    ("目的の表の列を消す", "tree", "| `機能` | 指標の行だけ", "| 機能 | 指標の行だけ"),
    ("目的の表の接頭辞を変える", "tree", "目的は `G-`、指標は `K-`", "目的は `P-`、指標は `K-`"),
    ("目的の表の種類ごとの列を変える", "tree", "| `上位` | 指標の行だけ", "| `上位` | 目的の行だけ"),
    ("目的の表の区切りを変える", "tree", "`・` で区切って並べる（`F-001・F-003`）", "`,` で区切って並べる（`F-001・F-003`）"),
    ("目的の表の決める人を崩す", "tree", "の `id` を `・` で区切って並べる（`F-001・F-003`）。システムの機能では動かさない指標（業務の手順で動かす）は `なし` とだけ書く。目的の行は空にする | 利用者 |",
     "の `id` を `・` で区切って並べる（`F-001・F-003`）。システムの機能では動かさない指標（業務の手順で動かす）は `なし` とだけ書く。目的の行は空にする | 開発者 |"),
    ("関係者の表の列を消す", "tree", "| `関心事` | その関係者", "| 関心事 | その関係者"),
    ("関係者の表の接頭辞を変える", "tree", "| `id` | `P-` に 3 桁以上の数字（`P-001`）", "| `id` | `S-` に 3 桁以上の数字（`S-001`）"),
    ("関係者の表の役割を足す", "tree", "`利用者`・`予算責任者`・`決裁者`・`連携先` のどれか", "`利用者`・`予算責任者`・`決裁者`・`連携先`・`開発者` のどれか"),
    ("関係者の表の合意を変える", "tree", "`決裁`（提案書の決裁）", "`発注`（提案書の決裁）"),
    ("関係者の表の区切りを変える", "tree", "を `・` で区切って並べる（`利用者・決裁者`）", "を `,` で区切って並べる（`利用者・決裁者`）"),
    ("関係者の表のなしを変える", "tree", "要らないなら `なし`", "要らないなら `無し`"),
    ("関係者の表の名前の文字を変える", "tree", "`・`・`（`・`）` を使わない", "`・` を使わない"),
    ("関係者の表の決める人を崩す", "tree", "答えないなら `なし` | 利用者 |", "答えないなら `なし` | 開発者 |"),
    ("非機能要求の単位を変える", "nfr", "| `保管期間` | 正の整数（`7`） | `日`・`月`・`年` のどれか |", "| `保管期間` | 正の整数（`7`） | `日`・`年` のどれか |"),
]


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def load(path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_design_csv_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    with tempfile.TemporaryDirectory(prefix="design-csv-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        for name, result in run_all(scripts, tmp_path / "work").items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result[0]} {result[1][-400:]}")

        module = load(scripts / TARGET)
        tree = TREE.read_text(encoding="utf-8")
        nfr_md = NFR_REF.read_text(encoding="utf-8")
        problems = reference_mismatches(module, tree, nfr_md)
        check("本体の定数が references と一致しない", not problems, "; ".join(problems))
        for name, which, before, after in REFERENCE_MUTATIONS:
            text = tree if which == "tree" else nfr_md
            if text.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {text.count(before)} 回現れる")
                continue
            broken = text.replace(before, after)
            mismatches = reference_mismatches(module, broken, nfr_md) if which == "tree" else reference_mismatches(module, tree, broken)
            check(f"崩すと不一致になる: {name}", bool(mismatches))

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            result = run_all(mutated, tmp_path / f"mutwork{index}", only=killer)[killer]
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result[1][-300:])

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
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(OO_MUTATIONS)} 件・references の崩し {len(REFERENCE_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
