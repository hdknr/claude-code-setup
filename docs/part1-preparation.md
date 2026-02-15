# Part 1: 事前準備

Claude Code をインストールする前に必要なツールをセットアップします。

## 1.1 ターミナルを開く

1. Finder で「アプリケーション」→「ユーティリティ」→「ターミナル」を開きます
2. または Spotlight（`⌘ + Space`）で「ターミナル」と入力して開きます

!!! tip "ターミナルとは"
    ターミナルは Mac に標準で入っているアプリで、テキストでコマンドを入力してパソコンを操作できます。
    この手順書では、ターミナルにコマンドをコピー＆ペーストして実行していきます。

## 1.2 Homebrew のインストール

Homebrew は Mac 用のパッケージマネージャーです。各種ツールのインストールに使います。

ターミナルで以下のコマンドをコピー＆ペーストして実行してください:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

!!! note "パスワードを聞かれたら"
    Mac のログインパスワードを入力してください。入力中は画面に何も表示されませんが、正常です。

インストール完了後、表示される「Next steps」の指示に従ってパスを設定してください:

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

確認:

```bash
brew --version
```

バージョン番号が表示されれば成功です。

## 1.3 Git の確認

Mac には Git がプリインストールされています。確認してみましょう:

```bash
git --version
```

バージョンが表示されれば OK です。表示されない場合は以下を実行:

```bash
xcode-select --install
```

## 1.4 GitHub CLI のインストール

GitHub をターミナルから操作するためのツールです。

```bash
brew install gh
```

## 1.5 GitHub アカウントの作成とログイン

### アカウント作成

まだ GitHub アカウントがない場合は [github.com](https://github.com/) でアカウントを作成してください。

### ログイン

ターミナルで以下を実行:

```bash
gh auth login
```

対話形式で聞かれるので、以下のように選択してください:

1. `GitHub.com` を選択
2. `HTTPS` を選択
3. `Login with a web browser` を選択
4. 表示されるコードをコピーして、ブラウザで認証を完了

確認:

```bash
gh auth status
```

「Logged in to github.com」と表示されれば成功です。

## 1.6 Node.js のインストール

Claude Code の実行に Node.js が必要です。

```bash
brew install node
```

確認:

```bash
node --version
```

v18 以上が表示されれば OK です。

## 次のステップ

事前準備が完了しました。[Part 2: Claude Code インストール](part2-installation.md) に進んでください。
