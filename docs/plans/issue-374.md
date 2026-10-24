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
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（minor: 0.21.1 → 0.22.0。main が #361 で先に 0.22.0 に達したので、取り込んで 0.23.0 に上げた）と description
- `.claude-plugin/marketplace.json` — 同上
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

- 周の在り処: ブランチ `issue/374-proposal-provisional-spec`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-374`・起点 `eab8581`・base 参照 `origin/main`。
  切った時点の base は `eab8581b1f0d687b98e5552e9053df8570470c97`。**main（#361）を取り込んだので式を当て直した: `git merge-base origin/main HEAD` = `fdcf631bcc50b87bd40c0e3eb1826ab0f850414e`**——関門にはこれを渡す
- 実装: 済み（`60006cc`・取り込み `26fc08e`）。`check-all.py` 44/44 緑・PR 限定の 3 本（変更範囲・description・版）も緑
- 関門 1 パス目: **Verifier（dev-loop:dev-loop-verifier・sonnet）反証 2 件**（どちらも一時リポジトリで再現済み）／**`/code-review`（base `fdcf631`）指摘 9 件**。どちらも `test-build-proposal.py`（51 試料・58 変異）・`test-check-qa-csv.py`（60・47）・鮮度 2 本が緑と報告。`check-all.py` は関門側では回していない
- 1 パス目の指摘対応: 直す 4 件（V1/CR5・CR1・CR2・CR4）。`test-build-proposal.py` 53 試料・63 変異、`test-check-qa-csv.py` 60・47 で緑
- 指摘対応のコミット: `b0d48af`（`check-all.py` 44/44 緑）。**2 パス目の狭いパスの起点は、2 パス目の指摘対応を始める直前の HEAD を、指摘対応に入る前にここへ書く**
- 2 パス目の前の割り目: 提案した（AskUserQuestion）→ **「ここで割る」が選ばれた**（2026-10-24）
- **次にやること**: 手順 5 の当て直し（Verifier）と手順 6 の 2 パス目（`/code-review`）の**両方**。base は同じ `fdcf631bcc50b87bd40c0e3eb1826ab0f850414e`。1 パス目の指摘対応（下の表の「直す」4 件）を重点に。渡す文面は前回の委譲文に 2 パス目の差し込みを足す
- 手順 4 の割り目: 提案した（AskUserQuestion）→ **「ここで割る」が選ばれた**。再開は手順 5 の 1 パス目から
- 交絡: 実験なし（出力の目視は生成物を読んだだけ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 前の版の暫定の行 | 載せない | 主な決定事項と同じ範囲（その版の `qa.csv`）に揃える |
| レビュー会の資料が `反映済み`＋「暫定で採用」を載せない | 残課題 | req-loop の話で、この Issue の受入基準の外 |
| PPTX に図を載せない | 採った | 標準ライブラリだけで SVG を PPTX に埋められない。載せていないことを書く |
| 仕様書の規模の暫定の数（v1〜v<n>）と提案書の暫定の節（その版）が食い違いうる | 残す | D2 で提案書は主な決定事項と同じ範囲に揃えた。仕様書は重ねた全体を数える（1 パス目 CR9） |
| v1 でも重ね合わせを通す | 採った | D3（1 パス目 CR7） |

### 1 パス目の指摘

| # | 出所 | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- | --- |
| V1 / CR5 | 両方 | `is_provisional` が部分一致で「暫定で採用しない」「暫定で採用していた A を取り下げ」を暫定に数える | 示せる（Verifier が再現。修正前の形の変異「活用の続く書き方も暫定にする」が新しい試料で赤） | 2 | **直す**——後に活用が続く書き方を数えない（`PROVISIONAL_MARK`。`qa-csv.md` に明記） |
| V2 | Verifier | `--out` を任意の場所に向けると同じ場所の手書きの `spec.md`・`<stem>.pptx`・`spec-figure-*.svg` を消す | 示せる（Verifier が再現） | 無し（不変条件 5 は「古い出力を消す」を求めており、手書きとの同居は基準の外） | 残課題 |
| CR1 | code-review | 提案書の PPTX のガントの注記が「Markdown の仕様書で見る」と、ガントの無い文書を指す | 示せる（`--pptx` の提案書の PPTX の文字列） | 7 | **直す**——注記は元の Markdown（`proposal.md`／`spec.md`）を名指す |
| CR2 | code-review | `--out` の stem が `spec`（`spec.html` 等）・大文字違いだと出力が衝突する | 示せる（`Spec.html --pptx` の試料が修正前の形の変異で赤） | 5・7（終了 0 で提案書の PPTX が無い） | **直す**——PPTX の名前と大文字小文字も照らす |
| CR3 | code-review | `out_of_scope` が「範囲の外」を含む最初の見出しを拾う | 示せない（`spec-scope.md` の節は 線・原則・範囲の外 で、題に「範囲の外」を含む実物は無い） | 6 | 残課題 |
| CR4 | code-review | `figures_of` が `shared/` の図も拾う（D4・`tree.md` は `spec/`・`requirements/`） | 示せる（`shared/chart.svg` を足した試料が修正前の形の変異で赤） | 6 | **直す**——`FIGURE_DIRS` で絞る |
| CR6 | code-review | 書き込みが途中で失敗すると一部だけ残り、traceback で終わる | 示せない（`spec.md` という名のディレクトリなど、作り物の配置でしか起きない） | 5 | 残課題 |
| CR7 | code-review | v1 でも重ね合わせを通すので、v1 の重ね合わせの問題で提案書まで止まる | — | 無し（D3 で決めたとおり） | 決着済み（D3） |
| CR8 | code-review | `markdown_slides` で裸の `>` 行が空の段落になり行数の枠を食う | 示せない（見た目だけ。未証明の「見た目」） | 無し | 残課題 |
| CR9 | code-review | 仕様書の暫定の数（v1〜vn）と提案書の暫定の節（その版だけ）が食い違いうる | 示せない（D2 の決めたとおりの帰結） | 無し（D2） | 残課題（既知の限界に足す） |
