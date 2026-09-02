# Part 3: インストール後の環境準備

Claude Code を日常的に使うための環境を整えます。

!!! note "macOS / Windows 共通ページ"
    Part 3 は macOS・Windows で内容がほぼ共通のため、1 ページにまとめています。
    OS によってコマンドが異なる箇所のみ、**macOS / Windows のタブ**で切り替えて表示しています。

## 3.1 作業用リポジトリの作成

日々の作業を管理するための GitHub リポジトリを作成します。

=== "macOS"

    ```bash
    mkdir -p ~/Projects
    cd ~/Projects
    mkdir my-workspace
    cd my-workspace
    git init
    ```

=== "Windows"

    ```powershell
    mkdir $HOME\Projects\my-workspace
    cd $HOME\Projects\my-workspace
    git init
    ```

## 3.2 CLAUDE.md の作成

`CLAUDE.md` は Claude Code に対する常駐の指示ファイルです。プロジェクトのルートに配置すると、毎回の会話で自動的に読み込まれます。

```
claude
```

Claude Code を起動して、以下のように指示してください:

```
このディレクトリに CLAUDE.md ファイルを作成してください。
内容は「このリポジトリは私の日々の作業を管理するワークスペースです。
日本語で応答してください。」としてください。
```

## 3.3 GitHub リポジトリとの連携

!!! warning "必ず非公開（プライベート）リポジトリで始めてください"
    GitHub のリポジトリには**公開（Public）**と**非公開（Private）**があります。
    作業用リポジトリには個人情報や機密情報を含むファイルを保存する可能性があるため、**必ず非公開で作成してください**。

    公開リポジトリにすると、以下のような情報がインターネット上に公開されます:

    - 履歴書・職務経歴書に含まれる氏名・住所・連絡先
    - 確定申告の書類に含まれる所得情報・マイナンバー
    - 提案書・計画書に含まれる取引先情報
    - 写真に含まれる位置情報や個人が特定できる情報

    必要に応じて後から公開に変更することもできます。迷ったら非公開にしておけば安全です。

Claude Code にリポジトリの作成と連携を任せましょう:

```
GitHub に my-workspace というプライベートリポジトリを作成して、
このディレクトリと連携してください。
```

!!! tip "Claude Code に任せる"
    Claude Code は `gh` コマンドを使って GitHub リポジトリの作成やプッシュを実行できます。
    手動でコマンドを打つ必要はありません。

## 3.4 スキルの活用

スキルは Claude Code の機能を拡張する再利用可能なコマンドです。
`/` に続けてスキル名を入力することで実行できます。

### プラグイン・マーケットプレイスからインストール

このプロジェクトでは、プラグイン・マーケットプレイス方式でスキルとコマンドを配布しています。
Claude Code 内で以下のコマンドを実行するだけでインストールできます。

**① マーケットプレイスを追加する（最初に一度だけ）:**

```
/plugin marketplace add hdknr/claude-code-setup
```

**② 必要なプラグインをインストールする:**

このマーケットプレイスからは、次のプラグインをインストールできます。

| プラグイン | 呼び出し | 種別 | 内容 |
|---|---|---|---|
| `workspace-setup` | `/workspace-setup:workspace-setup` | コマンド | ワークスペースの初期セットアップを対話的に行う（ディレクトリ作成と git init、CLAUDE.md 作成、GitHub プライベートリポジトリの作成と連携） |
| `cmux` | `/cmux:cmux` | スキル | cmux ウィンドウで GitHub Issue/PR をブラウザ表示し、worktree でレビュー |
| `dev-loop` | `/dev-loop:dev-loop` | スキル | 1 Issue = 1 周のループ志向開発（開発者向け） |

```
# ワークスペース初期セットアップ用
/plugin install workspace-setup@claude-code-setup

# cmux 連携用（cmux ターミナルを使う場合）
/plugin install cmux@claude-code-setup

# ループ志向開発用（開発者向け・GitHub Issue で開発を回す場合）
/plugin install dev-loop@claude-code-setup
```

インストール時に**スコープ**を選ぶ画面が出ます。

| スコープ | 意味 |
|---|---|
| **User** | 自分の**全プロジェクト**で使う |
| **Project** | このリポジトリの**全メンバー**で使う |
| **Local** | このリポジトリで**自分だけ**が使う |

どのフォルダで作業しても使えるようにしたい場合は **User** を選びます。迷ったら User で
問題ありません。

!!! note "呼び出しに `プラグイン名:` が付きます"
    プラグインが提供するスキル**とコマンド**は、名前の衝突を防ぐため**常にプラグイン名が
    頭に付きます**。`cmux` プラグインのスキルは `/cmux` ではなく **`/cmux:cmux`** です。
    入力を始めれば候補が出るので、覚えなくても `/cmux` まで打てば選べます。

!!! tip "インストール済みプラグインの確認"
    `/plugin` を実行すると、追加済みのマーケットプレイスとインストール済みプラグインの一覧を確認・管理できます。

各プラグインの詳しい機能・前提・使い方は [プラグイン一覧](plugins/index.md) にまとめています。

### 使い方の例

作業用リポジトリで Claude Code を起動し:

=== "macOS"

    ```bash
    cd ~/Projects/my-workspace
    claude
    ```

=== "Windows"

    ```powershell
    cd $HOME\Projects\my-workspace
    claude
    ```

ワークスペースの初期セットアップを実行:

```
/workspace-setup:workspace-setup
```

このコマンドを実行すると、以下を対話的にセットアップできます:

- ワークスペースディレクトリの作成
- `CLAUDE.md` の作成
- GitHub プライベートリポジトリの作成と連携

`cmux` プラグインを入れた場合は、cmux ウィンドウ内で GitHub の Issue/PR を操作できます:

```
# Issue 番号 12 をブラウザペインに表示
/cmux:cmux 12

# PR 番号 34 を worktree でチェックアウトしてレビュー
/cmux:cmux -r 34
```

スキルの一覧を確認:

```
/help
```

## 3.5 日常的な使い方のヒント

### ドキュメント作成

```
提案書のテンプレートを作成してください。テーマは「新規事業の企画書」です。
```

### ファイル整理

```
このディレクトリ内のファイルを種類ごとにフォルダ分けしてください。
```

### 調べ物の整理

```
「確定申告の医療費控除」について調べて、ポイントをまとめたマークダウンファイルを作成してください。
```

!!! tip "会話の終了と再開"
    - 終了: `/exit` と入力
    - 再開: 同じディレクトリで `claude` を実行
    - 前回の会話を続ける: `claude --continue` を実行

## まとめ

以上で Claude Code の環境構築は完了です。

- **Part 1** で基盤ツール（GitHub CLI など）をインストール
- **Part 2** で Claude Code をインストール・認証
- **Part 3** で日常利用の環境を準備

あとは `claude` コマンドを起動して、日本語で自由に指示を出すだけです。
