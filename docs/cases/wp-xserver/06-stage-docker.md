# 6. Docker で stage 環境

このページを読むと、**ローカル PC に Docker で WordPress の動作確認用環境（stage）を作れる** ようになります。

## やること

1. Docker Desktop をインストールする
2. Claude Code に頼んで `docker-compose.yml` を作る
3. xserver のサイトデータをローカルに取り込む
4. ブラウザで `http://localhost:8080` で WordPress を開けるようにする

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
> - WordPress のバージョンは `plan.md` に書いた現状と同じバージョン
> - データベースは MariaDB
> - ポートは `8080:80`
> - ボリュームは `./wp-content` をコンテナの `/var/www/html/wp-content` にマウント

Claude Code が `docker-compose.yml` を作ってくれます。

## ステップ 3: 起動する

Claude Code に頼みます。

> stage 環境を起動してください。

または、自分でターミナルから起動してもよいです。

```bash
docker compose up -d
```

数十秒待つと、ブラウザで `http://localhost:8080` を開けば WordPress のセットアップ画面が表示されます。

## ステップ 4: xserver のサイトデータを取り込む

xserver のサイト内容をローカルの stage に持ってきます。これには 2 つの方法があります。

### 方法 A: All-in-One WP Migration プラグインを使う（推奨）

WordPress の管理画面から扱える方法です。SSH や FTP の知識は不要です。

1. **xserver の本番** で `All-in-One WP Migration` プラグインをインストール・有効化
2. 「エクスポート」→ ファイルとして書き出し → ダウンロード
3. **ローカルの stage**（`http://localhost:8080`）でも同プラグインをインストール・有効化
4. 「インポート」で先ほどのファイルを読み込む

!!! info "サイズ制限に当たったら"
    無料版は 80MB までの制限があります。大きい場合は管理画面の「設定」→「メディア」で制限を確認するか、Claude Code に「アップロード上限を引き上げる方法」を聞いてください。

### 方法 B: SSH + WP-CLI（本格運用向け）

xserver の SSH 接続が設定済みであれば、WP-CLI でデータベースとファイルを取得できます。Claude Code に頼んで SSH 設定から進める形になります。

> xserver に SSH 接続して、データベースとファイルをローカル stage にコピーする手順を進めてください。SSH の設定がまだなら、その方法から教えてください。

詳細は [8. xserver にデプロイ](08-deploy-xserver.md) でも触れます。

## ステップ 5: stage の WordPress URL を調整

xserver からインポートしたあと、ローカルでは URL が `https://example.com` のままになっていることがあります。Claude Code に頼んで書き換えます。

> stage の WordPress の URL を `http://localhost:8080` に書き換えてください。`wp-cli` の `search-replace` を使って構いません。

## ステップ 6: 起動・停止のコマンドを覚える

| やりたいこと | コマンド |
|---|---|
| 起動 | `docker compose up -d` |
| 停止 | `docker compose down` |
| ログを見る | `docker compose logs -f` |

毎回覚える必要はなく、Claude Code に「stage を起動してください / 止めてください」と頼めば OK です。

## 確認

- [ ] Docker Desktop が起動している
- [ ] `http://localhost:8080` で WordPress が表示される
- [ ] xserver のサイト内容が stage に反映されている

確認できたら、次の [7. 修正と PR](07-edit-and-pr.md) に進みます。
