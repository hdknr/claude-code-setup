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
   重ねた結果のファイルとディレクトリの衝突・大文字小文字や Unicode の正規化だけが違うパス・UTF-8 で書けない文字・
   **版の直下の、置き場所・`removed.csv` と綴りだけ違う名前（`Removed.csv`・`Shared/`。#276）——中身は読まない**。
   **綴りは git が見る綴り**——コミットが正しい綴りで、作業ツリーに古い綴りのフォルダ（`.DS_Store` だけ）が残っていても 0、
   コミットが綴り違いなら作業ツリーのフォルダの綴りに依らず 1（本物の git リポジトリを一時ディレクトリに作って当てる）。
   **置き場所より深いフォルダとファイルの名前も index の綴りで読み、`git archive` で書き出したものを重ねた答えと一致する**（#569）。
   **置き場所の中の構造ファイルの綴り違い（`shared/QA.csv`・`spec/QA-dev.csv`・`spec/Spec_IR.json`）は 1**（#511）。
   **作業ツリーの中なのに `git ls-files` が失敗したら（壊れた index）2**。**外かは `git rev-parse --is-inside-work-tree` で決める**
   ——`docs` の上の壊れた・中身の無い `.git`、発見が止まる境界の向こうの `.git` は外と読んで 0。**本物の FS の境界は作れないので
   `GIT_CEILING_DIRECTORIES` で代える**（どちらも git の発見を止める）。git が無いときは上に `.git` が在れば 2、無ければ 0（#572）。
   **フックが相対で設定した `GIT_DIR` は外し、`GIT_INDEX_FILE` は根からのパスとして読む**（一時の index の綴りで読む。無い index を
   指していれば 2。パスの指定の読み方を変える変数も外す。#570）。**追跡しているファイルは自分の index のパスでだけ数え、index に綴り違いの
   2 つが在るフォルダ・ファイルは、タグを読む `build-proposal.py` の `copy_docs` と同じく 1**（区別しない FS に展開した `git archive` は綴りを失うので、
   この形の比べ相手にしない）。**重ねた結果でフォルダの綴りだけが違うのも 1**（#569）。
   区別しない FS でだけ・区別する FS でだけ判別できる試料と変異は、走らせなかったことを出力に書く（緑のふりをしない）。
   **CI の Linux では区別しない FS（ext4 の casefold）を作って同じテストをもう 1 度回し、環境変数
   `MERGE_VERSIONS_TEST_REQUIRE_CASE_FOLD=1` を渡す——一時ディレクトリが区別する FS なら赤にする**（用意に失敗して黙って緑にならない。#571）。
   **前に作った出力は消す。** **入力が無い・読めない（2）ときも消す。**
4. **正本を消さない（2）**——印の無い空でない出力先・シンボリックリンクの出力先・`docs/` の中・`docs/` そのもの・
   `docs/` を含む場所には書かない。**中身は触らない。**
5. **同じ入力から同じバイト**——2 回作って一致。**陽性対照として、入力を 1 字変えると出力が変わる。**
   **2 回続けて作るだけでは、日付のように粒の粗い時刻を捕まえない**ので、出力の全バイト（印を含む）を期待値と突き合わせる。
8. **書いている途中で失敗したら、書きかけを残さない**——書き込みの口（`put`）を差し替えて 2 つ目で失敗させる。
   用意された空の出力先は消さない（印を書きかけて失敗しても、直下に書きかけを残さない）。**途中で落ちても（後始末が走らなくても）印は無い。**
9. **想定外の例外（128KB 超のセルの `csv.Error`・深い入れ子の `RecursionError`）も 2 で、前の出力を消す**。
   書いている途中の想定外の例外でも書きかけを残さない。前の出力を消そうとして上がった例外も入口が 2 にする
   （トレースバックの 1 にしない）。`-OO`（docstring が無い）で引数なしに呼んでも使い方の誤りとして 2（#286）。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。
7. **決まりの写しがずれていない**——本体の定数が `references/versions.md` と一致する。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**読めない入力の試料は root では作れない**（root は mode 000 でも読める）。root で走らせたときは、その試料と
それを名指しした変異を飛ばし、**飛ばしたことを出力に書く**（緑のふりをしない）。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "merge-versions.py"
REFERENCE = PLUGIN / "references" / "versions.md"

QA_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
Q1 = "Q-001,要求確定,質問1,A: 甲 / B: 乙,A,理由,A（業務部が回答）,決定表 1 行目,反映済み,\n"
Q2 = "Q-002,要求確定,質問2,A: 甲 / B: 乙,A,理由,未回答,—,確認中,\n"
Q2B = "Q-002,要求確定,質問2,A: 甲 / B: 乙,A,理由,B（業務部が回答）,決定表 2 行目,反映済み,\n"
Q3 = "Q-003,開発,質問3,A: 甲 / B: 乙,A,理由,未回答,—,確認中,\n"
# 内部の Q&A 表（spec/qa-dev.csv）の行（#339）
D1 = "D-001,仕様レビュー,内部1,A: 甲 / B: 乙,A,理由,未回答,—,確認中,\n"
D1B = "D-001,仕様レビュー,内部1,A: 甲 / B: 乙,A,理由,A（開発 2026-10-22）,spec/order.md,反映済み,\n"
D2 = "D-002,仕様レビュー,内部2,A: 甲 / B: 乙,B,理由,未回答,—,確認中,\n"
BAD_QA = "Q-004,要求確定,質問4,A: 甲 / B: 乙,A,理由,未回答,—,保留,\n"  # 状態が決まりに無い

SPEC1 = {"spec_ir_version": 1, "title": "注文", "features": [
    {"id": "F-001", "title": "割引", "cases": [{"id": "F-001-C1"}]},
    {"id": "F-002", "title": "送料"}]}
# v2 は差分だけ。並びを v1 と逆にして、置き換えが前の版の位置に入ることを見る
SPEC2 = {"title": "注文 v2", "features": [{"id": "F-003", "title": "ポイント"}, {"id": "F-002", "title": "送料 v2"}]}
REMOVED_HEAD = "種類,対象,理由\n"
# 入力の木の特別な値: シンボリックリンク（版の外のファイル／ディレクトリへ）と、読めないファイル／ディレクトリ
LINK, LINK_DIR, UNREADABLE, UNREADABLE_DIR = None, "\0link-dir", "\0unreadable", "\0unreadable-dir"
UNREADABLE_CASES = {"読めないファイル", "読めないディレクトリ", "読めない中間表現", "前の出力を消せないときの想定外の例外"}
# 128KB を超えるセル（csv.Error）と深い入れ子（RecursionError）——どちらも想定外の例外（#286）
BIG_QA = QA_HEAD + Q3.replace("質問3", "x" * 200_000)
DEEP_JSON = "[" * 200_000 + "]" * 200_000


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
NO_REMOVED = {k: v for k, v in MAIN.items() if k != "v2/removed.csv"}
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
                 again: dict[str, bytes] | None = None, docs_intact: bool = True, leftover: list[str] | None = None,
                 archive: tuple[int, dict[str, bytes] | None] | None = None):
        self.code, self.output, self.tree, self.preexisting, self.again = code, output, tree, preexisting, again
        self.docs_intact, self.leftover = docs_intact, leftover
        self.archive = archive  # 同じコミットを git archive で書き出したものを重ねた (終了コード, 出力)。#569

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
# ／"stale-loop"（印つきの前の出力があり、docs は自分を指すシンボリックリンク）／"parent-loop"（docs を含む印つきの場所が出力先で、docs は自分を指すリンク）
# ／"out-loop"（出力先が、自分を指すリンクの下にある）
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
    # docs が自分を指すリンクでも、読めない入力と同じに前の出力を消す——3.12 は resolve で RuntimeError を投げる（#286 の 1 パス目）
    ("入力が自分を指すリンクでも前の出力を消す", None, "stale-loop", [],
     lambda r: r.code == 2 and r.tree is None and "前に作った出力を消した" in r.output),
    # そのリンクを含む印つきの場所は、入力を含む場所として断り、消さない（#286 の 2 パス目——先に消す分岐が消していた）
    ("自分を指すリンクを含む場所は消さない", None, "parent-loop", [],
     lambda r: r.code == 2 and "を含む場所には書かない" in r.output and "前に作った出力を消した" not in r.output
     and r.tree is not None and "keep.md" in r.tree),
    # 出力先が輪の下でも、辿るところでは止まらず、書けないとして 2（#286 の狭いパスの NP-1——輪を out 側に置く試料が無かった）
    ("出力先が自分を指すリンクの下でも書けないとして止まる", MAIN, "out-loop", [],
     lambda r: r.code == 2 and "書けない" in r.output and "想定外の例外" not in r.output),
    ("読めないファイル", {**MAIN, "v2/requirements/d.md": UNREADABLE}, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "読めない" in r.output and "前に作った出力を消した" in r.output),
    ("読めないディレクトリ", {**MAIN, "v2/requirements/sub": UNREADABLE_DIR}, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "読めない" in r.output and "前に作った出力を消した" in r.output),
    # 権限で読めないものを「UTF-8 として読めない」と言わない。UTF-8 でないものは UTF-8 と言う（#286）
    ("読めない中間表現", {**MAIN, "v2/spec/spec_ir.json": UNREADABLE}, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "spec_ir.json: 読めない（" in r.output and "UTF-8" not in r.output),
    ("UTF-8 でない中間表現", {**MAIN, "v2/spec/spec_ir.json": b"\xff\xfe{}"}, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "spec_ir.json: UTF-8 として読めない" in r.output),
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
    ("内部の表を行で重ねる", {**MAIN, "v1/spec/qa-dev.csv": QA_HEAD + D1, "v2/spec/qa-dev.csv": QA_HEAD + D2 + D1B}, "none", [],
     lambda r: made(r) and r.text("spec/qa-dev.csv") == QA_HEAD + D1B + D2 and r.text("shared/qa.csv") == QA_HEAD + Q1 + Q2B + Q3),
    ("内部の行を removed.csv で消す",
     {**V1, "v1/spec/qa-dev.csv": QA_HEAD + D1 + D2, "v2/removed.csv": REMOVED_HEAD + "Q&A,D-001,共有へ移した（Q-003）\n"},
     "none", [], lambda r: made(r) and r.text("spec/qa-dev.csv") == QA_HEAD + D2 and r.text("shared/qa.csv") == QA_HEAD + Q1 + Q2),
    # 印つきの内部の番号（#278）も、層の判定で内部の表から消す
    ("印つきの内部の行を removed.csv で消す",
     {**V1, "v1/spec/qa-dev.csv": QA_HEAD + D1.replace("D-001", "D-S-001") + D2,
      "v2/removed.csv": REMOVED_HEAD + "Q&A,D-S-001,共有へ移した（Q-S-001）\n"},
     "none", [], lambda r: made(r) and r.text("spec/qa-dev.csv") == QA_HEAD + D2 and r.text("shared/qa.csv") == QA_HEAD + Q1 + Q2),
    ("内部の表の決まり違反（番号が Q-）", {**MAIN, "v2/spec/qa-dev.csv": QA_HEAD + Q3}, "none", [],
     lambda r: refused(r, "`D-S-001` の形でない")),
    ("内部の表をファイルとして消す", {**V1, "v1/spec/qa-dev.csv": QA_HEAD + D1,
                               "v2/removed.csv": REMOVED_HEAD + "ファイル,spec/qa-dev.csv,x\n"}, "none", [],
     lambda r: refused(r, "ファイルとしては消せない")),
    ("内部の表に無い D- を消す", with_removed("Q&A,D-009,x\n"), "none", [], lambda r: refused(r, "前の版までに無いもの")),
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
    # 版の直下の名前は綴りどおりに読む（#276）——区別しない FS でだけ removed.csv・shared/ として開けてしまう。
    # 中身（v2 でも置く a.md を消す行・決まりに反する qa.csv）は読まない——読めば別の問題が並ぶ（区別しない FS でだけ判別できる）。
    # 置き場所の試料は v2 に綴りどおりの置き場所を置かない（区別しない FS では同じディレクトリに書かれて試料にならない）
    ("綴りの違う Removed.csv は断る", {**NO_REMOVED, "v2/Removed.csv": REMOVED_HEAD + "ファイル,requirements/a.md,x\n"}, "stale", [],
     lambda r: refused(r, "Removed.csv: removed.csv と大文字小文字") and "置きつつ消している" not in r.output),
    ("綴りの違う Shared/ は断る", {**V1, "v2/Shared/qa.csv": QA_HEAD + BAD_QA}, "none", [],
     lambda r: refused(r, "Shared: shared と大文字小文字") and "保留" not in r.output),
    ("綴りの違う Requirements/ は断る", {**V1, "v2/Requirements/d.md": "D\n"}, "none", [],
     lambda r: refused(r, "Requirements: requirements と大文字小文字")),
    ("綴りの違う SPEC/ は断る", {**V1, "v2/SPEC/x.md": "X\n"}, "none", [],
     lambda r: refused(r, "SPEC: spec と大文字小文字")),
    # 綴りだけ違っても、読む名前を持たないディレクトリ（`.DS_Store` だけ）は数えない——タグにも写らない（#276 の CR2-1）
    ("中身の無い綴り違いは数えない", {**V1, "v2/requirements/d.md": "D\n", "v2/Shared/.DS_Store": "x"}, "none", [],
     lambda r: made(r) and "requirements/d.md" in r.tree),
    # コミットは正しい綴りで、作業ツリーに古い綴りのフォルダが残る（#276 の CR2-1。区別しない FS では requirements/ がそのフォルダに
    # 書かれる——試料は改名で作る。区別する FS では .DS_Store だけの Requirements/ が並ぶ）。git が見る綴りは requirements なので 0
    ("コミットが正しい綴りなら作業ツリーの古い綴りで断らない", {**V1, "v2/requirements/d.md": "D\n"}, "git-stale", [],
     lambda r: made(r) and "requirements/d.md" in r.tree),
    # コミットが綴り違い（#276 の CR2-2。区別しない FS では作業ツリーのフォルダを正しい綴りに改名しても git は変更と見ない）——1
    ("コミットが綴り違いなら作業ツリーの綴りに依らず断る", {**V1, "v2/Requirements/d.md": "D\n"}, "git-renamed", [],
     lambda r: refused(r, "Requirements: requirements と大文字小文字")),
    # 区別する FS でだけ作れる形: コミットは正しい綴り、追跡しない別のフォルダ Requirements/ に読むファイルがある——git にも別の名前で 1
    ("別の項目の綴り違いは index に寄せない", {**V1, "v2/requirements/d.md": "D\n"}, "git-alongside", [],
     lambda r: refused(r, "Requirements: requirements と大文字小文字")),
    # `.git` が在るのに git ls-files が失敗する（壊れた .git）——綴りを照合していないので 2
    # index に綴りの違う 2 つ（shared/・Shared/）が在り、区別しない FS では 1 つのフォルダ——タグと同じく 1
    ("index の綴り違いは同じフォルダでも断る", {**V1, "v2/shared/a.md": "A\n"}, "git-both", [],
     lambda r: refused(r, "Shared: shared と大文字小文字")),
    # removed.csv のファイルも同じ（1 パス目の Verifier の反証）——コミットが Removed.csv なら作業ツリーで removed.csv に改名しても 1、
    # コミットが removed.csv なら作業ツリーで Removed.csv に改名しても削除を当てて 0（区別しない FS では git も変更と見ない）
    ("コミットの Removed.csv は作業ツリーの綴りに依らず断る", {**V1, "v2/Removed.csv": REMOVED_HEAD + "ファイル,requirements/a.md,x\n"},
     "git-renamed-file", [], lambda r: refused(r, "Removed.csv: removed.csv と大文字小文字")),
    ("コミットの removed.csv は作業ツリーの綴りに依らず読む", {**V1, "v2/removed.csv": REMOVED_HEAD + "ファイル,requirements/a.md,x\n"},
     "git-renamed-file", [], lambda r: made(r) and "requirements/a.md" not in r.tree and "requirements/b.md" in r.tree),
    # docs・版のフォルダ自身の古い綴り（再開後の 2 パス目の /code-review）——docs が作業ツリーで Docs でも、コミットが Docs/ で docs と
    # 打っても、index の綴りで読む。版のフォルダが V2（.DS_Store だけ残る）でも、コミットの v2 として読む
    ("docs のフォルダの綴りが違っても index で断る", {**V1, "v2/Removed.csv": REMOVED_HEAD + "ファイル,requirements/a.md,x\n"},
     "git-docs-stale", [], lambda r: refused(r, "Removed.csv: removed.csv と大文字小文字")),
    ("コミットの Docs/ を docs で読んでも index で断る", {**V1, "v2/Removed.csv": REMOVED_HEAD + "ファイル,requirements/a.md,x\n"},
     "git-docs-upper", [], lambda r: refused(r, "Removed.csv: removed.csv と大文字小文字")),
    ("版のフォルダの古い綴りでも index の版として読む", {**V1, "v2/requirements/d.md": "D\n"}, "git-version-stale", [],
     lambda r: made(r) and "requirements/d.md" in r.tree),
    # 作業ツリーの中なのに index を読めない（壊れた index）——綴りを照合していないので 2（#538 で承認された決めた値。#572）
    ("git が失敗すれば判定しない", {**V1}, "git-index-corrupt", [],
     lambda r: r.code == 2 and "git ls-files が失敗した" in r.output and r.tree is None),
    # 外かどうかは git rev-parse --is-inside-work-tree で決める（#572）——docs の上の関係のない .git（壊れた gitdir:・中身の無い
    # ディレクトリ）と、git が発見を止める境界の向こうの .git（FS の境界の代わりに GIT_CEILING_DIRECTORIES）は外と読んで 0
    ("上の壊れた .git は外と読む", {**V1}, "git-broken", [], lambda r: made(r) and "requirements/a.md" in r.tree),
    ("上の中身の無い .git は外と読む", {**V1}, "git-empty-dotgit", [], lambda r: made(r) and "requirements/a.md" in r.tree),
    ("発見が止まる境界の向こうの .git は外と読む", {**V1, "v2/requirements/d.md": "D\n"}, "git-ceiling", [],
     lambda r: made(r) and "requirements/d.md" in r.tree),
    # git を走らせられないときだけ上へ辿る——.git が在れば中か外か決められないので 2、無ければ外（#572）
    ("git が無くて上に .git が在れば判定しない", {**V1}, "git-missing", [],
     lambda r: r.code == 2 and "git を走らせられない" in r.output and r.tree is None),
    ("git が無くても .git が無ければ外と読む", {**V1}, "no-git", [], lambda r: made(r) and "requirements/a.md" in r.tree),
    # フックが相対で設定した GIT_INDEX_FILE・GIT_DIR（#570）。どちらも根から見れば正しく、docs から見ると GIT_INDEX_FILE は壊れたファイル、
    # GIT_DIR は無い。GIT_INDEX_FILE は根からのパスとして読み（docs から読めば 2）、GIT_DIR は外す（引き継げば外と読んで綴り違いを通す）
    ("フックの相対の GIT_INDEX_FILE は根から読む", {**V1, "v2/requirements/d.md": "D\n"}, "git-env-index", [],
     lambda r: made(r) and "requirements/d.md" in r.tree),
    # GIT_INDEX_FILE は外さない——部分コミットの一時の index（コミットは Requirements/、一時の index は requirements/ に改名済み）の
    # 綴りで読む。外して .git/index を読むと、コミットされない Requirements/ で断る（区別しない FS）
    ("フックの一時の index の綴りで読む", {**V1, "v2/Requirements/d.md": "D\n"}, "git-env-temp-index", [],
     lambda r: made(r) and "requirements/d.md" in r.tree),
    ("フックの相対の GIT_DIR を引き継がない", {**V1, "v2/Requirements/d.md": "D\n"}, "git-env-dir", [],
     lambda r: refused(r, "Requirements: requirements と大文字小文字")),
    # GIT_INDEX_FILE が無い index を指す——git は空の index と読むので、黙って作業ツリーの綴りに戻さず 2（#570 の 1 パス目の指摘）
    ("無い GIT_INDEX_FILE は判定しない", {**V1}, "git-env-missing-index", [],
     lambda r: r.code == 2 and "GIT_INDEX_FILE が指す index" in r.output and r.tree is None),
    # index に深いフォルダの綴り違い 2 つ（Sub/a.md・sub/b.md）が在り、区別しない FS では 1 つのフォルダ——追跡しているファイルは
    # 自分の index のパスでだけ数え（コミットに無い sub/a.md・Sub/b.md を作らない）、フォルダの綴り違いとして 1。タグを読む
    # build-proposal.py の copy_docs と同じ答え（区別しない FS に展開した git archive は綴りを失うので比べ相手にしない）。#569 の 1・2 パス目の指摘
    ("深い段の index の綴り違い 2 つはフォルダの綴り違い", {**V1, "v2/requirements/Sub/a.md": "A\n"}, "git-deep-both", [],
     lambda r: refused(r, "ディレクトリ requirements/Sub と requirements/sub") and "requirements/Sub/b.md" not in r.output
     and "requirements/sub/a.md" not in r.output),
    # 2 段にまたがる形（Sub/x/a.md・sub/x/b.md）も同じ（2 パス目の指摘）
    ("2 段の index の綴り違いもフォルダの綴り違い", {**V1, "v2/requirements/Sub/x/a.md": "A\n"}, "git-deep-both-2", [],
     lambda r: refused(r, "ディレクトリ requirements/Sub と requirements/sub") and "requirements/Sub/x/b.md" not in r.output
     and "requirements/sub/x/a.md" not in r.output),
    # 版の段の綴り違い（index に v2/requirements/a.md・V2/requirements/b.md）——V2 は版でない名前。v2 は自分の index の a.md だけで、
    # b.md は v1 のまま（V2 の B2 を取り込まない。2 パス目の指摘）
    ("別の綴りの版で追跡するファイルは取り込まない", {**V1, "v2/requirements/a.md": "A\n"}, "git-version-both", [],
     lambda r: made(r) and r.text("requirements/a.md") == "A\n" and "requirements/b.md" in r.tree and r.text("requirements/b.md") == "B1\n"),
    # index にファイル名の綴り違い 2 つ（a.md・A.md）が在り、区別しない FS では 1 つのファイル——両方のパスで数えて 1（copy_docs と同じ）
    ("index のファイル名の綴り違い 2 つは断る", {**V1, "v2/requirements/d.md": "D\n"}, "git-file-both", [],
     lambda r: refused(r, "requirements/D.md と requirements/d.md")),
    # 重ねた結果でフォルダの綴りだけが違う（v1 の sub/、v2 の Sub/）——ファイルのパスはぶつからなくても 1（2 パス目の指摘。どの FS でも）
    ("フォルダの綴りだけ違うのも断る", {**V1, "v1/requirements/sub/y.md": "Y\n", "v2/requirements/Sub/x.md": "X\n"}, "none", [],
     lambda r: refused(r, "ディレクトリ requirements/Sub と requirements/sub")),
    # GIT_LITERAL_PATHSPECS（パスの指定を文字どおりに読む）を引き継がない——引き継げば index が空になり、綴り違いを通す（2 パス目の指摘）
    ("パスの指定を変える変数を引き継がない", {**V1, "v2/Requirements/d.md": "D\n"}, "git-env-literal", [],
     lambda r: refused(r, "Requirements: requirements と大文字小文字")),
    # 置き場所より深い段も index の綴りで読む（#569）——コミットは requirements/sub/d.md、作業ツリーは Sub/D.md（区別しない FS で
    # git も変更と見ない）。作業ツリーで重ねても、git archive で書き出したもので重ねても同じ答え
    ("深い段の綴りが作業ツリーで違っても index の綴りで読む", {**V1, "v2/requirements/sub/d.md": "D\n"}, "git-deep-stale", [],
     lambda r: made(r) and "requirements/sub/d.md" in r.tree and r.archive == (0, r.tree)),
    # 構造ファイルも同じ——コミットは shared/qa.csv、作業ツリーは QA.csv。index の綴りで Q&A 表として読む（書き出しと同じ）
    ("構造ファイルの綴りが作業ツリーで違っても index の綴りで読む", {**V1, "v2/shared/qa.csv": QA_HEAD + Q3}, "git-structured-stale", [],
     lambda r: made(r) and r.qa_numbers() == ["Q-001", "Q-002", "Q-003"] and r.archive == (0, r.tree)),
    # 置き場所の中の構造ファイルの綴り違いは 1（#511）——重ねた出力を決まった名前で開く側が、区別しない FS でだけ Q&A 表として読むため。
    # 中身（決まりに反する行）は読まない
    ("置き場所の中の QA.csv は断る", {**V1, "v2/shared/QA.csv": QA_HEAD + BAD_QA}, "none", [],
     lambda r: refused(r, "shared/QA.csv: shared/qa.csv と大文字小文字") and "保留" not in r.output),
    ("置き場所の中の QA-dev.csv は断る", {**V1, "v2/spec/QA-dev.csv": QA_HEAD + D1}, "none", [],
     lambda r: refused(r, "spec/QA-dev.csv: spec/qa-dev.csv と大文字小文字")),
    ("置き場所の中の Spec_IR.json は断る", {**V1, "v2/spec/Spec_IR.json": js(SPEC2)}, "none", [],
     lambda r: refused(r, "spec/Spec_IR.json: spec/spec_ir.json と大文字小文字")),
    ("途中で落ちても印は無い", MAIN, "crash", [],
     lambda r: r.code != 0 and r.leftover is not None and ".merged-versions" not in r.leftover),
    # 想定外の例外も 2（判定していない）で、トレースバックの 1 にしない。前の出力は読めない入力と同じに消す（#286）
    ("巨大なセル", {**MAIN, "v2/shared/qa.csv": BIG_QA}, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "想定外の例外で止まった（Error: field larger" in r.output
     and "前に作った出力を消した" in r.output and "Traceback" not in r.output),
    ("深い入れ子", {**MAIN, "v2/spec/spec_ir.json": DEEP_JSON}, "stale", [],
     lambda r: r.code == 2 and r.tree is None and "想定外の例外で止まった（RecursionError" in r.output
     and "前に作った出力を消した" in r.output and "Traceback" not in r.output),
    ("書いている途中の想定外の例外", MAIN, "failwrite-unexpected", [],
     lambda r: r.code == 2 and "想定外の例外 ValueError" in r.output and "書きかけを消した" in r.output and r.leftover is None),
    # 前の出力を消そうとして PermissionError——内側の捕捉の中で上がった例外は、入口が 2 にする
    ("前の出力を消せないときの想定外の例外", {**MAIN, "v2/shared/qa.csv": BIG_QA}, "stale-locked", [],
     lambda r: r.code == 2 and "想定外の例外で止まった（PermissionError" in r.output and "Traceback" not in r.output),
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
    ("ドットで始まる名前も読む", '        if name.startswith("."):\n', "        if False:\n",
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
    # 試料は 3.12 の Path.resolve を再現して走らせる（下の RESOLVE_312）ので、どちらの変異もどの版でも死ぬ
    ("docs を辿るのに Path.resolve を使う",
     "docs_real, out_real = Path(os.path.realpath(docs)), Path(os.path.realpath(out))",
     "docs_real, out_real = docs.resolve(), Path(os.path.realpath(out))",
     "入力が自分を指すリンクでも前の出力を消す"),
    ("出力先を辿るのに Path.resolve を使う",
     "docs_real, out_real = Path(os.path.realpath(docs)), Path(os.path.realpath(out))",
     "docs_real, out_real = Path(os.path.realpath(docs)), out.resolve()",
     "出力先が自分を指すリンクの下でも書けないとして止まる"),
    ("読めないとき前の出力を消さない",
     '        print("重ね合わせは作っていない", file=sys.stderr)\n        remove_stale(out)\n        return 2',
     '        print("重ね合わせは作っていない", file=sys.stderr)\n        return 2', "読めないファイル"),
    ("読めないファイルを包まない", "                except OSError as e:\n", "                except KeyError as e:\n",
     "読めないファイル"),
    ("読めないディレクトリを飛ばす", "        return {entry.name for entry in directory.iterdir()}\n    except OSError as e:\n",
     "        return {entry.name for entry in directory.iterdir()}\n    except OSError as e:\n        return set()\n", "読めないディレクトリ"),
    ("ファイルの形の版名を飛ばす", "        if not VERSION.fullmatch(name):\n            problems.append",
     "        if not VERSION.fullmatch(name):\n            continue\n            problems.append", "ファイルの形の版名"),
    ("版のシンボリックリンクを読む", "        if not entry.is_dir() or entry.is_symlink():\n", "        if not entry.is_dir():\n",
     "版がシンボリックリンク"),
    ("置き場所のシンボリックリンクを読む", "        if top.is_symlink():\n", "        if False:\n",
     "置き場所がシンボリックリンク"),
    ("removed.csv のリンクを読む", "        elif removed_path.is_symlink():\n", "        elif False:\n",
     "removed.csv がシンボリックリンク"),
    ("版の直下の綴り違いを見ない", "        problems.extend(misnamed(root, entries))\n", "", "綴りの違う Shared/ は断る"),
    ("綴り違いに removed.csv を含めない", "expected = {fold(name): name for name in [*AREAS, REMOVED]}",
     "expected = {fold(name): name for name in AREAS}", "綴りの違う Removed.csv は断る"),
    ("綴り違いを畳まずに比べる", "want = expected.get(fold(name))", "want = expected.get(name)", "綴りの違う Requirements/ は断る"),
    ("綴りが同じでも断る", "if want is None or name == want:", "if want is None:", "全部の経路を重ねる"),
    ("中身の無い綴り違いも数える", "            continue  # 読む名前を持たない", "            pass  # 読む名前を持たない",
     "中身の無い綴り違いは数えない"),
    ("index を見ない", "        entries = spelled(root, None if index is None else index.get((root.name,), set()))\n",
     "        entries = names(root)\n",
     "コミットが正しい綴りなら作業ツリーの古い綴りで断らない"),
    ("git を呼ばない", "    found = tracked(docs) if docs.is_dir() else None\n", "    found = None\n",
     "コミットが綴り違いなら作業ツリーの綴りに依らず断る"),
    ("同じ項目かを見ない", " and same_entry(root / m, root / name)}", "}", "別の項目の綴り違いは index に寄せない"),
    ("index に在る名前は寄せない", "    for name in entries:\n        # 自分自身も含む",
     "    for name in entries:\n        if name in index:\n            result.add(name)\n            continue\n        # 自分自身も含む",
     "index の綴り違いは同じフォルダでも断る"),
    ("版の直下のファイルを index から集めない", "        for depth in range(len(rest)):", "        for depth in range(min(len(rest), 1)):",
     "コミットの removed.csv は作業ツリーの綴りに依らず読む"),
    # 置き場所より深い段（#569）——前の形（版の直下まで）に戻す・walk が index を引かない
    ("深い段を index から集めない", "        for depth in range(len(rest)):", "        for depth in range(min(len(rest), 2)):",
     "深い段の綴りが作業ツリーで違っても index の綴りで読む"),
    ("深い段を index に寄せない", "    for name in sorted(spelled(directory, None if index is None else index.get(prefix, set()))):\n",
     "    for name in sorted(names(directory)):\n", "構造ファイルの綴りが作業ツリーで違っても index の綴りで読む"),
    ("深い段の接頭辞を伸ばさない", "            walk(root, path, files, problems, index, (*prefix, name), owned)\n",
     "            walk(root, path, files, problems, index, prefix, owned)\n", "深い段の綴りが作業ツリーで違っても index の綴りで読む"),
    # 追跡しているファイルは自分の index のパスでだけ数える・フォルダの綴り違い・パスの指定の変数（2 パス目の指摘）
    ("別の綴りで追跡するファイルも数える", '            if owned is not None and not claims(owned, path, "/".join((*prefix, name))):\n',
     "            if False:\n", "別の綴りの版で追跡するファイルは取り込まない"),
    ("2 段でも別の綴りで追跡するファイルを数える", '            if owned is not None and not claims(owned, path, "/".join((*prefix, name))):\n',
     "            if False:\n", "2 段の index の綴り違いもフォルダの綴り違い"),
    ("フォルダの綴り違いを見ない", "            if other != parent:\n                found.append(f\"重ねた結果でディレクトリ",
     "            if False:\n                found.append(f\"重ねた結果でディレクトリ", "フォルダの綴りだけ違うのも断る"),
    ("パスの指定の変数を外さない", "*GIT_LOCATION, *GIT_PATHSPECS, ", "*GIT_LOCATION, ", "パスの指定を変える変数を引き継がない"),
    ("無い GIT_INDEX_FILE を見ない", "    if index_file is not None and not os.path.isfile(index_file):\n", "    if False:\n",
     "無い GIT_INDEX_FILE は判定しない"),
    # 置き場所の中の構造ファイルの綴り違い（#511）
    ("構造ファイルの綴り違いを見ない", "        problems.extend(misnamed_structured(root, files))\n", "",
     "置き場所の中の QA.csv は断る"),
    ("構造ファイルの綴りを畳まずに比べる", "        want = expected.get(fold(path))\n", "        want = expected.get(path)\n",
     "置き場所の中の QA-dev.csv は断る"),
    ("構造ファイルは綴りが同じでも断る", "        if want is not None and path != want:", "        if want is not None:",
     "全部の経路を重ねる"),
    # git の呼び方（#570・#572）
    ("相対の GIT_INDEX_FILE を docs から読む", "        index_file = str(top / index_file)", "        index_file = str(start / index_file)",
     "フックの相対の GIT_INDEX_FILE は根から読む"),
    ("GIT_INDEX_FILE を渡さない", '        env["GIT_INDEX_FILE"] = index_file\n', "        pass\n", "フックの一時の index の綴りで読む"),
    ("GIT_DIR を外さない", '("GIT_DIR", "GIT_WORK_TREE",', '("GIT_WORK_TREE",', "フックの相対の GIT_DIR を引き継がない"),
    ("rev-parse の失敗を外と読まない", '    if inside.returncode != 0 or inside.stdout.strip() != b"true":\n',
     '    if inside.stdout.strip() == b"false":\n', "上の壊れた .git は外と読む"),
    ("中身の無い .git でも中と読む", '    if inside.returncode != 0 or inside.stdout.strip() != b"true":\n',
     '    if inside.stdout.strip() == b"false":\n', "上の中身の無い .git は外と読む"),
    ("境界の向こうでも中と読む", '    if inside.returncode != 0 or inside.stdout.strip() != b"true":\n',
     '    if inside.stdout.strip() == b"false":\n', "発見が止まる境界の向こうの .git は外と読む"),
    ("git が無いとき上の .git を見ない", '        if any((d / ".git").exists() for d in (start, *start.parents)):\n',
     "        if False:\n", "git が無くて上に .git が在れば判定しない"),
    ("git が無ければいつも判定しない", '        if any((d / ".git").exists() for d in (start, *start.parents)):\n',
     "        if True:\n", "git が無くても .git が無ければ外と読む"),
    ("index をリポジトリの根からの綴りで引かない", '"ls-files", "-z", "--full-name", "--"', '"ls-files", "-z", "--"',
     "docs のフォルダの綴りが違っても index で断る"),
    ("docs の綴りを畳まずに index を引く", '":(top,icase)"', '":(top)"', "コミットの Docs/ を docs で読んでも index で断る"),
    ("docs と同じ項目かを見ない", "prefixes[head] = head == rel or same_entry(top.joinpath(*head), start)",
     "prefixes[head] = head == rel", "コミットの Docs/ を docs で読んでも index で断る"),
    ("版の名前を index に寄せない", "    for name in sorted(spelled(docs, index)):\n", "    for name in sorted(names(docs)):\n",
     "版のフォルダの古い綴りでも index の版として読む"),
    ("git の失敗を見ない", "    if proc.returncode != 0:\n", "    if False:\n", "git が失敗すれば判定しない"),
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
    ("内部の表を重ねない", '        for row in internal_rows:\n            self.internal[row["No"]] = row\n', "", "内部の表を行で重ねる"),
    ("内部の表をファイルとして写す", "STRUCTURED = [QA_PATH, INTERNAL_QA_PATH, SPEC_PATH]", "STRUCTURED = [QA_PATH, SPEC_PATH]",
     "内部の表をファイルとして消す"),
    # 層の判定（`check-qa-csv.py` の `is_internal_number`）を外す・入れ替える（#353）
    ("内部の行を消さない", "(self.internal if qa.is_internal_number(target) else self.qa)", "self.qa", "内部の行を removed.csv で消す"),
    ("共有の行を内部の表から消す", "(self.internal if qa.is_internal_number(target) else self.qa)", "self.internal", "Q&A を消す"),
    ("消す表の層を入れ替える", "(self.internal if qa.is_internal_number(target) else self.qa)",
     "(self.qa if qa.is_internal_number(target) else self.internal)", "内部の行を removed.csv で消す"),
    # 前の形（`D-001`）だけを内部と読む写しに戻す（#278）——前の形の試料は緑のままで、印つきの試料だけが赤になる
    ("印つきの内部の番号を内部と読まない", "(self.internal if qa.is_internal_number(target) else self.qa)",
     "(self.internal if target.startswith('D-') and target[2].isdigit() else self.qa)", "印つきの内部の行を removed.csv で消す"),
    ("行が 0 なら qa.csv を書かない", "(self.has_qa, QA_PATH, self.qa)", "(bool(self.qa), QA_PATH, self.qa)",
     "Q&A が全部消えても qa.csv を書く"),
    # 読めなさの原因を取り違える・想定外の例外（#286）
    ("権限で読めないのを UTF-8 と言う", '        raise Unreadable(f"{path}: 読めない（{e.strerror}）") from None\n    except UnicodeDecodeError:',
     '        raise Unreadable(f"{path}: UTF-8 として読めない") from None\n    except UnicodeDecodeError:', "読めない中間表現"),
    ("想定外の例外で前の出力を消さない", "    except Exception as e:  # 想定外の例外（巨大なセルの csv.Error",
     "    except ImportError as e:  # 想定外の例外（巨大なセルの csv.Error", "巨大なセル"),
    ("深い入れ子で前の出力を消さない", "    except Exception as e:  # 想定外の例外（巨大なセルの csv.Error",
     "    except csv.Error as e:  # 想定外の例外（巨大なセルの csv.Error", "深い入れ子"),
    ("書いている途中の想定外の例外で書きかけを残す", "    except Exception as e:  # 想定外の例外でも書きかけを残さない",
     "    except OSError as e:  # 想定外の例外でも書きかけを残さない", "書いている途中の想定外の例外"),
    ("入口で想定外の例外を 2 に寄せない", "    except Exception as e:  # 想定外の例外も「判定していない」（2）",
     "    except ImportError as e:  # 想定外の例外も「判定していない」（2）", "前の出力を消せないときの想定外の例外"),
]

# -OO（docstring が無い）で引数なしに呼んでも、使い方の誤りとして 2（#286）。(名前, 壊す前, 壊した後)
OO_MUTATIONS = [("-OO で docstring が無いと落ちる", "__doc__.splitlines()[2] if __doc__ else", "__doc__.splitlines()[2] if True else")]


def oo_problems(scripts: Path, cwd: Path) -> list[str]:
    proc = subprocess.run([sys.executable, "-I", "-OO", str(scripts / TARGET)], capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 2 or "usage:" not in proc.stderr or "Traceback" in proc.stderr:
        return [f"-OO の引数なし: 終了 {proc.returncode}: {proc.stderr[-300:]!r}"]
    return []

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
        elif isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    for path in locked:
        path.chmod(0)
    return locked


def snapshot(out: Path) -> dict[str, bytes] | None:
    if not out.is_dir() or not (out / ".merged-versions").is_file():
        return None
    return {p.relative_to(out).as_posix(): p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()}


# python 3.13 から `Path.resolve` はリンクの輪で投げなくなった（3.12 は RuntimeError）。試料はすべて 3.12 の振る舞いを
# 再現して走らせる——「辿るのに Path.resolve を使う」変異を、走らせた版によらず殺すため（#286 の P2-4・P2-6）。
# 3.12 では再現しなくても同じに投げる。輪かどうかは os.path.realpath(strict=True) の ELOOP で見る
RESOLVE_312 = '''
import errno, os, pathlib
_resolve = pathlib.Path.resolve
def _resolve_312(self, strict=False):
    try:
        os.path.realpath(self, strict=True)
    except OSError as e:
        if e.errno == errno.ELOOP:
            raise RuntimeError(f"Symlink loop from {str(self)!r}")
    return _resolve(self, strict)
pathlib.Path.resolve = _resolve_312
'''

# 本体を `__main__` として走らせる（入口の想定外の例外の捕捉もそのまま通る）
MAIN_DRIVER = RESOLVE_312 + '''
import runpy, sys
script = sys.argv[1]
sys.argv = [script, *sys.argv[2:]]
runpy.run_path(script, run_name="__main__")
'''

# 書き込みの口（`put`）を差し替えて、2 つ目の書き込みで失敗させる。"crash" は後始末の走らない落ち方（OSError でない）。
# "marker" は印を書きかけたところで失敗させる——用意された出力先の直下に書きかけのファイルが残る形を作る
FAIL_DRIVER = RESOLVE_312 + '''
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
        if mode == "unexpected":
            raise ValueError("試料")
        raise OSError(28, "No space left on device")
    real(dest, content)
module.put = put
sys.exit(module.main(sys.argv[3:]))
'''


def merge(scripts: Path, docs: Path, out: Path, extra: list[str], fail: str | None = None,
          env: dict[str, str] | None = None) -> tuple[int, str]:
    head = ["-c", FAIL_DRIVER, str(scripts / TARGET), fail] if fail else ["-c", MAIN_DRIVER, str(scripts / TARGET)]
    proc = subprocess.run([sys.executable, "-I", *head, str(docs), str(out), *extra],
                          capture_output=True, text=True, cwd=docs.parent, env={**os.environ, **(env or {})})
    return proc.returncode, proc.stdout + proc.stderr


# 区別しない FS でだけ・区別する FS でだけ作れる（判別できる）試料。もう片方の FS では試料を走らせず、殺す変異も当てない
CASE_FOLD_ONLY = {"コミットが綴り違いなら作業ツリーの綴りに依らず断る", "index の綴り違いは同じフォルダでも断る",
                  "コミットの Removed.csv は作業ツリーの綴りに依らず断る", "コミットの removed.csv は作業ツリーの綴りに依らず読む",
                  "docs のフォルダの綴りが違っても index で断る", "コミットの Docs/ を docs で読んでも index で断る",
                  "版のフォルダの古い綴りでも index の版として読む", "フックの相対の GIT_DIR を引き継がない",
                  "フックの一時の index の綴りで読む", "深い段の index の綴り違い 2 つはフォルダの綴り違い",
                  "2 段の index の綴り違いもフォルダの綴り違い", "別の綴りの版で追跡するファイルは取り込まない",
                  "index のファイル名の綴り違い 2 つは断る", "パスの指定を変える変数を引き継がない",
                  "深い段の綴りが作業ツリーで違っても index の綴りで読む", "構造ファイルの綴りが作業ツリーで違っても index の綴りで読む"}
# 試料はどの FS でも走るが、区別する FS では殺せない変異（作業ツリーの綴りのままでも、`.DS_Store` だけのフォルダは数えないので 0）
FOLD_ONLY_MUTATIONS = {"index を見ない"}
CASE_SENSITIVE_ONLY = {"別の項目の綴り違いは index に寄せない"}
fs_skips: list[str] = []
FOLDS: list[bool] = []
# git archive の書き出しでも重ねて、作業ツリーの答えと比べる試料（#569）
ARCHIVED = {"git-deep-stale", "git-structured-stale"}
# この環境変数が 1 なら、一時ディレクトリが大文字小文字を区別しない FS でなければ赤にする——CI の Linux で区別しない FS
# （ext4 の casefold）を用意して回すステップが、用意に失敗しても区別する FS で黙って緑にならないように（#571）
REQUIRE_CASE_FOLD = "MERGE_VERSIONS_TEST_REQUIRE_CASE_FOLD"


def case_insensitive(tmp: Path) -> bool:
    if not FOLDS:
        probe = tmp / "case-probe"
        probe.write_text("x", encoding="utf-8")
        FOLDS.append((tmp / "CASE-PROBE").exists())
    return FOLDS[0]


def git(root: Path, *args: str) -> None:
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args], cwd=root, env=env,
                   check=True, capture_output=True)


def rename(path: Path, name: str) -> None:
    """綴りだけ変える（区別しない FS では 2 段に分けないと変わらない）。"""
    path.rename(path.parent / "tmp-rename")
    (path.parent / "tmp-rename").rename(path.parent / name)


# index に足す綴りだけ違うパスと、区別しない FS で作業ツリーに書く場所（None なら書かない——同じファイルを開く）
BOTH = {"git-deep-both": ("v2/requirements/sub/b.md", "v2/requirements/Sub/b.md"),
        "git-deep-both-2": ("v2/requirements/sub/x/b.md", "v2/requirements/Sub/x/b.md"),
        "git-version-both": ("V2/requirements/b.md", "v2/requirements/b.md"),
        "git-file-both": ("v2/requirements/D.md", None)}


def prepare_git(root: Path, docs: Path, prepare: str) -> None:
    """本物の git リポジトリに試料をコミットしてから、作業ツリーのフォルダの綴りを変える（#276）。"""
    if prepare == "git-broken":  # docs の上の関係のない壊れた .git（#572）
        (root / ".git").write_text("gitdir: /nonexistent\n", encoding="utf-8")
        return
    if prepare == "git-empty-dotgit":  # docs の上の中身の無い .git（#572）
        (root / ".git").mkdir()
        return
    if prepare == "git-docs-upper":  # コミットのフォルダは Docs（試料は docs で打つ）
        docs.rename(root / "tmp-rename")
        (root / "tmp-rename").rename(root / "Docs")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "試料")
    v2 = docs / "v2"
    folds = case_insensitive(root.parent)
    if prepare == "git-stale" and folds:
        (v2 / "requirements").rename(v2 / "tmp-rename")
        (v2 / "tmp-rename").rename(v2 / "Requirements")
        (v2 / "Requirements" / ".DS_Store").write_text("x", encoding="utf-8")
    elif prepare == "git-stale":
        (v2 / "Requirements").mkdir()
        (v2 / "Requirements" / ".DS_Store").write_text("x", encoding="utf-8")
    elif prepare in ("git-docs-stale", "git-docs-upper") and folds:
        if prepare == "git-docs-stale":
            docs.rename(root / "tmp-rename")
            (root / "tmp-rename").rename(root / "Docs")
        (docs / "v2" / "Removed.csv").rename(docs / "v2" / "tmp-rename")
        (docs / "v2" / "tmp-rename").rename(docs / "v2" / "removed.csv")
    elif prepare == "git-version-stale" and folds:
        (docs / "v2").rename(docs / "tmp-rename")
        (docs / "tmp-rename").rename(docs / "V2")
        (docs / "V2" / ".DS_Store").write_text("x", encoding="utf-8")
    elif prepare == "git-renamed-file" and folds:
        name = next(p.name for p in v2.iterdir() if p.name.casefold() == "removed.csv")
        (v2 / name).rename(v2 / "tmp-rename")
        (v2 / "tmp-rename").rename(v2 / ("removed.csv" if name == "Removed.csv" else "Removed.csv"))
    elif prepare == "git-env-temp-index" and folds:  # 一時の index でだけ Requirements/ → requirements/ に改名（部分コミット）
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_INDEX_FILE": str(root / "idx")}
        shutil.copyfile(root / ".git" / "index", root / "idx")
        rename(v2 / "Requirements", "requirements")
        for args in (["rm", "-q", "--cached", "docs/v2/Requirements/d.md"], ["add", "docs/v2/requirements/d.md"]):
            subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)
    elif prepare in ("git-renamed", "git-env-dir", "git-env-literal") and folds:
        (v2 / "Requirements").rename(v2 / "tmp-rename")
        (v2 / "tmp-rename").rename(v2 / "requirements")
    elif prepare == "git-deep-stale" and folds:  # コミットは requirements/sub/d.md（#569）
        rename(v2 / "requirements" / "sub" / "d.md", "D.md")
        rename(v2 / "requirements" / "sub", "Sub")
    elif prepare == "git-structured-stale" and folds:  # コミットは shared/qa.csv（#569）
        rename(v2 / "shared" / "qa.csv", "QA.csv")
    elif prepare in BOTH and folds:  # index に綴りだけ違うパスを足す。区別しない FS では既に在るフォルダ（ファイル）に書かれる
        added, written = BOTH[prepare]
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        sha = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=root, env=env, input=b"B2\n",
                             check=True, capture_output=True).stdout.decode().strip()
        git(root, "update-index", "--add", "--cacheinfo", f"100644,{sha},docs/{added}")
        git(root, "commit", "-q", "-m", "綴り違い")
        if written is not None:
            (docs / written).write_bytes(b"B2\n")
    elif prepare == "git-index-corrupt":  # 作業ツリーの中なのに index を読めない（#572）
        (root / ".git" / "index").write_bytes(b"broken index\n")
    elif prepare == "git-env-index":  # 根から見れば正しい index の写し、docs から見れば壊れたファイル（#570）
        shutil.copyfile(root / ".git" / "index", root / "idx")
        (docs / "idx").write_bytes(b"x")
    elif prepare == "git-both":
        blob = (v2 / "shared" / "a.md").read_bytes()
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        sha = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=root, env=env, input=blob,
                             check=True, capture_output=True).stdout.decode().strip()
        git(root, "update-index", "--add", "--cacheinfo", f"100644,{sha},docs/v2/Shared/b.md")
    elif prepare == "git-alongside" and not folds:
        (v2 / "Requirements").mkdir()
        (v2 / "Requirements" / "x.md").write_text("X\n", encoding="utf-8")


def run_case(scripts: Path, root: Path, tree: dict, prepare: str, extra: list[str], twice: bool = False) -> Result:
    assert_in_tmp(root)
    docs = root / "docs"
    locked = build(docs, tree)
    if prepare.startswith("git-"):
        prepare_git(root, docs, prepare)
    # git を呼ぶ環境（#570・#572）。GIT_CEILING_DIRECTORIES は FS の境界の代わり——どちらも git が上へ辿るのを止める
    env = {"git-env-index": {"GIT_INDEX_FILE": "idx"}, "git-env-missing-index": {"GIT_INDEX_FILE": "nonexistent-idx"}, "git-env-temp-index": {"GIT_INDEX_FILE": "idx"}, "git-env-dir": {"GIT_DIR": ".git"}, "git-env-literal": {"GIT_LITERAL_PATHSPECS": "1"},
           "git-ceiling": {"GIT_CEILING_DIRECTORIES": os.path.realpath(root)},
           "git-missing": {"PATH": os.devnull}, "no-git": {"PATH": os.devnull}}.get(prepare)
    out = {"inside": docs / "merged", "docs": docs, "parent": root, "parent-loop": root,
           "out-loop": root / "loop" / "merged"}.get(prepare, root / "build" / "merged")
    preexisting = None
    if prepare == "parent":
        (root / ".merged-versions").write_text("前の出力\n", encoding="utf-8")
    elif prepare == "symlink":
        (root / "real").mkdir()
        out.parent.mkdir(parents=True)
        os.symlink(root / "real", out)
    elif prepare == "parent-loop":
        docs.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(docs, docs)
        (root / ".merged-versions").write_text("前の出力\n", encoding="utf-8")
        (root / "keep.md").write_text("消してはいけない\n", encoding="utf-8")
    elif prepare == "out-loop":
        os.symlink(out.parent, out.parent)
    elif prepare == "stale-loop":
        docs.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(docs, docs)
        out.mkdir(parents=True)
        (out / ".merged-versions").write_text("前の出力\n", encoding="utf-8")
        (out / "old.md").write_text("古い\n", encoding="utf-8")
    elif prepare in ("stale", "stale-locked"):
        out.mkdir(parents=True)
        (out / ".merged-versions").write_text("前の出力\n", encoding="utf-8")
        (out / "old.md").write_text("古い\n", encoding="utf-8")
    elif prepare == "foreign":
        out.mkdir(parents=True)
        (out / "keep.md").write_text("正本\n", encoding="utf-8")
    elif prepare in ("failwrite-empty", "marker-empty"):
        out.mkdir(parents=True)
    fail = {"failwrite": "oserror", "failwrite-empty": "oserror", "crash": "crash", "marker-empty": "marker",
            "failwrite-unexpected": "unexpected"}.get(prepare)
    if prepare == "stale-locked":
        out.parent.chmod(0o555)  # 前の出力（の中身）は消せても、出力先そのものは消せない
        try:
            code, output = merge(scripts, docs, out, extra, fail)
        finally:
            out.parent.chmod(0o755)
    else:
        code, output = merge(scripts, docs, out, extra, fail, env)
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
    archive = None
    if prepare in ARCHIVED:  # 同じコミットを git archive で書き出して重ねる——タグから写す側の答え（#569）
        exported = root.parent / f"{root.name}-archive"
        exported.mkdir()
        tar = subprocess.run(["git", "archive", "--format=tar", "HEAD", "docs"], cwd=root, check=True, capture_output=True,
                             env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as archive_file:
            archive_file.extractall(exported, filter="data")
        archive_code, _ = merge(scripts, exported / "docs", exported / "build" / "merged", extra)
        archive = (archive_code, snapshot(exported / "build" / "merged"))
    return Result(code, output, tree_out, preexisting, again, docs_intact, leftover, archive)


def skipped(name: str) -> bool:
    """root は mode 000 でも読めるので、読めない入力の試料を作れない。FS に依る試料は、作れない FS では飛ばす（#276）。"""
    if name in CASE_FOLD_ONLY | CASE_SENSITIVE_ONLY and FOLDS and FOLDS[0] == (name in CASE_SENSITIVE_ONLY):
        if name not in fs_skips:
            fs_skips.append(name)
        return True
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
          "**" + "・".join(f"`{path}`" for path in module.STRUCTURED) + " はファイルとしては消せない**" in text)
    check("重ねる置き場所が versions.md と違う",
          "（" + "・".join(f"`{a}/`" for a in module.AREAS) + "）" in text)
    check("出力先の印が versions.md と違う", f"（`{module.MARKER}`）" in text)
    check("removed.csv の名前が versions.md と違う", f"### 削除（`{module.REMOVED}`）" in text)


def main() -> int:
    check_reference()
    with tempfile.TemporaryDirectory(prefix="merge-versions-test-") as tmp:
        tmp_path = Path(tmp)
        case_insensitive(tmp_path)
        if os.environ.get(REQUIRE_CASE_FOLD) == "1" and not FOLDS[0]:
            check(f"{REQUIRE_CASE_FOLD}=1 なのに一時ディレクトリ（{tmp_path}）が大文字小文字を区別する（区別しない FS の試料を走らせていない）", False)
        if shutil.which("git") is None:
            check("git が無いので git の試料を走らせられない（緑ではない）", False)
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
            # 壊す箇所の数は FS に依らず見る——片方の FS でしか走らない変異の当て先が消えても、もう片方の FS で気づく
            # （PR #660 の 2 パス目で、区別しない FS で飛ばした変異の当て先が消えていたのを Linux の CI が見つけた）
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            if skipped(killer):
                continue
            if name in FOLD_ONLY_MUTATIONS and not FOLDS[0]:
                fs_skips.append(name)
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            killer_case = next(case for case in CASES if case[0] == killer)
            result = run_case(mutated, tmp_path / f"mutwork{index}", *killer_case[1:4])
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result.output[-300:])

        problems = oo_problems(scripts, tmp_path)
        check("-OO の引数なしで使い方の誤り（2）にならない", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(OO_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"oo-mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}", bool(oo_problems(mutated, tmp_path)))

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    skip = [name for name, *_ in CASES if skipped(name)]
    if skip:
        fs = [name for name in skip if name in fs_skips]
        if fs:
            print(f"飛ばした（この FS では作れない・判別できない。#276）: 試料 {'・'.join(fs)} と、それを名指しした変異")
        if len(fs) < len(skip):
            print(f"飛ばした（root では読めない入力を作れない）: 試料 {'・'.join(n for n in skip if n not in fs)} と、それを名指しした変異")
    lone = [name for name in fs_skips if name in FOLD_ONLY_MUTATIONS]
    if lone:
        print(f"飛ばした（区別する FS では殺せない。#276）: 変異 {'・'.join(lone)}")
    print(f"この一時ディレクトリの FS: 大文字小文字を{'区別しない' if FOLDS[0] else '区別する'}")
    print(f"OK: 試料 {len(CASES) - len(skip)} 件・変異 {sum(not skipped(m[3]) for m in MUTATIONS) - len(lone) + len(OO_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
