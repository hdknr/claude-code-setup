# Issue #1581 — screen-spec: 外部の語彙と core の決まった値（種別・ステータス）に共通する値が無い profile を止める

**利用者が不在の周**（cruise の子。出所: `/dev-loop:cruise 1583 --absent` の起動、2026-11-26T08:52:16Z。親 Issue #1583）。読み込んだ dev-loop は 2.26.0（`SKILL.md` 1969 行）。

直す線: `既定`（出所: cruise の台帳の確かめた線——親 Issue #1583 の `cruise:` の行を利用者が起動時に確かめた）。
台帳の確かめた線: 直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた）/ 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）。実機確認の線は無い。
版の上げ方: `screen-spec` を **patch**（0.12.0 → 0.12.1。#1571 の止め方の穴を塞ぐ不具合の修正。マージの直前に上げ直すなら、main の先端の版から patch で 1 つ上げる）。

Issue 本文（外部入力。作者は利用者本人。#1571 の 2 パス目の /code-review の残課題から起票）から読んだ要件: `load_external` で、`種別`・`ステータス` の外部の語彙と決まった値の共通部分が空なら 4 で止める。
止めないなら、理由を書き直す。→ 止める（Issue の提案のとおり）。

## 変更範囲

触る:

- `plugins/screen-spec/scripts/check-screens.py` — `load_external` で、`screens.csv` の決まった値の列（`種別`・`ステータス`）の外部の語彙と決まった値の共通部分を照らす。守る／守らないは docstring
- `plugins/screen-spec/references/profiles.md` — 行の種類の説明と「読めないとき」に足す（決まりの原本）
- `scripts/test-check-screens.py` — 試料・変異
- `scripts/test-write-screens.py` — `init` が共通部分の空な画面の層で書かずに 4 で止まる試料
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/screen-spec/skills/*/SKILL.md` — 版の 2 行（2 本）
- `docs/plans/issue-1581.md` — この計画ファイル

触らない:

- `plugins/screen-spec/scripts/write-screens.py`——`init` は `load_external` を読み込むので、同じ止め方を受け継ぐ（コードは変えない）
- `screen-items.csv`・`transitions.csv` の決まった値の列（`種類`・`必須` など）の語彙——Issue の範囲は画面の表の `種別`・`ステータス`。守らないものに名指す
- `plugins/spec-loop/`、plugin.json・marketplace.json の description
- `CLAUDE.md`——プロジェクト構成の `check-screens.py` の項に 1 句（#1581 の止め方）を足すつもりだったが、その変更を含むコミットが自動モードの分類器に「Undermining Oversight」で 2 回拒まれた（2026-11-26。CLAUDE.md を外したコミットは通った）。不在の周なので変更を外し、足すかは人間に渡す（PR コメントの残課題）。決まりの原本は `profiles.md` と docstring で、CLAUDE.md の項は「#1571 の 4 つ」を列挙したまま 1 つ欠ける（偽ではないが不足）

依存の追加・更新: なし

## 設計の判断

- 照らすのは `SCREEN_FIXED`（`screens.csv` の `種別`・`ステータス`）の列に外部の語彙が在るときだけ。語彙と決まった値の共通部分が空なら 4（`Stop`）。語彙が無い列・共通部分が 1 つでもある列は止めない。
- 止めた理由には、列・語彙の値・決まった値と、語彙の行の ID を名指す。
- 照らすのは画面の層の行を全部読んでから（語彙の行の順に依らない）。既定の照合（#1571）より前に置く。
- 複製の数: 決まりの原本（`profiles.md`）1・本体の docstring（守ること 1 行・守らないもの 1 行）——原本以外は指すだけ。分けない（1 つの規則）。CLAUDE.md の 1 句は外した（変更範囲の「触らない」）。

## verify の受入基準

不変条件 × 経路（入口は `check-screens.py` と、`load_external` を読み込む `write-screens.py init`・`hint`）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | `ステータス` の外部の語彙と決まった値（下書き・記入中）の共通部分が空なら、表の値に依らず検査の前に 4 で止まる | `check-screens.py`（Issue の再現: `S-1,完了だけ,,語彙,screens.csv,ステータス,,完了` を足し、表の値が `記入中` でも `完了` でも） | `load_external` で Stop | 試料（Issue の再現の 2 形。直す前は rc=1） |
| 2 | `種別` の外部の語彙と決まった種別の共通部分が空なら 4 | `check-screens.py` | 同上 | 試料 |
| 3 | 共通部分が 1 つでもあれば止めない（共通の値を書けば通る） | `check-screens.py`（語彙 下書き・完了、表 下書き） | 共通部分で判定 | 試料（陰性対照） |
| 4 | 決まった値の無い列の語彙は照らさない（今までどおり） | `check-screens.py`（既存の `ext-good` ほか） | — | 既存の試料 |
| 5 | 語彙の行の順に依らない | `check-screens.py`（語彙の行を既定・ほかの行の後ろに） | 全行を読んでから照らす | 試料 |
| 6 | `init` が共通部分の空な画面の層で、書く前に 4 で止まる（書かない） | `write-screens.py init --external` | `load_external` を共有 | `test-write-screens.py` の試料（書いたファイル 0） |
| 7 | 止めた理由に列・語彙・決まった値・語彙の行の ID を名指す | 出力 | メッセージ | 試料の期待文字列 |
| 8 | 決まりの原本（`profiles.md`）と docstring が新しい止め方を書き、「守らないもの」の偽の理由（「語彙の外れは語彙の中の決まった値を書けば通る（どの値も違反になる形ではない）」）を正す | 文書 | — | 目視・`check-all.py` |
| 9 | 新しい分岐を外す・緩めると試料が赤になる（変異） | テスト | `MUTATIONS` | `test-check-screens.py` |
| 10 | 既存の試料は今までどおり（後退が無い） | 全テスト | — | `check-all.py` |

- 未証明: なし。BLOCKED: なし。
- 生成物: 該当判定——screen-spec の検査には生成物が無い。`SKILL.md` は版の 2 行だけで、`skill-metrics.py` の対象は dev-loop の `SKILL.md` だけ（`--check` を回して確かめる）。図は触らない。→ 生成物なし。
- プロパティテスト: なし（入力は語彙の有無と共通部分の空・非空の 2 つの境界で、例で尽くせる）。
- 差分テスト: なし（振る舞いを変える周。止める入力を足す）。
- 必須要件の掛け算: 受入基準を Verifier・/code-review の両方 × 1・2 パス目に渡す（2 パス目が該当なしなら初回の 2 つ）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1581-vocab-disjoint-fixed`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1581`・起点 `8ed2f8fe`・base 参照 `origin/main` → `8ed2f8fe646def5a9e494707f780ea809637c27b`
- 実装: `431a0962`（check-all 緑——失敗 0。Issue の再現の試料は直す前の本体で rc=1・直した後で rc=4）
- 割り目（手順 4）: 割らない（cruise の周）——訊かずに「このまま続ける」
- 1 パス目の指摘対応の起点（1 パス目の関門に渡した HEAD）: `431a0962`
- 関門 1 パス目（2026-11-26T09:09Z に起こした）:
  - Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/60512778-ba8a-4b9c-afb8-fadbe195ec94/scratchpad/gate-1581-verifier-1-20261126T090908Z.md`
  - /code-review 1 パス目: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/60512778-ba8a-4b9c-afb8-fadbe195ec94/scratchpad/gate-1581-code-review-1-20261126T090908Z.md`
- 関門 1 パス目を通した（HEAD `431a0962`）——**Verifier 反証 0 件・/code-review 指摘 3 件**（採否は下の表。直す 1・残課題 2）。どちらも報告のファイルに終わりの印つき。`git status --porcelain` は両方とも前後同じ。Verifier は verifier.md 260 行を読んだと報告（`wc -l` と一致）。/code-review は直す前の本体で新しい試料が rc=1 になることを独立に当てた
- 1 パス目の指摘対応: CR1-3 に試料 `ext-status-vocab-overlap-disjoint-first` と変異「語彙の行を読むたびに共通部分を照らす」を足した（変異の本体で試料が rc=4・直した本体で rc=0——陽性対照を著者が当てた）
- 交絡: 実験なし（試料の赤→緑は、直す前の本体と直した本体で同じ試料を走らせた陽性対照）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `screen-items.csv`・`transitions.csv` の決まった値の列（`種類`・`必須`・`種類`（web-spa）など）の語彙の共通部分 | 照らさない（採らなかった） | Issue の範囲は画面の表の `種別`・`ステータス`（#1571 の `SCREEN_FIXED`）。守らないものに名指す |
| 共通部分は空でないが、入口の種別 `top` を欠く `種別` の語彙 | 照らさない | 共通の値を書けば列の違反は消える（入口が無い違反は別の検査が出す）。守らないものに名指す |


### 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1: 守らないものの「入口の種別 `top` を欠く `種別` の語彙」の理由が足りない——共通部分が空でなくても `top` を欠けば、どの表も入口の違反で rc=1（#1581 と同じ形が残る） | 示せる（/code-review の読み。check_reach は top が無ければ違反） | 無し（受入基準は共通部分が空の列。理由の文言は偽ではない——列の違反は消え、入口の違反は入口の検査が出す） | 残課題 |
| CR1-2: 版を patch で上げたが、同じ型の #1571 は minor | 示せる（#1571 の計画の版の上げ方） | 無し | 残課題（計画に「不具合の修正」として patch の理由を書いてある） |
| CR1-3: 不変条件 5（順に依らない）の陰性対照が、重ならない行が先に来る順を持たず、順に依る変異をメッセージの ID でたまたま殺すだけ | 示せる——/code-review が変異を当てて overlap 試料で殺せないと実測 | 5・9 | 直す（試料と変異を足した） |

## 経験の還元（手順 8）

- この周の起票: 0 件（不在の周で、手順 8 の起票は訊かない。起票の候補は `references/found-lines.md` の振り分けで直すに入った行だけで、いまは無い）
