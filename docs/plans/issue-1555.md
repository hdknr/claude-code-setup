# Issue #1555: test-build-proposal.py の変異をプールで並列に当てる（#1517 の候補 3）

- 周の種類: cruise（親 Issue #1559）の子。**利用者が不在の周**（`/dev-loop:cruise 1559 --absent` の起動、2026-11-25T08:54Z。線は台帳の確かめた線——出所: 利用者の確認（起動時・2026-11-25T08:54:22Z、配布を見せて確かめた））
- 台帳の確かめた線: 仕様の穴 = 推奨で決めて起票／直す線 = 既定／周の途中の課題 = 台帳に足して直す／マージ = 関門を通ればマージ（マージは親）／マージ前の判断 = 推奨で決めて起票（後退・未達を含む）／実機確認: 書いていない（止まる）
- 直す線: 既定（出所: cruise の確かめた線）
- 単独で回す周: **当たる**——受入基準（A4・A5）が所要時間と CPU を測る（cruise の `references/parallel.md` の「単独で回す周」の 1）

## 変更範囲

触る:

- `scripts/test-build-proposal.py` — 子プロセスだけで判定する変異（`MUTATIONS`・`QA_MUTATIONS`・`PREVIOUS_MUTATIONS`・`NO_GIT_MUTATIONS`）を作業者のプール（スレッド）で同時に当て、結果は宣言順に `check` する。`--jobs N`（既定と上限 4）・`--pool-size`・`check_pool_size`。試料の写しの一覧（`_templates`）を排他で読み書きする
- `scripts/check-all.py` — `NESTED` に `test-build-proposal.py` を足し、docstring・コメントの本数を直す
- `scripts/test-check-all.py` — `nested_tests` に `test-build-proposal.py` を足し、コメントの本数を直す
- `CLAUDE.md` — `test-build-proposal.py` の説明に `--jobs` を 1 文
- `docs/plans/issue-1555.md` — この計画

触らない:

- `plugins/` の中（本体の `build-proposal.py` も含めて変えない。版も上げない）
- 本体を同じプロセスに読み込んで呼ぶ変異（`COMPOSE_MUTATIONS`・`WRITE_MUTATIONS`・`ENTRY_MUTATIONS`・`OWN_MUTATIONS`・`HAND_SPELLING_MUTATIONS`・`LOCKED_MUTATIONS`・`LINK_MUTATIONS`・`LEFTOVER_MUTATIONS`）——`entry_problems` が `os.environ` の `PATH` を、`link_problems` が標準出力を差し替えるので、並列にすると他の作業者に効く。プールが終わった後に今までどおり 1 つずつ当てる
- 試料（`CASES`）の並列化——Issue に無い（題は変異）。残課題に書く
- `.github/workflows/plugins.yml`（既定が並列なので CI のステップは今のまま変わる）

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

版: 上げない——`plugins/` を触らない（`scripts/`・`CLAUDE.md`・計画だけ）。マージの直前の取り込みでも版の行は無い

## デプロイ経路

main へのマージ → GitHub Pages の再ビルド。プラグインの中身は変えないので配布は起きない。反映経路: サイトの再ビルドだけ（`CLAUDE.md` の変更。公開ページの本文は変えない）。

## 周の大きさ

同じことを述べている箇所: 入れ子に `--jobs` を渡すテストの一覧と本数が `check-all.py` の `NESTED`・docstring（43・45 行）・コメント（170 行）、`test-check-all.py` の `nested_tests`・コメント（609 行）の 5 箇所と、`CLAUDE.md` の 1 文、`test-build-proposal.py` の docstring とコメントの 2 箇所。
分けない理由: 一覧に足すことと本数を直すことは同じ 1 つの変更で、分けると片方だけ古くなる（`test-check-all.py` が一覧の食い違いを見る）。#1361 と同じ形。

## 仕様の穴（不在の線で推奨により決めた）

- 穴: Issue は「受入基準は、測り方を決めたあとに書く」とし、測り方（何を測り、何をもって「悪化しない」とするか）を決めていない。実装の前に決めないと周を閉じる条件が無い
- 選択肢:
  - A（推奨）: 単体の壁時計と CPU（`/usr/bin/time -lp`、run-serial の枠の中、base と新を 1 回ずつ）＋ `check-all.py --no-cache` の全体（base と新を続けて 1 回ずつ。全体の壁時計・このテストの時間・上位）＋ 変異の判定が base と同じ（差分テスト）。「悪化しない」の線は、check-all の全体の壁時計が base の 1.10 倍以内、このテストが check-all の中で最も遅い 1 本にならない、単体の CPU（user＋sys）が base の 1.20 倍以内
  - B: 単体の壁時計・CPU と変異の判定だけ（check-all の全体は測らない）
  - C: A に加え、check-all を base と新で 3 回ずつ回してばらつきを見る
- 決めた値: A
- 推した理由: Issue が「単体の壁時計だけでなく、check-all 全体の時間と、他のテストの CPU の取り合いを見る」と書いており、#1517 の候補 1 は check-all の中でだけ逆効果が見えた——B では同じ見落としが起きうる。C は check-all 1 回がおよそ 30 分で、6 回は機械をおよそ 3 時間占め、並行の周を止める。取り合いは「このテストの CPU の総量が増えない」で代わりに見る（総量が同じなら、他のテストから取る CPU の合計は変わらず、時間の上での寄せ方が変わるだけ）
- 使った線と出所: `仕様の穴 = 推奨で決めて起票`（cruise の台帳の確かめた線。利用者の確認・2026-11-25T08:54:22Z）
- 確認の Issue: #1561（`要確認: test-build-proposal.py を速くする変更（#1555）の良し悪しを、何を測って決めるか`）

## 受入基準

不変条件 × 経路:

| # | 不変条件 | 経路（入口） | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 変異の判定と出力が base と同じ（差分テスト） | 素の起動（CI の `plugins.yml`・手元）・`--jobs 1`・`check-all.py` からの起動 | 下の「差分テスト」。base・新の既定・新の `--jobs 1` の終了コードと出力（正規化後）が一致 |
| A2 | 生き残る変異・届かない変異・期待どおりでない試料が、並列でも直列でも赤になり、失敗の行が宣言順に並ぶ | プールの 4 群（`MUTATIONS`・`QA_MUTATIONS`・`PREVIOUS_MUTATIONS`・`NO_GIT_MUTATIONS`）・プールの外の群・試料 | 差分テストの入力 S1・S2（壊した写し）で、新の既定と `--jobs 1` が base と同じ失敗の行を同じ順で出す |
| A3 | `--jobs 1` で作業者 1・`--jobs 99` は上限 4 で切る・`--jobs 0` を断る（2） | 引数 | テスト自身の `check_pool_size`・手で `--pool-size` を叩く |
| A4 | 単体の壁時計が base より短く、CPU（user＋sys）が base の 1.20 倍以内 | 素の起動 | `/usr/bin/time -lp`（run-serial の枠の中で 1 回ずつ） |
| A5 | check-all の全体の壁時計が base の 1.10 倍以内で、このテストが check-all の中で最も遅い 1 本にならない | `check-all.py --no-cache`（入れ子の `--jobs`） | base と新を続けて 1 回ずつ。全体の秒と上位の行 |
| A6 | `check-all.py` から入れ子の `--jobs` が渡る（親の半分。`--jobs 1` なら 1） | `check-all.py` の `NESTED` | `test-check-all.py` の 9) が `test-build-proposal.py` を含めて緑 |
| A7 | 試料の写しの一覧（`_templates`）が、同時に作っても壊れない（同じ名前に写さない・書きかけを読まない） | 作業者が同じ `steps` を同時に `build_repo` で作る | 一時の場所で `build_repo` を 8 スレッド同時に呼ぶ（同じ `steps` 4 つ・違う `steps` 4 つ。名前を決める点をそろえ、写しの 1 本目を先に写し終えさせる）。全部の根ができ、一覧が 5 件で、一覧の写しから作り直した根がその `steps` の中身であること。旧い名前の振り方（base の `len(_templates)`）では壊れる陽性対照 |
| A8 | プールの作業者が走っているあいだ、本体を同じプロセスに読み込む群（`PATH` と標準出力を差し替える）が走らない | `main` の順 | コードの構造（`run_jobs` はプールを閉じて全部を待ってから返す）を関門が読む・A1 の一致 |
| A9 | 実リポジトリを触らない | すべての起動 | 走らせる前後の `git status --porcelain` が同じ |
| A10 | 歯止めが全部緑 | リポジトリの CI | `python3 scripts/check-all.py` と PR 側の CI |

掛け算: 受入基準を Verifier と `/code-review` の両方に、2 パス（1 パス目の指摘対応の差分が 0 行なら 1 パス）。

未証明: A5 は 1 回ずつで、ばらつきは見ていない（他のセッションの負荷を止められない。始めと終わりの負荷平均を書く）。CI（4 vCPU）での秒は手元（28 コア）と違う——PR 側の CI のステップの秒は観測として書くだけで、基準にしない。

生成物: なし（このテストは一時ディレクトリにだけ書く。§8.2 の生成ブロック・図の書き出しに触れない）。

プロパティテスト: なし（入力は固定の試料と変異の一覧で、生成する入力の空間が無い。等価性は差分テストが見る）

差分テスト: あり

## 差分テスト

| 項目 | 書くもの |
| --- | --- |
| 旧 | 周の base の SHA `a06a460f5b0a63d917b6311c0672235be01afe84` |
| 新 | `f4effc21`（成果物の最後のコミット。以後は計画ファイルだけを変える） |
| 入力の出どころ | 生成（手で選んだ 3 つの形）: S0 = 壊さない木、S1 = テストの写しの末尾で変異の一覧を書き換えた木（プールの 4 群とプールの外の 1 群で、変異を等価にする・壊す箇所を消す）、S2 = 本体 `build-proposal.py` を 1 か所壊した木。旧（base の木）・新の既定・新の `--jobs 1` の 3 通りで、計 9 回 |
| 正規化した項目 | 一時ディレクトリのパス（`tempfile` が毎回違う名前を振る。比較に関係ない）。`run.py` は完全なパスだけを置き換え、`output[-300:]` で頭の切れたパスの `proposal-test-<8 文字>` を残したので、`compare.py` で `proposal-test-` の後ろ 8 文字だけを置き換えて比べ直した（Verifier 1 パス目の反証 2。外すと 4 組が「差分あり」で、違いはその 8 文字だけ） |
| 結果 | 6 組（S0・S1・S2 × 新の既定・`--jobs 1`）を旧と比べ、差分 0 組（`compare.py`）。旧の失敗の行は S0 0・S1 7（プールの 4 群・届かない変異・プールの外の LINK）・S2 2。陽性対照: 指摘 CR1-1 の再現（worktree 型の試料の確かめを落とす写し）で、`f4effc21` の新は旧と失敗の行の順が違った（差分を検出）。Verifier は新の写しで宣言順を逆にして順の違いが出ることを独立に確かめた |
| 回した場所 | リポジトリの外（`git archive` で取り出した木。scratchpad） |

### 承認済みの変更の一覧

承認済みの変更: なし

（新しい口 `--jobs`・`--pool-size` は旧に無い口で、差分テストの入力に入れない——旧と新で同じに呼べる引数なしの形だけを比べる。新しい口は A3 が見る。）

## 測定の結果（A4・A5）

28 コアの macOS。run-serial の枠の中で 1 回ずつ（同じリポジトリの他の check-all とは重ならない。他のセッションの処理とは重なりうる）。負荷は 1 分平均。

| 測ったもの | base（`a06a460f`） | 新（作業ツリー＝`f4effc21` と同じ中身） | 比 |
| --- | --- | --- | --- |
| 単体の壁時計（既定） | 155.3 秒（08:59:10Z〜。負荷 2.85 → 3.62） | 124.9 秒（09:01:59Z〜。負荷 3.26 → 4.04） | 0.80 |
| 単体の CPU（user＋sys） | 146.7 秒（91.7＋55.0） | 148.1 秒（92.4＋55.7） | 1.01 |
| 単体の壁時計（新の `--jobs 1`） | — | 145.6 秒（CPU 136.4。09:04:04Z〜。負荷 4.04 → 2.59） | — |
| check-all `--no-cache` の全体 | 905.6 秒（09:10:12Z〜。失敗 0） | 891.1 秒（09:25:18Z〜。失敗 0） | 0.98 |
| check-all の中のこのテスト | 483.2 秒（最も遅いのは `test-line-effects.py` 905.2 秒） | 437.6 秒（最も遅いのは `test-line-effects.py` 890.7 秒） | 0.91 |
| check-all の CPU（user＋sys） | 15029.6 秒 | 14683.9 秒 | 0.98 |

- A4: 満たす（壁時計 0.80・CPU 1.01 ≦ 1.20）。A5: 満たす（全体 0.98 ≦ 1.10・最も遅い 1 本は両方とも `test-line-effects.py`）
- 単体の短縮が 2 割にとどまるのは、試料（`CASES` 117 件・2 回ずつ生成）とプールの外の群が直列のままだから（既知の限界）
- base の check-all の終わりと新の始めは連続していて、新の始めの 5 分平均・15 分平均は base の回の負荷を含む

## A7 の確かめ

`<scratchpad>/a7.py <test-build-proposal.py>`（モジュールを読み込み、`_build_repo` の後に 8 本をそろえ、写しの 1 本目を先に写し終えさせる）。
新（作業ツリー）: 3 回とも 0（一覧 5 件・欠けた写し 0・作り直した根の中身が一致）。base の写し（`a06a460f`）: 2 回とも 1——一覧に載った写し `templates/0` が他の作業者の `rmtree` で消え、作り直しが `FileNotFoundError`。

### A7 の後半（書きかけを読まない）

`<scratchpad>/a7b.py`: 写しを遅らせている最中に、同じ `steps` で読む作業者を 4 本走らせる。新: 3 回とも 0。写し終える前に一覧へ載せる変異（`setdefault` を `copytree` の前へ）: 2 回とも 1（読み手が `FileNotFoundError`）。/code-review 1 パス目の指摘 CR1-2 に応えて足した（`a7.py` だけでは判別していなかった）。

## 未解決の判断・確認待ち事項

- 測り方（上の「仕様の穴」）——確認の Issue で利用者に確かめる

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1555-parallel-build-proposal-mutations`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1555`・起点 `a06a460f`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `a06a460f5b0a63d917b6311c0672235be01afe84`
- 割り目（手順 4）: 割らない（cruise の周）
- 実装: `f4effc21`（`check-all.py --no-cache` を作業ツリーで回して失敗 0——上の「測定の結果」の新の回）
- 1 パス目の指摘対応の起点: `2b0b0612a172e55ee0cff917269ce77b3501cceb`
- 関門: Verifier 1 パス目（報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/e26910d5-e27d-462f-bd16-ccb8bf1b1046/scratchpad/gate-1555-verifier-1-20261125T095959Z.md`）・/code-review 1 パス目（報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/e26910d5-e27d-462f-bd16-ccb8bf1b1046/scratchpad/gate-1555-code-review-1-20261125T095959Z.md`）の結果: Verifier 1 反証 3（受入基準を破ると示したもの 0）・/code-review 1 指摘 6（nit）。採否は下の表。直し `3b24bbc4`（check-all 失敗 0）
- 割り目（手順 6 の 2 パス目の前）: 割らない（cruise の周）。残りは Verifier 2 パス目と /code-review 2 パス目
- 関門: Verifier 2 パス目（報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/e26910d5-e27d-462f-bd16-ccb8bf1b1046/scratchpad/gate-1555-verifier-2-20261125T110322Z.md`）・/code-review 2 パス目（報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/e26910d5-e27d-462f-bd16-ccb8bf1b1046/scratchpad/gate-1555-code-review-2-20261125T110322Z.md`）を起こした（終点 `3b24bbc4`）

```dev-loop-gates
周の base: a06a460f5b0a63d917b6311c0672235be01afe84
関門: Verifier 1 2b0b0612a172e55ee0cff917269ce77b3501cceb 反証=3
関門: /code-review 1 2b0b0612a172e55ee0cff917269ce77b3501cceb 指摘=6
```

## 既知の限界・決着済みの論点

- 試料（`CASES`）は直列のまま——Issue の題は変異で、試料の並列化は範囲の外（触らない）。単体の短縮はその分だけ小さい
- 本体を同じプロセスに読み込む群は直列のまま——並列にすると `PATH`・標準出力の差し替えが他の作業者に効く（A8）
- 測定は 1 回ずつ（上の「未証明」）
- A7 の行は確定のコミットの後に「確かめ方」の列だけを、実際に回した形（同じ `steps` 4 つ・違う 4 つ）に書き直した。不変条件の列は変えていない

### 1 パス目の指摘の採否（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1-1／V1-3 | `run_no_git` の worktree 型の `check` が作業者の中で走り、失敗の行が宣言順より前に並ぶ | 示せる——`cr1/`（worktree の確かめを落とし PREVIOUS_MUTATIONS[0] を等価にした写し）で旧は「確かめ→生き残り→確かめ」、`f4effc21` は「確かめ→確かめ→生き残り」。直した後は旧と同じ順 | A2 | 直す（試料の形の確かめを返し、宣言順の位置で `check`） |
| CR1-2 | A7 の確かめ（`a7.py`）が「書きかけを読まない」を判別していない | 示せる——`setdefault` を前へ移した変異で `a7.py` が 0 | A7（確かめ方） | 直す（実験の側。`a7b.py` を足した。成果物の差分なし） |
| CR1-2b | `build_repo` の docstring の「同じ `steps` を同時に作り終えた」が狭い（違う `steps` でも同じ名前になる） | 示せない（文言） | 無し | 残課題 |
| CR1-3 | A5 の全体の壁時計の線は、律速の `test-line-effects.py` に決まり、このテストに反応しない | 示せない（計測の設計） | 無し | 残課題（確認の Issue #1561 にコメントで材料を足す） |
| CR1-4 | `check_pool_size` は `--pool-size` の経路だけで、main の変異の経路がプールを使うかを見ない | 示せない（退行は仮定） | 無し | 残課題 |
| CR1-5 | プールの仕事が例外を投げると、残りを当て終えるまで上がらない | 示せない（環境の失敗の仮定） | 無し | 残課題 |
| CR1-6 | 同じ `steps` を同時に作った負けた側の写しが消されずに残る | 示せる（`a7.py` で一覧 5 件・ディレクトリ 8 つ） | 無し | 残課題 |
| V1-1 | A7 を守る回帰テストがリポジトリに無い | 示せない（CI が緑のままなのは仮定） | 無し | 残課題 |
| V1-2 | 差分テストの正規化が切れたパスを残す | 示せる（`bg-diff.txt` の 4 組） | A1（確かめ方） | 直す（実験の側。`compare.py`。成果物の差分なし） |

## 経験の還元（手順 8）

- この周の起票: 1 件（仕様の穴の確認の Issue #1561。不在の線 `仕様の穴 = 推奨で決めて起票`）
