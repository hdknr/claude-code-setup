#!/usr/bin/env python3
"""`scaffold.py` の回帰テスト。

    python3 scripts/test-scaffold.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-spec-exit.py` と同じ形。

見るもの:

1. **確定していない仕様からは作らない**（反映済みでない Q&A・未決定の印・中間表現の各規則・指す Q&A や仕様が無い）。
   **作らなかったときは、前の Issue の本文を消し、`scaffold/` は消さない。**
2. **生成した Red テストが、実装の無い状態で実際に失敗する**——`unittest` で走らせ、
   **ケースの数だけ失敗（エラーではない）**になること。モジュールはあるが関数が無い・誤った値を返す実装でも同じ。
   **陽性対照: 正しい実装を置くと緑になる**（別の理由で落ちているのではないことを見る）。
3. **Issue の本文から辿れる**——印・節の順・ケースごとの Red テストの名前・Q&A の回答・
   **本文の sha256 が、指しているファイルの実物と一致する**こと。
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

HEADER = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
QA_DONE = "Q-001,要求確定（決定表）,シルバーで 10000 円未満の割引は？,A: 割引なし / B: 3% 割引,A（業務部が回答）,決定表 4 行目,反映済み,\n"
QA_DONE2 = "Q-002,仕様レビュー（Red Team）,金額が負なら？,A: 拒否する / B: 0 とみなす,A（業務部が回答）,spec/order.md,反映済み,\n"
QA_OPEN = "Q-003,開発（#9）,期限切れは？,A: 拒否 / B: 受け付ける,未回答,—,確認中,\n"

IR = {
    "spec_ir_version": 1,
    "title": "注文",
    "features": [
        {
            "id": "F-001", "title": "割引額を計算する", "source": ["docs/spec/order.md"], "qa": ["Q-001"],
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
            "id": "F-002", "title": "注文を取り消せるか", "source": ["docs/spec/order.md"], "qa": [],
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
                 post: Callable[[Path], str | None] | None = None, generate_first: bool = False, impl: str | None = None):
        self.name, self.code, self.text = name, code, text
        self.ir, self.raw, self.qa, self.spec = ir, raw, qa, spec
        self.args, self.pre, self.post = args, pre, post
        self.generate_first, self.impl = generate_first, impl


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
    return None


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
    return None


def body_traceable(repo: Path) -> str | None:
    body = (repo / "build" / "scaffold" / "issues" / "F-001.md").read_text(encoding="utf-8")
    lines = body.splitlines()
    if lines[:2] != ["<!-- spec-loop-handoff: v1 -->", "<!-- spec-loop-feature: F-001 -->"]:
        return f"先頭 2 行が印でない: {lines[:2]}"
    positions = [body.find(f"\n{s}\n") for s in ("## 仕様", "## 受入基準", "## Red テスト", "## Q&A の回答", "## 仕様の穴を見つけたら")]
    if -1 in positions or positions != sorted(positions):
        return f"節が揃っていないか順が違う: {positions}"
    for needle in ("TestF001.test_f_001_c1", "TestF001.test_f_001_c2", "`F-001-C1`", "`F-001-C2`",
                   "| Q-001 | シルバーで 10000 円未満の割引は？ | A（業務部が回答） | 決定表 4 行目 |",
                   # 機能ではなくケースだけが指す Q&A（受入基準の表の `| Q-002 |` と区別するため、質問まで見る）
                   "| Q-002 | 金額が負なら？ |", "`POST /orders/discount`",
                   "`calc_discount`", "docs/spec/order.md", "起票元 `開発`", "references/spec-gap.md"):
        if needle not in body:
            return f"本文に {needle!r} が無い"
    # 本文の sha256 と、指しているファイルの実物
    shas = dict(re.findall(r"`([^`]+)`（sha256: `([0-9a-f]{64})`）", body))
    for rel in ("docs/spec/spec_ir.json", "scaffold/tests/test_f_001.py"):
        if rel not in shas:
            return f"本文に {rel} の sha256 が無い"
        actual = hashlib.sha256((repo / rel).read_bytes()).hexdigest()
        if shas[rel] != actual:
            return f"{rel} の sha256 が実物と違う"
    index = json.loads((repo / "build" / "scaffold" / "issues" / "issues.json").read_text(encoding="utf-8"))
    if [i["title"] for i in index] != ["F-001: 割引額を計算する", "F-002: 注文を取り消せるか"]:
        return f"issues.json の題が違う: {index}"
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
    path = repo / "docs" / "spec" / "spec_ir.json"
    ir = json.loads(path.read_text(encoding="utf-8"))
    ir["features"][0]["cases"][0]["expected"]["discount"] = 5
    path.write_text(json.dumps(ir, ensure_ascii=False), encoding="utf-8")


def drop_feature(repo: Path) -> None:
    path = repo / "docs" / "spec" / "spec_ir.json"
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
    path = repo / "docs" / "spec" / "spec_ir.json"
    path.write_text(path.read_text(encoding="utf-8").replace('"注文"', '"注文2"'), encoding="utf-8")


def issues_gone(repo: Path) -> str | None:
    if (repo / "build" / "scaffold" / "issues").exists():
        return "前の Issue の本文が残っている"
    return None


def plant_draft_spec(repo: Path) -> None:
    draft = repo / "docs" / "spec" / ".draft"
    draft.mkdir()
    (draft / "order.md").write_text(SPEC + "上限は TBD。\n", encoding="utf-8")


ONE = edit(lambda ir: None)

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
    Case("中間表現が無い", 2, "中間表現を読めない", raw="", pre=plant_old_issues, post=nothing_written),
    Case("中間表現が JSON でない", 2, "中間表現を読めない", raw="{,", pre=plant_old_issues, post=nothing_written),
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
    Case("機能の id の重複", 1, "id F-001 が重複している", ir=edit(lambda ir: ir["features"][1].update(id="F-001"))),
    Case("改行を含む題", 1, "title が空か、1 行でない", ir=edit(lambda ir: f1(ir).update(title="割引\n計算"))),
    Case("Q&A が表に無い", 1, "Q-099 は Q&A 表に無い", ir=edit(lambda ir: f1(ir).update(qa=["Q-099"]))),
    Case("ケースの Q&A が表に無い", 1, "Q-098 は Q&A 表に無い", ir=edit(lambda ir: f1(ir)["cases"][0].update(qa=["Q-098"]))),
    Case("Q&A の重複", 1, "Q&A の No が重複している", ir=edit(lambda ir: f1(ir).update(qa=["Q-001", "Q-001"]))),
    Case("仕様のファイルが無い", 1, "docs/spec/missing.md が無い", ir=edit(lambda ir: f1(ir).update(source=["docs/spec/missing.md"]))),
    Case("仕様の外のファイル", 1, "の中に無い", ir=edit(lambda ir: f1(ir).update(source=["docs/shared/qa.csv"]))),
    Case("ドットの場所の仕様", 1, "`.` で始まる場所", pre=plant_draft_spec,
         ir=edit(lambda ir: f1(ir).update(source=["docs/spec/.draft/order.md"]))),
    Case("中間表現を出所にする", 1, "中間表現そのもの", ir=edit(lambda ir: f1(ir).update(source=["docs/spec/spec_ir.json"]))),
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
         ir=edit(lambda ir: f1(ir).update(source=["docs/spec/a\u0000b.md"]))),
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
         pre=lambda repo: (repo / "docs/spec/spec_ir.json").write_text(
             (repo / "docs/spec/spec_ir.json").read_text(encoding="utf-8").replace('"amount": 9999', '"amount": Infinity'),
             encoding="utf-8")),
    # 孤立したサロゲートは JSON として読めるが UTF-8 で書けない——書く途中で落ちて契約を切り詰めない
    Case("孤立したサロゲート", 1, "孤立したサロゲート",
         raw=json.dumps(IR, ensure_ascii=False).replace("割引額を計算する", "\\ud800"),
         pre=plant_old_contract, post=contract_kept_issues_gone),
    # 桁の大きい整数は float に直せない——`math.isfinite` に渡すと OverflowError で落ちる
    Case("number に桁の大きい整数", 0, "作った",
         ir=edit(lambda ir: f1(ir)["operation"]["input"]["amount"].update(type="number")),
         pre=lambda repo: (repo / "docs/spec/spec_ir.json").write_text(
             (repo / "docs/spec/spec_ir.json").read_text(encoding="utf-8").replace('"amount": 9999', '"amount": 1' + "0" * 400),
             encoding="utf-8")),
    Case("全部を出す", 1, "（2 件）",
         ir=edit(lambda ir: (f1(ir)["operation"].update(method="FETCH"), ir["features"][1].update(title="")))),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("関門を見ない", "    if code:\n        return code, lines + [", "    if False:\n        return code, lines + [", "確認中の Q&A"),
    ("失敗時に Issue の本文を消さない", "        if writing:\n            clear_issues(repo)", "        if False:\n            clear_issues(repo)",
     "確認中の Q&A"),
    ("--dry-run でも Issue の本文を消す", "    writing = not (args.check or args.dry_run)", "    writing = True",
     "--dry-run は失敗しても消さない"),
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
    ("中間表現の実装のモジュールを読まない", 'ir.get("impl_module", DEFAULT_IMPL_MODULE)', "DEFAULT_IMPL_MODULE",
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
    ("深い入れ子を読めないと言わない", "ValueError, RecursionError) as exc:", "ValueError) as exc:", "深い入れ子"),
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
    ("サロゲートを見ない", "    problems = surrogates(ir)\n    if problems:", "    problems = []\n    if problems:", "孤立したサロゲート"),
    ("整数を isfinite に渡す", "        return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))",
     "        return math.isfinite(value) and isinstance(value, (int, float))", "number に桁の大きい整数"),
    ("エラーのケースで error を期待しない", 'expected = case["expected"] if "expected" in case else {"error": case["error"]}',
     'expected = case.get("expected", {})', "正しい実装で緑"),
    ("ケースを 1 つしか作らない", '    for case in sorted(feature["cases"], key=case_order):\n        expected',
     '    for case in sorted(feature["cases"], key=case_order)[:1]:\n        expected',
     "Red テストが失敗する"),
    ("中間表現の sha256 を取らない", "    ir_sha = sha256(raw)", "    ir_sha = sha256(b\"\")", "本文から辿れる"),
    ("Q&A の回答を写さない", "            lines.append(f\"| {no} | {cell(row['質問'])} | {cell(row['回答'])} | {cell(row['反映先'])} |\")",
     "            lines.append(f\"| {no} |\")", "本文から辿れる"),
    ("ケースの Q&A を本文に集めない", '    refs = set(feature["qa"]) | {no for case in cases for no in case.get("qa", [])}',
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
    (root / "docs" / "shared").mkdir(parents=True)
    (root / "docs" / "spec").mkdir(parents=True)
    qa = HEADER + QA_DONE + QA_DONE2 if case.qa is None else case.qa
    if qa:
        (root / "docs" / "shared" / "qa.csv").write_text(qa, encoding="utf-8")
    for rel, body in (case.spec or {"order.md": SPEC}).items():
        (root / "docs" / "spec" / rel).write_text(body, encoding="utf-8")
    if case.raw is not None:
        if case.raw:
            (root / "docs" / "spec" / "spec_ir.json").write_text(case.raw, encoding="utf-8")
    else:
        ir = (case.ir or ONE)(IR)
        (root / "docs" / "spec" / "spec_ir.json").write_text(json.dumps(ir, ensure_ascii=False, indent=2), encoding="utf-8")
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
        sections = table_cells(handoff, "## 節")
        check("SECTIONS が references/handoff-issue.md の節の表と違う", list(constant(source, "SECTIONS") or ()) == sections,
              f"{constant(source, 'SECTIONS')} vs {sections}")
        for rel in (constant(source, "IR_PATH"), constant(source, "QA_PATH"), constant(source, "ISSUES_DIR"),
                    f"{constant(source, 'OUT_DIR')}/openapi.json"):
            check(f"置き場所 {rel} が references/tree.md に無い", rel is not None and rel.rsplit("/", 1)[-1] in tree)
        # 2 つのプラグインの境界の写し
        check("dev-loop の references/spec-gap.md に印が無い", marker is not None and marker in gap)
        skill = DEV_LOOP_SKILL.read_text(encoding="utf-8")
        check("dev-loop の SKILL.md に印が無い（手順 1 が spec-loop の Issue に気づかない）", marker is not None and marker in skill)
        # 陽性対照: 印を上げたら、`SKILL.md` に残った古い印では当たらない
        check("印の版を変えても SKILL.md の照合が不一致にならない",
              marker is not None and marker.replace("v1", "v2") not in skill)
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
