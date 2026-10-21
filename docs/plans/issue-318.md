# Issue #318 — scaffold の OpenAPI でパスの変数の schema・`<Base>Input`・required を見るテストが無い

## 変更範囲

触る:

- `scripts/test-scaffold.py` — 入口の型の整合を全試料の OpenAPI に当てる検査と、P2〜P4 の変異
- `docs/plans/issue-318.md` — この計画

触らない:

- `plugins/spec-loop/scripts/scaffold.py`（生成は正しい。#318 はテストの穴だけ）。だから**プラグインの版も上げない**
  （`scripts/` の変更は配布物ではない）
- `plugins/spec-loop/references/spec-ir.md`（63〜64 行が既に決まりを持つ。R6 の書き足しは #318 の外）
- 互換性（#319）

### 同じことを述べている箇所の数

決まりは `spec-ir.md` 63〜64 行（原本。触らない）と、テストの検査（新しい関数）と、テストの docstring の「見るもの 5」の 2 箇所。
分けない理由: 検査と docstring は同じファイルの中の同じ 1 つの主張。

## 決めたこと

- **入口ごとに、パラメータとボディを合わせると `<Base>Input` がちょうど復元できる**ことを見る関数を足し、
  `run_case` で exit 0 の全試料の OpenAPI に当てる（`path_params_problem` と同じ置き方）。中身:
  1. `<Base>Input` の `required` が全項目（`object_schema` の決まり）
  2. 各パラメータ（path・query）が `required: true` で、`schema` が `<Base>Input` の同名の項目と同じ（P2・P4 のクエリ）
  3. ボディの型の各項目の schema が `<Base>Input` の同名の項目と同じで、`required` が全項目（P4 のボディ）
  4. パラメータの名前とボディの項目の和が `<Base>Input` の項目とちょうど一致し、重ならない（P3）
- `<Base>` は応答の `<Base>Output` の参照から取る（`pascal()` を写さない）。
- 変異を 4 本足す: path の schema を `{"type": "string"}` に固定・`<Base>Input` を残りの項目に縮める・
  `<Base>Body` の `required` を空にする・クエリを必須にしない。殺すのは試料「パスの変数」。

## 乗るデプロイ経路

テストだけ。プラグインは配布し直さない（版を上げない）。`docs/plans/` を含むので、マージで GitHub Pages にデプロイされる。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | path パラメータの schema が入力の項目の schema と違えば、テストが赤になる | enum を落とす（rank）／型を変える | 検査 2。変異「path の schema を固定」 |
| 2 | `<Base>Input` が入力の全項目を持たなければ赤 | パスの変数を持つ POST／GET | 検査 4。変異「`<Base>Input` を縮める」 |
| 3 | `<Base>Body` の `required` が全項目でない・クエリが必須でなければ赤 | POST の Body／GET・DELETE のクエリ | 検査 3・2。変異 2 本 |
| 4 | 新しい検査が、今の正しい生成のどの試料も断らない（exit 0 の全試料で緑） | 既存の全試料（パスの変数なし・入力が空・全部パスの変数・v2 など） | `python3 scripts/test-scaffold.py` が緑 |
| 5 | 足した変異はどれも名指しした試料で赤になり、壊す箇所が本体にちょうど 1 回現れる | 変異テスト | `MUTATIONS` の既存の仕組み |
| 6 | 歯止めが全部緑 | — | `python3 scripts/check-all.py` |

組み合わせ: 1〜3 × 4（検査を強めても、正しい生成の試料を誤って断らないこと）。

**未証明**: 無し（すべてテストで当てられる）。

生成物: リポジトリに commit した `scaffold/` は無い。`SKILL.md` の測定値は触らない。**生成物なし**。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/318-openapi-path-param-tests`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-318`・
  起点 `21bb63b`・base の参照 `origin/main`・base `21bb63b6974db9698574c924e08b1790d7f1afab`
- 実装: 済み。`test-scaffold.py` は 試料 148 件・変異 101 件で緑（新しい検査が今の生成のどの試料も断らない＝基準 4）
- 反証: —
- 交絡: 実験 1 つ。陽性対照——足した 4 変異を、修正前（`21bb63b`）と修正後のテストの試料「パスの変数」に当てた
  （scratchpad の `ctl318.py`）。無変異は両方緑、4 変異は修正前で全部緑・修正後で全部赤。赤の理由は新しい検査のメッセージ
  （「schema が入力の型と違う」×2・「ボディの型の required が全項目でない」・「query パラメータ limit が必須でない」）。
  観測窓: この 1 試料・各 1 回。「入力の型を縮める」は検査 4（項目の和）より先に検査 2（schema の一致）で赤になる——
  検査 4 だけが殺す変異は足していない

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 生成を直す | 採らない | 生成は正しい。#318 はテストの穴 |
| 応答（`<Base>Output`・`<Base>Error`）の整合も見る | 採らない | #318 の外。パスの変数とは関係しない |
