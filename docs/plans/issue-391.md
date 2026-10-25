# Issue #391 — 実装役の委譲文テンプレートを prompts/ に足し、起動文を「参照＋差分」にする

#389（オートクルーズ）の要件候補 2 を分けたもの。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/prompts/implementer.md` — 新規。手順 4 の実装役に渡す文面（指摘対応の差し込みを含む）
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「使い方」に参照＋差分の渡し方への指し先を 1 行（`---` より下の本文は変えない）
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 同上
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 原則（委譲文の渡し方 2 つと、参照＋差分を選んだときの条件）・手順 4（実装の委譲に `prompts/implementer.md`・指摘対応を返すとき）・版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/untrusted-input.md` — 委譲先の一覧に手順 4 の実装役を足す
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（minor。手順の追加）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — 委譲先の表に実装役を足す・§8.2 の生成ブロック（`skill-metrics.py` で書き直す）
- `CLAUDE.md` — 「委譲文は `prompts/` に置く」の 2 本の列挙に `implementer.md` を足す
- `docs/plans/issue-391.md` — この計画

触らない:

- `agents/dev-loop-verifier.md`（Verifier の定義。渡し方が変わっても定義の中身は変わらない）
- `/code-review` 本体の挙動・`check-*.py` の歯止め（参照の形を機械で見る検査は作らない——渡すのは実行時の委譲文で、リポジトリに残らない）
- description（`plugin.json`・`marketplace.json`・frontmatter）——要約に足すほどの規範ではない
- 台帳・stacked・マージ（#390・#392・#389 の範囲）

### 同じことを述べている箇所の数

- **委譲文のファイルの列挙**: `CLAUDE.md`・設計ドキュメント §8.2 の生成ブロック（生成）の 2 箇所。`SKILL.md` は 1 本ずつ名指しで指す。
- **渡し方（参照＋差分）の規定**: 原本は `SKILL.md` 原則の 1 箇所だけ。`prompts/` の 3 本は「使い方」でそこを指す（3 箇所の指し先）。
- **委譲先の一覧**: `references/untrusted-input.md` と設計ドキュメントの表の 2 箇所（既存の複製。両方に足す）。
- **実装の委譲で委譲文に書く 4 つ**: `SKILL.md` 手順 4（原本）と `prompts/implementer.md`（実装）の 2 箇所。
  分けない理由: 規定と委譲文で役が違う（verifier.md・review-handoff.md と同じ構成）。

## 設計の決定

- **参照＋差分は任意の渡し方**（利用者の決定。2026-10-25 の `AskUserQuestion`）。貼る形も残す。選んだときの条件は必須。
- **参照するのは、親が従っているスキルの base ディレクトリのファイル**（著者の決定）——リポジトリの `plugins/` とキャッシュの版が違うことがある（この周の親は 1.37.0 のキャッシュから起動している）。
- **子が読めたことは、子の報告（読んだファイルの行数）と親の `wc -l` で照合する**（著者の決定）。読めなければ子は止まる。
- **`---` より上は親向けの説明**（著者の決定）。参照の形では子に「`---` より下が指示」と渡す。
- **実装役は push・PR・マージをしない**（著者の決定）。それは親の手順 6・7。

## 乗るデプロイ経路

main へのマージ → (a) プラグインのカタログ（利用者は `claude plugin update`）、(b) `docs/`・`CLAUDE.md` は GitHub Pages の自動デプロイ（`docs/` のみ）。

## verify の受入基準

不変条件 × それを破りうる経路。経路は「`prompts/` の委譲文が子に渡る入口」から数える。

1. **実装役の委譲文に、手順 4 が「委譲文に書く」と定めた要件が全部ある**——worktree 上で作業する・受入基準に照らす（緩めない）・
   信頼できない入力の扱い・変更範囲の外へ黙って出ない・仕様の穴を実装で決めない。`SKILL.md` 手順 4 と `prompts/implementer.md` が食い違わない。
   経路: 手順 4 の `Agent` への委譲・プランニングプラグインの実行フェーズへの委譲・指摘対応を実装役に返す（`SendMessage`）・新しい実装役に指摘対応を渡す
2. **参照＋差分を選んだとき、貼る形で渡るものが 1 つも落ちない**——(a) 絶対パス（親が従っている版）、(b) すべての `{{ }}` に値、
   条件つきの差し込みは「入れる／入れない」を明示、(c) `---` より上は親向けと伝える、(d) 子が読んだ行数を報告させ親が照合、
   (e) 読めなければ子は止まる。
   経路: 手順 4 の実装役・手順 5 の Verifier（1・2 パス目・狭いパス）・多レンズの各体・手順 6 の `/code-review`・レビューの fan-out・
   `Workflow` のノード・再開した周（新しい子）・指摘対応の `SendMessage`
3. **貼る形は変わらない**——`verifier.md`・`review-handoff.md` の `---` より下は変えない（`test-worktree-scripts.py` の形の検査が緑）
4. **`prompts/` に必須マーカーが無い**（`check-norm-markers.py`）
5. **委譲先の一覧に実装役が載る**（`untrusted-input.md` と設計ドキュメントの表の両方）
6. **指摘対応を実装役に返すときは、採否の表で「直す」とした行だけを渡す**（残課題を直させない）。`SKILL.md` と `implementer.md` が食い違わない
7. **構造の歯止め**: 版 3 種の一致・§8.2 の生成ブロックの鮮度・指し先の実在（`prompts/implementer.md`・散文の指し先）——`python3 scripts/check-all.py` が緑
8. **必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目の両方で渡す（4 つの受け渡し）

### この環境では証明できないもの（未証明）

- **実際の子が、参照の形で渡されたテンプレートを読み、条件を守るか**（振る舞い）。#389 の周では実際に使われたが、
  この周ではケースを作らない（`claude plugin eval` は worktree 隔離セッションから起動できない。CLAUDE.md）。受入基準は文面とその整合に置く

### 生成物の鮮度

- **該当あり**: 設計ドキュメント §8.2 の生成ブロック（`skill-metrics.py`）。`SKILL.md` と `prompts/` を編集するので書き直し、`--check` で見る
- drawio の書き出し: 該当なし（図を触らない）

## 未解決

- なし

## 手順 8

- この周の起票: 0 件

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/391-implementer-prompt`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-391`・
  起点 `f21e2eb`・base の参照 `origin/main`・base の SHA `f21e2ebac131f21af533f581d3d941d89f198ae7`
- 直す線（この周）: 既定（出所: 手順 3 の `AskUserQuestion` の回答）
- 手順 4 実装: 済（`075b0ef`）。`check-all.py` 47/47 緑
- 割り目（手順 4）: 訊いた → 「ここで割る」
- 再開したらすること: 手順 5 Verifier 1 パス目・手順 6 `/code-review` 1 パス目（どちらも base `f21e2ebac131f21af533f581d3d941d89f198ae7`）
- 交絡を潰した手順: 実験なし

## 既知の限界・決着済みの論点

- **参照の形を機械で検査しない** → 採らない。委譲文は実行時に組まれ、リポジトリに残らない
- **参照の形を既定にしない** → 採らない（利用者の決定）。`/code-review` に `Read` が使えるかを確かめていない経路がある
