#!/usr/bin/env python3
r"""外部の profile（パターンの持ち主のリポジトリに置いた `spec-profile/<名前>/`）を、**中身を知らずに**読む（#1455）。

    python3 <spec-loop の根>/scripts/external-profile.py find  --repo <リポジトリ> [--clone <パス>] [--project <案件の根>]
    python3 <spec-loop の根>/scripts/external-profile.py check --repo <リポジトリ> --profile <名前> --tag <タグ> --layer <層>=<下限>,<上限> … [--clone <パス>] [--project <案件の根>]
    python3 <spec-loop の根>/scripts/external-profile.py diff  --repo <リポジトリ> --profile <名前> --old <タグ> --new <タグ> --layer <層>=<下限>,<上限> … [--clone <パス>] [--project <案件の根>]

**読むだけ**——clone にも案件にも書かない。clone では `git rev-parse`・`git ls-tree`・`git cat-file` だけを走らせ、checkout・fetch をしない。

**決まり（置き場所・`profile.csv` の列・層の表の先頭 3 列・形式の版の形と範囲・リンクの書き方・探し方と宣言の行）の原本は
`references/external-profile.md`**（このスクリプトの定数はその写しで、このリポジトリのテストが突き合わせる）。
platform-spec と screen-spec はこのファイルを `importlib` で読み込んで、下の関数を使う（写さない）。層ごとの値の意味は、使う側が持つ。

## 何をするか

- **`find`**——リポジトリ（`<持ち主>/<名前>`）の手元の clone を探す。順は 引数 `--clone` → 環境変数 `SPEC_PROFILE_CLONE` → 案件の `CLAUDE.md` の
  `外部の profile の clone: <リポジトリ> <パス>` の行。**上が在れば下を見ない。上が指した場所が git のリポジトリでなければ、下に落ちずに 4。**
- **`check`**——タグの時点の `spec-profile/<名前>/profile.csv` を読み、`--layer` で名指しした層ごとに、形式の版が範囲（下限を含み上限を含まない）に入るかを見て、
  層の表を読み、`リンク` がリポジトリの中を指すならタグの時点に在るかを見る。
- **`diff`**——2 つのタグの層の表を ID を鍵に比べ、変わった・消えた・足した行と、新しいタグで切れているリンクを出す。

使う側が読み込む関数: `find_clone`・`resolve_tag`・`read_profile`・`read_layer`・`check_links`・`diff_layers`・`in_range`・`parse_version`。
判定できなかったときは `Undetermined`、求めた層が profile に無いときは `LayerMissing` を投げる。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 見つかった（`find`）・切れたリンクが無い（`check`）・差分が無い（`diff`） |
| 1 | 切れたリンクがある（`check`）・差分がある（`diff`） |
| 2 | 引数が違う |
| 3 | 求めた層が profile に無い（「無い」） |
| 4 | 判定できなかった——clone が見つからない・git のリポジトリでない・タグが無い・形式の版が範囲の外か読めない・表の形が違う |

**複数の層を求めて結果が混じるときは 4 > 1 > 3 > 0 の順で強いほうを返す**（層ごとの結果は出力に出る）。

## 何を守り、何を守らないか

守る:

- **引数で名指しした clone があれば、環境変数と `CLAUDE.md` を見ない。**
- **環境変数があれば、`CLAUDE.md` の行を見ない。**
- **名指し（引数・環境変数・行）が git のリポジトリでなければ、次の探し方に落ちずに 4**——黙って別の clone を読まない。
- **名指しが git のリポジトリの中のサブディレクトリ（リポジトリの根でない）なら 4**——外のリポジトリを clone として読まない。根かどうかは同じファイルか（`os.path.samefile`）で比べ、パスの大文字・小文字の書き方の違いでは 4 にしない。
- **bare のリポジトリは、git のディレクトリそのものを根として読む。**
- **git がリポジトリの場所を決める環境変数（`git rev-parse --local-env-vars` の全部。`GIT_DIR`・`GIT_OBJECT_DIRECTORY` など）を子の git に渡さない**——フックの中などで走らせても、名指しの clone を読む。
- **clone の置き換え（`refs/replace`）を効かせない**（`--no-replace-objects`）——タグに無い中身を読まない。
- **どこにも見つからなければ 4**（「無い」の 3 にしない）。
- **`CLAUDE.md` の行は、ほかのリポジトリの行を使わない**——リポジトリの名前が一致する行だけ。
- **同じリポジトリの行が 2 行以上なら 4**——どれを使うか決めない。
- **`CLAUDE.md` のコードフェンスの中の行を宣言と読まない**（読み方は `check-tlc.py` の `scan_declarations`）。
- **タグが無ければ 4**——ブランチや同じ名前の別の参照に落ちない（`refs/tags/` だけを見る）。
- **タグの名前に版の記法（`v2~1`・`v2^` など、参照の名前に使えない形）を書いたら 4**——たどった先のタグの無いコミットを読まない。
- **作業ツリーではなくタグの時点の中身を読む**——作業ツリーが違っても、別のブランチに居ても、タグの内容を返す。
- **clone の作業ツリー・HEAD・参照を変えない**（`rev-parse`・`ls-tree`・`cat-file` だけを走らせる）。
- **形式の版が下限より小さければ 4、上限と同じか大きければ 4**（下限は含み、上限は含まない）。
- **形式の版を桁ごとの数で比べる**——`1.10` は `1.9` より大きい。足りない桁は 0 として比べる（`1` と `1.0` は同じ）。
- **数字と `.` 以外の形式の版は 4。**
- **ASCII でない数字（全角の `１` など）の形式の版も 4。**
- **求めた層が `profile.csv` に無ければ 3**（判定できなかったの 4 にしない）。
- **`profile.csv` の見出しが `層,形式の版,ファイル,重ねる先` でなければ 4。**
- **同じ層が 2 行あれば 4。**
- **層の表の先頭 3 列が `ID,要約,リンク` でなければ 4。**
- **層の表の見出しに同じ列の名前が 2 つあれば 4**——後ろの列が前の列（`リンク` を含む）を黙って上書きしない。
- **ID が空なら 4。**
- **ID が同じ層の中で重なれば 4**（層のファイルが複数でも、層の中で重なれば 4）。
- **列の数が見出しと合わない行があれば 4。**
- **`ファイル` がどのファイルにも当たらなければ 4。**
- **`ファイル` が profile のディレクトリの外を指すなら 4**（そこに表が在っても読まない）。
- **層の中身（先頭 3 列より後ろ）を解釈しない**——列の名前と値をそのまま持ち、比べるだけ。
- **先頭 3 列より後ろの列だけが違う行も「変わった」に出す。**
- **古いタグに在って新しいタグに無い ID を「消えた」に出す。**
- **新しいタグだけに在る ID を「足した」に出す。**
- **`リンク` のファイルがタグの時点に無ければ切れた**（作業ツリーに在っても）。
- **`リンク` の `#節` が、指す `.md` の見出しの id のどれにも当たらなければ切れた**（id は GitHub と同じ作り方。重なった見出しは `-1`・`-2`）。
- **見出しの id は、コードフェンスの中の `#` の行から作らない。**
- **BOM つきの `.md` の先頭の見出しも id にする。**
- **リポジトリの外を指す `リンク`（`..` で根より上）は切れた。**
- **外の URL（`https:` などのスキームを持つ `リンク`）は見ない**——切れたにしない。
- **百分率で符号化したパスと節（GitHub の URL からコピーした形）は、戻してから照らす。**
- **`diff` の切れたリンクは、新しいタグの時点で見る。**
- **BOM つきの CSV の先頭の列を読む。**
- **想定外の例外（git が無い・パスに NUL など）は 4**——1（切れた・差分あり）と取り違えない。

守らない:

- **`gh` で取りに行かない**——手元の clone が無ければ 4（作るかは仕様の穴として確認の Issue に残した）。
- **環境変数 `SPEC_PROFILE_CLONE` はリポジトリを問わず効く**——2 つのリポジトリを使う案件で置くと、両方が同じ clone を読む（タグが無ければ 4）。
- **clone が本当にそのリポジトリの clone か（`origin` の URL）を見ない**——名指しを信じる。
- **見出しの id は ATX 見出し（`#` で始まる行）からだけ作る**——setext 見出し（下線）・HTML のアンカー（`<a id>`）・見出しの中のリンクの記法の扱いは GitHub と違いうる。
- **`.md` でないファイルの `#節` は見ない**——ファイルが在れば切れたにしない。
- **層の表の後ろの列の値が何を意味するか**（語彙・既定・照合）を見ない——使う側が持つ。
- **`重ねる先` が組み込みの profile の名前として在るかを見ない**——使う側が持つ。
- **タグが署名されているか・動いたか（同じ名前で付け直された）を見ない。**
"""

import argparse
import csv
import fnmatch
import importlib.util
import io
import os
import posixpath
import re
import subprocess
import sys
from urllib.parse import unquote
from dataclasses import dataclass, field
from pathlib import Path

# check-tlc.py を読み込むときに `__pycache__` を書かない（このスクリプトはファイルを 1 つも書かない）
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tlc = _load("spec_loop_check_tlc_for_profile", "check-tlc.py")

# ---- `references/external-profile.md` の写し
PROFILE_ROOT = "spec-profile"
PROFILE_FILE = "profile.csv"
PROFILE_COLUMNS = ("層", "形式の版", "ファイル", "重ねる先")
LAYER_HEAD = ("ID", "要約", "リンク")
ENV_CLONE = "SPEC_PROFILE_CLONE"
DECL_KEY = "外部の profile の clone:"

EXIT_OK = 0
EXIT_FOUND = 1
EXIT_USAGE = 2
EXIT_ABSENT = 3
EXIT_UNKNOWN = 4

VERSION_RE = re.compile(r"[0-9]+(?:\.[0-9]+)*")
SCHEME_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
FENCE_RE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
HEADING_RE = re.compile(r" {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*#*[ \t]*$")


class Undetermined(Exception):
    """判定できなかった（4）。"""


class LayerMissing(Exception):
    """求めた層が profile に無い（3）。"""


@dataclass
class ProfileRow:
    layer: str
    version: str
    file: str
    base: str


@dataclass
class Layer:
    name: str
    version: str
    base: str
    files: list[str]
    rows: dict[str, dict[str, str]] = field(default_factory=dict)  # ID → {列: 値}（先頭 3 列も含む）


# ---- 探し方


GIT_ENV_FALLBACK = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY",
                    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_REPLACE_REF_BASE", "GIT_CONFIG_PARAMETERS", "GIT_NAMESPACE")
_drop_cache: list = []


def _drop_vars() -> set:
    """子の git に渡さない環境変数（`git rev-parse --local-env-vars` と、取れなかったときの既定の和）。"""
    if not _drop_cache:
        proc = subprocess.run(["git", "rev-parse", "--local-env-vars"], capture_output=True, text=True,
                              env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
        _drop_cache.append(set(proc.stdout.split()) | set(GIT_ENV_FALLBACK))
    return _drop_cache[0]


def _child_env() -> dict:
    drop = _drop_vars()
    return {k: v for k, v in os.environ.items() if k not in drop}


def _is_repo(path: Path) -> bool:
    """path が git のリポジトリの根か（bare なら git のディレクトリそのもの）。"""
    env = _child_env()
    bare = subprocess.run(["git", "-C", str(path), "rev-parse", "--is-bare-repository"], capture_output=True, text=True, env=env)
    if bare.returncode != 0:
        return False
    key = "--absolute-git-dir" if bare.stdout.strip() == "true" else "--show-toplevel"
    top = subprocess.run(["git", "-C", str(path), "rev-parse", key], capture_output=True, text=True, env=env)
    return top.returncode == 0 and os.path.samefile(top.stdout.strip(), path)


def find_clone(repo: str, clone: str | None = None, project: str | Path | None = None, env=None) -> tuple[Path, str]:
    """(clone の絶対パス, 出所)。見つからない・名指しが git のリポジトリでなければ Undetermined。"""
    env = os.environ if env is None else env
    if clone:
        return _named(Path(clone), "引数 --clone")
    if env.get(ENV_CLONE):
        return _named(Path(env[ENV_CLONE]), f"環境変数 {ENV_CLONE}")
    root = Path(project) if project else Path.cwd()
    md = root / "CLAUDE.md"
    try:
        text = md.read_text(encoding="utf-8").removeprefix("\ufeff")
    except (FileNotFoundError, NotADirectoryError):
        text = ""
    except (OSError, ValueError) as e:
        raise Undetermined(f"{md} を読めない: {e}")
    hits = []
    for value in tlc.scan_declarations(text, (DECL_KEY,))[DECL_KEY]:
        parts = value.split(None, 1)
        if len(parts) == 2 and parts[0] == repo:
            hits.append(parts[1].strip())
    if len(hits) > 1:
        raise Undetermined(f"{md} に `{DECL_KEY} {repo} …` の行が {len(hits)} 行ある（どれを使うか決めない）")
    if hits:
        path = Path(hits[0])
        if not path.is_absolute():
            path = root / path
        return _named(path, f"{md.name} の `{DECL_KEY}` の行")
    raise Undetermined(
        f"{repo} の手元の clone が見つからない（引数 --clone・環境変数 {ENV_CLONE}・{md} の `{DECL_KEY} {repo} <パス>` のどれも無い）。"
        f" clone を作って（例: git clone <URL> <パス>）、案件の CLAUDE.md に `{DECL_KEY} {repo} <パス>` を書く。gh では取りに行かない")


def _named(path: Path, source: str) -> tuple[Path, str]:
    path = path.expanduser().resolve()
    if not path.is_dir() or not _is_repo(path):
        raise Undetermined(f"{source} が指す {path} は git のリポジトリ（の根）でない（次の探し方には進まない）")
    return path, source


# ---- タグの時点の読み出し


def _git(clone: Path, *args: str, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--no-replace-objects", "-C", str(clone), *args], input=data, capture_output=True, env=_child_env())


def resolve_tag(clone: Path, tag: str) -> str:
    """タグが指すコミットの SHA。タグが無ければ Undetermined（ブランチには落ちない）。"""
    if not tag or tag.startswith("-"):
        raise Undetermined(f"タグの名前が違う: {tag!r}")
    if _git(clone, "check-ref-format", f"refs/tags/{tag}").returncode != 0:
        raise Undetermined(f"タグの名前が参照の名前に使えない形（版の記法はたどらない）: {tag!r}")
    proc = _git(clone, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}")
    if proc.returncode != 0:
        raise Undetermined(f"{clone} にタグ {tag} が無い（手元の clone で git fetch --tags してから読み直す）")
    return proc.stdout.decode().strip()


def list_files(clone: Path, commit: str) -> set[str]:
    """コミットの木のファイルのパス（リポジトリの根から）。"""
    proc = _git(clone, "ls-tree", "-r", "-z", "--full-tree", "--name-only", commit)
    if proc.returncode != 0:
        raise Undetermined(f"git ls-tree が失敗した: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return {p.decode("utf-8", "surrogateescape") for p in proc.stdout.split(b"\0") if p}


def read_blob(clone: Path, commit: str, path: str) -> bytes:
    proc = _git(clone, "cat-file", "blob", f"{commit}:{path}")
    if proc.returncode != 0:
        raise Undetermined(f"{path} を読めない: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout


def _csv_rows(raw: bytes, where: str) -> list[list[str]]:
    try:
        text = raw.decode("utf-8").removeprefix("\ufeff")
    except UnicodeDecodeError as e:
        raise Undetermined(f"{where} が UTF-8 でない: {e}")
    try:
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as e:
        raise Undetermined(f"{where} を CSV として読めない: {e}")
    return [r for r in rows if r]


def _profile_dir(name: str) -> str:
    if not name or "/" in name or name in (".", ".."):
        raise Undetermined(f"profile の名前が違う: {name!r}")
    return f"{PROFILE_ROOT}/{name}"


def read_profile(clone: Path, commit: str, name: str) -> dict[str, ProfileRow]:
    """`profile.csv` を読む。{層: ProfileRow}。"""
    where = f"{_profile_dir(name)}/{PROFILE_FILE}"
    files = list_files(clone, commit)
    if where not in files:
        raise Undetermined(f"{where} がその時点に無い（profile の名前かタグが違う）")
    rows = _csv_rows(read_blob(clone, commit, where), where)
    if not rows or tuple(rows[0]) != PROFILE_COLUMNS:
        raise Undetermined(f"{where} の見出しが `{','.join(PROFILE_COLUMNS)}` でない: {rows[0] if rows else '（空）'}")
    out: dict[str, ProfileRow] = {}
    for i, r in enumerate(rows[1:], start=2):
        if len(r) != len(PROFILE_COLUMNS):
            raise Undetermined(f"{where} の {i} 行目の列の数が {len(r)}（見出しは {len(PROFILE_COLUMNS)}）")
        layer, version, file, base = (c.strip() for c in r)
        if not layer:
            raise Undetermined(f"{where} の {i} 行目の層が空")
        if layer in out:
            raise Undetermined(f"{where} に層 {layer} が 2 行ある")
        out[layer] = ProfileRow(layer, version, file, base)
    return out


# ---- 形式の版


def parse_version(text: str) -> tuple[int, ...]:
    if not VERSION_RE.fullmatch(text or ""):
        raise Undetermined(f"形式の版が数字を `.` で区切った形でない: {text!r}")
    return tuple(int(p) for p in text.split("."))


def _pad(a: tuple[int, ...], n: int) -> tuple[int, ...]:
    return a + (0,) * (n - len(a))


def in_range(version: str, low: str, high: str) -> bool:
    """下限を含み、上限を含まない。足りない桁は 0 として比べる。"""
    v, lo, hi = parse_version(version), parse_version(low), parse_version(high)
    n = max(len(v), len(lo), len(hi))
    v, lo, hi = _pad(v, n), _pad(lo, n), _pad(hi, n)
    return lo <= v < hi


# ---- 層の表


def _safe_rel(path: str) -> str | None:
    """リポジトリの中の正規化したパス。外へ出るなら None。"""
    norm = posixpath.normpath(path)
    if norm.startswith("/") or norm == ".." or norm.startswith("../"):
        return None
    return "" if norm == "." else norm


def read_layer(clone: Path, commit: str, name: str, layer: str, low: str, high: str) -> Layer:
    """層の表を読む。形式の版が範囲の外なら Undetermined、層が無ければ LayerMissing。"""
    profile = read_profile(clone, commit, name)
    if layer not in profile:
        raise LayerMissing(f"層 {layer} が {_profile_dir(name)}/{PROFILE_FILE} に無い（在る層: {', '.join(profile) or 'なし'}）")
    row = profile[layer]
    if not in_range(row.version, low, high):
        raise Undetermined(f"層 {layer} の形式の版 {row.version} が、受け付ける範囲（{low} 以上 {high} 未満）の外")
    base_dir = _profile_dir(name)
    rel = _safe_rel(row.file) if row.file and not row.file.startswith("/") else None
    if not rel:
        raise Undetermined(f"層 {layer} の `ファイル` がリポジトリの profile の中を指していない: {row.file!r}")
    pattern = f"{base_dir}/{rel}"
    files = list_files(clone, commit)
    if any(ch in rel for ch in "*?["):
        depth = pattern.count("/")
        matched = sorted(p for p in files if p.count("/") == depth and fnmatch.fnmatchcase(p, pattern))
    else:
        matched = [pattern] if pattern in files else []
    if not matched:
        raise Undetermined(f"層 {layer} の `ファイル` {row.file} に当たるファイルがその時点に無い")
    result = Layer(layer, row.version, row.base, matched)
    for path in matched:
        rows = _csv_rows(read_blob(clone, commit, path), path)
        if not rows or tuple(rows[0][:3]) != LAYER_HEAD:
            raise Undetermined(f"{path} の先頭の列が `{','.join(LAYER_HEAD)}` でない: {rows[0][:3] if rows else '（空）'}")
        head = rows[0]
        if len(set(head)) != len(head):
            raise Undetermined(f"{path} の見出しに同じ列の名前が 2 つある: {head}")
        for i, r in enumerate(rows[1:], start=2):
            if len(r) != len(head):
                raise Undetermined(f"{path} の {i} 行目の列の数が {len(r)}（見出しは {len(head)}）")
            rid = r[0].strip()
            if not rid:
                raise Undetermined(f"{path} の {i} 行目の ID が空")
            if rid in result.rows:
                raise Undetermined(f"層 {layer} に ID {rid} が 2 行ある（{path} の {i} 行目）")
            result.rows[rid] = dict(zip(head, r))
    return result


# ---- リンク


def heading_ids(markdown: str) -> set[str]:
    """ATX 見出しから GitHub と同じ作り方の id（コードフェンスの外だけ）。"""
    ids: set[str] = set()
    seen: dict[str, int] = {}
    fence = None
    for line in markdown.splitlines():
        m = FENCE_RE.match(line)
        if fence is None:
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence = (m.group(1)[0], len(m.group(1)))
                continue
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and not m.group(2).strip():
                fence = None
            continue
        h = HEADING_RE.match(line)
        if not h:
            continue
        slug = re.sub(r"[^\w\- ]", "", (h.group(2) or "").strip().lower()).replace(" ", "-")
        n = seen.get(slug, 0)
        ids.add(slug if n == 0 else f"{slug}-{n}")
        seen[slug] = n + 1
    return ids


def check_links(clone: Path, commit: str, layer: Layer) -> list[tuple[str, str, str]]:
    """切れたリンク。[(ID, リンク, 理由)]。外の URL と空のリンクは見ない。"""
    files = list_files(clone, commit)
    dirs = {posixpath.dirname(p) for p in files}
    for d in list(dirs):
        while d:
            d = posixpath.dirname(d)
            dirs.add(d)
    cache: dict[str, set[str]] = {}
    broken = []
    for rid, row in layer.rows.items():
        link = row.get("リンク", "").strip()
        if not link or SCHEME_RE.match(link):
            continue
        path, _, anchor = link.partition("#")
        path, anchor = unquote(path), unquote(anchor)
        rel = _safe_rel(path.lstrip("/")) if path.strip("/") else None
        if rel is None:
            broken.append((rid, link, "リポジトリの中のファイルを指していない" if not path.strip("/") else "リポジトリの外を指す"))
            continue
        if rel not in files and rel not in dirs:
            broken.append((rid, link, "ファイルがその時点に無い"))
            continue
        if anchor and rel.endswith(".md") and rel in files:
            if rel not in cache:
                cache[rel] = heading_ids(read_blob(clone, commit, rel).decode("utf-8", "replace").removeprefix("\ufeff"))
            if anchor not in cache[rel]:
                broken.append((rid, link, f"節 #{anchor} が {rel} の見出しに無い"))
    return broken


# ---- 差分


def diff_layers(old: Layer | None, new: Layer | None, broken_new: list[tuple[str, str, str]]) -> dict[str, list]:
    """ID を鍵にした差分。{変わった: [(ID, {列: (古い, 新しい)})], 消えた: [ID], 足した: [ID], 切れた: [(ID, リンク, 理由)]}。"""
    o = old.rows if old else {}
    n = new.rows if new else {}
    changed = []
    for rid in sorted(set(o) & set(n)):
        cols = sorted(set(o[rid]) | set(n[rid]))
        delta = {c: (o[rid].get(c), n[rid].get(c)) for c in cols if o[rid].get(c) != n[rid].get(c)}
        if delta:
            changed.append((rid, delta))
    return {
        "変わった": changed,
        "消えた": sorted(set(o) - set(n)),
        "足した": sorted(set(n) - set(o)),
        "切れた": list(broken_new),
    }


# ---- CLI


def _parse_layers(specs: list[str]) -> list[tuple[str, str, str]]:
    out = []
    for s in specs:
        name, eq, rng = s.partition("=")
        low, comma, high = rng.partition(",")
        if not (name and eq and comma and low and high):
            raise ValueError(f"--layer は <層>=<下限>,<上限>: {s!r}")
        parse_version(low)
        parse_version(high)
        out.append((name, low, high))
    return out


def _worst(codes: list[int]) -> int:
    for c in (EXIT_UNKNOWN, EXIT_FOUND, EXIT_ABSENT):
        if c in codes:
            return c
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except Exception as e:  # 想定外の例外は判定できなかった（4）——1（切れた・差分あり）と取り違えない
        print(f"判定できなかった（想定外の例外）: {type(e).__name__}: {e}")
        return EXIT_UNKNOWN


def _main(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(description="外部の profile を中身を知らずに読む（#1455）")
    sub = p.add_subparsers(dest="cmd")
    for cmd in ("find", "check", "diff"):
        s = sub.add_parser(cmd)
        s.add_argument("--repo", required=True)
        s.add_argument("--clone")
        s.add_argument("--project")
        if cmd != "find":
            s.add_argument("--profile", required=True)
            s.add_argument("--layer", action="append", required=True)
        if cmd == "check":
            s.add_argument("--tag", required=True)
        if cmd == "diff":
            s.add_argument("--old", required=True)
            s.add_argument("--new", required=True)
    try:
        args = p.parse_args(argv)
        if not args.cmd:
            p.print_usage(sys.stderr)
            return EXIT_USAGE
        layers = _parse_layers(args.layer) if args.cmd != "find" else []
    except SystemExit:
        return EXIT_USAGE
    except (ValueError, Undetermined) as e:
        print(f"引数が違う: {e}", file=sys.stderr)
        return EXIT_USAGE

    try:
        clone, source = find_clone(args.repo, args.clone, args.project)
    except Undetermined as e:
        print(f"判定できなかった: {e}")
        return EXIT_UNKNOWN
    print(f"clone: {clone}（出所: {source}）")
    if args.cmd == "find":
        return EXIT_OK

    codes = []
    if args.cmd == "check":
        try:
            commit = resolve_tag(clone, args.tag)
        except Undetermined as e:
            print(f"判定できなかった: {e}")
            return EXIT_UNKNOWN
        for name, low, high in layers:
            try:
                layer = read_layer(clone, commit, args.profile, name, low, high)
                broken = check_links(clone, commit, layer)
            except LayerMissing as e:
                print(f"[{name}] 無い: {e}")
                codes.append(EXIT_ABSENT)
                continue
            except Undetermined as e:
                print(f"[{name}] 判定できなかった: {e}")
                codes.append(EXIT_UNKNOWN)
                continue
            print(f"[{name}] 形式の版 {layer.version}・{len(layer.rows)} 行・切れたリンク {len(broken)} 件")
            for rid, link, why in broken:
                print(f"  切れた: {rid} {link}（{why}）")
            codes.append(EXIT_FOUND if broken else EXIT_OK)
        return _worst(codes)

    try:
        old_commit, new_commit = resolve_tag(clone, args.old), resolve_tag(clone, args.new)
    except Undetermined as e:
        print(f"判定できなかった: {e}")
        return EXIT_UNKNOWN
    for name, low, high in layers:
        try:
            got = []
            for commit in (old_commit, new_commit):
                try:
                    got.append(read_layer(clone, commit, args.profile, name, low, high))
                except LayerMissing:
                    got.append(None)
            old, new = got
            if old is None and new is None:
                raise LayerMissing(f"層 {name} がどちらのタグの profile にも無い")
            broken = check_links(clone, new_commit, new) if new else []
        except LayerMissing as e:
            print(f"[{name}] 無い: {e}")
            codes.append(EXIT_ABSENT)
            continue
        except Undetermined as e:
            print(f"[{name}] 判定できなかった: {e}")
            codes.append(EXIT_UNKNOWN)
            continue
        d = diff_layers(old, new, broken)
        print(f"[{name}] 変わった {len(d['変わった'])}・消えた {len(d['消えた'])}・足した {len(d['足した'])}・切れた {len(d['切れた'])}")
        for rid, delta in d["変わった"]:
            print(f"  変わった: {rid}（{', '.join(delta)}）")
        for rid in d["消えた"]:
            print(f"  消えた: {rid}")
        for rid in d["足した"]:
            print(f"  足した: {rid}")
        for rid, link, why in d["切れた"]:
            print(f"  切れた: {rid} {link}（{why}）")
        codes.append(EXIT_FOUND if any(d.values()) else EXIT_OK)
    return _worst(codes)


if __name__ == "__main__":
    sys.exit(main())
