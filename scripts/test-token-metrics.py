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
import contextlib
import importlib.util
import io
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


def line(model="claude-opus-5", day="2026-09-15", u=None, tool=None, msg_id=None):
    message = {"model": model}
    if msg_id is not None:
        # **本物は必ず `id` を持つ。** 同じ id の行が複数あり、各行が usage を再掲する。
        message["id"] = msg_id
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
        w, cr = mod.weighted_tokens(usage(inp=100, cw=200, cr=1000, out=10))
        # 100*1 + 200*1.25 + 1000*0.1 + 10*5 = 100 + 250 + 100 + 50 = 500
        check("加重が式どおり", w == 500.0)
        check("cache read を別に返す", cr == 1000)

        print("iterations を二重計上しない")
        u = usage(inp=100, cw=200, cr=1000, out=10)
        check("iterations がある入力を使っている", "iterations" in u)
        w2, _ = mod.weighted_tokens(u)
        check("iterations があっても加重が変わらない", w2 == 500.0)

        print("トップレベルが全部 0 で iterations に実数があるとき")
        # **実データに 2 件あった**（全件 151,922 件中）。片方は cache read だけで
        # 約 100 万トークン。**トップレベルだけ読むと丸ごと落ちる**（#95 のレビューが発見）。
        u = {
            "input_tokens": 0, "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0, "output_tokens": 0,
            "iterations": [{"input_tokens": 2, "cache_creation_input_tokens": 545,
                            "cache_read_input_tokens": 996796, "output_tokens": 3070}],
        }
        w, cr = mod.weighted_tokens(u)
        # 2*1 + 545*1.25 + 996796*0.1 + 3070*5 = 2 + 681.25 + 99679.6 + 15350
        check("iterations から拾う", abs(w - 115712.85) < 0.01)
        check("cache read も iterations から取る", cr == 996796)

        print("トップレベルに値があれば iterations を足さない")
        w2, _ = mod.weighted_tokens(usage(inp=100, cw=200, cr=1000, out=10))
        check("二重計上しない（500 のまま）", w2 == 500.0)
        # **キーごとに大きいほうを採る。**「全部 0 のときだけ iterations を見る」だと、
        # 1 フィールドでも実数があると残りを落とした（#95 のレビュー）。
        u3 = usage(inp=100)
        u3["iterations"] = [{"input_tokens": 999999}]
        w3, _ = mod.weighted_tokens(u3)
        check("キーごとに大きいほうを採る", w3 == 999999.0)
        # 部分的に 0 のとき、iterations にしかない残りを落とさない。
        u4 = {"input_tokens": 0, "cache_creation_input_tokens": 0,
              "cache_read_input_tokens": 0, "output_tokens": 5,
              "iterations": [{"input_tokens": 1000, "cache_read_input_tokens": 500000,
                              "output_tokens": 5}]}
        w4, _ = mod.weighted_tokens(u4)
        # 1000*1 + 500000*0.1 + 5*5 = 1000 + 50000 + 25
        check("部分的に 0 でも残りを拾う", w4 == 51025.0)
        # iterations が 2 要素の再掲でも倍にしない。
        u5 = {"input_tokens": 0, "cache_creation_input_tokens": 0,
              "cache_read_input_tokens": 0, "output_tokens": 0,
              "iterations": [{"input_tokens": 100}, {"input_tokens": 100}]}
        w5, _ = mod.weighted_tokens(u5)
        check("iterations が複数要素でも足さない", w5 == 100.0)

        print("レコードはあるが加重が 0 でも落ちない")
        root = base / "zero"
        make_tree(root, {"repo-a/s.jsonl": [line(u=usage())]})
        check("ゼロ除算にならない", mod.main(["--projects", str(root)]) == 0)

        print("1 応答が複数行に書かれるとき（message.id で畳む）")
        # **実データの支配的な形。** 全件で「usage を持つ行 179,948 / 異なる id 99,718」、
        # 行ごとに足すと**加重が 1.77 倍・req が 1.80 倍**に膨らんでいた（#95 のレビュー）。
        root = base / "msgid"
        make_tree(root, {
            "repo-a/s.jsonl": [line(u=usage(out=1), msg_id="m1"),
                               line(u=usage(out=1), msg_id="m1"),
                               line(u=usage(out=207), msg_id="m1")],
        })
        records, _, _, _ = mod.scan(root)
        check("同じ id の 3 行を 1 件に畳む", len(records) == 1)
        # 育っていく形なので最大（207*5）を採る。
        check("畳むときに最大を採る", records[0].weighted == 1035.0)

        print("id が違えば別々に数える")
        root = base / "msgid2"
        make_tree(root, {
            "repo-a/s.jsonl": [line(u=usage(out=10), msg_id="m1"),
                               line(u=usage(out=10), msg_id="m2")],
        })
        records, _, _, _ = mod.scan(root)
        check("別の id は畳まない", len(records) == 2)

        print("id が無ければそのまま数える")
        root = base / "noid"
        make_tree(root, {"repo-a/s.jsonl": [line(u=usage(out=10)), line(u=usage(out=10))]})
        records, _, _, _ = mod.scan(root)
        check("id が無ければ落とさずに数える", len(records) == 2)

        print("同じ id でもファイルが違えば畳まない")
        root = base / "msgid3"
        make_tree(root, {
            "repo-a/s1.jsonl": [line(u=usage(out=10), msg_id="m1")],
            "repo-a/s2.jsonl": [line(u=usage(out=10), msg_id="m1")],
        })
        records, _, _, _ = mod.scan(root)
        check("別セッションの同名 id は別物として数える", len(records) == 2)

        print("サブエージェントを取りこぼさない")
        root = base / "sub"
        make_tree(root, {
            "repo-a/sess1.jsonl": [line(u=usage(inp=1000))],
            "repo-a/sess1/subagents/agent1.jsonl": [line(u=usage(inp=3000))],
        })
        records, _, _, _ = mod.scan(root)
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
        records, _, _, _ = mod.scan(root)
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
        _, dev, _, _ = mod.scan(root)
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
        records, _, _, _ = mod.scan(root)
        check("既定では worktree を別リポジトリとして数える",
              len({r.repo for r in records}) == 2)
        records, _, _, _ = mod.scan(root, merge_worktrees=True)
        check("--merge-worktrees で元のリポジトリに寄せる",
              {r.repo for r in records} == {"repo-a"})

        print("壊れた入力で落ちない")
        root = base / "broken"
        make_tree(root, {
            "repo-a/s.jsonl": ["{壊れた JSON", "", "null", '{"type":"assistant"}',
                               '{"type":"assistant","message":{"usage":"文字列"}}',
                               line(u=usage(inp=10))],
        })
        records, _, unreadable, broken = mod.scan(root)
        check("壊れた行を飛ばして生き残る", len(records) == 1)
        check("読めなかったファイルは 0 件", unreadable == 0)
        # **壊れた行は数える。** 初版は 0 をアサートして「黙って落とす」を固定していた。
        check("壊れた行を数えている", broken == 2)

        print("usage の在処を型で絞らない")
        root = base / "type"
        make_tree(root, {
            "repo-a/s.jsonl": [json.dumps({"type": "将来の型", "timestamp": "2026-09-15T10:00:00Z",
                                           "message": {"model": "m", "usage": usage(inp=10)}})],
        })
        records, _, _, _ = mod.scan(root)
        check("assistant 以外でも usage があれば拾う", len(records) == 1)

        print("集計の出力")
        root = base / "render"
        make_tree(root, {
            "repo-a/s1.jsonl": [line(day="2026-09-15", u=usage(inp=1000, cr=100000)),
                                line(day="2026-09-15", u=usage(inp=1000, cr=100000),
                                     tool=skill_use("dev-loop"))],
            "repo-b/s2.jsonl": [line(day="2026-09-08", u=usage(inp=1000))],
        })
        records, dev, _, _ = mod.scan(root)
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
            "iterations を足す（二重計上になるはず）": (
                "        out[key] = best",
                "        out[key] = sum((i.get(key) or 0) for i in its if isinstance(i, dict))",
            ),
            "iterations を見ない（取りこぼすはず）": (
                "    nested = _from_iterations(usage)",
                "    nested = {}",
            ),
            "message.id で畳まない（1 応答を複数回数えるはず）": (
                "            previous = by_id.get(message_id)",
                "            records.append(record)\n            previous = record\n"
                "            by_id.pop(message_id, None)\n            previous = None",
            ),
            "畳むときに最小を採る（育つ形で小さいほうを採るはず）": (
                "            if previous is None or record.weighted > previous.weighted:",
                "            if previous is None or record.weighted < previous.weighted:",
            ),
            "壊れた行を数えない": (
                "                broken_lines += 1\n                continue\n"
                "            if not isinstance(row, dict):",
                "                continue\n"
                "            if not isinstance(row, dict):",
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
            top_zero = {
                "input_tokens": 0, "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0, "output_tokens": 0,
                "iterations": [{"input_tokens": 7, "cache_creation_input_tokens": 0,
                                "cache_read_input_tokens": 0, "output_tokens": 0}],
            }
            two_iters = {
                "input_tokens": 0, "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0, "output_tokens": 0,
                "iterations": [{"input_tokens": 50}, {"input_tokens": 50}],
            }
            make_tree(tree, {
                "repo-a/s.jsonl": [line(u=usage(inp=100, cw=200, cr=1000, out=10)),
                                   line(model="<synthetic>", u=usage(inp=0)),
                                   # **トップレベルが全部 0 で iterations に実数**——
                                   # この 1 行が無いと「iterations を見ない」変異が殺せない。
                                   line(u=top_zero),
                                   # **iterations が 2 要素の再掲**——足す変異を殺すのに要る。
                                   line(u=two_iters),
                                   # **同じ message.id の重複行**（usage が育つ形）——
                                   # 畳む判定の変異 2 件は、これが無いと殺せない。
                                   line(u=usage(out=1), msg_id="msg_dup"),
                                   line(u=usage(out=207), msg_id="msg_dup"),
                                   # **壊れた行**——数えない変異を殺すのに要る。
                                   "{壊れた JSON",
                                   line(u=usage(inp=10), tool=agent_use("dev-loop-verifier"))],
                "repo-a/s/subagents/a.jsonl": [line(u=usage(inp=3000))],
            })
            correct = load()
            mutated = load(mscript)
            # **`scan()` の 3 つだけを比べると、`main()` / `render_*` / `iso_week` /
            # `fmt_m` の変異が全部生き残る**（#95 のレビューが 12 変異中 8 件の生存を実証）。
            # **出力そのものを比べる**——CLI が返すものが最終的な成果物なので、
            # そこが変わらない変異は「殺せていない」と言うべきである。
            def observe(module):
                rec, dev, unread, broke = module.scan(tree)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    for argv in ([], ["--per-cycle"], ["--split"],
                                 ["--since", "2026-09-15"], ["--list-repos"]):
                        module.main(["--projects", str(tree)] + argv)
                return (len(rec), sum(r.weighted for r in rec), dev, unread, broke,
                        buf.getvalue())

            check(f"変異を殺せる: {name}", observe(correct) != observe(mutated))

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
