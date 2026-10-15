#!/usr/bin/env python3
"""確定した仕様の中間表現（`spec_ir.json`）から、dev-loop に渡すものを作る。

usage: python3 scaffold.py [--repo <正本リポジトリ>] [--impl-module <モジュール名>] [--check | --dry-run]

作るもの（置き場所の正は `references/tree.md`）:

- `scaffold/openapi.json`・`scaffold/types.py`・`scaffold/tests/test_<機能>.py`（Red テスト）——**commit する契約**
- `build/scaffold/issues/<機能の id>.md` と `issues.json`——**Issue の本文**（登録はスクリプトの外。`gh` を呼ばない）

**形の正は `references/spec-ir.md`（中間表現）と `references/handoff-issue.md`（Issue の本文）である**
（このプラグインの中にある）。下の定数（メソッド・型・番号の形・印・節）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-scaffold.py` が突き合わせて見る**。

**生成の前に、自分で関門を通す**——`check-spec-exit.py` の条件 1（反映済みでない Q&A・未決定の印が 0 件）を呼び、
通らなければ 1 バイトも書かない。**条件 2〜5 は判定しない**（判定役の報告で決まる。`scaffold` の本文）。
**全部を組み立ててから書く**ので、途中で落ちて一部だけ書くことはない。

- `--check`: 書かずに、置いてある `scaffold/` が今の入力から作るものと同じかを確かめる（鮮度）。
  **消した機能の Red テストが残っていても古いと言う**（生成の印のあるファイルだけを数える）。
- `--dry-run`: 関門と中間表現の検査だけをして、何も書かず何も消さない。

終了コード:

- 0: 作った（`--check` なら新しい・`--dry-run` なら作れる）
- 1: 作らなかった——関門の条件 1 を満たさない・中間表現が決まりに反する（全部を 1 行ずつ出す）・
  `--check` で古い。**Issue の本文の前の出力は消す**（古い本文を登録させない。`--check`・`--dry-run` では消さない）
- 2: 判定していない——引数の誤り・関門が判定していない・中間表現が無い／JSON として読めない。前の Issue の本文は消す

**`scaffold/` は失敗しても消さない**——commit 済みの契約で、古ければ `--check` が言う。

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う（`git` も要らない）。

**この生成が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **中間表現が仕様と意味で一致するか** | 書き起こしは判断（`scaffold` の仕事）。出所（`source` の実在・Q&A が `反映済み`）までを見る |
| **Red テストが仕様のケースを漏れなく持つか** | 中間表現に書いたケースだけが生成される。漏れは書き起こしの側で見る |
| **Python 以外の言語の型・テスト** | OpenAPI から対象リポジトリの道具で作る |
| **Issue を登録したか・登録した本文が同じか** | 登録はスクリプトの外（`gh issue create --body-file` に、生成した本文をそのまま渡す） |
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
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 置き場所（`references/tree.md` の写し）
QA_PATH = "docs/shared/qa.csv"
SPEC_DIR = "docs/spec"
IR_PATH = "docs/spec/spec_ir.json"
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
# 引数を持たないメソッド（入力はクエリに載せる）
NO_BODY = ("GET", "DELETE")

# `references/handoff-issue.md` の写し
HANDOFF_MARKER = "<!-- spec-loop-handoff: v1 -->"
FEATURE_MARKER = "<!-- spec-loop-feature: {} -->"
SECTIONS = ("## 仕様", "## 受入基準", "## Red テスト", "## Q&A の回答", "## 仕様の穴を見つけたら")

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


# ---------------------------------------------------------------- 中間表現を検査する

def one_line(value) -> bool:
    """空でない 1 行の文字列か（生成するコードのコメントと表のセルに載せるので、制御文字を許さない）。"""
    return (isinstance(value, str) and value.strip() != ""
            and not any(unicodedata.category(c) == "Cc" for c in value))


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
        # `NaN`・`Infinity` は JSON として読めてしまうが、値として比べられない
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
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
            elif len({json.dumps(v) for v in enum}) != len(enum):
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


def check_source(where: str, sources, repo: Path) -> list[str]:
    if not isinstance(sources, list) or not sources:
        return [f"{where}: 仕様のファイルの配列（1 つ以上）でない"]
    problems = []
    spec_root = (repo / SPEC_DIR).resolve()
    for rel in sources:
        if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
            problems.append(f"{where}: 正本の根からの相対パスでない（{rel!r}）")
            continue
        path = (repo / rel).resolve()
        if spec_root not in path.parents:
            problems.append(f"{where}: {rel} は {SPEC_DIR}/ の中に無い")
        elif rel == IR_PATH or path == (repo / IR_PATH).resolve():
            problems.append(f"{where}: {rel} は中間表現そのもの（仕様の原文を指す）")
        elif not path.is_file():
            problems.append(f"{where}: {rel} が無い")
    return problems


def check_ir(ir, repo: Path, answered: dict[str, dict[str, str]]) -> list[str]:
    problems = keys_problem("spec_ir.json", ir, {"spec_ir_version", "title", "features"})
    if problems and not isinstance(ir, dict):
        return problems
    if ir.get("spec_ir_version") != IR_VERSION or isinstance(ir.get("spec_ir_version"), bool):
        problems.append(f"spec_ir.json: spec_ir_version が {IR_VERSION} でない")
    if "title" in ir and not one_line(ir["title"]):
        problems.append("spec_ir.json: title が空か、1 行でない")
    features = ir.get("features")
    if not isinstance(features, list) or not features:
        problems.append("spec_ir.json: features が 1 つ以上の配列でない")
        return problems

    feature_ids, operation_ids, routes, case_ids = set(), set(), set(), set()
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
            problems += check_source(f"{where}.source", feature["source"], repo)
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
                else:
                    operation_ids.add(oid)
                method, path = op.get("method"), op.get("path")
                if method not in METHODS:
                    problems.append(f"{where}.operation.method: 決まりに無い（{' / '.join(METHODS)}）: {method!r}")
                if not isinstance(path, str) or not path.startswith("/") or not one_line(path):
                    problems.append(f"{where}.operation.path: / で始まる 1 行でない: {path!r}")
                elif (method, path) in routes:
                    problems.append(f"{where}.operation: {method} {path} が重複している")
                else:
                    routes.add((method, path))
                if "input" in op:
                    problems += check_fields(f"{where}.operation.input", op["input"], False, False)
                    fields_in = op["input"] if isinstance(op["input"], dict) else {}
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


def load(repo: Path) -> tuple[int, list[str], dict | None, bytes, dict]:
    """(終了コード, 出力する行, 中間表現, 中間表現のバイト, Q&A の行) を返す。"""
    code, lines = spec_exit.check(repo / QA_PATH, repo / SPEC_DIR)
    if code:
        return code, lines + ["関門（仕様レビューを抜ける条件 1）を通らない。生成しない"], None, b"", {}
    ir_path = repo / IR_PATH
    try:
        raw = ir_path.read_bytes()
        ir = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Unjudged(f"{ir_path}: 中間表現を読めない（{exc.__class__.__name__}: {exc}）")
    answered = read_answered(repo / QA_PATH)
    problems = check_ir(ir, repo, answered)
    if problems:
        return 1, problems + [f"中間表現が決まりに反する（{len(problems)} 件）。生成しない"], None, b"", {}
    return 0, [], ir, raw, answered


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
        if op["method"] in NO_BODY:
            entry["parameters"] = [{"name": name, "in": "query", "required": True, "schema": schema_of(op["input"][name])}
                                   for name in sorted(op["input"])]
        elif op["input"]:
            entry["requestBody"] = {"required": True, "content": {"application/json": {
                "schema": {"$ref": f"#/components/schemas/{base}Input"}}}}
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


def test_file(feature: dict) -> str:
    return f"test_{feature['id'].lower().replace('-', '_')}.py"


def test_method(case: dict) -> str:
    return f"test_{case['id'].lower().replace('-', '_')}"


def test_class(feature: dict) -> str:
    return "Test" + feature["id"].replace("-", "")


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
    ]
    for case in sorted(feature["cases"], key=lambda c: int(c["id"].rsplit("C", 1)[1])):
        expected = case["expected"] if "expected" in case else {"error": case["error"]}
        refs = "・".join(case.get("qa", []))
        lines += [
            "",
            f"    # {case['id']}: {case['title']}" + (f"（{refs}）" if refs else ""),
            f"    def {test_method(case)}(self):",
            f"        self.assertEqual(self.call({literal(case['input'])}), {literal(expected)})",
        ]
    lines += ["", "", "if __name__ == \"__main__\":", "    unittest.main()"]
    return "\n".join(lines) + "\n"


def sha256(data: str | bytes) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def cell(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("|", "\\|").replace("\n", "<br>")


def qa_sort_key(no: str) -> int:
    return int(no.split("-", 1)[1])


def issue_body(feature: dict, ir_sha: str, test_text: str, impl_module: str, answered: dict) -> str:
    op = feature["operation"]
    base = pascal(op["id"])
    names = [f"`{base}Input`", f"`{base}Output`"] + ([f"`{base}Error`"] if op.get("errors") else [])
    tfile = f"{OUT_DIR}/tests/{test_file(feature)}"
    cases = sorted(feature["cases"], key=lambda c: int(c["id"].rsplit("C", 1)[1]))
    refs = set(feature["qa"]) | {no for case in cases for no in case.get("qa", [])}
    lines = [
        HANDOFF_MARKER,
        FEATURE_MARKER.format(feature["id"]),
        "",
        "この Issue は spec-loop の `scaffold` が、確定した仕様から生成した。**本文を手で直さない。**",
        "",
        SECTIONS[0],
        "",
        f"- 機能: `{feature['id']}` {feature['title']}",
        f"- 中間表現: `{IR_PATH}`（sha256: `{ir_sha}`）",
        "- 仕様の原文: " + "・".join(f"`{s}`" for s in feature["source"]),
        f"- API: `{op['method']} {op['path']}`（`{OUT_DIR}/openapi.json` の `operationId`: `{op['id']}`）",
        f"- 型: `{OUT_DIR}/types.py` の " + "・".join(names),
        "",
        SECTIONS[1],
        "",
        "**下の Red テストがすべて緑になること。** テストを書き換えて緑にしない——テストが仕様と食い違うと思ったら、",
        "それは仕様の穴である（下の「仕様の穴を見つけたら」）。",
        "",
        "| ケース | 確かめること | Red テスト | Q&A |",
        "| --- | --- | --- | --- |",
    ]
    for case in cases:
        lines.append(f"| `{case['id']}` | {cell(case['title'])} | `{test_class(feature)}.{test_method(case)}` | "
                     + ("・".join(case.get("qa", [])) or "—") + " |")
    lines += [
        "",
        SECTIONS[2],
        "",
        f"- ファイル: `{tfile}`（sha256: `{sha256(test_text)}`）",
        f"- 実装を置く場所: モジュール `{impl_module}` の関数 `{op['id']}(**input) -> dict`"
        "（失敗は `{\"error\": \"<名前>\"}` を返す）",
        "- 回し方（正本リポジトリの根で）:",
        "",
        "```bash",
        f"python3 -m unittest discover -s {OUT_DIR}/tests -p {test_file(feature)}",
        "```",
        "",
        "実装が無い状態では、ケースの数だけ失敗する。",
        "",
        SECTIONS[3],
        "",
    ]
    if refs:
        lines += ["| No | 質問 | 回答 | 反映先 |", "| --- | --- | --- | --- |"]
        for no in sorted(refs, key=qa_sort_key):
            row = answered[no]
            lines.append(f"| {no} | {cell(row['質問'])} | {cell(row['回答'])} | {cell(row['反映先'])} |")
        lines.append("")
        lines.append(f"（生成した時点の `{QA_PATH}` から写した。）")
    else:
        lines.append("この機能が根拠にした Q&A は無い。")
    lines += [
        "",
        SECTIONS[4],
        "",
        f"**実装で決めない。** Q&A 表（`{QA_PATH}`）に起票元 `開発` で起票して、要求側に差し戻す。",
        "手順は dev-loop の `references/spec-gap.md` にある。",
        f"**手元の `{IR_PATH}` か Red テストの sha256 が上と違うなら、この Issue は手元の仕様と別の時点のもの**——",
        "実装に入らず、同じく差し戻す。",
    ]
    return "\n".join(lines) + "\n"


def render(ir: dict, raw: bytes, answered: dict, impl_module: str) -> tuple[dict[str, str], dict[str, str]]:
    """({`scaffold/` からの相対パス: 中身}, {Issue の本文のファイル名: 中身}) を返す。"""
    contract = {"openapi.json": openapi(ir), "types.py": types_py(ir)}
    issues, index = {}, []
    ir_sha = sha256(raw)
    for feature in features_of(ir):
        text = red_test(feature, impl_module)
        contract[f"tests/{test_file(feature)}"] = text
        issues[f"{feature['id']}.md"] = issue_body(feature, ir_sha, text, impl_module, answered)
        index.append({"feature": feature["id"], "title": f"{feature['id']}: {feature['title']}",
                      "body": f"{feature['id']}.md"})
    issues["issues.json"] = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    return contract, issues


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
            current = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            problems.append(f"{OUT_DIR}/{rel}: 無い（生成していない）")
            continue
        if current != text:
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
    out = repo / OUT_DIR
    for rel in sorted(generated_tests(out) - contract.keys()):
        (out / rel).unlink()
    for rel, text in contract.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    clear_issues(repo)
    target = repo / ISSUES_DIR
    target.mkdir(parents=True)
    for name, text in issues.items():
        (target / name).write_text(text, encoding="utf-8", newline="\n")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--impl-module", default="spec_impl")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    repo = Path(args.repo)
    writing = not (args.check or args.dry_run)
    if not all(NAME.fullmatch(part) and not keyword.iskeyword(part) for part in args.impl_module.split(".")):
        print(f"--impl-module: モジュール名の形に反する: {args.impl_module!r}", file=sys.stderr)
        return 2
    if not repo.is_dir():
        print(f"{repo}: ディレクトリが無い。判定していない", file=sys.stderr)
        return 2

    try:
        code, lines, ir, raw, answered = load(repo)
    except Unjudged as exc:
        code, lines = 2, [str(exc)]
    if code:
        if writing:
            clear_issues(repo)
            lines.append(f"前の Issue の本文（{ISSUES_DIR}/）は消した")
        for line in lines:
            print(line, file=sys.stderr)
        return code

    contract, issues = render(ir, raw, answered, args.impl_module)
    features = len(ir["features"])
    cases = sum(len(f["cases"]) for f in ir["features"])
    if args.check:
        problems = stale(repo / OUT_DIR, contract)
        for line in problems:
            print(line, file=sys.stderr)
        if problems:
            print(f"{OUT_DIR}/ が古い（{len(problems)} 件）。scaffold.py で作り直す", file=sys.stderr)
            return 1
        print(f"{OUT_DIR}/ は新しい（機能 {features} 件・ケース {cases} 件）")
        return 0
    if args.dry_run:
        print(f"作れる（機能 {features} 件・ケース {cases} 件）。何も書いていない")
        return 0
    write(repo, contract, issues)
    print(f"作った: {OUT_DIR}/（機能 {features} 件・ケース {cases} 件の Red テスト）・{ISSUES_DIR}/（Issue の本文 {features} 件）")
    print("**条件 2〜5 は判定していない**——spec-review が「抜けた」と報告したことを確かめてから登録する")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
