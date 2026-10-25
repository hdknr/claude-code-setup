# Issue #408 — dev-loop: merge-pr.py が終了コード 7 のとき、撤去の失敗を出力しない

PR #406（#389）の 2 パス目の `/code-review` の残課題 R2-2。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py` — 7 で終わるとき、積んだ `problems` も出す。「守る」に 1 行
- `scripts/test-merge-pr.py` — 撤去が失敗し、かつ Issue の読みが失敗する試料。出力に撤去の失敗があることを見る。変異 1 件
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行のみ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.47.0 → 1.47.1。不具合の修正なので patch）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（版の行で動く場合だけ。`skill-metrics.py` が書く）
- `docs/plans/issue-408.md` — この計画

触らない:

- R2-1（撤去に失敗したときにロックを戻さない）・N-1（`CheckRun` の `status` のガードの試料）——Issue の「範囲の外」
- 終了コードの割り当て（7 のまま。7 は 9 より優先する）

### 同じことを述べている箇所の数

- 「7 のとき何を出力するか」: `merge-pr.py` の docstring の終了コード 7 の行と「守る」の行 —— 2 箇所（同じファイル）。`SKILL.md` は指すだけ。
- 分けない理由: 同じファイルの 2 行で、テストが「守る」と変異を 1 対 1 で数える。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` は main への push で Pages。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 7 で終わるとき、それまでに積んだ `problems`（撤去の失敗）が出力に出る | `except Undetermined` の節 | 試料: 偽の `gh` の `pr merge` が worktree に未追跡を置き、Issue の読みが失敗する。出力に `worktree を撤去できなかった` |
| A2 | 上の試料は修正前の本体で赤になる | 試料の設計 | 修正前の本体（`e7aedee`）で試料を流して rc=7・撤去の失敗が無いこと |
| A3 | 7 の他の経路（マージ前の 7・マージ後 MERGED 前の 7）の出力と rc は変わらない | 既存の試料 | 既存の全試料が緑 |
| A4 | 9 の経路（Issue が閉じない）の出力と rc は変わらない | 既存の試料 | 「Issue が閉じなければ 9」が緑 |
| A5 | docstring の「守る」と変異が 1 対 1・新しい変異で新しい試料が赤 | `MUTATIONS` | テストが数える |
| X1 | 版が 3 箇所で揃う・生成ブロックが新しい・全歯止めが緑 | 版・§8.2 | `check-all.py` |

### この環境では証明できないもの（未証明）

- 本物の `gh` での撤去失敗と Issue の読みの失敗が同時に起きる場面——偽の `gh` でしか当てていない（既存の docstring の「守らない」と同じ）。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` の版の行で動きうる）。`skill-metrics.py --check` で見る。他に生成物なし。

### 規定の掛け算

- 受入基準を Verifier と `/code-review` の両方 × 1 パス目・2 パス目 = 4 つの受け渡し。

## 未解決の判断

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/408-merge-pr-undetermined-problems`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-408`・起点 `e7aedee`・base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `e7aedeeb9b22dda924562cd6cbd183f916fbdf20`
- 実装: `5a554dc` でコミット済み。`check-all.py` は 47 本中 46 本が緑で、落ちたのは件数の行の 1 本だけ（行を足したあと、単体で緑）
- 割り目 1（手順 4 の後）: 利用者は「ここで割る」を選んだ（2026-10-25）。次は手順 5（Verifier の 1 パス目）から
- 関門: まだ通していない
- 反証・差し戻し: なし
- 交絡: 実験は A2（修正前の本体で赤）——陽性対照は修正後の本体で同じ試料が緑になること。
  実測: 修正前の本体で新しい試料 2 件のうち「7」だけが赤（rc=7・撤去の失敗が出力に無い）、対照の「9」は緑。修正後は全試料・全変異（13 件）が緑／赤どおり
- この周の起票: 0 件

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| R2-1・N-1 を同じ周で直すか | 直さない | Issue の「範囲の外」 |
