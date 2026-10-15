#!/usr/bin/env python3
"""scripts/check-version-bump.py の回帰テスト。

    python3 scripts/test-check-version-bump.py

なぜ必要か（#253）: このチェッカーは**「版が変わったか」だけを見ていて、「上がったか」を
見ていなかった**。#210 の周（PR #252）で、作業中に別の PR が main の `dev-loop` を 1.38.4 に
上げ、ブランチは 1.38.3 のままだった——出力は `version 1.38.4 -> 1.38.3。OK`。
**それまでテストが 1 本も無かった**ので、ここに固定する。

**このテストは実環境を触らない。** 毎回テンポラリに使い捨ての git リポジトリを作り、
そこだけを対象にする。実リポジトリの内側を対象にしてしまうテストは**実行前にアサートで落とす**
（`test-check-description-sync.py` と同じ方針）。

判定する 3 つ:

  (i)   版が**下がった**差分が落ちる（本件。base の先端が先に進んだ形を含む）
  (ii)  版が上がった差分は通る。**比較は数値**——`1.38.9 -> 1.38.10` を後退と読まない
  (iii) 比較できない版を黙って通さない

**変異テスト**: 本体の写しに変異を入れ、上のケースのどれかが赤になることを確かめる。
陽性対照（変異の前に全ケースが緑であること）を先に見る——**緑のまま走らなかった変異を
「届いていない」と読まないため、置換対象が本体に 1 回だけ在ることもアサートする。**

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-version-bump.py"

def real_repo_roots() -> list[Path]:
    """実リポジトリの作業ツリー。ここを対象にしてしまうテストは実行前に落とす。

    **worktree から走らせると `REPO_ROOT` は worktree を指す**ので、それだけでは
    メインの作業ツリーの内側を通してしまう。共有の `.git` の親も加える。
    """
    roots = [REPO_ROOT.resolve()]
    proc = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        main_root = Path(proc.stdout.strip()).resolve().parent
        if main_root not in roots:
            roots.append(main_root)
    return roots


REAL_REPOS = real_repo_roots()

failures: list[str] = []
checks = 0


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def git(cwd: Path, *args: str) -> None:
    proc = run("git", *args, cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} が失敗: {proc.stderr}")


def assert_outside_real_repo(root: Path) -> None:
    """テストの作業先が実リポジトリでないことを、実行前に構造で担保する。"""
    resolved = root.resolve()
    for real in REAL_REPOS:
        assert resolved != real, "テストが実リポジトリを対象にしている"
        assert not str(resolved).startswith(str(real) + os.sep), (
            "テストの作業ディレクトリが実リポジトリの内側にある"
        )


def set_version(root: Path, version: object, plugin: str = "demo") -> None:
    manifest = root / "plugins" / plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}), encoding="utf-8")


def touch(root: Path, rel: str, text: str, plugin: str = "demo") -> None:
    path = root / "plugins" / plugin / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-q", "--allow-empty", "-m", message)


def new_repo(tmp: Path, base_version: object) -> Path:
    """`base-ref` に base の版を持つ使い捨てリポジトリを作り、`work` ブランチに立つ。"""
    root = tmp / "repo"
    root.mkdir()
    assert_outside_real_repo(root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "test")
    git(root, "config", "commit.gpgsign", "false")
    # 後片付けの最中に .git へ書き込む切り離しの処理を起こさない（CI で rmtree が落ちた。#253）
    git(root, "config", "gc.auto", "0")
    git(root, "config", "maintenance.auto", "false")
    set_version(root, base_version)
    touch(root, "skills/demo/SKILL.md", "old\n")
    touch(root, "README.md", "old\n")
    commit(root, "base")
    git(root, "branch", "-q", "base-ref")
    git(root, "checkout", "-q", "-b", "work")
    return root


# ケース: (名前, 組み立て, 期待する終了コードが 0 か, 出力に含むべき語)
Case = tuple[str, Callable[[Path], Path], bool, str]


def own_downgrade(tmp: Path) -> Path:
    """ブランチが自分で版を下げた。"""
    root = new_repo(tmp, "1.38.4")
    set_version(root, "1.38.3")
    touch(root, "skills/demo/SKILL.md", "new\n")
    commit(root, "下げる")
    return root


def base_moved_ahead(tmp: Path) -> Path:
    """本件（#252）: ブランチは 1.38.2 -> 1.38.3、そのあいだに base が 1.38.4 へ進んだ。"""
    root = new_repo(tmp, "1.38.2")
    set_version(root, "1.38.3")
    touch(root, "skills/demo/SKILL.md", "new\n")
    commit(root, "このブランチの bump")
    git(root, "checkout", "-q", "base-ref")
    set_version(root, "1.38.4")
    touch(root, "agents/x.md", "other\n")
    commit(root, "別の PR が先に上げた")
    git(root, "checkout", "-q", "work")
    return root


def major_downgrade(tmp: Path) -> Path:
    root = new_repo(tmp, "2.0.0")
    set_version(root, "1.99.99")
    commit(root, "major を下げる")
    return root


def patch_two_digits(tmp: Path) -> Path:
    """文字列比較なら "1.38.10" < "1.38.9" で後退に見える。"""
    root = new_repo(tmp, "1.38.9")
    set_version(root, "1.38.10")
    touch(root, "skills/demo/SKILL.md", "new\n")
    commit(root, "patch を 2 桁へ")
    return root


def minor_two_digits(tmp: Path) -> Path:
    root = new_repo(tmp, "1.9.0")
    set_version(root, "1.10.0")
    touch(root, "skills/demo/SKILL.md", "new\n")
    commit(root, "minor を 2 桁へ")
    return root


def same_version_significant(tmp: Path) -> Path:
    root = new_repo(tmp, "1.0.0")
    touch(root, "skills/demo/SKILL.md", "new\n")
    commit(root, "中身だけ")
    return root


def same_version_readme(tmp: Path) -> Path:
    root = new_repo(tmp, "1.0.0")
    touch(root, "README.md", "new\n")
    commit(root, "README だけ")
    return root


def unparsable_head(tmp: Path) -> Path:
    root = new_repo(tmp, "1.38.4")
    set_version(root, "1.38")
    touch(root, "skills/demo/SKILL.md", "new\n")
    commit(root, "版を壊す")
    return root


def unparsable_both_same(tmp: Path) -> Path:
    """両側が同じ壊れた文字列でも、「同じ」として従来判定に流さない。"""
    root = new_repo(tmp, "v1")
    touch(root, "README.md", "new\n")
    commit(root, "README だけ")
    return root


def fullwidth_digit(tmp: Path) -> Path:
    """全角の数字は X.Y.Z ではない（`\\d` は Unicode の数字にも当たる）。"""
    root = new_repo(tmp, "1.0.0")
    set_version(root, "\uff11.0.1")
    touch(root, "skills/demo/SKILL.md", "new\n")
    commit(root, "全角の版")
    return root


def non_string_version(tmp: Path) -> Path:
    root = new_repo(tmp, "1.0.0")
    set_version(root, 2)
    commit(root, "数値の版")
    return root


def break_base_manifest(tmp: Path, text: str) -> Path:
    """base の plugin.json は在るが、版が読めない形に書き換える。"""
    root = new_repo(tmp, "1.0.0")
    git(root, "checkout", "-q", "base-ref")
    manifest = root / "plugins" / "demo" / ".claude-plugin" / "plugin.json"
    manifest.write_text(text, encoding="utf-8")
    commit(root, "base の plugin.json を壊す")
    git(root, "checkout", "-q", "work")
    set_version(root, "0.0.1")
    touch(root, "skills/demo/SKILL.md", "new\n")
    commit(root, "版を付ける")
    return root


def base_without_version(tmp: Path) -> Path:
    """base に plugin.json は在るが version が無い。新規プラグインと読まない。"""
    return break_base_manifest(tmp, json.dumps({"name": "demo"}))


def base_broken_json(tmp: Path) -> Path:
    """base の plugin.json が JSON として読めない。新規プラグインと読まない。"""
    return break_base_manifest(tmp, '{"name": "demo",')


def new_plugin(tmp: Path) -> Path:
    root = new_repo(tmp, "1.0.0")
    set_version(root, "0.0.1", plugin="fresh")
    commit(root, "新規プラグイン")
    return root


CASES: list[Case] = [
    ("自分で版を下げた", own_downgrade, False, "下がっている"),
    ("base が先に進んで版が後退する（#252）", base_moved_ahead, False, "下がっている"),
    ("major を下げた", major_downgrade, False, "下がっている"),
    ("1.38.9 -> 1.38.10", patch_two_digits, True, "1.38.9 -> 1.38.10。OK"),
    ("1.9.0 -> 1.10.0", minor_two_digits, True, "1.9.0 -> 1.10.0。OK"),
    ("版を据え置いて中身を変えた", same_version_significant, False, "のまま"),
    ("版を据え置いて README だけ", same_version_readme, True, "::warning::"),
    ("head の版が X.Y.Z でない", unparsable_head, False, "比較できない"),
    ("両側とも同じ壊れた版", unparsable_both_same, False, "比較できない"),
    ("版に全角の数字", fullwidth_digit, False, "比較できない"),
    ("版が文字列でない", non_string_version, False, "比較できない"),
    ("base の plugin.json に version が無い", base_without_version, False, "比較できない"),
    ("base の plugin.json が壊れている", base_broken_json, False, "読めない"),
    ("新規プラグイン", new_plugin, True, "新規プラグイン"),
]


def run_cases(script: Path) -> list[str]:
    """全ケースを回し、期待と違ったケースの説明を返す。"""
    wrong: list[str] = []
    for name, build, want_ok, needle in CASES:
        with tempfile.TemporaryDirectory(prefix="version-bump-test-", ignore_cleanup_errors=True) as tmp:
            root = build(Path(tmp))
            proc = run(sys.executable, str(script), "base-ref", cwd=root)
        out = proc.stdout + proc.stderr
        if (proc.returncode == 0) != want_ok:
            wrong.append(f"{name}: 終了コード {proc.returncode}\n{out}")
        elif needle not in out:
            wrong.append(f"{name}: 出力に「{needle}」が無い\n{out}")
    return wrong


# 変異: (名前, [(置換前, 置換後), ...])。置換前は本体に 1 回だけ在ること。
MUTATIONS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "旧い判定に戻す（変わったら OK）",
        [
            ("if head_key < base_key:", "if False:"),
            ("if head_key > base_key:", "if head_key != base_key:"),
        ],
    ),
    ("後退の判定を外す", [("if head_key < base_key:", "if False:")]),
    (
        "文字列のまま比べる",
        [
            ("base_key = parse_version(base_version)", "base_key = base_version"),
            ("head_key = parse_version(head_version)", "head_key = head_version"),
        ],
    ),
    (
        "比較できない版の検査を外す",
        [("if base_key is None or head_key is None:", "if False:")],
    ),
    (
        "版の読めない base を新規プラグイン扱いに戻す",
        [
            (
                "if base_manifest is None:",
                "if base_manifest is None or version_in(base_manifest)[1] is None:",
            )
        ],
    ),
    (
        "数字を Unicode の数字まで広げる",
        [(r'r"([0-9]+)\.([0-9]+)\.([0-9]+)"', r'r"(\d+)\.(\d+)\.(\d+)"')],
    ),
]


def check(condition: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def guard_rejects(path: Path) -> bool:
    try:
        assert_outside_real_repo(path)
    except AssertionError:
        return True
    return False


def main() -> int:
    # ガード自体: どの実作業ツリー（worktree から走らせたときのメインを含む）の内側も通さない。
    # パスを作らずに述語だけ当てる
    for real in REAL_REPOS:
        check(guard_rejects(real / "version-bump-probe"), f"ガードが {real} の内側を通す")
    check(not guard_rejects(Path(tempfile.gettempdir()) / "version-bump-probe"), "ガードが一時ディレクトリまで拒む")

    # 陽性対照: 本物の本体で全ケースが期待どおり
    wrong = run_cases(SCRIPT)
    check(not wrong, "本体で期待と違うケースがある", "\n".join(wrong))

    source = SCRIPT.read_text(encoding="utf-8")
    for name, replacements in MUTATIONS:
        mutated = source
        reached = True
        for old, new in replacements:
            count = mutated.count(old)
            check(count == 1, f"変異「{name}」の置換対象が本体に 1 回だけ無い（{count} 回）", old)
            if count != 1:
                reached = False
                break
            mutated = mutated.replace(old, new)
        if not reached:
            continue
        with tempfile.TemporaryDirectory(prefix="version-bump-mut-", ignore_cleanup_errors=True) as tmp:
            path = Path(tmp) / "check-version-bump.py"
            path.write_text(mutated, encoding="utf-8")
            killed = run_cases(path)
        check(bool(killed), f"変異「{name}」を入れても全ケースが緑のまま")

    if failures:
        print(f"{len(failures)} 件の失敗（{checks} 判定）:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"check-version-bump.py のテスト: 全 {checks} 判定に合格（ケース {len(CASES)}・変異 {len(MUTATIONS)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
