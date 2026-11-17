#!/usr/bin/env python3
"""関門を通ったかを、計画ファイルの記録とリポジトリの履歴で照合する——マージの前に必ず通す（#1043）。

    python3 <このスキルの base ディレクトリ>/scripts/check-gates.py <計画ファイル> [--head <rev>] [--absent]

**周を閉じてマージに進めてよいかの最終判定を、モデルの読解ではなくスクリプトで照合する。**
`SKILL.md` 手順 7 はマージの前（どの経路でも）にこれを素の 1 行で呼び、0 でなければマージしない。
`merge-pr.py` は `gh pr merge` の前に、確かめた head の SHA を `--head` に渡して呼ぶ（13 で止まる）。

- `<計画ファイル>`——周の計画ファイル（`SKILL.md` 手順 3）。git の操作は、このファイルのある作業ツリーで行う。
- `--head`——照合する先端（既定は計画ファイルのある作業ツリーの `HEAD`）。PR の head の SHA を渡す。
- `--absent`——不在の周のマージとして照合する（線で決めた判断を通し、`マージの反映:` の記録を求める）。

## 記録の形（ここが原本）

計画ファイルの中に、情報文字列が `dev-loop-gates` のコードブロックを**ちょうど 1 つ**置き、1 行に 1 つ書く。
空行と `#` で始まる行は読まない。**ほかの形の行は 2（読めない）**——黙って読み飛ばさない。

```text
周の base: <SHA>                                  # 手順 4 の base（関門に渡した SHA）
関門: Verifier 1 <終点> 反証=<件数>                  # 終点 = その関門に渡した時点の HEAD
関門: /code-review 1 <終点> 指摘=<件数>
関門: Verifier 2 <終点> 反証=<件数>
関門: /code-review 2 <終点> 指摘=<件数>
関門: 2 パス目 該当なし <起点>                       # 1 パス目の指摘対応が 0 行（手順 6）。起点は再開点に書いた SHA
関門: 狭いパス <起点> <終点> 反証=<件数>             # 2 パス目で直した差分（手順 6）
関門: 狭いパス 該当なし
関門: 当て直し <起点> <終点> 反証=<件数>             # 外部レビューの直し・推奨の直しに当てた Verifier 1 回
受入基準: <番号> <満たす|満たさない|BLOCKED|未証明> [判断=<出所>]
マージの反映: <ドキュメントのみ|ドキュメントとプラグインの配布|なし>
```

- **SHA** は 7〜40 桁の 16 進。**件数** は 0 以上の整数（「通した」は結果まで書く——手順 3）。
- **判断の出所** は `利用者の指示（<YYYY-MM-DD…>）`・`マージ前の判断`・`実機確認` の 3 つ。
- **判断=** の後ろは行末まで（空白を含んでよい）。
- **受入基準の表**: 見出しに「受入基準」を含む節（`##` 以下の見出し。次の同じか上の階層の見出しまでで、下位の見出しの下を含む。
  `#` の見出しは文書の題で、節に数えない）の中の表のうち、第 1 列の見出しが `#`・`番号`・`ID` のもの。その第 1 列が番号で、**計画の中で重複しない**
  （まとめの周は Issue ごとに番号を分ける——cruise の `references/grouping.md`）。

## 何を照合するか

1. **関門の記録**——1 パス目の Verifier と `/code-review`・2 パス目（両方か「該当なし」）・狭いパス（記録か「該当なし」）。
2. **コミットごとに、それを見た関門があるか**——周の base（既定ブランチに入っていること）から head までの周自身の線（`--first-parent`）の、
   既定ブランチに入っていないコミットを 1 つずつ見て、
   **ある回の Verifier と `/code-review` の両方の終点に含まれる**か、**狭いパス・当て直しの範囲（起点の後から終点まで）にある**か、
   **関門が見なくてよい形**（計画ファイルだけ・版の行だけ（下の「守らない」の形）を変えたコミット・既定ブランチの親を取り込んだ merge commit）かのどれか。
   **どれでもないコミットがあれば通さない**——2 パス目を回さずに直した・狭いパスの後に直した・最後の関門の後に足した、の形がここに出る。
3. **受入基準の判定**——表の番号ごとに判定があるか。`BLOCKED`・`満たさない` は判断の出所があるか（下の表）。
4. **マージの反映**——記録の値が、既定ブランチの `.claude/dev-loop.md` の宣言と同じか。宣言はコードブロックと HTML コメントの外の行だけを読み
   （`check-unattended-env.py` の `visible_lines`）、読める値（`ドキュメントのみ`・`ドキュメントとプラグインの配布`）がちょうど 1 本のときだけ宣言がある（`references/absent-lines.md` の「行が無い・値が違う・2 本以上ある」）。
   `なし` は宣言が無いこと。
   **宣言は既定ブランチから読む**——PR の中で足した・書き換えた宣言を効かせない（`references/absent-lines.md`）。
5. **影響範囲（`--absent` だけ。#1047）**——周の差分（既定ブランチとの分岐点から head まで。`git diff --name-only --no-renames`。計画ファイルは数えない）が触るファイルのうち、
   次の 2 つの範囲に当たるものがあれば通さない。宣言そのものを外す差分と、読めない宣言も通さない（下の 3・4 つ目。どれも不在の周ではマージせず、PR で止めて利用者に回す——`references/absent-lines.md` の「影響範囲で止める」）:
   - **既定ブランチの `.claude/dev-loop.md` の `不在で止める範囲: <パターン>` の行**——1 行に 1 つ、何本でも書ける。パターンは glob（`fnmatch`。`*` はディレクトリ区切りも跨ぐ）で、
     `/` で終われば配下すべて。glob の文字（`*?[`）を持たないパターンは、そのパス自身と配下の両方に当てる（`src/shared` は `src/shared/x.py` にも当たる）。
     読むのはコードブロックと HTML コメントの外の行だけ（4 と同じ読み方）。
   - **既定ブランチで戻した（revert した）コミットが触ったファイル**——既定ブランチから辿れるコミットの本文の `This reverts commit <SHA>`（`git revert` が書く行）のうち、
     その SHA が既定ブランチから辿れる（既定ブランチの祖先の）もの。merge commit で入れた PR の中のコミットも含む。戻されたコミットがその最初の親から変えたファイルを、戻した履歴のある範囲とする。
   - **周の差分が、既定ブランチの `不在で止める範囲:` の行を 1 本でも外す**——分岐点にも既定ブランチにもあるパターンの行が、head の `.claude/dev-loop.md` に無い。
     周が自分の止まる範囲を外さない。分岐の後に既定ブランチへ足された行は、head に無くても外したと読まない。
   - **読めない宣言**——行頭の Markdown の飾りを外して `不在で止める範囲` で始まるのに、直後（強調の閉じと空白を除く）がコロン（全角も）でも助詞（は・を・が・も・の・に・で・と・や）でもない行
     （`=`・コロン抜け・読点・値の無い宣言（`**不在で止める範囲:**`）など。助詞が続く行は散文として読み飛ばし、飾りを外してもキーワードで始まらない行は読まない。飾った行・全角のコロンの行・強調の閉じがコロンの内側にある行は宣言として読む）と、既定ブランチの木（`git ls-tree`）と周の差分のどのパスにも当たらないパターン
     （`/` で始まる・行末の注釈・`**/x` が根の `x` に当たらない、など）。書き損じを文字で列挙せず、当たるパスが無いことで見る——**まだ無いパスを宣言すると、できるまで止まり続ける**。

| 判定 | 通る判断の出所 |
| --- | --- |
| `満たす`・`未証明` | 要らない（`未証明` は PR コメントで人間のレビューに回す——手順 6） |
| `BLOCKED` | `利用者の指示（日付）`。`--absent` なら `マージ前の判断`・`実機確認` も |
| `満たさない` | `利用者の指示（日付）` だけ（線では通さない——`references/absent-lines.md` の「マージ前の判断 = 推奨で決めて起票」） |

## 何を守るか

- **記録が無い・2 つある計画を通さない**（2）。
- **読めない行を黙って読み飛ばさない**（2）。
- **受入基準の表が無い計画を通さない**（2）——番号と判定を突き合わせる相手が無い。
- **受入基準の番号が重複する計画を通さない**（2）——1 行の判定が、別の表の同じ番号まで覆ってしまう。
- **1 パス目の Verifier と `/code-review` の両方が無ければ通さない。**
- **2 パス目は、両方の記録か「該当なし」の明記が無ければ通さない。**
- **狭いパスは、記録か「該当なし」の明記が無ければ通さない。**
- **2 パス目が「該当なし」なら、狭いパスの記録を通さない**——狭いパスは 2 パス目で直した差分に当てるもので、1 パス目の後の直しを覆わない。
- **記録の SHA が head の祖先でなければ通さない**——rebase した・別の履歴の記録。
- **周の base が既定ブランチに入っていなければ通さない**——base を周の線の上にずらすと、その前のコミットが照合から外れる。
- **関門が見ていないコミットを通さない**——ある回の 2 つの関門の両方の終点に含まれるか、狭いパス・当て直しの範囲にあるものだけを、見たとみなす。
- **狭いパス・当て直しの起点そのものを、その範囲に数えない**——範囲は起点の後から終点まで。
- **計画ファイルと版の行だけのコミットは、関門が見ていなくても通す**——関門の後に再開点を書く・main を取り込んで版を上げ直す（cruise の `references/parallel.md`）。
- **既定ブランチ以外を取り込んだ merge commit は通さない**——既定ブランチに入っていない親は、関門の見ていないコミットを連れてくる。
- **受入基準の表の番号に判定が無ければ通さない。**
- **`BLOCKED`・`満たさない` は、判断の出所が無ければ通さない。**
- **`満たさない` を線（`マージ前の判断`・`実機確認`）で通さない。**
- **`--absent` でなければ、線の判断を通さない**——線は不在の周にだけ効く。
- **`マージの反映:` の記録が既定ブランチの宣言と違えば通さない**——`なし` と書いても、既定ブランチに宣言があれば違う。
- **宣言（`マージの反映:`・`不在で止める範囲:`）は既定ブランチから読み、head からは読まない。**
- **コードブロックと HTML コメントの中の行・読めない値・2 本以上の宣言を、宣言と読まない**（`不在で止める範囲:` は何本でも読む）。
- **`--absent` では、`マージの反映:` の記録が無ければ通さない。**
- **`--absent` では、既定ブランチの宣言 `不在で止める範囲:` に当たるファイルを変えた差分を通さない**（#1047）。
- **`/` で終わるパターンは、その配下のファイルすべてに当てる。**
- **`--absent` では、既定ブランチで戻した（revert した）コミットが触ったファイルを変えた差分を通さない**（#1047）。
- **既定ブランチから辿れないコミットを戻した行は、戻した履歴に数えない**——squash した PR の本文に残った、PR の途中の revert。
- **merge commit で既定ブランチに入れたコミットを戻した行も、戻した履歴に数える**——戻されたコミットが既定ブランチの最初の親の線に無くても。
- **既定ブランチの木と周の差分のどのパスにも当たらないパターンを、黙って捨てない**——読めない宣言として止める。
- **行頭の Markdown の飾り（リストの印・番号・チェックボックス・見出し・引用・強調・空白）を外してから読む**——飾った宣言（`**不在で止める範囲:** x`・`## 不在で止める範囲: x` など）を宣言として読む。
- **キーワードで始まり、コロン（全角も）でも助詞でもないものが続く行を、黙って捨てない**——`=`・コロン抜け・読点の行を読めない宣言として止める。
- **キーワードの直後が助詞（は・を・が・も・の・に・で・と・や）の行は、散文として読み飛ばす**——説明の行で不在のマージを止めない。
- **全角のコロンの宣言も宣言として読む。**
- **強調の閉じがコロンの内側にある宣言（`*不在で止める範囲:* x`・`**不在で止める範囲:**x`・`_…:_ x`）も宣言として読む**——行頭で開いた強調と同じ印がコロンの直後にあれば、外してから値を読む（開きの無い行の値の先頭の `*` は glob・`_` はパスの一部として残す。`*`・`_`・`__` の閉じはコロンの直後に空白か行末が続くときだけ、`**` は値が続く `**…:**x` も閉じと読む——`:*.zz`・`:_build/` のように値が続く形は値、コロンの後に空白を置く `: *.zz` も値）。
- **値の無い宣言（`**不在で止める範囲:**`）を、`**` というパターンと読まない**——全部の差分に当たったと言わず、読めない宣言として名指して止める。
- **パスは引用符なしで読む**（`core.quotePath=false`）——非 ASCII のパスの宣言を、どのパスにも当たらない宣言と読まない。
- **分岐の後に既定ブランチへ足された範囲の宣言を、周の差分が外したと読まない。**
- **glob の文字を持たないパターンは、配下にも当てる**——末尾の `/` を書き忘れたディレクトリを、黙って何にも当たらない宣言にしない。
- **`--absent` では、既定ブランチの `不在で止める範囲:` の行を外す差分を通さない**——周が自分の止まる範囲を外さない。
- **影響範囲を見る差分は既定ブランチとの分岐点から取る**——周に取り込んだ既定ブランチの変更（周の base より後）を、周の差分に数えない。
- **`--absent` でなければ、影響範囲で止めない**——居る周のマージは人が決める。
- **判定できないことを、通過と答えない**（7）。

## 終了コード

- **0**: 照合を通った
- **1**: 引数の誤り
- **2**: 記録の形が違う——記録が無い・2 つある・読めない行・受入基準の表が無い（何が違うかを出す）
- **3**: 照合を通らない（理由を全部出す）
- **7**: 判定できなかった——`git` が失敗した・`--head` が解決しない・要る既定ブランチの参照が無い

## 何を守らないか

- **記録が本当かは見ない**——関門の件数・判断の出所・`利用者の指示` の日付は、書いてあれば通る。照合が塞ぐのは**記録が無い・履歴と合わない**形だけで、記録を書き換えれば通る。
- **関門が未コミットの変更を見たかは見ない**——終点はコミットで、関門に渡した時点の未コミットの分は記録に残らない。未コミットのまま関門に渡し、後でコミットした分は「見ていない」と出る（手順 6 は、渡す前にコミットする）。
- **merge commit の中の変更は見ない**——既定ブランチの親を取り込んだ merge commit は丸ごと通す。衝突を解いた変更は関門が見ていなくても通る。
- **版の行の形はこのリポジトリの決まり**——`.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` の `"version": "…"` の行と、
  `SKILL.md` の `<!-- skill-version: … -->`・`> **このスキルの版: …**（プラグイン `…`）。` の行全体。ほかのファイル・形の版の行（`package.json` など）は、関門の見ていない変更と出る。
  生成ブロックの書き直し（`skill-metrics.py`）など、版のほかの機械の書き直しも同じく出る——取り込みの merge commit の中で直せば通る。
- **既定ブランチは手元の追跡参照で決める**（`refs/remotes/origin/HEAD` → `origin/main` → `origin/master`）。**取り直さない**——古ければ古い既定ブランチと比べる。
- **狭いパスの指摘の振り分け・PR コメントの推奨・CI・宣言の外の反映（ワークフロー）は見ない**——今までどおり親のモデルと `merge-pr.py` の既存の段。
- **線の判断（`マージ前の判断`・`実機確認`）が、台帳の確かめた線にその値であるかは見ない**——`--absent` かどうかと、判定に対して出所が許されるかだけを見る。線があるかは親が読む（`references/absent-lines.md`）。
- **載せ替えた（rebase した）周の記録の書き直しが正しいかは見ない**——積んだ周は載せ替えの後、記録の SHA を載せ替え先の対応するコミットと新しい base に
  書き直す（`references/stacked.md` の「下の周がマージされたら」）。照合は書き直した記録を履歴と突き合わせるだけで、対応が `git range-diff` のとおりかは見ない。
- **`当て直し` がどの直しに当てたものかは見ない**——2 パス目を「該当なし」にして、1 パス目の後の直しを `当て直し`（Verifier 1 回）で覆った記録は通る。
  外部レビュー bot の指摘を 2 パス目「該当なし」の周で直した正しい記録（`references/external-review.md` の「2 パスとの関係」）と、履歴の形が同じで分けられない。
- **既定ブランチの追跡参照が無いリポジトリでは判定できない**（7）——base が既定ブランチに入っているかを決められない。
- **HTML コメントの中の記録も読む**——コメントで無効にした記録も、記録の 1 つに数える。
- **計画は作業ツリーのファイルを読む**——`--head` のコミットの中の計画とは比べない（`merge-pr.py` は未コミットと push していない worktree を先に止める）。
- **受入基準の表の形は 1 つだけ読む**——第 1 列の見出しが `#`・`番号`・`ID` の表。箇条書きの受入基準は数えない（表が無ければ 2）。
- **計画ファイルの外の受入基準（Issue の本文）とは照合しない。**
- **影響範囲は、ファイルの名前でだけ決める**——差分の中身（どの関数・何行）は見ない。宣言に無い共有モジュール・スキーマは、名前が何でも止めない（宣言するのは利用者）。
- **計画ファイルは影響範囲に数えない**——周の記録で、成果物ではない（`docs/` を宣言しても、計画だけでは止まらない）。
- **戻した履歴は、既定ブランチの本文の `This reverts commit <SHA>` の行だけから読む**——GitHub の Issue・PR・ラベルは読まない（取り直さない・ネットに出ない）。
  `git revert` を使わずに手で戻した変更は数えない。revert でない本文がこの行を引用していても、戻したと読む（止まる側に倒れる）。
  **merge commit で入れるリポジトリでは、PR の中で自分のコミットを revert した行も数える**（その PR がマージされた後は、戻されたコミットも既定ブランチから辿れる。止まる側に倒れる）。
  **期間で区切らない**——何年前に戻した範囲でも止まる。止めたくなければ利用者が居る周でマージする。
  **マージの後に見つかった欠陥**（revert していないもの）は、利用者が `不在で止める範囲:` の行を足して止める（`references/absent-lines.md` の「影響範囲で止める」）。
- **戻されたコミットの範囲は、その最初の親からの差分のファイルである**——merge commit を戻したなら、取り込んだ側の変更すべて。

## 判定を足すとき（#1047 など）

照合は `CHECKS` に並べた関数で行う。1 つの関数は `(record, ctx) -> list[str]`（通らない理由の一覧。空なら通る）で、
`record` は読んだ記録（`Record`）、`ctx` は git の操作と引数（`Context`）。**判定を足すときは関数を足して `CHECKS` に並べ、
記録に行の形を足すなら上の「記録の形」の表と `parse` の `LINE_FORMS` を同じコミットで直す。**
"""
from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

FENCE_OPEN = re.compile(r"^(`{3,}|~{3,})\s*dev-loop-gates\s*$")
FENCE_ANY = re.compile(r"^(`{3,}|~{3,})")
SHA = r"([0-9a-f]{7,40})"
COUNT = r"(?:反証|指摘)=(\d+)"
VERDICTS = ("満たす", "満たさない", "BLOCKED", "未証明")
USER = re.compile(r"^利用者の指示（\d{4}-\d{2}-\d{2}[^）]*）$")
LINE_JUDGES = ("マージ前の判断", "実機確認")  # 線で決めた判断——不在の周だけ
REFLECTIONS = ("ドキュメントのみ", "ドキュメントとプラグインの配布", "なし")
DEFAULT_REFS = ("refs/remotes/origin/HEAD", "refs/remotes/origin/main", "refs/remotes/origin/master")
# 関門が見なくてよい「版の行」（このリポジトリの決まり。docstring の「守らない」）
VERSION_JSON = re.compile(r'^\s*"version"\s*:\s*"[^"]*",?\s*$')
VERSION_JSON_FILES = (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json")
VERSION_SKILL = re.compile(r"^<!-- skill-version: \S+ -->$|^> \*\*このスキルの版: \S+\*\*（プラグイン `[^`]+`）。$")
ID_HEADERS = ("#", "番号", "ID")
STOP_KEYWORD = "不在で止める範囲"  # 影響範囲の宣言のキーワード（#1047）
# 行頭の Markdown の飾り（空白・リストの印・番号・チェックボックス・見出し・引用・強調の開き）。1 つずつ繰り返し外す（#1047 R1）
DECOR = re.compile(r"^(?:\s+|[-*+]\s+|\d+[.)]\s+|\[[ xX]\]\s*|#{1,6}\s+|>\s*|\*\*|__|\*|_)")
PARTICLES = "はをがものにでとや"  # キーワードの直後がこれなら散文（#1047 J2）
COLONS = (":", "：")
REVERTS = re.compile(r"This reverts commit ([0-9a-f]{7,64})\b")  # SHA-1（40 桁）と SHA-256（64 桁）

LINE_FORMS = {
    "base": re.compile(rf"^周の base:\s*{SHA}$"),
    "pass": re.compile(rf"^関門:\s*(Verifier|/code-review)\s+([0-9]+)\s+{SHA}\s+{COUNT}$"),
    "pass2_none": re.compile(rf"^関門:\s*2\s*パス目\s+該当なし\s+{SHA}$"),
    "narrow": re.compile(rf"^関門:\s*狭いパス\s+{SHA}\s+{SHA}\s+{COUNT}$"),
    "narrow_none": re.compile(r"^関門:\s*狭いパス\s+該当なし$"),
    "redo": re.compile(rf"^関門:\s*当て直し\s+{SHA}\s+{SHA}\s+{COUNT}$"),
    "criterion": re.compile(r"^受入基準:\s*(\S+)\s+(\S+)(?:\s+判断=(.+?))?$"),
    "reflection": re.compile(r"^マージの反映:\s*(\S+)$"),
}


def closes(line: str, fence: str) -> bool:
    """コードブロックを閉じる行か（開いた印と同じ文字が同じ数以上だけの行）。"""
    t = line.strip()
    return t.startswith(fence) and not t.strip(fence[0])


def _visible_lines():
    """`.claude/dev-loop.md` の宣言を読む関数（同じ場所の `check-unattended-env.py` の `visible_lines`。読み方の写しを作らない）。"""
    path = Path(__file__).resolve().parent / "check-unattended-env.py"
    try:
        spec = importlib.util.spec_from_file_location("dev_loop_check_unattended_env", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.visible_lines
    except (OSError, ImportError, SyntaxError, AttributeError) as e:
        raise Undetermined(f"宣言を読む check-unattended-env.py を読み込めない（{path}）: {e}") from e


class Malformed(Exception):
    """記録の形が違う（2）。"""


class Undetermined(Exception):
    """判定できない（7）。"""


@dataclass
class Record:
    base: str | None = None
    passes: list[tuple[str, int, str]] = field(default_factory=list)  # (Verifier|/code-review, 回, 終点)
    pass2_none: list[str] = field(default_factory=list)  # 起点
    narrow: list[tuple[str, str]] = field(default_factory=list)  # (起点, 終点)
    narrow_none: bool = False
    redo: list[tuple[str, str]] = field(default_factory=list)
    criteria: dict[str, tuple[str, str | None]] = field(default_factory=dict)  # 番号 → (判定, 判断)
    reflection: str | None = None
    table_ids: list[str] = field(default_factory=list)


def gate_block(text: str) -> list[str]:
    """`dev-loop-gates` のブロックの中の行。無い・2 つある・閉じていないなら Malformed。"""
    blocks, cur, fence = [], None, None
    for line in text.splitlines():
        if cur is None:
            m = FENCE_OPEN.match(line)
            if m:
                cur, fence = [], m.group(1)
            elif FENCE_ANY.match(line):
                cur, fence = False, FENCE_ANY.match(line).group(1)  # ほかのコードブロック——中は読まない
            continue
        if closes(line, fence):
            if cur is not False:
                blocks.append(cur)
            cur, fence = None, None
            continue
        if cur is not False:
            cur.append(line)
    if cur is not None:
        raise Malformed("コードブロックが閉じていない")
    if not blocks:
        raise Malformed("記録（情報文字列が dev-loop-gates のコードブロック）が無い")
    if len(blocks) > 1:
        raise Malformed(f"記録が {len(blocks)} つある（1 つだけ置く）")
    return blocks[0]


def table_ids(text: str) -> list[str]:
    """受入基準の表の第 1 列の番号（コードブロックの外・見出しに「受入基準」を含む節）。"""
    ids, in_section, level, fence, in_table = [], False, 0, None, False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if fence:
            if closes(line, fence):
                fence = None
            continue
        m = FENCE_ANY.match(line)
        if m:
            fence = m.group(1)
            continue
        h = re.match(r"^(#{1,6})\s", line)
        if h:
            in_table = False
            if len(h.group(1)) == 1:  # 文書の題——節に数えない
                in_section = False
            elif not (in_section and len(h.group(1)) > level):  # 下位の見出しは節の中
                in_section, level = "受入基準" in line, len(h.group(1))
            continue
        if not in_section or not line.lstrip().startswith("|"):
            in_table = False
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if in_table:
            if not re.fullmatch(r":?-{3,}:?", cells[0]):
                ids.append(cells[0].replace("**", "").replace("`", "").strip())
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if cells[0] in ID_HEADERS and re.match(r"^\s*\|\s*:?-{3,}", nxt):
            in_table = True
    return [x for x in ids if x]


def parse(text: str) -> Record:
    rec = Record()
    for line in gate_block(text):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        for kind, rx in LINE_FORMS.items():
            m = rx.match(s)
            if m:
                break
        else:
            raise Malformed(f"読めない行: {s}")
        g = m.groups()
        if kind == "base":
            if rec.base:
                raise Malformed("周の base が 2 行ある")
            rec.base = g[0]
        elif kind == "pass":
            rec.passes.append((g[0], int(g[1]), g[2]))
        elif kind == "pass2_none":
            rec.pass2_none.append(g[0])
        elif kind == "narrow":
            rec.narrow.append((g[0], g[1]))
        elif kind == "narrow_none":
            rec.narrow_none = True
        elif kind == "redo":
            rec.redo.append((g[0], g[1]))
        elif kind == "criterion":
            if g[1] not in VERDICTS:
                raise Malformed(f"受入基準の判定が読めない: {s}（{'・'.join(VERDICTS)} のどれか）")
            if g[0] in rec.criteria:
                raise Malformed(f"受入基準 {g[0]} の判定が 2 行ある")
            rec.criteria[g[0]] = (g[1], g[2])
        elif kind == "reflection":
            if g[0] not in REFLECTIONS:
                raise Malformed(f"マージの反映の値が読めない: {s}")
            if rec.reflection:
                raise Malformed("マージの反映が 2 行ある")
            rec.reflection = g[0]
    if not rec.base:
        raise Malformed("周の base の行が無い")
    rec.table_ids = table_ids(text)
    if not rec.table_ids:
        raise Malformed("受入基準の表が無い（見出しに「受入基準」を含む節に、第 1 列の見出しが # の表を置く）")
    dup = sorted({i for i in rec.table_ids if rec.table_ids.count(i) > 1})
    if dup:
        raise Malformed(f"受入基準の番号が重複している: {'・'.join(dup)}（まとめの周は Issue ごとに番号を分ける）")
    return rec


@dataclass
class Context:
    top: Path
    plan_rel: str
    head: str
    absent: bool
    _sha: dict = field(default_factory=dict)
    _default: str | None = None

    def git(self, *args: str, ok: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess:
        try:
            res = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=str(self.top),
                                 capture_output=True, text=True)  # 非 ASCII のパスを引用符なしで読む（#1047 J1）
        except OSError as e:
            raise Undetermined(f"git を起動できなかった: {e}") from e
        if res.returncode not in ok:
            raise Undetermined(f"git {' '.join(args)} が失敗した（rc={res.returncode}）: {res.stderr.strip()}")
        return res

    def resolve(self, rev: str) -> str | None:
        if rev not in self._sha:
            res = self.git("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}", ok=(0, 1))
            self._sha[rev] = res.stdout.strip() if res.returncode == 0 else None
        return self._sha[rev]

    def is_ancestor(self, a: str, b: str) -> bool:
        return self.git("merge-base", "--is-ancestor", a, b, ok=(0, 1)).returncode == 0

    def default_ref(self) -> str:
        if self._default is None:
            for ref in DEFAULT_REFS:
                if self.resolve(ref):
                    self._default = ref
                    break
            else:
                raise Undetermined("既定ブランチの追跡参照が無い（" + "・".join(DEFAULT_REFS) + "）")
        return self._default


def known(ctx: Context, sha: str, what: str, reasons: list[str]) -> str | None:
    """記録の SHA を解決し、head の祖先であることを確かめる。だめなら理由を足して None。"""
    full = ctx.resolve(sha)
    if not full:
        reasons.append(f"{what} の SHA {sha} がこのリポジトリに無い")
        return None
    if not ctx.is_ancestor(full, ctx.head):
        reasons.append(f"{what} の SHA {sha} が head {ctx.head[:12]} の祖先でない（rebase した・別の履歴の記録）")
        return None
    return full


def check_passes(rec: Record, ctx: Context) -> list[str]:
    """関門の記録がそろっているか。"""
    reasons = []
    kinds = {(k, n) for k, n, _ in rec.passes}
    for n in sorted({n for _, n, _ in rec.passes}):
        if n not in (1, 2):
            reasons.append(f"{n} パス目の記録がある（関門は 2 パスで打ち切る——手順 6）")
    for k in ("Verifier", "/code-review"):
        if (k, 1) not in kinds:
            reasons.append(f"1 パス目の {k} の記録が無い")
    two = [k for k in ("Verifier", "/code-review") if (k, 2) in kinds]
    if rec.pass2_none and two:
        reasons.append("2 パス目に、記録と「該当なし」の両方がある")
    elif not rec.pass2_none and len(two) < 2:
        missing = [k for k in ("Verifier", "/code-review") if k not in two]
        reasons.append(f"2 パス目の {'・'.join(missing)} の記録も「該当なし」も無い")
    if rec.pass2_none and rec.narrow:
        reasons.append("2 パス目が「該当なし」なのに狭いパスの記録がある（狭いパスは 2 パス目で直した差分に当てる）")
    if rec.narrow_none and rec.narrow:
        reasons.append("狭いパスに、記録と「該当なし」の両方がある")
    elif not rec.narrow_none and not rec.narrow:
        reasons.append("狭いパスの記録も「該当なし」も無い")
    return reasons


def exempt(ctx: Context, commit: str, parents: list[str]) -> bool:
    """関門が見なくてよいコミットか。"""
    if len(parents) > 1:
        default = ctx.default_ref()
        return all(ctx.is_ancestor(p, default) for p in parents[1:])
    files = [f for f in ctx.git("diff-tree", "-r", "--no-commit-id", "--name-only", "--no-renames",
                                commit).stdout.splitlines() if f]
    if not files:
        return True  # 中身の変わらないコミット
    for f in files:
        if f == ctx.plan_rel:
            continue
        if f.endswith(VERSION_JSON_FILES):
            rx = VERSION_JSON
        elif f == "SKILL.md" or f.endswith("/SKILL.md"):
            rx = VERSION_SKILL
        else:
            return False
        diff = ctx.git("diff", "-U0", "--no-color", "--no-ext-diff", f"{commit}^", commit, "--", f).stdout
        changed = [l[1:] for l in diff.splitlines()
                   if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        if not changed or not all(rx.match(l) for l in changed):
            return False
    return True


def check_coverage(rec: Record, ctx: Context) -> list[str]:
    """周の線のコミットを 1 つずつ、それを見た関門があるかで見る。"""
    reasons = []
    base = known(ctx, rec.base, "周の base", reasons)
    ends: dict[tuple[str, int], list[str]] = {}
    for k, n, sha in rec.passes:
        full = known(ctx, sha, f"{n} パス目の {k}", reasons)
        if full:
            ends.setdefault((k, n), []).append(full)
    for sha in rec.pass2_none:
        known(ctx, sha, "2 パス目「該当なし」の起点", reasons)
    ranges = []
    for name, rows in (("狭いパス", rec.narrow), ("当て直し", rec.redo)):
        for s, e in rows:
            fs, fe = known(ctx, s, f"{name}の起点", reasons), known(ctx, e, f"{name}の終点", reasons)
            if not (fs and fe):
                continue
            if not ctx.is_ancestor(fs, fe):
                reasons.append(f"{name}の起点 {s} が終点 {e} の祖先でない")
            else:
                ranges.append((fs, fe))
    if not base:
        return reasons
    default = ctx.default_ref()
    if not ctx.is_ancestor(base, default):
        reasons.append(f"周の base {rec.base} が既定ブランチ（{default}）に入っていない"
                       "（手順 4 の base——周を切った元の参照との merge-base を書く）")
        return reasons
    out = ctx.git("rev-list", "--first-parent", "--reverse", "--parents", f"{base}..{ctx.head}").stdout
    for line in out.splitlines():
        commit, *parents = line.split()
        if ctx.is_ancestor(commit, default):
            continue  # 既定ブランチに入っている——周のコミットではない
        seen = any(all(any(ctx.is_ancestor(commit, e) for e in ends.get((k, n), []))
                       for k in ("Verifier", "/code-review")) for n in (1, 2))
        seen = seen or any(commit != s and ctx.is_ancestor(s, commit) and ctx.is_ancestor(commit, e)
                           for s, e in ranges)
        if seen or exempt(ctx, commit, parents):
            continue
        subject = ctx.git("log", "-1", "--format=%s", commit).stdout.strip()
        reasons.append(f"関門が見ていないコミット: {commit[:12]} {subject}")
    return reasons


def check_criteria(rec: Record, ctx: Context) -> list[str]:
    """受入基準の表の番号ごとの判定と、BLOCKED・満たさないの判断の出所。"""
    reasons = []
    for i in rec.table_ids:
        if i not in rec.criteria:
            reasons.append(f"受入基準 {i} の判定が無い")
    for i in rec.criteria:
        if i not in rec.table_ids:
            reasons.append(f"受入基準 {i} が受入基準の表に無い")
    for i, (verdict, judge) in rec.criteria.items():
        if verdict in ("満たす", "未証明"):
            continue
        if judge is None:
            reasons.append(f"受入基準 {i} が {verdict} で、判断の出所（判断=）が無い")
        elif USER.match(judge):
            continue
        elif judge not in LINE_JUDGES:
            reasons.append(f"受入基準 {i} の判断の出所が読めない: {judge}")
        elif verdict == "満たさない":
            reasons.append(f"受入基準 {i} が満たさないで、線（{judge}）では通さない（利用者の指示だけ）")
        elif not ctx.absent:
            reasons.append(f"受入基準 {i} が BLOCKED で、線（{judge}）は不在の周（--absent）でしか通さない")
    return reasons


def visible(text: str) -> list[str]:
    """`.claude/dev-loop.md` の、コードブロックと HTML コメントの外の行。"""
    return _visible_lines()(text.lstrip("\ufeff"))


def default_dev_loop_md(ctx: Context) -> str:
    """既定ブランチの `.claude/dev-loop.md`（無ければ空）。宣言は head からは読まない。"""
    res = ctx.git("show", f"{ctx.default_ref()}:.claude/dev-loop.md", ok=(0, 128))
    return res.stdout if res.returncode == 0 else ""


def declared(text: str) -> str:
    """`.claude/dev-loop.md` の `マージの反映:` の宣言。読める値がちょうど 1 本のときだけその値、ほかは `なし`。"""
    values = []
    for line in visible(text):
        m = re.match(r"^マージの反映:\s*(.+?)\s*$", line)
        if m:
            values.append(m.group(1))
    if len(values) == 1 and values[0] in REFLECTIONS[:2]:
        return values[0]
    return "なし"


def check_reflection(rec: Record, ctx: Context) -> list[str]:
    """`マージの反映:` の記録が、既定ブランチの宣言と同じか。"""
    if rec.reflection is None:
        return ["不在の周で、マージの反映の記録が無い"] if ctx.absent else []
    ref = ctx.default_ref()
    value = declared(default_dev_loop_md(ctx))
    if value != rec.reflection:
        return [f"マージの反映の記録「{rec.reflection}」が、既定ブランチ（{ref}）の宣言（{value}）と違う"
                "——その周が足した・書き換えた宣言は効かない"]
    return []


def matches(path: str, pattern: str) -> bool:
    """`不在で止める範囲:` のパターンに当たるか（glob。`/` で終われば配下すべて。glob の文字が無ければ自身と配下）。"""
    if pattern.endswith("/"):
        return fnmatch.fnmatchcase(path, pattern + "*")
    if not any(c in pattern for c in "*?["):
        return path == pattern or path.startswith(pattern + "/")
    return fnmatch.fnmatchcase(path, pattern)


def read_stop_line(line: str) -> tuple[str, str | None]:
    """1 行を `("pattern", <パターン>)`・`("bad", <行>)`・`("skip", None)` に分ける（#1047 R1・J2）。

    行頭の飾りを外し、キーワードで始まらなければ skip。キーワードの直後（強調の閉じと空白を外して）が
    助詞なら散文で skip、コロン（全角も）で値があれば pattern、それ以外（`=`・空白とパス・行末・読点など）は bad。
    """
    s = line
    openers = []  # 外した強調の開き（`**`・`__`・`*`・`_`。リストの印 `* ` は含めない）
    while True:
        m = DECOR.match(s)
        if not m:
            break
        if m.group(0) in ("**", "__", "*", "_"):
            openers.append(m.group(0))
        s = s[m.end():]
    if not s.startswith(STOP_KEYWORD):
        return "skip", None
    rest = s[len(STOP_KEYWORD):].lstrip("*_ \t")
    if rest and rest[0] in PARTICLES:
        return "skip", None  # 散文（`不在で止める範囲は…`）
    if rest[:1] in COLONS:
        after = rest[1:]
        value = after.strip()
        mark = openers[-1] if openers else ""
        tail = after[len(mark):]
        # コロンの直後（空白なし）に同じ印があり、その後が空白・行末（`**` だけは値が続いてもよい）なら、開いた強調の閉じ
        if mark and after.startswith(mark) and (mark == "**" or tail == "" or tail[0].isspace()):
            value = tail.strip()  # 開いた強調の閉じがコロンの内側にあれば外す（`*…:* x`・`**…:**x`。#1148 F1）
        else:
            value = re.sub(r"^(\*\*|__)\s+", "", value).strip()  # 開きの無い `**` が値の前に空白つきである形（#1047 R1）
        if value:
            return "pattern", value
    return "bad", line.strip()


def stop_lines(text: str) -> tuple[list[str], list[str]]:
    """`.claude/dev-loop.md` の `不在で止める範囲:` のパターンと、宣言のつもりなのに形の読めない行（コードブロックと HTML コメントの外）。"""
    patterns, bad = [], []
    for l in visible(text):
        kind, v = read_stop_line(l)
        if kind == "pattern":
            patterns.append(v)
        elif kind == "bad":
            bad.append(v)
    return patterns, bad


def dev_loop_md_at(ctx: Context, rev: str) -> str:
    res = ctx.git("show", f"{rev}:.claude/dev-loop.md", ok=(0, 128))
    return res.stdout if res.returncode == 0 else ""


def rolled_back(ctx: Context) -> dict[str, str]:
    """既定ブランチで戻した（revert した）コミットが触ったファイル → そのコミット（`<SHA> <件名>`）。"""
    default = ctx.default_ref()
    out: dict[str, str] = {}
    for entry in ctx.git("log", "--format=%H%x00%B%x1e", default).stdout.split("\x1e"):
        if "\x00" not in entry:
            continue
        for m in REVERTS.finditer(entry.split("\x00", 1)[1]):
            full = ctx.resolve(m.group(1))
            if not full or not ctx.is_ancestor(full, default):
                continue  # 既定ブランチから辿れない——squash した PR の途中の revert
            parent = ctx.resolve(f"{full}^1")
            files = (ctx.git("diff", "--name-only", "--no-renames", parent, full) if parent else
                     ctx.git("diff-tree", "-r", "--root", "--no-commit-id", "--name-only", "--no-renames", full))
            subject = ctx.git("log", "-1", "--format=%s", full).stdout.strip()
            for f in files.stdout.splitlines():
                if f:
                    out.setdefault(f, f"{full[:12]} {subject}")
    return out


def check_risk(rec: Record, ctx: Context) -> list[str]:
    """影響範囲（#1047）——不在の周で、宣言した範囲・戻した履歴のある範囲に触れる差分を通さない。"""
    if not ctx.absent:
        return []
    default = ctx.default_ref()
    fork = ctx.git("merge-base", default, ctx.head).stdout.strip()
    files = [f for f in ctx.git("diff", "--name-only", "--no-renames", fork, ctx.head).stdout.splitlines()
             if f and f != ctx.plan_rel]
    patterns, bad = stop_lines(default_dev_loop_md(ctx))
    rolled = rolled_back(ctx) if files else {}
    reasons = []
    for l in bad:
        reasons.append(f"影響範囲: 既定ブランチ（{default}）の行「{l}」が `不在で止める範囲: <パターン>` の形で読めない"
                       "——読めない宣言は止まる側に倒す")
    if patterns:
        paths = set(ctx.git("ls-tree", "-r", "--name-only", default).stdout.splitlines()) | set(files)
        for pat in patterns:
            if not any(matches(f, pat) for f in paths):
                reasons.append(f"影響範囲: 既定ブランチ（{default}）の宣言「不在で止める範囲: {pat}」が、既定ブランチの木と周の差分の"
                               "どのパスにも当たらない（読めない宣言）——黙って何にも当たらない宣言にせず、止まる側に倒す")
    kept = set(stop_lines(dev_loop_md_at(ctx, ctx.head))[0])
    at_fork = set(stop_lines(dev_loop_md_at(ctx, fork))[0])
    for pat in patterns:
        if pat in at_fork and pat not in kept:
            reasons.append(f"影響範囲: 周の差分が既定ブランチの宣言「不在で止める範囲: {pat}」を外す"
                           "——止まる範囲を外す変更は利用者が居る周でマージする")
    for f in files:
        hit = next((p for p in patterns if matches(f, p)), None)
        if hit:
            reasons.append(f"影響範囲: {f} が既定ブランチ（{default}）の宣言「不在で止める範囲: {hit}」に当たる"
                           "——不在の周ではマージせず、PR で止めて利用者に回す")
        if f in rolled:
            reasons.append(f"影響範囲: {f} は既定ブランチで戻した（revert した）コミット {rolled[f]} が触ったファイル"
                           "——不在の周ではマージせず、PR で止めて利用者に回す")
    return reasons


CHECKS = (check_passes, check_coverage, check_criteria, check_reflection, check_risk)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"引数の誤り: {message}", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str]) -> int:
    p = Parser(description="計画ファイルの関門の記録を、リポジトリの履歴と照合する。")
    p.add_argument("plan", help="計画ファイル")
    p.add_argument("--head", default="HEAD", help="照合する先端（既定は HEAD）")
    p.add_argument("--absent", action="store_true", help="不在の周のマージとして照合する")
    a = p.parse_args(argv)
    plan = Path(a.plan)
    try:
        text = plan.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"**判定できなかった**: 計画ファイルを読めない: {e}", file=sys.stderr)
        return 7
    try:
        rec = parse(text)
    except Malformed as e:
        print(f"**記録の形が違う**: {e}（形は check-gates.py の docstring の「記録の形」）", file=sys.stderr)
        return 2
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(plan.resolve().parent),
                             capture_output=True, text=True)
        if top.returncode != 0:
            raise Undetermined(f"計画ファイルが git の作業ツリーの中に無い: {top.stderr.strip()}")
        top_path = Path(top.stdout.strip())
        ctx = Context(top=top_path, plan_rel=plan.resolve().relative_to(top_path.resolve()).as_posix(),
                      head="", absent=a.absent)
        head = ctx.resolve(a.head)
        if not head:
            raise Undetermined(f"--head {a.head} が解決しない")
        ctx.head = head
        reasons = [r for check in CHECKS for r in check(rec, ctx)]
    except (Undetermined, OSError, ValueError) as e:
        print(f"**判定できなかった**: {e}", file=sys.stderr)
        return 7
    if reasons:
        print(f"**照合を通らない**（head {ctx.head[:12]}）:", file=sys.stderr)
        for r in reasons:
            print(f"  - {r}", file=sys.stderr)
        return 3
    blocked = [f"{i}（{v}・判断={j}）" for i, (v, j) in rec.criteria.items() if v in ("BLOCKED", "満たさない")]
    unproven = [i for i, (v, _) in rec.criteria.items() if v == "未証明"]
    print(f"照合を通った（head {ctx.head[:12]}・受入基準 {len(rec.criteria)} 件）。")
    if blocked:
        print(f"  判断の記録で通した受入基準: {'、'.join(blocked)}")
    if unproven:
        print(f"  未証明（PR コメントで人間のレビューに回す）: {'、'.join(unproven)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
