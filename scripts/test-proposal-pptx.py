#!/usr/bin/env python3
"""`plugins/spec-loop/scripts/proposal-pptx.py`（提案書・仕様書の PPTX の既定のデザイン。#1289）の回帰テスト（変異テストを含む）。

試料は**一時ディレクトリの中の合成の材料**（手書き部分・Q&A の行・見積り・スケジュール・図）で、実案件の正本は読まない。
**描画はしない**（LibreOffice が CI に無い）——描画して確かめるのは `check-pptx-render.py` で、その実機の結果は PR に貼る。
ここで見るのは、描画の前に決まる**構造**:

1. **参照の括弧を外す**（Q&A の番号・パスだけの括弧。中身が参照だけでない括弧は残す）。
2. **費用**は開発費と運用費が別のページで、行が増えたら枚数で受け、どの行も 1 度ずつ載り、番号だけの根拠は出さず、長すぎる根拠は出さず、合計が載る。
3. **期間**は 1 枚の図形（工程の表の枚は無い）で、工程名がすべて載り、節目は ◆、休みの網掛けがあり、月の見出しは幅に収まる水準で書く。
4. **カード**は、枚数に合わせて並べ、同じ枚は同じ文字の大きさで、収まらないカードは割って**どの箇条も落とさない**。
5. **別紙の表（xlsx）**に Q&A の全件があり、同じ材料から同じバイトになる。
6. **図**は PNG にして載せ（偽の `rsvg-convert` を `SPEC_LOOP_RSVG` で差す）、drawio の代わりの文字は変換の入力から消え、正本の SVG は変わらない。
   道具が無ければ図を載せずに名指しする。見出しは図の中の名前か読める名前。
7. **PNG の部品**（`ppt/media/`・コンテンツタイプ・スライドの関係）が揃い、XML がすべて整形式。
8. **仕様書**: 値の無い規模の行を出さず、範囲の外は理由だけ。

**守らないもの**: PowerPoint・LibreOffice で開けること・見た目・文字の寸法の見積りが実際の描画と合うこと（見積りは余裕を持たせてあるだけ）。
**変異テストを含む。** 本体を 1 箇所ずつ壊し、**壊したのに全部の観測が期待どおりなら失格**とする。変異ごとに、壊す箇所が本体にちょうど 1 回現れることを先に確かめる。
**このテストは実環境を触らない。** 試料はすべて一時ディレクトリに書く。
"""
from __future__ import annotations

import importlib.util
import io
import os
import re
import shutil
import struct
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

REAL_REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REAL_REPO / "plugins" / "spec-loop" / "scripts"
TARGET = "proposal-pptx.py"
NEEDED = [TARGET, "qa-to-pptx.py", "check-qa-csv.py"]
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

PNG_HEAD = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 400, 200) + b"\x08\x06\x00\x00\x00"
FAKE_RSVG = (f"#!/usr/bin/env python3\nimport sys, pathlib\ndata = sys.stdin.buffer.read()\n"
             "pathlib.Path(sys.argv[0] + '.in').write_bytes(data)\n"
             f"sys.stdout.buffer.write({PNG_HEAD!r} + b'x' * 20)\n")
DRAWIO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"><g data-cell-id="title"><switch><foreignObject>'
              '<div xmlns="http://www.w3.org/1999/xhtml"><div>注文の流れ</div></div></foreignObject><text>注文の流れ</text></switch></g>'
              '<switch><g/><a transform="translate(0,-5)" xlink:href="https://www.drawio.com/doc/faq/svg-export-text-problems" target="_blank">'
              '<text text-anchor="middle" font-size="10px" x="50%" y="100%">Text is not SVG - cannot display</text></a></switch></svg>')

HAND = [("01-background.md", """## 背景と目的

**転記に月 40 時間かかっている**

- 受注票を 3 つのシステムに手で転記している（Q-R-001）。
- 誤りが月に 5 件ほど出る。

**年内に動かしたい**

- 年末商戦の前に稼働させる（`docs/v1/requirements/purposes.csv`）。

**暫定の回答を引く**

- Q-R-002（暫定の回答。利用者に未確認）を前提にする。

## リスク

**繁忙期に間に合わない**

- 工程が 1 週間遅れると稼働が年明けになる。
""")]


def load(source: str | None = None, directory: Path | None = None):
    """`proposal-pptx.py` を読み込む。`source` を渡すと壊した本体を `directory` に置いて読む。"""
    if directory is None:
        path = SCRIPTS / TARGET
    else:
        for name in NEEDED:
            shutil.copy(SCRIPTS / name, directory / name)
        (directory / TARGET).write_text(source, encoding="utf-8")
        path = directory / TARGET
    spec = importlib.util.spec_from_file_location("proposal_pptx_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def texts(parts) -> list[str]:
    """スライドごとの文字（スライドの番号の順）。"""
    named = {n: b for n, b in parts if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)}
    out = []
    for name in sorted(named, key=lambda n: int(re.sub(r"\D", "", n))):
        root = ET.fromstring(named[name])
        out.append("".join(t.text or "" for t in root.iter(f"{A}t")))
    return out


def slide_xmls(parts) -> list[str]:
    named = {n: b for n, b in parts if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)}
    return [named[n] for n in sorted(named, key=lambda n: int(re.sub(r"\D", "", n)))]


def slide_list_texts_parts(parts) -> list[str]:
    return texts(parts)


def slide_list_texts(slides) -> list[str]:
    return ["".join(t.text or "" for t in ET.fromstring(s.render()).iter(f"{A}t")) for s in slides]


def qa_row(mod, n: int, state: str = "反映済み", rec: str = "A", ans: str = "A（業務部が回答）", target: str = "決定表 4 行目",
           question: str | None = None, source: str = "要求確定") -> dict:
    return {"No": f"Q-R-{n:03d}", "起票元": source, "質問": question or f"質問 {n}", "選択肢": "A: する / B: しない", "推奨": rec,
            "推奨の理由": "理由", "回答": ans, "反映先": target, "状態": state, "費用への影響": ""}


def estimate_rows(n_dev: int = 22) -> list[dict]:
    rows = []
    for i in range(1, n_dev + 1):
        basis = ["画面一覧の 12 画面 × 40 万円", "Q-F-001 の回答 B", "決定表 24 行 × 1.5 人日 × 8 万円 + 結合の試験を 3 人日 × 8 万円 + 余裕を 10%（Q-F-004 と D-F-003 の回答）",
                 "あ" * 150][i % 4]
        rows.append({"No": f"E-{i:03d}", "区分": "開発費", "項目": f"開発の項目{i:02d}", "金額": str(100000 * i), "根拠": basis})
    for i in range(1, 4):
        rows.append({"No": f"E-{50 + i}", "区分": "運用費（月額）", "項目": f"運用の項目{i:02d}", "金額": str(30000 * i), "根拠": "Q-F-001 の回答 B"})
    return rows


def schedule_rows(n: int = 14, start: str = "2026-11-02") -> list[dict]:
    from datetime import date, timedelta
    rows, d = [], date.fromisoformat(start)
    for i in range(1, n + 1):
        days = 1 if i in (3, 9) else 20
        rows.append({"No": f"T-{i:03d}", "工程": f"工程{i:02d}", "開始": d.isoformat(), "終了": (d + timedelta(days=days - 1)).isoformat(), "前提": ""})
        d += timedelta(days=days)
    return rows


def pp_title(text: str) -> str:
    slide = LOADED[0].Slide()
    slide.title(text)
    return slide.render()


LOADED: list = []


def observe(mod, tool_dir: Path) -> dict:
    """本体の観測。例外は観測の値にする（壊した本体が落ちたことも「期待と違う」と数える）。"""
    obs: dict = {}

    def seen(key: str, fn) -> None:
        try:
            obs[key] = fn()
        except Exception as e:  # noqa: BLE001
            obs[key] = f"例外 {type(e).__name__}"

    pp = mod
    LOADED[:] = [mod]
    # 1. 参照の括弧
    seen("参照の括弧を外す", lambda: pp.strip_refs("画面は 4 枚（Q-R-001）。") == "画面は 4 枚。")
    seen("暫定の断り書きは残す", lambda: pp.strip_refs("Q-R-002（暫定の回答。利用者に未確認）") == "（暫定の回答。利用者に未確認）")
    seen("パスの括弧を外す", lambda: "docs/v1" not in pp.strip_refs("全文は（`docs/v1/a.md`）にある"))
    seen("参照でない括弧は残す", lambda: pp.strip_refs("業務部（受注担当）が決める") == "業務部（受注担当）が決める")
    seen("追加の形を外す", lambda: pp.strip_refs("案 X-9", [re.compile(r"X-\d")]) == "案")
    # 2. 根拠
    seen("番号だけの根拠は出さない", lambda: pp.basis_text("Q-F-001 の回答 B", 300, 11) == ("", "none"))
    seen("計算式は出す", lambda: pp.basis_text("画面一覧の 12 画面 × 40 万円", 300, 11) == ("画面一覧の 12 画面 × 40 万円", "formula"))
    seen("式の後ろの番号の括弧は外す", lambda: pp.basis_text("12 画面 × 40 万円（Q-F-004 と D-F-003 の回答）", 300, 11) == ("12 画面 × 40 万円", "formula"))
    seen("長すぎる根拠は出さない", lambda: pp.basis_text("あ" * 200, 200, 11) == ("", "long"))
    # 3. 費用
    cost = pp.cost_slides(estimate_rows(), ["開発費", "運用費（月額）"], "proposal.md")
    ct = slide_list_texts(cost)
    v2 = slide_list_texts(pp.cost_slides(estimate_rows(), ["開発費", "運用費（月額）"], "proposal.md", "この版（v2）の差分の見積り。前の版までの費用は含まない。"))
    ctx2 = {"title": "提案書", "version": 2, "hand": [], "qa": [], "estimate": estimate_rows(2), "schedule": schedule_rows(3), "purposes": None, "purpose_kinds": [],
            "provisional_lead": "この版の Q&A で", "changes": {"title": "前の版（v1）からの変更", "summary": (["種類", "追加"], [["Q&A", "1"]]), "details": []}}
    p2 = slide_list_texts_parts(pp.proposal_deck(ctx2, ["開発費", "運用費（月額）"], pp.Options(), "proposal.md")[0])
    seen("v2 以降の提案書の費用の枚は差分と書く", lambda: any(t.startswith("開発費") and "この版（v2）の差分の見積り" in t for t in p2))
    seen("v2 以降の費用は差分と書く", lambda: all("この版（v2）の差分の見積り" in t for t in v2) and not any("差分" in t for t in ct))
    seen("開発費は枚数で受ける", lambda: sum("開発費の合計" in t for t in ct) >= 2 and sum("運用費（月額）の合計" in t for t in ct) == 1)
    seen("費用の行は 1 度ずつ載る", lambda: all(sum(f"開発の項目{i:02d}" in t for t in ct) == 1 for i in range(1, 23))
         and all(sum(f"運用の項目{i:02d}" in t for t in ct) == 1 for i in range(1, 4)))
    seen("費用に省略記号が無い", lambda: not any("…" in t for t in ct))
    seen("費用の合計が載る", lambda: any("25,300,000" in t for t in ct) and any("180,000" in t for t in ct))
    seen("番号だけの根拠は費用の枚に出ない", lambda: not any("Q-F-001" in t or "D-F-003" in t for t in ct))
    seen("長い根拠は全文を指す", lambda: any("根拠は proposal.md を見る" in t for t in ct) and not any("あ" * 20 in t for t in ct))
    seen("合計の行が最後の枚に載る（注記と表の行の 2 か所）", lambda: [t for t in ct if t.startswith("開発費")][-1].count("25,300,000") == 2
         and [t for t in ct if t.startswith("開発費")][0].count("25,300,000") == 1)
    # 3. 期間
    sched = schedule_rows()
    g = pp.gantt_slides(sched)
    gt = slide_list_texts(g)
    gx = [s.render() for s in g]
    seen("期間は 1 枚", lambda: len(g) == 1)
    seen("工程名がすべて載る", lambda: all(r["工程"] in gt[0] for r in sched))
    seen("節目は ◆", lambda: gx[0].count('prst="diamond"') == 2)
    def weekend(start: str, end: str):
        """(休みの網掛けの (x, 幅) の並び, 月の境目の x, チャートの右端)。月の境目の x が最初の日の位置。"""
        xml = pp.gantt_slides([{"No": "T-001", "工程": "a", "開始": start, "終了": end, "前提": ""}])[0].render()
        rects = [(int(a), int(b)) for a, b in re.findall(r'<p:cNvPr id="\d+" name="Weekend \d+"/>.*?<a:off x="(\d+)" y="\d+"/><a:ext cx="(\d+)"', xml)]
        line = int(re.search(r'name="MonthLine \d+"/>.*?<a:off x="(\d+)"', xml)[1])
        return rects, line, pp.W - pp.MARGIN

    def saturday_group():
        rects, line, right = weekend("2026-11-02", "2026-11-09")
        return len(rects) == 1 and abs(rects[0][1] / (rects[0][0] - line) - 0.4) < 0.02

    def lone_sunday():
        rects, line, right = weekend("2026-11-01", "2026-11-02")
        return len(rects) == 1 and rects[0][0] == line and abs(rects[0][1] * 2 - (right - line)) < 10

    seen("土曜と日曜は 1 つの網掛け", saturday_group)
    seen("日曜から始まる期間の日曜も網掛け", lone_sunday)
    seen("休みの網掛けがある", lambda: gx[0].count('name="Weekend') >= 4)
    seen("工程の表の枚は作らない", lambda: "<a:tbl>" not in gx[0])
    seen("月の見出し", lambda: "2026年11月" in gt[0] and "12月" in gt[0])
    seen("棒の横に日付", lambda: "11/2〜11/21" in gt[0] and "11/22〜12/11" in gt[0])
    many = pp.gantt_slides(schedule_rows(40))
    seen("工程が多ければ枚を分ける", lambda: len(many) >= 2 and all("2026年" in t or "11月" in t for t in slide_list_texts(many)))
    long_span = pp.gantt_slides([{"No": "T-001", "工程": "長い", "開始": "2026-01-05", "終了": "2028-06-30", "前提": ""}])
    seen("月の見出しは幅に収まる水準で書く", lambda: "2026年" in slide_list_texts(long_span)[0] and "2026年1月" not in slide_list_texts(long_span)[0])
    # 4. カード
    def cards(n: int, bullets: int = 2, long: str = "文") -> list[dict]:
        return [{"heading": f"見出し{i}", "lines": [(0, f"箇条{i}-{j}" + long, True) for j in range(bullets)]} for i in range(n)]

    seen("カード 3 枚は 1 枚に 3 列", lambda: [len(c) for c, _ in pp.place_cards(cards(3), pp.CY1 - pp.CY0)] == [3])
    seen("カード 6 枚は 1 枚", lambda: [len(c) for c, _ in pp.place_cards(cards(6), pp.CY1 - pp.CY0)] == [6])
    seen("カード 7 枚は 2 枚に分ける", lambda: len(pp.place_cards(cards(7), pp.CY1 - pp.CY0)) >= 2)
    seen("カードの文字は大きく", lambda: all(size >= 14 for _, size in pp.place_cards(cards(3), pp.CY1 - pp.CY0)))
    big = cards(1, bullets=40, long="あ" * 30)
    placed = pp.place_cards(big, pp.CY1 - pp.CY0)
    seen("収まらないカードは割る", lambda: len(placed) >= 2)
    seen("割ってもどの箇条も落とさない", lambda: all(any(f"箇条0-{j}" in line[1] for chunk, _ in placed for card in chunk for line in card["lines"]) for j in range(40)))
    seen("割った前半は見出しを持つ", lambda: placed[0][0][0]["heading"] == "見出し0")
    seen("割った続きに見出し", lambda: any("（続き）" in (card["heading"] or "") for chunk, _ in placed for card in chunk))
    seen("見積りの余裕（行の高さ 1.3 倍以上・折り返し 0.97 以下）", lambda: pp.LINE_HEIGHT >= 1.3 and pp.SAFETY <= 0.97)
    para1 = [{"heading": "大きな見出し", "lines": [(0, "これは長い段落の文である。" * 200, False)]}]
    placed1 = pp.place_cards(para1, pp.CY1 - pp.CY0)
    seen("長い 1 段落は枚を分け、文字を落とさない", lambda: len(placed1) >= 2 and "".join(l[1] for ch, _ in placed1 for c in ch for l in c["lines"]) == para1[0]["lines"][0][1])
    seen("続きの見出しは重ならない", lambda: all("（続き）（続き）" not in (c["heading"] or "") for ch, _ in placed1 for c in ch) and any("（続き）" in (c["heading"] or "") for ch, _ in placed1 for c in ch))
    seen("長い 1 段落の各枚は最小の文字の大きさ以上", lambda: all(size >= pp.CARD_MIN for _, size in placed1))
    parsed = pp.parse_hand(HAND)
    seen("節とカード", lambda: [(t, [c["heading"] for c in cs]) for t, cs in parsed] == [
        ("背景と目的", ["転記に月 40 時間かかっている", "年内に動かしたい", "暫定の回答を引く"]), ("リスク", ["繁忙期に間に合わない"])])
    seen("続きの見出しを毎回足さない（長い段落でも「続き」は 1 つ）", lambda: all("（続き）（続き）" not in (c["heading"] or "") for ch, _ in pp.place_cards(
        [{"heading": "見出し", "lines": [(0, "長い文である。" * 2500, False)]}], pp.CY1 - pp.CY0) for c in ch))
    seen("手書き部分の参照の括弧は外れる", lambda: all("Q-R-001" not in line[1] and "purposes.csv" not in line[1] for _, cs in parsed for c in cs for line in c["lines"]))
    seen("手書き部分の暫定の断りは残る", lambda: any("暫定の回答。利用者に未確認" in line[1] for _, cs in parsed for c in cs for line in c["lines"]))
    seen("箇条は箇条", lambda: all(line[2] for _, cs in parsed[:1] for c in cs for line in c["lines"]))
    # 表の枚の分け方
    rows60 = [[f"行{i:03d}", "あ" * 10] for i in range(60)]
    tslides = pp.table_slides("表", ["名前", "値"], rows60, size=12)
    tt = slide_list_texts(tslides)
    seen("表は枚に分け、見出しを繰り返す", lambda: len(tt) >= 2 and all(t.startswith("名前値") or "名前値" in t for t in tt))
    seen("表の行は 1 度ずつ", lambda: all(sum(f"行{i:03d}" in t for t in tt) == 1 for i in range(60)))
    # 5. 別紙・概要・範囲
    qa_rows = [qa_row(mod, 1), qa_row(mod, 2, rec="B"), qa_row(mod, 3, rec="なし"),
               qa_row(mod, 4, state="暫定反映", ans="A（暫定で採用。業務部の指示）"),
               qa_row(mod, 5, state="確認中", ans="未回答", target="—"),
               qa_row(mod, 6, question="初版では帳票を作らない範囲でよいか", target="spec/scope.md", source="仕様レビュー（Red Team）")]
    x1, x2 = pp.decisions_xlsx(qa_rows), pp.decisions_xlsx(qa_rows)
    def sheet():
        with zipfile.ZipFile(io.BytesIO(x1)) as z:
            return z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    seen("別紙に全件", lambda: sheet().count("<row ") == 1 + len(qa_rows) and all(f"Q-R-{n:03d}" in sheet() for n in range(1, 7)))
    seen("別紙は同じバイト", lambda: x1 == x2)
    seen("別紙の暫定", lambda: ">暫定<" in sheet())
    seen("別紙は整形式", lambda: ET.fromstring(sheet()) is not None)
    ov = slide_list_texts(pp.overview_slides(qa_rows, pp.OVERVIEW_ITEMS, True))
    seen("概要の件数", lambda: any("決定: 4 件" in t and "暫定（利用者に未確認）: 1 件" in t and "未決定: 1 件" in t for t in ov))
    seen("概要の推奨どおり", lambda: any("推奨どおり: 2 件" in t and "推奨と違う: 1 件" in t and "推奨なしの質問: 1 件" in t for t in ov))
    seen("概要の起票元とテーマ", lambda: any("要求確定: 5 件" in t and "仕様レビュー: 1 件" in t and "決定表（業務ルール）" in t for t in ov))
    seen("概要の別紙の案内", lambda: any("decisions.xlsx" in t for t in ov))
    seen("概要の別紙の案内は別紙が無ければ出ない", lambda: not any("decisions.xlsx" in t for t in slide_list_texts(pp.overview_slides(qa_rows, pp.OVERVIEW_ITEMS, False))))
    seen("概要は指示で絞る", lambda: len(pp.overview_slides(qa_rows, ("counts",), True)) == 1
         and not any("起票元ごと" in t for t in slide_list_texts(pp.overview_slides(qa_rows, ("counts",), True))))
    seen("Q&A が 0 行なら概要の枚を作らない", lambda: pp.overview_slides([], pp.OVERVIEW_ITEMS, True) == [])
    free = qa_row(mod, 30, rec="なし", ans="自由に書いた回答", target="spec/scope.md", question="範囲の自由記述")
    seen("推奨なしの質問は推奨どおりと言わない", lambda: "推奨なし" in slide_list_texts(pp.scope_slides([free], None, None, []))[0]
         and "推奨どおり" not in slide_list_texts(pp.scope_slides([free], None, None, []))[0])
    sc = slide_list_texts(pp.scope_slides(qa_rows, None, None, []))
    seen("範囲を決めた質問の 1 枚", lambda: len(sc) == 1 and "帳票を作らない" in sc[0] and "決めたこと" in sc[0] and "作らない" in sc[0])
    seen("範囲の質問を番号で選ぶ", lambda: "質問 2" in slide_list_texts(pp.scope_slides(qa_rows, ["Q-R-002"], None, []))[0])
    seen("範囲の質問を正規表現で選ぶ", lambda: "質問 3" in slide_list_texts(pp.scope_slides(qa_rows, None, "質問 3", []))[0])
    pend = qa_rows + [qa_row(mod, 7, state="確認中", ans="未回答", target="—", question="範囲の未回答の質問")]
    seen("未回答の質問は範囲の枚に載せない", lambda: not any("未回答の質問" in t for t in slide_list_texts(pp.scope_slides(pend, None, None, []))))
    many_scope = [qa_row(mod, 20 + i, target="spec/scope.md", question=f"範囲の質問{i:02d}") for i in range(12)]
    seen("別紙が無いとき範囲の案内は提案書の名前を指す", lambda: "teian.md" in slide_list_texts(pp.scope_slides(many_scope, None, None, [], False, "teian.md"))[0])
    seen("別紙が無いとき変更の案内は提案書の名前を指す", lambda: any("teian.md" in t for t in slide_list_texts(pp.change_slides(
        {"title": "前の版（v1）からの変更", "summary": (["種類", "追加"], [["ファイル", "1"]]), "details": [("ファイル", ["パス", "変化", "削除の理由"], [["spec/a.md", "追加", "—"]])]}, [], "teian.md"))))
    long_q = [qa_row(mod, 40 + i, target="spec/scope.md", question="範囲を決めた長い質問の文" * 16) for i in range(12)]
    lq = pp.scope_slides(long_q, None, None, [], True)
    seen("長い質問でも既定の選び方は 1 枚に収める", lambda: len(lq) == 1)
    def card_bottoms_above_note():
        x = lq[0].render()
        bottoms = [int(a) + int(b) for a, b in re.findall(r'name="Card \d+"/>.*?<a:off x="\d+" y="(\d+)"/><a:ext cx="\d+" cy="(\d+)"', x)]
        note = int(re.search(r'name="Note \d+"/>.*?<a:off x="\d+" y="(\d+)"', x)[1])
        return bool(bottoms) and max(bottoms) <= note
    seen("範囲の枚の注記はカードと重ならない", card_bottoms_above_note)
    ms = slide_list_texts(pp.scope_slides(many_scope, None, None, [], True))
    seen("既定の選び方は 1 枚に収め、残りは別紙を見ると書く", lambda: len(ms) == 1 and "ほかに範囲に関わる質問が 6 件" in ms[0] and "decisions.xlsx" in ms[0] and "範囲の質問06" not in ms[0])
    seen("番号の指示は全部載せる", lambda: "範囲の質問11" in "".join(slide_list_texts(pp.scope_slides(many_scope, [r["No"] for r in many_scope], None, []))))
    seen("範囲の質問が無ければ枚を作らない", lambda: pp.scope_slides(qa_rows, ["Q-999"], None, []) == [])
    # 6. 図
    figs = [("spec/er.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>"), ("spec/screens/wireframe-注文.drawio.svg", DRAWIO_SVG.encode("utf-8"))]
    old = os.environ.get(pp.SPEC_RSVG_ENV)
    try:
        os.environ[pp.SPEC_RSVG_ENV] = str(tool_dir / "rsvg")
        fs, failed = pp.figure_slides(figs)
        seen("図が載る", lambda: len(fs) == 2 and failed == [] and all(s.images and s.images[0].startswith(b"\x89PNG") for s in fs))
        seen("図の見出しはファイル名でない", lambda: slide_list_texts(fs) == ["データモデル（ER 図）", "注文の流れ"])
        seen("drawio の代わりの文字は変換の入力から消える", lambda: b"Text is not SVG" not in Path(str(tool_dir / "rsvg") + ".in").read_bytes())
        seen("正本の SVG は変えない", lambda: b"Text is not SVG" in figs[1][1])
        deck = pp.Deck("図")
        for s in fs:
            deck.add(s)
        parts = deck.parts()
        names = [n for n, _ in parts]
        seen("PNG の部品", lambda: "ppt/media/image1.png" in names and "ppt/media/image2.png" in names)
        seen("PNG のコンテンツタイプ", lambda: 'Extension="png"' in dict(parts)["[Content_Types].xml"])
        seen("PNG の関係", lambda: 'Target="../media/image1.png"' in dict(parts)["ppt/slides/_rels/slide1.xml.rels"]
             and 'Target="../media/image2.png"' in dict(parts)["ppt/slides/_rels/slide2.xml.rels"])
        seen("スライドが PNG を指す", lambda: 'r:embed="rId2"' in slide_xmls(parts)[0])
        def wellformed():
            for n, b in parts:
                if n.endswith((".xml", ".rels")):
                    ET.fromstring(b)
            return True
        seen("部品はすべて整形式", wellformed)
        seen("図の同じ材料は同じバイト（何度作っても）", lambda: deck.parts() == parts)
        os.environ[pp.SPEC_RSVG_ENV] = str(tool_dir / "nothing-here")
        fs2, failed2 = pp.figure_slides(figs)
        seen("道具が無ければ図を載せずに名指しする", lambda: fs2 == [] and failed2 == [p for p, _ in figs])
    finally:
        if old is None:
            os.environ.pop(pp.SPEC_RSVG_ENV, None)
        else:
            os.environ[pp.SPEC_RSVG_ENV] = old
    seen("図の見出し: title のセル", lambda: pp.figure_title("a.svg", DRAWIO_SVG.encode("utf-8")) == "注文の流れ")
    seen("図の見出し: title 要素", lambda: pp.figure_title("a.svg", "<svg><title>返品の画面</title></svg>".encode("utf-8")) == "返品の画面")
    drawio_page = '<svg content="&lt;mxfile&gt;&lt;diagram id=&quot;abc&quot; name=&quot;受注の流れ&quot;&gt;"></svg>'.encode("utf-8")
    seen("drawio のページ名（content 属性の中）", lambda: pp.figure_title("spec/order-flow.drawio.svg", drawio_page) == "受注の流れ")
    seen("図の見出しは unescape する", lambda: pp.figure_title("a.svg", "<svg><title>A &amp; B</title></svg>".encode("utf-8")) == "A & B")
    seen("図形の tooltip は図の見出しにしない", lambda: pp.figure_title("spec/order-flow.svg", "<svg><g><title>tooltip text</title></g></svg>".encode("utf-8")) == "order flow")
    seen("長い題は小さくして 1 行に収める", lambda: 'sz="2600"' not in pp_title("受注から出荷までの業務の流れと現場への影響を踏まえた推奨案の全体像について") and 'sz="2600"' in pp_title("短い題"))
    seen("折れない長い語は新しい行に移してから割る", lambda: pp.lines_needed("項目" + "1" * 54, 12, 100) >= pp.lines_needed("1" * 54, 12, 100) + 1)
    seen("図の見出し: 画面", lambda: pp.figure_title("spec/wireframe-受注一覧.svg", b"<svg/>") == "画面: 受注一覧")
    seen("図の見出し: 一般の名前", lambda: pp.figure_title("spec/order-flow.drawio.svg", b"<svg/>") == "order flow")
    # 8. 仕様書
    ctx = {"title": "仕様書", "version": 1, "hand": [], "scale": [["要求のファイル（`requirements/`）", "12"], ["決定表の行（見出しを除く）", "—（決定表が無い）"]],
           "figures": [], "features": [("F-001", "受注の登録")], "decision": [["区分", "値"], ["ゴールド", "5%"]],
           "out_of_scope": ["| 場面 | 根拠 |", "| --- | --- |", "| 返品の取り消し | 既定の線（まれ × 影響が小さい）。レビューでの経緯: 判定役が指摘した。Q-S-004 |"],
           "files": [f"spec/{i % 3}/f{i}.md" for i in range(30)], "changes": None, "missing": ["requirements/flow.drawio"], "stale": []}
    spec_parts, spec_failed = pp.spec_deck(ctx, pp.Options())
    st = texts(spec_parts)
    seen("値の無い規模の行は出さない", lambda: any("要求のファイル" in t for t in st) and not any("決定表が無い" in t for t in st))
    seen("範囲の外は理由だけ", lambda: any("返品の取り消し" in t and "まれ × 影響が小さい" in t and "レビュー" not in t and "既定の線" not in t and "Q-S-004" not in t for t in st))
    seen("ファイルの一覧は 1 枚にまとめる", lambda: sum("仕様と要求のファイル" in t for t in st) == 1 and any("全部のパスは spec.md を見る" in t for t in st))
    seen("決定表は列ごとのセル", lambda: any("ゴールド5%" in t for t in st))
    seen("載せていない図を名指しする", lambda: any("requirements/flow.drawio" in t and "載せていない" in t for t in st))
    seen("値の無い規模の行を落とした枚数", lambda: spec_failed == [])
    seen("機能の一覧は番号を出さない", lambda: any("受注の登録" in t and "F-001" not in t for t in st))
    return obs


def main() -> int:
    failures: list[str] = []

    def check(label: str, ok: bool) -> None:
        print(f"{'OK  ' if ok else 'NG  '}{label}")
        if not ok:
            failures.append(label)

    with tempfile.TemporaryDirectory(prefix="proposal-pptx-test-") as tmp:
        base = Path(tmp)
        tool_dir = base / "tools"
        tool_dir.mkdir()
        rsvg = tool_dir / "rsvg"
        rsvg.write_text(FAKE_RSVG, encoding="utf-8")
        rsvg.chmod(0o755)
        mod = load()
        real = observe(mod, tool_dir)
        bad = {k: v for k, v in real.items() if v is not True}
        check(f"本物の本体は全部の観測が期待どおり（{len(real)} 件。{'; '.join(f'{k}={v!r}' for k, v in bad.items()) or '問題なし'}）", not bad)

        print("\nリポジトリの外で単体で動く")
        alone = base / "alone"
        alone.mkdir()
        m = load(Path(SCRIPTS / TARGET).read_text(encoding="utf-8"), alone)
        check("3 つのファイルだけの場所で読み込める", callable(getattr(m, "proposal_deck", None)))

        print("\n変異（1 箇所ずつ壊して、観測のどれかが期待と違うこと）")
        source = (SCRIPTS / TARGET).read_text(encoding="utf-8")
        for number, (name, needle, replacement) in enumerate(MUTATIONS):
            if source.count(needle) != 1:
                check(f"変異を当てる先が 1 箇所ある: {name}（{source.count(needle)} 箇所）", False)
                continue
            d = base / f"mut-{number}"
            d.mkdir()
            try:
                mutant = observe(load(source.replace(needle, replacement, 1), d), tool_dir)
            except Exception as e:  # noqa: BLE001
                mutant = {"読み込み": f"例外 {type(e).__name__}"}
            killed = [k for k in real if mutant.get(k) is not True]
            check(f"変異を殺せる: {name}" + ("" if killed else "（生き残った）"), bool(killed) or "読み込み" in mutant)
    if failures:
        print(f"\n{len(failures)} 件の失敗:\n" + "\n".join(f"  - {f}" for f in failures))
        return 1
    print(f"\nOK: 観測 {len(real)} 件・変異 {len(MUTATIONS)} 件")
    return 0


# (名前, 壊す前, 壊した後)
MUTATIONS: list[tuple[str, str, str]] = [
    ("参照の括弧を外さない", "        if only_refs(inner):", "        if False:"),
    ("参照でない括弧も外す", "        if only_refs(inner):", "        if True:"),
    ("番号が続く括弧の番号を外さない", '    text = re.sub(ID.pattern + r"(?=[（(])", "", text)\n', "    pass\n"),
    ("追加の形を使わない", "    for pattern in extra or []:\n        text = pattern.sub(\"\", text)\n", "    pass\n"),
    ("番号だけの根拠を出す", '        return "", "none"\n', "        pass\n"),
    ("長い根拠を出す", "    if lines_needed(text, size, width_pt) > max_lines:", "    if False:"),
    ("開発費と運用費を同じ表に混ぜる", '        rows = [r for r in estimate if r["区分"] == category]\n', "        rows = list(estimate)\n"),
    ("合計の行を出さない", '        body.append(["合計", money(total), ""])\n', "        pass\n"),
    ("費用を枚に分けない", "        if pages[-1] and used + h > avail:\n            pages.append([])\n            used = head_h\n", "        pass\n"),
    ("費用の行を落とす", "        pages[-1].append(index)\n", "        pages[-1].append(index) if index % 7 else None\n"),
    ("節目をダイヤにしない", 'geom="diamond"', 'geom="rect"'),
    ("休みの網掛けを描かない", "            if d.weekday() == 5:\n", "            if False:\n"),
    ("休みの網掛けを日曜だけにする", "            elif d.weekday() == 6:\n", "            elif d.weekday() == 5:\n"),
    ("月の見出しの幅を見ない", "            if fits:\n", "            if True:\n"),
    ("期間の枚を分けない", "        if pages[-1] and used + h > avail:\n            pages.append([])\n            used = 0\n", "        pass\n"),
    ("カードを 1 枚ずつにする", "            for k in range(min(MAX_CARDS, len(queue)), 0, -1):", "            for k in range(1, 0, -1):"),
    ("収まらないカードの続きを捨てる", "                queue = parts + queue[1:]", "                queue = parts[:1] + queue[1:]"),
    ("カードの上限を外す", "MAX_CARDS = 6", "MAX_CARDS = 9"),
    ("続きの見出しを付けない", 'heading if heading is None or heading.endswith("（続き）") else heading + "（続き）"', "heading"),
    ("長い 1 段落を割らない", "    elif lines and len(split_text(lines[0][1])) == 2:", "    elif False:"),
    ("前半の見出しを落とす", '    return [{"heading": heading, "lines": first}, {"heading": more, "lines": second}]', '    return [{"heading": None, "lines": first}, {"heading": more, "lines": second}]'),
    ("範囲の質問に未回答も選ぶ", '    done = [r for r in rows if r["状態"].strip() == qa.DONE]\n    if numbers is not None:', '    done = list(rows)\n    if numbers is not None:'),
    ("推奨なしを推奨どおりと言う", '        mark = "推奨なし" if rec is None else ("推奨どおり" if answer_label(r) == rec else "推奨と違う")', '        mark = "推奨どおり" if answer_label(r) == rec else ("推奨と違う" if rec else "推奨なし")'),
    ("Q&A が 0 行でも概要を作る", "    if not rows:\n        return []\n    if \"counts\" in items:", "    if \"counts\" in items:"),
    ("題を縮めない", "        while size > 14 and lines_needed(text, size, width) > 1:\n            size -= 2\n", "        pass\n"),
    ("図の見出しを unescape しない", "    if m and unescape(m.group(1)).strip().lower() not in GENERIC_NAMES:\n        return unescape(m.group(1)).strip()\n    m = re.search(r'(?:<|&lt;)diagram", "    if m and m.group(1).strip().lower() not in GENERIC_NAMES:\n        return m.group(1).strip()\n    m = re.search(r'(?:<|&lt;)diagram"),
    ("図形の tooltip を図の見出しにする", '    m = re.search(r"<svg\\b[^>]*>\\s*(?:<defs\\b[^>]*/>\\s*|<defs\\b.*?</defs>\\s*)?<title', '    m = re.search(r"<title'),
    ("折れない長い語を現在の行から割る", "                if line > 0:  # 折れない長い語は、新しい行に移してから割る（描画の側もそうする）\n                    count += 1\n                    line = 0.0\n", ""),
    ("別紙が無くても別紙を指す", '        where = "別紙の表（decisions.xlsx）" if appendix else md_name', '        where = "別紙の表（decisions.xlsx）"'),
    ("範囲の枚の注記の分を空けない", "        note_h = CY1 - CY0 - 420000", "        note_h = CY1 - CY0"),
    ("1 枚に収まる問数に絞らない", "            while k > 1 and best_size(cards[:k], note_h) is None:\n                k -= 1\n", "            pass\n"),
    ("drawio のページ名を見ない", "    m = re.search(r'(?:<|&lt;)diagram", "    m = re.search(r'(?:<|&lt;)NODIAGRAM"),
    ("v2 の費用を差分と書かない", '    version_note = f"この版（v{ctx[\'version\']}）の差分の見積り。前の版までの費用は含まない。" if ctx.get("changes") else ""', '    version_note = ""'),
    ("範囲の枚に上限を掛けない", "    if numbers is None:  # 番号を指示されたときは", "    if False:  # 番号を指示されたときは"),
    ("見積りの余裕を外す（行の高さ）", "LINE_HEIGHT = 1.42", "LINE_HEIGHT = 1.0"),
    ("見積りの余裕を外す（折り返し）", "SAFETY = 0.94", "SAFETY = 1.2"),
    ("別紙に全件を書かない", "    for n, row in enumerate(rows, 2):", "    for n, row in enumerate(rows[:4], 2):"),
    ("別紙の暫定を状態にしない", '        state = "暫定" if qa.is_provisional(row) else row["状態"].strip()', '        state = row["状態"].strip()'),
    ("概要の推奨どおりを数えない", "        same = sum(1 for r in done if answer_label(r) is not None and answer_label(r) == qa_recommended(r))", "        same = 0"),
    ("概要の別紙の案内を常に出す", "    if out and appendix:", "    if out:"),
    ("範囲の質問を選ばない", '    return [r for r in done if "scope.md" in r["反映先"] or pattern.search(r["質問"])]', "    return []"),
    ("範囲の質問の番号を無視する", "        return [by_no[n] for n in numbers if n in by_no]", "        return list(by_no.values())"),
    ("drawio の代わりの文字を消さない", 'return DRAWIO_TEXT.sub("", DRAWIO_LINK.sub("", svg))', "return svg"),
    ("図の見出しをファイル名にする", "    named = drawio_title_cell(text)\n", "    named = None\n"),
    ("PNG の部品を書かない", "        return out + media", "        return out"),
    ("PNG の関係を足さない", '                body = body.replace("</Relationships>", extra + "</Relationships>")', "                pass"),
    ("PNG のコンテンツタイプを足さない", "        if name == \"[Content_Types].xml\" and has_images:", "        if False:"),
    ("道具が無くても図を載せたことにする", "        if png is None:\n            failed.append(path)\n            continue\n", "        if png is None:\n            png = b'x'\n"),
    ("値の無い規模の行を出す", '    scale = [[plain(name.replace("`", ""), opts.strip), value] for name, value in ctx["scale"] if not value.startswith("—")]',
     '    scale = [[plain(name.replace("`", ""), opts.strip), value] for name, value in ctx["scale"]]'),
    ("範囲の外に経緯を残す", 'keep = [s for s in re.split(r"(?<=。)", t) if not re.search(r"レビュー|経緯|判定役|Red Team|Domain Checker|Formal Checker|指摘", s)]', 'keep = [s for s in re.split(r"(?<=。)", t)]'),
    ("範囲の外の括りを残す", '    t = re.sub(r"既定の線[（(]([^）)]*)[）)]", r"\\1", t)\n', "    pass\n"),
    ("載せていない図を言わない", '    notes = ([[plain(p.replace("`", "")), "書き出し（.svg）が無いので載せていない"] for p in ctx.get("missing", [])]', '    notes = ([[plain(p.replace("`", "")), "書き出し（.svg）が無いので載せていない"] for p in []]'),
    ("機能の番号を出す", '[[plain(t, opts.strip) or fid] for fid, t in ctx["features"]]', '[[f"{fid} {t}"] for fid, t in ctx["features"]]'),
]


if __name__ == "__main__":
    sys.exit(main())
