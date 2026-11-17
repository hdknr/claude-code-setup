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
- 1 パス目: Verifier（dev-loop-verifier・opus）反証 1 件・/code-review（high）指摘 5 件。どちらも終点 dbad420
- 1 パス目の指摘対応の起点: dbad420f8a18c118c136b1ec8b6c8852d17f0aef。直す行 0 件のため成果物の差分 0 行（計画ファイル以外）
- 2 パス目: 該当なし（1 パス目の指摘対応の差分 0 行。直す行が 0 件）
- 狭いパス: 該当なし
- 反証・差し戻し: 手順 4 への差し戻しなし
- 交絡: 実験なし

```dev-loop-gates
周の base: 05aa0d5c36b012abe57239ba0f288a47f74083fc
関門: Verifier 1 dbad420f8a18c118c136b1ec8b6c8852d17f0aef 反証=1
関門: /code-review 1 dbad420f8a18c118c136b1ec8b6c8852d17f0aef 指摘=5
関門: 2 パス目 該当なし dbad420f8a18c118c136b1ec8b6c8852d17f0aef
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
マージの反映: なし
```

## 既知の限界・決着済みの論点

直す線: 既定（示せる かつ 受入基準を破る行だけ直す）。採否の表:

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR-1 tree.md の手当て `git ls-remote --tags origin` は未 push のローカルタグを見せず、停止条件を黙って飛ばしうる | 示せない（git の性質の主張。実際に停止条件を飛ばした実行は無く、tree.md は未 push のタグを映らないと明記し利用者が確かめると書いた） | 無し（基準 3 は「止まることと手当て」） | 残課題 |
| CR-2 `GIT_TAG_LIST_NOTE` に未 push タグの注意が無い | 示せない（同上） | 無し | 残課題 |
| CR-3 managed のみの規則では `.claude/settings.local.json` の層が無視される | 示せない（実行して示していない） | 無し | 残課題 |
| CR-4 autopilot の `SKILL.md` 手順 1 は層を名指さない | 示せない | 無し（案の文面は出力にあり、スキル本文は案を持たない決まり） | 残課題 |
| CR-5 tree.md の注記がコロンと番号つきの列の間にある・実測していない主張を断定で書いた | 示せない | 無し | 残課題 |
| V-R1 `Bash(gh issue create:*)` の案は scaffold スキルの手順 3（`gh issue create`）も止める | 示せる（`rule_matches` が True）。ただし #1046 から在る案で、この周の変更が持ち込んだものではない | 無し（受入基準は層と `git tag --list`） | 残課題 |

決着: `git ls-remote --tags origin` を手当てに採った理由は、Issue の提案がそれを挙げているため。未 push のタグの注意は tree.md に書いた。

## 手順 8 の記録

- 切り分けの層: 学びなし（案の文面と手当ての修正で、仕事の切り方の問題ではない）
- この周の起票: 0 件（関門の指摘はすべて残課題。起票は直すの行だけ）
