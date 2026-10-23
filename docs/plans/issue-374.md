# Issue #374 — proposal が暫定の回答を見分け、仕様書も一緒に作る（#366・#371 のまとめ）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/build-proposal.py` — 暫定の節（A）・仕様書の生成（C）・`--pptx`（D）・古い出力の消し方
- `plugins/spec-loop/scripts/check-qa-csv.py` — 暫定の回答の判定 `is_provisional`（1 か所だけに置く。#353 と同じ形）
- `plugins/spec-loop/scripts/qa-to-pptx.py` — Markdown をスライドにする関数（提案書・仕様書の PPTX。同じ仕組み）
- `plugins/spec-loop/references/qa-csv.md` — 暫定の回答の判別（原本）
- `plugins/spec-loop/references/tree.md` — 仕様書・PPTX・図の置き場所、仕様書の手書き部分の置き場所、提案書から仕様書への参照
- `plugins/spec-loop/skills/proposal/SKILL.md` — 手書き部分の指示（B）・手順 3・4・frontmatter
- `plugins/spec-loop/README.md` — proposal の節とスクリプトの使い方
- `scripts/test-build-proposal.py` — 回帰テスト（E）
- `scripts/test-check-qa-csv.py` — `is_provisional` の印が `qa-csv.md` と一致すること
- `CLAUDE.md` — `build-proposal.py` の行
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版（minor: 0.21.1 → 0.22.0）と description
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-374.md` — この計画

触らない:

- `check-signoff.py`（照合の 3 は `暫定反映` だけで決める。`反映済み` に「暫定で採用」と書いた行は照合を止めない——止めると A の節が空にしかならない）
- `qa-to-pptx.py` のレビュー会の資料の載せ方（`反映済み`＋「暫定で採用」の行はレビュー会に載らない）——残課題
- `check-spec-exit.py`・`scaffold.py`
- `#268`（drawio の決まり）そのもの

### 同じことを述べている箇所の数

- 暫定の判別: `qa-csv.md`（原本）・`check-qa-csv.py`（実装 1 か所）・SKILL 手順 2/3・`build-proposal.py` docstring の **4 箇所**
- 仕様書の中身と置き場所: `tree.md`（原本）・SKILL 手順 3/4・README・`build-proposal.py` docstring・CLAUDE.md の **5 箇所**
- **分けない理由**: Issue が同じ決まり（承認したタグの時点から作る・照合が通らなければ作らない）の上に載る 2 件をまとめた。原本を `qa-csv.md` と `tree.md` に置き、ほかは指すだけにする。

## 乗るデプロイ経路

main へのマージ。プラグインは利用者の `plugin update` で届く（サイトのページは触らない）。

## 設計の決定（関門に渡す）

- **D1 暫定の行 = `状態` が `暫定反映`、または `状態` が `反映済み` で `回答` に「暫定で採用」を含む行。**
  `暫定反映` の行は照合の 3 で止まるので、提案書に載りうるのは実際には後者（#366 の実データの形）。
  `確認中` の行は「暫定で採用」と書いてあっても未決定（反映していない）。推奨（#339）は回答ではないので判別に使わない。
  内部の表は提案書に載らない（今のまま）。**判別は 1 か所（`check-qa-csv.py` の `is_provisional`）**。
- **D2 暫定の行は「主な決定事項」から外し、「利用者にまだ確かめていない決定（N 件）」の節に載せる。0 件でも節を出す**（無いことも決裁者の材料）。
  載せるのは**その版の `qa.csv`**（主な決定事項と同じ範囲）。前の版の暫定の行は載せない——既知の限界。
- **D3 仕様書 `spec.md` は提案書と同じ場所に、同じ実行で作る。** 材料は `signoff/v<n>/req-<k>` の時点の v1〜v<n> を重ねた全体（v1 もこの経路——
  重ね合わせの決まりの違反は v1 でも 1）と、作業ツリーの `docs/v<n>/proposal/spec/*.md`（手書き。任意。提案書の手書き部分には入らない）。
  節: 手書き部分・規模・構成の図・機能の一覧（中間表現があれば）・決定表・範囲の外（`spec/scope.md` の「範囲の外」の節）・v2 以降は前の版からの変更・ファイルの一覧。
  画面の一覧・試作で確かめること・要約は一意に決まらないので手書き。
- **D4 図は `spec/`・`requirements/` の `.svg` を `spec-figure-NN.svg` として写して載せる。`.svg` を持たない `.drawio` は「書き出しが無いので載せていない」と書く。**
  draw.io を起動しない（`.drawio.svg` はそのまま SVG）。PPTX には図を載せず、載せていないことをスライドに書く（標準ライブラリで SVG を埋めない）。
- **D5 `--pptx` を渡すと `proposal.pptx`（出力の名前の拡張子違い）と `spec.pptx` も作る。** Markdown の `## ` ごとに 1 枚（長ければ分ける）。
- **D6 作る前に古い出力（提案書・ガント・仕様書・PPTX 2 つ・`spec-figure-*.svg`）を全部消し、全部作れてから書く。**

## verify の受入基準

不変条件 × 経路:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | 暫定の行は主な決定事項に載らず、暫定の節に載る | v1・v2 の `qa.csv`／承認後に作業ツリーで直した `回答` | `is_provisional` で分ける・タグの時点の表を読む |
| 2 | 暫定でない行は暫定の節に載らない（陽性対照） | `確認中`＋「暫定で採用」／確定の書き方の `反映済み` | 判定は `反映済み` に限る |
| 3 | 暫定の判別は 1 か所で、`qa-csv.md` の印と同じ | 写しを作る | `test-check-qa-csv.py` が印を突き合わせる |
| 4 | 仕様書はタグの時点の中身から作る | 作業ツリーの直し／req と budget の間の直し／前の版 | `compare_at` の写しから重ねる |
| 5 | 照合が通らない・材料が決まりに反すると、仕様書も PPTX も図も書かない（古いものは消す） | 1・2・3 の各終了／git 不在 | 全部作れてから書く・最初に消す |
| 6 | 仕様書に規模・図・機能・決定表・範囲の外・（v2）変更・手書きが載る | 図の無い `.drawio`／範囲の文書が無い／中間表現が無い | 無いことを本文に書く |
| 7 | PPTX は同じ入力から同じバイト・部品が揃い XML が整形式・図を載せないと書く | `--pptx` の有無 | `qa-to-pptx.py` の `package`・`write` を使う |
| 8 | SKILL.md の手書き部分の指示に B の 2 点がある・その事実が正しい | — | 文面 |
| 9 | 版が 3 種類で揃う・`check-all.py` が緑 | — | CI |
| 10 | 各判定を外す変異で赤になる | — | `MUTATIONS` |

規定の掛け算: 受入基準 × {Verifier, `/code-review`} × {1 パス目, 2 パス目}。

**この環境では証明できないもの（未証明）**: PPTX が PowerPoint・Keynote で開けて読めること（CI にも手元にも入れていない。見るのは部品と XML の整形式まで）。見た目。

**生成物**: このリポジトリの生成物（図の書き出し・§8.2 の測定値）は触らない——`check-all.py` の鮮度検査で確かめる。PPTX・仕様書は正本リポジトリ側の生成物で commit しない。

## 未解決の判断・確認待ち

- なし（D1〜D6 は著者が決めた。関門に渡す）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/374-proposal-provisional-spec`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-374`・起点 `eab8581`・base 参照 `origin/main` = `eab8581b1f0d687b98e5552e9053df8570470c97`
- 実装: 着手
- 関門: 未
- 交絡: 実験なし

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 前の版の暫定の行 | 載せない | 主な決定事項と同じ範囲（その版の `qa.csv`）に揃える |
| レビュー会の資料が `反映済み`＋「暫定で採用」を載せない | 残課題 | req-loop の話で、この Issue の受入基準の外 |
| PPTX に図を載せない | 採った | 標準ライブラリだけで SVG を PPTX に埋められない。載せていないことを書く |
