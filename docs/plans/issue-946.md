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
- 1 パス目: 未着手
- 実験: 未着手

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `on:` の値（`paths:` の glob・`types:` の中身・`branches:` の glob）は読まず、鍵があれば赤 | 採った | 上の「決めた範囲」。外す向きは偽の赤だけ |
| `push` も要る側にする | 採った | Issue の受入基準 1 の「PR（と main への push）」 |
| 起動しない理由はファイル単位で出す（ジョブ単位の `if:` の理由とは別の検査の行） | 採った | 直し方が別（`on:` を直す） |

## 手順 8（起票と学び）

- この周の起票: 0 件（不在の cruise の周——起票の候補は振り分けで直すの行だけで、いまは無い）
