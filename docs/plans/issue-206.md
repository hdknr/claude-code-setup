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
| P7 コメント中の `exit N`（`# … exit 7`） | 数えない | 行頭（空白のみ許す）の `exit` だけ数える |
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
- 関門: 未着手
- 反証: —
- 交絡: 実験は「`${1:?}` の終了コードが 1」の実測 1 件（引数なしで実行し rc=1）。

## 6. 既知の限界・決着済みの論点

- **スクリプトのヘッダコメントの一覧は突き合わせない**——採らなかった。理由: ヘッダは「何を守るか」の散文で、
  終了コードの網羅一覧ではない（`prepare-worktree.sh` は 5/6/7 だけを挙げる）。
- **「0 以外はすべて『作っていない』」は厳密ではない**——`git worktree add` が成功した後の
  `git -C … rev-parse` が失敗すれば、作ったうえで非 0 になる。この周の範囲外（一覧の番号の話ではない）。
