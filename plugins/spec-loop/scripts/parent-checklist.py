#!/usr/bin/env python3
"""登録した Issue から、依存の連鎖を cruise の親 Issue の書式（`- [ ] #N (depends: #M)`）で出す（#876）。

usage: python3 parent-checklist.py --index build/scaffold/issues/issues.json --issues <Issue の一覧の JSON>

**依存の連鎖は `scaffold.py` が `issues.json` に書く**——項目ごとの `depends`（依存先の機能の id。呼ぶ機能の Issue は、
呼ばれる機能の Issue に依存する）。Issue の番号は登録の後にしか無いので、このスクリプトが登録した Issue の一覧から番号を引いて、
dev-loop の cruise の親 Issue に貼れる行にする（書式の正は dev-loop の `skills/cruise/scripts/parent-issue.py` の docstring）。
入力の Issue の一覧は、登録した先のリポジトリから決まった 1 行で取る（**このスクリプトは `gh` を呼ばない**。`rebuild-scope.py` と同じ形）:

```bash
gh issue list --repo <開発のリポジトリ> --state all --limit 1000 --json number,title,state,body > issues.json
```

**項目の Issue は、本文が生成した本文（`issues.json` の `body` が指す、同じディレクトリのファイル）と同じ Issue である**——
登録は生成した本文をそのまま渡す決まりなので（`scaffold` の `SKILL.md` の手順 6）。比べるときは改行（`\\r\\n`）と前後の空白だけをならす。

出す行（項目ごとに 1 行。依存先が先に来る順）:

```markdown
- [ ] #12 F-001
- [ ] #13 F-002・F-003 (depends: #12)
- [x] #9 F-004
```

- 題は機能の id だけにする——`parent-issue.py` は題の `#番号` と依存の書き方らしい語を拒むので、機能の題を写さない（Issue の題は Issue を開けば見える）。
- **閉じた Issue は `[x]`**——`parent-issue.py` はそれを済んだものとして台帳に入れず、それへの依存は満たされたと読む。

終了コード:

- 0: 出した
- 1: 出していない——項目の本文と同じ本文の Issue が入力に無い（登録していない・本文を書き換えた・`--limit` の外）か 2 件以上ある。
  **一部だけの一覧を出さない**（抜けた項目への依存が黙って落ちる）。どの項目かを名指しする
- 2: 判定していない——引数の誤り・入力が読めない（`issues.json` の形が違う・本文のファイルが無い・`depends` が `issues.json` に無い機能を指す・
  依存が循環する・Issue の一覧の形が違う）

対象リポジトリで単体で動くよう、**標準ライブラリだけ**を使う（同じ `scripts/` の `rebuild-scope.py` の読み方を読み込む）。

**守ること**:

- **項目の Issue は、本文が生成した本文と同じものだけ**——題や機能の印で探すと、同じ機能の前の版の Issue や、書き換えた本文の Issue を当てる。
- **改行と前後の空白はならして比べる**——GitHub が改行を `\\r\\n` にし、末尾の改行を落としても、同じ本文と読む。
- **同じ本文の Issue が 2 件以上あれば 1**——どちらの番号を親に書くかを決めない（同じ機能を 2 度登録している）。
- **本文の Issue が無い項目があれば 1 で、一覧を出さない**——その項目への依存が黙って落ちた一覧を、親 Issue に貼らせない。
- **依存は機能の id から、その機能を持つ項目の番号に引く**——まとめた本文（`features`）の機能への依存も、まとめた Issue の番号になる。
- **`depends` が `issues.json` に無い機能を指せば 2**——依存の行を黙って落とさない。
- **依存が循環すれば 2**——`parent-issue.py` が拒む台帳を、貼るまで気づかせない。
- **依存先が先に来る順で出す**（同じ段は `issues.json` の順）。
- **閉じた Issue は `[x]` で出す。**
- **題は機能の id だけ**——機能の題を写すと、`parent-issue.py` が拒む文字（`#番号`・依存の語）を持ち込む。

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **入力が全部の Issue を含むか** | `--limit` を超えた Issue・取った後に登録した Issue は見えない——無ければ 1 で名指しするので、取り直す |
| **GitHub が本文の中の文字をならしたか**（改行と前後の空白のほか） | 比べる前にならすのは改行と前後の空白だけ。ほかを変えられたら「同じ本文の Issue が無い」で 1 |
| **登録した Issue が開いているかの正しさ** | `state` を写すだけ（`CLOSED` なら `[x]`）。閉じた理由は見ない |
| **親 Issue の `cruise:` の線と、ほかのチェックリストの行** | 出すのは依存の連鎖の行だけ。線は利用者が書き、`parent-issue.py show` で確かめる |
| **前の版の Issue への依存** | `depends` はこの版で本文を作った機能の間だけ（`scaffold.py` の docstring）。前の版で作った機能は親に載せない |
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rebuild = _load("rebuild_scope", "rebuild-scope.py")
CLOSED = "CLOSED"


class Bad(Exception):
    """判定していない（2）。"""


def normalize(body: str) -> str:
    return body.replace("\r\n", "\n").strip()


def read_index(path: Path) -> list[dict]:
    """`issues.json` の項目に、本文（`text`）と機能の id（`ids`）を足して返す。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Bad(f"{path}: 読めない（{exc.__class__.__name__}: {exc}）")
    if not isinstance(data, list):
        raise Bad(f"{path}: 項目の配列でない（scaffold.py が書いた issues.json を渡す）")
    entries = []
    for index, item in enumerate(data):
        ids = [item.get("feature")] if isinstance(item, dict) and "feature" in item else (
            item.get("features") if isinstance(item, dict) else None)
        depends = item.get("depends", []) if isinstance(item, dict) else None
        if not (isinstance(ids, list) and ids and all(isinstance(i, str) for i in ids) and isinstance(item.get("body"), str)
                and isinstance(depends, list) and all(isinstance(d, str) for d in depends)):
            raise Bad(f"{path}: {index} 番目が項目の形でない（feature か features・body・depends を持つ）")
        body = path.parent / item["body"]
        try:
            text = body.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise Bad(f"{body}: 本文が読めない（{exc.__class__.__name__}）——scaffold.py で作り直す")
        entries.append({"ids": ids, "depends": depends, "text": normalize(text), "body": item["body"]})
    return entries


def owners(entries: list[dict]) -> dict[str, int]:
    """{機能の id: その機能を持つ項目の番号}——まとめた項目（`features`）の機能は、どれもその項目を指す。"""
    return {fid: index for index, entry in enumerate(entries) for fid in entry["ids"]}


def order(entries: list[dict]) -> list[int]:
    """依存先が先に来る順の項目の番号（同じ段は入力の順）。"""
    owner = owners(entries)
    needs = []
    for entry in entries:
        missing = [d for d in entry["depends"] if d not in owner]
        if missing:
            raise Bad(f"{entry['body']}: depends の {'・'.join(missing)} が issues.json に無い——scaffold.py で作り直す")
        needs.append({owner[d] for d in entry["depends"]} - {owner[entry["ids"][0]]})
    done: list[int] = []
    while len(done) < len(entries):
        ready = [i for i in range(len(entries)) if i not in done and needs[i] <= set(done)]
        if not ready:
            looped = "・".join(entries[i]["body"] for i in range(len(entries)) if i not in done)
            raise Bad(f"依存が循環している（{looped}）——scaffold.py で作り直す")
        done.extend(ready)
    return done


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--issues", required=True)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    try:
        entries = read_index(Path(args.index))
        issues = rebuild.read_issues(Path(args.issues))
        ranked = order(entries)
    except (Bad, rebuild.Bad) as exc:
        print(f"{exc}。判定していない", file=sys.stderr)
        return 2
    found, problems = [], []
    for entry in entries:
        hits = [i for i in issues if normalize(i["body"]) == entry["text"]]
        label = "・".join(entry["ids"])
        if not hits:
            problems.append(f"{label}（{entry['body']}）: 本文が同じ Issue が入力に無い——登録していないか、本文を書き換えたか、"
                            "取り方の --limit・--state all の外")
        elif len(hits) > 1:
            problems.append(f"{label}（{entry['body']}）: 本文が同じ Issue が {len(hits)} 件ある（"
                            + "、".join(f"#{i['number']}" for i in hits) + "）——同じ機能を 2 度登録している。どちらを残すかを決めてから")
        found.append(hits[0] if len(hits) == 1 else None)
    if problems:
        for line in problems:
            print(line, file=sys.stderr)
        print("一覧を出していない（抜けた項目への依存が落ちるので、一部だけを出さない）", file=sys.stderr)
        return 1
    owner = owners(entries)
    for index in ranked:
        entry, issue = entries[index], found[index]
        mark = "x" if (issue.get("state") or "").upper() == CLOSED else " "
        targets = sorted({found[owner[d]]["number"] for d in entry["depends"] if owner[d] != index})
        depends = f" (depends: {', '.join(f'#{n}' for n in targets)})" if targets else ""
        print(f"- [{mark}] #{issue['number']} {'・'.join(entry['ids'])}{depends}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
