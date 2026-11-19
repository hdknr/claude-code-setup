#!/usr/bin/env python3
"""`plugins/spec-loop/scripts/check-pptx-render.py`（PPTX を描画して探す・PNG を書く。#1289）の回帰テスト（変異テストを含む）。

描画の道具（LibreOffice の `soffice`・poppler の `pdftotext`・`pdftoppm`）は CI に無いので、**偽の道具を `PATH` の先頭に置く**
（`PATH` の残りは `/usr/bin:/bin` だけ——本物の道具には届かない）。偽の `pdftotext` は、用意した語の枠（`-bbox` の XHTML）をそのまま返す。
PPTX の試料は `proposal-pptx.py` の部品で一時ディレクトリに作る。

見るもの:

1. **見つからない**: ページの中に収まった語だけ・隣り合うだけの語・ページの辺の許容の内側の語では 0 で、1 ページずつの PNG を書く（陽性対照）。
2. **見切れ**: PPTX の文字の省略記号・描画した文字の省略記号は 1。
3. **図の中の代わりの文字**（`Text is not SVG`）は 1。
4. **はみ出し**: ページの外の語・重なる語・文字を持つ枠の下の辺をまたぐ語は 1。
5. **確かめられない**: 描画の道具が無ければ 3（PPTX の本文だけ見た結果は出し、終わりは 3 のまま。緑にしない）。描画に失敗・PPTX が読めない・引数の誤りは 2。
6. **PPTX に書き込まない**（実行の前後でバイトが同じ）。
7. （手元に道具があれば）**実機**: 本物の LibreOffice で、収まる枚は 0・はみ出す枚は 1。無ければ「走らせていない」と言う。

**守らないもの**: 偽の道具の出力が本物の poppler・LibreOffice と同じ形であること（本物の `pdftotext -bbox` の形に合わせてあるが、版による違いは見ない。実機の確認が別にある）。
**変異テストを含む。** 本体を 1 箇所ずつ壊し、名指しした試料が期待どおりでなくなることを確かめる。
**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "check-pptx-render.py"

FAKE_SOFFICE = """#!/usr/bin/env python3
import os, sys, pathlib
if os.environ.get("FAKE_SOFFICE_FAIL"):
    print("soffice が壊れている", file=sys.stderr); sys.exit(3)
if os.environ.get("FAKE_SOFFICE_NOWRITE"):
    sys.exit(0)  # 0 で終わるが PDF を書かない
args = sys.argv[1:]
out = pathlib.Path(args[args.index("--outdir") + 1]); src = pathlib.Path(args[-1])
(out / (src.stem + ".pdf")).write_bytes(b"%PDF-fake")
"""
FAKE_PDFTOTEXT = """#!/usr/bin/env python3
import os, sys, pathlib
sys.stdout.write(pathlib.Path(os.environ["FAKE_BBOX"]).read_text(encoding="utf-8"))
"""
FAKE_PDFTOPPM = """#!/usr/bin/env python3
import sys, pathlib
args = sys.argv[1:]
prefix = args[-1]
for n in (1, 2):
    pathlib.Path(f"{prefix}-{n}.png").write_bytes(b"\\x89PNG fake")
"""


def page(*words: tuple[float, float, float, float, str], width: float = 960.0, height: float = 540.0) -> str:
    body = "".join(f'<word xMin="{a}" yMin="{b}" xMax="{c}" yMax="{d}">{t}</word>' for a, b, c, d, t in words)
    return f'<?xml version="1.0"?><doc><page width="{width}" height="{height}">{body}</page></doc>'


def load_pptx_module():
    spec = importlib.util.spec_from_file_location("proposal_pptx_for_render_test", SCRIPTS / "proposal-pptx.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_pptx(pp, path: Path, text: str, box: tuple[int, int, int, int] = (1000000, 1000000, 3000000, 1000000)) -> Path:
    deck = pp.Deck("t")
    slide = pp.Slide()
    slide.title("題")
    slide.box(*box, [pp.para(text, 14)])
    deck.add(slide)
    pp.pptx.write(deck.parts(), path)
    return path


def run(script: Path, args: list[str], bin_dir: Path, bbox: str | None, work: Path, env_extra: dict[str, str] | None = None):
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(work / "home"), "LANG": "C.UTF-8"}
    if bbox is not None:
        (work / "bbox.xml").write_text(bbox, encoding="utf-8")
        env["FAKE_BBOX"] = str(work / "bbox.xml")
    env.update(env_extra or {})
    proc = subprocess.run([sys.executable, "-I", str(script), *args], capture_output=True, text=True, env=env, cwd=work)
    return proc.returncode, proc.stdout + proc.stderr


def with_parts(src: Path, dst: Path, edits: dict[str, tuple[str, str]]) -> Path:
    """PPTX の部品を書き換えた写しを作る。edits: 部品名 → (置き換える文字列, 置き換え後)。"""
    import zipfile
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in edits:
                old, new = edits[item.filename]
                text = data.decode("utf-8")
                assert old in text, item.filename
                data = text.replace(old, new, 1).encode("utf-8")
            zout.writestr(item, data)
    return dst


def shape(x: int, y: int, cx: int, cy: int, text: str | None, positioned: bool = True) -> str:
    xfrm = f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>' if positioned else ""
    body = f"<a:r><a:t>{text}</a:t></a:r>" if text else ""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="90" name="S"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>{xfrm}</p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p>{body}</a:p></p:txBody></p:sp>')


def cases(script: Path, work: Path, pp, bin_dir: Path, bare_dir: Path) -> dict[str, bool]:
    """観測。(名前 → 期待どおりか)。"""
    (work / "home").mkdir(exist_ok=True)
    good = make_pptx(pp, work / "good.pptx", "収まった文")
    ellipsis = make_pptx(pp, work / "ellipsis.pptx", "切れた文…")
    alt = make_pptx(pp, work / "alt.pptx", "Text is not SVG - cannot display")
    out = work / "pages"
    inside = page((40, 25, 90, 40, "あ"), (90, 25, 140, 40, "い"), (100, 100, 160, 114, "う"))
    obs: dict[str, bool] = {}

    before = good.read_bytes()
    rc, text = run(script, [str(good), "--out", str(out)], bin_dir, inside, work)
    obs["収まっていれば 0"] = rc == 0 and "見つからなかった" in text
    obs["1 ページずつの PNG を書く"] = sorted(p.name for p in out.glob("good-*.png")) == ["good-1.png", "good-2.png"]
    obs["PNG の場所を言う"] = "good.pptx: 2 ページの PNG" in text and str(out) in text
    obs["PPTX に書き込まない"] = good.read_bytes() == before

    rc, text = run(script, [str(ellipsis), "--out", str(work / "p2")], bin_dir, inside, work)
    obs["PPTX の本文の省略記号は 1"] = rc == 1 and "見切れ（省略記号）" in text and "1 ページ" in text
    rc, text = run(script, [str(alt), "--out", str(work / "p3")], bin_dir, inside, work)
    obs["図の代わりの文字は 1"] = rc == 1 and "Text is not SVG" in text and "図の代わりの文字" in text
    rc, text = run(script, [str(good), "--out", str(work / "p4")], bin_dir, page((10, 10, 60, 24, "切れ…")), work)
    obs["描画した文字の省略記号は 1"] = rc == 1 and "描画した文字に省略記号" in text
    rc, text = run(script, [str(good), "--out", str(work / "p5")], bin_dir, page((900, 10, 1000, 24, "外へ")), work)
    obs["ページの外は 1"] = rc == 1 and "ページの外" in text and "外へ" in text
    rc, text = run(script, [str(good), "--out", str(work / "p6")], bin_dir, page((10, 10, 60, 24, "上"), (20, 12, 70, 26, "下")), work)
    obs["重なる文字は 1"] = rc == 1 and "文字の重なり" in text
    # 枠 (1000000, 1000000, 3000000, 1000000) EMU = x 78.7pt・y 78.7pt・幅 236.2pt・高さ 78.7pt → 下の辺は 157.5pt
    rc, text = run(script, [str(good), "--out", str(work / "p7")], bin_dir, page((100, 150, 150, 165, "またぐ")), work)
    obs["枠の下の辺をまたぐ語は 1"] = rc == 1 and "枠の下の辺をまたぐ" in text and "またぐ" in text
    # 枠の下 100pt に、枠をまたがず他の文字にも重ならない行が丸ごと出ている（反証: またぐ語・重なりでは見えない形）
    rc, text = run(script, [str(good), "--out", str(work / "p7b")], bin_dir, page((100, 260, 150, 274, "枠の外"), (160, 260, 210, 274, "の行")), work)
    obs["どの枠にも無い文字は 1"] = rc == 1 and "どの枠の中にも無い" in text and "枠の外" in text
    rc, text = run(script, [str(good), "--out", str(work / "p7c")], bin_dir, page((-8, 10, 20, 24, "左へ")), work)
    obs["左へはみ出した語は 1"] = rc == 1 and "ページの外" in text and "左へ" in text
    rc, text = run(script, [str(good), "--out", str(work / "p8")], bin_dir, page((100, 120, 150, 134, "中")), work)
    obs["枠の中の語は 0"] = rc == 0
    rc, text = run(script, [str(good), "--out", str(work / "p9")], bin_dir, page((100, 143, 150, 157.5 + 1.0, "辺の近く")), work)
    obs["枠の辺の許容の内側は 0"] = rc == 0
    rc, text = run(script, [str(good), "--out", str(work / "p10")], bin_dir, page((10, 30, 960 + 1.0, 44, "辺")), work)
    obs["ページの辺の許容の内側は 0"] = rc == 0
    rc, text = run(script, [str(good), "--out", str(work / "p11")], bin_dir, page((40, 30, 90, 44, "同じ行"), (90, 30, 140, 44, "の隣")), work)
    obs["隣り合うだけの語は 0"] = rc == 0

    # レイアウトの図形（社のテンプレートのフッター）の枠は、どのスライドにも出る。文字の無い図形はページ全体を覆っても枠にしない
    layout = "ppt/slideLayouts/slideLayout1.xml"
    footer = with_parts(good, work / "footer.pptx", {layout: ("</p:spTree>", shape(1000000, 5000000, 3000000, 300000, "社外秘") + "</p:spTree>")})
    rc, text = run(script, [str(footer), "--out", str(work / "p16")], bin_dir, page((100, 395, 150, 408, "社外秘")), work)
    obs["レイアウトのフッターの中の語は 0"] = rc == 0
    rc, text = run(script, [str(footer), "--out", str(work / "p16b")], bin_dir, page((100, 260, 150, 274, "枠の外")), work)
    obs["レイアウトのフッターがあっても、枠の外の語は 1"] = rc == 1 and "どの枠の中にも無い" in text
    empty_ph = with_parts(good, work / "empty-ph.pptx", {layout: ("</p:spTree>", shape(0, 0, 12192000, 6858000, None) + "</p:spTree>")})
    rc, text = run(script, [str(empty_ph), "--out", str(work / "p16c")], bin_dir, page((100, 260, 150, 274, "枠の外")), work)
    obs["空のプレースホルダがページ全体を覆っても、枠の外の語は 1"] = rc == 1 and "どの枠の中にも無い" in text
    inherited = with_parts(good, work / "inherited.pptx", {"ppt/slides/slide1.xml": ("</p:spTree>", shape(0, 0, 0, 0, "継ぐ", positioned=False) + "</p:spTree>")})
    rc, text = run(script, [str(inherited), "--out", str(work / "p16d")], bin_dir, page((100, 260, 150, 274, "どこか")), work)
    obs["位置をレイアウトから継ぐ文字があるスライドは、枠の判定をしない（0）"] = rc == 0
    rc, text = run(script, [str(inherited), "--out", str(work / "p16e")], bin_dir, page((900, 10, 1000, 24, "外へ")), work)
    obs["枠の判定をしなくても、ページの外は 1"] = rc == 1 and "ページの外" in text

    rc, text = run(script, [str(ellipsis), "--out", str(work / "p12")], bare_dir, None, work)
    obs["道具が無ければ 3"] = rc == 3 and "描画の道具が無い（soffice）" in text and "確かめられていない" in text
    obs["道具が無くても PPTX の本文は見る"] = "見切れ（省略記号）" in text
    rc, text = run(script, [str(good), "--out", str(work / "p13")], bare_dir, None, work)
    obs["道具が無ければ緑にしない"] = rc == 3 and "描画して確かめていない" in text
    rc, text = run(script, [str(good), "--out", str(work / "p14")], bin_dir, inside, work, {"FAKE_SOFFICE_FAIL": "1"})
    obs["描画に失敗したら 2"] = rc == 2 and "描画して確かめられなかった" in text
    stale_out = work / "p14b"
    run(script, [str(good), "--out", str(stale_out)], bin_dir, inside, work)  # 前の PDF が残る
    rc, text = run(script, [str(good), "--out", str(stale_out)], bin_dir, inside, work, {"FAKE_SOFFICE_NOWRITE": "1"})
    obs["PDF を書かずに 0 で終わっても、前の PDF を検査しない"] = rc == 2 and "描画して確かめられなかった" in text
    broken = work / "broken.pptx"
    broken.write_bytes(b"not a zip")
    rc, text = run(script, [str(broken), "--out", str(work / "p15")], bin_dir, inside, work)
    obs["PPTX として読めなければ 2"] = rc == 2 and "PPTX として読めない" in text
    rc, text = run(script, [], bin_dir, inside, work)
    obs["引数が無ければ 2"] = rc == 2
    rc, text = run(script, [str(good), "--dpi", "5"], bin_dir, inside, work)
    obs["解像度の範囲の外は 2"] = rc == 2 and "--dpi" in text
    rc, text = run(script, [str(good), "--nothing"], bin_dir, inside, work)
    obs["知らない引数は 2"] = rc == 2
    return obs


def real_tools_check(pp, work: Path) -> tuple[bool | None, str]:
    """本物の道具があれば実機で確かめる。道具が無ければ (None, 理由)。"""
    missing = [n for n in ("soffice", "pdftotext", "pdftoppm") if shutil.which(n) is None]
    if missing:
        return None, f"走らせていない（{'・'.join(missing)} が無い）"
    script = SCRIPTS / TARGET
    clean = make_pptx(pp, work / "real-clean.pptx", "収まる文")
    # 枠の右半分がページの外に出る——外に出た文字は、枠の高さや行の割れ方に依らず必ず見つかる
    bad = make_pptx(pp, work / "real-bad.pptx", "はみ出す文" * 6, box=(pp.W - 1500000, 1000000, 3000000, 700000))
    env = {"PATH": os.environ["PATH"], "HOME": str(work / "home"), "LANG": "C.UTF-8"}
    results = []
    for pptx in (clean, bad):
        proc = subprocess.run([sys.executable, "-I", str(script), str(pptx), "--out", str(work / f"real-{pptx.stem}")],
                              capture_output=True, text=True, env=env, cwd=work, timeout=300)
        results.append(proc.returncode)
    return results == [0, 1], f"収まる枚 {results[0]}・はみ出す枚 {results[1]}（期待は 0 と 1）"


MUTATIONS: list[tuple[str, str, str, str]] = [
    ("描画した文字の省略記号を見ない", "            if ELLIPSIS in text:\n", "            if False:\n", "描画した文字の省略記号は 1"),
    ("図の代わりの文字を見ない", "        if ALT in text:\n", "        if False:\n", "図の代わりの文字は 1"),
    ("ページの外を見ない", "            if x0 < -TOLERANCE or y0 < -TOLERANCE or x1 > width + TOLERANCE or y1 > height + TOLERANCE:\n",
     "            if False:\n", "ページの外は 1"),
    ("文字の重なりを見ない", "                if w > 0 and h > 0 and w * h > OVERLAP", "                if False and w * h > OVERLAP", "重なる文字は 1"),
    ("枠の下の辺をまたぐ語を見ない", "                if bx - TOLERANCE <= x0 <= bx + bw and y0 < bottom - TOLERANCE and y1 > bottom + TOLERANCE and by <= y0:\n",
     "                if False:\n", "枠の下の辺をまたぐ語は 1"),
    ("どの枠にも無い文字を見ない", "        if regions:  # どの枠", "        if False:  # どの枠", "どの枠にも無い文字は 1"),
    ("負の座標を読まない", 'xMin="(-?[\\d.]+)" yMin="(-?[\\d.]+)"', 'xMin="([\\d.]+)" yMin="([\\d.]+)"', "左へはみ出した語は 1"),
    ("前の PDF を消さない", '    (out / f"{pptx.stem}.pdf").unlink(missing_ok=True)', "    pass", "PDF を書かずに 0 で終わっても、前の PDF を検査しない"),
    ("枠の辺の許容を外す", "and y1 > bottom + TOLERANCE and by <= y0", "and y1 > bottom and by <= y0", "枠の辺の許容の内側は 0"),
    ("ページの辺の許容を外す", "or x1 > width + TOLERANCE or", "or x1 > width or", "ページの辺の許容の内側は 0"),
    ("道具が無くても緑にする", "        return 3\n", "        return 0\n", "道具が無ければ 3"),
    ("描画の失敗を緑にする", "            print(f\"{pptx}: 描画して確かめられなかった（{e}）\", file=sys.stderr)\n            return 2\n",
     "            print(f\"{pptx}: 描画して確かめられなかった（{e}）\", file=sys.stderr)\n            return 0\n", "描画に失敗したら 2"),
    ("見つけても 0 にする", "    if findings:\n        print(f\"{len(set(findings))} 件見つかった", "    if False:\n        print(f\"{len(set(findings))} 件見つかった",
     "ページの外は 1"),
    ("解像度の範囲を見ない", "            if not value.isdigit() or not 20 <= int(value) <= 300:\n", "            if False:\n", "解像度の範囲の外は 2"),
    ("PNG を書かない", "    done = subprocess.run([pdftoppm,", "    return pdf\n    done = subprocess.run([pdftoppm,", "1 ページずつの PNG を書く"),
    ("PPTX の本文の省略記号を見ない", "        for m in re.finditer(re.escape(ELLIPSIS), text):", "        for m in []:", "PPTX の本文の省略記号は 1"),
    ("道具が無いときに本文を見ない", "    found_tools, missing = tools()\n    if missing:\n        for line in findings:\n            print(line)\n",
     "    found_tools, missing = tools()\n    if missing:\n", "道具が無くても PPTX の本文は見る"),
    ("テンプレートの枠を足さない", "                boxes.extend(template)\n", "                pass\n", "レイアウトのフッターの中の語は 0"),
    ("空の図形も枠にする", "                        continue  # 文字の無い図形", "                        pass  # 文字の無い図形", "空のプレースホルダがページ全体を覆っても、枠の外の語は 1"),
    ("位置を継ぐ文字を見ない", "None if inherited else boxes", "boxes", "位置をレイアウトから継ぐ文字があるスライドは、枠の判定をしない（0）"),
]


def main() -> int:
    failures: list[str] = []

    def check(label: str, ok: bool) -> None:
        print(f"{'OK  ' if ok else 'NG  '}{label}")
        if not ok:
            failures.append(label)

    pp = load_pptx_module()
    with tempfile.TemporaryDirectory(prefix="check-pptx-render-test-") as tmp:
        base = Path(tmp)
        for name, body in (("soffice", FAKE_SOFFICE), ("pdftotext", FAKE_PDFTOTEXT), ("pdftoppm", FAKE_PDFTOPPM)):
            for d in (base / "bin", base / "bare"):
                d.mkdir(exist_ok=True)
                if d.name == "bare" and name == "soffice":
                    continue  # 道具が無い（soffice だけ無い）
                (d / name).write_text(body, encoding="utf-8")
                (d / name).chmod(0o755)
        script = SCRIPTS / TARGET
        work = base / "real"
        work.mkdir()
        real = cases(script, work, pp, base / "bin", base / "bare")
        bad = [k for k, v in real.items() if not v]
        check(f"本物の本体は全部の観測が期待どおり（{len(real)} 件。{'; '.join(bad) or '問題なし'}）", not bad)

        print("\nリポジトリの外で単体で動く")
        alone = base / "alone"
        alone.mkdir()
        shutil.copy(script, alone / TARGET)
        awork = base / "alone-work"
        awork.mkdir()
        rc_obs = cases(alone / TARGET, awork, pp, base / "bin", base / "bare")
        check("写しだけの場所でも全部の観測が期待どおり", all(rc_obs.values()))

        print("\n変異（1 箇所ずつ壊して、名指しした観測が期待と違うこと）")
        source = script.read_text(encoding="utf-8")
        for n, (name, needle, replacement, victim) in enumerate(MUTATIONS):
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}（{source.count(needle)} 箇所）", False)
                continue
            d = base / f"mut-{n}"
            d.mkdir()
            (d / TARGET).write_text(source.replace(needle, replacement, 1), encoding="utf-8")
            w = base / f"mut-work-{n}"
            w.mkdir()
            try:
                observed = cases(d / TARGET, w, pp, base / "bin", base / "bare")
            except Exception as e:  # noqa: BLE001
                observed = {victim: False, "例外": type(e).__name__}
            check(f"変異を殺せる: {name}（殺すはずの観測: {victim}）", victim in observed and not observed[victim])

        print("\n実機（道具があれば）")
        ok, detail = real_tools_check(pp, base / "alone-work")
        if ok is None:
            print(f"  実機の確認は{detail}。手元で回す")
        else:
            check(f"本物の LibreOffice・poppler で、収まる枚は 0・はみ出す枚は 1（{detail}）", bool(ok))
    if failures:
        print(f"\n{len(failures)} 件の失敗:\n" + "\n".join(f"  - {f}" for f in failures))
        return 1
    print(f"\nOK: 観測 {len(real)} 件・変異 {len(MUTATIONS)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
