#!/usr/bin/env python3
"""仕様レビューを抜ける条件のうち、**機械で決まる条件 1** だけを判定する。

usage: python3 check-spec-exit.py <qa.csv> <仕様のディレクトリ> [--docs <docs ディレクトリ> [--upto <n>] [--screen-spec <screen-spec のプラグインの根>]]

**条件の正は `references/spec-exit.md` である**（このプラグインの中にある）。
条件 1 は「Q&A 表に、仕様に反映した状態でない行が 0 件で、仕様に未決定の印が 0 件」。
**Q&A 表は 2 つ見る**——引数の共有の表と、仕様のディレクトリの中の内部の表（`check-qa-csv.py` の `INTERNAL_NAME`。
あれば）。内部の表の行も、反映していなければ条件 1 を止める（資料には載らないが、開発者が決めた記録が要る。#339）。
**内部の表は未決定の印を探すファイルから外す**——表として検査するもので、質問の文に印の語が入りうる。
仕様のファイルの数にも数えない（内部の表だけがあっても、仕様は書いていない）。
**形式検査のモデル（仕様のディレクトリの中の `formal/`）も見ない**——Formal Checker が仕様から書き起こした写しで、
spec-review はその記録に置いた前提（未決定のことを含む）を書き残す。未決定は Q&A 表と仕様の本文で決まる
（判別は `merge-versions.py` の `is_formal`。`references/tree.md` の「形式検査のモデル」。#908）。仕様のファイルの数にも数えない。
`formal` という名前のファイル（ディレクトリでない）は仕様のファイルとして見る。
**画面の表（`requirements/screens/`）があれば、画面の関門も条件 1 に入れる**（#1097）——`--docs` で正本の `docs` を渡すと、
同梱の `screen-gate.py` の `check` を当て（`--upto`・`--screen-spec` もそのまま渡す）、**1 は条件 1 を満たさない（1）、2・4（判定していない・
screen-spec が無いなどで止めた）は条件 1 を判定していない（2）**。画面の表が無ければ何も足さない（出力も変えない）。
**`--docs` を渡さずに、仕様のディレクトリの親（重ねた全体の根）に画面の表があれば 2**——画面の関門を判定していない。
画面の表とは何か・screen-spec の見つけ方・終了コードの読み替えは `screen-gate.py` の docstring を正とする。
**`--docs` の `docs` と、引数の Q&A 表・仕様のディレクトリが同じ正本から重ねたものかは見ない**（スキルは同じ `docs` から重ねた直後に呼ぶ）。
**条件 2〜5 はこのスクリプトでは判定しない**——判定役の報告で決まる（`spec-review` の本文）。
**0 で終わっても「抜けた」ではない。** 出力もそう言う。

- Q&A 表は **`qa-to-pptx.py` の `read_rows` で読み**、**状態が `check-qa-csv.py` の `REFLECTED`
  （`反映済み`・`暫定反映`）でない行**を数える。**PPTX に載る行とは別の定義**——暫定の回答で反映した行は
  資料には載る（確認してもらうため）が、仕様には反映済みなので条件 1 を止めない（#325）。
  **`REFLECTED` に無い状態は数える側に倒れる**（決まりに状態が増えても、反映が残っている行を黙って落とさない）。
  暫定の行（判別は `check-qa-csv.py` の `is_provisional`）は件数を出す（要求確定のサインオフの前に確認が要る。`references/signoff-tags.md`）。
  Q&A 表の列検査（`check-qa-csv.py`）も `read_rows` で掛かる。
- **テストケースの番号が重複していたら 1**（#1297）——**同じ重ねた全体の仕様（`spec/`）の `.md` の中で**、見出しの先頭のセルが `CASE_HEADER`（`テストケース`・`test case`・`ケース番号`・`TC` など。正規表現は `references/spec-exit.md`）に当たる表の、データ行の先頭のセルが
  番号（`CASE_NUMBER` の形）である行が、同じファイルでも別のファイルでも 2 つ以上あれば、番号と出た場所（`ファイル:行`）を全部名指しする。
  **中間表現のケースの `ref` の照合（`scaffold.py` の `check_ref`。#465）は番号が原文に在るかだけを見る**ので、重複は通り、どちらの行を写したのかが決まらない。
  **数えるのは重ねた後の全体**——後の版が同じファイルを置き換えたなら、置き換えられた前の版の行は全体に無いので重複に数えない
  （重ね方は `merge-versions.py`。このスクリプトは重ねない）。番号の形・どの列を番号と読むか・読まないものは `references/spec-exit.md` の
  「テストケースの番号の重複」を正とする。重複が無い仕様では出力も終了コードも変わらない。
- 未決定の印（`MARKERS`）と、印に当たらない語（`NOT_MARKERS`）は `references/spec-exit.md` の写しで、
  **写しがずれていないかはこのリポジトリの `scripts/test-check-spec-exit.py` が突き合わせて見る**。

終了コード:

- 0: 条件 1 を満たす
- 1: 条件 1 を満たさない（反映した状態でない行と、印のある箇所を**全部** 1 行ずつ出す）。
  **Q&A 表が列検査を通らないときもここ**（決まりに反する表は、確定していない）。**画面の関門（`--docs`）が 1 のときもここ**（#1097）
- 2: 判定していない——引数の誤り・Q&A 表が読めない・想定外の例外（128KB を超えるセルの `csv.Error` など。#286）・
  仕様のディレクトリが無い・
  仕様のファイルが 1 つも無い（**書いていない仕様は、確定していない**ので、0 にはしない）・
  **図（`FIGURE_SUFFIXES`）以外に読めないファイルがある**（UTF-16・`.xlsx` など。見ていないものを
  「印 0 件」と言わない）・**読めた仕様のファイルが 1 つも無い**（図だけ）・
  **読めた仕様のファイルがどれも中身が空**（空白・改行だけを含む。**中身のあるファイルが 1 つでもあれば止めない**。
  見た仕様に中身が 0 なら、書いていない仕様と同じ。#291）。
  **NUL を含むファイルは読めない側に数える**——ASCII だけの UTF-16 は UTF-8 として*読めてしまう*
  （NUL は UTF-8 として有効）ので、復号の成否だけでは見分けられない。
  **画面の関門が 2・4**（判定していない・画面の表があるのに screen-spec が無いなどで止めた）・**`--docs` が無いのに重ねた全体に画面の表がある**（#1097）。
  **印のある箇所が別に見つかったら 1 を優先する**（読めないファイルがあっても、満たさないことは確か）

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。

**この判定が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **図（`FIGURE_SUFFIXES`）の中の印** | 図を置くことがあるので落とさない。**見なかったファイルは件数と名前を出す**。図以外の読めないファイルは 2 にする |
| **印を使わずに書いた未決定**（「あとで決める」「検討中」） | 言い回しは列挙しきれない。判定役（Red Team）が条件 2・3 で見る |
| **ドット始まりのファイル・ディレクトリの中** | `.git` などを見ないため |
| **テストケースの表以外の先頭のセル（見出しが `ID`・`No`・`項番` の表は、テストケースの表でも読まない）・先頭のセル以外の番号・`.md` 以外のファイルの番号（`.MD` を含む）・フェンスのコードブロックの中の番号・引用や先頭の `|` の無い表・`1-1`・`TC001`・`TC-1.1` のような形の外の番号** | 番号を振る場所の決まりはテストケースの表の先頭のセルだけ（`references/spec-exit.md`）。ほかを読むと、Q&A・NFR・決定表の行の番号を並べた表や本文中の言及（`F1-5b を参照`）を重複に数える。**逆に、4 字下げのコードブロックと HTML コメントの中の表は、読んでしまう（数える）** |
| **番号の形に当たらない行の識別子**（`1`・`あ`・`No.3` など） | 表ごとに 1 から振り直す連番は、表が違えば重複でも誤りでない。形に当たる番号だけを全体で一意とみなす |
| **全角・半角の違い以外の表記ゆれ**（`F1-5B` と `F1-5b`・`F1‐5b`（別のハイフン）） | 別の番号として数える。NFKC で畳むのは全角の英数字とハイフンだけ |
| **形式検査のモデル（`formal/`）の中の印** | 仕様から書き起こした写しなので見ない（上）。綴りだけ違う `Formal/` は写しと見なさず、印を見る |
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
# 形式検査のモデルの判別（`merge-versions.py` の `is_formal`。写さない。#908）
versions = _load("merge_versions", "merge-versions.py")
# 画面の関門（#1097。screen-spec は読み込まない——子のプロセスで呼ぶ）
screens = _load("screen_gate", "screen-gate.py")


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

# `references/spec-exit.md` の「テストケースの番号の重複」の写し（`scripts/test-check-spec-exit.py` が突き合わせる）。
# テストケースの表のデータ行の先頭のセルがこの形（英字で始まり、`-` で区切った英数字が 1 つ以上続き、数字を 1 つ以上含む）なら番号
CASE_NUMBER = r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+"
CASE_NUMBER_RE = re.compile(CASE_NUMBER)
# テストケースの表の見出し（先頭のセル）。`references/spec-exit.md` の「テストケースの番号の重複」の写し
CASE_HEADER = re.compile(r"\btest ?cases?\b|テストケース|\bcase ?(?:id|no\.?|number)\b|ケース(?:番号|ID|No)|テスト(?:番号|ID|No)|\btc\b", re.IGNORECASE)
SEPARATOR = re.compile(r"\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


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


def case_numbers(text: str) -> list[tuple[int, str]]:
    """(行番号, 番号) の一覧。**見出しの先頭のセルがテストケースの表（`CASE_HEADER`）の、データ行の先頭のセル**だけを見る。
    見出し行そのもの・区切りの行・見出しが `CASE_HEADER` に当たらない表（Q&A・NFR・決定表の行の番号を並べた表など）は見ない。
    コードブロックの中は見ない。セルは NFKC で正規化し、前後の空白・バッククォート・`*`・`_`（強調と等幅の飾り）を外してから番号の形に当てる。"""
    found = []
    fence = None
    previous = None  # 直前の行が表の行なら、その先頭のセル（次の行が区切りの行なら見出し）
    counting = False  # いまの表の見出しがテストケースの表か
    for number, line in enumerate(text.splitlines(), 1):
        opened = FENCE.match(line)
        if fence is not None:
            if opened and opened.group(1)[0] == fence[0] and len(opened.group(1)) >= len(fence) and not line.strip(" `~"):
                fence = None
            continue
        if opened:
            fence = opened.group(1)
            previous, counting = None, False
            continue
        stripped = line.strip()
        if not stripped.startswith("|"):
            previous, counting = None, False
            continue
        cell = unicodedata.normalize("NFKC", stripped[1:].split("|", 1)[0]).strip().strip("`*_ ")
        if SEPARATOR.fullmatch(stripped):
            counting = previous is not None and CASE_HEADER.search(previous) is not None
            previous = None
            continue
        if counting and CASE_NUMBER_RE.fullmatch(cell) and any(ch.isdigit() for ch in cell):
            found.append((number, cell))
        previous = cell
    return found


def duplicate_numbers(places: dict[str, list[tuple[Path, int]]]) -> list[str]:
    """番号ごとの出た場所（読んだ順）から、2 か所以上に出た番号を `ファイル:行` つきで名指しする。"""
    problems = []
    for number, where in places.items():
        if len(where) < 2:
            continue
        spots = "、".join(f"{path}:{line}" for path, line in where)
        problems.append(f"{where[0][0]}:{where[0][1]}: テストケースの番号 {number} が {len(where)} か所で重複（{spots}）"
                        "——中間表現の `ref` がどの行を指すか決まらない")
    return problems


def spec_files(root: Path) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if path == root / pptx.qa.INTERNAL_NAME:
            continue  # 内部の Q&A 表。印ではなく表として見る（check の中）
        if versions.is_formal("spec/" + path.relative_to(root).as_posix()):
            continue  # 形式検査のモデル。仕様から書き起こした写し（#908）。`root` は仕様のディレクトリ（重ねた全体の `spec/`）
        files.append(path)
    return files


def screen_gate(spec_dir: Path, docs: Path | None, upto: int | None, named: str | None) -> tuple[int, list[str]]:
    """画面の関門（#1097）。`docs` があれば `screen-gate.py` の `check`、無ければ重ねた全体の根に画面の表が無いことだけを見る。"""
    if docs is not None:
        return screens.check(docs, upto, named)
    if screens.has_tables(spec_dir.resolve().parent):  # `.` で渡されても重ねた全体の根を見る
        return screens.EXIT_UNJUDGED, [
            f"{spec_dir.parent / screens.SCREENS_DIR}: 画面の表があるのに --docs が無い——画面の関門を判定していない"
            "（--docs <docs ディレクトリ> を渡す。screen-gate.py）"]
    return screens.EXIT_OK, []


def check(qa_path: Path, spec_dir: Path, docs: Path | None = None, upto: int | None = None,
          named: str | None = None, screen: bool = True) -> tuple[int, list[str]]:
    """(終了コード, 出力する行) を返す。`docs`・`upto`・`named` は画面の関門（`screen-gate.py`）に渡す。
    `screen=False` は画面の関門を当てない——呼ぶ側（`scaffold.py`）が自分の条件で `screen-gate.py` を当てるとき。"""
    code, lines, rows = pptx.read_rows(qa_path)
    provisional = [row for row in rows if pptx.qa.is_provisional(row)]
    if code == 2:
        return 2, lines + ["条件 1 を判定していない（Q&A 表を読めない）"]
    if not spec_dir.is_dir():
        return 2, [f"{spec_dir}: ディレクトリが無い。条件 1 を判定していない（書いていない仕様は確定していない）"]
    files = spec_files(spec_dir)
    if not files:
        return 2, [f"{spec_dir}: ファイルが 1 つも無い。条件 1 を判定していない（書いていない仕様は確定していない）"]
    internal_path = spec_dir / pptx.qa.INTERNAL_NAME
    internal_code, internal_lines, internal_rows = (pptx.read_rows(internal_path) if internal_path.exists()
                                                    else (0, [], []))
    if internal_code == 2:
        return 2, internal_lines + ["条件 1 を判定していない（内部の Q&A 表を読めない）"]

    problems = []
    for path, table_code, table_lines, table_rows in ((qa_path, code, lines, rows),
                                                      (internal_path, internal_code, internal_lines, internal_rows)):
        if table_code:
            problems += table_lines
            problems.append(f"{path}: 列検査を通らない（決まりに反する表は確定していない）")
        for row in table_rows:
            if row["状態"].strip() not in pptx.qa.REFLECTED:
                problems.append(f"{path}: {row['No']}: 状態が {row['状態']}（{row['質問']}）")

    unread = []
    blank = []
    numbers: dict[str, list[tuple[Path, int]]] = {}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            unread.append(path)
            continue
        if "\0" in text:
            unread.append(path)
            continue
        if not text.strip():
            blank.append(path)
        for number, marker in find_markers(text):
            problems.append(f"{path}:{number}: 未決定の印 {marker}")
        if path.suffix == ".md":
            for number, case in case_numbers(text):
                numbers.setdefault(case, []).append((path, number))
    problems += duplicate_numbers(numbers)

    screen_code, screen_lines = screen_gate(spec_dir, docs, upto, named) if screen else (0, [])
    if screen_code == screens.EXIT_FAIL:
        problems += screen_lines
        screen_lines = []

    notes = [f"暫定反映の行（仕様には反映済み・利用者の確認待ち）: {len(provisional)} 件"]
    notes += [f"    {row['No']}: {row['回答']}" for row in provisional]
    notes.append(f"見なかったファイル（読めない・UTF-8 でない）: {len(unread)} 件")
    notes += [f"    {path}" for path in unread]
    if problems:
        return 1, problems + screen_lines + notes + ["条件 1 を満たさない。仕様レビューを抜けていない"]
    if screen_code:
        return 2, notes + screen_lines + ["条件 1 を判定していない（画面の関門。screen-gate.py）"]
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
    if len(blank) == len(files) - len(unread):
        # 読めた仕様がどれも空なら、中身のある仕様は 0 ファイル——「1 つも無い」と同じ扱い（#291）
        return 2, notes + [
            f"{spec_dir}: 読めた仕様がどれも中身が空（{len(blank)} ファイル）。"
            "条件 1 を判定していない（書いていない仕様は確定していない）"
        ]
    return 0, notes + screen_lines + [
        f"条件 1 を満たす（Q&A 表（共有・内部）に反映した状態でない行 0 件・仕様 {len(files) - len(unread)} ファイルに未決定の印 0 件）",
        "**これだけでは抜けていない**——条件 2〜5 は判定していない（references/spec-exit.md）",
    ]


def main(argv: list[str]) -> int:
    args = list(argv)
    options: dict[str, str | None] = {"--docs": None, "--upto": None, "--screen-spec": None}
    usage = (__doc__.splitlines()[2] if __doc__ else
             f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）")
    for name in options:
        while name in args:
            at = args.index(name)
            if at + 1 >= len(args) or options[name] is not None:
                print(f"{name} には値を 1 つ渡す\n{usage}", file=sys.stderr)
                return 2
            options[name] = args[at + 1]
            del args[at:at + 2]
    upto = options["--upto"]
    if (len(args) != 2 or any(a.startswith("--") for a in args)
            or (upto is not None and not re.fullmatch(r"[1-9][0-9]*", upto))
            or (options["--docs"] is None and (upto is not None or options["--screen-spec"] is not None))):
        print(usage, file=sys.stderr)
        return 2
    code, lines = check(Path(args[0]), Path(args[1]), None if options["--docs"] is None else Path(options["--docs"]),
                        None if upto is None else int(upto), options["--screen-spec"])
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
