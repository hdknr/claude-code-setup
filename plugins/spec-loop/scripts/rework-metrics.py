#!/usr/bin/env python3
"""仮回答と推奨で決めた事項のうち、どれだけ変わり、変わったものでどれだけ作り直したかを数える（#886）。

usage: python3 rework-metrics.py --issues <Issue の一覧の JSON> --prs <PR の一覧の JSON> [--spec-repo <正本リポジトリ>] [--ref <参照>] [--summary] [--record [--case <案件の名前>]]

出すのは 3 つである:

1. **仮回答の数と、確かめたときに回答が変わった数**——正本リポジトリの Q&A 表の git の履歴から（下の「回答が変わった」の見分け方）。
2. **確認の Issue の数と、推奨のまま・変えた・結果なしの内訳**——確認の Issue（dev-loop が推奨で決めた判断を利用者に確かめてもらう Issue）の
   閉じのコメントの結果の行から。確認の Issue の見分け方と結果の行の読み方は、同じ `scripts/` の `rebuild-scope.py` の `Decision` を読む（写さない。#884）。
3. **変わった 1 件ごとの作り直しの量**——引いた範囲（Q&A の No なら、それを根拠にした spec-loop の Issue と受入基準のケースの数。確認の Issue なら
   `影響する Issue: ` の数。引き方は `rebuild-scope.py` と同じ）と、**作り直しの元の印**（本文の行頭の `作り直しの元: <No>`・`作り直しの元: #<番号>`。
   形の正は `references/handoff-issue.md` の「作り直しの元の印」で、頭は `rebuild-scope.py` の `ORIGIN` を読む。#885）を持つ Issue・PR の数と、
   その PR のうちマージしたものの差分の行数（`additions + deletions`）。

**このスクリプトは `gh` を呼ばない**（`rebuild-scope.py` と同じ）。**`git` は呼ぶ**——正本リポジトリの Q&A 表の履歴を読むだけで、何も書かない。

## 使い方（実案件で数えて、spec-loop を回す PC の中に記録するまで）

1. **開発のリポジトリ**（spec-loop の Issue を登録した先）の Issue と PR を、決まった 2 行で取る:

   ```bash
   gh issue list --repo <開発のリポジトリ> --state all --limit 1000 --json number,title,state,body,comments > issues.json
   gh pr list --repo <開発のリポジトリ> --state all --limit 1000 --json number,title,state,body,additions,deletions > prs.json
   ```

   `--limit` は Issue・PR の数より大きくする（超えた分は見えない）。
2. **正本リポジトリ**（`docs/v<n>/shared/qa.csv` を持つリポジトリ）を数えたい時点にする（`git pull`。別の時点なら `--ref`。版の区切りならリリースのタグ `--ref release-v<n>`）。
3. 数えて、記録する（#989）:

   ```bash
   python3 <spec-loop の base ディレクトリ>/scripts/rework-metrics.py --issues issues.json --prs prs.json --spec-repo <正本リポジトリ> --ref release-v1 --record
   ```

   **終了コードを見る**——1 なら名指しされたもの（標準エラー）を直して取り直すか、数えきれなかった件数（記録の `uncounted`）を承知で残す。2 なら何も数えていない（`--record` なら記録もしていない）。
   3 なら同じ案件・同じコミットの記録がすでにあるので書いていない（下の「記録」）。
4. **分析する**——`python3 <spec-loop の base ディレクトリ>/scripts/rework-report.py`（案件 × 時点の表・時点どうしの差・合計と率。使い方はその docstring を正とする）。
   `issues.json`・`prs.json` は案件の情報を含むので、使い終わったら捨てる（記録に残るのは数だけ）。
   規範を変える判断の根拠にするときは、`rework-report.py` の出力から数を人が読んで、起票の本文に書く——**記録のファイルを公開の場へ自動では出さない**（このリポジトリは公開）。

## 記録（`--record`。#989）

- **置き場所**: 環境変数 `SPEC_LOOP_REWORK_LOG` があればそのパス、無ければ `~/.claude/spec-loop/rework-metrics.jsonl`（spec-loop を回す PC の中。リポジトリには置かない）。
  無ければ親のディレクトリごと作る。
- **1 行 1 記録の JSON**（鍵の一覧は `RECORD_KEYS`）: 案件（`--case`。既定は正本リポジトリの最上位のディレクトリの名前——worktree や別名で clone したなら `--case` で揃える）・
  `--ref` の文字列・解決したコミットの SHA とその日付・記録した日と、標準出力に出した数（`uncounted` は数えきれないものの件数）。
- **同じ案件・同じコミットの行がすでにあれば書かない**（3）——`--ref` の綴りが違っても同じコミットなら同じと読む。
  取り直した数を残したいなら、その行を手で消してから記録する。**記録のファイルに読めない行があれば書かない**（2）——二重かを決められないので。
- 既存の行は消さない（追記だけ）。`--summary` と併せてよい（記録する数は同じ）。

## 回答が変わった（Q&A 表の履歴の読み方）

- **読む履歴**: 正本リポジトリの `--ref`（既定 `HEAD`）の **first-parent の履歴**のうち、Q&A 表（`docs/v<n>/shared/qa.csv`・`docs/v<n>/spec/qa-dev.csv`）を
  変えたコミットを古い順に読む。各コミットの時点で、**同じ No は版の大きいほうの行が効く**（`references/versions.md` の「重ねるもの」——同じ No の行を置くのが変更）。
- **仮回答**: どこかのコミットの時点で `状態` が `暫定反映` だった No（判定は `check-qa-csv.py` の `is_provisional`——`回答` の文言は見ない）。
- **確かめた**: 前のコミットの時点で `暫定反映` だった No が、次のコミットの時点で `暫定反映` でなくなった（`反映済み` か `確認中`）。
  行そのものが無くなったら「消えた」と数える（確かめたとは言わない）。
- **回答が変わった**: 確かめたコミットで、**`回答` の先頭の選択肢のラベル**（英大文字 1 字。`A（業務部が確認）` の `A`）が、**直前の `暫定反映` の行のラベルと違う**。
  **`回答` の列全体の変化では見ない**——同じ選択肢で確定するときも `A（暫定で採用。…）` を `A（業務部が確認）` に書き換える決まり（`references/qa-csv.md` の「暫定の回答」）なので、
  列全体で比べると確定を変化と数える。**`状態` が `確認中` に戻ったかでも見ない**——決まりでは違う選択肢なら `確認中` に戻すが、ラベルのほうが直接の印である。
  どちらかのラベルが読めない（`未回答`・ラベルで始まらない回答）なら「見分けられない」と名指しする。
- **No ごとの数え方**: 同じ No が `暫定反映` に戻って 2 度以上確かめられたら、どれか 1 度でも変わっていれば「変わった」に数える（出来事は全部並べる）。

## 終了コード

- 0: 数えた
- 1: 数えきれないものがある（数えたものは出し、数えきれないものを標準エラーに名指しする）——ラベルが読めず回答が変わったかを見分けられない No・
  読めない Q&A 表（見出しが決まりの形でない・CSV として読めない）のあるコミット（そのコミットではその表を前の時点のまま読む）・
  結果の行が決まりの形でない確認の Issue・変えた確認の Issue のうち台帳の行（`決めた値: `・`影響する Issue: `）が無い／形に反するもの・
  頭 `作り直しの元:`（全角のコロン `作り直しの元：` も）で始まり、後ろが空白 1 つと Q&A の No か `#<番号>` でない行（空白が無い・2 つ・全角・後ろが空・コロンが全角）・印の元が変わったと数えた件に無い Issue・PR（合計に入れていない）・Q&A 表を変えたコミットが 1 本も無い（`--spec-repo` が正本リポジトリでないかもしれない）
- 3: 数えたが記録しなかった（`--record` で、同じ案件・同じコミットの記録がすでにある）
- 2: 数えていない——引数の誤り・入力が読めない（JSON でない・Issue／PR の形が違う・確認の Issue を数えるのに `comments` の鍵が無い・PR に `additions`・`deletions` が無い）・
  `--spec-repo` が git のリポジトリでない・`--ref` が解決できない・`git` が失敗した・
  `--record` で記録のファイルが読めない／書けない／読めない行がある（数は出すが記録しない）

対象リポジトリで単体で動くよう、**標準ライブラリだけ**を使う（同じ `scripts/` の `rebuild-scope.py`・`check-qa-csv.py` を読み込む）。

## 守らないもの

| 守らないもの | なぜ |
| --- | --- |
| **Q&A の No の作り直しで、scaffold が作り直した spec-loop の Issue とその PR を数えること** | 作り直した本文とその周の PR は作り直しの元の印を持たない（#885 の既知の限界。`handoff-issue.md` の「作り直しの元の印」）。印で結べるのは、`rebuild-scope.py --draft` の下書きから立てた Issue（範囲の記録）と、印を写した周の PR だけ——No の行で PR が 0 件と出るのはふつうで、出力もそう添える。作り直した Issue の数の代わりに、引いた範囲（作り直すはずの Issue とケース）を出す |
| **確認の Issue の作り直しで、印を写し忘れた PR を数えること** | 印を本文の行頭に持つ PR だけを数える。dev-loop の周は写す決まり（`spec-gap.md` の「作り直しの周」）だが、写したかは見ない |
| **差分の行数が作り直しの分だけか** | PR の `additions + deletions` をそのまま足す（作り直し以外の変更が混ざっても分けない）。マージしていない PR は数に入れ、行数には入れない |
| **first-parent の外の履歴** | マージしたブランチの途中のコミットは読まない——マージのコミットで一度に変わったと読む。ブランチの途中で `暫定反映` に戻して確かめ直した出来事は 1 つに見える |
| **`removed.csv` で消した Q&A の行** | 重ね合わせの削除は読まない——前の版の行が効いたまま残る（消えたとは数えない） |
| **Q&A 表のファイルの綴り** | git の木のパスを決まりの綴り（`docs/v<n>/shared/qa.csv`・`docs/v<n>/spec/qa-dev.csv`）で探す。綴りだけ違うパスは読まない |
| **`暫定反映` のまま選択肢を替えた作り直し** | 確かめたのは `暫定反映` でなくなったときだけを見る——`A` を暫定で採っていたのを `B` を暫定で採るに替え、のちに `B` で確定したら「同じ選択肢で確定」と数える（暫定のあいだの作り直しは数えない） |
| **#404（spec-loop 0.25.0）より前の決まりの仮回答** | 仮回答は `状態` が `暫定反映` の行だけ。前の決まり（`反映済み` で `回答` に「暫定で採用」）の時期の仮回答とその確定・変更は数えない（`references/tree.md` の「暫定の行を状態へ移す」の前の形） |
| **回答のラベルが選択肢の列にあるか** | 先頭の英大文字 1 字（後ろが `（`・`(`・空白・行末のときだけ。`B: 変更` は読めない）を読むだけ。選択肢の列と突き合わせない（決まりどおりかは `check-qa-csv.py` が見る） |
| **入力が全部の Issue・PR を含むか** | `--limit` を超えた分・取った後に足した分は見えない（`rebuild-scope.py` と同じ） |
| **確認の Issue の結果の行を誰が書いたか** | `rebuild-scope.py` の `Decision` の守らないものと同じ（行を読むだけ） |
| **`--summary` が案件の情報を漏らさないこと** | 出すのは数と日付だけだが、貼る前に人が読む |
| **版ごとの数** | 数は `--ref` までの累計である——Q&A 表は v1・v2… を重ねて読み、Issue・PR は渡した JSON の全件を読む（版で絞らない）。版ごとの増分は、リリースのタグごとに `--ref` を替えて記録し、`rework-report.py` が時点どうしの差で出す。Issue・PR は取った時点で切れるので、`--ref` の時点と合わせて取らない限り Q&A の数とは揃わない |
| **同じコミットで取り直した数を残すこと** | 記録は案件とコミットで 1 行——Issue・PR を後で取り直して数えても、同じコミットなら書かない（3）。残すなら前の行を手で消す |
| **記録のファイルを壊さずに書くこと（同時に 2 つ走らせたとき）** | 読んでから追記するだけで、ロックは取らない——同じ時に 2 つ記録すると二重を見落としうる |
"""

from __future__ import annotations

import argparse
import csv
import datetime
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild = _load("rebuild_scope", "rebuild-scope.py")
qa = rebuild.qa

# 正本リポジトリの Q&A 表の置き場所（`references/versions.md` の「重ねるもの」）。版の番号で重ねる
TABLE = re.compile(r"docs/v([1-9][0-9]*)/(?:shared/qa\.csv|spec/qa-dev\.csv)")
# `回答` の先頭の選択肢のラベル（`A（業務部が回答）`・`B`）。`check-qa-csv.py` の `OPTION_LABEL` を読む
LABEL = re.compile(rf"({qa.OPTION_LABEL})(?:（|\(|\s|$)")
# 前の形（spec-loop 0.17.0 まで）の Q&A 表の見出し——推奨の 2 列が無い（`references/tree.md` の「Q&A 表を移す」）
OLD_COLUMNS = [c for c in qa.COLUMNS if c not in ("推奨", "推奨の理由")]
# 作り直しの元の印の行（行頭から・装飾なし・1 行に 1 つ）
ORIGIN_LINE = re.compile("^" + re.escape(rebuild.ORIGIN) + r"(\S.*?)\s*$")
# 頭（`作り直しの元:`）で始まる行は、形が崩れていても拾って名指しする——空白が無い・2 つ・全角・後ろが空の行を黙って落とさない（2 パス目の指摘）
ORIGIN_HEAD = rebuild.ORIGIN.rstrip()
# 全角のコロンで書いた頭（`作り直しの元：`）も、形に反する印として拾って名指しする（利用者の判断 2026-11-06。狭いパスの N-2）
ORIGIN_HEADS = (ORIGIN_HEAD, ORIGIN_HEAD[:-1] + "：")
PR_STATES_MERGED = "MERGED"

# 記録（#989）——この形は `rework-report.py` も読み込む（写さない）
RECORD_ENV = "SPEC_LOOP_REWORK_LOG"
RECORD_DEFAULT = Path(".claude") / "spec-loop" / "rework-metrics.jsonl"  # `HOME` の下
RECORD_TEXT = ("case", "ref", "commit", "date", "recorded")
RECORD_COUNTS = (
    "provisional", "confirmed", "changed", "same", "unknown", "vanished", "still", "provisional_now",
    "decisions", "kept", "decision_changed", "decision_none", "decision_malformed",
    "rework_items", "rework_issues", "rework_prs", "rework_lines", "uncounted",
)
RECORD_KEYS = RECORD_TEXT + RECORD_COUNTS


class Bad(Exception):
    """数えていない（2）。"""


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise Bad(f"git {' '.join(args)} が失敗した（{proc.stderr.strip() or proc.returncode}）")
    return proc.stdout


def label(answer: str) -> str | None:
    m = LABEL.match(answer.strip())
    return m.group(1) if m else None


def parse_table(text: str) -> dict[str, dict[str, str]] | None:
    """Q&A 表 1 つ。見出しが決まりの形でない・CSV として読めないなら None。"""
    try:
        rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    except csv.Error:
        return None
    # 前の形（spec-loop 0.17.0 まで）の見出しは推奨の 2 列が無いだけで、列の名前で読める（1 パス目の指摘——読めないと名指しすると古い履歴を持つ正本は毎回 1 になる）
    if not rows or rows[0] not in (qa.COLUMNS, OLD_COLUMNS):
        return None
    header = rows[0]
    out = {}
    for cells in rows[1:]:
        if not any(c.strip() for c in cells):
            continue
        if len(cells) != len(header):
            return None
        row = dict(zip(header, cells))
        out[row["No"].strip()] = row
    return out


class History:
    """正本リポジトリの Q&A 表の履歴を読み、仮回答の No ごとの出来事を集める。"""

    def __init__(self, repo: Path, ref: str) -> None:
        if not repo.is_dir():
            raise Bad(f"{repo}: ディレクトリでない")
        try:
            top = git(repo, "rev-parse", "--show-toplevel").strip()
        except Bad:
            raise Bad(f"{repo}: git のリポジトリでない（--spec-repo に正本リポジトリを渡す）")
        self.repo = Path(top)
        try:
            self.tip = git(self.repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip()
        except Bad:
            raise Bad(f"--ref {ref!r} が解決できない")
        self.tip_date = git(self.repo, "log", "-1", "--format=%cs", self.tip).strip()
        log = git(self.repo, "log", "--first-parent", "--reverse", "--format=%H%x09%cs", self.tip, "--",
                  "docs/v*/shared/qa.csv", "docs/v*/spec/qa-dev.csv")
        self.commits = [tuple(line.split("\t", 1)) for line in log.splitlines() if line.strip()]
        self.provisional: set[str] = set()  # どこかの時点で暫定反映だった No
        self.events: dict[str, list[tuple[str, str]]] = {}  # No → [(種類, 1 行の説明)]
        self.unreadable: list[str] = []  # 読めない表（コミットとパス）
        tables: dict[str, dict[str, dict[str, str]]] = {}  # パス → 表（読めないコミットでは前の時点のまま）
        before: dict[str, dict[str, str]] = {}
        for sha, date in self.commits:
            paths = [p for p in git(self.repo, "ls-tree", "-r", "--name-only", sha, "--", "docs").splitlines() if TABLE.fullmatch(p)]
            current: dict[str, dict[str, dict[str, str]]] = {}
            for path in paths:
                parsed = parse_table(git(self.repo, "show", f"{sha}:{path}"))
                if parsed is None:
                    self.unreadable.append(f"{sha[:7]} {date} {path}: 読めない Q&A 表（見出しが決まりの形でない・CSV として読めない）——前の時点のまま読む")
                    parsed = tables.get(path, {})
                current[path] = parsed
            tables = current
            view = self.overlay(tables)
            for no, row in view.items():
                if qa.is_provisional(row):
                    self.provisional.add(no)
            for no, old in before.items():
                if not qa.is_provisional(old):
                    continue
                new = view.get(no)
                where = f"{sha[:7]} {date}"
                if new is None:
                    self.events.setdefault(no, []).append(("消えた", f"暫定反映 {old['回答']!r} → 行が無い（{where}）"))
                elif not qa.is_provisional(new):
                    a, b = label(old["回答"]), label(new["回答"])
                    kind = "見分けられない" if a is None or b is None else ("変わった" if a != b else "同じ")
                    self.events.setdefault(no, []).append(
                        (kind, f"暫定反映 {old['回答']!r} → {new['状態'].strip()} {new['回答']!r}（{where}）"))
            before = view
        self.still = {no for no, row in before.items() if qa.is_provisional(row)}

    @staticmethod
    def overlay(tables: dict[str, dict[str, dict[str, str]]]) -> dict[str, dict[str, str]]:
        """同じ No は版の大きいほうの行が効く。"""
        view: dict[str, tuple[int, dict[str, str]]] = {}
        for path, rows in tables.items():
            version = int(TABLE.fullmatch(path).group(1))
            for no, row in rows.items():
                if no not in view or view[no][0] < version:
                    view[no] = (version, row)
        return {no: row for no, (_, row) in view.items()}

    def outcome(self, no: str) -> str:
        """No ごとの区分。1 度でも変わっていれば変わった。"""
        kinds = {kind for kind, _ in self.events.get(no, [])}
        for kind in ("変わった", "見分けられない", "同じ"):
            if kind in kinds:
                return kind
        return "まだ暫定反映" if no in self.still else "消えた"


def read_list(path: Path, what: str) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Bad(f"{path}: 読めない（{exc.__class__.__name__}: {exc}）")
    if not isinstance(data, list):
        raise Bad(f"{path}: {what}の配列でない")
    return data


def read_prs(path: Path) -> list[dict]:
    data = read_list(path, "PR ")
    for index, pr in enumerate(data):
        if not (isinstance(pr, dict) and type(pr.get("number")) is int and isinstance(pr.get("title"), str)
                and isinstance(pr.get("body"), str) and isinstance(pr.get("state"), str)
                and type(pr.get("additions")) is int and type(pr.get("deletions")) is int):
            raise Bad(f"{path}: {index} 番目が PR の形でない（gh pr list --json number,title,state,body,additions,deletions の出力を渡す）")
    return data


def origins(body: str) -> tuple[list[str], list[str]]:
    """本文の作り直しの元の印の元（`Q-R-002`・`#881`）と、形に反する印の行。"""
    found, bad = [], []
    for line in body.splitlines():
        if not line.startswith(ORIGIN_HEADS):
            continue
        m = ORIGIN_LINE.match(line)
        key = m.group(1) if m else ""
        if m and (rebuild.is_number(key) or re.fullmatch(r"#[1-9][0-9]*", key)):
            found.append(key)
        else:
            bad.append(line.strip())
    return found, bad


def record_path() -> Path:
    """記録のファイル。環境変数 `SPEC_LOOP_REWORK_LOG` があればそれ、無ければ `~/.claude/spec-loop/rework-metrics.jsonl`。"""
    env = os.environ.get(RECORD_ENV)
    return Path(env) if env else Path.home() / RECORD_DEFAULT


def check_record(rec: object) -> str | None:
    """記録の 1 行の形の誤り。正しければ None。"""
    if not isinstance(rec, dict):
        return "記録の形でない（JSON のオブジェクトでない）"
    missing = [k for k in RECORD_KEYS if k not in rec]
    if missing:
        return f"鍵が足りない（{'・'.join(missing)}）"
    wrong = ([k for k in RECORD_TEXT if not isinstance(rec[k], str)]
             + [k for k in RECORD_COUNTS if type(rec[k]) is not int or rec[k] < 0])
    if wrong:
        return f"値の型が違う（{'・'.join(wrong)}）"
    return None


def read_records(path: Path) -> tuple[str, list[dict], list[str]]:
    """記録のファイルを読む。(本文, 読めた記録, 読めない行の名指し)。ファイルが無ければ空。読めなければ Bad。
    空白だけの行は読み飛ばす（末尾の改行など）。"""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "", [], []
    except (OSError, UnicodeDecodeError) as exc:
        raise Bad(f"{path}: 記録のファイルが読めない（{exc.__class__.__name__}: {exc}）")
    records: list[dict] = []
    bad: list[str] = []
    # 行は `\n` だけで分ける——`splitlines()` は JSON が素のまま書く U+2028・U+2029・U+0085 でも割る（2 パス目の CR2-4）
    for n, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except (ValueError, RecursionError):
            bad.append(f"{path}:{n}: JSON として読めない")
            continue
        problem = check_record(rec)
        if problem:
            bad.append(f"{path}:{n}: {problem}")
            continue
        records.append(rec)
    return text, records, bad


def write_record(record: dict) -> int:
    """記録を 1 行追記する。0: 書いた・2: 書けない／記録のファイルに読めない行がある・3: 同じ案件・同じコミットの行がある（書かない）。"""
    path = record_path()
    try:
        text, records, unreadable = read_records(path)
    except Bad as exc:
        print(f"{exc}。記録しなかった", file=sys.stderr)
        return 2
    if unreadable:  # 読めない行が同じ案件・同じコミットかは決められない——黙って二重に書かない
        for line in unreadable:
            print(f"記録のファイルの読めない行——{line}", file=sys.stderr)
        print(f"{path} に読めない行がある——直してから記録する。記録しなかった", file=sys.stderr)
        return 2
    for rec in records:
        if rec["case"] == record["case"] and rec["commit"] == record["commit"]:
            print(f"{path} に案件 {record['case']} のコミット {record['commit'][:7]} の行がすでにある（{rec['ref']}・記録 {rec['recorded']}）"
                  "——取り直した数を残すなら、その行を消してから記録する。記録しなかった", file=sys.stderr)
            return 3
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(("\n" if text and not text.endswith("\n") else "") + json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"{path}: 書けない（{exc.__class__.__name__}: {exc}）。記録しなかった", file=sys.stderr)
        return 2
    print(f"記録した——{path}（案件 {record['case']}・{record['ref']}・{record['date']}）", file=sys.stderr)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--issues", required=True)
    parser.add_argument("--prs", required=True)
    parser.add_argument("--spec-repo", default=".")
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--case", default="")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        issues = rebuild.read_issues(Path(args.issues))
        prs = read_prs(Path(args.prs))
        decisions = [rebuild.Decision(i) for i in issues if rebuild.is_decision(i)]
        lacking = [rebuild.label(d.issue) for d in decisions if not d.comments_read]
        if lacking:
            raise Bad(f"{args.issues}: 確認の Issue に comments の鍵が無い（{'・'.join(lacking)}）——取り方の 1 行に comments を足す")
        history = History(Path(args.spec_repo), args.ref)
    except (Bad, rebuild.Bad) as exc:
        print(f"{exc}。数えていない", file=sys.stderr)
        return 2

    by_number = {i["number"]: i for i in issues}
    handoffs = [rebuild.Handoff(i, part) for i in issues if i["body"].startswith(rebuild.HANDOFF_PREFIX)
                and not rebuild.REMOVAL.search(i["body"]) for part in rebuild.parts(i["body"])]
    out: list[str] = []
    bad: list[str] = list(history.unreadable)
    if not history.commits:  # 正本リポジトリでないリポジトリを渡すと、黙って 0 件と出る
        bad.append(f"{history.repo} の {args.ref}: Q&A 表（docs/v<n>/shared/qa.csv・docs/v<n>/spec/qa-dev.csv）を変えたコミットが無い——--spec-repo が正本リポジトリかを確かめる")

    # 1. 仮回答と、確かめたときに回答が変わった数
    nos = sorted(history.provisional, key=lambda n: qa.number_order(n) if rebuild.is_number(n) else (True, 99, 0))
    kinds = {no: history.outcome(no) for no in nos}
    count = {k: sum(1 for v in kinds.values() if v == k) for k in ("変わった", "同じ", "見分けられない", "消えた", "まだ暫定反映")}
    confirmed = count["変わった"] + count["同じ"] + count["見分けられない"]
    out.append(f"## 仮回答（Q&A 表の履歴: {'' if args.summary else history.tip[:7] + ' '}{history.tip_date} まで・Q&A 表を変えたコミット {len(history.commits)} 本）")
    out.append(f"- 仮回答（どこかの時点で `暫定反映` だった Q&A）: {len(nos)} 件")
    out.append(f"- 確かめた: {confirmed} 件（回答が変わった {count['変わった']} 件・同じ選択肢で確定 {count['同じ']} 件・見分けられない {count['見分けられない']} 件）")
    out.append(f"- 確かめずに行が消えた: {count['消えた']} 件・まだ `暫定反映`: {count['まだ暫定反映']} 件"
               f"（いまの時点で `暫定反映` の Q&A は {len(history.still)} 件——確かめた後に暫定へ戻したものを含む）")
    if not args.summary:
        for no in nos:
            out.append(f"  - {no}: {kinds[no]}")
            for _, text in history.events.get(no, []):
                out.append(f"    - {text}")
    for no in nos:
        if kinds[no] == "見分けられない":
            bad.append(f"{no}: 回答の選択肢のラベルが読めず、変わったかを見分けられない")

    # 2. 確認の Issue の内訳
    decisions.sort(key=lambda d: d.issue["number"])
    kept = [d for d in decisions if d.result == rebuild.KEPT]
    changed = [d for d in decisions if d.changed()]
    malformed = [d for d in decisions if d.result_malformed is not None]
    none = [d for d in decisions if d.result is None and d.result_malformed is None]
    out.append("")
    out.append("## 確認の Issue（推奨で決めた事項）")
    out.append(f"- 確認の Issue: {len(decisions)} 件（推奨のまま {len(kept)} 件・変えた {len(changed)} 件・結果なし {len(none)} 件"
               + (f"・結果の行が形に反する {len(malformed)} 件" if malformed else "") + "）")
    if not args.summary:
        for d in decisions:
            out.append(f"  - {rebuild.label(d.issue)}: {d.outcome()}")
    for d in malformed:
        bad.append(f"{rebuild.label(d.issue)}: {rebuild.RESULT}{d.outcome()}")

    # 3. 変わった 1 件ごとの作り直しの量
    marked: dict[str, list[dict]] = {}
    marked_prs: dict[str, list[dict]] = {}
    for issue in issues:
        if rebuild.is_decision(issue):
            continue  # 確認の Issue 自体は作り直しの Issue でない
        keys, wrong = origins(issue["body"])
        for key in dict.fromkeys(keys):
            marked.setdefault(key, []).append(issue)
        bad += [f"#{issue['number']} {issue['title']}: 作り直しの元の印の後ろが Q&A の No でも #<番号> でもない（{line!r}）" for line in wrong]
    for pr in prs:
        keys, wrong = origins(pr["body"])
        for key in dict.fromkeys(keys):
            marked_prs.setdefault(key, []).append(pr)
        bad += [f"PR #{pr['number']} {pr['title']}: 作り直しの元の印の後ろが Q&A の No でも #<番号> でもない（{line!r}）" for line in wrong]

    items: list[tuple[str, str, str]] = []  # (元, 説明, 引いた範囲)
    for no in nos:
        if kinds[no] != "変わった":
            continue
        hits = [h for h in handoffs if no in h.refs]
        numbers = {h.issue["number"] for h in hits}
        cases = sum(len(h.cases.get(no, [])) for h in hits)
        whole = sum(1 for h in hits if not h.cases.get(no))
        items.append((no, "Q&A の回答が変わった", f"Issue {len(numbers)} 件・ケース {cases} 件" + (f"（機能全体 {whole} 件）" if whole else "")))
    for d in changed:
        key = f"#{d.issue['number']}"
        if d.malformed is not None or d.value is None or d.affects is None:
            bad.append(f"{rebuild.label(d.issue)}: 変えたが {rebuild.entry(d)}——引いた範囲を数えられない")
            scope = "引けない（台帳の行が無いか形に反する）"
        else:
            scope = f"Issue {len(d.affects)} 件"
        items.append((key, "確認の Issue で値を変えた", scope))

    out.append("")
    out.append("## 作り直しの量（変わった 1 件ごと）")
    counted_issues: dict[int, dict] = {}
    counted_prs: dict[int, dict] = {}
    for key, why, scope in items:
        rebuilt = marked.get(key, [])
        rework = marked_prs.get(key, [])
        lines = sum(p["additions"] + p["deletions"] for p in rework if p["state"].upper() == PR_STATES_MERGED)
        merged = sum(1 for p in rework if p["state"].upper() == PR_STATES_MERGED)
        # 合計は Issue・PR ごとに 1 回——1 つの本文が元を 2 行並べても（`handoff-issue.md`）二重に数えない（1 パス目の指摘）
        counted_issues.update((i["number"], i) for i in rebuilt)
        counted_prs.update((p["number"], p) for p in rework)
        name = "Q&A" if not key.startswith("#") else "確認の Issue"
        head = f"{name} {key}" if not args.summary else name
        note = ("——scaffold が作り直した spec-loop の Issue とその PR は印を持たない（#885 の限界）ので、Issue は下書きから立てた範囲の記録だけ"
                if not key.startswith("#") else "")
        out.append(f"- {head}（{why}）: 引いた範囲 {scope}／作り直しの元の印: Issue {len(rebuilt)} 件・PR {len(rework)} 件（マージ {merged} 件）・"
                   f"差分 {lines} 行{note}")
        if not args.summary:
            for issue in rebuilt:
                out.append(f"  - Issue {rebuild.label(issue)}")
            for pr in rework:
                out.append(f"  - PR #{pr['number']} {pr['title']} [{pr['state']}] +{pr['additions']} −{pr['deletions']}")
    total_lines = sum(p["additions"] + p["deletions"] for p in counted_prs.values() if p["state"].upper() == PR_STATES_MERGED)
    out.append(f"- 合計: 変わった {len(items)} 件・作り直しの元の印の Issue {len(counted_issues)} 件・PR {len(counted_prs)} 件・差分 {total_lines} 行（マージした PR。"
               "元を 2 つ持つ Issue・PR は 1 回だけ数える）")
    # 印の元が、変わったと数えた件に無い Issue・PR——黙って合計から落とさない（1 パス目の指摘）
    # 名指しするのは合計に 1 度も入らなかったものだけ——ほかの元で合計に入れた Issue・PR は名指ししない（2 パス目の指摘）
    keys = {key for key, _, _ in items}
    for key in sorted(set(marked) - keys):
        bad += [f"#{i['number']} {i['title']}: 作り直しの元 {key} は変わったと数えた件に無い——合計に入れていない"
                for i in marked[key] if i["number"] not in counted_issues]
    for key in sorted(set(marked_prs) - keys):
        bad += [f"PR #{p['number']} {p['title']}: 作り直しの元 {key} は変わったと数えた件に無い——合計に入れていない"
                for p in marked_prs[key] if p["number"] not in counted_prs]

    for line in out:
        print(line)
    for line in bad:
        print(f"数えきれない——{line}", file=sys.stderr)
    code = 1 if bad else 0
    if args.record:
        record = {
            "case": args.case or history.repo.name, "ref": args.ref, "commit": history.tip, "date": history.tip_date,
            "recorded": datetime.date.today().isoformat(),
            "provisional": len(nos), "confirmed": confirmed, "changed": count["変わった"], "same": count["同じ"],
            "unknown": count["見分けられない"], "vanished": count["消えた"], "still": count["まだ暫定反映"],
            "provisional_now": len(history.still),
            "decisions": len(decisions), "kept": len(kept), "decision_changed": len(changed), "decision_none": len(none),
            "decision_malformed": len(malformed),
            "rework_items": len(items), "rework_issues": len(counted_issues), "rework_prs": len(counted_prs),
            "rework_lines": total_lines, "uncounted": len(bad),
        }
        written = write_record(record)
        if written:
            return written
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「数えていない」（2）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。数えていない", file=sys.stderr)
        sys.exit(2)
