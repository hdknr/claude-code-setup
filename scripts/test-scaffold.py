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
   **本文の指紋と sha256 が、指しているファイルの実物と一致する**こと（中間表現は `merge-versions.py docs build/merged`
   が書いた実物に、**dev-loop の `scripts/spec-fingerprint.py` を実際に当てた出力**と比べる——2 つのプラグインに
   置いた指紋の式の写しが揃っていることも、これで見る）。**指紋は機能単位**——関係の無い機能を直しても変わらない
   （陽性対照: 全体の sha256 は変わる）。撤去の本文は前の版の全体（`build/merged-v<n-1>/`）を指し、そこで辿れる（#290）。
4. **決定論的で、`--check` が鮮度を見る**——2 回の生成でバイト一致。生成直後の `--check` は 0（陽性対照）、
   中間表現を直した後・手で直した後・消した機能の Red テストが残ったときは 1。
5. **生成した OpenAPI で、パスの変数がすべて `in: path`・必須で宣言され、クエリ・ボディに重ならない**（#289）。
   基準の試料（「OpenAPI と型」）と、パスの変数を持つ試料に当てる。パスに在って `input` に無い変数・壊れた波括弧・重複・
   変数の名前だけが違うパスからは作らない。
   **入口ごとに、パラメータとボディを合わせると `<Base>Input` がちょうど復元できる**（#318）——名前・schema・必須の
   どれかが落ちても、`<Base>Input` が入力の一部しか持たなくても赤。`<Base>Input` の項目と schema は `types.py` の
   同名の型と突き合わせる（OpenAPI の中で一緒に落ちる・変わるのを見るため）。exit 0 の全試料に当てる。
6. **本体の定数が `references/` の表と一致する**（メソッド・型・Issue の印と節）。**dev-loop の
   `references/spec-gap.md` も同じ印と節を持ち、dev-loop の `SKILL.md` も同じ印を持つ**（2 つのプラグインの境界の写し）。
6'. **想定外の例外（128KB 超のセルの `csv.Error`）も 2 で、古い Issue の本文を残さない**。`-OO`（docstring が無い）で
   引数なしに呼んでもトレースバックにならない。判定（`run`）の外——引数の解釈——で上がった想定外の例外も入口が 2 にする
   （`argparse` を差し替えて作る。#286）。
7. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

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
import os
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
VERSIONS_REF = PLUGIN / "references" / "versions.md"
SCAFFOLD_SKILL = PLUGIN / "skills" / "scaffold" / "SKILL.md"
SPEC_GAP_REF = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "references" / "spec-gap.md"
# dev-loop の手順 1 は、この印を見て `spec-gap.md` へ送る——印の写しはここにもある
DEV_LOOP_SKILL = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "SKILL.md"
# 前の形（段 5d より前）の印——登録済みの Issue はこの形のまま残るので、dev-loop は読み続ける
LEGACY_MARKERS = ("<!-- spec-loop-handoff: v2 -->", "<!-- spec-loop-handoff: v1 -->")
# dev-loop が手元の中間表現から機能の指紋を出すスクリプト——`scaffold.py` の `fingerprint` の写しを持つ
DEV_FINGERPRINT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "spec-fingerprint.py"
FINGERPRINT = re.compile(r"`([^`]+)` の `(F-[0-9]+)`（機能の指紋: `([0-9a-f]{64})`）")

HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
QA_DONE = "Q-001,要求確定（決定表）,シルバーで 10000 円未満の割引は？,A: 割引なし / B: 3% 割引,A,理由,A（業務部が回答）,決定表 4 行目,反映済み,\n"
QA_DONE2 = "Q-002,仕様レビュー（Red Team）,金額が負なら？,A: 拒否する / B: 0 とみなす,A,理由,A（業務部が回答）,spec/order.md,反映済み,\n"
# 暫定の回答で反映した行——抜ける条件 1 は通るが、中間表現から指せば止まる（利用者の確認待ち。#325）
QA_PROVISIONAL = QA_DONE.replace("A（業務部が回答）,決定表 4 行目,反映済み", "A（推奨案を暫定で採用。業務部 2026-10-21 の指示）,決定表 4 行目,暫定反映")
assert QA_PROVISIONAL != QA_DONE
# `反映済み` で `回答` に「暫定で採用」と書いた行（#366 の実データの形）。暫定は状態だけで決まる——止めない（#404）
QA_WORDED = QA_DONE.replace("A（業務部が回答）", "A（推奨案を暫定で採用。開発側の指示）")
assert QA_WORDED != QA_DONE
# 中間表現のどこからも指さない暫定の行
QA_PROVISIONAL_UNCITED = "Q-004,要求確定（決定表）,返品の受付期間は？,A: 7 日 / B: 14 日,A,理由,A（暫定で採用。業務部 2026-10-21 の指示）,spec/order.md,暫定反映,\n"
# 内部の Q&A 表（spec/qa-dev.csv）の行。中間表現から D- の番号で指せる（#339）
QA_INTERNAL_DONE = "D-001,仕様レビュー（Red Team）,取り消しの記録の保存先は,A: 同じ表 / B: 別の表,B,検索が速い,B（開発 2026-10-22）,spec/order.md,反映済み,\n"
QA_INTERNAL_OPEN = QA_INTERNAL_DONE.replace("B（開発 2026-10-22）,spec/order.md,反映済み", "未回答,—,確認中")
assert QA_INTERNAL_OPEN != QA_INTERNAL_DONE
# 起票したループの印つきの番号（#278）。共有の表と内部の表の両方を、中間表現から指せる
QA_MARKED = "Q-S-001,仕様レビュー（Red Team）,在庫が足りなければ？,A: 拒否する / B: 取り寄せ,A,理由,A（業務部が回答）,spec/order.md,反映済み,\n"
QA_INTERNAL_MARKED = QA_INTERNAL_DONE.replace("D-001,", "D-S-001,", 1)
assert QA_INTERNAL_MARKED != QA_INTERNAL_DONE
QA_OPEN = "Q-003,開発（#9）,期限切れは？,A: 拒否 / B: 受け付ける,A,理由,未回答,—,確認中,\n"

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


def cite_internal(ir: dict) -> None:
    # 共有の行も併せて指す——内部の行だけだと、層の判定を `all` にしても写した元が変わらない（#353 の狭いパス）
    ir["features"][1]["qa"] = ["D-001", "Q-001"]


def cite_marked(ir: dict) -> None:
    # 前の形の番号（Q-001）も併せて指し、表の並びを見る
    ir["features"][1]["qa"] = ["D-S-001", "Q-S-001", "Q-001"]


def marked_in_issue(repo: Path) -> str | None:
    body = (repo / "build" / "scaffold" / "issues" / "F-002.md").read_text(encoding="utf-8")
    order = ("Q-001", "Q-S-001", "D-S-001")  # 共有の表が先・前の形の番号が先（`check-qa-csv.py` の `number_order`）
    missing = [no for no in order if f"| {no} |" not in body]
    if missing:
        return f"Issue の本文に印つきの Q&A（{', '.join(missing)}）が載っていない"
    if [body.index(f"| {no} |") for no in order] != sorted(body.index(f"| {no} |") for no in order):
        return f"Issue の本文の Q&A が {' → '.join(order)} の順に並んでいない"
    # 印つきの D- も内部の層と読む——読まなければ写した元に内部の表が出ない
    return None if "`build/merged/spec/qa-dev.csv`" in body else "印つきの内部の番号を内部の層と読んでいない"


def internal_in_issue(repo: Path) -> str | None:
    body = (repo / "build" / "scaffold" / "issues" / "F-002.md").read_text(encoding="utf-8")
    if "| D-001 |" not in body:
        return "Issue の本文に内部の Q&A（D-001）が載っていない"
    # 写した元にも内部の表を挙げる——共有の表だけを挙げると、dev-loop がそこを引いて D-001 を見つけられない（#339）
    if "`build/merged/spec/qa-dev.csv`" not in body:
        return "Issue の本文が内部の表を写した元に挙げていない"
    # 共有の行（Q-001）しか指さない機能は、内部の表を挙げない——層の判定を外すと全部の Issue に出る（#353）
    shared = (repo / "build" / "scaffold" / "issues" / "F-001.md").read_text(encoding="utf-8")
    return "共有の Q&A しか指さない Issue が内部の表を写した元に挙げている" if "qa-dev.csv" in shared else None


class Case:
    def __init__(self, name: str, code: int, text: str = "", *, ir=None, raw: str | None = None, qa: str | None = None,
                 spec: dict[str, str] | None = None, args: tuple[str, ...] = (), pre: Callable[[Path], None] | None = None,
                 post: Callable[[Path], str | None] | None = None, generate_first: bool = False, impl: str | None = None,
                 extra: dict[str, str] | None = None, root: Path = V1, absent: str = "", env: dict[str, str] | None = None):
        # absent: 出力に現れてはならない文言（対照）。env: 生成のコマンドの環境に重ねるもの（`git` を外す試料）
        self.name, self.code, self.text, self.absent, self.env = name, code, text, absent, env
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


def merge_with_script(repo: Path, out: str = "build/merged", *extra: str) -> Path:
    """`merge-versions.py docs <out>` を走らせ、重ね合わせた全体の根を返す（Issue の本文が指す場所）。"""
    proc = subprocess.run([sys.executable, "-I", str(repo.parent / "scripts" / "merge-versions.py"),
                           str(repo / "docs"), str(repo / out), *extra], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return repo / out


def dev_fingerprint(ir_path: Path, feature: str) -> tuple[int, str]:
    """dev-loop の照合（`spec-gap.md`）が走らせるスクリプトを、そのまま当てる。"""
    proc = subprocess.run([sys.executable, "-I", str(DEV_FINGERPRINT), str(ir_path), feature],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def fingerprint_matches(repo: Path, body: str, feature: str, where: str) -> str | None:
    """本文の指紋が `where` の中間表現を指し、そこに dev-loop のスクリプトを当てた出力と一致するか。"""
    found = FINGERPRINT.search(body)
    if not found or found.group(2) != feature:
        return f"本文に {feature} の機能の指紋が無い"
    if found.group(1) != f"{where}/spec/spec_ir.json":
        return f"本文の指紋が {where}/ の中間表現を指していない: {found.group(1)}"
    code, out = dev_fingerprint(repo / found.group(1), feature)
    if code != 0:
        return f"dev-loop のスクリプトが {found.group(1)} で指紋を出せない（exit={code}）"
    return None if out == found.group(3) else f"{found.group(1)} の {feature} の指紋が本文と違う"


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
    if lines[:3] != ["<!-- spec-loop-handoff: v3 -->", "<!-- spec-loop-feature: F-001 -->",
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
    # 本文の指紋と sha256 と、指しているファイルの実物——中間表現は `merge-versions.py` が書く全体に、dev-loop の照合を当てる
    merge_with_script(repo)
    problem = fingerprint_matches(repo, body, "F-001", "build/merged")
    if problem:
        return problem
    shas = dict(re.findall(r"`([^`]+)`（sha256: `([0-9a-f]{64})`）", body))
    rel = "scaffold/tests/test_f_001.py"
    if rel not in shas:
        return f"本文に {rel} の sha256 が無い"
    if shas[rel] != hashlib.sha256((repo / rel).read_bytes()).hexdigest():
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
    problem = path_params_problem(doc)
    if problem:
        return problem
    post = doc["paths"]["/orders/discount"]["post"]
    if post["operationId"] != "calc_discount" or "400" not in post["responses"] or "requestBody" not in post:
        return f"POST の入口が違う: {post}"
    # パスの変数を持たない入口は #289 の前と同じ形——既存の `scaffold/` の `--check` を古くしない（基準 4）
    if "parameters" in post or post["requestBody"]["content"]["application/json"]["schema"]["$ref"] != "#/components/schemas/CalcDiscountInput":
        return f"パスの変数を持たない POST の形が変わった: {post}"
    if any(name.endswith("Body") for name in doc["components"]["schemas"]):
        return "パスの変数を持たない入口にボディの型を作った"
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


def path_params_problem(doc: dict) -> str | None:
    """OpenAPI の最低限の妥当性: 各パスの `{x}` がすべて `in: path`・必須で宣言され、パスに無い宣言が無く、
    クエリ・ボディに重ねていない（#289）。"""
    schemas = doc["components"]["schemas"]
    for path, ops in doc["paths"].items():
        names = re.findall(r"\{([^{}]*)\}", path)
        for method, op in ops.items():
            params = op.get("parameters", [])
            declared = [p["name"] for p in params if p["in"] == "path"]
            if sorted(declared) != sorted(names):
                return f"{method.upper()} {path}: path パラメータ {declared} がパスの変数 {names} と違う"
            if any(not p.get("required") for p in params if p["in"] == "path"):
                return f"{method.upper()} {path}: path パラメータが必須でない"
            if any(p["name"] in names for p in params if p["in"] != "path"):
                return f"{method.upper()} {path}: パスの変数をクエリにも重ねた"
            ref = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {}).get("$ref")
            if ref and set(schemas[ref.rsplit("/", 1)[1]]["properties"]) & set(names):
                return f"{method.upper()} {path}: パスの変数をボディにも重ねた"
    return None


PY_SCHEMA_TYPES = {"str": "string", "int": "integer", "float": "number", "bool": "boolean"}


def typed_dict_fields(types: str) -> dict[str, dict[str, dict]]:
    """`types.py` の型ごとの項目と、その注釈から戻した JSON Schema の候補。`pass` だけの型は項目が無い。
    候補は `{"types": 許される type の集合, "enum": 値の並び（Literal のときだけ）}`。
    `Literal[...]` は値しか持たない——number の enum の値がすべて整数なら integer と区別できないので、
    整数だけなら integer と number の両方を許し、float が 1 つでもあれば number だけを許す（#318 の N1）。"""
    fields: dict[str, dict[str, dict]] = {}
    for block in re.findall(r"^class (\w+)\(TypedDict\):\n((?:    .+\n)+)", types, flags=re.MULTILINE):
        fields[block[0]] = {}
        for field, note in re.findall(r"^    (\w+): (.+)$", block[1], flags=re.MULTILINE):
            if note.startswith("Literal[") and note.endswith("]"):
                values = ast.literal_eval("[" + note[len("Literal["):-1] + "]")
                kinds = {PY_SCHEMA_TYPES[type(value).__name__] for value in values}
                if kinds == {"integer"}:
                    kinds = {"integer", "number"}
                elif kinds == {"integer", "number"}:
                    kinds = {"number"}
                elif len(kinds) != 1:
                    kinds = set()
                fields[block[0]][field] = {"types": kinds, "enum": values}
            else:
                fields[block[0]][field] = {"types": {PY_SCHEMA_TYPES.get(note, note)}}
    return fields


def schema_matches(schema: dict, expected: dict) -> bool:
    """OpenAPI の項目の schema が、`types.py` の注釈から戻した候補に合うか。"""
    if schema.get("type") not in expected["types"]:
        return False
    if "enum" in expected:
        return set(schema) == {"type", "enum"} and schema["enum"] == expected["enum"]
    return set(schema) == {"type"}


def input_split_problem(doc: dict, types: str) -> str | None:
    """入口ごとに、パラメータとボディを合わせると `<Base>Input` がちょうど復元できる（#318）。
    名前・schema・必須のどれかが落ちても、`<Base>Input` が入力の一部しか持たなくても赤にする。
    `<Base>Input` の項目と schema は、中間表現から OpenAPI とは別に生成される `types.py` の同名の型と突き合わせる
    ——OpenAPI の中だけで比べると、Input・パラメータ・ボディから同じ項目が一緒に落ちたとき、
    同じ schema が一緒に変わったとき（`types.py` は OpenAPI の schema を作る `schema_of` を通らない）に気づけない。"""
    schemas = doc["components"]["schemas"]
    typed = typed_dict_fields(types)
    for name in schemas:
        if not name.endswith("Input"):
            continue
        expected = typed.get(name, {})
        if sorted(schemas[name]["properties"]) != sorted(expected):
            return f"{name} の項目 {sorted(schemas[name]['properties'])} が types.py の {sorted(expected)} と違う"
        for field, schema in schemas[name]["properties"].items():
            if not schema_matches(schema, expected[field]):
                return f"{name} の項目 {field} の schema {schema} が types.py の {expected[field]} と違う"
    for path, ops in doc["paths"].items():
        for method, op in ops.items():
            where = f"{method.upper()} {path}"
            output = op["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[1]
            whole = schemas[output.removesuffix("Output") + "Input"]
            fields = whole["properties"]
            if whole["required"] != sorted(fields):
                return f"{where}: 入力の型の required が全項目でない"
            seen = []
            for p in op.get("parameters", []):
                if not p.get("required"):
                    return f"{where}: {p['in']} パラメータ {p['name']} が必須でない"
                if p["schema"] != fields.get(p["name"]):
                    return f"{where}: {p['in']} パラメータ {p['name']} の schema が入力の型と違う"
                seen.append(p["name"])
            ref = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {}).get("$ref")
            if ref:
                body = schemas[ref.rsplit("/", 1)[1]]
                if body["required"] != sorted(body["properties"]):
                    return f"{where}: ボディの型の required が全項目でない"
                for name, schema in body["properties"].items():
                    if schema != fields.get(name):
                        return f"{where}: ボディの項目 {name} の schema が入力の型と違う"
                    seen.append(name)
            if sorted(seen) != sorted(fields):
                return f"{where}: パラメータとボディの項目 {sorted(seen)} が入力の型の項目 {sorted(fields)} と違う"
    return None


def path_vars_declared(repo: Path) -> str | None:
    doc = json.loads((repo / "scaffold" / "openapi.json").read_text(encoding="utf-8"))
    problem = path_params_problem(doc)
    if problem:
        return problem
    post = doc["paths"].get("/orders/{rank}/discount", {}).get("post")
    if post is None or post["requestBody"]["content"]["application/json"]["schema"]["$ref"] != "#/components/schemas/CalcDiscountBody":
        return f"POST の入口がパスの変数を除いたボディを指さない: {post}"
    if list(doc["components"]["schemas"]["CalcDiscountBody"]["properties"]) != ["amount"]:
        return "CalcDiscountBody がパスの変数を除いた項目でない"
    get = doc["paths"].get("/orders/{shipped}", {}).get("get")
    if get is None or [(p["name"], p["in"]) for p in get["parameters"]] != [("shipped", "path"), ("limit", "query")]:
        return f"GET の入口のパラメータが違う: {get}"
    # 型と Red テストは変わらない——関数はパスの変数も入力の項目として受け取る
    if "    rank: Literal['silver', 'gold']" not in (repo / "scaffold" / "types.py").read_text(encoding="utf-8"):
        return "型からパスの変数が落ちた"
    return None


def path_vars_only(repo: Path) -> str | None:
    doc = json.loads((repo / "scaffold" / "openapi.json").read_text(encoding="utf-8"))
    problem = path_params_problem(doc)
    if problem:
        return problem
    post = doc["paths"]["/orders/{rank}/{amount}"]["post"]
    if "requestBody" in post or [p["name"] for p in post["parameters"]] != ["rank", "amount"]:
        return f"入力がすべてパスの変数の入口が違う: {post}"
    return None


def path_vars_put_delete(repo: Path) -> str | None:
    doc = json.loads((repo / "scaffold" / "openapi.json").read_text(encoding="utf-8"))
    put = doc["paths"].get("/orders/{rank}/discount", {}).get("put")
    if put is None or put["requestBody"]["content"]["application/json"]["schema"]["$ref"] != "#/components/schemas/CalcDiscountBody":
        return f"PUT の入口がパスの変数を除いたボディを指さない: {put}"
    delete = doc["paths"].get("/orders/{shipped}", {}).get("delete")
    if delete is None or "requestBody" in delete or [(p["name"], p["in"]) for p in delete["parameters"]] != [("shipped", "path"), ("limit", "query")]:
        return f"DELETE の入口のパラメータが違う: {delete}"
    return None


def with_path_vars_put_delete(ir: dict) -> None:
    with_path_vars(ir)
    f1(ir)["operation"]["method"] = "PUT"
    ir["features"][1]["operation"]["method"] = "DELETE"


def with_path_vars(ir: dict) -> None:
    f1(ir)["operation"]["path"] = "/orders/{rank}/discount"
    second = ir["features"][1]
    second["operation"]["path"] = "/orders/{shipped}"
    second["operation"]["input"]["limit"] = {"type": "integer"}
    second["cases"][0]["input"]["limit"] = 1


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
QA_V2 = "Q-004,要求確定,返品は何日まで？,A: 7 日 / B: 14 日,A,理由,A（業務部が回答）,spec/return.md,反映済み,\n"
RETURN_SPEC = "# 返品\n\n7 日以内。\n"


# ---- 実装の状態（#294。Red テストと受入基準は、実装が前の版の状態にあることを前提にしない）
# #281: 前の版の実装がもう満たす追加・変更——既存の振る舞いのケースを足す・入力だけ変える
V2_SAME_ADDED = copy.deepcopy(IR["features"][0])
V2_SAME_ADDED["cases"].append({"id": "F-001-C3", "title": "ゴールドの 5000 円は割引なし",
                               "input": {"rank": "gold", "amount": 5000}, "expected": {"discount": 0}})
V2_INPUT_ONLY = copy.deepcopy(IR["features"][0])
V2_INPUT_ONLY["cases"][0]["input"] = {"rank": "silver", "amount": 5000}
# #281: 型を number から integer に狭める（v1 は number。v2 は試料の元の integer に戻す）
V1_NUMBER = edit(lambda ir: f1(ir)["operation"]["output"]["discount"].update(type="number"))
# v2 の変更（V2_CHANGED: シルバーの割引 300）をもう実装した（#282・B）
V2_IMPL = GOOD_IMPL.replace('    return {"discount": 0}', '    return {"discount": 300 if rank == "silver" else 0}')
# どちらの版の期待も満たさない（シルバーの割引 7）
NEITHER_IMPL = GOOD_IMPL.replace('    return {"discount": 0}', '    return {"discount": 7 if rank == "silver" else 0}')
# v2 で入力 amount を total に改名した——実装すると、前の版の Red テストは呼び出しでエラーになる（#294 の 1 パス目）
V2_RENAMED = copy.deepcopy(IR["features"][0])
V2_RENAMED["operation"]["input"] = {("total" if k == "amount" else k): v
                                    for k, v in V2_RENAMED["operation"]["input"].items()}
for _case in V2_RENAMED["cases"]:
    _case["input"] = {("total" if k == "amount" else k): v for k, v in _case["input"].items()}
RENAMED_IMPL = GOOD_IMPL.replace("rank, amount", "rank, total").replace("amount < 0", "total < 0")
RENAMED_NEITHER_IMPL = NEITHER_IMPL.replace("rank, amount", "rank, total").replace("amount < 0", "total < 0")
# v2 で必須の入力 coupon を足した——前の版の状態の実装には、作業中の版の Red テストが呼び出しでエラーになる（#294 の 2 パス目）
V2_NEW_INPUT = copy.deepcopy(IR["features"][0])
V2_NEW_INPUT["operation"]["input"]["coupon"] = {"type": "boolean"}
for _case in V2_NEW_INPUT["cases"]:
    _case["input"]["coupon"] = False
# v2 で関数（operation.id）を改名した——前の版の Red テストは「未実装」で落ちる
V2_OP_RENAMED = copy.deepcopy(IR["features"][0])
V2_OP_RENAMED["operation"]["id"] = "compute_discount"
OP_RENAMED_NEITHER_IMPL = NEITHER_IMPL.replace("def calc_discount(", "def compute_discount(")


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
    if body.splitlines()[:3] != ["<!-- spec-loop-handoff: v3 -->", "<!-- spec-loop-feature: F-001 -->",
                                 "<!-- spec-loop-change: modify; base=v1 -->"]:
        return f"変更の印でない: {body.splitlines()[:3]}"
    if not sections_in_order(body):
        return "変更の本文の節が揃っていない"
    index = json.loads((repo / ISSUES / "issues.json").read_text(encoding="utf-8"))
    if index != [{"feature": "F-001", "title": "F-001: 割引額を計算する（v2 で変更）", "change": "modify",
                  "body": "F-001.md", "red": ["TestF001.test_f_001_c1"]}]:
        return f"issues.json が違う: {index}"
    return body_has(body, ("| `F-001-C1` | 変更 |", "| `F-001-C2` | 回帰 |", "変化: 変更（v1 の時点から v2 で変えた機能）",
                           "`merge-versions.py docs build/merged --upto 2`", "**`回帰` のケースも緑であること**",
                           "前の版の実装の上で失敗しうるのは `追加`・`変更` のケース（1 件）だけで",
                           "**ほかの機能は、周の前に緑だった Red テストが、周の後も緑のままであること**"), "変更")


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
    # 撤去の本文は前の版の全体を指す（#290 の P1-8）——本文のコマンドで作り、仕様の原文と指紋がそこで辿れる
    command = "`merge-versions.py docs build/merged-v1 --upto 1`"
    if command not in body:
        return f"撤去の本文に前の版の全体の作り方 {command} が無い"
    # 末尾の照合は、どちらのコマンドで作った全体に何を当てるかを名指しする（1 パス目 CR4）
    if ("`build/merged-v1/spec/spec_ir.json` での機能の指紋が上と違うか" not in body
            or "`build/merged/spec/spec_ir.json` にこの機能が残っているなら" not in body):
        return "撤去の本文の末尾が、前の版の全体での一致と作業中の版の全体での不在を分けて書いていない"
    # 文言ではなく、本文に書いたコマンドそのものを走らせる（1 パス目 CR8）
    written = command.strip("`").split()[1:]
    old = merge_with_script(repo, written[1], *written[2:])
    sources = re.search(r"^- 仕様の原文（v1 の時点）: (.+)$", body, flags=re.MULTILINE)
    paths = re.findall(r"`([^`]+)`", sources.group(1)) if sources else []
    if not paths or any(not p.startswith("build/merged-v1/") or not (repo / p).is_file() for p in paths):
        return f"撤去の本文の仕様の原文が、前の版の全体の中に辿れない: {paths}"
    problem = fingerprint_matches(repo, body, "F-002", "build/merged-v1")
    if problem:
        return problem
    # 作業中の版の全体には、その機能が無い（dev-loop のスクリプトは 3）。陽性対照: 前の版の全体には在る
    code, _ = dev_fingerprint(merge_with_script(repo) / "spec" / "spec_ir.json", "F-002")
    if code != 3:
        return f"作業中の版の全体で、撤去した機能が「無い」にならない（exit={code}）"
    if dev_fingerprint(old / "spec" / "spec_ir.json", "F-002")[0] != 0:
        return "前の版の全体に撤去した機能が無い（試料が判別しない）"
    # 読めない全体は「無い」（3）ではなく「比べていない」（2）——3 だと読み損ねで撤去が確かめられたことになる（2 パス目 CR2-3）
    code, _ = dev_fingerprint(repo / "build" / "merged-missing" / "spec" / "spec_ir.json", "F-002")
    if code != 2:
        return f"読めない中間表現で、dev-loop のスクリプトが 2 を返さない（exit={code}）"
    return body_has(body, ("理由: 取り消しはやめる", "撤去する API: `GET /orders/cancelable`", "| `F-002-C1` | 削除 |",
                           "—（`scaffold/tests/test_f_002.py` ごと消した）", "モジュール `spec_impl` の関数 `can_cancel`",
                           "python3 -m unittest discover -s scaffold/tests\n", "この機能が根拠にした Q&A は無い"), "撤去")


def outcomes(repo: Path) -> dict[str, str]:
    """{テストの id: ok／FAIL／ERROR}（`unittest -v` の行から）。"""
    proc = subprocess.run([sys.executable, "-E", "-s", "-m", "unittest", "discover", "-v", "-s", "scaffold/tests"],
                          capture_output=True, text=True, cwd=repo)
    return dict((m.group(1), m.group(2)) for m in re.finditer(r"^\S+ \(([^)]+)\) \.\.\. (ok|FAIL|ERROR)$",
                                                               proc.stderr, flags=re.MULTILINE))


def removal_before_after(repo: Path) -> str | None:
    """撤去の受入基準が、同じ版で足した機能が未実装のままでも満たせる（前後で緑の集合が減らない）。"""
    body = bodies(repo).get("F-002", "")
    if "周の前に緑だった Red テストが、周の後も緑のままであること" not in body:
        return "撤去の本文の受入基準が、周の前後を比べる形でない"
    if "ほかの Red テストがすべて緑のまま" in body:
        return "撤去の本文が、同じ版の未実装の追加と両立しない受入基準を残している"
    before = outcomes(repo)
    # 陽性対照: 撤去の前は「全部が緑」ではない（F-003 が未実装）——#280 の行き止まりがこの試料で起きている
    if not before or all(v == "ok" for v in before.values()):
        return f"試料が #280 を再現していない（撤去の前に全部が緑か、何も走らない）: {before}"
    (repo / "spec_impl.py").write_text(GOOD_IMPL.split("\n\n\ndef can_cancel")[0] + "\n", encoding="utf-8")
    after = outcomes(repo)
    lost = sorted(t for t, v in before.items() if v == "ok" and after.get(t) != "ok")
    return f"撤去の後に緑でなくなった: {lost}" if lost else None


def red_check_wrote_nothing(repo: Path) -> str | None:
    """`--red-check` は前の版の Red テストを一時ディレクトリに作る——`scaffold/tests/` と根に置かない。"""
    tests = sorted(p.name for p in (repo / "scaffold" / "tests").glob("test_*.py"))
    if tests != ["test_f_001.py", "test_f_003.py"]:
        return f"scaffold/tests/ に前の版の Red テストが残った: {tests}"
    if (repo / "tests").exists():
        return "正本リポジトリの根に tests/ を作った"
    cache = sorted(str(p.relative_to(repo)) for p in repo.rglob("*.pyc"))
    if cache:
        return f"正本リポジトリにバイトコードを書いた: {cache}"
    return None


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
    """v2 で作った後に v3 を足す（F-001 の題を変える）——本文の再現コマンドは v2 の全体を作り直せること（#262 の R2）。

    **v3 は F-001 そのものを変える**——指紋は機能単位なので、ほかの機能や全体の題だけを変える v3 では、
    版を指定しなくても指紋が合い、下の陽性対照が判別しない。
    """
    path = repo / "docs" / "v3" / "spec" / "spec_ir.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"features": [dict(V2_CHANGED, title="割引額を計算する（v3）")]}, ensure_ascii=False),
                    encoding="utf-8")


def sha_reproducible_after_v3(repo: Path) -> str | None:
    body = bodies(repo)["F-001"]
    ir = repo / "build" / "merged" / "spec" / "spec_ir.json"
    expected = FINGERPRINT.search(body).group(3)
    # 陽性対照: 版を指定しないと v3 まで重なり、本文の指紋と合わない
    merge_with_script(repo)
    if dev_fingerprint(ir, "F-001")[1] == expected:
        return "v3 を足しても F-001 の指紋が変わらない（試料が判別しない）"
    command = re.search(r"`(merge-versions\.py [^`]+)`", body).group(1).split()[1:]
    merge_with_script(repo, command[1], *command[2:])
    return None if dev_fingerprint(ir, "F-001")[1] == expected else f"本文のコマンド {command} で作った中間表現の指紋が本文と違う"


# v2 で F-002 の題だけを変える——F-001 とは関係の無い機能の編集（#290 の CR5）
V2_OTHER = dict(IR["features"][1], title="注文を取り消せるか（v2 で言い換え）")


def note_before_unrelated(repo: Path) -> None:
    """v2 で F-001 を変えて作った本文の指紋と、全体の sha256 を控え、F-002 だけを直す（同じ版の作り直しの経路）。"""
    body = bodies(repo)["F-001"]
    whole = merge_with_script(repo) / "spec" / "spec_ir.json"
    note = {"fingerprint": FINGERPRINT.search(body).group(3), "whole": hashlib.sha256(whole.read_bytes()).hexdigest()}
    (repo.parent / "before.json").write_text(json.dumps(note), encoding="utf-8")
    shutil.rmtree(repo / "build" / "merged")
    (repo / V2 / "spec" / "spec_ir.json").write_text(json.dumps({"features": [V2_CHANGED, V2_OTHER]}, ensure_ascii=False),
                                                     encoding="utf-8")


def unrelated_edit_keeps_fingerprint(repo: Path) -> str | None:
    note = json.loads((repo.parent / "before.json").read_text(encoding="utf-8"))
    whole = merge_with_script(repo) / "spec" / "spec_ir.json"
    # 陽性対照: 全体の sha256 は変わる（v2 の本文までの照合なら、F-001 の Issue は不一致になっていた）
    if hashlib.sha256(whole.read_bytes()).hexdigest() == note["whole"]:
        return "F-002 を直しても全体が変わらない（試料が判別しない）"
    body = bodies(repo)["F-001"]
    if FINGERPRINT.search(body).group(3) != note["fingerprint"]:
        return "関係の無い機能（F-002）を直しただけで、F-001 の指紋が変わった"
    problem = fingerprint_matches(repo, body, "F-001", "build/merged")
    if problem:
        return problem
    # その機能自身を変えれば指紋は変わる——v1 の F-001 と v2 の F-001
    old = merge_with_script(repo, "build/merged-v1", "--upto", "1") / "spec" / "spec_ir.json"
    if dev_fingerprint(old, "F-001")[1] == note["fingerprint"]:
        return "F-001 を変えても指紋が変わらない"
    return None


def add_v2_changed(repo: Path) -> None:
    for rel, text in v2([V2_CHANGED]).items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


# v1 の機能 F-002 の期待の型が誤り（v2 で直した）——前の版の中間表現が決まりに反する
BAD_V1 = edit(lambda ir: ir["features"][1]["cases"][0].update(expected={"ok": "yes"}))
# v1 の F-001 のパスの変数が入力に無い（#289 より前の scaffold は通した）
OLD_PATH_V1 = edit(lambda ir: f1(ir)["operation"].update(path="/orders/{order_id}"))
# v1 で F-001 が指す Q-001 が確認中（v2 で反映済みに置き換える）——前の版の時点でも抜ける条件 1 を通らない状態
QA_OPEN_Q001 = QA_DONE.replace(",反映済み,", ",確認中,")
assert QA_OPEN_Q001 != QA_DONE
# v1 の F-001 が表に無い Q-009 も指す（v2 で直した）
MISSING_QA_V1 = edit(lambda ir: f1(ir).update(qa=["Q-001", "Q-009"]))


def only_f001_modified(repo: Path) -> str | None:
    found = bodies(repo)
    if list(found) != ["F-001"]:
        return f"本文を作るのはパスを直した機能だけのはず: {list(found)}"
    if "<!-- spec-loop-change: modify; base=v1 -->" not in found["F-001"]:
        return "パスを直した機能が変更の本文になっていない"
    return None


# ---- 前の版の時点が崩れている（#361。反映済みでない Q&A が v1 に残る）
QA_OPEN_UNCITED = QA_PROVISIONAL_UNCITED.replace(",暫定反映,", ",確認中,")
assert QA_OPEN_UNCITED != QA_PROVISIONAL_UNCITED
# 試料の git は利用者の設定を読まない（`test-check-signoff.py` と同じ形）
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}


def git_in(where: Path, *args: str) -> None:
    assert_in_tmp(where)
    subprocess.run(["git", "-C", str(where), *args], check=True, capture_output=True, env=GIT_ENV)


def release(tag: str | None = "release-v1", top: str = "") -> Callable[[Path], None]:
    """試料を git のリポジトリにして commit し、`tag` を付ける（`top` は根にする親のディレクトリ）。"""
    def apply(repo: Path) -> None:
        root = repo / top if top else repo
        git_in(root, "init", "-q")
        git_in(root, "add", "-A")
        git_in(root, "commit", "-q", "-m", "v1")
        if tag:
            git_in(root, "tag", tag)
    return apply


def shallow_release(repo: Path) -> None:
    release()(repo)
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                          env=GIT_ENV).stdout.strip()
    (repo / ".git" / "shallow").write_text(head + "\n", encoding="utf-8")
    # 浅い clone はタグを取らない——タグが見えないのを「凍結していない」と読まないこと（タグが残ると、
    # `check-frozen.py` の浅い clone の検査が先に 2 を返し、scaffold 側の検査を外しても判別しない）
    git_in(repo, "tag", "-d", "release-v1")


def edited_after_release(repo: Path) -> None:
    """凍結した後に `docs/v1/` を直す（作業ツリー）——`check-frozen.py` は 1。"""
    release()(repo)
    spec = repo / "docs" / "v1" / "spec" / "order.md"
    spec.write_text(spec.read_text(encoding="utf-8") + "\n凍結の後に足した行\n", encoding="utf-8")


def release_without_version(repo: Path) -> None:
    """`docs/v1/` を持たないコミットに `release-v1` を付ける——`check-frozen.py` は 2。"""
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    git_in(repo, "init", "-q")
    git_in(repo, "add", "README.md")
    git_in(repo, "commit", "-q", "-m", "before v1")
    git_in(repo, "tag", "release-v1")


def other_release_edited(repo: Path) -> None:
    """`release-v1` と `release-v2` を付けて `docs/v2/` だけを直す——v1 の凍結は変わらない（2 パス目の P2-1）。
    `check-frozen.py` を版で絞らずに呼べば 1 になる。"""
    release()(repo)
    git_in(repo, "tag", "release-v2")
    spec = repo / "docs" / "v2" / "spec" / "return.md"
    spec.write_text(spec.read_text(encoding="utf-8") + "\n凍結の後に足した行\n", encoding="utf-8")


def other_release_without_version(repo: Path) -> None:
    """`docs/v2/` を持たないコミットに `release-v2` を付け、その後に `release-v1` を付ける——v1 の凍結は変わらない。
    `check-frozen.py` を版で絞らずに呼べば 2 になる。"""
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    git_in(repo, "init", "-q")
    git_in(repo, "add", "README.md")
    git_in(repo, "commit", "-q", "-m", "before v1")
    git_in(repo, "tag", "release-v2")
    git_in(repo, "add", "-A")
    git_in(repo, "commit", "-q", "-m", "v1")
    git_in(repo, "tag", "release-v1")


def drop_v1_ir(repo: Path) -> None:
    (repo / "docs" / "v1" / "spec" / "spec_ir.json").unlink()


def frozen_all_added(repo: Path) -> str | None:
    found = bodies(repo)
    if list(found) != ["F-001"]:
        return f"凍結した前の版が崩れていたら v2 の機能を全部 追加 にするはず: {list(found)}"
    if "<!-- spec-loop-change: add; base=v1 -->" not in found["F-001"]:
        return "凍結した前の版から変わっていない機能が 追加 の本文になっていない"
    # 凍結した版を作れることそのもの（C）——凍結の確かめは直されていないと言う
    proc = subprocess.run([sys.executable, "-I", str(repo.parent / "scripts" / "check-frozen.py"), "--repo", str(repo)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return f"凍結の確かめが 0 でない（凍結した版を作れていない）: {proc.stdout}{proc.stderr}"
    return None


def remedy(repo: Path) -> None:
    """`versions.md` の「前の版の時点が崩れていたら」の手当てを、書いてあるとおりに流す（#355）。"""
    aside = repo.parent / "v2-aside"
    shutil.move(str(repo / V2), str(aside))  # 1. docs/ の外へ退ける
    (repo / V1 / "shared" / "qa.csv").write_text(HEADER + QA_DONE + QA_DONE2, encoding="utf-8")  # 2. 確定する
    scaffold = [sys.executable, "-I", str(repo.parent / "scripts" / TARGET), "--repo", str(repo)]
    # 3. v1 で作る（失敗すれば v1 の scaffold/ が無く、本体の `--check --upto 1` が古いと言う）
    subprocess.run(scaffold, capture_output=True, text=True)
    shutil.move(str(aside), str(repo / V2))  # 4. 戻す

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
    Case("暫定反映の Q&A を指す", 1, "Q-001: 状態が 暫定反映", qa=HEADER + QA_PROVISIONAL + QA_DONE2),
    # 中間表現が指さない暫定の行でも止める——仕様には反映されているので、指さない機能にも効いている（#325 の 2 パス目）
    Case("暫定反映の Q&A を指さない", 1, "Q-004: 状態が 暫定反映", qa=HEADER + QA_DONE + QA_DONE2 + QA_PROVISIONAL_UNCITED),
    Case("文言だけ暫定の反映済みは止めない", 0, qa=HEADER + QA_WORDED + QA_DONE2),
    Case("内部の Q&A を指す", 0, ir=edit(cite_internal), spec={"order.md": SPEC, "qa-dev.csv": HEADER + QA_INTERNAL_DONE},
         post=internal_in_issue),
    Case("内部の Q&A が反映済みでない（関門が止める）", 1, "qa-dev.csv: D-001: 状態が 確認中", ir=edit(cite_internal),
         spec={"order.md": SPEC, "qa-dev.csv": HEADER + QA_INTERNAL_DONE.replace("反映済み", "確認中")}),
    Case("内部の表に無い D- を指す", 1, "D-001 は Q&A 表に無い", ir=edit(cite_internal)),
    Case("印つきの番号を指す", 0, ir=edit(cite_marked), qa=HEADER + QA_DONE + QA_DONE2 + QA_MARKED,
         spec={"order.md": SPEC, "qa-dev.csv": HEADER + QA_INTERNAL_MARKED}, post=marked_in_issue),
    Case("印の形に反する番号を指す", 1, "Q&A の No の形に反する（'Q-X-001'）",
         ir=edit(lambda ir: ir["features"][1].__setitem__("qa", ["Q-X-001"]))),
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
    # ケースの ref——仕様の原文にその番号が在るか（#465）。在れば通る（陽性対照）・無い／別の番号の一部／空なら断る
    Case("ケースの ref が仕様に在る", 0, ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10")),
         spec={"order.md": SPEC + "| R-F10 | silver | 9999 | 0 |\n"}),
    Case("ケースの ref が仕様に無い", 1, "R-F10 が仕様の原文（source）のどこにも無い",
         ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10"))),
    Case("ケースの ref が別の番号の一部にしか無い", 1, "R-F10 が仕様の原文（source）のどこにも無い",
         ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10")),
         spec={"order.md": SPEC + "| R-F100 | x |\n| R-F10a | y |\n| R-F10.1 | z |\n| R-F10/2 | w |\n| R-F10ａ | v |\n"}),
    # 前に付く形も別の番号の一部（#465 の 2 パス目）
    Case("ケースの ref が別の番号の後ろの一部にしか無い", 1, "R-F10 が仕様の原文（source）のどこにも無い",
         ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10")), spec={"order.md": SPEC + "| XR-F10 | x |\n| ＸR-F10 | y |\n"}),
    Case("数字の ref が小番号にしか無い", 1, "1 が仕様の原文（source）のどこにも無い",
         ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="1")), spec={"order.md": SPEC + "| R-F10.1 | x |\n"}),
    # 区切りの後ろが数字でなければ在ることにする（2 パス目の P2）
    Case("拡張子の付いた ref は在ることにする", 0, ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10")),
         spec={"order.md": SPEC + "R-F10.md を見る。\n"}),
    Case("区切りの後ろの ref は在ることにする", 0, ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F11")),
         spec={"order.md": SPEC + "R-F10/R-F11 を参照。\n"}),
    Case("--dry-run もケースの ref を見る", 1, "R-F10 が仕様の原文（source）のどこにも無い", args=("--dry-run",),
         ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10"))),
    Case("文末の ref は在ることにする", 0, ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10")),
         spec={"order.md": SPEC + "割引は R-F10.\n"}),
    Case("--check もケースの ref を見る", 1, "R-F10 が仕様の原文（source）のどこにも無い", args=("--check",),
         ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10"))),
    Case("ケースの ref が空", 1, "仕様の中の番号（1 行・前後に空白なし）でない", ir=edit(lambda ir: f1(ir)["cases"][0].update(ref=""))),
    # 原文に「R-F10 |」と在っても、前後に空白のある ref・複数行の ref は断る（#465 の 1 パス目）
    Case("ケースの ref の後ろに空白", 1, "仕様の中の番号（1 行・前後に空白なし）でない",
         ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10 ")), spec={"order.md": SPEC + "| R-F10 | x |\n"}),
    Case("ケースの ref が複数行", 1, "仕様の中の番号（1 行・前後に空白なし）でない",
         ir=edit(lambda ir: f1(ir)["cases"][0].update(ref="R-F10\nR-F11")), spec={"order.md": SPEC + "| R-F10 | x |\n| R-F11 | y |\n"}),
    # source に spec/ の外のファイルを書いても（check_source が断る）、ref はそこで探さない（#465 の 1 パス目）
    Case("ケースの ref を仕様の外のファイルで探さない", 1, "R-F10 が仕様の原文（source）のどこにも無い",
         ir=edit(lambda ir: (f1(ir).update(source=["spec/order.md", "requirements/r.md"]),
                             f1(ir)["cases"][0].update(ref="R-F10"))),
         extra={"docs/v1/requirements/r.md": "R-F10\n"}),
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
    # ---- パスの変数（#289）
    Case("パスの変数", 0, "作った", ir=edit(with_path_vars), post=path_vars_declared),
    Case("パスの変数の Red テスト", 0, ir=edit(with_path_vars), post=expect_red(3)),
    Case("パスの変数（PUT・DELETE）", 0, "作った", ir=edit(with_path_vars_put_delete), post=path_vars_put_delete),
    Case("入力がすべてパスの変数", 0, "作った",
         ir=edit(lambda ir: f1(ir)["operation"].update(path="/orders/{rank}/{amount}")), post=path_vars_only),
    # 入力が空の入口（#318。新しい検査が誤って断らない）
    Case("入力が空（GET）", 0, "作った", ir=edit(lambda ir: (ir["features"][1]["operation"].update(input={}),
                                                       ir["features"][1]["cases"][0].update(input={})))),
    Case("入力が空（POST）", 0, "作った", ir=edit(lambda ir: (ir["features"][1]["operation"].update(input={}, method="POST"),
                                                        ir["features"][1]["cases"][0].update(input={})))),
    # number の enum（#318 の N1。`Literal[...]` は値の型しか持たないので、新しい検査が integer と取り違えて断らない）
    Case("number の enum の先頭が整数", 0, "作った",
         ir=edit(lambda ir: (f1(ir)["operation"]["input"]["rank"].update(type="number", enum=[1, 2.5]),
                             f1(ir)["cases"][0]["input"].update(rank=1), f1(ir)["cases"][1]["input"].update(rank=2.5)))),
    Case("number の enum の値がすべて整数", 0, "作った",
         ir=edit(lambda ir: (f1(ir)["operation"]["input"]["rank"].update(type="number", enum=[1, 2]),
                             f1(ir)["cases"][0]["input"].update(rank=1), f1(ir)["cases"][1]["input"].update(rank=2)))),
    Case("パスの変数が入力に無い", 1, "パスの変数 {order_id} が operation.input の項目に無い", pre=plant_old_issues,
         post=issues_gone, ir=edit(lambda ir: f1(ir)["operation"].update(path="/orders/{order_id}"))),
    Case("空のパスの変数", 1, "パスの変数 {} が operation.input の項目に無い",
         ir=edit(lambda ir: f1(ir)["operation"].update(path="/orders/{}"))),
    Case("波括弧が対でない", 1, "波括弧が対になっていない", ir=edit(lambda ir: f1(ir)["operation"].update(path="/orders/{rank"))),
    Case("閉じ括弧だけ", 1, "波括弧が対になっていない", ir=edit(lambda ir: f1(ir)["operation"].update(path="/orders/rank}"))),
    Case("パスの変数の重複", 1, "パスの変数 {rank} が重複している",
         ir=edit(lambda ir: f1(ir)["operation"].update(path="/orders/{rank}/{rank}"))),
    Case("変数の名前だけが違うパス", 1, "/orders/{shipped} は /orders/{rank} と変数の名前だけが違う",
         ir=edit(lambda ir: (f1(ir)["operation"].update(path="/orders/{rank}"),
                             ir["features"][1]["operation"].update(path="/orders/{shipped}")))),
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
    # 128KB 超のセル（csv.Error）も予期しない失敗として 2 で、古い Issue の本文を残さない（#286）
    Case("巨大なセル", 2, "予期しない失敗（Error: field larger", pre=plant_old_issues, post=issues_gone, absent="Traceback",
         qa=HEADER + QA_DONE.replace("シルバーで 10000 円未満の割引は？", "x" * 200_000) + QA_DONE2),
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
    Case("v3 を足しても本文の指紋が合う", 0, generate_first=True, extra=v2([V2_CHANGED]), pre=add_v3,
         args=("--check", "--upto", "2"), post=sha_reproducible_after_v3),
    Case("関係の無い機能を直しても指紋は変わらない", 0, "modify 2", generate_first=True, extra=v2([V2_CHANGED]),
         pre=note_before_unrelated, post=unrelated_edit_keeps_fingerprint),
    Case("前の版の中間表現が決まりに反する", 1, "前の版（v1）の中間表現が決まりに反する", ir=BAD_V1,
         extra=v2([IR["features"][1]]), pre=plant_old_issues, post=nothing_written_issues),
    # #319: #289 より前の scaffold が通した v1（凍結していて直せない）のパスの変数は、v2 で直せば作れる
    Case("前の版だけパスの変数が入力に無い", 0, "modify 1", ir=OLD_PATH_V1, extra=v2([IR["features"][0]]),
         post=only_f001_modified),
    # --red-check も前の版を比べる相手として読むので、パスの変数で止まらない（前の版の Red テストの中身までは見ない）
    Case("前の版だけパスの変数が入力に無い（--red-check）", 0, "失敗 0 件（追加・変更）・緑 3 件（回帰）", args=("--red-check",), generate_first=True,
         ir=OLD_PATH_V1, extra=v2([IR["features"][0]]), impl=GOOD_IMPL),
    Case("前の版だけパスの変数が入力に無い（--dry-run）", 0, "modify 1", args=("--dry-run",), ir=OLD_PATH_V1,
         extra=v2([IR["features"][0]]), post=nothing_written),
    # 前の版の時点を作る・確かめるときは決まりを外さない（生成するので外せない。spec-ir.md の移行の 3）
    Case("前の版だけパスの変数が入力に無い（--check --upto 1）", 1, "パスの変数 {order_id} が operation.input の項目に無い",
         args=("--check", "--upto", "1"), ir=OLD_PATH_V1, extra=v2([IR["features"][0]])),
    Case("前の版だけパスの変数が入力に無い（--dry-run --upto 1）", 1, "パスの変数 {order_id} が operation.input の項目に無い",
         args=("--dry-run", "--upto", "1"), ir=OLD_PATH_V1, extra=v2([IR["features"][0]])),
    # #335: v1 で暫定反映の Q-001 を指し、v2 で反映済みに置き換えた——v1 は scaffold できていないので止め、そう名指しする
    Case("前の版で暫定だった Q&A を後の版で確定する", 1, "v1 の時点では 反映済み でない Q&A が残り、v1 の scaffold は作れていない"
         "（`--check --upto 1` が 0 にならない）。v2 の差分を測る土台が無い——references/versions.md の「前の版の時点が崩れていたら」",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=plant_old_issues,
         post=nothing_written_issues),
    Case("前の版で暫定だった Q&A（どの状態か）", 1, "v1 の時点の Q-001: 状態が 暫定反映（反映済み でない）",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE)),
    # 前の版の時点を作るときも止まる（今の版と同じ関門）
    Case("前の版で暫定だった Q&A（--check --upto 1）", 1, "Q-001: 状態が 暫定反映", args=("--check", "--upto", "1"),
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE)),
    Case("前の版で暫定だった Q&A（--dry-run --upto 1）", 1, "Q-001: 状態が 暫定反映", args=("--dry-run", "--upto", "1"),
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE)),
    # #361: 前の版で確認中だった——条件 1 で v1 の scaffold も作れないので、同じく名指しする（#335 の対照を反転。人間の判断）
    Case("前の版で確認中だった Q&A を後の版で確定する", 1, "v1 の時点の Q-001: 状態が 確認中（反映済み でない）",
         qa=HEADER + QA_OPEN_Q001 + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=plant_old_issues,
         post=nothing_written_issues),
    Case("前の版で確認中だった Q&A（名指し）", 1, "v1 の scaffold は作れていない",
         qa=HEADER + QA_OPEN_Q001 + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE)),
    # #358: 中間表現が指していない行でも止まる（v2 の QA_V2 が Q-004 を反映済みに置き換える）
    Case("前の版に指していない暫定反映の行がある", 1, "v1 の時点の Q-004: 状態が 暫定反映（反映済み でない）",
         qa=HEADER + QA_DONE + QA_DONE2 + QA_PROVISIONAL_UNCITED, extra=v2([V2_CHANGED]), pre=plant_old_issues,
         post=nothing_written_issues),
    Case("前の版に指していない暫定反映の行がある（--dry-run）", 1, "v1 の scaffold は作れていない", args=("--dry-run",),
         qa=HEADER + QA_DONE + QA_DONE2 + QA_PROVISIONAL_UNCITED, extra=v2([V2_CHANGED]), post=nothing_written),
    Case("前の版に指していない暫定反映の行がある（--red-check）", 1, "v1 の scaffold は作れていない", args=("--red-check",),
         qa=HEADER + QA_DONE + QA_DONE2 + QA_PROVISIONAL_UNCITED, extra=v2([V2_CHANGED]), impl=GOOD_IMPL),
    Case("前の版に指していない確認中の行がある", 1, "v1 の時点の Q-004: 状態が 確認中（反映済み でない）",
         qa=HEADER + QA_DONE + QA_DONE2 + QA_OPEN_UNCITED, extra=v2([V2_CHANGED]), pre=plant_old_issues,
         post=nothing_written_issues),
    # 内部の表（qa-dev.csv）の行も見る——v2 で D-001 を反映済みに置き換える
    Case("前の版の内部の表に確認中の行がある", 1, "v1 の時点の D-001: 状態が 確認中（反映済み でない）",
         spec={"order.md": SPEC, "qa-dev.csv": HEADER + QA_INTERNAL_OPEN},
         extra=v2([V2_CHANGED], spec={"return.md": RETURN_SPEC, "qa-dev.csv": HEADER + QA_INTERNAL_DONE}),
         pre=plant_old_issues, post=nothing_written_issues),
    # #355: versions.md の手当て（v2 を docs/ の外へ退け、v1 を確定して作り、戻す）を流すと、前の版の時点が新しくなり v2 を作れる
    Case("前の版の時点を直す手当て（--check --upto 1）", 0, "新しい（v1 まで", args=("--check", "--upto", "1"),
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=remedy),
    Case("前の版の時点を直す手当て（v2 を作る）", 0, "modify 1",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=remedy,
         post=lambda repo: None if list(bodies(repo)) == ["F-001"] else f"本文は v2 で変えた機能だけのはず: {list(bodies(repo))}"),
    # #357: 凍結した v1（release-v1）に暫定反映が残る状態は作れる——直せないので止めず、v2 の機能を全部 追加 にする
    Case("凍結した前の版が崩れている", 0, "v1 は release-v1 で凍結していて直せない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2,
         extra=v2([V2_CHANGED], qa=HEADER + QA_DONE, removed="機能,F-002,取り消しはやめる\n"), pre=release(),
         post=frozen_all_added, absent="変わっていない機能の本文は作らない"),
    # タグがあるだけでは凍結と読まない（1 パス目の P1-1）——タグの後に直した版は止め、タグの時点に版が無ければ判定しない
    Case("凍結した前の版がタグの後に直されている", 1, "v1 は凍結しているのに直されている",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=edited_after_release,
         absent="凍結していて直せない"),
    Case("凍結のタグの時点に前の版が無い", 2, "v1 が凍結しているかを判定していない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=release_without_version),
    # 別の版のタグは v1 の凍結を言わない（P1-4）
    Case("別の版のタグで凍結と読まない", 1, "v1 の scaffold は作れていない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=release("release-v2"),
         absent="凍結していて"),
    # 他の版のタグの状態は v1 の凍結を変えない（2 パス目の P2-1）——直された版・版の無いタグが v2 の側にあっても全部を追加にする
    Case("他の版のタグの後の直しで止めない", 0, "v1 は release-v1 で凍結していて直せない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=other_release_edited,
         absent="直されている"),
    Case("他の版のタグの時点に版が無くても判定する", 0, "v1 は release-v1 で凍結していて直せない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE),
         pre=other_release_without_version, absent="凍結しているかを判定していない"),
    # git を起動できなければ凍結を判定しない（P1-9）
    Case("凍結を判定できない（git を起動できない）", 2, "git を起動できない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), env={"PATH": ""},
         pre=plant_old_issues, post=nothing_written_issues),
    # 前の版に中間表現が無くても、Q&A の状態は見る（P1-6）
    Case("中間表現の無い前の版に暫定反映の行がある", 1, "v1 の時点の Q-004: 状態が 暫定反映（反映済み でない）",
         qa=HEADER + QA_DONE + QA_DONE2 + QA_PROVISIONAL_UNCITED,
         extra=v2(IR["features"], top={k: v for k, v in IR.items() if k != "features"}), pre=drop_v1_ir,
         post=nothing_written),
    Case("凍結した前の版が崩れている（撤去を名指し）", 0, "v2 で消した機能（F-002）の撤去の本文は作らない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2,
         extra=v2([V2_CHANGED], qa=HEADER + QA_DONE, removed="機能,F-002,取り消しはやめる\n"), pre=release()),
    # 対照: git でもタグが無ければ凍結していない——止まる
    Case("凍結していない git の前の版が崩れている", 1, "v1 の scaffold は作れていない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=release(None),
         absent="凍結していて"),
    # 対照: 親のリポジトリのタグは、この docs/ の凍結を言わない（check-frozen.py も根の docs/ を見る）
    Case("親のリポジトリのタグで凍結と読まない", 1, "v1 の scaffold は作れていない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=release(top=".."),
         absent="凍結していて"),
    # 浅い clone はタグがそろわない——凍結しているかを判定しない
    Case("凍結を判定できない（浅い clone）", 2, "v1 が凍結しているかを判定していない",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=shallow_release),
    # 陽性対照: 凍結していても、前の版が崩れていなければ今までどおり変わった機能だけ
    Case("凍結した前の版が崩れていない", 0, "modify 1", extra=v2([V2_CHANGED]), pre=release(),
         post=lambda repo: None if list(bodies(repo)) == ["F-001"] else f"本文は変えた機能だけのはず: {list(bodies(repo))}",
         absent="凍結していて"),
    # 前の版でも Q&A の実在は見る
    Case("前の版の Q&A が表に無い", 1, "v1 の時点の F-001.qa: Q-009 は Q&A 表に無い", ir=MISSING_QA_V1,
         extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), pre=plant_old_issues, post=nothing_written_issues),
    # 陽性対照: v2 で直さなければ、今の版の誤りとして止まる
    Case("前の版のパスの変数を直さない", 1, "パスの変数 {order_id} が operation.input の項目に無い", ir=OLD_PATH_V1,
         extra=v2([]), pre=plant_old_issues, post=nothing_written_issues),
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
    # ---- --red-check（判定の決まりは scaffold.py の docstring を正とする。#294）
    Case("Red の状態: v1 で実装なし", 0, "失敗 3 件", args=("--red-check",), generate_first=True),
    # v1 には前の版の Red テストが無い——実装がもう満たすケースは「もう緑」として知らせる（#294。前は 1）
    Case("Red の状態: v1 で実装がある", 0, "もう緑 3 件", args=("--red-check",), generate_first=True, impl=GOOD_IMPL),
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
    # ---- 実装の状態（#294）
    # #281: 前の版の実装がもう満たす追加・変更は止めず、名指しで知らせる
    Case("Red の状態: 既存の振る舞いのケースを足す", 0, "もう緑: test_f_001.TestF001.test_f_001_c3", args=("--red-check",),
         generate_first=True, extra=v2([V2_SAME_ADDED]), impl=GOOD_IMPL),
    Case("Red の状態: 入力だけ変える", 0, "失敗 0 件（追加・変更）・緑 2 件（回帰）・もう緑 1 件", args=("--red-check",),
         generate_first=True, extra=v2([V2_INPUT_ONLY]), impl=GOOD_IMPL),
    Case("Red の状態: 型を狭めて整数を返す", 0, "もう緑: test_f_001.TestF001.test_f_001_c1", args=("--red-check",),
         generate_first=True, ir=V1_NUMBER, extra=v2([IR["features"][0]]), impl=GOOD_IMPL),
    # 陽性対照: 型を狭めて小数を返す実装は、変更のケースで失敗する（前の版の number では緑）
    Case("Red の状態: 型を狭めて小数を返す", 0, "失敗 1 件（追加・変更）", args=("--red-check",),
         generate_first=True, ir=V1_NUMBER, extra=v2([IR["features"][0]]),
         impl=GOOD_IMPL.replace('{"discount": 0}', '{"discount": 0.0}')),
    # B: 前の版の期待を満たさず、作業中の版の期待を満たす——実装は前の版の状態に無い
    Case("Red の状態: 変更をもう実装した", 1, "実装は前の版の状態に無い", args=("--red-check",), generate_first=True,
         extra=v2([V2_CHANGED]), impl=V2_IMPL),
    Case("Red の状態: どちらの版の期待も満たさない", 1, "作業中の版の期待も満たさない（前の版の仕様とも食い違う）",
         args=("--red-check",), generate_first=True, extra=v2([V2_CHANGED]), impl=NEITHER_IMPL),
    # 作り直しでは、作りかけの実装の誤りを先に挙げる（#300）
    Case("Red の状態: どちらの版の期待も満たさない（作り直し）", 1, "（作りかけの実装の誤りか、前の版の仕様とも食い違う）",
         args=("--red-check", "--in-progress"), generate_first=True, extra=v2([V2_CHANGED]), impl=NEITHER_IMPL),
    # #282: 作り直しの経路
    Case("Red の状態: 作り直し（変更を実装済み）", 0, "実装済み 1 件", args=("--red-check", "--in-progress"),
         generate_first=True, extra=v2([V2_CHANGED]), impl=V2_IMPL),
    # 実装が全く無く、回帰のケースも無い——前の版のテストも「実装が無い」で、食い違いではない（#294 の 1 パス目）
    Case("Red の状態: 実装が無く、変更のケースだけ", 0, "失敗 1 件（追加・変更）", args=("--red-check",),
         generate_first=True, ir=lambda ir: {**ir, "features": [copy.deepcopy(ir["features"][0])]},
         extra=v2([{**V2_CHANGED, "cases": V2_CHANGED["cases"][:1]}]), impl=""),
    # 入力の改名を実装済み——前の版の Red テストはエラーになるが、作業中の版のテストが緑なら「前の版で失敗」と同じ
    Case("Red の状態: 作り直し（入力の改名を実装済み）", 0, "実装済み 2 件", args=("--red-check", "--in-progress"),
         generate_first=True, extra=v2([V2_RENAMED]), impl=RENAMED_IMPL),
    Case("Red の状態: 入力の改名をもう実装した", 1, "実装は前の版の状態に無い", args=("--red-check",),
         generate_first=True, extra=v2([V2_RENAMED]), impl=RENAMED_IMPL),
    # 陽性対照: 改名は実装したが値はどちらの版でもない——前の版のエラーを緑の代わりにしない
    Case("Red の状態: 入力の改名と、どちらの版でもない値", 1, "前の版の状態を判定できない",
         args=("--red-check", "--in-progress"), generate_first=True, extra=v2([V2_RENAMED]), impl=RENAMED_NEITHER_IMPL),
    # 入力の名前・形を変える変更で、実装は前の版の状態——作業中の版の Red テストはエラーになるが、Red の正常な状態（2 パス目）
    Case("Red の状態: 入力を改名する（前の版の実装）", 0, "失敗 2 件（追加・変更）・緑 1 件（回帰）", args=("--red-check",),
         generate_first=True, extra=v2([V2_RENAMED]), impl=GOOD_IMPL),
    Case("Red の状態: 必須の入力を足す（前の版の実装）", 0, "失敗 2 件（追加・変更）・緑 1 件（回帰）", args=("--red-check",),
         generate_first=True, extra=v2([V2_NEW_INPUT]), impl=GOOD_IMPL),
    # 陽性対照: 前の版でも失敗する実装なら、作業中の版のエラーを失敗の代わりにしない
    Case("Red の状態: 必須の入力を足し、前の版でも失敗する実装", 1, "エラー（失敗でも緑でもない）", args=("--red-check",),
         generate_first=True, extra=v2([V2_NEW_INPUT]), impl=NEITHER_IMPL),
    # 関数の改名: 前の版の Red テストだけが「未実装」——新しい関数がどちらの版も満たさなければ 1（2 パス目）
    Case("Red の状態: 関数を改名し、どちらの版でもない値", 1, "前の版の期待も作業中の版の期待も満たさない",
         args=("--red-check",), generate_first=True, extra=v2([V2_OP_RENAMED]), impl=OP_RENAMED_NEITHER_IMPL),
    # 関数の改名: 作業中の版のテストが「未実装」、旧名の実装は前の版でも失敗する——どちらの版も満たさないので 1（#298）
    Case("Red の状態: 関数を改名し、旧名だけ誤った値で残す", 1, "前の版の期待も作業中の版の期待も満たさない",
         args=("--red-check",), generate_first=True, extra=v2([V2_OP_RENAMED]), impl=NEITHER_IMPL),
    # 関数の改名も、作り直しでは作りかけの実装の誤りを先に挙げる（#300 の 1 パス目）
    Case("Red の状態: 関数を改名し、どちらの版でもない値（作り直し）", 1, "（作りかけの実装の誤りか、前の版の仕様とも食い違う）",
         args=("--red-check", "--in-progress"), generate_first=True, extra=v2([V2_OP_RENAMED]),
         impl=OP_RENAMED_NEITHER_IMPL),
    Case("Red の状態: 関数を改名する（前の版の実装）", 0, "失敗 2 件（追加・変更）・緑 1 件（回帰）", args=("--red-check",),
         generate_first=True, extra=v2([V2_OP_RENAMED]), impl=GOOD_IMPL),
    Case("Red の状態: 作り直し（v1 を実装済み）", 0, "もう緑 3 件", args=("--red-check", "--in-progress"),
         generate_first=True, impl=GOOD_IMPL),
    Case("Red の状態: 作り直し（回帰が壊れた実装）", 1, "回帰のケースなのに失敗した", args=("--red-check", "--in-progress"),
         generate_first=True, extra=v2([V2_CHANGED]), impl=WRONG_IMPL),
    Case("--in-progress だけ", 2, "--in-progress は --red-check と一緒にだけ使う", args=("--in-progress",),
         pre=plant_old_issues, post=old_issues_kept),
    Case("--check に --in-progress", 2, "--in-progress は --red-check と一緒にだけ使う", args=("--check", "--in-progress"),
         generate_first=True),
    # #280: 撤去と追加が同じ版にある
    Case("撤去の受入基準は前後を比べる", 0, "remove 1", extra=v2([V2_RETURN], removed="機能,F-002,取り消しはやめる\n"),
         impl=GOOD_IMPL, post=removal_before_after),
    Case("Red の状態: 撤去と追加（前の版の実装）", 0, "失敗 1 件（追加・変更）・緑 2 件（回帰）", args=("--red-check",),
         generate_first=True, extra=v2([V2_RETURN], removed="機能,F-002,取り消しはやめる\n"), impl=GOOD_IMPL,
         post=red_check_wrote_nothing),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("ケースの ref を見ない", '            if "ref" in case:\n                problems += check_ref',
     '            if False:\n                problems += check_ref', "ケースの ref が仕様に無い"),
    ("ref の部分一致を許す", 'pattern = re.compile(rf"(?<![A-Za-z0-9_\\-Ａ-Ｚａ-ｚ０-９]){sub}{re.escape(ref)}(?![A-Za-z0-9_\\-Ａ-Ｚａ-ｚ０-９]|[./:][0-9])")',
     'pattern = re.compile(re.escape(ref))', "ケースの ref が別の番号の一部にしか無い"),
    ("ref の前の英数字を許す", 'pattern = re.compile(rf"(?<![A-Za-z0-9_\\-Ａ-Ｚａ-ｚ０-９]){sub}', 'pattern = re.compile(rf"{sub}',
     "ケースの ref が別の番号の後ろの一部にしか無い"),
    ("ref の後ろの全角の英数字を許す", '(?![A-Za-z0-9_\\-Ａ-Ｚａ-ｚ０-９]|[./:][0-9])', '(?![A-Za-z0-9_\\-]|[./:][0-9])',
     "ケースの ref が別の番号の一部にしか無い"),
    ("数字の ref の前の小番号を許す", '    sub = r"(?<![A-Za-z0-9Ａ-Ｚａ-ｚ０-９][./:])" if ref[:1].isdigit() else ""', '    sub = ""',
     "数字の ref が小番号にしか無い"),
    ("前の区切りを英字で始まる ref にも当てる", 'if ref[:1].isdigit() else ""', 'if True else ""', "区切りの後ろの ref は在ることにする"),
    ("区切りの後ろの英字も別の番号とみなす", '|[./:][0-9])")', '|[./:][A-Za-z0-9])")', "拡張子の付いた ref は在ることにする"),
    ("ref の空を許す", "    if not isinstance(ref, str) or not one_line(ref) or ref != ref.strip():", "    if not isinstance(ref, str):",
     "ケースの ref が空"),
    ("ref の前後の空白を許す", " or ref != ref.strip():", ":", "ケースの ref の後ろに空白"),
    ("ref の複数行を許す", "    if not isinstance(ref, str) or not one_line(ref) or", "    if not isinstance(ref, str) or not ref or",
     "ケースの ref が複数行"),
    ("ref を仕様の外でも探す", "        if not path.is_relative_to(spec_root):\n            continue\n", "",
     "ケースの ref を仕様の外のファイルで探さない"),
    ("ref の後ろの小番号を別の番号とみなさない", "Ａ-Ｚａ-ｚ０-９]|[./:][0-9])", "Ａ-Ｚａ-ｚ０-９])",
     "ケースの ref が別の番号の一部にしか無い"),
    ("ref を在れば通す", "                return []\n        except (OSError, UnicodeDecodeError, ValueError):", "                pass\n        except (OSError, UnicodeDecodeError, ValueError):",
     "ケースの ref が仕様に在る"),
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
    ("暫定の行を見ない", "            if held:", "            if False:", "暫定反映の Q&A を指さない"),
    ("内部の表を読まない", "        for path in (QA_PATH, INTERNAL_QA_PATH):", "        for path in (QA_PATH,):", "内部の Q&A を指す"),
    ("D- の番号を指せない", "(qa.NUMBER.fullmatch(no) or qa.is_internal_number(no))", "qa.NUMBER.fullmatch(no)",
     "内部の Q&A を指す"),
    ("番号の形を見ない", "(qa.NUMBER.fullmatch(no) or qa.is_internal_number(no))", "True", "印の形に反する番号を指す"),
    ("写した元に内部の表を挙げない", "(QA_PATH, *([INTERNAL_QA_PATH] if any(", "(QA_PATH, *([] if any(", "内部の Q&A を指す"),
    # 層の判定（`check-qa-csv.py` の `is_internal_number`）を入れ替える（#353）
    ("写した元の層を入れ替える", "if any(qa.is_internal_number(no) for no in refs)",
     "if not any(qa.is_internal_number(no) for no in refs)", "内部の Q&A を指す"),
    ("写した元の層を見ない（常に内部の表を挙げる）", "if any(qa.is_internal_number(no) for no in refs)", "if True",
     "内部の Q&A を指す"),
    ("写した元の層を全部の行で見る", "if any(qa.is_internal_number(no) for no in refs)",
     "if all(qa.is_internal_number(no) for no in refs)", "内部の Q&A を指す"),
    # 2 パス目の前の形（中間表現が指す行だけ見る）に戻す——指さない暫定の行が止まらず 0 になる
    ("中間表現が指す暫定の行だけ見る",
     '            held = [no for no, row in answered.items() if qa.is_provisional(row)]',
     '            held = [no for no, row in answered.items() if qa.is_provisional(row)\n'
     '                    and any(no in f.get("qa", []) for f in ir.get("features", []))]',
     "暫定反映の Q&A を指さない"),
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
    ("巨大なセルの予期しない失敗を捕まえない", "    except Exception as exc:  # 予期しない失敗",
     "    except ZeroDivisionError as exc:  # 予期しない失敗", "巨大なセル"),
    ("メソッドが決まりに無くても入口の重複を見る", "                elif method in METHODS and (method, path) in routes:",
     "                elif (method, path) in routes:", "メソッドが配列"),
    # パスの変数（#289）
    ("パスの変数をクエリで宣言する", 'parameters = [{"name": name, "in": "path"', 'parameters = [{"name": name, "in": "query"',
     "パスの変数"),
    ("パスの変数を宣言しない", "                      for name in in_path]", "                      for name in []]", "パスの変数"),
    ("パスの変数を必須にしない", '"in": "path", "required": True', '"in": "path", "required": False', "パスの変数"),
    ("パスの変数をクエリ・ボディに重ねる",
     '        rest = {name: op["input"][name] for name in op["input"] if name not in in_path}',
     '        rest = dict(op["input"])', "パスの変数"),
    ("パスの変数を持たない入口もボディの型を指す",
     '            body = f"{base}Input" if not in_path else f"{base}Body"\n            if in_path:',
     '            body = f"{base}Body"\n            if True:', "OpenAPI と型"),
    ("ボディを持つ入口にも空の parameters を足す", '        if parameters or op["method"] in NO_BODY:', "        if True:",
     "OpenAPI と型"),
    ("パスの変数を入力と突き合わせない", "        if name not in fields:", "        if False:", "パスの変数が入力に無い"),
    ("波括弧の対を見ない", '    if "{" in PATH_VAR.sub("", path) or "}" in PATH_VAR.sub("", path):', "    if False:",
     "波括弧が対でない"),
    ("閉じ括弧だけを見ない", ' or "}" in PATH_VAR.sub("", path):', ":", "閉じ括弧だけ"),
    ("パスの変数の重複を見ない", "        if names.count(name) > 1:", "        if False:", "パスの変数の重複"),
    ("変数の名前だけが違うパスを見ない", "    if templates.setdefault(template, path) != path:", "    if False:",
     "変数の名前だけが違うパス"),
    # 入口の型の整合（#318）
    ("path パラメータの schema を固定する", '"required": True, "schema": schema_of(op["input"][name])}',
     '"required": True, "schema": {"type": "string"}}', "パスの変数"),
    ("入力の型をボディの項目に縮める", "                schemas[body] = object_schema(rest)",
     '                schemas[body] = object_schema(rest)\n                schemas[f"{base}Input"] = object_schema(rest)',
     "パスの変数"),
    ("ボディの型の項目を必須にしない", "                schemas[body] = object_schema(rest)",
     '                schemas[body] = dict(object_schema(rest), required=[])', "パスの変数"),
    ("クエリを必須にしない", '"in": "query", "required": True', '"in": "query", "required": False', "パスの変数"),
    # Input・パラメータ・ボディから同じ項目が一緒に落ちる——OpenAPI の中だけで比べると見えない
    ("OpenAPI から入力の項目を落とす",
     '        op = feature["operation"]\n        base = pascal(op["id"])\n        schemas[f"{base}Input"]',
     '        op = dict(feature["operation"], input={k: v for k, v in feature["operation"]["input"].items()'
     ' if k != "amount"})\n        base = pascal(op["id"])\n        schemas[f"{base}Input"]', "OpenAPI と型"),
    ("OpenAPI の schema から enum を落とす", '        out["enum"] = field["enum"]', "        pass", "パスの変数"),
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
    ("中間表現の指紋を取らない",
     "            f\"- 中間表現: `{merged(IR_PATH)}` の `{feature['id']}`（機能の指紋: `{fingerprint(feature)}`）\",",
     "            f\"- 中間表現: `{merged(IR_PATH)}` の `{feature['id']}`（機能の指紋: `{sha256(b'')}`）\",", "本文から辿れる"),
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
     'command = f"merge-versions.py {DOCS} {MERGED_DIR}"', "v3 を足しても本文の指紋が合う"),
    # ---- 機能の指紋（#290）
    ("全体の sha256 を本文に書く（#290 の前）",
     "            f\"- 中間表現: `{merged(IR_PATH)}` の `{feature['id']}`（機能の指紋: `{fingerprint(feature)}`）\",",
     "            f\"- 中間表現: `{merged(IR_PATH)}` の `{feature['id']}`（機能の指紋: `{sha256(loaded.raw)}`）\",",
     "関係の無い機能を直しても指紋は変わらない"),
    ("指紋の式を dev-loop の写しとずらす", 'separators=(",", ":")))', 'separators=(", ", ":")))', "本文から辿れる"),
    ("撤去の仕様の原文を前の版の全体の外で書く（#290 の前）", '"・".join(f"`{old_dir}/{s}`" for s in feature["source"])',
     '"・".join(f"`{s}`" for s in feature["source"])', "v2 で機能を消す"),
    ("撤去の前の版の全体を作業中の版で作る", 'old_command = f"merge-versions.py {DOCS} {old_dir} --upto {number - 1}"',
     'old_command = f"merge-versions.py {DOCS} {old_dir} --upto {number}"', "v2 で機能を消す"),
    # 検査だけ飛ばし、中間表現は返す形にする——`if code:` を潰すと None を読んで落ち、意味ではなく例外で殺される
    ("前の版の中間表現を検査しない", "        problems = check_ir(ir, whole, answered, path_rules=gate)\n",
     "        problems = check_ir(ir, whole, answered, path_rules=gate) if gate else []\n", "前の版の中間表現が決まりに反する"),
    ("前の版にもパスの変数の決まりを当てる", "check_ir(ir, whole, answered, path_rules=gate)",
     "check_ir(ir, whole, answered, path_rules=True)", "前の版だけパスの変数が入力に無い"),
    ("今の版にもパスの変数の決まりを当てない", "check_ir(ir, whole, answered, path_rules=gate)",
     "check_ir(ir, whole, answered, path_rules=False)", "前の版のパスの変数を直さない"),
    # #361: 前の版の Q&A の状態を直接見る（#358）・名指し（#335）・凍結した前の版（#357）
    ("前の版の Q&A の状態を見ない", "    unsettled = unsettled_qa(rendered)\n", "    unsettled = []\n",
     "前の版に指していない暫定反映の行がある"),
    ("前の版の暫定反映だけを見る", 'if row["状態"].strip() != qa.DONE]', 'if row["状態"].strip() == qa.PROVISIONAL]',
     "前の版に指していない確認中の行がある"),
    ("前の版の内部の表を見ない", "    for path in (QA_PATH, INTERNAL_QA_PATH):\n        if path in rendered:",
     "    for path in (QA_PATH,):\n        if path in rendered:", "前の版の内部の表に確認中の行がある"),
    ("前の版の確認中なら名指ししない", "    if unsettled:\n", "    if any(s == qa.PROVISIONAL for _, s in unsettled):\n",
     "前の版で確認中だった Q&A（名指し）"),
    ("名指しで今の版を確かめさせる", "`--check --upto {number - 1}` が 0 にならない", "`--check --upto {number}` が 0 にならない",
     "前の版で暫定だった Q&A を後の版で確定する"),
    ("凍結を見ない（いつも止める）", "        tag, edited = released(loaded.docs.parent, number - 1)\n", "        tag, edited = None, []\n",
     "凍結した前の版が崩れている"),
    ("凍結していなくても止めない", "        tag, edited = released(loaded.docs.parent, number - 1)\n", '        tag, edited = "release-v0", []\n',
     "前の版に指していない暫定反映の行がある"),
    ("凍結した前の版で全部を追加にしない", "return 0, out, [Change(ADD, f) for _, f in sorted(now.items())], distrusted",
     "return 0, out, [], distrusted", "凍結した前の版が崩れている"),
    ("凍結した前の版で撤去を名指ししない", "        if dropped:\n", "        if False:\n",
     "凍結した前の版が崩れている（撤去を名指し）"),
    ("凍結しても崩れていない前の版は信じる（崩れていなくても全部を追加にする）", "    if unsettled:\n",
     "    if unsettled or released(loaded.docs.parent, number - 1)[0]:\n", "凍結した前の版が崩れていない"),
    ("親のリポジトリのタグを読む", "Path(top.stdout.strip()).resolve() != repo.resolve()", "False",
     "親のリポジトリのタグで凍結と読まない"),
    ("浅い clone を見ない", 'shallow.stdout.strip() != "false"', "False", "凍結を判定できない（浅い clone）"),
    # 1 パス目の指摘対応（P1-1・P1-2・P1-4・P1-6・P1-9）
    ("凍結のタグの時点と比べない", "    code, lines = frozen.check(repo, only=number)\n", "    code, lines = 0, []\n",
     "凍結した前の版がタグの後に直されている"),
    # 2 パス目の指摘対応（P2-1）
    ("凍結の確かめを前の版に絞らない（直された他の版）", "frozen.check(repo, only=number)", "frozen.check(repo)",
     "他の版のタグの後の直しで止めない"),
    ("凍結の確かめを前の版に絞らない（版の無い他のタグ）", "frozen.check(repo, only=number)", "frozen.check(repo)",
     "他の版のタグの時点に版が無くても判定する"),
    ("タグの時点に版が無くても凍結と読む", "    if code == 2:\n        raise Unjudged(", "    if False:\n        raise Unjudged(",
     "凍結のタグの時点に前の版が無い"),
    ("凍結した版が直されていても止めない", "        if edited:\n", "        if False:\n",
     "凍結した前の版がタグの後に直されている"),
    ("別の版のタグでも凍結と読む", "if n == number), None)", "if True), None)", "別の版のタグで凍結と読まない"),
    ("git を起動できないのを判定していないと言わない", "        except OSError as exc:\n            raise Unjudged(f\"git を起動できない",
     "        except ValueError as exc:\n            raise Unjudged(f\"git を起動できない", "凍結を判定できない（git を起動できない）"),
    ("凍結の経路でも変わっていない機能を省いたと言う", "if loaded.number > 1 and before.trusted else",
     "if loaded.number > 1 else", "凍結した前の版が崩れている"),
    # `check_qa_refs` の状態の行（`は状態が {state}`）は、今の版では関門が、前の版では `unsettled_qa` が先に止めるので
    # 届かない——変異を入れても殺せない（等価変異）。守りとして残すが変異には入れない（#361）
    ("期待に無い項目の型も見る", "not in WIDENED for name in expected)", "not in WIDENED for name in now)",
     "Red の状態: v2 で出力の項目を足す"),
    ("型を広げたのを変化に数える", 'WIDENED = {("integer", "number")}', "WIDENED = set()", "Red の状態: v2 で型を広げる"),
    ("impl_module の変化を見ない", "    if before.impl_module != loaded.ir.get(", "    if False and before.impl_module != loaded.ir.get(",
     "v2 で impl_module だけ変える"),
    ("--upto で書くのを断らない", "        if not (args.check or args.dry_run):\n", "        if False:\n", "--upto で書く"),
    ("--upto を渡さない", "load(repo, args.upto)", "load(repo)", "前の版の時点の --check"),
    ("回帰の失敗を見ない", '            if got != "pass":\n                problems.append(f"{name}: {CASE_KEPT}',
     '            if False:\n                problems.append(f"{name}: {CASE_KEPT}', "Red の状態: 回帰が壊れた実装"),
    # ---- 実装の状態（#294）
    ("前の版の Red テストを当てない", "        previous = previous_outcomes(repo, before)", "        previous = {}",
     "Red の状態: 変更をもう実装した"),
    ("--in-progress を無視する", "        elif in_progress:", "        elif False:", "Red の状態: 作り直し（変更を実装済み）"),
    ("もう緑を止める（#294 の前）", '        elif was in (None, "pass"):\n            satisfied.append(name)',
     '        elif False:\n            satisfied.append(name)', "Red の状態: 既存の振る舞いのケースを足す"),
    ("どちらの版でも失敗を見ない", '        elif got != "pass" and was not in (None, "pass") and (got, was)', "        elif False and (got, was)",
     "Red の状態: どちらの版の期待も満たさない"),
    ("作り直しでは、どちらの版でも失敗を見ない", '        elif got != "pass" and was not in (None, "pass") and (got, was)',
     '        elif not in_progress and got != "pass" and was not in (None, "pass") and (got, was)',
     "Red の状態: どちらの版の期待も満たさない（作り直し）"),
    ("作り直しでも乖離だけを挙げる（#300 の前）", 'if in_progress\n                               else', 'if False\n                               else',
     "Red の状態: どちらの版の期待も満たさない（作り直し）"),
    ("既定の経路でも作りかけの実装を挙げる", 'if in_progress\n                               else', 'if True\n                               else',
     "Red の状態: どちらの版の期待も満たさない"),
    ("前の版の「実装が無い」を食い違いに数える", ' and (got, was) != ("missing", "missing"):', ":",
     "Red の状態: 実装が無く、変更のケースだけ"),
    ("前の版だけの「未実装」を食い違いに数えない（2 パス目の前）", 'was not in (None, "pass") and (got, was) != ("missing", "missing"):',
     'was not in (None, "pass", "missing"):', "Red の状態: 関数を改名し、どちらの版でもない値"),
    ("作業中の版の「未実装」を食い違いに数えない（#298 の前）", ' and (got, was) != ("missing", "missing"):',
     ' and got != "missing":', "Red の状態: 関数を改名し、旧名だけ誤った値で残す"),
    ("作業中の版のエラーを一律に止める（2 パス目の前）", '            if got == "error" and was == "pass":\n                got = "fail"',
     '            if False:\n                got = "fail"', "Red の状態: 入力を改名する（前の版の実装）"),
    ("作業中の版のエラーを失敗の代わりにする", '            if got == "error" and was == "pass":\n                got = "fail"',
     '            if got == "error":\n                got = "fail"', "Red の状態: 必須の入力を足し、前の版でも失敗する実装"),
    ("バイトコードを書く", '[sys.executable, "-B", "-c", DRIVER', '[sys.executable, "-c", DRIVER',
     "Red の状態: 撤去と追加（前の版の実装）"),
    ("前の版のエラーを一律に止める", '            elif was == "error" and got == "pass":\n                was = "fail"',
     '            elif False:\n                was = "fail"', "Red の状態: 作り直し（入力の改名を実装済み）"),
    ("前の版のエラーを緑の代わりにする", '            elif was == "error" and got == "pass":\n                was = "fail"',
     '            elif was == "error":\n                was = "pass"', "Red の状態: 入力の改名と、どちらの版でもない値"),
    ("--in-progress を --red-check 以外でも受け付ける", "    if args.in_progress and not args.red_check:", "    if False:",
     "--check に --in-progress"),
    ("撤去の受入基準を全部緑に戻す（#294 の前）", "を撤去し、{KEPT_GREEN}。**", "を撤去し、ほかの Red テストがすべて緑のままであること。**",
     "撤去の受入基準は前後を比べる"),
    ("変更の受入基準を全部緑に戻す（#294 の前）", "**ほかの機能は、{KEPT_GREEN}**",
     "**ほかの機能の Red テストも緑のままであること。**", "v2 で機能を変える"),
    ("前の版の Red テストを scaffold/tests に置く", '        tests = Path(tmp) / "tests"',
     '        tests = repo / OUT_DIR / "tests"', "Red の状態: 撤去と追加（前の版の実装）"),
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
    proc = subprocess.run(command + list(case.args), capture_output=True, text=True,
                          env={**os.environ, **case.env} if case.env else None)
    out = proc.stdout + proc.stderr
    if proc.returncode != case.code:
        return False, f"exit={proc.returncode}（期待 {case.code}）{out[-400:]}"
    if case.text and case.text not in out:
        return False, f"出力に {case.text!r} が無い: {out[-400:]}"
    if case.absent and case.absent in out:
        return False, f"出力に {case.absent!r} がある: {out[-400:]}"
    if case.post:
        problem = case.post(repo)
        if problem:
            return False, problem
    # 作った OpenAPI はどの試料でもパスの変数を宣言し（#289）、パラメータとボディで入力の型を復元できる（#318）。
    # post を持たない試料にも当てる
    openapi = repo / "scaffold" / "openapi.json"
    if case.code == 0 and openapi.is_file():
        doc = json.loads(openapi.read_text(encoding="utf-8"))
        types = (repo / "scaffold" / "types.py").read_text(encoding="utf-8")
        problem = path_params_problem(doc) or input_split_problem(doc, types)
        if problem:
            return False, problem
    return True, ""


def table_cells(markdown: str, heading: str) -> list[str]:
    section = markdown.split(heading, 1)[1].split("\n#", 1)[0]
    return re.findall(r"^\| `([^`]+)` \|", section, flags=re.MULTILINE)


def constant(source: str, name: str):
    found = re.search(rf"^{name} = (.+)$", source, flags=re.MULTILINE)
    return ast.literal_eval(found.group(1)) if found else None


# 入口の捕捉（#286）。`argparse` の解釈で ValueError を投げさせ、`__main__` から走らせる
ENTRY_GUARD = "    except Exception as e:  # 想定外の例外も「判定していない」（2）"
UNEXPECTED_RUNNER = """
import argparse, runpy, sys
def parse_args(self, *args, **kwargs):
    raise ValueError("試料")
argparse.ArgumentParser.parse_args = parse_args
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def entry_caught(script: Path, cwd: Path) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-I", "-c", UNEXPECTED_RUNNER, str(script)], capture_output=True, text=True, cwd=cwd)
    output = proc.stdout + proc.stderr
    return (proc.returncode == 2 and "想定外の例外で止まった（ValueError: 試料）" in output and "Traceback" not in output), output


CHECKER = "check-qa-csv.py"
CHECKER_MUTATIONS: list[tuple[str, str, str, str]] = [
    ("判別の本体で暫定を見ない", 'return row["状態"].strip() == PROVISIONAL', "return False", "暫定反映の Q&A を指さない"),
    ("判別の本体を文言の一致に戻す", 'return row["状態"].strip() == PROVISIONAL',
     'return row["状態"].strip() == PROVISIONAL or (row["状態"].strip() == DONE and "暫定で採用" in row["回答"])',
     "文言だけ暫定の反映済みは止めない"),
]


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
        # dev-loop は今の形（v3）も、登録済みの前の形（v2・v1）も読む
        for current in (marker, *LEGACY_MARKERS):
            check(f"dev-loop の references/spec-gap.md に印 {current} が無い", current is not None and current in gap)
            check(f"dev-loop の SKILL.md に印 {current} が無い（手順 1 が spec-loop の Issue に気づかない）",
                  current is not None and current in skill)
        check("dev-loop の references/spec-gap.md に変化の印が無い",
              change_marker is not None and change_marker.split("{}")[0] in gap)
        # 陽性対照: 印を上げたら、`SKILL.md` に残った古い印では当たらない
        check("印の版を変えても SKILL.md の照合が不一致にならない",
              marker is not None and marker.replace("v3", "v4") not in skill)
        gap_sections = table_cells(gap, "## spec-loop から来た Issue を読む")
        check("dev-loop の references/spec-gap.md の節の表が handoff-issue.md と違う", gap_sections == sections,
              f"{gap_sections} vs {sections}")
        # 実装の状態についての前提（#294）——3 つの文書が定数の文言をそのまま持つ
        scaffold_skill = SCAFFOLD_SKILL.read_text(encoding="utf-8")
        for const in ("PREMISE", "KEPT_GREEN"):
            text = constant(source, const)
            check(f"{const} を本体から読めない", isinstance(text, str) and len(text) > 10, f"{text!r}")
            for label, doc in (("scaffold の SKILL.md", scaffold_skill), ("handoff-issue.md", handoff),
                               ("dev-loop の references/spec-gap.md", gap)):
                check(f"{label} に {const} の文言が無い", isinstance(text, str) and text in doc, f"{text!r}")
        # 前の版の時点が崩れていたときの手当ての指し先（#361）——versions.md にその見出しがある
        remedy_ref = constant(source, "BROKEN_REMEDY")
        versions_ref = VERSIONS_REF.read_text(encoding="utf-8")
        remedy_heading = re.fullmatch(r"references/versions\.md の「(.+)」", remedy_ref or "")
        check("BROKEN_REMEDY が references/versions.md の見出しを指していない",
              remedy_heading is not None and f"\n### {remedy_heading.group(1)}\n" in versions_ref, f"{remedy_ref!r}")
        check("見出しを改名しても BROKEN_REMEDY の照合が不一致にならない（照合が壊れている）",
              remedy_heading is not None
              and f"\n### {remedy_heading.group(1)}\n" not in versions_ref.replace(remedy_heading.group(1), "前の版を直す"))
        # 突き合わせ自体の陽性対照
        broken = handoff.replace("| `## Red テスト` |", "| `## 赤のテスト` |")
        check("handoff-issue.md の写しを崩しても不一致にならない", table_cells(broken, "## 節") != sections)

        # 変異テスト
        by_name = {case.name: case for case in CASES}
        # 指紋の式の写しの、dev-loop の側だけを崩す（F。scaffold 側の変異は MUTATIONS にある）——
        # 本文の指紋は dev-loop のスクリプトで照合しているので、こちらだけ変えても落ちること
        global DEV_FINGERPRINT
        dev_source = DEV_FINGERPRINT.read_text(encoding="utf-8")
        dev_mutations = (
            ("dev-loop の指紋の式をずらす", 'separators=(",", ":"))', 'separators=(", ", ":"))', "本文から辿れる"),
            # 読み損ねを「無い」と答えると、撤去の不在の確認が素通りする（2 パス目 CR2-3）
            ("dev-loop のスクリプトが読めない中間表現に 3 を返す",
             '読めない: {error}", file=sys.stderr)\n        return 2', '読めない: {error}", file=sys.stderr)\n        return 3',
             "v2 で機能を消す"),
        )
        for index, (name, before, after, killer) in enumerate(dev_mutations):
            count = dev_source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated_dev = tmp_path / f"mutdev{index}" / "spec-fingerprint.py"
            assert_in_tmp(mutated_dev)
            mutated_dev.parent.mkdir()
            mutated_dev.write_text(dev_source.replace(before, after), encoding="utf-8")
            real_dev, DEV_FINGERPRINT = DEV_FINGERPRINT, mutated_dev
            try:
                ok, detail = run_case(scripts, tmp_path / f"mutdevwork{index}", by_name[killer])
            finally:
                DEV_FINGERPRINT = real_dev
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not ok, detail)
        # 判別の本体（`check-qa-csv.py` の `is_provisional`）を壊す——scaffold は写しを持たずにそれを読む（#404）
        checker = (SCRIPTS / CHECKER).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(CHECKER_MUTATIONS):
            count = checker.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"checker-mut{index}")
            (mutated / CHECKER).write_text(checker.replace(before, after), encoding="utf-8")
            ok, detail = run_case(mutated, tmp_path / f"checker-mutwork{index}", by_name[killer])
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not ok, detail)
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}", source.replace(before, after))
            ok, detail = run_case(mutated, tmp_path / f"mutwork{index}", by_name[killer])
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not ok, detail)

        # -OO（docstring が無い）で引数なしに呼んでも、想定外の例外にもトレースバックにもならない（#286）。
        # 引数なしは今のディレクトリを正本として読むので、空のディレクトリでは docs/ が無くて 2
        (tmp_path / "oo").mkdir()
        proc = subprocess.run([sys.executable, "-I", "-OO", str(SCRIPTS / TARGET)], capture_output=True, text=True,
                              cwd=tmp_path / "oo")
        output = proc.stdout + proc.stderr
        check("-OO の引数なしで 2 にならない", proc.returncode == 2 and "予期しない失敗" not in output
              and "想定外の例外" not in output and "Traceback" not in output, output[-300:])
        # 予期しない失敗は `run` の中なら本体が捕まえる。その外（引数の解釈）で上がった例外も入口が 2 にする（#286）
        caught, output = entry_caught(SCRIPTS / TARGET, tmp_path / "oo")
        check("引数の解釈で上がった想定外の例外を入口が 2 にしない", caught, output[-300:])
        if source.count(ENTRY_GUARD) != 1:
            check("変異が届いていない: 入口で想定外の例外を 2 に寄せない", False, f"壊す箇所が {source.count(ENTRY_GUARD)} 回現れる")
        else:
            mutated = copy_scripts(tmp_path / "entry-mut", source.replace(ENTRY_GUARD, ENTRY_GUARD.replace("Exception", "ImportError")))
            caught, output = entry_caught(mutated / TARGET, tmp_path / "oo")
            check("変異が生き残った: 入口で想定外の例外を 2 に寄せない", not caught, output[-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(CHECKER_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
