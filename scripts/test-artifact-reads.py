#!/usr/bin/env python3
"""`artifact-reads.py`（dev-loop の周が読んだ spec-loop の成果物を計画ファイルから数える。#1157）の回帰テスト。

    python3 scripts/test-artifact-reads.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）。`test-find-cycle.py` と同じ形。

見るもの:

1. **数える**——成果物ごとに読んだ周の数・その周の起票の合計・関門の指摘の合計（陽性対照）。1 周で同じパスは 1 件、`./` は外す、
   ディレクトリは `*.md` を再帰、同じファイルを 2 度渡しても 1 本、コードブロックの中の行は数えない、起票の行・関門の記録の無い周の数を出す。
2. **一度も読まれない成果物**——`--all-artifacts` に挙げたパスのうち、どの周にも無いものを 0 の行で出す。
3. **黙って落とさない**——形に合わない行（装飾つき・字下げ・番号・チェックボックス・見出し・バッククォートの無いパス・1 行に 2 つのパス・`なし` とパスの混在）・
   閉じないコードブロック・読めない関門の記録は名指しして 1。関門の記録は `check-gates.py` が通す書き方（`~~~`・コロンの後の空白なし・当て直し）を同じに読む。
4. **0 にしない**——無いパス・計画ファイルが 1 本も無い・UTF-8 でない計画ファイル・引数の誤り・読めない `--all-artifacts` は 2。
5. **読むだけ**——走らせた前後で試料のディレクトリと、写したスクリプトのディレクトリ（`__pycache__` を含む）が 1 バイトも変わらない。
   **陽性対照**: 試料のディレクトリ・スクリプトの隣に書き込む変異と、読み込みで `__pycache__` を書く変異が落ちる。
6. **原本との突き合わせ**——`references/spec-gap.md` の例の行が本体の正規表現に当たり、本体を指す。
7. **リポジトリの外で単体で動く**——`scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待（終了コードと、出力に含む行・含まない語）から外れること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**と、**変異の前は期待どおりであること**を先に確かめる。
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SKILL = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop"
SCRIPTS = SKILL / "scripts"
TARGET = "artifact-reads.py"
SPEC_GAP = SKILL / "references" / "spec-gap.md"

IR = "build/merged/spec/spec_ir.json"
RED = "scaffold/tests/test_order.py"
REF = "scaffold/refs/order-mock.html"


def plan(*reads: str, count: int | None = 0, gates: list[int] | None = None, extra: str = "") -> str:
    body = "# Issue #1 — 試料\n\n## 読んだ成果物\n\n"
    for r in reads:
        body += (r if r.startswith(("- ", " ", "*", "読")) else f"- 読んだ成果物: `{r}`") + "\n"
    body += extra
    if gates is not None:
        body += "\n```dev-loop-gates\n周の base: abcdef1\n"
        for i, n in enumerate(gates):
            body += f"関門: Verifier {i + 1} abcdef1 反証={n}\n" if i % 2 == 0 else f"関門: /code-review {i} abcdef1 指摘={n}\n"
        body += "関門: 狭いパス 該当なし\n受入基準: A1 満たす\n```\n"
    if count is not None:
        body += f"\n## 手順 8\n\n- この周の起票: {count} 件（試料）\n"
    return body


def row(path: str, cycles: int, counts: int, gates: int) -> str:
    return f"| `{path}` | {cycles} | {counts} | {gates} |"


# 名前 → (試料のファイル（相対パス → 中身。None は置かずに渡す）, 渡す引数（"@" はディレクトリの根）, 期待の終了コード, 出力に含む語, 出力に含まない語)
CASES: dict[str, tuple] = {
    "数える: 周の結果と並べる（陽性対照）": ({"plans/a.md": plan(IR, RED, count=1, gates=[2, 3]), "plans/b.md": plan(IR, count=2, gates=[0, 4])},
                                       ["@plans"], 0,
                                       [row(IR, 2, 3, 9), row(RED, 1, 1, 5), "計画ファイル: 2 本・読んだ成果物の記録のある周: 2 本"], []),
    "数える: 多い順に並べる": ({"p/a.md": plan("a/spec.md", IR), "p/b.md": plan(IR)}, ["@p"], 0, [row(IR, 2, 0, 0) + "\n" + row("a/spec.md", 1, 0, 0)], []),
    "数える: 同じ周の同じパスは 1 件": ({"p/a.md": plan(IR, IR, f"./{IR}")}, ["@p"], 0, [row(IR, 1, 0, 0)], [f"`./{IR}`"]),
    "数える: 注記つきの行": ({"p/a.md": plan(f"- 読んだ成果物: `{REF}`（手順 4）", f"- 読んだ成果物: `{RED}` 手順 2")}, ["@p"], 0,
                        [row(REF, 1, 0, 0), row(RED, 1, 0, 0)], ["形に合わない"]),
    "数える: ディレクトリを再帰する": ({"p/x/y/a.md": plan(IR), "p/b.txt": plan(RED)}, ["@p"], 0, [row(IR, 1, 0, 0), "計画ファイル: 1 本"], [f"`{RED}`"]),
    "数える: 同じファイルを 2 度渡しても 1 本": ({"p/a.md": plan(IR)}, ["@p/a.md", "@p"], 0, [row(IR, 1, 0, 0), "計画ファイル: 1 本"], []),
    "数える: コードブロックの中の行は数えない": ({"p/a.md": plan(IR, extra=f"\n```text\n- 読んだ成果物: `{RED}`\n- 読んだ成果物: x\n```\n")}, ["@p"], 0,
                                        [row(IR, 1, 0, 0)], [f"`{RED}`", "形に合わない"]),
    "数える: 記録の無い周は数えない": ({"p/a.md": plan(IR), "p/b.md": plan(count=5, gates=[7])}, ["@p"], 0,
                                   [row(IR, 1, 0, 0), "読んだ成果物の記録のある周: 1 本"], []),
    "数える: なしの周": ({"p/a.md": plan("- 読んだ成果物: なし"), "p/b.md": plan(IR)}, ["@p"], 0,
                     ["記録のある周: 2 本（うち `なし`: 1 本）", row(IR, 1, 0, 0)], ["形に合わない"]),
    "数える: 起票の行・関門の記録の無い周": ({"p/a.md": plan(IR, count=None), "p/b.md": plan(IR, count=1, gates=[1, 1])}, ["@p"], 0,
                                      [row(IR, 2, 1, 2), "起票の行が無い周: 1", "関門の記録が無い周: 1"], []),
    "数える: 関門のブロックの外（地の文・ほかのコードブロック）の関門の行は数えない": ({"p/a.md": plan(IR, extra="関門: Verifier 1 abcdef1 反証=50\n\n```text\n関門: Verifier 1 abcdef1 反証=70\n```\n", gates=[1])}, ["@p"], 0,
                                             [row(IR, 1, 0, 1)], []),
    "数える: 一度も読まれない成果物": ({"p/a.md": plan(IR), "all.txt": f"# 試料\n{IR}\n\n./{REF}\n"}, ["@p", "--all-artifacts", "@all.txt"], 0,
                                   [row(IR, 1, 0, 0), row(REF, 0, 0, 0), "一度も読まれない成果物: 1"], []),
    "数えない: 太字の行": ({"p/a.md": plan(IR, f"**読んだ成果物**: `{RED}`")}, ["@p"], 1, ["形に合わない行（数えていない）: 1", "a.md: 6 行目"], [f"`{RED}`"]),
    "数えない: 字下げした行": ({"p/a.md": plan(IR, f"  - 読んだ成果物: `{RED}`")}, ["@p"], 1, ["a.md: 6 行目", row(IR, 1, 0, 0)], [f"`{RED}`"]),
    "数えない: バッククォートの無いパス": ({"p/a.md": plan(f"- 読んだ成果物: {RED}")}, ["@p"], 1, ["a.md: 5 行目"], [f"`{RED}`"]),
    "数えない: 全角のコロン": ({"p/a.md": plan(f"- 読んだ成果物：`{RED}`")}, ["@p"], 1, ["a.md: 5 行目"], [f"`{RED}`"]),
    "数えない: なしとパスの混在": ({"p/a.md": plan(IR, "- 読んだ成果物: なし")}, ["@p"], 1, ["a.md: 6 行目: なしとパスを両方書いている"], []),
    "数えない: 散文の言及は形の誤りでない": ({"p/a.md": plan(IR, extra="読んだ成果物を記録する決まりは spec-gap.md にある。\n読んだ成果物ごとに数える。\n- 読んだ成果物、とは何か\n"
                                                         "- 読んだ成果物から集める\n- 読んだ成果物として\n## 読んだ成果物\n")}, ["@p"], 0, [row(IR, 1, 0, 0)], ["形に合わない"]),
    "数える: ほかのブロックの中の関門の記録の例は記録でない": ({"p/a.md": plan(IR, extra="\n````markdown\n```dev-loop-gates\n関門: Verifier 1 abcdef1 反証=1\n```\n````\n")}, ["@p"], 0,
                                                  [row(IR, 1, 0, 0), "関門の記録が無い周: 1"], ["形に合わない"]),
    "数えない: 無いパス": ({"p/a.md": plan(IR)}, ["@p", "@nothing"], 2, ["無いパス"], ["| `"]),
    "数えない: 計画ファイルが無い": ({"p/a.txt": "x"}, ["@p"], 2, ["1 本も無い"], []),
    "数えない: 引数なし": ({}, [], 2, ["usage"], []),
    "数えない: 未知の引数": ({"p/a.md": plan(IR)}, ["@p", "--all"], 2, ["usage"], []),
    "数えない: 読めない --all-artifacts": ({"p/a.md": plan(IR)}, ["@p", "--all-artifacts", "@none.txt"], 2, ["読めない"], ["| `"]),
    "数えない: 番号・チェックボックス・見出し・バッククォートの見出し": ({"p/a.md": plan(IR, f"1. 読んだ成果物: `{RED}`", f"- [ ] 読んだ成果物: `{RED}`",
                                                                    f"### 読んだ成果物: `{RED}`", f"- `読んだ成果物`: `{RED}`")}, ["@p"], 1,
                                                      ["形に合わない行（数えていない）: 4", "a.md: 6 行目", "a.md: 9 行目", row(IR, 1, 0, 0)], [f"`{RED}` |"]),
    "数えない: 1 行に 2 つのパス": ({"p/a.md": plan(f"- 読んだ成果物: `{IR}` `{RED}`")}, ["@p"], 1, ["a.md: 5 行目"], [f"`{RED}` |", f"`{IR}` |"]),
    "数えない: 4 つのバッククォートの中の 3 つのブロック": ({"p/a.md": plan(IR, extra=f"\n````markdown\n```text\nx\n```\n- 読んだ成果物: `{RED}`\n````\n")}, ["@p"], 0,
                                                 [row(IR, 1, 0, 0)], [f"`{RED}`"]),
    "数えない: 情報文字列つきの印では閉じない": ({"p/a.md": plan(IR, extra=f"\n````markdown\n````python\n- 読んだ成果物: `{RED}`\n````\n")}, ["@p"], 0,
                                          [row(IR, 1, 0, 0)], [f"`{RED}`", "形に合わない"]),
    "数えない: 閉じないコードブロック": ({"p/a.md": plan(IR, extra=f"\n```text\n- 読んだ成果物: `{RED}`\n")}, ["@p"], 1,
                                  ["a.md: 7 行目: 閉じないコードブロックがある", row(IR, 1, 0, 0)], [f"`{RED}`"]),
    "数えない: UTF-8 でない計画ファイル": ({"p/a.md": plan(IR), "p/b.md": b"\xff\xfe\x00"}, ["@p"], 2, ["読めない計画ファイル"], ["Traceback", "| `"]),
    "数える: 関門の記録の別の書き方（~~~・コロンの後の空白なし・当て直し）": (
        {"p/a.md": plan(IR, count=1, extra="\n~~~dev-loop-gates\n周の base: abcdef1\n関門:Verifier 1 abcdef1 反証=5\n関門: /code-review 1 abcdef1 指摘=2\n"
                                         "関門: 当て直し abcdef1 abcdef2 反証=4\n# 前の記録の 反証=100\n~~~\n")}, ["@p"], 0, [row(IR, 1, 1, 11), "関門の記録が無い周: 0"], []),
    "数えない: 関門の記録が 2 つ": ({"p/a.md": plan(IR, gates=[1], extra="\n```dev-loop-gates\n関門: Verifier 1 abcdef1 反証=1\n```\n")}, ["@p"], 1,
                               ["関門の記録が読めない", "関門の記録が無い周: 1"], []),
    "数える: 最初の起票の行だけ": ({"p/a.md": plan(IR, count=2, extra="\n- この周の起票: 9 件\n")}, ["@p"], 0, [row(IR, 1, 9, 0)], []),
    "数える: 全角の数字の関門の行": ({"p/a.md": plan(IR, extra="\n```dev-loop-gates\n関門: Verifier 1 abcdef1 反証=１２\n```\n")}, ["@p"], 0, [row(IR, 1, 0, 12)], ["Traceback"]),
    "数えない: 関門の記録の読めない行": ({"p/a.md": plan(IR, extra="\n```dev-loop-gates\n関門: Verifier 1 abcdef1 反証 = 7\n関門: Verifier 2 abcdef1 反証=3\n```\n")}, ["@p"], 1,
                                   ["関門の記録が読めない（読めない行: 関門: Verifier 1 abcdef1 反証 = 7）", "関門の記録が無い周: 1"], []),
    "数えない: コロンの無いラベル・括弧つきのラベル": ({"p/a.md": plan(IR, f"- 読んだ成果物 `{RED}`", f"- 読んだ成果物（手順 2）: `{RED}`", f"- 読んだ成果物=`{RED}`")}, ["@p"], 1,
                                           ["形に合わない行（数えていない）: 3", "a.md: 6 行目", "a.md: 7 行目", "a.md: 8 行目"], [f"`{RED}` |"]),
    "数えない: コロンもバッククォートも無いラベル（R1）": ({"p/a.md": plan(IR, "- 読んだ成果物 a.md", f"- 読んだ成果物  {RED}（手順 2）")}, ["@p"], 1,
                                              ["形に合わない行（数えていない）: 2", "a.md: 6 行目", "a.md: 7 行目", row(IR, 1, 0, 0)], [f"`{RED}` |", "`a.md` |"]),
    "数えない: 空白の後が散文なら形の誤りでない": ({"p/a.md": plan(IR, extra="- 読んだ成果物 は spec-gap.md にある\n- 読んだ成果物 ... とは\n## 読んだ成果物 の書き方\n")}, ["@p"], 0,
                                         [row(IR, 1, 0, 0)], ["形に合わない"]),
    "数えない: 空白の後のなしとパスのような語（R3）": ({"p/a.md": plan(IR, "- 読んだ成果物 なし", "- 読んだ成果物 spec_ir")}, ["@p"], 1,
                                              ["形に合わない行（数えていない）: 2", "a.md: 6 行目", "a.md: 7 行目", row(IR, 1, 0, 0)], ["`spec_ir` |", "うち `なし`: 1"]),
    "数えない: 空白の後の略語・数・版は形の誤りでない（R4）": ({"p/a.md": plan(IR, extra="- 読んだ成果物 e.g. これ\n- 読んだ成果物 1.5 倍\n- 読んだ成果物 v2.0\n"
                                                                    "- 読んだ成果物 v2.0の版\n- 読んだ成果物 なしで進めた\n- 読んだ成果物 1/2 を読んだ\n")}, ["@p"], 0,
                                                  [row(IR, 1, 0, 0)], ["形に合わない"]),
    "数える: パスの前後の空白": ({"p/a.md": plan(f"- 読んだ成果物: `{IR} `"), "p/b.md": plan(IR)}, ["@p"], 0, [row(IR, 2, 0, 0)], [f"`{IR} `"]),
    "数える: リストの中のコードブロック": ({"p/a.md": plan(IR, extra=f"- 例:\n\n  ```text\n- 読んだ成果物: `{RED}`\n  ```\n")}, ["@p"], 0, [row(IR, 1, 0, 0)], [f"`{RED}`", "形に合わない"]),
    "数えない: 読めないディレクトリ": ({"p/a.md": plan(IR), "p/LOCKED/b.md": plan(RED)}, ["@p"], 2, ["読めないディレクトリ"], ["| `"]),
    "数えない: UTF-8 でない --all-artifacts": ({"p/a.md": plan(IR), "all.txt": b"\xff\xfe"}, ["@p", "--all-artifacts", "@all.txt"], 2, ["読めない"], ["Traceback", "| `"]),
    "数えない: check-gates.py に名前が足りない": ({"p/a.md": plan(IR), "DROP:closes": ""}, ["@p"], 2, ["check-gates.py を読み込めない", "closes が無い"], ["Traceback", "| `"]),
    "数える: 挙げたパスの重なりは 1 つ": ({"p/a.md": plan(IR), "all.txt": f"{REF}\n./{REF}\n"}, ["@p", "--all-artifacts", "@all.txt"], 0,
                                    [row(REF, 0, 0, 0), "一度も読まれない成果物: 1"], []),
}

# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("読み込みで __pycache__ を書く", "    sys.dont_write_bytecode = True  # 読むだけ——読み込みで __pycache__ を書かない\n", "", "数える: 多い順に並べる"),
    ("./ を外さない", '    while path.startswith("./"):\n', '    while False:\n', "数える: 同じ周の同じパスは 1 件"),
    ("同じ周の同じパスを 2 度数える", "                if p not in reads:\n", "                if True:\n", "数える: 同じ周の同じパスは 1 件"),
    ("注記を許さない", r'(?P<rest>$|[\s（][^`]*$)', r'(?P<rest>$)', "数える: 注記つきの行"),
    ("注記の中のバッククォートを許す", r'(?P<rest>$|[\s（][^`]*$)', r'(?P<rest>$|[\s（].*$)', "数えない: 1 行に 2 つのパス"),
    ("コードブロックを読み飛ばさない", "            if m:\n                fence, opened = m.group(1), no\n                continue\n", "            if False:\n                pass\n", "数える: コードブロックの中の行は数えない"),
    ("印の長さを 3 で切る", "                fence, opened = m.group(1), no\n", "                fence, opened = m.group(1)[:3], no\n", "数えない: 4 つのバッククォートの中の 3 つのブロック"),
    ("閉じる印の後ろの文字を見ない", "            if gates.closes(line, fence):\n", "            if line.strip().startswith(fence):\n", "数えない: 情報文字列つきの印では閉じない"),
    ("閉じないコードブロックを名指ししない", '        bad.append(f"{opened} 行目: 閉じないコードブロックがある（その後ろを読んでいない）")\n', "        pass\n", "数えない: 閉じないコードブロック"),
    ("コメントの行も数える", '        if not t or t.startswith("#"):\n            continue\n', '        if not t:\n            continue\n', "数える: 関門の記録の別の書き方（~~~・コロンの後の空白なし・当て直し）"),
    ("読めない関門の行を飛ばす", '            return None, f"関門の記録が読めない（読めない行: {t}）"\n', "            continue\n", "数えない: 関門の記録の読めない行"),
    ("当て直しを数えない", '        for k in ("pass", "narrow", "redo"):\n            if forms[k]:', '        for k in ("pass", "narrow"):\n            if forms[k]:', "数える: 関門の記録の別の書き方（~~~・コロンの後の空白なし・当て直し）"),
    ("関門の指摘を数えない", "                total += int(forms[k].groups()[-1])\n", "                total += 0\n", "数える: 周の結果と並べる（陽性対照）"),
    ("関門の記録の有無を印で見ない", "    if not has_gate_block(text, gates):\n        return None, None\n", "", "数える: 記録の無い周は数えない"),
    ("ほかのブロックの中の例も記録と見る", "            m = gates.FENCE_ANY.match(line)\n            if m:\n                fence = m.group(1)\n        elif", "            m = None\n            if m:\n                fence = m.group(1)\n        elif", "数える: ほかのブロックの中の関門の記録の例は記録でない"),
    ("読めない関門の記録を名指ししない", "    if why:\n        bad.append(why)\n", "", "数えない: 関門の記録が 2 つ"),
    ("起票を数えない", "            counts[p] += info[\"count\"] or 0\n", "", "数える: 周の結果と並べる（陽性対照）"),
    ("最後の起票の行を使う", "        if c and count is None:\n", "        if c:\n", "数える: 最初の起票の行だけ"),
    ("2 本目以降の計画を数えない", "    for plan in plans:\n        try:", "    for plan in plans[:1]:\n        try:", "数える: 周の結果と並べる（陽性対照）"),
    ("ディレクトリを再帰しない", 'for f in files if f.endswith(".md"))', 'for f in files if f.endswith(".md") and Path(d) == root)', "数える: ディレクトリを再帰する"),
    ("同じファイルを 2 度数える", "        if p.resolve() not in resolved:\n", "        if True:\n", "数える: 同じファイルを 2 度渡しても 1 本"),
    ("多い順に並べない", "key=lambda n: (-cycles[n], n)", "key=lambda n: n", "数える: 多い順に並べる"),
    ("記録の無い周も数える", "        if not info[\"reads\"] and not info[\"none\"]:\n            continue\n", "", "数える: 記録の無い周は数えない"),
    ("なしの周を数えない", "            nones += 1\n", "            pass\n", "数える: なしの周"),
    ("起票の行が無い周を数えない", "            no_count += 1\n", "            pass\n", "数える: 起票の行・関門の記録の無い周"),
    ("関門の記録が無い周を数えない", "            no_gates += 1\n", "            pass\n", "数える: 起票の行・関門の記録の無い周"),
    ("一度も読まれない成果物を出さない", "            names.append(p)\n", "            pass\n", "数える: 一度も読まれない成果物"),
    ("挙げたパスを 2 度数える", ' and normalize(s) not in expected:\n', ':\n', "数える: 挙げたパスの重なりは 1 つ"),
    ("形に合わない行を名指ししない", '            bad.append(f"{no} 行目")\n', "            pass\n", "数えない: 太字の行"),
    ("飾りを外さない", "        m = gates.DECOR.match(t)\n", "        m = None\n", "数えない: 番号・チェックボックス・見出し・バッククォートの見出し"),
    ("バッククォートの見出しを見ない", r'LABEL = re.compile(r"^`?読んだ成果物', r'LABEL = re.compile(r"^読んだ成果物', "数えない: 番号・チェックボックス・見出し・バッククォートの見出し"),
    ("コロンでしか形の誤りと見ない", "    return bool(after) and after[0] in STARTS\n", '    return after[:1] in (":", "：")\n', "数えない: コロンの無いラベル・括弧つきのラベル"),
    ("散文も形の誤りと見る", "    return bool(after) and after[0] in STARTS\n", "    return bool(after)\n", "数えない: 散文の言及は形の誤りでない"),
    ("空白とパスのような語のラベルを形の誤りと見ない", '    if s and (s.group("none") or is_pathlike(s.group("word"))):\n', '    if s and s.group("none"):\n', "数えない: コロンもバッククォートも無いラベル（R1）"),
    ("空白の後のなしを形の誤りと見ない（R3）", r'(?P<none>なし)(?=$|[\s（(])', r'(?P<none>(?!))', "数えない: 空白の後のなしとパスのような語（R3）"),
    ("英字だけの語をパスと見ない（R3）", r'(?P<word>[A-Za-z0-9_./~+-]+)', r'(?P<word>[A-Za-z0-9./~+-]*[./][A-Za-z0-9_./~+-]*)', "数えない: 空白の後のなしとパスのような語（R3）"),
    ("なしの後ろを見ない", r'(?P<none>なし)(?=$|[\s（(])', r'(?P<none>なし)', "数えない: 空白の後の略語・数・版は形の誤りでない（R4）"),
    ("空白の後を何でも形の誤りと見る（R4）", '    return bool(re.search(r"[A-Za-z]", word)) and not PROSE_WORD.fullmatch(word)\n', "    return True\n", "数えない: 空白の後の略語・数・版は形の誤りでない（R4）"),
    ("英字の無い語もパスと見る", 'bool(re.search(r"[A-Za-z]", word)) and ', "", "数えない: 空白の後の略語・数・版は形の誤りでない（R4）"),
    ("数・版もパスと見る（R4）", r'PROSE_WORD = re.compile(r"v?[0-9]+(?:\.[0-9]+)*|.*\.")', r'PROSE_WORD = re.compile(r".*\.")', "数えない: 空白の後の略語・数・版は形の誤りでない（R4）"),
    ("略語もパスと見る（R4）", r'PROSE_WORD = re.compile(r"v?[0-9]+(?:\.[0-9]+)*|.*\.")', r'PROSE_WORD = re.compile(r"v?[0-9]+(?:\.[0-9]+)*")', "数えない: 空白の後の略語・数・版は形の誤りでない（R4）"),
    ("語の頭だけで散文と見る", "not PROSE_WORD.fullmatch(word)", "not PROSE_WORD.match(word)", "数えない: コロンもバッククォートも無いラベル（R1）"),
    ("ASCII の外の文字も語に入れる", r'(?P<word>[A-Za-z0-9_./~+-]+)', r'(?P<word>\S+)', "数えない: 空白の後の略語・数・版は形の誤りでない（R4）"),
    ("空白の後の語を見ずに次の語のパスで見る", r'\s+(?:(?P<none>', r'.*?\s+(?:(?P<none>', "数えない: 空白の後が散文なら形の誤りでない"),
    ("パスの空白を外さない", "    path = path.strip()\n", "", "数える: パスの前後の空白"),
    ("字下げしたコードブロックを見ない", "            m = gates.FENCE_ANY.match(line.strip())", "            m = gates.FENCE_ANY.match(line)", "数える: リストの中のコードブロック"),
    ("読めないディレクトリを飛ばす", "    if errors:\n", "    if False:\n", "数えない: 読めないディレクトリ"),
    ("足りない名前を見ない", "    if missing:\n", "    if False:\n", "数えない: check-gates.py に名前が足りない"),
    ("なしとパスの混在を見ない", "    if none and reads:\n", "    if False:\n", "数えない: なしとパスの混在"),
    ("読めない --all-artifacts（UTF-8 でない）で落ちる", "            except (OSError, UnicodeDecodeError) as e:\n                print(f\"--all-artifacts", "            except OSError as e:\n                print(f\"--all-artifacts", "数えない: UTF-8 でない --all-artifacts"),
    ("形に合わない行で 0", "        return 1\n    return 0\n", "        return 0\n    return 0\n", "数えない: バッククォートの無いパス"),
    ("無いパスを読み飛ばす", "（数えていない）\", file=sys.stderr)\n            return None\n", "（数えていない）\", file=sys.stderr)\n            continue\n", "数えない: 無いパス"),
    ("読めない計画ファイルで落ちる", "        except (OSError, UnicodeDecodeError) as e:\n            print(f\"読めない計画", "        except OSError as e:\n            print(f\"読めない計画", "数えない: UTF-8 でない計画ファイル"),
    ("計画ファイルが無くても 0", "    if not plans:\n", "    if False:\n", "数えない: 計画ファイルが無い"),
    ("引数なしで 0", "    if not rest:\n", "    if False:\n", "数えない: 引数なし"),
    ("未知の引数を通す", '        if a.startswith("-"):\n', '        if False:\n', "数えない: 未知の引数"),
    ("読めない --all-artifacts で 0", "                return 2\n            for line", "                text = \"\"\n            for line", "数えない: 読めない --all-artifacts"),
    ("書き込む（読むだけの陽性対照）", "    plans = collect(rest)\n", "    plans = collect(rest)\n    Path(rest[0], 'written.out').write_text('x') if Path(rest[0]).is_dir() else None\n", "数える: 多い順に並べる"),
    ("スクリプトの隣に書き込む（読むだけの陽性対照）", "    plans = collect(rest)\n", "    plans = collect(rest)\n    (Path(__file__).parent / 'written.out').write_text('x')\n", "数える: 多い順に並べる"),
]


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name}{(': ' + detail) if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    tmp = Path(tempfile.gettempdir()).resolve()
    check(f"試料が一時ディレクトリの中: {path}", tmp in path.resolve().parents)


def snapshot(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        h.update(str(p.relative_to(root)).encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def run_one(script: Path, work: Path, case: tuple) -> tuple[int, str, bool]:
    files, args, _, _, _ = case
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    assert_in_tmp(work)
    locked = []
    for rel, body in files.items():
        if body is None:
            continue
        if rel.startswith("DROP:"):
            gates = script.parent / "check-gates.py"
            text = gates.read_text(encoding="utf-8")
            name = rel.split(":", 1)[1]
            gates.write_text(text.replace(f"def {name}(", f"def {name}_renamed("), encoding="utf-8")
            continue
        if "/LOCKED/" in rel:
            locked.append(work / rel.split("/LOCKED/")[0] / "LOCKED")
        p = work / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            p.write_bytes(body)
        else:
            p.write_text(body, encoding="utf-8")
    argv = [str(work / a[1:]) if a.startswith("@") else a for a in args]
    before = (snapshot(work), snapshot(script.parent))
    for d in locked:
        d.chmod(0)
    try:
        proc = subprocess.run([sys.executable, "-I", str(script), *argv], capture_output=True, text=True, cwd=work)
    finally:
        for d in locked:
            d.chmod(0o755)
    if any(r.startswith("DROP:") for r in files):
        shutil.copy2(SCRIPTS / "check-gates.py", script.parent / "check-gates.py")
        return proc.returncode, proc.stdout + proc.stderr, True
    return proc.returncode, proc.stdout + proc.stderr, (snapshot(work), snapshot(script.parent)) == before


def as_expected(case: tuple, result: tuple[int, str, bool]) -> bool:
    return result[0] == case[2] and all(w in result[1] for w in case[3]) and not any(w in result[1] for w in case[4]) and result[2]


def reference_problems(spec_gap: str, line_re: re.Pattern) -> list[str]:
    problems = []
    section = spec_gap.split("### 読んだ成果物を記録する（#1157）", 1)
    if len(section) != 2:
        return ["spec-gap.md に「読んだ成果物を記録する（#1157）」の節が無い"]
    body = section[1].split("\n## ", 1)[0]
    if "`scripts/artifact-reads.py`" not in body:
        problems.append("spec-gap.md の節が本体を指さない")
    examples = [ln.strip() for ln in body.splitlines() if "読んだ成果物" in ln and ln.strip().startswith("- ")]
    if len(examples) < 2:
        problems.append("spec-gap.md の節に例の行が 2 つ以上無い")
    for ex in examples:
        if not line_re.match(ex):
            problems.append(f"spec-gap.md の例の行が本体の形に当たらない: {ex}")
    if not any(line_re.match(ex) and line_re.match(ex).group("none") for ex in examples):
        problems.append("spec-gap.md の節に `なし` の例が無い")
    return problems


def main() -> int:
    source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="artifact-reads-test-") as tmp:
        root = Path(tmp)
        scripts = root / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        print("試料")
        for i, (name, case) in enumerate(CASES.items()):
            result = run_one(scripts / TARGET, root / f"c{i}", case)
            check(f"試料: {name}", as_expected(case, result), f"期待 {case[2]}・{case[3]!r} / 実際 {result[0]}・変わらない={result[2]}・{result[1][-600:]!r}")
        print(f"  {len(CASES)} 件 OK")

        print("原本との突き合わせ")
        spec = importlib.util.spec_from_file_location("artifact_reads", scripts / TARGET)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        spec_gap = SPEC_GAP.read_text(encoding="utf-8")
        problems = reference_problems(spec_gap, mod.LINE)
        check("spec-gap.md と本体が一致する", not problems, "; ".join(problems))
        broken = spec_gap.replace("- 読んだ成果物: `build/merged/spec/spec_ir.json`", "- **読んだ成果物**: `build/merged/spec/spec_ir.json`", 1)
        check("崩した spec-gap.md で突き合わせが落ちる（陽性対照）", broken != spec_gap and reference_problems(broken, mod.LINE) != [])
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
            check(f"変異を殺す（期待から外れる）: {name} ← {killer}", not as_expected(case, result), f"{result[0]} {result[1][-300:]!r}")
        print(f"  変異 {len(MUTATIONS)} 件 OK")
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
