#!/usr/bin/env python3
"""`build-proposal.py`（照合が通ったときだけ提案書を作る）の回帰テスト。

    python3 scripts/test-build-proposal.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。照合そのものの分岐は
`scripts/test-check-signoff.py` が見る。ここで見るのは**生成の側が照合に従うこと**:

1. **照合が通らないとき、提案書を作らない**——一致しない（1）・照合していない（2）。
   **前に作った提案書とガントチャートも消す**（古いものを今のものと取り違えないため）。
2. **承認したタグの時点の中身から作る**——承認の後に直した見積り・Q&A 表は入らない。
   `docs/v<n>/feasibility/` は `signoff/v<n>/budget-<k>`、`docs/v<n>/shared/` は `signoff/v<n>/req-<k>` の時点。
   **版は照合が決めたもの**（省けば作業中の版・`--version` で指定）で、**その版の表と手書き部分だけ**が載る。
   **v2 以降で `qa.csv` を置かない版は Q&A 0 行で作り、v1 では `qa.csv` が無ければ作らない。**
3. **材料が欠けた・決まりに反するときも作らない**——手書き部分が無い・見積りが無い・見積りが決まりに反する。
4. **作れるときは作る**（陽性対照）——決定事項・未決定の質問・費用の合計・期間・ガントチャートが載り、
   手書き部分がファイル名の順に並ぶ。**同じ入力から同じバイト。**
5. **承認の記録を持たない**——「承認済み」と書かない。
6. **素の `v1` タグと共存する試料が、その `v1` を判別している**（#309）——承認のタグを #260 の名前
   （`v1/req-signoff-1`）にするとタグの手順で作れない。**本体は SHA で読むので `v1` に触れない**——
   判別しているのは本体の判定ではなく、試料の名前が素の `v1` と衝突しないこと（照合の側は
   `scripts/test-check-signoff.py` が同じ形で見る）。
7. **消すのは、印（`.build-proposal`）が名指しする前の出力だけ**（#397・#398・#405）——手で置いたファイルは
   失敗の経路でも消さず、作れる経路でも上書きしない（2）。印が同じ場所の外を名指ししても外は消さない。
   `--out` の誤り（`.`・`/`・`..`・ディレクトリ・名前の衝突）は traceback ではなく 2 で、それでも印の名指しする前の出力は消す。
   **陽性対照は本物の前の実行**——試料の前の出力は印を手で書くので、本体が印に何を載せるかはそこでしか見えない。

**このテストは実環境を触らない。** 試料の git リポジトリはすべて一時ディレクトリに作り、
`HOME` と `GIT_CONFIG_GLOBAL` を差し替える。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "build-proposal.py"

QA = "docs/v1/shared/qa.csv"
SCHEDULE = "docs/v1/feasibility/schedule.csv"
ESTIMATE = "docs/v1/feasibility/estimate.csv"
R1, B1 = "signoff/v1/req-1", "signoff/v1/budget-1"
QA_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
QA_ROWS = (
    "Q-001,要求確定,割引は？,A: なし / B: 3%,A,理由,A（業務部が回答）,決定表 4 行目,反映済み,\n"
    "Q-005,実現性・コスト,夜間は止めてよいか,A: 止まってよい / B: 24 時間,A,理由,未回答,—,確認中,B は月額が約 2 倍\n"
)
SCHEDULE_CSV = "No,工程,開始,終了,前提\nT-001,要件定義,2026-11-02,2026-11-27,\nT-002,基本設計,2026-11-30,2026-12-25,T-001\n"
NFC_E, NFD_E = "é", "é"  # é の NFC と NFD


def estimate(amount: str) -> str:
    return f"No,区分,項目,金額,根拠\nE-001,開発費,画面の開発,{amount},12 画面\nE-002,運用費（月額）,サーバ,120000,Q-005\n"


BASE = [("w", QA, QA_HEAD + QA_ROWS), ("w", SCHEDULE, SCHEDULE_CSV), ("w", ESTIMATE, estimate("4800000")),
        ("w", "docs/v1/proposal/02-recommendation.md", "## 推奨案\n\n案 B を推す。\n"),
        ("w", "docs/v1/proposal/01-background.md", "## 背景と目的\n\n受注を自動化する。\n"), ("c",)]
SIGNED = BASE + [("t", R1), ("t", B1)]
# v2: その版の差分だけを置き、v2 のタグで承認する（v1 は凍結したまま）
V2 = SIGNED + [("w", "docs/v2/shared/qa.csv", QA_HEAD + "Q-006,要求確定,返品は？,A: 可 / B: 不可,A,理由,A,決定表 9 行目,反映済み,\n"),
               ("w", "docs/v2/feasibility/schedule.csv", SCHEDULE_CSV),
               ("w", "docs/v2/feasibility/estimate.csv", estimate("700000")),
               ("w", "docs/v2/proposal/01-change.md", "## 変更の背景\n\n返品を受け付ける。\n"), ("c",),
               ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")]
# 前の版との比較: v1 に要求・機能を足して承認し、v2 で Q&A・機能・ファイルをそれぞれ足し・変え・消し、置き直す
SPEC_V1 = '{"title": "注文", "features": [{"id": "F-001", "title": "割引"}, {"id": "F-002", "title": "送料"}]}'
SPEC_V2 = '{"features": [{"id": "F-002", "title": "送料（離島）"}, {"id": "F-003", "title": "返品"}]}'
SIGNED_R = BASE[:-1] + [("w", "docs/v1/requirements/a.md", "A\n"), ("w", "docs/v1/requirements/b.md", "B\n"),
                        ("w", "docs/v1/requirements/same.md", "S\n"), ("w", "docs/v1/spec/spec_ir.json", SPEC_V1),
                        ("c",), ("t", R1), ("t", B1)]
V2_CHANGES = [
    ("w", "docs/v2/shared/qa.csv", QA_HEAD + QA_ROWS.splitlines(True)[0].replace("A（業務部が回答）", "B（業務部が回答）")
     + "Q-006,要求確定,返品は？,A: 可 / B: 不可,A,理由,A,決定表 9 行目,反映済み,\n"),
    ("w", "docs/v2/removed.csv", "種類,対象,理由\nQ&A,Q-005,夜間の停止を決めた\nファイル,requirements/b.md,a.md に統合した\n"
     "機能,F-001,割引を廃止した\n"),
    ("w", "docs/v2/requirements/a.md", "A2\n"), ("w", "docs/v2/requirements/c.md", "C\n"),
    ("w", "docs/v2/requirements/same.md", "S\n"), ("w", "docs/v2/spec/spec_ir.json", SPEC_V2),
    ("w", "docs/v2/feasibility/schedule.csv", SCHEDULE_CSV), ("w", "docs/v2/feasibility/estimate.csv", estimate("700000")),
    ("w", "docs/v2/proposal/01-change.md", "## 変更の背景\n\n返品を受け付ける。\n")]
V2C = SIGNED_R + V2_CHANGES + [("c",), ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")]


# 仕様書（#374）の試料: v1 に決定表・範囲の文書・図（書き出しあり／なし）・仕様書の手書き部分を足して承認する
DECISION = "docs/v1/shared/decision_table.csv"
SCOPE_MD = "# 範囲\n\n## 線\n\n既定の線\n\n## 範囲の外\n\n| 場面 | 原則 |\n| --- | --- |\n| ディスクがいっぱい | 失敗を見せる |\n\n## 付録\n\n付録の本文\n"
SVG = '<svg xmlns="http://www.w3.org/2000/svg"><text>構成</text></svg>\n'
SPEC_STEPS = [("w", DECISION, "会員,金額,割引\nシルバー,10000 未満,0%\nゴールド,すべて,5%\n"),
              ("w", "docs/v1/spec/scope.md", SCOPE_MD), ("w", "docs/v1/spec/a.md", "仕様 A\n"),
              ("w", "docs/v1/spec/arch.drawio.svg", SVG), ("w", "docs/v1/shared/chart.svg", SVG), ("w", "docs/v1/requirements/flow.drawio", "<mxfile/>\n"),
              ("w", "docs/v1/proposal/spec/01-notes.md", "## 試作で確かめること\n\n読み取りの速さ。\n")]
SIGNED_S = BASE[:-1] + SPEC_STEPS + [("c",), ("t", R1), ("t", B1)]
# 回答に「暫定で採用」と書いて反映済みにした行（#366 の実データの形）と、確認中のまま「暫定で採用」と書いた行。
# 暫定は `状態` だけで決まる（#404）——前者は確定の行、後者は未決定の質問
PROVISIONAL_QA = (QA_HEAD + QA_ROWS.replace("A（業務部が回答）", "A（推奨案を暫定で採用。開発側の指示）")
                  + "Q-007,要求確定,返品は？,A: 可 / B: 不可,A,理由,B（暫定で採用の予定）,—,確認中,\n")
PROVISIONAL = [("w", QA, PROVISIONAL_QA)] + BASE[1:] + [("t", R1), ("t", B1)]
# 回答に肯定の書き方で「暫定で採用します」と書いた行——状態が `反映済み` なので確定の行（文言は見ない。#404）
AFFIRMED = [("w", QA, QA_HEAD + QA_ROWS.replace("A（業務部が回答）", "A を暫定で採用します（業務部の確認待ち）"))] + BASE[1:] + [("t", R1), ("t", B1)]
# 確定した回答が暫定の経緯に触れただけの行（否定・取り下げの書き方が続く）——確定の行
SETTLED = [("w", QA, QA_HEAD + QA_ROWS.replace("A（業務部が回答）", "A（暫定で採用していた B を取り下げ、業務部が A に決定）"))] + BASE[1:] + [("t", R1), ("t", B1)]
STALE = ["proposal.md", "gantt.svg", "spec.md", "spec.pptx", "spec-figure-01.svg"]
# 出力と同じ場所に本体が置く印（#405）。試料の「前の出力」は、本体が書くのと同じ形の印と一緒に置く
MANIFEST = ".build-proposal"
# 手で置いたファイル（印に無い）。前 3 つは出力と同じ名前、最後は出力と関係の無い名前（#397）
HAND = ["proposal.md", "spec.md", "spec-figure-01.svg", "notes.md"]
HAND_TEXT = "手書き\n"
FIGURE_NOTE = "PPTX に載せていない"


class Result:
    def __init__(self, code: int | None, output: str, text: str | None, svg: bool, again: str | None,
                 spec: str | None = None, names: frozenset = frozenset(), pptx: dict | None = None,
                 again_pptx: dict | None = None, again_spec: str | None = None, directory: Path | None = None):
        self.code, self.output, self.text, self.svg, self.again = code, output, text, svg, again
        # 出力の場所に残ったファイル（名前 → 中身。印も含む）
        self.files = ({p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
                      if directory is not None and directory.is_dir() else {})
        self.spec, self.names, self.again_spec = spec, names, again_spec
        self.pptx, self.again_pptx = pptx or {}, again_pptx or {}


def made(r: Result) -> bool:
    return r.code == 0 and r.text is not None and r.svg and r.spec is not None


def not_made(code: int) -> Callable[[Result], bool]:
    # 提案書だけでなく、仕様書・PPTX・図も 1 つも無い
    return lambda r: (r.code == code and r.text is None and not r.svg and r.spec is None and not r.names
                      and "提案書は作っていない" in r.output)


def section(text: str, head: str) -> str:
    """`head` の行から次の `#`・`##`・`###` の見出しまで。"""
    start = text.find(head)
    if start < 0:
        return ""
    end = re.search(r"^#{1,3} ", text[start + len(head):], re.M)
    return text[start:start + len(head) + (end.start() if end else len(text))]


def pptx_text(parts: dict) -> str:
    return "".join(re.findall(r"<a:t>([^<]*)</a:t>", "".join(v for k, v in sorted(parts.items()) if k.startswith("ppt/slides/slide"))))


def slide_texts(parts: dict) -> list[str]:
    """スライドごとの文字（スライドの番号の順）。"""
    names = sorted((k for k in parts if re.fullmatch(r"ppt/slides/slide\d+\.xml", k)), key=lambda k: int(re.sub(r"\D", "", k)))
    return ["".join(re.findall(r"<a:t>([^<]*)</a:t>", parts[k])) for k in names]


def collided(r: Result) -> bool:
    return r.code == 2 and "同じ名前になる" in r.output and r.text is None and r.spec is None and not r.names


def hand_kept(r: Result) -> bool:
    """手で置いたファイルが 1 つも消えず、書き換わってもいない（#397）。"""
    return all(r.files.get(name) == HAND_TEXT.encode("utf-8") for name in HAND)


def bad_out(word: str) -> Callable[[Result], bool]:
    # 引数の誤りは traceback ではなく 2（#398）
    return lambda r: r.code == 2 and word in r.output and "Traceback" not in r.output and "提案書は作っていない" in r.output


def pptx_ok(parts: dict) -> bool:
    """部品が揃い、XML がすべて整形式（開けるかは見ない——未証明）。"""
    import xml.dom.minidom
    need = {"[Content_Types].xml", "ppt/presentation.xml", "ppt/slides/slide1.xml"}
    if not need <= set(parts):
        return False
    try:
        for name, body in parts.items():
            if name.endswith(".xml") or name.endswith(".rels"):
                xml.dom.minidom.parseString(body.encode("utf-8"))
    except Exception:
        return False
    return True


# (名前, 手順, 前の出力を置くか, 判定)
CASES: list[tuple[str, list[tuple[str, ...]], bool, Callable[[Result], bool]]] = [
    ("作れるときは作る", SIGNED, False,
     lambda r: made(r) and "## 主な決定事項" in r.text and "| Q-001 | 割引は？ |" in r.text
     and "| 開発費 | 4,800,000 |" in r.text and "| 運用費（月額） | 120,000 |" in r.text
     and "2026-11-02 〜 2026-12-25" in r.text and "![ガントチャート](gantt.svg)" in r.text),
    ("未決定の質問を載せる", SIGNED, False,
     lambda r: made(r) and "承認の時点で未決定の質問（1 件）" in r.text and "| Q-005 |" in r.text),
    ("手書き部分はファイル名の順", SIGNED, False,
     lambda r: made(r) and 0 < r.text.find("## 背景と目的") < r.text.find("## 推奨案")),
    ("同じ入力から同じバイト", SIGNED, False, lambda r: made(r) and r.text == r.again),
    # 本体の判定は v1 に触れない。この試料が判別するのは名前の衝突で、OLD_NAMES で当てる（#309）
    ("素の v1 タグと共存する", BASE + [("t", "v1"), ("t", R1), ("t", B1)], False,
     lambda r: made(r) and "`signoff/v1/req-1`" in r.text),
    ("承認の記録を持たない", SIGNED, False, lambda r: made(r) and "承認済み" not in r.text and "承認の記録ではありません" in r.text),
    # 予算のタグは見積りを直した後、作業ツリーはさらにその後に直している
    ("承認したタグの時点の見積り", BASE + [("t", R1), ("w", ESTIMATE, estimate("5000000")), ("c",),
                                    ("t", B1), ("w", ESTIMATE, estimate("9999999")), ("c",)], False,
     lambda r: made(r) and "5,000,000" in r.text and "9,999,999" not in r.text and "4,800,000" not in r.text),
    ("承認の後に直した Q&A 表は入らない", SIGNED + [("w", QA, QA_HEAD + QA_ROWS.replace("割引は？", "割引は本当に？")), ("c",)],
     False, lambda r: made(r) and "割引は？" in r.text and "割引は本当に？" not in r.text),
    ("一致しないと作らない", BASE + [("t", R1), ("w", QA, QA_HEAD), ("c",), ("t", B1)],
     False, not_made(1)),
    ("前の提案書を消す", BASE + [("t", R1), ("w", QA, QA_HEAD), ("c",), ("t", B1)],
     True, lambda r: not_made(1)(r) and r.output.count("前に作った出力を消した") == len(STALE)),
    ("照合していないと作らない", BASE, True, not_made(2)),
    # 要求確定の時点に暫定の回答が残る（#325）——照合の 3 をそのまま返し、前の出力も消す
    ("暫定の回答が残ると作らない",
     [("w", QA, QA_HEAD + QA_ROWS.replace("A（業務部が回答）,決定表 4 行目,反映済み",
                                          "A（推奨案を暫定で採用。業務部 2026-10-21 の指示）,決定表 4 行目,暫定反映"))]
     + BASE[1:] + [("t", R1), ("t", B1)],
     True, lambda r: not_made(3)(r) and "暫定の回答（暫定反映）が 1 件残る" in r.output
     and r.output.count("前に作った出力を消した") == len(STALE)),
    ("見積りが決まりに反すると作らない", BASE[:2] + [("w", ESTIMATE, estimate('"4,800,000"'))] + BASE[3:]
     + [("t", R1), ("t", B1)], False, not_made(1)),
    ("見積りが無いと作らない", [s for s in SIGNED if s[:2] != ("w", ESTIMATE)], False,
     lambda r: not_made(1)(r) and "承認の時点に無い" in r.output),
    ("手書き部分が無いと作らない", [s for s in SIGNED if not (len(s) > 1 and s[1].startswith("docs/v1/proposal/"))],
     False, lambda r: not_made(1)(r) and "手書き部分" in r.output),
    # ---- 版
    ("作業中の版から作る", V2, False,
     lambda r: made(r) and "| Q-006 | 返品は？ |" in r.text and "Q-001" not in r.text and "700,000" in r.text
     and "4,800,000" not in r.text and "## 変更の背景" in r.text and "## 推奨案" not in r.text
     and "`docs/v2/shared/`" in r.text and "`signoff/v2/req-1`" in r.text),
    ("版を指定して作る", V2 + [("arg", "--version", "1")], False,
     lambda r: made(r) and "| Q-001 | 割引は？ |" in r.text and "Q-006" not in r.text and "`docs/v1/shared/`" in r.text),
    # v2 の手書き部分が無い——v1 の手書き部分で代わりに作らない
    ("作業中の版の手書き部分が無いと作らない",
     [s for s in V2 if not (len(s) > 1 and s[1].startswith("docs/v2/proposal/"))], False,
     lambda r: not_made(1)(r) and "docs/v2/proposal" in r.output),
    # v2 以降は差分だけ——Q&A を足さない版は qa.csv を置かない（versions.md）。それでも作れる
    ("Q&A を足さない版でも作る", [s for s in V2 if not (len(s) > 1 and s[1] == "docs/v2/shared/qa.csv")]
     + [("w", "docs/v2/requirements/returns.md", "x\n"), ("c",), ("t", "signoff/v2/req-2"), ("t", "signoff/v2/budget-2")],
     False, lambda r: made(r) and "（反映済みの決定事項はありません）" in r.text and "Q-001" not in r.text
     and "700,000" in r.text),
    # v1 は qa.csv が要る（v2 以降の扱いを v1 に広げない）
    ("v1 は Q&A 表が無いと作らない", [s for s in SIGNED if s[:2] != ("w", QA)]
     + [("w", "docs/v1/shared/nfr.csv", "x\n"), ("c",), ("t", "signoff/v1/req-2"), ("t", "signoff/v1/budget-2")],
     False, lambda r: not_made(1)(r) and "docs/v1/shared/qa.csv: 承認の時点に無い" in r.output),
    # ---- 前の版との比較（v2 以降）
    ("前の版との比較を載せる", V2C, False,
     lambda r: made(r) and "## 前の版（v1）からの変更" in r.text
     and "| Q&A | 1 | 1 | 1 |" in r.text and "| 機能 | 1 | 1 | 1 |" in r.text and "| ファイル | 1 | 1 | 1 |" in r.text
     and "| Q-001 | 変更 | 割引は？ | A（業務部が回答） | B（業務部が回答） | — |" in r.text
     and "| Q-006 | 追加 | 返品は？ | — | A | — |" in r.text
     and "| Q-005 | 削除 | 夜間は止めてよいか | 未回答 | — | 夜間の停止を決めた |" in r.text
     and "| F-002 | 変更 | 送料（離島） | — |" in r.text and "| F-003 | 追加 | 返品 | — |" in r.text
     and "| F-001 | 削除 | 割引 | 割引を廃止した |" in r.text
     and "| requirements/a.md | 変更 | — |" in r.text and "| requirements/c.md | 追加 | — |" in r.text
     and "| requirements/b.md | 削除 | a.md に統合した |" in r.text
     and "same.md" not in r.text
     and "この版（v2）の差分の見積り" in r.text
     and r.text.find("## 変更の背景") < r.text.find("## 前の版（v1）からの変更") < r.text.find("## 主な決定事項")),
    ("比較も同じ入力から同じバイト", V2C, False, lambda r: made(r) and r.text == r.again),
    ("足しただけの版は追加だけを載せる", V2, False,
     lambda r: made(r) and "| Q&A | 1 | 0 | 0 |" in r.text and "### Q&A" in r.text and "### 機能" not in r.text),
    ("変更が無い版", SIGNED + [("w", "docs/v2/feasibility/schedule.csv", SCHEDULE_CSV),
                             ("w", "docs/v2/feasibility/estimate.csv", estimate("700000")),
                             ("w", "docs/v2/proposal/01-change.md", "## 変更の背景\n\n見直しだけ。\n"), ("c",),
                             ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: made(r) and "（前の版からの変更はありません）" in r.text),
    # 比較は req のタグの時点から作る——承認の後に作業ツリーとコミットで足した要求は載らない
    ("承認の後に直した差分は比較に入らない", V2C + [("w", "docs/v2/requirements/late.md", "L\n"), ("c",)], False,
     lambda r: made(r) and "| requirements/c.md | 追加 |" in r.text and "late.md" not in r.text),
    # 比較は req のタグの時点から作る——2 つのタグの間で removed.csv の理由の列だけを変える（照合は理由を比べないので通る。
    # 提案書の「削除の理由」は req のタグの時点のもの）。#375 で一度「等価変異」として外し、関門に反証された
    ("比較は要求のタグの時点から作る", SIGNED_R + V2_CHANGES + [("c",), ("t", "signoff/v2/req-1"),
                                    ("w", "docs/v2/removed.csv", "種類,対象,理由\nQ&A,Q-005,予算側でだけ書き換えた理由\n"
                                     "ファイル,requirements/b.md,a.md に統合した\n機能,F-001,割引を廃止した\n"),
                                    ("c",), ("t", "signoff/v2/budget-1")], False,
     lambda r: made(r) and "夜間の停止を決めた" in r.text and "予算側でだけ書き換えた理由" not in r.text),
    # req のタグと budget のタグの間に要求を足すと、照合が 1 で止める（#375。見積りの根拠が承認と違う）
    ("2 つのタグの間に要求を足すと照合で止まる", SIGNED_R + V2_CHANGES + [("c",), ("t", "signoff/v2/req-1"),
                                             ("w", "docs/v2/requirements/between.md", "B\n"), ("c",), ("t", "signoff/v2/budget-1")], False,
     lambda r: not_made(1)(r) and "docs/v2/requirements/between.md" in r.output),
    # 大文字小文字だけ違うパスは写す前に断る——区別しない FS では上書きし合い、先に置いたリンクを辿って外に書きうる
    ("大文字小文字だけ違うパスは比較で断る", V2C[:-3] + [("i", "docs/v2/requirements/C.md", "100644", "X\n"), ("c",),
                                          ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: not_made(1)(r) and "写すと同じ場所に書かれる" in r.output and "requirements/C.md" in r.output),
    ("リンクと大文字小文字だけ違うファイルは比較で断る", V2C[:-3] + [("i", "docs/v2/requirements/L", "120000", "x"),
                                                    ("i", "docs/v2/requirements/l", "100644", "OVER\n"), ("c",),
                                                    ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: not_made(1)(r) and "写すと同じ場所に書かれる" in r.output),
    ("ファイルとディレクトリが大文字小文字だけ違うと比較で断る", V2C[:-3] + [("i", "docs/v2/requirements/D", "100644", "X\n"),
                                                           ("i", "docs/v2/requirements/d/y.md", "100644", "Y\n"), ("c",),
                                                           ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: not_made(1)(r) and "ファイルとディレクトリの両方" in r.output and "写すと同じ場所に書かれる" in r.output),
    # ファイル名は違ってもディレクトリだけが大文字小文字違い——区別しない FS では片方のディレクトリに寄り、git に無いパスが載る
    ("ディレクトリが大文字小文字だけ違うと比較で断る", V2C[:-3] + [("i", "docs/v2/requirements/Dir/a.md", "100644", "A\n"),
                                                      ("i", "docs/v2/requirements/dir/b.md", "100644", "B\n"), ("c",),
                                                      ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: not_made(1)(r) and "ディレクトリ" in r.output and "requirements/dir" in r.output
     and "写すと同じ場所に書かれる" in r.output),
    # 大文字小文字ではなく Unicode の正規化（NFC/NFD）だけが違うディレクトリ——macOS の FS では同じ場所になる。
    # 出力に NFD の綴りが出ることまで見る（索引で NFC に潰れていれば衝突が起きず、提案書が作られて赤になる）
    ("ディレクトリが正規化だけ違うと比較で断る", V2C[:-3] + [("i", f"docs/v2/requirements/x/{NFC_E}/a.md", "100644", "A\n"),
                                                    ("i", f"docs/v2/requirements/x/{NFD_E}/b.md", "100644", "B\n"), ("c",),
                                                    ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: not_made(1)(r) and f"requirements/x/{NFD_E}" in r.output and f"requirements/x/{NFC_E}" in r.output
     and "写すと同じ場所に書かれる" in r.output),
    # 重ね合わせが読まないもの（版の外・版の中の重ねない置き場所）は写さない——そこで並んでも比較は作れる
    ("重ね合わせが読まないものは写さない", V2C[:-3] + [("i", "docs/notes/A.md", "100644", "X\n"), ("i", "docs/notes/a.md", "100644", "Y\n"),
                                              ("i", "docs/v2/proposal/N.md", "100644", "X\n"), ("i", "docs/v2/proposal/n.md", "100644", "Y\n"),
                                              ("c",), ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: made(r) and "| requirements/c.md | 追加 |" in r.text),
    # 内部の層の Q&A（spec/qa-dev.csv の D-）は決裁者に見せない——比較の節にも件数にも入れない（#339）
    ("内部の Q&A は比較に載せない", V2C[:-3] + [("w", "docs/v2/spec/qa-dev.csv", QA_HEAD
                                             + "D-001,仕様レビュー,ワーカーを分けるか,A: 分ける / B: 分けない,B,費用,B（開発）,spec/a.md,反映済み,\n"),
                                            ("c",), ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: made(r) and "D-001" not in r.text and "ワーカーを分けるか" not in r.text and "| Q&A | 1 | 1 | 1 |" in r.text
     and "Q&A（内部）" not in r.text),
    # 内部の表は比べる前に外す——内部の表の決まりの違反（`暫定反映`・前の版に無い D- を消す）でも、照合と同じく提案書は作れる
    ("内部の表の違反でも比較を作る", V2C[:-3] + [("w", "docs/v2/spec/qa-dev.csv", QA_HEAD
                                               + "D-001,仕様レビュー,ワーカーを分けるか,A: 分ける / B: 分けない,B,費用,B（開発）,spec/a.md,暫定反映,\n"),
                                              ("w", "docs/v2/removed.csv", "種類,対象,理由\nQ&A,Q-005,夜間の停止を決めた\n"
                                               "ファイル,requirements/b.md,a.md に統合した\n機能,F-001,割引を廃止した\nQ&A,D-009,共有へ移した（Q-007）\n"),
                                              ("c",), ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: made(r) and "D-00" not in r.text and "| Q&A | 1 | 1 | 1 |" in r.text),
    # 前の版（v1）の内部の表も比べる前に外す——v1 の内部の表の違反（`暫定反映`）で比較が作れなくならない（#343）
    ("前の版の内部の表の違反でも比較を作る",
     SIGNED_R[:-3] + [("w", "docs/v1/spec/qa-dev.csv", QA_HEAD
                       + "D-001,仕様レビュー,ワーカーを分けるか,A: 分ける / B: 分けない,B,費用,B（開発）,spec/a.md,暫定反映,\n"),
                      ("c",), ("t", R1), ("t", B1)] + V2_CHANGES + [("c",), ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")],
     False, lambda r: made(r) and "D-001" not in r.text and "| Q&A | 1 | 1 | 1 |" in r.text),
    ("v1 は比較の節を持たない", SIGNED_R, False,
     lambda r: made(r) and "前の版" not in r.text and "差分の見積り" not in r.text),
    # 重ね合わせが作れない（前の版に無いものを消す）——比較を作れないので書かない
    ("比較を作れないと作らない", SIGNED_R + [s if s[:2] != ("w", "docs/v2/removed.csv")
                                    else ("w", "docs/v2/removed.csv", "種類,対象,理由\n機能,F-999,誤記\n")
                                    for s in V2_CHANGES] + [("c",), ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")],
     False, lambda r: not_made(1)(r) and "前の版との比較を作れない" in r.output and "F-999" in r.output),
    ("版の中のシンボリックリンクは比較で断る", V2C[:-2] + [("l", "docs/v2/requirements/link.md", "../../v1/requirements/a.md"), ("c",),
                                              ("t", "signoff/v2/req-1"), ("t", "signoff/v2/budget-1")], False,
     lambda r: not_made(1)(r) and "シンボリックリンク" in r.output and "link.md" in r.output),
    # ---- 暫定の回答（#366。判別は check-qa-csv.py の is_provisional——`状態` だけで決める。#404）
    # `反映済み` に「暫定で採用」と書いた行は確定の行——主な決定事項に載り、暫定の節は 0 件（暫定反映 の行は照合の 3 で作らない）
    ("文言だけ暫定の反映済みは決定事項に載せる", PROVISIONAL, False,
     lambda r: made(r) and "| Q-001 | 割引は？ | A（推奨案を暫定で採用。開発側の指示） |" in section(r.text, "## 主な決定事項")
     and "（ありません）" in section(r.text, "## 利用者にまだ確かめていない決定（0 件）")),
    # 確認中の行は「暫定で採用」と書いてあっても反映していない——未決定の質問に載り、暫定の節には載らない
    ("確認中の行は暫定にしない", PROVISIONAL, False,
     lambda r: made(r) and "| Q-007 |" in section(r.text, "## 承認の時点で未決定の質問（2 件）")
     and "Q-007" not in section(r.text, "## 利用者にまだ確かめていない決定")),
    # 陽性対照: 確定の書き方の反映済みの行は決定事項に載り、暫定の節は 0 件
    ("確定した行は暫定にしない", SIGNED, False,
     lambda r: made(r) and "| Q-001 | 割引は？ |" in section(r.text, "## 主な決定事項")
     and "（ありません）" in section(r.text, "## 利用者にまだ確かめていない決定（0 件）")),
    ("否定・取り下げの書き方は暫定にしない", SETTLED, False,
     lambda r: made(r) and "| Q-001 | 割引は？ |" in section(r.text, "## 主な決定事項")
     and "（ありません）" in section(r.text, "## 利用者にまだ確かめていない決定（0 件）")),
    ("肯定の書き方も文言では暫定にしない", AFFIRMED, False,
     lambda r: made(r) and "| Q-001 | 割引は？ |" in section(r.text, "## 主な決定事項")
     and "（ありません）" in section(r.text, "## 利用者にまだ確かめていない決定（0 件）") and "前の版までの" not in r.text),
    # v2 以降の暫定の節は、その版の Q&A だけを見ていると言う（前の版の暫定の行は載せない——D2）
    ("v2 の暫定の節はこの版の Q&A と書く", V2C, False,
     lambda r: made(r) and "## この版の Q&A で利用者にまだ確かめていない決定（" in r.text
     and "前の版までの Q&A の暫定の行はここに載らない" in r.text),
    # PPTX は `##` ごとにスライドを分ける——暫定の節が「主な決定事項」の題のスライドに載らない
    ("暫定の節は決定事項のスライドと分ける", SIGNED + [("arg", "--pptx")], False,
     lambda r: made(r) and any("利用者にまだ確かめていない決定" in t for t in slide_texts(r.pptx.get("proposal.pptx", {})))
     and not any("主な決定事項" in t and "利用者にまだ確かめていない決定" in t
                 for t in slide_texts(r.pptx.get("proposal.pptx", {})))),
    ("承認の後に書き足した暫定は載らない", SIGNED + [("w", QA, PROVISIONAL_QA), ("c",)], False,
     lambda r: made(r) and "## 利用者にまだ確かめていない決定（0 件）" in r.text and "Q-007" not in r.text),
    # ---- 仕様書（#371）
    ("仕様書を作る", SIGNED_S, False,
     lambda r: made(r) and "[spec.md](spec.md)" in r.text and "[proposal.md](proposal.md)" in r.spec
     and "`signoff/v1/req-1`" in r.spec and "承認の記録ではありません" in r.spec
     and "## 試作で確かめること" in r.spec
     and "| 決定表の行（見出しを除く） | 2 |" in r.spec and "| Q&A（共有。v1 から重ねた全体） | 2（決定 1・暫定 0・未決定 1） |" in r.spec
     and "| 会員 | 金額 | 割引 |" in r.spec and "| ゴールド | すべて | 5% |" in r.spec
     and "| ディスクがいっぱい | 失敗を見せる |" in section(r.spec, "## 範囲の外") and "付録の本文" not in r.spec
     and "![spec/arch.drawio.svg](spec-figure-01.svg)" in r.spec and "spec-figure-01.svg" in r.names
     and "- `requirements/flow.drawio`" in r.spec and "| 図 | 1（書き出しが無いので載せていない図 1） |" in r.spec
     and "—（中間表現が無い）" in r.spec and "| spec/a.md |" in r.spec and not r.pptx),
    # `Spec.html` は PPTX が `Spec.pptx`——仕様書の PPTX と大文字小文字だけ違う（区別しない FS では同じファイル）
    ("出力の名前が仕様書の PPTX と重なると作らない", SIGNED + [("out", "Spec.html"), ("arg", "--pptx")], False,
     collided),
    ("出力の名前がガントチャートと重なると作らない", SIGNED + [("out", "Gantt.svg")], False, collided),
    ("出力が PPTX の名前だと作らない", SIGNED + [("out", "proposal.pptx"), ("arg", "--pptx")], False, collided),
    ("出力の名前が図と重なると作らない", SIGNED + [("out", "spec-figure-01.md")], False, collided),
    ("出力の名前が印と重なると作らない", SIGNED + [("out", MANIFEST)], False, collided),
    # ---- 何を消すか（#397・#398・#405）
    # 印に無いファイルは、名前が出力と同じでも消さない——失敗の経路でも、作れる経路でも
    ("手で置いたファイルは作れないときも消さない", BASE + [("t", R1), ("w", QA, QA_HEAD), ("c",), ("t", B1)], "hand",
     lambda r: r.code == 1 and hand_kept(r) and "前に作った出力を消した" not in r.output),
    ("手で置いたファイルを上書きしない", SIGNED, "hand",
     lambda r: r.code == 2 and hand_kept(r) and "上書きしない" in r.output and not r.svg and MANIFEST not in r.files
     and set(r.files) == set(HAND)),
    # 手で置いたのが仕様書だけでも上書きしない——提案書の名前だけ見る検査を判別する（#405 の 2 パス目）
    ("手で置いた仕様書だけでも上書きしない", SIGNED, "handspec",
     lambda r: r.code == 2 and "上書きしない" in r.output and r.files == {"spec.md": HAND_TEXT.encode("utf-8")}),
    # 印が同じ場所の外を名指ししても、外は消さない
    ("印が外を名指ししても消さない", BASE + [("t", R1), ("w", QA, QA_HEAD), ("c",), ("t", B1)], "evil",
     lambda r: r.code == 1 and hand_kept(r) and "前に作った出力を消した" not in r.output),
    # 名前の衝突で止まっても、印の名指しする前の出力は消す（残すと今回のものと取り違える。#398）
    ("名前の衝突で止まっても前の出力を消す", SIGNED + [("out", "Spec.html"), ("arg", "--pptx")], True,
     lambda r: collided(r) and r.output.count("前に作った出力を消した") == len(STALE) and not r.files),
    # `--out` の誤りは traceback ではなく 2（#398）
    ("出力先が . だと 2", SIGNED + [("rawout", ".")], False, bad_out("名前が無い")),
    ("出力先が / だと 2", SIGNED + [("rawout", "/")], False, bad_out("名前が無い")),
    ("出力先が .. だと 2", SIGNED + [("rawout", "..")], False, bad_out("名前が無い")),
    ("出力先がディレクトリだと 2", SIGNED + [("rawout", "docs")], False, bad_out("ディレクトリ")),
    # ディレクトリを渡したなら、指したつもりのその中の前の出力も消す（`--out` の親だけ消すと残る。#405 の 1 パス目）
    ("出力先がディレクトリならその中の前の出力を消す", SIGNED + [("rawout", "build/proposal")], True,
     lambda r: bad_out("ディレクトリ")(r) and r.output.count("前に作った出力を消した") == len(STALE) and not r.files),
    # 印は 1 行 1 名前で前後の空白を落とし `#` の行を飛ばすので、そう読み違える名前では作らない（#405 の 1 パス目）
    ("出力の名前が空白で始まると 2", SIGNED + [("out", " notes.md")], False, bad_out("空白")),
    ("出力の名前が改行を含むと 2", SIGNED + [("out", "x\nY.md")], False, bad_out("改行")),
    ("出力の名前が # で始まると 2", SIGNED + [("out", "#draft.md")], False, bad_out("`#`")),
    # 印を読む側は `\` を含む名前を捨て、印は UTF-8 で書く——どちらも印に残せない（#405 の 2 パス目）
    ("出力の名前が \\ を含むと 2", SIGNED + [("out", "a\\b.md")], False, bad_out("`\\`")),
    ("出力の名前が UTF-8 で書けないと 2", SIGNED + [("out", "x\udcff.md")], False, bad_out("UTF-8")),
    # 出力の親が普通のファイルでも traceback の 1（照合の不一致と同じ値）にしない
    ("出力の親がファイルだと 2", SIGNED + [("w", "afile", "x\n"), ("rawout", "afile/proposal.md")], False, bad_out("書けない")),
    ("範囲の外の節が空", [s if s[:2] != ("w", "docs/v1/spec/scope.md") else ("w", "docs/v1/spec/scope.md", "# 範囲\n\n## 範囲の外\n\n## 付録\n\nX\n")
                       for s in SIGNED_S], False,
     lambda r: made(r) and "「範囲の外」の節は空" in r.spec and "節が無い" not in r.spec),
    ("仕様書も同じ入力から同じバイト", SIGNED_S, False, lambda r: made(r) and r.spec == r.again_spec),
    # 承認の後に直した決定表・足した仕様は入らない
    ("仕様書は承認したタグの時点から", SIGNED_S + [("w", DECISION, "会員,金額,割引\nブロンズ,すべて,1%\n"),
                                       ("w", "docs/v1/spec/late.md", "L\n"), ("c",)], False,
     lambda r: made(r) and "| ゴールド | すべて | 5% |" in r.spec and "ブロンズ" not in r.spec and "late.md" not in r.spec),
    ("仕様書の材料が無くても作る", SIGNED, False,
     lambda r: made(r) and "—（決定表が無い）" in r.spec and "「範囲の外」の節が無い" in r.spec
     and "（図はありません）" in r.spec and "手書き部分（`docs/v1/proposal/spec/*.md`）はありません" in r.spec
     and "## 試作" not in r.text and not r.names),
    # 仕様書の手書き部分は提案書に入らない（提案書の手書き部分は proposal/ の直下だけ）
    ("仕様書の手書きは提案書に入らない", SIGNED_S, False, lambda r: made(r) and "試作で確かめること" not in r.text),
    ("v2 の仕様書は重ねた全体と変更", V2C, False,
     lambda r: made(r) and "## 前の版（v1）からの変更" in r.spec and "| F-002 | 送料（離島） |" in r.spec
     and "| F-003 | 返品 |" in r.spec and "| F-001 | 割引 |" not in r.spec and "| 機能（中間表現） | 2 |" in r.spec
     and "| requirements/c.md |" in section(r.spec, "## 仕様と要求のファイル")
     and "requirements/b.md" not in section(r.spec, "## 仕様と要求のファイル")
     and "| Q&A（共有。v1 から重ねた全体） | 2（決定 2・暫定 0・未決定 0） |" in r.spec),
    # ---- PPTX（--pptx）
    ("PPTX も作る", SIGNED_S + [("arg", "--pptx")], False,
     lambda r: made(r) and set(k for k in r.pptx if not k.endswith(":bytes")) == {"proposal.pptx", "spec.pptx"}
     and pptx_ok(r.pptx["proposal.pptx"]) and pptx_ok(r.pptx["spec.pptx"])
     and "利用者にまだ確かめていない決定" in pptx_text(r.pptx["proposal.pptx"])
     and "ゴールド ／ すべて ／ 5%" in pptx_text(r.pptx["spec.pptx"])
     and FIGURE_NOTE in pptx_text(r.pptx["spec.pptx"])
     and "（spec.md で見る）" in pptx_text(r.pptx["spec.pptx"]) and "（proposal.md で見る）" in pptx_text(r.pptx["proposal.pptx"])
     and r.pptx["spec.pptx:bytes"] == r.again_pptx.get("spec.pptx:bytes")
     and r.pptx["proposal.pptx:bytes"] == r.again_pptx.get("proposal.pptx:bytes")),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    # 外さなくても `Q&A（内部）` の節は描かない（共有の種類だけ描く。#344）——外すことが効くのは内部の表の違反のほう
    ("内部の Q&A も比較に載せる", "        drop_internal(Path(tmp) / signoff.DOCS)\n", "", "内部の表の違反でも比較を作る"),
    ("removed.csv の D- の行を外さない", "if len(kept) != len(rows):", "if False:", "内部の表の違反でも比較を作る"),
    ("内部の表を外さない", "            internal.unlink()\n", "            pass\n", "内部の表の違反でも比較を作る"),
    ("最後の版の内部の表だけ外す", "for root in sorted(p for p in docs.iterdir() if mv.VERSION.fullmatch(p.name)):",
     "for root in sorted(p for p in docs.iterdir() if mv.VERSION.fullmatch(p.name))[-1:]:", "前の版の内部の表の違反でも比較を作る"),
    # 層の判定（`check-qa-csv.py` の `is_internal_number`）を外す・入れ替える（#353）
    ("removed.csv の層を見ない", "r[0] == mv.KIND_QA and qa.is_internal_number(r[1].strip())", "False",
     "内部の表の違反でも比較を作る"),
    ("removed.csv の層を入れ替える", "r[0] == mv.KIND_QA and qa.is_internal_number(r[1].strip())",
     "r[0] == mv.KIND_QA and not qa.is_internal_number(r[1].strip())", "内部の表の違反でも比較を作る"),
    ("件数の表に内部の層も載せる", "for k in diffs.SHARED_KINDS])", "for k in diffs.KINDS])", "内部の Q&A は比較に載せない"),
    ("v2 以降も Q&A 表を必須にする", 'if info["version"] > 1 and not exists(', 'if False and not exists(',
     "Q&A を足さない版でも作る"),
    ("v1 でも Q&A 表を省ける", 'if info["version"] > 1 and not exists(', 'if not exists(',
     "v1 は Q&A 表が無いと作らない"),
    ("照合を見ない", "    if code:\n        raise Stop(code, lines)\n", "    if False:\n        raise Stop(code, lines)\n",
     "一致しないと作らない"),
    ("見積りを作業ツリーから読む", 'show(top, info["budget_commit"], info["budget"], estimate_path)',
     '(top / estimate_path).read_text(encoding="utf-8")', "承認したタグの時点の見積り"),
    ("見積りを要求のタグの時点で読む", 'show(top, info["budget_commit"], info["budget"], estimate_path)',
     'show(top, info["req_commit"], info["budget"], estimate_path)', "承認したタグの時点の見積り"),
    ("Q&A 表を作業ツリーから読む", 'show(top, info["req_commit"], info["req"], qa_path)',
     '(top / qa_path).read_text(encoding="utf-8")', "承認の後に直した Q&A 表は入らない"),
    ("版のパスを v1 に固定する", 'return f"{signoff.DOCS}/v{version}/{path}"', 'return f"{signoff.DOCS}/v1/{path}"',
     "作業中の版から作る"),
    ("--version を渡さない", "signoff.resolve(args.repo, args.req, args.budget, args.version)",
     "signoff.resolve(args.repo, args.req, args.budget)", "版を指定して作る"),
    ("手書き部分を版の外から読む", 'hand_dir = top / in_version(info["version"], HAND_DIR)',
     'hand_dir = top / in_version(1, HAND_DIR)', "作業中の版の手書き部分が無いと作らない"),
    ("前の出力を消さない", "            stale.unlink()\n", "            pass\n", "前の提案書を消す"),
    ("手書き部分を逆順に並べる", 'sorted(directory.glob("*.md"))', 'sorted(directory.glob("*.md"), reverse=True)',
     "手書き部分はファイル名の順"),
    ("手書きが無くても作る", "    if not hand:\n        raise Stop(1", "    if False:\n        raise Stop(1", "手書き部分が無いと作らない"),
    ("表の検査を見ない", "    if problems:\n        raise Stop(1, problems)", "    if False:\n        raise Stop(1, problems)",
     "見積りが決まりに反すると作らない"),
    ("未決定の質問を載せない", "    if pending:\n", "    if False:\n", "未決定の質問を載せる"),
    ("比較を作業ツリーから作る", "        copy_docs(top, commit, tag, Path(tmp))\n",
     "        __import__('shutil').copytree(top / signoff.DOCS, Path(tmp) / signoff.DOCS, symlinks=True)\n",
     "承認の後に直した差分は比較に入らない"),
    ("比較を予算のタグの時点から作る", 'compare_at(top, info["req_commit"], info["req"]',
     'compare_at(top, info["budget_commit"], info["req"]', "比較は要求のタグの時点から作る"),
    ("大文字小文字だけ違うパスを断らない", "    if clashes:\n", "    if False:\n", "大文字小文字だけ違うパスは比較で断る"),
    ("ファイルとディレクトリの重なりを見ない", "            if fold(parent) in seen:\n", "            if False:\n",
     "ファイルとディレクトリが大文字小文字だけ違うと比較で断る"),
    ("ディレクトリ同士の重なりを見ない", "            if other != parent:\n", "            if False:\n",
     "ディレクトリが大文字小文字だけ違うと比較で断る"),
    ("正規化を畳まない", "    fold = diffs.merge_versions.fold\n", "    fold = lambda p: p.lower()\n",
     "ディレクトリが正規化だけ違うと比較で断る"),
    ("重ね合わせが読まないものも写す", "        if not merged_reads(path):\n            continue\n", "",
     "重ね合わせが読まないものは写さない"),
    ("比較が作れなくても作る", "    if problems:\n        raise Stop(1, [f\"{tag}: ",
     "    if False:\n        raise Stop(1, [f\"{tag}: ", "比較を作れないと作らない"),
    ("v1 にも比較の節を出す", "if not problems and version > 1:", "if not problems:", "v1 は比較の節を持たない"),
    ("v2 以降も比較の節を出さない", "if not problems and version > 1:", "if False:", "前の版との比較を載せる"),
    ("シンボリックリンクを中身で写す", '        if mode == "120000":\n', '        if False:\n',
     "版の中のシンボリックリンクは比較で断る"),
    ("比較の節を手書き部分の前に置く", '    for _, body in hand:\n        out += [body.rstrip("\\n"), ""]\n    if diff is not None:\n        out += changes_section(diff, info["req"])\n',
     '    if diff is not None:\n        out += changes_section(diff, info["req"])\n    for _, body in hand:\n        out += [body.rstrip("\\n"), ""]\n',
     "前の版との比較を載せる"),
    ("削除の理由を載せない", "answer(c.before), answer(c.after), c.reason or \"—\"]",
     "answer(c.before), answer(c.after), \"—\"]", "前の版との比較を載せる"),
    ("区分ごとに合計しない","sum(int(r['金額']) for r in estimate if r['区分'] == c)", "sum(int(r['金額']) for r in estimate)",
     "作れるときは作る"),
    # ---- 暫定の回答（#366）
    ("確認中を決定事項に載せる", 'done = [r for r in qa_rows if r["状態"].strip() == qa.DONE]',
     'done = [r for r in qa_rows if r["状態"].strip() != qa.DONE]', "文言だけ暫定の反映済みは決定事項に載せる"),
    ("暫定の判別を作業ツリーの表で行う", 'show(top, info["req_commit"], info["req"], qa_path)',
     '(top / qa_path).read_text(encoding="utf-8")', "承認の後に書き足した暫定は載らない"),
    # ---- 仕様書（#371）
    ("仕様書を作業ツリーから作る", "        copy_docs(top, commit, tag, Path(tmp))\n",
     "        __import__('shutil').copytree(top / signoff.DOCS, Path(tmp) / signoff.DOCS, symlinks=True)\n",
     "仕様書は承認したタグの時点から"),
    ("仕様書を最後の版だけから作る", "diffs.merge_versions.merge(Path(tmp) / signoff.DOCS, version)",
     "diffs.merge_versions.merge(Path(tmp) / signoff.DOCS, 1)", "v2 の仕様書は重ねた全体と変更"),
    ("図を写さない", "        figures[name] = whole.files[path]\n", "", "仕様書を作る"),
    ("書き出しの無い図を言わない", "    if missing:\n", "    if False:\n", "仕様書を作る"),
    ("範囲の外を載せない", '        out += body + [""]\n', '        out += [""]\n', "仕様書を作る"),
    ("範囲の外の節の終わりを見ない", "                if 0 < heading_level(rest) <= level:\n", "                if False:\n", "仕様書を作る"),
    ("決定表を載せない", "        out += table([cell(c) for c in padded[0]], padded[1:])\n", "", "仕様書を作る"),
    ("仕様書の手書きを読まない", 'read_hand(top / in_version(info["version"], SPEC_HAND_DIR))', "[]", "仕様書を作る"),
    ("仕様書の手書きを提案書にも入れる", 'hand = read_hand(hand_dir)', 'hand = read_hand(hand_dir) + read_hand(hand_dir / "spec")',
     "仕様書の手書きは提案書に入らない"),
    ("仕様書に比較の節を出さない", '    if diff is not None:\n        out += changes_section(diff, info["req"])\n\n    out += ["## 仕様と要求',
     '    out += ["## 仕様と要求', "v2 の仕様書は重ねた全体と変更"),
    # ---- 何を消すか（#405）。印に何を載せるかは本物の前の実行で見る（下の PREVIOUS_MUTATIONS）
    ("印を見ずに名前で消す", "    for name in names:\n",
     '    for name in ["proposal.md", "spec.md", "gantt.svg", "spec-figure-01.svg"]:\n', "手で置いたファイルは作れないときも消さない"),
    ("印に無いファイルを上書きする", "        if path.exists() or path.is_symlink():\n            raise Stop(2",
     "        if False:\n            raise Stop(2", "手で置いたファイルを上書きしない"),
    ("印の名前の外へ出る", 'if name and not name.startswith("#") and "/" not in name and "\\\\" not in name\n',
     'if name and not name.startswith("#")\n', "印が外を名指ししても消さない"),
    ("引数の誤りで前の出力を消さない", "    problem = bad_out(out)\n    remove_owned(out.parent)\n",
     "    problem = bad_out(out)\n    if problem:\n        return 2\n    remove_owned(out.parent)\n",
     "名前の衝突で止まっても前の出力を消す"),
    ("ディレクトリの出力先の中を消さない", "        remove_owned(out)  # ディレクトリを", "        pass  # ディレクトリを",
     "出力先がディレクトリならその中の前の出力を消す"),
    ("前後に空白のある名前を見ない", "    if out.name != out.name.strip() or ", "    if ", "出力の名前が空白で始まると 2"),
    ("改行を含む名前を見ない", "len(out.name.splitlines()) != 1 or ", "", "出力の名前が改行を含むと 2"),
    ("# で始まる名前を見ない", ' or out.name.startswith("#"):\n', ":\n", "出力の名前が # で始まると 2"),
    ("親を作るのを try の外に置く",
     "    try:\n        directory.mkdir(parents=True, exist_ok=True)  # 親が普通のファイルでも traceback にしない\n",
     "    directory.mkdir(parents=True, exist_ok=True)\n    try:\n", "出力の親がファイルだと 2"),
    ("引数を検査しない", "    problem = bad_out(out)\n", "    problem = None\n", "出力先が . だと 2"),
    ("名前の無い出力先を見ない", '    if out.name in ("", ".", ".."):\n', "    if False:\n", "出力先が .. だと 2"),
    ("ディレクトリの出力先を見ない", "    if is_directory:\n        return", "    if False:\n        return", "出力先がディレクトリだと 2"),
    ("\\ を含む名前を見ない", '    if "\\\\" in out.name:\n', "    if False:\n", "出力の名前が \\ を含むと 2"),
    ("UTF-8 で書けない名前を見ない", '        out.name.encode("utf-8")\n', "        pass\n", "出力の名前が UTF-8 で書けないと 2"),
    ("仕様書の名前の上書きを見ない", "    for path in outputs:\n        if path.exists()",
     "    for path in list(outputs)[:1]:\n        if path.exists()", "手で置いた仕様書だけでも上書きしない"),
    ("印の名前を照らさない", "(SPEC_NAME, GANTT_NAME, SPEC_PPTX_NAME, MANIFEST)", "(SPEC_NAME, GANTT_NAME, SPEC_PPTX_NAME)",
     "出力の名前が印と重なると作らない"),
    ("PPTX を作らない", "    if args.pptx:\n", "    if False:\n", "PPTX も作る"),
    ("PPTX の図はどれも仕様書で見ると書く", "FIGURE_NOTE.format(source)", "FIGURE_NOTE.format(SPEC_NAME)", "PPTX も作る"),
    ("shared/ の図も載せる", "for p in whole.files if p.startswith(FIGURE_DIRS)", "for p in whole.files", "仕様書を作る"),
    ("出力の PPTX の名前を照らさない", ', out.with_suffix(".pptx").name.lower()}', "}", "出力の名前が仕様書の PPTX と重なると作らない"),
    ("出力の PPTX の名前を大文字小文字で区別する", 'out.with_suffix(".pptx").name.lower()}', 'out.with_suffix(".pptx").name}',
     "出力の名前が仕様書の PPTX と重なると作らない"),
    ("頼まれなくても PPTX を作る", "    if args.pptx:\n", "    if True:\n", "仕様書を作る"),
    ("ガントチャートの名前を照らさない", "(SPEC_NAME, GANTT_NAME, SPEC_PPTX_NAME, MANIFEST)", "(SPEC_NAME, SPEC_PPTX_NAME, MANIFEST)",
     "出力の名前がガントチャートと重なると作らない"),
    ("PPTX の拡張子の出力を照らさない", ' or out.suffix.lower() == ".pptx"', "", "出力が PPTX の名前だと作らない"),
    ("図の接頭辞を照らさない", "            or out.name.lower().startswith(FIGURE_PREFIX)):", "            ):", "出力の名前が図と重なると作らない"),
    ("暫定の節を決定事項の下に置く", '[f"## {scope}利用者にまだ', '[f"### {scope}利用者にまだ', "暫定の節は決定事項のスライドと分ける"),
    ("v2 でもこの版と書かない", 'scope = "この版の Q&A で" if diff is not None else ""', 'scope = ""', "v2 の暫定の節はこの版の Q&A と書く"),
    ("v1 でもこの版と書く", 'scope = "この版の Q&A で" if diff is not None else ""', 'scope = "この版の Q&A で"', "確定した行は暫定にしない"),
    ("空の範囲の外も節が無いと書く", "    elif body is not None:\n", "    elif False:\n", "範囲の外の節が空"),
]

# 判別の本体（`check-qa-csv.py` の `is_provisional`）を壊す。(名前, 壊す前, 壊した後, 殺すはずの試料の名前)
QA_TARGET = "check-qa-csv.py"
QA_MUTATIONS: list[tuple[str, str, str, str]] = [
    # 照合（`check-signoff.py`）も同じ判別を読むので、暫定の行を見なければ作ってしまう
    ("判別の本体で暫定を見ない", 'return row["状態"].strip() == PROVISIONAL', "return False", "暫定の回答が残ると作らない"),
    # #374 の形（`反映済み` の `回答` の文言で暫定を決める）に戻す——照合が 3 で止め、文言だけの行で作れなくなる
    ("判別の本体を文言の一致に戻す", 'return row["状態"].strip() == PROVISIONAL',
     'return row["状態"].strip() == PROVISIONAL or (row["状態"].strip() == DONE and "暫定で採用" in row["回答"])',
     "文言だけ暫定の反映済みは決定事項に載せる"),
    ("どの反映済みも暫定にする", 'return row["状態"].strip() == PROVISIONAL',
     'return row["状態"].strip() in (PROVISIONAL, DONE)', "確定した行は暫定にしない"),
]

# 照合を通った提案書では暫定の節は 0 件にしかならない（`暫定反映` が残れば照合が 3）ので、節の中身は `compose` を直接呼んで見る。
# 照合を通らない経路（`compose` だけを使う）でも、暫定の行を決定事項に混ぜないことの歯止め
COMPOSE_ROWS = [
    {"No": "Q-101", "起票元": "要求確定", "質問": "暫定の質問", "選択肢": "A: x / B: y", "推奨": "A", "推奨の理由": "r",
     "回答": "A（業務部 2026-10-21 の指示）", "反映先": "決定表 1 行目", "状態": "暫定反映", "費用への影響": ""},
    {"No": "Q-102", "起票元": "要求確定", "質問": "確定の質問", "選択肢": "A: x / B: y", "推奨": "A", "推奨の理由": "r",
     "回答": "A（推奨案を暫定で採用。開発側の指示）", "反映先": "決定表 2 行目", "状態": "反映済み", "費用への影響": ""},
    {"No": "Q-103", "起票元": "要求確定", "質問": "未決定の質問", "選択肢": "A: x / B: y", "推奨": "A", "推奨の理由": "r",
     "回答": "未回答", "反映先": "—", "状態": "確認中", "費用への影響": ""},
]
COMPOSE_MUTATIONS: list[tuple[str, str, str]] = [
    ("暫定の節に載せない", "provisional = [r for r in qa_rows if qa.is_provisional(r)]", "provisional = []"),
    ("暫定の行を未決定にも載せる", 'pending = [r for r in qa_rows if r["状態"].strip() != qa.DONE and not qa.is_provisional(r)]',
     'pending = [r for r in qa_rows if r["状態"].strip() != qa.DONE]'),
    ("暫定の行を決定事項に混ぜる", 'done = [r for r in qa_rows if r["状態"].strip() == qa.DONE]',
     'done = [r for r in qa_rows if r["状態"].strip() in (qa.DONE, qa.PROVISIONAL)]'),
]


def compose_problems(scripts: Path) -> list[str]:
    """`scripts` の中の `build-proposal.py` の `compose` に暫定・確定・未決定の 3 行を渡し、載る節を見る。"""
    spec = importlib.util.spec_from_file_location("build_proposal_compose", scripts / TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    info = {"version": 1, "req": R1, "req_commit": "0" * 40, "budget": B1, "budget_commit": "0" * 40}
    schedule = [{"No": "S-001", "工程": "設計", "開始": "2026-11-01", "終了": "2026-11-30", "前提": "—"}]
    estimate_rows = [{"No": "E-001", "区分": "開発費", "項目": "設計", "金額": "1000", "根拠": "r"}]
    text = module.compose("提案書", info, [], COMPOSE_ROWS, schedule, estimate_rows, None)
    problems = []
    if "| Q-101 |" not in section(text, "## 利用者にまだ確かめていない決定（1 件）"):
        problems.append("暫定の行が暫定の節（1 件）に無い")
    if "Q-101" in section(text, "## 主な決定事項") or "Q-101" in section(text, "## 承認の時点で未決定の質問"):
        problems.append("暫定の行が決定事項か未決定に載る")
    if "| Q-102 |" not in section(text, "## 主な決定事項"):
        problems.append("文言だけ暫定の反映済みの行が決定事項に無い")
    if "| Q-103 |" not in section(text, "## 承認の時点で未決定の質問（1 件）"):
        problems.append("確認中の行が未決定（1 件）に無い")
    return problems

# 書いている途中の失敗で殺す変異。(名前, 壊す前, 壊した後)
WRITE_MUTATIONS: list[tuple[str, str, str]] = [
    ("書きかけを消さない", "        remove_owned(directory)\n        raise Stop(2, [f\"{directory}: 書けない",
     "        raise Stop(2, [f\"{directory}: 書けない"),
    ("印を書かない（途中の失敗）", "        (directory / MANIFEST).write_text(", "        (directory / MANIFEST).with_name('unused').write_text("),
]


def write_failure_problems(scripts: Path) -> list[str]:
    """`write_outputs` を直接呼び、1 つ目を書いた後の PPTX で失敗させる——書きかけと印が残らず 2 で止まるか（#405 の 1 パス目）。

    CLI からは途中で書けなくする手が無い（書く前に名前の在る・無しを見るので、在るものは書き始める前に 2 になる）。
    """
    import contextlib
    import errno
    import io
    spec = importlib.util.spec_from_file_location("build_proposal_write", scripts / TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def fail(*_args) -> None:
        raise OSError(errno.EACCES, "書けない（試料）")

    module.pptx.write = fail
    problems = []
    with tempfile.TemporaryDirectory(prefix="proposal-write-") as tmp:
        directory = Path(tmp) / "out"
        try:
            with contextlib.redirect_stderr(io.StringIO()):  # 消したことの通知は親の出力に混ぜない
                module.write_outputs({directory / "proposal.md": b"x", directory / "proposal.pptx": []}, directory)
            problems.append("書けないのに止まらない")
        except module.Stop as stop:
            if stop.code != 2 or not any("書きかけを消した" in line for line in stop.lines):
                problems.append(f"止まり方が違う: {stop.code} {stop.lines}")
        left = sorted(p.name for p in directory.iterdir()) if directory.is_dir() else []
        if left:
            problems.append(f"書きかけが残る: {left}")
    return problems

# 読めない印・辿れない出力先で殺す変異。(名前, 壊す前, 壊した後)
OWN_MUTATIONS: list[tuple[str, str, str]] = [
    ("読めない印を消す", "    if names is None:\n        return\n", "    names = names or []\n"),
    ("辿れない出力先を見ない", '        return f"{out}: 出力先を確かめられない（{e.strerror}）"\n', "        is_directory = False\n"),
]


def ownership_problems(scripts: Path) -> list[str]:
    """読めない印は消さない／辿れない出力先は traceback でなく 2（#405 の 2 パス目）。

    読めない印は `remove_owned` を直接呼ぶ。辿れない出力先は CLI で走らせる——python3.12 の `pathlib` は
    `is_dir`・`is_file` で `PermissionError` を投げ、3.14 は投げない。`bad_out` が `stat` で見るので、どちらでも同じ文言の 2。
    """
    import contextlib
    import io
    spec = importlib.util.spec_from_file_location("build_proposal_own", scripts / TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    problems = []
    with tempfile.TemporaryDirectory(prefix="proposal-own-") as tmp:
        directory = Path(tmp) / "out"
        directory.mkdir()
        (directory / MANIFEST).write_bytes(b"\xff\nproposal.md\n")
        (directory / "proposal.md").write_text("古い出力\n", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            module.remove_owned(directory)
        if sorted(p.name for p in directory.iterdir()) != sorted([MANIFEST, "proposal.md"]):
            problems.append(f"読めない印のあとに残るものが違う: {sorted(p.name for p in directory.iterdir())}")

        locked = Path(tmp) / "locked"
        locked.mkdir()
        locked.chmod(0)
        try:
            proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), "--repo", tmp,
                                   "--out", str(locked / "sub" / "proposal.md")], capture_output=True, text=True, cwd=tmp)
        finally:
            locked.chmod(0o755)
        output = proc.stdout + proc.stderr
        if proc.returncode != 2 or "Traceback" in output or "確かめられない" not in output:
            problems.append(f"辿れない出力先: {proc.returncode} {output[-300:]}")
    return problems

# #260 の名前（版を根にした名前）。素の `v1` と共存する試料を、承認のタグだけこの名前にして作ると、
# タグの手順で作れない（`refs/tags/v1` と `refs/tags/v1/...` は共存できない）——試料が衝突を判別している確かめ
OLD_NAMES = {R1: "v1/req-signoff-1", B1: "v1/budget-signoff-1"}
COEXIST = ["素の v1 タグと共存する"]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def sandbox_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_DATE="2026-01-01T00:00:00Z", GIT_COMMITTER_DATE="2026-01-01T00:00:00Z")
    return env


def run_git(repo: Path, env: dict[str, str], *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com",
                    "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                   check=True, capture_output=True, env=env)


def build_repo(root: Path, steps: list[tuple[str, ...]], env: dict[str, str]) -> None:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    run_git(root, env, "init", "-q", "-b", "main")
    for step in steps:
        if step[0] == "w":
            path = root / step[1]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(step[2], encoding="utf-8")
            run_git(root, env, "add", "-A")
        elif step[0] == "l":  # シンボリックリンク（リンク先は書いたまま）
            path = root / step[1]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(step[2])
            run_git(root, env, "add", "-A")
        elif step[0] == "i":  # 作業ツリーを通さず索引にだけ置く（大文字小文字を区別しない FS でも並べられる）。("i", パス, モード, 中身)
            blob = subprocess.run(["git", "-C", str(root), "hash-object", "-w", "--stdin"], input=step[3].encode(),
                                  check=True, capture_output=True, env=env).stdout.decode().strip()
            # パスは stdin で渡す——macOS の git は引数のパスを NFC に直す（core.precomposeunicode）ので、
            # --cacheinfo では NFD の試料が NFC に潰れ、試したつもりで試せていない形になる（#275）
            subprocess.run(["git", "-C", str(root), "update-index", "--add", "--index-info"],
                           input=f"{step[2]} {blob}\t{step[1]}\n".encode(), check=True, capture_output=True, env=env)
        elif step[0] == "c":
            run_git(root, env, "commit", "-q", "--allow-empty", "-m", "step")
        elif step[0] == "t":
            run_git(root, env, "tag", step[1])


def generate(scripts: Path, root: Path, out: Path | str, env: dict[str, str], extra: list[str] = ()) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), "--repo", str(root), "--out", str(out), *extra],
                          capture_output=True, text=True, cwd=root, env=env)
    return proc.returncode, proc.stdout + proc.stderr


def run_case(scripts: Path, root: Path, steps, stale: bool | str, env: dict[str, str]) -> Result:
    """`stale`: True なら本体が作ったのと同じ形の前の出力（印つき）を、"hand" なら手で置いたファイル（印なし）を、
    "evil" なら同じ場所の外を名指しする印を置いてから生成する。"""
    try:
        build_repo(root, steps, env)
    except subprocess.CalledProcessError as e:  # 1 つの試料が作れなくても、実行全体は落とさない
        return Result(None, f"試料を作れなかった: {' '.join(e.cmd[-2:])}: {e.stderr.decode(errors='replace')}",
                      None, False, None)
    # ("arg", …) の手順は、生成に渡す引数（リポジトリには何もしない）
    extra = [value for step in steps if step[0] == "arg" for value in step[1:]]
    # ("out", 名前) の手順は、出力の名前（リポジトリには何もしない）
    out = root / "build" / "proposal" / next((step[1] for step in steps if step[0] == "out"), "proposal.md")
    # ("rawout", 値) の手順は、`--out` にそのまま渡す値（cwd は試料の根）。`.`・`/` は Path にすると名前が消えるので文字列で渡す
    raw = next((step[1] for step in steps if step[0] == "rawout"), None)
    if stale == "hand":
        write_hand(out)
    elif stale == "handspec":
        write_hand(out, ["spec.md"])
    elif stale == "evil":
        write_evil(out)
    elif stale:
        write_stale(out)
    code, output = generate(scripts, root, raw if raw is not None else out, env, extra)
    text = out.read_text(encoding="utf-8", errors="replace") if out.is_file() else None
    svg = (out.parent / "gantt.svg").is_file()
    spec = (out.parent / "spec.md").read_text(encoding="utf-8", errors="replace") if (out.parent / "spec.md").is_file() else None
    names = frozenset(p.name for p in out.parent.iterdir()) - {"proposal.md", "gantt.svg", "spec.md", MANIFEST} if out.parent.is_dir() else frozenset()
    again_out = root / "build" / "again" / "proposal.md"
    generate(scripts, root, again_out, env, extra)
    again = again_out.read_text(encoding="utf-8", errors="replace") if again_out.is_file() else None
    again_spec = (again_out.parent / "spec.md").read_text(encoding="utf-8", errors="replace") if (again_out.parent / "spec.md").is_file() else None
    return Result(code, output, text, svg, again, spec, names, read_pptx(out.parent), read_pptx(again_out.parent), again_spec,
                  out.parent)


def write_stale(out: Path) -> None:
    out.parent.mkdir(parents=True)
    for name in STALE:
        (out.parent / name).write_text("古い出力\n", encoding="utf-8")
    (out.parent / MANIFEST).write_text("# 本体が書くのと同じ形\n" + "\n".join(STALE) + "\n", encoding="utf-8")


def write_hand(out: Path, names: list[str] = HAND) -> None:
    out.parent.mkdir(parents=True)
    for name in names:
        (out.parent / name).write_text(HAND_TEXT, encoding="utf-8")


def write_evil(out: Path) -> None:
    """同じ場所の外（上・下のディレクトリ）を名指しする印。名指しされたファイルは消えてはならない。"""
    write_hand(out)
    (out.parent / "sub").mkdir()
    (out.parent / "sub" / "x.md").write_text(HAND_TEXT, encoding="utf-8")
    (out.parent.parent / "outside.md").write_text(HAND_TEXT, encoding="utf-8")
    (out.parent / MANIFEST).write_text("../outside.md\nsub/x.md\n..\n.\n" + MANIFEST + "\n", encoding="utf-8")


def read_pptx(directory: Path) -> dict:
    """PPTX のファイル名 → (zip の中のパス → 中身)。zip として読めなければ中身は空。"""
    import zipfile
    found = {}
    for path in sorted(directory.glob("*.pptx")) if directory.is_dir() else []:
        try:
            with zipfile.ZipFile(path) as z:
                found[path.name] = {n: z.read(n).decode("utf-8") for n in z.namelist()}
        except (zipfile.BadZipFile, UnicodeDecodeError):
            found[path.name] = {}
        found[path.name + ":bytes"] = path.read_bytes()
    return found


def run_no_git(scripts: Path, root: Path, env: dict[str, str], subdir: bool = False) -> Result:
    """作れる状態のリポジトリと古い出力を置いてから、git を起動できない PATH で生成する。

    `subdir` なら `--out` を渡さず下位ディレクトリから走らせる——既定の出力先（根の下）の古い出力が消えるか。
    """
    build_repo(root, SIGNED, env)
    out = root / "build" / "proposal" / "proposal.md"
    write_stale(out)
    empty = root.parent / f"{root.name}-empty-path"
    empty.mkdir()
    no_git_env = {**env, "PATH": str(empty)}
    if subdir:
        proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), "--repo", "."],
                              capture_output=True, text=True, cwd=root / "docs", env=no_git_env)
        code, output = proc.returncode, proc.stdout + proc.stderr
    else:
        code, output = generate(scripts, root, out, no_git_env)
    names = frozenset(p.name for p in out.parent.iterdir()) - {"proposal.md", "gantt.svg", "spec.md", MANIFEST}
    return Result(code, output, out.read_text(encoding="utf-8", errors="replace") if out.is_file() else None,
                  (out.parent / "gantt.svg").is_file(), None,
                  (out.parent / "spec.md").read_text(encoding="utf-8", errors="replace") if (out.parent / "spec.md").is_file() else None, names)


# git を起動できないとき: 古い出力を消し、2 で終わる（トレースバックの 1 にしない）
def no_git(r: Result) -> bool:
    return not_made(2)(r) and r.output.count("前に作った出力を消した") == len(STALE) and "Traceback" not in r.output


# (名前, 壊す前, 壊した後, 殺す試料は下位ディレクトリから走らせるか)
NO_GIT_MUTATIONS = [
    ("git を起動できないと落ちる", "    except signoff.Unjudged:\n        pass",
     "    except ZeroDivisionError:\n        pass", True),  # `--out` を渡すと根を求めないので、下位からでないと届かない
    ("git で根を求められないと .git をたどらない", "    for parent in (repo.resolve(), *repo.resolve().parents):",
     "    for parent in ():", True),
]


def run_previous(scripts: Path, root: Path, env: dict[str, str]) -> tuple[int, int, str, list[str]]:
    """本物の前の実行（PPTX と図を含む）のあとに照合で止め、前の実行が書いたものが全部消えるかを見る（陽性対照。#405）。

    試料の前の出力（`write_stale`）は印を手で書くので、**本体が印に何を載せるか**はこちらでしか見えない。
    返すのは (前の実行の終了コード, 止めた実行の終了コード, 出力, 残ったファイル)。
    """
    build_repo(root, SIGNED_S, env)
    out = root / "build" / "proposal" / "proposal.md"
    first, _ = generate(scripts, root, out, env, ["--pptx"])
    second, output = generate(scripts, root, out, env, ["--pptx", "--req", "signoff/v1/req-99"])
    return first, second, output, sorted(p.name for p in out.parent.iterdir()) if out.parent.is_dir() else []


def previous_removed(result: tuple[int, int, str, list[str]]) -> bool:
    first, second, output, left = result
    # 前の実行は提案書・ガントチャート・仕様書・図 1 つ・PPTX 2 つ（6 つ）を書いた
    return first == 0 and second == 2 and not left and output.count("前に作った出力を消した") == 6


# 本物の前の実行で殺す変異。(名前, 壊す前, 壊した後)
PREVIOUS_MUTATIONS = [
    ("印に PPTX と図を載せない", "*sorted(p.name for p in outputs)]", '*sorted(p.name for p in outputs if p.suffix == ".md")]'),
    ("印を書かない", "        (directory / MANIFEST).write_text(", "        (directory / 'unused').write_text("),
]


def run_all(scripts: Path, work: Path, env: dict[str, str]) -> dict[str, Result]:
    return {name: run_case(scripts, work / f"case{i}", steps, stale, env)
            for i, (name, steps, stale, _) in enumerate(CASES)}


def with_old_names(steps: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    return [(s[0], OLD_NAMES.get(s[1], s[1]), *s[2:]) if s[0] == "t" else s for s in steps]


# 衝突の片側が素の v1 そのものであるときだけ数える——v1/x と v1/x/y の衝突も同じ形で落ちる（#309）
V1_COLLISION = re.compile(r"'refs/tags/v1' exists|cannot (?:lock ref|create) 'refs/tags/v1'")


def old_names_collide(root: Path, steps: list[tuple[str, ...]], env: dict[str, str]) -> str:
    """承認のタグを #260 の名前にして作る。タグの手順で失敗すれば空文字列、そうでなければ何が起きたか。"""
    old = with_old_names(steps)
    if old == steps:
        return "置き換える承認のタグが試料に無い"
    try:
        build_repo(root, old, env)
    except subprocess.CalledProcessError as e:
        if "tag" not in e.cmd:
            return f"タグ以外の手順で作れなかった: {' '.join(e.cmd[-2:])}"
        # タグの失敗なら何でもよいのではない——同じ名前の付け直しも tag で落ちる（#309）
        stderr = e.stderr.decode(errors="replace")
        return "" if V1_COLLISION.search(stderr) else f"素の v1 との衝突ではない理由で作れなかった: {stderr.strip()}"
    return "#260 の名前でも作れた（素の v1 と衝突していない）"


def as_expected(name: str, result: Result) -> bool:
    return next(case for case in CASES if case[0] == name)[3](result)


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    if shutil.which("git") is None:
        print("git が無いので走らせていない（緑ではない）", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="proposal-test-") as tmp:
        tmp_path = Path(tmp)
        home = tmp_path / "home"
        home.mkdir()
        env = sandbox_env(home)
        scripts = copy_scripts(tmp_path / "scripts")
        for name, result in run_all(scripts, tmp_path / "work", env).items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result.code} {result.output[-300:]}")
        for index, name in enumerate(COEXIST):
            steps = next(case[1] for case in CASES if case[0] == name)
            problem = old_names_collide(tmp_path / f"old{index}", steps, env)
            check(f"試料が #260 の名前を判別していない: {name}", not problem, problem)

        for subdir in (False, True):
            result = run_no_git(scripts, tmp_path / f"nogit-{subdir}", env, subdir)
            check(f"試料が期待どおりでない: git を起動できない（下位から: {subdir}）", no_git(result),
                  f"exit={result.code} {result.output[-300:]}")

        result = run_previous(scripts, tmp_path / "previous", env)
        check("試料が期待どおりでない: 本物の前の実行が書いたものを消す", previous_removed(result), str(result[:2]) + result[2][-300:])

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after) in enumerate(PREVIOUS_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut-prev{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            result = run_previous(mutated, tmp_path / f"mutwork-prev{index}", env)
            check(f"変異が生き残った: {name}", not previous_removed(result), result[2][-300:])
        for index, (name, before, after, subdir) in enumerate(NO_GIT_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut-nogit{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            result = run_no_git(mutated, tmp_path / f"mutwork-nogit{index}", env, subdir)
            check(f"変異が生き残った: {name}", not no_git(result), result.output[-300:])
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            killer_case = next(case for case in CASES if case[0] == killer)
            result = run_case(mutated, tmp_path / f"mutwork{index}", killer_case[1], killer_case[2], env)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result.output[-300:])
        qa_source = (SCRIPTS / QA_TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(QA_MUTATIONS):
            count = qa_source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"{QA_TARGET} で壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mutqa{index}")
            (mutated / QA_TARGET).write_text(qa_source.replace(before, after), encoding="utf-8")
            killer_case = next(case for case in CASES if case[0] == killer)
            result = run_case(mutated, tmp_path / f"mutqawork{index}", killer_case[1], killer_case[2], env)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result.output[-300:])

        problems = compose_problems(SCRIPTS)
        check("compose が暫定・確定・未決定を分けない", not problems, "; ".join(problems))
        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after) in enumerate(COMPOSE_MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mutcompose{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}（compose を直接呼んで殺せるはず）", bool(compose_problems(mutated)))

        problems = write_failure_problems(SCRIPTS)
        check("書いている途中で失敗したときに書きかけを消さない", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(WRITE_MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mutwrite{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}（write_outputs を直接呼んで殺せるはず）", bool(write_failure_problems(mutated)))

        problems = ownership_problems(SCRIPTS)
        check("読めない印か辿れない出力先の扱いが違う", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(OWN_MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mutown{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}（読めない印か辿れない出力先で殺せるはず）", bool(ownership_problems(mutated)))

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES) + 6} 件・変異 {len(MUTATIONS) + len(NO_GIT_MUTATIONS) + len(PREVIOUS_MUTATIONS) + len(QA_MUTATIONS) + len(COMPOSE_MUTATIONS) + len(WRITE_MUTATIONS) + len(OWN_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
