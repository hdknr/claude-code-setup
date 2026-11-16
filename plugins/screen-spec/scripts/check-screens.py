#!/usr/bin/env python3
"""画面・項目・遷移の表と散文の仕様書を、spec-loop の重ね方で重ねた全体に当てて検査する。

usage: python3 check-screens.py <docs ディレクトリ> [--upto <n>] [--spec-loop <spec-loop のプラグインの根>]

**決まりの正は `references/tables.md`・`references/prose.md`・`references/spec-loop.md` である**（このプラグインの中にある）。
下の定数（表の置き場所・列・空でよい列・決まった値・入口の種別・散文の節・表を出す印・対応する spec-loop の版の範囲）はその写しで、
**写しがずれていないかは、このプラグインを置いているリポジトリの `scripts/test-check-screens.py` が突き合わせる。**

- **spec-loop の決まりを写さない**——版の重ね方は spec-loop の `merge-versions.py` の `merge`、Q&A の番号の形は `check-qa-csv.py`、
  未決定の印は `check-spec-exit.py` の `find_markers`、成果物の表の置き場所と番号の形は `check-design-csv.py` を読み込む。
- **検査の前に spec-loop を見つけ、版が対応の範囲（`SPEC_LOOP_MIN` 以上 `SPEC_LOOP_BELOW` 未満）に入るかを確かめる**——外なら何も検査せずに 4。
  見つけ方は `references/spec-loop.md` の「spec-loop の見つけ方」（`find_spec_loop`）。
- **ファイルを 1 つも書かない。Q&A の番号を振らない**——Q&A の番号を添えていない未決定の印は「起票の候補」として出すだけ。
- 標準ライブラリだけを使う。

終了コード:

- 0: 違反も未決定も無い（警告はあってもよい）。画面の表が 1 つも無いときも 0
- 1: 違反がある（未決定も併せて出す）。重ね合わせが spec-loop の決まりに反するときも 1
- 3: 違反は無いが、未決定の印か必須の欄の空がある
- 2: 判定していない——引数の誤り・`docs` が無い・読めない・想定外の例外
- 4: 検査の前に止めた——spec-loop が見つからない・spec-loop の版が読めない・対応の範囲の外

**守ること**:

- 表に無い画面を指す項目・遷移・親画面を違反にする（v1 の行も、後の版で置いた行も、重ねた全体で照らす）
- 入口（種別 `top`）から遷移で辿れない画面を違反にする（`tab` は親の画面が辿れれば辿れる）。入口が 1 つも無いのも違反。
  ただし未決定のセル（遷移の `遷移元`・`遷移先`・`きっかけ`、画面の `種別`・`親画面`）があって決められないものは警告にする（未決定は 3 のまま）
- それを `きっかけ` にする遷移の無いボタンを違反にする。`きっかけ` が遷移元の画面の項目でないのも違反
- `根拠`・印に添えた番号・散文の Q&A の番号が重ねた Q&A 表（共有と内部）に無ければ違反、回答はあるが未反映の行・`removed.csv` で消した行なら警告
- 画面の `機能`・`根拠` の機能の番号・`帳票`・遷移の `操作` が成果物の表に無ければ違反（表が無いときも）
- 表のセルと散文に残った未決定の印を「未決定」（3）にし、Q&A の番号の無いものを「起票の候補」に出す。`⚠️` だけのものは警告
- 仕様書が無い・最初の見出しに画面ID が無い・節が無い／順が違う／重なる・空の節・理由の無い `N/A`・表から指されない仕様書を違反にする
- 画面ID と項目・遷移の番号が表をまたいで重なるのを違反にする
- 見出し行・決まった値・種別や種類に合わない列の値を違反にし、必須の欄の空を 3 にする
- spec-loop が見つからない・版が範囲の外なら、検査の前に 4 で止める（名指しした spec-loop が spec-loop でなければ、ほかを探さずに止める）
- ファイルを書かない（Q&A の番号を振らない。spec-loop を読み込むときの `__pycache__` も書かない）

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **画面ID・番号の prefix**（`settings.csv` の `画面IDの接頭辞`） | 接頭辞は `add` が採番に使う設定で、手で置いた画面ID を止めない（`references/tables.md` の「案件ごとの設定」） |
| **セルの中身の意味**（目的が業務に合うか・入力チェックが足りるか） | 判断であって、一意に決まらない |
| **印を使わずに書いた未決定**（「あとで決める」） | 言い回しは列挙しきれない。spec-loop の `check-spec-exit.py` と同じ限界 |
| **成果物の表そのものの形** | spec-loop の `check-design-csv.py` が見る。ここは指す先の `id`・`操作` が在るかだけ |
| **`common.md` の節** | 案件で節を足し、書いていない節は空のままでよい（`references/prose.md` の「共通仕様」）。Q&A の番号と未決定の印だけを見る |
| **ワイヤーフレーム（drawio）と画面遷移図** | 図の鮮度は spec-loop の `render-diagrams.py --check` |
| **本物のプラグインのキャッシュの形が変わったとき**（`installed_plugins.json` の形） | 1 つの実測（`plugins` の下に `<名前>@<マーケットプレイス>` → 入れた先の一覧）に合わせて読む。読めなければ見つからないとして 4 |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import sys
import unicodedata
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
# spec-loop のスクリプトを読み込むときに `__pycache__` を書かない（このスクリプトはファイルを 1 つも書かない。`-I` では環境変数が効かない）
sys.dont_write_bytecode = True
PLUGIN_ROOT = HERE.parent

# ---- `references/spec-loop.md` の写し
SPEC_LOOP_NAME = "spec-loop"
SPEC_LOOP_MIN = (0, 93, 0)  # この版を含む
SPEC_LOOP_BELOW = (1, 0, 0)  # この版を含まない
SPEC_LOOP_ENV = "SCREEN_SPEC_SPEC_LOOP"
INSTALLED = "plugins/installed_plugins.json"

# ---- `references/tables.md` の写し
SCREENS_DIR = "requirements/screens/"
SCREENS = SCREENS_DIR + "data/screens.csv"
ITEMS = SCREENS_DIR + "data/screen-items.csv"
TRANSITIONS = SCREENS_DIR + "data/transitions.csv"
TABLES = (SCREENS, ITEMS, TRANSITIONS)
COLUMNS = {
    SCREENS: ["画面ID", "画面名", "種別", "親画面", "主たる利用者", "ステータス", "参考資料", "目的と背景", "できること",
              "機能", "帳票", "仕様書", "根拠"],
    ITEMS: ["番号", "画面ID", "まとまり", "並び順", "項目名", "種類", "中身", "例", "必須", "入力チェック", "エラーメッセージ",
            "並び替え", "絞り込み", "根拠"],
    TRANSITIONS: ["番号", "遷移元", "きっかけ", "操作", "条件", "遷移先", "結果", "根拠"],
}
# 空でよい列（種別・種類で決まる列は下の `check_*` が見る）
MAY_BE_EMPTY = {
    SCREENS: {"親画面", "参考資料", "機能", "帳票"},
    ITEMS: {"中身", "例", "必須", "入力チェック", "エラーメッセージ", "並び替え", "絞り込み"},
    TRANSITIONS: {"操作", "条件", "結果"},
}
SCREEN_KINDS = ("top", "list", "detail", "form", "flow", "preview", "dialog", "setting", "static", "tab")
ENTRY_KIND = "top"
CHILD_KINDS = ("tab", "dialog")  # 親画面を持つ種別
REACHED_WITH_PARENT = ("tab",)  # 親の画面が辿れれば辿れる種別
STATUSES = ("下書き", "記入中")
ITEM_KINDS = ("表示", "入力", "ボタン", "一覧", "一覧の列")
BUTTON = "ボタン"
INPUT = "入力"
LIST_COLUMN = "一覧の列"
YES_NO = ("はい", "いいえ")
SEPARATOR = "、"
WARNING_SIGNS = ("⚠",)  # `⚠️` は `⚠` に異体字の印が付いたもの

# ---- `references/prose.md` の写し
COMMON = "common.md"
SECTIONS = [
    ("1. 基本情報", True),
    ("2. 画面概要", True),
    ("3. レイアウト", True),
    ("4. データ表示", True),
    ("5. 操作とアクション", True),
    ("6. 入力とバリデーション", True),
    ("7. 状態", False),
    ("8. 権限とデータの見える範囲", True),
    ("9. 他システム連携", False),
    ("10. 同時編集", False),
    ("11. 表示ルール", False),
    ("12. 一覧・表の能力", True),
    ("13. 画面遷移", True),
    ("未決の論点", False),
]
TABLE_MARK = "<!-- screen-spec: 表 -->"

NOT_APPLICABLE = re.compile(r"N/A[\s。．.:：、\-－—–()（）\[\]「」]*", re.IGNORECASE)
HEADING_LINE = re.compile(r"^ {0,3}#{1,6}([ \t].*)?$", re.MULTILINE)
HEADING = re.compile(r" {0,3}(#{1,6})[ \t]+(.*?)[ \t#]*$")
LIST_MARK = re.compile(r"^[ \t]*(?:[-+*>]|[0-9]+[.)])[ \t]+", re.MULTILINE)  # 箇条書き・引用の印
DECORATION = re.compile(r"[*_`~]")  # 強調・コードの印
FENCE = re.compile(r"(`{3,}|~{3,})")
COMMENT = re.compile(r"<!--.*?-->", re.S)


class Stop(Exception):
    """検査の前に止める（4）。"""


class Unreadable(Exception):
    """判定していない（2）。"""


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_version(text: object) -> tuple[int, int, int] | None:
    if not isinstance(text, str):
        return None
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", text)
    return tuple(int(part) for part in match.groups()) if match else None


def manifest(root: Path) -> dict | None:
    try:
        data = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def is_spec_loop(root: Path) -> bool:
    data = manifest(root)
    return data is not None and data.get("name") == SPEC_LOOP_NAME


def installed_spec_loop(docs: Path) -> Path | None:
    """プラグインのキャッシュの形（`<config>/plugins/cache/<マーケットプレイス>/screen-spec/<版>/`）のとき、
    `installed_plugins.json` が名指しする同じマーケットプレイスの spec-loop を返す。形が違う・読めない・1 つに決まらなければ None。"""
    if PLUGIN_ROOT.parent.name != "screen-spec":
        return None
    market = PLUGIN_ROOT.parent.parent.name
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        data = json.loads((config / INSTALLED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    entries = data.get("plugins", {}).get(f"{SPEC_LOOP_NAME}@{market}") if isinstance(data, dict) and isinstance(data.get("plugins"), dict) else None
    if not isinstance(entries, list):
        return None
    here = docs.resolve()
    project = [e for e in entries if isinstance(e, dict) and e.get("scope") == "project" and isinstance(e.get("projectPath"), str)
               and (here == Path(e["projectPath"]) or Path(e["projectPath"]) in here.parents)]
    user = [e for e in entries if isinstance(e, dict) and e.get("scope") == "user"]
    chosen = project if project else user
    if len(chosen) != 1 or not isinstance(chosen[0].get("installPath"), str):
        return None
    return Path(chosen[0]["installPath"])


def find_spec_loop(named: str | None, docs: Path) -> Path:
    """`references/spec-loop.md` の「spec-loop の見つけ方」の順に探す。名指しされたものが spec-loop でなければ、ほかを探さずに止める。"""
    for source, value in (("--spec-loop", named), (SPEC_LOOP_ENV, os.environ.get(SPEC_LOOP_ENV) or None)):
        if value is not None:
            root = Path(value)
            if not is_spec_loop(root):
                raise Stop(f"{source} が指す {root} は spec-loop のプラグインの根でない（.claude-plugin/plugin.json の name が spec-loop でない・読めない）")
            return root
    sibling = PLUGIN_ROOT.parent / SPEC_LOOP_NAME
    if is_spec_loop(sibling):
        return sibling
    cached = installed_spec_loop(docs)
    if cached is not None and is_spec_loop(cached):
        return cached
    raise Stop(f"spec-loop が見つからない——--spec-loop <spec-loop のプラグインの根> か環境変数 {SPEC_LOOP_ENV} で渡す")


def check_version(root: Path) -> str:
    version = parse_version((manifest(root) or {}).get("version"))
    shown = ".".join(map(str, version)) if version else None
    if version is None:
        raise Stop(f"{root}: spec-loop の版が読めない（.claude-plugin/plugin.json の version）")
    if not (SPEC_LOOP_MIN <= version < SPEC_LOOP_BELOW):
        raise Stop(f"spec-loop の版 {shown}（{root}）は対応の範囲の外——"
                   f"{'.'.join(map(str, SPEC_LOOP_MIN))} 以上 {'.'.join(map(str, SPEC_LOOP_BELOW))} 未満（references/spec-loop.md）")
    return shown


class Report:
    def __init__(self) -> None:
        self.violations: list[str] = []
        self.undecided: list[str] = []
        self.empty: list[str] = []
        self.warnings: list[str] = []
        self.candidates: list[str] = []

    def lines(self) -> list[str]:
        out = [f"違反: {m}" for m in self.violations]
        out += [f"必須の欄が空: {m}" for m in self.empty]
        out += [f"未決定: {m}" for m in self.undecided]
        out += [f"警告: {m}" for m in self.warnings]
        out += [f"起票の候補: {m}" for m in self.candidates]
        out.append(f"違反 {len(self.violations)} 件・必須の欄が空 {len(self.empty)} 件・未決定 {len(self.undecided)} 件・"
                   f"警告 {len(self.warnings)} 件・起票の候補 {len(self.candidates)} 件")
        return out

    def code(self) -> int:
        if self.violations:
            return 1
        return 3 if self.undecided or self.empty else 0


class Checker:
    def __init__(self, spec_loop: Path, docs: Path, upto: int | None) -> None:
        scripts = spec_loop / "scripts"
        try:
            self.versions = _load("merge_versions", scripts / "merge-versions.py")
            self.design = _load("check_design_csv", scripts / "check-design-csv.py")
        except (OSError, SyntaxError, ImportError) as e:
            raise Stop(f"{scripts}: spec-loop のスクリプトを読み込めない（{e}）") from None
        self.qa = self.versions.qa
        self.find_markers = self.design.spec_exit.find_markers
        # 番号の形は spec-loop の `check-qa-csv.py` の `NUMBER`・`INTERNAL_NUMBER`（名前の付いたグループは 2 つを並べると重なるので外す）
        shapes = "|".join(re.sub(r"\(\?P<[^>]+>", "(?:", p.pattern) for p in (self.qa.NUMBER, self.qa.INTERNAL_NUMBER))
        self.qa_number = re.compile(rf"(?<![A-Za-z0-9-])(?:{shapes})(?![0-9])")
        self.feature_number = re.compile(rf"(?<![A-Za-z0-9-]){re.escape(self.design.ID_PREFIX[self.design.FEATURES])}[0-9]{{3,}}(?![0-9])")
        self.docs = docs
        self.upto = upto
        self.report = Report()
        self.undecided_cells: set[tuple[str, str, str]] = set()  # 印のあったセル（表のパス, 鍵, 列）

    # ---- 読む

    def merged(self):
        try:
            problems, versions, whole, _ = self.versions.merge(self.docs, self.upto)
        except self.versions.Unreadable as e:
            raise Unreadable(str(e)) from None
        return problems, versions, whole

    def text(self, whole, path: str) -> str | None:
        if path not in whole.files:
            return None
        try:
            return whole.files[path].decode("utf-8-sig")
        except UnicodeDecodeError:
            raise Unreadable(f"{path}: UTF-8 で読めない") from None

    def column(self, whole, path: str, name: str | None) -> set[str] | None:
        """成果物の表の 1 つの列の値。`name` が None なら 1 列目。表が無ければ None。"""
        text = self.text(whole, path)
        if text is None:
            return None
        try:
            rows = list(csv.reader(io.StringIO(text, newline="")))
        except csv.Error as e:
            raise Unreadable(f"{path}: CSV として読めない（{e}）") from None
        if not rows:
            return set()
        at = 0 if name is None else (rows[0].index(name) if name in rows[0] else None)
        if at is None:
            return set()
        return {row[at].strip() for row in rows[1:] if len(row) > at and row[at].strip()}

    def removed_qa(self, versions) -> set[str]:
        removed: set[str] = set()
        for _, root in versions[:self.upto]:
            path = root / self.versions.REMOVED
            if path.is_file():
                for _, kind, target in self.versions.read_removed(path, []):
                    if kind == self.versions.KIND_QA:
                        removed.add(target)
        return removed

    # ---- 1 つのセル・1 つの行

    def marked(self, where: str, value: str) -> bool:
        """未決定の印があれば数えて True。`⚠` だけなら警告する。"""
        hits = self.find_markers(value)
        if hits:
            for _, marker in hits:
                self.report.undecided.append(f"{where}: 未決定の印 {marker!r}")
            if not self.qa_number.search(value):
                self.report.candidates.append(f"{where}: {value.strip()}")
            return True
        if any(sign in value for sign in WARNING_SIGNS):
            self.report.warnings.append(f"{where}: ⚠️ だけで未決定の印が無い（未決定なら印と Q&A の番号を書く）")
        return False

    def references(self, where: str, value: str) -> None:
        for match in self.qa_number.finditer(value):
            number = match.group(0)
            row = self.all_qa.get(number)
            if row is None:
                if number in self.removed:
                    self.report.warnings.append(f"{where}: removed.csv で消した Q&A {number} を指す（反映を確かめる）")
                else:
                    self.report.violations.append(f"{where}: Q&A {number} が Q&A 表に無い")
            elif row.get("回答") != self.qa.NO_ANSWER:
                self.report.warnings.append(f"{where}: Q&A {number} は回答がある（反映を確かめる）")

    def cells(self, path: str, key: str, row: dict[str, str]) -> dict[str, str]:
        """印の無いセルの値（前後の空白を除く）。印のあるセルは値の決まりに当てないので入れない。空の必須の欄は数える。"""
        decided = {}
        for name in COLUMNS[path]:
            value = row[name]
            where = f"{path} {key} {name}"
            if self.marked(where, value):
                self.references(where, value)  # 印に添えた Q&A の番号も Q&A 表に在ること
                self.undecided_cells.add((path, key, name))
                continue
            decided[name] = value.strip()
            if not decided[name] and name not in MAY_BE_EMPTY[path]:
                self.report.empty.append(where)
        if "根拠" in decided:
            self.references(f"{path} {key} 根拠", decided["根拠"])
            for match in self.feature_number.finditer(decided["根拠"]):
                self.listed(f"{path} {key} 根拠", match.group(0), self.features, self.design.FEATURES, "機能")
        return decided

    def listed(self, where: str, value: str, known: set[str] | None, table: str, what: str) -> None:
        if known is None:
            self.report.violations.append(f"{where}: {what} {value} を指すが {table} が無い")
        elif value not in known:
            self.report.violations.append(f"{where}: {what} {value} が {table} に無い")

    def one_of(self, where: str, value: str | None, allowed: tuple[str, ...], what: str) -> bool:
        if value is None or value == "":
            return False
        if value not in allowed:
            self.report.violations.append(f"{where}: {what} {value!r} は決まった値（{'・'.join(allowed)}）でない")
            return False
        return True

    def must_be_empty(self, where: str, value: str | None, why: str) -> None:
        if value:
            self.report.violations.append(f"{where}: {why}には書かない（{value!r}）")

    # ---- 表

    def check(self) -> int:
        problems, versions, whole = self.merged()
        if problems:
            for problem in problems:
                self.report.violations.append(f"版の重ね合わせ: {problem}")
            return self.finish()
        placed = [path for path in TABLES if path in whole.headers]
        if not placed:
            print("画面の表が無い（requirements/screens/data/ に 3 つの表のどれも無い）——検査するものが無い")
            return 0
        for path in TABLES:
            if path not in whole.headers:
                self.report.violations.append(f"{path}: 表が無い（3 つの表は揃えて置く。行が無くても見出し行は置く）")
            elif whole.headers[path] != COLUMNS[path]:
                self.report.violations.append(f"{path}:1: 見出し行が決まり（{','.join(COLUMNS[path])}）と違う: {','.join(whole.headers[path])}")
        if self.report.violations:
            return self.finish()

        self.all_qa = {**whole.qa, **whole.internal}
        self.removed = self.removed_qa(versions)
        self.features = self.column(whole, self.design.FEATURES, "id")
        self.reports = self.column(whole, self.design.REPORTS, "id")
        self.roles = self.column(whole, self.design.ROLES, None)

        screens = {k: self.cells(SCREENS, k, row) for k, row in whole.tables[SCREENS].items()}
        items = {k: self.cells(ITEMS, k, row) for k, row in whole.tables[ITEMS].items()}
        transitions = {k: self.cells(TRANSITIONS, k, row) for k, row in whole.tables[TRANSITIONS].items()}

        for (a, keys_a), (b, keys_b) in ((("画面", screens), ("項目", items)), (("画面", screens), ("遷移", transitions)),
                                          (("項目", items), ("遷移", transitions))):
            for key in sorted(set(keys_a) & set(keys_b)):
                self.report.violations.append(f"{a}と{b}の番号 {key} が重なる（表をまたいでも重ねない）")

        self.check_screens(screens)
        self.check_items(screens, items)
        self.check_transitions(screens, items, transitions)
        self.check_reach(screens, transitions)
        self.check_prose(whole, screens)
        return self.finish()

    def check_screens(self, screens: dict[str, dict[str, str]]) -> None:
        documents: dict[str, str] = {}
        for key, row in screens.items():
            where = f"{SCREENS} {key}"
            kind = row.get("種別")
            self.one_of(f"{where} 種別", kind, SCREEN_KINDS, "種別")
            self.one_of(f"{where} ステータス", row.get("ステータス"), STATUSES, "ステータス")
            parent = row.get("親画面")
            if kind in CHILD_KINDS:
                if parent == "":
                    self.report.empty.append(f"{where} 親画面（種別 {kind} の画面は親画面を書く）")
                elif parent is not None and parent not in screens:
                    self.report.violations.append(f"{where} 親画面: {parent} が画面の表に無い")
                elif parent == key:
                    self.report.violations.append(f"{where} 親画面: 自分を親にしている")
            elif kind in SCREEN_KINDS:
                self.must_be_empty(f"{where} 親画面", parent, f"種別 {kind} の画面")
            elif parent and parent not in screens:
                self.report.violations.append(f"{where} 親画面: {parent} が画面の表に無い")
            for value in self.split(row.get("機能")):
                self.listed(f"{where} 機能", value, self.features, self.design.FEATURES, "機能")
            for value in self.split(row.get("帳票")):
                self.listed(f"{where} 帳票", value, self.reports, self.design.REPORTS, "帳票")
            document = row.get("仕様書")
            if document:
                if "/" in document or "\\" in document or not document.endswith(".md") or document == COMMON or document.startswith("."):
                    self.report.violations.append(f"{where} 仕様書: {document!r} は {SCREENS_DIR} の直下の <slug>.md でない")
                elif document in documents:
                    self.report.violations.append(f"{where} 仕様書: {document} を画面 {documents[document]} も指している（画面ごとに別のファイル）")
                else:
                    documents[document] = key

    def check_items(self, screens, items) -> None:
        for key, row in items.items():
            where = f"{ITEMS} {key}"
            screen = row.get("画面ID")
            if screen and screen not in screens:
                self.report.violations.append(f"{where} 画面ID: {screen} が画面の表に無い")
            order = row.get("並び順")
            if order and not re.fullmatch(r"[1-9][0-9]{0,8}", order):
                self.report.violations.append(f"{where} 並び順: {order!r} は正の整数でない")
            kind = row.get("種類")
            if not self.one_of(f"{where} 種類", kind, ITEM_KINDS, "種類"):
                continue
            if kind != BUTTON and row.get("中身") == "":
                self.report.empty.append(f"{where} 中身")
            if kind == INPUT:
                if row.get("必須") == "":
                    self.report.empty.append(f"{where} 必須（種類 {INPUT} の項目は書く）")
                self.one_of(f"{where} 必須", row.get("必須"), YES_NO, "必須")
            else:
                for name in ("必須", "入力チェック", "エラーメッセージ"):
                    self.must_be_empty(f"{where} {name}", row.get(name), f"種類 {kind} の項目")
            for name in ("並び替え", "絞り込み"):
                if kind == LIST_COLUMN:
                    if row.get(name) == "":
                        self.report.empty.append(f"{where} {name}（種類 {LIST_COLUMN} の項目は書く）")
                    self.one_of(f"{where} {name}", row.get(name), YES_NO, name)
                else:
                    self.must_be_empty(f"{where} {name}", row.get(name), f"種類 {kind} の項目")

    def check_transitions(self, screens, items, transitions) -> None:
        triggered: set[str] = set()
        for key, row in transitions.items():
            where = f"{TRANSITIONS} {key}"
            for name in ("遷移元", "遷移先"):
                value = row.get(name)
                if value and value not in screens:
                    self.report.violations.append(f"{where} {name}: {value} が画面の表に無い")
            trigger = row.get("きっかけ")
            if trigger:
                triggered.add(trigger)
                if trigger not in items:
                    self.report.violations.append(f"{where} きっかけ: {trigger} が項目の表に無い")
                elif row.get("遷移元") and items[trigger].get("画面ID") not in (None, row["遷移元"]):
                    self.report.violations.append(f"{where} きっかけ: 項目 {trigger} は遷移元 {row['遷移元']} の項目でない"
                                                  f"（{items[trigger]['画面ID']} の項目）")
            operation = row.get("操作")
            if operation:
                self.listed(f"{where} 操作", operation, self.roles, self.design.ROLES, "操作")
        # きっかけが未決定の遷移は、遷移元の画面（遷移元も未決定ならどの画面でも）のボタンを 1 つずつ指しうる。
        # 指しうる数より遷移の無いボタンが多ければ、どれかは確かに遷移が無い（違反）。指しうる数に収まれば決められない（警告）
        open_by_source: dict[str | None, int] = {}
        for key, row in transitions.items():
            if (TRANSITIONS, key, "きっかけ") in self.undecided_cells:
                open_by_source[row.get("遷移元")] = open_by_source.get(row.get("遷移元"), 0) + 1
        untriggered: dict[str | None, list[str]] = {}
        for key, row in items.items():
            if row.get("種類") == BUTTON and key not in triggered:
                untriggered.setdefault(row.get("画面ID"), []).append(key)
        for screen, keys in untriggered.items():
            room = sum(open_by_source.values()) if screen is None else open_by_source.get(screen, 0) + open_by_source.get(None, 0)
            for key in keys:
                message = f"{ITEMS} {key}: ボタン {items[key].get('項目名', '')!r} を きっかけ にする遷移が無い"
                if len(keys) <= room:
                    self.report.warnings.append(f"{message}かもしれない（きっかけが未決定の遷移があるので決められない）")
                elif room:
                    self.report.violations.append(f"{message}（きっかけが未決定の遷移は {room} つで、{len(keys)} 個のボタンの少なくとも "
                                                  f"{len(keys) - room} 個は遷移が無い）")
                else:
                    self.report.violations.append(message)

    def check_reach(self, screens, transitions) -> None:
        if not screens:
            return
        entries = [key for key, row in screens.items() if row.get("種別") == ENTRY_KIND]
        undecided = lambda table, key, name: (table, key, name) in self.undecided_cells  # noqa: E731
        if not entries:
            message = f"{SCREENS}: 入口の画面（種別 {ENTRY_KIND}）が無い"
            if any(undecided(SCREENS, key, "種別") for key in screens):
                self.report.warnings.append(f"{message}かもしれない（種別が未決定の画面があるので決められない）")
            else:
                self.report.violations.append(message)
                return
        edges: dict[str, list[str]] = {}
        for row in transitions.values():
            if row.get("遷移元") in screens and row.get("遷移先") in screens:
                edges.setdefault(row["遷移元"], []).append(row["遷移先"])
        children: dict[str, list[str]] = {}
        for key, row in screens.items():
            if row.get("種別") in REACHED_WITH_PARENT and row.get("親画面") in screens:
                children.setdefault(row["親画面"], []).append(key)

        def walk(starts) -> set[str]:
            seen = set(starts)
            queue = deque(starts)
            while queue:
                here = queue.popleft()
                for there in edges.get(here, []) + children.get(here, []):
                    if there not in seen:
                        seen.add(there)
                        queue.append(there)
            return seen

        reached = walk(entries)
        # 辿れるかもしれない画面: 種別が未決定（入口かもしれない）・親画面が未決定のタブ（か種別も未決定）・遷移元が未決定の遷移の遷移先から辿れるもの。
        # 遷移先が未決定の遷移は、遷移元が辿れる（かもしれない）か未決定なら、どの画面へも行きうる
        seeds = [key for key, row in screens.items()
                 if undecided(SCREENS, key, "種別")
                 or (undecided(SCREENS, key, "親画面") and row.get("種別") in REACHED_WITH_PARENT)]
        seeds += [row["遷移先"] for key, row in transitions.items() if undecided(TRANSITIONS, key, "遷移元") and row.get("遷移先") in screens]
        maybe = walk(set(seeds) | reached)
        anywhere = any(undecided(TRANSITIONS, key, "遷移先") and (row.get("遷移元") in maybe or undecided(TRANSITIONS, key, "遷移元"))
                       for key, row in transitions.items())
        for key in screens:
            if key not in reached:
                message = f"{SCREENS} {key}: 入口の画面から遷移で辿れない"
                if anywhere or key in maybe:
                    self.report.warnings.append(f"{message}かもしれない（未決定の遷移・種別・親画面があるので決められない）")
                else:
                    self.report.violations.append(message)

    @staticmethod
    def split(value: str | None) -> list[str]:
        return [part.strip() for part in (value or "").split(SEPARATOR) if part.strip()]

    # ---- 散文

    def check_prose(self, whole, screens) -> None:
        referenced = {}
        for key, row in screens.items():
            document = row.get("仕様書")
            if not document or "/" in document or "\\" in document or not document.endswith(".md") or document == COMMON:
                continue
            referenced[document] = key
            path = SCREENS_DIR + document
            text = self.text(whole, path)
            if text is None:
                self.report.violations.append(f"{SCREENS} {key} 仕様書: {path} が無い")
                continue
            self.check_document(path, text, key)
        for path in sorted(whole.files):
            if not path.startswith(SCREENS_DIR) or not path.endswith(".md"):
                continue
            name = path[len(SCREENS_DIR):]
            if "/" in name:
                continue
            if name == COMMON:
                self.scan_lines(path, self.text(whole, path) or "")
            elif name not in referenced:
                self.report.violations.append(f"{path}: どの画面の 仕様書 からも指されていない（表から指されない仕様書を残さない）")

    def scan_lines(self, path: str, text: str) -> None:
        for number, line in enumerate(text.splitlines(), start=1):
            where = f"{path}:{number}"
            self.marked(where, line)
            self.references(where, line)

    @staticmethod
    def without_comments(text: str) -> list[str]:
        """HTML のコメントを外した行（行の位置は保ち、表を出す印は残す）。コードブロックの中の `<!--` はコメントに数えない。"""
        lines = text.splitlines()
        fenced: dict[int, str] = {}
        fence = None
        for at, line in enumerate(lines):
            opened = FENCE.match(line.lstrip())
            if fence is not None or opened:
                fenced[at] = line
                lines[at] = ""
                if fence is None:
                    fence = opened.group(1)
                elif opened and opened.group(1)[0] == fence[0] and len(opened.group(1)) >= len(fence):
                    fence = None
        joined = COMMENT.sub(lambda m: m.group(0) if m.group(0) == TABLE_MARK else "\n" * m.group(0).count("\n"), "\n".join(lines))
        out = joined.split("\n")
        for at, line in fenced.items():
            out[at] = line
        return out

    def check_document(self, path: str, text: str, key: str) -> None:
        self.scan_lines(path, text)
        # HTML のコメントの中の見出しは見出しに数えない（表を出す印は残す）。行の位置は保つ
        lines = self.without_comments(text)
        headings: list[tuple[int, int, str]] = []  # (行の位置, 段, 見出しの文字)
        fence = None
        for at, line in enumerate(lines):
            opened = FENCE.match(line.lstrip())
            if fence is not None:
                if opened and opened.group(1)[0] == fence[0] and len(opened.group(1)) >= len(fence):
                    fence = None
                continue
            if opened:
                fence = opened.group(1)
                continue
            match = HEADING.match(line)
            if match:
                headings.append((at, len(match.group(1)), match.group(2).strip()))
        title = next((h for h in headings if h[1] == 1), None)
        if title is None or key not in title[2]:
            self.report.violations.append(f"{path}: 最初の # の見出しに画面ID {key} を書いていない")
        names = [name for name, _ in SECTIONS]
        found: dict[str, int] = {}
        for index, (at, level, heading) in enumerate(headings):
            if level != 2 or heading not in names:
                continue
            if heading in found:
                self.report.violations.append(f"{path}:{at + 1}: 節 ## {heading} が 2 つある")
                continue
            found[heading] = index
            end = next((h[0] for h in headings[index + 1:] if h[1] <= 2), len(lines))
            body = "\n".join(lines[at + 1:end])
            tabled = dict(SECTIONS)[heading]
            content = unicodedata.normalize("NFKC", HEADING_LINE.sub("", COMMENT.sub("", body))).strip()  # 小見出しだけの節は空
            if tabled and TABLE_MARK in body:
                continue
            if not content:
                self.report.violations.append(f"{path}:{at + 1}: 節 ## {heading} が空（書くことが無ければ N/A と理由を書く）")
            elif NOT_APPLICABLE.fullmatch(DECORATION.sub("", LIST_MARK.sub("", content)).strip()):
                self.report.violations.append(f"{path}:{at + 1}: 節 ## {heading} が N/A だけで理由が無い")
        for name in names:
            if name not in found:
                self.report.violations.append(f"{path}: 節 ## {name} が無い")
        order = [name for name in names if name in found]
        if [found[name] for name in order] != sorted(found[name] for name in order):
            self.report.violations.append(f"{path}: 節の順が決まり（references/prose.md）と違う")

    def finish(self) -> int:
        for line in self.report.lines():
            print(line)
        return self.report.code()


def main(argv: list[str]) -> int:
    args = list(argv)
    named = None
    upto = None
    try:
        while "--spec-loop" in args:
            at = args.index("--spec-loop")
            if at + 1 >= len(args) or named is not None:
                raise ValueError("--spec-loop には spec-loop のプラグインの根を 1 つ渡す")
            named = args[at + 1]
            del args[at:at + 2]
        while "--upto" in args:
            at = args.index("--upto")
            if at + 1 >= len(args) or upto is not None or not re.fullmatch(r"[1-9][0-9]*", args[at + 1]):
                raise ValueError("--upto には 1 以上の整数を 1 つ渡す")
            upto = int(args[at + 1])
            del args[at:at + 2]
        if len(args) != 1 or args[0].startswith("-"):
            raise ValueError(__doc__.splitlines()[2] if __doc__ else
                             f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）")
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    docs = Path(args[0])
    if not docs.is_dir():
        print(f"{docs}: ディレクトリが無い——判定していない", file=sys.stderr)
        return 2
    try:
        spec_loop = find_spec_loop(named, docs)
        shown = check_version(spec_loop)
        checker = Checker(spec_loop, docs, upto)
    except Stop as e:
        print(f"止めた: {e}", file=sys.stderr)
        return 4
    print(f"spec-loop {shown}（{spec_loop}）の決まりで検査する")
    try:
        return checker.check()
    except Unreadable as e:
        print(f"{e}——判定していない", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 — 想定外の例外を 0 や 1 にしない
        print(f"想定外の例外で判定していない: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
