# Docker をやさしく理解する

Docker は WordPress のような Web サービスを **自分の PC で安全に動かす** ための仕組みです。普段 Web 制作や IT の現場で耳にする言葉が出てきますが、**専門知識がなくても使える** ように、ここで全体像を整理します。

!!! info "このページの読みかた"
    最初から最後まで読まなくても大丈夫です。「Docker って結局なに？」が分かる **「ひとことで言うと」** と、よく聞く言葉が出てくる **「用語」** だけ押さえれば、各事例ページに戻って作業を進められます。

## ひとことで言うと

Docker は、**自分の PC の中に「使いたいときだけ動かせる、独立した小さい PC」を作れる仕組み** です。

- WordPress、データベース、メールサーバーなど、**動かすのが面倒なソフト** を一発で立ち上げられる
- 自分の PC を **汚さない**（不要になったら丸ごと消せる）
- どの PC でも **同じ環境** が再現できる（同僚や別の PC でも同じ動き）

たとえば、xserver で動いている WordPress を **そっくりそのまま** 自分の PC で動かせる、というのが Docker でできることです。

## なぜ必要なのか

WordPress を自分の PC で動かそうとすると、本来なら次のソフトをすべて入れる必要があります。

- Web サーバー（Apache または Nginx）
- PHP（決まったバージョン）
- MySQL または MariaDB（データベース）
- WordPress 本体

これを 1 つずつインストールしていくと、

- バージョンの組み合わせで動かないことがある
- 自分の PC の他の作業と **干渉** することがある
- 不要になったときに **きれいに消すのが難しい**

という問題が起きます。Docker を使うと、上記をまとめて **隔離された箱** に入れて動かせるので、これらの面倒ごとがなくなります。

## 比喩で理解する

Docker を **「家具付きの貸しアパート」** だと思ってください。

| 普通の方法 | Docker |
|---|---|
| 自分の家に、机・椅子・ベッドを買って組み立てる | アパートを借りる → 部屋には最初から家具が揃っている |
| 引っ越すときに全部処分するのが大変 | 鍵を返せば終わり（自分の持ち物には何も残らない） |
| 別の家でも同じ環境にしたければ、同じ家具を買い直す | 同じ間取りのアパートをもう 1 つ借りるだけ |

「家具付きアパート」が **コンテナ**、「アパートの間取り図」が **イメージ** です（次の用語を参照）。

## よく出てくる用語

### Docker Desktop / OrbStack

PC にインストールする **本体アプリ**。これが起動していないと Docker は動きません。

- **Windows**: 標準は **Docker Desktop**（タスクトレイにクジラのアイコン）
- **macOS**: 標準は **Docker Desktop** だが、軽量で高速な **OrbStack** も人気（後述）

どちらを選んでも `docker` コマンドの使い方は同じです。

### コンテナ（Container）

実際に動いている **小さい PC** のこと。WordPress 用のコンテナ、データベース用のコンテナ、というように **役割ごとに 1 つずつ** 立ち上げて使います。

### イメージ（Image）

コンテナの **設計図 / レシピ**。「WordPress 6.5 が入っていて、こういう設定で動く」という型を表します。

レシピ（イメージ）から料理（コンテナ）を作る関係です。同じイメージから何個でもコンテナを起動できます。

### ボリューム（Volume）

コンテナの **外側に保管されるデータ置き場**。コンテナ自体は消えても、ボリュームに保存したデータ（記事や画像）は残るので、安心して使えます。

### docker-compose.yml

「WordPress と MariaDB を同時に立ち上げて、こうつなぐ」という **設計をまとめて書いたファイル**。これがあれば、`docker compose up` ひとつで全部が起動します。

WordPress の事例で扱うのは主にこの `docker-compose.yml` です。中身は Claude Code が作ってくれます。

## 基本コマンド（覚えなくて OK）

Claude Code に「stage を起動してください」と頼めばすべて代わりにやってくれますが、参考までに紹介します。

| やりたいこと | コマンド |
|---|---|
| 起動 | `docker compose up -d` |
| 停止 | `docker compose down` |
| ログを見る | `docker compose logs -f` |
| 動いているコンテナ一覧 | `docker ps` |

`-d` は「バックグラウンドで動かす」という意味です。これがないとターミナルが占有されてしまいます。

## よくある誤解と Q&A

### Q. Docker Desktop / OrbStack を起動 = WordPress が動く？

いいえ。Docker Desktop（または OrbStack）は **箱を作る土台** で、WordPress を動かすには **追加でコンテナを起動** する必要があります（`docker compose up -d`）。

### Q. PC を再起動したらどうなる？

コンテナは止まります。Docker Desktop / OrbStack を再起動した後、もう一度 `docker compose up -d` を実行（または Claude Code に頼む）してください。データはボリュームに残っているので消えません。

### Q. 不要になったら？

`docker compose down` でコンテナを止めて、Docker Desktop / OrbStack をアンインストールすれば、PC からほぼ何も残りません。**自分の PC の他の作業は何の影響も受けません**。

### Q. PC が重くなる？

Docker Desktop が動いている間は、それなりにメモリを使います。WordPress 程度なら問題ありませんが、PC のスペックが低い場合は **使い終わったら停止する** 習慣をつけると快適です。

なお、**macOS では OrbStack を使うとかなり軽くなります**（次の「インストール」セクション参照）。

### Q. xserver の本番に影響する？

ありません。Docker は **完全に自分の PC の中だけ** で動いていて、xserver や本番サイトには一切触りません。安心して試せます。

## インストール

Docker を動かすためのアプリには、いくつか選択肢があります。**macOS では OrbStack、Windows では Docker Desktop** が標準的なおすすめです。

### macOS：OrbStack を推奨

[OrbStack](https://orbstack.dev/) は Mac 専用に作られた Docker 環境です。Docker Desktop に対して次のような利点があります。

| | Docker Desktop for Mac | OrbStack |
|---|---|---|
| **メモリ消費** | 多い（数 GB 占有することも） | **少ない**（バックグラウンドでもごくわずか） |
| **起動の速さ** | 数十秒 | **数秒** |
| **バッテリー消費** | やや多い | **少ない** |
| **Apple Silicon 対応** | 対応済み | **ネイティブ** |
| **互換性** | Docker 本家 | **Docker コマンドはそのまま使える** |
| **無料利用範囲** | 個人・小規模事業者は無料 | **個人利用は無料**（業務利用は有償） |

`docker compose up -d` などのコマンドは **OrbStack でもそのまま動きます**。事例のページに出てくるコマンドは書き換える必要がありません。

#### インストール手順

1. [https://orbstack.dev/](https://orbstack.dev/) を開いて「Download」をクリック
2. ダウンロードした `OrbStack.dmg` を開いて、`OrbStack.app` を「Applications」フォルダにドラッグ
3. `OrbStack.app` を起動 → 初回セットアップ画面で「Docker」を選択
4. メニューバーに OrbStack のアイコンが出れば準備完了

ターミナルで動作確認:

```bash
docker --version
```

`Docker version 2X.X.X, ...` のように表示されれば OK です。

!!! info "業務で使う場合のライセンス"
    OrbStack は **個人利用は無料**、**会社の業務で使う場合は有償**（年額・月額プラン）です。会社の Mac で WordPress を運用する用途では、ライセンス購入が必要になります。詳しくは [OrbStack のライセンスページ](https://orbstack.dev/pricing) を参照してください。
    
    ライセンス購入が難しい場合は、**Docker Desktop**（次節）でも同じことができます。

#### Docker Desktop for Mac でも問題ありません

OrbStack のライセンスを購入できない、もしくは慣れた Docker Desktop を使いたい場合は、[Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) でも同じ事例を進められます。手順は同じです。

### Windows：Docker Desktop

[Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) からダウンロードしてインストール。途中で「WSL 2 を有効にする」と聞かれたら、画面の指示に従って有効化します。

インストール後、タスクトレイの **クジラのアイコン** が起動していれば準備完了です。

!!! info "Windows のライセンス"
    Docker Desktop は、**個人利用・小規模事業者（従業員 250 名未満かつ年商 1000 万ドル未満）・教育用途・非商用 OSS** は無料で利用できます。これを超える規模の企業で業務利用する場合は、有償の「Docker Business」サブスクリプションが必要です。

## どこで使うか（事例へのリンク）

- [WordPress (xserver) を Claude Code で管理 / 8. Docker で stage 環境](../cases/wp-xserver/08-stage-docker.md) — 実際に Docker で WordPress の動作確認環境を立ち上げます

## 困ったときは

- [トラブルシュート（wp-xserver 事例）](../cases/wp-xserver/11-troubleshooting.md) の「Docker 関連」セクションに詰まりどころをまとめています
- それでも解決しないときは、Claude Code に **エラーメッセージをそのまま貼り付けて** 相談してください
