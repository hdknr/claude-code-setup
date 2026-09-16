#!/usr/bin/env python3
"""公開サイトへの絶対リンクを集めて、解決するかを見る。複数のスクリプトが共有する。

`check-plugin-versions.py`（配布物からのリンク）と `check-site-links.py`
（リポジトリ全体）が使う。**式が 2 箇所にあると片方だけ緑になる**——
`diagram_manifest.py` / `markdown_fences.py` を分けたのと同じ理由で、ここに 1 つだけ置く。
**実行するものではない**（import される）。

**なぜ機械で見るのか（#97）。** このリポジトリは「**ここには書かない。〇〇を正とする**」
という形で複製を 1 箇所に寄せている。**その形は指し先が実在して初めて意味を持つ**のに、
**指し先の実在は誰も見ていなかった**——実際に #95 で、`#miscount` を「#75 の経緯の正」として
指したのに**その節に #75 が無かった**（レビューが見つけた）。

**mkdocs はこれを検証できない。** 配布物（`plugins/` の `.md`）は `docs_dir` の外なので
読まれないし、**絶対 URL は仮に読んでも検証対象外**である。`strict: true` にしても
**ここだけは守られていない**。

標準ライブラリのみ。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from markdown_fences import strip_fences  # noqa: E402

SITE_PREFIX = "https://hdknr.github.io/claude-code-setup/"

# URL の切れ目。**`*` と `"` を含める**——強調の中や文字列リテラルに URL を書くと、
# そこまで URL として食ってしまう（`.../**` や `.../"` を指すリンクは存在しない）。
URL_BOUNDARY = re.compile(r"[\s)>\]`\"'*|」）。、]")

# 文末に置かれた URL の**末尾の約物**。**境界に入れられない**——ASCII の `.` は
# ドメインにもパスにも出るので、切れ目にすると URL を途中で切ってしまう。
# **末尾からだけ削る**（`…/#verify.` の `.`、`…/#verify,` の `,`）。
TRAILING_PUNCT = ".,;:!?"

# 見出し行に明示 id が付いているか。**`{ #id }` と `{ #id .class }` の両方**——
# `attr_list` はクラスや属性を並べられる（`{ #verify .no-toc }` は Material の定石）。
# **`}` が直後に来ることを要求すると、正しいアンカーを「無い」と言って落ちる。**
HEADING_ID = re.compile(r"^#{1,6}\s.*\{\s*#([A-Za-z0-9_-]+)(?:\s[^}]*)?\}\s*$")



def explicit_heading_ids(text: str) -> set[str]:
    """見出し行に明示された id だけを集める。

    **自動生成の id は数えない。** mkdocs は見出しごとに id を振るが、日本語見出しは
    `_5` のような連番になり、**見出しを 1 つ足すだけで後続がずれる**（#66 で実際に踏んだ）。
    リンク先にそれを使うと、無関係な編集で静かに 404 になる。

    **見出し行だけを見る。** 本文に `{ #x }` と書いてあるだけのものを数えると、
    存在しないアンカーへのリンクを通してしまう。**admonition のタイトルに書いても
    id は付かない**——#94 と #95 で 2 度踏んだので、ここで拾わないことが効いている。

    **コード例も落とす。** フェンスの中に `## 節 { #x }` と書いてあるだけの行は、
    見出しではない。**最初はここを見ておらず、docstring の主張と実装が食い違っていた**
    （#97 の 1 パス目のレビューが再現例つきで指摘）。式は `markdown_fences.py` にある
    ——`check-plugin-versions.py` が版の可視テキストで、`skill-metrics.py` が節の数えで
    使っているのと同じもの。
    """
    return {
        m.group(1)
        for line in strip_fences(text).split("\n")
        if (m := HEADING_ID.match(line.strip()))
    }


def iter_site_links(text: str):
    """テキストから公開サイトへの絶対リンクを取り出す。`(url, page, fragment)` を返す。"""
    for line in text.split("\n"):
        index = 0
        while (index := line.find(SITE_PREFIX, index)) != -1:
            url = URL_BOUNDARY.split(line[index:])[0].rstrip(TRAILING_PUNCT)
            index += len(SITE_PREFIX)
            page, _, fragment = url[len(SITE_PREFIX):].partition("#")
            yield url, page.strip("/"), fragment


def resolve(docs_dir: Path, page: str) -> Path | None:
    """ページ URL に対応する Markdown を返す（無ければ `None`）。"""
    for candidate in (docs_dir / f"{page}.md", docs_dir / page / "index.md"):
        if candidate.is_file():
            return candidate
    return None


def broken_links(source: Path, docs_dir: Path) -> list[str]:
    """1 ファイル分の壊れたリンクを、エラーメッセージの列として返す。

    **`site_url` だけの行は飛ばす。** `mkdocs.yml` の `site_url` は
    ページを指すリンクではないので、ページの実在を要求しない。

    **読めないファイルは黙って飛ばさない。** 最初は空を返しており、**壊れたリンクを
    含む復号できないファイルが「問題なし」で通り、しかも走査件数には数えられていた**
    （#97 の 1 パス目のレビューが再現した）。`token-metrics.py` が
    「読めないファイルは件数を報告に出す。黙って 0 にしない」と書いているのと
    **同じ規範**なのに、こちらで破っていた。

    **指し先のページも同じ扱い。** 読めなければ**その旨を返す**——例外を投げると
    検査全体がトレースバックで止まる。
    """
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"ファイルを読めなかったので検査できていない（{type(exc).__name__}）"]

    problems = []
    pages: dict[Path, set[str] | None] = {}
    for url, page, fragment in iter_site_links(text):
        if not page:
            # サイトのルートそのもの。ページを指していないので検査しない。
            continue
        target = resolve(docs_dir, page)
        if target is None:
            problems.append(f"リンク {url} が指すページが docs/ に無い")
            continue
        if not fragment:
            continue
        if target not in pages:
            # **ページごとに 1 回だけ読む。** 同じページへのリンクが複数あると、
            # 読み直して数え直すことになる。
            try:
                pages[target] = explicit_heading_ids(target.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                pages[target] = None
        ids = pages[target]
        if ids is None:
            problems.append(f"リンク {url} の指すページ {target.name} を読めなかった")
            continue
        if fragment not in ids:
            problems.append(
                f"リンク {url} のアンカー #{fragment} が "
                f"{target.name} の見出しに無い。見出しに `{{ #{fragment} }}` を付ける"
                "（絶対 URL なので mkdocs は検証しない。自動 id は見出しを足すとずれる）"
            )
    return problems
