#!/usr/bin/env python3
"""`rework-metrics.py`（spec-loop の、仮回答と推奨で決めた事項の変化と作り直しの量を数えるスクリプト。#886）の回帰テスト。

    python3 scripts/test-rework-metrics.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-rebuild-scope.py` と同じ形。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、本物の GitHub には届かない（本体は `gh` を呼ばない。
入力の JSON は `gh issue list --json number,title,state,body,comments`・`gh pr list --json number,title,state,body,additions,deletions` と同じ鍵の試料で、
本物の出力の形は見ない）。**Q&A 表の履歴は一時ディレクトリに本物の git リポジトリで作る**（`HOME`・`GIT_CONFIG_GLOBAL` を差し替え、利用者の git 設定を読まない）。
**spec-loop の Issue の本文は、本物の `scaffold.py --provisional` で作る**（試料の Q&A 表・中間表現は `test-rebuild-scope.py` のものを読み込む——写さない）。
**プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる**（正本リポジトリで単体で動くこと）。

**守ること**（各行に変異が 1 つ以上ある——下の `MUTATIONS`）:

- Q&A 表を変えた first-parent のコミットだけを古い順に読み、`暫定反映` だった No を仮回答に数える（マージしたブランチの途中のコミットは読まない）
- `暫定反映` でなくなったときに、`回答` の先頭の選択肢のラベルが直前の `暫定反映` の行と違えば「変わった」、同じなら「同じ選択肢で確定」（回答の文言の書き換えは変化に数えない）
- ラベルが読めない回答は「見分けられない」と名指しして 1。行が無くなったら「消えた」、最後まで `暫定反映` なら「まだ」。いまの時点で `暫定反映` の数は、確かめた後に戻したものも数える
- 前の形の見出し（推奨の 2 列が無い）の表は読める表として読む
- 同じ No は版の大きいほうの行が効く（v2 で置いた行で確かめたら確かめたと読む）。2 度確かめた No は 1 度でも変われば「変わった」
- 読めない Q&A 表のあるコミットでは、その表を前の時点のまま読み、名指しして 1
- 確認の Issue を数え、推奨のまま・変えた・結果なし（形に反する結果の行は名指しして 1）に分ける。`comments` の鍵が無い入力は 2
- 変わった 1 件ごとに、引いた範囲（No なら Issue・ケース・機能全体の数、確認の Issue なら影響する Issue の数。台帳の行が無ければ名指しして 1）と、
  作り直しの元の印を行頭に持つ Issue（確認の Issue 自体は数えない）・PR と、マージした PR の差分の行数を出す（装飾つき・行頭でない印は数えない。後ろの形が違う・空白の崩れた・コロンが全角の印は名指しして 1）
- 合計は Issue・PR ごとに 1 回数え（元を 2 つ持つ本文を二重に数えない）、印の元が変わったと数えた件に無い Issue・PR は名指しして 1（ほかの元で合計に入れたものは名指ししない）
- No の行には、scaffold が作り直した本文と PR は印を持たない（#885 の限界）と添える
- `--summary` は数と日付だけを出す（題・No・番号・コミットの SHA を出さない）
- Q&A 表を変えたコミットが 1 本も無いリポジトリは名指しして 1（黙って 0 件と出さない）
- 入力の形が違えば 2（PR に `additions`・`deletions` が無い・git のリポジトリでない・`--ref` が解決できない）

**変異テストを含む。** 写した本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。変異ごとに、
**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、穴が無くても緑になるので）。

**docstring の突き合わせ**: 本体の docstring に「回答が変わった」の見分け方（選択肢のラベルで比べ、列全体では見ない）と、#885 の限界を守らないものとして持つこと（陽性対照つき）。
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "rework-metrics.py"

_spec = importlib.util.spec_from_file_location("test_rebuild_scope", Path(__file__).resolve().parent / "test-rebuild-scope.py")
fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixtures)
HEADER = fixtures.HEADER


def row(no: str, answer: str, state: str, target: str = "決定表 1 行目") -> str:
    source = {"R": "要求確定（決定表）", "S": "仕様レビュー（Red Team）"}.get(no.split("-")[1] if no.count("-") == 2 else "R", "要求確定")
    if no.startswith("D-"):
        source = "仕様レビュー（Red Team）"
    return f"{no},{source},質問 {no},A: 一 / B: 二 / C: 三,A,理由,{answer},{target},{state},\n"


PROV = "A（暫定で採用。業務部 2026-10-21 の指示）"

# コミットの並び（main の first-parent）。各段は (版のファイル → 中身) の上書き。None は削除
V1, V2, DEV = "docs/v1/shared/qa.csv", "docs/v2/shared/qa.csv", "docs/v1/spec/qa-dev.csv"
BASE_ROWS = {
    "Q-001": row("Q-001", PROV, "暫定反映"),
    "Q-R-001": row("Q-R-001", PROV, "暫定反映"),
    "Q-R-002": row("Q-R-002", PROV, "暫定反映"),
    "Q-R-003": row("Q-R-003", PROV, "暫定反映"),
    "Q-R-004": row("Q-R-004", PROV, "暫定反映"),
    "Q-R-005": row("Q-R-005", "未回答", "確認中", "—"),
    "Q-R-007": row("Q-R-007", PROV, "暫定反映"),
    "Q-R-008": row("Q-R-008", PROV, "暫定反映"),
    "Q-R-009": row("Q-R-009", PROV, "暫定反映"),
    "Q-R-011": row("Q-R-011", PROV, "暫定反映"),
    "Q-S-001": row("Q-S-001", "A（業務部が回答）", "反映済み"),
}


def table(rows: dict[str, str]) -> str:
    return HEADER + "".join(rows.values())


def build_history(repo: Path, env: dict[str, str]) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com",
                        "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args], check=True, capture_output=True, env=env)

    def write(files: dict[str, str | None]) -> None:
        for name, text in files.items():
            path = repo / name
            if text is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")

    def commit(message: str, day: int) -> None:
        git("add", "-A")
        e = dict(env, GIT_AUTHOR_DATE=f"2026-10-{day:02d}T00:00:00Z", GIT_COMMITTER_DATE=f"2026-10-{day:02d}T00:00:00Z")
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com",
                        "-c", "commit.gpgsign=false", "commit", "-q", "-m", message], check=True, capture_output=True, env=e)

    repo.mkdir(parents=True)
    git("init", "-q", "-b", "main")
    rows = dict(BASE_ROWS)
    # 内部の表は前の形（推奨の 2 列が無い見出し）——読める表として読む
    old = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\nD-S-001,仕様レビュー（Red Team）,q,A: 一 / B: 二,B（開発 山田 2026-10-22）,x,反映済み,\n"
    write({V1: table(rows), DEV: old})
    commit("c1: 起票と暫定の反映", 1)
    write({"README.md": "Q&A 表を触らないコミット\n"})
    commit("c2: Q&A 表を触らない", 2)
    git("tag", "early")
    rows.update({
        "Q-001": row("Q-001", "B（業務部が回答）", "確認中"),           # 違う選択肢——変わった
        "Q-R-001": row("Q-R-001", "A（業務部が確認）", "反映済み"),      # 同じ選択肢で確定（文言だけ変わる）
        "Q-R-002": row("Q-R-002", "B（業務部が回答）", "確認中"),        # 変わった
        "Q-R-003": row("Q-R-003", "業務部と相談して決めた", "反映済み"),  # ラベルが読めない
        "Q-R-008": row("Q-R-008", "B（業務部が回答）", "確認中"),        # 1 度目は変わった
        "Q-R-011": row("Q-R-011", "A（業務部が確認）", "反映済み"),      # 同じで確定し、あとで暫定に戻す
    })
    write({V1: table(rows)})
    commit("c3: 確かめた", 3)
    rows["Q-R-006"] = row("Q-R-006", PROV, "暫定反映")
    write({V1: table(rows), V2: HEADER + row("Q-R-004", "B（業務部が回答）", "反映済み") + row("Q-R-010", PROV, "暫定反映")})  # v2 で置いた行で確かめた——変わった
    commit("c4: v2 で確かめ、暫定を足す", 4)
    del rows["Q-R-006"]                                                  # 確かめずに消えた
    rows["Q-R-008"] = row("Q-R-008", "B（暫定で採用。業務部 2026-10-25 の指示）", "暫定反映")
    write({V1: table(rows)})
    commit("c5: 消えた・暫定に戻した", 5)
    rows["Q-R-008"] = row("Q-R-008", "B（業務部が確認）", "反映済み")     # 2 度目は同じ——1 度でも変われば変わった
    rows["Q-R-011"] = row("Q-R-011", "B（暫定で採用。業務部 2026-10-26 の指示）", "暫定反映")
    write({V1: table(rows)})
    commit("c6: 2 度目に確かめた・暫定に戻した", 6)
    # マージしたブランチの途中で Q-R-009 を確かめてから暫定に戻した——first-parent ではマージで何も変わらない
    git("checkout", "-q", "-b", "side")
    side = dict(rows, **{"Q-R-009": row("Q-R-009", "B（業務部が回答）", "反映済み")})
    write({V1: table(side)})
    commit("s1: ブランチで確かめた", 7)
    # 戻すときに別の行も変える——マージが両方の親と違う木になり、first-parent でなければ途中のコミットが履歴に出る
    side = dict(rows, **{"Q-R-005": row("Q-R-005", "未回答", "確認中", "—").replace("質問 Q-R-005", "質問 Q-R-005（言い直し）")})
    write({V1: table(side)})
    commit("s2: ブランチで戻した", 8)
    git("checkout", "-q", "main")
    rows["Q-S-001"] = row("Q-S-001", "A（業務部が回答）", "反映済み", "決定表 2 行目")
    write({V1: table(rows), "README.md": "main が進む\n"})
    commit("c7: main が進む", 9)
    e = dict(env, GIT_AUTHOR_DATE="2026-10-10T00:00:00Z", GIT_COMMITTER_DATE="2026-10-10T00:00:00Z")
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com",
                    "merge", "-q", "--no-ff", "-m", "c8: マージ", "side"], check=True, capture_output=True, env=e)
    # 読めない表（見出しの名前が違う）を持つコミットを別のブランチに
    git("checkout", "-q", "-b", "broken")
    write({V2: "No,起票元,質問,選択肢,推奨,推奨理由,回答,反映先,状態,費用\nQ-R-004,要求確定,q,A: 一 / B: 二,A,r,B,x,反映済み,\n"})
    commit("b1: 見出しの名前が違う", 11)
    git("checkout", "-q", "main")


def decision(title: str, lines: str, comments: list[str], state: str = "CLOSED", number: int = 0) -> dict:
    t, b = fixtures.decision(True, title, lines)
    return {"number": number, "title": t, "state": state, "body": b, "comments": [{"body": c} for c in comments]}


def issues_json(bodies: dict[str, str]) -> list[dict]:
    return [
        {"number": 11, "title": "F-001: 割引額を計算する", "state": "OPEN", "body": bodies["F-001"], "comments": []},
        {"number": 12, "title": "F-002: 注文を取り消せるか", "state": "CLOSED", "body": bodies["F-002"], "comments": []},
        decision("要確認: 返品の受付期間を 7 日にした", "決めた値: 7 日\n影響する Issue: #11, #12\n",
                 ["承認します\n確認の結果: 推奨のまま", "やはり変える\n確認の結果: 変えた: 14 日"], number=20),
        decision("要確認: 推奨のまま", "決めた値: B\n影響する Issue: なし\n", ["確認の結果: 推奨のまま"], number=21),
        decision("要確認: まだ確かめていない", "決めた値: C\n影響する Issue: #11\n", [], state="OPEN", number=22),
        decision("要確認: 形に反する結果", "決めた値: D\n影響する Issue: なし\n", ["確認の結果: 変えた: "], number=23),
        decision("要確認: 台帳の行が無いまま変えた", "", ["確認の結果: 変えた: E"], number=24),
        # 作り直しの元の印——行頭のものだけを数える。確認の Issue 自体（本文に印の文字列がある）は数えない
        {"number": 30, "title": "作り直し: Q-001", "state": "OPEN", "body": "作り直しの元: Q-001\n\n## 作り直す範囲\n", "comments": []},
        {"number": 31, "title": "実装: 14 日にする", "state": "CLOSED", "body": "作り直しの元: #20\r\n\r\n受入基準\r\n", "comments": []},
        {"number": 32, "title": "装飾と文の途中", "state": "OPEN",
         "body": "**作り直しの元: #20**\n説明 作り直しの元: #20\n - 作り直しの元: Q-001\n", "comments": []},
        {"number": 35, "title": "同じで確定した No の印", "state": "OPEN", "body": "作り直しの元: Q-R-001\n", "comments": []},
        {"number": 33, "title": "形に反する印", "state": "OPEN", "body": "作り直しの元: 割引の件\n", "comments": []},
        {"number": 36, "title": "空白の崩れた印", "state": "OPEN", "body": "作り直しの元:Q-001\n作り直しの元:  #20\n作り直しの元：Q-001\n", "comments": []},
        # 元を 2 つ持ち、片方（Q-001）だけ変わった Issue——合計に入れたので、もう片方の元（Q-R-001）では名指ししない（狭いパスの N-1）
        {"number": 37, "title": "変わった元と同じ元を持つ Issue", "state": "OPEN", "body": "作り直しの元: Q-001\n作り直しの元: Q-R-001\n", "comments": []},
        decision("要確認: 印の文字列を本文に持つ", "決めた値: F\n影響する Issue: なし\n作り直しの元: #20\n", ["確認の結果: 推奨のまま"], number=34),
    ]


PRS = [
    {"number": 50, "title": "14 日にする", "state": "MERGED", "body": "<!-- dev-loop: 子 #31 -->\n作り直しの元: #20\nFixes #31\n",
     "additions": 10, "deletions": 2},
    {"number": 51, "title": "14 日にする（2）", "state": "OPEN", "body": "作り直しの元: #20\n", "additions": 5, "deletions": 5},
    {"number": 52, "title": "Q-001 の範囲", "state": "MERGED", "body": "作り直しの元: Q-001\n", "additions": 3, "deletions": 1},
    {"number": 54, "title": "元を 2 つ持つ PR", "state": "MERGED", "body": "作り直しの元: Q-001\n作り直しの元: #20\n", "additions": 7, "deletions": 0},
    {"number": 56, "title": "変わった元と同じ元を持つ PR", "state": "MERGED", "body": "作り直しの元: Q-001\n作り直しの元: Q-R-001\n", "additions": 1, "deletions": 0},
    {"number": 55, "title": "推奨のままの確認の印", "state": "MERGED", "body": "作り直しの元: #21\n", "additions": 50, "deletions": 0},
    {"number": 53, "title": "印の無い PR", "state": "MERGED", "body": "Fixes #11\n", "additions": 100, "deletions": 0},
]


class Case:
    def __init__(self, name: str, code: int, has: tuple[str, ...] = (), lacks: tuple[str, ...] = (), *, issues: str = "issues",
                 prs: str = "prs", ref: str = "", repo: str = "repo", extra: tuple[str, ...] = (), quiet: tuple[str, ...] = ()):
        self.name, self.code, self.has, self.lacks = name, code, has, lacks
        self.quiet = quiet  # 標準エラー（名指し）に出ないもの
        self.issues, self.prs, self.ref, self.repo, self.extra = issues, prs, ref, repo, extra


CASES = [
    Case("全部", 1, (
        "Q&A 表を変えたコミット 7 本",
        "- 仮回答（どこかの時点で `暫定反映` だった Q&A）: 11 件",
        "- 確かめた: 7 件（回答が変わった 4 件・同じ選択肢で確定 2 件・見分けられない 1 件）",
        "- 確かめずに行が消えた: 1 件・まだ `暫定反映`: 3 件（いまの時点で `暫定反映` の Q&A は 4 件", "  - Q-R-010: まだ暫定反映", "  - Q-R-011: 同じ",
        "  - Q-001: 変わった", "  - Q-R-001: 同じ", "  - Q-R-002: 変わった", "  - Q-R-003: 見分けられない", "  - Q-R-004: 変わった",
        "  - Q-R-006: 消えた", "    - 暫定反映 'A（暫定で採用。業務部 2026-10-21 の指示）' → 行が無い（", "  - Q-R-007: まだ暫定反映", "  - Q-R-008: 変わった", "  - Q-R-009: まだ暫定反映",
        "数えきれない——Q-R-003: 回答の選択肢のラベルが読めず",
        "- 確認の Issue: 6 件（推奨のまま 2 件・変えた 2 件・結果なし 1 件・結果の行が形に反する 1 件）",
        "数えきれない——#23 要確認: 形に反する結果",
        "- Q&A Q-001（Q&A の回答が変わった）: 引いた範囲 Issue 2 件・ケース 1 件（機能全体 1 件）／作り直しの元の印: Issue 2 件・PR 3 件（マージ 3 件）・差分 12 行——scaffold が作り直した",
        "- Q&A Q-R-002（Q&A の回答が変わった）: 引いた範囲 Issue 0 件・ケース 0 件／作り直しの元の印: Issue 0 件・PR 0 件（マージ 0 件）・差分 0 行",
        "- 確認の Issue #20（確認の Issue で値を変えた）: 引いた範囲 Issue 2 件／作り直しの元の印: Issue 1 件・PR 3 件（マージ 2 件）・差分 19 行",
        "- 確認の Issue #24（確認の Issue で値を変えた）: 引いた範囲 引けない",
        "数えきれない——#24 要確認: 台帳の行が無いまま変えた [CLOSED]: 変えたが 台帳の行が無い（前の書き方）",
        "数えきれない——#33 形に反する印: 作り直しの元の印の後ろが Q&A の No でも #<番号> でもない",
        "  - Issue #30 作り直し: Q-001 [OPEN]", "  - Issue #31 実装: 14 日にする [CLOSED]",
        "  - PR #50 14 日にする [MERGED] +10 −2", "  - PR #51 14 日にする（2） [OPEN] +5 −5",
        "- 合計: 変わった 6 件・作り直しの元の印の Issue 3 件・PR 5 件・差分 24 行（マージした PR。",
        "数えきれない——#36 空白の崩れた印: 作り直しの元の印の後ろが Q&A の No でも #<番号> でもない（'作り直しの元:Q-001'）",
        "数えきれない——#36 空白の崩れた印: 作り直しの元の印の後ろが Q&A の No でも #<番号> でもない（'作り直しの元:  #20'）",
        "数えきれない——#36 空白の崩れた印: 作り直しの元の印の後ろが Q&A の No でも #<番号> でもない（'作り直しの元：Q-001'）",
        "数えきれない——#35 同じで確定した No の印: 作り直しの元 Q-R-001 は変わったと数えた件に無い",
        "数えきれない——PR #55 推奨のままの確認の印: 作り直しの元 #21 は変わったと数えた件に無い",
    ), ("Issue #32", "Issue #34", "PR #53", "Q-R-005", "Q-S-001", "D-S-001", "Q&A Q-R-001（"), quiet=("PR #56 変わった元と同じ元を持つ PR: 作り直しの元 Q-R-001", "#37 変わった元と同じ元を持つ Issue: 作り直しの元 Q-R-001",
                                         "#32 装飾と文の途中")),
    Case("まだ確かめていない時点（--ref）", 0, (
        "Q&A 表を変えたコミット 1 本", "- 仮回答（どこかの時点で `暫定反映` だった Q&A）: 9 件",
        "- 確かめた: 0 件", "まだ `暫定反映`: 9 件", "- 合計: 変わった 0 件"), ("数えきれない——Q-R",), issues="clean", prs="noprs", ref="early"),
    Case("読めない表", 1, ("2026-10-11 docs/v2/shared/qa.csv: 読めない Q&A 表", "docs/v2/shared/qa.csv: 読めない Q&A 表", "まだ `暫定反映`: 3 件", "  - Q-R-004: 変わった", "  - Q-R-010: まだ暫定反映"), ref="broken"),
    Case("--summary", 1, ("## 仮回答（Q&A 表の履歴: 2026-10-10 まで", "- 仮回答（どこかの時点で `暫定反映` だった Q&A）: 11 件", "- 確認の Issue: 6 件",
                          "- Q&A（Q&A の回答が変わった）: 引いた範囲 Issue 2 件", "- 合計: 変わった 6 件"),
         ("割引額", "要確認: ", "  - Q-001", "Q&A Q-001", "#20（", "PR #50"), extra=("--summary",)),
    Case("comments の無い確認の Issue", 2, ("comments の鍵が無い", "数えていない"), issues="nocomments"),
    Case("PR に行数が無い", 2, ("0 番目が PR の形でない",), prs="nolines"),
    Case("Q&A 表の無いリポジトリ", 1, ("Q&A 表を変えたコミット 0 本", "を変えたコミットが無い——--spec-repo が正本リポジトリか"),
         issues="clean", repo="nohistory"),
    Case("git のリポジトリでない", 2, ("git のリポジトリでない",), repo="plain"),
    Case("解決できない --ref", 2, ("--ref 'nothing' が解決できない",), ref="nothing"),
    Case("PR が配列でない", 2, ("PR の配列でない",), prs="object"),
]

# (名前, 壊す箇所, 置き換え, 落ちるはずの試料)
MUTATIONS = [
    ("first-parent で読まない", '"log", "--first-parent", "--reverse"', '"log", "--reverse"', "全部"),
    ("Q&A 表を触らないコミットも読む", '"--format=%H%x09%cs", self.tip, "--",\n                  "docs/v*/shared/qa.csv", "docs/v*/spec/qa-dev.csv")',
     '"--format=%H%x09%cs", self.tip)', "全部"),
    ("新しい順に読む", '"--first-parent", "--reverse",', '"--first-parent",', "全部"),
    ("回答の列全体で比べる", 'kind = "見分けられない" if a is None or b is None else ("変わった" if a != b else "同じ")',
     'kind = "変わった" if old["回答"] != new["回答"] else "同じ"', "全部"),
    ("ラベルが読めなくても名指ししない", '            bad.append(f"{no}: 回答の選択肢のラベルが読めず', '            (f"{no}: 回答の選択肢のラベルが読めず', "全部"),
    ("消えた行を数えない", '                if new is None:\n', '                if new is None:\n                    continue\n', "全部"),
    ("仮回答を数えない", "                if qa.is_provisional(row):\n                    self.provisional.add(no)",
     "                if False:\n                    self.provisional.add(no)", "全部"),
    ("版の大きいほうを効かせない", "if no not in view or view[no][0] < version:", "if no not in view:", "全部"),
    ("2 度目の変化を数えない（最後の出来事で決める）", '        for kind in ("変わった", "見分けられない", "同じ"):\n            if kind in kinds:',
     '        for kind in ("変わった", "見分けられない", "同じ"):\n            if kinds and kind == self.events[no][-1][0]:', "全部"),
    ("最後まで暫定反映を数えない", '"まだ暫定反映" if no in self.still else "消えた"', '"消えた"', "全部"),
    ("読めない表を空と読む", "                    parsed = tables.get(path, {})", "                    parsed = {}", "読めない表"),
    ("読めない表を名指ししない", "    bad: list[str] = list(history.unreadable)", "    bad: list[str] = []", "読めない表"),
    ("見出しを見ない", "    if not rows or rows[0] not in (qa.COLUMNS, OLD_COLUMNS):", "    if not rows:", "読めない表"),
    ("結果なしを数えない", "none = [d for d in decisions if d.result is None and d.result_malformed is None]", "none = []", "全部"),
    ("推奨のままを数えない", "kept = [d for d in decisions if d.result == rebuild.KEPT]", "kept = []", "全部"),
    ("形に反する結果を名指ししない", '        bad.append(f"{rebuild.label(d.issue)}: {rebuild.RESULT}{d.outcome()}")', "        pass", "全部"),
    ("comments の鍵が無くても数える", "        if lacking:\n", "        if False:\n", "comments の無い確認の Issue"),
    ("No の範囲にケースを数えない", 'cases = sum(len(h.cases.get(no, [])) for h in hits)', "cases = 0", "全部"),
    ("No の範囲に機能全体を数えない", "whole = sum(1 for h in hits if not h.cases.get(no))", "whole = 0", "全部"),
    ("確認の Issue の範囲を数えない", 'scope = f"Issue {len(d.affects)} 件"', 'scope = "Issue 0 件"', "全部"),
    ("台帳の行が無い変えた確認の Issue を名指ししない", '            bad.append(f"{rebuild.label(d.issue)}: 変えたが', '            (f"{rebuild.label(d.issue)}: 変えたが', "全部"),
    ("確認の Issue 自体も作り直しの Issue に数える", "        if rebuild.is_decision(issue):\n            continue", "        if False:\n            continue", "全部"),
    ("行頭でない印も読む", "        if not line.startswith(ORIGIN_HEADS):", "        if not any(h in line for h in ORIGIN_HEADS):", "全部"),
    ("マージしていない PR の行数も足す", 'lines = sum(p["additions"] + p["deletions"] for p in rework if p["state"].upper() == PR_STATES_MERGED)',
     'lines = sum(p["additions"] + p["deletions"] for p in rework)', "全部"),
    ("形に反する印を名指ししない", "            bad.append(line.strip())", "            pass", "全部"),
    ("PR の印を読まない", "        keys, wrong = origins(pr[\"body\"])", "        keys, wrong = [], []", "全部"),
    ("限界を添えない", 'note = ("——scaffold が作り直した', 'note = ("" if True else "——scaffold が作り直した', "全部"),
    ("--summary でも題を出す", "    if not args.summary:\n        for d in decisions:", "    if True:\n        for d in decisions:", "--summary"),
    ("--summary でも No を出す", 'head = f"{name} {key}" if not args.summary else name', 'head = f"{name} {key}"', "--summary"),
    ("PR の形を見ない", "and type(pr.get(\"additions\")) is int and type(pr.get(\"deletions\")) is int):", "):", "PR に行数が無い"),
    ("git でないディレクトリでも続ける", '            raise Bad(f"{repo}: git のリポジトリでない', '            return\n            raise Bad(f"{repo}: git のリポジトリでない', "git のリポジトリでない"),
    ("Q&A 表の無いリポジトリを黙る", "    if not history.commits:", "    if False:", "Q&A 表の無いリポジトリ"),
    ("前の形の見出しを読めないと読む", "rows[0] not in (qa.COLUMNS, OLD_COLUMNS)", "rows[0] != qa.COLUMNS", "まだ確かめていない時点（--ref）"),
    ("いまの暫定反映を数えない", "{len(history.still)} 件——", "{count['まだ暫定反映']} 件——", "全部"),
    ("--summary でも SHA を出す", "{'' if args.summary else history.tip[:7] + ' '}", "{history.tip[:7] + ' '}", "--summary"),
    ("元を 2 つ持つ PR を二重に数える", 'counted_prs.update((p["number"], p) for p in rework)',
     'counted_prs.update((p["number"] * 1000 + len(counted_prs), p) for p in rework)', "全部"),
    ("印の元が数えた件に無い Issue を黙る", "    for key in sorted(set(marked) - keys):", "    for key in []:", "全部"),
    ("印の元が数えた件に無い PR を黙る", "    for key in sorted(set(marked_prs) - keys):", "    for key in []:", "全部"),
    ("ほかの元で合計に入れた PR も名指しする", "for p in marked_prs[key] if p[\"number\"] not in counted_prs]", "for p in marked_prs[key]]", "全部"),
    ("崩れた印を黙って落とす", "        if not line.startswith(ORIGIN_HEADS):", "        if not ORIGIN_LINE.match(line):", "全部"),
    ("ほかの元で合計に入れた Issue も名指しする", "for i in marked[key] if i[\"number\"] not in counted_issues]", "for i in marked[key]]", "全部"),
    ("全角のコロンの印を黙って落とす", 'ORIGIN_HEADS = (ORIGIN_HEAD, ORIGIN_HEAD[:-1] + "：")', "ORIGIN_HEADS = (ORIGIN_HEAD,)", "全部"),
    ("数えきれなくても 0", "    return 1 if bad else 0", "    return 0", "全部"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def run_case(scripts: Path, work: Path, env: dict[str, str], case: Case) -> str | None:
    args = [sys.executable, "-I", str(scripts / TARGET), "--issues", str(work / f"{case.issues}.json"),
            "--prs", str(work / f"{case.prs}.json"), "--spec-repo", str(work / case.repo), *case.extra]
    if case.ref:
        args += ["--ref", case.ref]
    proc = subprocess.run(args, capture_output=True, text=True, env=env)
    out = proc.stdout + proc.stderr
    if proc.returncode != case.code:
        return f"exit={proc.returncode}（期待 {case.code}）{out[-800:]}"
    for needle in case.has:
        if needle not in out:
            return f"出力に {needle!r} が無い: {out[-1500:]}"
    for needle in case.quiet:
        if needle in proc.stderr:
            return f"標準エラーに {needle!r} がある: {proc.stderr[-800:]}"
    for needle in case.lacks:  # 出さないものは標準出力（貼る側）で見る——名指しは標準エラーに出てよい
        if needle in proc.stdout:
            return f"出力に {needle!r} がある: {out[-800:]}"
    return None


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="test-rework-metrics-")).resolve()
    assert REAL_REPO not in work.parents
    try:
        home = work / "home"
        home.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")
        scripts = work / "scripts"
        shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
        bodies = fixtures.make_bodies(work / "scaffold", scripts)
        build_history(work / "repo", env)
        (work / "plain").mkdir()
        nohistory = work / "nohistory"
        nohistory.mkdir()
        (nohistory / "README.md").write_text("開発のリポジトリ\n", encoding="utf-8")
        for args in (("init", "-q", "-b", "main"), ("add", "-A"), ("commit", "-q", "-m", "init")):
            subprocess.run(["git", "-C", str(nohistory), "-c", "user.name=test", "-c", "user.email=test@example.com",
                            "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, env=env)
        issues = issues_json(bodies)
        (work / "issues.json").write_text(json.dumps(issues, ensure_ascii=False), encoding="utf-8")
        (work / "clean.json").write_text(json.dumps([i for i in issues if i["number"] in (11, 12, 21)], ensure_ascii=False), encoding="utf-8")
        nocomments = [dict(i) for i in issues]
        del nocomments[2]["comments"]
        (work / "nocomments.json").write_text(json.dumps(nocomments, ensure_ascii=False), encoding="utf-8")
        (work / "prs.json").write_text(json.dumps(PRS, ensure_ascii=False), encoding="utf-8")
        (work / "nolines.json").write_text(json.dumps([{k: v for k, v in PRS[0].items() if k != "additions"}], ensure_ascii=False),
                                           encoding="utf-8")
        (work / "object.json").write_text("{}", encoding="utf-8")
        (work / "noprs.json").write_text("[]", encoding="utf-8")

        print("正しい本体")
        for case in CASES:
            problem = run_case(scripts, work, env, case)
            check(f"試料: {case.name}", problem is None, problem or "")

        print("docstring の突き合わせ")
        source = (scripts / TARGET).read_text(encoding="utf-8")
        doc = ast.get_docstring(ast.parse(source)) or ""

        def explains(text: str) -> bool:
            return ("**`回答` の先頭の選択肢のラベル**" in text and "**`回答` の列全体の変化では見ない**" in text
                    and "#885 の既知の限界" in text.split("## 守らないもの", 1)[-1])

        check("docstring に見分け方と #885 の限界がある", explains(doc))
        check("docstring に実案件で貼るまでの手順がある", "## 使い方（実案件で数えて #980 に貼るまで）" in doc and "gh issue comment 980" in doc
              and "gh pr list --repo" in doc and "--json number,title,state,body,additions,deletions" in doc)
        for old in ("**`回答` の列全体の変化では見ない**", "#885 の既知の限界"):
            check(f"陽性対照: docstring の {old!r} を消すと突き合わせが落ちる", not explains(doc.replace(old, "")))

        print("変異テスト")
        by_name = {case.name: case for case in CASES}
        pristine = source
        for name, old, new, target in MUTATIONS:
            count = pristine.count(old)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            (scripts / TARGET).write_text(pristine.replace(old, new), encoding="utf-8")
            try:
                problem = run_case(scripts, work, env, by_name[target])
            finally:
                (scripts / TARGET).write_text(pristine, encoding="utf-8")
            check(f"変異が素通りした: {name}（試料: {target}）", problem is not None)
        rules = docstring_rules()
        check("docstring の「守ること」の各行に変異がある（変異の数 ≥ 行の数）", len(MUTATIONS) >= rules,
              f"変異 {len(MUTATIONS)}・行 {rules}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


def docstring_rules() -> int:
    doc = ast.get_docstring(ast.parse(Path(__file__).read_text(encoding="utf-8"))) or ""
    block = doc.split("**守ること**", 1)[1].split("\n\n", 1)[1].split("\n\n", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("- "))


if __name__ == "__main__":
    sys.exit(main())
