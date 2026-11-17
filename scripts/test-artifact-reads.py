#!/usr/bin/env python3
"""`artifact-reads.py`（dev-loop の周が読んだ spec-loop の成果物を計画ファイルから数える。#1157）の回帰テスト。

    python3 scripts/test-artifact-reads.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）。`test-find-cycle.py` と同じ形。

見るもの:

1. **数える**——成果物ごとに読んだ周の数・その周の起票の合計・関門の指摘の合計（陽性対照）。1 周で同じパスは 1 件、`./` は外す、
   ディレクトリは `*.md` を再帰、同じファイルを 2 度渡しても 1 本、コードブロックの中の行は数えない、起票の行・関門の記録の無い周の数を出す。
2. **一度も読まれない成果物**——`--all-artifacts` に挙げたパスのうち、どの周にも無いものを 0 の行で出す。
3. **黙って落とさない**——形に合わない行（装飾つき・字下げ・バッククォートの無いパス・`なし` とパスの混在）は名指しして 1。
4. **0 にしない**——無いパス・計画ファイルが 1 本も無い・引数の誤り・読めない `--all-artifacts` は 2。
5. **読むだけ**——走らせた前後で試料のディレクトリが 1 バイトも変わらない。
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
    "数えない: なしとパスの混在": ({"p/a.md": plan(IR, "- 読んだ成果物: なし")}, ["@p"], 1, ["なしとパスを両方書いている"], []),
    "数えない: 散文の言及は形の誤りでない": ({"p/a.md": plan(IR, extra="読んだ成果物を記録する決まりは spec-gap.md にある。\n")}, ["@p"], 0, [row(IR, 1, 0, 0)], ["形に合わない"]),
    "数えない: 無いパス": ({"p/a.md": plan(IR)}, ["@p", "@nothing"], 2, ["無いパス"], ["| `"]),
    "数えない: 計画ファイルが無い": ({"p/a.txt": "x"}, ["@p"], 2, ["1 本も無い"], []),
    "数えない: 引数なし": ({}, [], 2, ["usage"], []),
    "数えない: 未知の引数": ({"p/a.md": plan(IR)}, ["@p", "--all"], 2, ["usage"], []),
    "数えない: 読めない --all-artifacts": ({"p/a.md": plan(IR)}, ["@p", "--all-artifacts", "@none.txt"], 2, ["読めない"], ["| `"]),
}

# (名前, 壊す前, 壊した後, 殺す試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("./ を外さない", '    while path.startswith("./"):\n', '    while False:\n', "数える: 同じ周の同じパスは 1 件"),
    ("同じ周の同じパスを 2 度数える", "                if p not in reads:\n", "                if True:\n", "数える: 同じ周の同じパスは 1 件"),
    ("注記を許さない", r'(?=$|[\s（])"', r'$"', "数える: 注記つきの行"),
    ("コードブロックを読み飛ばさない", "        if fence is not None:\n            if line", "        if False:\n            if line", "数える: コードブロックの中の行は数えない"),
    ("関門のブロックの外の関門の行も数える", "            if in_gates:\n", "            if True:\n", "数える: 関門のブロックの外（地の文・ほかのコードブロック）の関門の行は数えない"),
    ("関門の指摘を数えない", "                    gates += int(g.group(1))\n", "                    gates += 0\n", "数える: 周の結果と並べる（陽性対照）"),
    ("起票を数えない", "            counts[p] += info[\"count\"] or 0\n", "", "数える: 周の結果と並べる（陽性対照）"),
    ("2 本目以降の計画を数えない", "    for plan in plans:\n", "    for plan in plans[:1]:\n", "数える: 周の結果と並べる（陽性対照）"),
    ("ディレクトリを再帰しない", 'p.rglob("*.md")', 'p.glob("*.md")', "数える: ディレクトリを再帰する"),
    ("同じファイルを 2 度数える", "        if p.resolve() not in [s.resolve() for s in seen]:\n", "        if True:\n", "数える: 同じファイルを 2 度渡しても 1 本"),
    ("多い順に並べない", "key=lambda n: (-cycles[n], n)", "key=lambda n: n", "数える: 多い順に並べる"),
    ("記録の無い周も数える", "        if not info[\"reads\"] and not info[\"none\"]:\n            continue\n", "", "数える: 記録の無い周は数えない"),
    ("なしの周を数えない", "            nones += 1\n", "            pass\n", "数える: なしの周"),
    ("起票の行が無い周を数えない", "            no_count += 1\n", "            pass\n", "数える: 起票の行・関門の記録の無い周"),
    ("関門の記録が無い周を数えない", "            no_gates += 1\n", "            pass\n", "数える: 起票の行・関門の記録の無い周"),
    ("一度も読まれない成果物を出さない", "            names.append(p)\n", "            pass\n", "数える: 一度も読まれない成果物"),
    ("形に合わない行を名指ししない", "            bad.append(no)\n", "            pass\n", "数えない: 太字の行"),
    ("字下げを形の誤りと見ない", r'CANDIDATE = re.compile(r"^[\s>*_\-+]*', r'CANDIDATE = re.compile(r"^[>*_\-+]*', "数えない: 字下げした行"),
    ("全角のコロンを形の誤りと見ない", r'(?:\*\*|__)?\s*[:：]")', r'(?:\*\*|__)?\s*[:]")', "数えない: 全角のコロン"),
    ("なしとパスの混在を見ない", "    if none and reads:\n", "    if False:\n", "数えない: なしとパスの混在"),
    ("形に合わない行で 0", "        return 1\n    return 0\n", "        return 0\n    return 0\n", "数えない: バッククォートの無いパス"),
    ("無いパスを読み飛ばす", "            return None\n", "            continue\n", "数えない: 無いパス"),
    ("計画ファイルが無くても 0", "    if not plans:\n", "    if False:\n", "数えない: 計画ファイルが無い"),
    ("引数なしで 0", "    if not rest:\n", "    if False:\n", "数えない: 引数なし"),
    ("未知の引数を通す", '        if a.startswith("-"):\n', '        if False:\n', "数えない: 未知の引数"),
    ("読めない --all-artifacts で 0", "                return 2\n            for line", "                text = \"\"\n            for line", "数えない: 読めない --all-artifacts"),
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
    for rel, body in files.items():
        if body is None:
            continue
        p = work / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    argv = [str(work / a[1:]) if a.startswith("@") else a for a in args]
    before = snapshot(work)
    proc = subprocess.run([sys.executable, "-I", str(script), *argv], capture_output=True, text=True, cwd=work)
    return proc.returncode, proc.stdout + proc.stderr, snapshot(work) == before


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
