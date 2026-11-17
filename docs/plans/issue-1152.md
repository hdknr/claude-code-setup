# Issue #1152 — spec-loop: 提案書の「前の版からの変更」に画面の表の変更が出ない（#1091 の後退）

**不在の周である**——cruise（親 Issue #1168）の子として回す。出所: `/dev-loop:cruise 1168 --absent` の起動（2026-11-17）。
確かめた線（台帳 `issue-1168`。出所: cruise の確かめた線）:
直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた）/ 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。
#1152 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。
この周はマージしない（親がする）——PR を作り、PR 側の CI が通るのを見るところまで（手順 8 は計画ファイルに書くところまで）。
割り目は訊かない——**割らない（cruise の周）**。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/build-proposal.py` — `changes_section` が画面・項目・遷移の変更を件数の表と節に載せる（表があるときだけ）
- `scripts/test-build-proposal.py` — 試料・変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `docs/plans/issue-1152.md` — この計画

触らない:

- `plugins/spec-loop/scripts/diff-versions.py`（比較そのものは #1091 で行の単位になっている。出さないのは `build-proposal.py` の描き側）
- `references/versions.md`・`tree.md`・`skills/proposal/SKILL.md`（節の説明は「種類ごとの追加・変更・削除」で、画面の種類を足しても偽にならない）
- 仕様書（`spec.md`）・PPTX の「前の版からの変更」の節の作り方は同じ `changes_section` を共有するので、別に直さない

複製の数: 比較の節を描く場所は `changes_section` 1 つ（提案書と仕様書が同じ関数を呼ぶ）。分けない理由: 複製は 1。
依存の追加・更新: なし
仕様の振る舞い: 変えない（正本の `Q&A`・仕様に書かれた機能の利用者に見える振る舞いは変わらない。生成物の欠落を直す。このリポジトリは spec-loop の正本ではなくプラグインの置き場）

生成物: なし（`build-proposal.py` の出力は正本リポジトリで生成するもので、このリポジトリに commit される生成物は無い）。

## 決めたこと（仕様の穴）

- 画面・項目・遷移の節の列は `鍵`・`変化`・`題`・`削除の理由`（`題` は画面だけ画面名、項目・遷移は `—`）。Issue は節の形を決めていない。
  - 選択肢: A) 3 つの種類を同じ形の節にする（推奨）／ B) 種類ごとに列を変える（項目名・遷移元・遷移先も出す）
  - 推奨 A。理由: 受入基準は「その変更が出る」で、中身の列は `docs/v<n>/` を開けば分かる（`diff-versions.py` の「守らないもの」と同じ）。B は項目・遷移の中身（Q&A の番号の列を含む）を決裁者向けの資料に出す入口を増やす。
  - 確認の Issue は立てない（親が立てる）。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）。公開ページ（`docs/`）は触らない。

## 版の上げ方

spec-loop を **minor** で上げる（0.99.0 → 0.100.0。0.x なので壊れる変更も minor。生成物の出力に節が足る）——`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行。
他の周（#1144・#1148・#1149・#1153）が同じプラグインの版を上げうる。マージの直前に main が進んでいたら、**main の先端の spec-loop の版から minor で 1 つ上げた値**にする（親が子に依頼する。cruise の `references/parallel.md` の「版とマージの順」）。

## 受入基準（不変条件 × 経路）

- U1: 画面の表の行を足す・変える・消した v2 の正本で、`build-proposal.py` の「前の版からの変更」の節にその変更が出る（陽性対照: 修正の前の版では出ない）。
- U2: 画面の表を持たない正本では、出力が今と同じバイトのまま。

不変条件 × 入口:

- I1（画面・項目・遷移の追加・変更・削除が件数の表に出る）: 入口は `changes_section` を呼ぶ 2 箇所（提案書 `compose` と仕様書 `compose_spec`）。守り方: 描き側 1 関数で共有。
- I2（画面の表だけが変わった版で「変更はありません」と言わない）: 入口は同じ 2 箇所。守り方: 判定が `shown`（画面の種類を含む）で見る。
- I3（表を持たない正本の出力のバイトが変わらない）: 入口は `diff.changes` が画面の種類を持つかだけ。守り方: `row_kinds` を `diff.changes` にある種類だけにする。
- I4（連鎖で消えた項目・遷移の理由が出る）: `diff-versions.py` の `reason` をそのまま描く。
- 未証明: なし。

## 関門の進捗（再開点）

周の在り処:

- ブランチ: `issue/1152-build-proposal-screens-diff`（参照 `origin/main`）
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1152`
- 起点: `05aa0d5`
- base: `05aa0d5c36b012abe57239ba0f288a47f74083fc`

割り目: 割らない（cruise の周）。

## 手順 8 の記録

- この周の起票: 0 件（関門の指摘で直すに入った行の起票は親が振り分ける。この周では起票しない）
