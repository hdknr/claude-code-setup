# 3. GitHub リポジトリの用意

このページを読むと、**Claude Code に依頼して GitHub の private リポジトリを作り、`plan.md` を登録できる** ようになります。

## やること

1. Claude Code に頼んで GitHub に private リポジトリを作る
2. ローカルの `plan.md` を main ブランチに登録（コミット・プッシュ）する

## 前提

- GitHub CLI（`gh`）がインストールされ、`gh auth login` でログイン済み

確認したい場合は、ターミナルで以下を実行します。

```bash
gh auth status
```

`Logged in to github.com as ...` と表示されれば OK です。表示されない場合は [Part 1 - 事前準備](../../macos/part1-preparation.md) を参照してください。

## ステップ 1: private リポジトリを作る

Claude Code に次のように伝えます。

> このフォルダ（`wp-mysite`）の内容を GitHub の **private リポジトリ** にしてください。リポジトリ名はフォルダ名と同じで、main ブランチを作って `plan.md` を登録してください。

Claude Code は内部的に次のような処理をしてくれます（参考までに）。

```bash
git init
git add plan.md
git commit -m "Add plan.md"
gh repo create wp-mysite --private --source=. --push
```

!!! info "private リポジトリとは"
    GitHub のリポジトリには **public（誰でも見られる）** と **private（自分と招待した人だけ）** があります。WordPress のサイト情報や認証情報を含む可能性があるため、**必ず private** にします。

## ステップ 2: リポジトリができたか確認する

GitHub のサイトで作成されたか確認します。

```bash
gh repo view --web
```

ブラウザが開いて、作ったリポジトリのページが表示されます。`plan.md` がリポジトリに登録されていれば成功です。

## ステップ 3: GitHub 上の表示を確認する

GitHub のページで、以下が確認できます。

- リポジトリ名（例: `your-username/wp-mysite`）
- `plan.md` ファイル
- 鍵マーク（private の証）

!!! warning "Public になっていないか必ず確認"
    リポジトリ名の右に「Private」と表示されていることを確認してください。「Public」になっていたら、Claude Code に「private に変更してください」と頼んで切り替えます。

## ステップ 4: ローカルとリモートが繋がっているか確認

ターミナルで以下を実行します。

```bash
git remote -v
```

次のような表示が出れば、ローカルと GitHub が繋がっています。

```
origin  https://github.com/your-username/wp-mysite.git (fetch)
origin  https://github.com/your-username/wp-mysite.git (push)
```

## 確認

- [ ] GitHub に `wp-mysite` リポジトリが作られている
- [ ] private になっている
- [ ] `plan.md` が main ブランチに登録されている
- [ ] `git remote -v` で origin が表示される

確認できたら、次の [4. plan.md から Issue を作る](04-issue-creation.md) に進みます。
