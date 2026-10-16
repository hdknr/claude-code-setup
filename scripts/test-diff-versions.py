#!/usr/bin/env python3
"""`diff-versions.py`（ある版が前の版から何を足し・変え・消したか）の回帰テスト。

    python3 scripts/test-diff-versions.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。重ね方そのものは `scripts/test-merge-versions.py` が見る。
ここで見るのは**比べ方**:

1. **3 種（Q&A・機能・ファイル）それぞれの追加・変更・削除**が、前の版の時点の全体との比較で出る。削除には
   `removed.csv` の理由が付く。**出力の全行を期待値と突き合わせる。**
2. **同じ中身を置き直しただけのものは変更に数えない。**
3. **v1 は前の版が無いので全部が追加。**
4. **比べる相手は直前の版の時点の全体**——3 版あるとき、v3 の差分に v2 の変更・削除は出ず、`--version 2` の差分に v3 は出ない。
5. **重ねないもの（`feasibility/`・`proposal/`・版でない名前）は差分に出ない。**
6. **比べられないときは比べない**——その版が無い（2。文言は `--version`）・決まりに反する（1）・`docs` が無い（2）。
7. **同じ入力から同じ出力。**
   **1 変更は 1 行**——セルの改行は `\\n` と書き、偽の変更行を作らない（件数と一覧の行数が食い違わない）。
8. **リポジトリの外で単体で動く**——プラグインの `scripts/` を一時ディレクトリに写し、`python3 -I` で走らせる。
9. **決まりの原本（`references/versions.md`）に「版の差分」の節があり、3 つの変化の名前とコマンドが載っている。**

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPTS = PLUGIN / "scripts"
TARGET = "diff-versions.py"
REFERENCE = PLUGIN / "references" / "versions.md"

QA_HEAD = "No,起票元,質問,選択肢,回答,反映先,状態,費用への影響\n"


def q(no: str, question: str, answer: str = "未回答", where: str = "—", state: str = "確認中") -> str:
    return f"{no},要求確定,{question},A: 甲 / B: 乙,{answer},{where},{state},\n"


def spec(*features: tuple[str, str], title: str | None = "注文") -> str:
    data = {"features": [{"id": i, "title": t} for i, t in features]}
    if title is not None:
        data = {"title": title, **data}
    return json.dumps(data, ensure_ascii=False)


V1 = {
    "v1/shared/qa.csv": QA_HEAD + q("Q-001", "質問1", "A（業務部）", "決定表 1 行目", "反映済み") + q("Q-002", "質問2") + q("Q-003", "質問3"),
    "v1/requirements/a.md": "a\n", "v1/requirements/b.md": "b\n", "v1/requirements/c.md": "c\n",
    "v1/spec/spec_ir.json": spec(("F-001", "割引"), ("F-002", "送料")),
}
V2 = {
    # Q-001 は置き直しただけ（同じ中身）・Q-002 は答えが変わった・Q-004 は新しい
    "v2/shared/qa.csv": QA_HEAD + q("Q-001", "質問1", "A（業務部）", "決定表 1 行目", "反映済み")
    + q("Q-002", "質問2", "B（業務部）", "決定表 2 行目", "反映済み") + q("Q-004", "質問4"),
    "v2/requirements/a.md": "a\n", "v2/requirements/b.md": "b2\n", "v2/requirements/d.md": "d\n",
    "v2/spec/spec_ir.json": spec(("F-002", "送料 v2"), ("F-003", "ポイント"), title=None),
    "v2/removed.csv": "種類,対象,理由\nQ&A,Q-003,不要になった\nファイル,requirements/c.md,統合した\n機能,F-001,廃止\n",
    # 重ねないもの
    "v2/feasibility/estimate.csv": "x\n", "v2/proposal/01.md": "x\n", "index.md": "x\n",
}
V2_EXPECTED = """v2 の差分（v1 の時点の全体との比較）
Q&A: 追加 1・変更 1・削除 1
  変更 Q-002 質問2
  追加 Q-004 質問4
  削除 Q-003 質問3（理由: 不要になった）
機能: 追加 1・変更 1・削除 1
  変更 F-002 送料 v2
  追加 F-003 ポイント
  削除 F-001 割引（理由: 廃止）
ファイル: 追加 1・変更 1・削除 1
  変更 requirements/b.md
  追加 requirements/d.md
  削除 requirements/c.md（理由: 統合した）
"""
V3 = {
    # v3 は v2 で変えた b.md をさらに変え、v2 で足した F-003 を消す
    "v3/requirements/b.md": "b3\n",
    "v3/removed.csv": "種類,対象,理由\n機能,F-003,やめた\n",
}


class Result:
    def __init__(self, code: int, output: str, again: str):
        self.code, self.output, self.again = code, output, again


def run(scripts: Path, docs: Path, extra: list[str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-I", str(scripts / TARGET), str(docs), *extra],
                          capture_output=True, text=True, cwd=docs.parent)
    return proc.returncode, proc.stdout + proc.stderr


# (名前, 試料の木（None ならディレクトリを作らない）, 引数, 判定)
CASES: list[tuple[str, dict | None, list[str], Callable[[Result], bool]]] = [
    ("3 種の追加・変更・削除", {**V1, **V2}, [], lambda r: r.code == 0 and r.output == V2_EXPECTED),
    ("置き直しは変更に数えない", {**V1, **V2}, [],
     lambda r: r.code == 0 and "Q-001" not in r.output and "requirements/a.md" not in r.output),
    ("v1 は全部が追加", {**V1, **V2}, ["--version", "1"],
     lambda r: r.code == 0 and r.output.startswith("v1 の差分（前の版が無いので、全部が追加）")
     and "Q&A: 追加 3・変更 0・削除 0" in r.output and "ファイル: 追加 3・変更 0・削除 0" in r.output
     and "  追加 F-002 送料\n" in r.output),
    ("v3 は v2 の時点と比べる", {**V1, **V2, **V3}, [],
     lambda r: r.code == 0 and r.output.startswith("v3 の差分（v2 の時点の全体との比較）")
     and "  変更 requirements/b.md\n" in r.output and "  削除 F-003 ポイント（理由: やめた）\n" in r.output
     and "Q&A: 追加 0・変更 0・削除 0" in r.output and "F-001" not in r.output and "c.md" not in r.output),
    ("版を指定すると後の版を見ない", {**V1, **V2, **V3}, ["--version", "2"], lambda r: r.code == 0 and r.output == V2_EXPECTED),
    ("重ねないものは差分に出ない", {**V1, **V2}, [],
     lambda r: r.code == 0 and "feasibility" not in r.output and "proposal" not in r.output and "index.md" not in r.output),
    ("同じ入力から同じ出力", {**V1, **V2, **V3}, [], lambda r: r.code == 0 and r.output == r.again),
    ("その版が無いと比べない", {**V1, **V2}, ["--version", "3"],
     lambda r: r.code == 2 and "--version 3: v3 が無い" in r.output and "--upto" not in r.output and "比べていない" in r.output),
    ("決まりに反すると比べない", {**V1, **V2, "v2/removed.csv": "種類,対象,理由\n機能,F-999,誤記\n"}, [],
     lambda r: r.code == 1 and "F-999" in r.output and "比べていない" in r.output and "差分（" not in r.output),
    ("docs が無いと比べない", None, [], lambda r: r.code == 2 and "ディレクトリが無い" in r.output),
    ("--version の誤り", {**V1}, ["--version", "0"], lambda r: r.code == 2 and "1 以上の整数" in r.output),
    # セルの改行で偽の変更行を作らない（1 変更 = 1 行。件数と一覧の行数が食い違わない）
    ("セルの改行は 1 行に留める",
     {**V1, "v1/shared/qa.csv": V1["v1/shared/qa.csv"] + 'Q-005,要求確定,"一行目\n  追加 Q-999 偽",A: 甲 / B: 乙,未回答,—,確認中,\n'},
     ["--version", "1"],
     lambda r: r.code == 0 and "Q&A: 追加 4・変更 0・削除 0" in r.output
     and sum(line.startswith("  追加 Q-") for line in r.output.splitlines()) == 4
     and "  追加 Q-005 一行目\\n  追加 Q-999 偽\n" in r.output),
]

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("変更を見ない", "        elif before[key] != value:\n", "        elif False:\n", "3 種の追加・変更・削除"),
    ("置き直しも変更に数える", "        elif before[key] != value:\n", "        else:\n", "置き直しは変更に数えない"),
    ("削除を見ない", "        if key not in after:\n", "        if False:\n", "3 種の追加・変更・削除"),
    ("直前の版でなく v1 と比べる", "merge_versions.merge(docs, number - 1)", "merge_versions.merge(docs, 1)",
     "v3 は v2 の時点と比べる"),
    ("後の版まで重ねる", "merge_versions.merge(docs, version)\n", "merge_versions.merge(docs, None)\n",
     "版を指定すると後の版を見ない"),
    ("削除の理由を添えない", 'change.reason = reasons.get((kind, change.key), "")', 'change.reason = ""',
     "3 種の追加・変更・削除"),
    ("理由を v1 から読む", "removal_reasons(versions[number - 1][1])", "removal_reasons(versions[0][1])",
     "3 種の追加・変更・削除"),
    ("ファイルを比べない", "    diff.changes[merge_versions.KIND_FILE] = compare_maps(dict(sorted(before.files.items())),\n",
     "    diff.changes[merge_versions.KIND_FILE] = [] or compare_maps({},\n", "3 種の追加・変更・削除"),
    ("範囲外の文言を言い直さない", 'str(e).replace("--upto", "--version", 1)', "str(e)", "その版が無いと比べない"),
    ("改行をそのまま出す", 'return text.replace("\\r\\n", "\\n")', 'return text\n    return text.replace("\\r\\n", "\\n")',
     "セルの改行は 1 行に留める"),
    ("決まりに反しても比べる", "    if problems:\n        return problems, None\n    number",
     "    if False:\n        return problems, None\n    number", "決まりに反すると比べない"),
]

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


def run_case(scripts: Path, root: Path, tree: dict | None, extra: list[str]) -> Result:
    assert_in_tmp(root)
    root.mkdir(parents=True)
    docs = root / "docs"
    for path, text in (tree or {}).items():
        dest = docs / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    code, output = run(scripts, docs, extra)
    return Result(code, output, run(scripts, docs, extra)[1])


def as_expected(name: str, result: Result) -> bool:
    return next(case for case in CASES if case[0] == name)[3](result)


def copy_scripts(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def check_reference() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    check("references/versions.md に「版の差分」の節が無い", "\n## 版の差分\n" in text)
    section = text.split("\n## 版の差分\n", 1)[-1].split("\n## ", 1)[0]
    for word in ("追加", "変更", "削除", "scripts/diff-versions.py"):
        check(f"references/versions.md の「版の差分」に {word} が無い", word in section)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="diff-versions-test-") as tmp:
        tmp_path = Path(tmp)
        scripts = copy_scripts(tmp_path / "scripts")
        for index, (name, tree, extra, _) in enumerate(CASES):
            result = run_case(scripts, tmp_path / f"case{index}", tree, extra)
            check(f"試料が期待どおりでない: {name}", as_expected(name, result), f"exit={result.code}\n{result.output}")

        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            count = source.count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = copy_scripts(tmp_path / f"mut{index}")
            (mutated / TARGET).write_text(source.replace(before, after), encoding="utf-8")
            _, tree, extra, _ = next(case for case in CASES if case[0] == killer)
            result = run_case(mutated, tmp_path / f"mutwork{index}", tree, extra)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(killer, result), result.output[-300:])
    check_reference()

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件・原本の照合")
    return 0


if __name__ == "__main__":
    sys.exit(main())
