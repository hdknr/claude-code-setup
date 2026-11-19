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
  （承認の対象ではない。ファイル名の順に先頭へ並べる）。**書いた綴りのとおりに探し、`docs/v<n>/Proposal/` のような綴りだけ違うフォルダは
  名指しして 2**（`read_hand`。区別しない FS でだけ読めてしまうため。#514）。
  **v2 以降は、その版の差分の表に加えて、前の版との比較の節が載る**（変更の提案書）——比較は同梱の `diff-versions.py` の
  `compare` を、**`signoff/v<n>/req-<k>` の時点の `docs/`** に当てる（`git ls-tree`・`git cat-file` で一時ディレクトリに写す。
  `git archive` は `.gitattributes` で中身が変わるので使わない。写すのは重ね合わせが読むものだけで、
  **大文字小文字・Unicode の正規化だけが違うパスがあれば写さずに 1**——区別しないファイルシステムでは同じ場所に書かれる。
  **版の直下の、置き場所・`removed.csv` と綴りだけ違う名前（`Removed.csv`・`Shared/`）も写し、重ね合わせに 1 で断らせる**——
  写さなければ、作業ツリーで重ねる側（綴りだけ違う名前を断る）と答えが食い違う。#276。
  内部の層を外すときも綴りどおりの名前だけを外す）。決まりの正は `references/versions.md` の「版の差分」。
  **重ね合わせが作れなければ書かない（1）。** 費用の節は**その版の差分の見積り**で、前の版までの費用は足さない。
  **v2 以降で `shared/qa.csv` を置かない版**（Q&A を足さない版。`references/versions.md`）は、Q&A を 0 行として作る。
  v1 では `qa.csv` が無ければ作らない。
- 読んだ表は決まりの検査（`check-qa-csv.py`・`check-feasibility-csv.py`）を通す。通らなければ書かない。
- **基盤要件のゲート（#950）**: `signoff/v<n>/req-<k>` の時点の v1〜v<n> を重ねた全体（仕様書の材料と同じ）の `shared/infra.csv` に
  同梱の `check-infra-csv.py` を当てる——**形式の違反・未決定は 1、暫定は 3、読めなければ 2 で書かない**（予算の決裁を、誰も決めていない
  基盤で進めない）。暫定は、根拠の Q&A が `暫定反映` なので照合の 3 が先に止める。**表が無ければ止めず、標準エラーに警告して書く**
  （前からの正本は表を持たない）。決まりの正は `references/tree.md` の「基盤要件」の「ゲート」。
- **目的と成功の判定（#1154）**: `signoff/v<n>/req-<k>` の時点の重ねた全体に目的の表（`requirements/purposes.csv`）があれば、手書き部分の後ろに
  「目的と成功の判定」の節としてその表を載せる（手書きの背景と目的に、目的と指標を二重に書かせない）。**表が無ければ節を出さない**（前と同じバイト）。
  **見出しの行・列の数が決まり（`check-design-csv.py` の `PURPOSES_COLUMNS`。写さない）と違えば 1 で書かない**——中身の検査（結び付け・未決定）は
  `check-design-csv.py`（req-loop・spec-review・scaffold が当てる）。決まりの正は `references/tree.md` の「目的と成功の判定」。
- **暫定の行**（判別は `check-qa-csv.py` の `is_provisional`。決まりの正は `references/qa-csv.md` の「暫定の行の判別」）は
  主な決定事項に載せず、「利用者にまだ確かめていない決定」の節に載せる（0 件でも節を出す。#366）。
  **照合が 3 で止めるので、書いた提案書ではこの節は 0 件になる**（#404 で判別を状態だけにした）——節は、決裁者に
  「残っていない」ことを示すために出す。
- **仕様書（`spec.md`）も同じ実行で作る**（#371）——材料は `signoff/v<n>/req-<k>` の時点の v1〜v<n> を重ねた全体
  （前の版との比較と同じ写しから。**v1 でも重ね合わせの決まりを通す**）と、作業中の版の `proposal/spec/*.md`（手書き。任意）。
  `spec/`・`requirements/` の `.svg` の図は同じ場所に `spec-figure-NN.svg` として写して載せ、`.svg` の無い `.drawio`・`.bpmn` は載せていないと書く（描画系は起動しない）。
  **書き出しが今のソースと合わない図**（ソース `X.drawio`・`X.bpmn` の隣の `X.svg` に `render-diagrams.py` の印が無いか、印の指紋がソースと違う。判定は
  `render-diagrams.py` の関数を読み込む。改行の変換で作業ツリーが CRLF でも合うと見る）**も載せ、仕様書にそう名指しする**（#902。終了コードは変えない）。
  `X.drawio.svg` は `X.drawio` の書き出しと数えるが、`X.bpmn.svg` は `X.bpmn` の書き出しと数えず、隣に `X.bpmn` があれば図としても載せない。載せるものと置き場所の正は `references/tree.md` の「仕様書」。
  **形式検査のモデル（`spec/formal/`）は、規模・図・「仕様と要求のファイル」のどれにも入れない**——仕様から書き起こした写し（判別は `merge-versions.py` の `is_formal`。
  `references/tree.md` の「形式検査のモデル」。#908）。「前の版からの変更」にも出ない（`diff-versions.py` が比べない）。
- **`--pptx` で提案書と仕様書の PPTX と、別紙の表（`decisions.xlsx`。利用者と決めたことの全件）も作る**（#1289。既定のデザインは `proposal-pptx.py`、
  決まりの正は `references/tree.md` の「PPTX のデザインと指示」）。図は PNG にして載せる（`rsvg-convert`。無ければ載せずに標準エラーに知らせ、0 で作る）。
  **指示（正本の `CLAUDE.md`。proposal のスキルが引数に組む）**: `--pptx-script <スクリプト>`（PPTX の生成を差し替える。材料は出力（提案書は `--out` の名前。既定は `proposal.md`）・`spec.md`・`gantt.svg`・
  `spec-figure-NN.svg`・別紙だけを置いたディレクトリで、`python3 <スクリプト> --materials <ディレクトリ> --proposal-out <p.pptx> --spec-out <s.pptx>`。0 でない・2 本が揃わない・
  zip でない・300 秒を超えるは 2）・`--no-appendix`（別紙を作らない）・`--no-scope-slide`・`--scope-questions`・`--scope-match`・`--overview`・`--slide-strip`。
  **これらは `--pptx` と一緒にしか渡せない**（argparse の 2）。
- **始める前に、前に作った出力を消し、全部作れてから書く**——作れなかったときに、古い提案書を今のものと取り違えないため。
  **消すのは、出力と同じ場所の印（`.build-proposal`）が名指しするものだけ**（#405）——印は書いた出力（提案書・`gantt.svg`・
  `spec.md`・PPTX・別紙 `decisions.xlsx`・`spec-figure-*.svg`）の名前の一覧で、出力より先に書く。**印の無い場所では何も消さない**——`--out` を
  手書きの `spec.md` の在る場所に向けても消さない（#397）。**書こうとする名前のファイルが印に無いまま在れば、上書きせずに 2。** **読めない印は消さない**（名指しした出力も消さない）。
  **読めない印（UTF-8 で読めない・ディレクトリ・symlink——辿れても辿れなくても）は書き換えもせず、作れても書く前に 2 で止まる**（#512。書けば読めない印の跡が消え、
  symlink の印なら先——出力の場所の外——に書く）。**印が名指しする出力が symlink なら、先が在る（辿れない先を含む）かぎりリンクも先も消さず、
  リンクと先のパスを「消せない」で名指しして 2**（#512。`schedule-to-gantt.py` の #626 と同じ——リンクを消しても先の古い中身は残る）。壊れたリンクは消す。
  **引数の誤り（名前が無い・ディレクトリ・名前の衝突・印に残せない名前）は消す前に見て 2 で止めるが、印が名指しする前の出力は消す**（#398。
  ディレクトリを渡したなら、その中の印が名指しするものも消す）。
  **spec-loop 0.25.0 までが作った出力には印が無い**ので、消してから作り直す（`references/tree.md` の移行の節）。
  **作れなかったとき（0 以外。出力先が決まる前に止まった 2——引数の解釈に失敗した `argparse` の 2 と、`--out` を渡さずに根を求める途中の想定外の例外——は除く）は、出力の場所に残った今回の出力ではないファイルを名指しする**（#498。消さない）——
  出力の名前（`--out` の名前・`proposal.md`・`gantt.svg`・`spec.md`・提案書と仕様書の PPTX・`spec-figure-<数字>.svg`。大文字小文字を区別しない）の
  ファイルのうち読める印に無いものと、読めない印（とその場所の出力の名前のファイル）。印が名指しするのに消せなかった出力は「消せない」で名指しする。
  **上書きを断った 2 では、「上書きしない」と言ったファイルを「今回の出力ではない」で重ねて名指ししない**（#551。同じ項目か——同じ名前か、
  大文字小文字だけ違い `lstat` が同じファイル——で見る。ハードリンクのような別の名前の項目は別に名指しする）。
  **作れたとき（0）も、印に無い出力の名前のファイルが残っていれば「今回の出力ではない」と標準エラーに名指しする**（#553。終了コードは 0 のまま。
  0.25.0 の `proposal.pptx` を `--pptx` 無しで作ったとき・手で置いた `spec-figure-NN.svg` など。出力の場所を読めなければ「前の出力が残っているかを確かめられない」と言う）。**出力の名前でないファイル（手書きの `notes.md` など）は名指ししない。**
- **提案書は承認の記録を持たない。** 載せるのは生成元のタグとコミットだけで、「承認済み」とは書かない。
- 同じ入力から同じバイトを作る（時刻を書かない）。標準ライブラリだけを使う（`git` は要る）。

終了コード:

- 0: 書いた
- 1: 照合が一致しない・表が決まりに反する（目的の表の見出しの行・列の数を含む。#1154）・材料（表・手書き部分）が無い・基盤要件が決まっていない（#950）——書いていない
- 2: 照合していない・表が読めない（`check-signoff.py` の 2 と同じ。目的の表の空のファイルを含む——#1154）・手書き部分のフォルダの綴りが書いた綴りと大文字小文字だけ違う（#514）・出力先の名前が無い・前後に空白がある・改行を含むか `#` で始まる・`\\` を含む・UTF-8 で書けない・確かめられない（辿れない）・ディレクトリ・仕様書・ガントチャート・PPTX・図・印と重なる・
  印に無いファイルが出力の名前で在る・印が読めない（書き換えない。#512）・書けない・印が名指しする前の出力を消せない（消せなかったものを名指しし、印は残す。#440。
  印が名指しする出力が先の在る symlink のときを含む——#512）・
  想定外の例外（128KB を超えるセルの `csv.Error` など。#286。前の出力は作り始める前に消してあり、書いている途中なら書きかけを消す）——書いていない。
  **git を起動できない・手書き部分を読めない・出力を書けない・一時ファイルを読み書きできないは、別の文言で strerror とパスを出す**
- 3: 要求確定のタグの時点に暫定の回答（`暫定反映`）が残る（`check-signoff.py` の 3 と同じ）・基盤要件に暫定の行がある（#950）——書いていない

**守らないもの**: 手書き部分の中身（判断であって一意に決まらない）・見た目（Markdown を表示して目で見る）・
PPTX がアプリで開けること（見るのは部品の揃いと XML の整形式まで。描画して確かめるのは `check-pptx-render.py`）・差し替えスクリプトの中身・前の版の暫定の行（提案書に載るのはその版の `qa.csv` だけ）。
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import os
import re
import stat
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
# `--pptx` の既定のデザイン・別紙の xlsx（#1289）
ppt = _load("proposal_pptx", "proposal-pptx.py")
# 図の書き出しの印と指紋（#902）。判定の式を 2 箇所に置かない
diagrams = _load("render_diagrams", "render-diagrams.py")
# 基盤要件の表の検査とゲートの判定（#950。写さない）
infra = _load("check_infra_csv", "check-infra-csv.py")
# 目的の表の置き場所と見出しの行（#1154。写さない）
design = _load("check_design_csv", "check-design-csv.py")

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
DECISIONS_NAME = "decisions.xlsx"  # 別紙（`--pptx`。利用者と決めたことの全件。#1289）
SCRIPT_TIMEOUT = 300  # 差し替えスクリプト（`--pptx-script`）の秒数
SPEC_HAND_DIR = HAND_DIR + "/spec"
FIGURE_PREFIX = "spec-figure-"
FIGURE_DIRS = ("spec/", "requirements/")
# 出力と同じ場所に置く印（書いた出力のファイル名の一覧）。次の実行はここに載る名前だけを消す（#405）
MANIFEST = ".build-proposal"
MANIFEST_HEAD = "# build-proposal.py が作った出力の一覧。手で直さない（ここに載るファイルは次の実行で消える）"
# 重ねた全体（版のディレクトリからのパス）
DECISION_PATH = "shared/decision_table.csv"
SCOPE_PATH = "spec/scope.md"
OUT_OF_SCOPE = "範囲の外"


def in_version(version: int, path: str) -> str:
    return f"{signoff.DOCS}/v{version}/{path}"


class Stop(Exception):
    def __init__(self, code: int, lines: list[str], named: tuple[Path, ...] = ()):
        super().__init__(lines)
        # named: `lines` がもう名指ししたファイル——続く「今回の出力ではない」で 2 度名指ししない（#551）
        self.code, self.lines, self.named = code, lines, named


def run_git(top: Path, *args: str, **kwargs) -> subprocess.CompletedProcess:
    """`git` を起動する。起動できなければ Stop(2)——手書き部分の読み・出力の書き込みの失敗と文言を分ける（#286）。"""
    try:
        return subprocess.run(["git", "-C", str(top), *args], capture_output=True, **kwargs)
    except OSError as e:
        raise Stop(2, [f"git を起動できない（{e.strerror}: {e.filename}）。提案書の材料を読んでいない"])


def show(top: Path, commit: str, tag: str, path: str) -> str:
    result = run_git(top, "show", f"{commit}:{path}")
    if result.returncode != 0:
        raise Stop(1, [f"{tag}:{path}: 承認の時点に無い。提案書の材料が無い"])
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        raise Stop(2, [f"{tag}:{path}: UTF-8 として読めない。中身を検査していない"])


def exists(top: Path, commit: str, path: str) -> bool:
    result = run_git(top, "ls-tree", "--name-only", commit, "--", path, text=True)
    if result.returncode != 0:
        raise Stop(2, [f"{commit[:7]}:{path}: 在るかを確かめられない: {result.stderr.strip()}"])
    return bool(result.stdout.strip())


def merged_reads(path: str) -> bool:
    """重ね合わせが読むものか——`docs/v…` の名前そのものと、版の中の置き場所・`removed.csv`（`.` で始まる名前は読まない）。

    **版の直下の名前は、綴りだけ違うもの（`Removed.csv`・`Shared/`）も写す**——重ね合わせがそれを 1 で断る（#276）。
    写さないと、作業ツリーで重ねる側と答えが食い違う。
    """
    parts = PurePosixPath(path).parts
    if len(parts) < 2 or parts[0] != signoff.DOCS or not diffs.merge_versions.VERSION_LIKE.match(parts[1]):
        return False
    if len(parts) == 2:
        return True
    inside = parts[2:]
    if any(p.startswith(".") for p in inside):
        return False
    mv = diffs.merge_versions
    return mv.fold(inside[0]) in {mv.fold(name) for name in [*mv.AREAS, mv.REMOVED]}


def copy_docs(top: Path, commit: str, tag: str, dest: Path) -> None:
    """`commit` の時点の `docs/` のうち重ね合わせが読むものを `dest` の下に写す（作業ツリーは読まない）。

    **大文字小文字・Unicode の正規化だけが違うパスがあれば写さない（1）**——区別しないファイルシステム
    （macOS の既定）では同じ場所に書かれ、片方が黙って消えるか、先に置いたリンクを辿って一時ディレクトリの外に
    書く。どのファイルシステムでも同じ答えにするため、写す前に一覧で断る。書く先が既にあるときも断る。
    """
    listing = run_git(top, "ls-tree", "-r", "-z", "--full-tree", commit, "--", signoff.DOCS)
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
    batch = run_git(top, "cat-file", "--batch", input=b"".join(sha.encode() + b"\n" for _, sha, _ in entries))
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
    **綴りどおりの名前だけを外す**（`merge-versions.py` の `exact`）——区別しないファイルシステムで `spec/QA-dev.csv`
    （重ね合わせではふつうのファイル）を内部の表として消すと、作業ツリーの差分と比較が食い違う（#276）。
    **途中の名前（版のディレクトリ `docs/v<n>` そのもの・`spec/`）がリンクなら、消さず・書き換えない**（#512）——`exact` はリンクを辿るので、
    外の `qa-dev.csv` を消し、外の `removed.csv` を書き換える（リンクの先が一時ディレクトリの中でも、その先は版の外である）。
    外さずに残せば、重ね合わせがリンクの置き場所を断る。対象そのもの（`qa-dev.csv`）がリンクなら、消えるのは一時ディレクトリの中のリンクだけである。
    """
    mv = diffs.merge_versions

    def inside(path: Path) -> bool:
        """`docs` から置き場所（親のディレクトリ）までの途中にリンクが無いか（`docs` の下の名前だけを見る）。"""
        place = path.parent
        while place != docs:
            if place.is_symlink():
                return False
            place = place.parent
        return True

    for root in sorted(p for p in docs.iterdir() if mv.VERSION.fullmatch(p.name)):
        internal = mv.exact(root, mv.INTERNAL_QA_PATH)
        if internal is not None and inside(internal):
            internal.unlink()
        removed = mv.exact(root, mv.REMOVED)
        if removed is not None and inside(removed) and removed.is_file() and not removed.is_symlink():
            rows = list(csv.reader(io.StringIO(mv.read_text(removed), newline="")))
            kept = [r for r in rows if not (len(r) >= 2 and r[0] == mv.KIND_QA and qa.is_internal_number(r[1].strip()))]
            if len(kept) != len(rows):
                buffer = io.StringIO(newline="")
                csv.writer(buffer, lineterminator="\n").writerows(kept)
                removed.write_text(buffer.getvalue(), encoding="utf-8")


def compare_at(top: Path, commit: str, tag: str, version: int):
    """`commit` の時点の v1〜v<version> を重ねた全体と、v2 以降なら v<version-1> との比較と、重ねた全体のバイト（根からのパス → 中身）を返す。
    作れなければ Stop。

    全体は仕様書の材料、比較は「前の版からの変更」の節（提案書と仕様書）。**v1 でも重ね合わせの決まりを通す**（#374）。
    バイトは基盤要件のゲート（#950）が読む——`whole.files` は Q&A 表など構造ファイル（`merge-versions.py` の `STRUCTURED`）を持たない。
    """
    with tempfile.TemporaryDirectory() as tmp:
        copy_docs(top, commit, tag, Path(tmp))
        drop_internal(Path(tmp) / signoff.DOCS)
        prefix = str(Path(tmp)) + "/"
        try:
            problems, _, whole, rendered = diffs.merge_versions.merge(Path(tmp) / signoff.DOCS, version)
            diff = None
            if not problems and version > 1:
                problems, diff = diffs.compare(Path(tmp) / signoff.DOCS, version)
        except diffs.merge_versions.Unreadable as e:
            raise Stop(2, [f"{tag}: {str(e).replace(prefix, '')}"])
    if problems:
        raise Stop(1, [f"{tag}: {line.replace(prefix, '')}" for line in problems]
                   + ["仕様書・前の版との比較を作れない（重ね合わせが決まりに反する）"])
    return whole, diff, rendered


def changes_section(diff, tag: str) -> list[str]:
    qa_kind, feature_kind, file_kind = diffs.SHARED_KINDS
    out = [f"## 前の版（v{diff.version - 1}）からの変更", ""]
    out += [f"> `{tag}` の時点の、v{diff.version - 1} までの全体と v{diff.version} までの全体の比較。"
            "同じ中身を置き直しただけのものは載らない。", ""]
    # 画面の表（画面・項目・遷移。行の単位で重ねる。#1091）は、どちらかの版の全体に表があるときだけ載せる（#1152）。
    # 表の無い正本は `diff.changes` に画面の種類を持たないので、出力は今と同じバイトのまま
    row_kinds = [k for k in diffs.ROW_KINDS if k in diff.changes]
    shown = [*diffs.SHARED_KINDS, *row_kinds]
    out += table(["種類", *diffs.STATUSES], [[k, *(str(diff.count(k, s)) for s in diffs.STATUSES)] for k in shown])
    out.append("")
    if not any(diff.changes[k] for k in shown):
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
    for kind in row_kinds:
        if diff.changes[kind]:
            # 鍵（画面ID・番号）・変化・題（画面だけ画面名）・削除の理由。項目・遷移の中身の列は出さない
            out += [f"### {kind}", ""]
            out += table(["鍵", "変化", "題", "削除の理由"],
                         [[c.key, c.status, diffs.label(kind, c) or "—", c.reason or "—"] for c in diff.changes[kind]])
            out.append("")
    return out


def changes_material(diff, tag: str) -> dict:
    """前の版からの変更を `--pptx` の既定のデザインに渡す形にする（#1289）。`changes_section` と同じ表の値（見出しの行・変化の語・削除の理由）。"""
    qa_kind, feature_kind, file_kind = diffs.SHARED_KINDS
    screen_kinds = [k for k in diffs.ROW_KINDS if diff.changes.get(k) is not None]
    listed = [*diffs.SHARED_KINDS, *screen_kinds]

    def reason(c) -> str:
        return c.reason or "—"

    def after_of(c) -> str:
        return c.after["回答"] if c.after is not None else "—"

    def before_of(c) -> str:
        return c.before["回答"] if c.before is not None else "—"

    details = []
    if diff.changes[qa_kind]:
        details.append((qa_kind, ["No", "変化", "質問", "前の版の回答", "この版の回答", "削除の理由"],
                        [[c.key, c.status, diffs.label(qa_kind, c), before_of(c), after_of(c), reason(c)] for c in diff.changes[qa_kind]]))
    if diff.changes[feature_kind]:
        details.append((feature_kind, ["id", "変化", "題", "削除の理由"],
                        [[c.key, c.status, diffs.label(feature_kind, c) or "—", reason(c)] for c in diff.changes[feature_kind]]))
    if diff.changes[file_kind]:
        details.append((file_kind, ["パス", "変化", "削除の理由"], [[c.key, c.status, reason(c)] for c in diff.changes[file_kind]]))
    for kind in screen_kinds:
        if diff.changes[kind]:
            details.append((kind, ["鍵", "変化", "題", "削除の理由"],
                            [[c.key, c.status, diffs.label(kind, c) or "—", reason(c)] for c in diff.changes[kind]]))
    return {"title": f"前の版（v{diff.version - 1}）からの変更", "tag": tag,
            "summary": (["種類", *diffs.STATUSES], [[k, *(str(diff.count(k, st)) for st in diffs.STATUSES)] for k in listed]),
            "details": details}


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


def read_purposes(files: dict[str, bytes], tag: str) -> list[list[str]] | None:
    """目的の表（#1154）の行（見出しを除く）。`files` は `tag` の時点の重ねた全体。表が無ければ None。
    見出しの行・列の数が決まりと違えば Stop(1)、CSV として読めなければ Stop(2)。"""
    content = files.get(design.PURPOSES)
    if content is None:
        return None
    label = f"{tag}:{design.PURPOSES}"
    text = decode(content, label)
    if not text.strip():
        raise Stop(2, [f"{label}: 空のファイル。提案書を作れない"])  # check-design-csv.py と同じく「読めない」（2）
    try:
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as e:
        raise Stop(2, [f"{label}: CSV として読めない（{e}）。提案書を作れない"])
    # 見出しは最初の行（check-design-csv.py と同じ——空行を飛ばして次の行を見出しに取らない）。空行を除くのは本文だけ
    rows = rows[:1] + [r for r in rows[1:] if any(c.strip() for c in r)]
    if rows[0] != design.PURPOSES_COLUMNS:
        raise Stop(1, [f"{label}: 見出しの行が決まり（{','.join(design.PURPOSES_COLUMNS)}）と違う。提案書の材料にできない"
                       "（check-design-csv.py で直す。references/tree.md の「目的と成功の判定」）"])
    bad = [str(n) for n, r in enumerate(rows[1:], 1) if len(r) != len(design.PURPOSES_COLUMNS)]
    if bad:
        raise Stop(1, [f"{label}: 列の数が見出しと違う行がある（空行を除いて {'・'.join(bad)} 行目）。提案書の材料にできない"])
    return rows[1:]


def purposes_section(rows: list[list[str]]) -> list[str]:
    """提案書の「目的と成功の判定」の節。種類は id の接頭辞から（決まらない id は `—`）。行は表の順のまま、どれも落とさない。"""
    kinds = [next((kind for prefix, kind in design.PURPOSE_KINDS.items() if r[0].strip().startswith(prefix)), "—") for r in rows]
    out = ["## 目的と成功の判定", "",
           f"承認したタグの時点の目的の表（`{design.PURPOSES}`。v1 から重ねた全体）から生成した。"
           "指標の「機能」は、その指標を動かす機能の id（`なし` はシステムの機能では動かさない指標）。", ""]
    columns = design.PURPOSES_COLUMNS
    out += table([columns[0], "種類"] + columns[1:], [[r[0], kind] + r[1:] for r, kind in zip(rows, kinds)])
    out.append("")
    return out


def compose(title: str, info: dict, hand: list[tuple[str, str]], qa_rows: list[dict[str, str]],
            schedule: list[dict[str, str]], estimate: list[dict[str, str]], diff=None,
            purposes: list[list[str]] | None = None) -> str:
    version = info["version"]
    out = [f"# {title}", ""]
    out.append(f"> この提案書は生成物です。生成元: `{info['req']}`（`{info['req_commit']}`）・"
               f"`{info['budget']}`（`{info['budget_commit']}`）の時点の `{in_version(version, 'shared/')}`・"
               f"`{in_version(version, 'feasibility/')}` と、"
               f"`{in_version(version, HAND_DIR)}/` の手書き部分。**決裁者の承認の記録ではありません。**")
    out += [">", f"> 何を作るかは、同じ場所の仕様書（[{SPEC_NAME}]({SPEC_NAME})）を見る。", ""]
    for _, body in hand:
        out += [body.rstrip("\n"), ""]
    if purposes is not None:
        out += purposes_section(purposes)
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
    """手書き部分（`directory` 直下の `*.md`、ファイル名の順）。作業ツリーから読む。

    **書いた綴りのとおりに探す**（`check-qa-csv.py` の `misspelled`。#514）——区別しない FS では `docs/v2/proposal` が
    `docs/v2/Proposal` を開いてしまい、区別する FS と答えが食い違う。綴りだけ違う名前なら名指しして 2。"""
    problem = qa.misspelled(directory)
    if problem:
        raise Stop(2, [f"{problem}。中身を検査していない"])
    hand = []
    for path in sorted(directory.glob("*.md")) if directory.is_dir() else []:
        try:
            hand.append((path.name, path.read_text(encoding="utf-8-sig")))
        except OSError as e:  # 権限などを「UTF-8 として読めない」「git を起動できない」と言わない（#286）
            raise Stop(2, [f"{path}: 手書き部分を読めない（{e.strerror}）。中身を検査していない"])
        except UnicodeDecodeError:
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


def figures_of(whole) -> tuple[list[str], list[str], list[str]]:
    """(載せる図——`.svg`、書き出しが無いので載せないソース——`.drawio`・`.bpmn`、
    載せるが書き出しが今のソースと合わない図——「`<書き出し>`（理由）」)。どれもパスの順。図は `spec/`・`requirements/` の中だけ。

    鮮度は `render-diagrams.py` の印で見る——ソース `X.drawio`・`X.bpmn` の書き出し `X.svg`（大文字小文字を区別しない）の印が無いか、
    印の指紋がソースのバイトの sha256 と違う。**ソースのバイトは承認のタグの blob で、`render-diagrams.py` は作業ツリーのバイトで印を書く**ので、
    改行の変換（`core.autocrlf`・`.gitattributes` の `eol`）で作業ツリーが CRLF になっても合うよう、LF と CRLF の両方の形の指紋を許す。
    `X.drawio.svg` は drawio の書き出し（編集できる SVG）と数えるが `render-diagrams.py` の書き出しではないので鮮度を見ない。
    `X.bpmn.svg` は BPMN の書き出しと数えず、隣に `X.bpmn` があれば図としても載せない（BPMN にその形は無い——手で作った書き出しなので、
    `X.bpmn` を「載せていない」と名指しするだけにし、載せつつ載せていないと言う矛盾を作らない。`X.bpmn` の無い `X.bpmn.svg` はふつうの図として載る）。
    ソースの消えた印つきの `.svg`（`render-diagrams.py --check` の「ソースが無い」）は見ない。"""
    paths = sorted(p for p in whole.files if p.startswith(FIGURE_DIRS) and not signoff.versions.is_formal(p))
    bpmn_sources = {p.lower() for p in paths if p.lower().endswith(".bpmn")}
    svgs = [p for p in paths if p.lower().endswith(".svg") and not (p.lower().endswith(".bpmn.svg") and p[:-4].lower() in bpmn_sources)]
    by_lower = {p.lower(): p for p in svgs}
    missing: list[str] = []
    stale: list[str] = []
    for p in paths:
        suffix = next((s for s in diagrams.SUFFIXES if p.lower().endswith(s)), None)
        if suffix is None:
            continue
        out = by_lower.get(f"{p[:-len(suffix)]}.svg".lower())
        if out is None:
            # 隣にソースのある `X.bpmn.svg` は `svgs` に無いので、ここで数えるのは `X.drawio.svg` だけ
            if f"{p}.svg".lower() not in by_lower:
                missing.append(p)
            continue
        got = diagrams.marked_digest(whole.files[out])
        if got is None:
            stale.append(f"`{out}`（印が無い——`render-diagrams.py` で書き出していない）")
        elif got not in eol_digests(whole.files[p]):
            stale.append(f"`{out}`（古い——ソース `{p}` を直したあと書き出していない）")
    return svgs, missing, stale


def eol_digests(data: bytes) -> set[str]:
    """ソースの指紋（`render-diagrams.py` の式）を、改行を LF にした形と CRLF にした形の両方で。"""
    lf = data.replace(b"\r\n", b"\n")
    return {diagrams.source_digest(form) for form in (data, lf, lf.replace(b"\n", b"\r\n"))}


def compose_spec(title: str, info: dict, hand: list[tuple[str, str]], whole, diff,
                 proposal_name: str) -> tuple[str, dict[str, bytes], dict]:
    """(仕様書, 図のファイル名 → 中身, `--pptx` の材料) を返す。材料は req のタグの時点の重ねた全体と、仕様書の手書き部分。"""
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

    # 形式検査のモデル（`spec/formal/`）は仕様から書き起こした写しなので、規模にも一覧にも入れない（#908）
    files = sorted(p for p in whole.files if not signoff.versions.is_formal(p))
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
    svgs, missing, stale = figures_of(whole)
    out += ["## 規模", ""]
    scale_rows = [
        ["要求のファイル（`requirements/`）", str(sum(1 for p in files if p.startswith("requirements/")))],
        ["仕様のファイル（`spec/`。中間表現・内部の Q&A 表・形式検査のモデルを除く）", str(sum(1 for p in files if p.startswith("spec/")))],
        ["決定表の行（見出しを除く）", str(len(decision_rows) - 1) if decision_rows else "—（決定表が無い）"],
        ["Q&A（共有。v1 から重ねた全体）",
         f"{len(shared_rows)}（決定 {decided}・暫定 {provisional}・未決定 {len(shared_rows) - decided - provisional}）"],
        ["機能（中間表現）", str(len(whole.features)) if whole.spec is not None else "—（中間表現が無い）"],
        ["図", f"{len(svgs)}（書き出しが無いので載せていない図 {len(missing)}・書き出しが今のソースと合わない図 {len(stale)}）"],
    ]
    out += table(["もの", "数"], scale_rows)
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
    if stale:
        out += ["書き出しが今のソースと合わない図（仕様書（`spec.md`）の図には載せている。`render-diagrams.py --check` で確かめ、書き出し直して承認を取り直す）:", ""]
        out += [f"- {line}" for line in stale] + [""]

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
    # `--pptx` の既定のデザインが読む材料（#1289）。Markdown と同じ値から作る
    material = {
        "title": title, "version": version, "hand": hand, "scale": scale_rows,
        "figures": [(path, whole.files[path]) for path in svgs],
        "features": [(fid, str(f.get("title", ""))) for fid, f in whole.features.items()],
        "decision": padded if decision_rows else None, "missing": missing, "stale": stale,
        "out_of_scope": body, "files": listed,
        "changes": changes_material(diff, info["req"]) if diff is not None else None,
    }
    return "\n".join(out), figures, material


def infra_gate(files: dict[str, bytes], tag: str) -> None:
    """基盤要件のゲート（#950。決まりの正は `references/tree.md` の「基盤要件」の「ゲート」）。`files` は `tag` の時点の重ねた全体。
    形式の違反・未決定は Stop(1)、暫定は Stop(3)、読めなければ Stop(2)。表が無ければ止めずに標準エラーで知らせる。"""
    report = infra.inspect_files(files)
    if report.missing:
        print(f"{tag}: 基盤要件の表（{infra.INFRA}）が無い——{'・'.join(infra.REQUIRED_ITEMS)}が決まっていないまま提案書を作る"
              "（決めるなら feasibility で推奨付きの質問を起票して表を作る。references/tree.md の「基盤要件」）", file=sys.stderr)
        return
    code = report.code()
    if code:
        raise Stop({2: 2, 4: 3}.get(code, 1), [f"{tag}: {line.strip()}" if line.startswith("  ") else line for line in report.lines()]
                   + ["関門（基盤要件。references/tree.md の「基盤要件」の「ゲート」）を通らない"])


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
    whole, diff, rendered = compare_at(top, info["req_commit"], info["req"], info["version"])
    infra_gate(rendered, info["req"])
    purposes = read_purposes(whole.files, info["req"])
    hand_dir = top / in_version(info["version"], HAND_DIR)
    hand = read_hand(hand_dir)
    if not hand:
        raise Stop(1, [f"{hand_dir}: 手書き部分（*.md）が無い。背景と目的・推奨案・代替案・リスクを書いてから作る"])
    text = compose(args.title, info, hand, qa_rows, schedule, estimate, diff, purposes)
    spec_text, figures, spec_material = compose_spec(args.spec_title, info,
                                                     read_hand(top / in_version(info["version"], SPEC_HAND_DIR)), whole, diff, out.name)
    outputs = {out: text.encode("utf-8"), out.parent / GANTT_NAME: gantt.render(schedule).encode("utf-8"),
               out.parent / SPEC_NAME: spec_text.encode("utf-8")}
    outputs.update({out.parent / name: content for name, content in figures.items()})
    if args.pptx:
        appendix = not args.no_appendix and bool(qa_rows)
        if appendix:
            outputs[out.parent / DECISIONS_NAME] = ppt.decisions_xlsx(qa_rows)
        if args.pptx_script is not None:
            proposal_pptx, spec_pptx = run_pptx_script(args.pptx_script, {path.name: content for path, content in outputs.items()
                                                                            if isinstance(content, bytes)})
        else:
            lead = "この版の Q&A で" if diff is not None else ""
            ctx = {"title": args.title, "version": info["version"], "hand": hand, "qa": qa_rows, "estimate": estimate,
                   "schedule": schedule, "changes": changes_material(diff, info["req"]) if diff is not None else None,
                   "purposes": purposes, "purpose_kinds": [next((kind for prefix, kind in design.PURPOSE_KINDS.items()
                                                                if r[0].strip().startswith(prefix)), "—") for r in purposes or []],
                   "provisional_lead": lead}
            opts = pptx_options(args)
            proposal_pptx, _ = ppt.proposal_deck(ctx, feasibility.CATEGORIES, opts, out.name)
            spec_pptx, failed = ppt.spec_deck(spec_material, opts)
            if failed:  # 図を PNG にできなかった——載せていないことを隠さない（終了コードは 0 のまま）
                print(f"図 {len(failed)} 枚を仕様書の PPTX に載せていない: SVG を PNG にする道具（rsvg-convert。"
                      f"環境変数 {ppt.SPEC_RSVG_ENV} で差し替え）が無いか、変換に失敗した", file=sys.stderr)
        outputs[out.with_suffix(".pptx")] = proposal_pptx
        outputs[out.parent / SPEC_PPTX_NAME] = spec_pptx
    return outputs


def pptx_options(args) -> "ppt.Options":
    """正本の `CLAUDE.md` の指示から渡された引数を、既定のデザインの設定にする（#1289）。"""
    numbers = None if args.scope_questions is None else [n.strip() for n in args.scope_questions.split(",") if n.strip()]
    overview = ppt.OVERVIEW_ITEMS if args.overview is None else tuple(i.strip() for i in args.overview.split(",") if i.strip())
    return ppt.Options(appendix=not args.no_appendix, scope_slide=not args.no_scope_slide, scope_questions=numbers,
                       scope_match=args.scope_match, overview=overview, strip=[re.compile(p) for p in args.slide_strip])


def run_pptx_script(script: Path, materials: dict[str, bytes]) -> tuple[list | bytes, list | bytes]:
    """プロジェクトの PPTX 生成スクリプトに差し替える（`--pptx-script`。#1289）。材料は `build-proposal.py` の出力だけで、
    一時ディレクトリに同じ名前で置いて渡す——スクリプトは中身を足さない・変えない（出力は 2 本の PPTX だけ）。
    `python3 <script> --materials <dir> --proposal-out <p.pptx> --spec-out <s.pptx>`。0 でない・2 本が揃わない・タイムアウトは Stop(2)。"""
    if not script.is_file():
        raise Stop(2, [f"{script}: --pptx-script のスクリプトが無い（ファイルでない）。PPTX を作れない"])
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "materials").mkdir()
        for name, content in materials.items():
            (base / "materials" / name).write_bytes(content)
        targets = (base / "proposal.pptx", base / "spec.pptx")
        try:
            done = subprocess.run([sys.executable, str(script), "--materials", str(base / "materials"),
                                   "--proposal-out", str(targets[0]), "--spec-out", str(targets[1])],
                                  capture_output=True, text=True, timeout=SCRIPT_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise Stop(2, [f"{script}: {SCRIPT_TIMEOUT} 秒で終わらなかった。PPTX を作れない"])
        except OSError as e:
            raise Stop(2, [f"{script}: 起動できない（{e.strerror}）。PPTX を作れない"])
        if done.returncode != 0:
            tail = [line for line in (done.stderr or done.stdout).splitlines() if line.strip()][-5:]
            raise Stop(2, [f"{script}: 終了コード {done.returncode}。PPTX を作れない", *tail])
        missing = [t.name for t in targets if not t.is_file()]
        if missing:
            raise Stop(2, [f"{script}: 出力が揃っていない（{'・'.join(missing)} が無い）。PPTX を作れない"])
        blobs = tuple(t.read_bytes() for t in targets)
    bad = [name for name, blob in zip(("proposal.pptx", "spec.pptx"), blobs) if not blob.startswith(b"PK")]
    if bad:
        raise Stop(2, [f"{script}: {'・'.join(bad)} が zip（PPTX）として読めない。PPTX を作れない"])
    return blobs


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


def is_dir(path: Path) -> bool:
    """辿れない親の下でも例外を投げない `is_dir`（python3.12 の `pathlib` は `PermissionError` を投げる）。"""
    try:
        return path.is_dir()
    except OSError:
        return False


def owned_names(directory: Path) -> list[str] | None:
    """印が名指しする、前回この道具が書いた出力の名前。印が無ければ空——消してよいと確かめられるものが無い。
    印が在るか・何を名指しするかを読めなければ None（印を消さずに残す）。**普通のファイルでない印（ディレクトリ・symlink——
    辿れても辿れなくても）も読めない印である**（#512）——この道具は印を普通のファイルとして書くので、別の形の印は書いたものと確かめられず、
    書けば symlink の先（出力の場所の外）に書く。"""
    manifest = directory / MANIFEST
    try:
        try:
            mode = manifest.lstat().st_mode  # symlink を辿らない
        except (FileNotFoundError, NotADirectoryError):
            return []
        if not stat.S_ISREG(mode):
            return None
        lines = manifest.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    # 同じ場所の素の名前だけ（印を書き換えられても、外のファイルや印そのものは消さない）
    return [name for name in (line.strip() for line in lines)
            if name and not name.startswith("#") and "/" not in name and "\\" not in name
            and name not in (".", "..", MANIFEST)]


def remove_owned(directory: Path) -> list[str]:
    """印に載る出力と印を消し、消せなかったものを（理由つきで）返す。載っていないもの（手書きのファイル）は、名前が出力と同じでも消さない。
    読めない印は消さない——消すと、名指ししていた出力がこの道具のものだった跡が無くなる。
    消せなかった出力があれば印も残す（#440）——次の実行が、残った出力をこの道具のものと確かめて消せるように。
    **symlink は、先が在れば（辿れなくても）リンクも先も消さず、リンクと先のパスを消せなかったものとして返す**（#512。
    `schedule-to-gantt.py` の #626 と同じ）——リンクを消しても先の古い中身は残るので、「消した」と言えば古い中身を今のものと取り違える。
    先のパスは鎖を解いた先（辿れないときは辿れたところまで）。壊れたリンク（先が無い・輪・長すぎる名前——判定は `schedule-to-gantt.py` の `absent`）は消す
    ——残る古い中身が無い。鎖が長すぎて辿れない（ELOOP）だけで先に実物があるものは消さない。**ディレクトリを指すリンクも消さずに名指しする**
    （`schedule-to-gantt.py` は名指ししない——こちらは印が名指しする名前なので、黙って残すと次に同じ名前を書くときに「上書きしない」で止まる）。"""
    names = owned_names(directory)
    if names is None:
        return []
    left = []
    for name in names:
        stale = directory / name
        try:
            # symlink を先に見る——python3.12 の `is_file` は辿れない先を指す symlink で例外を投げる
            if stale.is_symlink():
                target = os.path.realpath(stale)  # 非 strict——辿れなくても例外を出さず、辿れたところまで解く
                try:
                    mode = stale.stat().st_mode
                except OSError as e:
                    # 鎖が OS の上限より長いだけ（ELOOP）でも、鎖を解いた先に実物があれば古い中身が残る（#512 の 2 パス目 CR2-1）
                    real = os.path.lexists(target) and not os.path.islink(target)
                    if real or not gantt.absent(Path(target), e):
                        reason = "リンクの鎖が長すぎる" if real else f"リンクの先を辿れない: {e.strerror}"
                        left.append(f"{stale}（{reason}。先: {target}）")
                        continue
                    # 壊れたリンク（先が無い・輪・長すぎる名前——判定は `schedule-to-gantt.py` の `absent` を使う）——消す
                else:
                    if stat.S_ISDIR(mode):
                        left.append(f"{stale}（リンクの先がディレクトリ——この道具の出力ではないので消さない。先: {target}）")
                    else:
                        left.append(f"{stale}（リンクの先に前の出力が残る——リンクを消しても先は消えない。先: {target}）")
                    continue
            elif not stale.is_file():
                continue
            stale.unlink()
            print(f"{stale}: 前に作った出力を消した", file=sys.stderr)
        except OSError as e:
            left.append(f"{stale}（{e.strerror}）")
    manifest = directory / MANIFEST
    if not left:
        try:
            if manifest.is_file():
                manifest.unlink()
        except OSError as e:
            left.append(f"{manifest}（{e.strerror}）")
    return left


def left_lines(left: list[str]) -> list[str]:
    return [f"前に作った出力を消せない: {name}" for name in left]


def output_named(name: str, out_name: str) -> bool:
    """この道具の出力の名前か（大文字小文字を区別しない）。PPTX は提案書（`--out` の名前・`proposal.md`）と仕様書のものだけで、
    `--pptx` の有無に依らない——前の出力は今回の引数と関係が無い。図は `spec-figure-<数字>.svg` だけ。"""
    proposals = {n for n in (out_name, Path(DEFAULT_OUT).name) if n not in ("", ".", "..")}
    names = proposals | {str(Path(n).with_suffix(".pptx")) for n in proposals} | {GANTT_NAME, SPEC_NAME, SPEC_PPTX_NAME, DECISIONS_NAME}
    lower = name.lower()
    return lower in {n.lower() for n in names} or re.fullmatch(re.escape(FIGURE_PREFIX) + r"[0-9]+\.svg", lower) is not None


def unreadable_manifest(directory: Path) -> bool:
    """在るのに読めない印か（#512）。作れたあと、書く前に見る（作れない経路は今までどおりその終了コードで止まる）——書けば読めない印を黙って書き換え（UTF-8 で読めない印）、
    symlink の印なら先（出力の場所の外）に書く。"""
    return owned_names(directory) is None


def same_entry(a: Path, b: Path) -> bool:
    """同じディレクトリの同じ項目か（#551）。名前が同じか、大文字小文字だけ違い同じファイル（区別しない FS の同じ項目）なら同じ。
    **ファイルの同一性（inode）だけでは見ない**——ハードリンクは別の名前の別の項目で、それぞれ名指しする。
    大文字小文字を区別する FS で綴りだけ違う 2 つのファイルは inode が違うので、別の項目として名指しする。"""
    if os.path.normcase(os.path.abspath(a.parent)) != os.path.normcase(os.path.abspath(b.parent)):
        return False
    if a.name == b.name:
        return True
    if a.name.lower() != b.name.lower():
        return False
    try:
        sa, sb = a.lstat(), b.lstat()  # symlink を辿らない
    except OSError:
        return False
    return (sa.st_dev, sa.st_ino) == (sb.st_dev, sb.st_ino)


def leftover_lines(out: Path, named: tuple[Path, ...] = ()) -> list[str]:
    """出力の場所に残った、今回の出力ではないファイルを名指しする行（作れなかったとき——#498。作れたとき——#553）。何も消さない。

    名指しするのは、出力の名前のファイルのうち読める印に無いもの（spec-loop 0.25.0 までの出力・手で置いたもの）と、
    読めない印とその場所の出力の名前のファイル。印が名指しするのに消せなかった出力は `left_lines` が名指しするので数えない。
    `named` は、ほかの行（「上書きしない」）がもう名指ししたファイルで、2 度は名指ししない（#551）。"""
    directories = [out.parent]
    if is_dir(out) and out.resolve() != out.parent.resolve():
        directories.append(out)  # ディレクトリを渡したなら、その中も（`main` が消す場所と同じ）
    lines = []
    for directory in directories:
        try:
            entries = sorted(directory.iterdir())
        except (FileNotFoundError, NotADirectoryError):
            continue  # 場所が無い——残っているものも無い
        except OSError as e:
            lines.append(f"{directory}: 前の出力が残っているかを確かめられない（{e.strerror}）")
            continue
        owned = owned_names(directory)
        if owned is None:
            lines.append(f"{directory / MANIFEST}: 印を読めない——この場所の前の出力は消していない（この道具が作ったものか確かめられない）")
        for path in entries:
            try:
                regular = path.is_symlink() or stat.S_ISREG(path.stat().st_mode)
            except OSError:
                regular = True  # 確かめられないものも名指しする（消さないので害が無い）
            if not regular or path.name == MANIFEST or not output_named(path.name, out.name):
                continue
            if any(same_entry(path, other) for other in named):
                continue
            if owned is None:
                lines.append(f"{path}: 今回の出力ではない（印が読めない。消していない）")
            elif path.name not in owned:
                lines.append(f"{path}: 今回の出力ではない（印 {MANIFEST} に無い——spec-loop 0.25.0 までの出力か手で置いたもの。消していない）")
    return lines


def bad_out(out: Path) -> str | None:
    """出力先の誤り。消す前・作る前に見る（`with_suffix` は名前が空だと例外を投げるので、名前を先に見る）。"""
    if out.name in ("", ".", ".."):
        return f"{out}: 出力先にファイルの名前が無い（`--out` には `<ディレクトリ>/proposal.md` の形で渡す）"
    # 印は 1 行 1 名前で、読むときに前後の空白を落とし `#` の行を飛ばす——そう読み違える名前は印に残せない
    if out.name != out.name.strip() or len(out.name.splitlines()) != 1 or out.name.startswith("#"):
        return f"{out}: 出力の名前の前後に空白があるか、改行を含むか、`#` で始まる（印 {MANIFEST} に名前として残せない）"
    # 印を読む側は `\` を含む名前を捨てる。印は UTF-8 で書く——どちらも印に残せない
    if "\\" in out.name:
        return f"{out}: 出力の名前が `\\` を含む（印 {MANIFEST} に名前として残せない）"
    try:
        out.name.encode("utf-8")
    except UnicodeEncodeError:
        return f"{out}: 出力の名前が UTF-8 で書けない（印 {MANIFEST} に名前として残せない）"
    try:
        is_directory = stat.S_ISDIR(out.stat().st_mode)
    except (FileNotFoundError, NotADirectoryError):
        is_directory = False  # 無い・親が普通のファイル——後者は書くときに 2
    except OSError as e:
        return f"{out}: 出力先を確かめられない（{e.strerror}）"
    if is_directory:
        return f"{out}: 出力先がディレクトリ（`--out` には `<ディレクトリ>/proposal.md` の形で渡す）"
    # 大文字小文字だけ違う名前も重なる（区別しない FS では同じファイル）。`spec.html` なら PPTX が仕様書の PPTX と重なる
    reserved = {name.lower() for name in (SPEC_NAME, GANTT_NAME, SPEC_PPTX_NAME, DECISIONS_NAME, MANIFEST)}
    if ({out.name.lower(), out.with_suffix(".pptx").name.lower()} & reserved or out.suffix.lower() == ".pptx"
            or out.name.lower().startswith(FIGURE_PREFIX)):
        return f"{out}: 仕様書・ガントチャート・PPTX・別紙・図・印と同じ名前になる"
    return None


def write_outputs(outputs: dict[Path, bytes | list], directory: Path) -> None:
    """印を先に書いてから出力を書く——途中で失敗しても、書きかけは印に載っているので次の実行で消える。"""
    for path in outputs:
        if path.exists() or path.is_symlink():
            raise Stop(2, [f"{path}: 前にこの道具が作った出力か確かめられない（印 {directory / MANIFEST} に無い）。上書きしない",
                           "手で置いたものでなければ（spec-loop 0.25.0 までが作った出力など）、消してから作り直す"], (path,))
    try:
        directory.mkdir(parents=True, exist_ok=True)  # 親が普通のファイルでも traceback にしない
        (directory / MANIFEST).write_text("\n".join([MANIFEST_HEAD, *sorted(p.name for p in outputs)]) + "\n", encoding="utf-8")
        for path, content in outputs.items():
            if isinstance(content, list):
                pptx.write(content, path)
            else:
                path.write_bytes(content)
    except Exception as e:  # 想定外の例外でも書きかけを残さない（#286）。印に載っているので消せる
        reason = (f"{e.filename or directory}: 出力を書けない（{e.strerror}）" if isinstance(e, OSError)
                  else f"{directory}: 書いている途中に想定外の例外（{type(e).__name__}: {e}）")
        left = remove_owned(directory)
        if left:
            raise Stop(2, [f"{reason}。書きかけを消せなかった", *left_lines(left)])
        raise Stop(2, [f"{reason}。書きかけを消した"])


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--repo", default=".", type=Path)
    parser.add_argument("--version", type=signoff.positive)
    parser.add_argument("--req")
    parser.add_argument("--budget")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title", default="提案書")
    parser.add_argument("--spec-title", default="仕様書")
    parser.add_argument("--pptx", action="store_true", help="提案書と仕様書の PPTX も作る")
    # 以下は `--pptx` の既定のデザインを正本の `CLAUDE.md` の指示で変える引数（#1289。proposal のスキルが組んで渡す）
    parser.add_argument("--pptx-script", type=Path, help="PPTX の生成を、このプロジェクトのスクリプトに差し替える")
    parser.add_argument("--no-appendix", action="store_true", help="別紙の表（decisions.xlsx）を作らない")
    parser.add_argument("--no-scope-slide", action="store_true", help="範囲を決めた質問の 1 枚を載せない")
    parser.add_argument("--scope-questions", help="範囲を決めた質問の番号（コンマ区切り。渡した順に載せる）")
    parser.add_argument("--scope-match", help="範囲を決めた質問を、質問の文から選ぶ正規表現")
    parser.add_argument("--overview", help="概要の 1 枚に載せるもの（counts・recommend・origin・theme のコンマ区切り）")
    parser.add_argument("--slide-strip", action="append", default=[], help="スライドから外す参照の形（正規表現。何度でも書ける）")
    args = parser.parse_args(argv)
    custom = (args.pptx_script is not None, args.no_appendix, args.no_scope_slide, args.scope_questions is not None,
              args.scope_match is not None, args.overview is not None, bool(args.slide_strip))
    if any(custom) and not args.pptx:
        parser.error("--pptx-script・--no-appendix・--no-scope-slide・--scope-questions・--scope-match・--overview・--slide-strip は --pptx と一緒に渡す")
    if args.scope_questions is not None and not [n for n in args.scope_questions.split(",") if n.strip()]:
        parser.error("--scope-questions に番号が無い（範囲の 1 枚を載せないなら --no-scope-slide）")
    if args.overview is not None and not set(i.strip() for i in args.overview.split(",") if i.strip()) <= set(ppt.OVERVIEW_ITEMS):
        parser.error(f"--overview は {'・'.join(ppt.OVERVIEW_ITEMS)} のコンマ区切り")
    for pattern in [args.scope_match, *args.slide_strip]:
        if pattern is not None:
            try:
                re.compile(pattern)
            except re.error as e:
                parser.error(f"正規表現として読めない: {pattern}（{e}）")

    # git を起動できなくても、古い出力は消してから 2 で終わる（ここで落ちると古い提案書が残る）
    out = args.out if args.out else repo_top(args.repo) / DEFAULT_OUT
    # 引数の誤りは消す前に見る。誤りで止まっても、印が名指しする前の出力は消す（残すと今回のものと取り違える。#398）
    problem = bad_out(out)
    left = remove_owned(out.parent)
    if is_dir(out) and out.resolve() != out.parent.resolve():
        left += remove_owned(out)  # ディレクトリを渡したなら、指したつもりの場所の前の出力も消す
    if left:  # 消せない場所には書けもしない。残ったものを今回のものと取り違えないよう名指しする（#440）
        for line in left_lines(left) + ([problem] if problem else []) + leftover_lines(out):
            print(line, file=sys.stderr)
        print("提案書は作っていない", file=sys.stderr)
        return 2
    if problem:
        for line in leftover_lines(out):  # 印に無い前の出力も、今回のものと取り違えないよう名指しする（#498）
            print(line, file=sys.stderr)
        print(f"{problem}。提案書は作っていない", file=sys.stderr)
        return 2

    try:
        try:
            outputs = build(args, out)
        except signoff.Unjudged as e:
            raise Stop(2, [str(e)])
        except OSError as e:  # git の起動（`run_git`）と手書き部分（`read_hand`）は先に捕まえる。残るのは一時ファイルの読み書き
            raise Stop(2, [f"{e.filename or '（パス不明）'}: 読み書きできない（{e.strerror}）。提案書の材料を読み終えていない"])
        if unreadable_manifest(out.parent):  # 読めない印は書き換えない・symlink の印の先に書かない（#512）。名指しは `leftover_lines` が言う
            raise Stop(2, [f"{out.parent / MANIFEST}: 読めない印は書き換えない（印は手で直さない——印と、名指しされた出力が前にこの道具が作ったものかを人間に確かめてから消して作り直すか、別の --out を渡す）"])
        write_outputs(outputs, out.parent)
    except Stop as stop:
        for line in stop.lines + leftover_lines(out, stop.named):
            print(line, file=sys.stderr)
        print("提案書は作っていない", file=sys.stderr)
        return stop.code
    except Exception:  # 想定外の例外も、残った前の出力を名指ししてから外側の 2 に渡す（#286・#498）
        for line in leftover_lines(out):
            print(line, file=sys.stderr)
        raise
    print(f"{out}: 提案書を書いた（同じ場所に {'・'.join(p.name for p in outputs if p != out)}）")
    # 作れたときも、印に無い前の出力が残っていれば名指しする（#553）。終了コードは 0 のまま——書いたものは今回の出力である
    for line in leftover_lines(out):
        print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
