# Issue #298 — 関数を改名し旧名だけ誤値で残す実装の試料

#294（PR #297）の狭いパスの指摘 N-1。`red_check` の
`(got, was) != ("missing", "missing")` を `got != "missing"` に弱める変異が、`scripts/test-scaffold.py` で死なない。

## 変更範囲

触る:

- `scripts/test-scaffold.py` — 試料 1 本と `MUTANTS` 1 本
- `docs/plans/issue-298.md`

触らない: `plugins/spec-loop/scripts/scaffold.py`（本体は正しい——Issue のとおり元のコードは 1 を返す）。
`plugins/` に触らないので版は上げない。

## 乗るデプロイ経路

main への merge のみ。`scripts/` と `docs/plans/` は公開サイト（`docs/plans/` は nav 外）と
プラグインカタログのどちらにも載る変更ではない——**反映経路なし**（`docs/plans/` のページ化は既存の周と同じ扱い）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 証拠 |
| --- | --- | --- | --- |
| A | v2 で関数を改名し、実装は旧名だけを誤った値で残す（作業中の版 missing・前の版 fail）と `--red-check` が 1 で「前の版の期待も作業中の版の期待も満たさない」 | `red_check` の食い違いの条件 | 新しい試料が元のコードで緑 |
| B | 上の条件を `got != "missing"` に弱める変異が赤になる | 同上 | `MUTANTS` に足した変異が死ぬ（`test-scaffold.py` の変異の集計） |
| C | 既存の試料・変異がすべて緑のまま | 試料と変異の追加 | `python3 scripts/check-all.py` が緑 |

掛け算: A×B は同じ試料で当てる（変異の対照がその試料）。陽性対照は「元のコードで A が緑」。

未証明: なし。生成物: なし（`test-scaffold.py` は生成物を持たない。`skill-metrics` は `SKILL.md` に触れないので動かない）。

複製の数: 1（試料と変異は 1 ファイルに閉じる）。

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/298-rename-old-wrong-fixture`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-298`、起点 `4dea6b3`、
  base の参照 `origin/main`、base の SHA `4dea6b313fe19552e111f31c641089bcb7002561`
- 関門: 未着手
- 交絡: 未着手

## 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
