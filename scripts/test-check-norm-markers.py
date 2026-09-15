#!/usr/bin/env python3
"""`check-norm-markers.py` の回帰テスト。

    python3 scripts/test-check-norm-markers.py

**このテストは実環境を触らない。** 毎回テンポラリに偽リポジトリを作り、そこだけを対象にする
（`assert_not_real_repo` がそれを担保する）。実リポジトリを対象にしたテストは、
通ったことが「歯止めが効く」の証明にならないうえ、壊す危険がある。

**変異テストを含む。** 検査本体を 1 箇所ずつ壊し、**壊したのに緑のままなら失格**とする。
歯止めのテストは「正しい入力で緑」だけでは足りない——それは**何も検査しない実装でも通る**
（#62 で実際に、弱い assertion が変異を殺せなかった）。
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import importlib.util

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPT = REAL_REPO / "scripts" / "check-norm-markers.py"
MARKER = "（必須）"

failures: list[str] = []


def load(root: Path):
    """偽リポジトリを root として検査モジュールを読み込む。"""
    spec = importlib.util.spec_from_file_location(f"cnm_{root.name}", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_repo(root: Path) -> None:
    assert root.resolve() != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(root.resolve()).startswith(str(REAL_REPO) + os.sep), (
        "テストの対象が実リポジトリの内側にある"
    )
    # **両側を resolve() してから比べる。** macOS では `gettempdir()` が `/var/folders/...`
    # を返すのに `Path.resolve()` は `/private/var/folders/...` を返すので、
    # 片側だけ解決すると**実環境でも偽リポジトリでも落ちる**（このテストを書いた周で踏んだ）。
    tmp_root = Path(tempfile.gettempdir()).resolve()
    assert root.resolve().is_relative_to(tmp_root), "テストの対象がテンポラリの外にある"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def make_repo(root: Path, *, origin_body: str, others: dict[str, str]) -> None:
    assert_not_real_repo(root)
    origin = root / "plugins" / "dev-loop" / "skills" / "dev-loop" / "SKILL.md"
    origin.parent.mkdir(parents=True, exist_ok=True)
    origin.write_text(origin_body, encoding="utf-8")
    for rel, body in others.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def run(root: Path) -> list[tuple[str, int, str]]:
    mod = load(root)
    return mod.violations(root)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cnm-test-") as tmp:
        base = Path(tmp)

        print("正常系")
        root = base / "ok"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- **これは必須である{MARKER}**\n",
            others={
                "plugins/dev-loop/README.md": "# README\n\n手順は SKILL.md が正。\n",
                "docs/plugins/dev-loop-design.md": "# 設計\n\n本文。\n",
            },
        )
        check("原本にマーカーがあっても通る", run(root) == [])

        print("違反を捕まえる")
        root = base / "leak"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={"plugins/dev-loop/README.md": f"# README\n\n- 漏れた規範{MARKER}\n"},
        )
        found = run(root)
        check("原本の外の素のマーカーを捕まえる", len(found) == 1)
        check("捕まえた場所が README", found and found[0][0] == "plugins/dev-loop/README.md")
        check("行番号が正しい", found and found[0][1] == 3)

        print("例外 1: バッククォートに囲まれた引用は通す")
        root = base / "quoted"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "docs/plugins/dev-loop-design.md":
                    f"# 設計\n\n数えているのは `{MARKER}` だけである。\n",
            },
        )
        check("引用されたマーカーは違反にしない", run(root) == [])

        print("例外 1 の境界: 同じ行に引用と素のマーカーが混在したら捕まえる")
        root = base / "mixed"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "docs/plugins/dev-loop-design.md":
                    f"# 設計\n\n`{MARKER}` の話。ところでこれは必須{MARKER}\n",
            },
        )
        check("引用があっても素のマーカーは見逃さない", len(run(root)) == 1)

        print("例外 2: 生成ブロックの中は通す")
        root = base / "generated"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "docs/plugins/dev-loop-design.md": (
                    "# 設計\n\n<!-- skill-metrics:begin -->\n"
                    f"| 途中から再開する周{MARKER} | 38 | 3 |\n"
                    "<!-- skill-metrics:end -->\n"
                ),
            },
        )
        check("生成ブロック内のマーカーは違反にしない", run(root) == [])

        print("例外 2 の境界: 生成ブロックを閉じたあとは通さない")
        root = base / "after-generated"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "docs/plugins/dev-loop-design.md": (
                    "# 設計\n\n<!-- skill-metrics:begin -->\n"
                    "| 節 | 行 |\n"
                    "<!-- skill-metrics:end -->\n"
                    f"\nここは生成の外{MARKER}\n"
                ),
            },
        )
        check("生成ブロックの外は捕まえる", len(run(root)) == 1)

        print("例外 1 の境界: 2 つのインラインコードの間の素のマーカー")
        # **最初の実装はこれを見逃した。** マーカーを含む囲みだけを狙う正規表現だと、
        # 最初の囲みの閉じと次の囲みの開きが 1 つの囲みとして一致し、
        # **間の素のマーカーごと消える**（#94 のレビューが再現例つきで指摘）。
        root = base / "between-spans"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "plugins/dev-loop/README.md": (
                    f"# README\n\n"
                    f"`/code-review` は{MARKER}で、`SKILL.md` の受入基準をまるごと渡す。\n"
                    f"\n| `x` | 渡すもの{MARKER} | `y` |\n"
                ),
            },
        )
        check("囲みと囲みの間の素のマーカーを捕まえる", len(run(root)) == 2)

        print("例外 1 の境界: 二重バッククォートの囲みは通す")
        # **見逃しを直した版が、今度はこれを誤検出した。** 開きの 2 本目を「空の囲み」として
        # 食い、間のマーカーが素のまま残っていた（#94 のレビューが再現例つきで指摘）。
        # **開いた本数と同じ本数で閉じる**ようにして直した。
        root = base / "double-backtick"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "docs/plugins/dev-loop-design.md": (
                    f"# 設計\n\n"
                    f"``{MARKER}`` と書けば引用である。\n"
                    f"`` {MARKER} `` も同じ。\n"
                ),
            },
        )
        check("二重バッククォートの引用を違反にしない", run(root) == [])

        print("例外 1 の境界: 二重で囲んでも、外にある素のマーカーは捕まえる")
        root = base / "double-and-bare"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "docs/plugins/dev-loop-design.md":
                    f"# 設計\n\n``{MARKER}`` の話。ところでこれは必須{MARKER}\n",
            },
        )
        check("二重の引用があっても素のマーカーは見逃さない", len(run(root)) == 1)

        print("例外 3: フェンスの中は数えない")
        root = base / "fenced"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "docs/plugins/dev-loop-design.md":
                    f"# 設計\n\n```bash\ngh issue view 999   # 把握{MARKER}\n```\n",
            },
        )
        check("フェンス内のマーカーは違反にしない", run(root) == [])

        print("例外 3 の境界: フェンスを閉じたあとは数える")
        root = base / "after-fence"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "docs/plugins/dev-loop-design.md":
                    f"# 設計\n\n```bash\necho hi\n```\n\nここは外{MARKER}\n",
            },
        )
        found = run(root)
        check("フェンスの外は捕まえる", len(found) == 1)
        # `strip_fences` は行数を保って空行に置き換えるので、行番号がずれない。
        check("フェンスを落としても行番号がずれない", found and found[0][1] == 7)

        print("原本の数え方が skill-metrics と揃っている")
        root = base / "count"
        make_repo(
            root,
            origin_body=(
                f"# 原本\n\n- 本体{MARKER}\n\n"
                f"```bash\ngh issue view 999   # 例{MARKER}\n```\n"
            ),
            others={},
        )
        mod = load(root)
        origin_text = (root / mod.ORIGIN).read_text(encoding="utf-8")
        check("フェンス内を数えない（素だと 2、落とすと 1）",
              origin_text.count(MARKER) == 2
              and mod.strip_fences(origin_text).count(MARKER) == 1)

        print("収集範囲")
        root = base / "skip"
        make_repo(
            root,
            origin_body=f"# 原本\n\n- 本体{MARKER}\n",
            others={
                "site/plugins/index.md": f"# ビルド成果物{MARKER}\n",
                ".claude/plans/issue-1.md": f"# 作業メモ{MARKER}\n",
                "docs/nested/deep/page.md": f"# 深い場所{MARKER}\n",
            },
        )
        found = run(root)
        rels = {f[0] for f in found}
        check("site/ は見ない", "site/plugins/index.md" not in rels)
        check(".claude/ は見ない", ".claude/plans/issue-1.md" not in rels)
        check("入れ子の深い .md も見る", "docs/nested/deep/page.md" in rels)

        print("終了コード（CI が見ているのはここ）")
        # **`violations()` だけを呼ぶテストでは、CI が依存する終了コードが無検査になる。**
        # #94 のレビューが実証した——`main()` の `return 1` を `return 0` に変えても、
        # **漏れのあるリポジトリでスクリプトが 0 を返し、テストは「すべて合格」のまま**だった。
        # `test-check-plugin-versions.py` / `test-skill-metrics.py` と同じく、
        # **スクリプトを実際に起動して `returncode` を見る**。
        for name, others, want in [
            ("漏れが無ければ 0", {"plugins/dev-loop/README.md": "# README\n\n手順は SKILL.md が正。\n"}, 0),
            ("漏れがあれば 1", {"plugins/dev-loop/README.md": f"# README\n\n- 漏れた{MARKER}\n"}, 1),
        ]:
            eroot = base / ("exit-" + str(want))
            assert_not_real_repo(eroot)
            (eroot / "scripts").mkdir(parents=True, exist_ok=True)
            for helper in ("check-norm-markers.py", "markdown_fences.py"):
                shutil.copy(REAL_REPO / "scripts" / helper, eroot / "scripts" / helper)
            make_repo(eroot, origin_body=f"# 原本\n\n- 本体{MARKER}\n", others=others)
            proc = subprocess.run(
                [sys.executable, str(eroot / "scripts" / "check-norm-markers.py")],
                capture_output=True, text=True,
            )
            check(f"{name}（実際に起動して returncode を見る）", proc.returncode == want)

        print("原本が無ければ落ちる（fail-closed）")
        nroot = base / "no-origin"
        assert_not_real_repo(nroot)
        (nroot / "scripts").mkdir(parents=True, exist_ok=True)
        for helper in ("check-norm-markers.py", "markdown_fences.py"):
            shutil.copy(REAL_REPO / "scripts" / helper, nroot / "scripts" / helper)
        (nroot / "docs").mkdir(parents=True, exist_ok=True)
        (nroot / "docs" / "page.md").write_text("# ページ\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(nroot / "scripts" / "check-norm-markers.py")],
            capture_output=True, text=True,
        )
        check("原本が見つからなければ非ゼロで落ちる", proc.returncode != 0)
        check("原本が無いことを理由として言う", "原本が見つからない" in proc.stderr)

        print("変異テスト（壊したのに緑なら失格）")
        mutants = {
            "原本の除外をやめる（原本自身が違反になるはず）": (
                'if rel == ORIGIN:\n            continue',
                'if False:\n            continue',
            ),
            "生成ブロックの判定をやめる": (
                "if MARKER not in line or in_generated:",
                "if MARKER not in line:",
            ),
            "引用の除去をやめる（引用が違反になるはず）": (
                "if MARKER in CODE_SPAN.sub(\"\", line):",
                "if MARKER in line:",
            ),
            "フェンスの除去をやめる（フェンス内が違反になるはず）": (
                "stripped = strip_fences(path.read_text(encoding=\"utf-8\")).splitlines()",
                "stripped = path.read_text(encoding=\"utf-8\").splitlines()",
            ),
            "囲みの長さを見ない（二重バッククォートが違反になるはず）": (
                'CODE_SPAN = re.compile(r"(`+)(?:(?!\\1)[\\s\\S])*?\\1")',
                'CODE_SPAN = re.compile(r"`[^`]*`")',
            ),
        }
        # **終了コードの変異は、起動しないと殺せない。** `violations()` を呼ぶだけの
        # テストでは `main()` の `return 1` を `return 0` に変えても緑のままになる（#94）。
        exit_mutant = ("        return 1\n\n    total", "        return 0\n\n    total")
        source_for_exit = SCRIPT.read_text(encoding="utf-8")
        assert source_for_exit.count(exit_mutant[0]) == 1, "終了コードの変異の対象が 1 箇所でない"
        mroot = base / "mutant-exit"
        assert_not_real_repo(mroot)
        (mroot / "scripts").mkdir(parents=True, exist_ok=True)
        (mroot / "scripts" / "check-norm-markers.py").write_text(
            source_for_exit.replace(*exit_mutant), encoding="utf-8")
        shutil.copy(REAL_REPO / "scripts" / "markdown_fences.py", mroot / "scripts" / "markdown_fences.py")
        make_repo(mroot, origin_body=f"# 原本\n\n- 本体{MARKER}\n",
                  others={"plugins/dev-loop/README.md": f"# README\n\n- 漏れた{MARKER}\n"})
        proc = subprocess.run(
            [sys.executable, str(mroot / "scripts" / "check-norm-markers.py")],
            capture_output=True, text=True,
        )
        # **変異体は 0 を返す**（それが変異の中身）。上の「漏れがあれば 1」が 1 を要求して
        # いるので、変異体はそこで落ちる＝殺せる。ここで確かめるのは
        # **変異が実際に挙動を変えていること**——変わらないなら、その assertion は
        # 何も見ていないことになる。
        check("変異を殺せる: 違反時に 0 を返す（起動しないと殺せない）", proc.returncode == 0)

        source = SCRIPT.read_text(encoding="utf-8")
        for name, (old, new) in mutants.items():
            assert source.count(old) == 1, f"変異の対象が 1 箇所でない: {name}"
            mroot = base / ("mutant-" + str(abs(hash(name)) % 10**6))
            assert_not_real_repo(mroot)
            (mroot / "scripts").mkdir(parents=True, exist_ok=True)
            mscript = mroot / "scripts" / "check-norm-markers.py"
            mscript.write_text(source.replace(old, new), encoding="utf-8")
            make_repo(
                mroot,
                origin_body=f"# 原本\n\n- 本体{MARKER}\n",
                others={
                    "docs/plugins/dev-loop-design.md": (
                        "# 設計\n\n<!-- skill-metrics:begin -->\n"
                        f"| 節{MARKER} | 38 |\n"
                        "<!-- skill-metrics:end -->\n"
                        f"\n数えているのは `{MARKER}` だけ。\n"
                        f"\n``{MARKER}`` と二重で囲んでも引用である。\n"
                        f"\n```bash\necho 例{MARKER}\n```\n"
                    ),
                },
            )
            spec = importlib.util.spec_from_file_location(f"mut_{mroot.name}", mscript)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # 正常な入力（原本にマーカー・生成ブロック内・引用）だけを置いてあるので、
            # **正しい実装なら 0 件**。変異体が 0 件のままなら、その判定は効いていない。
            killed = len(mod.violations(mroot)) > 0
            check(f"変異を殺せる: {name}", killed)

        print("実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("必須マーカー検査のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
