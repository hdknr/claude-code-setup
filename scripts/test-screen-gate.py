#!/usr/bin/env python3
"""`screen-gate.py`（spec-loop の画面の表の関門。#1097）と、それを条件 1 に入れる `check-spec-exit.py` の回帰テスト。

    python3 scripts/test-screen-gate.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。一時ディレクトリに `plugins/spec-loop/`（本物の `.claude-plugin/` と `scripts/` の写し）を置き、
試料に応じて隣に `plugins/screen-spec/`（本物の写し）を置く・置かない・偽物を名指す。正本の試料は screen-spec の `scripts/test-check-screens.py` の
`base()`（正しく書いた小さな画面の表）を読み込み、Q&A を全部 `反映済み` にして使う（試料の形を写さない）。

見るもの:

1. **#1097 の受入基準**——画面の表も screen-spec も無い正本で何も出さずに 0（回帰。`check-spec-exit.py` は `--docs` の有無で同じ出力）・
   画面の表があって screen-spec が無ければ 4（`check-spec-exit.py --docs` は 2、`--docs` なしも 2）・画面の表に `未定` を 1 つ置くと 1
   （**陽性対照: 同じ正本で、画面の関門を当てない今の条件 1 は 0**）。
2. **screen-spec の結果の読み替え**——偽の screen-spec の終了コード 0・1・2・3・4・7 が 0・1・2・1・4・2 になる。`--spec-loop`・`--upto` を渡す。
3. **screen-spec の見つけ方**——引数・環境変数・隣・`installed_plugins.json`（一時の `CLAUDE_CONFIG_DIR`）。名指しが screen-spec でなければほかを探さずに 4。
4. **本物の screen-spec を通す**——違反（遷移先の無い遷移）で 1、spec-loop の版が対応の範囲の外で 4、正しい表で 0。
5. **ファイルを書かない**——正本・走らせた場所・プラグインの写し（`__pycache__` を含む。`-B` を付けずに走らせる）。

**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書き、`HOME` を一時ディレクトリにし、`CLAUDE_CONFIG_DIR`・`SPEC_LOOP_SCREEN_SPEC`・
`SCREEN_SPEC_SPEC_LOOP`・`PYTHONDONTWRITEBYTECODE` を外す（試料が名指すときだけ一時ディレクトリの値を渡す）。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**名指しした試料が期待どおりでなくなること**を確かめる。壊す箇所が本体にちょうど 1 回現れることを先に確かめる。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SPEC_LOOP = REAL_REPO / "plugins" / "spec-loop"
SCREEN_SPEC = REAL_REPO / "plugins" / "screen-spec"
GATE = "screen-gate.py"
EXIT = "check-spec-exit.py"

failures: list[str] = []


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


screens_test = load(REAL_REPO / "scripts" / "test-check-screens.py", "test_check_screens")


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        failures.append(f"{name}{': ' + detail if detail else ''}")


def assert_in_tmp(path: Path) -> None:
    resolved = path.resolve()
    assert REAL_REPO not in resolved.parents and resolved != REAL_REPO, f"実リポジトリの中を触ろうとした: {path}"


# ---- 正本の試料（screen-spec のテストの `base()` を、Q&A を全部反映済みにして使う）

t = screens_test


def reflected() -> dict[str, object]:
    files = t.base()
    files[t.QA] = (t.QA_HEAD + t.qa_row("Q-R-001", "要求確定", "A（業務部）", "requirements/screens/data/screen-items.csv", "反映済み")
                   + t.qa_row("Q-R-002", "要求確定", "A（業務部）", "requirements/screens/data/screens.csv", "反映済み")
                   + t.qa_row("Q-R-003", "要求確定", "B（業務部）", "spec/rules.md", "反映済み"))
    files[t.QA_DEV] = t.QA_HEAD + t.qa_row("D-S-001", "仕様レビュー", "A（開発）", "spec/rules.md", "反映済み")
    files["v1/spec/rules.md"] = "# 業務ルール\n\n受注は登録できる。\n"
    return files


def without_screens() -> dict[str, object]:
    return {k: v for k, v in reflected().items() if "requirements/screens/" not in k}


def changed(path: str, before: str, after: str) -> dict[str, object]:
    files = reflected()
    assert before in files[path], (path, before)
    files[path] = files[path].replace(before, after)
    return files


def plus(files: dict[str, object], **extra: str) -> dict[str, object]:
    out = dict(files)
    out.update({k.replace("__", "/"): v for k, v in extra.items()})
    return out


GOOD = reflected()
NONE = without_screens()
UNDECIDED = changed(t.S, "受注を探す", "未定（Q-R-002）")
UNDECIDED_PROSE = changed(t.LIST_MD, "## 3. レイアウト\n\n<!-- screen-spec: 表 -->", "## 3. レイアウト\n\n<!-- screen-spec: 表 -->\n\n並び方は 未定（Q-R-002）")
UNDECIDED_V2 = plus(GOOD, **{"v2__requirements__screens__data__screens.csv": t.S_HEAD + t.S2.replace("入力", "TBD（Q-R-002）")})
VIOLATION = changed(t.T, t.T1, t.T1.replace(",S-002,", ",S-009,"))
NOTE = "v1/requirements/screens/note.md"
REMOVED_NOTE = plus(NONE, **{"v1__requirements__screens__note.md": "# メモ\n\n未定\n",
                             "v2__removed.csv": "種類,対象,理由\nファイル,requirements/screens/note.md,要らない\n",
                             "v2__spec__rules.md": "# 業務ルール\n\n受注は登録できる。v2\n"})
WIREFRAME_ONLY = plus(NONE, **{"v1__requirements__screens__wireframes__order-list.drawio": "<mxfile>未定</mxfile>\n"})
PROSE_ONLY = plus(NONE, **{"v1__requirements__screens__order-list.md": "# S-001 受注一覧\n\n並び方は未定\n"})
HEADER_CHANGED = plus(GOOD, **{"v2__requirements__screens__data__screens.csv": t.S_HEAD.replace(",根拠\n", ",根拠,備考\n")
                               + t.S2.replace("\n", ",\n")})


# ---- 置き方

def copy_spec_loop(dest: Path, version: str | None = None) -> Path:
    assert_in_tmp(dest)
    for part in (".claude-plugin", "scripts"):
        shutil.copytree(SPEC_LOOP / part, dest / part, ignore=shutil.ignore_patterns("__pycache__"))
    if version is not None:
        manifest = json.loads((dest / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        manifest["version"] = version
        (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return dest


def copy_screen_spec(dest: Path) -> Path:
    assert_in_tmp(dest)
    shutil.copytree(SCREEN_SPEC, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def fake_screen_spec(dest: Path, code: int, name: str = "screen-spec") -> Path:
    """`check-screens.py` が受けた引数を出して `code` で終わる偽物。"""
    assert_in_tmp(dest)
    (dest / ".claude-plugin").mkdir(parents=True)
    (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": name}), encoding="utf-8")
    (dest / "scripts").mkdir()
    (dest / "scripts" / "check-screens.py").write_text(
        f"import sys\nprint('偽の検査 ' + ' '.join(sys.argv[1:]))\nraise SystemExit({code})\n", encoding="utf-8")
    return dest


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def write_docs(docs: Path, files: dict[str, object]) -> None:
    for rel, body in files.items():
        path = docs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))


class Case:
    """layout: `alone`（隣に screen-spec が無い）・`sibling`（本物の写しが隣）・`fake:<code>`（偽物を --screen-spec で名指す）・
    `env-bad`（隣に本物、環境変数は screen-spec でないもの）・`arg-bad`（--screen-spec が screen-spec でないもの）・
    `cache`・`cache-other`（プラグインのキャッシュの形。後者は別のマーケットプレイスの記録だけ）・`range`（隣に本物、spec-loop の版が 1.0.0）。
    script: `gate`（screen-gate.py）・`exit`（check-spec-exit.py。正本を重ねてから）・`exit-docs`（同じく --docs つき）。"""

    def __init__(self, name: str, layout: str, files: dict[str, object], code: int, text: str = "", *, args: tuple[str, ...] = (),
                 script: str = "gate", absent: str = "", empty: bool = False) -> None:
        self.name, self.layout, self.files, self.code, self.text = name, layout, files, code, text
        self.args, self.script, self.absent, self.empty = args, script, absent, empty


CASES = [
    # 1. 受入基準
    Case("画面の表も screen-spec も無い: 何も出さずに 0", "alone", NONE, 0, empty=True),
    Case("画面の表が無い: screen-spec を呼ばない（偽物が 1 でも 0）", "fake:1", NONE, 0, empty=True),
    Case("画面の表を removed.csv で消した: 何も出さずに 0", "alone", REMOVED_NOTE, 0, empty=True),
    Case("ワイヤーフレームだけの screens/ は画面の表でない: 何も出さずに 0", "alone", WIREFRAME_ONLY, 0, empty=True),
    Case("散文だけの screens/ は画面の表でない: 何も出さずに 0", "alone", PROSE_ONLY, 0, empty=True),
    Case("画面の表があって screen-spec が無い: 4", "alone", GOOD, 4, "画面の表があるのに screen-spec が見つからない"),
    Case("画面の表の未定: 1（screen-spec あり）", "sibling", UNDECIDED, 1, "requirements/screens/data/screens.csv:2: 未決定の印 未定"),
    Case("画面の表の未定: screen-spec が無くても 1（4 より強い）", "alone", UNDECIDED, 1, "screen-spec が見つからない"),
    Case("散文の仕様書の未定: 1", "alone", UNDECIDED_PROSE, 1, "requirements/screens/order-list.md"),
    Case("v2 に置いた行の TBD: 1", "alone", UNDECIDED_V2, 1, "未決定の印 TBD"),
    Case("正しい表と本物の screen-spec: 0", "sibling", GOOD, 0, "画面の関門を通る"),
    # 2. 読み替え
    Case("screen-spec の 0 は 0（--spec-loop を渡す）", "fake:0", GOOD, 0, "/docs --spec-loop "),
    Case("screen-spec の 1 は 1", "fake:1", GOOD, 1, "screen-spec の検査の終了コード: 1"),
    Case("screen-spec の 2 は 2", "fake:2", GOOD, 2, "画面の関門を判定していない"),
    Case("screen-spec の 3 は 1", "fake:3", GOOD, 1, "screen-spec の検査の終了コード: 3"),
    Case("screen-spec の 4 は 4", "fake:4", GOOD, 4, "画面の関門で止めた"),
    Case("screen-spec の知らない 7 は 2", "fake:7", GOOD, 2, "screen-spec の検査の終了コード: 7"),
    Case("--upto を screen-spec に渡す", "fake:0", GOOD, 0, "--upto 1", args=("--upto", "1")),
    # 3. 見つけ方
    Case("環境変数が screen-spec でなければ、隣に在っても 4", "env-bad", GOOD, 4, "SPEC_LOOP_SCREEN_SPEC が指す"),
    Case("--screen-spec が screen-spec でなければ 4", "arg-bad", GOOD, 4, "--screen-spec が指す"),
    Case("プラグインのキャッシュの記録から見つける", "cache", GOOD, 0, "画面の関門を通る"),
    Case("別のマーケットプレイスの記録だけなら見つからない", "cache-other", GOOD, 4, "見つからない"),
    # 4. 本物の screen-spec
    Case("遷移先の無い遷移: 1（screen-spec の違反）", "sibling", VIOLATION, 1, "screen-spec: 違反:"),
    Case("spec-loop の版が対応の範囲の外: 4", "range", GOOD, 4, "対応の範囲の外"),
    Case("版の間で画面の表の見出し行が違う: 1（重ね合わせ）", "sibling", HEADER_CHANGED, 1, "版の重ね合わせが決まりに反する"),
    # 引数
    Case("引数が無い: 2", "alone", NONE, 2, "usage", args=("<none>",)),
    Case("--upto 0: 2", "alone", NONE, 2, "--upto", args=("--upto", "0")),
    Case("docs が無い: 2", "alone", NONE, 2, "ディレクトリが無い", args=("<missing>",)),
    # 5. 条件 1（check-spec-exit.py）
    Case("条件 1: 画面の表が無い正本は --docs なしで 0", "alone", NONE, 0, "条件 1 を満たす", script="exit"),
    Case("条件 1: 画面の表が無い正本は --docs ありで 0（出力は --docs なしと同じ）", "alone", NONE, 0, "条件 1 を満たす", script="exit-docs"),
    Case("条件 1: ワイヤーフレームだけの screens/ は --docs なしでも 0", "alone", WIREFRAME_ONLY, 0, "条件 1 を満たす", script="exit"),
    Case("条件 1: 画面の表があるのに --docs が無い: 2", "sibling", GOOD, 2, "画面の表があるのに --docs が無い", script="exit"),
    Case("条件 1: 画面の表があって screen-spec が無い: 2", "alone", GOOD, 2, "screen-spec が見つからない", script="exit-docs"),
    Case("条件 1: 正しい表と本物の screen-spec: 0", "sibling", GOOD, 0, "画面の関門を通る", script="exit-docs"),
    Case("条件 1: 画面の表の未定: 1", "sibling", UNDECIDED, 1, "未決定の印 未定", script="exit-docs"),
    Case("条件 1: --docs の無い --upto は 2", "alone", NONE, 2, "usage", script="exit", args=("--upto", "1")),
]


def run_case(work: Path, case: Case, spec_loop_source: Path | None = None) -> tuple[int, str]:
    """(終了コード, 出力)。`spec_loop_source` は変異した spec-loop の写し（無ければ本物から写す）。"""
    assert_in_tmp(work)
    work.mkdir(parents=True)
    docs = work / "docs"
    write_docs(docs, case.files)
    home = work / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_CONFIG_DIR", "SPEC_LOOP_SCREEN_SPEC", "SCREEN_SPEC_SPEC_LOOP", "PYTHONDONTWRITEBYTECODE")}
    env["HOME"] = str(home)

    def place_spec_loop(dest: Path, version: str | None = None) -> Path:
        if spec_loop_source is None:
            return copy_spec_loop(dest, version)
        shutil.copytree(spec_loop_source, dest, ignore=shutil.ignore_patterns("__pycache__"))
        if version is not None:
            manifest = json.loads((dest / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
            manifest["version"] = version
            (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        return dest

    extra: list[str] = []
    layout = case.layout
    plugins = work / "plugins"
    if layout.startswith("cache"):
        config = work / "config"
        cache = config / "plugins" / "cache" / "market"
        spec_loop = place_spec_loop(cache / "spec-loop" / "0.94.0")
        installed = copy_screen_spec(cache / "screen-spec" / "0.1.0")
        key = "screen-spec@market" if layout == "cache" else "screen-spec@other-market"
        (config / "plugins" / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": {
            key: [{"scope": "user", "installPath": str(installed), "version": "0.1.0"}]}}), encoding="utf-8")
        env["CLAUDE_CONFIG_DIR"] = str(config)
    else:
        spec_loop = place_spec_loop(plugins / "spec-loop", "1.0.0" if layout == "range" else None)
        if layout in ("sibling", "env-bad", "range"):
            copy_screen_spec(plugins / "screen-spec")
        if layout.startswith("fake:"):
            extra = ["--screen-spec", str(fake_screen_spec(work / "fake", int(layout.split(":")[1])))]
        elif layout == "env-bad":
            env["SPEC_LOOP_SCREEN_SPEC"] = str(fake_screen_spec(work / "not-screen-spec", 0, name="other"))
        elif layout == "arg-bad":
            extra = ["--screen-spec", str(fake_screen_spec(work / "not-screen-spec", 0, name="other"))]

    scripts = spec_loop / "scripts"
    if case.script == "gate":
        if case.args == ("<none>",):
            argv = [str(scripts / GATE)]
        elif case.args == ("<missing>",):
            argv = [str(scripts / GATE), str(work / "nowhere")]
        else:
            argv = [str(scripts / GATE), str(docs), *case.args, *extra]
    else:
        merged = work / "merged"
        made = subprocess.run([sys.executable, "-B", str(scripts / "merge-versions.py"), str(docs), str(merged)],
                              capture_output=True, text=True, env=env, cwd=work)
        if made.returncode != 0:
            return -1, f"重ね合わせが失敗した: {made.stdout}{made.stderr}"
        argv = [str(scripts / EXIT), str(merged / "shared" / "qa.csv"), str(merged / "spec"), *case.args]
        if case.script == "exit-docs":
            argv += ["--docs", str(docs), *extra]
    # 書かないことは、正本・走らせた場所・プラグインの写し（`__pycache__`）で見る——画面の関門は `-B` を付けない
    # （`check-spec-exit.py` は前から `__pycache__` を書きうるので `-B` で走らせる。画面の関門の分は screen-gate の試料で見る）
    before = snapshot(work)
    flags = [] if case.script == "gate" else ["-B"]
    proc = subprocess.run([sys.executable, *flags, *argv], capture_output=True, text=True, cwd=work, env=env)
    out = proc.stdout + proc.stderr
    if snapshot(work) != before:
        out += "\n<<正本か走らせた場所かプラグインの写しにファイルを書いた>>"
    return proc.returncode, out


def as_expected(case: Case, result: tuple[int, str]) -> bool:
    code, out = result
    if code != case.code or "<<" in out:
        return False
    if case.empty and out != "":
        return False
    if case.text and case.text not in out:
        return False
    return not (case.absent and case.absent in out)


# (名前, 本体のファイル, 壊す前, 壊した後, 殺す試料)
MUTATIONS = [
    ("screen-spec の 3（未決定）を通す", GATE, "3: EXIT_FAIL,", "3: EXIT_OK,", "screen-spec の 3 は 1"),
    ("知らない終了コードを通す", GATE, "SCREEN_SPEC_CODES.get(proc.returncode, EXIT_UNJUDGED)",
     "SCREEN_SPEC_CODES.get(proc.returncode, EXIT_OK)", "screen-spec の知らない 7 は 2"),
    ("spec-loop が印を数えない", GATE, "for number, marker in spec_exit.find_markers(text):", "for number, marker in []:",
     "画面の表の未定: screen-spec が無くても 1（4 より強い）"),
    ("印を 4 より弱くする", GATE, "if marked or code == EXIT_FAIL:", "if code == EXIT_FAIL:",
     "画面の表の未定: screen-spec が無くても 1（4 より強い）"),
    ("名指しが screen-spec でなくても使う", GATE, "            if not is_screen_spec(root):\n                raise NotFound(",
     "            if False:\n                raise NotFound(", "環境変数が screen-spec でなければ、隣に在っても 4"),
    ("隣の screen-spec を探さない", GATE, "    if is_screen_spec(sibling):\n        return sibling",
     "    if False:\n        return sibling", "正しい表と本物の screen-spec: 0"),
    ("キャッシュの記録の user を読まない", GATE, "chosen = project if project else user", "chosen = project",
     "プラグインのキャッシュの記録から見つける"),
    ("キャッシュの記録のマーケットプレイスを見ない", GATE, 'entries = plugins.get(f"{SCREEN_SPEC_NAME}@{market}")',
     'entries = next((v for k, v in plugins.items() if k.startswith(SCREEN_SPEC_NAME + "@")), None)',
     "別のマーケットプレイスの記録だけなら見つからない"),
    ("--spec-loop を渡さない", GATE, ', "--spec-loop", str(PLUGIN_ROOT)]', "]", "screen-spec の 0 は 0（--spec-loop を渡す）"),
    ("--upto を渡さない", GATE, '        command += ["--upto", str(upto)]', "        pass", "--upto を screen-spec に渡す"),
    ("画面の表が無いことを先に見ない", GATE, "    return any(has_tables(root) for _, root in versions.find_versions(docs, [])[:upto])",
     "    return False", "画面の表があって screen-spec が無い: 4"),
    ("表の無い screens/ も画面の表と見る", GATE, "    return any((root / table).is_file() for table in TABLES)",
     "    return any((root / table).is_file() for table in TABLES) or (root / SCREENS_DIR).is_dir()",
     "条件 1: ワイヤーフレームだけの screens/ は --docs なしでも 0"),
    ("重ね合わせの誤りを見ない", GATE, "    if problems:\n        return EXIT_FAIL, problems",
     "    if False:\n        return EXIT_FAIL, problems", "版の間で画面の表の見出し行が違う: 1（重ね合わせ）"),
    ("__pycache__ を書く", GATE, "sys.dont_write_bytecode = True", "sys.dont_write_bytecode = False",
     "画面の表があって screen-spec が無い: 4"),
    ("条件 1 に画面の関門を入れない", EXIT, "screen_gate(spec_dir, docs, upto, named) if screen else (0, [])", "(0, [])",
     "条件 1: 画面の表の未定: 1"),
    ("--docs が無いのに画面の表があっても通す", EXIT, "    if screens.has_tables(spec_dir.parent):",
     "    if False:", "条件 1: 画面の表があるのに --docs が無い: 2"),
    ("画面の関門の 4 を条件 1 の 0 にする", EXIT, "    if screen_code:\n        return 2, notes + screen_lines",
     "    if False:\n        return 2, notes + screen_lines", "条件 1: 画面の表があって screen-spec が無い: 2"),
]


def main() -> int:
    names = [case.name for case in CASES]
    assert len(names) == len(set(names)), "試料の名前が重複している"
    killers = {killer for *_, killer in MUTATIONS}
    assert killers <= set(names), f"変異の殺す試料が無い: {killers - set(names)}"
    with tempfile.TemporaryDirectory(prefix="screen-gate-test-") as tmp:
        tmp_path = Path(tmp)
        results = {case.name: run_case(tmp_path / f"case{i}", case) for i, case in enumerate(CASES)}
        for case in CASES:
            result = results[case.name]
            check(f"試料が期待どおりでない: {case.name}", as_expected(case, result), f"exit={result[0]} {result[1][-600:]}")
        # 回帰: 画面の表が無い正本で、--docs の有無で条件 1 の出力が同じ（受入基準）
        plain = results["条件 1: 画面の表が無い正本は --docs なしで 0"][1]
        with_docs = results["条件 1: 画面の表が無い正本は --docs ありで 0（出力は --docs なしと同じ）"][1]
        check("画面の表が無い正本で、--docs の有無で条件 1 の出力が同じ",
              plain == with_docs, f"{plain!r} / {with_docs!r}")

        # 陽性対照: 同じ「未定」の正本で、画面の関門を当てない今の条件 1 は通ってしまう（#1097 の受入基準）
        work = tmp_path / "control"
        write_docs(work / "docs", UNDECIDED)
        spec_loop = copy_spec_loop(work / "plugins" / "spec-loop")
        made = subprocess.run([sys.executable, "-B", str(spec_loop / "scripts" / "merge-versions.py"), str(work / "docs"), str(work / "merged")],
                              capture_output=True, text=True)
        exit_module = load(spec_loop / "scripts" / EXIT, "check_spec_exit_control")
        code, _ = exit_module.check(work / "merged" / "shared" / "qa.csv", work / "merged" / "spec", screen=False)
        check("陽性対照: 画面の関門を当てない条件 1 は、画面の表に未定が残っても 0", made.returncode == 0 and code == 0, f"merge={made.returncode} code={code}")
        code, _ = exit_module.check(work / "merged" / "shared" / "qa.csv", work / "merged" / "spec", work / "docs")
        check("同じ正本で、画面の関門を当てた条件 1 は 1", code == 1, f"code={code}")

        sources = {name: (SPEC_LOOP / "scripts" / name).read_text(encoding="utf-8") for name in (GATE, EXIT)}
        for index, (name, target, before, after, killer) in enumerate(MUTATIONS):
            count = sources[target].count(before)
            if count != 1:
                check(f"変異が届いていない: {name}", False, f"壊す箇所が {count} 回現れる")
                continue
            mutated = tmp_path / f"mut{index}" / "spec-loop"
            copy_spec_loop(mutated)
            (mutated / "scripts" / target).write_text(sources[target].replace(before, after), encoding="utf-8")
            case = next(c for c in CASES if c.name == killer)
            result = run_case(tmp_path / f"mutwork{index}", case, spec_loop_source=mutated)
            check(f"変異が生き残った: {name}（{killer} で殺せるはず）", not as_expected(case, result), result[1][-300:])

    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
