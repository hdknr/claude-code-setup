# Issue #1149 — spec-loop autopilot: deny の案に足す層を名指し、git tag --list も拒むと添える

## 周の在り処

- ブランチ: `issue/1149-autopilot-deny-layer`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1149`
- 起点: `05aa0d5`（origin/main。取り直した）
- 積み先: なし（既定ブランチから切った周）
- 周の base: `05aa0d5c36b012abe57239ba0f288a47f74083fc`
- cruise の周（親 Issue #1168、`--absent`）。割り目: 割らない（cruise の周）

## 直す線と確かめた線

- 直す線: 既定（出所: cruise の確かめた線。台帳 issue-1168。不在の周で、起動は `/dev-loop:cruise 1168 --absent`、2026-11-17）
- 仕様の穴: 推奨で決めて起票（同上）
- マージ: 関門を通ればマージ（配布を見せて確かめた。同上。マージは親）
- 周の途中の課題: 外に出す（同上）
- マージ前の判断: 推奨で決めて起票（同上）
- 仕様の振る舞い: 変えない（spec-loop 自身の点検スクリプトの案の文面。このリポジトリは spec-loop の正本ではない）
- 依存の追加・更新: なし
- 生成物: 生成物なし（`SKILL.md` の測定値は `skill-metrics.py --check` で最新を確認。図・書き出しは触らない）
- 実験: 実験なし
- 同じ規範を述べている箇所の数: 3（`autopilot-check.py` の docstring と案の文面・`references/tree.md` の手当て・テスト）。分けない理由: 小さく、数が少ない
- 版の上げ方: spec-loop を patch（0.99.0 → 0.99.1）。PR ごとに版を上げるリポジトリで、並行する周（#1144・#1148・#1152・#1153）も同じプラグインの版を上げうる。
  マージの直前に main の先端の版から patch で 1 つ上げ直す（親が子に依頼する。cruise の `references/parallel.md` の「版とマージの順」）

## 変更範囲

触る:
- `plugins/spec-loop/scripts/autopilot-check.py` — deny の案に層と git tag --list の添え書き
- `scripts/test-autopilot-check.py` — 案の文面の試料
- `plugins/spec-loop/references/tree.md` — Q&A 表の移行の手順の手当て
- `plugins/spec-loop/skills/*/SKILL.md` — 版の行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1149.md` — この計画

触らない: Claude Code が deny で `git tag --list` を実際に拒むかの実測（範囲の外）／`REFUSED_OPS` の中身／点検の判定の区分

## 受入基準

不変条件: 点検が出す deny の案は、利用者がそのまま足しても他のリポジトリを止めず、移行の手順を黙って止めない。

| 番号 | 基準 | 経路・証明 |
| --- | --- | --- |
| 1 | 案が足す層（正本の `.claude/settings.local.json`）を名指す | `check` の → の行 4 本（`git tag`・`git push --tags`・`gh issue create`・scaffold）すべて。テスト（`test-autopilot-check.py`）の試料 |
| 2 | 案が `git tag --list` も拒むと添える | `git tag` の行だけ（ほかの行には添えない）。`rule_matches` で当たる陽性対照つき |
| 3 | tree.md の Q&A 表の移行の手順に、止まることと手当てがある | 「Q&A 表を移す」の節の冒頭。もう 1 つの節（暫定の行を状態へ移す）は同じ `git tag --list` を打つので、同じ手当てが掛かることを節が指す |
| 4 | テストに案の文面が層を名指すことの試料がある | `test-autopilot-check.py` |
| 5 | 版を上げ、`check-all.py` が通る | 3 箇所の版（marketplace・plugin.json・SKILL.md 7 本）。`check-all.py` を run-serial 越しに |

経路（案を読む入口）: `autopilot-check.py check` の標準出力／点検の docstring／spec-loop の autopilot スキルの本文（案の文面は持たない）／tree.md。
未証明: Claude Code が deny の規則で実際に `git tag --list` を拒むか（範囲の外。判定は写しの `rule_matches` で見た）。

## 未解決の判断

なし

## 関門の進捗（再開点）

- 割り目: 割らない（cruise の周）
- 手順 4 完了: 実装（コミット前）

```dev-loop-gates
周の base: 05aa0d5c36b012abe57239ba0f288a47f74083fc
```

## 既知の限界・決着済みの論点

- なし（関門の採否の表はここに足す）

## 手順 8 の記録

- 切り分けの層: 学びがあれば書く
- この周の起票: 0 件
