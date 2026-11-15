#!/usr/bin/env python3
"""`check-spec-writeback.py`（仕様にある振る舞いを変える周が、申告と正本への戻しを残しているかを見る。#1001）の回帰テスト。

    python3 scripts/test-check-spec-writeback.py            # 変異は既定で 4 つまで同時に当てる
    python3 scripts/test-check-spec-writeback.py --jobs 1   # 変異を 1 つずつ当てる（check-all.py --jobs 1 が渡す）

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）——`test-check-deps-declared.py` と同じ形で、
**`dev-loop` はどのリポジトリでも使えるスキル**なので。

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリを作り、そこだけを対象にする（`assert_not_real_repo`）。

**変異テストを含む。** 本体の docstring の「守る」の各行に変異を 1 つ以上当て、**壊したのに契約が保たれるなら失格**とする。
**変異の前に、元の本体で全部緑であること（陽性対照）を見る。** 変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
**変異の回は最初に破れた契約で止め、変異どうしは別々のプロセスで同時に当てる。土台のリポジトリは形ごとに 1 度作って複製する**
（#1049。`test-check-deps-declared.py` の #1021 と同じ形。理由は `MUTANT_JOBS_MAX` の上）。
**変異を入れた本体は、本体の隣のファイルごと写した場所に置く**（#1053。`place_body`）——本体は同じ場所の `check-unattended-env.py` を読み込むので、
単独で一時ディレクトリに置くと何も変えない写しでも契約が破れ、変異が効いたのか置き場所のせいかを判別しない。
**置き方の陽性対照**: 何も変えない写しを同じ置き方で置き、契約が全部通ることを毎回見る。あわせて単独で置く形（#1053 の前の置き方）では
何も変えない写しでも契約が破れることを見る——置き方の対照が置き方を判別していることの確かめ。

**申告漏れの陽性対照**（Issue の受入基準 3）: spec-loop の本物の `scaffold.py` で `scaffold/` を作り、実装の見本と本物の `green-list.py record` で
緑のケースの一覧を書いた試料で、計画の申告を `変えない` のまま実装の値を変えると `green-list.py check` が 1、壊れたケースを一覧から手で外すと
`check` は 0 に戻るが `check-spec-writeback.py` が 1、を見る（変える前は両方 0）。spec-loop のスクリプトは一時ディレクトリに写し、`python3 -I` で、
子のプロセスの環境から `PYTHONPATH` を外して走らせる（`test-green-list.py` と同じ理由）。

あわせて、**申告の値が原本（`references/spec-writeback.md` の「申告」の表）と本体の `VALUES` で同じこと**と、
**Q&A 表の列・回答・状態の写しが spec-loop の `check-qa-csv.py` と同じこと**を見る（dev-loop から spec-loop を相対パスで指せないので写している）。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop"
SCRIPT = SKILL_DIR / "scripts" / "check-spec-writeback.py"
DOC = SKILL_DIR / "references" / "spec-writeback.md"
SPEC_LOOP_SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
CHILD_ENV = {k: v for k, v in os.environ.items() if k != "PYTHONPATH" and not k.startswith("GIT_")}
# 偽のリポジトリの git には利用者・システムの設定を読ませない——読めば利用者の hook・署名・fsmonitor・保守が効く（#1028 と同じ。#1049）
GIT_ENV = {**CHILD_ENV, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

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
                          check=True, capture_output=True, text=True, env=GIT_ENV).stdout


def repo(root: Path, *, plan: str | None = PLAN, branch: str = "issue/7-demo",
         base_files: dict[str, str] | None = None) -> str:
    """偽のリポジトリを作り、base の SHA を返す。計画ファイルは base の後のコミットに置く（周の形）。"""
    assert_not_real_repo(root)
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    # コミットの後の `git maintenance run --auto` は切り離して走り、`.git/objects/maintenance.lock` を作っては消す——
    # 土台を複製する `copytree` がその途中に当たると落ちる（#1028・#1032）。`.git/config` に書くので複製にも写る
    git(root, "config", "maintenance.auto", "false")
    git(root, "config", "gc.auto", "0")
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


# **土台のリポジトリは形ごとに 1 度だけ作り、複製する**（#1049。#1021 と同じ）——契約 1 回で 40 近い土台を作り直し、
# 1 つに `git` を 6〜7 回起こしていた。土台の形は `repo` の引数だけで決まるので、同じ引数なら中身（コミットの SHA まで）が同じ複製で足りる。
# 置き場はプロセスごとに分ける（変異の作業者は別プロセスで、同じ一時ディレクトリの下に作る）。
_TEMPLATES: dict[tuple, tuple[Path, str]] = {}


def fresh_repo(d: Path, *, plan: str | None = PLAN, branch: str = "issue/7-demo",
               base_files: dict[str, str] | None = None) -> str:
    """`repo(d, ...)` と同じリポジトリを、土台の複製で作って base の SHA を返す。"""
    assert_not_real_repo(d)
    key = (plan, branch, tuple(sorted((base_files or {}).items())))
    if key not in _TEMPLATES:
        tpl = d.parent.parent / f"tpl-{os.getpid()}" / str(len(_TEMPLATES))
        _TEMPLATES[key] = (tpl, repo(tpl, plan=plan, branch=branch, base_files=base_files))
    tpl, base = _TEMPLATES[key]
    shutil.copytree(tpl, d, symlinks=True)
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


def contract(script: Path, tmp: Path, tag: str) -> Iterator[tuple[str, bool]]:
    """契約を 1 ケースずつ当てて `(名前, 通ったか)` を出す。**逐次に評価する**ので、変異の回は最初に破れたところで止められる（#1049）。"""
    n = [0]

    def fresh(**kw) -> tuple[Path, str]:
        n[0] += 1
        d = tmp / f"{tag}{n[0]}"
        return d, fresh_repo(d, **kw)

    # 1) 正本が無い → 申告が無くても 0（計画も要らない）
    d, base = fresh(plan=None, branch="feature/x")
    put(d, "src/a.py", commit=True)
    rc, out = run(script, d, base)
    yield from [("正本が無ければ計画が無くても 0", rc == 0 and "該当なし" in out)]
    for label, files in (("docs/ があるだけ", {"docs/index.md": "x\n"}),
                         ("docs/v1-notes/ は版でない", {"docs/v1-notes/shared/qa.csv": HEADER}),
                         ("版のディレクトリに shared・requirements・spec が無い", {"docs/v1/notes.md": "x\n"})):
        d, base = fresh(base_files=files)
        put(d, "src/a.py", commit=True)
        rc, _ = run(script, d, base)
        yield from [(f"{label}なら正本でなく 0", rc == 0)]

    # 2) 正本があるのに申告が無い → 1。`変えない` → 0（陽性対照）。箇条書きも数える
    d, base = fresh(base_files=CANON)
    put(d, "src/a.py", commit=True)
    rc, out = run(script, d, base)
    yield from [("正本があって申告が無ければ 1", rc == 1 and "仕様の振る舞い:" in out),
            ("1 のとき原本を案内する", "spec-writeback.md" in out)]
    for rel in ("docs/v1/spec/openapi.yaml", "docs/v1/requirements/r.md", "docs/v1/shared/qa.csv"):
        d, base = fresh(base_files={rel: "openapi: 3.0.0\n" if rel.endswith(".yaml") else "x,y,z\n"})
        rc, _ = run(script, d, base)
        yield from [(f"spec-loop の形の qa.csv が無い（{rel} だけ）なら正本でなく 0", rc == 0)]
    d, base = fresh(base_files={**CANON, "docs/v2/spec/s.md": "x\n"})
    rc, out = run(script, d, base)
    yield from [("spec-loop の形の qa.csv が v1 にあれば、spec/ だけの v2 を作業中の版と読む（申告が無ければ 1）", rc == 1 and "docs/v2/" in out)]
    # 版のディレクトリでも shared・requirements・spec が無ければ版に数えない——作業中の版は v1 のまま（#1053。変異 `版の中身を見ない` を捕まえる）
    d, base = fresh(base_files={**CANON, "docs/v2/notes.md": "x\n"})
    rc, out = run(script, d, base)
    yield from [("v2 に shared・requirements・spec が無ければ作業中の版は v1 のまま（申告が無ければ 1）",
                 rc == 1 and "docs/v1/" in out and "docs/v2/" not in out)]
    d, base = fresh(base_files={"docs/v1/shared/qa.csv": "\ufeff" + HEADER})
    rc, _ = run(script, d, base)
    yield from [("BOM 付きの qa.csv も spec-loop の形と読む（申告が無ければ 1）", rc == 1)]
    d, base = fresh(base_files=CANON, plan=decl("変えない"))
    put(d, "src/a.py", commit=True)
    rc, _ = run(script, d, base)
    yield from [("申告が `変えない` なら 0", rc == 0)]
    d, base = fresh(base_files=CANON, plan=PLAN + "\n- 仕様の振る舞い: spec-loop の Issue\n")
    rc, _ = run(script, d, base)
    yield from [("箇条書きの `- 仕様の振る舞い: spec-loop の Issue` も申告", rc == 0)]

    # 3) 値が違う・2 本以上・フェンスの中だけ → 1
    for label, extra in (("決まった値でない", "\n仕様の振る舞い: たぶん変えない\n"),
                         ("2 本以上", "\n仕様の振る舞い: 変えない\n仕様の振る舞い: 変えない\n"),
                         ("フェンスの中だけ", "\n```text\n仕様の振る舞い: 変えない\n```\n")):
        d, base = fresh(base_files=CANON, plan=PLAN + extra)
        rc, _ = run(script, d, base)
        yield from [(f"申告が{label}なら 1", rc == 1)]

    # 4) 正本があって計画が見つからない → 2
    d, base = fresh(base_files=CANON, plan=None, branch="feature/x")
    rc, out = run(script, d, base)
    yield from [("正本があって計画が見つからなければ 2", rc == 2 and "緑ではない" in out)]

    # 5) `変える`: 計画の `正本に起票する行:`（同じリポジトリでも）。正本の表に直接足しただけでは 1
    row = f"\n正本に起票する行: {PLAN_ROW}\n"
    d, base = fresh(base_files=CANON, plan=decl("変える") + row)
    rc, _ = run(script, d, base)
    yield from [("`変える` で計画に行があれば 0（同じリポジトリ）", rc == 0)]
    d, base = fresh(base_files=CANON, plan=decl("変える") + f"\n- 正本に起票する行: {PLAN_ROW}\n")
    rc, _ = run(script, d, base)
    yield from [("箇条書きの `- 正本に起票する行:` も数える", rc == 0)]
    d, base = fresh(base_files=CANON, plan=decl("変える"))
    put(d, "docs/v1/shared/qa.csv", HEADER + OLD_ROW + NEW_ROW, commit=True)
    rc, out = run(script, d, base)
    yield from [("`変える` で正本の表に直接足しただけなら 1", rc == 1 and "正本に起票する行:" in out and "開発（#7）" in out)]
    d, base = fresh(base_files=CANON, plan=decl("変える") + f"\n```text\n正本に起票する行: {PLAN_ROW}\n```\n")
    rc, _ = run(script, d, base)
    yield from [("`変える` で行がフェンスの中だけなら 1", rc == 1)]
    for label, r in (("列が 1 つ足りない", PLAN_ROW[:-1]),
                     ("別の Issue の起票元", PLAN_ROW.replace("（#7）", "（#8）")),
                     ("状態が `反映済み`", PLAN_ROW.replace(",確認中,", ",反映済み,")),
                     ("回答を埋めた", PLAN_ROW.replace(",未回答,", ",A,"))):
        d, base = fresh(base_files=CANON, plan=decl("変える") + f"\n正本に起票する行: {r}\n")
        rc, _ = run(script, d, base)
        yield from [(f"`変える` で計画の行が{label}なら 1", rc == 1)]

    # 6) 正本が別のリポジトリ（宣言か scaffold-source.txt）
    sep = {".claude/dev-loop.md": "# 追補\n\n仕様の正本: acme/spec\n"}
    d, base = fresh(base_files=sep)
    rc, out = run(script, d, base)
    yield from [("宣言で別のリポジトリの正本があれば申告が無いと 1", rc == 1 and "acme/spec" in out)]
    d, base = fresh(base_files={".claude/dev-loop.md": "```text\n仕様の正本: acme/spec\n```\n"})
    rc, _ = run(script, d, base)
    yield from [("フェンスの中の `仕様の正本:` は宣言でない（0）", rc == 0)]
    d, base = fresh(base_files={".claude/dev-loop.md": "<!--\n例:\n仕様の正本: acme/spec\n-->\n"}, plan=None, branch="feature/x")
    rc, _ = run(script, d, base)
    yield from [("HTML コメントの中の `仕様の正本:` は宣言でない（0）", rc == 0)]
    d, base = fresh(base_files={"scaffold-source.txt": "acme/spec@0123abc\n"})
    rc, out = run(script, d, base)
    yield from [("scaffold-source.txt があれば正本（申告が無いと 1）", rc == 1 and "acme/spec" in out)]
    d, base = fresh(base_files=sep, plan=decl("変える") + row)
    rc, _ = run(script, d, base)
    yield from [("別のリポジトリで `変える` と計画の行があれば 0", rc == 0)]
    d, base = fresh(base_files=sep, plan=decl("変える"))
    rc, out = run(script, d, base)
    yield from [("別のリポジトリで `変える` なのに計画の行が無ければ 1", rc == 1 and "正本に起票する行:" in out)]
    # 計画が git に載っていない（gitignore した .claude/plans/）なら、行があっても 1
    d, base = fresh(base_files={**CANON, ".gitignore": ".claude/plans/\n"}, plan=None)
    put(d, ".claude/plans/issue-7.md", decl("変える") + row)
    rc, out = run(script, d, base)
    yield from [("`変える` で計画が git に載っていなければ 1", rc == 1 and "git に載っていない" in out)]
    d, base = fresh(base_files={**CANON, ".gitignore": ".claude/plans/\n"}, plan=None)
    put(d, ".claude/plans/issue-7.md", decl("変えない"))
    rc, _ = run(script, d, base)
    yield from [("`変えない` なら計画が git に載っていなくても 0", rc == 0)]

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
        yield from [(f"一覧: {label}なら {want}", rc == want and (want == 0 or "a.T.test_2" in out))]
    d, base = fresh(base_files={**canon_green, "svc/scaffold-green.txt": GREEN}, plan=decl("変えない"))
    (d / "svc" / "scaffold-green.txt").unlink()  # 消してコミットしない
    rc, out = run(script, d, base)
    yield from [("一覧: 下の階層の一覧を消した（未コミット）なら 1", rc == 1 and "svc/scaffold-green.txt" in out)]
    d, base = fresh(base_files=canon_green, plan=decl("変える") + f"\n正本に起票する行: {PLAN_ROW}\n")
    put(d, "scaffold-green.txt", GREEN.split("a.T.test_2")[0], commit=True)
    rc, _ = run(script, d, base)
    yield from [("一覧: `変える` で行を足しても、載った行を外したら 1", rc == 1)]

    # 8) `変える` で Issue の番号が取れない → 2。--plan の名前からは取る
    d, base = fresh(base_files=CANON, plan=None, branch="feature/x")
    put(d, "notes/plan.md", decl("変える"))
    rc, out = run(script, d, base, "--plan", "notes/plan.md")
    yield from [("`変える` で Issue の番号が取れなければ 2", rc == 2)]
    d, base = fresh(base_files=CANON, plan=None, branch="feature/x")
    put(d, "notes/issue-7.md", decl("変える") + f"\n正本に起票する行: {PLAN_ROW}\n", commit=True)
    rc, _ = run(script, d, base, "--plan", "notes/issue-7.md")
    yield from [("--plan の名前 issue-<n>.md から番号を取る", rc == 0)]
    d, base = fresh(base_files=CANON)
    git(d, "switch", "-q", "--detach", "HEAD")
    rc, out = run(script, d, base, env={"GITHUB_HEAD_REF": "issue/7-demo"})
    yield from [("detached でも GITHUB_HEAD_REF から計画を当てる", rc == 1 and "issue-7.md" in out)]

    # 9) git が失敗 → 2
    d, base = fresh(base_files=CANON)
    rc, _ = run(script, d, "no-such-ref")
    yield from [("git が失敗したら 2", rc == 2)]


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


# **変異は別々のプロセスで同時に当て、最初に破れた契約で止める**（#1049。#1021 と同じ）——直列に契約を 31 回（陽性対照 1 回・変異 30 個）
# 全部当てていて（契約 1 回で約 26 秒・git を 316 回）、2026-11-15 の `check-all.py`（28 並列）で 437.9 秒、全体の律速だった（#1040 の測定）。
# 変異の判定は「1 件でも破れたか」なので、止めても判定は変わらない。**陽性対照は止めずに全部を見る。**
# **`--jobs N` で絞る**——`check-all.py` が入れ子として親の半分を渡す（`NESTED`）。上限は `test-check-deps-declared.py` と同じ 4。
MUTANT_JOBS_MAX = max(1, min(4, os.cpu_count() or 1))
MUTANT_JOBS = MUTANT_JOBS_MAX
pool_sizes: list[int] = []


class _MutantPool(concurrent.futures.ProcessPoolExecutor):
    """変異の作業者のプール。**渡された作業者の数を `pool_sizes` に残す**（`--pool-size` が出す）。"""

    def __init__(self, max_workers, **kwargs):
        pool_sizes.append(max_workers)
        super().__init__(max_workers, **kwargs)


def place_body(dest: Path, text: str) -> Path:
    """本体の隣のファイルごと `dest` に写し、本体だけを `text` に差し替えて、そのパスを返す（#1053）。

    **本体は同じ場所の `check-unattended-env.py` を読み込む**（`HERE / …`）——本体だけを一時ディレクトリに置くと、
    何も変えない写しでも契約が破れる。どの隣を読むかを数えずにディレクトリごと写す（隣を読む箇所が増えても置き方は追従する）。"""
    assert_not_real_repo(dest)
    shutil.copytree(SCRIPT.parent, dest, ignore=shutil.ignore_patterns("__pycache__"))
    body = dest / SCRIPT.name
    body.write_text(text, encoding="utf-8")
    return body


def _kill_one(job: tuple[int, str, str, bool]) -> list[str]:
    """作業者で本体の写しを 1 つ当て、破れた契約の名前を返す。

    `full` が偽（変異）なら**最初に破れたところで止める**——判定は「1 件でも破れたか」なので。
    真（何も変えない写しの陽性対照）なら止めずに全部を当てる。"""
    i, text, tmp, full = job
    body = place_body(Path(tmp) / f"body{i}", text)
    broken = []
    for name, ok in contract(body, Path(tmp) / f"m{i}", f"m{i}"):
        if not ok:
            broken.append(name)
            if not full:
                break
    return broken


def kill_mutations(mutations: dict[str, tuple[str, str]], src: str, tmp: Path, *, identity: bool = True) -> None:
    """変異を当てる。`identity` が真なら、**何も変えない写しを変異と同じ置き方（`place_body`）・同じプールで当て**、
    契約が全部通ることを見る（置き方の陽性対照。#1053）——通らなければ、変異が捕まったのは置き場所のせいかもしれない。"""
    order, jobs = [], []  # order: (変異の名前, jobs の番号。当てる先が 1 箇所でなければ None)
    if identity:
        jobs.append((len(mutations), src, str(tmp), True))
    for i, (name, (old, new)) in enumerate(mutations.items()):
        if src.count(old) != 1:
            order.append((name, None))
            continue
        order.append((name, len(jobs)))
        jobs.append((i, src.replace(old, new), str(tmp), False))
    with _MutantPool(max_workers=MUTANT_JOBS, mp_context=multiprocessing.get_context("spawn")) as pool:
        results = list(pool.map(_kill_one, jobs))
    if identity:
        broken = results[0]
        check(f"置き方の陽性対照: 何も変えない写しを変異と同じ置き方で当てると契約が全部通る（破れた: {broken or 'なし'}）", not broken)
    for name, k in order:  # 出力は変異の宣言順（終わった順ではない）
        if k is None:
            check(f"変異 `{name}` の当て先が 1 箇所", False)
        else:
            check(f"変異 `{name}` を契約が捕まえる", bool(results[k]))


def check_solo_placement_breaks(src: str, tmp: Path) -> None:
    """置き方の対照が置き方を判別していることの確かめ（#1053）: 本体を**単独で**一時ディレクトリに置く形（#1053 の前の置き方）なら、
    何も変えない写しでも契約が破れる。破れなくなったら（本体が隣を読まなくなったら）、置き方の陽性対照は何も判別していない——
    そのときはこの確かめと `place_body` の理由を見直す。最初に破れたところで止める。"""
    solo = tmp / "solo" / SCRIPT.name
    assert_not_real_repo(solo.parent)
    solo.parent.mkdir(parents=True)
    solo.write_text(src, encoding="utf-8")
    broken = next((name for name, ok in contract(solo, tmp / "solo-m", "s") if not ok), None)
    check(f"置き方の対照: 本体を単独で置くと、何も変えない写しでも契約が破れる（最初に破れた: {broken or 'なし'}）", broken is not None)


def check_pool_size() -> None:
    """自分を `--jobs N --pool-size` で起こし、プールに渡した作業者の数が `min(N, 上限)` かを見る
    （`test-check-deps-declared.py` と同じ形——受けた `--jobs` を使わなくても、遅く・速くなるだけで緑のままなので）。"""
    for asked in (1, 99):
        want = min(asked, MUTANT_JOBS_MAX)
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--jobs", str(asked), "--pool-size"],
                              capture_output=True, text=True, timeout=120)
        got = proc.stdout.strip()
        check(f"--jobs {asked} で変異のプールに渡す作業者は {want}（出力: {got or '空'}・終了コード {proc.returncode}）",
              proc.returncode == 0 and got == str(want))


def main() -> int:
    global MUTANT_JOBS
    parser = argparse.ArgumentParser(description="check-spec-writeback.py の回帰テスト")
    parser.add_argument("--jobs", type=int, default=MUTANT_JOBS_MAX,
                        help=f"変異を同時に当てるプロセスの数（既定と上限: {MUTANT_JOBS_MAX}。1 で 1 つずつ）")
    parser.add_argument("--pool-size", action="store_true",
                        help="変異のプールに渡す作業者の数を出して終わる（試料の中で使う）")
    opts = parser.parse_args()
    if opts.jobs < 1:
        parser.error(f"--jobs は 1 以上: {opts.jobs}")
    MUTANT_JOBS = min(opts.jobs, MUTANT_JOBS_MAX)
    if opts.pool_size:
        with tempfile.TemporaryDirectory() as tmp:
            # 変異を当てる経路そのもの（`kill_mutations`）でプールを作る——変異が 0 件なので作業者は起きない
            kill_mutations({}, "", Path(tmp), identity=False)
        print(pool_sizes[-1] if pool_sizes else "")
        return 0

    static_checks()
    print("変異の作業者の数:")
    check_pool_size()
    src = SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        leak_control(root)
        print("陽性対照（元の本体——全部通らなければならない）:")
        for name, ok in contract(SCRIPT, root / "real", "r"):
            check(name, ok)
        print("置き方（変異を置く場所が判定を決めていないか。#1053）:")
        check_solo_placement_breaks(src, root)
        print("変異（1 箇所ずつ壊す——契約が破れなければ失格）。何も変えない写しも同じ置き方で当てる:")
        kill_mutations(MUTATIONS, src, root)
    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


if __name__ == "__main__":
    sys.exit(main())
