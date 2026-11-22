#!/usr/bin/env python3
"""案件の基盤要件の表（`shared/infra.csv`）の `profile の行` が、案件の設定で決めた外部の profile のタグの基盤の層に在るかを照らす（#1456）。

usage: python3 check-infra-profile.py <docs ディレクトリ> [--upto <n>] [--clone <profile の手元の clone>] [--spec-loop <spec-loop のプラグインの根>]

**決まりの正は `references/infra-profile.md`（基盤の層の形・形式の版の範囲・案件の設定・`profile の行` の書き方）と `references/spec-loop.md`
（対応する spec-loop の版・spec-loop の見つけ方）である**（このプラグインの中にある）。下の定数はその写しで、
**写しがずれていないかは、このプラグインを置いているリポジトリの `scripts/test-check-infra-profile.py` が突き合わせる。**

- **spec-loop の決まりを写さない**——版の重ね方は spec-loop の `merge-versions.py` の `merge`、列の名前は `check-infra-csv.py` の `PROFILE_COLUMN`、
  外部の profile の探し方・タグの時点の読み出し・形式の版の判定は `external-profile.py` の `find_clone`・`resolve_tag`・`read_layer` を読み込む。
- **読むだけ**——ファイルを 1 つも書かない（spec-loop を読み込むときの `__pycache__` も）。clone は `external-profile.py` のとおり、タグの時点を読むだけ。
- 基盤要件の表のほかの形（見出しの行・状態・根拠）は見ない——spec-loop の `check-infra-csv.py` が見る。
- 標準ライブラリと `git` だけを使う。

終了コード:

- 0: `profile の行` の ID が全部、そのタグの基盤の層に在る。設定も `profile の行` の値も無いとき（platform-spec を使っていない案件）も 0
- 1: 違反——無い ID がある・`profile の行` を指しているのに設定が無い・設定の形が違う・ID の形が違う・重ね合わせが spec-loop の決まりに反する
- 2: 判定していない——引数の誤り・`docs` が無い・表が読めない・想定外の例外
- 4: 止めた（判定できなかった）——spec-loop が見つからない・版が範囲の外か古い・clone が見つからない・タグが無い・profile に基盤の層が無い・
  基盤の層の形式の版が範囲の外・層の表の形が違う

**守ること**:

- 設定も `profile の行` の値も無ければ、clone を探さずに 0
- `profile の行` の ID が、設定のタグの時点の基盤の層に在れば通す
- そのタグの基盤の層に無い ID（別のタグにだけ在る ID も）を、表の行・項目・ID を名指しして 1
- 1 つのセルに `・` で区切った ID を、1 つずつ照らす
- `・` で区切った中に空の ID があれば 1
- `profile の行` を指しているのに設定が無ければ 1
- 設定の見出しが `項目,値` でなければ 1
- 設定に決まりの外の項目があれば 1
- 設定に同じ項目が 2 行あれば 1
- 設定の値が空なら 1
- 設定に決まりの項目が足りなければ 1
- 設定の `リポジトリ` が `<持ち主>/<名前>` の形でなければ 1
- 設定の `profile` が profile の名前の形（`/` を含まない・`.`・`..` でない）でなければ 1
- 設定の `タグ` がタグの名前に使えない形（`git check-ref-format` が通さない。`v1~1` など）なら 1
- 設定があれば、`profile の行` の値が無くても profile を読む（設定の誤りを 0 にしない）
- profile に基盤の層が無ければ 4（「無い」の 3 にしない）
- 基盤の層の表の見出しが形式の版 1 の 4 列（`ID,要約,リンク,項目`）でなければ 4
- 基盤の層の表の見出しは、空の行を飛ばした最初の行で読む（spec-loop の読み方と同じ）
- 名指した spec-loop が spec-loop でなければ、ほかを探さずに 4
- spec-loop の版が対応の範囲の外なら、照らす前に 4
- 重ね合わせが spec-loop の決まりに反すれば 1
- `--upto` で前の版の時点の全体を照らす
- 引数 `--clone` を外部の profile の探し方に渡す
- 外部の profile の探し方の `CLAUDE.md` は、正本の根（`docs` の親）のものを読む
- 基盤要件の表が UTF-8 で読めなければ 2

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **基盤の層の `項目` と、案件の行の `項目` が合うか** | この版は ID が在るかだけを照らす（#1312 の段 1）。項目の照合は後の段 |
| **`リンク` が切れていないか** | spec-loop の `external-profile.py check` が見る。照合は ID だけ |
| **`profile の行` のセルの未決定の印**（`TBD` など） | 印も ID として照らし、無い ID として名指す（印を別に数えない） |
| **2 つのタグの間の差分** | 版を上げたときの差分と関門は後の段（#1457） |
| **基盤要件の表のほかの形**（見出し・状態・根拠） | spec-loop の `check-infra-csv.py` が見る。ここは `profile の行` の列だけを読む（列が無ければ、照らす ID が無い） |
| **clone が本当にそのリポジトリの clone か** | `external-profile.py` の守らないもの（名指しを信じる） |
| **本物のプラグインのキャッシュの形が変わったとき**（`installed_plugins.json` の形） | screen-spec と同じ 1 つの実測に合わせて読む。読めなければ見つからないとして 4 |
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
# spec-loop のスクリプトを読み込むときに `__pycache__` を書かない（このスクリプトはファイルを 1 つも書かない）
sys.dont_write_bytecode = True

# ---- `references/spec-loop.md` の写し
SPEC_LOOP_NAME = "spec-loop"
SPEC_LOOP_MIN = (0, 133, 0)  # この版を含む
SPEC_LOOP_BELOW = (1, 0, 0)  # この版を含まない
SPEC_LOOP_ENV = "PLATFORM_SPEC_SPEC_LOOP"
INSTALLED = "plugins/installed_plugins.json"

# ---- `references/infra-profile.md` の写し
INFRA = "shared/infra.csv"
SETTINGS = "shared/platform/settings.csv"
SETTINGS_COLUMNS = ["項目", "値"]
SETTING_REPO = "リポジトリ"
SETTING_PROFILE = "profile"
SETTING_TAG = "タグ"
SETTING_KEYS = (SETTING_REPO, SETTING_PROFILE, SETTING_TAG)
LAYER = "基盤"
LAYER_COLUMNS = ["ID", "要約", "リンク", "項目"]
FORMAT_LOW = "1"   # この版を含む
FORMAT_HIGH = "2"  # この版を含まない
ID_SEPARATOR = "・"
REPO_FORM = re.compile(r"[^/\s]+/[^/\s]+")


class Stop(Exception):
    """止めた・判定できなかった（4）。"""


class Unreadable(Exception):
    """判定していない（2）。"""


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- spec-loop の見つけ方（screen-spec の `check-screens.py` と同じ順の写し。platform-spec は screen-spec に依存しない）


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
    """プラグインのキャッシュの形（`<config>/plugins/cache/<マーケットプレイス>/platform-spec/<版>/`）のとき、
    `installed_plugins.json` が名指しする同じマーケットプレイスの spec-loop を返す。形が違う・読めない・1 つに決まらなければ None。"""
    if PLUGIN_ROOT.parent.name != "platform-spec":
        return None
    market = PLUGIN_ROOT.parent.parent.name
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        data = json.loads((config / INSTALLED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    entries = plugins.get(f"{SPEC_LOOP_NAME}@{market}") if isinstance(plugins, dict) else None
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


# ---- 照らす


class Checker:
    def __init__(self, spec_loop: Path, docs: Path, upto: int | None, clone: str | None) -> None:
        scripts = spec_loop / "scripts"
        try:
            self.versions = _load("platform_spec_merge_versions", scripts / "merge-versions.py")
            infra = _load("platform_spec_check_infra_csv", scripts / "check-infra-csv.py")
            self.ext = _load("platform_spec_external_profile", scripts / "external-profile.py")
        except (OSError, SyntaxError, ImportError) as e:
            raise Stop(f"{scripts}: spec-loop のスクリプトを読み込めない（{e}）") from None
        column = getattr(infra, "PROFILE_COLUMN", None)
        if not isinstance(column, str):
            raise Stop(f"{scripts}/check-infra-csv.py が任意の列の名前（PROFILE_COLUMN）を持たない——spec-loop が古い（references/spec-loop.md）")
        self.column = column
        self.docs = docs
        self.upto = upto
        self.clone = clone
        self.violations: list[str] = []
        self.notes: list[str] = []

    def text(self, whole, path: str) -> str | None:
        if path not in whole.files:
            return None
        try:
            return whole.files[path].decode("utf-8-sig")
        except UnicodeDecodeError:
            raise Unreadable(f"{path}: UTF-8 として読めない") from None

    @staticmethod
    def rows(text: str, path: str) -> list[tuple[int, list[str]]]:
        try:
            reader = csv.reader(io.StringIO(text, newline=""))
            return [(reader.line_num, fields) for fields in reader]
        except csv.Error as e:
            raise Unreadable(f"{path}: CSV として読めない（{e}）") from None

    def references(self, whole) -> list[tuple[str, str, list[str]]]:
        """`profile の行` の値のある行の (場所, 項目, ID の並び)。列が無ければ空。"""
        text = self.text(whole, INFRA)
        if text is None:
            return []
        rows = self.rows(text, INFRA)
        if not rows or self.column not in rows[0][1]:
            return []
        header = rows[0][1]
        at = header.index(self.column)
        item = header.index("項目") if "項目" in header else None
        out = []
        for line, fields in rows[1:]:
            value = fields[at].strip() if len(fields) > at else ""
            if not value:
                continue
            name = fields[item].strip() if item is not None and len(fields) > item else ""
            out.append((f"{INFRA}:{line}", name or "(項目なし)", [part.strip() for part in value.split(ID_SEPARATOR)]))
        return out

    def settings(self, whole) -> dict[str, str] | None:
        """案件の設定。無ければ None。形の違反は violations に足して、読めたものを返す。"""
        text = self.text(whole, SETTINGS)
        if text is None:
            return None
        rows = self.rows(text, SETTINGS)
        if not rows or rows[0][1] != SETTINGS_COLUMNS:
            self.violations.append(f"{SETTINGS}:1: 見出しの行が `{','.join(SETTINGS_COLUMNS)}` でない: {','.join(rows[0][1]) if rows else '（空）'}")
            return {}
        found: dict[str, str] = {}
        for line, fields in rows[1:]:
            if not any(f.strip() for f in fields):
                continue
            where = f"{SETTINGS}:{line}"
            if len(fields) != len(SETTINGS_COLUMNS):
                self.violations.append(f"{where}: 列の数が {len(fields)}（見出しは {len(SETTINGS_COLUMNS)}）")
                continue
            key, value = fields[0].strip(), fields[1].strip()
            if key not in SETTING_KEYS:
                self.violations.append(f"{where}: 項目 {key!r} は決まりの外（{'・'.join(SETTING_KEYS)} のどれか）")
                continue
            if key in found:
                self.violations.append(f"{where}: 項目 {key} が 2 行ある")
                continue
            if not value:
                self.violations.append(f"{where}: {key} の値が空")
            found[key] = value
        for key in SETTING_KEYS:
            if key not in found:
                self.violations.append(f"{SETTINGS}: 項目 {key} の行が無い")
        self.setting_forms(found)
        return found

    def setting_forms(self, found: dict[str, str]) -> None:
        """設定の値の形。違えば violations に足す（外部の profile を読む前に、書き間違いを 1 にする）。"""
        repo, name, tag = (found.get(key, "") for key in SETTING_KEYS)
        if repo and not REPO_FORM.fullmatch(repo):
            self.violations.append(f"{SETTINGS}: {SETTING_REPO} {repo!r} が `<持ち主>/<名前>` の形でない")
        if name and ("/" in name or name in (".", "..")):
            self.violations.append(f"{SETTINGS}: {SETTING_PROFILE} {name!r} が profile の名前の形でない（`/` を含まない・`.`・`..` でない）")
        if tag and subprocess.run(["git", "check-ref-format", f"refs/tags/{tag}"], capture_output=True).returncode != 0:
            self.violations.append(f"{SETTINGS}: {SETTING_TAG} {tag!r} がタグの名前に使えない形")

    def layer_ids(self, settings: dict[str, str]) -> set[str]:
        """設定のタグの時点の基盤の層の ID。判定できなければ Stop。"""
        ext = self.ext
        repo, name, tag = settings[SETTING_REPO], settings[SETTING_PROFILE], settings[SETTING_TAG]
        try:
            clone, source = ext.find_clone(repo, self.clone, self.docs.resolve().parent)
            commit = ext.resolve_tag(clone, tag)
            layer = ext.read_layer(clone, commit, name, LAYER, FORMAT_LOW, FORMAT_HIGH)
            for path in layer.files:
                head = next((row for row in csv.reader(io.StringIO(ext.read_blob(clone, commit, path).decode("utf-8-sig"), newline=""))
                             if any(cell.strip() for cell in row)), [])
                if head != LAYER_COLUMNS:
                    raise Stop(f"{repo} の {path}（タグ {tag}）の見出しが形式の版 1 の `{','.join(LAYER_COLUMNS)}` でない: {','.join(head)}")
        except ext.LayerMissing as e:
            raise Stop(f"profile {name}（{repo} のタグ {tag}）に{LAYER}の層が無い: {e}") from None
        except ext.Undetermined as e:
            raise Stop(f"{repo} の profile {name}（タグ {tag}）を読めない: {e}") from None
        except UnicodeDecodeError as e:
            raise Stop(f"{repo} の profile {name}（タグ {tag}）の{LAYER}の層の表が UTF-8 でない: {e}") from None
        self.notes.append(f"profile: {repo} の {name}（タグ {tag}・{layer.version}・{len(layer.rows)} 行。clone {clone}（出所: {source}））")
        return set(layer.rows)

    def check(self) -> int:
        try:
            problems, _, whole, _ = self.versions.merge(self.docs, self.upto)
        except self.versions.Unreadable as e:
            raise Unreadable(str(e)) from None
        if problems:
            self.violations.extend(f"版の重ね合わせ: {problem}" for problem in problems)
            return self.finish()
        refs = self.references(whole)
        settings = self.settings(whole)
        if settings is None:
            if not refs:
                print(f"{SETTINGS} も {INFRA} の {self.column} の値も無い——照らすものが無い（platform-spec を使っていない）")
                return 0
            for where, item, _ in refs:
                self.violations.append(f"{where}: {item} が {self.column} を指しているのに、案件の設定（{SETTINGS}）が無い")
            return self.finish()
        for where, item, ids in refs:
            if any(not i for i in ids):
                self.violations.append(f"{where}: {item} の {self.column} に空の ID がある（`{ID_SEPARATOR}` で区切った間・前後）")
        if self.violations:
            return self.finish()
        known = self.layer_ids(settings)
        checked = 0
        for where, item, ids in refs:
            for rid in ids:
                checked += 1
                if rid not in known:
                    self.violations.append(f"{where}: {item} の {self.column} {rid} が {settings[SETTING_REPO]} の {settings[SETTING_PROFILE]}"
                                           f"（タグ {settings[SETTING_TAG]}）の{LAYER}の層に無い")
        self.notes.append(f"照らした ID {checked} 件")
        return self.finish()

    def finish(self) -> int:
        for note in self.notes:
            print(note)
        for violation in self.violations:
            print(f"違反: {violation}")
        print(f"違反 {len(self.violations)} 件")
        return 1 if self.violations else 0


def main(argv: list[str]) -> int:
    args = list(argv)
    named = {"--spec-loop": None, "--clone": None, "--upto": None}
    try:
        for flag in named:
            while flag in args:
                at = args.index(flag)
                if at + 1 >= len(args) or named[flag] is not None:
                    raise ValueError(f"{flag} には値を 1 つ渡す")
                named[flag] = args[at + 1]
                del args[at:at + 2]
        if named["--upto"] is not None and not re.fullmatch(r"[1-9][0-9]*", named["--upto"]):
            raise ValueError("--upto には 1 以上の整数を 1 つ渡す")
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
    upto = int(named["--upto"]) if named["--upto"] is not None else None
    try:
        spec_loop = find_spec_loop(named["--spec-loop"], docs)
        shown = check_version(spec_loop)
        checker = Checker(spec_loop, docs, upto, named["--clone"])
        print(f"spec-loop {shown}（{spec_loop}）の重ね方と外部の profile の読み方で照らす")
        return checker.check()
    except Stop as e:
        print(f"止めた: {e}", file=sys.stderr)
        return 4
    except Unreadable as e:
        print(f"{e}——判定していない", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 — 想定外の例外を 0 や 1 にしない
        print(f"想定外の例外で判定していない: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
