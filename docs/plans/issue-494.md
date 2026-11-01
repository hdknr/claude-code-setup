# Issue #494（3 回目の周）— check-all の 1 回を軽くする（次の長い柱）

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-11-01）の周。**不在の周**である——訊く場面は
  `references/absent-lines.md` の「訊く場面」のとおり訊かずに進める（`AskUserQuestion` を使わない）。この周は cruise の親から委ねられ、
  `EnterWorktree` を使わず worktree の絶対パスで作業する。マージは親が行う（この周は PR・PR 側の CI・関門 2 パス・狭いパス・手順 8 の件数の行まで）。
  台帳は書かない。
- **単独で回す周**（台帳の `note` の `単独: check-all の所要時間を測る`。cruise `references/parallel.md` の「単独で回す周」）——
  測定のあいだ他の cruise の周は走っていない。**機械の上の他のプロセスは交絡として残る**ので、測定ごとに `uptime` の負荷を書く。
  重い検査は `run-serial.py` 越しに走らせた。
- 使った線（出所: 利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた）。
  cruise の台帳 `issue-474` の確かめた線を親から受けた）:
  `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`。
- 利用者の直接の指示（2026-10-29、親から受けた）: 人間の判断が要るもの（狭いパスの指摘を含む）は推奨で決め、`要確認:` で始まる題の Issue
  （本文の先頭に `<!-- cruise-decision: #474 -->`、ラベル `要確認`。#557 の形）で確かめる。起票はこの周が行い、番号を親に報告する。
- **線の変更（2026-11-01、周の途中に親から受けた。利用者が台帳の線を変えた）**: `周の途中の課題 = 外に出す`（前は `台帳に足して直す`）。
  この周で後続の Issue を立てるのは、受入基準を破るもの・利用者に見える誤った結果・この周が入れた退行だけ。
  試料の穴・まれな入力の形・言い回し・性能の推測は PR コメントの残課題にだけ書く（Issue にしない）。
  したがって `references/found-lines.md` の「振り分け」「台帳に足す」は行わない。
- 直す線: **既定**（出所: 同上の cruise の確かめた線）。
- 版: **上げない**——触るのは `scripts/` と計画ファイルだけで、プラグインのファイルを触らない（`CLAUDE.md`「プラグインの更新」）。

### 前の 2 つの周と、計画ファイルの名前（仕様の穴）

- #494 の周は 3 回目である: 1 回目は PR #674（計画 `docs/plans/issue-494.md` → この周で `docs/plans/issue-494-674.md` に改名）、
  2 回目は PR #747（#687 とまとめた周。計画 `docs/plans/issue-687.md`）。どちらもマージ済みで、この周は再開ではない（`find-cycle.py 494` は
  ブランチ・worktree に当たらず、計画ファイルとコミットにだけ当たった）。
- 1 回目のブランチ `issue/494-check-all-bundle` は利用者が消した（#751 で利用者が承認した形の後）。`prepare-worktree.sh 494 check-all-light-2` は 0 で作れた。
- **仕様の穴**: ブランチ `issue/494-…` の周の計画ファイルは、`check-plan-scope.py` がブランチ名の番号で `docs/plans/issue-494.md` に当てる。
  そこには 1 回目の周の記録があり、件数の行は 1 ファイルに 1 本（`check-plan-counts.py`）なので、同じファイルに 2 つの周を書けない。
  - 選択肢: (A) 1 回目の記録を `docs/plans/issue-494-674.md`（PR 番号）へ改名し、この周が `docs/plans/issue-494.md` を使う／
    (B) この周を `docs/plans/issue-494-2.md` に書き、`check-plan-scope.py` が `issue-<n>-*.md` も探すよう直す／
    (C) 1 回目の記録の末尾に足し、件数の行を 2 本にできるよう `check-plan-counts.py` を直す
  - **決めた値: (A)**。理由: 歯止め 2 本（変更範囲・件数の行）をどちらも直さずに働かせられる。中身は 1 文字も変えない改名（`git mv`）なので記録は残る。
    失うのは公開サイトの `plans/issue-494/` の URL が 1 回目の記録を指さなくなることと、`docs/plans/issue-687.md` の本文の 2 か所の言及が古いパスを指すこと（記録なので直さない）。
  - 確認の Issue: #775（推奨: マージの前に直すものは無い。(B)・(C) を選ぶなら後続で直す）

## 変更範囲

触る:

- `scripts/test-schedule-to-gantt.py` — 入口の変異の回を最初の問題で止める（`Problems`・`found`）・`MUTATIONS` の回は名指しした試料だけを回す
- `scripts/test-build-proposal.py` — `link_problems`・`leftover_problems` の変異の回を最初の問題で止める・変異の回は 2 回目の生成を、判定が読んだときだけ回す
  （`judge_mutant`）・同じ `steps` の試料のリポジトリを写しから複製する（`build_repo`）
- `scripts/test-parent-issue.py` — 変異の回を、観測が正しい本体と食い違った時点で止める（`Observations`。`test-ledger.py` と同じ形）
- `scripts/test-check-spec-exit.py` — 変異の回は名指しした試料だけを回す（`run_all` の `only`）
- `scripts/test-check-frozen.py` — 同じ
- `scripts/test-check-feasibility-csv.py` — 同じ（チェックリストに無いが、同じ形を `grep` で見つけた。25 秒）
- `docs/plans/issue-494.md` — この計画
- `docs/plans/issue-494-674.md` — 1 回目の周の記録（`docs/plans/issue-494.md` からの改名だけ。中身は変えない）

触らない:

- `scripts/check-all.py` の `GUARDS`・`TESTS`・並列の形（**回すものを 1 本も減らさない**）
- `plugins/` の中（版も上げない）
- CI のワークフロー
- `docs/plans/issue-687.md`（2 回目の周の記録）

## 複製の数

- 「最初の問題で止める」補助（`_Found`・`Problems`・`found`）は `test-schedule-to-gantt.py` と `test-build-proposal.py` の 2 箇所に同じ形で書いた
  （回帰テストは単独で動くスクリプトで、共有のモジュールを足すと `scripts/` の収録と回帰テストが要る——#687 の `test-ledger.py`・`test-check-unattended-env.py` と同じ判断）。
- `Observations`・`_Diverged` は `test-ledger.py`（前の周）と `test-parent-issue.py` の 2 箇所。
- `run_all` の `only` の説明は `test-check-spec-exit.py`・`test-check-frozen.py`・`test-check-feasibility-csv.py` の 3 箇所に同じ文。
- 分けない理由: どれもテストごとに観測の形が違い、合わせて 20 行ほど。共有にすると 6 本のテストが 1 つのモジュールに依存する。

## デプロイ経路

- 反映経路なし（`scripts/` と計画ファイルだけ。プラグインの配布に入らない）。計画ファイルは `docs/` の下なので公開サイトに載る（main への push で自動デプロイ）——
  `plans/issue-494/` のページの中身が 1 回目の記録から今回の記録に替わり、1 回目は `plans/issue-494-674/` に移る（#775）。

## 測ったこと（#494 の求めること 1）

**条件**: 2026-11-01、10 コアの macOS（Darwin 27.0.0）・Python 3.14.3（CI は 3.12）。**単独で回す周**で、他の cruise の周は走っていない。
機械の上の他のプロセスは残る——とくに `fseventsd` が CPU 約 95%（測り始めの `ps`）・`XProtectRemediatorPirrit` が約 56%。何もしていないときの負荷の平均は 3〜6。
重い測定は `run-serial.py` 越し。台本は scratchpad の `i494b-time.py`（`check-all.py` の `GUARDS`・`TESTS` を読み、同じ引数で 1 本ずつ直列に起こす。
入れ子は `--jobs 5`。環境変数は足さない——#687 の `PYTHONDONTWRITEBYTECODE` の交絡）・`i494b-prof.py`（cProfile でテスト自身の関数の累積時間）。

### 1 本ずつ直列に回した wall（変える前の木 = base `7a6addf1` の `git archive`。`.git` が無いので base の要る歯止め 2 本は rc=2）

| スクリプト | 秒 | 負荷（前→後） |
| --- | --- | --- |
| `test-schedule-to-gantt.py` | 191 | 4.1→3.7 |
| `test-build-proposal.py` | 181 | 3.6→3.5 |
| `test-parent-issue.py` | 131 | 9.8→5.1 |
| `test-check-unattended-env.py` | 122 | 6.8→7.7 |
| `test-ledger.py` | 117 | 6.3→9.8 |
| `test-run-serial.py` | 95 | 4.3→4.3 |
| `test-worktree-scripts.py` | 79 | 4.5→4.6 |
| `test-check-spec-exit.py` | 71 | 3.5→4.0 |
| `test-check-mutation-claims.py` | 56 | 4.7→4.9 |
| `test-scaffold.py` | 55 | 3.5→3.6 |
| `test-qa-to-pptx.py` | 46 | 4.9→3.5 |
| `test-check-frozen.py` | 45 | 3.4→3.5 |
| `check-mutation-claims.py` | 43 | 5.4→7.5 |
| `test-launch-with-long-token.py` | 42 | 7.7→6.3 |
| `test-merge-pr.py` | 39 | 3.3→3.5 |
| `test-check-all.py` | 34 | 6.4→6.6 |
| `test-check-version-bump.py` | 34 | 6.7→6.3 |
| `test-check-signoff.py` | 32 | 3.7→3.6 |
| `test-child-cycle.py` | 30 | 5.1→4.3 |
| `test-check-feasibility-csv.py` | 25 | 4.0→4.1 |
| `test-check-plan-scope.py` | 25 | 6.6→6.6 |
| 残り 37 本 | 合計 81 | 3〜8 |

- 合計 1,591 秒（58 本）。#687 の表（2,534 秒）から、`test-ledger.py`・`test-check-unattended-env.py` が前の周で、`test-build-proposal.py`（293 → 181 秒）は
  その間の main の変更で下がっていた（この周の変更ではない。どの変更かは追っていない）。

### 中身（cProfile。変える前の木）

- `test-schedule-to-gantt.py` 190 秒: `entry_problems` 60 回で 179 秒（正しい本体 1 回＋入口の変異 59 件。1 回約 3 秒・子のプロセス約 28 本）。
  `MUTATIONS` 12 件は毎回 13 試料を全部回し、判定は名指しした 1 試料だけ（9.5 秒）。
- `test-build-proposal.py` 182 秒: `run_case` 168 回 110 秒（うち `build_repo` 296 回 48 秒・git の子 3,769 本、`generate` 469 回 106 秒）・`link_problems` 13 回 34 秒・
  `leftover_problems` 27 回 30 秒。2 回目の生成（`again`）を読む判定は 83 試料のうち 4 つだけ。
- `test-parent-issue.py` 100 秒（cProfile 越し）: `scenario` 36 回（正しい本体 1・変異 35）。
- `test-check-spec-exit.py` 89 秒: `run_all` 36 回（変異ごとに 42 試料を全部回し、判定は名指しした 1 試料）。`test-check-frozen.py` 48 秒: 同じ形（`run_all` 15 回）。
- `test-child-cycle.py` 27 秒（`scenario` 18 回・待ち合わせ 12 秒）・`test-check-plan-scope.py` 18 秒——柱ではないので触らない。

## 受入基準（不変条件 × 経路）

| # | 基準 | 証明 |
| --- | --- | --- |
| A1 | 各スクリプトの所要時間の表が、測った条件とともに残っている | 上の「測ったこと」 |
| A2 | 他の周と重ならない条件で、`check-all.py` の 1 回の wall が測った値から下がっている（どれだけかを同じ条件で示す） | 下の「直した前後の比較」 |
| A3 | 変える前後で、各回帰テストが殺す変異の数が減っていない（変えたテストごと） | 下の「殺す変異の数」 |
| A4 | (c) を採るなら、入力を 1 文字変えると飛ばさずに回ることを示す | **該当なし**——(c) は採らない |
| A5 | **守るものを落とさない**——陽性対照・「当てられなかった」は緑ではない・**毎回全部回す（#117）**——`check-all.py` の回すものを減らさない | `check-all.py` の差分 0 行・変えたテストの陽性対照（正しい本体の回は今までどおり全部を回す） |
| A6 | #494 のチェックリスト「重いテストを軽くする（1 本ずつ測ってから）」の 7 本を、測ってから判断している | 上の表と「中身」——`test-parent-issue.py`・`test-build-proposal.py`・`test-check-frozen.py`・`test-check-spec-exit.py` を軽くした。`test-ledger.py` は前の周（#747）。`test-child-cycle.py`（30 秒）・`test-check-plan-scope.py`（25 秒）は測って柱でないと判断し触らない |

### 不変条件と、それを破りうる経路

| 不変条件 | 破りうる経路 | どう守るか |
| --- | --- | --- |
| I1: 変える前に殺せた変異は、変えた後も殺せる（変異の判定は変えない） | ①最初の問題で止める（`Problems.append`・`extend`・`+=` の 3 つの足し方。足し方を漏らすと止まらないだけ——判定は同じ）②`_Found` が試料の中の `except` に飲まれる ③名指しした試料だけ回す（他の試料の結果が判定に効いていた場合）④`Observations`（同じ鍵を 2 度書く・書いた値を後で変える）⑤2 回目の生成を省く（判定が読む・2 回目の生成が出力の場所を変える変異）⑥写しから作るリポジトリ（本体が索引の stat を読む・権限・symlink・作れない手順） | ①判定は `bool(問題の一覧)`——1 件目で決まる ②`_Found`・`_AgainSkipped`・`_Diverged` は `BaseException` の直接の子（`main` が表明）③判定は `as_expected(killer, …)` だけを読む・試料は別の場所で別のプロセス ④前提を正しい本体の回で表明（`unchanged`）⑤読んだら `_AgainSkipped` で回し直す・生き残れば赤 ⑥本体の git は `show`・`ls-tree`・`cat-file`・コミット間 `diff`・`rev-parse`・`tag --list`・`chmod` の手順は写さない・写せなければ毎回作る。**全体として**: 変える前後で殺す変異の数と全部殺すこと（A3） |
| I2: `check-all.py` は毎回全部を回す | この周は `check-all.py` を変えない。テストの中で変異を飛ばす形 | `check-all.py` の差分 0 行・変異は全部当てる（止めるのは 1 件の変異の中だけ） |
| I3: 正しい本体の回は今までどおり全部を見る | 止める・省く・名指しの形が正しい本体の回にも効く | `stop`・`again=False`・`only`・`ref` は変異の回でだけ渡す（正しい本体の回は既定値）。写しから作るリポジトリは正しい本体の回にも効く（⑥） |
| I4: テストは実リポジトリを書き換えない | 写しの置き場・止めた回の後始末（権限を戻す `finally`） | 写しは一時ディレクトリの中（`TEMPLATES`）・`assert_in_tmp`・止める例外は `finally` を通る |

### 証明できないもの（未証明）

- **CI（Linux・Python 3.12）での所要時間**——手元（macOS・3.14）で測った。CI は各テストを個別のステップで回す。
- **将来の変異で、止めない形と止める形の判定が分かれないこと**——今の変異は前後で全部殺す（A3）。分かれうるのは ⑤（2 回目の生成が出力の場所を変える変異）だけで、その向きは「生き残る」＝赤。

### 生成物

- **生成物なし**——`SKILL.md`・図・設計ドキュメントの生成ブロックに触らない（`scripts/` と計画ファイルだけ）。

## 採った候補と採らなかった候補（#494 の (a)〜(d)）

- (a)・(b)——採らない（#687 の測定のとおり `check-mutation-claims.py` は柱ではない。今回の直列で 43 秒）。
- (c) 入力が変わっていない検査を飛ばす——採らない（柱は中身で縮められ、飛ばす仕組みは「毎回全部回す（#117）」の例外を作る）。
- (d) 回帰テストの準備を軽くする——**採った**: 変異の回の仕事を減らす形（最初の失敗で止める・名指しした試料だけ・2 回目の生成を省く・同じリポジトリを写しから作る）。
  **作業者を増やす形（同時に当てる）は採らない**——#687 で `test-build-proposal.py` のスレッドが遅くなり、`check-all.py` の中では CPU が埋まる（負荷 15〜28）ので、
  総量を減らす形のほうが `check-all.py` の wall に効く。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/494-check-all-light-2`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-494`・
  起点コミット `7a6addf1`・base `7a6addf1ae7c88690aa852c5cf76675f8f259011`（参照 `origin/main`。`prepare-worktree.sh` の出力）
- 割り目（手順 4 の完了時）: 不在の周なので訊かない。このまま続ける。
- 実装のコミット: `bd9e0ee7`。

## 手順 8

- この周の起票: 1 件（#775——仕様の穴を推奨で決めた確認の Issue。起票の承認は不在のため訊いていない）
