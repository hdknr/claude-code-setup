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
- **テストケースの番号が重複していたら 1**（#1297）——**同じ重ねた全体の仕様（`spec/`）の `.md` の中で**、見出しの先頭のセルが `CASE_HEADER`（`テストケース`・`test case`・`ケース番号`・`TC` など。正規表現は `references/spec-exit.md`）に当たる表
  （**と、テストケースの節（`#` の見出しの末尾がテストケースの語の節。小見出しの下を含む）の、見出しの先頭のセルが `ID_HEADER`（`ID`・`No`・`項番`）の表**。#1333）の、データ行の先頭のセルが
  番号（`CASE_NUMBER` の形）である行が、同じファイルでも別のファイルでも 2 つ以上あれば、番号と出た場所（`ファイル:行`）を全部名指しする。
  **中間表現のケースの `ref` の照合（`scaffold.py` の `check_ref`。#465）は番号が原文に在るかだけを見る**ので、重複は通り、どちらの行を写したのかが決まらない。
  **数えるのは重ねた後の全体**——後の版が同じファイルを置き換えたなら、置き換えられた前の版の行は全体に無いので重複に数えない
  （重ね方は `merge-versions.py`。このスクリプトは重ねない）。番号の形・どの列を番号と読むか・読まないものは `references/spec-exit.md` の
  「テストケースの番号の重複」を正とする。重複が無い仕様では出力も終了コードも変わらない。
- **「呼ぶ側の分岐」の行が 8 分岐のどれかに触れていなければ 1**（#1340）——仕様の `.md` の、見出し・項目の行・表の行・表の見出しの形の「呼ぶ側の分岐」の行ごとに、
  分岐（`CALLER_BRANCHES`）のうち触れていないものを、行（`ファイル:行`）と一緒に名指しする。**組の名前だけの項目（`量: …`）と別の節を指す書き方（「…と同じ」）は
  どの分岐にも触れない**（そう添えて出す）。**行の形・まとめて書く書き方・触れているの読み方は `references/spec-exit.md` の「呼ぶ側の分岐の行の形」を正とする。**
  **分岐の名前の原本はここ**で、`scaffold.py` の `BRANCHES`（課題一覧（案）の未決定事項）はこれを読む——検査器と scaffold は同じ定義で数える。
  行の無い仕様では出力も終了コードも変わらない。`check(callers=False)` は見ない（`scaffold.py` の前の版の時点の `--upto`）。
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
| **テストケースの表以外の先頭のセル（見出しが `ID`・`No`・`項番` の表は、テストケースの節（`#` の見出しの末尾がテストケースの語。小見出しの下を含む）の外なら、テストケースの表でも読まない。節の中の小見出しの下の `ID` の表は、テストケースでなくても読む。下線の見出し（本文の行の直後の `===`・`---`）は見出しと読まず、テストケースの節を閉じる。空行の後の `---` は区切りの線で、閉じない）・先頭のセル以外の番号・`.md` 以外のファイルの番号（`.MD` を含む）・フェンスのコードブロックの中の番号・引用や先頭の `|` の無い表・`1-1`・`TC001`・`TC-1.1` のような形の外の番号** | 番号を振る場所の決まりはテストケースの表の先頭のセルだけ（`references/spec-exit.md`）。ほかを読むと、Q&A・NFR・決定表の行の番号を並べた表や本文中の言及（`F1-5b を参照`）を重複に数える。**逆に、4 字下げのコードブロックと HTML コメントの中の表は、読んでしまう（数える）** |
| **番号の形に当たらない行の識別子**（`1`・`あ`・`No.3` など） | 表ごとに 1 から振り直す連番は、表が違えば重複でも誤りでない。形に当たる番号だけを全体で一意とみなす |
| **全角・半角の違い以外の表記ゆれ**（`F1-5B` と `F1-5b`・`F1‐5b`（別のハイフン）） | 別の番号として数える。NFKC で畳むのは全角の英数字とハイフンだけ |
| **形式検査のモデル（`formal/`）の中の印** | 仕様から書き起こした写しなので見ない（上）。綴りだけ違う `Formal/` は写しと見なさず、印を見る |
| **「呼ぶ側の分岐」の行そのものが無い機能** | 機能の単位（仕様が書き分けている単位）を機械で決めない。行の無い機能は条件 2 の判定役（Red Team）が見る |
| **4 つの形の外の「呼ぶ側の分岐」**（「呼ぶ側の分岐は次のとおり」のような本文・見出しの後ろに字が続く `呼ぶ側の分岐（受注）`）と、**`.md` 以外のファイルの行** | 行の形の決まり（`references/spec-exit.md`）の外は行と読まない——読まない行は揃いを見ない |
| **分岐の項目の文の中身**（見せるものが仕様として足りるか・「該当なし」に理由があるか） | 触れているか（`:` の後ろに文があるか）だけを見る。中身は条件 2 の判定役が見る |
| **4 字下げのコードブロックと HTML コメントの中の行** | フェンスのコードブロックの中だけを外す（テストケースの番号と同じ）。中の行も読んでしまう |
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
# テストケースの節の表の見出し（先頭のセル）。テストケースの節（`SECTION_HEADER`）の中でだけ、テストケースの表と読む（#1333）。
# `references/spec-exit.md` の「テストケースの番号の重複」の写し
ID_HEADER = re.compile(r"^(?:id|no\.?|項番)$", re.IGNORECASE)
# テストケースの節の見出し（`#` の見出しの文）。**末尾が**テストケースの語（後ろに `一覧` と括弧書きを許す）。同じ写し
SECTION_HEADER = re.compile(r"(?:テストケース|\btest ?cases?|\btc)(?:\s*一覧)?\s*(?:[(（][^()（）]*[)）])?$", re.IGNORECASE)
HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]|$)")
# 下線の見出しの下線（`===`・`---`）。本文の行の直後にあるときだけ下線の見出しで、節の見出しと読まず、テストケースの節を閉じる
# （#1333。下線の見出しの下の表をテストケースに数えない。空行の後の `---`・`***` は区切りの線で、節を閉じない）
UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
SEPARATOR = re.compile(r"\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)*\|?")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def fence_closes(opened: re.Match[str] | None, fence: str, line: str) -> bool:
    """開いているフェンス（`fence`）を、この行が閉じるか——同じ種類で、開きより短くなく、情報文字列の無いフェンスの行。
    テストケースの番号（`case_rows`）と呼ぶ側の分岐の行（`caller_rows`）が同じ読み方でコードブロックを外す。"""
    return bool(opened and opened.group(1)[0] == fence[0] and len(opened.group(1)) >= len(fence) and not line.strip(" `~"))


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


def case_rows(text: str) -> list[tuple[int, str, str]]:
    """(行番号, 番号, 行の原文) の一覧。**見出しの先頭のセルがテストケースの表（`CASE_HEADER`）の、データ行の先頭のセル**だけを見る。
    行の原文は前後の空白を落とした 1 行（`scaffold.py` の `acceptance` が、中間表現に並べた原文から番号を引くのに使う。#1301）。
    見出し行そのもの・区切りの行・見出しが `CASE_HEADER` に当たらない表（Q&A・NFR・決定表の行の番号を並べた表など）は見ない。
    **ただしテストケースの節（`#` の見出しの文の末尾が `SECTION_HEADER` に当たる。その節の小見出しの下も、同じか浅い見出しが来るまで節の中）では、
    表の見出しの先頭のセルが `ID_HEADER`（`ID`・`No`・`項番`）の表もテストケースの表と読む**（#1333）。
    コードブロックの中は見ない。セルは NFKC で正規化し、前後の空白・バッククォート・`*`・`_`（強調と等幅の飾り）を外してから番号の形に当てる。"""
    found = []
    fence = None
    previous = None  # 直前の行が表の行なら、その先頭のセル（次の行が区切りの行なら見出し）
    counting = False  # いまの表の見出しがテストケースの表か
    prose = False  # 直前の行が本文の行（空でなく、表・見出し・コードブロックでない）か——次の下線で下線の見出しになる
    section = None  # いまの見出しがテストケースの節の中なら、その節の見出しの深さ（#1333。小見出しは節を引き継ぐ）
    for number, line in enumerate(text.splitlines(), 1):
        opened = FENCE.match(line)
        if fence is not None:
            if fence_closes(opened, fence, line):
                fence = None
            continue
        if opened:
            fence = opened.group(1)
            previous, counting, prose = None, False, False
            continue
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            if section is None or level <= section:
                title = unicodedata.normalize("NFKC", line.strip().strip("#")).strip(" `*_").rstrip(":：").strip(" `*_")
                section = level if SECTION_HEADER.search(title) else None
            previous, counting, prose = None, False, False
            continue
        if UNDERLINE.match(line) and prose:
            section = None
            previous, counting, prose = None, False, False
            continue
        stripped = line.strip()
        if not stripped.startswith("|"):
            previous, counting = None, False
            prose = bool(stripped)
            continue
        prose = False
        cell = unicodedata.normalize("NFKC", stripped[1:].split("|", 1)[0]).strip().strip("`*_ ")
        if SEPARATOR.fullmatch(stripped):
            counting = previous is not None and (CASE_HEADER.search(previous) is not None
                                                 or (section is not None and ID_HEADER.fullmatch(previous) is not None))
            previous = None
            continue
        if counting and CASE_NUMBER_RE.fullmatch(cell) and any(ch.isdigit() for ch in cell):
            found.append((number, cell, stripped))
        previous = cell
    return found


def case_numbers(text: str) -> list[tuple[int, str]]:
    """(行番号, 番号) の一覧（`case_rows` の行の原文を除いたもの）。"""
    return [(number, case) for number, case, _ in case_rows(text)]


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


# 呼ぶ側の分岐（#1340）。`references/spec-exit.md` の「呼ぶ側の分岐の行の形」の写し（`scripts/test-check-spec-exit.py` が突き合わせる）。
# **分岐の名前の原本はここ**——`scaffold.py` の `BRANCHES` はこれを読む（写さない）。組の名前 → (つなぐ助詞, 分岐の述語) の並び
CALLER_LABEL = "呼ぶ側の分岐"
CALLER_GROUPS = (
    ("入力", (("が", "欠ける"), ("が", "遅れる"), ("の", "順が崩れる"))),
    ("呼ぶ処理", (("が", "失敗する"), ("が", "やり直される"), ("が", "再起動する"))),
    ("量", (("が", "上限を超える"), ("が", "重なる"))),
)
CALLER_BRANCHES = tuple(f"{group}{particle}{predicate}" for group, preds in CALLER_GROUPS for particle, predicate in preds)
CALLER_NONE = "該当なし"
# まとめて書くときの区切り（`入力が欠ける・遅れる`）。NFKC の後なので全角の `／` は `/` になっている
CALLER_JOINERS = re.compile(r"[・、/]")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?")  # タスクリストのチェックボックスも外す
BREAK = re.compile(r"<br\s*/?>", re.IGNORECASE)
# 別の節を指す書き方（「[価格照会書を出力する] と同じ」）——文の末尾が「と同じ」
REFERS = re.compile(r"[\]」』]\s*と同じ")  # 角括弧・鉤括弧で名指した先と「同じ」（文の途中でも）


def _bare(text: str) -> str:
    """前後の空白・強調と等幅の飾り（`*`・`_`・`` ` ``）を外す。"""
    return text.strip().strip("*`_ ").strip()


def caller_label(label: str) -> tuple[set[str], bool] | None:
    """項目の見出し（`:` の前）を分岐の書き方として読む。読めれば (触れる分岐, 読めない書き方か)、組の名前で始まらなければ None。

    分岐の名前（`入力が欠ける`）か、組の名前に `が`・`の` を続けてその組の述語を `・`・`、`・`/` で並べたもの
    （`入力が欠ける・遅れる・順が崩れる`。並べる途中で別の組の分岐の名前を書いてもよい）。
    **組の名前だけ（`量`）や組に無い述語を含む書き方は、どの分岐にも触れない**（読めない書き方として返す）。"""
    label = _bare(label)
    if not any(label.startswith(group) for group, _ in CALLER_GROUPS):
        return None
    touched: set[str] = set()
    current = None
    for piece in CALLER_JOINERS.split(label):
        piece = _bare(piece)
        for group, preds in CALLER_GROUPS:
            if piece.startswith(group) and piece[len(group):len(group) + 1] in ("が", "の"):
                current, piece = (group, preds), piece[len(group) + 1:]
                break
        if current is None:
            return set(), True
        group, preds = current
        names = [f"{group}{particle}{predicate}" for particle, predicate in preds if predicate == piece]
        if not names:
            return set(), True
        touched.update(names)
    return touched, False


def _caller_start(line: str) -> tuple[str, str] | None:
    """行が「呼ぶ側の分岐」の行の始まりなら (形, 同じ行の中身)。形は `見出し`・`表`・`項目`。"""
    text = unicodedata.normalize("NFKC", line)
    heading = HEADING.match(text)
    if heading:
        title = _bare(text.strip().strip("#")).rstrip(":").strip()
        title = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s+", "", _bare(title))  # 節の番号（`3.2 `）を外す
        return ("見出し", "") if _bare(title) == CALLER_LABEL else None
    stripped = text.strip()
    if stripped.startswith("|"):
        cells = stripped.strip("|").split("|")
        return ("表", "|".join(cells[1:])) if _bare(cells[0]) == CALLER_LABEL else None
    body = BULLET.sub("", stripped)
    if not body.lstrip("*_`").startswith(CALLER_LABEL):
        return None
    rest = _bare(body.lstrip("*_`")[len(CALLER_LABEL):].lstrip("*_`"))
    if rest == "":
        return "項目", ""
    if rest.startswith(":"):
        return "項目", rest[1:].strip()
    return None


def _caller_item(line: str) -> tuple[str, str] | None:
    """中身の 1 項目を (見出し, 文) に分ける。表の行は先頭のセルが見出し。`:` の無い行は None。"""
    text = unicodedata.normalize("NFKC", line).strip()
    if text.startswith("|"):
        if SEPARATOR.fullmatch(text):
            return None
        cells = text.strip("|").split("|")
        return (cells[0], "|".join(cells[1:])) if len(cells) > 1 else None
    body = BULLET.sub("", text)
    if ":" not in body:
        return None
    label, _, rest = body.partition(":")
    return label, rest


def _is_branch_item(line: str) -> bool:
    item = _caller_item(line)
    return item is not None and caller_label(item[0]) is not None


def caller_rows(text: str) -> list[tuple[int, list[str], list[str], bool]]:
    """仕様の「呼ぶ側の分岐」の行ごとに (行番号, 触れていない分岐, 読めない書き方, 別の節を指す書き方か)。

    行の形と読み方は `references/spec-exit.md` の「呼ぶ側の分岐の行の形」を正とする（#1340）。コードブロックの中は見ない。"""
    lines = text.splitlines()
    rows = []
    fence = None
    at = 0
    while at < len(lines):
        line = lines[at]
        opened = FENCE.match(line)
        if fence:
            if fence_closes(opened, fence, line):
                fence = None
            at += 1
            continue
        if opened:
            fence = opened.group(1)
            at += 1
            continue
        start = _caller_start(line)
        if start is None:
            at += 1
            continue
        kind, own = start
        follow = at + 1
        if kind == "表" and follow < len(lines) and SEPARATOR.fullmatch(lines[follow].strip()):
            # 先頭の列の見出しが `呼ぶ側の分岐` の表——見出し行のほかのセルは列の名前で、続く表の行（先頭のセルが分岐の書き方）が中身
            kind = "表の見出し"
            content, follow = _table_body(lines, follow + 1)
        elif kind == "表":
            content = [cell for cell in own.split("|") if cell.strip()]  # セルごとに項目（`<br>` でも分ける）
        else:
            content = [own] if own else []
            inner = None  # 中身の途中のコードブロック（中は読まずに飛ばし、行は閉じない）
            while follow < len(lines):
                nxt = lines[follow]
                fenced = FENCE.match(nxt)
                if inner:
                    if fence_closes(fenced, inner, nxt):
                        inner = None
                    follow += 1
                    continue
                if fenced:
                    inner = fenced.group(1)
                    follow += 1
                    continue
                nested = _caller_start(nxt)
                if nested is not None and nested[0] == "表" and follow + 1 < len(lines) and SEPARATOR.fullmatch(lines[follow + 1].strip()):
                    # 見出しの下の、先頭の列の見出しが `呼ぶ側の分岐` の表は、この行の中身（別の行にしない）
                    body, follow = _table_body(lines, follow + 2)
                    content += body
                    continue
                if nested is not None:
                    break
                if HEADING.match(unicodedata.normalize("NFKC", nxt)):
                    break
                if not nxt.strip() and kind == "項目":
                    ahead = follow + 1
                    while ahead < len(lines) and not lines[ahead].strip():
                        ahead += 1
                    if ahead >= len(lines) or not _is_branch_item(lines[ahead]):
                        break
                content.append(nxt)
                follow += 1
        touched: set[str] = set()
        unread: list[str] = []
        whole_none = False
        refers = False
        first = True  # 中身の最初の空でない部分か——行ごと該当なしは、中身が `該当なし` で始まり、分岐の項目を持たないときだけ
        labelled = False  # 分岐の書き方の項目を 1 つでも持つか
        for part in (piece for entry in content for piece in BREAK.split(entry)):
            item = _caller_item(part)
            plain = _bare(BULLET.sub("", unicodedata.normalize("NFKC", part).strip()).strip("|"))
            if not plain:
                continue
            leading, first = first, False
            if item is None or caller_label(item[0]) is None:
                if leading and plain.startswith(CALLER_NONE):
                    whole_none = True
                if REFERS.search(plain):
                    refers = True
                continue
            label, rest = item
            labelled = True
            names, bad = caller_label(label)
            text_of = _bare(rest.strip("|"))
            if bad:
                unread.append(_bare(label))
            elif REFERS.search(text_of):
                refers = True  # 別の節を指す書き方は、分岐の項目の文でも触れない
            elif text_of:
                touched |= names
        whole_none = whole_none and not labelled
        missing = [] if whole_none else [name for name in CALLER_BRANCHES if name not in touched]
        # 表の行で、分岐の書き方も「該当なし」も別の節も持たないもの（`| 呼ぶ側の分岐 | 下の節 |`）は、ほかの行を指す案内——ほかに行があれば行に数えない
        pointer = kind == "表" and not labelled and not whole_none and not refers
        rows.append((at + 1, missing, unread, refers, pointer))
        at = follow
    if any(not row[4] for row in rows):
        rows = [row for row in rows if not row[4]]
    return [row[:4] for row in rows]


def _table_body(lines: list[str], at: int) -> tuple[list[str], int]:
    """`at` から続く表の行（`|` で始まる行）と、その次の行の番号。"""
    body = []
    while at < len(lines) and lines[at].strip().startswith("|"):
        body.append(lines[at])
        at += 1
    return body, at


def caller_problems(path: Path, text: str) -> list[str]:
    """揃わない「呼ぶ側の分岐」の行を、行と欠けた分岐を名指しして 1 行ずつ。"""
    problems = []
    for number, missing, unread, refers in caller_rows(text):
        if not missing:
            continue
        line = (f"{path}:{number}: 呼ぶ側の分岐の行が 8 分岐のうち {len(missing)} 分岐に触れていない（{'・'.join(missing)}）"
                "——分岐ごとに見せるものか「該当なし」と理由を書く")
        if unread:
            line += f"。読めない分岐の書き方（組の名前だけ・組に無い述語。どの分岐にも触れない）: {'・'.join(unread)}"
        if refers:
            line += "。別の節を指す書き方（「…と同じ」）は認めない——この機能の分岐を書く"
        problems.append(line + "（references/spec-exit.md の「呼ぶ側の分岐の行の形」）")
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
          named: str | None = None, screen: bool = True, callers: bool = True) -> tuple[int, list[str]]:
    """(終了コード, 出力する行) を返す。`docs`・`upto`・`named` は画面の関門（`screen-gate.py`）に渡す。
    `screen=False` は画面の関門を当てない——呼ぶ側（`scaffold.py`）が自分の条件で `screen-gate.py` を当てるとき。
    `callers=False` は呼ぶ側の分岐の行の揃いを見ない——`scaffold.py` が前の版の時点（`--upto <n-1>`。凍結した版は直せない）を見るとき（#1340）。"""
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
            if callers:
                problems += caller_problems(path, text)
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
