#!/usr/bin/env python3
"""計画ファイルの件数の行（`- この周の起票: N 件`）が、集める側に拾える形で 1 本だけあるかを見る。

CI（.github/workflows/plugins.yml）から呼ばれるが、ローカルでもそのまま実行できる:

    python3 scripts/check-plan-counts.py            # docs/plans/ を見る
    python3 scripts/check-plan-counts.py <dir>      # 別のディレクトリを見る（テスト用）

なぜ必要か（#384）: 件数の行の書式は dev-loop の `SKILL.md` 手順 8 が決めているが、
**規定を足しても機械で確かめていなかった**ので、#287 → #305 → #311 と足すたびに後続が出て、
直近の周（`issue-288.md`・`issue-365.md`・`issue-373.md`）でも守られていなかった。
**書式の本体は `SKILL.md` 手順 8 を正とする**——ここにあるのは集める側のパターンだけである。

見ること（ファイルごと）:

1. **件数の行がフェンスの外にちょうど 1 本ある**——パターン `^- この周の起票: [0-9]+ 件`。
   無い・2 本ある、はどちらも落とす。
2. **形が崩れた行が無い**——行頭（字下げ・箇条の印・番号・見出し・引用・太字を許して）`この周の起票` で始まるのに
   パターンに当たらない行（`- ` が無い・字下げ・`1. `・`## `・`> `・太字（`**`・`__`）など）。**集める側から黙って落ちる形**である。
   文の途中で「この周の起票」に触れる行は見ない。
3. **入れ子の中に無い**——件数の行の後ろに続く字下げした範囲に**箇条の項**があれば落とす。
   **字下げした兄弟の項の上に件数の行を差し込むと、後ろの項が件数の行の子になる**（#317。
   `57f75d3` で戻した `issue-216/217/253.md` の形）。**字下げした継続行（件数の行自身の折り返し）は落とさない**
   ——`issue-175.md`・`issue-194.md`・`issue-216.md` が正しくその形をしている。

**対象（免除の条件はここに 1 か所だけ書く）**: `issue-<N>*.md` で **N ≥ 175** のもの全部。
175 は件数の行の規定が入った dev-loop 1.35.0（`4e3c805`）の後に始まった最初の周で、
**175 未満の計画ファイルは件数の行を 1 本も持たない**（規定が無かった）。
**内容（`## 手順 8` の節の有無など）で対象を決めない**——件数の行を書き忘れた計画ファイルは
手順 8 の節も持たないことが多く（`issue-373.md` がそう）、内容で決めると直すべきものが対象から外れる。
**周の途中の計画ファイルも対象になる**——PR の CI がマージの前の関門になる。

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **件数の値の正しさ** | 見ているのは形だけ。どの Issue をどの周に数えるかは `SKILL.md` 手順 8 の規定で、機械では決まらない |
| **括弧書きの中身** | 決定が変わったのに古い注記が残る（#313）形は見えない |
| **遅延継続** | 件数の行の直後に字下げの無い文が空行なしで続くと、Markdown ではその項に取り込まれる。実データに無いので見ない |
| **N < 175 の計画ファイル** | 上の免除 |
| **`docs/plans/` の外の計画ファイル** | `.claude/plans/`（作業メモ）は gitignore され CI に無い |

標準ライブラリのみ。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from markdown_fences import strip_fences  # noqa: E402

FIRST_ISSUE = 175
COUNT_LINE = re.compile(r"^- この周の起票: [0-9]+ 件")
# 行頭（字下げ・箇条の印・番号・見出し・引用・太字を許して）「この周の起票」で始まる行。件数の行のつもりで書いた行。
LOOKS_LIKE = re.compile(r"^\s*(?:(?:[-*+]|\d+[.)]|#+|>|__)\s*)*この周の起票")
PLAN_NAME = re.compile(r"^issue-(\d+)")
NESTED_ITEM = re.compile(r"^[ \t]+(?:[-*+]|\d+[.)])\s")


def targets(plans: Path) -> list[Path]:
    out = []
    for path in sorted(plans.glob("issue-*.md")):
        m = PLAN_NAME.match(path.name)
        if m and int(m.group(1)) >= FIRST_ISSUE:
            out.append(path)
    return out


def problems(path: Path) -> list[str]:
    """`行番号: 理由` の並びを返す。空なら問題なし。"""
    lines = strip_fences(path.read_text(encoding="utf-8")).split("\n")
    found: list[str] = []
    hits: list[int] = []
    for i, line in enumerate(lines):
        if COUNT_LINE.match(line):
            hits.append(i)
        elif LOOKS_LIKE.match(line):
            found.append(f"{i + 1}: 件数の行の形が崩れている（行頭から `- この周の起票: N 件` と書く）: {line.strip()[:80]}")
    if not hits and not found:
        found.append("件数の行（`- この周の起票: N 件`）が無い")
    if len(hits) > 1:
        found.append(f"{', '.join(str(i + 1) for i in hits)}: 件数の行が {len(hits)} 本ある（1 本だけ置く）")
    for i in hits:
        child = nested_item(lines, i)
        if child is not None:
            found.append(f"{i + 1}: 件数の行が入れ子の中にある（{child + 1} 行の字下げした項が件数の行の子になる。"
                         "親の項の並び（子を含む）が終わった後ろに置く）")
    return found


def nested_item(lines: list[str], i: int) -> int | None:
    """件数の行（i 行目）の子になってしまう、字下げした箇条の項の行番号を返す。無ければ `None`。

    件数の行に続く字下げした行は、件数の行自身の折り返し（継続行）でもありうるので、
    **字下げしただけでは落とさない**——落とすのは、字下げした範囲の中に**箇条の項**があるときだけ。
    範囲は、次の字下げしていない空行でない行の手前まで。
    """
    for j in range(i + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            continue
        if line[:1] not in (" ", "\t"):
            return None
        if NESTED_ITEM.match(line):
            return j
    return None


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    plans = Path(argv[0]) if argv else root / "docs" / "plans"
    if not plans.is_dir():
        print(f"ERROR: 計画ファイルのディレクトリが無い: {plans}", file=sys.stderr)
        return 1
    files = targets(plans)
    bad = 0
    for path in files:
        for p in problems(path):
            print(f"ERROR: {path.name}:{p}", file=sys.stderr)
            bad += 1
    if bad:
        print("", file=sys.stderr)
        print("件数の行の書式は dev-loop の SKILL.md 手順 8 を正とする（集める側は "
              "`^- この周の起票: [0-9]+ 件` の 1 本で拾う）。", file=sys.stderr)
        return 1
    print(f"件数の行の検査: 問題なし（issue-{FIRST_ISSUE} 以降の計画ファイル {len(files)} 本）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
