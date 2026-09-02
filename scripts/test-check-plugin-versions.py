#!/usr/bin/env python3
"""scripts/check-plugin-versions.py の SKILL.md 版チェックの回帰テスト。

    python3 scripts/test-check-plugin-versions.py

なぜ必要か（#63）: 「version を上げれば届く」は誤りで、利用者のカタログが凍結していると
**version の変化自体が見えない**。リポジトリ側からできる歯止めは、SKILL.md 本文に版を書いて
**古いキャッシュが読まれたら目に入る**ようにすることだけ。その歯止めが効かなくなっていたら
意味が無いので、ここで固定する。

**歯止めは「落として黙って免除する」形で破られる**（#62 の教訓）。初版は実際に 2 つ落としていた:

- **可視テキストを見ていなかった。** コメントだけ検査していたので、実際に目に入る引用文が
  ずれても緑のまま通った。**守りたいのは可視テキストのほう**なのに検査していなかった。
- **`skills/` を持たないレイアウトを無検査にしていた。** 公式ドキュメントは、単一スキルの
  プラグインは `SKILL.md` をプラグインルート直下に置いてよいと明記している。
  `skills/` の有無だけで判断すると、そのレイアウトが丸ごとすり抜ける。

どちらもレビューが使い捨て fixture で再現した。ここに固定して再発を止める。

**このテストは実環境を触らない。** 毎回テンポラリに偽リポジトリを作り、そこだけを対象にする。
実リポジトリを対象にしてしまうテストは**実行前にアサートで落とす**
（`test-link-skills.py` と同じ設計方針）。

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
SCRIPT = REPO_ROOT / "scripts" / "check-plugin-versions.py"

# 実リポジトリ。ここを対象にしてしまうテストは実行前に落とす。
REAL_REPO = REPO_ROOT.resolve()

failures: list[str] = []
checks = 0


def check(condition: bool, label: str, detail: str = "") -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(f"{label}{': ' + detail if detail else ''}")


def skill_md(
    *,
    comment: str | None,
    visible: str | None,
    name: str = "demo",
    extra: str = "",
) -> str:
    """SKILL.md の中身。`None` を渡すとその記載を省く。"""
    lines = [
        "---",
        f"name: {name}",
        "description: テスト用",
        "---",
        "",
        f"# {name} スキル",
        "",
    ]
    if comment is not None:
        lines.append(f"<!-- skill-version: {comment} -->")
    if visible is not None:
        lines.append(f"> **このスキルの版: {visible}**（プラグイン `{name}`）。")
    if extra:
        lines.append(extra)
    lines += ["", "本文。"]
    return "\n".join(lines) + "\n"


def build(root: Path, plugins: dict[str, dict]) -> None:
    """偽リポジトリを組み立てる。

    `plugins` は {ディレクトリ名: {"version": str, "skills": {相対パス: 中身}}}。
    相対パスは `SKILL.md`（ルート直下）や `skills/foo/SKILL.md` を取る。
    """
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの作業ディレクトリが実リポジトリの内側にある"
    )

    entries = []
    for name, spec in plugins.items():
        entries.append(
            {
                "name": name,
                "source": f"./plugins/{name}",
                "version": spec["version"],
                "description": f"{name} の説明",
            }
        )
        manifest_dir = root / "plugins" / name / ".claude-plugin"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        (manifest_dir / "plugin.json").write_text(
            json.dumps(
                {"name": name, "version": spec["version"], "description": f"{name} の説明"},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        for rel, body in spec.get("skills", {}).items():
            path = root / "plugins" / name / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps(
            {"name": "test-catalog", "owner": {"name": "tester"}, "plugins": entries},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def run_case(plugins: dict[str, dict]) -> subprocess.CompletedProcess[str]:
    """偽リポジトリを作り、そこに**スクリプトをコピーして**走らせる。

    `check-plugin-versions.py` は `REPO_ROOT = Path(__file__).parent.parent` で対象を
    決める（cwd ではない）。実リポジトリの側から呼ぶと**偽リポジトリではなく実リポジトリを
    検査してしまい、テストが常に通る**——最初に書いたときに実際にそうなっていた。
    コピーして走らせることで、対象が偽リポジトリになる。
    """
    with tempfile.TemporaryDirectory(prefix="cpv-test-") as tmp:
        root = Path(tmp) / "repo"
        (root / "scripts").mkdir(parents=True)
        build(root, plugins)
        copied = root / "scripts" / SCRIPT.name
        copied.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(copied)], cwd=root, capture_output=True, text=True
        )


def main() -> int:
    ok = skill_md(comment="1.0.0", visible="1.0.0")

    # 正常系: コメントも可視テキストも一致 → 通る
    proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": ok}}})
    check(proc.returncode == 0, "版が揃っているのに落ちた", proc.stdout)

    # SKILL.md を 1 つも持たないプラグインは検査対象なし（workspace-setup がこの形）
    proc = run_case({"demo": {"version": "1.0.0"}})
    check(proc.returncode == 0, "SKILL.md を持たないプラグインで落ちた", proc.stdout)

    # コメントの版がずれる
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {"skills/demo/SKILL.md": skill_md(comment="9.9.9", visible="1.0.0")},
            }
        }
    )
    check(proc.returncode != 0, "コメントの版ずれがすり抜けた")

    # **可視テキストの版だけずれる**（初版が見逃していた形）
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {"skills/demo/SKILL.md": skill_md(comment="1.0.0", visible="0.1.0")},
            }
        }
    )
    check(proc.returncode != 0, "可視テキストの版ずれがすり抜けた（守りたいのはこちら）")

    # 記載が無い（コメント / 可視テキストそれぞれ）
    for missing, label in (("comment", "コメント"), ("visible", "可視テキスト")):
        body = skill_md(
            comment=None if missing == "comment" else "1.0.0",
            visible=None if missing == "visible" else "1.0.0",
        )
        proc = run_case({"demo": {"version": "1.0.0", "skills": {"skills/demo/SKILL.md": body}}})
        check(proc.returncode != 0, f"版の{label}が無いのに通った（fail-open）")

    # 記載が 2 つある
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {
                    "skills/demo/SKILL.md": skill_md(
                        comment="1.0.0", visible="1.0.0", extra="<!-- skill-version: 1.0.0 -->"
                    )
                },
            }
        }
    )
    check(proc.returncode != 0, "版の記載が 2 つあるのに通った")

    # **skills/ を持たず、プラグインルート直下に SKILL.md を置く公式レイアウト**
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {"SKILL.md": skill_md(comment=None, visible=None)},
            }
        }
    )
    check(
        proc.returncode != 0,
        "ルート直下 SKILL.md のプラグインが無検査で免除された（受入基準 2-e）",
    )

    proc = run_case(
        {"demo": {"version": "1.0.0", "skills": {"SKILL.md": ok}}}
    )
    check(proc.returncode == 0, "ルート直下 SKILL.md で版が揃っているのに落ちた", proc.stdout)

    # スキルが複数あり、片方だけ記載漏れ
    proc = run_case(
        {
            "demo": {
                "version": "1.0.0",
                "skills": {
                    "skills/one/SKILL.md": skill_md(comment="1.0.0", visible="1.0.0", name="one"),
                    "skills/two/SKILL.md": skill_md(comment=None, visible=None, name="two"),
                },
            }
        }
    )
    check(proc.returncode != 0, "複数スキルの片方の記載漏れがすり抜けた")

    if failures:
        print(f"{len(failures)} 件の失敗（{checks} 判定）:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"check-plugin-versions.py の版チェック: 全 {checks} 判定に合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
