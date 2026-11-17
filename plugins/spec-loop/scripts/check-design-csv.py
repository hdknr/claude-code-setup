#!/usr/bin/env python3
"""システム設計書の成果物の表（目的と成功の判定・機能一覧・データモデル・入出力・帳票・権限・バッチ・ジョブと、非機能要求の性能のほかの種類）と関係者の表を検査する。

usage: python3 check-design-csv.py <版のディレクトリ（docs/v<n>）か重ね合わせた全体（build/merged）>

**決まりの正は `references/tree.md` の「システム設計書の成果物」（関係者の表を含む）と `references/nfr.md` の「性能のほかの種類」である**（このプラグインの中にある）。
下の定数（表の置き場所・列・空でよい列・決まった値・番号の形・重複させない欄・権限一覧の形・非機能要求の種類・関係者の表の列と決まった値）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-check-design-csv.py` が突き合わせて見る**。

渡したディレクトリの `requirements/` と `shared/nfr.csv`・`shared/stakeholders.csv` を読み、見つけたものを **4 つに分けて**出す（#957）:

- **形式の違反**——見出しの行が決まりと違う（順・綴り・列の過不足。物理設計の列を足した表もここ）・列の数・番号の形・重複・
  決まった値でない・レイアウトの id が入出力の一覧に無い・同じ帳票の id で帳票名が違う・非機能要求の種類の上限と単位の形・
  目的の表（#1154）の種類ごとに空にする欄に書いた（未決定の印なら未決定に数える）・指標の `上位` が表の目的でない・指標の `機能` の id が機能一覧に無い（一覧が無いときも）・`なし` と id を混ぜた・
  関係者の表（#1161）の名前の重複・役割と合意の値が決まった値でない・同じ値を重ねた・合意に `なし` とほかの値を混ぜた
- **表が無い**——決まりの表のうち、渡したディレクトリに無いもの。**止めない**（前からの正本は成果物の表を持たない。v2 以降の版のディレクトリは足した表しか持たない）
- **必須の欄が空**——空でよい列のほかの欄が空（要る情報がまだ無い）
- **未決定の印**——セルに `references/spec-exit.md` の未決定の印（`TBD`・`TODO`・`未定`・`要確認`）がある。
  印の判定は `check-spec-exit.py` の `find_markers` を読む（写さない）。**印のあるセルと空のセルは、値の決まりに当てない**——未決定は違反ではない。
  **目的の表の結び付けの欠け**（目的を測る指標が無い・機能一覧の機能がどの指標の `機能` にも無い——目的を指さない機能）もここに数える——
  要るかどうかは利用者が決めることで、表の形の誤りではない

**4 つのほかに、回答者の照合を報告する（終了コードに数えない。#1161）**——関係者の表が決まりどおりで、`shared/qa.csv` があるとき、
`未回答` でも暫定でもない行の回答者（`check-qa-csv.py` の `respondent` が `回答` の括弧から読む）が、表の `名前` に無い・表で `答える範囲` が `なし`・括弧から読めない、を出す。
関係者の表が決まりに反するなら照らさず、そう出す。

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
| **表どうしの整合**（データモデルの項目と入出力の項目が合うか・権限一覧の操作が機能一覧にあるか） | 名前の付け方が表ごとに違ってよく、機械で対応を決められない。**例外は id で指す 2 つだけ**——入出力のレイアウトの id（一覧に無い id は落とす）と、目的の表の指標の `機能`（機能一覧の id と照らす）。Q&A 表の回答者と関係者の表の名前の照合は報告で、終了コードに数えない（下の行） |
| **目的に照らした過不足の中身**（`機能` に載った機能が本当にその指標を動かすか・目的の切り方が正しいか） | 判断であって、一意に決まらない。spec-review の Domain Checker が目的の表を照合先にして見る。ここは結び付けの有無と id の実在だけ |
| **回答者が答えた質問が、その人の答える範囲の中か** | 範囲は自由に書く（分野・機能・目的の id）ので、質問との対応を機械で決められない。req-loop が回答を反映するときに確かめる（`references/tree.md` の「関係者の表」）。照らすのは名前と `なし` だけで、**終了コードにも数えない**——表を置く前の回答（凍結した版を含む）は書き直せない |
| **関係者の表の名前が個人名でないか・非公式の影響力を書いていないか** | 書き方の判断で、文字列からは決まらない |
| **入出力の一覧の `相手` と関係者の表の対応** | 相手はシステムの名前、関係者は部署・役職で、名前の付け方が違う |
| **機能一覧と中間表現の機能の対応** | このスクリプトは中間表現を読まない。`scaffold.py` が関門で照らす（`listed_features` を読む） |
| **印を使わずに書いた未決定**（「あとで決める」） | 言い回しは列挙しきれない。`check-spec-exit.py` と同じ限界 |
| **非機能要求の性能の行・ほかの語の行・種類の語の綴りの揺れ**（`稼働率` と書いた行） | 上のとおり見ない。種類は `指標` の語が 4 つのどれかと一致する行だけ |
| **綴りだけ違う置き場所**（`Requirements/features.csv`） | 決まりの綴りで探し、無ければ「表が無い」と出す。大文字小文字を区別しないファイルシステムでは開けてしまう |
"""

from __future__ import annotations

import csv
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

ALL_TABLES = list(COLUMNS) + [PURPOSES, ROLES, NFR, STAKEHOLDERS]


class Report:
    def __init__(self) -> None:
        self.violations: list[str] = []
        self.missing: list[str] = []
        self.empty: list[str] = []
        self.undecided: list[str] = []
        self.unreadable: list[str] = []
        # 回答者の照合（#1161）——終了コードに数えない報告
        self.respondents: list[str] = []
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
    for line, fields in rows:
        where = f"{rel}:{line}"
        if len(fields) != len(expected):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(expected)}）")
            continue
        row = dict(zip(expected, fields))
        decided = {column: cell_state(report, where, column, value, column in MAY_BE_EMPTY.get(rel, set()))
                   for column, value in row.items()}
        pending = pending or ("id" in decided and not decided["id"])
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
    try:
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as e:
        # 128KB を超えるセルなど——表の検査は check-qa-csv.py の仕事で、ここは報告だけなので終了コードを変えない
        report.respondents.append(f"{QA_TABLE}: CSV として読めない（{e}）——回答者を照らしていない（check-qa-csv.py で確かめる）")
        return
    if not rows or rows[0] != qa.COLUMNS:
        report.respondents.append(f"{QA_TABLE}: 見出しの行が決まりと違う——回答者を照らしていない（check-qa-csv.py で確かめる）")
        return
    for line_num, fields in enumerate(rows[1:], start=2):
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
    check_roles(root, report)
    check_nfr(root, report)
    answers = check_stakeholders(root, report)
    if answers is not None:
        check_respondents(root, report, answers)
    elif (root / STAKEHOLDERS).is_file():
        report.respondents.append(f"{STAKEHOLDERS} が決まりに反する・読めないので、回答者を照らしていない")
    return report


def respondent_block(lines: list[str]) -> list[str]:
    """`check` の出力のうち、回答者の照合の報告（見出しから後ろ）。無ければ空。scaffold の関門が、通ったときにも出す。"""
    start = next((i for i, line in enumerate(lines) if line.startswith(RESPONDENT_HEADING)), None)
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
