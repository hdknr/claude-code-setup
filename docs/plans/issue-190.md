# #190 — dev-loop の Eval: 陽性対照をリポジトリに置き、人間が別端末で回す実行と要約を 1 コマンドにする

## 周の在り処

- ブランチ: `issue/190-eval-runner`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-190`
  （`prepare-worktree.sh` で作り、`EnterWorktree` に `path` で入った。セッションは issue-183 の worktree から移った）
- 起点: `4c291f5`（Merge pull request #186）
- base: 参照 `origin/main` → `4c291f54539db4ada20d6271b2e1e0c57a332f4a`
- 読み込まれた dev-loop は **1.35.0**（リポジトリは 1.36.1）

## 0. 設計の判断

- **対照の定義は `scripts/` に置き、実行時に本物のケースから組む。** `plugins/dev-loop/evals/` の下に対照のケースを
  置くと、(1) grader と scaffold の**複製**ができて片方だけ古くなる、(2) ハーネスは `<eval dir>/**/case.yaml` を
  全部ケースとして拾う（2.1.291 のバイナリの `plugin eval` の説明文）ので、本物のケースの実行に対照が混ざる、
  (3) `plugins/` の中身を変えると版の bump が 3 箇所に要る。実行スクリプトがプラグインを**リポジトリの外の一時領域に
  複製**し、その複製の `evals/` に対照を組んで 1 回で回せば、どれも起きない
- **対照は「本物のケースの `case.yaml` の `name` と `prompt` だけを差し替えたもの」**に限る。差し替える行が
  ちょうど 1 つずつ見つからなければ組まずに止まる（#183 の `build-control.py` と同じ形）
- **要約は trace から作る**（`aggregate-result.json` の `tracePath`）。合否と期待の一致、子の Bash のコマンド、
  その出力から**既知の雑音を除いた**行。**`--keep-temp` を必ず付ける**——付けないと trace が残らない

## 1. 変更範囲

触る:

- `scripts/run-dev-loop-evals.py` — 実行と要約（**CI からは呼ばない**）
- `scripts/test-run-dev-loop-evals.py` — 上の回帰テスト（変異テストを含む）
- `scripts/check-all.py` — テストを登録
- `.github/workflows/plugins.yml` — テストを CI のステップに
- `CLAUDE.md` — `scripts/` の一覧と「振る舞いを Eval で当てる」の回し方
- `docs/plans/issue-190.md` — この計画

触らない: `plugins/`（ケース・scaffold・版。**対照は複製の中にしか作らない**）、
`docs/plans/issue-183.md`（その周の記録）

**同じことを述べている箇所の数**: 対照の定義は `run-dev-loop-evals.py` の 1 箇所。回し方は `CLAUDE.md` の 1 箇所
（スクリプトの docstring は使い方を持つが、`CLAUDE.md` は指すだけにする）。分ける理由は無い。

## 2. デプロイ経路

`CLAUDE.md` と `scripts/` の変更で、公開サイト（`docs/`）は計画ファイルだけ。プラグインの版は動かない。
main へのマージで `docs.yml` がサイトをデプロイする（計画ファイルが載るかに依らず、内容は記録）。

## 3. 受入基準

不変条件:

- **I1** 対照は本物のケースの grader・scaffold・設定を**そのまま**使い、違うのは `name` と `prompt` だけ
- **I2** リポジトリの中のファイルを 1 つも作らない・変えない（`results/` も含む）
- **I3** 要約は「期待と違った」と「判定できなかった」を緑にしない（終了コードと表示の両方）
- **I4** 要約は赤・緑の理由を trace の行で示し、既知の雑音（`xcrun` の cache）を失敗の印と読まない

破りうる経路:

| 不変条件 | 経路 | 守り方 |
| --- | --- | --- |
| I1 | 本物のケースの `case.yaml` が変わる（grader を足す・`prompt` の行の形が変わる） | 組むたびに本物から写す。差し替える行が 1 つずつでなければ止まる |
| I1 | 対照の定義側に grader を書き足す | 定義は `name`・`prompt`・期待だけを持つ形にし、grader を持たせない |
| I2 | プラグインの下に対照を書く／`results/` が repo に出来る | 複製をリポジトリの外の一時領域に作り、eval はその複製に当てる |
| I2 | `--keep-temp` の一時領域 | `/private/tmp/e-*`（ハーネスが作る。リポジトリの外） |
| I3 | `aggregate-result.json` が無い・trace が無い・ケースが報告に無い | 「判定できなかった」として非ゼロ（期待違いとは別のコード） |
| I3 | 期待と違う grader がある | 非ゼロ |
| I3 | 本物のケースが緑でも、Bash を 1 回も呼ばずに止まった | 要約に「Bash 0 回」を出す（**緑のまま。理由は「既知の限界」**） |
| I4 | 子の出力が雑音だけ | 雑音の行を除いて「（雑音のみ）」と出す |
| I4 | 子の `git` が `can't exec` | 「測定不成立の候補」として目立たせる（#181 の実測） |

| # | 受入基準 | 証明手段 |
| --- | --- | --- |
| A | `--dry-run` で組んだ複製の対照が、本物のケースと `name`・`prompt` 以外で一致する（I1）。リポジトリの `git status` が変わらない（I2） | テスト・手元で実行 |
| B | 要約が、#183 の実データ（`/private/tmp/e-LqmttA`・`/private/tmp/e-iAcqg0`）で期待どおりの表を出す（A は狙いの 2 本が赤＝期待どおり、B は 3/3） | 手元で `--summarize` |
| C | 期待違い・判定不能で非ゼロ（I3）、雑音を除き `can't exec` を目立たせる（I4） | テスト（試料の trace） |
| D | テストの変異（各守り方を外す）で赤になる | テストに埋め込む |
| E | **1 コマンドで本物のケースと対照の両方が回り、貼れる要約が出る** | 人間が別の端末で 1 回回す（**このセッションからは起動できない**） |
| F | `check-all.py` が緑、PR 側の CI も緑 | `check-all.py`・`gh pr checks` |

**E は BLOCKED**——**何が無いか: 道具**（worktree 隔離セッションのガードが `claude plugin eval` を拒否する。#181）。
人間が別の端末で回せば消える。費用はおよそ $1.5。

**未証明**: なし（E 以外は手元で当たる）。

生成物: **なし**（`skill-metrics.py` の対象 `SKILL.md` は触らない。図も触らない）。

## 4. 未解決の判断

- `case.yaml` の冒頭の「実ハーネスでの陽性対照は docs/plans/issue-183.md を正とする」は、この周では変えない
  （`plugins/` を触ると版の bump が要る。指し先は実在し、結果も書いてある）

## 5. 関門の進捗（再開点）

- 手順 4: 実装済み（`run-dev-loop-evals.py`・テスト 29 件・変異 10 件・登録・`CLAUDE.md`）
  - テストが**本体の実バグを 1 件捕まえた**: `build()` が `out` だけ `resolve()` して `REPO` を解決しておらず、
    symlink 越し（macOS の `/var` → `/private/var`）だとリポジトリの中を指していても素通りした。両側を解決する形に直した
- 割り目（手順 4 の後）: `AskUserQuestion` で訊き、**「このまま続ける」**が選ばれた
- `check-all.py`: 30/30 緑（1 パス目の前）
- Verifier: 1 パス目 起動 / `/code-review`: 1 パス目 起動
- 実験: B（#183 の実データに `--summarize` を当てた）
  - 対照（`/private/tmp/e-LqmttA`）: 狙いの 2 本が期待どおり不合格、`ran-find-cycle` は目的外。
    Bash 1 回、`Preparing worktree (new branch 'issue/7-again')` と `HEAD is now at edfb64d init` を出し、雑音 12 行を除いた
  - 本物（`/private/tmp/e-iAcqg0`）: 3/3 合格。Bash 11 回
  - **どちらも終了コード 2**——#183 では 2 つを別々に回したので、各報告にもう片方のケースが無い（I3 のとおり）。
    **1 つの報告に両方が入る形は、E（人間が回す）で初めて当たる**
- `--dry-run`: 複製の対照と本物の `case.yaml` の差は `name` と `prompt` の 2 行だけ（`diff -r`）。リポジトリの
  `git status` は新規ファイル 2 つだけ

## 6. 既知の限界・決着済みの論点

- **本物のケースの緑が「何もせず止まった」でないかは、機械で判定しない**——要約は Bash の回数とコマンドを出し、
  読むのは人間（#183 の B で人間と私が trace を読んで確かめた形をそのまま出す）
