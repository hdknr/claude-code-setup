#!/usr/bin/env python3
"""screen-spec の `init`・`add` のスキルが呼ぶ機械の部分——画面の表と雛形を正本の作業中の版に置く。

usage: python3 write-screens.py hint <docs ディレクトリ> [--spec-loop <spec-loop のプラグインの根>]
       python3 write-screens.py init <docs ディレクトリ> [--prefix <画面IDの接頭辞>] [--profile <profile>] [--spec-loop <…>]
       python3 write-screens.py add <docs ディレクトリ> --name <画面名> --kind <種別> --user <主たる利用者> --purpose <目的と背景>
                                    --can <できること> --basis <根拠> [--parent <画面ID>] [--features <機能>] [--reports <帳票>]
                                    [--refs <参考資料>] [--spec-loop <…>]
       python3 write-screens.py mkdocs <docs ディレクトリ> [--spec-loop <…>]

- `hint`: 何も書かない。`shared/infra.csv` のフロントエンドの行と、このプラグインにある profile の一覧を出す（`init` のスキルが profile を推す材料）。
- `init`: 作業中の版の `requirements/screens/` に、3 つの表（見出し行だけ）・案件ごとの設定（`settings.csv`）・共通仕様（`common.md`）・
  仕様書の雛形（`templates/spec.md`）を置く。
- `add`: 画面ID を採番し、作業中の版の画面の表に 1 行足し、仕様書（`<画面ID>.md`）とワイヤーフレーム（`wireframes/<画面ID>.drawio`）の雛形を置く。
- `mkdocs`: このプラグインの MkDocs のフック（`templates/mkdocs/screen_spec_pages.py`）を、spec-loop の `init-mkdocs.py --hook` で正本（`docs` の親）に登録する（#1098）。
  書くのは spec-loop の `init-mkdocs.py`（`mkdocs.yml` が無ければ spec-loop の雛形も写す。在るファイルは変えない。`mkdocs.yml` は書き換えない）。
  決まりは `references/mkdocs.md`。

**決まりの正は `references/tables.md`（置き場所・設定・採番）と `references/prose.md`（雛形）である**（このプラグインの中にある）。
表の置き場所・列・種別・spec-loop の見つけ方と版の範囲は `check-screens.py` を読み込む（写さない）。
spec-loop の決まりは spec-loop のスクリプトを読み込む——版の見つけ方と重ね方は `merge-versions.py`、成果物の表の番号の形は `check-design-csv.py`。

終了コード:

- 0: 書いた（`hint` は出した。`mkdocs` は登録した・登録済み）
- 1: 重ね合わせが spec-loop の決まりに反する——書かない
- 2: 引数の誤り・`docs` が無い・読めない・想定外の例外——書かない（`mkdocs` は spec-loop の `init-mkdocs.py` が 0 以外で終わったときも 2）
- 3: 今の正本の状態では書けない——版が無い、`init` は置き済み、`add` は `init` の前・設定が読めない・同じ名前の仕様書かワイヤーフレームが在る。書かない
- 4: spec-loop が見つからない・版が対応の範囲の外（`check-screens.py` と同じ）——書かない

**守ること**:

- Q&A 表を読むだけで書かない——Q&A の番号を振らない（番号は spec-loop の req-loop・spec-review が振る）
- 書くのは作業中の版（いちばん大きい `v<n>`）の `requirements/screens/` の中だけ。版が 1 つも無ければ何も書かない（3。版を作るのは spec-loop）
- `mkdocs` は自分では書かない——spec-loop の `init-mkdocs.py --hook` に渡す（`mkdocs.yml` を書き換えない・在るファイルを変えないのは向こうの決まり）
- `init` は、重ねた全体か作業中の版に、3 つの表・`settings.csv`・`common.md`・`templates/spec.md` のどれかが在れば何も書かない（3）
- `add` は、どの版の画面・項目・遷移の表の鍵（重ねる前の生の行。`removed.csv` で消した鍵も含む）とも重ならない番号を採る（接頭辞は `settings.csv`。最大の番号の次）
- 接頭辞は、採る画面ID が spec-loop の成果物の表の番号・Q&A の番号の形・未決定の印に読まれないものだけを受ける（読まれると足した直後の検査が違反か未決定になる）
- `add` の行は、種別・親画面の組・必須の欄を満たす（満たさない引数は 2 で何も書かない）。ステータスは `下書き`
- `add` の仕様書は、重ねた全体に案件の雛形（`templates/spec.md`）があればそれを、無ければこのプラグインの雛形を使う
- 書く前に全部を決め、決まらなければ 1 つも書かない（引数・状態・重ね合わせ・spec-loop の版・表の見出し行・置き場所の形・UTF-8 にできない値）。
  1 つのファイルは一時のファイルに書いてから置き換える（書いている途中で止まっても、前の中身を空にしない）
- spec-loop を読み込むときの `__pycache__` を書かない

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **作業中の版がリリース済みか**（`release-v<n>` のタグ） | タグを見るには git とリモートが要る。正本の CI の spec-loop の `check-frozen.py` が見る |
| **足した行が検査を通るか**（機能・帳票の在りか・入口から辿れること） | `check-screens.py` が見る。`add` のスキルは書いた後にそれを走らせる |
| **項目と遷移の行**（ボタン・遷移） | 画面の中身で、利用者と決める。`add` は画面の行だけを足す（`references/tables.md` の「`init` と `add`」） |
| **ワイヤーフレームの書き出し（SVG）** | spec-loop の `render-diagrams.py` が書き出す。`add` のスキルは書いた後にそれを走らせる |
| **書いている途中の失敗**（ディスクが一杯・権限など） | 置き場所の形（途中がファイル・置き場所がディレクトリ）は書く前に確かめて 3 で止めるが、ほかの失敗では書いた分が残る。書いたものは 1 つずつ出力に名指しする |
| **profile の中身** | profile はまだ無い（#1094）。`--profile` は `未設定` かこのプラグインの `profiles/` にあるディレクトリの名前だけを受ける |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

# spec-loop のスクリプトを読み込むときに `__pycache__` を書かない（`-I` では環境変数が効かない）
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
TEMPLATES = PLUGIN_ROOT / "templates"
PROFILES = PLUGIN_ROOT / "profiles"
MKDOCS_HOOK = TEMPLATES / "mkdocs" / "screen_spec_pages.py"  # `references/mkdocs.md` の写し（テストが突き合わせる）
INIT_MKDOCS = "scripts/init-mkdocs.py"  # spec-loop の中


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checks = _load("check_screens", HERE / "check-screens.py")

# ---- `references/tables.md` の写し（置き場所・設定・採番）
SETTINGS = checks.SCREENS_DIR + "settings.csv"
SETTINGS_COLUMNS = ["項目", "値"]
PREFIX_KEY = "画面IDの接頭辞"
PROFILE_KEY = "profile"
DEFAULT_PREFIX = "S-"
UNSET = "未設定"
PREFIX = re.compile(r"[A-Z][A-Z0-9]*-")
ID_DIGITS = 3
DRAFT = "下書き"
COMMON = checks.SCREENS_DIR + checks.COMMON
SPEC_TEMPLATE = checks.SCREENS_DIR + "templates/spec.md"
WIREFRAMES = checks.SCREENS_DIR + "wireframes/"
FRONTEND = ("frontend", "フロントエンド")  # infra.csv の `項目` の綴り（NFKC・小文字で比べる）
INFRA = "shared/infra.csv"
# 雛形の差し込み
ID_SLOT = "{{画面ID}}"
NAME_SLOT = "{{画面名}}"


class Refused(Exception):
    """書けない（3）。"""


class Broken(Exception):
    """重ね合わせが決まりに反する（1）。"""


def table(columns: list[str] | None, rows: list[list[str]]) -> str:
    """CSV の文字列（`columns` が None なら見出し行を書かない）。"""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    if columns is not None:
        writer.writerow(columns)
    writer.writerows(rows)
    return out.getvalue()


class Docs:
    """正本の `docs` と、spec-loop で重ねた全体。"""

    def __init__(self, spec_loop: Path, docs: Path) -> None:
        scripts = spec_loop / "scripts"
        try:
            self.versions = _load("merge_versions", scripts / "merge-versions.py")
            self.design = _load("check_design_csv", scripts / "check-design-csv.py")
        except (OSError, SyntaxError, ImportError) as e:
            raise checks.Stop(f"{scripts}: spec-loop のスクリプトを読み込めない（{e}）") from None
        self.docs = docs
        try:
            if not self.versions.find_versions(docs, []):
                raise Refused(f"{docs}: 版（v1 など）が 1 つも無い——spec-loop の正本（docs/v1/）を作ってから")
            problems, self.found, self.whole, _ = self.versions.merge(docs)
        except self.versions.Unreadable as e:
            raise checks.Unreadable(str(e)) from None
        if problems:
            raise Broken("\n".join(f"版の重ね合わせ: {p}" for p in problems))
        self.number, self.root = self.found[-1]

    def text(self, path: str) -> str | None:
        if path not in self.whole.files:
            return None
        try:
            return self.whole.files[path].decode("utf-8-sig")
        except UnicodeDecodeError:
            raise checks.Unreadable(f"{path}: UTF-8 で読めない") from None

    def rows(self, path: str) -> list[list[str]] | None:
        text = self.text(path)
        if text is None:
            return None
        try:
            return list(csv.reader(io.StringIO(text, newline="")))
        except csv.Error as e:
            raise checks.Unreadable(f"{path}: CSV として読めない（{e}）") from None

    def placed(self, path: str) -> bool:
        """重ねた全体か作業中の版に在るか。"""
        return path in self.whole.files or path in self.whole.headers or (self.root / path).exists()

    def settings(self) -> dict[str, str]:
        rows = self.rows(SETTINGS)
        if rows is None:
            raise Refused(f"{SETTINGS} が無い——先に init を走らせる")
        if not rows or rows[0] != SETTINGS_COLUMNS:
            raise checks.Unreadable(f"{SETTINGS}:1: 見出し行が決まり（{','.join(SETTINGS_COLUMNS)}）と違う")
        values = {}
        for row in rows[1:]:
            if len(row) != len(SETTINGS_COLUMNS):
                raise checks.Unreadable(f"{SETTINGS}: 列の数が見出し行と違う行がある（{row}）")
            values[row[0].strip()] = row[1].strip()
        return values

    def used_keys(self) -> set[str]:
        """どの版の 3 つの表の鍵（重ねる前の生の行）。

        `removed.csv` で消した鍵もここに入る——spec-loop の重ね方は、前の版までに無いものを消すのを違反にするので、消した鍵は前の版の生の表に在る。
        """
        keys: set[str] = set()
        for _, root in self.found:
            for path in checks.TABLES:
                file = root / path
                if file.is_file():
                    try:
                        rows = list(csv.reader(io.StringIO(file.read_bytes().decode("utf-8-sig"), newline="")))
                    except (OSError, UnicodeDecodeError, csv.Error) as e:
                        raise checks.Unreadable(f"{file}: 読めない（{e}）") from None
                    keys |= {row[0].strip() for row in rows[1:] if row}
        return keys

    def write(self, files: dict[str, str]) -> None:
        """書く前に、どの置き場所も書けない形（途中がファイル・置き場所がディレクトリ）でないことを確かめてから、1 つずつ書いて名指しする。"""
        blocked = []
        for path in files:
            target = self.root / path
            for parent in reversed(target.relative_to(self.root).parents):
                if parent.parts and (self.root / parent).exists() and not (self.root / parent).is_dir():
                    blocked.append(f"{path}（{parent} がディレクトリでない）")
                    break
            else:
                if target.is_dir():
                    blocked.append(f"{path}（ディレクトリが在る）")
        if blocked:
            raise Refused("置き場所に書けない——何も書いていない: " + "、".join(blocked))
        try:
            data = {path: text.encode("utf-8") for path, text in files.items()}  # 書く前に全部を符号にする（符号にできない値で途中から止めない）
        except UnicodeEncodeError as e:
            raise ValueError(f"UTF-8 にできない値がある（{e}）") from None
        for path, body in data.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{target.name}.write-screens")
            temporary.write_bytes(body)
            temporary.replace(target)  # 置き換えは一度に——前の中身を空にしてから書かない
            print(f"書いた: {target}", flush=True)


def profiles() -> list[str]:
    if not PROFILES.is_dir():
        return []
    return sorted(p.name for p in PROFILES.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def check_prefix(prefix: str, docs: "Docs") -> str:
    """接頭辞の形と、採る画面ID が spec-loop のほかの番号・未決定の印に読まれないこと（読まれると、足した直後の検査が違反・未決定になる）。"""
    if not PREFIX.fullmatch(prefix):
        raise ValueError(f"画面IDの接頭辞 {prefix!r} は英大文字で始まり英大文字と数字が続き `-` で終わる形（例: S-）でない")
    taken = {value for value in docs.design.ID_PREFIX.values()}
    if prefix in taken:
        raise ValueError(f"画面IDの接頭辞 {prefix!r} は spec-loop の成果物の表の番号（{'・'.join(sorted(taken))}）と重なる")
    sample = f"{prefix}{1:0{ID_DIGITS}d}"
    qa = docs.versions.qa
    if any(shape.fullmatch(sample) for shape in (qa.NUMBER, qa.INTERNAL_NUMBER)):
        raise ValueError(f"画面IDの接頭辞 {prefix!r} では画面ID（{sample}）が spec-loop の Q&A の番号の形になる")
    if docs.design.spec_exit.find_markers(sample):
        raise ValueError(f"画面IDの接頭辞 {prefix!r} では画面ID（{sample}）が spec-loop の未決定の印を含む")
    return prefix


def hint(docs: Docs) -> int:
    rows = docs.rows(INFRA)
    found = []
    if rows:
        header = rows[0]
        for row in rows[1:]:
            entry = dict(zip(header, row))
            if unicodedata.normalize("NFKC", entry.get("項目", "")).strip().lower() in FRONTEND:
                found.append(entry)
    if rows is None:
        print(f"{INFRA}: 無い（フロントエンドから profile を推せない）")
    elif not found:
        print(f"{INFRA}: フロントエンドの行（項目が {'・'.join(FRONTEND)}）が無い（profile を推せない）")
    for entry in found:
        print(f"{INFRA}: フロントエンド: {entry.get('決定', '')}（状態: {entry.get('状態', '')}）")
    names = profiles()
    print(f"profile: {'・'.join(names) if names else 'このプラグインにはまだ無い——' + UNSET + ' にする'}")
    return 0


def init(docs: Docs, prefix: str, profile: str) -> int:
    check_prefix(prefix, docs)
    if profile != UNSET and profile not in profiles():
        raise ValueError(f"profile {profile!r} はこのプラグインに無い（あるもの: {'・'.join(profiles()) or 'なし'}。無ければ {UNSET}）")
    targets = [*checks.TABLES, SETTINGS, COMMON, SPEC_TEMPLATE]
    there = [path for path in targets if docs.placed(path)]
    if there:
        raise Refused("置き済み——init は何も書かない: " + "、".join(there))
    files = {path: table(checks.COLUMNS[path], []) for path in checks.TABLES}
    files[SETTINGS] = table(SETTINGS_COLUMNS, [[PREFIX_KEY, prefix], [PROFILE_KEY, profile]])
    files[COMMON] = (TEMPLATES / "common.md").read_text(encoding="utf-8")
    files[SPEC_TEMPLATE] = (TEMPLATES / "spec.md").read_text(encoding="utf-8")
    docs.write(files)
    print(f"版 v{docs.number} に置いた（画面IDの接頭辞: {prefix}、profile: {profile}）")
    return 0


def add(docs: Docs, values: dict[str, str]) -> int:
    for path in checks.TABLES:
        if path not in docs.whole.headers:
            raise Refused(f"{path} が無い——先に init を走らせる")
        if docs.whole.headers[path] != checks.COLUMNS[path]:
            raise Refused(f"{path}:1: 見出し行が決まり（{','.join(checks.COLUMNS[path])}）と違う——直してから足す（references/tables.md）")
    settings = docs.settings()
    try:
        prefix = check_prefix(settings.get(PREFIX_KEY, ""), docs)
    except ValueError as e:
        raise Refused(f"{SETTINGS}: {e}") from None
    kind = values["種別"]
    if kind not in checks.SCREEN_KINDS:
        raise ValueError(f"種別 {kind!r} は決まった値（{'・'.join(checks.SCREEN_KINDS)}）でない")
    for column in ("画面名", "主たる利用者", "目的と背景", "できること", "根拠"):
        if not values[column].strip():
            raise ValueError(f"{column} が空——表の必須の欄（references/tables.md）")
    screens = docs.whole.tables[checks.SCREENS]
    parent = values["親画面"].strip()
    if kind in checks.CHILD_KINDS:
        if not parent:
            raise ValueError(f"種別 {kind} には親画面（その画面を持つ画面の画面ID）が要る")
        if parent not in screens:
            raise ValueError(f"親画面 {parent} が画面の表に無い")
    elif parent:
        raise ValueError(f"種別 {kind} には親画面を書かない")

    shape = re.compile(re.escape(prefix) + r"([0-9]+)")
    numbers = [int(m.group(1)) for key in docs.used_keys() if (m := shape.fullmatch(key))]
    key = f"{prefix}{max(numbers, default=0) + 1:0{ID_DIGITS}d}"
    document = f"{key}.md"
    wireframe = f"{WIREFRAMES}{key}.drawio"
    there = [path for path in (checks.SCREENS_DIR + document, wireframe) if docs.placed(path)]
    if there:
        raise Refused(f"画面ID {key} の雛形の置き場所が使われている: " + "、".join(there))

    template = docs.text(SPEC_TEMPLATE)
    source = SPEC_TEMPLATE if template is not None else str(TEMPLATES / "spec.md")
    if template is None:
        template = (TEMPLATES / "spec.md").read_text(encoding="utf-8")
    name = values["画面名"].strip()
    row = {column: "" for column in checks.COLUMNS[checks.SCREENS]}
    row.update({column: values[column].strip() for column in values})
    row.update({"画面ID": key, "ステータス": DRAFT, "仕様書": document})

    own = docs.root / checks.SCREENS
    if own.is_file():
        current = own.read_bytes().decode("utf-8-sig")
        body = current if current.endswith("\n") or not current else current + "\n"
        screens_text = body + table(None, [[row[c] for c in checks.COLUMNS[checks.SCREENS]]])
    else:
        screens_text = table(checks.COLUMNS[checks.SCREENS], [[row[c] for c in checks.COLUMNS[checks.SCREENS]]])
    drawio = (TEMPLATES / "wireframe.xml").read_text(encoding="utf-8")
    docs.write({
        checks.SCREENS: screens_text,
        checks.SCREENS_DIR + document: template.replace(ID_SLOT, key).replace(NAME_SLOT, name),
        wireframe: drawio.replace(ID_SLOT, escape(key, {'"': "&quot;"})).replace(NAME_SLOT, escape(name, {'"': "&quot;"})),
    })
    print(f"画面ID: {key}（版 v{docs.number}。仕様書の雛形: {source}）")
    return 0


OPTIONS = {
    "--name": "画面名", "--kind": "種別", "--user": "主たる利用者", "--purpose": "目的と背景", "--can": "できること",
    "--basis": "根拠", "--parent": "親画面", "--features": "機能", "--reports": "帳票", "--refs": "参考資料",
}
REQUIRED = ("--name", "--kind", "--user", "--purpose", "--can", "--basis")


def parse(args: list[str], allowed: set[str]) -> tuple[list[str], dict[str, str]]:
    positional, options = [], {}
    at = 0
    while at < len(args):
        arg = args[at]
        if arg.startswith("--"):
            if arg not in allowed:
                raise ValueError(f"{arg} は使えない引数")
            if arg in options or at + 1 >= len(args):
                raise ValueError(f"{arg} には値を 1 つ渡す")
            options[arg] = args[at + 1]
            at += 2
        else:
            positional.append(arg)
            at += 1
    return positional, options


def mkdocs(spec_loop: Path, docs_dir: Path) -> int:
    """フックを spec-loop の `init-mkdocs.py --hook` で登録する。出力はそのまま出す。"""
    root = docs_dir.resolve().parent
    proc = subprocess.run([sys.executable, "-I", str(spec_loop / INIT_MKDOCS), str(root), "--hook", str(MKDOCS_HOOK)],
                          capture_output=True, text=True, check=False)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        print(f"spec-loop の init-mkdocs.py が {proc.returncode} で終わった——登録していない（上の出力）", file=sys.stderr)
        return 2
    return 0


def usage() -> str:
    return "\n".join(__doc__.splitlines()[2:8]) if __doc__ else f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）"


def main(argv: list[str]) -> int:
    try:
        if not argv or argv[0] not in ("hint", "init", "add", "mkdocs"):
            raise ValueError(usage())
        command = argv[0]
        allowed = {"--spec-loop"} | ({"--prefix", "--profile"} if command == "init" else set(OPTIONS) if command == "add" else set())
        positional, options = parse(argv[1:], allowed)
        if len(positional) != 1:
            raise ValueError(usage())
        if command == "add":
            missing = [name for name in REQUIRED if name not in options]
            if missing:
                raise ValueError(f"add には {'・'.join(missing)} が要る")
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    docs_dir = Path(positional[0])
    if not docs_dir.is_dir():
        print(f"{docs_dir}: ディレクトリが無い——書いていない", file=sys.stderr)
        return 2
    try:
        spec_loop = checks.find_spec_loop(options.get("--spec-loop"), docs_dir)
        shown = checks.check_version(spec_loop)
        if command == "mkdocs":
            print(f"spec-loop {shown}（{spec_loop}）の init-mkdocs.py で登録する")
            return mkdocs(spec_loop, docs_dir)
        docs = Docs(spec_loop, docs_dir)
    except checks.Stop as e:
        print(f"止めた: {e}", file=sys.stderr)
        return 4
    except checks.Unreadable as e:
        print(f"{e}——書いていない", file=sys.stderr)
        return 2
    except Broken as e:
        print(f"{e}\n重ね合わせが決まりに反する——書いていない", file=sys.stderr)
        return 1
    except Refused as e:
        print(f"{e}", file=sys.stderr)
        return 3
    print(f"spec-loop {shown}（{spec_loop}）の決まりで読む")
    try:
        if command == "hint":
            return hint(docs)
        if command == "init":
            return init(docs, options.get("--prefix", DEFAULT_PREFIX), options.get("--profile", UNSET))
        return add(docs, {column: options.get(flag, "") for flag, column in OPTIONS.items()})
    except ValueError as e:
        print(f"{e}——書いていない", file=sys.stderr)
        return 2
    except Refused as e:
        print(f"{e}", file=sys.stderr)
        return 3
    except checks.Unreadable as e:
        print(f"{e}——書いていない", file=sys.stderr)
        return 2
    except Broken as e:
        print(f"{e}\n重ね合わせが決まりに反する——書いていない", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 — 想定外の例外を 0 にしない
        print(f"想定外の例外で書いていない（書いた分は上に名指しした）: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
