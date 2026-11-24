#!/usr/bin/env python3
"""dev-loop の委譲文の行の台帳と、行を外す PR の eval を検査する（#1194）。

usage: python3 scripts/check-prompt-lines.py <base-ref>

CI（.github/workflows/plugins.yml）が PR で呼ぶ。ローカルでも実行できる: `python3 scripts/check-prompt-lines.py origin/main`

決まりの原本は `plugins/dev-loop/skills/dev-loop/references/prune.md`。見るのは 2 つ:

1. **台帳と原文の整合**——プラグインの `scripts/line-effects.py check` と同じ判定（読み込んで呼ぶ。式を写さない）。
   `prompts/*.md` の項が台帳に無い・引きが原文に 1 回でない・台帳の行の引きが項の頭に当たらない、は 1。
2. **台帳から行を外す PR は、その行の元の事故を再現する eval を付ける**——base の台帳にあって HEAD に無い行（外した行）ごとに、
   `base...HEAD` の差分に含まれる `plugins/dev-loop/evals/*/case.yaml` のうち、次を満たすものが 1 つ要る:
   - コメント行 `# 外した行: <ID>`（そのケースが再現する行）と `# 元の事故: <番号>`（base の台帳の `元の事故` が `-` でなければ、その番号が全部入っていること。
     `-` なら何か書いてあればよい）がある
   - **`graders:` のブロック（次の最上位のキーまで）の中に** `- name:` が 1 つ以上ある
   **ただし、HEAD の台帳の別の行の `統合元` に挙がり、その行が base にも在って、同じファイルで、同じ `同趣旨`（空でない）を持っていた行は、統合なので eval を求めない**
   （同じ受け手の文面に同じ趣旨の行が残るため）。
3. **生き残る行の ID のファイルを変えない**（別の受け手の文面へ移さない）。**ただし base から作業ツリーまでの差分で git が改名と見たファイル（`git diff -M`）は同じファイルと読む**（#1423 の R1。
   中身を大きく変えて改名と見られなかったもの・索引に載せていない新しいファイルは「ファイルを変えた」で 1 のまま——止まる向き）。
   **ID を別の既存の項に付け替えない**——base と HEAD の両方にある ID の引きが変わったら、次のどちらかで 1:
   - 新しい引きが、**HEAD に項の頭のまま残る** base の別の項の頭に前方一致する（言い換えない付け替え）。HEAD に残った頭だけを照らすので、
     同じ PR で外した別の項の base の頭に縮めた引きが前方一致しても 1 にしない（#1423 の S5）。
   - HEAD でその引きが当たる項（頭の行と、その下の字下げした行。字下げの無い行で切る）に、飾り（`*`・`_`・`` ` ``）と空白を除いた形で**元の項の頭が残らず**、
     base の別の項の頭が入っている——付け替え先の項を同じ PR で言い換えても当たる（#1423 の S1・S2）。
   元の項の頭が残る言い換え（頭の飾りを外す・本文の文を頭に上げる・頭を縮める）は通る。後者の照らしでは、**その ID の `統合元` に挙がった行の項の頭**（統合で取り込んだ文面）と、
   **元の項が base の時点から本文（字下げした行）で引いていた別の項の頭のうち、新しい引きの項がその引用を受け継ぐもの**は照らさない
   （前者は統合の言い換え、後者は同じ項の頭の言い換えを付け替えと見ないため）。**引用を受け継ぐ**とは、元の項の行（行頭の `-`・`1.` などの印を除き、飾りと空白を除いた形）の
   その頭の引用の前か後ろの文面が、頭と続いたまま新しい引きの項に残ること——本文をそのまま残す・引いた文を頭の行に上げる・引用の片側を言い換える言い換えは照らさない。
   引いた先の項が HEAD に頭のまま残るかは見ないので、**同じ PR で引いた先の項の頭も言い換え、本文に引いた先の古い頭を残す言い換えも 0**（#1453）。
   **引用を受け継がずに頭の文面だけが残る形は照らす**——元の項を消し、本文で引いていた項の頭を言い換えて（飾りを外す・前置きを足す・後ろを延ばす・
   字下げした行へ折り返す・新しい頭を置いて元の頭を本文に下ろす）ID を付け替える形（#1430）と、元の項をその頭を写した新しい項（`要点: <頭>` など）に差し替えて
   ID を付け替える形（#1452。付け替え先の項が HEAD に残っていても）を止める。元の項の行が引いた頭だけ（前にも後ろにも文面が無い）なら、受け継いだと見ない（止まる向き）。
   **項を本文ごと別の新しい文面に差し替えて ID を付け替える形のうち、引いた先の頭を持たないもの・付け替え先の頭も言い換えたうえで元の項の頭の文面をその字下げした行か字下げの無い続きの行に写して付け替える形・
   元の項の引用の行の前後の文面を新しい項に写して付け替える形は見ない**（守られているのは項の頭だけ）。

## 守らないもの

- **eval が元の事故を実際に再現するか・外した後も通るか**——見るのは eval が差分に在って名指しが揃うことだけ（`claude plugin eval` は課金し、CI から呼ばない）。
  通ったことは PR に `run-dev-loop-evals.py` の要約を貼って人間が見る（`references/prune.md`）。
- **承認**——外す PR を人間が承認したかは見ない。
- **台帳の無い base**（導入の PR）——外した行が定義できないので 2 を飛ばす。
- **改名と同じ PR で受け手を変えること**——改名を同じファイルと読むのは、SKILL.md がそのファイルを渡す体を変えていないと仮定してである（SKILL.md の参照の変化は見ない）。

## 終了コード

0: 問題なし／1: 上の違反／2: 判定していない（base を解決できない・台帳を読めない）。
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_REL = "plugins/dev-loop/skills/dev-loop"
REGISTRY_REL = f"{SKILL_REL}/references/line-registry.csv"
EVALS_REL = "plugins/dev-loop/evals"


def load_effects(root: Path):
    path = root / SKILL_REL / "scripts" / "line-effects.py"
    spec = importlib.util.spec_from_file_location("dev_loop_line_effects", path)
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def parse_registry_text(effects, text: str) -> list[dict]:
    """base の台帳（git show の文字列）を読む。形は line-effects.py の `load_registry` と同じ——一時ファイルに書かずに読むため、csv だけ使う。"""
    import csv
    rows = list(csv.reader(text.splitlines()))
    if not rows or rows[0] != effects.HEADER:
        raise ValueError("base の台帳のヘッダが違う")
    return [dict(zip(effects.HEADER, r)) for r in rows[1:] if len(r) == len(effects.HEADER)]


def flat(text: str) -> str:
    """項の頭と項を照らす形——飾り（`*`・`_`・`` ` ``）と空白（改行を含む）を除く。頭の飾りを外す・本文の文を頭に上げる言い換えでも、元の頭の文面が残る。"""
    return re.sub(r"[\s*_`]+", "", text)


def own_lines(body: str) -> str:
    """項の頭の行と、その下の字下げした行（と空行）だけ。字下げの無い行（段落・見出し・コードブロック・別の印の項）で切る。"""
    lines = body.split("\n")
    out = lines[:1]
    for line in lines[1:]:
        if line.strip() and not line[:1].isspace():
            break
        out.append(line)
    return "\n".join(out)


LIST_MARK = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)])\s+")


def kept_quote(head: str, prev_lines: list[str], cur: str) -> bool:
    """元の項の行（印を除いて `flat` した形）のどれかが頭 `head`（`flat` した形）を引き、その行の引用の前か後ろの文面が、
    頭と続いたまま新しい引きの項 `cur` に残るか——元の項の本文の引用を受け継いだ言い換えか（#1452・#1453）。
    頭だけの行（前にも後ろにも文面が無い）は受け継いだと見ない（止まる向き）。"""
    for line in prev_lines:
        i = line.find(head)
        while i >= 0:
            before, after = line[:i], line[i + len(head):]
            if (after and head + after in cur) or (before and before + head in cur):
                return True
            i = line.find(head, i + 1)
    return False


def renames(root: Path, base: str) -> dict[str, str]:
    """base から作業ツリーまでで git が改名と見た prompts のファイル——スキルのディレクトリからの相対パスで 旧 → 新（#1423 の R1）。
    台帳と原文を作業ツリーから読むので、改名も作業ツリーまで見る（コミットの前に回しても同じ答え。追跡していない新しいファイルは改名と見えない）。読めなければ空（改名を追わない——止まる向き）。"""
    r = git(root, "diff", "-z", "--name-status", "-M", base, "--", f"{SKILL_REL}/prompts/")
    if r.returncode != 0:
        return {}
    parts = r.stdout.split("\0")
    out: dict[str, str] = {}
    i = 0
    while i < len(parts) and parts[i]:
        status = parts[i]
        if status[:1] in ("R", "C"):
            if status[:1] == "R" and i + 2 < len(parts):
                out[parts[i + 1][len(SKILL_REL) + 1:]] = parts[i + 2][len(SKILL_REL) + 1:]
            i += 3
        else:
            i += 2
    return out


def case_ok(text: str, line_id: str, base_incident: str) -> str | None:
    """None なら条件を満たす。満たさないなら理由。"""
    m = re.search(rf"^#\s*外した行:\s*{re.escape(line_id)}\s*$", text, re.M)
    if not m:
        return f"`# 外した行: {line_id}` が無い"
    inc = re.search(r"^#\s*元の事故:\s*(.+?)\s*$", text, re.M)
    if not inc:
        return "`# 元の事故: <番号>` が無い"
    want = {x for x in re.findall(r"#[0-9]+", base_incident)}
    have = set(re.findall(r"#[0-9]+", inc.group(1)))
    if want and not want <= have:
        return f"`# 元の事故:` に {' '.join(sorted(want - have))} が無い（base の台帳の元の事故）"
    if not want and inc.group(1).strip() in ("", "-"):
        return "`# 元の事故:` が空（台帳が `-` なら、なぜ入れた行かを書く）"
    block = re.search(r"^graders:[^\n]*\n((?:[ \t]+[^\n]*\n|[ \t]*\n)*)", text + "\n", re.M)
    if not block or not re.search(r"^[ \t]*-[ \t]+name:", "\n".join(l for l in block.group(1).split("\n") if not l.lstrip().startswith("#")), re.M):
        return "`graders:` のブロックの中に `- name:` が 1 つも無い"
    return None


def main(argv: list[str]) -> int:
    sys.dont_write_bytecode = True
    if len(argv) != 1:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    base = argv[0]
    root = ROOT
    try:
        effects = load_effects(root)
        problems = effects.check(root / REGISTRY_REL)
        head_rows = effects.load_registry(root / REGISTRY_REL)
    except Exception as e:  # noqa: BLE001 — 読み込めない・台帳の形が違う・原文を読めないは、判定していない
        print(f"check-prompt-lines.py: {e}", file=sys.stderr)
        return 2
    for p in problems:
        print(f"NG: {p}")

    mb = git(root, "merge-base", base, "HEAD")
    if mb.returncode == 0 and mb.stdout.strip():
        base = mb.stdout.strip()  # base の先端が進んでいても、周が分かれた時点の台帳と比べる
    shown = git(root, "show", f"{base}:{REGISTRY_REL}")
    removed_note = ""
    if shown.returncode != 0:
        if git(root, "rev-parse", "--verify", f"{base}^{{commit}}").returncode != 0:
            print(f"check-prompt-lines.py: base `{base}` を解決できない", file=sys.stderr)
            return 2
        removed_note = "base に台帳が無い（導入の PR）——外した行の検査は飛ばした"
        base_rows: list[dict] = []
    else:
        try:
            base_rows = parse_registry_text(effects, shown.stdout)
        except ValueError as e:
            print(f"check-prompt-lines.py: {e}", file=sys.stderr)
            return 2
    head_ids = {r["ID"] for r in head_rows}
    merged_from = {}
    for r in head_rows:
        for src in filter(None, r["統合元"].split(";")):
            merged_from[src] = r
    removed = [r for r in base_rows if r["ID"] not in head_ids]
    head_by_id = {r["ID"]: r for r in head_rows}
    renamed = renames(root, base)
    for b in base_rows:
        h = head_by_id.get(b["ID"])
        if h is None:
            continue
        moved = renamed.get(b["ファイル"]) == h["ファイル"]
        if h["引き"] == b["引き"] and (h["ファイル"] == b["ファイル"] or moved):
            continue
        if h["ファイル"] != b["ファイル"]:
            if not moved:
                problems.append(f"{b['ID']}: ファイルを {b['ファイル']} から {h['ファイル']} に変えた（別の受け手の文面へ移さない。外すなら ID ごと外して eval を付ける）")
                print(f"NG: {problems[-1]}")
                continue
        old_text = git(root, "show", f"{base}:{SKILL_REL}/{b['ファイル']}")
        if old_text.returncode != 0:
            continue
        # HEAD で新しい引きが当たる項（本文を含む）が、base のどの項の頭を持っているかで見る。元の項の頭が残れば同じ項（言い換え・統合）、
        # 残らずに base の別の項の頭を持てば付け替え。HEAD に残った項だけを照らすので、同じ PR で外した項の頭は当たらない
        base_items = effects.items_of(old_text.stdout)
        prev = next((f for _, f, _ in base_items if f.startswith(b["引き"])), None)
        prev_lines = next(([flat(LIST_MARK.sub("", x)) for x in own_lines(body).split("\n")] for _, f, body in base_items if f == prev), [])
        new_file = root / SKILL_REL / h["ファイル"]
        new_items = effects.items_of(new_file.read_text(encoding="utf-8")) if new_file.is_file() else []
        new_heads = {f for _, f, _ in new_items}
        cur = next((flat(own_lines(body)) for _, f, body in new_items if f.startswith(h["引き"])), None)
        if cur is None:
            continue  # 引きが HEAD の項の頭に当たらない——上の check が名指す
        merged = [x["引き"] for x in base_rows if x["ID"] in h["統合元"].split(";") and x["ファイル"] == b["ファイル"]]
        others = [f for _, f, _ in base_items if f != prev]
        # 新しい引きが、HEAD に項の頭のまま残る base の別の項の頭に前方一致する（言い換えない付け替え）
        clash = [f for f in others if f.startswith(h["引き"]) and f in new_heads]
        # 元の項の頭が新しい引きの項に残らず、base の別の項の頭が入っている（付け替え先を言い換えた付け替え）
        if not (prev is not None and flat(prev) in cur):
            # 統合元の項の頭（取り込んだ文面）と、元の項が base の時点から本文で引いていた別の項の頭のうち、新しい引きの項が
            # その引用を受け継ぐ（引用の行の前か後ろの文面が、頭と続いて残る）ものは照らさない。引用を受け継がずに頭の文面だけが
            # 残るのは、元の項を消すか頭を写した新しい項に差し替えた付け替えである（#1430・#1452）。引いた先の項が HEAD に
            # 頭のまま残るかは見ない——引いた先の頭を同じ PR で言い換えても、引用を受け継ぐ言い換えは止めない（#1453）
            clash += [f for f in others if flat(f) and flat(f) in cur and f not in clash
                      and not any(f.startswith(m) for m in merged)
                      and not kept_quote(flat(f), prev_lines, cur)]
        if clash:
            problems.append(f"{b['ID']}: 引きを base に既にある別の項の頭「{clash[0][:30]}」に付け替えた（元の項を外したなら ID ごと外して eval を付ける）")
            print(f"NG: {problems[-1]}")
    changed = git(root, "diff", "--name-only", f"{base}...HEAD")
    if changed.returncode != 0:
        print(f"check-prompt-lines.py: git diff が失敗: {changed.stderr.strip()}", file=sys.stderr)
        return 2
    cases = [f for f in changed.stdout.split("\n") if re.fullmatch(rf"{re.escape(EVALS_REL)}/[^/]+/case\.yaml", f)
             and (root / f).is_file()]
    for r in removed:
        target = merged_from.get(r["ID"])
        if target is not None and r["同趣旨"] and target["ID"] != r["ID"]:
            base_target = next((b for b in base_rows if b["ID"] == target["ID"]), None)
            if base_target is not None and base_target["同趣旨"] == r["同趣旨"] and base_target["ファイル"] == r["ファイル"]:
                print(f"OK: {r['ID']} は {target['ID']} に統合（同趣旨 {r['同趣旨']}）——eval は求めない")
                continue
            why = ("統合先が base に無い（新しい行）" if base_target is None
                   else f"統合先 {target['ID']} の同趣旨が base で `{r['同趣旨']}` と同じでない" if base_target["同趣旨"] != r["同趣旨"]
                   else f"統合先 {target['ID']} が別のファイル（{base_target['ファイル']}）")
            problems.append(f"{r['ID']}: {why}")
            print(f"NG: {problems[-1]}")
            continue
        reasons = []
        for f in cases:
            why = case_ok((root / f).read_text(encoding="utf-8"), r["ID"], r["元の事故"])
            if why is None:
                break
            reasons.append(f"{f}: {why}")
        else:
            detail = "；".join(reasons) if reasons else "差分に `evals/*/case.yaml` が無い"
            problems.append(f"{r['ID']}（{r['ファイル']}「{r['引き']}」）を外したのに、元の事故を再現する eval が付いていない（{detail}）")
            print(f"NG: {problems[-1]}")
            continue
        print(f"OK: {r['ID']} を外す PR に eval {f} が付いている")
    if removed_note:
        print(removed_note)
    print(f"{'NG' if problems else 'OK'}: 台帳 {len(head_rows)} 行・外した行 {len(removed)} 件・問題 {len(problems)} 件")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
