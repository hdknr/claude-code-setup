#!/usr/bin/env python3
"""`check-tlc.py`（spec-loop の TLC の前提の確かめ。#912）の回帰テスト。

    python3 scripts/test-check-tlc.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。`test-autopilot-check.py` と同じ形。

**このテストは実環境を触らない。** 正本リポジトリはテンポラリに作り、TLC は**偽物**（`PATH` に置かず絶対パスで呼ぶスクリプト）で当てる。
偽の TLC は本物の TLC の出力に合わせた 2 つの文字列（`No error has been found`・`is violated`）を出す——**本物の TLC の出力の形は見ない**
（本体の docstring の「守らない」）。`PATH` の先頭には、`command -v tlc` で見つかる偽の `tlc` を置く——呼び方の行が無いときに探しに行かないことを見るため。

**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに観測がそろったままなら失格**とする。
**陽性対照**: 壊さない本体で全試料が期待どおりであること（下の「正しい本体」）。本体の docstring の「守る」の行数と変異の数が等しいことを、
テスト自身が数えて見る。終了コードの表と定数、書き方の 2 つの行が README・スキル・Formal Checker に書かれていることも見る。
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
SCRIPT = PLUGIN / "scripts" / "check-tlc.py"

failures: list[str] = []

# 本体の docstring の「守る」の各行に 1 つずつ。(探す文字列, 置き換え) の組
MUTATIONS = {
    "呼び方の行が無い正本を 0 にする": [("    if call is None:\n        return EXIT_MISSING,", "    if call is None:\n        return EXIT_OK,")],
    "通るモデルの終了コードを見ない": [("        if rc != 0 or GOOD_MARK not in out:\n", "        if GOOD_MARK not in out:\n")],
    "違反するモデルを見ない": [("        if BROKEN_MARK not in out:\n", "        if False:\n")],
    "command -v で探す": [("    if call is None:\n        return EXIT_MISSING,",
                         "    if call is None and shutil.which(\"tlc\"):\n        call = \"tlc\"\n    if call is None:\n        return EXIT_MISSING,"),
                        ("import argparse\n", "import argparse\nimport shutil\n")],
    "フェンスの中の行を読む": [("                fence = None\n            continue\n", "                fence = None\n")],
    "フェンスを長さ・info string を見ずに閉じる": [("len(m.group(1)) >= fence[1] and not m.group(2).strip()", "True")],
    "BOM を外さない": [('    text = text.removeprefix("\\ufeff")\n', "")],
    "同じ宣言が 2 行でも先頭を使う": [("    if len(calls) > 1:\n", "    if False:\n")],
    "外す宣言の値を見ない": [("    if opt_outs and opt_outs[0] != OPT_OUT_VALUE:\n", "    if False:\n")],
    "--autopilot で外しても呼び方を走らせる": [("    if opt_out and autopilot:\n", "    if opt_out and autopilot and (call is None or probe(call)[0]):\n")],
    "--autopilot が無くても外す宣言で確かめない": [("    if opt_out and autopilot:\n", "    if opt_out:\n")],
    "読めない CLAUDE.md を書いていないと読む": [('        raise Unknown(f"{path} を読めない: {e}")\n', '        return None, False, f"{path} を読めない: {e}"\n')],
    "時間切れで止めない": [("        out, _ = proc.communicate(timeout=timeout)\n", "        out, _ = proc.communicate()\n")],
    "正本で走らせる": [("cwd=workdir,", "cwd=None,")],
}

FAKE_TLC = """#!/bin/sh
# 偽の TLC。最後の引数（モデルのファイル）で振る舞いを決め、本物と同じく作業ディレクトリに states/ を作る
for a in "$@"; do f="$a"; done
mkdir -p states
case "$f" in
  Probe.tla) echo "Model checking completed. No error has been found."; exit 0;;
  Broken.tla) echo "Error: Invariant Inv is violated."; exit 12;;
esac
echo "unknown model: $f"
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
    """偽の TLC と、通らない形の呼び方。どれも絶対パスで呼ぶ（`PATH` の `tlc` とは別）。"""
    tools = base / "tools"
    tools.mkdir(parents=True)
    t = {
        "good": write_exe(tools / "fake-tlc", FAKE_TLC),
        # 何にでも「エラーなし」と言う（違反するモデルでも）
        "always-ok": write_exe(tools / "always-ok", "#!/bin/sh\necho 'Model checking completed. No error has been found.'\nexit 0\n"),
        # 印は出すが終了コードが 0 でない
        "bad-rc": write_exe(tools / "bad-rc", "#!/bin/sh\necho 'Model checking completed. No error has been found.'\necho 'x is violated'\nexit 3\n"),
        # 起動しても TLC でない（Java はあるが jar の場所が違う、の形）
        "broken": write_exe(tools / "broken", "#!/bin/sh\necho 'Error: Could not find or load main class tlc2.TLC'\nexit 1\n"),
        # 走ったら印を書く（走らせないことを見る）
        "marker": write_exe(tools / "marker-tlc", "#!/bin/sh\ntouch \"$MARKER\"\n" + FAKE_TLC.split("\n", 1)[1]),
        # 時間切れ（子のプロセスも残す——プロセスグループで止めないと出力の管が閉じない）
        "slow": write_exe(tools / "slow", "#!/bin/sh\nsleep 20 &\nwait\n"),
    }
    # PATH の先頭に置く `tlc`（command -v で見つかる、通る偽物）
    pathdir = base / "pathbin"
    pathdir.mkdir()
    write_exe(pathdir / "tlc", FAKE_TLC)
    t["pathdir"] = pathdir
    return t


def snapshot(root: Path):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


def run(mod, argv):
    """(終了コード, 標準出力)。テンポラリのパスは出力から伏せる。"""
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
    os.environ["MARKER"] = str(marker)
    # 走らせる場所を正本にしておく——本体が一時ディレクトリで走らせなければ、偽の TLC の states/ が正本に残る
    os.chdir(root)
    o = {}

    def case(text, *flags):
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
        rc, out = run(mod, [str(root), *flags])
        return rc, marker.exists(), snapshot(root) == before

    def call_line(name, extra=""):
        return f"TLC の呼び方: {tools[name]}{extra}\n"

    o["CLAUDE.md が無い"] = case(None)
    o["CLAUDE.md が無い（--autopilot）"] = case(None, "--autopilot")
    o["呼び方の行が無い（PATH に tlc が在る）"] = case("# 正本\n\nほかの行だけ\n")
    o["呼び方の行が無い（--autopilot）"] = case("# 正本\n", "--autopilot")
    o["通る呼び方"] = case("# 正本\n" + call_line("good", " -workers 1"))
    o["通る呼び方（--autopilot）"] = case(call_line("good"), "--autopilot")
    o["通らない呼び方"] = case(call_line("broken"))
    o["何にでもエラーなし"] = case(call_line("always-ok"))
    o["印は出すが終了コードが 0 でない"] = case(call_line("bad-rc"))
    o["フェンスの中だけ"] = case("例:\n\n```text\n" + call_line("good") + "```\n")
    o["チルダのフェンスの中だけ"] = case("~~~\n" + call_line("good") + "~~~\n")
    o["フェンスを閉じた後の行"] = case("```\n例\n```\n" + call_line("good"))
    o["4 つのフェンスの中の 3 つのフェンスの中"] = case("````markdown\n```text\n" + call_line("good") + "```\n````\n")
    o["info string の行では閉じない"] = case("```\n```bash\n" + call_line("good") + "```\n")
    o["長いフェンスを閉じた後の行"] = case("````\n```\n````\n" + call_line("good"))
    o["BOM つきの 1 行目"] = case("\ufeff" + call_line("good"))
    o["行頭でない（字下げ）"] = case("  " + call_line("good"))
    o["呼び方が 2 行"] = case(call_line("good") + call_line("broken"))
    o["外す宣言が 2 行"] = case("業務フローの形式検査: しない\n業務フローの形式検査: しない\n", "--autopilot")
    o["外す宣言の値が 無し"] = case("業務フローの形式検査: 無し\n", "--autopilot")
    o["外す宣言の値が しない（v2 から）"] = case("業務フローの形式検査: しない（v2 から）\n", "--autopilot")
    o["呼び方が空"] = case("TLC の呼び方:   \n")
    o["外す宣言と通る呼び方（--autopilot）"] = case("業務フローの形式検査: しない\n" + call_line("marker"), "--autopilot")
    o["外す宣言だけ（--autopilot）"] = case("業務フローの形式検査: しない\n", "--autopilot")
    o["外す宣言だけ（--autopilot なし）"] = case("業務フローの形式検査: しない\n")
    o["外す宣言と通る呼び方（--autopilot なし）"] = case("業務フローの形式検査: しない\n" + call_line("marker"))
    o["読めない CLAUDE.md（UTF-8 でない）"] = case(b"\xff\xfe\x00TLC\n")
    saved = mod.PROBE_TIMEOUT
    mod.PROBE_TIMEOUT = 1
    start = time.monotonic()
    rc = case(call_line("slow"))
    o["時間切れ"] = (rc, "早い" if time.monotonic() - start < 10 else "遅い")
    mod.PROBE_TIMEOUT = saved
    o["引数なし"] = run(mod, [])[0]
    md.write_text(call_line("good"), encoding="utf-8")
    o["出力（通る）"] = run(mod, [str(root)])[1].replace(str(tools["good"]), "<tlc>")
    md.unlink()
    o["出力（無い）"] = run(mod, [str(root)])[1].replace(str(root), "<root>")
    os.chdir(base)
    return o


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="test-check-tlc-")).resolve()
    saved_env = dict(os.environ)
    cwd = os.getcwd()
    try:
        mod = load_module(SCRIPT, "ctlc")
        tools_probe = make_tools(tmp / "path-probe")
        os.environ["PATH"] = f"{tools_probe['pathdir']}{os.pathsep}{os.environ.get('PATH', '')}"
        check("陽性対照: PATH の先頭の偽の tlc が command -v で見つかる", shutil.which("tlc") == str(tools_probe["pathdir"] / "tlc"))
        print("正しい本体")
        o = scenario(mod, tmp, "correct")
        ok, missing, unknown = (0, False, True), (1, False, True), (4, False, True)
        check("CLAUDE.md が無い: 1（--autopilot でも 1）", o["CLAUDE.md が無い"] == missing and o["CLAUDE.md が無い（--autopilot）"] == missing)
        check("呼び方の行が無い: PATH に tlc が在っても 1（command -v で探さない）", o["呼び方の行が無い（PATH に tlc が在る）"] == missing)
        check("呼び方の行が無い（--autopilot）: 1", o["呼び方の行が無い（--autopilot）"] == missing)
        check("通る呼び方（PATH に無い絶対パス・引数つき）: 0", o["通る呼び方"] == ok and o["通る呼び方（--autopilot）"] == ok)
        check("通らない呼び方: 1", o["通らない呼び方"] == missing)
        check("何にでもエラーなしと言う呼び方: 1（陽性対照）", o["何にでもエラーなし"] == missing)
        check("印は出すが終了コードが 0 でない: 1", o["印は出すが終了コードが 0 でない"] == missing)
        check("フェンスの中の行は読まない: 1", o["フェンスの中だけ"] == missing and o["チルダのフェンスの中だけ"] == missing)
        check("フェンスを閉じた後の行は読む: 0（陽性対照）", o["フェンスを閉じた後の行"] == ok and o["長いフェンスを閉じた後の行"] == ok)
        check("4 つのフェンスの中の 3 つのフェンスの中は読まない: 1", o["4 つのフェンスの中の 3 つのフェンスの中"] == missing)
        check("info string の行ではフェンスを閉じない: 1", o["info string の行では閉じない"] == missing)
        check("BOM つきの 1 行目の宣言を読む: 0", o["BOM つきの 1 行目"] == ok)
        check("行頭でない行は読まない: 1", o["行頭でない（字下げ）"] == missing)
        check("呼び方が 2 行: 4", o["呼び方が 2 行"] == unknown)
        check("外す宣言が 2 行: 4", o["外す宣言が 2 行"] == unknown)
        check("外す宣言の値が しない でない: 4", o["外す宣言の値が 無し"] == unknown and o["外す宣言の値が しない（v2 から）"] == unknown)
        check("呼び方が空: 4", o["呼び方が空"] == unknown)
        check("外す宣言と呼び方（--autopilot）: 0 で呼び方を走らせない", o["外す宣言と通る呼び方（--autopilot）"] == (0, False, True))
        check("外す宣言だけ（--autopilot）: 0", o["外す宣言だけ（--autopilot）"] == ok)
        check("外す宣言だけ（--autopilot なし）: 1（確かめる）", o["外す宣言だけ（--autopilot なし）"] == missing)
        check("外す宣言と呼び方（--autopilot なし）: 0 で呼び方を走らせる（陽性対照）",
              o["外す宣言と通る呼び方（--autopilot なし）"] == (0, True, True))
        check("読めない CLAUDE.md: 4", o["読めない CLAUDE.md（UTF-8 でない）"] == unknown)
        check("時間切れ: 1 で、子のプロセスを待たずに早く返る", o["時間切れ"] == (missing, "早い"))
        check("引数なし: 2", o["引数なし"] == 2)
        check("出力（通る）は呼び方を名指しする", "TLC が在る: 呼び方 `<tlc>`" in o["出力（通る）"])
        check("出力（無い）は用意のしかたと書く行を出す", "TLC の呼び方: <コマンド>" in o["出力（無い）"]
              and "業務フローの形式検査: しない" in o["出力（無い）"] and "command -v" in o["出力（無い）"])

        print("\n終了コードの表・書き方の行が、docstring・README・スキル・Formal Checker と一致する")
        source = SCRIPT.read_text(encoding="utf-8")
        exits = source.split("## 終了コード")[1].split("## ")[0]
        documented = {int(m) for m in re.findall(r"^\| (\d+) \|", exits, re.M)}
        defined = {mod.EXIT_OK, mod.EXIT_MISSING, mod.EXIT_USAGE, mod.EXIT_UNKNOWN}
        check(f"終了コードの表 {sorted(documented)} と定数 {sorted(defined)}", documented == defined)
        table = source.split("## 正本の `CLAUDE.md` に書く行")[1].split("## ")[0]
        check("docstring の表に 2 つの行の頭がある", f"`{mod.CALL_KEY} <コマンド>`" in table
              and f"`{mod.OPT_OUT_KEY} {mod.OPT_OUT_VALUE}`" in table)
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        front = readme.split("## 前提")[1]
        check("README の「前提」が 2 つの行を、写せる形（行頭）で書く",
              re.search(rf"^{re.escape(mod.CALL_KEY)} \S", front, re.M) is not None
              and re.search(rf"^{re.escape(mod.OPT_OUT_KEY)} {mod.OPT_OUT_VALUE}$", front, re.M) is not None)
        check("README の「前提」が Java と tla2tools.jar を挙げる", "Java" in front and "tla2tools.jar" in front)
        spec_review = (PLUGIN / "skills" / "spec-review" / "SKILL.md").read_text(encoding="utf-8")
        check("spec-review が check-tlc.py で確かめる", "scripts/check-tlc.py" in spec_review)
        autopilot = (PLUGIN / "skills" / "autopilot" / "SKILL.md").read_text(encoding="utf-8")
        check("autopilot の各起動が check-tlc.py --autopilot で確かめる", re.search(r"check-tlc\.py <[^>]+> --autopilot", autopilot) is not None)
        formal = (PLUGIN / "agents" / "formal-checker.md").read_text(encoding="utf-8")
        check("Formal Checker が呼び方の行を名指しする", f"`{mod.CALL_KEY}`" in formal)

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
            broken = d / "check-tlc.py"
            broken.write_text(mutated, encoding="utf-8")
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
    print("TLC の前提の確かめのテスト: すべて合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
