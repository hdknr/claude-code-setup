# 7. xserver の内容を GitHub に取り込む

このページを読むと、**今 xserver で動いている WordPress の中身（テーマ・プラグイン・アップロード画像・データベース）を、GitHub のリポジトリに取り込める** ようになります。

## やること

1. SSH 経由で xserver から WordPress のファイルをローカルに取得
2. データベースをエクスポートしてローカルに保存
3. 機密ファイルを `.gitignore` で除外
4. すべてをコミットして GitHub に push

これが終わると、ローカル PC・GitHub・xserver の 3 か所に「同じサイトの状態」が揃います。次の章で Docker stage 環境に取り込む素材も、これでそろいます。

## 前提

- [6. SSH 接続を設定する](06-ssh-setup.md) が完了し、`ssh xserver` で接続できる
- 作業フォルダ（例: `~/Projects/wp-mysite`）に移動済み

## ステップ 1: xserver のディレクトリ構造を確認

xserver では、サイトのファイルは次の場所にあります。

```
/home/your-account-name/example.com/public_html/
```

`example.com` の部分は実際のドメイン名に置き換わります。Claude Code に頼んで確認できます。

> `ssh xserver` で接続して、`example.com` ディレクトリ配下にどんなファイルがあるか `ls` で見てください。

## ステップ 2: WordPress ファイルをローカルに取得

`rsync` を使って、xserver の `public_html` の中身をローカルの作業フォルダに同期します。

Claude Code に頼みます。

> xserver の `~/example.com/public_html/` の中身を、このフォルダにコピーしてください。
>
> - `rsync` を使う
> - `wp-config.php` は除外（個別に扱う）
> - 進捗が見える形で実行

Claude Code が次のような処理をしてくれます。

```bash
rsync -avz --exclude='wp-config.php' \
  xserver:~/example.com/public_html/ ./
```

!!! info "rsync とは"
    ファイルやディレクトリをサーバー間で **差分だけコピー** するコマンドです。初回はすべて転送しますが、2 回目以降は変更のあったファイルだけが転送されます。

!!! warning "uploads が大きいときは時間がかかります"
    `wp-content/uploads/` に画像が大量にある場合、初回コピーには数十分〜数時間かかることがあります。Claude Code に「進捗を表示しながら」と頼めば、完了するまで状況が見えます。

## ステップ 3: データベースをエクスポート

WordPress は記事やページの本文を **データベース** に保存しています。ファイルだけでは情報が足りないので、データベースもエクスポートします。

Claude Code に頼みます。

> xserver にログインして、WP-CLI でデータベースを `db-export.sql` にエクスポートし、ローカルにダウンロードしてください。

Claude Code が次のような処理をしてくれます。

```bash
ssh xserver "cd ~/example.com/public_html && wp db export ~/db-export.sql"
scp xserver:~/db-export.sql ./db/db-export.sql
ssh xserver "rm ~/db-export.sql"
```

!!! info "WP-CLI が使えない場合"
    xserver では WP-CLI を使えるアカウントと使えないアカウントがあります。使えない場合は、xserver サーバーパネルの **phpMyAdmin** からエクスポートする方法を Claude Code に教えてもらってください。

## ステップ 4: 機密ファイルを除外する

GitHub に push する前に、**絶対に公開してはいけないファイル** を `.gitignore` に登録します。

Claude Code に頼みます。

> このフォルダに `.gitignore` を作って、以下を除外してください。
>
> - `wp-config.php`（DB 接続情報・認証キー）
> - `.env.local`（個人の認証情報）
> - `*.log`、`error_log`（ログファイル）
> - `db/db-export.sql`（DB ダンプは別管理が望ましい）
> - `wp-content/uploads/` 以下の巨大ファイル（必要なら検討）

`.gitignore` の例:

```gitignore
# WordPress
wp-config.php

# 認証情報
.env.local
.env

# ログ
*.log
error_log

# DB ダンプ（GitHub には載せない）
db/*.sql

# システム
.DS_Store
Thumbs.db
```

!!! danger "wp-config.php は絶対に push しない"
    `wp-config.php` にはデータベースのパスワードや認証キーが含まれます。GitHub が private でも、流出のリスクを下げるために最初から含めないのが鉄則です。

## ステップ 5: wp-config.php をローカル用に分けて保管

`wp-config.php` 自体はローカルや stage で必要になります。Claude Code に頼んで安全に保管します。

> `wp-config.php` をひとまず xserver から取得し、`wp-config.local.php` という名前でローカルに保存してください。`.gitignore` には `wp-config*.php` を追加してください。

将来、stage や本番のそれぞれの設定を持ち回すときに、テンプレート化して扱いやすくなります。

## ステップ 6: コミットして GitHub に push

Claude Code に頼みます。

> ここまでのファイルを git に登録して、GitHub の main ブランチに push してください。コミットメッセージは「`Initial import from xserver`」でお願いします。

Claude Code が次のような処理をしてくれます。

```bash
git add .gitignore wp-content wp-includes wp-admin index.php ...
git commit -m "Initial import from xserver"
git push origin main
```

## ステップ 7: GitHub で確認

ブラウザでリポジトリを開いて、ファイル一覧に WordPress 一式が登録されていることを確認します。

```bash
gh repo view --web
```

確認するポイント:

- `wp-content/themes/` が登録されている
- `wp-content/plugins/` が登録されている
- **`wp-config.php` が登録されていない**（重要）
- **`.env.local` などの認証情報が登録されていない**

!!! danger "もし誤って機密ファイルを push してしまったら"
    `wp-config.php` などを誤って push してしまった場合、GitHub の履歴からも完全に消す必要があります。Claude Code に「履歴ごと削除する手順を教えてください」と相談してください。同時に、データベースのパスワードや認証キーは **すべて差し替え** ます。

## なぜ最初に GitHub に取り込むのか

| もし取り込まなかったら | 取り込んだ後 |
|---|---|
| Docker stage を作るたびに xserver から落とす必要 | ローカルにあるファイルから即構築 |
| 修正前の状態が記録に残らない | **xserver の現状が起点として履歴に残る** |
| 複数人で作業すると食い違いが起きる | GitHub を起点に同期できる |

## 確認

- [ ] xserver の WordPress ファイルが作業フォルダに揃っている
- [ ] DB エクスポート（`db/db-export.sql`）がローカルにある
- [ ] `.gitignore` に機密ファイルが登録されている
- [ ] GitHub の main ブランチに push 済み（`wp-config.php` は含まれない）

確認できたら、次の [8. Docker で stage 環境](08-stage-docker.md) に進みます。
