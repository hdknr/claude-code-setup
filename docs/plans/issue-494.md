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
  - 確認の Issue: （起票後に番号を書く）

## 変更範囲

触る:

- `scripts/test-schedule-to-gantt.py` — 入口の変異の回を最初の問題で止める（`Problems`・`found`）・`MUTATIONS` の回は名指しした試料だけを回す
- `scripts/test-build-proposal.py` — `link_problems`・`leftover_problems` の変異の回を最初の問題で止める・変異の回は 2 回目の生成を、判定が読んだときだけ回す
  （`judge_mutant`）・同じ `steps` の試料のリポジトリを写しから複製する（`build_repo`）
- `scripts/test-parent-issue.py` — 変異の回を、観測が正しい本体と食い違った時点で止める（`Observations`。`test-ledger.py` と同じ形）
- `scripts/test-check-spec-exit.py`・`scripts/test-check-frozen.py`・`scripts/test-check-feasibility-csv.py` — 変異の回は名指しした試料だけを回す（`run_all` の `only`）
- `docs/plans/issue-494.md` — この計画
- `docs/plans/issue-494-674.md` — 1 回目の周の記録（`docs/plans/issue-494.md` からの改名だけ。中身は変えない）

触らない:

- `scripts/check-all.py` の `GUARDS`・`TESTS`・並列の形（**回すものを 1 本も減らさない**）
- `plugins/` の中（版も上げない）
- CI のワークフロー
- `docs/plans/issue-687.md`（2 回目の周の記録）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/494-check-all-light-2`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-494`・
  起点コミット `7a6addf1`・base `7a6addf1ae7c88690aa852c5cf76675f8f259011`（参照 `origin/main`。`prepare-worktree.sh` の出力）
