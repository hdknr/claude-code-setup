#!/usr/bin/env python3
"""持ち込まれた動くコードから要求の候補を起こす取り込みの段（req-loop の手順 3a）の、機械で決まる部分（#998）。

usage:
  python3 intake-code.py snapshot <正本の根> <取り込む元> <出力先> [--remote <名前>]
  python3 intake-code.py rows <正本の根> <候補の JSON> <スナップショット> [--dry-run]

取り込む元: `pr:<番号>`（`refs/pull/<番号>/head` を取る）・`branch:<名前>`（手元のブランチかリモート追跡）・`dir:<パス>`

**決まりの正は `references/intake.md` である**（このプラグインの中にある）。下の定数（候補の種類・候補と食い違いの鍵・起票元の詳細・
取り込みの出所の印の名前・読み飛ばすディレクトリ・基盤要件の目印）はそこに書いた決まりの写しで、目印の一覧の本体はここにある。

2 つの口がある:

- **`snapshot`**——取り込む元を、**読むだけで**出力先に写す（コミットの木を `git ls-tree`・`git cat-file` で書き出すか、ディレクトリの写し）。出所の印 `.intake-source.json` を書く。
  **出力先は正本の外か、正本の `build/` の下だけ**——`docs/`・`scaffold/` などの正本の中には置かない。
- **`rows`**——スキル（LLM）が書いた候補の JSON を検査し、**作業中の版（`docs/` の版で番号が最大のもの）の `shared/qa.csv`** に、
  `確認中`・`未回答`・`—` の行として足す。足した後の表全体を `check-qa-csv.py` に当て、通らなければ書かない。
  あわせて、**既存の正本との食い違い**を出す——スキルが書いた食い違い（引用が正本のそのファイルに在るかを見る）と、
  基盤要件の表（`shared/infra.csv`）の `決定` とコードの目印を機械で照らした食い違い。`--dry-run` は書かずに行を出す。

**守ること**:

- `snapshot` は正本のリポジトリで `git fetch`・`git rev-parse`・`git ls-tree`・`git cat-file`・`git check-ignore` だけを走らせる——`merge`・`checkout`・`switch`・`commit`・`push` を走らせない。
  `pr:` の `fetch` は `--refmap=` で参照を作らずに取る（git が `FETCH_HEAD` を書く）。正本のブランチ・HEAD・作業ツリー・index は変わらない。`--remote` の名前が `-` で始まれば 2
- `snapshot` はコミットの木を `ls-tree`・`cat-file` で写す——取り込む元の `.gitattributes`（`export-ignore` など）を効かせない。
  木でもディレクトリでも、シンボリックリンク・サブモジュール・どの段の `.git`・根の `.intake-source.json`・大文字小文字だけ違う名前（とファイルとディレクトリの衝突）は写さず、名前を出す。失敗したら半端な写しを残さない
- `snapshot` の出力先が正本の中で `build/` の下でない・`build/` の下でも正本の `.gitignore` に外されていない・空でなければ、2 で止まって何も写さない
- `rows` の行は必ず `回答 = 未回答`・`反映先 = —`・`状態 = 確認中`——候補の JSON に回答・状態・反映先の鍵があれば違反（1）で、何も書かない
- 候補の各行に、スナップショットの中の実在するファイル（途中のシンボリックリンクでスナップショットの外へ出ない）と範囲の中の行（`code`）と、コードの振る舞い（`code_behavior`）が要る。質問の文の後ろに
  `（コードではこうなっていた: <振る舞い>。<パス>:<行>）` を足す
- 同じ質問の行は足さない——候補の質問を、既にある行（全部の版）の質問から取り込みの添え書き `（コードではこうなっていた: …）` を外した文と照らし、
  一致すれば違反（1）で何も書かない（同じ候補の JSON で当て直しても、`code_behavior`・該当箇所を直して当て直しても重ねて足さない）
- 既にある作業中の版の表の BOM と改行（CRLF か LF。最初の行で決める）を保って書く——既にある行のバイトは変えず、足した行も同じ改行で書く。表が無ければ BOM なし・LF で作る
- 番号は `Q-R-` の、全部の版の `shared/qa.csv` を通した最大の次から振る（印の無い前の形の番号と、ほかの印の番号は数えない）
- 起票元は `要求確定（取り込み・<種類>。<出所>）`（`references/intake.md` の「起票の形」）
- スキルが書いた食い違いは、`canon` が重ね合わせた全体のファイルで、`canon_quote` がその中に在るときだけ出す（無ければ違反）
- 基盤要件の `ホスティング環境`・`DBMS` の行で `決定` の値から種類を読めれば、コードの目印が別の種類を示すたびに食い違いを 1 件出す。
  `言語` は拡張子で数え、決定の言語のファイルより多いほかの言語ごとに 1 件出す（同じ数以下のほかの言語——設定や補助の数本——は出さない）

終了コード:

- 0: `snapshot` は写した。`rows` は書いた（`--dry-run` なら出した）、食い違いは 0 件
- 3: `rows` は書いた（出した）が、食い違いがある（止まる理由ではない——スキルが利用者に示す）
- 1: `rows` の候補の JSON が決まりに反する（全部を出す）。何も書いていない
- 2: 判定していない——引数の誤り・正本が読めない・版を重ねられない・既にある表が検査を通らない・スナップショットでない・`git` が失敗した・出力先が不正

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。Q&A 表の列・印・検査は `check-qa-csv.py`、
版の重ね合わせは `merge-versions.py` を読む（写さない）。

**この検査が守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **候補の中身**（コードから読み取った要求・業務ルール・暗黙の前提が、作った人の意図と合うか・抜けが無いか） | 判断であって、一意に決まらない。スキルが読み、利用者が答えて決める |
| **質問が既にある質問と同じ意味か** | 見るのは質問の文がそのまま一致する行だけ。言い換えた重複は見えない |
| **スキルが書かなかった食い違い**（決定表・要求の本文とコードの振る舞いの違い） | 機械で照らすのは基盤要件の 3 項目だけ。ほかはスキルが読んで `findings` に書いたものの引用を確かめるだけ |
| **目印の網羅**（下の `MARKERS` に無い SDK・ドライバ・言語） | 目印の一覧は代表だけ。一覧に無い書き方のコードは、照らしても 0 件になる |
| **目印の文脈**（コメントや文字列の中・使っていない依存） | 行単位の一致で、構文を読まない。コメントの中の `boto3` も目印に数える |
| **`決定` の値から読めない種類**（「自社のデータセンター」） | 種類を読めない行は照らさず、照らしていないと出す |
| **出所の印を手で書き換えたスナップショット** | 印は `snapshot` が書いたものとして読む |
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

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


qa = _load("check_qa_csv", "check-qa-csv.py")
mv = _load("merge_versions", "merge-versions.py")

# ---- `references/intake.md` の写し
SOURCE_FILE = ".intake-source.json"
SOURCE_NAME = "要求確定"  # 起票元（印は qa.MARKS から引く）
MARK = qa.MARKS[SOURCE_NAME]
KINDS = ("要求", "業務ルール", "暗黙の前提")
CANDIDATE_KEYS = {"kind", "question", "options", "recommend", "reason", "code_behavior", "code"}
CANDIDATE_OPTIONAL = {"cost"}
FINDING_KEYS = {"summary", "canon", "canon_quote", "code_behavior", "code"}
TOP_KEYS = {"candidates", "findings"}
# 取り込んだ行を確定扱いにする鍵（書けない）
CONFIRMING = ("answer", "回答", "state", "状態", "target", "反映先")
# 取り込んだ行の状態（回答待ち）。名前が `check-qa-csv.py` の状態に無ければ、書く前の表全体の検査が落とす
PENDING = "確認中"
CODE_NOTE = "（コードではこうなっていた: "  # build_row が質問の後ろに足す添え書きの頭（重複の照合で外す）
QA_PATH = "shared/qa.csv"
INFRA_PATH = "shared/infra.csv"
# 正本の中で、スナップショットを置いてよいのはここだけ（生成物で commit しない）
BUILD = "build"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "vendor"}
MAX_BYTES = 1_000_000

# ---- 基盤要件の目印（本体はここ）。項目 → [(種類, 決定の値に現れる語, コードの目印)]
MARKERS: dict[str, list[tuple[str, re.Pattern, re.Pattern]]] = {
    "ホスティング環境": [
        ("AWS", re.compile(r"AWS|Amazon", re.I),
         re.compile(r"\bboto3\b|\bbotocore\b|@aws-sdk/|\baws-sdk\b|\baws-cdk-lib\b|amazonaws\.com", re.I)),
        ("Google Cloud", re.compile(r"Google ?Cloud|\bGCP\b", re.I),
         re.compile(r"\bgoogle-cloud-[a-z]|\bgoogle\.cloud\b|@google-cloud/|\bfirebase-admin\b|googleapis\.com", re.I)),
        ("Azure", re.compile(r"Azure", re.I),
         re.compile(r"\bazure-[a-z]|@azure/|\bazure\.(?:storage|identity|cosmos)\b|\.windows\.net\b", re.I)),
    ],
    "DBMS": [
        ("PostgreSQL", re.compile(r"Postgre", re.I),
         re.compile(r"\bpsycopg2?\b|\basyncpg\b|\bpostgres(?:ql)?(?:\+\w+)?://", re.I)),
        ("MySQL", re.compile(r"MySQL|MariaDB", re.I),
         re.compile(r"\bpymysql\b|\bmysqlclient\b|\bmysql2\b|\bmysql(?:\+\w+)?://|\bmysql\.connector\b", re.I)),
        ("SQLite", re.compile(r"SQLite", re.I),
         re.compile(r"\bimport sqlite3\b|\bsqlite(?:\+\w+)?:///|\bbetter-sqlite3\b", re.I)),
    ],
}
# 言語は拡張子で見る。種類 → (決定の値に現れる語, 拡張子)
LANGUAGES: list[tuple[str, re.Pattern, tuple[str, ...]]] = [
    ("Python", re.compile(r"Python", re.I), (".py",)),
    ("TypeScript", re.compile(r"TypeScript", re.I), (".ts", ".tsx")),
    ("JavaScript", re.compile(r"JavaScript|Node", re.I), (".js", ".jsx", ".mjs", ".cjs")),
    ("Ruby", re.compile(r"Ruby", re.I), (".rb",)),
    ("Go", re.compile(r"\bGo\b|Golang", re.I), (".go",)),
    ("Java", re.compile(r"\bJava\b(?!Script)", re.I), (".java",)),
    ("PHP", re.compile(r"PHP", re.I), (".php",)),
]
LANGUAGE_ITEM = "言語"
DECIDED_STATES = ("決定", "暫定")


class Stop(Exception):
    """判定していない（終了コード 2）。"""


def git(root: Path, *args: str, binary: bool = False) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=not binary)
    if proc.returncode != 0:
        err = proc.stderr if isinstance(proc.stderr, str) else proc.stderr.decode("utf-8", "replace")
        raise Stop(f"git {' '.join(args)} が失敗した: {err.strip()}")
    return proc


def inside(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


# ---------------------------------------------------------------- snapshot

def snapshot(root: Path, source: str, out: Path, remote: str) -> list[str]:
    if not root.is_dir():
        raise Stop(f"{root}: 正本の根がディレクトリでない")
    if inside(out, root):
        if not inside(out, root / BUILD):
            raise Stop(f"{out}: 正本の中に置かない（正本の外か {root / BUILD} の下にする）")
        # build/ が git に外されていなければ、写したコードが正本の未追跡のファイルとして見え、`git add -A` で入る
        ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(out)], capture_output=True)
        if ignored.returncode != 0:
            raise Stop(f"{out}: 正本の .gitignore が {BUILD}/ を外していない（写したコードが正本に入りうる）——正本の外に写すか、.gitignore に {BUILD}/ を足す")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Stop(f"{out}: 空でない（前の取り込みを残したまま重ねない）")
    if remote.startswith("-"):
        raise Stop(f"--remote の名前が `-` で始まる: {remote!r}")
    kind, _, ref = source.partition(":")
    if not ref or ref.startswith("-"):
        raise Stop(f"取り込む元の形でない: {source!r}（pr:<番号>・branch:<名前>・dir:<パス>）")
    if kind == "pr":
        if not ref.isdigit():
            raise Stop(f"PR の番号が数字でない: {ref!r}")
        # `--refmap=` で、設定の refspec（`refs/pull/*` を追跡する設定など）による参照の更新もしない
        git(root, "fetch", "--no-tags", "--quiet", "--refmap=", remote, f"refs/pull/{ref}/head")
        commit = git(root, "rev-parse", "--verify", "FETCH_HEAD^{commit}").stdout.strip()
        meta = {"kind": "pr", "ref": ref, "commit": commit, "label": f"PR #{ref}（{commit[:7]}）"}
    elif kind == "branch":
        commit = git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").stdout.strip()
        meta = {"kind": "branch", "ref": ref, "commit": commit, "label": f"ブランチ {ref}（{commit[:7]}）"}
    elif kind == "dir":
        src = Path(ref).resolve()
        if not src.is_dir():
            raise Stop(f"{src}: ディレクトリでない")
        if inside(out, src):
            raise Stop(f"{out}: 取り込む元の中に写さない")
        meta = {"kind": "dir", "ref": str(src), "commit": None, "label": f"ディレクトリ {src.name}"}
    else:
        raise Stop(f"取り込む元の種類が無い: {kind!r}（pr・branch・dir）")

    created = not out.exists()
    out.mkdir(parents=True, exist_ok=True)
    skipped: list[str] = []
    try:
        if meta["commit"]:
            skipped = extract_tree(root, meta["commit"], out)
        else:
            skipped = copy_dir(src, out)
        if (out / SOURCE_FILE).exists() or (out / SOURCE_FILE).is_symlink():
            raise Stop(f"{out / SOURCE_FILE}: 出所の印の場所に、写したものが在る")
        (out / SOURCE_FILE).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except BaseException:
        # 半端な写しを残さない（次の実行が「空でない」で止まる）
        if created:
            shutil.rmtree(out, ignore_errors=True)
        else:
            for child in out.iterdir():
                shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
        raise
    files = sum(1 for _ in source_files(out))
    report = [f"写した: {meta['label']} → {out}（ファイル {files} 件）"]
    if skipped:
        report.append(f"写していない（シンボリックリンク・サブモジュール・`.git`・出所の印の名前・大文字小文字だけ違う名前）: {'、'.join(skipped)}")
    return report + ["正本のブランチ・作業ツリーには何も書いていない（マージしない・正本にしない）"]


def unsafe_name(parts: tuple[str, ...]) -> bool:
    """写さない名前——どの段でも `.git`（写した先が git のリポジトリになり、中で git を走らせると持ち込んだ側の設定が動く）と、
    根の出所の印 `.intake-source.json`（印とぶつかる）。大文字小文字は問わない。"""
    folded = [part.casefold() for part in parts]
    return ".git" in folded or (bool(folded) and folded[0] == SOURCE_FILE.casefold())


def copy_dir(src: Path, out: Path) -> list[str]:
    """ディレクトリを写す。シンボリックリンク・`.git`・根の出所の印は写さず、名前を返す。"""
    skipped: list[str] = []

    def ignore(directory: str, names: list[str]) -> set[str]:
        base = Path(directory).relative_to(src)
        drop = set()
        for name in names:
            rel = base / name
            if (Path(directory) / name).is_symlink() or unsafe_name(rel.parts):
                drop.add(name)
                skipped.append(rel.as_posix())
        return drop

    shutil.copytree(src, out, symlinks=True, dirs_exist_ok=True, ignore=ignore)
    return skipped


def extract_tree(root: Path, commit: str, out: Path) -> list[str]:
    """コミットの木のファイルを、`git ls-tree` と `git cat-file` で出力先に書く。返すのは写さなかったもののパス。

    `git archive` を使わない——取り込む元の `.gitattributes`（`export-ignore`・`export-subst`）が効き、持ち込んだ側が
    ファイルを黙って外したり書き換えたりできる。シンボリックリンク（120000）とサブモジュール（160000）は写さない。"""
    listing = git(root, "ls-tree", "-r", "-z", "--full-tree", commit, binary=True).stdout
    blobs: list[tuple[str, str]] = []
    skipped: list[str] = []
    seen_files: set[str] = set()
    seen_dirs: set[str] = set()
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        head, _, raw = entry.partition(b"\t")
        mode, kind, sha = head.decode().split()
        rel = raw.decode("utf-8", "surrogateescape")
        parts = Path(rel).parts
        if kind != "blob" or mode == "120000" or rel.startswith("/") or ".." in parts or unsafe_name(parts):
            skipped.append(rel)
            continue
        # 大文字小文字を区別しないファイルシステムで同じ場所になるもの・ファイルとディレクトリがぶつかるものは、後のほうを写さない
        folded = [part.casefold() for part in parts]
        key = "/".join(folded)
        prefixes = {"/".join(folded[:i]) for i in range(1, len(folded))}
        if key in seen_files or key in seen_dirs or prefixes & seen_files:
            skipped.append(rel)
            continue
        seen_files.add(key)
        seen_dirs.update(prefixes)
        blobs.append((sha, rel))
    if not blobs:
        return skipped
    proc = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"], input="".join(f"{sha}\n" for sha, _ in blobs).encode(),
                          capture_output=True)
    if proc.returncode != 0:
        raise Stop(f"git cat-file が失敗した: {proc.stderr.decode('utf-8', 'replace').strip()}")
    data, pos = proc.stdout, 0
    for sha, rel in blobs:
        end = data.index(b"\n", pos)
        size = int(data[pos:end].split()[2])
        content = data[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    return skipped


# ---------------------------------------------------------------- 読む

def source_files(snap: Path):
    """読むファイル（スナップショットの根からの相対パス）。読み飛ばすディレクトリ・`.` で始まる名前・シンボリックリンクは除く。"""
    for dirpath, dirnames, filenames in os.walk(snap):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
                             and not os.path.islink(os.path.join(dirpath, d)))
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if name.startswith(".") or path.is_symlink():
                continue
            yield path.relative_to(snap)


def read_lines(path: Path) -> list[str] | None:
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def locate(snap: Path, code, where: str, problems: list[str]) -> list[str]:
    """`code` を検査し、`パス:行` の並びを返す。"""
    if not isinstance(code, list) or not code:
        problems.append(f"{where}: `code`（コードの該当箇所）が 1 つも無い")
        return []
    places = []
    for i, loc in enumerate(code):
        at = f"{where}.code[{i}]"
        if not isinstance(loc, dict) or set(loc) != {"path", "line"}:
            problems.append(f"{at}: `path` と `line` の 2 つの鍵で書く")
            continue
        rel, line = loc["path"], loc["line"]
        if not isinstance(rel, str) or not rel or rel.startswith("/") or ".." in Path(rel).parts:
            problems.append(f"{at}: `path` はスナップショットの根からの相対パス（`..` を使わない）: {rel!r}")
            continue
        if type(line) is not int or line < 1:
            problems.append(f"{at}: `line` は 1 以上の整数: {line!r}")
            continue
        path = snap / rel
        if path.is_symlink() or not path.is_file():
            problems.append(f"{at}: スナップショットに無いファイル: {rel}")
            continue
        if not inside(path.resolve(), snap.resolve()):
            problems.append(f"{at}: スナップショットの外を指す（途中にシンボリックリンクがある）: {rel}")
            continue
        lines = read_lines(path)
        if lines is None:
            problems.append(f"{at}: 読めないファイル（UTF-8 でない・大きすぎる）: {rel}")
            continue
        if line > len(lines):
            problems.append(f"{at}: {rel} は {len(lines)} 行しかない（{line} 行目）")
            continue
        places.append(f"{rel}:{line}")
    return places


def text_field(obj: dict, key: str, where: str, problems: list[str]) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        problems.append(f"{where}: `{key}` が空か文字列でない")
        return ""
    if "\n" in value or "\r" in value:
        problems.append(f"{where}: `{key}` に改行を入れない")
        return ""
    return value.strip()


def check_keys(obj, allowed: set[str], required: set[str], where: str, problems: list[str]) -> bool:
    if not isinstance(obj, dict):
        problems.append(f"{where}: オブジェクトで書く")
        return False
    confirming = sorted(k for k in obj if k in CONFIRMING)
    if confirming:
        problems.append(f"{where}: {'・'.join(confirming)} は書けない——取り込んだ行は利用者が回答するまで `確認中`・`未回答` で起票する")
    unknown = sorted(k for k in obj if k not in allowed and k not in CONFIRMING)
    if unknown:
        problems.append(f"{where}: 知らない鍵: {'・'.join(unknown)}")
    missing = sorted(required - set(obj))
    if missing:
        problems.append(f"{where}: 鍵が足りない: {'・'.join(missing)}")
    return not (confirming or unknown or missing)


def build_row(c: dict, where: str, snap: Path, label: str, problems: list[str]) -> dict[str, str] | None:
    before = len(problems)
    if not check_keys(c, CANDIDATE_KEYS | CANDIDATE_OPTIONAL, CANDIDATE_KEYS, where, problems):
        return None
    kind = c["kind"]
    if kind not in KINDS:
        problems.append(f"{where}: `kind` が {'・'.join(KINDS)} のどれでもない: {kind!r}")
    question = text_field(c, "question", where, problems)
    reason = text_field(c, "reason", where, problems)
    behavior = text_field(c, "code_behavior", where, problems)
    cost = c.get("cost", "")
    if not isinstance(cost, str) or "\n" in cost:
        problems.append(f"{where}: `cost` は 1 行の文字列")
        cost = ""
    options = c["options"]
    labels: list[str] = []
    if not isinstance(options, list) or len(options) < qa.MIN_OPTIONS:
        problems.append(f"{where}: `options` は {qa.MIN_OPTIONS} つ以上の文字列の並び")
    elif len(options) > 26:
        problems.append(f"{where}: `options` が多すぎる（26 まで）")
    else:
        for i, option in enumerate(options):
            if not isinstance(option, str) or not option.strip() or "\n" in option or qa.OPTION_SEPARATOR in option:
                problems.append(f"{where}.options[{i}]: 空でない 1 行の文字列で、` / ` を含めない: {option!r}")
        labels = [chr(ord("A") + i) for i in range(len(options))]
    recommend = c["recommend"]
    if labels and recommend not in labels + [qa.NO_RECOMMENDATION]:
        problems.append(f"{where}: `recommend` が選択肢のラベル（{'・'.join(labels)}）でも `{qa.NO_RECOMMENDATION}` でもない: {recommend!r}")
    places = locate(snap, c["code"], where, problems)
    if len(problems) != before:
        return None
    return {
        "No": "", "起票元": f"{SOURCE_NAME}（取り込み・{kind}。{label}）",
        "質問": f"{question}（コードではこうなっていた: {behavior}。{'、'.join(places)}）",
        "選択肢": qa.OPTION_SEPARATOR.join(f"{l}: {o.strip()}" for l, o in zip(labels, options)),
        "推奨": recommend, "推奨の理由": reason,
        "回答": qa.NO_ANSWER, "反映先": qa.NO_TARGET, "状態": PENDING, "費用への影響": cost.strip(),
    }


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def bare(question: str) -> str:
    """取り込んだ行の質問から、build_row が足した末尾の添え書き `（コードではこうなっていた: …）` を外した文。添え書きが無ければそのまま。"""
    at = question.rfind(CODE_NOTE)
    return question[:at] if at > 0 and question.rstrip().endswith("）") else question


def check_finding(f, where: str, snap: Path, canon: dict[str, bytes], problems: list[str]) -> str | None:
    before = len(problems)
    if not check_keys(f, FINDING_KEYS, FINDING_KEYS, where, problems):
        return None
    summary = text_field(f, "summary", where, problems)
    behavior = text_field(f, "code_behavior", where, problems)
    quote = text_field(f, "canon_quote", where, problems)
    path = f["canon"]
    if not isinstance(path, str) or path not in canon:
        problems.append(f"{where}: `canon` が正本（重ね合わせた全体）に無いファイル: {path!r}")
    elif quote and squash(quote) not in squash(canon[path].decode("utf-8", "replace")):
        problems.append(f"{where}: `canon_quote` が {path} に無い——正本に在る文をそのまま引く: {quote!r}")
    places = locate(snap, f["code"], where, problems)
    if len(problems) != before:
        return None
    return f"{summary}——正本 {path}「{quote}」／コード: {behavior}（{'、'.join(places)}）"


# ---------------------------------------------------------------- 基盤要件

def infra_findings(snap: Path, canon: dict[str, bytes]) -> tuple[list[str], list[str]]:
    """(食い違い, 照らしていないことの注記)。"""
    if INFRA_PATH not in canon:
        return [], [f"基盤要件の表（{INFRA_PATH}）が無い——基盤要件は照らしていない"]
    rows = list(csv.DictReader(io.StringIO(canon[INFRA_PATH].decode("utf-8-sig", "replace"), newline="")))
    decided = {}
    for row in rows:
        item, value, state = (row.get(k) or "" for k in ("項目", "決定", "状態"))
        if state.strip() in DECIDED_STATES and value.strip():
            decided[item.strip()] = value.strip()
    files = list(source_files(snap))
    texts: dict[Path, list[str]] = {}
    for rel in files:
        lines = read_lines(snap / rel)
        if lines is not None:
            texts[rel] = lines
    findings, notes = [], []
    for item, families in MARKERS.items():
        if item not in decided:
            notes.append(f"基盤要件の{item}が決まっていない——照らしていない")
            continue
        value = decided[item]
        mine = [name for name, word, _ in families if word.search(value)]
        if len(mine) != 1:
            notes.append(f"基盤要件の{item}「{value}」から種類を読めない——照らしていない")
            continue
        for name, _, marker in families:
            if name == mine[0]:
                continue
            hit = next(((rel, i + 1, m.group(0)) for rel, lines in texts.items() for i, line in enumerate(lines)
                        for m in [marker.search(line)] if m), None)
            if hit:
                findings.append(f"基盤要件の{item}: 正本は「{value}」（{INFRA_PATH}）、持ち込まれたコードは {name} を前提にしている"
                                f"（{hit[2]}: {hit[0]}:{hit[1]}）")
    if LANGUAGE_ITEM not in decided:
        notes.append(f"基盤要件の{LANGUAGE_ITEM}が決まっていない——照らしていない")
    else:
        value = decided[LANGUAGE_ITEM]
        mine = [ext for name, word, ext in LANGUAGES if word.search(value)]
        if len(mine) != 1:
            notes.append(f"基盤要件の{LANGUAGE_ITEM}「{value}」から種類を読めない——照らしていない")
        else:
            own = sum(1 for rel in files if rel.suffix in mine[0])
            for name, _, ext in LANGUAGES:
                found = [rel for rel in files if rel.suffix in ext]
                # 決定の言語のファイルより多いほかの言語を食い違いにする——同じ数以下（補助の数本・小さな試作の静的な JS）は数えない
                if ext != mine[0] and found and len(found) > own:
                    findings.append(f"基盤要件の{LANGUAGE_ITEM}: 正本は「{value}」（{INFRA_PATH}）、持ち込まれたコードは {name} で書かれている"
                                    f"（{found[0]} ほか {len(found)} 件）")
    return findings, notes


# ---------------------------------------------------------------- rows

def next_number(versions: list[tuple[int, Path]]) -> int:
    top = 0
    for _, root in versions:
        path = root / QA_PATH
        if not path.is_file():
            continue
        for row in csv.DictReader(io.StringIO(path.read_text(encoding="utf-8-sig"), newline="")):
            m = qa.NUMBER.fullmatch(row.get("No") or "")
            if m and m["mark"] == MARK:
                top = max(top, int(m.group(0).rsplit("-", 1)[1]))
    return top + 1


def rows(root: Path, candidates_path: Path, snap: Path, dry_run: bool) -> tuple[int, list[str]]:
    docs = root / "docs"
    if not docs.is_dir():
        raise Stop(f"{docs}: 正本の docs/ が無い")
    meta_path = snap / SOURCE_FILE
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        label = meta["label"]
    except (OSError, ValueError, KeyError, TypeError):
        raise Stop(f"{snap}: スナップショットでない（{SOURCE_FILE} が読めない——snapshot で作る）") from None
    try:
        problems, versions, _, canon = mv.merge(docs)
    except mv.Unreadable as e:
        raise Stop(str(e)) from None
    if problems:
        raise Stop("版を重ねられない:\n" + "\n".join(f"  {p}" for p in problems))
    target = versions[-1][1] / QA_PATH
    if target.exists():
        code, out = qa.check(target)
        if code != 0:
            raise Stop("作業中の版の Q&A 表が検査を通らない——先に直す:\n" + "\n".join(f"  {line}" for line in out))
        # 既にある表の BOM と改行を保つ——read_text(encoding="utf-8-sig") は BOM を落とし改行を \n に揃えるので、
        # そのまま書き戻すと既存の全行が差分になる。BOM は文字のまま先頭に残し、書くときもそのまま書く
        existing = target.read_bytes().decode("utf-8")
    else:
        existing = ",".join(qa.COLUMNS) + "\n"
    eol = "\r\n" if existing.split("\n", 1)[0].endswith("\r") else "\n"
    try:
        data = json.loads(candidates_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Stop(f"{candidates_path}: JSON として読めない（{e}）") from None

    errors: list[str] = []
    new_rows: list[dict[str, str]] = []
    findings: list[str] = []
    if check_keys(data, TOP_KEYS, TOP_KEYS, "候補の JSON", errors):
        if not isinstance(data["candidates"], list) or not isinstance(data["findings"], list):
            errors.append("候補の JSON: `candidates` と `findings` は並び（無ければ []）")
        else:
            # 既にある行の質問は、取り込みの添え書きを外した文で照らす——同じ候補で当て直したときに重ねて足さない
            asked = {squash(bare(r["質問"])) for r in csv.DictReader(io.StringIO(canon.get(QA_PATH, b"").decode("utf-8-sig"), newline=""))}
            for i, c in enumerate(data["candidates"]):
                row = build_row(c, f"candidates[{i}]", snap, label, errors)
                if row is None:
                    continue
                if squash(c["question"]) in asked:
                    errors.append(f"candidates[{i}]: 同じ質問が既にある: {c['question']!r}")
                    continue
                asked.add(squash(c["question"]))
                new_rows.append(row)
            for i, f in enumerate(data["findings"]):
                line = check_finding(f, f"findings[{i}]", snap, canon, errors)
                if line:
                    findings.append(line)
    if errors:
        return 1, ["候補の JSON が決まりに反する（何も書いていない）:"] + [f"  {e}" for e in errors]

    start = next_number(versions)
    for offset, row in enumerate(new_rows):
        row["No"] = f"Q-{MARK}-{start + offset:03d}"
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator=eol)
    for row in new_rows:
        writer.writerow([row[c] for c in qa.COLUMNS])
    text = existing if existing.endswith("\n") else existing + eol
    text += buffer.getvalue()
    payload = text.encode("utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "qa.csv"
        probe.write_bytes(payload)
        code, out = qa.check(probe)
    if code != 0:
        return 1, ["足した後の表が check-qa-csv.py を通らない（何も書いていない）:"] + [f"  {line}" for line in out]

    infra, notes = infra_findings(snap, canon)
    findings = infra + findings
    report = []
    if dry_run:
        report.append(f"書いていない（--dry-run）。{target} に足すはずの行 {len(new_rows)} 件:")
        report.append(buffer.getvalue().replace("\r\n", "\n").rstrip("\n"))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".intake-tmp")
        tmp.write_bytes(payload)
        os.replace(tmp, target)
        numbers = "・".join(r["No"] for r in new_rows) or "無し"
        report.append(f"{target} に {len(new_rows)} 行を足した（{numbers}。どれも `確認中`・`未回答`——利用者が回答するまで確定しない）")
    report.append(f"食い違い: {len(findings)} 件")
    report.extend(f"  - {line}" for line in findings)
    report.extend(f"  （{note}）" for note in notes)
    return (3 if findings else 0), report


# ---------------------------------------------------------------- 入口

def main(argv: list[str]) -> int:
    usage = (__doc__ or "").split("\n\n", 2)[1] if __doc__ else "usage: intake-code.py snapshot|rows …"
    args = list(argv)
    try:
        if args[:1] == ["snapshot"]:
            remote = "origin"
            if "--remote" in args:
                i = args.index("--remote")
                if i + 1 >= len(args):
                    raise Stop("--remote に名前が無い")
                remote = args[i + 1]
                del args[i:i + 2]
            if len(args) != 4:
                raise Stop(usage)
            for line in snapshot(Path(args[1]).resolve(), args[2], Path(args[3]).resolve(), remote):
                print(line)
            return 0
        if args[:1] == ["rows"]:
            dry_run = "--dry-run" in args
            args = [a for a in args if a != "--dry-run"]
            if len(args) != 4:
                raise Stop(usage)
            code, report = rows(Path(args[1]).resolve(), Path(args[2]), Path(args[3]).resolve(), dry_run)
            print("\n".join(report), file=sys.stderr if code == 1 else sys.stdout)
            return code
        raise Stop(usage)
    except Stop as e:
        print(f"{e}\n判定していない（何も書いていない）", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 — 想定外の例外はトレースバックの 1 にしない
        print(f"想定外の例外: {type(e).__name__}: {e}\n判定していない", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
