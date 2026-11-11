#!/usr/bin/env python3
"""`check-findings-csv.py`（仕様レビューの指摘の表の形式の検査。#982）の回帰テスト。

    python3 scripts/test-check-findings-csv.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-infra-csv.py` と同じ形。

見るもの:

1. **決まりに反する形を、理由つきで落とす（1）**——見出し（順・列の過不足）・列の数・数える列の値（レビュー・判定役・重さ・確かめたか）・
   **振り分けが区分の名前でない（言い換え・理由を足した・`確かめられない`）**・`-` と `確かめられない` の対応（2 方向）・
   範囲の外／実装に渡す の行の重さ・`回` の形・`回` が実行の行でない（`上限` の行・無い番号）・日付の形と食い違い・`指摘` が空。
2. **決まりどおりの形を通す（0）**——**6 つの区分のどれも通す**（「実装に渡す」「退ける」の行を含む）・`確かめられない` の行の `-`・
   3 つのレビュー・BOM・見出しの行だけ・`記法の移行` の行を持つ実行の記録。
3. **中身を検査していない形を 0 にしない（2）**——名前が `v<n>-findings.csv` でない・ファイルが無い・空・UTF-8 でない・
   実行の記録が無い・実行の記録の見出しに `結果` が無い・引数の誤り。
4. **本体の定数が references と一致する**（写しのずれ）——列と数える列の値は `references/spec-exit.md` の「指摘の表」、
   振り分けの 6 つの名前は `references/spec-scope.md` の「振り分けの区分」。崩した写しで落ちることも見る。
5. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料の終了コードが変わること**を確かめる（文言の違いでは殺したと数えない）。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-findings-csv.py"
SPEC_EXIT = PLUGIN / "references" / "spec-exit.md"
SPEC_SCOPE = PLUGIN / "references" / "spec-scope.md"

F_HEAD = "回,日付,レビュー,判定役,重さ,確かめたか,振り分け,指摘,根拠,結果\n"
RUNS = ("回,日付,結果,条件2〜4,要求の行,決定表の行,テストケース,仕様の行,判断,機能\n"
        "1,2026-11-01,抜けていない,満たさない,10,5,8,40,-,注文\n"
        "2,2026-11-02,上限,-,-,-,-,-,-,-\n"
        "3,2026-11-02,利用者の判断,-,-,-,-,-,続ける,-\n"
        "4,2026-11-03,抜けた,満たす,10,5,9,44,-,-\n"
        "5,2026-11-04,記法の移行,-,-,-,-,-,-,-\n")


def row(no="1", day="2026-11-01", review="1回目", judge="red-team", weight="補い", confirmed="確かめた",
        category="仕様を直す", text="境界の 0 が無い", basis="spec/a.md:3", result="spec/a.md:4") -> str:
    return ",".join([no, day, review, judge, weight, confirmed, category, text, basis, result]) + "\n"


GOOD = (F_HEAD + row()
        + row(category="共有の Q&A 表に起票する", weight="判断が要る", result="Q-S-001")
        + row(category="内部の Q&A 表に記録する", weight="結果が割れる", judge="domain-checker", result="D-S-001")
        + row(category="範囲の外として記録する", weight="-", judge="formal-checker", result="spec/scope.md:5")
        + row(category="実装に渡す", weight="-", review="2回目", result="設計メモ")
        + row(category="退ける", review="狭いパス", result="根拠の行に書いてあった")
        + row(confirmed="確かめられない", category="-", basis="確かめられない（照合先が無い）", result="-")
        + row(no="4", day="2026-11-03", text='"a,b を含む指摘"'))

# 名前 → (指摘の表の名前, 指摘の表の中身（bytes か str か None）, 実行の記録（None なら置かない）, 引数（None なら表のパス）, 期待の終了コード, 出力に含む語)
CASES: dict[str, tuple] = {
    "通る: 6 区分すべて・確かめられない・3 つのレビュー": ("v1-findings.csv", GOOD, RUNS, None, 0, "違反なし"),
    "通る: BOM つき": ("v1-findings.csv", "﻿" + GOOD, RUNS, None, 0, "違反なし"),
    "通る: 見出しの行だけ": ("v1-findings.csv", F_HEAD, RUNS, None, 0, "違反なし"),
    "通る: 版 12": ("v12-findings.csv", F_HEAD + row(), RUNS, None, 0, "違反なし"),
    "落ちる: 見出しの順": ("v1-findings.csv", F_HEAD.replace("回,日付", "日付,回") + row(), RUNS, None, 1, "見出しの行"),
    "落ちる: 見出しの列が足りない": ("v1-findings.csv", F_HEAD.replace(",結果", "") + row(), RUNS, None, 1, "見出しの行"),
    "落ちる: 列の数": ("v1-findings.csv", F_HEAD + row().replace(",spec/a.md:4", ""), RUNS, None, 1, "列の数"),
    "落ちる: レビューの値": ("v1-findings.csv", F_HEAD + row(review="3回目"), RUNS, None, 1, "`レビュー`"),
    "落ちる: 判定役の値": ("v1-findings.csv", F_HEAD + row(judge="Red Team"), RUNS, None, 1, "`判定役`"),
    "落ちる: 重さの値": ("v1-findings.csv", F_HEAD + row(weight="重い"), RUNS, None, 1, "`重さ`"),
    "落ちる: 確かめたかの値": ("v1-findings.csv", F_HEAD + row(confirmed="はい"), RUNS, None, 1, "`確かめたか`"),
    "落ちる: 振り分けの言い換え": ("v1-findings.csv", F_HEAD + row(category="実装へ", weight="-"), RUNS, None, 1, "区分の名前でない"),
    "落ちる: 振り分けに理由を足した": ("v1-findings.csv", F_HEAD + row(category="退ける（誤り）"), RUNS, None, 1, "区分の名前でない"),
    "落ちる: 振り分けに確かめられない": ("v1-findings.csv", F_HEAD + row(confirmed="確かめられない", category="確かめられない"), RUNS, None, 1, "区分の名前でない"),
    "落ちる: 確かめたのに振り分けが -": ("v1-findings.csv", F_HEAD + row(category="-"), RUNS, None, 1, "`振り分け` が `-` なのは"),
    "落ちる: 確かめられないのに区分を確定": ("v1-findings.csv", F_HEAD + row(confirmed="確かめられない"), RUNS, None, 1, "どの区分にも確定しない"),
    "落ちる: 実装に渡すの重さ": ("v1-findings.csv", F_HEAD + row(category="実装に渡す", weight="補い"), RUNS, None, 1, "の行の `重さ` は `-`"),
    "落ちる: 範囲の外の重さ": ("v1-findings.csv", F_HEAD + row(category="範囲の外として記録する", weight="判断が要る"), RUNS, None, 1, "の行の `重さ` は `-`"),
    "落ちる: 回の形": ("v1-findings.csv", F_HEAD + row(no="01"), RUNS, None, 1, "1 からの番号でない"),
    "落ちる: 回が上限の行": ("v1-findings.csv", F_HEAD + row(no="2", day="2026-11-02"), RUNS, None, 1, "実行の行"),
    "落ちる: 回が記法の移行の行": ("v1-findings.csv", F_HEAD + row(no="5", day="2026-11-04"), RUNS, None, 1, "実行の行"),
    "落ちる: 回が無い": ("v1-findings.csv", F_HEAD + row(no="9"), RUNS, None, 1, "実行の行"),
    "落ちる: 日付の形": ("v1-findings.csv", F_HEAD + row(day="2026/11/01"), RUNS, None, 1, "YYYY-MM-DD"),
    # 実行の記録の側にも同じ無い日付を置く——日付の食い違いでは落ちず、無い日付だけで落ちる形にする
    "落ちる: 無い日付": ("v1-findings.csv", F_HEAD + row(no="6", day="2026-02-30"), RUNS + "6,2026-02-30,抜けていない,満たさない,1,1,1,1,-,注文\n", None, 1, "YYYY-MM-DD"),
    "落ちる: 日付が実行の行と違う": ("v1-findings.csv", F_HEAD + row(day="2026-11-02"), RUNS, None, 1, "日付 '2026-11-01' と違う"),
    "落ちる: 指摘が空": ("v1-findings.csv", F_HEAD + row(text=""), RUNS, None, 1, "`指摘` が空"),
    "判定しない: 名前": ("findings.csv", GOOD, RUNS, None, 2, "v<n>-findings.csv でない"),
    "判定しない: 表が無い": ("v1-findings.csv", None, RUNS, None, 2, "指摘の表が無い"),
    "判定しない: 空のファイル": ("v1-findings.csv", "", RUNS, None, 2, "空"),
    "判定しない: UTF-8 でない": ("v1-findings.csv", F_HEAD.encode("cp932"), RUNS, None, 2, "UTF-8 でない"),
    "判定しない: 実行の記録が無い": ("v1-findings.csv", GOOD, None, None, 2, "実行の記録が無い"),
    "判定しない: 実行の記録に結果が無い": ("v1-findings.csv", GOOD, RUNS.replace(",結果,", ",出来事,", 1), None, 2, "結果 が無い"),
    "判定しない: 引数なし": ("v1-findings.csv", GOOD, RUNS, [], 2, "usage"),
    "判定しない: 引数が 2 つ": ("v1-findings.csv", GOOD, RUNS, ["a", "b"], 2, "usage"),
}

# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("振り分けの値を見ない", "    elif category not in CATEGORIES:\n", "    elif False:\n", "落ちる: 振り分けの言い換え"),
    ("確かめたのに - を通す", "        if cell[\"確かめたか\"] != UNCONFIRMED:\n", "        if False:\n", "落ちる: 確かめたのに振り分けが -"),
    ("確かめられないのに区分を通す", "    elif cell[\"確かめたか\"] == UNCONFIRMED:\n", "    elif False:\n", "落ちる: 確かめられないのに区分を確定"),
    ("範囲の外・実装に渡すの重さを見ない", "    if category in NO_WEIGHT and cell[\"重さ\"] != NONE:\n", "    if False:\n", "落ちる: 実装に渡すの重さ"),
    ("回が実行の行かを見ない", "    elif no not in runs:\n", "    elif False:\n", "落ちる: 回が無い"),
    ("上限の行も実行の行と読む", "        if row[at[\"結果\"]].strip() in RUN_RESULTS:\n", "        if True:\n", "落ちる: 回が上限の行"),
    ("日付の食い違いを見ない", "    elif no in runs and runs[no] != cell[\"日付\"]:\n", "    elif False:\n", "落ちる: 日付が実行の行と違う"),
    ("無い日付を通す", "        date.fromisoformat(value)\n", "        pass\n", "落ちる: 無い日付"),
    ("見出しを見ない", "    if header != COLUMNS:\n", "    if False:\n", "落ちる: 見出しの順"),
    ("列の数を見ない", "        if len(row) != len(COLUMNS):\n", "        if False:\n", "落ちる: 列の数"),
    ("指摘が空でも通す", "    if not cell[\"指摘\"]:\n", "    if False:\n", "落ちる: 指摘が空"),
    ("判定役の値を見ない", "(\"判定役\", JUDGES), ", "", "落ちる: 判定役の値"),
    ("BOM を読まない", "decode(\"utf-8-sig\")", "decode(\"utf-8\")", "通る: BOM つき"),
    # 「判定しない（2）」を崩す変異は、2 のままの形（別の例外で落ちる）にしない——判定して 0 か 1 を返す形にする（#982 の 1 パス目の R2）
    ("空のファイルを見出しだけの表と読む", "    if not rows:\n        raise Unreadable(f\"{what}が空（見出しの行も無い）: {path}\")\n",
     "    if not rows:\n        return [list(COLUMNS)]\n", "判定しない: 空のファイル"),
    ("実行の記録が無ければ空と読む", "    rows = read_csv(path, \"実行の記録\")\n",
     "    rows = read_csv(path, \"実行の記録\") if path.is_file() else [list(RUN_COLUMNS)]\n", "判定しない: 実行の記録が無い"),
    ("名前を見ずに v1.csv を読む", "        raise Unreadable(f\"指摘の表の名前が v<n>-findings.csv でない: {findings.name}\")\n",
     "        return findings.with_name(\"v1.csv\")\n", "判定しない: 名前"),
    ("違反を 0 で返す", "    return (1 if lines else 0), lines\n", "    return 0, lines\n", "落ちる: 回の形"),
]


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name}{(': ' + detail) if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    tmp = Path(tempfile.gettempdir()).resolve()
    check(f"試料が一時ディレクトリの中: {path}", tmp in path.resolve().parents)


def run_one(script: Path, work: Path, case: tuple, isolated: bool = False) -> tuple[int, str]:
    filename, content, runs, args, _, _ = case
    if work.exists():
        shutil.rmtree(work)
    folder = work / "spec-review"
    folder.mkdir(parents=True)
    assert_in_tmp(folder)
    target = folder / filename
    if content is not None:
        target.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    if runs is not None:
        (folder / "v1.csv").write_text(runs, encoding="utf-8")
        (folder / "v12.csv").write_text(runs, encoding="utf-8")
    argv = [str(target)] if args is None else list(args)
    cmd = [sys.executable] + (["-I"] if isolated else []) + [str(script)] + argv
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=work)
    return proc.returncode, proc.stdout + proc.stderr


def as_expected(case: tuple, result: tuple[int, str]) -> bool:
    code, out = result
    return code == case[4] and case[5] in out


def section(markdown: str, heading: str) -> str:
    start = markdown.index(heading)
    rest = markdown[start + len(heading):]
    m = re.search(r"^#{2,3} ", rest, re.M)
    return rest[: m.start()] if m else rest


def table_rows(text: str) -> list[list[str]]:
    out = []
    for line in text.splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*-", line):
            out.append([c.strip() for c in line.strip().strip("|").split("|")])
    return out[1:]  # 見出しの行を除く


def reference_mismatches(module, spec_exit: str, spec_scope: str) -> list[str]:
    problems: list[str] = []
    rows = table_rows(section(spec_exit, "### 指摘の表"))
    columns = [re.sub(r"^`|`$", "", r[0]) for r in rows]
    if columns != module.COLUMNS:
        problems.append(f"列: references {columns} ≠ 本体 {module.COLUMNS}")
    by_column = {re.sub(r"^`|`$", "", r[0]): r[2] for r in rows}
    for column, values in (("レビュー", module.REVIEWS), ("判定役", module.JUDGES), ("重さ", module.WEIGHTS),
                           ("確かめたか", (module.CONFIRMED, module.UNCONFIRMED)), ("振り分け", module.CATEGORIES)):
        # 値は、セルの最初の「。」までに書いた `…` の並び（振り分けは「どれか」の後ろ、ほかは「（」の前）
        seg = by_column.get(column, "").split("。")[0]
        seg = seg.split("どれか", 1)[-1] if column == "振り分け" else seg.split("（")[0]
        written = re.findall(r"`([^`]+)`", seg)
        if list(values) != written:
            problems.append(f"`{column}` の値: references {written} ≠ 本体 {list(values)}")
    categories = [re.sub(r"\*", "", r[0]) for r in table_rows(section(spec_scope, "## 振り分けの区分"))]
    if categories != list(module.CATEGORIES):
        problems.append(f"振り分けの区分: spec-scope.md {categories} ≠ 本体 {list(module.CATEGORIES)}")
    return problems


REFERENCE_MUTATIONS = [
    ("spec-exit の列の順を入れ替える", "spec_exit", "| `根拠` | 文面 |", "| `根拠x` | 文面 |"),
    ("spec-exit のレビューの値を変える", "spec_exit", "`1回目`／`2回目`／`狭いパス`", "`1回目`／`2回目`"),
    ("spec-exit の振り分けの名前を変える", "spec_exit", "`内部の Q&A 表に記録する`・`範囲の外", "`内部の表に記録する`・`範囲の外"),
    ("spec-scope の区分の名前を変える", "spec_scope", "| **実装に渡す** |", "| **実装へ渡す** |"),
]


def load(path: Path, name: str = "check_findings_csv_under_test"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
    spec_exit = SPEC_EXIT.read_text(encoding="utf-8")
    spec_scope = SPEC_SCOPE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        work = root / "work"

        print("試料（本物の本体）")
        for name, case in CASES.items():
            result = run_one(SCRIPTS / TARGET, work, case)
            check(name, as_expected(case, result), f"期待 {case[4]}・{case[5]!r}、実際 {result[0]}\n{result[1]}")
        print(f"  {len(CASES)} 件 OK")

        print("references との突き合わせ")
        module = load(SCRIPTS / TARGET)
        problems = reference_mismatches(module, spec_exit, spec_scope)
        check("本体の定数が references と一致する", not problems, "\n".join(problems))
        for name, which, before, after in REFERENCE_MUTATIONS:
            text = spec_exit if which == "spec_exit" else spec_scope
            check(f"崩しの前の形がちょうど 1 回: {name}", text.count(before) == 1, before)
            broken = text.replace(before, after)
            args = (broken, spec_scope) if which == "spec_exit" else (spec_exit, broken)
            check(f"崩した写しで落ちる: {name}", bool(reference_mismatches(module, *args)))
        print(f"  崩し {len(REFERENCE_MUTATIONS)} 件 OK")

        print("リポジトリの外で単体で動く")
        alone = root / "alone"
        alone.mkdir()
        shutil.copy2(SCRIPTS / TARGET, alone / TARGET)
        name = "通る: 6 区分すべて・確かめられない・3 つのレビュー"
        result = run_one(alone / TARGET, work, CASES[name], isolated=True)
        check("python3 -I で写しが通る", as_expected(CASES[name], result), result[1])
        name = "落ちる: 振り分けの言い換え"
        result = run_one(alone / TARGET, work, CASES[name], isolated=True)
        check("python3 -I で写しが落とす", as_expected(CASES[name], result), result[1])

        print("変異テスト")
        mutant = root / "mutant" / TARGET
        mutant.parent.mkdir()
        killed = 0
        for name, before, after, killer in MUTATIONS:
            check(f"壊す箇所がちょうど 1 回: {name}", source.count(before) == 1, repr(before))
            mutant.write_text(source.replace(before, after), encoding="utf-8")
            result = run_one(mutant, work, CASES[killer])
            # 殺したと数えるのは終了コードが変わったときだけ（出力の文言の違いでは数えない）
            check(f"変異が終了コードを変える: {name}（{killer}）", result[0] != CASES[killer][4], f"{result[0]}\n{result[1]}")
            killed += 1
        print(f"  {killed} 件 OK")

    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件・references の崩し {len(REFERENCE_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
