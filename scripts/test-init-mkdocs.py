#!/usr/bin/env python3
"""spec-loop の MkDocs の雛形（`init-mkdocs.py` と、雛形のフック `spec_loop_pages.py`）の回帰テスト。

    python3 scripts/test-init-mkdocs.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/init-mkdocs.py` と `plugins/spec-loop/templates/mkdocs/`）。
ここで見るのは:

1. **写し方**——空の根には雛形をすべて（`gitignore` は `.gitignore` として）バイトどおりに写す。
   **`mkdocs.yml` が在れば何も写さない。** 在るファイル（シンボリックリンク・壊れたリンクを含む）は 1 バイトも変えず、
   `pyproject.toml`・`.gitignore` が在れば足りない依存・行を出力で示す。`--dry-run` は何も書かない。根がディレクトリでなければ 2。
2. **フックの描き方**——版ごとの節を番号の順（`v10` は `v2` の後）に、表の行をすべて、版をまたいで一意なアンカーで描く。
   セルの HTML と Markdown の記号・`|`・改行をエスケープする。空の `費用への影響` は注記を出さない。
   読めない表・見出しの違う表・知らない印は**警告**（`mkdocs` のロガー。`--strict` で落ちる）とページ上の注意書き。
   表が 1 つも無ければそう書き、警告は出さない。印の無いページは変えない。
3. **写しの突き合わせ**——フックの列名・状態・印は `check-qa-csv.py` の定数と同じ（フックは正本リポジトリへ写されて
   単独で動くので import できず、写しを持つ）。
4. **重ね合わせに混ざらない**——雛形を写した正本で `merge-versions.py` が通り、出力に表示用のファイルが入らない。
5. **決まりの原本（`references/tree.md`）の「ドキュメントのツール」の節が、写し方のコマンドを載せている。**

**`mkdocs build` は走らせない**（CI に MkDocs と Material の組を入れていない）。実際に組んで表が出ることは
dev-loop の検証で見る（#266 の計画ファイル）。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
"""
from __future__ import annotations

import importlib.util
import io
import logging
import os
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

HEADER = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
QA_V1 = HEADER + (
    "Q-001,要求確定,割引は <b>A</b> | B？,A: なし / B: 3%,A（業務部）,決定表 4 行目,反映済み,\n"
    "Q-002,実現性・コスト,夜間は？,A: 止める / B: 24 時間,未回答,—,確認中,B は月額 2 倍\n"
)
QA_V2 = HEADER + (
    "Q-002,実現性・コスト,夜間は（問い直し）？,A: 止める / B: 24 時間,B（部長）,—,確認中,B は月額 2 倍\n"
    '"Q-003",要求確定,"1 行目\n2 行目 *強調* `x` [y](z)",A: はい / B: いいえ,未回答,—,確認中,\n'
)
QA_V10 = HEADER + "Q-010,要求確定,十番目,A: はい / B: いいえ,未回答,—,確認中,\n"

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
    code, _ = run_init(plugin, root)
    expected = template_map(plugin)
    got = {k: v for k, v in snapshot(root).items() if isinstance(v, bytes)}
    return code == 0 and got == expected and len(expected) >= 6


def init_config_exists(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    write(root, {"mkdocs.yml": "site_name: 既存\n"})
    before = snapshot(root)
    code, out = run_init(plugin, root)
    return code == 0 and snapshot(root) == before and "何も写さない" in out


def init_keeps_existing(plugin: Path, work: Path) -> bool:
    root = work / "repo"
    write(root, {"pyproject.toml": '[project]\nname = "x"\ndependencies = ["requests"]\n',
                 ".gitignore": "site/\n", "docs/index.md": "# 既存の表紙\n"})
    before = snapshot(root)
    code, out = run_init(plugin, root)
    after = snapshot(root)
    kept = all(after[k] == v for k, v in before.items())
    wrote = {"mkdocs.yml", "docs/qa.md", "hooks/spec_loop_pages.py"} <= set(after)
    return (code == 0 and kept and wrote
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


def render(plugin: Path, docs: Path, markdown: str) -> tuple[str, list[str]]:
    hook = load_hook(plugin)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("mkdocs")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        page = SimpleNamespace(file=SimpleNamespace(src_path="qa.md"))
        out = hook.on_page_markdown(markdown, page, {"docs_dir": str(docs)}, None)
    finally:
        logger.removeHandler(handler)
    return out, [line for line in stream.getvalue().splitlines() if line]


def hook_versions(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1, "v2/shared/qa.csv": QA_V2})
    out, warnings = render(plugin, docs, "# Q&A\n\n<!-- spec-loop: qa -->\n")
    v1, v2 = out.index("## v1"), out.index("## v2")
    return (not warnings and out.startswith("# Q&A\n\n") and v1 < v2
            and "(#v1-q-001)" in out and "{#v1-q-002}" in out and "{#v2-q-002}" in out and "{#v2-q-003}" in out
            and "確認中 1 件（うち回答あり・未反映 0 件）・反映済み 1 件" in out[v1:v2]
            and "確認中 2 件（うち回答あり・未反映 1 件）・反映済み 0 件" in out[v2:]
            and "- A: 止める" in out and "- B: 24 時間" in out
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


def hook_cost(plugin: Path, work: Path) -> bool:
    docs = work / "docs"
    write(docs, {"v1/shared/qa.csv": QA_V1})
    out, _ = render(plugin, docs, "<!-- spec-loop: qa -->")
    return out.count('!!! note "費用への影響"') == 1 and "nan" not in out and "    B は月額 2 倍" in out


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
    "在るファイルは変えず、足りないものを示す": init_keeps_existing,
    "壊れたリンクも在るとみなす": init_symlink,
    "--dry-run は書かない": init_dry_run,
    "根がディレクトリでなければ 2": init_not_dir,
    "版ごとの節・アンカー・件数": hook_versions,
    "版は番号の順・形に合わない名前は読まない": hook_numeric_order,
    "セルをエスケープする": hook_escape,
    "費用への影響は空なら出さない": hook_cost,
    "見出しの違う表は警告": hook_bad_header,
    "読めない表は警告": hook_undecodable,
    "表が無ければそう書く": hook_no_table,
    "知らない印は警告": hook_unknown_marker,
    "印の無いページは変えない": hook_no_marker,
    "重ね合わせに表示用のファイルが混ざらない": merge_ignores_pages,
}

# (名前, 壊す対象, 壊す前, 壊した後, 殺すはずの試料の名前)。2 箇所を壊すときは (壊す前, 壊した後) の列を渡す
MUTATIONS: list[tuple] = [
    ("mkdocs.yml が在っても写す", INIT, "    if os.path.lexists(root / CONFIG):\n", "    if False:\n",
     "mkdocs.yml が在れば何も写さない"),
    # 在るかの確認と排他的な作成は二重の守りなので、片方だけ壊しても挙動は変わらない（等価変異）。両方を壊す。
    ("在るファイルを上書きする", INIT, [("        if os.path.lexists(dest):\n", "        if False:\n"),
                                       ('dest.open("xb")', 'dest.open("wb")')],
     "在るファイルは変えず、足りないものを示す"),
    ("リンクを辿って在るかを見る", INIT, [("        if os.path.lexists(dest):\n", "        if dest.exists():\n"),
                                         ('dest.open("xb")', 'dest.open("wb")')],
     "壊れたリンクも在るとみなす"),
    ("--dry-run でも書く", INIT, "        if not args.dry_run:\n", "        if True:\n", "--dry-run は書かない"),
    ("gitignore の名前を変えない", INIT, 'RENAMES = {"gitignore": ".gitignore"}', "RENAMES = {}",
     "空の根には雛形をすべて写す"),
    ("足りない依存を示さない", INIT, "            if names:\n", "            if False:\n",
     "在るファイルは変えず、足りないものを示す"),
    ("根を確かめない", INIT, "    if not root.is_dir():\n", "    if False:\n", "根がディレクトリでなければ 2"),
    ("版を名前の順に並べる", HOOK, "            found.append((int(entry.name[1:]), entry))",
     "            found.append((entry.name, entry))", "版は番号の順・形に合わない名前は読まない"),
    ("版の形を見ない", HOOK, "VERSION.fullmatch(entry.name) and ", "entry.name.startswith('v') and ",
     "版は番号の順・形に合わない名前は読まない"),
    ("アンカーに版を入れない", HOOK, 'return f"v{version}-{number.lower()}"', "return number.lower()",
     "版ごとの節・アンカー・件数"),
    ("HTML をエスケープしない", HOOK, "html.escape(value.replace", "str(value.replace", "セルをエスケープする"),
    ("| をエスケープしない", HOOK, r'MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]#|])")',
     r'MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]#])")', "セルをエスケープする"),
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
    ("回答あり未反映を数えない", HOOK, ' and row["回答"] != QA_NO_ANSWER for row in rows)', " and False for row in rows)",
     "版ごとの節・アンカー・件数"),
]


def check_copies() -> None:
    """フックの写しが check-qa-csv.py の定数と同じか。"""
    hook = load_hook(PLUGIN)
    spec = importlib.util.spec_from_file_location("check_qa_csv", PLUGIN / "scripts" / "check-qa-csv.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    for name, theirs in (("QA_COLUMNS", checker.COLUMNS), ("QA_DONE", checker.DONE),
                         ("QA_NO_ANSWER", checker.NO_ANSWER), ("QA_OPTION_SEPARATOR", checker.OPTION_SEPARATOR)):
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
    for word in ("scripts/init-mkdocs.py", "mkdocs.yml", "docs/qa.md", "shared/"):
        check(f"references/tree.md の「ドキュメントのツール」に {word} が無い", word in section)


def main() -> int:
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
