#!/usr/bin/env python3
"""`check-plan-scope.py` の回帰テスト。

    python3 scripts/test-check-plan-scope.py

**このテストは実環境を触らない。** 毎回テンポラリに偽リポジトリを作り、そこだけを
対象にする（`assert_not_real_repo` がそれを担保する）。

**変異テストを含む。** 検査本体を 1 箇所ずつ壊し、**壊したのに契約が保たれるなら失格**とする。
「正しい入力で緑」だけでは、**何も検査しない実装でも通る**。

**この検査の壊れ方は 2 つある**——**範囲の外を見逃す**（緩すぎ）と、
**範囲の中を外と言う**（厳しすぎ）。**契約は両方を持つ。**
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "check-plan-scope.py"
# 依存の申告の判定（#996）はプラグインの本体を読み込む——偽リポジトリにも同じ場所に置く
DEPS_REL = "plugins/dev-loop/skills/dev-loop/scripts/check-deps-declared.py"
DEPS_SCRIPT = REAL_REPO / DEPS_REL

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


def git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "-C", str(root), *args],
        check=True, capture_output=True, text=True,
    )


PLAN = """# Issue #7 の計画

## 1. 変更範囲

触る:

- `plugins/demo/SKILL.md` — 本文
- `scripts/*.py` — 歯止め
- `docs/` — 一式

触らない:

- `diagrams/` 一切
- `never/touched.md`

## 2. 乗るデプロイ経路

省略。
"""


def build(root: Path, *, plan: str | None = PLAN, branch: str = "issue/7-demo",
          head_files: dict[str, str] | None = None,
          script_text: str | None = None, deps_text: str | None = None) -> Path:
    """偽リポジトリを作り、base（main）と HEAD を持たせる。scripts/ の場所を返す。"""
    assert_not_real_repo(root)
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    (root / "seed.txt").write_text("seed\n")
    # 本体が読み込む依存の判定は base に置く（差分に出さない）
    deps = root / DEPS_REL
    deps.parent.mkdir(parents=True)
    deps.write_text(deps_text if deps_text is not None else DEPS_SCRIPT.read_text())
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")

    scripts = root / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "check-plan-scope.py").write_text(
        script_text if script_text is not None else SCRIPT.read_text()
    )

    git(root, "switch", "-q", "-c", branch)
    if plan is not None:
        (root / "docs" / "plans").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "plans" / "issue-7.md").write_text(plan)
    for rel, body in (head_files or {}).items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "work")
    return scripts


PLAN_NO_DOCS = PLAN.replace("- `docs/` — 一式\n", "")


def outside(out: str) -> str:
    """「変更範囲の外に出ているファイル」の列挙部分だけを返す（無ければ空）。"""
    marker = "変更範囲の外に出ているファイル:"
    return out.split(marker, 1)[1] if marker in out else ""


def run(root: Path, *args: str, env: dict | None = None, detach: bool = False) -> tuple[int, str]:
    """検査を回す。`detach=True` は **CI と同じ detached HEAD** を作ってから回す。"""
    if detach:
        git(root, "switch", "-q", "--detach", "HEAD")
    e = dict(os.environ)
    # 実行環境が GitHub Actions だと、テストが本物の値を拾ってしまう
    e.pop("GITHUB_HEAD_REF", None); e.pop("GITHUB_REF_NAME", None)
    e.update(env or {})
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "check-plan-scope.py"), *args],
        capture_output=True, text=True, check=False, cwd=root, env=e,
    )
    return proc.returncode, proc.stdout + proc.stderr


# ------------------------------------------------------------------- 契約
def contract(tmp: Path, tag: str, script_text: str | None = None,
             deps_text: str | None = None) -> list[tuple[str, bool]]:
    got: list[tuple[str, bool]] = []
    i = [0]

    def fresh(**kw) -> Path:
        i[0] += 1
        d = tmp / f"{tag}{i[0]}"
        build(d, script_text=script_text, deps_text=deps_text, **kw)
        return d

    # 1) 範囲の中だけ → 緑
    d = fresh(head_files={
        "plugins/demo/SKILL.md": "x\n",
        "scripts/new.py": "x\n",
        "docs/a/b.md": "x\n",
    })
    rc, out = run(d, "main")
    got += [
        ("範囲の中だけなら rc=0", rc == 0),
        ("`/` 終わりは配下に当たる", "docs/a/b.md" not in out),
    ]

    # 2) 範囲の外が 1 つ → 赤、しかも名指し
    d = fresh(head_files={"plugins/demo/SKILL.md": "x\n", "never/touched.md": "x\n"})
    rc, out = run(d, "main")
    got += [
        ("範囲の外があれば rc=1", rc == 1),
        ("範囲の外を名指しする", "never/touched.md" in out),
        ("範囲の中を外と言わない", "plugins/demo/SKILL.md" not in outside(out)),
    ]

    # 3) 「触らない」側に書いてあっても、触ったらエラー
    d = fresh(head_files={"diagrams/x.drawio": "x\n"})
    rc, out = run(d, "main")
    got += [("触らないと書いた先を触ったら rc=1", rc == 1)]

    # 4) 計画ファイル自身は免除（**`docs/` を触る側から外して測る**——
    #    入れたままだと「覆われているから通った」と区別がつかない）
    d = fresh(plan=PLAN_NO_DOCS, head_files={"plugins/demo/SKILL.md": "x\n"})
    rc, out = run(d, "main")
    got += [
        ("計画ファイル自身は数えない", rc == 0),
        ("計画ファイルを外として名指ししない", "issue-7.md" not in outside(out)),
    ]
    # 陽性対照——同じ計画で、覆われていない別のファイルは外として出る
    d = fresh(plan=PLAN_NO_DOCS, head_files={"docs/a.md": "x\n"})
    rc, out = run(d, "main")
    got += [("陽性対照: 覆われない docs/ は外として出る", rc == 1 and "docs/a.md" in outside(out))]

    # 5) 計画ファイルが無い → 判定しないが、黙らない
    d = fresh(plan=None, head_files={"whatever.md": "x\n"})
    rc, out = run(d, "main")
    got += [
        ("計画ファイルが無ければ rc=0", rc == 0),
        ("見ていないことを出す", "判定していない" in out),
    ]

    # 6) 「変更範囲」の節が無い → 赤（黙って通さない）
    d = fresh(plan="# 計画\n\n## 1. なにか\n\n本文。\n",
              head_files={"plugins/demo/SKILL.md": "x\n"})
    rc, out = run(d, "main")
    got += [("変更範囲の節が読めなければ rc=1", rc == 1)]

    # 7) 「触る:」が無い → 赤
    d = fresh(plan="# 計画\n\n## 1. 変更範囲\n\n触らない:\n\n- `a/`\n",
              head_files={"plugins/demo/SKILL.md": "x\n"})
    rc, out = run(d, "main")
    got += [("触る側が無ければ rc=1", rc == 1)]

    # 8) 別の Issue の計画ファイルが差分にあっても、それで採点しない
    d = fresh(plan=None, branch="issue/7-demo", head_files={
        "docs/plans/issue-999.md": "# 他人の計画\n\n## 変更範囲\n\n触る:\n\n- `zzz/`\n",
        "never/touched.md": "x\n",
    })
    rc, out = run(d, "main")
    got += [("番号を名乗るブランチは、差分の別計画で代用しない", rc == 0 and "判定していない" in out)]

    # 9) **detached HEAD（CI と同じ形）でも、GITHUB_HEAD_REF があれば働く。**
    #    **ここが無いと、この検査は CI で一度も働かない**（実際にそうなっていた）。
    d = fresh(head_files={"never/touched.md": "x\n"})
    rc, out = run(d, "main", env={"GITHUB_HEAD_REF": "issue/7-demo"}, detach=True)
    got += [
        ("detached でも GITHUB_HEAD_REF から計画を当てる", "issue-7.md" in out),
        ("detached でも範囲の外を捕まえる", rc == 1 and "never/touched.md" in outside(out)),
    ]

    # 10) detached で環境変数も無ければ、**黙らずに「判定していない」**。
    #     **差分の別計画で代用してはならない**（1 度目の修正が detached で抜けた道）。
    d = fresh(plan=None, head_files={
        "docs/plans/issue-999.md": "# 他人の計画\n\n## 変更範囲\n\n触る:\n\n- `zzz/`\n",
        "never/touched.md": "x\n",
    })
    rc, out = run(d, "main", detach=True)
    got += [
        ("detached かつ環境変数なしなら判定しない", rc == 0 and "判定していない" in out),
        ("detached でも差分の別計画で代用しない", "issue-999" not in outside(out)),
        # **git が返す "HEAD" をブランチ名として報告しない**——
        # そう報告すると、読む側は「ブランチ名は取れている」と読む。
        ("git の HEAD をブランチ名として報告しない", "ブランチ: (取れない)" in out),
    ]

    # 11) GITHUB_REF_NAME が "HEAD" のときは、ブランチ名として使わない
    d = fresh(head_files={"never/touched.md": "x\n"})
    rc, out = run(d, "main", env={"GITHUB_REF_NAME": "HEAD"}, detach=True)
    got += [
        ("GITHUB_REF_NAME が HEAD なら名前として使わない", rc == 0 and "判定していない" in out),
        ("GITHUB_REF_NAME の HEAD をブランチ名として報告しない", "ブランチ: (取れない)" in out),
    ]

    # 12) 依存の申告（#996）——範囲の中（docs/）の package.json を、申告せずに足したら赤
    d = fresh(head_files={"docs/app/package.json": "{}\n"})
    rc, out = run(d, "main")
    got += [
        ("依存のファイルを申告せずに足したら rc=1", rc == 1),
        ("依存のファイルを名指しする", "docs/app/package.json" in out),
        ("依存の申告の書き方を案内する", "依存の追加・更新: あり" in out),
        ("範囲の中の依存のファイルを範囲の外と言わない", "package.json" not in outside(out)),
    ]
    # 13) 申告があれば緑（陽性対照——12 の赤が申告の有無で決まっていることを示す）
    d = fresh(plan=PLAN + "\n依存の追加・更新: あり\n", head_files={"docs/app/package.json": "{}\n"})
    rc, out = run(d, "main")
    got += [("依存の申告があれば rc=0", rc == 0)]
    # 14) `なし` と申告して足したら赤
    d = fresh(plan=PLAN + "\n依存の追加・更新: なし\n", head_files={"docs/app/uv.lock": "x\n"})
    rc, out = run(d, "main")
    got += [("`なし` と申告して依存のファイルを触ったら rc=1", rc == 1)]
    # 15) 計画が無い PR は、依存のファイルがあっても今までどおり「判定していない」
    d = fresh(plan=None, head_files={"package.json": "{}\n"})
    rc, out = run(d, "main")
    got += [("計画が無ければ依存のファイルがあっても rc=0（判定していない）", rc == 0 and "判定していない" in out)]

    return got


MUTANTS = {
    "外に出たファイルを数えない": ("        if f != rel and not covered(f, patterns)\n",
                                   "        if False\n"),
    "常に覆われていると答える": ("    for pat in patterns:\n",
                                 "    return True\n    for pat in patterns:\n"),
    "外があっても 0 を返す": ("        failed = True\n    else:\n",
                              "        failed = False\n    else:\n"),
    "節が読めなくても通す": ('            "  バッククォートで囲んだパターンの箇条書きを置く（SKILL.md 手順 3 を正とする）。"\n        )\n        return 1\n',
                             '            "  バッククォートで囲んだパターンの箇条書きを置く（SKILL.md 手順 3 を正とする）。"\n        )\n        return 0\n'),
    "計画が無いときに黙る": ('    plan = find_plan(opts.plan)\n',
                            '    plan = find_plan(opts.plan) or Path("/nonexistent")\n'),
    "detached で環境変数を見ない": (
        '    for env in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):\n',
        '    for env in ():\n'),
    "GITHUB_REF_NAME の HEAD を名前として使う": (
        '        if v and v != "HEAD":\n', "        if v:\n"),
    "git が返す HEAD を名前として使う": (
        '    return "" if name == "HEAD" else name\n', "    return name\n"),
    "計画ファイル自身も外として数える": ("        if f != rel and not covered(f, patterns)\n",
                                        "        if not covered(f, patterns)\n"),
    # 依存の申告（#996）
    "依存の判定を当てない": ("    code, deps, reason = deps_module().judge(files, plan.read_text())\n",
                            '    code, deps, reason = 0, [], ""\n'),
    "依存の判定が赤でも通す": ("        failed = True\n    return 1 if failed else 0\n",
                              "        pass\n    return 1 if failed else 0\n"),
}

# 判定の式をプラグインの本体から読み込んでいること（写していないこと）を、本体のほうを壊して見る（#996 の D6）
DEPS_MUTANTS = {
    "本体の宣言の値を見ない": ('    if values[0] != "あり":\n', "    if False:\n"),
    "本体が依存のファイルを 1 つも見つけない": ("    deps = dependency_files(paths)\n", "    deps = []\n"),
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        print("契約（本体そのまま——全部通らなければならない）:")
        for name, ok in contract(root / "real", "r"):
            check(name, ok)

        print("変異（1 箇所ずつ壊す——契約が破れなければ失格）:")
        src = SCRIPT.read_text()
        for i, (name, (old, new)) in enumerate(MUTANTS.items()):
            if src.count(old) != 1:
                check(f"変異 `{name}` の当て先が 1 箇所", False)
                continue
            broken = [
                n for n, ok in contract(root / f"m{i}", f"m{i}", src.replace(old, new))
                if not ok
            ]
            check(f"変異 `{name}` を契約が捕まえる", bool(broken))
            if not broken:
                print("       壊したのに契約が全部通った")

        print("依存の判定の本体の変異（check-plan-scope.py が本体を読み込んでいるか）:")
        deps_src = DEPS_SCRIPT.read_text()
        for i, (name, (old, new)) in enumerate(DEPS_MUTANTS.items()):
            if deps_src.count(old) != 1:
                check(f"変異 `{name}` の当て先が 1 箇所", False)
                continue
            broken = [
                n for n, ok in contract(root / f"d{i}", f"d{i}", deps_text=deps_src.replace(old, new))
                if not ok
            ]
            check(f"変異 `{name}` を契約が捕まえる", bool(broken))
    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


if __name__ == "__main__":
    sys.exit(main())
