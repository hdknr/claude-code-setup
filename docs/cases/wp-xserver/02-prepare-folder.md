# 2. フォルダ作成と plan.md

このページを読むと、**作業フォルダを作って、やりたいことを `plan.md` に書ける** ようになります。

## やること

1. ホームディレクトリに作業フォルダを作る
2. その中に `plan.md` を作り、やりたいことを文章で書く

`plan.md` は、Claude Code に「全体として何をしたいのか」を伝える設計書のような役割です。次の章で、この内容をもとに GitHub Issue を作っていきます。

## ステップ 1: 作業フォルダを作る

ターミナル（macOS は Terminal.app、Windows は PowerShell）を開いて、以下を実行します。

=== "macOS"

    ```bash
    mkdir -p ~/Projects/wp-mysite
    cd ~/Projects/wp-mysite
    ```

=== "Windows"

    ```powershell
    mkdir $HOME\Projects\wp-mysite
    cd $HOME\Projects\wp-mysite
    ```

!!! info "`wp-mysite` の部分はお好きな名前で OK"
    自分のサイトを表す英数字の名前にしてください（例: `wp-mycompany`、`wp-portfolio`）。日本語・スペースは避けます。

## ステップ 2: Claude Code を起動する

作業フォルダの中で Claude Code を起動します。

```bash
claude
```

!!! tip "Claude Code は **そのフォルダ専用** で動きます"
    Claude Code は起動したフォルダの内容を見て作業します。別のフォルダを触りたいときは、いったん終了してから別フォルダに移動して起動し直してください。

## ステップ 3: plan.md を作る

Claude Code に次のように伝えます。

> このフォルダに `plan.md` を作ってください。内容は次の通りです。
>
> ---
>
> # WordPress (xserver) 管理プラン
>
> ## やりたいこと
>
> - xserver で運用している WordPress サイトを GitHub で管理する
> - 修正は stage 環境で確認してから本番に反映する
>
> ## 現状
>
> - サイト URL: https://example.com
> - ホスティング: xserver
> - WordPress バージョン: （管理画面で確認して記入）
> - stage 環境: なし
>
> ## 構築したい環境
>
> - GitHub private リポジトリで管理
> - ローカル PC に Docker で stage 環境を構築
> - 修正は stage で確認 → GitHub に PR → 確認後マージ
> - マージ後、xserver に SSH または WP REST API でデプロイ
>
> ## 制約
>
> - SSH や Docker の知識は乏しい
> - 操作は Claude Code に依頼する形で進めたい

Claude Code が `plan.md` を作ってくれます。

## plan.md のサンプル全文

参考までに、上記の指示で作られる `plan.md` の中身です。コピーして使っても構いません。

```markdown title="plan.md"
# WordPress (xserver) 管理プラン

## やりたいこと

- xserver で運用している WordPress サイトを GitHub で管理する
- 修正は stage 環境で確認してから本番に反映する

## 現状

- サイト URL: https://example.com
- ホスティング: xserver
- WordPress バージョン: （管理画面で確認して記入）
- stage 環境: なし

## 構築したい環境

- GitHub private リポジトリで管理
- ローカル PC に Docker で stage 環境を構築
- 修正は stage で確認 → GitHub に PR → 確認後マージ
- マージ後、xserver に SSH または WP REST API でデプロイ

## 制約

- SSH や Docker の知識は乏しい
- 操作は Claude Code に依頼する形で進めたい
```

## ステップ 4: 自分のサイトの情報に書き換える

サンプルの `https://example.com` を、自分の WordPress サイトの URL に書き換えます。Claude Code に次のように頼めば OK です。

> `plan.md` の `https://example.com` を `https://（自分のサイト URL）` に書き換えてください。

WordPress のバージョンは、サイトの管理画面（`/wp-admin/`）にログインして「ダッシュボード」→「概要」で確認できます。確認できたら同様に書き換えを依頼してください。

## 確認

- [ ] `~/Projects/wp-mysite/` フォルダが作られている
- [ ] その中に `plan.md` がある
- [ ] `plan.md` に自分のサイト URL が書かれている

確認できたら、次の [3. GitHub リポジトリの用意](03-github-repo.md) に進みます。
