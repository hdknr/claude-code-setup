#!/usr/bin/env python3
"""`check-all.py` の回帰テスト。

    python3 scripts/test-check-all.py

**このテストは実環境を書き換えない。** 集約の挙動はテンポラリに作った偽スクリプトだけを
対象にする（`assert_not_real_repo` がそれを担保する）。**収録漏れの検査だけは実リポジトリを
読む**——**そこが検査の対象そのもの**だからで、**読むだけで書かない。**

**変異テストを含む。** 形は「**契約**を 1 組の表明として書き、**本体を 1 箇所ずつ壊して、
その契約が破れることを要求する**」。**壊したのに契約が保たれるなら、その契約は
その箇所を見ていない**ので失格とする。

**この runner の壊れ方は「落とす」である**——登録から 1 本落とす・落ちたのに数えない・
飛ばしたのに黙っている。**契約はその 3 つに対応させてある。**
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "scripts"
TARGET = SCRIPTS / "check-all.py"

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


def assert_not_real_repo(root: Path) -> None:
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの対象が実リポジトリの内側にある"
    )
    tmp_root = Path(tempfile.gettempdir()).resolve()
    assert root.resolve().is_relative_to(tmp_root), "テストの対象がテンポラリの外にある"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_main(mod, argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["check-all.py", *argv]
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
    finally:
        sys.argv = old
    return rc, buf.getvalue()


# ------------------------------------------------------------- 偽の scripts/
def build_fake(root: Path) -> Path:
    """偽の scripts/ を作り、そこに置いた check-all.py のパスを返す。"""
    assert_not_real_repo(root)
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "ok-a.py").write_text("print('a ok')\n")
    (scripts / "ok-b.py").write_text("print('b ok')\n")
    (scripts / "ok-c.py").write_text("print('c ok')\n")
    (scripts / "bad.py").write_text("import sys; print('BOOM-GUARD'); sys.exit(1)\n")
    (scripts / "bad-test.py").write_text("import sys; print('BOOM-TEST'); sys.exit(1)\n")
    (scripts / "needs-base.py").write_text("print('base ok')\n")
    target = scripts / "check-all.py"
    target.write_text(TARGET.read_text())
    return target


def wire(mod, root: Path, *, bad_guard: bool, bad_test: bool) -> None:
    mod.SCRIPTS = root / "scripts"
    mod.GUARDS = [("ok-a.py", [], False), ("ok-c.py", [], False),
                  ("needs-base.py", [], True)]
    mod.TESTS = ["ok-b.py"]
    if bad_guard:
        # **ok-c.py より前**に挟む。後ろに通る歯止めが無いと、
        # 「最初の失敗で止める」変異を契約が捕まえられない（実際に一度そうなった）。
        mod.GUARDS.insert(1, ("bad.py", [], False))
    if bad_test:
        mod.TESTS.append("bad-test.py")


# ------------------------------------------------------------------- 契約
# **本体を壊したときに、少なくとも 1 つが破れなければならない。**
def contract(target: Path, root: Path, tag: str) -> list[tuple[str, bool]]:
    got: list[tuple[str, bool]] = []

    # 1) 全部通る。base は解決できない → base を要する 1 本は SKIP。
    mod = load(target, f"{tag}_pass")
    wire(mod, root, bad_guard=False, bad_test=False)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("全部通れば rc=0", rc == 0),
        ("飛ばしたものを数えて出す", "飛ばし 1" in out),
        ("飛ばしたことを黙らない", "飛ばしたものは回していない" in out),
        ("SKIP でも残りは回る", "OK   ok-b.py" in out),
    ]

    # 2) 歯止めだけが落ちる
    mod = load(target, f"{tag}_badguard")
    wire(mod, root, bad_guard=True, bad_test=False)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("歯止めが落ちたら rc=1", rc == 1),
        ("歯止めの失敗を名指しする", "落ちたもの: bad.py" in out),
        ("歯止めが落ちても後続の歯止めを回す", "OK   ok-c.py" in out),
        ("歯止めが落ちても回帰テストを回す", "OK   ok-b.py" in out),
        ("歯止めの失敗の出力を見せる", "BOOM-GUARD" in out),
    ]

    # 3) 回帰テストだけが落ちる（歯止めとは別の経路で数えている）
    mod = load(target, f"{tag}_badtest")
    wire(mod, root, bad_guard=False, bad_test=True)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz"])
    got += [
        ("回帰テストが落ちたら rc=1", rc == 1),
        ("回帰テストの失敗を名指しする", "落ちたもの: bad-test.py" in out),
        ("回帰テストの失敗の出力を見せる", "BOOM-TEST" in out),
        ("回帰テストの失敗を 1 件と数える", "失敗 1" in out),
    ]

    # 4) --guards-only は回帰テストを飛ばし、そのことを出す
    mod = load(target, f"{tag}_guardsonly")
    wire(mod, root, bad_guard=False, bad_test=False)
    rc, out = run_main(mod, ["--base", "no-such-ref-xyz", "--guards-only"])
    got += [
        ("--guards-only で回帰テストを回さない", "OK   ok-b.py" not in out),
        ("--guards-only でも飛ばしたことを出す", "飛ばしたものは回していない" in out),
    ]
    return got


def contract_with_base(target: Path, root: Path, tag: str) -> list[tuple[str, bool]]:
    """base が解決できるなら、base を要する検査も回る。"""
    mod = load(target, f"{tag}_base")
    wire(mod, root, bad_guard=False, bad_test=False)
    rc, out = run_main(mod, ["--base", "HEAD"])
    return [
        ("base が解決できれば飛ばさない", "飛ばし 0" in out),
        ("base を要する検査が回る", "OK   needs-base.py" in out),
        ("base ありでも全部通れば rc=0", rc == 0),
    ]


# ---------------------------------------------------------------- 収録漏れ
def test_registry_covers_every_script() -> None:
    """実リポジトリを読む。`scripts/` に検査を足して登録し忘れたら落とす。"""
    src = TARGET.read_text()
    guards = sorted(
        p.name for p in SCRIPTS.glob("check-*.py") if p.name != "check-all.py"
    ) + ["skill-metrics.py"]
    tests = sorted(
        p.name for p in SCRIPTS.glob("test-*.py") if p.name != "test-check-all.py"
    )
    missing_g = [n for n in guards if f'"{n}"' not in src]
    missing_t = [n for n in tests if f'"{n}"' not in src]
    check(f"歯止めを全部収録している（{len(guards)} 本）", not missing_g)
    if missing_g:
        print(f"       収録漏れ: {missing_g}")
    check(f"回帰テストを全部収録している（{len(tests)} 本）", not missing_t)
    if missing_t:
        print(f"       収録漏れ: {missing_t}")


# ------------------------------------------------------------------ 変異
MUTANTS = {
    "歯止めが落ちても failed に積まない": (
        "            failed.append(label)\n", "            pass\n"),
    "回帰テストが落ちても failed に積まない": (
        "                failed.append(name)\n", "                pass\n"),
    "失敗があっても 0 を返す": ("        return 1\n", "        return 0\n"),
    "落ちたものの出力を見せない": (
        "        print(out.rstrip())\n", "        pass\n"),
    "飛ばしたことを黙る": (
        '        print("**飛ばしたものは回していない。** '
        '手元の緑をそのまま「全部緑」と報告しない。")\n',
        "        pass\n"),
    "最初の失敗で止める": ("            logs.append((label, out))\n",
                           "            logs.append((label, out))\n            break\n"),
}


def main() -> int:
    print("収録漏れ（実リポジトリを読むだけ）:")
    test_registry_covers_every_script()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        print("契約（本体そのまま——全部通らなければならない）:")
        target = build_fake(root / "real")
        for name, ok in contract(target, root / "real", "real"):
            check(name, ok)

        repo = root / "withbase"
        target = build_fake(repo)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-q", "--allow-empty", "-m", "init"], check=True)
        for name, ok in contract_with_base(target, repo, "wb"):
            check(name, ok)

        print("変異（1 箇所ずつ壊す——契約が破れなければ失格）:")
        src = TARGET.read_text()
        for i, (name, (old, new)) in enumerate(MUTANTS.items()):
            if src.count(old) != 1:
                check(f"変異 `{name}` の当て先が 1 箇所", False)
                continue
            d = root / f"mut{i}"
            t = build_fake(d)
            t.write_text(src.replace(old, new))
            broken = [n for n, ok in contract(t, d, f"m{i}") if not ok]
            check(f"変異 `{name}` を契約が捕まえる", bool(broken))
            if not broken:
                print("       壊したのに契約が全部通った")

    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


if __name__ == "__main__":
    sys.exit(main())
