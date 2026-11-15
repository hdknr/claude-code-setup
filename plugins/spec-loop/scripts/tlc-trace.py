#!/usr/bin/env python3
r"""TLC の反例の JSON（`-dumpTrace json`）と対応表から、spec-ir のトレースのケース（`trace`）を作る（#1020）。

    python3 <spec-loop の根>/scripts/tlc-trace.py <反例の JSON> <対応表の JSON>

**読むだけ**——標準出力にトレースのケースの `trace` の値（JSON 1 行）を出す。ファイルは書かない。
出した値の形（`formal`・`calls`・`steps`・`setup`・`outcomes`・`after`）は `references/spec-ir.md` の「トレースのケース」を正とし、
**形の検査はしない**——`scaffold.py` が中間表現を読むときに `check_trace` で当てる。

## なぜ在るのか（#1015・#1020）

Formal Checker が出した反例の実行順を、トレースのケースの `steps` へ手で書き写していた。
#1015 では、反例の状態の `pc` の差から段を決める変換を試したが、`pc` の変わらない遷移・引数の無い行為・単語でない `pc` の値を落とす。
TLC の `-dumpTrace json` は、行為ごとに名前（`name`）と引数（`parameters`・`context`）と前後の状態を出す——**段は行為の名前と引数だけで決め、状態は読まない**。

## 反例の JSON

TLC に `-dumpTrace json <ファイル>` を渡すと、違反したときだけ書く（違反が無ければ書かない）。形（TLA+ のプレリリース v1.8.0 の `tla2tools.jar`——`-h` の版 `2026.11.15.002146`——で確かめた）:

    {"counterexample": {"action": [[[1, {状態}], {"name": "Read", "context": {"w": "new"}, "parameters": ["w"], "location": {…}}, [2, {状態}]], …],
                        "state": [[1, {状態}], …]},
     "vars": [変数の名前, …]}

- **`-dumpTrace` を持たない TLC がある**——安定版の v1.7.4（TLC 2.19）は `Error: unrecognized option: -dumpTrace` で止まる。v1.8.0 のプレリリースと、`apalache.jar` に入っている TLC は持つ（#1015）。
  持たない TLC なら、このスクリプトは使えない（反例の出力から手で写す。`agents/formal-checker.md`）。
- **引数の無い行為には `context`・`parameters` が無い**。**`\E w \in W : …` を行為の中に書いたモデルは、行為の名前が `Next` になり引数を持たない**——
  呼び出しを決めるには、呼び出しを引数に取る名前つきの行為（`Read(w)`）で書く。
- **繰り返しのある反例**（活性の違反）は、最後の行為の後の状態が前の状態の番号に戻る（`Back to state`）。

## 対応表

反例に無いものは人が書く（#1015 の A4）——モデルの呼び出しと実装の入口・入力の対応、行為とトレースの段の名前の対応、期待（直した仕様の結果なので反例からは出ない）:

    {"formal": "version-write",
     "caller": "w",
     "calls": {"old": {"name": "old_writer", "operation": "write_row", "input": {"key": "k", "ver": 1}},
               "new": {"name": "new_writer", "operation": "write_row", "input": {"key": "k", "ver": 2}}},
     "actions": {"Read": "read", "Write": "write"},
     "skip": ["Done"],
     "rest": {"setup": […], "outcomes": […], "after": […]}}

| 鍵 | 書くもの |
| --- | --- |
| `formal` | 反例を出した形式検査の対象の名前（トレースのケースの `formal` にそのまま写す） |
| `caller` | 呼び出しを決める行為の引数の名前（行為の `parameters` の 1 つ）。全部の行為で同じ名前 |
| `calls` | 呼び出しの引数の値 → `{"name": <呼び出しの名前>, "operation": <入口>, "input": <入力>}`。値は文字列か整数で、鍵は文字列にした値（整数の `2` は `"2"`） |
| `actions` | 行為の名前 → 段の名前 |
| `skip` | （任意）段にしない行為の名前の配列（全員が終わった後の `Done` など）。`actions` と重ねない |
| `rest` | （任意）`setup`・`outcomes`・`after` だけを持つオブジェクト。トレースのケースにそのまま写す |

**出す `calls` は、対応表の `calls` の全部**（段に出ない呼び出しも出す——`scaffold.py` の `check_trace` が「どれも 1 回以上出る」で落とす）。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 作れた（標準出力に `trace` の値） |
| 1 | 反例を段の並びにできない——表に無い行為、呼び出しの引数の無い・ほかの引数もある行為、`calls` に無い呼び出し、繰り返しのある反例、段が 2 つより少ない |
| 2 | 引数が違う・読めない・JSON でない・反例の JSON か対応表の形が違う（状態の番号が続かないを含む） |

## 何を守り、何を守らないか

守る:

- **段は行為の名前で決め、状態（`pc`）の差から推さない**——反例の行為の並びの順に、`actions` で引いた段の名前を並べる。
- **呼び出しは行為の `context` の `caller` の値で決める**——`calls` の鍵で引いた `name` を段の呼び出しにする。
- **表に無い行為を黙って捨てない**——`actions` にも `skip` にも無い行為は 1。
- **`skip` に挙げた行為は段にしない**——呼び出しの引数が無くても止めない。
- **呼び出しの引数の無い行為を推して段にしない**——`parameters` か `context` に `caller` が無い行為（`skip` に無いもの）は 1。
- **呼び出しの引数のほかの引数がある行為を段にしない**——ほかの引数の値は `calls` の入力に写せないので、1。
- **`calls` に無い呼び出しの値を段にしない**——1。
- **呼び出しの値の型を混ぜない**——文字列と整数のほか（真偽・オブジェクト）は 1。真偽の `true` を `"True"` と引かない。
- **繰り返しのある反例を段にしない**——行為の後の状態の番号が前の状態の番号以下なら 1。
- **状態の番号が続かない反例を読まない**——初めの行為の前が 1 でない・行為の前の状態が前の行為の後の状態と違う・後が前の次でない（戻る形を除く）なら 2。
- **段が 2 つより少ない反例を 0 にしない**——初めの状態で違反した（行為が 0 個）反例を含め、1。
- **`rest` で `formal`・`calls`・`steps` を上書きしない**——`rest` に `setup`・`outcomes`・`after` のほかの鍵があれば 2。
- **呼び出しの名前が重なる表を読まない**——2 つの呼び出しが 1 つにまとまって出るので、2。名前は空でない文字列に限る（`true` と `1` を別の名前と読まない）。
- **形の違う行為を 1 にしない**——`name` が空でない文字列でない・`parameters` が文字列の配列でない・`parameters` と `context` の片方にだけ呼び出しの引数がある行為は、モデルの書き方ではなく JSON の形の違いなので 2。
- **`actions` と `skip` に同じ行為を書いた表を読まない**——どちらを採るかを決めないので、2。
- **ファイルを書かない**——出すのは標準出力だけ。

守らない:

- **出した値がトレースのケースの形に合うか**（名前の形・`calls` の入力が入口の項目と合うか・段の数）——`scaffold.py` の `check_trace` に任せる。
- **段の順の正しさ**——反例の行為の順をそのまま写す。モデルと実装の段の対応（`actions`）が誤っていても見えない。
  #1015 の A4 のとおり、読むと書くを 1 つの操作の直前に続けて呼ぶ実装では、生成した Red テストは読む段の位置の誤りを判別しない。
- **呼び出しごとに引数の名前が違うモデル**（`Read(w)`・`Approve(a)`）——`caller` は 1 つ。モデルの引数の名前を揃える。
- **`skip` に挙げた行為が状態を変えるか**——挙げた行為は順に入らない（環境の行為を飛ばすと、その順は落ちる）。
- **整数と文字列の同じ表記の値**（`2` と `"2"`）を同じモデルで使うとき——`calls` の鍵は同じ `"2"` になる。
- **活性の違反のうち、前の状態へ戻らずに終わるもの**（公平性なしで止まって終わる反例など）——JSON の形は不変条件の違反と同じで、ここでは見分けられない（0 で `steps` を出す）。
  **使うのは不変条件の違反（TLC の `Invariant … is violated`。終了コード 12）の反例だけにする**——呼び出し側（`agents/formal-checker.md`）の決まり。
- **行為の中の選択**（`Put(w) == \E v \in S : …`）——選んだ値は JSON に出ない（`context` は行為の引数だけ）ので、0 で `steps` を出し、テストは値を強制できない。
  呼び出しの入力に写る選択は、行為の引数にしてモデルを書く（引数にすれば、ほかの引数として 1 で止まる）。
- **TLC の版による JSON の形の違い**——v1.8.0 のプレリリースで確かめた形だけ。CI には TLC が無いので、回帰テストは手元で取った JSON を試料にする。
"""

import json
import sys

EXIT_OK = 0
EXIT_CANNOT = 1
EXIT_USAGE = 2

REST_KEYS = ("setup", "outcomes", "after")
MIN_STEPS = 2


class Cannot(Exception):
    """反例を段の並びにできない（1）。"""


class Malformed(Exception):
    """引数・ファイル・形が違う（2）。"""


def load(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise Malformed(f"{what}（{path}）を読めない: {e}")


def check_table(table):
    if not isinstance(table, dict):
        raise Malformed("対応表がオブジェクトでない")
    for key in ("formal", "caller", "calls", "actions"):
        if key not in table:
            raise Malformed(f"対応表に `{key}` が無い")
    if not isinstance(table["caller"], str) or not table["caller"]:
        raise Malformed("対応表の `caller` が空でない文字列でない")
    calls, actions = table["calls"], table["actions"]
    if not isinstance(calls, dict) or not calls:
        raise Malformed("対応表の `calls` が空でないオブジェクトでない")
    for value, call in calls.items():
        if not isinstance(call, dict) or set(call) != {"name", "operation", "input"}:
            raise Malformed(f"対応表の `calls` の `{value}` が name・operation・input のオブジェクトでない")
    names = [call["name"] for call in calls.values()]
    if not all(isinstance(n, str) and n for n in names):
        raise Malformed(f"対応表の `calls` の name が空でない文字列でない: {names}")
    if len(set(names)) != len(names):
        raise Malformed(f"対応表の `calls` に同じ呼び出しの名前がある: {names}")
    if not isinstance(actions, dict) or not actions or not all(isinstance(v, str) for v in actions.values()):
        raise Malformed("対応表の `actions` が、行為の名前 → 段の名前（文字列）の空でないオブジェクトでない")
    skip = table.get("skip", [])
    if not isinstance(skip, list) or not all(isinstance(s, str) for s in skip):
        raise Malformed("対応表の `skip` が文字列の配列でない")
    both = sorted(set(skip) & set(actions))
    if both:
        raise Malformed(f"`actions` と `skip` の両方にある行為: {', '.join(both)}")
    rest = table.get("rest", {})
    if not isinstance(rest, dict):
        raise Malformed("対応表の `rest` がオブジェクトでない")
    extra = sorted(set(rest) - set(REST_KEYS))
    if extra:
        raise Malformed(f"対応表の `rest` に {'・'.join(REST_KEYS)} のほかの鍵がある: {', '.join(extra)}")
    unknown = sorted(set(table) - {"formal", "caller", "calls", "actions", "skip", "rest"})
    if unknown:
        raise Malformed(f"対応表に決まりに無い鍵がある: {', '.join(unknown)}")
    return set(skip)


def numbered(item, where):
    if not (isinstance(item, list) and len(item) == 2 and isinstance(item[0], int) and not isinstance(item[0], bool)):
        raise Malformed(f"{where} が [番号, 状態] でない")
    return item[0]


def actions_of(dump):
    try:
        actions = dump["counterexample"]["action"]
    except (TypeError, KeyError):
        raise Malformed("反例の JSON に counterexample.action が無い")
    if not isinstance(actions, list):
        raise Malformed("反例の JSON の counterexample.action が配列でない")
    expect = 1
    out = []
    for i, entry in enumerate(actions, 1):
        if not (isinstance(entry, list) and len(entry) == 3 and isinstance(entry[1], dict)):
            raise Malformed(f"{i} 番目の行為が [前の状態, 行為, 後の状態] でない")
        before = numbered(entry[0], f"{i} 番目の行為の前の状態")
        after = numbered(entry[2], f"{i} 番目の行為の後の状態")
        if before != expect:
            raise Malformed(f"{i} 番目の行為の前の状態の番号が {before}（{expect} のはず）")
        if after <= before:
            raise Cannot(f"{i} 番目の行為（{entry[1].get('name')}）が状態 {after} に戻る——繰り返しのある反例（活性の違反）は段の並びにしない")
        if after != before + 1:
            raise Malformed(f"{i} 番目の行為の後の状態の番号が {after}（{before + 1} のはず）")
        expect = after
        out.append(entry[1])
    return out


def key_of(value, name):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise Cannot(f"行為 {name} の呼び出しの値 {json.dumps(value, ensure_ascii=False)} が文字列でも整数でもない")
    return value if isinstance(value, str) else str(value)


def convert(dump, table):
    skip = check_table(table)
    caller = table["caller"]
    steps = []
    for i, action in enumerate(actions_of(dump), 1):
        name = action.get("name")
        if not isinstance(name, str) or not name:
            raise Malformed(f"{i} 番目の行為の name が空でない文字列でない: {json.dumps(name, ensure_ascii=False)}")
        if name in skip:
            continue
        if name not in table["actions"]:
            raise Cannot(f"{i} 番目の行為 {name} が対応表の `actions` にも `skip` にも無い")
        params = action.get("parameters", [])
        context = action.get("context", {})
        if not isinstance(params, list) or not all(isinstance(p, str) for p in params) or not isinstance(context, dict):
            raise Malformed(f"{i} 番目の行為 {name} の parameters・context の形が違う")
        if (caller in params) != (caller in context):
            raise Malformed(f"{i} 番目の行為 {name} の parameters と context の片方にだけ `{caller}` がある")
        if caller not in params:
            raise Cannot(f"{i} 番目の行為 {name} に呼び出しの引数 `{caller}` が無い（引数: {params}）——"
                         "呼び出しを引数に取る名前つきの行為で書くか、段にしないなら `skip` に挙げる")
        others = [p for p in params if p != caller]
        if others:
            raise Cannot(f"{i} 番目の行為 {name} に呼び出しのほかの引数がある: {others}（値を `calls` の入力に写せない）")
        key = key_of(context[caller], name)
        if key not in table["calls"]:
            raise Cannot(f"{i} 番目の行為 {name} の呼び出し {key!r} が対応表の `calls` に無い")
        steps.append([table["calls"][key]["name"], table["actions"][name]])
    if len(steps) < MIN_STEPS:
        raise Cannot(f"段が {len(steps)} つ（{MIN_STEPS} つより少ない）——初めの状態で違反した反例は段の並びにしない")
    calls = {c["name"]: {"operation": c["operation"], "input": c["input"]} for c in table["calls"].values()}
    trace = {"formal": table["formal"], "calls": calls, "steps": steps}
    trace.update(table.get("rest", {}))
    return trace


def main(argv):
    if len(argv) != 2:
        print("使い方: tlc-trace.py <反例の JSON> <対応表の JSON>", file=sys.stderr)
        return EXIT_USAGE
    try:
        trace = convert(load(argv[0], "反例の JSON"), load(argv[1], "対応表"))
    except Malformed as e:
        print(f"tlc-trace: 形が違う: {e}", file=sys.stderr)
        return EXIT_USAGE
    except Cannot as e:
        print(f"tlc-trace: 段の並びにできない: {e}", file=sys.stderr)
        return EXIT_CANNOT
    print(json.dumps(trace, ensure_ascii=False))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
