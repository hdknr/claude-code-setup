# Issue #946 — test-check-all.py: ワークフローの on: を見ず、PR で起動しなくしても素通しする

不在の周（cruise の子）。出所: `/dev-loop:cruise 947 --absent` の起動（2026-11-10）。親 Issue #947、台帳 `issue-947`（台帳は親だけが書く）。
従う版は dev-loop 1.99.0（キャッシュ。`SKILL.md` 1861 行——`wc -l`）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-947`）——利用者の確認（起動時・2026-11-10T08:57:23Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-947`））
- 版の上げ方: **上げない**——`plugins/` を触らない（`scripts/test-check-all.py` と計画だけ。`check-version-bump.py` の対象外）。マージ直前の取り込みでも版の行は出ない
- PR は `Fixes #946`（`Refs #931 #942`）。確認の Issue #949 は指さない。手順 7 のマージは親がする（子は PR と PR 側の CI まで）

## 周の在り処

- ブランチ: `issue/946-workflow-on`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-946`
- 起点コミット: `718ca43e`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `718ca43e96d3a3625a8f18819f124a8ddc55607c`

## 変更範囲

触る:
- `scripts/test-check-all.py` — ワークフローの `on:` を読む `trigger_reasons` を足し、収録漏れの検査（`--part registry`）に「無条件の `run:` が PR と main への push で起動するワークフローにあるか」の検査を足す。試料（`SAMPLE_ON`）・契約（`scan_contract`）・判別の変異（`SCAN_MUTANTS`）・実物の `plugins.yml` への `mutation-claim`・docstring の守る／守らないを直す
- `docs/plans/issue-946.md` — この計画

触らない:
- `.github/workflows/*.yml`——書き方は変えない（`plugins.yml`・`docs.yml` は `pull_request:` と `push: branches: [main]` で起動する。`release.yml` は `workflow_dispatch` だけだが、収録したスクリプトを回していない）
- `CLAUDE.md`——`test-check-all.py` の行は条件を docstring に任せていて、`on:` に触れていない（`grep` で確かめる）
- `check-all.py`

複製の数（同じことを述べている箇所）: `on:` を見ないことを述べるのは `test-check-all.py` の中だけ——モジュールの docstring の守らない（`on:` の項）・`gated_runs` の docstring の守らない。1 ファイルの中なので分けない。

## 決めた範囲（受入基準 1 の「どこまで読むか」）

**`on:` の鍵（イベント名）と、`pull_request`・`push` の下の鍵まで読み、値は `branches:` だけ読む。** 推奨で決めた（仕様の穴ではない——Issue が「周の中で決め、docstring に書く」と委ねている）。

- 要るもの: `pull_request` と `push` の両方。`push` は `branches:` に `main` を（文字どおり）含むこと。`pull_request` に `branches:` があれば同じく `main` を含むこと
- 赤にするもの: `on:` が無い・`pull_request` か `push` が無い（`workflow_dispatch` だけ・スカラーの `on: push` など）・`branches:` に `main` が無い（`push` に `branches:` が無く `tags:` だけの形を含む——`push` の下に `branches:` 以外の鍵があれば赤）・**`branches:` 以外の鍵**（`paths:`・`paths-ignore:`・`branches-ignore:`・`types:`・`tags:` など）・フロー形式のマッピング（`on: {…}`・`push: {…}`。読まない）
- 理由: 値まで読む（`paths:` が今の変更に当たるか、`types:` に `synchronize` が入るか、glob が `main` に当たるか）のは GitHub の照合規則の写しになり、外すと黙って緑になる向きの誤りを作る。鍵の有無で赤にすれば、外す向きは**偽の赤**（`types: [opened, synchronize, reopened]` を書いた・`branches: ['**']` と書いた、など）だけになる
- `push` を要る側にするのは、Issue の受入基準 1 が「PR（と main への push）」と書いているため。今の 2 つの yml は両方持つ

## デプロイ経路

`CI の歯止め`——main へのマージで次の PR・push から効く。`plugins/` を触らないので、プラグインの配布は起きない（GitHub Pages の再ビルドは起きるが、計画ファイルのページが 1 枚足されるだけ）。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **収録したスクリプトの無条件の位置の `run:`（と、回帰テストの無条件・引数なしの `run:`）が、PR と main への push で起動するワークフローに 1 つも無ければ `--part registry` が赤。**
   経路（入口は `.github/workflows/*.yml` の `on:` に人が書きうる書き方）:
   (a) `on:` を消す、(b) `pull_request:` を消す（`push` だけ）、(c) `push:` を消す、(d) `workflow_dispatch` だけにする、
   (e) `paths:`・`paths-ignore:` を足す、(f) `branches:` を `main` を含まない値に変える・`branches-ignore:` を足す、(g) `types:` を足す、
   (h) `push` を `tags:` だけにする、(i) スカラー `on: push`・フロー列 `on: [push]`、(j) フロー形式のマッピング、
   (k) 全部を回す行だけ起動しないワークフローに置き、起動するワークフローでは狭める（#945 の組と同じ形のファイル版）。
   陽性: (l) ブロックのマッピング・ブロックの列・フロー列 `[pull_request, push]`・`branches: [main]`・`branches:` の下の `- main`（コンパクトな列も）・引用符つきの `"on":` を「起動する」と読む。
   守り方: `trigger_reasons`（1 ファイルの `on:` から起動しない理由を返す）で起動するファイルだけを繋いだ文字列を作り、`gated_runs`・`full_ungated_runs` を全体と起動する側とで比べる。
2. **陽性対照: 今の 3 つの yml で `--part registry` が緑のまま。**
3. **試料と変異**: (a)〜(l) の試料を持ち、判定を戻す変異が `--part scan` で赤になる。実物の `plugins.yml` の `on:` を変える `mutation-claim`（`pull_request:` を消す・`paths:` を足す）が `--part registry` で赤になる。
4. **docstring**: モジュールの守る／守らない・`gated_runs` の docstring が決めた範囲（上の節）と合う。
5. **既存の判別を壊さない**: 既存の契約（`--part scan`）と既存の `mutation-claim` が緑のまま。
6. `python3 scripts/check-all.py` が緑（run-serial 越し）で、PR 側の CI も全部緑。

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）に渡す——4 つの受け渡し（2 パス目が該当なしなら 2 つ）。

検証で証明できるもの: 1〜6。

未証明: なし（行を読む判定で、GitHub の実物の起動には寄りかからない——「GitHub が実際に起動するか」は主張しない）。

生成物: なし（`skill-metrics.py` の対象の `SKILL.md`・図の書き出しを触らない）。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目: Verifier（`dev-loop:dev-loop-verifier`、sonnet）と `/code-review`（high）に受入基準 1〜6・既知の限界を渡した。起点 `e2407ac7`（1 パス目の関門に渡した時点の HEAD）
  - Verifier: 反証 0 件（軽微 1 件——タブで字下げした子が緑になり、docstring の「偽の赤」と食い違う）。mutation-claim 51 件を退避して当て全部赤。`git status --porcelain` の差は親の計画のコミット（`ee94eded`）だけ
  - `/code-review`: 指摘 8 件——採否は下の表。差し戻し: あり（手順 4 で直した。`6cd5a64c`）
- 1 パス目の指摘対応: `6cd5a64c`（`git diff e2407ac7` は計画を除いて `scripts/test-check-all.py` 1 ファイル +91/−21——0 行ではないので 2 パス目を回す）
- 割り目（手順 6）: 割らない（cruise の周）。残っているのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方
- 2 パス目: Verifier（sonnet）と `/code-review`（high）に受入基準 1〜6・既知の限界（1 パス目の採否の表を含む）を渡した
  - Verifier: 反証 0 件（軽微 1 件——`branches:` の下の深い行・継続行を読み飛ばし、docstring の「残るのは `concurrency:` だけ」が偽）。`check-all.py` は順番待ちで未完走（自分で止めた）
  - `/code-review`: 指摘 6 件——採否は下の表
- 狭いパス: 起点 `f554ac06`（2 パス目の指摘対応を始める直前の HEAD。前に `0341ef76` と書いたが、その後に計画だけのコミット `f554ac06` を足したので、直前の HEAD はこちら）・終点 `f4b638cf`（指摘対応のコミット）。別ティアの Verifier に当てる
- ローカルの `check-all.py`: 1 パス目の指摘対応の後（`6cd5a64c`）で 70/70 緑
- 実験: 実物の 3 つの yml に `trigger_reasons` を当てた——`docs.yml`・`plugins.yml` は空、`release.yml` は `pull_request`・`push` で起動しない（収録したスクリプトを回していないので赤にならない）。陽性対照は `mutation-claim`（`plugins.yml` の `pull_request:` を外す・`paths:` を足す）で、両関門が退避した複製で赤を確かめた

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `on:` の値（`paths:` の glob・`types:` の中身・`branches:` の glob）は読まず、鍵があれば赤 | 採った | 上の「決めた範囲」。外す向きは偽の赤だけ |
| `push` も要る側にする | 採った | Issue の受入基準 1 の「PR（と main への push）」 |
| 起動しない理由はファイル単位で出す（ジョブ単位の `if:` の理由とは別の検査の行） | 採った | 直し方が別（`on:` を直す） |

### 1 パス目の指摘の採否（Verifier 1 件・`/code-review` 8 件）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 | 振り分け（found-lines） |
| --- | --- | --- | --- | --- |
| V1: タブで字下げした子（`\tbranches: [dev]`）が緑。docstring は「タブで始まる行」を偽の赤に分類 | 示せる（Verifier の probe・自分で再現） | 4（docstring が実装と食い違う） | 直す（タブで字下げした行はファイルのどこでも赤） | 直す（この周の後退ではないが、この周が書いた誤り）。仕様の穴ではない |
| CR1: `branches:` の `!` の除外（`[main, '!main']`）が緑 | 示せる（レビューの probe。`--part registry` が rc=0） | 1・4（「偽の赤だけ」が偽） | 直す（`!` で始まる項があれば赤） | 直す。仕様の穴ではない（決めた範囲は「外れる向きは偽の赤だけ」） |
| CR2: 重なるイベント・値と子が両方・列とマッピングの混在・重なる `branches:` を起動すると読む | 示せる（`trigger_reasons` が空を返す。GitHub がどう扱うかは確かめていない） | 4（「偽の赤だけ」） | 直す（どれも赤） | 直す |
| CR3: モジュールの docstring の「黙って素通しする向き」が不完全で、重なりの読み方も誤り | 示せる（docstring と実装） | 4 | 直す（docstring を直した。残るのは `concurrency:` だけ） | 直す |
| CR4: イベントの下の浅い行を黙って飛ばす | 示せる（probe） | 4 | 直す（赤） | 直す |
| CR5: 列の項の下の行・フロー列の `{x: 1}` を起動すると読む | 示せる（probe） | 4 | 直す（赤） | 直す |
| CR6: 直し方の案内が (k) の形でも「`on:` を直せ」だけ。名前はコメントの中からも拾う | 示せる（出力の文言） | 無し | 直す（直す線は既定だが、利用者に見える誤りでこの周が足した文言——案内に「行を起動するワークフローに移す」を足し、名前は無条件の `run:` から拾う） | 直す（利用者に見える誤り） |
| CR7: `trigger_reasons` が `gate_records` の行の読み方を写している | 示せない（設計の提案） | 無し | 残課題 | 捨てる |
| CR8: `gated_runs`・`trigger_reasons` を 2 度計算する | 示せない（遅さの実測なし） | 無し | 残課題 | 捨てる |

### 2 パス目の指摘の採否（Verifier 1 件・`/code-review` 6 件）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 | 振り分け（found-lines） |
| --- | --- | --- | --- | --- |
| V2-1: `branches:` の下の深い行・継続行（`branches: main` の次の深い `dev`）を読み飛ばす。docstring の「残るのは `concurrency:` だけ」が偽 | 示せる（Verifier の probe） | 1・4 | 直す（`f4b638cf`） | 直す（この周の後退ではない——前は `on:` を読まなかった）。仕様の穴ではない |
| CR2-1: `branches: dev` の下の深い `- main`（`dev - main`）・継続行・項の下の深い `- main` を `main` と読む | 示せる（複製の `plugins.yml` で `--part registry` rc=0） | 1 | 直す（値が空の `branches:` の後ろに 1 つの字下げで並ぶ `- <スカラー>` だけを受け取る一般則にした） | 直す |
| CR2-2: `branches:` の下の YAML として読めない形（項の下の `paths:`・フロー列の後ろの `- main`）を起動すると読む | 示せる（PyYAML の ParserError・`trigger_reasons` が空） | 4（「読めない形は赤」） | 直す（同上） | 直す |
| CR2-3: docstring の「残るのは `concurrency:` だけ」「読めない形はどれも赤」が偽 | 示せる（上の 2 件） | 4 | 直す（実装を直し、docstring に `branches:` の下の行を足した） | 直す |
| CR2-4: `SCAN_MUTANTS` の「列の項の下の行を飛ばす」が契約ではなく `KeyError` で捕まる | 示せる（1 件ずつ当てた結果） | 3（判定を戻す変異が赤になる——理由の違う殺し方は判別を示さない） | 直す（理由を足す行を `pass` にする変異に替えた。#946 の変異 35 件を 1 件ずつ当て、全部が契約の行で捕まり例外は 0 件） | 直す |
| CR2-5: コメントの「上で赤の名前は重ねて出さない」が #945 の行と重なる形で偽 | 示せる（probe） | 無し | 残課題 | 記録だけ（実際の利用でまず起きない形——無条件のジョブで狭め、全部を回す行を条件つきのジョブと起動しないファイルの両方に置く。同じ名前が 2 行に出るだけで赤は変わらない） |
| CR2-6: 手書きの読み方に特例を足し続けている（一般則にせよ） | 示せない（設計の提案） | 無し | 残課題（`branches:` の段は CR2-1 の直しで一般則にした） | 捨てる |

## 手順 8（起票と学び）

- この周の起票: 0 件（不在の cruise の周——起票の候補は振り分けで直すの行だけで、いまは無い）
