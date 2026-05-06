# 6. SSH 接続を設定する

このページを読むと、**xserver にコマンドラインから接続できる SSH 環境を準備できる** ようになります。次の章でサイトの中身を GitHub に取り込むためにも、本番にデプロイするときにも、SSH が必要になります。

## やること

1. xserver サーバーパネルで SSH を有効化
2. xserver で SSH 鍵ペアを生成・ダウンロード
3. ローカル PC に鍵を配置・パーミッション設定
4. `~/.ssh/config` で接続情報を登録
5. `ssh xserver` で接続できることを確認

## SSH とは

SSH は「**自分の PC から、ネット越しにサーバーを安全に操作する仕組み**」です。

- 管理画面（ブラウザ）でできない、ファイル単位のコピーや一括処理ができる
- パスワードではなく **鍵ペア** で認証するので安全
- Claude Code がコマンドで操作するときも SSH 経由

!!! info "鍵ペアって？"
    家の鍵に例えると、**公開鍵 = 玄関の鍵穴**、**秘密鍵 = 自分が持つ鍵** です。サーバー側に鍵穴を置いておき、自分の PC に鍵を持っておく形になります。秘密鍵は他人に渡してはいけません。

## ステップ 1: xserver で SSH を有効化

1. xserver サーバーパネル（[https://www.xserver.ne.jp/login_server.php](https://www.xserver.ne.jp/login_server.php)）にログイン
2. 左メニューの「アカウント」→ **「SSH 設定」** を開く
3. 状態が **「OFF」** なら「ON にする」をクリック

「SSH 設定」のページに、後で使う **ホスト名** と **ポート番号** が表示されています（例: `sv-xxxx.xserver.jp` / `10022`）。メモしておきます。

## ステップ 2: SSH 鍵ペアを生成

同じ「SSH 設定」のページに **「公開鍵認証用鍵ペアの生成」** タブがあります。

1. タブをクリック
2. パスフレーズ（鍵を使うときの追加パスワード）を入力
3. 「確認画面へ進む」→ 「生成する」
4. ダウンロードされる `.key` ファイル（秘密鍵）を **大切に保存**

!!! warning "ダウンロードは 1 度だけ"
    秘密鍵ファイルはこのタイミングでしかダウンロードできません。なくすと再生成になります。

!!! tip "パスフレーズを忘れずに"
    パスフレーズは鍵を使うたびに毎回求められます。メモして安全な場所に保管してください。

## ステップ 3: 秘密鍵をローカルに配置

ダウンロードした `.key` ファイル（例: `your-account.key`）を、ローカル PC の `~/.ssh/` フォルダに移動します。Claude Code に頼むのが簡単です。

> ダウンロードフォルダにある `your-account.key` を `~/.ssh/xserver-deploy.key` に移動して、パーミッションを 600 に設定してください。

Claude Code が次のような処理をしてくれます。

=== "macOS"

    ```bash
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    mv ~/Downloads/your-account.key ~/.ssh/xserver-deploy.key
    chmod 600 ~/.ssh/xserver-deploy.key
    ```

=== "Windows"

    ```powershell
    mkdir $HOME\.ssh -ErrorAction SilentlyContinue
    Move-Item $HOME\Downloads\your-account.key $HOME\.ssh\xserver-deploy.key
    icacls $HOME\.ssh\xserver-deploy.key /inheritance:r /grant:r "$env:USERNAME:(R)"
    ```

!!! warning "パーミッションは必ず 600 に"
    秘密鍵が「他のユーザーから読める状態」だと SSH が安全のため接続を拒否します。

## ステップ 4: ~/.ssh/config に接続情報を登録

`~/.ssh/config` ファイルに、xserver への接続を簡単にする設定を書きます。Claude Code に頼みます。

> `~/.ssh/config` に xserver への接続設定を追記してください。
>
> - Host: `xserver`
> - HostName: `sv-xxxx.xserver.jp`（自分のサーバー名）
> - User: `your-account-name`（xserver のアカウント名）
> - Port: `10022`
> - IdentityFile: `~/.ssh/xserver-deploy.key`

ファイルが無ければ作ってくれます。最終的に次のような内容になります。

```
Host xserver
  HostName sv-xxxx.xserver.jp
  User your-account-name
  Port 10022
  IdentityFile ~/.ssh/xserver-deploy.key
```

!!! info "値はサーバーパネルの「SSH 設定」で確認"
    `HostName` `User` `Port` の正確な値は、xserver サーバーパネルの SSH 設定ページに表示されています。

## ステップ 5: 接続を確認する

ターミナルで次を実行します。

```bash
ssh xserver
```

初回は次のようなメッセージが出ます。

```
The authenticity of host '[sv-xxxx.xserver.jp]:10022' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxxxx
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

`yes` と入力 → Enter。次にパスフレーズを聞かれるので、ステップ 2 で設定したパスフレーズを入力します。

接続できると、次のようなプロンプトに変わります。

```
[your-account-name@sv-xxxx ~]$
```

これで xserver 上にいる状態です。`exit` と入力すれば自分の PC に戻ります。

## トラブル対応

### `Permission denied (publickey)`

- 秘密鍵のパーミッションが 600 になっているか確認: `ls -l ~/.ssh/xserver-deploy.key`
- `~/.ssh/config` の `IdentityFile` のパスが正しいか確認

### `Connection refused`

- xserver の SSH 設定が ON になっているか
- ポート番号（`10022` など）が `~/.ssh/config` と一致しているか

### `Host key verification failed`

- 過去に違う鍵で接続した記録が残っています。Claude Code に「`~/.ssh/known_hosts` から xserver の古いエントリを削除してください」と頼んで再接続。

## 確認

- [ ] `~/.ssh/xserver-deploy.key` が存在し、パーミッション 600
- [ ] `~/.ssh/config` に `Host xserver` の設定がある
- [ ] `ssh xserver` で xserver に接続できる

確認できたら、次の [7. xserver の内容を GitHub に取り込む](07-xserver-to-github.md) に進みます。
