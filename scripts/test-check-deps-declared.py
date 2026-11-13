#!/usr/bin/env python3
"""`check-deps-declared.py` の回帰テスト（#996）。

    python3 scripts/test-check-deps-declared.py

**本体はプラグインの中にある**（`plugins/dev-loop/skills/dev-loop/scripts/`）——`test-find-cycle.py` と同じ形で、
**`dev-loop` はどのリポジトリでも使えるスキル**なので。

**このテストは実環境を触らない。** 毎回テンポラリに偽のリポジトリを作り、そこだけを対象にする（`assert_not_real_repo`）。

**変異テストを含む。** 本体の docstring の「守る」の各行に変異を 1 つ以上当て、**壊したのに契約が保たれるなら失格**とする。
**変異の前に、元の本体で全部緑であること（陽性対照）を見る。**

あわせて、**Verifier の委譲文（`prompts/verifier.md`）の依存の差し込みが、表の欄を全部名指していること**と、
**`references/dependencies.md` が未検証の扱いを持つこと**を見る（受入基準 V1・V2）——欄を 1 つ落とすと赤。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REAL_REPO / "plugins" / "dev-loop" / "skills" / "dev-loop"
SCRIPT = SKILL_DIR / "scripts" / "check-deps-declared.py"
VERIFIER = SKILL_DIR / "prompts" / "verifier.md"
DEPS_DOC = SKILL_DIR / "references" / "dependencies.md"
# Verifier の表の欄（`prompts/verifier.md` が正。Issue #996 の受入基準 2 の 5 つと、名前の近い包）
TABLE_COLUMNS = ("名前", "版", "公開日", "公開者", "インストールスクリプト", "名前の近い")

failures: list[str] = []

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
                          check=True, capture_output=True, text=True).stdout


def repo(root: Path, *, plan: str | None = PLAN, branch: str = "issue/7-demo",
         base_files: dict[str, str] | None = None) -> str:
    """偽のリポジトリを作り、base の SHA を返す。計画ファイルは base の後のコミットに置く（周の形）。"""
    assert_not_real_repo(root)
    root.mkdir(parents=True)
    git(root, "init", "-q", "-b", "main")
    files = {"seed.txt": "seed\n", **(base_files or {})}
    for rel, body in files.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD").strip()
    git(root, "switch", "-q", "-c", branch)
    if plan is not None:
        p = root / "docs" / "plans" / "issue-7.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(plan)
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "plan")
    return base


def put(root: Path, rel: str, body: str = "x\n", commit: bool = False) -> None:
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(body)
    if commit:
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "work")


def run(script: Path, root: Path, *args: str, env: dict | None = None) -> tuple[int, str]:
    e = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    e.pop("GITHUB_HEAD_REF", None)
    e.pop("GITHUB_REF_NAME", None)
    e.update(env or {})
    proc = subprocess.run([sys.executable, str(script), *args], cwd=root, env=e,
                          capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def contract(script: Path, tmp: Path, tag: str) -> list[tuple[str, bool]]:
    got: list[tuple[str, bool]] = []
    n = [0]

    def fresh(**kw) -> tuple[Path, str]:
        n[0] += 1
        d = tmp / f"{tag}{n[0]}"
        return d, repo(d, **kw)

    # 1) コミットした package.json・宣言なし → 1、名指す
    d, base = fresh()
    put(d, "package.json", "{}\n", commit=True)
    rc, out = run(script, d, base)
    got += [("申告せずに足した依存のファイルで 1", rc == 1),
            ("依存のファイルを名指す", "package.json" in out),
            ("申告の書き方を案内する", "依存の追加・更新: あり" in out)]

    # 2) 宣言 `あり` → 0（陽性対照）
    d, base = fresh(plan=PLAN + "\n依存の追加・更新: あり\n")
    put(d, "package.json", "{}\n", commit=True)
    rc, out = run(script, d, base)
    got += [("宣言が `あり` なら 0", rc == 0), ("`あり` なら Verifier の表を案内する", "Verifier" in out)]

    # 3) 箇条書きの宣言も数える
    d, base = fresh(plan=PLAN + "\n- 依存の追加・更新: あり\n")
    put(d, "package.json", "{}\n", commit=True)
    rc, _ = run(script, d, base)
    got += [("箇条書きの `- 依存の追加・更新: あり` も宣言", rc == 0)]

    # 4) `なし`・別の値・2 本以上・フェンスの中だけ → 1
    for label, extra in (("`なし`", "\n依存の追加・更新: なし\n"),
                         ("別の値", "\n依存の追加・更新: あり（予定）\n"),
                         ("2 本以上", "\n依存の追加・更新: あり\n依存の追加・更新: あり\n"),
                         ("フェンスの中だけ", "\n```text\n依存の追加・更新: あり\n```\n")):
        d, base = fresh(plan=PLAN + extra)
        put(d, "uv.lock", commit=True)
        rc, _ = run(script, d, base)
        got += [(f"宣言が{label}なら 1", rc == 1)]

    # 5) 未コミットの変更（追跡しているファイル）・未追跡・下の階層・消した・取得経路の設定 → 1
    d, base = fresh(base_files={"web/app/package.json": "{}\n"})
    put(d, "web/app/package.json", '{"dependencies": {"a": "1"}}\n')  # コミットしない
    rc, out = run(script, d, base)
    got += [("未コミットの変更（下の階層の package.json）で 1", rc == 1 and "web/app/package.json" in out)]

    d, base = fresh()
    put(d, "svc/requirements-dev.txt")  # 未追跡のまま
    rc, out = run(script, d, base)
    got += [("未追跡の requirements-dev.txt で 1", rc == 1 and "svc/requirements-dev.txt" in out)]

    d, base = fresh(base_files={"yarn.lock": "x\n"})
    (d / "yarn.lock").unlink()
    git(d, "add", "-A")
    git(d, "commit", "-q", "-m", "rm")
    rc, out = run(script, d, base)
    got += [("消した yarn.lock で 1", rc == 1 and "yarn.lock" in out)]

    d, base = fresh()
    put(d, "サービス/package.json", "{}\n", commit=True)
    rc, out = run(script, d, base)
    got += [("非 ASCII の名前のディレクトリの下の package.json で 1", rc == 1 and "サービス/package.json" in out)]

    d, base = fresh()
    put(d, ".npmrc", "registry=https://example.invalid/\n", commit=True)
    rc, _ = run(script, d, base)
    got += [("取得経路の設定（.npmrc）を触ったら 1", rc == 1)]

    # 6) 依存のファイルが無い → 宣言の有無に依らず 0
    d, base = fresh()
    put(d, "src/a.py", commit=True)
    rc, _ = run(script, d, base)
    got += [("依存のファイルが無ければ、宣言が無くても 0", rc == 0)]

    # 7) 計画が見つからない: 依存のファイルがあれば 2、無ければ 0
    d, base = fresh(plan=None, branch="feature/x")
    put(d, "go.mod", commit=True)
    rc, out = run(script, d, base)
    got += [("計画が見つからず依存のファイルがあれば 2", rc == 2 and "緑ではない" in out)]
    d, base = fresh(plan=None, branch="feature/x")
    put(d, "src/a.py", commit=True)
    rc, _ = run(script, d, base)
    got += [("計画が見つからず依存のファイルも無ければ 0", rc == 0)]

    # 8) --plan で名指す・detached でも GITHUB_HEAD_REF から当てる
    d, base = fresh(branch="feature/x", plan=None)
    put(d, "notes/plan.md", PLAN + "\n依存の追加・更新: あり\n")
    put(d, "Cargo.lock", commit=True)
    rc, _ = run(script, d, base, "--plan", "notes/plan.md")
    got += [("--plan で名指した計画の宣言を読む", rc == 0)]
    d, base = fresh()
    put(d, "Gemfile.lock", commit=True)
    git(d, "switch", "-q", "--detach", "HEAD")
    rc, out = run(script, d, base, env={"GITHUB_HEAD_REF": "issue/7-demo"})
    got += [("detached でも GITHUB_HEAD_REF から計画を当てる", rc == 1 and "issue-7.md" in out)]

    # 9) git が失敗（存在しない base）→ 2
    d, base = fresh()
    rc, out = run(script, d, "no-such-ref")
    got += [("git が失敗したら 2", rc == 2)]

    return got


MUTATIONS = {
    # 守る: 宣言が `あり` でない限り 0 にしない
    "宣言の値を見ない": ('    if values[0] != "あり":\n', "    if False:\n"),
    "2 本以上を通す": ("    if len(values) > 1:\n", "    if False:\n"),
    "フェンスの中も数える": ("        if fence is not None:\n            continue\n", ""),
    "箇条書きの宣言を数えない": (r'DECLARE = re.compile(r"^(?:[-*]\s+)?依存の追加・更新:\s*(.*?)\s*$")',
                                 r'DECLARE = re.compile(r"^依存の追加・更新:\s*(.*?)\s*$")'),
    # 守る: 計画が見つからないとき、依存のファイルがあれば 0 にしない
    "計画が見つからなければ 0": ('        return 2, deps, "依存のファイルが差分にあるのに',
                                '        return 0, deps, "依存のファイルが差分にあるのに'),
    "git の失敗を 0 にする": ('        print(f"git で差分を取れなかった（base: {opts.base}）——判定していない（緑ではない）。")\n        return 2\n',
                             '        return 0\n'),
    # 守る: 未コミット・未追跡・消した・下の階層を落とさない
    "未追跡を見ない": ("    return [line for line in (diff + untracked).splitlines() if line.strip()]\n",
                       "    return [line for line in diff.splitlines() if line.strip()]\n"),
    "3 点で取る（未コミットを見ない）": ('    rc1, diff = git("diff", "--name-only", "--no-renames", base)\n',
                                       '    rc1, diff = git("diff", "--name-only", "--no-renames", f"{base}...HEAD")\n'),
    "非 ASCII のパスを引用符で包ませる": ('["git", "-c", "core.quotePath=false", *args]', '["git", *args]'),
    "下の階層を見ない": ('    name = path.rsplit("/", 1)[-1]\n', "    name = path\n"),
    "消したファイルを見ない": ('    rc1, diff = git("diff", "--name-only", "--no-renames", base)\n',
                              '    rc1, diff = git("diff", "--name-only", "--no-renames", "--diff-filter=d", base)\n'),
    # 守る: 依存のファイルが無ければ 0
    "依存のファイルが無くても宣言を求める": ("    if not deps:\n        return 0, deps,", "    if False:\n        return 0, deps,"),
}


def static_checks() -> None:
    print("委譲文と規定（V1・V2）:")
    text = VERIFIER.read_text(encoding="utf-8")
    start = text.find("依存を追加・更新する周なら")
    section = text[start:start + 3000] if start >= 0 else ""
    check("verifier.md に依存の差し込みがある", bool(section))
    header = next((ln for ln in section.splitlines() if ln.strip().startswith("| 名前")), "")
    cells = [c.strip() for c in header.strip().strip("|").split("|")]
    for col in TABLE_COLUMNS:
        check(f"依存の差し込みの表の見出しの行が欄「{col}」を持つ", any(c.startswith(col) for c in cells))
    check("依存の差し込みが包を入れないよう言う", "入れないで" in section)
    doc = DEPS_DOC.read_text(encoding="utf-8")
    check("dependencies.md が未検証の扱いを持つ", "未検証" in doc)
    check("dependencies.md が宣言の行を書く", "依存の追加・更新: あり" in doc)


def main() -> int:
    static_checks()
    src = SCRIPT.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
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
            broken = [n for n, ok in contract(mutant, root / f"m{i}", f"m{i}") if not ok]
            check(f"変異 `{name}` を契約が捕まえる", bool(broken))
    if failures:
        print(f"\n{len(failures)} 件失敗: {failures}")
        return 1
    print("\nすべて通った")
    return 0


if __name__ == "__main__":
    sys.exit(main())
