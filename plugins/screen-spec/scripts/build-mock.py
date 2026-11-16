#!/usr/bin/env python3
"""画面・項目・遷移の表から、UI モック（HTML 1 枚）を生成する。

usage: python3 build-mock.py <docs ディレクトリ> [--upto <n>] [--spec-loop <spec-loop のプラグインの根>]

**決まりの正は `references/mock.md` である**（このプラグインの中にある）。下の定数（出力の置き場所・描き方のファイルの置き場所と名前・
版の中で止めるディレクトリの名前・出す列・説明の欄に出す画面の列）はその写しで、
**写しがずれていないかは、このプラグインを置いているリポジトリの `scripts/test-build-mock.py` が突き合わせる。**

- **表の置き場所・列・種別・散文の節と、spec-loop の見つけ方・版の範囲・重ね方は `check-screens.py` を読み込む**（写さない）。
  重ね方は spec-loop の `merge-versions.py`、内部の層の Q&A の番号の形は spec-loop の `check-qa-csv.py`（どちらも `check-screens.py` 経由）。
- v1〜v<n>（`--upto` を省くと作業中の版 = 番号が最大の版）を重ねた表から、`<docs の親>/build/mock/v<n>/index.html` を書く。
- 出力は HTML 1 枚。表（許可した列だけ）を JSON にして埋め込み、描き方の JS も埋め込む。外のファイル・CDN を読まない。
- **描き方の差し替え**: `<docs の親>/screen-spec/renderers/<画面ID>.js`（素の JS。関数の本体として `ctx` を受ける）を埋め込む。
  **どれかの版のディレクトリの下に `renderers` という名前のディレクトリが在れば、何も書かずに止める**（版の中に置くとサインオフで比べる範囲に入る）。
- **何で作ったかを書き込む**: 版・表の出どころ（`docs` の git のコミットとそれを指すタグ。未コミットの変更の有無）・生成器の版（screen-spec の
  `plugin.json`）・描き方のファイルのコミット。時刻は書かない（同じ入力から同じバイト）。
- **共有の層だけを出す**: 許可した列のほかは埋め込まず、どのセルからも内部の層の Q&A の番号（`D-`）を外す。
- **表の検査の結果に依らず作る**（違反・未決定のある表でも作る。検査は `check-screens.py` を先に回す——#1095 の確認の Issue で決めた値）。
- 標準ライブラリだけを使う。

終了コード:

- 0: 書いた
- 1: 決まりに反する——重ね合わせが spec-loop の決まりに反する・3 つの表が揃っていない・見出し行が決まりと違う・描き方のファイルが版の中に在る。書かない
- 2: 判定していない——引数の誤り・`docs` が無い・`--upto` の版が無い・読めない・書けない・想定外の例外
- 4: 検査の前に止めた——spec-loop が見つからない・spec-loop の版が読めない・対応の範囲の外（`check-screens.py` と同じ）

**守ること**:

- 埋め込む画面・項目・遷移は重ねた全体の行だけ（モックにだけある画面・ボタンを作らない）
- 外を指す読み込み（`<script src>`・`<link>`・`<img>`・`url(`）を書かない
- 版・表の出どころ・生成器の版・描き方のファイルのコミットを HTML に書く（見える文字と `<meta>`）
- 描き方のファイルが版の中に在れば 1 で止めて書かない（`--upto` より後の版でも）
- 許可した列のほかを埋め込まない。どのセルからも `D-` の番号を外す
- 書くのは出力の 1 ファイルだけ（正本・spec-loop・screen-spec を書かない。`__pycache__` も、正本の git の index も書かない——`--no-optional-locks`）
- 埋め込む JSON と描き方の JS が `</script` で HTML を閉じない。描き方のファイルは 1 つずつ別の `<script>` に置く（構文の誤りがほかを巻き込まない）
- 表の遷移は、きっかけの項目の種類（ボタン・一覧・表示・入力・一覧の列）に依らずモックの上で押せる。タブの中のタブは道筋のタブを選ぶ

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **表の検査**（辿れない画面・遷移の無いボタン・Q&A の根拠） | `check-screens.py` が見る。生成器は検査の結果に依らず作る（遷移の無いボタンは灰色にして、押すと「遷移が表に無い」と出す） |
| **`renderers` のほかの名前で版の中に置いた JS** | 置き場所の名前で見る。版の中のどのファイルが描き方かは名前のほかに決める手段が無い |
| **描き方のファイルの中身**（表に無い名前を書いた・外を読む） | 素の JS で、案件の開発者が書く。表に無い遷移を呼べばモックが「遷移が表に無い」と出すところまで |
| **Chrome のほかのブラウザでの見え方** | 手元で確かめたのはヘッドレスの Chrome だけ（`scripts/test-build-mock.py --browser`） |
| **前の出力**（止めたときに `build/mock/v<n>/index.html` を消さない） | 止めたことは終了コードと出力で分かる |
"""

from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # 読み込むスクリプトの `__pycache__` を書かない（`-I` では環境変数が効かない）
PLUGIN_ROOT = HERE.parent

# ---- `references/mock.md` の写し
OUT_DIR = "build/mock"  # リポジトリの直下（`docs` の親）
OUT_NAME = "index.html"
RENDERERS = "screen-spec/renderers"  # リポジトリの直下（版の外）
RENDERER_SUFFIX = ".js"
FORBIDDEN_DIR = "renderers"  # 版のディレクトリの下に在れば止める
# 埋め込む列（共有の層の列）。ここに無い列（profile の列のうち開発者が決めるもの——パスなど）は埋め込まない
SHOWN = {
    "screens": ["画面ID", "画面名", "種別", "親画面", "主たる利用者", "ステータス", "参考資料", "目的と背景", "できること",
                "機能", "帳票", "仕様書", "根拠"],
    "items": ["番号", "画面ID", "まとまり", "並び順", "項目名", "種類", "中身", "例", "必須", "入力チェック", "エラーメッセージ",
              "並び替え", "絞り込み", "根拠"],
    "transitions": ["番号", "遷移元", "きっかけ", "操作", "条件", "遷移先", "結果", "根拠"],
}

LIST = "一覧"  # 項目の種類のうち、行の並ぶ表（`references/tables.md` の「項目の種類」）

GIT_LOCATION = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


screens_check = _load("screen_spec_check_screens", HERE / "check-screens.py")


class Refused(Exception):
    """決まりに反する（1）。"""


# ---- 共有の層だけにする

class Sharer:
    def __init__(self, qa_module) -> None:
        shape = re.sub(r"\(\?P<[^>]+>", "(?:", qa_module.INTERNAL_NUMBER.pattern)
        self.internal = re.compile(rf"(?<![A-Za-z0-9-]){shape}(?![0-9])")

    def clean(self, value: str) -> str:
        if not self.internal.search(value):
            return value
        text = self.internal.sub("", value)
        text = re.sub(r"[（(][\s、,]*[)）]", "", text)  # 番号だけを囲んでいた括弧
        text = re.sub(rf"(?:\s*{screens_check.SEPARATOR}\s*)+", screens_check.SEPARATOR, text)
        return text.strip().strip(screens_check.SEPARATOR).strip()


# ---- git（何で作ったか）

def git(cwd: Path, *args: str) -> str | None:
    env = {k: v for k, v in os.environ.items() if k not in GIT_LOCATION}
    try:
        proc = subprocess.run(["git", "--no-optional-locks", "-C", str(cwd), *args], capture_output=True, env=env, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip()


def source_of_tables(docs: Path) -> str:
    if git(docs, "rev-parse", "--is-inside-work-tree") != "true":
        return "git の外（コミットを決められない）"
    head = git(docs, "rev-parse", "HEAD")
    if not head:
        return "コミットが無い（git のリポジトリだがコミットを決められない）"
    tags = [t for t in (git(docs, "tag", "--points-at", "HEAD") or "").splitlines() if t]
    dirty = git(docs, "status", "--porcelain", "--untracked-files=all", "--", ".")
    out = f"コミット {head}"
    if tags:
        out += f"（タグ: {', '.join(sorted(tags))}）"
    if dirty is None:
        out += "（未コミットの変更を確かめられない）"
    elif dirty:
        out += "（docs に未コミットの変更あり）"
    return out


def source_of_renderers(directory: Path, files: list[Path]) -> str:
    if not files:
        return "差し替え無し"
    if git(directory, "rev-parse", "--is-inside-work-tree") != "true":
        return "git の外（コミットを決められない）"
    last = git(directory, "log", "-1", "--format=%H", "--", ".")
    dirty = git(directory, "status", "--porcelain", "--untracked-files=all", "--", ".")
    out = f"コミット {last}" if last else "コミットが無い"
    if dirty is None:
        out += "（未コミットの変更を確かめられない）"
    elif dirty:
        out += "（未コミットの変更あり）"
    return out


def generator_version() -> str:
    try:
        data = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "screen-spec（版が読めない）"
    return f"{data.get('name', 'screen-spec')} {data.get('version', '（版が読めない）')}"


# ---- 組み立て

def forbidden_renderers(versions) -> list[str]:
    found = []
    for _, root in versions:
        for current, dirs, _ in os.walk(root):
            for name in dirs:
                if name == FORBIDDEN_DIR:
                    found.append(Path(current, name).as_posix())
    return sorted(found)


def document_links(versions, upto: int, screens: dict, out_dir: Path, merged_files, link=None) -> dict[str, str]:
    """画面ID → 仕様書へのリンク。`link`（仕様書の Markdown のパス → リンク）を渡せばそれで作る（MkDocs のサイトに置くとき。#1098）。
    渡さなければ、出力の場所からの相対のパス。"""
    links = {}
    for key, row in screens.items():
        document = (row.get("仕様書") or "").strip()
        if not document or "/" in document or "\\" in document or not document.endswith(".md"):
            continue
        if screens_check.SCREENS_DIR + document not in merged_files:
            continue  # 重ねた全体に無い（removed.csv で消した）仕様書は指さない
        for _, root in reversed(versions[:upto]):
            path = root / screens_check.SCREENS_DIR / document
            if path.is_file():
                links[key] = link(path) if link else Path(os.path.relpath(path.resolve(), out_dir.resolve())).as_posix()
                break
    return links


def read_renderers(directory: Path, screens: dict) -> tuple[dict[str, str], list[Path], list[str]]:
    if not directory.is_dir():
        return {}, [], []
    embedded: dict[str, str] = {}
    used: list[Path] = []
    warnings: list[str] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if not path.name.endswith(RENDERER_SUFFIX):
            warnings.append(f"{path}: 描き方のファイル（<画面ID>{RENDERER_SUFFIX}）でないので読まない")
            continue
        key = path.name[:-len(RENDERER_SUFFIX)]
        if key not in screens:
            warnings.append(f"{path}: 画面 {key} が表に無いので埋め込まない")
            continue
        try:
            embedded[key] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise screens_check.Unreadable(f"{path}: 読めない（{e}）") from None
        used.append(path)
    return embedded, used, warnings


def script_safe(text: str) -> str:
    """`<script>` の中に置いても HTML を閉じない形（JS としての意味は変えない）。"""
    return re.sub(r"<(/script|!--)", lambda m: "<\\" + m.group(1), text, flags=re.IGNORECASE)


def json_for_script(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=False).replace("<", "\\u003c")


def build(docs: Path, upto: int | None, spec_loop: Path, spec_loop_version: str, link=None) -> tuple[Path, str, list[str]]:
    """(出力のディレクトリ, HTML, 警告)。書かない（書くのは `main`。MkDocs のフック（`mkdocs-pages.py`）も読み込んで使う）。
    `link` は仕様書へのリンクの作り方（`document_links`）。"""
    checker = screens_check.Checker(spec_loop, docs, upto)
    problems, versions, whole = checker.merged()
    if problems:
        raise Refused("版の重ね合わせが spec-loop の決まりに反する:\n" + "\n".join(f"  {p}" for p in problems))
    number = upto or len(versions)
    forbidden = forbidden_renderers(versions)
    if forbidden:
        raise Refused("描き方のファイルを版の中に置いている（版の外の " + RENDERERS + "/ に置く——references/mock.md）:\n"
                      + "\n".join(f"  {p}" for p in forbidden))
    missing = [p for p in screens_check.TABLES if p not in whole.headers]
    if missing:
        raise Refused("画面の表が揃っていない（3 つの表を置く）: " + "、".join(missing))
    for path in screens_check.TABLES:
        if whole.headers[path] != screens_check.COLUMNS[path]:
            raise Refused(f"{path}: 見出し行が決まり（{','.join(screens_check.COLUMNS[path])}）と違う: {','.join(whole.headers[path])}")

    sharer = Sharer(checker.qa)
    names = {screens_check.SCREENS: "screens", screens_check.ITEMS: "items", screens_check.TRANSITIONS: "transitions"}
    data: dict[str, object] = {}
    for path, name in names.items():
        data[name] = [{column: sharer.clean(row.get(column, "")) for column in SHOWN[name] if column in row}
                      for row in whole.tables[path].values()]

    repo = docs.resolve().parent
    out_dir = repo / OUT_DIR / f"v{number}"
    screens = {row["画面ID"]: row for row in whole.tables[screens_check.SCREENS].values()}
    renderer_dir = repo / RENDERERS
    renderers, used, warnings = read_renderers(renderer_dir, screens)
    provenance = {
        "版": f"v{number}",
        "表の出どころ": source_of_tables(docs),
        "生成器": generator_version(),
        "描き方のファイル": source_of_renderers(renderer_dir, used),
        "spec-loop": spec_loop_version,
    }
    data["provenance"] = provenance
    data["renderers"] = sorted(renderers)
    data["documents"] = document_links(versions, number, screens, out_dir, whole.files, link)
    data["proseSections"] = [name for name, tabled in screens_check.SECTIONS if not tabled]
    data["entryKind"] = screens_check.ENTRY_KIND
    data["childKinds"] = list(screens_check.CHILD_KINDS)
    data["tabKind"] = screens_check.REACHED_WITH_PARENT[0]  # 親の画面の中で切り替える種別。ほかの親を持つ種別（dialog）は親の上に重ねる
    data["separator"] = screens_check.SEPARATOR
    data["kinds"] = {"button": screens_check.BUTTON, "input": screens_check.INPUT, "listColumn": screens_check.LIST_COLUMN,
                     "list": LIST}
    return out_dir, render_html(number, data, renderers), warnings


# ---- HTML

STYLE = """
:root { color-scheme: light; --line: #c8ccd2; --muted: #5b6370; --accent: #1f5fbf; --bg: #f5f6f8; --off: #9aa0a8; }
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif; background: var(--bg); color: #1d2228; }
header.bar { padding: 8px 16px; background: #1d2228; color: #fff; font-size: 13px; display: flex; gap: 16px; flex-wrap: wrap; align-items: center; }
header.bar select { font: inherit; }
#app { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 16px; padding: 16px; }
@media (max-width: 900px) { #app { grid-template-columns: 1fr; } }
#stage { position: relative; background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 16px; min-height: 320px; }
#explain { background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 12px 16px; font-size: 13px; }
#explain h2 { font-size: 14px; margin: 12px 0 4px; }
#explain dl { margin: 0; display: grid; grid-template-columns: 7em 1fr; gap: 2px 8px; }
#explain dt { color: var(--muted); }
#explain dd { margin: 0; white-space: pre-wrap; }
#message { min-height: 1.5em; margin: 0 16px; color: #a3261b; font-weight: bold; }
.screen-head { display: flex; align-items: baseline; gap: 8px; border-bottom: 1px solid var(--line); margin-bottom: 12px; }
.screen-head h1 { font-size: 18px; margin: 0 0 8px; }
.screen-head .meta { color: var(--muted); font-size: 12px; }
fieldset { border: 1px solid var(--line); border-radius: 4px; margin: 0 0 12px; padding: 8px 12px; }
legend { color: var(--muted); font-size: 12px; }
.field { display: grid; grid-template-columns: 10em 1fr; gap: 8px; align-items: center; margin: 4px 0; }
.field .label { color: var(--muted); }
.required::after { content: " *"; color: #a3261b; }
button.mock-button { font: inherit; padding: 4px 12px; margin: 4px 8px 4px 0; border: 1px solid var(--accent); background: #fff; color: var(--accent); border-radius: 4px; cursor: pointer; }
button.mock-button.no-transition { border-color: var(--off); color: var(--off); background: #eceef1; cursor: not-allowed; }
table.mock-list { border-collapse: collapse; width: 100%; margin: 4px 0; }
table.mock-list th, table.mock-list td { border: 1px solid var(--line); padding: 4px 8px; text-align: left; }
table.mock-list tr.clickable { cursor: pointer; }
table.mock-list tr.clickable:hover { background: #eef3fb; }
.clickable-item { cursor: pointer; color: var(--accent); text-decoration: underline; }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--line); margin: 12px 0 8px; }
.tabs button { font: inherit; border: 1px solid var(--line); border-bottom: none; background: #eceef1; padding: 4px 12px; border-radius: 4px 4px 0 0; cursor: pointer; }
.tabs button[aria-selected="true"] { background: #fff; font-weight: bold; }
.overlay { position: absolute; inset: 0; background: rgba(29, 34, 40, 0.35); display: flex; align-items: center; justify-content: center; border-radius: 6px; }
.overlay .dialog { background: #fff; border-radius: 6px; padding: 16px; min-width: 60%; max-width: 90%; box-shadow: 0 4px 24px rgba(0,0,0,.25); }
.chooser { border: 1px solid var(--accent); border-radius: 4px; padding: 8px; margin: 8px 0; background: #f4f8fe; }
.chooser button { display: block; margin: 4px 0; font: inherit; cursor: pointer; }
footer#provenance { padding: 8px 16px 24px; color: var(--muted); font-size: 12px; }
footer#provenance dl { display: grid; grid-template-columns: 9em 1fr; gap: 2px 8px; margin: 0; }
footer#provenance dd { margin: 0; word-break: break-all; }
.renderer-error { color: #a3261b; }
"""

APP = r"""
(function () {
  "use strict";
  var DATA = JSON.parse(document.getElementById("screen-spec-data").textContent);
  var RENDERERS = window.screenSpecRenderers || {};
  var K = DATA.kinds;
  var screens = {}, order = [];
  DATA.screens.forEach(function (s) { screens[s["画面ID"]] = s; order.push(s["画面ID"]); });
  var itemsOf = {}, items = {};
  DATA.items.forEach(function (it, at) {
    it.__at = at;
    items[it["番号"]] = it;
    (itemsOf[it["画面ID"]] = itemsOf[it["画面ID"]] || []).push(it);
  });
  Object.keys(itemsOf).forEach(function (k) {
    itemsOf[k].sort(function (a, b) {
      var x = parseInt(a["並び順"], 10), y = parseInt(b["並び順"], 10);
      x = isNaN(x) ? Infinity : x; y = isNaN(y) ? Infinity : y;
      return x !== y ? (x < y ? -1 : 1) : a.__at - b.__at;
    });
  });
  var transitions = {}, byTrigger = {};
  DATA.transitions.forEach(function (t) {
    transitions[t["番号"]] = t;
    (byTrigger[t["きっかけ"]] = byTrigger[t["きっかけ"]] || []).push(t);
  });
  var values = {};    // 項目の値（モックの中だけで覚える）
  var history = [];   // 通った遷移
  var selectedTab = {};
  var current = null;
  var stage = document.getElementById("stage");
  var explain = document.getElementById("explain");
  var message = document.getElementById("message");
  var picker = document.getElementById("screen-picker");

  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "class") node.className = attrs[k]; else node.setAttribute(k, attrs[k]);
    });
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }
  function say(text) { message.textContent = text; }
  function nameOf(id) { return screens[id] ? screens[id]["画面名"] : id; }

  function follow(number) {
    var t = transitions[number];
    if (!t) { say("遷移が表に無い: " + number); return false; }
    if (!screens[t["遷移先"]]) { say("遷移 " + number + " の行き先 " + t["遷移先"] + " が画面の表に無い"); return false; }
    history.push(t);
    open(t["遷移先"]);
    return true;
  }

  function showTransitions(list) {
    clearExplain();
    var box = el("section");
    box.appendChild(el("h2", null, "ボタンの遷移"));
    list.forEach(function (t) {
      var dl = el("dl");
      [["番号", t["番号"]], ["行き先", t["遷移先"] + " " + nameOf(t["遷移先"])], ["操作", t["操作"]], ["条件", t["条件"]],
       ["結果", t["結果"]], ["根拠", t["根拠"]]].forEach(function (p) {
        dl.appendChild(el("dt", null, p[0])); dl.appendChild(el("dd", null, p[1] || "—"));
      });
      box.appendChild(dl);
    });
    explain.appendChild(box);
    drawHistory();
  }

  function trigger(item, node, attribute) {
    var list = byTrigger[item["番号"]] || [];
    node.setAttribute(attribute || "data-item", item["番号"]);
    node.addEventListener("mouseenter", function () { if (list.length) showTransitions(list); });
    node.addEventListener("focus", function () { if (list.length) showTransitions(list); });
    node.addEventListener("mouseleave", function () { drawExplain(current); });
    node.addEventListener("click", function (event) {
      event.preventDefault();
      if (!list.length) { say("遷移が表に無い: " + item["項目名"] + "（" + item["番号"] + "）を きっかけ にする遷移"); return; }
      if (list.length === 1) { follow(list[0]["番号"]); return; }
      var chooser = el("div", {"class": "chooser", "data-role": "chooser"});
      chooser.appendChild(el("div", null, item["項目名"] + " の遷移（条件で分かれる）"));
      list.forEach(function (t) {
        var b = el("button", {"type": "button", "data-transition": t["番号"]},
          t["番号"] + ": " + (t["条件"] || "条件なし") + " → " + nameOf(t["遷移先"]));
        b.addEventListener("click", function () { follow(t["番号"]); });
        chooser.appendChild(b);
      });
      var old = stage.querySelector("[data-role=chooser]");
      if (old) old.remove();
      var anchor = node.closest("table") || node;
      anchor.parentNode.insertBefore(chooser, anchor.nextSibling);
    });
    return node;
  }

  function button(item) {
    var list = byTrigger[item["番号"]] || [];
    var b = el("button", {"type": "button", "class": "mock-button" + (list.length ? "" : " no-transition"),
                          "data-role": "button", "aria-disabled": list.length ? "false" : "true"}, item["項目名"]);
    return trigger(item, b);
  }

  function field(item) {
    var row = el("div", {"class": "field", "data-field": item["番号"]});
    var label = el("span", {"class": "label" + (item["必須"] === "はい" ? " required" : ""), "data-role": "item-name"}, item["項目名"]);
    row.appendChild(label);
    if (item["種類"] === K.input) {
      var input = el("input", {"type": "text", "data-item": item["番号"]});
      input.value = values[item["番号"]] !== undefined ? values[item["番号"]] : item["例"];
      input.addEventListener("input", function () { values[item["番号"]] = input.value; });
      row.appendChild(input);
      if (byTrigger[item["番号"]]) {  // 入力の項目を きっかけ にする遷移——入力欄は入力に使い、隣の印で遷移する
        var go = el("button", {"type": "button", "class": "mock-button follow-input"}, "→ " + item["項目名"]);
        row.appendChild(trigger(item, go, "data-trigger"));
      }
    } else {
      var shown = el("span", {"data-item": item["番号"]},
                     item["例"] || item["中身"] || (byTrigger[item["番号"]] ? item["項目名"] : ""));  // 押せる項目は空にしない
      if (byTrigger[item["番号"]]) { shown.className = "clickable-item"; trigger(item, shown); }
      row.appendChild(shown);
    }
    return row;
  }

  function listTable(item, columns) {
    var wrap = el("div", {"data-list": item["番号"]});
    wrap.appendChild(el("div", {"class": "label", "data-role": "item-name"}, item["項目名"]));
    var filters = columns.filter(function (c) { return c["絞り込み"] === "はい"; });
    filters.forEach(function (c) {
      var f = el("div", {"class": "field"});
      f.appendChild(el("span", {"class": "label"}, c["項目名"] + "（絞り込み）"));
      f.appendChild(el("input", {"type": "text", "data-filter": c["番号"]}));
      wrap.appendChild(f);
    });
    var table = el("table", {"class": "mock-list"});
    var head = el("tr");
    columns.forEach(function (c) {
      var th = el("th", {"data-item": c["番号"], "data-role": "item-name"}, c["項目名"] + (c["並び替え"] === "はい" ? " ⇅" : ""));
      if (byTrigger[c["番号"]]) { th.className = "clickable-item"; trigger(c, th); }
      head.appendChild(th);
    });
    table.appendChild(head);
    var row = el("tr");
    columns.forEach(function (c) { row.appendChild(el("td", null, c["例"] || "")); });
    if (!columns.length) row.appendChild(el("td", null, item["項目名"]));  // 列の無い一覧も押せる行を持つ
    if (byTrigger[item["番号"]]) { row.className = "clickable"; trigger(item, row); }
    else row.setAttribute("data-item", item["番号"]);
    table.appendChild(row);
    wrap.appendChild(table);
    return wrap;
  }

  function drawItems(id, container) {
    var list = itemsOf[id] || [];
    var lists = {};
    list.forEach(function (it) { if (it["種類"] === K.list) lists[it["項目名"]] = it; });
    var used = {};
    var groups = [], byGroup = {};
    list.forEach(function (it) {
      if (it["種類"] === K.listColumn && lists[it["まとまり"]]) return;  // 一覧の列は一覧の中に描く
      var g = it["まとまり"] || "";
      if (!byGroup[g]) { byGroup[g] = []; groups.push(g); }
      byGroup[g].push(it);
    });
    groups.forEach(function (g) {
      var box = el("fieldset", {"data-group": g});
      box.appendChild(el("legend", null, g));
      byGroup[g].forEach(function (it) {
        if (it["種類"] === K.button) box.appendChild(button(it));
        else if (it["種類"] === K.list) {
          var columns = list.filter(function (c) { return c["種類"] === K.listColumn && c["まとまり"] === it["項目名"]; });
          box.appendChild(listTable(it, columns));
        } else box.appendChild(field(it));
      });
      container.appendChild(box);
    });
  }

  function context(id, container) {
    return {
      screen: screens[id],
      items: (itemsOf[id] || []).slice(),
      root: container,
      button: function (number) {
        var it = items[number];
        if (!it || it["画面ID"] !== id) return el("span", {"class": "renderer-error"}, "項目が表に無い: " + number);
        if (it["種類"] !== K.button) return el("span", {"class": "renderer-error"}, "ボタンでない項目: " + number);
        return button(it);
      },
      item: function (number) {
        var it = items[number];
        if (!it || it["画面ID"] !== id) return el("span", {"class": "renderer-error"}, "項目が表に無い: " + number);
        return it["種類"] === K.button ? button(it) : field(it);
      },
      value: function (number) { var it = items[number]; return values[number] !== undefined ? values[number] : (it ? it["例"] : undefined); },
      follow: follow
    };
  }

  function drawBody(id, container) {
    var custom = RENDERERS[id];
    if (!custom && DATA.renderers.indexOf(id) >= 0) {
      container.appendChild(el("p", {"class": "renderer-error"}, "描き方のファイル " + id + ".js を読み込めない（構文の誤りなど）——表の既定の描き方で描く"));
    }
    if (custom) {
      try { custom(context(id, container)); return; }
      catch (e) {
        container.appendChild(el("p", {"class": "renderer-error"}, "描き方のファイル " + id + ".js が失敗した: " + e + "（表の既定の描き方で描く）"));
      }
    }
    drawItems(id, container);
  }

  function drawScreen(id, container, path, drawn) {
    drawn = drawn || {};
    drawn[id] = true;  // 親画面が巡っている（検査の違反）とき、描いた画面をタブとして描き直さない
    var s = screens[id];
    var head = el("div", {"class": "screen-head"});
    head.appendChild(el("h1", {"data-role": "screen-name", "data-screen": id}, s["画面名"]));
    head.appendChild(el("span", {"class": "meta"}, id + " ・ " + s["種別"]));
    container.appendChild(head);
    drawBody(id, container);
    var tabs = order.filter(function (k) { return screens[k]["種別"] === DATA.tabKind && screens[k]["親画面"] === id && !drawn[k]; });
    if (tabs.length) {
      var inPath = tabs.filter(function (k) { return path.indexOf(k) >= 0; })[0];
      var chosen = inPath ? inPath : (selectedTab[id] && tabs.indexOf(selectedTab[id]) >= 0 ? selectedTab[id] : tabs[0]);
      selectedTab[id] = chosen;
      var strip = el("div", {"class": "tabs", "role": "tablist"});
      tabs.forEach(function (k) {
        var b = el("button", {"type": "button", "role": "tab", "data-tab": k, "aria-selected": k === chosen ? "true" : "false"}, screens[k]["画面名"]);
        b.addEventListener("click", function () { selectedTab[id] = k; open(k); });
        strip.appendChild(b);
      });
      container.appendChild(strip);
      var panel = el("div", {"role": "tabpanel", "data-tab-panel": chosen});
      drawScreen(chosen, panel, path, drawn);
      container.appendChild(panel);
    }
  }

  function chain(id) {  // 根から id までの画面の並び（dialog・tab の親を遡る）
    var out = [id], seen = {};
    var s = screens[id];
    while (s && DATA.childKinds.indexOf(s["種別"]) >= 0 && screens[s["親画面"]] && !seen[s["画面ID"]]) {
      seen[s["画面ID"]] = true;
      out.unshift(s["親画面"]);
      s = screens[s["親画面"]];
    }
    return out;
  }

  function render(id) {
    stage.textContent = "";
    current = id;
    document.getElementById("app").setAttribute("data-current", id);
    var path = chain(id);
    var base = path[0];
    // 根の画面と、その中のタブ（入れ子のタブは道筋のものを選ぶ）を描く。dialog は根から順に重ねる
    var holder = el("div", {"data-screen-root": base});
    drawScreen(base, holder, path);
    stage.appendChild(holder);
    var overlaid = {};
    overlaid[base] = true;  // dialog の親が巡っている（検査の違反）とき、根の画面を重ねて描き直さない
    path.slice(1).forEach(function (k) {
      if (screens[k]["種別"] === DATA.tabKind || overlaid[k]) return;
      overlaid[k] = true;
      var overlay = el("div", {"class": "overlay", "data-dialog": k});
      var box = el("div", {"class": "dialog", "role": "dialog"});
      drawScreen(k, box, path);
      overlay.appendChild(box);
      stage.appendChild(overlay);
    });
    if (picker) picker.value = id;
    drawExplain(id);
  }

  function clearExplain() { explain.textContent = ""; }

  function pairList(pairs) {
    var dl = el("dl");
    pairs.forEach(function (p) { dl.appendChild(el("dt", null, p[0])); dl.appendChild(el("dd", null, p[1] || "—")); });
    return dl;
  }

  function drawHistory() {
    var box = el("section", {"data-role": "history"});
    box.appendChild(el("h2", null, "通った遷移"));
    if (!history.length) box.appendChild(el("p", null, "まだ無い"));
    var ol = el("ol");
    history.forEach(function (t) {
      ol.appendChild(el("li", {"data-transition": t["番号"]}, t["番号"] + ": " + nameOf(t["遷移元"]) + " → " + nameOf(t["遷移先"])));
    });
    box.appendChild(ol);
    explain.appendChild(box);
  }

  function drawExplain(id) {
    clearExplain();
    var s = screens[id];
    if (!s) { drawHistory(); return; }
    explain.appendChild(el("h2", null, "画面"));
    explain.appendChild(pairList([["画面", id + " " + s["画面名"]], ["種別", s["種別"]], ["目的と背景", s["目的と背景"]],
      ["できること", s["できること"]], ["主たる利用者", s["主たる利用者"]], ["ステータス", s["ステータス"]], ["根拠", s["根拠"]]]));
    var list = itemsOf[id] || [];
    if (list.length) {
      explain.appendChild(el("h2", null, "項目"));
      list.forEach(function (it) {
        var pairs = [["項目", it["番号"] + " " + it["項目名"] + "（" + it["種類"] + "）"], ["中身", it["中身"]]];
        if (it["種類"] === K.input) pairs.push(["入力チェック", it["入力チェック"]], ["エラーメッセージ", it["エラーメッセージ"]]);
        pairs.push(["根拠", it["根拠"]]);
        explain.appendChild(pairList(pairs));
      });
    }
    var doc = DATA.documents[id];
    if (doc && DATA.proseSections.length) {
      explain.appendChild(el("h2", null, "仕様書の節（散文）"));
      var ul = el("ul");
      DATA.proseSections.forEach(function (name) {
        var li = el("li");
        li.appendChild(el("a", {"href": doc, "data-role": "prose-link"}, name));
        ul.appendChild(li);
      });
      explain.appendChild(ul);
    }
    drawHistory();
  }

  function open(id) {
    if (location.hash !== "#screen=" + encodeURIComponent(id)) location.hash = "#screen=" + encodeURIComponent(id);
    else { say(""); render(id); }
  }

  function fromHash() {
    var found = /^#screen=(.*)$/.exec(location.hash);
    var id = null;
    if (found) {
      try { id = decodeURIComponent(found[1]); } catch (e) { say("画面が表に無い: " + found[1]); return; }
    }
    if (id !== null && !screens[id]) { say("画面が表に無い: " + id); return; }
    say("");
    if (id === null) {
      id = order.filter(function (k) { return screens[k]["種別"] === DATA.entryKind; })[0] || order[0];
      if (!id) { stage.textContent = "画面の表に画面が無い"; drawHistory(); return; }
    }
    render(id);
  }

  if (picker) {
    order.forEach(function (k) { picker.appendChild(el("option", {"value": k}, k + " " + screens[k]["画面名"])); });
    picker.addEventListener("change", function () { open(picker.value); });
  }
  window.screenSpecMock = { follow: follow, open: open, history: history };
  window.addEventListener("hashchange", fromHash);
  fromHash();
})();
"""


def render_html(number: int, data: dict, renderers: dict[str, str]) -> str:
    provenance = data["provenance"]
    meta = "\n".join(
        f'<meta name="screen-spec-{key}" content="{html.escape(value, quote=True)}">'
        for key, value in (("version", provenance["版"]), ("tables", provenance["表の出どころ"]),
                           ("generator", provenance["生成器"]), ("renderers", provenance["描き方のファイル"])))
    footer = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in provenance.items())
    # 描き方のファイルは 1 つずつ別の <script> に置く——構文の誤りが、ほかのファイルを巻き込まない
    blocks = ["<script>window.screenSpecRenderers = {};</script>"]
    for key in sorted(renderers):
        blocks.append(f"<script>\nwindow.screenSpecRenderers[{json_for_script(key)}] = function (ctx) {{\n{script_safe(renderers[key])}\n}};\n</script>")
    renderer_script = "\n".join(blocks)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>画面モック v{number}</title>
{meta}
<style>{STYLE}</style>
</head>
<body>
<header class="bar"><span>画面モック（画面の表から生成した参考資料。受入基準ではない）</span><label>画面 <select id="screen-picker" aria-label="画面"></select></label></header>
<div id="message" role="status"></div>
<div id="app"><main id="stage"></main><aside id="explain" aria-label="説明"></aside></div>
<footer id="provenance"><dl>{footer}</dl></footer>
<script type="application/json" id="screen-spec-data">{json_for_script(data)}</script>
{renderer_script}
<script>{APP}</script>
</body>
</html>
"""


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
        print(f"{docs}: ディレクトリが無い——作っていない", file=sys.stderr)
        return 2
    try:
        spec_loop = screens_check.find_spec_loop(named, docs)
        shown = screens_check.check_version(spec_loop)
    except screens_check.Stop as e:
        print(f"止めた: {e}", file=sys.stderr)
        return 4
    try:
        out_dir, text, warnings = build(docs, upto, spec_loop, f"spec-loop {shown}")
    except screens_check.Stop as e:
        print(f"止めた: {e}", file=sys.stderr)
        return 4
    except Refused as e:
        print(f"作っていない: {e}", file=sys.stderr)
        return 1
    except screens_check.Unreadable as e:
        print(f"{e}——作っていない", file=sys.stderr)
        return 2
    for warning in warnings:
        print(f"警告: {warning}")
    target = out_dir / OUT_NAME
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    except OSError as e:
        print(f"{target}: 書けない（{e}）——作っていない", file=sys.stderr)
        return 2
    print(f"書いた: {target}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 — 想定外の例外を 0 や 1 にしない
        print(f"想定外の例外で作っていない: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
