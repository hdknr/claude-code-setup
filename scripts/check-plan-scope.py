#!/usr/bin/env python3
"""差分が、計画ファイルの「変更範囲」に収まっているかを検出する。

usage: python3 scripts/check-plan-scope.py <base-ref> [--plan PATH]

CI（.github/workflows/plugins.yml）が PR で呼ぶ。ローカルでも実行できる:

    python3 scripts/check-plan-scope.py origin/main

なぜ必要か（#119）: `SKILL.md` 手順 4 は「手順 3 に書いた変更範囲の外へ、黙って出ない」を
**必須**として決めているが、**守られたかどうかを見る歯止めが 1 本も無かった**。
#118 の周ではこれを **BLOCKED** として申告し、**人手（`/code-review` 3 パスと Verifier 2 回、
および計画ファイルへの手書き）だけ**で代替していた。

**禁止しているのは「広げること」ではなく「黙って広げること」**（手順 4）なので、
**この検査が求めるのも「計画ファイルに書いてあること」だけ**である。
**範囲を広げたければ、計画ファイルの「変更範囲」を先に更新すればよい。**

読む書式（`SKILL.md` 手順 3 が正）:

    ## 1. 変更範囲

    触る:

    - `plugins/dev-loop/skills/dev-loop/SKILL.md` — 説明は自由
    - `scripts/*.py`
    - `docs/`

    触らない:

    - `diagrams/` 一切

- **「変更範囲」を含む見出し**から、**次の同レベル以上の見出し**までを対象の節とする。
- 節の中の **`触る`** で始まる行から **`触らない`** で始まる行までが、**触る側**である。
- 箇条書き（`-` / `*`）の**最初のバッククォート span** をパターンとして読む。説明は自由。
- パターンは **glob**（`fnmatch`）。**`*` はディレクトリ区切りも跨ぐ**ので、
  `scripts/*.py` は `scripts/a/b.py` にも当たる。**絞りたいなら具体的に書く。**
- **`/` で終わるパターンは、その配下すべて**を指す。

判定:

- 差分にあって、どのパターンにも当たらないファイルがある → **エラー**（非ゼロ終了）
- **計画ファイル自身は常に免除する。** 周が進めば必ず更新されるもので、
  手順 3 が「計画が変わったらファイルを更新する」と決めている。

**この検査が守らないもの**——**何を守らないかを書いておかないと、緑であることが
安心の根拠に化ける**:

| 守らないもの | なぜ |
| --- | --- |
| **ブランチ名が `issue/<n>-…` でない周** | 計画ファイルを当てる最後の手は「差分に計画ファイルが 1 つだけある」だが、**別の Issue の計画ファイルを*直すのが成果物*の周では、それを拾ってしまう。** ブランチが番号を名乗っていれば**そこだけを見る** |
| **計画ファイルを持たない周** | **この仕組みの外にある。** 計画ファイルが見つからなければ**判定せずに 0 で終わる**（見つからないことは出力に出す）。`check-diagram-freshness.py` の `output: null` と**同じ形の限界**である |
| **範囲を*後から*広げた周** | 見るのは **HEAD 時点**の計画ファイルだけ。**手を動かす前に更新したのか、後で辻褄を合わせたのかは、この検査には見えない**（差分の順序は見ていない）。手順 4 が求めているのは前者で、**そこは人間のレビューが見る** |
| **広すぎるパターン** | `**` や `.` と書けば全部に当たる。**「書いてある」しか見ない**ので、**範囲の妥当性は採点しない** |
| **触らないと宣言した側** | **`触らない:` は読むが、判定には使わない。** 触る側に当たらなければ、そもそもエラーになる |
| **受入基準を広げたか** | 手順 4 は「範囲を広げたら受入基準も広げる」と決めているが、**それはここでは見ていない**（採点表の中身は機械で読めない） |

標準ライブラリのみ。git はサブプロセスで呼ぶ。
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN_GLOBS = ("docs/plans/issue-*.md", ".claude/plans/issue-*.md")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET = re.compile(r"^\s*[-*]\s+")
TICKED = re.compile(r"`([^`]+)`")


def git(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False, cwd=REPO
    )
    return proc.returncode, proc.stdout


def changed_files(base: str) -> list[str]:
    rc, out = git("diff", "--name-only", f"{base}...HEAD")
    if rc != 0:
        return []
    return [line for line in out.splitlines() if line.strip()]


def find_plan(files: list[str], explicit: str | None) -> Path | None:
    """計画ファイルを当てる。`--plan` → ブランチ名 → 差分 の順。

    **ブランチ名が Issue 番号を名乗っているなら、そこだけを見る。**
    差分に別の Issue の計画ファイルが入っていることがあり（それを*直すのが成果物*の周）、
    **差分から拾うと、別の周の変更範囲で採点してしまう**
    ——**これはこのスクリプトを書いた周自身が最初に踏んだ**（差分に入っていた
    `docs/plans/issue-110.md` を、この周の計画として読んだ）。
    """
    if explicit:
        p = REPO / explicit
        return p if p.is_file() else None

    rc, out = git("rev-parse", "--abbrev-ref", "HEAD")
    m = re.match(r"^issue/(\d+)", out.strip()) if rc == 0 else None
    if m:
        for template in ("docs/plans/issue-{}.md", ".claude/plans/issue-{}.md"):
            p = REPO / template.format(m.group(1))
            if p.is_file():
                return p
        return None  # 番号は名乗っている。差分で代用しない

    hits = [
        f for f in files
        if any(fnmatch.fnmatch(f, g) for g in PLAN_GLOBS) and (REPO / f).is_file()
    ]
    return REPO / hits[0] if len(hits) == 1 else None


def parse_scope(text: str) -> list[str] | None:
    """「変更範囲」の節の *触る側* のパターンを返す。節が読めなければ None。"""
    lines = text.splitlines()
    start = level = None
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m and "変更範囲" in m.group(2):
            start, level = i + 1, len(m.group(1))
            break
    if start is None:
        return None

    section: list[str] = []
    for line in lines[start:]:
        m = HEADING.match(line)
        if m and len(m.group(1)) <= level:
            break
        section.append(line)

    # 「触る」から「触らない」まで。**「触らない」が先に当たらないよう、前方一致で見る。**
    patterns: list[str] = []
    collecting = False
    seen_touch = False
    for line in section:
        bare = line.strip().lstrip("*_ ").strip()
        if bare.startswith("触らない"):
            collecting = False
            continue
        if bare.startswith("触る"):
            collecting = True
            seen_touch = True
            continue
        if collecting and BULLET.match(line):
            m = TICKED.search(line)
            if m:
                patterns.append(m.group(1).strip())
    return patterns if seen_touch else None


def covered(path: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if pat.endswith("/"):
            if path == pat.rstrip("/") or path.startswith(pat):
                return True
        elif fnmatch.fnmatch(path, pat):
            return True
        elif fnmatch.fnmatch(path, pat.rstrip("/") + "/*"):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="差分が計画の変更範囲に収まっているか")
    ap.add_argument("base", help="比較元の ref（例: origin/main）")
    ap.add_argument("--plan", help="計画ファイルのパス（既定: 差分／ブランチ名から当てる）")
    opts = ap.parse_args()

    files = changed_files(opts.base)
    if not files:
        print(f"{opts.base}...HEAD に差分が無い。判定していない。")
        return 0

    plan = find_plan(files, opts.plan)
    if plan is None:
        print(
            "計画ファイルが見つからないので、変更範囲を**判定していない**。\n"
            "  探した順: (1) --plan  (2) ブランチ名 issue/<n>-… から引いた\n"
            "            docs/plans/issue-<n>.md ／ .claude/plans/issue-<n>.md\n"
            "            (3) 番号を名乗らないブランチなら、差分の中の計画ファイル 1 件\n"
            "  **緑ではなく「見ていない」である。** --plan で明示もできる。"
        )
        return 0

    rel = plan.relative_to(REPO).as_posix()
    patterns = parse_scope(plan.read_text())
    if patterns is None:
        print(
            f"{rel} の「変更範囲」の節が読めない。\n"
            "  見出しに「変更範囲」を含め、その節に `触る:` の行と、\n"
            "  バッククォートで囲んだパターンの箇条書きを置く（SKILL.md 手順 3 を正とする）。"
        )
        return 1
    if not patterns:
        print(f"{rel} の「触る:」にパターンが 1 つも無い。")
        return 1

    outside = [
        f for f in files
        if f != rel and not covered(f, patterns)
    ]
    print(f"計画: {rel}（触る: {len(patterns)} パターン） / 差分: {len(files)} ファイル")
    if outside:
        print("\n変更範囲の外に出ているファイル:")
        for f in outside:
            print(f"  - {f}")
        print(
            "\n**禁止しているのは「広げること」ではなく「黙って広げること」**（手順 4）。\n"
            f"広げると決めたなら、{rel} の「変更範囲」に足してからコミットする。\n"
            "**範囲を広げたら受入基準も広げる**（手順 4。ここでは見ていない）。"
        )
        return 1
    print("差分はすべて変更範囲の中にある。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
