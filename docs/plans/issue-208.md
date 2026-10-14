# Issue #208 — 「複数の Haiku と Sonnet 5 体に fan-out」がモデル名と体数を固定している

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 5（選択肢 2 の注記）と手順 6（「同時には落ちない」ではない）の 2 箇所の括弧書き・版のバナー
- `plugins/dev-loop/.claude-plugin/plugin.json` — version（patch）
- `.claude-plugin/marketplace.json` — version（patch）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手では書かない）
- `docs/plans/issue-208.md` — この計画ファイル

触らない:

- `docs/plugins/dev-loop-design.md` の danger 注記（「Sonnet 5 体の並列」）——同じ形だが Issue の受入基準は `plugins/` 配下。PR コメントの残課題に書く
- `references/untrusted-input.md`（「`/code-review` 自体が内部でサブエージェントに fan-out する」は体数もモデル名も持たない）
- `Opus` / `sonnet` を「別ティアの例」として挙げている箇所（ハーネスの内部構成ではなく、利用者が選ぶ `model` 引数の例）

**複製の数**: 「`/code-review` が内部でサブエージェントを起動する」を述べている箇所は `plugins/` 内に 3（SKILL.md 2・untrusted-input.md 1）、
内訳を固定しているのは SKILL.md の 2 と設計ドキュメントの 1。**分けない理由**: SKILL.md の 2 箇所は同じ文の複製で、片方だけ直すと食い違う。

## 2. デプロイ経路

- `plugins/`：プラグイン配布（version bump → 利用者の `plugin update`）。
- `docs/`：main への push で GitHub Pages（生成ブロックと計画ファイルのみ）。

## 3. 受入基準

**I1. `plugins/` 配下に、ハーネスの内部構成（`/code-review` などの内部のモデル名・体数）を固定した記述が無い。**

| 経路（その記述が現れうる場所） | 守り方 |
| --- | --- |
| P1 SKILL.md 手順 5 の選択肢 2 の注記 | 括弧書きを「内訳は環境・版で変わる」に置換 |
| P2 SKILL.md 手順 6 の「同時には落ちない」ではない | 同上 |
| P3 `references/*.md`・`prompts/*.md`・`agents/*.md`・README・他プラグイン | grep（Haiku/Sonnet/Opus/「N 体」）で 0 件を確認。別ティアの例示は対象外（§1） |

**I2. 要点「`Agent` が禁止された周では手順 5 と 6 が同時に落ちうる」「`/code-review` を `Agent` フリーの逃げ道にしない」が残っている。**

**I3. 版が 3 箇所で揃って上がり、`check-all.py` が緑。** 生成物（§8.2 の生成ブロック）の鮮度を含む。

**生成物**: 該当あり——`skill-metrics.py` の生成ブロック（SKILL.md の行数が変わる）。`--check` で差分ゼロを確認。drawio は該当なし。

**未証明**: なし。

**掛け算**: 受入基準 × {Verifier, `/code-review`} × {1 パス目, 2 パス目} = 4 つの受け渡し。

## 4. 未解決の判断

- なし

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/208-review-fanout-wording`・worktree `.claude/worktrees/issue-208`・起点 `75516dd`・
  base 参照 `origin/main` → `75516dd8f05d649ceec4f42ef50b417b19e973da`
- 関門: 未着手
- 反証・差し戻し: なし
- 交絡: 実験なし

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 設計ドキュメントの同じ記述 | 直さない（残課題） | Issue の受入基準が `plugins/` 配下に限っている |
| 「実装が Opus なら `sonnet`」の例示 | 対象外 | ハーネスの内部構成ではなく、利用者が渡す引数の例 |
