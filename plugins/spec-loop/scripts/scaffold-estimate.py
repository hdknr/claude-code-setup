#!/usr/bin/env python3
"""scaffold の書き起こしの前に、仕様のテストケースがどれだけ Red テストに乗るかの見積もりを数える（#1302）。

usage: python3 scaffold-estimate.py list  [--repo <正本>]
       python3 scaffold-estimate.py check [--repo <正本>] [--file <見積もりのファイル>]

`/spec-loop:scaffold` の手順 1a（中間表現を書き起こす前）の道具である。#1296 では、仕様のテストケースのほとんどが中間表現に乗らないことに
**書き起こしの途中で**気づいた。**書き起こす前に、ケースを 3 つに分けて数え、利用者に示して続けるかを確かめる**——どれに分けるかは
仕様の読み方（判断）なのでスキルが決め、**このスクリプトは、仕様のケースの一覧を出し（`list`）、スキルが書いた分け方の形と網羅を確かめて数える（`check`）**。
決まり（3 つの区分の意味・止める割合の線を決めていない理由）の原本は `references/spec-ir.md` の「書き起こす前の見積もり」。

**仕様のテストケースの数え方は `scaffold.py` の `spec_case_rows`（条件 1 の番号の形。`check-spec-exit.py` の `case_rows`）を読む**——写さない。
`docs/` の版を**メモリ上で**重ね合わせた全体の仕様（`spec/`）を見る。**中間表現（`spec_ir.json`）は要らない**（書き起こす前だから）。

`list`: 仕様のケースを `番号  ファイル:行  行の原文` で 1 行ずつ出す。

`check`: 見積もりのファイル（既定 `<正本>/build/scaffold-estimate.json`。`build/` は commit しない）を読む。形:

    {"cases": {"F1-1": {"class": "red"},
               "F1-7": {"class": "acceptance", "reason": "画面で 2 回押す。関数の 1 回の呼び出しでは表せない"},
               "F1-9": {"class": "neither", "reason": "期待が書かれていない"}}}

- `class` は `red`（Red テストにできる）・`acceptance`（Red テストにできず、受入基準に回す）・`neither`（どちらにもできない）の 3 つ。
- `acceptance`・`neither` は `reason`（空でない 1 行の文字列）が要る——`red` は書いてもよい。
- 仕様のケースの番号を**全部**分け、**1 つずつ**（番号は NFKC で正規化し、前後の空白を落として比べる）。仕様に無い番号は分けない。
- 出力は `仕様のテストケース N 件のうち、Red テストにできる a 件・受入基準に回す b 件・どちらにもできない c 件（Red テストだけの割合 R%・受入基準まで含めた乗る割合 P%）` と、
  どちらにもできないケースの番号・場所（`ファイル:行`）・`reason`、受入基準に回すケースの番号。
  **「乗る割合」は Red テスト + 受入基準（開発に渡るケース）の割合で、Red テストだけの割合も併記する**（受入基準に回すものは Red テストにならない）。

**止める割合の線は決めていない**（`references/spec-ir.md` の「書き起こす前の見積もり」が理由）。0 を返しても「続けてよい」ではない——
**割合に依らず、結果を利用者に示し、続けるかを確かめてから 2 に入る**のはスキルの手順である。

終了コード: 0 ／ 1 形の違反か、分けていないケース・仕様に無い番号がある ／ 2 判定していない（`docs/` が無い・版が無い・重ね合わせが読めない・
見積もりのファイルが無いか JSON として読めない・引数の誤り）／ 3 仕様にテストケースの番号の表が無く、見積もれない（`list`・`check` とも。
番号の形に当たる表が無いと `ref` と結べない——止めて、利用者に仕様の番号の振り方を確かめる）。版の重ね合わせが決まりに反するときは 1。

**守ること**:

- `check` は、仕様のケースのうち分けていないものがあれば 1 を返し、番号を名指しする
- `check` は、仕様に無い番号を分けていれば 1
- `check` は、同じ番号を 2 度分けていれば 1（正規化した後の重なりも）
- `check` は、`class` が 3 つのどれでもなければ 1
- `check` は、`acceptance`・`neither` の `reason` が空か文字列でなければ 1
- `check` は、形（最上位のキー・`cases` の入れ子・値の型）が違えば 1
- `check` は、分けたとおりに件数を数え、どちらにもできないケースを番号と場所で全部名指しする
- `check` は、乗る割合が低くても止めず、形が正しければ 0
- `check` は、見積もりのファイルが無いか JSON として読めなければ 2
- 仕様にテストケースの番号が 1 件も無ければ、`list`・`check` とも 3
- `list` は、仕様のケースを全部（番号・場所・原文で）出す
- どちらも何も書かない（正本の中のファイルを変えない）

**守らないもの**:

- **分け方が正しいか**——`red` と書いたケースが本当に関数の 1 回の呼び出しで書けるかは、書き起こす側の判断で、機械は見ない（書き起こした後の内訳は `scaffold.py` が出す）。
- **番号の形に当たらない表のケース**——`check-spec-exit.py` の `case_rows` が数えない表（見出しが `ID`・`No` の表）は、見積もりの対象に出ない（#1297 の限界）。
- **見積もりのとおりに書き起こしたか**——書き起こした後の内訳（`scaffold.py` の「仕様のテストケース N 件のうち…」）と見積もりを突き合わせない。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 仕様のケースの数え方・版の重ね合わせ・docs の場所は `scaffold.py` のもの（写さない）
scaffold = _load("scaffold", "scaffold.py")

DEFAULT_FILE = Path("build") / "scaffold-estimate.json"
RED, ACCEPTANCE, NEITHER = "red", "acceptance", "neither"
CLASSES = (RED, ACCEPTANCE, NEITHER)
NEEDS_REASON = (ACCEPTANCE, NEITHER)
TOP_KEYS = {"cases"}
ITEM_KEYS = {"class", "reason"}


class Unjudged(Exception):
    """判定していない（2）。"""


class Violation(Exception):
    """見積もりのファイルの形か網羅の違反（1）。行を持つ。"""

    def __init__(self, lines: list[str]):
        super().__init__("\n".join(lines))
        self.lines = lines


class NoCases(Exception):
    """仕様にテストケースの番号の表が無い（3）。"""


def normalize(number: str) -> str:
    return unicodedata.normalize("NFKC", number).strip()


def spec_cases(repo: Path) -> list[tuple[str, int, str, str]]:
    """重ね合わせた全体の仕様のケース (ファイル, 行, 番号, 行の原文)。重ね合わせが決まりに反すれば `Violation`。"""
    docs = repo / scaffold.DOCS
    if not docs.is_dir():
        raise Unjudged(f"{docs}: ディレクトリが無い（版は {scaffold.DOCS}/v1/ から置く。references/versions.md）")
    versions = scaffold.versions
    try:
        if not versions.find_versions(docs, []):
            raise Unjudged(f"{docs}: 版（v1 など）が 1 つも無い（references/versions.md）。判定していない")
        problems, _, _, rendered = versions.merge(docs)
    except versions.Unreadable as exc:
        raise Unjudged(f"{exc}。重ね合わせていない")
    except RecursionError:
        raise Unjudged("版の中間表現を読めない（入れ子が深すぎる）。重ね合わせていない")
    if problems:
        raise Violation(problems + ["版の重ね合わせが決まりに反する（references/versions.md）。見積もらない"])
    rows = scaffold.spec_case_rows(rendered)
    if not rows:
        raise NoCases("仕様にテストケースの番号の表が無い（見出しがテストケースの表で、先頭のセルが番号の形の表。references/spec-exit.md の"
                      "「テストケースの番号の重複」）。見積もれない——ケースの番号が無いと、書き起こした `ref` と結べない")
    return rows


def unique_cases(rows: list[tuple[str, int, str, str]]) -> dict[str, tuple[str, int]]:
    """番号 → 最初に出た場所。重複は条件 1 が止めるので、ここでは最初の場所だけ持つ。"""
    cases: dict[str, tuple[str, int]] = {}
    for rel, line, number, _ in rows:
        cases.setdefault(number, (rel, line))
    return cases


def read_estimate(path: Path) -> dict[str, dict]:
    """見積もりのファイルを読んで形を確かめる。読めなければ `Unjudged`、形の違反は `Violation`。返すのは正規化した番号 → 項目。"""
    if not path.is_file():
        raise Unjudged(f"{path}: 見積もりのファイルが無い（仕様のケースを分けて書く。scaffold スキルの手順 1a）。判定していない")
    repeated: list[str] = []

    def keep(pairs):
        keys = [key for key, _ in pairs]
        repeated.extend(sorted({key for key in keys if keys.count(key) > 1}))
        return dict(pairs)

    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=keep)
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Unjudged(f"{path}: JSON として読めない（{type(exc).__name__}）。判定していない")
    problems: list[str] = []
    if not isinstance(data, dict):
        raise Violation([f"{path}: 最上位が JSON のオブジェクトでない"])
    extra = sorted(set(data) - TOP_KEYS)
    if extra:
        problems.append(f"{path}: 最上位に決まりの外のキー: {', '.join(extra)}（書けるのは cases だけ）")
    cases = data.get("cases")
    if not isinstance(cases, dict) or not cases:
        problems.append(f"{path}: `cases` が、番号から項目へのオブジェクト（1 件以上）でない")
        raise Violation(problems)
    found: dict[str, dict] = {}
    for raw, item in cases.items():
        number = normalize(raw)
        if number in found:
            problems.append(f"同じ番号を 2 度分けている: {number}")
            continue
        label = f"{number}"
        if not isinstance(item, dict):
            problems.append(f"{label}: 項目がオブジェクトでない")
            continue
        unknown = sorted(set(item) - ITEM_KEYS)
        if unknown:
            problems.append(f"{label}: 項目に決まりの外のキー: {', '.join(unknown)}（書けるのは class・reason だけ）")
        kind = item.get("class")
        if kind not in CLASSES:
            problems.append(f"{label}: class が {'・'.join(CLASSES)} のどれでもない（{kind!r}）")
        reason = item.get("reason")
        if kind in NEEDS_REASON and (not isinstance(reason, str) or not reason.strip() or "\n" in reason.strip()):
            problems.append(f"{label}: class が {kind} なら reason（空でない 1 行の文字列）が要る")
        elif reason is not None and not isinstance(reason, str):
            problems.append(f"{label}: reason が文字列でない")
        found[number] = item
    # JSON の同じキーの重複（`json` は後のものだけ残す）。`cases` の直下なら番号の 2 度の分け、ほかのキーでも決まりの違反
    for key in repeated:
        problems.append(f"同じ番号を 2 度分けている: {normalize(key)}（JSON の同じキーが 2 つ）" if key in cases
                        else f"JSON の同じキーが 2 つ: {key}")
    if problems:
        raise Violation(problems)
    return found


def estimate_lines(cases: dict[str, tuple[str, int]], estimate: dict[str, dict]) -> list[str]:
    """分けたとおりの内訳。`read_estimate` と `spec_cases` を通した後の値を渡す（網羅は `coverage` が先に確かめる）。"""
    by_class = {kind: [n for n in cases if estimate[n]["class"] == kind] for kind in CLASSES}
    total = len(cases)
    reachable = len(by_class[RED]) + len(by_class[ACCEPTANCE])
    percent = 100 * reachable / total  # 開発に渡る割合（Red テスト + 受入基準）
    red_percent = 100 * len(by_class[RED]) / total  # Red テストになる割合（受入基準に回すものは数えない）
    lines = [f"仕様のテストケース {total} 件のうち、Red テストにできる {len(by_class[RED])} 件・受入基準に回す {len(by_class[ACCEPTANCE])} 件"
             f"・どちらにもできない {len(by_class[NEITHER])} 件（Red テストだけの割合 {red_percent:.1f}%・受入基準まで含めた乗る割合 {percent:.1f}%）"]
    if by_class[ACCEPTANCE]:
        lines.append(f"  受入基準に回す: {', '.join(by_class[ACCEPTANCE])}")
    for number in by_class[NEITHER]:
        rel, line = cases[number]
        lines.append(f"  どちらにもできない: {number}（{rel}:{line}）: {estimate[number]['reason'].strip()}")
    lines.append("  ——止める割合の線は決めていない。割合に依らず、この結果を利用者に示し、続けるかを確かめてから中間表現の書き起こしに入る"
                 "（どちらにもできないケースは、`/spec-loop:spec-review` に戻して仕様で決めるか、仕様から外すかを利用者と決める。"
                 "`references/spec-ir.md` の「書き起こす前の見積もり」）")
    return lines


def coverage(cases: dict[str, tuple[str, int]], estimate: dict[str, dict]) -> list[str]:
    """分けていないケースと、仕様に無い番号を名指しする行（無ければ空）。"""
    problems = [f"分けていないケース: {number}（{rel}:{line}）" for number, (rel, line) in cases.items() if number not in estimate]
    problems += [f"仕様に無い番号を分けている: {number}" for number in estimate if number not in cases]
    return problems


def cmd_list(repo: Path) -> int:
    rows = spec_cases(repo)
    print(f"仕様のテストケース {len(unique_cases(rows))} 件（番号・場所・原文。重ね合わせた全体の `spec/`）")
    for rel, line, number, text in rows:
        print(f"{number}\t{rel}:{line}\t{text}")
    return 0


def cmd_check(repo: Path, path: Path) -> int:
    cases = unique_cases(spec_cases(repo))
    estimate = read_estimate(path)
    problems = coverage(cases, estimate)
    if problems:
        raise Violation(problems + [f"{path} を直して当て直す（仕様のケースを全部、1 つずつ分ける）"])
    for line in estimate_lines(cases, estimate):
        print(line)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="scaffold の書き起こしの前に、仕様のテストケースが Red テストに乗る見積もりを数える")
    parser.add_argument("command", choices=["list", "check"])
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--file", type=Path, default=None, help=f"見積もりのファイル（既定 <正本>/{DEFAULT_FILE}）")
    try:
        args = parser.parse_args()
    except SystemExit as exc:
        return 2 if exc.code else 0
    repo = args.repo.resolve()
    path = args.file if args.file is not None else repo / DEFAULT_FILE
    try:
        return cmd_list(repo) if args.command == "list" else cmd_check(repo, path)
    except Unjudged as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Violation as exc:
        for line in exc.lines:
            print(line, file=sys.stderr)
        return 1
    except NoCases as exc:
        print(str(exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
