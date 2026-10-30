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
- 2: 引数の誤り・表が読めない（中身を検査していない。入力のパスの名前が使えない——NUL・符号化できない孤立サロゲート——ときを含む。#592）・
  書けない（出力先の名前が使えないときを含む）・想定外の例外（巨大なセルの `csv.Error` など。#286）
  ——同じく書かず、前の出力を消す（引数の誤りでは出力先が分からないので消さない）。
  **名前が使えない**のは、NUL を含む名前と、surrogateescape でバイトに戻せない孤立サロゲート（U+D800〜U+DC7F・U+DD00〜U+DFFF）を含む名前で、
  どちらも `ValueError` になる（CLI からは届かない）。**U+DC80〜U+DCFF はバイトに戻せる**（CLI が UTF-8 でないバイトを渡すとこの形になる）ので
  `ValueError` にならず、OS が拒めば `OSError` の「書けない（<理由>）」・「読めない（<理由>）」になる（#591）。
- **前の出力を消せない**（出力先のディレクトリが書けない・辿れないなど）**ときは、どの経路でも 2**——表が決まりに反していても 1 にしない。
  **残った前の出力を、消せなかった理由つきで名指しする**（今の表のものと取り違えないため。#499）。
  前の出力があるかどうかを確かめられないとき（辿れないディレクトリ・先を辿れない symlink）も、消せなかったものとして名指しする。
- **出力先が symlink なら、リンクも先も消さない。** 先が通常のファイル（辿れる先。#626）でも、先を辿れなくても（#535）、
  リンクと先のパスを名指しして 2——先のパスは鎖を解いた先で、先を辿れないときは辿れたところまで解いたもの（その先にまだリンクがありうる）。リンクを消しても先の古い中身は残り、辿れない先はディレクトリかも分からない。
  壊れたリンクとディレクトリを指すリンクは、この道具の出力ではないので消さずに名指しもしない（表が決まりに反するなら 1）。
  表が正しく書けるときは、リンクの先に書く（0）。

**守らないもの**: 見た目（文字が枠からはみ出すか・読みやすいか）。ブラウザで開いて目で見る。
"""

from __future__ import annotations

import errno
import importlib.util
import os
import re
import stat
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


# 「無い」と読んでよい stat の失敗（python3.12 の `Path.is_file` が無視するもの）。ほかの失敗（辿れないなど）は消せなかったと言う。
# ENAMETOOLONG は、名前の 1 つが NAME_MAX を超えるとき（その名前のファイルは在りえない）だけ「無い」と読む——
# パス全体が PATH_MAX を超えるだけなら、ファイルは在りうる（相対パスで辿れる）ので消せなかったと言う（#499 の 2 パス目）
ABSENT = (errno.ENOENT, errno.ENOTDIR, errno.EBADF, errno.ELOOP)
NAME_MAX = 255


def absent(out: Path, e: OSError) -> bool:
    if e.errno in ABSENT:
        return True
    return e.errno == errno.ENAMETOOLONG and any(len(os.fsencode(part)) > NAME_MAX for part in out.parts)


def unusable_name(path: Path) -> bool:
    """OS に渡せない名前か——NUL を含む・surrogateescape でバイトに戻せない孤立サロゲートを含む（どちらも開くと `ValueError`）。
    U+DC80〜U+DCFF はバイトに戻せるので使える名前と読む（OS が拒めば `OSError`。#591）。"""
    try:
        return b"\0" in os.fsencode(path)
    except UnicodeEncodeError:
        return True


def remove_stale(out: Path) -> str | None:
    """前に作った出力（通常のファイル）を消す。消せなかったら、名指しする行を返す（#499）。

    `Path.is_file` で確かめない——python3.14 は辿れないディレクトリでも黙って False を返し、残った出力を見逃す。
    symlink は `lstat` で見て、**リンクも先も消さない**:
    先が通常のファイル（辿れる先）なら、リンクを消しても先の古い中身は残る（`unlink` が消すのはリンク）ので、
    リンクと先のパスを名指しする（#626。#499 ではリンクを消して「消した」と言っていた）。
    先を辿れない（EACCES など）なら、先が前の出力かを確かめられないので同じく名指しする——
    辿れないディレクトリと同じ扱い（#535。先がディレクトリでも消してしまう）。先のパスも名指しする（#625）。
    先がディレクトリ・辿れる先が無い（壊れたリンク）なら、この道具の出力ではないので消さずに名指しもしない。"""
    try:
        mode = out.lstat().st_mode
        if stat.S_ISLNK(mode):
            # 先のパス（鎖を解いた先）。非 strict の realpath は辿れなくても例外を出さず、辿れたところまで解く
            target = Path(os.path.realpath(out))
            try:
                mode = out.stat().st_mode
            except OSError as e:
                # 長すぎる名前は、鎖を解いた先のパスで見る（途中のどこかの名前が NAME_MAX を超えるなら在りえない——壊れたリンク。
                # 別のリンクを経由しても同じ。#535 の CR1-1・R2-1）
                if absent(target, e):
                    return None  # 壊れたリンク——この道具の出力ではない
                return f"前に作った出力を消せない: {out}（リンクの先を辿れない: {e.strerror}。先: {target}）。今の表から作ったものではない"
            if stat.S_ISREG(mode):  # 辿れる先の通常のファイル——リンクを消しても先の古い中身は残る（#626）
                return f"前に作った出力を消せない: {out}（リンクの先に前の出力が残る。先: {target}）。今の表から作ったものではない"
        if not stat.S_ISREG(mode):
            return None  # ディレクトリなど、この道具の出力でないものは消さない
        out.unlink()
    except OSError as e:
        if absent(out, e):  # 無い（確かめてから消すまでに消えたものを含む）
            return None
        return f"前に作った出力を消せない: {out}（{e.strerror}）。今の表から作ったものではない"
    except ValueError:  # 符号化できない名前など（NUL・U+DC80〜U+DCFF のほかの孤立サロゲート）——その名前のファイルは在りえない（3.12 の `is_file` も無いと読んだ）
        return None
    except Exception as e:  # 想定外の例外でも、消せなかったことを名指しする（「想定外の例外」に化けさせない）
        return f"前に作った出力を消せない: {out}（{type(e).__name__}: {e}）。今の表から作ったものではない"
    print(f"{out}: 前に作った出力を消した（今の表から作ったものではないため）", file=sys.stderr)
    return None


def stop(out: Path, code: int) -> int:
    """前の出力を消して終わる。消せなければ、どの経路でも 2 にして名指しする（1 の「表が決まりに反する」と取り違えない）。"""
    left = remove_stale(out)
    if left:
        print(left, file=sys.stderr)
        return 2
    return code


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.splitlines()[2] if __doc__ else
              f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）", file=sys.stderr)
        return 2
    source, out = Path(argv[0]), Path(argv[1])
    try:
        problems, rows = feasibility.check_schedule(source)
        if not problems and rows:
            svg = render(rows).encode("utf-8")
    except feasibility.Unreadable as e:
        print(e, file=sys.stderr)
        return stop(out, 2)
    except Exception as e:  # 想定外の例外（巨大なセルの csv.Error など）でも、前の出力を残さない（#286）
        if isinstance(e, ValueError) and unusable_name(source):  # 入力のパスの名前が使えない——読めない（#592。CLI からは届かない）
            print(f"{source}: 読めない（入力のパスの名前が使えない: {type(e).__name__}: {e}）。中身を検査していない", file=sys.stderr)
        else:
            print(f"{source}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        return stop(out, 2)
    if not problems and not rows:
        problems = [f"{source}: 描く工程が 1 行も無い"]
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        print("ガントチャートは作っていない", file=sys.stderr)
        return stop(out, 1)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(svg)
    except OSError as e:  # 書きかけを今の表のものと取り違えないよう消す
        print(f"{out}: 書けない（{e.strerror}）", file=sys.stderr)
        return stop(out, 2)
    except ValueError as e:  # 出力先の名前が符号化できない（NUL・U+DC80〜U+DCFF のほかの孤立サロゲート。#591）——その名前には書けない（#582。CLI からは届かない）
        print(f"{out}: 書けない（出力先の名前が使えない: {type(e).__name__}: {e}）", file=sys.stderr)
        return stop(out, 2)
    except Exception as e:  # 書く途中の想定外の例外でも、前の出力を消すか名指しする（入口に逃がさない。#499 の 2 パス目）
        print(f"{out}: 書く途中の想定外の例外で止まった（{type(e).__name__}: {e}）", file=sys.stderr)
        return stop(out, 2)
    print(f"{out}: {len(rows)} 工程のガントチャートを書いた")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
