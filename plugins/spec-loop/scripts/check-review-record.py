#!/usr/bin/env python3
"""仕様レビューの記録（`spec-review/v<n>.csv` と `spec-review/v<n>-findings.csv`）から、抜ける条件 2・3 と実行の上限（#1044）と、
条件 5 のうち内部の Q&A 表の行の確かめ（#1155）を数え直す。

usage:
    python3 check-review-record.py conditions <spec-review/v<n>-findings.csv> [--run <回>]
    python3 check-review-record.py internal <spec-review/v<n>-findings.csv> --docs <正本の docs> [--run <回>]
    python3 check-review-record.py limit <spec-review/v<n>.csv> [--limit <N>]

**決まりの正は `references/spec-exit.md` の「指摘の重さ」と「実行の上限と記録」である**（このプラグインの中にある）。
指摘の表の列と値・実行の記録の読み方は同梱の `check-findings-csv.py` のもの（読み込んで使う——写さない）。
`scaffold.py` は記録の表の最後の実行の行をここの `last_run` で読む（写さない）。
`internal` の版の差分は同梱の `diff-versions.py` の `compare`、重ねた全体は `merge-versions.py` の `merge`、内部の層の番号は `check-qa-csv.py` の
`is_internal_number` で決める（読み込んで使う——写さない）。**内部の行の印（`（内部の行: <No>）`）は spec-exit.md の「指摘の表」の写しで、
このリポジトリの `scripts/test-check-review-record.py` が突き合わせる。**

## なぜ在るのか（#1044）

抜ける条件 2・3 は Red Team（モデル）の判定がそのまま条件になり、上限もモデルが記録の表を読んで数えていた。
**記録は機械で読める表なので、数え直せる分は機械で数え直す**——判定役の書き写しと食い違ったら、厳しいほうを取る（spec-review の手順 6）。

## `conditions` — 条件 2・3（と狭いパスの効く重さ）を数え直す

指摘の表を同梱の `check-findings-csv.py` の検査に当て（違反があれば判定していない——2）、`--run` の回（省けば、実行の記録の最後の実行の行）の行を見る:

- **最後のレビュー**: その回に `2回目` の行があるか、`1回目` の行に振り分けが `仕様を直す`・`範囲の外として記録する`・`内部の Q&A 表に記録する` の行があれば 2 回目
  （spec-review の手順 5 が 2 回目を回す条件——内部の Q&A 表に記録した行は、その回に決めて仕様に反映すれば 2 回目が回り、反映していなければ条件 1 が止める。
  2 回目の行が 0 件なら、2 回目は指摘なし）。そうでなければ 1 回目。
- **数える行**: 最後のレビューの `red-team` の行と、`狭いパス` の行（役を問わない——spec-exit.md の「2 回目のあとの直し」の 3 つ目）のうち、
  **重さが `判断が要る`・`結果が割れる`** で、**振り分けが `退ける` でない**もの（退けた指摘は誤り。`確かめられない` の行は判定役の重さのまま数える）。
  **2 回目の `仕様を直す` の行で `結果` が `次の回` でないもの（その回の 2 回目のあとで直した）は数えない**（重さが `判断が要る` の行は除く——解消済みにはならない）——spec-exit.md の「2 回目の `満たさない` を
  解消済みに置き換えてよい」の道で、直しは狭いパスが確かめる（2 パス目の CR2-1）。
- **確かめの行は 2 回目を回したことに数えない**（#1155）——`domain-checker` の行で、振り分けが `内部の Q&A 表に記録する`、`指摘` に内部の行の印
  （`（内部の行: <No>）`。コロンは全角でもよい）がある行は、Domain Checker が内部の表の行を確かめて内部のまま置いた記録で、仕様を直していない
  （spec-review の手順 5 は 2 回目を回さない）。数えると、2 回目の行が 0 件の回に 1 回目の Red Team の効く重さを数え落とす。
  **印を引いただけのほかの行**（Red Team の直し・書き手が仕様に移した行）は今までどおり数える。
- 1 件でもあれば `満たさない`（1）。数えた行を全部出す。

## `internal` — 条件 5 のうち、内部の Q&A 表の行を判定役が確かめたか（#1155）

指摘の表を `conditions` と同じく検査に当て、`--run` の回（省けば最後の実行の行）を見る。版は指摘の表の名前（`v<n>-findings.csv`）の `<n>`:

- **確かめる行**: その版で足した・変えた内部の層の行（`diff-versions.py` の `Q&A（内部）` の `追加`・`変更`。v1 は全部が追加）。
  **前の版から変わらない行は求めない**——その版の spec-review が確かめている（spec-exit.md の条件 5）。
- **確かめた行**: その回の `domain-checker` の行で、`確かめたか` が `確かめた`、`指摘` に印 `（内部の行: <No>）` があるもの（どのレビューでもよい）。
- 確かめる行のうち、確かめた行の無いものが 1 つでもあれば `満たさない`（1）。
- **確かめた行の振り分けが `共有の Q&A 表に起票する` なのに、その番号が重ねた全体の内部の表に残っていれば `満たさない`（1）**——
  利用者に見える結果が変わると決めた判断を、内部の表に置いたまま抜けない（移し方は `references/qa-csv.md` の「層を移す」）。
- 確かめる行が 0 件なら 0（その旨を出す）。
- **判定を読めない行の名指し（#1248）**: 確かめた行を書き手が `実装に渡す`・`範囲の外として記録する` に振ると、重さは `-`（`check-findings-csv.py` の決まり）で判定が読めず、割れも見えない。
  そういう行を `読めない: <No> …` と名指しする（終了コードは変えない。内部の行はその 2 区分に振らない決まり——spec-exit.md）。
- **割れた行の名指し（#1248）**: 同じ回の中で、同じ内部の行の確かめた行の判定が段（`1回目`・`2回目`・`狭いパス`）ごとに食い違ったら、`割れた: <No> …` を出力に足す。
  判定は `重さ` で読む（`補い`＝変わらない・`判断が要る`／`結果が割れる`＝変わる。書き手が判定を退けても重さを書き換えない決まり——spec-exit.md）。**終了コードには数えない**——
  割れたのが、書き手が段の間で行を直したからか、判定役の判断のぶれか、照合先の不足（事実を確かめられなかった）かは、表からは分からない。
  数えると、正当な直しの後の判定替えも止める。割れた行をどう扱うか（退けるなら、どの段の判定をどの根拠で退けたかを `結果` に書く）は
  `references/spec-exit.md` の「内部の表の行を確かめる」。

## `limit` — 実行の上限を数える

**数え始め**は `判断` が `続ける` か `範囲を決め直す` の最後の `利用者の判断` の行の後（無ければ表の最初）。そこから後の実行の行
（`結果` が `抜けた`／`抜けていない`）で、`条件2〜4` が `満たさない` か `判定できなかった` の行を数え、**N 行（既定 3）以上なら上限（3）**。
**最後の `利用者の判断` の行が `止める` なら、数えずに上限（3）**。表が無ければ実行 0 回（0）。数えた行の `機能` も出す（すべて `-` ならそう言う）。
N は正本の `CLAUDE.md` で変えてよい（spec-exit.md）——このスクリプトは `CLAUDE.md` を読まず、spec-review が `--limit` で渡す。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | `conditions`: 数える行が 0 件（条件 2・3 と狭いパスの効く重さを満たす）／`internal`: 確かめる行がすべて確かめてあり、移すと決めた行が内部の表に残らない／`limit`: 上限に達していない |
| 1 | `conditions`: 数える行がある（満たさない）／`internal`: 確かめていない行か、移していない行がある（満たさない） |
| 2 | 判定していない——引数の誤り・ファイルが読めない・指摘の表が `check-findings-csv.py` の検査に通らない・実行の行が無い・`--run` の回が実行の行でない・記録の見出しに要る列が無い・`internal`: `--docs` が無い・正本の版が無い／読めない／重ね合わせが決まりに反する・想定外の例外 |
| 3 | `limit`: 上限に達した（か、最後の利用者の判断が `止める`）——判定役を起動せずに利用者に訊く |

## 何を守り、何を守らないか

守る:

| 守ること | 破る形 |
| --- | --- |
| 最後のレビューの Red Team の効く重さの行が 1 行でもあれば 1 | 判定役が `満たす` と書いた回を、表のとおり満たさないと言えない（Issue の受入基準 1） |
| 狭いパスの効く重さの行は役を問わず数える | 狭いパスの新しい指摘が残ったまま抜けたと読む |
| 1 回目に直した行があれば、最後のレビューは 2 回目と読む | 2 回目で消えた 1 回目の指摘を数えて、抜けた回を満たさないと言う |
| `退ける` の行・`補い` の行・重さが `-` の行は数えない | 誤りと分かった指摘・条件に効かない指摘で止める |
| 指摘の表が検査に通らない・読めないなら 2 | 壊れた表を「行が無い」と読んで 0 にする |
| 実行の行が無い・`--run` が実行の行でないなら 2 | 数える回が決まらないのに 0 にする |
| 記録の表に列の足りない行があれば 2 | その実行の行を数え落として、上限に達したのに 0 にする |
| 数え始めは `続ける`・`範囲を決め直す` の最後の行の後 | 利用者が数え直しを選んだのに、前の行を数え続ける |
| 最後の利用者の判断が `止める` なら上限 | 呼び直しただけで判定役が動き出す |
| `回答待ち`・`満たす` の行は上限に数えない | 利用者の回答待ちを判定役の空回りと数える |
| 確かめの行（`domain-checker`・`内部の Q&A 表に記録する`・印）は、2 回目を回したことに数えない。印のほかの行は数える | 確かめの行だけの 1 回目を 2 回目ありと読み、1 回目の Red Team の効く重さを数え落とす／印を引いた直しを 2 回目なしと読み、直した指摘を数える（#1155） |
| 印のコロンは全角でも読む | 全角で書いた確かめの行を、確かめていない・2 回目を回したと読む |
| `internal`: その版で足した・変えた内部の行に、その回の Domain Checker の確かめた行が無ければ 1 | 書き手が判定役に渡し忘れた・判定役が見落とした内部の行が、書き手の自己判定のまま抜ける（#1155） |
| `internal`: `確かめられない` の行・ほかの判定役の行・前の回の行は確かめに数えない | 確かめていない判断を確かめたと読む |
| `internal`: 前の版から変わらない内部の行は求めない | 前の版で確かめた行を毎回確かめ直させる（H1） |
| `internal`: 移すと決めた行が内部の表に残れば 1 | 利用者に見える結果が変わる判断が、利用者に見えないまま抜ける |
| `internal`: 重ね合わせが決まりに反する・版が無いなら 2 | 比べられない版を「確かめる行が無い」と読んで 0 にする |
| `internal`: 同じ回の中で段ごとに判定（重さ）が食い違った行を `割れた:` と名指しする（終了コードは変えない） | 段ごとに逆の判定が出た行が、最後の判定だけで決まって、割れたことが誰にも見えない（#1248） |
| `internal`: 確かめた行が `実装に渡す`・`範囲の外として記録する`（重さ `-`）に振られていたら `読めない:` と名指しする | 重さが `-` の行は判定が読めず、段ごとの食い違いが見えなくなる（#1248 の F1） |
| `internal`: `確かめられない` の行・前の回の行・同じ判定の段は割れに数えない | 確かめていない行や回をまたいだ違いを、同じ回の判定の割れと読む |

守らない:

| 守らないもの | なぜ |
| --- | --- |
| **判定役が案を「範囲の外」「実装に渡す」とした行を、範囲の中に振り直した回**（spec-exit.md の条件の表の下） | 指摘の表は判定役の案を残さない。spec-review は判定役の判定と数え直しの両方が `満たす` のときだけ満たすとする |
| **狭いパスが全部の役から返ったか・元の指摘が `解消した` か**（狭いパスの 1・2 つ目） | 指摘の表に残らない。2 回目のあとで直した行は数えないので、その行が解消したかは判定役（狭いパス）の判定だけで決まる |
| **2 回目を回す前に止めた回**で、1 回目に直した行がある | 2 回目は指摘なしと読む。その回の記録は `抜けていない` なので、scaffold は止まる |
| **判定役の書いた重さが正しいか**・行を落とさずに足したか | 判断であり、表の元は会話にしか無い（`check-findings-csv.py` と同じ） |
| **条件 1・4・5** | 条件 1 は `check-spec-exit.py`、条件 4 の TLC のモデルは `check-formal-rerun.py`、条件 5 は振り分けの表——`internal` が見るのは条件 5 のうち内部の行の確かめだけ |
| **`internal`: 判定役の判定（変わる／変わらない）が正しいか**・確かめた後に行を書き換えたか | 判断であり、指摘の表は行の中身を残さない（確かめた時点の行と今の行を比べられない） |
| **`internal`: spec-review を抜けた後に、feasibility・dev-loop が内部の表に足した行** | 抜けた記録は記録の表に残り、scaffold はそれを読むだけ。足した行は次の spec-review の実行で確かめる |
| **`internal`: 書き手が `重さ` を書き換えた行**（判定役の判定と区別できない。書き換えない決まりは spec-exit.md） | 表は判定役の返した重さと書き手の直した重さを区別して残さない。割れが名指しされない（#1248） |
| **`internal`: 割れた行の判定のどちらが正しいか**・書き手が `結果` に退けた根拠を書いたか・割れた原因（行を直した・判定役のぶれ・照合先の不足） | 判断であり、表の行は中身も原因も残さない。名指しは書き手に気づかせるだけで、止めない（#1248） |
| **`internal`: 移した先の共有の表の行があるか**・指し先を直したか | 移し方は `references/qa-csv.md` の「層を移す」。共有の表の行は条件 1 が見る |
| **記録の表の `条件2〜4` の値が判定どおりか** | `limit` は書いた値を数えるだけ |

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


findings = _load("check_findings_csv", "check-findings-csv.py")
Unreadable = findings.Unreadable
diff_versions = _load("diff_versions", "diff-versions.py")
merge_versions = diff_versions.merge_versions

# ---- `references/spec-exit.md` の「指摘の重さ」「実行の上限と記録」の写し
EFFECTIVE = ("判断が要る", "結果が割れる")
REJECTED = "退ける"
# spec-review の手順 5 が 2 回目のレビューを回す振り分け（仕様を直した・範囲の文書に足した）。内部の Q&A 表に記録した行は、その回に決めて
# 仕様に反映すれば 2 回目が回る——反映していなければ内部の表に反映していない行が残り、条件 1 が止める（その回は抜けない）
SECOND_TRIGGERS = ("仕様を直す", "範囲の外として記録する", "内部の Q&A 表に記録する")
RED_TEAM = "red-team"
FIRST, SECOND, NARROW = findings.REVIEWS
PASSED = findings.RUN_RESULTS[0]  # `抜けた`（scaffold.py が読む）
COUNTED = ("満たさない", "判定できなかった")
DECISION = "利用者の判断"
RECOUNT = ("続ける", "範囲を決め直す")
STOP = "止める"
LIMIT = 3
LIMIT_COLUMNS = ("回", "結果", "条件2〜4", "判断", "機能")
# 2 回目の `仕様を直す` の行で、その回は直さなかった印（spec-exit.md の「指摘の表」の `結果`）
NEXT_RUN = "次の回"
DECIDE = EFFECTIVE[0]  # `判断が要る`——直しても解消済みにはならない
FIX = "仕様を直す"
# ---- `references/spec-exit.md` の「指摘の表」の、内部の Q&A 表の行を確かめた印（#1155）の写し
INTERNAL_MARK = re.compile(r"（内部の行\s*[:：]\s*([^）\s]+)）")  # コロンは全角でもよい（findings-by-feature.py の機能の印と同じ）
KEEP = "内部の Q&A 表に記録する"
DOMAIN_CHECKER = "domain-checker"
MOVE = "共有の Q&A 表に起票する"
SAME = "補い"  # 内部の行の判定が「変わらない」のときの重さ。「変わる」は DECIDE（`判断が要る`）——domain-checker.md の「内部の Q&A 表に置いた判断」

EXIT_OK, EXIT_UNMET, EXIT_UNJUDGED, EXIT_LIMIT = 0, 1, 2, 3


def read_runs(path: Path, columns: tuple[str, ...] = ("回", "結果")) -> list[dict[str, str]]:
    """実行の記録の全行（見出しの順）を、`columns` の列だけの辞書で返す。列が欠けた行は飛ばす。"""
    rows = findings.read_csv(path, "実行の記録")
    header = [h.strip() for h in rows[0]]
    missing = [c for c in columns if c not in header]
    if missing:
        raise Unreadable(f"実行の記録の見出しに {'・'.join(missing)} が無い: {path}")
    at = {c: header.index(c) for c in columns}
    short = [n for n, row in enumerate(rows[1:], start=2) if row and len(row) <= max(at.values())]
    if short:
        # 列の欠けた行を飛ばすと、その実行の行を数え落とす（上限が効かない）
        raise Unreadable(f"実行の記録の {'・'.join(map(str, short))} 行目の列が足りない（見出しは {len(header)} 列）: {path}")
    return [{c: row[i].strip() for c, i in at.items()} for row in rows[1:] if len(row) > max(at.values())]


def last_run(path: Path) -> dict[str, str] | None:
    """実行の記録の最後の実行の行（`結果` が `抜けた`／`抜けていない`）。無ければ None。scaffold.py が読み込む。"""
    runs = [r for r in read_runs(path) if r["結果"] in findings.RUN_RESULTS]
    return runs[-1] if runs else None


def run_cells(table: Path, run: str | None) -> tuple[str | None, list[tuple[int, dict[str, str]]], list[str]]:
    """(数える回, その回の指摘の行（行番号つき）, 判定していない理由)。理由があれば回は None。"""
    code, problems = findings.check(table)
    if code:
        return None, [], problems + [f"指摘の表が check-findings-csv.py の検査に通らない（{len(problems)} 件）。数え直していない"]
    record = findings.runs_path(table)
    runs = [r for r in read_runs(record) if r["結果"] in findings.RUN_RESULTS]
    if not runs:
        return None, [], [f"{record}: 実行の行（結果が {'／'.join(findings.RUN_RESULTS)}）が無い。数え直していない"]
    if run is None:
        run = runs[-1]["回"]
    elif run not in {r["回"] for r in runs}:
        return None, [], [f"{record}: 回 {run} は実行の行でない。数え直していない"]
    rows = findings.read_csv(table, "指摘の表")
    cells = [dict(zip(findings.COLUMNS, (v.strip() for v in r))) for r in rows[1:]]
    return run, [(number, c) for number, c in enumerate(cells, start=2) if c["回"] == run], []


def is_confirmation(c: dict[str, str]) -> bool:
    """Domain Checker が内部の行を確かめて、内部のまま置いた行か（印つき・`domain-checker`・振り分けが `内部の Q&A 表に記録する`）。
    仕様を直していないので 2 回目のレビューを回す理由にならない。印を引いただけのほかの行（Red Team の直し・書き手が仕様に移した行）は除く。"""
    return c["判定役"] == DOMAIN_CHECKER and c["振り分け"] == KEEP and internal_number(c) is not None


def internal_number(c: dict[str, str]) -> str | None:
    """`指摘` の内部の行の印が指す番号（無ければ None）。"""
    m = INTERNAL_MARK.search(c["指摘"])
    return m.group(1) if m else None


def conditions(table: Path, run: str | None) -> tuple[int, list[str]]:
    run, mine, problems = run_cells(table, run)
    if run is None:
        return EXIT_UNJUDGED, problems
    second = any(c["レビュー"] == SECOND for _, c in mine) or any(
        c["レビュー"] == FIRST and c["振り分け"] in SECOND_TRIGGERS and not is_confirmation(c) for _, c in mine)
    last = SECOND if second else FIRST
    counted = [(number, c) for number, c in mine
               if c["重さ"] in EFFECTIVE and c["振り分け"] != REJECTED
               and ((c["レビュー"] == last and c["判定役"] == RED_TEAM and not fixed_after_second(c)) or c["レビュー"] == NARROW)]
    seen = f"回 {run}・最後のレビューは {last}（その行 {sum(1 for _, c in mine if c['レビュー'] == last)} 件）"
    if not counted:
        return EXIT_OK, [f"満たす: {seen}——Red Team と狭いパスに、効く重さ（{'・'.join(EFFECTIVE)}）の行が無い"]
    lines = [f"{table}:{number}: {c['レビュー']}・{c['判定役']}・{c['重さ']}・{c['振り分け']}: {c['指摘']}" for number, c in counted]
    return EXIT_UNMET, lines + [f"満たさない: {seen}——効く重さの行が {len(counted)} 件（条件 2・3 か狭いパスの 3 つ目。references/spec-exit.md の「指摘の重さ」）"]


def internal(table: Path, docs: Path, run: str | None) -> tuple[int, list[str]]:
    run, mine, problems = run_cells(table, run)
    if run is None:
        return EXIT_UNJUDGED, problems
    version = int(findings.NAME.match(table.name).group(1))
    try:
        problems, diff = diff_versions.compare(docs, version)
        if not problems:
            problems, _, whole, _ = merge_versions.merge(docs, version)
    except merge_versions.Unreadable as e:
        return EXIT_UNJUDGED, [f"正本の版を読めない: {e}。数え直していない"]
    if problems:
        return EXIT_UNJUDGED, problems + [f"v{version} の重ね合わせが決まりに反する（{len(problems)} 件）。数え直していない"]
    targets = [c.key for c in diff.changes[diff_versions.KIND_QA_INTERNAL] if c.status != diff_versions.REMOVED]
    judged: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for number, c in mine:
        no = internal_number(c)
        if no is not None and c["判定役"] == DOMAIN_CHECKER and c["確かめたか"] == findings.CONFIRMED:
            judged.setdefault(no, []).append((number, c))
    remaining = diff_versions.qa_layers(whole)[1]
    seen = f"回 {run}・v{version} で足した・変えた内部の行 {len(targets)} 件"
    lines = [f"{no}: Domain Checker が確かめた行（印 `（内部の行: {no}）`）が回 {run} の指摘の表に無い" for no in targets if no not in judged]
    lines += [f"{table}:{number}: {no} は {MOVE} に振り分けたのに、重ねた全体の内部の表に残る（references/qa-csv.md の「層を移す」）"
              for no, rows in judged.items() if no in remaining for number, c in rows if c["振り分け"] == MOVE]
    split = split_judgments(judged)  # 名指しするだけで、終了コードには数えない（#1248）
    if lines:
        return EXIT_UNMET, lines + [f"満たさない: {seen}——確かめていない・移していない行が {len(lines)} 件（条件 5。references/spec-exit.md）"] + split
    if not targets:
        return EXIT_OK, [f"満たす: {seen}——確かめる行が無い"] + split
    return EXIT_OK, [f"満たす: {seen}——すべて Domain Checker が確かめた"] + split


def split_judgments(judged: dict[str, list[tuple[int, dict[str, str]]]]) -> list[str]:
    """同じ回の中で、同じ内部の行の判定（`補い`＝変わらない／`判断が要る`＝変わる）が段（レビュー）ごとに食い違った行を名指しする（#1248）。
    判定は `重さ` で読む——書き手が判定を退けた行も重さは判定役のまま残る（振り分けは `退ける` になる）。終了コードには数えない。"""
    unread = [f"読めない: {no} の確かめた行（{number} 行目・{c['レビュー']}）は {c['振り分け']} に振られ、重さが - で判定（変わる・変わらない）を読めない。"
              "内部の行は 内部の Q&A 表に記録する・共有の Q&A 表に起票する・退ける のどれかに振る（references/spec-exit.md の「内部の表の行を確かめる」）"
              for no, rows in sorted(judged.items()) for number, c in rows if c["振り分け"] in findings.NO_WEIGHT]
    names = {SAME: "変わらない", **{w: "変わる" for w in EFFECTIVE}}  # `結果が割れる` も「変わる」側（domain-checker.md は迷ったら重いほうと言う）
    lines = []
    for no, rows in sorted(judged.items()):
        verdicts = [(c["レビュー"], names[c["重さ"]], number) for number, c in rows if c["重さ"] in names]
        if len({v for _, v, _ in verdicts}) > 1:
            seen = "・".join(f"{review}={verdict}（{number} 行目）" for review, verdict, number in verdicts)
            lines.append(f"割れた: {no} の判定が同じ回の中で段ごとに食い違う——{seen}。終了コードには数えない。"
                         "書き手が判定を退けるなら、どの段の判定をどの根拠で退けたかを `結果` に書く（references/spec-exit.md の「内部の表の行を確かめる」）")
    return lines + unread


def fixed_after_second(c: dict[str, str]) -> bool:
    """2 回目のあとで直した行か——2 回目の `仕様を直す` で、`結果` が `次の回` でない（その回に直した）。`判断が要る` の行は除く
    （spec-exit.md の「2 回目のあとの直し」——`判断が要る` は起票して条件 1 が止めるので、解消済みにはならない。狭いパスの N1）。

    その直しは狭いパスが確かめる（解消したかは指摘の表に残らない——判定役の側の判定）。数え直しは、狭いパスの新しい効く重さの行を数える。
    """
    return c["レビュー"] == SECOND and c["振り分け"] == FIX and c["結果"] != NEXT_RUN and c["重さ"] != DECIDE


def limit(record: Path, n: int) -> tuple[int, list[str]]:
    if not record.exists():
        return EXIT_OK, [f"{record} が無い——実行 0 回。上限（{n}）まであと {n} 回"]
    rows = read_runs(record, LIMIT_COLUMNS)
    decisions = [i for i, r in enumerate(rows) if r["結果"] == DECISION]
    if decisions and rows[decisions[-1]]["判断"] == STOP:
        return EXIT_LIMIT, [f"上限: 最後の利用者の判断（回 {rows[decisions[-1]]['回']}）が `{STOP}`——数えずに利用者に訊く"]
    start = max((i for i in decisions if rows[i]["判断"] in RECOUNT), default=-1) + 1
    counted = [r for r in rows[start:] if r["結果"] in findings.RUN_RESULTS and r["条件2〜4"] in COUNTED]
    since = f"回 {rows[start]['回']} から" if start < len(rows) else "数え始めの後に行が無い"
    names = [r["機能"] for r in counted]
    features = "すべて `-`（範囲を決め直す は出さない）" if names and all(x == "-" for x in names) else "・".join(names) or "-"
    head = f"数え始め: {since}。満たさない・判定できなかった の実行の行 {len(counted)} 件（回 {'・'.join(r['回'] for r in counted) or '-'}）。機能: {features}"
    if len(counted) >= n:
        return EXIT_LIMIT, [head, f"上限: {len(counted)} 件 ≧ {n}——判定役を起動せず、続ける／範囲を決め直す／止める を利用者に訊く"]
    return EXIT_OK, [head, f"上限（{n}）まであと {n - len(counted)} 回"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="仕様レビューの記録から、抜ける条件 2・3 と実行の上限を数え直す")
    sub = parser.add_subparsers(dest="command")
    c = sub.add_parser("conditions")
    c.add_argument("table", type=Path, help="spec-review/v<n>-findings.csv")
    c.add_argument("--run", help="数える回（省けば最後の実行の行）")
    i = sub.add_parser("internal")
    i.add_argument("table", type=Path, help="spec-review/v<n>-findings.csv")
    i.add_argument("--docs", type=Path, required=True, help="正本の docs ディレクトリ（版 v1・v2…を持つ）")
    i.add_argument("--run", help="数える回（省けば最後の実行の行）")
    m = sub.add_parser("limit")
    m.add_argument("record", type=Path, help="spec-review/v<n>.csv")
    m.add_argument("--limit", default=str(LIMIT), help=f"上限の N（既定 {LIMIT}）")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_UNJUDGED
    try:
        if args.command in ("conditions", "internal"):
            if args.run is not None and not findings.NUMBER.match(args.run):
                print(f"--run は 1 からの番号: {args.run!r}", file=sys.stderr)
                return EXIT_UNJUDGED
            if args.command == "conditions":
                code, lines = conditions(args.table, args.run)
            else:
                code, lines = internal(args.table, args.docs, args.run)
        elif args.command == "limit":
            if not re.fullmatch(r"[1-9][0-9]*", args.limit):
                print(f"--limit は 1 以上の整数: {args.limit!r}", file=sys.stderr)
                return EXIT_UNJUDGED
            if not re.fullmatch(r"v[1-9][0-9]*\.csv", args.record.name):
                print(f"記録の表の名前が v<n>.csv でない: {args.record.name}", file=sys.stderr)
                return EXIT_UNJUDGED
            code, lines = limit(args.record, int(args.limit))
        else:
            parser.print_usage(sys.stderr)
            return EXIT_UNJUDGED
    except Unreadable as e:
        print(f"判定していない: {e}", file=sys.stderr)
        return EXIT_UNJUDGED
    for line in lines:
        print(line, file=sys.stderr if code == EXIT_UNJUDGED else sys.stdout)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1 に化けさせない
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
