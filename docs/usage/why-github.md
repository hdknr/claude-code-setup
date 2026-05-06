# なぜ GitHub を使うのか

Claude Code には、提案書・ポートフォリオ・コード・WordPress サイトなど、**自分にとって大事なファイル** を編集してもらう場面が出てきます。これらを GitHub に保存しながら作業すると、Claude Code をぐっと安心して使えるようになります。このページではその **要点だけ** を紹介します。

!!! info "もっと詳しく知りたい方へ"
    用語の図解、PR ワークフローの考え方、料金やデータ所在の詳細などは [GitHub をやさしく理解する](../tools/github/index.md) にまとめています。

## ひとことで言うと

GitHub は、**ファイルの変更履歴を自動で記録してくれるオンライン保管庫** です。

Google ドライブが「**今のファイルを置いておく場所**」だとすれば、GitHub は「**過去から現在までのすべての変化を記録する場所**」です。「いつ・誰が・どこを変えたか」がすべて残り、いつでも過去の状態に戻せます。

## Claude Code と組み合わせる主なメリット

- **Claude が間違えても安心して戻せる** — 数秒前の状態にワンコマンドで戻せる
- **PC が壊れてもファイルが消えない** — 別の PC から作業を再開できる
- **スマホや別の PC からも確認できる** — ブラウザでいつでも見られる
- **ポートフォリオやサイトとして公開できる**（GitHub Pages）
- **AI が「過去の経緯」を読んで賢く動ける** — 履歴と PR が判断材料になる

→ 詳しい説明は [GitHub をやさしく理解する / Claude Code と組み合わせる 5 つのメリット](../tools/github/index.md#claude-code-5)

## 最低限知っておきたい 3 つの言葉

| 用語 | 普段の言葉に置き換えると |
|---|---|
| **リポジトリ** | プロジェクト用のフォルダ |
| **コミット** | 「ここまで OK」のしおりを挟む |
| **プッシュ** | GitHub にアップロード |

打ち込む必要はなく、Claude Code に「ここまでの変更をコミットして、GitHub にも上げておいて」と日本語で頼むだけで動きます。

→ 図解と「PR とは何か / なぜ作るのか」は [GitHub をやさしく理解する](../tools/github/index.md#3) で解説しています。

## Private で作るのが基本

Claude Code の作業用リポジトリは **必ず Private（非公開）** で作成してください。Public（公開）にすると、世界中の誰からも見られる状態になります。

| 用途 | おすすめ |
|---|---|
| 提案書・履歴書・WordPress 一式・下書き全般 | **Private** |
| 自己紹介サイト・公開済みブログ・OSS | Public |

迷ったら Private に。

→ 公開可否の判断基準やデータ所在の詳細は [GitHub をやさしく理解する / Public と Private の使い分け](../tools/github/index.md#public-private) を参照してください。

## 次のステップ

- **これから準備する方**: [macOS Part 1](../macos/part1-preparation.md) / [Windows Part 1](../windows/part1-preparation.md) で GitHub CLI のインストールとログインを行います
- **インストール済みの方**: [macOS Part 3](../macos/part3-post-setup.md) / [Windows Part 3](../windows/part3-post-setup.md) でリポジトリを作成し、Claude Code から使える状態にします
- **GitHub の概念をもっと理解したい方**: [GitHub をやさしく理解する](../tools/github/index.md)
