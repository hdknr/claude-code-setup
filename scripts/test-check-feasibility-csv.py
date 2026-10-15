#!/usr/bin/env python3
"""`check-feasibility-csv.py`（スケジュールと見積りの表の検査）の回帰テスト。

    python3 scripts/test-check-feasibility-csv.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-spec-exit.py` と同じ形。

見るもの:

1. **決まりに反する形を、理由つきで落とす（1）**——見出し・空のセル・番号・日付・終了が開始より前・
   前提（無い工程・自分自身・前提が終わる前に始まる）・区分・金額（カンマ・全角・小数）。
2. **決まりどおりの形を通す**（陽性対照。`references/feasibility-csv.md` の「例」も通ること）。
3. **中身を検査していない形を 0 にしない（2）**——ファイルが無い・UTF-8 でない・空。
4. **本体の定数が `references/feasibility-csv.md` の表と一致する**（写しのずれ）。
5. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-feasibility-csv.py"
REFERENCE = PLUGIN / "references" / "feasibility-csv.md"

S_HEAD = "No,工程,開始,終了,前提\n"
S_GOOD = (
    "T-001,要件定義,2026-11-02,2026-11-27,\n"
    "T-002,基本設計,2026-11-30,2026-12-25,T-001\n"
    "T-003,予算の合意,2026-12-25,2026-12-25,T-001 / T-002\n"
)
E_HEAD = "No,区分,項目,金額,根拠\n"
E_GOOD = (
    "E-001,開発費,画面の開発,4800000,12 画面 × 40 万円\n"
    "E-002,運用費（月額）,サーバ,0,Q-005 の回答 A\n"
)

# (名前, schedule.csv の中身, estimate.csv の中身（None なら作らない）, 期待する終了コード, 出力に含まれるべき文字列)
CASES: list[tuple[str, str | bytes | None, str | bytes | None, int, str]] = [
    ("決まりどおり", S_HEAD + S_GOOD, E_HEAD + E_GOOD, 0, "OK（"),
    ("BOM 付き", "﻿" + S_HEAD + S_GOOD, "﻿" + E_HEAD + E_GOOD, 0, "OK（"),
    ("前提の終了日に始まる", S_HEAD + "T-001,a,2026-11-02,2026-11-05,\nT-002,b,2026-11-05,2026-11-06,T-001\n",
     E_HEAD + E_GOOD, 0, "OK（"),
    ("1 日の節目", S_HEAD + "T-001,a,2026-11-02,2026-11-02,\n", E_HEAD + E_GOOD, 0, "OK（"),
    ("番号が 4 桁", S_HEAD + "T-1000,a,2026-11-02,2026-11-02,\n", E_HEAD + "E-1000,開発費,a,1,b\n", 0, "OK（"),
    ("見出しが違う", "No,工程,開始,終了\n", E_HEAD + E_GOOD, 1, "見出し行が決まりと違う"),
    ("見積りの見出しが違う", S_HEAD + S_GOOD, "No,区分,項目,金額\n", 1, "見出し行が決まりと違う"),
    ("列の数", S_HEAD + "T-001,a,2026-11-02,2026-11-02\n", E_HEAD + E_GOOD, 1, "列の数が 4"),
    ("工程が空", S_HEAD + "T-001,,2026-11-02,2026-11-02,\n", E_HEAD + E_GOOD, 1, "`工程` が空"),
    ("根拠が空", S_HEAD + S_GOOD, E_HEAD + "E-001,開発費,a,100,\n", 1, "`根拠` が空"),
    ("工程の番号", S_HEAD + "T-1,a,2026-11-02,2026-11-02,\n", E_HEAD + E_GOOD, 1, "`No` が `T-001` の形でない"),
    ("工程の番号が全角", S_HEAD + "T-００１,a,2026-11-02,2026-11-02,\n", E_HEAD + E_GOOD, 1, "`T-001` の形でない"),
    ("費用の番号", S_HEAD + S_GOOD, E_HEAD + "T-001,開発費,a,1,b\n", 1, "`No` が `E-001` の形でない"),
    ("工程の番号の重複", S_HEAD + "T-001,a,2026-11-02,2026-11-02,\nT-001,b,2026-11-03,2026-11-03,\n",
     E_HEAD + E_GOOD, 1, "2 行目と重複"),
    ("費用の番号の重複", S_HEAD + S_GOOD, E_HEAD + "E-001,開発費,a,1,b\nE-001,開発費,c,1,d\n", 1, "2 行目と重複"),
    ("日付の書式", S_HEAD + "T-001,a,2026/11/02,2026-11-02,\n", E_HEAD + E_GOOD, 1, "`開始` が `YYYY-MM-DD` の日付でない"),
    ("無い日付", S_HEAD + "T-001,a,2026-02-30,2026-03-02,\n", E_HEAD + E_GOOD, 1, "`開始` が `YYYY-MM-DD` の日付でない"),
    ("月が 1 桁", S_HEAD + "T-001,a,2026-11-02,2026-1-02,\n", E_HEAD + E_GOOD, 1, "`終了` が `YYYY-MM-DD` の日付でない"),
    # Python 3.11 以降の `date.fromisoformat` は基本形式（区切りなし）も読むので、書式は別に見る
    ("基本形式の日付", S_HEAD + "T-001,a,20261102,2026-11-02,\n", E_HEAD + E_GOOD, 1, "`開始` が `YYYY-MM-DD` の日付でない"),
    ("終了が開始より前", S_HEAD + "T-001,a,2026-11-05,2026-11-02,\n", E_HEAD + E_GOOD, 1, "`終了` が `開始` より前"),
    ("前提が表に無い", S_HEAD + "T-001,a,2026-11-02,2026-11-02,T-009\n", E_HEAD + E_GOOD, 1, "'T-009' が表に無い"),
    ("前提の区切りが違う", S_HEAD + "T-001,a,2026-11-02,2026-11-02,\nT-002,b,2026-11-03,2026-11-03,\n"
     "T-003,c,2026-11-04,2026-11-04,T-001,T-002\n", E_HEAD + E_GOOD, 1, "列の数が 6"),
    ("前提の区切りに空白が無い", S_HEAD + "T-001,a,2026-11-02,2026-11-02,\nT-002,b,2026-11-03,2026-11-03,\n"
     "T-003,c,2026-11-04,2026-11-04,T-001/T-002\n", E_HEAD + E_GOOD, 1, "'T-001/T-002' が表に無い"),
    ("前提が自分自身", S_HEAD + "T-001,a,2026-11-02,2026-11-02,T-001\n", E_HEAD + E_GOOD, 1, "`前提` に自分自身"),
    ("前提が終わる前に始まる", S_HEAD + "T-001,a,2026-11-02,2026-11-10,\nT-002,b,2026-11-09,2026-11-20,T-001\n",
     E_HEAD + E_GOOD, 1, "T-001 が終わる前（2026-11-10）に始まる"),
    # 後ろの行を前提にしても見る（表の順に依らない）
    ("後ろの行が前提", S_HEAD + "T-001,a,2026-11-02,2026-11-03,T-002\nT-002,b,2026-11-05,2026-11-06,\n",
     E_HEAD + E_GOOD, 1, "T-002 が終わる前"),
    ("区分が無い", S_HEAD + S_GOOD, E_HEAD + "E-001,保守費,a,1,b\n", 1, "`区分` が決まりに無い"),
    ("金額にカンマ", S_HEAD + S_GOOD, E_HEAD + 'E-001,開発費,a,"4,800,000",b\n', 1, "`金額` が半角数字だけでない"),
    ("金額が全角", S_HEAD + S_GOOD, E_HEAD + "E-001,開発費,a,１００,b\n", 1, "`金額` が半角数字だけでない"),
    ("金額に小数", S_HEAD + S_GOOD, E_HEAD + "E-001,開発費,a,100.5,b\n", 1, "`金額` が半角数字だけでない"),
    ("金額が負", S_HEAD + S_GOOD, E_HEAD + "E-001,開発費,a,-100,b\n", 1, "`金額` が半角数字だけでない"),
    ("両方の問題を全部出す", S_HEAD + "T-1,a,2026-11-02,2026-11-02,\n", E_HEAD + "E-001,保守費,a,1,b\n", 1,
     "`区分` が決まりに無い"),
    ("スケジュールが無い", None, E_HEAD + E_GOOD, 2, "読めない"),
    ("見積りが UTF-8 でない", S_HEAD + S_GOOD, (E_HEAD + E_GOOD).encode("cp932"), 2, "UTF-8 として読めない"),
    ("見積りが空", S_HEAD + S_GOOD, "", 2, "空のファイル"),
    # 片方に問題があっても、もう片方を読んでいなければ 2
    ("問題と読めないファイル", S_HEAD + "T-1,a,2026-11-02,2026-11-02,\n", "", 2, "`T-001` の形でない"),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("空のセルを見ない", "if column not in MAY_BE_EMPTY and not row[column].strip():", "if False:", "根拠が空"),
    ("前提の空を許さない", 'MAY_BE_EMPTY = {"前提"}', "MAY_BE_EMPTY = set()", "決まりどおり"),
    ("番号の書式を見ない", "if row[\"No\"] and not number.fullmatch(row[\"No\"]):", "if False:", "工程の番号"),
    ("番号を Unicode の数字で見る", r'TASK_NUMBER = re.compile(r"T-[0-9]{3,}")', r'TASK_NUMBER = re.compile(r"T-\d{3,}")',
     "工程の番号が全角"),
    ("費用の番号に工程の書式を使う", 'check_estimate(path: Path, text: str | None = None)',
     'check_estimate(path: Path, text: str | None = None, COST_NUMBER=TASK_NUMBER)', "費用の番号"),
    ("番号の重複を見ない", 'if row["No"] in seen:', "if False:", "工程の番号の重複"),
    ("見出しを見ない", "if header != columns:", "if False:", "見出しが違う"),
    ("列の数を見ない", "if len(fields) != len(columns):", "if False:", "列の数"),
    ("日付の書式を見ない", "if not DATE.fullmatch(value):\n        return None", "if False:\n        return None",
     "基本形式の日付"),
    ("無い日付を通す", "    except ValueError:\n        return None", "    except ValueError:\n        return date(2000, 1, 1)",
     "無い日付"),
    ("終了と開始を比べない", "if start and end and end < start:", "if False:", "終了が開始より前"),
    ("前提の終了日に始まるのを許さない", "if start and before_end and start < before_end:",
     "if start and before_end and start <= before_end:", "前提の終了日に始まる"),
    ("前提の終了日を見ない", "if start and before_end and start < before_end:", "if False:", "前提が終わる前に始まる"),
    ("前提の実在を見ない", "elif before not in by_no:", "elif False:", "前提が表に無い"),
    ("自分自身を見ない", 'if before == row["No"]:', "if False:", "前提が自分自身"),
    ("後ろの行を前提にできない", 'by_no = {row["No"]: row for _, row in rows}',
     "by_no = {}", "後ろの行が前提"),
    ("区分を見ない", 'if row["区分"].strip() and row["区分"] not in CATEGORIES:', "if False:", "区分が無い"),
    ("金額の書式を見ない", 'if row["金額"].strip() and not AMOUNT.fullmatch(row["金額"]):', "if False:", "金額にカンマ"),
    ("金額を Unicode の数字で見る", 'AMOUNT = re.compile(r"[0-9]+")', r'AMOUNT = re.compile(r"\d+")', "金額が全角"),
    ("読めないより問題を優先する", "    if unreadable:\n        return 2\n    if problems:\n        return 1",
     "    if problems:\n        return 1\n    if unreadable:\n        return 2", "問題と読めないファイル"),
    ("BOM を剥がさない", 'path.read_text(encoding="utf-8-sig")', 'path.read_text(encoding="utf-8")', "BOM 付き"),
    ("空のファイルを 2 にしない", "    if not text.strip():\n        raise Unreadable", "    if False:\n        raise Unreadable",
     "見積りが空"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def write(path: Path, body: str | bytes | None) -> None:
    if isinstance(body, bytes):
        path.write_bytes(body)
    elif body is not None:
        path.write_text(body, encoding="utf-8")


def run_one(scripts: Path, root: Path, schedule, estimate) -> tuple[int, str]:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    write(root / "schedule.csv", schedule)
    write(root / "estimate.csv", estimate)
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), str(root / "schedule.csv"),
                           str(root / "estimate.csv")], capture_output=True, text=True, cwd=root)
    return proc.returncode, proc.stdout + proc.stderr


def run_all(scripts: Path, work: Path) -> dict[str, tuple[int, str]]:
    return {name: run_one(scripts, work / f"case{i}", s, e) for i, (name, s, e, _, _) in enumerate(CASES)}


def as_expected(name: str, result: tuple[int, str]) -> bool:
    expected = next(case for case in CASES if case[0] == name)
    return result[0] == expected[3] and expected[4] in result[1]


def section(markdown: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", markdown, re.S | re.M)
    return m.group(1) if m else ""


def table_keys(text: str) -> list[str]:
    return re.findall(r"^\| `([^`]+)` \|", text, flags=re.MULTILINE)


def constant(source: str, name: str):
    m = re.search(rf"^{name} = (.+)$", source, flags=re.MULTILINE)
    return ast.literal_eval(m.group(1)) if m else None


def regex_of(source: str, name: str) -> str | None:
    m = re.search(rf'^{name} = re\.compile\(r"([^"]+)"\)$', source, flags=re.MULTILINE)
    return m.group(1) if m else None


def reference_mismatches(source: str, markdown: str) -> list[str]:
    problems = []
    schedule, estimate = section(markdown, "`schedule.csv` — スケジュール"), section(markdown, "`estimate.csv` — 見積り")
    for label, keys, name in (("schedule.csv の列", table_keys(schedule), "SCHEDULE_COLUMNS"),
                              ("estimate.csv の列", table_keys(estimate.split("### 区分")[0]), "ESTIMATE_COLUMNS"),
                              ("区分", table_keys(estimate.split("### 区分")[-1]), "CATEGORIES")):
        if keys != constant(source, name):
            problems.append(f"{label} {keys} ≠ 本体 {constant(source, name)}")
    empty = re.search(r"\*\*どの列も空を許さない\*\*（`([^`]+)` を除く）", markdown)
    may_be_empty = {empty.group(1)} if empty else None
    if may_be_empty != constant(source, "MAY_BE_EMPTY"):
        problems.append(f"空を許す列 {empty and empty.group(1)!r} ≠ 本体 {constant(source, 'MAY_BE_EMPTY')}")
    for prefix, name in (("T", "TASK_NUMBER"), ("E", "COST_NUMBER")):
        digits = re.search(rf"`{prefix}-` に (\d+) 桁以上の数字", markdown)
        expected = rf"{prefix}-[0-9]{{{digits.group(1)},}}" if digits else None
        if expected != regex_of(source, name):
            problems.append(f"{name} {expected!r} ≠ 本体 {regex_of(source, name)!r}")
    date_word = re.search(r"開始日。`([^`]+)`", markdown)
    if DATE_WORDS.get(date_word.group(1) if date_word else "") != regex_of(source, "DATE"):
        problems.append(f"日付の書式 {date_word and date_word.group(1)!r} ≠ 本体 {regex_of(source, 'DATE')!r}")
    separator = re.search(r"の `No` を `([^`]+)` でつなぐ", markdown)
    if (separator.group(1) if separator else None) != constant(source, "SEPARATOR"):
        problems.append(f"前提の区切り {separator and separator.group(1)!r} ≠ 本体 {constant(source, 'SEPARATOR')!r}")
    amount = re.search(r"円。\*\*(.+?)\*\*", markdown)
    if AMOUNT_WORDS.get(amount.group(1) if amount else "") != regex_of(source, "AMOUNT"):
        problems.append(f"金額の書式 {amount and amount.group(1)!r} ≠ 本体 {regex_of(source, 'AMOUNT')!r}")
    return problems


DATE_WORDS = {"YYYY-MM-DD": "[0-9]{4}-[0-9]{2}-[0-9]{2}"}
AMOUNT_WORDS = {"半角数字だけ": "[0-9]+"}

REFERENCE_MUTATIONS: list[tuple[str, str, str]] = [
    ("schedule.csv の列", "| `前提` |", "| `依存` |"),
    ("estimate.csv の列", "| `根拠` |", "| `備考` |"),
    ("区分", "| `運用費（月額）` |", "| `運用費` |"),
    ("空を許す列", "（`前提` を除く）", "（`根拠` を除く）"),
    ("工程の番号の桁", "`T-` に 3 桁以上の数字", "`T-` に 4 桁以上の数字"),
    ("費用の番号の桁", "`E-` に 3 桁以上の数字", "`E-` に 2 桁以上の数字"),
    ("日付の書式", "開始日。`YYYY-MM-DD`", "開始日。`YYYY/MM/DD`"),
    ("前提の区切り", "の `No` を ` / ` でつなぐ", "の `No` を `, ` でつなぐ"),
    ("金額の書式", "円。**半角数字だけ**", "円。**数字だけ**"),
]


def reference_example(markdown: str) -> tuple[str, str] | None:
    blocks = re.findall(r"```csv\n(.*?)```", section(markdown, "例"), re.S)
    return (blocks[0], blocks[1]) if len(blocks) == 2 else None


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="feasibility-csv-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        for name, result in run_all(scripts, tmp_path / "work").items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result[0]} {result[1][-300:]}")

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        problems = reference_mismatches(source, reference)
        check("本体の定数が references/feasibility-csv.md と一致しない", not problems, "; ".join(problems))
        for name, before, after in REFERENCE_MUTATIONS:
            if reference.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {reference.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(source, reference.replace(before, after))))

        example = reference_example(reference)
        check("references の「例」が 2 つの CSV として読めない", example is not None)
        if example:
            result = run_one(scripts, tmp_path / "example", example[0], example[1])
            check("references の「例」が検査を通らない", result[0] == 0, result[1])

        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            mutated_results = run_all(mutated, tmp_path / f"mutwork{index}")
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）",
                  not as_expected(killer, mutated_results[killer]), mutated_results[killer][1][-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
