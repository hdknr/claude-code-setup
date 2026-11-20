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
   - `graders:` に 1 つ以上の `- name:` がある
   **ただし、HEAD の台帳の別の行の `統合元` に挙がり、かつその行が base で同じ `同趣旨`（空でない）を持っていた行は、統合なので eval を求めない**
   （同じ趣旨の行がほかに残るため）。

## 守らないもの

- **eval が元の事故を実際に再現するか・外した後も通るか**——見るのは eval が差分に在って名指しが揃うことだけ（`claude plugin eval` は課金し、CI から呼ばない）。
  通ったことは PR に `run-dev-loop-evals.py` の要約を貼って人間が見る（`references/prune.md`）。
- **承認**——外す PR を人間が承認したかは見ない。
- **台帳の無い base**（導入の PR）——外した行が定義できないので 2 を飛ばす。

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
    if not re.search(r"^\s+-\s+name:", text, re.M) or not re.search(r"^graders:", text, re.M):
        return "`graders:` に `- name:` が 1 つも無い"
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
            if base_target is not None and base_target["同趣旨"] == r["同趣旨"]:
                print(f"OK: {r['ID']} は {target['ID']} に統合（同趣旨 {r['同趣旨']}）——eval は求めない")
                continue
            problems.append(f"{r['ID']}: 統合先 {target['ID']} の同趣旨が base で `{r['同趣旨']}` と同じでない")
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
