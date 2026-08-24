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

以下は全プロジェクトで使う場合の手順。リポジトリを clone して、付属のスクリプトを実行する。

```bash
git clone https://github.com/hdknr/claude-code-setup.git ~/src/claude-code-setup
~/src/claude-code-setup/scripts/link-skills.sh cmux
```

スクリプト名を省略すると（`scripts/link-skills.sh`）、このリポジトリが配布する素のスキルを
すべて張る。`-d <dir>` で置き場所を変えられ（既定は `~/.claude/skills`）、`-n` を付けると
何をするかだけ表示して変更しない。

> **なぜスクリプトなのか。** 素朴に `ln -s` を並べるだけだと、宛先や clone の状態によって
> **黙って壊れる**（動いているスキルを退避したうえで壊れた symlink を張り、終了コード 0 で
> 何も出力しない、など）。手順を文書に手で複製していたところ、4 ラウンド連続でこの類のバグが
>出たので、1 箇所に集めてテスト（`scripts/test-link-skills.py`）を当てている。
>
> スクリプトは**リポジトリの位置を自分で解決する**ので clone 先を入力する必要がなく、
> 同名の実ディレクトリがあれば `.bak.<日時>` へ退避し、**張った後に解決を確認して、
> できていなければ非 0 で終わる**。

次のセッションから、どのプロジェクトでも `/cmux` で呼べる。更新は clone 先で
`git pull` するだけでよい（symlink なので張り直しは不要）。

- **プラグインと併用すると `/cmux` と `/cmux:cmux` が両方並ぶ。** 中身は同じなのでどちらでも
  動くが、スキル一覧が二重になる。片方だけにしたいなら、プラグインを入れずに symlink だけにする。
- **スクリプトは sh / bash / zsh / dash でテストしている**（`scripts/test-link-skills.py`）。
  テストは macOS で回しているが、POSIX sh で書いてあり dash も含めて通るので Linux でも
  同じ挙動になる見込み。**Windows は未検証**で、symlink を使わない場合はディレクトリを
  コピーする（その場合は `git pull` のたびにコピーし直す必要がある）。
