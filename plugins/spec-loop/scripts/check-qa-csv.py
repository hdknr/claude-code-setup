#!/usr/bin/env python3
"""Q&A 表（共有の `shared/qa.csv` と内部の `spec/qa-dev.csv`）が、spec-loop のデータの決まりどおりかを検査する。

usage: python3 check-qa-csv.py <qa.csv | qa-dev.csv>

**決まりの正は `references/qa-csv.md` である**（このプラグインの中にある）。
このスクリプトは、そこに書いた決まりのうち**答えが一意に決まるもの**だけを機械で見る。
下の定数（列・起票元・状態・反映した状態・「まだ無い」の印・空を許す列・費用付きの質問の起票元・番号の桁・起票元の括弧・選択肢のラベル／数／区切り・
推奨しない印・内部の表の名前と番号・内部の表で使わない状態・暫定の回答の印）は
その写しで、**写しがずれていないかは
このリポジトリの `scripts/test-check-qa-csv.py` が `references/qa-csv.md` の表と突き合わせて見る**。

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。

**どちらの層の表かは、ファイルの名前で決める**——`qa-dev.csv` なら内部の層（番号は `D-`、`暫定反映` を使わない）、
それ以外は共有の層（番号は `Q-`）。照合が一時ファイルに写して読むときも、共有の表は `qa.csv` の名前のまま写す。

判定:

- 決まりに反する箇所があれば、**全部を 1 行ずつ出して**非ゼロ（1）で終わる（最初の 1 件で止めない）。
- ファイルが読めない・UTF-8 でない・空のときは 2 で終わる（**中身を検査していない**）。
- 反する箇所が無ければ 0 で終わり、検査した行数を出す。

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **質問・回答の中身** | 「利用者が答えられる言葉か」「回答が選択肢のどれかを選んでいるか」は判断であって、一意に決まらない |
| **推奨の理由の中身・質問がどちらの層に属するか** | 理由が妥当か・利用者に見える結果が変わるかは判断である（線は `references/spec-scope.md`）。見るのは推奨のラベルが選択肢にあり、理由が空でないことまで |
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

COLUMNS = ["No", "起票元", "質問", "選択肢", "推奨", "推奨の理由", "回答", "反映先", "状態", "費用への影響"]
# 前の形（spec-loop 0.17.0 まで）の見出しには推奨の 2 列が無い。見出しが違うときは移行の手順を指す
MIGRATION = "references/tree.md の「Q&A 表を移す」"
SOURCES = ["要求確定", "仕様レビュー", "実現性・コスト", "開発"]
STATES = ["確認中", "暫定反映", "反映済み"]
# 回答を仕様に反映し終え、利用者の確認も済んだ状態。**これ以外の状態の行は、レビュー会で利用者に見せる**
# （`qa-to-pptx.py` はこの定数で絞る——状態の名前を写さないため）。
DONE = "反映済み"
# 推奨案などを暫定で採って仕様に反映したが、利用者の確認がまだの状態
PROVISIONAL = "暫定反映"
# 仕様に反映した状態。**この 2 つ以外の行は、仕様への反映が残っている**
# （`check-spec-exit.py`・`scaffold.py` はこの定数で絞る。列挙の外の状態は「残っている」側に倒れる）。
# どちらも `回答` と `反映先` を求める
REFLECTED = (DONE, PROVISIONAL)
assert set(REFLECTED) <= set(STATES)

# 内部の層の表（開発者が決めて記録する質問。レビュー会の資料に載せない）。`shared/` の外に置く
INTERNAL_NAME = "qa-dev.csv"
# 内部の表で使わない状態——確かめる利用者がいないので、暫定で採ることが無い
INTERNAL_FORBIDDEN = {PROVISIONAL}
assert INTERNAL_FORBIDDEN <= set(STATES)

# `反映済み` の行の `回答` にこの語があれば、利用者が確かめていない暫定の回答として扱う（`is_provisional`）
PROVISIONAL_ANSWER = "暫定で採用"
# 後に活用が続く書き方（`暫定で採用しない`・`暫定で採用していた`・`暫定で採用された`）は印に数えない
PROVISIONAL_MARK = re.compile(re.escape(PROVISIONAL_ANSWER) + "(?![しさすせれ])")

NO_ANSWER = "未回答"
NO_TARGET = "—"
# 推奨しない質問の `推奨`。空と区別する（理由は `推奨の理由` に書く）
NO_RECOMMENDATION = "なし"
# 空を許す列。それ以外は空を許さない。
MAY_BE_EMPTY = {"費用への影響"}
# 費用付きの質問を起票する起票元。この起票元の行だけは `費用への影響` を空にしない
COST_SOURCE = "実現性・コスト"
assert COST_SOURCE in SOURCES

# `\d` は全角や他の文字体系の数字にも合い、`Q-001` と `Q-００１` が別の番号になるので使わない
NUMBER = re.compile(r"Q-[0-9]{3,}")
INTERNAL_NUMBER = re.compile(r"D-[0-9]{3,}")
# `仕様レビュー` または `仕様レビュー（Red Team）`
DETAIL_OPEN, DETAIL_CLOSE = "（", "）"
SOURCE = re.compile(rf"(?P<name>[^{DETAIL_OPEN}]+)(?:{DETAIL_OPEN}.+{DETAIL_CLOSE})?")
OPTION_LABEL = "[A-Z]"
OPTION = re.compile(rf"(?P<label>{OPTION_LABEL}): \S.*")
OPTION_SEPARATOR = " / "
MIN_OPTIONS = 2


def is_internal(path: Path) -> bool:
    return path.name == INTERNAL_NAME


def is_internal_number(number: str) -> bool:
    """番号（`D-001` など）が内部の層の行か。**行の層を番号で決めるのはここだけ**——`merge-versions.py`・
    `diff-versions.py`・`scaffold.py`・`build-proposal.py`・`check-signoff.py` はこれを読む（#353）。"""
    return INTERNAL_NUMBER.fullmatch(number) is not None


def is_provisional(row: dict[str, str]) -> bool:
    """利用者が確かめていない暫定の回答で仕様に反映した行か——`暫定反映`、または `反映済み` で `回答` に `PROVISIONAL_MARK`。
    **行が暫定かを決めるのはここだけ**——`build-proposal.py` はこれを読む（#374）。`確認中` の行は反映していないので暫定ではない。"""
    state = row["状態"].strip()
    return state == PROVISIONAL or (state == DONE and PROVISIONAL_MARK.search(row["回答"]) is not None)


def option_labels(value: str) -> tuple[list[str], str | None]:
    """(ラベルの並び, 決まりに反するときの理由) を返す。"""
    options = value.split(OPTION_SEPARATOR)
    if len(options) < MIN_OPTIONS:
        return [], f"選択肢が {MIN_OPTIONS} つ未満（` / ` でつなぐ）: {value!r}"
    labels = []
    for option in options:
        m = OPTION.fullmatch(option)
        if not m:
            return [], f"選択肢が `A: …` の形でない: {option!r}"
        labels.append(m["label"])
    if len(set(labels)) != len(labels):
        return [], f"選択肢のラベルが重複している: {value!r}"
    return labels, None


def check_row(row: dict[str, str], internal: bool = False) -> list[str]:
    problems = []
    for column in COLUMNS:
        if column not in MAY_BE_EMPTY and not row[column].strip():
            hint = {"回答": f"（まだなら `{NO_ANSWER}`）", "反映先": f"（まだなら `{NO_TARGET}`）",
                    "推奨": f"（推奨しないなら `{NO_RECOMMENDATION}`）"}
            problems.append(f"`{column}` が空{hint.get(column, '')}")

    number, example = (INTERNAL_NUMBER, "D-001") if internal else (NUMBER, "Q-001")
    if row["No"] and not number.fullmatch(row["No"]):
        problems.append(f"`No` が `{example}` の形でない: {row['No']!r}")

    if row["起票元"]:
        m = SOURCE.fullmatch(row["起票元"])
        if not m or m["name"] not in SOURCES:
            problems.append(f"`起票元` が決まりに無い: {row['起票元']!r}")
        elif m["name"] == COST_SOURCE and not row["費用への影響"].strip():
            problems.append(f"起票元が `{COST_SOURCE}` なのに `費用への影響` が空")

    if row["選択肢"]:
        labels, problem = option_labels(row["選択肢"])
        if problem:
            problems.append(problem)
        elif row["推奨"].strip() and row["推奨"] != NO_RECOMMENDATION and row["推奨"] not in labels:
            problems.append(f"`推奨` が選択肢のラベルでも `{NO_RECOMMENDATION}` でもない: {row['推奨']!r}")

    if row["状態"] and row["状態"] not in STATES:
        problems.append(f"`状態` が決まりに無い: {row['状態']!r}")
    elif internal and row["状態"] in INTERNAL_FORBIDDEN:
        problems.append(f"内部の表で `{row['状態']}` は使わない（確かめる利用者がいない）")

    if row["状態"] in REFLECTED:
        # 空の検査と同じく前後の空白を落として比べる（`未回答 ` を回答ありと読まない）
        if row["回答"].strip() in ("", NO_ANSWER):
            problems.append(f"`{row['状態']}` なのに `回答` が無い")
        if row["反映先"].strip() in ("", NO_TARGET):
            problems.append(f"`{row['状態']}` なのに `反映先` が無い")
    return problems


def check(path: Path) -> tuple[int, list[str]]:
    """(終了コード, 出力する行) を返す。層はファイルの名前で決める（`is_internal`）。"""
    internal = is_internal(path)
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
        if "推奨" not in header:
            errors.append(f"    推奨の列が無い——前の形の表なら、移す手順は {MIGRATION}")
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
        for problem in check_row(row, internal):
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
