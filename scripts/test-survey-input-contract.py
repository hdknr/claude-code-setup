#!/usr/bin/env python3
"""`survey-input-contract.py`（screen-spec の、画面の入力の項目と API の入力の照らし合わせを数える調べる道具。#1596）の回帰テスト。

    python3 scripts/test-survey-input-contract.py

**本体はプラグインの中にある**（`plugins/screen-spec/scripts/`）。`check-screens.py` と spec-loop のスクリプトを読み込むので、
一時ディレクトリに `plugins/screen-spec/`（本体）と `plugins/spec-loop/`（本物の spec-loop の `.claude-plugin/` と `scripts/` の写し）を並べて、`python3 -I` で走らせる。

見るもの（計画ファイル `docs/plans/issue-1596.md` の受入基準）:

1. **陽性対照**——編集できる入力の項目 8 つが保存の入口の入力に無い合成の試料で、順向きの食い違いが 8 件と出る（`positive-8`）。
2. **引けない箇所の理由ごとの件数**——画面（機能が空・中間表現に無い・入力を持つ入口が無い・1 つに決まらない・対応の CSV の入口が中間表現に無い）と
   項目（画面の入口が決まらない・当たるフィールドが無い・2 つ以上・画面が表に無い）。
3. **逆向き**（指されない・システムが埋めると宣言・パスの変数）と、照らさなかった入口の数。
4. **入れ子**（`rows[].x`・`a.b`・`m[]`）。5. **`tab` の親を辿る**（循環で止まる）。6. **版の重ね合わせ**（`--upto`）。
7. **読むだけ**——どの試料でも、実行の前後で正本・対応の CSV・プラグインのバイトが変わらず、`__pycache__` を書かない。
8. **名前を出さない**——終了コード 0 の試料の既定の出力に、試料の目印（画面名・項目名・機能の題・入口の id・フィールドの名前）と画面ID・項目の番号が出ない。`--detail` のときだけ ID とパスが出る。
9. **関門ではない**（食い違いがあっても 0）・照らすものが無ければ 3。10. **止まり方**（2・4）。
11. **本体の定数が `plugins/screen-spec/references/input-contract.md` と一致する**（崩すと落ちることも見る）。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、`HOME` を一時ディレクトリにし、`CLAUDE_CONFIG_DIR`・`SCREEN_SPEC_SPEC_LOOP` を外す。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
変異の数は、本体の docstring の「守ること」の行の数以上（テストが数えて見る）。
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "screen-spec"
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
TARGET = "survey-input-contract.py"
DOC = PLUGIN / "references" / "input-contract.md"

S_HEAD = "画面ID,画面名,種別,親画面,主たる利用者,ステータス,参考資料,目的と背景,できること,機能,帳票,仕様書,根拠\n"
I_HEAD = "番号,画面ID,まとまり,並び順,項目名,種類,中身,例,必須,入力チェック,エラーメッセージ,並び替え,絞り込み,根拠\n"
T_HEAD = "番号,遷移元,きっかけ,操作,条件,遷移先,結果,根拠\n"
SCREENS = "requirements/screens/data/screens.csv"
ITEMS = "requirements/screens/data/screen-items.csv"
TRANSITIONS = "requirements/screens/data/transitions.csv"
IR = "spec/spec_ir.json"
MARKERS = ("めじるし", "mejirushi")  # 名前に必ず入れる目印。既定の出力に出てはならない
ID_SHAPES = re.compile(r"(?<![A-Za-z0-9])(?:S|I)-[0-9]{3}")  # 試料の画面ID・項目の番号の形


def screen(sid: str, kind: str, features: str = "", parent: str = "") -> str:
    return f"{sid},画面めじるし{sid},{kind},{parent},担当者,記入中,,目的,できること,{features},,{sid}.md,F-001\n"


def item(number: str, sid: str, name: str, kind: str = "入力") -> str:
    required = "はい" if kind == "入力" else ""
    body = "" if kind == "ボタン" else "中身"
    return f"{number},{sid},まとまり,1,{name},{kind},{body},,{required},,,,,F-001\n"


def field(kind: str = "string") -> dict:
    return {"type": kind}


def feature(fid: str, oid: str, inputs: dict, method: str = "POST", path: str | None = None) -> dict:
    return {"id": fid, "title": f"題めじるし{fid}", "source": ["spec/a.md"], "qa": [],
            "operation": {"id": oid, "method": method, "path": path or f"/{oid}", "input": inputs,
                          "output": {"ok": {"type": "boolean"}}, "errors": []},
            "cases": [{"id": f"{fid}-C1", "title": "t", "input": {}, "expected": {"ok": True}}]}


def ir(*features: dict) -> str:
    return json.dumps({"spec_ir_version": 1, "title": "仕様", "features": list(features)}, ensure_ascii=False)


SEARCH = feature("F-001", "op_mejirushi_search", {"q": field()}, method="GET")
SAVE_INPUT = {"fld_mejirushi_a": field(), "fld_mejirushi_b": field(), "order_id": field(), "version": field("integer"), "memo": field()}
SAVE = feature("F-002", "op_mejirushi_save", SAVE_INPUT, path="/bundles/{order_id}")


def tables(screens: str, items: str, version: int = 1) -> dict[str, str]:
    return {f"v{version}/{SCREENS}": S_HEAD + screens, f"v{version}/{ITEMS}": I_HEAD + items, f"v{version}/{TRANSITIONS}": T_HEAD}


def positive_files() -> dict[str, str]:
    # S-002 は機能を 2 つ挙げる（入力を持つ入口が 2 つ——対応の CSV が無ければ決まらない）。10 個の入力のうち 2 つは在るパス、8 つは無いパス、1 つは保存しない
    items = "".join(item(f"I-1{n:02d}", "S-002", f"項目めじるし{n}") for n in range(1, 12)) + item("I-150", "S-002", "保存めじるし", "ボタン")
    files = tables(screen("S-001", "top", "F-001") + screen("S-002", "form", "F-001、F-002"), items)
    files[f"v1/{IR}"] = ir(SEARCH, SAVE)
    return files


POSITIVE_MAP = ("対象,値\nS-002,op_mejirushi_save\nI-101,fld_mejirushi_a\nI-102,fld_mejirushi_b\n"
                + "".join(f"I-1{n:02d},fld_mejirushi_x{n}\n" for n in range(3, 11))
                + "I-111,保存しない\nop_mejirushi_save,version\n")


def no_map_files() -> dict[str, str]:
    # 機能の列で入口が決まる画面。項目名は日本語（引けない）・フィールド名そのもの・入れ子の末尾の名前
    inputs = {"code": field(), "rows": {"type": "array", "items": {"type": "object", "properties": {"qty": field("integer")}}}}
    items = (item("I-101", "S-002", "数量めじるし") + item("I-102", "S-002", "メモめじるし") + item("I-103", "S-002", "code")
             + item("I-104", "S-002", "qty"))
    files = tables(screen("S-001", "top") + screen("S-002", "form", "F-002"), items)
    files[f"v1/{IR}"] = ir(feature("F-002", "op_mejirushi_save", inputs))
    return files


def reasons_files() -> dict[str, str]:
    screens = (screen("S-001", "top", "F-001") + screen("S-003", "tab", "F-003、F-004", "S-001") + screen("S-005", "form")
               + screen("S-006", "form", "F-099") + screen("S-007", "form", "F-005") + screen("S-008", "form", "F-003"))
    items = (item("I-301", "S-003", "a") + item("I-501", "S-005", "a") + item("I-601", "S-006", "a") + item("I-701", "S-007", "a")
             + item("I-801", "S-008", "a") + item("I-901", "S-999", "a"))
    files = tables(screens, items)
    files[f"v1/{IR}"] = ir(SEARCH, feature("F-003", "op_mejirushi_c", {"a": field()}), feature("F-004", "op_mejirushi_d", {"a": field()}),
                           feature("F-005", "op_mejirushi_e", {}))
    return files


REASONS_MAP = "対象,値\nS-008,op_mejirushi_nothing\n"


def many_files() -> dict[str, str]:
    inputs = {"name": field(), "rows": {"type": "array", "items": {"type": "object", "properties": {"name": field()}}}}
    files = tables(screen("S-001", "top") + screen("S-002", "form", "F-002"), item("I-101", "S-002", "name"))
    files[f"v1/{IR}"] = ir(feature("F-002", "op_mejirushi_save", inputs))
    return files


def nested_files() -> dict[str, str]:
    inputs = {"rows": {"type": "array", "items": {"type": "object", "properties": {"code": field(), "qty": field("integer")}}},
              "meta": {"type": "object", "properties": {"note": field(), "tag": field()}},
              "m": {"type": "array", "items": {"type": "array", "items": field("integer")}},
              "tags": {"type": "array", "items": field()}}
    items = (item("I-101", "S-002", "x") + item("I-102", "S-002", "x") + item("I-103", "S-002", "x") + item("I-104", "S-002", "x")
             + item("I-105", "S-002", "x"))
    files = tables(screen("S-001", "top") + screen("S-002", "form", "F-002"), items)
    files[f"v1/{IR}"] = ir(feature("F-002", "op_mejirushi_save", inputs))
    return files


NESTED_MAP = "対象,値\nI-101,rows[].code\nI-102,meta\nI-103,rows[].bad\nI-104,m\nI-105,tags\n"


def tab_files(cycle: bool = False) -> dict[str, str]:
    if cycle:
        screens = screen("S-001", "top") + screen("S-002", "tab", "", "S-003") + screen("S-003", "tab", "", "S-002")
    else:
        screens = screen("S-001", "top") + screen("S-002", "form", "F-002") + screen("S-003", "tab", "", "S-002")
    files = tables(screens, item("I-301", "S-003", "memo"))
    files[f"v1/{IR}"] = ir(SAVE)
    return files


def v2_files() -> dict[str, str]:
    files = tables(screen("S-001", "top") + screen("S-002", "form", "F-002"), item("I-101", "S-002", "late"))
    files[f"v1/{IR}"] = ir(feature("F-002", "op_mejirushi_save", {"early": field()}))
    files[f"v2/{IR}"] = ir(feature("F-002", "op_mejirushi_save", {"early": field(), "late": field()}))
    return files


def malformed_files() -> dict[str, str]:
    files = no_map_files()
    data = json.loads(files[f"v1/{IR}"])
    data["features"].append({"id": "F-009", "title": "t"})
    files[f"v1/{IR}"] = json.dumps(data, ensure_ascii=False)
    return files


def without(files: dict[str, str], *keys: str) -> dict[str, str]:
    return {k: v for k, v in files.items() if k not in keys}


# (名前, 正本のファイル, 対応の CSV（None なら渡さない）, 追加の引数, 期待する終了コード, 出力に要る文字列, 出力に無い文字列)
CASES = [
    ("positive-8", positive_files(), POSITIVE_MAP, [], 0,
     ["入力の項目 11", "画面 2（form）: 入力 11 — 入口: 決まった（対応の CSV） — 一致 2・食い違い 8・保存しない 1・引けない 0",
      "入力の項目（順向き）: 一致 2・食い違い 8（パスが入口の入力に無い）・保存しない 1・引けない 0",
      "照らした入口 1・葉 5 — どの項目からも指されない 1・システムが埋めると宣言 1・パスの変数 1・照らさなかった入力のある入口 1",
      "画面の入口: 決まった 2（対応の CSV 1・機能の列 1・親の画面の機能の列 0）"], []),
    ("detail", positive_files(), POSITIVE_MAP, ["--detail"], 0,
     ["食い違い: S-002 I-103 → op_mejirushi_save fld_mejirushi_x3", "どの項目からも指されない: op_mejirushi_save memo", "公開の場に貼らない"],
     ["項目めじるし", "画面めじるし", "題めじるし"]),
    ("no-map-names", no_map_files(), None, [], 0,
     ["入口: 決まった（機能の列）", "一致 2・食い違い 0（パスが入口の入力に無い）・保存しない 0・引けない 2（画面の入口が決まらない 0・当たるフィールドが無い 2",
      "対応の CSV なし"], []),
    ("reasons", reasons_files(), REASONS_MAP, [], 0,
     ["引けない 5（機能が空 1・機能が中間表現に無い 1・入力を持つ入口が無い 1・入口が 1 つに決まらない 1・対応の CSV の入口が中間表現に無い 1）",
      "引けない 6（画面の入口が決まらない 5・当たるフィールドが無い 0・当たるフィールドが 2 つ以上 0・画面が表に無い 1）",
      "画面の表に無い画面: 入力 1", "照らした入口 0"], []),
    ("many-fields", many_files(), None, [], 0, ["当たるフィールドが 2 つ以上 1"], []),
    ("nested", nested_files(), NESTED_MAP, [], 0,
     ["一致 4・食い違い 1", "照らした入口 1・葉 6 — どの項目からも指されない 1・システムが埋めると宣言 0・パスの変数 0"], []),
    ("nested-detail", nested_files(), NESTED_MAP, ["--detail"], 0,
     ["食い違い: S-002 I-103 → op_mejirushi_save rows[].bad", "どの項目からも指されない: op_mejirushi_save rows[].qty"], ["meta.note", "meta.tag"]),
    ("tab-inherit", tab_files(), None, [], 0, ["画面 3（tab）: 入力 1 — 入口: 決まった（親の画面の機能の列） — 一致 1"], []),
    ("parent-cycle", tab_files(cycle=True), None, [], 0, ["機能が空 3", "画面の入口が決まらない 1"], []),
    ("v2-whole", v2_files(), None, [], 0, ["一致 1・食い違い 0"], []),
    ("v2-upto", v2_files(), None, ["--upto", "1"], 0, ["一致 0・食い違い 0", "当たるフィールドが無い 1"], []),
    ("malformed-feature", malformed_files(), None, [], 0, ["形の崩れた機能・入口を飛ばした 1"], []),
    ("nothing-tables", without(positive_files(), f"v1/{SCREENS}", f"v1/{ITEMS}", f"v1/{TRANSITIONS}"), None, [], 3, ["照らす画面が無い"], []),
    ("nothing-ir", without(positive_files(), f"v1/{IR}"), None, [], 3, ["照らす入口が無い"], []),
    ("bad-map-head", positive_files(), "対象,値段\n", [], 2, ["見出し行が 対象,値 でない"], []),
    ("bad-map-target", positive_files(), "対象,値\nZ-001,x\n", [], 2, ["対象が画面の表・項目の表・中間表現の入口のどれにも無い"], []),
    ("bad-map-empty", positive_files(), "対象,値\nI-101,\n", [], 2, ["空のセルがある"], []),
    ("bad-map-columns", positive_files(), "対象,値\nI-101,a,b\n", [], 2, ["列が 2 つでない"], []),
    ("bad-map-not-input", positive_files(), "対象,値\nI-150,fld_mejirushi_a\n", [], 2, ["種類が 入力 の項目でない"], []),
    ("bad-map-dup-screen", positive_files(), "対象,値\nS-002,op_mejirushi_save\nS-002,op_mejirushi_search\n", [], 2, ["同じ画面の行が 2 つある"], []),
    ("bad-map-dup-item", positive_files(), "対象,値\nI-101,fld_mejirushi_a\nI-101,fld_mejirushi_b\n", [], 2, ["同じ項目の行が 2 つある"], []),
    ("bad-map-path", positive_files(), "対象,値\nI-101,Bad-Path\n", [], 2, ["値がフィールドのパスの形でも 保存しない でもない"], []),
    ("bad-map-system", positive_files(), "対象,値\nop_mejirushi_save,nope\n", [], 2, ["システムが埋めると宣言したフィールドが入口の入力に無い"], []),
    ("bad-map-system-shape", positive_files(), "対象,値\nop_mejirushi_save,Nope\n", [], 2, ["値がフィールドのパスの形でない"], []),
    ("bad-map-ambiguous", {**positive_files(), f"v1/{ITEMS}": I_HEAD + item("S-002", "S-001", "a")}, "対象,値\nS-002,op_mejirushi_save\n", [], 2,
     ["対象が 画面と項目 の 2 つに当たる"], []),
    ("bad-map-missing", positive_files(), "@missing", [], 2, ["読めない"], []),
    ("bad-screens-head", {**positive_files(), f"v1/{SCREENS}": "画面ID,画面名\nS-001,a\n"}, None, [], 2, ["見出し行に 種別・親画面・機能 が無い"], []),
    ("bad-ir-json", {**positive_files(), f"v1/{IR}": "{"}, None, [], 2, ["判定していない"], []),
    ("bad-merge", {**{k.replace("v1/", "v3/"): v for k, v in positive_files().items()}, **positive_files()}, None, [], 2, ["判定していない"], []),
    ("bad-upto", positive_files(), None, ["--upto", "5"], 2, ["判定していない"], []),
    ("bad-args", positive_files(), None, ["--bogus"], 2, ["usage"], []),
    ("bad-detail-twice", positive_files(), None, ["--detail", "--detail"], 2, ["--detail は 1 度だけ"], []),
    ("stop-not-spec-loop", positive_files(), None, ["--spec-loop", "@plugin"], 4, ["spec-loop のプラグインの根でない"], []),
    ("stop-version", positive_files(), None, ["--spec-loop", "@old-spec-loop"], 4, ["対応の範囲の外"], []),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def make_plugins(root: Path, body: str | None = None) -> Path:
    """`<root>/plugins/screen-spec`（本体は `body` で差し替えられる）と `<root>/plugins/spec-loop` を並べ、screen-spec の根を返す。"""
    assert_in_tmp(root)
    plugin = root / "plugins" / "screen-spec"
    shutil.copytree(PLUGIN, plugin, ignore=shutil.ignore_patterns("__pycache__"))
    if body is not None:
        (plugin / "scripts" / TARGET).write_text(body, encoding="utf-8")
    for part in (".claude-plugin", "scripts"):
        shutil.copytree(SPEC_LOOP / part, root / "plugins" / "spec-loop" / part, ignore=shutil.ignore_patterns("__pycache__"))
    old = root / "old-spec-loop"
    for part in (".claude-plugin", "scripts"):
        shutil.copytree(SPEC_LOOP / part, old / part, ignore=shutil.ignore_patterns("__pycache__"))
    manifest = json.loads((old / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    manifest["version"] = "0.1.0"
    (old / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    return plugin


def run_case(plugins_root: Path, plugin: Path, case_dir: Path, case, check_readonly: bool = True) -> tuple[int, str]:
    name, files, map_text, args, _, _, _ = case
    assert_in_tmp(case_dir)
    docs = case_dir / "docs"
    docs.mkdir(parents=True)
    for rel, body in files.items():
        path = docs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    home = case_dir / "home"
    home.mkdir()
    extra: list[str] = []
    if map_text is not None:
        map_path = case_dir / "map.csv"
        if map_text != "@missing":
            map_path.write_text(map_text, encoding="utf-8")
        extra = ["--map", str(map_path)]
    real_args = [str(plugin) if a == "@plugin" else str(plugins_root / "old-spec-loop") if a == "@old-spec-loop" else a for a in args]
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR", "SCREEN_SPEC_SPEC_LOOP") and not k.startswith("GIT_")}
    env["HOME"] = str(home)
    before_case, before_plugins = snapshot(case_dir), snapshot(plugins_root)
    try:
        proc = subprocess.run([sys.executable, "-I", str(plugin / "scripts" / TARGET), str(docs), *extra, *real_args],
                              capture_output=True, text=True, env=env, cwd=case_dir, timeout=30)
    except subprocess.TimeoutExpired:
        return -1, "時間切れ"
    if check_readonly:
        check(f"{name}: 正本と対応の CSV を書かない", snapshot(case_dir) == before_case)
        check(f"{name}: プラグインを書かない（__pycache__ も）", snapshot(plugins_root) == before_plugins)
    return proc.returncode, proc.stdout + proc.stderr


def judge(case, code: int, out: str) -> list[str]:
    name, _, _, args, want, needed, banned = case
    problems = []
    if code != want:
        problems.append(f"終了コード {code}（期待 {want}）")
    problems += [f"出力に {s!r} が無い" for s in needed if s not in out]
    problems += [f"出力に {s!r} がある" for s in banned if s in out]
    if want == 0 and "--detail" not in args:
        problems += [f"既定の出力に目印 {m!r} がある" for m in MARKERS if m in out]
        found = ID_SHAPES.findall(out)
        if found:
            problems.append(f"既定の出力に画面ID・項目の番号 {found[:3]} がある")
    return problems


# ---- 本体の定数と原本

def load_target(path: Path):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("survey_input_contract_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def doc_table(text: str, heading: str) -> list[str]:
    """`### <heading>`（か `## <heading>`）の節の最初の表の、1 列目のバッククォートの値。"""
    match = re.search(rf"^#{{2,3}} {re.escape(heading)}\n(.*?)(?=^#{{2,3}} |\Z)", text, re.M | re.S)
    if not match:
        return []
    return [m.group(1) for m in re.finditer(r"^\| `([^`]+)` \|", match.group(1), re.M)]


def doc_problems(module, text: str) -> list[str]:
    out = []
    expected = {
        "画面の入口の決まり方": [module.BY_MAP, module.BY_FEATURE, module.BY_PARENT],
        "画面の入口が引けない理由": list(module.SCREEN_REASONS),
        "項目の結果": [module.MATCHED, module.MISMATCHED, module.SAVED_NOT, module.UNRESOLVED],
        "項目が引けない理由": list(module.ITEM_REASONS),
        "逆向き": [module.UNPOINTED, module.SYSTEM_FILLED, module.PATH_VARIABLE],
    }
    for heading, values in expected.items():
        if doc_table(text, heading) != values:
            out.append(f"「{heading}」の表が本体と違う（{doc_table(text, heading)} と {values}）")
    if f"見出し行は `{','.join(module.MAP_COLUMNS)}`" not in text:
        out.append("対応の CSV の見出し行が原本に無い")
    if f"`{module.NOT_SAVED}`" not in text:
        out.append("保存しない の書き方が原本に無い")
    codes = re.search(r"^## 終了コード\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    found = sorted(int(c) for c in re.findall(r"^\| ([0-9]) \|", codes.group(1), re.M)) if codes else []
    if found != sorted({module.EXIT_OK, module.EXIT_UNJUDGED, module.EXIT_NOTHING, module.EXIT_STOPPED}):
        out.append(f"終了コードの表が本体と違う（{found}）")
    return out


def keep_lines(source: str) -> int:
    """本体の docstring の「守ること」の行の数（`- ` で始まる行）。"""
    doc = source.split('"""', 2)[1]
    block = doc.split("**守ること**:", 1)[1].split("**守らないもの**", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("- "))


# (名前, 壊す前, 壊した後, 期待どおりでなくなるはずの試料)
MUTATIONS = [
    ("順向きの照らし合わせを外す", "            if mapped in paths:\n", "            if True:\n", "positive-8"),
    ("対応の CSV の画面の行を使わない", "        if sid in self.map_screen:\n", "        if False:\n", "positive-8"),
    ("親の画面を辿らない", "            row, how = parent, BY_PARENT\n", "            return [], how\n", "tab-inherit"),
    ("親の循環で止まらない", 'if parent is None or parent["画面ID"] in seen:', "if parent is None:", "parent-cycle"),
    ("入口が 2 つでも決める", "        if len(with_input) > 1:\n", "        if False:\n", "reasons"),
    ("当たるパスが 2 つでも引く", "                if len(hits) > 1:\n", "                if False:\n", "many-fields"),
    ("保存しないを先に見ない", "            if mapped == NOT_SAVED:\n", "            if False:\n", "positive-8"),
    ("親のパスで下の葉を指さない", ' or leaf.startswith(pointer + ".")', "", "nested"),
    ("配列の要素の下の葉を指さない", ' or leaf.startswith(pointer + "[]")', "", "nested"),
    ("パスの変数を分けない", "                if leaf in variables:\n", "                if False:\n", "positive-8"),
    ("システムが埋める宣言を分けない", "                elif any(covers(p, leaf) for p in system):\n", "                elif False:\n", "positive-8"),
    ("入力の無い画面の入口も逆向きに照らす", "resolved[sid][0] for sid in per_screen if sid in resolved", "resolved[sid][0] for sid in resolved", "positive-8"),
    ("既定の出力に画面ID を出す", 'label = f"画面 {order[sid]}', 'label = f"画面 {sid}', "positive-8"),
    ("宣言したパスが入力に在るかを見ない", "                elif value not in self.paths[target]:\n", "                elif False:\n", "bad-map-system"),
    ("入力でない項目を止めない", "                if target not in inputs:\n", "                if False:\n", "bad-map-not-input"),
    ("同じ画面の行を止めない", "                if target in self.map_screen:\n", "                if False:\n", "bad-map-dup-screen"),
    ("2 つの種類に当たる対象を止めない", "            elif len(kinds) > 1:\n", "            elif False:\n", "bad-map-ambiguous"),
    ("形の崩れた機能を黙って落とす", "                self.skipped += 1\n", "                pass\n", "malformed-feature"),
    ("末尾の名前で引かない", ' or last_name(p) == row["項目名"]', "", "no-map-names"),
    ("中間表現が無いのを 3 にしない", "        if ir_path not in rendered:\n", "        if False:\n", "nothing-ir"),
    ("画面の表が無いのを 3 にしない", "        if missing:\n            raise Nothing", "        if False:\n            raise Nothing", "nothing-tables"),
    ("__pycache__ を書く", "sys.dont_write_bytecode = True  #", "sys.dont_write_bytecode = False  #", "positive-8"),
    ("画面が表に無い項目を分けない", "            if sid not in resolved:\n", "            if False:\n", "reasons"),
    ("重ね合わせの違反で止めない", "        if problems:\n            raise Unjudged(\"重ね合わせ", "        if False:\n            raise Unjudged(\"重ね合わせ", "bad-merge"),
]


def main() -> int:
    source = (PLUGIN / "scripts" / TARGET).read_text(encoding="utf-8")
    by_name = {case[0]: case for case in CASES}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plugin = make_plugins(root / "base")
        for case in CASES:
            code, out = run_case(root / "base", plugin, root / "cases" / case[0], case)
            for problem in judge(case, code, out):
                failures.append(f"{case[0]}: {problem}\n--- 出力 ---\n{out}")

        # 本体の定数と原本
        module = load_target(PLUGIN / "scripts" / TARGET)
        text = DOC.read_text(encoding="utf-8")
        for problem in doc_problems(module, text):
            failures.append(f"原本との突き合わせ: {problem}")
        broken = text.replace("| `当たるフィールドが無い` |", "| `当たるフィールドが見つからない` |", 1)
        check("原本との突き合わせ: 原本を崩すと落ちる（陽性対照）", broken != text and bool(doc_problems(module, broken)))

        # 変異
        check("変異の数が「守ること」の行の数以上", len(MUTATIONS) >= keep_lines(source),
              f"変異 {len(MUTATIONS)}・守ること {keep_lines(source)}")
        for at, (label, old, new, case_name) in enumerate(MUTATIONS):
            if source.count(old) != 1:
                failures.append(f"変異「{label}」: 壊す箇所が本体に {source.count(old)} 回現れる（1 回であること）")
                continue
            mutant_root = root / f"mutant-{at}"
            mutant = make_plugins(mutant_root, source.replace(old, new, 1))
            case = by_name[case_name]
            if label == "__pycache__ を書く":
                before = snapshot(mutant_root)
                run_case(mutant_root, mutant, mutant_root / "case", case, check_readonly=False)
                killed = snapshot(mutant_root) != before
            else:
                code, out = run_case(mutant_root, mutant, mutant_root / "case", case, check_readonly=False)
                killed = bool(judge(case, code, out))
            check(f"変異「{label}」で {case_name} が期待どおりでなくなる", killed)
            shutil.rmtree(mutant_root)
    if failures:
        print(f"NG: {len(failures)} 件")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件・原本との突き合わせ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
