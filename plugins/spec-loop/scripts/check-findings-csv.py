#!/usr/bin/env python3
"""仕様レビューの指摘の表（`spec-review/v<n>-findings.csv`）の形式を検査する（#982）。

usage: python3 check-findings-csv.py <spec-review/v<n>-findings.csv>

**決まりの正は `references/spec-exit.md` の「指摘の表」である**（このプラグインの中にある）。下の定数（列・数える列の値）はその写しで、
振り分けの 6 つの名前は `references/spec-scope.md` の「振り分けの区分」の写しである。**写しがずれていないかはこのリポジトリの
`scripts/test-check-findings-csv.py` が突き合わせて見る**。

渡した指摘の表と、**同じディレクトリの実行の記録（`v<n>.csv`。名前は指摘の表の名前から決める）**を読み、次を見る:

- **見出しの行**が決まりの列と同じ（順・綴り・過不足）。行の列の数が見出しと同じ。
- **数える列の値**が決まった値のどれか——`レビュー`・`判定役`・`重さ`・`確かめたか`・`振り分け`。
- **`振り分け` は振り分けの区分の名前だけ**——`-` は `確かめたか` が `確かめられない` の行だけで、`確かめられない` の行は必ず `-`。
- **`振り分け` が `範囲の外として記録する`・`実装に渡す` の行は、`重さ` が `-`。**
- **`確かめたか` が `確かめられない` の行は、`結果` も `-`**（#986。その回は何もしていない——何が無かったかは `根拠` に書く）。
  `確かめたか` で見る——`確かめた` のまま `振り分け` を `-` にした行に「`結果` を消せ」と案内しないため。
- **`回` が実行の記録の実行の行**（`結果` が `抜けた`／`抜けていない`）を指し、**`日付` がその行の `日付` と同じ**。
- **`指摘` が空でない。**

終了コード:

- 0: 違反なし（見出しの行だけの表も 0）
- 1: 違反がある（全部を出す）
- 2: 判定していない——引数の誤り・名前が `v<n>-findings.csv` でない・ファイルが無い・空のファイル・UTF-8 でない・
  実行の記録が無い／読めない・実行の記録の見出しに `回`・`日付`・`結果` が無い・想定外の例外

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **振り分けが正しいか**（実装に渡すべき指摘を退けた、など） | 判断であって、一意に決まらない |
| **`確かめた` と書いた行で、本当に根拠を開いたか**・`根拠`・`結果` の中身 | 文面の列は自由文。見るのは `指摘` が空でないことと、`確かめられない` の行の `結果` が `-` であることだけ |
| **`結果` が `-` の行の振り分けが `-` か**（逆向き） | ほかの区分の `結果` は自由文で、`-` と書いた誤りを中身の誤りと区別して見ない |
| **手順 4 の表の全行を足したか**（行の落とし） | 表の元は会話にしか無く、比べる相手が無い。指摘が 0 件の実行もあるので、行の無い回を落としとは決められない |
| **同じ回の指摘を 2 度足したか** | 同じ文面の指摘が 2 回目のレビュー・別の判定役から出るのは正当で、重複と区別できない |
| **実行の記録の表そのものの形** | 見るのは `回`・`日付`・`結果` の 3 列だけ |
"""

from __future__ import annotations

import csv
import io
import re
import sys
from datetime import date
from pathlib import Path

USAGE = "usage: python3 check-findings-csv.py <spec-review/v<n>-findings.csv>"

# ---- `references/spec-exit.md` の「指摘の表」の写し
COLUMNS = ["回", "日付", "レビュー", "判定役", "重さ", "確かめたか", "振り分け", "指摘", "根拠", "結果"]
REVIEWS = ("1回目", "2回目", "狭いパス")
JUDGES = ("red-team", "domain-checker", "formal-checker")
WEIGHTS = ("判断が要る", "結果が割れる", "補い", "-")
CONFIRMED = "確かめた"
UNCONFIRMED = "確かめられない"
NONE = "-"
# ---- `references/spec-scope.md` の「振り分けの区分」の写し
CATEGORIES = ("仕様を直す", "共有の Q&A 表に起票する", "内部の Q&A 表に記録する", "範囲の外として記録する", "実装に渡す", "退ける")
# 重さが `-` だけの区分（spec-review の手順 4 の表）
NO_WEIGHT = ("範囲の外として記録する", "実装に渡す")
# ---- 実行の記録（`references/spec-exit.md` の「記録の表」）から読む列と、実行の行の `結果`
RUN_COLUMNS = ("回", "日付", "結果")
RUN_RESULTS = ("抜けた", "抜けていない")

NAME = re.compile(r"^v([1-9][0-9]*)-findings\.csv$")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
NUMBER = re.compile(r"^[1-9][0-9]*$")


class Unreadable(Exception):
    """判定していない（終了コード 2）。"""


def read_csv(path: Path, what: str) -> list[list[str]]:
    if not path.is_file():
        raise Unreadable(f"{what}が無い（ファイルでない）: {path}")
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Unreadable(f"{what}が UTF-8 でない: {path}")
    except OSError as e:
        raise Unreadable(f"{what}が読めない: {path}（{e.strerror}）")
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if not rows:
        raise Unreadable(f"{what}が空（見出しの行も無い）: {path}")
    return rows


def run_rows(path: Path) -> dict[str, str]:
    """実行の記録から、実行の行の `回` → `日付` を返す。"""
    rows = read_csv(path, "実行の記録")
    header = [h.strip() for h in rows[0]]
    missing = [c for c in RUN_COLUMNS if c not in header]
    if missing:
        raise Unreadable(f"実行の記録の見出しに {'・'.join(missing)} が無い: {path}")
    at = {c: header.index(c) for c in RUN_COLUMNS}
    out: dict[str, str] = {}
    for row in rows[1:]:
        if len(row) <= max(at.values()):
            continue
        if row[at["結果"]].strip() in RUN_RESULTS:
            out[row[at["回"]].strip()] = row[at["日付"]].strip()
    return out


def runs_path(findings: Path) -> Path:
    m = NAME.match(findings.name)
    if m is None:
        raise Unreadable(f"指摘の表の名前が v<n>-findings.csv でない: {findings.name}")
    return findings.with_name(f"v{m.group(1)}.csv")


def valid_date(value: str) -> bool:
    if not DATE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def check_row(row: list[str], runs: dict[str, str]) -> list[str]:
    cell = dict(zip(COLUMNS, (v.strip() for v in row)))
    problems: list[str] = []
    no = cell["回"]
    if not NUMBER.match(no):
        problems.append(f"`回` が 1 からの番号でない: {no!r}")
    elif no not in runs:
        problems.append(f"`回` {no} が実行の記録の実行の行（`結果` が {'／'.join(RUN_RESULTS)}）に無い")
    if not valid_date(cell["日付"]):
        problems.append(f"`日付` が YYYY-MM-DD でない: {cell['日付']!r}")
    elif no in runs and runs[no] != cell["日付"]:
        problems.append(f"`日付` {cell['日付']} が実行の記録の回 {no} の日付 {runs[no]!r} と違う")
    for column, allowed in (("レビュー", REVIEWS), ("判定役", JUDGES), ("重さ", WEIGHTS), ("確かめたか", (CONFIRMED, UNCONFIRMED))):
        if cell[column] not in allowed:
            problems.append(f"`{column}` が決まった値でない: {cell[column]!r}（{'／'.join(allowed)}）")
    category = cell["振り分け"]
    if category == NONE:
        if cell["確かめたか"] != UNCONFIRMED:
            problems.append(f"`振り分け` が `-` なのは `確かめたか` が `{UNCONFIRMED}` の行だけ")
    elif category not in CATEGORIES:
        problems.append(f"`振り分け` が振り分けの区分の名前でない: {category!r}（{'／'.join(CATEGORIES)}）")
    elif cell["確かめたか"] == UNCONFIRMED:
        problems.append(f"`確かめたか` が `{UNCONFIRMED}` の行の `振り分け` は `-`（どの区分にも確定しない）: {category!r}")
    if cell["確かめたか"] == UNCONFIRMED and cell["結果"] != NONE:
        problems.append(f"`確かめたか` が `{UNCONFIRMED}` の行の `結果` は `-`（何もしていない。何が無かったかは `根拠` に書く）: {cell['結果']!r}")
    if category in NO_WEIGHT and cell["重さ"] != NONE:
        problems.append(f"`振り分け` が {category} の行の `重さ` は `-`: {cell['重さ']!r}")
    if not cell["指摘"]:
        problems.append("`指摘` が空")
    return problems


def check(findings: Path) -> tuple[int, list[str]]:
    runs = run_rows(runs_path(findings))
    rows = read_csv(findings, "指摘の表")
    header = [h.strip() for h in rows[0]]
    if header != COLUMNS:
        return 1, [f"{findings}:1: 見出しの行が決まりと違う: {','.join(header)}（決まり: {','.join(COLUMNS)}）"]
    lines: list[str] = []
    for number, row in enumerate(rows[1:], start=2):
        if len(row) != len(COLUMNS):
            lines.append(f"{findings}:{number}: 列の数が {len(row)}（見出しは {len(COLUMNS)}）")
            continue
        lines.extend(f"{findings}:{number}: {p}" for p in check_row(row, runs))
    return (1 if lines else 0), lines


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0].startswith("-"):
        print(USAGE, file=sys.stderr)
        return 2
    findings = Path(argv[0])
    try:
        code, lines = check(findings)
    except Unreadable as e:
        print(f"判定していない: {e}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    if code == 0:
        print(f"OK: {findings}（違反なし）")
    else:
        print(f"違反 {len(lines)} 件: {findings}")
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as e:  # 想定外の例外は 0 にしない
        print(f"判定していない（想定外の例外）: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
