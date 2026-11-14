#!/usr/bin/env python3
"""`check-spec-writeback.py`（仕様にある振る舞いを変える周が、申告と正本への戻しを残しているかを見る。#1001）の回帰テスト。

    python3 scripts/test-check-spec-writeback.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）——`test-check-deps-declared.py` と同じ形で、
**`dev-loop` はどのリポジトリでも使えるスキル**なので。

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリを作り、そこだけを対象にする（`assert_not_real_repo`）。

**変異テストを含む。** 本体の docstring の「守る」の各行に変異を 1 つ以上当て、**壊したのに契約が保たれるなら失格**とする。
**変異の前に、元の本体で全部緑であること（陽性対照）を見る。** 変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。

**申告漏れの陽性対照**（Issue の受入基準 3）: spec-loop の本物の `scaffold.py` で `scaffold/` を作り、実装の見本と本物の `green-list.py record` で
緑のケースの一覧を書いた試料で、計画の申告を `変えない` のまま実装の値を変えると `green-list.py check` が 1、壊れたケースを一覧から手で外すと
`check` は 0 に戻るが `check-spec-writeback.py` が 1、を見る（変える前は両方 0）。spec-loop のスクリプトは一時ディレクトリに写し、`python3 -I` で、
子のプロセスの環境から `PYTHONPATH` を外して走らせる（`test-green-list.py` と同じ理由）。

あわせて、**申告の値が原本（`references/spec-writeback.md` の「申告」の表）と本体の `VALUES` で同じこと**と、
**Q&A 表の列・回答・状態の写しが spec-loop の `check-qa-csv.py` と同じこと**を見る（dev-loop から spec-loop を相対パスで指せないので写している）。
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop"
SCRIPT = SKILL_DIR / "scripts" / "check-spec-writeback.py"
DOC = SKILL_DIR / "references" / "spec-writeback.md"
SPEC_LOOP_SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
CHILD_ENV = {k: v for k, v in os.environ.items() if k != "PYTHONPATH" and not k.startswith("GIT_")}

failures: list[str] = []

HEADER = "No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響\n"
OLD_ROW = "Q-R-001,要求確定,割引は？,A: なし / B: あり,A,理由,A,決定表 4 行目,反映済み,\n"
NEW_ROW = "Q-D-001,開発（#7）,締め日が休日なら前の営業日にした。仕様もそう直すか,A: 仕様を直す / B: 戻す,A,Issue が求めた,未回答,—,確認中,\n"
PLAN_ROW = ",開発（#7）,締め日が休日なら前の営業日にした。仕様もそう直すか,A: 仕様を直す / B: 戻す,A,Issue が求めた,未回答,—,確認中,"
CANON = {"docs/v1/shared/qa.csv": HEADER + OLD_ROW}
GREEN = "# 一覧\na.T.test_1 " + "0" * 64 + "\na.T.test_2 " + "1" * 64 + "\n"

PLAN = """# 計画

## 変更範囲

触る:

- `src/`
"""


def check(name: str, cond: bool) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


def assert_not_real_repo(root: Path) -> None:
    r = root.resolve()
    assert r != REAL_REPO and not str(r).startswith(str(REAL_REPO) + os.sep), "テストが実リポジトリを対象にしている"
    assert r.is_relative_to(Path(tempfile.gettempdir()).resolve()), "テストの対象がテンポラリの外にある"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-C", str(root), *args],
                          check=True, capture_output=True, text=True, env=CHILD_ENV).stdout


def repo(root: Path, *, plan: str | None = PLAN, branch: str = "issue/7-demo",
         base_files: dict[str, str] | None = None) -> str:
    """偽のリポジトリを作り、base の SHA を返す。計画ファイルは base の後のコミットに置く（周の形）。"""
    assert_not_real_repo(root)
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    files = {"seed.txt": "seed\n", **(base_files or {})}
    for rel, body in files.items():
        put(root, rel, body)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD").strip()
    git(root, "switch", "-q", "-c", branch)
    if plan is not None:
        put(root, "docs/plans/issue-7.md", plan, commit=True)
    return base


def put(root: Path, rel: str, body: str = "x\n", commit: bool = False) -> None:
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(body, encoding="utf-8")
    if commit:
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "work")


def run(script: Path, root: Path, *args: str, env: dict | None = None) -> tuple[int, str]:
    e = dict(CHILD_ENV)
    e.pop("GITHUB_HEAD_REF", None)
    e.pop("GITHUB_REF_NAME", None)
    e.update(env or {})
    proc = subprocess.run([sys.executable, str(script), *args], cwd=root, env=e,
                          capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def decl(value: str) -> str:
    return PLAN + f"\n仕様の振る舞い: {value}\n"


def contract(script: Path, tmp: Path, tag: str) -> list[tuple[str, bool]]:
    got: list[tuple[str, bool]] = []
    n = [0]

    def fresh(**kw) -> tuple[Path, str]:
        n[0] += 1
        d = tmp / f"{tag}{n[0]}"
        return d, repo(d, **kw)

    # 1) 正本が無い → 申告が無くても 0（計画も要らない）
    d, base = fresh(plan=None, branch="feature/x")
    put(d, "src/a.py", commit=True)
    rc, out = run(script, d, base)
    got += [("正本が無ければ計画が無くても 0", rc == 0 and "該当なし" in out)]
    for label, files in (("docs/ があるだけ", {"docs/index.md": "x\n"}),
                         ("docs/v1-notes/ は版でない", {"docs/v1-notes/shared/qa.csv": HEADER}),
                         ("版のディレクトリに shared・requirements・spec が無い", {"docs/v1/notes.md": "x\n"})):
        d, base = fresh(base_files=files)
        put(d, "src/a.py", commit=True)
        rc, _ = run(script, d, base)
        got += [(f"{label}なら正本でなく 0", rc == 0)]

    # 2) 正本があるのに申告が無い → 1。`変えない` → 0（陽性対照）。箇条書きも数える
    d, base = fresh(base_files=CANON)
    put(d, "src/a.py", commit=True)
    rc, out = run(script, d, base)
    got += [("正本があって申告が無ければ 1", rc == 1 and "仕様の振る舞い:" in out),
            ("1 のとき原本を案内する", "spec-writeback.md" in out)]
    for rel in ("docs/v1/spec/openapi.yaml", "docs/v1/requirements/r.md", "docs/v1/shared/qa.csv"):
        d, base = fresh(base_files={rel: "openapi: 3.0.0\n" if rel.endswith(".yaml") else "x,y,z\n"})
        rc, _ = run(script, d, base)
        got += [(f"spec-loop の形の qa.csv が無い（{rel} だけ）なら正本でなく 0", rc == 0)]
    d, base = fresh(base_files={**CANON, "docs/v2/spec/s.md": "x\n"})
    rc, out = run(script, d, base)
    got += [("spec-loop の形の qa.csv が v1 にあれば、spec/ だけの v2 を作業中の版と読む（申告が無ければ 1）", rc == 1 and "docs/v2/" in out)]
    d, base = fresh(base_files={"docs/v1/shared/qa.csv": "\ufeff" + HEADER})
    rc, _ = run(script, d, base)
    got += [("BOM 付きの qa.csv も spec-loop の形と読む（申告が無ければ 1）", rc == 1)]
    d, base = fresh(base_files=CANON, plan=decl("変えない"))
    put(d, "src/a.py", commit=True)
    rc, _ = run(script, d, base)
    got += [("申告が `変えない` なら 0", rc == 0)]
    d, base = fresh(base_files=CANON, plan=PLAN + "\n- 仕様の振る舞い: spec-loop の Issue\n")
    rc, _ = run(script, d, base)
    got += [("箇条書きの `- 仕様の振る舞い: spec-loop の Issue` も申告", rc == 0)]

    # 3) 値が違う・2 本以上・フェンスの中だけ → 1
    for label, extra in (("決まった値でない", "\n仕様の振る舞い: たぶん変えない\n"),
                         ("2 本以上", "\n仕様の振る舞い: 変えない\n仕様の振る舞い: 変えない\n"),
                         ("フェンスの中だけ", "\n```text\n仕様の振る舞い: 変えない\n```\n")):
        d, base = fresh(base_files=CANON, plan=PLAN + extra)
        rc, _ = run(script, d, base)
        got += [(f"申告が{label}なら 1", rc == 1)]

    # 4) 正本があって計画が見つからない → 2
    d, base = fresh(base_files=CANON, plan=None, branch="feature/x")
    rc, out = run(script, d, base)
    got += [("正本があって計画が見つからなければ 2", rc == 2 and "緑ではない" in out)]

    # 5) `変える`: 計画の `正本に起票する行:`（同じリポジトリでも）。正本の表に直接足しただけでは 1
    row = f"\n正本に起票する行: {PLAN_ROW}\n"
    d, base = fresh(base_files=CANON, plan=decl("変える") + row)
    rc, _ = run(script, d, base)
    got += [("`変える` で計画に行があれば 0（同じリポジトリ）", rc == 0)]
    d, base = fresh(base_files=CANON, plan=decl("変える") + f"\n- 正本に起票する行: {PLAN_ROW}\n")
    rc, _ = run(script, d, base)
    got += [("箇条書きの `- 正本に起票する行:` も数える", rc == 0)]
    d, base = fresh(base_files=CANON, plan=decl("変える"))
    put(d, "docs/v1/shared/qa.csv", HEADER + OLD_ROW + NEW_ROW, commit=True)
    rc, out = run(script, d, base)
    got += [("`変える` で正本の表に直接足しただけなら 1", rc == 1 and "正本に起票する行:" in out and "開発（#7）" in out)]
    d, base = fresh(base_files=CANON, plan=decl("変える") + f"\n```text\n正本に起票する行: {PLAN_ROW}\n```\n")
    rc, _ = run(script, d, base)
    got += [("`変える` で行がフェンスの中だけなら 1", rc == 1)]
    for label, r in (("列が 1 つ足りない", PLAN_ROW[:-1]),
                     ("別の Issue の起票元", PLAN_ROW.replace("（#7）", "（#8）")),
                     ("状態が `反映済み`", PLAN_ROW.replace(",確認中,", ",反映済み,")),
                     ("回答を埋めた", PLAN_ROW.replace(",未回答,", ",A,"))):
        d, base = fresh(base_files=CANON, plan=decl("変える") + f"\n正本に起票する行: {r}\n")
        rc, _ = run(script, d, base)
        got += [(f"`変える` で計画の行が{label}なら 1", rc == 1)]

    # 6) 正本が別のリポジトリ（宣言か scaffold-source.txt）
    sep = {".claude/dev-loop.md": "# 追補\n\n仕様の正本: acme/spec\n"}
    d, base = fresh(base_files=sep)
    rc, out = run(script, d, base)
    got += [("宣言で別のリポジトリの正本があれば申告が無いと 1", rc == 1 and "acme/spec" in out)]
    d, base = fresh(base_files={".claude/dev-loop.md": "```text\n仕様の正本: acme/spec\n```\n"})
    rc, _ = run(script, d, base)
    got += [("フェンスの中の `仕様の正本:` は宣言でない（0）", rc == 0)]
    d, base = fresh(base_files={".claude/dev-loop.md": "<!--\n例:\n仕様の正本: acme/spec\n-->\n"}, plan=None, branch="feature/x")
    rc, _ = run(script, d, base)
    got += [("HTML コメントの中の `仕様の正本:` は宣言でない（0）", rc == 0)]
    d, base = fresh(base_files={"scaffold-source.txt": "acme/spec@0123abc\n"})
    rc, out = run(script, d, base)
    got += [("scaffold-source.txt があれば正本（申告が無いと 1）", rc == 1 and "acme/spec" in out)]
    d, base = fresh(base_files=sep, plan=decl("変える") + row)
    rc, _ = run(script, d, base)
    got += [("別のリポジトリで `変える` と計画の行があれば 0", rc == 0)]
    d, base = fresh(base_files=sep, plan=decl("変える"))
    rc, out = run(script, d, base)
    got += [("別のリポジトリで `変える` なのに計画の行が無ければ 1", rc == 1 and "正本に起票する行:" in out)]
    # 計画が git に載っていない（gitignore した .claude/plans/）なら、行があっても 1
    d, base = fresh(base_files={**CANON, ".gitignore": ".claude/plans/\n"}, plan=None)
    put(d, ".claude/plans/issue-7.md", decl("変える") + row)
    rc, out = run(script, d, base)
    got += [("`変える` で計画が git に載っていなければ 1", rc == 1 and "git に載っていない" in out)]
    d, base = fresh(base_files={**CANON, ".gitignore": ".claude/plans/\n"}, plan=None)
    put(d, ".claude/plans/issue-7.md", decl("変えない"))
    rc, _ = run(script, d, base)
    got += [("`変えない` なら計画が git に載っていなくても 0", rc == 0)]

    # 7) 緑のケースの一覧から載った行が減った
    canon_green = {**CANON, "scaffold-green.txt": GREEN}
    for label, value, body, want in (("`変えない` で 1 行外した", "変えない", GREEN.split("a.T.test_2")[0], 1),
                                     ("`spec-loop の Issue` で 1 行外した", "spec-loop の Issue", GREEN.split("a.T.test_2")[0], 0),
                                     ("`変えない` で行を足しただけ", "変えない", GREEN + "a.T.test_3 " + "2" * 64 + "\n", 0),
                                     ("`変えない` で名前は同じまま指紋を変えた", "変えない", GREEN.replace("1" * 64, "3" * 64), 1),
                                     ("`変えない` で accepted-changed の行にした", "変えない",
                                      GREEN.split("a.T.test_2")[0] + "# accepted-changed: a.T.test_2\n", 1)):
        d, base = fresh(base_files=canon_green, plan=decl(value))
        put(d, "scaffold-green.txt", body, commit=True)
        rc, out = run(script, d, base)
        got += [(f"一覧: {label}なら {want}", rc == want and (want == 0 or "a.T.test_2" in out))]
    d, base = fresh(base_files={**canon_green, "svc/scaffold-green.txt": GREEN}, plan=decl("変えない"))
    (d / "svc" / "scaffold-green.txt").unlink()  # 消してコミットしない
    rc, out = run(script, d, base)
    got += [("一覧: 下の階層の一覧を消した（未コミット）なら 1", rc == 1 and "svc/scaffold-green.txt" in out)]
    d, base = fresh(base_files=canon_green, plan=decl("変える") + f"\n正本に起票する行: {PLAN_ROW}\n")
    put(d, "scaffold-green.txt", GREEN.split("a.T.test_2")[0], commit=True)
    rc, _ = run(script, d, base)
    got += [("一覧: `変える` で行を足しても、載った行を外したら 1", rc == 1)]

    # 8) `変える` で Issue の番号が取れない → 2。--plan の名前からは取る
    d, base = fresh(base_files=CANON, plan=None, branch="feature/x")
    put(d, "notes/plan.md", decl("変える"))
    rc, out = run(script, d, base, "--plan", "notes/plan.md")
    got += [("`変える` で Issue の番号が取れなければ 2", rc == 2)]
    d, base = fresh(base_files=CANON, plan=None, branch="feature/x")
    put(d, "notes/issue-7.md", decl("変える") + f"\n正本に起票する行: {PLAN_ROW}\n", commit=True)
    rc, _ = run(script, d, base, "--plan", "notes/issue-7.md")
    got += [("--plan の名前 issue-<n>.md から番号を取る", rc == 0)]
    d, base = fresh(base_files=CANON)
    git(d, "switch", "-q", "--detach", "HEAD")
    rc, out = run(script, d, base, env={"GITHUB_HEAD_REF": "issue/7-demo"})
    got += [("detached でも GITHUB_HEAD_REF から計画を当てる", rc == 1 and "issue-7.md" in out)]

    # 9) git が失敗 → 2
    d, base = fresh(base_files=CANON)
    rc, _ = run(script, d, "no-such-ref")
    got += [("git が失敗したら 2", rc == 2)]
    return got


MUTATIONS = {
    # 守る: 正本があれば、申告が 1 本で決まった値でない限り 0 にしない
    "申告が無くても通す": ('        return 1, "計画に `仕様の振る舞い:` の行が無い"', '        return 0, "計画に `仕様の振る舞い:` の行が無い"'),
    "2 本以上を通す": ("    if len(values) > 1:\n", "    if False:\n"),
    "値を見ない": ("    if value not in VALUES:\n", "    if False:\n"),
    "フェンスの中も数える": ("        if fence is not None:\n            continue\n", ""),
    "箇条書きの申告を数えない": (r'DECLARE = re.compile(r"^(?:[-*]\s+)?仕様の振る舞い:\s*(.*?)\s*$")',
                                 r'DECLARE = re.compile(r"^仕様の振る舞い:\s*(.*?)\s*$")'),
    # 守る: 正本があるのに計画が見つからなければ 0 にしない
    "計画が見つからなければ 0": ('        return 2, "正本があるのに計画ファイルが見つからない', '        return 0, "正本があるのに計画ファイルが見つからない'),
    # 守る: 正本が無ければ 0
    "正本が無くても申告を求める": ("    if version is None and separate is None:\n", "    if False:\n"),
    "版の名前を広げる（v1-notes を拾う）": ('VERSION_DIR = re.compile(r"^v([0-9]+)$")', 'VERSION_DIR = re.compile(r"^v([0-9]+)")'),
    "版の中身を見ない": ("and any((child / part).is_dir() for part in CANONICAL_PARTS)", "and True"),
    # 守る: `変える` の周の計画の行
    "計画の行を見ない": ("    if any(writeback_ok(r, issue) for r in plan_rows(plan_text)):\n", "    if True:\n"),
    "計画の行の列の数を見ない": ("        if len(cells) == len(COLUMNS):\n", "        if len(cells) >= 9:\n"),
    "起票元を見ない": ('    return (fields.get("起票元", "").strip() == f"開発（#{issue}）"\n', '    return (True\n'),
    "回答を見ない": ('            and fields.get("回答", "").strip() == NO_ANSWER\n', ""),
    "状態を見ない": ('            and fields.get("状態", "").strip() == OPEN_STATE)', "            )"),
    "計画の行をフェンスの中も読む": ("    for value in scan(plan_text, ROW_LINE):", "    for value in [m.group(1) for m in map(ROW_LINE.match, plan_text.splitlines()) if m]:"),
    "箇条書きの計画の行を数えない": (r'ROW_LINE = re.compile(r"^(?:[-*]\s+)?正本に起票する行:\s*(.*?)\s*$")', r'ROW_LINE = re.compile(r"^正本に起票する行:\s*(.*?)\s*$")'),
    "qa.csv の形を見ない": ("    if not any(is_qa_table(child / \"shared\" / \"qa.csv\") for _, child in found):\n", "    if not found:\n"),
    "BOM を残して読む": ('with path.open(encoding="utf-8-sig", newline="")', 'with path.open(encoding="utf-8", newline="")'),
    "計画が git に載っているかを見ない": ("    if not plan_tracked:\n", "    if False:\n"),
    # 守る: 正本が別のリポジトリ
    "scaffold-source.txt を見ない": ("    if src.is_file():\n", "    if False:\n"),
    "宣言を見ない": ("    if values:\n        return values[0]\n", ""),
    "宣言をコメントとフェンスの中も読む": ("    return list(env.visible_lines(text)) if text else []", "    return text.splitlines()"),
    # 守る: 緑のケースの一覧
    "一覧の減りを見ない": ("        if removed:\n", "        if False:\n"),
    "`spec-loop の Issue` でも一覧の減りを赤にする": ("    if value != FROM_SPEC_LOOP:\n", "    if True:\n"),
    "下の階層の一覧を見ない": ('if p.split("/")[-1] == GREEN_LIST]', "if p == GREEN_LIST]"),
    "指紋を比べず名前だけを比べる": ("for name, _ in green_pairs(old) - green_pairs(now)}", "for name in {n for n, _ in green_pairs(old)} - {n for n, _ in green_pairs(now)}}"),
    "消した一覧を見ない": ('if p.split("/")[-1] == GREEN_LIST]', 'if p.split("/")[-1] == GREEN_LIST and (root / p).is_file()]'),
    # 守る: 未コミットの変更・消した一覧を落とさない
    "3 点で取る（未コミットを見ない）": ('    rc, diff = git("diff", "--name-only", "--no-renames", base)\n',
                                       '    rc, diff = git("diff", "--name-only", "--no-renames", f"{base}...HEAD")\n'),
    # 判定できないものを緑にしない
    "Issue の番号が取れなくても 0": ('        return 2, "申告が `変える` なのに Issue の番号が取れない', '        return 0, "申告が `変える` なのに Issue の番号が取れない'),
    "git の失敗を 0 にする": ('        print(f"git で差分を取れなかった（base: {opts.base}）——判定していない（緑ではない）。")\n        return 2\n',
                             '        return 0\n'),
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def static_checks() -> None:
    print("原本と写し:")
    body = load(SCRIPT, "check_spec_writeback")
    qa = load(SPEC_LOOP_SCRIPTS / "check-qa-csv.py", "check_qa_csv")
    check("Q&A 表の列の写しが check-qa-csv.py の COLUMNS と同じ", body.COLUMNS == qa.COLUMNS)
    check("回答の写しが check-qa-csv.py の NO_ANSWER と同じ", body.NO_ANSWER == qa.NO_ANSWER)
    check("状態の写しが check-qa-csv.py の状態にあり、反映した状態でない",
          body.OPEN_STATE in qa.STATES and body.OPEN_STATE not in qa.REFLECTED)
    check("起票元の `開発` が check-qa-csv.py の起票元にある", "開発" in qa.SOURCES)
    doc = DOC.read_text(encoding="utf-8")
    start = doc.find("## 申告")
    section = doc[start:doc.find("\n## ", start + 1)] if start >= 0 else ""
    table_values = re.findall(r"^\| `([^`]+)` \|", section, flags=re.M)
    check("原本の「申告」の表の値が本体の VALUES と同じ（順も）", tuple(table_values) == tuple(body.VALUES))
    check("原本が PR の前に当てるコマンドを書く", "scripts/check-spec-writeback.py <周の base の SHA>" in doc)
    check("原本が計画の行（正本に起票する行:）を書く", "正本に起票する行: " in doc)
    check("原本が、周は正本の Q&A 表に書かないと決めている（W4）", "**正本の Q&A 表にも、周の中で書かない**" in doc)


def leak_control(tmp: Path) -> None:
    """申告漏れの陽性対照（受入基準 3）。本物の scaffold.py と green-list.py で作った一覧に当てる。"""
    print("申告漏れの陽性対照（本物の scaffold.py・green-list.py）:")
    scripts = tmp / "spec-loop-scripts"
    shutil.copytree(SPEC_LOOP_SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__"))
    d = tmp / "leak"
    assert_not_real_repo(d)
    ir = {"spec_ir_version": 1, "title": "計算", "features": [
        {"id": "F-001", "title": "倍にする", "source": ["spec/calc.md"], "qa": [],
         "operation": {"id": "double", "method": "POST", "path": "/calc/double",
                       "input": {"n": {"type": "integer"}}, "output": {"v": {"type": "integer"}}},
         "cases": [{"id": "F-001-C1", "title": "1 なら 2", "input": {"n": 1}, "expected": {"v": 2}}]}]}
    files = {"docs/v1/shared/qa.csv": HEADER + OLD_ROW, "docs/v1/spec/calc.md": "# 計算\n\n倍。\n",
             "docs/v1/spec/spec_ir.json": json.dumps(ir, ensure_ascii=False, indent=2),
             "spec_impl.py": 'def double(n):\n    return {"v": n * 2}\n', ".gitignore": "__pycache__/\n"}
    d.mkdir(parents=True)
    git(d, "init", "-q", "-b", "main")
    for rel, b in files.items():
        put(d, rel, b)

    def py(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", *args], cwd=d, capture_output=True, text=True, timeout=300, env=CHILD_ENV)

    gen = py(str(scripts / "scaffold.py"), "--repo", str(d))
    rec = py(str(scripts / "green-list.py"), "record", "--repo", str(d))
    check("試料: scaffold.py と green-list.py record が通る", gen.returncode == 0 and rec.returncode == 0)
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "base")
    base = git(d, "rev-parse", "HEAD").strip()
    git(d, "switch", "-q", "-c", "issue/7-demo")
    put(d, "docs/plans/issue-7.md", decl("変えない"), commit=True)
    green_check = lambda: py(str(scripts / "green-list.py"), "check", "--repo", str(d)).returncode  # noqa: E731
    check("対照: 変える前は green-list.py check が 0", green_check() == 0)
    check("対照: 変える前は check-spec-writeback.py が 0", run(SCRIPT, d, base)[0] == 0)
    put(d, "spec_impl.py", 'def double(n):\n    return {"v": n * 3}\n', commit=True)
    check("`変えない` のまま振る舞いを変えたら green-list.py check が 1", green_check() == 1)
    listed = (d / "scaffold-green.txt").read_text(encoding="utf-8")
    put(d, "scaffold-green.txt", "".join(ln for ln in listed.splitlines(True) if ln.startswith("#")), commit=True)
    check("壊れたケースを一覧から手で外すと green-list.py check は 0 に戻る（#1000 の守らないもの）", green_check() == 0)
    rc, out = run(SCRIPT, d, base)
    check("そのとき check-spec-writeback.py が 1 で外したケースを名指す", rc == 1 and "test_f_001" in out)


def main() -> int:
    static_checks()
    src = SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        leak_control(root)
        print("陽性対照（元の本体——全部通らなければならない）:")
        for name, ok in contract(SCRIPT, root / "real", "r"):
            check(name, ok)
        print("変異（1 箇所ずつ壊す——契約が破れなければ失格）:")
        for i, (name, (old, new)) in enumerate(MUTATIONS.items()):
            if src.count(old) != 1:
                check(f"変異 `{name}` の当て先が 1 箇所", False)
                continue
            mutant = root / f"mutant{i}.py"
            mutant.write_text(src.replace(old, new), encoding="utf-8")
            broken = [nm for nm, ok in contract(mutant, root / f"m{i}", f"m{i}") if not ok]
            check(f"変異 `{name}` を契約が捕まえる", bool(broken))
    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


if __name__ == "__main__":
    sys.exit(main())
