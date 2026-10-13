#!/usr/bin/env python3
"""Q&A 表（`qa.csv`）が、spec-loop のデータの決まりどおりかを検査する。

usage: python3 check-qa-csv.py <qa.csv>

**決まりの正は `references/qa-csv.md` である**（このプラグインの中にある）。
このスクリプトは、そこに書いた決まりのうち**答えが一意に決まるもの**だけを機械で見る。
下の定数（列・起票元・状態・`未回答` と `—`・空を許す列・番号の桁・選択肢の区切り）はその写しで、**写しがずれていないかは
このリポジトリの `scripts/test-check-qa-csv.py` が `references/qa-csv.md` の表と突き合わせて見る**。

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。

判定:

- 決まりに反する箇所があれば、**全部を 1 行ずつ出して**非ゼロ（1）で終わる（最初の 1 件で止めない）。
- ファイルが読めない・UTF-8 でない・空のときは 2 で終わる（**中身を検査していない**）。
- 反する箇所が無ければ 0 で終わり、検査した行数を出す。

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **質問・回答の中身** | 「利用者が答えられる言葉か」「回答が選択肢のどれかを選んでいるか」は判断であって、一意に決まらない |
| **`反映先` が実在するか** | 書き方が自由（`決定表 4 行目`）で、ファイルのパスとは限らない |
| **行の並び順・番号の欠番** | 欠番は削除した行の跡として正当にありうる |
| **他のファイルとの整合** | 決定表・見積りがこの表の回答と合っているかは見ない |
"""

from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

COLUMNS = ["No", "起票元", "質問", "選択肢", "回答", "反映先", "状態", "費用への影響"]
SOURCES = ["要求確定", "仕様レビュー", "実現性・コスト", "開発"]
STATES = ["確認中", "反映済み"]

NO_ANSWER = "未回答"
NO_TARGET = "—"
# 空を許す列。それ以外は空を許さない。
MAY_BE_EMPTY = {"費用への影響"}

NUMBER = re.compile(r"Q-\d{3,}")
# `仕様レビュー` または `仕様レビュー（Red Team）`
SOURCE = re.compile(r"(?P<name>[^（]+)(?:（.+）)?")
OPTION = re.compile(r"(?P<label>[A-Z]): \S.*")
OPTION_SEPARATOR = " / "


def check_options(value: str) -> str | None:
    options = value.split(OPTION_SEPARATOR)
    if len(options) < 2:
        return f"選択肢が 2 つ未満（` / ` でつなぐ）: {value!r}"
    labels = []
    for option in options:
        m = OPTION.fullmatch(option)
        if not m:
            return f"選択肢が `A: …` の形でない: {option!r}"
        labels.append(m["label"])
    if len(set(labels)) != len(labels):
        return f"選択肢のラベルが重複している: {value!r}"
    return None


def check_row(row: dict[str, str]) -> list[str]:
    problems = []
    for column in COLUMNS:
        if column not in MAY_BE_EMPTY and not row[column].strip():
            hint = {"回答": f"（まだなら `{NO_ANSWER}`）", "反映先": f"（まだなら `{NO_TARGET}`）"}
            problems.append(f"`{column}` が空{hint.get(column, '')}")

    if row["No"] and not NUMBER.fullmatch(row["No"]):
        problems.append(f"`No` が `Q-001` の形でない: {row['No']!r}")

    if row["起票元"]:
        m = SOURCE.fullmatch(row["起票元"])
        if not m or m["name"] not in SOURCES:
            problems.append(f"`起票元` が決まりに無い: {row['起票元']!r}")

    if row["選択肢"]:
        problem = check_options(row["選択肢"])
        if problem:
            problems.append(problem)

    if row["状態"] and row["状態"] not in STATES:
        problems.append(f"`状態` が決まりに無い: {row['状態']!r}")

    if row["状態"] == "反映済み":
        # 空の検査と同じく前後の空白を落として比べる（`未回答 ` を回答ありと読まない）
        if row["回答"].strip() in ("", NO_ANSWER):
            problems.append("`反映済み` なのに `回答` が無い")
        if row["反映先"].strip() in ("", NO_TARGET):
            problems.append("`反映済み` なのに `反映先` が無い")
    return problems


def check(path: Path) -> tuple[int, list[str]]:
    """(終了コード, 出力する行) を返す。"""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        return 2, [f"{path}: 読めない（{e.strerror}）。中身を検査していない"]
    except UnicodeDecodeError:
        return 2, [f"{path}: UTF-8 として読めない。中身を検査していない"]
    if not text.strip():
        return 2, [f"{path}: 空のファイル。中身を検査していない"]

    # 行に割らずに渡す（csv の文書どおり `newline=""`）。`str.splitlines()` は
    # U+2028 などの改行でない文字でも割るので、Web から貼った質問が 2 行に化ける。
    # 報告する行番号は、ファイル上でその行が終わる行（`line_num`）。
    reader = csv.reader(io.StringIO(text, newline=""))
    header = next(reader)
    errors = []
    if header != COLUMNS:
        errors.append(
            f"{path}:1: 見出し行が決まりと違う\n"
            f"    期待: {','.join(COLUMNS)}\n"
            f"    実際: {','.join(header)}"
        )
        # 見出しが違うと、列の位置で読むことができない
        return 1, errors

    seen: dict[str, int] = {}
    for fields in reader:
        line = reader.line_num
        if not any(f.strip() for f in fields):
            continue  # 空行
        if len(fields) != len(COLUMNS):
            errors.append(f"{path}:{line}: 列の数が {len(fields)}（見出しは {len(COLUMNS)}）")
            continue
        row = dict(zip(COLUMNS, fields))
        for problem in check_row(row):
            errors.append(f"{path}:{line}: {row['No'] or '(番号なし)'}: {problem}")
        if row["No"] in seen:
            errors.append(f"{path}:{line}: `No` が {seen[row['No']]} 行目と重複: {row['No']}")
        elif row["No"]:
            seen[row["No"]] = line

    if errors:
        return 1, errors
    return 0, [f"{path}: OK（{len(seen)} 行）"]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    code, lines = check(Path(argv[0]))
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
