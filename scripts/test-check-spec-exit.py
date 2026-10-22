#!/usr/bin/env python3
"""`check-spec-exit.py` の回帰テスト。

    python3 scripts/test-check-spec-exit.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-qa-csv.py` と同じ形。

見るもの:

1. **条件 1 を満たさない形を、理由つきで落とす**（仕様に反映した状態でない行・未決定の印・列検査を通らない表）。
   **暫定反映の行は止めない**（資料に載る行とは別の定義。#325）。
2. **満たす形を通す**（陽性対照。`未定義` や `mastodon` のような印でない語で落ちないこと）。
3. **判定できない形を 0 にしない**（仕様のディレクトリが無い・空・Q&A 表が読めない）。
4. **0 で終わっても「抜けた」とは言わない**——出力に「条件 2〜5 は判定していない」が出る。
5. **本体の定数が `references/spec-exit.md` の「未決定の印」の表と一致する**（写しのずれ）。
6. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる（届いていない変異は、
穴が無くても緑になるので）。
"""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "check-spec-exit.py"
REFERENCE = PLUGIN / "references" / "spec-exit.md"

HEADER = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"
DONE_ROW = "Q-001,仕様レビュー（Red Team）,通信が切れたら？,A: 取り消す / B: 残す,A（業務部が回答）,spec/order.md,反映済み,\n"
OPEN_ROW = "Q-002,仕様レビュー（Domain Checker）,端数は？,A: 切り捨て / B: 四捨五入,未回答,—,確認中,\n"
# 回答はあるが未反映——これも仕様に反映した状態でない
ANSWERED_ROW = "Q-003,仕様レビュー（Formal Checker）,上限は？,A: 拒否 / B: 切り詰める,B（業務部が回答）,—,確認中,\n"
# 暫定の回答で反映した——仕様には反映済みなので条件 1 を止めない（#325）
PROVISIONAL_ROW = "Q-005,仕様レビュー（Red Team）,上限は？,A: なし / B: 5000 円,A（推奨案を暫定で採用。業務部 2026-10-21 の指示）,spec/order.md,暫定反映,\n"
BAD_ROW = "Q-004,仕様レビュー,選択肢が 1 つ,A: これだけ,未回答,—,確認中,\n"
CLEAN_SPEC = "# 注文\n\n未定義の状態に遷移しない。\nmastodon のような語も、TODOS も印ではない。\n"

# (名前, qa.csv の中身（None なら作らない）, {仕様の相対パス: 中身}（None ならディレクトリを作らない）,
#  期待する終了コード, 出力に含まれるべき文字列)
CASES: list[tuple[str, str | bytes | None, dict[str, str | bytes] | None, int, str]] = [
    ("満たす", HEADER + DONE_ROW, {"order.md": CLEAN_SPEC}, 0, "条件 2〜5 は判定していない"),
    ("見出しだけの表", HEADER, {"order.md": CLEAN_SPEC}, 0, "条件 1 を満たす"),
    ("確認中の行", HEADER + DONE_ROW + OPEN_ROW, {"order.md": CLEAN_SPEC}, 1, "Q-002: 状態が 確認中"),
    ("暫定反映は止めない", HEADER + DONE_ROW + PROVISIONAL_ROW, {"order.md": CLEAN_SPEC}, 0,
     "暫定反映の行（仕様には反映済み・利用者の確認待ち）: 1 件"),
    ("暫定反映と確認中", HEADER + PROVISIONAL_ROW + OPEN_ROW, {"order.md": CLEAN_SPEC}, 1, "Q-002: 状態が 確認中"),
    ("回答はあるが未反映", HEADER + ANSWERED_ROW, {"order.md": CLEAN_SPEC}, 1, "Q-003: 状態が 確認中"),
    ("列検査を通らない表", HEADER + BAD_ROW, {"order.md": CLEAN_SPEC}, 1, "列検査を通らない"),
    ("TBD", HEADER, {"order.md": CLEAN_SPEC + "リトライ回数は TBD。\n"}, 1, "order.md:5: 未決定の印 TBD"),
    ("小文字の todo", HEADER, {"order.md": "- todo: 上限\n"}, 1, "未決定の印 todo"),
    ("日本語に挟まれた TODO", HEADER, {"order.md": "割引はTODOとする\n"}, 1, "未決定の印 TODO"),
    ("未定", HEADER, {"order.md": "割引: 未定\n"}, 1, "未決定の印 未定"),
    ("未定義と未定が同じ行", HEADER, {"order.md": "未定義の値は未定\n"}, 1, "未決定の印 未定"),
    ("要確認", HEADER, {"order.md": "端数（要確認）\n"}, 1, "未決定の印 要確認"),
    ("入れ子のファイル", HEADER, {"order.md": CLEAN_SPEC, "formal/rules.py": "# TODO 下限\n"}, 1,
     "rules.py:1: 未決定の印 TODO"),
    ("印が無い行の後ろに印", HEADER, {"order.md": CLEAN_SPEC, "flow.md": "a\nb\nc TBD\n"}, 1, "flow.md:3"),
    ("読めないファイルは件数を出して通す", HEADER, {"order.md": CLEAN_SPEC, "fig.png": b"\x89PNG\xff\xfe"}, 0,
     "見なかったファイル（読めない・UTF-8 でない）: 1 件"),
    # 見ていない仕様を「印 0 件」と言わない（UTF-16 で書いた仕様の TBD を見落として 0 にしていた）
    ("図以外に読めない仕様", HEADER, {"order.md": "割引は TBD\n".encode("utf-16")}, 2, "図以外に読めないファイルが 1 件"),
    # 読める別ファイルが混ざっても同じ（全部読めないときだけ 2 にしていた）
    ("読めない仕様と読める README", HEADER,
     {"order.md": "割引は TBD\n".encode("utf-16"), "README.md": "目次\n"}, 2, "図以外に読めないファイルが 1 件"),
    # ASCII だけの UTF-16 は UTF-8 として復号できてしまう（NUL は有効）。NUL で読めない側に数える
    ("BOM の無い ASCII の UTF-16", HEADER, {"a.md": "Status: TBD\n".encode("utf-16-le")}, 2,
     "図以外に読めないファイルが 1 件"),
    ("図だけ", HEADER, {"fig.png": b"\x89PNG\xff\xfe"}, 2, "どの仕様も読めなかった"),
    # 読めないファイルがあっても、印が見つかれば満たさないことは確か
    ("読めない仕様と印のある仕様", HEADER,
     {"order.md": "割引は TBD\n".encode("utf-16"), "flow.md": "TODO\n"}, 1, "flow.md:1: 未決定の印 TODO"),
    # 全角の英字は IGNORECASE では半角にならない
    ("全角の ＴＢＤ", HEADER, {"order.md": "仕様はＴＢＤ。\n"}, 1, "未決定の印 TBD"),
    ("ドット始まりは見ない", HEADER, {"order.md": CLEAN_SPEC, ".cache/x.md": "TODO\n"}, 0, "条件 1 を満たす"),
    ("仕様のディレクトリが無い", HEADER, None, 2, "ディレクトリが無い"),
    ("仕様が空", HEADER, {}, 2, "ファイルが 1 つも無い"),
    ("ドット始まりしか無い", HEADER, {".keep": ""}, 2, "ファイルが 1 つも無い"),
    ("Q&A 表が無い", None, {"order.md": CLEAN_SPEC}, 2, "Q&A 表を読めない"),
    ("Q&A 表が UTF-8 でない", b"\xff\xfe\x00", {"order.md": CLEAN_SPEC}, 2, "Q&A 表を読めない"),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("反映済みでない行を見ない", "for row in pending:", "for row in []:", "確認中の行"),
    ("暫定反映を反映した状態に数えない", "not in pptx.qa.REFLECTED", "!= pptx.qa.DONE", "暫定反映は止めない"),
    ("資料に載る行で数える", "not in pptx.qa.REFLECTED", "not in ()", "暫定反映は止めない"),
    ("暫定の件数を出さない", "== pptx.qa.PROVISIONAL]", "== None]", "暫定反映は止めない"),
    ("列検査の失敗を見ない", "    if code:\n        problems += lines", "    if False:\n        problems += lines",
     "列検査を通らない表"),
    ("読めない表を 2 にしない", "if code == 2:", "if False:", "Q&A 表が無い"),
    ("大文字・小文字を区別する", "re.compile(\"|\".join(parts), re.IGNORECASE)", "re.compile(\"|\".join(parts))",
     "小文字の todo"),
    ("英字の印を部分一致で当てる", "        if marker.isascii():", "        if False:", "満たす"),
    ("英字の印の前の境界を広げる", r'rf"(?<![A-Za-z0-9_]){re.escape(marker)}(?![A-Za-z0-9_])"',
     r'rf"\b{re.escape(marker)}(?![A-Za-z0-9_])"', "日本語に挟まれた TODO"),
    ("未定義を伏せない", "            line = line.replace(word, \"\\0\" * len(word))", "            pass", "満たす"),
    ("伏せたら行ごと飛ばす", "            line = line.replace(word, \"\\0\" * len(word))",
     "            line = \"\" if word in line else line", "未定義と未定が同じ行"),
    ("ディレクトリが無くても進む", "    if not spec_dir.is_dir():", "    if False:", "仕様のディレクトリが無い"),
    ("空の仕様を通す", "    if not files:", "    if False:", "仕様が空"),
    ("図だけでも通す", "    if len(unread) == len(files):", "    if False:", "図だけ"),
    ("図以外の読めないファイルも通す", "    if not_figures:", "    if False:", "読めない仕様と読める README"),
    ("NUL を含むファイルも読む", '        if "\\0" in text:', "        if False:", "BOM の無い ASCII の UTF-16"),
    ("全角を正規化しない", '        line = unicodedata.normalize("NFKC", line)\n', "", "全角の ＴＢＤ"),
    ("読めないファイルを印より先に見る", "    if problems:\n        return 1",
     "    if problems and not unread:\n        return 1", "読めない仕様と印のある仕様"),
    ("ドット始まりも見る", "        if any(part.startswith(\".\") for part in path.relative_to(root).parts):",
     "        if False:", "ドット始まりは見ない"),
    ("入れ子を見ない", 'root.rglob("*")', 'root.glob("*")', "入れ子のファイル"),
    ("行番号を 0 から数える", "enumerate(text.splitlines(), start=1)", "enumerate(text.splitlines())", "TBD"),
    ("TBD を印から外す", 'MARKERS = ("TBD", "TODO", "未定", "要確認")', 'MARKERS = ("TODO", "未定", "要確認")', "TBD"),
    ("満たしても但し書きを出さない", '        "**これだけでは抜けていない**——条件 2〜5 は判定していない（references/spec-exit.md）",\n',
     "", "満たす"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def build_case(root: Path, qa: str | bytes | None, spec: dict[str, str | bytes] | None) -> tuple[Path, Path]:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    qa_path = root / "qa.csv"
    if isinstance(qa, bytes):
        qa_path.write_bytes(qa)
    elif qa is not None:
        qa_path.write_text(qa, encoding="utf-8")
    spec_dir = root / "spec"
    if spec is not None:
        spec_dir.mkdir()
        for rel, body in spec.items():
            path = spec_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(body, bytes):
                path.write_bytes(body)
            else:
                path.write_text(body, encoding="utf-8")
    return qa_path, spec_dir


def run_all(scripts: Path, work: Path) -> dict[str, tuple[int, str]]:
    results = {}
    for index, (name, qa, spec, _, _) in enumerate(CASES):
        qa_path, spec_dir = build_case(work / f"case{index}", qa, spec)
        proc = subprocess.run(
            [sys.executable, "-I", str(scripts / TARGET), str(qa_path), str(spec_dir)],
            capture_output=True, text=True, cwd=work,
        )
        results[name] = (proc.returncode, proc.stdout + proc.stderr)
    return results


def as_expected(name: str, result: tuple[int, str]) -> bool:
    expected = next(case for case in CASES if case[0] == name)
    return result[0] == expected[3] and expected[4] in result[1]


def reference_markers(markdown: str) -> tuple[list[str], list[str]]:
    """「未決定の印」の節の表のセルと、「印に当たらない」と書いた語を返す。"""
    section = markdown.split("## 未決定の印", 1)[1].split("\n## ", 1)[0]
    markers = re.findall(r"^\| `([^`]+)` \|$", section, flags=re.MULTILINE)
    not_markers = re.findall(r"\*\*`([^`]+)` は印に当たらない\*\*", section)
    return markers, not_markers


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="spec-exit-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        results = run_all(scripts, tmp_path / "work")
        for name, result in results.items():
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result[0]} {result[1][-300:]}")

        # references との突き合わせ
        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")
        markers, not_markers = reference_markers(reference)
        code_markers = re.search(r"^MARKERS = (\(.*\))$", source, flags=re.MULTILINE)
        code_not = re.search(r"^NOT_MARKERS = (\(.*\))$", source, flags=re.MULTILINE)
        check("本体に MARKERS が見つからない", code_markers is not None)
        check("本体に NOT_MARKERS が見つからない", code_not is not None)
        if code_markers and code_not:
            check("MARKERS が references/spec-exit.md の表と違う",
                  list(ast.literal_eval(code_markers.group(1))) == markers, f"{code_markers.group(1)} vs {markers}")
            check("NOT_MARKERS が references/spec-exit.md と違う",
                  list(ast.literal_eval(code_not.group(1))) == not_markers, f"{code_not.group(1)} vs {not_markers}")
        check("references から印を 1 つも読めない（読み方が壊れている）", len(markers) >= 2, str(markers))

        # 突き合わせ自体の陽性対照: 写しを崩すと不一致になる
        broken = reference.replace("| `要確認` |", "| `要検討` |")
        check("references の写しを崩しても不一致にならない", reference_markers(broken)[0] != markers)

        # 変異テスト
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            mutated_results = run_all(mutated, tmp_path / f"mutwork{index}")
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）",
                  not as_expected(killer, mutated_results[killer]), mutated_results[killer][1][-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
