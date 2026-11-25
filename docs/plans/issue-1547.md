# Issue #1547 — spec-loop の手順文の条件を docs/design/sources.csv にも揃える

<!-- dev-loop: 子 #1547 -->

不在の周（`/dev-loop:cruise 1540 --absent` の起動。2026-11-25）。親 Issue #1540 の子。#1542（PR #1545）の `/code-review` の指摘 CR1 から起票された世代 1 の行。
線（台帳で確かめ済み）: 直す線=既定／仕様の穴=推奨で決めて起票／マージ=関門を通ればマージ／周の途中の課題=台帳に足して直す／マージ前の判断=推奨で決めて起票（後退・未達を含む）。出所は同起動。
この周は世代 1 の行なので、周の途中で見つけた課題は、受入基準を破る・利用者に見える誤り・この周が持ち込んだ後退のどれかに当たらなければ記録だけ。世代 2 の行は周として回さない。

## 周の在り処

- ブランチ: `issue/1547-spec-loop-design-sources-docs`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1547`
- 切った元の参照: `origin/main`（`refs/remotes/origin/HEAD`）
- 起点コミット: `5734eebe`
- base: `5734eebe3949f081bc7523730ec69c2d07db072f`
- 直す線: 既定（出所: cruise の台帳の確かめた線）

## 変更範囲

触る:
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 見送った見た目の指摘の引き渡しの条件
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 同じ条件（2 箇所）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — `refs` に書かない旨の文の条件
- `plugins/spec-loop/references/spec-scope.md` — 同じ条件（3 箇所）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版（2 行）
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1547.md` — この計画

触らない:
- `plugins/spec-loop/references/tree.md`・`handoff-issue.md`（原本。#1542 で `docs/design/sources.csv` を書いてある）
- dev-loop の `references/spec-gap.md`（Issue 本文のとおり別の Issue。プラグインが違う）
- scripts（振る舞いは変えない。文面だけ）

## 設計（仕様の穴ではない。Issue が 2 案を許している）

条件を「正本の根に `design/sources.csv` があれば」から「正本の根の直下か `docs/` の下に `design/sources.csv` があれば」に揃える。
原本（`tree.md` の「デザインの正本の参照」）を指す書き方でなく、両方のパスを条件に書く案を採った——手順文は原本へ行かずに条件が読めるほうが、発火の見落としが起きにくい。原本を指す書き方との差は小さく、どちらでも Issue の受入基準を満たす。

## 受入基準（不変条件 × 破りうる経路）

| 番号 | 不変条件 | 破りうる経路（入口） |
| --- | --- | --- |
| 1 | `docs/design/sources.csv` に置いた正本でも、見送った見た目の指摘の引き渡しの手順文が発火する条件に読める | req-loop の SKILL.md（382 行付近）、spec-review の SKILL.md（160・455 行付近） |
| 2 | scaffold の SKILL.md の「`refs` に書かない」の文が、`docs/design/sources.csv` に置いた場合も指す | scaffold の SKILL.md（165 行付近） |
| 3 | spec-scope.md の同じ条件（131・133・135 行付近）が揃っている | spec-scope.md |
| 4 | 手順文に「正本の根の `design/sources.csv`」だけを条件にする言い回しが spec-loop の手順文に残らない（`design/sources.csv` を挙げる条件を全部数える） | grep（`design/sources.csv` を含む spec-loop の md。原本の `tree.md`・`handoff-issue.md` は両パスを書いてある） |
| 5 | 版を上げる（spec-loop の `marketplace.json`・`plugin.json`・7 つの `SKILL.md` の 2 行）。`scripts/check-all.py` が通る | `check-plugin-versions.py`・`check-version-bump.py`・`check-all.py` |

### 未証明・BLOCKED

- 未証明: なし（文面の変更で、証明は grep と読みで足りる）。
- BLOCKED: なし。

### 生成物

- 生成物なし（文面だけ。図・スナップショットは触らない）。`SKILL.md` の測定値は `skill-metrics.py --check` で確認する（spec-loop の SKILL.md の節構造は変えない）。

### 規定の数と分けない理由

- 同じ規範（見送った見た目の指摘の条件）の複製: req-loop 1・spec-review 2・scaffold 1・spec-scope 3 = 7 箇所。分けない理由: 1 つの条件を揃える周で、片方だけ直すと食い違うため。
- プロパティテスト: なし（文面の変更）。
- 差分テスト: なし（振る舞いを変えない受入基準は無い。文面だけ）。
- 依存の追加・更新: なし。
- 仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）。
- 形式検査のモデル: なし。

## 既知の限界・決着済みの論点

採否の表（関門の指摘。既定の線: 「示せる」かつ「この周の受入基準を破る」行だけ直す）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| （1 パス目の前） | — | — | — |

## 関門の進捗（再開点）

- 実装: 着手（未コミット）
- PR: 未作成
- 割り目: 訊かない（cruise の周）。割らない。
- 外部レビュー: 未確認
- 交絡を潰した手順: 実験なし

- この周の起票: 0 件（確認の Issue は親が立てる。周の中では起票しない）
