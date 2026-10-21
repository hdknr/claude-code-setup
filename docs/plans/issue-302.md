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
- 実装: 未着手
- 反証・差し戻し: なし
- 交絡: 実験なし

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `--red-check` の場合分けを `versions.md`・テストのコメントに写すか | 写さない | 写しは #294 のように本体だけ直って古くなる（#299 と同じ方針。Issue の「直すときの注意」） |
