#!/usr/bin/env python3
"""`merge-versions.py`（版ごとのディレクトリの重ね合わせ）の回帰テスト。

    python3 scripts/test-merge-versions.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。

見るもの:

1. **決まりどおりに重なる**——ファイル・`qa.csv` の行・機能・トップレベルのキーの追加と置き換え、3 種類の削除、
   3 つ以上の版、`--upto`。**置き換えは前の版の順の位置に入る**（末尾に回さない）。
2. **重ねないもの**——`feasibility/`・`proposal/`・`.` で始まる名前・版でない名前（`videos/`・`index.md`）。
3. **決まりに反する入力からは作らない（1）**——版の欠番・形に合わない版名（ファイルでも）・シンボリックリンク
   （版・置き場所・ファイル・`removed.csv`）・`qa.csv` の決まり違反・機能の `id` の重複と欠落・`removed.csv` の誤り・
   重ねた結果のファイルとディレクトリの衝突・大文字小文字や Unicode の正規化だけが違うパス・UTF-8 で書けない文字。
   **前に作った出力は消す。** **入力が無い・読めない（2）ときも消す。**
4. **正本を消さない（2）**——印の無い空でない出力先・シンボリックリンクの出力先・`docs/` の中・`docs/` そのもの・
   `docs/` を含む場所には書かない。**中身は触らない。**
5. **同じ入力から同じバイト**——2 回作って一致。**陽性対照として、入力を 1 字変えると出力が変わる。**
   **2 回続けて作るだけでは、日付のように粒の粗い時刻を捕まえない**ので、出力の全バイト（印を含む）を期待値と突き合わせる。
8. **書いている途中で失敗したら、書きかけを残さない**——書き込みの口（`put`）を差し替えて 2 つ目で失敗させる。
   用意された空の出力先は消さない（印を書きかけて失敗しても、直下に書きかけを残さない）。**途中で落ちても（後始末が走らなくても）印は無い。**
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。
7. **決まりの写しがずれていない**——本体の定数が `references/versions.md` と一致する。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**読めない入力の試料は root では作れない**（root は mode 000 でも読める）。root で走らせたときは、その試料と
それを名指しした変異を飛ばし、**飛ばしたことを出力に書く**（緑のふりをしない）。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
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
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "merge-versions.py"
REFERENCE = PLUGIN / "references" / "versions.md"

QA_HEAD = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
Q1 = "Q-001,要求確定,質問1,A: 甲 / B: 乙,A（業務部が回答）,決定表 1 行目,反映済み,\n"
Q2 = "Q-002,要求確定,質問2,A: 甲 / B: 乙,未回答,—,確認中,\n"
Q2B = "Q-002,要求確定,質問2,A: 甲 / B: 乙,B（業務部が回答）,決定表 2 行目,反映済み,\n"
Q3 = "Q-003,開発,質問3,A: 甲 / B: 乙,未回答,—,確認中,\n"
BAD_QA = "Q-004,要求確定,質問4,A: 甲 / B: 乙,未回答,—,保留,\n"  # 状態が決まりに無い

SPEC1 = {"spec_ir_version": 1, "title": "注文", "features": [
    {"id": "F-001", "title": "割引", "cases": [{"id": "F-001-C1"}]},
    {"id": "F-002", "title": "送料"}]}
# v2 は差分だけ。並びを v1 と逆にして、置き換えが前の版の位置に入ることを見る
SPEC2 = {"title": "注文 v2", "features": [{"id": "F-003", "title": "ポイント"}, {"id": "F-002", "title": "送料 v2"}]}
REMOVED_HEAD = "種類,対象,理由\n"
# 入力の木の特別な値: シンボリックリンク（版の外のファイル／ディレクトリへ）と、読めないファイル／ディレクトリ
LINK, LINK_DIR, UNREADABLE, UNREADABLE_DIR = None, "\0link-dir", "\0unreadable", "\0unreadable-dir"
UNREADABLE_CASES = {"読めないファイル", "読めないディレクトリ"}


def js(data) -> str:
    return json.dumps(data, ensure_ascii=False)


V1 = {
    "v1/shared/qa.csv": QA_HEAD + Q1 + Q2,
    "v1/shared/decision_table.csv": "決定表 v1\n",
    "v1/requirements/a.md": "A1\n",
    "v1/requirements/b.md": "B1\n",
    "v1/spec/order.md": "仕様 v1\n",
    "v1/spec/spec_ir.json": js(SPEC1),
    "v1/feasibility/estimate.csv": "見積り v1\n",
    "v1/proposal/01-background.md": "背景\n",
}
V2 = {
    "v2/shared/qa.csv": QA_HEAD + Q3 + Q2B,
    "v2/requirements/a.md": "A2\n",
    "v2/requirements/c.md": "C2\n",
    "v2/spec/spec_ir.json": js(SPEC2),
    "v2/removed.csv": REMOVED_HEAD + "ファイル,requirements/b.md,要件から外した\n",
    "v2/feasibility/estimate.csv": "見積り v2\n",
}
MAIN = {**V1, **V2}
NFC, NFD = "\u30ac\u30a4\u30c9.md", "\u30ab\u3099\u30a4\u30c8\u3099.md"  # ガイド.md の NFC と NFD
# MAIN を重ねた出力の全バイト（印を含む）。2 回作って比べるだけでは日付のような時刻を捕まえないので、値で突き合わせる
GOLDEN = {
    ".merged-versions": "merge-versions.py が作った。手で直さない\n".encode("utf-8"),
    "requirements/a.md": b"A2\n",
    "requirements/c.md": b"C2\n",
    "shared/decision_table.csv": "決定表 v1\n".encode("utf-8"),
    "shared/qa.csv": (QA_HEAD + Q1 + Q2B + Q3).encode("utf-8"),
    "spec/order.md": "仕様 v1\n".encode("utf-8"),
    "spec/spec_ir.json": (json.dumps({"spec_ir_version": 1, "title": "注文 v2", "features": [
        SPEC1["features"][0], {"id": "F-002", "title": "送料 v2"}, {"id": "F-003", "title": "ポイント"}]},
        ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
}


def with_removed(*rows: str) -> dict[str, str]:
    return {**MAIN, "v2/removed.csv": REMOVED_HEAD + "".join(rows)}


class Result:
    def __init__(self, code: int, output: str, tree: dict[str, bytes] | None, preexisting: str | None = None,
                 again: dict[str, bytes] | None = None, docs_intact: bool = True, leftover: list[str] | None = None):
        self.code, self.output, self.tree, self.preexisting, self.again = code, output, tree, preexisting, again
        self.docs_intact, self.leftover = docs_intact, leftover

    def text(self, path: str) -> str | None:
        return self.tree[path].decode("utf-8") if self.tree and path in self.tree else None

    def qa_numbers(self) -> list[str]:
        return [line.split(",")[0] for line in self.text("shared/qa.csv").splitlines()[1:]]

    def spec(self) -> dict:
        return json.loads(self.text("spec/spec_ir.json"))

    def feature_ids(self) -> list[str]:
        return [f["id"] for f in self.spec()["features"]]


def made(r: Result) -> bool:
    return r.code == 0 and r.tree is not None


def refused(r: Result, message: str) -> bool:
    return r.code == 1 and r.tree is None and message in r.output and "重ね合わせは作っていない" in r.output


def main_case(r: Result) -> bool:
    return (made(r)
            and r.text("requirements/a.md") == "A2\n"          # 変更
            and r.text("requirements/c.md") == "C2\n"          # 追加
            and "requirements/b.md" not in r.tree              # 削除
            and r.text("shared/decision_table.csv") == "決定表 v1\n"  # 変えていない
            and r.text("spec/order.md") == "仕様 v1\n"
            and r.qa_numbers() == ["Q-001", "Q-002", "Q-003"]  # 置き換えは前の位置に・追加は末尾
            and "B（業務部が回答）" in r.text("shared/qa.csv")
            and r.feature_ids() == ["F-001", "F-002", "F-003"]
            and r.spec()["features"][1]["title"] == "送料 v2"
            and r.spec()["title"] == "注文 v2" and r.spec()["spec_ir_version"] == 1
            and not any(p.startswith(("feasibility/", "proposal/")) for p in r.tree)
            and "removed.csv" not in r.tree)


# (名前, 入力の木（パス → 中身。None ならシンボリックリンクを作る）, 出力先の準備, 引数, 判定)
# 出力先の準備: "none"（無い）／"stale"（印つきの前の出力）／"foreign"（印の無い正本らしきもの）／"inside"（docs の中）
# ／"docs"（docs そのもの）／"parent"（docs を含む、印つきの場所）／"symlink"（空のディレクトリへのシンボリックリンク）
# ／"failwrite"（無い出力先に、2 つ目の書き込みで失敗する）／"failwrite-empty"（用意された空の出力先に、同上）
# ／"crash"（2 つ目の書き込みで後始末の走らない落ち方をする）
# ／"marker-empty"（用意された空の出力先に、印を書きかけたところで失敗する）
# 入力の木が None なら docs を作らない
CASES: list[tuple[str, dict, str, list[str], Callable[[Result], bool]]] = [
    ("全部の経路を重ねる", MAIN, "none", [], main_case),
    ("Q&A を消す", with_removed("Q&A,Q-001,質問を取り下げた\n"), "none", [],
     lambda r: made(r) and r.qa_numbers() == ["Q-002", "Q-003"]),
    ("機能を消す", with_removed("機能,F-001,機能を外した\n"), "none", [],
     lambda r: made(r) and r.feature_ids() == ["F-002", "F-003"]),
    ("3 つ目の版を順に重ねる", {**MAIN, "v3/requirements/a.md": "A3\n", "v3/requirements/b.md": "B3\n"}, "none", [],
     lambda r: made(r) and r.text("requirements/a.md") == "A3\n" and r.text("requirements/b.md") == "B3\n"),
    ("--upto 1 は v1 だけ", MAIN, "none", ["--upto", "1"],
     lambda r: made(r) and r.text("requirements/a.md") == "A1\n" and r.text("requirements/b.md") == "B1\n"
     and r.qa_numbers() == ["Q-001", "Q-002"] and r.feature_ids() == ["F-001", "F-002"] and r.spec()["title"] == "注文"),
    ("--upto が版を越える", MAIN, "none", ["--upto", "3"], lambda r: r.code == 2 and r.tree is None),
    ("版でない名前は読まない", {**MAIN, "videos/x.md": "動画\n", "index.md": "# サイト\n"}, "none", [], main_case),
    ("ドットで始まる名前は読まない", {**MAIN, "v2/requirements/.DS_Store": "x"}, "none", [],
     lambda r: made(r) and not any(".DS_Store" in p for p in r.tree)),
    ("版の欠番", {**V1, "v3/requirements/a.md": "A3\n"}, "none", [], lambda r: refused(r, "v2 が無い")),
    ("形に合わない版名", {**MAIN, "v2-draft/requirements/a.md": "x\n"}, "none", [], lambda r: refused(r, "版の名前の形")),
    ("先頭に 0 の付いた版名", {**MAIN, "v02/requirements/a.md": "x\n"}, "none", [], lambda r: refused(r, "版の名前の形")),
    ("版が 1 つも無い", {"index.md": "# サイト\n"}, "none", [], lambda r: refused(r, "版（v1 など）が 1 つも無い")),
    ("シンボリックリンク", {**MAIN, "v2/requirements/link.md": None}, "none", [], lambda r: refused(r, "シンボリックリンク")),
    ("qa.csv の決まり違反", {**MAIN, "v2/shared/qa.csv": QA_HEAD + BAD_QA}, "none", [], lambda r: refused(r, "保留")),
    ("機能の id の重複", {**MAIN, "v2/spec/spec_ir.json": js({"features": [{"id": "F-003"}, {"id": "F-003"}]})},
     "none", [], lambda r: refused(r, "版の中で重複")),
    ("機能に id が無い", {**MAIN, "v2/spec/spec_ir.json": js({"features": [{"title": "x"}]})}, "none", [],
     lambda r: refused(r, "`id`（文字列）が無い")),
    ("features が配列でない", {**MAIN, "v2/spec/spec_ir.json": js({"title": "x"})}, "none", [],
     lambda r: refused(r, "`features` が配列でない")),
    ("消す種類が決まりに無い", with_removed("画面,requirements/b.md,x\n"), "none", [], lambda r: refused(r, "`種類` が")),
    ("無いものを消す", with_removed("ファイル,requirements/z.md,x\n"), "none", [], lambda r: refused(r, "前の版までに無いもの")),
    ("置きつつ消す", with_removed("ファイル,requirements/a.md,x\n"), "none", [], lambda r: refused(r, "置きつつ消している")),
    ("同じ対象を 2 度消す", with_removed("Q&A,Q-001,x\n", "Q&A,Q-001,y\n"), "none", [], lambda r: refused(r, "2 度消す")),
    ("構造ファイルをファイルとして消す", with_removed("ファイル,shared/qa.csv,x\n"), "none", [],
     lambda r: refused(r, "ファイルとしては消せない")),
    ("理由が空", with_removed("ファイル,requirements/b.md,\n"), "none", [], lambda r: refused(r, "`理由` が空")),
    ("removed.csv の見出し違い", {**MAIN, "v2/removed.csv": "種類,対象\nファイル,requirements/b.md\n"}, "none", [],
     lambda r: refused(r, "見出し行が決まりと違う")),
    ("v1 に removed.csv", {**MAIN, "v1/removed.csv": REMOVED_HEAD + "ファイル,requirements/a.md,x\n"}, "none", [],
     lambda r: refused(r, "v1 には置かない")),
    ("前の出力を消す", {**MAIN, "v2/removed.csv": REMOVED_HEAD + "画面,x,y\n"}, "stale", [],
     lambda r: refused(r, "前に作った出力を消した")),
    ("前の出力の中身を残さない", MAIN, "stale", [], lambda r: main_case(r) and "old.md" not in r.tree),
    ("印の無い場所には書かない", MAIN, "foreign", [],
     lambda r: r.code == 2 and "印" in r.output and r.preexisting == "正本\n"),
    ("docs の中には書かない", MAIN, "inside", [], lambda r: r.code == 2 and "の中には書かない" in r.output),
    ("docs そのものには書かない", MAIN, "docs", [],
     lambda r: r.code == 2 and "の中には書かない" in r.output and r.docs_intact),
    ("docs を含む場所には書かない", MAIN, "parent", [],
     lambda r: r.code == 2 and "を含む場所には書かない" in r.output and r.docs_intact),
    ("出力先のシンボリックリンクには書かない", MAIN, "symlink", [],
     lambda r: r.code == 2 and "シンボリックリンクは使わない" in r.output),
    ("入力が無いと前の出力を消す", None, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "前に作った出力を消した" in r.output),
    ("読めないファイル", {**MAIN, "v2/requirements/d.md": UNREADABLE}, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "読めない" in r.output and "前に作った出力を消した" in r.output),
    ("読めないディレクトリ", {**MAIN, "v2/requirements/sub": UNREADABLE_DIR}, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "読めない" in r.output and "前に作った出力を消した" in r.output),
    ("ファイルの形の版名", {**MAIN, "v3.md": "x\n"}, "none", [], lambda r: refused(r, "版の名前の形")),
    ("版がシンボリックリンク", {**MAIN, "v3": LINK_DIR}, "none", [], lambda r: refused(r, "版はディレクトリで置く")),
    ("置き場所がシンボリックリンク", {**V1, "v2/requirements": LINK_DIR}, "none", [],
     lambda r: refused(r, "シンボリックリンク")),
    ("removed.csv がシンボリックリンク", {**MAIN, "v2/removed.csv": LINK}, "none", [],
     lambda r: refused(r, "シンボリックリンク")),
    ("ファイルとディレクトリの衝突", {**V1, "v2/requirements/b.md/x.md": "x\n"}, "none", [],
     lambda r: refused(r, "ファイルとディレクトリの両方")),
    ("衝突を削除で解く", {**V1, "v2/requirements/b.md/x.md": "x\n",
                       "v2/removed.csv": REMOVED_HEAD + "ファイル,requirements/b.md,ディレクトリに分けた\n"}, "none", [],
     lambda r: made(r) and r.text("requirements/b.md/x.md") == "x\n"),
    ("Q&A が全部消えても qa.csv を書く",
     {**V1, "v2/removed.csv": REMOVED_HEAD + "Q&A,Q-001,取り下げ\nQ&A,Q-002,取り下げ\n"}, "none", [],
     lambda r: made(r) and r.text("shared/qa.csv") == QA_HEAD),
    ("出力のバイトが決まっている", MAIN, "none", [], lambda r: made(r) and r.tree == GOLDEN),
    ("大文字小文字だけ違うパス", {**V1, "v2/requirements/A.md": "x\n"}, "stale", [],
     lambda r: refused(r, "正規化だけ違う") and "前に作った出力を消した" in r.output),
    ("正規化だけ違うパス", {**V1, "v1/requirements/" + NFC: "nfc\n", "v2/requirements/" + NFD: "nfd\n"}, "none", [],
     lambda r: refused(r, "正規化だけ違う")),
    ("大文字小文字だけ違うファイルとディレクトリ", {**V1, "v2/requirements/B.md/x.md": "x\n"}, "none", [],
     lambda r: refused(r, "ファイルとディレクトリの両方")),
    ("UTF-8 で書けない文字", {**MAIN, "v2/spec/spec_ir.json": '{"title": "\\ud800", "features": []}'}, "stale", [],
     lambda r: refused(r, "UTF-8 で書けない") and "前に作った出力を消した" in r.output),
    ("書いている途中で失敗したら書きかけを消す", MAIN, "failwrite", [],
     lambda r: r.code == 2 and "書きかけを消した" in r.output and r.leftover is None),
    ("用意した空の出力先は失敗しても消さない", MAIN, "failwrite-empty", [],
     lambda r: r.code == 2 and r.leftover == []),
    ("印を書きかけて失敗しても直下に残さない", MAIN, "marker-empty", [],
     lambda r: r.code == 2 and r.leftover == []),
    ("大文字の V は版でない", {**MAIN, "V3/requirements/a.md": "x\n"}, "none", [], main_case),
    ("途中で落ちても印は無い", MAIN, "crash", [],
     lambda r: r.code != 0 and r.leftover is not None and ".merged-versions" not in r.leftover),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("Q&A の置き換えを末尾に回す", '            self.qa[row["No"]] = row\n',
     '            self.qa.pop(row["No"], None)\n            self.qa[row["No"]] = row\n', "全部の経路を重ねる"),
    ("機能の置き換えを末尾に回す", '                self.features[feature["id"]] = feature\n',
     '                self.features.pop(feature["id"], None)\n                self.features[feature["id"]] = feature\n',
     "全部の経路を重ねる"),
    ("トップレベルのキーを前の版が勝つ", 'self.spec = {**base, **{k: v for k, v in spec.items() if k != "features"}}',
     'self.spec = {**{k: v for k, v in spec.items() if k != "features"}, **base}', "全部の経路を重ねる"),
    ("削除を当てない", "[kind].pop(target)", "[kind].get(target)", "全部の経路を重ねる"),
    ("feasibility も重ねる", 'AREAS = ["shared", "requirements", "spec"]',
     'AREAS = ["shared", "requirements", "spec", "feasibility"]', "全部の経路を重ねる"),
    ("--upto を無視する", "for number, root in versions[:upto]:", "for number, root in versions:", "--upto 1 は v1 だけ"),
    ("v で始まる名前を全部版と読む", "if not VERSION_LIKE.match(name):", 'if not name.startswith("v"):',
     "版でない名前は読まない"),
    ("ドットで始まる名前も読む", '        if path.name.startswith("."):\n', "        if False:\n",
     "ドットで始まる名前は読まない"),
    ("欠番を見ない", "if number != expected:", "if False:", "版の欠番"),
    ("版名の形を見ない", "        if not VERSION.fullmatch(name):\n            problems.append",
     "        if False:\n            problems.append", "形に合わない版名"),
    ("版が無いのを通す", "if not problems and not versions:", "if False:", "版が 1 つも無い"),
    ("シンボリックリンクを読む", "        if path.is_symlink():\n", "        if False:\n", "シンボリックリンク"),
    ("qa.csv の検査を通さない", "    if code == 1:\n", "    if False:\n", "qa.csv の決まり違反"),
    ("機能の重複を見ない", "elif fid in seen:", "elif False:", "機能の id の重複"),
    ("消す種類を見ない", "if kind not in KINDS:", "if False:", "消す種類が決まりに無い"),
    ("無いものを消すのを見ない", "elif target not in present[kind]:", "elif False:", "無いものを消す"),
    ("置きつつ消すのを見ない", "elif target in placed[kind]:", "elif False:", "置きつつ消す"),
    ("2 度消すのを見ない", "if (kind, target) in seen:", "if False:", "同じ対象を 2 度消す"),
    ("構造ファイルの削除を通す", "if kind == KIND_FILE and target in STRUCTURED:", "if False:",
     "構造ファイルをファイルとして消す"),
    ("理由の空を通す", "elif not reason.strip():", "elif False:", "理由が空"),
    ("v1 の removed.csv を通す", "if number == 1:", "if False:", "v1 に removed.csv"),
    ("前の出力を消さない", '        print("重ね合わせは作っていない", file=sys.stderr)\n        remove_stale(out)\n        return 1',
     '        print("重ね合わせは作っていない", file=sys.stderr)\n        return 1', "前の出力を消す"),
    ("書く前に前の出力を消さない", "    remove_stale(out, quiet=True)\n", "", "前の出力の中身を残さない"),
    ("印を見ない", "return out.is_dir() and not out.is_symlink() and (out / MARKER).is_file()", "return out.is_dir()",
     "印の無い場所には書かない"),
    ("docs の中を断らない", "if out_real == docs_real or docs_real in out_real.parents:", "if False:",
     "docs の中には書かない"),
    ("docs そのものを断らない", "if out_real == docs_real or docs_real in out_real.parents:",
     "if docs_real in out_real.parents:", "docs そのものには書かない"),
    ("docs を含む場所を断らない", "if out_real in docs_real.parents:", "if False:", "docs を含む場所には書かない"),
    ("出力先のシンボリックリンクを通す", "    if out.is_symlink():\n", "    if False:\n",
     "出力先のシンボリックリンクには書かない"),
    ("入力が無いとき前の出力を消さない",
     '        print(f"{docs}: ディレクトリが無い", file=sys.stderr)\n        remove_stale(out)\n',
     '        print(f"{docs}: ディレクトリが無い", file=sys.stderr)\n', "入力が無いと前の出力を消す"),
    ("読めないとき前の出力を消さない",
     '        print("重ね合わせは作っていない", file=sys.stderr)\n        remove_stale(out)\n        return 2',
     '        print("重ね合わせは作っていない", file=sys.stderr)\n        return 2', "読めないファイル"),
    ("読めないファイルを包まない", "                except OSError as e:\n", "                except KeyError as e:\n",
     "読めないファイル"),
    ("読めないディレクトリを飛ばす", "        entries = sorted(directory.iterdir())\n    except OSError as e:\n",
     "        entries = sorted(directory.iterdir())\n    except OSError as e:\n        return\n", "読めないディレクトリ"),
    ("ファイルの形の版名を飛ばす", "        if not VERSION.fullmatch(name):\n            problems.append",
     "        if not VERSION.fullmatch(name):\n            continue\n            problems.append", "ファイルの形の版名"),
    ("版のシンボリックリンクを読む", "        if not entry.is_dir() or entry.is_symlink():\n", "        if not entry.is_dir():\n",
     "版がシンボリックリンク"),
    ("置き場所のシンボリックリンクを読む", "        if top.is_symlink():\n", "        if False:\n",
     "置き場所がシンボリックリンク"),
    ("removed.csv のリンクを読む", "        if removed_path.is_symlink():\n", "        if False:\n",
     "removed.csv がシンボリックリンク"),
    ("衝突を見ない", "problems.extend(collisions(list(rendered)))", "pass", "ファイルとディレクトリの衝突"),
    ("大文字小文字を畳まない", 'unicodedata.normalize("NFC", path).casefold()', 'unicodedata.normalize("NFC", path)',
     "大文字小文字だけ違うパス"),
    ("正規化を畳まない", 'unicodedata.normalize("NFC", path).casefold()', "path.casefold()", "正規化だけ違うパス"),
    ("親を畳まずに比べる", "if fold(parent) in by_fold:", "if parent in by_fold:", "大文字小文字だけ違うファイルとディレクトリ"),
    ("書けない文字を包まない", "            except UnicodeEncodeError:\n", "            except KeyError:\n",
     "UTF-8 で書けない文字"),
    ("出力に時刻を入れる", 'whole = {**self.spec, "features": list(self.features.values())}',
     'whole = {**self.spec, "generated": __import__("time").strftime("%Y-%m-%d"), "features": list(self.features.values())}',
     "出力のバイトが決まっている"),
    ("書きかけを消さない", "        if not existed:\n            shutil.rmtree(out, ignore_errors=True)\n",
     "        if not existed:\n            pass\n", "書いている途中で失敗したら書きかけを消す"),
    ("用意された出力先ごと消す", "    existed = out.is_dir()", "    existed = False", "用意した空の出力先は失敗しても消さない"),
    ("直下の書きかけを消さない", "                    child.unlink(missing_ok=True)\n", "                    pass\n",
     "印を書きかけて失敗しても直下に残さない"),
    ("大文字の V も版と読む", 'VERSION_LIKE = re.compile(r"v[0-9]")', 'VERSION_LIKE = re.compile(r"v[0-9]", re.I)',
     "大文字の V は版でない"),
    ("印を先に書く", "        for path in sorted(rendered):\n",
     '        put(out / MARKER, b"x\\n")\n        for path in sorted(rendered):\n', "途中で落ちても印は無い"),
    ("行が 0 なら qa.csv を書かない", "        if self.has_qa:\n            buffer", "        if self.qa:\n            buffer",
     "Q&A が全部消えても qa.csv を書く"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def build(docs: Path, tree: dict | None) -> list[Path]:
    """試料を書く。読めなくしたパスを返す（後で戻す——一時ディレクトリを消せるように）。"""
    assert_in_tmp(docs)
    if tree is None:
        return []
    docs.mkdir(parents=True)
    locked = []
    for rel, content in tree.items():
        path = docs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if content is LINK:
            target = docs.parent / "outside.md"
            target.write_text("版の外\n", encoding="utf-8")
            os.symlink(target, path)
        elif content == LINK_DIR:
            target = docs.parent / "outside"
            (target / "requirements").mkdir(parents=True, exist_ok=True)
            (target / "requirements" / "x.md").write_text("版の外\n", encoding="utf-8")
            os.symlink(target, path)
        elif content == UNREADABLE:
            path.write_text("読めない\n", encoding="utf-8")
            locked.append(path)
        elif content == UNREADABLE_DIR:
            path.mkdir()
            (path / "e.md").write_text("読めない\n", encoding="utf-8")
            locked.append(path)
        else:
            path.write_text(content, encoding="utf-8")
    for path in locked:
        path.chmod(0)
    return locked


def snapshot(out: Path) -> dict[str, bytes] | None:
    if not out.is_dir() or not (out / ".merged-versions").is_file():
        return None
    return {p.relative_to(out).as_posix(): p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()}


# 書き込みの口（`put`）を差し替えて、2 つ目の書き込みで失敗させる。"crash" は後始末の走らない落ち方（OSError でない）。
# "marker" は印を書きかけたところで失敗させる——用意された出力先の直下に書きかけのファイルが残る形を作る
FAIL_DRIVER = '''
import importlib.util, sys
spec = importlib.util.spec_from_file_location("merge_versions", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
mode, real, calls = sys.argv[2], module.put, []
def put(dest, content):
    calls.append(dest)
    if mode == "marker":  # 中身を全部書いたあと、印を 5 バイト書いたところで失敗する（出力先の直下に書きかけが残る）
        if dest.name == ".merged-versions":
            dest.write_bytes(content[:5])
            raise OSError(28, "No space left on device")
    elif len(calls) == 2:
        if mode == "crash":
            raise KeyboardInterrupt
        raise OSError(28, "No space left on device")
    real(dest, content)
module.put = put
sys.exit(module.main(sys.argv[3:]))
'''


def merge(scripts: Path, docs: Path, out: Path, extra: list[str], fail: str | None = None) -> tuple[int, str]:
    head = ["-c", FAIL_DRIVER, str(scripts / TARGET), fail] if fail else [str(scripts / TARGET)]
    proc = subprocess.run([sys.executable, "-I", *head, str(docs), str(out), *extra],
                          capture_output=True, text=True, cwd=docs.parent)
    return proc.returncode, proc.stdout + proc.stderr


def run_case(scripts: Path, root: Path, tree: dict, prepare: str, extra: list[str], twice: bool = False) -> Result:
    assert_in_tmp(root)
    docs = root / "docs"
    locked = build(docs, tree)
    out = {"inside": docs / "merged", "docs": docs, "parent": root}.get(prepare, root / "build" / "merged")
    preexisting = None
    if prepare == "parent":
        (root / ".merged-versions").write_text("前の出力\n", encoding="utf-8")
    elif prepare == "symlink":
        (root / "real").mkdir()
        out.parent.mkdir(parents=True)
        os.symlink(root / "real", out)
    elif prepare == "stale":
        out.mkdir(parents=True)
        (out / ".merged-versions").write_text("前の出力\n", encoding="utf-8")
        (out / "old.md").write_text("古い\n", encoding="utf-8")
    elif prepare == "foreign":
        out.mkdir(parents=True)
        (out / "keep.md").write_text("正本\n", encoding="utf-8")
    elif prepare in ("failwrite-empty", "marker-empty"):
        out.mkdir(parents=True)
    fail = {"failwrite": "oserror", "failwrite-empty": "oserror", "crash": "crash", "marker-empty": "marker"}.get(prepare)
    code, output = merge(scripts, docs, out, extra, fail)
    leftover = (sorted(p.relative_to(out).as_posix() for p in out.rglob("*"))
                if out.is_dir() and not out.is_symlink() else None)
    for path in locked:
        path.chmod(0o755)
    docs_intact = tree is None or (docs / "v1").is_dir()
    if prepare == "foreign":
        keep = out / "keep.md"
        preexisting = keep.read_text(encoding="utf-8") if keep.is_file() else None
    again = None
    if twice:
        second = root / "build" / "again"
        merge(scripts, docs, second, extra)
        again = snapshot(second)
    tree_out = None if prepare in ("docs", "parent") else snapshot(out)
    return Result(code, output, tree_out, preexisting, again, docs_intact, leftover)


def skipped(name: str) -> bool:
    """root は mode 000 でも読めるので、読めない入力の試料を作れない。"""
    return name in UNREADABLE_CASES and hasattr(os, "geteuid") and os.geteuid() == 0


def run_all(scripts: Path, work: Path) -> dict[str, Result]:
    return {name: run_case(scripts, work / f"case{i}", tree, prepare, extra)
            for i, (name, tree, prepare, extra, _) in enumerate(CASES) if not skipped(name)}


def as_expected(name: str, result: Result) -> bool:
    judge = next(case for case in CASES if case[0] == name)[4]
    try:
        return judge(result)
    except (TypeError, KeyError, IndexError, AttributeError, ValueError):
        return False


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def check_reference() -> None:
    """本体の定数（写し）が `references/versions.md`（原本）と一致するか。"""
    spec = importlib.util.spec_from_file_location("merge_versions", SCRIPTS / TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    text = REFERENCE.read_text(encoding="utf-8")

    section = text.split("### 削除（`removed.csv`）", 1)[1].split("\n## ", 1)[0]
    columns = re.findall(r"^\| `([^`]+)` \|", section, re.M)
    check("removed.csv の列が versions.md と違う", columns == module.REMOVED_COLUMNS, f"{columns} vs {module.REMOVED_COLUMNS}")
    kinds_line = next((line for line in section.splitlines() if line.startswith("| `種類` |")), "")
    kinds = re.findall(r"`([^`]+)`", kinds_line.split("|")[2])
    check("removed.csv の種類が versions.md と違う", kinds == module.KINDS, f"{kinds} vs {module.KINDS}")
    check("ファイルとして消せないものが versions.md と違う",
          f"**`{module.STRUCTURED[0]}` と `{module.STRUCTURED[1]}` はファイルとしては消せない**" in text)
    check("重ねる置き場所が versions.md と違う",
          "（" + "・".join(f"`{a}/`" for a in module.AREAS) + "）" in text)
    check("出力先の印が versions.md と違う", f"（`{module.MARKER}`）" in text)
    check("removed.csv の名前が versions.md と違う", f"### 削除（`{module.REMOVED}`）" in text)


def main() -> int:
    check_reference()
    with tempfile.TemporaryDirectory(prefix="merge-versions-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        results = run_all(scripts, tmp_path / "work")
        for name, result in results.items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result.code} {result.output[-400:]}")

        # 決定論: 2 回作ってバイトが一致し、陽性対照として入力を 1 字変えると変わる
        twice = run_case(scripts, tmp_path / "twice", MAIN, "none", [], twice=True)
        check("2 回作ってバイトが一致しない", made(twice) and twice.tree == twice.again)
        shifted = run_case(scripts, tmp_path / "shifted", {**MAIN, "v2/requirements/c.md": "C3\n"}, "none", [])
        check("入力を変えても出力が変わらない（何を渡しても同じものを出している）",
              made(shifted) and shifted.tree != twice.tree)

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            if skipped(killer):
                continue
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            killer_case = next(case for case in CASES if case[0] == killer)
            result = run_case(mutated, tmp_path / f"mutwork{index}", *killer_case[1:4])
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result.output[-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    skip = [name for name, *_ in CASES if skipped(name)]
    if skip:
        print(f"飛ばした（root では読めない入力を作れない）: 試料 {'・'.join(skip)} と、それを名指しした変異")
    print(f"OK: 試料 {len(CASES) - len(skip)} 件・変異 {sum(not skipped(m[3]) for m in MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
