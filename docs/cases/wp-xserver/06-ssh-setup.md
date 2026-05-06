# 6. SSH 接続を設定する

このページを読むと、**xserver にコマンドラインから接続できる SSH 環境を準備できる** ようになります。次の章でサイトの中身を GitHub に取り込むためにも、本番にデプロイするときにも、SSH が必要になります。

## やること

1. xserver サーバーパネルで SSH を有効化（ブラウザ操作）
2. xserver で SSH 鍵ペアを生成・ダウンロード（ブラウザ操作）
3. **ローカルへの配置・設定・接続確認は Claude Code にまとめて依頼**

「ファイルのどこに何を置くか」「パーミッション設定」「`~/.ssh/config` の編集」「接続テスト」といった **ローカル PC 側の作業はすべて Claude Code に頼みます**。手作業より速く、ファイル名や改行コードのような目に見えない落とし穴も避けられます。

!!! info "SSH の鍵管理が初めての人へ"
    [SSH と鍵ファイルをやさしく理解する](../../tools/ssh/index.md) を先に読むと、用語（公開鍵 / 秘密鍵 / `~/.ssh/`）が分かって作業の見通しが良くなります。Windows ユーザーは [Windows での SSH 鍵ファイル管理](../../tools/ssh/windows.md) も合わせて。

## SSH とは

SSH は「**自分の PC から、ネット越しにサーバーを安全に操作する仕組み**」です。

- 管理画面（ブラウザ）でできない、ファイル単位のコピーや一括処理ができる
- パスワードではなく **鍵ペア** で認証するので安全
- Claude Code がコマンドで操作するときも SSH 経由

!!! info "鍵ペアって？"
    家の鍵に例えると、**公開鍵 = 玄関の鍵穴**、**秘密鍵 = 自分が持つ鍵** です。サーバー側に鍵穴を置いておき、自分の PC に鍵を持っておく形になります。秘密鍵は他人に渡してはいけません。

## ステップ 1: xserver で SSH を有効化（ブラウザ）

1. xserver サーバーパネル（[https://www.xserver.ne.jp/login_server.php](https://www.xserver.ne.jp/login_server.php)）にログイン
2. 左メニューの「アカウント」→ **「SSH 設定」** を開く
3. 状態が **「OFF」** なら「ON にする」をクリック

「SSH 設定」のページに、後で使う **ホスト名** と **ポート番号** が表示されています（例: `sv-xxxx.xserver.jp` / `10022`）。メモしておきます。

## ステップ 2: SSH 鍵ペアを生成（ブラウザ）

同じ「SSH 設定」のページに **「公開鍵認証用鍵ペアの生成」** タブがあります。

1. タブをクリック
2. パスフレーズ（鍵を使うときの追加パスワード）を入力
3. 「確認画面へ進む」→ 「生成する」
4. ダウンロードされる `.key` ファイル（秘密鍵）を **大切に保存**

!!! warning "ダウンロードは 1 度だけ"
    秘密鍵ファイルはこのタイミングでしかダウンロードできません。なくすと再生成になります。

!!! tip "パスフレーズを忘れずに"
    パスフレーズは鍵を使うたびに毎回求められます。メモして安全な場所に保管してください。

## ステップ 3: 配置から接続確認まで Claude Code にまとめて依頼

ここから先は、Claude Code に一気にやってもらいます。エクスプローラーや Finder を開いてファイルを動かしたり、ターミナルでコマンドを打ったりは **一切不要** です。

### 依頼文（コピペして値だけ書き換える）

ステップ 2 でダウンロードした秘密鍵が `Downloads` フォルダにある状態で、Claude Code に次のように頼みます。

> xserver への SSH 接続をセットアップしてください。次のことを順番にやって、最後に接続確認まで報告してください。
>
> 1. ダウンロードフォルダにある `your-account.key` を `~/.ssh/xserver-deploy.key` に移動
> 2. 秘密鍵のパーミッションを「自分だけ読める」状態に設定（Windows なら `icacls`、macOS なら `chmod 600`）
> 3. `~/.ssh/config` に xserver への接続設定を追記（既にあれば更新）
>    - Host: `xserver`
>    - HostName: `sv-xxxx.xserver.jp`（自分のサーバー名）
>    - User: `your-account-name`
>    - Port: `10022`
>    - IdentityFile: `~/.ssh/xserver-deploy.key`
> 4. `ssh xserver` で接続できることを確認
> 5. 上記の各ステップが成功したかを箇条書きで報告

`sv-xxxx.xserver.jp` / `your-account-name` / `10022` の値は、ステップ 1 で開いた xserver の SSH 設定ページに表示されている値に置き換えてください。

!!! tip "Windows の人は OneDrive 同期だけ気にしてください"
    秘密鍵をうっかり OneDrive 配下のフォルダ（デスクトップ・ドキュメント等）に保存していると、クラウドに鍵がコピーされてしまいます。`~/.ssh/`（= `C:\Users\<名前>\.ssh\`）はホーム直下なので通常は同期対象外です。詳しくは [Windows での SSH 鍵ファイル管理](../../tools/ssh/windows.md) を参照。

### 接続確認のときに聞かれること

`ssh xserver` の初回実行で、Claude Code から次のような確認が来ることがあります。

- **「サーバーのフィンガープリントが未登録です。続行しますか？」** → 続行を選択（初回だけ）
- **「秘密鍵のパスフレーズを入力してください」** → ステップ 2 で設定したパスフレーズを入力

接続できると、Claude Code が「xserver に接続できました」と報告してくれます。これで完了です。

### うまくいかなかったとき

エラーが出たら、メッセージを **そのままコピーして** Claude Code に貼り付ければ、原因と対処を教えてくれます。

> SSH の接続でこういうエラーが出ました。原因と直し方を教えてください。
>
> ```
> （ここにエラー全文を貼る）
> ```

## 確認

- [ ] Claude Code から「xserver に接続できました」と報告があった

接続できたら、次の [7. xserver の内容を GitHub に取り込む](07-xserver-to-github.md) に進みます。

---

## リファレンス：自分で確認するには？

「Claude Code が裏で何をやっているのか知りたい」「結果を自分の目で確かめたい」人向けの内容です。**読まなくても作業は完了します**。

### 鍵が正しく置かれているかを自分で確認する

=== "macOS"

    ターミナルで:
    
    ```bash
    ls -l ~/.ssh/xserver-deploy.key
    ```
    
    `-rw-------` のような表示で、自分のユーザー名だけが出ていれば OK。

=== "Windows"

    PowerShell で:
    
    ```powershell
    Test-Path $HOME\.ssh\xserver-deploy.key
    icacls $HOME\.ssh\xserver-deploy.key
    ```
    
    自分のユーザー名と `(R)`（読み取り）だけが表示されていれば OK。

### `~/.ssh/config` の中身を自分で確認する

最終的に次のような内容になっているはずです。

```
Host xserver
  HostName sv-xxxx.xserver.jp
  User your-account-name
  Port 10022
  IdentityFile ~/.ssh/xserver-deploy.key
```

VS Code で開いて確認するのがおすすめです（Windows の場合は **改行コードが LF** になっているかも併せて確認）。

### 自分で接続テストをする

ターミナル（Windows なら PowerShell）で次を実行します。

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

xserver 上にいる状態です。`exit` と入力すれば自分の PC に戻ります。

### Claude Code が裏で実行しているコマンド

参考までに、実際に実行されているコマンドの中身です。

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

!!! warning "パーミッションは必ず厳しく"
    秘密鍵が「他のユーザーから読める状態」だと SSH が安全のため接続を拒否します。Claude Code がやっている `chmod 600` / `icacls` の処理がこれに相当します。

### 詰まりやすいエラーと対応

| エラー | 主な原因 | 対応 |
|---|---|---|
| `Permission denied (publickey)` | 秘密鍵のパーミッション、`IdentityFile` のパス間違い、公開鍵未登録 | エラー全文を Claude Code に渡して直してもらう |
| `Connection refused` | xserver の SSH 設定が OFF、ポート番号間違い | ステップ 1 をブラウザで再確認 |
| `Host key verification failed` | 過去の `known_hosts` エントリと鍵が変わった | Claude Code に「`~/.ssh/known_hosts` から xserver の古いエントリを削除して」と依頼 |
| Windows で `Permissions ... are too open.` | パーミッションが緩い | Claude Code に「鍵のパーミッションを設定し直して」と依頼 |

Windows 特有のエラーは [Windows での SSH 鍵ファイル管理](../../tools/ssh/windows.md) のリファレンス節に「詰まりやすいエラーと対応」表があります。
