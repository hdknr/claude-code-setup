#!/usr/bin/env python3
"""scaffold の Red テストのうち緑のケースを一覧に書き（`record`）、一覧に載ったケースが緑のままかを見る（`check`）。

usage: python3 green-list.py record [--repo <リポジトリ>] [--list <一覧>]
       python3 green-list.py check  [--repo <リポジトリ>] [--list <一覧>]

**製品のリポジトリの CI で、実装が緑にした機能の Red テストを走らせ続ける**ための道具である（#1000）。
決まり（いつ・誰が・どこで回すか、性能テストの扱い、別リポジトリの形、GitHub Actions の雛形）の原本は
`references/tree.md` の「Red テストを CI で走らせ続ける」（このプラグインの中にある）。

- **走らせるのは `<リポジトリ>/scaffold/tests` の、生成の印を持つ Red テストだけ**（`scaffold.py` の `GENERATED`）。
  走らせ方は `scaffold.py --red-check` と同じ（`scaffold.py` の `run_tests`。リポジトリの根で、このスクリプトを走らせた Python で、
  `-B` で `__pycache__` を書かずに。環境（`PYTHONPATH` など）は引き継ぐ）。**性能テスト（`scaffold/perf/`）は見ない。**
- **一覧**（既定 `<リポジトリ>/scaffold-green.txt`。`scaffold/` の外——`scaffold/` は生成物で、`scaffold.py --check` の範囲）は、
  `#` で始まる行と空行を読まず、ほかの行は `<テストの名前> <指紋>`（名前は `unittest` の `モジュール.クラス.メソッド`、指紋は sha256 の 16 進 64 字）。
  **手で書かない**——`record` が書く。
- **指紋はケースごとで、そのケースの Red テストが実行する中身から取る**——ファイルを読んで AST でテストのメソッドの行を取り、
  **コメントの行と空行を除いた**「メソッドの外の行（型・実装のモジュール名・共通の関数）」と「そのメソッドの行」を sha256 にする。
  だから**同じ機能の別のケース・題・コメントが変わっても変わらず**、そのケースの入力・期待・呼び出しや、型・`impl_module` が変われば変わる。

`record`:

- Red テストを走らせ、**緑（pass）のケースだけ**を、今の指紋と一緒に一覧に書く（名前の順。前の一覧は書き直す）。
- **前の一覧に載り、今も同じ指紋のケースが緑でなければ、何も書かずに 1**——壊したケースを `record` で一覧から落とさない。
  指紋が変わった・ケースが無くなった載った行は落としてよい（仕様が変えた）——落とした行を出力で名指しする。
- 0: 書いた ／ 1: 載ったケースを壊している（書いていない）／ 2: 判定していない（下）。

`check`（CI が呼ぶ）:

- **1**: 一覧に載り、今も同じ指紋のケースが緑でない（失敗・エラー・飛ばされた・走らなかった）——**実装済みの性質を壊した**。名指しする。
  **一覧に載っていないケースの失敗は数えない**——まだ実装していない機能（追加・変更で赤のもの）で CI が落ちないように。
- **3**: 壊したものは無いが、一覧が古い——緑なのに載っていないケース、指紋が変わったケース、もう無いケースがある。`record` で書き直して commit する。
  1 と 3 が両方あれば 1。
- **0**: 載ったケースが全部緑で、一覧が今の緑と同じ。
- 載ったケースが全部「未実装」で落ちたら、読み込みの経路（`PYTHONPATH`）の付け忘れの見込みも出す（1 のまま）。

**2（判定していない）**: `scaffold/tests` が無い・生成の印を持つ Red テストが 1 つも無い・Red テストを Python として読めない・
Red テストを走らせられない（`run_tests` が落ちた・時間切れ）・一覧が読めないか形が違う・引数の誤り。**緑と読まない。**

**守ること**:

- `check` は、一覧に載って指紋が同じケースが緑でなければ 1 を返し、名指しする
- `check` は、一覧に載っていないケースの失敗で 1 にしない
- `check` は、指紋が変わったケース・もう無いケースを壊したと読まず、3 で書き直しを求める
- `check` は、緑なのに一覧に無いケースがあれば 3
- `record` は緑のケースだけを書く
- `record` は、載って指紋が同じケースが緑でなければ何も書かずに 1
- 指紋は、同じ機能の別のケースとコメントの変更では変わらず、そのケースの中身と共通の部分の変更では変わる
- 生成の印を持たないテストのファイルは見ない
- 一覧の形が違えば 2

**守らないもの**:

- **一覧から手で行を消すこと**——消したケースは見られなくなる（`check` は git の base の一覧と比べない）。PR の差分で見える。
- **`scaffold/` が仕様から見て新しいか**——それは `scaffold.py --check`（同じリポジトリ）か、正本と写しの比べ（別リポジトリ）が見る。CI では先にそれを当てる。
- **Red テストが仕様のケースを写しているか**——生成の側（`scaffold.py`）の責任。
- **性能テスト**（`scaffold/perf/`）——受入基準ではなく、CI の機械の速さで揺れる（`references/nfr.md`）。
- **指紋が変わったケースを `record` までの間に見ること**——作り直しで型や `impl_module` を変えると、その機能の全ケースが一度外れる（3 で赤にするので黙っては外れない）。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 走らせ方・生成の印・置き場所・「未実装」の印は `scaffold.py` のもの（写さない）
scaffold = _load("scaffold", "scaffold.py")

DEFAULT_LIST = "scaffold-green.txt"
HEADER = ("# spec-loop green-list.py record が書いた、scaffold の Red テストのうち緑のケースと、その中身の指紋（手で直さない）。\n"
          "# CI は green-list.py check で、ここに載ったケースが緑のままかを見る（references/tree.md の「Red テストを CI で走らせ続ける」）。\n")
LINE = re.compile(r"(\S+) ([0-9a-f]{64})")


class Unjudged(Exception):
    """判定していない（2）。"""


def code_lines(lines) -> str:
    """コメントの行と空行を除いた行を、改行でつなぐ。"""
    return "\n".join(line for line in lines if line.strip() and not line.strip().startswith("#"))


def fingerprints(tests: Path) -> dict[str, str]:
    """{テストの名前: 指紋}。生成の印を持つ Red テストのファイルだけ。"""
    found = {}
    for path in sorted(tests.glob("test_*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise Unjudged(f"{path}: 読めない（{exc}）")
        if scaffold.GENERATED not in text.split("\n", 1)[0]:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            raise Unjudged(f"{path}: Python として読めない（{exc}）")
        lines = text.split("\n")
        methods = []
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test"):
                    start = min([item.lineno] + [d.lineno for d in item.decorator_list])
                    methods.append((f"{path.stem}.{node.name}.{item.name}", start, item.end_lineno))
        taken = {number for _, start, end in methods for number in range(start, end + 1)}
        common = code_lines(line for number, line in enumerate(lines, 1) if number not in taken)
        for name, start, end in methods:
            body = code_lines(lines[start - 1:end])
            found[name] = hashlib.sha256(f"{common}\n\0\n{body}".encode("utf-8")).hexdigest()
    return found


def read_list(path: Path) -> dict[str, str] | None:
    """一覧の {テストの名前: 指紋}。ファイルが無ければ None。"""
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Unjudged(f"{path}: 一覧を読めない（{exc}）")
    listed = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        match = LINE.fullmatch(line)
        if not match:
            raise Unjudged(f"{path}:{number}: 一覧の行の形が違う（`<テストの名前> <sha256>`）: {line!r}")
        if match.group(1) in listed:
            raise Unjudged(f"{path}:{number}: 同じテストが 2 度載っている: {match.group(1)}")
        listed[match.group(1)] = match.group(2)
    return listed


def observe(repo: Path) -> tuple[dict[str, str], dict]:
    """(指紋, 結果)。結果は `scaffold.py` の `run_tests` のもの（pass・fail・missing・error・skip）。"""
    tests = repo / scaffold.OUT_DIR / "tests"
    if not tests.is_dir():
        raise Unjudged(f"{tests}: Red テストの置き場所が無い")
    prints = fingerprints(tests)
    if not prints:
        raise Unjudged(f"{tests}: 生成の印を持つ Red テストが 1 つも無い")
    try:
        outcomes = scaffold.run_tests(repo, tests)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise Unjudged(f"Red テストを走らせられない（{exc.__class__.__name__}: {exc}）")
    return prints, outcomes


def compare(listed: dict[str, str], prints: dict[str, str], outcomes: dict) -> tuple[list[str], list[str], list[str], list[str]]:
    """(壊した, 指紋が変わった, もう無い, 緑なのに載っていない)。"""
    broken, moved, gone = [], [], []
    for name, digest in sorted(listed.items()):
        if name not in prints:
            gone.append(name)
        elif prints[name] != digest:
            moved.append(name)
        elif outcomes.get(name) != "pass":
            broken.append(name)
    unlisted = sorted(name for name in prints if outcomes.get(name) == "pass" and name not in listed)
    return broken, moved, gone, unlisted


def describe(outcome) -> str:
    return {None: "走らなかった", "fail": "失敗した", "missing": "未実装で失敗した", "error": "エラー",
            "skip": "飛ばされた"}.get(outcome, str(outcome))


def say_broken(broken: list[str], outcomes: dict) -> None:
    for name in broken:
        print(f"壊した: {name}（{describe(outcomes.get(name))}）", file=sys.stderr)
    if broken and all(outcomes.get(name) == "missing" for name in broken):
        print("載ったケースが全部「未実装」で落ちた——実装を読み込めていない見込みもある"
              "（読み込みの経路 PYTHONPATH の付け忘れ。references/monorepo.md の「Red テストを走らせる」）", file=sys.stderr)


def record(repo: Path, path: Path) -> int:
    listed = read_list(path) or {}
    prints, outcomes = observe(repo)
    broken, moved, gone, unlisted = compare(listed, prints, outcomes)
    if broken:
        say_broken(broken, outcomes)
        print(f"一覧に載ったケースのうち {len(broken)} 件が緑でない。一覧を書き直していない"
              "（壊したケースを record で落とさない——実装を直す）", file=sys.stderr)
        return 1
    green = sorted(name for name in prints if outcomes.get(name) == "pass")
    path.write_text(HEADER + "".join(f"{name} {prints[name]}\n" for name in green), encoding="utf-8")
    for name in moved:
        print(f"指紋が変わった: {name}（" + ("緑なので今の指紋で載せ直した" if name in green else "緑でないので落とした") + "）")
    for name in gone:
        print(f"もう無いので落とした: {name}")
    for name in unlisted:
        print(f"足した: {name}")
    print(f"書いた: {path}（緑 {len(green)} 件・足した {len(unlisted)} 件・指紋が変わった {len(moved)} 件・落とした "
          f"{len(gone) + sum(1 for n in moved if n not in green)} 件）")
    return 0


def check(repo: Path, path: Path) -> int:
    listed = read_list(path)
    prints, outcomes = observe(repo)
    broken, moved, gone, unlisted = compare(listed or {}, prints, outcomes)
    if broken:
        say_broken(broken, outcomes)
        print(f"実装済みのケースのうち {len(broken)} 件が緑でない——性質を壊した", file=sys.stderr)
        return 1
    stale = [f"緑なのに一覧に無い: {name}" for name in unlisted]
    stale += [f"指紋が変わった（仕様が変えた）: {name}" for name in moved]
    stale += [f"もう無い: {name}" for name in gone]
    if stale:
        if listed is None:
            print(f"{path}: 一覧が無い", file=sys.stderr)
        for line in stale:
            print(line, file=sys.stderr)
        print(f"一覧が古い（{len(stale)} 件）——green-list.py record で書き直して commit する", file=sys.stderr)
        return 3
    red = sum(1 for name in prints if outcomes.get(name) != "pass")
    print(f"一覧のケースは全部緑（{len(listed or {})} 件）。一覧に無い赤 {red} 件は見ていない（まだ実装していない）")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("command", choices=("record", "check"))
    parser.add_argument("--repo", default=".")
    parser.add_argument("--list")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    path = Path(args.list) if args.list else repo / DEFAULT_LIST
    try:
        return record(repo, path) if args.command == "record" else check(repo, path)
    except Unjudged as exc:
        print(f"{exc}。判定していない", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
