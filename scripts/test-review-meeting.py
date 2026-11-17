#!/usr/bin/env python3
"""`review-meeting.py`（spec-loop の、モックと Q&A 表で進めるレビュー会の口。#1082）の回帰テスト。

    python3 scripts/test-review-meeting.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-intake-code.py` と同じ形。

**このテストは実環境を触らない。** 正本（`docs/` の 2 つの版・画面の表・`reviews/<日付>/`）は試料ごとに一時ディレクトリに作り、
**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる**（正本リポジトリで単体で動くこと）。
足した表には、写した**本物の `check-qa-csv.py`** を CLI で走らせる。

**守ること**（各行に変異が 1 つ以上ある——下の `MUTATIONS`）:

- `notes` は何も書かない（Q&A 表のバイトもファイルの一覧も同じ）。指摘は対象・メモ・起票済みか（`指摘 1` を `指摘 10` と取り違えない）、回答の候補はいまの Q&A の行（状態・回答・選択肢）とメモ・発言者を出す
- 会のディレクトリが `reviews/<YYYY-MM-DD>/`（正本の根の直下）でなければ 2
- 会の記録の決まり（見出し・種類・空のメモ・番号を書いた指摘・表に無い／共有の層でない回答の番号・空の発言者・改行のある対象）に反すれば 1
- `rows` の行は `確認中`・`未回答`・`—` で、振り分けのファイルに回答・状態・反映先の鍵があれば 1 で何も書かない
- `rows` の起票元は `要求確定（レビュー会 <日付>）`、質問の後ろに `（レビュー会 <日付> の指摘 <行>。対象: <対象>）`（対象が空なら `。対象:` を付けない）
- `rows` は会の指摘を落とさない——候補にも見送りにも無い・両方にある・指摘でない行／無い行／真偽値を指す・起票済みの指摘をまた指す、は 1 で何も書かない
- 見送りの種類は `見た目`・`既にある`（在る番号）・`質問にしない` だけで、`detail` は空にしない（反すれば 1）。見送りは Q&A 表に行を足さない
- 同じ振り分けで当て直しても同じ質問を重ねて足さず、1 で何も書かない
- 番号は `Q-R-` の、全部の版を通した最大の次（ほかの印は数えない）で、作業中の版の表に書く。書いた表は本物の `check-qa-csv.py` を通る。`--dry-run` は書かない
- `rows` は既にある表の BOM と CRLF を保ち、既にある行のバイトを変えずに足す。足す行が無ければ書かない
- `groups` の逆引きは、画面の行・その画面の項目・その画面を遷移元にする遷移（遷移先ではない）のセルを、重ね合わせた全体（後の版の画面の行を含む）で見て、画面の表の順で最初の画面に入れる
- `groups` は出力先が入力の Q&A 表なら 2 で書かない。セルの番号は境界つきで読む（`XQ-R-005` を `Q-R-005` と読まない）
- 記録の行の番号は見出しと空行を除いて数える（`指摘 1`・`指摘 10` の試料）
- `groups` の出力は画面のまとまり（画面の表の順・質問の無い画面は出さない・名前は `画面 <画面ID> <画面名>`）、続けてテーマ（渡した順）。中の質問は Q&A 表の順
- `groups` のテーマの決まり（画面に掛かる質問・載らない番号・漏れ・重複・空のテーマ・画面のまとまりと同じ名前・オブジェクトでない）に反すれば 1 で何も書かない。内部の層の表は 2
- 本体の定数が `references/tree.md` の「レビュー会の記録」の表と一致する

**変異テストを含む。** 写した本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TREE = REAL_REPO / "plugins" / "spec-loop" / "references" / "tree.md"
TARGET = "review-meeting.py"
DATE = "2026-11-20"
HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響"


def qa_row(no: str, question: str, state: str = "確認中", answer: str = "未回答", target: str = "—") -> str:
    return f"{no},要求確定,{question},A: はい / B: いいえ,A,理由,{answer},{target},{state},"


QA_V1 = "\n".join([HEADER, qa_row("Q-R-004", "済んだ質問", "反映済み", "A（業務部が回答）", "決定表 1 行目"),
                   "Q-S-012,仕様レビュー,別の印の質問,A: はい / B: いいえ,A,理由,未回答,—,確認中,"]) + "\n"
QA_V2_ROWS = [qa_row("Q-R-002", "保存の後はどこへ戻りますか？"), qa_row("Q-R-003", "保存の確認を出しますか？"),
              qa_row("Q-R-005", "通知はメールですか？"), qa_row("Q-R-006", "担当者で並び替えますか？"),
              qa_row("Q-R-007", "締めの時刻は何時ですか？"), qa_row("Q-R-008", "備考の欄を出しますか？"),
              qa_row("Q-R-009", "設定を保存しますか？")]
# v2 の表は BOM と CRLF（既にある行のバイトを保つことを見る）
QA_V2 = "﻿" + "\r\n".join([HEADER] + QA_V2_ROWS) + "\r\n"
SCREENS_V1 = "画面ID,画面名,種別,根拠\nS-001,受注一覧,list,\nS-002,受注入力,form,\nS-003,設定,form,\nS-004,ヘルプ,detail,\n"  # S-004 は質問が無い
SCREENS_V2 = "画面ID,画面名,種別,根拠\nS-003,設定,form,Q-R-009\n"   # 後の版で画面の行に番号を足す
# I-003 の `XQ-R-005` は番号ではない（境界——screen-spec の逆引きと同じ読み方。読めば Q-R-005 が S-001 に入る）
ITEMS_V1 = "番号,画面ID,項目名,根拠\nI-001,S-002,備考,Q-R-008\nI-002,S-001,担当者,Q-R-006\nI-003,S-001,記号,XQ-R-005\n"
TRANSITIONS_V1 = ("番号,遷移元,きっかけ,遷移先,根拠\nT-001,S-001,押す,S-002,Q-R-002\n"
                  "T-002,S-002,保存,S-001,Q-R-003\nT-003,S-003,戻る,S-001,Q-R-006\n")
NOTES = ("種類,No,対象,メモ,発言者\n"
         "指摘,,S-002 I-001,備考は 2 行要る,業務部\n"
         ",,,,\n"            # Excel の空行（数えない——指摘 2 は次の行）
         "指摘,,,通知の文が硬い,業務部\n"
         "指摘,,S-001,色が薄い,業務部\n"
         "指摘,,S-001,担当者の並び替えが要る,業務部\n"
         "回答,Q-R-002,,一覧に戻りたい,業務部 田中\n")
GOOD = {
    "candidates": [
        {"note": 1, "question": "備考の欄は何行にしますか？", "options": ["1 行", "2 行"], "recommend": "B", "reason": "会で 2 行と言われた"},
        {"note": 2, "question": "通知の文は丁寧語にしますか？", "options": ["丁寧語", "今のまま"], "recommend": "A", "reason": "会で硬いと言われた"},
    ],
    "skipped": [{"note": 3, "kind": "見た目", "detail": "一覧の色"}, {"note": 4, "kind": "既にある", "detail": "Q-R-006 と同じ"}],
}
NEW_ROWS = [
    "Q-R-010,要求確定（レビュー会 2026-11-20）,備考の欄は何行にしますか？（レビュー会 2026-11-20 の指摘 1。対象: S-002 I-001）,"
    "A: 1 行 / B: 2 行,B,会で 2 行と言われた,未回答,—,確認中,",
    "Q-R-011,要求確定（レビュー会 2026-11-20）,通知の文は丁寧語にしますか？（レビュー会 2026-11-20 の指摘 2）,"
    "A: 丁寧語 / B: 今のまま,A,会で硬いと言われた,未回答,—,確認中,",
]
THEMES = {"通知": ["Q-R-005"], "その他": ["Q-R-007"]}   # 名前の順と違う順に渡す
GROUPS = {"画面 S-001 受注一覧": ["Q-R-002", "Q-R-006"], "画面 S-002 受注入力": ["Q-R-003", "Q-R-008"],
          "画面 S-003 設定": ["Q-R-009"], "通知": ["Q-R-005"], "その他": ["Q-R-007"]}

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def variant(**change) -> dict:
    data = json.loads(json.dumps(GOOD, ensure_ascii=False))
    for key, value in change.items():
        if key.startswith("c_"):
            data["candidates"][0][key[2:]] = value
        elif key.startswith("s_"):
            data["skipped"][0][key[2:]] = value
        else:
            data[key] = value
    return data


class Env:
    def __init__(self, work: Path, scripts: Path):
        self.work, self.scripts, self.n = work, scripts, 0
        home = work / "home"
        home.mkdir(exist_ok=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update({"HOME": str(home), "GIT_CONFIG_GLOBAL": str(home / "gitconfig"), "GIT_CONFIG_NOSYSTEM": "1"})

    def run(self, *args: str) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, "-I", str(self.scripts / TARGET), *args], capture_output=True, text=True,
                              env=self.env, cwd=self.work)
        return proc.returncode, proc.stdout + proc.stderr

    def repo(self, notes: str = NOTES, triage: dict | None = None) -> Path:
        self.n += 1
        root = self.work / f"canon-{self.n}"
        write(root / "docs/v1/shared/qa.csv", QA_V1)
        write(root / "docs/v2/shared/qa.csv", QA_V2)
        write(root / "docs/v1/requirements/screens/data/screens.csv", SCREENS_V1)
        write(root / "docs/v2/requirements/screens/data/screens.csv", SCREENS_V2)
        write(root / "docs/v1/requirements/screens/data/screen-items.csv", ITEMS_V1)
        write(root / "docs/v1/requirements/screens/data/transitions.csv", TRANSITIONS_V1)
        write(root / "reviews" / DATE / "notes.csv", notes)
        write(root / "reviews" / DATE / "triage.json", json.dumps(GOOD if triage is None else triage, ensure_ascii=False))
        return root


def tree_files(root: Path) -> dict[str, tuple[bytes, int]]:
    """パス → (中身, inode)。同じ中身で置き換えても（書いても）違うと読む。"""
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_ino) for p in sorted(root.rglob("*")) if p.is_file()}


def checker_ok(e: Env, path: Path) -> bool:
    proc = subprocess.run([sys.executable, "-I", str(e.scripts / "check-qa-csv.py"), str(path)], capture_output=True, text=True)
    return proc.returncode == 0


def v2(root: Path) -> Path:
    return root / "docs/v2/shared/qa.csv"


# ---------------------------------------------------------------- 試料

def case_notes(e: Env) -> str | None:
    root = e.repo()
    before = tree_files(root)
    code, out = e.run("notes", str(root), str(root / "reviews" / DATE))
    if code != 0:
        return f"終了 {code}: {out}"
    if tree_files(root) != before:
        return "notes が何かを書いた"
    for want in ("指摘 4 件・回答の候補 1 件", "指摘 1（対象: S-002 I-001）: 備考は 2 行要る — まだ起票していない",
                 "指摘 2（対象なし）: 通知の文が硬い", "Q-R-002（いまの状態: 確認中・回答: 未回答）: 保存の後はどこへ戻りますか？",
                 "選択肢: A: はい / B: いいえ", "メモ: 一覧に戻りたい（業務部 田中）"):
        if want not in out:
            return f"出力に {want!r} が無い: {out}"
    return None


def case_notes_raised(e: Env) -> str | None:
    """起票済みの指摘を名指しする——`指摘 1` の印が `指摘 10` の行に当たらない。"""
    notes = "種類,No,対象,メモ,発言者\n" + "".join(f"指摘,,,メモ {i},業務部\n" for i in range(1, 11))
    root = e.repo(notes=notes)
    raised = qa_row("Q-R-020", f"十番目（レビュー会 {DATE} の指摘 10）")
    write(v2(root), QA_V2 + raised + "\r\n")
    code, out = e.run("notes", str(root), str(root / "reviews" / DATE))
    if code != 0:
        return f"終了 {code}: {out}"
    if "指摘 10（対象なし）: メモ 10 — 起票済み: Q-R-020" not in out:
        return f"指摘 10 が起票済みと出ない: {out}"
    if "指摘 1（対象なし）: メモ 1 — まだ起票していない" not in out:
        return f"指摘 1 を指摘 10 の印で起票済みと取り違えた: {out}"
    return None


def case_bad_dir(e: Env) -> str | None:
    root = e.repo()
    write(root / "reviews" / "next" / "notes.csv", NOTES)
    write(root / "docs" / DATE / "notes.csv", NOTES)
    for directory in (root / "reviews" / "next", root / "docs" / DATE, root / "reviews"):
        code, out = e.run("notes", str(root), str(directory))
        if code != 2:
            return f"{directory.relative_to(root)}: 終了 {code}（期待 2）: {out}"
    return None


BAD_NOTES = {
    "見出し": "種類,No,メモ,対象,発言者\n指摘,,S-001,色,業務部\n",
    "種類": "種類,No,対象,メモ,発言者\n感想,,S-001,よい,業務部\n",
    "空のメモ": "種類,No,対象,メモ,発言者\n指摘,,S-001,,業務部\n",
    "番号を書いた指摘": "種類,No,対象,メモ,発言者\n指摘,Q-R-099,S-001,要る,業務部\n",
    "表に無い回答の番号": "種類,No,対象,メモ,発言者\n回答,Q-R-099,,A,業務部\n",
    "内部の層の回答の番号": "種類,No,対象,メモ,発言者\n回答,D-R-001,,A,業務部\n",
    "空の発言者": "種類,No,対象,メモ,発言者\n回答,Q-R-002,,A,\n",
    "改行のある対象": '種類,No,対象,メモ,発言者\n指摘,,"S-001\nS-002",要る,業務部\n',
}


def case_bad_notes(e: Env) -> str | None:
    for name, body in BAD_NOTES.items():
        root = e.repo(notes=body)
        before = tree_files(root)
        for command in ("notes", "rows"):
            code, out = e.run(command, str(root), str(root / "reviews" / DATE))
            if code != 1:
                return f"{name}（{command}）: 終了 {code}（期待 1）: {out}"
            if tree_files(root) != before:
                return f"{name}（{command}）: 書いた"
    return None


def case_rows(e: Env) -> str | None:
    root = e.repo()
    before = v2(root).read_bytes()
    code, out = e.run("rows", str(root), str(root / "reviews" / DATE))
    if code != 0:
        return f"終了 {code}: {out}"
    after = v2(root).read_bytes()
    if not after.startswith(before):
        return "既にある行のバイトが変わった（BOM・CRLF）"
    added = after[len(before):].decode("utf-8")
    if added != "".join(r + "\r\n" for r in NEW_ROWS):
        return f"足した行が違う: {added!r}"
    if not checker_ok(e, v2(root)):
        return "足した表が check-qa-csv.py を通らない"
    if (root / "docs/v1/shared/qa.csv").read_text(encoding="utf-8") != QA_V1:
        return "前の版の表を書き換えた"
    if "指摘 3: 見た目——一覧の色" not in out or "指摘 4: 既にある——Q-R-006 と同じ" not in out:
        return f"見送りを出さない: {out}"
    return None


def case_dry_run(e: Env) -> str | None:
    root = e.repo()
    before = tree_files(root)
    code, out = e.run("rows", str(root), str(root / "reviews" / DATE), "--dry-run")
    if code != 0 or tree_files(root) != before:
        return f"終了 {code}・書いたか {tree_files(root) != before}: {out}"
    if NEW_ROWS[0] not in out:
        return f"足すはずの行を出さない: {out}"
    return None


def case_rerun(e: Env) -> str | None:
    """同じ振り分けで当て直しても足さない（0・表を書かない）。末尾に足した指摘は、前の振り分けを残したまま足して当て直せる。"""
    root = e.repo()
    e.run("rows", str(root), str(root / "reviews" / DATE))
    first = tree_files(root)
    code, out = e.run("rows", str(root), str(root / "reviews" / DATE))
    if code != 0 or tree_files(root) != first or "同じ質問が既にあるので足していない" not in out:
        return f"当て直し: 終了 {code}・書いたか {tree_files(root) != first}: {out}"
    write(root / "reviews" / DATE / "notes.csv", NOTES + "指摘,,S-003,保存の前に確かめたい,業務部\n")
    triage = json.loads(json.dumps(GOOD, ensure_ascii=False))
    triage["candidates"].append({"note": 6, "question": "設定の保存の前に確認を出しますか？", "options": ["出す", "出さない"],
                                 "recommend": "A", "reason": "会で言われた"})
    write(root / "reviews" / DATE / "triage.json", json.dumps(triage, ensure_ascii=False))
    before = v2(root).read_bytes()
    code, out = e.run("rows", str(root), str(root / "reviews" / DATE))
    added = v2(root).read_bytes()[len(before):].decode("utf-8")
    want = ("Q-R-012,要求確定（レビュー会 2026-11-20）,設定の保存の前に確認を出しますか？（レビュー会 2026-11-20 の指摘 6。対象: S-003）,"
            "A: 出す / B: 出さない,A,会で言われた,未回答,—,確認中,\r\n")
    if code != 0 or added != want:
        return f"末尾に足した指摘: 終了 {code}・足した行 {added!r}: {out}"
    return None


def case_raised_again(e: Env) -> str | None:
    """起票済みの指摘を、別の質問でまた候補にする・見送りにする——1 で何も書かない。"""
    root = e.repo()
    e.run("rows", str(root), str(root / "reviews" / DATE))
    first = v2(root).read_bytes()
    for triage in ({"candidates": [{"note": 1, "question": "備考の欄の長さは？", "options": ["短い", "長い"], "recommend": "A", "reason": "r"}],
                    "skipped": []},
                   {"candidates": [], "skipped": [{"note": 1, "kind": "質問にしない", "detail": "もう訊いた"}]}):
        write(root / "reviews" / DATE / "triage.json", json.dumps(triage, ensure_ascii=False))
        code, out = e.run("rows", str(root), str(root / "reviews" / DATE))
        if code != 1 or v2(root).read_bytes() != first or "もう起票してある" not in out:
            return f"起票済みをまた指した: 終了 {code}: {out}"
    return None


BAD_TRIAGE = {
    "回答の鍵": variant(c_answer="A"),
    "状態の鍵": variant(c_状態="反映済み"),
    "漏れた指摘": variant(skipped=[GOOD["skipped"][0]]),
    "両方にある": variant(skipped=GOOD["skipped"] + [{"note": 1, "kind": "質問にしない", "detail": "x"}]),
    "見送りが 2 つ": variant(skipped=GOOD["skipped"] + [{"note": 3, "kind": "質問にしない", "detail": "x"}]),
    "回答の行を指す": variant(c_note=5),
    "無い行を指す": variant(c_note=9),
    "真偽値を指す": variant(c_note=True),
    "知らない見送りの種類": variant(s_kind="好み"),
    "在らない番号の既にある": variant(skipped=[GOOD["skipped"][0], {"note": 4, "kind": "既にある", "detail": "Q-R-099 と同じ"}]),
    "番号の無い既にある": variant(skipped=[GOOD["skipped"][0], {"note": 4, "kind": "既にある", "detail": "前に訊いた"}]),
    "空の detail": variant(s_detail=" "),
    "選択肢が 1 つ": variant(c_options=["1 行"]),
    "推奨がラベルでない": variant(c_recommend="C"),
    "改行のある質問": variant(c_question="備考は\n何行？"),
    "知らない鍵": variant(c_extra="x"),
    "候補が並びでない": variant(candidates={}),
    "同じ候補が 2 つ": variant(candidates=GOOD["candidates"] + [GOOD["candidates"][0]]),
}


def case_bad_triage(e: Env) -> str | None:
    for name, triage in BAD_TRIAGE.items():
        root = e.repo(triage=triage)
        before = tree_files(root)
        code, out = e.run("rows", str(root), str(root / "reviews" / DATE))
        if code != 1:
            return f"{name}: 終了 {code}（期待 1）: {out}"
        if tree_files(root) != before:
            return f"{name}: 書いた"
    return None


def case_no_new(e: Env) -> str | None:
    """見送りだけなら表を書かない。振り分けのファイルが無ければ 2。"""
    notes = "種類,No,対象,メモ,発言者\n指摘,,S-001,色が薄い,業務部\n"
    root = e.repo(notes=notes, triage={"candidates": [], "skipped": [{"note": 1, "kind": "見た目", "detail": "色"}]})
    before = tree_files(root)
    code, out = e.run("rows", str(root), str(root / "reviews" / DATE))
    if code != 0 or tree_files(root) != before:
        return f"見送りだけ: 終了 {code}・書いたか {tree_files(root) != before}: {out}"
    (root / "reviews" / DATE / "triage.json").unlink()
    code, out = e.run("rows", str(root), str(root / "reviews" / DATE))
    if code != 2:
        return f"振り分けのファイルが無い: 終了 {code}（期待 2）: {out}"
    return None


def run_groups(e: Env, root: Path, themes, qa: Path | None = None) -> tuple[int, str, Path]:
    themes_path = root / "build" / "themes.json"
    write(themes_path, themes if isinstance(themes, str) else json.dumps(themes, ensure_ascii=False))
    out = root / "build" / "req-loop" / "groups.json"
    code, text = e.run("groups", str(root), str(qa or v2(root)), str(themes_path), str(out))
    return code, text, out


def case_groups(e: Env) -> str | None:
    root = e.repo()
    code, out, path = run_groups(e, root, THEMES)
    if code != 0:
        return f"終了 {code}: {out}"
    got = json.loads(path.read_text(encoding="utf-8"))
    if list(got.items()) != list(GROUPS.items()):
        return f"まとまりが違う: {got}"
    return None


BAD_THEMES = {
    "画面に掛かる質問": {"その他": ["Q-R-005", "Q-R-007", "Q-R-002"]},
    "載らない番号": {"その他": ["Q-R-005", "Q-R-007", "Q-R-004"]},
    "漏れ": {"その他": ["Q-R-005"]},
    "重複": {"その他": ["Q-R-005", "Q-R-007"], "別": ["Q-R-005"]},
    "空のテーマ": {"その他": ["Q-R-005", "Q-R-007"], "空": []},
    "画面のまとまりと同じ名前": {"画面 S-001 受注一覧": ["Q-R-005", "Q-R-007"]},
    "オブジェクトでない": ["Q-R-005", "Q-R-007"],
}


def case_bad_themes(e: Env) -> str | None:
    for name, themes in BAD_THEMES.items():
        root = e.repo()
        code, out, path = run_groups(e, root, themes)
        if code != 1 or path.exists():
            return f"{name}: 終了 {code}（期待 1）・書いたか {path.exists()}: {out}"
    root = e.repo()
    before = v2(root).read_bytes()
    themes_path = root / "build" / "themes.json"
    write(themes_path, json.dumps(THEMES, ensure_ascii=False))
    code, out = e.run("groups", str(root), str(v2(root)), str(themes_path), str(v2(root)))
    if code != 2 or v2(root).read_bytes() != before:
        return f"出力先が入力の表: 終了 {code}（期待 2）・表が変わったか {v2(root).read_bytes() != before}: {out}"
    internal = root / "docs/v2/spec/qa-dev.csv"
    write(internal, HEADER + "\nD-S-001,仕様レビュー,内部の質問,A: x / B: y,A,r,未回答,—,確認中,\n")
    code, out, path = run_groups(e, root, {}, internal)
    if code != 2 or path.exists():
        return f"内部の層の表: 終了 {code}（期待 2）: {out}"
    return None


def case_constants(e: Env) -> str | None:
    """本体の定数が `references/tree.md` の「レビュー会の記録」の表と一致する。"""
    spec = importlib.util.spec_from_file_location("rm", e.scripts / TARGET)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    text = TREE.read_text(encoding="utf-8")
    section = text.split("## レビュー会の記録", 1)[1].split("\n## ", 1)[0] if "## レビュー会の記録" in text else ""
    table: dict[str, list[str]] = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2:
            table[cells[0]] = re.findall(r"`([^`]+)`", cells[1])
    want = {
        "置き場所": [f"{mod.REVIEWS}/<YYYY-MM-DD>/"],
        "会で見せたモック": [mod.MOCK_NAME], "会の記録": [mod.NOTES_NAME], "振り分けのファイル": [mod.TRIAGE_NAME],
        "記録の列": list(mod.NOTE_COLUMNS), "記録の種類": list(mod.NOTE_KINDS), "見送りの種類": list(mod.SKIP_KINDS),
        "起票元の詳細": [f"{mod.SOURCE_NAME}（{mod.SOURCE_DETAIL.format(date='<日付>')}）"],
        "質問の添え書き": [mod.NOTE_HEAD.format(date="<日付>", line="<行>") + "。対象: <対象>）"],
        "画面のまとまりの名前": [mod.SCREEN_GROUP.format(id="<画面ID>", name="<画面名>")],
    }
    wrong = [f"{k}: 文書 {table.get(k)} ／ 本体 {v}" for k, v in want.items() if table.get(k) != v]
    return "; ".join(wrong) or None


CASES = {
    "notes": case_notes, "notes_raised": case_notes_raised, "bad_dir": case_bad_dir, "bad_notes": case_bad_notes,
    "rows": case_rows, "dry_run": case_dry_run, "rerun": case_rerun, "raised_again": case_raised_again,
    "bad_triage": case_bad_triage, "no_new": case_no_new, "groups": case_groups, "bad_themes": case_bad_themes,
    "constants": case_constants,
}

# (名前, 壊す前, 壊した後, 殺すはずの試料)
MUTATIONS: list[tuple[str, str, str, str]] = [
    # notes
    ("notes が回答の候補の行を出さない", '        out.append(f"    メモ: {squash(r[\'メモ\'])}（{r[\'発言者\']}）")\n', "", "notes"),
    ("notes が起票済みを見ない", 'state = f"起票済み: {\'・\'.join(done)}" if done else "まだ起票していない"',
     'state = "まだ起票していない"', "notes_raised"),
    ("添え書きの印を後ろの区切りまで見ない", '    return (head + "。") in question or (head + "）") in question', "    return head in question",
     "notes_raised"),
    # 会のディレクトリ
    ("会のディレクトリの名前を見ない", "    if len(parts) != 2 or parts[0] != REVIEWS or not DATE.fullmatch(parts[1]):",
     "    if len(parts) != 2:", "bad_dir"),
    # 会の記録の決まり
    ("記録の見出しを見ない", "    if header != NOTE_COLUMNS:", "    if False:", "bad_notes"),
    ("空行も行に数える", "        if not any(f.strip() for f in fields):\n            continue\n        line = len(rows) + 1",
     "        line = len(rows) + 1", "rows"),
    ("記録の種類を見ない", "        if kind not in NOTE_KINDS:", "        if False:", "bad_notes"),
    ("空のメモを通す", '        if not row["メモ"]:', "        if False:", "bad_notes"),
    ("番号を書いた指摘を通す", '        if kind == KIND_FINDING and row["No"]:', "        if False:", "bad_notes"),
    ("表に無い回答の番号を通す", '            if row["No"] not in shared:', "            if False:", "bad_notes"),
    ("空の発言者を通す", '            if not row["発言者"]:', "            if False:", "bad_notes"),
    ("改行のある対象を通す", '        if "\\n" in row["対象"] or "\\r" in row["対象"]:', "        if False:", "bad_notes"),
    # rows の行
    ("回答の鍵を通す", "    confirming = sorted(k for k in obj if k in CONFIRMING)", "    confirming = []", "bad_triage"),
    ("状態を確認中にしない", '"状態": PENDING,', '"状態": "反映済み",', "rows"),
    ("回答を未回答にしない", '"回答": qa.NO_ANSWER,', '"回答": recommend,', "rows"),
    ("起票元に会の日付を入れない", '"起票元": f"{SOURCE_NAME}（{SOURCE_DETAIL.format(date=date)}）"', '"起票元": SOURCE_NAME', "rows"),
    ("質問に対象を付けない", '(f"。対象: {target}）" if target else "）")', '"）"', "rows"),
    ("対象が空でも対象を付ける", '(f"。対象: {target}）" if target else "）")', 'f"。対象: {target}）"', "rows"),
    ("質問に添え書きを付けない", '        "質問": question + tail,', '        "質問": question,', "rows"),
    # 指摘を落とさない
    ("漏れた指摘を通す", "            elif not kinds:\n", "            elif False:\n", "bad_triage"),
    ("両方にある指摘を通す", '            elif "見送り" in kinds and len(kinds) > 1:', "            elif False:", "bad_triage"),
    ("指摘でない行を指せる", "    if not isinstance(value, int) or isinstance(value, bool) or value not in findings:",
     "    if not isinstance(value, int) or isinstance(value, bool):", "bad_triage"),
    ("真偽値を行と読む", "    if not isinstance(value, int) or isinstance(value, bool) or value not in findings:",
     "    if not isinstance(value, int) or value not in findings:", "bad_triage"),
    ("起票済みの指摘を見送りにできる", '                if "見送り" in kinds:\n', "                if False:\n", "raised_again"),
    ("起票済みの指摘に違う質問を足せる", "                    else:\n                        errors.append(f\"candidates[{i}]: 指摘 {line} はもう起票してある",
     "                    elif False:\n                        errors.append(f\"candidates[{i}]: 指摘 {line} はもう起票してある", "raised_again"),
    ("起票済みの同じ候補で止まる", "                    if squash(row[\"質問\"]) in asked:\n                        filed.append(row[\"質問\"])",
     "                    if False:\n                        filed.append(row[\"質問\"])", "rerun"),
    # 見送り
    ("見送りの種類を見ない", "    if kind not in SKIP_KINDS:", "    if False:", "bad_triage"),
    ("既にあるの番号を見ない", "    if kind == SKIP_EXISTING and detail:", "    if False:", "bad_triage"),
    ("見送りの理由を出さない", '    report.extend(f"  - 指摘 {line}: {kind}——{detail}" for line, kind, detail in skipped)\n', "", "rows"),
    # 重ねない
    ("同じ質問を重ねて足す", '                if squash(row["質問"]) in asked:\n                    errors.append(f"candidates[{i}]: 同じ質問が既にある',
     '                if False:\n                    errors.append(f"candidates[{i}]: 同じ質問が既にある', "bad_triage"),
    # 番号と書き方
    ("番号をほかの印も数える", "    start = ic.next_number(versions)", "    start = 13", "rows"),
    ("--dry-run でも書く", "    if dry_run:\n", "    if False:\n", "dry_run"),
    ("BOM を落として読む", '        existing = target.read_bytes().decode("utf-8")', '        existing = target.read_text(encoding="utf-8-sig")', "rows"),
    ("足す行が無くても書く", "    elif not new_rows:\n", "    elif False:\n", "no_new"),
    # groups
    ("遷移先で画面を引く", '[r for r in transitions if (r.get("遷移元") or "").strip() == sid]',
     '[r for r in transitions if (r.get("遷移先") or "").strip() == sid]', "groups"),
    ("項目を見ない", '[r for r in items if (r.get("画面ID") or "").strip() == sid]', "[]", "groups"),
    ("画面の行を見ない", "        cells = [screen] + ", "        cells = [] + ", "groups"),
    ("後の画面で上書きする", "                owner.setdefault(number, name)", "                owner[number] = name", "groups"),
    ("質問の無い画面も出す", "        if members:\n            result[name] = members", "        result[name] = members", "groups"),
    ("テーマを渡した順に並べない", "    for name in themes:\n", "    for name in sorted(themes):\n", "groups"),
    ("画面に掛かる質問をテーマに入れられる", "            elif number.strip() in owner:", "            elif False:", "bad_themes"),
    ("載らない番号をテーマに入れられる", "            if not isinstance(number, str) or number.strip() not in shown:",
     "            if not isinstance(number, str):", "bad_themes"),
    ("テーマから漏れた質問を通す", "    if missing:\n        errors.append(", "    if False:\n        errors.append(", "bad_themes"),
    ("2 つのテーマに入る質問を通す", "            elif number.strip() in placed:", "            elif False:", "bad_themes"),
    ("空のテーマを通す", "        if not isinstance(numbers, list) or not numbers:", "        if not isinstance(numbers, list):", "bad_themes"),
    ("画面のまとまりと同じ名前を通す", "        if name.strip() in names:", "        if False:", "bad_themes"),
    ("内部の層の表からまとめる", "    if qa.is_internal(qa_path):", "    if False:", "bad_themes"),
    ("入力の表に上書きする", "    if out.exists() and qa_path.exists() and out.samefile(qa_path):", "    if False:", "bad_themes"),
    ("番号の前の境界を見ない", 'SHARED_NUMBER = re.compile(rf"(?<![A-Za-z0-9-]){qa.NUMBER.pattern}(?![0-9])")',
     'SHARED_NUMBER = re.compile(rf"{qa.NUMBER.pattern}(?![0-9])")', "groups"),
    # 定数
    ("見送りの種類の写しがずれる", 'SKIP_KINDS = ("見た目", "既にある", "質問にしない")', 'SKIP_KINDS = ("見た目", "既にある", "質問にしない", "好み")',
     "constants"),
    ("画面のまとまりの名前の写しがずれる", 'SCREEN_GROUP = "画面 {id} {name}"', 'SCREEN_GROUP = "{id} {name}"', "constants"),
]


def docstring_rules() -> int:
    doc = (SCRIPTS / TARGET).read_text(encoding="utf-8").split('"""', 2)[1]
    part = doc.split("**守ること**:", 1)[1].split("終了コード:", 1)[0]
    return sum(1 for line in part.splitlines() if line.startswith("- "))


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="test-review-meeting-")).resolve()
    assert REAL_REPO not in work.parents
    try:
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        e = Env(work, scripts)

        print("正しい本体")
        for name, case in CASES.items():
            try:
                problem = case(e)
            except Exception as ex:  # noqa: BLE001
                problem = f"例外: {type(ex).__name__}: {ex}"
            check(f"試料: {name}", problem is None, problem or "")

        print("変異テスト")
        pristine = (scripts / TARGET).read_text(encoding="utf-8")
        for name, old, new, target in MUTATIONS:
            count = pristine.count(old)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            (scripts / TARGET).write_text(pristine.replace(old, new), encoding="utf-8")
            try:
                try:
                    problem = CASES[target](e)
                except Exception as ex:  # noqa: BLE001
                    problem = f"例外: {ex}"
            finally:
                (scripts / TARGET).write_text(pristine, encoding="utf-8")
            check(f"変異が素通りした: {name}（試料: {target}）", problem is not None)
        rules = docstring_rules()
        check("docstring の「守ること」の各行に変異がある（変異の数 ≥ 行の数）", len(MUTATIONS) >= rules, f"変異 {len(MUTATIONS)}・行 {rules}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
