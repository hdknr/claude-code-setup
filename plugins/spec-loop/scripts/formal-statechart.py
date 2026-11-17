#!/usr/bin/env python3
r"""保存した TLC のモデル（`spec/formal/<対象>/`）を TLC で展開し、利用者の言葉の状態遷移図（Mermaid）にする（#1177）。

usage:
    python3 formal-statechart.py <正本リポジトリの根> <spec/formal/<対象> のディレクトリ> [--out <ファイル>] [--controls] [--max-edges <本数>] [--timeout <秒>]

**図は描かずに、モデルからレンダリングする。** 状態と遷移は TLC が展開した状態グラフ（`-dump dot,actionlabels`）だけから取り、
ラベルは対象のディレクトリの対応のファイル（記録の `図の対応のファイル`。下の「対応」）の言葉だけを使う——**変数名・行為の名前・TLC の状態の式は図に出さない。**

**正本リポジトリに書くのは `--out` で渡したファイル 1 つだけ**（渡さなければ標準出力に出し、何も書かない）。モデルは一時ディレクトリに写して走らせ、終わったら消す（TLC の `states/` と
状態グラフのファイルを正本に残さない）。**描けなかったら `--out` のファイルに触らない。**

**決まりの正は `references/tree.md` の「形式検査のモデル」（記録の項目と、図と対応の置き場所）である**（このプラグインの中にある）。
記録（`README.md`）の読み方は同梱の `formal-baseline.py` の `read_records`、一覧から TLC のモデルを選ぶのと違反の印は `check-formal-rerun.py` の `entries`・`violated`、
TLC の呼び方の読み方・走らせ方は `check-tlc.py` のもの（読み込んで使う——写さない）。

## なぜ在るのか（#1177）

Formal Checker が組んだモデルは `spec/formal/<対象>/` に残るが、人が読める形にする段が無かった。反例は `[呼び出しの名前, 段の名前]` の並び（テキスト）でしか渡らず、
利用者は「どの状態から、どの操作で、規則を破る状態に行くか」を見て判断できなかった。

## 何を描くか

- **本体**: 記録の `モデルのファイル` の TLC のモデル（同じ名前の `.tla` と `.cfg`。陽性対照の一覧にもある名前は除く——`check-formal-rerun.py` と同じ）。
- **陽性対照**（`--controls` のときだけ）: 記録の `陽性対照のファイル` の TLC のモデル。**違反が 1 つも出なければ描いたことにしない（4）**——印を付ける形を確かめられない。
- 一覧のファイルを 1 つの一時ディレクトリに写し、呼び方の後ろに `-continue -dump dot,actionlabels <名前>.dump.dot <名前>.tla` を足してそのディレクトリで `sh` に渡す。
  `-continue` は不変条件の違反の後も展開を続けさせる（違反した状態ごとに反例を出し、状態グラフを最後まで書く）。
- **状態**: 状態グラフの節点。対応で同じ言葉になる状態は 1 つにまとめる（ビュー）。初めの状態（`style = filled`）に `[*]` からの矢印を付ける。
- **遷移**: 状態グラフの辺を、行為の名前を対応の言葉に替えて描く（まとめた結果が同じ遷移は 1 本）。対応の `skip` の行為は、まとめた後で同じ状態に戻る辺に限って描かない。
- **印**: TLC の出力の反例（`is violated`・`Deadlock reached`。初めの状態が破る `is violated by the initial state:` の形も）の最後の状態を、規則を破る状態として `⚠` を付けて描く（`classDef violated` も付ける）。
  行き止まり（`Deadlock reached`）の状態にも同じ印を付け、図にそう書く（`check-formal-rerun.py` も行き止まりを反例に数える）。
- **経路**: 最初の反例（幅優先の展開なので最短）の段を、遷移の言葉の前に段の番号（`1. 申請する`）を付けて描き、図の下に経路の一覧を書く。
- **大きいモデル**: まとめた後の遷移が `--max-edges`（既定 20）本を超え、反例があるなら、**反例までの経路の状態と遷移だけを描き**、そう書く（反例が無ければ全部を描いて、多いと書く）。
- **全体でないグラフ**: TLC が待ちの状態を残して止まった（`N states left on queue` の N が 0 でない。行き止まりで止まったときなど）なら、図に「全体ではない」と書く。

## 対応（`図の対応のファイル`）

JSON のオブジェクト。Formal Checker が報告に書き（`agents/formal-checker.md`）、spec-review がモデルと一緒に残す:

    {"states": [{"when": {"status": "\"draft\""}, "label": "下書き"},
                {"when": {"status": "\"shipped\"", "paid": "FALSE"}, "label": "未払いのまま出荷済み"},
                {"when": {"status": "\"shipped\""}, "label": "出荷済み"}],
     "actions": {"Submit": "申請する", "Ship": "出荷する"},
     "skip": ["Done"]}

| 鍵 | 書くもの |
| --- | --- |
| `states` | 状態の言葉の並び（1 つ以上）。`when` は変数の名前 → 値（TLC が状態に印字する TLA+ の値の文字列。文字列は `"…"` ごと）。**状態ごとに、上から最初に `when` が全部合う行の `label` を使う**（空白の並びは 1 つの空白と見る） |
| `actions` | 行為の名前 → 操作の言葉 |
| `skip` | （任意）描かない行為の名前の配列（終わった後の `Done` のような、同じ状態に戻る行為）。`actions` と重ねない |

**言葉に使えない文字**: 改行と制御文字、半角の `"` `:` `;` `#` `<` `>` `{` `}` `[` `]` `|` と `` ` ``（Mermaid の構文の文字。全角の `：` などは使える）。

## 終了コード

| コード | 意味 |
| --- | --- |
| 0 | 描けた（`--out` に書いたか、標準出力に出した） |
| 1 | 描けない——対応に無い状態・行為がある、対応の形が違う・使えない文字、`skip` の行為が別の状態へ移る、規則を破る状態と破らない状態を 1 つの言葉にまとめた（不変条件の反例のとき）、時相の性質の反例（繰り返しのある反例）・行為の性質の反例。対応を直すか、描かない対象と読む |
| 2 | 引数が違う・想定外の例外 |
| 4 | 判定できなかった——呼び方の行が無い、記録が読めない、TLC のモデルが一覧に無い、`図の対応のファイル` が無い、一覧のファイルが無い、TLC が走りきらない（時間切れ・反例の印と別の `Error: ` の行——反例の後の評価の誤りを含む）・状態グラフが無いか読めない、反例の状態・段が状態グラフに無い、`--controls` で陽性対照に違反が出ない |

## 何を守り、何を守らないか

**守ること**:

| 守ること | 破る形 |
| --- | --- |
| 図の状態と遷移を TLC の状態グラフの節点と辺だけから作る | 図が TLC の展開と食い違う（描き足す・描き落とす） |
| 対応に無い状態・行為があれば描かない（1） | 変数名・行為の名前・状態の式が図に出る |
| `skip` は、まとめた後で同じ状態に戻る辺だけを描かない | 別の状態へ移る遷移が図から黙って消える |
| 反例の最後の状態に印を付ける（`-continue` で違反ごとの反例を読む） | 規則を破る状態が図の上で見分けられない |
| 規則を破る状態と破らない状態を 1 つの言葉にまとめた対応を通さない（1。不変条件の反例だけに当てる——行き止まりで TLC が止まると、同じ言葉のほかの終わりの状態は報告されない） | 印が、破らない状態まで覆う |
| 最初の反例の段を番号つきの遷移と経路の一覧で描く | 「どの状態から、どの操作で」破るかが図に出ない |
| 反例の状態と段が状態グラフに無ければ 4 | 状態グラフと食い違う経路を描く |
| `--controls` の陽性対照で違反が出なければ 4 | 印を付ける形が空振りのまま、描けたと言う |
| 時相の性質の反例（繰り返しのある反例）と行為の性質の反例（`Action property … is violated`）は描かない（1） | 戻る経路や、破った遷移の行き先を、規則を破る状態と読ませる |
| TLC が走りきらない（反例の印と別の `Error: ` の行がある）・状態グラフが無いなら 4 | 走っていないモデル・途中で止まったモデルの図を出す |
| 待ちの状態が残ったグラフには「全体ではない」と書く | 途中で止まった展開を全体と読ませる |
| 一時ディレクトリで走らせ、描けたときだけ `--out` の 1 ファイルを書く | 正本に `states/` や状態グラフが残る・描けなかったのに古い図が新しく見える |
| 呼び方の行が無ければ 4（`PATH` の `tlc` で探さない） | `check-tlc.py` と違う探し方で走らせる |

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **対応の言葉が正しいか**（状態の言葉が変数の値を正しく言い表しているか） | 判定役（Formal Checker）が書き、人が読む。機械が見るのは全部の状態と行為に言葉があることだけ |
| **図の鮮度**（モデルか対応を直した後で図を作り直したか） | 作り直すのは spec-review の「モデルを残す」（`tree.md`）。作り直すには TLC が要り、正本の CI には無いことが多い |
| **Mermaid の図が GitHub・MkDocs で描けるか** | 描くのは閲覧側。出す文字列の形（`stateDiagram-v2`・`classDef`）は回帰テストで見るが、描画は確かめていない |
| **TLC の版による出力の違い** | 状態グラフ（`-dump dot,actionlabels`）と反例の出力の形は TLC 2.19（tla2tools v1.7.4）で確かめた。回帰テストは本物で取った出力を偽の TLC が返す |
| **最初の反例のほかの反例の経路** | 印は全部の反例の最後の状態に付けるが、経路は最初の 1 つだけ描く |
| **TLC でないモデル**（Alloy・総当たり・Z3） | Issue の範囲の外。渡されたら TLC のモデルが無いとして 4 |
| **呼び方の安全** | 正本の `CLAUDE.md` の文字列をそのまま `sh` で走らせる（`check-tlc.py` と同じ） |

対象リポジトリ（正本リポジトリ）で単体で動くよう、**標準ライブラリだけ**を使う。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tlc = _load("check_tlc", "check-tlc.py")
baseline = _load("formal_baseline", "formal-baseline.py")
rerun = _load("check_formal_rerun", "check-formal-rerun.py")

VIEW_ITEM = "図の対応のファイル"
MAX_EDGES = 20
TIMEOUT = 600
EXIT_OK, EXIT_UNDRAWABLE, EXIT_USAGE, EXIT_UNKNOWN = 0, 1, 2, 4
BAD_MARK = "⚠ "
# 言葉に使えない文字（Mermaid の構文の文字）
FORBIDDEN = set('":;#<>{}[]|`')
NODE = re.compile(r'(-?\d+) \[label="((?:[^"\\]|\\.)*)"(,style = filled)?\];?')
# 活性を確かめる設定のとき TLC が書く、行為の名前の無い足踏み（同じ状態に留まる）の辺
STUTTER = re.compile(r'(-?\d+) -> (-?\d+) \[style="dashed"\];?')
EDGE = re.compile(r'(-?\d+) -> (-?\d+) \[label="((?:[^"\\]|\\.)*)"(?:,[^\]]*)?\];?')
STATE = re.compile(r"State (\d+): <(.*)>$")
QUEUE = re.compile(r"(\d+) states? left on queue")
TRACE_START = ("is violated", "Deadlock reached", "were violated")
# 反例の本体の前置き（反例の印の後ろに TLC が書く行）。ほかの `Error: ` の行は、TLC が走りきらなかった印
BEHAVIOR = ("Error: The behavior up to this point is:", "Error: The following behavior constitutes a counter-example:")
INITIAL = "by the initial state:"


class Stop(Exception):
    """描かずに止まる（終了コードと理由）。"""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def unescape(text: str) -> str:
    return re.sub(r"\\(.)", lambda m: "\n" if m.group(1) == "n" else m.group(1), text)


def norm(value: str) -> str:
    return " ".join(value.split())


def assignments(text: str) -> dict[str, str]:
    """TLC が印字する状態（`/\\ x = 1` の並び、変数が 1 つなら `x = 1`）を 変数 → 値 にする。"""
    lines = [line for line in text.strip().splitlines() if line.strip()]
    chunks: list[str] = []
    if lines and lines[0].startswith("/\\ "):
        for line in lines:
            if line.startswith("/\\ "):
                chunks.append(line[3:])
            else:
                chunks[-1] += " " + line.strip()
    elif lines:
        chunks = [" ".join(line.strip() for line in lines)]
    state: dict[str, str] = {}
    for chunk in chunks:
        name, sep, value = chunk.partition(" = ")
        if not sep or not name.strip() or name.strip() in state:
            raise Stop(EXIT_UNKNOWN, f"状態の印字を読めない: {chunk!r}")
        state[name.strip()] = norm(value)
    if not state:
        raise Stop(EXIT_UNKNOWN, "状態の印字が空")
    return state


def key(state: dict[str, str]) -> tuple:
    return tuple(sorted(state.items()))


def read_dot(text: str) -> tuple[dict[str, dict[str, str]], set[str], list[tuple[str, str, str]]]:
    """状態グラフ（`-dump dot,actionlabels`）を (節点 → 状態, 初めの節点, 辺 (元, 先, 行為)) にする。"""
    nodes: dict[str, dict[str, str]] = {}
    initial: set[str] = set()
    edges: list[tuple[str, str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        node = NODE.fullmatch(line)  # 節点を先に読む——状態の値（`[k |-> v]`）が `->` を含む
        if node is not None:
            nodes[node.group(1)] = assignments(unescape(node.group(2)))
            if node.group(3):
                initial.add(node.group(1))
        elif STUTTER.fullmatch(line):
            a, b = STUTTER.fullmatch(line).groups()
            if a != b:
                raise Stop(EXIT_UNKNOWN, f"状態グラフに行為の名前の無い辺が別の状態へ向かう: {line[:120]!r}")
        elif line[:1].isdigit() or line.startswith("-"):
            m = EDGE.fullmatch(line)
            if m is None:
                raise Stop(EXIT_UNKNOWN, f"状態グラフの節点・辺を読めない（辺に行為の名前が無い・形が違う）: {line[:120]!r}")
            edges.append((m.group(1), m.group(2), unescape(m.group(3))))
    if not nodes:
        raise Stop(EXIT_UNKNOWN, "状態グラフに節点が 1 つも無い")
    for a, b, _ in edges:
        if a not in nodes or b not in nodes:
            raise Stop(EXIT_UNKNOWN, f"状態グラフの辺が節点に無い状態を指す: {a} -> {b}")
    if not initial:
        raise Stop(EXIT_UNKNOWN, "状態グラフに初めの状態（style = filled）が無い")
    return nodes, initial, edges


def read_traces(out: str) -> list[tuple[bool, list[tuple[str | None, dict[str, str]]]]]:
    """TLC の出力の反例を、(行き止まりか, (段の行為（初めは None）, 状態) の並び) にする。時相の性質の反例は Stop(1)。"""
    traces: list[tuple[bool, list[tuple[str | None, dict[str, str]]]]] = []
    lines = out.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("Error: ") and any(mark in line for mark in TRACE_START):
            if "were violated" in line:
                raise Stop(EXIT_UNDRAWABLE, "時相の性質の反例（繰り返しのある反例）は描かない")
            if line.startswith("Error: Action property"):
                raise Stop(EXIT_UNDRAWABLE, "行為の性質の反例は描かない（破るのは状態ではなく遷移で、最後の状態に印を付けると誤る）")
            trace: list[tuple[str | None, dict[str, str]]] = []
            deadlock = "Deadlock reached" in line
            i += 1
            if line.rstrip().endswith(INITIAL):  # 初めの状態が破る形——`State 1:` の見出しが無く、状態がすぐ続く
                body = []
                while i < len(lines) and lines[i].strip():
                    body.append(lines[i])
                    i += 1
                traces.append((deadlock, [(None, assignments("\n".join(body)))]))
                continue
            while i < len(lines):
                head = lines[i].strip()
                if head.startswith("Back to state") or head.endswith(": Stuttering"):
                    raise Stop(EXIT_UNDRAWABLE, "繰り返しのある反例は描かない")
                m = STATE.fullmatch(head)
                if m is None:
                    if head.startswith("Error: ") and any(mark in head for mark in TRACE_START):
                        break
                    if trace and head and not head.startswith("Error: The"):
                        break
                    i += 1
                    continue
                inner = m.group(2)
                named = re.match(r"[A-Za-z_][A-Za-z0-9_]*", inner)
                action = None if inner == "Initial predicate" else (named.group(0) if named else inner)
                body = []
                i += 1
                while i < len(lines) and lines[i].strip():
                    body.append(lines[i])
                    i += 1
                trace.append((action, assignments("\n".join(body))))
            if not trace:
                raise Stop(EXIT_UNKNOWN, "反例の印はあるが、反例の状態を読めない")
            traces.append((deadlock, trace))
            continue
        i += 1
    return traces


def check_label(where: str, label) -> str:
    if not isinstance(label, str) or not label.strip():
        raise Stop(EXIT_UNDRAWABLE, f"対応の {where} の言葉が空でない文字列でない: {label!r}")
    bad = sorted({ch for ch in label if ch in FORBIDDEN or ord(ch) < 32 or ord(ch) == 127})
    if bad:
        raise Stop(EXIT_UNDRAWABLE, f"対応の {where} の言葉「{label}」に使えない文字がある: {bad!r}")
    return label.strip()


def read_view(path: Path) -> tuple[list[tuple[dict[str, str], str]], dict[str, str], set[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as e:
        raise Stop(EXIT_UNDRAWABLE, f"{path}: 対応を JSON として読めない（{e}）")
    if not isinstance(data, dict) or set(data) - {"states", "actions", "skip"} or not {"states", "actions"} <= set(data):
        raise Stop(EXIT_UNDRAWABLE, f"{path}: 対応は states・actions（と任意の skip）だけを持つオブジェクト")
    states = data["states"]
    if not isinstance(states, list) or not states:
        raise Stop(EXIT_UNDRAWABLE, f"{path}: states は 1 つ以上の並び")
    rules: list[tuple[dict[str, str], str]] = []
    for n, entry in enumerate(states, 1):
        if not isinstance(entry, dict) or set(entry) != {"when", "label"}:
            raise Stop(EXIT_UNDRAWABLE, f"{path}: states の {n} 番目は when・label だけを持つオブジェクト")
        when = entry["when"]
        if not isinstance(when, dict) or not when or not all(isinstance(k, str) and isinstance(v, str) for k, v in when.items()):
            raise Stop(EXIT_UNDRAWABLE, f"{path}: states の {n} 番目の when は 変数の名前 → 値の文字列 の空でないオブジェクト")
        rules.append(({k: norm(v) for k, v in when.items()}, check_label(f"states の {n} 番目", entry["label"])))
    actions = data["actions"]
    if not isinstance(actions, dict):
        raise Stop(EXIT_UNDRAWABLE, f"{path}: actions は 行為の名前 → 言葉 のオブジェクト")
    named = {name: check_label(f"actions の {name}", label) for name, label in actions.items()}
    skip = data.get("skip", [])
    if not isinstance(skip, list) or not all(isinstance(s, str) for s in skip):
        raise Stop(EXIT_UNDRAWABLE, f"{path}: skip は行為の名前の並び")
    if set(skip) & set(named):
        raise Stop(EXIT_UNDRAWABLE, f"{path}: actions と skip に同じ行為がある: {sorted(set(skip) & set(named))}")
    return rules, named, set(skip)


def label_of(state: dict[str, str], rules: list[tuple[dict[str, str], str]]) -> str | None:
    for when, label in rules:
        if all(state.get(name) == value for name, value in when.items()):
            return label
    return None


def render(name: str, kind: str, dot: str, out: str, view, max_edges: int) -> tuple[list[str], bool]:
    """1 つのモデルの節（Markdown の行）と、反例があったか。"""
    rules, actions, skip = view
    nodes, initial, edges = read_dot(dot)
    variables = {v for state in nodes.values() for v in state}
    unknown = sorted({v for when, _ in rules for v in when} - variables)
    if unknown:
        raise Stop(EXIT_UNDRAWABLE, f"{name}.tla: 対応の when が状態に無い変数を指す: {unknown}")
    labels: dict[str, str] = {}
    missing = []
    for node, state in nodes.items():
        label = label_of(state, rules)
        if label is None:
            missing.append(" /\\ ".join(f"{k} = {v}" for k, v in sorted(state.items())))
        else:
            labels[node] = label
    if missing:
        raise Stop(EXIT_UNDRAWABLE, f"{name}.tla: 対応に言葉の無い状態が {len(missing)} 個ある（例: {missing[0]}）")
    by_key = {key(state): node for node, state in nodes.items()}
    edge_set = set(edges)
    traces = read_traces(out)
    walks: list[list[tuple[str | None, str]]] = []
    for _, trace in traces:
        walk = []
        for action, state in trace:
            node = by_key.get(key(state))
            if node is None:
                raise Stop(EXIT_UNKNOWN, f"{name}.tla: 反例の状態が状態グラフに無い")
            if walk and (walk[-1][1], node, action) not in edge_set:
                raise Stop(EXIT_UNKNOWN, f"{name}.tla: 反例の段（{action}）が状態グラフの辺に無い")
            walk.append((action, node))
        walks.append(walk)
    bad_nodes = {walk[-1][1] for walk in walks}
    # 行き止まりで TLC が止まると、同じ言葉のほかの終わりの状態は展開されず報告されない——まとめの検査は不変条件の反例だけに当てる
    broken = {walk[-1][1] for walk, (dead, _) in zip(walks, traces) if not dead}
    bad_labels = {labels[n] for n in bad_nodes}
    mixed = sorted(lab for lab in {labels[n] for n in broken} if any(labels[n] == lab and n not in bad_nodes for n in nodes))
    if mixed:
        raise Stop(EXIT_UNDRAWABLE, f"{name}.tla: 規則を破る状態と破らない状態を同じ言葉にまとめている: {mixed}")
    view_edges: set[tuple[str, str, str]] = set()
    for a, b, action in edges:
        if action in skip:
            if labels[a] != labels[b]:
                raise Stop(EXIT_UNDRAWABLE, f"{name}.tla: skip の行為 {action} が別の状態へ移る（描かずに消せない）")
            continue
        if action not in actions:
            raise Stop(EXIT_UNDRAWABLE, f"{name}.tla: 対応に言葉の無い行為がある: {action}")
        view_edges.add((labels[a], labels[b], actions[action]))
    steps: dict[tuple[str, str, str], list[int]] = {}
    path_lines = []
    number = 0
    if walks:
        walk = walks[0]
        path_lines.append(f"- はじめ: {mark(labels[walk[0][1]], bad_labels)}")
        for (_, prev), (action, node) in zip(walk, walk[1:]):
            if action in skip:
                continue
            number += 1
            edge = (labels[prev], labels[node], actions[action])
            steps.setdefault(edge, []).append(number)
            path_lines.append(f"- {number}.「{actions[action]}」→ {mark(labels[node], bad_labels)}")
    starts = {labels[n] for n in initial}
    states = bfs_order(starts, view_edges, set(labels.values()))
    drawn_edges = view_edges
    notes = []
    if any(dead for dead, _ in traces):
        notes.append(f"TLC が行き止まり（次に進める操作の無い状態）を見つけた。行き止まりの状態にも `{BAD_MARK.strip()}` を付けた。")
    if len(view_edges) > max_edges:
        if walks:
            states = bfs_order(starts, set(steps), {labels[n] for _, n in walks[0]})
            drawn_edges = set(steps)
            notes.append(f"遷移が {len(view_edges)} 本あり、{max_edges} 本を超えるので、反例までの経路だけを描いた。")
        else:
            notes.append(f"遷移が {len(view_edges)} 本あり、{max_edges} 本を超える（反例が無いので全部を描いた）。")
    queued = QUEUE.findall(out)
    if queued and int(queued[-1]) != 0:
        notes.append("TLC が途中で止まった（待ちの状態が残った）ので、図は全体ではない。")
    ids = {label: f"s{i}" for i, label in enumerate(states, 1)}
    chart = ["```mermaid", "stateDiagram-v2"]
    chart += [f"    {ids[label]}: {mark(label, bad_labels)}" for label in states]
    chart += [f"    [*] --> {ids[label]}" for label in states if label in starts]
    for a, b, action in sorted(drawn_edges, key=lambda e: (states.index(e[0]), states.index(e[1]), e[2])):
        text = action if (a, b, action) not in steps else f"{'・'.join(map(str, steps[(a, b, action)]))}. {action}"
        chart.append(f"    {ids[a]} --> {ids[b]}: {text}")
    shown_bad = [ids[label] for label in states if label in bad_labels]
    if shown_bad:
        chart.append("    classDef violated fill:#fde2e2,stroke:#c62828,stroke-width:2px")
        chart += [f"    class {i} violated" for i in shown_bad]
    chart.append("```")
    result = "反例あり" if walks else "反例なし"
    lines = [f"## {name}.tla（{kind}）", "",
             f"- 結果: {result}（状態 {len(set(labels.values()))}・遷移 {len(view_edges)}。TLC の状態 {len(nodes)}・遷移 {len(edge_set)}）"]
    lines += [f"- {note}" for note in notes]
    lines += ["", *chart, ""]
    if walks:
        lines += [f"反例の経路（`{BAD_MARK.strip()}` は規則を破る状態）:", "", *path_lines, ""]
    return lines, bool(walks)


def bfs_order(starts: set[str], edges: set[tuple[str, str, str]], among: set[str]) -> list[str]:
    """状態の言葉を、初めの状態から幅優先でたどった順に並べる（たどれないものは後ろに名前の順で）。"""
    following: dict[str, list[tuple[str, str]]] = {}
    for a, b, action in edges:
        following.setdefault(a, []).append((action, b))
    queue = sorted(starts & among)
    seen = set(queue)
    order: list[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for _, b in sorted(following.get(current, [])):
            if b in among and b not in seen:
                seen.add(b)
                queue.append(b)
    return order + sorted(among - seen)


def mark(label: str, bad: set[str]) -> str:
    return f"{BAD_MARK}{label}" if label in bad else label


def draw(call: str, directory: Path, max_edges: int, timeout: int, controls: bool) -> tuple[str, list[str]]:
    """対象の図（Markdown）と、標準エラーに出す行。描けなければ Stop。"""
    if not directory.is_dir():
        raise Stop(EXIT_UNKNOWN, f"{directory}: ディレクトリでない")
    try:
        records, problems = baseline.read_records(directory / baseline.README)
    except baseline.Unjudged as e:
        raise Stop(EXIT_UNKNOWN, str(e))
    if problems:
        raise Stop(EXIT_UNKNOWN, "・".join(problems))
    models = baseline.FILE.findall(records.get(rerun.MODEL_ITEM, ""))
    control_files = baseline.FILE.findall(records.get(rerun.CONTROL_ITEM, ""))
    broken = rerun.entries(control_files)
    bodies = [n for n in rerun.entries(models) if n not in broken]
    if not bodies:
        raise Stop(EXIT_UNKNOWN, f"{directory}: {rerun.MODEL_ITEM}に TLC のモデル（同じ名前の .tla と .cfg）が無い")
    if controls and not broken:
        raise Stop(EXIT_UNKNOWN, f"{directory}: --controls だが {rerun.CONTROL_ITEM}に TLC のモデルが無い")
    views = baseline.FILE.findall(records.get(VIEW_ITEM, ""))
    if len(views) != 1:
        raise Stop(EXIT_UNKNOWN, f"{directory}: 記録の「{VIEW_ITEM}」にファイルの名前が 1 つだけ無い（{len(views)} 個）——変数名を出さないので、対応なしでは描かない")
    names = list(dict.fromkeys(models + control_files + views))
    for name in names:
        source = directory / name
        if "/" in name or name in (baseline.README, ".", "..") or source.is_symlink() or not source.is_file():
            raise Stop(EXIT_UNKNOWN, f"{directory}: 一覧のファイル「{name}」がこのディレクトリの通常のファイルとして無い")
    view = read_view(directory / views[0])
    targets = [(n, "本体") for n in bodies] + ([(n, "陽性対照（わざと壊した版）") for n in broken] if controls else [])
    sections: list[str] = []
    notes: list[str] = []
    with tempfile.TemporaryDirectory(prefix="spec-loop-statechart-") as tmp:
        for name in names:
            shutil.copyfile(directory / name, Path(tmp) / name)
        for name, kind in targets:
            dot_name = f"{name}.dump.dot"
            rc, out = tlc.run_model(f"{call} -continue -dump dot,actionlabels {shlex.quote(dot_name)}", tmp, name, timeout)
            dot_path = Path(tmp) / dot_name
            if rc is None or not (tlc.GOOD_MARK in out or rerun.violated(out)) or not dot_path.is_file():
                raise Stop(EXIT_UNKNOWN, f"{directory}: {name}.tla を TLC が走りきらなかった（終了コード {rc}）: {tlc.tail(out)}")
            odd = [line for line in out.splitlines()
                   if line.startswith("Error: ") and not any(mark in line for mark in TRACE_START) and not line.startswith(BEHAVIOR)]
            if odd:  # 反例の後に評価の誤りで止まった形——状態グラフが途中で切れている
                raise Stop(EXIT_UNKNOWN, f"{directory}: {name}.tla を TLC が走りきらなかった（終了コード {rc}。{odd[0]}）")
            lines, found = render(name, kind, dot_path.read_text(encoding="utf-8", errors="replace"), out, view, max_edges)
            if kind != "本体" and not found:
                raise Stop(EXIT_UNKNOWN, f"{directory}: 陽性対照 {name}.tla で違反が出ない（印を付ける形を確かめられない。空振りの疑い）")
            notes.append(f"{directory}: {name}.tla（{kind}）: {'反例あり' if found else '反例なし'}")
            sections += lines
    head = [f"# 状態遷移図: {directory.resolve().name}", "",
            "<!-- 生成物: spec-loop の scripts/formal-statechart.py が、保存したモデルと対応から作った。手で直さない -->", ""]
    return "\n".join(head + sections).rstrip("\n") + "\n", notes


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="保存した TLC のモデルを状態遷移図（Mermaid）にする")
    parser.add_argument("root", type=Path, help="正本リポジトリの根（CLAUDE.md の在る場所）")
    parser.add_argument("directory", type=Path, help="spec/formal/<対象> のディレクトリ")
    parser.add_argument("--out", type=Path, help="書く先（無ければ標準出力）")
    parser.add_argument("--controls", action="store_true", help="陽性対照の図も描く")
    parser.add_argument("--max-edges", default=str(MAX_EDGES), help=f"これを超えたら反例までの経路だけを描く（既定 {MAX_EDGES}）")
    parser.add_argument("--timeout", default=str(TIMEOUT), help=f"1 回の検査の上限の秒（既定 {TIMEOUT}）")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_USAGE
    for flag, value in (("--max-edges", args.max_edges), ("--timeout", args.timeout)):
        if not value.isdigit() or int(value) < 1:
            print(f"{flag} は 1 以上の整数: {value!r}", file=sys.stderr)
            return EXIT_USAGE
    if args.out is not None and not args.out.parent.is_dir():
        print(f"--out の親のディレクトリが無い: {args.out.parent}", file=sys.stderr)
        return EXIT_USAGE
    try:
        call, _, note = tlc.read_declarations(args.root)
    except tlc.Unknown as e:
        call, note = None, str(e)
    try:
        if call is None:
            raise Stop(EXIT_UNKNOWN, f"TLC の呼び方が無い（{note}。正本の CLAUDE.md の `{tlc.CALL_KEY}` の行。`command -v` では探さない）")
        text, notes = draw(call, args.directory, int(args.max_edges), int(args.timeout), args.controls)
    except Stop as stop:
        print(f"描かなかった: {stop}", file=sys.stderr)
        if args.out is not None:
            print(f"{args.out} には触っていない", file=sys.stderr)
        return stop.code
    for line in notes:
        print(line, file=sys.stderr)
    if args.out is None:
        sys.stdout.write(text)
    else:
        temp = args.out.with_name(f".{args.out.name}.tmp")
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, args.out)
        print(f"書いた: {args.out}", file=sys.stderr)
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も 2。トレースバックの 1（描けない）に化けさせない
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。描いていない", file=sys.stderr)
        sys.exit(2)
