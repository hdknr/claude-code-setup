#!/usr/bin/env python3
"""`check-qa-csv.py` の回帰テスト。

    python3 scripts/test-check-qa-csv.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`scripts/` ではない——
**spec-loop は正本リポジトリ（このリポジトリとは別）で使うプラグイン**なので、
スキルが自分の base ディレクトリから呼べる場所に置く（`test-find-cycle.py` と同じ形）。

見るもの:

1. **決まりに反する `qa.csv` を、反した理由つきで落とす**（1 種類ずつ）。
2. **決まりどおりの `qa.csv` を通す**（陽性対照。検査が厳しすぎて記事の例すら落とすのを防ぐ）。
3. **本体の定数が `references/qa-csv.md` の表と一致する**——決まりの正は `references/` で、
   本体の定数はその写しである。**写しがずれたらここで落ちる。** `references/qa-csv.md` の
   「例」のブロックも本体に通す（決まりの文書が、自分の例で決まりを破っていないか）。
4. **リポジトリの外で単体で動く**——本体だけを一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに全部の試料が期待どおりなら失格**とする。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、
穴が無くても緑になるので）。
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPT = PLUGIN / "scripts" / "check-qa-csv.py"
REFERENCE = PLUGIN / "references" / "qa-csv.md"

HEADER = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
GOOD_ROWS = (
    "Q-001,要求確定（決定表）,割引は A・B のどちらにしますか？,A: 割引なし / B: 3% 割引,A（業務部が回答）,決定表 4 行目,反映済み,\n"
    "Q-002,仕様レビュー（Red Team）,通信が切れたら？,A: 取り消す / B: 残す,未回答,—,確認中,\n"
    "Q-005,実現性・コスト,夜間は止めてよいか,A: 止まってよい / B: 24 時間,未回答,—,確認中,B は月額が約 2 倍\n"
    "Q-010,開発,上限を超えたら？,A: 拒否 / B: 切り詰める / C: 警告だけ,B（開発が仮置き）,—,確認中,\n"
)
# 記事（要求仕様書作成ループ）の Q&A 表の 6 行。記事の表は 2 つに分かれており、
# Q-005・Q-006 の表には `回答`・`反映先`・`状態` の列が無いので `未回答`・`—`・`確認中` で埋めた。
# Q-001 の `10,000` は区切りのコンマを含むので引用符で囲んだ。それ以外は記事の文のまま。
ARTICLE_ROWS = (
    'Q-001,要求確定（決定表）,"シルバー会員で 10,000 円未満のとき、割引は A・B のどちらにしますか？",'
    "A: 割引なし（0%） / B: 3% 割引,A（業務部が回答）,決定表 4 行目,反映済み,\n"
    "Q-002,仕様レビュー（Red Team）,決済の途中で通信が切れたとき、注文は A・B のどちらで扱いますか？,"
    "A: 取り消す / B: 「決済待ち」で残し、後で再開できる,未回答,—,確認中,\n"
    "Q-003,仕様レビュー（Domain Checker）,割引後の金額に 1 円未満の端数が出たら、A・B のどちらで丸めますか？,"
    "A: 切り捨て / B: 四捨五入,未回答,—,確認中,\n"
    "Q-004,仕様レビュー（形式検査・Z3 の反例）,クーポンを使うと「注文額の 60% 以上」の下限を割るとき、A・B のどちらにしますか？,"
    "A: 下限の金額で止める / B: この条件ではクーポンを使えなくする,未回答,—,確認中,\n"
    "Q-005,実現性・コスト（運用費の見積り）,夜間（0〜6 時）のシステム停止について、A・B のどちらにしますか？,"
    "A: 夜間は止まってよい / B: 24 時間稼働させる,未回答,—,確認中,"
    "B は冗長構成が要り、月額が A の約 2 倍、開発は 2 週間増える（仮の値）\n"
    "Q-006,実現性・コスト（運用費の見積り）,注文データを検索できる期間は、A・B のどちらにしますか？,"
    "A: 直近 1 年（それ以前はアーカイブ） / B: 全期間,未回答,—,確認中,B は保管と検索の費用が年ごとに増える（仮の値）\n"
)


def row(**over: str) -> str:
    """決まりどおりの 1 行を作り、指定した列だけ差し替える。"""
    base = {
        "No": "Q-001", "起票元": "要求確定", "質問": "どちらにしますか？",
        "選択肢": "A: する / B: しない", "回答": "未回答", "反映先": "—",
        "状態": "確認中", "費用への影響": "",
    }
    base.update(over)
    return ",".join(base.values()) + "\n"


# (名前, 中身（str は UTF-8 で書く。bytes はそのまま）, 期待する終了コード, 出力に含まれるべき文字列)
CASES: list[tuple[str, str | bytes, int, str]] = [
    # --- 陽性対照 ---
    ("決まりどおり", HEADER + GOOD_ROWS, 0, "OK（4 行）"),
    ("記事の Q-001〜Q-006", HEADER + ARTICLE_ROWS, 0, "OK（6 行）"),
    ("番号が 4 桁", HEADER + row(No="Q-1000"), 0, "OK（1 行）"),
    ("BOM 付き（Excel）", ("﻿" + HEADER + GOOD_ROWS), 0, "OK（4 行）"),
    ("空行は飛ばす", HEADER + GOOD_ROWS + "\n,,,,,,,\n", 0, "OK（4 行）"),
    ("セルの中の改行（引用符つき）",
     HEADER + 'Q-001,要求確定,"1 行目\n2 行目",A: x / B: y,未回答,—,確認中,\n', 0, "OK（1 行）"),
    ("セルの中の U+2028（Web から貼った文）", HEADER + row(質問="1 文目 2 文目"), 0, "OK（1 行）"),
    ("費用への影響は空でよい", HEADER + row(), 0, "OK（1 行）"),
    # --- 読めない（中身を検査していない） ---
    ("空のファイル", "", 2, "空のファイル"),
    ("UTF-8 でない", HEADER.encode("cp932"), 2, "UTF-8 として読めない"),
    # --- 見出し ---
    ("列が欠けている", HEADER.replace(",費用への影響", "") + row(), 1, "見出し行が決まりと違う"),
    ("列の順序が違う", HEADER.replace("回答,反映先", "反映先,回答") + row(), 1, "見出し行が決まりと違う"),
    ("余分な列", HEADER.replace("\n", ",備考\n") + row(), 1, "見出し行が決まりと違う"),
    # --- 行 ---
    ("行の列数が違う", HEADER + "Q-001,要求確定,質問,A: x / B: y,未回答,—,確認中\n", 1, "列の数が 7"),
    ("番号の書式", HEADER + row(No="Q-1"), 1, "`No` が `Q-001` の形でない"),
    ("番号が 2 桁", HEADER + row(No="Q-01"), 1, "`No` が `Q-001` の形でない"),
    ("番号が全角数字", HEADER + row(No="Q-００１"), 1, "`No` が `Q-001` の形でない"),
    ("番号の重複", HEADER + row() + row(), 1, ":3: `No` が 2 行目と重複"),
    ("未知の起票元", HEADER + row(起票元="営業"), 1, "`起票元` が決まりに無い"),
    ("未知の起票元（括弧つき）", HEADER + row(起票元="営業（電話）"), 1, "`起票元` が決まりに無い"),
    ("起票元の括弧が半角", HEADER + row(起票元="要求確定(決定表)"), 1, "`起票元` が決まりに無い"),
    ("選択肢が足りない", HEADER + row(選択肢="A: する"), 1, "選択肢が 2 つ未満"),
    ("選択肢の形", HEADER + row(選択肢="する / しない"), 1, "`A: …` の形でない"),
    ("選択肢のラベルが小文字", HEADER + row(選択肢="a: する / b: しない"), 1, "`A: …` の形でない"),
    ("選択肢のラベルが 2 字", HEADER + row(選択肢="AB: する / B: しない"), 1, "`A: …` の形でない"),
    ("選択肢のコロンの後に空白が無い", HEADER + row(選択肢="A:する / B: しない"), 1, "`A: …` の形でない"),
    ("選択肢の文が空", HEADER + row(選択肢="A:  / B: しない"), 1, "`A: …` の形でない"),
    ("選択肢のラベル重複", HEADER + row(選択肢="A: する / A: しない"), 1, "ラベルが重複"),
    ("未知の状態", HEADER + row(状態="回答済み"), 1, "`状態` が決まりに無い"),
    ("反映済みなのに未回答", HEADER + row(状態="反映済み", 反映先="決定表 1 行目"), 1, "`反映済み` なのに `回答` が無い"),
    ("反映済みなのに未回答（後ろに空白）", HEADER + row(状態="反映済み", 回答="未回答 ", 反映先="決定表 1 行目"), 1,
     "`反映済み` なのに `回答` が無い"),
    ("反映済みなのに反映先が無い", HEADER + row(状態="反映済み", 回答="A"), 1, "`反映済み` なのに `反映先` が無い"),
    ("反映済みなのに反映先が無い（前に空白）", HEADER + row(状態="反映済み", 回答="A", 反映先=" —"), 1,
     "`反映済み` なのに `反映先` が無い"),
    ("回答が空", HEADER + row(回答=""), 1, "`回答` が空（まだなら `未回答`）"),
    ("反映先が空", HEADER + row(反映先=""), 1, "`反映先` が空（まだなら `—`）"),
    ("質問が空", HEADER + row(質問=""), 1, "`質問` が空"),
    # 1 行に 2 つ反していて、後のほうも出る（`No` の検査が先に走る）
    ("全部を出す（最初の 1 件で止めない）", HEADER + row(No="X", 状態="?"), 1, "`状態` が決まりに無い"),
]

# 本体を 1 箇所ずつ壊す。(名前, 壊す前, 壊した後, それを殺すはずの試料)
# **殺すはずの試料が期待どおりでなくなること**まで見る——別の試料で偶然落ちたのを
# 「殺せた」と数えないため。
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("見出しを見ない", "if header != COLUMNS:", "if False:", "列の順序が違う"),
    ("状態を見ない", 'row["状態"] not in STATES', "False", "未知の状態"),
    ("反映済みの回答を見ない", 'if row["回答"].strip() in ("", NO_ANSWER):', "if False:", "反映済みなのに未回答"),
    ("反映済みの反映先を見ない", 'if row["反映先"].strip() in ("", NO_TARGET):', "if False:", "反映済みなのに反映先が無い"),
    ("選択肢の数を見ない", "if len(options) < MIN_OPTIONS:", "if False:", "選択肢が足りない"),
    ("選択肢を 1 つから許す", "MIN_OPTIONS = 2", "MIN_OPTIONS = 1", "選択肢が足りない"),
    ("選択肢の形を見ない", r'OPTION = re.compile(rf"(?P<label>{OPTION_LABEL}): \S.*")',
     r'OPTION = re.compile(r"(?P<label>.?).*")', "選択肢の形"),
    ("ラベルに小文字を許す", 'OPTION_LABEL = "[A-Z]"', 'OPTION_LABEL = "[A-Za-z]"', "選択肢のラベルが小文字"),
    ("ラベルに 2 字を許す", 'OPTION_LABEL = "[A-Z]"', 'OPTION_LABEL = "[A-Z]+"', "選択肢のラベルが 2 字"),
    ("コロンの後の空白を見ない", r'}): \S.*")', r'}):\s*\S.*")', "選択肢のコロンの後に空白が無い"),
    ("選択肢の文の空を許す", r'}): \S.*")', r'}): .*")', "選択肢の文が空"),
    ("起票元の括弧を半角でも許す",
     'SOURCE = re.compile(rf"(?P<name>[^{DETAIL_OPEN}]+)(?:{DETAIL_OPEN}.+{DETAIL_CLOSE})?")',
     'SOURCE = re.compile(r"(?P<name>[^（(]+)(?:[（(].+[）)])?")', "起票元の括弧が半角"),
    ("ラベルの重複を見ない", "if len(set(labels)) != len(labels):", "if False:", "選択肢のラベル重複"),
    ("番号の書式を見ない", 'not NUMBER.fullmatch(row["No"])', "False", "番号の書式"),
    ("番号を 2 桁から許す", r'NUMBER = re.compile(r"Q-[0-9]{3,}")', r'NUMBER = re.compile(r"Q-[0-9]{2,}")', "番号が 2 桁"),
    ("番号を 3 桁までにする", r'NUMBER = re.compile(r"Q-[0-9]{3,}")', r'NUMBER = re.compile(r"Q-[0-9]{3}")', "番号が 4 桁"),
    ("番号を Unicode の数字で見る", r'NUMBER = re.compile(r"Q-[0-9]{3,}")', r'NUMBER = re.compile(r"Q-\d{3,}")',
     "番号が全角数字"),
    ("反映済みの回答の空白を落とさない", 'if row["回答"].strip() in ("", NO_ANSWER):',
     'if row["回答"] in ("", NO_ANSWER):', "反映済みなのに未回答（後ろに空白）"),
    ("反映済みの反映先の空白を落とさない", 'if row["反映先"].strip() in ("", NO_TARGET):',
     'if row["反映先"] in ("", NO_TARGET):', "反映済みなのに反映先が無い（前に空白）"),
    ("番号の重複を見ない", 'if row["No"] in seen:', "if False:", "番号の重複"),
    ("起票元を見ない", 'm["name"] not in SOURCES', "False", "未知の起票元"),
    ("空のセルを見ない", "if column not in MAY_BE_EMPTY and not row[column].strip():", "if False:", "質問が空"),
    ("列の数を見ない", "if len(fields) != len(COLUMNS):", "if False:", "行の列数が違う"),
    ("BOM を剥がさない", 'encoding="utf-8-sig"', 'encoding="utf-8"', "BOM 付き（Excel）"),
    ("空のファイルを 2 にしない", "if not text.strip():", "if False:", "空のファイル"),
    ("UTF-8 でないのを 2 にしない", 'return 2, [f"{path}: UTF-8', 'return 1, [f"{path}: UTF-8', "UTF-8 でない"),
    ("費用への影響の空を許さない", 'MAY_BE_EMPTY = {"費用への影響"}', "MAY_BE_EMPTY = set()", "費用への影響は空でよい"),
    # 引用符つきの改行は `splitlines()` でも壊れない（csv が繋ぎ直す）ので、殺すのは U+2028 の試料
    ("splitlines で割る", 'csv.reader(io.StringIO(text, newline=""))', "csv.reader(text.splitlines())",
     "セルの中の U+2028（Web から貼った文）"),
    ("最初の 1 件で止める", "for problem in check_row(row):", "for problem in check_row(row)[:1]:",
     "全部を出す（最初の 1 件で止めない）"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{(' — ' + detail) if detail else ''}")
        failures.append(name)


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), f"試料がテンポラリの外: {resolved}"
    assert not resolved.is_relative_to(REAL_REPO), "試料が実リポジトリの内側にある"


def load(script: Path):
    spec = importlib.util.spec_from_file_location(f"qa_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_case(root: Path, index: int, content: str | bytes) -> Path:
    path = root / f"case-{index}.csv"
    assert_in_tmp(path)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def run_case(mod, path: Path) -> tuple[int, str]:
    """本体の `check` を呼ぶ。**例外は「期待どおりでない」として扱う**（変異で壊れる形の 1 つ）。"""
    try:
        code, lines = mod.check(path)
    except Exception as e:  # noqa: BLE001 — 変異の結果を観測するため
        return -1, f"{type(e).__name__}: {e}"
    return code, "\n".join(lines)


def matches(result: tuple[int, str], expected_code: int, expected_text: str) -> bool:
    code, out = result
    return code == expected_code and expected_text in out


def table_keys(markdown: str, heading: str) -> list[str]:
    """`## <heading>` の直後の表から、1 列目のバッククォートの中身を順に返す。"""
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", markdown, re.S | re.M)
    if not m:
        return []
    keys = []
    for line in m.group(1).splitlines():
        cell = re.match(r"\|\s*`([^`]+)`\s*\|", line)
        if cell:
            keys.append(cell.group(1))
    return keys


def column_cells(markdown: str) -> dict[str, list[str]]:
    """「列」の表を {列名: [書くもの, 空のとき]} で返す。"""
    m = re.search(r"^## 列\n(.*?)(?=^## |\Z)", markdown, re.S | re.M)
    cells: dict[str, list[str]] = {}
    for line in (m.group(1).splitlines() if m else []):
        parts = [p.strip() for p in line.strip().strip("|").split(" | ")]
        key = re.fullmatch(r"`([^`]+)`", parts[0]) if parts else None
        if key and len(parts) == 3:
            cells[key.group(1)] = parts[1:]
    return cells


def first_code(text: str, pattern: str) -> str | None:
    """`pattern` の `{}` の位置にあるバッククォートの中身を返す（空白はそのまま）。"""
    m = re.search(pattern.replace("{}", "`([^`]+)`"), text)
    return m.group(1) if m else None


def reference_mismatches(mod, markdown: str) -> list[str]:
    problems = []
    for heading, constant in (("列", mod.COLUMNS), ("起票元", mod.SOURCES), ("状態", mod.STATES)):
        keys = table_keys(markdown, heading)
        if keys != list(constant):
            problems.append(f"「{heading}」の表 {keys} ≠ 本体 {list(constant)}")

    # 「列」の表のセルに書いた決まりと、本体の写し
    cells = column_cells(markdown)
    write, empty = (lambda c: cells.get(c, ["", ""])[0]), (lambda c: cells.get(c, ["", ""])[1])
    may_be_empty = {c for c in cells if "空でよい" in empty(c)}
    if may_be_empty != set(mod.MAY_BE_EMPTY):
        problems.append(f"空でよい列 {sorted(may_be_empty)} ≠ 本体 {sorted(mod.MAY_BE_EMPTY)}")
    for column, constant in (("回答", mod.NO_ANSWER), ("反映先", mod.NO_TARGET)):
        marker = first_code(empty(column), "まだなら {}")
        if marker != constant:
            problems.append(f"`{column}` の「まだ無い」の印 {marker!r} ≠ 本体 {constant!r}")
    digits = re.search(r"`Q-` に (\d+) 桁以上", write("No"))
    expected = rf"Q-[0-9]{{{digits.group(1)},}}" if digits else None
    if expected != mod.NUMBER.pattern:
        problems.append(f"番号の書式 {expected!r} ≠ 本体 {mod.NUMBER.pattern!r}")
    separator = first_code(write("選択肢"), "の形を {} で")
    if separator != mod.OPTION_SEPARATOR:
        problems.append(f"選択肢の区切り {separator!r} ≠ 本体 {mod.OPTION_SEPARATOR!r}")
    count = re.search(r"で (\d+) つ以上つなぐ", write("選択肢"))
    if (int(count.group(1)) if count else None) != mod.MIN_OPTIONS:
        problems.append(f"選択肢の数 {count and count.group(1)!r} ≠ 本体 {mod.MIN_OPTIONS!r}")
    # 言葉で書いた決まりは、言葉 → 本体の値の対応（下の 2 つの辞書）で突き合わせる。
    # 決まりの言葉が変わると対応に無いので None になり、不一致として見える。
    label = re.search(r"ラベルは(.+?)で、", write("選択肢"))
    if LABEL_WORDS.get(label.group(1) if label else "") != mod.OPTION_LABEL:
        problems.append(f"選択肢のラベル {label and label.group(1)!r} ≠ 本体 {mod.OPTION_LABEL!r}")
    bracket = re.search(r"詳細は(.+?)で添えて", write("起票元"))
    if BRACKET_WORDS.get(bracket.group(1) if bracket else "") != (mod.DETAIL_OPEN, mod.DETAIL_CLOSE):
        problems.append(f"起票元の括弧 {bracket and bracket.group(1)!r} ≠ 本体 {(mod.DETAIL_OPEN, mod.DETAIL_CLOSE)!r}")
    return problems


LABEL_WORDS = {"英大文字 1 字": "[A-Z]"}
BRACKET_WORDS = {"全角括弧": ("（", "）")}


# references/qa-csv.md を 1 箇所ずつ崩す。どれも突き合わせで不一致として見えなければならない
# （突き合わせが空振りしていないことの陽性対照）。
REFERENCE_MUTATIONS: list[tuple[str, str, str]] = [
    ("状態の表の 1 行", "| `反映済み` |", "| 反映済み |"),
    ("空でよい列", "| 費用に関わらない質問は空でよい |", "| 許さない |"),
    ("回答の「まだ無い」の印", "まだなら `未回答` と書く", "まだなら `未定` と書く"),
    ("反映先の「まだ無い」の印", "まだなら `—` と書く", "まだなら `-` と書く"),
    ("番号の桁", "`Q-` に 3 桁以上の数字", "`Q-` に 4 桁以上の数字"),
    # ` | ` に崩すと表の行が割れて「欠落」で赤になり、値の比較を確かめられない
    ("選択肢の区切り", "の形を ` / ` で", "の形を ` ; ` で"),
    ("選択肢の数", "で 2 つ以上つなぐ", "で 3 つ以上つなぐ"),
    ("選択肢のラベル", "ラベルは英大文字 1 字で、", "ラベルは英字 1 字で、"),
    ("起票元の括弧", "詳細は全角括弧で添えて", "詳細は半角括弧で添えて"),
]


def reference_example(markdown: str) -> str | None:
    m = re.search(r"^## 例\n.*?```csv\n(.*?)```", markdown, re.S | re.M)
    return m.group(1) if m else None


def main() -> int:
    mod = load(SCRIPT)
    reference = REFERENCE.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = [write_case(root, i, content) for i, (_, content, _, _) in enumerate(CASES)]

        print("1・2. 試料（陽性対照を含む）")
        for (name, _, code, text), path in zip(CASES, paths):
            result = run_case(mod, path)
            check(name, matches(result, code, text), f"終了 {result[0]}: {result[1]!r}")

        print("3. references/qa-csv.md との一致")
        problems = reference_mismatches(mod, reference)
        check("決まりの表が本体の定数と一致する", not problems, "; ".join(problems))
        for name, before, after in REFERENCE_MUTATIONS:
            if reference.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {reference.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(mod, reference.replace(before, after))))
        example = reference_example(reference)
        check("「例」のブロックがある", example is not None)
        if example is not None:
            result = run_case(mod, write_case(root, 900, example))
            check("「例」が決まりを破っていない", result[0] == 0, result[1])

        print("4. リポジトリの外で単体で動く")
        alone = root / "alone"
        alone.mkdir()
        copied = alone / "check-qa-csv.py"
        shutil.copy(SCRIPT, copied)
        assert_in_tmp(copied)
        good, bad = paths[0], paths[CASES.index(next(c for c in CASES if c[0] == "未知の状態"))]
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        ok = subprocess.run([sys.executable, "-I", str(copied), str(good)], cwd=alone, env=env,
                            capture_output=True, text=True)
        ng = subprocess.run([sys.executable, "-I", str(copied), str(bad)], cwd=alone, env=env,
                            capture_output=True, text=True)
        check("決まりどおりなら 0", ok.returncode == 0, ok.stderr)
        check("反していれば 1 で、理由を stderr に出す", ng.returncode == 1 and "`状態`" in ng.stderr, ng.stderr)
        usage = subprocess.run([sys.executable, "-I", str(copied)], cwd=alone, env=env,
                               capture_output=True, text=True)
        check("引数が無ければ 2 で使い方を出す", usage.returncode == 2 and "usage:" in usage.stderr, usage.stderr)

        print("5. 変異テスト")
        source = SCRIPT.read_text(encoding="utf-8")
        by_name = {name: (code, text, path) for (name, _, code, text), path in zip(CASES, paths)}
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届く: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            broken = root / f"mutant-{index}.py"
            broken.write_text(source.replace(before, after), encoding="utf-8")
            assert_in_tmp(broken)
            mutant = load(broken)
            code, text, path = by_name[killer]
            check(f"変異を殺せる: {name}（{killer}）", not matches(run_case(mutant, path), code, text))

    print()
    if failures:
        print(f"FAIL: {len(failures)} 件")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
