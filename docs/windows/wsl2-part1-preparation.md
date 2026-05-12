# Part 1: 事前準備（WSL2 / Ubuntu）

WSL2 を使って Windows 上に Linux 環境を用意し、Claude Code のインストールに必要なツールをセットアップします。

!!! info "ネイティブ Windows と WSL2 の違い"
    - **ネイティブ Windows**: Windows 標準の PowerShell・winget をそのまま使う方式。手軽。
    - **WSL2 (Ubuntu)**: Windows 上に Linux 環境（Ubuntu）を構築して使う方式。Linux 系の開発ツールやサンドボックス機能を活用したい方向け。

    本パートは **WSL2** を選んだ方向けの手順です。ネイティブ Windows の手順は [Windows / Part 1](part1-preparation.md) を参照してください。

## 1.1 WSL2 とは

WSL2（Windows Subsystem for Linux 2）は、Windows の中で Linux（Ubuntu など）を動かす仕組みです。仮想マシンに似ていますが、Windows のスタートメニューから直接 Linux のターミナルを開ける軽量な構成になっています。

!!! tip "WSL2 を使うメリット"
    - `apt` や `bash` など Linux 標準のコマンドが使える
    - Linux 向けの開発ツール（Docker など）と相性が良い
    - Claude Code の**サンドボックス機能**が利用できる（ネイティブ Windows では非対応）

## 1.2 WSL2 のインストール

スタートメニューから **PowerShell** を**管理者として実行**で開いてください。

!!! warning "管理者として実行が必要です"
    通常の PowerShell では WSL2 のインストールができません。PowerShell アイコンを右クリック →「管理者として実行」を選んでください。

PowerShell で以下のコマンドを実行します:

```powershell
wsl --install
```

このコマンドで以下が一括で行われます:

- WSL2 機能の有効化
- 既定の Linux ディストリビューション（Ubuntu）のダウンロード
- 必要な仮想化機能の有効化

完了したら **Windows を再起動**してください。

!!! note "既に WSL がインストールされている場合"
    `wsl --status` で状態を確認できます。WSL1 を使っている場合は `wsl --set-default-version 2` で WSL2 を既定にしてください。

## 1.3 Ubuntu の初期設定

再起動後、スタートメニューから「**Ubuntu**」を起動してください（自動的に起動することもあります）。

初回起動時にユーザー名とパスワードの設定を求められます:

```
Enter new UNIX username: <好きなユーザー名>
New password: <パスワード>
Retype new password: <パスワード（確認）>
```

!!! tip "ユーザー名・パスワードについて"
    - **ユーザー名**は Windows のアカウント名と別でかまいません。小文字の英字で短めが扱いやすいです（例: `taro`）。
    - **パスワード**は `sudo`（管理者権限）を使うときに毎回入力します。忘れないようにメモしておきましょう。
    - 入力中、パスワードの文字は画面に表示されませんが、正常に入力できています。

## 1.4 パッケージの更新

まず Ubuntu のパッケージ一覧と既存パッケージを最新化します。Ubuntu ターミナルで:

```bash
sudo apt update && sudo apt upgrade -y
```

`[sudo] password for <ユーザー名>:` と表示されたら、1.3 で設定したパスワードを入力してください。

## 1.5 Git の確認

Ubuntu には標準で Git が入っています:

```bash
git --version
```

`git version 2.x.x` のように表示されれば OK です。

!!! note "Git が入っていない場合"
    まれに入っていないことがあります。その場合は次でインストール:
    ```bash
    sudo apt install -y git
    ```

## 1.6 GitHub CLI のインストール

GitHub をターミナルから操作するためのツールです。Ubuntu では GitHub 公式の apt リポジトリを追加して `gh` をインストールします。

以下のコマンドを順に実行してください:

```bash
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install -y gh
```

正しくインストールされたか確認:

```bash
gh --version
```

`gh version 2.x.x` のようにバージョンが表示されれば OK です。

## 1.7 GitHub アカウントの作成とログイン

!!! tip "GitHub を使う理由がピンとこない方へ"
    なぜ Claude Code に GitHub を組み合わせるのかは [なぜ GitHub を使うのか](../usage/why-github.md) で解説しています。

### アカウント作成

まだ GitHub アカウントがない場合は [github.com](https://github.com/) でアカウントを作成してください。

### ログイン

Ubuntu ターミナルで以下を実行:

```bash
gh auth login
```

対話形式で以下のように選んでください:

- `What account do you want to log into?` → **GitHub.com**
- `What is your preferred protocol for Git operations?` → **HTTPS**
- `Authenticate Git with your GitHub credentials?` → **Yes**
- `How would you like to authenticate GitHub CLI?` → **Login with a web browser**

ターミナルに 8 文字のワンタイムコードが表示されます。Enter キーで Windows 側のブラウザが開くので、コードを貼り付けて認証してください。

!!! note "ブラウザが自動で開かない場合"
    `! Failed opening a web browser` と表示されたら、ターミナルに表示された URL（`https://github.com/login/device`）を手動で Windows のブラウザに貼り付け、コードを入力してください。

正しくログインできたか確認:

```bash
gh auth status
```

`Logged in to github.com` と表示されれば成功です。

## 1.8 Windows と WSL2 のファイル連携（参考）

WSL2 で作業するファイルは Ubuntu のホームディレクトリ（`~/` または `/home/<ユーザー名>/`）に置きます。Windows のエクスプローラーから見たい場合は次のいずれかで:

- Ubuntu ターミナルで `explorer.exe .` を実行 → 現在のディレクトリがエクスプローラーで開きます
- エクスプローラーのアドレスバーに `\\wsl$\Ubuntu\home\<ユーザー名>` を入力

!!! warning "Windows 側（/mnt/c/...）にプロジェクトを置かない"
    `/mnt/c/Users/...` 配下に作業ファイルを置くと、ファイル I/O が遅くなり Claude Code の動作も重くなります。**Ubuntu のホームディレクトリ（`~/`）配下にプロジェクトを作成**してください。

## 次のステップ

事前準備が完了しました。[Part 2: Claude Code インストール（WSL2）](wsl2-part2-installation.md) に進んでください。
