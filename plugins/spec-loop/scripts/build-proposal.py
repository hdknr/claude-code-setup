#!/usr/bin/env python3
"""2 つのサインオフのタグの照合が通ったときだけ、決裁者向けの提案書と仕様書（Markdown。`--pptx` で PPTX も）を作る。

usage: python3 build-proposal.py [--repo <正本リポジトリ>] [--version <n>] [--req <タグ>] [--budget <タグ>] [--out <出力先.md>] [--title <題>] [--spec-title <題>] [--pptx]

**ツリー・生成物の置き場所の正は `references/tree.md`、版の決まりの正は `references/versions.md`、
タグの決まりの正は `references/signoff-tags.md` である**（どれもこのプラグインの中にある）。

- **最初に `check-signoff.py` の `resolve` で照合する。0 でなければ 1 バイトも書かない。**
  照合をスキル（LLM）の判断に任せないため、生成の側で担保する。**版（`<n>`）も照合が決めたものを使う**
  （`--version` を省けば作業中の版）。
- **承認されたタグの時点の、その版の中身から作る**——`docs/v<n>/shared/qa.csv` は `signoff/v<n>/req-<k>`、
  `docs/v<n>/feasibility/schedule.csv`・`estimate.csv` は `signoff/v<n>/budget-<k>` の時点のものを `git show` で読む。
  作業ツリーで承認後に直した中身は提案書に入らない。**手書き部分（`docs/v<n>/proposal/*.md`）だけは作業ツリーから読む**
  （承認の対象ではない。ファイル名の順に先頭へ並べる）。
  **v2 以降は、その版の差分の表に加えて、前の版との比較の節が載る**（変更の提案書）——比較は同梱の `diff-versions.py` の
  `compare` を、**`signoff/v<n>/req-<k>` の時点の `docs/`** に当てる（`git ls-tree`・`git cat-file` で一時ディレクトリに写す。
  `git archive` は `.gitattributes` で中身が変わるので使わない。写すのは重ね合わせが読むものだけで、
  **大文字小文字・Unicode の正規化だけが違うパスがあれば写さずに 1**——区別しないファイルシステムでは同じ場所に書かれる）。決まりの正は `references/versions.md` の「版の差分」。
  **重ね合わせが作れなければ書かない（1）。** 費用の節は**その版の差分の見積り**で、前の版までの費用は足さない。
  **v2 以降で `shared/qa.csv` を置かない版**（Q&A を足さない版。`references/versions.md`）は、Q&A を 0 行として作る。
  v1 では `qa.csv` が無ければ作らない。
- 読んだ表は決まりの検査（`check-qa-csv.py`・`check-feasibility-csv.py`）を通す。通らなければ書かない。
- **暫定の行**（判別は `check-qa-csv.py` の `is_provisional`。決まりの正は `references/qa-csv.md` の「暫定の行の判別」）は
  主な決定事項に載せず、「利用者にまだ確かめていない決定」の節に載せる（0 件でも節を出す。#366）。
  **照合が 3 で止めるので、書いた提案書ではこの節は 0 件になる**（#404 で判別を状態だけにした）——節は、決裁者に
  「残っていない」ことを示すために出す。
- **仕様書（`spec.md`）も同じ実行で作る**（#371）——材料は `signoff/v<n>/req-<k>` の時点の v1〜v<n> を重ねた全体
  （前の版との比較と同じ写しから。**v1 でも重ね合わせの決まりを通す**）と、作業中の版の `proposal/spec/*.md`（手書き。任意）。
  `spec/`・`requirements/` の `.svg` の図は同じ場所に `spec-figure-NN.svg` として写して載せ、`.svg` の無い `.drawio` は載せていないと書く（draw.io は起動しない）。
  載せるものと置き場所の正は `references/tree.md` の「仕様書」。
- **`--pptx` で提案書と仕様書の PPTX も作る**（`qa-to-pptx.py` の仕組み。図は載せず、載せていないとスライドに書く）。
- **始める前に、前に作った出力（提案書・`gantt.svg`・`spec.md`・2 つの PPTX・`spec-figure-*.svg`）を消し、
  全部作れてから書く**——作れなかったときに、古い提案書を今のものと取り違えないため。
- **提案書は承認の記録を持たない。** 載せるのは生成元のタグとコミットだけで、「承認済み」とは書かない。
- 同じ入力から同じバイトを作る（時刻を書かない）。標準ライブラリだけを使う（`git` は要る）。

終了コード:

- 0: 書いた
- 1: 照合が一致しない・表が決まりに反する・材料（表・手書き部分）が無い——書いていない
- 2: 照合していない・表が読めない（`check-signoff.py` の 2 と同じ）・出力先の名前が仕様書・ガントチャート・PPTX・図と重なる——書いていない
- 3: 要求確定のタグの時点に暫定の回答（`暫定反映`）が残る（`check-signoff.py` の 3 と同じ）——書いていない

**守らないもの**: 手書き部分の中身（判断であって一意に決まらない）・見た目（Markdown を表示して目で見る）・
PPTX がアプリで開けること（見るのは部品の揃いと XML の整形式まで）・前の版の暫定の行（提案書に載るのはその版の `qa.csv` だけ）。
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

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
diffs = _load("diff_versions", "diff-versions.py")
pptx = _load("qa_to_pptx", "qa-to-pptx.py")

# 版のディレクトリ（`docs/v<n>/`）からのパス
QA_PATH = "shared/qa.csv"
SCHEDULE_PATH = "feasibility/schedule.csv"
ESTIMATE_PATH = "feasibility/estimate.csv"
HAND_DIR = "proposal"
DEFAULT_OUT = "build/proposal/proposal.md"
GANTT_NAME = "gantt.svg"
# 仕様書（#374）。出力は提案書と同じ場所。手書き部分は提案書の手書き部分の下のディレクトリ（提案書には入らない）
SPEC_NAME = "spec.md"
SPEC_PPTX_NAME = "spec.pptx"
SPEC_HAND_DIR = HAND_DIR + "/spec"
FIGURE_PREFIX = "spec-figure-"
FIGURE_DIRS = ("spec/", "requirements/")
# 重ねた全体（版のディレクトリからのパス）
DECISION_PATH = "shared/decision_table.csv"
SCOPE_PATH = "spec/scope.md"
OUT_OF_SCOPE = "範囲の外"
FIGURE_NOTE = "PPTX に載せていない（{} で見る）"


def in_version(version: int, path: str) -> str:
    return f"{signoff.DOCS}/v{version}/{path}"


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


def exists(top: Path, commit: str, path: str) -> bool:
    result = subprocess.run(["git", "-C", str(top), "ls-tree", "--name-only", commit, "--", path],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise Stop(2, [f"{commit[:7]}:{path}: 在るかを確かめられない: {result.stderr.strip()}"])
    return bool(result.stdout.strip())


def merged_reads(path: str) -> bool:
    """重ね合わせが読むものか——`docs/v…` の名前そのものと、版の中の置き場所・`removed.csv`（`.` で始まる名前は読まない）。"""
    parts = PurePosixPath(path).parts
    if len(parts) < 2 or parts[0] != signoff.DOCS or not diffs.merge_versions.VERSION_LIKE.match(parts[1]):
        return False
    if len(parts) == 2:
        return True
    inside = parts[2:]
    if any(p.startswith(".") for p in inside):
        return False
    return inside[0] in diffs.merge_versions.AREAS or inside == (diffs.merge_versions.REMOVED,)


def copy_docs(top: Path, commit: str, tag: str, dest: Path) -> None:
    """`commit` の時点の `docs/` のうち重ね合わせが読むものを `dest` の下に写す（作業ツリーは読まない）。

    **大文字小文字・Unicode の正規化だけが違うパスがあれば写さない（1）**——区別しないファイルシステム
    （macOS の既定）では同じ場所に書かれ、片方が黙って消えるか、先に置いたリンクを辿って一時ディレクトリの外に
    書く。どのファイルシステムでも同じ答えにするため、写す前に一覧で断る。書く先が既にあるときも断る。
    """
    listing = subprocess.run(["git", "-C", str(top), "ls-tree", "-r", "-z", "--full-tree", commit, "--", signoff.DOCS],
                             capture_output=True)
    if listing.returncode != 0:
        raise Stop(2, [f"{tag}: {signoff.DOCS}/ を一覧できない: {listing.stderr.decode('utf-8', 'replace').strip()}"])
    entries, versions = [], set()
    for record in listing.stdout.split(b"\0"):
        if not record:
            continue
        meta, _, raw = record.partition(b"\t")
        mode, kind, sha = meta.decode().split()
        path = raw.decode("utf-8", "surrogateescape")
        parts = PurePosixPath(path).parts
        if len(parts) > 2 and parts[0] == signoff.DOCS and diffs.merge_versions.VERSION_LIKE.match(parts[1]):
            versions.add(parts[1])  # 重ねるものを持たない版も、版としては在る
        if not merged_reads(path):
            continue
        if kind != "blob":
            raise Stop(2, [f"{tag}:{path}: サブモジュールは読まない。仕様書・前の版との比較を作れない"])
        if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise Stop(2, [f"{tag}:{path}: 写せないパス。仕様書・前の版との比較を作れない"])
        entries.append((mode, sha, path))
    fold = diffs.merge_versions.fold
    seen: dict[str, str] = {}
    clashes = []
    for _, _, path in sorted(entries, key=lambda e: e[2]):
        other = seen.setdefault(fold(path), path)
        if other != path:
            clashes.append(f"{tag}: {other} と {path} が大文字小文字・Unicode の正規化だけ違う（同じ場所に書かれうる）")
    dirs: dict[str, str] = {}
    for _, _, path in sorted(entries, key=lambda e: e[2]):
        parts = path.split("/")
        for depth in range(1, len(parts)):
            parent = "/".join(parts[:depth])
            if fold(parent) in seen:
                clashes.append(f"{tag}: {seen[fold(parent)]} がファイルとディレクトリの両方になる（{path}）")
            other = dirs.setdefault(fold(parent), parent)
            if other != parent:
                clashes.append(f"{tag}: ディレクトリ {other} と {parent} が大文字小文字・Unicode の正規化だけ違う（同じ場所に書かれうる）")
    if clashes:
        raise Stop(1, sorted(set(clashes)) + ["仕様書・前の版との比較を作れない（写すと同じ場所に書かれる）"])
    batch = subprocess.run(["git", "-C", str(top), "cat-file", "--batch"],
                           input=b"".join(sha.encode() + b"\n" for _, sha, _ in entries), capture_output=True)
    if batch.returncode != 0:
        raise Stop(2, [f"{tag}: {signoff.DOCS}/ を読めない: {batch.stderr.decode('utf-8', 'replace').strip()}"])
    data, at, root = batch.stdout, 0, dest.resolve()
    for name in sorted(versions):
        (dest / signoff.DOCS / name).mkdir(parents=True, exist_ok=True)
    for mode, _, path in entries:
        end = data.index(b"\n", at)
        size = int(data[at:end].split()[2])
        content, at = data[end + 1:end + 1 + size], end + 2 + size
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        parent = target.parent.resolve()
        if parent != root and root not in parent.parents:
            raise Stop(2, [f"{tag}:{path}: 写す先が一時ディレクトリの外に出る。仕様書・前の版との比較を作れない"])
        if os.path.lexists(target):
            raise Stop(1, [f"{tag}:{path}: 写す先に既に別のものがある。仕様書・前の版との比較を作れない"])
        if mode == "120000":
            # リンクのまま置く——重ね合わせの決まりが断る（版の外を読ませない）
            target.symlink_to(content.decode("utf-8", "surrogateescape"))
        else:
            target.write_bytes(content)


def drop_internal(docs: Path) -> None:
    """内部の層の Q&A（`spec/qa-dev.csv` と `removed.csv` の `D-` の行）を比べる前に外す。

    提案書は共有の表だけを見る（`references/qa-csv.md` の「層」。#339）——載せないだけでなく、
    内部の表の決まりの違反で比較が作れなくなることもない（照合も内部の表を見ない）。
    """
    mv = diffs.merge_versions
    for root in sorted(p for p in docs.iterdir() if mv.VERSION.fullmatch(p.name)):
        internal = root / mv.INTERNAL_QA_PATH
        if os.path.lexists(internal):
            internal.unlink()
        removed = root / mv.REMOVED
        if removed.is_file() and not removed.is_symlink():
            rows = list(csv.reader(io.StringIO(mv.read_text(removed), newline="")))
            kept = [r for r in rows if not (len(r) >= 2 and r[0] == mv.KIND_QA and qa.is_internal_number(r[1].strip()))]
            if len(kept) != len(rows):
                buffer = io.StringIO(newline="")
                csv.writer(buffer, lineterminator="\n").writerows(kept)
                removed.write_text(buffer.getvalue(), encoding="utf-8")


def compare_at(top: Path, commit: str, tag: str, version: int):
    """`commit` の時点の v1〜v<version> を重ねた全体と、v2 以降なら v<version-1> との比較を返す。作れなければ Stop。

    全体は仕様書の材料、比較は「前の版からの変更」の節（提案書と仕様書）。**v1 でも重ね合わせの決まりを通す**（#374）。
    """
    with tempfile.TemporaryDirectory() as tmp:
        copy_docs(top, commit, tag, Path(tmp))
        drop_internal(Path(tmp) / signoff.DOCS)
        prefix = str(Path(tmp)) + "/"
        try:
            problems, _, whole, _ = diffs.merge_versions.merge(Path(tmp) / signoff.DOCS, version)
            diff = None
            if not problems and version > 1:
                problems, diff = diffs.compare(Path(tmp) / signoff.DOCS, version)
        except diffs.merge_versions.Unreadable as e:
            raise Stop(2, [f"{tag}: {str(e).replace(prefix, '')}"])
    if problems:
        raise Stop(1, [f"{tag}: {line.replace(prefix, '')}" for line in problems]
                   + ["仕様書・前の版との比較を作れない（重ね合わせが決まりに反する）"])
    return whole, diff


def changes_section(diff, tag: str) -> list[str]:
    qa_kind, feature_kind, file_kind = diffs.SHARED_KINDS
    out = [f"## 前の版（v{diff.version - 1}）からの変更", ""]
    out += [f"> `{tag}` の時点の、v{diff.version - 1} までの全体と v{diff.version} までの全体の比較。"
            "同じ中身を置き直しただけのものは載らない。", ""]
    out += table(["種類", *diffs.STATUSES], [[k, *(str(diff.count(k, s)) for s in diffs.STATUSES)] for k in diffs.SHARED_KINDS])
    out.append("")
    if not any(diff.changes[k] for k in diffs.SHARED_KINDS):
        return out + ["（前の版からの変更はありません）", ""]

    def answer(row) -> str:
        return row["回答"] if row is not None else "—"

    if diff.changes[qa_kind]:
        out += [f"### {qa_kind}", ""]
        out += table(["No", "変化", "質問", "前の版の回答", "この版の回答", "削除の理由"],
                     [[c.key, c.status, diffs.label(qa_kind, c), answer(c.before), answer(c.after), c.reason or "—"]
                      for c in diff.changes[qa_kind]])
        out.append("")
    if diff.changes[feature_kind]:
        out += [f"### {feature_kind}", ""]
        out += table(["id", "変化", "題", "削除の理由"],
                     [[c.key, c.status, diffs.label(feature_kind, c) or "—", c.reason or "—"]
                      for c in diff.changes[feature_kind]])
        out.append("")
    if diff.changes[file_kind]:
        out += [f"### {file_kind}", ""]
        out += table(["パス", "変化", "削除の理由"], [[c.key, c.status, c.reason or "—"] for c in diff.changes[file_kind]])
        out.append("")
    return out


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


def compose(title: str, info: dict, hand: list[tuple[str, str]], qa_rows: list[dict[str, str]],
            schedule: list[dict[str, str]], estimate: list[dict[str, str]], diff=None) -> str:
    version = info["version"]
    out = [f"# {title}", ""]
    out.append(f"> この提案書は生成物です。生成元: `{info['req']}`（`{info['req_commit']}`）・"
               f"`{info['budget']}`（`{info['budget_commit']}`）の時点の `{in_version(version, 'shared/')}`・"
               f"`{in_version(version, 'feasibility/')}` と、"
               f"`{in_version(version, HAND_DIR)}/` の手書き部分。**決裁者の承認の記録ではありません。**")
    out += [">", f"> 何を作るかは、同じ場所の仕様書（[{SPEC_NAME}]({SPEC_NAME})）を見る。", ""]
    for _, body in hand:
        out += [body.rstrip("\n"), ""]
    if diff is not None:
        out += changes_section(diff, info["req"])

    # 暫定の行（`check-qa-csv.py` の `is_provisional`）は利用者の合意ではないので、決定事項と分けて載せる（#374）
    provisional = [r for r in qa_rows if qa.is_provisional(r)]
    done = [r for r in qa_rows if r["状態"].strip() == qa.DONE]
    pending = [r for r in qa_rows if r["状態"].strip() != qa.DONE and not qa.is_provisional(r)]
    out += ["## 主な決定事項", ""]
    if done:
        out += table(["No", "質問", "回答", "反映先"], [[r["No"], r["質問"], r["回答"], r["反映先"]] for r in done])
    else:
        out.append("（反映済みの決定事項はありません）")
    out.append("")
    # `##` にする——`###` だと PPTX で「主な決定事項」の題のスライドに暫定の行が載る（`markdown_slides` は `##` で分ける）
    scope = "この版の Q&A で" if diff is not None else ""
    out += [f"## {scope}利用者にまだ確かめていない決定（{len(provisional)} 件）", ""]
    if diff is not None:
        out += ["前の版までの Q&A の暫定の行はここに載らない（仕様書の規模の「暫定」に数える）。", ""]
    if provisional:
        out += ["> 暫定で採った回答で、利用者の合意ではない。仕様レビューを抜けたことも合意の代わりにはならない。", ""]
        out += table(["No", "質問", "回答", "反映先"], [[r["No"], r["質問"], r["回答"], r["反映先"]] for r in provisional])
    else:
        out.append("（ありません）")
    out.append("")
    if pending:
        out += [f"## 承認の時点で未決定の質問（{len(pending)} 件）", ""]
        out += table(["No", "質問", "選択肢", "費用への影響"],
                     [[r["No"], r["質問"], r["選択肢"], r["費用への影響"]] for r in pending])
        out.append("")

    out += ["## 費用", ""]
    if diff is not None:
        out += [f"この版（v{version}）の差分の見積り。前の版までの費用は含まない。", ""]
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


def read_hand(directory: Path) -> list[tuple[str, str]]:
    """手書き部分（`directory` 直下の `*.md`、ファイル名の順）。作業ツリーから読む。"""
    hand = []
    for path in sorted(directory.glob("*.md")) if directory.is_dir() else []:
        try:
            hand.append((path.name, path.read_text(encoding="utf-8-sig")))
        except (OSError, UnicodeDecodeError):
            raise Stop(2, [f"{path}: UTF-8 として読めない。中身を検査していない"])
    return hand


def decode(content: bytes, label: str) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Stop(2, [f"{label}: UTF-8 として読めない。仕様書を作れない"])


def heading_level(line: str) -> int:
    level = len(line) - len(line.lstrip("#"))
    return level if 0 < level <= 6 and line[level:level + 1] == " " else 0


def out_of_scope(text: str) -> list[str] | None:
    """範囲の文書の「範囲の外」の節の本文（見出しは除く。次の同じか上の水準の見出しまで）。節が無ければ None。"""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        level = heading_level(line)
        if level and OUT_OF_SCOPE in line:
            body = []
            for rest in lines[i + 1:]:
                if 0 < heading_level(rest) <= level:
                    break
                body.append(rest)
            while body and not body[0].strip():
                body.pop(0)
            while body and not body[-1].strip():
                body.pop()
            return body
    return None


def figures_of(whole) -> tuple[list[str], list[str]]:
    """(載せる図——`.svg`、書き出しが無いので載せない `.drawio`)。どちらもパスの順。図は `spec/`・`requirements/` の中だけ。"""
    paths = sorted(p for p in whole.files if p.startswith(FIGURE_DIRS))
    svgs = [p for p in paths if p.lower().endswith(".svg")]
    exported = {p.lower() for p in svgs}
    missing = [p for p in paths if p.lower().endswith(".drawio")
               and f"{p}.svg".lower() not in exported and f"{p[:-len('.drawio')]}.svg".lower() not in exported]
    return svgs, missing


def compose_spec(title: str, info: dict, hand: list[tuple[str, str]], whole, diff,
                 proposal_name: str) -> tuple[str, dict[str, bytes]]:
    """(仕様書, 図のファイル名 → 中身) を返す。材料は req のタグの時点の重ねた全体と、仕様書の手書き部分。"""
    version = info["version"]
    span = f"`{signoff.DOCS}/v1/`" if version == 1 else f"`{signoff.DOCS}/v1/`〜`{signoff.DOCS}/v{version}/` を重ね合わせた全体"
    out = [f"# {title}", ""]
    out.append(f"> この仕様書は生成物です。生成元: `{info['req']}`（`{info['req_commit']}`）の時点の "
               f"{span}（`shared/`・`requirements/`・`spec/`。"
               f"内部の Q&A 表は除く）と、`{in_version(version, SPEC_HAND_DIR)}/` の手書き部分。"
               "**決裁者の承認の記録ではありません。**")
    out += [">", f"> 費用・期間・推奨案は、同じ場所の提案書（[{proposal_name}]({proposal_name})）を見る。", ""]
    for _, body in hand:
        out += [body.rstrip("\n"), ""]
    if not hand:
        out += [f"（手書き部分（`{in_version(version, SPEC_HAND_DIR)}/*.md`）はありません——画面の一覧・"
                "試作で確かめること・要約は載っていない）", ""]

    files = sorted(whole.files)
    decision = whole.files.get(DECISION_PATH)
    decision_rows = None
    if decision is not None:
        try:
            decision_rows = [r for r in csv.reader(io.StringIO(decode(decision, DECISION_PATH), newline=""))
                             if any(c.strip() for c in r)]
        except csv.Error as e:
            raise Stop(2, [f"{info['req']}:{DECISION_PATH}: CSV として読めない（{e}）。仕様書を作れない"])
    shared_rows = list(whole.qa.values())
    provisional = sum(1 for r in shared_rows if qa.is_provisional(r))
    decided = sum(1 for r in shared_rows if r["状態"].strip() == qa.DONE)
    svgs, missing = figures_of(whole)
    out += ["## 規模", ""]
    out += table(["もの", "数"], [
        ["要求のファイル（`requirements/`）", str(sum(1 for p in files if p.startswith("requirements/")))],
        ["仕様のファイル（`spec/`。中間表現と内部の Q&A 表を除く）", str(sum(1 for p in files if p.startswith("spec/")))],
        ["決定表の行（見出しを除く）", str(len(decision_rows) - 1) if decision_rows else "—（決定表が無い）"],
        ["Q&A（共有。v1 から重ねた全体）",
         f"{len(shared_rows)}（決定 {decided}・暫定 {provisional}・未決定 {len(shared_rows) - decided - provisional}）"],
        ["機能（中間表現）", str(len(whole.features)) if whole.spec is not None else "—（中間表現が無い）"],
        ["図", f"{len(svgs)}（書き出しが無いので載せていない図 {len(missing)}）"],
    ])
    out.append("")

    figures: dict[str, bytes] = {}
    out += ["## 構成の図", ""]
    for n, path in enumerate(svgs, 1):
        name = f"{FIGURE_PREFIX}{n:02d}.svg"
        figures[name] = whole.files[path]
        out += [f"![{path}]({name})", "", f"`{path}`", ""]
    if not svgs:
        out += ["（図はありません）", ""]
    if missing:
        out += ["書き出し（`.svg`）が無いので載せていない図:", ""] + [f"- `{path}`" for path in missing] + [""]

    out += ["## 機能の一覧", ""]
    if whole.features:
        out += table(["id", "題"], [[fid, str(f.get("title", ""))] for fid, f in whole.features.items()])
    else:
        out.append("（中間表現（`spec/spec_ir.json`）に機能がまだ無い——機能の一覧は scaffold の後に載る。画面の一覧は手書き部分に書く）")
    out.append("")

    out += ["## 決定表", ""]
    if decision_rows:
        width = max(len(r) for r in decision_rows)
        padded = [r + [""] * (width - len(r)) for r in decision_rows]
        out += table([cell(c) for c in padded[0]], padded[1:])
    else:
        out.append(f"（決定表（`{DECISION_PATH}`）が無いか空）")
    out.append("")

    out += [f"## {OUT_OF_SCOPE}", ""]
    scope = whole.files.get(SCOPE_PATH)
    body = out_of_scope(decode(scope, SCOPE_PATH)) if scope is not None else None
    if body:
        out += body + [""]
    elif body is not None:
        out += [f"（範囲の文書（`{SCOPE_PATH}`）の「{OUT_OF_SCOPE}」の節は空——範囲の外とした場面はまだ無い）", ""]
    else:
        out += [f"（範囲の文書（`{SCOPE_PATH}`）に「{OUT_OF_SCOPE}」の節が無い——範囲の外とした場面は記録されていない）", ""]

    if diff is not None:
        out += changes_section(diff, info["req"])

    out += ["## 仕様と要求のファイル", ""]
    listed = [p for p in files if p.startswith(("spec/", "requirements/"))]
    out += table(["パス"], [[p] for p in listed]) if listed else ["（ありません）"]
    out.append("")
    return "\n".join(out), figures


def build(args, out: Path) -> dict[Path, bytes | list]:
    """書くもの（出力先 → 中身。PPTX は部品の一覧）を返す。作れなければ Stop——1 つでも作れなければ何も書かない。"""
    code, lines, info = signoff.resolve(args.repo, args.req, args.budget, args.version)
    if code:
        raise Stop(code, lines)
    print("\n".join(lines))
    top = Path(info["top"])
    qa_path, schedule_path, estimate_path = (in_version(info["version"], p) for p in (QA_PATH, SCHEDULE_PATH, ESTIMATE_PATH))
    if info["version"] > 1 and not exists(top, info["req_commit"], qa_path):
        # v2 以降は差分だけなので、Q&A を足さない版は `qa.csv` を置かない（`references/versions.md`）
        qa_rows = []
    else:
        qa_rows = read_qa(show(top, info["req_commit"], info["req"], qa_path), f"{info['req']}:{qa_path}")
    schedule = read_table(feasibility.check_schedule, show(top, info["budget_commit"], info["budget"], schedule_path),
                          f"{info['budget']}:{schedule_path}")
    estimate = read_table(feasibility.check_estimate, show(top, info["budget_commit"], info["budget"], estimate_path),
                          f"{info['budget']}:{estimate_path}")
    if not schedule:
        raise Stop(1, [f"{info['budget']}:{schedule_path}: 工程が 1 行も無い。提案書の材料が無い"])
    if not estimate:
        raise Stop(1, [f"{info['budget']}:{estimate_path}: 費用が 1 行も無い。提案書の材料が無い"])
    whole, diff = compare_at(top, info["req_commit"], info["req"], info["version"])
    hand_dir = top / in_version(info["version"], HAND_DIR)
    hand = read_hand(hand_dir)
    if not hand:
        raise Stop(1, [f"{hand_dir}: 手書き部分（*.md）が無い。背景と目的・推奨案・代替案・リスクを書いてから作る"])
    text = compose(args.title, info, hand, qa_rows, schedule, estimate, diff)
    spec_text, figures = compose_spec(args.spec_title, info, read_hand(top / in_version(info["version"], SPEC_HAND_DIR)),
                                      whole, diff, out.name)
    outputs = {out: text.encode("utf-8"), out.parent / GANTT_NAME: gantt.render(schedule).encode("utf-8"),
               out.parent / SPEC_NAME: spec_text.encode("utf-8")}
    outputs.update({out.parent / name: content for name, content in figures.items()})
    if args.pptx:
        # 図を見る先は、その PPTX の元の Markdown（ガントチャートは提案書、構成の図は仕様書にしか無い）
        for path, body, name, source in ((out.with_suffix(".pptx"), text, args.title, out.name),
                                         (out.parent / SPEC_PPTX_NAME, spec_text, args.spec_title, SPEC_NAME)):
            outputs[path] = pptx.package(pptx.markdown_slides(body, FIGURE_NOTE.format(source)), name)
    return outputs


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
    parser.add_argument("--version", type=signoff.positive)
    parser.add_argument("--req")
    parser.add_argument("--budget")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title", default="提案書")
    parser.add_argument("--spec-title", default="仕様書")
    parser.add_argument("--pptx", action="store_true", help="提案書と仕様書の PPTX も作る")
    args = parser.parse_args(argv)

    # git を起動できなくても、古い出力は消してから 2 で終わる（ここで落ちると古い提案書が残る）
    out = args.out if args.out else repo_top(args.repo) / DEFAULT_OUT
    # 大文字小文字だけ違う名前も重なる（区別しない FS では同じファイル）。`spec.html` なら PPTX が仕様書の PPTX と重なる
    reserved = {name.lower() for name in (SPEC_NAME, GANTT_NAME, SPEC_PPTX_NAME)}
    if ({out.name.lower(), out.with_suffix(".pptx").name.lower()} & reserved or out.suffix.lower() == ".pptx"
            or out.name.lower().startswith(FIGURE_PREFIX)):
        print(f"{out}: 仕様書・ガントチャート・PPTX・図と同じ名前になる。提案書は作っていない", file=sys.stderr)
        return 2
    stales = [out, out.parent / GANTT_NAME, out.parent / SPEC_NAME, out.with_suffix(".pptx"), out.parent / SPEC_PPTX_NAME]
    stales += sorted(out.parent.glob(f"{FIGURE_PREFIX}*.svg")) if out.parent.is_dir() else []
    for stale in stales:
        if stale.is_file():
            stale.unlink()
            print(f"{stale}: 前に作った出力を消した", file=sys.stderr)

    try:
        try:
            outputs = build(args, out)
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
    for path, content in outputs.items():
        if isinstance(content, list):
            pptx.write(content, path)
        else:
            path.write_bytes(content)
    print(f"{out}: 提案書を書いた（同じ場所に {'・'.join(p.name for p in outputs if p != out)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
