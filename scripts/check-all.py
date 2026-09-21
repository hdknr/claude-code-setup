#!/usr/bin/env python3
"""歯止めと回帰テストを**全部**回す。1 本ずつ選ばせないための入口。

    python3 scripts/check-all.py                    # base は origin/main を既定で使う
    python3 scripts/check-all.py --base origin/main # 明示する
    python3 scripts/check-all.py --guards-only      # 回帰テストを飛ばす

なぜ必要か（#117 の 1）: #110 の周で、**直前の編集のあと 7 本のうち 2 本しか回さずに
コミットし、CI を割った**。**落ちたのは回さなかったほう**で、しかも計画ファイルの
2 行上には「`check-norm-markers` OK」という**自己申告**が残っていて、申告と実測が
食い違っていた。

**原因は「この編集はあの検査に関係ない」という判断である**——**関係の有無を判断する側が
間違える。** だから**まとめて、判断の余地を無くす。**

**CI からは呼ばない。** CI（`.github/workflows/plugins.yml` / `docs.yml`）は各スクリプトを
**個別のステップ**として呼ぶ——そのほうが**どれが落ちたかが GitHub の UI に出る**。
このスクリプトは**手元でコミットする前に回すためのもの**である。

判定:

- **1 本でも落ちたら非ゼロ終了。**
- **落ちても残りを回す**（最初の 1 本で止めない）。**全体像が出ないと、
  「1 本直してはまた回す」を繰り返すことになる。**
- **飛ばしたものは、黙って飛ばさず SKIP として数えて出す。**

**この検査が守らないもの**——**何を守らないかを書いておかないと、緑であることが
安心の根拠に化ける**:

| 守らないもの | なぜ |
| --- | --- |
| **`git push` したかどうか** | 手元で緑にしても**PR は赤のまま**でありうる（#117 の 2）。**PR 側は `gh pr checks` で見る**。このスクリプトはネットワークに出ない |
| **CI が回すもののうち、ここに無いもの** | 収録は下の `GUARDS` / `TESTS` が正。**`scripts/` に検査を足してここへ登録し忘れると落ちる**（`test-check-all.py` がそれを見る）が、**CI のワークフローに直接書かれたステップ**（`mkdocs build` など）は**見ていない** |
| **検査そのものの正しさ** | 各検査の回帰テストが見る。**このスクリプトは「全部回したか」だけを見る** |

標準ライブラリのみ。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

# 歯止め。(スクリプト名, 追加引数, base-ref を要するか)
GUARDS: list[tuple[str, list[str], bool]] = [
    ("check-plugin-versions.py", [], False),
    ("check-norm-markers.py", [], False),
    ("check-duplicate-counts.py", [], False),
    ("check-skill-pointers.py", [], False),
    ("check-site-links.py", [], False),
    ("check-diagram-freshness.py", [], False),
    ("skill-metrics.py", ["--check"], False),
    # **他の歯止めを子プロセスで回すので、1 本だけ重い。**
    # **並び順に意味は無い**——落ちても止めず、SKIP でも止めないので、
    # どこに置いても出力の順番しか変わらない。
    ("check-mutation-claims.py", [], False),
    ("check-version-bump.py", [], True),
    ("check-description-sync.py", [], True),
    ("check-plan-scope.py", [], True),
]

# 回帰テスト（歯止め自体が何も見ていない状態に退化していないかを見る）
TESTS: list[str] = [
    "test-check-plugin-versions.py",
    "test-check-norm-markers.py",
    "test-check-site-links.py",
    "test-check-diagram-freshness.py",
    "test-check-description-sync.py",
    "test-skill-metrics.py",
    "test-export-diagrams.py",
    "test-token-metrics.py",
    "test-link-skills.py",
    "test-check-all.py",
    "test-check-plan-scope.py",
    "test-collect-guard-rejections.py",
    "test-find-cycle.py",
    "test-check-duplicate-counts.py",
    "test-worktree-scripts.py",
    "test-check-skill-pointers.py",
    "test-check-mutation-claims.py",
]


def run(name: str, args: list[str]) -> tuple[bool, str]:
    """スクリプトを回して (通ったか, 出力) を返す。出力は落ちたときだけ見せる。"""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=SCRIPTS.parent,
    )
    return proc.returncode == 0, (proc.stdout + proc.stderr)


def base_resolves(ref: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        capture_output=True,
        text=True,
        check=False,
        cwd=SCRIPTS.parent,
    )
    return proc.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="歯止めと回帰テストを全部回す")
    parser.add_argument(
        "--base",
        default="origin/main",
        help="PR 限定の検査に渡す base ref（既定: origin/main）",
    )
    parser.add_argument(
        "--guards-only",
        action="store_true",
        help="回帰テストを飛ばす（飛ばしたことは出力に出る）",
    )
    opts = parser.parse_args()

    have_base = base_resolves(opts.base)

    failed: list[str] = []
    skipped: list[str] = []
    logs: list[tuple[str, str]] = []

    print("=== 歯止め ===")
    for name, extra, needs_base in GUARDS:
        label = name if not extra else f"{name} {' '.join(extra)}"
        if needs_base and not have_base:
            print(f"  SKIP {label:<40} base `{opts.base}` が解決できない")
            skipped.append(label)
            continue
        args = [*extra, opts.base] if needs_base else extra
        ok, out = run(name, args)
        print(f"  {'OK  ' if ok else 'FAIL'} {label}")
        if not ok:
            failed.append(label)
            logs.append((label, out))

    if opts.guards_only:
        print("=== 回帰テスト === SKIP（--guards-only）")
        skipped.extend(TESTS)
    else:
        print("=== 回帰テスト ===")
        for name in TESTS:
            ok, out = run(name, [])
            print(f"  {'OK  ' if ok else 'FAIL'} {name}")
            if not ok:
                failed.append(name)
                logs.append((name, out))

    for label, out in logs:
        print(f"\n----- {label} の出力 -----")
        print(out.rstrip())

    total = len(GUARDS) + len(TESTS)
    ran = total - len(skipped)
    print(f"\n{ran}/{total} 本を回した（失敗 {len(failed)} / 飛ばし {len(skipped)}）")
    if skipped:
        print("飛ばしたもの: " + ", ".join(skipped))
        print("**飛ばしたものは回していない。** 手元の緑をそのまま「全部緑」と報告しない。")
    if failed:
        print("落ちたもの: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
