#!/usr/bin/env python3
"""`token-metrics.py` の回帰テスト。

    python3 scripts/test-token-metrics.py

**このテストは実環境を触らない。** 毎回テンポラリに偽の `projects` ツリーを作り、
そこだけを対象にする（`assert_not_real_home` がそれを担保する）。
本体は実ホームの `~/.claude/projects` を既定にするので、**歯止めが無いと、
テストが利用者のトランスクリプトを読んで通ってしまう**——通っても「歯止めが効く」の
証明にならない。

**変異テストを含む。** 検査本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
「正しい入力で緑」だけでは、**何も検査しない実装でも通る**。

**本体は CI から呼ばないが、このテストは CI で回す。** `test-export-diagrams.py` が
同じ形——本体（`export-diagrams.py`）は CI から呼ばないが、テストは `docs.yml` で回っている。
**歯止めが「置いてあるが何も見ていない」状態に退化するのを防ぐ**のがテストの役目なので、
本体が手動でもテストは自動で回す。
"""
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "token-metrics.py"
REAL_HOME_PROJECTS = Path(os.path.expanduser("~")) / ".claude" / "projects"

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"tm_{script.parent.parent.name}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_home(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_HOME_PROJECTS.resolve(), "テストが実ホームの projects を対象にしている"
    assert not str(resolved).startswith(str(REAL_HOME_PROJECTS.resolve()) + os.sep), (
        "テストの対象が実ホームの projects の内側にある"
    )
    # 両側を resolve() してから比べる（macOS の /var → /private/var）。
    tmp_root = Path(tempfile.gettempdir()).resolve()
    assert resolved.is_relative_to(tmp_root), "テストの対象がテンポラリの外にある"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def usage(inp=0, cw=0, cr=0, out=0, *, iterations=True):
    u = {
        "input_tokens": inp,
        "cache_creation_input_tokens": cw,
        "cache_read_input_tokens": cr,
        "output_tokens": out,
    }
    if iterations:
        # **本物と同じ形**: 各要素がトップレベルと同じ数字を再掲している。
        u["iterations"] = [dict(u)]
    return u


def line(model="claude-opus-5", day="2026-09-15", u=None, tool=None):
    message = {"model": model}
    if u is not None:
        message["usage"] = u
    if tool is not None:
        message["content"] = [tool]
    return json.dumps({"type": "assistant", "timestamp": f"{day}T10:00:00.000Z",
                       "message": message}, ensure_ascii=False)


def skill_use(name):
    return {"type": "tool_use", "name": "Skill", "input": {"skill": name}}


def agent_use(subagent_type):
    return {"type": "tool_use", "name": "Agent", "input": {"subagent_type": subagent_type}}


def make_tree(root: Path, files: dict[str, list[str]]) -> None:
    assert_not_real_home(root)
    for rel, lines in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tm-test-") as tmp:
        base = Path(tmp)
        mod = load()

        print("加重の式")
        w, raw, cr = mod.weighted_tokens(usage(inp=100, cw=200, cr=1000, out=10))
        # 100*1 + 200*1.25 + 1000*0.1 + 10*5 = 100 + 250 + 100 + 50 = 500
        check("加重が式どおり", w == 500.0)
        check("生の合計が素朴な和", raw == 1310)
        check("cache read を別に返す", cr == 1000)

        print("iterations を二重計上しない")
        u = usage(inp=100, cw=200, cr=1000, out=10)
        check("iterations がある入力を使っている", "iterations" in u)
        w2, _, _ = mod.weighted_tokens(u)
        check("iterations があっても加重が変わらない", w2 == 500.0)

        print("サブエージェントを取りこぼさない")
        root = base / "sub"
        make_tree(root, {
            "repo-a/sess1.jsonl": [line(u=usage(inp=1000))],
            "repo-a/sess1/subagents/agent1.jsonl": [line(u=usage(inp=3000))],
        })
        records, _, _ = mod.scan(root)
        check("親とサブエージェントの両方を拾う", len(records) == 2)
        check("サブエージェント分の加重が入っている",
              sum(r.weighted for r in records) == 4000.0)
        check("サブエージェントに印が付く", sum(1 for r in records if r.is_sub) == 1)
        check("サブエージェントも親セッションに属する",
              {r.session for r in records} == {"sess1"})

        print("`<synthetic>` を除外する")
        root = base / "syn"
        make_tree(root, {
            "repo-a/s.jsonl": [line(u=usage(inp=1000)),
                               line(model="<synthetic>", u=usage(inp=0))],
        })
        records, _, _ = mod.scan(root)
        check("synthetic のレコードを数えない", len(records) == 1)

        print("dev-loop の周を判定する")
        root = base / "dl"
        make_tree(root, {
            "repo-a/plain.jsonl": [line(u=usage(inp=10))],
            "repo-a/viaskill.jsonl": [line(u=usage(inp=10), tool=skill_use("dev-loop:dev-loop"))],
            "repo-a/viaagent.jsonl": [line(u=usage(inp=10),
                                           tool=agent_use("dev-loop:dev-loop-verifier"))],
            "repo-a/bare.jsonl": [line(u=usage(inp=10), tool=skill_use("dev-loop"))],
            "repo-a/other.jsonl": [line(u=usage(inp=10), tool=skill_use("code-review"))],
        })
        _, dev, _ = mod.scan(root)
        sessions = {s for _, s in dev}
        check("Skill 経由（名前空間つき）を拾う", "viaskill" in sessions)
        check("Skill 経由（素の名前）を拾う", "bare" in sessions)
        check("Agent 経由を拾う", "viaagent" in sessions)
        check("無関係なセッションを拾わない", "plain" not in sessions and "other" not in sessions)

        print("worktree の扱い")
        root = base / "wt"
        make_tree(root, {
            "repo-a/s.jsonl": [line(u=usage(inp=10))],
            "repo-a--claude-worktrees-issue-1/s.jsonl": [line(u=usage(inp=10))],
        })
        records, _, _ = mod.scan(root)
        check("既定では worktree を別リポジトリとして数える",
              len({r.repo for r in records}) == 2)
        records, _, _ = mod.scan(root, merge_worktrees=True)
        check("--merge-worktrees で元のリポジトリに寄せる",
              {r.repo for r in records} == {"repo-a"})

        print("壊れた入力で落ちない")
        root = base / "broken"
        make_tree(root, {
            "repo-a/s.jsonl": ["{壊れた JSON", "", "null", '{"type":"assistant"}',
                               '{"type":"assistant","message":{"usage":"文字列"}}',
                               line(u=usage(inp=10))],
        })
        records, _, unreadable = mod.scan(root)
        check("壊れた行を飛ばして生き残る", len(records) == 1)
        check("読めなかったファイルは 0 件", unreadable == 0)

        print("usage の在処を型で絞らない")
        root = base / "type"
        make_tree(root, {
            "repo-a/s.jsonl": [json.dumps({"type": "将来の型", "timestamp": "2026-09-15T10:00:00Z",
                                           "message": {"model": "m", "usage": usage(inp=10)}})],
        })
        records, _, _ = mod.scan(root)
        check("assistant 以外でも usage があれば拾う", len(records) == 1)

        print("集計の出力")
        root = base / "render"
        make_tree(root, {
            "repo-a/s1.jsonl": [line(day="2026-09-15", u=usage(inp=1000, cr=100000)),
                                line(day="2026-09-15", u=usage(inp=1000, cr=100000),
                                     tool=skill_use("dev-loop"))],
            "repo-b/s2.jsonl": [line(day="2026-09-08", u=usage(inp=1000))],
        })
        records, dev, _ = mod.scan(root)
        weekly = mod.render_weekly(records, dev)
        check("週次に 2 つの ISO 週が出る",
              "2026-W37" in weekly and "2026-W38" in weekly)
        per_cycle = mod.render_per_cycle(records, dev)
        check("周ごとに dev-loop の周だけ出る",
              "repo-a" in per_cycle and "repo-b" not in per_cycle)

        print("main() の終了コード")
        root = base / "main"
        make_tree(root, {"repo-a/s.jsonl": [line(u=usage(inp=10))]})
        check("走査できれば 0", mod.main(["--projects", str(root)]) == 0)
        missing = base / "なにもない"
        check("走査先が無ければ非ゼロ", mod.main(["--projects", str(missing)]) == 1)

        print("変異テスト（壊したのに緑なら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        mutants = {
            "iterations も足す（二重計上になるはず）": (
                '    cache_read = usage.get("cache_read_input_tokens") or 0',
                '    for it in (usage.get("iterations") or []):\n'
                '        for key, factor in WEIGHTS.items():\n'
                '            weighted += (it.get(key) or 0) * factor\n'
                '    cache_read = usage.get("cache_read_input_tokens") or 0',
            ),
            "サブエージェントを見ない（取りこぼすはず）": (
                'for path in sorted(projects_root.rglob("*.jsonl")):',
                'for path in sorted(projects_root.glob("*/*.jsonl")):',
            ),
            "synthetic を除外しない": (
                "            if model in SYNTHETIC_MODELS:\n                continue",
                "            if False:\n                continue",
            ),
            "Agent 経由の判定をやめる": (
                "                elif name in AGENT_TOOLS:",
                "                elif False:",
            ),
            "加重の係数を 1 にする": (
                '    "output_tokens": 5.0,',
                '    "output_tokens": 1.0,',
            ),
        }
        for name, (old, new) in mutants.items():
            assert source.count(old) == 1, f"変異の対象が 1 箇所でない: {name}"
            mroot = base / ("mutant-" + str(abs(hash(name)) % 10**6))
            assert_not_real_home(mroot)
            (mroot / "scripts").mkdir(parents=True, exist_ok=True)
            mscript = mroot / "scripts" / "token-metrics.py"
            mscript.write_text(source.replace(old, new), encoding="utf-8")
            tree = mroot / "projects"
            make_tree(tree, {
                "repo-a/s.jsonl": [line(u=usage(inp=100, cw=200, cr=1000, out=10)),
                                   line(model="<synthetic>", u=usage(inp=0)),
                                   line(u=usage(inp=10), tool=agent_use("dev-loop-verifier"))],
                "repo-a/s/subagents/a.jsonl": [line(u=usage(inp=3000))],
            })
            correct = load()
            mutated = load(mscript)
            c_rec, c_dev, _ = correct.scan(tree)
            m_rec, m_dev, _ = mutated.scan(tree)
            same = (len(c_rec) == len(m_rec)
                    and sum(r.weighted for r in c_rec) == sum(r.weighted for r in m_rec)
                    and c_dev == m_dev)
            check(f"変異を殺せる: {name}", not same)

        print("実環境を対象にしない歯止め")
        try:
            assert_not_real_home(REAL_HOME_PROJECTS)
        except AssertionError:
            check("実ホームの projects を対象にすると落ちる", True)
        else:
            check("実ホームの projects を対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("トークン集計のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
