#!/usr/bin/env python3
"""`check-infra-csv.py`（システム基盤要件の表の検査とゲートの判定。#950）の回帰テスト。

    python3 scripts/test-check-infra-csv.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-design-csv.py` と同じ形。

見るもの:

1. **決まりに反する形を、理由つきで落とす（1）**——見出し（順・列の過不足）・列の数・項目の重複・状態の値・根拠の形（`D-` を含む）・
   根拠が Q&A 表に無い・Q&A 表が無い・**表の状態と根拠の Q&A の状態の食い違い（3 通り）**・水準の形・水準が非機能要求の表に無い・非機能要求の表が無い。
2. **決まりどおりの形を通す**（陽性対照。`references/tree.md` の例・BOM・空でよい欄が空・複数の水準・必ず置く項目のほかの項目）。
3. **分けて出す**——未決定（3。表が無い・必ず置く項目が無い・`未決定` の行・決定の行の空の欄・未決定の印）と暫定（4）と違反（1）。
   **未決定の印のあるセルを値の違反に数えない**。違反と未決定が両方あれば 1。
4. **中身を検査していない形を 0 にしない（2）**——UTF-8 でない・空のファイル・ファイルでない・Q&A 表の見出しに状態が無い・ディレクトリが無い・
   引数の誤り・想定外の例外・`-OO` で引数なし。
5. **本体の定数が `references/tree.md` の「基盤要件」と一致する**（写しのずれ）——列・必ず置く項目・状態・状態ごとの根拠の Q&A の状態と空でよい列。
   **根拠の Q&A の状態の名前が `check-qa-csv.py` の状態にある**ことも見る。
6. **言語の判定（`is_python`）**——`Python`・`Python 3.12`・`python3` は Python、`TypeScript`・`Pythonic` でない語・空は Python でない。
7. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-infra-csv.py"
TREE = PLUGIN / "references" / "tree.md"

I = "shared/infra.csv"
Q = "shared/qa.csv"
N = "shared/nfr.csv"

I_HEAD = "項目,決定,理由,費用への影響,水準,根拠,状態\n"
Q_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
N_HEAD = "No,対象,指標,上限,単位,条件,根拠\n"


def qa_row(no: str, state: str) -> str:
    answer = "未回答" if state == "確認中" else "A（業務部が確認）"
    target = "—" if state == "確認中" else "shared/infra.csv"
    return f"{no},実現性・コスト,質問,A: x / B: y,A,理由,{answer},{target},{state},A が安い\n"


QA = Q_HEAD + qa_row("Q-F-001", "反映済み") + qa_row("Q-F-002", "反映済み") + qa_row("Q-F-003", "反映済み") \
    + qa_row("Q-F-004", "暫定反映") + qa_row("Q-F-005", "確認中") + qa_row("Q-F-006", "反映済み")
NFR = N_HEAD + "N-002,注文の受付,可用性,99.9,%,月の稼働で,契約\nN-004,注文のデータベース,バックアップ,1,日,毎日,監査\n"
ROWS = ("言語,Python 3.12,社内の保守の担当が読める,なし,,Q-F-001,決定\n"
        "DBMS,PostgreSQL 16,ライセンスの費用が要らない,運用費は月 2 万円,N-002・N-004,Q-F-002,決定\n"
        "ホスティング環境,AWS,既存の契約,月 5 万円,N-002,Q-F-003,決定\n")
GOOD = {I: I_HEAD + ROWS, Q: QA, N: NFR}


def infra(rows: str, **extra) -> dict:
    files = {I: I_HEAD + rows, Q: QA, N: NFR}
    files.update(extra)
    return files


def tree_example() -> str:
    """`references/tree.md` の「基盤要件」の例（```csv のブロック）。"""
    text = TREE.read_text(encoding="utf-8")
    body = text.split("\n## 基盤要件", 1)[1].split("\n## ", 1)[0]
    return re.search(r"```csv\n(.*?)```", body, flags=re.S).group(1)


# (名前, 置く表（パス → 中身。bytes はそのまま・"<dir>" はディレクトリ）, 引数（None なら根）, 期待する終了コード, 出力に含まれるべき文字列, 含まれてはならない文字列)
CASES: list[tuple[str, dict | None, list[str] | None, int, str, str]] = [
    ("決まりどおり", GOOD, None, 0, "OK（shared/infra.csv（3 行）", "未決定"),
    ("BOM 付き", {rel: "﻿" + body for rel, body in GOOD.items()}, None, 0, "OK（", "見出しの行"),
    ("ほかの項目を足す", infra(ROWS + "認証基盤,社内の SSO,既存の資産,なし,,Q-F-006,決定\n"), None, 0, "OK（shared/infra.csv（4 行）", ""),
    # tree.md の例（ホスティング環境が未決定）は 3
    ("tree.md の例", {I: tree_example(), Q: QA.replace(qa_row("Q-F-003", "反映済み"), qa_row("Q-F-003", "確認中")), N: NFR}, None, 3,
     "ホスティング環境 が未決定（根拠 Q-F-003 の回答待ち）", "形式の違反（"),
    # ---- 未決定（3）
    ("表が無い", {Q: QA}, None, 3, "基盤要件の表（shared/infra.csv）が無い——言語・DBMS・ホスティング環境が決まっていない", ""),
    ("必ず置く項目が無い", infra(ROWS.replace("ホスティング環境,AWS,既存の契約,月 5 万円,N-002,Q-F-003,決定\n", "")), None, 3,
     "必ず置く項目 'ホスティング環境' の行が無い", ""),
    ("未決定の行", infra(ROWS.replace("ホスティング環境,AWS,既存の契約,月 5 万円,N-002,Q-F-003,決定", "ホスティング環境,,,,,Q-F-005,未決定")),
     None, 3, "ホスティング環境 が未決定（根拠 Q-F-005 の回答待ち）", "形式の違反（"),
    ("決定の行の決定が空", infra(ROWS.replace("言語,Python 3.12,", "言語,,")), None, 3, "shared/infra.csv:2: 決定 が空", "形式の違反（"),
    ("決定の行の理由が空", infra(ROWS.replace(",社内の保守の担当が読める,", ",,")), None, 3, "shared/infra.csv:2: 理由 が空", ""),
    ("根拠が空", infra(ROWS.replace(",Q-F-001,決定", ",,決定")), None, 3, "shared/infra.csv:2: 根拠 が空", ""),
    ("状態が空", infra(ROWS.replace(",Q-F-001,決定", ",Q-F-001,")), None, 3, "shared/infra.csv:2: 状態 が空", ""),
    ("未決定の印", infra(ROWS.replace("言語,Python 3.12,", "言語,未定,")), None, 3, "決定 に未決定の印（未定）", "形式の違反（"),
    # 印のある根拠は値の決まりに当てない（Q&A 表に無いと言わない）
    ("根拠の未決定の印", infra(ROWS.replace(",Q-F-001,決定", ",TBD,決定")), None, 3, "根拠 に未決定の印（TBD）", "Q&A 表（shared/qa.csv）に無い"),
    # ---- 暫定（4）
    ("暫定の行", infra(ROWS.replace("DBMS,PostgreSQL 16,ライセンスの費用が要らない,運用費は月 2 万円,N-002・N-004,Q-F-002,決定",
                                   "DBMS,PostgreSQL 16,ライセンスの費用が要らない,運用費は月 2 万円,N-002・N-004,Q-F-004,暫定")),
     None, 4, "DBMS が暫定（根拠 Q-F-004 の確認待ち）: 'PostgreSQL 16'", "形式の違反（"),
    # 未決定と暫定が両方なら 3
    ("未決定と暫定", infra(ROWS.replace(",Q-F-002,決定", ",Q-F-004,暫定").replace(
        "ホスティング環境,AWS,既存の契約,月 5 万円,N-002,Q-F-003,決定", "ホスティング環境,,,,,Q-F-005,未決定")), None, 3, "暫定（1 件）", ""),
    # ---- 形式の違反（1）
    ("見出しの順が違う", infra(ROWS).copy() | {I: "決定,項目,理由,費用への影響,水準,根拠,状態\n" + ROWS}, None, 1, "見出しの行が決まりと違う", ""),
    ("列を足す", {I: I_HEAD.replace("状態", "状態,版") + ROWS.replace("決定\n", "決定,1\n"), Q: QA, N: NFR}, None, 1, "見出しの行が決まりと違う", ""),
    ("列の数", infra(ROWS + "監視,a,b\n"), None, 1, "shared/infra.csv:5: 列の数が 3", ""),
    ("項目の重複", infra(ROWS + "言語,Java,x,y,,Q-F-006,決定\n"), None, 1, "shared/infra.csv:5: 項目 が 2 行目と重複: 言語", ""),
    ("状態の値", infra(ROWS.replace(",Q-F-001,決定", ",Q-F-001,確定")), None, 1, "状態 が 決定・暫定・未決定 のどれでもない: '確定'", ""),
    ("根拠の形", infra(ROWS.replace(",Q-F-001,", ",Q-1,")), None, 1, "根拠 が共有の Q&A 表の番号（Q-001・Q-F-001）の形でない: 'Q-1'", ""),
    ("根拠が内部の表", infra(ROWS.replace(",Q-F-001,", ",D-F-001,")), None, 1, "根拠 が内部の Q&A 表の番号: 'D-F-001'", ""),
    ("根拠が Q&A 表に無い", infra(ROWS.replace(",Q-F-001,", ",Q-F-099,")), None, 1, "根拠 Q-F-099 が Q&A 表（shared/qa.csv）に無い", ""),
    ("Q&A 表が無い", {I: I_HEAD + ROWS, N: NFR}, None, 1, "根拠 Q-F-001 を照らす Q&A 表（shared/qa.csv）が無い", ""),
    ("決定なのに根拠が暫定反映", infra(ROWS.replace(",Q-F-001,決定", ",Q-F-004,決定")), None, 1,
     "状態 '決定' なのに、根拠 Q-F-004 の Q&A の状態が '暫定反映'（状態 '決定' なら '反映済み'）", ""),
    ("暫定なのに根拠が反映済み", infra(ROWS.replace(",Q-F-001,決定", ",Q-F-001,暫定")), None, 1,
     "状態 '暫定' なのに、根拠 Q-F-001 の Q&A の状態が '反映済み'（状態 '暫定' なら '暫定反映'）", ""),
    ("未決定なのに根拠が反映済み", infra(ROWS.replace("ホスティング環境,AWS,既存の契約,月 5 万円,N-002,Q-F-003,決定", "ホスティング環境,,,,,Q-F-003,未決定")),
     None, 1, "状態 '未決定' なのに、根拠 Q-F-003 の Q&A の状態が '反映済み'（状態 '未決定' なら '確認中'）", ""),
    ("水準の形", infra(ROWS.replace(",N-002・N-004,", ",N-002、N-004,")), None, 1, "水準 が非機能要求の番号（N-001。複数は「・」で区切る）の形でない: 'N-002、N-004'", ""),
    ("水準が非機能要求の表に無い", infra(ROWS.replace(",N-002・N-004,", ",N-002・N-009,")), None, 1, "水準 N-009 が非機能要求の表（shared/nfr.csv）に無い", ""),
    ("非機能要求の表が無い", {I: I_HEAD + ROWS, Q: QA}, None, 1, "水準 N-002 を照らす非機能要求の表（shared/nfr.csv）が無い", ""),
    # 水準を指さなければ非機能要求の表は要らない（陽性対照）
    ("水準を指さなければ非機能要求の表は要らない", {I: I_HEAD + ROWS.replace(",N-002・N-004,", ",,").replace(",N-002,", ",,"), Q: QA}, None, 0, "OK（", ""),
    # 違反と未決定が両方なら 1
    ("違反と未決定", infra(ROWS.replace(",Q-F-001,決定", ",Q-1,決定").replace("言語,Python 3.12,", "言語,未定,")), None, 1, "未決定（1 件）", ""),
    # ---- 判定していない（2）
    ("UTF-8 でない", {I: (I_HEAD + ROWS).encode("cp932"), Q: QA, N: NFR}, None, 2, "shared/infra.csv: UTF-8 として読めない", ""),
    ("空のファイル", {I: "", Q: QA, N: NFR}, None, 2, "shared/infra.csv: 空のファイル", ""),
    ("ファイルでない", {I: "<dir>", Q: QA}, None, 2, "shared/infra.csv: ファイルでない", ""),
    ("Q&A 表の見出しに状態が無い", infra(ROWS, **{Q: "No,質問\nQ-F-001,x\n"}), None, 2, "shared/qa.csv:1: 見出しに No・状態 の列が無い", ""),
    ("Q&A 表が UTF-8 でない", infra(ROWS, **{Q: QA.replace("—", "-").encode("cp932")}), None, 2, "shared/qa.csv: UTF-8 として読めない", ""),
    ("ディレクトリが無い", {}, ["no-such-dir"], 2, "ディレクトリが無い", ""),
    ("引数が多い", {}, ["a", "b"], 2, "usage:", ""),
    ("巨大なセル", infra(ROWS.replace("社内の保守の担当が読める", "x" * 200_000)), None, 2, "想定外の例外で止まった（Error: field larger", ""),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("見出しを見ない", "    if header != COLUMNS:", "    if False:", "見出しの順が違う"),
    ("列の数を見ない", "        if len(fields) != len(COLUMNS):", "        if False:", "列の数"),
    ("項目の重複を見ない", "            if item in items:", "            if False:", "項目の重複"),
    ("状態の値を見ない", "        if state_known and state not in INFRA_STATES:", "        if False:", "状態の値"),
    ("内部の番号を見ない", "            if qa.is_internal_number(number):", "            if False:", "根拠が内部の表"),
    ("根拠の形を見ない", "            elif not qa.NUMBER.fullmatch(number):", "            elif False:", "根拠の形"),
    ("Q&A 表が無いのを通す", "                if answers is None:", "                if False:", "Q&A 表が無い"),
    ("Q&A 表に無い番号を通す", "                elif number not in answers:", "                elif False:", "根拠が Q&A 表に無い"),
    ("状態と根拠の状態を照らさない", "                elif state_known and not qa_matches(state, answers[number]):", "                elif False:",
     "決定なのに根拠が暫定反映"),
    ("暫定を is_provisional で見ない", "        return qa.is_provisional(row)\n", "        return True\n", "暫定なのに根拠が反映済み"),
    ("未決定の根拠の状態を見ない", 'QA_STATE = {DECIDED: "反映済み", TENTATIVE: f"{qa.PROVISIONAL}", UNDECIDED: "確認中"}',
     'QA_STATE = {DECIDED: "反映済み", TENTATIVE: f"{qa.PROVISIONAL}", UNDECIDED: "反映済み"}', "未決定なのに根拠が反映済み"),
    ("水準の形を見ない", "                if not design.NFR_NUMBER.fullmatch(number):", "                if False:", "水準の形"),
    ("非機能要求の表が無いのを通す", "                if levels is None:", "                if False:", "非機能要求の表が無い"),
    ("水準を照らさない", "                elif number not in levels:", "                elif False:", "水準が非機能要求の表に無い"),
    ("水準を空でよいことにしない", '    DECIDED: {"水準"},', "    DECIDED: set(),", "水準を指さなければ非機能要求の表は要らない"),
    ("決定の行の決定を空でよいことにする", '    DECIDED: {"水準"},', '    DECIDED: {"水準", "決定"},', "決定の行の決定が空"),
    ("必ず置く項目を見ない", "    for item in REQUIRED_ITEMS:", "    for item in ():", "必ず置く項目が無い"),
    ("未決定の行を数えない", "        if state_known and state == UNDECIDED:", "        if False:", "未決定の行"),
    ("暫定の行を数えない", "        if state_known and state == TENTATIVE:", "        if False:", "暫定の行"),
    ("表が無いのを 0 にする", "        if self.missing or self.undecided:", "        if self.undecided:", "表が無い"),
    ("暫定を 0 にする", "        if self.provisional:\n            return 4", "        if False:\n            return 4", "暫定の行"),
    ("暫定を未決定より先にする", "        if self.missing or self.undecided:\n            return 3\n        if self.provisional:\n            return 4",
     "        if self.provisional:\n            return 4\n        if self.missing or self.undecided:\n            return 3", "未決定と暫定"),
    ("未決定の印を見ない", "    hits = design.markers(value)", "    hits = []", "未決定の印"),
    ("未決定の印を値の決まりに当てる",
     "        report.undecided.append(f\"{where}: {column} に未決定の印（{'・'.join(hits)}）: {value.strip()!r}\")\n        return False",
     "        report.undecided.append(f\"{where}: {column} に未決定の印（{'・'.join(hits)}）: {value.strip()!r}\")", "根拠の未決定の印"),
    ("空の欄を数えない", '            report.undecided.append(f"{where}: {column} が空")', "            pass", "決定の行の決定が空"),
    ("読めない表を 2 にしない", "        if self.unreadable:\n            return 2", "        if False:\n            return 2", "UTF-8 でない"),
    ("ファイルでないものを無い表と読む", "            if path.exists():", "            if False:", "ファイルでない"),
    ("空のファイルを読む", '    if not text.strip():\n        raise Unreadable(f"{rel}: 空のファイル")', "    if False:\n        pass", "空のファイル"),
    ("Q&A 表の見出しを見ない", "    if key not in header or (value is not None and value not in header):", "    if False:", "Q&A 表の見出しに状態が無い"),
]

# -OO（docstring が無い）で引数なしに呼んでも、使い方の誤りとして 2（#286）。(名前, 壊す前, 壊した後)
OO_MUTATIONS = [("-OO で docstring が無いと落ちる", "__doc__.splitlines()[2] if __doc__ else", "__doc__.splitlines()[2] if True else")]

# 言語の判定（`is_python`）。(値, Python か)
PYTHON_CASES = [("Python", True), ("Python 3.12", True), ("python3", True), (" PYTHON（Django）", True),
                ("TypeScript", False), ("Pythonic", False), ("Java（Python は使わない）", False), ("", False)]
PYTHON_MUTATIONS = [("先頭でなくても Python と読む", "    return PYTHON.match(value) is not None", "    return PYTHON.search(value) is not None"),
                    ("後ろの文字を見ない", 'PYTHON = re.compile(r"\\s*python(?![a-z])", re.IGNORECASE)', 'PYTHON = re.compile(r"\\s*python", re.IGNORECASE)')]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def run_one(scripts: Path, root: Path, files: dict, args: list[str] | None) -> tuple[int, str]:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if body == "<dir>":
            path.mkdir()
        elif isinstance(body, bytes):
            path.write_bytes(body)
        else:
            path.write_text(body, encoding="utf-8")
    argv = [str(root)] if args is None else args
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), *argv], capture_output=True, text=True, cwd=root)
    return proc.returncode, proc.stdout + proc.stderr


def run_all(scripts: Path, work: Path, only: str | None = None) -> dict[str, tuple[int, str]]:
    return {name: run_one(scripts, work / f"case{i}", files, args) for i, (name, files, args, _, _, _) in enumerate(CASES)
            if only is None or name == only}


def as_expected(name: str, result: tuple[int, str]) -> bool:
    _, _, _, code, text, absent = next(case for case in CASES if case[0] == name)
    return result[0] == code and text in result[1] and not (absent and absent in result[1]) and "Traceback" not in result[1]


def oo_problems(scripts: Path, cwd: Path) -> list[str]:
    proc = subprocess.run([sys.executable, "-I", "-OO", str(scripts / TARGET)], capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 2 or "usage:" not in proc.stderr or "Traceback" in proc.stderr:
        return [f"-OO の引数なし: 終了 {proc.returncode}: {proc.stderr[-300:]!r}"]
    return []


def section(markdown: str, heading: str) -> str:
    """`heading` で始まる見出しの行から、次の同じか上の水準の見出しまで。"""
    level = len(heading) - len(heading.lstrip("#"))
    start = markdown.index(heading)
    rest = markdown[start + len(heading):]
    found = re.search(rf"^#{{1,{level}}} ", rest, flags=re.MULTILINE)
    return rest[:found.start()] if found else rest


def rows_of(text: str) -> list[list[str]]:
    """表の本文の行（見出しと区切りを除く）のセル。1 列目がバッククォートで囲まれた行だけ。"""
    return [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in text.splitlines() if re.match(r"^\| `[^`]+` \|", line)]


def reference_mismatches(module, tree: str, qa_states: list[str]) -> list[str]:
    """本体の定数が `references/tree.md` の「基盤要件」と一致するか（写しのずれ）。`module` は読み込んだ本体。"""
    problems = []
    infra = section(tree, "## 基盤要件")
    if f"版の中の `{module.INFRA}` に置く" not in infra:
        problems.append(f"置き場所（{module.INFRA}）が tree.md に無い")
    columns = [row[0].strip("`") for row in rows_of(section(infra, "### 列"))]
    if columns != module.COLUMNS:
        problems.append(f"列が違う（tree.md {columns} ／ 本体 {module.COLUMNS}）")
    required = re.search(r"必ず置く項目は ((?:`[^`]+`・)+`[^`]+`) の", infra)
    items = tuple(re.findall(r"`([^`]+)`", required.group(1))) if required else None
    if items != module.REQUIRED_ITEMS:
        problems.append(f"必ず置く項目が違う（tree.md {items} ／ 本体 {module.REQUIRED_ITEMS}）")
    states = rows_of(section(infra, "### 状態"))
    names = tuple(row[0].strip("`") for row in states)
    if names != module.INFRA_STATES:
        problems.append(f"状態が違う（tree.md {names} ／ 本体 {module.INFRA_STATES}）")
    for row in states:
        if len(row) != 4:
            problems.append(f"状態の表の列の数が 4 でない: {row}")
            continue
        state = row[0].strip("`")
        answer = row[2].strip("`")
        if module.QA_STATE.get(state) != answer:
            problems.append(f"{state}: 根拠の Q&A の状態が違う（tree.md {answer} ／ 本体 {module.QA_STATE.get(state)}）")
        if answer not in qa_states:
            problems.append(f"{state}: 根拠の Q&A の状態 {answer} が check-qa-csv.py の状態 {qa_states} に無い")
        empty = set(re.findall(r"`([^`]+)`", row[3]))
        if empty != module.MAY_BE_EMPTY.get(state):
            problems.append(f"{state}: 空でよい列が違う（tree.md {sorted(empty)} ／ 本体 {sorted(module.MAY_BE_EMPTY.get(state, set()))}）")
    if f"複数は `{module.LEVEL_SEPARATOR}` で区切る" not in infra:
        problems.append(f"水準の区切り（{module.LEVEL_SEPARATOR}）が tree.md に無い")
    return problems


# references を崩すと不一致になる（突き合わせが空振りでないこと）。(名前, 崩す前, 崩した後)
REFERENCE_MUTATIONS = [
    ("列を消す", "| `費用への影響` | 開発費・運用費への影響", "| 費用への影響 | 開発費・運用費への影響"),
    ("必ず置く項目を変える", "**必ず置く項目は `言語`・`DBMS`・`ホスティング環境` の 3 つ**", "**必ず置く項目は `言語`・`DBMS` の 3 つ**"),
    ("根拠の状態を変える", "| `暫定` | 利用者がまだ確かめていない暫定の回答で決めた（`qa-csv.md` の「暫定の回答」） | `暫定反映` |",
     "| `暫定` | 利用者がまだ確かめていない暫定の回答で決めた（`qa-csv.md` の「暫定の回答」） | `確認中` |"),
    ("空でよい列を変える", "| `確認中` | `決定`・`理由`・`費用への影響`・`水準` |", "| `確認中` | `決定`・`理由`・`水準` |"),
    ("置き場所を変える", "版の中の `shared/infra.csv` に置く", "版の中の `requirements/infra.csv` に置く"),
]


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def load(path: Path, name: str = "check_infra_csv_under_test"):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def python_problems(module) -> list[str]:
    return [f"{value!r}: is_python が {module.is_python(value)}（期待 {want}）" for value, want in PYTHON_CASES
            if module.is_python(value) != want]


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    with tempfile.TemporaryDirectory(prefix="infra-csv-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        for name, result in run_all(scripts, tmp_path / "work").items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result[0]} {result[1][-400:]}")

        module = load(scripts / TARGET)
        tree = TREE.read_text(encoding="utf-8")
        qa_states = list(module.qa.STATES)
        problems = reference_mismatches(module, tree, qa_states)
        check("本体の定数が references と一致しない", not problems, "; ".join(problems))
        for name, before, after in REFERENCE_MUTATIONS:
            if tree.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {tree.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(module, tree.replace(before, after), qa_states)))
        check("根拠の Q&A の状態が check-qa-csv.py に無いと不一致にならない",
              bool(reference_mismatches(module, tree, [s for s in qa_states if s != "確認中"])))

        problems = python_problems(module)
        check("言語の判定が期待どおりでない", not problems, "; ".join(problems))

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            result = run_all(mutated, tmp_path / f"mutwork{index}", only=killer)[killer]
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result[1][-300:])

        for index, (name, before, after) in enumerate(PYTHON_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"py-mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}", bool(python_problems(load(mutated / TARGET, f"py_mut{index}"))))

        problems = oo_problems(scripts, tmp_path)
        check("-OO の引数なしで使い方の誤り（2）にならない", not problems, "; ".join(problems))
        for index, (name, before, after) in enumerate(OO_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"oo-mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が生き残った: {name}", bool(oo_problems(mutated, tmp_path)))

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS) + len(PYTHON_MUTATIONS) + len(OO_MUTATIONS)} 件・"
          f"references の崩し {len(REFERENCE_MUTATIONS) + 1} 件・言語の判定 {len(PYTHON_CASES)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
