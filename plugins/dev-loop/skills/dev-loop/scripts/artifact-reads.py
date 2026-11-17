#!/usr/bin/env python3
"""dev-loop の周が読んだ spec-loop の成果物を、計画ファイルから集めて数える（#1157）。

    python3 artifact-reads.py <計画ファイルかディレクトリ> [...] [--all-artifacts <ファイル>]

spec-loop から来た Issue の周は、手順 2（文脈収集）と手順 4（実装）で開いて読んだ成果物のファイルを、計画ファイルに 1 ファイル 1 行で書く
（いつ・何を書くかは `references/spec-gap.md` の「読んだ成果物を記録する」）。このスクリプトはその行を集め、成果物ごとに
**読んだ周の数**と、**その周の結果**（起票の数・関門の指摘の数）を並べる。**測るだけで、閾値も削る候補も決めない**——判断は人がする。

## 行の形（ここが原本）

行頭から、装飾（太字・字下げ）を付けずに、次のどちらか:

    - 読んだ成果物: `<パス>`
    - 読んだ成果物: なし

- **`<パス>`** は Issue の本文が書いた形のまま（`build/merged/spec/spec_ir.json`・`scaffold/tests/test_order.py` など）、バッククォートで囲む。
  先頭の `./` は外して数える。**1 行に 1 つ。** 後ろに空白か `（` で注記を続けてよい（``- 読んだ成果物: `x.md`（手順 4）``）。
- **`なし`** は、本文が指すファイルを 1 つも開かなかった周の行（1 本だけ。パスの行と混ぜない）。
- **1 周で同じパスを 2 度書いても 1 件**に数える。コードブロック（``` か ~~~ で囲んだ範囲）の中の行は数えない。

## 何を並べるか

成果物ごとに: 読んだ周の数・その周の起票の合計（行 `- この周の起票: N 件`。`SKILL.md` 手順 8）・
その周の関門の指摘の合計（`dev-loop-gates` のブロックの `関門:` の行の `反証=`・`指摘=`。`check-gates.py` の「記録の形」）。
起票の行・関門の記録の無い周は 0 に数え、その周の数を別の行に出す。`--all-artifacts` に挙げたパス（1 行 1 つ。空行と `#` で始まる行は読まない）は、
どの周にも無ければ読んだ周 0 の行で出す——一度も読まれない成果物である。

## 終了コード

- **0**: 数えた。
- **1**: 数えたが、形に合わない行があった——ファイルと行番号を出す（その行は数えない）。形に合わない行は、行頭の飾りを外すと
  `読んだ成果物` で始まり直後がコロンなのに、上の形でないもの（装飾つき・字下げ・バッククォートの無いパス・空のパス）と、`なし` とパスを同じファイルに書いたもの。
- **2**: 数えていない——引数の誤り・無いパス・計画ファイル（`*.md`）が 1 本も無い・`--all-artifacts` のファイルが読めない。

## 守ること

- **読むだけ**——ファイルを書かない・消さない。外へ繋がない。標準ライブラリだけで、リポジトリの外で単体で動く。
- **黙って落とさない**——形に合わない行は名指しし、記録の無い周（起票の行・関門の記録）は数を出す。

## 守らないもの

- **申告の漏れ**——行を書き忘れた周は、読まなかった周と区別できない（記録のある周だけを数える）。
- **因果**——読んだ成果物と周の結果を並べるだけで、指摘がどの成果物に起因したかは分けない。
- **マージ後の欠陥・spec-gap の差し戻し**——計画ファイルに件数の行が無いので並べない。
- **同じ成果物の別名**——`build/merged/x` と `scaffold/refs/x` は別の成果物として数える（写しかどうかを見ない）。
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

LINE = re.compile(r"^- 読んだ成果物: (?:`(?P<path>[^`\s][^`]*)`|(?P<none>なし))(?=$|[\s（])")
CANDIDATE = re.compile(r"^[\s>*_\-+]*読んだ成果物\s*(?:\*\*|__)?\s*[:：]")
COUNT = re.compile(r"^- この周の起票: ([0-9]+) 件")
GATE = re.compile(r"^関門: .*?(?:反証|指摘)=([0-9]+)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
GATES_OPEN = re.compile(r"^\s*```dev-loop-gates\s*$")

USAGE = "usage: artifact-reads.py <計画ファイルかディレクトリ> [...] [--all-artifacts <ファイル>]"


def normalize(path: str) -> str:
    while path.startswith("./"):
        path = path[2:]
    return path


def read_plan(path: Path) -> dict:
    """1 本の計画ファイルから、読んだ成果物・なし・起票・関門の指摘・形に合わない行を取る。"""
    reads: list[str] = []
    none = False
    count = None
    gates = None
    bad: list[int] = []
    fence = None
    in_gates = False
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        m = FENCE.match(line)
        if fence is None and m:
            fence = m.group(1)
            if GATES_OPEN.match(line):
                in_gates = True
                gates = gates or 0
            continue
        if fence is not None:
            if line.strip().startswith(fence) and line.strip().strip(fence[0]) == "":
                fence = None
                in_gates = False
                continue
            if in_gates:
                g = GATE.match(line.strip())
                if g:
                    gates += int(g.group(1))
            continue
        c = COUNT.match(line)
        if c and count is None:
            count = int(c.group(1))
        r = LINE.match(line)
        if r:
            if r.group("none"):
                none = True
            else:
                p = normalize(r.group("path"))
                if p not in reads:
                    reads.append(p)
            continue
        if CANDIDATE.match(line):
            bad.append(no)
    if none and reads:
        bad.append(0)
    return {"reads": reads, "none": none, "count": count, "gates": gates, "bad": bad}


def collect(args: list[str]) -> list[Path] | None:
    plans: list[Path] = []
    for arg in args:
        p = Path(arg)
        if p.is_dir():
            plans.extend(sorted(q for q in p.rglob("*.md") if q.is_file()))
        elif p.is_file():
            plans.append(p)
        else:
            print(f"無いパス: {arg}（数えていない）", file=sys.stderr)
            return None
    seen: list[Path] = []
    for p in plans:
        if p.resolve() not in [s.resolve() for s in seen]:
            seen.append(p)
    return seen


def main(argv: list[str]) -> int:
    expected: list[str] = []
    rest: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--all-artifacts":
            if i + 1 >= len(argv):
                print(USAGE, file=sys.stderr)
                return 2
            try:
                text = Path(argv[i + 1]).read_text(encoding="utf-8")
            except OSError as e:
                print(f"--all-artifacts のファイルが読めない: {e}（数えていない）", file=sys.stderr)
                return 2
            for line in text.splitlines():
                s = line.strip()
                if s and not s.startswith("#"):
                    expected.append(normalize(s))
            i += 2
            continue
        if a.startswith("-"):
            print(USAGE, file=sys.stderr)
            return 2
        rest.append(a)
        i += 1
    if not rest:
        print(USAGE, file=sys.stderr)
        return 2
    plans = collect(rest)
    if plans is None:
        return 2
    if not plans:
        print("計画ファイル（*.md）が 1 本も無い（数えていない）", file=sys.stderr)
        return 2

    cycles: Counter[str] = Counter()
    counts: Counter[str] = Counter()
    gates: Counter[str] = Counter()
    recorded = 0
    nones = 0
    no_count = 0
    no_gates = 0
    bad: list[str] = []
    for plan in plans:
        info = read_plan(plan)
        for no in info["bad"]:
            where = "なしとパスを両方書いている" if no == 0 else f"{no} 行目"
            bad.append(f"{plan}: {where}")
        if not info["reads"] and not info["none"]:
            continue
        recorded += 1
        if info["none"] and not info["reads"]:
            nones += 1
        if info["count"] is None:
            no_count += 1
        if info["gates"] is None:
            no_gates += 1
        for p in info["reads"]:
            cycles[p] += 1
            counts[p] += info["count"] or 0
            gates[p] += info["gates"] or 0

    names = list(cycles)
    for p in expected:
        if p not in cycles and p not in names:
            names.append(p)
    names.sort(key=lambda n: (-cycles[n], n))

    print(f"計画ファイル: {len(plans)} 本・読んだ成果物の記録のある周: {recorded} 本（うち `なし`: {nones} 本）")
    print()
    print("| 成果物 | 読んだ周 | その周の起票 | その周の関門の指摘 |")
    print("| --- | --- | --- | --- |")
    for n in names:
        print(f"| `{n}` | {cycles[n]} | {counts[n]} | {gates[n]} |")
    print()
    print(f"起票の行が無い周: {no_count}")
    print(f"関門の記録が無い周: {no_gates}")
    if expected:
        never = [p for p in expected if cycles[p] == 0]
        print(f"一度も読まれない成果物: {len(never)}")
    if bad:
        print()
        print(f"形に合わない行（数えていない）: {len(bad)}")
        for b in bad:
            print(f"  {b}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
