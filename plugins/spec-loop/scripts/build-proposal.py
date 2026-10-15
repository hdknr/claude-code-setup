#!/usr/bin/env python3
"""2 つのサインオフのタグの照合が通ったときだけ、決裁者向けの提案書（Markdown）を作る。

usage: python3 build-proposal.py [--repo <正本リポジトリ>] [--req <タグ>] [--budget <タグ>] [--out <出力先.md>] [--title <題>]

**ツリー・生成物の置き場所の正は `references/tree.md`、タグの決まりの正は `references/signoff-tags.md`
である**（どちらもこのプラグインの中にある）。

- **最初に `check-signoff.py` の `resolve` で照合する。0 でなければ 1 バイトも書かない。**
  照合をスキル（LLM）の判断に任せないため、生成の側で担保する。
- **承認されたタグの時点の中身から作る**——`docs/shared/qa.csv` は `req-signoff`、
  `docs/feasibility/schedule.csv`・`estimate.csv` は `budget-signoff` の時点のものを `git show` で読む。
  作業ツリーで承認後に直した中身は提案書に入らない。**手書き部分（`docs/proposal/*.md`）だけは作業ツリーから読む**
  （承認の対象ではない。ファイル名の順に先頭へ並べる）。
- 読んだ表は決まりの検査（`check-qa-csv.py`・`check-feasibility-csv.py`）を通す。通らなければ書かない。
- **始める前に、前に作った出力（提案書と同じ場所の `gantt.svg`）を消す**——作れなかったときに、
  古い提案書を今のものと取り違えないため。
- **提案書は承認の記録を持たない。** 載せるのは生成元のタグとコミットだけで、「承認済み」とは書かない。
- 同じ入力から同じバイトを作る（時刻を書かない）。標準ライブラリだけを使う（`git` は要る）。

終了コード:

- 0: 書いた
- 1: 照合が一致しない・表が決まりに反する・材料（表・手書き部分）が無い——書いていない
- 2: 照合していない・表が読めない（`check-signoff.py` の 2 と同じ）——書いていない

**守らないもの**: 手書き部分の中身（判断であって一意に決まらない）・見た目（Markdown を表示して目で見る）。
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


signoff = _load("check_signoff", "check-signoff.py")
qa = _load("check_qa_csv", "check-qa-csv.py")
feasibility = _load("check_feasibility_csv", "check-feasibility-csv.py")
gantt = _load("schedule_to_gantt", "schedule-to-gantt.py")

QA_PATH = "docs/shared/qa.csv"
SCHEDULE_PATH = "docs/feasibility/schedule.csv"
ESTIMATE_PATH = "docs/feasibility/estimate.csv"
HAND_DIR = "docs/proposal"
DEFAULT_OUT = "build/proposal/proposal.md"
GANTT_NAME = "gantt.svg"


class Stop(Exception):
    def __init__(self, code: int, lines: list[str]):
        super().__init__(lines)
        self.code, self.lines = code, lines


def show(top: Path, commit: str, tag: str, path: str) -> str:
    result = subprocess.run(["git", "-C", str(top), "show", f"{commit}:{path}"], capture_output=True)
    if result.returncode != 0:
        raise Stop(1, [f"{tag}:{path}: 承認の時点に無い。提案書の材料が無い"])
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        raise Stop(2, [f"{tag}:{path}: UTF-8 として読めない。中身を検査していない"])


def read_qa(text: str, label: str) -> list[dict[str, str]]:
    """Q&A 表を検査して行を返す（`check-qa-csv.py` はパスを取るので一時ファイルに書く）。"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "qa.csv"
        path.write_text(text, encoding="utf-8")
        code, lines = qa.check(path)
        lines = [line.replace(str(path), label) for line in lines]
        if code:
            raise Stop(code, lines)
        reader = csv.reader(io.StringIO(text.lstrip("\ufeff"), newline=""))
        next(reader)
        return [dict(zip(qa.COLUMNS, f)) for f in reader if any(c.strip() for c in f)]


def read_table(checker, text: str, label: str) -> list[dict[str, str]]:
    try:
        problems, rows = checker(Path(label), text)
    except feasibility.Unreadable as e:
        raise Stop(2, [str(e)])
    if problems:
        raise Stop(1, problems)
    return rows


def cell(value: str) -> str:
    return value.strip().replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def table(columns: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "|" + " --- |" * len(columns)]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    return lines


def compose(title: str, info: dict[str, str], hand: list[tuple[str, str]], qa_rows: list[dict[str, str]],
            schedule: list[dict[str, str]], estimate: list[dict[str, str]]) -> str:
    out = [f"# {title}", ""]
    out.append(f"> この提案書は生成物です。生成元: `{info['req']}`（`{info['req_commit']}`）・"
               f"`{info['budget']}`（`{info['budget_commit']}`）の時点の `docs/shared/`・`docs/feasibility/` と、"
               f"`{HAND_DIR}/` の手書き部分。**決裁者の承認の記録ではありません。**")
    out.append("")
    for _, body in hand:
        out += [body.rstrip("\n"), ""]

    done = [r for r in qa_rows if r["状態"].strip() == qa.DONE]
    pending = [r for r in qa_rows if r["状態"].strip() != qa.DONE]
    out += ["## 主な決定事項", ""]
    if done:
        out += table(["No", "質問", "回答", "反映先"], [[r["No"], r["質問"], r["回答"], r["反映先"]] for r in done])
    else:
        out.append("（反映済みの決定事項はありません）")
    out.append("")
    if pending:
        out += [f"### 承認の時点で未決定の質問（{len(pending)} 件）", ""]
        out += table(["No", "質問", "選択肢", "費用への影響"],
                     [[r["No"], r["質問"], r["選択肢"], r["費用への影響"]] for r in pending])
        out.append("")

    out += ["## 費用", ""]
    totals = [[c, f"{sum(int(r['金額']) for r in estimate if r['区分'] == c):,}"] for c in feasibility.CATEGORIES]
    out += table(["区分", "合計（円）"], totals)
    out += ["", "### 内訳", ""]
    out += table(["No", "区分", "項目", "金額（円）", "根拠"],
                 [[r["No"], r["区分"], r["項目"], f"{int(r['金額']):,}", r["根拠"]] for r in estimate])
    out.append("")

    first = min(r["開始"] for r in schedule)
    last = max(r["終了"] for r in schedule)
    out += ["## 期間", "", f"{first} 〜 {last}", "", f"![ガントチャート]({GANTT_NAME})", ""]
    out += table(["No", "工程", "開始", "終了", "前提"],
                 [[r["No"], r["工程"], r["開始"], r["終了"], r["前提"]] for r in schedule])
    out.append("")
    return "\n".join(out)


def build(args) -> tuple[str, str, int]:
    """(提案書, ガントチャート, 工程数) を返す。作れなければ Stop。"""
    code, lines, info = signoff.resolve(args.repo, args.req, args.budget)
    if code:
        raise Stop(code, lines)
    print("\n".join(lines))
    top = Path(info["top"])
    qa_rows = read_qa(show(top, info["req_commit"], info["req"], QA_PATH), f"{info['req']}:{QA_PATH}")
    schedule = read_table(feasibility.check_schedule, show(top, info["budget_commit"], info["budget"], SCHEDULE_PATH),
                          f"{info['budget']}:{SCHEDULE_PATH}")
    estimate = read_table(feasibility.check_estimate, show(top, info["budget_commit"], info["budget"], ESTIMATE_PATH),
                          f"{info['budget']}:{ESTIMATE_PATH}")
    if not schedule:
        raise Stop(1, [f"{info['budget']}:{SCHEDULE_PATH}: 工程が 1 行も無い。提案書の材料が無い"])
    if not estimate:
        raise Stop(1, [f"{info['budget']}:{ESTIMATE_PATH}: 費用が 1 行も無い。提案書の材料が無い"])
    hand_dir = top / HAND_DIR
    hand = []
    for path in sorted(hand_dir.glob("*.md")) if hand_dir.is_dir() else []:
        try:
            hand.append((path.name, path.read_text(encoding="utf-8-sig")))
        except (OSError, UnicodeDecodeError):
            raise Stop(2, [f"{path}: UTF-8 として読めない。中身を検査していない"])
    if not hand:
        raise Stop(1, [f"{hand_dir}: 手書き部分（*.md）が無い。背景と目的・推奨案・代替案・リスクを書いてから作る"])
    text = compose(args.title, info, hand, qa_rows, schedule, estimate)
    return text, gantt.render(schedule), len(schedule)


def repo_top(repo: Path) -> Path:
    """既定の出力先の根。git で求められなければ `.git` を上へたどる（下位から走らせても根の古い出力を消すため）。"""
    try:
        top = signoff.git(repo, "rev-parse", "--show-toplevel")
        if top.returncode == 0 and top.stdout.strip():
            return Path(top.stdout.strip())
    except signoff.Unjudged:
        pass
    for parent in (repo.resolve(), *repo.resolve().parents):
        if (parent / ".git").exists():
            return parent
    return repo


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument("--req")
    parser.add_argument("--budget")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title", default="提案書")
    args = parser.parse_args(argv)

    # git を起動できなくても、古い出力は消してから 2 で終わる（ここで落ちると古い提案書が残る）
    out = args.out if args.out else repo_top(args.repo) / DEFAULT_OUT
    svg = out.parent / GANTT_NAME
    for stale in (out, svg):
        if stale.is_file():
            stale.unlink()
            print(f"{stale}: 前に作った出力を消した", file=sys.stderr)

    try:
        try:
            text, chart, count = build(args)
        except signoff.Unjudged as e:
            raise Stop(2, [str(e)])
        except OSError as e:
            raise Stop(2, [f"git を起動できない（{e.strerror}）。提案書の材料を読んでいない"])
    except Stop as stop:
        for line in stop.lines:
            print(line, file=sys.stderr)
        print("提案書は作っていない", file=sys.stderr)
        return stop.code
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))
    svg.write_bytes(chart.encode("utf-8"))
    print(f"{out}: 提案書を書いた（ガントチャート {svg}・{count} 工程）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
