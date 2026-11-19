#!/usr/bin/env python3
"""`check-review-record.py`（仕様レビューの記録から、抜ける条件 2・3 と実行の上限（#1044）と、条件 5 のうち内部の Q&A 表の行の確かめ（#1155）を数え直す）の回帰テスト。

    python3 scripts/test-check-review-record.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-findings-csv.py` と同じ形。

見るもの:

1. **`conditions`**——最後のレビューの Red Team に効く重さ（`判断が要る`・`結果が割れる`）の行が 1 行でも残る表で 1（Issue の受入基準 1。陽性対照）。
   `補い`・`退ける`・範囲の外・ほかの判定役の行だけなら 0。1 回目に直した行があれば最後のレビューは 2 回目（2 回目の行が 0 件でも）、
   直した行が無ければ 1 回目。狭いパスの効く重さは役を問わず 1。`--run` で前の回を数える。
2. **`limit`**——数え始め（`続ける`・`範囲を決め直す` の最後の行の後）からの `満たさない`・`判定できなかった` の実行の行が N 以上で 3、未満で 0、
   最後の利用者の判断が `止める` なら 3、`回答待ち`・`満たす` は数えない、表が無ければ 0、`--limit` で N を変える。
3. **`internal`（#1155）**——作業中の版で足した・変えた内部の行（`D-`）に、その回の Domain Checker の確かめた行（印 `（内部の行: <No>）`・`確かめた`）が
   無ければ 1（陽性対照）、すべてあれば 0。前の版から変わらない行・消した行は求めない。`確かめられない` の行・ほかの判定役・前の回の行は数えない。
   `共有の Q&A 表に起票する` に振り分けたのに内部の表に残る行は 1、移していれば 0。確かめる行が無ければ 0。重ね合わせの違反・版が読めない・`--docs` が無いなら 2。
   `conditions` は、確かめの行だけの 1 回目を 2 回目ありと読まない。
   **同じ回の中で、同じ内部の行の判定（重さ）が段ごとに食い違ったら `割れた:` と名指しし、終了コードは変えない**（#1248）——
   割れても確かめていない行があれば 1 のまま、同じ判定の段・`確かめられない` の行・前の回の判定は割れに数えない。名指しの変異は出力の語の有無で殺す（`OUTPUT_KILLED`）。
4. **中身を数えていない形を 0 にしない（2）**——指摘の表が検査に通らない・実行の行が無い・`--run` が実行の行でない・見出しが欠けた記録・引数の誤り。
5. **本体の定数が references と一致する**（`references/spec-exit.md` の「指摘の重さ」の効く重さ・「上限」の数える値と数え直しの判断・
   「指摘の表」の内部の行の印——`agents/domain-checker.md` の印も同じ形か）。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料の終了コードが変わること**を確かめる（文言の違いでは殺したと数えない）。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-review-record.py"
SPEC_EXIT = PLUGIN / "references" / "spec-exit.md"
SPEC_REVIEW = PLUGIN / "skills" / "spec-review" / "SKILL.md"
DOMAIN_CHECKER = PLUGIN / "agents" / "domain-checker.md"

R_HEAD = "回,日付,結果,条件2〜4,要求の行,決定表の行,テストケース,仕様の行,判断,機能\n"


def run_row(no: str, day: str, result: str = "抜けていない", cond: str = "満たさない", decision: str = "-", feature: str = "注文") -> str:
    is_run = result in ("抜けた", "抜けていない")
    size = "10,5,8,40" if is_run else "-,-,-,-"
    return f"{no},{day},{result},{cond if is_run else '-'},{size},{decision},{feature if is_run else '-'}\n"


RUNS = R_HEAD + run_row("1", "2026-11-01") + run_row("2", "2026-11-02", "抜けた", "満たす", feature="-")
F_HEAD = "回,日付,レビュー,判定役,重さ,確かめたか,振り分け,指摘,根拠,結果\n"


def f(no="2", day="2026-11-02", review="1回目", judge="red-team", weight="補い", category="仕様を直す", confirmed="確かめた",
      text="境界の 0 が無い", result="spec/a.md:4") -> str:
    if confirmed == "確かめられない":
        category, result = "-", "-"
    return ",".join([no, day, review, judge, weight, confirmed, category, text, "spec/a.md:3", result]) + "\n"


QA_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"


def qa(no: str, question: str) -> str:
    return f"{no},仕様レビュー（Domain Checker）,{question},A: 甲 / B: 乙,A,理由,A（開発 山田 2026-11-01）,spec/a.md 1 節,反映済み,\n"


# 正本の docs（版 → 置くファイル）。v1 の内部の行は D-001・D-002・D-004、v2 で D-002 を変え・D-003 を足し・D-004 を消す（D-001 は変わらない）
DOCS_V1 = {"v1/shared/qa.csv": QA_HEAD + qa("Q-001", "共有1"),
           "v1/spec/qa-dev.csv": QA_HEAD + qa("D-001", "内部1") + qa("D-002", "内部2") + qa("D-004", "内部4"),
           "v1/spec/a.md": "a\n"}
DOCS_V2 = {**DOCS_V1, "v2/spec/qa-dev.csv": QA_HEAD + qa("D-002", "内部2 を変えた") + qa("D-003", "内部3"),
           "v2/removed.csv": "種類,対象,理由\nQ&A,D-004,要らなくなった\n"}
# D-003 を共有の表へ移した（Q-002）——v2 の内部の表から消えている
DOCS_V2_MOVED = {**DOCS_V1, "v2/spec/qa-dev.csv": QA_HEAD + qa("D-002", "内部2 を変えた"),
                 "v2/shared/qa.csv": QA_HEAD + qa("Q-001", "共有1") + "Q-002,仕様レビュー（Domain Checker。D-003 から移した）,内部3,A: 甲 / B: 乙,A,理由,未回答,—,確認中,\n",
                 "v2/removed.csv": "種類,対象,理由\nQ&A,D-004,要らなくなった\n"}
RUNS2 = R_HEAD + run_row("1", "2026-11-03", "抜けていない", "満たす", feature="-")


def dc(no: str, review="1回目", category="内部の Q&A 表に記録する", weight="補い", confirmed="確かめた", judge="domain-checker",
       run="1", day="2026-11-03", colon=": ") -> str:
    """Domain Checker が内部の行を確かめた指摘の行（印 `（内部の行: <No>）`。`colon` で全角のコロンも作る）。"""
    return f(no=run, day=day, review=review, judge=judge, weight=weight, category=category, confirmed=confirmed,
             text=f"（内部の行{colon}{no}）利用者に見える結果は変わらない", result="内部のまま")


# 名前 → (サブコマンド, 指摘の表（None なら置かない）, 記録の表（None なら置かない）, 足す引数, 期待の終了コード, 出力に含む語[, 正本の docs, 版])
CASES: dict[str, tuple] = {
    # ---- conditions
    "条件: 判断が要るが 1 行（陽性対照）": ("conditions", F_HEAD + f(weight="判断が要る", category="共有の Q&A 表に起票する", result="Q-001"),
                                     RUNS, [], 1, "満たさない: 回 2・最後のレビューは 1回目"),
    "条件: 結果が割れるが 2 回目に 1 行": ("conditions", F_HEAD + f() + f(review="2回目", weight="結果が割れる", result="次の回"), RUNS, [], 1, "最後のレビューは 2回目"),
    # 2 回目のあとで直した行（`結果` が `次の回` でない）は狭いパスに任せて数えない（2 パス目の CR2-1）
    "条件: 2 回目のあとで直した行は数えない": ("conditions", F_HEAD + f() + f(review="2回目", weight="結果が割れる", result="spec/a.md:12"),
                                   RUNS, [], 0, "満たす: 回 2・最後のレビューは 2回目（その行 1 件）"),
    "条件: 2 回目のあとで直しても狭いパスの効く重さは数える": ("conditions", F_HEAD + f() + f(review="2回目", weight="結果が割れる", result="spec/a.md:12")
                                            + f(review="狭いパス", weight="結果が割れる", result="次の回"), RUNS, [], 1, "狭いパス・red-team"),
    # `判断が要る` は直しても解消済みにならない（spec-exit.md。狭いパスの N1）
    "条件: 2 回目の判断が要るは直しても数える": ("conditions", F_HEAD + f() + f(review="2回目", weight="判断が要る", result="spec/a.md:12"),
                                     RUNS, [], 1, "2回目・red-team・判断が要る"),
    "条件: 2 回目の起票の行は直しでないので数える": ("conditions", F_HEAD + f() + f(review="2回目", weight="結果が割れる", category="共有の Q&A 表に起票する",
                                                                     result="Q-009"), RUNS, [], 1, "最後のレビューは 2回目"),
    "条件: 補いだけ": ("conditions", F_HEAD + f() + f(review="2回目", result="次の回") + f(review="2回目", judge="domain-checker", result="次の回"),
                RUNS, [], 0, "満たす: 回 2"),
    "条件: 退けた行は数えない": ("conditions", F_HEAD + f(weight="結果が割れる", category="退ける", result="誤り"), RUNS, [], 0, "満たす"),
    "条件: 範囲の外・実装に渡すは数えない": ("conditions", F_HEAD + f(weight="-", category="実装に渡す") + f(weight="-", category="範囲の外として記録する"),
                                    RUNS, [], 0, "満たす"),
    "条件: ほかの判定役の効く重さは数えない": ("conditions", F_HEAD + f(review="2回目", judge="domain-checker", weight="判断が要る", category="共有の Q&A 表に起票する")
                                     + f(review="2回目", judge="formal-checker", weight="結果が割れる"), RUNS, [], 0, "満たす"),
    "条件: 1 回目に直した行は 2 回目が指摘なしなら数えない": ("conditions", F_HEAD + f(weight="結果が割れる"), RUNS, [], 0, "最後のレビューは 2回目（その行 0 件）"),
    "条件: 範囲の外に足した行も 2 回目を回す": ("conditions", F_HEAD + f(weight="判断が要る", category="共有の Q&A 表に起票する", result="Q-001")
                                    + f(weight="-", category="範囲の外として記録する"), RUNS, [], 0, "最後のレビューは 2回目"),
    "条件: 1 回目が直さなければ 2 回目は無い": ("conditions", F_HEAD + f(weight="結果が割れる", category="共有の Q&A 表に起票する", result="Q-001"),
                                   RUNS, [], 1, "最後のレビューは 1回目"),
    # 内部の Q&A 表に記録した行は、その回に決めて仕様に反映すれば 2 回目が回る（1 パス目の CR3）
    "条件: 内部の Q&A に記録した行も 2 回目を回す": ("conditions", F_HEAD + f(weight="結果が割れる", category="内部の Q&A 表に記録する", result="D-001"),
                                       RUNS, [], 0, "最後のレビューは 2回目（その行 0 件）"),
    # 確かめの行（印つきの 内部の Q&A 表に記録する）は仕様を直していないので 2 回目を回さない（#1155）
    "条件: 内部の行の確かめだけでは 2 回目を回さない": ("conditions", F_HEAD + f(weight="結果が割れる", category="共有の Q&A 表に起票する", result="Q-001")
                                         + dc("D-001", run="2", day="2026-11-02"), RUNS, [], 1, "最後のレビューは 1回目"),
    # 確かめの行に当たるのは domain-checker・内部の Q&A 表に記録する・印の 3 つが揃う行だけ（1 パス目の CR1-1・CR1-2）
    "条件: 印を引いた Red Team の直しは 2 回目を回す": ("conditions", F_HEAD + f(weight="結果が割れる", category="共有の Q&A 表に起票する", result="Q-001")
                                         + f(weight="結果が割れる", category="内部の Q&A 表に記録する", text="（内部の行: D-002）を決め直す", result="D-002"),
                                         RUNS, [], 0, "最後のレビューは 2回目"),
    "条件: 仕様に移した印つきの行は 2 回目を回す": ("conditions", F_HEAD + f(weight="結果が割れる", category="共有の Q&A 表に起票する", result="Q-001")
                                       + dc("D-001", run="2", day="2026-11-02", category="仕様を直す"), RUNS, [], 0, "最後のレビューは 2回目"),
    "条件: 全角のコロンの確かめも 2 回目を回さない": ("conditions", F_HEAD + f(weight="結果が割れる", category="共有の Q&A 表に起票する", result="Q-001")
                                         + dc("D-001", run="2", day="2026-11-02", colon="："), RUNS, [], 1, "最後のレビューは 1回目"),
    "条件: 1 回目の効く重さは 2 回目があれば数えない": ("conditions", F_HEAD + f(weight="結果が割れる") + f(review="2回目"), RUNS, [], 0, "満たす"),
    "条件: 狭いパスはほかの役でも数える": ("conditions", F_HEAD + f() + f(review="狭いパス", judge="formal-checker", weight="結果が割れる"),
                                RUNS, [], 1, "狭いパス・formal-checker"),
    "条件: 確かめられない行は重さのまま数える": ("conditions", F_HEAD + f(weight="判断が要る", confirmed="確かめられない"), RUNS, [], 1, "満たさない"),
    "条件: 前の回の行は数えない": ("conditions", F_HEAD + f(no="1", day="2026-11-01", weight="判断が要る", category="共有の Q&A 表に起票する")
                           + f(category="共有の Q&A 表に起票する", result="Q-002"), RUNS, [], 0, "満たす: 回 2・最後のレビューは 1回目"),
    "条件: --run で前の回を数える": ("conditions", F_HEAD + f(no="1", day="2026-11-01", weight="判断が要る", category="共有の Q&A 表に起票する")
                             + f(), RUNS, ["--run", "1"], 1, "回 1"),
    "条件: 見出しだけの表": ("conditions", F_HEAD, RUNS, [], 0, "満たす"),
    # ---- internal（#1155）
    "内部: 確かめた行が無い（陽性対照）": ("internal", F_HEAD + f(no="1", day="2026-11-03"), RUNS2, [], 1, "D-003: Domain Checker が確かめた行", DOCS_V2, 2),
    "内部: 足した・変えた行をすべて確かめた": ("internal", F_HEAD + dc("D-002") + dc("D-003", review="2回目"), RUNS2, [], 0,
                                    "満たす: 回 1・v2 で足した・変えた内部の行 2 件——すべて", DOCS_V2, 2),
    "内部: 1 行だけ確かめていない": ("internal", F_HEAD + dc("D-002"), RUNS2, [], 1, "確かめていない・移していない行が 1 件", DOCS_V2, 2),
    "内部: v1 は全部の行": ("internal", F_HEAD + dc("D-001") + dc("D-002"), RUNS2, [], 1, "D-004:", DOCS_V1, 1),
    "内部: 全角のコロンの印も数える": ("internal", F_HEAD + dc("D-002", colon="：") + dc("D-003", colon="： "), RUNS2, [], 0, "すべて", DOCS_V2, 2),
    "内部: 確かめられない行は数えない": ("internal", F_HEAD + dc("D-002") + dc("D-003", confirmed="確かめられない"), RUNS2, [], 1, "D-003:", DOCS_V2, 2),
    "内部: ほかの判定役の行は数えない": ("internal", F_HEAD + dc("D-002") + dc("D-003", judge="red-team"), RUNS2, [], 1, "D-003:", DOCS_V2, 2),
    "内部: 前の回の行は数えない": ("internal", F_HEAD + dc("D-002", run="1", day="2026-11-02") + dc("D-003", run="1", day="2026-11-02") + dc("D-002", run="2"),
                           R_HEAD + run_row("1", "2026-11-02", "抜けていない", "満たす", feature="-")
                           + run_row("2", "2026-11-03", "抜けていない", "満たす", feature="-"), [], 1, "D-003:", DOCS_V2, 2),
    "内部: 移すと決めたのに残る": ("internal", F_HEAD + dc("D-002") + dc("D-003", category="共有の Q&A 表に起票する", weight="判断が要る"), RUNS2, [], 1,
                           "D-003 は 共有の Q&A 表に起票する に振り分けたのに", DOCS_V2, 2),
    "内部: 移した行は求めない": ("internal", F_HEAD + dc("D-002") + dc("D-003", category="共有の Q&A 表に起票する", weight="判断が要る"), RUNS2, [], 0,
                          "内部の行 1 件——すべて", DOCS_V2_MOVED, 2),
    "内部: 退けた行は残ってよい": ("internal", F_HEAD + dc("D-002") + dc("D-003", category="退ける", weight="判断が要る"), RUNS2, [], 0, "すべて", DOCS_V2, 2),
    # ---- 判定が段ごとに割れた行の名指し（#1248）。終了コードには数えない
    "内部: 割れた行を名指しする（陽性対照）": ("internal", F_HEAD + dc("D-002") + dc("D-002", review="2回目", category="退ける", weight="判断が要る")
                                   + dc("D-002", review="狭いパス", category="退ける", weight="判断が要る") + dc("D-003"), RUNS2, [], 0,
                                   "割れた: D-002 の判定が同じ回の中で段ごとに食い違う——1回目=変わらない（2 行目）・2回目=変わる（3 行目）・狭いパス=変わる（4 行目）",
                                   DOCS_V2, 2),
    "内部: 割れても確かめていない行があれば 1 のまま名指しする": ("internal", F_HEAD + dc("D-002") + dc("D-002", review="狭いパス", weight="判断が要る"), RUNS2, [], 1,
                                           "割れた: D-002", DOCS_V2, 2),
    "内部: 結果が割れるも変わる側として割れを名指しする": ("internal", F_HEAD + dc("D-002") + dc("D-002", review="2回目", weight="結果が割れる", category="退ける") + dc("D-003"),
                                         RUNS2, [], 0, "割れた: D-002", DOCS_V2, 2),
    "内部: 確かめる行が無くても割れを名指しする": ("internal", F_HEAD + dc("D-001") + dc("D-001", review="狭いパス", weight="判断が要る"), RUNS2, [], 0, "割れた: D-001",
                                  {**DOCS_V1, "v2/shared/qa.csv": QA_HEAD + qa("Q-001", "共有1"), "v2/spec/qa-dev.csv": QA_HEAD + qa("D-001", "内部1")}, 2),
    "内部: 往復した判定も割れと名指しする": ("internal", F_HEAD + dc("D-002") + dc("D-002", review="2回目", weight="判断が要る", category="退ける") + dc("D-002", review="狭いパス", category="退ける")
                                 + dc("D-003"), RUNS2, [], 0, "割れた: D-002", DOCS_V2, 2),
    "内部: 同じ判定の段は割れと読まない": ("internal", F_HEAD + dc("D-002") + dc("D-002", review="2回目") + dc("D-003", weight="判断が要る", category="退ける")
                                 + dc("D-003", review="狭いパス", weight="判断が要る", category="退ける"), RUNS2, [], 0, "!割れた", DOCS_V2, 2),
    "内部: 確かめられない行は割れに数えない": ("internal", F_HEAD + dc("D-002") + dc("D-003") + dc("D-002", review="2回目", confirmed="確かめられない", weight="判断が要る"),
                                   RUNS2, [], 0, "!割れた", DOCS_V2, 2),
    "内部: 前の回の判定は割れに数えない": ("internal", F_HEAD + dc("D-002", run="1", day="2026-11-02", weight="判断が要る") + dc("D-002", run="2") + dc("D-003", run="2"),
                               R_HEAD + run_row("1", "2026-11-02", "抜けていない", "満たす", feature="-")
                               + run_row("2", "2026-11-03", "抜けていない", "満たす", feature="-"), [], 0, "!割れた", DOCS_V2, 2),
    "内部: 確かめる行が無い": ("internal", F_HEAD, RUNS2, [], 0, "確かめる行が無い",
                         {**DOCS_V1, "v2/shared/qa.csv": QA_HEAD + qa("Q-001", "共有1"), "v2/spec/qa-dev.csv": QA_HEAD + qa("D-001", "内部1")}, 2),
    "判定しない: 内部の重ね合わせが決まりに反する": ("internal", F_HEAD + dc("D-002"), RUNS2, [], 2, "重ね合わせが決まりに反する",
                                      {**DOCS_V2, "v2/removed.csv": "種類,対象\nQ&A,D-004\n"}, 2),
    "判定しない: 内部の版が無い": ("internal", F_HEAD + dc("D-002"), RUNS2, [], 2, "正本の版を読めない", DOCS_V1, 2),
    "判定しない: --docs が無い": ("internal-nodocs", F_HEAD + dc("D-002"), RUNS2, [], 2, "--docs", DOCS_V2, 2),
    "判定しない: 指摘の表が検査に通らない": ("conditions", F_HEAD + f(weight="重い"), RUNS, [], 2, "検査に通らない"),
    "判定しない: 実行の記録が無い": ("conditions", F_HEAD + f(), None, [], 2, "実行の記録が無い"),
    "判定しない: 実行の行が無い": ("conditions", F_HEAD, R_HEAD + run_row("1", "2026-11-01", "モデルの保存"), [], 2, "実行の行"),
    "判定しない: --run が実行の行でない": ("conditions", F_HEAD + f(), RUNS, ["--run", "9"], 2, "回 9 は実行の行でない"),
    "判定しない: --run の形": ("conditions", F_HEAD + f(), RUNS, ["--run", "01"], 2, "--run は 1 からの番号"),
    # ---- limit
    "上限: 3 行で達する": ("limit", None, R_HEAD + run_row("1", "2026-11-01") + run_row("2", "2026-11-02", cond="判定できなかった", feature="-")
                        + run_row("3", "2026-11-03"), [], 3, "上限: 3 件 ≧ 3"),
    "上限: 2 行なら達しない": ("limit", None, R_HEAD + run_row("1", "2026-11-01") + run_row("2", "2026-11-02"), [], 0, "あと 1 回"),
    "上限: 回答待ち・満たすは数えない": ("limit", None, R_HEAD + run_row("1", "2026-11-01") + run_row("2", "2026-11-02", cond="回答待ち")
                               + run_row("3", "2026-11-03", cond="満たす") + run_row("4", "2026-11-04"), [], 0, "2 件"),
    "上限: 続けるの後から数える": ("limit", None, R_HEAD + run_row("1", "2026-11-01") + run_row("2", "2026-11-02") + run_row("3", "2026-11-03")
                          + run_row("4", "2026-11-03", "上限") + run_row("5", "2026-11-03", "利用者の判断", decision="続ける")
                          + run_row("6", "2026-11-04"), [], 0, "数え始め: 回 6 から"),
    "上限: 範囲を決め直すの後から数える": ("limit", None, R_HEAD + run_row("1", "2026-11-01") + run_row("2", "2026-11-02") + run_row("3", "2026-11-03")
                               + run_row("4", "2026-11-03", "利用者の判断", decision="範囲を決め直す"), [], 0, "0 件"),
    "上限: 止めるなら数えずに達する": ("limit", None, R_HEAD + run_row("1", "2026-11-01", "利用者の判断", decision="止める"), [], 3, "止める"),
    "上限: 止めるの前の続けるは効かない": ("limit", None, R_HEAD + run_row("1", "2026-11-01", "利用者の判断", decision="続ける")
                                + run_row("2", "2026-11-02", "利用者の判断", decision="止める"), [], 3, "止める"),
    "上限: 止めるの後に続けるなら数える": ("limit", None, R_HEAD + run_row("1", "2026-11-01", "利用者の判断", decision="止める")
                                + run_row("2", "2026-11-02", "利用者の判断", decision="続ける"), [], 0, "0 件"),
    "上限: 表が無ければ 0 回": ("limit", None, None, [], 0, "実行 0 回"),
    "上限: --limit で N を変える": ("limit", None, R_HEAD + run_row("1", "2026-11-01") + run_row("2", "2026-11-02"), ["--limit", "2"], 3, "上限: 2 件 ≧ 2"),
    "上限: 機能がすべて - なら言う": ("limit", None, R_HEAD + run_row("1", "2026-11-01", cond="判定できなかった", feature="-"), ["--limit", "1"], 3,
                              "すべて `-`"),
    # 列の欠けた行を飛ばすと、上限に達した記録で 0 になる（1 パス目の CR4）
    "判定しない: 記録の行の列が足りない": ("limit", None, R_HEAD + "1,2026-11-01,抜けていない,満たさない\n2,2026-11-02,抜けていない,満たさない\n"
                                + run_row("3", "2026-11-03"), [], 2, "列が足りない"),
    "判定しない: 記録の見出しに判断が無い": ("limit", None, R_HEAD.replace(",判断,", ",決定,") + run_row("1", "2026-11-01"), [], 2, "判断 が無い"),
    "判定しない: --limit が 0": ("limit", None, RUNS, ["--limit", "0"], 2, "--limit は 1 以上"),
    "判定しない: 引数なし": ("", None, RUNS, [], 2, "usage"),
}

# 終了コードを変えず、出力の語の有無でだけ殺す変異（#1248。割れた行の名指しは出力だけで、終了コードに数えない）
OUTPUT_KILLED = {"割れを名指ししない", "最初と最後だけを比べる", "結果が割れるを変わると読まない", "確かめる行が無いとき割れを出さない", "同じ判定の段も割れと読む", "重さでなく振り分けで判定を読む"}

# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("効く重さを見ない", "               if c[\"重さ\"] in EFFECTIVE and c[\"振り分け\"] != REJECTED\n",
     "               if c[\"振り分け\"] != REJECTED\n", "条件: 補いだけ"),
    ("退けた行も数える", " and c[\"振り分け\"] != REJECTED\n", "\n", "条件: 退けた行は数えない"),
    ("Red Team に絞らない", " and c[\"判定役\"] == RED_TEAM and", " and",
     "条件: ほかの判定役の効く重さは数えない"),
    ("狭いパスを数えない", " or c[\"レビュー\"] == NARROW)]", ")]", "条件: 狭いパスはほかの役でも数える"),
    ("1 回目の直しで 2 回目と読まない", "    second = any(c[\"レビュー\"] == SECOND for _, c in mine) or any(\n",
     "    second = any(c[\"レビュー\"] == SECOND for _, c in mine) and any(\n", "条件: 1 回目に直した行は 2 回目が指摘なしなら数えない"),
    ("いつも 2 回目と読む", "    last = SECOND if second else FIRST\n", "    last = SECOND\n", "条件: 1 回目が直さなければ 2 回目は無い"),
    ("回で絞らない", "    return run, [(number, c) for number, c in enumerate(cells, start=2) if c[\"回\"] == run], []\n",
     "    return run, [(number, c) for number, c in enumerate(cells, start=2)], []\n", "条件: 前の回の行は数えない"),
    ("検査に通らない表を数える", "    if code:\n        return None, [], problems", "    if False:\n        return None, [], problems",
     "判定しない: 指摘の表が検査に通らない"),
    # 「判定しない（2）」を崩す変異は、別の例外で 2 のままの形にしない——判定して 0 を返す形にする
    ("実行の行が無いのに満たすと言う", "    if not runs:\n        return None, [], [", "    if not runs:\n        return \"1\", [], [", "判定しない: 実行の行が無い"),
    ("--run を見ない", "    elif run not in {r[\"回\"] for r in runs}:\n", "    elif False:\n", "判定しない: --run が実行の行でない"),
    ("数えたのに 0", "    return EXIT_UNMET, lines + [f\"満たさない: {seen}——効く重さ", "    return EXIT_OK, lines + [f\"満たさない: {seen}——効く重さ",
     "条件: 判断が要るが 1 行（陽性対照）"),
    ("止めるを見ない", "    if decisions and rows[decisions[-1]][\"判断\"] == STOP:\n", "    if False:\n", "上限: 止めるなら数えずに達する"),
    ("数え始めを見ない", "    start = max((i for i in decisions if rows[i][\"判断\"] in RECOUNT), default=-1) + 1\n", "    start = 0\n",
     "上限: 続けるの後から数える"),
    ("回答待ちも数える", " and r[\"条件2〜4\"] in COUNTED]", "]", "上限: 回答待ち・満たすは数えない"),
    ("N を 1 つずらす", "    if len(counted) >= n:\n", "    if len(counted) > n:\n", "上限: 3 行で達する"),
    ("--limit を使わない", "            code, lines = limit(args.record, int(args.limit))\n", "            code, lines = limit(args.record, LIMIT)\n",
     "上限: --limit で N を変える"),
    ("内部の Q&A で 2 回目と読まない", ', "内部の Q&A 表に記録する")', ")", "条件: 内部の Q&A に記録した行も 2 回目を回す"),
    ("列の足りない行を飛ばす", "    if short:\n", "    if False:\n", "判定しない: 記録の行の列が足りない"),
    ("2 回目のあとで直した行も数える", " and not fixed_after_second(c))", ")", "条件: 2 回目のあとで直した行は数えない"),
    ("次の回の行も直したと読む", 'and c["振り分け"] == FIX and c["結果"] != NEXT_RUN and',
     'and c["振り分け"] == FIX and', "条件: 結果が割れるが 2 回目に 1 行"),
    ("起票の行も直したと読む", 'and c["振り分け"] == FIX and c["結果"] != NEXT_RUN and',
     'and c["結果"] != NEXT_RUN and', "条件: 2 回目の起票の行は直しでないので数える"),
    ("判断が要るも直したと読む", ' and c["重さ"] != DECIDE\n', "\n", "条件: 2 回目の判断が要るは直しても数える"),
    # ---- internal（#1155）
    ("確かめの行で 2 回目と読む", " and not is_confirmation(c) for _, c in mine)", " for _, c in mine)", "条件: 内部の行の確かめだけでは 2 回目を回さない"),
    ("確かめの行を判定役で絞らない", 'return c["判定役"] == DOMAIN_CHECKER and c["振り分け"] == KEEP and', 'return c["振り分け"] == KEEP and',
     "条件: 印を引いた Red Team の直しは 2 回目を回す"),
    ("確かめの行を振り分けで絞らない", 'return c["判定役"] == DOMAIN_CHECKER and c["振り分け"] == KEEP and', 'return c["判定役"] == DOMAIN_CHECKER and',
     "条件: 仕様に移した印つきの行は 2 回目を回す"),
    ("全角のコロンを読まない", "（内部の行\\s*[:：]\\s*", "（内部の行: ", "条件: 全角のコロンの確かめも 2 回目を回さない"),
    ("全角のコロンを内部で読まない", "（内部の行\\s*[:：]\\s*", "（内部の行\\s*:\\s*", "内部: 全角のコロンの印も数える"),
    ("内部: 確かめていない行を見ない", " for no in targets if no not in judged]", " for no in targets if False]", "内部: 確かめた行が無い（陽性対照）"),
    ("内部: 満たさないのに 0", "        return EXIT_UNMET, lines + [f\"満たさない: {seen}", "        return EXIT_OK, lines + [f\"満たさない: {seen}",
     "内部: 1 行だけ確かめていない"),
    ("内部: 消した行も確かめる行に数える", " if c.status != diff_versions.REMOVED]", "]", "内部: 足した・変えた行をすべて確かめた"),
    ("内部: 前の版から変わらない行も求める", "    targets = [c.key for c in diff.changes[diff_versions.KIND_QA_INTERNAL]",
     "    targets = list(diff_versions.qa_layers(whole)[1]) or [c.key for c in diff.changes[diff_versions.KIND_QA_INTERNAL]",
     "内部: 足した・変えた行をすべて確かめた"),
    ("内部: 確かめられない行も数える", " and c[\"確かめたか\"] == findings.CONFIRMED:", ":", "内部: 確かめられない行は数えない"),
    ("内部: ほかの判定役も数える", " and c[\"判定役\"] == DOMAIN_CHECKER and", " and", "内部: ほかの判定役の行は数えない"),
    ("内部: 移していない行を見ない", " if c[\"振り分け\"] == MOVE]", " if False]", "内部: 移すと決めたのに残る"),
    ("内部: 退けた行も移すと読む", " if c[\"振り分け\"] == MOVE]", " if c[\"振り分け\"] in (MOVE, \"退ける\")]", "内部: 退けた行は残ってよい"),
    ("内部: 重ね合わせの違反でも判定する", "        return EXIT_UNJUDGED, problems + [f\"v{version}", "        return EXIT_OK, problems + [f\"v{version}",
     "判定しない: 内部の重ね合わせが決まりに反する"),
    ("内部: 版が読めないのに判定する", "        return EXIT_UNJUDGED, [f\"正本の版を読めない", "        return EXIT_OK, [f\"正本の版を読めない", "判定しない: 内部の版が無い"),
    # ---- 割れた行の名指し（#1248）。名指しは出力だけで終了コードを変えないので、殺す条件は「期待どおりでなくなる」（終了コードか、語の有無）
    ("割れを名指ししない", "    split = split_judgments(judged)  #", "    split = []  #", "内部: 割れた行を名指しする（陽性対照）"),
    ("割れを終了コードに数える", '    return EXIT_OK, [f"満たす: {seen}——すべて Domain Checker が確かめた"] + split\n',
     '    return (EXIT_UNMET if split else EXIT_OK), [f"満たす: {seen}——すべて Domain Checker が確かめた"] + split\n', "内部: 割れた行を名指しする（陽性対照）"),
    ("結果が割れるを変わると読まない", '**{w: "変わる" for w in EFFECTIVE}}', '"判断が要る": "変わる"}', "内部: 結果が割れるも変わる側として割れを名指しする"),
    ("確かめる行が無いとき割れを出さない", '[f"満たす: {seen}——確かめる行が無い"] + split', '[f"満たす: {seen}——確かめる行が無い"]', "内部: 確かめる行が無くても割れを名指しする"),
    ("最初と最後だけを比べる", "        if len({v for _, v, _ in verdicts}) > 1:\n", "        if verdicts and verdicts[0][1] != verdicts[-1][1]:\n", "内部: 往復した判定も割れと名指しする"),
    ("同じ判定の段も割れと読む", "        if len({v for _, v, _ in verdicts}) > 1:\n", "        if len(verdicts) > 1:\n", "内部: 同じ判定の段は割れと読まない"),
    ("重さでなく振り分けで判定を読む", '        verdicts = [(c["レビュー"], names[c["重さ"]], number) for number, c in rows if c["重さ"] in names]\n',
     '        verdicts = [(c["レビュー"], names[c["重さ"]], number) for number, c in rows if c["重さ"] in names and c["振り分け"] != REJECTED]\n',
     "内部: 割れた行を名指しする（陽性対照）"),
    ("表が無ければ判定しない", "    if not record.exists():\n        return EXIT_OK", "    if False:\n        return EXIT_OK", "上限: 表が無ければ 0 回"),
]


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name}{(': ' + detail) if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    tmp = Path(tempfile.gettempdir()).resolve()
    check(f"試料が一時ディレクトリの中: {path}", tmp in path.resolve().parents)


def run_one(script: Path, work: Path, case: tuple) -> tuple[int, str]:
    command, table, runs, extra = case[:4]
    docs, version = (case[6], case[7]) if len(case) > 6 else (None, 1)
    if work.exists():
        shutil.rmtree(work)
    folder = work / "spec-review"
    folder.mkdir(parents=True)
    assert_in_tmp(folder)
    if table is not None:
        (folder / f"v{version}-findings.csv").write_text(table, encoding="utf-8")
    if runs is not None:
        (folder / f"v{version}.csv").write_text(runs, encoding="utf-8")
    for rel, text in (docs or {}).items():
        path = work / "docs" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        assert_in_tmp(path)
        path.write_text(text, encoding="utf-8")
    findings_path = str(folder / f"v{version}-findings.csv")
    if command == "conditions":
        argv = ["conditions", findings_path]
    elif command == "internal":
        argv = ["internal", findings_path, "--docs", str(work / "docs")]
    elif command == "internal-nodocs":
        argv = ["internal", findings_path]
    elif command == "limit":
        argv = ["limit", str(folder / "v1.csv")]
    else:
        argv = []
    proc = subprocess.run([sys.executable, "-I", str(script), *argv, *extra], capture_output=True, text=True, cwd=work)
    return proc.returncode, proc.stdout + proc.stderr


def as_expected(case: tuple, result: tuple[int, str]) -> bool:
    """終了コードと出力の語を見る。語が `!` で始まれば、その語が出力に無いことを見る（#1248——割れた行を名指ししない試料）。"""
    word = case[5]
    present = word[1:] not in result[1] if word.startswith("!") else word in result[1]
    return result[0] == case[4] and present


def section(markdown: str, heading: str) -> str:
    rest = markdown[markdown.index(heading) + len(heading):]
    m = re.search(r"^#{2,3} ", rest, re.M)
    return rest[: m.start()] if m else rest


def constant(source: str, name: str):
    found = re.search(rf"^{name} = \((.*)\)$", source, flags=re.MULTILINE)
    return re.findall(r'"([^"]+)"', found.group(1)) if found else None


def reference_mismatches(source: str, spec_exit: str) -> list[str]:
    problems = []
    weights = section(spec_exit, "## 指摘の重さ")
    effective = re.findall(r"^\| `([^`]+)` \|[^\n]*\| \*\*効く\*\* \|$", weights, flags=re.MULTILINE)
    if effective != constant(source, "EFFECTIVE"):
        problems.append(f"効く重さ: references {effective} ≠ 本体 {constant(source, 'EFFECTIVE')}")
    limit = section(spec_exit, "### 上限")
    if "`条件2〜4` が `満たさない` か `判定できなかった` の行が 3 つあれば" not in limit or constant(source, "COUNTED") != ["満たさない", "判定できなかった"]:
        problems.append("上限の数える値・N=3 が references と違う")
    if "`判断` が `続ける` か `範囲を決め直す` の最後の行の後" not in limit or constant(source, "RECOUNT") != ["続ける", "範囲を決め直す"]:
        problems.append("数え始めの判断が references と違う")
    if not re.search(r"^LIMIT = 3$", source, flags=re.MULTILINE):
        problems.append("LIMIT が 3 でない")
    problems += mark_mismatches(source, section(spec_exit, "### 指摘の表"), "spec-exit.md の「指摘の表」")
    return problems


def mark_mismatches(source: str, text: str, where: str) -> list[str]:
    """内部の行の印（`（内部の行: <No>）`）が文書に在り、本体の `INTERNAL_MARK` がその形の番号を取り出すか（#1155）。"""
    found = re.search(r"`(（内部の行: <No>）)`", text)
    pattern = re.search(r'^INTERNAL_MARK = re\.compile\(r"(.+?)"\)', source, flags=re.MULTILINE)
    if not found or not pattern:
        return [f"内部の行の印が {where} か本体に無い"]
    m = re.search(pattern.group(1), found.group(1).replace("<No>", "D-S-003"))
    return [] if m and m.group(1) == "D-S-003" else [f"本体の INTERNAL_MARK が {where} の印から番号を取り出せない"]


def step6_problems(skill: str) -> list[str]:
    """spec-review の手順 6 が、数え直しを厳しくする向きにだけ使い、`回答待ち` を `結果が割れる` の行で `満たさない` に直させるか（N2）。"""
    step = skill.split("### 6.", 1)[-1].split("### 7.", 1)[0]
    problems = []
    if "`回答待ち` なら変えない" in step:
        problems.append("「回答待ち なら変えない」が残る——結果が割れる の行が出ても 満たさない にならない")
    if "`回答待ち` で、数えた行に `結果が割れる` があれば `満たさない`" not in step:
        problems.append("回答待ちを 結果が割れる で 満たさない にする文が無い")
    return problems


def main() -> int:
    source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="check-review-record-test-") as tmp:
        root = Path(tmp)
        scripts = root / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        print("試料")
        for i, (name, case) in enumerate(CASES.items()):
            result = run_one(scripts / TARGET, root / f"c{i}", case)
            check(f"試料: {name}", as_expected(case, result), f"期待 {case[4]}・{case[5]!r} / 実際 {result[0]}・{result[1][-400:]!r}")
        print(f"  {len(CASES)} 件 OK")

        print("references との突き合わせ")
        spec_exit = SPEC_EXIT.read_text(encoding="utf-8")
        problems = reference_mismatches(source, spec_exit)
        check("本体の定数が references/spec-exit.md と一致する", not problems, "; ".join(problems))
        broken = re.sub(r"(\| `結果が割れる` \|[^\n]*\| )\*\*効く\*\*( \|)", r"\1効かない\2", spec_exit, count=1)
        check("崩した references で突き合わせが落ちる（陽性対照）", reference_mismatches(source, broken) != [])
        check("印を崩した references で突き合わせが落ちる（陽性対照）",
              reference_mismatches(source, spec_exit.replace("`（内部の行: <No>）`", "`（内部: <No>）`")) != [])
        problems = mark_mismatches(source, DOMAIN_CHECKER.read_text(encoding="utf-8"), "agents/domain-checker.md")
        check("domain-checker.md の印が本体の印と同じ形", not problems, "; ".join(problems))
        print("  OK")

        print("spec-review の手順 6（狭いパスの N2）")
        problems = step6_problems(SPEC_REVIEW.read_text(encoding="utf-8"))
        check("手順 6 が、回答待ちの行で数え直しに 結果が割れる があれば 満たさない にさせる", not problems, "; ".join(problems))
        print("  OK")

        print("変異テスト")
        for name, before, after, killer in MUTATIONS:
            check(f"壊す箇所がちょうど 1 回: {name}", source.count(before) == 1, f"{source.count(before)} 回: {before!r}")
            mutated = root / "mutated"
            if mutated.exists():
                shutil.rmtree(mutated)
            shutil.copytree(scripts, mutated)
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            case = CASES[killer]
            original = run_one(scripts / TARGET, root / "orig", case)
            result = run_one(mutated / TARGET, root / "mut", case)
            check(f"変異の前は期待どおり: {name}", as_expected(case, original))
            killed = result[0] != original[0] or (name in OUTPUT_KILLED and not as_expected(case, result))
            check(f"変異を殺す（終了コードが変わる。名指しの変異だけは語の有無）: {name} ← {killer}", killed, f"{result[0]} {result[1][-300:]!r}")
        print(f"  変異 {len(MUTATIONS)} 件 OK")
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
