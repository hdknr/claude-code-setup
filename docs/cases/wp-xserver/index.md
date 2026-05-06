# WordPress (xserver) を Claude Code で管理

xserver（[https://www.xserver.ne.jp/](https://www.xserver.ne.jp/)）でホスティングしている WordPress サイトを、**GitHub と Claude Code で管理・更新する** ためのフローを作っていく事例です。

## このページを読むと何ができるようになるか

- WordPress の修正指示を **GitHub Issue** で管理できるようになります
- 修正は **ローカル PC の stage 環境（Docker）** で確認してから、xserver に反映できるようになります
- すべての変更履歴が GitHub に残り、いつでも前の状態に戻せるようになります

## 想定する読者

- xserver の WordPress サイトを **編集・運用している方**（コンテンツマネージャ）
- SSH や Docker は使ったことがないが、Claude Code に頼めば動かせるレベルになりたい方
- Part 1〜3 のセットアップが完了している方

!!! info "Claude Code の基本操作はこちら"
    まだ Claude Code をインストールしていない方は、先に [macOS 手順](../../macos/part1-preparation.md) または [Windows 手順](../../windows/part1-preparation.md) を完了してください。

## 全体像

おおまかに、次の 4 つの段階で進めます。

1. **準備**: 作業フォルダと GitHub のリポジトリを用意する
2. **指示出し**: やりたいことを `plan.md` に書き、Claude Code に Issue を作らせる
3. **対話**: Issue のコメントで Claude Code と相談しながら修正内容を固める
4. **反映**: ローカルの stage で確認 → PR → xserver にデプロイ

詳しくは [全体フロー](01-overview.md) のページで図解します。

## 章構成

| # | 内容 | 何ができるようになるか |
|---|------|----------------------|
| [1](01-overview.md) | ゴールと全体フロー | この事例で目指すゴールと、各章の位置付けが分かる |
| [2](02-prepare-folder.md) | フォルダ作成と plan.md | 作業フォルダを作り、やりたいことを文章化できる |
| [3](03-github-repo.md) | GitHub リポジトリの用意 | Claude Code に依頼して private リポジトリを作れる |
| [4](04-issue-creation.md) | plan.md から Issue を作る | plan.md の内容を Claude Code が GitHub Issue に変換できる |
| [5](05-issue-dialogue.md) | Issue で対話する | コメントで指示を追加・確認できる |
| [6](06-stage-docker.md) | Docker で stage 環境 | ローカル PC に WordPress の動作確認用環境を作れる |
| [7](07-edit-and-pr.md) | 修正と PR | stage で確認 → GitHub に PR を出せる |
| [8](08-deploy-xserver.md) | xserver にデプロイ | SSH または WP REST API で本番に反映できる |
| [9](09-troubleshooting.md) | トラブルシュート | よく詰まる箇所と回避法が分かる |

!!! warning "本番環境を直接いじらないでください"
    xserver の WordPress 本番環境に直接修正を加えると、サイトが表示されなくなるリスクがあります。**必ず stage で確認してから** 本番に反映する流れを守ってください。
