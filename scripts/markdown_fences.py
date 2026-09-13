#!/usr/bin/env python3
"""Markdown のコードフェンスを落とす。複数のスクリプトが共有する。

`check-plugin-versions.py`（版の可視テキストを数える）と
`skill-metrics.py`（`SKILL.md` の節と `（必須）` を数える）は、どちらも
**例示のためのフェンスを本物と数えてはいけない**。

**式が 2 箇所にあると片方だけ緑になる**——`diagram_manifest.py` を分けたのと同じ理由で、
ここに 1 つだけ置く。**実行するものではない**（import される）。

標準ライブラリのみ。
"""

from __future__ import annotations


def strip_fences(text: str) -> str:
    """コードフェンスの中身を落とす（``` と ~~~ の両方）。

    フェンス内の記載は読者に「版」として見えないので、それを根拠に合格させると
    可視テキストを検査する意味が無くなる。逆に、**規約を例示しているだけの
    フェンス**を数えると「2 個ある」で誤って落ちる（`CLAUDE.md` がまさにその例を載せている）。

    **同じ文字で、開いたのと同じ長さ以上でしか閉じない**（Markdown の規則）。長さを見ないと、
    4 個の ` で開いた囲み——**まさに ``` を含む例を載せるときの書き方**——が内側の ``` で
    閉じてしまい、例が本文に漏れて「2 個ある」と誤検出する。

    行数を保つため、落とした行は空行に置き換える。
    """
    lines, _ = _scan(text)
    return "\n".join(lines)


def unclosed_fence(text: str) -> str | None:
    """閉じられないまま終わったフェンスの開始記号を返す。無ければ `None`。

    **閉じ忘れは「落とす」形の事故になる。** 閉じていないフェンスは以降を全部
    飲み込むので、**そこから後ろの見出しが丸ごと消える**——`skill-metrics.py` では
    実測で 2 節が表から消え、1 節が 12 行を飲んだ。
    **`--check` は赤くなるが、作り直せば緑になる**ので、鮮度では守れない。
    だから**測る前に落とす**。

    式を `strip_fences` と共有するため、走査は `_scan` に 1 つだけ置く。
    """
    _, fence = _scan(text)
    return fence


def _scan(text: str) -> tuple[list[str], str | None]:
    """フェンスを空行に置き換えた行と、最後まで開いたままのフェンス記号を返す。"""
    out: list[str] = []
    fence: str | None = None
    for line in text.split("\n"):
        marker = line.lstrip()
        run = ""
        for char in ("`", "~"):
            if marker.startswith(char * 3):
                run = marker[: len(marker) - len(marker.lstrip(char))]
                break
        if fence is None:
            if run:
                fence = run
                out.append("")
                continue
        elif run and run[0] == fence[0] and len(run) >= len(fence):
            fence = None
            out.append("")
            continue
        out.append("" if fence else line)
    return out, fence

