#!/usr/bin/env python3
r"""worktree 隔離セッションのガードによる拒否を、トランスクリプトから収集する。

#122 の「他の OS で測る手段が無い」を埋めるために置いた。**同じ式で macOS と Linux の
両方を数える**ためのもので、片方だけ別の数え方をすると、OS の差と数え方の差が交絡する。

## 何を 1 件と数えるか

**`type == "user"` のレコードで、`is_error` が真の content ブロックの本文が、
`<tool_use_error>` の包みを剥がしたうえでガードの接頭辞で始まるもの**を 1 件と数える。

**アシスタントが拒否文を引用した行は数えない。** レコードの本文に接頭辞が現れたら
数える素朴な走査は、**拒否レコードと、それを引用したアシスタントの応答を二重に数える**。
2026-09-20 の手元のトランスクリプト（5,905 ファイル）で実測すると、
**素朴な走査が 1,534 件、この定義が 1,388 件**だった。

**定義を 1 つ横に振って確かめてある。** `toolUseResult` の側（`Error: ` を外し、
包みを剥がして接頭辞で始まるもの）で数えても **1,388 件**で一致した。
**一致は「正しい」の証明ではないが、少なくとも数える場所の選び方では動かない。**

**#122 の前半（PR #133）が挙げた 870 件とは一致しない。理由は特定できていない。**
リポジトリで絞っても（`claude-code-setup` は 267 件）、測定時点で切っても
（2026-09-20T04:00Z より前が 1,386 件）、`version` を持たない件を除いても（0 件）、
870 にはならなかった。**だから、この数と 870 を並べて増減を語ってはならない。**
**このスクリプトが保証するのは「macOS と Linux を同じ式で数えること」だけである。**

**包みは剥がす。** ファイル編集ツールの拒否は `<tool_use_error>` で包まれて届くので、
剥がさないと**メッセージ形が 1 つ丸ごと母集団から落ちる**（#112 でここが 2 度壊れた）。

## 何を守り、何を守らないか

守る:

- **二重計上**——拒否レコードだけを数え、引用は数えない（上記）。
- **包みの取りこぼし**——`<tool_use_error>` を剥がしてから接頭辞を見る。
- **版と環境の取り違え**——各件に `version` と `cwd` を添える。`cwd` は OS の代理変数
  （`/Users` は macOS、`/home` や `/root` は Linux、`X:\` は Windows）。
- **理由節の正規化**——パスを伏せる。伏せないと件数が入力の多様性を映すだけになる
  （#122 の前半で実測。正規化なしでは 464 通り、正規化後は 136 通り）。

守らない:

- **ガードが発火したのに記録されなかった拒否**——トランスクリプトに無いものは数えられない。
- **理由節の空間が数え上げられたかどうか**——#112 の未解決 1 のとおり、
  **増えなくなったことを確かめる手段が無い**。このスクリプトが出すのは
  **走査した範囲に出た集合**であって、境界ではない。
- **`cwd` が OS と一致すること**——代理変数であって、OS フィールドではない
  （レコードは `platform` / `os` を持たない。2026-09-20 に 5,898 ファイルで確認）。
- **拒否の原因**——なぜその形が拒否されたかは、このスクリプトの範囲外である。
"""

import argparse
import json
import pathlib
import re
import sys
from collections import Counter

GUARD_PREFIX = "This session is isolated in the worktree "
WRAPPER = re.compile(r"<tool_use_error>(.*?)</tool_use_error>", re.S)
# 絶対パス（POSIX / Windows）を伏せる。伏せないと件数が入力の多様性を映すだけになる。
PATH_POSIX = re.compile(r"/(?:[\w.@%+-]+/)*[\w.@%+-]+")
PATH_WIN = re.compile(r"[A-Za-z]:\\(?:[^\s\\]+\\)*[^\s\\]*")


def unwrap(text):
    """`<tool_use_error>` の包みを剥がす。包まれていなければそのまま返す。"""
    m = WRAPPER.search(text)
    return m.group(1).strip() if m else text


def error_blocks(record):
    """そのレコードが持つ「エラーとして届いた本文」を列挙する。"""
    message = record.get("message")
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict) or not block.get("is_error"):
            continue
        body = block.get("content")
        if isinstance(body, str):
            yield body
        elif isinstance(body, list):
            for part in body:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    yield part["text"]


def reason_clause(text):
    """`, but ` の直後の 1 文を理由節として取り出し、パスを伏せて返す。

    規則文（`Refusing to run it …`）を持たない形があるので、**位置ではなく
    `, but ` の直後**で切る。見つからなければ None を返す（数えない）。
    """
    marker = ", but "
    index = text.find(marker)
    if index < 0:
        return None
    rest = text[index + len(marker):]
    end = rest.find(". ")
    clause = rest if end < 0 else rest[:end]
    clause = PATH_WIN.sub("<PATH>", clause)
    clause = PATH_POSIX.sub("<PATH>", clause)
    return " ".join(clause.split())


def os_of(cwd):
    """`cwd` から OS を推定する。**代理変数であって OS フィールドではない。**"""
    if not cwd:
        return "(cwd なし)"
    if re.match(r"^[A-Za-z]:[\\/]", cwd):
        return "Windows"
    head = "/" + cwd.lstrip("/").split("/")[0]
    if head in ("/Users", "/private", "/var"):
        return "macOS"
    if head in ("/home", "/root"):
        return "Linux"
    return f"不明 ({head})"


def collect(root):
    """トランスクリプトを走査して、拒否イベントを列挙する。"""
    events = []
    scanned = 0
    for path in sorted(pathlib.Path(root).rglob("*.jsonl")):
        scanned += 1
        try:
            handle = path.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                if GUARD_PREFIX not in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("type") != "user":
                    continue
                for body in error_blocks(record):
                    text = unwrap(body)
                    if not text.startswith(GUARD_PREFIX):
                        continue
                    events.append({
                        "uuid": record.get("uuid"),
                        "version": record.get("version"),
                        "cwd": record.get("cwd"),
                        "os": os_of(record.get("cwd")),
                        "timestamp": record.get("timestamp"),
                        "reason": reason_clause(text),
                        "has_rule_sentence": "Refusing to run it" in text,
                        "wrapped": body != text,
                    })
                    break  # 1 レコード 1 件
    return events, scanned


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--root",
        default=str(pathlib.Path.home() / ".claude" / "projects"),
        help="トランスクリプトの置き場所（既定: ~/.claude/projects）",
    )
    parser.add_argument("--json", metavar="PATH", help="収集結果を JSON で書き出す")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root)
    if not root.exists():
        print(f"置き場所が無い: {root}", file=sys.stderr)
        return 2

    events, scanned = collect(root)

    print(f"走査したファイル: {scanned}")
    print(f"拒否イベント: {len(events)}")
    if not events:
        print("\n**0 件は「拒否されなかった」ではない。** 収集が届いていない可能性と"
              "区別がつかないので、レコードそのものが在るかを先に確かめること。")
        if args.json:
            pathlib.Path(args.json).write_text(json.dumps(events, ensure_ascii=False, indent=2))
        return 0

    for label, key in (("OS（cwd からの推定）", "os"), ("harness 版", "version")):
        counter = Counter(e[key] for e in events)
        print(f"\n=== {label}: {len(counter)} 種 ===")
        for value, count in counter.most_common(10):
            print(f"  {count:>6}  {value}")

    reasons = Counter(e["reason"] for e in events if e["reason"])
    unparsed = sum(1 for e in events if not e["reason"])
    print(f"\n=== 理由節（パスを伏せた）: {len(reasons)} 通り"
          f"／`, but ` が無く取れなかったもの {unparsed} 件 ===")
    for clause, count in reasons.most_common(8):
        print(f"  {count:>6}  {clause}")

    no_rule = sum(1 for e in events if not e["has_rule_sentence"])
    wrapped = sum(1 for e in events if e["wrapped"])
    print(f"\n規則文（`Refusing to run it`）を持たない件: {no_rule}")
    print(f"`<tool_use_error>` に包まれていた件: {wrapped}")

    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n書き出した: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
