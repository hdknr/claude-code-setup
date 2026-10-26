#!/usr/bin/env python3
r"""親 Issue の本文に並べた Issue と依存を取り出し、確かめた結果だけを台帳にする。

    python3 <このスキルの base ディレクトリ>/scripts/parent-issue.py show  <親 Issue>
    python3 <…>/parent-issue.py apply <親 Issue> --digest <show が出した指紋>

**いつ使い、利用者に何を確かめるかは `SKILL.md` を正とする**（このスクリプトと同じスキルの下にある）。
ここにあるのは親 Issue の書式と、このスクリプトが守るものである。

本文は `gh issue view <親> --json body -q .body` で取る（cwd のリポジトリ）。`--body-file` を渡せば、
そのファイルを本文として読む（テスト用）。台帳の読み書きは dev-loop の `scripts/ledger.py` に任せ、
子プロセスで呼ぶ——台帳の形・置き場所・状態は `ledger.py` の docstring を正とする。台帳の名前は `issue-<親>`。

## なぜ在るのか（#446）

オートクルーズ（#389）の起動は、回す Issue と依存を親セッションへ毎回文章で書き下していた。
一覧を親 Issue に置けば短いコマンドで起動できるが、**親 Issue の本文は信頼できない入力である**
（dev-loop の `references/untrusted-input.md`）。だから取り出しを 2 段に分ける——`show` が取り出した結果と
**指紋**を出し、利用者がそれを確かめてから `apply` が台帳にする。**`apply` は本文を取り直して指紋を比べる**ので、
確かめた後に本文が書き換えられたら台帳を作らない。

## 書式

```markdown
- [ ] #12
- [ ] #13 ログイン画面 (depends: #12)
- [ ] #14 (depends: #12, #13)
- [x] #11
```

- **チェックリストの行**（`-`・`*`・`+` のあとに `[ ]` か `[x]`）だけを読む。ほかの行は読まない。**コードフェンスの中も読まない。**
- 回す Issue の行は `#番号` で始める。番号の後ろの文は題として台帳に入れる。**`#番号` で始まらないチェックリストの行**
  （受入基準など）は台帳に入れず、`show` に**読み飛ばした行**として出す——親 Issue に受入基準が混ざっていてもよい。
- 依存は `(depends: #番号, #番号)` を 1 つだけ書く。
- **`[x]` の行は済んだもの**として台帳に入れず、それへの依存は満たされたと読む（「マージ済み」とは読まない）。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 通った（`show` は取り出した結果と指紋を出した。`apply` は台帳を作った） |
| 2 | 引数が違う |
| 3 | 拒んだ——**台帳は作っていない**（書式の誤り・回すものが 0 件・指紋の不一致・台帳が既に在る） |
| 4 | 判定できなかった（`gh` が失敗した・本文が読めない・`ledger.py` が失敗した・git の外）。**「回すものなし」とは答えていない** |

## 何を守り、何を守らないか

守る:

- **`#番号` で始まらないチェックリストの行は、`show` に読み飛ばした行として出す**——黙って飛ばすと、`# ` の書き忘れで
  回すはずの課題が台帳から落ちたことに、確かめる側が気づけない。
- **`(depends: …)` の中身が `#番号` のカンマ区切りでなければ拒む。**
- **依存の書き方らしい語（`depend`・`依存`）が `(depends: …)` の外にあれば拒む**——書き損じた依存を黙って落とさない。
- **コードフェンスの中のチェックリストは読まない**——書式の例を貼った本文で、例の Issue を回さない。
- **同じ番号が 2 行あれば拒む。**
- **一覧に無い依存先・自己依存・未チェックの間の循環を拒む**——どれも、その Issue が永遠に着手できない台帳になる。
- **`[x]` の行への依存は満たされたものとして外す**——依存先が済んでいるのに着手できない台帳にしない。
- **台帳には依存先が先に来る順で足す**——`ledger.py add` は台帳に無い依存先を拒む。
- **`apply` は本文を取り直し、指紋が `show` と同じときだけ台帳を作る**——確かめた後の書き換えを台帳に入れない。
- **台帳が既に在れば作り直さず、親 Issue にあって台帳に無い Issue を名指しする**——再開は台帳から行う。
- **`apply` の途中で `ledger.py` が失敗したら、この実行で作った台帳を消す**——半端な台帳を正として再開させない。

守らない:

- **一覧に無いが閉じている依存先**——`gh` で状態を引かない。済んだ依存先は `[x]` の行として書く。
- **台帳を作った後の親 Issue の変更**——台帳に足すのは `ledger.py add`（`apply` は名指しするだけ）。
- **親 Issue のチェックボックスの更新**——読むだけで、本文を書き換えない。
- **一覧の Issue が開いているか・在るか**——各周の手順 1（`gh issue view`）で見る。
- **本物の `gh` の出力の形**——テストは `--body-file` と偽の `gh` で当てる。
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_REJECTED = 3
EXIT_UNKNOWN = 4

LEDGER = Path(__file__).resolve().parents[2] / "dev-loop" / "scripts" / "ledger.py"
CHECK_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s*(.*)$")
ITEM_RE = re.compile(r"^#([0-9]+)(?![0-9A-Za-z_])(.*)$")
DEPS_RE = re.compile(r"\(depends:([^)]*)\)")
DEP_LIST_RE = re.compile(r"^#[0-9]+(\s*,\s*#[0-9]+)*$")
SUSPECT_RE = re.compile(r"depend|依存", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")


class Refused(Exception):
    """拒んだ（台帳は作っていない）。"""


class Unknown(Exception):
    """判定できなかった。"""


def parse(body):
    """本文から ([{"number", "deps", "title"}]（未チェックだけ・依存先が先）, 読み飛ばした行) を返す。"""
    items, skipped, done, in_fence = [], [], set(), False
    for lineno, line in enumerate(body.splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        m = CHECK_RE.match(line)
        if in_fence or not m:
            continue
        item = ITEM_RE.match(m.group(2).strip())
        if not item or int(item.group(1)) == 0:
            skipped.append(f"{lineno} 行目: {line.strip()}")
            continue
        number, rest = int(item.group(1)), item.group(2)
        found = DEPS_RE.findall(rest)
        if len(found) > 1:
            raise Refused(f"{lineno} 行目: (depends: …) が 2 つある")
        deps = []
        if found:
            text = found[0].strip()
            if not DEP_LIST_RE.match(text):
                raise Refused(f"{lineno} 行目: (depends: …) の中身が #番号 のカンマ区切りでない: {text}")
            deps = [int(d) for d in re.findall(r"[0-9]+", text)]
        outside = DEPS_RE.sub("", rest)
        if SUSPECT_RE.search(outside):
            raise Refused(f"{lineno} 行目: 依存の書き方らしい語が (depends: #番号) の外にある: {line.strip()}")
        if number in done or any(i["number"] == number for i in items):
            raise Refused(f"{lineno} 行目: #{number} が 2 行ある")
        if m.group(1) in "xX":
            done.add(number)
            continue
        items.append({"number": number, "deps": deps, "title": " ".join(outside.split())})
    if not items:
        raise Refused("未チェックの Issue が 0 件（回すものが無い）")
    listed = {i["number"] for i in items}
    for i in items:
        for d in i["deps"]:
            if d == i["number"]:
                raise Refused(f"#{d} が自分に依存している")
            if d not in listed and d not in done:
                raise Refused(f"#{i['number']} の依存先 #{d} が一覧に無い（済んでいるなら [x] の行で書く）")
        i["deps"] = [d for d in dict.fromkeys(i["deps"]) if d in listed]
    return order(items), skipped


def order(items):
    """依存先が先に来る順（同じ段では本文の順）。未チェックの間の循環は拒む。"""
    placed, out, rest = set(), [], list(items)
    while rest:
        ready = [i for i in rest if all(d in placed for d in i["deps"])]
        if not ready:
            raise Refused("依存が循環している: " + ", ".join(f"#{i['number']}" for i in rest))
        for i in ready:
            placed.add(i["number"])
            out.append(i)
        rest = [i for i in rest if i["number"] not in placed]
    return out


def digest(items):
    raw = json.dumps([[i["number"], i["deps"], i["title"]] for i in items], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def read_body(parent, body_file, cwd):
    if body_file:
        try:
            return Path(body_file).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise Unknown(f"本文を読めなかった: {exc}") from exc
    try:
        proc = subprocess.run(["gh", "issue", "view", str(parent), "--json", "body", "-q", ".body"],
                              cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise Unknown(f"gh を起動できなかった: {exc}") from exc
    if proc.returncode != 0:
        raise Unknown(f"gh issue view #{parent} が失敗した: {proc.stderr.strip()}")
    return proc.stdout


def ledger(ledger_script, cwd, *args):
    try:
        proc = subprocess.run([sys.executable, str(ledger_script), *args],
                              cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise Unknown(f"ledger.py を起動できなかった: {exc}") from exc
    return proc


def cmd_show(items, skipped):
    for i in items:
        deps = ", ".join(f"#{d}" for d in i["deps"]) or "-"
        print(f"#{i['number']}\t依存: {deps}\t{i['title']}")
    if skipped:
        print("読み飛ばした行（#番号 で始まらない）:")
        for line in skipped:
            print(f"  {line}")
    print(f"指紋: {digest(items)}")


def cmd_apply(items, parent, expected, ledger_script, cwd):
    if digest(items) != expected:
        raise Refused(f"指紋が違う（show の後に本文が変わったか、別の親 Issue）: {digest(items)} ≠ {expected}")
    name = f"issue-{parent}"
    proc = ledger(ledger_script, cwd, "path", name)
    if proc.returncode != 0:
        raise Unknown(f"台帳の場所を決められなかった: {proc.stderr.strip()}")
    path = Path(proc.stdout.strip())
    if path.exists():
        try:
            have = {i["number"] for i in json.loads(path.read_text(encoding="utf-8"))["issues"]}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise Unknown(f"既に在る台帳を読めなかった: {exc}") from exc
        missing = [f"#{i['number']}" for i in items if i["number"] not in have]
        note = f"親 Issue にあって台帳に無い: {', '.join(missing)}" if missing else "親 Issue の Issue はすべて台帳に在る"
        raise Refused(f"台帳が既に在る（再開は ledger.py show {name}）: {path}。{note}")
    proc = ledger(ledger_script, cwd, "init", name)
    if proc.returncode != 0:
        raise Unknown(f"ledger.py init が失敗した: {proc.stderr.strip()}")
    for i in items:
        args = ["add", name, str(i["number"]), "--deps", ",".join(map(str, i["deps"]))]
        if i["title"]:
            args += ["--title", i["title"]]
        proc = ledger(ledger_script, cwd, *args)
        if proc.returncode != 0:
            path.unlink(missing_ok=True)
            raise Unknown(f"ledger.py add #{i['number']} が失敗したので、作った台帳を消した: {proc.stderr.strip()}")
    print(f"台帳を作った: {path}（{len(items)} 件）")
    print(f"続きは: ledger.py show {name}")


def build_parser():
    p = argparse.ArgumentParser(description="親 Issue の一覧から台帳を作る")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("show", "apply"):
        s = sub.add_parser(name)
        s.add_argument("parent", type=int)
        s.add_argument("--body-file")
        if name == "apply":
            s.add_argument("--digest", required=True)
    return p


def main(argv=None, cwd=None, ledger_script=LEDGER):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    if args.parent <= 0:
        print("引数が違う: 親 Issue の番号は正の整数", file=sys.stderr)
        return EXIT_USAGE
    try:
        items, skipped = parse(read_body(args.parent, args.body_file, cwd))
        if args.cmd == "show":
            cmd_show(items, skipped)
        else:
            cmd_apply(items, args.parent, args.digest, ledger_script, cwd)
    except Refused as exc:
        print(f"拒んだ（台帳は作っていない）: {exc}", file=sys.stderr)
        return EXIT_REJECTED
    except Unknown as exc:
        print(f"判定できなかった: {exc}", file=sys.stderr)
        return EXIT_UNKNOWN
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
