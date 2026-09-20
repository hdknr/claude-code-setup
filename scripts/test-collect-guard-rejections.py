#!/usr/bin/env python3
"""`collect-guard-rejections.py` の回帰テスト。

    python3 scripts/test-collect-guard-rejections.py

**このテストは実環境を触らない。** 毎回テンポラリに偽の `projects` ツリーを作り、
そこだけを対象にする（`assert_not_real_home` がそれを担保する）。
本体は実ホームの `~/.claude/projects` を既定にするので、**歯止めが無いと、
テストが利用者のトランスクリプトを読んで通ってしまう**——通っても「収集が効く」の
証明にならない。

**変異テストを含む。** 収集本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
「正しい入力で緑」だけでは、**何も検査しない実装でも通る**。

**主張とテストを 1 対 1 にする。** 本体の docstring の「守る」は 4 行あるので、
**その 4 行それぞれに変異を 1 つ当てる**。行を足したら変異も足す。

**ただし 1 対 1 にならない行がある。** 「二重計上」を止めているのは 1 箇所ではなく
**3 つの条件の組み合わせ**で、**どれか 1 つを壊しても残り 2 つが止める**——
つまり**単独の変異では殺せない**。そこだけは素朴な実装に丸ごと差し替えている
（`MUTATIONS` の該当行に理由を書いた）。**「1 対 1」を保てないことを、
テストが黙って飲み込まないように明示しておく。**
"""
import importlib.util
import json
import os
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "collect-guard-rejections.py"
REAL_HOME_PROJECTS = Path(os.path.expanduser("~")) / ".claude" / "projects"

GUARD = "This session is isolated in the worktree "

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"cgr_{script.parent.name}_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_home(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_HOME_PROJECTS.resolve(), "テストが実ホームの projects を対象にしている"
    assert not str(resolved).startswith(str(REAL_HOME_PROJECTS.resolve()) + os.sep), (
        "テストの対象が実ホームの projects の内側にある"
    )
    tmp_root = Path(tempfile.gettempdir()).resolve()
    assert resolved.is_relative_to(tmp_root), "テストの対象がテンポラリの外にある"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def rejection(cwd, reason, *, wrapped=False, rule=True, version="2.1.278", uuid="u1"):
    """拒否レコード 1 行。本物と同じ形（`type=user` ＋ `is_error` ブロック）。"""
    body = f"{GUARD}{cwd}/.claude/worktrees/w, but {reason}."
    if rule:
        body += (" Refusing to run it — a worktree-isolated session's git operations"
                 " must target its own worktree.")
        body += f" Run the plain command from {cwd}/.claude/worktrees/w."
    if wrapped:
        body = f"<tool_use_error>{body}</tool_use_error>"
    return json.dumps({
        "type": "user", "uuid": uuid, "version": version, "cwd": cwd,
        "timestamp": "2026-09-20T00:00:00.000Z",
        "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "is_error": True, "content": body},
        ]},
    }, ensure_ascii=False)


def echo(cwd, reason):
    """アシスタントが拒否文を引用した行。**これを数えたら失格。**"""
    text = f"The harness refused it:\n\n```\n{GUARD}{cwd}/w, but {reason}.\n```"
    return json.dumps({
        "type": "assistant", "uuid": "a1", "version": "2.1.278", "cwd": cwd,
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }, ensure_ascii=False)


TOO_COMPLEX = "this command names git in a form too complex"
EDITS_SHARED = "this command edits a path in the shared checkout"


def cd_reason(path):
    """**パスを含む**理由節。正規化を当てないと OS ごとに別物に数えられる。"""
    return f"this command changes directory to the shared checkout ({path}) before running git"


def build_tree(root: Path) -> None:
    """macOS 2 件・Linux 3 件（うち 1 件は包み＋規則文なし）＋引用 1 件。

    **同じ理由節をパスだけ変えて両 OS に置いてある**——正規化しなければ
    2 通りに割れるので、`パスを伏せない` 変異がここで殺せる。
    """
    mac = root / "-Users-someone-repo"
    lin = root / "-root-work"
    mac.mkdir(parents=True)
    lin.mkdir(parents=True)
    (mac / "s1.jsonl").write_text("\n".join([
        rejection("/Users/someone/repo", TOO_COMPLEX, uuid="m1"),
        echo("/Users/someone/repo", TOO_COMPLEX),
    ]) + "\n", encoding="utf-8")
    (mac / "s3.jsonl").write_text(
        rejection("/Users/someone/repo", cd_reason("/Users/someone/repo"), uuid="m2") + "\n",
        encoding="utf-8")
    (lin / "s2.jsonl").write_text("\n".join([
        rejection("/root/work", TOO_COMPLEX, uuid="l1"),
        rejection("/root/work", EDITS_SHARED, wrapped=True, rule=False, uuid="l2"),
    ]) + "\n", encoding="utf-8")
    (lin / "s4.jsonl").write_text(
        rejection("/root/work", cd_reason("/root/work"), uuid="l3") + "\n",
        encoding="utf-8")


def observe(mod, root: Path) -> dict:
    events, scanned = mod.collect(root)
    return {
        "件数": len(events),
        "OS": sorted({e["os"] for e in events}),
        "理由の種類": len({e["reason"] for e in events if e["reason"]}),
        "包み": sum(1 for e in events if e["wrapped"]),
        "規則文なし": sum(1 for e in events if not e["has_rule_sentence"]),
        "版": sorted({e["version"] for e in events}),
        "走査": scanned,
    }


MUTATIONS = {
    # 守る 1: 二重計上。
    # **これを止めているのは 1 箇所ではなく 3 つの条件の組み合わせ**
    # （`type == "user"` ／ `is_error` のブロック ／ 接頭辞で「始まる」）で、
    # **どれか 1 つを壊しても残り 2 つが止める**。だから単独の変異では殺せない
    # ——**素朴な実装（行に接頭辞が現れたら数える）に丸ごと差し替える**。
    '素朴な走査に戻す': ('                if record.get("type") != "user":\n'
                        '                    continue\n'
                        '                for body in error_blocks(record):\n'
                        '                    text = unwrap(body)\n'
                        '                    if not text.startswith(GUARD_PREFIX):\n'
                        '                        continue\n',
                        '                if False:\n'
                        '                    continue\n'
                        '                for body in [line]:\n'
                        '                    text = unwrap(body)\n'
                        '                    if GUARD_PREFIX not in text:\n'
                        '                        continue\n'),
    # 守る 2: 包みの取りこぼし
    '包みを剥がさない': ('    m = WRAPPER.search(text)\n    return m.group(1).strip() if m else text',
                        '    return text'),
    # 守る 3: 版と環境の取り違え（OS の推定）
    'OS を一定にする': ('    if head in ("/home", "/root"):\n        return "Linux"\n', ''),
    # 守る 4: 理由節の正規化（パスを伏せる）
    'パスを伏せない': ('    clause = PATH_POSIX.sub("<PATH>", clause)', '    pass'),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        root = tmpdir / "projects"
        root.mkdir()
        assert_not_real_home(root)
        build_tree(root)

        mod = load()
        correct = observe(mod, root)

        print("正しい入力での収集")
        check("拒否レコードだけを 5 件数える（引用は数えない）", correct["件数"] == 5)
        check("cwd から macOS と Linux を判別する", correct["OS"] == ["Linux", "macOS"])
        check("包まれた拒否も 1 件拾う", correct["包み"] == 1)
        check("規則文を持たない形も 1 件拾う", correct["規則文なし"] == 1)
        check("理由節はパスを伏せて 3 通りに畳まれる", correct["理由の種類"] == 3)
        check("版を取り出す", correct["版"] == ["2.1.278"])
        check("走査したファイル数を返す", correct["走査"] == 4)

        print("\n0 件と収集失敗を混同しない")
        empty = tmpdir / "empty"
        empty.mkdir()
        assert_not_real_home(empty)
        events, scanned = mod.collect(empty)
        check("空のツリーは 0 件・走査 0 件", (len(events), scanned) == (0, 0))

        print("\n理由節が取れない形は None にする（黙って畳まない）")
        odd = tmpdir / "odd"
        (odd / "p").mkdir(parents=True)
        (odd / "p" / "s.jsonl").write_text(json.dumps({
            "type": "user", "uuid": "o1", "version": "2.1.278", "cwd": "/root/x",
            "message": {"role": "user", "content": [
                {"type": "tool_result", "is_error": True,
                 "content": f"{GUARD}/root/x/w. No reason clause here."},
            ]},
        }, ensure_ascii=False) + "\n", encoding="utf-8")
        assert_not_real_home(odd)
        events, _ = mod.collect(odd)
        check("`, but ` が無ければ reason は None", len(events) == 1 and events[0]["reason"] is None)

        print("\n変異テスト（壊したのに緑なら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (needle, replacement) in MUTATIONS.items():
            if needle not in source:
                check(f"変異を当てる先がある: {name}", False)
                continue
            broken_dir = tmpdir / f"mut-{abs(hash(name))}"
            broken_dir.mkdir()
            broken = broken_dir / "collect-guard-rejections.py"
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            mutated = observe(load(broken), root)
            check(f"変異を殺せる: {name}", mutated != correct)

        print("\n実環境を対象にしない歯止め")
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
    print("ガード拒否の収集のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
