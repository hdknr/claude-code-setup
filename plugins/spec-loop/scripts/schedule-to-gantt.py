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
- 2: 引数の誤り・表が読めない（中身を検査していない。入力のパスの名前が使えない——NUL・符号化できない孤立サロゲート——ときを含む。
  名前は開く前に確かめ、理由を「NUL を含む」「バイトに戻せない文字を含む: <理由>」と書く。#592・#662。NUL は `\\x00` と出す）・
  書けない（出力先の名前が使えないときを含む）・想定外の例外（巨大なセルの `csv.Error` など。#286）
  ——同じく書かず、前の出力を消す（引数の誤りでは出力先が分からないので消さない）。
  **名前が使えない**のは、NUL を含む名前と、surrogateescape でバイトに戻せない孤立サロゲート（U+D800〜U+DC7F・U+DD00〜U+DFFF）を含む名前で、
  どちらも `ValueError` になる（CLI からは届かない）。**U+DC80〜U+DCFF はバイトに戻せる**（CLI が UTF-8 でないバイトを渡すとこの形になる）ので
  `ValueError` にならず、OS が拒めば `OSError` の「書けない（<理由>）」・「読めない（<理由>）」になる（#591）。
- **前の出力を消せない**（出力先のディレクトリが書けない・辿れないなど）**ときは、どの経路でも 2**——表が決まりに反していても 1 にしない。
  **残った前の出力を、消せなかった理由つきで名指しする**（今の表のものと取り違えないため。#499）。
  前の出力があるかどうかを確かめられないとき（辿れないディレクトリ・先を辿れない symlink）も、消せなかったものとして名指しする。
  **出力先を開いた（切り詰めた）あとで書けず、消せもしない**（書けないディレクトリの中で容量が尽きたなど）ときは、残るのは前の出力ではなく
  今回の書きかけなので「書きかけの出力を消せない: <出力先>（<理由>。今回の書きかけが残る）。完全な出力ではない」と名指しする（#689。リンクの先は下）。
- **出力先が symlink なら、リンクも先も消さない。** 先が通常のファイル（辿れる先。#626）でも、先を辿れなくても（#535）、
  リンクと先のパスを名指しして 2——先のパスは鎖を解いた先で、先を辿れないときは辿れたところまで解いたもの（その先にまだリンクがありうる）。リンクを消しても先の古い中身は残り、辿れない先はディレクトリかも分からない。
  壊れたリンク・輪になったリンク（a→b→a）とディレクトリを指すリンクは、この道具の出力ではないので消さずに名指しもしない（表が決まりに反するなら 1）。
  **OS の上限（Linux 40・macOS 32）より長い輪でない鎖**は、辿ると輪と同じ ELOOP になるが、鎖を解いた先が通常のファイルなら
  「リンクの鎖が長すぎる」とリンクと先のパスを名指しして 2（#689。出力先の親のディレクトリが長すぎる鎖のときも同じ）——鎖の先が輪・無い・ディレクトリなら名指ししない。
  python3.12 では千段ほどの鎖は解けない（RecursionError）ので、先が前の出力かを確かめられないものとして「リンクの鎖を解けない」と名指しして 2。
  表が正しく書けるときは、リンクの先に書く（0）。**先を開いた（切り詰めた）あとで書けなかった**（容量が尽きたなど）ときは、
  先に残るのは前の出力ではなく今回の書きかけなので、「書きかけの出力を消せない」とリンクと先のパスを名指しして 2（#662。前の中身は失われている）。
  **先の無い壊れたリンクも、表が正しければ開いたときに先が作られる**——書く途中で失敗したら、作った先（今回の書きかけ）を同じく
  「書きかけの出力を消せない」とリンクと先のパスで名指しして 2（#689。リンクも先も消さない。名指ししないのは、表が決まりに反する・書く前に止まったときだけ）。
  **0.39.0 より前は、表が決まりに反する・描く工程が無いとき、辿れる先の通常のファイルを指すリンクを消して 1 だった**（表が正しくて書けないときは前も 2）——移行は `references/tree.md` の「生成物の置き場所」。

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


def name_problem(path: Path) -> str | None:
    """OS に渡せない名前なら、その理由を返す——NUL を含む・surrogateescape でバイトに戻せない孤立サロゲートを含む（どちらも開くと `ValueError`）。
    U+DC80〜U+DCFF はバイトに戻せるので使える名前と読む（OS が拒めば `OSError`。#591）。"""
    try:
        return "NUL を含む" if b"\0" in os.fsencode(path) else None
    except UnicodeEncodeError as e:
        return f"バイトに戻せない文字を含む: {e}"


def shown(path: Path) -> str:
    """標準エラーに出すパス。NUL は素のバイトで出さず `\\x00` と書く（端末で名前が切れて見えないように。#662 の CR9）。
    孤立サロゲートは標準エラーの backslashreplace が `\\udXXX` と書く。"""
    return str(path).replace("\0", "\\x00")


def link_target(link: Path) -> Path:
    """リンクの先のパス（鎖を解いた先）。非 strict の realpath は辿れなくても例外を出さず、辿れたところまで解く。
    先のパスを使う分岐でだけ呼ぶ（#662 の CR10）——名指しするときと、名前が長すぎる（ENAMETOOLONG）先の壊れたリンクの判定と、
    ELOOP の出力先の判定（#689。`long_chain` は strict の realpath を自分で呼び、これは辿れない先の名指しにだけ使う）。
    先の無い壊れたリンク・ディレクトリを指すリンクでは呼ばない。"""
    return Path(os.path.realpath(link))


def long_chain(out: Path, e: OSError) -> str | None:
    """ELOOP の出力先を見分ける（#689）。ELOOP は輪（a→b→a）でも、OS の上限（Linux 40・macOS 32）より長い輪でない鎖でも出る——
    出力先のリンクの鎖でも、親のディレクトリのリンクの鎖でも。strict の realpath は OS の上限を持たずに 1 段ずつ鎖を解き、
    輪（輪のあとに `..` が続く形を含む）なら ELOOP、先が無ければ ENOENT の OSError を出す——非 strict は輪のあとの `..` を文字として当て、
    関係の無いファイルに着くことがある（#689 の 2 パス目 CR2-2）。
    解いた先が通常のファイルなら、長い鎖の先に前の出力が残る——消さずに、出力先と先のパスを名指しする行を返す（消そうにも、出力先からは辿れない）。
    輪・先が無い・先がディレクトリなら、この道具の出力ではないので None（名指ししない）。先を辿れない（EACCES など）なら、確かめられないので名指しする。
    **python3.12 の realpath は再帰で鎖を解くので、千段ほどの鎖では RecursionError になる**（3.13 からは解ける）——先が前の出力かを
    確かめられないので、確かめられないものとして名指しする（#499 の決まり。#689 の 2 パス目 CR2-1）。"""
    try:
        try:
            target = Path(os.path.realpath(out, strict=True))
        except OSError as e2:
            if absent(Path(e2.filename) if isinstance(e2.filename, str) else out, e2):
                return None  # 輪・先が無い（ELOOP・ENOENT）——壊れたリンク
            return f"前に作った出力を消せない: {out}（リンクの先を辿れない: {e2.strerror}。先: {link_target(out)}）。今の表から作ったものではない"
        mode = target.stat().st_mode
    except Exception as e2:  # 解けない（python3.12 の深すぎる鎖の RecursionError など）——「想定外の例外」に化けさせず、確かめられないと名指しする
        # （外側の `except OSError` から呼ぶときは、`remove_stale` の `except Exception` に守られていない。#689 の 1 パス目 CR1-1）
        return f"前に作った出力を消せない: {out}（リンクの鎖を解けない: {type(e2).__name__}: {e2}）。先が前の出力かを確かめられない"
    if not stat.S_ISREG(mode):
        return None  # ディレクトリ——長い鎖の先でも、この道具の出力ではない
    return f"前に作った出力を消せない: {out}（リンクの鎖が長すぎる: {e.strerror}。先: {target}）。今の表から作ったものではない"


def left(out: Path, reason: str, partial: bool) -> str:
    """消せなかったリンクでない出力先を名指しする行。`partial`（今回開いて切り詰めたあと）なら、残るのは前の出力ではなく
    今回の書きかけ（#689 の A1。前の中身は切り詰めで失われている）。"""
    if partial:
        return f"書きかけの出力を消せない: {out}（{reason}。今回の書きかけが残る）。完全な出力ではない"
    return f"前に作った出力を消せない: {out}（{reason}）。今の表から作ったものではない"


def remove_stale(out: Path, partial: bool = False) -> str | None:
    """前に作った出力（通常のファイル）を消す。消せなかったら、名指しする行を返す（#499）。

    `Path.is_file` で確かめない——python3.14 は辿れないディレクトリでも黙って False を返し、残った出力を見逃す。
    symlink は `lstat` で見て、**リンクも先も消さない**:
    先が通常のファイル（辿れる先）なら、リンクを消しても先の古い中身は残る（`unlink` が消すのはリンク）ので、
    リンクと先のパスを名指しする（#626。#499 ではリンクを消して「消した」と言っていた）。
    `partial` は、今回この出力先を開いた（先を切り詰めた）あとで書けなかったこと——そのとき先に残るのは前の出力ではなく
    今回の書きかけなので、そう名指しする（#662 の CR2-1。前の中身は切り詰めで失われている）。リンクでない普通のファイルでも、
    消せなければ同じく書きかけと名指しする（#689 の A1）。**先の無い壊れたリンクに書いた**ときは、開いたときに先が作られるので、
    作った先（今回の書きかけ）をリンクと先のパスで名指しする（#689 の A3——リンクも先も消さない決まりのまま）。
    先を辿れない（EACCES など）なら、先が前の出力かを確かめられないので同じく名指しする——
    辿れないディレクトリと同じ扱い（#535。リンクを消さないのは、消しても先の古い中身は残るから——先がディレクトリかも分からない）。
    先のパス（辿れたところまで鎖を解いたもの）も名指しする（#625）。
    先がディレクトリ・辿れる先が無い（壊れたリンク・輪になったリンク）なら、この道具の出力ではないので消さずに名指しもしない
    ——ただし表が決まりに反する・書く前に止まったときに限る（先の無い壊れたリンクに書いて途中で失敗したら、上のとおり作った先を名指しする）。
    ELOOP は輪とは限らない——OS の上限より長い輪でない鎖の先に通常のファイルがあれば名指しする（`long_chain`。#689 の A2）。"""
    try:
        mode = out.lstat().st_mode
        if stat.S_ISLNK(mode):
            try:
                mode = out.stat().st_mode
            except OSError as e:
                if e.errno == errno.ELOOP:
                    return long_chain(out, e)  # 輪か、長すぎる鎖か（#689 の A2）
                if e.errno in ABSENT:
                    return None  # 先の無い壊れたリンク——この道具の出力ではない（先を解かない。#662 の 1 パス目 CR1-3）
                target = link_target(out)
                # 長すぎる名前は、鎖を解いた先のパスで見る（途中のどこかの名前が NAME_MAX を超えるなら在りえない——壊れたリンク。
                # 別のリンクを経由しても同じ。#535 の CR1-1・R2-1）
                if absent(target, e):
                    return None  # 壊れたリンク——この道具の出力ではない
                return f"前に作った出力を消せない: {out}（リンクの先を辿れない: {e.strerror}。先: {target}）。今の表から作ったものではない"
            if stat.S_ISREG(mode) and partial:  # 今回切り詰めて書きかけた先——前の出力ではない（#662 の CR2-1）
                return f"書きかけの出力を消せない: {out}（リンクの先に今回の書きかけが残る。先: {link_target(out)}）。完全な出力ではない"
            if stat.S_ISREG(mode):  # 辿れる先の通常のファイル——リンクを消しても先の古い中身は残る（#626）
                return f"前に作った出力を消せない: {out}（リンクの先に前の出力が残る。先: {link_target(out)}）。今の表から作ったものではない"
        if not stat.S_ISREG(mode):
            return None  # ディレクトリなど、この道具の出力でないものは消さない
        out.unlink()
    except OSError as e:
        if e.errno == errno.ELOOP:  # 親のディレクトリのリンクの鎖が輪か、長すぎるか（#689 の A2）
            return long_chain(out, e)
        if absent(out, e):  # 無い（確かめてから消すまでに消えたものを含む）
            return None
        return left(out, e.strerror, partial)
    except ValueError:  # 符号化できない名前など（NUL・U+DC80〜U+DCFF のほかの孤立サロゲート）——その名前のファイルは在りえない（3.12 の `is_file` も無いと読んだ）
        return None
    except Exception as e:  # 想定外の例外でも、消せなかったことを名指しする（「想定外の例外」に化けさせない）
        return left(out, f"{type(e).__name__}: {e}", partial)
    print(f"{out}: 前に作った出力を消した（今の表から作ったものではないため）", file=sys.stderr)
    return None


def stop(out: Path, code: int, partial: bool = False) -> int:
    """前の出力を消して終わる。消せなければ、どの経路でも 2 にして名指しする（1 の「表が決まりに反する」と取り違えない）。
    `partial` は `remove_stale` を見る。"""
    left = remove_stale(out, partial)
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
    problem = name_problem(source)
    if problem:  # 入力のパスの名前が使えない——開く前に読めないと言う（#592・#662 の CR8。CLI からは届かない）
        print(f"{shown(source)}: 読めない（入力のパスの名前が使えない: {problem}）。中身を検査していない", file=sys.stderr)
        return stop(out, 2)
    try:
        problems, rows = feasibility.check_schedule(source)
        if not problems and rows:
            svg = render(rows).encode("utf-8")
    except feasibility.Unreadable as e:
        print(e, file=sys.stderr)
        return stop(out, 2)
    except Exception as e:  # 想定外の例外（巨大なセルの csv.Error など）でも、前の出力を残さない（#286）
        print(f"{source}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        return stop(out, 2)
    if not problems and not rows:
        problems = [f"{source}: 描く工程が 1 行も無い"]
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        print("ガントチャートは作っていない", file=sys.stderr)
        return stop(out, 1)
    opened = False  # 出力先を開いた——開いた時点で（リンクの先も）切り詰められている（#662 の CR2-1）
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as f:
            opened = True
            f.write(svg)
    except OSError as e:  # 書きかけを今の表のものと取り違えないよう消す
        print(f"{out}: 書けない（{e.strerror}）", file=sys.stderr)
        return stop(out, 2, opened)
    except ValueError as e:  # 出力先の名前が符号化できない（NUL・U+DC80〜U+DCFF のほかの孤立サロゲート。#591）——その名前には書けない（#582。CLI からは届かない）
        print(f"{shown(out)}: 書けない（出力先の名前が使えない: {type(e).__name__}: {e}）", file=sys.stderr)
        return stop(out, 2, opened)
    except Exception as e:  # 書く途中の想定外の例外でも、前の出力を消すか名指しする（入口に逃がさない。#499 の 2 パス目）
        print(f"{out}: 書く途中の想定外の例外で止まった（{type(e).__name__}: {e}）", file=sys.stderr)
        return stop(out, 2, opened)
    print(f"{out}: {len(rows)} 工程のガントチャートを書いた")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
