# Issue #1487 — screen-spec: 「外部の profile の行が 2 つある」のテストに、空の行が先の試料と変異を足す

**不在の周**（出所: `/dev-loop:cruise 1508 --absent` の起動。台帳 2026-11-24T01:28:28Z に確かめ、2026-11-24 に再開）。利用者には訊かない。親（cruise #1508）から委譲文で受けた子。
Issue #1487 は #1461 の cruise のフォローアップの Issue（`<!-- cruise-followup: #1461 -->`）。元の Issue #1458・マージした PR #1481・確認の Issue #1486。

作り直しの元: #1486

確かめた線（出所: cruise の確かめた線（台帳 `issue-1508`）。利用者の確認（起動時・2026-11-24T01:28:28Z、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
子はマージしない（親の委譲文）。台帳は書かない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1508`））。
版の上げ方: `screen-spec` を **patch**（0.10.0 → 0.10.1。テストの穴を埋める修正。Issue の指定どおり）。

## 変更範囲

触る:

- `scripts/test-check-screens.py` — `EXT_CASES` に試料 `ext-setting-valued-after-empty`、`MUTATIONS` に変異「空の行が先だと値つきの行を数えない」
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/screen-spec/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1487.md` — この計画

触らない:

- `plugins/screen-spec/scripts/check-screens.py`（本体の振る舞いは正しい——Issue と陽性対照のとおり）
- `plugins/screen-spec/references/`（決まりは変わらない）

依存の追加・更新: なし
仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）

同じことを述べている箇所の数: 1（試料と変異はテストファイルの中だけ。本体の docstring の「守る」は変えない——判定そのものは前からある）。分けない理由: 該当なし。

## デプロイ経路

main へのマージで、プラグインの配布（`marketplace.json` の版）と GitHub Pages（`docs/` の計画ファイル）。`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`。子はマージしない。

## 受入基準

不変条件 × 破りうる経路（入口は `check-screens.py` の CLI と、テストが本体を読み込む・写して変異を当てる経路）:

| # | 不変条件 | 経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| 1 | `python3 scripts/test-check-screens.py` が緑 | テスト全体（試料・references の照合・変異・-OO） | `run-serial.py` 越しに走らせて `OK:` の行 |
| 2 | 変異「空の行が先だと値つきの行を数えない」（`any(values)` → `bool(values[0])`）が試料 `ext-setting-valued-after-empty` で殺せる | `MUTATIONS` のループ | テストの合格（「変異が生き残った」が出ない） |
| 3 | 足す前の版（周の base `089f1b4b` のテスト）では、同じ変異が全試料で生き残る（陽性対照） | 周の base のテストの CASES 全部 | scratchpad の `pc1487.py` で base のテスト 203 件を変異の本体に当てて 0 件が期待どおりでない／新しいテスト 204 件では `ext-setting-valued-after-empty` の 1 件だけ |
| 4 | 新しい試料は本体（変異なし）で期待どおり——`settings.csv` に `外部の profile,` → `外部の profile,org/guide org v1` の順で終了コード 1・「外部の profile: 行が 2 つある」 | `check-screens.py` の CLI | 同じ `pc1487.py` の original の行（期待どおりでない 0 件）とテストの合格 |
| 5 | #1458 の受入基準を破らない（外部の profile を書いていない案件で結果が変わらない・語彙／既定／`重ねる先`／形式の版の違反の名指し・外部の profile の本文を写さない） | 本体は変えない。既存の試料 | 本体の差分 0 行（`git diff 089f1b4b -- plugins/screen-spec/scripts/`）と既存の試料が全部緑 |
| 6 | 版が 3 種類で揃って上がっている | 版 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| 7 | 歯止めを全部回して緑（`check-all.py`） | 全体 | `run-serial.py` 越しの `check-all.py` |

必須要件の掛け算: 受入基準を両方の関門（Verifier・`/code-review`）に × 2 パス（1 パス目の指摘対応が 0 行なら 2 パス目は該当なし）= 4 つの受け渡し。2 パス目で直した行があれば狭いパスにも受入基準をまるごと渡す。

証明できないもの（未証明）: なし。

生成物: なし（テストと版の行だけ。`SKILL.md` の測定値（設計 §8.2）は screen-spec の `SKILL.md` を測らない——`skill-metrics.py --check` で確かめる）。
プロパティテスト: なし（試料 1 件の追加で、入力の空間が広い不変条件ではない）
差分テスト: なし（本体を変えない周。テストを足すだけ）

## 未解決の判断・確認待ち

- 仕様の穴: なし（足す試料と変異は Issue に書いてあり、本体の振る舞いは決まっている）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1487-valued-after-empty-test`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1487`・
  起点 `089f1b4b`・base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `089f1b4b2d38a343045439b90072c16ca5449dc1`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: まだ
- 交絡を潰した手順: 陽性対照（受入基準 3・4）——同じ `pc1487.py`・同じ変異で、base のテストと新しいテストを並べ、変異なしの本体（original）でどちらも 0 件が期待どおりでないこと（試料が環境で落ちていない）を併せて見た

```dev-loop-gates
周の base: 089f1b4b2d38a343045439b90072c16ca5449dc1
```

## 既知の限界・決着済みの論点

- 本体の docstring の「守る」には足さない（決着: 採らない。理由: 判定「値のある行があれば空の行も数える」は前から本体にあり、この周は試料の穴を埋めるだけ）。

## 手順 8 の記録

- この周の起票: 0 件（まだ）
