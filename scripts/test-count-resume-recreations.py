#!/usr/bin/env python3
"""`count-resume-recreations.py` の回帰テスト。

    python3 scripts/test-count-resume-recreations.py

**このテストは実環境を触らない。** 毎回テンポラリに偽の `projects` ツリーを作り、
そこだけを対象にする（`assert_not_real_home` がそれを担保する）。本体は実ホームの
`~/.claude/projects` を既定にするので、**歯止めが無いと、テストが利用者の
トランスクリプトを読んで通ってしまう**。

**陽性対照は合成である。** #96 の実物（別リポジトリの Issue 10902。1 本目の worktree のあと、
後のセッションが `EnterWorktree` の `name` で 2 本目を作った）と**同じ形**を作って当てる。
**実物そのものは CI に持ち込めない**（リポジトリの外で、公開できない）。

**変異テストを含む。** 本体の docstring の「守る」の行数だけ変異を当て、
**壊したのに観測が変わらなければ失格**とする。行を足したら変異も足す。
"""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "count-resume-recreations.py"
REAL_HOME_PROJECTS = Path(os.path.expanduser("~")) / ".claude" / "projects"
REPO = "/work/app"
WT = REPO + "/.claude/worktrees/"
CACHE = "/home/u/.claude/plugins/cache/x/dev-loop/{v}/skills/dev-loop"

failures: list[str] = []


def load(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location(f"crr_{id(script)}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_home(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_HOME_PROJECTS.resolve(), "テストが実ホームの projects を対象にしている"
    assert not str(resolved).startswith(str(REAL_HOME_PROJECTS.resolve()) + os.sep), (
        "テストの対象が実ホームの projects の内側にある"
    )
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "テストの対象がテンポラリの外にある"


def check(name: str, cond: bool) -> None:
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        failures.append(name)


class Session:
    """1 ファイル分のレコードを組み立てる。uuid は渡さなければ連番。"""

    def __init__(self, sid: str, ts: str, cwd: str = REPO):
        self.sid, self.ts, self.cwd, self.rows, self.n = sid, ts, cwd, [], 0

    def _rec(self, role, content, uuid=None, cwd=None):
        self.n += 1
        ts = f"{self.ts}:{self.n:02d}Z"
        self.rows.append({"type": role, "uuid": uuid or f"{self.sid}-{self.n}", "timestamp": ts,
                          "cwd": cwd or self.cwd, "message": {"role": role, "content": content}})
        return self

    def slash(self, args, uuid=None):
        return self._rec("user", [{"type": "text", "text":
                         f"<command-name>/dev-loop:dev-loop</command-name><command-args>{args}</command-args>"}], uuid)

    def skill_tool(self, args):
        return self._rec("assistant", [{"type": "tool_use", "id": f"{self.sid}-sk{self.n}", "name": "Skill",
                                        "input": {"skill": "dev-loop:dev-loop", "args": args}}])

    def body(self, banner=None, cache=None, find_cycle=True):
        text = (f"Base directory for this skill: {CACHE.format(v=cache)}\n" if cache else
                "Base directory for this skill: /home/u/.claude/skills/dev-loop\n")
        if banner:
            text += f"<!-- skill-version: {banner} -->\n"
        if find_cycle:
            text += "python3 scripts/find-cycle.py <n>\n"
        return self._rec("user", [{"type": "text", "text": text}])

    def tool(self, name, inp, out, cwd=None):
        tid = f"{self.sid}-t{self.n}"
        self._rec("assistant", [{"type": "tool_use", "id": tid, "name": name, "input": inp}], cwd=cwd)
        return self._rec("user", [{"type": "tool_result", "tool_use_id": tid, "content": out}], cwd=cwd)

    def write(self, root: Path, project="-work-app", extra_lines=()):
        d = root / project
        d.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(r, ensure_ascii=False) for r in self.rows] + list(extra_lines)
        (d / f"{self.sid}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self


CREATED = "Created worktree at /work/app/.claude/worktrees/x on branch worktree-x. The session is now working"
ENTERED = "Entered worktree at /work/app/.claude/worktrees/x on branch issue/7-x. The session is now working"
PREPARING = "Preparing worktree (new branch 'issue/7-x')\nHEAD is now at abc"
FIND_HIT = "[1] 計画ファイル\n      docs/plans/issue-7.md\n\n**当たったものがある。** どれで再開するか"
FIND_MISS = "[1] 計画ファイル\n      当たらなかった\n\n**5 本とも当たらなかった。新規の周として始めてよい。**"


def build_tree(root: Path) -> None:
    # 周 7: 1 区間目で worktree を作り、2 区間目（別セッション）で EnterWorktree の name で
    # **2 本目を作る**——#96 の実物（10902）と同じ形。3 区間目は既存に入るだけ。
    s1 = (Session("s1", "2026-09-16T23:00").slash("7").body(banner="1.14.0", find_cycle=False)
          .tool("Bash", {"command": "git worktree add .claude/worktrees/issue-7 -b issue/7-x"}, PREPARING))
    s1.write(root)
    s2 = (Session("s2", "2026-09-17T01:00").slash("https://github.com/org-2/app/issues/7")
          .body(banner="1.14.0", find_cycle=False)
          .tool("EnterWorktree", {"name": "issue-7-again"}, CREATED))
    s2.write(root)
    (Session("s3", "2026-09-17T03:00").slash("7").body(cache="1.35.0")
     .tool("Bash", {"command": "python3 /p/find-cycle.py 7"}, FIND_HIT)
     .tool("EnterWorktree", {"path": WT + "issue-7"}, ENTERED)
     .tool("EnterWorktree", {"name": "issue-7"}, "Resumed worktree at /work/app/.claude/worktrees/issue-7 on branch b")
     # 失敗した作成と、テストの出力に出た Preparing は作成ではない
     .tool("Bash", {"command": "git worktree add .claude/worktrees/issue-7 -b issue/7-x"},
           "fatal: a branch named 'issue/7-x' already exists")
     .tool("Bash", {"command": "python3 scripts/test-worktree-scripts.py"}, PREPARING)
     .write(root))
    # **履歴のコピー**（fork / --resume）: s1 の起動レコードを同じ uuid で別ファイルに写す。
    copy = Session("s1copy", "2026-09-16T23:00")
    copy.rows = [dict(s1.rows[0])]
    copy.write(root, project="-work-app--claude-worktrees-issue-7")
    # 周 8: Skill の tool_use で起動、版はバナーもパスも無い。新規で switch -c。
    # 同じセッションで続けて周 9 を起動し、そちらは作らない（**直前の起動に帰属**）。
    (Session("s4", "2026-09-18T00:00", cwd=WT + "issue-8").skill_tool("8")
     .tool("Bash", {"command": "git switch -c issue/8-y"}, "Switched to a new branch 'issue/8-y'")
     .slash("9").body(banner="1.35.0")
     .tool("Bash", {"command": "grep -n 当たった plugins/dev-loop/skills/dev-loop/scripts/find-cycle.py"},
           "209:        print(\"**当たったものがある。** どれで再開するか\")\n**当たったものがある。**")
     .tool("Bash", {"command": "cat plugins/dev-loop/skills/dev-loop/scripts/find-cycle.py"},
           "print(\"**当たったものがある。**\")")
     .write(root, extra_lines=["{broken"]))
    # 周 10: 1 区間目だが find-cycle が当てた（部分一致の誤ヒットでありうる）。作る。
    (Session("s5", "2026-09-19T00:00").slash("10").body(banner="1.35.0")
     .tool("Bash", {"command": "python3 /p/find-cycle.py 10"}, FIND_HIT)
     .tool("Bash", {"command": "bash /p/prepare-worktree.sh 10 z"}, PREPARING)
     .write(root))
    # 周 11: 新規、find-cycle は当てない。作らない。
    (Session("s6", "2026-09-19T01:00").slash("11").body(banner="1.35.0")
     .tool("Bash", {"command": "python3 /p/find-cycle.py 11"}, FIND_MISS).write(root))
    # 周 12・13: 同じセッションで 2 つ起動し、**作成は後の起動の後**。
    # 上の s4 は作成が先なので、「最初の起動に帰属させる」変異はそこでは区別できない。
    (Session("s7", "2026-09-19T02:00").slash("12").body(banner="1.35.0").slash("13").body(banner="1.35.0")
     .tool("Bash", {"command": "git worktree add ../w -b issue/13-q"}, PREPARING).write(root))
    # 番号なし: 引数なしの起動（入り直した再開でありうる）。作らない。**新規の分母に入れない。**
    # find-cycle が当てて作っても、番号なしは発生の一覧にも find-cycle の列にも出さない。
    (Session("s8", "2026-09-19T03:00").slash("").body(banner="1.35.0")
     .tool("Bash", {"command": "python3 /p/find-cycle.py 5"}, FIND_HIT)
     .tool("EnterWorktree", {"name": "issue-5"}, CREATED).write(root))


def build_blind(root: Path) -> None:
    """新規の区間はあるが、作成の信号が 1 つも無い（形式が変わった・検出器が壊れた）。"""
    (Session("b1", "2026-09-20T00:00").slash("20").body(banner="1.35.0")
     .tool("EnterWorktree", {"name": "w"}, "Something else entirely").write(root))


def observe(mod, root: Path, blind: Path) -> dict:
    assert_not_real_home(root)
    assert_not_real_home(blind)
    segments, stats = mod.collect(root)
    out = {
        "segments": sorted((s["session"], s["issue"], s["resume"], tuple(sorted(s["signals"])),
                            s["created_before"], s["version"]) for s in segments),
        "dups": stats["duplicate_invocations"], "broken": stats["broken"],
    }
    for name, path, anon in (("plain", root, False), ("anon", root, True), ("blind", blind, False)):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            status = mod.main(["--root", str(path)] + (["--anonymize"] if anon else []))
        out[name] = (status, buf.getvalue())
    return out


MUTATIONS = {
    "履歴のコピーを畳まない": ('if inv["id"] in invocations:', "if False:"),
    "失敗した作成も数える（出力を見ない）": ("and PREPARING.search(out)", ""),
    "既存に入った EnterWorktree も数える": ('out.startswith("Created worktree at")', "True"),
    "Skill の tool_use を起動と読まない": ('if name == "Skill" and', "if False and"),
    "キャッシュのパスの版を見ない": ("BANNER.search(text) or CACHE_VERSION.search(text)", "BANNER.search(text)"),
    "find-cycle を走らせたかをコマンドの文字列だけで見る":
        ("FIND_CYCLE_RUN.search(command)", '"find-cycle.py" in command'),
    "find-cycle が当てただけの区間を母数に混ぜる":
        ('"2+" if inv["ordinal"]', '"2+" if inv["ordinal"] or inv["find_cycle"] == "hit"'),
    "作成をファイルの最初の起動に帰属させる":
        ('"invocation": current["id"]', '"invocation": invocations[0]["id"]'),
    "検出できていないのに 0 で終わる": ("status = 3", "status = 0"),
    "番号なしの区間を新規に混ぜる": ('row["no_issue"] += 1', 'row["new"] += 1'),
}


def main() -> int:
    mod = load()
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        root, blind = tmpdir / "projects", tmpdir / "blind"
        build_tree(root)
        build_blind(blind)
        correct = observe(mod, root, blind)
        seg = {(s[0], s[1]): s for s in correct["segments"]}

        print("区間と再開の判定")
        check("区間は 10（コピーした起動は畳む）", len(correct["segments"]) == 10 and correct["dups"] == 1)
        check("1 区間目は新規・作成あり", seg[("s1", "7")][2:4] == (None, ("worktree add",)))
        check("陽性対照: 2 区間目の EnterWorktree name は発生で、既に作成済み（#96 の実物と同じ形）",
              seg[("s2", "7")][2:5] == ("2+", ("EnterWorktree",), True))
        check("URL の引数は issues/ の後の番号（org-2 の 2 ではない）", ("s2", "7") in seg)
        check("既存に入っただけ・失敗した add・テストの出力は作成ではない", seg[("s3", "7")][2:4] == ("2+", ()))
        check("Skill の tool_use も起動で、switch -c は新ブランチ", seg[("s4", "8")][2:4] == (None, ("new branch",)))
        check("作成は直前の起動に帰属（周 9 には付かない）", seg[("s4", "9")][3] == ())
        check("作成は直前の起動に帰属（後の起動の後なら後の周）",
              (seg[("s7", "12")][3], seg[("s7", "13")][3]) == ((), ("worktree add",)))
        check("find-cycle のソースを読んだだけでは再開にならない", seg[("s4", "9")][2] is None)
        check("1 区間目で find-cycle が当てたものは別の種別", seg[("s5", "10")][2] == "find-cycle")
        check("find-cycle が当てなければ新規", seg[("s6", "11")][2] is None)
        check("版: バナー／キャッシュのパス／どちらも無い", (seg[("s1", "7")][5], seg[("s3", "7")][5],
              seg[("s4", "8")][5]) == ("1.14.0", "1.35.0", None))
        check("壊れた行は数えて続ける", correct["broken"] == 1)

        print("\n出力")
        status, text = correct["plain"]
        check("信号が拾えていれば 0 で終わる", status == 0)
        check("母数と発生と作成済みを出す", "（母数）: 2・発生: 1（うち前の区間で既に作っていた周: 1）" in text)
        check("find-cycle が当てただけの区間は別の行", "find-cycle が当てただけの区間: 1・発生: 1" in text)
        check("新規の区間の作成率を出す", "新規の区間の作成: 3 / 6" in text)
        check("番号なしの区間は別に出し、新規の分母に入れない", "番号なしの区間: 1" in text)
        check("番号なしは find-cycle が当てても発生の一覧に出ない", "#None" not in text)
        with tempfile.TemporaryDirectory() as only_tmp:
            only = Path(only_tmp) / "projects"
            Session("n1", "2026-09-21T00:00").slash("").body(banner="1.35.0").write(only)
            assert_not_real_home(only)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                ostatus = mod.main(["--root", str(only)])
        check("新規の区間が 0 なら対照が取れないので終了コード 3", ostatus == 3)
        check("版の不明を黙って落とさない", "| 不明 / 本文なし |" in text)
        astatus, atext = correct["anon"]
        check("--anonymize はリポジトリ名と番号を伏せる",
              astatus == 0 and "| R1 |" in atext and "app" not in atext and "#7" not in atext and "s2" not in atext)
        bstatus, btext = correct["blind"]
        check("新規の区間があるのに作成が 0 なら終了コード 3", bstatus == 3 and "検出できていない" in btext)

        print("\n変異テスト（壊したのに観測が変わらなければ失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for name, (needle, replacement) in MUTATIONS.items():
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所: {name}", False)
                continue
            broken = tmpdir / f"mut-{abs(hash(name))}" / SCRIPT.name
            broken.parent.mkdir()
            broken.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            check(f"変異を殺せる: {name}", observe(load(broken), root, blind) != correct)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

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
    print("再開の周の作り直しの計数のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
