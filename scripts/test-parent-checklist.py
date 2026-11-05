#!/usr/bin/env python3
"""`parent-checklist.py`（spec-loop の、登録した Issue から依存の連鎖を cruise の親 Issue の書式で出すスクリプト。#876）の回帰テスト。

    python3 scripts/test-parent-checklist.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-rebuild-scope.py` と同じ形。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、本物の GitHub には届かない（本体は `gh` を呼ばない。
入力の JSON は `gh issue list --json number,title,state,body` と同じ鍵の試料で、本物の出力の形は見ない）。

**`issues.json` と本文は、本物の `scaffold.py` で作る**（`--bundle` の有無で 2 組）——手で書いた索引に当てると、生成の形が変わっても緑のままになる。
**出した行は、本物の dev-loop の `parent-issue.py show` に通す**（`--body-file`。子 Issue の本文を取る `gh` は `PATH` の先頭に置いた偽物で、
失敗させる——本物の `gh` には届かない）。**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。**

試料の依存（`called_by`）: F-003 が F-001 から呼ばれ、F-002 が F-003 から呼ばれる——F-001 は F-003 に、F-003 は F-002 に依存する
（`issues.json` の順は F-001・F-002・F-003 で、依存先が先に来る順はその逆向き）。`--bundle F-002,F-003` の組では、F-001 が組の
2 つ目の機能（F-003）に依存する。

**守ること**（各行に変異が 1 つ以上ある——下の `MUTATIONS`）:

- 項目の Issue は、本文が生成した本文と同じものだけ（同じ機能の印を持つが本文の違う Issue を当てない）
- 改行（`\\r\\n`）と前後の空白はならして比べる
- 同じ本文の Issue が 2 件以上あれば 1
- 本文の Issue が無い項目があれば 1 で、一覧を出さない
- まとめた項目の 2 つ目以降の機能への依存も、まとめた Issue の番号に引く
- `depends` が `issues.json` に無い機能を指せば 2（理由を言う）
- 依存が循環すれば 2
- 依存先が先に来る順で出す
- 閉じた Issue は `[x]` で出す
- 題は機能の id だけ（出した行が `parent-issue.py show` にそのまま通り、依存がそのとおり読まれる）

**変異テストを含む。** 写した本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。変異ごとに、
**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、穴が無くても緑になるので）。
"""
from __future__ import annotations

import ast
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "parent-checklist.py"
PARENT_ISSUE = REAL_REPO / "plugins" / "dev-loop" / "skills" / "cruise" / "scripts" / "parent-issue.py"

QA = ("No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
      "Q-001,要求確定（決定表）,割引は？,A: なし / B: あり,A,理由,A（業務部が回答）,決定表 4 行目,反映済み,\n")
SPEC = "# 注文\n\n割引と取り消しとラベル。\n"


def feature(fid: str, op: str, title: str, called_by: list[str] | None = None) -> dict:
    out = {"id": fid, "title": title, "source": ["spec/order.md"], "qa": [],
           "operation": {"id": op, "method": "POST", "path": f"/orders/{op}",
                         "input": {"n": {"type": "integer"}}, "output": {"ok": {"type": "boolean"}}},
           "cases": [{"id": f"{fid}-C1", "title": "1 なら真", "input": {"n": 1}, "expected": {"ok": True}}]}
    if called_by:
        out["called_by"] = called_by
    return out


IR = {"spec_ir_version": 1, "title": "注文", "features": [
    feature("F-001", "place_order", "注文を受ける"),
    feature("F-002", "calc_discount", "割引額を計算する", ["F-003"]),
    feature("F-003", "check_stock", "在庫を確かめる", ["F-001"]),
]}


class Case:
    def __init__(self, name: str, kind: str, code: int, out: str | None = None, err: tuple[str, ...] = (),
                 issues=None, index=None, show: tuple[str, ...] = ()):
        # kind: "plain"（--bundle なし）か "bundle"。issues: 本文の組 → Issue の一覧。index: issues.json を書き換える関数
        self.name, self.kind, self.code, self.out, self.err = name, kind, code, out, err
        self.issues, self.index, self.show = issues, index, show


def listing(*rows: tuple[int, str, str, str]) -> list[dict]:
    return [{"number": n, "title": t, "state": s, "body": b} for n, t, s, b in rows]


def plain(b: dict[str, str], closed: bool = False, extra: tuple = (), drop: str = "") -> list[dict]:
    """F-001 → #11・F-002 → #12（改行を CRLF にして末尾の改行を落とす）・F-003 → #13。#30 は F-001 の印を持つが本文が違う。"""
    rows = [(11, "F-001: 注文を受ける", "CLOSED" if closed else "OPEN", b["F-001.md"]),
            (12, "F-002: 割引額を計算する", "OPEN", b["F-002.md"].replace("\n", "\r\n").rstrip("\r\n")),
            (13, "F-003: 在庫を確かめる", "OPEN", b["F-003.md"]),
            (30, "F-001: 注文を受ける（書き換えた）", "OPEN", b["F-001.md"].replace("注文を受ける", "注文を受け付ける")),
            (40, "ふつうの Issue", "OPEN", "関係ない\n"), *extra]
    return listing(*[r for r in rows if r[1].split(":")[0] != drop])


def bundle(b: dict[str, str]) -> list[dict]:
    return listing((21, "F-001: 注文を受ける", "OPEN", b["F-001.md"]),
                   (22, "F-002・F-003: 割引額を計算する／在庫を確かめる", "OPEN", b["bundle-F-002-F-003.md"]))


def redepend(fid: str, depends: list[str]):
    def edit(index: list[dict]) -> list[dict]:
        index = copy.deepcopy(index)
        for item in index:
            if item.get("feature") == fid:
                item["depends"] = depends
        return index
    return edit


PLAIN_OUT = "- [ ] #12 F-002\n- [ ] #13 F-003 (depends: #12)\n- [ ] #11 F-001 (depends: #13)\n"
CASES = [
    Case("依存の連鎖", "plain", 0, PLAIN_OUT, issues=plain,
         show=("#12\t依存: -\tF-002", "#13\t依存: #12\tF-003", "#11\t依存: #13\tF-001")),
    Case("まとめた Issue への依存", "bundle", 0, "- [ ] #22 F-002・F-003\n- [ ] #21 F-001 (depends: #22)\n", issues=bundle,
         show=("#22\t依存: -\tF-002・F-003", "#21\t依存: #22\tF-001")),
    Case("閉じた Issue は済んだ行", "plain", 0, PLAIN_OUT.replace("- [ ] #11", "- [x] #11"), issues=lambda b: plain(b, closed=True),
         show=("#12\t依存: -\tF-002", "#13\t依存: #12\tF-003")),
    Case("登録していない項目", "plain", 1, "", ("F-003（F-003.md）: 本文が同じ Issue が入力に無い", "一覧を出していない"),
         issues=lambda b: plain(b, drop="F-003")),
    Case("同じ本文が 2 件", "plain", 1, "", ("F-001（F-001.md）: 本文が同じ Issue が 2 件ある（#11、#14）",),
         issues=lambda b: plain(b, extra=((14, "F-001: 注文を受ける", "OPEN", b["F-001.md"]),))),
    Case("無い機能への依存", "plain", 2, "", ("F-001.md: depends の F-009 が issues.json に無い",), issues=plain,
         index=redepend("F-001", ["F-009"])),
    Case("依存の循環", "plain", 2, "", ("依存が循環している",), issues=plain, index=redepend("F-002", ["F-001"])),
    Case("索引が配列でない", "plain", 2, "", ("項目の配列でない",), issues=plain, index=lambda index: {}),
    Case("本文のファイルが無い", "plain", 2, "", ("本文が読めない",), issues=plain,
         index=lambda index: [{**index[0], "body": "F-999.md"}] + index[1:]),
]

# (名前, 壊す箇所, 置き換え, 落ちるはずの試料)
MUTATIONS = [
    ("機能の印で探す", 'hits = [i for i in issues if normalize(i["body"]) == entry["text"]]',
     'hits = [i for i in issues if f"spec-loop-feature: {entry[\'ids\'][0]} " in i["body"]]', "依存の連鎖"),
    ("改行をならさない", '    return body.replace("\\r\\n", "\\n").strip()', "    return body", "依存の連鎖"),
    ("2 件でも止めない", "        elif len(hits) > 1:", "        elif False:", "同じ本文が 2 件"),
    ("無い項目でも止めない", "        if not hits:", "        if False:", "登録していない項目"),
    ("まとめた項目の頭の機能だけを引く", 'for fid in entry["ids"]}', 'for fid in entry["ids"][:1]}', "まとめた Issue への依存"),
    ("無い機能への依存を言わない", "        if missing:\n", "        if False:\n", "無い機能への依存"),
    ("循環でも出す", '            looped = "・".join(', '            break\n            looped = "・".join(', "依存の循環"),
    ("入力の順で出す", "    return done\n", "    return list(range(len(entries)))\n", "依存の連鎖"),
    ("閉じた Issue も未チェック", 'mark = "x" if', 'mark = " " if', "閉じた Issue は済んだ行"),
    ("題を写す", "{'・'.join(entry['ids'])}{depends}", "{issue['title']}{depends}", "依存の連鎖"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def generate(work: Path, scripts: Path, *extra: str) -> Path:
    """本物の `scaffold.py` で本文と `issues.json` を作り、置き場所（`build/scaffold/issues`）を返す。"""
    repo = work / "repo"
    base = repo / "docs" / "v1"
    (base / "shared").mkdir(parents=True)
    (base / "spec").mkdir(parents=True)
    (base / "shared" / "qa.csv").write_text(QA, encoding="utf-8")
    (base / "spec" / "order.md").write_text(SPEC, encoding="utf-8")
    (base / "spec" / "spec_ir.json").write_text(json.dumps(IR, ensure_ascii=False, indent=2), encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(scripts / "scaffold.py"), "--repo", str(repo), *extra],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return repo / "build" / "scaffold" / "issues"


def show(work: Path, text: str) -> tuple[int, str]:
    """出した行を親 Issue の本文として、本物の `parent-issue.py show` に通す。"""
    body = work / f"parent-{abs(hash(text))}.md"
    body.write_text("cruise の親\n\n" + text, encoding="utf-8")
    env = {**os.environ, "PATH": f"{work / 'bin'}{os.pathsep}{os.environ['PATH']}"}
    proc = subprocess.run([sys.executable, "-I", str(PARENT_ISSUE), "show", "50", "--body-file", str(body)],
                          capture_output=True, text=True, cwd=work, env=env)
    return proc.returncode, proc.stdout + proc.stderr


def run_case(work: Path, scripts: Path, made: dict[str, Path], case: Case, tag: str) -> str | None:
    where = made[case.kind]
    texts = {p.name: p.read_text(encoding="utf-8") for p in where.iterdir() if p.suffix == ".md"}
    case_dir = work / f"case-{tag}"
    shutil.copytree(where, case_dir)
    if case.index is not None:
        index = json.loads((where / "issues.json").read_text(encoding="utf-8"))
        (case_dir / "issues.json").write_text(json.dumps(case.index(index), ensure_ascii=False), encoding="utf-8")
    data = work / f"gh-{tag}.json"
    data.write_text(json.dumps(case.issues(texts), ensure_ascii=False), encoding="utf-8")
    try:
        proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), "--index", str(case_dir / "issues.json"),
                               "--issues", str(data)], capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return "止まらない"
    if proc.returncode != case.code:
        return f"exit={proc.returncode}（期待 {case.code}）{(proc.stdout + proc.stderr)[-400:]}"
    if case.out is not None and proc.stdout != case.out:
        return f"出力が違う: {proc.stdout!r}"
    for needle in case.err:
        if needle not in proc.stderr:
            return f"エラー出力に {needle!r} が無い: {proc.stderr[-400:]}"
    if case.show:
        code, out = show(work, proc.stdout)
        if code != 0:
            return f"parent-issue.py show が {code}: {out[-400:]}"
        for needle in case.show:
            if needle not in out:
                return f"parent-issue.py show の出力に {needle!r} が無い: {out[-400:]}"
    return None


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="test-parent-checklist-")).resolve()
    assert REAL_REPO not in work.parents
    try:
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        # 子 Issue の本文を取る偽の gh——失敗させる（parent-issue.py は「判定できなかった」と名指しして続ける）
        (work / "bin").mkdir()
        (work / "bin" / "gh").write_text("#!/bin/sh\necho 'gh: 偽の失敗' >&2\nexit 1\n", encoding="utf-8")
        (work / "bin" / "gh").chmod(0o755)
        made = {"plain": generate(work / "plain", scripts), "bundle": generate(work / "bundle", scripts, "--bundle", "F-002,F-003")}
        check("scaffold が本文を作った", sorted(p.name for p in made["plain"].glob("*.md")) == ["F-001.md", "F-002.md", "F-003.md", "proposals.md"]
              and (made["bundle"] / "bundle-F-002-F-003.md").is_file())

        print("正しい本体")
        for index, case in enumerate(CASES):
            problem = run_case(work, scripts, made, case, f"ok{index}")
            check(f"試料: {case.name}", problem is None, problem or "")

        print("変異テスト")
        by_name = {case.name: case for case in CASES}
        pristine = (scripts / TARGET).read_text(encoding="utf-8")
        for index, (name, old, new, target) in enumerate(MUTATIONS):
            count = pristine.count(old)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            (scripts / TARGET).write_text(pristine.replace(old, new), encoding="utf-8")
            try:
                problem = run_case(work, scripts, made, by_name[target], f"mut{index}")
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
