# Issue #206 — SKILL.md の prepare-worktree.sh 終了コード一覧に 7 が無い

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 4 の `prepare-worktree.sh` 終了コード一覧に 7 を足す・版のバナー
- `plugins/dev-loop/.claude-plugin/plugin.json` — version 1.37.1 → 1.37.2（patch: 記述の修正）
- `.claude-plugin/marketplace.json` — 同上
- `scripts/test-worktree-scripts.py` — 一覧とスクリプトの終了コードの突き合わせ（2 本とも）と、その変異
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合のみ）
- `docs/plans/issue-206.md` — この計画ファイル

触らない:

- `prepare-worktree.sh` / `check-pr-preconditions.sh` 本体（挙動は正しい。直すのは一覧の側）
- スクリプトのヘッダコメント（`check-pr-preconditions.sh` のヘッダにも一覧があるが、突き合わせの対象にしない——既知の限界）
- 新しい歯止めスクリプト（既存の `test-worktree-scripts.py` の `check_norm_shape` と同じ「規定の側を読む」形に載せる）

**複製の数**: 「`prepare-worktree.sh` の終了コード」を述べている箇所は 2 つ——`SKILL.md` 手順 4 の一覧と、
スクリプト本体（`exit N` とヘッダの 5/6/7 の箇条）。`check-pr-preconditions.sh` も同じ形で 2 つ
（`SKILL.md` 手順 6 の一覧・本体とヘッダ）。**分けない理由**: 一覧の修正とその突き合わせは同じ 1 つの決定で、
突き合わせを後回しにすると次の終了コード追加で同じずれが再発する（Issue の受入基準 2）。

## 2. デプロイ経路

- `plugins/`：プラグイン配布（version bump → マージ → 利用者の `plugin update`）。
- `scripts/`：CI の回帰テスト（`plugins.yml` が `test-worktree-scripts.py` を回しているか確認する）。
- `docs/`：main への push で GitHub Pages に自動デプロイ（計画ファイル・生成ブロック）。

## 3. 受入基準

**I1. `SKILL.md` の `prepare-worktree.sh` 一覧に挙がる番号の集合が、スクリプトが返しうる固定の終了コードの集合と一致する。**
固定の終了コード = 明示の `exit N` ∪ {0（正常終了）} ∪ {1（`${N:?}` の引数不足。bash の実測で 1）}。
`git worktree add` の失敗は git の終了コードで固定でないので「それ以外」に残す。

**I2. 7 の説明が挙動と合っている**: 「`DEV_LOOP_BASE_REF` で名指しした参照が解決できない／作っていない／HEAD に落とさない」。
挙動は既存テスト（`名指しが解決しない: rc == 7`・`名指しが解決しなければ作らない`）が当てている。

**I3. 一覧とスクリプトのずれを機械で見る**: `test-worktree-scripts.py` が両者を突き合わせ、次のどの経路でも赤になる。

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 一覧から番号を消す（Issue の再現。7 が無い） | 赤 | 一覧の番号集合 ⊇ スクリプトの集合 |
| P2 スクリプトに新しい `exit N` を足して一覧を直さない | 赤 | 同上（スクリプトから自動で集める） |
| P3 一覧にスクリプトに無い番号を書く | 赤 | 一覧 ⊆ スクリプト |
| P4 `5・6` のように束ねた書き方 | 両方を数える | `・` で割る |
| P5 `check-pr-preconditions.sh` の一覧（手順 6）で P1〜P3 | 赤 | 同じ関数を 2 本に当てる |
| P6 一覧の段落そのものが見つからない（見出し語の改名など） | 赤（「当てられなかった」を緑にしない） | 見つからなければ失敗として数える |
| P7 コメント中の `exit N`（`# … exit 7`・行末の `cmd  # … exit 7`） | 数えない | 引用の外の `#`（行頭か空白・`;` の直後）から行末を落としてから数える |
| P8 実リポジトリの現状（修正後） | 緑 | — |

**I4. 修正前の版で赤になる（陽性対照）**: base（`53d06c3`）の `SKILL.md` を当てると P1 として赤になる。

**I5. version 3 箇所が 1.37.2 で揃い、`check-all.py` が全部緑、PR の CI も緑。**

**I6. 生成物の鮮度**: 生成物は `skill-metrics.py` の §8.2 生成ブロックのみ該当（`SKILL.md` の行数が動きうる）。
`skill-metrics.py --check` が緑。図（drawio）は触らないので該当なし。

**必須要件の掛け算**: 受入基準 × {Verifier, `/code-review`} × {1 パス目, 2 パス目} = 4 つの受け渡し。

### 証明の手段

- I1・I3・I4: `test-worktree-scripts.py`（変異は文字列上で当てる）＋ base の `SKILL.md` に対して手で当てる。
- I2: 既存テストと本体 `prepare-worktree.sh` の読解。
- I5・I6: `python3 scripts/check-all.py`、`gh pr checks`。
- **未証明**: なし。**BLOCKED**: なし。

## 4. 未解決の判断

- なし。

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/206-exit-code-list` ／ worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-206` ／
  起点 `53d06c3` ／ base 参照 `origin/main` → `53d06c35b1c94561dae32203f20adf57f03d43fa`
- 実装: 済（`SKILL.md` に 7 を追記・版 1.37.2・`test-worktree-scripts.py` に `check_exit_code_lists`）
- 陽性対照（I4）: base `53d06c3` の `SKILL.md` に当てると prepare は `[0,1,2,3,5,6]` vs `[0,1,2,3,5,6,7]` で不一致（赤）。
  check-pr-preconditions は base でも一致（緑）——こちらは元からずれていない。
- `check-all.py`: 33 本中 32 本緑。**落ちたのは `test-tab-match.py`（orca）だけで、この周の差分と無関係**——
  **main（`53d06c3` = PR #237 のマージ）の `Check plugin catalog` が既に failure**。この周では直さない（範囲外）。
  したがって I5 の「PR の CI も緑」は、この 1 ステップについて満たせない（main 由来）。
- 割り目 1（手順 4 完了時）: AskUserQuestion で提案 → **人間が「ここで割る」を選択**（2026-10-14）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 206` → **手順 5（Verifier 1 パス目）から**。
- 関門 1 パス目: **Verifier（Sonnet・`dev-loop:dev-loop-verifier`）反証 1 件**／**`/code-review`（high）指摘 8 件**。
  採否は 6 の表。直すのは 2 件（V1=CR1・CR2）で、手順 4 へ差し戻し。
- 反証: 1 パス目 計 9 件（重複 1）。
- 1 パス目の指摘対応: 済（`dafb1c8`）。`script_exit_codes` が同じ行の `exit N` を数え、値の読めない `exit` で `None`。
  変異に `|| exit N`・`then exit N; fi`・`; exit N`・`exit "$rc"`・`exit -1`・素の `exit` を追加。
  **陽性対照**: 旧い正規表現はこの 6 形のどれも検出しない（`exit 8` だけ検出）——新しい変異は旧実装で赤になる。
  `check-all.py`: 33/33 本、失敗 1（`test-tab-match.py`。main 由来——両関門が `53d06c3` で同じ赤を確認）。
- 関門 2 パス目: **Verifier（Sonnet・`dev-loop:dev-loop-verifier`）反証 0 件**／**`/code-review`（high）指摘 8 件**。
  採否は 6 の「2 パス目の指摘の採否」。周の中で手を入れる対象は CR2-1・CR2-2・CR2-4 ＋記録の訂正 CR2-5。
- **狭いパスの起点（2 パス目の指摘対応を始める直前の SHA）**: `2508ba482fdd9609f3493851c145189b1f40192a`
- 狭いパス: 済。Verifier 反証 4 件（N1〜N4。採否は人間が決める——§6 の表）。
- 2 パス目の指摘対応: 済。`script_exit_codes` が引用（`'…'`・`"…"`）を外してからコメントを落とし、
  heredoc（`<<EOF`・`<<-'EOF'`）の本文を数えない。変異に「引用の中の `#`」「実際の `exit N` を
  文字列 2 形・heredoc 2 形に置き換え」「heredoc・`<<` 演算の後ろの `exit`」「行末のコメント」を追加。
  **陽性対照**: 1 パス目の版の `script_exit_codes` に差し替えると新しい検査 10 件が赤
  （引用の `#` 2・置き換え 8）。コメントの正規表現を `^\s*#` に狭めると行末コメントの検査 2 件が赤。
  `test-worktree-scripts.py` 緑。
- 割り目 2（2 パス目の前）: AskUserQuestion で提案 → **人間が「ここで割る」を選択**（2026-10-14）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 206` → **2 パス目から**。**残っているのは 2 つ**——手順 5 の当て直し（Verifier 2 パス目）と
  手順 6 の 2 パス目（`/code-review`）。どちらも base `53d06c3` で、受入基準・既知の限界・採否の表をまるごと渡す。
- 交絡: 実験は「`${1:?}` の終了コードが 1」の実測 1 件（引数なしで実行し rc=1）。

## 6. 既知の限界・決着済みの論点

- **スクリプトのヘッダコメントの一覧は突き合わせない**——採らなかった。理由: ヘッダは「何を守るか」の散文で、
  終了コードの網羅一覧ではない（`prepare-worktree.sh` は 5/6/7 だけを挙げる）。
- **「0 以外はすべて『作っていない』」は厳密ではない**——`git worktree add` が成功した後の
  `git -C … rev-parse` が失敗すれば、作ったうえで非 0 になる。この周の範囲外（一覧の番号の話ではない）。

### 1 パス目の指摘の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1=CR1 | `script_exit_codes` が行頭の `exit N` しか数えない（`|| exit 8`・`then exit 8; fi`・`; exit 8`・`exit "$rc"` が見えない） | 示せる——実 `SKILL.md` に対し `foo \|\| exit 8` を足したスクリプトで `exit_lists_agree == True`（両関門が実測） | I3／P2 | **直す** |
| CR2 | P2 の変異が行頭の `exit` の形だけで、P2 を判別していない | 示せる——CR1 の形を足しても変異は緑のまま（同上） | I3／P2 | **直す**（同じ行に置く形の変異を足す） |
| CR3 | 計画の「未証明: なし／BLOCKED: なし」と、I5 の「PR の CI も緑」が満たせないことが食い違う | 計画ファイルの記述（関門は記録を検査しない——手順 6） | 無し（記録） | 残課題——PR コメントで I5 の CI 部分を「満たしていない受入基準（main 由来）」として名指しする |
| CR4 | `prepare-worktree.sh:218` のコメント「文書化した 2/3/5/6」が 7 を欠く | 示せる（行がある） | 無し（ヘッダ・コメントは突き合わせ対象外と決着済み。#148 当時の経緯の記述） | 残課題 |
| CR5 | `find-cycle.py` の 0/1/2 の表は突き合わせていない | 示せない（現状は一致） | 無し（I1 は 2 本のスクリプト） | 残課題 |
| CR6 | 最大の番号が束ねた形（`**6・7:`）だと変異の当て先が無く偽陽性の赤 | 示せない（現在の一覧は束ねていない） | 無し | 残課題 |
| CR7 | 同じ番号の重複・矛盾した記載を集合で潰す | 示せない（現状なし） | 無し | 残課題 |
| CR8 | `exit 256` を 0 に正規化しない・`${FOO:?}`／`${1?}` を引数不足として数えない | 示せない（現状どのスクリプトにも無い） | 無し | 残課題 |

### 2 パス目の指摘の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR2-1 | 引用の中の `#`（`echo "see #206"; exit 8`）で行末まで落ち、同じ行の `exit 8` が数えられない | 示せる——`/code-review` が `exit_lists_agree == True` を再現 | I3／P2 | **直す** |
| CR2-2 | 文字列・heredoc の中の `exit N` を数える（実 `exit 7` を `echo 'caller should exit 7'` に置き換えても一致） | 示せる——同上で再現（Verifier も heredoc・文字列で {9} を観測） | I3／P3 | **直す** |
| CR2-3 | `--exit-code`・`trap '…' exit` が `None` になり偽の赤 | 示せない（現スクリプトに無い。赤側に倒れる） | 無し | 残課題 |
| CR2-4 | P7 の変異が行頭のコメントだけで、行末コメントの分岐を当てていない | 示せる——正規表現を `^\s*#` に狭めても全部緑（`/code-review`） | I3／P7 | **直す**（行末コメントの変異を足す） |
| CR2-5 | 計画の P7 の守り方が実装と食い違う | 記録 | 無し（記録） | 記録を訂正（§3 P7） |
| CR2-6 | `exit_paragraph_span` が最初の `scripts/<name>` に錨を下ろす | 示せない（赤側に倒れる） | 無し | 残課題 |
| CR2-7 | `set -e` 下の 1・「それ以外」の意味が一覧の説明より広い | 示せない（番号の集合の話ではない） | 無し（既知の限界の 2 番目と同じ型） | 残課題 |
| CR2-8 | I5 の CI 部分が未達なのに「未証明/BLOCKED: なし」 | 記録 | I5（CI 部分） | PR コメントで「満たしていない受入基準（main 由来）」として名指し。PR 作成後に main の状態を確かめて判定する |

### 狭いパスの指摘の採否（起点 `2508ba4`。採否は人間が決める）

Verifier（Sonnet・`dev-loop:dev-loop-verifier`）反証 4 件。著者が F1〜F3 を手元で再現した。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | 変数オペランドの `$((a<<b))` が偽の heredoc を開き、以降の行の `exit` が全部消える（2 パス目の修正が持ち込んだ偽の緑） | 示せる——`x=$((a<<b))⏎exit 8` → `{0}` | I3／P2 | 人間が決める |
| N2 | `trap 'exit 7' EXIT`・`eval "exit 7"` の 7 が消える（CR2-3 の「赤側に倒れる」は誤り） | 示せる——`trap 'exit 7' EXIT` → `{0}` | I3／P2 | 人間が決める |
| N3 | 引用・heredoc の判定が行単位——複数行の文字列・`<<\EOF`・1 行に 2 つの heredoc で本文の `exit` を数える | 示せる——`echo "a⏎exit 7⏎b"⏎exit 8` → `{0,7,8}` | I3／P3 | 人間が決める |
| N4 | 素通りした変異: `<<-` のタブ除去を落とす・`(?<!<)` を外す（here-string）——どちらも追加テストに判別する検査が無い。ほか `exit 010` を 10 と読む・`E"OF"` 形の終端語 | 示せる（変異が緑のまま。対照で旧挙動の再現を確認済み） | I3／P7 相当（判別力） | 人間が決める |

- この周の起票: 0 件
