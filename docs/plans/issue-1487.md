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
- 関門: 1 パス目に渡した（Verifier・/code-review。終点 `3adb0b358af04221f43d3c71066f4d3283ebe63e`——実装のコミット）。1 パス目の指摘対応の起点: `3adb0b358af04221f43d3c71066f4d3283ebe63e`（先に当てた関門に渡した時点の HEAD）
  - 2026-11-24 11:2x（JST）ごろ、利用上限（HTTP 429）で前の親・子・関門の体が一斉に落ち、1 パス目の 2 票は結果が記録されていない——**欠票**。再開した子（11:37 JST）が同じパス・同じ base・同じ起点で取り直した（取り直しはパスに数えない）。
  - 1 パス目（取り直し）の結果: Verifier（`dev-loop:dev-loop-verifier`・sonnet）**反証 0 件**（受入基準 2〜6 一致、1 は走らせず未確認・7 は親が回す。`git status --porcelain` は前後同じ）。`/code-review`（high）**指摘 2 件**（どちらも受入基準を破らない——採否の表）。`git status --porcelain` は前後同じ。
  - 1 パス目の指摘対応: 採否の表で「直す」の行 0 件。`git diff 3adb0b35 -- ':(top)' ':(top,exclude)docs/plans/issue-1487.md'` は空、`git status --porcelain` は計画ファイルだけ——**2 パス目: 該当なし**（理由: 1 パス目の指摘対応の差分 0 行。起点 `3adb0b358af04221f43d3c71066f4d3283ebe63e`）。**狭いパス: 該当なし**。2 つ目の割り目も無し。
  - 受入基準 1 は `/code-review` が `run-serial.py` 越しに走らせて `OK: 試料 204 件・変異 169 件・references の崩し 41 件`（前の子の記録も同じ）。受入基準 7 は子が `run-serial.py` 越しに `check-all.py` を回した——`29/105 本を回した（失敗 0 / 飛ばし 0）`・76 本は CACHED（終了コード 0）。2 本は回している間に入力が変わったとしてキャッシュに記録しなかった（緑の結果は変わらない）。
- PR: #1509。PR 側の CI は全部 pass（deploy は skipping）・`mergeable: MERGEABLE`。外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い——`external-reviews.py` が 3）。
- 交絡を潰した手順: 陽性対照（受入基準 3・4）——同じ `pc1487.py`・同じ変異で、base のテストと新しいテストを並べ、変異なしの本体（original）でどちらも 0 件が期待どおりでないこと（試料が環境で落ちていない）を併せて見た

```dev-loop-gates
周の base: 089f1b4b2d38a343045439b90072c16ca5449dc1
関門: Verifier 1 3adb0b358af04221f43d3c71066f4d3283ebe63e 反証=0
関門: /code-review 1 3adb0b358af04221f43d3c71066f4d3283ebe63e 指摘=2
関門: 2 パス目 該当なし 3adb0b358af04221f43d3c71066f4d3283ebe63e
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

- 本体の docstring の「守る」には足さない（決着: 採らない。理由: 判定「値のある行があれば空の行も数える」は前から本体にあり、この周は試料の穴を埋めるだけ）。

採否の表（1 パス目・取り直し）:

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| /code-review 1: `external_setting` の違反の後の `return False`（check-screens.py:565）を外す変異が、行が 2 つある 3 試料のどれでも素通りする（試料に出てはならない文字列が無い） | 示せる（レビューの体が scratchpad `rv1487/m2.py` で当てて 3 試料とも期待どおりのまま） | 無し（前からある試料の穴。この周の受入基準 2 の変異 `bool(values[0])` とは別の変異） | 残課題（振り分け: 記録だけ——試料の穴） |
| /code-review 1: 隣の試料 `ext-setting-empty-and-valued` は値つきの行が先で、名前と順が逆に読める（新しい `ext-setting-valued-after-empty` と取り違えうる） | 示せない（名前の読みの問題で、失敗の出る入力は無い） | 無し | 残課題（振り分け: 記録だけ——文言） |
| Verifier 1: 反証 0 件 | — | — | — |

## 手順 8 の記録

- この周の起票: 0 件（不在の周。振り分けで直すの行が 0 件——2 件とも記録だけ）

- 切り分けの層: 学び（受入基準 3 の陽性対照の形——base のテストに新しい変異を当てて全試料で生き残ることを示す）は #1458 の周の関門が試料の穴として挙げたものを、親 Issue のフォローアップで 1 周にした形で、切り方は既にそうなっている。戻す先なし。
- 焼き戻す学びなし（周の途中の課題は記録だけの 2 件。PR コメントに残す）。
- 効いた行: R-04（変異を当てて、違反の後の `return False` を外す変異が素通りすると示した）
