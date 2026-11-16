#!/usr/bin/env python3
"""`check-review-record.py`（仕様レビューの記録から、抜ける条件 2・3 と実行の上限を数え直す。#1044）の回帰テスト。

    python3 scripts/test-check-review-record.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-findings-csv.py` と同じ形。

見るもの:

1. **`conditions`**——最後のレビューの Red Team に効く重さ（`判断が要る`・`結果が割れる`）の行が 1 行でも残る表で 1（Issue の受入基準 1。陽性対照）。
   `補い`・`退ける`・範囲の外・ほかの判定役の行だけなら 0。1 回目に直した行があれば最後のレビューは 2 回目（2 回目の行が 0 件でも）、
   直した行が無ければ 1 回目。狭いパスの効く重さは役を問わず 1。`--run` で前の回を数える。
2. **`limit`**——数え始め（`続ける`・`範囲を決め直す` の最後の行の後）からの `満たさない`・`判定できなかった` の実行の行が N 以上で 3、未満で 0、
   最後の利用者の判断が `止める` なら 3、`回答待ち`・`満たす` は数えない、表が無ければ 0、`--limit` で N を変える。
3. **中身を数えていない形を 0 にしない（2）**——指摘の表が検査に通らない・実行の行が無い・`--run` が実行の行でない・見出しが欠けた記録・引数の誤り。
4. **本体の定数が references と一致する**（`references/spec-exit.md` の「指摘の重さ」の効く重さ・「上限」の数える値と数え直しの判断）。
5. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

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


# 名前 → (サブコマンド, 指摘の表（None なら置かない）, 記録の表（None なら置かない）, 足す引数, 期待の終了コード, 出力に含む語)
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
    "条件: 2 回目の起票の行は直しでないので数える": ("conditions", F_HEAD + f() + f(review="2回目", weight="判断が要る", category="共有の Q&A 表に起票する",
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
    "条件: 1 回目の効く重さは 2 回目があれば数えない": ("conditions", F_HEAD + f(weight="結果が割れる") + f(review="2回目"), RUNS, [], 0, "満たす"),
    "条件: 狭いパスはほかの役でも数える": ("conditions", F_HEAD + f() + f(review="狭いパス", judge="formal-checker", weight="結果が割れる"),
                                RUNS, [], 1, "狭いパス・formal-checker"),
    "条件: 確かめられない行は重さのまま数える": ("conditions", F_HEAD + f(weight="判断が要る", confirmed="確かめられない"), RUNS, [], 1, "満たさない"),
    "条件: 前の回の行は数えない": ("conditions", F_HEAD + f(no="1", day="2026-11-01", weight="判断が要る", category="共有の Q&A 表に起票する")
                           + f(category="共有の Q&A 表に起票する", result="Q-002"), RUNS, [], 0, "満たす: 回 2・最後のレビューは 1回目"),
    "条件: --run で前の回を数える": ("conditions", F_HEAD + f(no="1", day="2026-11-01", weight="判断が要る", category="共有の Q&A 表に起票する")
                             + f(), RUNS, ["--run", "1"], 1, "回 1"),
    "条件: 見出しだけの表": ("conditions", F_HEAD, RUNS, [], 0, "満たす"),
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
    ("回で絞らない", "    mine = [(number, c) for number, c in enumerate(cells, start=2) if c[\"回\"] == run]\n",
     "    mine = [(number, c) for number, c in enumerate(cells, start=2)]\n", "条件: 前の回の行は数えない"),
    ("検査に通らない表を数える", "    if code:\n        return EXIT_UNJUDGED, problems", "    if False:\n        return EXIT_UNJUDGED, problems",
     "判定しない: 指摘の表が検査に通らない"),
    # 「判定しない（2）」を崩す変異は、別の例外で 2 のままの形にしない——判定して 0 を返す形にする
    ("実行の行が無いのに満たすと言う", "    if not runs:\n        return EXIT_UNJUDGED", "    if not runs:\n        return EXIT_OK", "判定しない: 実行の行が無い"),
    ("--run を見ない", "    elif run not in {r[\"回\"] for r in runs}:\n", "    elif False:\n", "判定しない: --run が実行の行でない"),
    ("数えたのに 0", "    return EXIT_UNMET, lines", "    return EXIT_OK, lines", "条件: 判断が要るが 1 行（陽性対照）"),
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
    ("次の回の行も直したと読む", '    return c["レビュー"] == SECOND and c["振り分け"] == FIX and c["結果"] != NEXT_RUN\n',
     '    return c["レビュー"] == SECOND and c["振り分け"] == FIX\n', "条件: 結果が割れるが 2 回目に 1 行"),
    ("起票の行も直したと読む", '    return c["レビュー"] == SECOND and c["振り分け"] == FIX and c["結果"] != NEXT_RUN\n',
     '    return c["レビュー"] == SECOND and c["結果"] != NEXT_RUN\n', "条件: 2 回目の起票の行は直しでないので数える"),
    ("表が無ければ判定しない", "    if not record.exists():\n        return EXIT_OK", "    if False:\n        return EXIT_OK", "上限: 表が無ければ 0 回"),
]


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        raise AssertionError(f"{name}{(': ' + detail) if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    tmp = Path(tempfile.gettempdir()).resolve()
    check(f"試料が一時ディレクトリの中: {path}", tmp in path.resolve().parents)


def run_one(script: Path, work: Path, case: tuple) -> tuple[int, str]:
    command, table, runs, extra, _, _ = case
    if work.exists():
        shutil.rmtree(work)
    folder = work / "spec-review"
    folder.mkdir(parents=True)
    assert_in_tmp(folder)
    if table is not None:
        (folder / "v1-findings.csv").write_text(table, encoding="utf-8")
    if runs is not None:
        (folder / "v1.csv").write_text(runs, encoding="utf-8")
    if command == "conditions":
        argv = ["conditions", str(folder / "v1-findings.csv")]
    elif command == "limit":
        argv = ["limit", str(folder / "v1.csv")]
    else:
        argv = []
    proc = subprocess.run([sys.executable, "-I", str(script), *argv, *extra], capture_output=True, text=True, cwd=work)
    return proc.returncode, proc.stdout + proc.stderr


def as_expected(case: tuple, result: tuple[int, str]) -> bool:
    return result[0] == case[4] and case[5] in result[1]


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
            check(f"変異を殺す（終了コードが変わる）: {name} ← {killer}", result[0] != original[0], f"{result[0]} {result[1][-300:]!r}")
        print(f"  変異 {len(MUTATIONS)} 件 OK")
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"NG: {e}")
        sys.exit(1)
