#!/usr/bin/env python3
"""`check-formal-rerun.py`（保存した TLC のモデルの本体と陽性対照を走らせ直す。#1044）の回帰テスト。

    python3 scripts/test-check-formal-rerun.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-tlc.py` と同じく、**本物の TLC は走らせない**——
**偽の TLC**（モデルのファイルの中の印 `FAKE:<形>` を読んで、TLC 2.19 の出力の行の形を出すスクリプト）を絶対パスで呼び方の行に書き、
**`PATH` には `command -v` で見つかる偽の `tlc`（呼ばれたら通す）を置く**——呼び方の行が無いときに `PATH` で探さないことを見るため。
偽の TLC は走った場所に `states/` を作る——正本に残さないこと（一時ディレクトリで走らせること）を見るため。
さらに本物の TLC 2.19 と同じく `states/` の下に時刻の名前のディレクトリ（偽物では固定の名前）を作り、時相の性質の違反・構文の誤りで終わった回はそれを残し、
**既にあれば `util.FileUtil.makeMetaDir` の例外の行を出して検査の前に落ちる**（#1346。本物の TLC で同じ秒に起動した回が落ちた形を、秒に依らず再現する）。

見るもの:

1. **陽性対照で反例が出ないモデルを「判定できなかった」として 4**（Issue の受入基準 2）。陽性対照のファイルが無い・TLC のモデルが一覧に無い・
   本体が通らず違反も出さない（構文の誤り・`No error has been found` が無い・時間切れ）・一覧のファイルが無い・呼び方の行が無いも 4。
2. **本体で反例が出たら 1**、**本体が通り陽性対照が反例を出せば 0**（違反の印は `is violated`・`were violated`・`Deadlock reached` のどれでも）。
   反例ありの対象と判定できなかった対象が並べば 1。
3. **正本に `states/` を残さない**。**走らせる 1 回ごとに別のディレクトリで走らせ、前の回が残した `states/` に次の回がぶつからない**（#1346）。
4. **引数の誤りは 2**。
5. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。
6. **CI の雛形（`references/tree.md` の「保存したモデルを CI で走らせ続ける」。#1178）の走らせるステップが、空振りのモデルで落ちる**——
   雛形の最後のステップの `run:` の中身を毎回抜き出し（写しを作らない）、写した正本（`.spec-loop/plugins/spec-loop/scripts/` にプラグインの写し）で `bash -eo pipefail` に渡す
   （GitHub Actions の `run:` の既定のシェル）。空振り・本体の反例で非 0、通るモデル・TLC でない対象だけで 0。雛形を崩す変異（最後のコマンドの結果を捨てる・
   TLC でない対象も渡す）で期待が変わることも見る。**YAML そのもの（`actions/*`・jar の取得）は走らせない。**

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料の終了コードか、正本に残したファイルが期待と変わること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import os
import re
import textwrap
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "check-formal-rerun.py"
PREFIX = "spec-loop-formal-rerun-"

FAKE_TLC = f"""#!{sys.executable}
import os, sys, time
name = sys.argv[-1]
os.makedirs("states", exist_ok=True)
# 本物の TLC は states/<yy-MM-dd-HH-mm-ss> を作る——同じ秒に起動した回を、秒に依らず固定の名前で再現する（#1346）
meta = os.path.join("states", "26-11-21-00-38-41")
if os.path.exists(meta):  # 本物の TLC 2.19 の出力（#1346 で手元で取った）
    print('Exception in thread "main" util.Assert$TLCRuntimeException: TLC writes its files to a directory whose name is generated from the current time.')
    print(f"This directory should be {{os.path.abspath(meta)}}, but that directory already exists.")
    print("Trying to run TLC again will probably fix this problem.")
    print("\tat util.Assert.check(Assert.java:91)")
    print("\tat util.FileUtil.makeMetaDir(FileUtil.java:252)"); sys.exit(1)
os.makedirs(meta)
def clean():  # 本物の TLC 2.19 は通った回・不変条件の違反・行き止まりで消し、時相の性質の違反・構文の誤りでは残す（#1346 で確かめた）
    os.rmdir(meta)
text = open(name, encoding="utf-8").read()
print("TLC2 Version 2.19 of 08 August 2024 (偽物)")
if "FAKE:PASS" in text:
    clean()
    print("Model checking completed. No error has been found.")
    # 最後の行は区切らない（TLC 2.19 はロケールに依らずこの形。#1339 で ドイツ語のロケールでも確かめた）
    print("1234567 states generated, 456789 distinct states found, 0 states left on queue."); sys.exit(0)
if "FAKE:PRUNED" in text:  # CONSTRAINT と PROPERTY を一緒に検査した（TLC 2.19 の警告の行。#1339 で本物の TLC から取った）
    clean()
    print("Warning: Declaring state or action constraints during liveness checking is dangerous: Please read section 14.3.5 on page 247 of Specifying Systems.")
    print("Model checking completed. No error has been found.")
    print("5 states generated, 4 distinct states found, 0 states left on queue."); sys.exit(0)
if "FAKE:QUIETPASS" in text:  # 状態数の行を出さずに通る（ほかの版で形が違うとき）
    clean()
    print("Model checking completed. No error has been found."); sys.exit(0)
if "FAKE:VIOLATE" in text:
    clean()
    print("Error: Invariant Inv is violated.")
    print("12 states generated, 9 distinct states found, 3 states left on queue."); sys.exit(12)
if "FAKE:TEMPORAL" in text:
    print("Error: Temporal properties were violated."); sys.exit(13)
if "FAKE:DEADLOCK" in text:
    clean()
    print("Error: Deadlock reached."); sys.exit(11)
if "FAKE:SILENT" in text:
    sys.exit(0)
if "FAKE:SLEEPY" in text:  # 自分の pid と、待たされている信号を書いてから眠り、通る（信号で止める試料。#1600）
    import signal
    open(os.environ["FAKE_TLC_MASK"], "w").write(str(sorted(int(s) for s in signal.pthread_sigmask(signal.SIG_BLOCK, []))))
    open(os.environ["FAKE_TLC_PID"], "w").write(str(os.getpid()))
    time.sleep(float(os.environ.get("FAKE_TLC_SLEEP", "60")))
    clean()
    print("Model checking completed. No error has been found.")
    print("5 states generated, 4 distinct states found, 0 states left on queue."); sys.exit(0)
# 時間切れの前の進み具合の行の区切りは JVM のロケールで変わる（#1339 で本物の TLC 2.19 から取った形）
for form, sep in (("SLEEPDE", "."), ("SLEEPFR", "\u202f"), ("SLEEPNB", "\u00a0"), ("SLEEPCH", "'")):
    if "FAKE:" + form in text:
        # 状態数の前は `(` にする——数の始まりが空白でない形も読むことを見る（`Progress(` と同じ文字）
        print(f"Progress(67) at 2026-11-20 11:11:02: 56{{sep}}259{{sep}}125 states generated (54{{sep}}153{{sep}}637 s/min), "
              f"(12{{sep}}118{{sep}}483 distinct states found (11{{sep}}632{{sep}}650 ds/min), 866{{sep}}583 states left on queue.", flush=True)
        time.sleep(3)
        sys.exit(0)
if "FAKE:SLEEP" in text:
    # 時間切れの前に出る進み具合の行（TLC 2.19 の形。#1339 で本物の TLC から取った）
    print("Progress(2) at 2026-11-20 10:38:37: 9,989 states generated (9,989 s/min), 2,219 distinct states found (2,219 ds/min), "
          "221 states left on queue.", flush=True)
    print("Progress(3) at 2026-11-20 10:39:37: 178,284 states generated (168,295 s/min), 37,791 distinct states found (35,571 ds/min), "
          "2,121 states left on queue.", flush=True)
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


def two_bodies(first: str, second: str) -> dict[str, str]:
    """本体を 2 つ（Order と Second）持つ対象。陽性対照は Broken0（違反する）。"""
    files = target(body=first, model_list="`Order.tla`・`Order.cfg`・`Second.tla`・`Second.cfg`")
    files["Second.tla"] = f"---- MODULE Second ----\n\\* FAKE:{second}\n====\n"
    files["Second.cfg"] = CFG
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
    # 時相の性質の違反で終わった回が states/ を残し、次の回が同じ秒に起動しても落ちない（#1346）
    # 本体の回どうしも別のディレクトリ——構文の誤りで残った states/ に、次の本体がぶつかって反例を落とさない（#1346 の /code-review 1 パス目）
    "前の本体の states に次の本体がぶつからない": (f"TLC の呼び方: {CALL}\n", {T1: two_bodies("PARSE", "VIOLATE")}, [], 1,
                                  "本体 Second.tla で反例が出た"),
    # 本体の回と陽性対照の回も別のディレクトリ——時相の性質の違反の本体が残した states/ に、陽性対照がぶつからない（#1346 の /code-review 2 パス目）。
    # 終了コードは本体の反例で 1 のまま変わらないので、陽性対照の行で見る
    "本体の states に陽性対照がぶつからない": (f"TLC の呼び方: {CALL}\n", {T1: target(body="TEMPORAL")}, [], 1,
                                 "陽性対照 Broken0.tla: 反例が出た（空振りでない）"),
    "前の回の states に次の回がぶつからない": (f"TLC の呼び方: {CALL}\n", {T1: target(controls=("TEMPORAL", "VIOLATE"))}, [], 0,
                                "陽性対照 Broken1.tla: 反例が出た（空振りでない）"),
    # 陽性対照を両方の一覧に書いた記録（1 パス目の CR1）——陽性対照を本体の反例と読まない
    "両方の一覧に書いた陽性対照は本体に数えない": (f"TLC の呼び方: {CALL}\n", {T1: target(model_list="`Order.tla`・`Order.cfg`・`Broken0.tla`・`Broken0.cfg`")},
                                    [], 0, "満たす"),
    "陽性対照のファイルが無い": (f"TLC の呼び方: {CALL}\n", {T1: target(controls=())}, [], 4, "陽性対照のファイルに TLC のモデル"),
    "TLC でない対象": (f"TLC の呼び方: {CALL}\n", {T1: {**target(model_list="`perm.als`"), "perm.als": "sig A {}\n"}}, [], 4, "TLC でない対象は走らせ直さない"),
    "呼び方の行が無い": (None, {T1: target()}, [], 4, "TLC の呼び方が無い"),
    "一覧のファイルが無い": (f"TLC の呼び方: {CALL}\n", {T1: target(drop=("Broken0.cfg",))}, [], 4, "「Broken0.cfg」がこのディレクトリの通常のファイルとして無い"),
    "反例ありが判定できなかったより先": (f"TLC の呼び方: {CALL}\n", {T1: target(body="VIOLATE"), T2: target(controls=("PASS",))}, [], 1, "反例あり 1 件"),
    "時間切れ": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEP")}, ["--timeout", "1"], 4, "時間切れ"),
    # 重さの注記（#1339）——判定には使わない
    "制約で刈った時相の性質は判定できなかった": (f"TLC の呼び方: {CALL}\n", {T1: target(body="PRUNED")}, [], 4, "時相の性質の「反例なし」は根拠にならない（状態数 4・"),
    "状態数を出す": (f"TLC の呼び方: {CALL}\n", {T1: target()}, [], 0, "本体 Order.tla: 反例なし（状態数 456789・"),
    "本体の反例の行にも重さの注記": (f"TLC の呼び方: {CALL}\n", {T1: target(body="VIOLATE")}, [], 1, "本体 Order.tla で反例が出た（状態数 9・"),
    "進み具合の行の . 区切り（ドイツ語のロケール）": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEPDE")}, ["--timeout", "1"], 4, "（状態数 12118483・"),
    "進み具合の行の U+202F 区切り（フランス語のロケール）": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEPFR")}, ["--timeout", "1"], 4, "（状態数 12118483・"),
    "進み具合の行の U+00A0 区切り": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEPNB")}, ["--timeout", "1"], 4, "（状態数 12118483・"),
    "知らない区切りの数は読まない": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEPCH")}, ["--timeout", "1"], 4, "（状態数は読めなかった・"),
    "陽性対照の状態数も出す": (f"TLC の呼び方: {CALL}\n", {T1: target()}, [], 0, "反例が出た（空振りでない）（状態数 9・"),
    "時間切れは進み具合の行の状態数": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEP")}, ["--timeout", "1"], 4, "（状態数 37791・"),
    "状態数が読めなくても判定を変えない": (f"TLC の呼び方: {CALL}\n", {T1: target(body="QUIETPASS", controls=("TEMPORAL",))}, [], 0,
                            "本体 Order.tla: 反例なし（状態数は読めなかった・"),
    "状態数の無い構文の誤りは読めなかったと言う": (f"TLC の呼び方: {CALL}\n", {T1: target(body="PARSE")}, [], 4, "（状態数は読めなかった・"),
    "判定しない: --timeout が 0": (f"TLC の呼び方: {CALL}\n", {T1: target()}, ["--timeout", "0"], 2, "--timeout は 1 以上"),
    "判定しない: 対象が無い": (f"TLC の呼び方: {CALL}\n", {}, [], 2, "usage"),
}
# 正本に states/ を残さない（終了コードに加えて見る試料）
POST = {"満たす": no_states}

# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("違反の印を不変条件だけにする", 'VIOLATED = (tlc.BROKEN_MARK, "were violated", "Deadlock reached")', "VIOLATED = (tlc.BROKEN_MARK,)",
     "時相の性質と行き止まりの印を読む"),
    ("陽性対照の空振りを通す", '空振りの疑い）{weight}: {tlc.tail(out)}")\n                if verdict == PASS:\n',
     '空振りの疑い）{weight}: {tlc.tail(out)}")\n                if False:\n', "陽性対照で反例が出ない（受入基準 2）"),
    ("通った印を見ない", "            elif rc != 0 or tlc.GOOD_MARK not in out:\n", "            elif rc != 0:\n", "本体が通ったと言わない"),
    ("本体の反例を反例ありにしない", "                verdict = COUNTEREXAMPLE\n", "                verdict = verdict\n", "本体で反例"),
    ("陽性対照のファイルが無くても通す", "    if not broken:\n        return UNKNOWN", "    if False:\n        return UNKNOWN", "陽性対照のファイルが無い"),
    ("TLC のモデルが無くても通す", "    if not bodies:\n        return UNKNOWN", "    if False:\n        return UNKNOWN", "TLC でない対象"),
    ("呼び方が無ければ PATH の tlc を使う", "    if call is None:\n        print(f\"注記: {note}\")\n",
     "    if call is None:\n        call = \"tlc\"\n        print(f\"注記: {note}\")\n", "呼び方の行が無い"),
    ("陽性対照を本体からも外さない", "    bodies = [n for n in entries(models) if n not in broken]\n", "    bodies = entries(models)\n",
     "両方の一覧に書いた陽性対照は本体に数えない"),
    ("正本で走らせる", "            return where\n", "            return str(directory)\n", "満たす"),
    ("1 回ごとに分けない（1 つの一時ディレクトリで続けて走らせる）", "            where = tempfile.mkdtemp(dir=tmp)\n", "            where = tmp\n",
     "前の回の states に次の回がぶつからない"),
    ("本体の回でディレクトリを分けない", "        for name in bodies:\n            rc, out, weight = timed(call, fresh(), name, timeout, group)\n",
     "        shared = fresh()\n        for name in bodies:\n            rc, out, weight = timed(call, shared, name, timeout, group)\n",
     "前の本体の states に次の本体がぶつからない"),
    ("陽性対照が最後に作ったディレクトリを使い回す", "timed(call, fresh(), name, timeout, group)\n            if violated(out):\n                lines.append(f\"{directory}: 陽性対照",
     "timed(call, max((str(d) for d in Path(tmp).iterdir() if d.is_dir()), key=lambda d: Path(d).stat().st_mtime_ns), name, timeout, group)\n            if violated(out):\n                lines.append(f\"{directory}: 陽性対照",
     "本体の states に陽性対照がぶつからない"),
    ("判定できなかったを反例ありより先に読む", "    if COUNTEREXAMPLE in verdicts:\n", "    if COUNTEREXAMPLE in verdicts and UNKNOWN not in verdicts:\n",
     "反例ありが判定できなかったより先"),
    ("桁区切りを外さない", "re.sub('[' + GROUP_SEPARATORS + ']', '', found[-1])", "found[-1]", "時間切れは進み具合の行の状態数"),
    ("最初の状態数を読む（時間切れの最後の進み具合でなく）", "'', found[-1])", "'', found[0])", "時間切れは進み具合の行の状態数"),
    ("桁区切りを , だけにする", 'GROUP_SEPARATORS = ",.\\u00a0\\u202f"', 'GROUP_SEPARATORS = ","', "進み具合の行の . 区切り（ドイツ語のロケール）"),
    ("U+202F を区切りにしない", 'GROUP_SEPARATORS = ",.\\u00a0\\u202f"', 'GROUP_SEPARATORS = ",.\\u00a0"', "進み具合の行の U+202F 区切り（フランス語のロケール）"),
    ("U+00A0 を区切りにしない", 'GROUP_SEPARATORS = ",.\\u00a0\\u202f"', 'GROUP_SEPARATORS = ",.\\u202f"', "進み具合の行の U+00A0 区切り"),
    ("数の始まりを空白だけにする", "(?<![^ \\t:(\\n])", "(?<![^ ])", "進み具合の行の . 区切り（ドイツ語のロケール）"),
    ("制約で刈った時相の性質の反例なしを満たすにする", "            elif PRUNED_LIVENESS in out:\n", "            elif False:\n", "制約で刈った時相の性質は判定できなかった"),
    ("数の始まりを縛らない", "(?<![^ \\t:(\\n])", "", "知らない区切りの数は読まない"),
    ("本体の反例の行に重さの注記を付けない", "で反例が出た{weight}: ", "で反例が出た: ", "本体の反例の行にも重さの注記"),
    ("経過時間に 秒 を付けない", "{seconds:.1f} 秒）", "{seconds:.1f}）", "時間切れは進み具合の行の状態数"),
    ("状態数が読めないと判定できなかったにする", "    return rc, out, measure(out, time.monotonic() - begun)\n",
     "    return (rc if DISTINCT.search(out or \"\") else None), out, measure(out, time.monotonic() - begun)\n",
     "状態数が読めなくても判定を変えない"),
    ("陽性対照に重さの注記を付けない", "反例が出た（空振りでない）{weight}\")", "反例が出た（空振りでない）\")", "陽性対照の状態数も出す"),
    ("--timeout を使わない", "        verdict, lines = rerun(call, directory, int(args.timeout))\n", "        verdict, lines = rerun(call, directory, TIMEOUT)\n", "時間切れ"),
]


TREE = REAL_REPO / "plugins" / "spec-loop" / "references" / "tree.md"
CI_SECTION = "## 保存したモデルを CI で走らせ続ける"
CI_STEP = "- name: 保存したモデルを走らせ直す"
ALLOY = {"README.md": "| 項目 | 記録 |\n| --- | --- |\n| モデルのファイル | `perm.als` |\n", "perm.als": "sig A {}\n"}
# 名前 → ({対象のパス: 中身}, 0 で終わるか, 出力に含む語——走らせずに通った形と分けるため)
CI_CASES: dict[str, tuple[dict, bool]] = {
    "雛形: 空振りのモデルで落ちる（受入基準 4）": ({T1: target(controls=("PASS",))}, False, "空振りの疑い"),
    "雛形: 本体の反例で落ちる": ({T1: target(body="VIOLATE")}, False, "本体 Order.tla で反例が出た"),
    "雛形: 陽性対照のファイルの無いモデルで落ちる": ({T1: target(controls=())}, False, "陽性対照のファイルに TLC のモデル"),
    "雛形: 通るモデルは通す": ({T1: target()}, True, "渡した 1 件とも満たす"),
    "雛形: TLC でない対象は渡さない": ({T1: target(), T2: ALLOY}, True, "渡した 1 件とも満たす"),
    "雛形: TLC の対象が無ければ通す": ({T2: ALLOY}, True, "TLC のモデルが無い"),
}
# (名前, 壊す前, 壊した後, 殺す試料)——雛形の run: の中身を崩す
CI_MUTATIONS = [
    ("最後のコマンドの結果を捨てる", "check-formal-rerun.py . $targets", "check-formal-rerun.py . $targets || true", "雛形: 空振りのモデルで落ちる（受入基準 4）"),
    ("TLC でない対象も渡す", 'if ls "$d"*.tla > /dev/null 2>&1; then targets="$targets $d"; fi', 'targets="$targets $d"', "雛形: TLC でない対象は渡さない"),
]


def ci_block(markdown: str) -> str:
    """tree.md の雛形の、モデルを走らせ直すステップの `run: |` の中身（字下げを外したもの）。"""
    section = re.search(rf"^{re.escape(CI_SECTION)}.*?(?=^## )", markdown, flags=re.MULTILINE | re.DOTALL)
    check("tree.md に CI の雛形の節がある", section is not None)
    lines = section.group(0).splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip().startswith(CI_STEP)), None)
    check("雛形にモデルを走らせ直すステップがある", start is not None)
    check("ステップの次の行が run: |", lines[start + 1].strip() == "run: |", lines[start + 1])
    body = []
    indent = len(lines[start + 1]) - len(lines[start + 1].lstrip())
    for line in lines[start + 2:]:
        if line.strip() == "```" or (line.strip() and len(line) - len(line.lstrip()) <= indent):
            break
        body.append(line)
    return textwrap.dedent("\n".join(body)) + "\n"


def run_ci(block: str, plugin_scripts: Path, work: Path, fake: Path, targets: dict) -> tuple[int, str]:
    if work.exists():
        shutil.rmtree(work)
    repo = work / "canon"
    repo.mkdir(parents=True)
    assert_in_tmp(repo)
    (repo / "CLAUDE.md").write_text(f"TLC の呼び方: {fake}\n", encoding="utf-8")
    shutil.copytree(plugin_scripts, repo / ".spec-loop" / "plugins" / "spec-loop" / "scripts")
    for rel, files in targets.items():
        (repo / rel).mkdir(parents=True)
        for name, body in files.items():
            (repo / rel / name).write_text(body, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", block], capture_output=True, text=True,
                          cwd=repo, env=env, timeout=300)
    return proc.returncode, proc.stdout + proc.stderr


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
    proc = subprocess.run([sys.executable, "-I", str(script), str(repo), *[str(repo / rel) for rel in targets], *extra],
                          capture_output=True, text=True, cwd=work, env=env_of(work, fakebin), timeout=120)
    return proc.returncode, proc.stdout + proc.stderr, repo


def env_of(work: Path, fakebin: Path) -> dict[str, str]:
    """試料ごとの空の `TMPDIR`（#1600。走らせた後の残りを見る・利用者の `$TMPDIR` を回収させない）。"""
    (work / "tmp").mkdir(parents=True, exist_ok=True)
    return {**os.environ, "PATH": f"{fakebin}{os.pathsep}/usr/bin{os.pathsep}/bin", "TMPDIR": str(work / "tmp"),
            "FAKE_TLC_PID": str(work / "tlc.pid"), "FAKE_TLC_MASK": str(work / "tlc.mask")}


def leftovers(work: Path) -> list[str]:
    """`TMPDIR` に残った一時ディレクトリ（#1600）。"""
    tmp = work / "tmp"
    return sorted(p.name for p in tmp.iterdir() if p.name.startswith(PREFIX)) if tmp.is_dir() else []


# 出力に当てる正規表現（終了コードと語に加えて見る試料）——経過時間は回ごとに変わるので語では見られない
PATTERN = {"時間切れは進み具合の行の状態数": r"本体 Order\.tla が通らず、反例も出さなかった（終了コード None）（状態数 37791・[0-9]+\.[0-9] 秒）"}


def as_expected(name: str, case: tuple, result: tuple[int, str, Path]) -> bool:
    code, out, repo = result
    return (code == case[3] and case[4] in out and (name not in POST or POST[name](repo)) and not leftovers(repo.parent)
            and (name not in PATTERN or re.search(PATTERN[name], out) is not None))


# --- 信号と回収（#1600）——本体と check-tlc.py の部品を、子のプロセスで当てる ---
SLEEPY = (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEPY")}, [], 0, "")


def setup(work: Path, fake: Path, fakebin: Path, case: tuple, seed: dict[str, bytes | None] | None = None) -> tuple[list[str], dict[str, str]]:
    """正本を組み、(argv, env)。`seed` は `TMPDIR` に先に置くディレクトリ（中身は `.tool-group` の記録。None なら置かない）。"""
    claude, targets, extra, _, _ = case
    if work.exists():
        shutil.rmtree(work)
    repo = work / "repo"
    repo.mkdir(parents=True)
    assert_in_tmp(repo)
    (repo / "CLAUDE.md").write_text(claude.replace(CALL, str(fake)), encoding="utf-8")
    for rel, files in targets.items():
        (repo / rel).mkdir(parents=True)
        for name, body in files.items():
            (repo / rel / name).write_text(body, encoding="utf-8")
    env = env_of(work, fakebin)
    for name, record in (seed or {}).items():
        (work / "tmp" / name).mkdir()
        (work / "tmp" / name / "keep").write_text("x", encoding="utf-8")
        if record is not None:
            (work / "tmp" / name / ".tool-group").write_bytes(record)
    return [str(repo), *[str(repo / rel) for rel in targets], *extra], env


def wait_pid(work: Path) -> int | None:
    pid_file = work / "tlc.pid"
    for _ in range(300):
        if pid_file.is_file() and pid_file.read_text().strip():
            return int(pid_file.read_text())
        time.sleep(0.05)
    return None


def gone(pid: int) -> bool:
    for _ in range(100):  # 親の居なくなった子は init が拾うまで少しかかる
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    os.kill(pid, signal.SIGKILL)  # 偽の TLC を置き去りにしない
    return False


def dead_pid() -> int:
    proc = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"], capture_output=True, text=True, check=True)
    pid = int(proc.stdout)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return pid
    raise AssertionError(f"終わったはずのプロセス {pid} が居る（pid の再使用）——試料を組めない")


# `sh -c` の最後のコマンドを exec しない sh（Linux の dash）では、検査器は sh の子で、sh が待たせ方を解いてから起こすことがあり、検査器の待たせ方を見ても引き継いだかが分からない（PR #1627 の CI）。
# 本体を読み込み、`/bin/sh -c` に渡す文字列の頭に `exec ` を足して、検査器を Popen の子そのものにしてから本体を走らせる
EXEC_SHELL = """import importlib.util, subprocess, sys
spec = importlib.util.spec_from_file_location("check_formal_rerun", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
real = subprocess.Popen
class Popen(real):
    def __init__(self, args, *a, **k):
        if isinstance(args, list) and args[:2] == ["/bin/sh", "-c"]:
            args = [*args[:2], "exec " + args[2], *args[3:]]
        super().__init__(args, *a, **k)
subprocess.Popen = Popen
sys.exit(module.main(sys.argv[2:]))
"""


def signal_problems(script: Path, work: Path, fake: Path, fakebin: Path, sig: int, exec_shell: bool = False) -> list[str]:
    """TLC が走っている間に信号を受けたら、TLC を止め、一時ディレクトリを消し、128+信号で終わる。`exec_shell` は検査器を Popen の子そのものにする形（上の EXEC_SHELL）。"""
    argv, env = setup(work, fake, fakebin, SLEEPY)
    head = [str(script)]
    if exec_shell:
        wrapper = work / "exec_shell.py"
        wrapper.write_text(EXEC_SHELL, encoding="utf-8")
        head = [str(wrapper), str(script)]
    proc = subprocess.Popen([sys.executable, "-I", *head, *argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            cwd=work, env=env, preexec_fn=lambda: signal.signal(sig, signal.SIG_DFL))  # 走らせる側が無視にしていても、試料は既定から始める
    pid = wait_pid(work)
    if pid is None:
        proc.kill()
        proc.communicate()
        return ["偽の TLC が起動しなかった（試料を組めない）"]
    proc.send_signal(sig)
    try:
        out, _ = proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        gone(pid)
        return [f"信号の後 30 秒で終わらない: {out[-300:]!r}"]
    problems = []
    if proc.returncode != 128 + sig:
        problems.append(f"終了コード {proc.returncode}（期待 {128 + sig}）: {out[-300:]!r}")
    if "信号" not in out:
        problems.append(f"信号で止められたと言わない: {out[-300:]!r}")
    if not gone(pid):
        problems.append(f"TLC（偽の TLC。pid {pid}）が残った")
    if leftovers(work):
        problems.append(f"TMPDIR に残した: {leftovers(work)}")
    mask = (work / "tlc.mask").read_text() if (work / "tlc.mask").is_file() else None
    if mask != "[]":
        problems.append(f"TLC が信号を待たされたまま起きた（{mask}）")
    return problems


def ignored_problems(script: Path, work: Path, fake: Path, fakebin: Path, sig: int) -> list[str]:
    """親が無視にした信号は無視のまま——TLC が走っている間に受けても止まらず、判定し切る。"""
    argv, env = setup(work, fake, fakebin, SLEEPY)
    env["FAKE_TLC_SLEEP"] = "2"
    proc = subprocess.Popen([sys.executable, "-I", str(script), *argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            cwd=work, env=env, preexec_fn=lambda: signal.signal(sig, signal.SIG_IGN))
    if wait_pid(work) is None:
        proc.kill()
        proc.communicate()
        return ["偽の TLC が起動しなかった（試料を組めない）"]
    proc.send_signal(sig)
    try:
        out, _ = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        return [f"60 秒で終わらない: {out[-300:]!r}"]
    problems = [] if proc.returncode == 0 and "渡した 1 件とも満たす" in out else [f"終了コード {proc.returncode}（期待 0——親が無視にした信号で止まった）: {out[-300:]!r}"]
    if leftovers(work):
        problems.append(f"TMPDIR に残した: {leftovers(work)}")
    return problems


def reclaim_problems(script: Path, work: Path, fake: Path, fakebin: Path) -> list[str]:
    """SIGKILL の残り（持ち主の居ない pid つき）だけを消し、持ち主の居るもの・分からないもの・この形でない名前・ほかの頭のものを消さない。"""
    pid = dead_pid()
    dead = f"{PREFIX}{pid}-abcd1234"
    full = str(pid)[0] + str(pid)[1:].translate({ord(c): ord(c) + 0xFEE0 for c in "0123456789"})  # 2 桁目から全角
    keep = {"持ち主が居る": f"{PREFIX}{os.getpid()}-abcd1234", "持ち主が分からない（pid 1。権限）": f"{PREFIX}1-abcd1234",
            "pid の無い古い名前": f"{PREFIX}zzflmv9r", "全角の数字": f"{PREFIX}{full}-abcd1234", "乱字に無い文字": f"{PREFIX}{pid}-abcd12é4",
            "後ろに余分": f"{PREFIX}{pid}-abcd1234-keep", "乱字が 1 文字": f"{PREFIX}{pid}-a", "pid の先頭の 0": f"{PREFIX}00{pid}-abcd1234",
            "pid が 0": f"{PREFIX}0-abcd1234", "ほかの頭（Alloy）": f"spec-loop-check-alloy-{pid}-abcd1234",
            "ほかの頭（状態遷移図）": f"spec-loop-statechart-{pid}-abcd1234"}
    argv, env = setup(work, fake, fakebin, CASES["満たす"], {dead: None, **{name: None for name in keep.values()}})
    proc = subprocess.run([sys.executable, "-I", str(script), *argv], capture_output=True, text=True, cwd=work, env=env, timeout=120)
    out = proc.stdout + proc.stderr
    problems = [] if proc.returncode == 0 else [f"終了コード {proc.returncode}: {out[-300:]!r}"]
    if (work / "tmp" / dead).exists() or "持ち主の居ない一時ディレクトリを消した" not in out:
        problems.append(f"持ち主の居ないディレクトリを消していない: {out[-300:]!r}")
    for why, name in keep.items():
        if not (work / "tmp" / name / "keep").is_file():
            problems.append(f"消してはならないディレクトリを消した（{why}）: {name!r}")
    return problems


def unreadable_problems(script: Path, work: Path, fake: Path, fakebin: Path) -> list[str]:
    """持ち主の居ない残りの `.tool-group` が読めない（権限・ASCII でない・数字でない・0 以下）とき、判定を止めず、その残りを消さずにそう言う。"""
    pid = dead_pid()
    contents = {"abcd1234": b"1", "efgh5678": b"\xff\xfe", "ijkl9012": b"abc", "mnop3456": b"0", "qrst7890": b"-1"}  # 最初のものは権限を外す
    names = {f"{PREFIX}{pid}-{suffix}": body for suffix, body in contents.items()}
    argv, env = setup(work, fake, fakebin, CASES["満たす"], names)
    record = work / "tmp" / next(iter(names)) / ".tool-group"
    record.chmod(0)
    try:
        if os.access(record, os.R_OK):
            return ["権限を外しても読める（root で走っている？）——試料を組めない"]
        proc = subprocess.run([sys.executable, "-I", str(script), *argv], capture_output=True, text=True, cwd=work, env=env, timeout=120)
    finally:
        if record.exists():  # 消された（変異）なら戻すものは無い
            record.chmod(0o600)
    out = proc.stdout + proc.stderr
    problems = [] if proc.returncode == 0 else [f"終了コード {proc.returncode}（期待 0）: {out[-300:]!r}"]
    for name, body in names.items():
        if not (work / "tmp" / name).is_dir():
            problems.append(f"記録の読めない残りを消した（中身 {body!r}。TLC が走っているかを決められないのに）")
        elif not any(name in line and "読めない" in line and "消していない" in line for line in out.splitlines()):
            problems.append(f"消していないことを言わない（中身 {body!r}）: {out[-300:]!r}")
    return problems


def killed_problems(script: Path, work: Path, fake: Path, fakebin: Path) -> list[str]:
    """SIGKILL の後も別のセッションの TLC が走っている間は、次の起動が一時ディレクトリを消さずにそう言い、止まった後の起動が消す。"""
    argv, env = setup(work, fake, fakebin, SLEEPY)
    proc = subprocess.Popen([sys.executable, "-I", str(script), *argv], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=work, env=env)
    pid = wait_pid(work)
    if pid is None:
        proc.kill()
        proc.wait()
        return ["偽の TLC が起動しなかった（試料を組めない）"]
    proc.kill()
    proc.wait()
    problems = []
    other = setup(work / "next", fake, fakebin, CASES["満たす"])[0]  # 同じ TMPDIR で、別の正本を判定する
    try:
        first = subprocess.run([sys.executable, "-I", str(script), *other], capture_output=True, text=True, cwd=work, env=env, timeout=120)
        out = first.stdout + first.stderr
        left = leftovers(work)
        if len(left) != 1 or not any(left[0] in line and "まだ書いている" in line and "消していない" in line for line in out.splitlines()):
            problems.append(f"TLC が走っている間に消した・そう言わない（残り {left}）: {out[-300:]!r}")
    finally:
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)  # 偽物の pid はグループの番号とは限らない——Linux の sh（dash）は `sh -c` の最後のコマンドを exec しないことがある（PR #1627 の CI）
        except ProcessLookupError:
            pass
    if not gone(pid):
        problems.append("偽の TLC を止められない（試料を組めない）")
    second = subprocess.run([sys.executable, "-I", str(script), *other], capture_output=True, text=True, cwd=work, env=env, timeout=120)
    if leftovers(work):
        problems.append(f"TLC が止まった後の起動が消さない: {leftovers(work)}: {(second.stdout + second.stderr)[-300:]!r}")
    return problems


# 片付けの途中に信号が届く形——本体を読み込み、`shutil.rmtree` の入口で自分に SIGTERM を送ってから本体を走らせる（`times` 回まで）。
# 1 回目は正常に終わる回の TemporaryDirectory の片付け、2 回目は信号の後の消し直し
IN_CLEANUP = """import importlib.util, os, shutil, signal, sys
spec = importlib.util.spec_from_file_location("check_formal_rerun", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
real, fired, times = shutil.rmtree, [], int(sys.argv[2])
def rmtree(*a, **k):
    if len(fired) < times:
        fired.append(1)
        os.kill(os.getpid(), signal.SIGTERM)
    return real(*a, **k)
shutil.rmtree = rmtree
sys.exit(module.main(sys.argv[3:]))
"""


def cleanup_problems(script: Path, work: Path, fake: Path, fakebin: Path, times: int) -> list[str]:
    """片付けの途中に信号が届いても（消し直しの途中の 2 回目・3 回目も）、一時ディレクトリを残さず 128+信号で終わる。"""
    argv, env = setup(work, fake, fakebin, CASES["満たす"])
    wrapper = work / "in_cleanup.py"
    wrapper.write_text(IN_CLEANUP, encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(wrapper), str(script), str(times), *argv],
                          capture_output=True, text=True, cwd=work, env=env, timeout=120, preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL))
    problems = []
    if proc.returncode != 128 + signal.SIGTERM:
        problems.append(f"終了コード {proc.returncode}（期待 {128 + signal.SIGTERM}）: {(proc.stdout + proc.stderr)[-300:]!r}")
    if leftovers(work):
        problems.append(f"TMPDIR に残した: {leftovers(work)}")
    return problems


# 信号の扱いの境目に信号が届く形（1 パス目の /code-review の指摘 CR1-1・CR1-2 と Verifier の観察 1）——本体を読み込み、
# popen: Popen が子を起こした後・返る前に SIGTERM（起こした検査器の pid を書く）／catch: 1 つ目を入れた直後に SIGTERM／restore: 1 つ目を戻した直後に SIGHUP。
# 信号を受けた直後に関数を 1 つ呼んで、待っていない信号の例外をその場で上げさせる
WINDOW = """import importlib.util, os, signal, subprocess, sys, time
spec = importlib.util.spec_from_file_location("check_formal_rerun", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
kind, pid_file = sys.argv[2], sys.argv[3]
if kind == "popen":
    real = subprocess.Popen
    class Popen(real):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            open(pid_file, "w").write(str(self.pid))
            # 偽の検査器が起きて pid を書くまで待ってから送る——起きる前に作業ディレクトリが消えると、偽物は自分で死に（読めない・閉じた管に書いて SIGPIPE）、残る形と区別できない（実測の交絡）
            for _ in range(300):
                if os.path.exists(os.environ["FAKE_TLC_PID"]):
                    break
                time.sleep(0.02)
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(0.01)
    subprocess.Popen = Popen
elif kind == "restore-entry":  # 信号の扱いを戻す入口（待たせる前）に SIGTERM（2 パス目の /code-review の指摘 CR2-1）
    real_restore = module.tlc.restore_signals
    def restore_signals(saved):
        os.kill(os.getpid(), signal.SIGTERM)
        return real_restore(saved)
    module.tlc.restore_signals = restore_signals
else:
    real, count = signal.signal, []
    def wrapped(sig, handler):
        result = real(sig, handler)
        if sys._getframe(1).f_code.co_name == ("catch_signals" if kind == "catch" else "restore_signals") and not count:
            count.append(1)
            os.kill(os.getpid(), signal.SIGTERM if kind == "catch" else signal.SIGHUP)
            time.sleep(0.01)
        return result
    signal.signal = wrapped
sys.exit(module.main(sys.argv[4:]))
"""


def window_problems(script: Path, work: Path, fake: Path, fakebin: Path, kind: str) -> list[str]:
    """信号の扱いの境目に届いた信号: 起こした直後・入れる途中は 143 で検査器と一時ディレクトリを残さず、戻す途中は戻した後の扱い（既定）で終わる（1 ではない）。"""
    argv, env = setup(work, fake, fakebin, SLEEPY if kind == "popen" else CASES["満たす"])
    wrapper = work / "window.py"
    wrapper.write_text(WINDOW, encoding="utf-8")
    pid_file = work / "popen.pid"
    proc = subprocess.run([sys.executable, "-I", str(wrapper), str(script), kind, str(pid_file), *argv], capture_output=True, text=True,
                          cwd=work, env=env, timeout=120,
                          preexec_fn=lambda: [signal.signal(s, signal.SIG_DFL) for s in (signal.SIGTERM, signal.SIGHUP)])
    out = proc.stdout + proc.stderr
    want = -signal.SIGHUP if kind == "restore" else 128 + signal.SIGTERM
    problems = [] if proc.returncode == want else [f"終了コード {proc.returncode}（期待 {want}）: {out[-300:]!r}"]
    if "Traceback" in out:
        problems.append(f"捕まえられない例外で止まった: {out[-300:]!r}")
    if kind == "popen":
        if not pid_file.is_file():
            problems.append("起こした検査器の pid が無い（試料を組めない）")
        else:
            group = int(pid_file.read_text())
            time.sleep(0.2)
            try:
                os.killpg(group, 0)
            except ProcessLookupError:
                pass
            else:
                os.killpg(group, signal.SIGKILL)
                problems.append("起こした直後の信号で、検査器のグループが残った")
    if leftovers(work):
        problems.append(f"TMPDIR に残した: {leftovers(work)}")
    return problems


# 時間切れの枝で止める前に届く形（2 パス目の Verifier の反証 V2-R1）——同じ場所の check-tlc.py の `run_model` を時間切れ 1 秒で眠る検査器に当て、
# 最初の `with_group`（止める呼び出し）の入口で自分に SIGTERM を送る。抜ける前に検査器のグループを止めるかを見る
TIMEOUT_BRANCH = """import importlib.util, os, signal, sys, tempfile
spec = importlib.util.spec_from_file_location("check_tlc", sys.argv[1])
tlc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tlc)
real, fired = tlc.with_group, []
def with_group(proc, sig):
    if not fired:
        fired.append(1)
        open(sys.argv[2], "w").write(str(proc.pid))
        os.kill(os.getpid(), signal.SIGTERM)
    return real(proc, sig)
tlc.with_group = with_group
saved = tlc.current_signals()
try:
    tlc.catch_signals(saved)
    tlc.run_model("sleep 30 #", tempfile.mkdtemp(), "M", 1)
    print("信号が上がらない")
except tlc.Interrupted as stop:
    print("Interrupted", stop.signum)
finally:
    tlc.restore_signals(saved)
"""


def timeout_branch_problems(script: Path, work: Path) -> list[str]:
    if work.exists():
        shutil.rmtree(work)
    (work / "tmp").mkdir(parents=True)
    wrapper = work / "timeout_branch.py"
    wrapper.write_text(TIMEOUT_BRANCH, encoding="utf-8")
    group_file = work / "timeout.pid"
    proc = subprocess.run([sys.executable, "-I", str(wrapper), str(script.parent / "check-tlc.py"), str(group_file)], capture_output=True, text=True,
                          cwd=work, env={**os.environ, "TMPDIR": str(work / "tmp")}, timeout=120,
                          preexec_fn=lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL))
    problems = [] if proc.stdout.strip() == "Interrupted 15" else [f"時間切れの枝の信号が上がらない: {(proc.stdout + proc.stderr)[-300:]!r}"]
    if not group_file.is_file():
        return problems + ["起こした検査器の pid が無い（試料を組めない）"]
    group = int(group_file.read_text())
    time.sleep(0.2)
    try:
        os.killpg(group, 0)
    except ProcessLookupError:
        return problems
    os.killpg(group, signal.SIGKILL)
    return problems + ["時間切れの枝で止める前に届いた信号で、検査器のグループが残った"]


def broken_stderr_problems(script: Path, work: Path, fake: Path, fakebin: Path) -> list[str]:
    """標準エラーが書けない（読む側を閉じた管——SIGHUP の後の閉じた端末の形）ときの SIGHUP でも、129 で TLC と一時ディレクトリを残さない（2 パス目の CR2-3）。"""
    argv, env = setup(work, fake, fakebin, SLEEPY)
    read_end, write_end = os.pipe()
    proc = subprocess.Popen([sys.executable, "-I", str(script), *argv], stdout=subprocess.PIPE, stderr=write_end, text=True,
                            cwd=work, env=env, preexec_fn=lambda: signal.signal(signal.SIGHUP, signal.SIG_DFL))
    os.close(write_end)
    pid = wait_pid(work)
    os.close(read_end)
    if pid is None:
        proc.kill()
        proc.communicate()
        return ["偽の TLC が起動しなかった（試料を組めない）"]
    proc.send_signal(signal.SIGHUP)
    try:
        proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
    problems = [] if proc.returncode == 128 + signal.SIGHUP else [f"終了コード {proc.returncode}（期待 {128 + signal.SIGHUP}）"]
    if not gone(pid):
        problems.append("TLC が残った")
    if leftovers(work):
        problems.append(f"TMPDIR に残した: {leftovers(work)}")
    return problems


# 同じプロセスで main を呼んだ後、信号の扱いが元に戻るか（formal-sync.py のように読み込んで使う側・テスト）
RESTORE = """import importlib.util, signal, sys
spec = importlib.util.spec_from_file_location("check_formal_rerun", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sigs = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
before = [signal.getsignal(s) for s in sigs]
rc = module.main(sys.argv[2:])
print("戻った" if [signal.getsignal(s) for s in sigs] == before else "戻らない")
sys.exit(rc)
"""


def restore_problems(script: Path, work: Path, fake: Path, fakebin: Path) -> list[str]:
    argv, env = setup(work, fake, fakebin, CASES["満たす"])
    wrapper = work / "restore.py"
    wrapper.write_text(RESTORE, encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(wrapper), str(script), *argv], capture_output=True, text=True, cwd=work, env=env, timeout=120)
    out = proc.stdout + proc.stderr
    return [] if proc.returncode == 0 and "戻った" in out else [f"信号の扱いが元に戻らない（終了コード {proc.returncode}）: {out[-300:]!r}"]


SIGNAL_CASES = {f"信号: {sig.name}": sig for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
IGNORED_CASES = {f"親が無視にした信号: {sig.name}": sig for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)}
SPECIAL = [*SIGNAL_CASES, *IGNORED_CASES, "回収", "回収: 記録が読めない", "SIGKILL の後に TLC が走っている",
           "信号: 片付けの途中", "信号: 片付けの途中に 3 回", "main の後に信号の扱いを戻す",
           "信号: 起こした直後（Popen の中）", "信号: 入れる途中", "信号: 戻す途中",
           "信号: 戻す入口", "信号: 時間切れの枝", "信号: 書けない標準エラー", "信号: 検査器の待たせ方（sh が exec する形）"]


def special_problems(name: str, script: Path, work: Path, fake: Path, fakebin: Path) -> list[str]:
    if name in SIGNAL_CASES:
        return signal_problems(script, work, fake, fakebin, SIGNAL_CASES[name])
    if name in IGNORED_CASES:
        return ignored_problems(script, work, fake, fakebin, IGNORED_CASES[name])
    if name == "回収":
        return reclaim_problems(script, work, fake, fakebin)
    if name == "回収: 記録が読めない":
        return unreadable_problems(script, work, fake, fakebin)
    if name == "SIGKILL の後に TLC が走っている":
        return killed_problems(script, work, fake, fakebin)
    if name == "信号: 片付けの途中":
        return cleanup_problems(script, work, fake, fakebin, 1)
    if name == "信号: 片付けの途中に 3 回":  # 3 回目は、戻す入口の信号を受ける外の try の片付けに届く（#1600 の 2 パス目——2 回では外の try が 2 回目を受けて隠す）
        return cleanup_problems(script, work, fake, fakebin, 3)
    if name == "信号: 起こした直後（Popen の中）":
        return window_problems(script, work, fake, fakebin, "popen")
    if name == "信号: 入れる途中":
        return window_problems(script, work, fake, fakebin, "catch")
    if name == "信号: 戻す途中":
        return window_problems(script, work, fake, fakebin, "restore")
    if name == "信号: 検査器の待たせ方（sh が exec する形）":
        return signal_problems(script, work, fake, fakebin, signal.SIGTERM, exec_shell=True)
    if name == "信号: 戻す入口":
        return window_problems(script, work, fake, fakebin, "restore-entry")
    if name == "信号: 時間切れの枝":
        return timeout_branch_problems(script, work)
    if name == "信号: 書けない標準エラー":
        return broken_stderr_problems(script, work, fake, fakebin)
    return restore_problems(script, work, fake, fakebin)


# 本体（check-formal-rerun.py）を壊す変異——(名前, 壊す前, 壊した後, 殺す試料)
SPECIAL_MUTATIONS: list[tuple[str, str, str, str]] = [
    ("信号を例外にしない", "        tlc.catch_signals(saved)\n", "        pass\n", "信号: SIGTERM"),
    ("入れるのを try の外にする", "    saved = tlc.current_signals()\n    try:\n        try:\n            tlc.catch_signals(saved)\n",
     "    saved = tlc.current_signals()\n    tlc.catch_signals(saved)\n    try:\n        try:\n", "信号: 入れる途中"),
    ("片付けの途中の信号の後に消し直さない", "    tlc.sweep(PREFIX)  # 片付け", "    pass  # 片付け", "信号: 片付けの途中"),
    ("戻す入口の信号を受けない", "    except tlc.Interrupted as stop:  # 信号の扱いを戻す入口", "    except ZeroDivisionError as stop:  # 信号の扱いを戻す入口", "信号: 戻す入口"),
    ("起動時に回収しない", "    for line in tlc.reclaim_lines(*tlc.reclaim(PREFIX)):\n        print(line, file=sys.stderr)\n", "", "回収"),
    ("TLC のグループを記録しない", "        group = tlc.record_group(tmp)", "        group = None", "SIGKILL の後に TLC が走っている"),
    ("名前に pid を入れない", "    with tlc.owned_dir(PREFIX) as tmp:", "    with tempfile.TemporaryDirectory(prefix=PREFIX) as tmp:", "SIGKILL の後に TLC が走っている"),
    ("信号の扱いを戻さない", "        finally:\n            tlc.restore_signals(saved)\n", "        finally:\n            pass\n", "main の後に信号の扱いを戻す"),
]

# check-tlc.py の部品を壊す変異——(名前, 壊す前, 壊した後, 殺す試料)
TLC_MUTATIONS: list[tuple[str, str, str, str]] = [
    ("親が無視にした信号を奪う", "        if old is not signal.SIG_IGN:", "        if True:", "親が無視にした信号: SIGHUP"),
    ("無視の確認を SIGHUP だけに効かせる", "        if old is not signal.SIG_IGN:", "        if sig != signal.SIGHUP or old is not signal.SIG_IGN:", "親が無視にした信号: SIGINT"),
    ("SIGHUP を片付けない", "SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)", "SIGNALS = (signal.SIGTERM, signal.SIGINT)", "信号: SIGHUP"),
    ("1 回目の後に信号を無視しない", "    for sig in SIGNALS:  # 2 回目は無視する", "    for sig in ():  # 2 回目は無視する", "信号: 片付けの途中に 3 回"),
    ("元の扱いに戻さない", "            signal.signal(sig, signal.SIG_DFL if old is None else old)", "            pass", "main の後に信号の扱いを戻す"),
    ("戻す途中の信号を待たせない", "    mask = signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)\n    try:\n        for sig, old in saved.items():",
     "    mask = signal.pthread_sigmask(signal.SIG_BLOCK, ())\n    try:\n        for sig, old in saved.items():", "信号: 戻す途中"),
    ("起こす間に信号を待たせない", "    mask = signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)\n    try:\n        proc = subprocess.Popen(",
     "    mask = signal.pthread_sigmask(signal.SIG_BLOCK, ())\n    try:\n        proc = subprocess.Popen(", "信号: 起こした直後（Popen の中）"),
    ("検査器に待たせた信号を引き継ぐ", ", preexec_fn=lambda: signal.pthread_sigmask(signal.SIG_SETMASK, mask))", ")", "信号: 検査器の待たせ方（sh が exec する形）"),
    ("待っている間の例外・時間切れの枝で止める前の信号で検査器を止めない", "        if proc.returncode is None:\n            with_group(proc, signal.SIGKILL)\n",
     "        if False:\n            with_group(proc, signal.SIGKILL)\n", "信号: 時間切れの枝"),
    ("書けない標準エラーで例外を上げる", "    except OSError:\n        sys.stderr = None", "    except ZeroDivisionError:\n        sys.stderr = None", "信号: 書けない標準エラー"),
    ("書けない標準エラーで終わるときの書き出しを失敗させる", "        sys.stderr = None  # 終わるときの", "        pass  # 終わるときの", "信号: 書けない標準エラー"),
    ("消し直しで自分の pid を見ない", 'glob(f"{prefix}{os.getpid()}-*")', 'glob(f"{prefix}0-*")', "信号: 片付けの途中"),
    ("持ち主の居ないディレクトリを消さない", "        shutil.rmtree(path, ignore_errors=True)\n        if not path.exists():", "        pass\n        if not path.exists():", "回収"),
    ("持ち主の居るディレクトリも消す", "        if int(found.group(1)) == os.getpid() or alive(int(found.group(1))):", "        if False:", "回収"),
    ("分からない pid を居ないに倒す", "    except (OSError, OverflowError):\n        return True\n    return True", "    except (OSError, OverflowError):\n        return False\n    return True", "回収"),
    ("ほかの頭のものも消す", "    return re.compile(re.escape(prefix) + r\"([1-9]", "    return re.compile(r\"spec-loop-[a-z-]*?-\" + r\"([1-9]", "回収"),
    ("pid の無い古い名前も消す", "        if not found or path.is_symlink() or not path.is_dir():\n            continue\n        if int(",
     "        if path.is_symlink() or not path.is_dir():\n            continue\n        if not found:\n            shutil.rmtree(path)\n            continue\n        if int(", "回収"),
    ("全角の数字を pid と読む", 'r"([1-9][0-9]*)-[a-z0-9_]{8}")', 'r"([1-9]\\d*)-[a-z0-9_]{8}")', "回収"),
    ("pid の先頭の 0 と pid 0 を読む", 'r"([1-9][0-9]*)-[a-z0-9_]{8}")', 'r"([0-9]+)-[a-z0-9_]{8}")', "回収"),
    ("乱字に無い文字の名前を消す", 'r"([1-9][0-9]*)-[a-z0-9_]{8}")', 'r"([1-9][0-9]*)-[^-]{8}")', "回収"),
    ("乱字の長さを見ない", 'r"([1-9][0-9]*)-[a-z0-9_]{8}")', 'r"([1-9][0-9]*)-[a-z0-9_]+")', "回収"),
    ("名前の後ろの余分を見ない", "        found = owned.fullmatch(path.name)", "        found = owned.match(path.name)", "回収"),
    ("TLC が走っていても消す", "        if group is not None:  # 持ち主が SIGKILL", "        if False:  # 持ち主が SIGKILL", "SIGKILL の後に TLC が走っている"),
    ("読めない記録の残りを消す", "    except OSError:  # 権限などで読めない\n        return UNREADABLE", "    except OSError:  # 権限などで読めない\n        return None", "回収: 記録が読めない"),
    ("数字でない記録の残りを消す", "    except ValueError:  # ASCII でない（UnicodeDecodeError も ValueError）・数字でない\n        return UNREADABLE",
     "    except ValueError:  # ASCII でない（UnicodeDecodeError も ValueError）・数字でない\n        return None", "回収: 記録が読めない"),
    ("0 以下の記録をグループと読む", "    if group < 1:", "    if False:", "回収: 記録が読めない"),
    ("読めない記録を黙る", "        if group == UNREADABLE:\n            lines.append(", "        if group == UNREADABLE:\n            continue\n            lines.append(", "回収: 記録が読めない"),
]


def special_killed(killer: str, script: Path, work: Path, fake: Path, fakebin: Path) -> bool:
    return bool(special_problems(killer, script, work, fake, fakebin))


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

        print("信号と回収（#1600）")
        for i, name in enumerate(SPECIAL):
            problems = special_problems(name, scripts / TARGET, root / f"s{i}", fake, fakebin)
            check(f"試料: {name}", not problems, "・".join(problems))
        print(f"  {len(SPECIAL)} 件 OK")
        tlc_source = (SCRIPTS / "check-tlc.py").read_text(encoding="utf-8")
        for target_name, text, mutations in ((TARGET, source, SPECIAL_MUTATIONS), ("check-tlc.py", tlc_source, TLC_MUTATIONS)):
            for index, (name, before, after, killer) in enumerate(mutations):
                check(f"壊す箇所がちょうど 1 回: {name}", text.count(before) == 1, f"{text.count(before)} 回: {before!r}")
                mutated = root / f"sm-{target_name}-{index}"
                shutil.copytree(scripts, mutated)
                (mutated / target_name).write_text(text.replace(before, after), encoding="utf-8")
                check(f"変異を殺す: {name} ← {killer}", special_killed(killer, mutated / TARGET, root / f"smw-{target_name}-{index}", fake, fakebin))
        print(f"  変異 {len(SPECIAL_MUTATIONS) + len(TLC_MUTATIONS)} 件 OK")

        print("CI の雛形（#1178）")
        block = ci_block(TREE.read_text(encoding="utf-8"))
        for i, (name, (targets, passes, word)) in enumerate(CI_CASES.items()):
            code, out = run_ci(block, scripts, root / f"ci{i}", fake, targets)
            check(name, (code == 0) == passes and word in out and "Traceback" not in out, f"終了コード {code}: {out[-400:]!r}")
        for name, before, after, killer in CI_MUTATIONS:
            check(f"雛形の壊す箇所がちょうど 1 回: {name}", block.count(before) == 1, f"{block.count(before)} 回")
            targets, passes, _ = CI_CASES[killer]
            code, out = run_ci(block.replace(before, after), scripts, root / "cimut", fake, targets)
            check(f"雛形の変異を殺す: {name} ← {killer}", (code == 0) != passes, f"終了コード {code}: {out[-300:]!r}")
        print(f"  試料 {len(CI_CASES)} 件・変異 {len(CI_MUTATIONS)} 件 OK")
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件・信号と回収の試料 {len(SPECIAL)} 件・変異 {len(SPECIAL_MUTATIONS) + len(TLC_MUTATIONS)} 件・"
          f"雛形の試料 {len(CI_CASES)} 件・雛形の変異 {len(CI_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
