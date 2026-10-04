# #181 — dev-loop の振る舞いの回帰 Eval（最初の 1 ケース）

## 周の在り処

- ブランチ: `issue/181-dev-loop-eval`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-181`
  （`prepare-worktree.sh` で作り、`EnterWorktree` に `path` で入った）
- 起点: `9602820`（Merge pull request #180）
- base: 参照 `origin/main` → `9602820b110c7fadf5c9dcfec756869f6e01881c`
- 読み込まれた dev-loop は **1.35.0**（`claude plugin list --json` とリポジトリが一致）

## 0. 方針（着手前に決めた）

#181 は方向性の一覧で受入基準を持たない。分析（Issue コメント 5977176842）のうち、
人間が **1: 振る舞いの回帰 Eval** を選んだ。**この周は最初の 1 ケースに限る。**

対象にする振る舞いは **#96 型**——**再開の周（既に周の worktree とブランチがある）で、
worktree を新規作成しない**。失敗の実物がある（#96 で 2 本目の worktree を作って実装をやり直した）。

道具は `claude plugin eval`（Claude Code 同梱）。**CI では回さない**——`claude` を起こして課金する
（`measure-guard-os.sh` と同じ扱い）。

## 1. 変更範囲

触る:

- `plugins/dev-loop/evals/` — Eval ケース（prompt・graders・scaffold）
- `docs/plans/issue-181.md` — この計画ファイル
- `CLAUDE.md` — Eval の置き場所と回し方（`plugins/` の構成の行と、新しい節「振る舞いを Eval で当てる」）

触らない: `SKILL.md` の規範（**規範を変えずに測る仕組みだけ足す**——分析の 2 番目「規範の追加を止める」と整合）、
`scripts/check-all.py`・CI（課金するので組み込まない）、#1737 の帰属違い（別の候補）

（version bump が要るかは歯止めに従う。要るなら `plugin.json`・`marketplace.json`・`SKILL.md` のバナーをここに足す）

## 2. デプロイ経路

プラグインのカタログ（`plugins/` の変更はマージで利用者のクローンに届く）。サイト（`docs/`）は
計画ファイルのみ。

## 3. 受入基準

**不変条件**: **再開の周で dev-loop は worktree を新規作成しない。**
**それを破る入口**（エージェントが worktree を作る手段）:
(a) `git worktree add`、(b) `prepare-worktree.sh`、(c) `EnterWorktree` に `name`（または引数なし）、
(d) `git checkout -b` / `git switch -c` で周のブランチと別の新ブランチを切る。

| # | 基準 | 証明手段 |
| --- | --- | --- |
| A | ケースが (a)〜(d) のどれかを使った実行を**失敗**と採点する | grader の定義を読む＋変異実行 |
| B | **陽性対照**: 規範から再開の節を抜いた `SKILL.md` で回すと、**実際に (a)〜(d) が起き、失敗と採点される**。起きなければ「このケースは振る舞いを判別していない」と書き、周を閉じない | 変異した版で `claude plugin eval` を回す |
| C | 現行の `SKILL.md` で回すと**通る** | `claude plugin eval` を回す |
| D | scaffold が**実環境に触れない**（一時ディレクトリの中に git リポジトリ・worktree・計画ファイルを作る。`$HOME` のリポジトリを触らない） | scaffold を読む＋実行後に本物の `git worktree list` が変わっていないことを見る |
| E | 回し方と費用が `CLAUDE.md` に書いてあり、`check-all.py` が緑 | 実行 |

**組み合わせ**: B と C は**同じケース・同じ回数**で回す（違う設定で比べると交絡する）。

**2026-10-04 人間の決定で B を狭めた**（`AskUserQuestion`「主張を狭めて PR」）。
元の B（作成を見る grader が #96 修正前の版で赤になる）は**満たしていない**——3 回とも通った
（§5）。**消したのではなく、満たしていない基準として PR に名指しする。** 代わりに置いた基準:

| # | 基準 | 証明手段 |
| --- | --- | --- |
| B' | `ran-find-cycle` が **現行で通り、#96 修正前の版で落ちる** | C4 と M2c（同じ設定・1 回ずつ） |
| B'' | ケースの冒頭と `CLAUDE.md` が、**判別を確かめた grader は `ran-find-cycle` だけ**と書いており、それ以上を主張しない | 読む |
| F | 入口 (c)（`EnterWorktree`）は eval で起こせないことが書いてある（**BLOCKED**） | 読む |

**未証明**: 回数が少ない（`runs` 3 程度）ので、**通過率の差はサンプルが小さい**。B と C の差が
偶然でないことは言えない——**言えるのは「この回数で、この差が出た」まで**。

**生成物**: `SKILL.md` を触る場合だけ `skill-metrics.py` の生成ブロックが該当（version バナーのみなら
節構造は変わらないが、`--check` で確かめる）。図なし。

## 4. 未解決

- `claude plugin eval` のケース書式（guide に確認中）
- version bump の要否

## 5. 関門の進捗（再開点）

- 手順 4: 実装中（`plugins/dev-loop/evals/resume-no-new-worktree/`）
- Verifier: 未 / `/code-review`: 未
- 実験（すべて `--runs 1 --ablation none`、子のモデルは `claude-opus-5-5`）:
    - C3（現行 `SKILL.md`）: **4/4 通過**、5 ターン、$0.62
    - M2a（**#96 修正前の `SKILL.md`＝`14fcc7f^`、v1.14.0**）: 3/4。**落ちたのは `ran-find-cycle`
      だけ**（旧版は `find-cycle.py` を持たないので自明に落ちる）。**worktree は作らなかった**——
      既存の worktree を見つけて手順 5 から再開した。13 ターン、$0.92
    - **交絡**: M2a・C3 の子の道具は **8 本で `EnterWorktree` を含まなかった**（trace の init）。
      **入口 (c) が起きえない設定だった**——#96 の実物は `path` 無しの `EnterWorktree`。
      `allowed_tools` と `--allow-tools` に足して M2b を回す
    - M2b（M2a ＋ `EnterWorktree` を許可）: 3/4（同じく `ran-find-cycle` だけ）。12 ターン、$0.72。
      **子の道具は `Task, Bash, Glob, Grep, Read, Skill, TaskStop, ToolSearch` で、許可しても
      `EnterWorktree` は提供されなかった。** 再び既存の worktree から正しく再開した
    - **もう 1 つの交絡: サンドボックスの中で `git` が動かない**（M2b の子の報告:
      `can't exec '/usr/local/bin/git'`。子は `.git/objects` を zlib で読んで代用した）。
      **ホスト側の原因を確かめた**: `/usr/local/bin/git` は `../Cellar/git/2.47.0/bin/git` への
      **切れたリンク**（`/usr/local/Cellar/git` が無い）。ホストの `git` は Xcode の 2.54.0
      （`/usr/bin/git` のスタブ経由）で、**サンドボックスの外では動く**。
      **これで C3 の通過も判別していない**——`find-cycle.py` は `git` に依るので、
      5 ターンで止まったのは「探せなかった（exit 2）→ 人間に訊く」だった可能性がある
      （C3 の trace は `--keep-temp` 前で消えており、**確かめられない**）
    - **陽性対照（基準 B）は取れなかった。** 2 回とも、#96 修正前の版でも worktree を作らなかった
    - 費用の合計: **$2.27**（C3 0.62 ＋ M2a 0.92 ＋ M2b 0.72。scaffold で落ちた 3 回は $0）
- **判定: BLOCKED**（手順 5）。無いもの: **道具**——(1) サンドボックスで動く `git`、
  (2) eval の子に `EnterWorktree`。**人間の判断待ち**
- **人間が (1) を直した**（2026-10-04。切れたリンクを消し `brew install git` → `/opt/homebrew/bin/git` 2.56.0）。
  同じ設定で回し直した:
    - C4（現行）: **4/4**、14 ターン、$1.29。trace で `find-cycle.py` が「当たったものがある」を返し、
      `references/resume.md` を読んで既存の worktree で手順 5 から再開した（**今度は判別している通過**）
    - M2c（#96 修正前）: **3/4**、12 ターン、$1.06。**worktree は作らなかった**。落ちたのは `ran-find-cycle` だけ
    - 費用の合計: **$4.62**
- **結論**: 作成を見る 3 つの grader は、**この条件では修正前後を判別しない**——
  **#96 修正前の版でも、現在のモデルは worktree を作らない**（git あり・なしの 3 回すべて）。
  これは**変異が届いていない**（手順 5）であって、砦の穴ではない。
  **判別したのは `ran-find-cycle` だけ**——言えるのは「**再開の探索を走らせる手順が消えたら赤になる**」まで。
  入口 (c)（#96 の実物）は eval の子に `EnterWorktree` が無いので**引き続き BLOCKED**

## 6. 既知の限界・決着済みの論点

（まだ無い）

## 7. 事故の記録（この周）

**scaffold を手で走らせて、cwd（この周の worktree）を壊した。** 2026-10-04 15:10。
空き場所で試すつもりが、`bash scaffold.sh` を cwd のまま実行した。起きたこと:

- **リポジトリ共有の `.git/config` に `user.name=eval` / `user.email=eval@example.invalid`**
  （全 worktree とメインに効く）
- このブランチに `init` コミット（`.gitignore` と `README.md` を上書き）
- worktree `issue-181/.claude/worktrees/issue-7` とブランチ `issue/7-bump-version`

復旧: `git config --local --unset` 2 件・`git worktree remove`・`git branch -D`・
`git reset --hard 9602820`。**確かめたこと**: `git config --local --get-regexp '^user\.'` が
0 件、`git worktree list` が元の 5 本、`git status` が未追跡 2 件のみ。
**メインの作業ツリーの `git status` は見ていない**（ガードが `-C` を拒否）——
scaffold が書いたのは cwd と共有の `.git/` だけなので、メインのファイルには触れていない。

再発防止: scaffold の冒頭に「**空でない／git リポジトリの中なら断る**」を入れ、
空でない dir で exit 1・空の dir で成功（`find-cycle.py 7` が exit 1＝当たり）を確かめた。
