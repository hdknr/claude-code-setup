#!/usr/bin/env python3
"""ある版が前の版から何を足し・変え・消したかを、前の版の時点の全体と比べて出す。

usage: python3 diff-versions.py <docs ディレクトリ> [--version <n>]

**決まりの正は `references/versions.md` の「版の差分」である**（このプラグインの中にある）。

- **v<n> の差分 ＝ v<n-1> の時点の全体と v<n> の時点の全体の比較。** 全体は同梱の `merge-versions.py` の `merge` で重ねる
  （**重ね方を写さない**）。`--version` を省けば作業中の版（番号が最大の版）。
- 単位は重ね合わせと同じ——Q&A は行（`No`。共有の表と内部の表の両方。並びは共有が先）、機能は `id`、ほかのファイルは版のディレクトリからのパス。
  **追加**は v<n> にだけある、**変更**は両方にあって中身が違う、**削除**は v<n-1> にだけある。
- **同じ中身を置き直しただけのものは変更に数えない**（比較なので）。**v1 は前の版が無いので、全部が追加。**
- 削除には `docs/v<n>/removed.csv` の `理由` を添える。
- 何も書かない。同じ入力から同じ出力（並びは全体の並び・パスの順）。標準ライブラリだけを使う。

終了コード（`merge-versions.py` に合わせる）:

- 0: 出した
- 1: 入力が決まりに反する（重ね合わせが作れない）——比べていない
- 2: 引数の誤り・入力が無い／読めない・その版が無い——比べていない

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **変更の中身（どの列・どの行が変わったか）** | 比べるのは単位ごとの一致だけ。中身は `docs/v<n>/` と前の版を開いて見る |
| **新しいつもりで前の版の番号を書いた** | 同じ番号は「変更」の意味と決めている（`merge-versions.py` と同じ） |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


merge_versions = _load("merge_versions", "merge-versions.py")

ADDED, CHANGED, REMOVED = "追加", "変更", "削除"
STATUSES = [ADDED, CHANGED, REMOVED]
# 種類の名前は removed.csv の `種類` と同じ（理由を引き当てるため）
KINDS = [merge_versions.KIND_QA, merge_versions.KIND_FEATURE, merge_versions.KIND_FILE]


# dataclass は使わない——ほかのスクリプトが importlib で読み込むと sys.modules に無く、dataclass が落ちる
class Change:
    def __init__(self, status: str, key: str, before=None, after=None) -> None:
        self.status = status
        self.key = key  # Q&A の No・機能の id・ファイルのパス
        self.before = before  # 前の版の全体での中身（追加なら None）
        self.after = after  # この版の全体での中身（削除なら None）
        self.reason = ""  # 削除の理由（removed.csv）


class Diff:
    def __init__(self, version: int) -> None:
        self.version = version
        self.changes: dict[str, list[Change]] = {}  # 種類 → 変化

    def count(self, kind: str, status: str) -> int:
        return sum(1 for c in self.changes[kind] if c.status == status)


def compare_maps(before: dict, after: dict) -> list[Change]:
    """並びは、この版の全体の並び（追加・変更）のあとに、前の版の全体の並び（削除）。"""
    changes = []
    for key, value in after.items():
        if key not in before:
            changes.append(Change(ADDED, key, None, value))
        elif before[key] != value:
            changes.append(Change(CHANGED, key, before[key], value))
    for key, value in before.items():
        if key not in after:
            changes.append(Change(REMOVED, key, value, None))
    return changes


def removal_reasons(root: Path) -> dict[tuple[str, str], str]:
    """`removed.csv` の (種類, 対象) → 理由。決まりの検査は `merge` が済ませている。"""
    path = root / merge_versions.REMOVED
    if not path.is_file():
        return {}
    reader = csv.reader(io.StringIO(merge_versions.read_text(path), newline=""))
    next(reader, None)
    return {(f[0], f[1]): f[2].strip() for f in reader if len(f) == len(merge_versions.REMOVED_COLUMNS)}


def compare(docs: Path, version: int | None = None) -> tuple[list[str], Diff | None]:
    """(決まりに反する点, 差分) を返す。決まりに反する点があれば差分は None。

    無い・読めない入力と無い版は `merge_versions.Unreadable` を投げる（`OutOfRange` を含む）。
    """
    try:
        problems, versions, now, _ = merge_versions.merge(docs, version)
    except merge_versions.OutOfRange as e:
        # `merge` の文言は `--upto` を名指しするので、この引数の名前で言い直す
        raise merge_versions.OutOfRange(str(e).replace("--upto", "--version", 1)) from None
    if problems:
        return problems, None
    number = version if version is not None else len(versions)
    if number > 1:
        problems, _, before, _ = merge_versions.merge(docs, number - 1)
        if problems:
            return problems, None
    else:
        before = merge_versions.Whole()
    diff = Diff(number)
    diff.changes[merge_versions.KIND_QA] = compare_maps({**before.qa, **before.internal}, {**now.qa, **now.internal})
    diff.changes[merge_versions.KIND_FEATURE] = compare_maps(before.features, now.features)
    diff.changes[merge_versions.KIND_FILE] = compare_maps(dict(sorted(before.files.items())),
                                                          dict(sorted(now.files.items())))
    reasons = removal_reasons(versions[number - 1][1])
    for kind in KINDS:
        for change in diff.changes[kind]:
            if change.status == REMOVED:
                change.reason = reasons.get((kind, change.key), "")
    return [], diff


def label(kind: str, change: Change) -> str:
    """一覧に添える 1 行の説明（Q&A は質問、機能は題）。"""
    value = change.after if change.after is not None else change.before
    if kind == merge_versions.KIND_QA:
        return value.get("質問", "").strip()
    if kind == merge_versions.KIND_FEATURE:
        title = value.get("title") if isinstance(value, dict) else None
        return title.strip() if isinstance(title, str) else ""
    return ""


def one_line(text: str) -> str:
    """セルの改行で偽の行を作らない——改行は `\\n` と書いて 1 行に留める（1 変更 = 1 行）。"""
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")


def render(diff: Diff) -> list[str]:
    if diff.version == 1:
        lines = ["v1 の差分（前の版が無いので、全部が追加）"]
    else:
        lines = [f"v{diff.version} の差分（v{diff.version - 1} の時点の全体との比較）"]
    for kind in KINDS:
        counts = "・".join(f"{s} {diff.count(kind, s)}" for s in STATUSES)
        lines.append(f"{kind}: {counts}")
        for change in diff.changes[kind]:
            text = one_line(label(kind, change))
            line = f"  {change.status} {one_line(change.key)}" + (f" {text}" if text else "")
            if change.status == REMOVED:
                line += f"（理由: {one_line(change.reason or '')}）"
            lines.append(line)
    return lines


def main(argv: list[str]) -> int:
    version = None
    args = list(argv)
    if "--version" in args:
        at = args.index("--version")
        if at + 1 >= len(args) or not re.fullmatch(r"[1-9][0-9]*", args[at + 1]):
            print("--version には 1 以上の整数を渡す", file=sys.stderr)
            return 2
        version = int(args[at + 1])
        del args[at:at + 2]
    if len(args) != 1:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    docs = Path(args[0])
    if not docs.is_dir():
        print(f"{docs}: ディレクトリが無い", file=sys.stderr)
        return 2
    try:
        problems, diff = compare(docs, version)
    except merge_versions.Unreadable as e:
        print(e, file=sys.stderr)
        print("比べていない", file=sys.stderr)
        return 2
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        print("重ね合わせが作れないので、比べていない", file=sys.stderr)
        return 1
    print("\n".join(render(diff)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
