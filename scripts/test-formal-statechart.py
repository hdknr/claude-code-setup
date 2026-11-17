#!/usr/bin/env python3
"""`formal-statechart.py`（保存した TLC のモデルを利用者の言葉の状態遷移図にする。#1177）の回帰テスト。

    python3 scripts/test-formal-statechart.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-formal-rerun.py` と同じく、**本物の TLC は走らせない**（CI に無い）——
**偽の TLC** を呼び方の行に絶対パスで書く。偽の TLC はモデルの `MODULE <名前>` で下の `FIXTURES` を引き、**本物の TLC 2.19（tla2tools v1.7.4）に
`-continue -dump dot,actionlabels <ファイル>` を渡して手元で取った出力と状態グラフをそのまま返す**（出力の `Parsing file …` などの絶対パスの行と時刻の行だけ落とした）。
`-continue` を渡されなければ、本物に渡さずに取った出力（`Two:nocontinue`）を返す。走った場所に `states/` を作る——正本に残さないことを見るため。
**`PATH` には同じ偽の TLC を `tlc` の名前で置く**——呼び方の行が無いときに `PATH` で探さないことを見るため。

見るもの:

1. **図と TLC の状態グラフが食い違わない**（Issue の受入基準 3）——試料ごとに、**状態グラフ（`FIXTURES` の dot）と反例（出力）を本体と別に読み**、
   対応（ビュー）で言葉に替えた状態・遷移・初めの状態・規則を破る状態（印）・最初の反例の経路（番号つきの遷移）を、出した Mermaid と突き合わせる。
2. **ラベルは対応の言葉だけ**（受入基準 1）——変数名・行為の名前・TLA+ の値が図に出ない。対応に無い状態・行為は 1。
3. **不変条件を破るモデルで印と経路**（受入基準 2）——本体の反例・陽性対照（`--controls`）の両方。陽性対照で違反が出なければ 4。
4. 対応の誤り（使えない文字・破る状態と破らない状態のまとめ・`skip` の誤用）は 1、時相の性質の反例は 1、記録・呼び方・TLC の欠けは 4、引数の誤りは 2。
5. **正本に `--out` のほかを書かない**（`states/`・状態グラフ）・**描けなかったら `--out` に触らない**。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、名指しした試料が期待どおりでなくなることを確かめる（壊す箇所が本体にちょうど 1 回現れることも先に見る）。
変異の数は本体の docstring の「守ること」の行の数以上。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "formal-statechart.py"

# 本物の TLC 2.19（tla2tools v1.7.4）で手元で取った出力（2026-11-18）。鍵はモジュールの名前（`:nocontinue` は -continue なし）。
# `ActProp`（行為の性質の違反）・`Ends`（行き止まりで止まり、同じ言葉の終わりの状態が報告されない）は 2 パス目の関門の指摘を、`Mid`（行き止まりと先へ進める状態）は狭いパスの指摘を受けて足した。
# `InitBad`（初めの状態が破る）・`CrashAfter`（反例の後に評価の誤り）・`Dup`（同じ辺を重ねて書く）は 1 パス目の関門の指摘を受けて同じ日に足した。
# `Skew` は本物の `OrderBroken` を書き換えて作った（反例の 2 段目の行為を `Ship` から `Pay` に替え、状態グラフの辺と食い違わせた）。
FIXTURES: dict[str, dict] = {'Order': {'rc': 0,
           'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                     'Semantic processing of module Naturals\n'
                     'Semantic processing of module Order\n'
                     'Computing initial states...\n'
                     'Model checking completed. No error has been found.\n'
                     '  Estimates of the probability that TLC did not check all reachable states\n'
                     '  because two distinct states had the same fingerprint:\n'
                     '  calculated (optimistic):  val = 2.7E-19\n'
                     '6 states generated, 5 distinct states found, 0 states left on queue.\n'
                     'The depth of the complete state graph search is 4.\n'
                     'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 2 and the 95th percentile is 2).\n',
           'dot': 'strict digraph DiskGraph {\n'
                  'nodesep=0.35;\n'
                  'subgraph cluster_graph {\n'
                  'color="white";\n'
                  '-3825569175176308035 [label="/\\\\ status = \\"draft\\"\\n/\\\\ paid = FALSE",style = filled]\n'
                  '-3825569175176308035 -> -4253732934433187626 [label="Submit",color="black",fontcolor="black"];\n'
                  '-4253732934433187626 [label="/\\\\ status = \\"submitted\\"\\n/\\\\ paid = FALSE"];\n'
                  '-3825569175176308035 -> 1865327454971209557 [label="Cancel",color="black",fontcolor="black"];\n'
                  '1865327454971209557 [label="/\\\\ status = \\"cancelled\\"\\n/\\\\ paid = FALSE"];\n'
                  '-4253732934433187626 -> -8823999408617791120 [label="Pay",color="black",fontcolor="black"];\n'
                  '-8823999408617791120 [label="/\\\\ status = \\"submitted\\"\\n/\\\\ paid = TRUE"];\n'
                  '-4253732934433187626 -> 1865327454971209557 [label="Cancel",color="black",fontcolor="black"];\n'
                  '-8823999408617791120 -> -2208559592176759684 [label="Ship",color="black",fontcolor="black"];\n'
                  '-2208559592176759684 [label="/\\\\ status = \\"shipped\\"\\n/\\\\ paid = TRUE"];\n'
                  '{rank = same; -3825569175176308035;}\n'
                  '{rank = same; -4253732934433187626;}\n'
                  '{rank = same; -8823999408617791120;}\n'
                  '}\n'
                  '}',
           'tla': '---- MODULE Order ----\n'
                  'EXTENDS Naturals\n'
                  'VARIABLES status, paid\n'
                  'vars == <<status, paid>>\n'
                  'Init == status = "draft" /\\ paid = FALSE\n'
                  'Submit == status = "draft" /\\ status\' = "submitted" /\\ UNCHANGED paid\n'
                  'Pay == status = "submitted" /\\ ~paid /\\ paid\' = TRUE /\\ UNCHANGED status\n'
                  'Ship == status = "submitted" /\\ paid /\\ status\' = "shipped" /\\ UNCHANGED paid\n'
                  'Cancel == status \\in {"draft", "submitted"} /\\ ~paid /\\ status\' = "cancelled" /\\ UNCHANGED paid\n'
                  'Next == Submit \\/ Pay \\/ Ship \\/ Cancel\n'
                  'Spec == Init /\\ [][Next]_vars\n'
                  'NoShipUnpaid == status = "shipped" => paid\n'
                  '====\n',
           'cfg': 'SPECIFICATION Spec\nINVARIANT NoShipUnpaid\nCHECK_DEADLOCK FALSE\n'},
 'OrderBroken': {'rc': 0,
                 'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                           'Semantic processing of module Naturals\n'
                           'Semantic processing of module OrderBroken\n'
                           'Computing initial states...\n'
                           'Error: Invariant NoShipUnpaid is violated.\n'
                           'Error: The behavior up to this point is:\n'
                           'State 1: <Initial predicate>\n'
                           '/\\ status = "draft"\n'
                           '/\\ paid = FALSE\n'
                           '\n'
                           'State 2: <Submit line 6, col 11 to line 6, col 69 of module OrderBroken>\n'
                           '/\\ status = "submitted"\n'
                           '/\\ paid = FALSE\n'
                           '\n'
                           'State 3: <Ship line 8, col 9 to line 8, col 69 of module OrderBroken>\n'
                           '/\\ status = "shipped"\n'
                           '/\\ paid = FALSE\n'
                           '\n'
                           'Model checking completed. No error has been found.\n'
                           '  Estimates of the probability that TLC did not check all reachable states\n'
                           '  because two distinct states had the same fingerprint:\n'
                           '  calculated (optimistic):  val = 3.3E-19\n'
                           '7 states generated, 6 distinct states found, 0 states left on queue.\n'
                           'The depth of the complete state graph search is 4.\n'
                           'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 2 and the 95th percentile is 2).\n',
                 'dot': 'strict digraph DiskGraph {\n'
                        'nodesep=0.35;\n'
                        'subgraph cluster_graph {\n'
                        'color="white";\n'
                        '8181626006461855957 [label="/\\\\ status = \\"draft\\"\\n/\\\\ paid = FALSE",style = filled]\n'
                        '8181626006461855957 -> 339239318837375949 [label="Submit",color="black",fontcolor="black"];\n'
                        '339239318837375949 [label="/\\\\ status = \\"submitted\\"\\n/\\\\ paid = FALSE"];\n'
                        '8181626006461855957 -> 1431808373273980104 [label="Cancel",color="black",fontcolor="black"];\n'
                        '1431808373273980104 [label="/\\\\ status = \\"cancelled\\"\\n/\\\\ paid = FALSE"];\n'
                        '339239318837375949 -> -3851923108473148600 [label="Pay",color="black",fontcolor="black"];\n'
                        '-3851923108473148600 [label="/\\\\ status = \\"submitted\\"\\n/\\\\ paid = TRUE"];\n'
                        '339239318837375949 -> 5915724344508359127 [label="Ship",color="black",fontcolor="black"];\n'
                        '5915724344508359127 [label="/\\\\ status = \\"shipped\\"\\n/\\\\ paid = FALSE"];\n'
                        '339239318837375949 -> 1431808373273980104 [label="Cancel",color="black",fontcolor="black"];\n'
                        '-3851923108473148600 -> -7194817092460316334 [label="Ship",color="black",fontcolor="black"];\n'
                        '-7194817092460316334 [label="/\\\\ status = \\"shipped\\"\\n/\\\\ paid = TRUE"];\n'
                        '{rank = same; 8181626006461855957;}\n'
                        '{rank = same; 339239318837375949;}\n'
                        '{rank = same; -3851923108473148600;}\n'
                        '}\n'
                        '}',
                 'tla': '---- MODULE OrderBroken ----\n'
                        'EXTENDS Naturals\n'
                        'VARIABLES status, paid\n'
                        'vars == <<status, paid>>\n'
                        'Init == status = "draft" /\\ paid = FALSE\n'
                        'Submit == status = "draft" /\\ status\' = "submitted" /\\ UNCHANGED paid\n'
                        'Pay == status = "submitted" /\\ ~paid /\\ paid\' = TRUE /\\ UNCHANGED status\n'
                        'Ship == status = "submitted" /\\ status\' = "shipped" /\\ UNCHANGED paid\n'
                        'Cancel == status \\in {"draft", "submitted"} /\\ ~paid /\\ status\' = "cancelled" /\\ UNCHANGED paid\n'
                        'Next == Submit \\/ Pay \\/ Ship \\/ Cancel\n'
                        'Spec == Init /\\ [][Next]_vars\n'
                        'NoShipUnpaid == status = "shipped" => paid\n'
                        '====\n',
                 'cfg': 'SPECIFICATION Spec\nINVARIANT NoShipUnpaid\nCHECK_DEADLOCK FALSE\n'},
 'Two': {'rc': 0,
         'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                   'Semantic processing of module Naturals\n'
                   'Semantic processing of module Two\n'
                   'Computing initial states...\n'
                   'Error: Invariant Small is violated.\n'
                   'Error: The behavior up to this point is:\n'
                   'State 1: <Initial predicate>\n'
                   'x = 0\n'
                   '\n'
                   'State 2: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 1\n'
                   '\n'
                   'State 3: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 2\n'
                   '\n'
                   'Error: Invariant Small is violated.\n'
                   'Error: The behavior up to this point is:\n'
                   'State 1: <Initial predicate>\n'
                   'x = 0\n'
                   '\n'
                   'State 2: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 1\n'
                   '\n'
                   'State 3: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 2\n'
                   '\n'
                   'State 4: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 3\n'
                   '\n'
                   'Error: Invariant Small is violated.\n'
                   'Error: The behavior up to this point is:\n'
                   'State 1: <Initial predicate>\n'
                   'x = 0\n'
                   '\n'
                   'State 2: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 1\n'
                   '\n'
                   'State 3: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 2\n'
                   '\n'
                   'State 4: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 3\n'
                   '\n'
                   'State 5: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                   'x = 4\n'
                   '\n'
                   'Model checking completed. No error has been found.\n'
                   '  Estimates of the probability that TLC did not check all reachable states\n'
                   '  because two distinct states had the same fingerprint:\n'
                   '  calculated (optimistic):  val = 2.7E-19\n'
                   '6 states generated, 5 distinct states found, 0 states left on queue.\n'
                   'The depth of the complete state graph search is 5.\n'
                   'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 1 and the 95th percentile is 1).\n',
         'dot': 'strict digraph DiskGraph {\n'
                'nodesep=0.35;\n'
                'subgraph cluster_graph {\n'
                'color="white";\n'
                '-1024003171824700855 [label="x = 0",style = filled]\n'
                '-1024003171824700855 -> -214127697328389584 [label="Inc",color="black",fontcolor="black"];\n'
                '-214127697328389584 [label="x = 1"];\n'
                '-214127697328389584 -> -1706723098300869957 [label="Inc",color="black",fontcolor="black"];\n'
                '-1706723098300869957 [label="x = 2"];\n'
                '-1706723098300869957 -> -1973208759514029374 [label="Inc",color="black",fontcolor="black"];\n'
                '-1973208759514029374 [label="x = 3"];\n'
                '-1973208759514029374 -> -4395786626616183891 [label="Inc",color="black",fontcolor="black"];\n'
                '-4395786626616183891 [label="x = 4"];\n'
                '-4395786626616183891 -> -1024003171824700855 [label="Reset",color="black",fontcolor="black"];\n'
                '{rank = same; -1024003171824700855;}\n'
                '{rank = same; -214127697328389584;}\n'
                '{rank = same; -1706723098300869957;}\n'
                '{rank = same; -1973208759514029374;}\n'
                '{rank = same; -4395786626616183891;}\n'
                '}\n'
                '}',
         'tla': '---- MODULE Two ----\n'
                'EXTENDS Naturals\n'
                'VARIABLES x\n'
                'Init == x = 0\n'
                "Inc == x < 4 /\\ x' = x + 1\n"
                "Reset == x = 4 /\\ x' = 0\n"
                'Next == Inc \\/ Reset\n'
                'Spec == Init /\\ [][Next]_x\n'
                'Small == x < 2\n'
                '====\n',
         'cfg': 'SPECIFICATION Spec\nINVARIANT Small\n'},
 'Par': {'rc': 11,
         'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                   'Semantic processing of module Naturals\n'
                   'Semantic processing of module Par\n'
                   'Computing initial states...\n'
                   'Error: Deadlock reached.\n'
                   'Error: The behavior up to this point is:\n'
                   'State 1: <Initial predicate>\n'
                   'done = {}\n'
                   '\n'
                   'State 2: <Write line 6, col 13 to line 6, col 50 of module Par>\n'
                   'done = {a}\n'
                   '\n'
                   'State 3: <Write line 6, col 13 to line 6, col 50 of module Par>\n'
                   'done = {a, b}\n'
                   '\n'
                   '5 states generated, 4 distinct states found, 0 states left on queue.\n'
                   'The depth of the complete state graph search is 3.\n'
                   'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 2 and the 95th percentile is 2).\n',
         'dot': 'strict digraph DiskGraph {\n'
                'nodesep=0.35;\n'
                'subgraph cluster_graph {\n'
                'color="white";\n'
                '-5707877284640651330 [label="done = {}",style = filled]\n'
                '-5707877284640651330 -> -4565032024616907137 [label="Write",color="black",fontcolor="black"];\n'
                '-4565032024616907137 [label="done = {a}"];\n'
                '-5707877284640651330 -> -7045116986138263292 [label="Write",color="black",fontcolor="black"];\n'
                '-7045116986138263292 [label="done = {b}"];\n'
                '-4565032024616907137 -> -7530439614608312686 [label="Write",color="black",fontcolor="black"];\n'
                '-7530439614608312686 [label="done = {a, b}"];\n'
                '-7045116986138263292 -> -7530439614608312686 [label="Write",color="black",fontcolor="black"];\n'
                '{rank = same; -5707877284640651330;}\n'
                '{rank = same; -4565032024616907137;-7045116986138263292;}\n'
                '}\n'
                '}',
         'tla': '---- MODULE Par ----\n'
                'EXTENDS Naturals\n'
                'CONSTANT W\n'
                'VARIABLES done\n'
                'Init == done = {}\n'
                "Write(w) == w \\notin done /\\ done' = done \\cup {w}\n"
                'Next == \\E w \\in W : Write(w)\n'
                'Spec == Init /\\ [][Next]_done\n'
                '====\n',
         'cfg': 'CONSTANT W = {a, b}\nSPECIFICATION Spec\n'},
 'Live': {'rc': 13,
          'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                    'Semantic processing of module Naturals\n'
                    'Semantic processing of module Live\n'
                    'Implied-temporal checking--satisfiability problem has 1 branches.\n'
                    'Computing initial states...\n'
                    'Checking temporal properties for the complete state space with 3 total distinct states at (2026-11-18 06:11:40)\n'
                    'Error: Temporal properties were violated.\n'
                    '\n'
                    'Error: The following behavior constitutes a counter-example:\n'
                    '\n'
                    'State 1: <Initial predicate>\n'
                    'x = 0\n'
                    '\n'
                    'State 2: <Inc line 5, col 8 to line 5, col 26 of module Live>\n'
                    'x = 1\n'
                    '\n'
                    'Back to state 1: <Loop line 6, col 9 to line 6, col 23 of module Live>\n'
                    '\n'
                    'Finished checking temporal properties in 00s at 2026-11-18 06:11:40\n'
                    '4 states generated, 3 distinct states found, 0 states left on queue.\n',
          'dot': 'strict digraph DiskGraph {\n'
                 'nodesep=0.35;\n'
                 'subgraph cluster_graph {\n'
                 'color="white";\n'
                 '5606216787188616689 [label="x = 0",style = filled]\n'
                 '5606216787188616689 -> -4251494465449466658 [label="Inc",color="black",fontcolor="black"];\n'
                 '-4251494465449466658 [label="x = 1"];\n'
                 '5606216787188616689 -> 5606216787188616689 [style="dashed"];\n'
                 '-4251494465449466658 -> 4815952587077643994 [label="Inc",color="black",fontcolor="black"];\n'
                 '4815952587077643994 [label="x = 2"];\n'
                 '-4251494465449466658 -> 5606216787188616689 [label="Loop",color="black",fontcolor="black"];\n'
                 '-4251494465449466658 -> -4251494465449466658 [style="dashed"];\n'
                 '4815952587077643994 -> 4815952587077643994 [style="dashed"];\n'
                 '{rank = same; 5606216787188616689;}\n'
                 '{rank = same; -4251494465449466658;}\n'
                 '{rank = same; 4815952587077643994;}\n'
                 '}\n'
                 '}',
          'tla': '---- MODULE Live ----\n'
                 'EXTENDS Naturals\n'
                 'VARIABLES x\n'
                 'Init == x = 0\n'
                 "Inc == x < 2 /\\ x' = x + 1\n"
                 "Loop == x = 1 /\\ x' = 0\n"
                 'Next == Inc \\/ Loop\n'
                 'Spec == Init /\\ [][Next]_x /\\ WF_x(Next)\n'
                 'Reach == <>(x = 2)\n'
                 '====\n',
          'cfg': 'SPECIFICATION Spec\nPROPERTY Reach\nCHECK_DEADLOCK FALSE\n'},
 'Dead': {'rc': 11,
          'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                    'Semantic processing of module Naturals\n'
                    'Semantic processing of module Dead\n'
                    'Computing initial states...\n'
                    'Error: Deadlock reached.\n'
                    'Error: The behavior up to this point is:\n'
                    'State 1: <Initial predicate>\n'
                    '/\\ r = [s |-> "a"]\n'
                    '/\\ x = 0\n'
                    '\n'
                    'State 2: <Stop line 5, col 9 to line 5, col 46 of module Dead>\n'
                    '/\\ r = [s |-> "stop"]\n'
                    '/\\ x = 1\n'
                    '\n'
                    '3 states generated, 3 distinct states found, 1 states left on queue.\n'
                    'The depth of the complete state graph search is 2.\n'
                    'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 2 and the 95th percentile is 2).\n',
          'dot': 'strict digraph DiskGraph {\n'
                 'nodesep=0.35;\n'
                 'subgraph cluster_graph {\n'
                 'color="white";\n'
                 '-450861040123297973 [label="/\\\\ r = [s |-> \\"a\\"]\\n/\\\\ x = 0",style = filled]\n'
                 '-450861040123297973 -> -6996382385565020697 [label="Stop",color="black",fontcolor="black"];\n'
                 '-6996382385565020697 [label="/\\\\ r = [s |-> \\"stop\\"]\\n/\\\\ x = 1"];\n'
                 '-450861040123297973 -> -3945272772725974090 [label="Go",color="black",fontcolor="black"];\n'
                 '-3945272772725974090 [label="/\\\\ r = [s |-> \\"a\\"]\\n/\\\\ x = 2"];\n'
                 '{rank = same; -450861040123297973;}\n'
                 '}\n'
                 '}',
          'tla': '---- MODULE Dead ----\n'
                 'EXTENDS Naturals\n'
                 'VARIABLES x, r\n'
                 'Init == x = 0 /\\ r = [s |-> "a"]\n'
                 'Stop == x = 0 /\\ x\' = 1 /\\ r\' = [s |-> "stop"]\n'
                 "Go == x = 0 /\\ x' = 2 /\\ UNCHANGED r\n"
                 "Step == x >= 2 /\\ x < 4 /\\ x' = x + 1 /\\ UNCHANGED r\n"
                 "Back == x = 4 /\\ x' = 2 /\\ UNCHANGED r\n"
                 'Next == Stop \\/ Go \\/ Step \\/ Back\n'
                 'Spec == Init /\\ [][Next]_<<x, r>>\n'
                 '====\n',
          'cfg': 'SPECIFICATION Spec\n'},
 'Two:nocontinue': {'rc': 12,
                    'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                              'Semantic processing of module Naturals\n'
                              'Semantic processing of module Two\n'
                              'Computing initial states...\n'
                              'Error: Invariant Small is violated.\n'
                              'Error: The behavior up to this point is:\n'
                              'State 1: <Initial predicate>\n'
                              'x = 0\n'
                              '\n'
                              'State 2: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                              'x = 1\n'
                              '\n'
                              'State 3: <Inc line 5, col 8 to line 5, col 26 of module Two>\n'
                              'x = 2\n'
                              '\n'
                              '3 states generated, 3 distinct states found, 0 states left on queue.\n'
                              'The depth of the complete state graph search is 3.\n'
                              'The average outdegree of the complete state graph is 1 (minimum is 1, the maximum 1 and the 95th percentile is 1).\n',
                    'dot': 'strict digraph DiskGraph {\n'
                           'nodesep=0.35;\n'
                           'subgraph cluster_graph {\n'
                           'color="white";\n'
                           '-1189342407435300990 [label="x = 0",style = filled]\n'
                           '-1189342407435300990 -> -1147412928863307716 [label="Inc",color="black",fontcolor="black"];\n'
                           '-1147412928863307716 [label="x = 1"];\n'
                           '-1147412928863307716 -> -3340393667992641282 [label="Inc",color="black",fontcolor="black"];\n'
                           '-3340393667992641282 [label="x = 2"];\n'
                           '{rank = same; -1189342407435300990;}\n'
                           '{rank = same; -1147412928863307716;}\n'
                           '}\n'
                           '}'},
 'Crash': {'rc': 255,
           'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                     'Semantic processing of module Naturals\n'
                     'Semantic processing of module Crash\n'
                     'Computing initial states...\n'
                     'Error: The second argument of \\div is 0.\n'
                     'Error: The behavior up to this point is:\n'
                     'State 1: <Initial predicate>\n'
                     'x = 0\n'
                     '\n'
                     'State 2: <Inc line 5, col 8 to line 5, col 26 of module Crash>\n'
                     'x = 1\n'
                     '\n'
                     'State 3: <Inc line 5, col 8 to line 5, col 26 of module Crash>\n'
                     'x = 2\n'
                     '\n'
                     'Error: The second argument of \\div is 0.\n'
                     'Error: The behavior up to this point is:\n'
                     'State 1: <Initial predicate>\n'
                     'x = 0\n'
                     '\n'
                     'State 2: <Inc line 5, col 8 to line 5, col 26 of module Crash>\n'
                     'x = 1\n'
                     '\n'
                     'State 3: <Inc line 5, col 8 to line 5, col 26 of module Crash>\n'
                     'x = 2\n'
                     '\n'
                     'Error: The error occurred when TLC was evaluating the nested\n'
                     'expressions at the following positions:\n'
                     '0. Line 6, column 9 to line 6, column 37 in Crash\n'
                     '1. Line 6, column 9 to line 6, column 13 in Crash\n'
                     '2. Line 6, column 18 to line 6, column 37 in Crash\n'
                     '3. Line 6, column 23 to line 6, column 37 in Crash\n'
                     '\n'
                     '\n'
                     '4 states generated, 4 distinct states found, 1 states left on queue.\n',
           'dot': 'strict digraph DiskGraph {\n'
                  'nodesep=0.35;\n'
                  'subgraph cluster_graph {\n'
                  'color="white";\n'
                  '-7685261171725000945 [label="x = 0",style = filled]\n'
                  '-7685261171725000945 -> -515189975988816849 [label="Inc",color="black",fontcolor="black"];\n'
                  '-515189975988816849 [label="x = 1"];\n'
                  '-515189975988816849 -> 5646319963321911631 [label="Inc",color="black",fontcolor="black"];\n'
                  '5646319963321911631 [label="x = 2"];\n'
                  '5646319963321911631 -> 2583404599119274607 [label="Inc",color="black",fontcolor="black"];\n'
                  '2583404599119274607 [label="x = 3"];\n'
                  '5646319963321911631 -> 2583404599119274607 [label="Inc",color="black",fontcolor="black"];\n'
                  '{rank = same; -7685261171725000945;}\n'
                  '{rank = same; -515189975988816849;}\n'
                  '{rank = same; 5646319963321911631;}\n'
                  '}\n'
                  '}',
           'tla': '---- MODULE Crash ----\n'
                  'EXTENDS Naturals\n'
                  'VARIABLES x\n'
                  'Init == x = 0\n'
                  "Inc == x < 3 /\\ x' = x + 1\n"
                  "Boom == x = 2 /\\ x' = 10 \\div (x - 2)\n"
                  'Next == Inc \\/ Boom\n'
                  'Spec == Init /\\ [][Next]_x\n'
                  '====\n',
           'cfg': 'SPECIFICATION Spec\nCHECK_DEADLOCK FALSE\n'},
 'InitBad': {'rc': 0,
             'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                       'Semantic processing of module Naturals\n'
                       'Semantic processing of module InitBad\n'
                       'Computing initial states...\n'
                       'Error: Invariant Small is violated by the initial state:\n'
                       'x = 5\n'
                       '\n'
                       'Error: Invariant Small is violated.\n'
                       'Error: The behavior up to this point is:\n'
                       'State 1: <Initial predicate>\n'
                       'x = 5\n'
                       '\n'
                       'State 2: <Inc line 5, col 8 to line 5, col 26 of module InitBad>\n'
                       'x = 6\n'
                       '\n'
                       'Model checking completed. No error has been found.\n'
                       '  Estimates of the probability that TLC did not check all reachable states\n'
                       '  because two distinct states had the same fingerprint:\n'
                       '  calculated (optimistic):  val = 3.8E-19\n'
                       '8 states generated, 7 distinct states found, 0 states left on queue.\n'
                       'The depth of the complete state graph search is 5.\n'
                       'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 1 and the 95th percentile is 1).\n',
             'dot': 'strict digraph DiskGraph {\n'
                    'nodesep=0.35;\n'
                    'subgraph cluster_graph {\n'
                    'color="white";\n'
                    '6878809131176742310 [label="x = 0",style = filled]\n'
                    '120556001817863923 [label="x = 5",style = filled]\n'
                    '6878809131176742310 -> -3856709652555242122 [label="Inc",color="black",fontcolor="black"];\n'
                    '-3856709652555242122 [label="x = 1"];\n'
                    '120556001817863923 -> 3754412053038006208 [label="Inc",color="black",fontcolor="black"];\n'
                    '3754412053038006208 [label="x = 6"];\n'
                    '-3856709652555242122 -> -14597302870295483 [label="Inc",color="black",fontcolor="black"];\n'
                    '-14597302870295483 [label="x = 2"];\n'
                    '-14597302870295483 -> 7692258802772710549 [label="Inc",color="black",fontcolor="black"];\n'
                    '7692258802772710549 [label="x = 3"];\n'
                    '7692258802772710549 -> -7737172615487680989 [label="Inc",color="black",fontcolor="black"];\n'
                    '-7737172615487680989 [label="x = 4"];\n'
                    '-7737172615487680989 -> 120556001817863923 [label="Inc",color="black",fontcolor="black"];\n'
                    '{rank = same; 120556001817863923;6878809131176742310;}\n'
                    '{rank = same; -3856709652555242122;}\n'
                    '{rank = same; -14597302870295483;}\n'
                    '{rank = same; 7692258802772710549;}\n'
                    '{rank = same; -7737172615487680989;}\n'
                    '}\n'
                    '}',
             'tla': '---- MODULE InitBad ----\n'
                    'EXTENDS Naturals\n'
                    'VARIABLES x\n'
                    'Init == x \\in {0, 5}\n'
                    "Inc == x < 6 /\\ x' = x + 1\n"
                    'Next == Inc\n'
                    'Spec == Init /\\ [][Next]_x\n'
                    'Small == x < 5\n'
                    '====\n',
             'cfg': 'SPECIFICATION Spec\nINVARIANT Small\nCHECK_DEADLOCK FALSE\n'},
 'CrashAfter': {'rc': 75,
                'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                          'Semantic processing of module Naturals\n'
                          'Semantic processing of module CrashAfter\n'
                          'Computing initial states...\n'
                          'Error: Invariant Small is violated.\n'
                          'Error: The behavior up to this point is:\n'
                          'State 1: <Initial predicate>\n'
                          'x = 0\n'
                          '\n'
                          'State 2: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 1\n'
                          '\n'
                          'State 3: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 2\n'
                          '\n'
                          'Error: Invariant Small is violated.\n'
                          'Error: The behavior up to this point is:\n'
                          'State 1: <Initial predicate>\n'
                          'x = 0\n'
                          '\n'
                          'State 2: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 1\n'
                          '\n'
                          'State 3: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 2\n'
                          '\n'
                          'State 4: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 3\n'
                          '\n'
                          'Error: TLC threw an unexpected exception.\n'
                          'This was probably caused by an error in the spec or model.\n'
                          'See the User Output or TLC Console for clues to what happened.\n'
                          ': Attempted to compute the value of an expression of form\n'
                          'CHOOSE x \\in S: P, but no element of S satisfied P.\n'
                          'line 6, col 23 to line 6, col 44 of module CrashAfter\n'
                          'Error: The behavior up to this point is:\n'
                          'State 1: <Initial predicate>\n'
                          'x = 0\n'
                          '\n'
                          'State 2: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 1\n'
                          '\n'
                          'State 3: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 2\n'
                          '\n'
                          'State 4: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 3\n'
                          '\n'
                          'Error: TLC threw an unexpected exception.\n'
                          'This was probably caused by an error in the spec or model.\n'
                          'See the User Output or TLC Console for clues to what happened.\n'
                          ': Attempted to compute the value of an expression of form\n'
                          'CHOOSE x \\in S: P, but no element of S satisfied P.\n'
                          'line 6, col 23 to line 6, col 44 of module CrashAfter\n'
                          'Error: The behavior up to this point is:\n'
                          'State 1: <Initial predicate>\n'
                          'x = 0\n'
                          '\n'
                          'State 2: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 1\n'
                          '\n'
                          'State 3: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 2\n'
                          '\n'
                          'State 4: <Inc line 5, col 8 to line 5, col 26 of module CrashAfter>\n'
                          'x = 3\n'
                          '\n'
                          'Error: The error occurred when TLC was evaluating the nested\n'
                          'expressions at the following positions:\n'
                          '0. Line 6, column 9 to line 6, column 44 in CrashAfter\n'
                          '1. Line 6, column 9 to line 6, column 13 in CrashAfter\n'
                          '2. Line 6, column 18 to line 6, column 44 in CrashAfter\n'
                          '3. Line 6, column 23 to line 6, column 44 in CrashAfter\n'
                          '\n'
                          '\n'
                          '4 states generated, 4 distinct states found, 0 states left on queue.\n',
                'dot': 'strict digraph DiskGraph {\n'
                       'nodesep=0.35;\n'
                       'subgraph cluster_graph {\n'
                       'color="white";\n'
                       '67180241641765912 [label="x = 0",style = filled]\n'
                       '67180241641765912 -> 6296468819102642741 [label="Inc",color="black",fontcolor="black"];\n'
                       '6296468819102642741 [label="x = 1"];\n'
                       '6296468819102642741 -> -5768849194604109758 [label="Inc",color="black",fontcolor="black"];\n'
                       '-5768849194604109758 [label="x = 2"];\n'
                       '-5768849194604109758 -> -540485634259276177 [label="Inc",color="black",fontcolor="black"];\n'
                       '-540485634259276177 [label="x = 3"];\n'
                       '{rank = same; 67180241641765912;}\n'
                       '{rank = same; 6296468819102642741;}\n'
                       '{rank = same; -5768849194604109758;}\n'
                       '}\n'
                       '}',
                'tla': '---- MODULE CrashAfter ----\n'
                       'EXTENDS Naturals\n'
                       'VARIABLES x\n'
                       'Init == x = 0\n'
                       "Inc == x < 3 /\\ x' = x + 1\n"
                       "Boom == x = 3 /\\ x' = CHOOSE n \\in {} : TRUE\n"
                       'Next == Inc \\/ Boom\n'
                       'Spec == Init /\\ [][Next]_x\n'
                       'Small == x < 2\n'
                       '====\n',
                'cfg': 'SPECIFICATION Spec\nINVARIANT Small\nCHECK_DEADLOCK FALSE\n'},
 'Dup': {'rc': 0,
         'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                   'Semantic processing of module Dup\n'
                   'Computing initial states...\n'
                   'Model checking completed. No error has been found.\n'
                   '  Estimates of the probability that TLC did not check all reachable states\n'
                   '  because two distinct states had the same fingerprint:\n'
                   '  calculated (optimistic):  val = 3.3E-19\n'
                   '5 states generated, 2 distinct states found, 0 states left on queue.\n'
                   'The depth of the complete state graph search is 2.\n'
                   'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 1 and the 95th percentile is 1).\n',
         'dot': 'strict digraph DiskGraph {\n'
                'nodesep=0.35;\n'
                'subgraph cluster_graph {\n'
                'color="white";\n'
                '-4620721407511713798 [label="x = 0",style = filled]\n'
                '-4620721407511713798 -> -3743087399657325628 [label="Next",color="black",fontcolor="black"];\n'
                '-3743087399657325628 [label="x = 1"];\n'
                '-4620721407511713798 -> -3743087399657325628 [label="Next",color="black",fontcolor="black"];\n'
                '-3743087399657325628 -> -3743087399657325628 [label="Next",color="black",fontcolor="black"];\n'
                '-3743087399657325628 -> -3743087399657325628 [label="Next",color="black",fontcolor="black"];\n'
                '{rank = same; -4620721407511713798;}\n'
                '{rank = same; -3743087399657325628;}\n'
                '}\n'
                '}',
         'tla': "---- MODULE Dup ----\nVARIABLES x\nInit == x = 0\nNext == \\E i \\in {1, 2} : x' = 1\nSpec == Init /\\ [][Next]_x\n====\n",
         'cfg': 'SPECIFICATION Spec\nCHECK_DEADLOCK FALSE\n'},
 'ActProp': {'rc': 0,
             'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                       'Semantic processing of module Naturals\n'
                       'Semantic processing of module ActProp\n'
                       'Computing initial states...\n'
                       'Error: Action property Mono is violated.\n'
                       'Error: The behavior up to this point is:\n'
                       'State 1: <Initial predicate>\n'
                       'x = 0\n'
                       '\n'
                       'State 2: <Inc line 5, col 8 to line 5, col 26 of module ActProp>\n'
                       'x = 1\n'
                       '\n'
                       'State 3: <Inc line 5, col 8 to line 5, col 26 of module ActProp>\n'
                       'x = 2\n'
                       '\n'
                       'State 4: <Back line 6, col 9 to line 6, col 23 of module ActProp>\n'
                       'x = 1\n'
                       '\n'
                       'Model checking completed. No error has been found.\n'
                       '  Estimates of the probability that TLC did not check all reachable states\n'
                       '  because two distinct states had the same fingerprint:\n'
                       '  calculated (optimistic):  val = 1.6E-19\n'
                       '4 states generated, 3 distinct states found, 0 states left on queue.\n'
                       'The depth of the complete state graph search is 3.\n'
                       'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 1 and the 95th percentile is 1).\n',
             'dot': 'strict digraph DiskGraph {\n'
                    'nodesep=0.35;\n'
                    'subgraph cluster_graph {\n'
                    'color="white";\n'
                    '-1367331574555479329 [label="x = 0",style = filled]\n'
                    '-1367331574555479329 -> -637813419044459402 [label="Inc",color="black",fontcolor="black"];\n'
                    '-637813419044459402 [label="x = 1"];\n'
                    '-637813419044459402 -> -2790308373070655603 [label="Inc",color="black",fontcolor="black"];\n'
                    '-2790308373070655603 [label="x = 2"];\n'
                    '-2790308373070655603 -> -637813419044459402 [label="Back",color="black",fontcolor="black"];\n'
                    '{rank = same; -1367331574555479329;}\n'
                    '{rank = same; -637813419044459402;}\n'
                    '{rank = same; -2790308373070655603;}\n'
                    '}\n'
                    '}',
             'tla': '---- MODULE ActProp ----\n'
                    'EXTENDS Naturals\n'
                    'VARIABLES x\n'
                    'Init == x = 0\n'
                    "Inc == x < 2 /\\ x' = x + 1\n"
                    "Back == x = 2 /\\ x' = 1\n"
                    'Next == Inc \\/ Back\n'
                    'Spec == Init /\\ [][Next]_x\n'
                    "Mono == [][x' >= x]_x\n"
                    '====\n',
             'cfg': 'SPECIFICATION Spec\nPROPERTY Mono\nCHECK_DEADLOCK FALSE\n'},
 'Ends': {'rc': 11,
          'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                    'Semantic processing of module Ends\n'
                    'Computing initial states...\n'
                    'Error: Deadlock reached.\n'
                    'Error: The behavior up to this point is:\n'
                    'State 1: <Initial predicate>\n'
                    '/\\ n = 0\n'
                    '/\\ status = "draft"\n'
                    '\n'
                    'State 2: <Ship line 4, col 9 to line 4, col 62 of module Ends>\n'
                    '/\\ n = 0\n'
                    '/\\ status = "shipped"\n'
                    '\n'
                    '4 states generated, 4 distinct states found, 1 states left on queue.\n'
                    'The depth of the complete state graph search is 2.\n'
                    'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 1 and the 95th percentile is 1).\n',
          'dot': 'strict digraph DiskGraph {\n'
                 'nodesep=0.35;\n'
                 'subgraph cluster_graph {\n'
                 'color="white";\n'
                 '-1166403320719592901 [label="/\\\\ n = 0\\n/\\\\ status = \\"draft\\"",style = filled]\n'
                 '389800232400978624 [label="/\\\\ n = 1\\n/\\\\ status = \\"draft\\"",style = filled]\n'
                 '-1166403320719592901 -> -5910665020207294348 [label="Ship",color="black",fontcolor="black"];\n'
                 '-5910665020207294348 [label="/\\\\ n = 0\\n/\\\\ status = \\"shipped\\""];\n'
                 '389800232400978624 -> -8316141006715767992 [label="Ship",color="black",fontcolor="black"];\n'
                 '-8316141006715767992 [label="/\\\\ n = 1\\n/\\\\ status = \\"shipped\\""];\n'
                 '{rank = same; 389800232400978624;-1166403320719592901;}\n'
                 '}\n'
                 '}',
          'tla': '---- MODULE Ends ----\n'
                 'VARIABLES status, n\n'
                 'Init == status = "draft" /\\ n \\in {0, 1}\n'
                 'Ship == status = "draft" /\\ status\' = "shipped" /\\ UNCHANGED n\n'
                 'Next == Ship\n'
                 'Spec == Init /\\ [][Next]_<<status, n>>\n'
                 '====\n',
          'cfg': 'SPECIFICATION Spec\n'},
 'Mid': {'rc': 11,
         'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                   'Semantic processing of module Naturals\n'
                   'Semantic processing of module Mid\n'
                   'Computing initial states...\n'
                   'Error: Deadlock reached.\n'
                   'Error: The behavior up to this point is:\n'
                   'State 1: <Initial predicate>\n'
                   'x = 0\n'
                   '\n'
                   'State 2: <Inc line 5, col 8 to line 5, col 26 of module Mid>\n'
                   'x = 1\n'
                   '\n'
                   'State 3: <Inc line 5, col 8 to line 5, col 26 of module Mid>\n'
                   'x = 2\n'
                   '\n'
                   '3 states generated, 3 distinct states found, 0 states left on queue.\n'
                   'The depth of the complete state graph search is 3.\n'
                   'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 1 and the 95th percentile is 1).\n',
         'dot': 'strict digraph DiskGraph {\n'
                'nodesep=0.35;\n'
                'subgraph cluster_graph {\n'
                'color="white";\n'
                '2067335237120451972 [label="x = 0",style = filled]\n'
                '2067335237120451972 -> -243121665473337171 [label="Inc",color="black",fontcolor="black"];\n'
                '-243121665473337171 [label="x = 1"];\n'
                '-243121665473337171 -> 5184847016464905161 [label="Inc",color="black",fontcolor="black"];\n'
                '5184847016464905161 [label="x = 2"];\n'
                '{rank = same; 2067335237120451972;}\n'
                '{rank = same; -243121665473337171;}\n'
                '}\n'
                '}',
         'tla': '---- MODULE Mid ----\n'
                'EXTENDS Naturals\n'
                'VARIABLES x\n'
                'Init == x = 0\n'
                "Inc == x < 2 /\\ x' = x + 1\n"
                'Next == Inc\n'
                'Spec == Init /\\ [][Next]_x\n'
                '====\n',
         'cfg': 'SPECIFICATION Spec\n'},
 'Skew': {'rc': 0,
          'stdout': 'TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n'
                    'Semantic processing of module Naturals\n'
                    'Semantic processing of module Skew\n'
                    'Computing initial states...\n'
                    'Error: Invariant NoShipUnpaid is violated.\n'
                    'Error: The behavior up to this point is:\n'
                    'State 1: <Initial predicate>\n'
                    '/\\ status = "draft"\n'
                    '/\\ paid = FALSE\n'
                    '\n'
                    'State 2: <Submit line 6, col 11 to line 6, col 69 of module Skew>\n'
                    '/\\ status = "submitted"\n'
                    '/\\ paid = FALSE\n'
                    '\n'
                    'State 3: <Pay line 8, col 9 to line 8, col 69 of module Skew>\n'
                    '/\\ status = "shipped"\n'
                    '/\\ paid = FALSE\n'
                    '\n'
                    'Model checking completed. No error has been found.\n'
                    '  Estimates of the probability that TLC did not check all reachable states\n'
                    '  because two distinct states had the same fingerprint:\n'
                    '  calculated (optimistic):  val = 3.3E-19\n'
                    '7 states generated, 6 distinct states found, 0 states left on queue.\n'
                    'The depth of the complete state graph search is 4.\n'
                    'The average outdegree of the complete state graph is 1 (minimum is 0, the maximum 2 and the 95th percentile is 2).\n',
          'dot': 'strict digraph DiskGraph {\n'
                 'nodesep=0.35;\n'
                 'subgraph cluster_graph {\n'
                 'color="white";\n'
                 '8181626006461855957 [label="/\\\\ status = \\"draft\\"\\n/\\\\ paid = FALSE",style = filled]\n'
                 '8181626006461855957 -> 339239318837375949 [label="Submit",color="black",fontcolor="black"];\n'
                 '339239318837375949 [label="/\\\\ status = \\"submitted\\"\\n/\\\\ paid = FALSE"];\n'
                 '8181626006461855957 -> 1431808373273980104 [label="Cancel",color="black",fontcolor="black"];\n'
                 '1431808373273980104 [label="/\\\\ status = \\"cancelled\\"\\n/\\\\ paid = FALSE"];\n'
                 '339239318837375949 -> -3851923108473148600 [label="Pay",color="black",fontcolor="black"];\n'
                 '-3851923108473148600 [label="/\\\\ status = \\"submitted\\"\\n/\\\\ paid = TRUE"];\n'
                 '339239318837375949 -> 5915724344508359127 [label="Ship",color="black",fontcolor="black"];\n'
                 '5915724344508359127 [label="/\\\\ status = \\"shipped\\"\\n/\\\\ paid = FALSE"];\n'
                 '339239318837375949 -> 1431808373273980104 [label="Cancel",color="black",fontcolor="black"];\n'
                 '-3851923108473148600 -> -7194817092460316334 [label="Ship",color="black",fontcolor="black"];\n'
                 '-7194817092460316334 [label="/\\\\ status = \\"shipped\\"\\n/\\\\ paid = TRUE"];\n'
                 '{rank = same; 8181626006461855957;}\n'
                 '{rank = same; 339239318837375949;}\n'
                 '{rank = same; -3851923108473148600;}\n'
                 '}\n'
                 '}',
          'tla': '---- MODULE Skew ----\n'
                 'EXTENDS Naturals\n'
                 'VARIABLES status, paid\n'
                 'vars == <<status, paid>>\n'
                 'Init == status = "draft" /\\ paid = FALSE\n'
                 'Submit == status = "draft" /\\ status\' = "submitted" /\\ UNCHANGED paid\n'
                 'Pay == status = "submitted" /\\ ~paid /\\ paid\' = TRUE /\\ UNCHANGED status\n'
                 'Ship == status = "submitted" /\\ status\' = "shipped" /\\ UNCHANGED paid\n'
                 'Cancel == status \\in {"draft", "submitted"} /\\ ~paid /\\ status\' = "cancelled" /\\ UNCHANGED paid\n'
                 'Next == Submit \\/ Pay \\/ Ship \\/ Cancel\n'
                 'Spec == Init /\\ [][Next]_vars\n'
                 'NoShipUnpaid == status = "shipped" => paid\n'
                 '====\n',
          'cfg': 'SPECIFICATION Spec\nINVARIANT NoShipUnpaid\nCHECK_DEADLOCK FALSE\n'}}

# `Calm` は本物の `Order` のモジュールの名前だけを替えた写し（違反の出ない陽性対照）
FIXTURES["Calm"] = {**FIXTURES["Order"], "tla": FIXTURES["Order"]["tla"].replace("MODULE Order", "MODULE Calm")}
# `Slow` も同じ写し。偽の TLC は状態グラフを書いてから眠る（時間切れ——状態グラフが在っても走りきっていない）
FIXTURES["Slow"] = {**FIXTURES["Order"], "tla": FIXTURES["Order"]["tla"].replace("MODULE Order", "MODULE Slow")}

FAKE_TLC = """#!{python}
import json, os, re, sys
fixtures = json.load(open({fixtures!r}, encoding="utf-8"))
args = sys.argv[1:]
os.makedirs("states", exist_ok=True)
text = open(args[-1], encoding="utf-8").read()
module = re.search(r"MODULE (\\w+)", text).group(1)
if module == "Broken":
    print("Error: Parsing or semantic analysis failed."); sys.exit(150)
name = module if "-continue" in args else module + ":nocontinue"
case = fixtures.get(name, fixtures[module])
if "-dump" in args:
    kind, path = args[args.index("-dump") + 1], args[args.index("-dump") + 2]
    if kind == "dot,actionlabels":
        open(path, "w", encoding="utf-8").write(case["dot"])
if module == "Slow":
    sys.stdout.flush(); import time; time.sleep(5)
sys.stdout.write(case["stdout"])
sys.exit(case["rc"])
"""

VIEW_ORDER = {"states": [
    {"when": {"status": '"draft"'}, "label": "下書き"},
    {"when": {"status": '"submitted"', "paid": "FALSE"}, "label": "申請済み（未払い）"},
    {"when": {"status": '"submitted"', "paid": "TRUE"}, "label": "申請済み（支払い済み）"},
    {"when": {"status": '"shipped"', "paid": "FALSE"}, "label": "未払いのまま出荷済み"},
    {"when": {"status": '"shipped"'}, "label": "出荷済み"},
    {"when": {"status": '"cancelled"'}, "label": "取り消し済み"}],
    "actions": {"Submit": "申請する", "Pay": "支払う", "Ship": "出荷する", "Cancel": "取り消す"}}
# 申請済みを 1 つにまとめ、支払いを同じ状態に戻る行為として描かない
VIEW_ORDER_MERGED = {"states": [
    {"when": {"status": '"draft"'}, "label": "下書き"},
    {"when": {"status": '"submitted"'}, "label": "申請済み"},
    {"when": {"status": '"shipped"'}, "label": "出荷済み"},
    {"when": {"status": '"cancelled"'}, "label": "取り消し済み"}],
    "actions": {"Submit": "申請する", "Ship": "出荷する", "Cancel": "取り消す"}, "skip": ["Pay"]}
VIEW_TWO = {"states": [{"when": {"x": str(n)}, "label": w} for n, w in enumerate(["ゼロ", "いち", "に", "さん", "よん"])],
            "actions": {"Inc": "増やす", "Reset": "戻す"}}
VIEW_PAR = {"states": [{"when": {"done": "{}"}, "label": "まだ"}, {"when": {"done": "{a}"}, "label": "aだけ"},
                       {"when": {"done": "{b}"}, "label": "bだけ"}, {"when": {"done": "{a, b}"}, "label": "両方"}],
            "actions": {"Write": "書く"}}
VIEW_LIVE = {"states": [{"when": {"x": str(n)}, "label": w} for n, w in enumerate(["ゼロ", "いち", "に"])],
             "actions": {"Inc": "増やす", "Loop": "戻す"}}
VIEW_DEAD = {"states": [{"when": {"x": "1"}, "label": "止めた"}, {"when": {"r": '[s |-> "a"]', "x": "0"}, "label": "はじめ"},
                        {"when": {"x": "2"}, "label": "進めた"}, {"when": {"x": "3"}, "label": "3 番目"}, {"when": {"x": "4"}, "label": "4 番目"}],
             "actions": {"Stop": "止める", "Go": "進める", "Step": "次へ", "Back": "戻る"}}
VIEW_INIT = {"states": [{"when": {"x": str(n)}, "label": f"{n} 個"} for n in range(7)], "actions": {"Inc": "増やす"}}
VIEW_DUP = {"states": [{"when": {"x": "0"}, "label": "はじめ"}, {"when": {"x": "1"}, "label": "進んだ"}], "actions": {"Next": "進む"}}
VIEW_ENDS = {"states": [{"when": {"status": '"draft"'}, "label": "下書き"}, {"when": {"status": '"shipped"'}, "label": "出荷済み"}],
             "actions": {"Ship": "出荷する"}}
# 行き止まり（x=2）と、先へ進める状態（x=1）を同じ言葉にまとめる——狭いパスの指摘（R1）の試料
VIEW_MID = {"states": [{"when": {"x": "0"}, "label": "はじめ"}, {"when": {"x": "1"}, "label": "途中終わり"}, {"when": {"x": "2"}, "label": "途中終わり"}],
            "actions": {"Inc": "増やす"}}
# 図に出てはならない語（変数名・行為の名前・TLA+ の値）
HIDDEN = {"Order": ["status", "paid", "Submit", "Ship", "Cancel", "draft", "FALSE"], "OrderBroken": ["status", "paid", "Ship", "FALSE"],
          "Two": ["x =", "Inc", "Reset"], "Par": ["done", "Write"], "Dead": ["|->", "Stop", "Go"]}


def model_files(name: str) -> dict[str, str]:
    return {f"{name}.tla": FIXTURES[name]["tla"], f"{name}.cfg": FIXTURES[name]["cfg"]}


def target(body: str = "Order", controls: tuple[str, ...] = (), view: dict | str | None = VIEW_ORDER,
           extra_rows: tuple[str, ...] = ()) -> dict[str, str]:
    files = {**model_files(body)}
    rows = ["| 項目 | 記録 |", "| --- | --- |", "| 対象 | x |", "| 検査器 | TLC 2.19 |", "| 構成の大きさ | 1 |", "| 結果 | 反例なし |",
            "| 陽性対照 | x |", "| 置いた前提 | なし |", "| 前回のモデル | 無かった |", f"| モデルのファイル | `{body}.tla`・`{body}.cfg` |"]
    if controls:
        rows.append("| 陽性対照のファイル | " + "・".join(f"`{c}.tla`・`{c}.cfg`" for c in controls) + " |")
        for c in controls:
            files.update(model_files(c) if c in FIXTURES else {f"{c}.tla": f"---- MODULE {c} ----\n====\n", f"{c}.cfg": "x\n"})
    if view is not None:
        rows.append("| 図の対応のファイル | `view.json` |")
        files["view.json"] = view if isinstance(view, str) else json.dumps(view, ensure_ascii=False)
    rows += list(extra_rows) + ["| 残した回 | v1・2026-11-18・1 回目 |"]
    files["README.md"] = "\n".join(rows) + "\n"
    return files


T = "docs/v1/spec/formal/order-ship"
CALL = "@FAKE@"
OUT = "OUT"  # --out の置き場所の印（試料を組むときに一時ディレクトリの中のファイルに替える）
OLD = "古い図\n"


def bad_view(**over) -> dict:
    view = json.loads(json.dumps(VIEW_ORDER))
    for k, v in over.items():
        view[k] = v
    return view


# 名前 → (CLAUDE.md（None なら置かない）, 対象の中身, 引数, 期待の終了コード, 出力に含む語, 照らす (モデル, 対応, 経路だけか) の並び)
CASES: dict[str, tuple] = {
    "本体: 反例なし": (f"TLC の呼び方: {CALL}\n", target(), [], 0, "反例なし", [("Order", VIEW_ORDER, False)]),
    "陽性対照に印と経路（受入基準 2）": (f"TLC の呼び方: {CALL}\n", target(controls=("OrderBroken",)), ["--controls"], 0, "⚠ 未払いのまま出荷済み",
                               [("Order", VIEW_ORDER, False), ("OrderBroken", VIEW_ORDER, False)]),
    "本体の反例が 3 つ": (f"TLC の呼び方: {CALL}\n", target("Two", view=VIEW_TWO), [], 0, "反例あり", [("Two", VIEW_TWO, False)]),
    "行き止まり": (f"TLC の呼び方: {CALL}\n", target("Par", view=VIEW_PAR), [], 0, "行き止まり", [("Par", VIEW_PAR, False)]),
    "途中で止まったグラフ・値に ->": (f"TLC の呼び方: {CALL}\n", target("Dead", view=VIEW_DEAD), [], 0, "全体ではない", [("Dead", VIEW_DEAD, False)]),
    "初めの状態が破る": (f"TLC の呼び方: {CALL}\n", target("InitBad", view=VIEW_INIT), [], 0, "反例あり", [("InitBad", VIEW_INIT, False)]),
    "重なった辺は 1 本に数える": (f"TLC の呼び方: {CALL}\n", target("Dup", view=VIEW_DUP), [], 0, "TLC の状態 2・遷移 2）", [("Dup", VIEW_DUP, False)]),
    "反例の後に評価の誤りで止まる": (f"TLC の呼び方: {CALL}\n", target("CrashAfter", view=VIEW_TWO | {"actions": {"Inc": "増やす", "Boom": "壊す"}}),
                          ["--out", OUT], 4, "unexpected exception", []),
    "行為の性質の反例は描かない": (f"TLC の呼び方: {CALL}\n", target("ActProp", view=VIEW_TWO | {"actions": {"Inc": "増やす", "Back": "戻す"}}),
                        ["--out", OUT], 1, "行為の性質", []),
    "行き止まりで止まった同じ言葉の終わり": (f"TLC の呼び方: {CALL}\n", target("Ends", view=VIEW_ENDS), [], 0, "行き止まり", [("Ends", VIEW_ENDS, False)]),
    "行き止まりと先へ進める状態をまとめる": (f"TLC の呼び方: {CALL}\n", target("Mid", view=VIEW_MID), [], 1, "同じ言葉にまとめている", []),
    "大きいモデルは経路だけ": (f"TLC の呼び方: {CALL}\n", target("Two", view=VIEW_TWO), ["--max-edges", "2"], 0, "経路だけを描いた", [("Two", VIEW_TWO, True)]),
    "まとめて skip": (f"TLC の呼び方: {CALL}\n", target(view=VIEW_ORDER_MERGED), [], 0, "申請済み", [("Order", VIEW_ORDER_MERGED, False)]),
    "--out に書く": (f"TLC の呼び方: {CALL}\n", target(), ["--out", OUT], 0, "書いた", [("Order", VIEW_ORDER, False)]),
    "時相の性質の反例は描かない": (f"TLC の呼び方: {CALL}\n", target("Live", view=VIEW_LIVE), ["--out", OUT], 1, "時相の性質", []),
    "対応に無い状態": (f"TLC の呼び方: {CALL}\n", target(view=bad_view(states=VIEW_ORDER["states"][:-1])), ["--out", OUT], 1, "言葉の無い状態", []),
    "対応に無い行為": (f"TLC の呼び方: {CALL}\n", target(view=bad_view(actions={"Submit": "申請する", "Pay": "支払う", "Ship": "出荷する"})), [], 1,
                "言葉の無い行為", []),
    "破る状態と破らない状態をまとめる": (f"TLC の呼び方: {CALL}\n", target(controls=("OrderBroken",), view=VIEW_ORDER_MERGED | {"skip": ["Pay"]}),
                            ["--controls"], 1, "同じ言葉にまとめている", []),
    "skip が別の状態へ移る": (f"TLC の呼び方: {CALL}\n", target(view=bad_view(actions={"Submit": "申請する", "Pay": "支払う", "Cancel": "取り消す"},
                                                                skip=["Ship"])), [], 1, "別の状態へ移る", []),
    "使えない文字": (f"TLC の呼び方: {CALL}\n", target(view=bad_view(actions={**VIEW_ORDER["actions"], "Pay": "支払う: 全額"})), [], 1,
               "使えない文字", []),
    "対応が無い変数を指す": (f"TLC の呼び方: {CALL}\n", target(view=bad_view(states=[{"when": {"state": '"draft"'}, "label": "a"}])), [], 1,
                   "状態に無い変数", []),
    "対応が JSON でない": (f"TLC の呼び方: {CALL}\n", target(view="{"), [], 1, "JSON として読めない", []),
    "反例の段が状態グラフに無い": (f"TLC の呼び方: {CALL}\n", target(controls=("Skew",)), ["--controls"], 4, "辺に無い", []),
    "対応の項目が無い": (f"TLC の呼び方: {CALL}\n", target(view=None), [], 4, "対応なしでは描かない", []),
    "陽性対照で違反が出ない": (f"TLC の呼び方: {CALL}\n", target(controls=("Calm",)), ["--controls"], 4, "空振り", []),
    "TLC が走りきらない（構文）": (f"TLC の呼び方: {CALL}\n", target(controls=("Broken",)), ["--controls", "--out", OUT], 4, "走りきらなかった", []),
    "TLC が途中で止まる": (f"TLC の呼び方: {CALL}\n", target("Crash", view=VIEW_TWO | {"actions": {"Inc": "増やす", "Boom": "壊す"}}), ["--out", OUT], 4,
                    "走りきらなかった", []),
    "時間切れ": (f"TLC の呼び方: {CALL}\n", target("Slow"), ["--timeout", "1", "--out", OUT], 4, "時間切れ", []),
    "呼び方の行が無い": (None, target(), [], 4, "TLC の呼び方が無い", []),
    "判定しない: --max-edges が 0": (f"TLC の呼び方: {CALL}\n", target(), ["--max-edges", "0"], 2, "--max-edges は 1 以上", []),
}


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name}{(': ' + detail) if detail else ''}")


# ---- 本体と別に読む（受入基準 3 の突き合わせの側）
def parse_state(text: str) -> dict[str, str]:
    lines = [ln for ln in text.strip().split("\n") if ln.strip()]
    parts = [ln[3:] for ln in lines] if lines[0].startswith("/\\ ") else [" ".join(lines)]
    return {p.split(" = ", 1)[0].strip(): " ".join(p.split(" = ", 1)[1].split()) for p in parts}


def parse_graph(dot: str):
    nodes, initial, edges = {}, set(), []
    for line in dot.split("\n"):
        line = line.strip()
        m = re.match(r'^(-?\d+) \[label="(.*)"(,style = filled)?\];?$', line)
        if m:
            nodes[m.group(1)] = parse_state(m.group(2).replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\"))
            if m.group(3):
                initial.add(m.group(1))
            continue
        m = re.match(r'^(-?\d+) -> (-?\d+) \[label="([^"]+)"', line)
        if m:
            edges.append(m.groups())
    return nodes, initial, edges


def parse_traces(out: str) -> list[list[tuple[str | None, dict[str, str]]]]:
    traces = []
    parts = re.split(r"^Error: (?:Invariant \w+ is violated(\.| by the initial state:)|Deadlock reached\.)$", out, flags=re.MULTILINE)
    for form, block in zip(parts[1::2], parts[2::2]):
        if form == " by the initial state:":  # 初めの状態が破る形——見出しが無く、状態がすぐ続く
            traces.append([(None, parse_state(block.strip().split("\n\n")[0]))])
            continue
        steps = []
        for m in re.finditer(r"^State \d+: <(\w+)[^>]*>\n((?:.+\n)+)", block, flags=re.MULTILINE):
            steps.append((None if m.group(1) == "Initial" else m.group(1), parse_state(m.group(2))))
        traces.append(steps)
    return traces


def label(state: dict[str, str], view: dict) -> str:
    return next(r["label"] for r in view["states"] if all(state.get(k) == v for k, v in r["when"].items()))


def expected(model: str, view: dict, path_only: bool):
    nodes, initial, edges = parse_graph(FIXTURES[model]["dot"])
    names = {n: label(s, view) for n, s in nodes.items()}
    skip = set(view.get("skip", []))
    all_edges = {(names[a], names[b], view["actions"][act]) for a, b, act in edges if act not in skip}
    traces = parse_traces(FIXTURES[model]["stdout"])
    bad = {label(t[-1][1], view) for t in traces}
    path = []
    if traces:
        t = traces[0]
        path = [(label(t[i - 1][1], view), label(t[i][1], view), view["actions"][t[i][0]]) for i in range(1, len(t))]
    states = set(names.values())
    if path_only:
        states = {label(s, view) for _, s in traces[0]}
        all_edges = set(path)
    return states, {names[n] for n in initial}, all_edges, bad & states, path


def parse_section(text: str, model: str):
    m = re.search(rf"^## {model}\.tla（[^\n]*）\n.*?```mermaid\nstateDiagram-v2\n(.*?)```", text, flags=re.MULTILINE | re.DOTALL)
    if m is None:
        return None
    ids, initial, edges, bad, numbered = {}, set(), set(), set(), {}
    classes = set()
    for line in m.group(1).split("\n"):
        line = line.strip()
        if mm := re.fullmatch(r"(s\d+): (.+)", line):
            text_ = mm.group(2)
            ids[mm.group(1)] = text_.removeprefix("⚠ ")
            if text_.startswith("⚠ "):
                bad.add(mm.group(1))
        elif mm := re.fullmatch(r"\[\*\] --> (s\d+)", line):
            initial.add(mm.group(1))
        elif mm := re.fullmatch(r"(s\d+) --> (s\d+): (.+)", line):
            nm = re.fullmatch(r"([0-9・]+)\. (.+)", mm.group(3))
            act = nm.group(2) if nm else mm.group(3)
            edges.add((mm.group(1), mm.group(2), act))
            if nm:
                for n in nm.group(1).split("・"):
                    numbered[int(n)] = (mm.group(1), mm.group(2), act)
        elif mm := re.fullmatch(r"class (s\d+) violated", line):
            classes.add(mm.group(1))
    to = ids.get
    return (set(ids.values()), {to(i) for i in initial}, {(to(a), to(b), act) for a, b, act in edges}, {to(i) for i in bad},
            {to(i) for i in classes}, [(to(numbered[k][0]), to(numbered[k][1]), numbered[k][2]) for k in sorted(numbered)])


def compare(text: str, model: str, view: dict, path_only: bool) -> list[str]:
    got = parse_section(text, model)
    if got is None:
        return [f"{model}: 図の節が無い"]
    states, initial, edges, bad, path = expected(model, view, path_only)
    g_states, g_initial, g_edges, g_bad, g_classes, g_path = got
    problems = []
    for what, want, have in (("状態", states, g_states), ("初めの状態", initial, g_initial), ("遷移", edges, g_edges),
                             ("印（⚠）", bad, g_bad), ("印（class）", bad, g_classes)):
        if want != have:
            problems.append(f"{model}: {what}が状態グラフと食い違う: 期待 {sorted(want)} / 図 {sorted(have)}")
    if path != g_path:
        problems.append(f"{model}: 反例の経路が食い違う: 期待 {path} / 図 {g_path}")
    for word in HIDDEN.get(model, []):
        if word in text:
            problems.append(f"{model}: 図に「{word}」が出た")
    return problems


def run_one(script: Path, work: Path, fake: Path, fakebin: Path, case: tuple) -> tuple[int, str, Path]:
    claude, files, args, *_ = case
    if work.exists():
        shutil.rmtree(work)
    repo = work / "repo"
    (repo / T).mkdir(parents=True)
    tmp = Path(tempfile.gettempdir()).resolve()
    check(f"試料が一時ディレクトリの中: {repo}", tmp in repo.resolve().parents)
    if claude is not None:
        (repo / "CLAUDE.md").write_text(claude.replace(CALL, str(fake)), encoding="utf-8")
    for name, body in files.items():
        (repo / T / name).write_text(body, encoding="utf-8")
    out_file = repo / T / "statechart.md"
    out_file.write_text(OLD, encoding="utf-8")
    argv = [str(out_file) if a == OUT else a for a in args]
    env = {**os.environ, "PATH": f"{fakebin}{os.pathsep}/usr/bin{os.pathsep}/bin"}
    proc = subprocess.run([sys.executable, "-I", str(script), str(repo), str(repo / T), *argv],
                          capture_output=True, text=True, cwd=work, env=env, timeout=120)
    return proc.returncode, proc.stdout + proc.stderr, repo


def problems_of(name: str, case: tuple, result: tuple[int, str, Path]) -> list[str]:
    code, out, repo = result
    _, files, args, want_code, want_text, compares = case
    problems = []
    if code != want_code:
        problems.append(f"終了コード {code}（期待 {want_code}）: {out[-300:]!r}")
    if want_text not in out:
        problems.append(f"出力に「{want_text}」が無い: {out[-300:]!r}")
    written = (repo / T / "statechart.md").read_text(encoding="utf-8")
    if OUT in args and code == 0:
        text = written
        if written == OLD:
            problems.append("--out に書いていない")
    else:
        text = out
        if written != OLD:
            problems.append("--out に触った（描けなかった・--out なし）")
    for model, view, path_only in compares:
        problems += compare(text, model, view, path_only)
    left = sorted(p.name for p in (repo / T).iterdir()) if (repo / T).is_dir() else []
    if left != sorted([*files, "statechart.md"]):
        problems.append(f"正本に残した: {sorted(set(left) - set(files) - {'statechart.md'})}")
    return problems


# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("遷移を 1 本落とす", "    for a, b, action in edges:\n        if action in skip:", "    for a, b, action in edges[:-1]:\n        if action in skip:", "本体: 反例なし"),
    ("言葉の無い状態に状態の式を使う", "            return label\n    return None",
     "            return label\n    return \" \".join(f\"{k}={v}\" for k, v in state.items())", "対応に無い状態"),
    ("言葉の無い行為を名前のまま描く", "        if action not in actions:\n            raise Stop(EXIT_UNDRAWABLE",
     "        if action not in actions:\n            actions[action] = action\n        if False:\n            raise Stop(EXIT_UNDRAWABLE", "対応に無い行為"),
    ("skip が別の状態へ移っても消す", "            if labels[a] != labels[b]:", "            if False:", "skip が別の状態へ移る"),
    ("印を付けない", "    bad_nodes = {walk[-1][1] for walk in walks}", "    bad_nodes = set()", "陽性対照に印と経路（受入基準 2）"),
    ("-continue を渡さない", '{call} -continue -dump dot,actionlabels', '{call} -dump dot,actionlabels', "本体の反例が 3 つ"),
    ("破る状態と破らない状態をまとめても通す", "    if mixed:\n", "    if False:\n", "破る状態と破らない状態をまとめる"),
    ("経路に番号を付けない", "            steps.setdefault(edge, []).append(number)", "            steps.setdefault(edge, [])", "陽性対照に印と経路（受入基準 2）"),
    ("経路の段が状態グラフに無くても通す", "            if walk and (walk[-1][1], node, action) not in edge_set:",
     "            if walk and (walk[-1][1], node, action) in edge_set and False:", "反例の段が状態グラフに無い"),
    ("陽性対照の空振りを通す", '        if kind != "本体" and not found:', "        if False:", "陽性対照で違反が出ない"),
    ("時相の性質の反例を描く", '                raise Stop(EXIT_UNDRAWABLE, "時相の性質の反例（繰り返しのある反例）は描かない")', "                pass",
     "時相の性質の反例は描かない"),
    ("走りきらない TLC の図を出す", "            if rc is None or not (tlc.GOOD_MARK in out or rerun.violated(out)) or not dot_path.is_file():",
     "            if not dot_path.is_file():", "時間切れ"),
    ("待ちの残ったグラフに書かない", "    if queued and int(queued[-1]) != 0:", "    if False:", "途中で止まったグラフ・値に ->"),
    ("辺を節点より先に読む", "        node = NODE.fullmatch(line)", '        node = None if "->" in line else NODE.fullmatch(line)', "途中で止まったグラフ・値に ->"),
    ("大きいモデルも全部描く", "            drawn_edges = set(steps)", "            drawn_edges = view_edges", "大きいモデルは経路だけ"),
    ("正本で走らせる", "{shlex.quote(dot_name)}\", tmp, name, timeout)", "{shlex.quote(dot_name)}\", str(directory), name, timeout)", "本体: 反例なし"),
    ("呼び方が無ければ PATH の tlc を使う", "        if call is None:\n            raise Stop(",
     "        if call is None:\n            call = \"tlc\"\n        if False:\n            raise Stop(", "呼び方の行が無い"),
    ("描けなくても --out を書く", "        print(f\"描かなかった: {stop}\", file=sys.stderr)\n",
     "        print(f\"描かなかった: {stop}\", file=sys.stderr)\n        args.out and args.out.write_text(\"x\")\n", "時相の性質の反例は描かない"),
    ("初めの状態に矢印を付けない", '    chart += [f"    [*] --> {ids[label]}" for label in states if label in starts]', "", "本体: 反例なし"),
    ("初めの状態が破る形を読まない", "            if line.rstrip().endswith(INITIAL):", "            if False:", "初めの状態が破る"),
    ("反例の後の評価の誤りを通す", "            if odd:", "            if False:", "反例の後に評価の誤りで止まる"),
    ("重なった辺を数える", "遷移 {len(edge_set)}）", "遷移 {len(edges)}）", "重なった辺は 1 本に数える"),
    ("行為の性質の反例を不変条件の反例と読む", '            if line.startswith("Error: Action property"):', "            if False:", "行為の性質の反例は描かない"),
    ("行き止まりにもまとめの検査をそのまま当てる", "    broken = {labels[walk[-1][1]] for walk, (dead, _) in zip(walks, traces) if not dead}",
     "    broken = bad_labels", "行き止まりで止まった同じ言葉の終わり"),
    ("行き止まりを先へ進める状態とまとめても通す", "(lab in broken or n in moving)", "(lab in broken)", "行き止まりと先へ進める状態をまとめる"),
    ("使えない文字を通す", "    if bad:\n        raise Stop(EXIT_UNDRAWABLE, f\"対応の {where}", "    if False:\n        raise Stop(EXIT_UNDRAWABLE, f\"対応の {where}",
     "使えない文字"),
]


def guard_rows(source: str) -> int:
    block = source.split("**守ること**:", 1)[1].split("**守らないもの**", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("| ") and not line.startswith("| 守ること") and "---" not in line)


def main() -> int:
    source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="formal-statechart-test-") as tmp:
        root = Path(tmp)
        scripts = root / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        fixtures = root / "fixtures.json"
        fixtures.write_text(json.dumps(FIXTURES, ensure_ascii=False), encoding="utf-8")
        fake = root / "fake-tlc"
        fake.write_text(FAKE_TLC.format(python=sys.executable, fixtures=str(fixtures)), encoding="utf-8")
        fake.chmod(0o755)
        fakebin = root / "bin"
        fakebin.mkdir()
        shutil.copyfile(fake, fakebin / "tlc")
        (fakebin / "tlc").chmod(0o755)
        check("偽の tlc が PATH で見つかる（呼び方の行が無いのに探したら描ける形）",
              shutil.which("tlc", path=f"{fakebin}{os.pathsep}/usr/bin{os.pathsep}/bin") == str(fakebin / "tlc"))

        # 突き合わせの側の陽性対照: 状態グラフから遷移を 1 本落とした図は食い違うと言う
        print("試料")
        results = {}
        for i, (name, case) in enumerate(CASES.items()):
            results[name] = run_one(scripts / TARGET, root / f"c{i}", fake, fakebin, case)
            problems = problems_of(name, case, results[name])
            check(f"試料: {name}", not problems, "・".join(problems))
        good = results["陽性対照に印と経路（受入基準 2）"][1]
        first_edge = re.search(r"^    s\d+ --> s\d+: .+$\n", good, flags=re.MULTILINE).group(0)
        check("突き合わせの陽性対照: 遷移を落とした図", bool(compare(good.replace(first_edge, "", 1), "Order", VIEW_ORDER, False)))
        check("突き合わせの陽性対照: 印を外した図", bool(compare(good.replace("⚠ ", ""), "OrderBroken", VIEW_ORDER, False)))
        check("突き合わせの陽性対照: 経路の番号を外した図", bool(compare(re.sub(r": [0-9・]+\. ", ": ", good), "OrderBroken", VIEW_ORDER, False)))
        print(f"  {len(CASES)} 件 OK（突き合わせの陽性対照 3 件）")

        print("変異テスト")
        rows = guard_rows(source)
        check("変異の数が「守ること」の行の数以上", len(MUTATIONS) >= rows, f"変異 {len(MUTATIONS)} < 行 {rows}")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            check(f"壊す箇所がちょうど 1 回: {name}", source.count(before) == 1, f"{source.count(before)} 回: {before!r}")
            mutated = root / f"m{index}"
            shutil.copytree(scripts, mutated)
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            case = CASES[killer]
            got = run_one(mutated / TARGET, root / f"mw{index}", fake, fakebin, case)
            check(f"変異を殺す: {name} ← {killer}", bool(problems_of(killer, case, got)), f"{got[0]} {got[1][-300:]!r}")
        print(f"  変異 {len(MUTATIONS)} 件 OK")
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
