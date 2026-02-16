# Part 1: 事前準備

Claude Code をインストールする前に必要なツールをセットアップします。

## 1.1 ターミナルを開く

![ターミナルの開き方](images/screenshots/open-terminal.svg)

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

![GitHub アカウント作成画面](images/screenshots/github-signup.png)

### ログイン

ターミナルで以下を実行:

```bash
gh auth login
```

対話形式で聞かれるので、以下の図のように選択してください:

![gh auth login の操作ガイド](images/screenshots/gh-auth-flow.svg)

ステップ❹でブラウザが開いたら、コードを入力して認証を完了します:

![GitHub デバイス認証画面](images/screenshots/github-device-auth.png)

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
