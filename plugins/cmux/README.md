# cmux plugin

cmux ウィンドウで GitHub Issue/PR を扱うためのスキルを提供するプラグイン。

## 提供スキル

### `/cmux [-n] [-w|-r] <number>`

cmux のブラウザペインで GitHub Issue/PR を開き、worktree でレビューを行う。

| 呼び出し | モード | 動作 |
|---|---|---|
| `/cmux <number>` | Issue | Issue の URL をブラウザペインに表示 |
| `/cmux -w <number>` | PR worktree | PR をブラウザ表示し、worktree を作成して `gh pr checkout` |
| `/cmux -r <number>` | PR レビュー | worktree でチェックアウトし、`gh pr diff` でレビュー開始 |

`-n` フラグを付けると、処理の最初に新しいターミナルタブ（サーフェス）を作成してそこで実行する。

## 前提

- `cmux` CLI がインストールされていること
- `gh` CLI が認証済みであること
- Claude Code の `EnterWorktree` ツールが利用可能であること

## インストール

```
/plugin marketplace add hdknr/claude-code-setup
/plugin install cmux@claude-code-setup
```
