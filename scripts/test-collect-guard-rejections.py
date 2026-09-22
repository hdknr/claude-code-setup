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

**主張とテストを 1 対 1 にする。** 本体の docstring の「守る」の行数だけ変異を当てる。
行を足したら変異も足す。

**引数を渡さない呼びでは、その引数の分岐は 1 度も走らない（必須の注意）。**
`--cwd-prefix` の絞り込みは、**渡さない観測では分岐に入らないので、反転しても
全アサートが通ってしまう**——実際にそうなっていた（`/code-review` が指摘）。
**だから変異ごとに「どの観測で殺すか」を `MUTATION_PROBE` に書く。**

**ただし 1 対 1 にならない行がある。** 「二重計上」を止めているのは 1 箇所ではなく
**3 つの条件の組み合わせ**で、**どれか 1 つを壊しても残り 2 つが止める**——
つまり**単独の変異では殺せない**。そこだけは素朴な実装に丸ごと差し替えている
（`MUTATIONS` の該当行に理由を書いた）。**「1 対 1」を保てないことを、
テストが黙って飲み込まないように明示しておく。**
"""
import importlib.util
import contextlib
import io
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


def rejection(cwd, reason, *, wrapped=False, rule=True, version="2.1.278", uuid="u1",
              sidechain=False):
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
        "isSidechain": sidechain,
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
    """macOS 3 件（うち 1 件は sidechain）・Linux 3 件（うち 1 件は包み＋規則文なし）＋引用 1 件。

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
        # **サブエージェントの拒否**（#137）。理由節は既存と同じものを使い、
        # **内訳だけが動く**ようにしてある——ここで種類が動くと、
        # sidechain の変異を「理由の種類」が殺してしまい、判別できなくなる。
        rejection("/Users/someone/repo", TOO_COMPLEX, uuid="m3", sidechain=True),
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


def observe(mod, root: Path, cwd_prefix=None) -> dict:
    events, scanned = mod.collect(root, cwd_prefix)
    return {
        "件数": len(events),
        "OS": sorted({e["os"] for e in events}),
        "理由の種類": len({e["reason"] for e in events if e["reason"]}),
        "包み": sum(1 for e in events if e["wrapped"]),
        "規則文なし": sum(1 for e in events if not e["has_rule_sentence"]),
        "版": sorted({e["version"] for e in events}),
        "main": sum(1 for e in events if not e["sidechain"]),
        "sidechain": sum(1 for e in events if e["sidechain"]),
        # **件数ではなく「どのレコードが sidechain か」。** 和や差の形で書くと、
        # **どんな実装でも真になる**（`main` と `sidechain` は同じ列を数えた
        # 相補な分割なので、和は必ず総件数に等しい）。
        "sidechain_uuids": sorted(e["uuid"] for e in events if e["sidechain"]),
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
                        '                if cwd_prefix and not (record.get("cwd") or "").startswith(cwd_prefix):\n'
                        '                    continue\n'
                        '                for body in error_blocks(record):\n'
                        '                    text = unwrap(body)\n'
                        '                    if not text.startswith(GUARD_PREFIX):\n'
                        '                        continue\n',
                        '                if False:\n'
                        '                    continue\n'
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
    # 守る 5: main と sidechain の取り違え。
    # **既定の観測で殺せる**——内訳を観測に入れてあるため（`observe` の `main`/`sidechain`）。
    # **試料の sidechain は理由節を既存と共有している**ので、この変異は内訳*だけ*を
    # 動かす——共有していないと「理由の種類」が先に殺してしまい、判別にならない。
    'sidechain を見ない': ('"sidechain": bool(record.get("isSidechain")),',
                           '"sidechain": False,'),
    # 守る 6: `cwd_prefix` の絞り込み。
    # **これは既定の観測では殺せない**（`cwd_prefix` を渡さない呼びでは分岐に入らない）ので、
    # **絞り込みを渡した観測**を別に取って当てる（`MUTATION_PROBE` 参照）。
    '絞り込みを反転する': ('                if cwd_prefix and not (record.get("cwd") or "").startswith(cwd_prefix):',
                          '                if cwd_prefix and (record.get("cwd") or "").startswith(cwd_prefix):'),
}

# 変異ごとに、どの観測で殺すか。**既定の観測で殺せないものがある**ことを明示しておく
# ——書かないと、渡していない引数の分岐が丸ごと無検査のまま残る（実測でそうなっていた）。
MUTATION_PROBE = {
    '絞り込みを反転する': "/Users/someone",
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
        check("拒否レコードだけを 6 件数える（引用は数えない）", correct["件数"] == 6)
        check("cwd から macOS と Linux を判別する", correct["OS"] == ["Linux", "macOS"])
        check("包まれた拒否も 1 件拾う", correct["包み"] == 1)
        check("規則文を持たない形も 1 件拾う", correct["規則文なし"] == 1)
        check("理由節はパスを伏せて 3 通りに畳まれる", correct["理由の種類"] == 3)
        check("版を取り出す", correct["版"] == ["2.1.278"])
        check("走査したファイル数を返す", correct["走査"] == 4)
        check("main と sidechain の内訳を出す（#137）",
              (correct["main"], correct["sidechain"]) == (5, 1))
        check("sidechain と数えたのは、その印を持つレコードである（#137）",
              correct["sidechain_uuids"] == ["m3"])

        mac_only = observe(mod, root, "/Users/someone")
        lin_only = observe(mod, root, "/root")
        check("`--cwd-prefix` で macOS の 3 件だけに絞れる",
              mac_only["件数"] == 3 and mac_only["OS"] == ["macOS"])
        check("`--cwd-prefix` で Linux の 3 件だけに絞れる",
              lin_only["件数"] == 3 and lin_only["OS"] == ["Linux"])

        print("\n0 件と収集失敗を混同しない")
        empty = tmpdir / "empty"
        empty.mkdir()
        assert_not_real_home(empty)
        events, scanned = mod.collect(empty)
        check("空のツリーは 0 件・走査 0 件", (len(events), scanned) == (0, 0))

        # **0 件でも内訳を出す**（#137）。**docstring が「必ず出力する」と言っている**ので、
        # **いちばん怪しい場合だけ出ない**のでは主張が偽になる。
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = mod.main(["--root", str(empty)])
        printed = buffer.getvalue()
        # **sidechain の行も見る。** main の行だけを見ていると、
        # **`if sidechain:` で囲う素朴な整理**で 0 件のときの sidechain 行が消えても緑になる
        # ——**docstring が「0 件のときも出す」と太字で言っている当のものが落ちる。**
        check("0 件でも母集団の内訳を出す（#137。main と sidechain の両方）",
              "=== 母集団の内訳 ===" in printed
              and "0  main-chain" in printed
              and "0  sidechain（サブエージェント）" in printed)
        check("0 件は既定では失敗にしない", code == 0)

        # **0 件の枝だけでは、印字の側を判別できない**（#137 の 2 パス目が指摘）。
        # **0 件では main も sidechain も 0 なので、札を入れ替えても、
        # sidechain の行を消しても、この上のアサートは緑のままである。**
        # **だから「値が違う試料」で印字そのものを見る**——`collect()` が返す辞書を
        # 見るアサートは、**印字の側には 1 件も当たっていない。**
        print("\n空でない試料で、印字される内訳を見る（#137）")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = mod.main(["--root", str(root)])
        printed = buffer.getvalue()
        check("印字される内訳が main 5 / sidechain 1（札の入れ替えを見る）",
              "5  main-chain" in printed and "1  sidechain（サブエージェント）" in printed)
        check("空でない走査は 0 を返す", code == 0)

        # **`--json` は「870 を当て直す唯一の機械的手段」として docstring が名指ししている**
        # （I1）。**名指ししているのに 1 度も走っていない**のでは、主張が偽になりうる。
        # **当て直しに要る 2 つの鍵（`sidechain` と `timestamp`）が在ること**まで見る。
        out_json = tmpdir / "events.json"
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = mod.main(["--root", str(root), "--json", str(out_json)])
        # **書き出しが壊れたときに、ここで例外を出して止めない。**
        # **素の `json.loads(read_text())` だと `FileNotFoundError` で落ち、
        # 以降の変異テスト 6 本と実環境の歯止めが丸ごと走らなくなる**
        # ——**CI は赤いままだが、いちばん知りたいときに診断が消える。**
        dumped = []
        if out_json.exists():
            try:
                dumped = json.loads(out_json.read_text(encoding="utf-8"))
            except ValueError:
                dumped = []
        check("`--json` が書き出され、件数が一致する", code == 0 and len(dumped) == 6)
        check("`--json` の各件が `sidechain` と `timestamp` を持つ（870 の当て直しに要る）",
              all("sidechain" in e and "timestamp" in e for e in dumped))
        check("`--json` で main 5 / sidechain 1 に分けられる",
              (sum(1 for e in dumped if not e["sidechain"]),
               sum(1 for e in dumped if e["sidechain"])) == (5, 1))

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

        print("\n`isSidechain` を持たないレコードは main に数える（#137）")
        nosc = tmpdir / "nosc"
        (nosc / "p").mkdir(parents=True)
        # **印を持つレコードを隣に置く。** 印の無いレコードだけで「main と数える」を
        # 見ると、**何もかも main と数える実装でも緑になる**——`sidechain` を
        # 見ない変異がここを素通りする。**判別するには両方が要る。**
        (nosc / "p" / "s.jsonl").write_text("\n".join([
            json.dumps({
                "type": "user", "uuid": "n1", "version": "2.1.278", "cwd": "/root/x",
                "message": {"role": "user", "content": [
                    {"type": "tool_result", "is_error": True,
                     "content": f"{GUARD}/root/x/w, but {TOO_COMPLEX}."},
                ]},
            }, ensure_ascii=False),
            rejection("/root/x", TOO_COMPLEX, uuid="n2", sidechain=True),
        ]) + "\n", encoding="utf-8")
        assert_not_real_home(nosc)
        events, _ = mod.collect(nosc)
        by_uuid = {e["uuid"]: e["sidechain"] for e in events}
        check("フィールドが無ければ main、印があれば sidechain（#137）",
              by_uuid == {"n1": False, "n2": True})

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
            prefix = MUTATION_PROBE.get(name)
            base = correct if prefix is None else observe(mod, root, prefix)
            mutated = observe(load(broken), root, prefix)
            check(f"変異を殺せる: {name}", mutated != base)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = SCRIPT.read_text(encoding="utf-8").split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件",
              len(promises) == len(MUTATIONS))

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
