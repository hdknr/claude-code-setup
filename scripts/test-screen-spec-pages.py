#!/usr/bin/env python3
"""screen-spec の MkDocs のフック（#1098）の回帰テスト。

    python3 scripts/test-screen-spec-pages.py

**本体はプラグインの中にある**——フックの本体 `plugins/screen-spec/scripts/mkdocs-pages.py`、正本に登録する薄いフック
`plugins/screen-spec/templates/mkdocs/screen_spec_pages.py`、登録の入口 `write-screens.py mkdocs`。登録の口は spec-loop の雛形のフック
（`plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py`）と `init-mkdocs.py --hook` にある（そちらの試料は `test-init-mkdocs.py`）。

一時ディレクトリに `plugins/screen-spec/`（本体）と `plugins/spec-loop/`（本物の spec-loop の `.claude-plugin/`・`scripts/`・`templates/` の写し）を並べ、
正本（`docs/v1/`〜）に **`write-screens.py mkdocs` で登録し**、**正本に写った spec-loop のフック**を読み込んで MkDocs のイベントを直に呼ぶ
（`mkdocs build` は CI に無いので走らせない——`test-init-mkdocs.py` と同じ形。`File` は偽物を `mkdocs.structure.files` に差す）。見るもの:

1. **#1098 の受入基準**——登録した案件で `init-mkdocs.py` を回し直しても登録が消えない（`write-screens.py mkdocs` と `init-mkdocs.py` のどちらで回しても。
   `mkdocs.yml` を書き換えない）・`docs/mocks.md` に版ごとの生成したモックへのリンクが出る（手で書いたモックと並ぶ。モックはサイトに置かれ、中の仕様書へのリンクは
   サイトのページを指す）・画面の表の行が仕様書の節に表として出る（節ごとの行と列・版ごとの重ね方・共有の層だけ・未決定の `⚠️` の飾り）。
2. **ほかの決まり**——散文の節の印・当たる画面の無い仕様書・コードブロックの中の印・仕様書でないページ（案件の雛形）・作れない版・
   screen-spec が見つからない（環境変数の誤り・記録が無い）ときの警告と注意書き・記録（`installed_plugins.json`）から見つけること・案件の雛形をサイトに出さないこと・
   `write-screens.py mkdocs` の終了コード。
3. **本体の定数が `plugins/screen-spec/references/mkdocs.md` の原本と一致する**（節ごとの行・種類・列、モックの置き場所と名前、見つけ方の環境変数、登録するファイル）。
   列は `build-mock.py` の許可の列の中で、節は `check-screens.py` の「表で持つ」節と同じ。薄いフックの印と表の場所は `check-screens.py` と同じ。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、`HOME`・`CLAUDE_CONFIG_DIR` を一時ディレクトリにし、`SCREEN_SPEC_SPEC_LOOP` を外す。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる（壊す箇所が本体にちょうど 1 回現れることを先に確かめる）。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from types import SimpleNamespace

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "screen-spec"
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
IMPL = Path("scripts") / "mkdocs-pages.py"
SHIM = Path("templates") / "mkdocs" / "screen_spec_pages.py"
WRITE = Path("scripts") / "write-screens.py"
BUILD = Path("scripts") / "build-mock.py"
REFERENCE = PLUGIN / "references" / "mkdocs.md"

SD = "requirements/screens/"
DATA = SD + "data/"
S_HEAD = "画面ID,画面名,種別,親画面,主たる利用者,ステータス,参考資料,目的と背景,できること,機能,帳票,仕様書,根拠\n"
I_HEAD = "番号,画面ID,まとまり,並び順,項目名,種類,中身,例,必須,入力チェック,エラーメッセージ,並び替え,絞り込み,根拠\n"
T_HEAD = "番号,遷移元,きっかけ,操作,条件,遷移先,結果,根拠\n"
QA_HEAD = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"

V1_SCREENS = S_HEAD + (
    "S-001,受注一覧,top,,担当者,記入中,,受注を探す,一覧と絞り込み,F-001,,order-list.md,Q-R-001\n"
    "S-002,受注登録,form,,担当者,記入中,,未定（Q-R-001）,入力,F-002,,order-new.md,F-002、D-S-001\n")
V1_ITEMS = I_HEAD + (
    "I-012,S-001,受注の一覧,3,顧客名,一覧の列,顧客の名前,山田商店,,,,いいえ,いいえ,Q-R-001\n"
    "I-010,S-001,一覧,1,受注の一覧,一覧,受注の並び,,,,,,,Q-R-001\n"
    "I-011,S-001,受注の一覧,2,受注日,一覧の列,受注した日,2026/11/16,,,,はい,はい,Q-R-001\n"
    "I-013,S-001,操作,4,新規,ボタン,,,,,,,,F-002\n"
    "I-014,S-001,一覧,10,件数,表示,件数の表示,3 件,,,,,,F-001\n"
    "I-020,S-002,入力,1,顧客名,入力,顧客の名前,山田,はい,30 文字まで,30 文字までで入れてください,,,F-002\n"
    "I-021,S-002,操作,2,保存,ボタン,,,,,,,,F-002\n")
V1_TRANSITIONS = T_HEAD + (
    "T-001,S-001,I-013,受注の登録,担当者のみ（D-S-001）,S-002,,F-002\n"
    "T-002,S-002,I-021,受注の登録,,S-001,保存した,F-002\n"
    "T-003,S-001,I-014,,,S-002,,F-001\n")   # 条件の無い遷移（権限の節に出さない）
V2_SCREENS = S_HEAD + "S-001,受注一覧,top,,担当者,記入中,,受注を探す,一覧と絞り込みと並び替え,F-001,,order-list.md,Q-R-001\n" + (
    "S-002,受注登録,form,,担当者,記入中,,未定（Q-R-001）,入力と確認,F-002,,order-new.md,F-002、D-S-001\n")  # 仕様書を v2 に写さずに表だけ変える
TABLED = ["1. 基本情報", "2. 画面概要", "3. レイアウト", "4. データ表示", "5. 操作とアクション", "6. 入力とバリデーション",
          "8. 権限とデータの見える範囲", "12. 一覧・表の能力", "13. 画面遷移"]
MARK = "<!-- screen-spec: 表 -->"


def spec_page(key: str) -> str:
    out = [f"# {key}", ""]
    for name in ["1. 基本情報", "2. 画面概要", "3. レイアウト", "4. データ表示", "5. 操作とアクション", "6. 入力とバリデーション", "7. 状態",
                 "8. 権限とデータの見える範囲", "9. 他システム連携", "10. 同時編集", "11. 表示ルール", "12. 一覧・表の能力", "13. 画面遷移", "未決の論点"]:
        out += [f"## {name}", "", MARK if name in TABLED else "N/A。無い", ""]
    return "\n".join(out)


def base_files() -> dict[str, str]:
    return {
        "docs/v1/shared/qa.csv": QA_HEAD + "Q-R-001,要求確定,質問,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n",
        "docs/v1/spec/qa-dev.csv": QA_HEAD + "D-S-001,仕様レビュー,質問,A: はい / B: いいえ,A,理由,未回答,—,確認中,\n",
        "docs/v1/" + DATA + "screens.csv": V1_SCREENS,
        "docs/v1/" + DATA + "screen-items.csv": V1_ITEMS,
        "docs/v1/" + DATA + "transitions.csv": V1_TRANSITIONS,
        "docs/v1/" + SD + "order-list.md": spec_page("S-001 受注一覧"),
        "docs/v1/" + SD + "order-new.md": spec_page("S-002 受注登録"),
        "docs/v1/" + SD + "templates/spec.md": "# {{画面ID}} {{画面名}}\n\n## 1. 基本情報\n\n" + MARK + "\n",
        "docs/v1/requirements/mocks/手書き.html": "<p>手</p>\n",
        "docs/v2/" + DATA + "screens.csv": V2_SCREENS,
        "docs/v2/" + SD + "order-list.md": spec_page("S-001 受注一覧"),
    }


failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def layout(work: Path, plugin: Path) -> tuple[Path, Path]:
    """一時ディレクトリに plugins/screen-spec（`plugin` の写し）と plugins/spec-loop（本物の写し）を並べる。"""
    assert_in_tmp(work)
    screen = work / "plugins" / "screen-spec"
    shutil.copytree(plugin, screen, ignore=shutil.ignore_patterns("__pycache__"))
    spec_loop = work / "plugins" / "spec-loop"
    for part in (".claude-plugin", "scripts", "templates"):
        shutil.copytree(SPEC_LOOP / part, spec_loop / part, ignore=shutil.ignore_patterns("__pycache__"))
    return screen, spec_loop


def write_files(root: Path, files: dict[str, str]) -> None:
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def clean_env(work: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_CONFIG_DIR", "SCREEN_SPEC_SPEC_LOOP", "SCREEN_SPEC_PLUGIN")}
    home = work / "home"
    home.mkdir(exist_ok=True)
    env["HOME"] = str(home)
    env["CLAUDE_CONFIG_DIR"] = str(home / ".claude")
    return env


def run(script: Path, *args: str, env: dict[str, str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-I", str(script), *args], capture_output=True, text=True, env=env, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def snapshot(root: Path, skip: tuple[str, ...] = ()) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and not p.relative_to(root).as_posix().startswith(skip)}


def project(work: Path, plugin: Path, files: dict[str, str] | None = None) -> tuple[Path, Path, Path, dict[str, str]]:
    """(正本の根, screen-spec, spec-loop, 環境)。正本に `write-screens.py mkdocs` で登録しておく。"""
    screen, spec_loop = layout(work, plugin)
    root = work / "repo"
    write_files(root, base_files() if files is None else files)
    env = clean_env(work)
    code, out = run(screen / WRITE, "mkdocs", str(root / "docs"), env=env)
    assert code == 0, out
    return root, screen, spec_loop, dict(env, SCREEN_SPEC_PLUGIN=str(screen))


# ---- MkDocs の偽物（File と Files）

class FakeFile:
    def __init__(self, path, src_dir, dest_dir, use_directory_urls):
        self.src_uri = self.src_path = path
        self.abs_src_path = os.path.join(src_dir, path)
        self.dest_dir = dest_dir
        self.use_directory_urls = use_directory_urls


class FakeFiles(list):
    def get_file_from_path(self, path):
        return next((f for f in self if f.src_uri == path), None)


@contextlib.contextmanager
def mkdocs_env(env: dict[str, str]):
    """偽の `mkdocs.structure.files` を差し、環境変数を差し替え、`mkdocs` のロガーの警告を集める。"""
    saved_modules = {name: sys.modules.get(name) for name in ("mkdocs", "mkdocs.structure", "mkdocs.structure.files")}
    package = types.ModuleType("mkdocs")
    structure = types.ModuleType("mkdocs.structure")
    files = types.ModuleType("mkdocs.structure.files")
    files.File = FakeFile
    package.structure = structure
    structure.files = files
    sys.modules.update({"mkdocs": package, "mkdocs.structure": structure, "mkdocs.structure.files": files})
    saved_env = dict(os.environ)
    os.environ.clear()
    os.environ.update(env)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("mkdocs")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        yield stream
    finally:
        logger.removeHandler(handler)
        os.environ.clear()
        os.environ.update(saved_env)
        for name, module in saved_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def load_project_hook(root: Path):
    spec = importlib.util.spec_from_file_location(f"project_spec_loop_{abs(hash(str(root)))}", root / "hooks" / "spec_loop_pages.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def page(src: str):
    return SimpleNamespace(file=SimpleNamespace(src_path=src, src_uri=src))


def build(root: Path, env: dict[str, str], pages: dict[str, str], use_directory_urls: bool = False,
          extra_files: list[str] = ()) -> tuple[FakeFiles, dict[str, str], list[str]]:
    """正本のフックで on_files と各ページの on_page_markdown を回す（MkDocs の順）。(files, ページ → 出力, 警告)。"""
    with mkdocs_env(env) as stream:
        hook = load_project_hook(root)
        config = {"docs_dir": str(root / "docs"), "site_dir": str(root / "site"), "use_directory_urls": use_directory_urls}
        files = FakeFiles(FakeFile(src, str(root / "docs"), str(root / "site"), use_directory_urls) for src in [*pages, *extra_files])
        files = hook.on_files(files, config=config)
        out = {src: hook.on_page_markdown(markdown, page(src), config, files) for src, markdown in pages.items()}
    return files, out, [line for line in stream.getvalue().splitlines() if line]


def section(markdown: str, name: str) -> str:
    start = markdown.find(f"## {name}\n")
    if start < 0:
        return ""
    end = markdown.find("\n## ", start + 1)
    return markdown[start:end if end >= 0 else len(markdown)]


def spec_pages(root: Path) -> dict[str, str]:
    return {f"v1/{SD}order-list.md": (root / "docs" / "v1" / SD / "order-list.md").read_text(encoding="utf-8"),
            f"v1/{SD}order-new.md": (root / "docs" / "v1" / SD / "order-new.md").read_text(encoding="utf-8"),
            f"v2/{SD}order-list.md": (root / "docs" / "v2" / SD / "order-list.md").read_text(encoding="utf-8")}


# ---- 試料（screen-spec の写し, 作業場所）→ 期待どおりか

def registered_kept(plugin: Path, work: Path) -> bool:
    """`write-screens.py mkdocs` で登録した案件で、`init-mkdocs.py` を回し直しても登録は消えず、mkdocs.yml を書き換えない（受入基準 1）。"""
    root, screen, spec_loop, env = project(work, plugin)
    reg = root / "hooks" / "spec_loop_plugins" / "screen_spec_pages.py"
    first = reg.read_bytes() if reg.is_file() else None
    config = (root / "mkdocs.yml").read_bytes()
    results = [first == (screen / SHIM).read_bytes()]
    code, out = run(spec_loop / "scripts" / "init-mkdocs.py", str(root), env=env)
    results.append(code == 0 and reg.read_bytes() == first and (root / "mkdocs.yml").read_bytes() == config)
    code, out = run(screen / WRITE, "mkdocs", str(root / "docs"), env=env)
    results.append(code == 0 and "既に登録してある" in out and reg.read_bytes() == first and (root / "mkdocs.yml").read_bytes() == config)
    return all(results)


def tables_in_sections(plugin: Path, work: Path) -> bool:
    """画面の表の行が、仕様書の節に表として出る（受入基準 3）——節ごとの行と列・版ごとの重ね方・共有の層だけ・未決定の飾り。"""
    root, _, _, env = project(work, plugin)
    _, out, warnings = build(root, env, spec_pages(root))
    s1 = out[f"v1/{SD}order-list.md"]
    s2 = out[f"v1/{SD}order-new.md"]
    v2 = out[f"v2/{SD}order-list.md"]
    layout_rows = [line.split(" | ")[2] for line in section(s1, "3. レイアウト").splitlines() if line.startswith("| ") and "I-0" in line]
    return (not warnings and MARK not in s1 + s2 + v2
            and "| 画面ID | S-001 |" in section(s1, "1. 基本情報") and "| 呼び出し元 | S-002（T-002） |" in section(s1, "1. 基本情報")
            and "| できること | 一覧と絞り込み |" in section(s1, "2. 画面概要") and "| できること | 一覧と絞り込みと並び替え |" in section(v2, "2. 画面概要")
            and "| できること | 入力と確認 |" in section(s2, "2. 画面概要")
            and layout_rows == ["I-011", "I-012", "I-010", "I-014", "I-013"]
            and "I-014" in section(s1, "4. データ表示") and "I-011" in section(s1, "4. データ表示") and "I-013" not in section(s1, "4. データ表示")
            and "| T-001 | I-013 | 受注の登録 | 担当者のみ | S-002 |" in section(s1, "5. 操作とアクション")
            and "この画面に当たる行は無い" in section(s1, "6. 入力とバリデーション")
            and "| I-020 | 顧客名 | はい | 30 文字まで | 30 文字までで入れてください | 山田 | F-002 |" in section(s2, "6. 入力とバリデーション")
            and "T-001" in section(s1, "8. 権限とデータの見える範囲") and "T-002" not in section(s1, "8. 権限とデータの見える範囲")
            and "T-003" not in section(s1, "8. 権限とデータの見える範囲") and "T-003" in section(s1, "5. 操作とアクション")
            and "| I-011 | 受注の一覧 | 受注日 | 一覧の列 | はい | はい |" in section(s1, "12. 一覧・表の能力")
            and "T-001" in section(s1, "13. 画面遷移") and "T-002" in section(s1, "13. 画面遷移")
            and "D-S-001" not in s1 + s2 + v2 and "| 根拠 | F-002 |" in section(s2, "1. 基本情報")
            and "| 目的と背景 | ⚠️ 未定（Q-R-001） |" in section(s2, "2. 画面概要") and "⚠️" not in s1
            and "N/A。無い" in section(s1, "7. 状態")
            and "（v1〜v1 を重ねた表の行）" in section(s1, "2. 画面概要") and "（v1〜v2 を重ねた表の行）" in section(s2, "2. 画面概要"))


def later_versions(plugin: Path, work: Path) -> bool:
    """後の版の重ね合わせの誤りで前の版のページを止めない・後の版で画面を消しても、消す手前の版の行を出す・
    同じ名前の仕様書を指す画面が 2 つあれば注意書き。"""
    files = base_files()
    files["docs/v3/removed.csv"] = "種類,対象,理由\n画面,S-002,やめた\n"
    files["docs/v4/" + DATA + "screens.csv"] = S_HEAD.replace("根拠", "根拠X")
    root, _, _, env = project(work, plugin, files)
    _, out, _ = build(root, env, spec_pages(root))
    s2 = out[f"v1/{SD}order-new.md"]
    dup = base_files()
    dup["docs/v2/" + DATA + "screens.csv"] = V2_SCREENS + "S-003,重なる,detail,,担当者,記入中,,x,x,F-001,,order-new.md,F-001\n"
    root2, _, _, env2 = project(work / "dup", plugin, dup)
    _, out2, warnings2 = build(root2, env2, spec_pages(root2))
    return ("| できること | 入力と確認 |" in section(s2, "2. 画面概要") and "（v1〜v2 を重ねた表の行）" in section(s2, "2. 画面概要")
            and "表示できない" not in s2
            and "2 つある" in out2[f"v1/{SD}order-new.md"] and "| できること |" not in out2[f"v1/{SD}order-new.md"] and bool(warnings2))


def marks_left_alone(plugin: Path, work: Path) -> bool:
    """仕様書でないページ（案件の雛形・版の外）とコードブロックの中の印は変えない。散文の節の印・当たる画面の無い仕様書は警告と注意書き。"""
    root, _, _, env = project(work, plugin)
    fenced = "# x\n\n## 1. 基本情報\n\n```\n" + MARK + "\n```\n\n## 7. 状態\n\n" + MARK + "\n"
    pages = {f"v1/{SD}templates/spec.md": "## 1. 基本情報\n\n" + MARK + "\n", "notes.md": "## 1. 基本情報\n\n" + MARK + "\n",
             f"v1/{SD}order-list.md": fenced, f"v1/{SD}unknown.md": "## 1. 基本情報\n\n" + MARK + "\n"}
    _, out, warnings = build(root, env, pages)
    listed = out[f"v1/{SD}order-list.md"]
    return (out[f"v1/{SD}templates/spec.md"] == pages[f"v1/{SD}templates/spec.md"] and out["notes.md"] == pages["notes.md"]
            and "```\n" + MARK + "\n```" in listed and "表で持つ節の外にある" in section(listed, "7. 状態")
            and "表示できない" in out[f"v1/{SD}unknown.md"] and MARK not in out[f"v1/{SD}unknown.md"]
            and len(warnings) == 2)


def mocks_page(plugin: Path, work: Path) -> bool:
    """docs/mocks.md に、版ごとの生成したモックへのリンクが出る（受入基準 2）——手で書いたモックと並び、モックはサイトに置かれ（偽の File）、
    中の仕様書へのリンクはサイトのページを指す。案件の雛形はサイトに出さない。"""
    root, _, _, env = project(work, plugin)
    pages = {"mocks.md": (root / "docs" / "mocks.md").read_text(encoding="utf-8")}
    files, out, warnings = build(root, env, pages, extra_files=[f"v1/{SD}templates/spec.md", f"v1/{SD}order-list.md"])
    text = out["mocks.md"]
    v1, v2 = text.find("## v1"), text.find("## v2")
    placed = {f.src_uri: f for f in files}
    mock_v1 = root / "build" / "mock" / "v1" / "index.html"
    data = {}
    if mock_v1.is_file():
        found = re.search(r'id="screen-spec-data">(.*?)</script>', mock_v1.read_text(encoding="utf-8"), re.S)
        data = json.loads(found.group(1)) if found else {}
    return (not warnings and 0 <= v1 < v2
            and "| [画面モック（表から生成）](mock/v1/index.html) | HTML（screen-spec が生成） |" in text[v1:v2]
            and "手書き" in text[v1:v2]
            and "| [画面モック（表から生成）](mock/v2/index.html) | HTML（screen-spec が生成） |" in text[v2:]
            and "mock/v1/index.html" in placed and "mock/v2/index.html" in placed
            and Path(placed["mock/v1/index.html"].abs_src_path).resolve() == mock_v1.resolve()
            and f"v1/{SD}templates/spec.md" not in placed and f"v1/{SD}order-list.md" in placed
            and data.get("documents", {}).get("S-001") == "../../v1/requirements/screens/order-list.html")


def mocks_directory_urls(plugin: Path, work: Path) -> bool:
    """use_directory_urls のサイトでは、モックの中の仕様書へのリンクはディレクトリの URL を指す。"""
    root, _, _, env = project(work, plugin)
    build(root, env, {}, use_directory_urls=True)
    page_text = (root / "build" / "mock" / "v2" / "index.html").read_text(encoding="utf-8")
    data = json.loads(re.search(r'id="screen-spec-data">(.*?)</script>', page_text, re.S).group(1))
    return data["documents"].get("S-001") == "../../v2/requirements/screens/order-list/"


def mocks_broken_version(plugin: Path, work: Path) -> bool:
    """作れない版（見出し行が前の版と違う）は、警告し、モックのページのその版の節に理由を出す。ほかの版は作る。"""
    files = base_files()
    files["docs/v3/" + DATA + "screens.csv"] = S_HEAD.replace("根拠", "根拠X")
    root, _, _, env = project(work, plugin, files)
    pages = {"mocks.md": (root / "docs" / "mocks.md").read_text(encoding="utf-8")}
    placed, out, warnings = build(root, env, pages)
    text = out["mocks.md"]
    v3 = text.find("## v3")
    return (v3 > 0 and "画面モックを作れない" in text[v3:] and "mock/v3/index.html" not in {f.src_uri for f in placed}
            and "mock/v1/index.html" in {f.src_uri for f in placed} and len(warnings) == 2)


def not_found(plugin: Path, work: Path) -> bool:
    """screen-spec が見つからない（記録が無い・環境変数が screen-spec でない）なら、警告し、仕様書の印とモックのページに注意書きを置く。"""
    root, _, spec_loop, env = project(work, plugin)
    env.pop("SCREEN_SPEC_PLUGIN")
    pages = {"mocks.md": (root / "docs" / "mocks.md").read_text(encoding="utf-8"), **spec_pages(root)}
    _, out, warnings = build(root, env, pages)
    bad = dict(env, SCREEN_SPEC_PLUGIN=str(spec_loop))
    _, out2, warnings2 = build(root, bad, pages)
    return (not any(env.get(k) for k in ("SCREEN_SPEC_PLUGIN",))
            and "screen-spec が見つからない" in out[f"v1/{SD}order-list.md"] and MARK not in out[f"v1/{SD}order-list.md"]
            and "画面モックを作れない" in out["mocks.md"] and "## v2" in out["mocks.md"] and warnings
            and "screen-spec のプラグインの根でない" in out2[f"v1/{SD}order-list.md"] and warnings2)


def found_in_record(plugin: Path, work: Path) -> bool:
    """環境変数が無ければ、Claude Code のプラグインの記録（installed_plugins.json の screen-spec@…）から見つける。"""
    root, screen, _, env = project(work, plugin)
    env.pop("SCREEN_SPEC_PLUGIN")
    config = Path(env["CLAUDE_CONFIG_DIR"])
    (config / "plugins").mkdir(parents=True)
    (config / "plugins" / "installed_plugins.json").write_text(json.dumps(
        {"version": 2, "plugins": {"screen-spec@m": [{"scope": "user", "installPath": str(screen)}],
                                   "spec-loop@m": [{"scope": "user", "installPath": "/nowhere"}]}}), encoding="utf-8")
    _, out, warnings = build(root, env, spec_pages(root))
    return not warnings and "| 画面ID | S-001 |" in out[f"v1/{SD}order-list.md"]


def found_by_env(plugin: Path, work: Path) -> bool:
    """環境変数 SCREEN_SPEC_PLUGIN が screen-spec の根なら、それを使う（記録は見ない）。"""
    root, screen, _, env = project(work, plugin)
    config = Path(env["CLAUDE_CONFIG_DIR"])
    (config / "plugins").mkdir(parents=True)  # 記録は別のもの（見つからない）を指す——環境変数のほうで見つける
    (config / "plugins" / "installed_plugins.json").write_text(json.dumps(
        {"version": 2, "plugins": {"screen-spec@m": [{"scope": "user", "installPath": "/nowhere"}]}}), encoding="utf-8")
    _, out, warnings = build(root, env, spec_pages(root))
    return not warnings and "| 画面ID | S-001 |" in out[f"v1/{SD}order-list.md"]


def write_screens_codes(plugin: Path, work: Path) -> bool:
    """`write-screens.py mkdocs`: spec-loop が見つからなければ 4、init-mkdocs.py が 0 以外なら 2（何も登録しない）。"""
    screen, spec_loop = layout(work, plugin)
    root = work / "repo"
    write_files(root, base_files())
    env = clean_env(work)
    (root / "hooks").write_text("ファイル\n", encoding="utf-8")  # hooks がファイルなら init-mkdocs.py は書けずに 2
    code, out = run(screen / WRITE, "mkdocs", str(root / "docs"), env=env)
    shutil.rmtree(spec_loop)
    code2, _ = run(screen / WRITE, "mkdocs", str(root / "docs"), env=env)
    return code == 2 and "登録していない" in out and code2 == 4 and not (root / "mkdocs.yml").exists()


def env_for(work: Path, screen: Path) -> dict[str, str]:
    return dict(clean_env(work), SCREEN_SPEC_PLUGIN=str(screen))


CASES = {
    "登録した案件で回し直しても登録は消えない": registered_kept,
    "画面の表の行が仕様書の節に表として出る": tables_in_sections,
    "後の版の誤り・消した画面・重なる仕様書": later_versions,
    "仕様書でないページとコードブロックの印は変えず、散文の節と当たらない仕様書は注意書き": marks_left_alone,
    "docs/mocks.md に版ごとの生成したモックへのリンクが出る": mocks_page,
    "use_directory_urls のサイトでは仕様書のディレクトリの URL を指す": mocks_directory_urls,
    "作れない版はモックのページに理由を出す": mocks_broken_version,
    "screen-spec が見つからなければ警告と注意書き": not_found,
    "記録から screen-spec を見つける": found_in_record,
    "環境変数の screen-spec を使う": found_by_env,
    "write-screens.py mkdocs の終了コード": write_screens_codes,
}

# (名前, 壊す対象, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple] = [
    ("D- を外さない", IMPL, "        shown = self.sharer.clean(value or \"\")\n", "        shown = value or \"\"\n", "画面の表の行が仕様書の節に表として出る"),
    ("⚠️ を付けない", IMPL, "        return DECORATION + text if self.find_markers(shown) else text\n", "        return text\n",
     "画面の表の行が仕様書の節に表として出る"),
    ("呼び出し元を出さない", IMPL, "                pairs.append((CALLERS, checks.SEPARATOR.join(callers)))\n", "                pass\n",
     "画面の表の行が仕様書の節に表として出る"),
    ("項目を並び順で並べない", IMPL, "            return sorted(rows, key=order)\n", "            return rows\n", "画面の表の行が仕様書の節に表として出る"),
    ("項目の種類で絞らない", IMPL, ' and (not kinds or r.get("種類", "").strip() in kinds)]', "]", "画面の表の行が仕様書の節に表として出る"),
    ("条件の無い遷移も権限の節に出す", IMPL, ' and r.get("条件", "").strip()]', "]", "画面の表の行が仕様書の節に表として出る"),
    ("遷移先の遷移を画面遷移の節に出さない", IMPL, '            return [r for r in source if screen_id in (r.get("遷移元", "").strip(), r.get("遷移先", "").strip())]',
     '            return [r for r in source if screen_id == r.get("遷移元", "").strip()]', "画面の表の行が仕様書の節に表として出る"),
    ("表だけ変えた後の版を見ない", IMPL, "    for upto in range(last_version_of(docs, version, document), version - 1, -1):\n",
     "    for upto in range(version, version - 1, -1):\n",
     "画面の表の行が仕様書の節に表として出る"),
    ("後の版の仕様書を見ない", IMPL, "            return number - 1\n", "            pass\n", "画面の表の行が仕様書の節に表として出る"),
    ("版の重ね方を見ない", IMPL, "            _, whole, checker = merged(docs, upto)\n", "            _, whole, checker = merged(docs, None)\n",
     "画面の表の行が仕様書の節に表として出る"),
    ("後の版の誤りで前の版のページを止める", IMPL, "            if upto == version:\n                raise\n", "            raise\n",
     "後の版の誤り・消した画面・重なる仕様書"),
    ("重なる仕様書で前の版に戻る", IMPL, "        if len(found) > 1:\n", "        if False:\n", "後の版の誤り・消した画面・重なる仕様書"),
    ("画面を消した版で下へ探さない", IMPL, "        if found:\n            return found[0], tables, upto\n",
     "        if True:\n            raise Problem('消した')\n", "後の版の誤り・消した画面・重なる仕様書"),
    ("どの版まで重ねたかを書かない", IMPL, 'f"{RANGE.format(upto=upto)}\\n\\n" + ', "", "画面の表の行が仕様書の節に表として出る"),
    ("節を見ずに出す", IMPL, "        if section not in SECTION_TABLES:\n", "        if section not in SECTION_TABLES and False:\n",
     "仕様書でないページとコードブロックの印は変えず、散文の節と当たらない仕様書は注意書き"),
    ("コードブロックの中も置き換える", IMPL, "        if fence is not None:\n", "        if False:\n",
     "仕様書でないページとコードブロックの印は変えず、散文の節と当たらない仕様書は注意書き"),
    ("仕様書でないページも置き換える", IMPL, "        return markdown  # 仕様書でないページ", "        match = PAGE.match('v1/' + checks.SCREENS_DIR + 'order-list.md')  # 仕様書でないページ",
     "仕様書でないページとコードブロックの印は変えず、散文の節と当たらない仕様書は注意書き"),
    ("モックをサイトに置かない", IMPL, "        files.append(File(src_uri, str(source_dir), config[\"site_dir\"], use_directory_urls))\n", "",
     "docs/mocks.md に版ごとの生成したモックへのリンクが出る"),
    ("モックの行を出さない", IMPL, '        rows.append({"version": number, "name": MOCK_NAME, "path": src_uri, "kind": MOCK_KIND})\n', "",
     "docs/mocks.md に版ごとの生成したモックへのリンクが出る"),
    ("仕様書へのリンクをサイトに向けない", IMPL, ", link=site_link(docs, number, use_directory_urls))", ")",
     "docs/mocks.md に版ごとの生成したモックへのリンクが出る"),
    ("案件の雛形をサイトに出す", IMPL, "            files.remove(file)\n", "            pass\n", "docs/mocks.md に版ごとの生成したモックへのリンクが出る"),
    ("ディレクトリの URL を見ない", IMPL, "    if not use_directory_urls:\n        return stem + \".html\"\n", "    return stem + \".html\"\n",
     "use_directory_urls のサイトでは仕様書のディレクトリの URL を指す"),
    ("作れない版を黙って飛ばす", IMPL, '            rows.append({"version": number, "problem": f"画面モックを作れない（{e}）"})\n', "",
     "作れない版はモックのページに理由を出す"),
    ("見つからなくても注意書きを置かない", SHIM, '    return "\\n".join(notice(reason) if line.strip() == MARK else line for line in markdown.split("\\n"))',
     "    return markdown", "screen-spec が見つからなければ警告と注意書き"),
    ("見つからなくてもモックのページに出さない", SHIM, '            out.append({"version": int(entry.name[1:]), "problem": f"画面モックを作れない（{reason}）"})', "            pass",
     "screen-spec が見つからなければ警告と注意書き"),
    ("環境変数の誤りで記録へ進む", SHIM, '        return (root, "") if is_screen_spec(root) else (None, f"{ENV} が指す {root} は screen-spec のプラグインの根でない")',
     '        if is_screen_spec(root):\n            return root, ""', "screen-spec が見つからなければ警告と注意書き"),
    ("記録を見ない", SHIM, "    root = installed(docs)\n", "    root = None\n", "記録から screen-spec を見つける"),
    ("環境変数を見ない", SHIM, "    named = os.environ.get(ENV)\n", "    named = None\n", "環境変数の screen-spec を使う"),
    ("init-mkdocs.py の失敗を 0 にする", WRITE, "    if proc.returncode != 0:\n", "    if False:\n", "write-screens.py mkdocs の終了コード"),
    ("--hook を渡さない", WRITE, ', "--hook", str(MKDOCS_HOOK)]', "]", "登録した案件で回し直しても登録は消えない"),
    ("link を使わない", BUILD, "                links[key] = link(path) if link else", "                links[key] =",
     "docs/mocks.md に版ごとの生成したモックへのリンクが出る"),
]


# ---- 原本との突き合わせ

def table_rows(markdown: str, heading_cells: list[str]) -> list[list[str]]:
    """見出しが `heading_cells` の表（いくつあっても）の行。"""
    lines = markdown.splitlines()
    header = "| " + " | ".join(heading_cells) + " |"
    rows = []
    for at, line in enumerate(lines):
        if line != header:
            continue
        for row in lines[at + 2:]:
            if not row.startswith("|"):
                break
            rows.append([cell.strip() for cell in row.strip().strip("|").split(" | ")])
    return rows


def ticks(cell: str) -> list[str]:
    return re.findall(r"`([^`]+)`", cell)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_reference() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    impl = load(PLUGIN / IMPL, "screen_spec_mkdocs_pages_ref")
    shim = load(PLUGIN / SHIM, "screen_spec_shim_ref")
    write = load(PLUGIN / WRITE, "screen_spec_write_ref")
    rows = table_rows(text, ["節", "行", "種類", "列"])
    found = {ticks(r[0])[0]: (r[1], tuple(ticks(r[2])), ticks(r[3])) for r in rows if ticks(r[0])}
    check("references/mkdocs.md の節の表が本体の SECTION_TABLES と違う", found == impl.SECTION_TABLES,
          f"{found!r} != {impl.SECTION_TABLES!r}")
    tabled = [name for name, is_table in impl.checks.SECTIONS if is_table]
    check("本体の SECTION_TABLES の節が check-screens.py の「表で持つ」節と違う", list(impl.SECTION_TABLES) == tabled)
    shown = set(impl.mock.SHOWN["screens"]) | set(impl.mock.SHOWN["items"]) | set(impl.mock.SHOWN["transitions"])
    outside = [c for _, _, columns in impl.SECTION_TABLES.values() for c in columns if c not in shown]
    check("節に出す列が build-mock.py の許可の列の外にある", not outside, ", ".join(outside))
    kinds = [k for _, ks, _ in impl.SECTION_TABLES.values() for k in ks if k not in impl.checks.ITEM_KINDS]
    check("節の種類が check-screens.py の項目の種類の外にある", not kinds, ", ".join(kinds))
    mocks = dict((r[0], r[1]) for r in table_rows(text, ["決まり", "値"]))
    check("サイトの中の置き場所が違う", mocks.get("サイトの中の置き場所") == f"`{impl.SITE_DIR}/v<n>/{impl.mock.OUT_NAME}`")
    check("モックのページの名前が違う", mocks.get("モックのページの名前") == f"`{impl.MOCK_NAME}`")
    check("モックのページの形式が違う", mocks.get("モックのページの形式") == f"`{impl.MOCK_KIND}`")
    check("登録するファイルが違う", mocks.get("登録するファイル") == f"`{SHIM.as_posix()}`"
          and write.MKDOCS_HOOK == write.PLUGIN_ROOT / SHIM)
    check("登録する入口が違う", mocks.get("登録する入口") == f"spec-loop の `{write.INIT_MKDOCS}` の `--hook`")
    order = table_rows(text, ["順", "探す先"])
    check("見つけ方の環境変数が違う", bool(order) and f"`{shim.ENV}`" in order[0][1] and shim.ENV == "SCREEN_SPEC_PLUGIN")
    check("見つけ方の記録が違う", len(order) > 1 and f"`{shim.INSTALLED}`" in order[1][1] and f"`{shim.NAME}@<マーケットプレイス>`" in order[1][1])
    check("薄いフックの印が check-screens.py と違う", shim.MARK == impl.checks.TABLE_MARK)
    check("薄いフックの表の場所が check-screens.py と違う", tuple(shim.TABLES) == tuple(impl.checks.TABLES))
    check("薄いフックの本体の場所が違う", (PLUGIN / shim.IMPL).resolve() == (PLUGIN / IMPL).resolve())
    check("薄いフックの名前が plugin.json と違う",
          json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["name"] == shim.NAME)
    check("薄いフックの仕様書の形が check-screens.py の置き場所と違う", shim.SCREENS.pattern == r"v[1-9][0-9]*/" + impl.checks.SCREENS_DIR + r"[^/]+\.md")
    check("references/prose.md が mkdocs.md を指していない", "`references/mkdocs.md`" in (PLUGIN / "references" / "prose.md").read_text(encoding="utf-8"))
    check("init のスキルが登録の手順を持たない",
          "write-screens.py mkdocs <docs>" in (PLUGIN / "skills" / "init" / "SKILL.md").read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="screen-spec-pages-") as tmp:
        work = Path(tmp)
        for index, (name, case) in enumerate(CASES.items()):
            try:
                ok = case(PLUGIN, work / f"case{index}")
            except Exception as e:  # noqa: BLE001
                ok = False
                name += f"（例外: {type(e).__name__}: {e}）"
            check(f"試料が期待どおりでない: {name}", ok)
        for index, (name, target, before, after, killer) in enumerate(MUTATIONS):
            source = (PLUGIN / target).read_text(encoding="utf-8")
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = work / f"mut{index}" / "screen-spec"
            shutil.copytree(PLUGIN, mutated, ignore=shutil.ignore_patterns("__pycache__"))
            (mutated / target).write_text(source.replace(before, after), encoding="utf-8")
            try:
                survived = CASES[killer](mutated, work / f"mutwork{index}")
            except Exception:  # noqa: BLE001 — 壊した本体が例外で落ちるのも「期待どおりでない」
                survived = False
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not survived)
    check_reference()
    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件・原本との突き合わせ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
