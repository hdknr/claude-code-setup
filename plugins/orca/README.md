# orca plugin

[Orca](https://github.com/stablyai/orca) で GitHub Issue/PR を扱うためのスキルを提供するプラグイン。
[`cmux` プラグイン](../cmux/README.md)の Orca 版で、引数と動作は揃えてある。

## 提供スキル

### `/orca:orca [-n] [-w|-r] <number>`

Orca の内蔵ブラウザで GitHub Issue/PR を開き、worktree でレビューを行う。

| 呼び出し | モード | 動作 |
|---|---|---|
| `/orca:orca <number>` | Issue | Issue の URL を内蔵ブラウザに表示 |
| `/orca:orca -w <number>` | PR worktree | PR をブラウザ表示し、worktree を作成して `gh pr checkout` |
| `/orca:orca -r <number>` | PR レビュー | worktree でチェックアウトし、`gh pr diff` でレビュー開始 |

`-n` フラグを付けると、処理の最初に新しいターミナルタブを作成し、現在のディレクトリへ cd する。タブが付くのは現在のディレクトリを含む Orca 管理の worktree で、`.claude/worktrees/` 配下のように Orca に登録していない worktree の中からだと、それを含むメインのチェックアウトに付く。

> **なぜ `/orca` ではなく `/orca:orca` なのか**
>
> プラグインが提供するスキルは、名前の衝突を防ぐため**常にプラグイン名で名前空間化される**。
> プラグインとして入れた場合の呼び出しは `/orca:orca` になり、`/orca` にはならない。
> `commands/` に置いても同じ名前空間に載るので、bare な `/orca` をプラグインで提供する方法は無い。
>
> `/orca` で呼びたい場合は「[bare `/orca` で使う](#bare-orca-で使う)」の手順を使う。

## 前提

- Orca アプリが起動しており、`orca` CLI がインストールされていること（`orca status` でランタイムに届くこと）
- Claude Code を Orca のターミナルの中で、Orca 管理の worktree の中から起動していること
  （`orca worktree current` が通ること。スキルは最初にこれを確かめ、外にいれば止まる）
- `gh` CLI が認証済みであること
- Claude Code の `EnterWorktree` ツールが利用可能であること

## インストール

まずマーケットプレイスを追加する（最初に一度だけ）。

```
/plugin marketplace add hdknr/claude-code-setup
```

`/plugin install` はスコープの選択画面を出すので、用途に応じて選ぶ。

```
/plugin install orca@claude-code-setup
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
claude plugin install orca@claude-code-setup --scope user
```

`claude plugin install` はセッションの外で走るため、反映は次回起動時か、開いている
セッションで `/reload-plugins` を実行したときになる。

### 更新のしかた

**version を上げただけでは届かない。** 利用者のマーケットプレイスのクローンは
**導入時のコミットで凍結したままになる**——#63 で実際に、`dev-loop` が 1.0.0 のまま
使われていた。**原因はプラグイン固有ではなくマーケットプレイス側の凍結なので、
このプラグインにも同じことが起きる。**
**確認方法・注意点・最新の実測値は[プラグイン一覧の「更新のしかた」](https://hdknr.github.io/claude-code-setup/plugins/#updating)を正とする**（ここには再掲しない）。2 段階で更新する。

```
/plugin marketplace update                  # カタログを取り直す
/plugin update orca@claude-code-setup      # 新しい版に上げる（要再起動）
```

入っている版は **`SKILL.md` の冒頭**に書いてある。読み込まれた版がここより古ければ、
上の 2 段階で更新する。

**常に最新を使いたいなら、下の symlink 経路を選ぶ**——キャッシュを経由しないので、
`git pull` した時点で反映される（構造的に古くならない）。
**ただしスクリプトは自分の位置からリポジトリを解決して絶対パスで張る**ので、
**worktree から実行するとその worktree に固定される**。メインの作業ツリーから実行する。

### bare `/orca` で使う

プラグイン経由では `/orca` にならない。`/orca` で呼びたい場合は、スキルを
**マニフェスト（`.claude-plugin/`）を持たない素のスキル**として skills ディレクトリに置く。
置き場所で有効範囲が変わる。

| 置き場所 | 有効範囲 |
|---|---|
| `~/.claude/skills/orca/` | すべてのプロジェクト |
| `<プロジェクト>/.claude/skills/orca/` | そのプロジェクトだけ |

以下は全プロジェクトで使う場合の手順。リポジトリを clone して、付属のスクリプトを実行する。

```bash
git clone https://github.com/hdknr/claude-code-setup.git ~/src/claude-code-setup
~/src/claude-code-setup/scripts/link-skills.sh orca
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

次のセッションから、どのプロジェクトでも `/orca` で呼べる。更新は clone 先で
`git pull` するだけでよい（symlink なので張り直しは不要）。

- **プラグインと併用すると `/orca` と `/orca:orca` が両方並ぶ。** 中身は同じなのでどちらでも
  動くが、スキル一覧が二重になる。片方だけにしたいなら、プラグインを入れずに symlink だけにする。
- **スクリプトは sh / bash / zsh / dash でテストしている**（`scripts/test-link-skills.py`）。
  テストは macOS で回しているが、POSIX sh で書いてあり dash も含めて通るので Linux でも
  同じ挙動になる見込み。**Windows は未検証**で、symlink を使わない場合はディレクトリを
  コピーする（その場合は `git pull` のたびにコピーし直す必要がある）。
