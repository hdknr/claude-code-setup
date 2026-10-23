#!/usr/bin/env python3
"""`check-plan-counts.py` の回帰テスト。

    python3 scripts/test-check-plan-counts.py

**このテストは実環境を触らない。** 毎回テンポラリに偽の `docs/plans/` を作り、そこだけを対象にする
（`assert_not_real_repo` がそれを担保する）。実リポジトリの計画ファイルは CI が本体で見る。

**変異テストを含む。** 検査本体を 1 箇所ずつ壊し、**壊したのに全試料の期待どおりのままなら失格**とする。
正しい入力で緑なだけでは、何も検査しない実装でも通る。

試料の形は実データから取った——`- ` が無い行は `issue-288.md:127`・`issue-365.md:102`、
行が無いのは `issue-309.md`・`issue-373.md`、入れ子は `57f75d3` で戻した `issue-253.md`、
字下げした継続行（落としてはならない形）は `issue-175.md:136`。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "check-plan-counts.py"

failures: list[str] = []

OK = "- この周の起票: 0 件\n"

# (名前, ファイル名, 中身, 通るべきか, 落ちるなら出力に含むべき文字列)
CASES: list[tuple[str, str, str, bool, str]] = [
    ("正しい行", "issue-300.md", "# t\n\n" + OK, True, ""),
    ("括弧つき", "issue-300.md", "# t\n\n- この周の起票: 2 件（#1・#2。周の外で起票）\n", True, ""),
    ("継続行で折り返す", "issue-300.md",
     "# t\n\n- この周の起票: 0 件——理由が長く\n  次の行に続く\n- 次の項\n", True, ""),
    ("行が無い", "issue-300.md", "# t\n\n本文だけ\n", False, "が無い"),
    ("`- ` が無い", "issue-300.md", "# t\n\nこの周の起票: 0 件（現時点）\n", False, "形が崩れている"),
    ("字下げした行", "issue-300.md", "# t\n\n- 親\n  - この周の起票: 0 件\n", False, "形が崩れている"),
    ("正しい行と太字の行", "issue-300.md", "# t\n\n" + OK + "\n**この周の起票: 1 件**\n", False, "形が崩れている"),
    ("2 本ある", "issue-300.md", "# t\n\n" + OK + "\n- この周の起票: 1 件\n", False, "2 本ある"),
    ("入れ子（後ろの項を子にする）", "issue-300.md",
     "# t\n\n- 親\n  - 子 1\n- この周の起票: 0 件\n  - 子 2\n- 次\n", False, "入れ子"),
    ("入れ子（継続行の後ろに子）", "issue-300.md",
     "# t\n\n- この周の起票: 0 件——折り返し\n  続き\n  1. 子\n", False, "入れ子"),
    ("フェンスの中だけ", "issue-300.md", "# t\n\n```\n" + OK + "```\n", False, "が無い"),
    ("正しい行とフェンスの中の例", "issue-300.md", "# t\n\n" + OK + "\n```\n- この周の起票: 9 件\n```\n", True, ""),
    ("接尾辞つきの名前も対象", "issue-300-stage2.md", "# t\n", False, "が無い"),
    ("175 未満は免除", "issue-174.md", "# t\n", True, ""),
    ("175 は対象", "issue-175.md", "# t\n", False, "が無い"),
    ("文の途中の言及は見ない", "issue-300.md",
     "# t\n\n手順 8 の「この周の起票」の行は下に書く。\n\n" + OK, True, ""),
]


def assert_not_real_repo(root: Path) -> None:
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not root.resolve().is_relative_to(REAL_REPO), "テストの対象が実リポジトリの内側にある"
    assert root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()), "テストの対象がテンポラリの外にある"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def load(source: str | None = None):
    """本体を読み込む。`source` を渡せば、その中身（変異を入れたソース）を本体として実行する。"""
    spec = importlib.util.spec_from_file_location("check_plan_counts", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    if source is None:
        spec.loader.exec_module(mod)
    else:
        mod.__file__ = str(SCRIPT)
        exec(compile(source, str(SCRIPT), "exec"), mod.__dict__)
    return mod


def run_case(mod, tmp: Path, fname: str, body: str) -> tuple[int, str]:
    plans = tmp / fname.replace(".md", "")
    plans.mkdir()
    assert_not_real_repo(plans)
    (plans / fname).write_text(body, encoding="utf-8")
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = mod.main([str(plans)])
    return rc, out.getvalue() + err.getvalue()


def mismatches(mod) -> list[str]:
    """期待と食い違った試料の名前を返す。"""
    bad = []
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for i, (name, fname, body, ok, needle) in enumerate(CASES):
            case_dir = tmp / str(i)
            case_dir.mkdir()
            rc, text = run_case(mod, case_dir, fname, body)
            if ok and rc != 0:
                bad.append(f"{name}（通るべきが rc={rc}）")
            elif not ok and (rc == 0 or needle not in text):
                bad.append(f"{name}（落ちるべきが rc={rc}・『{needle}』が出力に無い）")
    return bad


# (名前, 本体のソースの元の文字列, 置き換え)。元の文字列はソースにちょうど 1 回現れなければならない
# ——現れなければ変異は何も壊さずに「素通り」に見えるので、それ自体を失格にする。
MUTANTS: list[tuple[str, str, str]] = [
    ("件数の行のパターンを緩める（`- ` と字下げを許す）",
     'COUNT_LINE = re.compile(r"^- この周の起票', 'COUNT_LINE = re.compile(r"^\\s*-?\\s*この周の起票'),
    ("形が崩れた行を見ない", "elif LOOKS_LIKE.match(line):", "elif False:"),
    ("2 本目を数えない", "if len(hits) > 1:", "if len(hits) > 2:"),
    ("入れ子を見ない", "if child is not None:", "if False:"),
    ("字下げだけで入れ子と見る（継続行を落とす）", "if NESTED_ITEM.match(line):", "if True:"),
    ("フェンスの中も数える", "lines = strip_fences(path.read_text(", "lines = (lambda t: t)(path.read_text("),
    ("免除を外す（0 から）", "FIRST_ISSUE = 175", "FIRST_ISSUE = 0"),
    ("全部免除する", "FIRST_ISSUE = 175", "FIRST_ISSUE = 10**9"),
    ("免除の境界を 1 ずらす", ">= FIRST_ISSUE", "> FIRST_ISSUE"),
    ("接尾辞つきの名前を対象から外す", 'PLAN_NAME = re.compile(r"^issue-(\\d+)")', 'PLAN_NAME = re.compile(r"^issue-(\\d+)\\.md$")'),
]


def main() -> int:
    print("試料（素の本体）")
    bad = mismatches(load())
    for b in bad:
        print(f"    {b}")
    check(f"全 {len(CASES)} 試料が期待どおり", not bad)

    print("変異（壊したら少なくとも 1 試料が期待から外れる）")
    source = SCRIPT.read_text(encoding="utf-8")
    for name, old, new in MUTANTS:
        if source.count(old) != 1:
            check(f"{name} → 元の文字列がソースに {source.count(old)} 回（1 回でなければ当てられない）", False)
            continue
        killed = mismatches(load(source.replace(old, new)))
        check(f"{name} → {killed[0] if killed else '素通り'}", bool(killed))

    print("実データの形（陽性対照）")
    # `57f75d3` で戻す前の issue-253.md の崩れ方そのもの。ここが緑なら入れ子の検査は実物を判別する。
    broken = ("- 割り目\n"
              "  - 関門はここで打ち切り（3 パス目は無い）\n"
              "- この周の起票: 0 件\n"
              "  - PR #256 の CI 初回が落ちた（`rmtree` が `.git` で\n"
              "    Directory not empty。再実行で緑）\n"
              "- 反証と差し戻し: なし\n")
    with tempfile.TemporaryDirectory() as d:
        rc, text = run_case(load(), Path(d), "issue-253.md", broken)
    check("#317 の崩れ方（issue-253.md）を入れ子として落とす", rc != 0 and "入れ子" in text)

    if failures:
        print(f"\n{len(failures)} 件失敗", file=sys.stderr)
        return 1
    print("\nすべて通過")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
