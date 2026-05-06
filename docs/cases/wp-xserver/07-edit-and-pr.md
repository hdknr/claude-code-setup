# 7. 修正と PR

このページを読むと、**stage 環境で修正内容を確認し、GitHub に PR（プルリクエスト）として登録できる** ようになります。

## やること

1. Issue で確定した修正内容を Claude Code に作業させる
2. ローカル stage で動作確認する
3. GitHub に PR として登録する
4. PR レビュー → マージ

## ステップ 1: 作業ブランチを切る

修正は **main ブランチではなく専用のブランチ** で行います。これにより、修正中の状態と本番反映済みの状態を分けて管理できます。

Claude Code に頼みます。

> Issue #1 の修正に取り掛かります。`issue/1-update-catchphrase` というブランチを切ってください。

## ステップ 2: 修正を実行

Issue の内容にもとづいて Claude Code に修正を依頼します。

> Issue #1 のコメントで確定した内容（キャッチコピーの変更）を、`wp-content/themes/...` 配下のテーマファイルに反映してください。

Claude Code がファイルを編集します。どのファイルをどう変えたかは、Claude Code が報告してくれます。

!!! tip "修正対象がどのファイルか分からないとき"
    Claude Code に「キャッチコピー `未来を拓く、確かな技術` がどのファイルにあるか探してください」と頼めば、`grep` で探してくれます。

## ステップ 3: stage で確認

ブラウザで `http://localhost:8080` を開きます。

- 修正が反映されているか
- 他のページが壊れていないか
- レイアウトが崩れていないか

を確認します。

!!! warning "キャッシュが残っているように見えたら"
    ブラウザに古い表示が残ることがあります。Mac は `Cmd + Shift + R`、Windows は `Ctrl + F5` でハードリロードしてください。

## ステップ 4: コミット

修正内容を git に記録します。Claude Code に頼みます。

> 変更を `Update homepage catchphrase` というメッセージでコミットしてください。Issue #1 への参照も含めてください。

Claude Code が次のような処理をしてくれます。

```bash
git add wp-content/themes/...
git commit -m "Update homepage catchphrase

Refs #1"
```

## ステップ 5: ブランチを GitHub にプッシュ

> このブランチを GitHub にプッシュしてください。

```bash
git push -u origin issue/1-update-catchphrase
```

## ステップ 6: PR を作る

Claude Code に頼みます。

> Issue #1 を解決する PR を作ってください。タイトルは `Update homepage catchphrase`、本文には Issue へのリンクと、変更点の概要を入れてください。マージ時に Issue が自動で閉じるよう `Fixes #1` を含めてください。

Claude Code が `gh pr create` で PR を作ります。

```bash
gh pr create --title "Update homepage catchphrase" --body "$(cat <<'EOF'
## 概要

トップページのキャッチコピーを更新。

## 変更内容

- `wp-content/themes/.../header.php` の `<h1>` を変更

Fixes #1
EOF
)"
```

## ステップ 7: PR をレビュー

GitHub の PR ページで、変更内容（diff）を確認します。

- 想定外のファイルが変わっていないか
- 修正内容が指示通りか

問題なければ、PR の **Files changed** タブで確認 → **Review changes** → **Approve** → **Merge pull request**。

!!! info "Approve は自分でも押せます"
    自分一人で進めるプロジェクトでも、いったん PR を作ってマージする流れにしておくと、変更履歴が綺麗に残ります。

## ステップ 8: マージ後のクリーンアップ

マージしたら Claude Code に頼みます。

> ブランチを main に戻して、最新を pull してください。作業ブランチはローカルから削除してください。

```bash
git checkout main
git pull
git branch -d issue/1-update-catchphrase
```

## 確認

- [ ] stage 環境で修正内容が確認できた
- [ ] PR が GitHub に登録された
- [ ] PR がマージされた

確認できたら、次の [8. xserver にデプロイ](08-deploy-xserver.md) に進みます。
