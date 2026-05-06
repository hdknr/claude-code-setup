# 8. Docker で stage 環境

このページを読むと、**ローカル PC に Docker で WordPress の動作確認用環境（stage）を作れる** ようになります。前章でローカルに揃えたファイル・データベースを使って、本番と同じ状態を立ち上げます。

## やること

1. Docker Desktop をインストールする
2. Claude Code に頼んで `docker-compose.yml` を作る
3. 前章で取得したファイル・DB を stage にロード
4. ブラウザで `http://localhost:8080` で WordPress を開けるようにする

## 前提

- [7. xserver の内容を GitHub に取り込む](07-xserver-to-github.md) が完了している
  - ローカルに WordPress ファイル一式がある
  - `db/db-export.sql` が手元にある

## なぜ stage が必要か

- 修正を **本番（xserver）に直接当てる** と、もし不具合があったときにサイトが見られなくなります
- ローカル PC の stage で **先に動作確認** すれば、安心して本番に反映できます

## ステップ 1: Docker Desktop をインストール

Docker は「軽量な仮想 PC を、必要なときだけ動かせる仕組み」です。WordPress の動作環境を、自分の PC を汚さずに動かせます。

=== "macOS"

    [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) からインストーラをダウンロードしてインストール。

    インストール後、`Docker.app` を起動するとメニューバーにクジラのアイコンが現れます。

=== "Windows"

    [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) からインストーラをダウンロードしてインストール。

    途中で「WSL 2 の機能を有効にする」を求められたら、画面の指示に従って有効化します。

確認は次のコマンドで。

```bash
docker --version
```

`Docker version 2X.X.X, ...` のように表示されれば OK です。

## ステップ 2: docker-compose.yml を Claude Code に作ってもらう

Claude Code に次のように頼みます。

> このフォルダに、WordPress を動かす `docker-compose.yml` を作ってください。
>
> - WordPress のバージョンは現状と同じ
> - データベースは MariaDB
> - ポートは `8080:80`
> - 既存の `wp-content/` をコンテナの `/var/www/html/wp-content` にマウント
> - DB の初期化用に `./db/` をコンテナの `/docker-entrypoint-initdb.d` にマウント

Claude Code が `docker-compose.yml` を作ってくれます。`./db/db-export.sql` が初回起動時に自動でインポートされる構成にしてもらうと、手作業が減ります。

## ステップ 3: 起動する

Claude Code に頼みます。

> stage 環境を起動してください。

または、自分でターミナルから起動してもよいです。

```bash
docker compose up -d
```

数十秒待つと、ブラウザで `http://localhost:8080` を開けば WordPress が表示されます。前章で取得した DB が初回起動時にインポートされ、本番と同じ記事・ページが入った状態になります。

## ステップ 4: stage の WordPress URL を調整

DB は本番から持ってきているので、サイト内のリンクや画像 URL が `https://example.com` のままになっています。Claude Code に頼んで書き換えます。

> stage の WordPress の URL を `http://localhost:8080` に書き換えてください。`wp-cli` の `search-replace` を使って構いません。

Claude Code が次のような処理をしてくれます。

```bash
docker compose exec wordpress wp search-replace 'https://example.com' 'http://localhost:8080' --allow-root
```

## ステップ 5: wp-config.php をローカル用に配置

前章で `wp-config.local.php` として保管したファイルを、stage 用にコピーまたは配置します。

> `wp-config.local.php` を `wp-config.php` としてコピーし、DB ホスト・ユーザー・パスワードを `docker-compose.yml` の値に合わせて書き換えてください。

`.gitignore` で `wp-config*.php` を除外しているので、このファイルは GitHub には push されません。

## ステップ 6: 動作確認

ブラウザで `http://localhost:8080` を開いて、

- トップページが本番と同じように表示される
- 個別の記事ページに遷移できる
- 画像が表示される
- 管理画面（`/wp-admin/`）にログインできる

を確認します。

!!! tip "管理画面のログイン情報は本番と同じ"
    DB を本番から持ってきているので、ログインに使うユーザー名とパスワードも本番のものになります。

## ステップ 7: 起動・停止のコマンドを覚える

| やりたいこと | コマンド |
|---|---|
| 起動 | `docker compose up -d` |
| 停止 | `docker compose down` |
| ログを見る | `docker compose logs -f` |

毎回覚える必要はなく、Claude Code に「stage を起動してください / 止めてください」と頼めば OK です。

## 確認

- [ ] Docker Desktop が起動している
- [ ] `http://localhost:8080` で WordPress が表示される
- [ ] 本番と同じ記事・ページが見える
- [ ] 画像が表示される

確認できたら、次の [9. 修正と PR](09-edit-and-pr.md) に進みます。
