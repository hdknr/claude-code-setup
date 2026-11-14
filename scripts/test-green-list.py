#!/usr/bin/env python3
"""`green-list.py`（spec-loop の、scaffold の Red テストのうち緑のケースを一覧に書き、CI で緑のままかを見るスクリプト。#1000）の回帰テスト。

    python3 scripts/test-green-list.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-parent-checklist.py` と同じ形。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。**`scaffold/` は本物の `scaffold.py` で作る**——
手で書いた Red テストに当てると、生成の形が変わっても緑のままになる。v2 の試料（1 つのケースの期待を変え、別のケースの題だけ直す）も
本物の `scaffold.py` で作り直す。**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせ、
子のプロセスの環境から `PYTHONPATH` を外す**——`-I` が効くのは起こしたプロセスだけで、`green-list.py` が Red テストを走らせる孫のプロセス
（`scaffold.py` の `run_tests`）は環境を引き継ぐ。外さないと、試料の外の `spec_impl.py` が読み込まれて陽性対照が崩れうる。

試料: 機能 F-001（`double`。2 ケース）と F-002（`negate`。2 ケース）。実装は試料の根の `spec_impl.py`（`impl_module` の既定）。

**陽性対照**（受入基準の 3。#1000）: 「壊した」の試料——実装済みの F-001 の実装を誤ったものに替えると `check` が 1 を返し、
壊したケースを名指しする（壊す前の「全部を実装」の試料は 0）。
**別リポジトリの形**（受入基準の 4）: 正本のディレクトリと、`scaffold/` だけを写した開発のディレクトリを作り、`references/tree.md` の雛形の
ジョブが当てる 2 本（`scaffold.py --repo <正本> --check` と `diff -r -x __pycache__`）が、写しを変えると・正本の仕様だけ変えると非 0 を返すことを見る
（このスクリプトの外の確かめで、変異は当てない）。

**変異テストを含む。** 写した本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。変異ごとに、
**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、穴が無くても緑になるので）。
**本体の docstring の「守ること」の行の数だけ、変異が要る**（変異の数 ≥ 行の数）。
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
TARGET = "green-list.py"

QA = ("No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
      "Q-001,要求確定（決定表）,割引は？,A: なし / B: あり,A,理由,A（業務部が回答）,決定表 4 行目,反映済み,\n")
SPEC = "# 計算\n\n倍と符号。\n"
IMPL_DOUBLE = 'def double(n):\n    return {"v": n * 2}\n'
IMPL_NEGATE = '\n\ndef negate(n):\n    return {"v": -n}\n'
IMPL_ALL = IMPL_DOUBLE + IMPL_NEGATE
CHILD_ENV = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
HAND_TEST = "import unittest\n\n\nclass TestHand(unittest.TestCase):\n    def test_hand(self):\n        self.assertTrue(True)\n"

C1, C2 = "test_f_001.TestF001.test_f_001_c1", "test_f_001.TestF001.test_f_001_c2"
D1, D2 = "test_f_002.TestF002.test_f_002_c1", "test_f_002.TestF002.test_f_002_c2"


def feature(fid: str, op: str, title: str, cases: list[tuple[str, int, int]]) -> dict:
    return {"id": fid, "title": title, "source": ["spec/calc.md"], "qa": [],
            "operation": {"id": op, "method": "POST", "path": f"/calc/{op}",
                          "input": {"n": {"type": "integer"}}, "output": {"v": {"type": "integer"}}},
            "cases": [{"id": f"{fid}-C{i}", "title": t, "input": {"n": n}, "expected": {"v": v}}
                      for i, (t, n, v) in enumerate(cases, 1)]}


IR_V1 = {"spec_ir_version": 1, "title": "計算", "features": [
    feature("F-001", "double", "倍にする", [("1 なら 2", 1, 2), ("2 なら 4", 2, 4)]),
    feature("F-002", "negate", "符号を変える", [("1 なら -1", 1, -1), ("3 なら -3", 3, -3)])]}
# v2: F-001-C2 の期待を変え（4 → 5）、F-001-C1 は題だけ直す——C1 の指紋は変わらず、C2 だけ変わる
IR_V2 = {"spec_ir_version": 1, "title": "計算", "features": [
    feature("F-001", "double", "倍にする", [("1 なら 2（題を直した）", 1, 2), ("2 なら 5", 2, 5)])]}
# v2（型を広げる）: F-001 の出力 v を integer から number に広げる。期待は変えない——共通の部分だけが変わり、C1・C2 の指紋が変わる
IR_V2_WIDEN = {"spec_ir_version": 1, "title": "計算", "features": [
    feature("F-001", "double", "倍にする", [("1 なら 2", 1, 2), ("2 なら 4", 2, 4)])]}
IR_V2_WIDEN["features"][0]["operation"]["output"] = {"v": {"type": "number"}}


class Case:
    def __init__(self, name: str, steps: list, code: int, err: tuple[str, ...] = (), out: tuple[str, ...] = (),
                 absent: tuple[str, ...] = (), listed: tuple[str, ...] | None = None):
        # steps: 試料を作る手順（("impl", 中身)・("record"[, 終了コード, 旗…])・("v2"[, 中間表現])・("hand",)・("list", 中身)・("noimpl",)・
        # ("rm", scaffold/ からのパス)）。最後に check を走らせる
        # listed: check の後の一覧に載っているテストの名前（全部。None なら見ない）
        self.name, self.steps, self.code, self.err, self.out = name, steps, code, err, out
        self.absent, self.listed = absent, listed


CASES = [
    Case("何も実装していない", [("noimpl",)], 0, out=("一覧のケースは全部緑（0 件）",)),
    Case("一部だけ実装", [("impl", IMPL_DOUBLE), ("record",)], 0, out=("一覧のケースは全部緑（2 件）",), listed=(C1, C2)),
    Case("全部を実装", [("impl", IMPL_ALL), ("record",)], 0, listed=(C1, C2, D1, D2)),
    Case("壊した", [("impl", IMPL_ALL), ("record",), ("impl", IMPL_ALL.replace("n * 2", "n * 3"))], 1,
         err=(f"壊した: {C1}（失敗した）", f"壊した: {C2}（失敗した）", "性質を壊した"), absent=(D1, D2),
         listed=(C1, C2, D1, D2)),
    Case("record は壊したケースを落とさない", [("impl", IMPL_ALL), ("record",), ("impl", IMPL_NEGATE), ("record", 1)], 1,
         err=(f"壊した: {C1}（未実装で失敗した）",), listed=(C1, C2, D1, D2)),
    Case("緑なのに一覧に無い", [("impl", IMPL_DOUBLE), ("record",), ("impl", IMPL_ALL)], 3,
         err=(f"緑なのに一覧に無い: {D1}", "一覧が古い"), listed=(C1, C2)),
    Case("一覧が無いのに緑がある", [("impl", IMPL_ALL)], 3, err=("一覧が無い", f"緑なのに一覧に無い: {C1}")),
    Case("仕様が変えたケース", [("impl", IMPL_ALL), ("record",), ("v2",)], 3,
         err=(f"指紋が変わった: {C2}（いま失敗した）",), absent=(C1, "壊した: "), listed=(C1, C2, D1, D2)),
    Case("仕様が変えたケースを書き直す", [("impl", IMPL_ALL), ("record",), ("v2",), ("record", 1), ("record", 0, "--accept-changed")], 0,
         listed=(C1, D1, D2)),
    Case("型を変えた作り直し", [("impl", IMPL_ALL), ("record",), ("v2", IR_V2_WIDEN)], 3,
         err=(f"指紋が変わった: {C1}（いま緑）", f"指紋が変わった: {C2}（いま緑）"), absent=("壊した: ", "分けていない")),
    Case("型を広げた作り直しと同時に壊した", [("impl", IMPL_ALL), ("record",), ("v2", IR_V2_WIDEN),
                                     ("impl", IMPL_ALL.replace("n * 2", "n * 3")), ("record", 1)], 3,
         err=(f"指紋が変わった: {C1}（いま失敗した）", "分けていない"), listed=(C1, C2, D1, D2)),
    Case("機能を消した", [("impl", IMPL_ALL), ("record",), ("rm", "tests/test_f_002.py")], 3,
         err=(f"もう無い: {D1}", f"もう無い: {D2}"), absent=("壊した: ",), listed=(C1, C2, D1, D2)),
    Case("生成の印の無いテストは見ない", [("impl", IMPL_ALL), ("record",), ("hand",)], 0, listed=(C1, C2, D1, D2)),
    Case("読み込めない", [("impl", IMPL_ALL), ("record",), ("noimpl",)], 1, err=("PYTHONPATH",)),
    Case("一覧の形が違う", [("impl", IMPL_ALL), ("record",), ("list", "test_x 123\n")], 2, err=("一覧の行の形が違う",)),
]

# (名前, 壊す箇所, 置き換え, 落ちるはずの試料)
MUTATIONS = [
    ("載ったケースが落ちても 1 にしない", '        elif outcomes.get(name) != "pass":\n            broken.append(name)',
     '        elif False:\n            broken.append(name)', "壊した"),
    ("載っていないケースの失敗も壊したと読む", "    if broken:\n        say_broken(broken, outcomes, kept_count(listed or {}, prints))\n        print(f\"実装済み",
     "    if broken or any(o != \"pass\" for o in outcomes.values()):\n        say_broken(broken, outcomes, kept_count(listed or {}, prints))\n        print(f\"実装済み",
     "一部だけ実装"),
    ("指紋が変わったケースを壊したと読む", "        elif prints[name] != digest:\n            moved.append(name)",
     "        elif False:\n            moved.append(name)", "仕様が変えたケース"),
    ("緑なのに一覧に無いケースを数えない", '    stale = [f"緑なのに一覧に無い: {name}" for name in unlisted]',
     "    stale = []", "緑なのに一覧に無い"),
    ("record が緑でないケースも書く", '    green = sorted(name for name in prints if outcomes.get(name) == "pass")',
     "    green = sorted(prints)", "一部だけ実装"),
    ("record が壊したケースを落とす", "    if broken:\n        say_broken(broken, outcomes, kept_count(listed, prints))\n        print(f\"一覧に載った",
     "    if False:\n        say_broken(broken, outcomes, kept_count(listed, prints))\n        print(f\"一覧に載った", "record は壊したケースを落とさない"),
    ("指紋にコメントを入れる", ' and not line.strip().startswith("#"))', ")", "仕様が変えたケース"),
    ("指紋にそのケースの中身を入れない", 'f"{common}\\n\\0\\n{body}"', 'f"{common}"', "仕様が変えたケース"),
    ("指紋に別のケースの中身を入れる", "if number not in taken)", "if True)", "仕様が変えたケース"),
    ("生成の印を見ない", "        if scaffold.GENERATED not in text.split(\"\\n\", 1)[0]:\n            continue",
     "        if False:\n            continue", "生成の印の無いテストは見ない"),
    ("形の違う行を飛ばす", "        if not match:\n            raise Unjudged(", "        if not match:\n            continue\n            raise Unjudged(",
     "一覧の形が違う"),
    ("指紋が変わって緑でないケースを黙って落とす", "    if changed_red and not accept_changed:", "    if False:",
     "型を広げた作り直しと同時に壊した"),
    ("指紋に共通の部分を入れない", 'f"{common}\\n\\0\\n{body}"', 'f"{body}"', "型を変えた作り直し"),
    ("もう無いケースを壊したと読む", "            gone.append(name)", "            broken.append(name)", "機能を消した"),
    ("もう無いケースを数えない", '    stale += [f"もう無い: {name}" for name in gone]', "    stale += []", "機能を消した"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def scaffold_run(scripts: Path, repo: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(scripts / "scaffold.py"), "--repo", str(repo), *extra],
                          capture_output=True, text=True, timeout=120, env=CHILD_ENV)


def make_base(work: Path, scripts: Path) -> Path:
    """v1 の正本を置き、本物の `scaffold.py` で `scaffold/` を作る。"""
    repo = work / "base"
    base = repo / "docs" / "v1"
    (base / "shared").mkdir(parents=True)
    (base / "spec").mkdir(parents=True)
    (base / "shared" / "qa.csv").write_text(QA, encoding="utf-8")
    (base / "spec" / "calc.md").write_text(SPEC, encoding="utf-8")
    (base / "spec" / "spec_ir.json").write_text(json.dumps(IR_V1, ensure_ascii=False, indent=2), encoding="utf-8")
    proc = scaffold_run(scripts, repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return repo


def green(scripts: Path, repo: Path, command: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(scripts / TARGET), command, "--repo", str(repo), *extra],
                          capture_output=True, text=True, timeout=300, env=CHILD_ENV)


def listed_names(repo: Path) -> list[str] | None:
    path = repo / "scaffold-green.txt"
    if not path.exists():
        return None
    return sorted(line.split()[0] for line in path.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#"))


def run_case(work: Path, scripts: Path, base: Path, case: Case, tag: str) -> str | None:
    repo = work / f"case-{tag}"
    shutil.copytree(base, repo)
    try:
        for step in case.steps:
            kind = step[0]
            if kind == "impl":
                (repo / "spec_impl.py").write_text(step[1], encoding="utf-8")
            elif kind == "noimpl":
                (repo / "spec_impl.py").unlink(missing_ok=True)
            elif kind == "record":
                proc = green(scripts, repo, "record", *step[2:])
                want = step[1] if len(step) > 1 else 0
                if proc.returncode != want:
                    return f"record: exit={proc.returncode}（期待 {want}）{(proc.stdout + proc.stderr)[-400:]}"
            elif kind == "rm":
                (repo / "scaffold" / step[1]).unlink()
            elif kind == "v2":
                (repo / "docs" / "v2" / "spec").mkdir(parents=True)
                ir = step[1] if len(step) > 1 else IR_V2
                (repo / "docs" / "v2" / "spec" / "spec_ir.json").write_text(json.dumps(ir, ensure_ascii=False, indent=2),
                                                                           encoding="utf-8")
                proc = scaffold_run(scripts, repo)
                if proc.returncode != 0:
                    return f"v2 の scaffold.py: exit={proc.returncode} {(proc.stdout + proc.stderr)[-400:]}"
            elif kind == "hand":
                (repo / "scaffold" / "tests" / "test_hand.py").write_text(HAND_TEST, encoding="utf-8")
            elif kind == "list":
                (repo / "scaffold-green.txt").write_text(step[1], encoding="utf-8")
        proc = green(scripts, repo, "check")
    except subprocess.TimeoutExpired:
        return "止まらない"
    if proc.returncode != case.code:
        return f"exit={proc.returncode}（期待 {case.code}）{(proc.stdout + proc.stderr)[-600:]}"
    for needle in case.err:
        if needle not in proc.stderr:
            return f"エラー出力に {needle!r} が無い: {proc.stderr[-600:]}"
    for needle in case.out:
        if needle not in proc.stdout:
            return f"出力に {needle!r} が無い: {proc.stdout[-400:]}"
    for needle in case.absent:
        if needle in proc.stdout + proc.stderr:
            return f"出力に {needle!r} がある: {(proc.stdout + proc.stderr)[-600:]}"
    if case.listed is not None and listed_names(repo) != sorted(case.listed):
        return f"一覧が違う: {listed_names(repo)}（期待 {sorted(case.listed)}）"
    if list(repo.rglob("__pycache__")):
        return f"__pycache__ を書いた: {[str(p) for p in repo.rglob('__pycache__')]}"
    return None


def separate_repo(work: Path, scripts: Path, base: Path) -> None:
    """別リポジトリの形（受入基準の 4）: 雛形のジョブが当てる 2 本が、写しの崩れと正本の古さを非 0 で示す。"""
    canon, dev = work / "canon", work / "dev"
    shutil.copytree(base, canon)
    dev.mkdir()
    shutil.copytree(canon / "scaffold", dev / "scaffold")
    (dev / "spec_impl.py").write_text(IMPL_ALL, encoding="utf-8")

    def same() -> int:
        return subprocess.run(["diff", "-r", "-x", "__pycache__", str(canon / "scaffold"), str(dev / "scaffold")],
                              capture_output=True, text=True).returncode

    check("別リポジトリ: 正本の scaffold/ は新しい（陽性対照）", scaffold_run(scripts, canon, "--check").returncode == 0)
    check("別リポジトリ: 写しは正本と同じ（陽性対照）", same() == 0)
    rec = green(scripts, dev, "record")
    check("別リポジトリ: 開発の側で record できる", rec.returncode == 0, rec.stdout + rec.stderr)
    check("別リポジトリ: 開発の側で check が 0", green(scripts, dev, "check").returncode == 0)
    check("別リポジトリ: record と check は scaffold/ に __pycache__ を書かない（写しの比べが崩れない）", same() == 0)
    copied = dev / "scaffold" / "tests" / "test_f_001.py"
    pristine = copied.read_text(encoding="utf-8")
    copied.write_text(pristine.replace("{'v': 4}", "{'v': 6}"), encoding="utf-8")
    check("別リポジトリ: 写しを手で直すと diff が非 0", pristine.count("{'v': 4}") == 1 and same() == 1)
    copied.write_text(pristine, encoding="utf-8")
    ir = canon / "docs" / "v1" / "spec" / "spec_ir.json"
    ir.write_text(ir.read_text(encoding="utf-8").replace('"v": 4', '"v": 6'), encoding="utf-8")
    check("別リポジトリ: 正本の仕様だけ変えて作り直していないと --check が 1",
          scaffold_run(scripts, canon, "--check").returncode == 1)
    proc = scaffold_run(scripts, canon)
    check("別リポジトリ: 正本を作り直して写していないと diff が非 0", proc.returncode == 0 and same() == 1)


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="test-green-list-")).resolve()
    assert REAL_REPO not in work.parents
    try:
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        base = make_base(work, scripts)
        check("scaffold が Red テストを作った", sorted(p.name for p in (base / "scaffold" / "tests").glob("test_*.py"))
              == ["test_f_001.py", "test_f_002.py"])

        print("正しい本体")
        for index, case in enumerate(CASES):
            problem = run_case(work, scripts, base, case, f"ok{index}")
            check(f"試料: {case.name}", problem is None, problem or "")
        separate_repo(work, scripts, base)

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
                problem = run_case(work, scripts, base, by_name[target], f"mut{index}")
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
    print(f"OK: 試料 {len(CASES)} 件・別リポジトリの形・変異 {len(MUTATIONS)} 件")
    return 0


def docstring_rules(path: Path) -> int:
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    block = doc.split("**守ること**", 1)[1].split("\n\n", 1)[1].split("\n\n", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("- "))


if __name__ == "__main__":
    sys.exit(main())
