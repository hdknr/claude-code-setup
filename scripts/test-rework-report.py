#!/usr/bin/env python3
"""`rework-report.py`（spec-loop の、PC の中に貯めた作り直しの量の記録を分析するスクリプト。#989）の回帰テスト。

    python3 scripts/test-rework-report.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-rework-metrics.py` と同じ形。

**このテストは実環境を触らない。** 記録のファイルはすべて一時ディレクトリに書き、`HOME` と子プロセスの cwd を一時ディレクトリに差し替える——
利用者の `~/.claude/spec-loop/` は読まない（既定のパスの試料も一時の `HOME` の下に置く）。読まないことはこの差し替えで決まり、
終わった後のアサートが見るのは書いていないこと（mtime）だけである——読んだことは mtime に出ない。
**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる**（正本リポジトリで単体で動くこと）。

**守ること**（各行に変異が 1 つ以上ある——下の `MUTATIONS`）:

- 案件 × 時点の表を、案件の名前の順・案件の中はコミットの日付の順（同じ日付ならファイルの順）で出す
- 同じ案件の隣り合う時点の差を「後 − 前」で出す
- 合計は案件ごとにいちばん後の時点の記録だけを足す（累計を二重に足さない）
- 率（回答が変わった率・値を変えた率・1 件あたりの差分の行）を決まりの分母で出し、分母が 0 なら `-` を出す（割らない）
- 読めない行（JSON として読めない・鍵が足りない・値の型が違う・負の数）は名指しして 1。空白だけの行は読み飛ばす
- 記録のファイルが無ければ 2
- `--log` が無ければ `SPEC_LOOP_REWORK_LOG`、それも無ければ `~/.claude/spec-loop/rework-metrics.jsonl` を読む（決め方は `rework-metrics.py` の `record_path`）

**変異テストを含む。** 写した本体（`rework-report.py` と、記録の形を持つ `rework-metrics.py`）を 1 箇所ずつ壊し、
**名指しした試料が期待どおりでなくなること**を確かめる。変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。

**写さないことの突き合わせ**: `rework-report.py` のコード（docstring を除く）が、記録のファイルの既定のパス・環境変数の名前・鍵の一覧を
自分で持たず、`rework-metrics.py` の `record_path`・`read_records`・`RECORD_COUNTS` を読むこと（陽性対照つき）。
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "rework-report.py"
METRICS = "rework-metrics.py"

ZERO = {
    "provisional": 0, "confirmed": 0, "changed": 0, "same": 0, "unknown": 0, "vanished": 0, "still": 0, "provisional_now": 0,
    "decisions": 0, "kept": 0, "decision_changed": 0, "decision_none": 0, "decision_malformed": 0,
    "rework_items": 0, "rework_issues": 0, "rework_prs": 0, "rework_lines": 0, "uncounted": 0,
}


def rec(case: str, ref: str, date: str, commit: str, **counts: int) -> dict:
    return {"case": case, "ref": ref, "commit": commit * 40, "date": date, "recorded": "2026-11-12", **ZERO, **counts}


# ファイルの順は日付の順と違えてある（A は後の時点が先・C は同じ日付の 2 つが SHA の逆順）
RECORDS = [
    rec("A", "release-v2", "2026-11-01", "b", provisional=8, confirmed=6, changed=3, same=3, decisions=4, kept=2, decision_changed=2,
        rework_items=5, rework_issues=3, rework_prs=4, rework_lines=100, uncounted=1),
    rec("C", "v1", "2026-09-01", "f", provisional=1),
    rec("A", "release-v1", "2026-10-01", "a", provisional=5, confirmed=3, changed=1, same=2, decisions=2, kept=1, decision_changed=1,
        rework_items=2, rework_issues=1, rework_prs=2, rework_lines=30),
    rec("C", "v2-rc", "2026-09-10", "e", provisional=2, confirmed=1, changed=1, rework_items=1, rework_lines=5),
    rec("B", "release-v1", "2026-10-15", "c", provisional=4, confirmed=4, changed=1, same=3, decisions=2, kept=2,
        rework_items=1, rework_issues=1, rework_prs=1, rework_lines=20),
    rec("C", "v2", "2026-09-10", "d", provisional=3, confirmed=2, changed=1, rework_items=1, rework_lines=7),
]

ALL_ROWS = (
    "## 記録（", "・6 件・案件 3 件）",
    "| A | release-v1（2026-10-01・aaaaaaa） | 5 | 3 | 1 | 2 | 1 | 2 | 1 | 2 | 30 | 0 |",
    "| A | release-v2（2026-11-01・bbbbbbb） | 8 | 6 | 3 | 4 | 2 | 5 | 3 | 4 | 100 | 1 |",
    "| B | release-v1（2026-10-15・ccccccc） | 4 | 4 | 1 | 2 | 0 | 1 | 1 | 1 | 20 | 0 |",
    "| C | v1（2026-09-01・fffffff） | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |",
    "| A | release-v1（2026-10-01・aaaaaaa） → release-v2（2026-11-01・bbbbbbb） | +3 | +3 | +2 | +2 | +1 | +3 | +2 | +2 | +70 |",
    "| C | v1（2026-09-01・fffffff） → v2-rc（2026-09-10・eeeeeee） | +1 | +1 | +1 | 0 | 0 | +1 | 0 | 0 | +5 |",
    "| C | v2-rc（2026-09-10・eeeeeee） → v2（2026-09-10・ddddddd） | +1 | +1 | 0 | 0 | 0 | 0 | 0 | 0 | +2 |",
    "## 合計（案件ごとにいちばん後の時点の記録を足す・3 案件）",
    "- 仮回答 15 件・確かめた 12 件・回答が変わった 5 件——回答が変わった率 42%（5/12）",
    "- 確認の Issue 6 件・推奨のまま 4 件・変えた 2 件——値を変えた率 33%（2/6）",
    "- 変わった件 7 件・作り直しの元の印の Issue 4 件・PR 5 件・差分 127 行——変わった 1 件あたりの差分の行 18.1",
    "- 数えきれないものがあった記録: 1 件",
)


def lines(records: list) -> str:
    return "".join((r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)) + "\n" for r in records)


class Case:
    def __init__(self, name: str, code: int, has: tuple[str, ...] = (), lacks: tuple[str, ...] = (), *, log: str | None = "",
                 env: dict[str, str] | None = None, order: tuple[str, ...] = ()):
        self.name, self.code, self.has, self.lacks = name, code, has, lacks
        self.log = log  # 空なら `--log` を渡さない。None 以外の名前は一時ディレクトリの下のファイル
        self.env = env or {}  # 値の `{work}` は一時ディレクトリに置き換える
        self.order = order  # 出力の中で、この順に現れること


CASES = [
    Case("全部", 0, ALL_ROWS, ("読めない行",), log="all.jsonl", order=ALL_ROWS[2:6]),
    Case("読めない行", 1, (
        "・1 件・案件 1 件）", "| B | release-v1（2026-10-15・ccccccc） |",
        "読めない行——", "broken.jsonl:2: JSON として読めない", "broken.jsonl:3: 鍵が足りない（rework_lines・uncounted）",
        "broken.jsonl:4: 値の型が違う（changed）", "broken.jsonl:5: 値の型が違う（rework_lines）", "broken.jsonl:6: 記録の形でない",
        "broken.jsonl:8: 値の型が違う（changed）",  # 真偽値は数でない
    ), ("broken.jsonl:7",), log="broken.jsonl"),  # 7 行目は空行
    Case("無いファイル", 2, ("記録のファイルが無い", "出していない"), log="missing.jsonl"),
    Case("空のファイル", 0, ("## 記録（", "・0 件・案件 0 件）", "- 時点が 2 つ以上ある案件が無い", "回答が変わった率 -", "値を変えた率 -",
                             "1 件あたりの差分の行 -"), ("| 案件 |",), log="empty.jsonl"),
    Case("分母が 0", 0, ("回答が変わった率 -", "値を変えた率 -", "変わった 1 件あたりの差分の行 -", "- 時点が 2 つ以上ある案件が無い"), log="zero.jsonl"),
    Case("環境変数", 0, ("all.jsonl・6 件",), log="", env={"SPEC_LOOP_REWORK_LOG": "{work}/all.jsonl"}),
    Case("既定のパス", 0, ("rework-metrics.jsonl・1 件", "| B | release-v1"), log=""),
]

# (名前, 壊すファイル, 壊す箇所, 置き換え, 落ちるはずの試料)
MUTATIONS = [
    ("日付で並べない", TARGET, 'recs.sort(key=lambda r: r["date"])', "recs.sort(key=lambda r: 0)", "全部"),
    ("同じ日付を SHA の順に並べる", TARGET, 'recs.sort(key=lambda r: r["date"])', 'recs.sort(key=lambda r: (r["date"], r["commit"]))', "全部"),
    ("案件の名前の順に並べない", TARGET, "        for case in sorted(by_case):\n            for rec in by_case[case]:",
     "        for case in by_case:\n            for rec in by_case[case]:", "全部"),
    ("差を前 − 後で出す", TARGET, "signed(b[k] - a[k])", "signed(a[k] - b[k])", "全部"),
    ("記録を全部足す", TARGET, "latest = [by_case[case][-1] for case in sorted(by_case)]",
     "latest = [r for case in sorted(by_case) for r in by_case[case]]", "全部"),
    ("いちばん前の時点を足す", TARGET, "latest = [by_case[case][-1] for case in sorted(by_case)]",
     "latest = [by_case[case][0] for case in sorted(by_case)]", "全部"),
    ("変えた率の分母に結果なしを入れる", TARGET, "total['kept'] + total['decision_changed']", "total['decisions'] + 1", "全部"),
    ("回答が変わった率を仮回答で割る", TARGET, "rate(total['changed'], total['confirmed'])", "rate(total['changed'], total['provisional'])", "全部"),
    ("1 件あたりを PR で割る", TARGET, "per(total['rework_lines'], total['rework_items'])", "per(total['rework_lines'], total['rework_prs'])", "全部"),
    ("率の分母が 0 でも割る", TARGET, 'return "-" if den == 0 else f"{100 * num / den:.0f}%（{num}/{den}）"',
     'return f"{100 * num / den:.0f}%（{num}/{den}）"', "分母が 0"),
    ("1 件あたりの分母が 0 でも割る", TARGET, 'return "-" if den == 0 else f"{num / den:.1f}"', 'return f"{num / den:.1f}"', "分母が 0"),
    ("数えきれない記録を数えない", TARGET, "sum(1 for r in latest if r['uncounted'])", "0", "全部"),
    ("読めない行があっても 0", TARGET, "    return 1 if bad else 0", "    return 0", "読めない行"),
    ("読めない行を名指ししない", TARGET, '        print(f"読めない行——{line}", file=sys.stderr)', "        pass", "読めない行"),
    ("無いファイルを空と読む", TARGET, "        if not path.is_file():", "        if False:", "無いファイル"),
    ("--log を見ない", TARGET, "path = Path(args.log) if args.log else metrics.record_path()", "path = metrics.record_path()", "全部"),
    ("環境変数を見ない", METRICS, "return Path(env) if env else Path.home() / RECORD_DEFAULT", "return Path.home() / RECORD_DEFAULT", "環境変数"),
    ("既定のパスを HOME の下にしない", METRICS, "return Path(env) if env else Path.home() / RECORD_DEFAULT",
     "return Path(env) if env else Path.cwd() / RECORD_DEFAULT", "既定のパス"),
    ("鍵の欠けを見ない", METRICS, "    if missing:\n", "    if False:\n", "読めない行"),
    ("型を見ない", METRICS, "    if wrong:\n", "    if False:\n", "読めない行"),
    ("負の数を許す", METRICS, " or rec[k] < 0]", "]", "読めない行"),
    ("真偽値を数と読む", METRICS, "type(rec[k]) is not int", "not isinstance(rec[k], int)", "読めない行"),
    ("オブジェクトでない行を見ない", METRICS, "    if not isinstance(rec, dict):\n        return", "    if False:\n        return", "読めない行"),
    ("空白だけの行を読めない行と読む", METRICS, "        if not line.strip():\n            continue\n", "", "全部"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def run_case(scripts: Path, work: Path, env: dict[str, str], case: Case) -> str | None:
    args = [sys.executable, "-I", str(scripts / TARGET)]
    if case.log:
        args += ["--log", str(work / case.log)]
    run_env = dict(env)
    run_env.update({k: v.replace("{work}", str(work)) for k, v in case.env.items()})
    proc = subprocess.run(args, capture_output=True, text=True, env=run_env, cwd=work)  # cwd も一時ディレクトリ（1 パス目の CR3）
    out = proc.stdout + proc.stderr
    if proc.returncode != case.code:
        return f"exit={proc.returncode}（期待 {case.code}）{out[-800:]}"
    for needle in case.has:
        if needle not in out:
            return f"出力に {needle!r} が無い: {out[-1500:]}"
    for needle in case.lacks:
        if needle in out:
            return f"出力に {needle!r} がある: {out[-800:]}"
    places = [out.find(needle) for needle in case.order]
    if places != sorted(places):
        return f"出力の順が違う（{case.order}）: {out[-1500:]}"
    return None


def code_of(source: str) -> str:
    """docstring を除いたコード。"""
    tree = ast.parse(source)
    doc = ast.get_docstring(tree, clean=False)
    return source.replace(doc, "", 1) if doc else source


def borrows(code: str) -> bool:
    return (all(s in code for s in ("metrics.record_path()", "metrics.read_records(", "metrics.RECORD_COUNTS"))
            and not any(s in code for s in ("rework-metrics.jsonl", "SPEC_LOOP_REWORK_LOG", '"provisional_now"')))


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="test-rework-report-")).resolve()
    assert REAL_REPO not in work.parents
    real_log = Path(os.path.expanduser("~")) / ".claude" / "spec-loop" / "rework-metrics.jsonl"
    real_before = real_log.stat().st_mtime_ns if real_log.exists() else None
    try:
        home = work / "home"
        home.mkdir()
        env = {k: v for k, v in os.environ.items() if k != "SPEC_LOOP_REWORK_LOG"}
        env["HOME"] = str(home)
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        (work / "all.jsonl").write_text(lines(RECORDS) + "\n  \n", encoding="utf-8")  # 末尾の空白だけの行は読み飛ばす
        broken = [RECORDS[4], "{not json", {k: v for k, v in RECORDS[0].items() if k not in ("rework_lines", "uncounted")},
                  dict(RECORDS[0], changed="3"), dict(RECORDS[0], rework_lines=-1), "[1, 2]", "", dict(RECORDS[0], case="X", changed=True)]
        text = lines(broken)
        (work / "broken.jsonl").write_text(text, encoding="utf-8")
        (work / "empty.jsonl").write_text("", encoding="utf-8")
        (work / "zero.jsonl").write_text(lines([rec("Z", "v1", "2026-10-01", "9", provisional=2)]), encoding="utf-8")
        default = home / ".claude" / "spec-loop" / "rework-metrics.jsonl"
        default.parent.mkdir(parents=True)
        default.write_text(lines([RECORDS[4]]), encoding="utf-8")

        print("正しい本体")
        for case in CASES:
            problem = run_case(scripts, work, env, case)
            check(f"試料: {case.name}", problem is None, problem or "")

        print("写さないことの突き合わせ")
        report_code = code_of((scripts / TARGET).read_text(encoding="utf-8"))
        check("rework-report.py が記録の形を rework-metrics.py から読む", borrows(report_code))
        check("陽性対照: 既定のパスを写すと突き合わせが落ちる",
              not borrows(report_code + '\nX = Path.home() / ".claude" / "spec-loop" / "rework-metrics.jsonl"\n'))
        check("陽性対照: record_path を読まないと突き合わせが落ちる", not borrows(report_code.replace("metrics.record_path()", "None")))

        print("変異テスト")
        by_name = {case.name: case for case in CASES}
        pristine = {name: (scripts / name).read_text(encoding="utf-8") for name in (TARGET, METRICS)}
        for name, filename, old, new, target in MUTATIONS:
            count = pristine[filename].count(old)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"{filename} に壊す箇所が {count} 回現れる")
                continue
            (scripts / filename).write_text(pristine[filename].replace(old, new), encoding="utf-8")
            try:
                problem = run_case(scripts, work, env, by_name[target])
            finally:
                (scripts / filename).write_text(pristine[filename], encoding="utf-8")
            check(f"変異が素通りした: {name}（試料: {target}）", problem is not None)
        rules = docstring_rules()
        check("docstring の「守ること」の各行に変異がある（変異の数 ≥ 行の数）", len(MUTATIONS) >= rules, f"変異 {len(MUTATIONS)}・行 {rules}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    real_after = real_log.stat().st_mtime_ns if real_log.exists() else None
    check("利用者の ~/.claude/spec-loop/rework-metrics.jsonl に書いていない", real_before == real_after)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


def docstring_rules() -> int:
    doc = ast.get_docstring(ast.parse(Path(__file__).read_text(encoding="utf-8"))) or ""
    block = doc.split("**守ること**", 1)[1].split("\n\n", 1)[1].split("\n\n", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("- "))


if __name__ == "__main__":
    sys.exit(main())
