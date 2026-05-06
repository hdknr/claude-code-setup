# 4. plan.md から Issue を作る

このページを読むと、**`plan.md` の内容を Claude Code に GitHub Issue として登録してもらえる** ようになります。

## やること

1. Claude Code に `plan.md` を読ませる
2. 内容を GitHub Issue として登録してもらう

## なぜ Issue にするのか

`plan.md` に書いた「やりたいこと」を **GitHub Issue** に転記することで、

- Issue のコメント欄で **Claude Code と対話** できる
- 後から **何を依頼したか履歴** が辿れる
- 別の人にも経緯を共有できる

ようになります。Issue は「作業依頼書」のようなものです。

## ステップ 1: Claude Code に依頼する

Claude Code に次のように伝えます。

> `plan.md` の内容を読んで、GitHub にこのリポジトリの Issue として登録してください。
>
> - タイトル: `WordPress 管理環境の構築`
> - 本文: `plan.md` の内容をそのまま貼り付け
> - 末尾に「不明点や追加の指示はこの Issue のコメントでお願いします」と一言追加

Claude Code は内部的に次のような処理をしてくれます（参考）。

```bash
gh issue create --title "WordPress 管理環境の構築" --body-file plan.md
```

## ステップ 2: Issue が作られたか確認

ブラウザで開いて確認します。

```bash
gh issue list
```

または Claude Code に「作った Issue を開いてください」と頼むと、ブラウザで開いてくれます。

## ステップ 3: 必要なら Issue を編集

`plan.md` の内容に追記したい項目が出てきたら、GitHub の Issue ページで右上の `...` → `Edit` から直接編集できます。

または Claude Code に頼むこともできます。

> Issue #1 の本文に「対象ページは `/about/` と `/contact/` の 2 ページ」を追記してください。

## Issue とローカルの plan.md の使い分け

| | plan.md（ローカル） | Issue（GitHub） |
|---|------|--------|
| **役割** | 設計書の原本 | 作業依頼の窓口 |
| **更新タイミング** | 大きな方針が変わったとき | 個別の指示・確認 |
| **Claude Code との対話** | しない | **コメントで行う** |

つまり、`plan.md` は「建物の設計図」、Issue は「現場での工事指示書」のような関係です。

## 確認

- [ ] GitHub に Issue が登録された
- [ ] Issue の本文に `plan.md` の内容が反映されている

確認できたら、次の [5. Issue で対話する](05-issue-dialogue.md) に進みます。
