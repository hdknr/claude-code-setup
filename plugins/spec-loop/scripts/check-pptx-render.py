#!/usr/bin/env python3
"""生成した PPTX を PDF に描画して、機械で探せるずれを探し、1 ページずつの PNG を書く（#1289）。

usage: python3 check-pptx-render.py <PPTX>… [--out <PNG の出力先>] [--dpi <解像度>]

`build-proposal.py --pptx` が作った提案書・仕様書の PPTX を、**渡す前に**描画して確かめる（proposal の `SKILL.md` の手順 3 のあと）。
**機械で探すもの**（見つけたら 1 で終わり、ページと文字を名指しする）:

- **見切れ**: 文字に省略記号（`…`）がある（PPTX の本文と、描画した PDF の文字の両方）。
- **図の中の代わりの文字**: `Text is not SVG`（drawio の書き出しが付けるもの）がある。**図を PNG にした後の画像の中の文字は見えない**——目で見る。
- **はみ出し**: 描画した文字がページの外に出ている・文字どうしが重なっている（行が増えて前の行に被さる）・文字が枠の下の辺をまたいでいる。

**目で見るもの**（機械では決まらない）: 書き出した 1 ページずつの PNG（`--out`。既定は PPTX の隣の `<PPTX の名前>-pages/`）を、費用・期間・決定事項・図の順に開いて見る。
この道具が 0 で終わっても、見た目が読めることの証明ではない——**探せるのは上の 3 つだけ**である。

**描画の道具が無ければ確かめられない（3）**——LibreOffice（`soffice`。環境変数 `SOFFICE` で差し替え）・`pdftotext`・`pdftoppm`（poppler）。
3 は緑ではない: 「確かめていない」を報告に書く（弱い検査で代替して緑と書かない）。PPTX の本文（`…`・`Text is not SVG`）は、道具が無くても見られるので、
その結果は出すが、終わりは 3 のままにする。

終了コード:

- 0: 見つからなかった（描画して確かめた。PNG を書いた）
- 1: 見つかった（ページと文字を名指しする。PNG は書く）
- 2: 引数の誤り・PPTX が読めない・描画に失敗した（確かめていない）
- 3: 描画の道具が無い（確かめられていない。PPTX の本文だけ見た結果は出す）

**守らないもの**: PowerPoint での見え方（LibreOffice で描画する。フォントが違えば折り返しが変わる）・図の画像の中の文字・配色や読みやすさ。
標準ライブラリだけを使い、PPTX には書き込まない。**CI からは呼ばない**（道具が無い）。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ELLIPSIS = "…"
ALT = "Text is not SVG"
EMU_PT = 12700
OVERLAP = 0.25     # 小さいほうの面積のこの割合を超えて重なる 2 つの語を重なりと数える
TOLERANCE = 1.5    # pt。ページ・枠の辺の許容
TIMEOUT = 300
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def tools() -> tuple[dict[str, str], list[str]]:
    found, missing = {}, []
    soffice = os.environ.get("SOFFICE") or shutil.which("soffice")
    for name, path in (("soffice", soffice), ("pdftotext", shutil.which("pdftotext")), ("pdftoppm", shutil.which("pdftoppm"))):
        if path:
            found[name] = path
        else:
            missing.append(name)
    return found, missing


def slide_texts(pptx: Path) -> list[tuple[int, str]]:
    """(スライドの番号, 本文) の並び。PPTX を zip として読み、`a:t` を順に集める。"""
    out = []
    with zipfile.ZipFile(pptx) as z:
        names = sorted((n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                       key=lambda n: int(re.sub(r"\D", "", n)))
        for n in names:
            root = ElementTree.fromstring(z.read(n))
            out.append((int(re.sub(r"\D", "", n)), "".join(t.text or "" for t in root.iter(f"{{{NS['a']}}}t"))))
    return out


def text_findings(pptx: Path) -> list[str]:
    found = []
    for number, text in slide_texts(pptx):
        for m in re.finditer(re.escape(ELLIPSIS), text):
            found.append(f"{pptx.name} {number} ページ: 見切れ（省略記号）: …{text[max(0, m.start() - 20):m.end() + 10]}")
        if ALT in text:
            found.append(f"{pptx.name} {number} ページ: 図の代わりの文字（{ALT}）がある")
    return found


def text_boxes(pptx: Path) -> dict[int, list[tuple[float, float, float, float]]]:
    """スライドごとの、文字を持つ図形の枠（pt。左上が原点）。表・図は除く。"""
    out: dict[int, list] = {}
    with zipfile.ZipFile(pptx) as z:
        for n in z.namelist():
            if not re.fullmatch(r"ppt/slides/slide\d+\.xml", n):
                continue
            root = ElementTree.fromstring(z.read(n))
            boxes = []
            for sp in root.iter(f"{{{NS['p']}}}sp"):
                if not any((t.text or "").strip() for t in sp.iter(f"{{{NS['a']}}}t")):
                    continue
                off, ext = sp.find(".//a:off", NS), sp.find(".//a:ext", NS)
                if off is None or ext is None:
                    continue
                boxes.append((int(off.get("x")) / EMU_PT, int(off.get("y")) / EMU_PT,
                              int(ext.get("cx")) / EMU_PT, int(ext.get("cy")) / EMU_PT))
            out[int(re.sub(r"\D", "", n))] = boxes
    return out


WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')
PAGE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', re.S)


def render_findings(name: str, pdf: Path, pdftotext: str, boxes: dict[int, list]) -> list[str]:
    done = subprocess.run([pdftotext, "-bbox", str(pdf), "-"], capture_output=True, text=True, timeout=TIMEOUT)
    if done.returncode != 0:
        raise RuntimeError(f"pdftotext が {done.returncode} で終わった: {done.stderr.strip()[:200]}")
    found = []
    for number, (width, height, body) in enumerate(PAGE.findall(done.stdout), 1):
        width, height = float(width), float(height)
        words = [(float(a), float(b), float(c), float(d), t) for a, b, c, d, t in WORD.findall(body)]
        for x0, y0, x1, y1, text in words:
            if ELLIPSIS in text:
                found.append(f"{name} {number} ページ: 見切れ（描画した文字に省略記号）: {text}")
            if x0 < -TOLERANCE or y0 < -TOLERANCE or x1 > width + TOLERANCE or y1 > height + TOLERANCE:
                found.append(f"{name} {number} ページ: はみ出し（ページの外）: {text}")
        order = sorted(words, key=lambda w: w[1])
        for i, (ax0, ay0, ax1, ay1, at) in enumerate(order):
            for bx0, by0, bx1, by1, bt in order[i + 1:]:
                if by0 >= ay1:
                    break
                w, h = min(ax1, bx1) - max(ax0, bx0), min(ay1, by1) - max(ay0, by0)
                if w > 0 and h > 0 and w * h > OVERLAP * min((ax1 - ax0) * (ay1 - ay0), (bx1 - bx0) * (by1 - by0)):
                    found.append(f"{name} {number} ページ: はみ出し（文字の重なり）: {at} と {bt}")
        for bx, by, bw, bh in boxes.get(number, []):
            bottom = by + bh
            for x0, y0, x1, y1, text in words:
                if bx - TOLERANCE <= x0 <= bx + bw and y0 < bottom - TOLERANCE and y1 > bottom + TOLERANCE and by <= y0:
                    found.append(f"{name} {number} ページ: はみ出し（枠の下の辺をまたぐ）: {text}")
    return sorted(set(found))


def render(pptx: Path, out: Path, soffice: str, pdftoppm: str, dpi: int) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        done = subprocess.run([soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", "pdf", "--outdir", str(out), str(pptx)],
                              capture_output=True, text=True, timeout=TIMEOUT)
    pdf = out / f"{pptx.stem}.pdf"
    if done.returncode != 0 or not pdf.is_file():
        raise RuntimeError(f"描画に失敗した（soffice の終了コード {done.returncode}）: {(done.stderr or done.stdout).strip()[:200]}")
    for old in out.glob(f"{pptx.stem}-*.png"):
        old.unlink()
    done = subprocess.run([pdftoppm, "-r", str(dpi), "-png", str(pdf), str(out / pptx.stem)], capture_output=True, text=True, timeout=TIMEOUT)
    if done.returncode != 0:
        raise RuntimeError(f"PNG に書き出せなかった（pdftoppm の終了コード {done.returncode}）: {done.stderr.strip()[:200]}")
    return pdf


def main(argv: list[str]) -> int:
    files, out, dpi, it = [], None, 80, iter(argv)
    for a in it:
        if a == "--out":
            out = next(it, None)
            if out is None:
                print(__doc__.splitlines()[2], file=sys.stderr)
                return 2
        elif a == "--dpi":
            value = next(it, "")
            if not value.isdigit() or not 20 <= int(value) <= 300:
                print("--dpi は 20〜300 の整数", file=sys.stderr)
                return 2
            dpi = int(value)
        elif a.startswith("--"):
            print(__doc__.splitlines()[2], file=sys.stderr)
            return 2
        else:
            files.append(Path(a))
    if not files:
        print(__doc__.splitlines()[2], file=sys.stderr)
        return 2
    findings: list[str] = []
    for pptx in files:
        try:
            findings += text_findings(pptx)
        except (OSError, zipfile.BadZipFile, ElementTree.ParseError) as e:
            print(f"{pptx}: PPTX として読めない（{type(e).__name__}）。確かめていない", file=sys.stderr)
            return 2
    found_tools, missing = tools()
    if missing:
        for line in findings:
            print(line)
        print(f"描画の道具が無い（{'・'.join(missing)}）——確かめられていない。PPTX の本文だけを見た（見つかったもの {len(findings)} 件）。"
              "報告に「描画して確かめていない」と書く（緑にしない）", file=sys.stderr)
        return 3
    for pptx in files:
        target = Path(out) if out is not None else pptx.parent / f"{pptx.stem}-pages"
        try:
            pdf = render(pptx, target, found_tools["soffice"], found_tools["pdftoppm"], dpi)
            findings += render_findings(pptx.name, pdf, found_tools["pdftotext"], text_boxes(pptx))
        except (OSError, subprocess.SubprocessError, RuntimeError, zipfile.BadZipFile, ElementTree.ParseError) as e:
            print(f"{pptx}: 描画して確かめられなかった（{e}）", file=sys.stderr)
            return 2
        print(f"{pptx.name}: {len(list(target.glob(pptx.stem + '-*.png')))} ページの PNG を {target} に書いた（目で見る）")
    for line in sorted(set(findings)):
        print(line)
    if findings:
        print(f"{len(set(findings))} 件見つかった。元（手書き部分・見積り・スケジュール）か見せ方を直して作り直す（生成した PPTX を手で直さない）", file=sys.stderr)
        return 1
    print("見つからなかった（探せるのは見切れ・図の代わりの文字・はみ出しだけ。見た目は PNG を目で見る）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # 想定外の例外も「確かめていない」（2）。違反の 1 に化けさせない
        print(f"{Path(__file__).name}: 想定外の例外で止まった（{type(e).__name__}: {e}）。確かめていない", file=sys.stderr)
        sys.exit(2)
