#!/usr/bin/env python3
"""`scaffold-estimate.py`（spec-loop の、scaffold の書き起こしの前に、仕様のテストケースが開発に渡る（Red テスト・受入基準）見積もりを数えるスクリプト。#1302）の回帰テスト。

    python3 scripts/test-scaffold-estimate.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-green-list.py` と同じ形。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる**
（`scaffold-estimate.py` は同じ場所の `scaffold.py` と、そこから `check-spec-exit.py`・`merge-versions.py` を読み込む——仕様のケースの数え方を写さない）。
**どの試料も、走らせた前後で正本のファイルが変わらないこと**（何も書かない）を見る。

試料: 正本 `docs/v1/spec/order.md` にテストケースの表（F1-1・F1-2・F1-7・F1-9 の 4 件）と、数えない表（`No` 見出しの Q&A の表）を置き、
`.txt` のファイルにも番号の形の行を置く（数えない）。v2 の試料は `docs/v2/spec/more.md` に F2-1 を足し、重ね合わせた全体を数えることを見る。

**陽性対照**（受入基準の「見積もりの結果を利用者に示す」の元）: 正しい分け方は 0 で、分けた件数・乗る割合・どちらにもできないケースの番号と場所を出す。
**割合が低くても 0**（止める線を決めていない）。

**変異テストを含む。** 写した本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。変異ごとに、
**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、穴が無くても緑になるので）。
**本体の docstring の「守ること」の行の数だけ、変異が要る**（変異の数 ≥ 行の数）。
**例外で落ちて終了コード 1 になった形と、期待した 1 を見分けるため、どの試料も出力の文言も見る。**
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
TARGET = "scaffold-estimate.py"
CHILD_ENV = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}

SPEC = """# 注文

## テストケース

| テストケース | 入力 | 期待 |
| --- | --- | --- |
| F1-1 | 1 | 2 |
| F1-2 | 2 | 4 |
| F1-7 | 画面で 2 回押す | 注文は 1 件だけ |
| F1-9 | 何か | 未定 |

## 質問

| No | 内容 |
| --- | --- |
| Q-001 | 割引は？ |
"""
SPEC_NO_CASES = "# 注文\n\n| No | 内容 |\n| --- | --- |\n| Q-001 | 割引は？ |\n"
SPEC_V2 = "# 追加\n\n| テストケース | 入力 | 期待 |\n| --- | --- | --- |\n| F2-1 | 3 | 6 |\n"
NOTE_TXT = "| F8-1 | 数えない | .txt |\n"

ALL = {"F1-1": {"class": "red"}, "F1-2": {"class": "red"},
       "F1-7": {"class": "acceptance", "reason": "画面で 2 回押す。関数の 1 回の呼び出しでは表せない"},
       "F1-9": {"class": "neither", "reason": "期待が未定"}}


def est(cases: dict) -> str:
    return json.dumps({"cases": cases}, ensure_ascii=False)


def merged(base: dict, **changes) -> dict:
    out = {k: dict(v) for k, v in base.items()}
    for key, value in changes.items():
        out[key.replace("_", "-")] = value
    return out


class Case:
    def __init__(self, name: str, command: str, code: int, *, estimate: str | None = None, spec: str = SPEC, v2: bool = False,
                 docs: bool = True, err: tuple[str, ...] = (), out: tuple[str, ...] = (), absent: tuple[str, ...] = ()):
        self.name, self.command, self.code, self.estimate, self.spec, self.v2 = name, command, code, estimate, spec, v2
        self.docs, self.err, self.out, self.absent = docs, err, out, absent


FIRST = "F1-1\tspec/order.md:7\t| F1-1 | 1 | 2 |"
CASES = [
    Case("list は全部を出す", "list", 0, out=("仕様のテストケース 4 件", FIRST, "F1-2\tspec/order.md:8", "F1-7\tspec/order.md:9\t| F1-7 | 画面で 2 回押す | 注文は 1 件だけ |",
                                       "F1-9\tspec/order.md:10"), absent=("Q-001", "F8-1")),
    Case("list は重ね合わせた全体を数える", "list", 0, v2=True, out=("仕様のテストケース 5 件", "F2-1\tspec/more.md:5")),
    Case("list はケースの表が無ければ 3", "list", 3, spec=SPEC_NO_CASES, err=("テストケースの番号の表が無い",)),
    Case("docs が無ければ 2", "list", 2, docs=False, err=("ディレクトリが無い",)),
    Case("check はケースの表が無ければ 3", "check", 3, spec=SPEC_NO_CASES, estimate=est(ALL), err=("テストケースの番号の表が無い",)),
    Case("正しい分け方は 0", "check", 0, estimate=est(ALL),
         out=("仕様のテストケース 4 件のうち、Red テストにできる 2 件・受入基準に回す 1 件・どちらにもできない 1 件（Red テストだけの割合 50.0%・受入基準まで含めた乗る割合 75.0%）",
              "受入基準に回す: F1-7", "どちらにもできない: F1-9（spec/order.md:10）: 期待が未定", "線は決めていない")),
    Case("割合が低くても 0", "check", 0,
         estimate=est({"F1-1": {"class": "neither", "reason": "a"}, "F1-2": {"class": "neither", "reason": "b"},
                       "F1-7": {"class": "acceptance", "reason": "c"}, "F1-9": {"class": "neither", "reason": "d"}}),
         out=("Red テストにできる 0 件・受入基準に回す 1 件・どちらにもできない 3 件（Red テストだけの割合 0.0%・受入基準まで含めた乗る割合 25.0%）", "どちらにもできない: F1-1（spec/order.md:7）: a",
              "どちらにもできない: F1-2（spec/order.md:8）: b", "どちらにもできない: F1-9（spec/order.md:10）: d")),
    Case("重ね合わせた全体を分ける", "check", 0, v2=True, estimate=est(merged(ALL, **{"F2_1": {"class": "red"}})),
         out=("仕様のテストケース 5 件のうち、Red テストにできる 3 件",)),
    Case("全角の番号は正規化して比べる", "check", 0,
         estimate=est({"Ｆ１－１": {"class": "red"}, "F1-2": {"class": "red"}, "F1-7": ALL["F1-7"], "F1-9": ALL["F1-9"]}),
         out=("Red テストにできる 2 件",)),
    Case("分けていないケース", "check", 1, estimate=est({k: v for k, v in ALL.items() if k != "F1-9"}),
         err=("分けていないケース: F1-9（spec/order.md:10）",), absent=("分けていないケース: F1-1",)),
    Case("仕様に無い番号", "check", 1, estimate=est(merged(ALL, **{"F9_9": {"class": "red"}})), err=("仕様に無い番号を分けている: F9-9",)),
    Case("数えない表・.txt の番号を分けると仕様に無い", "check", 1, estimate=est(merged(ALL, **{"Q_001": {"class": "red"}, "F8_1": {"class": "red"}})),
         err=("仕様に無い番号を分けている: Q-001", "仕様に無い番号を分けている: F8-1")),
    Case("同じ番号を 2 度（正規化の後）", "check", 1, estimate=est({"F1-1": {"class": "red"}, "F1-1 ": {"class": "red"}, "F1-2": {"class": "red"},
                                                           "F1-7": ALL["F1-7"], "F1-9": ALL["F1-9"]}),
         err=("同じ番号を 2 度分けている: F1-1",)),
    Case("同じ番号を 2 度（JSON の同じキー）", "check", 1,
         estimate='{"cases": {"F1-1": {"class": "red"}, "F1-1": {"class": "red"}, "F1-2": {"class": "red"}, '
                  '"F1-7": {"class": "acceptance", "reason": "x"}, "F1-9": {"class": "neither", "reason": "y"}}}',
         err=("同じ番号を 2 度分けている: F1-1（JSON の同じキーが 2 つ）",)),
    Case("class が違う", "check", 1, estimate=est(merged(ALL, **{"F1_1": {"class": "green"}})), err=("F1-1: class が red・acceptance・neither のどれでもない",)),
    Case("acceptance の reason が無い", "check", 1, estimate=est(merged(ALL, **{"F1_7": {"class": "acceptance"}})),
         err=("F1-7: class が acceptance なら reason",)),
    Case("neither の reason が空", "check", 1, estimate=est(merged(ALL, **{"F1_9": {"class": "neither", "reason": "  "}})),
         err=("F1-9: class が neither なら reason",)),
    Case("reason が数", "check", 1, estimate=est(merged(ALL, **{"F1_9": {"class": "neither", "reason": 3}})), err=("F1-9: class が neither なら reason",)),
    Case("reason が複数行", "check", 1, estimate=est(merged(ALL, **{"F1_9": {"class": "neither", "reason": "a\nb"}})),
         err=("F1-9: class が neither なら reason",)),
    Case("red の reason が文字列でない", "check", 1, estimate=est(merged(ALL, **{"F1_1": {"class": "red", "reason": 5}})),
         err=("F1-1: reason が文字列でない",)),
    Case("最上位に余分なキー", "check", 1, estimate=json.dumps({"cases": ALL, "note": "x"}), err=("最上位に決まりの外のキー: note",)),
    Case("cases が配列", "check", 1, estimate=json.dumps({"cases": [ALL]}), err=("`cases` が、番号から項目へのオブジェクト",)),
    Case("cases が空", "check", 1, estimate=json.dumps({"cases": {}}), err=("`cases` が、番号から項目へのオブジェクト",)),
    Case("最上位が配列", "check", 1, estimate="[]", err=("最上位が JSON のオブジェクトでない",)),
    Case("項目が文字列", "check", 1, estimate=est(merged(ALL, **{"F1_1": "red"})), err=("F1-1: 項目がオブジェクトでない",)),
    Case("項目に余分なキー", "check", 1, estimate=est(merged(ALL, **{"F1_1": {"class": "red", "memo": "x"}})), err=("F1-1: 項目に決まりの外のキー: memo",)),
    Case("見積もりのファイルが無い", "check", 2, err=("見積もりのファイルが無い",)),
    Case("JSON として読めない", "check", 2, estimate="{not json", err=("JSON として読めない",)),
]

# (名前, 壊す箇所, 置き換え, 落ちるはずの試料)
MUTATIONS = [
    ("分けていないケースを見ない", "for number, (rel, line) in cases.items() if number not in estimate]", "for number, (rel, line) in cases.items() if False]",
     "分けていないケース"),
    ("仕様に無い番号を見ない", "for number in estimate if number not in cases]", "for number in estimate if False]", "仕様に無い番号"),
    ("正規化の後の重なりを見ない", "        if number in found:", "        if False:", "同じ番号を 2 度（正規化の後）"),
    ("JSON の同じキーを見ない", "        repeated.extend(sorted(", "        [].extend(sorted(", "同じ番号を 2 度（JSON の同じキー）"),
    ("class を見ない", "        if kind not in CLASSES:", "        if False:", "class が違う"),
    ("reason を求めない", "        if kind in NEEDS_REASON and (not isinstance(reason, str)", "        if False and (not isinstance(reason, str)",
     "acceptance の reason が無い"),
    ("reason の 1 行を見ない", '        if kind in NEEDS_REASON and (not isinstance(reason, str) or not reason.strip() or "\\n" in reason.strip()):',
     "        if kind in NEEDS_REASON and (not isinstance(reason, str) or not reason.strip()):", "reason が複数行"),
    ("reason の型を見ない", "        elif reason is not None and not isinstance(reason, str):", "        elif False:", "red の reason が文字列でない"),
    ("最上位の余分なキーを見ない", "    if extra:", "    if False:", "最上位に余分なキー"),
    ("cases の型を見ない", "    if not isinstance(cases, dict) or not cases:", "    if False:", "cases が配列"),
    ("項目の余分なキーを見ない", "        if unknown:", "        if False:", "項目に余分なキー"),
    ("項目の型を見ない", "        if not isinstance(item, dict):", "        if False:", "項目が文字列"),
    ("件数に受入基準を数えない", "    reachable = len(by_class[RED]) + len(by_class[ACCEPTANCE])", "    reachable = len(by_class[RED])", "正しい分け方は 0"),
    ("どちらにもできないを名指しする行を落とす", "    for number in by_class[NEITHER]:", "    for number in by_class[NEITHER][:0]:", "割合が低くても 0"),
    ("割合が低いと止める", "    for line in estimate_lines(cases, estimate):\n        print(line)\n    return 0",
     "    if sum(1 for item in estimate.values() if item[\"class\"] == RED) * 2 < len(cases):\n        return 1\n    for line in estimate_lines(cases, estimate):\n        print(line)\n    return 0",
     "割合が低くても 0"),
    ("見積もりのファイルが無くても進む", "    if not path.is_file():", "    if False:", "見積もりのファイルが無い"),
    ("JSON の読めなさを 2 にしない", "    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:", "    except (OSError, UnicodeDecodeError, RecursionError) as exc:",
     "JSON として読めない"),
    ("ケースが 0 件でも進む", "    if not rows:", "    if False:", "list はケースの表が無ければ 3"),
    ("list が最初の 1 件だけ出す", "    for rel, line, number, text in rows:\n        print(", "    for rel, line, number, text in rows[:1]:\n        print(",
     "list は全部を出す"),
    ("正本に書く", "    estimate = read_estimate(path)\n    problems = coverage(", "    estimate = read_estimate(path)\n    (repo / \"wrote.txt\").write_text(\"x\")\n    problems = coverage(",
     "正しい分け方は 0"),
    ("番号を正規化しない", '    return unicodedata.normalize("NFKC", number).strip()', "    return number", "全角の番号は正規化して比べる"),
    ("版を重ねずに v1 だけ数える", "        problems, _, _, rendered = versions.merge(docs)", "        problems, _, _, rendered = versions.merge(docs, 1)",
     "重ね合わせた全体を分ける"),
    ("docs が無くても進む", "    if not docs.is_dir():", "    if False:", "docs が無ければ 2"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def snapshot(repo: Path) -> dict[str, bytes]:
    return {str(p.relative_to(repo)): p.read_bytes() for p in sorted(repo.rglob("*")) if p.is_file()}


def build(work: Path, case: Case, tag: str) -> Path:
    repo = work / f"repo-{tag}"
    repo.mkdir()
    if case.docs:
        spec = repo / "docs" / "v1" / "spec"
        spec.mkdir(parents=True)
        (spec / "order.md").write_text(case.spec, encoding="utf-8")
        (spec / "note.txt").write_text(NOTE_TXT, encoding="utf-8")
        if case.v2:
            (repo / "docs" / "v2" / "spec").mkdir(parents=True)
            (repo / "docs" / "v2" / "spec" / "more.md").write_text(SPEC_V2, encoding="utf-8")
    if case.estimate is not None:
        (repo / "build").mkdir()
        (repo / "build" / "scaffold-estimate.json").write_text(case.estimate, encoding="utf-8")
    return repo


def run_case(work: Path, scripts: Path, case: Case, tag: str) -> str | None:
    repo = build(work, case, tag)
    before = snapshot(repo)
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), case.command, "--repo", str(repo)],
                          capture_output=True, text=True, timeout=120, env=CHILD_ENV)
    if proc.returncode != case.code:
        return f"終了コードが {proc.returncode}（期待 {case.code}）: {proc.stdout[-400:]}{proc.stderr[-400:]}"
    for needle in case.err:
        if needle not in proc.stderr:
            return f"標準エラーに {needle!r} が無い: {proc.stderr[-400:]}"
    for needle in case.out:
        if needle not in proc.stdout:
            return f"標準出力に {needle!r} が無い: {proc.stdout[-400:]}"
    for needle in case.absent:
        if needle in proc.stdout or needle in proc.stderr:
            return f"出力に {needle!r} が出ている"
    if snapshot(repo) != before:
        return "正本のファイルが変わった（何も書かないはず）"
    return None


def docstring_rules(path: Path) -> int:
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    block = doc.split("**守ること**", 1)[1].split("\n\n", 1)[1].split("\n\n", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("- "))


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="test-scaffold-estimate-")).resolve()
    assert REAL_REPO not in work.parents
    try:
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))

        print("正しい本体")
        for index, case in enumerate(CASES):
            problem = run_case(work, scripts, case, f"ok{index}")
            check(f"試料: {case.name}", problem is None, problem or "")

        print("変異テスト")
        by_name = {case.name: case for case in CASES}
        pristine = (scripts / TARGET).read_text(encoding="utf-8")
        for index, (name, old, new, target) in enumerate(MUTATIONS):
            count = pristine.count(old)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            if target not in by_name:
                check(f"変異の試料が無い: {name}", False, target)
                continue
            (scripts / TARGET).write_text(pristine.replace(old, new), encoding="utf-8")
            try:
                problem = run_case(work, scripts, by_name[target], f"mut{index}")
            finally:
                (scripts / TARGET).write_text(pristine, encoding="utf-8")
            check(f"変異が素通りした: {name}（試料: {target}）", problem is not None)
        rules = docstring_rules(SCRIPTS / TARGET)
        check("本体の docstring の「守ること」の各行に変異がある（変異の数 ≥ 行の数）", rules > 0 and len(MUTATIONS) >= rules,
              f"変異 {len(MUTATIONS)}・行 {rules}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
