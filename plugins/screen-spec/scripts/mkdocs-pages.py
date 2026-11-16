"""screen-spec の MkDocs のフックの本体（#1098）——正本に登録した薄いフック（`templates/mkdocs/screen_spec_pages.py`）が読み込んで渡す。

単独では走らせない（MkDocs のイベントの関数と、spec-loop のフックの口 `spec_loop_mocks` を持つモジュール）。

**決まりの正は `references/mkdocs.md` である**（このプラグインの中にある）。下の定数（節ごとの行・種類・列、サイトの中のモックの置き場所と名前）は
その写しで、**写しがずれていないかは、このプラグインを置いているリポジトリの `scripts/test-screen-spec-pages.py` が突き合わせる。**

- **表の置き場所・列・節の名前・表を出す印と、spec-loop の見つけ方・版の範囲・重ね方は `check-screens.py` を読み込む**（写さない。`build-mock.py` 経由）。
- **共有の層だけを出す**のは `build-mock.py` の許可の列（`SHOWN`）と `Sharer`（内部の層の番号 `D-` を外す）を読み込む。未決定の印は spec-loop の `find_markers`。
- **モックは `build-mock.py` の `build` で作る**（`--upto <n>` と同じもの）。仕様書へのリンクだけを、サイトの仕様書のページに向ける。
- 標準ライブラリだけを使う（`File` は MkDocs のもの——ビルドのときにだけ読み込む）。

**守ること**:

- 案件の雛形（`docs/v<k>/requirements/screens/templates/` の下）はサイトに出さない（`{{画面ID}}` を持ち、リンクが解決しない）
- 正本を書かない——書くのは `<docs の親>/build/mock/v<n>/index.html`（`build-mock.py` と同じ場所。commit しない）だけ。`mkdocs.yml` を書き換えない
- 表を出すのは `docs/v<k>/requirements/screens/` の直下の Markdown の、表で持つ節の印だけ（ほかのページ・コードブロックの中は変えない）
- 版 `v<k>` の仕様書には、後の版が同じ名前の仕様書を置くまでの版を重ねた行を出す（表だけを変えた版の行も出る）
- 出す列は `references/mkdocs.md` の表の列だけ（`build-mock.py` の許可の列の中）。どのセルからも `D-` の番号を外す
- 未決定の印を含むセルの頭に `⚠️ ` を付ける（見せるときだけ。正本には書かない）
- 当たる画面が無い・重ね合わせの違反・散文の節の印・作れなかったモックは、警告（`mkdocs` のロガー）とページの注意書きにする（黙って空にしない）
- サイトの同じ場所に正本のファイルが在れば、モックを置かない（警告する）

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **散文の `⚠️` の飾り** | 散文を書き換えると本文（コード・リンク）を壊しうる。飾るのはフックが描く表のセルだけ |
| **MkDocs の 1.6 のほかの版での `File` の作り方** | 確かめたのは 1.6 だけ（`File(src_uri, src_dir, dest_dir, use_directory_urls)`） |
| **表の検査**（辿れない画面・遷移の無いボタン） | `check-screens.py` が見る。フックは検査の結果に依らず出す（`build-mock.py` と同じ） |
"""

from __future__ import annotations

import html
import importlib.util
import logging
import posixpath
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True

log = logging.getLogger("mkdocs.hooks.screen_spec_pages")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mock = _load("screen_spec_build_mock_for_pages", HERE / "build-mock.py")
checks = mock.screens_check

# ---- `references/mkdocs.md` の写し
# 節 → (行, 種類, 列)。行は「画面」「項目」「遷移元」「遷移元（条件あり）」「遷移元・遷移先」
SECTION_TABLES = {
    "1. 基本情報": ("画面", (), ["画面ID", "画面名", "種別", "親画面", "主たる利用者", "ステータス", "参考資料", "機能", "帳票", "根拠"]),
    "2. 画面概要": ("画面", (), ["目的と背景", "できること"]),
    "3. レイアウト": ("項目", (), ["まとまり", "並び順", "番号", "項目名", "種類"]),
    "4. データ表示": ("項目", ("表示", "一覧", "一覧の列"), ["番号", "項目名", "種類", "中身", "例", "根拠"]),
    "5. 操作とアクション": ("遷移元", (), ["番号", "きっかけ", "操作", "条件", "遷移先", "結果", "根拠"]),
    "6. 入力とバリデーション": ("項目", ("入力",), ["番号", "項目名", "必須", "入力チェック", "エラーメッセージ", "例", "根拠"]),
    "8. 権限とデータの見える範囲": ("遷移元（条件あり）", (), ["番号", "きっかけ", "条件", "遷移先", "根拠"]),
    "12. 一覧・表の能力": ("項目", ("一覧", "一覧の列"), ["番号", "まとまり", "項目名", "種類", "並び替え", "絞り込み"]),
    "13. 画面遷移": ("遷移元・遷移先", (), ["番号", "遷移元", "きっかけ", "遷移先", "条件"]),
}
CALLERS = "呼び出し元"  # `1. 基本情報` に足す行
NO_ROWS = "この画面に当たる行は無い"
SITE_DIR = "mock"  # サイトの中の置き場所 `mock/v<n>/index.html`
MOCK_NAME = "画面モック（表から生成）"
MOCK_KIND = "HTML（screen-spec が生成）"
DECORATION = "⚠️ "

TEMPLATES = "templates/"  # 案件の雛形の置き場所（requirements/screens/ の下）。サイトに出さない
PAGE = re.compile(r"v([1-9][0-9]*)/" + re.escape(checks.SCREENS_DIR) + r"([^/]+\.md)")
TEMPLATE_FILES = re.compile(r"v[1-9][0-9]*/" + re.escape(checks.SCREENS_DIR + TEMPLATES) + r".*")
MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]{}#|<>])")

_mocks: dict[str, list[dict]] = {}
_merged: dict[tuple[str, int], tuple] = {}


class Problem(Exception):
    """表を出せない・モックを作れない（警告と注意書きにする）。"""


def notice(message: str) -> str:
    log.warning("screen-spec: %s", message)
    return f'!!! warning "表示できない"\n\n    {cell_text(message)}\n'


def cell_text(value: str) -> str:
    escaped = html.escape(value.replace("\r\n", "\n").replace("\r", "\n"), quote=False)
    return MARKDOWN_SPECIAL.sub(r"\\\1", escaped).replace("\n", "<br>")


def spec_loop_of(docs: Path) -> tuple[Path, str]:
    try:
        root = checks.find_spec_loop(None, docs)
        return root, f"spec-loop {checks.check_version(root)}"
    except checks.Stop as e:
        raise Problem(str(e)) from None


def merged(docs: Path, upto: int | None):
    """(版の一覧, 重ねた全体, Checker)。重ね合わせの違反・読めないときは Problem。ビルドの間は覚えておく。"""
    key = (str(docs.resolve()), upto or 0)
    if key not in _merged:
        spec_loop, _ = spec_loop_of(docs)
        try:
            checker = checks.Checker(spec_loop, docs, upto)
            problems, versions, whole = checker.merged()
        except (checks.Stop, checks.Unreadable) as e:
            raise Problem(str(e)) from None
        if problems:
            raise Problem("版の重ね合わせが spec-loop の決まりに反する: " + "; ".join(problems))
        _merged[key] = (versions, whole, checker)
    return _merged[key]


def has_tables(whole) -> bool:
    return any(path in whole.headers for path in checks.TABLES)


# ---- 表を節に出す

class Tables:
    def __init__(self, whole, checker) -> None:
        missing = [p for p in checks.TABLES if p not in whole.headers]
        if missing:
            raise Problem("画面の表が揃っていない（3 つの表を置く）: " + "、".join(missing))
        self.sharer = mock.Sharer(checker.qa)
        self.find_markers = checker.find_markers
        self.screens = list(whole.tables[checks.SCREENS].values())
        self.items = list(whole.tables[checks.ITEMS].values())
        self.transitions = list(whole.tables[checks.TRANSITIONS].values())

    def cell(self, value: str) -> str:
        shown = self.sharer.clean(value or "")
        text = cell_text(shown)
        return DECORATION + text if self.find_markers(shown) else text

    def screen_of(self, document: str) -> dict | None:
        found = [row for row in self.screens if (row.get("仕様書") or "").strip() == document]
        return found[0] if len(found) == 1 else None

    def rows(self, kind: str, kinds: tuple, screen_id: str) -> list[dict]:
        if kind == "項目":
            rows = [r for r in self.items if r.get("画面ID", "").strip() == screen_id and (not kinds or r.get("種類", "").strip() in kinds)]
            groups: list[str] = []
            for r in rows:
                if r.get("まとまり", "") not in groups:
                    groups.append(r.get("まとまり", ""))

            def order(r):
                value = r.get("並び順", "").strip()
                return (groups.index(r.get("まとまり", "")), 0 if value.isdigit() else 1, int(value) if value.isdigit() else 0)
            return sorted(rows, key=order)
        source = [r for r in self.transitions]
        if kind == "遷移元":
            return [r for r in source if r.get("遷移元", "").strip() == screen_id]
        if kind == "遷移元（条件あり）":
            return [r for r in source if r.get("遷移元", "").strip() == screen_id and r.get("条件", "").strip()]
        if kind == "遷移元・遷移先":
            return [r for r in source if screen_id in (r.get("遷移元", "").strip(), r.get("遷移先", "").strip())]
        raise ValueError(kind)

    def section(self, name: str, screen: dict) -> str:
        kind, kinds, columns = SECTION_TABLES[name]
        screen_id = screen.get("画面ID", "").strip()
        if kind == "画面":
            pairs = [(column, screen.get(column, "")) for column in columns]
            if name == "1. 基本情報":
                callers = [f"{r.get('遷移元', '').strip()}（{r.get('番号', '').strip()}）" for r in self.transitions
                           if r.get("遷移先", "").strip() == screen_id]
                pairs.append((CALLERS, checks.SEPARATOR.join(callers)))
            out = ["| 項目 | 内容 |", "| --- | --- |"] + [f"| {cell_text(k)} | {self.cell(v)} |" for k, v in pairs]
            return "\n".join(out) + "\n"
        rows = self.rows(kind, kinds, screen_id)
        if not rows:
            return f"{NO_ROWS}。\n"
        out = ["| " + " | ".join(cell_text(c) for c in columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
        out += ["| " + " | ".join(self.cell(row.get(c, "")) for c in columns) + " |" for row in rows]
        return "\n".join(out) + "\n"


def page_path(page) -> str:
    return getattr(page.file, "src_uri", page.file.src_path).replace("\\", "/")


def replace_marks(markdown: str, render) -> str:
    """表を出す印の行を `render(節の名前 or None)` で置き換える。コードブロックの中は変えない。"""
    out = []
    fence = None
    section = None
    for line in markdown.split("\n"):
        stripped = line.strip()
        opener = checks.FENCE.match(stripped)
        if fence is not None:
            if opener and stripped.startswith(fence) and stripped.strip(fence[0]) == "":
                fence = None
            out.append(line)
            continue
        if opener:
            fence = opener.group(1)
            out.append(line)
            continue
        heading = checks.HEADING.fullmatch(line)
        if heading:
            section = heading.group(2).strip() if len(heading.group(1)) == 2 else section
        if stripped == checks.TABLE_MARK:
            out.append(render(section))
            continue
        out.append(line)
    return "\n".join(out)


def last_version_of(docs: Path, version: int, document: str) -> int:
    """仕様書 `v<version>/…/<document>` が重ねた全体の仕様書である最後の版——後の版が同じ名前の仕様書を置くまで（版は差分だけを置くので、
    仕様書を写さずに表だけを変えた版の行も、このページに出す）。"""
    later = [n for n in raw_versions(docs) if n > version]
    for number in later:
        if (docs / f"v{number}" / checks.SCREENS_DIR / document).is_file():
            return number - 1
    return max(later) if later else version


def on_page_markdown(markdown: str, page, config, files):
    if checks.TABLE_MARK not in markdown:
        return markdown
    match = PAGE.fullmatch(page_path(page))
    if match is None:
        return markdown  # 仕様書でないページ（案件の雛形 templates/spec.md など）の印は変えない
    docs = Path(config["docs_dir"])
    version, document = int(match.group(1)), match.group(2)
    upto = last_version_of(docs, version, document)
    try:
        _, whole, checker = merged(docs, upto)
        tables = Tables(whole, checker)
        screen = tables.screen_of(document)
        if screen is None and upto != version:  # 後の版で消した画面——そのページの版で重ねたものを出す
            upto = version
            _, whole, checker = merged(docs, upto)
            tables = Tables(whole, checker)
            screen = tables.screen_of(document)
        if screen is None:
            raise Problem(f"v1〜v{upto} を重ねた画面の表に、仕様書が {document} の画面が 1 つに決まらない")
    except Problem as e:
        message = f"{page_path(page)}: 表を出せない（{e}）"
        log.warning("screen-spec: %s", message)
        return replace_marks(markdown, lambda _: f'!!! warning "表示できない"\n\n    {cell_text(message)}\n')

    def render(section: str | None) -> str:
        if section not in SECTION_TABLES:
            return notice(f"{page_path(page)}: 表を出す印が、表で持つ節の外にある（節: {section or 'なし'}。references/prose.md の「節」）")
        return tables.section(section, screen)

    return replace_marks(markdown, render)


# ---- 版ごとのモック

def page_url(rel: str, use_directory_urls: bool) -> str:
    """`docs` からの Markdown のパス → サイトの中の URL（MkDocs の決まり）。"""
    stem = rel[:-len(".md")]
    if not use_directory_urls:
        return stem + ".html"
    head, name = posixpath.split(stem)
    if name in ("index", "README"):
        return (head + "/") if head else "./"
    return stem + "/"


def site_link(docs: Path, number: int, use_directory_urls: bool):
    base = f"{SITE_DIR}/v{number}"

    def link(path: Path) -> str:
        url = page_url(path.resolve().relative_to(docs.resolve()).as_posix(), use_directory_urls)
        out = posixpath.relpath(url, base)
        return out + "/" if url.endswith("/") and not out.endswith("/") else out
    return link


def on_files(files, config):
    _merged.clear()
    for file in list(files):  # 案件の雛形（`{{画面ID}}` を持ち、リンクが解決しない）はページにしない
        if TEMPLATE_FILES.fullmatch(file.src_uri.replace("\\", "/")):
            files.remove(file)
    docs = Path(config["docs_dir"])
    rows: list[dict] = []
    _mocks[str(docs.resolve())] = rows
    if not any(has_raw_tables(docs, n) for n in raw_versions(docs)):
        return files  # 画面の表がどの版にも無い——作るものが無い
    try:
        spec_loop, shown = spec_loop_of(docs)
    except Problem as e:
        log.warning("screen-spec: 版ごとのモックを作らない（%s）", e)
        rows.extend({"version": n, "problem": f"画面モックを作れない（{e}）"} for n in raw_versions(docs) if has_raw_tables(docs, n))
        return files
    from mkdocs.structure.files import File  # ビルドのときにだけ読み込む

    use_directory_urls = bool(config.get("use_directory_urls", True))
    for number in raw_versions(docs):  # 版ごとに重ねる——後の版の誤りで前の版のモックを止めない
        try:
            _, whole, _ = merged(docs, number)
            if not has_tables(whole):
                continue
            out_dir, text, warnings = mock.build(docs, number, spec_loop, shown, link=site_link(docs, number, use_directory_urls))
        except (Problem, mock.Refused, checks.Stop, checks.Unreadable) as e:
            log.warning("screen-spec: v%d: 画面モックを作れない（%s）", number, e)
            rows.append({"version": number, "problem": f"画面モックを作れない（{e}）"})
            continue
        for warning in warnings:
            log.warning("screen-spec: v%d: %s", number, warning)
        src_uri = f"{SITE_DIR}/v{number}/{mock.OUT_NAME}"
        if files.get_file_from_path(src_uri) is not None:
            log.warning("screen-spec: v%d: サイトの %s に正本のファイルが在るので、画面モックを置かない", number, src_uri)
            rows.append({"version": number, "problem": f"サイトの {src_uri} に正本のファイルが在るので、画面モックを置かない"})
            continue
        target = out_dir / mock.OUT_NAME
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="\n")
        except OSError as e:
            log.warning("screen-spec: v%d: %s: 書けない（%s）", number, target, e)
            rows.append({"version": number, "problem": f"{target} を書けない（{e}）"})
            continue
        if not target.as_posix().endswith("/" + src_uri):  # build-mock.py の出力の場所とサイトの中の場所がずれた
            rows.append({"version": number, "problem": f"{target} をサイトの {src_uri} に置けない（置き場所の決まりがずれている）"})
            log.warning("screen-spec: v%d: %s をサイトの %s に置けない", number, target, src_uri)
            continue
        source_dir = target.parents[len(Path(src_uri).parts) - 1]
        files.append(File(src_uri, str(source_dir), config["site_dir"], use_directory_urls))
        rows.append({"version": number, "name": MOCK_NAME, "path": src_uri, "kind": MOCK_KIND})
    return files


def raw_versions(docs: Path) -> list[int]:
    found = []
    try:
        for entry in docs.iterdir():
            if re.fullmatch(r"v[1-9][0-9]*", entry.name) and entry.is_dir():
                found.append(int(entry.name[1:]))
    except OSError:
        return []
    return sorted(found)


def has_raw_tables(docs: Path, number: int) -> bool:
    return any((docs / f"v{number}" / path).is_file() for path in checks.TABLES)


def spec_loop_mocks(docs_dir) -> list[dict]:
    """spec-loop のフックの口（`mocks` の印に足す行）。`on_files` で作ったモックの行。"""
    return list(_mocks.get(str(Path(docs_dir).resolve()), []))
