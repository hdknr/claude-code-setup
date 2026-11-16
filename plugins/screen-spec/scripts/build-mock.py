#!/usr/bin/env python3
"""画面・項目・遷移の表から、UI モック（HTML 1 枚）を生成する。

usage: python3 build-mock.py <docs ディレクトリ> [--upto <n>] [--since <コミットかタグ>] [--spec-loop <spec-loop のプラグインの根>]

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
- **差分の印**（#1096）: v2 以降は前の版から（spec-loop の `diff-versions.py` の `compare` を読み込む——写さない）、`--since <コミットかタグ>` を渡すと
  その時点から（その時点の `docs` を一時ディレクトリに取り出して同じ版まで重ね、`compare_maps` で比べる）、変えた画面・項目・遷移に印と根拠の Q&A の番号を付け、
  消したものを一覧に並べる。
- **レビュー会の進め方・未回答・未反映**（#1096）: 共有の層の Q&A のうち `反映済み` でない行を並べて「質問 → 画面」の逆引きで飛ばし、
  未回答の質問に掛かる項目・遷移に「推奨案（X）で描いている」と出し、画面に掛かる行に回答の未反映が残っていれば警告する（モックは作る）。
- 標準ライブラリだけを使う。

終了コード:

- 0: 書いた
- 1: 決まりに反する——重ね合わせ（基準の時点の重ね合わせを含む）が spec-loop の決まりに反する・3 つの表が揃っていない・見出し行が決まりと違う・描き方のファイルが版の中に在る。書かない
- 2: 判定していない——引数の誤り・`docs` が無い・`--upto` の版が無い・`--since` を解決できない（git の外・その時点に `docs` が無い）・読めない・書けない・想定外の例外
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
- 差分の印は変わった画面・項目・遷移にだけ付ける（v1 には前の版からの印を付けない）。根拠は共有の層の番号だけ（消した行は消した理由の番号も足す）
- 基準の時点は一時ディレクトリに取り出し、終わったら消す（正本・git の index に書かない）。解決できなければ 2、その時点の重ね合わせが決まりに反すれば 1
- レビュー会の進め方は共有の層の `反映済み` でない行だけを Q&A 表の順に並べ、質問の画面（画面・その項目・その画面を遷移元にする遷移のセルに番号がある画面）へ飛ぶ
- 未回答の注記は共有の層の未回答の行を指す項目・遷移にだけ出す。画面に掛かる行（共有と内部）に回答の未反映が残っていれば標準出力に警告する（0 のまま）
- 埋め込む Q&A は共有の層の行の許可した列だけ（内部の層の行を埋め込まない）

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **表の検査**（辿れない画面・遷移の無いボタン・Q&A の根拠） | `check-screens.py` が見る。生成器は検査の結果に依らず作る（遷移の無いボタンは灰色にして、押すと「遷移が表に無い」と出す） |
| **`renderers` のほかの名前で版の中に置いた JS** | 置き場所の名前で見る。版の中のどのファイルが描き方かは名前のほかに決める手段が無い |
| **描き方のファイルの中身**（表に無い名前を書いた・外を読む） | 素の JS で、案件の開発者が書く。表に無い遷移を呼べばモックが「遷移が表に無い」と出すところまで |
| **Chrome のほかのブラウザでの見え方** | 手元で確かめたのはヘッドレスの Chrome だけ（`scripts/test-build-mock.py --browser`） |
| **前の出力**（止めたときに `build/mock/v<n>/index.html` を消さない） | 止めたことは終了コードと出力で分かる |
| **基準の時点からの差分で、画面を消して連鎖で消えた項目・遷移の理由** | 前の版からの差分は `diff-versions.py` が画面の行の理由を添えるが、基準の時点からの差分は `removed.csv` でその行を名指しした理由だけを添える（`compare` の連鎖の理由の付け方を写さないため） |
| **変えた根拠のうち、セルに書いていない番号** | 根拠は変わった行のセル（と消した理由）にある番号だけ。行を変えた理由の質問を `根拠` に書かなければ出ない |
| **`TMPDIR` が git の作業ツリーの中を指すとき** | 基準の時点を取り出した一時ディレクトリが別の git の作業ツリーの中にあると、spec-loop の重ね方がその index を読む。既定の一時ディレクトリでは起きない |
"""

from __future__ import annotations

import html
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
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

# 埋め込む Q&A の列（共有の層の行だけ。レビュー会の進め方・未回答の注記・未反映の印に使う）
QA_SHOWN = ["No", "質問", "選択肢", "推奨", "回答", "状態"]
# Q&A の行の分け方（`references/mock.md` の「未回答・未反映」）
UNANSWERED, UNREFLECTED, PROVISIONAL, REFLECTED = "未回答", "未反映", "暫定反映", "反映済み"

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
        text = re.sub(rf"([（(]){screens_check.SEPARATOR}|{screens_check.SEPARATOR}([)）])", r"\1\2", text)  # 括弧の中に余った区切り
        return text.strip().strip(screens_check.SEPARATOR).strip()


# ---- git（何で作ったか）

def git_bytes(cwd: Path, *args: str) -> bytes | None:
    """git の標準出力（失敗・走らせられなければ None）。任意のロックを取らない——正本の git の index を書き換えない。"""
    env = {k: v for k, v in os.environ.items() if k not in GIT_LOCATION}
    try:
        proc = subprocess.run(["git", "--no-optional-locks", "-C", str(cwd), *args], capture_output=True, env=env, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def git(cwd: Path, *args: str) -> str | None:
    out = git_bytes(cwd, *args)
    return None if out is None else out.decode("utf-8", "replace").strip()


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


def document_links(versions, upto: int, screens: dict, out_dir: Path, merged_files) -> dict[str, str]:
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
                links[key] = Path(os.path.relpath(path.resolve(), out_dir.resolve())).as_posix()
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


class Numbers:
    """セルの中の Q&A の番号（形は spec-loop の `check-qa-csv.py`。`check-screens.py` の `Checker` が作った正規表現を使う）。"""

    def __init__(self, checker) -> None:
        self.any = checker.qa_number  # 共有（`Q-`）と内部（`D-`）
        self.is_internal = checker.qa.is_internal_number

    def of(self, row: dict[str, str], shared_only: bool = False) -> list[str]:
        found: list[str] = []
        for value in row.values():
            for match in self.any.finditer(value or ""):
                number = match.group(0)
                if number not in found and not (shared_only and self.is_internal(number)):
                    found.append(number)
        return found


def load_diff(spec_loop: Path):
    """spec-loop の `diff-versions.py`（版の差分。写さない）。"""
    try:
        return screens_check._load("spec_loop_diff_versions", spec_loop / "scripts" / "diff-versions.py")
    except (OSError, SyntaxError, ImportError) as e:
        raise screens_check.Stop(f"{spec_loop / 'scripts'}: spec-loop のスクリプトを読み込めない（{e}）") from None


def baseline(docs: Path, ref: str, number: int, versions_module):
    """(基準の時点の名前, その時点の docs を重ねた全体)。`docs` の git で `ref` をコミットに解決し、その時点の `docs` を一時ディレクトリに
    取り出して（終わったら消す）、同じ版（その時点に無ければその時点の最大の版）まで重ねる。正本も git の index も書かない。"""
    if git(docs, "rev-parse", "--is-inside-work-tree") != "true":
        raise screens_check.Unreadable(f"--since {ref}: docs が git の作業ツリーの外——基準の時点を決められない")
    commit = git(docs, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if not commit:
        raise screens_check.Unreadable(f"--since {ref}: コミットに解決できない")
    prefix = (git(docs, "rev-parse", "--show-prefix") or "").rstrip("/")
    top = git(docs, "rev-parse", "--show-toplevel")
    # 根から呼ぶ——下のディレクトリから呼ぶと、git archive はその場所をもう一度前に付けて何も出さない
    archive = git_bytes(Path(top), "archive", "--format=tar", f"{commit}:{prefix}" if prefix else commit) if top else None
    if archive is None:
        raise screens_check.Unreadable(f"--since {ref}: その時点（コミット {commit}）の docs（{prefix or '.'}）を取り出せない——その時点に無いか、git が失敗した")
    with tempfile.TemporaryDirectory(prefix="screen-spec-since-") as tmp:
        target = Path(tmp) / "docs"
        target.mkdir()
        try:
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(target, filter="data")
                else:  # pragma: no cover — filter の無い古い Python
                    tar.extractall(target)
        except (tarfile.TarError, OSError) as e:
            raise screens_check.Unreadable(f"--since {ref}: その時点の docs を取り出せない（{e}）") from None
        try:
            try:
                problems, _, whole, _ = versions_module.merge(target, number)
            except versions_module.OutOfRange:
                problems, _, whole, _ = versions_module.merge(target, None)  # その時点にはまだ v<n> が無い
        except versions_module.Unreadable as e:
            raise screens_check.Unreadable(f"--since {ref}: {e}") from None
    if problems:
        raise Refused(f"基準の時点（{ref}）の版の重ね合わせが spec-loop の決まりに反する:\n" + "\n".join(f"  {p}" for p in problems))
    return f"{ref}（コミット {commit}）", whole


def shown_row(name: str, row: dict[str, str], sharer: Sharer) -> dict[str, str]:
    return {column: sharer.clean(row.get(column, "")) for column in SHOWN[name] if column in row}


def diff_entry(kind: str, label: str, changes: dict, row_tables: dict, names: dict, numbers: Numbers, sharer: Sharer,
               removed_status: str) -> dict:
    """差分 1 つ分の印（画面・項目・遷移の鍵 → 追加／変更／削除）・根拠（共有の層の Q&A の番号）・消したもの。"""
    entry: dict[str, object] = {"kind": kind, "label": label, "marks": {}, "basis": {}, "removed": []}
    for path, (row_kind, _, _) in row_tables.items():
        name = names[path]
        marks: dict[str, str] = {}
        basis: dict[str, list[str]] = {}
        for change in changes.get(row_kind, []):
            row = change.after if change.after is not None else change.before
            marks[change.key] = change.status
            basis[change.key] = numbers.of(row, shared_only=True)
            if change.status == removed_status:  # 消した行は、消した理由（removed.csv）に書いた番号も根拠に足す
                basis[change.key] += [n for n in numbers.of({"理由": change.reason or ""}, shared_only=True) if n not in basis[change.key]]
                entry["removed"].append({"table": name, "kind": row_kind, "key": change.key, "row": shown_row(name, row, sharer),
                                         "reason": sharer.clean(change.reason or ""), "basis": basis[change.key]})
        entry["marks"][name] = marks
        entry["basis"][name] = basis
    return entry


def qa_class(row: dict[str, str], qa) -> str:
    """Q&A の行の分け方（`references/mock.md` の「未回答・未反映」）。"""
    if row.get("回答", "").strip() in ("", qa.NO_ANSWER):
        return UNANSWERED
    state = row.get("状態", "").strip()
    if state == qa.DONE:
        return REFLECTED
    if qa.is_provisional(row):
        return PROVISIONAL
    return UNREFLECTED


def build(docs: Path, upto: int | None, spec_loop: Path, spec_loop_version: str, since: str | None = None) -> tuple[Path, str, list[str]]:
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
        data[name] = [shown_row(name, row, sharer) for row in whole.tables[path].values()]

    # ---- 差分の印（前の版から・基準の時点から）
    diff_versions = load_diff(spec_loop)
    row_tables = checker.versions.ROW_TABLES
    numbers = Numbers(checker)
    diffs = []
    if number > 1:
        try:
            diff_problems, diff = diff_versions.compare(docs, number)
        except diff_versions.merge_versions.Unreadable as e:
            raise screens_check.Unreadable(str(e)) from None
        if diff_problems:
            raise Refused("前の版との差分を作れない:\n" + "\n".join(f"  {p}" for p in diff_problems))
        diffs.append(diff_entry("version", f"前の版（v{number - 1}）から", diff.changes, row_tables, names, numbers, sharer,
                                diff_versions.REMOVED))
    if since is not None:
        label, before = baseline(docs, since, number, checker.versions)
        reasons = diff_versions.removal_reasons(versions[number - 1][1])
        changes = {}
        for path, (row_kind, _, _) in row_tables.items():
            changes[row_kind] = diff_versions.compare_maps(before.tables.get(path, {}), whole.tables[path])
            for change in changes[row_kind]:
                if change.status == diff_versions.REMOVED:
                    change.reason = reasons.get((row_kind, change.key), "")
        diffs.append(diff_entry("since", f"基準の時点 {label} から", changes, row_tables, names, numbers, sharer,
                                diff_versions.REMOVED))
    data["diffs"] = diffs

    # ---- Q&A（共有の層だけを埋め込む）・レビュー会の進め方・未回答の注記・未反映の警告
    qa = checker.qa
    screens_raw = whole.tables[screens_check.SCREENS]
    items_raw = whole.tables[screens_check.ITEMS]
    transitions_raw = whole.tables[screens_check.TRANSITIONS]
    screen_refs: dict[str, list[str]] = {}  # 画面 → その画面に掛かる Q&A の番号（共有と内部）
    for key, row in screens_raw.items():
        found = numbers.of(row)
        related = [r for r in items_raw.values() if r.get("画面ID") == key] + [r for r in transitions_raw.values() if r.get("遷移元") == key]
        for other in related:  # その画面の項目と、その画面を遷移元にする遷移
            found += [n for n in numbers.of(other) if n not in found]
        screen_refs[key] = found
    shared = {no: row for no, row in whole.qa.items() if not qa.is_internal_number(no)}
    all_qa = {**whole.qa, **whole.internal}
    agenda_numbers = [no for no, row in shared.items() if row.get("状態", "").strip() != qa.DONE]
    referenced = [n for found in screen_refs.values() for n in found if n in shared]
    embedded_qa = [no for no in shared if no in agenda_numbers or no in referenced]
    data["qa"] = [{column: sharer.clean(shared[no].get(column, "")) for column in QA_SHOWN} for no in embedded_qa]
    data["qaClass"] = {no: qa_class(shared[no], qa) for no in embedded_qa}
    data["agenda"] = [{"No": no, "screens": [key for key, found in screen_refs.items() if no in found]} for no in agenda_numbers]
    data["screenQa"] = {key: [n for n in found if n in shared] for key, found in screen_refs.items()}
    unanswered = {no for no in embedded_qa if data["qaClass"][no] == UNANSWERED}
    data["pending"] = {
        name: {key: [n for n in numbers.of(row, shared_only=True) if n in unanswered]
               for key, row in whole.tables[path].items() if any(n in unanswered for n in numbers.of(row, shared_only=True))}
        for path, name in ((screens_check.ITEMS, "items"), (screens_check.TRANSITIONS, "transitions"))}
    warnings: list[str] = []
    for key, found in screen_refs.items():
        for no in found:
            row = all_qa.get(no)
            if row is not None and qa_class(row, qa) == UNREFLECTED:
                warnings.append(f"画面 {key} に掛かる Q&A {no} は回答があるが未反映（回答を反映してからモックを作る——references/mock.md）")

    repo = docs.resolve().parent
    out_dir = repo / OUT_DIR / f"v{number}"
    screens = {row["画面ID"]: row for row in screens_raw.values()}
    renderer_dir = repo / RENDERERS
    renderers, used, renderer_warnings = read_renderers(renderer_dir, screens)
    warnings = renderer_warnings + warnings
    provenance = {
        "版": f"v{number}",
        "表の出どころ": source_of_tables(docs),
        "生成器": generator_version(),
        "描き方のファイル": source_of_renderers(renderer_dir, used),
        "spec-loop": spec_loop_version,
    }
    data["provenance"] = provenance
    data["renderers"] = sorted(renderers)
    data["documents"] = document_links(versions, number, screens, out_dir, whole.files)
    data["proseSections"] = [name for name, tabled in screens_check.SECTIONS if not tabled]
    data["entryKind"] = screens_check.ENTRY_KIND
    data["childKinds"] = list(screens_check.CHILD_KINDS)
    data["tabKind"] = screens_check.REACHED_WITH_PARENT[0]  # 親の画面の中で切り替える種別。ほかの親を持つ種別（dialog）は親の上に重ねる
    data["separator"] = screens_check.SEPARATOR
    data["kinds"] = {"button": screens_check.BUTTON, "input": screens_check.INPUT, "listColumn": screens_check.LIST_COLUMN,
                     "list": LIST}
    data["qaWords"] = {"noRecommendation": qa.NO_RECOMMENDATION, "optionSeparator": qa.OPTION_SEPARATOR,
                       "unanswered": UNANSWERED, "unreflected": UNREFLECTED, "removed": diff_versions.REMOVED}
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
.diff-mark { display: inline-block; font-size: 11px; padding: 0 6px; margin: 0 4px; border-radius: 8px; background: #fff3cd; color: #6b4e00; border: 1px solid #e0c060; }
.diff-mark[data-diff="追加"] { background: #e3f4e6; color: #1f5b2c; border-color: #8cc79a; }
.diff-mark[data-diff="削除"] { background: #fbe5e3; color: #7a1f17; border-color: #e0a19a; }
.pending-note { display: inline-block; font-size: 11px; padding: 0 6px; margin: 0 4px; border-radius: 4px; background: #eef3fb; color: #1f3f7a; border: 1px dashed #7d9bd1; }
.item-notes { margin: 0 0 4px; }
.unreflected { color: #a3261b; }
section.panel { margin: 0 16px 12px; background: #fff; border: 1px solid var(--line); border-radius: 6px; padding: 4px 12px; font-size: 13px; }
section.panel summary { cursor: pointer; font-weight: bold; padding: 4px 0; }
section.panel ol, section.panel ul { margin: 4px 0 8px; padding-left: 1.5em; }
section.panel li { margin: 4px 0; }
button.agenda-question, button.removed-entry, button.goto { font: inherit; border: none; background: none; color: var(--accent); text-decoration: underline; cursor: pointer; padding: 0; text-align: left; }
.options { color: var(--muted); }
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
  var W = DATA.qaWords;
  var qa = {};
  DATA.qa.forEach(function (q) { qa[q["No"]] = q; });
  var agendaList = document.getElementById("agenda-list");
  var removedList = document.getElementById("removed-list");
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

  // ---- 差分の印（前の版から・基準の時点から）と未回答の注記
  function diffMarks(table, key) {
    var out = [];
    DATA.diffs.forEach(function (d) {
      var status = d.marks[table] && d.marks[table][key];
      if (status) out.push({diff: d, status: status, basis: (d.basis[table] && d.basis[table][key]) || []});
    });
    return out;
  }
  function markText(m) { return m.diff.label + " " + m.status + (m.basis.length ? "（根拠: " + m.basis.join(DATA.separator) + "）" : ""); }
  function markNodes(table, key, prefix) {
    return diffMarks(table, key).map(function (m) {
      return el("span", {"class": "diff-mark", "data-diff": m.status, "data-diff-of": m.diff.kind, "data-diff-table": table,
                         "data-diff-key": key}, (prefix || "") + markText(m));
    });
  }
  function pendingText(no) {
    var q = qa[no] || {};
    var r = q["推奨"];
    return (r && r !== W.noRecommendation ? "推奨案（" + r + "）で描いている。" : "推奨なし（表の値で描いている）。") + no + " は未回答";
  }
  function pendingOf(table, key) { return (DATA.pending[table] && DATA.pending[table][key]) || []; }
  function pendingNodes(table, key, prefix) {
    return pendingOf(table, key).map(function (no) {
      return el("span", {"class": "pending-note", "data-pending-table": table, "data-pending": key, "data-question": no}, (prefix || "") + pendingText(no));
    });
  }
  function notes(item) {  // 項目の印・注記と、それを きっかけ にする遷移の印・注記
    var nodes = markNodes("items", item["番号"]).concat(pendingNodes("items", item["番号"]));
    (byTrigger[item["番号"]] || []).forEach(function (t) {
      var prefix = "遷移 " + t["番号"] + ": ";
      nodes = nodes.concat(markNodes("transitions", t["番号"], prefix), pendingNodes("transitions", t["番号"], prefix));
    });
    if (!nodes.length) return null;
    var box = el("div", {"class": "item-notes", "data-notes": item["番号"]});
    nodes.forEach(function (n) { box.appendChild(n); });
    return box;
  }

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
      var pairs = [["番号", t["番号"]], ["行き先", t["遷移先"] + " " + nameOf(t["遷移先"])], ["操作", t["操作"]], ["条件", t["条件"]],
       ["結果", t["結果"]], ["根拠", t["根拠"]]];
      diffMarks("transitions", t["番号"]).forEach(function (m) { pairs.push(["差分", markText(m)]); });
      pendingOf("transitions", t["番号"]).forEach(function (no) { pairs.push(["未回答", pendingText(no)]); });
      pairs.forEach(function (p) {
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
        var drawnItems = [it];
        if (it["種類"] === K.button) box.appendChild(button(it));
        else if (it["種類"] === K.list) {
          var columns = list.filter(function (c) { return c["種類"] === K.listColumn && c["まとまり"] === it["項目名"]; });
          box.appendChild(listTable(it, columns));
          drawnItems = drawnItems.concat(columns);
        } else box.appendChild(field(it));
        drawnItems.forEach(function (d) { var n = notes(d); if (n) box.appendChild(n); });
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
    markNodes("screens", id).forEach(function (n) { head.appendChild(n); });
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

  function drawChanges(id) {  // この画面・その項目・この画面を遷移元にする遷移の差分（消したものを含む）
    var lines = [];
    function add(table, key, what) {
      diffMarks(table, key).forEach(function (m) { lines.push({text: what + ": " + markText(m), status: m.status}); });
    }
    add("screens", id, "画面 " + id);
    (itemsOf[id] || []).forEach(function (it) { add("items", it["番号"], "項目 " + it["番号"] + " " + it["項目名"]); });
    DATA.transitions.forEach(function (t) { if (t["遷移元"] === id) add("transitions", t["番号"], "遷移 " + t["番号"]); });
    DATA.diffs.forEach(function (d) {
      d.removed.forEach(function (r) {
        var own = (r.table === "items" && r.row["画面ID"] === id) || (r.table === "transitions" && r.row["遷移元"] === id);
        if (own) lines.push({text: r.kind + " " + r.key + ": " + d.label + " " + W.removed + (r.reason ? "（理由: " + r.reason + "）" : "")
                                   + (r.basis.length ? "（根拠: " + r.basis.join(DATA.separator) + "）" : ""), status: W.removed});
      });
    });
    if (!lines.length) return;
    explain.appendChild(el("h2", null, "変わったもの"));
    var ul = el("ul", {"data-role": "changes"});
    lines.forEach(function (l) { ul.appendChild(el("li", {"data-diff": l.status}, l.text)); });
    explain.appendChild(ul);
  }

  function questionLine(no, extra) {
    var q = qa[no] || {};
    var li = el("li", {"data-question": no}, no + " " + (q["質問"] || "") + (extra ? "——" + extra : ""));
    if (q["選択肢"]) li.appendChild(el("div", {"class": "options"}, q["選択肢"] + "（推奨: " + (q["推奨"] || "—") + "）"));
    return li;
  }

  function drawQuestions(id) {  // その画面に掛かる未回答の Q&A と、回答はあるが未反映の Q&A（共有の層だけ）
    var numbers = DATA.screenQa[id] || [];
    var unanswered = numbers.filter(function (no) { return DATA.qaClass[no] === W.unanswered; });
    var unreflected = numbers.filter(function (no) { return DATA.qaClass[no] === W.unreflected; });
    if (unanswered.length) {
      explain.appendChild(el("h2", null, "この画面に掛かる未回答の Q&A"));
      var ul = el("ul", {"data-role": "unanswered"});
      unanswered.forEach(function (no) { ul.appendChild(questionLine(no, pendingText(no))); });
      explain.appendChild(ul);
    }
    if (unreflected.length) {
      explain.appendChild(el("h2", {"class": "unreflected"}, "回答はあるが未反映の Q&A（モックはまだ回答を反映していない）"));
      var ur = el("ul", {"data-role": "unreflected"});
      unreflected.forEach(function (no) { ur.appendChild(questionLine(no, "回答: " + ((qa[no] || {})["回答"] || ""))); });
      explain.appendChild(ur);
    }
  }

  function drawRemoved(d, r) {  // 消したものを説明の欄に出す（前の版・基準の時点の行。許可した列だけ）
    clearExplain();
    explain.appendChild(el("h2", null, "消したもの: " + r.kind + " " + r.key));
    var pairs = [["差分", d.label + " " + W.removed], ["理由", r.reason], ["根拠の Q&A", r.basis.join(DATA.separator)]];
    Object.keys(r.row).forEach(function (k) { pairs.push([k, r.row[k]]); });
    var dl = pairList(pairs);
    dl.setAttribute("data-role", "removed-detail");
    explain.appendChild(dl);
    drawHistory();
  }

  function drawExplain(id) {
    clearExplain();
    var s = screens[id];
    if (!s) { drawHistory(); return; }
    explain.appendChild(el("h2", null, "画面"));
    explain.appendChild(pairList([["画面", id + " " + s["画面名"]], ["種別", s["種別"]], ["目的と背景", s["目的と背景"]],
      ["できること", s["できること"]], ["主たる利用者", s["主たる利用者"]], ["ステータス", s["ステータス"]], ["根拠", s["根拠"]]]));
    drawChanges(id);
    drawQuestions(id);
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

  if (agendaList) {  // レビュー会の進め方: 今回の会の質問を順に並べ、選ぶとその画面に飛ぶ
    if (!DATA.agenda.length) agendaList.appendChild(el("li", null, "今回の会の質問は無い"));
    DATA.agenda.forEach(function (a) {
      var q = qa[a.No] || {};
      var li = el("li", {"data-agenda": a.No});
      var title = el("button", {"type": "button", "class": "agenda-question", "data-question": a.No}, a.No + " " + (q["質問"] || ""));
      title.addEventListener("click", function () {
        if (a.screens.length) open(a.screens[0]); else say("質問 " + a.No + " は画面に掛からない（画面の表のどこからも指されていない）");
      });
      li.appendChild(title);
      li.appendChild(el("span", {"class": "meta"}, "（" + (DATA.qaClass[a.No] || "") + "）"));
      if (q["選択肢"]) {
        var ul = el("ul", {"class": "options"});
        q["選択肢"].split(W.optionSeparator).forEach(function (o) {
          ul.appendChild(el("li", null, o + (q["推奨"] && o.indexOf(q["推奨"] + ":") === 0 ? "（推奨）" : "")));
        });
        li.appendChild(ul);
      }
      var where = el("div");
      if (!a.screens.length) where.appendChild(el("span", {"class": "meta"}, "画面に掛からない"));
      a.screens.forEach(function (k) {
        var b = el("button", {"type": "button", "class": "goto", "data-goto": k}, "→ " + k + " " + nameOf(k));
        b.addEventListener("click", function () { open(k); });
        where.appendChild(b);
        where.appendChild(document.createTextNode(" "));
      });
      li.appendChild(where);
      agendaList.appendChild(li);
    });
  }
  if (removedList) {  // 消したもの（前の版から・基準の時点から）
    var count = 0;
    DATA.diffs.forEach(function (d) {
      d.removed.forEach(function (r) {
        count += 1;
        var li = el("li");
        var b = el("button", {"type": "button", "class": "removed-entry", "data-removed": r.key, "data-diff-of": d.kind},
                   d.label + ": " + r.kind + " " + r.key + (r.row["画面名"] || r.row["項目名"] ? " " + (r.row["画面名"] || r.row["項目名"]) : ""));
        b.addEventListener("click", function () { drawRemoved(d, r); });
        li.appendChild(b);
        removedList.appendChild(li);
      });
    });
    if (!count) removedList.appendChild(el("li", null, DATA.diffs.length ? "消したものは無い" : "比べる前の版も基準の時点も無い"));
  }
  if (picker) {
    order.forEach(function (k) {
      var marks = diffMarks("screens", k).map(function (m) { return "［" + m.status + "］"; }).join("");
      picker.appendChild(el("option", {"value": k}, marks + k + " " + screens[k]["画面名"]));
    });
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
<section class="panel" id="agenda"><details open><summary>レビュー会の進め方（今回の会の質問。選ぶとその画面に飛ぶ）</summary><ol id="agenda-list"></ol></details></section>
<section class="panel" id="removed"><details><summary>消したもの</summary><ul id="removed-list"></ul></details></section>
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
    since = None
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
        while "--since" in args:
            at = args.index("--since")
            if at + 1 >= len(args) or since is not None or not args[at + 1] or args[at + 1].startswith("-"):
                raise ValueError("--since には基準の時点（コミットかタグ）を 1 つ渡す")
            since = args[at + 1]
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
        out_dir, text, warnings = build(docs, upto, spec_loop, f"spec-loop {shown}", since)
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
