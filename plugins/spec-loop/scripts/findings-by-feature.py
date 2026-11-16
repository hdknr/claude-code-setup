#!/usr/bin/env python3
"""仕様レビューの指摘の表（`spec-review/v<n>-findings.csv`）から、機能ごとの指摘の件数を数える（#1045）。

usage: python3 findings-by-feature.py <spec-review/v<n>-findings.csv>...

**指摘が特定の機能に偏っているかを、仕事の切り方（範囲の既定の線・scaffold の `--bundle`）を見直す材料として数える。**
使い方（数をどう返すか）は `references/spec-scope.md` の「回を重ねたときの歯止め」、指摘の表の列と機能の印の書き方は
`references/spec-exit.md` の「指摘の表」を正とする（このプラグインの中にある）。指摘の表の読み方と検査は同梱の `check-findings-csv.py` のもの
（読み込んで使う——写さない）。

渡した表を 1 つずつ `check-findings-csv.py` の検査に当て（違反があれば数えない——2）、全部の表の行を足し合わせて、機能ごとに
合計と振り分けの区分（`spec-scope.md` の 6 つと、確かめられなかった行の `-`）ごとの件数を Markdown の表で出す。

**行を機能に結ぶのは `指摘` と `根拠` の文面の印である**（指摘の表は機能の列を持たない）:

- **`機能: <名前>`**——`spec-scope.md` の起票元の詳細と同じ形。コロンは全角でもよい。名前は、次の区切りの記号の手前か行末まで
  （前後の空白を外す）: `）` `)` `／` `/` `;` `；` `、` `,` `。` `」` と改行。
- **機能の id**——`F-` に 3 桁以上の数字（`references/spec-ir.md`）。ケースの id（`F-001-C1`）は機能 `F-001` に数える。

1 行が 2 つ以上の機能を挙げていれば、その全部に 1 件ずつ数え、その行の数を別に出す。**印の無い行は「（機能を決められない）」の行に数える**——
黙って落とさない。同じ機能を名前と id の両方で書いた行は、別々の機能として 2 つに数える（名前と id を結ばない）。

**出すのは数と機能の名前（か id）だけで、指摘の文面（`指摘`・`根拠`・`結果`）は出さない**——`spec-exit.md` の「指摘の表」が、表の外へ出すのは
区分ごとの件数だけと決めている。

終了コード:

| 値 | 意味 |
| --- | --- |
| 0 | 数えた（行が 1 つも無い表でも 0。印の無い行だけでも 0——決められない行の数が出る） |
| 2 | 数えていない——引数の誤り・表が `check-findings-csv.py` の検査に通らない（読めない・無い・違反がある）・想定外の例外 |

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。

**守ること**:

- **検査に通らない表で数えない**（2）——列のずれた行を別の列として数えない。
- **印の無い行を落とさない**——「（機能を決められない）」に数える。
- **2 つ以上の機能を挙げた行を、その全部に数える**——1 つに寄せない。
- **同じ行に同じ機能を 2 度書いても 1 件に数える。**
- **`指摘` と `根拠` の両方の列から印を拾う。**
- **ケースの id を機能の id に寄せる**——`F-001-C1` は `F-001`。
- **指摘の文面を出力に出さない。**
- **複数の表の行を足し合わせる**——版ごとの表（`v1-findings.csv`・`v2-findings.csv`）を一度に渡せる。

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **印が正しい機能を指しているか** | 印は判定役と呼び出し元が書く文面で、仕様の機能と照らす相手を読まない（`requirements/features.csv` も中間表現も読まない） |
| **名前と id が同じ機能か** | 結ぶ表を読まないので、別の機能として数える |
| **言い換えた名前を同じ機能に寄せるか** | `spec-scope.md` の「言い換えると数が割れる」と同じ——写した名前のまま数える |
| **何件から切り方を見直すか（閾値）** | 決めていない。数を返すのは人（`spec-scope.md`） |
| **同じ指摘を 2 つの表に足したか** | `check-findings-csv.py` と同じく、重複と正当な再指摘を区別できない |
| **区分や重さの偏り以外の傾向**（判定役ごと・レビューの回ごと） | 数えるのは機能 × 振り分けだけ |
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


findings = _load("check_findings_csv", "check-findings-csv.py")
Unreadable = findings.Unreadable

USAGE = "usage: python3 findings-by-feature.py <spec-review/v<n>-findings.csv>..."
EXIT_OK = 0
EXIT_UNCOUNTED = 2

# 印を拾う列（`spec-exit.md` の「指摘の表」）
MARKED = ("指摘", "根拠")
# `機能: <名前>`——名前は区切りの記号の手前まで
NAME_MARK = re.compile(r"機能\s*[:：]\s*([^）)／/;；、,。」\n]+)")
# 機能の id（`F-001`）。ケースの id（`F-001-C1`）の頭も拾う
ID_MARK = re.compile(r"(?<![A-Za-z0-9_-])(F-[0-9]{3,})(?![0-9])")
UNKNOWN = "（機能を決められない）"
# 列の並び: 振り分けの区分の 6 つと、確かめられなかった行の `-`
BUCKETS = (*findings.CATEGORIES, findings.NONE)


def features_of(cell: dict[str, str]) -> list[str]:
    """1 行が挙げた機能（出てきた順・重複なし）。"""
    out: list[str] = []
    for column in MARKED:
        text = cell[column]
        for m in NAME_MARK.finditer(text):
            name = m.group(1).strip()
            if name and name not in out:
                out.append(name)
        for m in ID_MARK.finditer(text):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


def count(tables: list[Path]) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """機能 → 区分 → 件数と、まとめの数を返す。検査に通らない表があれば Unreadable。"""
    per: dict[str, dict[str, int]] = {}
    totals = {"表": 0, "行": 0, "決められない行": 0, "2 つ以上の機能に数えた行": 0}
    for table in tables:
        code, problems = findings.check(table)
        if code != 0:
            raise Unreadable(f"{table} が check-findings-csv.py の検査に通らない（{len(problems)} 件）。数えていない:\n  "
                             + "\n  ".join(problems))
        rows = findings.read_csv(table, "指摘の表")
        totals["表"] += 1
        for row in rows[1:]:
            cell = dict(zip(findings.COLUMNS, (v.strip() for v in row)))
            totals["行"] += 1
            names = features_of(cell)
            if not names:
                names = [UNKNOWN]
                totals["決められない行"] += 1
            elif len(names) > 1:
                totals["2 つ以上の機能に数えた行"] += 1
            for name in names:
                per.setdefault(name, {b: 0 for b in BUCKETS})[cell["振り分け"]] += 1
    return per, totals


def render(per: dict[str, dict[str, int]], totals: dict[str, int]) -> list[str]:
    lines = ["| 機能 | 合計 | " + " | ".join(BUCKETS) + " |", "| --- | --- | " + " | ".join("---" for _ in BUCKETS) + " |"]
    known = sorted((n for n in per if n != UNKNOWN), key=lambda n: (-sum(per[n].values()), n))
    for name in known + ([UNKNOWN] if UNKNOWN in per else []):
        cells = per[name]
        lines.append(f"| {name} | {sum(cells.values())} | " + " | ".join(str(cells[b]) for b in BUCKETS) + " |")
    lines.append("")
    lines.append("・".join(f"{k}: {v}" for k, v in totals.items()))
    return lines


def main(argv: list[str]) -> int:
    if not argv or any(a.startswith("-") for a in argv):
        print(USAGE, file=sys.stderr)
        return EXIT_UNCOUNTED
    try:
        per, totals = count([Path(a) for a in argv])
    except Unreadable as e:
        print(f"数えていない: {e}", file=sys.stderr)
        return EXIT_UNCOUNTED
    for line in render(per, totals):
        print(line)
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except BaseException as e:  # 想定外の例外は 0 にしない
        print(f"数えていない（想定外の例外）: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(EXIT_UNCOUNTED)
