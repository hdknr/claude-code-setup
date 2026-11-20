#!/usr/bin/env python3
"""委譲文の各行が「最後に効いた周」を計画ファイルから引き、外す候補を根拠つきで並べる（#1194）。

    python3 line-effects.py check  [--registry <台帳>]
    python3 line-effects.py items  [--registry <台帳>]
    python3 line-effects.py report <計画ファイルかディレクトリ> [...] [--registry <台帳>] [--window <周数>]

`prompts/*.md`（委譲文）は事故のたびに行が増える。行を外す条件も見直す段も無かったので、**行ごとに最後に効いた周を引けるようにし、
効いていない行を候補に挙げる**（手順・承認・eval の決まりは `references/prune.md` が原本）。**測るだけで、削る判断はしない**——
外すのは人間の承認つきの PR でだけで、その PR の歯止めはこのリポジトリの `scripts/check-prompt-lines.py` が見る。

## 台帳（`references/line-registry.csv`。ここが原本）

1 行 1 項。ヘッダは次の順:

    ID,ファイル,引き,元の事故,登録日,同趣旨,統合元

- **ID**: `V-01` の形（英大文字 1〜3 字・`-`・数字 2 桁以上）。**再利用しない**（外した行の ID は計画ファイルの記録に残る）。
- **ファイル**: このスキルのディレクトリからの相対パス（`prompts/verifier.md` など）。
- **引き**: そのファイルの中に**ちょうど 1 回**現れる原文の一部。**`prompts/` の行は項の頭**（引き）で始まる項に当たること。
- **元の事故**: 行ができた事故の Issue 番号（`#233;#96`）。分からなければ `-`。**初期値は項の本文に現れた番号を機械で写したもので、事故の番号とは限らない**。
- **登録日**: `YYYY-MM-DD`。この日以降の周だけを「効いていない周」に数える。
- **同趣旨**: 同じ趣旨の行に共通の短い語（空でよい）。2 行以上が共有すれば、まとめる候補に出す。
- **統合元**: この行に統合して台帳から外した行の ID（`;` 区切り。空でよい）。

**項**とは、`prompts/*.md` の最初の `---` 以降の、行頭が `数字. ` か `- ` の行（コードブロックの外。`{{` で始まる差し込みの穴は数えない）。
**`prompts/` の項はすべて台帳に載っていなければならない**（`check` が見る）。`SKILL.md` の行は載せたいものだけ載せる。

## 記録（計画ファイル）

周が行頭から装飾なしで 1 行 1 項に書く（書き方は `references/prune.md`）:

    - 効いた行: V-05
    - 効いた行: V-05（指摘の一言）
    - 効いた行: なし

`なし` と ID は 1 ファイルに混ぜない。コードブロックの中は読まない。**1 行でも書いた計画ファイルを「記録のある周」と数える**（書いていない周は分母に入れない）。
周の順は、計画ファイルを最初に追加したコミットの時刻（履歴に無ければ最新）。

## 終了コード

- **0**: 判定した（候補が出ても 0）。
- **1**: 台帳と原文が食い違う・未登録の項がある（`check`）／形に合わない記録の行がある（`report`）——名指しする。
- **2**: 判定していない——引数の誤り・読めない・台帳の形が違う・計画ファイルが 1 本も無い。

## 守らないもの

- **申告の漏れ**——周が書き忘れた「効いた」は数えられない（記録のある周だけが分母）。
- **どの行が効いたかの判断**——周の著者が採否の表から書く。機械は照合しない。
- **既存の計画ファイル**——この台帳より前の周には行が無い。効いていない周数は、記録が貯まってからしか出ない。
- **eval の結果**——外す PR に eval を付ける決まりは `check-prompt-lines.py` が「在ること」を見るだけで、通ったかは見ない（課金する）。
"""
from __future__ import annotations

import csv
import datetime
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = SKILL / "references" / "line-registry.csv"
HEADER = ["ID", "ファイル", "引き", "元の事故", "登録日", "同趣旨", "統合元"]
ID_RE = re.compile(r"^[A-Z]{1,3}-[0-9]{2,}$")
ITEM_RE = re.compile(r"^(?:[0-9]+\. |- )")
RECORD_RE = re.compile(r"^- 効いた行: (?:(?P<none>なし)|(?P<id>[A-Z]{1,3}-[0-9]{2,}))(?P<rest>$|[ （(].*$)")
LABEL_RE = re.compile(r"^[\s>*#\-0-9.\[\]xX)]*(?:\*\*|__|`)*効いた行")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
DEFAULT_WINDOW = 30
USAGE = ("usage: line-effects.py check|items [--registry R] | "
         "report <計画ファイルかディレクトリ>... [--registry R] [--window N]")


class Fail(Exception):
    """終了コード 2（判定していない）。"""


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Fail(f"{path} を読めない: {e}")


def outside_fences(text: str):
    """(行番号 1 始まり, 行) をコードブロックの外だけ出す。開きの印は字下げを外して見る。"""
    fence = None
    for n, line in enumerate(text.split("\n"), 1):
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
                continue
            yield n, line
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and line.strip() == m.group(1):
                fence = None


def load_registry(path: Path) -> list[dict]:
    text = read(path)
    rows = list(csv.reader(text.splitlines()))
    if not rows or rows[0] != HEADER:
        raise Fail(f"{path} のヘッダが `{','.join(HEADER)}` でない")
    out = []
    seen = set()
    for n, r in enumerate(rows[1:], 2):
        if not r:
            continue
        if len(r) != len(HEADER):
            raise Fail(f"{path}:{n} 列の数が {len(HEADER)} でない（{len(r)}）")
        d = dict(zip(HEADER, r))
        if not ID_RE.match(d["ID"]):
            raise Fail(f"{path}:{n} ID `{d['ID']}` の形が違う")
        if d["ID"] in seen:
            raise Fail(f"{path}:{n} ID `{d['ID']}` が重複している")
        seen.add(d["ID"])
        try:
            datetime.date.fromisoformat(d["登録日"])
        except ValueError:
            raise Fail(f"{path}:{n} 登録日 `{d['登録日']}` が YYYY-MM-DD でない")
        if not d["ファイル"] or not d["引き"]:
            raise Fail(f"{path}:{n} ファイルか引きが空")
        if d["ファイル"].startswith("/") or ".." in Path(d["ファイル"]).parts:
            raise Fail(f"{path}:{n} ファイル `{d['ファイル']}` がスキルのディレクトリの外")
        d["_line"] = n
        out.append(d)
    return out


def items_of(text: str) -> list[tuple[int, str, str]]:
    """`prompts/` の項: (行番号, 項の頭の文面, 項の本文)。最初の `---` の後ろ・コードブロックの外・行頭が `数字. ` か `- ` で、`{{` で始まる穴を除く。"""
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if l.rstrip() == "---"), None)
    if start is None:
        return []
    heads = []
    for n, line in outside_fences("\n".join(lines[start + 1:])):
        n += start + 1
        m = ITEM_RE.match(line)
        if m and not line[m.end():].startswith("{{"):
            heads.append((n, line[m.end():]))
    blocks = []
    for k, (n, first) in enumerate(heads):
        end = heads[k + 1][0] - 1 if k + 1 < len(heads) else len(lines)
        blocks.append((n, first, "\n".join(lines[n - 1:end])))
    return blocks


def check(registry: Path) -> list[str]:
    rows = load_registry(registry)
    problems = []
    by_file: dict[str, list[dict]] = {}
    for r in rows:
        by_file.setdefault(r["ファイル"], []).append(r)
        for src in filter(None, r["統合元"].split(";")):
            if not ID_RE.match(src):
                problems.append(f"{registry.name}:{r['_line']} 統合元 `{src}` が ID の形でない")
            elif any(x["ID"] == src for x in rows):
                problems.append(f"{registry.name}:{r['_line']} 統合元 `{src}` が台帳に残っている（外してから書く）")
    for rel, rs in by_file.items():
        text = read(SKILL / rel)
        for r in rs:
            n = text.count(r["引き"])
            if n != 1:
                problems.append(f"{r['ID']}: 引き「{r['引き']}」が {rel} に {n} 回ある（ちょうど 1 回でなければならない）")
        if rel.startswith("prompts/"):
            its = items_of(text)
            for r in rs:
                if not any(first.startswith(r["引き"]) for _, first, _ in its):
                    problems.append(f"{r['ID']}: 引き「{r['引き']}」が {rel} の項の頭に当たらない")
    for p in sorted((SKILL / "prompts").glob("*.md")):
        rel = f"prompts/{p.name}"
        for n, first, _ in items_of(read(p)):
            if not any(first.startswith(r["引き"]) for r in by_file.get(rel, [])):
                problems.append(f"{rel}:{n} 台帳に無い項「{first[:30]}」（`items` で登録行の案を出せる）")
    return problems


def suggest(registry: Path) -> list[list[str]]:
    rows = load_registry(registry) if registry.exists() else []
    by_file: dict[str, list[dict]] = {}
    for r in rows:
        by_file.setdefault(r["ファイル"], []).append(r)
    ids = {r["ID"] for r in rows}
    today = datetime.date.today().isoformat()
    out = []
    for p in sorted((SKILL / "prompts").glob("*.md")):
        rel = f"prompts/{p.name}"
        prefix = {"verifier": "V", "implementer": "I", "review-handoff": "R"}.get(p.stem, p.stem[:1].upper())
        text = read(p)
        k = 0
        for n, first, block in items_of(text):
            if any(first.startswith(r["引き"]) for r in by_file.get(rel, [])):
                continue
            while True:
                k += 1
                new_id = f"{prefix}-{k:02d}"
                if new_id not in ids:
                    break
            ids.add(new_id)
            length = 24
            while length <= len(first) and text.count(first[:length]) != 1:
                length += 4
            nums = sorted({int(x) for x in re.findall(r"#([0-9]+)", block)})
            out.append([new_id, rel, first[:length], ";".join(f"#{x}" for x in nums) or "-", today, "", ""])
    return out


def plan_files(args: list[str]) -> list[Path]:
    files: list[Path] = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            files += sorted(p.rglob("*.md"))
        elif p.is_file():
            files.append(p)
        else:
            raise Fail(f"{a} が無い")
    seen, out = set(), []
    for f in files:
        key = f.resolve()
        if key not in seen:
            seen.add(key)
            out.append(f)
    if not out:
        raise Fail("計画ファイル（*.md）が 1 本も無い")
    return out


def added_at(path: Path) -> int | None:
    """計画ファイルを最初に追加したコミットの時刻（epoch）。履歴に無ければ None。"""
    try:
        r = subprocess.run(["git", "-C", str(path.resolve().parent), "log", "--diff-filter=A", "--format=%ct",
                            "--", str(path.resolve())], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    ts = [x for x in r.stdout.split() if x.isdigit()]
    return int(ts[-1]) if r.returncode == 0 and ts else None


def parse_plan(path: Path):
    """(記録の ID の集合 or None（記録なし）, 形に合わない行の名指し)。"""
    ids: list[str] = []
    none = False
    bad = []
    for n, line in outside_fences(read(path)):
        m = RECORD_RE.match(line)
        if m:
            if m.group("none"):
                none = True
            else:
                ids.append(m.group("id"))
        elif LABEL_RE.match(line):
            bad.append(f"{path}:{n} 記録の行の形でない「{line[:40]}」")
    if none and ids:
        bad.append(f"{path} `なし` と ID を同じファイルに書いている")
    if not ids and not none:
        return None, bad
    return set(ids), bad


def report(files: list[Path], registry: Path, window: int) -> int:
    rows = load_registry(registry)
    cycles = []
    unrecorded = 0
    bad: list[str] = []
    for f in files:
        ids, b = parse_plan(f)
        bad += b
        if ids is None:
            unrecorded += 1
            continue
        ts = added_at(f)
        cycles.append((ts if ts is not None else float("inf"), f.name, ids, ts))
    cycles.sort(key=lambda c: (c[0], c[1]))
    print(f"記録のある周: {len(cycles)}（記録の行が無い計画ファイル: {unrecorded}）／窓: {window} 周")
    known = {r["ID"] for r in rows}
    unknown = sorted({i for c in cycles for i in c[2]} - known)
    stats = []
    for r in rows:
        eff = [c for c in cycles if r["ID"] in c[2]]
        last = eff[-1] if eff else None
        def eligible(c):
            return c[3] is None or datetime.datetime.fromtimestamp(c[3], datetime.timezone.utc).date().isoformat() >= r["登録日"]
        el = [c for c in cycles if eligible(c)]
        if last is None:
            since = len(el)
        else:
            since = sum(1 for c in el if (c[0], c[1]) > (last[0], last[1]))
        stats.append((r, len(eff), last, since))
    print("\nID\t効いた周数\t最後に効いた周\t効いていない周数\t元の事故\tファイル\t引き")
    for r, n, last, since in stats:
        print(f"{r['ID']}\t{n}\t{last[1] if last else '-'}\t{since}\t{r['元の事故']}\t{r['ファイル']}\t{r['引き']}")
    cand = [s for s in stats if s[3] >= window]
    print(f"\n外す候補（効いていない周数 >= {window}。削る判断は人間——手順は references/prune.md）: {len(cand)} 件")
    for r, n, last, since in cand:
        basis = (f"最後に効いた周 {last[1]} の後、記録のある {since} 周で効いていない" if last
                 else f"登録日 {r['登録日']} 以降の記録のある {since} 周で 0 回")
        print(f"  {r['ID']}（{r['ファイル']}「{r['引き']}」）元の事故 {r['元の事故']} — {basis}")
    groups: dict[str, list[str]] = {}
    for r in rows:
        if r["同趣旨"]:
            groups.setdefault(r["同趣旨"], []).append(r["ID"])
    merge = {k: v for k, v in groups.items() if len(v) >= 2}
    print(f"\nまとめる候補（同趣旨が 2 行以上）: {len(merge)} 組")
    for k, v in sorted(merge.items()):
        print(f"  {k}: {' '.join(v)}")
    if unknown:
        print(f"\n台帳に無い ID（外した行か綴りの誤り）: {' '.join(unknown)}")
    if bad:
        print("\n形に合わない記録:")
        for b in bad:
            print(f"  {b}")
        return 1
    return 0


def main(argv: list[str]) -> int:
    sys.dont_write_bytecode = True
    args = list(argv)
    registry = DEFAULT_REGISTRY
    window = DEFAULT_WINDOW
    rest: list[str] = []
    try:
        while args:
            a = args.pop(0)
            if a in ("--registry", "--window"):
                if not args:
                    raise Fail(f"{a} に値が無い")
                v = args.pop(0)
                if a == "--registry":
                    registry = Path(v)
                else:
                    if not v.isdigit() or int(v) < 1:
                        raise Fail("--window は 1 以上の整数")
                    window = int(v)
            else:
                rest.append(a)
        if not rest or rest[0] not in ("check", "items", "report"):
            raise Fail(USAGE)
        cmd, targets = rest[0], rest[1:]
        if cmd != "report" and targets:
            raise Fail(USAGE)
        if cmd == "check":
            problems = check(registry)
            for p in problems:
                print(f"NG: {p}")
            print(f"{'NG' if problems else 'OK'}: 台帳 {len(load_registry(registry))} 行・問題 {len(problems)} 件")
            return 1 if problems else 0
        if cmd == "items":
            w = csv.writer(sys.stdout, lineterminator="\n")
            for row in suggest(registry):
                w.writerow(row)
            return 0
        if not targets:
            raise Fail(USAGE)
        return report(plan_files(targets), registry, window)
    except Fail as e:
        print(f"line-effects.py: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
