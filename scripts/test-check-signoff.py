#!/usr/bin/env python3
"""`check-signoff.py`（2 つのサインオフのタグの照合）の回帰テスト。

    python3 scripts/test-check-signoff.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-spec-exit.py` と同じ形。

見るもの:

1. **比べる場所（v1〜v<n> の `shared/` と v2〜v<n> の `removed.csv`）が食い違うタグの組で非ゼロ（1）**——
   中身の違い・追加・削除・**前の版の `shared/` だけ**・**`removed.csv` の `shared/` に効く行だけ**の違い・
   **片側だけ `.` で始まる名前の rename**（読む側に新しいファイルが現れる）。
2. **一致する組を通す**（陽性対照。比べる場所の外だけ違う組も一致——**`removed.csv` の `requirements/`・機能の行
   だけ・理由だけ・行の順序だけが違う組も**。**`.` で始まる名前だけの違いも**——途中の `.` で始まるディレクトリの中も含む）。
3. **「最新」を数で選ぶ**（`-10` > `-9`）・**命名に合わないタグ（旧い `v<n>/req-signoff-<k>`・`req-signoff-v<n>` を含む）を数えない**・
   指定したタグで照合する・**版を省けば作業中の版（番号の最大）**・`--version` で版を選ぶ・
   **素の `v1` タグがあっても（先でも後でも）承認のタグを作れて照合が 0 になる**（#270）。
   **その試料は、承認のタグを #260 の名前（`v1/req-signoff-1`）にするとタグの手順で作れない**（#309。
   試料が素の `v1` との名前の衝突を判別していることの確かめ——git の挙動はここで毎回当てる）。
4. **照合できない形を 0 にしない（2）**——タグが無い・片方だけ・指定したタグが無い／命名に合わない／**別の版のもの**・
   どちらかの時点に比べる場所が無い（**両方に無いときも**——`git diff` は差分なしを返す。**旧い構成のタグも**）・
   **タグの時点に `docs/v<n>/` が無い（前の版の `shared/` はある）**・
   タグがコミットを指さない・git でない・**作業ツリーの版が決まりに反する／1 つも無い（`--version` を渡しても）**・
   `--version` が版の番号でない。
5. **要求確定のタグの時点に暫定の回答（`暫定反映`）が残れば 3**（#325）——一致しなくても見る・予算のタグの時点は見ない・
   前の版の暫定も数える・**後の版で置き換えた／`removed.csv` で消した行は数えない**（その重ね方が `merge-versions.py`
   の `merge` と同じこと——作業ツリーを重ねて突き合わせる）・Q&A 表が決まりに反する／読めないなら 2・
   **`merge` が拒否する `removed.csv` の配置（同じ版で置きつつ消す・前の版までに無い行を消す・同じ行を 2 度消す）も 2**
   （#338。`merge` が実際に拒否することも突き合わせる）・**種類 `ファイル` の行で構造ファイルを消す・同じファイルを
   2 度消す・v1 に `removed.csv` を置くのも 2**（#348）・**拒否のメッセージにパスが 1 度だけ出る**（#351）・
   **要求確定側と予算側の `removed.csv` を入れ替えると、要求確定側だけが拒否する試料で捕まる**（#349。その試料と
   「removed.csv だけ違う」の作業ツリー＝予算側は `merge` が受け付ける）・**3 の案内が「要求確定と予算の合意の両方」を取り直させる**（#336。
   出力は試料と変異で、docstring の終了コード 3 の項は文字列で見る）。
6. **本体の定数が `references/signoff-tags.md` と一致する**（写しのずれ）。
7. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料の git リポジトリはすべて一時ディレクトリに作り、
`HOME` と `GIT_CONFIG_GLOBAL` を差し替えて利用者の git 設定を読まない。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
**試料は 1 度だけ作り、変異は殺すはずの試料だけに当てる**（#350。本体は試料を読むだけなので使い回せ、
判定に使うのはその 1 つの結果だけなので、全試料を回すのと捕捉は同じ）。
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

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-signoff.py"
REFERENCE = PLUGIN / "references" / "signoff-tags.md"

# Q&A 表は決まりどおりに書く——要求確定のタグの時点の表を読んで暫定の行を数えるので（#325）
QA_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
QA_1 = "Q-001,要求確定,割引は？,A: なし / B: 3%,A,理由,A（業務部が回答）,決定表 4 行目,反映済み,\n"
QA_2 = "Q-002,開発,上限は？,A: 拒否 / B: 切り詰める,A,理由,未回答,—,確認中,\n"
QA_A = QA_HEAD + QA_1
QA_B = QA_HEAD + QA_1 + QA_2
# 暫定の回答で反映した行（#325）
P_1 = "Q-001,要求確定,割引は？,A: なし / B: 3%,A,理由,A（推奨案を暫定で採用。業務部 2026-10-21 の指示）,決定表 4 行目,暫定反映,\n"
P_2 = "Q-002,開発,上限は？,A: 拒否 / B: 切り詰める,A,理由,A（推奨案を暫定で採用。業務部 2026-10-21 の指示）,spec/a.md,暫定反映,\n"

# 試料の作り方: 手順の列。("w", パス, 中身) 書く／("rm", パス) 消す／("c",) commit／("t", 名前) 軽量タグ／
# ("ta", 名前) 注釈つきタグ／("tt", 名前) ツリーを指すタグ。None なら git でないディレクトリ
Steps = list[tuple[str, ...]] | None
SHARED = "docs/v1/shared/qa.csv"
SHARED2 = "docs/v2/shared/qa.csv"
REMOVED2 = "docs/v2/removed.csv"
R1, B1 = "signoff/v1/req-1", "signoff/v1/budget-1"
R2, B2 = "signoff/v2/req-1", "signoff/v2/budget-1"

# (名前, 手順, 引数, 期待する終了コード, 出力に含まれるべき文字列)
CASES: list[tuple[str, Steps, list[str], int, str]] = [
    ("一致", [("w", SHARED, QA_A), ("c",), ("t", R1),
              ("w", "docs/v1/feasibility/schedule.csv", "x\n"), ("c",), ("t", B1)],
     [], 0, f"一致する: {R1}"),
    ("同じコミットの 2 つのタグ", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     [], 0, "一致する"),
    ("中身が違う", [("w", SHARED, QA_A), ("c",), ("t", R1),
                  ("w", SHARED, QA_B), ("c",), ("t", B1)],
     [], 1, "M\tdocs/v1/shared/qa.csv"),
    ("ファイルの追加", [("w", SHARED, QA_A), ("c",), ("t", R1),
                    ("w", "docs/v1/shared/nfr.csv", "a\n"), ("c",), ("t", B1)],
     [], 1, "A\tdocs/v1/shared/nfr.csv"),
    ("ファイルの削除", [("w", SHARED, QA_A), ("w", "docs/v1/shared/nfr.csv", "a\n"), ("c",), ("t", R1),
                    ("rm", "docs/v1/shared/nfr.csv"), ("c",), ("t", B1)],
     [], 1, "D\tdocs/v1/shared/nfr.csv"),
    # 文字列順なら -9 が最新になり、-9 の中身（QA_A）と budget（QA_B）が食い違う
    ("最新を数で選ぶ", [("w", SHARED, QA_A), ("c",), ("t", "signoff/v1/req-9"),
                     ("w", SHARED, QA_B), ("c",), ("t", "signoff/v1/req-10"), ("t", B1)],
     [], 0, "一致する: signoff/v1/req-10"),
    # 古い budget-1 は一致するが、最新の -2 は食い違う
    ("新しい予算のタグが違う", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1),
                         ("w", SHARED, QA_B), ("c",), ("t", "signoff/v1/budget-2")],
     [], 1, "signoff/v1/budget-2"),
    ("命名に合わないタグを数えない", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1),
                               ("w", SHARED, QA_B), ("c",), ("t", "signoff/v1/req-2-fix"), ("t", "signoff/v1/req-02"),
                               ("t", "req-signoff-v2"), ("t", "signoff/v01/req-3"),
                               # #260 の名前と、根の無い名前
                               ("t", "v1/req-signoff-2"), ("t", "v1/req-2")],
     [], 0, f"一致する: {R1}"),
    # #270: 素の `v1` タグとは ref の名前で衝突しない。版を根にした #260 の名前では、どちらの順でも
    # タグの手順で作れない——それを OLD_NAMES で当てる（#309）
    ("素の v1 タグが先にある", [("w", SHARED, QA_A), ("c",), ("t", "v1"), ("t", R1), ("t", B1)],
     [], 0, f"一致する: {R1}"),
    ("素の v1 タグを後から付ける", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1), ("t", "v1")],
     [], 0, f"一致する: {R1}"),
    ("指定したタグで照合", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1),
                       ("w", SHARED, QA_B), ("c",), ("t", "signoff/v1/req-2")],
     ["--req", R1], 0, f"一致する: {R1}"),
    ("注釈つきタグ", [("w", SHARED, QA_A), ("c",), ("ta", R1), ("ta", B1)],
     [], 0, "一致する"),
    ("サブディレクトリから", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     ["--repo", "docs"], 0, "一致する"),
    ("タグが無い", [("w", SHARED, QA_A), ("c",)], [], 2, "signoff/v1/req-<k> のタグが 1 つも無い"),
    ("予算のタグだけ無い", [("w", SHARED, QA_A), ("c",), ("t", R1)], [], 2,
     "signoff/v1/budget-<k> のタグが 1 つも無い"),
    ("指定したタグが無い", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     ["--req", "signoff/v1/req-5"], 2, "タグ signoff/v1/req-5 が無い"),
    ("指定が命名に合わない", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     ["--budget", R1], 2, "命名（signoff/v1/budget-<k>）に合わない"),
    # 作業中の版は v2。v1 のタグを渡しても組にしない
    ("指定が別の版", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R1), ("t", B1), ("t", R2), ("t", B2)],
     ["--req", R1, "--budget", B1], 2, "版 v2 の命名"),
    ("片方の時点に shared が無い", [("w", "README.md", "x\n"), ("c",), ("t", R1),
                               ("w", SHARED, QA_A), ("c",), ("t", B1)],
     [], 2, f"{R1} の時点に docs/v1/shared/ のファイルが 1 つも無い"),
    # 両方に無いと git diff は「差分なし」を返す——それを一致と読まない（作業ツリーには v1 を置く）
    ("両方に shared が無い", [("w", "README.md", "x\n"), ("c",), ("t", R1), ("t", B1), ("w", SHARED, QA_A)],
     [], 2, "ファイルが 1 つも無い"),
    # 版に分ける前の構成でタグを付け、あとで docs/v1/ へ移した——旧いタグの時点には比べる場所が無い
    ("旧い構成の時点のタグ", [("w", "docs/shared/qa.csv", QA_A), ("c",), ("t", R1), ("t", B1),
                         ("rm", "docs/shared/qa.csv"), ("w", SHARED, QA_A), ("c",)],
     [], 2, "ファイルが 1 つも無い"),
    ("タグがツリーを指す", [("w", SHARED, QA_A), ("c",), ("tt", R1), ("t", B1)],
     [], 2, "コミットを指していない"),
    ("git でない", None, [], 2, "作業ツリーでない"),
    # ---- 版
    ("作業中の版", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R1), ("t", B1), ("t", R2), ("t", B2)],
     [], 0, f"一致する: {R2}"),
    ("前の版の shared だけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                             ("w", SHARED, QA_B), ("c",), ("t", B2)],
     [], 1, "M\tdocs/v1/shared/qa.csv"),
    # 予算側は `merge` が受け付ける配置（v1 の Q-001 を v2 で消す。v2 は Q-001 を置かない——#349）
    ("removed.csv だけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_HEAD + QA_2), ("c",), ("t", R2),
                            ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-001,不要\n"), ("c",), ("t", B2)],
     [], 1, "docs/v2/removed.csv（shared/ に効く行が違う）"),
    # `merge` が拒否する配置は要求確定側だけ（予算側は受け付ける）——要求確定側の removed.csv で重ねていれば 2、
    # 予算側で重ねると拒否されず、範囲の違いで 1 になる（#349）
    ("要求確定側だけが拒否する配置", [("w", SHARED, QA_A), ("w", SHARED2, QA_HEAD + QA_2),
                                 ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-003,不要\n"), ("c",), ("t", R2),
                                 ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-001,不要\n"), ("c",), ("t", B2)],
     [], 2, "docs/v2/removed.csv:2: 前の版までに無いものを消そうとしている: Q&A Q-003"),
    ("removed.csv の shared のファイルの行が違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                                         ("w", REMOVED2, "種類,対象,理由\nファイル,shared/nfr.csv,不要\n"), ("c",), ("t", B2)],
     [], 1, "docs/v2/removed.csv（shared/ に効く行が違う）"),
    # requirements/ や機能の削除は共有の範囲の外——removed.csv のファイルが違っても一致のまま
    ("removed.csv の範囲の外の行だけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                                     ("w", REMOVED2, "種類,対象,理由\nファイル,requirements/r.md,不要\n機能,F-001,不要\n"),
                                     ("c",), ("t", B2)],
     [], 0, "v1〜v2 の shared/ と removed.csv は同じ"),
    # 内部の層の Q&A（spec/qa-dev.csv の D-）は共有の範囲の外——表を変えても、removed.csv で消しても一致のまま（#339）
    ("removed.csv の内部の Q&A の行だけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                                         ("w", REMOVED2, "種類,対象,理由\nQ&A,D-001,共有へ移した（Q-003）\n"),
                                         ("c",), ("t", B2)],
     [], 0, "v1〜v2 の shared/ と removed.csv は同じ"),
    ("内部の Q&A 表だけ違う", [("w", SHARED, QA_A), ("w", "docs/v1/spec/qa-dev.csv", QA_HEAD), ("c",), ("t", R1),
                           ("w", "docs/v1/spec/qa-dev.csv", QA_HEAD + "D-001,仕様レビュー,分けるか,A: 分ける / B: 分けない,B,費用,未回答,—,確認中,\n"),
                           ("c",), ("t", B1)],
     [], 0, "一致する"),
    # 理由の列は比べない（消したものが同じなら、見た共有の範囲は同じ）
    # 消す行は前の版に置く——同じ版で置きつつ消す配置は決まりに反する（versions.md。照合は 2）
    ("removed.csv の理由だけ違う", [("w", SHARED, QA_B),
                                 ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-001,不要\n"), ("c",), ("t", R2),
                                 ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-001,重複\n"), ("c",), ("t", B2)],
     [], 0, "一致する"),
    # v1 の shared/ はあるが、タグの時点に v2 はまだ無い——「v1〜v2 が一致」とは言わない
    ("タグの時点に作業中の版が無い", [("w", SHARED, QA_A), ("c",), ("t", R2), ("t", B2),
                                ("w", "docs/v2/spec/s.md", "x\n"), ("c",)],
     [], 2, f"{R2} の時点に docs/v2/ のファイルが 1 つも無い"),
    # 重ね合わせ（merge-versions.py）は `.` で始まる名前を読まない——承認が見た範囲に入らない
    ("shared の . で始まるファイルだけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                                       ("w", "docs/v1/shared/.DS_Store", "x\n"), ("c",), ("t", B2)],
     [], 0, "v1〜v2 の shared/ と removed.csv は同じ"),
    ("タグの時点の作業中の版が . で始まるファイルだけ", [("w", SHARED, QA_A), ("w", "docs/v2/.gitkeep", ""), ("c",),
                                                ("t", R2), ("t", B2), ("w", "docs/v2/spec/s.md", "x\n"), ("c",)],
     [], 2, f"{R2} の時点に docs/v2/ のファイルが 1 つも無い"),
    # 片側だけ `.` で始まる rename は、読む側に新しいファイルが現れる——違いに数える。
    # 期待に R100 を入れるのは、rename として出ていることの確かめ（D と A に分かれると、A だけで 1 になり判別しない）
    ("片側だけ . で始まる名前の rename", [("w", SHARED, QA_A), ("w", "docs/v1/shared/.x", QA_B), ("c",), ("t", R1),
                                     ("rm", "docs/v1/shared/.x"), ("w", "docs/v1/shared/vis.md", QA_B), ("c",), ("t", B1)],
     [], 1, "R100\tdocs/v1/shared/.x\tdocs/v1/shared/vis.md"),
    # 最後の要素だけでなく、途中の `.` で始まるディレクトリの中も重ね合わせは読まない
    ("shared の . で始まるディレクトリの中だけ違う", [("w", SHARED, QA_A), ("c",), ("t", R1),
                                             ("w", "docs/v1/shared/.cache/x", "x\n"), ("c",), ("t", B1)],
     [], 0, f"一致する: {R1}"),
    # 行の順序だけ違う removed.csv は、同じものを消している
    ("removed.csv の行の順序だけ違う", [("w", SHARED, QA_B),
                                    ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-001,不要\nQ&A,Q-002,不要\n"), ("c",), ("t", R2),
                                    ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-002,不要\nQ&A,Q-001,不要\n"), ("c",), ("t", B2)],
     [], 0, "v1〜v2 の shared/ と removed.csv は同じ"),
    # 決まりに反する removed.csv（見出しの順が違う）を、無い removed.csv と同じに読まない
    ("removed.csv が決まりに反する", [("w", SHARED, QA_A), ("w", SHARED2, QA_B),
                                   ("w", REMOVED2, "対象,種類,理由\nQ-001,Q&A,x\n"), ("c",), ("t", R2),
                                   ("rm", REMOVED2), ("c",), ("t", B2)],
     [], 2, "removed.csv が決まりに反する（references/versions.md）: docs/v2/removed.csv:1: 見出し行が決まりと違う"),
    ("範囲の外だけ違う", [("w", SHARED, QA_A), ("w", SHARED2, QA_B), ("c",), ("t", R2),
                       ("w", "docs/v2/requirements/a.md", "x\n"), ("c",), ("t", B2)],
     [], 0, "v1〜v2 の shared/ と removed.csv は同じ"),
    # 作業中の版は v2 だがタグは v1 にしかない。v1 の範囲に v2 は入らない
    ("版を指定", [("w", SHARED, QA_A), ("c",), ("t", R1), ("w", SHARED2, QA_A), ("c",), ("t", B1)],
     ["--version", "1"], 0, f"一致する: {R1}"),
    # 版を渡しても作業ツリーの版の並びは見る（渡したかどうかで判定が変わらない）
    ("版を指定しても作業ツリーの版を見る", [("w", SHARED, QA_A), ("w", "docs/v03/shared/qa.csv", QA_A), ("c",),
                                     ("t", R1), ("t", B1)],
     ["--version", "1"], 2, "版が決まりに反する"),
    ("版を省くと作業中の版のタグを探す", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1), ("w", SHARED2, QA_A), ("c",)],
     [], 2, "signoff/v2/req-<k> のタグが 1 つも無い"),
    ("作業ツリーの版が決まりに反する", [("w", "docs/v02/shared/qa.csv", QA_A), ("c",), ("t", R1), ("t", B1)],
     [], 2, "版が決まりに反する"),
    ("作業ツリーに版が無い", [("w", "README.md", "x\n"), ("c",), ("t", R1), ("t", B1)],
     [], 2, "版（v1 など）が 1 つも無い"),
    ("--version が番号でない", [("w", SHARED, QA_A), ("c",), ("t", R1), ("t", B1)],
     ["--version", "01"], 2, "版の番号"),
    # ---- 暫定の回答（#325）
    ("暫定の行が残る", [("w", SHARED, QA_HEAD + P_1 + QA_2), ("c",), ("t", R1), ("t", B1)],
     [], 3, "暫定の回答（暫定反映）が 1 件残る"),
    # 確かめると shared/qa.csv が変わり、今の予算の合意とも一致しなくなる——要求確定だけを取り直させない（#336）
    ("暫定の行が残ると両方を取り直す", [("w", SHARED, QA_HEAD + P_1 + QA_2), ("c",), ("t", R1), ("t", B1)],
     [], 3, "要求確定と予算の合意の両方のサインオフを取り直す"),
    # 一致しなくても暫定を見る（両方を出す）
    ("暫定の行が残り、一致もしない", [("w", SHARED, QA_HEAD + P_1), ("c",), ("t", R1),
                                ("w", SHARED, QA_HEAD + QA_1), ("c",), ("t", B1)],
     [], 3, "一致しない"),
    # 予算のタグの時点は見ない——暫定を数えるのは要求確定の側（予算の側だけにあれば、範囲の食い違いとして 1）
    ("予算のタグの時点の暫定は見ない", [("w", SHARED, QA_A), ("c",), ("t", R1),
                                 ("w", SHARED, QA_HEAD + P_1), ("c",), ("t", B1)],
     [], 1, "一致しない"),
    ("前の版の暫定が残る", [("w", SHARED, QA_HEAD + P_1), ("w", SHARED2, QA_HEAD + QA_2), ("c",), ("t", R2), ("t", B2)],
     [], 3, "Q-001: A（推奨案を暫定で採用"),
    # 後の版で同じ No を反映済みに置き換えた——重ねた結果には暫定が無い
    ("後の版で反映済みにした暫定は数えない", [("w", SHARED, QA_HEAD + P_1), ("w", SHARED2, QA_HEAD + QA_1), ("c",),
                                       ("t", R2), ("t", B2)],
     [], 0, f"一致する: {R2}"),
    ("removed.csv で消した暫定は数えない", [("w", SHARED, QA_HEAD + QA_1 + P_2),
                                     ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-002,不要\n"), ("c",), ("t", R2), ("t", B2)],
     [], 0, f"一致する: {R2}"),
    # 同じ版で置きつつ消す配置は `merge` が拒否する——黙って消すと、置いた暫定の行を数え落として 0 になる
    ("同じ版で置いて消した暫定", [("w", SHARED, QA_HEAD + QA_1), ("w", SHARED2, QA_HEAD + P_2),
                                ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-002,不要\n"), ("c",), ("t", R2), ("t", B2)],
     [], 2, "docs/v2/removed.csv:2: 同じ版で置きつつ消している: Q-002"),
    # `merge` が拒否する兄弟の配置（#338）——黙って通すと、`merge` が拒否する中身を 0 か 3 で照合したことになる。
    # 直す前は、前者は暫定の Q-001 を数えて 3、後者は 2 度消して 0 だった
    ("前の版までに無い行を消す", [("w", SHARED, QA_HEAD + P_1), ("w", SHARED2, QA_HEAD + QA_2),
                               ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-003,不要\n"), ("c",), ("t", R2), ("t", B2)],
     [], 2, "docs/v2/removed.csv:2: 前の版までに無いものを消そうとしている: Q&A Q-003"),
    ("同じ行を 2 度消す", [("w", SHARED, QA_HEAD + QA_1 + P_2),
                         ("w", REMOVED2, "種類,対象,理由\nQ&A,Q-002,不要\nQ&A,Q-002,重複\n"), ("c",), ("t", R2), ("t", B2)],
     [], 2, "docs/v2/removed.csv:3: 2 行目と同じ対象を 2 度消す: Q-002"),
    # 内部の層の Q&A（`D-`）を消す行は重ねに渡さない——共有の表だけを重ねるので、渡すと「前の版までに無い」で 2 になる
    # （#339 と #340 を重ねて生じた形。`merge` は内部の表も見て受け入れる）
    ("内部の Q&A を消しても暫定を数える", [("w", SHARED, QA_HEAD + P_1),
                                    ("w", "docs/v1/spec/qa-dev.csv",
                                     QA_HEAD + "D-001,仕様レビュー,分けるか,A: 分ける / B: 分けない,B,費用,未回答,—,確認中,\n"),
                                    ("w", SHARED2, QA_HEAD + QA_2),
                                    ("w", REMOVED2, "種類,対象,理由\nQ&A,D-001,共有へ移した（Q-002）\n"),
                                    ("c",), ("t", R2), ("t", B2)],
     [], 3, "Q-001: A（推奨案を暫定で採用"),
    # 種類 `ファイル` の行のうち、版のファイルの一覧を作らずに判定できる形と、v1 の removed.csv（#348）。
    # 直す前は、どれも暫定の Q-001 を数えて 3 だった
    ("構造ファイルをファイルとして消す", [("w", SHARED, QA_HEAD + P_1), ("w", SHARED2, QA_HEAD + QA_2),
                                   ("w", REMOVED2, "種類,対象,理由\nファイル,shared/qa.csv,不要\n"),
                                   ("c",), ("t", R2), ("t", B2)],
     [], 2, "docs/v2/removed.csv:2: shared/qa.csv はファイルとしては消せない"),
    ("同じファイルを 2 度消す", [("w", SHARED, QA_HEAD + P_1), ("w", "docs/v1/shared/nfr.csv", "a\n"),
                             ("w", SHARED2, QA_HEAD + QA_2),
                             ("w", REMOVED2, "種類,対象,理由\nファイル,shared/nfr.csv,不要\nファイル,shared/nfr.csv,重複\n"),
                             ("c",), ("t", R2), ("t", B2)],
     [], 2, "docs/v2/removed.csv:3: 2 行目と同じ対象を 2 度消す: shared/nfr.csv"),
    ("v1 に removed.csv を置く", [("w", SHARED, QA_HEAD + P_1), ("w", "docs/v1/removed.csv", "種類,対象,理由\n"),
                                ("c",), ("t", R1), ("t", B1)],
     [], 2, "docs/v1/removed.csv: v1 には置かない（消すものが無い）"),
    # v1 の removed.csv は後の版のタグの時点でも拒否する——`merge` はどの版まで重ねても v1 を見る
    ("v2 のタグの時点に v1 の removed.csv がある", [("w", SHARED, QA_HEAD + P_1), ("w", "docs/v1/removed.csv", "種類,対象,理由\n"),
                                              ("w", SHARED2, QA_HEAD + QA_2), ("c",), ("t", R2), ("t", B2)],
     [], 2, "docs/v1/removed.csv: v1 には置かない（消すものが無い）"),
    # 陽性対照: 要求確定の時点の正しい種類 `ファイル` の行（前の版に在るファイルを 1 度だけ消す）は拒否しない——
    # 暫定の Q-001 を数えて 3。ファイルの行を在るとしない・置いたとする変異はここで 2 になる
    ("要求確定の時点に正しいファイルの行がある", [("w", SHARED, QA_HEAD + P_1), ("w", "docs/v1/shared/nfr.csv", "a\n"),
                                           ("w", "docs/v1/requirements/r.md", "a\n"), ("w", SHARED2, QA_HEAD + QA_2),
                                           ("w", REMOVED2, "種類,対象,理由\nファイル,shared/nfr.csv,不要\n"
                                                           "ファイル,requirements/r.md,不要\n"),
                                           ("c",), ("t", R2), ("t", B2)],
     [], 3, "Q-001: A（推奨案を暫定で採用"),
    ("要求確定の時点の Q&A 表が決まりに反する", [("w", SHARED, "No,起票元\nQ-001,要求確定\n"), ("c",), ("t", R1), ("t", B1)],
     [], 2, "docs/v1/shared/qa.csv が決まりに反する（references/qa-csv.md）"),
    ("要求確定の時点の Q&A 表が空", [("w", SHARED, ""), ("c",), ("t", R1), ("t", B1)],
     [], 2, "docs/v1/shared/qa.csv を読めない"),
]

# 暫定の行の重ね方は `references/versions.md` の「重ねるもの」の写し——本体は Q&A の行だけを自前で重ねる。
# 作業ツリー（タグの時点と同じ中身）を `merge-versions.py` の `merge` で重ねた結果と、暫定の行が一致すること
OVERLAY_CASES = ["前の版の暫定が残る", "後の版で反映済みにした暫定は数えない", "removed.csv で消した暫定は数えない",
                 "内部の Q&A を消しても暫定を数える"]

# 照合が 2 にする `removed.csv` の配置は、`merge` も拒否する——試料が `merge` の拒否を表していることの確かめ
# （期待の文字列のうち、`removed.csv` の位置より後ろが `merge` の問題の行にも現れること）
REFUSED_CASES = ["同じ版で置いて消した暫定", "前の版までに無い行を消す", "同じ行を 2 度消す",
                 "構造ファイルをファイルとして消す", "同じファイルを 2 度消す", "v1 に removed.csv を置く",
                 "v2 のタグの時点に v1 の removed.csv がある"]

# 作業ツリー（予算側と同じ中身）を `merge` が受け付ける——変異の捕捉が、拒否される配置に寄りかからない（#349）
ACCEPTED_CASES = ["removed.csv だけ違う", "要求確定側だけが拒否する配置", "要求確定の時点に正しいファイルの行がある"]

# `removed.csv` の拒否のメッセージに、そのパスがちょうど 1 度出る（#351）。as_expected で見る
ONCE = {name: path for path, names in (
    ("docs/v2/removed.csv", ["removed.csv が決まりに反する", "同じ版で置いて消した暫定", "前の版までに無い行を消す",
                             "同じ行を 2 度消す", "構造ファイルをファイルとして消す", "同じファイルを 2 度消す",
                             "要求確定側だけが拒否する配置"]),
    ("docs/v1/removed.csv", ["v1 に removed.csv を置く", "v2 のタグの時点に v1 の removed.csv がある"])) for name in names}

# 直す前の `provisional_rows` は `removed.csv` の行を `pop(target, None)` で黙って消していた（#338）
CHECK_REMOVED = (
    "            versions.check_removed(path, sorted(rows + files),\n"
    "                                   {REMOVED_QA: placed, REMOVED_FILE: set()},\n"
    "                                   {REMOVED_QA: set(whole), REMOVED_FILE: {target for _, _, target in files}}, problems)\n"
    "            if problems:\n"
    "                raise Unjudged(refused(tag, problems))\n"
    "            for _, _, target in rows:\n"
    "                whole.pop(target)\n")
UNCHECKED_REMOVED = (
    "            for _, _, target in rows:\n"
    "                whole.pop(target, None)\n")

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("最新を文字列で選ぶ", "numbered = [(int(m.group(1)), name)", "numbered = [(m.group(1), name)", "最新を数で選ぶ"),
    ("命名を前方一致で見る", "if (m := pattern.fullmatch(name))", "if (m := pattern.match(name))",
     "命名に合わないタグを数えない"),
    ("先頭の 0 を許す", 'NUMBER = r"([1-9][0-9]*)"', 'NUMBER = r"([0-9]+)"', "命名に合わないタグを数えない"),
    ("最古を選ぶ", "return max(numbered)[1]", "return min(numbered)[1]", "新しい予算のタグが違う"),
    ("shared が空でも照合する", "    if not files:\n        raise Unjudged", "    if False:\n        raise Unjudged",
     "両方に shared が無い"),
    ("根で走らせない", "        repo = Path(top.stdout.strip())\n", "", "サブディレクトリから"),
    ("差分を見ない", "    if changed:", "    if False:", "中身が違う"),
    ("比べる場所を絞らない", 'info["budget_commit"], "--", *shared_scope(version))', 'info["budget_commit"])', "一致"),
    ("前の版を範囲に含めない", "for i in range(1, version + 1)]", "for i in range(version, version + 1)]",
     "前の版の shared だけ違う"),
    ("removed.csv を比べない", "if removed_shared_rows(at_req) != removed_shared_rows(at_budget):", "if False:",
     "removed.csv だけ違う"),
    ("removed.csv の行を絞らない",
     "if ((kind == REMOVED_QA and not qa.INTERNAL_NUMBER.fullmatch(target))\n                or (kind == REMOVED_FILE and target.startswith(SHARED))):",
     "if True:", "removed.csv の範囲の外の行だけ違う"),
    ("内部の Q&A を消した行も比べる", "(kind == REMOVED_QA and not qa.INTERNAL_NUMBER.fullmatch(target))", "kind == REMOVED_QA",
     "removed.csv の内部の Q&A の行だけ違う"),
    ("removed.csv の shared のファイルの行を見ない", "and target.startswith(SHARED))):", "and False)):",
     "removed.csv の shared のファイルの行が違う"),
    ("removed.csv の決まりを見ない", "    if problems:\n        raise Unjudged(refused(tag, problems))\n    return parsed",
     "    if False:\n        raise Unjudged(refused(tag, problems))\n    return parsed", "removed.csv が決まりに反する"),
    # #351 の前の形（前置きにもパスを書く）に戻す
    ("拒否の前置きにパスを書く", 'return (f"{tag} の時点の {REMOVED} が決まりに反する',
     'return (f"{tag} の docs/v2/removed.csv が決まりに反する', "同じ行を 2 度消す"),
    ("拒否の前置きにパスを書く（v1）", 'raise Unjudged(refused(tag, [f"{path}: {versions.V1_REMOVED}"]))',
     'raise Unjudged(f"{tag} の {path} が決まりに反する: " + f"{path}: {versions.V1_REMOVED}")',
     "v1 に removed.csv を置く"),
    ("`.` で始まるファイルで版があると言う", "if line and not hidden(line)]", "if line]",
     "タグの時点の作業中の版が . で始まるファイルだけ"),
    ("`.` で始まるファイルの違いも数える",
     'if line and not all(hidden(path) for path in line.split("\\t")[1:])]', "if line]",
     "shared の . で始まるファイルだけ違う"),
    ("片側だけ `.` で始まる rename を数えない",
     'if line and not all(hidden(path) for path in line.split("\\t")[1:])]',
     'if line and not any(hidden(path) for path in line.split("\\t")[1:])]', "片側だけ . で始まる名前の rename"),
    ("`.` で始まるかを最後の要素だけで見る", 'return any(part.startswith(".") for part in path.split("/"))',
     'return path.split("/")[-1].startswith(".")', "shared の . で始まるディレクトリの中だけ違う"),
    ("removed.csv の行を並べ替えない", "    return sorted(rows)", "    return rows", "removed.csv の行の順序だけ違う"),
    ("タグの時点に版 n があるかを見ない",
     'shared_files(repo, info[f"{key}_commit"], chosen[key], [f"{DOCS}/v{version}/"])', "pass",
     "タグの時点に作業中の版が無い"),
    ("版を渡すと作業ツリーの版を見ない",
     "        working = working_version(repo)\n        if version is None:\n            version = working\n",
     "        if version is None:\n            version = working_version(repo)\n",
     "版を指定しても作業ツリーの版を見る"),
    ("指定の命名を見ない", "if not tag_pattern(prefix, version).fullmatch(given):", "if False:", "指定が命名に合わない"),
    ("タグの版を見ない", 'rf"{re.escape(TAG_ROOT)}/v{version}/', 'rf"{re.escape(TAG_ROOT)}/v[0-9]+/',
     "指定が別の版"),
    ("タグの根を見ない", 'rf"{re.escape(TAG_ROOT)}/v{version}/', 'rf"(?:{re.escape(TAG_ROOT)}/)?v{version}/',
     "命名に合わないタグを数えない"),
    # 殺すのは試料の `v1/req-signoff-2` だけ（#309。その 1 つを消すと生き残ることを手で当てた）
    ("#260 の名前も数える", 'rf"{re.escape(TAG_ROOT)}/v{version}/{re.escape(prefix)}-{NUMBER}"',
     'rf"(?:{re.escape(TAG_ROOT)}/v{version}/{re.escape(prefix)}|v{version}/{re.escape(prefix)}-{re.escape(TAG_ROOT)})-{NUMBER}"',
     "命名に合わないタグを数えない"),
    ("作業中の版を最小にする", "return found[-1][0]", "return found[0][0]", "作業中の版"),
    ("--version を渡さない", "resolve(args.repo, args.req, args.budget, args.version)",
     "resolve(args.repo, args.req, args.budget)", "版を指定"),
    ("作業ツリーの版の誤りを見ない", '    if problems:\n        raise Unjudged("作業ツリーの版が',
     '    if False:\n        raise Unjudged("作業ツリーの版が', "作業ツリーの版が決まりに反する"),
    ("作業ツリーに版が無いのを見ない", "    if not found:\n", "    if False:\n", "作業ツリーに版が無い"),
    ("コミットに剥がさない", 'f"refs/tags/{tag}^{{commit}}"', 'f"refs/tags/{tag}"', "タグがツリーを指す"),
    ("git でないのを見ない", "if top.returncode != 0 or not top.stdout.strip():", "if False:", "git でない"),
    ("タグ無しを見ない", "if found is None:", "if False:", "タグが無い"),
    ("暫定の行を見ない", '    return [row for row in whole.values() if row["状態"].strip() == qa.PROVISIONAL]',
     "    return []", "暫定の行が残る"),
    ("一致しないとき暫定を見ない", "        return (3, pending + lines, info) if pending else (1, lines, info)",
     "        return 1, lines, info", "暫定の行が残り、一致もしない"),
    ("前の版を重ねない", "    for number in range(1, version + 1):", "    for number in range(version, version + 1):",
     "前の版の暫定が残る"),
    ("後の版で置き換えない", '                whole[row["No"]] = row', '                whole.setdefault(row["No"], row)',
     "後の版で反映済みにした暫定は数えない"),
    ("removed.csv で消さない", "                whole.pop(target)", "                pass",
     "removed.csv で消した暫定は数えない"),
    ("同じ版で置いて消すのを見ない", "{REMOVED_QA: placed,", "{REMOVED_QA: set(),", "同じ版で置いて消した暫定"),
    ("内部の Q&A を消した行も重ねる", "row[1] == REMOVED_QA and not qa.INTERNAL_NUMBER.fullmatch(row[2])",
     "row[1] == REMOVED_QA", "内部の Q&A を消しても暫定を数える"),
    # 拒否の条件式は `merge-versions.py` にしか無い——本体で壊せるのは、それを呼ぶかどうか（#338）。
    # 直す前の挙動（黙って `pop(target, None)`）に戻す——拒否だけ外すと `pop` の KeyError で落ち、
    # 旧い挙動（3 と 0）を表さないまま殺したことになる（#340 の 1 パス目 R3）
    ("merge が拒否する配置を見ない（無い行）", CHECK_REMOVED, UNCHECKED_REMOVED, "前の版までに無い行を消す"),
    ("merge が拒否する配置を見ない（2 度）", CHECK_REMOVED, UNCHECKED_REMOVED, "同じ行を 2 度消す"),
    # 要求確定側の removed.csv で重ねる——予算側と入れ替えると、要求確定側だけの拒否を見落とす（#349。
    # 殺すのは予算側が受け付ける配置の試料。拒否される配置に寄りかからない）
    ("予算側の removed.csv で重ねる", "{path: at_req for path, (at_req, _) in removed.items()}",
     "{path: at_budget for path, (_, at_budget) in removed.items()}", "要求確定側だけが拒否する配置"),
    # #348 の前の形（種類 `ファイル` の行を渡さない・v1 を見ない）に戻す
    ("ファイルの行を見ない（構造ファイル）", "files = [row for row in removed[path] or [] if row[1] == REMOVED_FILE]",
     "files = []", "構造ファイルをファイルとして消す"),
    ("ファイルの行を見ない（2 度）", "files = [row for row in removed[path] or [] if row[1] == REMOVED_FILE]",
     "files = []", "同じファイルを 2 度消す"),
    ("v1 の removed.csv を見ない", "            if listed.stdout.strip():\n                raise Unjudged(refused(",
     "            if False:\n                raise Unjudged(refused(", "v1 に removed.csv を置く"),
    ("v1 の removed.csv を v1 のタグだけで見る", "            if listed.stdout.strip():\n                raise Unjudged(refused(",
     "            if listed.stdout.strip() and version == 1:\n                raise Unjudged(refused(",
     "v2 のタグの時点に v1 の removed.csv がある"),
    # 判定できない 2 形を判定しようとして、正しいファイルの行まで拒否する
    ("ファイルの行を前の版までに無いとする", "REMOVED_FILE: {target for _, _, target in files}}",
     "REMOVED_FILE: set()}", "要求確定の時点に正しいファイルの行がある"),
    ("ファイルの行を同じ版で置いたとする", "{REMOVED_QA: placed, REMOVED_FILE: set()}",
     "{REMOVED_QA: placed, REMOVED_FILE: {target for _, _, target in files}}", "要求確定の時点に正しいファイルの行がある"),
    ("予算の時点の暫定を見る",'provisional_rows(repo, info["req_commit"], info["req"], version,',
     'provisional_rows(repo, info["budget_commit"], info["budget"], version,', "予算のタグの時点の暫定は見ない"),
    # 確かめると予算の合意とも一致しなくなる——案内を要求確定だけに戻させない（#336）
    ("取り直すのを要求確定だけにする", "要求確定と予算の合意の両方のサインオフを取り直す——",
     "要求確定のサインオフを取り直す——", "暫定の行が残ると両方を取り直す"),
    ("Q&A 表の決まりを見ない", '            if problems:\n                raise Unjudged(f"{tag} の {path} が決まりに反する（references/qa-csv.md）',
     '            if False:\n                raise Unjudged(f"{tag} の {path} が決まりに反する（references/qa-csv.md）',
     "要求確定の時点の Q&A 表が決まりに反する"),
    ("読めない Q&A 表を 2 にしない", "                except versions.Unreadable as e:\n                    raise Unjudged",
     "                except versions.Unreadable as e:\n                    rows = []\n                    if False: raise Unjudged",
     "要求確定の時点の Q&A 表が空"),
    # `git diff` 自体が失敗する分岐（`if diff.returncode != 0`）は、手前の検査（コミットを指すか・
    # shared を読めるか）を通った後には作れなかったので、変異を置いていない（殺せると主張しない）
]

# #260 の名前（版を根にした名前）。素の `v1` と共存する試料を、承認のタグだけこの名前にして作ると、
# タグの手順で作れない（`refs/tags/v1` と `refs/tags/v1/...` は共存できない）——試料が衝突を判別している確かめ
OLD_NAMES = {R1: "v1/req-signoff-1", B1: "v1/budget-signoff-1"}
COEXIST = ["素の v1 タグが先にある", "素の v1 タグを後から付ける"]

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


def build_repo(root: Path, steps: Steps, env: dict[str, str]) -> None:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    (root / "docs").mkdir()
    if steps is None:
        return
    run_git(root, env, "init", "-q", "-b", "main")
    for step in steps:
        kind = step[0]
        if kind == "w":
            path = root / step[1]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(step[2], encoding="utf-8")
            run_git(root, env, "add", "-A")
        elif kind == "rm":
            run_git(root, env, "rm", "-q", step[1])
        elif kind == "c":
            run_git(root, env, "commit", "-q", "--allow-empty", "-m", "step")
        elif kind == "t":
            run_git(root, env, "tag", step[1])
        elif kind == "ta":
            run_git(root, env, "tag", "-a", "-m", "signoff", step[1])
        elif kind == "tt":
            run_git(root, env, "tag", step[1], "HEAD^{tree}")


def build_all(work: Path, env: dict[str, str]) -> dict[str, str]:
    """試料を 1 度だけ作る（#350）。作れなかった試料の名前と理由を返す。

    本体は試料を読むだけ（`git ls-tree`・`git show`・`git diff <コミット> <コミット>`）なので、
    元の本体と全部の変異で同じ試料を使い回せる。
    """
    broken = {}
    for index, (name, steps, _, _, _) in enumerate(CASES):
        try:
            build_repo(work / f"case{index}", steps, env)
        except subprocess.CalledProcessError as e:  # 1 つの試料が作れなくても、実行全体は落とさない
            broken[name] = f"試料を作れなかった: {' '.join(e.cmd[-2:])}: {e.stderr.decode(errors='replace')}"
    return broken


def run_case(scripts: Path, work: Path, env: dict[str, str], broken: dict[str, str], name: str) -> tuple[int | None, str]:
    """作ってある試料に本体（`scripts` の中の）を当てる。"""
    if name in broken:
        return None, broken[name]
    index = [case[0] for case in CASES].index(name)
    root = work / f"case{index}"
    args = CASES[index][2]
    args = [str(root / a) if prev == "--repo" else a for prev, a in zip([""] + args, args)]
    if "--repo" not in args:
        args = ["--repo", str(root), *args]
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), *args],
                          capture_output=True, text=True, cwd=work, env=env)
    return proc.returncode, proc.stdout + proc.stderr


def with_old_names(steps: Steps) -> Steps:
    return [(s[0], OLD_NAMES.get(s[1], s[1]), *s[2:]) if s[0] == "t" else s for s in steps]


# 衝突の片側が素の v1 そのものであるときだけ数える——v1/x と v1/x/y の衝突も同じ形で落ちる（#309）
V1_COLLISION = re.compile(r"'refs/tags/v1' exists|cannot (?:lock ref|create) 'refs/tags/v1'")


def old_names_collide(root: Path, steps: Steps, env: dict[str, str]) -> str:
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


def overlay_mismatch(root: Path, result: tuple[int | None, str]) -> str:
    """作業ツリーを `merge-versions.py` の `merge` で重ねた暫定の行と、本体が出した暫定の行を比べる。"""
    spec = importlib.util.spec_from_file_location("merge_versions", SCRIPTS / "merge-versions.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    problems, _, whole, _ = module.merge(root / "docs")
    if problems:
        return f"merge が決まりに反すると言う（試料の誤り）: {problems}"
    # 陽性対照: 重ねる前（版ごと）には暫定の行が在る——無ければ、比べても重ね方を判別しない
    raw = sum(path.read_text(encoding="utf-8").count(",暫定反映,") for path in (root / "docs").glob("v*/shared/qa.csv"))
    if not raw:
        return "試料に暫定の行が無い（重ね方を判別しない）"
    expected = sorted(no for no, row in whole.qa.items() if row["状態"] == module.qa.PROVISIONAL)
    observed = sorted(re.findall(r"^    (Q-[0-9]+): ", result[1], flags=re.MULTILINE))
    return "" if expected == observed else f"merge: {expected} ≠ 本体: {observed}"


def merge_not_refusing(root: Path, name: str) -> str:
    """作業ツリーを `merge` で重ね、試料の期待と同じ理由で拒否するか。拒否すれば空文字列。"""
    problems = merge_refusing(root)
    reason = next(case for case in CASES if case[0] == name)[4].split("removed.csv")[-1]
    return "" if any(reason in line for line in problems) else f"merge が {reason!r} で拒否しない: {problems}"


def merge_refusing(root: Path) -> list[str]:
    """作業ツリーを `merge` で重ねたときの問題（受け付けるなら空）。"""
    spec = importlib.util.spec_from_file_location("merge_versions", SCRIPTS / "merge-versions.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.merge(root / "docs")[0]


def as_expected(name: str, result: tuple[int | None, str]) -> bool:
    expected = next(case for case in CASES if case[0] == name)
    once = name not in ONCE or result[1].count(ONCE[name]) == 1
    return result[0] == expected[3] and expected[4] in result[1] and once


NUMBER_WORDS = {"1 から始まる整数": r"([1-9][0-9]*)"}


def constant(source: str, name: str) -> str | None:
    found = re.search(rf'^{name} = r?"([^"]+)"$', source, flags=re.MULTILINE)
    return found.group(1) if found else None


def reference_mismatches(source: str, markdown: str) -> list[str]:
    problems = []
    rows = re.findall(r"^\| [^|]+ \| `([a-z-]+)/v<n>/([a-z-]+)-<k>` \|", markdown, flags=re.MULTILINE)
    roots = sorted({root for root, _ in rows})
    if roots != [constant(source, "TAG_ROOT")]:
        problems.append(f"タグの根 {roots} ≠ 本体 {constant(source, 'TAG_ROOT')!r}")
    prefixes = [prefix for _, prefix in rows]
    actual = [constant(source, k) for k in ("REQ_PREFIX", "BUDGET_PREFIX")]
    if prefixes != actual:
        problems.append(f"タグの種類 {prefixes} ≠ 本体 {actual}")
    word = re.search(r"`<k>` は (.+?)で、", markdown)
    if NUMBER_WORDS.get(word.group(1) if word else "") != constant(source, "NUMBER"):
        problems.append(f"番号の決まり {word and word.group(1)!r} ≠ 本体 {constant(source, 'NUMBER')!r}")
    place = re.search(r"比べる場所は `([^`/]+)/v1/([^`]+)`〜`[^`]+` と `[^`/]+/v2/([^`]+)`〜", markdown)
    expected = (constant(source, "DOCS"), constant(source, "SHARED"), constant(source, "REMOVED"))
    if (place.groups() if place else None) != expected:
        problems.append(f"比べる場所 {place and place.groups()!r} ≠ 本体 {expected!r}")
    return problems


REFERENCE_MUTATIONS: list[tuple[str, str, str]] = [
    ("予算のタグの種類", "| `signoff/v<n>/budget-<k>` |", "| `signoff/v<n>/approval-<k>` |"),
    ("予算のタグの根", "| `signoff/v<n>/budget-<k>` |", "| `approval/v<n>/budget-<k>` |"),
    ("番号の決まり", "`<k>` は 1 から始まる整数で、", "`<k>` は 0 から始まる整数で、"),
    ("比べる場所（shared）", "比べる場所は `docs/v1/shared/`〜", "比べる場所は `docs/v1/common/`〜"),
    ("比べる場所（removed.csv）", "と `docs/v2/removed.csv`〜", "と `docs/v2/deleted.csv`〜"),
]


# 終了コード 3 の案内は、出力（試料が見る）と docstring の両方にある——docstring は試料からは見えない（#340 の R9）
RETAKE_BOTH = "要求確定と予算の合意の両方のサインオフを取り直す"


def docstring_exit3_mismatch(source: str) -> str:
    """docstring の終了コード 3 の項が「両方を取り直す」でなければ、何が違うか。"""
    item = re.search(r"^- 3: (.+?)(?=^- [0-9]: )", source, flags=re.MULTILINE | re.DOTALL)
    if not item:
        return "docstring に終了コード 3 の項が無い"
    return "" if RETAKE_BOTH in item.group(1) else f"終了コード 3 の項に「{RETAKE_BOTH}」が無い"


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    if shutil.which("git") is None:
        print("git が無いので走らせていない（緑ではない）", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="signoff-test-") as tmp:
        tmp_path = Path(tmp)
        home = tmp_path / "home"
        home.mkdir()
        env = sandbox_env(home)
        scripts = copy_scripts(tmp_path / "scripts")
        work = tmp_path / "work"
        broken = build_all(work, env)
        results = {case[0]: run_case(scripts, work, env, broken, case[0]) for case in CASES}
        for name, result in results.items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result[0]} {result[1][-300:]}")
        for name in ACCEPTED_CASES:
            problems = merge_refusing(work / f"case{[c[0] for c in CASES].index(name)}")
            check(f"試料の作業ツリーを merge が拒否する: {name}", not problems, str(problems))
        for name in OVERLAY_CASES:
            problem = overlay_mismatch(tmp_path / "work" / f"case{[c[0] for c in CASES].index(name)}", results[name])
            check(f"暫定の行の重ね方が merge-versions.py と違う: {name}", not problem, problem)
        for name in REFUSED_CASES:
            problem = merge_not_refusing(tmp_path / "work" / f"case{[c[0] for c in CASES].index(name)}", name)
            check(f"照合が 2 にする配置を merge が拒否しない: {name}", not problem, problem)
        for index, name in enumerate(COEXIST):
            steps = next(case[1] for case in CASES if case[0] == name)
            problem = old_names_collide(tmp_path / f"old{index}", steps, env)
            check(f"試料が #260 の名前を判別していない: {name}", not problem, problem)

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        problem = docstring_exit3_mismatch(source)
        check("docstring の終了コード 3 が両方を取り直させない", not problem, problem)
        # 崩すと捕まる: 要求確定だけを取り直す文言（#325 の 1 パス目までの形）に戻す
        reverted = source.replace(f"{RETAKE_BOTH}**", "要求確定のサインオフを取り直す**")
        check("docstring を要求確定だけに戻しても捕まらない",
              reverted != source and bool(docstring_exit3_mismatch(reverted)))
        reference = REFERENCE.read_text(encoding="utf-8")
        problems = reference_mismatches(source, reference)
        check("本体の定数が references/signoff-tags.md と一致しない", not problems, "; ".join(problems))
        for name, before, after in REFERENCE_MUTATIONS:
            if reference.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {reference.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(source, reference.replace(before, after))))

        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            # 殺すはずの試料だけを走らせる——判定に使うのはその 1 つの結果だけなので、捕捉は全試料を回すのと同じ（#350）
            killed = run_case(mutated, work, env, broken, killer)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, killed), killed[1][-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件（うち {len(COEXIST)} 件は #260 の名前でも当てた）・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
