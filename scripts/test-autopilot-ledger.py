#!/usr/bin/env python3
"""`autopilot-ledger.py`（spec-loop の autopilot の台帳。#848）の回帰テスト。

    python3 scripts/test-autopilot-ledger.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-qa-csv.py` と同じ形。

**このテストは実環境を触らない。** 毎回テンポラリに本物の git リポジトリと worktree を作り、そこだけを対象にする
（`assert_not_real_repo` がそれを担保する）。本体は cwd からメインの作業ツリーを解決して `.claude/plans/` に書くので、
**歯止めが無いと、テストがこのリポジトリ自身に台帳を書く。**

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに観測がそろったままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が期待どおりであること（下の「正しい本体」）。**主張とテストを 1 対 1 にする**——
本体の docstring の「守る」の行数と変異の数が等しいことを、テスト自身が数えて見る。終了コードも docstring の表と突き合わせる。

**`main_worktree`・`_git`・`exists` は dev-loop の `ledger.py` の写しである**（本体の docstring）——2 つのソースが同じことも見る
（写しを片方だけ直すと落ちる。陽性対照として、1 文字変えた写しで「違う」と出ることも見る）。

**時刻は差し替える**——本体の `now()` を呼ぶたびに違う値を返す関数にする。同じ秒に書いた `updated` は変わらないので、
差し替えないと「`progress` に `updated` を混ぜる」変異が素通りする。
"""
import ast
import contextlib
import io
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "plugins" / "spec-loop" / "scripts" / "autopilot-ledger.py"
ORIGINAL = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop" / "scripts" / "ledger.py"
COPIED = ("_git", "main_worktree", "exists")

failures: list[str] = []

# 本体の docstring の「守る」の各行に 1 つずつ。(探す文字列, 置き換え) の組
MUTATIONS = {
    "場所を cwd の作業ツリーで決める": [
        ('return main_worktree(cwd) / ".claude"', 'return Path(_git(cwd, "rev-parse", "--show-toplevel")) / ".claude"')],
    "版に先頭の 0 を許す": [('VERSION_RE = re.compile(r"[1-9][0-9]*")', 'VERSION_RE = re.compile(r"[0-9]+")')],
    "在る台帳を init で上書きする": [("    if exists(path):\n        raise Refused(f\"台帳は既に在る", "    if False:\n        raise Refused(f\"台帳は既に在る")],
    "version・updated を set で書ける": [("        if key not in KEYS:\n", "        if key not in FIELDS:\n")],
    "一覧に無い stage を通す": [('    if data["stage"] and data["stage"] not in STAGES:\n', "    if False:\n")],
    "cycle の 0 を通す": [("and value >= 1", "and value >= 0")],
    "commit の短い値を通す": [('COMMIT_RE = re.compile(r"[0-9a-f]{7,40}")', 'COMMIT_RE = re.compile(r"[0-9a-f]{1,40}")')],
    "絶対パス・.. を指せる": [('    if path.is_absolute() or value.startswith("~") or ".." in path.parts:\n', "    if False:\n")],
    "status と phase の done を食い違わせる": [('    if (data["status"] == "done") != (data["phase"] == "done"):\n', "    if False:\n")],
    "理由の無い stopped を通す": [('        if not data["reason"].strip() or not data["next"].strip():\n', "        if False:\n")],
    "running に古い理由を残す": [('    elif data["reason"] or data["next"]:\n', "    elif False:\n")],
    "出所の無い線を書く": [('    if not source.strip():\n        raise Refused("線の出所が空', '    if False:\n        raise Refused("線の出所が空')],
    "線を置き換えずに足す": [('    data["lines"] = {"values": values,',
                          '    data["lines"] = {"values": {**data.get("lines", {}).get("values", {}), **values},')],
    "検査の前に書く": [("def save(path, data):\n    validate(data)\n", "def save(path, data):\n"),
                  ("        os.replace(tmp, path)\n", "        os.replace(tmp, path)\n        validate(data)\n")],
    "status で台帳を書く": [('    data = load(path, version)\n    status = data["status"]\n',
                         '    data = load(path, version)\n    data["updated"] = now()\n    save(path, data)\n    status = data["status"]\n')],
    "壊れた JSON を running と読む": [
        ('raise Unknown(f"台帳を読めない: {path}: {exc}") from exc',
         'return {"format": 1, "version": version, "phase": "spec-review", "cycle": 1, "stage": "", "commit": "", '
         '"status": "running", "reason": "", "next": "", "triage": "", "held": "", "updated": ""}')],
    "知らない欄を通す": [('not FIELDS <= set(data) <= FIELDS | {"lines"}', "not FIELDS <= set(data)")],
    "崩れた台帳を拒んだ（3）と言う": [('raise Unknown(f"台帳の中身が崩れている: {path}: {exc}") from exc', "raise")],
    "status を phase で決める": [("    return STATUS_CODES[status]\n", '    return EXIT_DONE if data["phase"] == "done" else EXIT_OK\n')],
    "progress に updated を混ぜる": [('PROGRESS_KEYS = ("phase", "cycle", "stage", "commit")',
                                 'PROGRESS_KEYS = ("phase", "cycle", "stage", "commit", "updated")')],
    "progress から commit を落とす": [('PROGRESS_KEYS = ("phase", "cycle", "stage", "commit")', 'PROGRESS_KEYS = ("phase", "cycle", "stage")')],
    "書けないと例外で終える": [("    except OSError as exc:  # 書けない", "    except ZeroDivisionError as exc:  # 書けない")],
}


def load(script: Path = SCRIPT):
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"apl_{id(script)}_{script.stat().st_mtime_ns}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ticks = itertools.count(1)
    mod.now = lambda: f"2026-11-05T00:00:{next(ticks):02d}Z"  # 呼ぶたびに違う時刻（上の docstring）
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


def isolate_env(home: Path) -> None:
    """`GIT_*` を外し、`HOME` と git の設定を差し替える（本体は子プロセスで git を呼ぶので `os.environ` ごと）。"""
    for key in [k for k in os.environ if k.startswith("GIT_")]:
        del os.environ[key]
    home.mkdir()
    (home / "gitconfig").write_text("[user]\n\temail = t@example.invalid\n\tname = t\n", encoding="utf-8")
    os.environ.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")


def build_repo(root: Path) -> Path:
    """本物のリポジトリと、その `.claude/worktrees/w` に本物の worktree。worktree のパスを返す。"""
    assert_not_real_repo(root.parent)
    root.mkdir(parents=True)
    git(root, "init", "-q")
    (root / "sub").mkdir()
    (root / "sub" / "x.txt").write_text("x\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    wt = root / ".claude" / "worktrees" / "w"
    git(root, "worktree", "add", "-q", str(wt), "-b", "wt")
    (wt / "sub").mkdir(exist_ok=True)
    return wt


def snapshot(path: Path):
    """ファイルのバイト列。無ければ None。"""
    return path.read_bytes() if path.is_file() else None


def run(mod, argv, cwd):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = mod.main(argv, cwd=str(cwd))
        except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
            return ("例外", type(exc).__name__, "")
    return (rc, out.getvalue(), err.getvalue())


def scenario(mod, base: Path, tag: str) -> dict:
    """1 つの本体に全試料を当て、観測を辞書で返す。**観測にはテンポラリのパスを入れない**（変異と比べるため）。"""
    root = base / tag / "repo"
    wt = build_repo(root)
    o = {}
    rc = lambda argv, cwd=root: run(mod, argv, cwd)[0]  # noqa: E731
    ledger = root / ".claude" / "plans" / "spec-autopilot-v3.json"

    # 場所: メインの作業ツリー・worktree・worktree のサブディレクトリで同じ
    paths = [run(mod, ["path", "3"], c)[1].strip() for c in (root, wt, wt / "sub")]
    o["場所"] = [p == str(ledger) for p in paths]

    # 版の名前
    o["版"] = [rc([cmd, v]) for cmd in ("init", "path") for v in ("03", "0", "-1", "../x", "3 ", "a", "３")]

    # init と、2 度目の init
    o["init"] = rc(["init", "3"])
    before = snapshot(ledger)
    o["init 2 度目"] = (rc(["init", "3", "--phase", "feasibility"]), snapshot(ledger) == before)
    o["progress 初期"] = run(mod, ["progress", "3"], root)[1]
    o["status 初期"] = run(mod, ["status", "3"], root)[:2]

    def refused(argv, cwd=root):
        """拒まれた操作の終了コードと、台帳が 1 バイトも変わらなかったか。"""
        b = snapshot(ledger)
        return (rc(argv, cwd), snapshot(ledger) == b)

    o["鍵"] = [refused(["set", "3", p]) for p in ("version=4", "updated=x", "format=2", "foo=1")]
    o["鍵の形"] = refused(["set", "3", "stage"])
    o["値"] = [refused(["set", "3", p]) for p in ("phase=spec_review", "stage=round3", "status=paused")]
    o["cycle"] = [refused(["set", "3", p]) for p in ("cycle=0", "cycle=x", "cycle=01", "cycle=-1")]
    o["commit"] = [refused(["set", "3", p]) for p in ("commit=abc", "commit=ABCDEF1", "commit=" + "a" * 41, "commit=abcdef1g")]
    o["指す先"] = [refused(["set", "3", p]) for p in ("triage=/tmp/x", "triage=../x", "held=a/../../x", "held=~/x")]
    o["done の整合"] = [refused(["set", "3", p]) for p in ("status=done", "phase=done")]
    o["stopped の理由"] = [refused(["set", "3", *ps]) for ps in (
        ["status=stopped"], ["status=stopped", "reason=r"], ["status=stopped", "next=n"],
        ["status=stopped", "reason= ", "next=n"])]
    o["running の古い理由"] = refused(["set", "3", "reason=r"])

    # progress: 進捗の欄以外の書き換えでは変わらず、進捗の欄が変われば変わる
    p0 = run(mod, ["progress", "3"], root)[1]
    unchanged = []
    for argv in (["set", "3", "status=stopped", "reason=権限で拒まれた", "next=許可を足す"],
                 ["set", "3", "reason=再確認したが止まったまま"],  # #790 の形: 理由と時刻だけを書き直す
                 ["set", "3", "status=running", "reason=", "next="],
                 ["set", "3", "triage=.claude/plans/triage.csv", "held=.claude/plans/held.md"],
                 ["lines", "3", "上限で続ける周=5", "--source", "利用者（起動時）"],
                 ["set", "3", "stage=planner"]):
        b = snapshot(ledger)
        r = rc(argv)
        unchanged.append((r, snapshot(ledger) != b, run(mod, ["progress", "3"], root)[1] == p0))
    o["progress は変わらない"] = unchanged
    changed = []
    for argv in (["set", "3", "stage=round1"], ["set", "3", "cycle=2"], ["set", "3", "commit=abcdef1"],
                 ["set", "3", "phase=feasibility", "stage="]):
        prev = run(mod, ["progress", "3"], root)[1]
        changed.append((rc(argv), run(mod, ["progress", "3"], root)[1] != prev))
    o["progress は変わる"] = changed
    o["progress の行"] = run(mod, ["progress", "3"], root)[1]

    # 線: 置き換え・出所・空
    o["線"] = [refused(["lines", "3", "a=b", "--source", s]) for s in ("", "  ")]
    o["線の空"] = [refused(["lines", "3", p, "--source", "s"]) for p in ("=b", "a=", "a= ")]
    o["線の 2 度"] = refused(["lines", "3", "a=b", "a=c", "--source", "s"])
    rc(["lines", "3", "a=b", "--source", "s1"])
    rc(["lines", "3", "c=d", "--source", "s2"])
    o["線は置き換え"] = json.loads(ledger.read_text(encoding="utf-8")).get("lines", {}).get("values")

    # status: 欄だけで決める。止まっても phase は spec-review のまま（#790 の形）
    rc(["set", "3", "phase=spec-review", "stage=fix1"])
    rc(["set", "3", "status=stopped", "reason=マージが拒まれた", "next=許可を足すかマージを人に残す"])
    o["status stopped"] = run(mod, ["status", "3"], root)[:2]
    b = snapshot(ledger)
    o["読むだけ"] = [rc([c, "3"]) for c in ("status", "progress", "show", "path")] + [snapshot(ledger) == b]
    o["stopped にも書ける"] = rc(["set", "3", "status=running", "reason=", "next="])
    o["status running"] = rc(["status", "3"])
    o["status done"] = (rc(["set", "3", "phase=done", "status=done"]), rc(["status", "3"]))
    o["show"] = run(mod, ["show", "3"], root)[0]

    # 手で直した台帳: 形の違い・崩れ・壊れた JSON・無い台帳
    # 手で直す元は、本体が書いた台帳ではなく固定の正しい台帳（変異が台帳を崩しても、試料が崩れない）。陽性対照として、そのまま読めば 5
    good = {"format": 1, "version": 3, "phase": "done", "cycle": 2, "stage": "fix1", "commit": "abcdef1", "status": "done",
            "reason": "", "next": "", "triage": "", "held": "", "updated": "t", "lines": {"values": {"c": "d"}, "source": "s2", "updated": "t"}}
    o["書いた台帳の欄"] = sorted(json.loads(ledger.read_text(encoding="utf-8")))
    ledger.write_text(json.dumps(good, ensure_ascii=False), encoding="utf-8")
    o["固定の正しい台帳"] = rc(["status", "3"])
    hand = []
    for change in (lambda d: d.update(extra=1), lambda d: d.pop("held"), lambda d: d.update(cycle=True),
                   lambda d: d.update(version=4), lambda d: d.update(format=1.0), lambda d: d.update(reason=1),
                   lambda d: d.update(lines={"values": {"a": 1}, "source": "s", "updated": ""}),
                   lambda d: d.update(phase="spec-review", status="stopped", reason="", next=""),
                   lambda d: d.update(phase="spec-review", status="running", stage="round9"),
                   lambda d: d.update(phase="spec-review", status="running", cycle=0),
                   lambda d: d.update(phase="spec-review", status="done")):
        d = json.loads(json.dumps(good))
        change(d)
        ledger.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        hand.append((rc(["status", "3"]), rc(["progress", "3"])))
    o["手で直した台帳"] = hand
    ledger.write_text("{壊れた", encoding="utf-8")
    o["壊れた JSON"] = (rc(["status", "3"]), rc(["progress", "3"]), rc(["set", "3", "stage=round1"]))
    o["無い台帳"] = (rc(["status", "9"]), rc(["progress", "9"]), rc(["set", "9", "stage=round1"]), rc(["lines", "9", "--source", "s"]))

    # 書けない: `.claude/plans` がファイル・書けないディレクトリ
    other = base / tag / "other"
    build_repo(other)
    (other / ".claude" / "plans").write_text("", encoding="utf-8")
    o["plans がファイル"] = rc(["init", "1"], other)
    (other / ".claude" / "plans").unlink()
    (other / ".claude" / "plans").mkdir()
    (other / ".claude" / "plans").chmod(0o500)
    try:
        o["plans に書けない"] = rc(["init", "1"], other)
    finally:
        (other / ".claude" / "plans").chmod(0o700)
    return o


def function_sources(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return {n.name: ast.get_source_segment(source, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in COPIED}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test-autopilot-ledger-")).resolve()  # macOS の /var は /private/var——git の返す形にそろえる
    saved_env = dict(os.environ)
    try:
        isolate_env(tmp / "home")
        mod = load()
        print("正しい本体")
        o = scenario(mod, tmp, "correct")
        check("場所: メインの作業ツリー・worktree・サブディレクトリで同じ台帳", o["場所"] == [True, True, True])
        check("版: 先頭の 0・0・符号・区切り・空白・文字・全角の数字は 2", o["版"] == [2] * 14)
        check("init は 0、2 度目は 3 で台帳を変えない", o["init"] == 0 and o["init 2 度目"] == (3, True))
        check("初期の progress", o["progress 初期"] == "phase=spec-review cycle=1 stage=planner commit=-\n")
        check("初期の status は running で 0", o["status 初期"][0] == 0 and o["status 初期"][1].startswith("running:"))
        check("一覧に無い鍵（version・updated・format を含む）は 3 で台帳を変えない", o["鍵"] == [(3, True)] * 4)
        check("鍵=値 の形でなければ 2 で台帳を変えない", o["鍵の形"] == (2, True))
        check("一覧に無い phase・stage・status は 3", o["値"] == [(3, True)] * 3)
        check("cycle の 0・文字・先頭 0・負は 3", o["cycle"] == [(3, True)] * 4)
        check("commit の短い・大文字・41 桁・16 進でない値は 3", o["commit"] == [(3, True)] * 4)
        check("triage・held の絶対パス・..・~ は 3", o["指す先"] == [(3, True)] * 4)
        check("phase が done でない status=done・status が running の phase=done は 3", o["done の整合"] == [(3, True)] * 2)
        check("理由か頼むことの無い stopped（空白だけを含む）は 3", o["stopped の理由"] == [(3, True)] * 4)
        check("running で理由を書くのは 3", o["running の古い理由"] == (3, True))
        check("progress は理由・時刻・状態・指す先・線・同じ値の書き直しでは変わらない（台帳のファイルは変わった——陽性対照）",
              o["progress は変わらない"] == [(0, True, True)] * 6)
        check("progress は段・周・コミット・phase が変われば変わる", o["progress は変わる"] == [(0, True)] * 4)
        check("progress の行", o["progress の行"] == "phase=feasibility cycle=2 stage=- commit=abcdef1\n")
        check("線の出所が空・空白だけなら 3", o["線"] == [(3, True)] * 2)
        check("線の項目か値が空なら 3", o["線の空"] == [(3, True)] * 3)
        check("線の同じ項目を 2 度なら 3", o["線の 2 度"] == (3, True))
        check("線は置き換え（前の項目が消える）", o["線は置き換え"] == {"c": "d"})
        check("stopped は phase が spec-review のままでも 3、理由と頼むことを出す",
              o["status stopped"][0] == 3 and "マージが拒まれた" in o["status stopped"][1] and "マージを人に残す" in o["status stopped"][1])
        check("status・progress・show・path は台帳を書き換えない", o["読むだけ"] == [3, 0, 0, 0, True])
        check("stopped の台帳を running に戻せる", o["stopped にも書ける"] == 0 and o["status running"] == 0)
        check("done は 5", o["status done"] == (0, 5) and o["show"] == 0)
        check("書いた台帳の欄は docstring の形", o["書いた台帳の欄"] == sorted(
            ["format", "version", "phase", "cycle", "stage", "commit", "status", "reason", "next", "triage", "held", "updated", "lines"]))
        check("固定の正しい台帳は読める（陽性対照）", o["固定の正しい台帳"] == 5)
        check("手で直した台帳（形の違い 7・崩れ 4）は status も progress も 4", o["手で直した台帳"] == [(4, 4)] * 11)
        check("壊れた JSON は 4（running と読まない）", o["壊れた JSON"] == (4, 4, 4))
        check("無い台帳は 4", o["無い台帳"] == (4, 4, 4, 4))
        check("`.claude/plans` がファイルなら 4", o["plans がファイル"] == 4)
        check("`.claude/plans` に書けなければ 4（root で回すと書けてしまうので見られない）",
              o["plans に書けない"] == 4 or os.geteuid() == 0)

        print("\nmain_worktree・_git・exists は dev-loop の ledger.py の写しと同じ")
        mine, theirs = function_sources(SCRIPT), function_sources(ORIGINAL)
        for name in COPIED:
            check(f"{name} が両方に在って同じ", name in mine and mine.get(name) == theirs.get(name))
        altered = dict(mine, main_worktree=mine["main_worktree"].replace("--show-toplevel", "--show-cdup"))
        check("陽性対照: 1 か所変えた写しは「違う」と出る", altered["main_worktree"] != theirs["main_worktree"])

        print("\n終了コードが docstring の表と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        table = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", table, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_USAGE, mod.EXIT_REJECTED, mod.EXIT_UNKNOWN, mod.EXIT_STOPPED, mod.EXIT_DONE}
        check(f"表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)
        check("status の 3 つの値の終了コード", mod.STATUS_CODES == {"running": 0, "stopped": 3, "done": 5})

        print("\n変異テスト（壊したのに観測がそろったままなら失格）")
        for i, (name, pairs) in enumerate(MUTATIONS.items()):
            mutated = source
            missing = [n for n, _ in pairs if n not in mutated]
            if missing:
                check(f"変異を当てる先がある: {name}: {missing}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d = tmp / f"mut-{i}"
            d.mkdir()
            broken = d / "autopilot-ledger.py"
            broken.write_text(mutated, encoding="utf-8")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**
            try:
                mutant = load(broken)
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, d, "s")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", got != o)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)
    finally:
        os.environ.clear()
        os.environ.update(saved_env)
        for p in tmp.rglob("plans"):
            with contextlib.suppress(OSError):
                p.chmod(0o700)
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("autopilot の台帳のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
