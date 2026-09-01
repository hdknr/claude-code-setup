#!/usr/bin/env python3
"""scripts/check-description-sync.py の回帰テスト。

    python3 scripts/test-check-description-sync.py

なぜ必要か（#62）: 歯止めは**わざとずらしたときに落ちること**を確かめないと、
「置いてあるが何も見ていない」状態に静かに退化する。#59 / PR #60 の周では、
description の同期漏れが**向きを変えて 2 回**すり抜けた。その 2 件をテストとして固定する。

**このテストは実環境を触らない。** 毎回テンポラリに使い捨ての git リポジトリを作り、
そこだけを対象にする。実リポジトリを対象にしてしまうテストは**実行前にアサートで落とす**
（`test-link-skills.py` と同じ設計方針——#56 で「実環境を触るな」という指示が破られた実績があるので、
指示ではなく構造で不可能にする）。

判定する 3 条件:

  (i)   片側だけ変えた差分が**落ちる**（見逃さない）
  (ii)  全部変えた／何も変えていない差分が**通る**（誤検知しない）
  (iii) 失敗が黙って通らない（終了コードが非 0、メッセージが出る）

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-description-sync.py"

# 実リポジトリ。ここを対象にしてしまうテストは実行前に落とす。
REAL_REPO = REPO_ROOT.resolve()

failures: list[str] = []
checks = 0


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, check=False
    )


def git(cwd: Path, *args: str) -> None:
    proc = run("git", *args, cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} が失敗: {proc.stderr}")


def check(condition: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def skill_md(description: str) -> str:
    return f"""---
name: demo
description: {description}
---

# demo skill
"""


def marketplace(description: str) -> str:
    return json.dumps(
        {
            "name": "test-catalog",
            "owner": {"name": "tester"},
            "plugins": [
                {
                    "name": "demo",
                    "source": "./plugins/demo",
                    "version": "1.0.0",
                    "description": description,
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


def manifest(description: str) -> str:
    return json.dumps(
        {"name": "demo", "version": "1.0.0", "description": description},
        ensure_ascii=False,
        indent=2,
    )


def write(root: Path, catalog: str, plugin: str, skill: str) -> None:
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(catalog, encoding="utf-8")
    manifest_dir = root / "plugins" / "demo" / ".claude-plugin"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "plugin.json").write_text(plugin, encoding="utf-8")
    skill_dir = root / "plugins" / "demo" / "skills" / "demo"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(skill, encoding="utf-8")


def make_repo(root: Path) -> None:
    """base コミット（3 スロットとも "old"）を持つ使い捨てリポジトリを作る。"""
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの作業ディレクトリが実リポジトリの内側にある"
    )

    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "test")
    write(root, marketplace("old catalog"), manifest("old catalog"), skill_md("old skill"))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    git(root, "branch", "-q", "base-ref")


def commit_case(
    root: Path,
    *,
    catalog: str,
    plugin: str,
    skill: str,
    message: str = "change",
) -> subprocess.CompletedProcess[str]:
    """base から作業ブランチを切り直して 1 コミットし、チェッカーを走らせる。"""
    git(root, "checkout", "-q", "-B", "work", "base-ref")
    write(root, marketplace(catalog), manifest(plugin), skill_md(skill))
    git(root, "add", "-A")
    # 「description を変えていない」ケースは差分ゼロになるので空コミットを許す
    git(root, "commit", "-q", "--allow-empty", "-m", message)
    return run(sys.executable, str(SCRIPT), "base-ref", cwd=root)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="desc-sync-test-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_repo(root)

        # (ii) 何も変えていない → 通る
        proc = commit_case(
            root, catalog="old catalog", plugin="old catalog", skill="old skill",
            message="無関係な変更",
        )
        check(proc.returncode == 0, "description 未変更で落ちた", proc.stdout + proc.stderr)

        # (ii) 3 スロットとも変えた → 通る
        proc = commit_case(
            root, catalog="new catalog", plugin="new catalog", skill="new skill"
        )
        check(proc.returncode == 0, "3 箇所すべて更新したのに落ちた", proc.stdout + proc.stderr)

        # (i) #60 の 1 件目: frontmatter だけ直して JSON が残る
        proc = commit_case(
            root, catalog="old catalog", plugin="old catalog", skill="new skill"
        )
        check(proc.returncode != 0, "frontmatter だけ変えたのに通った（#60 の 1 件目）")
        check(
            "SKILL.md" in proc.stdout and "plugin.json" in proc.stdout,
            "どのスロットが取り残されたかが出ていない",
            proc.stdout,
        )

        # (i) #60 の 2 件目: JSON 2 つを直して frontmatter が残る
        proc = commit_case(
            root, catalog="new catalog", plugin="new catalog", skill="old skill"
        )
        check(proc.returncode != 0, "JSON だけ変えたのに通った（#60 の 2 件目）")

        # (i) marketplace だけ / plugin.json だけ
        proc = commit_case(
            root, catalog="new catalog", plugin="old catalog", skill="old skill"
        )
        check(proc.returncode != 0, "marketplace だけ変えたのに通った")
        proc = commit_case(
            root, catalog="old catalog", plugin="new catalog", skill="old skill"
        )
        check(proc.returncode != 0, "plugin.json だけ変えたのに通った")

        # 逃げ道: 理由つきの trailer があれば通る
        proc = commit_case(
            root,
            catalog="new catalog",
            plugin="old catalog",
            skill="old skill",
            message="typo 修正\n\nSkip-description-sync: カタログの typo のみ",
        )
        check(proc.returncode == 0, "trailer を書いたのに落ちた", proc.stdout + proc.stderr)

        # 逃げ道: 理由が無ければ効かない
        proc = commit_case(
            root,
            catalog="new catalog",
            plugin="old catalog",
            skill="old skill",
            message="typo 修正\n\nSkip-description-sync:",
        )
        check(proc.returncode != 0, "理由の無い trailer で素通りした")

        # fail-closed: frontmatter が壊れていたらエラーにする（黙って対象外にしない）
        git(root, "checkout", "-q", "-B", "work", "base-ref")
        write(root, marketplace("new catalog"), manifest("new catalog"), "frontmatter なし\n")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "壊れた frontmatter")
        proc = run(sys.executable, str(SCRIPT), "base-ref", cwd=root)
        check(proc.returncode != 0, "frontmatter を読めないのに通った（fail-open）")
        check("読めない" in proc.stdout, "読めない旨のメッセージが出ていない", proc.stdout)

        # base ref が解決できない場合は、黙って 0 を返さない
        proc = run(sys.executable, str(SCRIPT), "no-such-ref", cwd=root)
        check(proc.returncode != 0, "解決できない base ref で 0 を返した")

    if failures:
        print(f"{len(failures)} 件の失敗（{checks} 判定）:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"check-description-sync.py のテスト: 全 {checks} 判定に合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
