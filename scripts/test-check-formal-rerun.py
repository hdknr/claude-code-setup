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
    print("Model checking completed. No error has been found.")
    # 最後の行は区切らない（TLC 2.19 はロケールに依らずこの形。#1339 で ドイツ語のロケールでも確かめた）
    print("1234567 states generated, 456789 distinct states found, 0 states left on queue."); sys.exit(0)
if "FAKE:QUIETPASS" in text:  # 状態数の行を出さずに通る（ほかの版で形が違うとき）
    print("Model checking completed. No error has been found."); sys.exit(0)
if "FAKE:VIOLATE" in text:
    print("Error: Invariant Inv is violated.")
    print("12 states generated, 9 distinct states found, 3 states left on queue."); sys.exit(12)
if "FAKE:TEMPORAL" in text:
    print("Error: Temporal properties were violated."); sys.exit(13)
if "FAKE:DEADLOCK" in text:
    print("Error: Deadlock reached."); sys.exit(11)
if "FAKE:SILENT" in text:
    sys.exit(0)
# 時間切れの前の進み具合の行の区切りは JVM のロケールで変わる（#1339 で本物の TLC 2.19 から取った形）
for form, sep in (("SLEEPDE", "."), ("SLEEPFR", "\u202f"), ("SLEEPCH", "'")):
    if "FAKE:" + form in text:
        print(f"Progress(67) at 2026-11-20 11:11:02: 56{{sep}}259{{sep}}125 states generated (54{{sep}}153{{sep}}637 s/min), "
              f"12{{sep}}118{{sep}}483 distinct states found (11{{sep}}632{{sep}}650 ds/min), 866{{sep}}583 states left on queue.", flush=True)
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
    # 重さの注記（#1339）——判定には使わない
    "状態数を出す": (f"TLC の呼び方: {CALL}\n", {T1: target()}, [], 0, "本体 Order.tla: 反例なし（状態数 456789・"),
    "本体の反例の行にも重さの注記": (f"TLC の呼び方: {CALL}\n", {T1: target(body="VIOLATE")}, [], 1, "本体 Order.tla で反例が出た（状態数 9・"),
    "進み具合の行の . 区切り（ドイツ語のロケール）": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEPDE")}, ["--timeout", "1"], 4, "（状態数 12118483・"),
    "進み具合の行の U+202F 区切り（フランス語のロケール）": (f"TLC の呼び方: {CALL}\n", {T1: target(body="SLEEPFR")}, ["--timeout", "1"], 4, "（状態数 12118483・"),
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
    ("正本で走らせる", "        where = tmp ", "        where = str(directory) ", "満たす"),
    ("判定できなかったを反例ありより先に読む", "    if COUNTEREXAMPLE in verdicts:\n", "    if COUNTEREXAMPLE in verdicts and UNKNOWN not in verdicts:\n",
     "反例ありが判定できなかったより先"),
    ("桁区切りを外さない", "re.sub('[' + GROUP_SEPARATORS + ']', '', found[-1])", "found[-1]", "時間切れは進み具合の行の状態数"),
    ("最初の状態数を読む（時間切れの最後の進み具合でなく）", "'', found[-1])", "'', found[0])", "時間切れは進み具合の行の状態数"),
    ("桁区切りを , だけにする", 'GROUP_SEPARATORS = ",.\\u00a0\\u202f"', 'GROUP_SEPARATORS = ","', "進み具合の行の . 区切り（ドイツ語のロケール）"),
    ("U+202F を区切りにしない", 'GROUP_SEPARATORS = ",.\\u00a0\\u202f"', 'GROUP_SEPARATORS = ",.\\u00a0"', "進み具合の行の U+202F 区切り（フランス語のロケール）"),
    ("数の始まりを縛らない", "(?<![^ \\t:(\\n])", "", "知らない区切りの数は読まない"),
    ("本体の反例の行に重さの注記を付けない", "で反例が出た{weight}: ", "で反例が出た: ", "本体の反例の行にも重さの注記"),
    ("経過時間に 秒 を付けない", "{seconds:.1f} 秒）", "{seconds:.1f}）", "時間切れは進み具合の行の状態数"),
    ("状態数が読めないと判定できなかったにする", "    return rc, out, measure(out, time.monotonic() - started)\n",
     "    return (rc if DISTINCT.search(out or \"\") else None), out, measure(out, time.monotonic() - started)\n",
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
    env = {**os.environ, "PATH": f"{fakebin}{os.pathsep}/usr/bin{os.pathsep}/bin"}
    proc = subprocess.run([sys.executable, "-I", str(script), str(repo), *[str(repo / rel) for rel in targets], *extra],
                          capture_output=True, text=True, cwd=work, env=env, timeout=120)
    return proc.returncode, proc.stdout + proc.stderr, repo


# 出力に当てる正規表現（終了コードと語に加えて見る試料）——経過時間は回ごとに変わるので語では見られない
PATTERN = {"時間切れは進み具合の行の状態数": r"本体 Order\.tla が通らず、反例も出さなかった（終了コード None）（状態数 37791・[0-9]+\.[0-9] 秒）"}


def as_expected(name: str, case: tuple, result: tuple[int, str, Path]) -> bool:
    code, out, repo = result
    return (code == case[3] and case[4] in out and (name not in POST or POST[name](repo))
            and (name not in PATTERN or re.search(PATTERN[name], out) is not None))


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
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件・雛形の試料 {len(CI_CASES)} 件・雛形の変異 {len(CI_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
