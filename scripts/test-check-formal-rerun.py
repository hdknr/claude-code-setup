#!/usr/bin/env python3
"""`check-formal-rerun.py`（保存した TLC のモデルの本体と陽性対照を走らせ直す。#1044）の回帰テスト。

    python3 scripts/test-check-formal-rerun.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-tlc.py` と同じく、**本物の TLC は走らせない**——
**偽の TLC**（モデルのファイルの中の印 `FAKE:<形>` を読んで、TLC 2.19 の出力の行の形を出すスクリプト）を絶対パスで呼び方の行に書き、
**`PATH` には `command -v` で見つかる偽の `tlc`（呼ばれたら通す）を置く**——呼び方の行が無いときに `PATH` で探さないことを見るため。
偽の TLC は走った場所に `states/` を作る——正本に残さないこと（一時ディレクトリで走らせること）を見るため。

見るもの:

1. **陽性対照で反例が出ないモデルを「判定できなかった」として 4**（Issue の受入基準 2）。陽性対照のファイルが無い・TLC のモデルが一覧に無い・
   本体が通らず違反も出さない（構文の誤り・`No error has been found` が無い・時間切れ）・一覧のファイルが無い・呼び方の行が無いも 4。
2. **本体で反例が出たら 1**、**本体が通り陽性対照が反例を出せば 0**（違反の印は `is violated`・`were violated`・`Deadlock reached` のどれでも）。
   反例ありの対象と判定できなかった対象が並べば 1。
3. **正本に `states/` を残さない**。
4. **引数の誤りは 2**。
5. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料の終了コードか、正本に残したファイルが期待と変わること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "check-formal-rerun.py"

FAKE_TLC = f"""#!{sys.executable}
import os, sys, time
name = sys.argv[-1]
os.makedirs("states", exist_ok=True)
text = open(name, encoding="utf-8").read()
print("TLC2 Version 2.19 of 08 August 2024 (偽物)")
if "FAKE:PASS" in text:
    print("Model checking completed. No error has been found."); sys.exit(0)
if "FAKE:VIOLATE" in text:
    print("Error: Invariant Inv is violated."); sys.exit(12)
if "FAKE:TEMPORAL" in text:
    print("Error: Temporal properties were violated."); sys.exit(13)
if "FAKE:DEADLOCK" in text:
    print("Error: Deadlock reached."); sys.exit(11)
if "FAKE:SILENT" in text:
    sys.exit(0)
if "FAKE:SLEEP" in text:
    time.sleep(3)
    print("Model checking completed. No error has been found."); sys.exit(0)
print("Error: Parsing or semantic analysis failed."); sys.exit(150)
"""
# PATH に置く偽の `tlc`——呼ばれたら何でも通す（呼び方の行が無いのに PATH で探したら 0 になる）
PATH_TLC = "#!/bin/sh\necho 'Error: Invariant Inv is violated.'\necho 'No error has been found'\nexit 0\n"
CFG = "INIT Init\nNEXT Next\nINVARIANT Inv\n"
ITEMS = ("| 対象 | x |", "| 検査器 | TLC 2.19 |", "| 構成の大きさ | 1 |", "| 結果 | 反例なし |", "| 陽性対照 | Inv を壊した |",
         "| 置いた前提 | なし |", "| 前回のモデル | 無かった |")


def target(body: str = "PASS", controls: tuple[str, ...] = ("VIOLATE",), model_list: str | None = None,
           control_list: str | None = None, drop: tuple[str, ...] = ()) -> dict[str, str]:
    """対象のディレクトリの中身（{名前: 中身}）。本体は Order、陽性対照は Broken<i>。"""
    files = {"Order.tla": f"---- MODULE Order ----\n\\* FAKE:{body}\n====\n", "Order.cfg": CFG}
    names = []
    for i, form in enumerate(controls):
        files[f"Broken{i}.tla"] = f"---- MODULE Broken{i} ----\n\\* FAKE:{form}\n====\n"
        files[f"Broken{i}.cfg"] = CFG
        names += [f"`Broken{i}.tla`", f"`Broken{i}.cfg`"]
    rows = ["| 項目 | 記録 |", "| --- | --- |", *ITEMS,
            f"| モデルのファイル | {model_list if model_list is not None else '`Order.tla`・`Order.cfg`'} |"]
    if control_list is not None or names:
        rows.append(f"| 陽性対照のファイル | {control_list if control_list is not None else '・'.join(names)} |")
    rows.append("| 残した回 | v1・2026-11-16・1 回目 |")
    files["README.md"] = "\n".join(rows) + "\n"
    for name in drop:
        files.pop(name, None)
    return files


T1 = "docs/v1/spec/formal/order-cancel"
T2 = "docs/v1/spec/formal/stock"
CALL = "@FAKE@"  # 試料を組むときに偽の TLC の絶対パスに置き換える


def no_states(repo: Path) -> bool:
    return not any(p.name == "states" for p in (repo / "docs").rglob("*"))


# 名前 → (CLAUDE.md の中身（None なら置かない）, {対象のパス: 中身}, 足す引数, 期待の終了コード, 出力に含む語)
CASES: dict[str, tuple] = {
    "満たす": (f"TLC の呼び方: {CALL}\n", {T1: target()}, [], 0, "渡した 1 件とも満たす"),
    "陽性対照で反例が出ない（受入基準 2）": (f"TLC の呼び方: {CALL}\n", {T1: target(controls=("PASS",))}, [], 4, "空振りの疑い"),
    "本体で反例": (f"TLC の呼び方: {CALL}\n", {T1: target(body="VIOLATE")}, [], 1, "本体 Order.tla で反例が出た"),
    "本体が構文の誤り": (f"TLC の呼び方: {CALL}\n", {T1: target(body="PARSE")}, [], 4, "通らず、反例も出さなかった"),
    "本体が通ったと言わない": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SILENT")}, [], 4, "通らず、反例も出さなかった"),
    "時相の性質と行き止まりの印を読む": (f"TLC の呼び方: {CALL}\n", {T1: target(controls=("TEMPORAL", "DEADLOCK"))}, [], 0, "満たす"),
    # 陽性対照を両方の一覧に書いた記録（1 パス目の CR1）——陽性対照を本体の反例と読まない
    "両方の一覧に書いた陽性対照は本体に数えない": (f"TLC の呼び方: {CALL}\n", {T1: target(model_list="`Order.tla`・`Order.cfg`・`Broken0.tla`・`Broken0.cfg`")},
                                    [], 0, "満たす"),
    "陽性対照のファイルが無い": (f"TLC の呼び方: {CALL}\n", {T1: target(controls=())}, [], 4, "陽性対照のファイルに TLC のモデル"),
    "TLC でない対象": (f"TLC の呼び方: {CALL}\n", {T1: {**target(model_list="`perm.als`"), "perm.als": "sig A {}\n"}}, [], 4, "TLC でない対象は走らせ直さない"),
    "呼び方の行が無い": (None, {T1: target()}, [], 4, "TLC の呼び方が無い"),
    "一覧のファイルが無い": (f"TLC の呼び方: {CALL}\n", {T1: target(drop=("Broken0.cfg",))}, [], 4, "「Broken0.cfg」がこのディレクトリの通常のファイルとして無い"),
    "反例ありが判定できなかったより先": (f"TLC の呼び方: {CALL}\n", {T1: target(body="VIOLATE"), T2: target(controls=("PASS",))}, [], 1, "反例あり 1 件"),
    "時間切れ": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEP")}, ["--timeout", "1"], 4, "時間切れ"),
    "判定しない: --timeout が 0": (f"TLC の呼び方: {CALL}\n", {T1: target()}, ["--timeout", "0"], 2, "--timeout は 1 以上"),
    "判定しない: 対象が無い": (f"TLC の呼び方: {CALL}\n", {}, [], 2, "usage"),
}
# 正本に states/ を残さない（終了コードに加えて見る試料）
POST = {"満たす": no_states}

# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("違反の印を不変条件だけにする", 'VIOLATED = (tlc.BROKEN_MARK, "were violated", "Deadlock reached")', "VIOLATED = (tlc.BROKEN_MARK,)",
     "時相の性質と行き止まりの印を読む"),
    ("陽性対照の空振りを通す", '空振りの疑い）: {tlc.tail(out)}")\n                if verdict == PASS:\n',
     '空振りの疑い）: {tlc.tail(out)}")\n                if False:\n', "陽性対照で反例が出ない（受入基準 2）"),
    ("通った印を見ない", "            elif rc != 0 or tlc.GOOD_MARK not in out:\n", "            elif rc != 0:\n", "本体が通ったと言わない"),
    ("本体の反例を反例ありにしない", "                verdict = COUNTEREXAMPLE\n", "                verdict = verdict\n", "本体で反例"),
    ("陽性対照のファイルが無くても通す", "    if not broken:\n        return UNKNOWN", "    if False:\n        return UNKNOWN", "陽性対照のファイルが無い"),
    ("TLC のモデルが無くても通す", "    if not bodies:\n        return UNKNOWN", "    if False:\n        return UNKNOWN", "TLC でない対象"),
    ("呼び方が無ければ PATH の tlc を使う", "    if call is None:\n        print(f\"注記: {note}\")\n",
     "    if call is None:\n        call = \"tlc\"\n        print(f\"注記: {note}\")\n", "呼び方の行が無い"),
    ("陽性対照を本体からも外さない", "    bodies = [n for n in entries(models) if n not in broken]\n", "    bodies = entries(models)\n",
     "両方の一覧に書いた陽性対照は本体に数えない"),
    ("正本で走らせる", "        where = tmp ", "        where = str(directory) ", "満たす"),
    ("判定できなかったを反例ありより先に読む", "    if COUNTEREXAMPLE in verdicts:\n", "    if COUNTEREXAMPLE in verdicts and UNKNOWN not in verdicts:\n",
     "反例ありが判定できなかったより先"),
    ("--timeout を使わない", "        verdict, lines = rerun(call, directory, int(args.timeout))\n", "        verdict, lines = rerun(call, directory, TIMEOUT)\n", "時間切れ"),
]


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name}{(': ' + detail) if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    tmp = Path(tempfile.gettempdir()).resolve()
    check(f"試料が一時ディレクトリの中: {path}", tmp in path.resolve().parents)


def run_one(script: Path, work: Path, fake: Path, fakebin: Path, case: tuple) -> tuple[int, str, Path]:
    claude, targets, extra, _, _ = case
    if work.exists():
        shutil.rmtree(work)
    repo = work / "repo"
    repo.mkdir(parents=True)
    assert_in_tmp(repo)
    if claude is not None:
        (repo / "CLAUDE.md").write_text(claude.replace(CALL, str(fake)), encoding="utf-8")
    for rel, files in targets.items():
        (repo / rel).mkdir(parents=True)
        for name, body in files.items():
            (repo / rel / name).write_text(body, encoding="utf-8")
    env = {**os.environ, "PATH": f"{fakebin}{os.pathsep}/usr/bin{os.pathsep}/bin"}
    proc = subprocess.run([sys.executable, "-I", str(script), str(repo), *[str(repo / rel) for rel in targets], *extra],
                          capture_output=True, text=True, cwd=work, env=env, timeout=120)
    return proc.returncode, proc.stdout + proc.stderr, repo


def as_expected(name: str, case: tuple, result: tuple[int, str, Path]) -> bool:
    code, out, repo = result
    return code == case[3] and case[4] in out and (name not in POST or POST[name](repo))


def main() -> int:
    source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="check-formal-rerun-test-") as tmp:
        root = Path(tmp)
        scripts = root / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        fake = root / "fake-tlc"
        fake.write_text(FAKE_TLC, encoding="utf-8")
        fake.chmod(0o755)
        fakebin = root / "bin"
        fakebin.mkdir()
        (fakebin / "tlc").write_text(PATH_TLC, encoding="utf-8")
        (fakebin / "tlc").chmod(0o755)
        check("偽の tlc が PATH で見つかる（呼び方の行が無いのに探したら 0 になる形）",
              shutil.which("tlc", path=f"{fakebin}{os.pathsep}/usr/bin{os.pathsep}/bin") == str(fakebin / "tlc"))
        print("試料")
        for i, (name, case) in enumerate(CASES.items()):
            result = run_one(scripts / TARGET, root / f"c{i}", fake, fakebin, case)
            check(f"試料: {name}", as_expected(name, case, result), f"期待 {case[3]}・{case[4]!r} / 実際 {result[0]}・{result[1][-400:]!r}")
        print(f"  {len(CASES)} 件 OK")

        print("変異テスト")
        for name, before, after, killer in MUTATIONS:
            check(f"壊す箇所がちょうど 1 回: {name}", source.count(before) == 1, f"{source.count(before)} 回: {before!r}")
            mutated = root / "mutated"
            if mutated.exists():
                shutil.rmtree(mutated)
            shutil.copytree(scripts, mutated)
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            case = CASES[killer]
            original = run_one(scripts / TARGET, root / "orig", fake, fakebin, case)
            result = run_one(mutated / TARGET, root / "mut", fake, fakebin, case)
            check(f"変異の前は期待どおり: {name}", as_expected(killer, case, original))
            check(f"変異を殺す: {name} ← {killer}", not as_expected(killer, case, result) and result[0] != 2,
                  f"{result[0]} {result[1][-300:]!r}")
        print(f"  変異 {len(MUTATIONS)} 件 OK")
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
