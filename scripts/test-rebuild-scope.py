#!/usr/bin/env python3
"""`rebuild-scope.py`（spec-loop の、仮回答と推奨で決めた事項の台帳から作り直す範囲を引くスクリプト。#875）の回帰テスト。

    python3 scripts/test-rebuild-scope.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-qa-csv.py` と同じ形。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、本物の GitHub には届かない（本体は `gh` を呼ばない。
入力の JSON は `gh issue list --json number,title,state,body` と同じ鍵の試料で、本物の出力の形は見ない）。

**spec-loop の Issue の本文は、本物の `scaffold.py --provisional` で作る**——手で書いた本文に当てると、生成の形が変わっても緑のままになる。
**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる**（正本リポジトリで単体で動くこと）。

**守ること**（各行に変異が 1 つ以上ある——下の `MUTATIONS`）:

- Q&A の No から、それを根拠にした spec-loop の Issue と、その受入基準のケースを引く（表の `（暫定）` を外して読む）
- 機能の `qa` だけが指す No は「ケースに無い（機能全体）」と言う（`## Q&A の回答` の節と `## 仕様` の `- 仮回答: ` の行を読む）
- 確認の Issue を、印 `<!-- cruise-decision: #<親> -->` でも題の `要確認: ` でも見分け、`決めた値: `・`影響する Issue: ` を読む
- 台帳の 2 行が無い確認の Issue・形に反する `影響する Issue: ` の行（説明の中の番号を数えない）・確認の Issue でない番号・入力に無い番号・
  入力に無い影響する Issue・本文に無い No は名指しして 1（引けたものは出す）
- 入力の形が違えば 2（どの Issue が違うかを言う）

**変異テストを含む。** 写した本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。変異ごとに、
**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、穴が無くても緑になるので）。

**写しの突き合わせ**: 確認の Issue の 2 行の頭（本体の `DECIDED`・`AFFECTS`）が dev-loop の `references/absent-lines.md` の
「確認の Issue の書き方」に在ること（陽性対照つき）。仮回答の印は本体が `scaffold.py` の定数を読む（写さない）。
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "rebuild-scope.py"
ABSENT_LINES = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "references" / "absent-lines.md"

HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
QA = (HEADER
      + "Q-001,要求確定（決定表）,シルバーで 10000 円未満の割引は？,A: 割引なし / B: 3% 割引,A,理由,"
        "A（暫定で採用。業務部 2026-10-21 の指示）,決定表 4 行目,暫定反映,\n"
      + "Q-002,仕様レビュー（Red Team）,金額が負なら？,A: 拒否する / B: 0 とみなす,A,理由,A（業務部が回答）,spec/order.md,反映済み,\n")
SPEC = "# 注文\n\n割引と取り消し。\n"
IR = {
    "spec_ir_version": 1, "title": "注文",
    "features": [
        {"id": "F-001", "title": "割引額を計算する", "source": ["spec/order.md"], "qa": ["Q-001"],
         "operation": {"id": "calc_discount", "method": "POST", "path": "/orders/discount",
                       "input": {"amount": {"type": "integer"}}, "output": {"discount": {"type": "integer"}},
                       "errors": ["INVALID_AMOUNT"]},
         "cases": [{"id": "F-001-C1", "title": "10000 円未満は割引なし", "input": {"amount": 9999},
                    "expected": {"discount": 0}, "qa": ["Q-001"]},
                   {"id": "F-001-C2", "title": "金額が負なら拒否する", "input": {"amount": -1},
                    "error": "INVALID_AMOUNT", "qa": ["Q-002"]}]},
        # 機能の qa だけが Q-001（暫定）と Q-002 を指す——どのケースも指さない
        {"id": "F-002", "title": "注文を取り消せるか", "source": ["spec/order.md"], "qa": ["Q-001", "Q-002"],
         "operation": {"id": "can_cancel", "method": "GET", "path": "/orders/cancelable",
                       "input": {"shipped": {"type": "boolean"}}, "output": {"ok": {"type": "boolean"}}},
         "cases": [{"id": "F-002-C1", "title": "発送前なら取り消せる", "input": {"shipped": False}, "expected": {"ok": True}}]},
    ],
}


def decision(marker: bool, title: str, lines: str) -> tuple[str, str]:
    body = ("<!-- cruise-decision: #877 -->\n\n" if marker else "") + (
        "- 何が起きたか: 推奨で決めた\n- あなたが選べること: A（推奨）／B\n- 何もしなければ: A のまま\n\n"
        "重さ: 済んだこと（取り消すなら revert が要る）\n" + lines + "\n## 背景\n\n背景\n")
    return title, body


def issues_json(bodies: dict[str, str]) -> list[dict]:
    t20, b20 = decision(True, "要確認: 返品の受付期間を 7 日にした", "決めた値: 7 日\n影響する Issue: #11, #12\n")
    t21, b21 = decision(True, "返品の受付期間（前の書き方）", "")  # 印だけで題は前の形、台帳の行が無い
    t23, b23 = decision(False, "要確認: 印の無い確認の Issue", "決めた値: B\n影響する Issue: なし\n")
    t24, b24 = decision(True, "要確認: 説明つきの行", "決めた値: C\n影響する Issue: #11（#12 の後続）\n")
    t25, b25 = decision(True, "要確認: 入力に無い Issue を指す", "決めた値: D\n影響する Issue: #11, #99\n")
    return [
        {"number": 11, "title": "F-001: 割引額を計算する", "state": "OPEN", "body": bodies["F-001"]},
        {"number": 12, "title": "F-002: 注文を取り消せるか", "state": "CLOSED", "body": bodies["F-002"]},
        {"number": 20, "title": t20, "state": "OPEN", "body": b20},
        {"number": 21, "title": t21, "state": "OPEN", "body": b21},
        {"number": 22, "title": "ふつうの Issue", "state": "OPEN", "body": "Q-001 に触れているが spec-loop の Issue ではない\n"},
        {"number": 23, "title": t23, "state": "CLOSED", "body": b23},
        {"number": 24, "title": t24, "state": "OPEN", "body": b24},
        {"number": 25, "title": t25, "state": "OPEN", "body": b25},
    ]


class Case:
    def __init__(self, name: str, args: tuple[str, ...], code: int, has: tuple[str, ...] = (), lacks: tuple[str, ...] = (),
                 data=None):
        self.name, self.args, self.code, self.has, self.lacks, self.data = name, args, code, has, lacks, data


CASES = [
    Case("暫定の Q-001", ("Q-001",), 0,
         ("Q-001（仮回答——本文に印がある）: 作り直す範囲 2 件", "#11 F-001: 割引額を計算する [OPEN]（F-001）——受入基準 `F-001-C1`",
          "#12 F-002: 注文を取り消せるか [CLOSED]（F-002）——ケースに無い（機能全体）"), ("`F-001-C2`", "#22")),
    Case("確定の Q-002", ("Q-002",), 0,
         ("Q-002: 作り直す範囲 2 件", "（F-001）——受入基準 `F-001-C2`", "（F-002）——ケースに無い（機能全体）"),
         ("仮回答", "`F-001-C1`")),
    Case("確認の Issue", ("#20",), 0, ("#20 要確認: 返品の受付期間を 7 日にした [OPEN]", "  決めた値: 7 日",
                                     "  影響する Issue: 2 件（作り直す範囲）", "  - #11 F-001: 割引額を計算する [OPEN]", "  - #12 F-002: 注文を取り消せるか [CLOSED]")),
    Case("印の無い確認の Issue（題で見分ける）", ("23",), 0, ("決めた値: B", "影響する Issue: なし")),
    Case("台帳の行が無い確認の Issue", ("#21",), 1, ("台帳の行（決めた値:・影響する Issue:）が無い",)),
    Case("影響する Issue に説明を添えた行", ("#24",), 1, ("影響する Issue: の行が決まりの形でない（'#11（#12 の後続）'）",),
         ("#12 F-002",)),
    Case("影響する Issue が入力に無い", ("#25",), 1, ("#99（入力に無い", "#11 F-001")),
    Case("確認の Issue でない", ("#22",), 1, ("#22: 確認の Issue でない",)),
    Case("入力に無い番号", ("#99",), 1, ("#99: 入力に無い",)),
    Case("本文に無い No", ("Q-S-009",), 1, ("Q-S-009: 根拠にした spec-loop の Issue が無い",)),
    Case("引けるものと引けないもの", ("Q-001", "#22"), 1, ("作り直す範囲 2 件", "確認の Issue でない")),
    Case("一覧", (), 0, ("仮回答（本文に仮回答の印がある Q&A）: 1 件", "  Q-001: #11（F-001）、#12（F-002）",
                        "推奨で決めた事項（確認の Issue）: 5 件（開いているもの 4 件）", "#24 要確認: 説明つきの行 [OPEN]——影響する Issue: の行が決まりの形でない",
                        "#20 要確認: 返品の受付期間を 7 日にした [OPEN]——決めた値: 7 日／影響する Issue: #11、#12",
                        "#21 返品の受付期間（前の書き方） [OPEN]——台帳の行が無い", "#23 要確認: 印の無い確認の Issue [CLOSED]——決めた値: B"),
         ("Q-002: #",)),
    Case("No でも番号でもない引数", ("foo",), 2, ("'foo': Q&A の No",)),
    Case("JSON でない", (), 2, ("読めない",), data="{"),
    Case("配列でない", (), 2, ("Issue の配列でない",), data="{}"),
    Case("本文が文字列でない", (), 2, ("0 番目が Issue の形でない",), data=json.dumps([{"number": 1, "title": "t", "body": 1}])),
]

# (名前, 壊す箇所, 置き換え, 落ちるはずの試料)
MUTATIONS = [
    ("表の暫定の印を外さない", "                    text = text[: -len(scaffold.PROVISIONAL_CELL)]\n", "                    pass\n",
     "暫定の Q-001"),
    ("仕様の行を読まない", "            if line.startswith(scaffold.PROVISIONAL_LINE):", "            if False:", "一覧"),
    ("Q&A の回答の節を読まない", "section(body, scaffold.SECTIONS[3])", 'section(body, "## 無い節")', "確定の Q-002"),
    ("ケースに無いのに機能全体と言わない", 'if cases else "ケースに無い（機能全体）"', 'if cases else ""', "確定の Q-002"),
    ("確認の Issue を印で見分けない", 'return bool(DECISION_MARKER.search(issue["body"])) or ', "return ",
     "台帳の行が無い確認の Issue"),
    ("確認の Issue を題で見分けない", ' or issue["title"].startswith(DECISION_TITLE)', "",
     "印の無い確認の Issue（題で見分ける）"),
    ("影響する Issue を読まない", 'self.affects = [int(n) for n in re.findall(r"#([0-9]+)", rest)]', "self.affects = []",
     "確認の Issue"),
    ("台帳の行が無いのを引けたと言う", "    if d.value is None or d.affects is None:\n        missing",
     "    if False:\n        missing", "台帳の行が無い確認の Issue"),
    ("説明の中の番号も影響する Issue に数える", "                elif AFFECTS_LIST.fullmatch(rest):", "                elif True:",
     "影響する Issue に説明を添えた行"),
    ("入力に無い影響する Issue でも 0", "    return not absent, out", "    return True, out", "影響する Issue が入力に無い"),
    ("引けない番号でも 0", "        code = code or (0 if ok else 1)", "        code = 0", "確認の Issue でない"),
    ("入力の Issue の形を見ない", "        if not (isinstance(issue, dict)", "        if False and not (isinstance(issue, dict)",
     "本文が文字列でない"),
    ("spec-loop の Issue を見分けない", 'handoffs = [Handoff(i) for i in issues if i["body"].startswith(HANDOFF_PREFIX)]',
     "handoffs = []", "暫定の Q-001"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def make_bodies(work: Path, scripts: Path) -> dict[str, str]:
    """本物の `scaffold.py --provisional` で本文を作る。"""
    repo = work / "repo"
    base = repo / "docs" / "v1"
    (base / "shared").mkdir(parents=True)
    (base / "spec").mkdir(parents=True)
    (base / "shared" / "qa.csv").write_text(QA, encoding="utf-8")
    (base / "spec" / "order.md").write_text(SPEC, encoding="utf-8")
    (base / "spec" / "spec_ir.json").write_text(json.dumps(IR, ensure_ascii=False, indent=2), encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(scripts / "scaffold.py"), "--repo", str(repo), "--provisional"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    issues = repo / "build" / "scaffold" / "issues"
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(issues.glob("F-*.md"))}


def run_case(scripts: Path, data: Path, case: Case) -> str | None:
    target = data
    if case.data is not None:
        target = data.parent / f"bad-{abs(hash(case.name))}.json"
        target.write_text(case.data, encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), "--issues", str(target), *case.args],
                          capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    if proc.returncode != case.code:
        return f"exit={proc.returncode}（期待 {case.code}）{out[-500:]}"
    for needle in case.has:
        if needle not in out:
            return f"出力に {needle!r} が無い: {out[-500:]}"
    for needle in case.lacks:
        if needle in out:
            return f"出力に {needle!r} がある: {out[-500:]}"
    return None


def constant(source: str, name: str):
    found = re.search(rf"^{name} = (.+)$", source, flags=re.MULTILINE)
    return ast.literal_eval(found.group(1)) if found else None


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="test-rebuild-scope-")).resolve()
    assert REAL_REPO not in work.parents
    try:
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        bodies = make_bodies(work, scripts)
        check("scaffold が F-001・F-002 の本文を作った", sorted(bodies) == ["F-001", "F-002"], f"{sorted(bodies)}")
        data = work / "issues.json"
        data.write_text(json.dumps(issues_json(bodies), ensure_ascii=False), encoding="utf-8")

        print("正しい本体")
        for case in CASES:
            problem = run_case(scripts, data, case)
            check(f"試料: {case.name}", problem is None, problem or "")

        print("写しの突き合わせ")
        source = (scripts / TARGET).read_text(encoding="utf-8")
        doc = ABSENT_LINES.read_text(encoding="utf-8")
        decided, affects = constant(source, "DECIDED"), constant(source, "AFFECTS")
        for name, value in (("DECIDED", decided), ("AFFECTS", affects)):
            check(f"{name} が absent-lines.md の確認の Issue の書き方に無い",
                  isinstance(value, str) and f"**`{value}" in doc.split("## 確認の Issue の書き方", 1)[1], f"{value!r}")
        check("陽性対照: 言い換えると当たらない",
              f"**`{decided}" not in doc.replace(decided or "?", "決定した値: ").split("## 確認の Issue の書き方", 1)[1])

        print("変異テスト")
        by_name = {case.name: case for case in CASES}
        pristine = source
        for name, old, new, target in MUTATIONS:
            count = pristine.count(old)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            (scripts / TARGET).write_text(pristine.replace(old, new), encoding="utf-8")
            try:
                problem = run_case(scripts, data, by_name[target])
            finally:
                (scripts / TARGET).write_text(pristine, encoding="utf-8")
            check(f"変異が素通りした: {name}（試料: {target}）", problem is not None)
        rules = docstring_rules()
        check("docstring の「守ること」の各行に変異がある（変異の数 ≥ 行の数）", len(MUTATIONS) >= rules,
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


def docstring_rules() -> int:
    doc = ast.get_docstring(ast.parse(Path(__file__).read_text(encoding="utf-8"))) or ""
    block = doc.split("**守ること**", 1)[1].split("\n\n", 1)[1].split("\n\n", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("- "))


if __name__ == "__main__":
    sys.exit(main())
