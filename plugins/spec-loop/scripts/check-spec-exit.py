#!/usr/bin/env python3
"""仕様レビューを抜ける条件のうち、**機械で決まる条件 1** だけを判定する。

usage: python3 check-spec-exit.py <qa.csv> <仕様のディレクトリ>

**条件の正は `references/spec-exit.md` である**（このプラグインの中にある）。
条件 1 は「Q&A 表に反映済みでない行が 0 件で、仕様に未決定の印が 0 件」。
**条件 2〜5 はこのスクリプトでは判定しない**——判定役の報告で決まる（`spec-review` の本文）。
**0 で終わっても「抜けた」ではない。** 出力もそう言う。

- 反映済みでない行は、**`qa-to-pptx.py` の `read_pending` で読む**（PPTX に載る行と同じ定義。
  状態の名前を列挙して絞らない）。Q&A 表の列検査（`check-qa-csv.py`）もそこで掛かる。
- 未決定の印（`MARKERS`）と、印に当たらない語（`NOT_MARKERS`）は `references/spec-exit.md` の写しで、
  **写しがずれていないかはこのリポジトリの `scripts/test-check-spec-exit.py` が突き合わせて見る**。

終了コード:

- 0: 条件 1 を満たす
- 1: 条件 1 を満たさない（反映済みでない行と、印のある箇所を**全部** 1 行ずつ出す）。
  **Q&A 表が列検査を通らないときもここ**（決まりに反する表は、確定していない）
- 2: 判定していない——引数の誤り・Q&A 表が読めない・仕様のディレクトリが無い・
  仕様のファイルが 1 つも無い（**書いていない仕様は、確定していない**ので、0 にはしない）・
  **図（`FIGURE_SUFFIXES`）以外に読めないファイルがある**（UTF-16・`.xlsx` など。見ていないものを
  「印 0 件」と言わない）・**読めた仕様のファイルが 1 つも無い**（図だけ）。
  **NUL を含むファイルは読めない側に数える**——ASCII だけの UTF-16 は UTF-8 として*読めてしまう*
  （NUL は UTF-8 として有効）ので、復号の成否だけでは見分けられない。
  **印のある箇所が別に見つかったら 1 を優先する**（読めないファイルがあっても、満たさないことは確か）

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。

**この判定が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **図（`FIGURE_SUFFIXES`）の中の印** | 図を置くことがあるので落とさない。**見なかったファイルは件数と名前を出す**。図以外の読めないファイルは 2 にする |
| **印を使わずに書いた未決定**（「あとで決める」「検討中」） | 言い回しは列挙しきれない。判定役（Red Team）が条件 2・3 で見る |
| **ドット始まりのファイル・ディレクトリの中** | `.git` などを見ないため |
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent

# `references/spec-exit.md` の「未決定の印」の写し
MARKERS = ("TBD", "TODO", "未定", "要確認")
# 印を含むが、印ではない語（同上）
NOT_MARKERS = ("未定義",)
# 読めなくても 2 にしないファイル（図）。**ここに無い拡張子は、読めなければ 2**——
# 知らない形式を「見なくてよいもの」に数えない
FIGURE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico")


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pptx = _load("qa_to_pptx", "qa-to-pptx.py")


def marker_pattern() -> re.Pattern[str]:
    """英字の印は語として（前後が英数字でない）、それ以外は部分一致で当てる。"""
    parts = []
    for marker in MARKERS:
        if marker.isascii():
            parts.append(rf"(?<![A-Za-z0-9_]){re.escape(marker)}(?![A-Za-z0-9_])")
        else:
            parts.append(re.escape(marker))
    return re.compile("|".join(parts), re.IGNORECASE)


PATTERN = marker_pattern()


def find_markers(text: str) -> list[tuple[int, str]]:
    """(行番号, 当たった印) の一覧。印ではない語は先に伏せる（長さを保つ）。

    **行は NFKC で正規化してから当てる**——全角の `ＴＢＤ` は `IGNORECASE` では半角と同じに
    ならない（日本語の仕様では全角の英字がふつうに出る）。
    """
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        line = unicodedata.normalize("NFKC", line)
        for word in NOT_MARKERS:
            line = line.replace(word, "\0" * len(word))
        for match in PATTERN.finditer(line):
            hits.append((number, match.group(0)))
    return hits


def spec_files(root: Path) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return files


def check(qa_path: Path, spec_dir: Path) -> tuple[int, list[str]]:
    """(終了コード, 出力する行) を返す。"""
    code, lines, pending = pptx.read_pending(qa_path)
    if code == 2:
        return 2, lines + ["条件 1 を判定していない（Q&A 表を読めない）"]
    if not spec_dir.is_dir():
        return 2, [f"{spec_dir}: ディレクトリが無い。条件 1 を判定していない（書いていない仕様は確定していない）"]
    files = spec_files(spec_dir)
    if not files:
        return 2, [f"{spec_dir}: ファイルが 1 つも無い。条件 1 を判定していない（書いていない仕様は確定していない）"]

    problems = []
    if code:
        problems += lines
        problems.append(f"{qa_path}: 列検査を通らない（決まりに反する表は確定していない）")
    for row in pending:
        problems.append(f"{qa_path}: {row['No']}: 状態が {row['状態']}（{row['質問']}）")

    unread = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            unread.append(path)
            continue
        if "\0" in text:
            unread.append(path)
            continue
        for number, marker in find_markers(text):
            problems.append(f"{path}:{number}: 未決定の印 {marker}")

    notes = [f"見なかったファイル（読めない・UTF-8 でない）: {len(unread)} 件"]
    notes += [f"    {path}" for path in unread]
    if problems:
        return 1, problems + notes + ["条件 1 を満たさない。仕様レビューを抜けていない"]
    not_figures = [path for path in unread if path.suffix.lower() not in FIGURE_SUFFIXES]
    if not_figures:
        return 2, notes + [
            f"{spec_dir}: 図以外に読めないファイルが {len(not_figures)} 件ある。"
            "条件 1 を判定していない（見ていない仕様は確定していない）"
        ]
    if len(unread) == len(files):
        # 1 つも読めなければ、見た仕様は 0 ファイル——「1 つも無い」と同じ扱い
        return 2, notes + [
            f"{spec_dir}: どの仕様も読めなかった（{len(files)} ファイルすべて）。"
            "条件 1 を判定していない（読めない仕様は確定していない）"
        ]
    return 0, notes + [
        f"条件 1 を満たす（Q&A 表に反映済みでない行 0 件・仕様 {len(files) - len(unread)} ファイルに未決定の印 0 件）",
        "**これだけでは抜けていない**——条件 2〜5 は判定していない（references/spec-exit.md）",
    ]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    code, lines = check(Path(argv[0]), Path(argv[1]))
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
