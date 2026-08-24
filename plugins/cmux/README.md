# cmux plugin

cmux ウィンドウで GitHub Issue/PR を扱うためのスキルを提供するプラグイン。

## 提供スキル

### `/cmux:cmux [-n] [-w|-r] <number>`

cmux のブラウザペインで GitHub Issue/PR を開き、worktree でレビューを行う。

| 呼び出し | モード | 動作 |
|---|---|---|
| `/cmux:cmux <number>` | Issue | Issue の URL をブラウザペインに表示 |
| `/cmux:cmux -w <number>` | PR worktree | PR をブラウザ表示し、worktree を作成して `gh pr checkout` |
| `/cmux:cmux -r <number>` | PR レビュー | worktree でチェックアウトし、`gh pr diff` でレビュー開始 |

`-n` フラグを付けると、処理の最初に新しいターミナルタブ（サーフェス）を作成してそこで実行する。

> **なぜ `/cmux` ではなく `/cmux:cmux` なのか**
>
> プラグインが提供するスキルは、名前の衝突を防ぐため**常にプラグイン名で名前空間化される**。
> プラグインとして入れた場合の呼び出しは `/cmux:cmux` になり、`/cmux` にはならない。
> `commands/` に置いても同じ名前空間に載るので、bare な `/cmux` をプラグインで提供する方法は無い。
>
> `/cmux` で呼びたい場合は「[bare `/cmux` で使う](#bare-cmux-で使う)」の手順を使う。

## 前提

- `cmux` CLI がインストールされていること
- `gh` CLI が認証済みであること
- Claude Code の `EnterWorktree` ツールが利用可能であること

## インストール

まずマーケットプレイスを追加する（最初に一度だけ）。

```
/plugin marketplace add hdknr/claude-code-setup
```

`/plugin install` はスコープの選択画面を出すので、用途に応じて選ぶ。

```
/plugin install cmux@claude-code-setup
```

| スコープ | 意味 |
|---|---|
| **User** | 自分の**全プロジェクト**で使う |
| **Project** | このリポジトリの**全メンバー**で使う（`.claude/settings.json` に入る） |
| **Local** | このリポジトリで**自分だけ**が使う（共有しない） |

### すべてのプロジェクトで使う（ユーザースコープ）

上のコマンドで **User** を選ぶ。シェルから非対話で入れる場合は `--scope` を渡す。

```bash
claude plugin marketplace add hdknr/claude-code-setup
claude plugin install cmux@claude-code-setup --scope user
```

`claude plugin install` はセッションの外で走るため、反映は次回起動時か、開いている
セッションで `/reload-plugins` を実行したときになる。

### bare `/cmux` で使う

プラグイン経由では `/cmux` にならない。`/cmux` で呼びたい場合は、スキルを
**マニフェストを持たない素のスキル**として `~/.claude/skills/` に置く。この配置だけが
名前空間の付かない呼び出しになる。

`plugins/cmux/skills/cmux/` は `SKILL.md` だけで `.claude-plugin/` を持たないので、
そのまま symlink できる。

```bash
git clone https://github.com/hdknr/claude-code-setup.git ~/src/claude-code-setup
ln -s ~/src/claude-code-setup/plugins/cmux/skills/cmux ~/.claude/skills/cmux
```

次のセッションから、どのプロジェクトでも `/cmux` で呼べる。更新は
`git -C ~/src/claude-code-setup pull` だけでよい（symlink なので張り直しは不要）。

- **プラグインと併用すると `/cmux` と `/cmux:cmux` が両方並ぶ。** 中身は同じなのでどちらでも
  動くが、スキル一覧が二重になる。片方だけにしたいなら、プラグインを入れずに symlink だけにする。
- macOS / Linux 向けの手順。Windows で symlink を使わない場合はディレクトリをコピーする
  （その場合は `git pull` のたびにコピーし直す必要がある）。
