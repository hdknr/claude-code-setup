#!/usr/bin/env python3
"""`ledger.py`（複数 Issue の台帳）の回帰テスト。

    python3 scripts/test-ledger.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）。
`test-find-cycle.py` と同じ形——**`dev-loop` はどのリポジトリでも使えるスキル**なので、
本体は対象リポジトリの `scripts/` に在ることを当てにできない。

**このテストは実環境を触らない。** 毎回テンポラリに本物の git リポジトリと worktree を作り、
そこだけを対象にする（`assert_not_real_repo` がそれを担保する）。本体は cwd から
メインの作業ツリーを解決して `.claude/plans/` に書くので、**歯止めが無いと、テストが
このリポジトリ自身に台帳を書く。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が緑であること（下の「正しい本体」）。

**主張とテストを 1 対 1 にする。** 本体の docstring の「守る」の行数だけ変異を当てる
（**テスト自身に数えさせる**）。終了コードも docstring の表と突き合わせる。
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "ledger.py"

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"ledger_{id(script)}_{script.stat().st_mtime_ns}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def build_repo(root: Path) -> Path:
    """本物のリポジトリと、その `.claude/worktrees/w` に本物の worktree。worktree のパスを返す。"""
    root.mkdir(parents=True)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "t")
    (root / "sub").mkdir()
    (root / "sub" / "x.txt").write_text("x\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    wt = root / ".claude" / "worktrees" / "w"
    git(root, "worktree", "add", "-q", str(wt), "-b", "wt")
    return wt


def snapshot(path: Path):
    """ファイルのバイト列。**無ければ None**——変異で別の場所に書かれても、テスト側が例外で落ちずに観測できる。"""
    return path.read_bytes() if path.is_file() else None


def run(mod, argv, cwd):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = mod.main(argv, cwd=str(cwd))
        except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
            return ("例外", type(exc).__name__, "")
    return (rc, out.getvalue(), err.getvalue())


def scenario(mod, tmp: Path, tag: str) -> dict:
    """全試料を 1 本のリポジトリで走らせ、観測を辞書で返す。**変異の前後で同じ関数を使う。**"""
    root = tmp / f"repo-{tag}"
    assert_not_real_repo(root)
    wt = build_repo(root)
    ledger = root / ".claude" / "plans" / "cruise-c.json"
    o = {}

    # L1: 場所は cwd に依らない。**root を伏せて記録する**——試料ごとに root の名前が違うので、
    # 伏せないと変異の前後の比較がパスの違いだけで「殺せた」になる（陽性対照が成り立たない）。
    def where(cwd):
        return str(run(mod, ["path", "c"], cwd)[1]).strip().replace(str(root), "<root>")

    o["path(main)"] = where(root)
    o["path(sub)"] = where(root / "sub")
    o["path(worktree)"] = where(wt)
    o["path(worktree/sub)"] = where(wt / "sub")

    # L7: 無い台帳
    o["show(無い)"] = run(mod, ["show", "c"], root)[0]
    o["next(無い)"] = run(mod, ["next", "c"], root)[0]

    # init（worktree の中から作っても、メインの作業ツリーに置かれる）
    o["init"] = run(mod, ["init", "c"], wt)[0]
    o["init の置き場所"] = ledger.is_file() and not (wt / ".claude" / "plans" / "cruise-c.json").exists()

    # 依存グラフ: 1 ← 2 ← 3、1 ← 4、5 は独立
    o["add 1"] = run(mod, ["add", "c", "1", "--title", "一"], root)[0]
    o["add 2"] = run(mod, ["add", "c", "2", "--deps", "1"], root)[0]
    o["add 3"] = run(mod, ["add", "c", "3", "--deps", "2"], root)[0]
    o["add 4"] = run(mod, ["add", "c", "4", "--deps", "1"], root)[0]
    o["add 5"] = run(mod, ["add", "c", "5"], root)[0]
    o["next(初め)"] = str(run(mod, ["next", "c"], root)[1]).split()

    # L2: 2 度目の init。**中身のある台帳に当てる**——空の台帳に当てると、上書きしても同じバイトになり
    # 「変わらない」が判別しない
    before = snapshot(ledger)
    o["init(2 度目)"] = run(mod, ["init", "c"], root)[0]
    o["init(2 度目) 後も同じ"] = snapshot(ledger) == before

    before = snapshot(ledger)
    # L4: 依存の誤り（add）
    o["add 依存先なし"] = run(mod, ["add", "c", "6", "--deps", "99"], root)[0]
    o["add 自己依存"] = run(mod, ["add", "c", "7", "--deps", "7"], root)[0]
    # L4: 依存の誤り（set deps=）——1 → 3 で 1 ← 2 ← 3 ← 1 の循環
    o["set 循環"] = run(mod, ["set", "c", "1", "deps=3"], root)[0]
    o["set 依存先なし"] = run(mod, ["set", "c", "1", "deps=99"], root)[0]
    # L5
    o["add 2 度目"] = run(mod, ["add", "c", "1"], root)[0]
    o["set 台帳に無い"] = run(mod, ["set", "c", "42", "state=impl"], root)[0]
    # L3
    o["set 無い状態"] = run(mod, ["set", "c", "5", "state=done"], root)[0]
    o["set 無い鍵"] = run(mod, ["set", "c", "5", "colour=red"], root)[0]
    # 引数の形
    o["set 鍵=値でない"] = run(mod, ["set", "c", "5", "state"], root)[0]
    o["add 番号でない"] = run(mod, ["add", "c", "x"], root)[0]
    o["拒んだ後も同じ"] = snapshot(ledger) == before

    # L6: 依存の状態ごとの next
    run(mod, ["set", "c", "1", "state=pr", "pr=#101"], root)
    o["next(依存が PR 中)"] = run(mod, ["next", "c"], root)[1].split()
    run(mod, ["set", "c", "1", "state=blocked"], root)
    o["next(依存が止まっている)"] = run(mod, ["next", "c"], root)[1].split()
    run(mod, ["set", "c", "1", "state=dropped"], root)
    o["next(依存が取り下げ)"] = run(mod, ["next", "c"], root)[1].split()
    run(mod, ["set", "c", "1", "state=merged"], root)
    o["next(依存がマージ済み)"] = run(mod, ["next", "c"], root)[1].split()
    run(mod, ["set", "c", "2", "state=impl", "worktree=/w/2", "agent=impl-2", "base=abc"], root)
    show = run(mod, ["show", "c"], root)
    o["show rc"] = show[0]
    o["show 進行中"] = "進行中（実物で確かめてから続ける）: #2(impl)" in show[1]
    o["show 着手できる"] = "着手できる: #4, #5" in show[1]
    o["show 依存待ち"] = "依存待ち: #3" in show[1]
    o["show の値"] = "/w/2" in show[1] and "impl-2" in show[1]
    try:
        data = json.loads(snapshot(ledger) or b"")
        o["set で書いた値"] = [(i["number"], i["state"], i["pr"]) for i in data["issues"]][:2]
    except (ValueError, KeyError, TypeError):
        o["set で書いた値"] = "読めない"

    # L7: 壊れた台帳・形の違う台帳
    broken = root / ".claude" / "plans" / "cruise-b.json"
    broken.write_text("{ 壊れている", encoding="utf-8")
    o["next(壊れた JSON)"] = run(mod, ["next", "b"], root)[0]
    o["set(壊れた JSON)"] = run(mod, ["set", "b", "1", "state=impl"], root)[0]
    o["壊れた JSON を書き換えない"] = broken.read_text(encoding="utf-8") == "{ 壊れている"
    shape = root / ".claude" / "plans" / "cruise-s.json"
    shape.write_text(json.dumps({"format": 1, "issues": [{"number": 1, "state": "wip", "deps": []}]}), encoding="utf-8")
    o["next(形が違う)"] = run(mod, ["next", "s"], root)[0]

    # L8: 名前
    o["名前 ../x"] = run(mod, ["init", "../x"], root)[0]
    o["名前 a/b"] = run(mod, ["init", "a/b"], root)[0]
    o["名前 .x"] = run(mod, ["init", ".x"], root)[0]
    # `cruise-` が前に付くので `../x` だけでは外に出ない。**実際に外へ出る名前**も当てる
    o["名前 x/../../../escaped"] = run(mod, ["init", "x/../../../escaped"], root)[0]
    o["plans の外に書いていない"] = sorted(p.name for p in (root / ".claude").iterdir()) == ["plans", "worktrees"] \
        and not list(root.rglob("escaped*"))

    # L9: git の外
    outside = tmp / f"outside-{tag}"
    outside.mkdir()
    o["git の外"] = run(mod, ["show", "c"], outside)[0]
    return o


# 1 件ずつ (探す文字列, 置き換え) の組。複数の組で 1 つの変異にしてよい。
MUTATIONS = {
    # 守る 1: 場所は cwd に依らない
    "worktree の git-dir の親を使う": [
        ('"--git-common-dir"],', '"--git-dir"],')],
    # 守る 2: init で上書きしない
    "在る台帳に init で上書きする": [
        ("    if path.exists():\n        raise Refused", "    if False:\n        raise Refused")],
    # 守る 3: 決まった一覧に無い状態を拒む
    "無い状態を通す": [
        ('        if issue["state"] not in STATES:\n            raise Refused',
         '        if False:\n            raise Refused')],
    # 守る 4: 依存の循環を拒む
    "循環を見ない": [
        ("    for n in graph:\n        visit(n, [])", "    pass")],
    # 守る 5: next は依存がすべてマージ済みのものだけ
    "依存が未着手でなければ済んだと読む": [
        ('all(state.get(d) == DONE for d in i["deps"])', 'all(state.get(d) != "todo" for d in i["deps"])')],
    # 守る 6: 読めない台帳を空と読まない
    "無い台帳を空と読む": [
        ('        raise Unknown(f"台帳が無い: {path}")',
         '        return {"format": FORMAT, "name": "", "issues": []}')],
    # 守る 7: 名前にパスの区切りと先頭のドットを許さない
    "名前を何でも通す": [
        ('NAME_RE = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._-]*")', 'NAME_RE = re.compile(r".+")')],
    # 守る 8: 拒んだ操作では台帳を変えない（検査してから書く）
    "書いてから検査する": [
        ("def save(path, data):\n    validate(data)\n", "def save(path, data):\n"),
        ("        os.replace(tmp, path)\n", "        os.replace(tmp, path)\n        validate(data)\n")],
}


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t).resolve()
        mod = load()
        o = scenario(mod, tmp, "correct")

        print("場所（L1）")
        paths = {o["path(main)"], o["path(sub)"], o["path(worktree)"], o["path(worktree/sub)"]}
        check("4 つの cwd から同じパスを指す", len(paths) == 1)
        check("メインの作業ツリーの .claude/plans/cruise-c.json",
              o["path(main)"] == "<root>/.claude/plans/cruise-c.json")
        check("worktree の中から init してもメインに置かれる", o["init"] == 0 and o["init の置き場所"])

        print("\ninit（L2）")
        check("2 度目の init は 3", o["init(2 度目)"] == 3)
        check("2 度目の init で中身が変わらない", o["init(2 度目) 後も同じ"])

        print("\n拒む操作（L3〜L5）")
        check("足すのは通る", all(o[f"add {n}"] == 0 for n in range(1, 6)))
        for key in ("add 依存先なし", "add 自己依存", "set 循環", "set 依存先なし",
                    "add 2 度目", "set 台帳に無い", "set 無い状態", "set 無い鍵"):
            check(f"{key} は 3", o[key] == 3)
        check("鍵=値でない set は 2", o["set 鍵=値でない"] == 2)
        check("番号でない add は 2", o["add 番号でない"] == 2)
        check("拒んだ操作のあとも台帳が 1 バイトも変わらない", o["拒んだ後も同じ"])

        print("\nnext（L6）")
        check("初めは依存なしの #1 と #5", o["next(初め)"] == ["1", "5"])
        for key in ("next(依存が PR 中)", "next(依存が止まっている)", "next(依存が取り下げ)"):
            check(f"{key}: #5 だけ", o[key] == ["5"])
        check("依存がマージ済みなら #2 と #4 も", o["next(依存がマージ済み)"] == ["2", "4", "5"])
        check("show が 3 区分を出す", o["show rc"] == 0 and o["show 進行中"]
              and o["show 着手できる"] and o["show 依存待ち"])
        check("show が書いた値を出す", o["show の値"])
        check("set が台帳に書く", o["set で書いた値"] == [(1, "merged", "#101"), (2, "impl", "")])

        print("\n読めない台帳（L7）")
        check("無い台帳の show / next は 4", o["show(無い)"] == 4 and o["next(無い)"] == 4)
        check("壊れた JSON の next / set は 4", o["next(壊れた JSON)"] == 4 and o["set(壊れた JSON)"] == 4)
        check("壊れた JSON を書き換えない", o["壊れた JSON を書き換えない"])
        check("形が違う台帳は 4", o["next(形が違う)"] == 4)

        print("\n名前（L8）・git の外（L9）")
        check("../x・a/b・.x・x/../../../escaped は 2",
              (o["名前 ../x"], o["名前 a/b"], o["名前 .x"], o["名前 x/../../../escaped"]) == (2, 2, 2, 2))
        check(".claude/plans の外に書いていない", o["plans の外に書いていない"])
        check("git の外は 4", o["git の外"] == 4)

        print("\n終了コードが docstring の表と一致する（L10）")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", table, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_USAGE, mod.EXIT_REJECTED, mod.EXIT_UNKNOWN}
        check(f"表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)
        states = re.findall(r"^\| `([a-z]+)` \|", source.split("**状態**")[1].split("**鍵**")[0], re.M)
        check(f"状態の表 {states} と STATES", tuple(states) == mod.STATES)

        print("\n変異テスト（壊したのに緑なら失格。L11）")
        for name, pairs in MUTATIONS.items():
            mutated = source
            missing = [n for n, _ in pairs if n not in mutated]
            if missing:
                check(f"変異を当てる先がある: {name}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement, 1)
            d = tmp / f"mut-{abs(hash(name))}"
            d.mkdir()
            broken = d / "ledger.py"
            broken.write_text(mutated, encoding="utf-8")
            try:
                got = scenario(load(broken), tmp, f"mut-{abs(hash(name))}")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", got != o)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [l for l in body.splitlines() if l.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件",
              len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め（L12）")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("台帳のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
