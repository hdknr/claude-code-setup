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
- 関門: 未着手
- 交絡を潰した手順: 未着手

## 既知の限界・決着済みの論点

- 大文字を含む名前（`constraints-Py38.txt`）は拾わない——前からの照合（`fnmatchcase`）と同じ。Issue の受入基準に無い。
- `cp38` のような接頭辞は拾わない——Issue の受入基準の接頭辞は `py`・`python`・`pypy`・`pyodide` の 4 つ。
- `constraints-py.txt`（接頭辞だけで数字が無い）は拾わない——Issue の形は「接頭辞の直後が数字」。

## 経験の還元（手順 8）

- この周の起票: 0 件（親から委譲された周で、起票しない指示。後続の指摘は PR コメントにだけ残す）
