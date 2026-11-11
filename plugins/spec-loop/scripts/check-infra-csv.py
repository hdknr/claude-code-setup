#!/usr/bin/env python3
"""システム基盤要件の表（`shared/infra.csv`）を検査し、基盤要件が決まっているかを判定する（#950）。

usage: python3 check-infra-csv.py <版のディレクトリ（docs/v<n>）か重ね合わせた全体（build/merged）>

**決まりの正は `references/tree.md` の「基盤要件」である**（このプラグインの中にある）。下の定数（置き場所・列・必須の項目・状態・
状態ごとの空でよい列・状態と根拠の Q&A の行の状態の対応）はその写しで、**写しがずれていないかはこのリポジトリの
`scripts/test-check-infra-csv.py` が突き合わせて見る**。Q&A の番号の形・状態の名前は `check-qa-csv.py`、非機能要求の番号の形と
未決定の印は `check-design-csv.py`（その先の `check-spec-exit.py`）のものを読む（写さない）。

渡したディレクトリの `shared/infra.csv` を読み、根拠に指した `shared/qa.csv` の行と、水準に指した `shared/nfr.csv` の行を照らして、
見つけたものを **4 つに分けて**出す:

- **形式の違反**——見出しの行が決まりと違う（順・綴り・列の過不足）・列の数・項目が重複・状態の値・根拠の形（共有の表の `Q-` でない。
  内部の表の `D-` も違反——基盤要件は発注者が決める）・根拠が Q&A 表に無い・Q&A 表が無い・**表の状態と根拠の行の状態が対応しない**
  （`決定` ↔ `反映済み`・`暫定` ↔ `暫定反映`・`未決定` ↔ `確認中`）・水準の形（`N-` の番号を `・` で区切る）・水準が非機能要求の表に無い・非機能要求の表が無い
- **未決定**——**表が無い**・必須の項目（言語・DBMS・ホスティング環境）の行が無い・状態が `未決定` の行・`決定`／`暫定` の行の必須の欄が空・
  未決定の印（`TBD`・`未定` など）。**印のあるセルと空のセルは、値の決まりに当てない**——未決定は違反ではない
- **暫定**——状態が `暫定` の行（利用者がまだ確かめていない回答で決めた）
- **読めない**——表が UTF-8 でない・空のファイル・ファイルでない・権限・Q&A 表と非機能要求の表の見出しに `No`・`状態` が無い

**v2 以降は重ね合わせた全体（`merge-versions.py docs build/merged`）に当てる**——版のディレクトリは足した・変えた表しか持たず、
根拠の Q&A の行が前の版にあると「Q&A 表に無い」と出る。

終了コード（ゲートの段ごとの扱いの正は `references/tree.md` の「基盤要件」の「ゲート」）:

- 0: 基盤要件が全部決まっている（違反も未決定も暫定も無い）
- 1: 形式の違反がある（ほかも併せて出す）
- 3: 形式の違反は無いが、未決定がある——**表が無いときも 3**（言語・DBMS・ホスティング環境が決まっていない）
- 4: 形式の違反も未決定も無いが、暫定の行がある
- 2: 判定していない——引数の誤り・ディレクトリが無い・表が読めない・想定外の例外

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。`scaffold.py`・`build-proposal.py` はこれを読み込んで
関門に当てる（`inspect`・`inspect_files`・`Report`・`is_python`）。

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **欄の中身**（その言語・DBMS が要求に合うか・理由が正しいか・費用への影響の額） | 判断であって、一意に決まらない |
| **根拠の Q&A の行が、その項目の質問か**（言語の行が DBMS の質問を指している） | 質問の文の意味は機械で決められない。見るのは在ることと状態だけ |
| **指した水準が決まっているか**（`nfr.csv` の水準の行の未決定） | 水準の行は `check-design-csv.py` が見る。ここは在ることだけ |
| **構成の図があるか・図が新しいか** | 図は drawio で、表の検査の外（図の鮮度は `render-diagrams.py --check`） |
| **印を使わずに書いた未決定**（「あとで決める」） | 言い回しは列挙しきれない。`check-spec-exit.py` と同じ限界 |
| **言語の値の綴りの揺れ**（`Py`・`パイソン`） | `is_python` は `Python` で始まる値（大文字小文字を問わない）だけを Python と読む |
| **綴りだけ違う置き場所**（`Shared/infra.csv`） | 決まりの綴りで探し、無ければ「表が無い」と出す。大文字小文字を区別しないファイルシステムでは開けてしまう |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import re
import sys
from pathlib import Path
from typing import Callable, Mapping

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Q&A の番号の形・状態の名前は `check-qa-csv.py`、非機能要求の番号の形と未決定の印は `check-design-csv.py` のもの（写さない）
qa = _load("check_qa_csv", "check-qa-csv.py")
design = _load("check_design_csv", "check-design-csv.py")

# ---- `references/tree.md` の「基盤要件」の写し
INFRA = "shared/infra.csv"
QA = "shared/qa.csv"
NFR = design.NFR
COLUMNS = ["項目", "決定", "理由", "費用への影響", "水準", "根拠", "状態"]
# 必ず置く項目（無ければ未決定）
REQUIRED_ITEMS = ("言語", "DBMS", "ホスティング環境")
LANGUAGE = "言語"
DECIDED = "決定"
PROVISIONAL = "暫定"
UNDECIDED = "未決定"
STATES = (DECIDED, PROVISIONAL, UNDECIDED)
# 状態 → 空でよい列（ほかの列が空なら未決定）
MAY_BE_EMPTY = {
    DECIDED: {"水準"},
    PROVISIONAL: {"水準"},
    UNDECIDED: {"決定", "理由", "費用への影響", "水準"},
}
# 状態 → 根拠の Q&A の行の状態（`references/qa-csv.md` の「状態」）
QA_STATE = {DECIDED: "反映済み", PROVISIONAL: "暫定反映", UNDECIDED: "確認中"}
# 水準に複数の No を並べるときの区切り
LEVEL_SEPARATOR = "・"

PYTHON = re.compile(r"\s*python(?![a-z])", re.IGNORECASE)


class Unreadable(Exception):
    """表を読めない（判定していない）。"""


class Report:
    def __init__(self) -> None:
        self.violations: list[str] = []
        self.undecided: list[str] = []
        self.provisional: list[str] = []
        self.unreadable: list[str] = []
        self.missing = False
        self.rows = 0
        # 項目 → 決定（状態が `決定` で、決定の欄が決まっている行だけ）
        self.decided: dict[str, str] = {}

    def code(self) -> int:
        if self.unreadable:
            return 2
        if self.violations:
            return 1
        if self.missing or self.undecided:
            return 3
        if self.provisional:
            return 4
        return 0

    def lines(self) -> list[str]:
        out = []
        for title, items in (("読めない", self.unreadable), ("形式の違反", self.violations),
                             ("未決定", self.undecided), ("暫定", self.provisional)):
            if items:
                out.append(f"{title}（{len(items)} 件）:")
                out.extend(f"  {item}" for item in items)
        code = self.code()
        if code == 2:
            out.append("読めない表がある。中身を検査していない（判定していない）")
        elif code == 1:
            out.append(f"形式の違反が {len(self.violations)} 件ある。表を直す（references/tree.md の「基盤要件」）")
        elif code == 3 and self.missing:
            out.append(f"基盤要件の表（{INFRA}）が無い——{'・'.join(REQUIRED_ITEMS)}が決まっていない。"
                       "推測で決めず、feasibility で推奨付きの質問を起票して表を作る（references/tree.md の「基盤要件」）")
        elif code == 3:
            out.append(f"形式の違反は無いが、決まっていない基盤要件が {len(self.undecided)} 件ある。"
                       "推測で埋めず、Q&A 表の回答を待つ（references/tree.md の「基盤要件」）")
        elif code == 4:
            out.append(f"基盤要件に暫定の行が {len(self.provisional)} 件ある——利用者がまだ確かめていない"
                       "（references/tree.md の「基盤要件」の「ゲート」）")
        else:
            out.append(f"OK（{INFRA}（{self.rows} 行）。基盤要件は全部決まっている）")
        return out


def directory_reader(root: Path) -> Callable[[str], str | None]:
    """版のディレクトリか重ね合わせた全体から読む。無ければ None、読めなければ Unreadable。"""
    def read(rel: str) -> str | None:
        path = root / rel
        if not path.is_file():
            if path.exists():
                raise Unreadable(f"{rel}: ファイルでない")
            return None
        try:
            return path.read_text(encoding="utf-8-sig")
        except OSError as e:
            raise Unreadable(f"{rel}: 読めない（{e.strerror}）")
        except UnicodeDecodeError:
            raise Unreadable(f"{rel}: UTF-8 として読めない")
    return read


def files_reader(files: Mapping[str, bytes]) -> Callable[[str], str | None]:
    """重ね合わせた全体のファイル（重ね合わせの根からのパス → 中身）から読む（`build-proposal.py` がタグの時点の全体に当てる）。"""
    def read(rel: str) -> str | None:
        data = files.get(rel)
        if data is None:
            return None
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise Unreadable(f"{rel}: UTF-8 として読めない")
    return read


def rows_of(text: str, rel: str) -> tuple[list[str], list[tuple[int, list[str]]]]:
    if not text.strip():
        raise Unreadable(f"{rel}: 空のファイル")
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader)
    rows = [(reader.line_num, fields) for fields in reader if any(f.strip() for f in fields)]
    return header, rows


def column_values(read: Callable[[str], str | None], rel: str, key: str, value: str | None) -> dict[str, str] | None:
    """表の `key` の列 → `value` の列（`value` が None なら空）。表が無ければ None。見出しに列が無ければ Unreadable。"""
    text = read(rel)
    if text is None:
        return None
    header, rows = rows_of(text, rel)
    if key not in header or (value is not None and value not in header):
        wanted = "・".join(name for name in (key, value) if name)
        raise Unreadable(f"{rel}:1: 見出しに {wanted} の列が無い（表の決まりの検査を先に通す）")
    at = header.index(key)
    by = header.index(value) if value is not None else None
    out: dict[str, str] = {}
    for _, fields in rows:
        if len(fields) > at and fields[at].strip():
            out.setdefault(fields[at].strip(), fields[by].strip() if by is not None and len(fields) > by else "")
    return out


def cell_state(report: Report, where: str, column: str, value: str, may_be_empty: bool) -> bool:
    """セルが決まっているか。空・印なら未決定に足して False（値の決まりに当てない）。"""
    hits = design.markers(value)
    if hits:
        report.undecided.append(f"{where}: {column} に未決定の印（{'・'.join(hits)}）: {value.strip()!r}")
        return False
    if not value.strip():
        if not may_be_empty:
            report.undecided.append(f"{where}: {column} が空")
        return False
    return True


def check_rows(read: Callable[[str], str | None], report: Report) -> None:
    text = read(INFRA)
    if text is None:
        report.missing = True
        return
    header, rows = rows_of(text, INFRA)
    if header != COLUMNS:
        report.violations.append(f"{INFRA}:1: 見出しの行が決まりと違う（期待: {','.join(COLUMNS)} ／ 実際: {','.join(header)}）")
        return
    answers: dict[str, str] | None | bool = False  # 読むまでは False（根拠を指す行が無ければ Q&A 表を読まない）
    levels: dict[str, str] | None | bool = False
    items: dict[str, int] = {}
    for line, fields in rows:
        where = f"{INFRA}:{line}"
        if len(fields) != len(COLUMNS):
            report.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(COLUMNS)}）")
            continue
        row = dict(zip(COLUMNS, fields))
        state = row["状態"].strip()
        state_known = cell_state(report, where, "状態", row["状態"], False)
        if state_known and state not in STATES:
            report.violations.append(f"{where}: 状態 が {'・'.join(STATES)} のどれでもない: {state!r}")
            state_known = False
        empty_ok = MAY_BE_EMPTY[state] if state_known else MAY_BE_EMPTY[UNDECIDED]
        item = row["項目"].strip()
        if cell_state(report, where, "項目", row["項目"], False):
            if item in items:
                report.violations.append(f"{where}: 項目 が {items[item]} 行目と重複: {item}")
            else:
                items[item] = line
        decided = {column: cell_state(report, where, column, row[column], column in empty_ok)
                   for column in ("決定", "理由", "費用への影響")}
        if decided["決定"] and state_known and state == DECIDED and item:
            report.decided.setdefault(item, row["決定"].strip())
        if state_known and state == UNDECIDED:
            report.undecided.append(f"{where}: {item or '(項目なし)'} が未決定（根拠 {row['根拠'].strip() or '(なし)'} の回答待ち）")
        if state_known and state == PROVISIONAL:
            report.provisional.append(f"{where}: {item or '(項目なし)'} が暫定（根拠 {row['根拠'].strip() or '(なし)'} の確認待ち）: "
                                      f"{row['決定'].strip()!r}")
        # 根拠: 共有の Q&A 表の行で、その行の状態が表の状態と対応する
        if cell_state(report, where, "根拠", row["根拠"], False):
            number = row["根拠"].strip()
            if qa.is_internal_number(number):
                report.violations.append(f"{where}: 根拠 が内部の Q&A 表の番号: {number!r}——基盤要件は発注者が決めるので、"
                                         f"共有の Q&A 表（{QA}）に起票した番号を指す")
            elif not qa.NUMBER.fullmatch(number):
                report.violations.append(f"{where}: 根拠 が共有の Q&A 表の番号（Q-001・Q-F-001）の形でない: {number!r}")
            else:
                if answers is False:
                    answers = column_values(read, QA, "No", "状態")
                if answers is None:
                    report.violations.append(f"{where}: 根拠 {number} を照らす Q&A 表（{QA}）が無い")
                elif number not in answers:
                    report.violations.append(f"{where}: 根拠 {number} が Q&A 表（{QA}）に無い")
                elif state_known and answers[number] != QA_STATE[state]:
                    report.violations.append(f"{where}: 状態 {state!r} なのに、根拠 {number} の Q&A の状態が {answers[number]!r}"
                                             f"（状態 {state!r} なら {QA_STATE[state]!r}）")
        # 水準: 非機能要求の表の No を `・` で区切る
        if cell_state(report, where, "水準", row["水準"], "水準" in empty_ok):
            for number in (part.strip() for part in row["水準"].split(LEVEL_SEPARATOR)):
                if not design.NFR_NUMBER.fullmatch(number):
                    report.violations.append(f"{where}: 水準 が非機能要求の番号（N-001。複数は「{LEVEL_SEPARATOR}」で区切る）の形でない: "
                                             f"{number!r}")
                    continue
                if levels is False:
                    levels = column_values(read, NFR, "No", None)
                if levels is None:
                    report.violations.append(f"{where}: 水準 {number} を照らす非機能要求の表（{NFR}）が無い")
                elif number not in levels:
                    report.violations.append(f"{where}: 水準 {number} が非機能要求の表（{NFR}）に無い")
    for item in REQUIRED_ITEMS:
        if item not in items:
            report.undecided.append(f"{INFRA}: 必ず置く項目 {item!r} の行が無い")
    report.rows = len(rows)


def inspect_with(read: Callable[[str], str | None]) -> Report:
    report = Report()
    try:
        check_rows(read, report)
    except Unreadable as e:
        report.unreadable.append(str(e))
    return report


def inspect(root: Path) -> Report:
    """`root`（版のディレクトリか重ね合わせた全体）の基盤要件の表を検査する。"""
    return inspect_with(directory_reader(root))


def inspect_files(files: Mapping[str, bytes]) -> Report:
    """重ね合わせた全体のファイル（根からのパス → 中身）の基盤要件の表を検査する。"""
    return inspect_with(files_reader(files))


def is_python(value: str) -> bool:
    """言語の決定が Python か（`Python`・`Python 3.12`・`python3`。大文字小文字を問わず `Python` で始まる値）。"""
    return PYTHON.match(value) is not None


def check(root: Path) -> tuple[int, list[str]]:
    report = inspect(root)
    return report.code(), report.lines()


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
