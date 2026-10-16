#!/usr/bin/env python3
"""版ごとのディレクトリ（`docs/v1/`・`docs/v2/`…）を重ね合わせて、ある版の時点の全体を作る。

usage: python3 merge-versions.py <docs ディレクトリ> <出力先ディレクトリ> [--upto <n>]

**決まりの正は `references/versions.md` である**（このプラグインの中にある）。
下の定数（版の名前・重ねる置き場所・`removed.csv` の列と種類・ファイルとしては消せないもの・出力先の印）はその写しで、
**写しがずれていないかは、このリポジトリの `scripts/test-merge-versions.py` が `references/versions.md` と突き合わせて見る**。

- v1 に v2、…、v<n> の差分を順に重ねる。`--upto` を省けば、番号が最大の版（作業中の版）まで。
- 出力は版に分ける前の `docs/` と同じ形（`shared/`・`requirements/`・`spec/`）。
- **同じ入力から同じバイトを作る**——時刻を使わず、行・機能は前の版の順、ファイルはパスの順。
- 各版の `qa.csv` は同梱の `check-qa-csv.py` で検査する（**列の決まりを写さない**）。
- 標準ライブラリだけを使う。

終了コード:

- 0: 書いた
- 1: 入力が決まりに反する——**書かない。前に作った出力があれば消す**（問題は 1 件で止めず、
  最初に問題のあった版の中は全部出す。それより後の版は前の版の全体に依るので見ない）
- 2: 引数の誤り・入力が読めない・出力先に書けない（印の無い空でないディレクトリ・`docs/` の中）——
  **書かない**。出力先が印の在るディレクトリなら、前の出力を消す

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **新しいつもりで前の版の番号を書いた** | 同じ番号は「変更」の意味と決めている。意図は機械で分からない |
| **重ね合わせた `spec_ir.json` の中身の決まり** | `spec-ir.md` の決まりは `scaffold.py` が全体に当てる |
| **凍結した版が直されていないか** | `release-v<n>` のタグとの照合で、git が要る（このスクリプトは git を使わない） |
| **大文字小文字を区別しないファイルシステムでの `V2`** | 試していない |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import re
import shutil
import sys
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
REMOVED = "removed.csv"
REMOVED_COLUMNS = ["種類", "対象", "理由"]
KIND_FILE, KIND_QA, KIND_FEATURE = "ファイル", "Q&A", "機能"
KINDS = [KIND_FILE, KIND_QA, KIND_FEATURE]
STRUCTURED = [QA_PATH, SPEC_PATH]
MARKER = ".merged-versions"


class Unreadable(Exception):
    """入力が読めない（中身を検査していない）。"""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except OSError as e:
        raise Unreadable(f"{path}: 読めない（{e.strerror}）") from None
    except UnicodeDecodeError:
        raise Unreadable(f"{path}: UTF-8 として読めない") from None


def find_versions(docs: Path, problems: list[str]) -> list[tuple[int, Path]]:
    found = []
    for entry in sorted(docs.iterdir()):
        name = entry.name
        if not VERSION_LIKE.match(name):
            continue
        if not entry.is_dir() or entry.is_symlink():
            if VERSION.fullmatch(name):
                problems.append(f"{entry}: 版はディレクトリで置く（シンボリックリンク・ファイルは不可）")
            continue
        if not VERSION.fullmatch(name):
            problems.append(f"{entry}: 版の名前の形（v<n>・先頭に 0 を付けない）に合わない")
            continue
        found.append((int(name[1:]), entry))
    found.sort()
    for expected, (number, entry) in enumerate(found, start=1):
        if number != expected:
            problems.append(f"{entry}: 版の番号が欠けている（v{expected} が無い）")
            break
    return found


def list_files(root: Path, problems: list[str]) -> dict[str, Path]:
    """版のディレクトリの、重ねる置き場所にあるファイル（`.` で始まる名前は読まない）。"""
    files: dict[str, Path] = {}
    for area in AREAS:
        top = root / area
        if top.is_symlink():
            problems.append(f"{top}: シンボリックリンクは置かない")
            continue
        if not top.is_dir():
            continue
        for path in sorted(top.rglob("*")):
            rel = path.relative_to(root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            if path.is_symlink():
                problems.append(f"{path}: シンボリックリンクは置かない")
            elif path.is_file():
                files[rel.as_posix()] = path
    return files


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


class Whole:
    """重ね合わせた全体。"""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.qa: dict[str, dict[str, str]] = {}  # 挿入順 = 並び順
        self.spec: dict | None = None
        self.features: dict[str, dict] = {}

    def apply(self, number: int, root: Path, problems: list[str]) -> None:
        files = list_files(root, problems)
        removed_path = root / REMOVED
        removed = []
        if removed_path.exists():
            if number == 1:
                problems.append(f"{removed_path}: v1 には置かない（消すものが無い）")
            else:
                removed = read_removed(removed_path, problems)

        qa_rows = read_qa(files[QA_PATH], problems) if QA_PATH in files else []
        spec = read_spec(files[SPEC_PATH], problems) if SPEC_PATH in files else None
        placed = {
            KIND_FILE: set(files) - set(STRUCTURED),
            KIND_QA: {row["No"] for row in qa_rows},
            KIND_FEATURE: {f["id"] for f in spec["features"]} if spec else set(),
        }
        present = {KIND_FILE: set(self.files), KIND_QA: set(self.qa), KIND_FEATURE: set(self.features)}

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

        if problems:
            return
        for path, source in files.items():
            if path not in STRUCTURED:
                self.files[path] = source.read_bytes()
        for row in qa_rows:
            self.qa[row["No"]] = row
        if spec is not None:
            base = self.spec or {}
            self.spec = {**base, **{k: v for k, v in spec.items() if k != "features"}}
            for feature in spec["features"]:
                self.features[feature["id"]] = feature
        for _, kind, target in removed:
            {KIND_FILE: self.files, KIND_QA: self.qa, KIND_FEATURE: self.features}[kind].pop(target)

    def write(self, out: Path) -> None:
        for path, content in sorted(self.files.items()):
            dest = out / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
        if self.qa:
            buffer = io.StringIO(newline="")
            writer = csv.writer(buffer, lineterminator="\n")
            writer.writerow(qa.COLUMNS)
            for row in self.qa.values():
                writer.writerow([row[c] for c in qa.COLUMNS])
            dest = out / QA_PATH
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(buffer.getvalue().encode("utf-8"))
        if self.spec is not None:
            whole = {**self.spec, "features": list(self.features.values())}
            dest = out / SPEC_PATH
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((json.dumps(whole, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def owned(out: Path) -> bool:
    return out.is_dir() and not out.is_symlink() and (out / MARKER).is_file()


def remove_stale(out: Path, quiet: bool = False) -> None:
    if owned(out):
        shutil.rmtree(out)
        if not quiet:
            print(f"{out}: 前に作った出力を消した（今の入力から作ったものではないため）", file=sys.stderr)


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
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    docs, out = Path(args[0]), Path(args[1])

    if not docs.is_dir():
        print(f"{docs}: ディレクトリが無い", file=sys.stderr)
        return 2
    docs_real, out_real = docs.resolve(), out.resolve()
    if out_real == docs_real or docs_real in out_real.parents:
        print(f"{out}: {docs} の中には書かない（次の重ね合わせで入力に混ざる）", file=sys.stderr)
        return 2
    if out.exists() and not owned(out) and (not out.is_dir() or any(out.iterdir())):
        print(f"{out}: 印（{MARKER}）の無い空でない場所には書かない（取り違えた正本を消さないため）", file=sys.stderr)
        return 2

    problems: list[str] = []
    try:
        versions = find_versions(docs, problems)
        if not problems and not versions:
            problems.append(f"{docs}: 版（v1 など）が 1 つも無い")
        if upto is not None and not problems and upto > len(versions):
            print(f"--upto {upto}: v{upto} が無い（最大は v{len(versions)}）", file=sys.stderr)
            remove_stale(out)
            return 2
        whole = Whole()
        for number, root in versions[:upto]:
            if problems:
                break
            whole.apply(number, root, problems)
    except Unreadable as e:
        print(e, file=sys.stderr)
        print("重ね合わせは作っていない", file=sys.stderr)
        remove_stale(out)
        return 2
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        print("重ね合わせは作っていない", file=sys.stderr)
        remove_stale(out)
        return 1

    remove_stale(out, quiet=True)
    out.mkdir(parents=True, exist_ok=True)
    (out / MARKER).write_text("merge-versions.py が作った。手で直さない\n", encoding="utf-8")
    whole.write(out)
    last = len(versions) if upto is None else upto
    print(f"{out}: v1〜v{last} を重ねた（ファイル {len(whole.files)}・Q&A {len(whole.qa)} 行・機能 {len(whole.features)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
