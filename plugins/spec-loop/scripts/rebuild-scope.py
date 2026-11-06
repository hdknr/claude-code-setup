#!/usr/bin/env python3
"""仮回答と推奨で決めた事項の台帳から、利用者が確かめたときに作り直す範囲を引く（#875）。

usage: python3 rebuild-scope.py --issues <Issue の一覧の JSON> [<Q&A の No> | #<Issue の番号>]...
       python3 rebuild-scope.py --issues <Issue の一覧の JSON> --changed

**台帳は、登録した Issue の本文そのものである**（新しいファイルを持たない）。入力は開発のリポジトリ（Issue を登録した先）の
Issue の一覧で、決まった 1 行で取る（**このスクリプトは `gh` を呼ばない**）:

```bash
gh issue list --repo <開発のリポジトリ> --state all --limit 1000 --json number,title,state,body,comments > issues.json
```

読むのは 2 種類の Issue である:

- **spec-loop から渡した Issue**（本文の先頭が `<!-- spec-loop-handoff: v`）——受入基準の表の `Q&A` の列と `## Q&A の回答` の No が、
  その Issue が根拠にした Q&A である。`## 仕様` の `- 仮回答: ` の行と表の `（暫定）` が仮回答の印（`--provisional` で作った本文だけ。
  形の正は `references/handoff-issue.md` の「仮回答の印」で、印の定数は `scaffold.py` のものを読む——写さない）。
  **まとめた本文**（2 行目が `<!-- spec-loop-bundle: … -->`。#876）は、機能の印の行で機能ごとの部分に分け、部分ごとに同じく読む
  （部分は機能 1 件の本文と同じ節を持つ。`references/handoff-issue.md` の「まとめた本文」）。
- **確認の Issue**（dev-loop が推奨で決めて進めた判断を、利用者に確かめてもらう Issue）——本文に印 `<!-- cruise-decision: #<親> -->` があるか、
  題が `要確認: ` で始まるもの。本文の行頭の `決めた値: ` と `影響する Issue: ` の 2 行（形の正は dev-loop の
  `references/absent-lines.md` の「確認の Issue の書き方」。下の定数はその写しで、`scripts/test-rebuild-scope.py` が突き合わせる）。
  **閉じたときの結果**は、コメントの行頭の `確認の結果: 推奨のまま` か `確認の結果: 変えた: <新しい値>`（#884。形の正は同じファイルの
  「閉じるときの結果の 1 行」で、定数は同じく写し）。**コメントの最後の結果の行を採る**（開き直して変えたときは後のコメント）。本文の中の行は読まない。

引き方:

- **引数なし**: 台帳の一覧——仮回答の印を持つ Q&A ごとに、依存する Issue とケース。続けて確認の Issue ごとに、決めた値と影響する Issue。
- **`<Q&A の No>`**（`Q-R-002`・`D-S-001`）: その No を根拠にした spec-loop の Issue（閉じたものも。**撤去の Issue は数えない**——作るものが無い）と、その受入基準のうちその No を根拠にする
  ケース——**ケースに無ければ「機能全体」**（機能の `qa` だけが指している）。どれかの本文が仮回答の印を付けていれば、そう言う。
- **`#<番号>`**: 確認の Issue なら、確認の結果（推奨のまま・変えた・結果なし）と、決めた値と影響する Issue（題と状態を添える）。
  引数なしの一覧も、確認の Issue ごとに確認の結果を出す。
- **`--changed`**（No・番号と一緒には渡せない）: 確認の結果が `変えた` の確認の Issue だけ——決めた値・新しい値・影響する Issue（作り直す範囲）。
  **閉じたのに結果の行が無い確認の Issue**（この決まりより前に閉じた・添え忘れ）は変えたかを読めないので名指しする。

終了コード:

- 0: 引けた（引数なしなら一覧を出した）
- 1: 引けない番号がある——その No を根拠にした spec-loop の Issue が無い・その番号の Issue が入力に無い・確認の Issue でない・
  確認の Issue に台帳の 2 行が無い（この決まりより前の書き方。`## 出所` を人が読む）・`影響する Issue: ` の行が決まりの形でない・
  影響する Issue が入力に無い（範囲を引ききれていない）・確認の結果の行が決まりの形でない。`--changed` では、入力に `comments` の鍵が無い
  確認の Issue（結果を読んでいない）・結果の行が決まりの形でない確認の Issue・閉じたのに結果の行が無い確認の Issue・変えた確認の Issue のうち
  台帳の行が無い／形に反する／影響する Issue が入力に無いものがあれば 1。引けたものは出力し、引けないものを名指しする
- 2: 判定していない——引数の誤り・入力が読めない（JSON でない・`number`・`title`・`body` の形が違う・`comments` が本文を持つコメントの配列でない）

**`comments` の鍵は任意**——無い入力（この決まりより前の取り方）でも台帳は引け、確認の結果は「読んでいない」と出る（「結果なし」とは言わない）。

対象リポジトリで単体で動くよう、**標準ライブラリだけ**を使う（同じ `scripts/` の `scaffold.py` を読み込む）。

**守らないもの**:

| 守らないもの | なぜ |
| --- | --- |
| **本文の印が、いまの Q&A 表の状態と同じか** | 本文は生成した時点の写し。利用者が確かめた後も印は残る——いまの状態の正は Q&A 表（`暫定反映` が残っているか） |
| **中間表現が指し漏らした機能を挙げるか** | 本文に No が無ければ引けない。指しているかは書き起こしの判断（`scaffold.py` の docstring） |
| **入力が全部の Issue を含むか** | `--limit` を超えた Issue・取った後に登録した Issue は見えない。取り方の 1 行の `--limit` を Issue の数より大きくする |
| **確認の Issue の 2 行が、本文の推奨・選んでほしいことと同じか** | 書いた側が揃える（`absent-lines.md`）。ここは行を読むだけ |
| **機能の `qa` とケースの `qa` の両方が指す No で、機能全体が作り直しになるか** | 本文の `## Q&A の回答` は両方を合わせて持つので見分けられない。ケースが指していればケースを挙げる——Issue は挙がるので、範囲を広げるかは読む人が本文で決める |
| **まとめた本文の部分が、機能 1 件の本文と同じ形か** | 部分の頭の機能の印の行で分けるだけ。同じ Issue の部分は、作り直す範囲の行に部分ごとに（機能の id を添えて）出る |
| **本文を手で直した Issue** | 本文は手で直さない決まり（`handoff-issue.md`）。直されていれば、読めた分だけを引く |
| **確認の結果の行を誰が書いたか・閉じたかと結果の行が合っているか** | 行を読むだけ。開いたままの Issue に結果の行があれば、そのまま出す（状態は題の後ろに添える）。利用者が閉じたかは cruise の `SKILL.md` §6 の閉じ方の判定が見る |
| **装飾を付けた・文の途中の結果の行** | 行頭が `確認の結果: ` の行だけを読む（台帳の 2 行と同じ決まり）。それ以外は「結果なし」と出る |
| **`gh` が返さなかったコメント** | 入力にあるコメントだけを読む。コメントの多い Issue で `gh issue list` が全部を返すかは確かめていない |
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scaffold = _load("scaffold", "scaffold.py")
qa = scaffold.qa

# 確認の Issue の台帳の 2 行の頭（dev-loop の `references/absent-lines.md` の「確認の Issue の書き方」の写し）と、その Issue の見分け方
DECIDED = "決めた値: "
AFFECTS = "影響する Issue: "
DECISION_MARKER = re.compile(r"<!-- cruise-decision: #[0-9]+ -->")
DECISION_TITLE = "要確認: "
NONE = "なし"
AFFECTS_LIST = re.compile(r"#[1-9][0-9]*(?:, #[1-9][0-9]*)*")
# 閉じるときの結果の 1 行の頭と値（同じ「確認の Issue の書き方」の「閉じるときの結果の 1 行」の写し。#884）
RESULT = "確認の結果: "
KEPT = "推奨のまま"
CHANGED = "変えた: "

HANDOFF_PREFIX = scaffold.HANDOFF_MARKER.split(": v", 1)[0] + ": v"  # 前の形（v2・v1）も読む
FEATURE = re.compile(re.escape(scaffold.FEATURE_MARKER).replace(r"\{\}", r"(F-[0-9]+)"))
# まとめた本文の印（2 行目）と、部分の頭の機能の印の行——印の定数は `scaffold.py` のものを読む（写さない）
BUNDLE = re.compile(re.escape(scaffold.BUNDLE_MARKER).replace(r"\{\}", r"F-[0-9]+(?:・F-[0-9]+)+"))
FEATURE_LINE = re.compile("^" + FEATURE.pattern + r"\r?$", re.M)
REMOVAL = re.compile(re.escape(scaffold.CHANGE_MARKER).replace(r"\{\}", scaffold.REMOVE, 1).replace(r"\{\}", r"[^ >]*", 1))
ROW = re.compile(r"^\| `([^`]+)` \|.*\| ([^|]*) \|$")
QA_ROW = re.compile(r"^\| ([QD]-[^ |]+) \|")


class Bad(Exception):
    """判定していない（2）。"""


def section(body: str, heading: str) -> str:
    """`heading` の節の中身（次の `## ` まで）。無ければ空。"""
    lines = body.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return ""
    out = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out)


def is_number(text: str) -> bool:
    return bool(qa.NUMBER.fullmatch(text) or qa.is_internal_number(text))


def parts(body: str) -> list[str]:
    """機能ごとの部分。まとめた本文（#876。2 行目が `scaffold.BUNDLE_MARKER` の印）なら機能の印の行ごとに分け、そうでなければ本文 1 つ。

    部分は機能 1 件の本文から 1 行目を外したもので、同じ節を持つ（`references/handoff-issue.md` の「まとめた本文」）。
    """
    lines = body.splitlines()  # 改行が `\r\n` でも分ける（GitHub が改行を `\r\n` にして返しうる）
    if len(lines) < 2 or not BUNDLE.fullmatch(lines[1]):
        return [body]
    starts = [m.start() for m in FEATURE_LINE.finditer(body)]
    return [body[a:b] for a, b in zip(starts, starts[1:] + [len(body)])] or [body]


class Handoff:
    """spec-loop から渡した Issue の、機能 1 件分（まとめた本文なら部分 1 つ）の Q&A への依存。"""

    def __init__(self, issue: dict, body: str | None = None) -> None:
        body = issue["body"] if body is None else body
        found = FEATURE.search(body)
        self.issue = issue
        self.feature = found.group(1) if found else "?"
        self.cases: dict[str, list[str]] = {}  # No → それを根拠にするケース
        self.held: set[str] = set()  # 仮回答の印を付けた No
        for line in section(body, scaffold.SECTIONS[1]).splitlines():
            row = ROW.match(line)
            if not row:
                continue
            for raw in row.group(2).split("・"):
                text = raw.strip()
                if text.endswith(scaffold.PROVISIONAL_CELL):
                    text = text[: -len(scaffold.PROVISIONAL_CELL)]
                    self.held.add(text)
                if is_number(text):
                    self.cases.setdefault(text, []).append(row.group(1))
        for line in section(body, scaffold.SECTIONS[0]).splitlines():
            if line.startswith(scaffold.PROVISIONAL_LINE):
                listed = line[len(scaffold.PROVISIONAL_LINE):].split("（", 1)[0]
                self.held |= {no.strip() for no in listed.split("・") if is_number(no.strip())}
        self.refs = {m.group(1) for line in section(body, scaffold.SECTIONS[3]).splitlines()
                     if (m := QA_ROW.match(line)) and is_number(m.group(1))}
        self.refs |= set(self.cases) | self.held


class Decision:
    """確認の Issue 1 件の、台帳の 2 行。"""

    def __init__(self, issue: dict) -> None:
        self.issue = issue
        self.value: str | None = None
        self.affects: list[int] | None = None
        self.malformed: str | None = None  # 台帳の行が決まりの形でない（その行の中身。空の行も形に反する）
        for line in issue["body"].splitlines():
            if line.startswith(DECIDED) and self.value is None and self.malformed is None:
                self.value = line[len(DECIDED):].strip()
                if not self.value:
                    self.value, self.malformed = None, line  # 空の行は「無い」ではなく形に反する（2 パス目の指摘）
            elif line.startswith(AFFECTS) and self.affects is None and self.malformed is None:
                rest = line[len(AFFECTS):].strip()
                # 番号だけを `, ` で並べる（説明を添えない）か `なし`——説明の中の番号を影響する Issue に数えない（1 パス目の指摘）
                if rest == NONE:
                    self.affects = []
                elif AFFECTS_LIST.fullmatch(rest):
                    self.affects = [int(n) for n in re.findall(r"#([0-9]+)", rest)]
                else:
                    self.malformed = line
        # 閉じのコメントの結果の行（#884）。コメントの最後の結果の行を採る——開き直して変えたら後のコメントが上書きする
        self.result: str | None = None  # `推奨のまま` か `変えた: <値>`。None は結果なし
        self.result_malformed: str | None = None  # 最後の結果の行が決まりの形でない（その行）
        comments = issue.get("comments")
        self.comments_read = comments is not None  # 鍵が無ければ読んでいない（「結果なし」と言わない）
        for comment in comments or []:
            for line in comment["body"].splitlines():
                if not line.startswith(RESULT.rstrip()):  # 頭の後ろの空白が無い行（`確認の結果:変えた: X`）も、形に反する行として拾う（2 パス目の指摘）
                    continue
                rest = line[len(RESULT):].strip() if line.startswith(RESULT) else ""
                value = rest[len(CHANGED):]
                # 空の `変えた: ` は strip で `変えた:` になり、形に反する。写す前の `<新しい値>` のままの行も形に反する（2 パス目の指摘）
                if rest == KEPT or (rest.startswith(CHANGED) and not (value.startswith("<") and value.endswith(">"))):
                    self.result, self.result_malformed = rest, None
                else:
                    self.result, self.result_malformed = None, line

    def changed(self) -> bool:
        return self.result is not None and self.result.startswith(CHANGED)

    def outcome(self) -> str:
        """確認の結果を 1 句で。"""
        if not self.comments_read:
            return "読んでいない（入力に comments が無い——取り方の 1 行に comments を足す）"
        if self.result_malformed is not None:
            return f"結果の行が決まりの形でない（{self.result_malformed!r}）"
        return self.result or "結果なし（まだ確かめていないか、結果の行を残さずに閉じた）"


def is_decision(issue: dict) -> bool:
    return bool(DECISION_MARKER.search(issue["body"])) or issue["title"].startswith(DECISION_TITLE)


def read_issues(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Bad(f"{path}: 読めない（{exc.__class__.__name__}: {exc}）")
    if not isinstance(data, list):
        raise Bad(f"{path}: Issue の配列でない（gh issue list --json number,title,state,body,comments の出力を渡す）")
    for index, issue in enumerate(data):
        if not (isinstance(issue, dict) and type(issue.get("number")) is int and isinstance(issue.get("title"), str)
                and isinstance(issue.get("body"), str) and isinstance(issue.get("state", ""), str)):
            raise Bad(f"{path}: {index} 番目が Issue の形でない（number・title・body・state を取る）")
        comments = issue.get("comments", [])
        if not (isinstance(comments, list) and all(isinstance(c, dict) and isinstance(c.get("body"), str) for c in comments)):
            raise Bad(f"{path}: {index} 番目の comments が、本文（body）を持つコメントの配列でない")
    return data


def label(issue: dict) -> str:
    state = issue.get("state") or "状態不明"
    return f"#{issue['number']} {issue['title']} [{state}]"


def by_qa(no: str, handoffs: list[Handoff]) -> tuple[bool, list[str]]:
    hits = [h for h in handoffs if no in h.refs]
    if not hits:
        return False, [f"{no}: 根拠にした spec-loop の Issue が無い（入力の Issue の本文のどれも、この No を挙げていない）"]
    held = any(no in h.held for h in hits)
    out = [f"{no}{'（仮回答——本文に印がある）' if held else ''}: 作り直す範囲 {len(hits)} 件"]
    for h in sorted(hits, key=lambda h: h.issue["number"]):
        cases = h.cases.get(no)
        where = "受入基準 " + "・".join(f"`{c}`" for c in cases) if cases else "ケースに無い（機能全体）"
        out.append(f"  - {label(h.issue)}（{h.feature}）——{where}")
    return True, out


def by_issue(number: int, issues: dict[int, dict]) -> tuple[bool, list[str]]:
    issue = issues.get(number)
    if issue is None:
        return False, [f"#{number}: 入力に無い（取り方の --limit・--state all を確かめる）"]
    if not is_decision(issue):
        return False, [f"#{number}: 確認の Issue でない（印 <!-- cruise-decision: #<親> --> も、題の {DECISION_TITLE!r} も無い）"]
    d = Decision(issue)
    out = [label(issue), f"  {RESULT}{d.outcome()}"]
    if d.malformed is not None:
        return False, out + [f"  台帳の行が決まりの形でない（{d.malformed!r}）——`{DECIDED}<値>` と、`{AFFECTS}` には"
                             f" `#<番号>, #<番号>` か `{NONE}` だけを書く"]
    if d.value is None or d.affects is None:
        missing = "・".join(t.strip() for t, v in ((DECIDED, d.value), (AFFECTS, d.affects)) if v is None)
        return False, out + [f"  台帳の行（{missing}）が無い——この決まりより前の書き方。本文の ## 出所 を人が読む"]
    out.append(f"  {DECIDED}{d.value}")
    out.append(f"  {AFFECTS}" + ("なし" if not d.affects else f"{len(d.affects)} 件（作り直す範囲）"))
    absent = [n for n in d.affects if n not in issues]
    for n in d.affects:
        target = issues.get(n)
        out.append(f"  - {label(target) if target else f'#{n}（入力に無い——取り方の --limit・--state all を確かめる）'}")
    # 影響する Issue が入力に無ければ、範囲を引ききれていない（1 パス目の指摘）。結果の行が形に反するなら、結果を引けていない
    return not absent and d.result_malformed is None, out


def ledger(handoffs: list[Handoff], decisions: list[Decision]) -> list[str]:
    held: dict[str, list[Handoff]] = {}
    for h in handoffs:
        for no in h.held:
            held.setdefault(no, []).append(h)
    out = [f"仮回答（本文に仮回答の印がある Q&A）: {len(held)} 件"]
    for no in sorted(held, key=lambda n: qa.number_order(n) if is_number(n) else (True, 99, 0)):
        out.append(f"  {no}: " + "、".join(f"#{h.issue['number']}（{h.feature}）" for h in
                                            sorted(held[no], key=lambda h: h.issue["number"])))
    opened = sum(1 for d in decisions if (d.issue.get("state") or "").upper() == "OPEN")
    out.append(f"推奨で決めた事項（確認の Issue）: {len(decisions)} 件（開いているもの {opened} 件・変えたもの "
               f"{sum(1 for d in decisions if d.changed())} 件）")
    for d in sorted(decisions, key=lambda d: d.issue["number"]):
        out.append(f"  {label(d.issue)}——{entry(d)}／{RESULT}{d.outcome()}")
    return out


def entry(d: Decision) -> str:
    """台帳の 2 行を 1 句で。"""
    if d.malformed is not None:
        return "台帳の行が決まりの形でない"
    if d.value is None or d.affects is None:
        return "台帳の行が無い（前の書き方）"
    return f"{DECIDED}{d.value}／{AFFECTS}" + ("、".join(f"#{n}" for n in d.affects) or "なし")


def changed(decisions: list[Decision], issues: dict[int, dict]) -> tuple[bool, list[str], list[str]]:
    """確認の結果が `変えた` の確認の Issue だけ。引ききれない確認の Issue は名指しする（引けたか, 出力, 名指し）。

    名指しするのは、結果を読んでいない・結果の行が形に反する・閉じたのに結果の行が無い（変えたかもしれない）確認の Issue と、
    変えた確認の Issue のうち台帳の行が無い・形に反する・影響する Issue が入力に無いもの（作り直す範囲を引ききれていない。1 パス目の指摘）。
    """
    ordered = sorted(decisions, key=lambda d: d.issue["number"])
    hits = [d for d in ordered if d.changed()]
    out = [f"変わった確認（{RESULT}{CHANGED.rstrip(': ')}）: {len(hits)} 件"]
    for d in hits:
        out.append(f"  {label(d.issue)}——{entry(d)}／{RESULT}{d.result}")
    bad = []
    for d in ordered:
        closed = (d.issue.get("state") or "").upper() == "CLOSED"
        if not d.comments_read or d.result_malformed is not None:
            bad.append(f"{label(d.issue)}: {RESULT}{d.outcome()}")
        elif closed and d.result is None:
            bad.append(f"{label(d.issue)}: 閉じたが {RESULT}の行が無い（変えたかを読めない）")
        elif d.changed() and (d.malformed is not None or d.value is None or d.affects is None):
            bad.append(f"{label(d.issue)}: {entry(d)}（作り直す範囲を引けない）")
        elif d.changed() and (absent := [n for n in d.affects if n not in issues]):
            bad.append(f"{label(d.issue)}: 影響する Issue " + "・".join(f"#{n}" for n in absent) + " が入力に無い（取り方の --limit・--state all を確かめる）")
    return not bad, out, bad


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--issues", required=True)
    parser.add_argument("--changed", action="store_true")
    parser.add_argument("keys", nargs="*")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2
    keys = []
    for key in args.keys:
        if is_number(key):
            keys.append(key)
        elif re.fullmatch(r"#?[1-9][0-9]*", key):
            keys.append(int(key.lstrip("#")))
        else:
            print(f"{key!r}: Q&A の No（Q-R-002・D-S-001）か Issue の番号（#12）でない。判定していない", file=sys.stderr)
            return 2
    if args.changed and args.keys:
        print("--changed は Q&A の No・Issue の番号と一緒には渡せない。判定していない", file=sys.stderr)
        return 2
    try:
        issues = read_issues(Path(args.issues))
    except Bad as exc:
        print(f"{exc}。判定していない", file=sys.stderr)
        return 2
    # 撤去の Issue は作り直す範囲に数えない——作るものが無い（2 パス目の指摘）
    handoffs = [Handoff(i, part) for i in issues if i["body"].startswith(HANDOFF_PREFIX) and not REMOVAL.search(i["body"])
                for part in parts(i["body"])]
    decisions = [Decision(i) for i in issues if is_decision(i)]
    if args.changed:
        ok, out, bad = changed(decisions, {i["number"]: i for i in issues})
        for line in out:
            print(line)
        for line in bad:
            print(f"引けない——{line}", file=sys.stderr)
        return 0 if ok else 1
    if not keys:
        for line in ledger(handoffs, decisions):
            print(line)
        return 0
    by_number = {i["number"]: i for i in issues}
    code = 0
    for key in keys:
        ok, lines = by_qa(key, handoffs) if isinstance(key, str) else by_issue(key, by_number)
        for line in lines:
            print(line, file=sys.stdout if ok else sys.stderr)
        code = code or (0 if ok else 1)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「判定していない」（2）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。判定していない", file=sys.stderr)
        sys.exit(2)
