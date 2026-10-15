#!/usr/bin/env python3
"""スケジュール（`schedule.csv`）からガントチャート（SVG）を作る。

usage: python3 schedule-to-gantt.py <schedule.csv> <出力先.svg>

**列の決まりの正は `references/feasibility-csv.md`、出力先の既定は `references/tree.md` の
「生成物の置き場所」である**（どちらもこのプラグインの中にある）。

- **決まりの検査（`check-feasibility-csv.py` の `check_schedule`）を通った表しか描かない。**
- **同じ表から同じバイトを作る**——時刻・乱数・環境（フォントの寸法など）を使わない。
  工程は表の行の順に上から並べ、横軸は最も早い開始日から最も遅い終了日まで 1 日 = 一定の幅。
- 標準ライブラリだけを使う。

終了コード:

- 0: 書いた
- 1: 表が決まりに反する・描く工程が 1 行も無い——**書かない。前に作った出力があれば消す**
  （古いガントチャートを今の表のものと取り違えないため）
- 2: 引数の誤り・表が読めない（中身を検査していない）——同じく書かず、前の出力を消す

**守らないもの**: 見た目（文字が枠からはみ出すか・読みやすいか）。ブラウザで開いて目で見る。
"""

from __future__ import annotations

import importlib.util
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


feasibility = _load("check_feasibility_csv", "check-feasibility-csv.py")

LABEL_W = 260
DAY_W = 12
ROW_H = 28
HEADER_H = 44
PAD = 12
BAR_H = 16
COLORS = {"bg": "#ffffff", "text": "#1f2328", "grid": "#d0d7de", "bar": "#4a7bd0", "milestone": "#d0794a"}

# XML 1.0 に書けない文字（qa-to-pptx.py と同じ）
INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


def text_of(value: str) -> str:
    return escape(INVALID_XML.sub("", value))


def render(rows: list[dict[str, str]]) -> str:
    """検査を通った行から SVG の文字列を作る。"""
    spans = [(date.fromisoformat(r["開始"]), date.fromisoformat(r["終了"])) for r in rows]
    first = min(start for start, _ in spans)
    last = max(end for _, end in spans)
    days = (last - first).days + 1
    width = LABEL_W + days * DAY_W + PAD
    height = HEADER_H + len(rows) * ROW_H + PAD

    def x_of(day: date) -> int:
        return LABEL_W + (day - first).days * DAY_W

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="sans-serif" font-size="12">',
        f'<title>ガントチャート（{first.isoformat()} 〜 {last.isoformat()}）</title>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{COLORS["bg"]}"/>',
    ]
    # 月の境目（最初の日と、各月の 1 日）
    day = first
    while day <= last:
        if day == first or day.day == 1:
            x = x_of(day)
            out.append(f'<line x1="{x}" y1="{PAD}" x2="{x}" y2="{height - PAD}" stroke="{COLORS["grid"]}"/>')
            out.append(f'<text x="{x + 3}" y="{PAD + 14}" fill="{COLORS["text"]}">{day.strftime("%Y-%m")}</text>')
        day += timedelta(days=1)
    out.append(f'<line x1="{PAD}" y1="{HEADER_H - 8}" x2="{width - PAD}" y2="{HEADER_H - 8}" stroke="{COLORS["grid"]}"/>')

    for index, (row, (start, end)) in enumerate(zip(rows, spans)):
        top = HEADER_H + index * ROW_H
        label = f'{row["No"]} {row["工程"]}'
        tooltip = f'{row["No"]} {row["工程"]}: {start.isoformat()} 〜 {end.isoformat()}'
        if row["前提"].strip():
            tooltip += f'（前提: {row["前提"]}）'
        color = COLORS["milestone"] if start == end else COLORS["bar"]
        bar_w = ((end - start).days + 1) * DAY_W
        out.append("<g>")
        out.append(f"<title>{text_of(tooltip)}</title>")
        out.append(f'<text x="{PAD}" y="{top + ROW_H // 2 + 4}" fill="{COLORS["text"]}">{text_of(label)}</text>')
        out.append(f'<rect x="{x_of(start)}" y="{top + (ROW_H - BAR_H) // 2}" width="{bar_w}" height="{BAR_H}" '
                   f'rx="3" fill="{color}" data-no={quoteattr(INVALID_XML.sub("", row["No"]))}/>')
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def remove_stale(out: Path) -> None:
    if out.is_file():
        out.unlink()
        print(f"{out}: 前に作った出力を消した（今の表から作ったものではないため）", file=sys.stderr)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    source, out = Path(argv[0]), Path(argv[1])
    try:
        problems, rows = feasibility.check_schedule(source)
    except feasibility.Unreadable as e:
        print(e, file=sys.stderr)
        remove_stale(out)
        return 2
    if not problems and not rows:
        problems = [f"{source}: 描く工程が 1 行も無い"]
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        print("ガントチャートは作っていない", file=sys.stderr)
        remove_stale(out)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(render(rows).encode("utf-8"))
    print(f"{out}: {len(rows)} 工程のガントチャートを書いた")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
