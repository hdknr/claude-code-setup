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
- **`陽性対照のファイル`（任意。#1044）**: 行があれば `モデルのファイル` と同じ形で見る。**行が無くても違反にしない**——前から残したモデルは持たない
  （`check-formal-rerun.py` は、行が無い対象を「判定できなかった」にする）。
- **`図の対応のファイル`・`状態遷移図のファイル`（任意。#1177）**: 同じく、行があれば同じ形で見て、行が無くても違反にしない——前から残したモデルは持たない
  （`formal-statechart.py` は対応が無い対象を描かない）。
- **`実装の対応`・`対応を確かめたコミット`（任意。#1178）**: 2 行ともそろって在るか、そろって無い（無いのは前から残したモデル）。
  `実装の対応` は `未実装` か、`` `<行為>` → `<ファイル>::<関数>` `` を `、` で区切った並び（行為は 2 回書かない。本体のモデル（`モデルのファイル` の `.tla` のうち陽性対照でないもの）が、注釈（`(* … *)`・`\\*`）を除いた本文の行頭から `<行為> ==` で定義していること。
  `.tla` が無い対象（Alloy など）は形だけを見る。本体の `.cfg` が（注釈の外で）名指す名前（`Init`・`Next`・性質）は行為として挙げない。ファイルは正規の相対パス（`./`・`..`・`//`・絶対パスは違反））。`対応を確かめたコミット` は `未実装` か 7〜40 桁の小文字の 16 進で、**`未実装` は 2 行で食い違わない**。
  対応のファイル・関数が在るか、コミットが在るかは見ない（正本と実装のリポジトリが別のことがある——dev-loop の `formal-sync.py` が実装のリポジトリで読む）。
- **ディレクトリの中身は、`README.md` と `モデルのファイル`・`陽性対照のファイル`・`図の対応のファイル`・`状態遷移図のファイル` の一覧だけ**——TLC の `states/`・Alloy の `<名前>/`・出力を落としたファイル・前に残したファイルが在れば違反。

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
| 記録の項目が欠けた・空・2 行あるなら違反にする（`陽性対照のファイル`・`図の対応のファイル`・`状態遷移図のファイル` は欠けてよい——空・2 行は違反） | 次の回が前提や陽性対照を確かめ直せない |
| `陽性対照のファイル` の一覧のファイルが無ければ違反にし、一覧のファイルは残ってよいとする | 走らせ直し（`check-formal-rerun.py`）が陽性対照を読めない・陽性対照を残すと違反になる |
| `図の対応のファイル`・`状態遷移図のファイル` の一覧のファイルが無ければ違反にし、一覧のファイルは残ってよいとする（#1177） | 図（`formal-statechart.py`）が対応を読めない・質問から指す図が無い・対応と図を残すと違反になる |
| `結果`・`前回のモデル` は値そのものか、値に `（…）` の要約を 1 つだけ続けた形（閉じた後ろに何も無い）だけを通す | `反例なしかは判定できなかった`・`反例なし（N=3）かは判定できなかった` のような、走らせていないモデルが残る |
| 置き場所と名前の形を見る | 次の回が同じ名前で探せない |
| `実装の対応`・`対応を確かめたコミット` の片方だけ・`未実装` の食い違い・対応の形の違い・本体が定義しない行為・SHA でないコミットを違反にする（2 行とも無いのは通す。#1178） | dev-loop の周が触れたファイルからモデルを引けない・確かめていないのにコミットだけ進んだ形が残る |
| `SPECIFICATION` が公平性の外で直に使う定義（`Init`・`Next`）を行為として挙げたら違反にする（#1178 の 2 パス目） | `SPECIFICATION Spec` 形の設定で `Next`・`Init` を対応に挙げて書き直し、検査を弱める |
| 行為の定義と設定が名指す名前は、注釈（`(* … *)`・`\\*`）を除いてから読む（#1178 の 2 パス目） | 注釈の中だけの定義を本体が定義する行為として通す・設定の注釈に書いた名前で正しい記録を落とす |

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **リモートにも押していない `release-v<n>`**（他の人の手元にだけあるタグ） | 訊く先に無いものは見えない。タグは付けたら押す運用で守る |
| **モデルの中身が仕様に合っているか・検査器が本当に走らせたものか** | 判定役の仕事で、報告から写すときにスキルが守る（`cp` で写す） |
| **記録の値が正しいか**（陽性対照が本当に反例を出したか・前提が全部か） | 文面の真偽は機械で決まらない |
| **`実装の対応` のファイル・関数が在るか、`対応を確かめたコミット` が在るか・本当に確かめたか** | 正本と実装のリポジトリが別のことがあり、このディレクトリからは決まらない（dev-loop の `formal-sync.py` が実装のリポジトリで読む） |
| **`残した回` が記録の表の行を指しているか** | 記録の表は版ごとに `docs/` の外にあり、このディレクトリからは決まらない |
| **前の版のモデルが重ね合わせた全体に残ること** | 決まりのとおり（前の版のファイルは直さない）。次の回は `モデルのファイル` の一覧だけを使う |

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う（`target` は `git` が要る）。
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import posixpath
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
ITEMS = ("対象", "検査器", "構成の大きさ", "結果", "陽性対照", "置いた前提", "前回のモデル", "モデルのファイル", "陽性対照のファイル", "図の対応のファイル", "状態遷移図のファイル", "実装の対応", "対応を確かめたコミット", "残した回")
# 行が無くてもよい項目（#1044。前から残したモデルは持たない——`check-formal-rerun.py` は無ければ判定できなかったにする。
# 図の対応と状態遷移図（#1177）も前から残したモデルは持たない——`formal-statechart.py` は対応が無ければ描かない）
OPTIONAL = ("陽性対照のファイル", "図の対応のファイル", "状態遷移図のファイル", "実装の対応", "対応を確かめたコミット")
# 実装との対応（#1178）——2 行はそろって在るか、そろって無い。実装の前は両方 `未実装`
SYNC = ("実装の対応", "対応を確かめたコミット")
UNIMPLEMENTED = "未実装"
# `実装の対応` の 1 項: `<行為>` → `<ファイル>::<関数>`。項は `、` で区切る
MAPPING_ENTRY = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`\s*→\s*`([^`:\s]+)::([^`\s]+)`")
COMMIT = re.compile(r"[0-9a-f]{7,40}")
# 一覧のファイルを持つ項目（ディレクトリに在ってよいのは `README.md` とこれらの一覧のファイルだけ）
LISTS = ("モデルのファイル", "陽性対照のファイル", "図の対応のファイル", "状態遷移図のファイル")
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
            if item not in OPTIONAL:
                problems.append(f"{README}: 項目「{item}」の行が無い")
        elif not records[item]:
            problems.append(f"{README}: 項目「{item}」の記録が空")
    result = records.get("結果", "")
    if result and not one_of(result, RESULTS):
        problems.append(f"{README}: 結果が {'／'.join(RESULTS)} のどちらでもない（続けてよいのは「（」で始まる要約だけ。判定できなかった対象は残さない）: {result!r}")
    previous = records.get("前回のモデル", "")
    if previous and not one_of(previous, PREVIOUS):
        problems.append(f"{README}: 前回のモデルが {'／'.join(PREVIOUS)} のどれでもない（続けてよいのは「（」で始まる要約だけ）: {previous!r}")
    listed: list[str] = []
    counts = []
    for item in LISTS:
        names = FILE.findall(records.get(item, ""))
        if records.get(item) and not names:
            problems.append(f"{README}: {item}にバッククォートで囲んだ名前が 1 つも無い")
        for name in names:
            path = directory / name
            if "/" in name or name in (README, ".", ".."):
                problems.append(f"{README}: {item}「{name}」はこのディレクトリのファイルの名前でない")
            elif path.is_symlink() or not path.is_file():
                problems.append(f"{README}: {item}「{name}」がこのディレクトリの通常のファイルとして無い")
        listed += names
        counts.append(f"{item} {len(names)} 件")
    for entry in sorted(p.name for p in directory.iterdir()):
        if entry != README and entry not in listed:
            problems.append(f"{directory}/{entry}: モデルのファイルの一覧に無い（陽性対照・図の対応・状態遷移図のファイルの一覧にも無い。検査器の作業ファイル・出力・前の残りは残さない）")
    problems += check_sync(directory, records)
    if problems:
        return 1, problems
    return 0, [f"{directory}: 形どおり（{'・'.join(counts)}）"]


def parse_mapping(value: str) -> list[tuple[str, str, str]] | None:
    """`実装の対応` の値を (行為, ファイル, 関数) の並びにする。`未実装` は空の並び。形が違えば None。

    形: `` `<行為>` → `<ファイル>::<関数>` `` を `、` で区切って並べる（ファイルは製品のリポジトリの根からのパス）。
    dev-loop の `formal-sync.py` もこの関数で読む（写さない）。
    """
    value = value.strip()
    if value == UNIMPLEMENTED:
        return []
    entries = []
    for part in value.split("、"):
        m = MAPPING_ENTRY.fullmatch(part.strip())
        if not m or not normal_path(m.group(2)):
            return None
        entries.append((m.group(1), m.group(2), m.group(3)))
    return entries or None


def normal_path(path: str) -> bool:
    """リポジトリの根からの正規の相対パスか（`./`・`..`・`//`・絶対パス・末尾の `/` は通さない——`git diff --name-only` の名前と文字列で突き合わせるため。#1178 の 1 パス目）。"""
    return not path.startswith("/") and "\\" not in path and posixpath.normpath(path) == path and not path.startswith("..")


def strip_comments(text: str) -> str:
    """TLA+ の注釈（入れ子の `(* … *)` と行の `\\*` から行末まで）を除く。文字列 `"…"` の中は除かない。改行は残す（行の区切りを変えない）。

    `.cfg` も同じ注釈の書き方なので、これで読む。dev-loop の `formal-sync.py` もこの関数で読む（写さない）。
    注釈の中の定義・名前を、TLC と同じく無いものとして読むため（#1178 の 1・2 パス目の指摘）。
    """
    out: list[str] = []
    i, depth, quoted = 0, 0, False
    while i < len(text):
        ch, two = text[i], text[i:i + 2]
        if depth:
            if two == "(*":
                depth, i = depth + 1, i + 2
            elif two == "*)":
                depth, i = depth - 1, i + 2
            else:
                if ch == "\n":
                    out.append(ch)
                i += 1
        elif quoted:
            out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            quoted = ch != '"'
            i += 1
        elif two == "(*":
            depth, i = 1, i + 2
        elif two == "\\*":
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
        else:
            quoted = ch == '"'
            out.append(ch)
            i += 1
    return "".join(out)


def spec_references(body: str) -> set[str]:
    """`SPECIFICATION` の定義の本文が、公平性（`WF_…(…)`・`SF_…(…)` の括弧の中）の外で直に使う名前（`Init`・`Next` など）。

    `Spec == Init /\\ [][Next]_x /\\ WF_x(Inc)` なら `Init`・`Next`（と `x`）。これらは状態の始まりと次の状態の関係そのもので、
    行為として書き直すと検査を弱められる（#1178 の 2 パス目の反証）。公平性に挙げた行為は書き直してよい。dev-loop の `formal-sync.py` もこの関数で読む（写さない）。
    """
    out: list[str] = []
    i = 0
    while i < len(body):
        m = re.compile(r"[WS]F_[^(\s]*\s*\(").match(body, i)
        if m and (i == 0 or not (body[i - 1].isalnum() or body[i - 1] == "_")):
            depth, j = 1, m.end()
            while j < len(body) and depth:
                depth += {"(": 1, ")": -1}.get(body[j], 0)
                j += 1
            i = j
            continue
        out.append(body[i])
        i += 1
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", "".join(out)))


def definition_body(text: str, name: str) -> str | None:
    """注釈を除いた TLA+ の本文で、行頭の `<name> ==` の定義の本文（次に行頭から始まる行の前まで）。無ければ None。"""
    m = re.search(rf"^{re.escape(name)}\s*==(.*?)(?=^\S|\Z)", strip_comments(text), re.MULTILINE | re.DOTALL)
    return None if m is None else m.group(1)


def defines(text: str, action: str) -> bool:
    """TLA+ の本文が、注釈の外の行頭から `<行為> ==`（引数つき `<行為>(…) ==` も）で定義しているか。"""
    return re.search(rf"^(?:LOCAL\s+)?{re.escape(action)}\s*(\([^)]*\))?\s*==", strip_comments(text), re.MULTILINE) is not None


def check_sync(directory: Path, records: dict[str, str]) -> list[str]:
    """`実装の対応`・`対応を確かめたコミット`（#1178）の形。2 行とも無ければ何も言わない（前からのモデル）。"""
    present = [item for item in SYNC if item in records]
    if not present:
        return []
    if len(present) == 1:
        missing = next(item for item in SYNC if item not in records)
        return [f"{README}: 「{present[0]}」があるのに「{missing}」の行が無い（実装との対応の 2 行はそろえて書く）"]
    mapping_value, commit_value = records[SYNC[0]], records[SYNC[1]]
    if not mapping_value or not commit_value:
        return []  # 空は上の「記録が空」で出している
    problems: list[str] = []
    mapping = parse_mapping(mapping_value)
    if mapping is None:
        problems.append(f"{README}: 実装の対応が「{UNIMPLEMENTED}」でも "
                        f"`<行為>` → `<ファイル>::<関数>` を「、」で区切った形でもない: {mapping_value!r}")
    if (mapping_value == UNIMPLEMENTED) != (commit_value == UNIMPLEMENTED):
        problems.append(f"{README}: 実装の対応と対応を確かめたコミットの片方だけが「{UNIMPLEMENTED}」（実装の前は両方、対応を書いたら確かめたコミットも書く）")
    elif commit_value != UNIMPLEMENTED and not COMMIT.fullmatch(commit_value):
        problems.append(f"{README}: 対応を確かめたコミットが「{UNIMPLEMENTED}」でも 7〜40 桁の小文字の 16 進でもない: {commit_value!r}")
    if mapping:
        controls = FILE.findall(records.get("陽性対照のファイル", ""))
        bodies = [n for n in FILE.findall(records.get("モデルのファイル", "")) if n.endswith(".tla") and n not in controls]
        texts = []
        named = ""
        for name in FILE.findall(records.get("モデルのファイル", "")):
            if name.endswith(".cfg") and name not in controls:
                try:
                    named += strip_comments((directory / name).read_text(encoding="utf-8")) + "\n"
                except (OSError, UnicodeDecodeError):
                    pass
        for name in bodies:
            try:
                texts.append((directory / name).read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                pass  # 無い・読めないファイルは一覧の検査が出す
        # SPECIFICATION 形の設定では、Spec が直に使う定義（Init・Next）も行為でない（#1178 の 2 パス目の反証）
        spec_direct: set[str] = set()
        for spec_name in re.findall(r"\bSPECIFICATION\s+([A-Za-z_][A-Za-z0-9_]*)", named):
            for t in texts:
                body = definition_body(t, spec_name)
                if body is not None:
                    spec_direct |= spec_references(body)
        seen: set[str] = set()
        for action, _, _ in mapping:
            if action in seen:
                problems.append(f"{README}: 実装の対応に行為「{action}」が 2 回ある")
            seen.add(action)
            if texts and not any(defines(t, action) for t in texts):
                problems.append(f"{README}: 実装の対応の行為「{action}」を、モデルのファイルの本体（.tla）が定義していない")
            if re.search(rf"\b{re.escape(action)}\b", named):
                problems.append(f"{README}: 実装の対応の「{action}」は本体の設定（.cfg）が名指す定義（INIT・NEXT・性質など）——行為でない")
            elif action in spec_direct:
                problems.append(f"{README}: 実装の対応の「{action}」は設定が名指す SPECIFICATION が直に使う定義（Init・Next など。公平性の外）——行為でない")
    return problems


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
