#!/usr/bin/env python3
"""`scaffold.py` の回帰テスト。

    python3 scripts/test-scaffold.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-spec-exit.py` と同じ形。

見るもの:

1. **確定していない仕様からは作らない**（反映済みでない Q&A・未決定の印・中間表現の各規則・指す Q&A や仕様が無い）。
   **作らなかったときは、前の Issue の本文を消し、`scaffold/` は消さない。**
   **入力は版（`docs/v1/`・`docs/v2/`…）を重ね合わせた全体**——v2 で変えた・消した・足した機能が反映され、
   v2 の Q&A・仕様にも関門が掛かり、重ね合わせの誤り・版に分けていない構成からは作らない。
   **`build/merged/` を書かない**（`--check`・`--dry-run` も）。
2. **生成した Red テストが、実装の無い状態で実際に失敗する**——`unittest` で走らせ、
   **ケースの数だけ失敗（エラーではない）**になること。モジュールはあるが関数が無い・誤った値を返す実装でも同じ。
   **陽性対照: 正しい実装を置くと緑になる**（別の理由で落ちているのではないことを見る）。
3. **Issue の本文から辿れる**——印・節の順・ケースごとの Red テストの名前・Q&A の回答・
   **本文の sha256 が、指しているファイルの実物と一致する**こと（中間表現は `merge-versions.py docs build/merged`
   が書いた実物——メモリ上の重ね合わせと同じバイトであること）。
4. **決定論的で、`--check` が鮮度を見る**——2 回の生成でバイト一致。生成直後の `--check` は 0（陽性対照）、
   中間表現を直した後・手で直した後・消した機能の Red テストが残ったときは 1。
5. **本体の定数が `references/` の表と一致する**（メソッド・型・Issue の印と節）。**dev-loop の
   `references/spec-gap.md` も同じ印と節を持ち、dev-loop の `SKILL.md` も同じ印を持つ**（2 つのプラグインの境界の写し）。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、
穴が無くても緑になるので）。
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "scaffold.py"
SPEC_IR_REF = PLUGIN / "references" / "spec-ir.md"
HANDOFF_REF = PLUGIN / "references" / "handoff-issue.md"
TREE_REF = PLUGIN / "references" / "tree.md"
SPEC_GAP_REF = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "references" / "spec-gap.md"
# dev-loop の手順 1 は、この印を見て `spec-gap.md` へ送る——印の写しはここにもある
DEV_LOOP_SKILL = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "SKILL.md"
# 前の形（段 5d より前）の印——登録済みの Issue はこの形のまま残るので、dev-loop は読み続ける
LEGACY_MARKER = "<!-- spec-loop-handoff: v1 -->"

HEADER = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
QA_DONE = "Q-001,要求確定（決定表）,シルバーで 10000 円未満の割引は？,A: 割引なし / B: 3% 割引,A（業務部が回答）,決定表 4 行目,反映済み,\n"
QA_DONE2 = "Q-002,仕様レビュー（Red Team）,金額が負なら？,A: 拒否する / B: 0 とみなす,A（業務部が回答）,spec/order.md,反映済み,\n"
QA_OPEN = "Q-003,開発（#9）,期限切れは？,A: 拒否 / B: 受け付ける,未回答,—,確認中,\n"

IR = {
    "spec_ir_version": 1,
    "title": "注文",
    "features": [
        {
            "id": "F-001", "title": "割引額を計算する", "source": ["spec/order.md"], "qa": ["Q-001"],
            "operation": {
                "id": "calc_discount", "method": "POST", "path": "/orders/discount",
                "input": {"rank": {"type": "string", "enum": ["silver", "gold"]}, "amount": {"type": "integer"}},
                "output": {"discount": {"type": "integer"}},
                "errors": ["INVALID_AMOUNT"],
            },
            "cases": [
                {"id": "F-001-C1", "title": "シルバーで 10000 円未満は割引なし",
                 "input": {"rank": "silver", "amount": 9999}, "expected": {"discount": 0}, "qa": ["Q-001"]},
                {"id": "F-001-C2", "title": "金額が負なら拒否する",
                 "input": {"rank": "gold", "amount": -1}, "error": "INVALID_AMOUNT", "qa": ["Q-002"]},
            ],
        },
        {
            "id": "F-002", "title": "注文を取り消せるか", "source": ["spec/order.md"], "qa": [],
            "operation": {
                "id": "can_cancel", "method": "GET", "path": "/orders/cancelable",
                "input": {"shipped": {"type": "boolean"}},
                "output": {"ok": {"type": "boolean"}},
            },
            "cases": [
                {"id": "F-002-C1", "title": "発送前なら取り消せる", "input": {"shipped": False}, "expected": {"ok": True}},
            ],
        },
    ],
}
SPEC = "# 注文\n\n割引と取り消し。\n"
# 試料の正本は版のディレクトリに置く（`references/versions.md`）
V1 = Path("docs") / "v1"
V2 = Path("docs") / "v2"
IR_FILE = V1 / "spec" / "spec_ir.json"

# 正しい実装（陽性対照）
GOOD_IMPL = '''
def calc_discount(rank, amount):
    if amount < 0:
        return {"error": "INVALID_AMOUNT"}
    return {"discount": 0}


def can_cancel(shipped):
    return {"ok": not shipped}
'''
WRONG_IMPL = '''
def calc_discount(rank, amount):
    return {"discount": 1}


def can_cancel(shipped):
    return {"ok": shipped}
'''
NO_FUNCTION_IMPL = "VALUE = 1\n"
# 値は等しいが型が違う（`0.0 == 0`・`1 == True`）——`assertEqual` だけなら緑になる
WRONG_TYPE_IMPL = '''
def calc_discount(rank, amount):
    if amount < 0:
        return {"error": "INVALID_AMOUNT"}
    return {"discount": 0.0}


def can_cancel(shipped):
    return {"ok": int(not shipped)}
'''
# 逆向き——真偽値を integer の項目に返す（`False == 0`）
WRONG_BOOL_IMPL = '''
def calc_discount(rank, amount):
    if amount < 0:
        return {"error": "INVALID_AMOUNT"}
    return {"discount": False}


def can_cancel(shipped):
    return {"ok": not shipped}
'''


def edit(fn: Callable[[dict], None]) -> Callable[[dict], dict]:
    def apply(ir: dict) -> dict:
        ir = copy.deepcopy(ir)
        fn(ir)
        return ir
    return apply


def f1(ir: dict) -> dict:
    return ir["features"][0]


class Case:
    def __init__(self, name: str, code: int, text: str = "", *, ir=None, raw: str | None = None, qa: str | None = None,
                 spec: dict[str, str] | None = None, args: tuple[str, ...] = (), pre: Callable[[Path], None] | None = None,
                 post: Callable[[Path], str | None] | None = None, generate_first: bool = False, impl: str | None = None,
                 extra: dict[str, str] | None = None, root: Path = V1):
        self.name, self.code, self.text = name, code, text
        self.ir, self.raw, self.qa, self.spec = ir, raw, qa, spec
        self.args, self.pre, self.post = args, pre, post
        self.generate_first, self.impl = generate_first, impl
        # extra: 正本の根からのパス → 中身（v2 の差分など）。root: 試料の版 1 を置く場所（旧い構成なら docs）
        self.extra, self.root = extra or {}, root


def red_run(repo: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-E", "-s", "-m", "unittest", "discover", "-s", "scaffold/tests"],
                          capture_output=True, text=True, cwd=repo)
    return proc.returncode, proc.stdout + proc.stderr


def expect_red(count: int) -> Callable[[Path], str | None]:
    def post(repo: Path) -> str | None:
        code, out = red_run(repo)
        if code == 0:
            return f"Red テストが通った: {out[-300:]}"
        if f"FAILED (failures={count})" not in out:
            return f"失敗が {count} 件の失敗（エラーなし）になっていない: {out[-400:]}"
        if "未実装" not in out and "AssertionError" not in out:
            return f"失敗の理由が出ていない: {out[-300:]}"
        return None
    return post


def expect_green(repo: Path) -> str | None:
    code, out = red_run(repo)
    return None if code == 0 and "OK" in out else f"正しい実装で緑にならない: {out[-400:]}"


def files_written(repo: Path) -> str | None:
    for rel in ("scaffold/openapi.json", "scaffold/types.py", "scaffold/tests/test_f_001.py",
                "scaffold/tests/test_f_002.py", "build/scaffold/issues/F-001.md", "build/scaffold/issues/F-002.md",
                "build/scaffold/issues/issues.json"):
        if not (repo / rel).is_file():
            return f"{rel} が無い"
    if (repo / "build" / "merged").exists():
        return "build/merged/ を書いた（重ね合わせはメモリ上で行う）"
    return None


def merge_with_script(repo: Path) -> Path:
    """`merge-versions.py docs build/merged` を走らせ、重ね合わせた全体の根を返す（Issue の本文が指す場所）。"""
    proc = subprocess.run([sys.executable, "-I", str(repo.parent / "scripts" / "merge-versions.py"),
                           str(repo / "docs"), str(repo / "build" / "merged")], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return repo / "build" / "merged"


def nothing_written(repo: Path) -> str | None:
    if (repo / "scaffold").exists():
        return "scaffold/ を書いた"
    if (repo / "build" / "scaffold" / "issues").exists():
        return "Issue の本文が残っている（前の本文を消していない）"
    return None


def plant_old_issues(repo: Path) -> None:
    old = repo / "build" / "scaffold" / "issues"
    old.mkdir(parents=True)
    (old / "F-009.md").write_text("古い本文\n", encoding="utf-8")


def plant_old_contract(repo: Path) -> None:
    plant_old_issues(repo)
    (repo / "scaffold").mkdir()
    (repo / "scaffold" / "openapi.json").write_text("{}\n", encoding="utf-8")


def contract_kept_issues_gone(repo: Path) -> str | None:
    if not (repo / "scaffold" / "openapi.json").is_file():
        return "commit 済みの scaffold/ を消した"
    return nothing_written_issues(repo)


def nothing_written_issues(repo: Path) -> str | None:
    return "前の Issue の本文が残っている" if (repo / "build" / "scaffold" / "issues").exists() else None


def old_issues_kept(repo: Path) -> str | None:
    if not (repo / "build" / "scaffold" / "issues" / "F-009.md").is_file():
        return "--dry-run / --check が前の Issue の本文を消した"
    if (repo / "scaffold").exists():
        return "--dry-run が書いた"
    if (repo / "build" / "merged").exists():
        return "--dry-run / --check が build/merged/ を書いた"
    return None


def body_traceable(repo: Path) -> str | None:
    body = (repo / "build" / "scaffold" / "issues" / "F-001.md").read_text(encoding="utf-8")
    lines = body.splitlines()
    if lines[:3] != ["<!-- spec-loop-handoff: v2 -->", "<!-- spec-loop-feature: F-001 -->",
                     "<!-- spec-loop-change: add; base=none -->"]:
        return f"先頭 3 行が印でない: {lines[:3]}"
    positions = [body.find(f"\n{s}\n") for s in ("## 仕様", "## 受入基準", "## Red テスト", "## Q&A の回答", "## 仕様の穴を見つけたら")]
    if -1 in positions or positions != sorted(positions):
        return f"節が揃っていないか順が違う: {positions}"
    for needle in ("TestF001.test_f_001_c1", "TestF001.test_f_001_c2", "`F-001-C1`", "`F-001-C2`",
                   "| Q-001 | シルバーで 10000 円未満の割引は？ | A（業務部が回答） | 決定表 4 行目 |",
                   # 機能ではなくケースだけが指す Q&A（受入基準の表の `| Q-002 |` と区別するため、質問まで見る）
                   "| Q-002 | 金額が負なら？ |", "`POST /orders/discount`",
                   "`calc_discount`", "`build/merged/spec/order.md`", "起票元 `開発`", "references/spec-gap.md",
                   "`merge-versions.py docs build/merged --upto 1`", "`docs/v<n>/shared/qa.csv`",
                   "| ケース | 変化 | 確かめること | Red テスト | Q&A |", "| `F-001-C1` | 追加 |", "変化: 追加（v1 の機能）",
                   "実装が無い状態では、ケースの数だけ失敗する。"):
        if needle not in body:
            return f"本文に {needle!r} が無い"
    # 本文の sha256 と、指しているファイルの実物——中間表現は `merge-versions.py` が書く全体（同じバイトであること）
    merge_with_script(repo)
    shas = dict(re.findall(r"`([^`]+)`（sha256: `([0-9a-f]{64})`）", body))
    for rel in ("build/merged/spec/spec_ir.json", "scaffold/tests/test_f_001.py"):
        if rel not in shas:
            return f"本文に {rel} の sha256 が無い"
        actual = hashlib.sha256((repo / rel).read_bytes()).hexdigest()
        if shas[rel] != actual:
            return f"{rel} の sha256 が実物と違う"
    index = json.loads((repo / "build" / "scaffold" / "issues" / "issues.json").read_text(encoding="utf-8"))
    if [i["title"] for i in index] != ["F-001: 割引額を計算する", "F-002: 注文を取り消せるか"]:
        return f"issues.json の題が違う: {index}"
    if [(i["change"], i["red"]) for i in index] != [("add", ["TestF001.test_f_001_c1", "TestF001.test_f_001_c2"]),
                                                    ("add", ["TestF002.test_f_002_c1"])]:
        return f"issues.json の変化と失敗するはずのテストが違う: {index}"
    other = (repo / "build" / "scaffold" / "issues" / "F-002.md").read_text(encoding="utf-8")
    if "この機能が根拠にした Q&A は無い" not in other:
        return "Q&A の無い機能でそう書いていない"
    return None


def openapi_shape(repo: Path) -> str | None:
    doc = json.loads((repo / "scaffold" / "openapi.json").read_text(encoding="utf-8"))
    post = doc["paths"]["/orders/discount"]["post"]
    if post["operationId"] != "calc_discount" or "400" not in post["responses"] or "requestBody" not in post:
        return f"POST の入口が違う: {post}"
    get = doc["paths"]["/orders/cancelable"]["get"]
    if "requestBody" in get or [p["name"] for p in get["parameters"]] != ["shipped"] or "400" in get["responses"]:
        return f"GET の入口が違う: {get}"
    types = (repo / "scaffold" / "types.py").read_text(encoding="utf-8")
    for needle in ("class CalcDiscountInput(TypedDict):", "    amount: int", "    rank: Literal['silver', 'gold']",
                   "class CalcDiscountError(TypedDict):", "    shipped: bool"):
        if needle not in types:
            return f"types.py に {needle!r} が無い"
    if "class CanCancelError" in types:
        return "errors の無い入口に Error の型を作った"
    return None


def deterministic(repo: Path) -> str | None:
    before = {p: p.read_bytes() for p in sorted(repo.rglob("*")) if p.is_file() and "scaffold" in p.parts}
    proc = subprocess.run([sys.executable, "-I", str(repo.parent / "scripts" / TARGET), "--repo", str(repo)],
                          capture_output=True, text=True)
    after = {p: p.read_bytes() for p in sorted(repo.rglob("*")) if p.is_file() and "scaffold" in p.parts}
    return None if proc.returncode == 0 and before == after else "2 回目の生成でバイトが違う"


def edit_ir_file(repo: Path) -> None:
    path = repo / IR_FILE
    ir = json.loads(path.read_text(encoding="utf-8"))
    ir["features"][0]["cases"][0]["expected"]["discount"] = 5
    path.write_text(json.dumps(ir, ensure_ascii=False), encoding="utf-8")


def drop_feature(repo: Path) -> None:
    path = repo / IR_FILE
    ir = json.loads(path.read_text(encoding="utf-8"))
    ir["features"] = ir["features"][:1]
    path.write_text(json.dumps(ir, ensure_ascii=False), encoding="utf-8")


def hand_edit(repo: Path) -> None:
    path = repo / "scaffold" / "tests" / "test_f_001.py"
    path.write_text(path.read_text(encoding="utf-8").replace("'discount': 0", "'discount': 1"), encoding="utf-8")


def drop_feature_and_plant_own_test(repo: Path) -> None:
    drop_feature(repo)
    (repo / "scaffold" / "tests" / "test_mine.py").write_text("# 自分で書いたテスト\n", encoding="utf-8")


def stale_test_removed(repo: Path) -> str | None:
    if (repo / "scaffold" / "tests" / "test_f_002.py").exists():
        return "消した機能の Red テストが残っている"
    if not (repo / "scaffold" / "tests" / "test_mine.py").is_file():
        return "生成の印の無いテストを消した"
    return None


def impl_module_used(repo: Path) -> str | None:
    test = (repo / "scaffold" / "tests" / "test_f_001.py").read_text(encoding="utf-8")
    body = (repo / "build" / "scaffold" / "issues" / "F-001.md").read_text(encoding="utf-8")
    if "IMPL_MODULE = 'app.core'" not in test:
        return "Red テストが中間表現の impl_module を使っていない"
    if "モジュール `app.core`" not in body:
        return "Issue の本文が中間表現の impl_module を指していない"
    return None


def hand_edit_impl_module(repo: Path) -> None:
    # 全部の Red テストを一様に書き換える——検査する相手から読む `--check` なら新しいと言ってしまう
    for path in (repo / "scaffold" / "tests").glob("test_*.py"):
        path.write_text(path.read_text(encoding="utf-8").replace("spec_impl", "hacked_mod"), encoding="utf-8")


def crlf_test(repo: Path) -> None:
    path = repo / "scaffold" / "tests" / "test_f_001.py"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))


def break_write(repo: Path) -> None:
    # 書き込みの途中で OSError——`types.py` をディレクトリにして、題を変えて作り直させる
    types = repo / "scaffold" / "types.py"
    types.unlink()
    (types / "x").mkdir(parents=True)
    path = repo / IR_FILE
    path.write_text(path.read_text(encoding="utf-8").replace('"注文"', '"注文2"'), encoding="utf-8")


def issues_gone(repo: Path) -> str | None:
    if (repo / "build" / "scaffold" / "issues").exists():
        return "前の Issue の本文が残っている"
    return None


def plant_draft_spec(repo: Path) -> None:
    draft = repo / V1 / "spec" / ".draft"
    draft.mkdir()
    (draft / "order.md").write_text(SPEC + "上限は TBD。\n", encoding="utf-8")


ONE = edit(lambda ir: None)

# ---- 版（v2 は v1 からの差分だけ）
V2_CHANGED = copy.deepcopy(IR["features"][0])
V2_CHANGED["cases"][0]["expected"] = {"discount": 300}  # v2 でシルバーの割引を変えた
V2_RETURN = {
    "id": "F-003", "title": "返品できるか", "source": ["spec/return.md"], "qa": ["Q-004"],
    "operation": {"id": "can_return", "method": "GET", "path": "/orders/returnable",
                  "input": {"days": {"type": "integer"}}, "output": {"ok": {"type": "boolean"}}},
    "cases": [{"id": "F-003-C1", "title": "7 日以内なら返品できる", "input": {"days": 3}, "expected": {"ok": True}, "qa": ["Q-004"]}],
}
# v2 で出力に項目を足した（C1 の期待は変わる。失敗のケース C2 は前の版の実装で緑のまま）
V2_OUTPUT_ADDED = copy.deepcopy(V2_CHANGED)
V2_OUTPUT_ADDED["operation"]["output"]["rate"] = {"type": "integer"}
V2_OUTPUT_ADDED["cases"][0]["expected"] = {"discount": 300, "rate": 3}
# v2 で割引の型を number に広げただけ（期待は同じ）——前の版の実装はどのケースも緑のまま
V2_WIDENED = copy.deepcopy(IR["features"][0])
V2_WIDENED["operation"]["output"]["discount"] = {"type": "number"}
QA_V2 = "Q-004,要求確定,返品は何日まで？,A: 7 日 / B: 14 日,A（業務部が回答）,spec/return.md,反映済み,\n"
RETURN_SPEC = "# 返品\n\n7 日以内。\n"


def v2(features: list[dict], qa: str | None = HEADER + QA_V2, removed: str | None = None,
       spec: dict[str, str] | None = None, top: dict | None = None) -> dict[str, str]:
    files = {str(V2 / "spec" / "spec_ir.json"): json.dumps({**(top or {}), "features": features}, ensure_ascii=False,
                                                            indent=2)}
    if qa is not None:
        files[str(V2 / "shared" / "qa.csv")] = qa
    if removed is not None:
        files[str(V2 / "removed.csv")] = "種類,対象,理由\n" + removed
    for rel, body in (spec or {"return.md": RETURN_SPEC}).items():
        files[str(V2 / "spec" / rel)] = body
    return files


ISSUES = Path("build") / "scaffold" / "issues"


def bodies(repo: Path) -> dict[str, str]:
    """{機能の id: 本文}（作った本文だけ）。"""
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted((repo / ISSUES).glob("F-*.md"))}


def body_has(body: str, needles: tuple[str, ...], what: str) -> str | None:
    for needle in needles:
        if needle not in body:
            return f"{what}の本文に {needle!r} が無い"
    return None


def sections_in_order(body: str) -> bool:
    positions = [body.find(f"\n{s}\n") for s in ("## 仕様", "## 受入基準", "## Red テスト", "## Q&A の回答", "## 仕様の穴を見つけたら")]
    return -1 not in positions and positions == sorted(positions)


def v2_changed(repo: Path) -> str | None:
    test = (repo / "scaffold" / "tests" / "test_f_001.py").read_text(encoding="utf-8")
    if "'discount': 300" not in test or "'discount': 0" in test:
        return "v2 で変えた機能のケースが Red テストに入っていない（v1 のまま）"
    if not (repo / "scaffold" / "tests" / "test_f_002.py").is_file():
        return "v2 で触っていない機能の Red テストが無い（契約は全体から作る）"
    found = bodies(repo)
    if list(found) != ["F-001"]:
        return f"本文を作るのは変えた機能だけのはず: {list(found)}"
    body = found["F-001"]
    if body.splitlines()[:3] != ["<!-- spec-loop-handoff: v2 -->", "<!-- spec-loop-feature: F-001 -->",
                                 "<!-- spec-loop-change: modify; base=v1 -->"]:
        return f"変更の印でない: {body.splitlines()[:3]}"
    if not sections_in_order(body):
        return "変更の本文の節が揃っていない"
    index = json.loads((repo / ISSUES / "issues.json").read_text(encoding="utf-8"))
    if index != [{"feature": "F-001", "title": "F-001: 割引額を計算する（v2 で変更）", "change": "modify",
                  "body": "F-001.md", "red": ["TestF001.test_f_001_c1"]}]:
        return f"issues.json が違う: {index}"
    return body_has(body, ("| `F-001-C1` | 変更 |", "| `F-001-C2` | 回帰 |", "変化: 変更（v1 の時点から v2 で変えた機能）",
                           "`merge-versions.py docs build/merged --upto 2`", "**`回帰` のケースは前の版の実装で緑で、緑のままであること**",
                           "`追加`・`変更` のケース（1 件）だけが失敗し、`回帰` のケース（1 件）は緑"), "変更")


def v2_removed(repo: Path) -> str | None:
    if (repo / "scaffold" / "tests" / "test_f_002.py").exists():
        return "v2 で消した機能の Red テストを作った"
    if not (repo / "scaffold" / "tests" / "test_f_001.py").is_file():
        return "残る機能の Red テストが無い"
    found = bodies(repo)
    if list(found) != ["F-002"]:
        return f"本文を作るのは消した機能だけのはず: {list(found)}"
    body = found["F-002"]
    if body.splitlines()[2] != "<!-- spec-loop-change: remove; base=v1 -->":
        return f"撤去の印でない: {body.splitlines()[:3]}"
    if not sections_in_order(body):
        return "撤去の本文の節が揃っていない"
    if "sha256: `" in body.split("## Red テスト", 1)[1]:
        return "撤去の本文が消した Red テストの sha256 を持つ"
    return body_has(body, ("理由: 取り消しはやめる", "撤去する API: `GET /orders/cancelable`", "| `F-002-C1` | 削除 |",
                           "—（`scaffold/tests/test_f_002.py` ごと消した）", "モジュール `spec_impl` の関数 `can_cancel`",
                           "python3 -m unittest discover -s scaffold/tests\n", "この機能が根拠にした Q&A は無い"), "撤去")


def v2_added(repo: Path) -> str | None:
    found = bodies(repo)
    if list(found) != ["F-003"]:
        return f"本文を作るのは足した機能だけのはず: {list(found)}"
    body = found["F-003"]
    if body.splitlines()[2] != "<!-- spec-loop-change: add; base=v1 -->":
        return f"追加の印でない: {body.splitlines()[:3]}"
    return body_has(body, ("`build/merged/spec/return.md`", "| Q-004 | 返品は何日まで？ |", "| `F-003-C1` | 追加 |",
                           "変化: 追加（v2 で足した機能）"), "追加")


# v2 でケースを足し・消し・題だけ変える（C1 は題だけ・C2 は消す・C3 を足す）
V2_CASES = copy.deepcopy(IR["features"][0])
V2_CASES["cases"] = [dict(V2_CASES["cases"][0], title="シルバーの少額は割引しない"),
                     {"id": "F-001-C3", "title": "ゴールドは 10% 割引", "input": {"rank": "gold", "amount": 1000},
                      "expected": {"discount": 100}}]


def v2_cases(repo: Path) -> str | None:
    body = bodies(repo).get("F-001", "")
    problem = body_has(body, ("| `F-001-C1` | 回帰 | シルバーの少額は割引しない |", "| `F-001-C3` | 追加 |",
                              "削除したケース（Red テストから外した。その振る舞いはもう求めない）: `F-001-C2` 金額が負なら拒否する"),
                       "ケースを変えた機能")
    if problem:
        return problem
    index = json.loads((repo / ISSUES / "issues.json").read_text(encoding="utf-8"))
    return None if index[0]["red"] == ["TestF001.test_f_001_c3"] else f"失敗するはずのテストが違う: {index}"


def v2_nothing_changed(repo: Path) -> str | None:
    found = bodies(repo)
    index = json.loads((repo / ISSUES / "issues.json").read_text(encoding="utf-8"))
    return None if not found and index == [] else f"機能が変わっていないのに本文を作った: {list(found)} {index}"


def add_v3(repo: Path) -> None:
    """v2 で作った後に v3 を足す（中間表現の題を変える）——本文の再現コマンドは v2 の全体を作り直せること（#262 の R2）。"""
    path = repo / "docs" / "v3" / "spec" / "spec_ir.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"title": "注文 v3", "features": []}, ensure_ascii=False), encoding="utf-8")


def sha_reproducible_after_v3(repo: Path) -> str | None:
    body = bodies(repo)["F-001"]
    sha = re.search(r"`build/merged/spec/spec_ir.json`（sha256: `([0-9a-f]{64})`）", body).group(1)
    scripts = repo.parent / "scripts" / "merge-versions.py"

    def merged_sha(*extra: str) -> str:
        out = repo / "build" / "merged"
        proc = subprocess.run([sys.executable, "-I", str(scripts), str(repo / "docs"), str(out), *extra],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        return hashlib.sha256((out / "spec" / "spec_ir.json").read_bytes()).hexdigest()

    # 陽性対照: 版を指定しないと v3 まで重なり、本文の sha256 と合わない
    if merged_sha() == sha:
        return "v3 を足しても全体が変わらない（試料が判別しない）"
    command = re.search(r"`(merge-versions\.py [^`]+)`", body).group(1).split()[1:]
    return None if merged_sha(*command[2:]) == sha else f"本文のコマンド {command} で作った中間表現の sha256 が本文と違う"


def add_v2_changed(repo: Path) -> None:
    for rel, text in v2([V2_CHANGED]).items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


# v1 の機能 F-002 の期待の型が誤り（v2 で直した）——前の版の中間表現が決まりに反する
BAD_V1 = edit(lambda ir: ir["features"][1]["cases"][0].update(expected={"ok": "yes"}))

CASES: list[Case] = [
    Case("作る", 0, "作った", post=files_written),
    Case("Red テストが失敗する", 0, post=expect_red(3)),
    Case("関数の無い実装でも失敗する", 0, impl=NO_FUNCTION_IMPL, post=expect_red(3)),
    Case("誤った実装で失敗する", 0, impl=WRONG_IMPL, post=expect_red(3)),
    Case("正しい実装で緑", 0, impl=GOOD_IMPL, post=expect_green),
    Case("型の違う実装で失敗する", 0, impl=WRONG_TYPE_IMPL, post=expect_red(2)),
    Case("本文から辿れる", 0, post=body_traceable),
    Case("OpenAPI と型", 0, post=openapi_shape),
    Case("決定論的", 0, post=deterministic),
    Case("生成直後の --check", 0, "新しい", args=("--check",), generate_first=True),
    Case("中間表現を直した後の --check", 1, "今の入力から作るものと違う", args=("--check",), generate_first=True, pre=edit_ir_file),
    Case("中間表現の実装のモジュールを使う", 0, ir=edit(lambda ir: ir.update(impl_module="app.core")), post=impl_module_used),
    Case("実装のモジュールを手で書き換えた --check", 1, "今の入力から作るものと違う", args=("--check",), generate_first=True,
         pre=hand_edit_impl_module),
    Case("改行を CRLF に変えた --check", 1, "test_f_001.py: 今の入力から作るものと違う", args=("--check",),
         generate_first=True, pre=crlf_test),
    Case("書き込みの途中で失敗する", 2, "予期しない失敗", generate_first=True, pre=break_write, post=issues_gone),
    Case("真偽値を整数の項目に返す実装で失敗する", 0, impl=WRONG_BOOL_IMPL, post=expect_red(1)),
    Case("手で直した後の --check", 1, "test_f_001.py: 今の入力から作るものと違う", args=("--check",), generate_first=True, pre=hand_edit),
    Case("消した機能の Red テストが残る --check", 1, "中間表現に無い機能の Red テスト", args=("--check",), generate_first=True,
         pre=drop_feature),
    Case("消した機能の Red テストを消す", 0, generate_first=True, pre=drop_feature_and_plant_own_test, post=stale_test_removed),
    Case("--dry-run は書かない", 0, "何も書いていない", args=("--dry-run",), pre=plant_old_issues, post=old_issues_kept),
    Case("--dry-run は失敗しても消さない", 1, args=("--dry-run",), qa=HEADER + QA_DONE + QA_DONE2 + QA_OPEN,
         pre=plant_old_issues, post=old_issues_kept),
    # 関門
    Case("確認中の Q&A", 1, "Q-003: 状態が 確認中", qa=HEADER + QA_DONE + QA_DONE2 + QA_OPEN, pre=plant_old_contract,
         post=contract_kept_issues_gone),
    Case("仕様に未決定の印", 1, "未決定の印 TBD", spec={"order.md": SPEC + "上限は TBD。\n"}, pre=plant_old_issues,
         post=nothing_written),
    Case("Q&A 表が無い", 2, "Q&A 表を読めない", qa="", pre=plant_old_issues, post=nothing_written),
    Case("中間表現が無い", 2, "どの版にも中間表現が無い", raw="", pre=plant_old_issues, post=nothing_written),
    # 版を重ねるときに読むので、重ね合わせの誤り（1）になる
    Case("中間表現が JSON でない", 1, "JSON として読めない", raw="{,", pre=plant_old_issues, post=nothing_written),
    # 中間表現の規則
    Case("版が違う", 1, "spec_ir_version が 1 でない", ir=edit(lambda ir: ir.update(spec_ir_version=2)), post=nothing_written),
    Case("版が true", 1, "spec_ir_version が 1 でない", ir=edit(lambda ir: ir.update(spec_ir_version=True))),
    Case("版が 1.0", 1, "spec_ir_version が 1 でない", ir=edit(lambda ir: ir.update(spec_ir_version=1.0))),
    Case("実装のモジュールの形", 1, "impl_module がモジュール名の形に反する", ir=edit(lambda ir: ir.update(impl_module="Bad-Name"))),
    Case("機能が無い", 1, "features が 1 つ以上の配列でない", ir=edit(lambda ir: ir.update(features=[]))),
    Case("決まりに無いキー", 1, "決まりに無いキー `priority`", ir=edit(lambda ir: f1(ir).update(priority="高"))),
    Case("ケースの決まりに無いキー", 1, "決まりに無いキー `note`", ir=edit(lambda ir: f1(ir)["cases"][0].update(note="x"))),
    Case("機能の id の形", 1, "id の形に反する", ir=edit(lambda ir: f1(ir).update(id="F-1"))),
    # ケースの id も揃えて全角にする——揃えないと、ケースの id の形で落ちて、機能の id の検査を判別しない
    Case("全角の数字の id", 1, "id の形に反する（F- に 3 桁以上の数字）",
         ir=edit(lambda ir: (f1(ir).update(id="F-００１"),
                             [c.update(id=c["id"].replace("F-001", "F-００１")) for c in f1(ir)["cases"]]))),
    # 版を重ねる段（`merge-versions.py`）が先に断る
    Case("機能の id の重複", 1, "機能の `id` が版の中で重複: F-001",ir=edit(lambda ir: ir["features"][1].update(id="F-001"))),
    Case("改行を含む題", 1, "title が空か、1 行でない", ir=edit(lambda ir: f1(ir).update(title="割引\n計算"))),
    Case("Q&A が表に無い", 1, "Q-099 は Q&A 表に無い", ir=edit(lambda ir: f1(ir).update(qa=["Q-099"]))),
    Case("ケースの Q&A が表に無い", 1, "Q-098 は Q&A 表に無い", ir=edit(lambda ir: f1(ir)["cases"][0].update(qa=["Q-098"]))),
    Case("Q&A の重複", 1, "Q&A の No が重複している", ir=edit(lambda ir: f1(ir).update(qa=["Q-001", "Q-001"]))),
    Case("仕様のファイルが無い", 1, "spec/missing.md が無い", ir=edit(lambda ir: f1(ir).update(source=["spec/missing.md"]))),
    Case("仕様の外のファイル", 1, "の中に無い", ir=edit(lambda ir: f1(ir).update(source=["shared/qa.csv"]))),
    # 版のディレクトリのパスは指さない（重ね合わせた全体の根からのパス）
    Case("版のディレクトリのパスを出所にする", 1, "の中に無い", ir=edit(lambda ir: f1(ir).update(source=["docs/v1/spec/order.md"]))),
    Case("ドットの場所の仕様", 1, "`.` で始まる場所", pre=plant_draft_spec,
         ir=edit(lambda ir: f1(ir).update(source=["spec/.draft/order.md"]))),
    Case("中間表現を出所にする", 1, "中間表現そのもの", ir=edit(lambda ir: f1(ir).update(source=["spec/spec_ir.json"]))),
    Case("出所が空", 1, "仕様のファイルの配列（1 つ以上）でない", ir=edit(lambda ir: f1(ir).update(source=[]))),
    Case("メソッドが決まりに無い", 1, "operation.method: 決まりに無い", ir=edit(lambda ir: f1(ir)["operation"].update(method="FETCH"))),
    Case("パスが / で始まらない", 1, "operation.path", ir=edit(lambda ir: f1(ir)["operation"].update(path="orders"))),
    Case("入口の重複", 1, "が重複している", ir=edit(lambda ir: ir["features"][1]["operation"].update(method="POST", path="/orders/discount"))),
    Case("入口の id の重複", 1, "operation.id: calc_discount が重複している",
         ir=edit(lambda ir: ir["features"][1]["operation"].update(id="calc_discount"))),
    Case("型の名前が潰れる", 1, "同じ型の名前 CalcDiscountInput",
         ir=edit(lambda ir: ir["features"][1]["operation"].update(id="calc__discount")), post=nothing_written),
    Case("予約語の入口", 1, "Python の予約語でない", ir=edit(lambda ir: f1(ir)["operation"].update(id="class"))),
    Case("予約語の項目", 1, "項目名の形に反する", ir=edit(lambda ir: f1(ir)["operation"]["input"].update({"from": {"type": "string"}}))),
    Case("型が決まりに無い", 1, "型 `date` は決まりに無い", ir=edit(lambda ir: f1(ir)["operation"]["output"]["discount"].update(type="date"))),
    Case("出力が無い", 1, "項目が 1 つも無い", ir=edit(lambda ir: f1(ir)["operation"].update(output={}))),
    Case("出力に error", 1, "正常時の出力に `error` は使えない",
         ir=edit(lambda ir: f1(ir)["operation"]["output"].update({"error": {"type": "string"}}))),
    Case("enum の型", 1, "enum の値が型 string でない", ir=edit(lambda ir: f1(ir)["operation"]["input"]["rank"].update(enum=["silver", 1]))),
    Case("enum の重複", 1, "enum の値が重複している", ir=edit(lambda ir: f1(ir)["operation"]["input"]["rank"].update(enum=["gold", "gold"]))),
    Case("enum の 1 と 1.0", 1, "enum の値が重複している",
         ir=edit(lambda ir: f1(ir)["operation"]["input"]["amount"].update(type="number", enum=[1, 1.0]))),
    # 以下は、検査の途中で Python の例外になっていた形——traceback（exit 1）で古い Issue の本文を残さない
    Case("メソッドが配列", 1, "operation.method: 決まりに無い", pre=plant_old_issues, post=issues_gone,
         ir=edit(lambda ir: f1(ir)["operation"].update(method=["POST"]))),
    Case("深い入れ子", 2, "中間表現を読めない", raw="[" * 200000 + "]" * 200000, pre=plant_old_issues, post=issues_gone),
    Case("仕様のパスに NUL", 2, "予期しない失敗", pre=plant_old_issues, post=issues_gone,
         ir=edit(lambda ir: f1(ir).update(source=["spec/a\u0000b.md"]))),
    Case("桁の多いケースの id", 0, "作った",
         ir=edit(lambda ir: ir["features"][1]["cases"][0].update(id="F-002-C" + "1" * 5000))),
    Case("エラー名の形", 1, "operation.errors: 名前の形に反する", ir=edit(lambda ir: f1(ir)["operation"].update(errors=["bad"]))),
    Case("ケースの id の形", 1, "<機能の id>-C<数字>", ir=edit(lambda ir: f1(ir)["cases"][0].update(id="F-002-C1"))),
    Case("ケースの id の重複", 1, "id F-001-C1 が重複している", ir=edit(lambda ir: f1(ir)["cases"][1].update(id="F-001-C1"))),
    Case("ケースが無い", 1, "cases: 1 つ以上の配列でない", ir=edit(lambda ir: f1(ir).update(cases=[]))),
    Case("入力の項目が足りない", 1, "input: 項目 `amount` が無い", ir=edit(lambda ir: f1(ir)["cases"][0]["input"].pop("amount"))),
    Case("入力に余計な項目", 1, "input: 決まりに無い項目 `coupon`", ir=edit(lambda ir: f1(ir)["cases"][0]["input"].update(coupon="X"))),
    Case("整数に真偽値", 1, "input.amount: 型 integer でない", ir=edit(lambda ir: f1(ir)["cases"][0]["input"].update(amount=True))),
    Case("整数に小数", 1, "input.amount: 型 integer でない", ir=edit(lambda ir: f1(ir)["cases"][0]["input"].update(amount=1.5))),
    Case("enum に無い値", 1, "input.rank: enum に無い値", ir=edit(lambda ir: f1(ir)["cases"][0]["input"].update(rank="bronze"))),
    Case("期待の型", 1, "expected.discount: 型 integer でない", ir=edit(lambda ir: f1(ir)["cases"][0]["expected"].update(discount="0"))),
    Case("期待の項目が足りない", 1, "expected: 項目 `discount` が無い", ir=edit(lambda ir: f1(ir)["cases"][0].update(expected={}))),
    Case("期待とエラーの両方", 1, "ちょうど片方だけ", ir=edit(lambda ir: f1(ir)["cases"][0].update(error="INVALID_AMOUNT"))),
    Case("期待もエラーも無い", 1, "ちょうど片方だけ", ir=edit(lambda ir: f1(ir)["cases"][1].pop("error"))),
    Case("エラーが入口に無い", 1, "error: operation.errors に無い", ir=edit(lambda ir: f1(ir)["cases"][1].update(error="OTHER"))),
    Case("NaN", 1, "型 integer でない", raw=json.dumps(IR).replace('"amount": 9999', '"amount": NaN')),
    Case("number に Infinity", 1, "型 number でない",
         ir=edit(lambda ir: f1(ir)["operation"]["input"]["amount"].update(type="number")),
         pre=lambda repo: (repo / IR_FILE).write_text(
             (repo / IR_FILE).read_text(encoding="utf-8").replace('"amount": 9999', '"amount": Infinity'),
             encoding="utf-8")),
    # 孤立したサロゲートは JSON として読めるが UTF-8 で書けない——書く途中で落ちて契約を切り詰めない
    # （版を重ねる段で `merge-versions.py` が先に断る）
    Case("孤立したサロゲート", 1, "サロゲート",
         raw=json.dumps(IR, ensure_ascii=False).replace("割引額を計算する", "\\ud800"),
         pre=plant_old_contract, post=contract_kept_issues_gone),
    # 桁の大きい整数は float に直せない——`math.isfinite` に渡すと OverflowError で落ちる
    Case("number に桁の大きい整数", 0, "作った",
         ir=edit(lambda ir: f1(ir)["operation"]["input"]["amount"].update(type="number")),
         pre=lambda repo: (repo / IR_FILE).write_text(
             (repo / IR_FILE).read_text(encoding="utf-8").replace('"amount": 9999', '"amount": 1' + "0" * 400),
             encoding="utf-8")),
    Case("全部を出す", 1, "（2 件）",
         ir=edit(lambda ir: (f1(ir)["operation"].update(method="FETCH"), ir["features"][1].update(title="")))),
    # ---- 版（重ね合わせた全体から作る）
    Case("v2 で機能を変える", 0, "作った", extra=v2([V2_CHANGED]), post=v2_changed),
    Case("v2 で機能を消す", 0, "作った", extra=v2([], removed="機能,F-002,取り消しはやめる\n"), post=v2_removed),
    Case("v2 で機能を足す", 0, "作った", extra=v2([V2_RETURN]), post=v2_added),
    Case("v2 の Q&A が確認中", 1, "build/merged/shared/qa.csv: Q-003: 状態が 確認中",
         extra=v2([V2_RETURN], qa=HEADER + QA_V2 + QA_OPEN), pre=plant_old_issues, post=nothing_written),
    Case("v2 の仕様に未決定の印", 1, "未決定の印 TBD", extra=v2([V2_RETURN], spec={"return.md": RETURN_SPEC + "上限は TBD。\n"}),
         pre=plant_old_issues, post=nothing_written),
    Case("重ね合わせが決まりに反する", 1, "前の版までに無いものを消そうとしている",
         extra=v2([], removed="機能,F-009,無いもの\n"), pre=plant_old_issues, post=nothing_written),
    Case("版に分けていない", 2, "版（v1 など）が 1 つも無い", root=Path("docs"), pre=plant_old_issues, post=nothing_written),
    # 版の名前が決まりに反する（`v02` だけ）のは移していないのではなく、重ね合わせの誤り——2 でなく 1
    Case("版の名前だけが決まりに反する", 1, "v02: 版の名前の形", root=Path("docs/v02"), pre=plant_old_issues,
         post=nothing_written),
    Case("docs が無い", 2, "ディレクトリが無い", root=Path("legacy"), pre=plant_old_issues, post=nothing_written),
    Case("v2 の --check は書かない", 0, "新しい", args=("--check",), generate_first=True, extra=v2([V2_CHANGED]),
         post=lambda repo: "--check が build/merged/ を書いた" if (repo / "build" / "merged").exists() else None),
    # ---- 追加・変更・削除に分ける（段 5d）
    Case("v2 でケースを足し・消し・題を変える", 0, "modify 1", extra=v2([V2_CASES]), post=v2_cases),
    Case("v2 で機能を変えない", 0, "Issue の本文 0 件", extra=v2([]), post=v2_nothing_changed),
    Case("v3 を足しても本文の sha256 が合う", 0, generate_first=True, extra=v2([V2_CHANGED]), pre=add_v3,
         args=("--check", "--upto", "2"), post=sha_reproducible_after_v3),
    Case("前の版の中間表現が決まりに反する", 1, "前の版（v1）の中間表現が決まりに反する", ir=BAD_V1,
         extra=v2([IR["features"][1]]), pre=plant_old_issues, post=nothing_written_issues),
    # ---- --upto（前の版の時点の鮮度）
    Case("前の版の時点の --check", 0, "新しい（v1 まで", args=("--check", "--upto", "1"), generate_first=True,
         pre=add_v2_changed),
    Case("前の版の時点の --check（陽性対照）", 1, "今の入力から作るものと違う", args=("--check",), generate_first=True,
         pre=add_v2_changed),
    Case("v2 で作り直した後の --upto 1", 1, "今の入力から作るものと違う", args=("--check", "--upto", "1"),
         generate_first=True, extra=v2([V2_CHANGED])),
    Case("--upto で書く", 2, "--upto は --check か --dry-run と一緒にだけ使う", args=("--upto", "1"),
         pre=plant_old_issues, post=old_issues_kept),
    Case("--red-check に --upto", 2, "--upto は --check か --dry-run と一緒にだけ使う", args=("--red-check", "--upto", "1")),
    Case("無い版の --upto", 2, "v3 が無い", args=("--check", "--upto", "3"), extra=v2([V2_CHANGED])),
    Case("--upto 0", 2, "1 以上の整数", args=("--dry-run", "--upto", "0")),
    # ---- --red-check（変わったケースだけ失敗し、ほかは緑）
    Case("Red の状態: v1 で実装なし", 0, "失敗 3 件", args=("--red-check",), generate_first=True),
    Case("Red の状態: v1 で実装がある", 1, "なのに緑", args=("--red-check",), generate_first=True, impl=GOOD_IMPL),
    Case("Red の状態: v2 で前の版の実装", 0, "失敗 1 件（追加・変更）・緑 2 件（回帰）", args=("--red-check",),
         generate_first=True, extra=v2([V2_CHANGED]), impl=GOOD_IMPL),
    Case("Red の状態: v2 で実装が無い", 2, "回帰のケース 2 件を判定していない", args=("--red-check",), generate_first=True,
         extra=v2([V2_CHANGED])),
    Case("Red の状態: 回帰が壊れた実装", 1, "test_f_002.TestF002.test_f_002_c1: 回帰のケースなのに失敗した",
         args=("--red-check",), generate_first=True, extra=v2([V2_CHANGED]), impl=WRONG_IMPL),
    Case("Red の状態: v2 で出力の項目を足す", 0, "失敗 1 件（追加・変更）・緑 2 件（回帰）", args=("--red-check",),
         generate_first=True, extra=v2([V2_OUTPUT_ADDED]), impl=GOOD_IMPL),
    Case("Red の状態: v2 で型を広げる", 0, "失敗 0 件（追加・変更）・緑 3 件（回帰）", args=("--red-check",),
         generate_first=True, extra=v2([V2_WIDENED]), impl=GOOD_IMPL),
    Case("v2 で impl_module だけ変える", 0, "modify 2", extra=v2([], top={"impl_module": "app_impl"})),
    Case("Red の状態: v2 で impl_module だけ変える", 0, "失敗 3 件", args=("--red-check",), generate_first=True,
         extra=v2([], top={"impl_module": "app_impl"}), impl=GOOD_IMPL),
    Case("Red の状態: scaffold が古い", 1, "作り直してから", args=("--red-check",), generate_first=True, pre=edit_ir_file),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("関門を見ない", "            if code:\n                return code, shown(lines) + [",
     "            if False:\n                return code, shown(lines) + [", "確認中の Q&A"),
    ("失敗時に Issue の本文を消さない", "    if writing:\n        clear_issues(repo)", "    if False:\n        clear_issues(repo)",
     "確認中の Q&A"),
    ("--dry-run でも Issue の本文を消す", "    writing = not (args.check or args.dry_run or args.red_check)", "    writing = True",
     "--dry-run は失敗しても消さない"),
    # 版が無いのは決まりに反するのではなく移していない——2 で止め、1（重ね合わせの誤り）と言わない
    ("版が無いのを重ね合わせの誤りと言う", "        if not versions.find_versions(docs, probe) and not probe:",
     "        if False:", "版に分けていない"),
    ("版の名前の誤りを、版が無いと言う", "        if not versions.find_versions(docs, probe) and not probe:",
     "        if not versions.find_versions(docs, probe):", "版の名前だけが決まりに反する"),
    ("決まりに無いキーを見ない", "    for key in sorted(obj.keys() - required - optional):", "    for key in []:", "決まりに無いキー"),
    ("Q&A の実在を見ない", "        elif no not in answered:", "        elif False:", "Q&A が表に無い"),
    ("ケースの Q&A を見ない", '            if "qa" in case:\n                problems += check_qa_refs',
     '            if False:\n                problems += check_qa_refs', "ケースの Q&A が表に無い"),
    ("仕様のファイルの実在を見ない", "        elif not path.is_file():", "        elif False:", "仕様のファイルが無い"),
    ("仕様の外を許す", "        if spec_root not in path.parents:", "        if False:", "仕様の外のファイル"),
    ("真偽値を整数に数える", "        return isinstance(value, int) and not isinstance(value, bool)",
     "        return isinstance(value, int)", "整数に真偽値"),
    ("有限を見ない", " and math.isfinite(value)", "", "number に Infinity"),
    ("enum を見ない", '        elif isinstance(field.get("enum"), list) and value not in field["enum"]:',
     "        elif False:", "enum に無い値"),
    ("入力の過不足を見ない", "    for name in sorted(fields.keys() - values.keys()):", "    for name in []:", "入力の項目が足りない"),
    ("片方だけを見ない", '            if ("expected" in case) == ("error" in case):', "            if False:", "期待とエラーの両方"),
    ("予約語を許す", "        if not NAME.fullmatch(name) or keyword.iskeyword(name):", "        if not NAME.fullmatch(name):",
     "予約語の項目"),
    ("出力の error を許す", "        if output and name == RESERVED_OUTPUT:", "        if False:", "出力に error"),
    ("改行を許す", 'and not any(unicodedata.category(c) == "Cc" for c in value))', ")", "改行を含む題"),
    ("全角の数字を許す", 'FEATURE_ID = re.compile(r"F-[0-9]{3,}")', 'FEATURE_ID = re.compile(r"F-\\d{3,}")', "全角の数字の id"),
    ("未実装をエラーにする", '"            return None",', '"            raise",', "Red テストが失敗する"),
    ("未実装で fail しない", '"            self.fail(f\\"未実装: {IMPL_MODULE}.{OPERATION} が無い\\")",', '"            pass",',
     "関数の無い実装でも失敗する"),
    ("期待を比べない", '"        self.assertEqual(actual, expected)",', '"        self.assertIsNotNone(actual)",', "誤った実装で失敗する"),
    ("型を見ない", '"            self.assertTrue(type_fits(OUTPUT_TYPES[name], value),",', '"            self.assertTrue(True,",',
     "型の違う実装で失敗する"),
    ("中間表現の実装のモジュールを読まない",
     '    impl_module = ir.get("impl_module", DEFAULT_IMPL_MODULE)\n    contract = {',
     '    impl_module = DEFAULT_IMPL_MODULE\n    contract = {',
     "中間表現の実装のモジュールを使う"),
    ("実装のモジュールの形を見ない", '    if "impl_module" in ir and not module_name(ir["impl_module"]):',
     "    if False:", "実装のモジュールの形"),
    ("--check が文字列で比べる", '        if current != text.encode("utf-8"):', '        if current.decode("utf-8").splitlines() != text.splitlines():',
     "改行を CRLF に変えた --check"),
    ("予期しない失敗で Issue の本文を消さない", "        if writing:\n            try:\n                clear_issues(repo)",
     "        if False:\n            try:\n                clear_issues(repo)", "仕様のパスに NUL"),
    ("予期しない失敗を捕まえない", "    except Exception as exc:  # 予期しない失敗", "    except ZeroDivisionError as exc:  # 予期しない失敗",
     "書き込みの途中で失敗する"),
    ("メソッドが決まりに無くても入口の重複を見る", "                elif method in METHODS and (method, path) in routes:",
     "                elif (method, path) in routes:", "メソッドが配列"),
    ("深い入れ子を読めないと言わない", "    except RecursionError:\n        # 版の", "    except ZeroDivisionError:\n        # 版の",
     "深い入れ子"),
    ("ケースの id を int() で並べる", '    digits = case["id"].rsplit("C", 1)[1].lstrip("0")\n    return len(digits), digits',
     '    return 0, str(int(case["id"].rsplit("C", 1)[1]))', "桁の多いケースの id"),
    ("版を値だけで比べる", '    if type(ir.get("spec_ir_version")) is not int or', '    if isinstance(ir.get("spec_ir_version"), bool) or',
     "版が 1.0"),
    ("enum の重複を文字列で数える", "            elif any(a == b for i, a in enumerate(enum) for b in enum[i + 1:]):",
     "            elif len({json.dumps(v) for v in enum}) != len(enum):", "enum の 1 と 1.0"),
    ("真偽値をどの型にも合うとする", '"        return kind == \\"boolean\\"",', '"        return True",',
     "真偽値を整数の項目に返す実装で失敗する"),
    ("型の名前の衝突を見ない", "                elif pascal(oid) in type_names:", "                elif False:", "型の名前が潰れる"),
    ("ドットの場所を許す", '        elif any(part.startswith(".") for part in path.relative_to(spec_root).parts):', "        elif False:",
     "ドットの場所の仕様"),
    # `surrogates(ir)` の検査には変異を置かない——版を重ねる段（`merge-versions.py` の `render`）が先に断るので、
    # 入力から届かない（殺せると主張しない）
    ("整数を isfinite に渡す", "        return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))",
     "        return math.isfinite(value) and isinstance(value, (int, float))", "number に桁の大きい整数"),
    ("エラーのケースで error を期待しない",
     '        expected = case["expected"] if "expected" in case else {"error": case["error"]}\n        refs',
     '        expected = case.get("expected", {})\n        refs', "正しい実装で緑"),
    ("ケースを 1 つしか作らない", '    for case in sorted(feature["cases"], key=case_order):\n        expected',
     '    for case in sorted(feature["cases"], key=case_order)[:1]:\n        expected',
     "Red テストが失敗する"),
    ("中間表現の sha256 を取らない", "sha256(loaded.raw)", "sha256(b\"\")", "本文から辿れる"),
    ("Q&A の回答を写さない", "        lines.append(f\"| {no} | {cell(row['質問'])} | {cell(row['回答'])} | {cell(row['反映先'])} |\")",
     "        lines.append(f\"| {no} |\")", "本文から辿れる"),
    ("ケースの Q&A を本文に集めない", '    refs = set(feature["qa"]) | {no for _, case in rows for no in case.get("qa", [])}',
     '    refs = set(feature["qa"])', "本文から辿れる"),
    ("GET にも本文を付ける", '        if op["method"] in NO_BODY:', "        if False:", "OpenAPI と型"),
    ("--check が残った Red テストを見ない", "    for rel in sorted(generated_tests(out) - contract.keys()):\n        problems",
     "    for rel in []:\n        problems", "消した機能の Red テストが残る --check"),
    ("書くときに残った Red テストを消さない", "    for rel in sorted(generated_tests(out) - contract.keys()):\n        (out / rel).unlink()",
     "    for rel in []:\n        (out / rel).unlink()", "消した機能の Red テストを消す"),
    ("印の無いテストも消す", "            if GENERATED in head:", "            if True:", "消した機能の Red テストを消す"),
    ("--check が中身を比べない", '        if current != text.encode("utf-8"):', "        if False:", "手で直した後の --check"),
    ("機能の並びを保たない", '    return sorted(ir["features"], key=lambda f: f["id"])', '    return list(ir["features"])[::-1]',
     "本文から辿れる"),
    # ---- 版
    ("v1 だけを読む", "versions.merge(docs, upto)", "versions.merge(docs, 1)", "v2 で機能を変える"),
    # ---- 追加・変更・削除（段 5d）
    ("前の版と比べない", "    if number == 1:\n        return 0, [], [Change(ADD", "    if True:\n        return 0, [], [Change(ADD",
     "v2 で機能を変える"),
    ("削除を変更と書く", "diffs.REMOVED: REMOVE}", "diffs.REMOVED: MODIFY}", "v2 で機能を消す"),
    ("ケースの期待の違いを見ない", "literal(case[\"input\"]), literal(expected)\n", "literal(case[\"input\"])\n",
     "v2 で機能を変える"),
    ("題だけの違いを変化に数える", "literal(case[\"input\"]), literal(expected)\n",
     "literal(case[\"input\"]), literal(expected), case[\"title\"]\n", "v2 でケースを足し・消し・題を変える"),
    ("消したケースを書かない", "    if gone:\n", "    if False:\n", "v2 でケースを足し・消し・題を変える"),
    ("再現コマンドに版を書かない", 'command = f"merge-versions.py {DOCS} {MERGED_DIR} --upto {number}"',
     'command = f"merge-versions.py {DOCS} {MERGED_DIR}"', "v3 を足しても本文の sha256 が合う"),
    # 検査だけ飛ばし、中間表現は返す形にする——`if code:` を潰すと None を読んで落ち、意味ではなく例外で殺される
    ("前の版の中間表現を検査しない", "        problems = check_ir(ir, whole, answered)\n",
     "        problems = check_ir(ir, whole, answered) if gate else []\n", "前の版の中間表現が決まりに反する"),
    ("期待に無い項目の型も見る", "not in WIDENED for name in expected)", "not in WIDENED for name in now)",
     "Red の状態: v2 で出力の項目を足す"),
    ("型を広げたのを変化に数える", 'WIDENED = {("integer", "number")}', "WIDENED = set()", "Red の状態: v2 で型を広げる"),
    ("impl_module の変化を見ない", "    if before.impl_module != loaded.ir.get(", "    if False and before.impl_module != loaded.ir.get(",
     "v2 で impl_module だけ変える"),
    ("--upto で書くのを断らない", "        if not (args.check or args.dry_run):\n", "        if False:\n", "--upto で書く"),
    ("--upto を渡さない", "load(repo, args.upto)", "load(repo)", "前の版の時点の --check"),
    ("回帰の失敗を見ない", '        elif name not in red and got != "pass":', "        elif False:", "Red の状態: 回帰が壊れた実装"),
    ("変化を捕まえない Red テストを見ない", '        elif name in red and got == "pass":', "        elif False:",
     "Red の状態: v1 で実装がある"),
    ("実装が無くても回帰を判定したと言う", "    if expected and green and all(", "    if False and all(",
     "Red の状態: v2 で実装が無い"),
    ("--red-check が鮮度を見ない", "    if args.red_check:\n        problems = stale(repo / OUT_DIR, contract)\n        if problems:",
     "    if args.red_check:\n        problems = stale(repo / OUT_DIR, contract)\n        if False:", "Red の状態: scaffold が古い"),
    ("重ね合わせの誤りを見ない", '    if problems:\n        return 1, problems + ["版の重ね合わせ',
     '    if False:\n        return 1, problems + ["版の重ね合わせ', "重ね合わせが決まりに反する"),
    ("一時ディレクトリの名前で言う", "return [line.replace(str(whole), MERGED_DIR) for line in lines]", "return lines",
     "v2 の Q&A が確認中"),
    ("本文に重ね合わせた全体の場所を書かない", 'return f"{MERGED_DIR}/{path}"', "return path", "本文から辿れる"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def build(root: Path, case: Case) -> Path:
    assert_in_tmp(root)
    base = root / case.root
    (base / "shared").mkdir(parents=True)
    (base / "spec").mkdir(parents=True)
    qa = HEADER + QA_DONE + QA_DONE2 if case.qa is None else case.qa
    if qa:
        (base / "shared" / "qa.csv").write_text(qa, encoding="utf-8")
    for rel, body in (case.spec or {"order.md": SPEC}).items():
        (base / "spec" / rel).write_text(body, encoding="utf-8")
    if case.raw is not None:
        if case.raw:
            (base / "spec" / "spec_ir.json").write_text(case.raw, encoding="utf-8")
    else:
        ir = (case.ir or ONE)(IR)
        (base / "spec" / "spec_ir.json").write_text(json.dumps(ir, ensure_ascii=False, indent=2), encoding="utf-8")
    for rel, body in case.extra.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    if case.impl is not None:
        (root / "spec_impl.py").write_text(case.impl, encoding="utf-8")
    return root


def run_case(scripts: Path, work: Path, case: Case) -> tuple[bool, str]:
    repo = build(work / "repo", case)
    # `deterministic` は `repo.parent / "scripts"` を使う
    shutil.copytree(scripts, work / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    command = [sys.executable, "-I", str(work / "scripts" / TARGET), "--repo", str(repo)]
    if case.generate_first:
        first = subprocess.run(command, capture_output=True, text=True)
        if first.returncode != 0:
            return False, f"前段の生成が失敗した: {first.stdout}{first.stderr}"
    if case.pre:
        case.pre(repo)
    proc = subprocess.run(command + list(case.args), capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    if proc.returncode != case.code:
        return False, f"exit={proc.returncode}（期待 {case.code}）{out[-400:]}"
    if case.text and case.text not in out:
        return False, f"出力に {case.text!r} が無い: {out[-400:]}"
    if case.post:
        problem = case.post(repo)
        if problem:
            return False, problem
    return True, ""


def table_cells(markdown: str, heading: str) -> list[str]:
    section = markdown.split(heading, 1)[1].split("\n#", 1)[0]
    return re.findall(r"^\| `([^`]+)` \|", section, flags=re.MULTILINE)


def constant(source: str, name: str):
    found = re.search(rf"^{name} = (.+)$", source, flags=re.MULTILINE)
    return ast.literal_eval(found.group(1)) if found else None


def copy_scripts(dest: Path, source: str | None = None) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    if source is not None:
        (dest / TARGET).write_text(source, encoding="utf-8")
    return dest


def main() -> int:
    names = [case.name for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    with tempfile.TemporaryDirectory(prefix="scaffold-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        for index, case in enumerate(CASES):
            ok, detail = run_case(scripts, tmp_path / f"case{index}", case)
            check(f"試料が期待どおりでない: {case.name}", ok, detail)

        # references との突き合わせ
        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        ir_ref = SPEC_IR_REF.read_text(encoding="utf-8")
        handoff = HANDOFF_REF.read_text(encoding="utf-8")
        tree = TREE_REF.read_text(encoding="utf-8")
        gap = SPEC_GAP_REF.read_text(encoding="utf-8")
        methods, types = table_cells(ir_ref, "### メソッド"), table_cells(ir_ref, "### 項目")
        check("METHODS が references/spec-ir.md の表と違う", list(constant(source, "METHODS") or ()) == methods,
              f"{constant(source, 'METHODS')} vs {methods}")
        check("TYPES が references/spec-ir.md の表と違う", list(constant(source, "TYPES") or ()) == types,
              f"{constant(source, 'TYPES')} vs {types}")
        check("references からメソッド・型を読めない（読み方が壊れている）", len(methods) >= 3 and len(types) >= 3,
              f"{methods} {types}")
        markers = table_cells(handoff, "## 印")
        marker = constant(source, "HANDOFF_MARKER")
        feature_marker = constant(source, "FEATURE_MARKER")
        check("HANDOFF_MARKER が references/handoff-issue.md の印と違う", markers[:1] == [marker], f"{marker} vs {markers}")
        check("FEATURE_MARKER が references/handoff-issue.md の印と違う",
              feature_marker is not None and markers[1:2] == [feature_marker.format("<機能の id>")], f"{feature_marker} vs {markers}")
        change_marker = constant(source, "CHANGE_MARKER")
        check("CHANGE_MARKER が references/handoff-issue.md の印と違う",
              change_marker is not None and markers[2:3] == [change_marker.format("<変化>", "<前の版>")],
              f"{change_marker} vs {markers}")
        kinds = table_cells(handoff, "### 変化")
        check("ADD, MODIFY, REMOVE が references/handoff-issue.md の変化の表と違う",
              kinds == list(constant(source, "ADD, MODIFY, REMOVE") or ()), f"{kinds}")
        sections = table_cells(handoff, "## 節")
        check("SECTIONS が references/handoff-issue.md の節の表と違う", list(constant(source, "SECTIONS") or ()) == sections,
              f"{constant(source, 'SECTIONS')} vs {sections}")
        for rel in (constant(source, "IR_PATH"), constant(source, "QA_PATH"), constant(source, "ISSUES_DIR"),
                    f"{constant(source, 'OUT_DIR')}/openapi.json"):
            check(f"置き場所 {rel} が references/tree.md に無い", rel is not None and rel.rsplit("/", 1)[-1] in tree)
        # 2 つのプラグインの境界の写し
        skill = DEV_LOOP_SKILL.read_text(encoding="utf-8")
        # dev-loop は今の形（v2）も、登録済みの前の形（v1）も読む
        for current in (marker, LEGACY_MARKER):
            check(f"dev-loop の references/spec-gap.md に印 {current} が無い", current is not None and current in gap)
            check(f"dev-loop の SKILL.md に印 {current} が無い（手順 1 が spec-loop の Issue に気づかない）",
                  current is not None and current in skill)
        check("dev-loop の references/spec-gap.md に変化の印が無い",
              change_marker is not None and change_marker.split("{}")[0] in gap)
        # 陽性対照: 印を上げたら、`SKILL.md` に残った古い印では当たらない
        check("印の版を変えても SKILL.md の照合が不一致にならない",
              marker is not None and marker.replace("v2", "v3") not in skill)
        gap_sections = table_cells(gap, "## spec-loop から来た Issue を読む")
        check("dev-loop の references/spec-gap.md の節の表が handoff-issue.md と違う", gap_sections == sections,
              f"{gap_sections} vs {sections}")
        # 突き合わせ自体の陽性対照
        broken = handoff.replace("| `## Red テスト` |", "| `## 赤のテスト` |")
        check("handoff-issue.md の写しを崩しても不一致にならない", table_cells(broken, "## 節") != sections)

        # 変異テスト
        by_name = {case.name: case for case in CASES}
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}", source.replace(before, after))
            ok, detail = run_case(mutated, tmp_path / f"mutwork{index}", by_name[killer])
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not ok, detail)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
