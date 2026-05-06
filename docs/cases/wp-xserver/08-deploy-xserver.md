# 8. xserver にデプロイ

このページを読むと、**PR をマージした内容を xserver の本番 WordPress に反映できる** ようになります。

## やること

1. xserver への接続方法を選ぶ（SSH または WP REST API）
2. 認証情報を **安全に** 設定する
3. Claude Code に頼んでデプロイする

## デプロイ方法の選び方

| 方法 | 向いているケース | 必要な準備 |
|------|----------------|-----------|
| **SSH + rsync** | テーマやプラグインのファイルを更新する場合 | xserver の SSH 設定・SSH 鍵 |
| **WP REST API** | 投稿・固定ページの本文だけ更新する場合 | アプリケーションパスワード |

迷ったら、まず **WP REST API** から試すのがおすすめです（SSH より設定が簡単）。

## 方法 A: WP REST API でデプロイ（簡単）

### 準備: アプリケーションパスワードを発行

WordPress の管理画面で API 用のパスワードを発行します。

1. WordPress 管理画面（`/wp-admin/`）にログイン
2. 「ユーザー」→ 自分のアカウント編集
3. 「アプリケーションパスワード」セクションで、新しいパスワード名（例: `claude-code`）を入力 → 「新しいアプリケーションパスワードを追加」
4. 表示されたパスワード（`xxxx xxxx xxxx xxxx xxxx xxxx`）をコピー

!!! warning "パスワードは一度しか表示されません"
    画面を閉じると二度と確認できません。下のステップでローカルファイルに保存するまで、画面は閉じないでください。

### 認証情報をローカルに保存

ターミナルで以下を実行します。

```bash
touch .env.local
chmod 600 .env.local
```

`.env.local` に次の内容を書き込みます（Claude Code に「`.env.local` に書いてください」と頼んでも OK）。

```
WP_BASE_URL=https://example.com
WP_USERNAME=your-username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

そして `.gitignore` に追加します。

```bash
echo ".env.local" >> .gitignore
```

!!! danger "絶対に GitHub にプッシュしないでください"
    `.env.local` は **個人の認証情報** です。`.gitignore` に登録して、git に含めないようにします。誤ってコミットしてしまった場合は、すぐに WordPress 管理画面でパスワードを失効させてください。

### Claude Code にデプロイを依頼

> `.env.local` の認証情報を使って、変更した固定ページ（`/about/`）の本文を WP REST API で xserver に反映してください。

Claude Code が `curl` か WP REST API クライアントで送信してくれます。

## 方法 B: SSH + rsync でデプロイ

テーマやプラグインのファイル自体を更新するときはこちら。

### 準備 1: xserver で SSH を有効化

xserver のサーバーパネルで SSH を有効化します。

1. xserver サーバーパネルにログイン
2. 「アカウント」→ 「SSH 設定」
3. 「ON」にして「公開鍵認証用鍵ペアの生成」から鍵をダウンロード

詳細手順は xserver の公式ドキュメントを参照してください。

### 準備 2: SSH 鍵をローカルに配置

ダウンロードした鍵ファイル（拡張子 `.key`）を `~/.ssh/` に配置します。

=== "macOS"

    ```bash
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    mv ~/Downloads/your-server.key ~/.ssh/xserver-deploy.key
    chmod 600 ~/.ssh/xserver-deploy.key
    ```

=== "Windows"

    ```powershell
    mkdir $HOME\.ssh
    Move-Item $HOME\Downloads\your-server.key $HOME\.ssh\xserver-deploy.key
    ```

### 準備 3: SSH 設定ファイル

`~/.ssh/config` に次のような設定を追記します（Claude Code に頼んでも OK）。

```
Host xserver
  HostName sv-xxxx.xserver.jp
  User your-account-name
  Port 10022
  IdentityFile ~/.ssh/xserver-deploy.key
```

`HostName` `User` `Port` は xserver サーバーパネルの「SSH 設定」で確認できる値に置き換えます。

### 接続確認

```bash
ssh xserver
```

接続できれば成功です。

### Claude Code にデプロイを依頼

> 変更したテーマファイル（`wp-content/themes/mytheme/`）を、`xserver` の `/home/your-account-name/example.com/public_html/wp-content/themes/mytheme/` に rsync で同期してください。

Claude Code が次のような処理をしてくれます。

```bash
rsync -avz --delete wp-content/themes/mytheme/ xserver:/home/your-account-name/example.com/public_html/wp-content/themes/mytheme/
```

!!! warning "`--delete` はファイルが消えます"
    rsync の `--delete` オプションは「ローカルにないファイルは本番でも削除」します。意図しないファイルが消えないよう、初回は `--dry-run` を付けて事前確認するのが安全です。Claude Code に「dry-run で確認してください」と頼めば対応してくれます。

## ステップ: 本番反映後の確認

デプロイ後、ブラウザで本番サイト（`https://example.com`）を開いて、

- 修正が反映されているか
- 他のページが壊れていないか

を確認します。

!!! tip "キャッシュに注意"
    xserver には「サーバーキャッシュ」「ブラウザキャッシュ」があります。すぐに反映されない場合は、サーバーパネルでキャッシュをクリアするか、シークレットウィンドウで確認します。

## ロールバック（戻し方）

万が一、本番反映後に問題が見つかった場合は、

1. GitHub で 1 つ前のコミットに戻す
2. 戻したものを再度デプロイ

の手順で戻せます。Claude Code に頼みます。

> 直前のデプロイを取り消したいです。1 つ前のコミットの状態を xserver に再デプロイしてください。

## 確認

- [ ] 本番サイトに修正が反映されている
- [ ] 認証情報が `.env.local` に保存され、`.gitignore` に登録されている
- [ ] 必要なら SSH 接続ができる

確認できたら、最後の [9. トラブルシュート](09-troubleshooting.md) を参照してください。
