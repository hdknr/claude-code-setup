# Issue #302 — #294 より前の `--red-check` の説明を `test-scaffold.py` と `versions.md` から外す

## 変更範囲

触る:

- `scripts/test-scaffold.py` — `--red-check` の節コメント 1 行だけ
- `plugins/spec-loop/references/versions.md` — 「差分の周を始める前に」の 2 文（137 行・145 行）だけ
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.13.0 → 0.13.1）
- `.claude-plugin/marketplace.json` — spec-loop の版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（5 本）
- `docs/plans/issue-302.md`

触らない: `scaffold.py`（docstring と `red_check()` が判定の正）・`README.md`・scaffold `SKILL.md`・`handoff-issue.md`・
`spec-gap.md`（#294 で直してある）・`CLAUDE.md`（#299 で直した）

同じことを述べている箇所の数: 直すのは 3 箇所。`grep -rn 'ほかは緑\|同じことを全部の版' scripts plugins docs CLAUDE.md`
（`docs/plans/` を除く）で当たるのはこの 3 箇所だけ。**場合分けは写さず docstring を指す**ので、
直したあとも写しは増えない。分けない理由: 3 箇所とも同じ 1 つの古い主張で、Issue が 1 件にまとめている。

## 乗るデプロイ経路

main への merge のみ。`versions.md` はプラグインの中にあり、利用者には spec-loop の版（0.13.1）で届く
（`claude plugin update`）。`scripts/test-scaffold.py` は CI だけ。公開サイト（`docs/`）は計画ファイルのみ。
**デプロイ後の確認は「反映経路なし」**（サイトの本文は変わらない。プラグインは版を上げるのが経路）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| A | `test-scaffold.py` の `--red-check` の節コメントが、#294 後の挙動と食い違う主張（「変わったケースだけ失敗し、ほかは緑」）を持たず、判定の本体（`scaffold.py` の docstring）を指す | 節コメント・同じ節の期待値（もう緑・実装済み） | `grep -n 'ほかは緑' scripts/test-scaffold.py` が 0 件。陽性対照: base の同じファイルで 1 件 |
| B | `versions.md` が「変わったケースだけ失敗し、ほかは緑」を持たず、137 行の文が言いたいこと（前の版の時点が崩れていると、v<n> の差分の土台が無い）を、#294 後の挙動と食い違わない形で言う | 「差分の周を始める前に」の節 | 差分を読む。`grep -n 'ほかは緑' plugins/spec-loop/references/versions.md` が 0 件 |
| C | `versions.md` が「`--red-check` が同じこと（前の版の Red テストが実装の上で全部緑）を全部の版について見る」と主張しない。`--red-check` への言及は判定の本体（docstring）を指す | 同上 145 行 | `red_check()`（`scaffold.py`）を読み、v<n-1> と v<n> しか比べないこと・消した機能の前の版の結果を判定に使わないことを確かめる。書き換えた文がその事実と食い違わない |
| D | spec-loop の版が 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 5 本の 2 行）で 0.13.1 に揃う | 版の 3 種類 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| E | 歯止めが全部緑（`test-merge-versions.py` は `versions.md` の定数を見る） | `scripts/check-all.py` | 集計行 |

証明できないもの（未証明）: なし。BLOCKED: なし。
生成物の該当判定: **生成物なし**——`versions.md`・`test-scaffold.py` はどの生成物のソースでもない（図は `diagrams/`、
`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` に依存。spec-loop の `SKILL.md` は版の 2 行だけ触る）。
必須要件の掛け算: 受入基準を Verifier × 1・2 パス目、`/code-review` × 1・2 パス目の 4 つの受け渡しに渡す。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/302-red-check-stale-docs`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-302`、起点 `21bb63b`、
  base 参照 `origin/main` → `21bb63b6974db9698574c924e08b1790d7f1afab`
- 実装: `6d34428` で完了。手順 4 の割り目で `AskUserQuestion` → **「ここで割る」**を選択（2026-10-21）
- `scripts/check-all.py`: 割った時点で走行中（`6d34428`）——**再開後に回し直して集計行を回収する**（E）
- 次: 手順 5（Verifier 1 パス目）と手順 6（`/code-review` 1 パス目）。base `21bb63b6974db9698574c924e08b1790d7f1afab` を渡す
- 反証・差し戻し: なし
- 交絡: 実験なし

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `--red-check` の場合分けを `versions.md`・テストのコメントに写すか | 写さない | 写しは #294 のように本体だけ直って古くなる（#299 と同じ方針。Issue の「直すときの注意」） |

### 1 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1: 145 行の理由（「2 つしか比べず、全部緑かは見ない」）が `red_check()` と部分的に食い違う——追加・変更のケースでは前の版の失敗も 1 にする。代わりにならない本当の理由は時点（v<n> を作る前に走らせると v<n-1> を作業中の版として判定する） | 示せる——`scaffold.py` の `red_check()` の分岐（どちらでも失敗 → 1）と、`main()` の `load(repo, args.upto)`（`--red-check` は `--upto` を取らず最新の版を作業中の版にする） | C | 直す |
| R2: 147 行「v<n> の差分の Red テストが、前の版から持ち越した赤と区別できない」も #294 前の言い方 | 示せない（#294 後も回帰のケースの赤は v<n> で壊したのか前からかを分けないので、文が偽とは言い切れない） | 無し（A〜C は 137・145 行と `test-scaffold.py` を名指し） | 残課題 |
| R3: 145 行の括弧が場合分けを写している（決着済みの論点に反する） | 示せる（R1 と同じ文） | C（「判定の本体を指す」） | 直す（R1 と同じ修正で写しを外す） |
| R4: `README.md:116`・scaffold `SKILL.md:107` の要約が `--in-progress`（#282）を落としている | 示せる | 無し（変更範囲の外。受入基準は手順 3 で固定） | 残課題 |
| R5: 137 行の新しい文が表の 2 行目しか説明せず、v<n> がまだ無いのに「v<n> の Red テストが既に赤い」と言う | 示せる（文の時点の食い違い） | B（137 行の言いたいことを食い違わずに言う） | 直す |
| V1（Verifier の推論の誤り。反証ではない）: 「追加・変更のケースで前の版が失敗しても期待どおり」 | `red_check()` はどちらでも失敗なら 1 | — | 記録のみ（Verifier の結論 C は別の理由で成り立つが、R1 で文を変えたので 2 パス目で当て直す） |
