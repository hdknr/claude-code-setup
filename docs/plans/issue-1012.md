# Issue #1012 — check-deps-declared: constraints-py38.txt のような Python の版の接頭辞つきの名前を依存と見ない（#996 の後退）

親セッションから委譲された周（サブエージェント）。手順 4・6 の割り目では訊かない（親から委譲された周）。マージ（手順 7）は親が行う。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-deps-declared.py` — `DEPENDENCY_FILES` の Python に、`constraints{-,_}{py,python,pypy,pyodide}<数字…>.{txt,in}` を足す。docstring の「守らない」を新しい範囲に合わせる
- `scripts/test-check-deps-declared.py` — 正と負の試料と変異
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — dev-loop の版（1.107.0 → 1.107.1。不具合の修正なので patch）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ。手で書かない）
- `docs/plans/issue-1012.md` — この計画

触らない:

- `check-unattended-env.py`（`DEPENDENCY_FILES` を読み込むだけ——一覧は 1 箇所。挙動は同じ関数で広がる）
- `references/dependencies.md`（名前の一覧は持たず `DEPENDENCY_FILES` を正とすると書いている）
- `constraints-<用途>` の用途の一覧（`REQUIREMENT_USES`）・`requirements*` の形・大文字の名前（`constraints-Py38.txt`。前からの照合は大文字小文字を区別する）
- Python の版の接頭辞のうち Issue に無いもの（`cp38` など）

依存の追加・更新: なし（この周は依存の定義・lockfile・取得経路の設定を触らない。触るのはそれを判定するスクリプト）

## デプロイ経路

main へのマージでプラグインの配布（カタログ）と GitHub Pages。マージは親が行う。

## 受入基準（不変条件 × 経路）

不変条件:

| # | 不変条件 | 破りうる経路（入口） | 守り方 |
| --- | --- | --- | --- |
| A1 | `constraints{-,_}{py,python,pypy,pyodide}<数字…>.{txt,in}`（例: `constraints-py38.txt`・`constraints_python3.12.txt`・`constraints-pyodide313.in`・`constraints-pypy3.10.txt`）を依存のファイルと見る——差分にあって宣言が無ければ 1 | (a) 周が PR の前に素の 1 行で呼ぶ `check-deps-declared.py`、(b) このリポジトリの CI の `scripts/check-plan-scope.py`（`judge` を読み込む）、(c) 不在の点検 `check-unattended-env.py`（`ecosystem_of` を読み込む）、(d) 下の階層（`constraints/constraints-py38.txt`） | `DEPENDENCY_FILES` の 1 箇所。(b)(c) は同じ関数を読み込むので同じ一覧。正の試料と変異（接頭辞ごと・区切り `_`・`.in`） |
| A2 | 文書の名前（`constraints-analysis.txt`・`constraints-pyproject-notes.txt` のように接頭辞の直後が数字でないもの）は引き続き拾わない | 同上 (a)〜(c) | 負の試料と、接頭辞の後ろを `*` に広げる変異 |
| A3 | `scripts/test-check-deps-declared.py` に、A1・A2 を殺す試料と変異がある | テストの変異の当て先が 1 箇所であること（テスト自身が見る） | 変異を足して全部捕まえることを走らせて見る |
| A4 | docstring の「守らない」の記述が新しい範囲を言う（事実として正しい） | docstring と `DEPENDENCY_FILES` の食い違い | 読解（関門） |
| A5 | 既存の判定を壊さない（既存の正と負の試料・変異が全部通る） | 既存のパターンの当て先 | 既存のテストが緑 |
| A6 | 版を 3 種類（`marketplace.json`・`plugin.json`・両 `SKILL.md`）で 1.107.1 に揃える | 版の上げ忘れ | `check-plugin-versions.py`・`check-version-bump.py` |
| X1 | 必須の掛け算: 受入基準を Verifier と /code-review の両方 × 1・2 パス目に渡す（2 パス目が該当なしなら 1 パス目の 2 つ） | — | 再開点で記録 |

証明できないもの（未証明）: なし——どれも一時の git リポジトリの試料と変異で当てられる。実物のリポジトリ（FreeCAD-addons・cibuildwheel）の上では走らせない（名前の形は Issue の検索結果と同じ文字列を試料にする）。

生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` の版の行を変えるので `skill-metrics.py --check` で鮮度を見る）。図の書き出しは該当なし。

周の大きさ（同じことを述べている箇所の数）: 名前の範囲を述べるのは `DEPENDENCY_FILES` と docstring の「守らない」の 2 箇所（`references/dependencies.md` と `check-unattended-env.py` は `DEPENDENCY_FILES` を指すだけ）。分けない理由: docstring は同じファイルの中で、コードの一覧の言い直しを利用者向けに持つ形が既存のもの。

## 直す線

既定（出所: `.claude/dev-loop.md` に `直す線:` の行が無く、親から委譲された周で訊かないため既定）。後続の指摘の振り分けは `references/found-lines.md` に従う（親の指示）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1012-constraints-python-prefix`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1012`・起点 `23cee426`・base の参照 `origin/main`・base の SHA `23cee426d81ac9e7bf6c758695a4fbae8acbe738`
- 手順 4 の割り目: 割らない（親から委譲された周）
- 1 パス目の指摘対応の起点: `cc4af91333720e99a058be6b35ef646a6bd540b7`（1 パス目の関門に渡した時点の HEAD）
- 関門: Verifier 1 パス目 通した——反証 0 件（`dev-loop:dev-loop-verifier`・sonnet。テンプレート 185 行を照合。陽性対照を自分で再現、テスト 3 分 12 秒で緑、git status の前後が同じ）。/code-review 1 パス目（high）通した——指摘 7 件、直す 0 件（採否は下の表）
- 2 パス目: 該当なし（1 パス目の指摘対応の差分 0 行。起点 `cc4af91333720e99a058be6b35ef646a6bd540b7`。`git diff <起点> -- ':(top)' ':(top,exclude)docs/plans/issue-1012.md'` が 0 行・`git status --porcelain` は計画ファイルだけ）
- 狭いパス: 該当なし
- 2 つ目の割り目: 無し（2 パス目が該当なし）
- 手順 5 の反証による手順 4 への差し戻し: なし
- 交絡を潰した手順: 新しい試料 6 本（正 4・負 2）を、起点 `23cee426` の本体と新しい本体の両方の `ecosystem_of` に当てた——起点では正の 4 本が None（拾わない＝後退の再現。陽性対照）、新しい本体では python。負の 2 本は両方で None。`check-all.py` 77/77 緑（コミット前）

## 既知の限界・決着済みの論点

- 大文字を含む名前（`constraints-Py38.txt`）は拾わない——前からの照合（`fnmatchcase`）と同じ。Issue の受入基準に無い。
- `cp38` のような接頭辞は拾わない——Issue の受入基準の接頭辞は `py`・`python`・`pypy`・`pyodide` の 4 つ。
- `constraints-py.txt`（接頭辞だけで数字が無い）は拾わない——Issue の形は「接頭辞の直後が数字」。

### 1 パス目の採否の表（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V | Verifier: 反証 0 件 | — | — | — |
| CR1 | 接頭辞の直後が数字ならその後ろは何でも当たる（`constraints-py3-notes.txt` を依存と見る） | 示せる（関門が `ecosystem_of` で実行。起点 None・新 python） | 無し（A2 は「接頭辞の直後が数字でないもの」。既存の `constraints-[0-9]*` と同じ形） | 残課題 |
| CR2 | docstring が「数字の後ろは何でも許す」を言っていない | 示せない（記述は偽ではなく、言っていないだけ） | 無し（A4 の記述は事実として正しい） | 残課題 |
| CR3 | `constraints-pyodide-0.27.txt`（接頭辞と版の間に区切り）を拾わない | 示せる（起点・新とも None） | 無し（Issue の形の外。後退でもない） | 残課題 |
| CR4 | 不在の点検（`check-unattended-env.py`）で `constraints-py38.txt` だけの場所に新しく 要対処 が出るのに、その点検のテストに試料が無い | 示せる（関門が実行） | 無し（A1 の経路 (c) の意図どおりの広がり。`constraints-3.8.txt` と同じ扱い） | 残課題 |
| CR5 | 例の名前がコメントと試料で揃っていない（`constraints-python312.txt` と `constraints_python3.12.txt`） | 示せない（振る舞いに影響なし） | 無し | 残課題 |
| CR6 | 3 つの生成器を 1 つの正規表現にまとめられる | 示せない（設計の提案） | 無し | 残課題 |
| CR7 | 「数字の後ろの任意の文字列」の境界を試料が押さえていない | 示せない（境界は受入基準に無い） | 無し | 残課題 |

## 経験の還元（手順 8）

焼き戻す学び: なし（後退の修正だけで、手順・規範に足すものは無い）。

振り分け（`references/found-lines.md`。親の指示）:

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| CR1 数字の後ろの任意の文字列を拾う | #1012 /code-review 1 パス目 | 示せる | 記録だけ（受入基準を破らない・後退でない（既存の `constraints-[0-9]*` と同じ形）・その名前の文書は実際の利用でまず作られない） |
| CR2 docstring が数字の後ろを言わない | 同上 | 示せない | 記録だけ |
| CR3 接頭辞と版の間に区切りのある名前 | 同上 | 示せる | 記録だけ（Issue の形の外。後退でない——起点でも拾わない） |
| CR4 不在の点検に新しい 要対処・試料なし | 同上 | 示せる | 記録だけ（意図した広がりで誤りではない） |
| CR5 例の名前の揺れ | 同上 | 示せない | 記録だけ |
| CR6 正規表現にまとめる | 同上 | 示せない | 記録だけ |
| CR7 境界の試料なし | 同上 | 示せない | 記録だけ |

- この周の起票: 0 件（親から委譲された周で起票しない指示。振り分けで直すの行も無い。残課題は PR コメントにだけ残す）
