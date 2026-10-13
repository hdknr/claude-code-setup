# Issue #199 — orca: -w / -r を Orca 管理の worktree の中から通しで確かめる

## 1. 変更範囲

触る:

- `plugins/orca/skills/orca/SKILL.md` — `-w` と `-r` の節（と版のバナー）
- `plugins/orca/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — orca の version
- `docs/plans/issue-199.md` — この計画ファイル

触らない:

- `plugins/cmux/` — 同じ文面を持つが、Issue は Orca 固有の前提（最初から Orca 管理の worktree の中にいる）を問うている。cmux から linked worktree の中で呼んだ場合の同型の危険は PR コメントの残課題に書く
- description（3 箇所）——「-w は worktree で gh pr checkout」は変わらない
- `plugins/orca/README.md` ——表の「worktree でチェックアウト」は変わらない
- `orca worktree create --pr` に寄せる案（#203 の未決）

**複製の数**: `-w`/`-r` の worktree 条件を述べている箇所は orca の `SKILL.md` の 2 節（`EnterWorktree`・`worktree 内`・`gh pr checkout` を `plugins/orca/` と `docs/` で引いた。README の表は条件を持たない）。版は 3 箇所（CI が見る）。**分けない理由**: 2 節は同じ欠陥（作れなかった・作らなかったときに利用者のツリーで checkout する）の 2 つの入口。

## 2. デプロイ経路

- マーケットプレイス（`plugins/` と `marketplace.json`）。`docs/` は計画ファイルだけ。破壊的・不可逆な操作は無い。

## 3. 受入基準

**実測（Issue のやること 1。2026-10-13、Orca 1.4.224）**: `orca worktree create --name probe-199` で作った
Orca 管理の linked worktree（`~/orca/workspaces/claude-code-setup/probe-199`）の中で:

- 前提の確認（`orca worktree current`）は `ok`——スキルは止まらない。
- `git rev-parse --path-format=absolute --git-dir` = `…/.git/worktrees/probe-199`、`--git-common-dir` = `…/.git`
  ——git の判定では「worktree 内」。旧 `-r` の「worktree 内でなければ」はこの読みで偽になり `EnterWorktree` を飛ばす。
- `gh pr checkout 192` は終了 0 で `hdknr/probe-199` → `issue/190-eval-runner` に切り替えた。
  `orca worktree current` もそのブランチを返した——**利用者の作業ブランチが切り替わる**。
- 陽性側: メインのチェックアウト（Orca の `isMainWorktree: true`）では git-dir = common-dir で「worktree の外」。
- probe は `orca worktree rm` で削除し、残ったブランチ `hdknr/probe-199` も削除した。

**I1. `-w`/`-r` の `gh pr checkout` が、呼び出した時点の作業ツリー（利用者の Orca worktree）のブランチを切り替えない。**

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 `-r`・Orca 管理の linked worktree の中（PR と別のブランチ） | 新しい worktree を作り、そこで checkout | 条件を「worktree 内か」から「HEAD が PR の head ブランチか」に変える |
| P2 `-r`・Orca のメインのチェックアウト | 同上（回帰しない） | 同上 |
| P3 `-r`・既にその PR のブランチの上にいる | 作らずにそのままレビュー（checkout は切り替えない） | 同上 |
| P4 `-w`/`-r`・`EnterWorktree` が作れない（worktree セッション中など） | 止まる。現在のツリーで checkout しない | 「作れなければ止まる」を明記 |
| P5 `-w`/`-r`・`EnterWorktree` は返ったが移っていない | 止まる | 作成前後の `--show-toplevel` を比べる |
| P6 fork の PR で head 名とローカル名が違う | 安全側（作る）に倒れる | 一致しなければ作る |

**I2. 版が揃い patch で上がっている**（orca 1.0.4 → 1.0.5）。`check-all.py` が緑。

### 証明の手段

- I1: 条件の判定（git・`gh pr view --json headRefName`）は Orca の linked worktree とメインで実測できる。
- **未証明**: モデルが新しい文面を読んで実際にどう動くか（`/orca -r` を Orca の中の Claude Code で通しで回すこと）。
  この周の Claude Code はメインのチェックアウトで起動しており、Orca の linked worktree の中のセッションではない。
  **`EnterWorktree` を Orca の linked worktree の中から呼んだとき、どこに作るか**も測っていない
  （道具の説明文は「`.claude/worktrees/` に作る」とだけ言う）。人間レビューに回す。
- 生成物: **生成物なし**（`SKILL.md` の測定値は dev-loop だけ、図は触らない）。

## 4. 未解決

- なし

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/199-orca-r-worktree-check`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-199`、
  起点 `4395dd2`、base 参照 `origin/main`、base SHA `4395dd2c1a85d7205ae2a4826297ca9b2d70d6b6`
- 関門: 未着手
- 反証・差し戻し: 0
- 交絡: 実験 1（上の実測）。陽性側（メインで「外」・checkout で実際に切り替わる）を取った。

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| cmux も同じ文面 | 触らない（残課題） | Issue は Orca の前提を問う。cmux で linked worktree から呼ぶ危険は同型だが受入基準の外 |
| `orca worktree create --pr` に寄せる | 採らない | #203 の未決 |
