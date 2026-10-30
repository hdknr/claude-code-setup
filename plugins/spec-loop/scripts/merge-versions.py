#!/usr/bin/env python3
"""版ごとのディレクトリ（`docs/v1/`・`docs/v2/`…）を重ね合わせて、ある版の時点の全体を作る。

usage: python3 merge-versions.py <docs ディレクトリ> <出力先ディレクトリ> [--upto <n>]

**決まりの正は `references/versions.md` である**（このプラグインの中にある）。
下の定数（版の名前・重ねる置き場所・`removed.csv` の列と種類・ファイルとしては消せないもの・出力先の印）はその写しで、
**写しがずれていないかは、このリポジトリの `scripts/test-merge-versions.py` が `references/versions.md` と突き合わせて見る**。

- v1 に v2、…、v<n> の差分を順に重ねる。`--upto` を省けば、番号が最大の版（作業中の版）まで。
- 出力は版に分ける前の `docs/` と同じ形（`shared/`・`requirements/`・`spec/`）。
- **同じ入力から同じバイトを作る**——時刻を使わず、行・機能は前の版の順、ファイルはパスの順。
- 各版の `qa.csv`（と内部の `spec/qa-dev.csv`）は同梱の `check-qa-csv.py` で検査する（**列の決まりを写さない**）。
  内部の表も共有の表と同じく行（`No`）で重ねる。`removed.csv` の `Q&A` は、番号（`Q-`／`D-`）で消す表が決まる。
- 標準ライブラリだけを使う。

終了コード:

- 0: 書いた
- 1: 入力が決まりに反する（重ねた結果が書けない形になる・UTF-8 で書けない文字を含む、も含む）——**書かない。前に作った出力があれば消す**（問題は 1 件で止めず、
  最初に問題のあった版の中は全部出す。それより後の版は前の版の全体に依るので見ない）
- 2: 引数の誤り・入力が無い／読めない・出力先に書けない・**`docs` が git の作業ツリーの中なのに git が失敗した・
  git を走らせられないのに `docs` の上に `.git` が在る**（綴りを index と照合できない。#276・#572）・想定外の例外（巨大なセルの `csv.Error`・深い入れ子の
  `RecursionError` など。#286）——**書かない**（書いている途中なら書きかけを消す）。
  **入力が無い・読めないときは**（重ねている途中の想定外の例外を含む）、出力先が印の在るディレクトリなら前の出力を消す。
  **出力先そのものを断ったとき**（印の無い空でない場所・シンボリックリンク・`docs/` の中・`docs/` を含む場所）は**消さない**

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **新しいつもりで前の版の番号を書いた** | 同じ番号は「変更」の意味と決めている。意図は機械で分からない |
| **重ね合わせた `spec_ir.json` の中身の決まり** | `spec-ir.md` の決まりは `scaffold.py` が全体に当てる |
| **凍結した版が直されていないか** | `release-v<n>` のタグとの照合で、タグが要る（このスクリプトが git を使うのは、名前の綴りを index と照合するときだけ） |
| **フックの外から、`docs` の属さないリポジトリを指す `GIT_INDEX_FILE` を渡す** | `GIT_INDEX_FILE` は読む（フックの一時の index がコミットされる綴りを持つため。相対なら `docs` が属するリポジトリの根から。#570）。別のリポジトリの index を指していれば、その名前で照合する |
| **作業ツリーの中なのに `git rev-parse --is-inside-work-tree` が失敗する形**（dubious ownership・壊れた `gitdir:` を持つ `.git`） | 失敗の理由は読み分けず（git のメッセージは版と言語で変わる）外と読む——作業ツリーの綴りで読むので、区別しない FS で作業ツリーのフォルダの綴りがコミットと違えば、タグと答えが食い違いうる（#572） |
| **git を走らせられない環境の `docs` の上の `.git`** | 中か外かを git で決められないので、上へ辿って `.git` が在れば 2（関係のない `.git` でも） |
| **index に綴りの違う 2 つが在るフォルダの、追跡していないファイル** | 区別しない FS ではどちらの綴りのフォルダにも見えるので、両方の綴りで数えて 1（重ねた結果で綴りだけ違うパス）になる。タグには写らないので、タグを読む側には現れない |
| **index に在る名前を作業ツリーで綴りだけ変えて、まだ `git add` していない** | 区別しない FS では git もそれを変更と見ない（`git status` が空）ので、index の綴りで読む。区別する FS では別の名前（`git status` に出る）なので作業ツリーの綴りで読む——同じコミットの答えは揃う |
| **大文字小文字を区別しないファイルシステムでの版名 `V2`** | `v` の次が数字の名前だけを版と読むので、`V2/` は版でない名前として読まない |

**名前は git が見る綴りで読む**（#276・#569）——`removed.csv`・置き場所（`shared/` など）をパスを組み立てて開くと、
大文字小文字を区別しないファイルシステムでだけ `Removed.csv`・`Shared/` が開けてしまい、タグから写して重ねる
`build-proposal.py` や区別するファイルシステムと答えが食い違う。**版の直下の置き場所・`removed.csv` と、置き場所の中の構造ファイル
（`shared/qa.csv`・`spec/qa-dev.csv`・`spec/spec_ir.json`）について、綴りだけ違う名前（大文字小文字・Unicode の正規化）は
決まりに反する（1）として名指しし、中身は読まない**（構造ファイルは #511——重ねた出力を決まった名前で開く `check-spec-exit.py`・
`scaffold.py` が、区別しない FS でだけ `shared/QA.csv` を Q&A 表として開くため）。

- **綴りは `spelled` が決める。** 区別しない FS では、作業ツリーのフォルダの綴り（`iterdir`）がコミットの綴りと食い違いうる
  ——git は既に在るフォルダに書き込むので、古い `Requirements/` が（追跡しない `.DS_Store` などで）残っていると、
  `requirements/` のファイルもそこに書かれる。だから `docs` が git の作業ツリーの中なら `git ls-files` をリポジトリの根からの綴りで
  1 回引き（`docs` のフォルダ自身の綴りがコミットと違っても引けるように）、**どの段の名前についても**（版のフォルダ・版の直下・
  置き場所より深いフォルダとファイル。#569）、
  **FS が index の綴りの名前と作業ツリーの名前を同じ項目として開くとき（`lstat` の dev・ino が同じで、そのフォルダに畳むと同じになる名前が
  ほかに無い——区別する FS で綴りだけ違う名前のハードリンクを並べると dev・ino は同じでも別の項目。#676）**は index の綴りを名前とする。
  区別する FS では 2 つは別の項目なので、作業ツリーの綴りのまま。
  index に無い名前（`git add` 前）と、git の外（`git rev-parse --is-inside-work-tree` が `true` を返さない。#572）は作業ツリーの綴りで読む。
- **追跡しているファイルは、自分の index のパスでだけ数える**（`owners`）——index に綴りの違う 2 つ（`Sub/a.md`・`sub/b.md`、`v2/…`・`V2/…`）が在り、
  区別しない FS で 1 つのフォルダになっていても、別の綴りで追跡しているファイルを取り込まない。タグを読む `build-proposal.py` の
  `copy_docs` はコミットの木からパスを作るので、それと揃う。**捨てるのは綴りだけ違う同じ項目だけ**（`claims`）——追跡しているファイルの
  ハードリンクを別の名前で置いた管理外のファイル（#676）と、`git add` 前のファイル（#677）は数える。**重ねた結果でフォルダの綴りだけが違うのも 1**（`collisions`。`copy_docs` と同じ判定）。
  **区別しない FS に展開した `git archive` の書き出しは綴りを失う**ので、この形の比べ相手にはならない。
- **git はリポジトリの場所を指す環境変数（`GIT_DIR`・`GIT_WORK_TREE`・`GIT_COMMON_DIR`）を外して呼ぶ**（`run_git`。#570）——
  フックの中ではこれらが相対パスで設定されていることがあり、引き継ぐと `docs` から見た別の場所を読む。**`GIT_INDEX_FILE` は外さない**
  ——部分コミットの一時の index はコミットされる綴りを持つ。相対なら、`docs` が属するリポジトリの根からのパスとして絶対パスにする。
- **綴りだけ違うディレクトリでも、読む名前（`.` で始まらない）のファイルを持たなければ数えない**（`has_content`）——
  `build-proposal.py` は `.` で始まる名前を写さないので、タグの側にもその名前は現れない。
- 綴りどおりのパスが在るかを見る `exact` は、写した一時ディレクトリから内部の層を外す `build-proposal.py` が使う。
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
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


qa = _load("check_qa_csv", "check-qa-csv.py")

VERSION = re.compile(r"v[1-9][0-9]*")
# `v` の次が数字なら版のつもりと読む（`videos/` は版ではない）
VERSION_LIKE = re.compile(r"v[0-9]")
AREAS = ["shared", "requirements", "spec"]
QA_PATH = "shared/qa.csv"
SPEC_PATH = "spec/spec_ir.json"
# 内部の層の Q&A 表（`check-qa-csv.py` の `INTERNAL_NAME`。#339）
INTERNAL_QA_PATH = "spec/" + qa.INTERNAL_NAME
REMOVED = "removed.csv"
REMOVED_COLUMNS = ["種類", "対象", "理由"]
KIND_FILE, KIND_QA, KIND_FEATURE = "ファイル", "Q&A", "機能"
KINDS = [KIND_FILE, KIND_QA, KIND_FEATURE]
STRUCTURED = [QA_PATH, INTERNAL_QA_PATH, SPEC_PATH]
MARKER = ".merged-versions"
# git を呼ぶ前に外す、リポジトリの場所を指す環境変数（`run_git`。#570）。`GIT_INDEX_FILE` は外さず絶対パスにする（`tracked`）
GIT_LOCATION = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR")
# パスの指定（`:(top,icase)`）の読み方を変える環境変数も外す——文字どおりに読まれると index が黙って空になる（#570 の 2 パス目の指摘）
GIT_PATHSPECS = ("GIT_LITERAL_PATHSPECS", "GIT_GLOB_PATHSPECS", "GIT_NOGLOB_PATHSPECS", "GIT_ICASE_PATHSPECS")
# v1 の `removed.csv` を拒否する文言（`check-signoff.py` も使う。写さない）
V1_REMOVED = "v1 には置かない（消すものが無い）"


class Unreadable(Exception):
    """入力が読めない（中身を検査していない）。"""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError as e:
        raise Unreadable(f"{path}: 読めない（{e.strerror}）") from None
    except UnicodeDecodeError:
        raise Unreadable(f"{path}: UTF-8 として読めない") from None


def find_versions(docs: Path, problems: list[str], index: set[str] | None = None) -> list[tuple[int, Path]]:
    """版のディレクトリ。名前は `spelled` の綴りで読む——区別しない FS で古い `V2/` が残っていても、index の `v2/` として読む。"""
    found = []
    for name in sorted(spelled(docs, index)):
        entry = docs / name
        if not VERSION_LIKE.match(name):
            continue
        if not VERSION.fullmatch(name):
            problems.append(f"{entry}: 版の名前の形（v<n>・先頭に 0 を付けない）に合わない")
            continue
        if not entry.is_dir() or entry.is_symlink():
            problems.append(f"{entry}: 版はディレクトリで置く（シンボリックリンク・ファイルは不可）")
            continue
        found.append((int(name[1:]), entry))
    found.sort()
    for expected, (number, entry) in enumerate(found, start=1):
        if number != expected:
            problems.append(f"{entry}: 版の番号が欠けている（v{expected} が無い）")
            break
    return found


def names(directory: Path) -> set[str]:
    """ディレクトリの中の名前を、書かれた綴りのまま（`Path.exists` は区別しないファイルシステムで綴りを無視する。#276）。"""
    try:
        return {entry.name for entry in directory.iterdir()}
    except OSError as e:
        raise Unreadable(f"{directory}: 読めない（{e.strerror}）") from None


def run_git(cwd: Path, *args: str, index_file: str | None = None) -> subprocess.CompletedProcess:
    """`git` を走らせる唯一の口。走らせられなければ `OSError`。

    **リポジトリの場所を指す環境変数（`GIT_LOCATION`）は外して渡す**（#570）——git のフックの中ではこれらが相対パスで
    設定されていることがあり、`cwd` を `docs` にして引き継ぐと `docs` から見た別の場所を読む。外せば git は `docs` から自分の
    リポジトリを見つける。パスの指定の読み方を変える変数（`GIT_PATHSPECS`）も外す。`GIT_INDEX_FILE` も外し、`index_file`
    （`tracked` が絶対パスにしたもの）があればそれだけを渡す。
    """
    env = {key: value for key, value in os.environ.items() if key not in (*GIT_LOCATION, *GIT_PATHSPECS, "GIT_INDEX_FILE")}
    if index_file is not None:
        env["GIT_INDEX_FILE"] = index_file
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, env=env)


def tracked(docs: Path) -> tuple[dict[tuple[str, ...], set[str]], set[str]] | None:
    """git の index にある、`docs` からの名前を段ごとに（`()` → `docs` の直下の綴り、`("v2",)` → 版の直下の綴り、
    `("v2", "requirements")` → その中の綴り……）と、`docs` からのパスの全部。`docs` が git の作業ツリーの外なら None。

    **外かどうかは `git rev-parse --is-inside-work-tree` で決める**（#572）——`true` を返さなければ（失敗も）外と読む。
    上へ辿って `.git` を探すと、`docs` の上にある関係のない・壊れた `.git` や、git が発見を止める境界（FS の境界・
    `GIT_CEILING_DIRECTORIES`）の向こうの `.git` で、正しい入力が 2 になる。**git を走らせられないときだけ**上へ辿り、
    `.git` が在れば `Unreadable`（2。中か外かを決められない）、無ければ外。
    中なのに git が失敗したら `Unreadable`（2。綴りを照合していない）。
    **`docs` のフォルダ自身の綴りがコミットと違ってもよい**——index はリポジトリの根からの綴り（`--full-name`）で
    大文字小文字を畳んで引き（`:(icase)`）、FS が `docs` と同じ項目として開く接頭辞のものだけを使う。
    """
    start = docs.resolve()
    try:
        inside = run_git(start, "rev-parse", "--is-inside-work-tree")
    except OSError as e:
        if any((d / ".git").exists() for d in (start, *start.parents)):
            raise Unreadable(f"{docs}: git を走らせられない（{e.strerror}）のに上に .git が在る——作業ツリーの中か決められず、"
                             "綴りを index と照合できない") from None
        return None
    if inside.returncode != 0 or inside.stdout.strip() != b"true":
        return None

    def git(*args: str, index_file: str | None = None) -> bytes:
        try:
            proc = run_git(start, *args, index_file=index_file)
        except OSError as e:
            raise Unreadable(f"{docs}: git の作業ツリーの中だが git を走らせられない（{e.strerror}）——綴りを index と照合できない") from None
        if proc.returncode != 0:
            detail = proc.stderr.decode("utf-8", "replace").strip()
            raise Unreadable(f"{docs}: git の作業ツリーの中だが git {args[0]} が失敗した（{detail}）——綴りを index と照合できない")
        return proc.stdout

    top = Path(os.fsdecode(git("rev-parse", "--show-toplevel").rstrip(b"\n")))
    rel = start.parts[len(top.parts):]
    if len(start.parts) < len(top.parts) or [fold(p) for p in start.parts[:len(top.parts)]] != [fold(p) for p in top.parts]:
        return {}, set()
    spec = [":(top,icase)" + "/".join(rel)] if rel else []
    # フックが設定した GIT_INDEX_FILE（部分コミットの一時の index など。コミットされる綴りを持つ）は読む。相対なら作業ツリーの根からの
    # パスとして絶対パスにする（#570）——フックは根で走り、git も根から解決するが、それに頼らず `docs` から呼んでも同じ index を指す
    index_file = os.environ.get("GIT_INDEX_FILE") or None
    if index_file is not None and not os.path.isabs(index_file):
        index_file = str(top / index_file)
    if index_file is not None and not os.path.isfile(index_file):
        # git は無い index を空の index と読む——黙って作業ツリーの綴りに戻ると照合が外れる（#570 の 1 パス目の指摘）
        raise Unreadable(f"{docs}: GIT_INDEX_FILE が指す index（{index_file}）が無い——綴りを index と照合できない")
    found: dict[tuple[str, ...], set[str]] = {}
    paths: set[str] = set()
    prefixes: dict[tuple[str, ...], bool] = {}
    for raw in git("ls-files", "-z", "--full-name", "--", *spec, index_file=index_file).split(b"\0"):
        if not raw:
            continue
        parts = tuple(raw.decode("utf-8", "surrogateescape").split("/"))
        head, rest = parts[:len(rel)], parts[len(rel):]
        if not rest or [fold(p) for p in head] != [fold(p) for p in rel]:
            continue
        if head not in prefixes:
            prefixes[head] = head == rel or same_entry(top.joinpath(*head), start)
        if not prefixes[head]:
            continue
        for depth in range(len(rest)):  # どの段の名前も（版の名前・版の直下・その中のフォルダとファイル。#569）
            found.setdefault(rest[:depth], set()).add(rest[depth])
        paths.add("/".join(rest))
    return found, paths


def owners(docs: Path, paths: set[str]) -> dict[tuple[int, int], set[str]]:
    """作業ツリーのファイル（`lstat` の dev・ino）→ それを追跡している index のパス（`docs` から）。

    区別しない FS では、綴りの違う 2 つのパス（`Sub/a.md`・`sub/a.md`、`v2/…`・`V2/…`）が同じファイルを開く。
    **追跡しているファイルは、自分の index のパスでだけ数える**（`walk`）——タグを読む側（`build-proposal.py` の `copy_docs`）は
    コミットの木からパスを作るので、別の綴りで追跡しているファイルを、辿っているフォルダの追跡していないファイルとして取り込まない（#569 の 2 パス目の指摘）。
    実体の番号はハードリンクでも同じなので、この表だけでは捨てない——綴りだけ違う同じ項目かは `claims` が見る（#676）。
    """
    found: dict[tuple[int, int], set[str]] = {}
    for path in paths:
        try:
            st = os.lstat(docs / path)
        except OSError:
            continue  # 作業ツリーで消した・区別する FS で綴りを変えた——そのパスで開くファイルは無い
        found.setdefault((st.st_dev, st.st_ino), set()).add(path)
    return found


def same_entry(a: Path, b: Path) -> bool:
    """2 つのパスを FS が同じ項目として開くか（区別しない FS で綴りだけ違う 2 つ）。リンクは辿らない。"""
    try:
        sa, sb = os.lstat(a), os.lstat(b)
    except OSError:
        return False
    return (sa.st_dev, sa.st_ino) == (sb.st_dev, sb.st_ino)


def spelled(root: Path, index: set[str] | None) -> set[str]:
    """ディレクトリの中の名前を、git が見る綴りで（上の docstring の「綴りは `spelled` が決める」）。`index` はその段の index の名前。"""
    entries = names(root)
    if not index:
        return entries
    result = set()
    # 畳むと同じ名前が 2 つ並ぶのは区別する FS だけ——そこでは実体が同じ（ハードリンク）でも別の項目なので寄せない（#676）
    folded = Counter(fold(name) for name in entries)
    for name in entries:
        # 自分自身も含む——index に綴りの違う 2 つが在り、区別しない FS で 1 つのフォルダになっていれば、両方の綴りが名前になる
        same = {m for m in index if fold(m) == fold(name) and folded[fold(name)] == 1 and same_entry(root / m, root / name)}
        result |= same or {name}
    return result


def has_content(directory: Path) -> bool:
    """`.` で始まらない名前を辿って、ディレクトリでない項目に届くか（読めなければ `Unreadable`）。"""
    for entry in names(directory):
        if entry.startswith("."):
            continue
        path = directory / entry
        if not path.is_dir() or path.is_symlink() or has_content(path):
            return True
    return False


def exact(root: Path, relative: str) -> Path | None:
    """`root` からの `relative`（`/` 区切り）が、書かれた綴りのとおりに在ればそのパス。無ければ・辿れなければ None。"""
    path = root
    for part in relative.split("/"):
        try:
            if part not in os.listdir(path):
                return None
        except OSError:
            return None
        path = path / part
    return path


def misnamed(root: Path, entries: set[str]) -> list[str]:
    """版の直下で、置き場所・`removed.csv` と大文字小文字・Unicode の正規化だけ違う名前（#276）。"""
    expected = {fold(name): name for name in [*AREAS, REMOVED]}
    found = []
    for name in sorted(entries):
        want = expected.get(fold(name))
        if want is None or name == want:
            continue
        path = root / name
        if path.is_dir() and not path.is_symlink() and not has_content(path):
            continue  # 読む名前を持たない（`.DS_Store` だけ）——タグにも写らない
        found.append(f"{root / name}: {want} と大文字小文字・Unicode の正規化だけ違う名前は置かない"
                     f"（区別しないファイルシステムでだけ {want} として開けてしまう）")
    return found


def misnamed_structured(root: Path, files: dict[str, Path]) -> list[str]:
    """置き場所の中で、構造ファイル（`shared/qa.csv` など）と大文字小文字・Unicode の正規化だけ違うパス（#511）。

    重ねた出力を読む側（`check-spec-exit.py`・`scaffold.py`）は決まった名前でパスを組み立てるので、
    区別しないファイルシステムでだけ `shared/QA.csv` を Q&A 表として開いてしまう。
    """
    expected = {fold(path): path for path in STRUCTURED}
    found = []
    for path in sorted(files):
        want = expected.get(fold(path))
        if want is not None and path != want:
            found.append(f"{root / path}: {want} と大文字小文字・Unicode の正規化だけ違う名前は置かない"
                         f"（区別しないファイルシステムでだけ {want} として開けてしまう）")
    return found


def list_files(root: Path, entries: set[str], problems: list[str],
               index: dict[tuple[str, ...], set[str]] | None = None,
               owned: dict[tuple[int, int], set[str]] | None = None) -> dict[str, Path]:
    """版のディレクトリの、重ねる置き場所にあるファイル（`.` で始まる名前は読まない）。置き場所は綴りどおりの名前だけ。
    名前はどの段も `spelled` の綴り（`index` は `tracked` の全体。#569）。"""
    files: dict[str, Path] = {}
    for area in AREAS:
        if area not in entries:
            continue
        top = root / area
        if top.is_symlink():
            problems.append(f"{top}: シンボリックリンクは置かない")
            continue
        if not top.is_dir():
            continue
        walk(root, top, files, problems, index, (root.name, area), owned)
    return files


def walk(root: Path, directory: Path, files: dict[str, Path], problems: list[str],
         index: dict[tuple[str, ...], set[str]] | None = None, prefix: tuple[str, ...] = (),
         owned: dict[tuple[int, int], set[str]] | None = None) -> None:
    """読めないディレクトリを黙って飛ばさない（`Path.rglob` は飛ばす。`names` が `Unreadable` を投げる）。
    `prefix` は `docs` からのこのディレクトリの名前（index の綴り）。`owned` は `owners` の表——追跡しているファイルは、
    自分の index のパス（`prefix` と名前）でだけ数える（綴りだけ違う同じ項目で追跡しているものを捨てる。`claims`）。"""
    for name in sorted(spelled(directory, None if index is None else index.get(prefix, set()))):
        if name.startswith("."):
            continue
        path = directory / name
        if path.is_symlink():
            problems.append(f"{path}: シンボリックリンクは置かない")
        elif path.is_dir():
            walk(root, path, files, problems, index, (*prefix, name), owned)
        elif path.is_file():
            if owned is not None and not claims(owned, path, "/".join((*prefix, name))):
                continue  # 別の綴りの index のパスで追跡している（そちらの綴りで数える。#569 の 2 パス目の指摘）
            files[path.relative_to(root).as_posix()] = path


def claims(owned: dict[tuple[int, int], set[str]], path: Path, relative: str) -> bool:
    """`path` のファイルを `relative`（`docs` からの index の綴り）として数えてよいか。

    捨てるのは、**同じ実体を、綴りだけ違う（`fold` が同じ）パスで追跡していて、FS が 2 つを同じ項目として開く**ときだけ
    ——区別しない FS で 1 つになったフォルダを別の綴りで辿った形（#569 の 2 パス目の指摘）。**ハードリンクは実体が同じでも
    別の項目**なので数える（#676）——名前が違う別名・区別する FS で別のフォルダにある別名・同じフォルダで綴りだけ違う名前の別名。
    """
    try:
        st = os.lstat(path)
    except OSError:
        return True
    paths = owned.get((st.st_dev, st.st_ino))
    if paths is None:
        return True  # 追跡していない（git に足す前のファイル。#677）
    if relative in paths:
        return True
    docs = path.parents[relative.count("/")]
    return not any(fold(other) == fold(relative) and same_item(docs / other, path) for other in paths)


def same_item(a: Path, b: Path) -> bool:
    """綴りだけ違う 2 つのパスを、FS が同じ項目（ディレクトリの同じ 1 項目）として開くか。

    親のフォルダが同じ項目で、その中に名前を畳むと同じになる項目が 1 つしか無ければ同じ——区別しない FS では 1 つ、
    区別する FS で綴りだけ違う名前のハードリンクを並べれば 2 つ。読めなければ別の項目と読む（数える側に倒す）。
    """
    if not same_entry(a.parent, b.parent):
        return False
    try:
        listed = os.listdir(b.parent)
    except OSError:
        return False
    return sum(fold(name) == fold(b.name) for name in listed) == 1


def read_qa(path: Path, problems: list[str]) -> list[dict[str, str]]:
    code, lines = qa.check(path)
    if code == 2:
        raise Unreadable(lines[0])
    if code == 1:
        problems.extend(lines)
        return []
    reader = csv.reader(io.StringIO(read_text(path), newline=""))
    next(reader)
    return [dict(zip(qa.COLUMNS, fields)) for fields in reader if any(f.strip() for f in fields)]


def read_spec(path: Path, problems: list[str]) -> dict | None:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as e:
        problems.append(f"{path}: JSON として読めない（{e.msg}・{e.lineno} 行目）")
        return None
    if not isinstance(data, dict):
        problems.append(f"{path}: JSON のオブジェクトでない")
        return None
    features = data.get("features")
    if not isinstance(features, list):
        problems.append(f"{path}: `features` が配列でない")
        return None
    seen = set()
    ok = True
    for index, feature in enumerate(features):
        fid = feature.get("id") if isinstance(feature, dict) else None
        if not isinstance(fid, str) or not fid:
            problems.append(f"{path}: features[{index}] に `id`（文字列）が無い")
            ok = False
        elif fid in seen:
            problems.append(f"{path}: 機能の `id` が版の中で重複: {fid}")
            ok = False
        else:
            seen.add(fid)
    return data if ok else None


def read_removed(path: Path, problems: list[str]) -> list[tuple[int, str, str]]:
    reader = csv.reader(io.StringIO(read_text(path), newline=""))
    header = next(reader, None)
    if header != REMOVED_COLUMNS:
        problems.append(f"{path}:1: 見出し行が決まりと違う（期待: {','.join(REMOVED_COLUMNS)}）")
        return []
    rows = []
    for fields in reader:
        line = reader.line_num
        if not any(f.strip() for f in fields):
            continue
        if len(fields) != len(REMOVED_COLUMNS):
            problems.append(f"{path}:{line}: 列の数が {len(fields)}（見出しは {len(REMOVED_COLUMNS)}）")
            continue
        kind, target, reason = fields
        if kind not in KINDS:
            problems.append(f"{path}:{line}: `種類` が {' / '.join(KINDS)} のどれでもない: {kind}")
        elif not target:
            problems.append(f"{path}:{line}: `対象` が空")
        elif not reason.strip():
            problems.append(f"{path}:{line}: `理由` が空")
        else:
            rows.append((line, kind, target))
    return rows


def check_removed(removed_path: Path | str, removed: list[tuple[int, str, str]],
                  placed: dict[str, set[str]], present: dict[str, set[str]], problems: list[str]) -> None:
    """`removed.csv` の行が、決まりに反する配置か（`references/versions.md` の「削除」）。

    `placed` はその版が置くもの、`present` は前の版までの全体にあるもの（どちらも種類ごと）。
    `check-signoff.py` も Q&A の行だけを渡して使う（写しを作らない）。
    """
    seen: dict[tuple[str, str], int] = {}
    for line, kind, target in removed:
        where = f"{removed_path}:{line}"
        if (kind, target) in seen:
            problems.append(f"{where}: {seen[(kind, target)]} 行目と同じ対象を 2 度消す: {target}")
            continue
        seen[(kind, target)] = line
        if kind == KIND_FILE and target in STRUCTURED:
            problems.append(f"{where}: {target} はファイルとしては消せない（行・機能の単位で消す）")
        elif target in placed[kind]:
            problems.append(f"{where}: 同じ版で置きつつ消している: {target}")
        elif target not in present[kind]:
            problems.append(f"{where}: 前の版までに無いものを消そうとしている: {kind} {target}")


class Whole:
    """重ね合わせた全体。"""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.qa: dict[str, dict[str, str]] = {}  # 挿入順 = 並び順
        self.internal: dict[str, dict[str, str]] = {}  # 内部の Q&A 表（同上）
        self.spec: dict | None = None
        self.features: dict[str, dict] = {}
        self.has_qa = False  # どれかの版に qa.csv があれば、行が 0 でも見出しだけ書く（出力を docs/ と同じ形に）
        self.has_internal = False  # 内部の表も同じ

    def apply(self, number: int, root: Path, problems: list[str], index: dict[tuple[str, ...], set[str]] | None = None,
              owned: dict[tuple[int, int], set[str]] | None = None) -> None:
        """`index` は `tracked` の全体（段ごとの index の名前）、`owned` は `owners` の表。`root.name` は index の綴りの版の名前（`find_versions`）。"""
        entries = spelled(root, None if index is None else index.get((root.name,), set()))
        problems.extend(misnamed(root, entries))
        files = list_files(root, entries, problems, index, owned)
        problems.extend(misnamed_structured(root, files))
        removed_path = root / REMOVED
        removed = []
        if REMOVED not in entries:
            pass
        elif removed_path.is_symlink():
            problems.append(f"{removed_path}: シンボリックリンクは置かない")
        else:
            if number == 1:
                problems.append(f"{removed_path}: {V1_REMOVED}")
            else:
                removed = read_removed(removed_path, problems)

        qa_rows = read_qa(files[QA_PATH], problems) if QA_PATH in files else []
        internal_rows = read_qa(files[INTERNAL_QA_PATH], problems) if INTERNAL_QA_PATH in files else []
        spec = read_spec(files[SPEC_PATH], problems) if SPEC_PATH in files else None
        placed = {
            KIND_FILE: set(files) - set(STRUCTURED),
            KIND_QA: {row["No"] for row in qa_rows + internal_rows},
            KIND_FEATURE: {f["id"] for f in spec["features"]} if spec else set(),
        }
        present = {KIND_FILE: set(self.files), KIND_QA: set(self.qa) | set(self.internal), KIND_FEATURE: set(self.features)}
        check_removed(removed_path, removed, placed, present, problems)

        if problems:
            return
        for path, source in files.items():
            if path not in STRUCTURED:
                try:
                    self.files[path] = source.read_bytes()
                except OSError as e:
                    raise Unreadable(f"{source}: 読めない（{e.strerror}）") from None
        self.has_qa = self.has_qa or QA_PATH in files
        self.has_internal = self.has_internal or INTERNAL_QA_PATH in files
        for row in qa_rows:
            self.qa[row["No"]] = row
        for row in internal_rows:
            self.internal[row["No"]] = row
        if spec is not None:
            base = self.spec or {}
            self.spec = {**base, **{k: v for k, v in spec.items() if k != "features"}}
            for feature in spec["features"]:
                self.features[feature["id"]] = feature
        for _, kind, target in removed:
            # 消す表は番号で決まる（`D-` なら内部の表）。番号と表が食い違わないことは `read_qa` の検査が保証する
            table = (self.internal if qa.is_internal_number(target) else self.qa) if kind == KIND_QA else None
            {KIND_FILE: self.files, KIND_QA: table, KIND_FEATURE: self.features}[kind].pop(target)

    def render(self, problems: list[str]) -> dict[str, bytes]:
        """書く前に、出力の全部をバイトにする——書いている途中で作れないと分かる経路を残さない。"""
        rendered = dict(self.files)
        for present, path, rows in ((self.has_qa, QA_PATH, self.qa), (self.has_internal, INTERNAL_QA_PATH, self.internal)):
            if not present:
                continue
            buffer = io.StringIO(newline="")
            writer = csv.writer(buffer, lineterminator="\n")
            writer.writerow(qa.COLUMNS)
            for row in rows.values():
                writer.writerow([row[c] for c in qa.COLUMNS])
            rendered[path] = buffer.getvalue().encode("utf-8")
        if self.spec is not None:
            whole = {**self.spec, "features": list(self.features.values())}
            try:
                rendered[SPEC_PATH] = (json.dumps(whole, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            except UnicodeEncodeError:
                problems.append(f"重ねた {SPEC_PATH} に UTF-8 で書けない文字（対のないサロゲート）がある")
        return rendered


def fold(path: str) -> str:
    """大文字小文字・Unicode の正規化だけが違うパスを同じものと見る（区別しないファイルシステムでは同じ場所に書かれる）。"""
    return unicodedata.normalize("NFC", path).casefold()


def collisions(paths: list[str]) -> list[str]:
    """重ねた結果で書けない形——ファイルとディレクトリが同じパスになる・大文字小文字や正規化だけが違うパス（ファイルもフォルダも）が並ぶ。"""
    found = []
    by_fold: dict[str, str] = {}
    for path in sorted(paths):
        other = by_fold.setdefault(fold(path), path)
        if other != path:
            found.append(f"重ねた結果で {other} と {path} が大文字小文字・Unicode の正規化だけ違う（同じ場所に書かれうる）")
    dirs: dict[str, str] = {}
    for path in sorted(paths):
        parts = path.split("/")
        for depth in range(1, len(parts)):
            parent = "/".join(parts[:depth])
            if fold(parent) in by_fold:
                found.append(f"重ねた結果で {by_fold[fold(parent)]} がファイルとディレクトリの両方になる（{path}）")
            # フォルダの綴りだけが違うのも書けない形——タグを読む `build-proposal.py` の `copy_docs` と同じ判定（#569 の 2 パス目の指摘）
            other = dirs.setdefault(fold(parent), parent)
            if other != parent:
                found.append(f"重ねた結果でディレクトリ {other} と {parent} が大文字小文字・Unicode の正規化だけ違う（同じ場所に書かれうる）")
    return sorted(set(found), key=found.index)


def put(dest: Path, content: bytes) -> None:
    """出力を書く唯一の口（テストはここを差し替えて、書いている途中の失敗を作る）。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)


def owned(out: Path) -> bool:
    return out.is_dir() and not out.is_symlink() and (out / MARKER).is_file()


def remove_stale(out: Path, quiet: bool = False) -> None:
    if owned(out):
        shutil.rmtree(out)
        if not quiet:
            print(f"{out}: 前に作った出力を消した（今の入力から作ったものではないため）", file=sys.stderr)


class OutOfRange(Unreadable):
    """`--upto` の版が無い（終了コード 2）。"""


def merge(docs: Path, upto: int | None = None) -> tuple[list[str], list[tuple[int, Path]], Whole, dict[str, bytes]]:
    """(決まりに反する点, 版の一覧, 重ねた全体, 書く中身) を返す。決まりに反する点があれば、書く中身は空。

    書かずに全体が要るもの（`scaffold.py`）もこの関数で重ねる——同じ入力から、出力と同じバイトを作る。
    無い・読めない入力と、無い版の `upto` は `Unreadable` を投げる。
    """
    problems: list[str] = []
    found = tracked(docs) if docs.is_dir() else None
    index, owned = (None, None) if found is None else (found[0], owners(docs, found[1]))
    versions = find_versions(docs, problems, None if index is None else index.get((), set()))
    if not problems and not versions:
        problems.append(f"{docs}: 版（v1 など）が 1 つも無い")
    if upto is not None and not problems and upto > len(versions):
        raise OutOfRange(f"--upto {upto}: v{upto} が無い（最大は v{len(versions)}）")
    whole = Whole()
    rendered: dict[str, bytes] = {}
    for number, root in versions[:upto]:
        if problems:
            break
        whole.apply(number, root, problems, index, owned)
    if not problems:
        rendered = whole.render(problems)
        problems.extend(collisions(list(rendered)))
    return problems, versions, whole, (rendered if not problems else {})


def main(argv: list[str]) -> int:
    upto = None
    args = list(argv)
    if "--upto" in args:
        at = args.index("--upto")
        if at + 1 >= len(args) or not re.fullmatch(r"[1-9][0-9]*", args[at + 1]):
            print("--upto には 1 以上の整数を渡す", file=sys.stderr)
            return 2
        upto = int(args[at + 1])
        del args[at:at + 2]
    if len(args) != 2:
        print(__doc__.splitlines()[2] if __doc__ else
              f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）", file=sys.stderr)
        return 2
    docs, out = Path(args[0]), Path(args[1])

    if out.is_symlink():
        print(f"{out}: 出力先にシンボリックリンクは使わない（印で持ち主を確かめられない）", file=sys.stderr)
        return 2
    # 3.12 の Path.resolve はリンクの輪で RuntimeError を投げる（3.13 からは投げない）。os.path.realpath は
    # どちらでも投げないので、下の出力先の検査と「ディレクトリが無い」の後始末が、版によらず同じ順で走る（#286）
    docs_real, out_real = Path(os.path.realpath(docs)), Path(os.path.realpath(out))
    if out_real == docs_real or docs_real in out_real.parents:
        print(f"{out}: {docs} の中には書かない（次の重ね合わせで入力に混ざる）", file=sys.stderr)
        return 2
    if out_real in docs_real.parents:
        print(f"{out}: {docs} を含む場所には書かない（前の出力と一緒に入力を消す）", file=sys.stderr)
        return 2
    if out.exists() and not owned(out) and (not out.is_dir() or any(out.iterdir())):
        print(f"{out}: 印（{MARKER}）の無い空でない場所には書かない（取り違えた正本を消さないため）", file=sys.stderr)
        return 2

    if not docs.is_dir():
        print(f"{docs}: ディレクトリが無い", file=sys.stderr)
        remove_stale(out)
        return 2

    try:
        problems, versions, whole, rendered = merge(docs, upto)
    except OutOfRange as e:
        print(e, file=sys.stderr)
        remove_stale(out)
        return 2
    except Unreadable as e:
        print(e, file=sys.stderr)
        print("重ね合わせは作っていない", file=sys.stderr)
        remove_stale(out)
        return 2
    except Exception as e:  # 想定外の例外（巨大なセルの csv.Error・深い入れ子の RecursionError など）も読めない入力と同じに扱う（#286）
        print(f"{docs}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない。重ね合わせは作っていない",
              file=sys.stderr)
        remove_stale(out)
        return 2
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        print("重ね合わせは作っていない", file=sys.stderr)
        remove_stale(out)
        return 1

    remove_stale(out, quiet=True)
    existed = out.is_dir()  # 利用者が用意した空の出力先は、失敗しても消さない（印の無いものは消さない）
    try:
        out.mkdir(parents=True, exist_ok=True)
        for path in sorted(rendered):
            put(out / path, rendered[path])
        # 印は最後に書く——途中で失敗した出力を、出来上がったものと取り違えないため
        put(out / MARKER, "merge-versions.py が作った。手で直さない\n".encode("utf-8"))
    except Exception as e:  # 想定外の例外でも書きかけを残さない——印の無い書きかけは、次の実行が断る（#286）
        reason = e.strerror if isinstance(e, OSError) else f"想定外の例外 {type(e).__name__}: {e}"
        print(f"{out}: 書けない（{reason}）。書きかけを消した", file=sys.stderr)
        if not existed:
            shutil.rmtree(out, ignore_errors=True)
        elif out.is_dir():
            for child in out.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    child.unlink(missing_ok=True)
        return 2
    last = len(versions) if upto is None else upto
    print(f"{out}: v1〜v{last} を重ねた（ファイル {len(whole.files)}・Q&A {len(whole.qa)} 行・機能 {len(whole.features)}）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
