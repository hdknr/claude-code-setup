# Issue #319 — パスの変数の決まりを足したことで、旧 scaffold の版が v2 を作れない・--check で古くなる

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — 前の版の中間表現にはパスの変数の決まりを当てない（`check_ir`・`read_whole`）
- `plugins/spec-loop/references/spec-ir.md` — パスの変数の節に、前の版の扱いと移行（1 度だけ作り直す）を書く。**決まりの原本**
- `scripts/test-scaffold.py` — 前の版だけがパスの変数の決まりに反する試料・その陽性対照・変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（patch）
- `.claude-plugin/marketplace.json` — 版（patch）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `CLAUDE.md` — 版の刻み方の表に、0.x の方針を書き足す
- `docs/plans/issue-319.md` — この計画

触らない:

- `openapi()` の出力の形（P5: 旧い出力は path パラメータを宣言しない無効な OpenAPI だった。形は保たない——人間の決定）
- `--check --upto <n-1>` の検査（生成するので、パスの変数の決まりを外せない——`input` に無い変数は生成で引けない）
- `references/versions.md`（「差分の周を始める前に」は spec-ir.md の移行の項から指す。列挙を複製しない）

### 同じことを述べている箇所の数

前の版の扱いは `scaffold.py`（実装・`classify` の docstring）・`spec-ir.md`（原本）・`test-scaffold.py`（期待）の 3 箇所。
0.x の方針は `CLAUDE.md` の 1 箇所。分けない理由: 実装と原本と期待は同じ 1 つの決定。

## 決めたこと（人間の決定。2026-10-21、AskUserQuestion）

- **R1**: 前の版には旧い決まりで当てる——`classify()` が前の版の中間表現を検査するときだけ、パスの変数の決まり
  （`check_path_vars`）を外す。前の版の中間表現はケースの比較と前の版の Red テストにしか使わず、OpenAPI を作らない。
  今の版にはそのまま当てる。
- **P5**: 1 度だけ作り直す移行手順を書く。出力の形は変えない。
- **版**: 今回は patch（0.13.1）。`CLAUDE.md` の表に「0.x の間は minor で非互換を含みうる」を書き足す。

## 乗るデプロイ経路

プラグインの版を上げて配布する。`docs/plans/`・`CLAUDE.md` は GitHub Pages のビルド対象（`docs/plans/` はマージでデプロイ）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | 前の版だけがパスの変数の決まりに反し、今の版が直していれば、v2 を作れる（0） | `classify` の前の版の検査／`--red-check` の前の版の Red テスト／`--dry-run` | `read_whole(gate=False)` で `check_path_vars` を外す |
| 2 | 今の版がパスの変数の決まりに反すれば、前の版の扱いに依らず 1 で止まる | v2 で直さない（v1 の誤りを持ち越す）／v1 だけ | `read_whole(gate=True)` は従来どおり |
| 3 | 前の版のほかの決まり（型の誤りなど）は今までどおり前の版にも当たる | 既存の「前の版の中間表現が決まりに反する」 | 外すのはパスの変数だけ |
| 4 | 新しい試料が、外す処理を潰す変異・外しすぎる変異で赤になる | 変異テスト | `MUTATIONS` |
| 5 | 移行の手順が `spec-ir.md` にあり、事実として正しい（作り直すと `--check` が 0 になる。凍結した v1 が反するなら `--check --upto 1` は通らない） | 文書 | 試料で確かめる |
| 6 | 版が 3 種類で揃い、歯止めが全部緑 | bump 漏れ | `python3 scripts/check-all.py` |

組み合わせ: 1 × 2（外すのは前の版だけで、今の版には掛かる）。1 × 3（外すのはパスの変数だけ）。

**この環境では証明できないもの（未証明）**: 実際の利用者の正本リポジトリ（凍結した v1 を持つもの）での動作——手元に無い。試料で代える。

生成物: リポジトリに commit した `scaffold/` は無い（試料は一時ディレクトリ）。`SKILL.md` の測定値は dev-loop だけで、触らない。

## 未解決の判断・確認待ち

無し（3 点とも人間が決めた）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/319-prev-version-path-vars`・worktree `.claude/worktrees/issue-319`・
  起点 `21bb63b`・base 参照 `origin/main` → `21bb63b6974db9698574c924e08b1790d7f1afab`
- 実装: `bc69185` で済み（`test-scaffold.py`: 試料 151 件・変異 99 件で緑）
- 関門: まだ（次は手順 5 の 1 パス目——Verifier と `/code-review` の両方）
- 反証と差し戻し: まだ
- 交絡: 実験 1 件——旧 scaffold（`f4e5dc9^`）と新 scaffold を同じ試料に当てた（scratchpad の `p5/run.py`）。
  **陽性対照**: パスの変数を持つ入口は旧版の出力が新版の `--check` で 1、作り直すと 0。
  **陰性対照**: パスの変数を持たない入口だけなら、旧版の出力のまま新版の `--check` が 0。
  R1: 凍結を模した v1（`/orders/{order_id}`）で `--check --upto 1` が 1、v2 の生成が 0、旧版の v1 の `--dry-run` は 0。
  観測窓: この 3 つの試料だけ

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `--check --upto <n-1>` もパスの変数の決まりを外す | 採らない | 生成するので外せない（`input` に無い変数は `openapi()` で引けない）。移行の項に書く |
| 旧い出力の形（`<Base>Input` をボディに・path パラメータなし）を保つ | 採らない（人間の決定） | 無効な OpenAPI を出し続けることになる |
