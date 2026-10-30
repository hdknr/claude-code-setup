#!/usr/bin/env python3
"""`schedule-to-gantt.py`（`schedule.csv` → ガントチャートの SVG）の回帰テスト。

    python3 scripts/test-schedule-to-gantt.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。

見るもの:

1. **決定論的に出る**——同じ表から 2 回作ってバイトが一致する。**陽性対照として、日付を 1 日変えた表では
   バイトが変わる**ことも見る（何を渡しても同じものを出す壊れ方と区別するため）。
2. **表の中身が図に出る**——工程の数だけ棒があり、表の順に並び、棒の位置と幅が日付から決まる。
3. **整形式の XML**——工程の名前に `&`・`<`・制御文字が入っても。
4. **決まりに反する表・読めない表からは描かない**（1・2）。**前に作った出力は消す。**
4'. **想定外の例外（128KB 超のセルの `csv.Error`）も 2 で、前の出力を消す。** 出力先に書けないときも
   トレースバックの 1 にせず 2。`-OO`（docstring が無い）で引数なしに呼んでも使い方の誤りとして 2（#286）。
   `main` の外へ逃げた例外は入口が 2 にする。
4''. **前の出力を消せない（書けない・辿れないディレクトリ）ときは、どの経路でも 2 で、残った出力を名指しする**（#499）
   ——表が決まりに反する（1 の経路）・読めない・想定外の例外・書けないの 4 つで。想定外の例外には化けない。
   **陽性対照**: 消せる場所では「消せない」と言わず、出力先が無ければ 1 のまま、出力先がディレクトリなら消さずに 1。
   名前の 1 つが NAME_MAX を超える（在りえない）出力先・親がファイルの出力先（ENOTDIR）は 1 のまま——名前がちょうど 256 バイトの
   出力先も（反対側の境界。#625）。
   符号化できない（NUL・surrogateescape でバイトに戻せない孤立サロゲート——U+D800〜U+DC7F・U+DD00〜U+DFFF——を含む）出力先も
   在りえないので 1 のまま——**CLI からは届かない**（argv に渡らない）ので、同じプロセスの中で `sys.argv` を差し替えて `main` に届かせる（#534）。
   表が正しくて出力先が符号化できない（名前・親のディレクトリの名前）ときは、書く途中の `ValueError` を「書けない」と
   名指しして 2——「書く途中の想定外の例外」にしない（#582。同じく `main` に届かせる）。
   **U+DC80〜U+DCFF の名前は `ValueError` にならない**（バイトに戻せる。CLI から届く）——書けないディレクトリの中の
   `\\udc80.svg` は `OSError` の「書けない（<理由>）」で 2 になり、「出力先の名前が使えない」とは言わない（#591）。
   入力のパスに NUL・バイトに戻せない孤立サロゲートがあるときは、開く前に名前を確かめ、「読めない（入力のパスの名前が使えない:
   NUL を含む／バイトに戻せない文字を含む: <理由>）」で 2——「想定外の例外」にしない（#592・#662 の CR8。同じく `main` に届かせる）。
   前の出力は消す。入力と出力のパスの NUL は、標準エラーに素のバイトではなく `\\x00` と出る（#662 の CR9）。
   パス全体が PATH_MAX を超えるだけの出力先（ファイルは在りうる）は「消せない」と名指しして 2——名前がちょうど NAME_MAX
   （255 バイト）の出力先も（境界。#536）。
   出力先が symlink なら、リンクも先も消さない: 先を辿れない symlink（先がファイルでもディレクトリでも。#535）も、
   辿れる先の通常のファイルを指す symlink（鎖を経由しても。#626）も、リンクと先のパス（鎖を解いた先。辿れないときは辿れたところまで）を名指しして 2
   （表が正しくて書けないときも。先のパスの名指しは #625）。表が正しく書ける辿れる先の symlink は 0 で、先に書く（陽性対照）。
   壊れた symlink（鎖を解いた先のどこかの名前が NAME_MAX を超えるもの——別のリンクを経由しても——を含む）・輪になった symlink（a→b→a。
   #662 の N2）とディレクトリを指す symlink は消さずに 1。
   辿れる先の symlink の先を開いて（切り詰めて）から書けない（ファイルの大きさの上限 `RLIMIT_FSIZE` で書く途中に EFBIG）ときは、
   先に残る今回の書きかけを「書きかけの出力を消せない」とリンクと先のパスで名指しして 2——「前に作った出力」と言わない（#662 の CR2-1）。
   先のパスは名指しする分岐でだけ解く——`os.path.realpath` を壊しても、ディレクトリを指す symlink は 1 のまま（#662 の CR10）。
   書く途中の想定外の例外（`Path.open` を差し替える）も入口に逃がさず、前の出力を消して 2。
   入口の捕捉は、書いたあとの標準出力の例外で見る（`sys.stdout` を差し替える）。
   消す途中の想定外の例外（`Path.lstat` を差し替える）も「消せない」と名指しし、「想定外の例外で止まった」にしない。
5. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**守らないもの**: 見た目（文字が枠からはみ出すか）。ブラウザで開いて目で見る。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
"""
from __future__ import annotations

import os
import re
import resource
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "schedule-to-gantt.py"
SVG = "{http://www.w3.org/2000/svg}"

HEAD = "No,工程,開始,終了,前提\n"
GOOD = (
    "T-001,要件定義,2026-11-02,2026-11-27,\n"
    "T-002,基本設計,2026-11-30,2026-12-25,T-001\n"
    "T-003,予算の合意,2026-12-25,2026-12-25,T-002\n"
)
# 日付を 1 日だけ変えた表（決定論の陽性対照）
SHIFTED = GOOD.replace("2026-11-27", "2026-11-26")


class Result:
    def __init__(self, code: int, output: str, svg: bytes | None, again: bytes | None = None):
        self.code, self.output, self.svg, self.again = code, output, svg, again

    def rects(self) -> list[ET.Element]:
        return [e for e in ET.fromstring(self.svg).iter(f"{SVG}rect") if e.get("data-no")]


def well_formed(r: Result) -> bool:
    try:
        ET.fromstring(r.svg)
        return True
    except (ET.ParseError, TypeError):
        return False


# (名前, 表の中身（None なら作らない）, 前の出力を置くか, 2 回作るか, 判定)
CASES: list[tuple[str, str | bytes | None, bool, bool, Callable[[Result], bool]]] = [
    ("2 回作ってバイトが一致する", HEAD + GOOD, False, True,
     lambda r: r.code == 0 and r.svg is not None and r.svg == r.again),
    ("工程の数と順", HEAD + GOOD, False, False,
     lambda r: r.code == 0 and [e.get("data-no") for e in r.rects()] == ["T-001", "T-002", "T-003"]),
    # 最初の工程は左端、2 つ目は 28 日後（12px/日 → 336px 右）
    ("棒の位置", HEAD + GOOD, False, False,
     lambda r: r.code == 0 and [int(e.get("x")) for e in r.rects()][:2] == [260, 260 + 28 * 12]),
    ("1 日の節目の幅", HEAD + GOOD, False, False, lambda r: r.code == 0 and r.rects()[2].get("width") == "12"),
    ("表の順に並べる（日付順に並べ替えない）",
     HEAD + "T-002,後,2026-12-01,2026-12-02,\nT-001,先,2026-11-01,2026-11-02,\n", False, False,
     lambda r: r.code == 0 and [e.get("data-no") for e in r.rects()] == ["T-002", "T-001"]),
    ("XML の特殊文字", HEAD + 'T-001,"A&B <設計>",2026-11-02,2026-11-03,\n', False, False,
     lambda r: r.code == 0 and well_formed(r) and b"A&amp;B &lt;" in r.svg),
    ("制御文字", HEAD + "T-001,設計\x01,2026-11-02,2026-11-03,\n", False, False,
     lambda r: r.code == 0 and well_formed(r)),
    ("月の境目", HEAD + GOOD, False, False, lambda r: r.code == 0 and b">2026-12</text>" in r.svg),
    ("終了が開始より前は描かない", HEAD + "T-001,a,2026-11-05,2026-11-02,\n", False, False,
     lambda r: r.code == 1 and r.svg is None and "ガントチャートは作っていない" in r.output),
    ("前の出力を消す", HEAD + "T-001,a,2026-11-05,2026-11-02,\n", True, False,
     lambda r: r.code == 1 and r.svg is None and "前に作った出力を消した" in r.output
     and "前に作った出力を消せない" not in r.output),
    ("工程が無い", HEAD, False, False, lambda r: r.code == 1 and r.svg is None and "描く工程が 1 行も無い" in r.output),
    ("読めない表", None, True, False, lambda r: r.code == 2 and r.svg is None),
    # 想定外の例外（128KB 超のセルの csv.Error）も 2 で、前の出力を消す（#286）
    ("巨大なセル", HEAD + "T-001," + "x" * 200_000 + ",2026-11-02,2026-11-03,\n", True, False,
     lambda r: r.code == 2 and r.svg is None and "想定外の例外で止まった（Error: field larger" in r.output
     and "前に作った出力を消した" in r.output and "Traceback" not in r.output),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("時刻を書く", "'<?xml version=\"1.0\" encoding=\"UTF-8\"?>',",
     "'<?xml version=\"1.0\" encoding=\"UTF-8\"?>' + f\"<!-- {__import__('time').time_ns()} -->\",",
     "2 回作ってバイトが一致する"),
    ("開始日から測らない", "return LABEL_W + (day - first).days * DAY_W", "return LABEL_W", "棒の位置"),
    ("棒の幅を 1 日少なく", "bar_w = ((end - start).days + 1) * DAY_W", "bar_w = (end - start).days * DAY_W",
     "1 日の節目の幅"),
    ("日付順に並べ替える", "    spans = [(date.fromisoformat(r[\"開始\"]), date.fromisoformat(r[\"終了\"])) for r in rows]\n",
     "    rows = sorted(rows, key=lambda r: r[\"開始\"])\n"
     "    spans = [(date.fromisoformat(r[\"開始\"]), date.fromisoformat(r[\"終了\"])) for r in rows]\n",
     "表の順に並べる（日付順に並べ替えない）"),
    ("文字を逃がさない", 'return escape(INVALID_XML.sub("", value))', "return value", "XML の特殊文字"),
    ("制御文字を落とさない", 'return escape(INVALID_XML.sub("", value))', "return escape(value)", "制御文字"),
    ("月の境目を描かない", "if day == first or day.day == 1:", "if day == first:", "月の境目"),
    ("検査を通さずに描く", "    if problems:\n        for line in problems:", "    if False:\n        for line in problems:",
     "終了が開始より前は描かない"),
    ("前の出力を消さない", "        out.unlink()\n", "        pass\n", "前の出力を消す"),
    ("空の表を通す", "if not problems and not rows:", "if False:", "工程が無い"),
    ("想定外の例外で前の出力を消さない", "    except Exception as e:  # 想定外の例外（巨大なセルの csv.Error など）でも",
     "    except ImportError as e:  # 想定外の例外（巨大なセルの csv.Error など）でも", "巨大なセル"),
    # 無い（ENOENT）まで「消せない」と読むと、出力先が無いだけで 2 になる（#499）
    ("無いを消せないと読む", "        if absent(out, e):  # 無い（", "        if False:  # 無い（", "終了が開始より前は描かない"),
]

# 想定外の例外は 2（#286）。前の出力を消せないとき・書けないとき・-OO の引数なしは CASES の外で見る。(名前, 壊す前, 壊した後)
ENTRY_MUTATIONS: list[tuple[str, str, str]] = [
    ("入口で想定外の例外を 2 に寄せない", "    except Exception as e:  # 想定外の例外も「判定していない」（2）",
     "    except ImportError as e:  # 想定外の例外も「判定していない」（2）"),
    # ここから #499
    ("消せないのに元の終了コードのまま", "        print(left, file=sys.stderr)\n        return 2\n",
     "        print(left, file=sys.stderr)\n        return code\n"),
    ("消せないことを名指ししない", "        print(left, file=sys.stderr)\n", "        pass\n"),
    ("消せない失敗も無いと読む", "        if absent(out, e):  # 無い（", "        if True:  # 無い（"),
    ("ディレクトリも消そうとする", "        if not stat.S_ISREG(mode):", "        if False:"),
    # 1 パス目の指摘対応（CR3・CR4・CR5）
    ("長すぎる名前を消せないと読む", "    return e.errno == errno.ENAMETOOLONG and any(", "    return False and any("),
    # 2 パス目の指摘対応（V2-1・V2-2・P2-1・P2-2・P2-4）
    ("長すぎるパスも無いと読む", "any(len(os.fsencode(part)) > NAME_MAX for part in out.parts)", "True"),
    # #536: 名前の長さの境界——ちょうど NAME_MAX の名前は在りうる
    ("名前がちょうど NAME_MAX でも在りえないと読む", "part)) > NAME_MAX for part", "part)) >= NAME_MAX for part"),
    ("壊れたリンクも消す", "                    return None  # 壊れたリンク", "                    mode = stat.S_IFREG  # 壊れたリンク"),
    ("書く途中の想定外の例外を逃がす", "    except Exception as e:  # 書く途中の", "    except ImportError as e:  # 書く途中の"),
    # #535: 先を辿れない symlink は消さずに名指しする
    ("辿れない先のリンクを消す", "                return f\"前に作った出力を消せない: {out}（リンクの先を辿れない",
     "                mode = stat.S_IFREG; f\"前に作った出力を消せない: {out}（リンクの先を辿れない"),
    ("辿れない先のリンクを黙って残す", "                return f\"前に作った出力を消せない: {out}（リンクの先を辿れない",
     "                return None; f\"前に作った出力を消せない: {out}（リンクの先を辿れない"),
    ("先の長すぎる名前を出力先の名前で見る", "if absent(target, e):", "if absent(out, e):"),
    ("先の鎖を解かずに 1 段目だけ見る", "    return Path(os.path.realpath(link))", "    return link.parent / os.readlink(link)"),
    # 名指しの先とは別に、壊れたリンクの判定（absent）だけが鎖を解かない形（chainlink.svg の試料が殺す。#591 の周の 2 パス目 CR2-2）
    ("壊れたリンクの判定だけ鎖を解かない", "if absent(target, e):", "if absent(out.parent / os.readlink(out), e):"),
    ("辿れないのがリンクの先だと言わない", "（リンクの先を辿れない: {e.strerror}。先: {target}）", "（{e.strerror}。先: {target}）"),
    # #625: 辿れない先のリンクは、先のパスも名指しする
    ("辿れない先のパスを名指ししない", "（リンクの先を辿れない: {e.strerror}。先: {target}）", "（リンクの先を辿れない: {e.strerror}）"),
    # #626: 辿れる先の通常のファイルを指すリンクも、消さずにリンクと先のパスを名指しする
    ("辿れる先のリンクを消す", "            if stat.S_ISREG(mode):  # 辿れる先", "            if False:  # 辿れる先"),
    ("辿れる先のリンクを黙って残す", "                return f\"前に作った出力を消せない: {out}（リンクの先に前の出力が残る",
     "                return None; f\"前に作った出力を消せない: {out}（リンクの先に前の出力が残る"),
    ("辿れる先のパスを名指ししない", "（リンクの先に前の出力が残る。先: {link_target(out)}）", "（リンクの先に前の出力が残る）"),
    # #625: 名前の長さの反対側の境界——256 バイトの名前は在りえない
    ("名前が NAME_MAX + 1 でも在りうると読む", "part)) > NAME_MAX for part", "part)) > NAME_MAX + 1 for part"),
    ("消す途中の想定外の例外を名指ししない", "    except Exception as e:  # 想定外の例外でも、消せなかった",
     "    except ImportError as e:  # 想定外の例外でも、消せなかった"),
    ("書けないときを捕まえない", "    except OSError as e:  # 書きかけを", "    except ImportError as e:  # 書きかけを"),
    # #534: 符号化できない名前も「無い」と読む分岐（CLI からは届かない）
    ("符号化できない名前を消せないと読む", "    except ValueError:  # 符号化できない", "    except ImportError:  # 符号化できない"),
    # #582: 書く途中の ValueError（符号化できない出力先）を「書けない」と読む分岐
    ("符号化できない出力先を書く途中の想定外の例外と読む", "    except ValueError as e:  # 出力先の名前が符号化できない",
     "    except ImportError as e:  # 出力先の名前が符号化できない"),
    ("符号化できない出力先の型と理由を書かない", "出力先の名前が使えない: {type(e).__name__}: {e}）", "出力先の名前が使えない: ）"),
    ("符号化できない出力先を名指ししない", 'print(f"{shown(out)}: 書けない（出力先の名前が使えない', 'print(f"書けない（出力先の名前が使えない'),
    # #591: U+DC80〜U+DCFF はバイトに戻せる——厳密に符号化して ValueError にすると「出力先の名前が使えない」になる
    ("U+DC80 の名前も符号化できないと読む", "        with out.open(\"wb\") as f:\n",
     "        str(out).encode('utf-8')\n        with out.open(\"wb\") as f:\n"),
    # #592・#662 の CR8: 入力のパスの名前が使えないときは、開く前に「読めない」と言う
    ("入力の名前が使えないを確かめない", "    if problem:  # 入力のパスの名前が使えない", "    if False:  # 入力のパスの名前が使えない"),
    ("入力の名前をすべて使えないと読む", 'return "NUL を含む" if b"\\0" in os.fsencode(path) else None', 'return "NUL を含む"'),
    ("入力の名前の理由を書かない", "入力のパスの名前が使えない: {problem}）", "入力のパスの名前が使えない: ）"),
    ("入力の NUL を使える名前と読む", 'return "NUL を含む" if b"\\0" in os.fsencode(path) else None', "return None"),
    ("入力の孤立サロゲートを使える名前と読む", '    except UnicodeEncodeError as e:\n        return f"バイトに戻せない',
     '    except UnicodeEncodeError as e:\n        return None; f"バイトに戻せない'),
    ("U+DC80 の入力の名前も使えないと読む", 'b"\\0" in os.fsencode(path) else None', 'b"\\0" in str(path).encode("utf-8") else None'),
    # #662 の CR9: パスの NUL を見える形で出す
    ("NUL を書き換えない", 'return str(path).replace("\\0", "\\\\x00")', "return str(path)"),
    ("入力のパスを素のまま出す", 'print(f"{shown(source)}: 読めない', 'print(f"{source}: 読めない'),
    ("出力先のパスを素のまま出す", 'print(f"{shown(out)}: 書けない', 'print(f"{out}: 書けない'),
    # #662 の N2（要確認 #652）: 輪になったリンクは辿れない先ではなく、壊れたリンクと同じく「無い」
    ("輪になったリンクを辿れない先と読む", "ABSENT = (errno.ENOENT, errno.ENOTDIR, errno.EBADF, errno.ELOOP)",
     "ABSENT = (errno.ENOENT, errno.ENOTDIR, errno.EBADF)"),
    # #662 の CR2-1: 先を切り詰めたあとで書けなければ、先に残るのは今回の書きかけ
    ("書きかけを前の出力と名指しする", "            if stat.S_ISREG(mode) and partial:", "            if False:"),
    ("書きかけを黙って残す", '                return f"書きかけの出力を消せない: {out}（',
     '                return None; f"書きかけの出力を消せない: {out}（'),
    ("書けないときに開いたことを渡さない", '        print(f"{out}: 書けない（{e.strerror}）", file=sys.stderr)\n        return stop(out, 2, opened)\n',
     '        print(f"{out}: 書けない（{e.strerror}）", file=sys.stderr)\n        return stop(out, 2)\n'),
    ("開く前に開いたと言う", '        with out.open("wb") as f:\n            opened = True\n',
     '        opened = True\n        with out.open("wb") as f:\n'),
    # #662 の CR10: 先のパスは名指しする分岐でだけ解く
    ("名指ししないリンクでも先を解く", "            try:\n                mode = out.stat().st_mode\n",
     "            link_target(out)\n            try:\n                mode = out.stat().st_mode\n"),
    ("-OO で docstring が無いと落ちる", "__doc__.splitlines()[2] if __doc__ else", "__doc__.splitlines()[2] if True else"),
]


LEFT = "前に作った出力を消せない: "


def entry_problems(scripts: Path, root: Path) -> list[str]:
    """CASES の外のもの。#286: 書けない出力先は 2 で「書けない」と言う・`-OO` の引数なしは使い方の誤りで 2・
    `main` の外へ逃げた例外を入口が 2 にする。#499: 前の出力を消せない場所では、どの経路でも 2 で残った出力を名指しする
    （想定外の例外に化けない）。陽性対照として、出力先がディレクトリなら消さずに 1。"""
    assert_in_tmp(root)
    root.mkdir(parents=True)
    problems = []
    big, good, bad = root / "big.csv", root / "good.csv", root / "bad.csv"
    big.write_text(HEAD + "T-001," + "x" * 200_000 + ",2026-11-02,2026-11-03,\n", encoding="utf-8")
    good.write_text(HEAD + GOOD, encoding="utf-8")
    bad.write_text("bad\n", encoding="utf-8")  # Issue #499 の再現: 見出しが決まりと違う（1 の経路）
    locked, hidden = root / "locked", root / "hidden"
    for directory in (locked, hidden):
        directory.mkdir()
        (directory / "gantt.svg").write_text("<svg>古い</svg>", encoding="utf-8")
    (locked / "ro.svg").write_text("<svg>古い</svg>", encoding="utf-8")
    (locked / "ro.svg").chmod(0o444)
    locked.chmod(0o555)
    hidden.chmod(0o000)  # 辿れない——python3.14 の `is_file` は黙って False を返す
    try:
        if _writable(locked) or _writable(hidden):
            return ["書けないディレクトリに書ける（root で走っている？）——試料が判別しない"]

        def left_named(output: str, name: str, directory: Path) -> bool:
            return f"{LEFT}{directory / name}（" in output and "Traceback" not in output and "PermissionError" not in output

        for label, source, directory, extra in (
            ("消せない前の出力（表が決まりに反する）", bad, locked, "見出し行が決まりと違う"),
            ("消せない前の出力（読めない表）", root / "none.csv", locked, ""),
            ("消せない前の出力（想定外の例外）", big, locked, "想定外の例外で止まった（Error: field larger"),
            ("辿れない場所の前の出力", bad, hidden, "見出し行が決まりと違う"),
        ):
            code, output = generate(scripts, source, directory / "gantt.svg")
            if code != 2 or not left_named(output, "gantt.svg", directory) or extra not in output:
                problems.append(f"{label}: 終了 {code}: {output[-300:]!r}")
        code, output = generate(scripts, good, locked / "new.svg")
        if code != 2 or "書けない（" not in output or "Traceback" in output or LEFT in output:
            problems.append(f"書けない出力先: 終了 {code}: {output[-300:]!r}")
        code, output = generate(scripts, good, locked / "ro.svg")  # 書けず、書けなかった前の出力も消せない
        if code != 2 or "書けない（" not in output or not left_named(output, "ro.svg", locked):
            problems.append(f"書けない出力先の消せない前の出力: 終了 {code}: {output[-300:]!r}")
        # U+DC80〜U+DCFF の名前はバイトに戻せる（CLI から届く）ので ValueError にならず、OSError の「書けない（<理由>）」で 2。
        # 「出力先の名前が使えない」と言わない（#591）。書けないディレクトリに置くのは、Linux（ext4）では 0x80 のバイトの名前に
        # 書けてしまうから——どちらの OS でも OSError（EACCES か EILSEQ）になる
        dc80 = locked / "\udc80.svg"
        code, output = generate(scripts, good, dc80)
        shown = str(dc80).encode("utf-8", "backslashreplace").decode("utf-8")
        if (code != 2 or f"{shown}: 書けない（" not in output or "名前が使えない" in output
                or "想定外の例外" in output or "Traceback" in output):
            problems.append(f"U+DC80 の名前の出力先: 終了 {code}: {output[-300:]!r}")
    finally:
        hidden.chmod(0o755)
        locked.chmod(0o755)
        (locked / "ro.svg").chmod(0o644)
    if not (locked / "gantt.svg").is_file() or not (hidden / "gantt.svg").is_file():
        problems.append("消せないはずの前の出力が消えた——試料が判別しない")
    # 陽性対照: 出力先がディレクトリなら、この道具の出力ではないので消さずに 1
    (root / "dir.svg").mkdir()
    code, output = generate(scripts, bad, root / "dir.svg")
    if code != 1 or not (root / "dir.svg").is_dir() or LEFT in output:
        problems.append(f"出力先がディレクトリ: 終了 {code}: {output[-300:]!r}")
    # 名前の 1 つが長すぎる出力先——その名前のファイルは在りえないので「無い」。1 のまま（CR3）。
    # ちょうど 256 バイト（NAME_MAX + 1）の名前も——反対側の境界（`> NAME_MAX` を `> NAME_MAX + 1` にすると 2 になる。#625）
    for size in (304, 256):  # 304 は今までの試料（"a" * 300 + ".svg"）
        code, output = generate(scripts, bad, root / ("a" * (size - 4) + ".svg"))
        if code != 1 or LEFT in output:
            problems.append(f"長すぎる名前（{size} バイト）の出力先: 終了 {code}: {output[-300:]!r}")
    def deep_output(base: Path, name: str) -> Path:
        """`base` の下に 200 バイトの名前のディレクトリを 25 段掘り（パス全体が PATH_MAX を超える）、`name` の前の出力を置く。
        素のパスでは辿れないので、ディレクトリの記述子から相対に作る。"""
        deep, fd = base, os.open(base, os.O_RDONLY)
        try:
            for _ in range(25):
                os.mkdir("d" * 200, dir_fd=fd)
                child = os.open("d" * 200, os.O_RDONLY, dir_fd=fd)
                os.close(fd)
                fd, deep = child, deep / ("d" * 200)
            os.close(os.open(name, os.O_WRONLY | os.O_CREAT, 0o644, dir_fd=fd))
        finally:
            os.close(fd)
        return deep / name

    # パス全体が PATH_MAX（Linux 4096・macOS 1024）を超えるだけの出力先——ファイルは在りうるので名指しして 2（P2-1）。
    # 名前がちょうど NAME_MAX（255 バイト）の出力先も在りうる——境界（`> NAME_MAX` を `>=` にすると 1 になる。#536）
    edge = root / "edge"
    edge.mkdir()
    for label, out in (("長すぎるパスの前の出力", deep_output(root, "gantt.svg")),
                       ("長すぎるパスの、名前がちょうど NAME_MAX の前の出力", deep_output(edge, "g" * 251 + ".svg"))):  # 255 バイト
        code, output = generate(scripts, bad, out)
        if code != 2 or f"{LEFT}{out}（" not in output:
            problems.append(f"{label}: 終了 {code}: {output[-200:]!r}")
    # 親がファイルの出力先（ENOTDIR）——無いので 1 のまま（V2-1）
    (root / "afile").write_text("", encoding="utf-8")
    code, output = generate(scripts, bad, root / "afile" / "x.svg")
    if code != 1 or LEFT in output:
        problems.append(f"親がファイルの出力先: 終了 {code}: {output[-300:]!r}")
    # 壊れた symlink・ディレクトリを指す symlink——この道具の出力ではないので消さずに 1（V2-2・P2-4）
    (root / "broken.svg").symlink_to(root / "nowhere.svg")
    (root / "adir").mkdir()
    (root / "dirlink.svg").symlink_to(root / "adir")
    (root / "longlink.svg").symlink_to("b" * 300)  # 先の名前が NAME_MAX を超える——在りえない先の壊れたリンク（#535 の CR1-1）
    (root / "mid.svg").symlink_to("b" * 300)
    (root / "chainlink.svg").symlink_to("mid.svg")  # 別のリンクを経由して在りえない先に着く（R2-1）
    # 輪になったリンク（a→b→a）——辿ると ELOOP。辿れない先ではなく、壊れたリンクと同じく「無い」（#662 の N2。要確認 #652）
    (root / "loopa.svg").symlink_to("loopb.svg")
    (root / "loopb.svg").symlink_to("loopa.svg")
    for name in ("broken.svg", "dirlink.svg", "longlink.svg", "chainlink.svg", "loopa.svg"):
        code, output = generate(scripts, bad, root / name)
        if code != 1 or LEFT in output or "前に作った出力を消した" in output or not (root / name).is_symlink():
            problems.append(f"消さない symlink {name}: 終了 {code}: {output[-300:]!r}")
    if not (root / "loopb.svg").is_symlink():
        problems.append("輪になったリンクのもう片方が消えた")
    # 先を辿れない symlink——先が前の出力かを確かめられない（先の古い中身は残り、先がディレクトリかも分からない）ので、
    # リンクを消さずに名指しして 2（#535。#499 の CR4 で「リンクを消して 1」にしていたのを改めた）。
    # 先がファイル・ディレクトリ（表が決まりに反する経路）と、表が正しくて書けない経路で、2・リンクの名指し・リンクと先が残る・
    # 「消した」と traceback が出ないことを見る
    shut = root / "shut"
    shut.mkdir()
    (shut / "g.svg").write_text("<svg>古い</svg>", encoding="utf-8")
    (shut / "d.svg").mkdir()
    (root / "far").mkdir()
    (root / "far" / "real.svg").write_text("<svg>古い</svg>", encoding="utf-8")
    (shut / "c.svg").symlink_to(Path("..") / "far" / "real.svg")  # shut の中のリンク——辿れないので、名指しする先はここで止まる
    for label, name, target, source, extra in (
        ("辿れない先の symlink", "link.svg", "g.svg", bad, "見出し行が決まりと違う"),
        ("辿れない先がディレクトリの symlink", "dlink.svg", "d.svg", bad, "見出し行が決まりと違う"),
        ("辿れない先の symlink（表が正しい）", "glink.svg", "g.svg", good, "書けない（"),
        ("辿れない先の symlink（先の中にまたリンク）", "clink.svg", "c.svg", bad, "見出し行が決まりと違う"),
    ):
        link = root / name
        link.symlink_to(shut / target)
        shut.chmod(0o000)
        try:
            code, output = generate(scripts, source, link)
        finally:
            shut.chmod(0o755)
        # 先のパス（辿れたところまで鎖を解いたもの）も名指しする（#625）——shut の中のリンク（c.svg）は解かずにそこで止まる
        # （期待値は shut を開けたあとに作るので、shut までを解き、名前は解かない）
        stopped = Path(os.path.realpath(shut)) / target
        if (code != 2 or f"{LEFT}{link}（リンクの先を辿れない: " not in output or extra not in output
                or f"。先: {stopped}）" not in output
                or "前に作った出力を消した" in output or "Traceback" in output
                or not link.is_symlink() or not (shut / target).exists()):
            problems.append(f"{label}: 終了 {code}: {output[-300:]!r}")
    if (shut / "g.svg").read_text(encoding="utf-8") != "<svg>古い</svg>" or not (shut / "d.svg").is_dir():
        problems.append("辿れない先の symlink の先が変わった——先に触っている")
    # 辿れる先の通常のファイルを指す symlink（鎖を経由しても）——リンクを消しても先の古い中身は残るので、リンクも先も消さずに
    # リンクと先のパス（鎖を解いた先）を名指しして 2（#626。#499 では「リンクを消して 1」だった）。表が正しくて書けない（先が書けない）経路も
    kept = root / "kept"
    kept.mkdir()
    for target in ("g.svg", "ro.svg"):
        (kept / target).write_text("<svg>古い</svg>", encoding="utf-8")
    (kept / "ro.svg").chmod(0o444)
    (root / "rlink.svg").symlink_to(kept / "g.svg")
    (root / "rmid.svg").symlink_to(kept / "g.svg")
    (root / "rchain.svg").symlink_to("rmid.svg")
    (root / "rolink.svg").symlink_to(kept / "ro.svg")
    try:
        for label, name, target, source, extra in (
            ("辿れる先の symlink", "rlink.svg", "g.svg", bad, "見出し行が決まりと違う"),
            ("辿れる先の symlink（鎖）", "rchain.svg", "g.svg", bad, "見出し行が決まりと違う"),
            ("辿れる先の symlink（表が正しく、先が書けない）", "rolink.svg", "ro.svg", good, "書けない（"),
        ):
            link = root / name
            code, output = generate(scripts, source, link)
            named = f"{LEFT}{link}（リンクの先に前の出力が残る。先: {os.path.realpath(kept / target)}）"
            if (code != 2 or named not in output or extra not in output
                    or "前に作った出力を消した" in output or "Traceback" in output or not link.is_symlink()
                    or (kept / target).read_text(encoding="utf-8") != "<svg>古い</svg>"):
                problems.append(f"{label}: 終了 {code}: {output[-300:]!r}")
    finally:
        (kept / "ro.svg").chmod(0o644)
    # 陽性対照: 表が正しく書けるなら、辿れる先の symlink は 0 で先に書く（リンクは残る）
    code, output = generate(scripts, good, root / "rlink.svg")
    if (code != 0 or not (root / "rlink.svg").is_symlink() or LEFT in output
            or not (kept / "g.svg").read_text(encoding="utf-8").startswith("<?xml")):
        problems.append(f"辿れる先の symlink（表が正しい）: 終了 {code}: {output[-300:]!r}")
    # 先を開いて（切り詰めて）から書けない——ファイルの大きさの上限（RLIMIT_FSIZE）を 300 バイトにして、書く途中で EFBIG にする
    # （CPython は SIGXFSZ を無視するので OSError になる。図は 300 バイトより大きい）。先に残るのは今回の書きかけで、前の出力ではないので、
    # 「書きかけの出力を消せない」とリンクと先のパスを名指しして 2——「前に作った出力」「今の表から作ったものではない」と言わない（#662 の CR2-1）。
    # 開く前に書けない（先が書けない rolink.svg）ときは「前の出力が残る」のまま（上の試料）
    (kept / "half.svg").write_text("<svg>古い</svg>", encoding="utf-8")
    (root / "hlink.svg").symlink_to(kept / "half.svg")
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), str(good), str(root / "hlink.svg")],
                          capture_output=True, text=True, cwd=root, preexec_fn=_limit_file_size)
    half = (kept / "half.svg").read_bytes()
    named = (f"書きかけの出力を消せない: {root / 'hlink.svg'}（リンクの先に今回の書きかけが残る。"
             f"先: {os.path.realpath(kept / 'half.svg')}）。完全な出力ではない")
    # 先が今回の書きかけであること（XML の宣言で始まり、上限で切れている）も見る——上限が効かずに書けたなら、この試料は何も判別しない
    if (proc.returncode != 2 or named not in proc.stderr or "書けない（" not in proc.stderr or LEFT in proc.stderr
            or "今の表から作ったものではない" in proc.stderr or "Traceback" in proc.stderr
            or not (root / "hlink.svg").is_symlink() or not half.startswith(b"<?xml") or len(half) > FILE_SIZE_LIMIT):
        problems.append(f"書きかけを残したリンクの先: 終了 {proc.returncode}: 先 {len(half)} バイト: {proc.stderr[-300:]!r}")

    def injected(method: str, source: Path, name: str) -> subprocess.CompletedProcess:
        """出力先 `build/<name>` について、そのパスの `Path.<method>` だけを差し替えて
        RuntimeError を起こす（python3.12 の `resolve` も stat を呼ぶので絞る）。"""
        script = str(scripts / TARGET)
        inject = ("import pathlib, runpy, sys\n"
                  f"real = pathlib.Path.{method}\n"
                  "def boom(self, *a, **k):\n"
                  f"    if self.name == {name!r}:\n        raise RuntimeError('boom')\n"
                  "    return real(self, *a, **k)\n"
                  f"pathlib.Path.{method} = boom\n"
                  f"sys.argv = [{script!r}, {str(source)!r}, {str(root / 'build' / name)!r}]\n"
                  f"runpy.run_path({script!r}, run_name='__main__')\n")
        return subprocess.run([sys.executable, "-I", "-c", inject], capture_output=True, text=True, cwd=root)

    # 消す途中の想定外の例外も「消せない」と名指しする——「想定外の例外で止まった」に化けない（CR5）
    proc = injected("lstat", bad, "y.svg")
    if (proc.returncode != 2 or f"{LEFT}{root / 'build' / 'y.svg'}（RuntimeError: boom）" not in proc.stderr
            or "想定外の例外で止まった" in proc.stderr or "Traceback" in proc.stderr):
        problems.append(f"消す途中の想定外の例外: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    # 書く途中の想定外の例外も入口に逃がさず、前の出力を消して 2（P2-2）。書く口は `Path.open`（#662 で `write_bytes` から変えた）
    (root / "build").mkdir(exist_ok=True)
    (root / "build" / "w.svg").write_text("<svg>古い</svg>", encoding="utf-8")
    proc = injected("open", good, "w.svg")
    if (proc.returncode != 2 or "書く途中の想定外の例外で止まった（RuntimeError: boom）" not in proc.stderr
            or "前に作った出力を消した" not in proc.stderr or (root / "build" / "w.svg").exists() or "Traceback" in proc.stderr):
        problems.append(f"書く途中の想定外の例外: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    # main の外へ逃げた例外（書いたあとの標準出力）は、入口が 2 にする（トレースバックの 1 にしない）
    script = str(scripts / TARGET)
    inject = ("import runpy, sys\n"
              "class Shut:\n    def write(self, s):\n        raise RuntimeError('boom')\n    def flush(self):\n        pass\n"
              "sys.stdout = Shut()\n"
              f"sys.argv = [{script!r}, {str(good)!r}, {str(root / 'build' / 'z.svg')!r}]\n"
              f"runpy.run_path({script!r}, run_name='__main__')\n")
    proc = subprocess.run([sys.executable, "-I", "-c", inject], capture_output=True, text=True, cwd=root)
    if proc.returncode != 2 or "想定外の例外で止まった（RuntimeError: boom" not in proc.stderr or "Traceback" in proc.stderr:
        problems.append(f"main の外へ逃げた例外: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    # 符号化できない出力先（NUL・バイトに戻せない孤立サロゲート——U+DC80〜U+DCFF は除く。#591）——その名前のファイルは在りえないので
    # 「無い」。1 のまま（#534）。CLI からは届かない（argv に NUL は渡らず、孤立サロゲートは U+DC80〜U+DCFF の形でしか渡らない）ので、
    # 同じプロセスの中で sys.argv を差し替えて main に届かせる
    for label, name in (("NUL", "x\0.svg"), ("単独のサロゲート", "\ud800.svg")):
        inject = ("import runpy, sys\n"
                  f"sys.argv = [{script!r}, {str(bad)!r}, {str(root / name)!r}]\n"
                  f"runpy.run_path({script!r}, run_name='__main__')\n")
        proc = subprocess.run([sys.executable, "-I", "-c", inject], capture_output=True, text=True, cwd=root)
        if (proc.returncode != 1 or LEFT in proc.stderr or "見出し行が決まりと違う" not in proc.stderr
                or "Traceback" in proc.stderr):
            problems.append(f"符号化できない出力先（{label}）: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    # 表が正しく、出力先が符号化できない——書く途中の ValueError も「書けない」と名指しして 2。「想定外の例外」にしない（#582）。
    # 親のディレクトリの名前に NUL があると mkdir で、名前の側なら open で起きる
    for label, name, kind in (("NUL", "x\0.svg", "ValueError"), ("単独のサロゲート", "\ud800.svg", "UnicodeEncodeError"),
                              ("親に NUL", "d\0/gantt.svg", "ValueError")):
        inject = ("import runpy, sys\n"
                  f"sys.argv = [{script!r}, {str(good)!r}, {str(root / name)!r}]\n"
                  f"runpy.run_path({script!r}, run_name='__main__')\n")
        proc = subprocess.run([sys.executable, "-I", "-c", inject], capture_output=True, text=True, cwd=root)
        # 出力先と、例外の型と理由まで名指しする（落ちても緑にならないように。#582 の 1 パス目 CR1・2 パス目 CR2-1）。
        # 標準エラーは単独のサロゲートを backslashreplace で書くので、期待する出力先も同じ形にする
        # NUL は素のバイトではなく `\x00` と出す（#662 の CR9）
        shown = str(root / name).replace("\0", "\\x00").encode("utf-8", "backslashreplace").decode("utf-8")
        named = re.search(re.escape(shown) + rf": 書けない（出力先の名前が使えない: {kind}: [^）\n]+）", proc.stderr)
        if (proc.returncode != 2 or not named or "想定外の例外" in proc.stderr or "\0" in proc.stderr
                or LEFT in proc.stderr or "Traceback" in proc.stderr):
            problems.append(f"符号化できない出力先に書く（{label}）: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    # 入力のパスに NUL・バイトに戻せない孤立サロゲート——開く前に名前を確かめ、「読めない（入力のパスの名前が使えない: <理由>）」と
    # 言って 2。「想定外の例外」にしない。前の出力は消す（#592・#662 の CR8。CLI からは届かないので main に届かせる）。
    # NUL は素のバイトではなく `\x00` と出す（#662 の CR9）
    for label, name, kind in (("NUL", "x\0.csv", "NUL を含む"),
                              ("単独のサロゲート", "\ud800.csv", "バイトに戻せない文字を含む: [^）\n]+")):
        stale = root / "src-stale.svg"
        stale.write_text("<svg>古い</svg>", encoding="utf-8")
        inject = ("import runpy, sys\n"
                  f"sys.argv = [{script!r}, {str(root / name)!r}, {str(stale)!r}]\n"
                  f"runpy.run_path({script!r}, run_name='__main__')\n")
        proc = subprocess.run([sys.executable, "-I", "-c", inject], capture_output=True, text=True, cwd=root)
        shown = str(root / name).replace("\0", "\\x00").encode("utf-8", "backslashreplace").decode("utf-8")
        named = re.search(re.escape(shown) + rf": 読めない（入力のパスの名前が使えない: {kind}）。中身を検査していない", proc.stderr)
        if (proc.returncode != 2 or not named or "想定外の例外" in proc.stderr or stale.exists() or "\0" in proc.stderr
                or "前に作った出力を消した" not in proc.stderr or "Traceback" in proc.stderr):
            problems.append(f"名前の使えない入力（{label}）: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    # 陽性対照: 名前の使える入力（U+DC80 も——バイトに戻せる。#591）で読む途中に ValueError が出たら、今までどおり「想定外の例外」。
    # 名前のせいにしない（`Path.read_text` を差し替えて起こす。名前の検査を外す・厳密に符号化する変異を殺す）
    for label, name in (("ASCII", "v.csv"), ("U+DC80", "\udc80.csv")):
        inject = ("import pathlib, runpy, sys\n"
                  "real = pathlib.Path.read_text\n"
                  "def boom(self, *a, **k):\n"
                  f"    if self.name == {name!r}:\n        raise ValueError('boom')\n"
                  "    return real(self, *a, **k)\n"
                  "pathlib.Path.read_text = boom\n"
                  f"sys.argv = [{script!r}, {str(root / name)!r}, {str(root / 'build' / 'v.svg')!r}]\n"
                  f"runpy.run_path({script!r}, run_name='__main__')\n")
        proc = subprocess.run([sys.executable, "-I", "-c", inject], capture_output=True, text=True, cwd=root)
        if (proc.returncode != 2 or "想定外の例外で止まった（ValueError: boom）" not in proc.stderr
                or "名前が使えない" in proc.stderr or "Traceback" in proc.stderr):
            problems.append(f"名前の使える入力の ValueError（{label}）: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    # 先のパスは名指しする分岐でだけ解く（#662 の CR10）——`os.path.realpath` を壊しても、名指ししないディレクトリを指すリンクは
    # 1 のまま（解いていれば「消せない（RuntimeError: boom）」の 2 になる）。陽性対照: 名指しする辿れる先のリンクでは壊れが届く
    for label, name, expect in (("ディレクトリを指すリンク", "dirlink.svg", 1), ("辿れる先のリンク（陽性対照）", "rlink.svg", 2)):
        inject = ("import os, runpy, sys\n"
                  "real = os.path.realpath\n"
                  "def boom(path, *a, **k):\n"
                  f"    if os.fspath(path).endswith({name!r}):\n        raise RuntimeError('boom')\n"
                  "    return real(path, *a, **k)\n"
                  "os.path.realpath = boom\n"
                  f"sys.argv = [{script!r}, {str(bad)!r}, {str(root / name)!r}]\n"
                  f"runpy.run_path({script!r}, run_name='__main__')\n")
        proc = subprocess.run([sys.executable, "-I", "-c", inject], capture_output=True, text=True, cwd=root)
        reached = f"{LEFT}{root / name}（RuntimeError: boom）" in proc.stderr
        if proc.returncode != expect or reached != (expect == 2) or "Traceback" in proc.stderr:
            problems.append(f"先を解く分岐（{label}）: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    proc = subprocess.run([sys.executable, "-I", "-OO", str(scripts / TARGET)], capture_output=True, text=True, cwd=root)
    if proc.returncode != 2 or "usage:" not in proc.stderr or "Traceback" in proc.stderr:
        problems.append(f"-OO の引数なし: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    return problems


FILE_SIZE_LIMIT = 300


def _limit_file_size() -> None:
    """子のファイルの大きさの上限を `FILE_SIZE_LIMIT` バイトにする（それを超える書き込みは EFBIG）。"""
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_SIZE_LIMIT, resource.RLIM_INFINITY))


def _writable(directory: Path) -> bool:
    try:
        (directory / "probe").write_text("", encoding="utf-8")
    except OSError:
        return False
    (directory / "probe").unlink()
    return True


failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def generate(scripts: Path, source: Path, out: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), str(source), str(out)],
                          capture_output=True, text=True, cwd=source.parent)
    return proc.returncode, proc.stdout + proc.stderr


def run_case(scripts: Path, root: Path, content, stale: bool, twice: bool) -> Result:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    source, out = root / "schedule.csv", root / "build" / "gantt.svg"
    if isinstance(content, bytes):
        source.write_bytes(content)
    elif content is not None:
        source.write_text(content, encoding="utf-8")
    if stale:
        out.parent.mkdir(parents=True)
        out.write_text("<svg>古い</svg>", encoding="utf-8")
    code, output = generate(scripts, source, out)
    svg = out.read_bytes() if out.is_file() else None
    again = None
    if twice:
        second = root / "again.svg"
        generate(scripts, source, second)
        again = second.read_bytes() if second.is_file() else None
    return Result(code, output, svg, again)


def run_all(scripts: Path, work: Path) -> dict[str, Result]:
    return {name: run_case(scripts, work / f"case{i}", content, stale, twice)
            for i, (name, content, stale, twice, _) in enumerate(CASES)}


def as_expected(name: str, result: Result) -> bool:
    judge = next(case for case in CASES if case[0] == name)[4]
    try:
        return judge(result)
    except (ET.ParseError, TypeError, IndexError):
        return False


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="gantt-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        results = run_all(scripts, tmp_path / "work")
        for name, result in results.items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result.code} {result.output[-300:]}")

        # 決定論の陽性対照: 日付を 1 日変えた表ではバイトが変わる
        shifted = run_case(scripts, tmp_path / "shifted", HEAD + SHIFTED, False, False)
        check("日付を変えてもバイトが変わらない（何を渡しても同じものを出している）",
              shifted.code == 0 and shifted.svg != results["2 回作ってバイトが一致する"].svg)

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            mutated_results = run_all(mutated, tmp_path / f"mutwork{index}")
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）",
                  not as_expected(killer, mutated_results[killer]), mutated_results[killer].output[-300:])

        problems = entry_problems(scripts, tmp_path / "entry")
        check("消せない前の出力・書けない出力先・-OO の引数なし・逃げた例外で期待どおりでない", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(ENTRY_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"entry-mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}", bool(entry_problems(mutated, tmp_path / f"entry-mutwork{index}")))

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(ENTRY_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
