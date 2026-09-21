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

## PR #133 の「870 件」との食い違い（#137 で特定した）

**主因は母集団の違いである。** **PR #133 が数えたのは main-chain のレコードだけで、
このスクリプトはサブエージェントのトランスクリプト（`isSidechain: true`）も数えている。**
**#133 がどの手段で落としたかは分からない**（下の「守らない」を正とする）——
**言えるのは「落ちていたのは sidechain の側である」までである。**

2026-09-21 に `~/.claude/projects`（6,003 ファイル）で数え直すと、
`timestamp < 2026-09-20T04:00Z` で全件 **1,386**、**`isSidechain` を除くと 872**、
**main-chain を時刻順に先頭 870 件まで取ると最新が `2026-09-20T03:49:33`** で、
**PR #133 のマージ（`2026-09-20T04:17:01Z`）の直前にあたる。**

**件数の一致だけでは偶然と区別できないので、内訳で判別した。** PR #133 が本文に
載せた理由節の表（件数と、その理由節が出た版の数）を同じ 870 件で数え直すと、
**5 行すべてが件数も版数も完全に一致する**（324/22・167/7・138/16・21/6・10/7）。
**陰性対照——同じ時刻カット（`< 2026-09-20T04:00Z`、全件 1,386）で数えると
同じ 5 行が 553/23・178/7・232/16・32/7・16/7 になり、どれも一致しない。**
**版の種類が 31 種（2.1.226 〜 2.1.278）である点は一致するが、
これは全件でも 31 種なので判別力を持たない**——根拠に数えない。

**陰性対照の母集団は、上の全件と同じカットである（必ず突き合わせること）。**
一度ここに **551/23** と書いていたが、それは**別のカット**——
**main-chain 870 件目の時刻（`03:49:33.205Z`）までで切った 1,384 件**——の値で、
**docstring が名指ししている `< 04:00Z`（1,386 件）からは再現しない。**
**残る 4 行はどちらのカットでも同じ**なので、**1 行だけが黙って別の母集団から来ていた。**
**#137 が直そうとしている食い違いと同じ形**なので、ここに記録して残す。

**870 を当て直すには `--json` を使う。** **標準出力の内訳は時刻で切っていない**
（走査した置き場所の全期間を数える）ので、**そこに 870 は出てこない**——
**日々増えるから、出るはずもない。** `--json` の各件が `sidechain` と `timestamp` を
持つので、**「main-chain だけ」「時刻順に先頭 870 件」は書き出しの側で当て直せる。**

**どちらも誤りではない。別の母集団を数えている。** 870 は **main-chain のみ**
（#123 が 40 件を無作為抽出したのもこの母集団である）、このスクリプトの既定は
**サブエージェントを含む全件**。**既定は変えない**——ガードは**サブエージェントの
コマンドにも発火する**ので、「ガードが何回発火したか」を数えるなら落としてはならないし、
**#122 の OS 比較もこの定義で取っている。**

**残差は特定できなかった。** PR #133 の「理由節は**パスを伏せてなお 106 通り、
うち 62 通りは 1 件**」は、上の 870 件に対して **108 / 67** までしか近づかない
（現行の `reason_clause` は `". "` で切るので 134 / 97。**`"."` 単独で切ると 108 / 67**）。
**バッククォート・引用符・数字の正規化と末尾記号の除去の 4 次元 16 通り、パス正規表現の
4 変種、母集団サイズ 700〜954 の全域**を当てたが、**(106, 62) になる組み合わせは無かった。**
**PR #133 の測定コードは残っていない**ので、**これ以上は復元できない。**

**このスクリプトが保証するのは「macOS と Linux を同じ式で数えること」だけである。**

**包みは剥がす。** ファイル編集ツールの拒否は `<tool_use_error>` で包まれて届くので、
剥がさないと**メッセージ形が 1 つ丸ごと母集団から落ちる**（#112 でここが 2 度壊れた）。

## 何を守り、何を守らないか

守る:

- **二重計上**——拒否レコードだけを数え、引用は数えない（上記）。
- **包みの取りこぼし**——`<tool_use_error>` を剥がしてから接頭辞を見る。
- **版と環境の取り違え**——各件に `version` と `cwd` を添える。`cwd` は OS の代理変数
  （`/Users` は macOS、`/home` や `/root` は Linux、`X:\` は Windows）。
- **理由節の正規化**——パスを伏せる。伏せないと件数が入力の多様性を映すだけになる。
- **母集団の混ざり**——`--cwd-prefix` を渡すと `cwd` がその接頭辞で始まる件だけを数える。
  **macOS 側は実作業の記録と同じ置き場所に probe の記録が混ざる**ので、これが無いと
  「probe の結果」と「日々の作業の履歴」を比べることになる。
- **main と sidechain の取り違え**——各件に `sidechain` を添え、**内訳を必ず出力する**。
  **これが無いと、同じ置き場所を数えた 2 つの値が食い違ったときに理由が分からない**
  （#137 でちょうどそれが起きた）。**0 件のときも出す**——**0 件はいちばん怪しい場合**
  （収集が届いていない可能性と区別がつかない）なので、**そこだけ内訳が無いのは逆である。**

守らない:

- **ガードが発火したのに記録されなかった拒否**——トランスクリプトに無いものは数えられない。
- **理由節の空間が数え上げられたかどうか**——#112 の未解決 1 のとおり、
  **増えなくなったことを確かめる手段が無い**。このスクリプトが出すのは
  **走査した範囲に出た集合**であって、境界ではない。
- **`cwd` が OS と一致すること**——代理変数であって、OS フィールドではない
  （レコードは `platform` / `os` を持たない。2026-09-20 に 5,898 ファイルで確認）。
  **両 OS に在る場所（`/var` `/tmp` `/opt` など）は `不明` を返す。**
  **判別できない場所で測ると、母集団が混ざっていることに気づけない。**
- **拒否の原因**——なぜその形が拒否されたかは、このスクリプトの範囲外である。
- **PR #133 が実際に `isSidechain` で絞ったこと**——**測定コードは残っていない。**
  上で示したのは**結果の一致**（main-chain だけが #133 の表を完全に再現し、全件は
  再現しない）であって、**意図ではない。**
  **同じ集合を作る別の絞り方が、実際に 1 つある**——**sidechain の拒否は
  main-chain の拒否と同じファイルに同居しない**（2026-09-21 の実測で、拒否を含む
  535 ファイルのうち **main のみ 251・sidechain のみ 284・混在 0**）。
  **だから「ファイル単位で絞った」でも、まったく同じ 870 件になる。**
  **言えるのは「落ちていたのは sidechain の側である」までで、
  「`isSidechain` フィールドで落とした」ではない。**
- **`isSidechain` が付いていない sidechain**——**フィールドが無いレコードは main として
  数える。** **付け忘れや、フィールドを持たない古い版の記録は判別できない。**
- **1 レコードに 2 件以上の拒否が入っている場合の 2 件目以降**——**最初の 1 件で打ち切る。**
  手元の 5,935 ファイルには**該当が 0 件**だが、**0 件なのは偶然であって、構造上の保証ではない**
  （`tool_result` を複数まとめた `user` レコードが来れば落ちる）。
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
    # **`/private` は macOS 固有**（`/tmp` の実体）。**`/var` は両方に在るので判別しない**
    # ——ここを macOS に倒すと、`/var/tmp` で回した Linux の測定が丸ごと macOS と
    # 札を付けられ、**「両 OS が一致した」が片方のデータから再現されてしまう。**
    if head in ("/Users", "/private"):
        return "macOS"
    if head in ("/home", "/root"):
        return "Linux"
    return f"不明 ({head})"


def collect(root, cwd_prefix=None):
    """トランスクリプトを走査して、拒否イベントを列挙する。

    `cwd_prefix` を渡すと、**`cwd` がその接頭辞で始まる件だけ**を数える。
    macOS 側は実作業のトランスクリプトと同じ置き場所に probe の記録が混ざるので、
    **probe だけを数えるのに要る**——混ぜると「probe の結果」と「日々の作業の履歴」を
    比べることになり、OS の差と母集団の差が交絡する。
    """
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
                if cwd_prefix and not (record.get("cwd") or "").startswith(cwd_prefix):
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
                        # **サブエージェントの記録か。** PR #133 の 870 件はこれを
                        # 落とした母集団だった（#137）。**フィールドが無ければ main**
                        # ——docstring の「守らない」を正とする。
                        "sidechain": bool(record.get("isSidechain")),
                        "timestamp": record.get("timestamp"),
                        "reason": reason_clause(text),
                        "has_rule_sentence": "Refusing to run it" in text,
                        "wrapped": body != text,
                    })
                    # **1 レコード 1 件で打ち切る。** 実測では 1 レコードに複数の
                    # 拒否が入った例が 0 件だが、**保証ではない**（docstring の
                    # 「守らない」を正とする）。
                    break
    return events, scanned


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--root",
        default=str(pathlib.Path.home() / ".claude" / "projects"),
        help="トランスクリプトの置き場所（既定: ~/.claude/projects）",
    )
    parser.add_argument("--json", metavar="PATH", help="収集結果を JSON で書き出す")
    parser.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="拒否が 0 件なら非ゼロ終了する（測定の失敗と『拒否されなかった』を人手に頼らず分ける）",
    )
    parser.add_argument(
        "--cwd-prefix",
        metavar="PREFIX",
        help="`cwd` がこの接頭辞で始まる件だけを数える（probe だけを取り出すのに使う）",
    )
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root)
    if not root.exists():
        print(f"置き場所が無い: {root}", file=sys.stderr)
        return 2

    events, scanned = collect(root, args.cwd_prefix)

    print(f"走査したファイル: {scanned}")
    print(f"拒否イベント: {len(events)}")

    # **内訳は必ず出す。** これが無いと、同じ置き場所を数えた 2 つの値が食い違ったときに
    # 理由が分からない（#137。PR #133 の 870 件は main-chain だけを数えていた）。
    # **0 件の枝より前に置く。** 後ろに置くと、**いちばん怪しい場合**——収集が
    # 届いていないかもしれない 0 件——だけ内訳が出ない。
    sidechain = sum(1 for e in events if e["sidechain"])
    print(f"\n=== 母集団の内訳 ===")
    print(f"  {len(events) - sidechain:>6}  main-chain")
    print(f"  {sidechain:>6}  sidechain（サブエージェント）")

    if not events:
        print("\n**0 件は「拒否されなかった」ではない。** 収集が届いていない可能性と"
              "区別がつかないので、レコードそのものが在るかを先に確かめること。")
        if args.json:
            pathlib.Path(args.json).write_text(json.dumps(events, ensure_ascii=False, indent=2))
        return 1 if args.fail_on_empty else 0

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
