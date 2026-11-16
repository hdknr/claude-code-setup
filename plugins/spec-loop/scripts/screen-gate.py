#!/usr/bin/env python3
"""画面の表の関門——画面の表（`requirements/screens/`）があれば、その未決定の印と screen-spec の検査の結果を関門に入れ、
screen-spec が無ければ止める（#1097。#1081 の「spec-loop との境目」）。

usage: python3 screen-gate.py <docs ディレクトリ> [--upto <n>] [--screen-spec <screen-spec のプラグインの根>]

**spec-loop は screen-spec に依存しない**——画面の表が無ければ何もせずに 0 で、何も出さない（今の関門と同じ出力）。
画面の表があるときだけ screen-spec の `scripts/check-screens.py` を**子のプロセスで**呼ぶ（読み込まない——screen-spec が無くても
このスクリプトと、これを読み込む `check-spec-exit.py`・`scaffold.py` は読み込めて動く）。

**画面の表がある**とは、`--upto` までの版のディレクトリのどれかに 3 つの表（`requirements/screens/data/` の `screens.csv`・`screen-items.csv`・
`transitions.csv`。置き場所は `merge-versions.py` の `ROW_TABLES` を読む——写さない）のどれかがあり、重ねた全体（spec-loop の `merge-versions.py` の `merge`）にも残ること。
**表を持たない `requirements/screens/`（ワイヤーフレームだけ・散文だけ）は画面の表と見ない**——screen-spec の検査も「画面の表が無い」として 0 にする形にそろえる。
版のディレクトリに無ければ重ね合わせもしない。

画面の表があれば、次の 2 つを見る:

1. **spec-loop が数える未決定の印**——重ねた全体の `requirements/screens/` の下の `.csv`・`.md` に、`check-spec-exit.py` の `find_markers` の印
   （`references/spec-exit.md` の「未決定の印」）があれば 1。**screen-spec が無くても数える**。
2. **screen-spec の検査**——screen-spec を下の順に探し、`check-screens.py <docs> [--upto <n>] --spec-loop <このプラグインの根>` を走らせる
   （同じ spec-loop の決まりで検査させる）。終了コードを読み替える: 0 → 通る、1・3（違反・未決定）→ 1、2 → 2、4 → 4、ほか → 2。
   出力は `screen-spec: ` を前に付けて全部写す。

**screen-spec の見つけ方**（最初に見つけたものを使う。決め方は確認の Issue で利用者に確かめる——#1097 の穴 1）:

1. 引数 `--screen-spec <screen-spec のプラグインの根>`
2. 環境変数 `SPEC_LOOP_SCREEN_SPEC`
3. リポジトリの形——このプラグインの根の隣の `screen-spec`（`plugins/screen-spec/`）
4. プラグインのキャッシュの形——このプラグインが `<設定>/plugins/cache/<マーケットプレイス>/spec-loop/<版>/` にあるとき、設定のディレクトリ
   （`CLAUDE_CONFIG_DIR`、無ければ `~/.claude`）の `plugins/installed_plugins.json` の `screen-spec@<同じマーケットプレイス>` の `installPath`
   （`scope` が `project` で `projectPath` が `docs` を含むものを先に、無ければ `user`。1 つに決まらなければ見つからないと同じ）

- プラグインの根は、`.claude-plugin/plugin.json` の `name` が `screen-spec` で `scripts/check-screens.py` があるディレクトリである。
- **1・2 で名指ししたものが screen-spec でなければ、3・4 へは進まずに止める（4）**——名指しを黙って別のものに替えない。
- 見つけ方の形は screen-spec の `check-screens.py` の spec-loop の見つけ方（screen-spec の `references/spec-loop.md`）と同じ形である
  （プラグインをまたいで読み込めないので写す。テストが両方を同じ形の試料で見る）。

終了コード:

- 0: 通る——画面の表が無い（何も出さない）か、印が無く screen-spec の検査が 0
- 1: 通らない——印がある・screen-spec の検査が違反（1）か未決定（3）・版の重ね合わせが決まりに反する。**4・2 より強い**（どちらもあれば 1。出力には両方が出る）
- 2: 判定していない——引数の誤り・`docs` が無い・読めない（重ね合わせの `Unreadable`、UTF-8 で読めない画面のファイル）・screen-spec の検査が 2 か想定外の終了コード
- 4: 止めた——**画面の表があるのに screen-spec が見つからない**、または screen-spec の検査が 4（spec-loop の版が対応の範囲の外など）

関門の使い方（どれも作業中の版の全体に当てる）:

- 抜ける条件 1（`check-spec-exit.py --docs <docs>`）——1 は条件 1 を満たさない、2・4 は条件 1 を判定していない（2）
- scaffold の関門（`scaffold.py`）——成果物の表の関門と同じ条件で当てる。1 は 1、2・4 は 2
- サインオフの前の確かめ（`references/signoff-tags.md`）——要求確定のタグを付ける前に 0 であること
- req-loop は 4・2 で止まる（1 では止まらない——未決定を起票する段である）。spec-review・scaffold は 0 以外で止まる（各 `SKILL.md`）
- req-loop は出力の `screen-spec: 起票の候補: ` で始まる行（screen-spec の検査が出す、Q&A の番号を添えていない未決定の印）を起票の候補として読む
  （#1100。読み方と起票の仕方は req-loop の `SKILL.md` の手順 3 を正とする）

**守ること**:

- 画面の表が無い正本では、重ね合わせもせず、何も出さずに 0（今の関門の出力を変えない）
- 画面の表があるのに screen-spec が見つからなければ 0 にしない（4）
- 名指しした screen-spec が screen-spec でなければ、ほかを探さずに 4
- 画面の表に残った未決定の印を、screen-spec が無くても 1 にする
- screen-spec の検査の 1・3 を 1、2 を 2、4 を 4 にし、知らない終了コードを 0 にしない（2）
- screen-spec の検査の出力を、`screen-spec: ` を前に付けて全部写す（起票の候補の行を落とさない。#1100）
- 1 を 4・2 より強くする
- screen-spec を読み込まない（子のプロセスで呼ぶ）。ファイルを書かない（`__pycache__` も）

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **screen-spec の版の範囲** | screen-spec の側が spec-loop の版を見る（#1110）。逆向きの範囲は #1081 に無い |
| **画面の表の中身の決まり**（参照・辿れること・散文の節） | screen-spec の `check-screens.py` が見る。ここは結果を読み替えるだけ |
| **表を持たない `requirements/screens/` の中の印**（散文だけ・ワイヤーフレームだけ） | 画面の表と見ない（screen-spec の検査と同じ）。表を置いたら数える |
| **`.csv`・`.md` のほかのファイル（ワイヤーフレームの drawio・svg）の中の印** | 表と散文の仕様書だけを数える。図の中の未決定は図の決まり（`tree.md` の「図」）で扱う |
| **大文字小文字を区別しない FS の `Requirements/Screens/`** | 画面の表が在るかの先の見方はパスの綴りどおり。重ね合わせは `merge-versions.py` の綴りの決まりのまま |
| **本物のプラグインのキャッシュの形が変わったとき**（`installed_plugins.json` の形） | screen-spec の `check-screens.py` と同じ 1 つの実測の形に合わせて読む。読めなければ見つからないとして 4 |
| **印を使わずに書いた未決定**（「あとで決める」） | `check-spec-exit.py` と同じ限界 |
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 読み込む spec-loop のスクリプトの `__pycache__` を書かない（このスクリプトはファイルを 1 つも書かない）
sys.dont_write_bytecode = True
PLUGIN_ROOT = HERE.parent

SCREEN_SPEC_NAME = "screen-spec"
SCREEN_SPEC_ENV = "SPEC_LOOP_SCREEN_SPEC"
SCREEN_SPEC_SCRIPT = "scripts/check-screens.py"
SPEC_LOOP_NAME = "spec-loop"
INSTALLED = "plugins/installed_plugins.json"
SCREENS_DIR = "requirements/screens/"
SCANNED_SUFFIXES = (".csv", ".md")

EXIT_OK, EXIT_FAIL, EXIT_UNJUDGED, EXIT_STOPPED = 0, 1, 2, 4
# screen-spec の `check-screens.py` の終了コード → この関門の終了コード（知らないコードは 2）
SCREEN_SPEC_CODES = {0: EXIT_OK, 1: EXIT_FAIL, 3: EXIT_FAIL, 2: EXIT_UNJUDGED, 4: EXIT_STOPPED}


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


versions = _load("merge_versions", "merge-versions.py")
# 画面の表の 3 つの置き場所（`merge-versions.py` の行の単位で重ねる表。写さない）
TABLES = tuple(versions.ROW_TABLES)


class NotFound(Exception):
    """screen-spec が見つからない（4）。"""


def manifest_name(root: Path) -> str | None:
    try:
        data = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data.get("name") if isinstance(data, dict) else None


def is_screen_spec(root: Path) -> bool:
    return manifest_name(root) == SCREEN_SPEC_NAME and (root / SCREEN_SPEC_SCRIPT).is_file()


def installed_screen_spec(docs: Path) -> Path | None:
    """プラグインのキャッシュの形（`<config>/plugins/cache/<マーケットプレイス>/spec-loop/<版>/`）のとき、
    `installed_plugins.json` が名指しする同じマーケットプレイスの screen-spec を返す。形が違う・読めない・1 つに決まらなければ None。"""
    if PLUGIN_ROOT.parent.name != SPEC_LOOP_NAME:
        return None
    market = PLUGIN_ROOT.parent.parent.name
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        data = json.loads((config / INSTALLED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    entries = plugins.get(f"{SCREEN_SPEC_NAME}@{market}") if isinstance(plugins, dict) else None
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


def find_screen_spec(named: str | None, docs: Path) -> Path:
    """docstring の「screen-spec の見つけ方」の順に探す。名指しされたものが screen-spec でなければ、ほかを探さずに止める。"""
    for source, value in (("--screen-spec", named), (SCREEN_SPEC_ENV, os.environ.get(SCREEN_SPEC_ENV) or None)):
        if value is not None:
            root = Path(value)
            if not is_screen_spec(root):
                raise NotFound(f"{source} が指す {root} は screen-spec のプラグインの根でない"
                               f"（.claude-plugin/plugin.json の name が screen-spec でない・{SCREEN_SPEC_SCRIPT} が無い）")
            return root
    sibling = PLUGIN_ROOT.parent / SCREEN_SPEC_NAME
    if is_screen_spec(sibling):
        return sibling
    cached = installed_screen_spec(docs)
    if cached is not None and is_screen_spec(cached):
        return cached
    raise NotFound("画面の表があるのに screen-spec が見つからない——screen-spec のプラグインを入れるか、"
                   f"--screen-spec <screen-spec のプラグインの根> か環境変数 {SCREEN_SPEC_ENV} で渡す。"
                   "検査を飛ばしたまま関門を通さない")


def has_tables(root: Path) -> bool:
    """`root`（版のディレクトリか重ねた全体の根）に 3 つの表のどれかがあるか。"""
    return any((root / table).is_file() for table in TABLES)


def placed(docs: Path, upto: int | None) -> bool:
    """`upto` までの版のディレクトリのどれかに 3 つの表のどれかがあるか。版の名前は `merge` と同じく git の index の綴りで読む
    （大文字小文字を区別しない FS で、作業ツリーのフォルダの綴りだけが `V1` に変わっていても `merge` が読む `v1` を見落とさない）。"""
    found = versions.tracked(docs)
    index = None if found is None else found[0].get((), set())
    return any(has_tables(root) for _, root in versions.find_versions(docs, [], index)[:upto])


def run_screen_spec(root: Path, docs: Path, upto: int | None) -> tuple[int, list[str], str]:
    """(読み替えた終了コード, 出力の行, 走らせたコマンド)。"""
    command = [sys.executable, str(root / SCREEN_SPEC_SCRIPT), str(docs), "--spec-loop", str(PLUGIN_ROOT)]
    if upto is not None:
        command += ["--upto", str(upto)]
    shown = shlex.join(["python3"] + command[1:])  # spec-review がこの行を直に打つ——空白を含むパスでも打てる形
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    except OSError as e:
        return EXIT_UNJUDGED, [f"screen-spec の検査を起動できない（{e}）"], shown
    lines = [f"screen-spec: {line}" for line in (proc.stdout + proc.stderr).splitlines()]
    return SCREEN_SPEC_CODES.get(proc.returncode, EXIT_UNJUDGED), lines + [f"screen-spec の検査の終了コード: {proc.returncode}"], shown


def check(docs: Path, upto: int | None = None, named: str | None = None) -> tuple[int, list[str]]:
    """(終了コード, 出力する行)。画面の表が無ければ (0, [])。"""
    if not docs.is_dir():
        return EXIT_UNJUDGED, [f"{docs}: ディレクトリが無い——画面の関門を判定していない"]
    try:
        if not placed(docs, upto):
            return EXIT_OK, []
        problems, _, _, rendered = versions.merge(docs, upto)
    except versions.Unreadable as e:
        return EXIT_UNJUDGED, [f"{e}——画面の関門を判定していない"]
    if problems:
        return EXIT_FAIL, problems + ["版の重ね合わせが決まりに反する（references/versions.md）——画面の関門を通らない"]
    if not any(table in rendered for table in TABLES):
        return EXIT_OK, []
    screens = sorted(path for path in rendered if path.startswith(SCREENS_DIR))

    spec_exit = _load("check_spec_exit", "check-spec-exit.py")
    lines = [f"画面の表がある（{SCREENS_DIR} の下に {len(screens)} ファイル）——画面の関門を当てる"]
    marked = 0
    unreadable = False
    for path in screens:
        if not path.endswith(SCANNED_SUFFIXES):
            continue
        try:
            text = rendered[path].decode("utf-8-sig")
        except UnicodeDecodeError:
            lines.append(f"{path}: UTF-8 で読めない——未決定の印を数えていない")
            unreadable = True
            continue
        for number, marker in spec_exit.find_markers(text):
            lines.append(f"{path}:{number}: 未決定の印 {marker}")
            marked += 1

    try:
        root = find_screen_spec(named, docs)
    except NotFound as e:
        lines.append(f"止めた: {e}")
        code = EXIT_STOPPED
    else:
        code, out, shown = run_screen_spec(root, docs, upto)
        lines += [f"screen-spec の検査: {shown}"] + out
    if marked or code == EXIT_FAIL:
        result = EXIT_FAIL
    elif code == EXIT_STOPPED:
        result = EXIT_STOPPED
    elif code == EXIT_UNJUDGED or unreadable:
        result = EXIT_UNJUDGED
    else:
        result = EXIT_OK
    lines.append({
        EXIT_OK: "画面の関門を通る（未決定の印 0 件・screen-spec の検査が 0）",
        EXIT_FAIL: f"画面の関門を通らない（未決定の印 {marked} 件・screen-spec の検査の結果は上）",
        EXIT_UNJUDGED: "画面の関門を判定していない（上の出力）",
        EXIT_STOPPED: "画面の関門で止めた（上の出力）",
    }[result])
    return result, lines


def main(argv: list[str]) -> int:
    args = list(argv)
    named = None
    upto = None
    try:
        while "--screen-spec" in args:
            at = args.index("--screen-spec")
            if at + 1 >= len(args) or named is not None:
                raise ValueError("--screen-spec には screen-spec のプラグインの根を 1 つ渡す")
            named = args[at + 1]
            del args[at:at + 2]
        while "--upto" in args:
            at = args.index("--upto")
            if at + 1 >= len(args) or upto is not None or not re.fullmatch(r"[1-9][0-9]*", args[at + 1]):
                raise ValueError("--upto には 1 以上の整数を 1 つ渡す")
            upto = int(args[at + 1])
            del args[at:at + 2]
        if len(args) != 1 or args[0].startswith("-"):
            raise ValueError(__doc__.splitlines()[3] if __doc__ else
                             f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）")
    except ValueError as e:
        print(e, file=sys.stderr)
        return EXIT_UNJUDGED
    code, lines = check(Path(args[0]), upto, named)
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 — 想定外の例外を 0 や 1 にしない
        print(f"{Path(__file__).name}: 想定外の例外で判定していない（{type(e).__name__}: {e}）", file=sys.stderr)
        sys.exit(EXIT_UNJUDGED)
