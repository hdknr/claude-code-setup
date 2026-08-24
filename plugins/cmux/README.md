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
**マニフェスト（`.claude-plugin/`）を持たない素のスキル**として skills ディレクトリに置く。
置き場所で有効範囲が変わる。

| 置き場所 | 有効範囲 |
|---|---|
| `~/.claude/skills/cmux/` | すべてのプロジェクト |
| `<プロジェクト>/.claude/skills/cmux/` | そのプロジェクトだけ |

以下は全プロジェクトで使う場合の手順。

`plugins/cmux/skills/cmux/` は `SKILL.md` だけで `.claude-plugin/` を持たないので、
そのまま symlink できる。

まずリポジトリを clone する。**すでに別の場所に clone してあるなら clone は省略し、
次のブロックの `repo=` をその場所に書き換える。**

```bash
git clone https://github.com/hdknr/claude-code-setup.git ~/src/claude-code-setup
```

```bash
# 自分の clone 先に合わせて書き換える
repo=$HOME/src/claude-code-setup

src=$repo/plugins/cmux/skills/cmux
target=$HOME/.claude/skills/cmux

if [ ! -f "$src/SKILL.md" ]; then
  # clone が無いまま進むと、動いているスキルを退避したうえで壊れた symlink を張ってしまう
  echo "中止: $src が見つかりません。repo= を clone 先に合わせてください。" >&2
else
  mkdir -p "$HOME/.claude/skills"

  # symlink 以外のものが同名で置かれていたら、日時付きの名前で退避する
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    mv "$target" "$target.bak.$(date +%Y%m%d%H%M%S)"
  fi

  # 退避できていなければ、symlink を張らずに中止する
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "中止: $target を退避できませんでした。手で移動してから再実行してください。" >&2
  else
    ln -sfn "$src" "$target"
  fi
fi
```

> **ガードの意図。** 素朴に `ln -sfn` するだけだと 2 通りの壊れ方をする。(1) **clone が無い／別の
> 場所にある場合**、動いているスキルを退避したうえで**壊れた symlink** を張り、**何も出力せずに**
> 終わる（`/cmux` が消える）。(2) `~/.claude/skills/cmux` に **symlink 以外のもの**（個人 skill と
> して直置きした実ディレクトリなど）があると、`ln -sfn` は**エラーを出さずに** `cmux/cmux` を
> 作り、`/cmux` は**古いスキルを指したまま**になる（`-f` はディレクトリを unlink できない）。
> 上のブロックは**先に clone の有無を確かめ**、退避してから張り、**退避できなければ張らずに
> 中止する**（メッセージは stderr）。
>
> **検証済みの範囲**: macOS の bash / zsh / sh、宛先が「無い／実ディレクトリ／空ディレクトリ／
> 通常ファイル／既存 symlink／壊れた symlink／`.bak` が既にある」の各状態、clone が無い場合、
> `$HOME` に空白や日本語を含む場合、2 回連続実行。`.bak` の名前が同一秒内に衝突した場合は
> 入れ子になるが、データは失われない。

次のセッションから、どのプロジェクトでも `/cmux` で呼べる。更新は clone 先で
`git pull` するだけでよい（symlink なので張り直しは不要）。

- **プラグインと併用すると `/cmux` と `/cmux:cmux` が両方並ぶ。** 中身は同じなのでどちらでも
  動くが、スキル一覧が二重になる。片方だけにしたいなら、プラグインを入れずに symlink だけにする。
- **検証環境は macOS のみ。** Linux も同じ手順で動く見込みだが未検証（シェルの実装差で
  挙動が変わりうる）。Windows も未検証で、symlink を使わない場合はディレクトリをコピーする
  （その場合は `git pull` のたびにコピーし直す必要がある）。
