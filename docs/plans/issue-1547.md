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

採否の表（Verifier と `/code-review` の 1 パス目。既定の線: 「示せる」かつ「この周の受入基準を破る」行だけ直す）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V0 Verifier: 反証 0 件。観察 A（CLAUDE.md 207 行ほかに「正本の根の `design/sources.csv`」だけを言う文が残る）・B（実装コミット `cff00b15` の `Verified:` が `Co-Authored-By` と別の段落でトレーラーに読まれない。`検証の関門` は既定 off で影響なし） | A: 示せる（行の読み。手順文ではなく原本・CLAUDE.md の導入文）／B: 示せる（`git log --format='%(trailers:key=Verified)'` が空）が影響なし | 無し（受入基準 4 の対象は spec-loop の手順文） | 残課題 |
| CR1 `docs/` の下の `design/sources.csv` は `docs/v<n>/design/sources.csv`（版の中）とも読める | 示せない（版の中に置くのは `tree.md` が版の外と決めた形の外。ふつうは作られない読み違い。scaffold 165 行は「版の外」を併記済み） | 無し | 残課題（文言） |
| CR2 `CLAUDE.md` 207 行の scaffold.py の説明が「正本の根の `design/sources.csv`」のまま（#1542 の残り。spec-loop の手順文ではない） | 示せる（行の読み） | 無し（この周の変更範囲の外。受入基準 4 は手順文） | 残課題（文言。記録だけ） |
| CR3 計画ファイルの複製数に数え方の注記が無い | 示せない（成果物の誤りではない） | 無し | 残課題（捨てる） |

振り分け（`references/found-lines.md`。PR コメントにも書く）: 直すは 0 件。記録だけは V0 観察 A・B・CR1・CR2（文言。受入基準を破らず、実際の利用でまず起きない）。捨てるは CR3（成果物の誤りではない）。

受入基準の判定: 1〜4 満たす（Verifier が各行を grep と `scaffold.py` の探索の実装との突き合わせで確かめた）。5 満たす（`check-plugin-versions.py`・`check-version-bump.py`・`check-all.py` が通る）。

## 関門の進捗（再開点）

- 実装: 済（`cff00b15`）。歯止め: `scripts/check-all.py` を run-serial 越しに回して失敗 0（35/105 本を回し、70 本は入力が前回の緑から変わっていないので CACHED。PR 側の CI は全部回す）
- PR: 未作成（main を取り込んで `check-all.py` を回してから作る）
- 割り目: 訊かない（cruise の周）。割らない（実装後・2 パス目の前とも）。
- 関門 1 パス目（実装のコミット `cff00b1523ab16499feff9b3881a0c170823fa75` を渡す。以後のコミットは計画ファイルだけ。base `5734eebe3949f081bc7523730ec69c2d07db072f`）:
  - Verifier（`dev-loop:dev-loop-verifier`・opus。実装は sonnet）: 反証 0 件（観察 A・B）。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/6afc4e45-0d5a-49c7-a3a4-03fd099dd38c/scratchpad/gate-1547-verifier-1-20261125T040657Z.md`（呼び出しの結果は「報告を届けずに終わった」の形で、報告はファイルから回収した）
  - `/code-review`（high）: 指摘 3 件（CR1〜CR3）。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/6afc4e45-0d5a-49c7-a3a4-03fd099dd38c/scratchpad/gate-1547-code-review-1-20261125T040657Z.md`
  - 1 パス目の指摘対応の起点: `cff00b1523ab16499feff9b3881a0c170823fa75`。「直す」の行が 0 件なので成果物の差分は 0 行（`git diff cff00b15 -- ':(top)' ':(top,exclude)docs/plans/issue-1547.md'` が空、`git status --porcelain` が空）。
  - 2 パス目: 該当なし（理由: 1 パス目の指摘対応の差分 0 行。起点 `cff00b1523ab16499feff9b3881a0c170823fa75`。判定の 2 本に計画ファイル以外が出なかった）。
  - 狭いパス: 該当なし。
- 外部レビュー: 未確認
- 交絡を潰した手順: 実験なし

- この周の起票: 0 件（確認の Issue は親が立てる。周の中では起票しない）

## 関門の記録

```dev-loop-gates
周の base: 5734eebe3949f081bc7523730ec69c2d07db072f
関門: Verifier 1 cff00b1523ab16499feff9b3881a0c170823fa75 反証=0
関門: /code-review 1 cff00b1523ab16499feff9b3881a0c170823fa75 指摘=3
関門: 2 パス目 該当なし cff00b1523ab16499feff9b3881a0c170823fa75
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
マージの反映: ドキュメントとプラグインの配布
```
