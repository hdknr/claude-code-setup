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
4'. **想定外の例外（128KB 超のセルの `csv.Error`）も 2 で、前の出力を消す。** 前の出力を消せない・出力先に書けないときも
   トレースバックの 1 にせず 2。`-OO`（docstring が無い）で引数なしに呼んでも使い方の誤りとして 2（#286）。
5. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**守らないもの**: 見た目（文字が枠からはみ出すか）。ブラウザで開いて目で見る。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
"""
from __future__ import annotations

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
     lambda r: r.code == 1 and r.svg is None and "前に作った出力を消した" in r.output),
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
]

# 想定外の例外は 2（#286）。前の出力を消せないとき・書けないとき・-OO の引数なしは CASES の外で見る。(名前, 壊す前, 壊した後)
ENTRY_MUTATIONS: list[tuple[str, str, str]] = [
    ("入口で想定外の例外を 2 に寄せない", "    except Exception as e:  # 想定外の例外も「判定していない」（2）",
     "    except ImportError as e:  # 想定外の例外も「判定していない」（2）"),
    ("書けないときを捕まえない", "    except OSError as e:  # 書きかけを", "    except ImportError as e:  # 書きかけを"),
    ("-OO で docstring が無いと落ちる", "__doc__.splitlines()[2] if __doc__ else", "__doc__.splitlines()[2] if True else"),
]


def entry_problems(scripts: Path, root: Path) -> list[str]:
    """CASES の外の 3 つ（#286）:
    前の出力を消せない場所（書けないディレクトリ）で巨大なセル——内側の捕捉が消そうとして `PermissionError` を投げても、
    入口が 2 にする（トレースバックの 1 にしない）。書けない出力先は 2 で「書けない」と言う。`-OO` の引数なしは使い方の誤りで 2。"""
    assert_in_tmp(root)
    root.mkdir(parents=True)
    problems = []
    big, good = root / "big.csv", root / "good.csv"
    big.write_text(HEAD + "T-001," + "x" * 200_000 + ",2026-11-02,2026-11-03,\n", encoding="utf-8")
    good.write_text(HEAD + GOOD, encoding="utf-8")
    locked = root / "locked"
    locked.mkdir()
    (locked / "gantt.svg").write_text("<svg>古い</svg>", encoding="utf-8")
    locked.chmod(0o555)
    try:
        if _writable(locked):
            return ["書けないディレクトリに書ける（root で走っている？）——試料が判別しない"]
        code, output = generate(scripts, big, locked / "gantt.svg")
        if code != 2 or "想定外の例外" not in output or "Traceback" in output:
            problems.append(f"消せない前の出力: 終了 {code}: {output[-300:]!r}")
        code, output = generate(scripts, good, locked / "new.svg")
        if code != 2 or "書けない（" not in output or "Traceback" in output:
            problems.append(f"書けない出力先: 終了 {code}: {output[-300:]!r}")
    finally:
        locked.chmod(0o755)
    proc = subprocess.run([sys.executable, "-I", "-OO", str(scripts / TARGET)], capture_output=True, text=True, cwd=root)
    if proc.returncode != 2 or "usage:" not in proc.stderr or "Traceback" in proc.stderr:
        problems.append(f"-OO の引数なし: 終了 {proc.returncode}: {proc.stderr[-300:]!r}")
    return problems


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
        check("消せない前の出力・書けない出力先・-OO の引数なしで 2 にならない", not problems, "; ".join(problems))
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
