# #183 — dev-loop の Eval: 作成を、コマンドの regex ではなく終了状態で採点する

## 周の在り処

- ブランチ: `issue/183-eval-end-state-graders`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-183`
  （`prepare-worktree.sh` で作り、`EnterWorktree` に `path` で入った。
  セッションは issue-184 の worktree から `path` で移ってきた）
- 起点: `1493a93`（Merge pull request #185）
- base: 参照 `origin/main` → `1493a93ca23c15579942c12dc63bab6501d5e5d8`
- 読み込まれた dev-loop は **1.35.0**（リポジトリは 1.36.0）

## 0. 着手時に分かったこと

**grader が見る「作成されたファイル」の取り方を、`claude` 2.1.289 のバイナリから読んだ**
（`~/.local/share/claude/versions/2.1.289` の `strings`。**公式ドキュメントは
「Only files created during the run count」までしか書いておらず、`.git` を含むかは書いていない**）:

- scaffold の直後と実行の後に、**作業ディレクトリを再帰で歩いて**ディレクトリ以外の相対パスを集める。
  **除外は無い**——`.git/` の中も入る。上限（件数・深さ）を超えると「file evidence cannot be trusted」で落ちる
- 差（実行後 − scaffold 直後）を改行で連結したものが `files`。`file_exists` はこれに glob を当てる
- glob は `*` → `[^/]*`、`**/` → `(?:.*/)?`、`**` → `.*`、全体を `^…$` で囲む

だから **`git worktree add` はどこに作っても `.git/worktrees/<名前>/HEAD` を新しく作る**
（admin ディレクトリは共通の `.git` に置かれる）。**新しいブランチは
`.git/refs/heads/<名前>` を新しく作る**（loose ref）。**既存の issue-7 の分は
scaffold 直後の集合に入っているので、差に現れない。**

## 1. 変更範囲

触る:

- `plugins/dev-loop/evals/resume-no-new-worktree/case.yaml` — 作成を見る 2 本を終了状態の grader に置き換える
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.36.0 → 1.36.1）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版のバナーだけ
- `docs/plans/issue-183.md` — この計画

触らない: `scaffold.sh`（終了状態の取り方は scaffold に依らない）、`ran-find-cycle`、
`CLAUDE.md`（grader の中身を書いていない。「ケースの冒頭のコメントを正とする」と指しているだけ）、
`docs/plans/issue-181.md`（その周の記録）

**同じことを述べている箇所の数**: 作成を見る grader の説明は `case.yaml` の冒頭と各 grader の
コメントの 1 ファイルだけ。版は 3 箇所（機械が揃いを見る）。分ける理由は無い。

## 2. デプロイ経路

プラグインの版を上げる → main にマージ → 利用者は `plugin update` で受け取る。
公開サイトの `docs/` は触らない（`docs/plans/` は mkdocs の nav に載るかに依らず、内容は記録）。

## 3. 受入基準

不変条件: **ケースの「作成したら赤」の歯止めは、作成の言い回しに依らず赤になり、
作成しない実行では緑のまま。**

破りうる経路（作成の入口）: `git worktree add`（cwd の内／外、`-C` 前置き、行継続、`--detach`）、
`prepare-worktree.sh`、`git checkout -b` / `switch -c` / `branch <名前>` / `branch -m`、
`python -c` 越し、サブエージェントの中、`EnterWorktree`（eval では使えない。#181）

| # | 基準 | 証明手段 |
| --- | --- | --- |
| A | **実ハーネスで**、作成した実行（陽性対照）で終了状態の grader が赤になる | `claude plugin eval` を別端末で（**この周のセッションからは起動できない**。下記） |
| B | **実ハーネスで**、現行の `SKILL.md` で当ケースが緑のまま（3/3 grader） | 同上 |
| C | 走査の式をローカルに再現し、陰性（作成しない操作）で緑・陽性（上の経路のうち git で起こせるもの）で赤 | `sim.py`（scratchpad）。**再現であって実ハーネスではない** |
| D | 版が 3 箇所で揃い、`check-all.py` が緑。PR 側の CI も緑 | `check-all.py`・`gh pr checks` |
| E | `case.yaml` のコメントが述べる事実（走査の仕方・何を見ないか）が正しい | バイナリの該当箇所・C の結果 |

**未証明**（この環境では原理的に証明できない）:

- **サブエージェントの中での作成**——eval の子に `Agent` を許していない（`allowed_tools`）ので、
  そもそも起こせない。終了状態は誰が作っても同じファイルなので**原理上は拾う**が、測っていない
- **eval の子の `git` が reftable 形式で `init` する設定**——そのとき新しいブランチは
  `refs/heads/` にファイルを作らない。サンドボックスの `HOME` は一時なので既定（files）のはず、までしか言えない

**A・B は BLOCKED**——**何が無いか: 道具**（worktree 隔離セッションのガードが
`claude plugin eval` を shell の `eval` と読んで拒否する。#181・`CLAUDE.md`）。
**人間が別の端末で回せば消える。** 回し方は下の「人間に回してもらうもの」。

生成物: **なし**（`case.yaml` は手書き。`skill-metrics.py` は `SKILL.md` の節構造を測るが、
版のバナーの数字の変更は節構造を動かさない——`check-all.py` の `--check` で確かめる）。

## 4. 未解決の判断

- 旧 regex の 2 本（`no-worktree-add`・`no-new-branch`）を**消す**。残すと「言い回しを足すたびに偽陽性」
  （#183 の本文）がそのまま残り、終了状態の grader と二重に赤になるだけで情報が増えない

## 5. 関門の進捗（再開点）

- 手順 4: 実装済み（`case.yaml` の 2 本を `file_exists` に置換・版 1.36.1）
- 陽性対照の用意: scratchpad の `build-control.py` が、本物のケースの grader と scaffold を
  **そのまま写し prompt だけ差し替えた**対照ケース（`git worktree add … -b issue/7-again` を
  走らせるだけ）をプラグインの複製の下に組む（`--eval-dir` はプラグインの下しか取らないため）。
  **A・B は人間が別の端末で回す**（結果をここに書き戻す）
- Verifier: 未 / `/code-review`: 未
- 実験: C（ローカル再現）。陰性 7・陽性 12、すべて期待どおり（`sim-v1.txt`）。
  **交絡**: 再現は私の書いた walker であって実ハーネスではない——だから A・B を別に置いた

## 6. 既知の限界・決着済みの論点

（まだ無し）
