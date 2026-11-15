#!/usr/bin/env python3
"""`tlc-trace.py`（spec-loop の TLC の反例の JSON から trace ケースを作る変換。#1020）の回帰テスト。

    python3 scripts/test-tlc-trace.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-tlc.py` と同じ形。

**このテストは実環境を触らない。** 本体は一時ディレクトリを cwd にして走らせ、そこに何も書かないことも見る。
**試料の反例の JSON は、本物の TLC（TLA+ のプレリリース v1.8.0 の `tla2tools.jar`。`-h` の版 `2026.11.15.002146`）に `-dumpTrace json` を渡して
手元で取ったもの**をそのまま埋めた（CI に TLC は無い）。モデルは下の `FIXTURES` の上に書いた。**ほかの版の TLC の JSON の形は見ない**（本体の docstring の「守らない」）。
試料のうち `真偽の呼び出し`・`番号が飛ぶ`・`状態に pc が無い` の 3 つだけは、本物の試料を書き換えて作った。

**出力は本物の `scaffold.py` の `check_trace` にも当てる**（陽性対照: 段の呼び出しを `calls` に無い名前にした版が赤）。
#1015 の付録 A のモデル（守りなし）の反例からは、#1015 の A4 が Red テストで判別した `steps` と同じ順が出ることも見る。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに観測がそろったままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が期待どおりであること（下の「正しい本体」）。本体の docstring の「守る」の行数と変異の数が等しいことを、
テスト自身が数えて見る。終了コードの表と定数、指し先（spec-ir.md・Formal Checker・README）も見る。
"""
import contextlib
import copy
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPT = PLUGIN / "scripts" / "tlc-trace.py"

failures: list[str] = []

# 本体の docstring の「守る」の各行に 1 つずつ。(探す文字列, 置き換え) の組
MUTATIONS = {
    "段を行為の名前の小文字で推す": [('        steps.append([table["calls"][key]["name"], table["actions"][name]])\n',
                             '        steps.append([table["calls"][key]["name"], name.lower()])\n')],
    "呼び出しを calls で引かない": [('        steps.append([table["calls"][key]["name"], table["actions"][name]])\n',
                              '        steps.append([key, table["actions"][name]])\n')],
    "表に無い行為を黙って捨てる": [('            raise Cannot(f"{i} 番目の行為 {name} が対応表の `actions` にも `skip` にも無い")\n',
                             "            continue\n")],
    "skip を段から外さない": [("        if name in skip:\n            continue\n", "        if False:\n            continue\n")],
    "呼び出しの引数の無い行為を飛ばす": [("            raise Cannot(f\"{i} 番目の行為 {name} に呼び出しの引数 `{caller}` が無い",
                                  "            continue\n            raise Cannot(f\"{i} 番目の行為 {name} に呼び出しの引数 `{caller}` が無い")],
    "ほかの引数を見ない": [("        if others:\n", "        if False:\n")],
    "calls に無い呼び出しを飛ばす": [("        if key not in table[\"calls\"]:\n            raise Cannot(",
                                "        if key not in table[\"calls\"]:\n            continue\n            raise Cannot(")],
    "真偽を文字列にして引く": [("    if isinstance(value, bool) or not isinstance(value, (str, int)):\n",
                          "    if not isinstance(value, (str, int)):\n")],
    "繰り返しを見ない": [("        if after <= before:\n", "        if False:\n")],
    "前の状態の番号を見ない": [("        if before != expect:\n", "        if False:\n")],
    "段の数を見ない": [("MIN_STEPS = 2\n", "MIN_STEPS = 0\n")],
    "rest のほかの鍵を見ない": [("    if extra:\n", "    if False:\n")],
    "呼び出しの名前の重なりを見ない": [("    if not all(isinstance(n, str) and n for n in names):\n", "    if False:\n"),
                          ("    if len(set(names)) != len(names):\n", "    if False:\n")],
    "形の違う行為を 2 にしない": [("        if set(params) != set(context):\n", "        if False:\n")],
    "actions と skip の重なりを見ない": [("    if both:\n", "    if False:\n")],
    "ファイルに書く": [("    print(json.dumps(trace, ensure_ascii=False))\n",
                    "    print(json.dumps(trace, ensure_ascii=False))\n    open(\"trace.json\", \"w\", encoding=\"utf-8\").write(\"{}\")\n")],
}

# 本物の TLC v1.8.0 の `-dumpTrace json` の出力（手元で取った）。モデル:
#   version-write: #1015 の付録 A（VersionWrite.tla）を `CONSTANT Guard = FALSE`・`INVARIANT NoRollback` で
#   skip:          `Open == x = 0 /\ x' = 1`（引数なし）と `Take(p)`（p \in {1, 2}。整数の呼び出し）。Inv は両方が b にならない
#   two-params:    `Step(p, k)`（p \in {p1, p2} はモデルの値・k \in 1..2）。Inv は x < 3
#   inline:        `Tick`（引数なし）と、`\E p \in {"u","v"} : …` を Next の中に書いた行為（名前が Next・引数なし）
#   lasso:         `Inc(k)`・`Back` に WF をつけ、PROPERTY <>(x = 5)（活性の違反。Back で状態 2 に戻る）
#   initial:       初めの状態で Inv が破れる（行為が 0 個）
FIXTURES = {
    'version-write': '{"counterexample":{"action":[[[1,{"maxWritten":0,"result":{"old":"none","new":"none"},"seen":{"old":0,"new":0},"lock":"none","pc":{"old":"read","new":"read"},"rowVer":0}],{"name":"Read","location":{"beginLine":16,"beginColumn":12,"endLine":19,"endColumn":54,"module":"VersionWrite"},"context":{"w":"new"},"parameters":["w"]},[2,{"maxWritten":0,"result":{"old":"none","new":"none"},"seen":{"old":0,"new":0},"lock":"new","pc":{"old":"read","new":"write"},"rowVer":0}]],[[2,{"maxWritten":0,"result":{"old":"none","new":"none"},"seen":{"old":0,"new":0},"lock":"new","pc":{"old":"read","new":"write"},"rowVer":0}],{"name":"Write","location":{"beginLine":21,"beginColumn":13,"endLine":29,"endColumn":29,"module":"VersionWrite"},"context":{"w":"new"},"parameters":["w"]},[3,{"maxWritten":2,"result":{"old":"none","new":"ok"},"seen":{"old":0,"new":0},"lock":"none","pc":{"old":"read","new":"done"},"rowVer":2}]],[[3,{"maxWritten":2,"result":{"old":"none","new":"ok"},"seen":{"old":0,"new":0},"lock":"none","pc":{"old":"read","new":"done"},"rowVer":2}],{"name":"Read","location":{"beginLine":16,"beginColumn":12,"endLine":19,"endColumn":54,"module":"VersionWrite"},"context":{"w":"old"},"parameters":["w"]},[4,{"maxWritten":2,"result":{"old":"none","new":"ok"},"seen":{"old":2,"new":0},"lock":"old","pc":{"old":"write","new":"done"},"rowVer":2}]],[[4,{"maxWritten":2,"result":{"old":"none","new":"ok"},"seen":{"old":2,"new":0},"lock":"old","pc":{"old":"write","new":"done"},"rowVer":2}],{"name":"Write","location":{"beginLine":21,"beginColumn":13,"endLine":29,"endColumn":29,"module":"VersionWrite"},"context":{"w":"old"},"parameters":["w"]},[5,{"maxWritten":2,"result":{"old":"ok","new":"ok"},"seen":{"old":2,"new":0},"lock":"none","pc":{"old":"done","new":"done"},"rowVer":1}]]],"state":[[1,{"maxWritten":0,"result":{"old":"none","new":"none"},"seen":{"old":0,"new":0},"lock":"none","pc":{"old":"read","new":"read"},"rowVer":0}],[2,{"maxWritten":0,"result":{"old":"none","new":"none"},"seen":{"old":0,"new":0},"lock":"new","pc":{"old":"read","new":"write"},"rowVer":0}],[3,{"maxWritten":2,"result":{"old":"none","new":"ok"},"seen":{"old":0,"new":0},"lock":"none","pc":{"old":"read","new":"done"},"rowVer":2}],[4,{"maxWritten":2,"result":{"old":"none","new":"ok"},"seen":{"old":2,"new":0},"lock":"old","pc":{"old":"write","new":"done"},"rowVer":2}],[5,{"maxWritten":2,"result":{"old":"ok","new":"ok"},"seen":{"old":2,"new":0},"lock":"none","pc":{"old":"done","new":"done"},"rowVer":1}]]},"vars":["rowVer","maxWritten","lock","pc","seen","result"]}',
    'skip': '{"counterexample":{"action":[[[1,{"x":0,"pc":["a","a"]}],{"name":"Open","location":{"beginLine":5,"beginColumn":9,"endLine":5,"endColumn":39,"module":"Skip"}},[2,{"x":1,"pc":["a","a"]}]],[[2,{"x":1,"pc":["a","a"]}],{"name":"Take","location":{"beginLine":6,"beginColumn":12,"endLine":6,"endColumn":78,"module":"Skip"},"context":{"p":1},"parameters":["p"]},[3,{"x":1,"pc":["b","a"]}]],[[3,{"x":1,"pc":["b","a"]}],{"name":"Take","location":{"beginLine":6,"beginColumn":12,"endLine":6,"endColumn":78,"module":"Skip"},"context":{"p":2},"parameters":["p"]},[4,{"x":1,"pc":["b","b"]}]]],"state":[[1,{"x":0,"pc":["a","a"]}],[2,{"x":1,"pc":["a","a"]}],[3,{"x":1,"pc":["b","a"]}],[4,{"x":1,"pc":["b","b"]}]]},"vars":["x","pc"]}',
    'two-params': '{"counterexample":{"action":[[[1,{"x":0,"pc":{"p1":"a","p2":"a"}}],{"name":"Step","location":{"beginLine":6,"beginColumn":15,"endLine":6,"endColumn":85,"module":"E"},"context":{"p":"p1","k":1},"parameters":["p","k"]},[2,{"x":1,"pc":{"p1":"b","p2":"a"}}]],[[2,{"x":1,"pc":{"p1":"b","p2":"a"}}],{"name":"Step","location":{"beginLine":6,"beginColumn":15,"endLine":6,"endColumn":85,"module":"E"},"context":{"p":"p2","k":2},"parameters":["p","k"]},[3,{"x":3,"pc":{"p1":"b","p2":"b"}}]]],"state":[[1,{"x":0,"pc":{"p1":"a","p2":"a"}}],[2,{"x":1,"pc":{"p1":"b","p2":"a"}}],[3,{"x":3,"pc":{"p1":"b","p2":"b"}}]]},"vars":["x","pc"]}',
    'inline': '{"counterexample":{"action":[[[1,{"x":0,"pc":{"v":"a","u":"a"}}],{"name":"Tick","location":{"beginLine":5,"beginColumn":9,"endLine":5,"endColumn":39,"module":"F"}},[2,{"x":1,"pc":{"v":"a","u":"a"}}]],[[2,{"x":1,"pc":{"v":"a","u":"a"}}],{"name":"Next","location":{"beginLine":6,"beginColumn":39,"endLine":6,"endColumn":105,"module":"F"}},[3,{"x":1,"pc":{"v":"b","u":"a"}}]],[[3,{"x":1,"pc":{"v":"b","u":"a"}}],{"name":"Next","location":{"beginLine":6,"beginColumn":39,"endLine":6,"endColumn":105,"module":"F"}},[4,{"x":1,"pc":{"v":"b","u":"b"}}]]],"state":[[1,{"x":0,"pc":{"v":"a","u":"a"}}],[2,{"x":1,"pc":{"v":"a","u":"a"}}],[3,{"x":1,"pc":{"v":"b","u":"a"}}],[4,{"x":1,"pc":{"v":"b","u":"b"}}]]},"vars":["x","pc"]}',
    'lasso': '{"counterexample":{"action":[[[1,{"x":0}],{"name":"Inc","location":{"beginLine":5,"beginColumn":11,"endLine":5,"endColumn":38,"module":"L"},"context":{"k":1},"parameters":["k"]},[2,{"x":1}]],[[2,{"x":1}],{"name":"Inc","location":{"beginLine":5,"beginColumn":11,"endLine":5,"endColumn":38,"module":"L"},"context":{"k":1},"parameters":["k"]},[3,{"x":2}]],[[3,{"x":2}],{"name":"Back","location":{"beginLine":6,"beginColumn":9,"endLine":6,"endColumn":23,"module":"L"}},[2,{"x":1}]]],"state":[[1,{"x":0}],[2,{"x":1}],[3,{"x":2}]]},"vars":["x"]}',
    'initial': '{"counterexample":{"action":[],"state":[[1,{"x":0}]]},"vars":["x"]}',
}

OPS = {
    "write_row": {"id": "write_row", "input": {"key": {"type": "string"}, "ver": {"type": "integer"}},
                  "output": {"ok": {"type": "boolean"}}, "errors": ["STALE_VERSION"]},
    "set_row": {"id": "set_row", "input": {"key": {"type": "string"}, "ver": {"type": "integer"}},
                "output": {"ver": {"type": "integer"}}, "errors": []},
    "get_row": {"id": "get_row", "input": {"key": {"type": "string"}},
                "output": {"ver": {"type": "integer"}}, "errors": []},
}

VW_TABLE = {
    "formal": "version-write", "caller": "w",
    "calls": {"old": {"name": "old_writer", "operation": "write_row", "input": {"key": "k", "ver": 1}},
              "new": {"name": "new_writer", "operation": "write_row", "input": {"key": "k", "ver": 2}}},
    "actions": {"Read": "read", "Write": "write"}, "skip": ["Done"],
    "rest": {"setup": [{"operation": "set_row", "input": {"key": "k", "ver": 0}, "expected": {"ver": 0}}],
             "outcomes": [{"ok": True}, {"error": "STALE_VERSION"}],
             "after": [{"operation": "get_row", "input": {"key": "k"}, "expected": {"ver": 2}}]},
}
# #1015 の A4 が Red テストで判別した順（守りなしを赤・守りありを緑に分けた）
VW_STEPS = [["new_writer", "read"], ["new_writer", "write"], ["old_writer", "read"], ["old_writer", "write"]]

SKIP_TABLE = {
    "formal": "take", "caller": "p",
    "calls": {"1": {"name": "first", "operation": "write_row", "input": {"key": "k", "ver": 1}},
              "2": {"name": "second", "operation": "write_row", "input": {"key": "k", "ver": 2}}},
    "actions": {"Take": "take"}, "skip": ["Open"], "rest": {"outcomes": [{"ok": True}, {"ok": True}]},
}


def check(name: str, ok: bool) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    if not ok:
        failures.append(name)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def table_with(**changes) -> dict:
    t = copy.deepcopy(VW_TABLE)
    t.update(changes)
    return t


def dump(name: str) -> dict:
    return json.loads(FIXTURES[name])


def with_action(d: dict, index: int, **changes) -> dict:
    """本物の試料の index 番目の行為の鍵を書き換えた写し（値が None なら鍵を消す）。"""
    d = copy.deepcopy(d)
    action = d["counterexample"]["action"][index][1]
    for key, value in changes.items():
        if value is None:
            action.pop(key, None)
        else:
            action[key] = value
    return d


def samples() -> dict:
    """ラベル → (反例の JSON（オブジェクトか、そのまま書く文字列）, 対応表)。"""
    vw = dump("version-write")
    renamed = table_with(actions={"Read": "load", "Write": "store"})
    boolean = dump("skip")
    for entry in boolean["counterexample"]["action"]:
        if "context" in entry[1]:
            entry[1]["context"]["p"] = entry[1]["context"]["p"] == 1
    gap = copy.deepcopy(vw)
    del gap["counterexample"]["action"][1]
    no_pc = copy.deepcopy(vw)
    for entry in no_pc["counterexample"]["action"]:
        for state in (entry[0][1], entry[2][1]):
            state.pop("pc")
    two = {"formal": "two", "caller": "p",
           "calls": {"p1": {"name": "a", "operation": "write_row", "input": {"key": "k", "ver": 1}},
                     "p2": {"name": "b", "operation": "write_row", "input": {"key": "k", "ver": 2}}},
           "actions": {"Step": "step"}}
    inline = {"formal": "inline", "caller": "p",
              "calls": {"u": {"name": "u", "operation": "write_row", "input": {"key": "k", "ver": 1}},
                        "v": {"name": "v", "operation": "write_row", "input": {"key": "k", "ver": 2}}},
              "actions": {"Next": "next"}, "skip": ["Tick"]}
    lasso = {"formal": "lasso", "caller": "k",
             "calls": {"1": {"name": "inc", "operation": "write_row", "input": {"key": "k", "ver": 1}}},
             "actions": {"Inc": "inc", "Back": "back"}}
    return {
        "version-write": (vw, VW_TABLE),
        "段の名前を表で引く": (vw, renamed),
        "状態に pc が無い": (no_pc, VW_TABLE),
        "skip と整数の呼び出し": (dump("skip"), SKIP_TABLE),
        "skip を外す": (dump("skip"), {**SKIP_TABLE, "skip": []}),
        "引数の無い行為を actions に": (dump("skip"), {**SKIP_TABLE, "skip": [], "actions": {"Take": "take", "Open": "open"}}),
        "Next の中の存在量化": (dump("inline"), inline),
        "引数が 2 つ": (dump("two-params"), two),
        "calls に無い呼び出し": (vw, table_with(calls={"old": VW_TABLE["calls"]["old"]})),
        "真偽の呼び出し": (boolean, {**SKIP_TABLE, "calls": {"True": SKIP_TABLE["calls"]["1"], "False": SKIP_TABLE["calls"]["2"]}}),
        "繰り返し": (dump("lasso"), lasso),
        "番号が飛ぶ": (gap, VW_TABLE),
        "初めの状態で違反": (dump("initial"), table_with()),
        "rest に steps": (vw, table_with(rest={"steps": [["old_writer", "read"]]})),
        "呼び出しの名前が重なる": (vw, table_with(calls={"old": VW_TABLE["calls"]["old"], "new": VW_TABLE["calls"]["old"]})),
        "actions と skip が重なる": (vw, table_with(skip=["Read"])),
        "名前が真偽と数": (vw, table_with(calls={"old": {**VW_TABLE["calls"]["old"], "name": True},
                                                 "new": {**VW_TABLE["calls"]["new"], "name": 1}})),
        "行為の name が配列": (with_action(vw, 0, name=["Read"]), VW_TABLE),
        "行為に name が無い": (with_action(vw, 0, name=None), VW_TABLE),
        "parameters にだけ呼び出しの引数": (with_action(vw, 0, context={}), VW_TABLE),
        "context にだけほかの鍵": (with_action(vw, 0, context={"w": "new", "v": 2}), VW_TABLE),
        "calls に名前だけ": (vw, table_with(calls={k: {"name": c["name"]} for k, c in VW_TABLE["calls"].items()})),
        "入れ子が深すぎる JSON": ("[" * 100000 + "]" * 100000, VW_TABLE),
        "JSON でない": ("{not json", VW_TABLE),
        "counterexample が無い": ({"vars": []}, VW_TABLE),
    }


def run(mod, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = mod.main(argv)
        except Exception as exc:  # 変異が例外で落ちる形も観測として残す
            return f"例外 {type(exc).__name__}", None
    text = out.getvalue().strip()
    return rc, (json.loads(text) if rc == 0 and text else text + err.getvalue())


def scenario(mod, base: Path, label: str) -> dict:
    work = base / label
    work.mkdir()
    inputs = work.parent / f"{label}-inputs"
    inputs.mkdir()
    cwd = os.getcwd()
    os.chdir(work)
    o = {}
    try:
        for i, (name, (d, t)) in enumerate(samples().items()):
            dpath, tpath = inputs / f"{i}-dump.json", inputs / f"{i}-table.json"
            dpath.write_text(d if isinstance(d, str) else json.dumps(d), encoding="utf-8")
            tpath.write_text(json.dumps(t), encoding="utf-8")
            rc, text = run(mod, [str(dpath), str(tpath)])
            # 入力のパスは試料ごとの置き場所で変わるので伏せる——伏せないと、何もしない変異も「殺せた」になる（#1020 の 1 パス目）
            o[name] = (rc, text.replace(str(inputs), "<in>") if isinstance(text, str) else text)
        o["引数なし"] = run(mod, [])[0]
        o["読めないファイル"] = run(mod, [str(inputs / "無い.json"), str(inputs / "0-table.json")])[0]
        o["cwd に書いたもの"] = sorted(p.name for p in work.iterdir())
    finally:
        os.chdir(cwd)
    return o


def main() -> int:
    if not FIXTURES:
        print("試料が無い")
        return 1
    tmp = Path(tempfile.mkdtemp(prefix="test-tlc-trace-")).resolve()
    try:
        mod = load_module(SCRIPT, "tlctrace")
        print("正しい本体")
        o = scenario(mod, tmp, "correct")
        rc, vw = o["version-write"]
        check("#1015 のモデルの反例: 0 で、A4 と同じ steps", rc == 0 and vw["steps"] == VW_STEPS)
        check("calls は対応表の全部を name → operation・input で出す",
              rc == 0 and vw["calls"] == {"old_writer": {"operation": "write_row", "input": {"key": "k", "ver": 1}},
                                          "new_writer": {"operation": "write_row", "input": {"key": "k", "ver": 2}}})
        check("formal と rest をそのまま写す", rc == 0 and vw["formal"] == "version-write"
              and all(vw[k] == VW_TABLE["rest"][k] for k in ("setup", "outcomes", "after")))
        rc, renamed = o["段の名前を表で引く"]
        check("段の名前は actions で引く（小文字で推さない）",
              rc == 0 and renamed["steps"] == [["new_writer", "load"], ["new_writer", "store"], ["old_writer", "load"], ["old_writer", "store"]])
        check("状態（pc）を消しても同じ steps（状態は読まない）", o["状態に pc が無い"] == o["version-write"])
        rc, skipped = o["skip と整数の呼び出し"]
        check("skip の行為は段にせず、整数の呼び出しは文字列の鍵で引く", rc == 0 and skipped["steps"] == [["first", "take"], ["second", "take"]])
        for name in ("skip を外す", "引数の無い行為を actions に", "Next の中の存在量化", "引数が 2 つ", "calls に無い呼び出し",
                     "真偽の呼び出し", "繰り返し", "初めの状態で違反"):
            check(f"{name}: 1", o[name][0] == 1)
        for name in ("番号が飛ぶ", "rest に steps", "呼び出しの名前が重なる", "名前が真偽と数", "行為の name が配列", "行為に name が無い",
                     "parameters にだけ呼び出しの引数", "context にだけほかの鍵", "入れ子が深すぎる JSON", "JSON でない",
                     "counterexample が無い", "引数なし", "読めないファイル"):
            got = o[name][0] if isinstance(o[name], tuple) else o[name]
            check(f"{name}: 2", got == 2)
        check("Next の中の存在量化: 呼び出しの引数が無いと名指しする", "呼び出しの引数 `p` が無い" in o["Next の中の存在量化"][1])
        check("繰り返し: 活性の違反と名指しする", "繰り返しのある反例" in o["繰り返し"][1])
        check("cwd に何も書かない", o["cwd に書いたもの"] == [])

        rc, names_only = o["calls に名前だけ"]
        check("calls に名前だけの表: 0 で、同じ steps と、入口・入力の無い calls",
              rc == 0 and names_only["steps"] == VW_STEPS and names_only["calls"] == {"old_writer": {}, "new_writer": {}})

        print("\n本物の scaffold.py の check_trace に当てる")
        sys.path.insert(0, str(PLUGIN / "scripts"))
        scaffold = load_module(PLUGIN / "scripts" / "scaffold.py", "scaffold_for_tlc_trace")
        whole = tmp / "whole"
        record = whole / "spec" / "formal" / "version-write" / "README.md"
        record.parent.mkdir(parents=True)
        record.write_text("# version-write\n", encoding="utf-8")
        problems = scaffold.check_trace("trace", vw, OPS, whole)
        check(f"変換の出力が check_trace を通る（{problems}）", problems == [])
        broken = copy.deepcopy(vw)
        broken["steps"][0][0] = "nobody"
        check("陽性対照: 段の呼び出しを calls に無い名前にした版は check_trace が赤", scaffold.check_trace("trace", broken, OPS, whole) != [])

        print("\n終了コードの表・指し先")
        source = SCRIPT.read_text(encoding="utf-8")
        exits = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", exits, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_CANNOT, mod.EXIT_USAGE}
        check(f"終了コードの表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)
        keys = source.split("## 対応表")[1].split("## ")[0]
        documented_keys = set(re.findall(r"^\| `([a-z]+)` \|", keys, re.M))
        check(f"対応表の鍵の表 {sorted(documented_keys)} が本体の受ける鍵と同じ",
              documented_keys == {"formal", "caller", "calls", "actions", "skip", "rest"})
        spec_ir = (PLUGIN / "references" / "spec-ir.md").read_text(encoding="utf-8")
        section = spec_ir.split("## トレースのケース")[1].split("\n## ")[0]
        check("spec-ir.md の「トレースのケース」が scripts/tlc-trace.py を指す", "scripts/tlc-trace.py" in section)
        formal = (PLUGIN / "agents" / "formal-checker.md").read_text(encoding="utf-8")
        check("Formal Checker が scripts/tlc-trace.py と -dumpTrace json を名指しする",
              "scripts/tlc-trace.py" in formal and "-dumpTrace json" in formal)
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        check("README の中身の表と「TLC の用意」が tlc-trace.py を挙げる",
              "| `scripts/tlc-trace.py` |" in readme and "tlc-trace.py" in readme.split("### TLC の用意")[1].split("\n### ")[0])

        print("\n陽性対照: 何もしない変異は殺せない（観測が置き場所で変わらない）")
        d = tmp / "noop"
        d.mkdir()
        (d / "tlc-trace.py").write_text(source, encoding="utf-8")
        check("壊さない写しを別の場所で走らせた観測が、正しい本体と同じ", scenario(load_module(d / "tlc-trace.py", "noop"), d, "s") == o)

        print("\n変異テスト（壊したのに観測がそろったままなら失格）")
        for i, (name, pairs) in enumerate(MUTATIONS.items()):
            mutated = source
            absent = [n for n, _ in pairs if n not in mutated]
            if absent:
                check(f"変異を当てる先がある: {name}: {absent}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d = tmp / f"mut-{i}"
            d.mkdir()
            path = d / "tlc-trace.py"
            path.write_text(mutated, encoding="utf-8")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**
            try:
                mutant = load_module(path, f"mut{i}")
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            got = scenario(mutant, d, "s")
            check(f"変異を殺せる: {name}", got != o)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("TLC の反例の JSON から trace ケースを作る変換のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
