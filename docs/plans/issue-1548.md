# Issue #1548 — dev-loop の spec-gap.md: デザインの正本の参照の出どころが docs/design/sources.csv の場合を言っていない

**不在の周である**——出所: `/dev-loop:cruise 1540 --absent` の起動（2026-11-25）。cruise の子（サブエージェント）として回す。
使った線（出所: cruise の確かめた線（台帳 `issue-1540`））: 直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す（世代 1 の行は、受入基準を破る・利用者に見える誤り・この周が持ち込んだ後退だけ）/ マージ前の判断 = 推奨で決めて起票。
台帳は書かない（親だけ）。マージは親がする。確認の Issue #1546 は閉じず、閉じるキーワードで指さない。

## 周の在り処

- ブランチ: `issue/1548-spec-gap-docs-design-sources`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1548`
- base: `5734eebe3949f081bc7523730ec69c2d07db072f`

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 「デザインの正本」の節の、参照の出どころを `docs/design/sources.csv` の場合も含む書き方にする（`handoff-issue.md` の「デザインの正本」の 2 点——根か `docs/` の下か・`docs/` の下から読んだ段落は最初の `design/sources.csv` が置き換わる——と食い違わせない）
- `plugins/dev-loop/.claude-plugin/plugin.json` — dev-loop の版 2.25.0 → 2.25.1（patch）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `docs/plans/issue-1548.md` — この計画

触らない: spec-loop 側（別の Issue）・`scripts/test-scaffold-screens.py`（突き合わせる印と見出しは変えない）。

依存の追加・更新: なし

仕様の振る舞い: 変えない

## 受入基準

| # | 受入基準 |
| --- | --- |
| 1 | spec-gap.md の出どころの記述が `docs/design/sources.csv` を含み、handoff-issue.md と食い違わない |
| 2 | 版を揃えて上げ、`scripts/check-all.py` が通る |

## 関門の記録

事実だけを書く。Verifier（opus）1 パス目は先端 565a9a3f に当て、反証 1 件（計画の変更範囲の書き方で `check-plan-scope.py` が赤）を計画ファイルだけの直しで直した。
`/code-review` 相当は general-purpose（opus）を df2e077c に当て、指摘なし（`feature-dev:code-reviewer` に 1 回目を当てたが報告が届かず、読めていない——記録しない）。
直した分への 2 パス目と狭いパスは回していない。直しが計画ファイルだけで、`check-plan-scope.py` が通り、PR 側の CI が全部通ったため。

```dev-loop-gates
周の base: 5734eebe3949f081bc7523730ec69c2d07db072f
関門: Verifier 1 565a9a3f40b08f9e8b5c43f03c98c68948e12b0e 反証=1
関門: /code-review 1 df2e077ca94585bb7b4eeca92a7d3f39465586a6 指摘=0
関門: 2 パス目 該当なし 565a9a3f40b08f9e8b5c43f03c98c68948e12b0e
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界

散文の記述の直しで、読んだ周が正しく扱うかを測る eval は無い。突き合わせは `test-scaffold-screens.py` が印と見出しまで。

## デプロイ経路

main へのマージで配布と Pages（マージは親がする）。

## 件数

- この周の起票: 0 件
