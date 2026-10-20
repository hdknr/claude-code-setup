# Issue #299 — `CLAUDE.md` の `scaffold.py` の説明を `--red-check` の判定の本体へ向ける

## 変更範囲

触る:

- `CLAUDE.md` — プロジェクト構成の `scaffold.py` の項の `--red-check` の 1 文だけ
- `docs/plans/issue-299.md`

触らない: `plugins/`（`scaffold.py` の docstring・`README.md`・scaffold `SKILL.md` は #294 で既に直っている。
版の bump も要らない——`plugins/` に触れない）

同じことを述べている箇所の数: `CLAUDE.md` の 1 箇所。`--red-check` を説明する他の 6 箇所
（`README.md`・scaffold `SKILL.md`・`handoff-issue.md`・`versions.md`・`spec-gap.md`・docstring）は #294 の周で直してあり、
この周の範囲の外。**列挙を写さず docstring を指す形にする**のは、`CLAUDE.md` に写しを 1 つ増やさないため。

## 乗るデプロイ経路

main への merge のみ。`CLAUDE.md` は公開サイト（`docs/`）にもプラグインにも載らない。**デプロイ後の確認は「反映経路なし」。**
（`docs/plans/` は `mkdocs.yml` の nav に無い計画ファイルで、サイトに出るかは既存の扱いに従う。）

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| A | `CLAUDE.md` の `--red-check` の説明が、#294 後の挙動と食い違う主張（「変わったケースだけ失敗し、ほかは緑」）を持たない | `CLAUDE.md` の `scaffold.py` の項・同じファイルの他の `--red-check`／scaffold の言及 | `grep -n 'red-check\|変わったケースだけ' CLAUDE.md` |
| B | 説明が判定の本体（`scaffold.py` の docstring）を指し、指し先にその判定（前の版の Red テストを同じ実装に当てる・もう緑の名指し・`--in-progress`）が実在する | 指し先のファイル | `plugins/spec-loop/scripts/scaffold.py` の docstring を読む |
| C | 書き換えた文が、残す主張（`--check --upto <n-1>` で前の版の時点の鮮度）を落とさない | 同じ括弧の中 | 差分を読む |
| D | 歯止めが全部緑（`check-duplicate-counts.py`・`check-site-links.py` など、`CLAUDE.md` を見るものを含む） | `scripts/check-all.py` | 集計行 |

証明できないもの（未証明）: なし。BLOCKED: なし。
生成物の該当判定: **生成物なし**——`CLAUDE.md` はどの生成物のソースでもない（図の書き出しは `diagrams/`、
`skill-metrics.py` の生成ブロックは `SKILL.md` に依存）。
必須要件の掛け算: 受入基準を Verifier × 1・2 パス目、`/code-review` × 1・2 パス目の 4 つの受け渡しに渡す。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/299-claude-md-red-check`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-299`、起点 `d45103e`、
  base 参照 `origin/main` → `d45103ee635b2bcf5eccaacf1a8d36f6937b7b90`
- 実装: `884c70a` で完了。手順 4 の割り目で `AskUserQuestion` → **「ここで割る」**を選択（2026-10-20）
- 関門 1 パス目（HEAD `6506405` を渡した。base `d45103e`）:
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**。A・B・C 一致、D は個別 5 本が緑（`check-all.py` は親が回す）
  - `/code-review`（受入基準を渡した）: **指摘 4 件・A〜D はすべて満たす**。採否は下の表——**4 件とも残課題**（直す行 0 件）
- 2 パス目の判定: **回す**。起点の SHA を 1 パス目の関門に渡す前に再開点へ書いていなかったので、
  #284 の「0 行なら回さない」は使えない（リポジトリの `SKILL.md` 1.41.1。読み込まれている版は 1.37.0 で、そもそもこの規定を持たない）
- 次: 手順 6 の 2 つ目の割り目（`AskUserQuestion`）→ Verifier 2 パス目・`/code-review` 2 パス目
- 反証・差し戻し: 反証 0 件・差し戻しなし
- 交絡: 実験なし

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `CLAUDE.md` に判定の場合分けを写すか | 写さない | 写しは #294 のように本体だけ直って古くなる。`CLAUDE.md` の作法（「〇〇を正とする」）に合わせる |

### 1 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: `scripts/test-scaffold.py:793` の節コメントが旧主張「変わったケースだけ失敗し、ほかは緑」のまま | 示せる（同じ節の 796 行「もう緑 3 件」・831 行「実装済み 1 件」と食い違う） | 無し（A の範囲は `CLAUDE.md`） | 残課題 |
| CR2: 計画の「他の 6 箇所は #294 で直してある」が誤り（CR1・CR3 が残っている） | 示せる | 無し（周の記録は関門の検査対象ではない） | 残課題。**計画の記述は誤りと認める**——「同じことを述べている箇所の数」の節は書いた時点の見積りで、実際には CR1・CR3 の 2 箇所が残っていた |
| CR3: `plugins/spec-loop/references/versions.md:137` が「変わったケースだけ失敗し、ほかは緑」と書く | 示せる（`handoff-issue.md` の #281・#282 の扱いと食い違う、と `/code-review`。Verifier は「前の版の健全性の議論で矛盾しない」と読んだ——読みが割れている） | 無し（`plugins/` は範囲外。触れば版の bump が要る） | 残課題 |
| CR4: `CLAUDE.md:61` の新しい文言が「先に `scaffold/` の鮮度を見て古ければ 1」を落とした | 示せない（指し先の docstring 44 行にある。要約が全部を写さないのは決着済みの論点のとおり） | 無し（A・B・C を破らない） | 残課題 |
