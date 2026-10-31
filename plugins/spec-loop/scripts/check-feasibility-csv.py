#!/usr/bin/env python3
"""スケジュール（`schedule.csv`）と見積り（`estimate.csv`）が、spec-loop のデータの決まりどおりかを検査する。

usage: python3 check-feasibility-csv.py <schedule.csv> <estimate.csv>

**決まりの正は `references/feasibility-csv.md` である**（このプラグインの中にある）。
下の定数（列・番号の書式・日付の書式・前提の区切り・区分・金額の書式・空を許す列）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-check-feasibility-csv.py` が
`references/feasibility-csv.md` の表と突き合わせて見る**。

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。
ガントチャートの生成（`schedule-to-gantt.py`）と提案書の生成（`build-proposal.py`）も、
**この検査を通った表しか読まない**（読む関数 `read_schedule`・`read_estimate` をここに置く）。

終了コード:

- 0: 2 つとも決まりどおり
- 1: 決まりに反する箇所がある（**全部を 1 行ずつ出す**。最初の 1 件で止めない）
- 2: 中身を検査していない——引数の誤り・読めない・UTF-8 でない・空・
  **書いたパスと大文字小文字だけ違う名前を開く表**（`docs/v2/feasibility/schedule.csv` と書いてディスクが `Feasibility/`。
  `check-qa-csv.py` の `misspelled`。#514）・想定外の例外（128KB を超えるセルの `csv.Error` など。#286）。
  **反する箇所が別のファイルに見つかっても 2 を優先する**（見ていないファイルを「決まりどおり」と言わない）

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **金額・期間が妥当か** | 判断であって一意に決まらない。見積りの検証役（`agents/estimate-checker.md`）が見る |
| **`根拠` が実在するか**（`Q-005` が Q&A 表にあるか） | 書き方が自由で、Q&A の番号とは限らない。検証役が見る |
| **2 つの表どうしの整合**（工程と費用の対応） | 対応の決まりを持っていない |
| **土日・祝日** | 暦はプロジェクトごとに違う |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 書いたパスの綴りの確かめ（`misspelled`。#514）——同じプラグインの `check-qa-csv.py` に 1 つだけ置く
qa = _load("check_qa_csv", "check-qa-csv.py")

SCHEDULE_COLUMNS = ["No", "工程", "開始", "終了", "前提"]
ESTIMATE_COLUMNS = ["No", "区分", "項目", "金額", "根拠"]
# 空を許す列。それ以外は空を許さない（2 つの表で共通）
MAY_BE_EMPTY = {"前提"}

# `\d` は全角の数字にも合うので使わない（check-qa-csv.py と同じ理由）
TASK_NUMBER = re.compile(r"T-[0-9]{3,}")
COST_NUMBER = re.compile(r"E-[0-9]{3,}")
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
SEPARATOR = " / "
CATEGORIES = ["開発費", "運用費（月額）"]
AMOUNT = re.compile(r"[0-9]+")


class Unreadable(Exception):
    """中身を検査していない（終了コード 2）。"""


def read_rows(path: Path, columns: list[str], text: str | None = None) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    """(見出しの問題, [(行番号, 行)]) を返す。読めなければ Unreadable。

    `text` を渡せばファイルを読まずにそれを使う（提案書はタグの時点の中身を `git show` で渡す）。
    """
    if text is None:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as e:
            raise Unreadable(f"{path}: 読めない（{e.strerror}）。中身を検査していない")
        except UnicodeDecodeError:
            raise Unreadable(f"{path}: UTF-8 として読めない。中身を検査していない")
    elif text.startswith("﻿"):
        text = text[1:]
    if not text.strip():
        raise Unreadable(f"{path}: 空のファイル。中身を検査していない")
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader)
    if header != columns:
        return [f"{path}:1: 見出し行が決まりと違う\n    期待: {','.join(columns)}\n    実際: {','.join(header)}"], []
    problems, rows = [], []
    for fields in reader:
        line = reader.line_num
        if not any(f.strip() for f in fields):
            continue
        if len(fields) != len(columns):
            problems.append(f"{path}:{line}: 列の数が {len(fields)}（見出しは {len(columns)}）")
            continue
        rows.append((line, dict(zip(columns, fields))))
    return problems, rows


def parse_date(value: str) -> date | None:
    if not DATE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def common(path: Path, rows: list[tuple[int, dict[str, str]]], columns: list[str], number: re.Pattern[str],
           example: str) -> list[str]:
    """空のセル・番号の書式・番号の重複。"""
    problems = []
    seen: dict[str, int] = {}
    for line, row in rows:
        where = f"{path}:{line}: {row['No'] or '(番号なし)'}"
        for column in columns:
            if column not in MAY_BE_EMPTY and not row[column].strip():
                problems.append(f"{where}: `{column}` が空")
        if row["No"] and not number.fullmatch(row["No"]):
            problems.append(f"{where}: `No` が `{example}` の形でない: {row['No']!r}")
        if row["No"] in seen:
            problems.append(f"{path}:{line}: `No` が {seen[row['No']]} 行目と重複: {row['No']}")
        elif row["No"]:
            seen[row["No"]] = line
    return problems


def check_schedule(path: Path, text: str | None = None) -> tuple[list[str], list[dict[str, str]]]:
    """(問題, 行) を返す。読めなければ Unreadable。"""
    problems, rows = read_rows(path, SCHEDULE_COLUMNS, text)
    problems += common(path, rows, SCHEDULE_COLUMNS, TASK_NUMBER, "T-001")
    by_no = {row["No"]: row for _, row in rows}
    for line, row in rows:
        where = f"{path}:{line}: {row['No'] or '(番号なし)'}"
        start, end = parse_date(row["開始"]), parse_date(row["終了"])
        for column, value in (("開始", start), ("終了", end)):
            if row[column].strip() and value is None:
                problems.append(f"{where}: `{column}` が `YYYY-MM-DD` の日付でない: {row[column]!r}")
        if start and end and end < start:
            problems.append(f"{where}: `終了` が `開始` より前（{row['開始']} → {row['終了']}）")
        if not row["前提"].strip():
            continue
        for before in row["前提"].split(SEPARATOR):
            if before == row["No"]:
                problems.append(f"{where}: `前提` に自分自身がある")
            elif before not in by_no:
                problems.append(f"{where}: `前提` の {before!r} が表に無い（` / ` でつなぐ）")
            else:
                before_end = parse_date(by_no[before]["終了"])
                if start and before_end and start < before_end:
                    problems.append(f"{where}: `前提` の {before} が終わる前（{by_no[before]['終了']}）に始まる（{row['開始']}）")
    problems += cycles(path, rows)
    return problems, [row for _, row in rows]


def cycles(path: Path, rows: list[tuple[int, dict[str, str]]]) -> list[str]:
    """`前提` をたどって自分に戻る工程を返す。自分自身を直接書いた行は上で報告済みなので数えない。

    終了日と同じ日に始めるのは許すので、同じ日の工程どうしの循環は日付の検査を通ってしまう。"""
    edges = {row["No"]: [b for b in row["前提"].split(SEPARATOR) if b and b != row["No"]]
             for _, row in rows if row["No"] and row["前提"].strip()}
    problems = []
    for line, row in rows:
        start = row["No"]
        stack, seen = list(edges.get(start, [])), set()
        while stack:
            current = stack.pop()
            if current == start:
                problems.append(f"{path}:{line}: {start}: `前提` をたどると自分に戻る（循環）")
                break
            if current not in seen:
                seen.add(current)
                stack.extend(edges.get(current, []))
    return problems


def check_estimate(path: Path, text: str | None = None) -> tuple[list[str], list[dict[str, str]]]:
    """(問題, 行) を返す。読めなければ Unreadable。"""
    problems, rows = read_rows(path, ESTIMATE_COLUMNS, text)
    problems += common(path, rows, ESTIMATE_COLUMNS, COST_NUMBER, "E-001")
    for line, row in rows:
        where = f"{path}:{line}: {row['No'] or '(番号なし)'}"
        if row["区分"].strip() and row["区分"] not in CATEGORIES:
            problems.append(f"{where}: `区分` が決まりに無い: {row['区分']!r}")
        if row["金額"].strip() and not AMOUNT.fullmatch(row["金額"]):
            problems.append(f"{where}: `金額` が半角数字だけでない（カンマ・単位・小数を書かない）: {row['金額']!r}")
    return problems, [row for _, row in rows]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.splitlines()[2] if __doc__ else
              f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）", file=sys.stderr)
        return 2
    problems, unreadable, counts = [], [], []
    for path, checker in ((Path(argv[0]), check_schedule), (Path(argv[1]), check_estimate)):
        problem = qa.misspelled(path)
        if problem:  # 区別しないファイルシステムでだけ開ける綴り違いの表を読まない（#514）
            unreadable.append(f"{problem}。中身を検査していない")
            continue
        try:
            found, rows = checker(path)
        except Unreadable as e:
            unreadable.append(str(e))
            continue
        problems += found
        counts.append(f"{path}: {len(rows)} 行")
    for line in unreadable + problems:
        print(line, file=sys.stderr)
    if unreadable:
        return 2
    if problems:
        return 1
    print("OK（" + "・".join(counts) + "）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
