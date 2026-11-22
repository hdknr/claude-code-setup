#!/usr/bin/env python3
"""外部の profile の関門——案件の基盤要件の表（`shared/infra.csv`）の `profile の行` が外部の profile の行を指していれば、
platform-spec の版の差分（`scripts/check-profile-diff.py`）を関門に入れ、platform-spec が無ければ止める（#1457。#1312 の段 2）。

usage: python3 profile-gate.py <docs ディレクトリ> [--upto <n>] [--platform-spec <platform-spec のプラグインの根>] [--project <正本の根>]

**spec-loop は platform-spec に依存しない**——`profile の行` に値が無ければ何もせずに 0 で、何も出さず、platform-spec を探さない。
値があるときだけ platform-spec の `scripts/check-profile-diff.py` を**子のプロセスで**呼ぶ（読み込まない——platform-spec が無くても
このスクリプトと、これを読み込む `scaffold.py`・`build-proposal.py` は読み込めて動く）。形は `screen-gate.py`（#1097）を前例にする。

**案件が profile を使っている**とは、`--upto` までの版を spec-loop の重ね方（`merge-versions.py` の `merge`）で重ねた全体の `shared/infra.csv` の
見出しに `profile の行`（列の名前は `check-infra-csv.py` の `PROFILE_COLUMN` を読む——写さない）があり、その列に値が 1 つでもあること。
**案件の設定（どの profile のどのタグか）の置き場所と形は platform-spec の決まりで、spec-loop は読まない**——設定だけ置いて値の無い案件は、比べる行が無いので何もしない。

使っていれば、platform-spec を下の順に探し、`check-profile-diff.py <docs> --spec-loop <このプラグインの根> [--upto <n>] [--project <正本の根>]` を走らせる
（同じ spec-loop の決まりで読ませる）。終了コードを読み替える: 0 → 通る、1（起票の候補がある・違反）→ 1、2 → 2、4 → 4、ほか → 2。
出力は `platform-spec: ` を前に付けて全部写す（`platform-spec: 起票の候補: ` で始まる行を feasibility が起票の候補として読む）。

**platform-spec の見つけ方**（最初に見つけたものを使う。`screen-gate.py` の screen-spec の見つけ方と同じ形の写し——プラグインをまたいで読み込めない）:

1. 引数 `--platform-spec <platform-spec のプラグインの根>`
2. 環境変数 `SPEC_LOOP_PLATFORM_SPEC`
3. リポジトリの形——このプラグインの根の隣の `platform-spec`（`plugins/platform-spec/`）
4. プラグインのキャッシュの形——このプラグインが `<設定>/plugins/cache/<マーケットプレイス>/spec-loop/<版>/` にあるとき、設定のディレクトリ
   （`CLAUDE_CONFIG_DIR`、無ければ `~/.claude`）の `plugins/installed_plugins.json` の `platform-spec@<同じマーケットプレイス>` の `installPath`
   （`scope` が `project` で `projectPath` が `docs` を含むものを先に、無ければ `user`。1 つに決まらなければ見つからないと同じ）

- プラグインの根は、`.claude-plugin/plugin.json` の `name` が `platform-spec` で `scripts/check-profile-diff.py` があるディレクトリである
  （版の差分を持たない古い platform-spec は見つからないと同じ）。
- **1・2 で名指ししたものが platform-spec でなければ、3・4 へは進まずに止める（4）**——名指しを黙って別のものに替えない。

終了コード:

- 0: 通る——`profile の行` に値が無い（何も出さない）か、platform-spec の版の差分が 0
- 1: 通らない——platform-spec の版の差分が 1（起票の候補がある・設定や `profile の行` の違反）か、版の重ね合わせが決まりに反する
- 2: 判定していない——引数の誤り・`docs` が無い・読めない（重ね合わせの `Unreadable`、UTF-8・CSV として読めない基盤要件の表）・platform-spec が 2 か想定外の終了コード
- 4: 止めた——**`profile の行` に値があるのに platform-spec が見つからない**、または platform-spec が 4（clone が無い・タグが無いなど）

関門の使い方:

- scaffold の関門（`scaffold.py`）——画面の関門と同じ条件（作業中の版の全体。`--upto` で前の版の時点を確かめるときは当てない）で当てる。1 は 1、2・4 は 2 で何も作らない
- 提案書（`build-proposal.py`）——要求確定のタグの時点の `docs/` の写しに当て、`--project` に正本の根を渡す（clone の探し方の `CLAUDE.md`）。
  platform-spec の見つけ方（プラグインのキャッシュの `projectPath`）には正本の `docs` を当てる（`locate`）。1 は 1、2・4 は 2 で書かない
- feasibility は CLI で呼び、出力の `platform-spec: 起票の候補: ` の行を共有の Q&A 表に起票する候補として読む（feasibility の `SKILL.md`）

**守ること**:

- `profile の行` に値が無い正本では、重ね合わせもせず、platform-spec を探さず、何も出さずに 0
- 版のディレクトリに値があっても、重ねた全体に値が残らなければ 0（後の版が消した・空にした）
- `profile の行` の見出しが無い表（7 列の表）も、値が無いと読む
- 基盤要件の表の見出しは、空の行を飛ばした最初の行で読む
- `profile の行` に値があるのに platform-spec が見つからなければ 0 にしない（4）
- 名指しした platform-spec が platform-spec でなければ、ほかを探さずに 4
- platform-spec の 1 を 1、2 を 2、4 を 4 にし、知らない終了コードを 0 にしない（2）
- platform-spec の出力を、`platform-spec: ` を前に付けて全部写す
- platform-spec に `--spec-loop`（このプラグインの根）・`--upto`・`--project` を渡す
- プラグインのキャッシュの `projectPath` には、写しではなく正本の `docs`（`locate`）を当てる
- 版の重ね合わせが決まりに反すれば 1
- platform-spec を読み込まない（子のプロセスで呼ぶ）。ファイルを書かない（`__pycache__` も）

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **platform-spec の版の範囲** | platform-spec の側が spec-loop の版を見る（`check-infra-profile.py` の版の確かめ）。逆向きの範囲は持たない（screen-spec と同じ） |
| **版の差分の中身の決まり**（新しい版の決め方・候補の種類・案件の設定） | platform-spec の `check-profile-diff.py` が見る。ここは結果を読み替えるだけ |
| **案件の設定だけを置いて `profile の行` に値の無い案件** | 比べる行が無い。設定の形は platform-spec の `check-infra-profile.py` が見る |
| **本物のプラグインのキャッシュの形が変わったとき**（`installed_plugins.json` の形） | `screen-gate.py` と同じ 1 つの実測の形に合わせて読む。読めなければ見つからないとして 4 |
| **抜ける条件 1・サインオフの前の確かめ** | Issue（#1457）は proposal・scaffold の前を求める。新しい版が出たかは clone のタグで決まり、仕様レビューの抜け方とは別の時点で変わる |
"""

from __future__ import annotations

import csv
import importlib.util
import io
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

PLATFORM_SPEC_NAME = "platform-spec"
PLATFORM_SPEC_ENV = "SPEC_LOOP_PLATFORM_SPEC"
PLATFORM_SPEC_SCRIPT = "scripts/check-profile-diff.py"
SPEC_LOOP_NAME = "spec-loop"
INSTALLED = "plugins/installed_plugins.json"

EXIT_OK, EXIT_FAIL, EXIT_UNJUDGED, EXIT_STOPPED = 0, 1, 2, 4
# platform-spec の `check-profile-diff.py` の終了コード → この関門の終了コード（知らないコードは 2）
PLATFORM_SPEC_CODES = {0: EXIT_OK, 1: EXIT_FAIL, 2: EXIT_UNJUDGED, 4: EXIT_STOPPED}


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


versions = _load("merge_versions", "merge-versions.py")
infra = _load("check_infra_csv", "check-infra-csv.py")
# 基盤要件の表の置き場所と任意の列の名前（`check-infra-csv.py` のもの。写さない）
INFRA = infra.INFRA
COLUMN = infra.PROFILE_COLUMN


class NotFound(Exception):
    """platform-spec が見つからない（4）。"""


class Unreadable(Exception):
    """判定していない（2）。"""


def manifest_name(root: Path) -> str | None:
    try:
        data = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data.get("name") if isinstance(data, dict) else None


def is_platform_spec(root: Path) -> bool:
    return manifest_name(root) == PLATFORM_SPEC_NAME and (root / PLATFORM_SPEC_SCRIPT).is_file()


def installed_platform_spec(docs: Path) -> Path | None:
    """プラグインのキャッシュの形（`<config>/plugins/cache/<マーケットプレイス>/spec-loop/<版>/`）のとき、
    `installed_plugins.json` が名指しする同じマーケットプレイスの platform-spec を返す。形が違う・読めない・1 つに決まらなければ None。"""
    if PLUGIN_ROOT.parent.name != SPEC_LOOP_NAME:
        return None
    market = PLUGIN_ROOT.parent.parent.name
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        data = json.loads((config / INSTALLED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    entries = plugins.get(f"{PLATFORM_SPEC_NAME}@{market}") if isinstance(plugins, dict) else None
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


def find_platform_spec(named: str | None, docs: Path) -> Path:
    """docstring の「platform-spec の見つけ方」の順に探す。名指しされたものが platform-spec でなければ、ほかを探さずに止める。"""
    for source, value in (("--platform-spec", named), (PLATFORM_SPEC_ENV, os.environ.get(PLATFORM_SPEC_ENV) or None)):
        if value is not None:
            root = Path(value)
            if not is_platform_spec(root):
                raise NotFound(f"{source} が指す {root} は platform-spec のプラグインの根でない"
                               f"（.claude-plugin/plugin.json の name が platform-spec でない・{PLATFORM_SPEC_SCRIPT} が無い）")
            return root
    sibling = PLUGIN_ROOT.parent / PLATFORM_SPEC_NAME
    if is_platform_spec(sibling):
        return sibling
    cached = installed_platform_spec(docs)
    if cached is not None and is_platform_spec(cached):
        return cached
    raise NotFound(f"基盤要件の表の {COLUMN} が外部の profile を指しているのに platform-spec が見つからない——platform-spec のプラグインを入れるか、"
                   f"--platform-spec <platform-spec のプラグインの根> か環境変数 {PLATFORM_SPEC_ENV} で渡す。"
                   "版の差分を見ないまま関門を通さない")


def referenced(rendered: dict[str, bytes]) -> int:
    """（重ねた全体か版のディレクトリの）基盤要件の表の `profile の行` に値のある行の数（表・列が無ければ 0）。"""
    if INFRA not in rendered:
        return 0
    try:
        text = rendered[INFRA].decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text, newline="")))
    except (UnicodeDecodeError, csv.Error) as e:
        raise Unreadable(f"{INFRA}: 読めない（{e}）——profile の関門を判定していない") from None
    while rows and not any(cell.strip() for cell in rows[0]):
        rows.pop(0)
    if not rows or COLUMN not in rows[0]:
        return 0
    at = rows[0].index(COLUMN)
    return sum(1 for row in rows[1:] if len(row) > at and row[at].strip())


def placed(docs: Path, upto: int | None) -> bool:
    """`upto` までの版のディレクトリのどれかの基盤要件の表の `profile の行` に値があるか（重ね合わせの前に見る——値の無い正本では重ねもしない）。
    版の名前は `merge` と同じく git の index の綴りで読む（`screen-gate.py` の `placed` と同じ）。"""
    found = versions.tracked(docs)
    index = None if found is None else found[0].get((), set())
    for _, root in versions.find_versions(docs, [], index)[:upto]:
        path = root / INFRA
        if path.is_file() and referenced({INFRA: path.read_bytes()}):
            return True
    return False


def run_platform_spec(root: Path, docs: Path, upto: int | None, project: Path | None) -> tuple[int, list[str], str]:
    """(読み替えた終了コード, 出力の行, 走らせたコマンド)。"""
    command = [sys.executable, str(root / PLATFORM_SPEC_SCRIPT), str(docs), "--spec-loop", str(PLUGIN_ROOT)]
    if upto is not None:
        command += ["--upto", str(upto)]
    if project is not None:
        command += ["--project", str(project)]
    shown = shlex.join(["python3"] + command[1:])
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    except OSError as e:
        return EXIT_UNJUDGED, [f"platform-spec の版の差分を起動できない（{e}）"], shown
    lines = [f"platform-spec: {line}" for line in (proc.stdout + proc.stderr).splitlines()]
    return PLATFORM_SPEC_CODES.get(proc.returncode, EXIT_UNJUDGED), lines + [f"platform-spec の版の差分の終了コード: {proc.returncode}"], shown


def check(docs: Path, upto: int | None = None, named: str | None = None, project: Path | None = None,
          locate: Path | None = None) -> tuple[int, list[str]]:
    """(終了コード, 出力する行)。`profile の行` に値が無ければ (0, [])。
    `locate` は platform-spec の見つけ方（プラグインのキャッシュの `projectPath`）に当てる正本の `docs`——`docs` が写しのとき（`build-proposal.py`）に本物を渡す。"""
    if not docs.is_dir():
        return EXIT_UNJUDGED, [f"{docs}: ディレクトリが無い——profile の関門を判定していない"]
    try:
        if not placed(docs, upto):
            return EXIT_OK, []
        problems, _, _, rendered = versions.merge(docs, upto)
        if problems:
            return EXIT_FAIL, problems + ["版の重ね合わせが決まりに反する（references/versions.md）——profile の関門を通らない"]
        count = referenced(rendered)
    except versions.Unreadable as e:
        return EXIT_UNJUDGED, [f"{e}——profile の関門を判定していない"]
    except Unreadable as e:
        return EXIT_UNJUDGED, [str(e)]
    if not count:
        return EXIT_OK, []
    lines = [f"{INFRA} の {COLUMN} が外部の profile を指している（{count} 行）——profile の関門を当てる"]
    try:
        root = find_platform_spec(named, locate if locate is not None else docs)
    except NotFound as e:
        lines.append(f"止めた: {e}")
        code = EXIT_STOPPED
    else:
        code, out, shown = run_platform_spec(root, docs, upto, project)
        lines += [f"platform-spec の版の差分: {shown}"] + out
    lines.append({
        EXIT_OK: "profile の関門を通る（版の差分の起票の候補 0 件）",
        EXIT_FAIL: "profile の関門を通らない（起票の候補か違反——上の出力）",
        EXIT_UNJUDGED: "profile の関門を判定していない（上の出力）",
        EXIT_STOPPED: "profile の関門で止めた（上の出力）",
    }[code])
    return code, lines


def main(argv: list[str]) -> int:
    args = list(argv)
    named: dict[str, str | None] = {"--platform-spec": None, "--upto": None, "--project": None}
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
            raise ValueError(__doc__.splitlines()[3] if __doc__ else
                             f"usage: python3 {Path(__file__).name} …（-OO で docstring が無く、使い方を出せない）")
    except ValueError as e:
        print(e, file=sys.stderr)
        return EXIT_UNJUDGED
    upto = int(named["--upto"]) if named["--upto"] is not None else None
    project = Path(named["--project"]) if named["--project"] is not None else None
    code, lines = check(Path(args[0]), upto, named["--platform-spec"], project)
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 — 想定外の例外を 0 や 1 にしない
        print(f"{Path(__file__).name}: 想定外の例外で判定していない（{type(e).__name__}: {e}）", file=sys.stderr)
        sys.exit(EXIT_UNJUDGED)
