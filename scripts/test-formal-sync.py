#!/usr/bin/env python3
"""dev-loop の `formal-sync.py`（形式検査のモデルと実装を揃えておく。#1178）の回帰テスト。

    python3 scripts/test-formal-sync.py

**本体は `plugins/dev-loop/skills/dev-loop/scripts/formal-sync.py`**（`test-find-cycle.py` と同じ形——dev-loop はどのリポジトリでも使う）。
spec-loop の `check-formal-rerun.py`・`formal-baseline.py`・`check-tlc.py` は**本物を一時ディレクトリに写して** `--spec-loop` で渡す。
**本物の TLC は走らせない**——偽の TLC（モデルのファイルの中の印 `FAKE:VIOLATE`・`FAKE:PASS` を読んで TLC 2.19 の出力の行の形を出す）を絶対パスで呼び方の行に書く。
`FAKE:VIOLATE` を先に見るので、保存したモデル（`FAKE:PASS` を持つ）の行為の定義に `FAKE:VIOLATE` を書き足したコードのモデルは反例を出す——
「対応のファイルの不変条件を破る変更」を、行為の定義を書き直す形で作る（Issue の受入基準 3 の陽性対照）。

見るもの:

1. **touched**: 周の差分（コミット済み・未コミット・未追跡）が対応のファイルに触れたモデルを出し、触れない差分・対応の無いモデルでは出さない。
   同じ対象は番号が最大の版の記録を読む。モデルが無ければ `--spec-loop` 無しで 0。base が祖先でない・`--spec-loop` が無い（モデルがある）は 2。
2. **check**: 触れたモデルの行が無い・`反例あり（コードの不具合）`・`正本に起票する行:` の無い `反例あり（モデルのずれ）`・2 本・値の違い・フェンスの中だけは 1（受入基準 2）。
   `反例なし`・`判定できなかった`・ずれと起票の行・触れていないモデルは 0。
3. **rerun**: 保存したモデルと同じコードのモデルは `反例なし`（0）。行為を書き直して反例を出すと `反例あり（コードの不具合）`（1。受入基準 3）、`--intended` で `モデルのずれ`。
   設定・性質・`Init`・陽性対照・定義の外の行・記録の一覧を変えた・定義を消したコードのモデルは `判定できなかった`（4。弱めて通さない）。
   保存したモデルが反例を出す・空振りなら 4。対応の無いモデルは 2。新しい定義を足して行為を書き直すのは通す。
4. **リポジトリの外で単体で動く**——本体と spec-loop の `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリの git リポジトリで、`HOME`・`GIT_CONFIG_GLOBAL` を差し替える。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、名指しした試料の結果が期待と変わることを確かめる（壊す箇所が本体にちょうど 1 回現れることも先に見る）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
BODY = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "formal-sync.py"
SPEC_LOOP_SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"

FAKE_TLC = f"""#!{sys.executable}
import os, sys
text = open(sys.argv[-1], encoding="utf-8").read()
os.makedirs("states", exist_ok=True)
print("TLC2 Version 2.19 of 08 August 2024 (偽物)")
if "FAKE:VIOLATE" in text:
    print("Error: Invariant Inv is violated."); sys.exit(12)
if "FAKE:PASS" in text:
    print("Model checking completed. No error has been found."); sys.exit(0)
print("Error: Parsing or semantic analysis failed."); sys.exit(150)
"""
CFG = "INIT Init\nNEXT Next\nINVARIANT Inv\n"
MODEL = """---- MODULE Counter ----
EXTENDS Naturals
VARIABLE x
\\* FAKE:PASS
Init == x = 0
Inc ==
  /\\ x < 2
  /\\ x' = x + 1
Reset == x' = 0
Next == Inc \\/ Reset
Inv == x <= 2
====
"""
BROKEN = "---- MODULE Broken ----\n\\* FAKE:VIOLATE\n====\n"
MAPPING = "`Inc` → `app/counter.py::inc`、`Reset` → `app/counter.py::reset`"
DIR1 = "docs/v1/spec/formal/counter"
DIR2 = "docs/v2/spec/formal/counter"


def readme(mapping: str = MAPPING, controls: str = "`Broken.tla`・`Broken.cfg`", models: str = "`Counter.tla`・`Counter.cfg`") -> str:
    rows = ["| 項目 | 記録 |", "| --- | --- |", "| 対象 | `spec/x.md:1` |", "| 検査器 | TLC 2.19 |", "| 構成の大きさ | 1 |",
            "| 結果 | 反例なし |", "| 陽性対照 | Inv を狭めた |", "| 置いた前提 | なし |", "| 前回のモデル | 無かった |",
            f"| モデルのファイル | {models} |", f"| 陽性対照のファイル | {controls} |"]
    if mapping is not None:
        commit = "未実装" if mapping == "未実装" else "abc1234"
        rows += [f"| 実装の対応 | {mapping} |", f"| 対応を確かめたコミット | {commit} |"]
    rows.append("| 残した回 | v1・2026-11-18・1 回目 |")
    return "\n".join(rows) + "\n"


def model_files(model: str = MODEL, broken: str = BROKEN, mapping: str | None = MAPPING) -> dict[str, str]:
    return {"README.md": readme(mapping), "Counter.tla": model, "Counter.cfg": CFG, "Broken.tla": broken, "Broken.cfg": CFG}


# コードのモデル（行為を書き直したもの）
VIOLATING = MODEL.replace("Inc ==\n  /\\ x < 2\n  /\\ x' = x + 1\n", "Inc ==\n  \\* FAKE:VIOLATE（上限の確かめを外した）\n  /\\ x' = x + 1\n")
# 1 パス目の反証: 行為の本文の注釈で行頭の性質の定義を隠し、行頭でない位置に弱めた定義を置く
COMMENT_TRICK = MODEL.replace("Inc ==\n  /\\ x < 2\n  /\\ x' = x + 1\n", "Inc ==\n  /\\ x' = x + 1 (*\n").replace(
    "Inv == x <= 2\n", "Inv == x <= 2\nReset == *)\n  Inv == x <= 100\n  Reset == x' = 0\n", 1)
# 性質が使う定義（Max）を持つモデル
MODEL_MAX = MODEL.replace("Inv == x <= 2", "Max == 2\nInv == x <= Max")
# 2 パス目の指摘: 字下げした弱めた性質と、====の後ろへ動かした元の性質
INDENT_TRICK = MODEL.replace("Inc ==\n  /\\ x < 2\n  /\\ x' = x + 1\n", "Inc == x' = x + 1\n  Inv == TRUE\n").replace(
    "Inv == x <= 2\n====\n", "====\nInv == x <= 2\n")
# 狭いパスの指摘: 行為の本文に字下げした弱めた Next・Inv と字下げした ==== を置き、行頭の本物の定義を後ろに残す
INDENTED_END = VIOLATING.replace("Reset == x' = 0\n", "Reset == x' = 0\n  Next == Inc \\/ Reset\n  Inv == TRUE\n  ====\n")
# EXTENDS した別のファイルの補助の定義（Bound）を性質が使うモデル
MODEL_EXT = MODEL.replace("EXTENDS Naturals", "EXTENDS Naturals, Helper").replace("Inv == x <= 2", "Inv == Bound(x)")
HELPER_TLA = "---- MODULE Helper ----\nEXTENDS Naturals\nBound(v) == v <= 2\n====\n"
# Init が使う補助の定義（Start）を持つモデル
MODEL_START = MODEL.replace("Init == x = 0", "Start == {0}\nInit == x \\in Start")
# SPECIFICATION 形の設定（Verifier 2 パス目の反証）
MODEL_SPEC = MODEL.replace("====\n", "Spec == Init /\\ [][Next]_x /\\ WF_x(Inc)\n====\n")
CFG_SPEC = "SPECIFICATION Spec\nINVARIANT Inv\n"
HELPER = MODEL.replace("Inc ==\n  /\\ x < 2\n  /\\ x' = x + 1\n", "Step(n) == n + 1\nInc ==\n  /\\ x < 2\n  /\\ x' = Step(x)\n")

# 計画ファイル
PLAN_HEAD = "# 計画\n\n"


def plan(*lines: str) -> str:
    return PLAN_HEAD + "".join(line + "\n" for line in lines)


# 試料: 名前 → dict
#   setup: 基準のコミットの上に重ねる {パス: 中身 | None（消す）}
#   after: base の後の変更 [(種類, パス, 中身)]——種類は commit（コミットする）・dirty（コミットしない）
#   args: 走らせる引数（{SPEC}・{BASE}・{PLAN}・{CODE} を置き換える）
#   code: 期待の終了コード・word: 出力に含む語
BASE_FILES = {"CLAUDE.md": "TLC の呼び方: {FAKE}\n", "app/counter.py": "def inc(x):\n    return x + 1\n", "app/other.py": "X = 1\n",
              **{f"{DIR1}/{k}": v for k, v in model_files().items()}}
TOUCH = [("commit", "app/counter.py", "def inc(x):\n    return x + 2\n")]
CASES: dict[str, dict] = {
    # touched
    "touched: 触れない差分": {"after": [("commit", "app/other.py", "X = 2\n")], "args": ["touched", "{BASE}", "--spec-loop", "{SPEC}"],
                         "code": 0, "word": "触れたモデルは無い"},
    "touched: コミットで触れる": {"after": TOUCH, "args": ["touched", "{BASE}", "--spec-loop", "{SPEC}"], "code": 0, "word": "触れたモデル: counter（app/counter.py）"},
    "touched: 未コミットで触れる": {"after": [("dirty", "app/counter.py", "def inc(x):\n    return x + 3\n")],
                            "args": ["touched", "{BASE}", "--spec-loop", "{SPEC}"], "code": 0, "word": "触れたモデル: counter"},
    "touched: 未追跡で触れる": {"setup": {f"{DIR1}/README.md": readme("`Inc` → `app/new.py::inc`")}, "after": [("untracked", "app/new.py", "x = 1\n")],
                           "args": ["touched", "{BASE}", "--spec-loop", "{SPEC}"], "code": 0, "word": "触れたモデル: counter（app/new.py）"},
    "touched: 対応が未実装": {"setup": {f"{DIR1}/README.md": readme("未実装")}, "after": TOUCH, "args": ["touched", "{BASE}", "--spec-loop", "{SPEC}"],
                          "code": 0, "word": "対応の無いモデル（未実装・行が無い）: counter"},
    "touched: 番号が最大の版の記録": {"setup": {f"{DIR1}/README.md": readme("未実装"), **{f"{DIR2}/{k}": v for k, v in model_files().items()}},
                              "after": TOUCH, "args": ["touched", "{BASE}", "--spec-loop", "{SPEC}"], "code": 0, "word": "docs/v2/spec/formal/counter"},
    "touched: 対応が古い": {"setup": {"app/counter.py": None}, "after": [("commit", "app/other.py", "X = 2\n")],
                         "args": ["touched", "{BASE}", "--spec-loop", "{SPEC}"], "code": 0, "word": "対応が古い: counter"},
    "touched: モデルが無い": {"setup": {f"{DIR1}/{k}": None for k in model_files()}, "after": TOUCH, "args": ["touched", "{BASE}"],
                          "code": 0, "word": "形式検査のモデルが無い"},
    "touched: spec-loop が無い": {"after": TOUCH, "args": ["touched", "{BASE}"], "code": 2, "word": "--spec-loop"},
    "touched: base が祖先でない": {"after": TOUCH, "args": ["touched", "{OTHER}", "--spec-loop", "{SPEC}"], "code": 2, "word": "HEAD の祖先でない"},
    "touched: 名前が ASCII でない": {"setup": {f"{DIR1}/README.md": readme("`Inc` → `app/注文.py::inc`"), "app/注文.py": "x = 1\n"},
                                 "after": [("commit", "app/注文.py", "x = 2\n")], "args": ["touched", "{BASE}", "--spec-loop", "{SPEC}"],
                                 "code": 0, "word": "触れたモデル: counter（app/注文.py）"},
    # check
    "check: 行が無い（受入基準 2）": {"after": TOUCH, "plan": plan(), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"],
                              "code": 1, "word": "「形式検査の再検査: counter <結果>」の行が無い"},
    "check: 反例なし": {"after": TOUCH, "plan": plan("- 形式検査の再検査: counter 反例なし"), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"],
                     "code": 0, "word": "counter（触れた対応のファイル: app/counter.py）: 反例なし"},
    "check: コードの不具合（受入基準 3）": {"after": TOUCH, "plan": plan("形式検査の再検査: counter 反例あり（コードの不具合）"),
                                  "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "コードを直して走らせ直し"},
    "check: ずれで起票の行が無い": {"after": TOUCH, "plan": plan("形式検査の再検査: counter 反例あり（モデルのずれ）"),
                             "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "そろっていない"},
    "check: ずれと起票の行": {"after": TOUCH, "plan": plan("形式検査の再検査: counter 反例あり（モデルのずれ）", "正本に起票する行: ,開発（#1）,…,A,A,…,未回答,—,確認中,",
                                                  "仕様の振る舞い: 変える"),
                          "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 0, "word": ""},
    "check: ずれで起票の行が空": {"after": TOUCH, "plan": plan("形式検査の再検査: counter 反例あり（モデルのずれ）", "正本に起票する行:", "仕様の振る舞い: 変える"),
                             "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "そろっていない"},
    "check: ずれで申告が変えない": {"after": TOUCH, "plan": plan("形式検査の再検査: counter 反例あり（モデルのずれ）", "正本に起票する行: ,開発（#1）,…", "仕様の振る舞い: 変えない"),
                               "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "そろっていない"},
    "check: 星の前置き": {"after": TOUCH, "plan": plan("* 形式検査の再検査: counter 反例なし"), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"],
                       "code": 0, "word": ": 反例なし"},
    "check: 保存したモデルを周が変える": {"after": TOUCH + [("commit", f"{DIR1}/Counter.cfg", "INIT Init\nNEXT Next\n")],
                                  "plan": plan("形式検査の再検査: counter 反例なし"), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"],
                                  "code": 1, "word": "保存したモデルのファイル docs/v1/spec/formal/counter/Counter.cfg を変えた"},
    "check: 記録の 2 行だけを進める": {"after": TOUCH + [("commit", f"{DIR1}/README.md", readme().replace("abc1234", "def5678"))],
                                "plan": plan("形式検査の再検査: counter 反例なし"), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"],
                                "code": 0, "word": ": 反例なし"},
    "check: 記録のほかの行を変える": {"after": TOUCH + [("commit", f"{DIR1}/README.md", readme().replace("| 結果 | 反例なし |", "| 結果 | 反例あり（x） |"))],
                                "plan": plan("形式検査の再検査: counter 反例なし"), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"],
                                "code": 1, "word": "のほかの行を変えた"},
    "check: 判定できなかった": {"after": TOUCH, "plan": plan("形式検査の再検査: counter 判定できなかった"),
                            "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 0, "word": "緑ではない"},
    "check: 2 本": {"after": TOUCH, "plan": plan("形式検査の再検査: counter 反例なし", "形式検査の再検査: counter 反例なし"),
                   "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "2 本ある"},
    "check: 値が違う": {"after": TOUCH, "plan": plan("形式検査の再検査: counter 確かめた"),
                     "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "どれでもない"},
    "check: フェンスの中だけ": {"after": TOUCH, "plan": plan("```text", "形式検査の再検査: counter 反例なし", "```"),
                           "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "の行が無い"},
    # 2 パス目の指摘: 対応の付け替え・モデルを消す・触れずにモデルを変える・フェンスの読み方
    "check: 対応を付け替える": {"after": TOUCH + [("commit", f"{DIR1}/README.md", readme("`Inc` → `app/other.py::inc`、`Reset` → `app/other.py::reset`"))],
                            "plan": plan(), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "「形式検査の再検査: counter <結果>」の行が無い"},
    "check: 対応の 2 行を消す": {"after": TOUCH + [("commit", f"{DIR1}/README.md", readme(None))],
                             "plan": plan(), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "「形式検査の再検査: counter <結果>」の行が無い"},
    "check: モデルを消す": {"after": TOUCH + [("commit", f"{DIR1}/{k}", None) for k in model_files()],
                         "plan": plan("形式検査の再検査: counter 反例なし"), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"],
                         "code": 1, "word": "保存したモデル docs/v1/spec/formal/counter/README.md を消した"},
    "check: 触れずに保存したモデルを変える": {"after": [("commit", "app/other.py", "X = 2\n"), ("commit", f"{DIR1}/Counter.cfg", "INIT Init\nNEXT Next\n")],
                                     "plan": plan(), "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"],
                                     "code": 1, "word": "保存したモデルのファイル docs/v1/spec/formal/counter/Counter.cfg を変えた"},
    "check: 違う印のフェンスの中": {"after": TOUCH, "plan": plan("~~~text", "```", "形式検査の再検査: counter 反例なし", "~~~"),
                               "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 1, "word": "の行が無い"},
    "check: 触れていない": {"after": [("commit", "app/other.py", "X = 2\n")], "plan": plan(),
                         "args": ["check", "{PLAN}", "{BASE}", "--spec-loop", "{SPEC}"], "code": 0, "word": "触れたモデルは無い"},
    "check: モデルが無いリポジトリ": {"setup": {f"{DIR1}/{k}": None for k in model_files()}, "after": TOUCH, "plan": plan(),
                              "args": ["check", "{PLAN}", "{BASE}"], "code": 0, "word": "何も求めない"},
    # rerun（{CODE} はコードのモデル。code_model: {名前: 中身} を保存したモデルの写しに重ねる）
    "rerun: 同じコードのモデルは反例なし": {"code_model": {}, "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"],
                                 "code": 0, "word": "形式検査の再検査: counter 反例なし"},
    "rerun: 不変条件を破る行為（受入基準 3）": {"code_model": {"Counter.tla": VIOLATING}, "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"],
                                    "code": 1, "word": "形式検査の再検査: counter 反例あり（コードの不具合）"},
    "rerun: 意図した変更": {"code_model": {"Counter.tla": VIOLATING}, "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}", "--intended"],
                         "code": 1, "word": "形式検査の再検査: counter 反例あり（モデルのずれ）"},
    "rerun: 定義を足して行為を書き直す": {"code_model": {"Counter.tla": HELPER}, "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"],
                                "code": 0, "word": "counter 反例なし"},
    "rerun: 設定を変える": {"code_model": {"Counter.cfg": "INIT Init\nNEXT Next\n"}, "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"],
                         "code": 4, "word": "Counter.cfg が保存したモデルと違う"},
    "rerun: 性質を弱める": {"code_model": {"Counter.tla": VIOLATING.replace("Inv == x <= 2", "Inv == TRUE")},
                         "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Inv」が保存したモデルと違う"},
    "rerun: Init を変える": {"code_model": {"Counter.tla": MODEL.replace("Init == x = 0", "Init == FALSE")},
                          "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Init」が保存したモデルと違う"},
    "rerun: 陽性対照を変える": {"code_model": {"Broken.tla": "---- MODULE Broken ----\n\\* FAKE:PASS\n====\n"},
                            "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "Broken.tla が保存したモデルと違う"},
    "rerun: 定義の外の行を変える": {"code_model": {"Counter.tla": MODEL.replace("VARIABLE x", "VARIABLE x, y")},
                              "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義の外の行"},
    "rerun: 定義を消す": {"code_model": {"Counter.tla": MODEL.replace("Reset == x' = 0\n", "")},
                        "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Reset」が消えた"},
    "rerun: 記録の一覧を変える": {"code_model": {"README.md": readme(controls="`Counter.tla`・`Counter.cfg`")},
                             "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "記録の「陽性対照のファイル」が保存したモデルと違う"},
    "rerun: 注釈で性質を隠す（1 パス目の反証）": {"code_model": {"Counter.tla": COMMENT_TRICK},
                                       "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Inv」が消えた"},
    "rerun: 対応に性質を挙げて書き直す": {"setup": {f"{DIR1}/README.md": readme(MAPPING + "、`Inv` → `app/counter.py::inc`")},
                                  "code_model": {"Counter.tla": VIOLATING.replace("Inv == x <= 2", "Inv == TRUE")},
                                  "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Inv」は設定（.cfg）が名指すか"},
    "rerun: 性質が使う定義を対応に挙げて書き直す": {"setup": {f"{DIR1}/README.md": readme(MAPPING + "、`Max` → `app/counter.py::inc`"), f"{DIR1}/Counter.tla": MODEL_MAX},
                                         "code_model": {"Counter.tla": MODEL_MAX.replace("Max == 2", "Max == 100")},
                                         "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Max」は設定（.cfg）が名指すか"},
    # 2 パス目の指摘
    "rerun: 字下げと ==== の後ろで性質を差し替える": {"code_model": {"Counter.tla": INDENT_TRICK},
                                          "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Inv」が消えた"},
    "rerun: 字下げした ==== で後ろの本物の定義を隠す（狭いパスの指摘）": {"code_model": {"Counter.tla": INDENTED_END}, "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"],
                                                  "code": 4, "word": "より後ろが保存したモデルと違う"},
    "rerun: ==== の後ろを変える": {"code_model": {"Counter.tla": MODEL + "Inv == TRUE\n"},
                               "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "より後ろが保存したモデルと違う"},
    "rerun: EXTENDS した補助の定義を対応に挙げて書き直す": {
        "setup": {f"{DIR1}/README.md": readme(MAPPING + "、`Bound` → `app/counter.py::inc`", models="`Counter.tla`・`Counter.cfg`・`Helper.tla`"),
                  f"{DIR1}/Counter.tla": MODEL_EXT, f"{DIR1}/Helper.tla": HELPER_TLA},
        "code_model": {"Helper.tla": HELPER_TLA.replace("Bound(v) == v <= 2", "Bound(v) == TRUE")},
        "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Bound」は設定（.cfg）が名指すか"},
    "rerun: Init が使う補助の定義を対応に挙げて書き直す": {
        "setup": {f"{DIR1}/README.md": readme(MAPPING + "、`Start` → `app/counter.py::inc`"), f"{DIR1}/Counter.tla": MODEL_START},
        "code_model": {"Counter.tla": MODEL_START.replace("Start == {0}", "Start == {}")},
        "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Start」は設定（.cfg）が名指すか"},
    "rerun: SPECIFICATION 形で Next を対応に挙げて書き直す": {
        "setup": {f"{DIR1}/README.md": readme(MAPPING + "、`Next` → `app/counter.py::step`"), f"{DIR1}/Counter.tla": MODEL_SPEC, f"{DIR1}/Counter.cfg": CFG_SPEC},
        "code_model": {"Counter.tla": MODEL_SPEC.replace("Next == Inc \\/ Reset", "Next == UNCHANGED x")},
        "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "定義「Next」は設定（.cfg）が名指すか"},
    "rerun: SPECIFICATION 形で公平性の行為を書き直す": {
        "setup": {f"{DIR1}/Counter.tla": MODEL_SPEC, f"{DIR1}/Counter.cfg": CFG_SPEC},
        "code_model": {"Counter.tla": MODEL_SPEC.replace("Inc ==\n  /\\ x < 2\n  /\\ x' = x + 1\n", "Step(n) == n + 1\nInc ==\n  /\\ x < 2\n  /\\ x' = Step(x)\n")},
        "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 0, "word": "counter 反例なし"},
    "rerun: 番号が最大の版でない記録を渡す": {"setup": {**{f"{DIR2}/{k}": v for k, v in model_files().items()}}, "code_model": {},
                                    "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 2, "word": "番号が最大の版）でない"},
    "rerun: 保存したモデルが反例を出す": {"setup": {f"{DIR1}/Counter.tla": MODEL.replace("FAKE:PASS", "FAKE:VIOLATE")}, "code_model": {},
                                "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "比べる基準が壊れている"},
    "rerun: 保存したモデルが空振り": {"setup": {f"{DIR1}/Broken.tla": "---- MODULE Broken ----\n\\* FAKE:PASS\n====\n"}, "code_model": {},
                               "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "空振りの疑い"},
    "rerun: 呼び方の行が無い": {"setup": {"CLAUDE.md": "# 正本\n"}, "code_model": {},
                            "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 4, "word": "counter 判定できなかった"},
    "rerun: 対応の無いモデル": {"setup": {f"{DIR1}/README.md": readme("未実装")}, "code_model": {},
                            "args": ["rerun", DIR1, "--code-model", "{CODE}", "--spec-loop", "{SPEC}"], "code": 2, "word": "実装の対応が無い"},
}

# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("未追跡を数えない", '    names += git("ls-files", "--others", "--exclude-standard", "-z").split("\\0")\n', "", "touched: 未追跡で触れる"),
    ("3 点の差分にする", 'names = git("diff", "--name-only", "--no-renames", "-z", base).split("\\0")',
     'names = git("diff", "--name-only", "--no-renames", "-z", f"{base}...HEAD").split("\\0")', "touched: 未コミットで触れる"),
    ("最小の版を読む", "if target.name not in found or found[target.name][0] < number:", "if target.name not in found:", "touched: 番号が最大の版の記録"),
    ("祖先を確かめない", '    if subprocess.run(["git", "merge-base", "--is-ancestor", base, "HEAD"], capture_output=True).returncode != 0:\n',
     "    if False:\n", "touched: base が祖先でない"),
    ("行が無いのを通す", '            problems.append(f"{where}: 計画に「{LINE_KEY} {name} <結果>」', '            lines.append(f"{where}: 計画に「{LINE_KEY} {name} <結果>」',
     "check: 行が無い（受入基準 2）"),
    ("コードの不具合を通す", "        elif results[0] == CODE_BUG:\n", "        elif False:\n", "check: コードの不具合（受入基準 3）"),
    ("ずれに起票の行を求めない", "        elif results[0] == MODEL_DRIFT and not writeback:\n", "        elif False:\n", "check: ずれで起票の行が無い"),
    ("2 本を通す", "        elif len(results) > 1:\n", "        elif False:\n", "check: 2 本"),
    ("値を見ない", "        elif results[0] not in RESULTS:\n", "        elif False:\n", "check: 値が違う"),
    ("フェンスの中も数える", "        if fence is not None:\n            continue\n", "", "check: フェンスの中だけ"),
    ("反例を既定でずれにする", "                result = MODEL_DRIFT if intended else CODE_BUG\n", "                result = MODEL_DRIFT\n",
     "rerun: 不変条件を破る行為（受入基準 3）"),
    ("反例を反例なしと読む", "            if code_verdict == module.PASS:\n", "            if code_verdict != module.UNKNOWN:\n", "rerun: 不変条件を破る行為（受入基準 3）"),
    ("弱めたのを見ない", "    if problems:\n        lines += [f\"弱めた違い:", "    if False:\n        lines += [f\"弱めた違い:", "rerun: 性質を弱める"),
    ("行為でない定義の書き直しを通す", "            elif definition not in actions and code_defs[definition] != body:\n", "            elif False:\n", "rerun: Init を変える"),
    ("行為の書き直しも止める", "            elif definition not in actions and code_defs[definition] != body:\n",
     "            elif code_defs[definition] != body:\n", "rerun: 不変条件を破る行為（受入基準 3）"),
    ("設定と陽性対照のバイトを見ない", "            if a.read_bytes() != b.read_bytes():\n", "            if False:\n", "rerun: 陽性対照を変える"),
    ("定義の外の行を見ない", "        if saved_others != code_others:\n", "        if False:\n", "rerun: 定義の外の行を変える"),
    ("消えた定義を通す", "            if definition not in code_defs:\n                problems.append", "            if False:\n                problems.append",
     "rerun: 定義を消す"),
    ("記録の一覧を比べない", "        if code_records.get(item) != saved_records.get(item):\n", "        if False:\n", "rerun: 記録の一覧を変える"),
    ("保存したモデルを確かめない", "        if saved_verdict != module.PASS:\n", "        if False:\n", "rerun: 保存したモデルが反例を出す"),
    # 1 パス目の指摘対応
    ("注釈を除かない", 'code_head, code_tail = module_end(module.baseline.strip_comments(b.read_text(encoding="utf-8")))',
     'code_head, code_tail = module_end(b.read_text(encoding="utf-8"))', "rerun: 注釈で性質を隠す（1 パス目の反証）"),
    ("設定が名指す行為の書き直しを通す", "    protected = roots | closure(everything, roots - steps) | closure(everything, steps | spec_direct, stop=actions)  #",
     "    protected = set()  #", "rerun: 対応に性質を挙げて書き直す"),
    ("性質が使う定義をたどらない", "    protected = roots | closure(everything, roots - steps) | closure(everything, steps | spec_direct, stop=actions)  #",
     "    protected = roots  #", "rerun: 性質が使う定義を対応に挙げて書き直す"),
    ("Spec が直に使う定義を守らない", "    spec_direct = {n for spec in specs if spec in everything", "    spec_direct = {n for spec in set() if spec in everything", "rerun: SPECIFICATION 形で Next を対応に挙げて書き直す"),
    ("Spec から行為で止めない", "closure(everything, steps | spec_direct, stop=actions)", "closure(everything, steps | spec_direct)",
     "rerun: SPECIFICATION 形で公平性の行為を書き直す"),
    ("-z を外す", 'names = git("diff", "--name-only", "--no-renames", "-z", base).split("\\0")',
     'names = git("diff", "--name-only", "--no-renames", base).split("\\n")', "touched: 名前が ASCII でない"),
    ("古い版の記録を通す", "    if target.name not in models or models[target.name].resolve() != target.resolve():\n",
     "    if target.name not in models:\n", "rerun: 番号が最大の版でない記録を渡す"),
    ("保存したモデルの変更を見ない", "    problems = saved_model_changes(base, canon)  #", "    problems = []  #", "check: 保存したモデルを周が変える"),
    ("記録のほかの行を見ない", "            elif not readme_rows_kept(base, path, root / path):\n", "            elif False:\n", "check: 記録のほかの行を変える"),
    ("空の起票の行を数える", "        if w and w.group(1):\n", "        if w:\n", "check: ずれで起票の行が空"),
    ("申告を見ない", '    return found, bool(rows) and declares == ["変える"]\n', "    return found, bool(rows)\n", "check: ずれで申告が変えない"),
    ("星の前置きを読まない", r'PLAN_LINE = re.compile(r"^(?:[-*]\s+)?"', r'PLAN_LINE = re.compile(r"^(?:- )?"', "check: 星の前置き"),
    ("新しい定義を止める", '                    raise Unjudged(f"定義「{current}」が 2 つある")\n                definitions[current] = line + "\\n"\n',
     '                    raise Unjudged(f"定義「{current}」が 2 つある")\n                definitions[current] = line + "\\n"\n                others.append("新しい定義")\n',
     "rerun: 定義を足して行為を書き直す"),
    # 2 パス目の指摘対応
    ("モジュールの終わりを読まない", 'MODULE_END = re.compile(r"^[ \\t]*={4,}[ \\t]*$", re.MULTILINE)', 'MODULE_END = re.compile(r"(?!)")',
     "rerun: 字下げと ==== の後ろで性質を差し替える"),
    ("字下げした ==== を終わりと読まない", 'MODULE_END = re.compile(r"^[ \\t]*={4,}', 'MODULE_END = re.compile(r"^={4,}', "rerun: 字下げした ==== で後ろの本物の定義を隠す（狭いパスの指摘）"),
    ("==== の後ろを比べない", "        if saved_tail.strip() != code_tail.strip():\n", "        if False:\n", "rerun: ==== の後ろを変える"),
    ("別のファイルの定義をたどらない", "    for _, saved_defs, _, _, _ in parsed:\n        for definition, body in saved_defs.items():\n",
     "    for _, saved_defs, _, _, _ in parsed[:1]:\n        for definition, body in saved_defs.items():\n", "rerun: EXTENDS した補助の定義を対応に挙げて書き直す"),
    ("INIT からたどらない", "closure(everything, roots - steps)", "closure(everything, roots - steps - {'Init'})", "rerun: Init が使う補助の定義を対応に挙げて書き直す"),

    ("base の時点の対応を読まない", "            entries += mapping(module, root / at_base[name], base_records(module, base, at_base[name]))\n", "",
     "check: 対応を付け替える"),
    ("base の時点のモデルを数えない", "    for name, rel in sorted(set(now.items()) | set(at_base.items())):\n", "    for name, rel in sorted(set(now.items())):\n",
     "check: モデルを消す"),
    ("触れていなければ保存したモデルを見ない", "        return (1, notes + problems) if problems else (0, notes)\n", "        return 0, notes\n",
     "check: 触れずに保存したモデルを変える"),
    ("どの印でもフェンスを閉じる", "            elif mark[0] == fence[0] and len(mark) >= len(fence) and not line.strip()[len(mark):].strip():\n", "            else:\n",
     "check: 違う印のフェンスの中"),
]


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name}{(': ' + detail) if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    tmp = Path(tempfile.gettempdir()).resolve()
    check(f"試料が一時ディレクトリの中: {path}", tmp in path.resolve().parents)


def sandbox_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_DATE="2026-01-01T00:00:00Z", GIT_COMMITTER_DATE="2026-01-01T00:00:00Z")
    return env


def git(repo: Path, env: dict[str, str], *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", *args],
                          check=True, capture_output=True, text=True, env=env).stdout.strip()


def write(path: Path, body: str | None) -> None:
    if body is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def run_case(body: Path, spec: Path, work: Path, fake: Path, env: dict[str, str], case: dict) -> tuple[int, str]:
    if work.exists():
        shutil.rmtree(work)
    repo = work / "repo"
    repo.mkdir(parents=True)
    assert_in_tmp(repo)
    git(repo, env, "init", "-q", "-b", "main")
    files = {**BASE_FILES, **case.get("setup", {})}
    for rel, text in files.items():
        write(repo / rel, None if text is None else text.replace("{FAKE}", str(fake)))
    git(repo, env, "add", "-A")
    git(repo, env, "commit", "-q", "-m", "base")
    base = git(repo, env, "rev-parse", "HEAD")
    git(repo, env, "checkout", "-q", "-b", "other")
    write(repo / "app/side.py", "S = 1\n")
    git(repo, env, "add", "-A")
    git(repo, env, "commit", "-q", "-m", "other")
    other = git(repo, env, "rev-parse", "HEAD")
    git(repo, env, "checkout", "-q", "main")
    for kind, rel, text in case.get("after", []):
        write(repo / rel, text)
        if kind == "commit":
            git(repo, env, "add", "-A")
            git(repo, env, "commit", "-q", "-m", "change")
    plan_path = work / "plan.md"
    plan_path.write_text(case.get("plan", plan()), encoding="utf-8")
    code_dir = work / "code-model" / "counter"
    if "code_model" in case:
        shutil.copytree(repo / DIR1, code_dir)
        for name, text in case["code_model"].items():
            write(code_dir / name, text)
    args = [a.replace("{SPEC}", str(spec)).replace("{BASE}", base).replace("{OTHER}", other).replace("{PLAN}", str(plan_path)).replace("{CODE}", str(code_dir))
            for a in case["args"]]
    before = git(repo, env, "status", "--porcelain")
    proc = subprocess.run([sys.executable, "-I", str(body), *args], capture_output=True, text=True, cwd=repo, env=env, timeout=120)
    after = git(repo, env, "status", "--porcelain")
    check("走らせても実装のリポジトリを変えない", before == after, f"{before!r} → {after!r}")
    check("正本に states/ を残さない", not any(p.name == "states" for p in (repo / "docs").rglob("*")) if (repo / "docs").exists() else True)
    return proc.returncode, proc.stdout + proc.stderr


def as_expected(case: dict, result: tuple[int, str]) -> bool:
    return result[0] == case["code"] and case["word"] in result[1] and "Traceback" not in result[1]


def main() -> int:
    source = BODY.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="formal-sync-test-") as tmp:
        root = Path(tmp)
        home = root / "home"
        home.mkdir()
        env = sandbox_env(home)
        spec = root / "spec-loop"
        shutil.copytree(SPEC_LOOP_SCRIPTS, spec / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        body = root / "dev-loop" / "formal-sync.py"
        body.parent.mkdir()
        shutil.copyfile(BODY, body)
        fake = root / "fake-tlc"
        fake.write_text(FAKE_TLC, encoding="utf-8")
        fake.chmod(0o755)
        print("試料")
        for i, (name, case) in enumerate(CASES.items()):
            result = run_case(body, spec, root / f"c{i}", fake, env, case)
            check(f"試料: {name}", as_expected(case, result), f"期待 {case['code']}・{case['word']!r} / 実際 {result[0]}・{result[1][-500:]!r}")
        print(f"  {len(CASES)} 件 OK")
        print("変異テスト")
        for name, before, after, killer in MUTATIONS:
            check(f"壊す箇所がちょうど 1 回: {name}", source.count(before) == 1, f"{source.count(before)} 回: {before!r}")
            mutated = root / "mutated" / "formal-sync.py"
            mutated.parent.mkdir(exist_ok=True)
            mutated.write_text(source.replace(before, after), encoding="utf-8")
            case = CASES[killer]
            check(f"変異の前は期待どおり: {name}", as_expected(case, run_case(body, spec, root / "orig", fake, env, case)))
            result = run_case(mutated, spec, root / "mut", fake, env, case)
            check(f"変異を殺す: {name} ← {killer}", not as_expected(case, result), f"{result[0]} {result[1][-300:]!r}")
        print(f"  変異 {len(MUTATIONS)} 件 OK")
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
