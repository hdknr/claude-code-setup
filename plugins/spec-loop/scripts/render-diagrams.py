#!/usr/bin/env python3
"""正本リポジトリの `docs/` の下の drawio（`*.drawio`）を SVG に書き出し、ソースの指紋を書き出しに書き込む。

usage: python3 render-diagrams.py [<正本リポジトリの根>] [--check]

**図の決まり（描かないもの・置き場所・形式）の正は `references/tree.md` の「図」である**（このプラグインの中にある）。

- **対象は `<根>/docs/` の下を再帰した `*.drawio`**（入れ子を含む。パスの順に処理する）。根の既定は cwd。
- **各 `X.drawio` を、同じディレクトリの `X.svg` に書き出す。** 書き出しには、ソースのバイトの sha256 を印として書き込む:
  `<!-- spec-loop-diagram-source: sha256=<64 桁> -->`（XML 宣言があればその直後、無ければ先頭。前の印は置き換える）。
- **`--check` は draw.io を起動せず、何も書かない。** 各 `X.drawio` について `X.svg` が無い・印が無い・印の指紋が今のソースと違う
  ものと、`docs/` の下で印を持つ `.svg` のうち同じ名前の `.drawio` が無いもの（ソースが無い）を名指しする。
- **印はソースのバイトだけで決まる。** draw.io は同じソースからでもバイトの一致する書き出しを作らない（このリポジトリの
  `CLAUDE.md` の実測）ので、書き出しのバイトは比べない——書き出し直しても `--check` の結果は変わらない。
- 標準ライブラリだけを使う。

draw.io の CLI は次の順に探す:

1. 環境変数 `DRAWIO`（`shlex.split` で分ける。`DRAWIO="xvfb-run -a drawio"` のように前置きもできる）。空なら 2
2. macOS の既定のパス `/Applications/draw.io.app/Contents/MacOS/draw.io`（在って実行できれば）。
   **環境変数 `SPEC_LOOP_DRAWIO_DEFAULT` で既定のパスを差し替えられる**（空なら既定のパスを見ない。テストが本物の draw.io を拾わないため）
3. `PATH` の `drawio`

書き出しのコマンドは `<CLI> --export --format svg --output <一時ファイル> <X.drawio>`。一時ファイルは `X.svg` と同じディレクトリに置き、
**成功の判定は 3 つ全部**——終了コード 0・一時ファイルが在って空でない・XML として読めて根の要素が `svg`（名前空間つきでよい）。
通ったら印を書き込み、`os.replace` で `X.svg` に置く。1 件の時間切れは環境変数 `DRAWIO_TIMEOUT`（秒。既定 600）。

終了コード:

- 0: 全部書き出した（`.drawio` が 0 件なら何もせずにそう言う）。`--check` では、どの `.drawio` にも今のソースの印を持つ `.svg` があり、
  ソースの無い印つきの `.svg` も無い
- 1: 書き出しに失敗したファイルがある——**そのファイルの前の `X.svg` は変えず、一時ファイルは消し、名指しして残りのファイルを続ける**。
  `--check` では、古い・無い・印が無い書き出しか、ソースの無い印つきの `.svg` がある（全部を 1 行ずつ名指しする）
- 2: 引数の誤り・`<根>/docs/` が無い・`DRAWIO_TIMEOUT` が正の数でない・**draw.io の CLI が見つからない**（`DRAWIO` が空・指したものが無いを含む）
  ——CLI が見つからないときは**何も書かず**、標準エラーに「書き出していない」と書き出していない `.drawio` を名指しする。
  想定外の例外で止まったときも 2

| 守るもの | 守らないもの |
| --- | --- |
| `docs/` の下の `.drawio` を全部、隣の同じ名前の `.svg` に書き出す | **書き出すのは各 `.drawio` の 1 ページ目だけ**（draw.io の CLI の既定）。複数ページの図の 2 ページ目から先は書き出さない |
| 失敗したファイルの前の `.svg` を変えず、書きかけを残さない | **印だけ手で書き換えて書き出さない形は見えない**（印はソースの指紋を書き出しの中に持つだけ。このリポジトリの `check-diagram-freshness.py` と同じ原理的な限界） |
| `--check` は draw.io を起動せず、何も書かない | **確かめたのは macOS の draw.io だけ**（Linux・Windows の CLI は確かめていない。`DRAWIO` で差し替えて、書き出しを目で確かめる） |
| 書くのは `.drawio` の隣の `.svg` と、同じ場所の一時ファイル（成否に依らず消す）だけ。CLI は自分のプロセスグループで起こし、終わったら（時間切れでも、このスクリプトが SIGTERM・SIGHUP で止められても）グループごと止める——前置き（`xvfb-run`）の孫が後から書かない（SIGKILL で止められたときは後始末できない）。**起動時に無視させられていたシグナル（`nohup` の SIGHUP）は無視したまま**——止まらずに最後まで書き出す。拡張子の大文字小文字は区別しない（`build-proposal.py` と同じ） | **見た目の品質**（利用者・決裁者に見せられる図か）。ブラウザで開いて目で見る |
| 印はソースのバイトだけで決まる | `X.svg` が symlink のときの扱い（`os.replace` はリンクを置き換える）・`docs/` の外の図・symlink のディレクトリの中（辿らない） |
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_DRAWIO = "/Applications/draw.io.app/Contents/MacOS/draw.io"
TIMEOUT_DEFAULT = 600

MARK_HEAD = b"<!-- spec-loop-diagram-source: sha256="
# 印。書き込むときは前の印（と直後の改行 1 つ）を全部消してから 1 つ書く
MARK_RE = re.compile(rb"<!-- spec-loop-diagram-source: sha256=([0-9a-f]{64}) -->\n?")
BOM = b"\xef\xbb\xbf"
XML_DECL = re.compile(rb"\A(?:\xef\xbb\xbf)?<\?xml[^>]*\?>")


def source_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mark(svg: bytes, digest: str) -> bytes:
    """書き出しに印を書き込む。前の印は置き換える。"""
    body = MARK_RE.sub(b"", svg)
    line = MARK_HEAD + digest.encode("ascii") + b" -->"
    decl = XML_DECL.match(body)
    if decl:
        return body[:decl.end()] + b"\n" + line + body[decl.end():]
    if body.startswith(BOM):
        return BOM + line + b"\n" + body[len(BOM):]
    return line + b"\n" + body


def marked_digest(svg: bytes) -> str | None:
    """書き出しの印の指紋。印が無ければ None。"""
    found = MARK_RE.search(svg)
    return found.group(1).decode("ascii") if found else None


def not_svg(data: bytes) -> str | None:
    """SVG として読めなければ理由を返す。"""
    if not data:
        return "空のファイル"
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return f"XML として読めない（{e}）"
    if root.tag != "svg" and not root.tag.endswith("}svg"):
        return f"根の要素が svg でない（{root.tag}）"
    return None


def find_sources(docs: Path) -> list[Path]:
    """`docs/` の下の `.drawio` をパスの順に。symlink のディレクトリは辿らない。"""
    found: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(docs):
        for name in filenames:
            if name.lower().endswith(".drawio"):
                found.append(Path(dirpath) / name)
    return sorted(found, key=lambda p: str(p))


def find_svgs(docs: Path) -> list[Path]:
    found: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(docs):
        for name in filenames:
            if name.endswith(".svg"):
                found.append(Path(dirpath) / name)
    return sorted(found, key=lambda p: str(p))


def output_of(source: Path) -> Path:
    return source.with_suffix(".svg")


def drawio_command() -> tuple[list[str] | None, str]:
    """draw.io の CLI の起動コマンドと、見つからなかったときの理由。"""
    raw = os.environ.get("DRAWIO")
    if raw is not None:
        command = shlex.split(raw)
        if not command:
            return None, "DRAWIO が空"
        binary = command[0]
        if shutil.which(binary) is None and not (os.path.isfile(binary) and os.access(binary, os.X_OK)):
            return None, f"DRAWIO の CLI が見つからない（{binary}）"
        return command, ""
    default = os.environ.get("SPEC_LOOP_DRAWIO_DEFAULT", DEFAULT_DRAWIO)
    if default and os.path.isfile(default) and os.access(default, os.X_OK):
        return [default], ""
    on_path = shutil.which("drawio")
    if on_path:
        return [on_path], ""
    shown = f"{default}・" if default else ""
    return None, f"draw.io の CLI が見つからない（{shown}PATH の drawio。DRAWIO で指定する）"


def kill_group(proc: subprocess.Popen[str]) -> None:
    """CLI のプロセスグループに残ったもの（前置きの孫など）を止める。もう無ければ何もしない。"""
    try:
        if hasattr(os, "killpg"):
            os.killpg(proc.pid, signal.SIGKILL)
        else:  # プロセスグループの無い OS（Windows）では CLI だけを止める
            proc.kill()
    except (ProcessLookupError, PermissionError):
        pass


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def export_one(source: Path, command: list[str], timeout: float, root: Path) -> str | None:
    """1 件書き出す。失敗したら理由を返す（前の `.svg` は変えない。一時ファイルは消す）。"""
    out = output_of(source)
    try:
        data = source.read_bytes()
    except OSError as e:
        return f"ソースを読めない（{e.strerror}）"
    tmp: Path | None = None
    try:
        fd, name = tempfile.mkstemp(prefix=f".{out.stem}.", suffix=".svg", dir=out.parent)
        os.close(fd)
        tmp = Path(name)
        # **先に消してから書かせる**——「在ること」がそのまま「CLI が今回書いたこと」になる
        tmp.unlink()
        cmd = [*command, "--export", "--format", "svg", "--output", str(tmp), str(source)]
        try:
            # **自分のプロセスグループで起こし、終わったらグループごと止める**——`DRAWIO="xvfb-run -a drawio"` のような前置きの
            # 孫が時間切れのあとも生き残ると、一時ファイルを消したあとに書きかけを置く
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
                                    start_new_session=True)
        except OSError as e:
            return f"draw.io の CLI を起動できない（{e.strerror}）"
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            kill_group(proc)
            proc.communicate()
            return f"draw.io の CLI が時間切れになった（{timeout:g} 秒）"
        finally:
            kill_group(proc)
        detail = (stdout + stderr).strip()
        tail = f"\n    {detail[-400:]}" if detail else ""
        if proc.returncode != 0:
            return f"draw.io の CLI が 0 以外で終わった（rc={proc.returncode}）{tail}"
        if not tmp.is_file():
            return f"書き出しが作られなかった（rc=0）{tail}"
        svg = tmp.read_bytes()
        broken = not_svg(svg)
        if broken is not None:
            return f"書き出しが SVG でない（{broken}）{tail}"
        with tmp.open("wb") as f:
            f.write(mark(svg, source_digest(data)))
        os.replace(tmp, out)
        return None
    except OSError as e:
        return f"書けない（{e.strerror}）"
    finally:
        try:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
        except OSError as e:
            print(f"{rel(tmp, root)}: 一時ファイルを消せない（{e.strerror}）", file=sys.stderr)


def check(docs: Path, root: Path, sources: list[Path]) -> int:
    problems: list[str] = []
    for source in sources:
        out = output_of(source)
        try:
            data = source.read_bytes()
        except OSError as e:
            problems.append(f"{rel(source, root)}: ソースを読めない（{e.strerror}）")
            continue
        if not out.is_file():
            problems.append(f"{rel(source, root)}: 書き出しが無い（{rel(out, root)}）")
            continue
        try:
            got = marked_digest(out.read_bytes())
        except OSError as e:
            problems.append(f"{rel(out, root)}: 書き出しを読めない（{e.strerror}）")
            continue
        if got is None:
            problems.append(f"{rel(out, root)}: 印が無い（render-diagrams.py で書き出していない）")
        elif got != source_digest(data):
            problems.append(f"{rel(out, root)}: 古い（ソース {rel(source, root)} を直したあと書き出していない）")
    # 大文字小文字だけ違う名前も、ソースの書き出しとして数える（区別しないファイルシステムでは同じファイル）
    exported = {str(output_of(source)).lower() for source in sources}
    for svg in find_svgs(docs):
        if str(svg).lower() in exported:
            continue
        try:
            got = marked_digest(svg.read_bytes())
        except OSError:
            continue
        if got is not None:
            problems.append(f"{rel(svg, root)}: ソースが無い（{rel(svg.with_suffix('.drawio'), root)}）")
    for line in problems:
        print(line, file=sys.stderr)
    if problems:
        print(f"{len(problems)} 件の書き出しが今のソースと合わない", file=sys.stderr)
        return 1
    print(f"{len(sources)} 件の書き出しは今のソースのもの")
    return 0


def stop_on_signal(signum: int, _frame: object) -> None:
    """SIGTERM・SIGHUP で止められたら、例外にして後始末（CLI のグループを止め、一時ファイルを消す）を走らせる。

    CLI は自分のプロセスグループにいるので、端末を閉じたときの SIGHUP やグループへの SIGTERM は CLI に届かない。
    後始末を走らせずに止まると、生き残った CLI が後から一時ファイルを置く。
    起動時に無視させられていたシグナル（`nohup` の SIGHUP）には登録しない（#820）。"""
    raise SystemExit(128 + signum)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="docs/ の下の drawio を SVG に書き出す（--check で鮮度を見る）")
    parser.add_argument("root", nargs="?", default=".", help="正本リポジトリの根（既定は cwd）")
    parser.add_argument("--check", action="store_true", help="書き出さずに、書き出しが今のソースのものかを見る")
    args = parser.parse_args(argv)

    root = Path(args.root)
    docs = root / "docs"
    if not docs.is_dir():
        print(f"{docs}: docs/ が無い。正本リポジトリの根を渡す", file=sys.stderr)
        return 2
    sources = find_sources(docs)

    if args.check:
        return check(docs, root, sources)

    raw_timeout = os.environ.get("DRAWIO_TIMEOUT", str(TIMEOUT_DEFAULT))
    try:
        timeout = float(raw_timeout)
        if not timeout > 0:
            raise ValueError
    except ValueError:
        print(f"DRAWIO_TIMEOUT が正の数でない（{raw_timeout!r}）", file=sys.stderr)
        return 2

    if not sources:
        print("書き出す .drawio が無い（0 件）")
        return 0

    # **1 件も書く前に CLI を探す。** 見つからなければ何も書かない
    command, reason = drawio_command()
    if command is None:
        print(f"エラー: {reason}", file=sys.stderr)
        print(f"書き出していない（{len(sources)} 件）:", file=sys.stderr)
        for source in sources:
            print(f"  {rel(source, root)}", file=sys.stderr)
        return 2

    failed: list[str] = []
    for source in sources:
        print(f"{rel(source, root)} -> {rel(output_of(source), root)}")
        reason = export_one(source, command, timeout, root)
        if reason is not None:
            print(f"{rel(source, root)}: 失敗: {reason}（前の {output_of(source).name} は変えていない）", file=sys.stderr)
            failed.append(rel(source, root))
    if failed:
        print(f"{len(failed)} 件の書き出しに失敗した: {', '.join(failed)}", file=sys.stderr)
        return 1
    print(f"{len(sources)} 件書き出した")
    return 0


if __name__ == "__main__":
    for name in ("SIGTERM", "SIGHUP"):
        # **起動時に無視させられていたら（`nohup` の SIGHUP など。SIG_IGN）登録しない**——上書きすると、無視させて起動した側の
        # 意図を破って止まる（#820）。無視したままなら止まらないので、後始末も要らない
        if hasattr(signal, name) and signal.getsignal(getattr(signal, name)) != signal.SIG_IGN:
            signal.signal(getattr(signal, name), stop_on_signal)
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も 2（トレースバックの 1 に化けさせない）
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）", file=sys.stderr)
        sys.exit(2)
