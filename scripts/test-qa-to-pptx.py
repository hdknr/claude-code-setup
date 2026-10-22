#!/usr/bin/env python3
"""`qa-to-pptx.py` の回帰テスト。

    python3 scripts/test-qa-to-pptx.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-qa-csv.py` と同じ形。

見るもの:

1. **PPTX の部品が揃い、どれも XML として読める**——`[Content_Types].xml` が先頭、
   すべての関係（`.rels`）の行き先が実在し、すべてのスライドに型の宣言がある。
2. **回答待ち・未反映・暫定反映の行がすべて載り、反映済みの行は載らない**——番号・質問・選択肢を、
   **段落の単位で**当てる（選択肢が 1 段落に潰れていても部分一致では通ってしまうので）。
3. **XML に書けない文字で壊れない**（`&` `<` `"` と制御文字）。**改行でない改行
   （U+2028）で段落を割らない。**
4. **列検査を通らない表からは作らず、既存の出力に触らない。** 引数の誤り・読めない表は 2、
   書けない出力先は 3 で、**一時ファイルを残さない。**
5. **出力が入力と引数だけで決まる**——時刻をまたいで 2 回作り、バイトが一致する。
6. **リポジトリの外で単体で動く**——2 本のスクリプトだけを一時ディレクトリに写し、`python3 -I` で走らせる。

**見ないもの**: PowerPoint・LibreOffice で開けること（CI に無い。周の検証で手で当てる）、
文字がはみ出さないこと（本体の docstring の「守らないもの」）。

**このテストは実環境を触らない。** 試料と出力はすべて一時ディレクトリに書く。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに全部の観測が期待どおりなら失格**とする。
変異ごとに、**壊す箇所が本体にちょうど 1 回現れること**を先に確かめる。
"""
from __future__ import annotations

import csv
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
SCRIPT = SCRIPTS / "qa-to-pptx.py"
CHECKER = SCRIPTS / "check-qa-csv.py"

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
HEADER = ["No", "起票元", "質問", "選択肢", "回答", "反映先", "状態", "費用への影響"]

ODD_QUESTION = "特殊文字 & <タグ> \"引用\"\x0b は？ 同じ段落"
ROWS = [
    ["Q-001", "要求確定（決定表）", "シルバー会員で 10000 円未満のとき、割引は？",
     "A: 割引なし（0%） / B: 3% 割引", "A（業務部が回答）", "決定表 4 行目", "反映済み", ""],
    ["Q-002", "仕様レビュー（Red Team）", "決済の途中で通信が切れたとき、注文は？",
     "A: 取り消す / B: 決済待ちで残す", "未回答", "—", "確認中", ""],
    ["Q-003", "要求確定", "回答済みだが未反映の質問",
     "A: はい / B: いいえ / C: 保留", "B（業務部が回答）", "—", "確認中", ""],
    ["Q-004", "実現性・コスト", ODD_QUESTION,
     "A: はい & 続ける / B: <いいえ>", "未回答", "—", "確認中", "B は月額が約 2 倍"],
    ["Q-005", "要求確定", "2 行の質問の 1 行目\n2 行目",
     "A: 一 / B: 二", "未回答", "—", "確認中", ""],
    ["Q-006", "要求確定", "暫定で採った質問",
     "A: 上限なし / B: 5000 円まで", "A（推奨案を暫定で採用。業務部 2026-10-21 の指示）", "決定表 7 行目", "暫定反映", ""],
]
# 載る行（反映済みでない行）。暫定反映も載る（#325）
PENDING = [r for r in ROWS if r[6] != "反映済み"]
PROVISIONAL = [r for r in ROWS if r[6] == "暫定反映"]
UNSETTLED = [r for r in PENDING if r not in PROVISIONAL]
DONE = [r for r in ROWS if r[6] == "反映済み"]

failures: list[str] = []


def check(name: str, cond: bool) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    if not cond:
        failures.append(name)


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert not resolved.is_relative_to(REAL_REPO), "試料が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "試料がテンポラリの外"


def write_csv(path: Path, rows: list[list[str]]) -> Path:
    assert_in_tmp(path)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(HEADER)
    w.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")
    return path


def load(script: Path):
    spec = importlib.util.spec_from_file_location(f"q2p_{id(script)}_{time.time_ns()}", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod, *args: str) -> int:
    """本体の `main` を呼ぶ。標準出力・エラーは捨てる（集計だけ見る）。"""
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return mod.main(list(args))


def slide_paragraphs(pptx: Path) -> tuple[list[list[str]], list[str]]:
    """(スライドごとの段落の文字列, 問題の一覧) を返す。部品の検査もここで行う。"""
    problems = []
    with zipfile.ZipFile(pptx) as z:
        names = z.namelist()
        if names[0] != "[Content_Types].xml":
            problems.append(f"先頭が [Content_Types].xml でない: {names[0]}")
        trees = {}
        for name in names:
            try:
                trees[name] = ET.fromstring(z.read(name))
            except ET.ParseError as e:
                problems.append(f"XML として読めない: {name}: {e}")
        if problems:
            return [], problems
        types = trees["[Content_Types].xml"]
        declared = {o.get("PartName") for o in types if o.get("PartName")}
        for name, tree in trees.items():
            if not name.endswith(".rels"):
                continue
            base = Path(name).parent.parent  # `ppt/slides/_rels/x.rels` → `ppt/slides`
            for rel in tree:
                target = os.path.normpath(base / rel.get("Target")).replace(os.sep, "/")
                if target not in names:
                    problems.append(f"関係の行き先が無い: {name} → {target}")
        slides = sorted((n for n in names if n.startswith("ppt/slides/slide")),
                        key=lambda n: int(n.removeprefix("ppt/slides/slide").removesuffix(".xml")))
        out = []
        for name in slides:
            if f"/{name}" not in declared:
                problems.append(f"型の宣言が無い: {name}")
            out.append(["".join(t.text or "" for t in p.iter(f"{A}t")) for p in trees[name].iter(f"{A}p")])
        pres = trees["ppt/presentation.xml"]
        ids = [e for e in pres.iter() if e.tag.endswith("}sldId")]
        if len(ids) != len(slides):
            problems.append(f"sldIdLst が {len(ids)} 件、スライドが {len(slides)} 件")
    return out, problems


def observe(mod, base: Path) -> dict:
    """1 つの本体に対する観測を全部まとめる（変異テストでも同じ観測を使う）。"""
    obs: dict = {}
    good = write_csv(base / "good.csv", ROWS)
    out = base / "out.pptx"
    obs["rc"] = run(mod, str(good), str(out), "--subtitle", "2026-10-13")
    if obs["rc"] == 0 and out.exists():
        slides, problems = slide_paragraphs(out)
        obs["problems"] = problems
        flat = [p for s in slides for p in s]
        obs["slides"] = len(slides)
        obs["pending_on_slides"] = all(
            any(p.startswith(f"{r[0]}（") for p in flat) for r in PENDING)
        obs["questions_as_paragraphs"] = all(
            all(line in flat for line in r[2].replace("\x0b", "").split("\n")) for r in PENDING)
        obs["options_as_paragraphs"] = all(
            all(o in flat for o in r[3].split(" / ")) for r in PENDING)
        obs["done_absent"] = not any(r[0] in p or r[2] in p for r in DONE for p in flat)
        # 未反映と暫定を分けて書く（#325）——表紙の件数・一覧の印・各問の回答の見出し
        cover = slides[0] if slides else []
        obs["cover_counts"] = (f"回答待ち・未反映の質問: {len(UNSETTLED)} 件" in cover
                               and f"暫定の回答（反映済み・確認待ち）: {len(PROVISIONAL)} 件" in cover)
        obs["index_marks"] = sorted(p.split("  ")[0] for p in flat if "（暫定）  " in p)
        questions = [p for sl in slides if sl and sl[0].startswith("Q-") for p in sl]
        obs["answer_labels"] = sorted(p for p in questions if p.startswith(("回答（未反映）: ", "暫定の回答（反映済み・確認待ち）: ")))
        # 決定性: 時刻をまたいで作り直す（zip の時刻を固定していないと、ここで違う）
        time.sleep(2.1)
        again = base / "again.pptx"
        run(mod, str(good), str(again), "--subtitle", "2026-10-13")
        obs["deterministic"] = again.exists() and again.read_bytes() == out.read_bytes()

    bad = write_csv(base / "bad.csv", ROWS + [["Q-006", "未知の起票元", "q", "A: x", "未回答", "—", "確認中", ""]])
    kept = base / "kept.pptx"
    kept.write_bytes(b"OLD")
    obs["bad_rc"] = run(mod, str(bad), str(kept))
    obs["bad_kept"] = kept.read_bytes() == b"OLD"

    # 例外は観測として残す（**変異が別の理由で落ちたのを「殺せた」と数えない**ため、
    # 1 つの観測の例外で残りの観測を止めない）
    try:
        obs["missing_rc"] = run(mod, str(base / "nope.csv"), str(base / "x.pptx"))
    except Exception as e:  # noqa: BLE001
        obs["missing_rc"] = f"例外: {type(e).__name__}"
    obs["usage_rc"] = run(mod, str(good))

    # 出力先が入力の表と同じなら書かない（正本の表が PPTX に置き換わって戻せない。#216 の Verifier）
    same = write_csv(base / "same.csv", ROWS)
    before = same.read_bytes()
    obs["same_rc"] = run(mod, str(same), str(same))
    obs["same_kept"] = same.read_bytes() == before

    # 出力先の親が無ければ作る（既定の出力先 `build/req-loop/` は初回には無い。#216 の /code-review）
    nested = base / "build" / "req-loop" / "qa-review.pptx"
    obs["nested_rc"] = run(mod, str(good), str(nested))
    obs["nested_made"] = nested.is_file()

    blocked = base / "is-a-dir.pptx"
    blocked.mkdir(exist_ok=True)
    obs["unwritable_rc"] = run(mod, str(good), str(blocked))
    obs["no_tmp_left"] = not list(base.glob(".is-a-dir.pptx.*"))
    return obs


EXPECTED = {
    "rc": 0, "problems": [], "slides": 1 + 1 + len(PENDING),
    "pending_on_slides": True, "questions_as_paragraphs": True, "options_as_paragraphs": True,
    "done_absent": True, "deterministic": True, "cover_counts": True,
    "index_marks": [f"{r[0]}（暫定）" for r in PROVISIONAL],
    "answer_labels": sorted([f"回答（未反映）: {r[4]}" for r in UNSETTLED if r[4] != "未回答"]
                            + [f"暫定の回答（反映済み・確認待ち）: {r[4]}" for r in PROVISIONAL]),
    "bad_rc": 1, "bad_kept": True, "missing_rc": 2, "usage_rc": 2,
    "unwritable_rc": 3, "no_tmp_left": True,
    "same_rc": 2, "same_kept": True, "nested_rc": 0, "nested_made": True,
}

MUTATIONS: list[tuple[str, str, str]] = [
    ("反映済みで絞らない", 'return code, lines, [row for row in rows if row["状態"].strip() != qa.DONE]',
     "return code, lines, rows"),
    ("暫定を見分けない", 'return row["状態"].strip() == qa.PROVISIONAL', "return False"),
    ("表紙の件数を分けない", 'body = lines_of(f"回答待ち・未反映の質問: {len(rows) - settled} 件", 2400)',
     'body = lines_of(f"回答待ち・未反映の質問: {len(rows)} 件", 2400)'),
    ("列検査を飛ばす", "    code, lines = qa.check(path)", "    code, lines = 0, []"),
    ("XML の特殊文字を逃がさない", 'return escape(INVALID_XML.sub("", text))', 'return INVALID_XML.sub("", text)'),
    ("制御文字を落とさない", 'return escape(INVALID_XML.sub("", text))', "return escape(text)"),
    ("選択肢を割らない", 'for option in row["選択肢"].split(qa.OPTION_SEPARATOR):', 'for option in [row["選択肢"]]:'),
    ("splitlines で割る", 'return text.replace("\\r\\n", "\\n").replace("\\r", "\\n").split("\\n")',
     "return text.splitlines() or [\"\"]"),
    ("zip の時刻を固定しない", "info = zipfile.ZipInfo(name, date_time=ZIP_TIME)",
     "info = zipfile.ZipInfo(name, date_time=time.localtime()[:6])"),
    ("一時ファイルを消さない", "        Path(tmp).unlink(missing_ok=True)\n", ""),
    ("入力と同じ出力先を拒まない", "    if out.exists() and src.exists() and out.samefile(src):",
     "    if False:"),
    ("出力先の親を作らない", "    out.parent.mkdir(parents=True, exist_ok=True)\n", ""),
]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        assert_in_tmp(base)

        print("本物の本体")
        (base / "real").mkdir()
        obs = observe(load(SCRIPT), base / "real")
        for key, want in EXPECTED.items():
            check(f"{key} = {want!r}（実際: {obs.get(key)!r}）", obs.get(key) == want)

        print("\n確認中が 0 件・一覧が 2 枚に割れる")
        mod = load(SCRIPT)
        empty = write_csv(base / "empty.csv", [ROWS[0]])
        out = base / "empty.pptx"
        rc = run(mod, str(empty), str(out))
        slides, problems = slide_paragraphs(out) if rc == 0 else ([], ["作られない"])
        check("載せる行が 0 件でも作り、そう書く",
              rc == 0 and not problems and any("載せる質問はありません" in p for s in slides for p in s))
        many = [[f"Q-{100 + i}", "要求確定", f"質問 {i}", "A: x / B: y", "未回答", "—", "確認中", ""]
                for i in range(12)]
        out = base / "many.pptx"
        rc = run(mod, str(write_csv(base / "many.csv", many)), str(out))
        slides, problems = slide_paragraphs(out) if rc == 0 else ([], ["作られない"])
        index = [s for s in slides if s and s[0].startswith("一覧")]
        check("一覧が 2 枚に割れ、12 件すべてが一覧に載る",
              not problems and len(index) == 2
              and all(any(p.startswith(f"Q-{100 + i} ") for s in index for p in s) for i in range(12)))

        print("\nリポジトリの外で単体で動く")
        alone = base / "alone"
        alone.mkdir()
        shutil.copy(SCRIPT, alone / SCRIPT.name)
        shutil.copy(CHECKER, alone / CHECKER.name)
        r = subprocess.run([sys.executable, "-I", str(alone / SCRIPT.name),
                            str(base / "real" / "good.csv"), str(alone / "o.pptx")],
                           capture_output=True, text=True, cwd=alone)
        check("python3 -I で 0 で終わり、出力がある", r.returncode == 0 and (alone / "o.pptx").exists())

        print("\n変異テスト（壊したのに期待どおりなら失格）")
        source = SCRIPT.read_text(encoding="utf-8")
        for n, (name, needle, replacement) in enumerate(MUTATIONS):
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}（{source.count(needle)} 箇所）", False)
                continue
            d = base / f"mut-{n}"
            d.mkdir()
            shutil.copy(CHECKER, d / CHECKER.name)
            mutated = source.replace(needle, replacement, 1)
            if "time.localtime" in replacement:
                mutated = mutated.replace("import tempfile\n", "import tempfile\nimport time\n", 1)
            (d / SCRIPT.name).write_text(mutated, encoding="utf-8")
            work = d / "work"
            work.mkdir()
            try:
                got = observe(load(d / SCRIPT.name), work)
                diff = [k for k, v in EXPECTED.items() if got.get(k) != v]
            except Exception as e:  # noqa: BLE001
                diff = [f"例外: {type(e).__name__}"]
            check(f"変異を殺せる: {name}（違った観測: {', '.join(diff) or 'なし'}）", bool(diff))

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("PPTX 生成のテスト: すべて合格")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
