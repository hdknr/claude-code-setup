#!/usr/bin/env python3
"""`rework-metrics.py --record` が spec-loop を回す PC の中に貯めた記録を読み、案件をまたいで分析する（#989）。

usage: python3 rework-report.py [--log <記録のファイル>]

記録のファイルの既定と 1 行の形は `rework-metrics.py` の `record_path`・`RECORD_KEYS` を読み込む（写さない）——
環境変数 `SPEC_LOOP_REWORK_LOG` があればそのパス、無ければ `~/.claude/spec-loop/rework-metrics.jsonl`。

出すのは 3 つである:

1. **案件 × 時点の表**——案件の名前の順、案件の中は記録の時点（コミットの日付）の順（同じ日付ならファイルの順）。
2. **時点どうしの差**——同じ案件の、上の順で隣り合う 2 つの記録の差（後 − 前）。`rework-metrics.py` の数は `--ref` までの累計なので、
   リリースのタグごとに記録しておけば、この差が版ごとの増分になる。記録が 1 つしか無い案件は出ない。
3. **合計と率**——案件ごとに**いちばん後の時点の記録だけ**を足す（累計なので、同じ案件の記録を全部足すと二重に数える）。率は
   - 回答が変わった率 = 変わった ÷ 確かめた（Q&A の仮回答のうち、確かめた分）
   - 確認の Issue で値を変えた率 = 変えた ÷（推奨のまま ＋ 変えた）（結果なし・形に反するものは分母に入れない）
   - 変わった 1 件あたりの差分の行 = 差分の行 ÷ 変わった件（Q&A と確認の Issue を合わせた数）

   分母が 0 なら割らずに `-` を出す。

**このスクリプトは記録のファイルを読むだけで、何も書かない。** `gh`・`git` も呼ばない。CI からは呼ばない——入力が利用者の PC にある。

## 終了コード

- 0: 出した（記録が 0 行の空のファイルなら「記録 0 件」と出して 0）
- 1: 読めない行がある——読めた行で出し、読めない行（JSON として読めない・鍵が足りない・値の型が違う）を標準エラーに名指しする（黙って捨てない）
- 2: 出していない——記録のファイルが無い（まだ 1 度も `--record` していないか、パスが違う）・読めない（権限・文字コード）・引数の誤り

対象リポジトリで単体で動くよう、**標準ライブラリだけ**を使う（同じ `scripts/` の `rework-metrics.py` を読み込む）。

## 守らないもの

| 守らないもの | なぜ |
| --- | --- |
| **記録の数が正しいこと** | 数えるのは `rework-metrics.py`——ここは記録を並べて引き算・割り算するだけ |
| **時点の順が版の順であること** | コミットの日付で並べる。日付の同じ 2 つの記録はファイルの順（記録した順）で、版の順とは限らない |
| **数えきれないものがあった記録の扱い** | 記録の `uncounted` を表に出すだけで、合計から外さない |
| **案件の名前の揺れ** | 名前が違えば別の案件と読む（`--case` で揃えるのは記録する側） |
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


metrics = _load("rework_metrics", "rework-metrics.py")

# 表に出す列（記録の鍵, 見出し）
COLUMNS = (
    ("provisional", "仮回答"), ("confirmed", "確かめた"), ("changed", "変わった"),
    ("decisions", "確認の Issue"), ("decision_changed", "変えた"),
    ("rework_items", "変わった件"), ("rework_issues", "作り直しの Issue"), ("rework_prs", "PR"), ("rework_lines", "差分の行"),
)


def rate(num: int, den: int) -> str:
    return "-" if den == 0 else f"{100 * num / den:.0f}%（{num}/{den}）"


def per(num: int, den: int) -> str:
    return "-" if den == 0 else f"{num / den:.1f}"


def signed(n: int) -> str:
    return f"+{n}" if n > 0 else str(n)


def when(rec: dict) -> str:
    return f"{rec['ref']}（{rec['date']}・{rec['commit'][:7]}）"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--log", default="")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    path = Path(args.log) if args.log else metrics.record_path()
    try:
        if not path.is_file():
            print(f"{path}: 記録のファイルが無い（まだ 1 度も rework-metrics.py --record していないか、パスが違う）。出していない", file=sys.stderr)
            return 2
        _, records, bad = metrics.read_records(path)
    except (metrics.Bad, OSError) as exc:
        print(f"{exc}。出していない", file=sys.stderr)
        return 2

    by_case: dict[str, list[dict]] = {}
    for rec in records:
        by_case.setdefault(rec["case"], []).append(rec)
    for recs in by_case.values():
        recs.sort(key=lambda r: r["date"])  # 安定な並べ替え——同じ日付ならファイルの順

    out = [f"## 記録（{path}・{len(records)} 件・案件 {len(by_case)} 件）"]
    head = ["案件", "時点"] + [title for _, title in COLUMNS] + ["数えきれない"]
    if records:
        out.append("")
        out.append("| " + " | ".join(head) + " |")
        out.append("|" + " --- |" * len(head))
        for case in sorted(by_case):
            for rec in by_case[case]:
                out.append("| " + " | ".join([case, when(rec)] + [str(rec[k]) for k, _ in COLUMNS] + [str(rec["uncounted"])]) + " |")

    out.append("")
    out.append("## 時点どうしの差（同じ案件の、隣り合う時点の後 − 前）")
    pairs = [(case, a, b) for case in sorted(by_case) for a, b in zip(by_case[case], by_case[case][1:])]
    if pairs:
        head = ["案件", "区間"] + [title for _, title in COLUMNS]
        out.append("")
        out.append("| " + " | ".join(head) + " |")
        out.append("|" + " --- |" * len(head))
        for case, a, b in pairs:
            out.append("| " + " | ".join([case, f"{when(a)} → {when(b)}"] + [signed(b[k] - a[k]) for k, _ in COLUMNS]) + " |")
    else:
        out.append("- 時点が 2 つ以上ある案件が無い")

    latest = [by_case[case][-1] for case in sorted(by_case)]
    total = {k: sum(r[k] for r in latest) for k in metrics.RECORD_COUNTS}
    out.append("")
    out.append(f"## 合計（案件ごとにいちばん後の時点の記録を足す・{len(latest)} 案件）")
    out.append(f"- 仮回答 {total['provisional']} 件・確かめた {total['confirmed']} 件・回答が変わった {total['changed']} 件"
               f"——回答が変わった率 {rate(total['changed'], total['confirmed'])}")
    out.append(f"- 確認の Issue {total['decisions']} 件・推奨のまま {total['kept']} 件・変えた {total['decision_changed']} 件"
               f"——値を変えた率 {rate(total['decision_changed'], total['kept'] + total['decision_changed'])}")
    out.append(f"- 変わった件 {total['rework_items']} 件・作り直しの元の印の Issue {total['rework_issues']} 件・PR {total['rework_prs']} 件・"
               f"差分 {total['rework_lines']} 行——変わった 1 件あたりの差分の行 {per(total['rework_lines'], total['rework_items'])}")
    out.append(f"- 数えきれないものがあった記録: {sum(1 for r in latest if r['uncounted'])} 件")

    for line in out:
        print(line)
    for line in bad:
        print(f"読めない行——{line}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「出していない」（2）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。出していない", file=sys.stderr)
        sys.exit(2)
