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
- 関門: 未着手
- 反証・差し戻し: なし
- 交絡: 実験なし

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `CLAUDE.md` に判定の場合分けを写すか | 写さない | 写しは #294 のように本体だけ直って古くなる。`CLAUDE.md` の作法（「〇〇を正とする」）に合わせる |
