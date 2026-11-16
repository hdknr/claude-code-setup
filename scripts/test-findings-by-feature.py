#!/usr/bin/env python3
"""`findings-by-feature.py`（仕様レビューの指摘の表から、機能ごとの指摘の件数を数える。#1045）の回帰テスト。

    python3 scripts/test-findings-by-feature.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-review-record.py` と同じ形。

見るもの:

1. **機能ごとの件数**——印 `機能: <名前>`（全角のコロンも）と機能の id（ケースの id `F-001-C1` は `F-001`）を、`指摘`・`根拠` の両方の列から拾い、
   機能ごとの合計と振り分けの区分ごとの件数を出す（Issue の受入基準 2。陽性対照）。複数の表（版）を足し合わせる。
2. **黙って落とさない**——印の無い行は「（機能を決められない）」に数え、2 つ以上の機能を挙げた行は全部に数えてその数を出す。同じ行の同じ機能は 1 件。
3. **中身を数えていない形を 0 にしない（2）**——検査に通らない表・無いファイル・引数の誤り。
4. **指摘の文面を出さない**——出力に `指摘`・`根拠`・`結果` の自由文が無い。
5. **原本との突き合わせ**——`references/spec-exit.md` の指摘の表が `（機能: <名前>）` の印と本体を指し、`references/spec-scope.md` が数え方を指す。
   本体の docstring と `spec-exit.md` が同じ印の形（`（機能: <名前>／機能: <名前>）`）を書く。括弧の中の括弧は名前の一部で、括弧の外の「機能:」・閉じない印・英数字に続く id を数えず、
   違反の行（セルの値）を写さず、同じ表を 2 度渡せば 2。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待（終了コードと、出力に含む行・含まない語）から外れること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**と、**変異の前は期待どおりであること**を先に確かめる。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "findings-by-feature.py"
SPEC_EXIT = PLUGIN / "references" / "spec-exit.md"
SPEC_SCOPE = PLUGIN / "references" / "spec-scope.md"

RUNS = "回,日付,結果,条件2〜4,要求の行,決定表の行,テストケース,仕様の行,判断,機能\n" \
       "1,2026-11-01,抜けていない,満たさない,10,5,8,40,-,注文\n2,2026-11-02,抜けた,満たす,10,5,8,40,-,-\n"
F_HEAD = "回,日付,レビュー,判定役,重さ,確かめたか,振り分け,指摘,根拠,結果\n"
HEADER = "| 機能 | 合計 | 仕様を直す | 共有の Q&A 表に起票する | 内部の Q&A 表に記録する | 範囲の外として記録する | 実装に渡す | 退ける | - |"
SECRET = "秘密の文面"
UNKNOWN = "（機能を決められない）"


def f(text: str, basis: str = "spec/a.md:3", category: str = "仕様を直す", confirmed: str = "確かめた", no: str = "1", day: str = "2026-11-01") -> str:
    weight = "-" if category in ("範囲の外として記録する", "実装に渡す") else "補い"
    result = "-" if confirmed == "確かめられない" else f"{SECRET}の結果"
    if confirmed == "確かめられない":
        category = "-"
    return ",".join([no, day, "1回目", "red-team", weight, confirmed, category, text, basis, result]) + "\n"


def row(name: str, total: int, *counts: int) -> str:
    cells = list(counts) + [0] * (7 - len(counts))
    return f"| {name} | {total} | " + " | ".join(str(c) for c in cells) + " |"


# 名前 → (表の一覧（名前 → 中身。None の表は置かずに渡す）, 足す引数, 期待の終了コード, 出力に含む語, 出力に含まない語)
CASES: dict[str, tuple] = {
    "数える: 名前の印（陽性対照）": ({"v1-findings.csv": F_HEAD + f(f"（機能: 注文）境界の 0 が無い{SECRET}") + f("（機能: 注文）負の数",
                                                                                       category="退ける")
                                     + f("（機能: 出荷）締めの時刻", category="共有の Q&A 表に起票する")},
                              [], 0, [HEADER, row("注文", 2, 1, 0, 0, 0, 0, 1), row("出荷", 1, 0, 1)], [SECRET]),
    "数える: 全角のコロン": ({"v1-findings.csv": F_HEAD + f("（機能：注文）全角")}, [], 0, [row("注文", 1, 1)], []),
    "数える: 機能の id とケースの id": ({"v1-findings.csv": F_HEAD + f("F-001 の境界") + f("ケースが無い", basis="spec/spec_ir.json の F-001-C2")
                                      + f("F-0012 の桁", category="実装に渡す")}, [], 0,
                                     [row("F-001", 2, 2), row("F-0012", 1, 0, 0, 0, 0, 1)], ["F-001-C2"]),
    "数える: 根拠の列の名前の印": ({"v1-findings.csv": F_HEAD + f("印の無い指摘", basis="spec/a.md:3（機能: 返品）")}, [], 0, [row("返品", 1, 1)], [UNKNOWN]),
    "数える: 印の無い行は決められない": ({"v1-findings.csv": F_HEAD + f("用語の定義が揺れる") + f("（機能: 注文）x")}, [], 0,
                                    [row(UNKNOWN, 1, 1), "決められない行: 1"], []),
    "数える: 2 つの機能を挙げた行は両方": ({"v1-findings.csv": F_HEAD + f("（機能: 注文／機能: 出荷）またがる")}, [], 0,
                                     [row("注文", 1, 1), row("出荷", 1, 1), "2 つ以上の機能に数えた行: 1"], []),
    "数える: 同じ機能を 2 度書いても 1 件": ({"v1-findings.csv": F_HEAD + f("（機能: 注文）x", basis="（機能: 注文）spec/a.md:3")}, [], 0,
                                       [row("注文", 1, 1), "2 つ以上の機能に数えた行: 0"], []),
    "数える: 確かめられない行は - の列": ({"v1-findings.csv": F_HEAD + f("（機能: 注文）x", confirmed="確かめられない")}, [], 0,
                                    [row("注文", 1, 0, 0, 0, 0, 0, 0, 1)], []),
    "数える: 多い順に並べる": ({"v1-findings.csv": F_HEAD + f("（機能: あ）1") + f("（機能: い）1") + f("（機能: い）2")}, [], 0,
                          [row("い", 2, 2) + "\n" + row("あ", 1, 1)], []),
    "数える: 2 つの版の表を足し合わせる": ({"v1-findings.csv": F_HEAD + f("（機能: 注文）x"), "v2-findings.csv": F_HEAD + f("（機能: 注文）y")}, [], 0,
                                    [row("注文", 2, 2), "表: 2・行: 2"], []),
    "数える: 見出しだけの表": ({"v1-findings.csv": F_HEAD}, [], 0, [HEADER, "表: 1・行: 0"], [UNKNOWN]),
    "数える: 英数字に続く id は数えない": ({"v1-findings.csv": F_HEAD + f("XF-001 と F-002a")}, [], 0, [row(UNKNOWN, 1, 1)], ["| F-00"]),
    "数える: 括弧の外の機能: は印でない": ({"v1-findings.csv": F_HEAD + f("（非機能: 性能が無い）") + f("この機能: 説明が長い（と思う）")}, [], 0,
                                    [row(UNKNOWN, 2, 2)], ["性能", "説明"]),
    "数える: 閉じない印は数えない": ({"v1-findings.csv": F_HEAD + f("（機能: 注文 の境界が無い")}, [], 0, [row(UNKNOWN, 1, 1)], ["境界"]),
    "数える: 名前の中の / と 、 は名前の一部": ({"v1-findings.csv": F_HEAD + f("（機能: 入出力/帳票、月次）x")}, [], 0, [row("入出力/帳票、月次", 1, 1)], []),
    "数える: 名前の | を逃がす": ({"v1-findings.csv": F_HEAD + f("（機能: a|b）x")}, [], 0, [row("a\\|b", 1, 1)], []),
    "数えない: 違反の行を写さない": ({"v1-findings.csv": F_HEAD + f("（機能: 注文）x", confirmed="確かめられない").replace(",-\n", f",{SECRET}\n")},
                               [], 2, ["検査に通らない"], [SECRET]),
    "数えない: 同じ表を 2 度渡す": ({"v1-findings.csv": F_HEAD + f("（機能: 注文）x")}, ["SAME"], 2, ["2 度"], ["| 注文 |"]),
    "数える: 括弧の中の括弧は名前の一部": ({"v1-findings.csv": F_HEAD + f("（機能: 受注（EDI））の検証") + f("（機能: 入出庫／棚卸し）y")}, [], 0,
                                      [row("受注（EDI）", 1, 1), row("入出庫／棚卸し", 1, 1)], []),
    "数える: 括弧の外の ／機能: は印でない": ({"v1-findings.csv": F_HEAD + f(f"見出し／機能: {SECRET}（と思う）")}, [], 0, [row(UNKNOWN, 1, 1)], [SECRET]),
    "数える: 閉じない印の後ろの括弧まで読まない": ({"v1-findings.csv": F_HEAD + f(f"（機能: 注文 の{SECRET}。例えば（0 件）のとき")}, [], 0, [row(UNKNOWN, 1, 1)], [SECRET]),
    "数える: 印の中の id は数えない": ({"v1-findings.csv": F_HEAD + f("（機能: F-001 受注）x")}, [], 0, [row("F-001 受注", 1, 1), "2 つ以上の機能に数えた行: 0"], []),
    "数える: つながった id は両方": ({"v1-findings.csv": F_HEAD + f("F-001-F-002 の境界")}, [], 0, [row("F-001", 1, 1), row("F-002", 1, 1)], []),
    "数えない: 検査に通らない表": ({"v1-findings.csv": F_HEAD + f("（機能: 注文）x", category="直す")}, [], 2, ["検査に通らない"], ["| 注文 |"]),
    "数えない: 2 つ目の表が検査に通らない": ({"v1-findings.csv": F_HEAD + f("（機能: 注文）x"), "v2-findings.csv": F_HEAD + f("（機能: 注文）y", no="9")},
                                      [], 2, ["v2-findings.csv が check-findings-csv.py の検査に通らない"], ["| 注文 |"]),
    "数えない: 無いファイル": ({"v1-findings.csv": None}, [], 2, ["数えていない"], []),
    "数えない: 引数なし": ({}, [], 2, ["usage"], []),
    "数えない: 未知の引数": ({"v1-findings.csv": F_HEAD}, ["--all"], 2, ["usage"], []),
}

# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("根拠の列を見ない", 'MARKED = ("指摘", "根拠")', 'MARKED = ("指摘",)', "数える: 根拠の列の名前の印"),
    ("全角のコロンを読まない", 'MARK_HEAD = re.compile(r"[（(]\\s*機能\\s*[:：]")', 'MARK_HEAD = re.compile(r"[（(]\\s*機能\\s*[:]")', "数える: 全角のコロン"),
    ("／で分けない", 'MARK_SPLIT = re.compile(r"\\s*／\\s*(?=機能\\s*[:：])")', 'MARK_SPLIT = re.compile(r"(?!)")', "数える: 2 つの機能を挙げた行は両方"),
    ("ケースの id を機能に寄せない", '(F-[0-9]{3,})(?![0-9A-Za-z_])', '(F-[0-9]{3,}(?:-C[0-9]+)?)(?![0-9A-Za-z_])', "数える: 機能の id とケースの id"),
    ("id の桁を 3 桁で切る", '(F-[0-9]{3,})(?![0-9A-Za-z_])', '(F-[0-9]{3})', "数える: 機能の id とケースの id"),
    ("id の後ろの英字を見ない", '(?![0-9A-Za-z_])"', '(?![0-9])"', "数える: 英数字に続く id は数えない"),
    ("id の前の英字を見ない", 'r"(?<![A-Za-z0-9_])(F-', 'r"(F-', "数える: 英数字に続く id は数えない"),
    ("id の前の - も止める", 'r"(?<![A-Za-z0-9_])(F-', 'r"(?<![A-Za-z0-9_-])(F-', "数える: つながった id は両方"),
    ("閉じない印も読む", "        if end is None:\n            continue\n", "        if end is None:\n            end = len(text)\n", "数える: 閉じない印は数えない"),
    ("括弧の入れ子を数えない", "        if text[i] in OPENS:\n            depth += 1\n", "        if i == start:\n            depth += 1\n", "数える: 括弧の中の括弧は名前の一部"),
    ("印の中の id も数える", "        for m in ID_MARK.finditer(rest):\n", "        for m in ID_MARK.finditer(cell[column]):\n", "数える: 印の中の id は数えない"),
    ("違反の行を写す", '                             f"——違反は python3 check-findings-csv.py {table} で見る")', '                             + "\\n".join(problems))', "数えない: 違反の行を写さない"),
    ("同じ表を 2 度数える", "        if table.resolve() in seen:\n", "        if False:\n", "数えない: 同じ表を 2 度渡す"),
    ("| を逃がさない", '    return name.replace("|", "\\\\|")\n', "    return name\n", "数える: 名前の | を逃がす"),
    ("印の無い行を落とす", "                names = [UNKNOWN]\n", "                continue\n", "数える: 印の無い行は決められない"),
    ("2 つ以上の機能を 1 つに寄せる", "            for name in names:\n", "            for name in names[:1]:\n", "数える: 2 つの機能を挙げた行は両方"),
    ("同じ機能を 2 度数える", "            if name not in out:\n", "            if True:\n", "数える: 同じ機能を 2 度書いても 1 件"),
    ("検査に通らない表を数える", "        if code != 0:\n", "        if False:\n", "数えない: 検査に通らない表"),
    ("1 つ目の表だけ数える", "    for table in tables:\n", "    for table in tables[:1]:\n", "数える: 2 つの版の表を足し合わせる"),
    ("区分を取り違える", "[cell[\"振り分け\"]] += 1", "[findings.CATEGORIES[0]] += 1", "数える: 名前の印（陽性対照）"),
    ("多い順に並べない", "key=lambda n: (-sum(per[n].values()), n)", "key=lambda n: n", "数える: 多い順に並べる"),
    ("決められない行の数を数えない", '                totals["決められない行"] += 1\n', "", "数える: 印の無い行は決められない"),
    ("引数なしで 0", "    if not argv or any(a.startswith(\"-\") for a in argv):\n", "    if any(a.startswith(\"-\") for a in argv):\n", "数えない: 引数なし"),
]


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name}{(': ' + detail) if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    tmp = Path(tempfile.gettempdir()).resolve()
    check(f"試料が一時ディレクトリの中: {path}", tmp in path.resolve().parents)


def run_one(script: Path, work: Path, case: tuple) -> tuple[int, str]:
    tables, extra, _, _, _ = case
    if work.exists():
        shutil.rmtree(work)
    folder = work / "spec-review"
    folder.mkdir(parents=True)
    assert_in_tmp(folder)
    argv = []
    for name, body in tables.items():
        if body is not None:
            (folder / name).write_text(body, encoding="utf-8")
            (folder / re.sub(r"-findings\.csv$", ".csv", name)).write_text(RUNS, encoding="utf-8")
        argv.append(str(folder / name))
    extra = [argv[0] if e == "SAME" else e for e in extra]
    proc = subprocess.run([sys.executable, "-I", str(script), *argv, *extra], capture_output=True, text=True, cwd=work)
    return proc.returncode, proc.stdout + proc.stderr


def as_expected(case: tuple, result: tuple[int, str]) -> bool:
    return result[0] == case[2] and all(w in result[1] for w in case[3]) and not any(w in result[1] for w in case[4])


def reference_problems(source: str, spec_exit: str, spec_scope: str) -> list[str]:
    problems = []
    if "**どの機能の指摘かを、先頭に `（機能: <名前>）` で書く**" not in spec_exit:
        problems.append("spec-exit.md の指摘の表に `（機能: <名前>）` の印の決まりが無い")
    if "`findings-by-feature.py`" not in spec_exit.split("#### 機能ごとに数える", 1)[-1].split("####", 1)[0]:
        problems.append("spec-exit.md の「機能ごとに数える」が本体を指さない")
    if "**数え方は `spec-exit.md` の「機能ごとに数える」を正とする**" not in spec_scope:
        problems.append("spec-scope.md が数え方を指さない")
    form = "`（機能: <名前>／機能: <名前>）`"
    if form not in spec_exit:
        problems.append(f"spec-exit.md に 2 つ以上の機能の印の形 {form} が無い")
    if form not in source:
        problems.append(f"本体の docstring に印の形 {form} が無い")
    return problems


def main() -> int:
    source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="findings-by-feature-test-") as tmp:
        root = Path(tmp)
        scripts = root / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        print("試料")
        for i, (name, case) in enumerate(CASES.items()):
            result = run_one(scripts / TARGET, root / f"c{i}", case)
            check(f"試料: {name}", as_expected(case, result), f"期待 {case[2]}・{case[3]!r} / 実際 {result[0]}・{result[1][-500:]!r}")
        print(f"  {len(CASES)} 件 OK")

        print("原本との突き合わせ")
        spec_exit = SPEC_EXIT.read_text(encoding="utf-8")
        spec_scope = SPEC_SCOPE.read_text(encoding="utf-8")
        problems = reference_problems(source, spec_exit, spec_scope)
        check("本体と references が一致する", not problems, "; ".join(problems))
        broken = source.replace("`（機能: <名前>／機能: <名前>）`", "`（機能: <名前>）`", 1)
        check("崩した docstring で突き合わせが落ちる（陽性対照）", reference_problems(broken, spec_exit, spec_scope) != [])
        print("  OK")

        print("変異テスト")
        for name, before, after, killer in MUTATIONS:
            check(f"壊す箇所がちょうど 1 回: {name}", source.count(before) == 1, f"{source.count(before)} 回: {before!r}")
            mutated = root / "mutated"
            if mutated.exists():
                shutil.rmtree(mutated)
            shutil.copytree(scripts, mutated)
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            case = CASES[killer]
            original = run_one(scripts / TARGET, root / "orig", case)
            result = run_one(mutated / TARGET, root / "mut", case)
            check(f"変異の前は期待どおり: {name}", as_expected(case, original))
            check(f"変異を殺す（期待から外れる）: {name} ← {killer}", not as_expected(case, result), f"{result[0]} {result[1][-300:]!r}")
        print(f"  変異 {len(MUTATIONS)} 件 OK")
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
