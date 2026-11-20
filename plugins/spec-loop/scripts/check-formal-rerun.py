#!/usr/bin/env python3
"""保存した TLC のモデル（`spec/formal/<対象>/`）の本体と陽性対照を、正本の `CLAUDE.md` の呼び方で走らせ直し、抜ける条件 4 を判定し直す（#1044）。

usage:
    python3 check-formal-rerun.py <正本リポジトリの根> <spec/formal/<対象> のディレクトリ>... [--timeout <秒>]

**読むだけ**——正本リポジトリに書かない。モデルは対象ごとに一時ディレクトリへ写して走らせ、終わったら消す（TLC の `states/` を正本に残さない）。

**決まりの正は `references/tree.md` の「形式検査のモデル」（記録の項目）と `references/spec-exit.md` の条件 4 である**（このプラグインの中にある）。
記録（`README.md`）の読み方は同梱の `formal-baseline.py` の `read_records`、TLC の呼び方の読み方・走らせ方・判定の文字列は同梱の
`check-tlc.py` のもの（読み込んで使う——写さない）。

## なぜ在るのか（#1044）

条件 4 は Formal Checker が TLC の出力と陽性対照を根拠にするが、**検査器を走らせて結果を書き写すのはモデル**だった。
`check-tlc.py` は呼び方が通るかを確かめるだけで、保存したモデルを走らせ直して判定し直すものは無かった。

## 何を走らせるか

- **本体**: 記録の `モデルのファイル` の一覧の `.tla` のうち、同じ名前の `.cfg` も一覧にあるもの（1 つ以上）。陽性対照の一覧にもある名前は本体に数えない。
- **陽性対照**: 記録の `陽性対照のファイル` の一覧の同じ形のもの（1 つ以上）——わざと壊したモデルと到達の確かめ（反例が出ることを確かめたもの）。
- 両方の一覧のファイルを 1 つの一時ディレクトリに写し、呼び方の後ろに `<名前>.tla` を足して、そのディレクトリで `sh` に渡す（`check-tlc.py` と同じ）。
- **保存した `.cfg` のまま走らせる**——`PROPERTY`（時相の性質）を外して速くしない（外すと判定が弱くなる。`references/tree.md` の「保存したモデルを CI で走らせ続ける」）。

## 重さの注記（#1339）

走らせたモデルごとの行の終わりに `（状態数 <m>・<秒> 秒）` を付ける——状態数は TLC の出力の最後の `<m> distinct states found` の数（進み具合の行の 3 桁ごとの区切り `,`・`.`・U+00A0・U+202F は外す）、秒はこのスクリプトが測った経過時間。
**時間切れ・重いモデルの切り分け**（状態数が多いのか、少ないのに遅いのか）の材料で、**判定と終了コードには使わない**。読めなければ `状態数は読めなかった` と言う。
時間切れの回の状態数は、そこまでの進み具合の行の数（全体より少ない）。状態数を見た後に何を試すかは `agents/formal-checker.md` の「検査が重いとき」を正とする。

## 判定（対象ごと）

| 判定 | 条件 |
| --- | --- |
| `満たす` | 本体がどれも終了コード 0 で `No error has been found` を出し、陽性対照がどれも違反の印（下）を出した |
| `反例あり` | 本体のどれかが違反の印を出した |
| `判定できなかった` | 上のどれでもない——**陽性対照が違反の印を出さない（空振り）**・**本体が通ったが、制約（`CONSTRAINT`）で刈ったまま時相の性質を検査した（TLC の警告 `Declaring state or action constraints during liveness checking is dangerous` が出た。#1339）**・本体が通らず違反の印も出さない（構文の誤り・時間切れ）・TLC のモデルが一覧に無い・`陽性対照のファイル` が無いか TLC のモデルを含まない・一覧のファイルが無い・記録が読めない・呼び方の行が無い |

**違反の印**: `is violated`（不変条件。`check-tlc.py` の陽性対照と同じ）・`were violated`（時相の性質）・`Deadlock reached`（行き止まり）。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 渡した対象がどれも `満たす` |
| 1 | どれかが `反例あり`（条件 4 を満たさない） |
| 2 | 引数が違う・想定外の例外 |
| 4 | `反例あり` は無いが、どれかが `判定できなかった` |

## 何を守り、何を守らないか

守る:

| 守ること | 破る形 |
| --- | --- |
| 陽性対照で反例が出ないモデルを 0 にしない（4） | 何にでも「エラーなし」と言う呼び方・壊れたモデルを、反例なしと読む（Issue の受入基準 2） |
| 本体で反例が出たら 1 | 判定役が「反例なし」と書き写したモデルを通す |
| 本体が通らず違反も出さない（構文の誤り・時間切れ）なら 4 | 走っていないモデルを反例なしと読む |
| `陽性対照のファイル` が無い対象は 4 | 空振りでないことを確かめないまま 0 にする |
| 制約で刈ったまま時相の性質を検査した本体の「反例なし」は 4（#1339） | `CONSTRAINT` で刈った先の時相の性質の違反を隠したまま 0 にする |
| 呼び方の行が無ければ 4 | `PATH` の `tlc` で走らせる（探し方を `check-tlc.py` に揃える） |
| 一時ディレクトリで走らせる | 正本に `states/` と出力が残り、`formal-baseline.py check` が落ちる |
| 1 回の検査を `--timeout` 秒で止める（プロセスグループごと） | 大きいモデルで待ち続ける |
| 走らせたモデルごとに状態数と経過時間を出し、状態数が読めなければそう言う（#1339） | 時間切れのとき、状態数が多すぎたのか遅いだけなのかが出力から分からない・読めない回に数を作る（知らない桁区切りの数の最後の 3 桁を数と読む） |
| 状態数が読めなくても判定と終了コードを変えない | 診断の材料が無いことで、通るモデルを「判定できなかった」にする |

守らない:

| 守らないもの | なぜ |
| --- | --- |
| **TLC でないモデル**（Alloy・総当たり・Z3） | Issue の範囲の外（`check-tlc.py` の呼び方で走らせ直す）。渡されたら `判定できなかった`——spec-review は TLC の対象だけを渡し、ほかは判定役の判定を使う |
| **モデルが仕様を正しく写しているか・陽性対照が意味のある壊し方か** | 判定役の仕事（記録の `陽性対照` に書く）。機械が見るのは、壊した形で反例が出ることだけ |
| **TLC の版による出力の違い** | 判定の文字列は TLC 2.19 で確かめた——`is violated`・`No error has been found` は `check-tlc.py`（#912）、`Temporal properties were violated.`・`Deadlock reached.` はこの周（#1044）に、本体が通り陽性対照が反例を出す形と、本体が行き止まりで反例を出す形を走らせた。ほかの版は確かめていない。回帰テストは偽の TLC で当てる |
| **状態数の行の形の違い** | `distinct states found` の形は TLC 2.19 で確かめた（#1339。手元で英語・ドイツ語・フランス語のロケールで走らせた）。ほかの版・ほかの区切りで形が違えば「読めなかった」になるだけで、判定は変わらない |
| **呼び方の安全** | 正本の `CLAUDE.md` の文字列をそのまま `sh` で走らせる（`check-tlc.py` と同じ） |
| **前の版の残りのファイル** | 一覧のファイルだけを写す（`tree.md` の「次の回が使うのは一覧のファイルだけ」） |

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tlc = _load("check_tlc", "check-tlc.py")
baseline = _load("formal_baseline", "formal-baseline.py")

MODEL_ITEM = "モデルのファイル"
CONTROL_ITEM = "陽性対照のファイル"
VIOLATED = (tlc.BROKEN_MARK, "were violated", "Deadlock reached")
# 状態・行為の制約（`CONSTRAINT`・`ACTION_CONSTRAINT`）と時相の性質を一緒に検査したときに TLC 2.19 が出す警告（#1339 で本物の TLC で確かめた）。
# 刈った先の状態が消えるので、時相の性質の「反例なし」は根拠にならない（`agents/formal-checker.md` の「検査が重いとき」）
PRUNED_LIVENESS = "Declaring state or action constraints during liveness checking is dangerous"
TIMEOUT = 600
PASS, COUNTEREXAMPLE, UNKNOWN = "満たす", "反例あり", "判定できなかった"
EXIT_OK, EXIT_COUNTEREXAMPLE, EXIT_USAGE, EXIT_UNKNOWN = 0, 1, 2, 4
# TLC 2.19 の状態数の行（`<n> states generated, <m> distinct states found, <k> states left on queue.`。区切りなし）と、
# 途中の進み具合の行（`Progress(…): … <m> distinct states found …`）。進み具合の行は JVM のロケールで 3 桁ごとに区切る——
# `,`（英語）・`.`（ドイツ語）・U+202F（フランス語）を手元で見た（#1339）。U+00A0 も同じ扱いにする。
# 数は空白・`:`・`(` か行頭の直後から始まるものだけ読む——知らない区切り（`'` など）の数の最後の 3 桁を、数として読まない
GROUP_SEPARATORS = ",.\u00a0\u202f"
DISTINCT = re.compile(r"(?<![^ \t:(\n])([0-9]{1,3}(?:[" + GROUP_SEPARATORS + r"][0-9]{3})+|[0-9]+) distinct states found")


def entries(names: list[str]) -> list[str]:
    """一覧の `.tla` のうち、同じ名前の `.cfg` も一覧にあるものの名前（拡張子なし）。"""
    return [n[:-4] for n in names if n.endswith(".tla") and f"{n[:-4]}.cfg" in names]


def violated(out: str) -> bool:
    return any(mark in out for mark in VIOLATED)


def measure(out: str, seconds: float) -> str:
    """走らせた 1 回の重さ（状態数と経過時間）の注記。判定には使わない——時間切れ・重いモデルの切り分けの材料（#1339）。

    状態数は出力の最後の `distinct states found` の数（時間切れなら、そこまでの進み具合の行の数で、全体より少ない）。読めなければそう言う。
    """
    found = DISTINCT.findall(out or "")
    count = f"状態数 {re.sub('[' + GROUP_SEPARATORS + ']', '', found[-1])}" if found else "状態数は読めなかった"
    return f"（{count}・{seconds:.1f} 秒）"


def timed(call: str, where: str, name: str, timeout: int) -> tuple[int | None, str, str]:
    """`tlc.run_model` を走らせ、(終了コード, 出力, 重さの注記)。"""
    started = time.monotonic()
    rc, out = tlc.run_model(call, where, name, timeout)
    return rc, out, measure(out, time.monotonic() - started)


def rerun(call: str | None, directory: Path, timeout: int) -> tuple[str, list[str]]:
    """1 つの対象の (判定, 説明の行)。"""
    if not directory.is_dir():
        return UNKNOWN, [f"{directory}: ディレクトリでない"]
    try:
        records, problems = baseline.read_records(directory / baseline.README)
    except baseline.Unjudged as e:
        return UNKNOWN, [str(e)]
    if problems:
        return UNKNOWN, problems
    models = baseline.FILE.findall(records.get(MODEL_ITEM, ""))
    controls = baseline.FILE.findall(records.get(CONTROL_ITEM, ""))
    broken = entries(controls)
    # 陽性対照の一覧にもある名前は本体として走らせない（両方の一覧に書いた記録で、陽性対照を本体の反例と読まない）
    bodies = [n for n in entries(models) if n not in broken]
    if not bodies:
        return UNKNOWN, [f"{directory}: {MODEL_ITEM}に TLC のモデル（同じ名前の .tla と .cfg）が無い——TLC でない対象は走らせ直さない"]
    if not broken:
        return UNKNOWN, [f"{directory}: {CONTROL_ITEM}に TLC のモデル（同じ名前の .tla と .cfg）が無い——空振りでないことを確かめられない"]
    if call is None:
        return UNKNOWN, [f"{directory}: TLC の呼び方が無い（正本の CLAUDE.md の `{tlc.CALL_KEY}` の行。`command -v` では探さない）"]
    names = list(dict.fromkeys(models + controls))
    for name in names:
        source = directory / name
        if "/" in name or name in (baseline.README, ".", "..") or source.is_symlink() or not source.is_file():
            return UNKNOWN, [f"{directory}: 一覧のファイル「{name}」がこのディレクトリの通常のファイルとして無い"]
    lines: list[str] = []
    with tempfile.TemporaryDirectory(prefix="spec-loop-formal-rerun-") as tmp:
        for name in names:
            shutil.copyfile(directory / name, Path(tmp) / name)
        where = tmp  # 写した先で走らせる——TLC の `states/` と出力を正本に残さない
        verdict = PASS
        for name in bodies:
            rc, out, weight = timed(call, where, name, timeout)
            if violated(out):
                lines.append(f"{directory}: 本体 {name}.tla で反例が出た{weight}: {tlc.tail(out)}")
                verdict = COUNTEREXAMPLE
            elif rc != 0 or tlc.GOOD_MARK not in out:
                lines.append(f"{directory}: 本体 {name}.tla が通らず、反例も出さなかった（終了コード {rc}）{weight}: {tlc.tail(out)}")
                if verdict == PASS:
                    verdict = UNKNOWN
            elif PRUNED_LIVENESS in out:
                lines.append(f"{directory}: 本体 {name}.tla は反例なしだが、制約（CONSTRAINT）で刈ったまま時相の性質を検査している——"
                             f"時相の性質の「反例なし」は根拠にならない{weight}")
                if verdict == PASS:
                    verdict = UNKNOWN
            else:
                lines.append(f"{directory}: 本体 {name}.tla: 反例なし{weight}")
        for name in broken:
            rc, out, weight = timed(call, where, name, timeout)
            if violated(out):
                lines.append(f"{directory}: 陽性対照 {name}.tla: 反例が出た（空振りでない）{weight}")
            else:
                lines.append(f"{directory}: 陽性対照 {name}.tla で反例が出ない（終了コード {rc}。空振りの疑い）{weight}: {tlc.tail(out)}")
                if verdict == PASS:
                    verdict = UNKNOWN
    return verdict, lines


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="保存した TLC のモデルの本体と陽性対照を走らせ直す（読むだけ）")
    parser.add_argument("root", type=Path, help="正本リポジトリの根（CLAUDE.md の在る場所）")
    parser.add_argument("targets", type=Path, nargs="+", help="spec/formal/<対象> のディレクトリ")
    parser.add_argument("--timeout", default=str(TIMEOUT), help=f"1 回の検査の上限の秒（既定 {TIMEOUT}）")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_USAGE
    if not args.timeout.isdigit() or int(args.timeout) < 1:
        print(f"--timeout は 1 以上の整数: {args.timeout!r}", file=sys.stderr)
        return EXIT_USAGE
    try:
        call, _, note = tlc.read_declarations(args.root)
    except tlc.Unknown as e:
        call, note = None, str(e)
    if call is None:
        print(f"注記: {note}")
    verdicts = []
    for directory in args.targets:
        verdict, lines = rerun(call, directory, int(args.timeout))
        verdicts.append(verdict)
        for line in lines:
            print(line)
        print(f"{directory}: {verdict}")
    if COUNTEREXAMPLE in verdicts:
        print(f"条件 4 を満たさない（反例あり {verdicts.count(COUNTEREXAMPLE)} 件）")
        return EXIT_COUNTEREXAMPLE
    if UNKNOWN in verdicts:
        print(f"条件 4 は判定できなかった（{verdicts.count(UNKNOWN)} 件）")
        return EXIT_UNKNOWN
    print(f"条件 4 の走らせ直し: 渡した {len(verdicts)} 件とも満たす")
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も 2。トレースバックの 1（反例あり）に化けさせない
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
