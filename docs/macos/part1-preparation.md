# Part 1: 事前準備

Claude Code をインストールする前に必要なツールをセットアップします。

## 1.1 ターミナルを開く

![ターミナルの開き方](../images/screenshots/open-terminal.svg)

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

!!! info "Command Line Tools のインストールダイアログが表示されたら"
    Homebrew のインストール中に、以下のようなダイアログが表示されることがあります。これは Homebrew が必要とする開発ツール（Command Line Tools）を自動的にインストールするためのものです。**「インストール」をクリック**してください。

    ![Command Line Tools インストールダイアログ](../images/screenshots/clt-dialog.png)

    インストールには数分かかる場合があります。完了するまでそのまま待ってください。

インストール完了後、表示される「Next steps」の指示に従ってパスを設定してください:

```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

正しくインストールされたか確認しましょう。ターミナルで以下のコマンドを実行してください:

```bash
brew --version
```

`Homebrew 4.x.x` のようにバージョン番号が表示されれば成功です。

## 1.3 Git の確認

Homebrew のインストール時に Command Line Tools と一緒に Git も導入されています。ターミナルで以下のコマンドを実行して確認しましょう:

```bash
git --version
```

`git version 2.x.x` のようにバージョンが表示されれば OK です。

## 1.4 GitHub CLI のインストール

GitHub をターミナルから操作するためのツールです。ターミナルで以下のコマンドを実行してください:

```bash
brew install gh
```

## 1.5 GitHub アカウントの作成とログイン

!!! tip "GitHub を使う理由がピンとこない方へ"
    なぜ Claude Code に GitHub を組み合わせるのかは [なぜ GitHub を使うのか](../usage/why-github.md) で解説しています。先に読むとこの先の手順の意味が理解しやすくなります。

### アカウント作成

まだ GitHub アカウントがない場合は [github.com](https://github.com/) でアカウントを作成してください。

![GitHub アカウント作成画面](../images/screenshots/github-signup.png)

### ログイン

ターミナルで以下のコマンドを実行してください:

```bash
gh auth login
```

対話形式で聞かれるので、以下の図のように選択してください:

![gh auth login の操作ガイド](../images/screenshots/gh-auth-flow.svg)

ステップ❹に進むと、**ターミナルに 8 桁の認証コードが表示** されます（例: `XXXX-XXXX`）。このコードを控えてから Enter キーを押すと、ブラウザで GitHub のデバイス認証画面が開きます。

![GitHub デバイス認証画面](../images/screenshots/github-device-auth.png)

ブラウザに切り替えたら、**ターミナルに表示された 8 桁のコード** を入力して「Continue」→「Authorize github」の順に進めば認証完了です。

!!! tip "ターミナルのコードを見失ったとき"
    ブラウザに切り替えるとターミナルのコードが画面外に流れてしまうことがあります。その場合はターミナルを少しスクロールアップすると `! First copy your one-time code: XXXX-XXXX` の行が見つかります。見つからなければ `Ctrl + C` で中断し、もう一度 `gh auth login` を実行してください。

正しくログインできたか確認しましょう。ターミナルで以下のコマンドを実行してください:

```bash
gh auth status
```

「Logged in to github.com」と表示されれば成功です。

## 次のステップ

事前準備が完了しました。[Part 2: Claude Code インストール](part2-installation.md) に進んでください。

!!! info "Node.js は不要になりました"
    以前は Claude Code のインストールに Node.js が必要でしたが、現在は公式の**ネイティブインストーラー**を使うため Node.js は不要です。Part 2 で詳しく説明します。
