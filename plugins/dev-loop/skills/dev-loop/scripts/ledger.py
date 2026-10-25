#!/usr/bin/env python3
r"""複数 Issue を回すときの台帳（依存グラフと状態）を、ファイルに持って読み書きする。

    python3 <このスキルの base ディレクトリ>/scripts/ledger.py init <名前>
    python3 <…>/ledger.py add  <名前> <番号> [--deps 12,13] [--title 題]
    python3 <…>/ledger.py set  <名前> <番号> 鍵=値 [鍵=値 …]
    python3 <…>/ledger.py show <名前>
    python3 <…>/ledger.py next <名前>
    python3 <…>/ledger.py path <名前>

**いつ使い、いつ書き換え、どう再開するかは `references/ledger.md` を正とする**
（このスキルと同じ場所にある）。ここにあるのは台帳の形と、このスクリプトが守るものである。

## なぜ在るのか（#390）

#389 の周では、依存のある 17 件を利用者不在で回すために、親が scratchpad に Markdown の台帳を置き、
状態が動くたびに書き換えて、30 分おきのタイマーがそれを読んで再開した。**台帳が親の文脈にしか無いと、
圧縮とセッションの終わりで消える**——「モデルは忘れる、リポジトリは忘れない」を複数 Issue の層にも当てる。
**scratchpad もセッションと一緒に消える**ので、置き場所はメインの作業ツリーの `.claude/plans/` にする。

## 台帳の場所

`<メインの作業ツリー>/.claude/plans/cruise-<名前>.json`。**メインの作業ツリーは
`git rev-parse --path-format=absolute --git-common-dir` の親から決める**——worktree の中から走らせても
同じファイルを指す（worktree の `.claude/plans/` は周を畳むと一緒に消える）。

## 台帳の形

```json
{"format": 1, "name": "<名前>", "issues": [
  {"number": 12, "title": "", "deps": [], "state": "todo",
   "pr": "", "branch": "", "worktree": "", "agent": "", "base": "", "note": "", "updated": "<UTC>"}
]}
```

**状態**（`set state=` に渡せるのはこれだけ）:

| 状態 | 意味 |
| --- | --- |
| `todo` | 未着手 |
| `impl` | 実装中（worktree がある） |
| `gate` | 関門（Verifier・`/code-review`）を回している |
| `pr` | PR を出し、マージを待っている |
| `merged` | マージ済み（**依存先として「済んだ」と読むのはこれだけ**） |
| `blocked` | 止まっている（人間の判断待ち・BLOCKED） |
| `dropped` | 取り下げ（依存先としては「済んでいない」と読む） |

**鍵**（`set` に渡せるのはこれだけ）: `state` `title` `deps` `pr` `branch` `worktree` `agent` `base` `note`。
`deps` はカンマ区切りの番号（空にすると依存なし）。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 通った（`next` で着手できるものが 0 件でも 0） |
| 2 | 引数が違う（名前の形・番号の形・`鍵=値` の形） |
| 3 | 操作を拒んだ——**台帳は 1 バイトも変えていない**（在る台帳への `init`・台帳に無い Issue・2 度目の `add`・決まった一覧に無い状態や鍵・依存の誤り） |
| 4 | 判定できなかった（git の外・台帳が無い・JSON が読めない・形が違う）。**「着手できるものなし」とは答えていない** |

## 何を守り、何を守らないか

守る:

- **台帳の場所は cwd に依らない**——メインの作業ツリーでも、worktree の中やそのサブディレクトリでも、同じ絶対パスを指す。
- **在る台帳を `init` で上書きしない。**
- **決まった一覧に無い状態・鍵を拒む**——綴りを誤った状態を書くと、`next` の判定から黙って外れる。
- **依存の誤り（台帳に無い依存先・自己依存・循環）を、`add` でも `set deps=` でも拒む**——循環があると、どの Issue も永遠に着手できない。
- **`next` は「未着手で、依存がすべてマージ済み」のものだけを出す**——依存が PR 中・止まっている・取り下げなら出さない。
- **読めない台帳を「空」と読まない**——壊れた JSON・形の違う台帳・無い台帳は 4 で止まり、書き換えない。
- **台帳の名前にパスの区切りと先頭のドットを許さない**——`.claude/plans/` の外に書かない。
- **拒んだ操作では台帳を変えない**——全体を検査してから一時ファイルに書き、`os.replace` で置き換える。

守らない:

- **複数のセッションからの同時書き込み**——`os.replace` なので半端なファイルは残らないが、後勝ちで片方の更新が消えうる。
  台帳を書くのは親 1 体である（`references/ledger.md`）。
- **状態の遷移の順序**——やり直し・取り下げで逆行が正当に起きるので縛らない。
- **台帳と実物（PR・worktree・ブランチ）が一致しているか**——書いてある値を出すだけで、`gh` も `git worktree` も見ない。
  再開する側が実物で確かめる（`references/ledger.md`）。
- **stacked な周**（依存が PR 中で、その上に積んで先に始める）——`next` には出さない（#392）。
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

STATES = ("todo", "impl", "gate", "pr", "merged", "blocked", "dropped")
KEYS = ("state", "title", "deps", "pr", "branch", "worktree", "agent", "base", "note")
TEXT_KEYS = ("title", "pr", "branch", "worktree", "agent", "base", "note")
DONE = "merged"
NAME_RE = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._-]*")
FORMAT = 1

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_REJECTED = 3
EXIT_UNKNOWN = 4


class Refused(Exception):
    """操作を拒んだ（台帳は変えていない）。"""


class Unknown(Exception):
    """判定できなかった。"""


class Usage(Exception):
    """引数が違う。"""


def main_worktree(cwd=None):
    """メインの作業ツリーの絶対パス。**worktree の中からでも同じ値を返す。**"""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise Unknown(f"git を起動できなかった: {exc}") from exc
    if proc.returncode != 0 or not proc.stdout.strip():
        raise Unknown("git のリポジトリの中ではない（場所を決められない）")
    return Path(proc.stdout.strip().splitlines()[0]).parent


def ledger_path(name, cwd=None):
    if not NAME_RE.fullmatch(name):
        raise Usage(f"台帳の名前が違う: {name!r}（英数字・`_`・`-`・`.` のみ。先頭のドットと区切りは不可）")
    return main_worktree(cwd) / ".claude" / "plans" / f"cruise-{name}.json"


def parse_number(text):
    if not re.fullmatch(r"[1-9][0-9]*", text.strip()):
        raise Usage(f"Issue 番号が違う: {text!r}")
    return int(text.strip())


def parse_deps(text):
    return [parse_number(t) for t in text.split(",") if t.strip()]


def load(path):
    if not path.is_file():
        raise Unknown(f"台帳が無い: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Unknown(f"台帳を読めない: {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("format") != FORMAT or not isinstance(data.get("issues"), list):
        raise Unknown(f"台帳の形が違う: {path}")
    for issue in data["issues"]:
        if (not isinstance(issue, dict) or not isinstance(issue.get("number"), int)
                or issue.get("state") not in STATES or not isinstance(issue.get("deps"), list)
                or not all(isinstance(d, int) for d in issue["deps"])):
            raise Unknown(f"台帳の形が違う: {path}: {issue!r}")
    return data


def validate(data):
    """台帳全体の整合。**書き込む前に必ず通す。**"""
    numbers = [i["number"] for i in data["issues"]]
    if len(numbers) != len(set(numbers)):
        raise Refused("同じ Issue が 2 度ある")
    known = set(numbers)
    graph = {}
    for issue in data["issues"]:
        if issue["state"] not in STATES:
            raise Refused(f"#{issue['number']}: 決まった一覧に無い状態 {issue['state']!r}（{', '.join(STATES)}）")
        for dep in issue["deps"]:
            if dep == issue["number"]:
                raise Refused(f"#{dep}: 自分自身に依存している")
            if dep not in known:
                raise Refused(f"#{issue['number']}: 依存先 #{dep} が台帳に無い（先に add する）")
        graph[issue["number"]] = issue["deps"]
    # 循環: 深さ優先で、いま辿っている途中の節点に戻ったら循環
    visiting, done = set(), set()

    def visit(n, path):
        if n in done:
            return
        if n in visiting:
            cycle = path[path.index(n):] + [n]
            raise Refused("依存が循環している: " + " → ".join(f"#{c}" for c in cycle))
        visiting.add(n)
        for d in graph[n]:
            visit(d, path + [n])
        visiting.discard(n)
        done.add(n)

    for n in graph:
        visit(n, [])


def save(path, data):
    validate(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find(data, number):
    for issue in data["issues"]:
        if issue["number"] == number:
            return issue
    raise Refused(f"#{number} は台帳に無い（先に add する）")


def ready(data):
    """着手できる Issue: 未着手で、依存がすべてマージ済み。"""
    state = {i["number"]: i["state"] for i in data["issues"]}
    return [i for i in data["issues"]
            if i["state"] == "todo" and all(state.get(d) == DONE for d in i["deps"])]


def cmd_init(path, name):
    if path.exists():
        raise Refused(f"台帳は既に在る（上書きしない）: {path}")
    save(path, {"format": FORMAT, "name": name, "issues": []})
    print(path)


def cmd_add(path, number, deps, title):
    data = load(path)
    if any(i["number"] == number for i in data["issues"]):
        raise Refused(f"#{number} は既に台帳に在る（変えるなら set）")
    entry = {"number": number, "title": title or "", "deps": deps, "state": "todo",
             **{k: "" for k in TEXT_KEYS if k != "title"}, "updated": now()}
    data["issues"].append(entry)
    save(path, data)
    print(f"#{number} を足した（依存: {', '.join(f'#{d}' for d in deps) or 'なし'}）")


def cmd_set(path, number, pairs):
    data = load(path)
    issue = find(data, number)
    changes = {}
    for pair in pairs:
        if "=" not in pair:
            raise Usage(f"`鍵=値` の形ではない: {pair!r}")
        key, value = pair.split("=", 1)
        if key not in KEYS:
            raise Refused(f"決まった一覧に無い鍵 {key!r}（{', '.join(KEYS)}）")
        changes[key] = parse_deps(value) if key == "deps" else value
    issue.update(changes)
    issue["updated"] = now()
    save(path, data)
    print(f"#{number}: " + ", ".join(f"{k}={v}" for k, v in changes.items()))


def cmd_show(path):
    data = load(path)
    print(f"台帳: {path}")
    print()
    print("| # | 状態 | 依存 | PR | ブランチ | worktree | 実装役 | 関門の起点 | メモ | 更新 |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for i in data["issues"]:
        deps = ", ".join(f"#{d}" for d in i["deps"]) or "-"
        cells = [f"#{i['number']} {i.get('title', '')}".strip(), i["state"], deps,
                 *(i.get(k, "") or "-" for k in ("pr", "branch", "worktree", "agent", "base", "note")),
                 i.get("updated", "")]
        print("| " + " | ".join(str(c) for c in cells) + " |")
    going = [i for i in data["issues"] if i["state"] in ("impl", "gate", "pr", "blocked")]
    can = ready(data)
    waiting = [i for i in data["issues"] if i["state"] == "todo" and i not in can]
    print()
    print("進行中（実物で確かめてから続ける）: " + (", ".join(f"#{i['number']}({i['state']})" for i in going) or "なし"))
    print("着手できる: " + (", ".join(f"#{i['number']}" for i in can) or "なし"))
    print("依存待ち: " + (", ".join(f"#{i['number']}" for i in waiting) or "なし"))
    if data["issues"] and all(i["state"] in (DONE, "dropped") for i in data["issues"]):
        print("すべてマージ済みか取り下げ")


def cmd_next(path):
    data = load(path)
    for i in ready(data):
        print(i["number"])


def build_parser():
    p = argparse.ArgumentParser(description="複数 Issue の台帳（依存グラフと状態）")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("init", "show", "next", "path"):
        sub.add_parser(name).add_argument("name")
    a = sub.add_parser("add")
    a.add_argument("name")
    a.add_argument("number")
    a.add_argument("--deps", default="")
    a.add_argument("--title", default="")
    s = sub.add_parser("set")
    s.add_argument("name")
    s.add_argument("number")
    s.add_argument("pairs", nargs="+")
    return p


def main(argv=None, cwd=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    try:
        path = ledger_path(args.name, cwd)
        if args.cmd == "init":
            cmd_init(path, args.name)
        elif args.cmd == "add":
            cmd_add(path, parse_number(args.number), parse_deps(args.deps), args.title)
        elif args.cmd == "set":
            cmd_set(path, parse_number(args.number), args.pairs)
        elif args.cmd == "show":
            cmd_show(path)
        elif args.cmd == "next":
            cmd_next(path)
        elif args.cmd == "path":
            print(path)
    except Usage as exc:
        print(f"引数が違う: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except Refused as exc:
        print(f"拒んだ（台帳は変えていない）: {exc}", file=sys.stderr)
        return EXIT_REJECTED
    except Unknown as exc:
        print(f"判定できなかった: {exc}", file=sys.stderr)
        return EXIT_UNKNOWN
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
