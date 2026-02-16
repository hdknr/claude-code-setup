# Part 1: 事前準備（Windows）

Claude Code をインストールする前に必要なツールをセットアップします。

## 1.1 ターミナル（PowerShell）を開く

Windows キーを押して「PowerShell」と入力し、**Windows PowerShell** を起動してください。

!!! tip "ターミナルとは"
    PowerShell は Windows に標準で入っているアプリで、テキストでコマンドを入力してパソコンを操作できます。
    この手順書では、PowerShell にコマンドをコピー＆ペーストして実行していきます。

!!! note "Windows Terminal がある場合"
    Windows 11 には「Windows Terminal」がプリインストールされています。
    Windows Terminal を使う場合も、PowerShell タブで同じ操作ができます。

## 1.2 winget の確認

winget は Windows 標準のパッケージマネージャーです。各種ツールのインストールに使います。

PowerShell で以下のコマンドを実行して、winget が使えることを確認してください:

```powershell
winget --version
```

バージョン番号が表示されれば OK です。

!!! note "winget が見つからない場合"
    Windows 10 の場合、Microsoft Store から「アプリ インストーラー」を更新してください。
    Windows 11 では標準でインストールされています。

## 1.3 Git のインストール

PowerShell で以下のコマンドを実行してください:

```powershell
winget install Git.Git
```

!!! note "インストール後にターミナルを再起動"
    Git のインストール後は PowerShell を一度閉じて、開き直してください。

正しくインストールされたか確認しましょう:

```powershell
git --version
```

`git version 2.x.x` のようにバージョンが表示されれば OK です。

## 1.4 GitHub CLI のインストール

GitHub をターミナルから操作するためのツールです。PowerShell で以下のコマンドを実行してください:

```powershell
winget install GitHub.cli
```

インストール後、PowerShell を再起動してください。

## 1.5 GitHub アカウントの作成とログイン

### アカウント作成

まだ GitHub アカウントがない場合は [github.com](https://github.com/) でアカウントを作成してください。

### ログイン

PowerShell で以下のコマンドを実行してください:

```powershell
gh auth login
```

対話形式で聞かれるので、以下のように選択してください:

1. **What account do you want to log into?** → `GitHub.com`
2. **What is your preferred protocol for Git operations on this host?** → `HTTPS`
3. **Authenticate Git with your GitHub credentials?** → `Yes`
4. **How would you like to authenticate GitHub CLI?** → `Login with a web browser`

ブラウザが開いたら、表示されるコードを入力して認証を完了します。

正しくログインできたか確認しましょう:

```powershell
gh auth status
```

「Logged in to github.com」と表示されれば成功です。

## 1.6 Node.js のインストール

Claude Code の実行に Node.js が必要です。PowerShell で以下のコマンドを実行してください:

```powershell
winget install OpenJS.NodeJS.LTS
```

インストール後、PowerShell を再起動してください。

正しくインストールされたか確認しましょう:

```powershell
node --version
```

`v18.x.x` 以上のバージョンが表示されれば OK です。

## 次のステップ

事前準備が完了しました。[Part 2: Claude Code インストール](part2-installation.md) に進んでください。
