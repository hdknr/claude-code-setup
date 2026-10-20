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
- 手順 6 の 2 つ目の割り目で `AskUserQuestion` → **「ここで割る」**を選択（2026-10-20）
- `scripts/check-all.py`: 割った時点では結果を回収していなかった（10 分を超えて走っていた）——再開後に回し直した（下）
- 関門 2 パス目（HEAD `ce25fd2` を渡した。base `d45103e`。受入基準・既知の限界・1 パス目の採否の表を両方に渡した）:
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**。A・B・C 一致（B は docstring と `red_check()` の実装まで照合）、
    D は個別 4 本が緑。A・B の根拠は親が当て直して一致
  - `/code-review`: **指摘 7 件・A〜D を破るものは 0 件**。採否は下の表——**7 件とも残課題**（直す行 0 件）
- 狭いパス: **該当なし**（2 パス目で直した行 0 件）
- `scripts/check-all.py`（HEAD `ce25fd2`）: **44/44 本・失敗 0・飛ばし 0**（終了コード 0）。D 充足
- 次: PR
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

### 2 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR5: `plugins/spec-loop/references/versions.md:145` も #294 前の挙動を書く（1 パス目の CR3 は 137 行） | 示せる（`red_check()` は v<n-1> と v<n> しか比べない、と `/code-review`） | 無し（`plugins/` は範囲外） | 残課題 |
| CR6: CR1 の再掲（`scripts/test-scaffold.py:793`） | 示せる | 無し | 残課題（決着済み） |
| CR7: A の証拠の grep が完全一致の 1 句だけで、言い換えた旧主張を判別しない | **示せない**——言い換えは仮定。親が判別できる形で当て直した: `scaffold.py` の項（50〜64 行）の `緑` は現在 0 件、**陽性対照**として base の同じ範囲では 61 行の旧文言が当たる | 無し | 残課題（証拠の当て方は補った） |
| CR8: 計画の「他の 6 箇所は直してある」の訂正も不完全（versions.md:145 が残る） | 示せる | 無し（周の記録は関門の検査対象ではない） | 残課題。残っている旧記述は CR1・CR3・CR5 の 3 箇所と認める |
| CR9: D は `check-all.py` を回収していないので未証明 | 示せる（割った時点で未回収） | D | **再開後に回し直して回収する**（下の再開点）——成果物の修正ではない |
| CR10: `CLAUDE.md:61` の新文言が「前の版の Red テストも同じ実装に当てる」という #294 の要点を落とした | 示せない（偽の主張は無い。要約の粒度の問題） | 無し（A・B・C を破らない） | 残課題（人間レビューで判断） |
| CR11: 指し先「`scaffold.py` の docstring」がリンクでもパスでもなく、機械で見られない | 示せない（いま指し先は実在する。B） | 無し | 残課題 |

この周の起票: 1 件（#302。手順 8 で人間が承認）

手順 7: PR #301 の CI は緑（build・check pass）。マージは人間の承認待ち。デプロイ後の確認: 反映経路なし。
手順 8: 焼き戻す学びなし（「10 分を超える check-all を割る前に回収する」は既存の「起動済みは進捗ではない」で足りる）。
