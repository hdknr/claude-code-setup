# Issue #208 — 「複数の Haiku と Sonnet 5 体に fan-out」がモデル名と体数を固定している

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 5（選択肢 2 の注記）と手順 6（「同時には落ちない」ではない）の 2 箇所の括弧書き・版のバナー
- `plugins/dev-loop/.claude-plugin/plugin.json` — version（patch）
- `.claude-plugin/marketplace.json` — version（patch）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手では書かない）
- `docs/plans/issue-208.md` — この計画ファイル
- `plugins/dev-loop/skills/dev-loop/references/untrusted-input.md` — 31 行目の「`/code-review` 自体が内部でサブエージェントに fan-out する」（**1 パス目の指摘対応で範囲を広げた**。断定のままだと、フォークで走る形を落とす。指摘 R1）

触らない:

- `docs/plugins/dev-loop-design.md` の danger 注記（「Sonnet 5 体の並列」）——同じ形だが Issue の受入基準は `plugins/` 配下。PR コメントの残課題に書く
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
| P4 （1 パス目で追加）置換文が「内部で起動する」だけを述べ、`/code-review` **自体が**フォークされた別実行として走る形を落とす——「起動していないから `Agent` フリー」と読める（I2 を弱める） | 2 箇所と `untrusted-input.md` に「それ自体が別実行として走るか、内部でサブエージェントを起動する」の両形を書く（体数・モデル名は書かない） |
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
- 実装: `e492bfb`（`check-all.py` 33/33 緑）。手順 4 の割り目: 提案済み → **「ここで割る」を選択**
- 関門:
    - Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**（`check-all.py` 33/33 緑・`skill-metrics --check` 緑）
    - `/code-review` 1 パス目（high）: **指摘 6 件**——採否は §6。直す 2 件（R1・R3）
    - 指摘対応: `2676273`（R1・R3。`check-all.py` 33/33 緑）
    - 次: 手順 5 の当て直し（Verifier 2 パス目）**と** `/code-review` 2 パス目の**両方が未**。base は上の SHA のまま
    - 2 つ目の割り目: 提案済み → **「ここで割る」を選択**。再開は手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目から
- 反証・差し戻し: Verifier 0 件。差し戻しなし（指摘対応のみ）
- 交絡: 実験なし

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 設計ドキュメントの同じ記述 | 直さない（残課題） | Issue の受入基準が `plugins/` 配下に限っている |
| 「実装が Opus なら `sonnet`」の例示 | 対象外 | ハーネスの内部構成ではなく、利用者が渡す引数の例 |

### 1 パス目の指摘の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | `untrusted-input.md:31` が「`/code-review` 自体が内部で fan-out する」と断定（SKILL.md の「多くの場合」と食い違う） | 示せる——この周の `/code-review` はハーネスの通知で「forked execution」として起動した（自身が別実行） | I1（内部構成の固定） | **直す** |
| R2 | 計画の P3「grep 0 件」が判別していない（手で除外した後の 0 件） | 計画ファイルの記述。成果物の失敗ではない | 無し（関門は計画ファイルを検査しない） | 残課題 |
| R3 | 置換で「組み込みのレビュースキルもフォークされた別実行」が消え、「内部で起動しないなら `Agent` フリー」と読める | 示せる——R1 と同じ観測（フォークで起動・内部の fan-out は無かったとレビュー体が報告） | I2 | **直す** |
| R4 | 設計ドキュメントの danger 注記を直さない理由が誤り | Issue 本文の受入基準は `plugins/` 配下（`gh issue view 208` で確認。Verifier も同判定） | 無し | 残課題（PR コメントに書く） |
| R5 | 複製数の数え違い（SKILL.md:1131・設計ドキュメント 406 行） | 計画ファイルの記述 | 無し | 残課題 |
| R6 | 残った下位項目が親文の繰り返し | 示せない（冗長の指摘） | 無し | 残課題 |
