#!/usr/bin/env python3
"""`check-alloy.py`（spec-loop の Alloy の確かめ。#922）の回帰テスト。

    python3 scripts/test-check-alloy.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-check-tlc.py` と同じ形。

**このテストは実環境を触らない。** 正本リポジトリはテンポラリに作り、Alloy は**偽物**（`PATH` に置かず絶対パスで呼ぶスクリプト）で当てる。
偽の Alloy は Alloy 6.2.0 の `exec` の結果の行の形（`00. run   someA … SAT`）を標準エラーに出し、本物と同じくモデルの隣に `<名前>/` を作る——
**本物の Alloy の出力の形は見ない**（本体の docstring の「守らない」）。`PATH` の先頭には、`command -v alloy` で見つかる偽の `alloy` を置く——
呼び方の行が無いときに探しに行かないことを見るため。**引数なし・`gui` の形は、偽物でも本物でも走らせない**——走ったら印を書く偽物で「走らせない」を見る。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに観測がそろったままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が期待どおりであること（下の「正しい本体」）。本体の docstring の「守る」の行数と変異の数が等しいことを、
テスト自身が数えて見る。終了コードの表と定数、書き方の行が README・スキル・Formal Checker に書かれていることも見る。
"""
import contextlib
import importlib.util
import io
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
PLUGIN = REAL_REPO / "plugins" / "spec-loop"
SCRIPT = PLUGIN / "scripts" / "check-alloy.py"
TLC = PLUGIN / "scripts" / "check-tlc.py"

failures: list[str] = []

# 本体の docstring の「守る」の各行に 1 つずつ。(探す文字列, 置き換え) の組
MUTATIONS = {
    "command -v で探す": [("    if call is None:\n        return EXIT_MISSING,",
                         "    if call is None and shutil.which(\"alloy\"):\n        call = \"alloy exec\"\n        check_form(call)\n"
                         "    if call is None:\n        return EXIT_MISSING,"),
                        ("import argparse\n", "import argparse\nimport shutil\n")],
    "exec の無い・gui の在る呼び方を走らせる": [("        if call is not None:\n            check_form(call)\n", "        pass\n")],
    "クォートの中の gui を見ない": [('    if any("gui" in word.split() for word in words):\n', '    if "gui" in words:\n')],
    "シェルの組み立てを見ない": [("    if special:\n", "    if False:\n")],
    "先頭の語の = を見ない": [('    if words and "=" in words[0]:\n', "    if False:\n")],
    "先頭の許可の一覧を見ない": [("    if not (head == HEAD_JAVA or HEAD_ALLOY in head.lower()):\n", "    if False:\n")],
    "通るモデルの終了コードを見ない": [("        if rc != 0:\n", "        if False:\n")],
    "到達できることを見ない": [('GOOD_EXPECT = {("run", "someA"): "SAT", ', "GOOD_EXPECT = {")],
    "成り立つ性質の反例を見ない": [(', ("check", "emptyOrNot"): "UNSAT"}', "}")],
    "違反するモデルを見ない": [("        missed = unmet(BROKEN_EXPECT, out)\n        if missed:\n",
                         "        missed = unmet(BROKEN_EXPECT, out)\n        if False:\n")],
    "BOM を外さない": [('    text = text.removeprefix("\\ufeff")\n', "")],
    "同じ行が 2 行でも先頭を使う": [("    if len(calls) > 1:\n", "    if False:\n")],
    "呼び方が空を見ない": [("    if calls and not calls[0]:\n", "    if False:\n")],
    "読めない CLAUDE.md を書いていないと読む": [('        raise Unknown(f"{path} を読めない: {e}")\n', '        return None, f"{path} を読めない: {e}"\n')],
    "headless を足さない": [('    env["JAVA_TOOL_OPTIONS"] = ', '    env["UNUSED"] = ')],
    "時間切れで止めない": [("        out, _ = proc.communicate(timeout=timeout)\n", "        out, _ = proc.communicate()\n")],
    "正本で走らせる": [("cwd=workdir,", "cwd=None,")],
}


def fake_alloy(probe_run="SAT", probe_check="UNSAT", broken_check="SAT", probe_rc=0, marker=False):
    """偽の Alloy。最後の引数（モデルのファイル）で振る舞いを決め、本物と同じく作業ディレクトリに `<名前>/` を作り、結果の行を標準エラーに出す。"""
    return f"""#!/bin/sh
for a in "$@"; do f="$a"; done
{'touch "$MARKER"' if marker else ':'}
[ -n "$ENVLOG" ] && printf '%s\\n' "$JAVA_TOOL_OPTIONS" > "$ENVLOG"
case "$f" in
  Probe.als) mkdir -p Probe && touch Probe/receipt.json
    printf '00. run   someA                    0    1/1     {probe_run}\\n01. check emptyOrNot               0       {probe_check}\\n' >&2; exit {probe_rc};;
  Broken.als) mkdir -p Broken && touch Broken/receipt.json
    printf '00. check alwaysEmpty              0    1/1     {broken_check}\\n' >&2; exit 0;;
esac
echo "unknown model: $f" >&2
exit 1
"""


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_{id(path)}_{path.stat().st_mtime_ns}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def assert_not_real_repo(root: Path) -> None:
    resolved = root.resolve()
    assert resolved != REAL_REPO, "テストが実リポジトリを対象にしている"
    assert not str(resolved).startswith(str(REAL_REPO) + os.sep), "対象が実リポジトリの内側にある"
    assert resolved.is_relative_to(Path(tempfile.gettempdir()).resolve()), "対象がテンポラリの外"


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}")
        failures.append(name)


def write_exe(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def make_tools(base: Path) -> dict:
    """偽の Alloy と、通らない形の呼び方。どれも絶対パスで呼ぶ（`PATH` の `alloy` とは別）。"""
    tools = base / "tools"
    tools.mkdir(parents=True)
    t = {
        "good": write_exe(tools / "fake-alloy", fake_alloy()),
        # 何にでも「反例なし」と言う（違反するモデルでも）
        "never-ce": write_exe(tools / "never-ce-alloy", fake_alloy(broken_check="UNSAT")),
        # 何にでも「反例あり」と言う（成り立つ性質でも）
        "always-ce": write_exe(tools / "always-ce-alloy", fake_alloy(probe_check="SAT")),
        # 何も許さない（到達できない）
        "unreachable": write_exe(tools / "unreachable-alloy", fake_alloy(probe_run="UNSAT")),
        # 結果の行は出すが終了コードが 0 でない
        "bad-rc": write_exe(tools / "bad-rc-alloy", fake_alloy(probe_rc=3)),
        # 起動しても Alloy でない（jar の場所が違う、の形）
        "broken": write_exe(tools / "broken-alloy", "#!/bin/sh\necho 'Error: Unable to access jarfile /nowhere/alloy.jar' >&2\nexit 1\n"),
        # 走ったら印を書く（走らせないことを見る）。中身は通る偽物
        "marker": write_exe(tools / "marker-alloy", fake_alloy(marker=True)),
        # 時間切れ（子のプロセスも残す——プロセスグループで止めないと出力の管が閉じない）
        "slow": write_exe(tools / "slow-alloy", "#!/bin/sh\nsleep 20 &\nwait\n"),
        # 先頭が java の通る偽物（`java -jar <jar> exec` の形の陽性対照）
        "java": write_exe(tools / "java", fake_alloy(marker=True)),
        # 空白を含むパスの通る偽物（クォートはシェルの組み立てに数えない）
        "spaced": write_exe(tools / "fake alloy", fake_alloy(marker=True)),
    }
    # PATH の先頭に置く `alloy`（command -v で見つかる、通る偽物）
    pathdir = base / "pathbin"
    pathdir.mkdir()
    write_exe(pathdir / "alloy", fake_alloy())
    t["pathdir"] = pathdir
    return t


def snapshot(root: Path):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


def run(mod, argv):
    """(終了コード, 標準出力)。"""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            rc = mod.main(argv)
        except Exception as exc:  # 変異で落ちたら、それも「違う挙動」として観測する
            return ("例外", type(exc).__name__)
    return rc, out.getvalue()


def scenario(mod, base: Path, tag: str) -> dict:
    """1 つの本体に全試料を当て、観測を辞書で返す。**観測にはテンポラリのパスを入れない。**"""
    work = base / tag
    assert_not_real_repo(work.parent)
    tools = make_tools(work)
    root = work / "repo"
    root.mkdir()
    md = root / "CLAUDE.md"
    marker = work / "ran"
    envlog = work / "envlog"
    os.environ["MARKER"] = str(marker)
    # 走らせる場所を正本にしておく——本体が一時ディレクトリで走らせなければ、偽の Alloy の <名前>/ が正本に残る
    os.chdir(root)
    o = {}

    def case(text):
        """(終了コード, 呼び方が走ったか, 正本が変わらなかったか)。"""
        if text is None:
            if md.exists():
                md.unlink()
        elif isinstance(text, bytes):
            md.write_bytes(text)
        else:
            md.write_text(text, encoding="utf-8")
        if marker.exists():
            marker.unlink()
        before = snapshot(root)
        rc, out = run(mod, [str(root)])
        return rc, marker.exists(), snapshot(root) == before

    def call_line(name, extra=" exec"):
        return f"Alloy の呼び方: {tools[name]}{extra}\n"

    o["CLAUDE.md が無い"] = case(None)
    o["呼び方の行が無い（PATH に alloy が在る）"] = case("# 正本\n\nほかの行だけ\n")
    o["通る呼び方"] = case("# 正本\n" + call_line("good", " exec -q"))
    o["通る呼び方（走ったら印）"] = case(call_line("marker"))
    o["exec の無い呼び方"] = case(call_line("marker", ""))
    o["gui の呼び方"] = case(call_line("marker", " gui"))
    o["exec と gui の両方"] = case(call_line("marker", " exec gui"))
    o["exec が 1 語の一部"] = case(call_line("marker", "-exec"))
    o["クォートの中の gui"] = case(call_line("marker", " exec 'x gui'"))
    o["シェルの組み立て（||）"] = case(f"Alloy の呼び方: {tools['marker']} exec || {tools['marker']}\n")
    o["シェルの組み立て（# の後ろの exec）"] = case(f"Alloy の呼び方: {tools['marker']} # exec\n")
    o["シェルの組み立て（; の後ろの exec）"] = case(f"Alloy の呼び方: {tools['marker']}; : exec\n")
    o["組み込みの exec で始まる（ラッパーの本文の形）"] = case(f"Alloy の呼び方: exec {tools['marker']}\n")
    o["シェルで始まる（sh -c）"] = case(f"Alloy の呼び方: sh -c '{tools['marker']}' exec\n")
    o["空白を含むパスをクォートで囲む"] = case(f"Alloy の呼び方: '{tools['spaced']}' exec\n")
    o["先頭が java"] = case(f"Alloy の呼び方: {tools['java']} -Dx=1 -jar /opt/alloy.jar exec\n")
    o["ブレースの展開"] = case(f"Alloy の呼び方: {tools['marker']} {{gui,}} exec\n")
    o["組み込みの trap で始まる"] = case(f"Alloy の呼び方: trap {tools['marker']} EXIT exec\n")
    o["別のシェルで始まる（tcsh -c）"] = case(f"Alloy の呼び方: tcsh -c {tools['marker']} exec\n")
    o["環境変数の代入で始まる"] = case(f"Alloy の呼び方: FOO=1 exec {tools['marker']}\n")
    o["! で始まる"] = case(f"Alloy の呼び方: ! exec {tools['marker']}\n")
    o["名前に alloy を含む代入で始まる"] = case(f"Alloy の呼び方: ALLOY=1 exec {tools['marker']}\n")
    o["値に alloy を含む代入で始まる"] = case(f"Alloy の呼び方: X=alloy exec {tools['marker']}\n")
    o["通らない呼び方"] = case(call_line("broken"))
    o["何にでも反例なし"] = case(call_line("never-ce"))
    o["何にでも反例あり"] = case(call_line("always-ce"))
    o["到達できない"] = case(call_line("unreachable"))
    o["結果の行は出すが終了コードが 0 でない"] = case(call_line("bad-rc"))
    o["フェンスの中だけ"] = case("例:\n\n```text\n" + call_line("good") + "```\n")
    o["BOM つきの 1 行目"] = case("\ufeff" + call_line("good"))
    o["全角のコロンの呼び方"] = case(call_line("good").replace("Alloy の呼び方:", "Alloy の呼び方："))
    o["呼び方が 2 行"] = case(call_line("good") + call_line("broken"))
    md.write_text("Alloy の呼び方:   \n", encoding="utf-8")
    rc, out = run(mod, [str(root)])
    o["呼び方が空"] = (rc, "空" in out)
    o["読めない CLAUDE.md（UTF-8 でない）"] = case(b"\xff\xfe\x00Alloy\n")
    os.environ["ENVLOG"] = str(envlog)
    os.environ["JAVA_TOOL_OPTIONS"] = "-Xmx64m"
    case(call_line("good"))
    o["走らせる環境の JAVA_TOOL_OPTIONS"] = envlog.read_text(encoding="utf-8").strip() if envlog.exists() else None
    del os.environ["ENVLOG"], os.environ["JAVA_TOOL_OPTIONS"]
    saved = mod.PROBE_TIMEOUT
    mod.PROBE_TIMEOUT = 1
    start = time.monotonic()
    rc = case(call_line("slow"))
    o["時間切れ"] = (rc, "早い" if time.monotonic() - start < 10 else "遅い")
    mod.PROBE_TIMEOUT = saved
    o["引数なし"] = run(mod, [])[0]
    md.write_text(call_line("good"), encoding="utf-8")
    o["出力（通る）"] = run(mod, [str(root)])[1].replace(str(tools["good"]), "<alloy>")
    md.unlink()
    o["出力（無い）"] = run(mod, [str(root)])[1].replace(str(root), "<root>")
    os.chdir(base)
    return o


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test-check-alloy-")).resolve()
    saved_env = dict(os.environ)
    cwd = os.getcwd()
    try:
        mod = load_module(SCRIPT, "calloy")
        tools_probe = make_tools(tmp / "path-probe")
        os.environ["PATH"] = f"{tools_probe['pathdir']}{os.pathsep}{os.environ.get('PATH', '')}"
        os.environ.pop("JAVA_TOOL_OPTIONS", None)
        check("陽性対照: PATH の先頭の偽の alloy が command -v で見つかる", shutil.which("alloy") == str(tools_probe["pathdir"] / "alloy"))
        print("正しい本体")
        o = scenario(mod, tmp, "correct")
        ok, missing, unknown = (0, False, True), (1, False, True), (4, False, True)
        check("CLAUDE.md が無い: 1", o["CLAUDE.md が無い"] == missing)
        check("呼び方の行が無い: PATH に alloy が在っても 1（command -v で探さない）", o["呼び方の行が無い（PATH に alloy が在る）"] == missing)
        check("通る呼び方（PATH に無い絶対パス・exec の後に引数）: 0", o["通る呼び方"] == ok)
        check("通る呼び方は走らせる: 0 で印がある（陽性対照）", o["通る呼び方（走ったら印）"] == (0, True, True))
        check("exec の無い呼び方（引数なしの形）: 4 で走らせない", o["exec の無い呼び方"] == unknown)
        check("gui の呼び方: 4 で走らせない", o["gui の呼び方"] == unknown and o["exec と gui の両方"] == unknown)
        check("exec が 1 語の一部: 4 で走らせない", o["exec が 1 語の一部"] == unknown)
        check("クォートの中の gui: 4 で走らせない", o["クォートの中の gui"] == unknown)
        check("シェルの組み立て（||・# の後ろ・; の後ろの exec）: 4 で走らせない",
              all(o[k] == unknown for k in ("シェルの組み立て（||）", "シェルの組み立て（# の後ろの exec）", "シェルの組み立て（; の後ろの exec）")))
        check("組み込みの exec で始まる・sh -c で始まる: 4 で走らせない",
              o["組み込みの exec で始まる（ラッパーの本文の形）"] == unknown and o["シェルで始まる（sh -c）"] == unknown)
        check("空白を含むパスをクォートで囲んだ呼び方: 0 で走らせる（陽性対照）", o["空白を含むパスをクォートで囲む"] == (0, True, True))
        check("先頭が java の呼び方（-D の = を含む）: 0 で走らせる（陽性対照）", o["先頭が java"] == (0, True, True))
        check("名前・値に alloy を含む環境変数の代入で始まる（ALLOY=1・X=alloy）: 4 で走らせない",
              o["名前に alloy を含む代入で始まる"] == unknown and o["値に alloy を含む代入で始まる"] == unknown)
        check("ブレースの展開（{gui,}）: 4 で走らせない", o["ブレースの展開"] == unknown)
        check("先頭が trap・tcsh -c・環境変数の代入・!: 4 で走らせない",
              all(o[k] == unknown for k in ("組み込みの trap で始まる", "別のシェルで始まる（tcsh -c）", "環境変数の代入で始まる", "! で始まる")))
        check("通らない呼び方: 1", o["通らない呼び方"] == missing)
        check("何にでも反例なしと言う呼び方: 1（陽性対照）", o["何にでも反例なし"] == missing)
        check("何にでも反例ありと言う呼び方: 1", o["何にでも反例あり"] == missing)
        check("到達できない呼び方: 1", o["到達できない"] == missing)
        check("結果の行は出すが終了コードが 0 でない: 1", o["結果の行は出すが終了コードが 0 でない"] == missing)
        check("フェンスの中の行は読まない（check-tlc.py の読み方）: 1", o["フェンスの中だけ"] == missing)
        check("BOM つきの 1 行目の行を読む: 0", o["BOM つきの 1 行目"] == ok)
        check("全角のコロンの行も読む: 0", o["全角のコロンの呼び方"] == ok)
        check("呼び方が 2 行: 4", o["呼び方が 2 行"] == unknown)
        check("呼び方が空: 4 で、空と言う", o["呼び方が空"] == (4, True))
        check("読めない CLAUDE.md: 4", o["読めない CLAUDE.md（UTF-8 でない）"] == unknown)
        check("走らせる環境の JAVA_TOOL_OPTIONS に headless を足し、前の値を残す",
              o["走らせる環境の JAVA_TOOL_OPTIONS"] == "-Xmx64m -Djava.awt.headless=true")
        check("時間切れ: 1 で、子のプロセスを待たずに早く返る", o["時間切れ"] == (missing, "早い"))
        check("引数なし: 2", o["引数なし"] == 2)
        check("出力（通る）は呼び方を名指しする", "Alloy が在る: 呼び方 `<alloy> exec`" in o["出力（通る）"])
        check("出力（無い）は用意のしかたと書く行を出す", "Alloy の呼び方: <コマンド> exec" in o["出力（無い）"]
              and "command -v" in o["出力（無い）"])

        print("\n終了コードの表・書き方の行が、docstring・README・スキル・Formal Checker と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        exits = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", exits, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_MISSING, mod.EXIT_USAGE, mod.EXIT_UNKNOWN}
        check(f"終了コードの表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)
        table = source.split("## 正本の `CLAUDE.md` に書く行")[1].split("## ")[0]
        check("docstring の表に行の頭がある", f"`{mod.CALL_KEY} <コマンド>`" in table)
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        front = readme.split("## 前提")[1].split("\n## ")[0]
        example = re.search(rf"^{re.escape(mod.CALL_KEY)} (.+)$", front, re.M)
        check("README の「前提」が呼び方の行を、写せる形（行頭）で、exec を含めて書く",
              example is not None and "exec" in example.group(1).split() and "gui" not in example.group(1).split())
        check("README の「前提」が Alloy の jar を挙げる", "alloy.jar" in front)
        spec_review = (PLUGIN / "skills" / "spec-review" / "SKILL.md").read_text(encoding="utf-8")
        check("spec-review が check-alloy.py で確かめる", "scripts/check-alloy.py" in spec_review)
        check("spec-review が Alloy を「版かヘルプ」で呼ばない・command -v で探さない",
              "版かヘルプ" not in spec_review and re.search(r"Alloy[^\n]*無ければ `command -v` で探す", spec_review) is None)
        formal = (PLUGIN / "agents" / "formal-checker.md").read_text(encoding="utf-8")
        check("Formal Checker が呼び方の行を名指しし、引数なし・gui の形を禁じる",
              f"`{mod.CALL_KEY}`" in formal and "引数なし" in formal and "`gui`" in formal)
        check("Formal Checker が、渡された呼び方でも exec の無い形を走らせないと書く",
              re.search(r"渡された呼び方でも、語 `exec` が無い", formal) is not None)
        check("spec-review が、check-alloy.py が 0 のときだけ呼び方を Formal Checker に渡す",
              "`check-alloy.py` が 0 を返したときだけ** `Alloy の呼び方:`" in spec_review)
        autopilot_check = (PLUGIN / "scripts" / "autopilot-check.py").read_text(encoding="utf-8")
        check("autopilot の点検の一覧に check-alloy.py が入る（各起動が spec-review の手順 3 で呼ぶ）",
              re.search(r"SPEC_REVIEW_SCRIPTS = \([^)]*\"check-alloy\.py\"", autopilot_check) is not None)

        print("\n変異テスト（壊したのに観測がそろったままなら失格）")
        for i, (name, pairs) in enumerate(MUTATIONS.items()):
            mutated = source
            absent = [n for n, _ in pairs if n not in mutated]
            if absent:
                check(f"変異を当てる先がある: {name}: {absent}", False)
                continue
            for needle, replacement in pairs:
                mutated = mutated.replace(needle, replacement)
            d = tmp / f"mut-{i}"
            d.mkdir()
            broken = d / "check-alloy.py"
            broken.write_text(mutated, encoding="utf-8")
            shutil.copy(TLC, d / "check-tlc.py")
            # **読み込めない変異は「殺せた」ではなく「当てられなかった」**
            try:
                mutant = load_module(broken, "mut")
            except Exception as exc:
                check(f"変異を読み込める（当てられなかった）: {name}: {type(exc).__name__}", False)
                continue
            try:
                got = scenario(mutant, d, "s")
            except Exception:
                check(f"変異を殺せる: {name}", True)
                continue
            check(f"変異を殺せる: {name}", got != o)

        print("\n「守る」の行数と変異の数が 1 対 1 か（手で数えない）")
        body = source.split("守る:")[1].split("守らない:")[0]
        promises = [line for line in body.splitlines() if line.startswith("- ")]
        check(f"本体の「守る」{len(promises)} 行に対して変異が {len(MUTATIONS)} 件", len(promises) == len(MUTATIONS))

        print("\n実環境を対象にしない歯止め")
        try:
            assert_not_real_repo(REAL_REPO)
        except AssertionError:
            check("実リポジトリを対象にすると落ちる", True)
        else:
            check("実リポジトリを対象にすると落ちる", False)
    finally:
        os.chdir(cwd)
        os.environ.clear()
        os.environ.update(saved_env)
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {len(failures)} 件")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Alloy の確かめのテスト: すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
