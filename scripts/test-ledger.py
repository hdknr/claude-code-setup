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
    # サブモジュールの試料はローカルのパスから足すので、file プロトコルを許す（この呼び出しだけ）
    subprocess.run(["git", "-c", "protocol.file.allow=always", *args],
                   cwd=root, capture_output=True, text=True, check=False)


def isolate_env(home: Path) -> None:
    """**`GIT_*` を外し、`HOME` と git の設定を差し替える**——`GIT_DIR` が他のリポジトリを指す環境
    （フックの中から回したなど）では、外さないと試料の `git commit`・`git config` と本体の場所の解決が
    そのリポジトリに当たる（#390 の 1 パス目で実測）。本体は子プロセスで git を呼ぶので、`os.environ` ごと替える。"""
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[key]
    home.mkdir()
    (home / "gitconfig").write_text("[user]\n\temail = t@example.invalid\n\tname = t\n", encoding="utf-8")
    os.environ.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")


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

    # L7: 中身の崩れた台帳（手で直した）。**3 ではなく 4、next は答えない、書き換えない**
    def plant(name, issues):
        f = root / ".claude" / "plans" / f"cruise-{name}.json"
        f.write_text(json.dumps({"format": 1, "name": name, "issues": issues}), encoding="utf-8")
        return f

    def entry(n, deps):
        return {"number": n, "state": "todo", "deps": deps}

    for name, issues in (("dup", [entry(1, []), entry(1, [])]),
                         ("cyc", [entry(1, [2]), entry(2, [1])]),
                         ("miss", [entry(1, [9])])):
        f = plant(name, issues)
        before = f.read_bytes()
        o[f"崩れた {name}"] = (run(mod, ["next", name], root)[:2], run(mod, ["set", name, "1", "note=x"], root)[0],
                              run(mod, ["add", name, "5"], root)[0], f.read_bytes() == before)
    plant("bool", [{"number": True, "state": "todo", "deps": []}])
    o["真偽値の番号"] = run(mod, ["next", "bool"], root)[:2]
    # 形の誤り（#390 の 2 パス目）: `true == 1`・`1.0 == 1` の format・決まった一覧に無い欄・ファイル名と違う name
    plans = root / ".claude" / "plans"
    for name, data in (("ftrue", {"format": True, "name": "ftrue", "issues": [entry(1, [])]}),
                       ("ffloat", {"format": 1.0, "name": "ffloat", "issues": [entry(1, [])]}),
                       ("extra", {"format": 1, "name": "extra", "issues": [{**entry(1, []), "colour": "red"}]}),
                       ("other", {"format": 1, "name": "OTHER", "issues": [entry(1, [])]})):
        (plans / f"cruise-{name}.json").write_text(json.dumps(data), encoding="utf-8")
        o[f"形の誤り {name}"] = run(mod, ["next", name], root)[:2]
    # 台帳に無い Issue への `鍵=値` の形の誤りは 2（Issue を先に引くと 3 になる）
    o["set 台帳に無い・鍵=値でない"] = run(mod, ["set", "c", "42", "bad"], root)[0]
    # 名前が長すぎる・読む権限が無い: 在るかを確かめる段で素の例外にしない（Python 3.13 以前）
    o["名前が長すぎる show"] = run(mod, ["show", "x" * 300], root)[0]
    o["名前が長すぎる init"] = run(mod, ["init", "x" * 300], root)[0]
    locked = tmp / f"locked-{tag}"
    locked.mkdir()
    git(locked, "init", "-q")
    (locked / ".claude" / "plans").mkdir(parents=True)
    (locked / ".claude" / "plans").chmod(0)
    try:
        r = run(mod, ["next", "c"], locked)
        o["読めない plans の next"] = (r[0], "台帳が無い" not in str(r[2]))
    finally:
        (locked / ".claude" / "plans").chmod(0o755)

    # L12（#458）: 確かめた線と、要確認 Issue の番号
    run(mod, ["init", "ln"], root)
    run(mod, ["add", "ln", "1"], root)
    lf = root / ".claude" / "plans" / "cruise-ln.json"
    o["lines 通る"] = run(mod, ["lines", "ln", "仕様の穴=推奨で決めて起票", "直す線=既定", "--source", "s1"], root)[0]
    before = snapshot(lf)
    o["lines 拒む"] = tuple(run(mod, ["lines", "ln", *pairs, "--source", src], root)[0] for pairs, src in (
        (["本番反映=する"], "s"), (["仕様の穴=決める"], "s"), (["速さ=速い"], "s"),
        (["直す線=既定", "直す線=広げる"], "s"), (["直す線=既定"], " ")))
    o["lines 鍵=値でない"] = run(mod, ["lines", "ln", "直す線", "--source", "s"], root)[0]
    o["lines 拒んだ後も同じ"] = snapshot(lf) == before
    o["lines 置き換え"] = run(mod, ["lines", "ln", "マージ=止まる", "--source", "s2"], root)[0]
    try:
        # `updated` は時刻なので観測に入れない——入れると、走った秒が違うだけで全変異が「殺せた」になる
        o["lines の値"] = {k: v for k, v in json.loads(lf.read_text(encoding="utf-8"))["lines"].items()
                          if k != "updated"}
    except (OSError, ValueError, KeyError):
        o["lines の値"] = None
    r = run(mod, ["show", "ln"], root)
    o["lines の show"] = (r[0], "確かめた線（出所: s2・" in str(r[1]) and "マージ = 止まる" in str(r[1]))
    o["線の無い show"] = "確かめた線: 無い" in str(run(mod, ["show", "c"], root)[1])
    o["decisions"] = (run(mod, ["set", "ln", "1", "decisions=12, 13"], root)[0],
                      run(mod, ["set", "ln", "1", "decisions=x"], root)[0])
    try:
        o["decisions の値"] = json.loads(lf.read_text(encoding="utf-8"))["issues"][0]["decisions"]
    except (OSError, ValueError, KeyError, IndexError):
        o["decisions の値"] = None
    # 手で崩した線は 4（next は答えない）。線と decisions を持たない台帳はこれまでどおり読む
    for name, extra in (("lbad", {"lines": {"values": {"本番反映": "する"}, "source": "s", "updated": ""}}),
                        ("lval", {"lines": {"values": {"マージ": "する"}, "source": "s", "updated": ""}}),
                        ("lsrc", {"lines": {"values": {}, "source": " ", "updated": ""}}),
                        ("lshape", {"lines": {"values": {}, "source": "s"}}),
                        ("ldec", {"issues": [{**entry(1, []), "decisions": "x"}]}),
                        ("lorig", {"issues": [{**entry(1, []), "origin": 5}]}),
                        ("lold", {})):
        data = {"format": 1, "name": name, "issues": [entry(1, [])], **extra}
        (plans / f"cruise-{name}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        o[f"線の形 {name}"] = run(mod, ["next", name], root)[:2]

    # L13（#464）: 周の途中で足した行の出所
    run(mod, ["init", "fo"], root)
    run(mod, ["add", "fo", "1"], root)
    o["origin の add"] = run(mod, ["add", "fo", "2", "--deps", "1", "--origin", "#1 狭いパス"], root)[:2]
    o["origin の set"] = run(mod, ["set", "fo", "1", "origin=手"], root)[0]
    # 空の出所は拒み、台帳を変えない（下の「origin の値」に #3 が無く #2 の出所が残ることで見る）
    o["origin の空"] = (run(mod, ["add", "fo", "3", "--deps", "1", "--origin", " "], root)[0],
                        run(mod, ["set", "fo", "2", "origin="], root)[0])
    # 出所を持つ行は依存を空にできない（下の「origin の値」に #4 が無く #2 の依存が残ることで見る）
    o["origin の依存なし"] = (run(mod, ["add", "fo", "4", "--origin", "#1 狭いパス"], root)[0],
                            run(mod, ["set", "fo", "2", "deps="], root)[0])
    try:
        o["origin の値"] = [(i["number"], i["origin"], i["deps"]) for i in json.loads(
            (plans / "cruise-fo.json").read_text(encoding="utf-8"))["issues"]]
    except (OSError, ValueError, KeyError):
        o["origin の値"] = None
    r = str(run(mod, ["show", "fo"], root)[1])
    o["origin の show"] = ("| 出所 |" in r, "| #1 狭いパス |" in r,
                           "周の途中で足した行のうち済んでいないもの: #1(todo), #2(todo)" in r)
    run(mod, ["set", "fo", "1", "state=merged"], root)
    run(mod, ["set", "fo", "2", "state=dropped"], root)
    r = str(run(mod, ["show", "fo"], root)[1])
    o["origin の show(済み)"] = "周の途中で足した行のうち済んでいないもの: なし" in r
    o["origin の無い show"] = "周の途中で足した行" not in str(run(mod, ["show", "ln"], root)[1])

    # L9: git の外。**無い台帳の `show` では判別しない**——台帳が無いことでも 4 になる。
    # 場所の解決そのものを当てる `path` と `init` を使い、何も書いていないことも見る
    outside = tmp / f"outside-{tag}"
    outside.mkdir()
    o["git の外"] = (run(mod, ["path", "c"], outside)[0], run(mod, ["init", "c"], outside)[0],
                     list(outside.iterdir()))

    # L10: 書けない（`.claude/plans` がファイル）。**別のリポジトリで**——上の台帳を巻き込まない
    flat = tmp / f"flat-{tag}"
    flat.mkdir()
    git(flat, "init", "-q")
    (flat / ".claude").mkdir()
    (flat / ".claude" / "plans").write_text("ファイル\n", encoding="utf-8")
    o["書けない init"] = run(mod, ["init", "c"], flat)[0]
    # 保存の段まで届く「書けない」: 台帳は在って読めるが、`.claude/plans` に一時ファイルを作れない。
    # **上の試料は在るかを確かめる段で 4 になり、保存の段に届かない**（#390 の 2 パス目）
    ro = tmp / f"ro-{tag}"
    ro.mkdir()
    git(ro, "init", "-q")
    run(mod, ["init", "c"], ro)
    (ro / ".claude" / "plans").chmod(0o555)
    try:
        o["書けない add"] = run(mod, ["add", "c", "1"], ro)[0]
    finally:
        (ro / ".claude" / "plans").chmod(0o755)

    # L1: `--separate-git-dir` とサブモジュール。**作業ツリーの外を指さない**
    base = tmp / f"layouts-{tag}"
    base.mkdir()

    def where2(cwd):
        r = run(mod, ["path", "c"], cwd)
        return (r[0], str(r[1]).strip().replace(str(base), "<base>"))

    git(base, "init", "-q", "--separate-git-dir", str(base / "sepgit"), "sep")
    git(base / "sep", "commit", "-q", "--allow-empty", "-m", "x")
    git(base / "sep", "worktree", "add", "-q", str(base / "sep-wt"))
    o["sep(メイン)"] = where2(base / "sep")
    o["sep(worktree)"] = where2(base / "sep-wt")
    git(base, "init", "-q", "lib")
    git(base / "lib", "commit", "-q", "--allow-empty", "-m", "l")
    git(base, "init", "-q", "sup")
    git(base / "sup", "commit", "-q", "--allow-empty", "-m", "s")
    git(base / "sup", "submodule", "add", "-q", str(base / "lib"), "m")
    git(base / "sup" / "m", "worktree", "add", "-q", str(base / "m-wt"))
    o["sub(メイン)"] = where2(base / "sup" / "m")
    o["sub(worktree)"] = where2(base / "m-wt")
    # bare を `<dir>/.git` に置いた形（#390 の 2 パス目）: 根からも worktree からも、作業ツリーでない <dir> を指さない
    git(base, "clone", "-q", "--bare", str(base / "lib"), str(base / "bp" / ".git"))
    git(base / "bp", "worktree", "add", "-q", str(base / "bp" / "main-wt"))
    o["bare(根)"] = where2(base / "bp")[0]
    o["bare(worktree)"] = where2(base / "bp" / "main-wt")[0]
    o["bare の worktree が在る"] = (base / "bp" / "main-wt" / ".git").is_file()
    return o


# 1 件ずつ (探す文字列, 置き換え) の組。複数の組で 1 つの変異にしてよい。
MUTATIONS = {
    # 守る: 場所は cwd に依らない
    "共通ディレクトリでなく worktree の git-dir を使う": [
        ("git_dir, common = Path(lines[0]), Path(lines[1])", "git_dir, common = Path(lines[0]), Path(lines[0])")],
    # 守る: separate-git-dir・サブモジュールでも作業ツリーの外に書かない
    "共通ディレクトリの親を無条件に使う": [
        ('    if common.name == ".git":\n', "    if True:\n")],
    # 守る: init で上書きしない
    "在る台帳に init で上書きする": [
        ("    if exists(path):\n        raise Refused", "    if False:\n        raise Refused")],
    # 守る: 決まった一覧に無い状態を拒む
    "無い状態を通す": [
        ('        if issue["state"] not in STATES:\n            raise Refused',
         '        if False:\n            raise Refused')],
    # 守る: 依存の循環を拒む
    "循環を見ない": [
        ("    for n in graph:\n        visit(n, [])", "    pass")],
    # 守る: next は依存がすべてマージ済みのものだけ
    "依存が未着手でなければ済んだと読む": [
        ('all(state.get(d) == DONE for d in i["deps"])', 'all(state.get(d) != "todo" for d in i["deps"])')],
    # 守る: 読めない台帳を空と読まない
    "無い台帳を空と読む": [
        ('        raise Unknown(f"台帳が無い: {path}")',
         '        return {"format": FORMAT, "name": "", "issues": []}')],
    # 守る: 中身の崩れた台帳に答えない
    "読み込みで整合を見ない": [
        ("    try:\n        validate(data)\n    except Refused as exc:\n        raise Unknown(f\"台帳の中身",
         "    try:\n        pass\n    except Refused as exc:\n        raise Unknown(f\"台帳の中身")],
    # 守る: 書けなかったときに表に無い終了コードで終えない
    "書けないときに素の例外で終える": [
        ("    except OSError as exc:  # 書けない", "    except ImportError as exc:  # 書けない")],
    # 守る: 名前にパスの区切りと先頭のドットを許さない
    "名前を何でも通す": [
        ('NAME_RE = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9._-]*")', 'NAME_RE = re.compile(r".+")')],
    # 守る: 拒んだ操作では台帳を変えない（検査してから書く）
    "一覧に無い線を書く": [
        ("def check_line(key, value):\n", "def check_line(key, value):\n    return\n")],
    # `cmd_lines` だけ外しても `validate` が拒むので挙動は変わらない（等価変異）——両方を外す
    # （`validate` だけ外す変異は、手で崩した台帳 `lsrc` の観測で殺せる）
    "出所の無い線を書く": [
        ('    if not source.strip():\n        raise Refused("出所が空', '    if False:\n        raise Refused("出所が空'),
        ('    if "lines" in data and not data["lines"]["source"].strip():',
         '    if False:')],
    # 守る: origin も文字列だけ
    "origin の型を見ない": [
        ('TEXT_KEYS = ("title", "pr", "branch", "worktree", "agent", "base", "note", "decisions", "origin")',
         'TEXT_KEYS = ("title", "pr", "branch", "worktree", "agent", "base", "note", "decisions")')],
    # 守る: origin を空で書かない
    "add の空の origin を通す": [
        ("    if origin is not None and not origin.strip():", "    if False:")],
    "set の空の origin を通す": [
        ('        elif key == "origin" and not value.strip():', '        elif False:')],
    # 守る: 出所を持つ行は元の周に依存する
    "add の依存の無い origin を通す": [
        ("    if origin is not None and not deps:", "    if False:")],
    "set で出所のある行の依存を消せる": [
        ('    if "deps" in changes and not changes["deps"] and changes.get("origin", issue.get("origin")):',
         "    if False:")],
    "書いてから検査する": [
        ("def save(path, data):\n    validate(data)\n", "def save(path, data):\n"),
        ("        os.replace(tmp, path)\n", "        os.replace(tmp, path)\n        validate(data)\n")],
}


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t).resolve()
        isolate_env(tmp / "home")
        mod = load()
        o = scenario(mod, tmp, "correct")

        print("場所（L1）")
        paths = {o["path(main)"], o["path(sub)"], o["path(worktree)"], o["path(worktree/sub)"]}
        check("4 つの cwd から同じパスを指す", len(paths) == 1)
        check("メインの作業ツリーの .claude/plans/cruise-c.json",
              o["path(main)"] == "<root>/.claude/plans/cruise-c.json")
        check("worktree の中から init してもメインに置かれる", o["init"] == 0 and o["init の置き場所"])
        check("separate-git-dir: メインの作業ツリーからは作業ツリーの下",
              o["sep(メイン)"] == (0, "<base>/sep/.claude/plans/cruise-c.json"))
        check("separate-git-dir: worktree の中からは決められないので 4（git-dir の隣に書かない）",
              o["sep(worktree)"][0] == 4)
        check("サブモジュール: 作業ツリーの下（.git/modules の下ではない）",
              o["sub(メイン)"] == (0, "<base>/sup/m/.claude/plans/cruise-c.json"))
        check("サブモジュールの worktree の中からも同じパス", o["sub(worktree)"] == o["sub(メイン)"])
        check("bare（<dir>/.git）の試料が作れている（作れないと 4 == 4 で素通りする）", o["bare の worktree が在る"])
        check("bare: 根からも worktree の中からも 4（作業ツリーでない <dir> を指さない）",
              (o["bare(根)"], o["bare(worktree)"]) == (4, 4))

        print("\ninit（L2）")
        check("2 度目の init は 3", o["init(2 度目)"] == 3)
        check("2 度目の init で中身が変わらない", o["init(2 度目) 後も同じ"])

        print("\n拒む操作（L3〜L5）")
        check("足すのは通る", all(o[f"add {n}"] == 0 for n in range(1, 6)))
        for key in ("add 依存先なし", "add 自己依存", "set 循環", "set 依存先なし",
                    "add 2 度目", "set 台帳に無い", "set 無い状態", "set 無い鍵"):
            check(f"{key} は 3", o[key] == 3)
        check("鍵=値でない set は 2", o["set 鍵=値でない"] == 2)
        check("台帳に無い Issue でも、鍵=値でない set は 2（3 ではない）", o["set 台帳に無い・鍵=値でない"] == 2)
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
        check("真偽値の番号は形の誤りで 4（next は答えない）", o["真偽値の番号"] == (4, ""))
        for name in ("dup", "cyc", "miss"):
            check(f"中身の崩れた台帳（{name}）: next は答えずに 4・set / add も 3 ではなく 4・書き換えない",
                  o[f"崩れた {name}"] == ((4, ""), 4, 4, True))
        for name in ("ftrue", "ffloat", "extra", "other"):
            check(f"形の誤り（{name}）は 4（next は答えない）", o[f"形の誤り {name}"] == (4, ""))
        check("書けない（.claude/plans がファイル）init は 4", o["書けない init"] == 4)
        check("書けない（.claude/plans に一時ファイルを作れない）add は 4", o["書けない add"] == 4)
        check("名前が長すぎる show / init は 4（素の例外にしない）",
              (o["名前が長すぎる show"], o["名前が長すぎる init"]) == (4, 4))
        check("読む権限の無い .claude/plans の next は 4 で、「台帳が無い」とは言わない",
              o["読めない plans の next"] == (4, True))

        print("\n確かめた線と要確認（L12・#458）")
        check("lines は通る", o["lines 通る"] == 0)
        check("本番反映・一覧に無い値・一覧に無い項目・同じ項目 2 度・空の出所は 3",
              o["lines 拒む"] == (3, 3, 3, 3, 3))
        check("項目=値でない lines は 2", o["lines 鍵=値でない"] == 2)
        check("拒んだ lines のあとも台帳が 1 バイトも変わらない", o["lines 拒んだ後も同じ"])
        check("lines は置き換え（渡さなかった項目は消える）・出所を残す",
              o["lines 置き換え"] == 0 and o["lines の値"] is not None
              and o["lines の値"]["values"] == {"マージ": "止まる"} and o["lines の値"]["source"] == "s2")
        check("show が確かめた線と出所を出す", o["lines の show"] == (0, True))
        check("線の無い台帳の show は「無い」と出す", o["線の無い show"])
        check("decisions は番号のカンマ区切りだけ（番号でなければ 3）",
              o["decisions"] == (0, 3) and o["decisions の値"] == "12,13")
        for name in ("lbad", "lval", "lsrc", "lshape", "ldec", "lorig"):
            check(f"手で崩した線・decisions・origin（{name}）は 4（next は答えない）", o[f"線の形 {name}"] == (4, ""))
        check("線と decisions と origin を持たない台帳はこれまでどおり読む", o["線の形 lold"] == (0, "1\n"))
        absent = (REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "references" / "absent-lines.md"
                  ).read_text(encoding="utf-8").split("## 線と既定")[1].split("\n## ")[0]
        rows = {k: (d, v) for k, d, v in re.findall(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|", absent, re.M)}
        skill = (REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "SKILL.md").read_text(encoding="utf-8")
        check(f"LINES が absent-lines.md の「線と既定」の表 {rows} と一致する（直す線・周の途中の課題を除く）",
              {k: v for k, v in mod.LINES.items() if k not in ("直す線", "周の途中の課題")} == rows)
        check("本番反映は LINES に無い", "本番反映" not in mod.LINES and "| `本番反映` |" in absent)
        check("直す線は SKILL.md 手順 3 の 2 値（既定・広げる）",
              mod.LINES["直す線"] == ("既定", "広げる") and "`直す線: 既定` か `直す線: 広げる`" in skill)
        found = (REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "references" / "found-lines.md"
                 ).read_text(encoding="utf-8")
        check("周の途中の課題は found-lines.md の 2 値（既定が外に出す）",
              mod.LINES["周の途中の課題"] == ("外に出す", "台帳に足して直す")
              and "`周の途中の課題 = 外に出す`（既定）" in found and "`周の途中の課題 = 台帳に足して直す`" in found)

        print("\n周の途中で足した行の出所（L13・#464）")
        check("add --origin が出所を残す", o["origin の add"][0] == 0 and "出所: #1 狭いパス" in str(o["origin の add"][1]))
        check("set origin= が通り、親 Issue から作った行は空・足した行は依存を持つ", o["origin の set"] == 0
              and o["origin の値"] == [(1, "手", []), (2, "#1 狭いパス", [1])])
        check("add --origin の空・set origin= は 3（台帳は変えない）", o["origin の空"] == (3, 3))
        check("add --origin に --deps が無い・出所のある行の set deps= は 3（台帳は変えない）",
              o["origin の依存なし"] == (3, 3))
        check("show が出所の列と、済んでいない足した行を出す", o["origin の show"] == (True, True, True))
        check("足した行がすべて merged か dropped なら「なし」", o["origin の show(済み)"])
        check("足した行の無い台帳の show は、その行を出さない", o["origin の無い show"])

        print("\n名前（L8）・git の外（L9）")
        check("../x・a/b・.x・x/../../../escaped は 2",
              (o["名前 ../x"], o["名前 a/b"], o["名前 .x"], o["名前 x/../../../escaped"]) == (2, 2, 2, 2))
        check(".claude/plans の外に書いていない", o["plans の外に書いていない"])
        check("git の外は path も init も 4 で、何も書かない", o["git の外"] == (4, 4, []))

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
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**——構文の誤りでも下の例外で
            # 殺せたと数えてしまい、主張を 1 度も当てずに緑になる（#390 の 2 パス目）
            try:
                mutant = load(broken)
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, tmp, f"mut-{abs(hash(name))}")
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
