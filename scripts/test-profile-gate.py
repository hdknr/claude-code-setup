#!/usr/bin/env python3
"""spec-loop の `profile-gate.py`（外部の profile の関門。#1457）と、それを当てる `scaffold.py`・`build-proposal.py` の口の回帰テスト。

    python3 scripts/test-profile-gate.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。一時ディレクトリに `plugins/spec-loop/`（本物の `.claude-plugin/` と `scripts/` の写し）を置き、
試料に応じて隣に `plugins/platform-spec/`（本物の写しか、終了コードと受けた引数を記録する偽物）を置く・置かない・名指す。
本物の platform-spec の試料（profile の clone と正本）は `scripts/test-check-profile-diff.py` を読み込む。scaffold の正本の試料は `scripts/test-scaffold-screens.py`、
提案書の正本の試料は `scripts/test-build-proposal.py` を読み込む（写さない）。

見るもの:

1. **#1457 の受入基準 2**——差分が残っていると関門が止まり（1）、無ければ通る（0。本物の platform-spec）。**profile を使わない案件では何も出さずに 0 で、platform-spec を呼ばない**
   （**陽性対照: 同じ置き方で `profile の行` に値があれば呼ぶ**）。
2. **#1457 の受入基準 3**——`profile の行` に値があるのに platform-spec が見つからなければ 4。名指しが platform-spec でなければ隣の本物があっても 4。
3. **読み替えと見つけ方**——偽の platform-spec の 0・1・2・4・7 が 0・1・2・4・2。出力に `platform-spec: ` を付けて写す。`--spec-loop`・`--upto`・`--project` を渡す。
   引数・環境変数・隣・`installed_plugins.json`（一時の `CLAUDE_CONFIG_DIR`）で見つかる。
4. **使っているかの読み方**——7 列の表・列はあるが値が無い・後の版で値を消した・`--upto` で値の無い前の版は呼ばない。先頭が空の行の表は読む。読めない表は 2。重ね合わせの違反は 1。
5. **scaffold.py と build-proposal.py の口**——関門が 1 なら 1、4 なら 2 で何も書かない（scaffold の本文・提案書が無い）。0 なら作る。scaffold の `--check` は呼ばない。
   profile を使わない正本では呼ばない。
6. **ファイルを書かない**——正本と、プラグインの写し（`__pycache__` を含む）。
7. **変異テスト**——`profile-gate.py` を 1 箇所ずつ壊し、名指しした試料が期待どおりでなくなること（壊さない写しで期待どおりになる陰性対照つき）。
   **変異の数は docstring の「守ること」の行の数と同じ**。`scaffold.py`・`build-proposal.py` の口も壊して、口の試料が期待どおりでなくなることを見る。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、`HOME`・`CLAUDE_CONFIG_DIR`・`GIT_CONFIG_GLOBAL` を一時ディレクトリにし、
`SPEC_LOOP_PLATFORM_SPEC`・`SPEC_PROFILE_CLONE`・`PLATFORM_SPEC_SPEC_LOOP`・`PYTHONDONTWRITEBYTECODE`・`GIT_*` を子に渡さない（試料が名指すときだけ一時ディレクトリの値を渡す）。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
PLATFORM = REAL_REPO / "plugins" / "platform-spec"
GATE = "profile-gate.py"
SOURCE = SPEC_LOOP / "scripts" / GATE

sys.dont_write_bytecode = True


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diff_test = load(REAL_REPO / "scripts" / "test-check-profile-diff.py", "test_check_profile_diff")
tip = diff_test.tip
assert_in_tmp = tip.assert_in_tmp

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


I = diff_test.I
I_HEAD, I7_HEAD = tip.I_HEAD, tip.I7_HEAD
infra = diff_test.infra
USED = {I: infra("LANG-1", "")}
UNUSED = {I: I7_HEAD + "言語,x,y,z,,Q-F-001,決定\n"}
EMPTY = {I: infra("", "")}

# ---- 置き方


def env_for(tmp: Path) -> dict[str, str]:
    env = tip.child_env(tmp)
    for key in ("SPEC_LOOP_PLATFORM_SPEC", "PYTHONDONTWRITEBYTECODE"):
        env.pop(key, None)
    return env


def copy_spec_loop(dest: Path, source: str | None = None, target: str = GATE) -> Path:
    assert_in_tmp(dest)
    dest.mkdir(parents=True)
    shutil.copytree(SPEC_LOOP / ".claude-plugin", dest / ".claude-plugin")
    shutil.copytree(SPEC_LOOP / "scripts", dest / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    if source is not None:
        (dest / "scripts" / target).write_text(source, encoding="utf-8")
    return dest


FAKE = """import json, os, sys
from pathlib import Path
here = Path(__file__).resolve().parent
(here / "called.json").write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
print("偽の版の差分")
sys.exit(int((here / "code.txt").read_text()))
"""


def fake_platform(dest: Path, code: int, name: str = "platform-spec") -> Path:
    assert_in_tmp(dest)
    (dest / ".claude-plugin").mkdir(parents=True)
    (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": name, "version": "0.2.0"}), encoding="utf-8")
    (dest / "scripts").mkdir()
    (dest / "scripts" / "check-profile-diff.py").write_text(FAKE, encoding="utf-8")
    (dest / "scripts" / "code.txt").write_text(str(code), encoding="utf-8")
    return dest


def called(fake: Path) -> list[str] | None:
    record = fake / "scripts" / "called.json"
    return json.loads(record.read_text(encoding="utf-8")) if record.is_file() else None


def write_files(root: Path, files: dict) -> None:
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            path.write_bytes(body)
        else:
            path.write_text(body, encoding="utf-8")


def caches(root: Path) -> list[str]:
    return [str(p) for p in root.rglob("__pycache__")]


# ---- 関門の試料
# (名前, 正本のファイル, 置き方, 偽物の終了コード, 引数, 期待する終了コード, 含むべき文字列, 出力が空か, 偽物が呼ばれるか（None は見ない）)
# 置き方: none（platform-spec を置かない）・sibling（隣に偽物）・env（隣に置かず環境変数で偽物）・named（引数で偽物）・
#        badnamed（隣に偽物、引数で platform-spec でないもの）・badenv（環境変数で platform-spec でないもの）・cache（installed_plugins.json）
CASES: list[tuple] = [
    ("使っていない", UNUSED, "badenv", 0, [], 0, "", True, None),
    ("値が無い列", EMPTY, "sibling", 0, [], 0, "", True, False),
    ("陽性対照: 値があれば呼ぶ", USED, "sibling", 0, [], 0, "platform-spec: 偽の版の差分", False, True),
    ("偽物の 1", USED, "sibling", 1, [], 1, "profile の関門を通らない", False, True),
    ("偽物の 2", USED, "sibling", 2, [], 2, "判定していない", False, True),
    ("偽物の 4", USED, "sibling", 4, [], 4, "止めた", False, True),
    ("偽物の知らないコード", USED, "sibling", 7, [], 2, "終了コード: 7", False, True),
    ("platform-spec が無い", USED, "none", 0, [], 4, "platform-spec が見つからない", False, None),
    ("名指しが違う", USED, "badnamed", 0, ["--platform-spec", "{bad}"], 4, "platform-spec のプラグインの根でない", False, False),
    ("名指しの環境変数が違う", USED, "badenv", 0, [], 4, "SPEC_LOOP_PLATFORM_SPEC が指す", False, None),
    ("引数で名指す", USED, "named", 0, ["--platform-spec", "{fake}"], 0, "偽の版の差分", False, True),
    ("環境変数で名指す", USED, "env", 0, [], 0, "偽の版の差分", False, True),
    ("プラグインのキャッシュ", USED, "cache", 0, [], 0, "偽の版の差分", False, True),
    ("7 列の表", UNUSED, "sibling", 0, [], 0, "", True, False),
    ("後の版で値を消した", {**USED, "docs/v2/shared/infra.csv": infra("", "")}, "sibling", 0, [], 0, "", True, False),
    ("前の版には値が無い", {**EMPTY, "docs/v2/shared/infra.csv": infra("LANG-1")}, "sibling", 0, ["--upto", "1"], 0, "", True, False),
    ("引数を渡す", {**EMPTY, "docs/v2/shared/infra.csv": infra("LANG-1")}, "sibling", 0, ["--upto", "2", "--project", "{project}"], 0, "偽の版の差分",
     False, True),
    ("先頭が空の行", {I: "\n" + infra("LANG-1")}, "sibling", 1, [], 1, "偽の版の差分", False, True),
    ("読めない表", {I: infra("LANG-1").encode("cp932")}, "sibling", 0, [], 2, "読めない", False, False),
    ("値が無く重ね合わせの違反", {**UNUSED, "docs/v2/removed.csv": "種類,対象\nファイル,shared/x.csv\n"}, "sibling", 0, [], 0, "", True, False),
    ("値があって重ね合わせの違反", {**USED, "docs/v2/removed.csv": "種類,対象\nファイル,shared/x.csv\n"}, "sibling", 0, [], 1, "版の重ね合わせが決まりに反する",
     False, False),
]


def run_case(work: Path, case: tuple, env: dict[str, str], gate_source: str | None = None) -> dict:
    name, files, layout, code, args = case[:5]
    assert_in_tmp(work)
    if layout == "cache":
        config = work / "config"
        plugins = config / "plugins" / "cache" / "mkt"
        spec_loop = copy_spec_loop(plugins / "spec-loop" / "0.134.0", gate_source)
        fake = fake_platform(work / "elsewhere-fake", code)
        (config / "plugins").mkdir(parents=True, exist_ok=True)
        (config / "plugins" / "installed_plugins.json").write_text(json.dumps(
            {"version": 2, "plugins": {"platform-spec@mkt": [{"scope": "user", "installPath": str(fake)}]}}), encoding="utf-8")
        env = dict(env, CLAUDE_CONFIG_DIR=str(config))
    else:
        plugins = work / "plugins"
        spec_loop = copy_spec_loop(plugins / "spec-loop", gate_source)
        fake = fake_platform((plugins / "platform-spec") if layout in ("sibling", "badnamed") else (work / "fake"), code) \
            if layout in ("sibling", "badnamed", "named", "env") else work / "nofake"
        if layout == "env":
            env = dict(env, SPEC_LOOP_PLATFORM_SPEC=str(fake))
    bad = fake_platform(work / "bad", 0, name="not-platform-spec")
    if layout == "badenv":
        env = dict(env, SPEC_LOOP_PLATFORM_SPEC=str(bad))
    project = work / "project"
    write_files(project, files)
    (project / "docs").mkdir(parents=True, exist_ok=True)
    before = tip.tree_state(project)
    argv = [a.format(bad=str(bad), fake=str(fake), project=str(project)) for a in args]
    proc = subprocess.run([sys.executable, str(spec_loop / "scripts" / GATE), str(project / "docs"), *argv],
                          capture_output=True, text=True, cwd=work, env=env)
    return {"code": proc.returncode, "out": proc.stdout + proc.stderr, "called": called(fake), "project": project,
            "changed": tip.tree_state(project) != before, "caches": caches(spec_loop)}


def as_expected(case: tuple, r: dict) -> bool:
    name, _, _, _, _, code, text, empty, invoked = case
    if r["code"] != code or "Traceback" in r["out"] or r["changed"] or r["caches"]:
        return False
    if text and text not in r["out"]:
        return False
    if empty and r["out"].strip():
        return False
    if invoked is not None and (r["called"] is not None) != invoked:
        return False
    if name == "引数を渡す":
        got = r["called"] or []
        want = ["--spec-loop", "--upto", "2", "--project", str(r["project"])]
        if not all(w in got for w in want) or got[got.index("--upto") + 1] != "2":
            return False
    if name == "陽性対照: 値があれば呼ぶ" and "--spec-loop" not in (r["called"] or []):
        return False
    return True


# docstring の「守ること」の行と同じ順の変異。(名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("値が無くても重ねる", "        if not placed(docs, upto):\n            return EXIT_OK, []\n", "", "値が無く重ね合わせの違反"),
    ("重ねた全体に値が無くても呼ぶ", "    if not count:\n        return EXIT_OK, []", "    if False:\n        return EXIT_OK, []", "後の版で値を消した"),
    ("見出しに列が無い表を読み違える", "    if not rows or COLUMN not in rows[0]:\n        return 0", "    if not rows:\n        return 0", "7 列の表"),
    ("見出しの前の空の行を飛ばさない", "    while rows and not any(cell.strip() for cell in rows[0]):", "    while False:", "先頭が空の行"),
    ("見つからないのを通す", "        lines.append(f\"止めた: {e}\")\n        code = EXIT_STOPPED", "        lines.append(f\"止めた: {e}\")\n        code = EXIT_OK",
     "platform-spec が無い"),
    ("名指しが違っても使う", "            if not is_platform_spec(root):\n                raise NotFound(", "            if False:\n                raise NotFound(", "名指しが違う"),
    ("知らない終了コードを通す", "PLATFORM_SPEC_CODES.get(proc.returncode, EXIT_UNJUDGED)", "PLATFORM_SPEC_CODES.get(proc.returncode, EXIT_OK)", "偽物の知らないコード"),
    ("出力を写さない", "    lines = [f\"platform-spec: {line}\" for line in (proc.stdout + proc.stderr).splitlines()]", "    lines = []",
     "陽性対照: 値があれば呼ぶ"),
    ("--spec-loop を渡さない", "str(docs), \"--spec-loop\", str(PLUGIN_ROOT)]", "str(docs)]", "引数を渡す"),
    ("重ね合わせの違反を通す", "        if problems:\n            return EXIT_FAIL, problems", "        if False:\n            return EXIT_FAIL, problems", "値があって重ね合わせの違反"),
    ("__pycache__ を書く", "sys.dont_write_bytecode = True", "sys.dont_write_bytecode = False", "使っていない"),
]


# ---- 本物の platform-spec を通す

def real_cases(tmp: Path, env: dict[str, str]) -> None:
    clone = diff_test.make_profile(tmp / "profile", env)
    plugins = tmp / "real" / "plugins"
    spec_loop = copy_spec_loop(plugins / "spec-loop")
    shutil.copytree(PLATFORM, plugins / "platform-spec", ignore=shutil.ignore_patterns("__pycache__"))
    for label, extra, want, text in (("差分が残る", "", 1, "platform-spec: 起票の候補: shared/infra.csv:2: 言語 の profile の行 LANG-1: 変わった"),
                                     ("確かめたタグ", "確かめたタグ,v10\n", 0, "profile の関門を通る")):
        project = tmp / "real" / label
        files = {rel: body.replace("{clone}", str(clone)) for rel, body in diff_test.OK.items()}
        files[diff_test.S] = diff_test.settings(extra=extra)
        write_files(project, files)
        before = tip.tree_state(project)
        proc = subprocess.run([sys.executable, str(spec_loop / "scripts" / GATE), str(project / "docs")], capture_output=True, text=True,
                              cwd=tmp, env=env)
        out = proc.stdout + proc.stderr
        check(f"本物の platform-spec: {label}", proc.returncode == want and text in out, f"exit={proc.returncode} {out[-500:]}")
        check(f"本物の platform-spec: 正本が変わった: {label}", tip.tree_state(project) == before)
    found = caches(plugins)
    check("本物の platform-spec: 写しに __pycache__ ができた", not found, ", ".join(found))


# ---- scaffold.py と build-proposal.py の口

scaffold_test = load(REAL_REPO / "scripts" / "test-scaffold-screens.py", "test_scaffold_screens")
proposal_test = load(REAL_REPO / "scripts" / "test-build-proposal.py", "test_build_proposal")
S_INFRA = (I_HEAD + "言語,Python 3.12,r,c,,Q-R-001,決定,LANG-1\nDBMS,PostgreSQL,r,c,,Q-R-001,決定,\nホスティング環境,AWS,r,c,,Q-R-001,決定,\n")
S_INFRA7 = (I7_HEAD + "言語,Python 3.12,r,c,,Q-R-001,決定\nDBMS,PostgreSQL,r,c,,Q-R-001,決定\nホスティング環境,AWS,r,c,,Q-R-001,決定\n")


def scaffold_world(work: Path, infra_csv: str, code: int, scaffold_source: str | None = None):
    files = scaffold_test.no_screens()
    files["v1/shared/infra.csv"] = infra_csv
    world = scaffold_test.World(work, files)
    if scaffold_source is not None:
        (world.spec_loop / "scripts" / "scaffold.py").write_text(scaffold_source, encoding="utf-8")
    fake = fake_platform(world.plugins / "platform-spec", code)
    return world, fake


def scaffold_run(world, *args: str) -> tuple[int, str]:
    env = world.env()
    env.pop("SPEC_LOOP_PLATFORM_SPEC", None)
    proc = subprocess.run([sys.executable, str(world.spec_loop / "scripts" / "scaffold.py"), "--repo", str(world.repo), *args],
                          capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout + proc.stderr


def scaffold_cases(work: Path, scaffold_source: str | None = None) -> dict[str, str | None]:
    """口の試料ごとに、期待どおりでなければその理由（期待どおりなら None）。"""
    out: dict[str, str | None] = {}
    for label, infra_csv, code, args, want, bodies, invoked in (
            ("scaffold: 関門の 1 で作らない", S_INFRA, 1, (), 1, False, True),
            ("scaffold: 関門の 4 は 2 で作らない", S_INFRA, 4, (), 2, False, True),
            ("scaffold: --dry-run も関門の 1 で止まる", S_INFRA, 1, ("--dry-run",), 1, False, True),
            ("scaffold: 関門の 0 なら作る", S_INFRA, 0, (), 0, True, True),
            ("scaffold: 使わない正本では呼ばない", S_INFRA7, 1, (), 0, True, False)):
        world, fake = scaffold_world(work / label.replace(" ", "_").replace(":", ""), infra_csv, code, scaffold_source)
        got, text = scaffold_run(world, *args)
        problems = []
        if got != want:
            problems.append(f"終了コード {got}（期待 {want}）")
        if bool(world.bodies()) != bodies:
            problems.append(f"本文が {world.bodies()}")
        if (called(fake) is not None) != invoked:
            problems.append(f"偽物が{'呼ばれた' if called(fake) is not None else '呼ばれない'}")
        if want == 1 and "関門（外部の profile。profile-gate.py）を通らない" not in text:
            problems.append("関門の名前が出ない")
        out[label] = f"{'; '.join(problems)} {text[-400:]}" if problems else None
    # --check は呼ばない: 関門の 0 で作ってから偽物を 1 にして --check
    world, fake = scaffold_world(work / "scaffold-check", S_INFRA, 0, scaffold_source)
    scaffold_run(world)
    (fake / "scripts" / "called.json").unlink(missing_ok=True)
    (fake / "scripts" / "code.txt").write_text("1", encoding="utf-8")
    got, text = scaffold_run(world, "--check")
    out["scaffold: --check は呼ばない"] = None if got == 0 and called(fake) is None else f"終了コード {got}・呼ばれた {called(fake)} {text[-300:]}"
    return out


def proposal_root(work: Path, profile: bool, code: int, proposal_source: str | None = None):
    assert_in_tmp(work)
    plugins = work / "plugins"
    spec_loop = copy_spec_loop(plugins / "spec-loop", proposal_source, "build-proposal.py")
    fake = fake_platform(plugins / "platform-spec", code)
    infra_csv = (proposal_test.INFRA_OK.replace(proposal_test.INFRA_HEAD, I_HEAD).replace(",決定\n", ",決定,LANG-1\n", 1).replace(",決定\n", ",決定,\n")
                 if profile else proposal_test.INFRA_OK)
    steps = proposal_test.BASE[:-1] + [("w", proposal_test.INFRA, infra_csv), ("c",), ("t", proposal_test.R1), ("t", proposal_test.B1)]
    home = work / "home"
    home.mkdir()
    env = proposal_test.sandbox_env(home)
    for key in ("SPEC_LOOP_PLATFORM_SPEC", "CLAUDE_CONFIG_DIR", "PYTHONDONTWRITEBYTECODE"):
        env.pop(key, None)
    root = work / "repo"
    proposal_test._build_repo(root, steps, env)
    return spec_loop, fake, root, env


def proposal_cases(work: Path, proposal_source: str | None = None) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for label, profile, code, want, invoked in (("proposal: 関門の 1 で書かない", True, 1, 1, True),
                                                ("proposal: 関門の 4 は 2 で書かない", True, 4, 2, True),
                                                ("proposal: 関門の 0 なら書く", True, 0, 0, True),
                                                ("proposal: 使わない正本では呼ばない", False, 1, 0, False)):
        spec_loop, fake, root, env = proposal_root(work / label.replace(" ", "_").replace(":", ""), profile, code, proposal_source)
        target = root / "build" / "proposal" / "proposal.md"
        got, text = proposal_test.generate(spec_loop / "scripts", root, target, env)
        problems = []
        if got != want:
            problems.append(f"終了コード {got}（期待 {want}）")
        if target.is_file() != (want == 0):
            problems.append(f"提案書が{'在る' if target.is_file() else '無い'}")
        got_args = called(fake)
        if (got_args is not None) != invoked:
            problems.append(f"偽物が{'呼ばれた' if got_args is not None else '呼ばれない'}")
        if got_args is not None and not ("--project" in got_args and Path(got_args[got_args.index("--project") + 1]).resolve() == root.resolve()
                                         and "--upto" in got_args):
            problems.append(f"--project に正本の根・--upto を渡していない: {got_args}")
        if want == 1 and "関門（外部の profile。profile-gate.py）を通らない" not in text:
            problems.append("関門の名前が出ない")
        out[label] = f"{'; '.join(problems)} {text[-400:]}" if problems else None
    return out


WIRING_MUTATIONS = [  # (ファイル, 壊す前, 壊した後, 殺すはずの試料の名前)
    ("scaffold.py", "        code, lines = profiles.check(repo / DOCS, None, None, repo)\n", "        code, lines = 0, []\n", "scaffold: 関門の 1 で作らない"),
    ("scaffold.py", "fail(repo, writing, 1 if code == profiles.EXIT_FAIL else 2,", "fail(repo, writing, 1,", "scaffold: 関門の 4 は 2 で作らない"),
    ("build-proposal.py", "    profile_gate(gate, info[\"req\"])\n", "", "proposal: 関門の 1 で書かない"),
    ("build-proposal.py", "raise Stop(1 if code == profiles.EXIT_FAIL else 2,", "raise Stop(1,", "proposal: 関門の 4 は 2 で書かない"),
    ("build-proposal.py", "profiles.check(Path(tmp) / signoff.DOCS, version, None, top)", "profiles.check(Path(tmp) / signoff.DOCS, version, None, None)",
     "proposal: 関門の 0 なら書く"),
]


def main() -> int:
    names = [case[0] for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    source = SOURCE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="profile-gate-test-") as tmp_name:
        tmp = Path(tmp_name)
        env = env_for(tmp)
        for index, case in enumerate(CASES):
            r = run_case(tmp / f"case{index}", case, env)
            check(f"試料が期待どおりでない: {case[0]}", as_expected(case, r), f"exit={r['code']} called={r['called']} {r['out'][-500:]}")

        real_cases(tmp, env)

        for label, problem in {**scaffold_cases(tmp / "scaffold"), **proposal_cases(tmp / "proposal")}.items():
            check(f"口の試料が期待どおりでない: {label}", problem is None, problem or "")

        # 変異
        guarded = tip.guarded_lines(source)
        check("変異の数が「守ること」の行の数と違う", len(guarded) == len(MUTATIONS), f"守ること {len(guarded)} 行・変異 {len(MUTATIONS)} 件")
        killers = {killer for _, _, _, killer in MUTATIONS}
        check("変異の殺す試料が試料に無い", killers <= set(names), ", ".join(sorted(killers - set(names))))
        for index, killer in enumerate(sorted(killers)):
            case = next(c for c in CASES if c[0] == killer)
            r = run_case(tmp / f"control{index}", case, env, source)
            check(f"壊さない写しで殺す試料が期待どおりでない: {killer}", as_expected(case, r), r["out"][-300:])
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            case = next(c for c in CASES if c[0] == killer)
            r = run_case(tmp / f"mut{index}", case, env, source.replace(before, after))
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(case, r), r["out"][-300:])
        for index, (target, before, after, killer) in enumerate(WIRING_MUTATIONS):
            text = (SPEC_LOOP / "scripts" / target).read_text(encoding="utf-8")
            if text.count(before) != 1:
                check(f"口の変異が届いていない: {target}: {before.strip()}", False, f"{text.count(before)} 回")
                continue
            mutated = text.replace(before, after)
            place = tmp / f"wire{index}"
            results = scaffold_cases(place, mutated) if target == "scaffold.py" else proposal_cases(place, mutated)
            check(f"口の変異が生き残った: {target}: {before.strip()}（{killer} で殺せるはず）", results[killer] is not None)

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 関門の試料 {len(CASES)} 件・本物の platform-spec 2 件・口の試料 10 件・変異 {len(MUTATIONS)} 件（守ること {len(guarded)} 行）・口の変異 {len(WIRING_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
