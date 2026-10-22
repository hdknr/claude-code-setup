#!/usr/bin/env python3
"""確定した仕様の中間表現（`spec_ir.json`）から、dev-loop に渡すものを作る。

usage: python3 scaffold.py [--repo <正本リポジトリ>] [--check [--upto <n>] | --dry-run [--upto <n>] | --red-check [--in-progress]]

作るもの（置き場所の正は `references/tree.md`）:

- `scaffold/openapi.json`・`scaffold/types.py`・`scaffold/tests/test_<機能>.py`（Red テスト）——**commit する契約**
- `build/scaffold/issues/<機能の id>.md` と `issues.json`——**Issue の本文**（登録はスクリプトの外。`gh` を呼ばない）

**形の正は `references/spec-ir.md`（中間表現）と `references/handoff-issue.md`（Issue の本文）である**
（このプラグインの中にある）。下の定数（メソッド・型・番号の形・印・節）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-scaffold.py` が突き合わせて見る**。

**入力は、正本の版（`docs/v1/`・`docs/v2/`…）を重ね合わせた全体である**（決まりは `references/versions.md`）。
同梱の `merge-versions.py` の `merge` で**メモリ上で**重ね（同じ入力から、`merge-versions.py docs build/merged` が書くのと
同じバイト）、一時ディレクトリに置いて当てる。**`build/merged/` には書かない。** 重ね合わせが決まりに反すれば 1
（JSON として読めない版を含む）、`docs/` が無い・版が読めない・どの版にも中間表現が無ければ 2。

**契約（`scaffold/`）は全体から作り、Issue の本文は変わった機能だけに作る。** 作業中の版 v<n> の全体と v<n-1> の全体を
機能の `id` で比べ（同梱の `diff-versions.py` の `compare_maps`）、**追加・変更・削除**の機能ごとに本文を 1 件作る。
**変わっていない機能の本文は作らない**（前の版の Issue がある）。v1 だけなら全部が追加。
ケースの変化は**Red テストが実行する中身**（入力・期待・`operation.id`・期待にある項目の出力の型・`impl_module`）で決める——
題だけの違い・`integer` を `number` に広げただけの違いは変化に数えない（前の版の実装は落ちない）。
**`impl_module` を変えた版では、残る機能も全部が変更になる**（どの Red テストも前の版の実装を探せない）。**前の版の中間表現も決まり（`references/spec-ir.md`）に当て、反すれば分けずに 1。**

**生成の前に、自分で関門を通す**——`check-spec-exit.py` の条件 1（仕様に反映した状態でない Q&A・未決定の印が 0 件）を呼び、
通らなければ 1 バイトも書かない。**条件 2〜5 は判定しない**（判定役の報告で決まる。`scaffold` の本文）。
**全部を組み立ててから書く**ので、入力の誤りで途中で落ちて一部だけ書くことはない。
**書き込みそのもの（ファイルシステム）が途中で失敗すると、`scaffold/` は一部だけ書かれうる**——そのときも
**Issue の本文は書く前に消してある**（古い本文を登録させない）ので、契約の乖離は `--check` が言う。

**実装のモジュールは中間表現の `impl_module` が決める**（省けば `spec_impl`）——引数では渡さない。
引数で渡すと、作り直すたびに指定を繰り返さなければ黙って別のモジュールになり、
`--check` は検査する相手（置いてある Red テスト）からそれを読むしかなくなる。

- `--check`: 書かずに、置いてある `scaffold/` が今の入力から作るものと同じかを確かめる（鮮度）。
  **消した機能の Red テストが残っていても古いと言う**（生成の印のあるファイルだけを数える）。
  **バイトで比べる**（改行の違いも古いと言う——Issue の本文の sha256 はバイトの指紋なので）。
- `--dry-run`: 関門と中間表現の検査（前の版との分け方を含む）だけをして、何も書かず何も消さない。
- `--upto <n>`: v<n> までを重ねた全体に当てる（`--check`・`--dry-run` でだけ使える）。**差分の周を始める前に、前の版の
  時点の `scaffold/` が新しいか**を `--check --upto <n-1>` で確かめるのに使う（`references/versions.md`）。
  **書く生成では断る**——古い版の契約を置くと、作業中の版の Issue が指すものと食い違う。
- `--red-check`: 置いてある `scaffold/` が新しいことを確かめてから、Red テストを正本リポジトリの根で走らせ、
  **回帰のケースは緑で、追加・変更のケースは前の版か作業中の版のどちらかの期待を満たすか**を見る。
  **Red テストと受入基準は、実装が前の版の状態にあることを前提にしない**（#294）——**前の版（v<n-1>）の全体から
  Red テストを一時ディレクトリに作り、同じ実装に当てて確かめる**。追加・変更のケースごとに:
    - 作業中の版で失敗し、前の版で緑（か前の版に無い）: 期待どおり（Red）
    - 作業中の版で緑で、前の版でも緑（か前の版に無い）: **0 のまま名指しで知らせる**（もう緑——前の版の実装がもう
      満たし、Red テストはこの変化を判別しない。#281）
    - 作業中の版で緑で、前の版で失敗: **実装は前の版の状態に無い**（1）。`--in-progress` なら実装済みとして数える（#282）
    - どちらでも失敗: 前の版の仕様とも食い違う（1）。`--in-progress` なら**作りかけの実装の誤りを先に挙げる**（同じく 1。
      作り直しでは実装はもう前の版の状態に無いはずなので。#300）。**ただしどちらの版でも「未実装」で落ちるなら、実装が無いだけで
      期待どおり（Red）**——片方の版だけ「未実装」（関数の改名など）なら、もう片方の期待を満たしていないので 1
    - **エラー**（失敗でも緑でもない）: もう一方の版のテストが緑なら、**その版の「失敗」と同じに読む**（入力の名前や
      形を変える変更では、呼び出しの形が合わない側の版のテストが呼び出しで落ちる）。そうでなければ 1——前の版の側なら
      「前の版の状態を判定できない」と言う（乖離とは言い切らない。扱いは scaffold `SKILL.md` 手順 4）。
      **飛ばされた**テストはどちらの版でも 1——前の版の側なら、作業中の版のテストが緑でも「前の版の状態を判定できない」と言う
  **実装が無い**（どのテストも「未実装」で落ちる）なら、期待が全部失敗のとき（v1・追加だけ）は判定でき、
  そうでなければ**回帰を判定していない**（2）。テストを書き換えない・何も書かない。
- `--in-progress`: `--red-check` と一緒にだけ使う。**作り直しの経路**（この版の Issue を登録し、実装が始まっている）で、
  追加・変更のケースが作業中の版の期待をもう満たしていても止めない。

終了コード:

- 0: 作った（`--check` なら新しい・`--dry-run` なら作れる・`--red-check` なら期待どおり）
- 1: 作らなかった——版の重ね合わせが決まりに反する・関門の条件 1 を満たさない・中間表現（前の版のものを含む）が決まりに
  反する（全部を 1 行ずつ出す）・`--check` で古い・`--red-check` で期待と違う（名指しする）。**Issue の本文の前の出力は消す**
  （古い本文を登録させない。`--check`・`--dry-run`・`--red-check` では消さない）
- 2: 判定していない——引数の誤り（書く生成・`--red-check` に `--upto`、`--red-check` の無い `--in-progress`、無い版の `--upto` を含む）・`docs/` が無い／版が 1 つも無い／
  版が読めない・関門が判定していない・中間表現が無い・Red テストを走らせられない・実装が無く回帰を判定できない・
  予期しない失敗（書き込みの失敗を含む）。書く生成では前の Issue の本文は消す

**`scaffold/` は失敗しても消さない**——commit 済みの契約で、古ければ `--check` が言う。

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う（`git` も要らない）。

**この生成が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **中間表現が仕様と意味で一致するか** | 書き起こしは判断（`scaffold` の仕事）。出所（`source` の実在・Q&A が `反映済み`）までを見る。`暫定反映` の行が表に残れば、指していなくても止める |
| **Red テストが仕様のケースを漏れなく持つか** | 中間表現に書いたケースだけが生成される。漏れは書き起こしの側で見る |
| **Python 以外の言語の型・テスト** | OpenAPI から対象リポジトリの道具で作る |
| **Issue を登録したか・登録した本文が同じか** | 登録はスクリプトの外（`gh issue create --body-file` に、生成した本文をそのまま渡す） |
| **変わった API（メソッド・パス）を Red テストが捕まえるか** | Red テストは関数を呼ぶ。メソッド・パスだけの変更は本文に前の版の API を書くが、ケースの変化には数えない |
| **`--red-check` が回した実装が、開発のリポジトリの実装か** | 走らせるのは正本リポジトリの根で読み込める実装。開発のリポジトリが別なら、そこで回すかは `CLAUDE.md` が決める |
| **もう緑の追加・変更が、中間表現の書き起こしの誤りか** | 前の版の実装がもう満たすケースは名指しで知らせるだけ（0）。Red テストがその変化を判別しないのが誤りかは意味の問題で、`scaffold` スキルの手順 4 で利用者に示す |
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import keyword
import math
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 置き場所（`references/tree.md`・`references/versions.md` の写し）
DOCS = "docs"
# 重ね合わせた全体の置き場所（`merge-versions.py docs build/merged` が書く場所。このスクリプトは書かない）
MERGED_DIR = "build/merged"
# 撤去の本文が指す、前の版 v<n-1> の全体の置き場所（`build/merged/` を前の版で上書きさせない）
PREVIOUS_DIR = "build/merged-v{}"
# 重ね合わせた全体の根からのパス
QA_PATH = "shared/qa.csv"
SPEC_DIR = "spec"
IR_PATH = "spec/spec_ir.json"
OUT_DIR = "scaffold"
ISSUES_DIR = "build/scaffold/issues"

# `references/spec-ir.md` の写し
IR_VERSION = 1
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
TYPES = ("string", "integer", "number", "boolean")
# `\d` は全角や他の文字体系の数字にも合うので使わない（`check-qa-csv.py` と同じ理由）
FEATURE_ID = re.compile(r"F-[0-9]{3,}")
NAME = re.compile(r"[a-z][a-z0-9_]*")
ERROR_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
QA_NO = re.compile(r"Q-[0-9]{3,}")
# 正常時の出力の項目に使えない名前（失敗の形 `{"error": …}` と見分けられないため）
RESERVED_OUTPUT = "error"
DEFAULT_IMPL_MODULE = "spec_impl"
# 引数を持たないメソッド（入力はクエリに載せる）
NO_BODY = ("GET", "DELETE")
# パスの変数（`/items/{id}`）。中身は `input` の項目名でなければならない
PATH_VAR = re.compile(r"\{([^{}]*)\}")

# `references/handoff-issue.md` の写し
HANDOFF_MARKER = "<!-- spec-loop-handoff: v3 -->"
FEATURE_MARKER = "<!-- spec-loop-feature: {} -->"
CHANGE_MARKER = "<!-- spec-loop-change: {}; base={} -->"
ADD, MODIFY, REMOVE = "add", "modify", "remove"
NO_BASE = "none"
SECTIONS = ("## 仕様", "## 受入基準", "## Red テスト", "## Q&A の回答", "## 仕様の穴を見つけたら")
# ケースの変化（受入基準の表の `変化` の列）
CASE_ADDED, CASE_CHANGED, CASE_KEPT, CASE_REMOVED = "追加", "変更", "回帰", "削除"
# Red テストが「実装が無い」で落ちたときの文言の頭（生成する Red テストの `self.fail` と同じ）
MISSING = "未実装: "
# 実装の状態についての前提（#294）。scaffold の `SKILL.md`・`handoff-issue.md`・dev-loop の `spec-gap.md` は
# この 2 つをそのまま持つ（`scripts/test-scaffold.py` が突き合わせる）。本文は `KEPT_GREEN` を持つ
PREMISE = "Red テストと受入基準は、実装が前の版の状態にあることを前提にしない"
KEPT_GREEN = "周の前に緑だった Red テストが、周の後も緑のままであること"

# 生成したファイルの印。**これを持つファイルだけを、消してよい・古いと言ってよい生成物に数える**
GENERATED = "spec-loop scaffold が生成（手で直さない。spec_ir.json を直して作り直す）"

PY_TYPES = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}


class Unjudged(Exception):
    """判定していない（2）。"""


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


spec_exit = _load("check_spec_exit", "check-spec-exit.py")
qa = spec_exit.pptx.qa
versions = _load("merge_versions", "merge-versions.py")
# 比べ方は `diff-versions.py` のもの（`compare_maps` は純粋な関数。重ねるのはこのスクリプトの `versions`）
diffs = _load("diff_versions", "diff-versions.py")


def merged(path: str) -> str:
    """重ね合わせた全体の中のパスを、利用者が開ける形（`build/merged/…`）で書く。"""
    return f"{MERGED_DIR}/{path}"


# ---------------------------------------------------------------- 中間表現を検査する

def one_line(value) -> bool:
    """空でない 1 行の文字列か（生成するコードのコメントと表のセルに載せるので、制御文字を許さない）。"""
    return (isinstance(value, str) and value.strip() != ""
            and not any(unicodedata.category(c) == "Cc" for c in value))


def module_name(value) -> bool:
    return isinstance(value, str) and all(NAME.fullmatch(part) and not keyword.iskeyword(part)
                                          for part in value.split("."))


def surrogates(obj, where: str = "spec_ir.json") -> list[str]:
    """孤立したサロゲート（`"\\ud800"` は JSON として読めるが UTF-8 で書けない）を、キーと値の全部から探す。

    **書く途中で落ちて契約を切り詰めないため**、生成より前に、どの文字列にも許さない。
    """
    if isinstance(obj, str):
        return [f"{where}: UTF-8 で書けない文字（孤立したサロゲート）を含む"] if any(
            unicodedata.category(c) == "Cs" for c in obj) else []
    if isinstance(obj, dict):
        found = []
        for key, value in obj.items():
            found += surrogates(key, f"{where}（キー）") + surrogates(value, f"{where}.{key}")
        return found
    if isinstance(obj, list):
        return [p for i, v in enumerate(obj) for p in surrogates(v, f"{where}[{i}]")]
    return []


def keys_problem(where: str, obj, required: set[str], optional: set[str] = frozenset()) -> list[str]:
    if not isinstance(obj, dict):
        return [f"{where}: オブジェクトでない"]
    problems = []
    for key in sorted(required - obj.keys()):
        problems.append(f"{where}: `{key}` が無い")
    for key in sorted(obj.keys() - required - optional):
        problems.append(f"{where}: 決まりに無いキー `{key}`（書いても生成物に現れない）")
    return problems


def value_fits(kind: str, value) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        # `NaN`・`Infinity` は JSON として読めてしまうが、値として比べられない。
        # 整数は `math.isfinite` に渡さない——桁が大きいと float に直せず OverflowError で落ちる
        if isinstance(value, bool):
            return False
        return isinstance(value, int) or (isinstance(value, float) and math.isfinite(value))
    return isinstance(value, bool)


def check_fields(where: str, fields, at_least_one: bool, output: bool) -> list[str]:
    if not isinstance(fields, dict):
        return [f"{where}: オブジェクトでない"]
    problems = []
    if at_least_one and not fields:
        problems.append(f"{where}: 項目が 1 つも無い")
    for name, field in fields.items():
        at = f"{where}.{name}"
        if not NAME.fullmatch(name) or keyword.iskeyword(name):
            problems.append(f"{at}: 項目名の形に反する（英小文字で始まり英小文字・数字・_、Python の予約語でない）")
        if output and name == RESERVED_OUTPUT:
            problems.append(f"{at}: 正常時の出力に `{RESERVED_OUTPUT}` は使えない（失敗の形と見分けられない）")
        found = keys_problem(at, field, {"type"}, {"enum"})
        if found:
            problems += found
            continue
        if field["type"] not in TYPES:
            problems.append(f"{at}: 型 `{field['type']}` は決まりに無い（{' / '.join(TYPES)}）")
            continue
        if "enum" in field:
            enum = field["enum"]
            if not isinstance(enum, list) or not enum:
                problems.append(f"{at}: enum は 1 つ以上の値の配列")
            elif not all(value_fits(field["type"], v) for v in enum):
                problems.append(f"{at}: enum の値が型 {field['type']} でない")
            # `json.dumps` の文字列で比べると `1` と `1.0` を別の値と数える
            elif any(a == b for i, a in enumerate(enum) for b in enum[i + 1:]):
                problems.append(f"{at}: enum の値が重複している")
    return problems


def check_values(where: str, values, fields: dict) -> list[str]:
    """`values` が `fields` の項目をちょうど全部、その型と enum で持つか。"""
    if not isinstance(values, dict):
        return [f"{where}: オブジェクトでない"]
    problems = []
    for name in sorted(fields.keys() - values.keys()):
        problems.append(f"{where}: 項目 `{name}` が無い")
    for name in sorted(values.keys() - fields.keys()):
        problems.append(f"{where}: 決まりに無い項目 `{name}`")
    for name in sorted(values.keys() & fields.keys()):
        field, value = fields[name], values[name]
        if not isinstance(field, dict) or field.get("type") not in TYPES:
            continue  # 項目の定義の誤りは別に出ている
        if not value_fits(field["type"], value):
            problems.append(f"{where}.{name}: 型 {field['type']} でない（{json.dumps(value, ensure_ascii=False)}）")
        elif isinstance(field.get("enum"), list) and value not in field["enum"]:
            problems.append(f"{where}.{name}: enum に無い値（{json.dumps(value, ensure_ascii=False)}）")
    return problems


def check_qa_refs(where: str, refs, answered: dict[str, dict[str, str]]) -> list[str]:
    if not isinstance(refs, list):
        return [f"{where}: 配列でない"]
    problems = []
    for no in refs:
        if not isinstance(no, str) or not QA_NO.fullmatch(no):
            problems.append(f"{where}: Q&A の No の形に反する（{no!r}）")
        elif no not in answered:
            problems.append(f"{where}: {no} は Q&A 表に無い")
        elif answered[no]["状態"].strip() != qa.DONE:
            problems.append(f"{where}: {no} は状態が {qa.DONE} でない")
    if len(set(map(str, refs))) != len(refs):
        problems.append(f"{where}: Q&A の No が重複している")
    return problems


def check_source(where: str, sources, whole: Path) -> list[str]:
    """`whole` は重ね合わせた全体の根。`source` はそこからのパス（`spec/order.md`）。"""
    if not isinstance(sources, list) or not sources:
        return [f"{where}: 仕様のファイルの配列（1 つ以上）でない"]
    problems = []
    spec_root = (whole / SPEC_DIR).resolve()
    for rel in sources:
        if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
            problems.append(f"{where}: 重ね合わせた全体の根からの相対パスでない（{rel!r}）")
            continue
        path = (whole / rel).resolve()
        if spec_root not in path.parents:
            problems.append(f"{where}: {rel} は {SPEC_DIR}/ の中に無い")
        elif any(part.startswith(".") for part in path.relative_to(spec_root).parts):
            # `check-spec-exit.py` は `.` で始まる場所を走査しない——そこを指すと未決定の印が関門を素通りする
            problems.append(f"{where}: {rel} は `.` で始まる場所にある（関門が未決定の印を見ない）")
        elif rel == IR_PATH or path == (whole / IR_PATH).resolve():
            problems.append(f"{where}: {rel} は中間表現そのもの（仕様の原文を指す）")
        elif not path.is_file():
            problems.append(f"{where}: {rel} が無い")
    return problems


def path_vars(path: str) -> list[str]:
    return PATH_VAR.findall(path)


def check_path_vars(where: str, path: str, fields: dict, templates: dict[str, str]) -> list[str]:
    problems = []
    if "{" in PATH_VAR.sub("", path) or "}" in PATH_VAR.sub("", path):
        problems.append(f"{where}: 波括弧が対になっていない: {path!r}")
    names = path_vars(path)
    for name in sorted(set(names)):
        if name not in fields:
            problems.append(f"{where}: パスの変数 {{{name}}} が operation.input の項目に無い")
        if names.count(name) > 1:
            problems.append(f"{where}: パスの変数 {{{name}}} が重複している")
    # OpenAPI では変数の名前だけが違うパスは同じパスなので、並べると無効になる（メソッドが違っても）
    template = PATH_VAR.sub("{}", path)
    if templates.setdefault(template, path) != path:
        problems.append(f"{where}: {path} は {templates[template]} と変数の名前だけが違う（OpenAPI では同じパス）")
    return problems


def check_ir(ir, whole: Path, answered: dict[str, dict[str, str]], path_rules: bool = True) -> list[str]:
    """`path_rules` が偽なら、パスの変数の決まり（#289）を当てない——前の版の中間表現だけ（#319。`classify`）。"""
    problems = surrogates(ir)
    if problems:
        return problems + ["孤立したサロゲートを含む中間表現は、ほかの規則を見ない"]
    problems = keys_problem("spec_ir.json", ir, {"spec_ir_version", "title", "features"}, {"impl_module"})
    if problems and not isinstance(ir, dict):
        return problems
    # `1.0 == True == 1` なので、値ではなく型ごと見る
    if type(ir.get("spec_ir_version")) is not int or ir.get("spec_ir_version") != IR_VERSION:
        problems.append(f"spec_ir.json: spec_ir_version が {IR_VERSION} でない")
    if "impl_module" in ir and not module_name(ir["impl_module"]):
        problems.append(f"spec_ir.json: impl_module がモジュール名の形に反する: {ir['impl_module']!r}")
    if "title" in ir and not one_line(ir["title"]):
        problems.append("spec_ir.json: title が空か、1 行でない")
    features = ir.get("features")
    if not isinstance(features, list) or not features:
        problems.append("spec_ir.json: features が 1 つ以上の配列でない")
        return problems

    feature_ids, operation_ids, routes, case_ids = set(), set(), set(), set()
    templates = {}  # 変数の名前を消したパス → 最初に使ったパス
    type_names = {}  # pascal(operation.id) → 最初に使った operation.id
    for index, feature in enumerate(features):
        where = f"features[{index}]"
        found = keys_problem(where, feature, {"id", "title", "source", "qa", "operation", "cases"})
        if found:
            problems += found
            if not isinstance(feature, dict):
                continue
        fid = feature.get("id")
        if not isinstance(fid, str) or not FEATURE_ID.fullmatch(fid):
            problems.append(f"{where}: id の形に反する（F- に 3 桁以上の数字）: {fid!r}")
            fid = None
        elif fid in feature_ids:
            problems.append(f"{where}: id {fid} が重複している")
        else:
            feature_ids.add(fid)
            where = fid
        if "title" in feature and not one_line(feature["title"]):
            problems.append(f"{where}: title が空か、1 行でない")
        if "source" in feature:
            problems += check_source(f"{where}.source", feature["source"], whole)
        if "qa" in feature:
            problems += check_qa_refs(f"{where}.qa", feature["qa"], answered)

        op = feature.get("operation")
        fields_in, fields_out, errors = {}, {}, []
        if "operation" in feature:
            found = keys_problem(f"{where}.operation", op, {"id", "method", "path", "input", "output"}, {"errors"})
            problems += found
            if isinstance(op, dict):
                oid = op.get("id")
                if not isinstance(oid, str) or not NAME.fullmatch(oid) or keyword.iskeyword(oid):
                    problems.append(f"{where}.operation.id: 形に反する（英小文字で始まり英小文字・数字・_、Python の予約語でない）: {oid!r}")
                elif oid in operation_ids:
                    problems.append(f"{where}.operation.id: {oid} が重複している")
                elif pascal(oid) in type_names:
                    # `a_1` と `a1`・`foo_bar` と `foo__bar` は別の id だが、型の名前が同じになり上書きし合う
                    problems.append(f"{where}.operation.id: {oid} は {type_names[pascal(oid)]} と"
                                    f"同じ型の名前 {pascal(oid)}Input / {pascal(oid)}Output になる")
                else:
                    operation_ids.add(oid)
                    type_names[pascal(oid)] = oid
                method, path = op.get("method"), op.get("path")
                if method not in METHODS:
                    problems.append(f"{where}.operation.method: 決まりに無い（{' / '.join(METHODS)}）: {method!r}")
                if not isinstance(path, str) or not path.startswith("/") or not one_line(path):
                    problems.append(f"{where}.operation.path: / で始まる 1 行でない: {path!r}")
                # メソッドが決まりに無い（配列など）なら入口の重複は見ない——組にできず TypeError で落ちる
                elif method in METHODS and (method, path) in routes:
                    problems.append(f"{where}.operation: {method} {path} が重複している")
                elif method in METHODS:
                    routes.add((method, path))
                if "input" in op:
                    problems += check_fields(f"{where}.operation.input", op["input"], False, False)
                    fields_in = op["input"] if isinstance(op["input"], dict) else {}
                if path_rules and isinstance(path, str) and path.startswith("/") and one_line(path):
                    problems += check_path_vars(f"{where}.operation.path", path, fields_in, templates)
                if "output" in op:
                    problems += check_fields(f"{where}.operation.output", op["output"], True, True)
                    fields_out = op["output"] if isinstance(op["output"], dict) else {}
                errors = op.get("errors", [])
                if not isinstance(errors, list):
                    problems.append(f"{where}.operation.errors: 配列でない")
                    errors = []
                else:
                    for name in errors:
                        if not isinstance(name, str) or not ERROR_NAME.fullmatch(name):
                            problems.append(f"{where}.operation.errors: 名前の形に反する: {name!r}")
                    if len(set(map(str, errors))) != len(errors):
                        problems.append(f"{where}.operation.errors: 重複している")

        cases = feature.get("cases")
        if "cases" in feature and (not isinstance(cases, list) or not cases):
            problems.append(f"{where}.cases: 1 つ以上の配列でない")
            continue
        for cindex, case in enumerate(cases or []):
            at = f"{where}.cases[{cindex}]"
            found = keys_problem(at, case, {"id", "title", "input"}, {"expected", "error", "qa"})
            if found:
                problems += found
                if not isinstance(case, dict):
                    continue
            cid = case.get("id")
            if not isinstance(cid, str) or fid is None or not re.fullmatch(rf"{re.escape(fid)}-C[0-9]+", cid):
                problems.append(f"{at}: id の形に反する（<機能の id>-C<数字>）: {cid!r}")
            elif cid in case_ids:
                problems.append(f"{at}: id {cid} が重複している")
            else:
                case_ids.add(cid)
                at = cid
            if "title" in case and not one_line(case["title"]):
                problems.append(f"{at}: title が空か、1 行でない")
            if "input" in case:
                problems += check_values(f"{at}.input", case["input"], fields_in)
            if ("expected" in case) == ("error" in case):
                problems.append(f"{at}: expected と error のちょうど片方だけを書く")
            elif "expected" in case:
                problems += check_values(f"{at}.expected", case["expected"], fields_out)
            elif case["error"] not in errors:
                problems.append(f"{at}.error: operation.errors に無い: {case['error']!r}")
            if "qa" in case:
                problems += check_qa_refs(f"{at}.qa", case["qa"], answered)
    return problems


# ---------------------------------------------------------------- 入力を読む

def read_answered(path: Path) -> dict[str, dict[str, str]]:
    """Q&A 表の全行を No で引けるようにする（関門を通った後に呼ぶので、表は検査済み）。"""
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""))
    next(reader)
    rows = {}
    for fields in reader:
        if any(f.strip() for f in fields):
            row = dict(zip(qa.COLUMNS, fields))
            rows[row["No"].strip()] = row
    return rows


# dataclass は使わない——importlib で読み込むと sys.modules に無く、dataclass が落ちる（`diff-versions.py` と同じ）
class Loaded:
    """重ね合わせた全体から読んだもの。"""

    def __init__(self, ir: dict, raw: bytes, answered: dict, number: int, docs: Path) -> None:
        self.ir = ir
        self.raw = raw  # 中間表現のバイト（本文の指紋は機能単位なので、これ全体の sha256 は使わない。#290）
        self.answered = answered  # Q&A の行（No → 行）
        self.number = number  # 重ねた最後の版の番号
        self.docs = docs


def load(repo: Path, upto: int | None = None) -> tuple[int, list[str], Loaded | None]:
    """(終了コード, 出力する行, 読んだもの) を返す。

    `docs/` の版を**メモリ上で**重ね合わせ（`merge-versions.py` の `merge`。同じバイト）、一時ディレクトリに書いて、
    関門・中間表現の検査をそこに当てる。**`build/merged/` には書かない**——`--check`・`--dry-run` は何も書かない。
    `upto` を渡せば v<upto> までを重ねる（無い版なら判定しない）。
    """
    docs = repo / DOCS
    if not docs.is_dir():
        raise Unjudged(f"{docs}: ディレクトリが無い（版は {DOCS}/v1/ から置く。references/versions.md）")
    # 版が 1 つも無い（版に分ける前の構成）は、決まりに反するのではなく移していない——判定しない
    probe: list[str] = []
    try:
        if not versions.find_versions(docs, probe) and not probe:
            raise Unjudged(f"{docs}: 版（v1 など）が 1 つも無い（版に分ける前の構成なら "
                           "references/versions.md の「移し方」で移す）。判定していない")
    except versions.Unreadable as exc:
        raise Unjudged(f"{exc}。重ね合わせていない")
    try:
        problems, found, _, rendered = versions.merge(docs, upto)
    except versions.Unreadable as exc:
        raise Unjudged(f"{exc}。重ね合わせていない")
    except RecursionError:
        # 版の中間表現の入れ子が深すぎて JSON として読めない（`merge-versions.py` は捕まえない）
        raise Unjudged("版の中間表現を読めない（入れ子が深すぎる）。重ね合わせていない")
    if problems:
        return 1, problems + ["版の重ね合わせが決まりに反する（references/versions.md）。生成しない"], None
    if IR_PATH not in rendered:
        raise Unjudged(f"重ね合わせた全体に {IR_PATH} が無い（どの版にも中間表現が無い）。判定していない")
    code, lines, ir, answered = read_whole(rendered, gate=True)
    if code:
        return code, lines, None
    number = upto if upto is not None else len(found)
    return 0, [], Loaded(ir, rendered[IR_PATH], answered, number, docs)


def read_whole(rendered: dict[str, bytes], gate: bool) -> tuple[int, list[str], dict | None, dict]:
    """重ね合わせた全体を一時ディレクトリに置き、(終了コード, 出力する行, 中間表現, Q&A の行) を返す。

    `gate` なら関門（条件 1）も当てる——前の版の全体には当てない（その版の時点で通ったもので、後の版の Q&A は関わらない）。
    パスの変数の決まりも前の版には当てない（#319）——#289 より前の scaffold が通した版は、凍結していれば直せず、
    前の版の中間表現からは OpenAPI を作らない（ケースの比較・前の版の Red テスト・Issue の本文の前の版を指す行にしか使わない）。
    """
    with tempfile.TemporaryDirectory() as tmp:
        whole = Path(tmp)
        for rel, data in rendered.items():
            versions.put(whole / rel, data)

        def shown(lines: list[str]) -> list[str]:
            # 一時ディレクトリの名前ではなく、利用者が `merge-versions.py` で作れる場所で言う
            return [line.replace(str(whole), MERGED_DIR) for line in lines]

        if gate:
            code, lines = spec_exit.check(whole / QA_PATH, whole / SPEC_DIR)
            if code:
                return code, shown(lines) + ["関門（仕様レビューを抜ける条件 1）を通らない。生成しない"], None, {}
        raw = rendered[IR_PATH]
        try:
            ir = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            raise Unjudged(f"{merged(IR_PATH)}: 中間表現を読めない（{exc.__class__.__name__}: {exc}）")
        answered = read_answered(whole / QA_PATH) if (whole / QA_PATH).is_file() else {}
        if gate:
            # 暫定の回答は利用者が確かめていない。scaffold の経路はサインオフの照合を通らないので、
            # 中間表現が指すかどうかに依らず、残っていれば止める——指さない機能の仕様にも反映されている（抜ける条件 1 とは別の定義。#325）
            held = [no for no, row in answered.items() if row["状態"].strip() == qa.PROVISIONAL]
            if held:
                return 1, shown([f"{no}: 状態が {qa.PROVISIONAL}（利用者の確認待ち）" for no in held]) + [
                    f"{merged(QA_PATH)} に {qa.PROVISIONAL} の行が {len(held)} 件残る。"
                    "利用者に確かめてもらうまで生成しない（/spec-loop:req-loop）"], None, {}
        problems = check_ir(ir, whole, answered, path_rules=gate)
    if problems:
        return 1, problems + [f"中間表現が決まりに反する（{len(problems)} 件）。生成しない"], None, {}
    return 0, [], ir, answered


# ---------------------------------------------------------------- 生成する

def pascal(name: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in name.split("_") if part)


def literal(values: dict) -> str:
    return "{" + ", ".join(f"{k!r}: {values[k]!r}" for k in sorted(values)) + "}"


def schema_of(field: dict) -> dict:
    out = {"type": field["type"]}
    if "enum" in field:
        out["enum"] = field["enum"]
    return out


def object_schema(fields: dict) -> dict:
    return {"type": "object", "required": sorted(fields), "additionalProperties": False,
            "properties": {name: schema_of(fields[name]) for name in sorted(fields)}}


def features_of(ir: dict) -> list[dict]:
    return sorted(ir["features"], key=lambda f: f["id"])


def openapi(ir: dict) -> str:
    paths, schemas = {}, {}
    for feature in features_of(ir):
        op = feature["operation"]
        base = pascal(op["id"])
        schemas[f"{base}Input"] = object_schema(op["input"])
        schemas[f"{base}Output"] = object_schema(op["output"])
        entry = {"operationId": op["id"], "summary": f"{feature['id']}: {feature['title']}"}
        in_path = path_vars(op["path"])
        rest = {name: op["input"][name] for name in op["input"] if name not in in_path}
        parameters = [{"name": name, "in": "path", "required": True, "schema": schema_of(op["input"][name])}
                      for name in in_path]
        if op["method"] in NO_BODY:
            parameters += [{"name": name, "in": "query", "required": True, "schema": schema_of(rest[name])}
                           for name in sorted(rest)]
        if parameters or op["method"] in NO_BODY:
            entry["parameters"] = parameters
        if op["method"] not in NO_BODY and rest:
            # パスの変数はボディに重ねない——変数を持たない入口は前と同じく入力の型そのものを指す
            body = f"{base}Input" if not in_path else f"{base}Body"
            if in_path:
                schemas[body] = object_schema(rest)
            entry["requestBody"] = {"required": True, "content": {"application/json": {
                "schema": {"$ref": f"#/components/schemas/{body}"}}}}
        responses = {"200": {"description": "正常", "content": {"application/json": {
            "schema": {"$ref": f"#/components/schemas/{base}Output"}}}}}
        if op.get("errors"):
            schemas[f"{base}Error"] = {"type": "object", "required": ["error"], "additionalProperties": False,
                                       "properties": {"error": {"type": "string", "enum": op["errors"]}}}
            responses["400"] = {"description": "失敗", "content": {"application/json": {
                "schema": {"$ref": f"#/components/schemas/{base}Error"}}}}
        entry["responses"] = responses
        paths.setdefault(op["path"], {})[op["method"].lower()] = entry
    doc = {
        "openapi": "3.1.0",
        "info": {"title": ir["title"], "version": f"spec-ir-{IR_VERSION}",
                 "description": GENERATED},
        "paths": {path: paths[path] for path in sorted(paths)},
        "components": {"schemas": {name: schemas[name] for name in sorted(schemas)}},
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def py_type(field: dict) -> str:
    if "enum" in field:
        return "Literal[" + ", ".join(repr(v) for v in field["enum"]) + "]"
    return PY_TYPES[field["type"]]


def typed_dict(name: str, fields: dict) -> list[str]:
    lines = [f"class {name}(TypedDict):"]
    lines += [f"    {field}: {py_type(fields[field])}" for field in sorted(fields)] or ["    pass"]
    return lines + ["", ""]


def types_py(ir: dict) -> str:
    lines = [f"# {GENERATED}", f"# {ir['title']} の入出力の型", "from __future__ import annotations", "",
             "from typing import Literal, TypedDict", "", ""]
    for feature in features_of(ir):
        op = feature["operation"]
        base = pascal(op["id"])
        lines.append(f"# {feature['id']}: {feature['title']}")
        lines += typed_dict(f"{base}Input", op["input"])
        lines += typed_dict(f"{base}Output", op["output"])
        if op.get("errors"):
            lines += typed_dict(f"{base}Error", {"error": {"type": "string", "enum": op["errors"]}})
    return "\n".join(lines).rstrip("\n") + "\n"


def case_order(case: dict) -> tuple[int, str]:
    # `int()` は桁が多すぎると ValueError で落ちる——桁数と文字列で数の順に並べる
    digits = case["id"].rsplit("C", 1)[1].lstrip("0")
    return len(digits), digits


def test_file(feature: dict) -> str:
    return f"test_{feature['id'].lower().replace('-', '_')}.py"


def test_method(case: dict) -> str:
    return f"test_{case['id'].lower().replace('-', '_')}"


def test_class(feature: dict) -> str:
    return "Test" + feature["id"].replace("-", "")


def output_types(op: dict) -> dict:
    """正常時の出力の項目と、失敗の形（`error`）の型。Red テストが値と一緒に型を見るのに使う。"""
    types = {name: field["type"] for name, field in op["output"].items()}
    types[RESERVED_OUTPUT] = "string"
    return types


def red_test(feature: dict, impl_module: str) -> str:
    op = feature["operation"]
    lines = [
        f"# {GENERATED}",
        f"# {feature['id']}: {feature['title']} の Red テスト",
        f"# 実装は `{impl_module}` モジュールの `{op['id']}(**input) -> dict`。失敗は {{\"error\": \"<名前>\"}} を返す。",
        "# 実装が無ければ、エラーではなく失敗になる。",
        "from __future__ import annotations",
        "",
        "import importlib",
        "import unittest",
        "",
        f"IMPL_MODULE = {impl_module!r}",
        f"OPERATION = {op['id']!r}",
        f"OUTPUT_TYPES = {literal(output_types(op))}",
        "",
        "",
        "def type_fits(kind, value):",
        "    # `assertEqual` は `True == 1 == 1.0` を等しいと見るので、型は別に見る",
        "    if isinstance(value, bool):",
        "        return kind == \"boolean\"",
        "    if kind == \"integer\":",
        "        return isinstance(value, int)",
        "    if kind == \"number\":",
        "        return isinstance(value, (int, float))",
        "    if kind == \"string\":",
        "        return isinstance(value, str)",
        "    return False",
        "",
        "",
        "def implementation():",
        "    try:",
        "        module = importlib.import_module(IMPL_MODULE)",
        "    except ModuleNotFoundError as exc:",
        "        if exc.name is not None and (exc.name == IMPL_MODULE or IMPL_MODULE.startswith(exc.name + \".\")):",
        "            return None",
        "        raise",
        "    return getattr(module, OPERATION, None)",
        "",
        "",
        f"class {test_class(feature)}(unittest.TestCase):",
        "    def call(self, given):",
        "        function = implementation()",
        "        if function is None:",
        "            self.fail(f\"未実装: {IMPL_MODULE}.{OPERATION} が無い\")",
        "        return function(**given)",
        "",
        "    def check(self, given, expected):",
        "        actual = self.call(given)",
        "        self.assertEqual(actual, expected)",
        "        for name, value in actual.items():",
        "            self.assertTrue(type_fits(OUTPUT_TYPES[name], value),",
        "                            f\"{name}: 型が {OUTPUT_TYPES[name]} でない（{value!r}）\")",
    ]
    for case in sorted(feature["cases"], key=case_order):
        expected = case["expected"] if "expected" in case else {"error": case["error"]}
        refs = "・".join(case.get("qa", []))
        lines += [
            "",
            f"    # {case['id']}: {case['title']}" + (f"（{refs}）" if refs else ""),
            f"    def {test_method(case)}(self):",
            f"        self.check({literal(case['input'])}, {literal(expected)})",
        ]
    lines += ["", "", "if __name__ == \"__main__\":", "    unittest.main()"]
    return "\n".join(lines) + "\n"


def sha256(data: str | bytes) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def fingerprint(feature: dict) -> str:
    """機能の指紋（`references/handoff-issue.md` の「機能の指紋で固定する」）。

    中間表現の中の機能のオブジェクトだけの sha256——**関係の無い機能を直しても変わらない**（全体の sha256 は変わる。#290）。
    **dev-loop の `scripts/spec-fingerprint.py` が同じ式の写しを持つ**（プラグインの外を相対パスで指せないため）——
    一致は `scripts/test-scaffold.py` が両方を走らせて見る。
    """
    return sha256(json.dumps(feature, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def cell(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("|", "\\|").replace("\n", "<br>")


def qa_sort_key(no: str) -> int:
    return int(no.split("-", 1)[1])


def qa_rows(refs: set[str], answered: dict, where: str) -> list[str]:
    if not refs:
        return ["この機能が根拠にした Q&A は無い。"]
    lines = ["| No | 質問 | 回答 | 反映先 |", "| --- | --- | --- | --- |"]
    for no in sorted(refs, key=qa_sort_key):
        row = answered[no]
        lines.append(f"| {no} | {cell(row['質問'])} | {cell(row['回答'])} | {cell(row['反映先'])} |")
    return lines + ["", f"（{where}から写した。）"]


# ---------------------------------------------------------------- 前の版と比べる

class Change:
    """Issue の本文 1 件になる機能の変化。"""

    def __init__(self, kind: str, feature: dict, before: dict | None = None) -> None:
        self.kind = kind  # ADD / MODIFY / REMOVE
        self.feature = feature  # この版の機能（削除なら前の版の機能）
        self.before = before  # 前の版の機能（変更・削除）
        self.reason = ""  # 削除の理由（removed.csv）


class Before:
    """前の版（v<n-1>）の全体から読んだもの。v1 なら空。"""

    def __init__(self, answered: dict | None = None, impl_module: str = DEFAULT_IMPL_MODULE, ir: dict | None = None) -> None:
        self.answered = answered or {}
        self.impl_module = impl_module
        self.ir = ir or {"features": []}


def classify(loaded: Loaded) -> tuple[int, list[str], list[Change], Before]:
    """(終了コード, 出力する行, 変化, 前の版) を返す。v<n> の全体と v<n-1> の全体を機能の `id` で比べる。

    前の版の中間表現も決まりに当てる——反すると、ケースの変化を Red テストの中身で比べられない（1）。
    **パスの変数の決まりだけは当てない**（`read_whole`。#319）。
    """
    number = loaded.number
    now = {f["id"]: f for f in features_of(loaded.ir)}
    if number == 1:
        return 0, [], [Change(ADD, f) for f in now.values()], Before()
    try:
        problems, found, _, rendered = versions.merge(loaded.docs, number - 1)
    except versions.Unreadable as exc:
        raise Unjudged(f"{exc}。前の版（v{number - 1}）を重ね合わせていない")
    if problems:
        return 1, problems + [f"前の版（v{number - 1}）の全体を重ねられない。生成しない"], [], Before()
    before_ir, before = {"features": []}, Before()
    if IR_PATH in rendered:
        code, lines, before_ir, answered = read_whole(rendered, gate=False)
        if code:
            return 1, [f"v{number - 1} の時点の {line}" for line in lines[:-1]] + [
                f"前の版（v{number - 1}）の中間表現が決まりに反するので、機能を追加・変更・削除に分けない。生成しない"], [], Before()
        before = Before(answered, before_ir.get("impl_module", DEFAULT_IMPL_MODULE), before_ir)
    reasons = diffs.removal_reasons(found[number - 1][1])
    kinds = {diffs.ADDED: ADD, diffs.CHANGED: MODIFY, diffs.REMOVED: REMOVE}
    old = {f["id"]: f for f in features_of(before_ir)}
    changes = []
    for diff in diffs.compare_maps(old, now):
        kind = kinds[diff.status]
        change = Change(kind, diff.before if kind == REMOVE else diff.after, diff.before)
        change.reason = reasons.get((versions.KIND_FEATURE, diff.key), "")
        changes.append(change)
    if before.impl_module != loaded.ir.get("impl_module", DEFAULT_IMPL_MODULE):
        # 実装のモジュールが変わると、機能が同じでも Red テストは全部、前の版の実装を探せずに失敗する
        moved = {c.feature["id"] for c in changes}
        changes += [Change(MODIFY, f, old[key]) for key, f in now.items() if key in old and key not in moved]
    return 0, [], sorted(changes, key=lambda c: c.feature["id"]), before


# 前の版の型で通った値は、広げた型にも合う（`type_fits`）——広げただけでは前の版の実装は落ちない
WIDENED = {("integer", "number")}


def behavior(feature: dict, case: dict, impl_module: str) -> tuple[str, ...]:
    """そのケースの Red テストが実行する中身のうち、型を除いたもの（題・コメントは入れない）。"""
    op = feature["operation"]
    expected = case["expected"] if "expected" in case else {"error": case["error"]}
    return impl_module, op["id"], literal(case["input"]), literal(expected)


def case_changed(before: dict, old: dict, impl_before: str, feature: dict, case: dict, impl_now: str) -> bool:
    """前の版で通った実装の上で、このケースの Red テストが失敗しうるか。

    型を見るのは期待にある項目だけ——Red テストは `actual == expected` のあとで `actual` の項目の型を見るので、
    期待に無い出力の項目・失敗のケースの `error` 以外の型は、そのケースの結果を変えない。
    """
    if behavior(before, old, impl_before) != behavior(feature, case, impl_now):
        return True
    was, now = output_types(before["operation"]), output_types(feature["operation"])
    expected = case["expected"] if "expected" in case else {"error": case["error"]}
    return any(was.get(name) != now.get(name) and (was.get(name), now.get(name)) not in WIDENED for name in expected)


def case_changes(change: Change, impl_now: str, impl_before: str) -> tuple[list[tuple[str, dict]], list[dict]]:
    """([(変化, ケース)], 消したケース) を返す。並びはケースの番号の順。"""
    cases = sorted(change.feature["cases"], key=case_order)
    if change.kind == REMOVE:
        return [(CASE_REMOVED, c) for c in cases], []
    if change.kind == ADD:
        return [(CASE_ADDED, c) for c in cases], []
    old = {c["id"]: c for c in change.before["cases"]}
    rows = []
    for case in cases:
        if case["id"] not in old:
            rows.append((CASE_ADDED, case))
        elif case_changed(change.before, old[case["id"]], impl_before, change.feature, case, impl_now):
            rows.append((CASE_CHANGED, case))
        else:
            rows.append((CASE_KEPT, case))
    ids = {case["id"] for case in cases}
    return rows, sorted((c for c in change.before["cases"] if c["id"] not in ids), key=case_order)


def test_name(feature: dict, case: dict) -> str:
    return f"{test_class(feature)}.{test_method(case)}"


def test_id(feature: dict, case: dict) -> str:
    """`unittest` が `scaffold/tests` から見つけたときの名前（モジュール.クラス.メソッド）。"""
    return f"{test_file(feature)[:-3]}.{test_name(feature, case)}"


def red_cases(rows: list[tuple[str, dict]]) -> list[dict]:
    """前の版の実装の上で失敗しうるケース（追加・変更）。"""
    return [case for status, case in rows if status in (CASE_ADDED, CASE_CHANGED)]


# ---------------------------------------------------------------- Issue の本文

def issue_title(change: Change, number: int) -> str:
    title = f"{change.feature['id']}: {change.feature['title']}"
    if change.kind == MODIFY:
        return f"{title}（v{number} で変更）"
    if change.kind == REMOVE:
        return f"{title}（v{number} で撤去）"
    return title


def issue_body(change: Change, loaded: Loaded, contract: dict[str, str], before: Before) -> str:
    feature, number = change.feature, loaded.number
    impl_now = loaded.ir.get("impl_module", DEFAULT_IMPL_MODULE)
    impl = before.impl_module if change.kind == REMOVE else impl_now
    op = feature["operation"]
    base = pascal(op["id"])
    names = [f"`{base}Input`", f"`{base}Output`"] + ([f"`{base}Error`"] if op.get("errors") else [])
    tfile = f"{OUT_DIR}/tests/{test_file(feature)}"
    rows, gone = case_changes(change, impl_now, before.impl_module)
    previous = f"v{number - 1}"
    kind_text = {
        ADD: "追加（v1 の機能）" if number == 1 else f"追加（v{number} で足した機能）",
        MODIFY: f"変更（{previous} の時点から v{number} で変えた機能）",
        REMOVE: f"削除（v{number} で消した機能。理由: {cell(change.reason)}）",
    }[change.kind]
    command = f"merge-versions.py {DOCS} {MERGED_DIR} --upto {number}"
    old_dir = PREVIOUS_DIR.format(number - 1)
    old_command = f"merge-versions.py {DOCS} {old_dir} --upto {number - 1}"
    lines = [
        HANDOFF_MARKER,
        FEATURE_MARKER.format(feature["id"]),
        CHANGE_MARKER.format(change.kind, previous if number > 1 else NO_BASE),
        "",
        "この Issue は spec-loop の `scaffold` が、確定した仕様から生成した。**本文を手で直さない。**",
        "",
        SECTIONS[0],
        "",
        f"- 機能: `{feature['id']}` {feature['title']}",
        f"- 変化: {kind_text}",
    ]
    if change.kind == REMOVE:
        lines += [
            f"- 中間表現（{previous} の時点）: `{old_dir}/{IR_PATH}` の `{feature['id']}`"
            f"（機能の指紋: `{fingerprint(feature)}`）——v{number} の `{merged(IR_PATH)}` にはこの機能が無い",
            f"- 仕様の原文（{previous} の時点）: " + "・".join(f"`{old_dir}/{s}`" for s in feature["source"]),
        ]
    else:
        lines += [
            f"- 中間表現: `{merged(IR_PATH)}` の `{feature['id']}`（機能の指紋: `{fingerprint(feature)}`）",
            "- 仕様の原文: " + "・".join(f"`{merged(s)}`" for s in feature["source"]),
        ]
    lines.append(f"- `{MERGED_DIR}/` は正本の版（`{DOCS}/v1/`…）を v{number} まで重ね合わせた全体で、commit しない——spec-loop の"
                 f" `{command}` で作る（**版を指定する**——後の版を足しても同じバイトになる）")
    if change.kind == REMOVE:
        lines.append(f"- `{old_dir}/` は {previous} までを重ね合わせた全体で、同じく commit しない——`{old_command}` で作る")
    if change.kind == REMOVE:
        lines += [f"- 撤去する API: `{op['method']} {op['path']}`（`operationId`: `{op['id']}`。`{OUT_DIR}/openapi.json` から消えた）",
                  "- 消えた型: " + "・".join(names) + f"（`{OUT_DIR}/types.py` から消えた）"]
    else:
        lines += [f"- API: `{op['method']} {op['path']}`（`{OUT_DIR}/openapi.json` の `operationId`: `{op['id']}`）",
                  f"- 型: `{OUT_DIR}/types.py` の " + "・".join(names)]
        old_op = change.before["operation"] if change.kind == MODIFY else None
        if old_op and (old_op["method"], old_op["path"], old_op["id"]) != (op["method"], op["path"], op["id"]):
            lines.append(f"- {previous} の API: `{old_op['method']} {old_op['path']}`（`operationId`: `{old_op['id']}`）")
    lines += ["", SECTIONS[1], ""]
    if change.kind == REMOVE:
        lines += [
            f"**この機能の実装（モジュール `{impl}` の関数 `{op['id']}`）を撤去し、{KEPT_GREEN}。**",
            "撤去した関数を呼ぶ箇所を残さない。下のケースの振る舞いは、もう求めない。",
            "同じ版で足した・変えたほかの機能のケースは、まだ実装されずに失敗していてよい——撤去の周はそれを緑にしない。",
        ]
    else:
        lines += [
            "**下の Red テストがすべて緑になること。** テストを書き換えて緑にしない——テストが仕様と食い違うと思ったら、",
            "それは仕様の穴である（下の「仕様の穴を見つけたら」）。",
        ]
        if change.kind == MODIFY:
            lines += [
                f"**`{CASE_KEPT}` のケースも緑であること**——前の版の実装の上で失敗しうるのは",
                f"`{CASE_ADDED}`・`{CASE_CHANGED}` のケースだけである。**ほかの機能は、{KEPT_GREEN}**",
                "（同じ版で足した・変えたほかの機能のケースは、この周の前に失敗していてよい）。",
            ]
    lines += ["", "| ケース | 変化 | 確かめること | Red テスト | Q&A |", "| --- | --- | --- | --- | --- |"]
    for status, case in rows:
        test = f"—（`{tfile}` ごと消した）" if change.kind == REMOVE else f"`{test_name(feature, case)}`"
        lines.append(f"| `{case['id']}` | {status} | {cell(case['title'])} | {test} | "
                     + ("・".join(case.get("qa", [])) or "—") + " |")
    if gone:
        lines += ["", f"{CASE_REMOVED}したケース（Red テストから外した。その振る舞いはもう求めない）: "
                  + "・".join(f"`{c['id']}` {cell(c['title'])}" for c in gone)]
    lines += ["", SECTIONS[2], ""]
    if change.kind == REMOVE:
        lines += [
            f"- 消したファイル: `{tfile}`（`scaffold.py` が消した。この機能の Red テストはもう無い）",
            "- 回帰（正本リポジトリの根で、撤去の前と後に回す。前に緑だったテストが後も緑であること）:",
            "",
            "```bash",
            f"python3 -m unittest discover -s {OUT_DIR}/tests",
            "```",
        ]
    else:
        red = red_cases(rows)
        lines += [
            f"- ファイル: `{tfile}`（sha256: `{sha256(contract[f'tests/{test_file(feature)}'])}`）",
            f"- 実装を置く場所: モジュール `{impl}` の関数 `{op['id']}(**input) -> dict`"
            "（失敗は `{\"error\": \"<名前>\"}` を返す）",
            "- 回し方（正本リポジトリの根で）:",
            "",
            "```bash",
            f"python3 -m unittest discover -s {OUT_DIR}/tests -p {test_file(feature)}",
            "```",
            "",
        ]
        if change.kind == ADD:
            lines.append("実装が無い状態では、ケースの数だけ失敗する。")
        else:
            lines += [f"前の版の実装の上で失敗しうるのは `{CASE_ADDED}`・`{CASE_CHANGED}` のケース（{len(red)} 件）だけで"
                      "（前の版の実装がもう満たすものは緑）、"
                      f"`{CASE_KEPT}` のケース（{len(rows) - len(red)} 件）は緑である。ほかの機能を含む回帰は",
                      f"`python3 -m unittest discover -s {OUT_DIR}/tests` で見る。"]
    lines += ["", SECTIONS[3], ""]
    refs = set(feature["qa"]) | {no for _, case in rows for no in case.get("qa", [])}
    if change.kind == REMOVE:
        lines += qa_rows(refs, before.answered, f"{previous} の時点の `{merged(QA_PATH)}` ")
    else:
        lines += qa_rows(refs, loaded.answered, f"生成した時点の `{merged(QA_PATH)}` ")
    lines += [
        "",
        SECTIONS[4],
        "",
        f"**実装で決めない。** 作業中の版の Q&A 表（`{DOCS}/v<n>/{QA_PATH}`）に起票元 `開発` で起票して、要求側に差し戻す。",
        "手順は dev-loop の `references/spec-gap.md` にある。",
    ]
    if change.kind == REMOVE:
        lines.append(f"**`{old_command}` で作った `{old_dir}/{IR_PATH}` での機能の指紋が上と違うか、"
                     f"`{command}` で作った `{merged(IR_PATH)}` にこの機能が残っているなら、"
                     "この Issue は手元の仕様と別の時点のもの**——")
    else:
        lines.append("**上のコマンドで作った手元の中間表現の機能の指紋か Red テストの sha256 が上と違うなら、"
                     "この Issue は手元の仕様と別の時点のもの**——")
    lines.append("実装に入らず、同じく差し戻す。")
    return "\n".join(lines) + "\n"


def render_contract(ir: dict) -> dict[str, str]:
    """{`scaffold/` からの相対パス: 中身} を返す。契約は全体から作る（変わっていない機能も）。"""
    impl_module = ir.get("impl_module", DEFAULT_IMPL_MODULE)
    contract = {"openapi.json": openapi(ir), "types.py": types_py(ir)}
    for feature in features_of(ir):
        contract[f"tests/{test_file(feature)}"] = red_test(feature, impl_module)
    return contract


def render_issues(changes: list[Change], loaded: Loaded, contract: dict[str, str], before: Before) -> dict[str, str]:
    """{Issue の本文のファイル名: 中身} を返す。本文は変わった機能だけ。"""
    impl_now = loaded.ir.get("impl_module", DEFAULT_IMPL_MODULE)
    issues, index = {}, []
    for change in changes:
        fid = change.feature["id"]
        rows, _ = case_changes(change, impl_now, before.impl_module)
        issues[f"{fid}.md"] = issue_body(change, loaded, contract, before)
        index.append({"feature": fid, "title": issue_title(change, loaded.number), "change": change.kind,
                      "body": f"{fid}.md",
                      "red": [] if change.kind == REMOVE else [test_name(change.feature, c) for c in red_cases(rows)]})
    issues["issues.json"] = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    return issues


# ---------------------------------------------------------------- Red の状態を見る

# 子のプロセスで走らせる——実装を読み込むのは正本リポジトリの根（`python3 -m unittest discover` と同じ）
DRIVER = r'''
import json
import sys
import unittest

outcomes = {}


class Result(unittest.TestResult):
    def addSuccess(self, test):
        outcomes[test.id()] = "pass"

    def addFailure(self, test, err):
        outcomes[test.id()] = "missing" if str(err[1]).startswith(sys.argv[2]) else "fail"

    def addError(self, test, err):
        outcomes[test.id()] = "error"

    def addSkip(self, test, reason):
        outcomes[test.id()] = "skip"

    def addExpectedFailure(self, test, err):
        outcomes[test.id()] = "skip"

    def addUnexpectedSuccess(self, test):
        outcomes[test.id()] = "pass"


unittest.defaultTestLoader.discover(sys.argv[1], top_level_dir=sys.argv[1]).run(Result())
print("\n" + json.dumps(outcomes, ensure_ascii=False))
'''
RED_TIMEOUT = 600


def run_tests(repo: Path, tests: Path) -> dict:
    """`tests` の Red テストを正本リポジトリの根で走らせ、{テストの名前: 結果} を返す。走らせられなければ ValueError など。"""
    # -B: 正本リポジトリに __pycache__ を書かない（`--red-check` は何も書かない）
    proc = subprocess.run([sys.executable, "-B", "-c", DRIVER, str(tests), MISSING], cwd=repo,
                          capture_output=True, text=True, timeout=RED_TIMEOUT)
    outcomes = json.loads(proc.stdout.rstrip("\n").rsplit("\n", 1)[-1])
    if proc.returncode != 0 or not isinstance(outcomes, dict):
        raise ValueError(proc.stderr[-400:])
    return outcomes


def previous_outcomes(repo: Path, before: Before) -> dict:
    """前の版（v<n-1>）の全体の Red テストを、同じ実装に当てた結果。v1 なら空。

    **`scaffold/` には書かない**——一時ディレクトリに作って走らせる（`--red-check` は何も書かない）。
    """
    features = features_of(before.ir)
    if not features:
        return {}
    with tempfile.TemporaryDirectory(prefix="scaffold-previous-") as tmp:
        tests = Path(tmp) / "tests"
        tests.mkdir()
        for feature in features:
            (tests / test_file(feature)).write_text(red_test(feature, before.impl_module), encoding="utf-8")
        return run_tests(repo, tests)


def red_check(repo: Path, loaded: Loaded, changes: list[Change], before: Before, in_progress: bool) -> int:
    """ケースごとに、作業中の版の Red テストと前の版の Red テストの結果を並べて、実装の状態を見る。

    **実装が前の版の状態にあることを前提にしない**（`PREMISE`）——前の版の Red テストを同じ実装に当てて確かめる。
    `in_progress`: 作り直しの経路。追加・変更のケースは、前の版と作業中の版のどちらの期待を満たしてもよい。
    """
    impl_now = loaded.ir.get("impl_module", DEFAULT_IMPL_MODULE)
    red = set()
    for change in changes:
        if change.kind != REMOVE:
            rows, _ = case_changes(change, impl_now, before.impl_module)
            red |= {test_id(change.feature, case) for case in red_cases(rows)}
    expected = [test_id(f, c) for f in features_of(loaded.ir) for c in sorted(f["cases"], key=case_order)]
    try:
        outcomes = run_tests(repo, Path(OUT_DIR) / "tests")
        previous = previous_outcomes(repo, before)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Red テストを走らせられない（{exc.__class__.__name__}: {exc}）。判定していない", file=sys.stderr)
        return 2
    green = [t for t in expected if t not in red]
    if expected and green and all(outcomes.get(t) == "missing" for t in expected):
        print(f"実装が無い（どの Red テストも「{MISSING.strip()}」で失敗した）。回帰のケース {len(green)} 件を判定していない"
              f"——前の版の実装を読み込める場所で走らせる", file=sys.stderr)
        return 2
    problems, failing, satisfied, done = [], [], [], []
    for name in expected:
        got, was = outcomes.get(name), previous.get(name)
        if name in red:
            # 入力の名前や形を変える変更では、呼び出しの形が合わない側の版の Red テストはエラーで落ちる
            # ——もう一方の版のテストが緑なら、エラーはその版の「失敗」と同じに読む
            if got == "error" and was == "pass":
                got = "fail"
            elif was == "error" and got == "pass":
                was = "fail"
        if got is None:
            problems.append(f"{name}: 走らなかった")
        elif got in ("error", "skip"):
            problems.append(f"{name}: {'エラー' if got == 'error' else '飛ばされた'}（失敗でも緑でもない）")
        elif name not in red:
            if got != "pass":
                problems.append(f"{name}: {CASE_KEPT}のケースなのに失敗した")
        elif was in ("error", "skip"):
            problems.append(f"{name}: 前の版の Red テストが{'エラー' if was == 'error' else '飛ばされた'}"
                            "（前の版の状態を判定できない）")
        elif got != "pass" and was not in (None, "pass") and (got, was) != ("missing", "missing"):
            # どちらの版でも「実装が無い」は食い違いではない——片方だけなら、もう片方の期待を満たしていない
            # 作り直しでは、実装はもう前の版の状態に無いはず——食い違いはたいてい作りかけの実装の誤り（#300）
            problems.append(f"{name}: {CASE_ADDED}・{CASE_CHANGED}のケースが、前の版の期待も作業中の版の期待も満たさない"
                            + ("（作りかけの実装の誤りか、前の版の仕様とも食い違う）" if in_progress
                               else "（前の版の仕様とも食い違う）"))
        elif got != "pass":
            failing.append(name)
        elif was in (None, "pass"):
            satisfied.append(name)
        elif in_progress:
            done.append(name)
        else:
            problems.append(f"{name}: 前の版の期待を満たさず、作業中の版の期待をもう満たす——実装は前の版の状態に無い"
                            "（この版をもう実装し始めた作り直しなら --in-progress）")
    for line in problems:
        print(line, file=sys.stderr)
    if problems:
        print(f"Red の状態が期待と違う（{len(problems)} 件）", file=sys.stderr)
        return 1
    for name in satisfied:
        print(f"もう緑: {name}（{CASE_ADDED}・{CASE_CHANGED}のケースを、前の版の実装がもう満たす——"
              "Red テストはこの変化を判別しない。中間表現が仕様のとおりかを確かめる）")
    summary = (f"Red の状態は期待どおり: 失敗 {len(failing)} 件（{CASE_ADDED}・{CASE_CHANGED}）・"
               f"緑 {len(green)} 件（{CASE_KEPT}）")
    if satisfied:
        summary += f"・もう緑 {len(satisfied)} 件（{CASE_ADDED}・{CASE_CHANGED}。前の版の実装がもう満たす）"
    if in_progress:
        summary += f"・実装済み {len(done)} 件（{CASE_ADDED}・{CASE_CHANGED}。作り直しの経路）"
    print(summary)
    return 0


# ---------------------------------------------------------------- 書く・比べる

def generated_tests(out: Path) -> set[str]:
    """`scaffold/tests/` にある、生成の印を持つ Red テスト（`tests/<名前>`）。"""
    found = set()
    tests = out / "tests"
    if tests.is_dir():
        for path in tests.glob("test_*.py"):
            try:
                head = path.read_text(encoding="utf-8").split("\n", 1)[0]
            except (OSError, UnicodeDecodeError):
                continue
            if GENERATED in head:
                found.add(f"tests/{path.name}")
    return found


def stale(out: Path, contract: dict[str, str]) -> list[str]:
    problems = []
    for rel, text in contract.items():
        path = out / rel
        try:
            current = path.read_bytes()
        except OSError:
            problems.append(f"{OUT_DIR}/{rel}: 無い（生成していない）")
            continue
        # 文字列で読むと改行が正規化され、CRLF に書き換えたものを新しいと言う
        if current != text.encode("utf-8"):
            problems.append(f"{OUT_DIR}/{rel}: 今の入力から作るものと違う（古い・手で直した）")
    for rel in sorted(generated_tests(out) - contract.keys()):
        problems.append(f"{OUT_DIR}/{rel}: 中間表現に無い機能の Red テストが残っている")
    return problems


def clear_issues(repo: Path) -> None:
    path = repo / ISSUES_DIR
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def write(repo: Path, contract: dict[str, str], issues: dict[str, str]) -> None:
    # **1 つ目のファイルに触る前に、全部をバイトにする**——符号化で落ちるなら、何も書かないうちに落ちる
    contract_bytes = {rel: text.encode("utf-8") for rel, text in contract.items()}
    issue_bytes = {name: text.encode("utf-8") for name, text in issues.items()}
    # **契約に触る前に前の Issue の本文を消す**——書き込みが途中で失敗しても、古い本文が新しい契約と並ばない
    clear_issues(repo)
    out = repo / OUT_DIR
    for rel in sorted(generated_tests(out) - contract.keys()):
        (out / rel).unlink()
    for rel, data in contract_bytes.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    target = repo / ISSUES_DIR
    target.mkdir(parents=True)
    for name, data in issue_bytes.items():
        (target / name).write_bytes(data)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--upto")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--red-check", action="store_true")
    parser.add_argument("--in-progress", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    repo = Path(args.repo)
    writing = not (args.check or args.dry_run or args.red_check)
    if args.upto is not None:
        if not re.fullmatch(r"[1-9][0-9]*", args.upto):
            print("--upto には 1 以上の整数を渡す", file=sys.stderr)
            return 2
        if not (args.check or args.dry_run):
            # 古い版の契約を置くと、作業中の版の Issue が指すものと食い違う
            print("--upto は --check か --dry-run と一緒にだけ使う（書く生成・--red-check は作業中の版に当てる）",
                  file=sys.stderr)
            return 2
        args.upto = int(args.upto)
    if args.in_progress and not args.red_check:
        print("--in-progress は --red-check と一緒にだけ使う（作り直しの経路で Red の状態を見る）", file=sys.stderr)
        return 2
    if not repo.is_dir():
        print(f"{repo}: ディレクトリが無い。判定していない", file=sys.stderr)
        return 2
    try:
        return run(repo, args, writing)
    except Exception as exc:  # 予期しない失敗も「作らなかった」(1) と区別し、古い Issue の本文を残さない
        lines = [f"予期しない失敗（{exc.__class__.__name__}: {exc}）。判定していない"]
        if writing:
            try:
                clear_issues(repo)
                lines.append(f"前の Issue の本文（{ISSUES_DIR}/）は消した。"
                             f"{OUT_DIR}/ は一部だけ書かれたかもしれない——--check で確かめる")
            except OSError as again:
                lines.append(f"前の Issue の本文（{ISSUES_DIR}/）を消せなかった（{again}）——登録しないこと")
        for line in lines:
            print(line, file=sys.stderr)
        return 2


def fail(repo: Path, writing: bool, code: int, lines: list[str]) -> int:
    if writing:
        clear_issues(repo)
        lines = lines + [f"前の Issue の本文（{ISSUES_DIR}/）は消した"]
    for line in lines:
        print(line, file=sys.stderr)
    return code


def run(repo: Path, args, writing: bool) -> int:
    try:
        code, lines, loaded = load(repo, args.upto)
    except Unjudged as exc:
        code, lines = 2, [str(exc)]
    if code:
        return fail(repo, writing, code, lines)

    contract = render_contract(loaded.ir)
    features = len(loaded.ir["features"])
    cases = sum(len(f["cases"]) for f in loaded.ir["features"])
    if args.check:
        problems = stale(repo / OUT_DIR, contract)
        for line in problems:
            print(line, file=sys.stderr)
        if problems:
            print(f"{OUT_DIR}/ が古い（{len(problems)} 件）。scaffold.py で作り直す", file=sys.stderr)
            return 1
        print(f"{OUT_DIR}/ は新しい（v{loaded.number} まで・機能 {features} 件・ケース {cases} 件）")
        return 0

    try:
        code, lines, changes, before = classify(loaded)
    except Unjudged as exc:
        code, lines = 2, [str(exc)]
    if code:
        return fail(repo, writing, code, lines)
    if args.red_check:
        problems = stale(repo / OUT_DIR, contract)
        if problems:
            for line in problems:
                print(line, file=sys.stderr)
            print(f"{OUT_DIR}/ が古い（{len(problems)} 件）。作り直してから Red の状態を見る", file=sys.stderr)
            return 1
        return red_check(repo, loaded, changes, before, args.in_progress)
    issues = render_issues(changes, loaded, contract, before)
    counted = "・".join(f"{kind} {sum(1 for c in changes if c.kind == kind)}" for kind in (ADD, MODIFY, REMOVE))
    summary = (f"機能 {features} 件・ケース {cases} 件。Issue の本文 {len(changes)} 件（{counted}）。"
               f"v{loaded.number - 1} から変わっていない機能の本文は作らない" if loaded.number > 1 else
               f"機能 {features} 件・ケース {cases} 件。Issue の本文 {len(changes)} 件（{counted}）")
    if args.dry_run:
        print(f"作れる（{summary}）。何も書いていない")
        return 0
    write(repo, contract, issues)
    print(f"作った: {OUT_DIR}/ と {ISSUES_DIR}/（{summary}）")
    print("**条件 2〜5 は判定していない**——spec-review が「抜けた」と報告したことを確かめてから登録する")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
