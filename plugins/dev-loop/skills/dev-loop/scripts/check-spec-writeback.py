#!/usr/bin/env python3
"""spec-loop の正本があるリポジトリで、仕様にある振る舞いを変える周が、申告と正本への戻しを残しているかを見る（#1001）。

    python3 <このスキルの base ディレクトリ>/scripts/check-spec-writeback.py <base> [--plan <計画ファイル>]

**周が PR を作る前に、worktree を cwd にして素の 1 行で呼ぶ**（`SKILL.md` 手順 6。終了コードで分岐する）。
`<base>` は周の base（計画ファイルの「周の在り処」の SHA）。**main を取り込んだ後は、`SKILL.md` 手順 4 の式を当て直した SHA を渡す**
——記録した古い SHA のままだと、main が足した Q&A 表の行や緑のケースの一覧の変化がこの周の変更に見える。
**規定（いつ申告するか・値の意味・変える周が残すもの・赤になったときにどうするか）の原本は `references/spec-writeback.md`**。

## なぜ要るか

spec-loop → dev-loop は仕様からコードへの向きのずれを何重にも見ているが、**コードから仕様への向き**——spec-loop から来ていない周
（障害の修正・小さな改修）が、仕様にある機能の利用者に見える振る舞いを変えた——を正本に戻す道が無かった。
**周に申告させ、変える周には正本への起票を残させ、申告漏れの一部（緑のケースの一覧から載った行を外した）を赤くする。**

## 読むもの

- **正本の有無**（どれも無ければ 0。申告も計画も求めない）:
    - **同じリポジトリ**: `docs/v<数字>/` の下に `shared/`・`requirements/`・`spec/` のどれかがある。**作業中の版は番号が最大のもの**（`spec-gap.md` の「差し戻す」と同じ）。
    - **別のリポジトリ**: `.claude/dev-loop.md` の行頭の `仕様の正本: <owner>/<repo>`（コードフェンスの中は数えない）か、
      リポジトリの根の `scaffold-source.txt`（spec-loop プラグインの `tree.md` の「Red テストを CI で走らせ続ける」。写した元の正本を名指す）。
      **同じリポジトリの正本があれば、そちらを採る。**
- **差分**: `git diff --name-only --no-renames <base>`（**2 点**——未コミットの変更も入る）と、未追跡のファイル。
- **計画ファイル**: `--plan`、無ければブランチ名 `issue/<n>-…` から `docs/plans/issue-<n>.md`・`.claude/plans/issue-<n>.md`。
  CI の detached HEAD では `GITHUB_HEAD_REF`・`GITHUB_REF_NAME` を先に見る。**Issue の番号**は、ブランチ名か計画ファイルの名前（`issue-<n>.md`）から取る。
- **申告**: 計画ファイルの行頭の `仕様の振る舞い: <値>`（箇条書きの `- ` は前に置いてよい。コードフェンスの中は数えない）。値は `VALUES` のどれか。
- **変える周が残すもの**:
    - 同じリポジトリ: 作業中の版の共有の Q&A 表 `docs/v<n>/shared/qa.csv` の、**base の時点に無かった No の行**で、
      起票元が `開発（#<n>）`・回答が `未回答`・状態が `確認中` のもの（base の時点に表が無ければ、全部の行が新しい）。
    - 別のリポジトリ: 計画ファイルの行頭の `正本に起票する行: <CSV の 1 行>`（Q&A 表の列の順。`No` は空でよい）で、
      列の数が `COLUMNS` と同じで、起票元・回答・状態が上と同じもの。
- **緑のケースの一覧**: 差分にある、名前が `scaffold-green.txt` のファイル（置き場所は問わない）。base の時点と今の、
  `#` で始まらない行の最初の語（ケースの名前）を比べる。

## 終了コード

- **0**: 正本が無い。または、申告が 1 本で値が決まったもので、`変える` なら残すものがあり、緑のケースの一覧から載った行が減っていない（値が `spec-loop の Issue` なら減っていてもよい）
- **1**: 正本があるのに——申告が無い・2 本以上・値が決まったものでない／`変える` なのに残すものが無い／`spec-loop の Issue` 以外の値で、緑のケースの一覧から載った行が減った
- **2**: 判定できない——git が失敗した・正本があるのに計画ファイルが見つからない・読めない・`変える` なのに Issue の番号が取れない（**緑ではない**）

## 何を守り、何を守らないか

守る:

- **正本があれば、申告が 1 本で決まった値でない限り 0 にしない**——行が無い・別の値・2 本以上・フェンスの中だけ、のどれも 1
- **正本があるのに計画が見つからなければ 0 にしない**（2）
- **正本が無ければ、申告の有無に依らず 0**——`docs/` があるだけ・`docs/v1-notes/` のような名前・版のディレクトリに `shared/`・`requirements/`・`spec/` が無い、は正本ではない
- **`変える` の周は、作業中の版の共有の表に、起票元が `開発（#<この Issue>）` で回答が `未回答`・状態が `確認中` の新しい行が無ければ 1**——
  内部の表（`qa-dev.csv`）にだけ足した・前の版の表に足した・別の Issue の起票元・既にあった行を書き換えただけ、のどれも 1
- **`変える` の周で正本が別のリポジトリなら、計画の `正本に起票する行:` が列の数と起票元・回答・状態で合わなければ 1**
- **緑のケースの一覧から載った行が減ったら、値が `spec-loop の Issue` でない限り 1**——一覧ごと消した・`--accept-changed` で外した、も減ったに数える
- **未コミットの変更・未追跡のファイル・base の時点に無かった表と一覧を落とさない**

守らない:

- **申告の真偽**——`変えない` と書けば、一覧の行を減らさない限り通る。仕様にある振る舞いを変えたかは、緑のケースの一覧が覆う範囲だけを
  spec-loop の `green-list.py check`（製品の CI）が見る。Red テストの無い振る舞い（仕様の原文にしかない振る舞い）の申告漏れは見えない
- **`spec-loop の Issue` の真偽**——Issue の本文（`spec-loop-handoff` の印）は読まない（`gh` を呼ばない）
- **足した行の中身**——質問が利用者の言葉か・選択肢が 2 つ以上か、は spec-loop の `check-qa-csv.py` が見る（このスクリプトは列の値 3 つだけを見る）
- **正本が別のリポジトリのとき、正本の表に実際に足されたか**——周は正本へ書きに行かない（`references/spec-writeback.md`）
- **作業中の版が凍結しているか**——番号が最大の版を作業中と読む（`spec-gap.md` の「差し戻す」と同じ）

標準ライブラリのみ。
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import re
import subprocess
import sys
from pathlib import Path

# 申告の値（原本は `references/spec-writeback.md` の「申告」。テストが突き合わせる）
CHANGE = "変える"
NO_CHANGE = "変えない"
FROM_SPEC_LOOP = "spec-loop の Issue"
VALUES = (CHANGE, NO_CHANGE, FROM_SPEC_LOOP)

# Q&A 表の列（spec-loop の `check-qa-csv.py` の `COLUMNS` の写し——dev-loop から spec-loop を相対パスで指せない。テストが突き合わせる）
COLUMNS = ["No", "起票元", "質問", "選択肢", "推奨", "推奨の理由", "回答", "反映先", "状態", "費用への影響"]
NO_ANSWER = "未回答"
OPEN_STATE = "確認中"

DECLARE = re.compile(r"^(?:[-*]\s+)?仕様の振る舞い:\s*(.*?)\s*$")
ROW_LINE = re.compile(r"^(?:[-*]\s+)?正本に起票する行:\s*(.*?)\s*$")
CANONICAL_DECL = re.compile(r"^(?:[-*]\s+)?仕様の正本:\s*(.*?)\s*$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
VERSION_DIR = re.compile(r"^v([0-9]+)$")
CANONICAL_PARTS = ("shared", "requirements", "spec")
GREEN_LIST = "scaffold-green.txt"
SCAFFOLD_SOURCE = "scaffold-source.txt"
PLAN_TEMPLATES = ("docs/plans/issue-{}.md", ".claude/plans/issue-{}.md")


def scan(text: str, pattern: re.Pattern) -> list[str]:
    """行頭の `pattern` の値を、出てきた順に返す。**コードフェンスの中は数えない。**"""
    values: list[str] = []
    fence = None
    for line in text.splitlines():
        m = FENCE.match(line)
        if m:
            mark = m.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence) and not line.strip()[len(mark):].strip():
                fence = None
            continue
        if fence is not None:
            continue
        d = pattern.match(line)
        if d:
            values.append(d.group(1))
    return values


def working_version(root: Path) -> int | None:
    """同じリポジトリの正本の作業中の版（番号が最大のもの）。無ければ None。"""
    docs = root / "docs"
    if not docs.is_dir():
        return None
    found = []
    for child in docs.iterdir():
        m = VERSION_DIR.match(child.name)
        if m and child.is_dir() and any((child / part).is_dir() for part in CANONICAL_PARTS):
            found.append(int(m.group(1)))
    return max(found) if found else None


def separate_canonical(root: Path) -> str | None:
    """別のリポジトリの正本の名前（宣言か `scaffold-source.txt`）。無ければ None。"""
    conf = root / ".claude" / "dev-loop.md"
    if conf.is_file():
        try:
            values = [v for v in scan(conf.read_text(encoding="utf-8"), CANONICAL_DECL) if v]
        except (OSError, UnicodeDecodeError):
            values = []
        if values:
            return values[0]
    src = root / SCAFFOLD_SOURCE
    if src.is_file():
        try:
            line = src.read_text(encoding="utf-8").strip().splitlines()
        except (OSError, UnicodeDecodeError):
            line = []
        name = line[0].split("@")[0].strip() if line else ""
        return name or SCAFFOLD_SOURCE
    return None


def qa_rows(text: str | None) -> list[dict[str, str]]:
    if not text:
        return []
    return list(csv.DictReader(io.StringIO(text)))


def writeback_ok(fields: dict[str, str], issue: str) -> bool:
    return (fields.get("起票元", "").strip() == f"開発（#{issue}）"
            and fields.get("回答", "").strip() == NO_ANSWER
            and fields.get("状態", "").strip() == OPEN_STATE)


def new_rows(base_text: str | None, now_text: str | None) -> list[dict[str, str]]:
    """base の時点に無かった No の行。"""
    old = {r.get("No", "").strip() for r in qa_rows(base_text)}
    return [r for r in qa_rows(now_text) if r.get("No", "").strip() and r.get("No", "").strip() not in old]


def plan_rows(plan_text: str) -> list[dict[str, str]]:
    rows = []
    for value in scan(plan_text, ROW_LINE):
        try:
            cells = next(csv.reader([value]))
        except (csv.Error, StopIteration):
            continue
        if len(cells) == len(COLUMNS):
            rows.append(dict(zip(COLUMNS, cells)))
    return rows


def green_names(text: str | None) -> set[str]:
    names = set()
    for line in (text or "").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            names.add(s.split()[0])
    return names


def judge(*, version: int | None, separate: str | None, plan_text: str | None, issue: str | None,
          qa_base: str | None, qa_now: str | None, green: list[tuple[str, str | None, str | None]]) -> tuple[int, str]:
    """(終了コード, 理由)。`green` は (一覧のパス, base の中身, 今の中身)。"""
    if version is None and separate is None:
        return 0, "spec-loop の正本が無い（docs/v<n>/ も `仕様の正本:` の宣言も scaffold-source.txt も無い）——該当なし"
    if plan_text is None:
        return 2, "正本があるのに計画ファイルが見つからない——申告を判定できない（緑ではない）"
    values = scan(plan_text, DECLARE)
    if not values:
        return 1, "計画に `仕様の振る舞い:` の行が無い"
    if len(values) > 1:
        return 1, f"計画に `仕様の振る舞い:` の行が {len(values)} 本ある（1 本だけ置く）"
    value = values[0]
    if value not in VALUES:
        return 1, f"計画の申告の値が決まったものでない（`{value}`。{' / '.join(VALUES)} のどれか）"
    if value != FROM_SPEC_LOOP:
        removed = sorted({f"{path}: {name}" for path, old, now in green for name in green_names(old) - green_names(now)})
        if removed:
            return 1, ("緑のケースの一覧から載った行が減った（" + "、".join(removed) + "）——Red テストが覆う仕様の振る舞いを外している。"
                       "一覧から外さず、references/spec-writeback.md の「Red テストが赤になったら」に従う")
    if value != CHANGE:
        return 0, f"申告は `{value}`"
    if issue is None:
        return 2, "申告が `変える` なのに Issue の番号が取れない（ブランチ名 issue/<n>-… か計画ファイルの名前 issue-<n>.md）——判定していない（緑ではない）"
    if version is not None:
        path = f"docs/v{version}/shared/qa.csv"
        if qa_now is None:
            return 1, f"申告が `変える` なのに作業中の版の共有の Q&A 表（{path}）が無い"
        if any(writeback_ok(r, issue) for r in new_rows(qa_base, qa_now)):
            return 0, f"申告は `変える`。{path} に起票元 `開発（#{issue}）` の新しい行がある"
        return 1, (f"申告が `変える` なのに、{path} に起票元 `開発（#{issue}）`・回答 `{NO_ANSWER}`・状態 `{OPEN_STATE}` の新しい行が無い")
    if any(writeback_ok(r, issue) for r in plan_rows(plan_text)):
        return 0, f"申告は `変える`。正本は別のリポジトリ（{separate}）で、計画に `正本に起票する行:` がある"
    return 1, (f"申告が `変える` で正本が別のリポジトリ（{separate}）なのに、計画に `正本に起票する行:` の行"
               f"（列 {len(COLUMNS)} 個・起票元 `開発（#{issue}）`・回答 `{NO_ANSWER}`・状態 `{OPEN_STATE}`）が無い")


def git(*args: str) -> tuple[int, str]:
    # core.quotePath=false: 非 ASCII のパスを "\343…" と引用符で包ませない
    proc = subprocess.run(["git", "-c", "core.quotePath=false", *args], capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def changed_paths(base: str) -> list[str] | None:
    rc1, diff = git("diff", "--name-only", "--no-renames", base)
    rc2, untracked = git("ls-files", "--others", "--exclude-standard")
    if rc1 != 0 or rc2 != 0:
        return None
    return [line for line in (diff + untracked).splitlines() if line.strip()]


def at_base(base: str, path: str) -> str | None:
    rc, out = git("show", f"{base}:{path}")
    return out if rc == 0 else None


def read_now(root: Path, path: str) -> str | None:
    f = root / path
    try:
        return f.read_text(encoding="utf-8") if f.is_file() else None
    except (OSError, UnicodeDecodeError):
        return None


def branch_name() -> str:
    for env in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        v = os.environ.get(env, "").strip()
        if v and v != "HEAD":
            return v
    rc, out = git("rev-parse", "--abbrev-ref", "HEAD")
    name = out.strip() if rc == 0 else ""
    return "" if name == "HEAD" else name


def issue_number(plan: Path | None) -> str | None:
    m = re.match(r"^issue/(\d+)", branch_name())
    if m:
        return m.group(1)
    if plan is not None:
        m = re.match(r"^issue-(\d+)\.md$", plan.name)
        if m:
            return m.group(1)
    return None


def find_plan(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = root / p
        return p if p.is_file() else None
    m = re.match(r"^issue/(\d+)", branch_name())
    if not m:
        return None
    for template in PLAN_TEMPLATES:
        p = root / template.format(m.group(1))
        if p.is_file():
            return p
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="仕様にある振る舞いを変える周が、申告と正本への戻しを残しているか（#1001）")
    ap.add_argument("base", help="周の base（SHA か参照）")
    ap.add_argument("--plan", help="計画ファイル（既定: ブランチ名 issue/<n>-… から引く）")
    opts = ap.parse_args(argv)

    rc, top = git("rev-parse", "--show-toplevel")
    paths = changed_paths(opts.base) if rc == 0 else None
    if paths is None:
        print(f"git で差分を取れなかった（base: {opts.base}）——判定していない（緑ではない）。")
        return 2
    root = Path(top.strip())
    version = working_version(root)
    separate = None if version is not None else separate_canonical(root)
    plan = find_plan(root, opts.plan)
    plan_text = None
    if plan is not None:
        try:
            plan_text = plan.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"計画ファイル {plan} を読めなかった: {e}——判定していない（緑ではない）。")
            return 2
    qa_base = qa_now = None
    if version is not None:
        qa_path = f"docs/v{version}/shared/qa.csv"
        qa_base, qa_now = at_base(opts.base, qa_path), read_now(root, qa_path)
    green = [(p, at_base(opts.base, p), read_now(root, p)) for p in paths if p.split("/")[-1] == GREEN_LIST]
    code, reason = judge(version=version, separate=separate, plan_text=plan_text, issue=issue_number(plan),
                         qa_base=qa_base, qa_now=qa_now, green=green)
    where = f"同じリポジトリ（docs/v{version}/）" if version is not None else (f"別のリポジトリ（{separate}）" if separate else "無い")
    print(f"正本: {where} / 計画: {plan if plan else '(見つからない)'} / 差分: {len(paths)} ファイル")
    print(reason)
    if code == 1:
        print("書き方と、振る舞いを変える周が正本に残すものは references/spec-writeback.md を正とする。")
    return code


if __name__ == "__main__":
    sys.exit(main())
