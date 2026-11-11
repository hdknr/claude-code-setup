#!/usr/bin/env python3
"""システム設計書の成果物の表（機能一覧・データモデル・入出力・帳票・権限・バッチ・ジョブと、非機能要求の性能のほかの種類）を検査する。

usage: python3 check-design-csv.py <版のディレクトリ（docs/v<n>）か重ね合わせた全体（build/merged）>

**決まりの正は `references/tree.md` の「システム設計書の成果物」と `references/nfr.md` の「性能のほかの種類」である**（このプラグインの中にある）。
下の定数（表の置き場所・列・空でよい列・決まった値・番号の形・重複させない欄・権限一覧の形・非機能要求の種類）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-check-design-csv.py` が突き合わせて見る**。

渡したディレクトリの `requirements/` と `shared/nfr.csv` を読み、見つけたものを **4 つに分けて**出す（#957）:

- **形式の違反**——見出しの行が決まりと違う（順・綴り・列の過不足。物理設計の列を足した表もここ）・列の数・番号の形・重複・
  決まった値でない・レイアウトの id が入出力の一覧に無い・同じ帳票の id で帳票名が違う・非機能要求の種類の上限と単位の形
- **表が無い**——決まりの表のうち、渡したディレクトリに無いもの。**止めない**（前からの正本は成果物の表を持たない。v2 以降の版のディレクトリは足した表しか持たない）
- **必須の欄が空**——空でよい列のほかの欄が空（要る情報がまだ無い）
- **未決定の印**——セルに `references/spec-exit.md` の未決定の印（`TBD`・`TODO`・`未定`・`要確認`）がある。
  印の判定は `check-spec-exit.py` の `find_markers` を読む（写さない）。**印のあるセルと空のセルは、値の決まりに当てない**——未決定は違反ではない

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
| **表どうしの整合**（データモデルの項目と入出力の項目が合うか・権限一覧の操作が機能一覧にあるか） | 名前の付け方が表ごとに違ってよく、機械で対応を決められない。**例外は入出力のレイアウトの id だけ**（一覧に無い id は落とす） |
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

# ---- `references/tree.md` の「システム設計書の成果物」の写し
FEATURES = "requirements/features.csv"
ENTITIES = "requirements/entities.csv"
IO_LIST = "requirements/io.csv"
IO_LAYOUT = "requirements/io-layout.csv"
REPORTS = "requirements/reports.csv"
JOBS = "requirements/jobs.csv"
ROLES = "requirements/roles.csv"
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
# 順番の列（正の整数）
ORDER_COLUMN = "順番"
# 権限一覧: 1 列目の名前と、ロールの列のセルの値
ROLES_FIRST = "操作"
ROLES_VALUES = ("可", "不可")
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

ALL_TABLES = list(COLUMNS) + [ROLES, NFR]


class Report:
    def __init__(self) -> None:
        self.violations: list[str] = []
        self.missing: list[str] = []
        self.empty: list[str] = []
        self.undecided: list[str] = []
        self.unreadable: list[str] = []
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
    check_roles(root, report)
    check_nfr(root, report)
    return report


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
