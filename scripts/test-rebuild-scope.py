#!/usr/bin/env python3
"""`rebuild-scope.py`（spec-loop の、仮回答と推奨で決めた事項の台帳から作り直す範囲を引くスクリプト。#875）の回帰テスト。

    python3 scripts/test-rebuild-scope.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-qa-csv.py` と同じ形。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、本物の GitHub には届かない（本体は `gh` を呼ばない。
入力の JSON は `gh issue list --json number,title,state,body,comments` と同じ鍵の試料で、本物の出力の形は見ない）。

**spec-loop の Issue の本文は、本物の `scaffold.py --provisional` で作る**——手で書いた本文に当てると、生成の形が変わっても緑のままになる。
**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる**（正本リポジトリで単体で動くこと）。

**守ること**（各行に変異が 1 つ以上ある——下の `MUTATIONS`）:

- Q&A の No から、それを根拠にした spec-loop の Issue と、その受入基準のケースを引く（表の `（暫定）` を外して読む）
- 機能の `qa` だけが指す No は「ケースに無い（機能全体）」と言う（`## Q&A の回答` の節と `## 仕様` の `- 仮回答: ` の行を読む）
- 確認の Issue を、印 `<!-- cruise-decision: #<親> -->` でも題の `要確認: ` でも見分け、`決めた値: `・`影響する Issue: ` を読む
- 台帳の 2 行が無い確認の Issue・形に反する `影響する Issue: ` の行（説明の中の番号を数えない）・確認の Issue でない番号・入力に無い番号・
  入力に無い影響する Issue・本文に無い No は名指しして 1（引けたものは出す）
- 撤去の Issue（変化の印 `remove`）は作り直す範囲に数えない。空の台帳の行は「決まりの形でない」と言う
- まとめた本文（2 行目が `<!-- spec-loop-bundle: … -->`。#876）は機能の印の行で部分に分け、部分ごとに引く（本物の `scaffold.py --bundle` で作る）
- まとめた本文の改行が `\r\n` でも部分に分ける
- 入力の形が違えば 2（どの Issue が違うかを言う）
- 確認の Issue の閉じのコメントの結果の行を読み、推奨のまま・変えた・結果なしを `#N` と一覧に出す（最後の結果の行を採る。本文の中・装飾つき・文の途中の行は読まない。#884）
- 形に反する結果の行は名指しして 1。`comments` の鍵が無い入力は「読んでいない」と言う（「結果なし」と言わない）。`comments` の形が違えば 2
- `--changed` は結果が `変えた` の確認の Issue だけを出し、結果を読めない・閉じたのに結果の行が無い確認の Issue と、台帳の行が無い／形に反する／影響する Issue が入力に無い変えた確認の Issue を名指しして 1。No・番号と一緒なら 2
- `--draft` は先頭の行に作り直しの元の印（`作り直しの元: <No>`・`作り直しの元: #<番号>`）を付けた下書きを出す——No なら引いた Issue とケース（撤去の Issue は数えない・まとめた本文は部分ごと）、確認の Issue なら推奨で決めた値・新しい値（無ければ「まだ無い」）・影響する Issue（無ければ「なし」）。値は箇条書きにし、行頭を台帳の行・結果の行の頭にしない（#885）
- `--draft` は範囲が空の No・推奨のまま確かめた確認の Issue・推奨のままかを読めない確認の Issue（`comments` が無い・開いていると読めないのに結果の行が無い——閉じた・`state` が無い）・`#N` の引きが 1 になる確認の Issue では下書きを出さずに 1。No・番号・`--changed` と一緒・2 回渡したら 2

**変異テストを含む。** 写した本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。変異ごとに、
**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、穴が無くても緑になるので）。

**写しの突き合わせ**: 確認の Issue の 2 行の頭（本体の `DECIDED`・`AFFECTS`）と、閉じるときの結果の 1 行（`RESULT`・`KEPT`・`CHANGED`）が
dev-loop の `references/absent-lines.md` の「確認の Issue の書き方」に在ること（陽性対照つき）。作り直しの元の印の頭（`ORIGIN`）が、原本の spec-loop の
`references/handoff-issue.md` の「作り直しの元の印」と、写しの dev-loop の `references/spec-gap.md` の「作り直しの周」に 2 つの形で在り、
`absent-lines.md` と dev-loop の `SKILL.md` が同じ頭で指していること（陽性対照つき。#885）。仮回答の印は本体が `scaffold.py` の定数を読む（写さない）。
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "rebuild-scope.py"
DEV_LOOP = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop"
ABSENT_LINES = DEV_LOOP / "references" / "absent-lines.md"
SPEC_GAP = DEV_LOOP / "references" / "spec-gap.md"
DEV_LOOP_SKILL = DEV_LOOP / "SKILL.md"
HANDOFF = REAL_REPO / "plugins" / "spec-loop" / "references" / "handoff-issue.md"

HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
QA = (HEADER
      + "Q-001,要求確定（決定表）,シルバーで 10000 円未満の割引は？,A: 割引なし / B: 3% 割引,A,理由,"
        "A（暫定で採用。業務部 2026-10-21 の指示）,決定表 4 行目,暫定反映,\n"
      + "Q-002,仕様レビュー（Red Team）,金額が負なら？,A: 拒否する / B: 0 とみなす,A,理由,A（業務部が回答）,spec/order.md,反映済み,\n")
SPEC = "# 注文\n\n割引と取り消し。\n"
IR = {
    "spec_ir_version": 1, "title": "注文",
    "features": [
        {"id": "F-001", "title": "割引額を計算する", "source": ["spec/order.md"], "qa": ["Q-001"],
         "operation": {"id": "calc_discount", "method": "POST", "path": "/orders/discount",
                       "input": {"amount": {"type": "integer"}}, "output": {"discount": {"type": "integer"}},
                       "errors": ["INVALID_AMOUNT"]},
         "cases": [{"id": "F-001-C1", "title": "10000 円未満は割引なし", "input": {"amount": 9999},
                    "expected": {"discount": 0}, "qa": ["Q-001"]},
                   {"id": "F-001-C2", "title": "金額が負なら拒否する", "input": {"amount": -1},
                    "error": "INVALID_AMOUNT", "qa": ["Q-002"]}]},
        # 機能の qa だけが Q-001（暫定）と Q-002 を指す——どのケースも指さない
        {"id": "F-002", "title": "注文を取り消せるか", "source": ["spec/order.md"], "qa": ["Q-001", "Q-002"],
         "operation": {"id": "can_cancel", "method": "GET", "path": "/orders/cancelable",
                       "input": {"shipped": {"type": "boolean"}}, "output": {"ok": {"type": "boolean"}}},
         "cases": [{"id": "F-002-C1", "title": "発送前なら取り消せる", "input": {"shipped": False}, "expected": {"ok": True}}]},
    ],
}


def decision(marker: bool, title: str, lines: str) -> tuple[str, str]:
    body = ("<!-- cruise-decision: #877 -->\n\n" if marker else "") + (
        "- 何が起きたか: 推奨で決めた\n- あなたが選べること: A（推奨）／B\n- 何もしなければ: A のまま\n\n"
        "重さ: 済んだこと（取り消すなら revert が要る）\n" + lines + "\n## 背景\n\n背景\n")
    return title, body


def issues_json(bodies: dict[str, str]) -> list[dict]:
    t20, b20 = decision(True, "要確認: 返品の受付期間を 7 日にした", "決めた値: 7 日\n影響する Issue: #11, #12\n")
    t21, b21 = decision(True, "返品の受付期間（前の書き方）", "")  # 印だけで題は前の形、台帳の行が無い
    t23, b23 = decision(False, "要確認: 印の無い確認の Issue", "決めた値: B\n影響する Issue: なし\n")
    t24, b24 = decision(True, "要確認: 説明つきの行", "決めた値: C\n影響する Issue: #11（#12 の後続）\n")
    t25, b25 = decision(True, "要確認: 入力に無い Issue を指す", "決めた値: D\n影響する Issue: #11, #99\n")
    t27, b27 = decision(True, "要確認: 空の決めた値", "決めた値: \n影響する Issue: #11\n")
    t28, b28 = decision(True, "要確認: 空の影響する Issue", "決めた値: E\n影響する Issue: \n")
    # 閉じのコメントの結果の行（#884）
    t29, b29 = decision(True, "要確認: 開き直して変えた", "決めた値: A\n影響する Issue: #11\n")
    t32, b32 = decision(True, "要確認: 形に反する結果", "決めた値: F\n影響する Issue: なし\n")
    t33, b33 = decision(True, "要確認: 本文と装飾の結果", "決めた値: G\n影響する Issue: なし\n確認の結果: 変えた: 本文の中\n")
    t34, b34 = decision(True, "要確認: 前の取り方", "決めた値: H\n影響する Issue: なし\n")
    t35, b35 = decision(True, "要確認: 頭の後ろに空白が無い", "決めた値: I\n影響する Issue: なし\n")
    t36, b36 = decision(True, "要確認: 写す前の値のまま", "決めた値: J\n影響する Issue: なし\n")
    # 撤去の Issue（変化の印 remove）——Q-001 を根拠にしていても作り直す範囲に数えない
    removal = bodies["F-002"].replace("<!-- spec-loop-change: add; base=none -->", "<!-- spec-loop-change: remove; base=v1 -->")
    assert removal != bodies["F-002"]
    found = [
        {"number": 11, "title": "F-001: 割引額を計算する", "state": "OPEN", "body": bodies["F-001"]},
        {"number": 12, "title": "F-002: 注文を取り消せるか", "state": "CLOSED", "body": bodies["F-002"]},
        {"number": 20, "title": t20, "state": "OPEN", "body": b20},
        {"number": 21, "title": t21, "state": "OPEN", "body": b21},
        {"number": 22, "title": "ふつうの Issue", "state": "OPEN", "body": "Q-001 に触れているが spec-loop の Issue ではない\n"},
        {"number": 23, "title": t23, "state": "CLOSED", "body": b23},
        {"number": 24, "title": t24, "state": "OPEN", "body": b24},
        {"number": 25, "title": t25, "state": "OPEN", "body": b25},
        {"number": 26, "title": "F-002: 注文を取り消せるか（v2 で撤去）", "state": "OPEN", "body": removal},
        {"number": 27, "title": t27, "state": "OPEN", "body": b27},
        {"number": 28, "title": t28, "state": "OPEN", "body": b28},
        {"number": 29, "title": t29, "state": "CLOSED", "body": b29,
         "comments": [{"body": "<!-- dev-loop: 子 #1 --> PR は #5"}, {"body": "承認します\n確認の結果: 推奨のまま"},
                      {"body": "開き直す"}, {"body": "やはり変える\r\n確認の結果: 変えた: 14 日\r\n"}]},
        {"number": 32, "title": t32, "state": "CLOSED", "body": b32, "comments": [{"body": "確認の結果: 変えた: "}]},
        {"number": 33, "title": t33, "state": "CLOSED", "body": b33,
         "comments": [{"body": "**確認の結果: 変えた: 装飾**"}, {"body": "閉じます。確認の結果: 変えた: 文の途中"}]},
        {"number": 34, "title": t34, "state": "OPEN", "body": b34, "no_comments": True},
        {"number": 35, "title": t35, "state": "CLOSED", "body": b35,
         "comments": [{"body": "確認の結果: 推奨のまま"}, {"body": "確認の結果:変えた: K"}]},
        {"number": 36, "title": t36, "state": "CLOSED", "body": b36, "comments": [{"body": "確認の結果: 変えた: <新しい値>"}]},
    ]
    for issue in found:  # `comments` の鍵は #34（前の取り方）だけ持たない
        if not issue.pop("no_comments", False):
            issue.setdefault("comments", [])
    found[[i["number"] for i in found].index(23)]["comments"] = [{"body": "承認します。\n\n確認の結果: 推奨のまま"}]
    return found


class Case:
    def __init__(self, name: str, args: tuple[str, ...], code: int, has: tuple[str, ...] = (), lacks: tuple[str, ...] = (),
                 data=None, bundle: str = "", starts: str = ""):
        self.name, self.args, self.code, self.has, self.lacks, self.data = name, args, code, has, lacks, data
        self.starts = starts  # 標準出力がこれで始まる（下書きの先頭の行。#885）
        self.bundle = bundle  # まとめた本文の Issue だけの入力（`bundle`・改行を CRLF にした `crlf`）に当てる（#876）


CASES = [
    Case("暫定の Q-001", ("Q-001",), 0,
         ("Q-001（仮回答——本文に印がある）: 作り直す範囲 2 件", "#11 F-001: 割引額を計算する [OPEN]（F-001）——受入基準 `F-001-C1`",
          "#12 F-002: 注文を取り消せるか [CLOSED]（F-002）——ケースに無い（機能全体）"), ("`F-001-C2`", "#22")),
    Case("確定の Q-002", ("Q-002",), 0,
         ("Q-002: 作り直す範囲 2 件", "（F-001）——受入基準 `F-001-C2`", "（F-002）——ケースに無い（機能全体）"),
         ("仮回答", "`F-001-C1`")),
    Case("確認の Issue", ("#20",), 0, ("#20 要確認: 返品の受付期間を 7 日にした [OPEN]", "  決めた値: 7 日",
                                     "  影響する Issue: 2 件（作り直す範囲）", "  - #11 F-001: 割引額を計算する [OPEN]", "  - #12 F-002: 注文を取り消せるか [CLOSED]")),
    Case("印の無い確認の Issue（題で見分ける）", ("23",), 0, ("決めた値: B", "影響する Issue: なし", "  確認の結果: 推奨のまま")),
    Case("確認の結果がまだ無い", ("#20",), 0, ("  確認の結果: 結果なし",)),
    Case("開き直して変えた（最後の結果の行を採る）", ("#29",), 0, ("  確認の結果: 変えた: 14 日",), ("推奨のまま",)),
    Case("結果の行が形に反する", ("#32",), 1, ("結果の行が決まりの形でない（'確認の結果: 変えた: '）",)),
    Case("頭の後ろに空白が無い結果の行", ("#35",), 1, ("結果の行が決まりの形でない（'確認の結果:変えた: K'）",), ("推奨のまま",)),
    Case("写す前の値のままの結果の行", ("#36",), 1, ("結果の行が決まりの形でない（'確認の結果: 変えた: <新しい値>'）",)),
    Case("本文と装飾の結果の行は読まない", ("#33",), 0, ("  確認の結果: 結果なし",), ("本文の中", "変えた: 装飾", "文の途中")),
    Case("comments の無い入力", ("#34",), 0, ("  確認の結果: 読んでいない",), ("結果なし",)),
    Case("変わった確認だけ", ("--changed",), 1,
         ("変わった確認（確認の結果: 変えた）: 1 件",
          "#29 要確認: 開き直して変えた [CLOSED]——決めた値: A／影響する Issue: #11／確認の結果: 変えた: 14 日",
          "引けない——#32 要確認: 形に反する結果", "引けない——#34 要確認: 前の取り方",
          "引けない——#33 要確認: 本文と装飾の結果 [CLOSED]: 閉じたが 確認の結果: の行が無い"), ("#23 要確認", "#20 要確認", "#21 ")),
    Case("変えた確認の範囲を引ききれない", ("--changed",), 1,
         ("変わった確認（確認の結果: 変えた）: 3 件", "引けない——#40 要確認: 入力に無い Issue [CLOSED]: 影響する Issue #99 が入力に無い",
          "引けない——#41 要確認: 説明つき [CLOSED]: 台帳の行が決まりの形でない（作り直す範囲を引けない）",
          "引けない——#45 要確認: 台帳の行が無い [CLOSED]: 台帳の行が無い（前の書き方）（作り直す範囲を引けない）"), bundle="broken"),
    Case("変わった確認だけ（読めるものだけの入力）", ("--changed",), 0, ("変わった確認（確認の結果: 変えた）: 1 件", "#29 要確認"),
         ("引けない",), bundle="decided"),
    Case("--changed と番号", ("--changed", "#20"), 2, ("一緒には渡せない",)),
    Case("台帳の行が無い確認の Issue", ("#21",), 1, ("台帳の行（決めた値:・影響する Issue:）が無い",)),
    Case("影響する Issue に説明を添えた行", ("#24",), 1, ("台帳の行が決まりの形でない（'影響する Issue: #11（#12 の後続）'）",),
         ("#12 F-002",)),
    Case("影響する Issue が入力に無い", ("#25",), 1, ("#99（入力に無い", "#11 F-001")),
    Case("空の決めた値の行", ("#27",), 1, ("台帳の行が決まりの形でない（'決めた値: '）",), ("前の書き方",)),
    Case("空の影響する Issue の行", ("#28",), 1, ("台帳の行が決まりの形でない（'影響する Issue: '）",), ("前の書き方",)),
    Case("確認の Issue でない", ("#22",), 1, ("#22: 確認の Issue でない",)),
    Case("入力に無い番号", ("#99",), 1, ("#99: 入力に無い",)),
    Case("本文に無い No", ("Q-S-009",), 1, ("Q-S-009: 根拠にした spec-loop の Issue が無い",)),
    Case("引けるものと引けないもの", ("Q-001", "#22"), 1, ("作り直す範囲 2 件", "確認の Issue でない")),
    Case("一覧", (), 0, ("仮回答（本文に仮回答の印がある Q&A）: 1 件", "  Q-001: #11（F-001）、#12（F-002）",
                        "推奨で決めた事項（確認の Issue）: 13 件（開いているもの 7 件・変えたもの 1 件）",
                        "#24 要確認: 説明つきの行 [OPEN]——台帳の行が決まりの形でない",
                        "#23 要確認: 印の無い確認の Issue [CLOSED]——決めた値: B／影響する Issue: なし／確認の結果: 推奨のまま",
                        "#34 要確認: 前の取り方 [OPEN]——決めた値: H／影響する Issue: なし／確認の結果: 読んでいない",
                        "#20 要確認: 返品の受付期間を 7 日にした [OPEN]——決めた値: 7 日／影響する Issue: #11、#12",
                        "#21 返品の受付期間（前の書き方） [OPEN]——台帳の行が無い", "#23 要確認: 印の無い確認の Issue [CLOSED]——決めた値: B"),
         ("Q-002: #",)),
    Case("まとめた本文の部分ごとに引く", ("Q-001",), 0,
         ("Q-001（仮回答——本文に印がある）: 作り直す範囲 2 件",
          "#30 F-001・F-002: 割引額を計算する／注文を取り消せるか [OPEN]（F-001）——受入基準 `F-001-C1`",
          "#30 F-001・F-002: 割引額を計算する／注文を取り消せるか [OPEN]（F-002）——ケースに無い（機能全体）"), bundle="bundle"),
    Case("改行が CRLF のまとめた本文", ("Q-001",), 0,
         ("作り直す範囲 2 件", "（F-001）——受入基準 `F-001-C1`", "（F-002）——ケースに無い（機能全体）"), bundle="crlf"),
    # 作り直しの Issue の下書き（#885）
    Case("下書き（No）", ("--draft", "Q-001"), 0,
         ("## 作り直す範囲", "- #11 F-001: 割引額を計算する [OPEN]（F-001）——受入基準 `F-001-C1`",
          "- #12 F-002: 注文を取り消せるか [CLOSED]（F-002）——ケースに無い（機能全体）"), ("#26", "#22", "`F-001-C2`"),
         starts="作り直しの元: Q-001\n"),
    Case("下書き（変えた確認の Issue）", ("--draft", "#29"), 0,
         ("- 推奨で決めた値: A", "- 新しい値: 14 日", "## 作り直す範囲", "- #11 F-001: 割引額を計算する [OPEN]"),
         ("\n決めた値: ", "\n影響する Issue: ", "\n確認の結果: "), starts="作り直しの元: #29\n"),
    Case("下書き（結果がまだ無い確認の Issue）", ("--draft", "20"), 0,
         ("- 推奨で決めた値: 7 日", "- 新しい値: まだ無い（結果なし", "- #11 F-001", "- #12 F-002"), ("\n決めた値: ", "\n影響する Issue: ", "\n確認の結果: "),
         starts="作り直しの元: #20\n"),
    Case("下書き（影響する Issue が無い）", ("--draft", "#37"), 0, ("- 新しい値: L", "- なし（確認の Issue の影響する Issue が無い）"),
         starts="作り直しの元: #37\n", bundle="draft"),
    Case("下書き（まとめた本文）", ("--draft", "Q-001"), 0, ("（F-001）——受入基準 `F-001-C1`", "（F-002）——ケースに無い（機能全体）"),
         starts="作り直しの元: Q-001\n", bundle="bundle"),
    Case("下書き（推奨のまま）", ("--draft", "#23"), 1, ("推奨のまま——作り直すものが無い",), ("作り直しの元",)),
    Case("下書き（影響する Issue が入力に無い）", ("--draft", "#25"), 1, ("#99（入力に無い", "下書きを出さない"), ("作り直しの元",)),
    Case("下書き（台帳の行が無い）", ("--draft", "#21"), 1, ("台帳の行（決めた値:・影響する Issue:）が無い", "下書きを出さない"), ("作り直しの元",)),
    Case("下書き（結果の行が形に反する）", ("--draft", "#32"), 1, ("結果の行が決まりの形でない", "下書きを出さない"), ("作り直しの元",)),
    Case("下書き（確認の Issue でない）", ("--draft", "#22"), 1, ("#22: 確認の Issue でない",), ("作り直しの元",)),
    Case("下書き（本文に無い No）", ("--draft", "Q-S-009"), 1, ("下書きを出さない",), ("作り直しの元",)),
    Case("--draft と No", ("--draft", "#29", "Q-001"), 2, ("一緒には渡せない",), ("作り直しの元",)),
    Case("--draft と --changed", ("--draft", "#29", "--changed"), 2, ("一緒には渡せない",), ("作り直しの元",)),
    Case("--draft の値が No でも番号でもない", ("--draft", "foo"), 2, ("'foo': Q&A の No",)),
    Case("--draft を 2 回", ("--draft", "#29", "--draft", "#20"), 2, ("1 回だけ渡す",), ("作り直しの元",)),
    Case("下書き（comments の無い入力）", ("--draft", "#34"), 1, ("推奨のままかを読めないので下書きを出さない",), ("作り直しの元",)),
    Case("下書き（閉じたが結果の行が無い）", ("--draft", "#33"), 1, ("開いていると読めないのに 確認の結果: の行が無い",), ("作り直しの元",)),
    Case("下書き（状態が入力に無く結果の行が無い）", ("--draft", "#38"), 1, ("[状態不明]: 開いていると読めないのに",), ("作り直しの元",),
         bundle="draft"),
    Case("No でも番号でもない引数", ("foo",), 2, ("'foo': Q&A の No",)),
    Case("JSON でない", (), 2, ("読めない",), data="{"),
    Case("配列でない", (), 2, ("Issue の配列でない",), data="{}"),
    Case("本文が文字列でない", (), 2, ("0 番目が Issue の形でない",), data=json.dumps([{"number": 1, "title": "t", "body": 1}])),
    Case("comments の形が違う", (), 2, ("0 番目の comments が",),
         data=json.dumps([{"number": 1, "title": "t", "body": "b", "comments": [{"body": 1}]}])),
]

# (名前, 壊す箇所, 置き換え, 落ちるはずの試料)
MUTATIONS = [
    ("表の暫定の印を外さない", "                    text = text[: -len(scaffold.PROVISIONAL_CELL)]\n", "                    pass\n",
     "暫定の Q-001"),
    ("仕様の行を読まない", "            if line.startswith(scaffold.PROVISIONAL_LINE):", "            if False:", "一覧"),
    ("Q&A の回答の節を読まない", "section(body, scaffold.SECTIONS[3])", 'section(body, "## 無い節")', "確定の Q-002"),
    ("ケースに無いのに機能全体と言わない", 'if cases else "ケースに無い（機能全体）"', 'if cases else ""', "確定の Q-002"),
    ("確認の Issue を印で見分けない", 'return bool(DECISION_MARKER.search(issue["body"])) or ', "return ",
     "台帳の行が無い確認の Issue"),
    ("確認の Issue を題で見分けない", ' or issue["title"].startswith(DECISION_TITLE)', "",
     "印の無い確認の Issue（題で見分ける）"),
    ("影響する Issue を読まない", 'self.affects = [int(n) for n in re.findall(r"#([0-9]+)", rest)]', "self.affects = []",
     "確認の Issue"),
    ("台帳の行が無いのを引けたと言う", "    if d.value is None or d.affects is None:\n        missing",
     "    if False:\n        missing", "台帳の行が無い確認の Issue"),
    ("空の決めた値の行を無いと読む", "                if not self.value:\n", "                if False:\n", "空の決めた値の行"),
    ("空の影響する Issue の行を無いと読む", "                    self.malformed = line\n", "                    self.malformed = rest or None\n",
     "空の影響する Issue の行"),
    ("撤去の Issue も作り直す範囲に数える", ' and not REMOVAL.search(i["body"])\n', "\n", "暫定の Q-001"),
    ("説明の中の番号も影響する Issue に数える", "                elif AFFECTS_LIST.fullmatch(rest):", "                elif True:",
     "影響する Issue に説明を添えた行"),
    ("入力に無い影響する Issue でも 0", "    return not absent and d.result_malformed is None, out",
     "    return d.result_malformed is None, out", "影響する Issue が入力に無い"),
    ("引けない番号でも 0", "        code = code or (0 if ok else 1)", "        code = 0", "確認の Issue でない"),
    ("入力の Issue の形を見ない", "        if not (isinstance(issue, dict)", "        if False and not (isinstance(issue, dict)",
     "本文が文字列でない"),
    ("spec-loop の Issue を見分けない", 'handoffs = [Handoff(i, part) for i in issues if i["body"].startswith(HANDOFF_PREFIX) and',
     "handoffs = [Handoff(i, part) for i in [] if False and", "暫定の Q-001"),
    ("まとめた本文を部分に分けない", "    return [body[a:b] for a, b in zip(starts, starts[1:] + [len(body)])] or [body]",
     "    return [body]", "まとめた本文の部分ごとに引く"),
    ("CRLF の部分の頭を見ない", 'FEATURE.pattern + r"\\r?$"', 'FEATURE.pattern + r"$"', "改行が CRLF のまとめた本文"),
    ("結果の行を読まない", "                if not line.startswith(RESULT.rstrip()):", "                if True:",
     "印の無い確認の Issue（題で見分ける）"),
    ("最初の結果の行を採る", "self.result, self.result_malformed = rest, None", "self.result, self.result_malformed = self.result or rest, None",
     "開き直して変えた（最後の結果の行を採る）"),
    ("形に反する結果の行を採る", "self.result, self.result_malformed = None, line", "self.result, self.result_malformed = rest, None",
     "結果の行が形に反する"),
    ("結果の行が形に反しても 0", "    return not absent and d.result_malformed is None, out", "    return not absent, out",
     "結果の行が形に反する"),
    ("本文の結果の行も読む", "        for comment in comments or []:", '        for comment in (comments or []) + [{"body": issue["body"]}]:',
     "本文と装飾の結果の行は読まない"),
    ("comments の鍵が無いのを結果なしと読む", "self.comments_read = comments is not None", "self.comments_read = True",
     "comments の無い入力"),
    ("番号の引きに結果を出さない", 'out = [label(issue), f"  {RESULT}{d.outcome()}"]', "out = [label(issue)]",
     "印の無い確認の Issue（題で見分ける）"),
    ("一覧に結果を出さない", '——{entry(d)}／{RESULT}{d.outcome()}")', '——{entry(d)}")', "一覧"),
    ("comments の形を見ない", "        if not (isinstance(comments, list)", "        if False and not (isinstance(comments, list)",
     "comments の形が違う"),
    ("--changed が変えた以外も出す", "hits = [d for d in ordered if d.changed()]", "hits = [d for d in ordered if True]",
     "変わった確認だけ"),
    ("--changed で読めないものを黙る", "    return not bad, out, bad", "    return True, out, []", "変わった確認だけ"),
    ("頭の後ろに空白が無い行を読まない", "if not line.startswith(RESULT.rstrip()):", "if not line.startswith(RESULT):",
     "頭の後ろに空白が無い結果の行"),
    ("写す前の値のままの行を採る", 'and not (value.startswith("<") and value.endswith(">"))', "", "写す前の値のままの結果の行"),
    ("--changed で閉じて結果なしを黙る", "        elif closed and d.result is None:", "        elif False:", "変わった確認だけ"),
    ("--changed で変えた確認の台帳を見ない", "        elif d.changed() and (d.malformed is not None", "        elif False and (d.malformed is not None",
     "変えた確認の範囲を引ききれない"),
    ("--changed で影響する Issue の入力を見ない", "        elif d.changed() and (absent := ", "        elif False and (absent := ",
     "変えた確認の範囲を引ききれない"),
    ("--changed と番号を一緒に受ける", "    if args.changed and args.keys:", "    if False:", "--changed と番号"),
    ("No の下書きの先頭に印を付けない", '    out = [f"{ORIGIN}{no}", "",', '    out = ["", "",', "下書き（No）"),
    ("確認の Issue の下書きの先頭に印を付けない", '    out = [f"{ORIGIN}#{number}", "",', '    out = ["", "",', "下書き（変えた確認の Issue）"),
    ("下書きにケースを出さない", '        out.append(f"- {label(h.issue)}（{h.feature}）——{where(h, no)}")', '        out.append(f"- {label(h.issue)}（{h.feature}）")',
     "下書き（No）"),
    ("範囲が空の No でも下書きを出す", "    if not hits:\n        return False, [f\"{no}: 根拠にした spec-loop の Issue が無い——作り直す範囲が空",
     "    if False:\n        return False, [f\"{no}: 根拠にした spec-loop の Issue が無い——作り直す範囲が空", "下書き（本文に無い No）"),
    ("推奨のままでも下書きを出す", "    if d.result == KEPT:\n", "    if False:\n", "下書き（推奨のまま）"),
    ("引けない確認の Issue でも下書きを出す", "    if not ok:\n        return False, lines + [", "    if False:\n        return False, lines + [",
     "下書き（影響する Issue が入力に無い）"),
    ("新しい値を出さない", "    new = d.result[len(CHANGED):] if d.changed() else", '    new = "" if d.changed() else', "下書き（変えた確認の Issue）"),
    ("結果がまだ無いと言わない", 'else f"まだ無い（{d.outcome()}）"', 'else ""', "下書き（結果がまだ無い確認の Issue）"),
    ("影響する Issue を並べない", '    out += [f"- {label(issues[n])}" for n in d.affects] or', "    out += [] or", "下書き（変えた確認の Issue）"),
    ("影響する Issue が無いと言わない", '["- なし（確認の Issue の影響する Issue が無い）"]', "[]", "下書き（影響する Issue が無い）"),
    ("下書きの値を台帳の行の頭で書く", 'f"- 推奨で決めた値: {d.value}"', 'f"{DECIDED}{d.value}"', "下書き（変えた確認の Issue）"),
    ("--draft と No を一緒に受ける", "    if args.draft is not None and (args.keys or args.changed):", "    if False:", "--draft と No"),
    ("--draft と --changed を一緒に受ける", "(args.keys or args.changed)", "(args.keys)", "--draft と --changed"),
    ("--draft を 2 回でも受ける", "    if args.draft is not None and len(args.draft) > 1:", "    if False:", "--draft を 2 回"),
    ("comments が無くても下書きを出す", "    if not d.comments_read:\n        return False, [f\"{label(d.issue)}: {RESULT}{d.outcome()}——推奨",
     "    if False:\n        return False, [f\"{label(d.issue)}: {RESULT}{d.outcome()}——推奨", "下書き（comments の無い入力）"),
    ("閉じて結果なしでも下書きを出す", '    if (d.issue.get("state") or "").upper() != "OPEN" and d.result is None:', "    if False:",
     "下書き（閉じたが結果の行が無い）"),
    ("状態が無いのを開いていると読む", '(d.issue.get("state") or "").upper() != "OPEN"', '(d.issue.get("state") or "OPEN").upper() != "OPEN"',
     "下書き（状態が入力に無く結果の行が無い）"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def make_bodies(work: Path, scripts: Path) -> dict[str, str]:
    """本物の `scaffold.py --provisional` で本文を作る。`bundle` の鍵に、F-001 と F-002 をまとめた本文（`--bundle`。#876）も入れる。"""
    repo = work / "repo"
    base = repo / "docs" / "v1"
    (base / "shared").mkdir(parents=True)
    (base / "spec").mkdir(parents=True)
    (base / "shared" / "qa.csv").write_text(QA, encoding="utf-8")
    (base / "spec" / "order.md").write_text(SPEC, encoding="utf-8")
    (base / "spec" / "spec_ir.json").write_text(json.dumps(IR, ensure_ascii=False, indent=2), encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(scripts / "scaffold.py"), "--repo", str(repo), "--provisional"],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    issues = repo / "build" / "scaffold" / "issues"
    found = {p.stem: p.read_text(encoding="utf-8") for p in sorted(issues.glob("F-*.md"))}
    proc = subprocess.run([sys.executable, "-I", str(scripts / "scaffold.py"), "--repo", str(repo), "--provisional",
                           "--bundle", "F-001,F-002"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    found["bundle"] = (issues / "bundle-F-001-F-002.md").read_text(encoding="utf-8")
    return found


def run_case(scripts: Path, data: Path, case: Case) -> str | None:
    target = data.parent / f"{case.bundle}.json" if case.bundle else data
    if case.data is not None:
        target = data.parent / f"bad-{abs(hash(case.name))}.json"
        target.write_text(case.data, encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), "--issues", str(target), *case.args],
                          capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    if case.starts and not proc.stdout.startswith(case.starts):
        return f"標準出力が {case.starts!r} で始まらない: {proc.stdout[:200]!r}"
    if proc.returncode != case.code:
        return f"exit={proc.returncode}（期待 {case.code}）{out[-500:]}"
    for needle in case.has:
        if needle not in out:
            return f"出力に {needle!r} が無い: {out[-500:]}"
    for needle in case.lacks:
        if needle in out:
            return f"出力に {needle!r} がある: {out[-500:]}"
    return None


def constant(source: str, name: str):
    found = re.search(rf"^{name} = (.+)$", source, flags=re.MULTILINE)
    return ast.literal_eval(found.group(1)) if found else None


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="test-rebuild-scope-")).resolve()
    assert REAL_REPO not in work.parents
    try:
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        bodies = make_bodies(work, scripts)
        check("scaffold が F-001・F-002 の本文を作った", sorted(bodies) == ["F-001", "F-002", "bundle"], f"{sorted(bodies)}")
        data = work / "issues.json"
        data.write_text(json.dumps(issues_json(bodies), ensure_ascii=False), encoding="utf-8")
        (work / "bundle.json").write_text(json.dumps([{"number": 30, "title": "F-001・F-002: 割引額を計算する／注文を取り消せるか",
                                                        "state": "OPEN", "body": bodies["bundle"]}], ensure_ascii=False),
                                          encoding="utf-8")
        decided = [i for i in issues_json(bodies) if i["number"] in (11, 23, 29)]
        (work / "decided.json").write_text(json.dumps(decided, ensure_ascii=False), encoding="utf-8")
        changed_comment = [{"body": "確認の結果: 変えた: Z"}]
        broken = [{"number": 11, "title": "F-001", "state": "OPEN", "body": "x", "comments": []}]
        for number, title, lines in ((40, "要確認: 入力に無い Issue", "決めた値: A\n影響する Issue: #11, #99\n"),
                                     (41, "要確認: 説明つき", "決めた値: B\n影響する Issue: #11（説明）\n"),
                                     (45, "要確認: 台帳の行が無い", "")):
            t, b = decision(True, title, lines)
            broken.append({"number": number, "title": t, "state": "CLOSED", "body": b, "comments": changed_comment})
        (work / "broken.json").write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
        t37, b37 = decision(True, "要確認: 影響する Issue が無いまま変えた", "決めた値: K\n影響する Issue: なし\n")
        t38, b38 = decision(True, "要確認: 状態の無い入力", "決めた値: M\n影響する Issue: なし\n")
        (work / "draft.json").write_text(json.dumps([{"number": 37, "title": t37, "state": "CLOSED", "body": b37,
                                                       "comments": [{"body": "確認の結果: 変えた: L"}]},
                                                      {"number": 38, "title": t38, "body": b38, "comments": []}], ensure_ascii=False),
                                         encoding="utf-8")
        (work / "crlf.json").write_text(json.dumps([{"number": 31, "title": "まとめた本文（CRLF）", "state": "OPEN",
                                                      "body": bodies["bundle"].replace("\n", "\r\n")}], ensure_ascii=False),
                                        encoding="utf-8")

        print("正しい本体")
        for case in CASES:
            problem = run_case(scripts, data, case)
            check(f"試料: {case.name}", problem is None, problem or "")

        print("写しの突き合わせ")
        source = (scripts / TARGET).read_text(encoding="utf-8")
        doc = ABSENT_LINES.read_text(encoding="utf-8")
        decided, affects = constant(source, "DECIDED"), constant(source, "AFFECTS")
        for name, value in (("DECIDED", decided), ("AFFECTS", affects)):
            check(f"{name} が absent-lines.md の確認の Issue の書き方に無い",
                  isinstance(value, str) and f"**`{value}" in doc.split("## 確認の Issue の書き方", 1)[1], f"{value!r}")
        result, kept, changed = constant(source, "RESULT"), constant(source, "KEPT"), constant(source, "CHANGED")
        closing = doc.split("### 閉じるときの結果の 1 行", 1)[-1].split("\n### ", 1)[0] if "### 閉じるときの結果の 1 行" in doc else ""

        def copies_in(text: str) -> bool:
            return None not in (result, kept, changed) and f"**`{result}{kept}`**" in text and f"**`{result}{changed}<" in text

        check("RESULT・KEPT・CHANGED が absent-lines.md の閉じるときの結果の 1 行に無い", copies_in(closing), f"{(result, kept, changed)!r}")
        # 陽性対照: 原本の側を言い換えると、突き合わせが落ちる（頭・推奨のまま・変えたのそれぞれ）
        for old, new in ((result, "確認結果: "), (f"{result}{kept}", f"{result}了承"), (f"{result}{changed}", f"{result}変更: ")):
            check(f"陽性対照: 原本の {old!r} を言い換えると突き合わせが落ちる",
                  isinstance(old, str) and old in closing and not copies_in(closing.replace(old, new)))
        check("陽性対照: 言い換えると当たらない",
              f"**`{decided}" not in doc.replace(decided or "?", "決定した値: ").split("## 確認の Issue の書き方", 1)[1])

        # 作り直しの元の印（#885）: 原本（handoff-issue.md）と写し（spec-gap.md）に 2 つの形、absent-lines.md と dev-loop の SKILL.md は頭で指す
        origin = constant(source, "ORIGIN")

        def section_of(text: str, heading: str) -> str:
            return text.split(heading + "\n", 1)[1].split("\n## ", 1)[0] if heading + "\n" in text else ""

        def forms_in(text: str) -> bool:
            return isinstance(origin, str) and f"**`{origin}<Q&A の No>`**" in text and f"**`{origin}#<確認の Issue の番号>`**" in text

        handoff = section_of(HANDOFF.read_text(encoding="utf-8"), "## 作り直しの元の印")
        gap = section_of(SPEC_GAP.read_text(encoding="utf-8"), "## 作り直しの周")
        check("ORIGIN が handoff-issue.md の作り直しの元の印（原本）に 2 つの形で無い", forms_in(handoff), f"{origin!r}")
        check("ORIGIN が spec-gap.md の作り直しの周（写し）に 2 つの形で無い", forms_in(gap), f"{origin!r}")
        check("absent-lines.md が作り直しの元の印の頭で指していない", isinstance(origin, str) and f"`{origin}#<この確認の Issue>`" in doc
              and "`references/spec-gap.md` の「作り直しの周」" in doc, f"{origin!r}")
        skill = DEV_LOOP_SKILL.read_text(encoding="utf-8")
        check("dev-loop の SKILL.md が作り直しの元の印の頭で指していない", isinstance(origin, str) and f"行頭が `{origin}` の行" in skill
              and "`references/spec-gap.md` の「作り直しの周」" in skill, f"{origin!r}")
        # 陽性対照: 原本・写しの側を言い換えると、突き合わせが落ちる
        for name, text in (("handoff-issue.md", handoff), ("spec-gap.md", gap)):
            check(f"陽性対照: {name} の作り直しの元の印を言い換えると突き合わせが落ちる",
                  isinstance(origin, str) and origin in text and not forms_in(text.replace(origin, "作り直し元: ")))

        print("変異テスト")
        by_name = {case.name: case for case in CASES}
        pristine = source
        for name, old, new, target in MUTATIONS:
            count = pristine.count(old)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            (scripts / TARGET).write_text(pristine.replace(old, new), encoding="utf-8")
            try:
                problem = run_case(scripts, data, by_name[target])
            finally:
                (scripts / TARGET).write_text(pristine, encoding="utf-8")
            check(f"変異が素通りした: {name}（試料: {target}）", problem is not None)
        rules = docstring_rules()
        check("docstring の「守ること」の各行に変異がある（変異の数 ≥ 行の数）", len(MUTATIONS) >= rules,
              f"変異 {len(MUTATIONS)}・行 {rules}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


def docstring_rules() -> int:
    doc = ast.get_docstring(ast.parse(Path(__file__).read_text(encoding="utf-8"))) or ""
    block = doc.split("**守ること**", 1)[1].split("\n\n", 1)[1].split("\n\n", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("- "))


if __name__ == "__main__":
    sys.exit(main())
