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
   **作らないもの**（#851。中間表現の `out_of_scope` に挙げた範囲の外の行が原文のまま・表の見出しつき・範囲の文書の順で写り、
   「次の版の候補」を含む行は別の小見出しに分かれ、挙げていない行は写らない。行の無い機能でも節と「無い」の文言と性能予算の「要求なし」が出る。
   `out_of_scope` が範囲の文書の「範囲の外」の節に原文のまま無い・形が決まりに反するなら作らない）・
   **性能の要求**（#852。中間表現の `nfr` が指す `shared/nfr.csv` の行の数字が性能予算に写り、性能テスト `scaffold/perf/perf_<機能>.py` が作られ、
   本文がその sha256 と回し方を持つ。性能テストは実装が無ければ「未実装」で失敗し、上限を超える遅い実装で失敗し、速い実装で緑（陽性対照）。
   `nfr` の無い機能は「要求なし」で性能テストを作らない。`nfr` を外せば性能テストを消し、`--check` が残りを古いと言う。
   `nfr` や指した行が決まりに反するなら作らない。性能でない行を指さなければ止めない）・
   **課題一覧（案）**（#855。`build/scaffold/issues/proposals.md` に、追加・変更した入口の機能ごとに 1 案——呼ばれる関数・撤去には作らない。
   各案に、未決定事項〔中間表現の `branches` に無い呼ぶ側の分岐〕・受入基準の雛形〔見せるものの原文のチェックボックスと該当なしの分岐〕・
   作らないもの〔本文の `## 作らないもの` と同じ中身〕が出る。`branches` を書かなければ 8 分岐が全部未決定。
   `branches` が決まりに反する・原文が `source` に無い・呼ばれる関数に書いたなら作らない）・
   **仕様の基準コミット**（#874。追加・変更・撤去のどの本文も `## 仕様` に `- 基準コミット: ` の行を 1 本持ち、git のリポジトリなら値が正本の HEAD と
   そのコミットの日時。git の作業ツリーでない・コミットが無い・git を起動できないなら止めずに「記録していない（理由）」を書き、出力でも知らせる）・
   **まとめた本文**（#876。`--bundle` で名指しした機能が 1 件の本文になり、部分が機能 1 件の本文から 1 行目を外したものとバイトで一致し、
   名指ししない機能の本文・課題一覧（案）は `--bundle` を付けない生成と同じ。本文を作らない機能・変化の揃わない機能・1 件・重複・依存の循環・
   `--check` との組み合わせは 2）・**依存の連鎖**（`issues.json` の `depends`。呼ぶ機能が呼ばれる機能に依存し、組の中は数えない）・
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
6. **本体の定数が `references/` の表と一致する**（メソッド・型・Issue の印と節・基準コミットの行の形——dev-loop の `spec-gap.md` も同じ形を持つ）。**dev-loop の
   `references/spec-gap.md` も同じ印と節を持ち、dev-loop の `SKILL.md` も同じ印を持つ**（2 つのプラグインの境界の写し）。
6'. **想定外の例外（128KB 超のセルの `csv.Error`）も 2 で、古い Issue の本文を残さない**。`-OO`（docstring が無い）で
   引数なしに呼んでもトレースバックにならない。判定（`run`）の外——引数の解釈——で上がった想定外の例外も入口が 2 にする
   （`argparse` を差し替えて作る。#286）。
7. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、
穴が無くても緑になるので）。
**`FOLDING_ONLY` の変異は、一時ディレクトリが大文字小文字を区別しない（実際に作って確かめる。OS の名前で決めない）ときだけ当てる**
——区別するファイルシステム（Linux の CI）では試料がその変異を判別しないので（#852）。当てなかった変異は「変異を当てなかった」と
名前を出し、最後の行の変異の件数に数えず、別に数を出す（当てなかったものを緑と数えない）。
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
NFR_REF = PLUGIN / "references" / "nfr.md"
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

# ---- null を許す項目（#487）。入力・出力の両方に、enum の有る・無い項目を置く
NULLABLE_FEATURE = {
    "id": "F-003", "title": "ラベルを付ける", "source": ["spec/order.md"], "qa": [],
    "operation": {
        "id": "label_of", "method": "POST", "path": "/orders/label",
        "input": {"note": {"type": "string", "nullable": True},
                  "kind": {"type": "string", "enum": ["a", "b"], "nullable": True}},
        "output": {"label": {"type": "string", "nullable": True}, "score": {"type": "integer", "nullable": True},
                   "count": {"type": "integer"}},
    },
    "cases": [
        {"id": "F-003-C1", "title": "メモがあればラベルを付ける", "input": {"note": "x", "kind": "a"},
         "expected": {"label": "x", "score": 1, "count": 1}},
        {"id": "F-003-C2", "title": "メモが無ければラベル無し", "input": {"note": None, "kind": None},
         "expected": {"label": None, "score": None, "count": 0}},
    ],
}
NULLABLE_IMPL = GOOD_IMPL + '''

def label_of(note, kind):
    if note is None:
        return {"label": None, "score": None, "count": 0}
    return {"label": note, "score": 1, "count": 1}
'''
# null を許す整数の項目に真偽値を返す（`True == 1`）——null を許すことが、null でない値の型の検査まで外してはならない
NULLABLE_BOOL_IMPL = NULLABLE_IMPL.replace('"score": 1, "count": 1', '"score": True, "count": 1')
assert NULLABLE_BOOL_IMPL != NULLABLE_IMPL
# `nullable` を書かない基準の試料の生成物の sha256——#487 の前（412ca8f7）の `scaffold.py` が作ったもの。
# **null を許す書き方を足しても、書かない中間表現の生成物は 1 バイトも変えない**（既存の `scaffold/` を `--check` で古くしない）
BASE_SHA256 = {
    "scaffold/openapi.json": "bb382f3f88b73d433944f378b8151d8dfe27b18667cc03bfb40cb4635d2361d9",
    "scaffold/types.py": "0f2cde40b5bf6caa43177aee714f6bfafd0cf713cc9299e4b32457701fad268b",
    "scaffold/tests/test_f_001.py": "7b06b1bbf8f884ddd69c5e4959a31f5fc72983c93dc82c2e828a7bb29ceadb01",
    "scaffold/tests/test_f_002.py": "973acaf11ca2cd5880570b4ece56b275b2f5e6576656fe2ca2ec2556ba3aedf8",
}


def with_nullable(ir: dict) -> None:
    ir["features"].append(copy.deepcopy(NULLABLE_FEATURE))


def f3(ir: dict) -> dict:
    return ir["features"][2]


def unchanged_without_nullable(repo: Path) -> str | None:
    for rel, digest in BASE_SHA256.items():
        actual = hashlib.sha256((repo / rel).read_bytes()).hexdigest()
        if actual != digest:
            return f"{rel} が #487 の前の生成物と違う（{actual}）"
    return None


def nullable_shape(repo: Path) -> str | None:
    doc = json.loads((repo / "scaffold" / "openapi.json").read_text(encoding="utf-8"))
    schemas = doc["components"]["schemas"]
    expected = {
        "LabelOfInput": {"note": {"type": ["string", "null"]}, "kind": {"type": ["string", "null"], "enum": ["a", "b", None]}},
        "LabelOfOutput": {"label": {"type": ["string", "null"]}, "score": {"type": ["integer", "null"]},
                          "count": {"type": "integer"}},
    }
    for name, fields in expected.items():
        if schemas[name]["properties"] != fields:
            return f"OpenAPI の {name} が違う: {schemas[name]['properties']}"
    types = (repo / "scaffold" / "types.py").read_text(encoding="utf-8")
    for needle in ("    note: str | None", "    kind: Literal['a', 'b'] | None", "    label: str | None",
                   "    score: int | None", "    count: int\n"):
        if needle not in types:
            return f"types.py に {needle!r} が無い"
    # null を許す項目を持たない機能の Red テストには、null の扱いを足さない（基準の試料と同じバイト）
    if "NULLABLE" in (repo / "scaffold" / "tests" / "test_f_001.py").read_text(encoding="utf-8"):
        return "null を許す項目を持たない機能の Red テストに NULLABLE がある"
    test = (repo / "scaffold" / "tests" / "test_f_003.py").read_text(encoding="utf-8")
    return None if "NULLABLE = ('label', 'score')" in test else "Red テストが null を許す項目を名指ししていない"


def edit(fn: Callable[[dict], None]) -> Callable[[dict], dict]:
    def apply(ir: dict) -> dict:
        ir = copy.deepcopy(ir)
        fn(ir)
        return ir
    return apply


# ---- 呼ばれる機能（#609）。試料では F-001（割引の判定）を F-002 が呼ぶことにする
def called(callers) -> Callable[[dict], dict]:
    return edit(lambda ir: ir["features"][0].update(called_by=callers))


CALLED = called(["F-002"])
# v2 で呼ばれる機能だけ変える（呼ぶ F-002 は変えない）／呼ぶ機能も変える
V2_CALLED = {**copy.deepcopy(IR["features"][0]), "called_by": ["F-002"]}
V2_CALLED["cases"][0]["expected"] = {"discount": 300}
V2_CALLER = copy.deepcopy(IR["features"][1])
V2_CALLER["cases"][0]["title"] = "発送前なら取り消せる（割引を見直した後も）"
CALLERS_NOTICE = "F-001 は v2 で modify だが、呼ぶ機能（F-002）は v2 で変わっていない"


def callers_in_issue(repo: Path) -> str | None:
    body = (repo / "build" / "scaffold" / "issues" / "F-001.md").read_text(encoding="utf-8")
    if "- 呼ぶ機能: `F-002` 注文を取り消せるか（" not in body:
        return "呼ばれる機能の本文に呼ぶ機能の行が無い"
    if body.index("- 呼ぶ機能:") > body.index("\n## 受入基準\n"):
        return "呼ぶ機能の行が ## 仕様 の節に無い"
    # 呼ばれない機能（入口）の本文には行を足さない
    other = (repo / "build" / "scaffold" / "issues" / "F-002.md").read_text(encoding="utf-8")
    return "呼ばれない機能の本文に呼ぶ機能の行がある" if "呼ぶ機能" in other else None


# ---- まとめた本文と依存の連鎖（#876）。3 機能の試料（F-003 は null を許す機能）
THREE = edit(with_nullable)
# F-002 が F-001 を、F-003 が F-002 を呼ぶ連鎖——{F-001, F-003} をまとめると依存が循環する
CHAIN = edit(lambda ir: (with_nullable(ir), f1(ir).update(called_by=["F-002"]),
                         ir["features"][1].update(called_by=["F-003"])))
BUNDLE_MARK = "<!-- spec-loop-bundle: {} -->"


def default_bodies(repo: Path, *extra: str) -> dict[str, str]:
    """同じ正本で `--bundle` を付けずに生成し直した本文（{ファイル名: 中身}）。生成は `repo` に書く。"""
    proc = subprocess.run([sys.executable, "-I", str(repo.parent / "scripts" / TARGET), "--repo", str(repo), *extra],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return {p.name: p.read_text(encoding="utf-8") for p in sorted((repo / ISSUES).iterdir())}


def bundle_parts(body: str) -> list[str]:
    """まとめた本文の部分（区切りの `---` の行の後ろ）。"""
    return body.split("\n\n---\n\n")[1:]


def bundled(repo: Path) -> str | None:
    """`--bundle F-001,F-002` で 3 機能のうち 2 つをまとめた。"""
    files = sorted(p.name for p in (repo / ISSUES).iterdir())
    if files != ["F-003.md", "bundle-F-001-F-002.md", "issues.json", "proposals.md"]:
        return f"本文のファイルが違う: {files}"
    body = (repo / ISSUES / "bundle-F-001-F-002.md").read_text(encoding="utf-8")
    lines = body.splitlines()
    if lines[:2] != ["<!-- spec-loop-handoff: v3 -->", BUNDLE_MARK.format("F-001・F-002")]:
        return f"まとめた本文の先頭 2 行が印でない: {lines[:2]}"
    if "- `F-001` 割引額を計算する\n- `F-002` 注文を取り消せるか\n" not in body:
        return "まとめた本文に機能の一覧が無い"
    # 機能の一覧をタスクリストにしない——Issue の画面でチェックすると本文が書き換わり、parent-checklist.py の本文の一致が外れる
    if re.search(r"^\s*[-*+] \[[ xX]\]", body, flags=re.M):
        return "まとめた本文にタスクリストの行がある（チェックすると本文が変わる）"
    index = json.loads((repo / ISSUES / "issues.json").read_text(encoding="utf-8"))
    expected = [{"features": ["F-001", "F-002"], "title": "F-001・F-002: 割引額を計算する／注文を取り消せるか", "change": "add",
                 "body": "bundle-F-001-F-002.md",
                 "red": ["TestF001.test_f_001_c1", "TestF001.test_f_001_c2", "TestF002.test_f_002_c1"]},
                {"feature": "F-003", "title": "F-003: ラベルを付ける", "change": "add", "body": "F-003.md",
                 "red": ["TestF003.test_f_003_c1", "TestF003.test_f_003_c2"]}]
    if index != expected:
        return f"issues.json が違う: {index}"
    # 部分は、機能 1 件の本文から 1 行目を外したものとバイトで一致する（指紋・sha256 が残る）——本文の後ろが、
    # 区切りの行と部分をこの順に並べたものとちょうど同じ
    single = default_bodies(repo)
    parts = [single[f"{fid}.md"].split("\n", 1)[1] for fid in ("F-001", "F-002")]
    tail = "".join(f"\n---\n\n{part}" for part in parts)
    if not body.endswith(tail) or not body[: -len(tail)].endswith("- `F-002` 注文を取り消せるか\n"):
        return "まとめた本文の部分が、機能 1 件の本文から 1 行目を外したものを区切りの行で並べたものと違う"
    if [p.split("\n", 1)[0] for p in bundle_parts(body)] != ["<!-- spec-loop-feature: F-001 -->", "<!-- spec-loop-feature: F-002 -->"]:
        return "部分の先頭が機能の印でない"
    merge_with_script(repo)
    for fid, part in zip(("F-001", "F-002"), parts):
        problem = fingerprint_matches(repo, part, fid, "build/merged")
        if problem:
            return problem
    return None


def bundle_keeps_others(repo: Path) -> str | None:
    """まとめた後も、まとめていない機能の本文・課題一覧（案）は既定と同じバイト。"""
    kept = {name: (repo / ISSUES / name).read_text(encoding="utf-8") for name in ("F-003.md", "proposals.md")}
    single = default_bodies(repo)
    for name, text in kept.items():
        if single[name] != text:
            return f"{name} が --bundle を付けない生成と違う"
    return None


def depends_written(repo: Path) -> str | None:
    """F-002 が F-001 を呼ぶ（CALLED）——F-002 の項目だけが `depends` を持つ。"""
    index = json.loads((repo / ISSUES / "issues.json").read_text(encoding="utf-8"))
    found = {i.get("feature"): i.get("depends") for i in index}
    return None if found == {"F-001": None, "F-002": ["F-001"]} else f"issues.json の依存が違う: {index}"


def bundle_depends(repo: Path) -> str | None:
    """連鎖 F-003 → F-002 → F-001 で {F-002, F-003} をまとめた——まとめた項目が F-001 に依存し、組の中の依存は数えない。"""
    index = json.loads((repo / ISSUES / "issues.json").read_text(encoding="utf-8"))
    found = [(i.get("feature") or i.get("features"), i.get("depends")) for i in index]
    return None if found == [("F-001", None), (["F-002", "F-003"], ["F-001"])] else f"issues.json の依存が違う: {found}"


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


# ---- 作らないもの（#851）。範囲の文書の「範囲の外」の節の行を、中間表現の out_of_scope で機能に結びつける
SCOPE_ROWS = ("| ディスクがいっぱい | 失敗を見せる | 既定の線 |",
              "| 外貨での割引 | 円だけで受ける | Q-001。次の版の候補 |",
              "| 取り消しの通知が届かない | 記録を残す | 既定の線 |",
              "- 割引の端数を利用者ごとに変える（原則: 一律に切り捨て。既定の線）",
              "- 取り消しの理由を選ばせる（次の版の候補）")
SCOPE_HEADER = "| 場面 | 原則 | 根拠 |\n| --- | --- | --- |"
SCOPE_MD = ("# 範囲\n\n## 線\n\n既定の線\n\n## 範囲の外\n\n" + SCOPE_HEADER + "\n" + "\n".join(SCOPE_ROWS[:3])
            + "\n\n" + SCOPE_ROWS[3] + "\n\n### 補足\n\n" + SCOPE_ROWS[4]
            + "\n\n## 付録\n\n" + SCOPE_HEADER + "\n| 付録の行 | 原則 | 根拠 |\n")
SCOPE_SPEC = {"order.md": SPEC, "scope.md": SCOPE_MD}
NOT_BUILT_NONE = "この機能に関わるとして写した{}は無い（無いことは、ほかのものを作ってよいという意味ではない）。"
NO_BUDGET = ("要求なし——この Issue は性能の要求（数字のある予算）を渡していない。"
             "速さのための最適化（キャッシュ・並列化・索引の追加など）をしない。最適化は、計測で予算を超えたと示せたときだけ。")
COPIED = "（範囲の文書 `build/merged/spec/scope.md` の「範囲の外」の節から、原文のまま写した。）"


def out_of_scope(f001, f002=None) -> Callable[[dict], dict]:
    def apply(ir: dict) -> None:
        f1(ir)["out_of_scope"] = f001
        if f002 is not None:
            ir["features"][1]["out_of_scope"] = f002
    return edit(apply)


# F-001 は並びを範囲の文書と変えて挙げる（本文は範囲の文書の順）。F-002 は小見出しの下の箇条書きの候補だけ
OUT_OF_SCOPE_IR = out_of_scope([SCOPE_ROWS[3], SCOPE_ROWS[1], SCOPE_ROWS[0]], [SCOPE_ROWS[4]])


def not_built_section(body: str) -> str:
    if "\n## 作らないもの\n\n" not in body:
        return "（作らないものの節が無い）"
    return body.split("\n## 作らないもの\n\n", 1)[1].split("\n\n## 仕様の穴を見つけたら\n", 1)[0]


PIPELESS_SCOPE_MD = "# 範囲\n\n## 範囲の外\n\n場面 | 原則\n--- | ---\n外貨 | 円だけ\n"


def pipeless_copied(repo: Path) -> str | None:
    section = not_built_section(bodies(repo)["F-001"])
    return None if "### 範囲の外\n\n場面 | 原則\n--- | ---\n外貨 | 円だけ\n\n" + COPIED in section else f"先頭の | の無い表の行に見出しが付かない: {section}"


def not_built_added_in_v2(repo: Path) -> str | None:
    found = bodies(repo)
    if list(found) != ["F-001"]:
        return f"本文を作るのは out_of_scope を足した機能だけのはず: {list(found)}"
    problem = body_has(found["F-001"], ("<!-- spec-loop-change: modify; base=v1 -->", "| `F-001-C1` | 回帰 |",
                                        "| `F-001-C2` | 回帰 |"), "out_of_scope を足した変更")
    if problem:
        return problem
    section = not_built_section(found["F-001"])
    return None if f"{SCOPE_HEADER}\n{SCOPE_ROWS[0]}\n\n{COPIED}" in section else f"v2 の本文の作らないものに行が無い: {section}"


def not_built_copied(repo: Path) -> str | None:
    found = bodies(repo)
    head = "受入基準に結びつかないものを作らない。下に挙げたものは、この機能では作らない。"
    budget = f"### 性能予算\n\n{NO_BUDGET}"
    expected = {
        "F-001": "\n\n".join([head, "### 範囲の外", f"{SCOPE_HEADER}\n{SCOPE_ROWS[0]}", SCOPE_ROWS[3], COPIED,
                              "### 次の版の候補", f"{SCOPE_HEADER}\n{SCOPE_ROWS[1]}", COPIED, budget]),
        "F-002": "\n\n".join([head, "### 範囲の外", NOT_BUILT_NONE.format("範囲の外の行"),
                              "### 次の版の候補", SCOPE_ROWS[4], COPIED, budget]),
    }
    for fid, want in expected.items():
        got = not_built_section(found[fid])
        if got != want:
            return f"{fid} の作らないものの節が違う:\n{got}\n---- 期待:\n{want}"
    # 挙げていない行（範囲の外の節の行・節の外の行）は、どの本文にも写らない
    for fid, body in found.items():
        for stray in (SCOPE_ROWS[2], "付録の行"):
            if stray in body:
                return f"{fid} の本文に挙げていない行 {stray!r} がある"
    return None


# ---- 呼ぶ側の分岐と課題一覧（案）（#855）。仕様の原文の行を、中間表現の branches で分岐に結びつける
BRANCH_LINES = ("- 入力が欠ける: 「データ欠落」と表示する",
                "- 入力が遅れる: 「取得中」と表示する",
                "| 呼ぶ処理が失敗する | 「再計算待ち」と表示し、担当に通知する |",
                "- 入力の順が崩れる: 該当なし（1 回の要求で全部そろって届く）",
                "呼ぶ側の分岐: 該当なし（純粋な計算で、外と結ばない）")
BRANCH_SPEC = SPEC + "\n## 呼ぶ側の分岐\n\n" + "\n".join(BRANCH_LINES[:2]) + "\n\n| 分岐 | 見せるもの |\n| --- | --- |\n" \
    + "  " + BRANCH_LINES[2] + "  \n\n" + BRANCH_LINES[3] + "\n\n" + BRANCH_LINES[4] + "\n"
BRANCH_SPECS = {"order.md": BRANCH_SPEC, "scope.md": SCOPE_MD}
# 未決定事項と受入基準の雛形を見分けるため、F-001 は分岐の一部だけ（見せるもの 3・該当なし 1。並びを分岐の表と変える）、
# F-002 は行ごと該当なし。F-001 は範囲の外の行も持つ（案の作らないもの）
F001_BRANCHES = {"呼ぶ処理が失敗する": {"shows": BRANCH_LINES[2]}, "入力の順が崩れる": {"none": BRANCH_LINES[3]},
                 "入力が遅れる": {"shows": BRANCH_LINES[1]}, "入力が欠ける": {"shows": BRANCH_LINES[0]}}
ALL_BRANCHES = ("入力が欠ける", "入力が遅れる", "入力の順が崩れる", "呼ぶ処理が失敗する", "呼ぶ処理がやり直される",
                "呼ぶ処理が再起動する", "量が上限を超える", "量が重なる")


def branches(f001=None, f002=None, scope=None) -> Callable[[dict], dict]:
    def apply(ir: dict) -> None:
        if f001 is not None:
            f1(ir)["branches"] = f001
        if f002 is not None:
            ir["features"][1]["branches"] = f002
        if scope is not None:
            f1(ir)["out_of_scope"] = scope
    return edit(apply)


BRANCHES_IR = branches(F001_BRANCHES, {"none": BRANCH_LINES[4]}, [SCOPE_ROWS[0], SCOPE_ROWS[1]])
PROPOSALS_FILE = Path("build") / "scaffold" / "issues" / "proposals.md"
UNDECIDED = "- {}: 中間表現の `branches` に書き起こしていない——仕様が決めていれば書き起こし、決めていなければ `/spec-loop:spec-review` に戻す"
KEEP_GREEN = "- [ ] 周の前に緑だった Red テストが、周の後も緑のままであること（元の機能 `{}` の Red テストを含む）"
NO_RED = "上の分岐に Red テストは無い——見せるものの確かめ方（結合テスト・実機確認）は、この案を登録した Issue の周が決める。"
NOT_BUILT_HEAD = "受入基準に結びつかないものを作らない。下に挙げたものは、この機能では作らない。"


def proposal_sections(repo: Path) -> dict[str, str] | str:
    """{機能の id: 案の本文（見出しの次の行から、次の案の見出しの前まで）}。ファイルが無ければ理由の文字列。"""
    path = repo / PROPOSALS_FILE
    if not path.is_file():
        return f"{PROPOSALS_FILE} が無い"
    text = path.read_text(encoding="utf-8")
    if not text.startswith("# 課題一覧（案）\n\n"):
        return f"課題一覧（案）の見出しで始まらない: {text[:80]!r}"
    if "**scaffold はこの案を登録しない**" not in text or "**未決定事項のある案は、登録の前に `/spec-loop:spec-review` に戻す**" not in text:
        return "課題一覧（案）の冒頭に、登録しないこと・未決定事項を spec-review に戻すことが無い"
    found = {}
    for chunk in text.split("\n## ")[1:]:
        head, _, rest = chunk.partition("\n")
        found[head.split(":", 1)[0]] = (head, rest)
    return found


def proposal_text(fid: str, title: str, change: str, undecided: list[str], template: list[str], not_built: list[str]) -> str:
    return "\n".join([
        "", f"- 元の機能: `{fid}`（Issue の本文 `{fid}.md`・変化 `{change}`）——その Red テストは関数の振る舞いを確かめる。"
        "この案は Red テストの外に残る呼ぶ側の結線を受け持つ",
        "- 仕様の原文: `build/merged/spec/order.md`",
        "", "### 未決定事項", "", *undecided,
        "", "### 受入基準の雛形", "", *template,
        "", KEEP_GREEN.format(fid), "", NO_RED, "", "### 作らないもの", "", *not_built]) + "\n"


def proposals_written(repo: Path) -> str | None:
    found = proposal_sections(repo)
    if isinstance(found, str):
        return found
    if list(found) != ["F-001", "F-002"]:
        return f"案は入口の機能ごとに 1 つのはず: {list(found)}"
    budget = ["#### 性能予算", "", NO_BUDGET]
    expected = {
        "F-001": ("F-001: 割引額を計算する の結線", proposal_text(
            "F-001", "割引額を計算する", "add",
            [UNDECIDED.format(name) for name in ALL_BRANCHES[4:]],
            [f"- [ ] 入力が欠ける: {BRANCH_LINES[0]}", f"- [ ] 入力が遅れる: {BRANCH_LINES[1]}",
             f"- [ ] 呼ぶ処理が失敗する: {BRANCH_LINES[2]}", "", "該当なしの分岐（仕様の原文）:", "",
             f"- 入力の順が崩れる: {BRANCH_LINES[3]}"],
            [NOT_BUILT_HEAD, "", "#### 範囲の外", "", SCOPE_HEADER, SCOPE_ROWS[0], "", COPIED,
             "", "#### 次の版の候補", "", SCOPE_HEADER, SCOPE_ROWS[1], "", COPIED, "", *budget])),
        "F-002": ("F-002: 注文を取り消せるか の結線", proposal_text(
            "F-002", "注文を取り消せるか", "add",
            ["無い（呼ぶ側の分岐は、どれも仕様が決めている）。"],
            [f"呼ぶ側の分岐は行ごと該当なし（仕様の原文: {BRANCH_LINES[4]}）——結線で見せるものは無い。"],
            [NOT_BUILT_HEAD, "", "#### 範囲の外", "", NOT_BUILT_NONE.format("範囲の外の行"),
             "", "#### 次の版の候補", "", NOT_BUILT_NONE.format("次の版の候補"), "", *budget])),
    }
    for fid, want in expected.items():
        if found[fid] != want:
            return f"{fid} の案が違う:\n{found[fid][0]}\n{found[fid][1]}\n---- 期待:\n{want[0]}\n{want[1]}"
    # 案の作らないものは、元の機能の本文の `## 作らないもの` と同じ中身（小見出しだけ 1 段下げる）
    body = not_built_section(bodies(repo)["F-001"])
    section = found["F-001"][1].split("### 作らないもの\n\n", 1)[1].rstrip("\n")
    if section != body.replace("\n### ", "\n#### "):
        return f"案の作らないものが本文の作らないものと違う:\n{section}\n---- 本文:\n{body}"
    return None


def proposals_unwritten(repo: Path) -> str | None:
    """branches を書いていない中間表現——どの入口の機能も 8 分岐が全部未決定。"""
    found = proposal_sections(repo)
    if isinstance(found, str):
        return found
    for fid in ("F-001", "F-002"):
        if fid not in found:
            return f"{fid} の案が無い: {list(found)}"
        part = found[fid][1].split("\n### 未決定事項\n\n", 1)[1].split("\n\n### 受入基準の雛形\n", 1)[0]
        if part.split("\n") != [UNDECIDED.format(name) for name in ALL_BRANCHES]:
            return f"{fid} の未決定事項が 8 分岐でない:\n{part}"
        if "見せるものが決まった分岐は無い（上の未決定事項を先に決める）。" not in found[fid][1]:
            return f"{fid} の受入基準の雛形に、決まった分岐が無いことの文言が無い"
    return None


def proposals_entry_only(repo: Path) -> str | None:
    """F-001 は F-002 から呼ばれる関数——案は呼ぶ入口の F-002 だけ。"""
    found = proposal_sections(repo)
    if isinstance(found, str):
        return found
    return None if list(found) == ["F-002"] else f"案は呼ぶ入口の機能だけのはず: {list(found)}"


def proposals_none(repo: Path) -> str | None:
    found = proposal_sections(repo)
    if isinstance(found, str):
        return found
    if found:
        return f"案は無いはず: {list(found)}"
    text = (repo / PROPOSALS_FILE).read_text(encoding="utf-8")
    return None if "案は無い——v2 で追加・変更した入口の機能（`impl_module` を変えただけのものを除く）が無い。" in text else f"案が無いことの文言が無い: {text[-200:]}"


ALL_NONE_SPEC = SPEC + "\n" + "\n".join(f"- {name}: 該当なし" for name in ALL_BRANCHES) + "\n"


def proposals_all_none(repo: Path) -> str | None:
    """F-001 は 8 分岐を 1 つずつ該当なし——未決定事項は無く、雛形は「決める」と言わない。"""
    found = proposal_sections(repo)
    if isinstance(found, str):
        return found
    text = found["F-001"][1]
    for needle in ("### 未決定事項\n\n無い（呼ぶ側の分岐は、どれも仕様が決めている）。",
                   "### 受入基準の雛形\n\n見せるものが決まった分岐は無い——どの分岐も該当なし。",
                   "- 量が重なる: - 量が重なる: 該当なし"):
        if needle not in text:
            return f"どの分岐も該当なしの案に {needle!r} が無い:\n{text[:600]}"
    return "上の未決定事項を先に決める と書いている" if "上の未決定事項を先に決める" in text else None


def proposals_modified(repo: Path) -> str | None:
    """v2 で branches だけ足した F-001——変更（modify）の案が 1 つ。"""
    found = proposal_sections(repo)
    if isinstance(found, str):
        return found
    if list(found) != ["F-001"]:
        return f"案は変えた機能だけのはず: {list(found)}"
    return None if "・変化 `modify`）" in found["F-001"][1] and f"- [ ] 入力が欠ける: {BRANCH_LINES[0]}" in found["F-001"][1] \
        else f"変更の案が違う: {found['F-001'][1][:300]}"


# ---- 性能の要求（#852）。`shared/nfr.csv` の性能の行を、中間表現の nfr で機能に結びつける
NFR_HEADER = "No,対象,指標,上限,単位,条件,根拠\n"
NFR_ROWS = ("N-001,割引の計算,p95,300,ms,ピーク 50 req/s,2025 年末のピークが 42 req/s",
            "N-002,取り消しの判定,p50,1,ms,負荷を問わない,画面の待ちを 1 ms に収める業務の締め切り",
            # 性能でない行（指標・単位が性能の形でない）——指さなければ止めない
            "N-003,注文の受付,稼働率,99.9,%,月,契約")
NFR_CSV = NFR_HEADER + "\n".join(NFR_ROWS) + "\n"
NFR_FILE = str(V1 / "shared" / "nfr.csv")
PERF_FILE = "scaffold/perf/perf_f_001.py"
# 1 回の呼び出しが 5 ms を下回らない実装（上限 1 ms の p50 を必ず超える）。値は正しい
SLOW_IMPL = "import time\n" + GOOD_IMPL.replace('    if amount < 0:\n', '    time.sleep(0.005)\n    if amount < 0:\n', 1)
assert SLOW_IMPL.count("time.sleep") == 1


def nfr(f001, f002=None) -> Callable[[dict], dict]:
    def apply(ir: dict) -> None:
        f1(ir)["nfr"] = f001
        if f002 is not None:
            ir["features"][1]["nfr"] = f002
    return edit(apply)


def with_nfr(text: str = NFR_CSV) -> dict[str, str]:
    return {NFR_FILE: text}


def perf_run(repo: Path, impl: str | None) -> tuple[int, str]:
    target = repo / "spec_impl.py"
    if impl is None:
        target.unlink(missing_ok=True)
    else:
        target.write_text(impl, encoding="utf-8")
    proc = subprocess.run([sys.executable, "-E", "-s", "-B", "-m", "unittest", "discover", "-s", "scaffold/perf", "-p", "perf_f_001.py"],
                          capture_output=True, text=True, cwd=repo)
    return proc.returncode, proc.stdout + proc.stderr


def budget_section(body: str) -> str:
    return not_built_section(body).split("### 性能予算\n\n", 1)[-1]


def budget_copied(repo: Path) -> str | None:
    found = bodies(repo)
    perf = repo / PERF_FILE
    if not perf.is_file():
        return f"{PERF_FILE} が無い（nfr を持つ機能の性能テスト）"
    others = sorted(p.name for p in (repo / "scaffold" / "perf").iterdir() if p.name != perf.name)
    if others:
        return f"nfr を持たない機能の性能テストがある: {others}"
    sha = hashlib.sha256(perf.read_bytes()).hexdigest()
    want = "\n".join([
        "この機能の性能の要求（`build/merged/shared/nfr.csv` の行から写した）:", "",
        "| No | 対象 | 指標 | 上限 | 条件 | 根拠 |", "| --- | --- | --- | --- | --- | --- |",
        "| N-001 | 割引の計算 | p95 | 300 ms | ピーク 50 req/s | 2025 年末のピークが 42 req/s |", "",
        "**予算の中なら、速さのための最適化をしない。** 最適化は、性能テストか計測で予算を超えたと示せたときだけ。", "",
        f"- 性能テスト: `{PERF_FILE}`（sha256: `{sha}`）——実装をケースの入力で 1 回ずつ 200 回呼び、1 回の時間から指標を出して上限と比べる",
        "- 回し方（正本リポジトリの根で）:", "", "```bash", "python3 -m unittest discover -s scaffold/perf -p perf_f_001.py", "```", "",
        "- **性能テストは `条件` の負荷（同時の呼び出し）を再現しない**——緑でも、負荷の下で上限を守る証明にはならない。"
        "負荷の下で守るかは、負荷試験・本番の計測で確かめる。",
        "- **性能テストは受入基準（上の Red テストの表）ではない**——最適化してよいかを決める計測の道具である。"])
    got = budget_section(found["F-001"])
    if got != want:
        return f"F-001 の性能予算が違う:\n{got}\n---- 期待:\n{want}"
    # nfr を持たない機能は「要求なし」のまま
    if budget_section(found["F-002"]) != NO_BUDGET:
        return f"F-002 の性能予算が「要求なし」でない: {budget_section(found['F-002'])}"
    # 性能テストは Red テストの表（受入基準）に入らない
    for fid, body in found.items():
        if "perf_" in body.split("\n## 作らないもの\n", 1)[0]:
            return f"{fid} の本文の受入基準・Red テストの節に性能テストがある"
    # 実装が無ければ失敗（エラーではない）、正しい実装なら緑（陽性対照）
    code, out = perf_run(repo, None)
    if code == 0 or "FAILED (failures=1)" not in out or "未実装: " not in out:
        return f"実装の無い性能テストが「未実装」で失敗しない: {out[-300:]}"
    code, out = perf_run(repo, GOOD_IMPL)
    return None if code == 0 and "OK" in out else f"速い実装で性能テストが緑にならない: {out[-300:]}"


def budget_compared(repo: Path) -> str | None:
    """上限 1 ms の p50 を、1 回 5 ms の実装は超え（失敗）、速い実装は超えない（陽性対照）。"""
    code, out = perf_run(repo, SLOW_IMPL)
    if code == 0 or "p50 が " not in out or "上限 1 ms を超えた（N-002）" not in out:
        return f"遅い実装で性能テストが上限を超えたと言わない: {out[-300:]}"
    code, out = perf_run(repo, GOOD_IMPL)
    return None if code == 0 else f"速い実装で性能テストが緑にならない: {out[-300:]}"


def drop_nfr(repo: Path) -> None:
    path = repo / IR_FILE
    ir = json.loads(path.read_text(encoding="utf-8"))
    for feature in ir["features"]:
        feature.pop("nfr", None)
    path.write_text(json.dumps(ir, ensure_ascii=False, indent=2), encoding="utf-8")


def perf_removed(repo: Path) -> str | None:
    if (repo / PERF_FILE).exists():
        return f"nfr を外した機能の性能テスト {PERF_FILE} が残っている"
    return None if NO_BUDGET in bodies(repo)["F-001"] else "nfr を外した機能の性能予算が「要求なし」でない"


def nfr_added_in_v2(repo: Path) -> str | None:
    found = bodies(repo)
    if list(found) != ["F-001"]:
        return f"本文を作るのは nfr を足した機能だけのはず: {list(found)}"
    problem = body_has(found["F-001"], ("<!-- spec-loop-change: modify; base=v1 -->", "| `F-001-C1` | 回帰 |",
                                        "| N-001 | 割引の計算 | p95 | 300 ms |"), "nfr を足した変更")
    return problem or (None if (repo / PERF_FILE).is_file() else f"v2 で nfr を足した機能の {PERF_FILE} が無い")


# #923: トレースのケース（形式検査の反例の実行順を、実装の口で強制して再現する Red テスト）
TRACE_FORMAL = {str(V1 / "spec" / "formal" / "stock-reserve" / "README.md"): "# stock-reserve\n\n結果: 反例あり（売り越し）\n"}
STOCK_TRACE = {
    "formal": "stock-reserve",
    "setup": [{"operation": "set_stock", "input": {"item": "a", "qty": 1}, "expected": {"stock": 1}}],
    "calls": {"first": {"operation": "reserve", "input": {"item": "a", "qty": 1}},
              "second": {"operation": "reserve", "input": {"item": "a", "qty": 1}}},
    "steps": [["first", "read"], ["second", "read"], ["first", "write"], ["second", "write"]],
    "outcomes": [{"ok": True}, {"error": "OUT_OF_STOCK"}],
    "after": [{"operation": "get_stock", "input": {"item": "a"}, "expected": {"stock": 0}}],
}
STOCK_FEATURES = [
    {
        "id": "F-003", "title": "在庫を引き当てる", "source": ["spec/order.md"], "qa": [],
        "operation": {"id": "reserve", "method": "POST", "path": "/stock/reserve",
                      "input": {"item": {"type": "string"}, "qty": {"type": "integer"}},
                      "output": {"ok": {"type": "boolean"}}, "errors": ["INVALID_QTY", "OUT_OF_STOCK"]},
        "cases": [
            {"id": "F-003-C1", "title": "数量が 0 なら拒否する", "input": {"item": "a", "qty": 0}, "error": "INVALID_QTY"},
            {"id": "F-003-C2", "title": "同じ品を同時に引き当てても売り越さない", "trace": STOCK_TRACE},
        ],
    },
    {
        "id": "F-004", "title": "在庫を置く", "source": ["spec/order.md"], "qa": [],
        "operation": {"id": "set_stock", "method": "PUT", "path": "/stock",
                      "input": {"item": {"type": "string"}, "qty": {"type": "integer"}}, "output": {"stock": {"type": "integer"}}},
        "cases": [{"id": "F-004-C1", "title": "置いた数を返す", "input": {"item": "b", "qty": 3}, "expected": {"stock": 3}}],
    },
    {
        "id": "F-005", "title": "在庫を数える", "source": ["spec/order.md"], "qa": [],
        "operation": {"id": "get_stock", "method": "GET", "path": "/stock/count",
                      "input": {"item": {"type": "string"}}, "output": {"stock": {"type": "integer"}}},
        "cases": [{"id": "F-005-C1", "title": "置いていない品は 0", "input": {"item": "none"}, "expected": {"stock": 0}}],
    },
]


def traced(fn: Callable[[dict], None] = lambda ir: None) -> Callable[[dict], dict]:
    """基準の中間表現に在庫の 3 機能（F-003 がトレースのケースを持つ）を足し、`fn` で崩す。"""
    def build_ir(ir: dict) -> dict:
        ir = copy.deepcopy(ir)
        ir["features"] += copy.deepcopy(STOCK_FEATURES)
        fn(ir)
        return ir
    return build_ir


def trace_of(ir: dict) -> dict:
    return ir["features"][2]["cases"][1]["trace"]


def after_only(ir: dict) -> None:
    trace = trace_of(ir)
    trace.pop("outcomes")
    trace["setup"][0].update(input={"item": "a", "qty": 2}, expected={"stock": 2})


STOCK_STATE = """
import threading

_stock = {}
_lock = threading.Lock()


def reset_state():
    _stock.clear()


def set_stock(item, qty):
    _stock[item] = qty
    return {"stock": qty}


def get_stock(item):
    return {"stock": _stock.get(item, 0)}
"""
# 競合する実装: 読んでから書くまでの間に、ほかの呼び出しが同じ在庫を読める（トレースの順で売り越す）
RACY_RESERVE = """

def reserve(item, qty, checkpoint=lambda name: None):
    if qty <= 0:
        return {"error": "INVALID_QTY"}
    checkpoint("read")
    have = _stock.get(item, 0)
    checkpoint("write")
    if have < qty:
        return {"error": "OUT_OF_STOCK"}
    _stock[item] = have - qty
    return {"ok": True}
"""
RACY_IMPL = GOOD_IMPL + STOCK_STATE + RACY_RESERVE
# 正しい実装（陽性対照）: 読むから書くまでを排他で守る——トレースの 2 段目で止めた呼び出しが排他を待つ
LOCKED_IMPL = GOOD_IMPL + STOCK_STATE + RACY_RESERVE.replace(
    '    checkpoint("read")\n    have = _stock.get(item, 0)\n    checkpoint("write")\n    if have < qty:\n'
    '        return {"error": "OUT_OF_STOCK"}\n    _stock[item] = have - qty\n    return {"ok": True}\n',
    '    with _lock:\n        checkpoint("read")\n        have = _stock.get(item, 0)\n        checkpoint("write")\n'
    '        if have < qty:\n            return {"error": "OUT_OF_STOCK"}\n        _stock[item] = have - qty\n        return {"ok": True}\n')
# 口を呼ばない競合する実装——順を強制できないので、素通りさせずに失敗にする
SILENT_IMPL = RACY_IMPL.replace('    checkpoint("read")\n', "").replace('    checkpoint("write")\n', "")
# 口の引数を受け取らない実装
NO_KEYWORD_IMPL = SILENT_IMPL.replace("def reserve(item, qty, checkpoint=lambda name: None):", "def reserve(item, qty):")
# 一部の段にだけ口を呼ぶ競合する実装（書く段の前で呼ばない）・段の名前を違える競合する実装——どちらも順を強制できないので失敗にする
PARTIAL_IMPL = RACY_IMPL.replace('    checkpoint("write")\n', "")
RENAMED_STEPS_IMPL = RACY_IMPL.replace('checkpoint("read")', 'checkpoint("load")').replace('checkpoint("write")', 'checkpoint("store")')
# 口の約束（段の操作の直前に、その段のために排他を取る前に呼ぶ）を守る実装（#923 の 2 パス目）。
# 読む段と書く段を別々の排他で守る競合する実装（TOCTOU）は赤、読むから書くまでを 1 つの排他で守る正しい実装は緑
_RACY_BODY = ('    checkpoint("read")\n    have = _stock.get(item, 0)\n    checkpoint("write")\n    if have < qty:\n'
              '        return {"error": "OUT_OF_STOCK"}\n    _stock[item] = have - qty\n    return {"ok": True}\n')
TOCTOU_IMPL = GOOD_IMPL + STOCK_STATE + RACY_RESERVE.replace(_RACY_BODY, (
    '    checkpoint("read")\n    with _lock:\n        have = _stock.get(item, 0)\n    checkpoint("write")\n    with _lock:\n'
    '        if have < qty:\n            return {"error": "OUT_OF_STOCK"}\n        _stock[item] = have - qty\n        return {"ok": True}\n'))
PRELOCK_IMPL = GOOD_IMPL + STOCK_STATE + RACY_RESERVE.replace(_RACY_BODY, (
    '    checkpoint("read")\n    with _lock:\n        have = _stock.get(item, 0)\n        checkpoint("write")\n'
    '        if have < qty:\n            return {"error": "OUT_OF_STOCK"}\n        _stock[item] = have - qty\n        return {"ok": True}\n'))
# 状態を空に戻す関数の無い実装
NO_RESET_IMPL = LOCKED_IMPL.replace("def reset_state():\n    _stock.clear()\n", "")
TRACE_TEST = "scaffold/tests/test_f_003.py"


def expect_trace_red(reason: str) -> Callable[[Path], str | None]:
    """トレースのケースだけが、`reason` を出して失敗（エラーではない）する。"""
    def post(repo: Path) -> str | None:
        code, out = red_run(repo)
        if code == 0:
            return f"トレースの Red テストが通った: {out[-300:]}"
        if "FAILED (failures=1)" not in out:
            return f"失敗がトレースのケースの 1 件（エラーなし）になっていない: {out[-600:]}"
        if "test_f_003_c2" not in out or reason not in out:
            return f"トレースのケースが {reason!r} で失敗していない: {out[-600:]}"
        return None
    return post


def trace_written(repo: Path) -> str | None:
    test = (repo / TRACE_TEST).read_text(encoding="utf-8")
    for needle in ("    def test_f_003_c2(self):\n        self.trace({", "class Schedule:", "import threading",
                   "TRACE_TYPES = {'get_stock': {'stock': 'integer', 'error': 'string'}, 'reserve': {'ok': 'boolean', 'error': 'string'}, "
                   "'set_stock': {'stock': 'integer', 'error': 'string'}}", "RESET = 'reset_state'"):
        if needle not in test:
            return f"{TRACE_TEST} に {needle!r} が無い"
    # トレースのケースを持たない機能の Red テストには足さない
    for rel in ("scaffold/tests/test_f_004.py", "scaffold/tests/test_f_001.py"):
        if "Schedule" in (repo / rel).read_text(encoding="utf-8"):
            return f"トレースのケースを持たない {rel} に順の強制がある"
    # トレースのケースを持たない機能の Red テストは、トレースを足す前と同じバイト（#923 の前の生成物）
    for rel in ("scaffold/tests/test_f_001.py", "scaffold/tests/test_f_002.py"):
        if hashlib.sha256((repo / rel).read_bytes()).hexdigest() != BASE_SHA256[rel]:
            return f"トレースのケースを持たない {rel} が #923 の前の生成物と違う"
    body = bodies(repo)["F-003"]
    return body_has(body, ("| `F-003-C2` | 追加 | 同じ品を同時に引き当てても売り越さない | `TestF003.test_f_003_c2` |",
                           "状態を空に戻す関数 `reset_state()`", "トレースが同時に走らせる関数（`reserve`）",
                           "`checkpoint(\"<段の名前>\")` を呼ぶ"), "トレースのケースを持つ機能")


def trace_kept_out(repo: Path) -> str | None:
    """トレースのケースを持たない機能の本文には、口の行が出ない。"""
    return None if "reset_state" not in bodies(repo)["F-004"] else "トレースのケースを持たない機能の本文に口の行がある"


def trace_perf(repo: Path) -> str | None:
    perf = (repo / "scaffold" / "perf" / "perf_f_003.py").read_text(encoding="utf-8")
    return None if "INPUTS = [{'item': 'a', 'qty': 0}]" in perf else f"性能テストの入力にトレースのケースが混ざった: {perf[:800]}"


def trace_v2(case: str, status: str) -> Callable[[Path], str | None]:
    def post(repo: Path) -> str | None:
        found = bodies(repo)
        if list(found) != ["F-003"]:
            return f"本文を作るのは変えた機能だけのはず: {list(found)}"
        return body_has(found["F-003"], (f"| `{case}` | {status} |",), "v2 の変更")
    return post


def trace_called_moved(repo: Path) -> str | None:
    """v2 でトレースが呼ぶほかの機能の入口（F-005）の出力の型だけを変えた——F-003 は機能が同じでも Red テストが変わるので変更の本文を作る。"""
    found = bodies(repo)
    if list(found) != ["F-003", "F-005"]:
        return f"本文を作るのは F-003（トレースが呼ぶ入口が変わった）と F-005 のはず: {list(found)}"
    return body_has(found["F-003"], ("<!-- spec-loop-change: modify; base=v1 -->", "| `F-003-C1` | 回帰 |", "| `F-003-C2` | 変更 |"),
                    "トレースが呼ぶ入口が変わった機能")


def reversed_keys(value):
    """入れ子の dict まで、キーの順を逆にした写し（中身は同じ）。"""
    if isinstance(value, dict):
        return {key: reversed_keys(value[key]) for key in reversed(list(value))}
    if isinstance(value, list):
        return [reversed_keys(item) for item in value]
    return value


def plant_reordered_v2(repo: Path) -> None:
    """v1 で作った Red テストの sha256 を残し、中身が同じで F-003 のキーの順だけ逆にした v2 を置く。"""
    (repo / "before.sha256").write_text(hashlib.sha256((repo / TRACE_TEST).read_bytes()).hexdigest(), encoding="utf-8")
    for rel, body in v2([reversed_keys(STOCK_FEATURES[0])]).items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def reordered_kept(repo: Path) -> str | None:
    if "F-003" in bodies(repo):
        return f"キーの順だけ変えた F-003 の本文を作った: {list(bodies(repo))}"
    now = hashlib.sha256((repo / TRACE_TEST).read_bytes()).hexdigest()
    before = (repo / "before.sha256").read_text(encoding="utf-8")
    return None if now == before else f"キーの順だけ変えたのに {TRACE_TEST} のバイトが変わった（{before[:12]} → {now[:12]}）"


def v2_trace(fn: Callable[[dict], None]) -> dict[str, str]:
    feature = copy.deepcopy(STOCK_FEATURES[0])
    fn(feature)
    return {**TRACE_FORMAL, **v2([feature])}


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
    # nfr を持たない中間表現からは、性能テストを作らない（#852）
    if (repo / "scaffold" / "perf").exists():
        return "nfr を持たない中間表現で scaffold/perf/ を書いた"
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
    positions = [body.find(f"\n{s}\n") for s in ("## 仕様", "## 受入基準", "## Red テスト", "## Q&A の回答", "## 作らないもの", "## 仕様の穴を見つけたら")]
    if -1 in positions or positions != sorted(positions):
        return f"節が揃っていないか順が違う: {positions}"
    for needle in ("TestF001.test_f_001_c1", "TestF001.test_f_001_c2", "`F-001-C1`", "`F-001-C2`",
                   "| Q-001 | シルバーで 10000 円未満の割引は？ | A（業務部が回答） | 決定表 4 行目 |",
                   # 機能ではなくケースだけが指す Q&A（受入基準の表の `| Q-002 |` と区別するため、質問まで見る）
                   "| Q-002 | 金額が負なら？ |", "`POST /orders/discount`",
                   "`calc_discount`", "`build/merged/spec/order.md`", "起票元 `開発`", "references/spec-gap.md",
                   "`merge-versions.py docs build/merged --upto 1`", "`docs/v<n>/shared/qa.csv`",
                   "| ケース | 変化 | 確かめること | Red テスト | Q&A |", "| `F-001-C1` | 追加 |", "変化: 追加（v1 の機能）",
                   "実装が無い状態では、ケースの数だけ失敗する。",
                   # 範囲の外の行の無い機能でも、作らないものの節は 3 つの小見出しと「無い」を書く（#851）
                   NOT_BUILT_NONE.format("範囲の外の行"), NOT_BUILT_NONE.format("次の版の候補"),
                   "### 性能予算\n\n" + NO_BUDGET):
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
            # `<型> | None` は null を許す項目（#487）——OpenAPI では `type` に `"null"` を足し、enum にも null を足す
            allow_null = note.endswith(" | None")
            note = note.removesuffix(" | None")
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
            if allow_null:
                fields[block[0]][field]["nullable"] = True
    return fields


def schema_matches(schema: dict, expected: dict) -> bool:
    """OpenAPI の項目の schema が、`types.py` の注釈から戻した候補に合うか。"""
    kind, enum = schema.get("type"), expected.get("enum")
    if expected.get("nullable"):
        if not isinstance(kind, list) or len(kind) != 2 or kind[1] != "null":
            return False
        kind, enum = kind[0], None if enum is None else enum + [None]
    if not isinstance(kind, str) or kind not in expected["types"]:
        return False
    if enum is not None:
        return set(schema) == {"type", "enum"} and schema["enum"] == enum
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
# v2 で割引の出力に null を許しただけ（期待は同じ）——前の版の実装はどのケースも緑のまま（#487）
V2_NULLABLE = copy.deepcopy(IR["features"][0])
V2_NULLABLE["operation"]["output"]["discount"]["nullable"] = True
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


# 仮回答の印（#875。`references/handoff-issue.md` の「仮回答の印」の写し——下の突き合わせが本体の定数と原本を見る）
PROVISIONAL_LINE = "- 仮回答: "
PROVISIONAL_CELL = "（暫定）"


def unmarked(body: str, what: str) -> str | None:
    """依存しない本文は印を持たない（行もセルも）。"""
    if PROVISIONAL_LINE in body or PROVISIONAL_CELL in body:
        return f"{what}の本文に、依存していない仮回答の印がある"
    return None


def provisional_marked(repo: Path) -> str | None:
    """Q-001（暫定反映）は F-001 の機能とケース C1 が指し、Q-002（反映済み）はケース C2 が指す。F-002 は Q&A を指さない。"""
    found = bodies(repo)
    one = found.get("F-001", "")
    lines = [line for line in one.splitlines() if line.startswith(PROVISIONAL_LINE)]
    if len(lines) != 1 or not lines[0].startswith(f"{PROVISIONAL_LINE}Q-001（状態 `暫定反映`"):
        return f"F-001 の本文の仮回答の行が 1 本で Q-001 だけを挙げていない: {lines}"
    if lines and "Q-002" in lines[0]:
        return "確定の Q-002 を仮回答の行に挙げた"
    spec = one.split("## 仕様", 1)[1].split("## 受入基準", 1)[0]
    if lines[0] not in spec:
        return "仮回答の行が ## 仕様 の節に無い"
    rows = {cid: row for row, cid in re.findall(r"^(\| `(F-001-C[0-9])` .*)$", one, flags=re.MULTILINE)}
    if not rows.get("F-001-C1", "").endswith("| Q-001（暫定） |"):
        return f"暫定の Q-001 を根拠にするケースに印が無い: {rows.get('F-001-C1')!r}"
    if not rows.get("F-001-C2", "").endswith("| Q-002 |"):
        return f"確定の Q-002 を根拠にするケースに印が付いた: {rows.get('F-001-C2')!r}"
    return unmarked(found.get("F-002", ""), "依存しない F-002 ")


def provisional_feature_only(repo: Path) -> str | None:
    """暫定の Q-001 を機能の qa だけが指す（どのケースも指さない）——行は付き、表のセルには付かない。"""
    one = bodies(repo).get("F-001", "")
    if f"{PROVISIONAL_LINE}Q-001（" not in one:
        return "機能の qa だけが指す暫定の No を、仮回答の行に挙げていない"
    return "ケースが指さないのに表に印を付けた" if PROVISIONAL_CELL in one else None


def provisional_resolved(repo: Path) -> str | None:
    """v1 で暫定だった Q-001 を v2 で確定した——v2 の変更の本文は印を持たない。"""
    found = bodies(repo)
    if list(found) != ["F-001"]:
        return f"本文を作るのは変えた機能だけのはず: {list(found)}"
    return unmarked(found["F-001"], "確定した後の変更の")


def provisional_cited_by_feature_only(ir: dict) -> None:
    ir["features"][0]["cases"][0].pop("qa")


def sections_in_order(body: str) -> bool:
    positions = [body.find(f"\n{s}\n") for s in ("## 仕様", "## 受入基準", "## Red テスト", "## Q&A の回答", "## 作らないもの", "## 仕様の穴を見つけたら")]
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
                           "python3 -m unittest discover -s scaffold/tests\n", "この機能が根拠にした Q&A は無い",
                           "## 作らないもの\n\n撤去の Issue なので、作るものは無い——消した機能の代わりを作らない。\n\n## 仕様の穴を見つけたら"),
                    "撤去")


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

# ---- 仕様の基準コミット（#874）。本文の `## 仕様` に、生成した時点の HEAD とその日時か、記録していないことを書く
BASE_LINE = "- 基準コミット: "


def spec_section(body: str) -> str:
    return body.split("\n## 仕様\n", 1)[-1].split("\n## 受入基準\n", 1)[0] if "\n## 仕様\n" in body else ""


def base_lines(body: str) -> list[str]:
    return [line for line in body.splitlines() if line.startswith(BASE_LINE)]


def base_recorded(kinds: tuple[str, ...]) -> Callable[[Path], str | None]:
    """どの本文も、`## 仕様` の中に基準コミットの行を 1 本だけ持ち、値が正本の HEAD とそのコミットの日時である。
    `kinds` は本文の変化の印にそろっているべき変化（試料が追加・変更・撤去を覆っていることを見る）。"""
    def post(repo: Path) -> str | None:
        found = bodies(repo)
        changes = sorted({m for body in found.values() for m in re.findall(r"<!-- spec-loop-change: (\w+);", body)})
        if changes != sorted(kinds):
            return f"試料の本文の変化が {sorted(kinds)} でない（試料が判別しない）: {changes}"
        head = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%H%n%cI", "HEAD"], capture_output=True,
                              text=True, env=GIT_ENV).stdout.split("\n")
        if len(head) < 2 or not re.fullmatch(r"[0-9a-f]{40}", head[0]) or not head[1]:
            return f"試料の HEAD を読めない: {head}"
        want = f"{BASE_LINE}`{head[0]}`（コミットの日時 {head[1]}。"
        for fid, body in found.items():
            lines = base_lines(body)
            if len(lines) != 1 or not lines[0].startswith(want):
                return f"{fid} の本文の基準コミットの行が HEAD とその日時でない: {lines}（期待 {want!r}）"
            if lines[0] not in spec_section(body).splitlines():
                return f"{fid} の本文の基準コミットの行が `## 仕様` の中に無い"
        return None
    return post


def base_unrecorded(reason: str) -> Callable[[Path], str | None]:
    """どの本文も、`## 仕様` の中に「記録していない（理由）」の行を 1 本だけ持つ。"""
    def post(repo: Path) -> str | None:
        found = bodies(repo)
        if not found:
            return "本文を作っていない"
        want = f"{BASE_LINE}記録していない（{reason}"
        for fid, body in found.items():
            lines = base_lines(body)
            if len(lines) != 1 or not lines[0].startswith(want) or lines[0] not in spec_section(body).splitlines():
                return f"{fid} の本文に `## 仕様` の中の {want!r} の行が 1 本だけ無い: {lines}"
        return None
    return post


def git_init_only(repo: Path) -> None:
    git_in(repo, "init", "-q")


CASES: list[Case] = [
    Case("作る", 0, "作った", post=files_written),
    Case("Red テストが失敗する", 0, post=expect_red(3)),
    Case("関数の無い実装でも失敗する", 0, impl=NO_FUNCTION_IMPL, post=expect_red(3)),
    Case("誤った実装で失敗する", 0, impl=WRONG_IMPL, post=expect_red(3)),
    Case("正しい実装で緑", 0, impl=GOOD_IMPL, post=expect_green),
    Case("型の違う実装で失敗する", 0, impl=WRONG_TYPE_IMPL, post=expect_red(2)),
    Case("本文から辿れる", 0, post=body_traceable),
    # #923: トレースのケース。陽性対照は排他で守る実装で緑、競合する実装で赤
    Case("トレース: 作る", 0, "作った", ir=traced(), extra=TRACE_FORMAL, post=trace_written),
    Case("トレース: 口の行はトレースのケースを持つ機能だけ", 0, "作った", ir=traced(), extra=TRACE_FORMAL, post=trace_kept_out),
    Case("トレース: 実装が無ければ失敗", 0, "作った", ir=traced(), extra=TRACE_FORMAL, post=expect_red(7)),
    Case("トレース: 正しい実装で緑", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=LOCKED_IMPL, post=expect_green),
    Case("トレース: 競合する実装で失敗", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=RACY_IMPL,
         post=expect_trace_red("結果が期待と違う")),
    Case("トレース: 口を呼ばない実装で失敗", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=SILENT_IMPL,
         post=expect_trace_red("checkpoint を呼ばない呼び出しがある")),
    Case("トレース: 口の引数を受け取らない実装で失敗", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=NO_KEYWORD_IMPL,
         post=expect_trace_red("TypeError")),
    Case("トレース: 状態を空に戻す関数が無ければ失敗", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=NO_RESET_IMPL,
         post=expect_trace_red("未実装: spec_impl.reset_state が無い")),
    # 在庫 2 を 2 つが 1 ずつ引き当てる——競合する実装は 2 つとも 2 を読んで 1 を書くので、結果は同じで後の状態だけが違う
    Case("トレース: 後の状態だけで確かめる", 0, "作った", ir=traced(after_only), extra=TRACE_FORMAL, impl=RACY_IMPL,
         post=expect_trace_red("get_stock({'item': 'a'}) が {'stock': 1} を返した")),
    Case("トレース: 後の状態だけで確かめる（正しい実装）", 0, "作った", ir=traced(after_only), extra=TRACE_FORMAL, impl=LOCKED_IMPL,
         post=expect_green),
    Case("トレース: --red-check が数える", 0, "失敗 1 件（追加・変更）", args=("--red-check",), generate_first=True,
         ir=traced(), extra=TRACE_FORMAL, impl=RACY_IMPL),
    Case("トレース: 性能テストに入れない", 0, "作った",
         ir=traced(lambda ir: ir["features"][2].update(nfr=["N-001"])), extra={**TRACE_FORMAL, **with_nfr()}, post=trace_perf),
    Case("トレース: v2 でトレースを変えたら変更", 0, "作った", ir=traced(),
         extra=v2_trace(lambda f: f["cases"][1]["trace"]["steps"].reverse()), post=trace_v2("F-003-C2", "変更")),
    Case("トレース: 一部の段にだけ口を呼ぶ実装で失敗", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=PARTIAL_IMPL,
         post=expect_trace_red("段 write の前で checkpoint を呼ばずに終わった")),
    Case("トレース: 段の名前を違える実装で失敗", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=RENAMED_STEPS_IMPL,
         post=expect_trace_red("段 read の前で checkpoint を呼ばずに終わった")),
    Case("トレース: v2 で呼ぶ入口の型だけ変えたら変更", 0, "作った", ir=traced(),
         extra={**TRACE_FORMAL, **v2([dict(copy.deepcopy(STOCK_FEATURES[2]), operation=dict(
             copy.deepcopy(STOCK_FEATURES[2]["operation"]), output={"stock": {"type": "number"}}))])},
         post=trace_called_moved),
    Case("トレース: 排他を分けた競合する実装で失敗", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=TOCTOU_IMPL,
         post=expect_trace_red("結果が期待と違う")),
    Case("トレース: 排他の前で口を呼ぶ正しい実装で緑", 0, "作った", ir=traced(), extra=TRACE_FORMAL, impl=PRELOCK_IMPL,
         post=expect_green),
    Case("トレース: v2 でキーの順だけ変えても Red テストは同じ", 0, "作った", ir=traced(), extra=TRACE_FORMAL,
         generate_first=True, pre=plant_reordered_v2, post=reordered_kept),
    Case("トレース: v2 でほかのケースだけ変えたら回帰", 0, "作った", ir=traced(),
         extra=v2_trace(lambda f: f["cases"][0]["input"].update(qty=-1)), post=trace_v2("F-003-C2", "回帰")),
    Case("トレース: 形式検査の記録が無い", 1, "F-003-C2.trace.formal: spec/formal/stock-reserve/README.md が無い", ir=traced(),
         pre=plant_old_issues, post=nothing_written),
    Case("トレース: 形式検査の対象の名前の形", 1, "F-003-C2.trace.formal: 形式検査の対象の名前の形に反する",
         ir=traced(lambda ir: trace_of(ir).update(formal="Stock_Reserve")), extra=TRACE_FORMAL),
    Case("トレース: 呼び出しが 1 つ", 1, "F-003-C2.trace.calls: 2 つ以上の呼び出しのオブジェクトでない",
         ir=traced(lambda ir: trace_of(ir)["calls"].pop("second")), extra=TRACE_FORMAL),
    Case("トレース: 入口が中間表現に無い", 1, "F-003-C2.trace.calls.second.operation: 中間表現の入口に無い: 'take'",
         ir=traced(lambda ir: trace_of(ir)["calls"]["second"].update(operation="take")), extra=TRACE_FORMAL),
    Case("トレース: 呼び出しの入力が型に反する", 1, "F-003-C2.trace.calls.first.input.qty: 型 integer でない",
         ir=traced(lambda ir: trace_of(ir)["calls"]["first"]["input"].update(qty="1")), extra=TRACE_FORMAL),
    Case("トレース: 前の呼び出しの期待が型に反する", 1, "F-003-C2.trace.setup[0].expected.stock: 型 integer でない",
         ir=traced(lambda ir: trace_of(ir)["setup"][0]["expected"].update(stock=True)), extra=TRACE_FORMAL),
    Case("トレース: 後の呼び出しの失敗が errors に無い", 1, "F-003-C2.trace.after[0].error: 入口 get_stock の errors に無い",
         ir=traced(lambda ir: (trace_of(ir)["after"][0].update(error="GONE"), trace_of(ir)["after"][0].pop("expected"))),
         extra=TRACE_FORMAL),
    Case("トレース: 段の呼び出しが calls に無い", 1, "F-003-C2.trace.steps[3]: 呼び出し 'third' が calls に無い",
         ir=traced(lambda ir: trace_of(ir)["steps"][3].__setitem__(0, "third")), extra=TRACE_FORMAL),
    Case("トレース: 段の名前の形", 1, "F-003-C2.trace.steps[0]: 段の名前の形に反する",
         ir=traced(lambda ir: trace_of(ir)["steps"][0].__setitem__(1, "Read")), extra=TRACE_FORMAL),
    Case("トレース: 段の形", 1, "F-003-C2.trace.steps[1]: [呼び出しの名前, 段の名前] の形でない",
         ir=traced(lambda ir: trace_of(ir)["steps"].__setitem__(1, "second.read")), extra=TRACE_FORMAL),
    Case("トレース: 段に出ない呼び出し", 1, "F-003-C2.trace.steps: 段に出ない呼び出しがある: second",
         ir=traced(lambda ir: trace_of(ir).update(steps=[["first", "read"], ["first", "write"]])), extra=TRACE_FORMAL),
    Case("トレース: 確かめるものが無い", 1, "F-003-C2.trace: outcomes と after のどちらも無い",
         ir=traced(lambda ir: (trace_of(ir).pop("outcomes"), trace_of(ir).pop("after"))), extra=TRACE_FORMAL),
    Case("トレース: 結果の数が呼び出しの数と違う", 1, "F-003-C2.trace.outcomes: 呼び出しの数と同じ長さの配列でない",
         ir=traced(lambda ir: trace_of(ir)["outcomes"].pop()), extra=TRACE_FORMAL),
    Case("トレース: 結果がどの入口の形にも合わない", 1,
         "F-003-C2.trace.outcomes[1]: どの呼び出しの入口の出力（か errors）の形にも合わない",
         ir=traced(lambda ir: trace_of(ir)["outcomes"].__setitem__(1, {"error": "GONE"})), extra=TRACE_FORMAL),
    Case("トレース: 入力に口と同じ名前の項目", 1, "F-003-C2.trace.calls.first: 入口 reserve の入力に項目 `checkpoint` がある",
         ir=traced(lambda ir: (ir["features"][2]["operation"]["input"].update(checkpoint={"type": "boolean"}),
                               ir["features"][2]["cases"][0]["input"].update(checkpoint=False),
                               [c["input"].update(checkpoint=False) for c in trace_of(ir)["calls"].values()])),
         extra=TRACE_FORMAL),
    Case("トレース: 口と同じ名前の入口", 1, "入口の名前 `reset_state` は、トレースのケースが実装に求める口",
         ir=traced(lambda ir: (ir["features"][3]["operation"].update(id="reset_state"),
                               [c.update(operation="reset_state") for c in trace_of(ir)["setup"]])), extra=TRACE_FORMAL),
    Case("トレース: 入出力と一緒に書く", 1, "F-003.cases[1]: 決まりに無いキー `input`",
         ir=traced(lambda ir: ir["features"][2]["cases"][1].update(input={"item": "a", "qty": 1})), extra=TRACE_FORMAL),
    Case("トレース: 入出力のケースが無い機能", 1, "F-003.cases: 入出力のケース（`trace` でないもの）が 1 つも無い",
         ir=traced(lambda ir: ir["features"][2]["cases"].pop(0)), extra=TRACE_FORMAL),
    # #851: 作らないもの
    Case("作らないもの: 範囲の外の行と次の版の候補を写す", 0, "作った", ir=OUT_OF_SCOPE_IR, spec=SCOPE_SPEC, post=not_built_copied),
    Case("作らないもの: 節に無い行", 1, "F-001.out_of_scope: 範囲の文書の「範囲の外」の節に、この行が原文のまま無い",
         ir=out_of_scope([SCOPE_ROWS[0], "| ディスクがいっぱい | 失敗を見せない | 既定の線 |"]), spec=SCOPE_SPEC,
         pre=plant_old_issues, post=nothing_written),
    Case("作らないもの: 節の外の行", 1, "この行が原文のまま無い（表の見出し・区切りの行は挙げない）: '| 付録の行 | 原則 | 根拠 |'",
         ir=out_of_scope(["| 付録の行 | 原則 | 根拠 |"]), spec=SCOPE_SPEC),
    Case("作らないもの: 表の見出しの行を挙げる", 1, "この行が原文のまま無い（表の見出し・区切りの行は挙げない）: '| 場面 | 原則 | 根拠 |'",
         ir=out_of_scope(["| 場面 | 原則 | 根拠 |"]), spec=SCOPE_SPEC),
    Case("作らないもの: 表の区切りの行を挙げる", 1, "この行が原文のまま無い（表の見出し・区切りの行は挙げない）: '| --- | --- | --- |'",
         ir=out_of_scope(["| --- | --- | --- |"]), spec=SCOPE_SPEC),
    # 先頭の | の無い表も表と読む——見出しの 2 行は挙げられず、行には見出しの 2 行が付く（#851 の /code-review 1 パス目）
    Case("作らないもの: 先頭の | の無い表", 0, "作った", ir=out_of_scope(["外貨 | 円だけ"]),
         spec={"order.md": SPEC, "scope.md": PIPELESS_SCOPE_MD}, post=pipeless_copied),
    # 単独の `---`（水平線）は表の区切りではない——前の `|` を含む行を表の見出しと読まない（#851 の /code-review 2 パス目）
    Case("作らないもの: 水平線の前の | を含む行", 0, "作った", ir=out_of_scope(["- 外貨（円|ドル）は受けない"]),
         spec={"order.md": SPEC, "scope.md": "# 範囲\n\n## 範囲の外\n\n- 外貨（円|ドル）は受けない\n---\n- 別の行\n"}),
    Case("作らないもの: 先頭の | の無い表の見出しを挙げる", 1, "この行が原文のまま無い（表の見出し・区切りの行は挙げない）: '場面 | 原則'",
         ir=out_of_scope(["場面 | 原則"]), spec={"order.md": SPEC, "scope.md": PIPELESS_SCOPE_MD}),
    Case("作らないもの: 見出しの行を挙げる", 1, "この行が原文のまま無い（表の見出し・区切りの行は挙げない）: '### 補足'",
         ir=out_of_scope(["### 補足"]), spec=SCOPE_SPEC),
    Case("作らないもの: 範囲の文書が無い", 1, "F-001.out_of_scope: 範囲の文書 build/merged/spec/scope.md が無い",
         ir=out_of_scope([SCOPE_ROWS[0]])),
    Case("作らないもの: 範囲の外の節が無い", 1, "見出しに「範囲の外」を含む節が無い", ir=out_of_scope([SCOPE_ROWS[0]]),
         spec={"order.md": SPEC, "scope.md": "# 範囲\n\n## 線\n\n既定の線\n"}),
    Case("作らないもの: 空の配列", 1, "F-001.out_of_scope: 範囲の外の行の原文の 1 つ以上の配列でない", ir=out_of_scope([]),
         spec=SCOPE_SPEC),
    Case("作らないもの: 配列でない", 1, "F-001.out_of_scope: 範囲の外の行の原文の 1 つ以上の配列でない",
         ir=out_of_scope(SCOPE_ROWS[0]), spec=SCOPE_SPEC),
    Case("作らないもの: 重複", 1, "F-001.out_of_scope: 重複している", ir=out_of_scope([SCOPE_ROWS[0], SCOPE_ROWS[0]]),
         spec=SCOPE_SPEC),
    Case("作らないもの: 複数行", 1, "F-001.out_of_scope: 前後に空白の無い 1 行の文字列でない行がある",
         ir=out_of_scope([SCOPE_ROWS[0] + "\n" + SCOPE_ROWS[2]]), spec=SCOPE_SPEC),
    Case("作らないもの: 前後に空白", 1, "F-001.out_of_scope: 前後に空白の無い 1 行の文字列でない行がある",
         ir=out_of_scope([" " + SCOPE_ROWS[0]]), spec=SCOPE_SPEC),
    # #852: 性能の要求。行があれば性能テストと予算、無ければ「要求なし」（基準の試料の本文は body_traceable が見る）
    Case("性能の要求: 行があれば性能テストと予算", 0, "作った", ir=nfr(["N-001"]), extra=with_nfr(), post=budget_copied),
    Case("性能の要求: 性能テストが上限と比べる", 0, "作った", ir=nfr(["N-002"]), extra=with_nfr(), post=budget_compared),
    Case("性能の要求: nfr を外すと性能テストを消す", 0, "作った", ir=nfr(["N-001"]), extra=with_nfr(), generate_first=True,
         pre=drop_nfr, post=perf_removed),
    Case("性能の要求: nfr を外した --check", 1, "scaffold/perf/perf_f_001.py: 性能の要求（nfr）を指す機能に無い性能テストが残っている",
         args=("--check",), ir=nfr(["N-001"]), extra=with_nfr(), generate_first=True, pre=drop_nfr),
    Case("性能の要求: 性能テストを手で直した --check", 1, "perf_f_001.py: 今の入力から作るものと違う", args=("--check",),
         ir=nfr(["N-001"]), extra=with_nfr(), generate_first=True,
         pre=lambda repo: (repo / PERF_FILE).write_text((repo / PERF_FILE).read_text(encoding="utf-8").replace("300", "3000"),
                                                        encoding="utf-8")),
    Case("性能の要求: v2 で nfr を足す", 0, "作った", extra={**with_nfr(), **v2([{**copy.deepcopy(IR["features"][0]), "nfr": ["N-001"]}])},
         post=nfr_added_in_v2),
    Case("性能の要求: 表が無い", 1, "F-001.nfr: 性能の要求の表 build/merged/shared/nfr.csv が無い", ir=nfr(["N-001"]),
         pre=plant_old_issues, post=nothing_written),
    Case("性能の要求: 行が無い", 1, "F-001.nfr: 性能の要求の表 build/merged/shared/nfr.csv に N-009 の行が無い",
         ir=nfr(["N-009"]), extra=with_nfr()),
    Case("性能の要求: 同じ No が 2 行", 1, "に N-001 の行が 2 行ある", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV + NFR_ROWS[0] + "\n")),
    Case("性能の要求: 見出しが違う", 1, "の見出しの行が No,対象,指標,上限,単位,条件,根拠 でない", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV.replace("根拠", "理由", 1))),
    Case("性能の要求: 性能でない行を指す", 1, "F-001.nfr: N-003: 指標が p50・p95・p99・最大 のどれでもない: '稼働率'",
         ir=nfr(["N-003"]), extra=with_nfr()),
    Case("性能の要求: 上限が 0", 1, "F-001.nfr: N-001: 上限が正の数の形でない（整数部は先頭に 0 を付けない 9 桁まで・小数部は 6 桁まで）: '0'", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV.replace(",p95,300,", ",p95,0,", 1))),
    Case("性能の要求: 上限の先頭に 0", 1, "F-001.nfr: N-001: 上限が正の数の形でない（整数部は先頭に 0 を付けない 9 桁まで・小数部は 6 桁まで）: '0300'", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV.replace(",p95,300,", ",p95,0300,", 1))),
    Case("性能の要求: 上限の桁が多い", 1, "上限が正の数の形でない（整数部は先頭に 0 を付けない 9 桁まで・小数部は 6 桁まで）: '1234567890'",
         ir=nfr(["N-001"]), extra=with_nfr(NFR_CSV.replace(",p95,300,", ",p95,1234567890,", 1))),
    Case("性能の要求: 表の名前の綴りが違う", 1, "F-001.nfr: 性能の要求の表 build/merged/shared/nfr.csv が無い", ir=nfr(["N-001"]),
         extra={str(V1 / "shared" / "NFR.csv"): NFR_CSV}),
    Case("性能の要求: 上限が数でない", 1, "F-001.nfr: N-001: 上限が正の数の形でない（整数部は先頭に 0 を付けない 9 桁まで・小数部は 6 桁まで）: '300ms'", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV.replace(",p95,300,", ",p95,300ms,", 1))),
    Case("性能の要求: 単位が ms でない", 1, "F-001.nfr: N-001: 単位が ms でない: '秒'", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV.replace(",300,ms,", ",300,秒,", 1))),
    Case("性能の要求: 根拠が空", 1, "F-001.nfr: N-001: 根拠 が空か、1 行でない", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV.replace(",2025 年末のピークが 42 req/s", ",", 1))),
    Case("性能の要求: 条件が空", 1, "F-001.nfr: N-001: 条件 が空か、1 行でない", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV.replace(",ピーク 50 req/s,", ",,", 1))),
    Case("性能の要求: 列が多い", 1, "F-001.nfr: N-001: 列の数が見出しと違う（8 列）", ir=nfr(["N-001"]),
         extra=with_nfr(NFR_CSV.replace("42 req/s", "42 req/s,余り", 1))),
    Case("性能の要求: 空の配列", 1, "F-001.nfr: 性能の要求の行の No の 1 つ以上の配列でない", ir=nfr([]), extra=with_nfr()),
    Case("性能の要求: 配列でない", 1, "F-001.nfr: 性能の要求の行の No の 1 つ以上の配列でない", ir=nfr("N-001"), extra=with_nfr()),
    Case("性能の要求: No の形", 1, "F-001.nfr: No の形に反する（N- に 3 桁以上の数字）: 'N-1'", ir=nfr(["N-1"]), extra=with_nfr()),
    Case("性能の要求: 重複", 1, "F-001.nfr: 重複している", ir=nfr(["N-001", "N-001"]), extra=with_nfr()),
    Case("作らないもの: 文字列でない", 1, "F-001.out_of_scope: 前後に空白の無い 1 行の文字列でない行がある",
         ir=out_of_scope([1]), spec=SCOPE_SPEC),
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
    # #875: 利用者が仮回答のまま渡すと決めたとき（--provisional）だけ通し、依存する本文と受入基準に印を付ける
    Case("--provisional で暫定反映を指す", 0, "仮回答（暫定反映）に依存する本文 1 件（F-001）", args=("--provisional",),
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, post=provisional_marked),
    Case("--provisional で暫定反映を機能だけが指す", 0, args=("--provisional",), qa=HEADER + QA_PROVISIONAL + QA_DONE2,
         ir=edit(provisional_cited_by_feature_only), post=provisional_feature_only),
    Case("--provisional でも指していない暫定反映は止める", 1,
         "Q-004: 状態が 暫定反映（利用者の確認待ち）なのに、中間表現のどの機能・ケースの qa からも指していない",
         args=("--provisional",), qa=HEADER + QA_DONE + QA_DONE2 + QA_PROVISIONAL_UNCITED, pre=plant_old_issues,
         post=nothing_written),
    Case("--provisional --dry-run でも指していない暫定反映は止める", 1, "指していない 暫定反映 の行が 1 件残る",
         args=("--provisional", "--dry-run"), qa=HEADER + QA_PROVISIONAL + QA_DONE2 + QA_PROVISIONAL_UNCITED),
    Case("--provisional --dry-run", 0, "作れる", args=("--provisional", "--dry-run"), qa=HEADER + QA_PROVISIONAL + QA_DONE2,
         post=nothing_written),
    Case("--provisional でも確認中は止める", 1, "Q-003", args=("--provisional",),
         qa=HEADER + QA_PROVISIONAL + QA_DONE2 + QA_OPEN, post=nothing_written),
    Case("--provisional の印は依存しない本文を変えない", 0, args=("--provisional",), post=lambda repo: (
        unmarked(bodies(repo).get("F-001", ""), "暫定反映の無い F-001 ") or unmarked(bodies(repo).get("F-002", ""), "F-002 "))),
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
    # 2 つ目以降の部も見る（#219 の狭いパス N1・N2。#291）——最初の部だけの試料では、部ごとの検査と予約語の検査を外しても緑だった
    Case("実装のモジュールの 2 つ目の部の形", 1, "impl_module がモジュール名の形に反する",
         ir=edit(lambda ir: ir.update(impl_module="a.Bad-Name"))),
    Case("実装のモジュールの予約語の部", 1, "impl_module がモジュール名の形に反する",
         ir=edit(lambda ir: ir.update(impl_module="a.class"))),
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
    # 形式検査のモデル（spec/formal/）も check-spec-exit.py が走査しない——出所にすると未決定の印が素通りする（#908 の V1・CR2）
    Case("形式検査のモデルを出所にする", 1, "形式検査のモデル（spec/formal/）の中にある",
         extra={"docs/v1/spec/formal/order/README.md": SPEC + "上限は TBD。\n"},
         ir=edit(lambda ir: f1(ir).update(source=["spec/formal/order/README.md"]))),
    # 陽性対照: 接頭辞だけ同じ spec/formalx.md は仕様の原文として通す（印が無いので作れる）
    Case("接頭辞だけ同じファイルを出所にする", 0, "作った", extra={"docs/v1/spec/formalx.md": SPEC},
         ir=edit(lambda ir: f1(ir).update(source=["spec/order.md", "spec/formalx.md"]))),
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
    # ---- null を許す項目（#487）
    Case("null を許す項目を書かない生成物は変わらない", 0, post=unchanged_without_nullable),
    Case("null を許す項目", 0, "作った", ir=edit(with_nullable), post=nullable_shape),
    Case("null を許す項目の Red テストが失敗する", 0, ir=edit(with_nullable), post=expect_red(5)),
    Case("null を返す正しい実装で緑", 0, ir=edit(with_nullable), impl=NULLABLE_IMPL, post=expect_green),
    Case("null を許す整数の項目に真偽値を返す実装で失敗する", 0, ir=edit(with_nullable), impl=NULLABLE_BOOL_IMPL,
         post=expect_red(1)),
    Case("nullable が false", 1, "`nullable` は true だけを書く",
         ir=edit(lambda ir: (with_nullable(ir), f3(ir)["operation"]["output"]["label"].update(nullable=False)))),
    Case("nullable が文字列", 1, "`nullable` は true だけを書く",
         ir=edit(lambda ir: (with_nullable(ir), f3(ir)["operation"]["output"]["label"].update(nullable="yes")))),
    Case("null を許さない出力に null を期待する", 1, "expected.count: 型 integer でない（null）",
         ir=edit(lambda ir: (with_nullable(ir), f3(ir)["cases"][1]["expected"].update(count=None)))),
    Case("null を許さない enum の入力に null を書く", 1, "input.rank: 型 string でない（null）",
         ir=edit(lambda ir: f1(ir)["cases"][0]["input"].update(rank=None))),
    Case("null を許す enum の入力に enum に無い値", 1, "input.kind: enum に無い値（\"c\"）",
         ir=edit(lambda ir: (with_nullable(ir), f3(ir)["cases"][0]["input"].update(kind="c")))),
    Case("null を許す項目に型の違う値", 1, "expected.label: 型 string でない（1）",
         ir=edit(lambda ir: (with_nullable(ir), f3(ir)["cases"][0]["expected"].update(label=1)))),
    Case("パスの変数を nullable にする", 1, "パスの変数 {note} は nullable にできない",
         ir=edit(lambda ir: (with_nullable(ir), f3(ir)["operation"].update(path="/orders/label/{note}")))),
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
    # #874: 仕様の基準コミット。git のリポジトリなら HEAD とその日時を、追加・変更・撤去のどの本文にも書く
    Case("基準コミット: 追加の本文", 0, "作った", pre=release(None), post=base_recorded(("add",)),
         absent="基準コミットを記録していない"),
    Case("基準コミット: 変更と撤去の本文", 0, "作った", pre=release(None),
         extra=v2([V2_CHANGED], removed="機能,F-002,取り消しはやめる\n"), post=base_recorded(("modify", "remove")),
         absent="基準コミットを記録していない"),
    # 記録できなくても止めない——本文に「記録していない（理由）」と書き、出力でも知らせる
    Case("基準コミット: git の作業ツリーでない", 0, "基準コミットを記録していない（正本リポジトリが git の作業ツリーでない",
         post=base_unrecorded("正本リポジトリが git の作業ツリーでない）")),
    # 根でなければ外側のリポジトリの HEAD を書かない（`released` と同じ。#874 の 1 パス目）
    Case("基準コミット: git の作業ツリーの根でない", 0, "基準コミットを記録していない（正本リポジトリが git の作業ツリーの根でない",
         pre=release(None, top=".."), post=base_unrecorded("正本リポジトリが git の作業ツリーの根でない）")),
    # 環境変数 GIT_DIR が別の場所を指していても、正本の HEAD を書く（フックの中。#874 の 1 パス目）
    Case("基準コミット: GIT_DIR が別を指す", 0, "作った", pre=release(None), env={"GIT_DIR": "/nonexistent-874/.git"},
         post=base_recorded(("add",)), absent="基準コミットを記録していない"),
    # 記録した行も決定論（同じ HEAD から同じバイト）
    Case("決定論的（基準コミットを記録する）", 0, pre=release(None), post=deterministic),
    Case("基準コミット: コミットが無い", 0, "基準コミットを記録していない（正本リポジトリの HEAD のコミットを読めない",
         pre=git_init_only, post=base_unrecorded("正本リポジトリの HEAD のコミットを読めない（コミットが無い）")),
    Case("基準コミット: git を起動できない", 0, "基準コミットを記録していない（git を起動できない",
         env={"PATH": ""}, post=base_unrecorded("git を起動できない")),
    # #851: out_of_scope を足すだけでも機能は変更になる（ケースは全部 回帰）。本文の作らないものに写る
    Case("v2 で作らないものだけ足す", 0, "modify 1", spec=SCOPE_SPEC,
         extra=v2([{**copy.deepcopy(IR["features"][0]), "out_of_scope": [SCOPE_ROWS[0]]}]), post=not_built_added_in_v2),
    # #855: 課題一覧（案）。案は入口の機能ごと・未決定事項・受入基準の雛形・作らないもの
    Case("課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの", 0, "課題一覧（案）: build/scaffold/issues/proposals.md（案 2 件・未決定事項 4 件）",
         ir=BRANCHES_IR, spec=BRANCH_SPECS, post=proposals_written),
    Case("課題一覧（案）: branches を書いていなければ全部の分岐が未決定", 0, "（案 2 件・未決定事項 16 件）", post=proposals_unwritten),
    Case("課題一覧（案）: 呼ばれる関数には案を作らない", 0, "（案 1 件・未決定事項 8 件）", ir=CALLED, post=proposals_entry_only),
    Case("課題一覧（案）: v2 で機能を消すだけなら案は無い", 0, "（案 0 件・未決定事項 0 件）",
         extra=v2([], removed="機能,F-002,取り消しはやめる\n"), post=proposals_none),
    # impl_module だけ変えると全部の機能が変更（modify）になるが、結線の課題は変わっていない（1 パス目の /code-review）
    Case("課題一覧（案）: v2 で impl_module だけ変えても案は無い", 0, "（案 0 件・未決定事項 0 件）",
         extra=v2([], top={"impl_module": "app_impl"}), post=proposals_none),
    Case("課題一覧（案）: どの分岐も該当なし", 0, "（案 2 件・未決定事項 8 件）", spec={"order.md": ALL_NONE_SPEC},
         ir=branches({name: {"none": f"- {name}: 該当なし"} for name in ALL_BRANCHES}), post=proposals_all_none),
    Case("課題一覧（案）: v2 で branches だけ足す", 0, "modify 1", spec=BRANCH_SPECS,
         extra=v2([{**copy.deepcopy(IR["features"][0]), "branches": {"入力が欠ける": {"shows": BRANCH_LINES[0]}}}]),
         post=proposals_modified),
    Case("呼ぶ側の分岐: 呼ばれる関数に書く", 1, "F-001.branches: 呼ばれる関数（called_by を持つ機能）には書かない",
         ir=edit(lambda ir: (f1(ir).update(called_by=["F-002"], branches={"none": BRANCH_LINES[4]}))), spec=BRANCH_SPECS,
         pre=plant_old_issues, post=nothing_written_issues),
    Case("呼ぶ側の分岐: オブジェクトでない", 1, "F-001.branches: 分岐の名前から", ir=branches([BRANCH_LINES[0]]),
         spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 空", 1, "F-001.branches: 分岐の名前から", ir=branches({}), spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 分岐の名前でない", 1, "F-001.branches: 分岐の名前でない（入力が欠ける / ", ir=branches({"通信が切れる": {"shows": BRANCH_LINES[0]}}),
         spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: shows と none を両方書く", 1, "F-001.branches.入力が欠ける: {\"shows\": 原文} か {\"none\": 原文} のどちらか 1 つでない",
         ir=branches({"入力が欠ける": {"shows": BRANCH_LINES[0], "none": BRANCH_LINES[3]}}), spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 値の鍵が違う", 1, "F-001.branches.入力が欠ける: {\"shows\": 原文} か {\"none\": 原文} のどちらか 1 つでない",
         ir=branches({"入力が欠ける": {"show": BRANCH_LINES[0]}}), spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 行ごとの該当なしと分岐を混ぜる", 1, "F-001.branches: 行ごとの該当なし（none）と分岐を一緒に書いている",
         ir=branches({"none": BRANCH_LINES[4], "入力が欠ける": {"shows": BRANCH_LINES[0]}}), spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 原文に無い行", 1, "F-001.branches.入力が遅れる.shows: 仕様の原文（source）に、この行が原文のまま無い: '- 入力が遅れる: 「待機中」と表示する'",
         ir=branches({"入力が遅れる": {"shows": "- 入力が遅れる: 「待機中」と表示する"}}), spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 行ごとの該当なしが原文に無い", 1, "F-001.branches.none: 仕様の原文（source）に、この行が原文のまま無い",
         ir=branches({"none": "該当なし"}), spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 複数行", 1, "F-001.branches.入力が欠ける.shows: 前後に空白の無い 1 行の文字列でない",
         ir=branches({"入力が欠ける": {"shows": BRANCH_LINES[0] + "\n" + BRANCH_LINES[1]}}), spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 前後に空白", 1, "F-001.branches.入力が欠ける.shows: 前後に空白の無い 1 行の文字列でない",
         ir=branches({"入力が欠ける": {"shows": " " + BRANCH_LINES[0]}}), spec=BRANCH_SPECS),
    Case("呼ぶ側の分岐: 文字列でない", 1, "F-001.branches.none: 前後に空白の無い 1 行の文字列でない",
         ir=branches({"none": 1}), spec=BRANCH_SPECS),
    # 原文の行は前後の空白を落として比べる（表の行の前後の空白・別の source のファイルの行）
    Case("呼ぶ側の分岐: 別の source の原文", 0, "（案 2 件・未決定事項 15 件）",
         ir=edit(lambda ir: f1(ir).update(source=["spec/order.md", "spec/wire.md"],
                                         branches={"量が重なる": {"shows": "二重送信は 1 件に寄せて「受け付けた」と表示する"}})),
         spec={"order.md": SPEC, "wire.md": "# 結線\n\n二重送信は 1 件に寄せて「受け付けた」と表示する\n"}),
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
    # #609: 呼ばれる機能（called_by）
    Case("呼ばれる機能", 0, "作った", ir=CALLED, post=callers_in_issue, absent="呼ぶ機能（"),
    Case("呼ぶ機能が中間表現に無い", 1, "F-001.called_by: 呼ぶ機能 F-009 が中間表現に無い", ir=called(["F-009"])),
    Case("呼ぶ機能が空の配列", 1, "F-001.called_by: 呼ぶ機能の id の 1 つ以上の配列でない", ir=called([])),
    Case("呼ぶ機能が配列でない", 1, "F-001.called_by: 呼ぶ機能の id の 1 つ以上の配列でない", ir=called("F-002")),
    Case("呼ぶ機能の id の形", 1, "F-001.called_by: id の形に反する", ir=called(["F-2"])),
    Case("呼ぶ機能が自分自身", 1, "F-001.called_by: 自分自身 F-001", ir=called(["F-001"])),
    Case("呼ぶ機能の重複", 1, "F-001.called_by: 重複している", ir=called(["F-002", "F-002"])),
    Case("呼ぶ関係の循環", 1, "呼ぶ関係が循環している",
         ir=edit(lambda ir: (f1(ir).update(called_by=["F-002"]), ir["features"][1].update(called_by=["F-001"])))),
    # #876: まとめた本文（--bundle）と依存の連鎖（depends）
    Case("まとめた本文", 0, "--bundle で 2 件の機能を 1 件の本文にまとめ、登録する本文は 2 件", ir=THREE,
         args=("--bundle", "F-002,F-001"), post=bundled),
    Case("まとめても他の本文は既定と同じ", 0, "作った", ir=THREE, args=("--bundle", "F-001,F-002"), post=bundle_keeps_others),
    Case("まとめる --dry-run は書かない", 0, "登録する本文は 2 件", ir=THREE, args=("--dry-run", "--bundle", "F-001,F-002"),
         pre=plant_old_issues, post=old_issues_kept),
    Case("依存の連鎖", 0, "作った", ir=CALLED, post=depends_written, absent="--bundle で"),
    Case("まとめた組の依存", 0, "作った", ir=CHAIN, args=("--bundle", "F-002,F-003"), post=bundle_depends),
    Case("まとめると依存が循環する", 2, "--bundle でまとめると依存が循環する", ir=CHAIN, args=("--bundle", "F-001,F-003"),
         pre=plant_old_issues, post=nothing_written_issues),
    Case("まとめる機能が 1 件", 2, "まとめるには機能を 2 件以上並べる", args=("--bundle", "F-001"),
         pre=plant_old_issues, post=nothing_written_issues),
    Case("まとめる機能の id の形", 2, "機能の id（F- に 3 桁以上の数字）をカンマで区切って並べる", args=("--bundle", "F-001, F-002"),
         pre=plant_old_issues, post=nothing_written_issues),
    Case("まとめる機能の重複", 2, "同じ機能を 2 度並べている", ir=THREE, args=("--bundle", "F-001,F-002", "--bundle", "F-002,F-003"),
         pre=plant_old_issues, post=nothing_written_issues),
    Case("まとめる機能が無い", 2, "F-009 はこの版で本文を作る機能でない", args=("--bundle", "F-001,F-009"),
         pre=plant_old_issues, post=nothing_written_issues),
    Case("まとめる機能が変わっていない", 2, "F-002 はこの版で本文を作る機能でない", extra=v2([V2_CHANGED]),
         args=("--bundle", "F-001,F-002")),
    Case("まとめる機能の変化が揃わない", 2, "変化が揃わない（F-001 は modify・F-003 は add）",
         extra=v2([V2_CHANGED, V2_RETURN]), args=("--bundle", "F-001,F-003")),
    Case("まとめるのは --check と一緒に使えない", 2, "--bundle は書く生成か --dry-run と一緒にだけ使う",
         args=("--check", "--bundle", "F-001,F-002")),
    Case("v2 で呼ばれる機能だけ変える", 0, CALLERS_NOTICE, ir=CALLED, extra=v2([V2_CALLED])),
    Case("v2 で呼ぶ機能も変える", 0, "modify 2", ir=CALLED, extra=v2([V2_CALLED, V2_CALLER]), absent="呼ぶ機能（"),
    Case("v2 で呼ぶ機能を消す", 1, "F-001.called_by: 呼ぶ機能 F-002 が中間表現に無い", ir=CALLED,
         extra=v2([], removed="機能,F-002,取り消しはやめる\n")),
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
    # #875: 前の版を --provisional で作っていれば、前の版の暫定反映は崩れではない
    Case("--provisional で前の版の暫定反映を確定する", 0, args=("--provisional",),
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE), post=provisional_resolved),
    # 1 パス目の指摘: 前の版で指されない暫定の行は、旗があっても前の版を作れていない（#335 の形を戻さない）
    Case("--provisional でも前の版の指されない暫定反映は崩れ", 1, "v1 の時点の Q-004: 状態が 暫定反映",
         args=("--provisional",), qa=HEADER + QA_DONE + QA_DONE2 + QA_PROVISIONAL_UNCITED,
         extra=v2([V2_CHANGED], qa=HEADER + QA_PROVISIONAL_UNCITED.replace("暫定反映", "反映済み")), post=nothing_written_issues),
    # 1 パス目の指摘: 撤去の本文には仮回答の印を付けない
    Case("--provisional の撤去の本文に印を付けない", 0, args=("--provisional",), qa=HEADER + QA_PROVISIONAL + QA_DONE2,
         ir=edit(lambda ir: ir["features"][1].__setitem__("qa", ["Q-001"])),
         extra=v2([], removed="機能,F-002,取り消しはやめる\n"),
         post=lambda repo: unmarked(bodies(repo).get("F-002", "（撤去の本文が無い）" + PROVISIONAL_LINE), "撤去の")),
    # 2 パス目の指摘: 残るのが前の版の中間表現が指す暫定の行だけなら、旗を付けて作る道があると言う
    Case("前の版を --provisional で作ったときの案内", 1, "v1 を --provisional で作ったなら、利用者のその指示のもとで --provisional を付けて作る",
         qa=HEADER + QA_PROVISIONAL + QA_DONE2, extra=v2([V2_CHANGED], qa=HEADER + QA_DONE)),
    Case("前の版を作れていないときは旗の案内を出さない", 1, "v1 の scaffold は作れていない", absent="--provisional を付けて作る",
         qa=HEADER + QA_DONE + QA_DONE2 + QA_PROVISIONAL_UNCITED, extra=v2([V2_CHANGED])),
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
    # null を許すようにしただけ（期待は同じ）——前の版の実装はどのケースも緑のまま（#487）
    Case("Red の状態: v2 で出力に null を許す", 0, "失敗 0 件（追加・変更）・緑 3 件（回帰）", args=("--red-check",),
         generate_first=True, extra=v2([V2_NULLABLE]), impl=GOOD_IMPL),
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
    # #923: トレースのケース
    ("トレースの形式検査の記録を見ない", "        elif not (whole / versions.FORMAL_DIR / formal / FORMAL_RECORD).is_file():",
     "        elif False:", "トレース: 形式検査の記録が無い"),
    ("段の呼び出しを calls と照らさない", "                if calls is not None and who not in calls:", "                if False:",
     "トレース: 段の呼び出しが calls に無い"),
    ("段に出ない呼び出しを見ない", "            if calls is not None and [who for who in calls if who not in seen]:", "            if False:",
     "トレース: 段に出ない呼び出し"),
    ("確かめるものの無いトレースを通す", '    if "outcomes" not in trace and "after" not in trace:', "    if False:",
     "トレース: 確かめるものが無い"),
    ("口と同じ名前の入口を通す", "    if traced and RESET in operation_ids:", "    if False:", "トレース: 口と同じ名前の入口"),
    ("口と同じ名前の入力の項目を通す", '    if not result and CHECKPOINT in op_fields(op, "input"):', "    if False:",
     "トレース: 入力に口と同じ名前の項目"),
    ("入出力のケースの無い機能を通す",
     "        if isinstance(cases, list) and cases and all(isinstance(c, dict) and TRACE in c for c in cases):",
     "        if False:", "トレース: 入出力のケースが無い機能"),
    ("結果の数を呼び出しの数と比べない", "        if not isinstance(outcomes, list) or (calls is not None and len(outcomes) != len(calls)):",
     "        if not isinstance(outcomes, list):", "トレース: 結果の数が呼び出しの数と違う"),
    ("順を強制しない", '    "            for who, name in self.steps:",', '    "            for who, name in []:",',
     "トレース: 競合する実装で失敗"),
    ("口を呼ばない呼び出しを通す", '        "        if silent:",', '        "        if False:",', "トレース: 口を呼ばない実装で失敗"),
    ("トレースの結果を比べない", '        "        if \\"outcomes\\" in trace:",', '        "        if False:",', "トレース: 競合する実装で失敗"),
    ("トレースの後の状態を比べない", '        "        for call in trace.get(\\"after\\", []):",', '        "        for call in []:",',
     "トレース: 後の状態だけで確かめる"),
    ("v2 でトレースの変化を見ない", "        return impl_module, TRACE, literal(canonical(case[TRACE]))", "        return impl_module, TRACE",
     "トレース: v2 でトレースを変えたら変更"),
    ("性能テストにトレースのケースを入れる", '    inputs = [case["input"] for case in plain_cases(feature)]',
     '    inputs = [case.get("input") for case in sorted(feature["cases"], key=case_order)]', "トレース: 性能テストに入れない"),
    ("本文に口の行を書かない", '"（結果で書かない分岐でも呼ぶ。段を飛ばす・違う名前で呼ぶと失敗）"] if any(is_trace(c) for c in feature["cases"]) else []),',
     '"（結果で書かない分岐でも呼ぶ。段を飛ばす・違う名前で呼ぶと失敗）"] if False else []),', "トレース: 作る"),
    ("段を飛ばした呼び出しを通す", '        "        if schedule.strayed:",', '        "        if False:",', "トレース: 一部の段にだけ口を呼ぶ実装で失敗"),
    ("段に来ずに終わった呼び出しを記録しない", '    "                    self.strayed = (who, name, self.at.get(who))",',
     '    "                    pass",', "トレース: 段の名前を違える実装で失敗"),
    ("トレースが呼ぶ入口の型の変化を見ない", "                if key in old and key not in moved and f == old[key] and trace_moved(f, ops_before, ops_now)]",
     "                if False]", "トレース: v2 で呼ぶ入口の型だけ変えたら変更"),
    ("本文の口の行に setup・after だけの入口も挙げる", '               + "・".join(f"`{name}`" for name in concurrent_operations(feature))',
     '               + "・".join(f"`{name}`" for name in traced_operations(feature))', "トレース: 作る"),
    ("トレースのキーを並べ替えない", "        return {key: canonical(value[key]) for key in sorted(value)}",
     "        return {key: canonical(value[key]) for key in value}", "トレース: v2 でキーの順だけ変えても Red テストは同じ"),
    ("トレースの無い機能にも順の強制を足す", '    traced = any(is_trace(case) for case in feature["cases"])',
     "    traced = True", "トレース: 作る"),
    # #876: まとめた本文（--bundle）と依存の連鎖（depends）
    ("まとめない", "        if len(group) == 1:\n", "        if True:\n", "まとめた本文"),
    ("機能の一覧をタスクリストにする", 'f"- `{c.feature[\'id\']}` {cell(', 'f"- [ ] `{c.feature[\'id\']}` {cell(', "まとめた本文"),
    ("部分に 1 行目の印を残す", "{bodies[fid].split(chr(10), 1)[1]}", "{bodies[fid]}", "まとめた本文"),
    ("依存を書かない", '        if depends:\n            entry["depends"] = depends', '        if False:\n            entry["depends"] = depends',
     "依存の連鎖"),
    ("依存の向きを逆にする", 'found[at].add(change.feature["id"])', "found[index].add(caller)", "依存の連鎖"),
    ("組の中の依存も数える", "if at is not None and at != index and", "if at is not None and", "まとめた組の依存"),
    ("まとめた組の循環を見ない", "    order = cycle_in(groups, dependencies(groups))", "    order = []", "まとめると依存が循環する"),
    ("変化の揃いを見ない", "        elif len({by_id[i].kind for i in ids}) != 1:", "        elif False:", "まとめる機能の変化が揃わない"),
    ("本文を作らない機能もまとめる", "absent = [i for i in ids if i not in by_id]", "absent = []", "まとめる機能が無い"),
    ("1 件のまとめを受け付ける", "        if len(ids) < 2:", "        if False:", "まとめる機能が 1 件"),
    ("まとめる機能の重複を見ない", "        if len(set(ids)) != len(ids) or seen & set(ids):", "        if False:", "まとめる機能の重複"),
    ("まとめ方の形の誤りで前の本文を消さない", "        return fail(repo, writing, 2, [problem])", "        return 2", "まとめる機能が 1 件"),
    ("--check でもまとめ方を受け付ける", "    if args.bundle and (args.check or args.red_check):", "    if False:",
     "まとめるのは --check と一緒に使えない"),
    # #874: 仕様の基準コミット
    ("基準コミットの行を本文に書かない", '        f"- 変化: {kind_text}",\n        base_line,\n', '        f"- 変化: {kind_text}",\n',
     "基準コミット: 変更と撤去の本文"),
    ("基準コミットにコミットでなく木の名前を書く", '"--format=%H%n%cI", "HEAD"', '"--format=%T%n%cI", "HEAD"',
     "基準コミット: 追加の本文"),
    ("基準コミットに日時を書かない", 'f"{BASE_COMMIT}`{found[0]}`（コミットの日時 {found[1]}。', 'f"{BASE_COMMIT}`{found[0]}`（',
     "基準コミット: 追加の本文"),
    ("git を起動できなければ止める", "    except OSError as exc:\n        reason = f\"git を起動できない",
     "    except ValueError as exc:\n        reason = f\"git を起動できない", "基準コミット: git を起動できない"),
    ("コミットの無いリポジトリで HEAD を信じる", "if len(found) >= 2 and COMMIT_ID.fullmatch(found[0]) and found[1]:", "if True:",
     "基準コミット: コミットが無い"),
    ("git の作業ツリーでないことを見ない", "        if code != 0 or inside.strip() != \"true\":\n            reason = \"正本リポジトリが git の作業ツリーでない\"",
     "        if False:\n            reason = \"正本リポジトリが git の作業ツリーでない\"", "基準コミット: git の作業ツリーでない"),
    ("根でない正本で外側の HEAD を書く", "        elif cdup.strip():", "        elif False:",
     "基準コミット: git の作業ツリーの根でない"),
    ("GIT_DIR を外さずに git を呼ぶ", "proc = versions.run_git(repo, *args)",
     "proc = subprocess.run([\"git\", \"-C\", str(repo), *args], capture_output=True)", "基準コミット: GIT_DIR が別を指す"),
    ("記録していない理由を書かない", 'f"{BASE_COMMIT}{BASE_UNRECORDED}（{reason}）——', 'f"{BASE_COMMIT}{BASE_UNRECORDED}——',
     "基準コミット: コミットが無い"),
    ("記録していないことを出力で知らせない", "    if unrecorded:\n", "    if False:\n", "基準コミット: git の作業ツリーでない"),
    # #852: 性能の要求
    # #875: 仮回答（--provisional）
    ("仮回答の行を書かない", "    if held:\n        lines.append(f\"{PROVISIONAL_LINE}\"", "    if False:\n        lines.append(f\"{PROVISIONAL_LINE}\"",
     "--provisional で暫定反映を指す"),
    ("受入基準の表に暫定の印を付けない", '"・".join(no + (PROVISIONAL_CELL if no in held else "") for no',
     '"・".join(no for no', "--provisional で暫定反映を指す"),
    ("確定の No にも暫定の印を付ける", '(PROVISIONAL_CELL if no in held else "")', "PROVISIONAL_CELL",
     "--provisional で暫定反映を指す"),
    ("機能の qa を仮回答の行に数えない", '    refs = set(feature["qa"]) | {no for _, case in rows',
     '    refs = set() | {no for _, case in rows', "--provisional で暫定反映を機能だけが指す"),
    ("--provisional でも指していない暫定の行を見ない", "            if uncited:", "            if False:",
     "--provisional でも指していない暫定反映は止める"),
    ("--provisional を読まない", "load(repo, args.upto, args.provisional)", "load(repo, args.upto, False)",
     "--provisional で暫定反映を指す"),
    ("--provisional でも暫定の行を qa から指せない", "!= qa.DONE and not (provisional and qa.is_provisional(answered[no])):",
     "!= qa.DONE:", "--provisional で暫定反映を指す"),
    ("前の版の判定に --provisional を当てない", "    unsettled = unsettled_qa(rendered, loaded.provisional)\n",
     "    unsettled = unsettled_qa(rendered)\n", "--provisional で前の版の暫定反映を確定する"),
    ("前の版の中間表現に --provisional を当てない", "read_whole(rendered, gate=False, provisional=loaded.provisional)",
     "read_whole(rendered, gate=False)", "--provisional で前の版の暫定反映を確定する"),
    ("前の版の指されない暫定の行を見ない", "qa.is_provisional(row) and no in cited)", "qa.is_provisional(row))",
     "--provisional でも前の版の指されない暫定反映は崩れ"),
    ("撤去の本文にも印を付ける", "    held = [] if change.kind == REMOVE else sorted(", "    held = [] if False else sorted(",
     "--provisional の撤去の本文に印を付けない"),
    ("前の版を旗で作ったときの案内を出さない", "            if not loaded.provisional and not unsettled_qa(rendered, provisional=True):",
     "            if False:", "前の版を --provisional で作ったときの案内"),
    ("前の版の暫定の行が残れば必ず旗の案内を出す", "            if not loaded.provisional and not unsettled_qa(rendered, provisional=True):",
     "            if not loaded.provisional:", "前の版を作れていないときは旗の案内を出さない"),
    ("仮回答の本文を出力で名指ししない", "    if marked:\n", "    if False:\n", "--provisional で暫定反映を指す"),
    ("性能予算に数字を写さない", "    if not rows:\n        return [NO_PERFORMANCE_BUDGET]", "    if True:\n        return [NO_PERFORMANCE_BUDGET]",
     "性能の要求: 行があれば性能テストと予算"),
    ("nfr を決まりに無いキーとして拒む", "{CALLED_BY, OUT_OF_SCOPE, NFR, BRANCHES_KEY})", "{CALLED_BY, OUT_OF_SCOPE, BRANCHES_KEY})",
     "性能の要求: 行があれば性能テストと予算"),
    ("性能テストを作らない", "        if rows:\n            contract[f\"{PERF_DIR}/", "        if False:\n            contract[f\"{PERF_DIR}/",
     "性能の要求: 行があれば性能テストと予算"),
    ("性能テストが実装の無いことを失敗にしない", '        MISSING_FAIL,\n        "        took = []",',
     '        "            return [0.0]",\n        "        took = []",', "性能の要求: 行があれば性能テストと予算"),
    ("性能テストが実装を呼ばない", '"            function(**given)",', '"            pass",', "性能の要求: 性能テストが上限と比べる"),
    ("性能テストが指標を 0 で出す", '"    return ordered[rank - 1]",', '"    return 0.0",',
     "性能の要求: 性能テストが上限と比べる"),
    ("nfr の検査を呼ばない", "        if NFR in feature:\n            problems += check_nfr", "        if False:\n            problems += check_nfr",
     "性能の要求: 行が無い"),
    ("表の見出しを見ない", "    if header != list(NFR_COLUMNS):", "    if False:", "性能の要求: 見出しが違う"),
    ("行の数を見ない", "        if len(rows) != 1:", "        if not rows:", "性能の要求: 同じ No が 2 行"),
    ("指標を見ない", '    if row.get("指標") not in METRICS:', "    if False:", "性能の要求: 性能でない行を指す"),
    ("上限が 0 を許す", "or float(limit) <= 0:", "or float(limit) < 0:", "性能の要求: 上限が 0"),
    ("上限の先頭の 0 を許す", 'LIMIT = re.compile(r"(0|[1-9]', 'LIMIT = re.compile(r"([0-9]', "性能の要求: 上限の先頭に 0"),
    ("上限の桁を数えない", "[1-9][0-9]{0,8})", "[1-9][0-9]*)", "性能の要求: 上限の桁が多い"),
    ("表の名前の綴りを見ない", " or path.name not in {child.name for child in path.parent.iterdir()}:", ":",
     "性能の要求: 表の名前の綴りが違う"),
    ("上限の形を見ない", "    if not LIMIT.fullmatch(limit) or float(limit) <= 0:", "    if False:", "性能の要求: 上限が数でない"),
    ("単位を見ない", '    if row.get("単位") != NFR_UNIT:', "    if False:", "性能の要求: 単位が ms でない"),
    ("根拠を見ない", '    for name in ("対象", "条件", "根拠"):', '    for name in ("対象", "条件"):', "性能の要求: 根拠が空"),
    ("列の数を見ない", "    if width != len(NFR_COLUMNS):", "    if False:", "性能の要求: 列が多い"),
    ("No の形を見ない", "for no in refs if not isinstance(no, str) or not NFR_ID.fullmatch(no)]", "for no in refs if False]",
     "性能の要求: No の形"),
    ("残った性能テストを数えない", '(PERF_DIR, "perf_*.py")', '(PERF_DIR, "none_*.py")', "性能の要求: nfr を外した --check"),
    # #851: 作らないもの
    ("作らないものの節を書かない", '    lines += ["", SECTIONS[4], ""] + not_built(change, loaded, contract)', "    lines += []",
     "作らないもの: 範囲の外の行と次の版の候補を写す"),
    ("次の版の候補も範囲の外に入れる", "[r for r in chosen if NEXT_VERSION not in r[0]]", "chosen",
     "作らないもの: 範囲の外の行と次の版の候補を写す"),
    ("次の版の候補を分けない", "[r for r in chosen if NEXT_VERSION in r[0]]", "[]",
     "作らないもの: 範囲の外の行と次の版の候補を写す"),
    ("挙げていない行も写す", "        if text in picked and text not in seen:", "        if text not in seen:",
     "作らないもの: 範囲の外の行と次の版の候補を写す"),
    ("表の見出しを付けない", "                lines += list(header)", "                pass",
     "作らないもの: 範囲の外の行と次の版の候補を写す"),
    ("範囲の文書の順に並べない", "    for text, header in rows:", "    for text, header in sorted(rows):",
     "作らないもの: 範囲の外の行と次の版の候補を写す"),
    ("表でない行を空の行で区切らない", "            if index and (header is None or header != group[index - 1][1]):",
     "            if index and header is not None and header != group[index - 1][1]:", "作らないもの: 範囲の外の行と次の版の候補を写す"),
    ("out_of_scope を決まりに無いキーとして拒む", "{CALLED_BY, OUT_OF_SCOPE, NFR, BRANCHES_KEY})", "{CALLED_BY, NFR, BRANCHES_KEY})",
     "作らないもの: 範囲の外の行と次の版の候補を写す"),
    ("out_of_scope の検査を呼ばない", "        if OUT_OF_SCOPE in feature:\n            problems += check_out_of_scope",
     "        if False:\n            problems += check_out_of_scope", "作らないもの: 節に無い行"),
    ("原文が在ることを見ない", "for row in picked if row not in present]", "for row in picked if False]", "作らないもの: 節に無い行"),
    ("区切りの行を見ず、表の見出しを行に数える",
     '        if "|" in line and "-" in following and TABLE_SEPARATOR.fullmatch(following):', "        if False:",
     "作らないもの: 表の見出しの行を挙げる"),
    ("単独の --- を区切りと読む", "(\\|\\s*:?-+:?\\s*)+\\|?|", "(\\|\\s*:?-+:?\\s*)*\\|?|", "作らないもの: 水平線の前の | を含む行"),
    ("区切りの行を表の行に数える", "            header = (line, following)\n            index += 2",
     "            header = (line, following)\n            index += 1", "作らないもの: 表の区切りの行を挙げる"),
    ("先頭の | の無い区切りを区切りと読まない", 'TABLE_SEPARATOR = re.compile(r"\\|?\\s*:?-+', 'TABLE_SEPARATOR = re.compile(r"\\|\\s*:?-+',
     "作らないもの: 先頭の | の無い表"),
    ("見出しの行を行に数える", "        if line and not proposal.heading_level(line):", "        if line:",
     "作らないもの: 見出しの行を挙げる"),
    ("範囲の文書が無いと言わない", '    if not path.is_file():\n        return [f"{where}: 範囲の文書',
     '    if False:\n        return [f"{where}: 範囲の文書', "作らないもの: 範囲の文書が無い"),
    ("範囲の外の節が無いと言わない", '    if rows is None:\n        return [f"{where}: 範囲の文書',
     '    if False:\n        return [f"{where}: 範囲の文書', "作らないもの: 範囲の外の節が無い"),
    ("out_of_scope の空の配列を許す", "    if not isinstance(picked, list) or not picked:", "    if not isinstance(picked, list):",
     "作らないもの: 空の配列"),
    ("out_of_scope の重複を許す", "    if len(set(map(str, picked))) != len(picked):", "    if False:", "作らないもの: 重複"),
    ("out_of_scope の複数行を許す", " or not one_line(row) or row != row.strip() for row in picked", " or row != row.strip() for row in picked",
     "作らないもの: 複数行"),
    ("out_of_scope の前後の空白を許す", " or row != row.strip() for row in picked", " for row in picked", "作らないもの: 前後に空白"),
    # #855: 呼ぶ側の分岐と課題一覧（案）
    ("課題一覧（案）を作らない", "    issues[PROPOSALS] = proposals(changes, loaded, contract)\n", "",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("呼ばれる関数にも案を作る", " and not c.feature.get(CALLED_BY)\n", "\n", "課題一覧（案）: 呼ばれる関数には案を作らない"),
    ("機能が同じ変更にも案を作る", "\n            and not (c.kind == MODIFY and c.before == c.feature)]", "]",
     "課題一覧（案）: v2 で impl_module だけ変えても案は無い"),
    ("該当なしだけでも未決定事項を先に決めると書く", 'if missing else "——どの分岐も該当なし。"', 'if True else "——どの分岐も該当なし。"',
     "課題一覧（案）: どの分岐も該当なし"),
    ("撤去にも案を作る", "if c.kind in (ADD, MODIFY) and not", "if c.kind in (ADD, MODIFY, REMOVE) and not",
     "課題一覧（案）: v2 で機能を消すだけなら案は無い"),
    ("未決定事項を出さない", "        if missing:\n", "        if False:\n", "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("書き起こした分岐も未決定に数える", "[name for name in BRANCHES if name not in branches]", "list(BRANCHES)",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("行ごとの該当なしでも未決定に数える", "    return [] if NONE in branches else [", "    return [] if False else [",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("受入基準の雛形に見せるものを写さない", '            lines += [f"- [ ] {name}: {text}" for name, text in shown]\n', "",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("該当なしの分岐を雛形に並べない", "            if absent:\n", "            if False:\n",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("決まった分岐が無いことを書かない", "            if not shown:\n", "            if False:\n",
     "課題一覧（案）: branches を書いていなければ全部の分岐が未決定"),
    ("案に作らないものを付けない", "        lines += [f\"#{line}\" if line in NOT_BUILT else line for line in not_built(change, loaded, contract)]\n", "",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("案の作らないものの小見出しを下げない", 'lines += [f"#{line}" if line in NOT_BUILT else line', "lines += [line",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("案が無いことを書かない", "    if not entries:\n", "    if False:\n", "課題一覧（案）: v2 で機能を消すだけなら案は無い"),
    ("案の件数を出さない", "（案 {len(entries)} 件", "（案 {len(changes)} 件", "課題一覧（案）: 呼ばれる関数には案を作らない"),
    ("branches を決まりに無いキーとして拒む", "{CALLED_BY, OUT_OF_SCOPE, NFR, BRANCHES_KEY})", "{CALLED_BY, OUT_OF_SCOPE, NFR})",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("branches の検査を呼ばない", "        if BRANCHES_KEY in feature:\n            problems += check_branches",
     "        if False:\n            problems += check_branches", "呼ぶ側の分岐: 原文に無い行"),
    ("呼ばれる関数に書いても通す", "    if CALLED_BY in feature:\n        return [f\"{where}: 呼ばれる関数", "    if False:\n        return [f\"{where}: 呼ばれる関数",
     "呼ぶ側の分岐: 呼ばれる関数に書く"),
    ("branches の空を許す", "    if not isinstance(branches, dict) or not branches:", "    if not isinstance(branches, dict):",
     "呼ぶ側の分岐: 空"),
    ("branches の配列を許す", "    if not isinstance(branches, dict) or not branches:", "    if not branches:",
     "呼ぶ側の分岐: オブジェクトでない"),
    ("行ごとの該当なしと分岐の混在を許す", "        if len(branches) != 1:\n", "        if False:\n",
     "呼ぶ側の分岐: 行ごとの該当なしと分岐を混ぜる"),
    ("分岐の名前を見ない", "            if name not in BRANCHES:\n", "            if False:\n", "呼ぶ側の分岐: 分岐の名前でない"),
    ("値の鍵を 2 つ許す", "or len(value) != 1 or next(iter(value))", "or next(iter(value))", "呼ぶ側の分岐: shows と none を両方書く"),
    ("値の鍵の名前を見ない", " or next(iter(value)) not in (SHOWS, NONE):", ":", "呼ぶ側の分岐: 値の鍵が違う"),
    ("原文の 1 行を見ない", "        if not isinstance(text, str) or not one_line(text) or text != text.strip():",
     "        if not isinstance(text, str) or text != text.strip():", "呼ぶ側の分岐: 複数行"),
    ("原文の前後の空白を許す", " or not one_line(text) or text != text.strip():", " or not one_line(text):", "呼ぶ側の分岐: 前後に空白"),
    ("原文が在ることを見ない（分岐）", "for at, text in good if text not in lines]", "for at, text in good if False]",
     "呼ぶ側の分岐: 原文に無い行"),
    ("原文の行の前後の空白を落とさない", "lines |= {line.strip() for line in", "lines |= {line for line in",
     "課題一覧（案）: 未決定事項と受入基準の雛形と作らないもの"),
    ("source の 1 つ目しか読まない", "            continue  # 読めない原文は source の検査と未決定の印の関門が言う\n    return lines",
     "            continue  # 読めない原文は source の検査と未決定の印の関門が言う\n        break\n    return lines",
     "呼ぶ側の分岐: 別の source の原文"),
    ("行の無い小見出しに無いと書かない",
     '            lines.append(f"この機能に関わるとして写した{what}は無い（無いことは、ほかのものを作ってよいという意味ではない）。")',
     "            pass", "本文から辿れる"),
    ("性能予算を書かない", '    lines += ["", NOT_BUILT[2], ""] + budget(change.feature, loaded, contract)', "    lines += []", "本文から辿れる"),
    ("撤去の本文に作らないものの 1 行を書かない", '        return ["撤去の Issue なので、作るものは無い',
     '        return [] and ["撤去の Issue なので、作るものは無い', "v2 で機能を消す"),
    # #609: 呼ばれる機能
    ("呼ぶ機能の検査を呼ばない", "    return problems + check_called_by(features)", "    return problems", "呼ぶ機能が中間表現に無い"),
    ("呼ぶ機能の実在を見ない", "            elif caller not in ids:", "            elif False:", "呼ぶ機能が中間表現に無い"),
    ("呼ぶ機能の空の配列を許す", "if not isinstance(callers, list) or not callers:", "if not isinstance(callers, list):",
     "呼ぶ機能が空の配列"),
    ("呼ぶ機能の id の形を見ない", "            if not isinstance(caller, str) or not FEATURE_ID.fullmatch(caller):",
     "            if not isinstance(caller, str):", "呼ぶ機能の id の形"),
    ("呼ぶ機能に自分自身を許す", "            elif caller == fid:", "            elif False:", "呼ぶ機能が自分自身"),
    ("呼ぶ機能の重複を許す", "        if len(set(map(str, callers))) != len(callers):", "        if False:", "呼ぶ機能の重複"),
    ("呼ぶ関係の循環を見ない", "            if state.get(nxt) == 1:\n                return nxt",
     "            if False:\n                return nxt", "呼ぶ関係の循環"),
    ("呼ぶ機能が変わっていなくても知らせない",
     "        if change.kind in (ADD, MODIFY) and callers and not changed & set(callers):", "        if False:",
     "v2 で呼ばれる機能だけ変える"),
    ("呼ぶ機能が変わっても知らせる", " and callers and not changed & set(callers):", " and callers:", "v2 で呼ぶ機能も変える"),
    ("本文に呼ぶ機能を書かない", "        if feature.get(CALLED_BY):\n            titles", "        if False:\n            titles",
     "呼ばれる機能"),
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
    ("暫定の行を見ない", "            if held and not provisional:", "            if False:", "暫定反映の Q&A を指さない"),
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
    ("未実装をエラーにする", '    "            return None",\n    "        raise",\n    "    return getattr(module, OPERATION, None)",',
     '    "            raise",\n    "        raise",\n    "    return getattr(module, OPERATION, None)",', "Red テストが失敗する"),
    # #923: トレースのケースが入口を探す関数も、実装が無ければ失敗（エラーではない）にする
    ("トレースで未実装をエラーにする", '    "            return None",\n    "        raise",\n    "    return getattr(module, name, None)",',
     '    "            raise",\n    "        raise",\n    "    return getattr(module, name, None)",', "トレース: 実装が無ければ失敗"),
    ("未実装で fail しない", 'MISSING_FAIL = "            self.fail(f\\"未実装: {IMPL_MODULE}.{OPERATION} が無い\\")"', 'MISSING_FAIL = "            pass"',
     "関数の無い実装でも失敗する"),
    ("期待を比べない", '"        self.assertEqual(actual, expected)",', '"        self.assertIsNotNone(actual)",', "誤った実装で失敗する"),
    ("nullable に true 以外を許す", "if NULLABLE in field and field[NULLABLE] is not True:",
     "if NULLABLE in field and field[NULLABLE] is None:", "nullable が false"),
    ("null を許す項目にも null を拒む", "        if value is None and nullable(field):\n            continue",
     "        if False:\n            continue", "null を許す項目"),
    ("null を許さない項目にも null を許す", "        if value is None and nullable(field):\n            continue",
     "        if value is None:\n            continue", "null を許さない出力に null を期待する"),
    ("null を許す項目の型を見ない", "        if value is None and nullable(field):\n            continue",
     "        if nullable(field):\n            continue", "null を許す項目に型の違う値"),
    ("パスの変数の nullable を見ない", "        if name in fields and nullable(fields[name]):", "        if False:",
     "パスの変数を nullable にする"),
    ("OpenAPI の型に null を足さない", '        out["type"] = [field["type"], "null"]', "        pass", "null を許す項目"),
    ("OpenAPI の enum に null を足さない", '            out["enum"] = field["enum"] + [None]', "            pass",
     "null を許す項目"),
    ("型に None を足さない", 'return name + " | None" if nullable(field) else name', "return name", "null を許す項目"),
    ("Red テストが null を型の検査から外さない",
     '*(["            if value is None and name in NULLABLE:", "                continue"] if allow_null else []),', "",
     "null を返す正しい実装で緑"),
    ("Red テストが null を許す項目の型を見ない", '"            if value is None and name in NULLABLE:"',
     '"            if name in NULLABLE:"', "null を許す整数の項目に真偽値を返す実装で失敗する"),
    ("null を許す項目の無い機能にも NULLABLE を書く", '*([f"NULLABLE = {tuple(allow_null)!r}"] if allow_null else []),',
     'f"NULLABLE = {tuple(allow_null)!r}",', "null を許す項目を書かない生成物は変わらない"),
    ("型を見ない", '"            self.assertTrue(type_fits(OUTPUT_TYPES[name], value),",', '"            self.assertTrue(True,",',
     "型の違う実装で失敗する"),
    ("中間表現の実装のモジュールを読まない",
     '    impl_module = ir.get("impl_module", DEFAULT_IMPL_MODULE)\n    contract = {',
     '    impl_module = DEFAULT_IMPL_MODULE\n    contract = {',
     "中間表現の実装のモジュールを使う"),
    ("実装のモジュールの形を見ない", '    if "impl_module" in ir and not module_name(ir["impl_module"]):',
     "    if False:", "実装のモジュールの形"),
    ("実装のモジュールの最初の部しか見ない", '                                          for part in value.split("."))',
     '                                          for part in value.split(".")[:1])', "実装のモジュールの 2 つ目の部の形"),
    ("実装のモジュールの予約語を許す", "all(NAME.fullmatch(part) and not keyword.iskeyword(part)",
     "all(NAME.fullmatch(part)", "実装のモジュールの予約語の部"),
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
    ("OpenAPI の schema から enum を落とす", '        out["enum"] = field["enum"]\n    if nullable(field):',
     "        pass\n    if nullable(field):", "パスの変数"),
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
    ("形式検査のモデルの場所を許す", "        elif versions.is_formal(path.relative_to(whole.resolve()).as_posix()):", "        elif False:",
     "形式検査のモデルを出所にする"),
    ("接頭辞で形式検査のモデルの場所を断る", "        elif versions.is_formal(path.relative_to(whole.resolve()).as_posix()):",
     '        elif path.relative_to(whole.resolve()).as_posix().startswith("spec/formal"):', "接頭辞だけ同じファイルを出所にする"),
    ("ドットの場所を許す", '        elif any(part.startswith(".") for part in path.relative_to(spec_root).parts):', "        elif False:",
     "ドットの場所の仕様"),
    # `surrogates(ir)` の検査には変異を置かない——版を重ねる段（`merge-versions.py` の `render`）が先に断るので、
    # 入力から届かない（殺せると主張しない）
    ("整数を isfinite に渡す", "        return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))",
     "        return math.isfinite(value) and isinstance(value, (int, float))", "number に桁の大きい整数"),
    ("エラーのケースで error を期待しない",
     '            expected = case["expected"] if "expected" in case else {"error": case["error"]}\n            run',
     '            expected = case.get("expected", {})\n            run', "正しい実装で緑"),
    ("ケースを 1 つしか作らない", '    for case in sorted(feature["cases"], key=case_order):\n        refs',
     '    for case in sorted(feature["cases"], key=case_order)[:1]:\n        refs',
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
    ("前の版の中間表現を検査しない", "        problems = check_ir(ir, whole, answered, path_rules=gate, provisional=provisional)\n",
     "        problems = check_ir(ir, whole, answered, path_rules=gate, provisional=provisional) if gate else []\n",
     "前の版の中間表現が決まりに反する"),
    ("前の版にもパスの変数の決まりを当てる", "check_ir(ir, whole, answered, path_rules=gate,",
     "check_ir(ir, whole, answered, path_rules=True,", "前の版だけパスの変数が入力に無い"),
    ("今の版にもパスの変数の決まりを当てない", "check_ir(ir, whole, answered, path_rules=gate,",
     "check_ir(ir, whole, answered, path_rules=False,", "前の版のパスの変数を直さない"),
    # #361: 前の版の Q&A の状態を直接見る（#358）・名指し（#335）・凍結した前の版（#357）
    ("前の版の Q&A の状態を見ない", "    unsettled = unsettled_qa(rendered, loaded.provisional)\n", "    unsettled = []\n",
     "前の版に指していない暫定反映の行がある"),
    ("前の版の暫定反映だけを見る", "if row[\"状態\"].strip() != qa.DONE and not (provisional and qa.is_provisional(row) and no in cited)]",
     'if row["状態"].strip() == qa.PROVISIONAL]',
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
    ("--upto を渡さない", "load(repo, args.upto, args.provisional)", "load(repo, None, args.provisional)", "前の版の時点の --check"),
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


# 大文字小文字を区別しないファイルシステムでだけ当てる変異（名前 → 理由）。区別するファイルシステムでは、綴りの違う
# `NFR.csv` は本体の検査が無くても開けないので、試料がその変異を判別しない（#852 の狭いパスの N1）
FOLDING_ONLY = {"表の名前の綴りを見ない": "綴りの違う表の名前を開けるのは大文字小文字を区別しないファイルシステムだけで、区別するなら本体の検査が無くても「表が無い」になる"}
skipped: list[str] = []


def case_folding(where: Path) -> bool:
    """`where` の下のファイルシステムが大文字小文字を区別しないか（OS の名前ではなく、実際に作って確かめる）。"""
    probe = where / "case-probe"
    probe.mkdir()
    (probe / "nfr.csv").write_text("", encoding="utf-8")
    return (probe / "NFR.csv").exists()


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
        # 呼ぶ側の分岐の名前（#855）——中間表現の原本は spec-ir.md の表
        branch_names = table_cells(ir_ref, "### 分岐の名前")
        check("BRANCHES が references/spec-ir.md の分岐の名前の表と違う", list(constant(source, "BRANCHES") or ()) == branch_names
              and len(branch_names) == 8, f"{constant(source, 'BRANCHES')} vs {branch_names}")
        check("試料の ALL_BRANCHES が references/spec-ir.md の分岐の名前の表と違う", list(ALL_BRANCHES) == branch_names,
              f"{ALL_BRANCHES} vs {branch_names}")
        # トレースのケースが実装に求める口（#923）——原本は spec-ir.md の「実装に求める口」の表。待つ時間も原本の文と一致する
        ports = table_cells(ir_ref, "### 実装に求める口")
        check("CHECKPOINT, RESET が references/spec-ir.md の実装に求める口の表と違う",
              ports == [constant(source, "CHECKPOINT"), constant(source, "RESET")], f"{ports}")
        check("TRACE_STEP_WAIT・TRACE_LIMIT が references/spec-ir.md の「Red テストが確かめること」と違う",
              f"（1 段 {constant(source, 'TRACE_STEP_WAIT')} 秒）" in ir_ref and f"（上限 {constant(source, 'TRACE_LIMIT')} 秒。" in ir_ref)
        check("試料の実装が口の名前を使っていない（口の名前の変異を試料が判別しない）",
              f"def {constant(source, 'RESET')}():" in LOCKED_IMPL and f", {constant(source, 'CHECKPOINT')}=" in LOCKED_IMPL)
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
        # 性能の要求の表の列と指標（#852）。原本は references/nfr.md
        nfr_ref = NFR_REF.read_text(encoding="utf-8")
        columns, metrics = table_cells(nfr_ref, "## 列"), table_cells(nfr_ref, "### 指標")
        check("NFR_COLUMNS が references/nfr.md の列の表と違う", list(constant(source, "NFR_COLUMNS") or ()) == columns,
              f"{constant(source, 'NFR_COLUMNS')} vs {columns}")
        check("METRICS が references/nfr.md の指標の表と違う", list(constant(source, "METRICS") or ()) == metrics,
              f"{constant(source, 'METRICS')} vs {metrics}")
        check("references/nfr.md から列・指標を読めない（読み方が壊れている）", len(columns) == 7 and len(metrics) >= 2,
              f"{columns} {metrics}")
        check("NFR_UNIT が references/nfr.md の列の表と違う",
              f"| `単位` | 性能の行なら `{constant(source, 'NFR_UNIT')}` |" in nfr_ref)
        check("既定の原則（NO_PERFORMANCE_BUDGET）が references/nfr.md の原則と違う",
              "最適化は、計測で予算を超えたと示せたときだけ" in nfr_ref
              and "最適化は、計測で予算を超えたと示せたときだけ" in NO_BUDGET)
        for rel in (constant(source, "IR_PATH"), constant(source, "QA_PATH"), constant(source, "ISSUES_DIR"),
                    constant(source, "NFR_PATH"), f"{constant(source, 'OUT_DIR')}/openapi.json",
                    f"{constant(source, 'PERF_DIR')}/perf_<機能>.py"):
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
        # まとめた本文の印（#876）——2 つのプラグインの境界の写し。原本は handoff-issue.md の「まとめた本文」
        bundle_marker = constant(source, "BUNDLE_MARKER")
        shown = bundle_marker.format("<機能の id>・<機能の id>") if isinstance(bundle_marker, str) else None
        check("BUNDLE_MARKER が本体とこのテストの写しで違う", bundle_marker == BUNDLE_MARK, f"{bundle_marker!r}")
        for label, doc in (("handoff-issue.md", handoff), ("dev-loop の references/spec-gap.md", gap)):
            check(f"{label} にまとめた本文の印 {shown!r} が無い", shown is not None and f"`{shown}`" in doc)
        check("まとめた本文の印を言い換えても照合が不一致にならない",
              shown is not None and f"`{shown}`" not in gap.replace("spec-loop-bundle", "spec-loop-group"))
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
        # 仕様の基準コミットの行の頭と「記録していない」の文言（#874）——2 つのプラグインの境界の写し
        base_head, base_none = constant(source, "BASE_COMMIT"), constant(source, "BASE_UNRECORDED")
        check("BASE_COMMIT・BASE_UNRECORDED を本体から読めない", base_head == BASE_LINE and isinstance(base_none, str)
              and len(base_none) > 2, f"{base_head!r} {base_none!r}")
        for label, doc in (("handoff-issue.md", handoff), ("dev-loop の references/spec-gap.md", gap)):
            for text in (f"{base_head}`<コミットの名前>`（コミットの日時 <日時>。", f"{base_head}{base_none}（<理由>）"):
                check(f"{label} に基準コミットの行の形 {text!r} が無い", isinstance(base_head, str) and isinstance(base_none, str)
                      and text in doc)
        # 陽性対照: 片方の文言を言い換えると当たらない
        check("基準コミットの文言を言い換えても照合が不一致にならない",
              isinstance(base_none, str) and f"{base_head}{base_none}（<理由>）" not in gap.replace(base_none, "記していない"))
        # 仮回答の印（#875）——2 つのプラグインの境界の写し。原本は handoff-issue.md の「仮回答の印」
        mark_line, mark_cell = constant(source, "PROVISIONAL_LINE"), constant(source, "PROVISIONAL_CELL")
        check("PROVISIONAL_LINE・PROVISIONAL_CELL が本体とこのテストの写しで違う",
              (mark_line, mark_cell) == (PROVISIONAL_LINE, PROVISIONAL_CELL), f"{mark_line!r} {mark_cell!r}")
        for label, doc in (("handoff-issue.md", handoff), ("dev-loop の references/spec-gap.md", gap)):
            for text in (f"{PROVISIONAL_LINE}<No>", f"`{PROVISIONAL_CELL}`"):
                check(f"{label} に仮回答の印の形 {text!r} が無い", text in doc)
        check("仮回答の印を言い換えても照合が不一致にならない",
              f"`{PROVISIONAL_CELL}`" not in gap.replace(PROVISIONAL_CELL, "（仮）"))
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
        folds = case_folding(tmp_path)
        unknown = sorted(set(FOLDING_ONLY) - {name for name, *_ in MUTATIONS})
        check("FOLDING_ONLY に MUTATIONS に無い変異の名前がある", not unknown, f"{unknown}")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            if name in FOLDING_ONLY and not folds:
                # 当てていない——緑には数えず、当てなかったことを出す（数は最後の行にも出る）
                skipped.append(name)
                print(f"変異を当てなかった: {name}（{FOLDING_ONLY[name]}。この一時ディレクトリは大文字小文字を区別する）")
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
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(CHECKER_MUTATIONS) - len(skipped)} 件"
          + (f"（ほかに当てなかった変異 {len(skipped)} 件: {'・'.join(skipped)}）" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
