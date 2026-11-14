#!/usr/bin/env python3
"""`formal-baseline.py`（形式検査のモデルの書く場所と形の確かめ。#1031）の回帰テスト。

    python3 scripts/test-formal-baseline.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-frozen.py` と同じ形。

見るもの:

1. **`target`**: 作業中の版（番号が最大の版）の書く場所を出す。**作業中の版がリリース済みなら 3 で書く場所を出さない**。
   前の版だけがリリース済みなら書ける（陽性対照）。命名に合わないタグは数えない。版が無い・版の番号が欠ける・git でない・
   **浅い clone**（同じ元からの深い clone では判定できることを陽性対照にする）は 2。サブディレクトリから呼んでも根で決める。
2. **`check`**: 形どおりのディレクトリは 0（陽性対照）。**一覧に無いファイル（TLC の `states/` など）・一覧のファイルが無い・symlink・
   項目の欠け・空・2 行・`結果` が `判定できなかった`・`前回のモデル` の値・バッククォートの無い一覧・パスを含む名前・`README.md` を一覧に入れる・
   名前の形・置き場所**は 1。ディレクトリが無い・`README.md` が無いは 2。
3. **本体の記録の項目・`結果` と `前回のモデル` の値が `references/tree.md` の「形式検査のモデル」の表と一致する**（写しのずれ）。
4. **`check-findings-csv.py` が `モデルの保存` の行を実行の行と読まない**（`抜けた` の行は読む——陽性対照）。
5. **想定外の例外は 2 で、トレースバックの 1 にしない。`-OO`（docstring が無い）で引数なしに呼んでも 2**（#286 と同じ形）。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる（全部の試料がこの形で走る）。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに作り、`HOME` と `GIT_CONFIG_GLOBAL` を差し替えて利用者の git 設定を読まない。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめ、**壊す前の本体では同じ試料が期待どおりであること**（陽性対照）を全試料の回で見る。
変異の数は本体の docstring の「守ること」の行の数以上であることも見る。
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "formal-baseline.py"
REFERENCE = PLUGIN / "references" / "tree.md"

V1 = "docs/v1/shared/qa.csv"
V2 = "docs/v2/shared/qa.csv"
V3 = "docs/v3/shared/qa.csv"

# ---- target の試料。手順: ("w", パス, 中身) 書いて add／("c",) commit／("t", 名前) タグ／("shallow",)・("deep",) clone し直す／
# ("arg", 根からのパス) --repo に渡す。None なら git でないディレクトリ
Steps = list[tuple[str, ...]] | None
TARGET_CASES: list[tuple[str, Steps, int, str]] = [
    ("v1 が作業中", [("w", V1, "a\n"), ("c",)], 0, "書く場所: docs/v1/spec/formal/<対象>/"),
    ("v1 は保存したモデルも同じ場所", [("w", V1, "a\n"), ("c",)], 0, "保存したモデルを探す場所: docs/v1/spec/formal/"),
    ("リリース済みの v1", [("w", V1, "a\n"), ("c",), ("t", "release-v1")], 3, "作業中の版 v1 はリリース済み"),
    ("v2 が作業中", [("w", V1, "a\n"), ("c",), ("t", "release-v1"), ("w", V2, "b\n"), ("c",)], 0,
     "書く場所: docs/v2/spec/formal/<対象>/"),
    ("v2 は重ね合わせた全体から探す", [("w", V1, "a\n"), ("c",), ("t", "release-v1"), ("w", V2, "b\n"), ("c",)], 0,
     "build/merged/spec/formal/"),
    ("リリース済みの v2", [("w", V1, "a\n"), ("w", V2, "b\n"), ("c",), ("t", "release-v2")], 3, "次の版（docs/v3/）"),
    ("命名に合わないタグを数えない", [("w", V1, "a\n"), ("c",), ("t", "release-v01"), ("t", "release-v1-fix")], 0,
     "書く場所: docs/v1/"),
    ("サブディレクトリから", [("w", V1, "a\n"), ("c",), ("t", "release-v1"), ("arg", "docs")], 3, "リリース済み"),
    ("版が無い", [("w", "docs/README.md", "a\n"), ("c",)], 2, "版（v<n>）が 1 つも無い"),
    ("docs が無い", [("w", "README.md", "a\n"), ("c",)], 2, "版（v<n>）が 1 つも無い"),
    ("版の番号が欠ける", [("w", V1, "a\n"), ("w", V3, "c\n"), ("c",)], 2, "版の決まりに反する"),
    ("浅い clone", [("w", V1, "a\n"), ("c",), ("t", "release-v1"), ("shallow",)], 2, "浅い clone"),
    # 陽性対照: 同じ元から履歴とタグをすべて取った clone は判定できる
    ("深い clone", [("w", V1, "a\n"), ("c",), ("t", "release-v1"), ("deep",)], 3, "リリース済み"),
    ("git でない", None, 2, "git の作業ツリーでない"),
    # タグを取っていない clone（--no-tags）・あとで付いて取っていないタグは、取り直してから見る（#1031 の 1 パス目）
    ("--no-tags の clone", [("w", V1, "a\n"), ("c",), ("t", "release-v1"), ("notags",)], 3, "リリース済み"),
    ("取っていないタグ", [("w", V1, "a\n"), ("c",), ("deep",), ("ts", "release-v1")], 3, "リリース済み"),
    ("取り直せない", [("w", V1, "a\n"), ("c",), ("t", "release-v1"), ("deep",), ("rmsrc",)], 2, "リリースのタグを取り直せない"),
    # 陽性対照: 取っていないタグが無ければ、取り直しても書ける
    ("取り直しても書ける", [("w", V1, "a\n"), ("c",), ("deep",)], 0, "書く場所: docs/v1/"),
]

# ---- check の試料
ITEMS = {
    "対象": "`spec/order.md:12` の取り消しのフロー",
    "検査器": "TLC 2.19",
    "構成の大きさ": "書き手 2・利用者 1",
    "結果": "反例なし",
    "陽性対照": "排他を外すと 2 重の取り消しの反例が出た",
    "置いた前提": "なし",
    "前回のモデル": "無かった",
    "モデルのファイル": "`order.tla`・`order.cfg`",
    "残した回": "v1・2026-11-14・`モデルの保存`（回 3）",
}
MODEL_FILES = {"order.tla": "---- MODULE order ----\n====\n", "order.cfg": "INIT Init\n"}


def readme(drop: tuple[str, ...] = (), **over: str) -> str:
    rows = ["| 項目 | 記録 |", "| --- | --- |"]
    for item, value in ITEMS.items():
        if item in drop:
            continue
        rows.append(f"| {item} | {over.get(item, value)} |")
    return "# order-cancel\n\n" + "\n".join(rows) + "\n"


# (名前, 対象のディレクトリの根からのパス, {ディレクトリからの相対パス: 中身（None なら order.tla への symlink）}, 期待する終了コード, 出力の文字列)
GOOD_DIR = "docs/v1/spec/formal/order-cancel"
CheckCase = tuple[str, str, dict[str, str | None] | None, int, str]
CHECK_CASES: list[CheckCase] = [
    ("形どおり", GOOD_DIR, {"README.md": readme(), **MODEL_FILES}, 0, "形どおり（モデルのファイル 2 件）"),
    ("states が残る", GOOD_DIR, {"README.md": readme(), **MODEL_FILES, "states/x.st": "x"}, 1, "states: モデルのファイルの一覧に無い"),
    ("出力のファイルが残る", GOOD_DIR, {"README.md": readme(), **MODEL_FILES, "tlc.out": "x"}, 1, "tlc.out: モデルのファイルの一覧に無い"),
    ("一覧のファイルが無い", GOOD_DIR, {"README.md": readme(), "order.tla": "x"}, 1, "「order.cfg」がこのディレクトリの通常のファイルとして無い"),
    ("一覧のファイルが symlink", GOOD_DIR, {"README.md": readme(), "order.tla": "x", "order.cfg": None}, 1,
     "「order.cfg」がこのディレクトリの通常のファイルとして無い"),
    ("陽性対照の行が無い", GOOD_DIR, {"README.md": readme(drop=("陽性対照",)), **MODEL_FILES}, 1, "項目「陽性対照」の行が無い"),
    ("置いた前提が空", GOOD_DIR, {"README.md": readme(置いた前提=""), **MODEL_FILES}, 1, "項目「置いた前提」の記録が空"),
    ("結果が 2 行", GOOD_DIR, {"README.md": readme() + "| 結果 | 反例あり |\n", **MODEL_FILES}, 1, "項目「結果」が 2 行ある"),
    ("結果が判定できなかった", GOOD_DIR, {"README.md": readme(結果="判定できなかった"), **MODEL_FILES}, 1, "結果が 反例なし／反例あり のどちらでもない"),
    ("結果の後ろに判定できなかった", GOOD_DIR, {"README.md": readme(結果="反例なしかは判定できなかった"), **MODEL_FILES}, 1,
     "結果が 反例なし／反例あり のどちらでもない"),
    ("前回のモデルの後ろに別の語", GOOD_DIR, {"README.md": readme(前回のモデル="直さず使ったかは不明"), **MODEL_FILES}, 1, "前回のモデルが"),
    ("前回のモデルに要約", GOOD_DIR, {"README.md": readme(前回のモデル="直して使った（排他を足した）"), **MODEL_FILES}, 0, "形どおり"),
    ("結果が反例あり", GOOD_DIR, {"README.md": readme(結果="反例あり（2 重の取り消し）"), **MODEL_FILES}, 0, "形どおり"),
    ("前回のモデルが違う値", GOOD_DIR, {"README.md": readme(前回のモデル="新しく作った"), **MODEL_FILES}, 1, "前回のモデルが"),
    ("一覧にバッククォートが無い", GOOD_DIR, {"README.md": readme(モデルのファイル="order.tla・order.cfg"), **MODEL_FILES}, 1,
     "バッククォートで囲んだ名前が 1 つも無い"),
    ("一覧の名前にパス", GOOD_DIR, {"README.md": readme(モデルのファイル="`sub/order.tla`"), "sub/order.tla": "x"}, 1,
     "「sub/order.tla」はこのディレクトリのファイルの名前でない"),
    ("README を一覧に入れる", GOOD_DIR, {"README.md": readme(モデルのファイル="`README.md`")}, 1,
     "「README.md」はこのディレクトリのファイルの名前でない"),
    ("名前に大文字", "docs/v1/spec/formal/Order", {"README.md": readme(), **MODEL_FILES}, 1, "英小文字・数字・ハイフンだけでない"),
    ("置き場所が違う", "docs/v1/spec/models/order-cancel", {"README.md": readme(), **MODEL_FILES}, 1, "置き場所が spec/formal/<対象>/ でない"),
    ("ディレクトリが無い", GOOD_DIR, None, 2, "ディレクトリでない"),
    ("README が無い", GOOD_DIR, dict(MODEL_FILES), 2, "README.md: 無い"),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("リリース済みでも書く", "    if number in released:\n", "    if False:\n", "リリース済みの v1"),
    ("最初の版に書く", "number = found[-1][0]", "number = found[0][0]", "v2 が作業中"),
    ("版の決まりの違反を通す", "    if problems:\n        return 2, problems + [", "    if False:\n        return 2, problems + [", "版の番号が欠ける"),
    ("版が無いのを通す", "    if not found:\n        return 2, [f\"{docs}", "    if False:\n        return 2, [f\"{docs}", "版が無い"),
    ("浅い clone を通す", 'if shallow.returncode != 0 or shallow.stdout.strip() == "true":', "if shallow.returncode != 0:", "浅い clone"),
    ("一覧に無いファイルを通す", "        if entry != README and entry not in listed:\n", "        if False:\n", "states が残る"),
    ("一覧のファイルが無いのを通す", "elif path.is_symlink() or not path.is_file():", "elif path.is_symlink():", "一覧のファイルが無い"),
    ("symlink を通す", "elif path.is_symlink() or not path.is_file():", "elif not path.is_file():", "一覧のファイルが symlink"),
    ("項目の欠けを通す", "        if item not in records:\n            problems.append(", "        if False:\n            problems.append(", "陽性対照の行が無い"),
    ("空の記録を通す", "        elif not records[item]:\n", "        elif False:\n", "置いた前提が空"),
    ("2 行ある項目を通す", '            problems.append(f"{readme}: 項目「{item}」が 2 行ある")\n', "            pass\n", "結果が 2 行"),
    ("判定できなかったを通す", "    if result and not one_of(result, RESULTS):\n", "    if False:\n", "結果が判定できなかった"),
    ("前回のモデルの値を通す", "    if previous and not one_of(previous, PREVIOUS):\n", "    if False:\n", "前回のモデルが違う値"),
    ("前方一致に戻す", '    return any(value == a or value.startswith(a + "（") for a in allowed)', "    return value.startswith(allowed)",
     "結果の後ろに判定できなかった"),
    ("タグを取り直さない", "    if remotes.stdout.strip():\n", "    if False:\n", "取っていないタグ"),
    ("取り直せなくても続ける", "        if fetched.returncode != 0:\n", "        if False:\n", "取り直せない"),
    ("バッククォートの無い一覧を通す", '    if records.get("モデルのファイル") and not listed:\n', "    if False:\n", "一覧にバッククォートが無い"),
    ("パスを含む名前を通す", 'if "/" in name or name in (README, ".", ".."):', 'if name in (README, ".", ".."):', "一覧の名前にパス"),
    ("README を一覧に入れるのを通す", 'if "/" in name or name in (README, ".", ".."):', 'if "/" in name:', "README を一覧に入れる"),
    ("名前の形を見ない", "    if not NAME.fullmatch(resolved.name):\n", "    if False:\n", "名前に大文字"),
    ("置き場所を見ない", '    if f"{resolved.parent.parent.name}/{resolved.parent.name}/" != versions.FORMAL_DIR:\n', "    if False:\n",
     "置き場所が違う"),
    ("ディレクトリでないのを 2 にしない", "    if not directory.is_dir():\n        return 2", "    if False:\n        return 2", "ディレクトリが無い"),
    ("README が無いのを 2 にしない", '    except FileNotFoundError:\n        raise Unjudged(f"{readme}: 無い")',
     "    except FileNotFoundError:\n        return {}, []", "README が無い"),
]

# 想定外の例外は 2・-OO（docstring が無い）で引数なしに呼んでも想定外の例外にならない（#286）。(名前, 壊す前, 壊した後)
OO_MUTATIONS = [
    ("想定外の例外を 2 に寄せない", "    except Exception as e:  # 想定外の例外も「判定していない」（2）",
     "    except ImportError as e:  # 想定外の例外も「判定していない」（2）"),
    ("-OO で docstring が無いと落ちる", "description=__doc__.splitlines()[0] if __doc__ else None",
     "description=__doc__.splitlines()[0] if True else None"),
]
UNEXPECTED_RUNNER = """
import runpy, subprocess, sys
def run(*args, **kwargs):
    raise ValueError("試料")
subprocess.run = run
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def sandbox_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(HOME=str(home), GIT_CONFIG_GLOBAL=str(home / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_DATE="2026-01-01T00:00:00Z", GIT_COMMITTER_DATE="2026-01-01T00:00:00Z")
    return env


def run_git(repo: Path, env: dict[str, str], *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=test", "-c", "user.email=test@example.com",
                    "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                   check=True, capture_output=True, env=env)


def build_target(root: Path, steps: Steps, env: dict[str, str]) -> list[str]:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    repo_arg = root
    if steps is None:
        return ["target", "--repo", str(root)]
    run_git(root, env, "init", "-q", "-b", "main")
    for step in steps:
        kind = step[0]
        if kind == "w":
            path = root / step[1]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(step[2], encoding="utf-8")
            run_git(root, env, "add", "-A")
        elif kind == "c":
            run_git(root, env, "commit", "-q", "-m", "step")
        elif kind == "t":
            run_git(root, env, "tag", step[1])
        elif kind in ("shallow", "deep", "notags"):
            source = root.with_name(root.name + "-src")
            root.rename(source)
            options = {"shallow": ["--depth=1", "--no-tags"], "notags": ["--no-tags"], "deep": []}[kind]
            subprocess.run(["git", "clone", "-q", *options, f"file://{source}", str(root)],
                           check=True, capture_output=True, env=env)
        elif kind == "ts":  # clone した元にだけタグを付ける（取っていないタグ）
            run_git(root.with_name(root.name + "-src"), env, "tag", step[1])
        elif kind == "rmsrc":  # clone した元を消す（取り直せない）
            shutil.rmtree(root.with_name(root.name + "-src"))
        elif kind == "arg":
            repo_arg = root / step[1]
    return ["target", "--repo", str(repo_arg)]


def build_check(root: Path, directory: str, files: dict[str, str | None] | None) -> list[str]:
    assert_in_tmp(root)
    target = root / directory
    if files is not None:
        target.mkdir(parents=True)
        for name, content in files.items():
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if content is None:
                path.symlink_to(target / "order.tla")
            else:
                path.write_text(content, encoding="utf-8")
    else:
        root.mkdir(parents=True)
    return ["check", str(target)]


def all_cases() -> list[tuple[str, int, str]]:
    return [(c[0], c[2], c[3]) for c in TARGET_CASES] + [(c[0], c[3], c[4]) for c in CHECK_CASES]


def run_all(scripts: Path, work: Path, env: dict[str, str], only: str | None = None) -> dict[str, tuple[int, str]]:
    results = {}
    for index, (name, steps, _, _) in enumerate(TARGET_CASES):
        if only is not None and name != only:
            continue
        args = build_target(work / f"t{index}", steps, env)
        proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), *args],
                              capture_output=True, text=True, cwd=work, env=env)
        results[name] = (proc.returncode, proc.stdout + proc.stderr)
    for index, (name, directory, files, _, _) in enumerate(CHECK_CASES):
        if only is not None and name != only:
            continue
        args = build_check(work / f"c{index}", directory, files)
        proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), *args],
                              capture_output=True, text=True, cwd=work, env=env)
        results[name] = (proc.returncode, proc.stdout + proc.stderr)
    return results


def as_expected(name: str, result: tuple[int, str]) -> bool:
    _, code, text = next(case for case in all_cases() if case[0] == name)
    return result[0] == code and text in result[1]


def reference_mismatches(source: str, markdown: str) -> list[str]:
    """`tree.md` の「形式検査のモデル」の記録の表の項目・`結果`・`前回のモデル` の値が、本体の定数と合うか。"""
    problems = []
    section = re.search(r"^## 形式検査のモデル.*?(?=^## )", markdown, flags=re.MULTILINE | re.DOTALL)
    if section is None:
        return ["tree.md に「形式検査のモデル」の節が無い"]
    table = re.search(r"^\| 項目 \| 書くもの \|\n\| --- \| --- \|\n((?:\|.*\|\n)+)", section.group(0), flags=re.MULTILINE)
    if table is None:
        return ["「形式検査のモデル」に項目の表が無い"]
    rows = {}
    for line in table.group(1).splitlines():
        item, _, value = line.strip()[1:-1].partition("|")
        rows[item.strip()] = value.strip()
    code_items = re.search(r"^ITEMS = \((.*)\)$", source, flags=re.MULTILINE)
    items = re.findall(r'"([^"]+)"', code_items.group(1)) if code_items else []
    if list(rows) != items:
        problems.append(f"記録の項目 {list(rows)} ≠ 本体 {items}")
    for item, constant in (("結果", "RESULTS"), ("前回のモデル", "PREVIOUS")):
        code = re.search(rf"^{constant} = \((.*)\)$", source, flags=re.MULTILINE)
        values = re.findall(r'"([^"]+)"', code.group(1)) if code else []
        written = re.findall(r"`([^`]+)`", rows.get(item, ""))
        if written != values:
            problems.append(f"{item} の値 {written} ≠ 本体 {constant} {values}")
    return problems


REFERENCE_MUTATIONS: list[tuple[str, str, str]] = [
    ("項目の名前", "| 陽性対照 | わざと壊した箇所", "| 対照 | わざと壊した箇所"),
    ("結果の値", "| 結果 | `反例なし`／`反例あり`", "| 結果 | `反例なし`／`反例あり`／`判定できなかった`"),
    ("前回のモデルの値", "`直さず使った`／`直して使った`", "`直さず使った`"),
]


def findings_problems() -> list[str]:
    """`check-findings-csv.py` の `run_rows` が `モデルの保存` の行を実行の行と読まないか（`抜けた` は読む——陽性対照）。"""
    spec = importlib.util.spec_from_file_location("check_findings_csv", SCRIPTS / "check-findings-csv.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "v1.csv"
        path.write_text("回,日付,結果,条件2〜4,要求の行,決定表の行,テストケース,仕様の行,判断,機能\n"
                        "1,2026-11-01,抜けた,満たす,10,0,5,20,-,-\n"
                        "2,2026-11-14,モデルの保存,-,-,-,-,-,-,-\n", encoding="utf-8")
        runs = module.run_rows(path)
    problems = []
    if "1" not in runs:
        problems.append(f"陽性対照: `抜けた` の行を実行の行と読まない: {runs}")
    if "2" in runs:
        problems.append(f"`モデルの保存` の行を実行の行と読んだ: {runs}")
    return problems


def oo_problems(scripts: Path, cwd: Path, env: dict[str, str]) -> list[str]:
    problems = []
    proc = subprocess.run([sys.executable, "-I", "-OO", str(scripts / TARGET)], capture_output=True, text=True,
                          cwd=cwd, env=env)
    output = proc.stdout + proc.stderr
    if proc.returncode != 2 or "想定外の例外" in output or "Traceback" in output:
        problems.append(f"-OO の引数なし: 終了 {proc.returncode}: {output[-300:]!r}")
    proc = subprocess.run([sys.executable, "-I", "-c", UNEXPECTED_RUNNER, str(scripts / TARGET), "target", "--repo", str(cwd)],
                          capture_output=True, text=True, cwd=cwd, env=env)
    output = proc.stdout + proc.stderr
    if proc.returncode != 2 or "想定外の例外で止まった（ValueError: 試料）" not in output or "Traceback" in output:
        problems.append(f"想定外の例外: 終了 {proc.returncode}: {output[-300:]!r}")
    return problems


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def guard_rows(source: str) -> int:
    """本体の docstring の「守ること」の表のデータの行数。"""
    block = source.split("**守ること**:", 1)[1].split("**守らないもの**", 1)[0]
    return sum(1 for line in block.splitlines() if line.startswith("| ") and not line.startswith("| 守ること") and "---" not in line)


def main() -> int:
    if shutil.which("git") is None:
        print("git が無いので走らせていない（緑ではない）", file=sys.stderr)
        return 2
    source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
    reference = REFERENCE.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        home.mkdir()
        env = sandbox_env(home)

        # 1・2・6: 全部の試料を、写したスクリプトで（リポジトリの外で単体で）回す
        scripts = copy_scripts(base / "scripts")
        work = base / "work"
        work.mkdir()
        results = run_all(scripts, work, env)
        for name, code, text in all_cases():
            got = results.get(name)
            check(f"試料: {name}", got is not None and as_expected(name, got),
                  f"期待 {code}・{text!r} / 実際 {got and got[0]}・{got and got[1][-400:]!r}")

        # 3: 写しのずれ
        for problem in reference_mismatches(source, reference):
            check("tree.md と本体の写し", False, problem)
        for name, before, after in REFERENCE_MUTATIONS:
            if reference.count(before) != 1:
                check(f"崩すと不一致になる: {name}", False, f"崩す箇所が {reference.count(before)} 回現れる")
                continue
            check(f"崩すと不一致になる: {name}", bool(reference_mismatches(source, reference.replace(before, after))))

        # 4: 記録の表の行
        for problem in findings_problems():
            check("check-findings-csv.py の実行の行", False, problem)

        # 5: 想定外の例外と -OO
        for problem in oo_problems(scripts, work, env):
            check("想定外の例外・-OO", False, problem)

        # 変異
        rows = guard_rows(source)
        check("変異の数が「守ること」の行の数以上", len(MUTATIONS) >= rows, f"変異 {len(MUTATIONS)} < 行 {rows}")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            if not as_expected(killer, results.get(killer, (-1, ""))):
                check(f"変異の陽性対照: {name}", False, f"壊す前に試料「{killer}」が期待どおりでない")
                continue
            mutated = copy_scripts(base / f"m{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            mwork = base / f"mw{index}"
            mwork.mkdir()
            got = run_all(mutated, mwork, env, only=killer)[killer]
            check(f"変異が殺されない: {name}", not as_expected(killer, got), f"試料「{killer}」が期待どおりのまま")
        for index, (name, before, after) in enumerate(OO_MUTATIONS):
            if source.count(before) != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {source.count(before)} 回現れる")
                continue
            mutated = copy_scripts(base / f"o{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            check(f"変異が殺されない: {name}", bool(oo_problems(mutated, work, env)))

    if failures:
        for failure in failures:
            print(f"NG: {failure}", file=sys.stderr)
        print(f"失敗 {len(failures)} 件", file=sys.stderr)
        return 1
    print(f"OK: 試料 {len(all_cases())} 件・変異 {len(MUTATIONS) + len(OO_MUTATIONS) + len(REFERENCE_MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
