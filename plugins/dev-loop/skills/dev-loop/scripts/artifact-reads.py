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
  前後の空白と先頭の `./` は外して数える。**1 行に 1 つ**——注記は後ろに空白か `（` で続けてよい（``- 読んだ成果物: `x.md`（手順 4）``）が、注記にバッククォートを置かない（2 つ目のパスと区別できない）。
- **`なし`** は、本文が指すファイルを 1 つも開かなかった周の行（1 本だけ。パスの行と混ぜない）。
- **1 周で同じパスを 2 度書いても 1 件**に数える。コードブロック（3 つ以上の ``` か ~~~ で囲んだ範囲。閉じるのは同じ文字が同じ数以上だけの行）の中の行は数えない。
  **開きの印は字下げを外して見る**——リストの中のコードブロックの例を数えないため（`check-gates.py` は字下げを外さない。ここだけ違う）。

## 何を並べるか

成果物ごとに: 読んだ周の数・その周の起票の合計（行 `- この周の起票: N 件`。`SKILL.md` 手順 8）・
その周の関門の指摘の合計（`dev-loop-gates` のブロックの関門の行（各パス・狭いパス・当て直し）の `反証=`・`指摘=`。
**ブロックと行の読み方は同じ場所の `check-gates.py`（`FENCE_OPEN`・`gate_block`・`LINE_FORMS`）を読み込む**——写さない。行頭の飾りとコードブロックの読み方も同じファイルの `DECOR`・`FENCE_ANY`・`closes`）。
起票の行・関門の記録の無い周は 0 に数え、その周の数を別の行に出す。`--all-artifacts` に挙げたパス（1 行 1 つ。空行と `#` で始まる行は読まない）は、
どの周にも無ければ読んだ周 0 の行で出す——一度も読まれない成果物である。

## 終了コード

- **0**: 数えた。
- **1**: 数えたが、形に合わない行があった——ファイルと行番号を出す（その行は数えない）。形に合わない行は、行頭の飾り（字下げ・リストの印・番号・チェックボックス・見出し・引用・強調）を外すと
  `読んだ成果物` で始まり、直後（空白を除く）がコロン（全角も）・括弧・`=`・バッククォートか、直後が空白で、その後ろの空白までの語が `なし`（括弧が続いてもよい）かパスのような語なのに、
  上の形でないもの（直後がほかの文字か行末、空白の後の語が `なし` でもパスのような語でもなければ散文・見出しと読む）
  （装飾つき・字下げ・コロンの無いラベル・コロンもバッククォートも無いラベル・括弧つきのラベル・全角のコロン・バッククォートの無いパス・空のパス・1 行に 2 つのパス）。
  **パスのような語**は、空白までの語（引用符・括弧・日本語を含んでよい）が英数字と `.`・`/`・`_` のどれかを含み、1 文字ずつの略語（`e.g.`）でも数・版（`1.5`・`v2.0`・`V2.0`・`1.5倍`）でもないもの
  （`a.md`・`spec_ir`・`要求.md`・`"a.md"`・`docs/a.md.` は記録の行、`e.g. これ`・`1.5 倍`・`v2.0` は散文。#1241）。`.`・`/`・`_` の無い語（`PR`・`2d190c9`・`README`）は散文と読む——
  バッククォートの無いパス `Makefile` は黙って落ちる（下の「守らないもの」）。
  ほかに、ファイルごとに次も名指しして 1 にする: `なし` とパスを同じファイルに書いた（`なし` の行番号。パスの行は数える）・閉じないコードブロックがある（開きの行番号。その後ろは読んでいない）・
  関門の記録が読めない（ブロックが 2 つある・閉じていない・`LINE_FORMS` のどれにも当たらない行がある。その周の関門の指摘は「記録が無い」に数える）。
- **2**: 数えていない——引数の誤り・無いパス・計画ファイル（`*.md`）が 1 本も無い・読めない計画ファイル（UTF-8 でない・権限）・読めないディレクトリ（その下を黙って落とさない）・`--all-artifacts` のファイルが読めない（UTF-8 でないを含む）・
  `check-gates.py` を読み込めない（使う名前が無いときも）。

## 守ること

- **読むだけ**——ファイルを書かない・消さない。外へ繋がない。標準ライブラリと同じ場所の `check-gates.py` だけで、リポジトリの外で単体で動く。
- **黙って落とさない**——形に合わない行は名指しし、記録の無い周（起票の行・関門の記録）は数を出す。

## 守らないもの

- **申告の漏れ**——行を書き忘れた周は、読まなかった周と区別できない（記録のある周だけを数える）。
- **因果**——読んだ成果物と周の結果を並べるだけで、指摘がどの成果物に起因したかは分けない。
- **マージ後の欠陥・spec-gap の差し戻し**——計画ファイルに件数の行が無いので並べない。
- **印の無いパス**——コロンもバッククォートも落とし、`.`・`/`・`_` も無いパス（`- 読んだ成果物 Makefile`）は散文と区別できず、名指ししない。
- **同じ成果物の別名**——`build/merged/x` と `scaffold/refs/x` は別の成果物として数える（写しかどうかを見ない）。
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from collections import Counter
from pathlib import Path

LINE = re.compile(r"^- 読んだ成果物: (?:`(?P<path>[^`\s][^`]*)`|(?P<none>なし))(?P<rest>$|[\s（][^`]*$)")
LABEL = re.compile(r"^`?読んだ成果物(?:`|\*\*|__)*")
STARTS = ":：（(=`"  # ラベルの直後がこれで始まれば、記録の行を書こうとした形（ほかは散文）
# ラベルの直後が空白なら、その後ろの空白までの語が `なし` か、パスのような語なら、コロンもバッククォートも落とした記録の行（#1157 の R1・#1241 の R3）
SPACED = re.compile(r"\s+(?P<word>\S+)")
NONE_WORD = re.compile(r"なし(?:[（(].*)?")
# パスのような語でないもの——1 文字ずつの略語（`e.g.`）と、数・版（`1.5`・`v2.0`・`1.5倍`）は散文（#1241 の R4）
PROSE_WORD = re.compile(r"(?:[A-Za-z]\.){2,}|[vV]?[0-9]+(?:\.[0-9]+)*(?:[^\x00-\x7f].*)?")
COUNT = re.compile(r"^- この周の起票: ([0-9]+) 件")
NEEDED = ("DECOR", "FENCE_ANY", "FENCE_OPEN", "LINE_FORMS", "closes", "gate_block", "Malformed")

USAGE = "usage: artifact-reads.py <計画ファイルかディレクトリ> [...] [--all-artifacts <ファイル>]"


def load_gates():
    """関門の記録の読み方（同じ場所の `check-gates.py` の `gate_block`・`LINE_FORMS`・コードブロックの読み方）。写しを作らない。"""
    path = Path(__file__).resolve().parent / "check-gates.py"
    spec = importlib.util.spec_from_file_location("dev_loop_check_gates", path)
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True  # 読むだけ——読み込みで __pycache__ を書かない
    sys.modules[spec.name] = mod  # dataclass が自分のモジュールを引くため
    spec.loader.exec_module(mod)
    missing = [n for n in NEEDED if not hasattr(mod, n)]
    if missing:
        raise AttributeError(f"{', '.join(missing)} が無い")
    return mod


def normalize(path: str) -> str:
    path = path.strip()
    while path.startswith("./"):
        path = path[2:]
    return path


def looks_like(line: str, gates) -> bool:
    """行頭の飾り（`check-gates.py` の `DECOR`）を外すと `読んだ成果物` で始まり、直後（空白を除く）がコロン・括弧・`=`・バッククォートか、直後が空白と `なし` かパスのような語か。"""
    t = line
    while True:
        m = gates.DECOR.match(t)
        if not m or not m.group(0):
            break
        t = t[m.end():]
    m = LABEL.match(t)
    if not m:
        return False
    after = t[m.end():].strip()
    s = SPACED.match(t, m.end())
    if s and (NONE_WORD.fullmatch(s.group("word")) or is_pathlike(s.group("word"))):
        return True
    return bool(after) and after[0] in STARTS


def is_pathlike(word: str) -> bool:
    """空白の後の語が、パスのような語か——英数字と `.`・`/`・`_` のどれかを含み、略語・数・版でない。"""
    return bool(re.search(r"[A-Za-z0-9]", word)) and bool(re.search(r"[./_]", word)) and not PROSE_WORD.fullmatch(word)


def has_gate_block(text: str, gates) -> bool:
    """コードブロックの外で `dev-loop-gates` のブロックを開いているか（ほかのブロックの中の例は数えない。読み方は `gate_block` と同じ）。"""
    fence = None
    for line in text.splitlines():
        if fence is None:
            if gates.FENCE_OPEN.match(line):
                return True
            m = gates.FENCE_ANY.match(line)
            if m:
                fence = m.group(1)
        elif gates.closes(line, fence):
            fence = None
    return False


def gate_findings(text: str, gates) -> tuple[int | None, str | None]:
    """関門の記録の反証・指摘の合計。記録が無ければ None、読めなければ理由（ブロックが 2 つ・閉じない・`LINE_FORMS` のどれにも当たらない行）。"""
    if not has_gate_block(text, gates):
        return None, None
    try:
        block = gates.gate_block(text)
    except gates.Malformed as e:
        return None, f"関門の記録が読めない（{e}）"
    total = 0
    for line in block:
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        forms = {k: rx.match(t) for k, rx in gates.LINE_FORMS.items()}
        if not any(forms.values()):
            return None, f"関門の記録が読めない（読めない行: {t}）"
        for k in ("pass", "narrow", "redo"):
            if forms[k]:
                total += int(forms[k].groups()[-1])
    return total, None


def read_plan(path: Path, gates) -> dict:
    """1 本の計画ファイルから、読んだ成果物・なし・起票・関門の指摘・形に合わない行を取る。"""
    reads: list[str] = []
    none = None
    count = None
    bad: list[str] = []
    fence = None
    opened = 0
    text = path.read_text(encoding="utf-8")
    for no, line in enumerate(text.splitlines(), start=1):
        if fence is None:
            m = gates.FENCE_ANY.match(line.strip())  # リストの中のコードブロックも見る（check-gates.py は字下げを外さない）
            if m:
                fence, opened = m.group(1), no
                continue
        else:
            if gates.closes(line, fence):
                fence = None
            continue
        c = COUNT.match(line)
        if c and count is None:
            count = int(c.group(1))
        r = LINE.match(line)
        if r:
            if r.group("none"):
                none = none or no
            else:
                p = normalize(r.group("path"))
                if p not in reads:
                    reads.append(p)
            continue
        if looks_like(line, gates):
            bad.append(f"{no} 行目")
    if fence is not None:
        bad.append(f"{opened} 行目: 閉じないコードブロックがある（その後ろを読んでいない）")
    if none and reads:
        bad.append(f"{none} 行目: なしとパスを両方書いている")
    findings, why = gate_findings(text, gates)
    if why:
        bad.append(why)
    return {"reads": reads, "none": bool(none), "count": count, "gates": findings, "bad": bad}


def md_files(root: Path) -> list[Path] | None:
    """ディレクトリの下の `*.md`。読めないディレクトリがあれば None（黙って落とさない）。"""
    errors: list[OSError] = []
    found: list[Path] = []
    for d, _, files in os.walk(root, onerror=errors.append):
        found.extend(Path(d) / f for f in files if f.endswith(".md"))
    if errors:
        print(f"読めないディレクトリ: {errors[0].filename}（数えていない）", file=sys.stderr)
        return None
    return sorted(q for q in found if q.is_file())


def collect(args: list[str]) -> list[Path] | None:
    plans: list[Path] = []
    for arg in args:
        p = Path(arg)
        if p.is_dir():
            found = md_files(p)
            if found is None:
                return None
            plans.extend(found)
        elif p.is_file():
            plans.append(p)
        else:
            print(f"無いパス: {arg}（数えていない）", file=sys.stderr)
            return None
    seen: list[Path] = []
    resolved: set[Path] = set()
    for p in plans:
        if p.resolve() not in resolved:
            resolved.add(p.resolve())
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
            except (OSError, UnicodeDecodeError) as e:
                print(f"--all-artifacts のファイルが読めない: {e}（数えていない）", file=sys.stderr)
                return 2
            for line in text.splitlines():
                s = line.strip()
                if s and not s.startswith("#") and normalize(s) not in expected:
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

    try:
        cg = load_gates()
    except (OSError, ImportError, SyntaxError, AttributeError) as e:
        print(f"関門の記録を読む check-gates.py を読み込めない: {e}（数えていない）", file=sys.stderr)
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
        try:
            info = read_plan(plan, cg)
        except (OSError, UnicodeDecodeError) as e:
            print(f"読めない計画ファイル: {plan}: {e}（数えていない）", file=sys.stderr)
            return 2
        for where in info["bad"]:
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
        if p not in names:
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
