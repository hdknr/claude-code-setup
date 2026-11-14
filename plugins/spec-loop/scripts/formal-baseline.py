#!/usr/bin/env python3
"""形式検査のモデルを残す場所を決め（`target`）、残したモデルの形を確かめる（`check`）。

usage:
    python3 formal-baseline.py target [--repo <正本リポジトリ>]
    python3 formal-baseline.py check <docs/v<n>/spec/formal/<対象>>

**決まりの正は `references/tree.md` の「形式検査のモデル」である**（このプラグインの中にある）。
下の定数（記録の項目・結果と前回のモデルの値）はその写しで、
**写しがずれていないかはこのリポジトリの `scripts/test-formal-baseline.py` が突き合わせて見る**。
`formal-baseline` のスキル（#1031）が両方を呼び、`spec-review` の「モデルを残す」も `check` を呼ぶ。

`target` — **モデルを書いてよい版**を決める:

- 版は `docs/` 直下の `v<n>`（見つけ方は `merge-versions.py` の `find_versions` を読み込む——写さない）。**書くのは番号が最大の版（作業中の版）だけ**。
- **作業中の版にリリースのタグ `release-v<n>` があれば書かない（3）**——凍結した版を直すと `check-frozen.py` が落ちる。
  次の版を作ってから呼び直す。タグの命名は `check-frozen.py` の `releases` を読み込む（写さない）。
- **手元のタグに加えて、リモートごとに `git ls-remote --tags` で訊いたタグも見る**——`--no-tags` で取った clone や、他の人が付けて
  まだ取っていない `release-v<n>` を「リリースしていない」と読まないため（#1031 の 1 パス目）。**どれか 1 つのリモートでも訊けなければ 2**。リモートが無ければ手元のタグだけを見る。
  **リポジトリの状態は変えない**——`git fetch` は使わない（利用者の `fetch.prune`・`fetch.pruneTags` に従って、手元にだけあるタグ（押す前のサインオフのタグ）を消すため。#1031 の 2 パス目）。
- 0 なら、書く場所（`docs/v<n>/spec/formal/`）と、保存したモデルを探す場所（v1 は同じ場所、v2 以降は重ね合わせた全体
  `build/merged/spec/formal/`——`merge-versions.py docs build/merged` が作る）を出す。

`check` — 残したモデルの 1 つの対象のディレクトリを確かめる:

- **置き場所**: 親が `spec/formal/` で、`<対象>` の名前が英小文字・数字・ハイフンだけ。
- **`README.md` の記録**: `| 項目 | 記録 |` の 2 列の表で、`tree.md` の項目が 1 行ずつ、記録が空でなく、同じ項目が 2 行無い。
  `結果` は `反例なし`／`反例あり` のどちらか（後ろに続けてよいのは `（` で始まる要約だけ。`判定できなかった` の対象は残さない）。
  `前回のモデル` も 4 つの値のどれか（同じく `（` で始まる要約を続けてよい）。
- **`モデルのファイル`**: バッククォートで囲んだファイルの名前が 1 つ以上あり、どれもこのディレクトリの通常のファイルである（`/` を含まない・`README.md` でない）。
- **ディレクトリの中身は、`README.md` と `モデルのファイル` の一覧だけ**——TLC の `states/`・Alloy の `<名前>/`・出力を落としたファイル・前に残したファイルが在れば違反。

終了コード:

- 0: `target` は書く場所を決めた／`check` は形どおり
- 1: `check` の違反（違反を全部出す）
- 2: 判定していない——git でない・浅い clone・リモートのタグを訊けない・版が無い・版の決まりに反する・ディレクトリが無い・`README.md` が読めない・想定外の例外
- 3: `target` で、作業中の版がリリース済み（書かない）

**守ること**:

| 守ること | 破る形 |
| --- | --- |
| 作業中の版がリリース済みなら書く場所を出さない（3） | 凍結した版に書いて `check-frozen.py` が落ちる |
| 版が無い・版の決まりに反する・浅い clone なら 2 で、書く場所を出さない | 「凍結していない」と読み違えて書く |
| リモートのタグも `ls-remote` で訊いて見る。訊けなければ 2 | `--no-tags` の clone・取っていないタグで、リリース済みの版に書く |
| `git fetch` を使わず、リポジトリを変えない | 利用者の `fetch.pruneTags` で、押す前のサインオフのタグが消える |
| 一覧に無いファイル・ディレクトリを違反にする | 検査器の作業ファイルや前の残りが基準のモデルに混ざる |
| 一覧のファイルが無ければ違反にする | 次の回が読むモデルが欠ける |
| 記録の項目が欠けた・空・2 行あるなら違反にする | 次の回が前提や陽性対照を確かめ直せない |
| `結果`・`前回のモデル` は値そのものか、値に `（…）` の要約を 1 つだけ続けた形（閉じた後ろに何も無い）だけを通す | `反例なしかは判定できなかった`・`反例なし（N=3）かは判定できなかった` のような、走らせていないモデルが残る |
| 置き場所と名前の形を見る | 次の回が同じ名前で探せない |

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **リモートにも押していない `release-v<n>`**（他の人の手元にだけあるタグ） | 訊く先に無いものは見えない。タグは付けたら押す運用で守る |
| **モデルの中身が仕様に合っているか・検査器が本当に走らせたものか** | 判定役の仕事で、報告から写すときにスキルが守る（`cp` で写す） |
| **記録の値が正しいか**（陽性対照が本当に反例を出したか・前提が全部か） | 文面の真偽は機械で決まらない |
| **`残した回` が記録の表の行を指しているか** | 記録の表は版ごとに `docs/` の外にあり、このディレクトリからは決まらない |
| **前の版のモデルが重ね合わせた全体に残ること** | 決まりのとおり（前の版のファイルは直さない）。次の回は `モデルのファイル` の一覧だけを使う |

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う（`target` は `git` が要る）。
"""

from __future__ import annotations

import argparse
import importlib.util
import os
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


versions = _load("merge_versions", "merge-versions.py")
frozen = _load("check_frozen", "check-frozen.py")

# ---- `references/tree.md` の「形式検査のモデル」の写し（`README.md` の記録の項目）
ITEMS = ("対象", "検査器", "構成の大きさ", "結果", "陽性対照", "置いた前提", "前回のモデル", "モデルのファイル", "残した回")
RESULTS = ("反例なし", "反例あり")
PREVIOUS = ("無かった", "直さず使った", "直して使った", "組み直した")
README = "README.md"
NAME = re.compile(r"[a-z0-9-]+")
FILE = re.compile(r"`([^`]+)`")


class Unjudged(Exception):
    """判定していない（終了コード 2）。"""


def target(repo: Path) -> tuple[int, list[str]]:
    try:
        return _target(repo)
    except frozen.Unjudged as e:  # git を起動できない
        return 2, [str(e)]


def _target(repo: Path) -> tuple[int, list[str]]:
    top = frozen.git(repo, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or not top.stdout.strip():
        return 2, [f"{repo}: git の作業ツリーでない。リリースのタグを確かめられないので判定していない"]
    root = Path(top.stdout.strip())
    problems: list[str] = []
    docs = root / frozen.DOCS
    found = versions.find_versions(docs, problems) if docs.is_dir() else []
    if problems:
        return 2, problems + ["版の決まりに反する（references/versions.md）。判定していない"]
    if not found:
        return 2, [f"{docs}: 版（v<n>）が 1 つも無い。判定していない"]
    number = found[-1][0]
    shallow = frozen.git(root, "rev-parse", "--is-shallow-repository")
    if shallow.returncode != 0 or shallow.stdout.strip() == "true":
        return 2, ["浅い clone である（か確かめられない）。リリースのタグが見えないので判定していない"]
    remotes = frozen.git(root, "remote")
    if remotes.returncode != 0:
        return 2, [f"リモートを読めない: {remotes.stderr.strip()}。判定していない"]
    listed = frozen.git(root, "tag", "--list")
    if listed.returncode != 0:
        return 2, [f"タグを読めない: {listed.stderr.strip()}。判定していない"]
    names = listed.stdout.split()
    for remote in remotes.stdout.split():
        asked = subprocess.run(["git", "-C", str(root), "ls-remote", "--tags", remote], capture_output=True, text=True,
                               env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        if asked.returncode != 0:
            return 2, [f"リモート {remote} のタグを読めない（git ls-remote --tags: {asked.stderr.strip()}）。"
                       "取っていないタグを「リリースしていない」と読まないため判定していない"]
        names += remote_tags(asked.stdout)
    released = {n for n, _ in frozen.releases(names)}
    where = f"{frozen.DOCS}/v{number}/{versions.FORMAL_DIR}"
    if number in released:
        return 3, [f"作業中の版 v{number} はリリース済み（release-v{number}）。{where} には書かない",
                   f"次の版（{frozen.DOCS}/v{number + 1}/）を作ってから呼び直す（references/versions.md）"]
    saved = where if number == 1 else f"build/merged/{versions.FORMAL_DIR}（merge-versions.py docs build/merged が作る）"
    return 0, [f"版: v{number}", f"書く場所: {where}<対象>/", f"保存したモデルを探す場所: {saved}"]


def remote_tags(output: str) -> list[str]:
    """`git ls-remote --tags` の出力（`<sha>\\trefs/tags/<名前>`、注釈つきタグは `^{}` の行も）からタグの名前を取る。"""
    names = []
    for line in output.splitlines():
        ref = line.partition("\t")[2]
        if ref.startswith("refs/tags/"):
            names.append(ref[len("refs/tags/"):].removesuffix("^{}"))
    return names


def one_of(value: str, allowed: tuple[str, ...]) -> bool:
    """値そのものか、値の直後に `（…）` の要約を 1 つだけ続けた形か（`反例あり（2 重の取り消し）`）。

    要約は `（` で始まり、それと対応する `）` で終わる（中の入れ子は構わない）。閉じた後ろに続けた語・閉じていない形・空の要約は通さない。
    """
    for a in allowed:
        if value == a:
            return True
        summary = value[len(a):] if value.startswith(a) else ""
        if len(summary) > 2 and summary[0] == "（" and closes_at_end(summary):
            return True
    return False


def closes_at_end(summary: str) -> bool:
    """`（` で始まる文字列の最初の `（` と対応する `）` が、ちょうど末尾にあるか。"""
    depth = 0
    for i, ch in enumerate(summary):
        depth += {"（": 1, "）": -1}.get(ch, 0)
        if depth == 0:
            return i == len(summary) - 1
    return False


def read_records(readme: Path) -> tuple[dict[str, str], list[str]]:
    try:
        text = readme.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise Unjudged(f"{readme}: 無い")
    except (OSError, UnicodeDecodeError) as e:
        raise Unjudged(f"{readme}: 読めない（{e}）")
    records: dict[str, str] = {}
    problems: list[str] = []
    for line in text.splitlines():
        row = line.strip()
        if not (row.startswith("|") and row.endswith("|") and len(row) > 1):
            continue
        item, _, value = row[1:-1].partition("|")
        item, value = item.strip(), value.strip()
        if item not in ITEMS:
            continue
        if item in records:
            problems.append(f"{readme}: 項目「{item}」が 2 行ある")
            continue
        records[item] = value
    return records, problems


def check(directory: Path) -> tuple[int, list[str]]:
    if not directory.is_dir():
        return 2, [f"{directory}: ディレクトリでない。判定していない"]
    problems: list[str] = []
    resolved = directory.resolve()
    if f"{resolved.parent.parent.name}/{resolved.parent.name}/" != versions.FORMAL_DIR:
        problems.append(f"{directory}: 置き場所が spec/formal/<対象>/ でない")
    if not NAME.fullmatch(resolved.name):
        problems.append(f"{directory}: 対象の名前「{resolved.name}」が英小文字・数字・ハイフンだけでない")
    try:
        records, found = read_records(directory / README)
    except Unjudged as e:
        return 2, [f"{e}。判定していない"]
    problems += found
    for item in ITEMS:
        if item not in records:
            problems.append(f"{README}: 項目「{item}」の行が無い")
        elif not records[item]:
            problems.append(f"{README}: 項目「{item}」の記録が空")
    result = records.get("結果", "")
    if result and not one_of(result, RESULTS):
        problems.append(f"{README}: 結果が {'／'.join(RESULTS)} のどちらでもない（続けてよいのは「（」で始まる要約だけ。判定できなかった対象は残さない）: {result!r}")
    previous = records.get("前回のモデル", "")
    if previous and not one_of(previous, PREVIOUS):
        problems.append(f"{README}: 前回のモデルが {'／'.join(PREVIOUS)} のどれでもない（続けてよいのは「（」で始まる要約だけ）: {previous!r}")
    listed = FILE.findall(records.get("モデルのファイル", ""))
    if records.get("モデルのファイル") and not listed:
        problems.append(f"{README}: モデルのファイルにバッククォートで囲んだ名前が 1 つも無い")
    for name in listed:
        path = directory / name
        if "/" in name or name in (README, ".", ".."):
            problems.append(f"{README}: モデルのファイル「{name}」はこのディレクトリのファイルの名前でない")
        elif path.is_symlink() or not path.is_file():
            problems.append(f"{README}: モデルのファイル「{name}」がこのディレクトリの通常のファイルとして無い")
    for entry in sorted(p.name for p in directory.iterdir()):
        if entry != README and entry not in listed:
            problems.append(f"{directory}/{entry}: モデルのファイルの一覧に無い（検査器の作業ファイル・出力・前の残りは残さない）")
    if problems:
        return 1, problems
    return 0, [f"{directory}: 形どおり（モデルのファイル {len(listed)} 件）"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command")
    t = sub.add_parser("target")
    t.add_argument("--repo", default=".", type=Path)
    c = sub.add_parser("check")
    c.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    if args.command == "target":
        code, lines = target(args.repo)
    elif args.command == "check":
        code, lines = check(args.directory)
    else:
        parser.print_usage(sys.stderr)
        return 2
    for line in lines:
        print(line, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）。トレースバックの 1（違反）に化けさせない（#286）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
