#!/usr/bin/env python3
"""spec-loop の MkDocs の雛形（`init-mkdocs.py` と、雛形のフック `spec_loop_pages.py`）の回帰テスト。

    python3 scripts/test-init-mkdocs.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/init-mkdocs.py` と `plugins/spec-loop/templates/mkdocs/`）。
ここで見るのは:

1. **写し方**——空の根には雛形をすべて（`gitignore` は `.gitignore` として）バイトどおりに写す。
   **`mkdocs.yml`・`mkdocs.yaml` が在れば何も写さない。** 在るファイル（シンボリックリンク・壊れたリンクを含む）は 1 バイトも変えず、
   `pyproject.toml`・`.gitignore` が在れば足りない依存・行を出力で示す。`--dry-run` は何も書かない。根がディレクトリでなければ 2。
   `mkdocs.yml` は最後に写す。行き先の親がファイルなら 2 で止まり（`mkdocs.yml` は書かない）、直して再実行すれば残りが写る。
   書き込みが途中で失敗しても（ファイルの大きさの上限で切る）切れたファイルも一時ファイルも残さず、再実行すれば残りが写る。
   **リンクを作れないとき**（`os.link` を差し替えて `ENOTSUP`（macOS）・`EPERM`（Linux の vfat）を出す——FAT32 のイメージを作れない CI でも回る）も雛形をすべて写し、
   確かめた後に作られたファイルは上書きせず、途中で書けなければ切れたファイルを残さない。それを消すのにも失敗したら
   （`Path.unlink` を差し替える）そう出力し、書けなかった理由のほうで 2。リンクと関係ない失敗（`EACCES`）は 2。
   写したファイルの権限は umask に従う（リンクの経路でも退路でも）。
   雛形の中の `__pycache__` は写さない。
2. **フックの描き方**——版ごとの節を番号の順（`v10` は `v2` の後）に、表の行をすべて、版をまたいで一意なアンカーで描く。
   セルの HTML と Markdown の記号（`&`・`\\`・`{` `}` を含む）・`|`・改行（`\\r` を含む）をエスケープする。
   アンカーに使えない文字（空白・`=`・`(`）は `-` にする（`No` の文字が見出しの属性にならない）。`qa.csv` の無い版は飛ばして次の版を描く。CSV の文字は表のセルにだけ置き、
   行頭の `!!! `・字下げ・`1. ` をブロックの記法にしない。空の `費用への影響` は行を出さない。
   BOM つきの表を読む。空白だけの行は読み飛ばし、列の足りない行は空で埋める。回答の `未回答 ` は未回答と数える。
   読めない表・見出しの違う表・知らない印は**警告**（`mkdocs` のロガー。`--strict` で落ちる）とページ上の注意書き。
   表が 1 つも無ければそう書き、警告は出さない。印の無いページは変えない。
   **本文の Q&A の番号**は、描いた後の HTML（`on_page_content`）で、`v1`〜ページの版のうちその番号を持つ最も新しい版の
   アンカーへのリンクにする（版の外のページはすべての版から。リンク先は `File.url_relative_to`——ここでは
   `use_directory_urls: false` の MkDocs と同じ値を返す偽物で当てる）。表のセルにも掛ける。見出し（容れ物の中・大文字の要素名も）・
   コード・リンク・`kbd`・`samp`・`script`・`style`・`textarea` の中と、属性（値の中の `>` を含む）・コメント・CDATA は変えない。
   変えない要素の後ろ・余分な閉じタグの後ろ・自己閉じの `<code/>` の後ろは置き換える。
   リンクにする版の表に無い番号はリンクにせず 1 度だけ警告し、警告は見た版の範囲を言う。読めない表があっても落ちず、他の版でリンクにする。
   空白つきの `No` はアンカーと合わないのでリンクにせず警告する。前後が英数字・`-`・`_` の `Q-` は番号でない。
   Q&A 表のページ（印を外せば掛かる）と、`qa.md` の無いサイトは変えない。
3. **写しの突き合わせ**——フックの列名・状態・印は `check-qa-csv.py` の定数と同じ（フックは正本リポジトリへ写されて
   単独で動くので import できず、写しを持つ）。
4. **重ね合わせに混ざらない**——雛形を写した正本で `merge-versions.py` が通り、出力に表示用のファイルが入らない。
5. **決まりの原本（`references/tree.md`）の「ドキュメントのツール」の節が、写し方のコマンドを載せている。**
   本文の番号の書き方は `references/qa-csv.md` の「本文での番号」にあり、`tree.md` がそこを指している。

**`mkdocs build` は走らせない**（CI に MkDocs と Material の組を入れていない）。実際に組んで表が出ることは
dev-loop の検証で見る（#266 の計画ファイル）。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
"""
from __future__ import annotations

import contextlib
import errno
import importlib.util
import io
import logging
import os
import posixpath
import resource
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
INIT = Path("scripts") / "init-mkdocs.py"
HOOK = Path("templates") / "mkdocs" / "hooks" / "spec_loop_pages.py"
REFERENCE = PLUGIN / "references" / "tree.md"

HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
# 前の形（spec-loop 0.17.0 まで）の見出し——推奨の 2 列が無い
OLD_HEADER = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
QA_V1 = HEADER + (
    "Q-001,要求確定,割引は <b>A</b> | B？,A: なし / B: 3%,A,理由,A（業務部）,決定表 4 行目,反映済み,\n"
    "Q-002,実現性・コスト,夜間は？,A: 止める / B: 24 時間,A,理由,未回答,—,確認中,B は月額 2 倍\n"
)
QA_V2 = HEADER + (
    "Q-002,実現性・コスト,夜間は（問い直し）？,A: 止める / B: 24 時間,A,理由,B（部長）,—,確認中,B は月額 2 倍\n"
    '"Q-003",要求確定,"1 行目\n2 行目 *強調* `x` [y](z)",A: はい / B: いいえ,A,理由,未回答,—,確認中,\n'
    # 暫定の回答で反映した行（#325）——確認中にも「回答あり・未反映」にも数えない
    "Q-004,要求確定,上限は？,A: なし / B: 5000 円,A,理由,A（暫定で採用。業務部 2026-10-21 の指示）,決定表 7 行目,暫定反映,\n"
)
QA_V10 = HEADER + "Q-010,要求確定,十番目,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n"

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def copy_plugin(dest: Path) -> Path:
    assert_in_tmp(dest)
    for part in ("scripts", "templates"):
        shutil.copytree(PLUGIN / part, dest / part, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def write(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")


def snapshot(root: Path) -> dict[str, bytes | str]:
    """根の中身（リンクは指し先の文字列）。"""
    out: dict[str, bytes | str] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                out[rel] = "->" + os.readlink(path)
            elif path.is_file():
                out[rel] = path.read_bytes()
    return out


def run_init(plugin: Path, root: Path, *extra: str) -> tuple[int, str]:
    assert_in_tmp(root)
    proc = subprocess.run([sys.executable, "-I", str(plugin / INIT), str(root), *extra],
                          capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout + proc.stderr


# os.link を差し替えて本体を走らせる。{err} は errno の名前、{race} は真なら失敗の前に行き先を作る（確かめた後に作られた形）、
# {cut} は真なら、512 バイトを超えるファイルで失敗の前に大きさの上限を 512 バイトにする（一時ファイルは書けたあと、退路の書き込みで切れる。
# 小さいファイルでは上限を掛けない——掛けると次のファイルの一時ファイルが先に切れて、退路まで届かない）。
# {stuck} は真なら Path.unlink を EROFS で失敗させる（書きかけを消せない形。一時ファイルは os.unlink で消すので当たらない）
NO_LINK_RUNNER = """
import errno, os, pathlib, resource, runpy, sys
def unlink(self, missing_ok=False):
    raise OSError(errno.EROFS, os.strerror(errno.EROFS))
if {stuck}:
    pathlib.Path.unlink = unlink
def link(src, dst):
    if {race}:
        with open(dst, "x", encoding="utf-8") as f:
            f.write("他人\\n")
    if {cut} and os.path.getsize(src) > 512:
        resource.setrlimit(resource.RLIMIT_FSIZE, (512, resource.RLIM_INFINITY))
    raise OSError(errno.{err}, os.strerror(errno.{err}))
os.link = link
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def run_init_no_link(plugin: Path, root: Path, err: str = "ENOTSUP", race: bool = False, cut: bool = False,
                     stuck: bool = False) -> tuple[int, str]:
    assert_in_tmp(root)
    code = NO_LINK_RUNNER.format(err=err, race=race, cut=cut, stuck=stuck)
    proc = subprocess.run([sys.executable, "-I", "-c", code, str(plugin / INIT), str(root)],
                          capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def modes_follow_umask(root: Path) -> bool:
    umask = os.umask(0)
    os.umask(umask)
    files = [path for path in root.rglob("*") if path.is_file() and not path.is_symlink()]
    return bool(files) and all(path.stat().st_mode & 0o777 == 0o666 & ~umask for path in files)


def template_map(plugin: Path) -> dict[str, bytes]:
    base = plugin / "templates" / "mkdocs"
    out = {}
    for path in base.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            rel = path.relative_to(base).as_posix()
            out[".gitignore" if rel == "gitignore" else rel] = path.read_bytes()
    return out


# ---- 写し方の試料（plugin, 作業場所）→ 期待どおりか ----

def init_empty(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    # 雛形の中に __pycache__ が在っても写さない（copy_plugin は落とすので、ここで置く）
    cache = plugin / "templates" / "mkdocs" / "hooks" / "__pycache__"
    assert_in_tmp(cache)
    cache.mkdir(exist_ok=True)
    (cache / "spec_loop_pages.cpython-312.pyc").write_bytes(b"\0")
    code, _ = run_init(plugin, root)
    expected = template_map(plugin)
    got = {k: v for k, v in snapshot(root).items() if isinstance(v, bytes)}
    return code == 0 and got == expected and len(expected) >= 6 and modes_follow_umask(root)


def init_config_exists(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    write(root, {"mkdocs.yml": "site_name: 既存\n"})
    before = snapshot(root)
    code, out = run_init(plugin, root)
    return code == 0 and snapshot(root) == before and "何も写さない" in out


def init_config_yaml(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    write(root, {"mkdocs.yaml": "site_name: 既存\n"})
    before = snapshot(root)
    code, out = run_init(plugin, root)
    return code == 0 and snapshot(root) == before and "何も写さない" in out


def init_config_last(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    code, out = run_init(plugin, root, "--dry-run")
    listed = [line for line in out.splitlines() if line.startswith("写す")]
    return code == 0 and len(listed) >= 6 and listed[-1].endswith(": mkdocs.yml")


def init_parent_is_file(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    write(root, {"hooks": "ファイル\n"})
    code, out = run_init(plugin, root)
    stopped = code == 2 and not (root / "mkdocs.yml").exists() and (root / "hooks").read_text(encoding="utf-8") == "ファイル\n"
    (root / "hooks").unlink()
    code2, _ = run_init(plugin, root)
    return (stopped and "既にあるので触らない: hooks" not in out
            and code2 == 0 and (root / "mkdocs.yml").is_file() and (root / "hooks" / "spec_loop_pages.py").is_file())


def init_cut_off(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    assert_in_tmp(root)
    # ファイルの大きさの上限で、512 バイトを超える雛形の書き込みを途中で失敗させる（Python は SIGXFSZ を無視するので EFBIG になる）
    proc = subprocess.run([sys.executable, "-I", str(plugin / INIT), str(root)], capture_output=True, text=True, check=False,
                          preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_FSIZE, (512, resource.RLIM_INFINITY)))
    big = [rel for rel, data in template_map(plugin).items() if len(data) > 512]
    after = snapshot(root)
    stopped = (proc.returncode == 2 and big and not any(rel in after for rel in big)
               and not any(Path(rel).name.startswith(".") and rel != ".gitignore" for rel in after))
    code, _ = run_init(plugin, root)
    return bool(stopped) and code == 0 and snapshot(root) == template_map(plugin)


def init_no_link(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    code, _ = run_init_no_link(plugin, root)
    return code == 0 and snapshot(root) == template_map(plugin) and modes_follow_umask(root)


def init_no_link_race(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    code, out = run_init_no_link(plugin, root, race=True)
    after = snapshot(root)
    others = [rel for rel in template_map(plugin)]
    return (code == 0 and set(after) == set(others) and all(after[rel] == "他人\n".encode("utf-8") for rel in others)
            and "既にあるので触らない: mkdocs.yml" in out)


def init_no_link_cut_off(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    code, _ = run_init_no_link(plugin, root, cut=True)
    big = [rel for rel, data in template_map(plugin).items() if len(data) > 512]
    after = snapshot(root)
    stopped = (code == 2 and big and not any(rel in after for rel in big)
               and not any(Path(rel).name.startswith(".") and rel != ".gitignore" for rel in after))
    code2, _ = run_init_no_link(plugin, root)
    return bool(stopped) and code2 == 0 and snapshot(root) == template_map(plugin)


def init_no_link_eperm(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    code, _ = run_init_no_link(plugin, root, err="EPERM")
    return code == 0 and snapshot(root) == template_map(plugin)


def init_no_link_stuck(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    code, out = run_init_no_link(plugin, root, cut=True, stuck=True)
    reason = [line for line in out.splitlines() if "書けない" in line]
    return (code == 2 and "書きかけを消せなかった" in out and len(reason) == 1
            and os.strerror(errno.EROFS) not in reason[0])


def init_link_other_error(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    code, out = run_init_no_link(plugin, root, err="EACCES")
    return code == 2 and snapshot(root) == {} and "書けない" in out


def init_keeps_existing(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    write(root, {"pyproject.toml": '[project]\nname = "x"\ndependencies = ["requests"]\n',
                 ".gitignore": "site/\n", "docs/index.md": "# 既存の表紙\n"})
    before = snapshot(root)
    code, out = run_init(plugin, root)
    after = snapshot(root)
    kept = all(after[k] == v for k, v in before.items())
    wrote = {"mkdocs.yml", "docs/qa.md", "hooks/spec_loop_pages.py"} <= set(after)
    return (code == 0 and kept and wrote and "既にあるので触らない: pyproject.toml" in out
            and "mkdocs mkdocs-material" in out and "build/ .venv/ __pycache__/" in out
            and "site/" not in out.split(".gitignore に無い行", 1)[-1].split("\n", 1)[0])


def init_symlink(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "qa.md").symlink_to(work / "nowhere.md")
    code, _ = run_init(plugin, root)
    return (code == 0 and (root / "docs" / "qa.md").is_symlink()
            and not (work / "nowhere.md").exists() and (root / "mkdocs.yml").is_file())


def init_dry_run(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    root.mkdir(parents=True)
    code, out = run_init(plugin, root, "--dry-run")
    return code == 0 and snapshot(root) == {} and "mkdocs.yml" in out


def init_not_dir(plugin: Path, work: Path) -> bool:
    work.mkdir(parents=True)
    code, _ = run_init(plugin, work / "missing")
    return code == 2


# ---- フックの試料 ----

def load_hook(plugin: Path):
    spec = importlib.util.spec_from_file_location(f"hook_{abs(hash(str(plugin)))}", plugin / HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def warnings_of():
    """`mkdocs` のロガーに出た警告を集める。"""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("mkdocs")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        yield stream
    finally:
        logger.removeHandler(handler)


def render(plugin: Path, docs: Path, markdown: str, src: str = "qa.md", renderers: dict | None = None) -> tuple[str, list[str]]:
    hook = load_hook(plugin)
    hook.RENDERERS.update(renderers or {})
    with warnings_of() as stream:
        page = SimpleNamespace(file=SimpleNamespace(src_path=src))
        out = hook.on_page_markdown(markdown, page, {"docs_dir": str(docs)}, None)
    return out, [line for line in stream.getvalue().splitlines() if line]


def hook_versions(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1, "v2/shared/qa.csv": QA_V2})
    out, warnings = render(plugin, docs, "# Q&A\n\n<!-- spec-loop: qa -->\n")
    v1, v2 = out.index("## v1"), out.index("## v2")
    return (not warnings and out.startswith("# Q&A\n\n") and v1 < v2
            and "(#v1-q-001)" in out and "{#v1-q-002}" in out and "{#v2-q-002}" in out and "{#v2-q-003}" in out
            and "確認中 1 件（うち回答あり・未反映 0 件）・暫定反映 0 件・反映済み 1 件" in out[v1:v2]
            and "確認中 2 件（うち回答あり・未反映 1 件）・暫定反映 1 件・反映済み 0 件" in out[v2:]
            and "| 選択肢 | **A: 止める**（推奨）<br>B: 24 時間 |" in out
            and "<!-- spec-loop" not in out)


def hook_numeric_order(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    files = {f"v{n}/shared/qa.csv": HEADER for n in range(1, 10)}
    files["v10/shared/qa.csv"] = QA_V10
    files["v02/shared/qa.csv"] = QA_V10
    write(docs, files)
    out, _ = render(plugin, docs, "<!-- spec-loop: qa -->")
    return out.index("## v9") < out.index("## v10") and "{#v2-q-010}" not in out and "{#v10-q-010}" in out


def hook_escape(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1, "v2/shared/qa.csv": QA_V2})
    out, _ = render(plugin, docs, "<!-- spec-loop: qa -->")
    return ("&lt;b&gt;A&lt;/b&gt; \\| B？" in out and "<b>" not in out
            and "1 行目<br>2 行目 \\*強調\\* \\`x\\` \\[y\\](z)" in out)


def hook_escape_more(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    (docs / "v1" / "shared").mkdir(parents=True)
    (docs / "v1" / "shared" / "qa.csv").write_bytes(
        (HEADER + 'Q-001,要求確定,"C:\\dir\\|x & y\r\n次\r三",A: x / B: y,A,理由,未回答,—,確認中,\n').encode("utf-8"))
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return not warnings and "C:\\\\dir\\\\\\|x &amp; y<br>次<br>三" in out and "\r" not in out


def hook_anchor(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": HEADER + "q-001 onclick=alert(1),要求確定,何？,A: x / B: y,A,理由,未回答,—,確認中,\n"})
    out, _ = render(plugin, docs, "<!-- spec-loop: qa -->")
    return ("{#v1-q-001-onclick-alert-1-}" in out and "(#v1-q-001-onclick-alert-1-)" in out
            and "{#v1-q-001 " not in out and "(#v1-q-001 " not in out)


def hook_skips_missing(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1, "v2/requirements/a.md": "# a\n", "v3/shared/qa.csv": QA_V10})
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return not warnings and "## v1" in out and "## v2" not in out and "{#v3-q-010}" in out


def hook_cost(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1})
    out, _ = render(plugin, docs, "<!-- spec-loop: qa -->")
    return out.count("| 費用への影響 |") == 1 and "nan" not in out and "| 費用への影響 | B は月額 2 倍 |" in out


def hook_block_syntax(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": HEADER + (
        "Q-001,要求確定,!!! note 注意,A: x / B: y,A,理由,未回答,—,確認中,\n"
        'Q-002,要求確定,"    字下げ",1. 一つ目 / 2. 二つ目,A,理由,未回答,—,確認中,\n'
        "Q-003,要求確定,1. 割引は？,A: x / B: y,A,理由,未回答,—,確認中,!!! warning 高い\n"
        "Q-004,要求確定,末尾 {: #evil },A: x / B: y,A,理由,未回答,—,確認中,\n")})
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    # 表のセル（| で始まる行）と見出し・件数の行のほかに、CSV の文字が出てこない
    stray = [line for line in out.splitlines()
             if line and not line.startswith(("|", "## ", "### ", "確認中 "))]
    return (not warnings and not stray and "| 質問 | !!! note 注意 |" in out
            and "| 選択肢 | 1. 一つ目<br>2. 二つ目 |" in out and "| 費用への影響 | !!! warning 高い |" in out
            and "末尾 \\{: \\#evil \\}" in out)


def hook_bom(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    (docs / "v1" / "shared").mkdir(parents=True)
    (docs / "v1" / "shared" / "qa.csv").write_bytes(b"\xef\xbb\xbf" + QA_V1.encode("utf-8"))
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return not warnings and "{#v1-q-001}" in out and "{#v1-q-002}" in out


def hook_blank_rows(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1 + ",,,,,,,,,\n , ,\n\nQ-004,要求確定,短い？,A: x / B: y,A,理由,未回答 ,—,確認中\n"})
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return (not warnings and "{#v1-q-004}" in out and "{#v1-}" not in out and out.count("### ") == 3
            and "確認中 2 件（うち回答あり・未反映 0 件）・暫定反映 0 件・反映済み 1 件" in out)


def hook_recommendation(plugin: Path, work: Path) -> bool:
    """推奨の選択肢だけを太字にして「（推奨）」を添え、理由（推奨しないなら「推奨なし」）を出す。一覧に推奨の列（#267）。"""
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": HEADER + "Q-001,要求確定,どちら？,A: 甲 / B: 乙,B,乙が安い,未回答,—,確認中,\n"
                 "Q-002,要求確定,誰が？,A: 広報 / B: 各部,なし,事実の確認,未回答,—,確認中,\n"})
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return (not warnings and "| 選択肢 | A: 甲<br>**B: 乙**（推奨） |" in out and "| 推奨の理由 | 乙が安い |" in out
            and "| 選択肢 | A: 広報<br>B: 各部 |" in out and "| 推奨なし | 事実の確認 |" in out
            and "| No | 質問 | 推奨 | 回答 | 状態 |" in out and "| どちら？ | B | 未回答 |" in out
            and out.count("（推奨）") == 1)


def hook_old_header(plugin: Path, work: Path) -> bool:
    """前の形（推奨の列が無い）の表は警告し、移す手順を指す（#337）。"""
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": OLD_HEADER + "Q-001,要求確定,何？,A: x / B: y,未回答,—,確認中,\n"})
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return (len(warnings) == 1 and "references/tree.md の「Q&A 表を移す」" in warnings[0] and "表示できない" in out)


def hook_bad_header(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": "No,質問\nQ-001,何？\n", "v2/shared/qa.csv": QA_V2})
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return len(warnings) == 1 and "v1/shared/qa.csv" in warnings[0] and "表示できない" in out and "## v2" in out


def hook_undecodable(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    (docs / "v1" / "shared").mkdir(parents=True)
    (docs / "v1" / "shared" / "qa.csv").write_bytes(HEADER.encode("utf-8") + b"\xff\xfe\n")
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return len(warnings) == 1 and "表示できない" in out


def hook_no_table(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/requirements/a.md": "# a\n"})
    out, warnings = render(plugin, docs, "<!-- spec-loop: qa -->")
    return not warnings and "まだ無い" in out


def hook_unknown_marker(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    docs.mkdir(parents=True)
    out, warnings = render(plugin, docs, "<!-- spec-loop: nfr -->")
    return len(warnings) == 1 and "nfr" in warnings[0] and "表示できない" in out


def hook_no_marker(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1})
    text = "# 表紙\n\n<!-- ふつうのコメント -->\n"
    out, warnings = render(plugin, docs, text)
    return out == text and not warnings


def link_site(work: Path) -> Path:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1, "v2/shared/qa.csv": QA_V2, "v3/requirements/a.md": "# a\n",
                 "qa.md": "<!-- spec-loop: qa -->\n"})
    return docs


def site_files(docs: Path) -> SimpleNamespace:
    """MkDocs の `Files` の代わり。`qa.md` の `url_relative_to` は `use_directory_urls: false` の MkDocs と同じ値を返す
    （実際の MkDocs で同じになることは dev-loop の検証で見る——#324 の計画ファイル）。"""
    qa = SimpleNamespace(url="qa.html", url_relative_to=lambda other: posixpath.relpath(
        "qa.html", posixpath.dirname(other.src_path) or "."))
    return SimpleNamespace(get_file_from_path=lambda path: qa if path == "qa.md" and (docs / path).is_file() else None)


def link(plugin: Path, docs: Path, content: str, src: str, markdown: str = "本文\n", hook=None) -> tuple[str, list[str]]:
    """`on_page_markdown` に `markdown` を通してから、描いた HTML に見立てた `content` を `on_page_content` に通す。"""
    hook = hook or load_hook(plugin)
    page = SimpleNamespace(file=SimpleNamespace(src_path=src))
    config = {"docs_dir": str(docs)}
    with warnings_of() as stream:
        hook.on_page_markdown(markdown, page, config, None)
        out = hook.on_page_content(content, page, config, site_files(docs))
    return out, [line for line in stream.getvalue().splitlines() if line]


def a(number: str, href: str) -> str:
    return f'<a href="{href}">{number}</a>'


def hook_links(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    v2, w2 = link(plugin, docs, "<p>決定（Q-001）と Q-002・Q-003。</p>\n", "v2/requirements/a.md")
    v1, w1 = link(plugin, docs, "<p>Q-001 と Q-002。</p>\n", "v1/a.md")
    v3, w3 = link(plugin, docs, "<p>Q-002</p>\n", "v3/requirements/a.md")
    top, w0 = link(plugin, docs, "<p>Q-001 と Q-002</p>\n", "index.md")
    return (not (w2 or w1 or w3 or w0)
            and v2 == f"<p>決定（{a('Q-001', '../../qa.html#v1-q-001')}）と {a('Q-002', '../../qa.html#v2-q-002')}・"
                      f"{a('Q-003', '../../qa.html#v2-q-003')}。</p>\n"
            and v1 == f"<p>{a('Q-001', '../qa.html#v1-q-001')} と {a('Q-002', '../qa.html#v1-q-002')}。</p>\n"
            and v3 == f"<p>{a('Q-002', '../../qa.html#v2-q-002')}</p>\n"
            and top == f"<p>{a('Q-001', 'qa.html#v1-q-001')} と {a('Q-002', 'qa.html#v2-q-002')}</p>\n")


def hook_links_older_version(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    out, warnings = link(plugin, docs, "<p>Q-003</p>\n", "v1/a.md")
    return out == "<p>Q-003</p>\n" and len(warnings) == 1 and "Q-003" in warnings[0] and "v1〜v1" in warnings[0]


# 見出し（容れ物の中・大文字の要素名を含む）・コード・リンク・属性（値の中の > を含む）・コメント・CDATA・script などの中
LEFT_ALONE = """<h1 id="x">見出し Q-001</h1>
<H2>Q-002</H2>
<h6>Q-001</h6>
<div class="admonition note"><h3 id="q-001">Q-001 の決定</h3></div>
<blockquote><h2>Q-001</h2></blockquote>
<pre><code>Q-001
<span class="err">Q-002</span>
</code></pre>
<p><code>Q-001</code> と <a href="qa.html#v1-q-001">Q-001</a> と <a href="b.md">決定（<em>Q-002</em>）</a> と <img alt="Q-001" src="Q-001.png" /></p>
<p><kbd>Q-001</kbd> <samp>Q-002</samp> <textarea>Q-001</textarea></p>
<p title="Q-001 > Q-002" data-x='a > Q-002'>段落</p>
<!-- a > Q-001 -->
<![CDATA[ a > Q-001 ]]>
<script>var s = "<p>Q-001</p>";</script>
<style>/* Q-001 */</style>
"""


def hook_links_left_alone(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    out, warnings = link(plugin, docs, LEFT_ALONE, "index.md")
    return out == LEFT_ALONE and not warnings


def hook_links_after_left_alone(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    page = ("<h1>Q-001</h1>\n<p>Q-001</p>\n<pre><code>Q-001</code></pre>Q-002<a href=\"#\">x</a> Q-001<br/>Q-002"
            "<p></code>Q-001</p><code/>Q-002\n")
    out, warnings = link(plugin, docs, page, "index.md")
    q1, q2 = a("Q-001", "qa.html#v1-q-001"), a("Q-002", "qa.html#v2-q-002")
    return not warnings and out == (
        f"<h1>Q-001</h1>\n<p>{q1}</p>\n<pre><code>Q-001</code></pre>{q2}<a href=\"#\">x</a> {q1}<br/>{q2}"
        f"<p></code>{q1}</p><code/>{q2}\n")


def hook_links_unreadable(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    write(docs, {"v2/shared/qa.csv": "No,質問\nQ-003,x\n"})
    out, warnings = link(plugin, docs, "<p>Q-001 と Q-003</p>\n", "index.md")
    return (out == f"<p>{a('Q-001', 'qa.html#v1-q-001')} と Q-003</p>\n" and len(warnings) == 1
            and "Q-003" in warnings[0] and "読めない表は数えない" in warnings[0])


def hook_links_spaced_number(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    write(docs, {"v2/shared/qa.csv": QA_V2 + " Q-005,要求確定,空白,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n"})
    out, warnings = link(plugin, docs, "<p>Q-005</p>\n", "index.md")
    return out == "<p>Q-005</p>\n" and len(warnings) == 1 and "Q-005" in warnings[0]


def hook_links_unknown(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    out, warnings = link(plugin, docs, "<p>Q-099 と Q-099 と Q-001</p>\n", "index.md")
    return (out == f"<p>Q-099 と Q-099 と {a('Q-001', 'qa.html#v1-q-001')}</p>\n" and len(warnings) == 1
            and "Q-099" in warnings[0] and "index.md" in warnings[0])


def hook_links_shape(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    write(docs, {"v4/shared/qa.csv": HEADER + "Q-0012,要求確定,四桁,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n"})
    out, warnings = link(plugin, docs, "<p>XQ-001 Q-01 Q-001x Q-001-a Q-001_x Q-0012 a-Q-001 (Q-001)</p>\n", "index.md")
    return not warnings and out == (
        f"<p>XQ-001 Q-01 Q-001x Q-001-a Q-001_x {a('Q-0012', 'qa.html#v4-q-0012')} a-Q-001 ({a('Q-001', 'qa.html#v1-q-001')})</p>\n")


def hook_links_not_qa_page(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    hook = load_hook(plugin)
    qa, warnings = link(plugin, docs, "<p>Q-001 と Q-099</p>\n", "qa.md", "<!-- spec-loop: qa -->\n", hook)
    # 同じページから印を外したら掛かる（`mkdocs serve` で組み直したとき、前に記録した Q&A 表のページを覚えたままにしない）
    again, more = link(plugin, docs, "<p>Q-001</p>\n", "qa.md", hook=hook)
    return (not warnings and qa == "<p>Q-001 と Q-099</p>\n"
            and not more and again == f"<p>{a('Q-001', 'qa.html#v1-q-001')}</p>\n")


def hook_links_rendered(plugin: Path, work: Path) -> bool:
    docs = link_site(work)
    out, warnings = link(plugin, docs, "<table><tr><td>会員</td><td>Q-002</td></tr></table>\n", "v1/decision.md")
    return not warnings and out == f"<table><tr><td>会員</td><td>{a('Q-002', '../qa.html#v1-q-002')}</td></tr></table>\n"


def hook_links_no_qa_page(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1})
    out, warnings = link(plugin, docs, "<p>Q-001 と Q-099</p>\n", "index.md")
    return out == "<p>Q-001 と Q-099</p>\n" and not warnings


def merge_ignores_pages(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    write(root / "docs", {"v1/shared/qa.csv": QA_V1})
    code, _ = run_init(plugin, root)
    proc = subprocess.run([sys.executable, "-I", str(plugin / "scripts" / "merge-versions.py"),
                           str(root / "docs"), str(work / "merged")], capture_output=True, text=True, check=False)
    merged = set(snapshot(work / "merged"))
    return code == 0 and proc.returncode == 0 and "shared/qa.csv" in merged and not any(
        name.endswith(("qa.md", "index.md")) for name in merged)


CASES = {
    "空の根には雛形をすべて写す": init_empty,
    "mkdocs.yml が在れば何も写さない": init_config_exists,
    "mkdocs.yaml が在っても何も写さない": init_config_yaml,
    "mkdocs.yml は最後に写す": init_config_last,
    "親がファイルなら 2 で止まり、直せば残りが写る": init_parent_is_file,
    "途中で書けなくても切れたファイルを残さず、直せば残りが写る": init_cut_off,
    "リンクを作れなくても雛形をすべて写す": init_no_link,
    "リンクを作れないとき、確かめた後に作られたファイルは上書きしない": init_no_link_race,
    "リンクを作れないとき、途中で書けなくても切れたファイルを残さない": init_no_link_cut_off,
    "EPERM（Linux の vfat）でも退路に入る": init_no_link_eperm,
    "書きかけを消せなければそう言い、書けなかった理由で 2": init_no_link_stuck,
    "リンクと関係ない失敗は 2": init_link_other_error,
    "在るファイルは変えず、足りないものを示す": init_keeps_existing,
    "壊れたリンクも在るとみなす": init_symlink,
    "--dry-run は書かない": init_dry_run,
    "根がディレクトリでなければ 2": init_not_dir,
    "版ごとの節・アンカー・件数": hook_versions,
    "版は番号の順・形に合わない名前は読まない": hook_numeric_order,
    "セルをエスケープする": hook_escape,
    "& と \\ と \\r もエスケープする": hook_escape_more,
    "アンカーに使えない文字を置き換える": hook_anchor,
    "qa.csv の無い版は飛ばして次の版を描く": hook_skips_missing,
    "費用への影響は空なら出さない": hook_cost,
    "CSV の文字をブロックの記法にしない": hook_block_syntax,
    "BOM つきの表を読む": hook_bom,
    "空白だけの行は読み飛ばし、短い行は埋める": hook_blank_rows,
    "見出しの違う表は警告": hook_bad_header,
    "推奨を目立たせる": hook_recommendation,
    "前の形の表は移す手順を指す": hook_old_header,
    "読めない表は警告": hook_undecodable,
    "表が無ければそう書く": hook_no_table,
    "知らない印は警告": hook_unknown_marker,
    "印の無いページは変えない": hook_no_marker,
    "本文の番号を版のアンカーへの相対リンクにする": hook_links,
    "ページの版より新しい版の番号はリンクにしない": hook_links_older_version,
    "見出し・コード・リンク・属性・コメントの中は変えない": hook_links_left_alone,
    "変えない要素の後ろは置き換える": hook_links_after_left_alone,
    "読めない表があっても他の版でリンクにする": hook_links_unreadable,
    "空白つきの No はリンクにせず警告": hook_links_spaced_number,
    "どの版にも無い番号は警告": hook_links_unknown,
    "番号の形": hook_links_shape,
    "Q&A 表のページは変えない": hook_links_not_qa_page,
    "描画した表のセルも置き換える": hook_links_rendered,
    "qa.md が無ければ変えない": hook_links_no_qa_page,
    "重ね合わせに表示用のファイルが混ざらない": merge_ignores_pages,
}

# (名前, 壊す対象, 壊す前, 壊した後, 殺すはずの試料の名前)。2 箇所を壊すときは (壊す前, 壊した後) の列を渡す
MUTATIONS: list[tuple] = [
    ("mkdocs.yml が在っても写す", INIT, "        if os.path.lexists(root / name):\n", "        if False:\n",
     "mkdocs.yml が在れば何も写さない"),
    ("mkdocs.yaml を設定とみなさない", INIT, 'CONFIG_NAMES = ("mkdocs.yml", "mkdocs.yaml")', 'CONFIG_NAMES = ("mkdocs.yml",)',
     "mkdocs.yaml が在っても何も写さない"),
    ("mkdocs.yml を名前の順に写す", INIT, "    return sorted(files, key=lambda item: item[1] == CONFIG)", "    return files",
     "mkdocs.yml は最後に写す"),
    ("親が作れないのを「既にある」と読む", INIT, "                dest.parent.mkdir(parents=True, exist_ok=True)\n",
     "                try:\n                    dest.parent.mkdir(parents=True, exist_ok=True)\n"
     "                except FileExistsError:\n                    kept.append(rel)\n                    continue\n",
     "親がファイルなら 2 で止まり、直せば残りが写る"),
    ("書けなくても 0 で続ける", INIT, "file=sys.stderr)\n                return 2\n", "file=sys.stderr)\n                continue\n",
     "親がファイルなら 2 で止まり、直せば残りが写る"),
    ("在って触らないものを示さない", INIT, '        print(f"既にあるので触らない: {rel}")\n', "",
     "在るファイルは変えず、足りないものを示す"),
    ("雛形の __pycache__ も写す", INIT, 'if path.is_dir() or "__pycache__" in path.parts:', "if path.is_dir():",
     "空の根には雛形をすべて写す"),
    # 在るかの確認と排他的な作成は二重の守りなので、片方だけ壊しても挙動は変わらない（等価変異）。両方を壊す。
    ("在るファイルを上書きする", INIT, [("        if os.path.lexists(dest):\n", "        if False:\n"),
                                       ("os.link(tmp, dest)", '__import__("shutil").copyfile(tmp, dest)')],
     "在るファイルは変えず、足りないものを示す"),
    ("リンクを辿って在るかを見る", INIT, [("        if os.path.lexists(dest):\n", "        if dest.exists():\n"),
                                         ("os.link(tmp, dest)", '__import__("shutil").copyfile(tmp, dest)')],
     "壊れたリンクも在るとみなす"),
    ("--dry-run でも書く", INIT, "        if not args.dry_run:\n", "        if True:\n", "--dry-run は書かない"),
    ("gitignore の名前を変えない", INIT, 'RENAMES = {"gitignore": ".gitignore"}', "RENAMES = {}",
     "空の根には雛形をすべて写す"),
    ("足りない依存を示さない", INIT, "            if names:\n", "            if False:\n",
     "在るファイルは変えず、足りないものを示す"),
    ("根を確かめない", INIT, "    if not root.is_dir():\n", "    if False:\n", "根がディレクトリでなければ 2"),
    ("版を名前の順に並べる", HOOK, "    return sorted(found)\n", "    return sorted(found, key=lambda item: item[1].name)\n",
     "版は番号の順・形に合わない名前は読まない"),
    ("版の形を見ない", HOOK, "VERSION.fullmatch(entry.name) and ", "entry.name.startswith('v') and ",
     "版は番号の順・形に合わない名前は読まない"),
    ("アンカーに版を入れない", HOOK, 'return f"v{version}-" + ANCHOR_UNSAFE', "return ANCHOR_UNSAFE",
     "版ごとの節・アンカー・件数"),
    ("アンカーの文字を置き換えない", HOOK, 'ANCHOR_UNSAFE.sub("-", number.lower())', "number.lower()",
     "アンカーに使えない文字を置き換える"),
    ("HTML をエスケープしない", HOOK, [("html.escape(value.replace", "(value.replace"), (", quote=False)", ")")],
     "セルをエスケープする"),
    ("& をエスケープしない", HOOK, r'MARKDOWN_SPECIAL.sub(r"\\\1", escaped)', r'MARKDOWN_SPECIAL.sub(r"\\\1", escaped.replace("&amp;", "&"))',
     "& と \\ と \\r もエスケープする"),
    ("\\ をエスケープしない", HOOK, r'MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]{}#|])")',
     r'MARKDOWN_SPECIAL = re.compile(r"([`*_\[\]{}#|])")', "& と \\ と \\r もエスケープする"),
    ("\\r を改行にしない", HOOK, '.replace("\\r", "\\n")', "", "& と \\ と \\r もエスケープする"),
    ("qa.csv の無い版で止まる", HOOK, "        if not path.is_file():\n            continue\n",
     "        if not path.is_file():\n            break\n", "qa.csv の無い版は飛ばして次の版を描く"),
    ("一時ファイルを残す", INIT, "        os.unlink(tmp)\n", "        pass\n", "空の根には雛形をすべて写す"),
    ("行き先へ直に書く", INIT, '        with os.fdopen(fd, "wb") as f:\n            f.write(data)\n',
     '        with os.fdopen(fd, "wb") as f, open(dest, "xb") as g:\n            g.write(data)\n            f.write(data)\n',
     "途中で書けなくても切れたファイルを残さず、直せば残りが写る"),
    ("一時ファイルの権限を直さない", INIT, "        os.chmod(tmp, 0o666 & ~UMASK)", "        pass", "空の根には雛形をすべて写す"),
    ("リンクを作れないと止まる", INIT,
     "            if e.errno not in NO_LINK:\n                raise\n            return place_directly(dest, data)\n",
     "            raise\n", "リンクを作れなくても雛形をすべて写す"),
    ("ENOTSUP を退路に入れない", INIT, "errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP,", "errno.EPERM,",
     "リンクを作れなくても雛形をすべて写す"),
    ("どの失敗でも退路に入る", INIT, "            if e.errno not in NO_LINK:\n", "            if False:\n",
     "リンクと関係ない失敗は 2"),
    ("退路で上書きする", INIT, '        f = dest.open("xb")', '        f = dest.open("wb")',
     "リンクを作れないとき、確かめた後に作られたファイルは上書きしない"),
    ("退路で切れたファイルを残す", INIT, "            dest.unlink()  #", "            pass  #",
     "リンクを作れないとき、途中で書けなくても切れたファイルを残さない"),
    ("EPERM を退路に入れない", INIT, "{errno.EPERM, errno.ENOTSUP,", "{errno.ENOTSUP,",
     "EPERM（Linux の vfat）でも退路に入る"),
    ("書きかけを消せなくても言わない", INIT,
     '            print(f"{dest}: 書きかけを消せなかった（{e.strerror}）。消してから再実行する", file=sys.stderr)\n',
     "            pass\n", "書きかけを消せなければそう言い、書けなかった理由で 2"),
    ("消せなかった理由で止まる", INIT, "        except OSError as e:\n            print(f\"{dest}: 書きかけ",
     "        except OSError as e:\n            raise\n            print(f\"{dest}: 書きかけ", "書きかけを消せなければそう言い、書けなかった理由で 2"),
    ("| をエスケープしない", HOOK, r'MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]{}#|])")',
     r'MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]{}#])")', "セルをエスケープする"),
    ("{} をエスケープしない", HOOK, r'MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]{}#|])")',
     r'MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]#|])")', "CSV の文字をブロックの記法にしない"),
    ("質問を段落に置く", HOOK, "\"| 項目 | 内容 |\", \"| --- | --- |\", f\"| 質問 | {text(row['質問'])} |\"",
     "text(row['質問']), \"\", \"| 項目 | 内容 |\", \"| --- | --- |\"", "CSV の文字をブロックの記法にしない"),
    ("推奨を太字にしない", HOOK, 'f"**{text(option)}**（推奨）" if', 'text(option) if', "推奨を目立たせる"),
    ("推奨しないのを理由と書く", HOOK, 'reason = "推奨なし" if recommended == QA_NO_RECOMMENDATION else "推奨の理由"',
     'reason = "推奨の理由"', "推奨を目立たせる"),
    ("一覧に推奨を出さない", HOOK, "f\"| {text(row['推奨'])} | {text(row['回答'])} |", "f\"| {text(row['回答'])} |", "推奨を目立たせる"),
    ("前の形の表で手順を指さない", HOOK, 'if header and "推奨" not in header else ""', 'if False else ""', "前の形の表は移す手順を指す"),
    ("選択肢を箇条書きにする", HOOK, 'options = "<br>".join(', 'options = "\\n- ".join(',
     "CSV の文字をブロックの記法にしない"),
    ("BOM を読まない", HOOK, 'path.open(encoding="utf-8-sig"', 'path.open(encoding="utf-8"', "BOM つきの表を読む"),
    ("空白だけの行も描く", HOOK, "for row in reader if any(cell.strip() for cell in row)]", "for row in reader if row]",
     "空白だけの行は読み飛ばし、短い行は埋める"),
    ("短い行を埋めない", HOOK, 'row + [""] * (len(QA_COLUMNS) - len(row))', "row",
     "空白だけの行は読み飛ばし、短い行は埋める"),
    ("未回答の空白を落とさない", HOOK, 'row["回答"].strip() not in', 'row["回答"] not in',
     "空白だけの行は読み飛ばし、短い行は埋める"),
    ("改行を残す", HOOK, '.replace("\\n", "<br>")', '.replace("\\n", " ")', "セルをエスケープする"),
    ("空の費用にも注記を出す", HOOK, '        if row["費用への影響"].strip():\n', "        if True:\n",
     "費用への影響は空なら出さない"),
    ("見出しを見ない", HOOK, "        if header != QA_COLUMNS:\n", "        if False:\n", "見出しの違う表は警告"),
    # UnicodeDecodeError は ValueError の子なので、それだけ外しても等価。両方を外す。
    ("読めない表で落ちる", HOOK, "except (OSError, UnicodeDecodeError, csv.Error, ValueError)",
     "except (OSError, csv.Error)", "読めない表は警告"),
    ("警告を出さない", HOOK, '    log.warning("spec-loop: %s", message)\n', "", "見出しの違う表は警告"),
    ("知らない印を消す", HOOK, "        if renderer is None:\n            return problem(",
     "        if renderer is None:\n            return (", "知らない印は警告"),
    ("暫定反映を確認中に数える", HOOK, "    pending = len(rows) - done - provisional\n", "    pending = len(rows) - done\n",
     "版ごとの節・アンカー・件数"),
    ("暫定反映を回答あり未反映に数える", HOOK, 'row["状態"] not in (QA_DONE, QA_PROVISIONAL) and', 'row["状態"] != QA_DONE and',
     "版ごとの節・アンカー・件数"),
    ("回答あり未反映を数えない", HOOK, ' and row["回答"].strip() not in ("", QA_NO_ANSWER)\n',
     " and False\n",
     "版ごとの節・アンカー・件数"),
    ("ページの版を上限にしない", HOOK, " if limit is None or version <= limit]", "]",
     "ページの版より新しい版の番号はリンクにしない"),
    ("最も古い版を指す", HOOK, "for version, numbers in reversed(tables) if", "for version, numbers in tables if",
     "本文の番号を版のアンカーへの相対リンクにする"),
    ("リンク先を相対パスにしない", HOOK, "qa.url_relative_to(page.file)", "qa.url",
     "本文の番号を版のアンカーへの相対リンクにする"),
    ("版の下のページを版の外とみなす", HOOK, 'limit = int(top[1:]) if VERSION.fullmatch(top) and "/" in src_path else None',
     "limit = None", "本文の番号を版のアンカーへの相対リンクにする"),
    ("見出しの中を変える", HOOK, '"textarea", "title", "h1", "h2", "h3", "h4", "h5", "h6"}', '"textarea", "title"}',
     "見出し・コード・リンク・属性・コメントの中は変えない"),
    ("コードの中を変える", HOOK, 'UNLINKED = {"a", "code", "pre", ', 'UNLINKED = {"a", ',
     "見出し・コード・リンク・属性・コメントの中は変えない"),
    ("リンクの中を変える", HOOK, 'UNLINKED = {"a", ', "UNLINKED = {",
     "見出し・コード・リンク・属性・コメントの中は変えない"),
    ("kbd・samp・script・style・textarea の中を変える", HOOK, '"kbd", "samp", "script", "style", "textarea", ', "",
     "見出し・コード・リンク・属性・コメントの中は変えない"),
    ("要素名の大文字を区別する", HOOK, '(match.group(2) or "").lower()', '(match.group(2) or "")',
     "見出し・コード・リンク・属性・コメントの中は変えない"),
    ("属性の値の中の > で切る", HOOK, r'''(?:\"[^\"]*\"|'[^']*'|[^'\">])*>"''', '''[^>]*>"''',
     "見出し・コード・リンク・属性・コメントの中は変えない"),
    ("コメントを > で切る", HOOK, 'MARKUP = re.compile(r"<!--.*?-->|', 'MARKUP = re.compile(r"',
     "見出し・コード・リンク・属性・コメントの中は変えない"),
    ("CDATA を > で切る", HOOK, r'|<!\[CDATA\[.*?\]\]>|', "|",
     "見出し・コード・リンク・属性・コメントの中は変えない"),
    ("閉じても戻らない", HOOK, "max(inside[name] - 1, 0) if match.group(1) else", "inside[name] if match.group(1) else",
     "変えない要素の後ろは置き換える"),
    ("余分な閉じで数を負にする", HOOK, "max(inside[name] - 1, 0)", "inside[name] - 1",
     "変えない要素の後ろは置き換える"),
    ("自己閉じを開きとみなす", HOOK, ' and not match.group(0).endswith("/>"):', ":",
     "変えない要素の後ろは置き換える"),
    ("読めない表で落ちる", HOOK, "            except (OSError, ValueError, csv.Error):  #", "            except ZeroDivisionError:  #",
     "読めない表があっても他の版でリンクにする"),
    ("No の空白を落とす", HOOK, '{row["No"] for row in read_qa(path)}', '{row["No"].strip() for row in read_qa(path)}',
     "空白つきの No はリンクにせず警告"),
    ("警告が見た版の範囲を言わない", HOOK, '    scope = (f"v1〜v{limit} のどの版" if limit is not None else "どの版")',
     '    scope = ("どの版")', "ページの版より新しい版の番号はリンクにしない"),
    ("知らない番号を警告しない", HOOK, '        log.warning("spec-loop: %s: %s は %sにも', '        str("spec-loop: %s: %s は %sにも',
     "どの版にも無い番号は警告"),
    ("知らない番号を何度も警告する", HOOK, "            if number not in unknown:\n                unknown.append(number)\n",
     "            unknown.append(number)\n", "どの版にも無い番号は警告"),
    ("番号の前を見ない", HOOK, r'QA_NUMBER = re.compile(r"(?<![A-Za-z0-9_-])Q-', r'QA_NUMBER = re.compile(r"Q-', "番号の形"),
    ("番号の後を見ない", HOOK, r'[0-9]{3,}(?![A-Za-z0-9_-])")', r'[0-9]{3,})")', "番号の形"),
    ("番号の後の - を見ない", HOOK, r'[0-9]{3,}(?![A-Za-z0-9_-])")', r'[0-9]{3,}(?![A-Za-z0-9_])")', "番号の形"),
    ("番号を 3 桁に限る", HOOK, r'Q-[0-9]{3,}(?!', r'Q-[0-9]{3}(?!', "番号の形"),
    ("Q&A 表のページにも掛ける", HOOK, "    if src_path in qa_pages or qa is None:", "    if qa is None:",
     "Q&A 表のページは変えない"),
    ("Q&A 表のページの記録を消さない", HOOK, "    else:\n        qa_pages.discard(page_path(page))\n", "",
     "Q&A 表のページは変えない"),
    ("表のセルの中を変えない", HOOK, '"textarea", "title", ', '"textarea", "title", "td", ',
     "描画した表のセルも置き換える"),
    ("qa.md が無くても掛ける", HOOK, " or qa is None:", ":",
     "qa.md が無ければ変えない"),
]


def check_copies() -> None:
    """フックの写しが check-qa-csv.py の定数と同じか。"""
    hook = load_hook(PLUGIN)
    spec = importlib.util.spec_from_file_location("check_qa_csv", PLUGIN / "scripts" / "check-qa-csv.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    for name, theirs in (("QA_COLUMNS", checker.COLUMNS), ("QA_DONE", checker.DONE), ("QA_PROVISIONAL", checker.PROVISIONAL),
                         ("QA_NO_ANSWER", checker.NO_ANSWER), ("QA_OPTION_SEPARATOR", checker.OPTION_SEPARATOR),
                         ("QA_NO_RECOMMENDATION", checker.NO_RECOMMENDATION)):
        check(f"フックの {name} が check-qa-csv.py と違う", getattr(hook, name) == theirs, f"{getattr(hook, name)!r} != {theirs!r}")
    page = (PLUGIN / "templates" / "mkdocs" / "docs" / "qa.md").read_text(encoding="utf-8")
    check("雛形の docs/qa.md に qa の印が無い", "<!-- spec-loop: qa -->" in page)
    config = (PLUGIN / "templates" / "mkdocs" / "mkdocs.yml").read_text(encoding="utf-8")
    check("雛形の mkdocs.yml がフックを指していない", f"  - {HOOK.relative_to('templates/mkdocs').as_posix()}\n" in config)
    check("雛形の pyproject.toml が mkdocs を 2 未満に留めていない",
          '"mkdocs>=1.6,<2"' in (PLUGIN / "templates" / "mkdocs" / "pyproject.toml").read_text(encoding="utf-8"))


def check_reference() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    check("references/tree.md に「ドキュメントのツール」の節が無い", "\n## ドキュメントのツール\n" in text)
    section = text.split("\n## ドキュメントのツール\n", 1)[-1].split("\n## ", 1)[0]
    for word in ("scripts/init-mkdocs.py", "mkdocs.yml", "docs/qa.md", "shared/", "`qa-csv.md` の「本文での番号」"):
        check(f"references/tree.md の「ドキュメントのツール」に {word} が無い", word in section)
    qa = (PLUGIN / "references" / "qa-csv.md").read_text(encoding="utf-8")
    check("references/qa-csv.md に「本文での番号」の節が無い", "\n## 本文での番号\n" in qa)


def main() -> int:
    # umask を mkstemp の 0600 にならない値に固定する（077 だと 0o666 & ~077 == 0600 で、権限を直さない変異が殺せない）
    os.umask(0o022)
    with tempfile.TemporaryDirectory(prefix="init-mkdocs-test-") as tmp:
        tmp_path = Path(tmp)
        plugin = copy_plugin(tmp_path / "plugin")
        for index, (name, case) in enumerate(CASES.items()):
            check(f"試料が期待どおりでない: {name}", case(plugin, tmp_path / f"case{index}"))

        for index, (name, target, *edits, killer) in enumerate(MUTATIONS):
            pairs = edits[0] if len(edits) == 1 else [tuple(edits)]
            source = (PLUGIN / target).read_text(encoding="utf-8")
            counts = [source.count(before) for before, _ in pairs]
            if counts != [1] * len(pairs):
                check(f"変異が届いていない: {name}", False, f"壊す箇所の出現回数が {counts}")
                continue
            for before, after in pairs:
                source = source.replace(before, after)
            mutated = copy_plugin(tmp_path / f"mut{index}")
            (mutated / target).write_text(source, encoding="utf-8")
            try:
                survived = CASES[killer](mutated, tmp_path / f"mutwork{index}")
            except Exception:  # 壊した本体が例外で落ちるのも「期待どおりでない」
                survived = False
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not survived)
    check_copies()
    check_reference()

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件・写しと原本の照合")
    return 0


if __name__ == "__main__":
    sys.exit(main())
