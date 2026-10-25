# Issue #404 — 暫定の回答の印を明示にし、全段が 1 つの判別を読む（#396・#403 のまとめ）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-qa-csv.py` — `is_provisional` を状態だけで決める。文言の印（`PROVISIONAL_ANSWER`・`PROVISIONAL_NOT`・`PROVISIONAL_MARK`）を消す
- `plugins/spec-loop/scripts/qa-to-pptx.py` — 暫定の判別を `qa.is_provisional` に
- `plugins/spec-loop/scripts/check-spec-exit.py` — 同上
- `plugins/spec-loop/scripts/scaffold.py` — 同上
- `plugins/spec-loop/scripts/check-signoff.py` — 同上（照合の 3）
- `plugins/spec-loop/scripts/build-proposal.py` — docstring と決定事項の絞り方
- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — 判別の写し（関数）
- `plugins/spec-loop/references/qa-csv.md` — 「暫定の行の判別」（原本）と段ごとの扱い
- `plugins/spec-loop/references/tree.md` — 「Q&A 表を移す」に暫定の行の移し方（D）
- `plugins/spec-loop/skills/proposal/SKILL.md` — 判別の指し先・暫定の節の説明
- `plugins/spec-loop/README.md` — proposal の 1 行
- `scripts/test-check-qa-csv.py` — 判別の試料（否定の書き方を含む）・読む側の静的な確かめ・参照との突き合わせ
- `scripts/test-build-proposal.py` / `scripts/test-qa-to-pptx.py` / `scripts/test-check-spec-exit.py` / `scripts/test-scaffold.py` / `scripts/test-check-signoff.py` / `scripts/test-init-mkdocs.py` — 同じ行の試料と変異
- `CLAUDE.md` — `build-proposal.py` ほかの行
- `plugins/spec-loop/.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` / `plugins/spec-loop/skills/*/SKILL.md` — 版（minor）
- `docs/plans/issue-404.md` — この計画

触らない:

- `merge-versions.py`・`diff-versions.py`（暫定を判別しない）
- `scaffold.py` の前の版の確かめ（#361。`反映済み` でない行を見る——暫定を含む。判別ではなく「確定か」）
- `REFLECTED`（反映した状態の定義。暫定の判別とは別）
- Q&A 表の見出し・状態の種類

### 同じことを述べている箇所の数

- 暫定の判別: `qa-csv.md`（原本）・`check-qa-csv.py`（実装 1 か所）・フックの写し・`build-proposal.py` docstring・proposal SKILL・README・CLAUDE.md の **7 箇所**
- 段ごとの扱い（止める／印を付けて通す）: `qa-csv.md`（新しい表。原本）・`spec-exit.md`・`signoff-tags.md`・`spec-ir.md`・`versions.md`・各スクリプトの docstring
- **分けない理由**: #396 と #403 は「印を何で表すか」と「どの段が読むか」の同じ決定の 2 面（Issue 本文）。原本を `qa-csv.md` に置き、ほかは指すだけにする。既存の `spec-exit.md` ほかは**意味を変えない**（もともと `暫定反映` で書いてある）ので触らない

## 乗るデプロイ経路

main へのマージ。プラグインは利用者の `plugin update` で届く（サイトのページは触らない）。

## 設計の決定（関門に渡す）

- **D1 暫定の行 = `状態` が `暫定反映` の行だけ。`回答` の文言は見ない。**（人間が 2026-10-25 に選んだ。選択肢は「状態だけ」と「`回答` の先頭の決まった印」）
  理由: #374 で文言の一致を 2 形試し、活用語尾で除く形は肯定を取りこぼし、列挙の形は否定を取りこぼした（#403）。
  状態はもともと全段が読む明示の印で、既存の決まり（#325: 残るうちはサインオフを付けない・scaffold は止まる）がそのまま効く。
- **D2 段ごとの扱い**（原本は `qa-csv.md` の新しい表。既存の決まりの写しで、意味は変えない）:
  レビュー会の資料 = 載せて「暫定」と印を付ける／条件 1 = 反映済みに数えて件数を出す（止めない）／
  照合 = 3 で止める／提案書 = 照合の 3 で作らない（通った時点で暫定の節は 0 件。節は残す——#366）／
  scaffold = 止める／MkDocs の表 = 件数に分けて出す。
- **D3 `反映済み` で `回答` に「暫定で採用」と書いた行は、確定の行として扱う。** 既存の表にあれば人間が確かめて移す（`tree.md` の「Q&A 表を移す」）。
  道具は作らない——確かめたかどうかは表に無く、機械では決められない。
  **検査（`check-qa-csv.py`）で「反映済み に 暫定 の語」を落とすことはしない**——文言の一致に戻り、確定した経緯の書き方（「暫定で採用していた B を取り下げ」）を落とす。
- **D4 「全段が 1 つの判別を読む」は構造の性質なので、構造で確かめる**——読む側のスクリプトが `is_provisional` を呼び、
  `暫定反映` を直接比べていないことを `test-check-qa-csv.py` が静的に見る。判別を状態だけにしたので、
  写しに戻す変異（`row["状態"] == qa.PROVISIONAL`）は**挙動では殺せない**（同値）。フックは単独で動くので写しを持ち、試料の行で本体と突き合わせる。
- **D5 同じ行の試料**: `反映済み`＋「A（推奨案を暫定で採用。開発側の指示）」（#366 の実データの形）を、資料・条件 1・照合・提案書・scaffold・フックの各テストに通し、
  どれも暫定にしないことを見る。`暫定反映` の行はどれも暫定にする（既存の試料）。

## verify の受入基準

不変条件 × 経路:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | 暫定の判別は状態だけで、`回答` の文言に依らない | `is_provisional` の本体／否定・肯定の書き方の行 | 本体を状態だけに。否定・肯定の書き方を含む試料で全部同じ答え |
| 2 | 判別は 1 か所で、全段がそれを読む | build-proposal・qa-to-pptx・check-spec-exit・scaffold・check-signoff・フック | 各スクリプトが `is_provisional` を呼ぶ（静的な確かめ）。フックは写しを試料で突き合わせ |
| 3 | 同じ行に全段が同じ答えを出す | #366 の形の行／`暫定反映` の行 | D5 の試料を各段のテストで |
| 4 | 段ごとの扱いが既存の決まりと食い違わない | `spec-exit.md`・`signoff-tags.md`・`spec-ir.md`・`versions.md` | `qa-csv.md` の表は写しで、既存の決まりの文は変えない |
| 5 | 決まりの原本が 1 か所で、古い判別（文言）が残らない | `qa-csv.md`・SKILL・README・CLAUDE.md・docstring | grep で「暫定で採用」の判別の記述を引く |
| 6 | 既存の表を移す手順がある | `tree.md` の「Q&A 表を移す」 | 洗い出し・確かめ・タグの取り直し |
| 7 | 判別を外す・段ごとに写しに戻す変異で赤 | 各テストの変異 | 本体の変異は各段のテスト、写しは静的な確かめ |

組み合わせ: 1×2（本体を変えた変異が全段のテストで赤）・2×3（同じ試料を全段に）。

- **証明できないもの（未証明）**: 実案件の表（#366 の 29 行）を移した結果——表がこのリポジトリに無い。
- **生成物**: `skill-metrics.py` の生成ブロック（spec-loop の SKILL は対象外のはず——`--check` で確かめる）・図なし。**`check-all.py` で鮮度を見る。**

## 未解決の判断・確認待ち

- なし（D1 は人間が選んだ）

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/404-provisional-state-only`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-404`・
  起点 `0330977`・base の参照 `origin/main`・base の SHA `0330977fc31ed62314e1dbb8c16f876b946d8e46`
- 実装: 済み（`da67dab`）。`check-all.py` 46/46 緑（ローカル）
- 関門: 1 パス目を起動（Verifier `dev-loop:dev-loop-verifier`・sonnet／`/code-review` high）——報告を回収する前にセッションが切れた（`/clear`）。
  **再開した周で 1 パス目を回し直す**（2026-10-25。`resume.md` の「報告待ちは済んでいない」）——**報告待ち（進捗ではない）**
- 反証・差し戻し: まだ
- 交絡: 実験なし（変異テストは試料の判別を見るもので、主張を支える実験ではない）
- 割り目 1（手順 4 の完了時）: 訊いた（AskUserQuestion）→ **このまま続ける**
- この周の起票: 0 件

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 提案書の暫定の節が常に 0 件になる | 採った（節は残す） | 照合の 3 で止まるので通った時点で 0。#366 の「0 件でも節を出す」と、照合を外した経路の歯止め |
| `反映済み`＋「暫定」の語を検査で落とす | 採らない | D3 |
| 写しに戻す変異を挙動で殺す | 採らない | 同値なので殺せない（D4）。静的に見る |
| 提案書の暫定の節の中身（1 件以上）を CLI の試料で当てる | 採らない（`compose` を直接呼んで当てる） | 照合の 3 の後では到達しない。`test-build-proposal.py` が `compose` に暫定・確定・未決定の 3 行を渡し、節の振り分けの変異 3 本を殺す |
| 公開ページ `docs/plugins/index.md:742` の「中間表現が暫定の回答の Q&A を指していれば止めます」 | 残課題（触らない） | 実際は指すかに依らず止まる（#325 の 2 パス目からの古い記述）。この周の前からある食い違いで、判別の決定ではない |
