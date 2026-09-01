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

初版のテストは**単一スキルのプラグイン 1 つ**しか作っておらず、計画で固定すると約束した
分岐（スキル無し・複数スキル・新規プラグイン）を実際にはテストしていなかった。
さらに検証で、**読めないものを黙って対象外にする**形の抜け道が 4 つ見つかった。
どちらも「テストが通っている」ことを根拠にしていたら気づけなかったので、ここに固定する。

標準ライブラリのみ。
"""

from __future__ import annotations

import json
import os
import shutil
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


def assert_outside_real_repo(root: Path) -> None:
    """テストの作業先が実リポジトリでないことを、実行前に構造で担保する。

    `test-link-skills.py` と同じ方針。#56 で「実環境を触るな」という指示が破られた実績が
    あるので、方針を書くだけにしない。
    """
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの作業ディレクトリが実リポジトリの内側にある"
    )


def folded_skill(description: str, name: str = "skill0") -> str:
    """`>` 折り畳みブロックの SKILL.md。**dev-loop の実物がこの形**。"""
    return f"""---
name: {name}
description: >
  {description}
---

# {name} skill
"""


def skill_md(description: str, name: str = "demo") -> str:
    return f"""---
name: {name}
description: {description}
---

# {name} skill
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


# スキル名の既定。スキルを複数持つケースでは呼び出し側が名前を渡す。
DEFAULT_SKILLS = ["demo"]


def write(root: Path, catalog: str, plugin: str, skills: list[str]) -> None:
    """カタログ・マニフェスト・各スキルの SKILL.md を書き出す。

    `skills` は SKILL.md の本文そのもののリスト。空リストなら skills/ を作らない
    （スキルを持たないプラグインのケース）。
    """
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(catalog, encoding="utf-8")
    manifest_dir = root / "plugins" / "demo" / ".claude-plugin"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "plugin.json").write_text(plugin, encoding="utf-8")
    for index, body in enumerate(skills):
        skill_dir = root / "plugins" / "demo" / "skills" / f"skill{index}"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")


def make_repo(root: Path, skills: list[str] | None = None) -> None:
    """base コミット（各スロットとも "old"）を持つ使い捨てリポジトリを作る。

    `skills` はスキルの description のリスト。None なら単一スキル。
    空リストならスキルを持たないプラグインになる。
    """
    assert_outside_real_repo(root)

    descriptions = ["old skill"] if skills is None else skills
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "test")
    write(
        root,
        marketplace("old catalog"),
        manifest("old catalog"),
        [skill_md(d, f"skill{i}") for i, d in enumerate(descriptions)],
    )
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    git(root, "branch", "-q", "base-ref")


def commit_case(
    root: Path,
    *,
    catalog: str,
    plugin: str,
    skill: str | None = None,
    skills: list[str] | None = None,
    message: str = "change",
) -> subprocess.CompletedProcess[str]:
    """base から作業ブランチを切り直して 1 コミットし、チェッカーを走らせる。

    `skill` は単一スキルの description（後方互換のための省略形）。
    `skills` を渡すと複数スキル・0 スキルを表現できる。
    """
    descriptions = [skill] if skills is None else skills
    if descriptions == [None]:
        descriptions = []
    return raw_case(
        root,
        catalog=marketplace(catalog),
        plugin=manifest(plugin),
        skill=[skill_md(d, f"skill{i}") for i, d in enumerate(descriptions)],
        message=message,
    )


def raw_case(
    root: Path,
    *,
    catalog: str,
    plugin: str,
    skill: str | list[str],
    message: str = "change",
) -> subprocess.CompletedProcess[str]:
    """ファイルの中身を**そのまま**書いて 1 コミットし、チェッカーを走らせる。

    壊れた JSON やキーの無い JSON など、正規の生成関数では作れない形を試すために使う。
    """
    bodies = [skill] if isinstance(skill, str) else skill
    git(root, "checkout", "-q", "-B", "work", "base-ref")
    write(root, catalog, plugin, bodies)
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
        write(root, marketplace("new catalog"), manifest("new catalog"), ["frontmatter なし\n"])
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "壊れた frontmatter")
        proc = run(sys.executable, str(SCRIPT), "base-ref", cwd=root)
        check(proc.returncode != 0, "frontmatter を読めないのに通った（fail-open）")
        check("読めない" in proc.stdout, "読めない旨のメッセージが出ていない", proc.stdout)

        # base ref が解決できない場合は、黙って 0 を返さない
        proc = run(sys.executable, str(SCRIPT), "no-such-ref", cwd=root)
        check(proc.returncode != 0, "解決できない base ref で 0 を返した")

        # --- 検証で見つかった抜け道（初版はすべてすり抜けていた） ---

        # 抜け道 1: description キーごと削除する
        proc = raw_case(
            root,
            catalog=json.dumps(
                {
                    "name": "test-catalog",
                    "owner": {"name": "tester"},
                    # description キーを持たないエントリ
                    "plugins": [{"name": "demo", "source": "./plugins/demo", "version": "1.0.0"}],
                },
                ensure_ascii=False,
            ),
            plugin=manifest("old catalog"),
            skill=skill_md("old skill"),
        )
        check(proc.returncode != 0, "marketplace の description キー削除がすり抜けた")

        proc = raw_case(
            root,
            catalog=marketplace("old catalog"),
            plugin=json.dumps({"name": "demo", "version": "1.0.0"}, ensure_ascii=False),
            skill=skill_md("old skill"),
        )
        check(proc.returncode != 0, "plugin.json の description キー削除がすり抜けた")

        # 抜け道 2: plugin.json の JSON を壊す（他は正しく更新済み）
        proc = raw_case(
            root,
            catalog=marketplace("new catalog"),
            plugin="{ 壊れた JSON",
            skill=skill_md("new skill"),
        )
        check(proc.returncode != 0, "plugin.json が壊れているのに通った（fail-open）")

        # 抜け道 3: marketplace.json の JSON を壊す（カタログ全体が黙るのが最悪）
        proc = raw_case(
            root,
            catalog="{ 壊れた JSON",
            plugin=manifest("new catalog"),
            skill=skill_md("new skill"),
        )
        check(proc.returncode != 0, "marketplace.json が壊れているのに通った（fail-open）")

        # --- 計画で固定すると約束していたのに、初版が実装していなかった分岐 ---

    # 1-f: スキルを持たないプラグイン（スロットは 2 つ）
    with tempfile.TemporaryDirectory(prefix="desc-sync-noskill-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_repo(root, skills=[])
        proc = commit_case(root, catalog="new catalog", plugin="old catalog", skills=[])
        check(proc.returncode != 0, "スキル無しプラグインで片側だけ変えたのに通った（1-f）")
        proc = commit_case(root, catalog="new catalog", plugin="new catalog", skills=[])
        check(proc.returncode == 0, "スキル無しプラグインで両方変えたのに落ちた（1-f）")

    # 1-g: スキルを複数持つプラグイン（全 frontmatter が対象）
    with tempfile.TemporaryDirectory(prefix="desc-sync-multi-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_repo(root, skills=["one", "two"])
        # base は ["one", "two"]。skill1 だけ据え置くと「1 つ取り残し」になる
        proc = commit_case(
            root, catalog="new catalog", plugin="new catalog", skills=["new one", "two"]
        )
        check(proc.returncode != 0, "2 スキル中 1 つを取り残したのに通った（1-g）")
        proc = commit_case(
            root, catalog="new catalog", plugin="new catalog", skills=["new one", "new two"]
        )
        check(proc.returncode == 0, "全スキルを更新したのに落ちた（1-g）")

    # --- レビューで見つかった「キーの次元」の抜け道 ---

    with tempfile.TemporaryDirectory(prefix="desc-sync-key-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_repo(root)

        # スキルのディレクトリ名を変えると、両側のキーが消えて無検知になっていた
        git(root, "checkout", "-q", "-B", "work", "base-ref")
        shutil.rmtree(root / "plugins" / "demo" / "skills")
        renamed = root / "plugins" / "demo" / "skills" / "renamed"
        renamed.mkdir(parents=True)
        (renamed / "SKILL.md").write_text(skill_md("new skill", "renamed"), encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "スキルを改名して frontmatter だけ変える")
        proc = run(sys.executable, str(SCRIPT), "base-ref", cwd=root)
        check(proc.returncode != 0, "スキル改名＋frontmatter 変更がすり抜けた")

        # trailer は行頭・末尾段落のもののみ有効（引用文で無効化できない）
        proc = commit_case(
            root,
            catalog="new catalog",
            plugin="old catalog",
            skill="old skill",
            message="無関係な変更\n\n以前こう書いた:\n    Skip-description-sync: 昔の理由",
        )
        check(proc.returncode != 0, "引用された trailer でチェックが無効化された")

    # 折り畳みブロックのスキル（dev-loop の実物がこの形。初版はここを一切テストしていなかった）
    with tempfile.TemporaryDirectory(prefix="desc-sync-block-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        assert_outside_real_repo(root)
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "test")
        write(root, marketplace("old catalog"), manifest("old catalog"), [folded_skill("old text")])
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "base")
        git(root, "branch", "-q", "base-ref")

        # 本文だけ変える → 検出される
        proc = raw_case(
            root,
            catalog=marketplace("old catalog"),
            plugin=manifest("old catalog"),
            skill=folded_skill("completely different"),
        )
        check(proc.returncode != 0, "折り畳みブロックの本文変更がすり抜けた")

        # 改行位置だけ変える（意味は同じ）→ 通る
        proc = raw_case(
            root,
            catalog=marketplace("old catalog"),
            plugin=manifest("old catalog"),
            skill="---\nname: skill0\ndescription: >\n  old\n  text\n---\n\nbody\n",
        )
        check(proc.returncode == 0, "折り畳みの改行位置を変えただけで落ちた", proc.stdout)

        # 未知の指示子（`>+`）でも指示子として認識し、値に化けない
        proc = raw_case(
            root,
            catalog=marketplace("old catalog"),
            plugin=manifest("old catalog"),
            skill="---\nname: skill0\ndescription: >+\n  brand new\n---\n\nbody\n",
        )
        check(proc.returncode != 0, "`>+` 指示子の frontmatter 変更がすり抜けた")

        # 同じ行で閉じないクォートは読めないものとして拒否する
        proc = raw_case(
            root,
            catalog=marketplace("new catalog"),
            plugin=manifest("new catalog"),
            skill='---\nname: skill0\ndescription: "first\n  second"\n---\n\nbody\n',
        )
        check(proc.returncode != 0, "閉じないクォートを黙って読んだ（fail-open）")
        check("読めません" in proc.stdout, "読めない旨が出ていない", proc.stdout)

    # カタログの name とディレクトリ名が食い違う場合、source を正とする
    with tempfile.TemporaryDirectory(prefix="desc-sync-src-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        assert_outside_real_repo(root)
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "test")

        def build(catalog_desc: str, manifest_desc: str) -> None:
            (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
            (root / ".claude-plugin" / "marketplace.json").write_text(
                json.dumps(
                    {
                        "name": "test-catalog",
                        "owner": {"name": "tester"},
                        "plugins": [
                            {
                                "name": "demo",
                                "source": "./plugins/other",
                                "version": "1.0.0",
                                "description": catalog_desc,
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            d = root / "plugins" / "other" / ".claude-plugin"
            d.mkdir(parents=True, exist_ok=True)
            (d / "plugin.json").write_text(
                json.dumps(
                    {"name": "demo", "version": "1.0.0", "description": manifest_desc},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

        build("old", "old")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "base")
        git(root, "branch", "-q", "base-ref")
        build("old", "new")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "plugin.json だけ変える")
        proc = run(sys.executable, str(SCRIPT), "base-ref", cwd=root)
        check(proc.returncode != 0, "name != source ディレクトリのプラグインが対象外になった")

    # base が進んでいても、分岐元（merge-base）と比べるので誤検出しない
    with tempfile.TemporaryDirectory(prefix="desc-sync-base-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        make_repo(root)
        git(root, "checkout", "-q", "-B", "work", "base-ref")
        (root / "NOTES.md").write_text("branch side\n", encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "description に無関係な変更")
        # base 側だけを進める（片側だけの description 変更を含む）
        git(root, "checkout", "-q", "base-ref")
        write(root, marketplace("moved on"), manifest("old catalog"), [skill_md("old skill", "skill0")])
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "base 側が進む")
        git(root, "checkout", "-q", "work")
        proc = run(sys.executable, str(SCRIPT), "base-ref", cwd=root)
        check(
            proc.returncode == 0,
            "base 側が進んだ分を、このブランチの変更として誤検出した",
            proc.stdout,
        )

    # 1-h: 新規プラグイン（base に plugin.json が無い）は対象外
    with tempfile.TemporaryDirectory(prefix="desc-sync-new-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        assert_outside_real_repo(root)
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "test")
        (root / ".claude-plugin").mkdir(parents=True)
        (root / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps(
                {"name": "test-catalog", "owner": {"name": "tester"}, "plugins": []},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "base")
        git(root, "branch", "-q", "base-ref")
        write(root, marketplace("new catalog"), manifest("new catalog"), ["new skill"])
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "プラグインを新規追加")
        proc = run(sys.executable, str(SCRIPT), "base-ref", cwd=root)
        check(proc.returncode == 0, "新規プラグインで落ちた（1-h は対象外のはず）", proc.stdout)

    if failures:
        print(f"{len(failures)} 件の失敗（{checks} 判定）:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"check-description-sync.py のテスト: 全 {checks} 判定に合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
