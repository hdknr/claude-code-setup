#!/usr/bin/env python3
"""システム設計書の成果物の表（目的と成功の判定・機能一覧・データモデル・機能とデータの対応（CRUD）・入出力・帳票・権限・バッチ・ジョブ・移行・テスト要件と、非機能要求の性能のほかの種類）と関係者の表・用語集を検査する。

usage: python3 check-design-csv.py <版のディレクトリ（docs/v<n>）か重ね合わせた全体（build/merged）>

**決まりの正は `references/tree.md` の「システム設計書の成果物」（関係者の表・用語集を含む）と `references/nfr.md` の「性能のほかの種類」である**（このプラグインの中にある）。
下の定数（表の置き場所・列・空でよい列・決まった値・番号の形・重複させない欄・権限一覧の形・非機能要求の種類・関係者の表の列と決まった値・用語集の列と日付の形と使わない言い方を探す範囲・
CRUD 表の列と操作の文字と `なし` と抜けに数える操作・移行の表の列と種類と種類ごとに書く列と切替の方式と `なし`・テスト要件の表の列と段と確かめ方と確かめ方ごとに書く列と受入の人の行）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-check-design-csv.py` が突き合わせて見る**。

渡したディレクトリの `requirements/` と `shared/nfr.csv`・`shared/stakeholders.csv`・`shared/glossary.csv` を読み、見つけたものを **4 つに分けて**出す（#957）:

- **形式の違反**——見出しの行が決まりと違う（順・綴り・列の過不足。物理設計の列を足した表もここ）・列の数・番号の形・重複・
  決まった値でない・レイアウトの id が入出力の一覧に無い・同じ帳票の id で帳票名が違う・非機能要求の種類の上限と単位の形・
  目的の表（#1154）の種類ごとに空にする欄に書いた（未決定の印なら未決定に数える）・指標の `上位` が表の目的でない・指標の `機能` の id が機能一覧に無い（一覧が無いときも）・`なし` と id を混ぜた・
  関係者の表（#1161）の名前の重複・役割と合意の値が決まった値でない・同じ値を重ねた・合意に `なし` とほかの値を混ぜた・
  用語集（#1164）の用語の重複・使わない言い方が表の用語と同じ・同じ行で重ねた・区切りで空の項・決めた日が `YYYY-MM-DD` の実在する日付でない・
  CRUD 表（#1162）の機能が機能一覧の id でも `なし` でもない・機能一覧に無い（一覧が無いときも）・エンティティがデータモデルに無い（データモデルが無いときも）・
  操作が `C`・`R`・`U`・`D` をこの順に 1 回ずつまで並べた形でない・機能とエンティティの組の重複・同じエンティティで機能がする操作を `なし` の行にも書いた・
  移行の表（#1158）の id の形と重複・種類と切替の方式が決まった値でない・種類の外の欄に書いた（未決定の印なら未決定に数える）・`並行稼働` でない方式の行に並行稼働の期間を書いた・
  対象が `なし` の行にほかの欄を書いた・`なし` と決めた種類にほかの行がある・
  テスト要件の表（#1160）の id の形と重複・段と確かめ方が決まった値でない・確かめ方の外の欄に書いた（未決定の印なら未決定に数える）・
  機能が機能一覧の id の形でない・機能一覧に無い（一覧が無いときも）
- **表が無い**——決まりの表のうち、渡したディレクトリに無いもの。**止めない**（前からの正本は成果物の表を持たない。v2 以降の版のディレクトリは足した表しか持たない）
- **必須の欄が空**——空でよい列のほかの欄が空（要る情報がまだ無い）
- **未決定の印**——セルに `references/spec-exit.md` の未決定の印（`TBD`・`TODO`・`未定`・`要確認`）がある。
  印の判定は `check-spec-exit.py` の `find_markers` を読む（写さない）。**印のあるセルと空のセルは、値の決まりに当てない**——未決定は違反ではない。
  **目的の表の結び付けの欠け**（目的を測る指標が無い・機能一覧の機能がどの指標の `機能` にも無い——目的を指さない機能）もここに数える——
  要るかどうかは利用者が決めることで、表の形の誤りではない。
  **CRUD 表の抜け**（#1162。データモデルのエンティティを作る（`C`）・読む（`R`）機能が無い、`保管期間` が決まっているのに消す（`D`）機能が無い——
  どれも、その操作を `なし` の行で「する機能は無い」と決めていなければ）も同じ理由でここに数える。
  **移行の表の行の無い種類**（#1158。表があるのに `データ`・`切替`・`業務` のどれかの行が無い——`なし` の行で決めていない）と、切替の方式が `並行稼働` なのに期間が空も、ここに数える。
  **テスト要件の表の受入の人の行の欠け**（#1160。表があるのに、段が `受入` で確かめ方が `人` の行が無い——利用者の受け入れの観点が決まっていない）も、ここに数える

**4 つのほかに、回答者の照合を報告する（終了コードに数えない。#1161）**——関係者の表が決まりどおりで、`shared/qa.csv` があるとき、
`未回答` でも暫定でもない行の回答者（`check-qa-csv.py` の `respondent` が `回答` の括弧から読む）が、表の `名前` に無い・表で `答える範囲` が `なし`・括弧から読めない、を出す。
関係者の表が決まりに反するなら照らさず、そう出す。

**同じく、用語集の使わない言い方を報告する（終了コードに数えない。#1164）**——用語集が決まりどおりなら、渡した根の `requirements/` と `shared/` の下の
`.md`・`.csv`（用語集と `shared/qa.csv` を除く。`.` で始まる名前の下は見ない）の行に、表の `使わない言い方` が現れたら `<パス>:<行>` で出す。
**その使わない言い方を含む用語（`受注` に対する `受注伝票`）の中の出現は出さない。** 用語集が決まりに反するなら探さず、そう出す。

**v2 以降は重ね合わせた全体（`merge-versions.py docs build/merged`）に当てる**——版のディレクトリは足した・変えた表しか持たない。

**非機能要求（`shared/nfr.csv`）は、`指標` が性能のほかの種類（可用性・保管期間・バックアップ・セキュリティ）の行だけを見る**
（見出しの行は、種類の行が 1 つでもあるときだけ見る——種類の行は見出しの `指標` の位置で探す）。**性能の行とほかの語の行は見ない**——性能の行は `scaffold.py` が中間表現から指された行だけを見る（`references/nfr.md`）。

終了コード:

- 0: 形式の違反も、必須の欄の空も、未決定の印も無い（**表が無いことは出すが 0**）
- 1: 形式の違反がある（ほかの 3 つも併せて出す）
- 3: 形式の違反は無いが、必須の欄が空か未決定の印がある——**要る情報がまだ決まっていない**。scaffold はこれでも止まる
- 2: 判定していない——引数の誤り・ディレクトリが無い・表が読めない（UTF-8 でない・空のファイル・権限など）・想定外の例外

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **欄の中身**（意味の書き方・保管期間が業務に合うか・ロールの切り方） | 判断であって、一意に決まらない |
| **帳票の見本・ER 図があるか** | 見本は HTML か PDF、図は drawio で、表の検査の外（図の鮮度は `render-diagrams.py --check`） |
| **表どうしの整合**（データモデルの項目と入出力の項目が合うか・権限一覧の操作が機能一覧にあるか） | 名前の付け方が表ごとに違ってよく、機械で対応を決められない。**例外は id と鍵で指す 4 つだけ**——入出力のレイアウトの id（一覧に無い id は落とす）と、目的の表の指標の `機能`（機能一覧の id と照らす）と、CRUD 表の `機能`・`エンティティ`（機能一覧の id とデータモデルのエンティティと照らす）と、テスト要件の表の `機能`（機能一覧の id と照らす）。Q&A 表の回答者と関係者の表の名前の照合は報告で、終了コードに数えない（下の行） |
| **権限一覧の操作と、機能が触るデータの食い違い**（CRUD 表で消さない機能に、権限一覧で消す操作を許している、など） | 権限一覧の `操作` は名前で書き、機能一覧の id を持たないので、CRUD 表の行と機械で結べない。spec-review の Formal Checker が権限・ロールを対象に選んだとき、権限一覧と並べて CRUD 表を入力に渡す（`references/tree.md` の「機能とデータの対応」） |
| **CRUD 表の更新（`U`）の抜け・どのデータも触らない機能** | 作った後に変えないデータ（履歴・記録）も、データを持たない機能（外部の呼び出しだけ・画面の切り替えだけ）もふつうにある。抜けに数えるのは作る・読む・消す（保管期間が決まっているとき）だけ |
| **CRUD 表の粒度より細かい対応**（エンティティのどの項目を作る・更新するか） | 表は機能 × エンティティの粒度で、項目を持たない（`references/tree.md` の「機能とデータの対応」） |
| **移行の表とほかの表の整合**（移行元と入出力の一覧の `相手`・データの行とデータモデルのエンティティ・切替の行と業務の行の対応） | 名前の付け方と切り方が違う（旧システムのデータは名寄せ・分割で 1 対多になる）。`references/tree.md` の「移行」 |
| **テスト要件の表とほかの表の整合**（観点と決定表の行・使うデータとデータモデル・移行のリハーサルの行と移行の表・担当と関係者の表の名前）と、**自動の行の `テストケース` が仕様にあるか** | 名前の付け方と切り方が違う。テストケースの番号の振り方は仕様に任されている（`references/spec-exit.md` の「仕様の規模」）。照らすのは `機能` の id だけ（`references/tree.md` の「テスト要件」） |
| **テスト要件の表の欄の中身**（観点が十分か・合格の条件が具体的か・期間が現実的か・期間の形）と、**`確かめ方` の決まっていない行の確かめ方ごとの欄** | 中身は判断で、一意に決まらない。期間の形は決めていない。`確かめ方` が決まらない行はどちらの行か決まらないので、確かめ方ごとの欄を判定しない |
| **テスト要件の表と仕様レビューを抜ける条件** | つながない——抜ける条件は仕様（`spec/`）が確定したかを見るもので、受入の合格は実装の後に人が判定する。表の未決定は scaffold の関門が 3 で止める（`references/tree.md` の「テスト要件」） |
| **移行の表の欄の中身**（範囲が十分か・切り戻しの条件が具体的か）と、**`対象` の決まっていない行の種類ごとの欄** | 中身は判断で、一意に決まらない。`対象` が決まらない行は `なし` の行かどうか決まらないので、種類ごとの欄を判定しない（`対象` は未決定に出る） |
| **目的に照らした過不足の中身**（`機能` に載った機能が本当にその指標を動かすか・目的の切り方が正しいか） | 判断であって、一意に決まらない。spec-review の Domain Checker が目的の表を照合先にして見る。ここは結び付けの有無と id の実在だけ |
| **回答者が答えた質問が、その人の答える範囲の中か** | 範囲は自由に書く（分野・機能・目的の id）ので、質問との対応を機械で決められない。req-loop が回答を反映するときに確かめる（`references/tree.md` の「関係者の表」）。照らすのは名前と `なし` だけで、**終了コードにも数えない**——表を置く前の回答（凍結した版を含む）は書き直せない |
| **関係者の表の名前が個人名でないか・非公式の影響力を書いていないか** | 書き方の判断で、文字列からは決まらない |
| **使わない言い方が、文脈で要る形で現れたか**（引用・「注文とは呼ばない」の説明）・**ほかの語の中の出現**（`注文書` の中の `注文`） | 日本語には語の区切りが無く、文字列の一致では決まらない。だから報告だけで、終了コードに数えない（`references/tree.md` の「用語集」）。除くのは用語集の用語の中の出現だけ |
| **用語の意味が要求・仕様の使い方と合うか** | 判断であって、一意に決まらない。spec-review の Red Team が「文書どうしの定義」で用語集を基準に見る（`references/spec-exit.md`） |
| **用語集の `決めた人` が関係者の表の名前か** | 関係者の表は任意で、照らす相手が無いことがある。書き方は `references/tree.md` の「用語集」 |
| **型・API の英語名と用語の対応** | 英語名は用語集に置かない（開発者が内部の Q&A 表に記録する。`references/tree.md` の「用語集」）。照らす相手が表に無い |
| **入出力の一覧の `相手` と関係者の表の対応** | 相手はシステムの名前、関係者は部署・役職で、名前の付け方が違う |
| **機能一覧と中間表現の機能の対応** | このスクリプトは中間表現を読まない。`scaffold.py` が関門で照らす（`listed_features` を読む） |
| **印を使わずに書いた未決定**（「あとで決める」） | 言い回しは列挙しきれない。`check-spec-exit.py` と同じ限界 |
| **非機能要求の性能の行・ほかの語の行・種類の語の綴りの揺れ**（`稼働率` と書いた行） | 上のとおり見ない。種類は `指標` の語が 4 つのどれかと一致する行だけ |
| **綴りだけ違う置き場所**（`Requirements/features.csv`） | 決まりの綴りで探し、無ければ「表が無い」と出す。大文字小文字を区別しないファイルシステムでは開けてしまう |
"""

from __future__ import annotations

import csv
import datetime
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 未決定の印の判定は `check-spec-exit.py` のもの（写さない）
spec_exit = _load("check_spec_exit", "check-spec-exit.py")
# Q&A 表の列・「まだ無い」の印・暫定の行の判別・回答の括弧から答えた人を読む関数は `check-qa-csv.py` のもの（写さない。#1161）
qa = _load("check_qa_csv", "check-qa-csv.py")

# ---- `references/tree.md` の「システム設計書の成果物」の写し
FEATURES = "requirements/features.csv"
ENTITIES = "requirements/entities.csv"
IO_LIST = "requirements/io.csv"
IO_LAYOUT = "requirements/io-layout.csv"
REPORTS = "requirements/reports.csv"
JOBS = "requirements/jobs.csv"
ROLES = "requirements/roles.csv"
PURPOSES = "requirements/purposes.csv"
NFR = "shared/nfr.csv"
# 置き場所（版の根から）→ 見出しの行
COLUMNS = {
    FEATURES: ["id", "名前", "種類", "関係"],
    ENTITIES: ["エンティティ", "項目", "意味", "型", "必須", "保管期間"],
    IO_LIST: ["id", "名前", "向き", "相手", "形式", "文字コード", "区切り", "ヘッダー", "契機"],
    IO_LAYOUT: ["id", "順番", "項目", "型", "桁", "必須", "意味"],
    REPORTS: ["id", "帳票名", "順番", "項目", "意味", "書式"],
    JOBS: ["id", "名前", "契機", "周期", "失敗したときの扱い"],
}
# 空でよい列（ほかの列が空なら「必須の欄が空」）
MAY_BE_EMPTY = {
    FEATURES: {"関係"},
    IO_LAYOUT: {"桁"},
    REPORTS: {"書式"},
}
YES_NO = ("はい", "いいえ")
# (表, 列) → 決まった値
VALUES = {
    (FEATURES, "種類"): ("画面", "API", "バッチ", "ファイル連携"),
    (ENTITIES, "必須"): YES_NO,
    (IO_LIST, "向き"): ("入力", "出力"),
    (IO_LIST, "ヘッダー"): ("あり", "なし"),
    (IO_LAYOUT, "必須"): YES_NO,
}
# 表 → 番号の接頭辞（`<接頭辞>` に 3 桁以上の数字。`F-` は中間表現の機能の `id` と同じ形——`references/spec-ir.md`）
ID_PREFIX = {FEATURES: "F-", IO_LIST: "IO-", REPORTS: "RP-", JOBS: "J-"}
# 表 → 重ねてはならない欄の組
UNIQUE = {
    FEATURES: ("id",),
    ENTITIES: ("エンティティ", "項目"),
    IO_LIST: ("id",),
    IO_LAYOUT: ("id", "順番"),
    REPORTS: ("id", "順番"),
    JOBS: ("id",),
}
# 目的の表（`references/tree.md` の「目的と成功の判定」。#1154）: 見出しの行・id の接頭辞 → 種類・種類ごとに書く列
# （`id`・`内容` はどちらの種類も書く。ここに無い列は、その種類では空にする）・`機能` の区切りと「動かす機能が無い」の値
PURPOSES_COLUMNS = ["id", "上位", "誰の課題か", "内容", "成功の判定", "機能"]
PURPOSE_KINDS = {"G-": "目的", "K-": "指標"}
PURPOSE_OWN = {"G-": ("誰の課題か",), "K-": ("上位", "成功の判定", "機能")}
PURPOSE_ID = re.compile(r"([GK]-)[0-9]{3,}")
PURPOSE_SEPARATOR = "・"
PURPOSE_NONE = "なし"
FEATURE_ID = re.compile(r"F-[0-9]{3,}")
# 順番の列（正の整数）
ORDER_COLUMN = "順番"
# データモデルのエンティティ名と保管期間の列（CRUD 表がエンティティ名で指し、保管期間が決まっていれば消す機能を求める。#1162）
ENTITY_COLUMN = "エンティティ"
RETENTION_COLUMN = "保管期間"
# 権限一覧: 1 列目の名前と、ロールの列のセルの値
ROLES_FIRST = "操作"
ROLES_VALUES = ("可", "不可")
# 関係者の表（`references/tree.md` の「関係者の表」。#1161）: 見出しの行・id の形・役割と合意の決まった値・区切り・「無い」の値
STAKEHOLDERS = "shared/stakeholders.csv"
STAKEHOLDERS_COLUMNS = ["id", "名前", "役割", "関心事", "答える範囲", "合意"]
STAKEHOLDER_ID = re.compile(r"P-[0-9]{3,}")
STAKEHOLDER_ROLES = ("利用者", "予算責任者", "決裁者", "連携先")
STAKEHOLDER_AGREEMENTS = ("要求確定", "予算", "決裁")
STAKEHOLDER_SEPARATOR = "・"
STAKEHOLDER_NONE = "なし"
# 名前に使わない文字——承認の行の区切り（`・`）と、回答の括弧（`（`・`）`）で名前を読めなくなる
STAKEHOLDER_NAME_FORBIDDEN = ("・", "（", "）")
# 回答者の照合の報告の見出し（scaffold の関門が、通ったときにもこの見出しから後ろを出す）
RESPONDENT_HEADING = "回答者の照合（終了コードに数えない。"
# 回答者を照らす Q&A 表（共有の表だけ。内部の表は開発者が決める）
QA_TABLE = "shared/qa.csv"
# 用語集（`references/tree.md` の「用語集」。#1164）: 見出しの行・空でよい列・`使わない言い方` の区切り・決めた日の形
GLOSSARY = "shared/glossary.csv"
GLOSSARY_COLUMNS = ["用語", "意味", "使わない言い方", "決めた人", "決めた日"]
GLOSSARY_MAY_BE_EMPTY = ("使わない言い方",)
GLOSSARY_SEPARATOR = "・"
GLOSSARY_DATE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
# 使わない言い方を探す文書: 根からのディレクトリ・拡張子・除くファイル（用語集そのものと、利用者の言葉を残す共有の Q&A 表）
USAGE_DIRS = ("requirements", "shared")
USAGE_SUFFIXES = (".md", ".csv")
USAGE_EXCLUDE = (GLOSSARY, QA_TABLE)
# 使わない言い方の報告の見出し（回答者の照合と同じく、scaffold の関門が通ったときにも出す）
USAGE_HEADING = "用語集の使わない言い方（終了コードに数えない。"
# ---- `references/nfr.md` の写し
NFR_COLUMNS = ["No", "対象", "指標", "上限", "単位", "条件", "根拠"]
NFR_NUMBER = re.compile(r"N-[0-9]{3,}")
# 性能のほかの種類（`指標` の語）→ 単位の決まった値（空のタプルは「単位は空」）
NFR_KINDS = {
    "可用性": ("%",),
    "保管期間": ("日", "月", "年"),
    "バックアップ": ("時間", "日"),
    "セキュリティ": (),
}
# 種類の行で空にしない列（上限・単位は種類ごとに下で見る）
NFR_REQUIRED = ("対象", "条件", "根拠")
POSITIVE_INTEGER = re.compile(r"[1-9][0-9]{0,8}")
PERCENT = re.compile(r"(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,6})?")

# 機能とデータの対応（CRUD 表。`references/tree.md` の「機能とデータの対応」。#1162）: 見出しの行・操作の文字（この順に 1 回ずつまで）・
# 「その操作をする機能は無い」と決めた行の機能の値・抜けに数える操作（`D` は保管期間が決まっているエンティティだけ）
CRUD = "requirements/crud.csv"
CRUD_COLUMNS = ["機能", "エンティティ", "操作"]
CRUD_OPERATIONS = ("C", "R", "U", "D")
CRUD_OPERATION = re.compile("".join(f"(?:{op})?" for op in CRUD_OPERATIONS))
CRUD_NONE = "なし"
CRUD_GAPS = {"C": "作る", "R": "読む", "D": "消す"}
CRUD_KEPT = "D"

# 移行の表（`references/tree.md` の「移行」。#1158）: 見出しの行・id の形・種類・種類ごとに書く列（どの行も書く列のほか）・切替の方式・
# 並行稼働の期間を求める方式・「移すもの・することは無い」と決めた行の対象の値
MIGRATION = "requirements/migration.csv"
MIGRATION_COLUMNS = ["id", "種類", "移行元", "対象", "範囲", "変換の決まり", "切替の方式", "並行稼働の期間", "切り戻しの条件", "担当"]
MIGRATION_ID = re.compile(r"M-[0-9]{3,}")
MIGRATION_KINDS = ("データ", "切替", "業務")
MIGRATION_COMMON = ("対象", "担当")
MIGRATION_OWN = {
    "データ": ("移行元", "範囲", "変換の決まり"),
    "切替": ("移行元", "切替の方式", "並行稼働の期間", "切り戻しの条件"),
    "業務": ("範囲",),
}
MIGRATION_METHODS = ("一斉", "段階", "並行稼働")
MIGRATION_PARALLEL = "並行稼働"
MIGRATION_PERIOD = "並行稼働の期間"
MIGRATION_NONE = "なし"

# テスト要件の表（`references/tree.md` の「テスト要件」。#1160）: 見出しの行・id の形・段・確かめ方・確かめ方ごとに書く列（どの行も書く列のほか）・
# どの行も空でよい列（`機能`。機能一覧の id を `PURPOSE_SEPARATOR` で区切る）・表があれば 1 行以上要る段と確かめ方の組
ACCEPTANCE = "requirements/acceptance.csv"
ACCEPTANCE_COLUMNS = ["id", "段", "観点", "確かめ方", "テストケース", "担当", "使うデータ", "期間", "合格の条件", "機能"]
ACCEPTANCE_ID = re.compile(r"A-[0-9]{3,}")
ACCEPTANCE_STAGES = ("総合", "受入", "移行のリハーサル")
ACCEPTANCE_WAYS = ("自動", "人")
ACCEPTANCE_COMMON = ("観点",)
ACCEPTANCE_OWN = {
    "自動": ("テストケース",),
    "人": ("担当", "使うデータ", "期間", "合格の条件"),
}
ACCEPTANCE_FEATURES = "機能"
# 確かめ方ごとに書く列のうち空でよいもの（自動の行のテストケースは、仕様のテストケースが書かれるまで空でよい）
ACCEPTANCE_MAY_BE_EMPTY = ("テストケース",)
ACCEPTANCE_REQUIRED = ("受入", "人")

ALL_TABLES = list(COLUMNS) + [PURPOSES, CRUD, MIGRATION, ACCEPTANCE, ROLES, NFR, STAKEHOLDERS, GLOSSARY]


class Report:
    def __init__(self) -> None:
        self.violations: list[str] = []
        self.missing: list[str] = []
        self.empty: list[str] = []
        self.undecided: list[str] = []
        self.unreadable: list[str] = []
        # 回答者の照合（#1161）——終了コードに数えない報告
        self.respondents: list[str] = []
        # 用語集の使わない言い方（#1164）——終了コードに数えない報告
        self.usages: list[str] = []
        self.rows: dict[str, int] = {}

    def code(self, strict_nfr: bool = True) -> int:
        """`strict_nfr` が偽なら、読めない `shared/nfr.csv` を「判定していない」に数えない（scaffold の関門。種類の行が在るかを
        読めない表で決められず、性能の行は scaffold が指された行だけを自分で読むので、前からの扱いを変えない）。"""
        if self.unreadable and (strict_nfr or any(not item.startswith(NFR + ":") for item in self.unreadable)):
            return 2
        if self.violations:
            return 1
        if self.empty or self.undecided:
            return 3
        return 0

    def lines(self, strict_nfr: bool = True) -> list[str]:
        out = []
        for title, items in (("読めない", self.unreadable), ("形式の違反", self.violations), ("表が無い", self.missing),
                             ("必須の欄が空", self.empty), ("未決定の印", self.undecided)):
            if items:
                out.append(f"{title}（{len(items)} 件）:")
                out.extend(f"  {item}" for item in items)
        code = self.code(strict_nfr)  # 終了コードと同じ判定で文面を作る（scaffold の関門は strict_nfr=False）
        if code == 2:
            out.append("読めない表がある。中身を検査していない（判定していない）")
        elif code == 1:
            out.append(f"形式の違反が {len(self.violations)} 件ある。表を直す（references/tree.md の「システム設計書の成果物」）")
        elif code == 3:
            out.append(f"形式の違反は無いが、決まっていない欄が {len(self.empty) + len(self.undecided)} 件ある。"
                       "推測で埋めずに Q&A 表に起票する（references/tree.md の「情報が無いとき」）")
        else:
            checked = ", ".join(f"{name}（{count} 行）" for name, count in self.rows.items())
            out.append(f"OK（{checked or '検査した表なし'}）")
        if self.respondents:
            out.append(f"{RESPONDENT_HEADING}{len(self.respondents)} 件）:")
            out.extend(f"  {item}" for item in self.respondents)
            out.append("表に無い人・答える範囲の無い人の回答は、範囲を持つ関係者に確かめてから反映する"
                       "（references/tree.md の「関係者の表」。質問がその人の範囲かは機械で見ていない）")
        if self.usages:
            out.append(f"{USAGE_HEADING}{len(self.usages)} 件）:")
            out.extend(f"  {item}" for item in self.usages)
            out.append("用語集の用語に言い換えるか、文脈で要る（引用・説明）なら残す（references/tree.md の「用語集」。"
                       "語の区切りは見ていない——ほかの語の中の出現も出る）")
        if len(self.missing) == len(ALL_TABLES):
            out.append("成果物の表が 1 つも無い——渡したディレクトリが版のディレクトリか重ね合わせた全体かを確かめる")
        return out


def markers(value: str) -> list[str]:
    return [hit for _, hit in spec_exit.find_markers(value)]


def read_table(root: Path, rel: str, report: Report) -> tuple[list[str], list[tuple[int, list[str]]]] | None:
    """(見出し, [(行番号, セル)]) を返す。無ければ「表が無い」に、読めなければ「読めない」に足して None。"""
    path = root / rel
    if not path.is_file():
        if path.exists():
            report.unreadable.append(f"{rel}: ファイルでない")
        else:
            report.missing.append(rel)
        return None
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        report.unreadable.append(f"{rel}: 読めない（{e.strerror}）")
        return None
    except UnicodeDecodeError:
        report.unreadable.append(f"{rel}: UTF-8 として読めない")
        return None
    if not text.strip():
        report.unreadable.append(f"{rel}: 空のファイル")
        return None
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader)
    rows = []
    for fields in reader:
        if not any(f.strip() for f in fields):
            continue  # 空行
        rows.append((reader.line_num, fields))
    return header, rows


def cell_state(report: Report, where: str, column: str, value: str, may_be_empty: bool) -> bool:
    """セルが決まっているか。空・印なら該当の見出しに足して False（値の決まりに当てない）。"""
    hits = markers(value)
    if hits:
        report.undecided.append(f"{where}: {column} に未決定の印（{'・'.join(hits)}）: {value.strip()!r}")
        return False
    if not value.strip():
        if not may_be_empty:
            report.empty.append(f"{where}: {column} が空")
        return False
    return True


def check_columns(report: Report, rel: str, header: list[str], expected: list[str]) -> bool:
    if header == expected:
        return True
    report.violations.append(f"{rel}:1: 見出しの行が決まりと違う（期待: {','.join(expected)} ／ 実際: {','.join(header)}）")
    extra = [name for name in header if name not in expected]
    if extra:
        report.violations.append(f"{rel}:1: 決まりに無い列（{'・'.join(extra)}）——物理設計（テーブル・インデックス・物理の型）は"
                                 "この表に書かず、内部の Q&A 表（spec/qa-dev.csv）に記録する")
    return False


def check_plain(root: Path, rel: str, report: Report, context: dict) -> None:
    table = read_table(root, rel, report)
    if table is None:
        return
    header, rows = table
    expected = COLUMNS[rel]
    if not check_columns(report, rel, header, expected):
        return
    seen: dict[tuple[str, ...], int] = {}
    names: dict[str, tuple[str, int]] = {}
    ids: set[str] = set()
    pending = False  # id が未決定・空の行がある（その行を指すレイアウトの id を違反と言い切れない）
    kept: set[str] = set()  # データモデルの、保管期間が決まっているエンティティ（CRUD 表の消す機能の抜けに使う。#1162）
    referenced = ENTITY_COLUMN if rel == ENTITIES else "id"  # ほかの表から指される欄（データモデルはエンティティ名で指される）
    for line, fields in rows:
        where = f"{rel}:{line}"
        if len(fields) != len(expected):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(expected)}）")
            continue
        row = dict(zip(expected, fields))
        decided = {column: cell_state(report, where, column, value, column in MAY_BE_EMPTY.get(rel, set()))
                   for column, value in row.items()}
        pending = pending or (referenced in decided and not decided[referenced])
        if rel == ENTITIES and decided[ENTITY_COLUMN]:
            ids.add(row[ENTITY_COLUMN].strip())
            if decided[RETENTION_COLUMN]:
                kept.add(row[ENTITY_COLUMN].strip())
        for column, value in row.items():
            if not decided[column]:
                continue
            value = value.strip()
            allowed = VALUES.get((rel, column))
            if allowed and value not in allowed:
                report.violations.append(f"{where}: {column} が {'・'.join(allowed)} のどれでもない: {value!r}")
            if column == "id" and rel in ID_PREFIX:
                if not re.fullmatch(re.escape(ID_PREFIX[rel]) + r"[0-9]{3,}", value):
                    report.violations.append(f"{where}: id が {ID_PREFIX[rel]} に 3 桁以上の数字の形でない: {value!r}")
                else:
                    ids.add(value)
            if column == ORDER_COLUMN and not POSITIVE_INTEGER.fullmatch(value):
                report.violations.append(f"{where}: {ORDER_COLUMN} が正の整数でない: {value!r}")
        key_columns = UNIQUE[rel]
        if all(decided[column] for column in key_columns):
            key = tuple(row[column].strip() for column in key_columns)
            if key in seen:
                report.violations.append(f"{where}: {'・'.join(key_columns)} が {seen[key]} 行目と重複: {' / '.join(key)}")
            else:
                seen[key] = line
        if rel == IO_LAYOUT and decided["id"]:
            listed = context.get(IO_LIST)
            if listed is None:
                report.violations.append(f"{where}: id {row['id'].strip()} を照らす入出力の一覧（{IO_LIST}）が無い・読めない")
            elif row["id"].strip() not in listed and context.get(IO_LIST + "#pending"):
                # 一覧の id が未決定なら、指す先が決まっていない——違反でなく未決定に数える
                report.undecided.append(f"{where}: id {row['id'].strip()} が入出力の一覧（{IO_LIST}）に無い（一覧に id の決まっていない行がある）")
            elif row["id"].strip() not in listed:
                report.violations.append(f"{where}: id {row['id'].strip()} が入出力の一覧（{IO_LIST}）に無い")
        if rel == REPORTS and decided["id"] and decided["帳票名"]:
            rid, name = row["id"].strip(), row["帳票名"].strip()
            if rid in names and names[rid][0] != name:
                report.violations.append(f"{where}: 帳票 {rid} の帳票名が {names[rid][1]} 行目と違う: {name!r}（{names[rid][0]!r}）")
            names.setdefault(rid, (name, line))
    report.rows[rel] = len(rows)
    context[rel] = ids
    context[rel + "#pending"] = pending
    if rel == ENTITIES:
        context[ENTITIES + "#kept"] = kept


def check_purposes(root: Path, report: Report, context: dict) -> None:
    """目的の表（#1154）。機能一覧の id は `context`（`check_plain` が先に読む）から照らす。"""
    table = read_table(root, PURPOSES, report)
    if table is None:
        return
    header, rows = table
    if not check_columns(report, PURPOSES, header, PURPOSES_COLUMNS):
        return
    features = context.get(FEATURES)  # 機能一覧が無い・読めない・見出しが違うなら None
    features_pending = context.get(FEATURES + "#pending", False)
    seen: dict[str, int] = {}
    goals: set[str] = set()
    measures: list[tuple[str, dict[str, str]]] = []
    pending = False  # id が未決定・空の行がある（その行を指す上位を違反と言い切れない）
    for line, fields in rows:
        where = f"{PURPOSES}:{line}"
        if len(fields) != len(PURPOSES_COLUMNS):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(PURPOSES_COLUMNS)}）")
            continue
        row = dict(zip(PURPOSES_COLUMNS, fields))
        kind = None
        if cell_state(report, where, "id", row["id"], False):
            value = row["id"].strip()
            matched = PURPOSE_ID.fullmatch(value)
            if not matched:
                report.violations.append(f"{where}: id が G-（目的）か K-（指標）に 3 桁以上の数字の形でない: {value!r}")
            elif value in seen:
                report.violations.append(f"{where}: id が {seen[value]} 行目と重複: {value}")
            else:
                seen[value] = line
                kind = matched.group(1)
        else:
            pending = True
        cell_state(report, where, "内容", row["内容"], False)
        if kind is None:
            continue
        own = PURPOSE_OWN[kind]
        for column in PURPOSES_COLUMNS:
            if column in ("id", "内容") or column in own:
                continue
            if markers(row[column]):
                # 印は未決定（値の決まりに当てない——上の docstring）。空にする欄でも違反にしない
                cell_state(report, where, column, row[column], True)
            elif row[column].strip():
                other = next(k for k, columns in PURPOSE_OWN.items() if column in columns)
                report.violations.append(f"{where}: {PURPOSE_KINDS[kind]}の行に {column} を書いた（{PURPOSE_KINDS[other]}の行だけに書く）: "
                                         f"{row[column].strip()!r}")
        for column in own:
            if column != "機能":
                cell_state(report, where, column, row[column], False)
        if kind == "G-":
            goals.add(row["id"].strip())
        else:
            measures.append((where, row))
    measured: set[str] = set()
    covered: set[str] = set()
    for where, row in measures:
        upper = row["上位"]
        if not markers(upper) and upper.strip():
            value = upper.strip()
            if value in goals:
                measured.add(value)
            elif value in seen:
                report.violations.append(f"{where}: 上位 {value} が目的（G-）の行でない——指標の上位は目的を指す")
            elif pending:
                report.undecided.append(f"{where}: 上位 {value} が表に無い（表に id の決まっていない行がある）")
            else:
                report.violations.append(f"{where}: 上位 {value} が表の目的に無い")
        value = row["機能"]
        if features is None:
            # 機能一覧が無ければ照らす相手が無い——空でよく、書いた id は違反（入出力のレイアウトと同じ扱い）
            if cell_state(report, where, "機能", value, True) and value.strip() != PURPOSE_NONE:
                report.violations.append(f"{where}: 機能 の id を照らす機能一覧（{FEATURES}）が無い・読めない")
            continue
        if markers(value):
            cell_state(report, where, "機能", value, False)
            # 印と並べた決まった id は結び付けに数える（印があるだけで、載っている機能を目的を指さない機能と名指ししない）
            covered.update(item.strip() for item in value.split(PURPOSE_SEPARATOR) if item.strip() in features)
            continue
        if not value.strip():
            report.empty.append(f"{where}: 機能 が空（どの機能も動かさない指標——動かす機能を足すか、{PURPOSE_NONE} と決める）")
            continue
        items = [item.strip() for item in value.split(PURPOSE_SEPARATOR)]
        if items == [PURPOSE_NONE]:
            continue
        if PURPOSE_NONE in items:
            report.violations.append(f"{where}: 機能 に {PURPOSE_NONE} と機能の id を混ぜた: {value.strip()!r}")
            continue
        for item in items:
            if not FEATURE_ID.fullmatch(item):
                report.violations.append(f"{where}: 機能 の値が機能一覧の id（F- に 3 桁以上の数字）でない: {item!r}"
                                         f"（区切りは {PURPOSE_SEPARATOR}）")
            elif item in features:
                covered.add(item)
            elif features_pending:
                report.undecided.append(f"{where}: 機能 {item} が機能一覧（{FEATURES}）に無い（一覧に id の決まっていない行がある）")
            else:
                report.violations.append(f"{where}: 機能 {item} が機能一覧（{FEATURES}）に無い")
    for goal in sorted(goals - measured):
        report.undecided.append(f"{PURPOSES}:{seen[goal]}: 目的 {goal} を測る指標（上位が {goal} の K- の行）が無い——成功の判定が決まっていない")
    if features is not None:
        for feature in sorted(features - covered):
            report.undecided.append(f"{PURPOSES}: 機能一覧の {feature} が、どの指標の 機能 にも無い（目的を指さない機能——"
                                    "要るか、要るならどの目的のためかを Q&A 表に起票する）")
    report.rows[PURPOSES] = len(rows)


def check_crud(root: Path, report: Report, context: dict) -> None:
    """CRUD 表（#1162）。機能一覧の id とデータモデルのエンティティは `context`（`check_plain` が先に読む）から照らす。
    表が決まりどおりに読めたら、データモデルのエンティティごとに作る・読む・消す（保管期間が決まっているとき）機能の抜けを未決定に数える。"""
    table = read_table(root, CRUD, report)
    if table is None:
        return
    header, rows = table
    if not check_columns(report, CRUD, header, CRUD_COLUMNS):
        return
    feature_ids = context.get(FEATURES)  # 機能一覧が無い・読めない・見出しが違うなら None
    feature_ids_pending = context.get(FEATURES + "#pending", False)
    entities = context.get(ENTITIES)  # データモデルが無い・読めない・見出しが違うなら None
    entities_pending = context.get(ENTITIES + "#pending", False)
    seen: dict[tuple[str, str], int] = {}
    done: dict[str, dict[str, str]] = {}  # エンティティ → 操作 → その操作をする機能（最初の 1 つ）
    declined: dict[str, dict[str, str]] = {}  # エンティティ → 操作 → `なし` と決めた行
    maybe: dict[str, set[str]] = {}  # エンティティ → 機能の決まっていない行（未決定の印・空）が持つ操作（する機能はある——結び付けに数える）
    pending: set[str] = set()  # 操作が決まっていない・機能が形式の違反の行のあるエンティティ（どの操作の抜けも言い切れない）
    unsure_ops: set[str] = set()  # エンティティの決まっていない行の操作（どのエンティティの、その操作の抜けも言い切れない）
    for line, fields in rows:
        where = f"{CRUD}:{line}"
        if len(fields) != len(CRUD_COLUMNS):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(CRUD_COLUMNS)}）")
            unsure_ops.update(CRUD_OPERATIONS)
            continue
        row = dict(zip(CRUD_COLUMNS, fields))
        feature = None
        feature_open = True  # 機能が未決定（未決定の印・空・一覧の未決定で照らせない）——形式の違反なら偽
        feature_value = entity_value = None  # 決まったセルの値（組の重複は、操作が決まっていなくても見る）
        if cell_state(report, where, "機能", row["機能"], False):
            feature_open = False
            value = feature_value = row["機能"].strip()
            if value == CRUD_NONE:
                feature = value
            elif not FEATURE_ID.fullmatch(value):
                report.violations.append(f"{where}: 機能 が機能一覧の id（F- に 3 桁以上の数字）でも {CRUD_NONE} でもない: {value!r}")
            elif feature_ids is None:
                report.violations.append(f"{where}: 機能 {value} を照らす機能一覧（{FEATURES}）が無い・読めない")
            elif value in feature_ids:
                feature = value
            elif feature_ids_pending:
                feature_open = True
                report.undecided.append(f"{where}: 機能 {value} が機能一覧（{FEATURES}）に無い（一覧に id の決まっていない行がある）")
            else:
                report.violations.append(f"{where}: 機能 {value} が機能一覧（{FEATURES}）に無い")
        entity = None
        entity_open = False  # エンティティが未決定（未決定の印・空）
        if cell_state(report, where, "エンティティ", row["エンティティ"], False):
            value = entity_value = row["エンティティ"].strip()
            if entities is None:
                report.violations.append(f"{where}: エンティティ {value} を照らすデータモデル（{ENTITIES}）が無い・読めない")
            elif value in entities:
                entity = value
            elif entities_pending:
                report.undecided.append(f"{where}: エンティティ {value} がデータモデル（{ENTITIES}）に無い（データモデルにエンティティの決まっていない行がある）")
            else:
                report.violations.append(f"{where}: エンティティ {value} がデータモデル（{ENTITIES}）に無い")
        else:
            entity_open = True
        operations = None
        if cell_state(report, where, "操作", row["操作"], False):
            value = row["操作"].strip()
            if value and CRUD_OPERATION.fullmatch(value):
                operations = value
            else:
                report.violations.append(f"{where}: 操作 が {'・'.join(CRUD_OPERATIONS)} をこの順に 1 回ずつまで並べた形（CR・RU など）でない: {value!r}")
        if feature_value is not None and entity_value is not None:
            pair = (feature_value, entity_value)
            if pair in seen:
                report.violations.append(f"{where}: 機能・エンティティ が {seen[pair]} 行目と重複: {feature_value} / {entity_value}")
                continue
            seen[pair] = line
        if entity_open:
            # どのエンティティの行か決まらない——その行の操作の抜けだけを、どのエンティティでも言い切らない（ほかの操作の抜けは言い切れる）
            unsure_ops.update(operations or CRUD_OPERATIONS)
            continue
        if entity is None:
            continue
        if operations is None or (feature is None and not feature_open):
            pending.add(entity)
            continue
        if feature is None:
            # する機能は決まっていないが、その操作をする機能があることは決まっている——結び付けに数える（目的の表の `機能` の印と同じ）
            maybe.setdefault(entity, set()).update(operations)
            continue
        for op in operations:
            if feature == CRUD_NONE:
                declined.setdefault(entity, {}).setdefault(op, where)
            else:
                done.setdefault(entity, {}).setdefault(op, feature)
    for entity, ops in declined.items():
        for op, where in ops.items():
            if op in done.get(entity, {}):
                report.violations.append(f"{where}: エンティティ {entity} の {op} を {CRUD_NONE} と書いたが、機能 {done[entity][op]} が {op} する"
                                         "——する機能があるなら なし の行から外す")
    report.rows[CRUD] = len(rows)
    if entities is None:
        return
    kept = context.get(ENTITIES + "#kept", set())
    for entity in sorted(entities - pending):
        covered = set(done.get(entity, {})) | set(declined.get(entity, {})) | maybe.get(entity, set())
        for op, verb in CRUD_GAPS.items():
            if op in covered or op in unsure_ops or (op == CRUD_KEPT and entity not in kept):
                continue
            reason = "保管期間が決まっているのに、" if op == CRUD_KEPT else ""
            report.undecided.append(f"{CRUD}: エンティティ {entity} を{verb}（{op}）機能が無い（{reason}どの機能の行にも {op} が無く、{CRUD_NONE} の行でも決めていない——"
                                    f"{verb}機能を足すか、{verb}機能は無いと {CRUD_NONE} の行で決めるかを Q&A 表に起票する）")


def check_migration(root: Path, report: Report) -> None:
    """移行の表（#1158）。種類ごとに書く列を見て、表があれば 3 つの種類のどれにも行（`なし` の行でもよい）があるかを見る。"""
    table = read_table(root, MIGRATION, report)
    if table is None:
        return
    header, rows = table
    if not check_columns(report, MIGRATION, header, MIGRATION_COLUMNS):
        return
    numbers: dict[str, int] = {}  # id → 最初の行
    kinds: dict[str, list[str]] = {}  # 種類 → その種類の行の場所
    declined: dict[str, str] = {}  # 種類 → `なし` と決めた行の場所
    kind_open = False  # 種類の決まっていない行がある（行の無い種類を言い切れない）
    for line, fields in rows:
        where = f"{MIGRATION}:{line}"
        if len(fields) != len(MIGRATION_COLUMNS):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(MIGRATION_COLUMNS)}）")
            kind_open = True
            continue
        row = dict(zip(MIGRATION_COLUMNS, fields))
        if cell_state(report, where, "id", row["id"], False):
            value = row["id"].strip()
            if not MIGRATION_ID.fullmatch(value):
                report.violations.append(f"{where}: id が M- に 3 桁以上の数字の形でない: {value!r}")
            elif value in numbers:
                report.violations.append(f"{where}: id が {numbers[value]} 行目と重複: {value}")
            else:
                numbers[value] = line
        kind = None
        if cell_state(report, where, "種類", row["種類"], False):
            value = row["種類"].strip()
            if value in MIGRATION_KINDS:
                kind = value
            else:
                kind_open = True  # どの種類の行のつもりか決まらない（列の数の違う行と同じ）
                report.violations.append(f"{where}: 種類 が {'・'.join(MIGRATION_KINDS)} のどれでもない: {value!r}")
        else:
            kind_open = True
        if kind is None:
            continue
        kinds.setdefault(kind, []).append(where)
        if not cell_state(report, where, "対象", row["対象"], False):
            continue  # `なし` の行かどうか決まらない——種類ごとの欄を判定しない
        if row["対象"].strip() == MIGRATION_NONE:
            declined.setdefault(kind, where)
            for column in MIGRATION_COLUMNS:
                if column in ("id", "種類", "対象"):
                    continue
                cell = row[column]
                if markers(cell):
                    cell_state(report, where, column, cell, True)
                elif cell.strip():
                    report.violations.append(f"{where}: 対象 が {MIGRATION_NONE} の行に {column} を書いた（移すもの・することが無いと決めた行は"
                                             f" id・種類・対象 のほかを空にする）: {row[column].strip()!r}")
            continue
        own = MIGRATION_OWN[kind]
        method = None
        for column in MIGRATION_COLUMNS:
            if column in ("id", "種類", "対象"):
                continue
            if column in MIGRATION_COMMON or column in own:
                if column == MIGRATION_PERIOD:
                    continue  # 切替の方式を見てから決める（下）
                if cell_state(report, where, column, row[column], False) and column == "切替の方式":
                    value = row[column].strip()
                    if value in MIGRATION_METHODS:
                        method = value
                    else:
                        report.violations.append(f"{where}: 切替の方式 が {'・'.join(MIGRATION_METHODS)} のどれでもない: {value!r}")
                continue
            cell = row[column]
            if markers(cell):
                # 印は未決定（値の決まりに当てない）。空にする欄でも違反にしない
                cell_state(report, where, column, cell, True)
            elif cell.strip():
                owners = "・".join(k for k in MIGRATION_KINDS if column in MIGRATION_OWN[k])
                report.violations.append(f"{where}: {kind}の行に {column} を書いた（{owners}の行だけに書く）: {row[column].strip()!r}")
        if MIGRATION_PERIOD in own:
            period = row[MIGRATION_PERIOD]
            if method == MIGRATION_PARALLEL:
                cell_state(report, where, MIGRATION_PERIOD, period, False)
            elif markers(period):
                cell_state(report, where, MIGRATION_PERIOD, period, True)
            elif method is not None and period.strip():
                report.violations.append(f"{where}: 切替の方式 が {method} の行に {MIGRATION_PERIOD} を書いた（{MIGRATION_PARALLEL} の行だけに書く）: "
                                         f"{period.strip()!r}")
    for kind, where in declined.items():
        others = [place for place in kinds[kind] if place != where]
        if others:
            report.violations.append(f"{where}: 種類 {kind} を 対象 {MIGRATION_NONE} と決めたが、同じ種類の行がほかにある（{'・'.join(others)}）"
                                     f"——移すもの・することがあるなら {MIGRATION_NONE} の行を外す")
    if not kind_open:
        for kind in MIGRATION_KINDS:
            if kind not in kinds:
                report.undecided.append(f"{MIGRATION}: 種類 {kind} の行が無い（{kind}の移行が決まっていない——移すもの・することが無いなら"
                                        f" 対象 を {MIGRATION_NONE} にした行で決める。どちらかを Q&A 表に起票する）")
    report.rows[MIGRATION] = len(rows)


def check_acceptance(root: Path, report: Report, context: dict) -> None:
    """テスト要件の表（#1160）。確かめ方ごとに書く列を見て、`機能` を機能一覧（`context`）と照らし、受入の人の行があるかを見る。"""
    table = read_table(root, ACCEPTANCE, report)
    if table is None:
        return
    header, rows = table
    if not check_columns(report, ACCEPTANCE, header, ACCEPTANCE_COLUMNS):
        return
    features = context.get(FEATURES)  # 機能一覧が無い・読めない・見出しが違うなら None
    features_pending = context.get(FEATURES + "#pending", False)
    stage_ids: dict[str, int] = {}  # id → 最初の行
    required = False  # 段が受入で確かめ方が人の行がある
    open_rows = False  # 段か確かめ方の決まっていない行がある（受入の人の行が無いと言い切れない）
    for line, fields in rows:
        where = f"{ACCEPTANCE}:{line}"
        if len(fields) != len(ACCEPTANCE_COLUMNS):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(ACCEPTANCE_COLUMNS)}）")
            open_rows = True
            continue
        row = dict(zip(ACCEPTANCE_COLUMNS, fields))
        if cell_state(report, where, "id", row["id"], False):
            value = row["id"].strip()
            if not ACCEPTANCE_ID.fullmatch(value):
                report.violations.append(f"{where}: id が A- に 3 桁以上の数字の形でない: {value!r}")
            elif value in stage_ids:
                report.violations.append(f"{where}: id が {stage_ids[value]} 行目と重複: {value}")
            else:
                stage_ids[value] = line
        stage = None
        if cell_state(report, where, "段", row["段"], False):
            value = row["段"].strip()
            if value in ACCEPTANCE_STAGES:
                stage = value
            else:
                report.violations.append(f"{where}: 段 が {'・'.join(ACCEPTANCE_STAGES)} のどれでもない: {value!r}")
        for column in ACCEPTANCE_COMMON:
            cell_state(report, where, column, row[column], False)
        way = None
        if cell_state(report, where, "確かめ方", row["確かめ方"], False):
            value = row["確かめ方"].strip()
            if value in ACCEPTANCE_WAYS:
                way = value
            else:
                report.violations.append(f"{where}: 確かめ方 が {'・'.join(ACCEPTANCE_WAYS)} のどれでもない: {value!r}")
        if stage is None or way is None:
            open_rows = True
        elif (stage, way) == ACCEPTANCE_REQUIRED:
            required = True
        check_acceptance_features(report, where, row[ACCEPTANCE_FEATURES], features, features_pending)
        if way is None:
            continue  # どちらの行か決まらない——確かめ方ごとの欄を判定しない
        for kind, columns in ACCEPTANCE_OWN.items():
            for column in columns:
                cell = row[column]
                if kind == way:
                    cell_state(report, where, column, cell, column in ACCEPTANCE_MAY_BE_EMPTY)
                elif markers(cell):
                    # 印は未決定（値の決まりに当てない）。空にする欄でも違反にしない
                    cell_state(report, where, column, cell, True)
                elif cell.strip():
                    report.violations.append(f"{where}: {way}の行に {column} を書いた（{kind}の行だけに書く）: {cell.strip()!r}")
    if not open_rows and not required:
        stage, way = ACCEPTANCE_REQUIRED
        report.undecided.append(f"{ACCEPTANCE}: 段 {stage} で 確かめ方 {way} の行が無い（利用者の受け入れの観点が決まっていない——"
                                "誰が・どのデータで・いつ・何をもって合格とするかを Q&A 表に起票する）")
    report.rows[ACCEPTANCE] = len(rows)


def check_acceptance_features(report: Report, where: str, value: str, features: set[str] | None, features_pending: bool) -> None:
    """テスト要件の表の `機能`（空でよい）。機能一覧の id を `PURPOSE_SEPARATOR` で区切ったもので、一覧と照らす（目的の表の `機能` と同じ扱い）。"""
    if not cell_state(report, where, ACCEPTANCE_FEATURES, value, True):
        return  # 空か未決定の印
    if features is None:
        report.violations.append(f"{where}: 機能 の id を照らす機能一覧（{FEATURES}）が無い・読めない")
        return
    for item in (item.strip() for item in value.split(PURPOSE_SEPARATOR)):
        if not FEATURE_ID.fullmatch(item):
            report.violations.append(f"{where}: 機能 の値が機能一覧の id（F- に 3 桁以上の数字）でない: {item!r}（区切りは {PURPOSE_SEPARATOR}）")
        elif item in features:
            continue
        elif features_pending:
            report.undecided.append(f"{where}: 機能 {item} が機能一覧（{FEATURES}）に無い（一覧に id の決まっていない行がある）")
        else:
            report.violations.append(f"{where}: 機能 {item} が機能一覧（{FEATURES}）に無い")


def check_roles(root: Path, report: Report) -> None:
    table = read_table(root, ROLES, report)
    if table is None:
        return
    header, rows = table
    if not header or header[0] != ROLES_FIRST or len(header) < 2:
        report.violations.append(f"{ROLES}:1: 見出しの行が「{ROLES_FIRST},<ロール>,<ロール>…」（ロールは 1 つ以上）でない: {','.join(header)}")
        return
    roles: dict[str, int] = {}
    for index, role in enumerate(header[1:], start=2):
        where = f"{ROLES}:1"
        if not role.strip():
            # 空のロール名は見出しの形の誤り（末尾のカンマなど）——未決定ではない
            report.violations.append(f"{where}: {index} 列目のロール名が空")
            continue
        if not cell_state(report, where, f"{index} 列目のロール名", role, False):
            continue
        if role.strip() in roles:
            report.violations.append(f"{where}: ロール {role.strip()!r} が {roles[role.strip()]} 列目と重複")
        else:
            roles[role.strip()] = index
    seen: dict[str, int] = {}
    for line, fields in rows:
        where = f"{ROLES}:{line}"
        if len(fields) != len(header):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(header)}）")
            continue
        operation = fields[0]
        if cell_state(report, where, ROLES_FIRST, operation, False):
            if operation.strip() in seen:
                report.violations.append(f"{where}: {ROLES_FIRST} が {seen[operation.strip()]} 行目と重複: {operation.strip()}")
            else:
                seen[operation.strip()] = line
        for role, value in zip(header[1:], fields[1:]):
            if cell_state(report, where, f"{role.strip() or '(ロール名なし)'} の可否", value, False) \
                    and value.strip() not in ROLES_VALUES:
                report.violations.append(f"{where}: {role.strip()} の可否が {'・'.join(ROLES_VALUES)} のどれでもない: {value.strip()!r}")
    report.rows[ROLES] = len(rows)


def check_stakeholders(root: Path, report: Report) -> dict[str, bool] | None:
    """関係者の表（#1161）。表が決まりどおりなら {名前: 答える範囲が `なし` でないか} を返す（回答者の照合に使う）。
    無い・読めない・形式の違反があるなら None（違反のある表で回答者を照らさない）。"""
    table = read_table(root, STAKEHOLDERS, report)
    if table is None:
        return None
    header, rows = table
    if not check_columns(report, STAKEHOLDERS, header, STAKEHOLDERS_COLUMNS):
        return None
    before = len(report.violations)
    ids: dict[str, int] = {}
    names: dict[str, int] = {}
    answers: dict[str, bool] = {}
    for line, fields in rows:
        where = f"{STAKEHOLDERS}:{line}"
        if len(fields) != len(STAKEHOLDERS_COLUMNS):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(STAKEHOLDERS_COLUMNS)}）")
            continue
        row = dict(zip(STAKEHOLDERS_COLUMNS, fields))
        if cell_state(report, where, "id", row["id"], False):
            value = row["id"].strip()
            if not STAKEHOLDER_ID.fullmatch(value):
                report.violations.append(f"{where}: id が P- に 3 桁以上の数字の形でない: {value!r}")
            elif value in ids:
                report.violations.append(f"{where}: id が {ids[value]} 行目と重複: {value}")
            else:
                ids[value] = line
        name = None
        if cell_state(report, where, "名前", row["名前"], False):
            name = row["名前"].strip()
            used = [char for char in STAKEHOLDER_NAME_FORBIDDEN if char in name]
            if used:
                report.violations.append(f"{where}: 名前 に {'・'.join(repr(char) for char in used)} を使った（承認の行の区切りと回答の括弧に使う文字）: {name}")
                name = None
            elif name in names:
                report.violations.append(f"{where}: 名前 が {names[name]} 行目と重複: {name}")
                name = None
            else:
                names[name] = line
        for column, allowed, none in (("役割", STAKEHOLDER_ROLES, None), ("合意", STAKEHOLDER_AGREEMENTS, STAKEHOLDER_NONE)):
            if not cell_state(report, where, column, row[column], False):
                continue
            items = [item.strip() for item in row[column].split(STAKEHOLDER_SEPARATOR)]
            if none is not None and items == [none]:
                continue
            if none is not None and none in items:
                report.violations.append(f"{where}: {column} に {none} とほかの値を混ぜた: {row[column].strip()!r}")
                continue
            for item in items:
                if item not in allowed:
                    report.violations.append(f"{where}: {column} の値が {'・'.join(allowed)} のどれでもない: {item!r}"
                                             f"（区切りは {STAKEHOLDER_SEPARATOR}）")
            if len(set(items)) != len(items):
                report.violations.append(f"{where}: {column} に同じ値を重ねた: {row[column].strip()!r}")
        cell_state(report, where, "関心事", row["関心事"], False)
        scope = cell_state(report, where, "答える範囲", row["答える範囲"], False)
        if name is not None:
            # 範囲が未決定・空の人も「答える人」に数える（範囲が `なし` と決まった人だけを答えない人と読む）
            answers[name] = not (scope and row["答える範囲"].strip() == STAKEHOLDER_NONE)
    report.rows[STAKEHOLDERS] = len(rows)
    return answers if len(report.violations) == before else None


def agreements(root: Path) -> dict[str, tuple[str, ...] | None] | None:
    """関係者の表の {名前: 合意}（`なし` なら空のタプル、未決定の印・空なら None）。表が無い・読めない・形式の違反があるなら None。
    **`check-signoff.py` が合意が要る関係者の報告（#1161）で読む**——表の読み方を写さない。名前が未決定・空の行は数えない。"""
    report = Report()
    if check_stakeholders(root, report) is None:
        return None
    _, rows = read_table(root, STAKEHOLDERS, report)
    result: dict[str, tuple[str, ...] | None] = {}
    for _, fields in rows:
        row = dict(zip(STAKEHOLDERS_COLUMNS, fields))
        name = row["名前"].strip()
        if not name or markers(name):
            continue
        value = row["合意"]
        if markers(value) or not value.strip():
            result[name] = None
            continue
        items = tuple(item.strip() for item in value.split(STAKEHOLDER_SEPARATOR))
        result[name] = () if items == (STAKEHOLDER_NONE,) else items
    return result


def check_respondents(root: Path, report: Report, answers: dict[str, bool]) -> None:
    """共有の Q&A 表の回答者を関係者の表の `名前` に照らし、表に無い・答える範囲が `なし`・読めない回答を報告する（#1161）。
    **終了コードに数えない**——表を置く前の回答（凍結した版の書き方を含む）は直せず、質問がその人の範囲かは機械で決まらない。
    `未回答` と暫定の行（利用者が確かめていない）は見ない。表の形は `check-qa-csv.py` が見る——ここは見出しが決まりどおりの表だけを読む。"""
    path = root / QA_TABLE
    if not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        report.respondents.append(f"{QA_TABLE}: 読めない——回答者を照らしていない（check-qa-csv.py で確かめる）")
        return
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        if next(reader, None) != qa.COLUMNS:
            report.respondents.append(f"{QA_TABLE}: 見出しの行が決まりと違う——回答者を照らしていない（check-qa-csv.py で確かめる）")
            return
        rows = [(reader.line_num, fields) for fields in reader]  # 行番号はファイルの物理の行（セルの中の改行を数える。check-qa-csv.py と同じ）
    except csv.Error as e:
        # 128KB を超えるセルなど——表の検査は check-qa-csv.py の仕事で、ここは報告だけなので終了コードを変えない
        report.respondents.append(f"{QA_TABLE}: CSV として読めない（{e}）——回答者を照らしていない（check-qa-csv.py で確かめる）")
        return
    for line_num, fields in rows:
        if not any(f.strip() for f in fields) or len(fields) != len(qa.COLUMNS):
            continue  # 空行と列の数の違う行は check-qa-csv.py が見る
        row = dict(zip(qa.COLUMNS, fields))
        answer = row["回答"].strip()
        if answer == qa.NO_ANSWER or qa.is_provisional(row):
            continue
        where = f"{QA_TABLE}:{line_num}: {row['No'].strip()}"
        who = qa.respondent(answer)
        if who is None:
            report.respondents.append(f"{where} の回答から答えた人を読めない（括弧を `<関係者の名前>が回答` で始める）: {answer!r}")
        elif who not in answers:
            report.respondents.append(f"{where} の回答者 {who} が関係者の表（{STAKEHOLDERS}）の名前に無い")
        elif not answers[who]:
            report.respondents.append(f"{where} の回答者 {who} は関係者の表で答える範囲が {STAKEHOLDER_NONE}")


def check_glossary(root: Path, report: Report) -> tuple[dict[str, list[str]], list[str]] | None:
    """用語集（#1164）。表が決まりどおりなら ({使わない言い方: [その行の用語]}, [表の用語]) を返す（使わない言い方の報告に使う）。
    無い・読めない・形式の違反があるなら None（違反のある表で探さない）。用語が未決定・空の行の使わない言い方は探さない（どの用語の言い換えか言えない）。"""
    table = read_table(root, GLOSSARY, report)
    if table is None:
        return None
    header, rows = table
    if not check_columns(report, GLOSSARY, header, GLOSSARY_COLUMNS):
        return None
    before = len(report.violations)
    terms: dict[str, int] = {}
    listed: list[tuple[str, list[str], str | None]] = []
    for line, fields in rows:
        where = f"{GLOSSARY}:{line}"
        if len(fields) != len(GLOSSARY_COLUMNS):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(GLOSSARY_COLUMNS)}）")
            continue
        row = dict(zip(GLOSSARY_COLUMNS, fields))
        term = None
        if cell_state(report, where, "用語", row["用語"], False):
            term = row["用語"].strip()
            if term in terms:
                report.violations.append(f"{where}: 用語 が {terms[term]} 行目と重複: {term}")
                term = None
            else:
                terms[term] = line
        cell_state(report, where, "意味", row["意味"], False)
        cell_state(report, where, "決めた人", row["決めた人"], False)
        if cell_state(report, where, "決めた日", row["決めた日"], False):
            value = row["決めた日"].strip()
            found = GLOSSARY_DATE.fullmatch(value)
            try:
                valid = found is not None and bool(datetime.date(*(int(part) for part in found.groups())))
            except ValueError:
                valid = False
            if not valid:
                report.violations.append(f"{where}: 決めた日 が YYYY-MM-DD の実在する日付でない: {value!r}")
        if cell_state(report, where, "使わない言い方", row["使わない言い方"], "使わない言い方" in GLOSSARY_MAY_BE_EMPTY):
            items = [item.strip() for item in row["使わない言い方"].split(GLOSSARY_SEPARATOR)]
            if "" in items:
                report.violations.append(f"{where}: 使わない言い方 に区切り（{GLOSSARY_SEPARATOR}）で空の項がある: {row['使わない言い方'].strip()!r}")
            elif len(set(items)) != len(items):
                report.violations.append(f"{where}: 使わない言い方 に同じ言い方を重ねた: {row['使わない言い方'].strip()!r}")
            else:
                listed.append((where, items, term))
    synonyms: dict[str, list[str]] = {}
    for where, items, owner in listed:
        for item in items:
            if item in terms:
                report.violations.append(f"{where}: 使わない言い方 {item!r} が表の用語（{terms[item]} 行目）と同じ——使う言葉と使わない言い方を兼ねられない")
            elif owner is not None:
                synonyms.setdefault(item, []).append(owner)
    report.rows[GLOSSARY] = len(rows)
    return (synonyms, list(terms)) if len(report.violations) == before else None


def usage_files(root: Path) -> list[tuple[str, Path]]:
    """使わない言い方を探す文書（`USAGE_DIRS` の下の `USAGE_SUFFIXES` のファイル。`USAGE_EXCLUDE` と `.` で始まる名前の下は除く）。"""
    found = []
    for top in USAGE_DIRS:
        base = root / top
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            parts = path.relative_to(root).parts
            rel = "/".join(parts)
            if any(part.startswith(".") for part in parts) or rel in USAGE_EXCLUDE or path.suffix not in USAGE_SUFFIXES or not path.is_file():
                continue
            found.append((rel, path))
    return found


def check_usages(root: Path, report: Report, synonyms: dict[str, list[str]], terms: list[str]) -> None:
    """文書の行に現れた用語集の使わない言い方を報告する（#1164）。**終了コードに数えない**——語の区切りを見ないので、
    文脈で要る出現（引用・説明）もほかの語の中の出現も出る。その言い方を含む用語の中の出現だけは除く（`受注` に対する `受注伝票`）。"""
    if not synonyms:
        return
    covering = {word: sorted((term for term in terms if word in term), key=len, reverse=True) for word in synonyms}
    for rel, path in usage_files(root):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            report.usages.append(f"{rel}: 読めない——使わない言い方を探していない")
            continue
        for number, line in enumerate(text.split("\n"), start=1):  # 行は改行（\n）で数える——splitlines は \x0c・U+2028 なども割り、行番号がずれる
            for word, owners in synonyms.items():
                masked = line
                for term in covering[word]:
                    masked = masked.replace(term, "\0")
                if word in masked:
                    report.usages.append(f"{rel}:{number}: 使わない言い方 「{word}」（用語集の用語: {'・'.join(owners)}）")


def check_nfr(root: Path, report: Report) -> None:
    table = read_table(root, NFR, report)
    if table is None:
        return
    header, rows = table
    if header != NFR_COLUMNS:
        # 種類の行が 1 つも無い表の見出しは見ない——性能の行とほかの語の行だけの表は、この検査の外（`nfr.md` の
        # 「指していない行は見ない」を変えない）。種類の行は、見出しの `指標` の位置（無ければ決まりの位置）で探す
        at = header.index("指標") if "指標" in header else NFR_COLUMNS.index("指標")
        if not any(len(fields) > at and fields[at].strip() in NFR_KINDS for _, fields in rows):
            report.rows[NFR] = 0
            return
        check_columns(report, NFR, header, NFR_COLUMNS)
        return
    numbers: dict[str, int] = {}
    counts: dict[str, int] = {}
    kinds = []
    for line, fields in rows:
        if len(fields) != len(NFR_COLUMNS):
            if len(fields) > 2 and fields[2].strip() in NFR_KINDS:
                report.violations.append(f"{NFR}:{line}: 列の数が {len(fields)}（見出しは {len(NFR_COLUMNS)}）")
            continue
        row = dict(zip(NFR_COLUMNS, fields))
        numbers.setdefault(row["No"].strip(), line)
        counts[row["No"].strip()] = counts.get(row["No"].strip(), 0) + 1
        if row["指標"].strip() in NFR_KINDS:
            kinds.append((line, row))
    for line, row in kinds:
        where = f"{NFR}:{line}"
        kind = row["指標"].strip()
        number = row["No"].strip()
        if cell_state(report, where, "No", row["No"], False):
            if not NFR_NUMBER.fullmatch(number):
                report.violations.append(f"{where}: No が N- に 3 桁以上の数字の形でない: {number!r}")
            elif numbers.get(number) != line:
                report.violations.append(f"{where}: No が {numbers[number]} 行目と重複: {number}")
            elif counts.get(number, 0) > 1:
                # 種類の行が先で、後ろの行が同じ No を使う
                report.violations.append(f"{where}: No が後ろの行と重複: {number}")
        for column in NFR_REQUIRED:
            cell_state(report, where, column, row[column], False)
        units = NFR_KINDS[kind]
        upper = row["上限"]
        if cell_state(report, where, "上限", upper, False):
            value = upper.strip()
            if kind == "可用性" and not (PERCENT.fullmatch(value) and 0 < float(value) <= 100):
                report.violations.append(f"{where}: {kind} の上限が 0 より大きく 100 以下の数でない: {value!r}")
            if kind in ("保管期間", "バックアップ") and not POSITIVE_INTEGER.fullmatch(value):
                report.violations.append(f"{where}: {kind} の上限が正の整数でない: {value!r}")
        unit = row["単位"]
        if units:
            if cell_state(report, where, "単位", unit, False) and unit.strip() not in units:
                report.violations.append(f"{where}: {kind} の単位が {'・'.join(units)} のどれでもない: {unit.strip()!r}")
        elif cell_state(report, where, "単位", unit, True):
            report.violations.append(f"{where}: {kind} の単位は空にする（水準は上限に書く）: {unit.strip()!r}")
    report.rows[NFR] = len(kinds)


def inspect(root: Path) -> Report:
    """`root`（版のディレクトリか重ね合わせた全体）の成果物の表を検査する。"""
    report = Report()
    context: dict = {}
    for rel in COLUMNS:  # 入出力の一覧はレイアウトより先（辞書の順）
        check_plain(root, rel, report, context)
    check_purposes(root, report, context)  # 機能一覧より後（`context` の機能一覧の id を照らす）
    check_crud(root, report, context)  # 機能一覧とデータモデルより後（`context` の id とエンティティを照らす）
    check_migration(root, report)
    check_acceptance(root, report, context)  # 機能一覧より後（`context` の id を照らす）
    check_roles(root, report)
    check_nfr(root, report)
    answers = check_stakeholders(root, report)
    if answers is not None:
        check_respondents(root, report, answers)
    elif (root / STAKEHOLDERS).is_file():
        report.respondents.append(f"{STAKEHOLDERS} が決まりに反する・読めないので、回答者を照らしていない")
    glossary = check_glossary(root, report)
    if glossary is not None:
        check_usages(root, report, *glossary)
    elif (root / GLOSSARY).is_file():
        report.usages.append(f"{GLOSSARY} が決まりに反する・読めないので、使わない言い方を探していない")
    return report


def respondent_block(lines: list[str]) -> list[str]:
    """`check` の出力のうち、終了コードに数えない報告——回答者の照合（#1161）と用語集の使わない言い方（#1164）——の最初の見出しから後ろ。
    無ければ空。scaffold の関門が、通ったときにも出す。"""
    start = next((i for i, line in enumerate(lines) if line.startswith((RESPONDENT_HEADING, USAGE_HEADING))), None)
    return [] if start is None else lines[start:]


def check(root: Path, strict_nfr: bool = True) -> tuple[int, list[str]]:
    report = inspect(root)
    return report.code(strict_nfr), report.lines(strict_nfr)


def listed_features(root: Path) -> list[str] | None:
    """機能一覧（`requirements/features.csv`）の id。表が無ければ None。`check` を通った表に呼ぶ（scaffold の関門）。"""
    table = read_table(root, FEATURES, Report())
    if table is None:
        return None
    _, rows = table
    return [fields[0].strip() for _, fields in rows if fields and fields[0].strip()]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.splitlines()[2] if __doc__ else
              f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）", file=sys.stderr)
        return 2
    root = Path(argv[0])
    if not root.is_dir():
        print(f"{root}: ディレクトリが無い。判定していない", file=sys.stderr)
        return 2
    code, lines = check(root)
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
