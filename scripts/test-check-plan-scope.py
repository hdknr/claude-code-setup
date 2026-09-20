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
          script_text: str | None = None) -> Path:
    """偽リポジトリを作り、base（main）と HEAD を持たせる。scripts/ の場所を返す。"""
    assert_not_real_repo(root)
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    (root / "seed.txt").write_text("seed\n")
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


def run(root: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "check-plan-scope.py"), *args],
        capture_output=True, text=True, check=False, cwd=root,
    )
    return proc.returncode, proc.stdout + proc.stderr


# ------------------------------------------------------------------- 契約
def contract(tmp: Path, tag: str, script_text: str | None = None) -> list[tuple[str, bool]]:
    got: list[tuple[str, bool]] = []
    i = [0]

    def fresh(**kw) -> Path:
        i[0] += 1
        d = tmp / f"{tag}{i[0]}"
        build(d, script_text=script_text, **kw)
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

    return got


MUTANTS = {
    "外に出たファイルを数えない": ("        if f != rel and not covered(f, patterns)\n",
                                   "        if False\n"),
    "常に覆われていると答える": ("    for pat in patterns:\n",
                                 "    return True\n    for pat in patterns:\n"),
    "外があっても 0 を返す": ('        return 1\n    print("差分はすべて変更範囲の中にある。")\n',
                              '        return 0\n    print("差分はすべて変更範囲の中にある。")\n'),
    "節が読めなくても通す": ('            "  バッククォートで囲んだパターンの箇条書きを置く（SKILL.md 手順 3 を正とする）。"\n        )\n        return 1\n',
                             '            "  バッククォートで囲んだパターンの箇条書きを置く（SKILL.md 手順 3 を正とする）。"\n        )\n        return 0\n'),
    "計画が無いときに黙る": ('    plan = find_plan(files, opts.plan)\n',
                            '    plan = find_plan(files, opts.plan) or Path("/nonexistent")\n'),
    "差分の別計画で代用する": ('        return None  # 番号は名乗っている。差分で代用しない\n', "        pass\n"),
    "計画ファイル自身も外として数える": ("        if f != rel and not covered(f, patterns)\n",
                                        "        if not covered(f, patterns)\n"),
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
    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


if __name__ == "__main__":
    sys.exit(main())
