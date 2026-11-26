#!/usr/bin/env python3
"""screen-spec の `init`・`add` のスキルが呼ぶ機械の部分——画面の表と雛形を正本の作業中の版に置く。

usage: python3 write-screens.py hint <docs ディレクトリ> [--spec-loop <spec-loop のプラグインの根>]
       python3 write-screens.py init <docs ディレクトリ> [--prefix <画面IDの接頭辞>] [--profile <profile>] [--external <外部の profile>|なし] [--spec-loop <…>]
       python3 write-screens.py add <docs ディレクトリ> --name <画面名> --kind <種別> --user <主たる利用者> --purpose <目的と背景>
                                    --can <できること> --basis <根拠> [--parent <画面ID>] [--features <機能>] [--reports <帳票>]
                                     [--refs <参考資料>] [--path <パス>] [--spec-loop <…>]
       python3 write-screens.py mkdocs <docs ディレクトリ> [--spec-loop <…>]

- `hint`: 何も書かない。`shared/infra.csv` のフロントエンドの行と、このプラグインにある profile の一覧と、基盤の profile（重ねた全体の `shared/platform/settings.csv`）が
  名指す画面の profile を出す（`init` のスキルが profile を推す材料。#1460）。
- `init`: 作業中の版の `requirements/screens/` に、3 つの表（見出し行だけ）・案件ごとの設定（`settings.csv`）・共通仕様（`common.md`）・
  仕様書の雛形（`templates/spec.md`）を置く。profile を選べば、表の見出し行に profile の列を入れ、共通仕様と仕様書の雛形の末尾に
  profile の節の雛形（このプラグインの `profiles/<profile>/`）を足す。`--external <持ち主>/<リポジトリ> <名前> <タグ>` で外部の profile を `settings.csv` に書き、
  外部の profile が足す列を見出し行に入れる（`--external なし` なら書かない）。
  **`--profile` と `--external` を両方省いたときの初期値は、基盤の profile の画面の層の `重ねる先`**（名指しがあれば `profile` はそれ・外部の profile は同じ束。
  基盤の profile が無い・名指しが無ければ今までどおり `未設定`・外部の profile なし。決まりは `references/profiles.md` の「基盤の profile から引く初期値」）。
- `add`: 画面ID を採番し、作業中の版の画面の表に 1 行足し、仕様書（`<画面ID>.md`）とワイヤーフレーム（`wireframes/<画面ID>.drawio`）の雛形を置く。
  profile の列のうち `パス`（web-spa）は `--path` で渡す。
- `mkdocs`: このプラグインの MkDocs のフック（`templates/mkdocs/screen_spec_pages.py`）を、spec-loop の `init-mkdocs.py --hook` で正本（`docs` の親）に登録する（#1098）。
  書くのは spec-loop の `init-mkdocs.py`（`mkdocs.yml` が無ければ spec-loop の雛形も写す。在るファイルは変えない。`mkdocs.yml` は書き換えない）。
  決まりは `references/mkdocs.md`。

**決まりの正は `references/tables.md`（置き場所・設定・採番）と `references/prose.md`（雛形）と `references/profiles.md`（profile）である**（このプラグインの中にある）。
表の置き場所・列・種別・設定の項目名・profile の列と言い回し・spec-loop の見つけ方と版の範囲・外部の profile の読み方は `check-screens.py` を読み込む（写さない）。
spec-loop の決まりは spec-loop のスクリプトを読み込む——版の見つけ方と重ね方は `merge-versions.py`、成果物の表の番号の形は `check-design-csv.py`、
外部の profile の探し方とタグの時点の `profile.csv` は `external-profile.py`。
**platform-spec は読み込まない**——基盤の profile の設定の置き場所・見出し・項目名（`PLATFORM_*`）は platform-spec の `references/infra-profile.md` の「案件の設定」の写しで、
このプラグインを置いているリポジトリのテスト（test-write-screens.py）が platform-spec の定数と突き合わせる。

終了コード:

- 0: 書いた（`hint` は出した。`mkdocs` は登録した・登録済み）
- 1: 重ね合わせが spec-loop の決まりに反する——書かない
- 2: 引数の誤り・`docs` が無い・読めない・想定外の例外——書かない（`mkdocs` は spec-loop の `init-mkdocs.py` が 0 以外で終わったときも 2）
- 3: 今の正本の状態では書けない——版が無い、`init` は置き済み、`add` は `init` の前・設定が読めない・同じ名前の仕様書かワイヤーフレームが在る。書かない
- 4: spec-loop が見つからない・版が対応の範囲の外（`check-screens.py` と同じ）——書かない。
  `init` が書く外部の profile を読めない・決まりに合わない（`check-screens.py` と同じ）、引数を省いた `init` で基盤の profile から初期値を決められない
  （設定の形が違う・spec-loop に `external-profile.py` が無い・clone が見つからない・タグが無い・`profile.csv` が読めない・`重ねる先` がこのプラグインの profile でない・
  名指した画面の層の行が決まりに合わない——このときは止めた理由に、同じ外部の profile を明示しても止まることと進める案内を添える。#1582）——書かない

**守ること**:

- Q&A 表を読むだけで書かない——Q&A の番号を振らない（番号は spec-loop の req-loop・spec-review が振る）
- 書くのは作業中の版（いちばん大きい `v<n>`）の `requirements/screens/` の中だけ。版が 1 つも無ければ何も書かない（3。版を作るのは spec-loop）
- `mkdocs` は自分では書かない——spec-loop の `init-mkdocs.py --hook` に渡す（`mkdocs.yml` を書き換えない・在るファイルを変えないのは向こうの決まり）
- `init` は、重ねた全体か作業中の版に、3 つの表・`settings.csv`・`common.md`・`templates/spec.md` のどれかが在れば何も書かない（3）
- `add` は、どの版の画面・項目・遷移の表の鍵（重ねる前の生の行。`removed.csv` で消した鍵も含む）とも重ならない番号を採る（接頭辞は `settings.csv`。最大の番号の次）
- 接頭辞は、採る画面ID が spec-loop の成果物の表の番号・Q&A の番号の形・未決定の印に読まれないものだけを受ける（読まれると足した直後の検査が違反か未決定になる）
- `add` の行は、種別・親画面の組・必須の欄を満たす（満たさない引数は 2 で何も書かない）。ステータスは `下書き`
- profile が web-spa なら、`add` は種別が `tab`・`dialog` でない画面に `--path` を求め、`/` で始まるか未決定の印か `N/A。実現方式が未定` の値だけを受ける。
  profile が `未設定` なら `--path` を受けない（2）。設定の `profile` がこのプラグインの profile でも `未設定` でもなければ書かない（3）
- `init` は、profile を選べば表の見出し行を決まりの列＋profile の列にし、共通仕様と案件の雛形の末尾に profile の節の雛形を足す。
  `add` は、案件の雛形が無くこのプラグインの雛形を使うときも、profile の節の雛形を足す
- `add` の仕様書は、重ねた全体に案件の雛形（`templates/spec.md`）があればそれを、無ければこのプラグインの雛形を使う
- 書く前に全部を決め、決まらなければ 1 つも書かない（引数・状態・重ね合わせ・spec-loop の版・表の見出し行・置き場所の形・UTF-8 にできない値）。
  1 つのファイルは一時のファイルに書いてから置き換える（書いている途中で止まっても、前の中身を空にしない）
- spec-loop を読み込むときの `__pycache__` を書かない
- `init` は、`--profile` と `--external` を両方省いたときだけ基盤の profile を読む。どちらかを渡せば読まず（読めない基盤の profile があっても止まらない）、省いた方は `未設定`・外部の profile なし
- 引数を省いた `init` は、基盤の profile の画面の層の `重ねる先` があれば、それを `profile` に、同じリポジトリ・名前・タグを外部の profile にする。
  基盤の profile が無い・画面の層が無い・`重ねる先` が空なら `未設定`・外部の profile なしで、書くものと出力は基盤の profile を見る前と同じ
- 引数を省いた `init` で基盤の profile から初期値を決められなければ、今の初期値に落とさずに 4 で止める（何も書かない）。
  名指した画面の層は `load_external` で確かめ（形式の版・層の行）、設定の値が `外部の profile` の行に写せない形（`リポジトリ` に `/` が無い・profile とタグに空白）なら決められないとする——`hint` も同じ確かめを通った値だけを初期値として出す
- `hint` と引数を省いた `init` は、基盤の profile が名指す画面の層の行が決まりに合わない（`check-screens.py` の `LayerRule`——#1571・#1581 の止め方を含む）とき、
  「明示して渡す」とだけ案内しない——同じ外部の profile を `--external` で明示しても止まることと、外部の profile を直してタグを付け、基盤の profile の設定のタグをそれにするか、`--profile <重ねる先> --external なし` を渡すことを出す（#1582。
  外部の profile はタグの時点で読むので、直しても設定のタグが同じなら止まったまま）。
  読めないとき（設定の形・clone・タグ・形式の版・`重ねる先`・行に写せない形）は今までどおり「読めない（…）」と出す
- `init` が外部の profile を書くときは、`check-screens.py` と同じ読み方（`load_external`）で読み、足す列を見出し行の profile の列の後ろに宣言の順で入れる（読めなければ 4）
- platform-spec のファイルを読み込まない（基盤の profile の設定の項目名は写し、値は spec-loop の `external-profile.py` が読む）

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **作業中の版がリリース済みか**（`release-v<n>` のタグ） | タグを見るには git とリモートが要る。正本の CI の spec-loop の `check-frozen.py` が見る |
| **足した行が検査を通るか**（機能・帳票の在りか・入口から辿れること） | `check-screens.py` が見る。`add` のスキルは書いた後にそれを走らせる |
| **項目と遷移の行**（ボタン・遷移） | 画面の中身で、利用者と決める。`add` は画面の行だけを足す（`references/tables.md` の「`init` と `add`」） |
| **ワイヤーフレームの書き出し（SVG）** | spec-loop の `render-diagrams.py` が書き出す。`add` のスキルは書いた後にそれを走らせる |
| **書いている途中の失敗**（ディスクが一杯・権限など） | 置き場所の形（途中がファイル・置き場所がディレクトリ）は書く前に確かめて 3 で止めるが、ほかの失敗では書いた分が残る。書いたものは 1 つずつ出力に名指しする |
| **profile の選び直し** | `init` で選んだ profile は表の見出し行に入る。後の版で変えると spec-loop の重ね方が止める（`references/profiles.md` の「選び方」） |
| **基盤の profile の設定の値の形の全部**（タグの名前に使える形・`.`・`..` の名前・ほかの項目） | platform-spec の `check-infra-profile.py` が見る。ここは 3 つの項目が 1 行ずつ値つきで在ることと、`外部の profile` の行に写せる形（`<持ち主>/<名前>`・空白なし）だけを見て、ほかは spec-loop の `external-profile.py` が読むときに判定する |
| **外部の profile の足した列を `add` が知ること** | `add` は見出し行が決まり（core＋profile の列）と違えば断る（`references/profiles.md` の「足す列と見出し行」） |
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

# ---- `references/tables.md` の写し（置き場所・設定・採番）。設定のファイル・見出し行・profile の項目名は `check-screens.py` を読む
SETTINGS = checks.SETTINGS
SETTINGS_COLUMNS = checks.SETTINGS_COLUMNS
PREFIX_KEY = "画面IDの接頭辞"
PROFILE_KEY = checks.PROFILE_KEY
DEFAULT_PREFIX = "S-"
UNSET = checks.UNSET
PREFIX = re.compile(r"[A-Z][A-Z0-9]*-")
ID_DIGITS = 3
DRAFT = "下書き"
COMMON = checks.SCREENS_DIR + checks.COMMON
SPEC_TEMPLATE = checks.SCREENS_DIR + "templates/spec.md"
WIREFRAMES = checks.SCREENS_DIR + "wireframes/"
FRONTEND = ("frontend", "フロントエンド")  # infra.csv の `項目` の綴り（NFKC・小文字で比べる）
INFRA = "shared/infra.csv"
EXTERNAL_KEY = checks.EXTERNAL_KEY
EXTERNAL_NONE = "なし"  # `--external なし`——外部の profile を書かない（外部の profile の値は `/` を含むので重ならない）

# ---- platform-spec の `references/infra-profile.md` の「案件の設定」の写し（#1460）。platform-spec は読み込まない——
# このプラグインを置いているリポジトリのテストが platform-spec の `check-infra-profile.py` の定数と突き合わせる
PLATFORM_SETTINGS = "shared/platform/settings.csv"
PLATFORM_SETTINGS_COLUMNS = ["項目", "値"]
PLATFORM_KEYS = ("リポジトリ", "profile", "タグ")
# 雛形の差し込み
ID_SLOT = "{{画面ID}}"
NAME_SLOT = "{{画面名}}"


class Refused(Exception):
    """書けない（3）。"""


class Broken(Exception):
    """重ね合わせが決まりに反する（1）。"""


class LayerBroken(checks.Stop):
    """基盤の profile が名指す画面の層が、行の決まりに合わない（4。`check-screens.py` の `LayerRule`。#1582）。

    同じ外部の profile を `--external` で明示して渡しても止まるので、「明示して渡す」とだけ案内すると行き止まりになる。
    `reason` は止めた理由、`advice` は進める案内（外部の profile を直してタグを付け、設定のタグをそれにするか、`--profile <重ねる先> --external なし`）。
    """

    def __init__(self, reason: str, profile: str) -> None:
        self.reason = reason
        self.advice = (f"外部の profile を直してタグを付け、{PLATFORM_SETTINGS} の タグ をそれにするか、"
                       f"--profile {profile} --external {EXTERNAL_NONE} を渡す")
        super().__init__(f"{reason}——同じ外部の profile を --external で明示して渡しても止まる（{self.advice}）")


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
        self.spec_loop = spec_loop
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


def columns(path: str, profile: str) -> list[str]:
    """表の見出し行——決まりの列＋profile の列（`未設定` なら決まりの列だけ）。"""
    return checks.COLUMNS[path] + checks.PROFILES.get(profile, {}).get("columns", {}).get(path, [])


def with_profile(text: str, profile: str, name: str) -> str:
    """雛形の末尾に profile の節の雛形（`profiles/<profile>/<name>`）を足す。`未設定` ならそのまま。"""
    if profile == UNSET:
        return text
    body = text if text.endswith("\n") or not text else text + "\n"
    return body + (PROFILES / profile / name).read_text(encoding="utf-8")


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
    try:
        profile, external, note = base_initial(docs)
    except LayerBroken as e:
        print(f"基盤の profile: 画面の層が決まりに合わない（{e.reason}）——init の引数を省いても、"
              f"同じ外部の profile を --external で明示して渡しても止まる（{e.advice}）")
        return 0
    except checks.Stop as e:
        print(f"基盤の profile: 読めない（{e}）——init の引数を省くと止まる（--profile と --external を明示して渡す）")
        return 0
    print(f"基盤の profile: {note}")
    if external:
        print(f"init の初期値（--profile と --external を省いたとき）: profile {profile}、外部の profile {' '.join(external)}")
    return 0


def platform_settings(docs: Docs) -> tuple[str, str, str] | None:
    """基盤の profile の設定（`PLATFORM_SETTINGS`）の (リポジトリ, profile, タグ)。無ければ None、形が違えば Stop。"""
    try:
        rows = docs.rows(PLATFORM_SETTINGS)
    except checks.Unreadable as e:
        raise checks.Stop(f"基盤の profile の設定を読めない: {e}") from None
    if rows is None:
        return None
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    where = f"基盤の profile の設定 {PLATFORM_SETTINGS}"
    if not rows or [cell.strip() for cell in rows[0]] != PLATFORM_SETTINGS_COLUMNS:
        raise checks.Stop(f"{where}: 見出しの行が `{','.join(PLATFORM_SETTINGS_COLUMNS)}` でない（platform-spec の check-infra-profile.py で確かめる）")
    found: dict[str, list[str]] = {}
    for row in rows[1:]:
        if len(row) != len(PLATFORM_SETTINGS_COLUMNS):
            raise checks.Stop(f"{where}: 列の数が見出しと違う行がある（{row}）")
        found.setdefault(row[0].strip(), []).append(row[1].strip())
    for key in PLATFORM_KEYS:
        values = found.get(key, [])
        if len(values) != 1 or not values[0]:
            state = "無い" if not values else f"{len(values)} 行ある" if len(values) > 1 else "値が空"
            raise checks.Stop(f"{where}: 項目 {key} の行が{state}（platform-spec の check-infra-profile.py で確かめる）")
    repo, name, tag = (found[key][0] for key in PLATFORM_KEYS)
    return repo, name, tag


def base_initial(docs: Docs) -> tuple[str, tuple[str, str, str] | None, str]:
    """基盤の profile が名指す画面の profile——(profile, 外部の profile か None, 説明)。

    名指し = 基盤の profile のタグの時点の `profile.csv` の層 `画面` の `重ねる先`。基盤の profile が無い・画面の層が無い・`重ねる先` が空なら (`未設定`, None, …)。
    決められない（設定の形・spec-loop の `external-profile.py` が無い・clone・タグ・`profile.csv`・このプラグインに無い `重ねる先`）なら Stop。
    """
    setting = platform_settings(docs)
    if setting is None:
        return UNSET, None, f"{PLATFORM_SETTINGS} が無い（基盤の profile から画面の profile を引かない）"
    repo, name, tag = setting
    label = f"基盤の profile {repo} の {name}（タグ {tag}）"
    path = docs.spec_loop / "scripts" / checks.EXTERNAL_SCRIPT
    if not path.is_file():
        raise checks.Stop(f"{label}: spec-loop に {checks.EXTERNAL_SCRIPT} が無い（spec-loop の版が古い）")
    try:
        ext = _load("spec_loop_external_profile", path)
    except (OSError, SyntaxError, ImportError) as e:
        raise checks.Stop(f"{path}: 読み込めない（{e}）") from None
    try:
        clone, _ = ext.find_clone(repo, project=docs.docs.resolve().parent)
        commit = ext.resolve_tag(clone, tag)
        layers = ext.read_profile(clone, commit, name)
    except ext.Undetermined as e:
        raise checks.Stop(f"{label} を読めない: {e}") from None
    except Exception as e:  # noqa: BLE001 — git が無い・パスが読めないなど。今の初期値に落とさない
        raise checks.Stop(f"{label} を読めない: {type(e).__name__}: {e}") from None
    row = layers.get(checks.EXTERNAL_LAYER)
    if row is None:
        return UNSET, None, f"{label} に層 {checks.EXTERNAL_LAYER} が無い（画面の profile を名指していない）"
    if not row.base:
        return UNSET, None, f"{label} の層 {checks.EXTERNAL_LAYER} の 重ねる先 が空（画面の profile を名指していない）"
    if row.base not in profiles() or row.base not in checks.PROFILES:
        raise checks.Stop(f"{label} の層 {checks.EXTERNAL_LAYER} の 重ねる先 {row.base!r} はこのプラグインの profile でない"
                          f"（あるもの: {'・'.join(profiles()) or 'なし'}）——--profile と --external を明示して渡す")
    if not checks.EXTERNAL_REPO.fullmatch(repo) or any(len(value.split()) != 1 for value in (name, tag)):  # 名指しが在るときだけ（無ければ行に写さない）
        raise checks.Stop(f"{label}: 画面の profile を名指しているが、`外部の profile` の行（`<持ち主>/<リポジトリ> <名前> <タグ>`。空白で区切る）に写せない形——"
                          f"リポジトリが `<持ち主>/<名前>` でないか、profile かタグが空白を含む（--profile と --external を明示して渡す）")
    checker = checks.Checker(docs.spec_loop, docs.docs, None)  # init が書く前に読むのと同じ読み方で、画面の層を確かめる（形式の版・層の行）
    checker.profile = row.base
    try:
        checker.load_external(repo, name, tag)
    except checks.LayerRule as e:  # 読めたが行が決まりに合わない——明示しても止まるので案内を言い分ける（#1582）
        raise LayerBroken(str(e), row.base) from None
    return row.base, (repo, name, tag), f"画面は {row.base} + 外部の profile {repo} {name} {tag}（{label} の層 {checks.EXTERNAL_LAYER} の 重ねる先）"


def parse_external(value: str) -> tuple[str, str, str] | None:
    """`--external` の値。`なし` なら None。形は `settings.csv` の `外部の profile` の行と同じ（`references/profiles.md`）。"""
    if value.strip() == EXTERNAL_NONE:
        return None
    parts = value.split()
    if len(parts) != 3 or not checks.EXTERNAL_REPO.fullmatch(parts[0]):
        raise ValueError(f"--external {value!r} は `<持ち主>/<リポジトリ> <名前> <タグ>` の形か {EXTERNAL_NONE} でない")
    return parts[0], parts[1], parts[2]


def init(docs: Docs, prefix: str, profile_arg: str | None, external_arg: str | None = None) -> int:
    check_prefix(prefix, docs)
    explicit = profile_arg is not None or external_arg is not None
    profile = UNSET if profile_arg is None else profile_arg
    external = None if external_arg is None else parse_external(external_arg)
    if profile != UNSET and (profile not in profiles() or profile not in checks.PROFILES):
        raise ValueError(f"profile {profile!r} はこのプラグインに無い（あるもの: {'・'.join(profiles()) or 'なし'}。無ければ {UNSET}）")
    targets = [*checks.TABLES, SETTINGS, COMMON, SPEC_TEMPLATE]
    there = [path for path in targets if docs.placed(path)]
    if there:
        raise Refused("置き済み——init は何も書かない: " + "、".join(there))
    if not explicit:  # 初期値（#1460）——両方省いたときだけ基盤の profile を読む
        profile, external, note = base_initial(docs)
        if external:
            print(f"基盤の profile から初期値を引いた: {note}")
    added: dict[str, list[str]] = {}
    if external:
        checker = checks.Checker(docs.spec_loop, docs.docs, None)
        checker.profile = profile
        added = checker.load_external(*external).columns
    files = {path: table(columns(path, profile) + added.get(path, []), []) for path in checks.TABLES}
    settings = [[PREFIX_KEY, prefix], [PROFILE_KEY, profile]] + ([[EXTERNAL_KEY, " ".join(external)]] if external else [])
    files[SETTINGS] = table(SETTINGS_COLUMNS, settings)
    files[COMMON] = with_profile((TEMPLATES / "common.md").read_text(encoding="utf-8"), profile, "common.md")
    files[SPEC_TEMPLATE] = with_profile((TEMPLATES / "spec.md").read_text(encoding="utf-8"), profile, "spec.md")
    docs.write(files)
    shown = f"、外部の profile: {' '.join(external)}" if external else ""
    print(f"版 v{docs.number} に置いた（画面IDの接頭辞: {prefix}、profile: {profile}{shown}）")
    return 0


def add(docs: Docs, values: dict[str, str]) -> int:
    for path in checks.TABLES:
        if path not in docs.whole.headers:
            raise Refused(f"{path} が無い——先に init を走らせる")
    settings = docs.settings()
    profile = settings.get(PROFILE_KEY, UNSET) or UNSET
    if profile != UNSET and profile not in checks.PROFILES:
        raise Refused(f"{SETTINGS}: profile {profile!r} はこのプラグインに無い（あるもの: {'・'.join(checks.PROFILES)}。無ければ {UNSET}）")
    for path in checks.TABLES:
        if docs.whole.headers[path] != columns(path, profile):
            raise Refused(f"{path}:1: 見出し行が決まり（{','.join(columns(path, profile))}）と違う——直してから足す（references/tables.md）")
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
    path_value = values.get(checks.PATH_COLUMN, "").strip()
    if checks.PATH_COLUMN in columns(checks.SCREENS, profile):
        if not path_value and kind not in checks.CHILD_KINDS:
            raise ValueError(f"profile {profile} の種別 {kind} の画面には --path（パス）が要る（決まっていなければ未決定の印か "
                             f"「N/A。実現方式が未定」）")
        if (path_value and not path_value.startswith("/") and not checks.undecided_profile(path_value)
                and not docs.design.spec_exit.find_markers(checks.mask_undecided(path_value))):
            raise ValueError(f"パス {path_value!r} は / で始まらない（references/profiles.md）")
    elif path_value:
        raise ValueError(f"profile が {profile} なのでパスの列は無い——--path を渡さない")

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
        template = with_profile((TEMPLATES / "spec.md").read_text(encoding="utf-8"), profile, "spec.md")
    name = values["画面名"].strip()
    header = columns(checks.SCREENS, profile)
    row = {column: "" for column in header}
    row.update({column: values[column].strip() for column in values if column in row})
    row.update({"画面ID": key, "ステータス": DRAFT, "仕様書": document})

    own = docs.root / checks.SCREENS
    if own.is_file():
        current = own.read_bytes().decode("utf-8-sig")
        body = current if current.endswith("\n") or not current else current + "\n"
        screens_text = body + table(None, [[row[c] for c in header]])
    else:
        screens_text = table(header, [[row[c] for c in header]])
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
    "--path": checks.PATH_COLUMN,
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
        allowed = {"--spec-loop"} | ({"--prefix", "--profile", "--external"} if command == "init" else set(OPTIONS) if command == "add" else set())
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
            return init(docs, options.get("--prefix", DEFAULT_PREFIX), options.get("--profile"), options.get("--external"))
        return add(docs, {column: options.get(flag, "") for flag, column in OPTIONS.items()})
    except checks.Stop as e:
        print(f"止めた: {e}——書いていない", file=sys.stderr)
        return 4
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
