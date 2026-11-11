# Issue #965 — qa-to-pptx.py: 手書き部分の太字の行が PPTX に ** のまま出る

不在の周（`/dev-loop:cruise 963 --absent` の起動・2026-11-11T01:02Z、利用者の確認（起動時・2026-11-11T01:02:52Z、配布を見せて確かめた））。cruise #963 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かない）。従う版は dev-loop 1.103.0（キャッシュ。SKILL.md 1861 行）。
元の Issue の本文の先頭は `<!-- cruise-found: #963 -->`（#958 の周の `/code-review` 1 パス目 CR-6 から足した行・世代 1）——この周で見つけた行は found-lines.md の「後続の後続」のとおり、3 つに当たらなければ記録だけ。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-963`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上）。Issue 本文は「仕様の穴ではない（`###` を太字にする既存の扱いに揃える）」——選択肢 A を採る
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。台帳は親が書く——足すべき行は報告に並べる）
- マージ前の判断: **推奨で決めて起票**（出所: 同上。子は推奨と理由を PR コメントに書き、確認の Issue は立てない）
- 実機確認: 台帳に線なし
- 版の上げ方: **patch・spec-loop だけ**（main の先端 spec-loop 0.77.1 → 0.77.2。利用者に見える出力の誤りの修正）。dev-loop は触らない。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方（patch）で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #965`・`Refs #963`
- 並行する周: #917・#957（別の worktree。触らない。#957 も spec-loop を触るので版が衝突しうる）
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/cruise/scripts/run-serial.py` 越し

## 周の在り処

- ブランチ: `issue/965-bold-line-pptx`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-965`
- 起点コミット: `54db6276`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `54db627615a59d96278055ff7dc476562cfe643c`

## 変更範囲

触る:
- `plugins/spec-loop/scripts/qa-to-pptx.py` — `markdown_slides` が太字の行（`**…**` だけの行）を太字の段落にする・docstring
- `scripts/test-qa-to-pptx.py` — 太字の行の試料と観測・変異
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-965.md` — この計画

触らない:
- 行の中の部分的な太字（`a **b** c`・`**a** と **b**`）を run に分けること——Issue は「`**…**` だけの行」。writing-style.md は箇条の中の太字を使わない決まり
- 番号つきの項の 1 行目（`1. **…**`・`4a. **…**`）の太字——Issue の受入基準の外（行が `**` で始まらない）。必要なら別の行
- `tree.md` の PPTX の 1 行（「見出しごとに 1 枚」）——太字の扱いを写していない（grep で確かめた）
- `build-proposal.py`——`markdown_slides` を読むだけで、太字の行の扱いを持たない

複製の数（同じことを述べている箇所）:
- 「Markdown の何を太字にするか」は `markdown_slides` の docstring と本体の **1 箇所**（`tree.md` は写していない）。分けない。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージでプラグインのカタログに入る（`docs/plans/` は公開サイト）。マージは親。

## verify の受入基準

不変条件 × 経路（入口は `markdown_slides` の行の分岐: 表紙の本文・節の本文・引用・コードフェンス・表・見出し・画像。呼び出し元は `build-proposal.py --pptx` の提案書と仕様書の 2 本）:

A. **太字の行（前後の空白を除いて `**…**` だけで、中に `**` を含まず、内側の両端が空白でない行）は、PPTX に `**` を含まず、太字の run（`b="1"`）として出る**（Issue の受入基準）
  - A1. 節（`##`）の本文の太字の行
  - A2. 表紙の本文（最初の `##` までの行）の太字の行
  - A3. 引用の中の太字の行（`> **…**`）——引用の印を外した後で同じ扱い
  - A4. `build-proposal.py --pptx` の経路（提案書・仕様書）で、手書き部分の太字の行が `**` を含まない——走らせて確かめる
B. **太字の行でない行は今までどおり**
  - B1. コードフェンスの中の `**…**` は字句のまま（太字にしない・`**` を残す）
  - B2. 行の中の部分的な太字・2 つの太字（`**a** と **b**`）・flanking で太字にならない形（`** a **`）は変えない（字句のまま・太字でない）
  - B3. `###` の行・表の行・画像の行の扱いは変わらない（既存のテスト `test-qa-to-pptx.py`・`test-build-proposal.py` が緑）
C. **回帰テスト**: `scripts/test-qa-to-pptx.py` に試料を足し、直す前の版（`qa-to-pptx.py` の base の版）で赤になる（陽性対照）。太字の行の扱いを外す変異で赤になる
D. **版**: 3 種類（`marketplace.json`・`plugin.json`・spec-loop の `SKILL.md` 6 本）が 0.77.2 で揃う（`check-plugin-versions.py`）
E. **歯止め全部**: `python3 scripts/check-all.py`（run-serial 越し）が緑・PR 側の CI が緑

証明できないもの（未証明）: PowerPoint・LibreOffice で太字に描かれること（CI にアプリが無い。XML の `b="1"` までを見る——既存の「守らないもの」の表と同じ）。

生成物の該当: リポジトリに置く生成物なし（PPTX は実行時の出力でリポジトリに無い。図・`skill-metrics.py` の生成ブロックは spec-loop の `SKILL.md` に依らないが、`skill-metrics.py --check` は check-all で回る）。

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方 × 1・2 パス目（2 パス目が該当なしなら初回の 2 つ）。

## 未解決の判断・確認待ち

- なし（仕様の穴なし——Issue が選択肢 A を採ると決めている）

## 関門の進捗（再開点）

- 割り目（手順 4・6）: 割らない（cruise の周）
- 実験: なし（走らせて確かめるのは受入基準の確認で、否定的な結果を主張に使う実験はない）

## 既知の限界・決着済みの論点

- 行の中の部分的な太字・番号つきの項の太字は扱わない（採らなかった。理由: Issue の受入基準は「`**…**` だけの行」。変更範囲の「触らない」）
- アプリでの見た目は見ない（採らなかった。理由: 既存の「守らないもの」の表と同じ。XML の `b="1"` まで）
