#!/usr/bin/env python3
"""`render-diagrams.py`（正本リポジトリの drawio・BPMN → SVG と、その鮮度の確かめ）の回帰テスト。

    python3 scripts/test-render-diagrams.py

**本体はプラグインの中にある**（`plugins/spec-loop/scripts/`）。

見るもの（受入基準は #268 の計画ファイル）:

1. **書き出す**（A1）——`docs/` の下の入れ子・複数・空白を含む名前の `.drawio` を、隣の同じ名前の `.svg` に。書き出しは SVG として読め、
   ソースのバイトの sha256 の印を持つ（XML 宣言があればその直後、無ければ先頭。前の印は置き換える）。CLI は `DRAWIO`・既定のパス
   （`SPEC_LOOP_DRAWIO_DEFAULT` で差し替える）・`PATH` の `drawio` のどれからでも見つかる。CLI に渡す引数の形も見る。
2. **CLI が見つからなければ 2**（A2）——`DRAWIO` が空・指したものが無い・既定のパスにも `PATH` にも無い。何も書かず、
   「書き出していない」と全部の `.drawio` を名指しする。
3. **失敗したら前の `.svg` を変えず、書きかけを残さず 1**（A3）——0 以外で終わる・SVG を書いてから 0 以外で終わる・書きかけで落ちる・
   何も書かない・空・XML でない・根が svg でない・時間切れ。前の `.svg` が在る形と無い形。ほかのファイルは書き出す。
4. **`--check`**（A4）——新しければ 0。書き出しが無い・印が無い・古い・ソースの無い印つきの `.svg` を名指しして 1。印の無いソースの無い
   `.svg`（ガントチャートなど）は見ない。`docs/` が無ければ 2、`.drawio` が 0 件なら 0。**CLI を起動せず、何も書かない。**
5. **印はソースのバイトだけで決まる**（A5）——書き出しのたびにバイトの変わる偽の CLI で 2 回書き出しても `--check` は 0。
6. **書くのは隣の `.svg` だけ**（A10）——実行の前後でツリー（`docs/` の外を含む）を比べ、一時ファイルが残らないことを見る。
8. **BPMN**（#901）——`.bpmn` を drawio と混ぜてパスの順に、隣の `.svg` に同じ印で書き出す（描画口の引数は `<ソース> <一時ファイル>`）。
   描画口は `BPMN_RENDER` か既定の `node render-bpmn.mjs --deps <依存> --chrome <Chrome>`（`PATH` の偽の `node` で引数の形を見る）。
   Node・依存（`SPEC_LOOP_BPMN_DEPS`）・Chrome（`CHROME_PATH`・`SPEC_LOOP_CHROME_DEFAULT`）・描画口が無ければ、無いものを全部名指しして
   2——**drawio の CLI が在っても、どちらの種類も 1 件も書かない**。`.bpmn` だけなら draw.io の CLI が無くても書く。失敗・時間切れ
   （`BPMN_TIMEOUT`）は drawio と同じ扱い。`--check` は `.bpmn` の書き出しも見る。同じ `X.svg` になるソース（`X.drawio` と `X.bpmn`）は、
   どちらのモードでも何も書かずに 2。大文字の拡張子の `.SVG` もソースの無い書き出しとして見る（#904 の残課題 P2-5）。
7. **起動時に無視させられていたシグナルは無視したまま**（#820）——`nohup` と同じ形（起動の前に SIGHUP・SIGTERM を SIG_IGN にし、
   exec に引き継がせる）で起こしてグループに送っても、止まらずに書き出して 0 で終わる。無視させていなければ、今のとおり止まって
   後始末する（SIGHUP の試料）。

**変異テストを含む**（A9）。本体を 1 箇所ずつ壊し、名指しした試料が期待どおりでなくなることを確かめる。
**陽性対照**として、壊す前の本体で全部の試料が期待どおりであることを先に見る（変異の回は名指しした試料だけを回す）。

**このテストは実環境を触らない。** 本体を一時ディレクトリに写して、一時ディレクトリの偽の正本リポジトリだけを対象にする
（このリポジトリの `docs/` を対象にしないことはアサートで担保する）。**本物の draw.io にも届かない**——`DRAWIO` は偽の CLI を指し、
`DRAWIO` を外す試料でも既定のパスを `SPEC_LOOP_DRAWIO_DEFAULT` で偽か無いパスに差し替え、`PATH` は一時ディレクトリだけにする
（どれもアサートで担保する）。**本物の Chrome・Node にも届かない**——`BPMN_RENDER` は偽の描画口を指し、外す試料でも
Chrome の既定のパスを `SPEC_LOOP_CHROME_DEFAULT` で偽か無いパスに差し替え、`node` は `PATH`（一時ディレクトリだけ）の偽物しか無い
（どれもアサートで担保する）。**同梱の `render-bpmn.mjs` そのものは走らせない**——既定の描画口の試料が起こすのは偽の `node` である。

標準ライブラリのみ。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "render-diagrams.py"
REAL_DRAWIO = "/Applications/draw.io.app/Contents/MacOS/draw.io"
REAL_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BPMN_SCRIPT = "render-bpmn.mjs"
DEPS_FILES = ("node_modules/bpmn-js/dist/bpmn-viewer.production.min.js", "node_modules/bpmn-js/dist/assets/diagram-js.css",
              "node_modules/bpmn-js/dist/assets/bpmn-js.css", "node_modules/puppeteer-core/package.json")

MARK = re.compile(rb"<!-- spec-loop-diagram-source: sha256=([0-9a-f]{64}) -->")
DECL = b'<?xml version="1.0" encoding="UTF-8"?>'

# 偽の draw.io の CLI と BPMN の描画口（偽の `node` を兼ねる）。draw.io の形なら `--output <パス>` と最後のソースを、
# BPMN の描画口の形（`<ソース> <出力>`）なら最後の 2 つを拾い、FAKE_BEHAVIOUR に応じて振る舞う。呼ばれた引数を FAKE_LOG に 1 行ずつ残す
FAKE_CLI = r'''
import json, os, sys, time, uuid
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\n")
behaviour = os.environ.get("FAKE_BEHAVIOUR", "success")
if "--output" in args:
    out = args[args.index("--output") + 1]
    src = args[-1]
else:
    src, out = args[-2], args[-1]
GOOD = '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>\n'
def write(text):
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
if behaviour == "fail_bad":
    behaviour = "nonzero" if "bad" in os.path.basename(src) else "success"
if behaviour == "success":
    write(GOOD); sys.exit(0)
if behaviour == "nodecl":
    write('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>\n'); sys.exit(0)
if behaviour == "oldmark":
    write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- spec-loop-diagram-source: sha256=' + "0" * 64
          + ' -->\n<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>\n'); sys.exit(0)
if behaviour == "nonce":
    write(GOOD.replace("<rect/>", "<rect id=\"" + uuid.uuid4().hex + "\"/>")); sys.exit(0)
if behaviour == "nonzero":
    sys.exit(3)
if behaviour == "svg_then_fail":
    write(GOOD); sys.exit(1)
if behaviour == "partial_then_fail":
    write("<svg xmlns="); sys.exit(1)
if behaviour == "nothing":
    sys.exit(0)
if behaviour == "empty":
    write(""); sys.exit(0)
if behaviour == "not_xml":
    write("not an svg at all"); sys.exit(0)
if behaviour == "wrong_root":
    write('<html xmlns="http://www.w3.org/1999/xhtml"/>'); sys.exit(0)
if behaviour == "orphan":
    # 前置き（`xvfb-run`）の孫の形: 出力を受けた孫が、親の時間切れのあとで書く（標準出力は閉じて、待たせない）
    import subprocess
    subprocess.Popen([sys.executable, "-c", "import sys, time; time.sleep(7); open(sys.argv[1], 'w').write('late')", out],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5); write(GOOD); sys.exit(0)
if behaviour == "slow":
    time.sleep(3); write(GOOD); sys.exit(0)
if behaviour == "hang":
    time.sleep(5); write(GOOD); sys.exit(0)
raise SystemExit("unknown behaviour: " + behaviour)
'''

PREVIOUS = b'<svg xmlns="http://www.w3.org/2000/svg"><circle/></svg>\n'


class Run:
    def __init__(self, proc: subprocess.CompletedProcess[str], root: Path, before: dict[str, bytes], log: list[list[str]]):
        self.code = proc.returncode
        self.stdout = proc.stdout
        self.stderr = proc.stderr
        self.root = root
        self.before = before
        self.after = snapshot(root)
        self.log = log


def snapshot(root: Path) -> dict[str, bytes]:
    """偽の正本リポジトリの全部のファイル（偽の CLI の記録と道具は除く）。"""
    files: dict[str, bytes] = {}
    for dirpath, _dirs, names in os.walk(root):
        for name in names:
            path = Path(dirpath) / name
            relative = str(path.relative_to(root))
            if relative.startswith("_tools/"):
                continue
            files[relative] = path.read_bytes()
    return files


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_repo(base: Path, files: dict[str, bytes | str]) -> Path:
    root = base / "repo"
    resolved = root.resolve()
    assert resolved != REAL_REPO and REAL_REPO not in resolved.parents, "テストが実リポジトリの中を対象にしている"
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
    (root / "_tools" / "bin").mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def fake_exe(root: Path, name: str) -> Path:
    """`#!python` の付いた実行できる偽の CLI（既定のパス・PATH の試料で使う）。"""
    path = root / "_tools" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!{sys.executable}\n{FAKE_CLI}", encoding="utf-8")
    path.chmod(0o755)
    return path


def run(script: Path, root: Path, *args: str, behaviour: str = "success", drawio: str | None = "fake",
        default: str | None = None, path_dirs: list[Path] | None = None, timeout: str = "60",
        target: Path | None = None, hup_after: float | None = None, pre: str | None = None,
        hup_signal: int = signal.SIGHUP, ignored: bool = False, bpmn: str | None = "fake",
        deps: str | None = None, chrome: str | None = None, chrome_default: str | None = None,
        bpmn_timeout: str = "60") -> Run:
    """偽の正本リポジトリで本体を走らせる。

    drawio: "fake" なら偽の CLI を指す。None なら `DRAWIO` を外す。ほかは文字列のまま渡す。
    default: `SPEC_LOOP_DRAWIO_DEFAULT`。None なら一時ディレクトリの無いパス（本物の既定のパスを見させない）。
    bpmn: `BPMN_RENDER`。"fake" なら偽の描画口を指す。None なら外す。ほかは文字列のまま渡す。
    deps・chrome: `SPEC_LOOP_BPMN_DEPS`・`CHROME_PATH`（None なら外す）。
    chrome_default: `SPEC_LOOP_CHROME_DEFAULT`。None なら一時ディレクトリの無いパス（本物の Chrome を見させない）。
    hup_after: 起こしてからこの秒数のあとで、本体のプロセスグループに `hup_signal` を送る。
    ignored: 本体を起こす前に `hup_signal` を SIG_IGN にする（`nohup` と同じ形——exec に引き継がれる）。
    """
    fake = root / "_tools" / "fake-drawio.py"
    fake.write_text(FAKE_CLI, encoding="utf-8")
    log_path = root / "_tools" / "fake.log"
    env = {k: v for k, v in os.environ.items()
           if k not in ("DRAWIO", "SPEC_LOOP_DRAWIO_DEFAULT", "DRAWIO_TIMEOUT", "BPMN_RENDER", "SPEC_LOOP_BPMN_DEPS", "CHROME_PATH",
                        "SPEC_LOOP_CHROME_DEFAULT", "BPMN_TIMEOUT")}
    if drawio == "fake":
        env["DRAWIO"] = f"{shlex.quote(sys.executable)} {shlex.quote(str(fake))}"
    elif drawio is not None:
        env["DRAWIO"] = drawio
    if bpmn == "fake":
        env["BPMN_RENDER"] = f"{shlex.quote(sys.executable)} {shlex.quote(str(fake))}"
    elif bpmn is not None:
        env["BPMN_RENDER"] = bpmn
    if deps is not None:
        env["SPEC_LOOP_BPMN_DEPS"] = deps
    if chrome is not None:
        env["CHROME_PATH"] = chrome
    env["SPEC_LOOP_CHROME_DEFAULT"] = str(root / "_tools" / "no-such-chrome") if chrome_default is None else chrome_default
    env["BPMN_TIMEOUT"] = bpmn_timeout
    env["SPEC_LOOP_DRAWIO_DEFAULT"] = str(root / "_tools" / "no-such-drawio") if default is None else default
    env["PATH"] = os.pathsep.join(str(p) for p in (path_dirs or [root / "_tools" / "bin"]))
    env["FAKE_BEHAVIOUR"] = behaviour
    env["FAKE_LOG"] = str(log_path)
    env["DRAWIO_TIMEOUT"] = timeout
    # 本物の draw.io に届かないこと
    assert env["SPEC_LOOP_DRAWIO_DEFAULT"] != REAL_DRAWIO, "既定のパスが本物の draw.io を指している"
    on_path = shutil.which("drawio", path=env["PATH"])
    assert on_path is None or root.resolve() in Path(on_path).resolve().parents, f"PATH の drawio が一時ディレクトリの外: {on_path}"
    assert "DRAWIO" not in env or REAL_DRAWIO not in env["DRAWIO"], "DRAWIO が本物の draw.io を指している"
    # 本物の Chrome・Node に届かないこと
    assert env["SPEC_LOOP_CHROME_DEFAULT"] != REAL_CHROME and env.get("CHROME_PATH") != REAL_CHROME, "本物の Chrome を指している"
    node = shutil.which("node", path=env["PATH"])
    assert node is None or root.resolve() in Path(node).resolve().parents, f"PATH の node が一時ディレクトリの外: {node}"
    render = shlex.split(env.get("BPMN_RENDER", "")) or ["x"]
    assert Path(render[0]).name != "node" or root.resolve() in Path(render[0]).resolve().parents, "BPMN_RENDER が本物の node を指している"
    target = root if target is None else target
    assert REAL_REPO not in target.resolve().parents and target.resolve() != REAL_REPO, "このリポジトリを対象にしている"
    before = snapshot(root)
    argv = [sys.executable, "-I", str(script), str(target), *args]
    if pre is not None:
        # 本体を走らせる前に環境を変える（例: `del os.killpg` でプロセスグループの無い OS を作る）
        argv = [sys.executable, "-I", "-c",
                f"import os, sys, runpy; {pre}; sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name='__main__')",
                str(script), str(target), *args]
    if hup_after is None:
        proc = subprocess.run(argv, cwd=root, capture_output=True, text=True, env=env, timeout=120)
    else:
        # 端末を閉じたときの形: 本体のプロセスグループに SIGHUP を送る
        # **無視させない試料も既定（SIG_DFL）に戻してから起こす**——テストを `nohup` の下で回すと SIGHUP の SIG_IGN が引き継がれ、
        # 本体が登録しなくなって「止まって後始末する」試料が偽の赤になる（#820）
        def disposition() -> None:
            signal.signal(hup_signal, signal.SIG_IGN if ignored else signal.SIG_DFL)
        child = subprocess.Popen(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
                                 start_new_session=True, preexec_fn=disposition)
        time.sleep(hup_after)
        os.killpg(child.pid, hup_signal)
        out, err = child.communicate(timeout=120)
        proc = subprocess.CompletedProcess(argv, child.returncode, out, err)
    log = []
    if log_path.is_file():
        log = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        log_path.unlink()
    return Run(proc, root, before, log)


def svg_problem(data: bytes) -> str | None:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return f"XML として読めない: {e}"
    if not root.tag.endswith("svg"):
        return f"根が svg でない: {root.tag}"
    return None


def leftovers(r: Run) -> list[str]:
    """一時ファイル（`.<名前>.<乱数>.svg`）が残っていないか。"""
    return [p for p in r.after if Path(p).name.startswith(".") and p.endswith(".svg")]


def only_svgs_changed(r: Run, expected_new: set[str]) -> list[str]:
    """変わったのが名指しした `.svg` だけか（A10）。"""
    problems = []
    for relative in set(r.before) | set(r.after):
        if r.before.get(relative) == r.after.get(relative):
            continue
        if relative not in expected_new:
            problems.append(f"{relative} が変わった")
    return problems


SOURCES = {
    "docs/a.drawio": "<mxfile>a</mxfile>\n",
    "docs/v1/spec/nested/b c.drawio": "<mxfile>b c</mxfile>\n",
    "docs/v1/requirements/flow.drawio": "<mxfile>flow</mxfile>\n",
    "docs/v1/requirements/rules.md": "本文\n",
    "README.md": "外\n",
}
OUTS = {k[: -len(".drawio")] + ".svg" for k in SOURCES if k.endswith(".drawio")}


# --- 試料（それぞれ問題の一覧を返す。空なら期待どおり） ------------------------------

def case_export(script: Path, tmp: Path) -> list[str]:
    """A1・A10: 入れ子・空白を含む名前を全部書き出し、印を持ち、ほかを変えない。"""
    root = make_repo(tmp, SOURCES)
    r = run(script, root)
    p = []
    if r.code != 0:
        p.append(f"終了コード {r.code}: {r.stderr[-300:]}")
    for out in sorted(OUTS):
        data = r.after.get(out)
        if data is None:
            p.append(f"{out} が無い")
            continue
        if (why := svg_problem(data)) is not None:
            p.append(f"{out}: {why}")
        marks = MARK.findall(data)
        src = SOURCES[out[: -len(".svg")] + ".drawio"].encode("utf-8")
        if marks != [sha(src).encode("ascii")]:
            p.append(f"{out}: 印がソースの指紋 1 つでない: {marks}")
        if not data.startswith(DECL + b"\n<!-- spec-loop-diagram-source: sha256="):
            p.append(f"{out}: 印が XML 宣言の直後に無い: {data[:120]!r}")
    p += only_svgs_changed(r, OUTS)
    p += [f"一時ファイルが残った: {x}" for x in leftovers(r)]
    # CLI に渡す引数の形: --export --format svg --output <同じディレクトリの .svg> <ソース>
    if len(r.log) != len(OUTS):
        p.append(f"CLI の呼び出しが {len(r.log)} 回")
    for args in r.log:
        if args[:4] != ["--export", "--format", "svg", "--output"] or len(args) != 6:
            p.append(f"CLI の引数の形が違う: {args}")
            continue
        out, src = Path(args[4]), Path(args[5])
        if out.parent != src.parent or not out.name.endswith(".svg") or out.exists():
            p.append(f"一時ファイルの置き場所・名前が違う: {args}")
    order = [str(Path(a[-1]).relative_to(root)) for a in r.log if len(a) == 6]
    if order != sorted(order):
        p.append(f"パスの順に書き出していない: {order}")
    return p


def case_nodecl(script: Path, tmp: Path) -> list[str]:
    """A1: XML 宣言の無い書き出しでは印を先頭に置く。"""
    root = make_repo(tmp, {"docs/a.drawio": "<mxfile/>\n"})
    r = run(script, root, behaviour="nodecl")
    data = r.after.get("docs/a.svg", b"")
    p = [] if r.code == 0 else [f"終了コード {r.code}"]
    if not data.startswith(b"<!-- spec-loop-diagram-source: sha256=" + sha(b"<mxfile/>\n").encode() + b" -->\n<svg"):
        p.append(f"印が先頭に無い: {data[:120]!r}")
    if svg_problem(data):
        p.append("SVG として読めない")
    return p


def case_oldmark(script: Path, tmp: Path) -> list[str]:
    """A1: 書き出しに前の印があれば置き換える（印は 1 つ）。"""
    root = make_repo(tmp, {"docs/a.drawio": "<mxfile/>\n"})
    r = run(script, root, behaviour="oldmark")
    data = r.after.get("docs/a.svg", b"")
    marks = MARK.findall(data)
    p = [] if r.code == 0 else [f"終了コード {r.code}"]
    if marks != [sha(b"<mxfile/>\n").encode()]:
        p.append(f"印が置き換わっていない: {marks}")
    return p


def case_default_path(script: Path, tmp: Path) -> list[str]:
    """A1: `DRAWIO` が無ければ既定のパス（`SPEC_LOOP_DRAWIO_DEFAULT` で差し替え）を使う。"""
    root = make_repo(tmp, {"docs/a.drawio": "<mxfile/>\n"})
    exe = fake_exe(root, "default-drawio")
    r = run(script, root, drawio=None, default=str(exe))
    p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-300:]}"]
    if "docs/a.svg" not in r.after or len(r.log) != 1:
        p.append(f"既定のパスの CLI で書き出していない（呼び出し {len(r.log)} 回）")
    return p


def case_path_drawio(script: Path, tmp: Path) -> list[str]:
    """A1: 既定のパスに無ければ `PATH` の `drawio` を使う。"""
    root = make_repo(tmp, {"docs/a.drawio": "<mxfile/>\n"})
    exe = fake_exe(root, "bin/drawio")
    r = run(script, root, drawio=None, default="", path_dirs=[exe.parent])
    p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-300:]}"]
    if "docs/a.svg" not in r.after or len(r.log) != 1:
        p.append(f"PATH の drawio で書き出していない（呼び出し {len(r.log)} 回）")
    return p


def not_found(script: Path, tmp: Path, reason: str, **kwargs) -> list[str]:
    root = make_repo(tmp, {**SOURCES, "docs/a.svg": PREVIOUS})
    r = run(script, root, **kwargs)
    p = []
    if r.code != 2:
        p.append(f"終了コードが 2 でない: {r.code}")
    if r.after != r.before:
        p.append("何か書いた")
    if r.log:
        p.append("CLI を呼んだ")
    if "書き出していない" not in r.stderr:
        p.append(f"「書き出していない」と言わない: {r.stderr[-300:]}")
    if reason not in r.stderr:
        p.append(f"理由 {reason!r} を言わない: {r.stderr[-300:]}")
    for src in SOURCES:
        if src.endswith(".drawio") and src not in r.stderr:
            p.append(f"{src} を名指ししない")
    return p


def case_drawio_empty(script: Path, tmp: Path) -> list[str]:
    """A2: `DRAWIO` が空。"""
    return not_found(script, tmp, "DRAWIO が空", drawio=" ")


def case_drawio_missing(script: Path, tmp: Path) -> list[str]:
    """A2: `DRAWIO` が無いパスを指す。"""
    return not_found(script, tmp, "DRAWIO の CLI が見つからない", drawio=str(tmp / "no-such-cli"))


def case_none_found(script: Path, tmp: Path) -> list[str]:
    """A2: `DRAWIO` が無く、既定のパスにも `PATH` にも無い。"""
    return not_found(script, tmp, "draw.io の CLI が見つからない", drawio=None)


def failing(behaviour: str, message: str, timeout: str = "60") -> Callable[[Path, Path], list[str]]:
    def case(script: Path, tmp: Path) -> list[str]:
        """A3・A10: 失敗したら前の `.svg` を変えず（無ければ無いまま）、書きかけを残さず 1。"""
        p = []
        for index, previous in enumerate((PREVIOUS, None)):
            files: dict[str, bytes | str] = {"docs/v1/a.drawio": "<mxfile/>\n"}
            if previous is not None:
                files["docs/v1/a.svg"] = previous
            root = make_repo(tmp / f"p{index}", files)
            r = run(script, root, behaviour=behaviour, timeout=timeout)
            label = "前の svg あり" if previous is not None else "前の svg なし"
            if r.code != 1:
                p.append(f"{label}: 終了コードが 1 でない: {r.code} {r.stderr[-200:]}")
            if r.after.get("docs/v1/a.svg") != previous:
                p.append(f"{label}: 前の svg が変わった")
            p += [f"{label}: {x}" for x in only_svgs_changed(r, set())]
            p += [f"{label}: 一時ファイルが残った: {x}" for x in leftovers(r)]
            if "docs/v1/a.drawio" not in r.stderr:
                p.append(f"{label}: ファイルを名指ししない")
            if message not in r.stderr:
                p.append(f"{label}: 理由 {message!r} を言わない: {r.stderr[-300:]}")
        return p
    return case


def case_partial_failure(script: Path, tmp: Path) -> list[str]:
    """A3: 1 件が失敗しても残りを書き出し、最後に 1。"""
    root = make_repo(tmp, {"docs/a-bad.drawio": "<mxfile>bad</mxfile>\n", "docs/z-good.drawio": "<mxfile>good</mxfile>\n"})
    r = run(script, root, behaviour="fail_bad")
    p = [] if r.code == 1 else [f"終了コードが 1 でない: {r.code}"]
    if "docs/z-good.svg" not in r.after:
        p.append("失敗のあとのファイルを書き出していない")
    if "docs/a-bad.svg" in r.after:
        p.append("失敗したファイルの書き出しがある")
    if "docs/a-bad.drawio" not in r.stderr:
        p.append("失敗したファイルを名指ししない")
    return p


def case_no_sources(script: Path, tmp: Path) -> list[str]:
    """`.drawio` が 0 件なら何もせずに 0（CLI が無くても）。"""
    root = make_repo(tmp, {"docs/index.md": "x\n"})
    r = run(script, root, drawio=" ")
    p = [] if r.code == 0 else [f"終了コード {r.code}"]
    if r.after != r.before or r.log:
        p.append("何かした")
    return p


def case_no_docs(script: Path, tmp: Path) -> list[str]:
    """`docs/` が無ければ 2（書き出しでも `--check` でも）。"""
    root = make_repo(tmp, {"README.md": "x\n"})
    p = []
    for args in ((), ("--check",)):
        r = run(script, root, *args)
        if r.code != 2:
            p.append(f"{args}: 終了コードが 2 でない: {r.code}")
    return p


def case_check_fresh(script: Path, tmp: Path) -> list[str]:
    """A4・A5: 書き出したあとは `--check` が 0。書き出しのバイトが変わる CLI で書き出し直しても 0。"""
    root = make_repo(tmp, SOURCES)
    p = []
    first = run(script, root, behaviour="nonce")
    second = run(script, root, behaviour="nonce")
    if first.code != 0 or second.code != 0:
        p.append(f"書き出せない: {first.code} {second.code}")
    if first.after.get("docs/a.svg") == second.after.get("docs/a.svg"):
        p.append("偽の CLI の書き出しのバイトが変わっていない（試料が働いていない）")
    r = run(script, root, "--check")
    if r.code != 0:
        p.append(f"書き出し直したあとの --check が 0 でない: {r.code} {r.stderr[-300:]}")
    return p


def case_orphan(script: Path, tmp: Path) -> list[str]:
    """A3・A10: 時間切れのあと、CLI の孫が一時ファイルの場所に書かない（プロセスグループごと止める）。"""
    root = make_repo(tmp, {"docs/v1/a.drawio": "<mxfile/>\n", "docs/v1/a.svg": PREVIOUS})
    started = time.time()
    r = run(script, root, behaviour="orphan", timeout="1")
    p = [] if r.code == 1 else [f"終了コードが 1 でない: {r.code}"]
    time.sleep(max(0.0, 9 - (time.time() - started)))
    after = snapshot(root)
    late = [k for k in after if Path(k).name.startswith(".") and k.endswith(".svg")]
    if late:
        p.append(f"時間切れのあとで孫が書いた: {late}")
    if after.get("docs/v1/a.svg") != PREVIOUS:
        p.append("前の svg が変わった")
    return p


def case_hangup(script: Path, tmp: Path) -> list[str]:
    """A3・A10: 書き出しの途中で本体が SIGHUP（端末を閉じた）で止められても、CLI が後から一時ファイルを置かない。"""
    root = make_repo(tmp, {"docs/v1/a.drawio": "<mxfile/>\n", "docs/v1/a.svg": PREVIOUS})
    started = time.time()
    r = run(script, root, behaviour="slow", hup_after=1.5)
    p = []
    if r.code == 0:
        p.append("SIGHUP で止めたのに 0 で終わった（試料が働いていない）")
    time.sleep(max(0.0, 6 - (time.time() - started)))
    after = snapshot(root)
    late = [k for k in after if Path(k).name.startswith(".") and k.endswith(".svg")]
    if late:
        p.append(f"止められたあとで CLI が書いた: {late}")
    if after.get("docs/v1/a.svg") != PREVIOUS:
        p.append("前の svg が変わった")
    return p


def ignored_case(sig: int) -> Callable[[Path, Path], list[str]]:
    def case(script: Path, tmp: Path) -> list[str]:
        """#820: 起動時に無視させられていたシグナルを書き出しの途中で受けても、止まらずに書き出して 0 で終わる（`nohup` の形）。"""
        root = make_repo(tmp, {"docs/v1/a.drawio": "<mxfile/>\n", "docs/v1/a.svg": PREVIOUS})
        r = run(script, root, behaviour="slow", hup_after=1.5, hup_signal=sig, ignored=True)
        p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-200:]}"]
        if r.log == []:
            p.append("CLI を起こしていない（試料が働いていない）")
        svg = r.after.get("docs/v1/a.svg")
        if svg is None or svg == PREVIOUS or svg_problem(svg) is not None:
            p.append("書き出していない")
        late = [k for k in r.after if Path(k).name.startswith(".") and k.endswith(".svg")]
        if late:
            p.append(f"一時ファイルが残った: {late}")
        return p
    return case


def case_no_killpg(script: Path, tmp: Path) -> list[str]:
    """A1: プロセスグループの無い OS（`os.killpg` が無い。Windows）でも書き出せる。"""
    root = make_repo(tmp, {"docs/a.drawio": "<mxfile/>\n"})
    r = run(script, root, pre="del os.killpg")
    p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-200:]}"]
    if "docs/a.svg" not in r.after:
        p.append("書き出さない")
    return p


def case_upper_suffix(script: Path, tmp: Path) -> list[str]:
    """A1・A6: 拡張子の大文字小文字を区別しない（`build-proposal.py` と同じ）。"""
    root = make_repo(tmp, {"docs/v1/spec/Arch.DRAWIO": "<mxfile/>\n"})
    r = run(script, root)
    p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-200:]}"]
    if "docs/v1/spec/Arch.svg" not in r.after:
        p.append("Arch.DRAWIO を書き出さない")
    c = run(script, root, "--check")
    if c.code != 0:
        p.append(f"--check が 0 でない: {c.code} {c.stderr[-200:]}")
    return p


def check_case(files: dict[str, bytes | str], expect: list[str]) -> Callable[[Path, Path], list[str]]:
    def case(script: Path, tmp: Path) -> list[str]:
        """A4: `--check` は名指しして 1。CLI を起動せず、何も書かない。"""
        root = make_repo(tmp, files)
        r = run(script, root, "--check")
        p = []
        if r.code != (1 if expect else 0):
            p.append(f"終了コード {r.code}: {r.stderr[-300:]}")
        for needle in expect:
            if needle not in r.stderr:
                p.append(f"{needle!r} を名指ししない: {r.stderr[-300:]}")
        if r.log:
            p.append("--check が CLI を起動した")
        if r.after != r.before:
            p.append("--check が書いた")
        return p
    return case


def check_case_absent(files: dict[str, bytes | str], absent: str) -> Callable[[Path, Path], list[str]]:
    def case(script: Path, tmp: Path) -> list[str]:
        """A4: `--check` が {absent!r} と言わない（ファイルシステムが大文字小文字を区別するかに依らない部分だけを見る）。"""
        root = make_repo(tmp, files)
        r = run(script, root, "--check")
        return [f"{absent!r} と言った: {r.stderr[-300:]}"] if absent in r.stderr else []
    return case


# --- BPMN（#901） ---------------------------------------------------------------

BPMN = '<?xml version="1.0" encoding="UTF-8"?>\n<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"/>\n'
MIXED = {
    "docs/a.drawio": "<mxfile>a</mxfile>\n",
    "docs/v1/requirements/flows/受注.bpmn": BPMN,
    "docs/v1/requirements/flows/z 出荷.bpmn": BPMN.replace("definitions", "definitions id=\"z\""),
    "docs/v1/spec/b.drawio": "<mxfile>b</mxfile>\n",
}
MIXED_OUTS = {k.rsplit(".", 1)[0] + ".svg" for k in MIXED}


def deps_dir(root: Path, skip: tuple[str, ...] = ()) -> Path:
    """`SPEC_LOOP_BPMN_DEPS` の偽物（中身は空のファイル。在るかだけを見られる）。"""
    deps = root / "_tools" / "deps"
    for name in DEPS_FILES:
        if name not in skip:
            (deps / name).parent.mkdir(parents=True, exist_ok=True)
            (deps / name).write_text("", encoding="utf-8")
    return deps


def case_bpmn_export(script: Path, tmp: Path) -> list[str]:
    """#901: `.bpmn` を drawio と混ぜてパスの順に、隣の `.svg` に同じ印で書き出す。描画口の引数は `<ソース> <一時ファイル>`。"""
    root = make_repo(tmp, MIXED)
    r = run(script, root)
    p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-300:]}"]
    for out in sorted(MIXED_OUTS):
        data = r.after.get(out)
        if data is None:
            p.append(f"{out} が無い")
            continue
        src = next(k for k in MIXED if k.rsplit(".", 1)[0] + ".svg" == out)
        if MARK.findall(data) != [sha(MIXED[src].encode("utf-8")).encode("ascii")]:
            p.append(f"{out}: 印がソースの指紋 1 つでない")
    p += only_svgs_changed(r, MIXED_OUTS)
    p += [f"一時ファイルが残った: {x}" for x in leftovers(r)]
    bpmn_calls = [a for a in r.log if "--output" not in a]
    if len(bpmn_calls) != 2:
        p.append(f"BPMN の描画口の呼び出しが {len(bpmn_calls)} 回: {r.log}")
    for args in bpmn_calls:
        if len(args) != 2 or not args[0].endswith(".bpmn"):
            p.append(f"BPMN の描画口の引数の形が違う: {args}")
            continue
        src, out = Path(args[0]), Path(args[1])
        if out.parent != src.parent or not out.name.endswith(".svg") or out.exists():
            p.append(f"一時ファイルの置き場所・名前が違う: {args}")
    order = [str(Path(a[0] if "--output" not in a else a[-1]).relative_to(root)) for a in r.log]
    if order != sorted(MIXED):
        p.append(f"パスの順に書き出していない: {order}")
    c = run(script, root, "--check")
    if c.code != 0:
        p.append(f"書き出したあとの --check が 0 でない: {c.code} {c.stderr[-300:]}")
    return p


def case_bpmn_only(script: Path, tmp: Path) -> list[str]:
    """#901: `.bpmn` だけなら draw.io の CLI が無くても書き出す（大文字の拡張子も）。"""
    root = make_repo(tmp, {"docs/v1/requirements/flows/Flow.BPMN": BPMN})
    r = run(script, root, drawio=" ")
    p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-300:]}"]
    if "docs/v1/requirements/flows/Flow.svg" not in r.after:
        p.append("Flow.BPMN を書き出さない")
    return p


def default_bpmn(script: Path, tmp: Path, use_chrome_path: bool, relative: bool = False) -> list[str]:
    root = make_repo(tmp, {"docs/v1/requirements/flows/受注.bpmn": BPMN})
    node = fake_exe(root, "bin/node")
    chrome = fake_exe(root, "chrome")
    deps = deps_dir(root)
    # relative: 依存と Chrome を cwd（偽の正本リポジトリの根）からの相対パスで渡す——描画口には絶対パスで届くこと（CR-1）
    given_deps = str(deps.relative_to(root)) if relative else str(deps)
    given_chrome = str(chrome.relative_to(root)) if relative else str(chrome)
    if use_chrome_path:
        r = run(script, root, bpmn=None, deps=given_deps, chrome=given_chrome, chrome_default="", path_dirs=[node.parent])
    else:
        r = run(script, root, bpmn=None, deps=given_deps, chrome_default=str(chrome), path_dirs=[node.parent])
    p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-300:]}"]
    if "docs/v1/requirements/flows/受注.svg" not in r.after:
        p.append("既定の描画口で書き出していない")
    if len(r.log) != 1:
        return p + [f"偽の node の呼び出しが {len(r.log)} 回"]
    args = r.log[0]
    expect = [str((script.parent / BPMN_SCRIPT).resolve()), "--deps", str(deps.resolve()), "--chrome", str(chrome.resolve())]
    # 絶対パスで渡っていること（相対のまま `resolve()` で一致させない）と、指す先が同じこと（`/var` と `/private/var` は同じ）
    got = [str(Path(a).resolve()) if Path(a).is_absolute() else a for a in args[:5]]
    if got != expect or len(args) != 7 or Path(args[5]).name != "受注.bpmn":
        p.append(f"既定の描画口の引数の形が違う: {args}（期待 {expect} <ソース> <一時ファイル>）")
    return p


def case_bpmn_default(script: Path, tmp: Path) -> list[str]:
    """#901: `BPMN_RENDER` が無ければ `node render-bpmn.mjs --deps <依存> --chrome <既定のパスの Chrome> <ソース> <一時ファイル>`。"""
    return default_bpmn(script, tmp, use_chrome_path=False)


def case_bpmn_chrome_path(script: Path, tmp: Path) -> list[str]:
    """#901: `CHROME_PATH` の Chrome を使う（既定のパスが無くても）。"""
    return default_bpmn(script, tmp, use_chrome_path=True)


def case_bpmn_relative(script: Path, tmp: Path) -> list[str]:
    """#901（CR-1）: 相対パスの `SPEC_LOOP_BPMN_DEPS`・`CHROME_PATH` は、絶対パスにして描画口に渡す。"""
    return default_bpmn(script, tmp, use_chrome_path=True, relative=True)


def case_bpmn_timeout_ignored(script: Path, tmp: Path) -> list[str]:
    """#901（CR-4）: `.bpmn` が無ければ `BPMN_TIMEOUT` を見ない——drawio だけのリポジトリは今までどおり書き出す。"""
    root = make_repo(tmp, {"docs/a.drawio": "<mxfile/>\n"})
    r = run(script, root, bpmn_timeout="0")
    p = [] if r.code == 0 else [f"終了コード {r.code}: {r.stderr[-200:]}"]
    if "docs/a.svg" not in r.after:
        p.append("書き出さない")
    return p


def bpmn_missing(reasons: list[str], setup: Callable[[Path, Path], dict], files: dict[str, bytes | str] | None = None
                 ) -> Callable[[Path, Path], list[str]]:
    def case(script: Path, tmp: Path) -> list[str]:
        """#901: BPMN の描画口に要るものが無ければ、無いものを全部名指しし、どちらの種類も何も書かずに 2。"""
        root = make_repo(tmp, files if files is not None else {**MIXED, "docs/a.svg": PREVIOUS})
        kwargs = setup(script, root)
        r = run(kwargs.pop("_script", script), root, **kwargs)
        p = []
        if r.code != 2:
            p.append(f"終了コードが 2 でない: {r.code} {r.stderr[-300:]}")
        if r.after != r.before:
            p.append("何か書いた")
        if r.log:
            p.append(f"描画系を呼んだ: {r.log}")
        if "書き出していない" not in r.stderr:
            p.append(f"「書き出していない」と言わない: {r.stderr[-300:]}")
        for reason in reasons:
            if reason not in r.stderr:
                p.append(f"理由 {reason!r} を言わない: {r.stderr[-400:]}")
        for src in (files if files is not None else MIXED):
            if src.lower().endswith((".drawio", ".bpmn")) and src not in r.stderr:
                p.append(f"{src} を名指ししない")
        return p
    return case


def no_tools(script: Path, root: Path) -> dict:
    return {"bpmn": None}


def deps_lacking(script: Path, root: Path) -> dict:
    node = fake_exe(root, "bin/node")
    return {"bpmn": None, "deps": str(deps_dir(root, skip=(DEPS_FILES[0], DEPS_FILES[3]))),
            "chrome_default": str(fake_exe(root, "chrome")), "path_dirs": [node.parent]}


def chrome_path_missing(script: Path, root: Path) -> dict:
    node = fake_exe(root, "bin/node")
    return {"bpmn": None, "deps": str(deps_dir(root)), "chrome": str(root / "_tools" / "no-chrome"),
            "chrome_default": str(fake_exe(root, "chrome")), "path_dirs": [node.parent]}


def script_missing(script: Path, root: Path) -> dict:
    # 描画口の無い写しを別の場所に作る（試料の間で共有する写しからは消さない）
    alone = root.parent / "alone"
    alone.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(script, alone / TARGET)
    node = fake_exe(root, "bin/node")
    return {"_script": alone / TARGET, "bpmn": None, "deps": str(deps_dir(root)), "chrome_default": str(fake_exe(root, "chrome")), "path_dirs": [node.parent]}


def bpmn_failing(behaviour: str, message: str, bpmn_timeout: str = "60") -> Callable[[Path, Path], list[str]]:
    def case(script: Path, tmp: Path) -> list[str]:
        """#901: BPMN の描画口が失敗したら前の `.svg` を変えず、書きかけを残さず、名指しして 1。"""
        root = make_repo(tmp, {"docs/v1/requirements/flows/a.bpmn": BPMN, "docs/v1/requirements/flows/a.svg": PREVIOUS})
        r = run(script, root, behaviour=behaviour, bpmn_timeout=bpmn_timeout)
        p = [] if r.code == 1 else [f"終了コードが 1 でない: {r.code} {r.stderr[-200:]}"]
        if r.after.get("docs/v1/requirements/flows/a.svg") != PREVIOUS:
            p.append("前の svg が変わった")
        p += [f"一時ファイルが残った: {x}" for x in leftovers(r)]
        if "docs/v1/requirements/flows/a.bpmn" not in r.stderr or message not in r.stderr:
            p.append(f"名指し・理由 {message!r} が無い: {r.stderr[-300:]}")
        return p
    return case


def case_bpmn_timeout_value(script: Path, tmp: Path) -> list[str]:
    """#901: `BPMN_TIMEOUT` が正の数でなければ 2（何も書かない）。"""
    root = make_repo(tmp, {"docs/v1/requirements/flows/a.bpmn": BPMN})
    r = run(script, root, bpmn_timeout="0")
    p = [] if r.code == 2 else [f"終了コードが 2 でない: {r.code}"]
    if r.after != r.before or r.log:
        p.append("何かした")
    if "BPMN_TIMEOUT" not in r.stderr:
        p.append(f"BPMN_TIMEOUT を名指ししない: {r.stderr[-200:]}")
    return p


def case_clash(script: Path, tmp: Path) -> list[str]:
    """#901: 同じ `X.svg` になるソース（`X.drawio` と `X.BPMN`）は、書き出しでも `--check` でも何も書かずに名指しして 2。"""
    files = {"docs/v1/flow.drawio": "<mxfile/>\n", "docs/v1/flow.BPMN": BPMN, "docs/v1/other.drawio": "<mxfile>o</mxfile>\n"}
    p = []
    for args in ((), ("--check",)):
        root = make_repo(tmp / ("check" if args else "write"), files)
        r = run(script, root, *args)
        if r.code != 2:
            p.append(f"{args}: 終了コードが 2 でない: {r.code}")
        if r.after != r.before or r.log:
            p.append(f"{args}: 何かした")
        if "docs/v1/flow.drawio" not in r.stderr or "docs/v1/flow.BPMN" not in r.stderr:
            p.append(f"{args}: 2 つのソースを名指ししない: {r.stderr[-300:]}")
    return p


def case_no_clash_by_case(script: Path, tmp: Path) -> list[str]:
    """#901（CR-3）: 名前が大文字小文字だけ違うソース（`Flow.drawio` と `flow.bpmn`）は、同じ書き出しとして止めない
    （大文字小文字を区別するファイルシステムでは別の書き出し。区別しないほうの扱いは docstring の「守らないもの」）。"""
    files = {"docs/v1/Flow.drawio": "<mxfile/>\n", "docs/v1/flow.bpmn": BPMN}
    p = []
    for args in ((), ("--check",)):
        root = make_repo(tmp / ("check" if args else "write"), files)
        r = run(script, root, *args)
        if "同じ書き出し" in r.stderr or r.code == 2:
            p.append(f"{args}: 同じ書き出しとして止めた: {r.code} {r.stderr[-300:]}")
    return p


def marked(source: str, body: bytes = b'<svg xmlns="http://www.w3.org/2000/svg"/>\n') -> bytes:
    return b"<!-- spec-loop-diagram-source: sha256=" + sha(source.encode("utf-8")).encode() + b" -->\n" + body


CASES: dict[str, Callable[[Path, Path], list[str]]] = {
    "書き出す": case_export,
    "XML 宣言の無い書き出し": case_nodecl,
    "前の印を置き換える": case_oldmark,
    "既定のパス": case_default_path,
    "PATH の drawio": case_path_drawio,
    "DRAWIO が空": case_drawio_empty,
    "DRAWIO が無いパス": case_drawio_missing,
    "どこにも無い": case_none_found,
    "0 以外で終わる": failing("nonzero", "0 以外で終わった（rc=3）"),
    "SVG を書いてから 0 以外で終わる": failing("svg_then_fail", "0 以外で終わった（rc=1）"),
    "書きかけで落ちる": failing("partial_then_fail", "0 以外で終わった（rc=1）"),
    "何も書かない": failing("nothing", "書き出しが作られなかった"),
    "空を書く": failing("empty", "空のファイル"),
    "XML でない": failing("not_xml", "XML として読めない"),
    "根が svg でない": failing("wrong_root", "根の要素が svg でない"),
    "時間切れ": failing("hang", "時間切れ", timeout="1"),
    "時間切れのあとで孫が書かない": case_orphan,
    "大文字の拡張子": case_upper_suffix,
    "SIGHUP で止められても CLI が後から書かない": case_hangup,
    "nohup の下で SIGHUP を受けても最後まで書き出す": ignored_case(signal.SIGHUP),
    "SIGTERM を無視させて起こしたら SIGTERM を受けても最後まで書き出す": ignored_case(signal.SIGTERM),
    "killpg の無い OS": case_no_killpg,
    "--check: 大文字小文字だけ違う書き出しはソースが無いと言わない": check_case_absent(
        {"docs/Arch.drawio": "<mxfile/>\n", "docs/ARCH.svg": marked("<mxfile/>\n")}, "ソースが無い"),
    "1 件の失敗で止まらない": case_partial_failure,
    ".drawio が 0 件": case_no_sources,
    "docs が無い": case_no_docs,
    "書き出し直しても新しい": case_check_fresh,
    "--check: 新しい": check_case({"docs/a.drawio": "<mxfile/>\n", "docs/a.svg": marked("<mxfile/>\n")}, []),
    "--check: 書き出しが無い": check_case({"docs/v1/a.drawio": "<mxfile/>\n"}, ["docs/v1/a.drawio: 書き出しが無い"]),
    "--check: 印が無い": check_case({"docs/a.drawio": "<mxfile/>\n", "docs/a.svg": PREVIOUS}, ["docs/a.svg: 印が無い"]),
    "--check: 古い": check_case({"docs/a.drawio": "<mxfile>new</mxfile>\n", "docs/a.svg": marked("<mxfile>old</mxfile>\n")},
                              ["docs/a.svg: 古い"]),
    "--check: ソースが無い": check_case({"docs/v1/spec/gone.svg": marked("<mxfile/>\n")}, ["docs/v1/spec/gone.svg: ソースが無い"]),
    "--check: 印の無いソースの無い svg は見ない": check_case({"docs/gantt.svg": PREVIOUS}, []),
    "--check: .drawio が 0 件": check_case({"docs/index.md": "x\n"}, []),
    "BPMN を書き出す": case_bpmn_export,
    "BPMN だけなら draw.io が無くても書く": case_bpmn_only,
    "BPMN の既定の描画口": case_bpmn_default,
    "BPMN の CHROME_PATH": case_bpmn_chrome_path,
    "BPMN: Node・依存・Chrome がどれも無い": bpmn_missing(
        ["Node が見つからない", "SPEC_LOOP_BPMN_DEPS", "Chrome が見つからない"], no_tools),
    "BPMN: 依存のファイルが足りない": bpmn_missing([DEPS_FILES[0], DEPS_FILES[3]], deps_lacking),
    "BPMN: CHROME_PATH が無いパス": bpmn_missing(["CHROME_PATH の Chrome が見つからない"], chrome_path_missing),
    "BPMN: 描画口のスクリプトが無い": bpmn_missing(["BPMN の描画口が無い"], script_missing),
    "BPMN: BPMN_RENDER が空": bpmn_missing(["BPMN_RENDER が空"], lambda s, r: {"bpmn": " "}),
    "BPMN: BPMN_RENDER が無いパス": bpmn_missing(["BPMN_RENDER の描画口が見つからない"],
                                               lambda s, r: {"bpmn": str(r / "_tools" / "no-such-render")}),
    "BPMN: draw.io も無ければ両方を名指しする": bpmn_missing(["draw.io の CLI が見つからない", "Node が見つからない"],
                                                   lambda s, r: {"bpmn": None, "drawio": None}),
    "BPMN: 0 以外で終わる": bpmn_failing("nonzero", "BPMN の描画口が 0 以外で終わった（rc=3）"),
    "BPMN: XML でない": bpmn_failing("not_xml", "XML として読めない"),
    "BPMN: 時間切れ": bpmn_failing("hang", "BPMN の描画口が時間切れ", bpmn_timeout="1"),
    "BPMN_TIMEOUT が正の数でない": case_bpmn_timeout_value,
    "同じ書き出しになるソース": case_clash,
    "大文字小文字だけ違う名前は同じ書き出しとして止めない": case_no_clash_by_case,
    "BPMN: 相対パスの依存と Chrome": case_bpmn_relative,
    "drawio だけなら BPMN_TIMEOUT を見ない": case_bpmn_timeout_ignored,
    "--check: BPMN が新しい": check_case({"docs/v1/requirements/flows/a.bpmn": BPMN,
                                         "docs/v1/requirements/flows/a.svg": marked(BPMN)}, []),
    "--check: BPMN の書き出しが無い": check_case({"docs/v1/requirements/flows/a.bpmn": BPMN},
                                              ["docs/v1/requirements/flows/a.bpmn: 書き出しが無い"]),
    "--check: BPMN の書き出しが古い": check_case({"docs/v1/requirements/flows/a.bpmn": BPMN,
                                              "docs/v1/requirements/flows/a.svg": marked(BPMN + "<!-- old -->\n")},
                                             ["docs/v1/requirements/flows/a.svg: 古い"]),
    "--check: BPMN の書き出しの印が無い": check_case({"docs/v1/requirements/flows/a.bpmn": BPMN,
                                                "docs/v1/requirements/flows/a.svg": PREVIOUS},
                                               ["docs/v1/requirements/flows/a.svg: 印が無い"]),
    "--check: 大文字の拡張子の svg もソースが無いと言う": check_case({"docs/v1/spec/gone.SVG": marked("<mxfile/>\n")},
                                                         ["docs/v1/spec/gone.SVG: ソースが無い"]),
}

# (名前, 壊す前, 壊した後, 殺すはずの試料の名前)
MUTATIONS: list[tuple[str, str, str, str]] = [
    ("印の照合を外す", "        elif got != source_digest(data):", "        elif False:", "--check: 古い"),
    ("見つからないときの 2 を 0 にする", '            print(f"  {rel(source, root)}", file=sys.stderr)\n        return 2\n',
     '            print(f"  {rel(source, root)}", file=sys.stderr)\n        return 0\n', "どこにも無い"),
    ("失敗のとき前の svg を消す", "    tmp: Path | None = None\n", "    out.unlink(missing_ok=True)\n    tmp: Path | None = None\n",
     "0 以外で終わる"),
    ("失敗のとき書きかけを置く", '            return f"{label}が 0 以外で終わった',
     '            tmp.is_file() and os.replace(tmp, out); return f"{label}が 0 以外で終わった', "書きかけで落ちる"),
    ("--check で書く", "    if args.check:\n", "    if False:\n", "--check: 書き出しが無い"),
    ("終了コードを見ない", "        if proc.returncode != 0:", "        if False:", "SVG を書いてから 0 以外で終わる"),
    ("在るかを見ない", "        if not tmp.is_file():", "        if False:", "何も書かない"),
    ("SVG かを見ない", "        broken = not_svg(svg)", "        broken = None", "XML でない"),
    ("根の要素を見ない", '    if root.tag != "svg" and not root.tag.endswith("}svg"):', "    if False:", "根が svg でない"),
    ("空を見ない", "    if not data:\n        return \"空のファイル\"", "    if False:\n        return \"空のファイル\"", "空を書く"),
    ("一時ファイルを消さない", "                tmp.unlink(missing_ok=True)", "                pass", "SVG を書いてから 0 以外で終わる"),
    ("時間切れを待たない", "timeout=timeout)", "timeout=None)", "時間切れ"),
    ("ソースが無いを見ない", "        if got is not None:\n            problems.append", "        if False:\n            problems.append",
     "--check: ソースが無い"),
    ("前の印を消さない", '    body = MARK_RE.sub(b"", svg)', "    body = svg", "前の印を置き換える"),
    ("入れ子を見ない", '            if name.lower().endswith(SUFFIXES):', '            if name.lower().endswith(SUFFIXES) and Path(dirpath) == docs:',
     "書き出す"),
    ("指紋を書き出しから取る", "f.write(mark(svg, source_digest(data)))", "f.write(mark(svg, source_digest(svg)))", "書き出す"),
    ("印を XML 宣言の前に置く", "    if decl:\n", "    if False:\n", "書き出す"),
    ("既定のパスを見ない", "    if default and os.path.isfile(default)", "    if False and os.path.isfile(default)", "既定のパス"),
    ("PATH を見ない", '    on_path = shutil.which("drawio")', "    on_path = None", "PATH の drawio"),
    ("DRAWIO の無いパスを通す", '            return None, f"DRAWIO の CLI が見つからない', '            return command, f"DRAWIO の CLI が見つからない',
     "DRAWIO が無いパス"),
    ("DRAWIO が空を名指ししない", '            return None, "DRAWIO が空"', '            command = ["true"]', "DRAWIO が空"),
    ("プロセスグループを止めない", "        os.killpg(proc.pid, signal.SIGKILL)", "        pass", "時間切れのあとで孫が書かない"),
    ("拡張子の大文字小文字を区別する", '            if name.lower().endswith(SUFFIXES):', '            if name.endswith(SUFFIXES):', "大文字の拡張子"),
    ("SIGHUP を受けない", '    for name in ("SIGTERM", "SIGHUP"):', '    for name in ():', "SIGHUP で止められても CLI が後から書かない"),
    # #820 の後退そのもの: 起動時の SIG_IGN を見ずに、無条件に登録する
    ("無視させられた SIGHUP にも登録する", ") != signal.SIG_IGN:", ") != signal.SIG_IGN or True:",
     "nohup の下で SIGHUP を受けても最後まで書き出す"),
    ("無視させられた SIGTERM にも登録する", ") != signal.SIG_IGN:", ") != signal.SIG_IGN or True:",
     "SIGTERM を無視させて起こしたら SIGTERM を受けても最後まで書き出す"),
    ("killpg の無い OS を見ない", '        if hasattr(os, "killpg"):', "        if True:", "killpg の無い OS"),
    ("孤立の判定で大文字小文字を区別する", "        if str(svg).lower() in exported:", "        if str(svg) in exported:",
     "--check: 大文字小文字だけ違う書き出しはソースが無いと言わない"),
    ("1 件の失敗で止まる", "            failed.append(rel(source, root))", "            failed.append(rel(source, root)); break",
     "1 件の失敗で止まらない"),
    # BPMN（#901）
    ("BPMN を見ない", 'SUFFIXES = (".drawio", ".bpmn")', 'SUFFIXES = (".drawio",)', "BPMN を書き出す"),
    ("BPMN に draw.io の引数を渡す", "        if is_bpmn(source):\n            cmd = [*command, str(source), str(tmp)]",
     "        if False:\n            cmd = [*command, str(source), str(tmp)]", "BPMN を書き出す"),
    ("BPMN の描画系が無くても drawio を書く", "        reasons += missing", "        pass", "BPMN: Node・依存・Chrome がどれも無い"),
    ("draw.io が在れば BPMN の描画系を探さない", "    if any(is_bpmn(source) for source in sources):\n        bpmn, missing",
     "    if command is None and any(is_bpmn(source) for source in sources):\n        bpmn, missing", "BPMN: Node・依存・Chrome がどれも無い"),
    ("Node を見ない", "    if node is None:", "    if False:", "BPMN: Node・依存・Chrome がどれも無い"),
    ("依存のファイルを見ない", "            if not os.path.isfile(os.path.join(deps, name)):", "            if False:",
     "BPMN: 依存のファイルが足りない"),
    ("無いものを 1 つしか言わない", "    if reasons:\n        return None, reasons", "    if reasons:\n        return None, reasons[:1]",
     "BPMN: Node・依存・Chrome がどれも無い"),
    ("Chrome の既定のパスを見ない", "        if not (chrome and os.path.isfile(chrome) and os.access(chrome, os.X_OK)):",
     "        if not chrome:", "BPMN: Node・依存・Chrome がどれも無い"),
    ("CHROME_PATH を見ない", '    chrome = os.environ.get("CHROME_PATH")', "    chrome = None", "BPMN の CHROME_PATH"),
    ("CHROME_PATH の無いパスを通す", "        if not (os.path.isfile(chrome) and os.access(chrome, os.X_OK)):", "        if False:",
     "BPMN: CHROME_PATH が無いパス"),
    ("描画口のスクリプトを見ない", "    if not script.is_file():", "    if False:", "BPMN: 描画口のスクリプトが無い"),
    ("既定の描画口に依存を渡さない", '"--deps", deps, ', "", "BPMN の既定の描画口"),
    ("BPMN_RENDER の無いパスを通す", "        if not executable(command[0]):", "        if False:", "BPMN: BPMN_RENDER が無いパス"),
    ("BPMN_RENDER が空を通す", '            return None, ["BPMN_RENDER が空"]', '            command = ["true"]', "BPMN: BPMN_RENDER が空"),
    ("BPMN の時間切れに draw.io の値を使う", 'timeouts["BPMN_TIMEOUT"], root)', 'timeouts["DRAWIO_TIMEOUT"], root)', "BPMN: 時間切れ"),
    ("時間切れの値を確かめない", "            if not timeouts[name] > 0:", "            if False:", "BPMN_TIMEOUT が正の数でない"),
    ("同じ書き出しを見ない", "    if clashes:", "    if False:", "同じ書き出しになるソース"),
    ("同じ書き出しの判定で大文字小文字を区別しない", "by_output.setdefault(str(output_of(source)), [])",
     "by_output.setdefault(str(output_of(source)).lower(), [])", "大文字小文字だけ違う名前は同じ書き出しとして止めない"),
    ("依存を絶対パスにしない", "        deps = os.path.abspath(deps)", "        deps = deps", "BPMN: 相対パスの依存と Chrome"),
    ("Chrome を絶対パスにしない", '"--chrome", os.path.abspath(chrome)]', '"--chrome", str(chrome)]', "BPMN: 相対パスの依存と Chrome"),
    ("無い種類の時間切れも確かめる", "        if not present:\n            continue", "        if False:\n            continue",
     "drawio だけなら BPMN_TIMEOUT を見ない"),
    # #904 の残課題 P2-5
    ("svg の拡張子の大文字小文字を区別する", '            if name.lower().endswith(".svg"):', '            if name.endswith(".svg"):',
     "--check: 大文字の拡張子の svg もソースが無いと言う"),
]


def copy_script(dest: Path, source: str | None = None) -> Path:
    """本体と、同じ場所に置く BPMN の描画口（既定の描画口の試料が引数の形を見る。走らせはしない）を写す。"""
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / TARGET
    path.write_text(source if source is not None else (SCRIPTS / TARGET).read_text(encoding="utf-8"), encoding="utf-8")
    shutil.copyfile(SCRIPTS / BPMN_SCRIPT, dest / BPMN_SCRIPT)
    return path


def main() -> int:
    failures: list[str] = []
    original = (SCRIPTS / TARGET).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="render-diagrams-test-") as tmp:
        tmp_path = Path(tmp)
        assert REAL_REPO not in tmp_path.resolve().parents, "一時ディレクトリが実リポジトリの中にある"
        script = copy_script(tmp_path / "scripts")
        # 陽性対照: 壊す前の本体で全部の試料が期待どおり
        for index, (name, case) in enumerate(CASES.items()):
            problems = case(script, tmp_path / f"case{index}")
            if problems:
                failures.append(f"試料が期待どおりでない: {name}: " + "; ".join(problems)[:600])
        names = list(CASES)
        for index, (name, before, after, killer) in enumerate(MUTATIONS):
            if killer not in CASES:
                failures.append(f"変異の試料が無い: {name}（{killer}）")
                continue
            count = original.count(before)
            if count != 1:
                failures.append(f"変異が届いていない: {name}（壊す箇所が {count} 回現れる）")
                continue
            mutated = copy_script(tmp_path / f"mut{index}", original.replace(before, after))
            problems = CASES[killer](mutated, tmp_path / f"mutwork{index}" / f"case{names.index(killer)}")
            if not problems:
                failures.append(f"変異が生き残った: {name}（{killer} で殺せるはず）")
    if (SCRIPTS / TARGET).read_text(encoding="utf-8") != original:
        failures.append("テストが本体を書き換えた")
    if failures:
        print(f"{len(failures)} 件の失敗:\n")
        for message in failures:
            print(f"  - {message}")
        return 1
    print(f"OK: 試料 {len(CASES)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
