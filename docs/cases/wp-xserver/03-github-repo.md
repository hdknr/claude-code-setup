# 3. GitHub リポジトリの用意

このページを読むと、**Claude Code に頼んで GitHub の private リポジトリを作り、`plan.md` を登録するところまで一気に終わらせる** ことができます。

## やること

1. **Claude Code に依頼して、リポジトリ作成から `plan.md` の登録、接続確認まで一気にやってもらう**

リポジトリ作成 (`gh repo create`)、`git init`、最初のコミット、push、リモート設定、private になっているかの確認 — これらを **すべて Claude Code に任せます**。手作業より速く、コマンドのスペルミスや「private にし忘れ」のような事故も防げます。

## 前提

- GitHub CLI（`gh`）がインストールされ、`gh auth login` でログイン済み

ログイン状態が分からない場合は、Claude Code に「`gh` の認証状態を確認してください」と頼めば教えてくれます。未ログインなら `gh auth login` を案内してくれます。インストールから済ませたい場合は [Part 1 - 事前準備](../../macos/part1-preparation.md) を参照してください。

## ステップ 1: 配置から接続確認まで Claude Code にまとめて依頼

ステップ 2 で作った `wp-mysite` フォルダで Claude Code を起動した状態（`/init` などの後）から、次のように頼みます。

### 依頼文（コピペで OK）

> このフォルダ（`wp-mysite`）を GitHub の **private リポジトリ** として用意してください。次のことを順番にやって、最後に結果を報告してください。
>
> 1. `gh` の認証状態を確認（未ログインなら案内して中断）
> 2. リポジトリを `git init` で初期化
> 3. `plan.md` をコミット
> 4. GitHub に **private** で同名リポジトリを作成
> 5. main ブランチを push
> 6. リモート（origin）が正しく繋がっているか、リポジトリが private になっているかを確認
> 7. 上記の各ステップが成功したかと、ブラウザで開ける URL を箇条書きで報告

### 報告で確認すべきこと

Claude Code から返ってくる報告で、次の 3 点だけ自分の目で確認します。

- **リポジトリ URL**（`https://github.com/<あなた>/wp-mysite`）が表示されている
- **private** になっている、と書かれている
- `plan.md` が登録されている、と書かれている

「`plan.md` のリンクを開きたい」と Claude Code に頼めば、ブラウザで該当ページを開いてくれます（`gh repo view --web` を実行）。

!!! warning "万一 public で作られていたら"
    まれに設定の取り違えで public になることがあります。報告に「private」が書かれていなければ、すぐ Claude Code に「private に変更してください」と依頼してください。

### うまくいかなかったとき

エラーが出たら、メッセージを **そのままコピーして** Claude Code に貼り付ければ、原因と対処を教えてくれます。

> GitHub リポジトリの作成でこういうエラーが出ました。原因と直し方を教えてください。
>
> ```
> （ここにエラー全文を貼る）
> ```

## 確認

- [ ] Claude Code から「リポジトリを private で作成し、`plan.md` を push しました」と報告があった
- [ ] 報告に含まれる URL をブラウザで開いて、`plan.md` と「Private」の表示を見た

確認できたら、次の [4. plan.md から Issue を作る](04-issue-creation.md) に進みます。

---

## リファレンス：自分で確認するには？

「Claude Code が裏で何をやっているのか知りたい」「結果を自分の目で確かめたい」人向けです。**読まなくても作業は完了します**。

### `gh` の認証状態を自分で確認する

ターミナルで:

```bash
gh auth status
```

`Logged in to github.com as ...` と表示されれば OK。

### ブラウザでリポジトリを自分で開く

```bash
gh repo view --web
```

ブラウザが開き、作成されたリポジトリのページが表示されます。GitHub のページで次を確認できます。

- リポジトリ名（例: `your-username/wp-mysite`）
- `plan.md` ファイル
- リポジトリ名の右に **「Private」** の表示
- 鍵マーク（private の証）

### ローカルとリモートが繋がっているかを自分で確認する

```bash
git remote -v
```

次のような表示が出れば、ローカルと GitHub が繋がっています。

```
origin  https://github.com/your-username/wp-mysite.git (fetch)
origin  https://github.com/your-username/wp-mysite.git (push)
```

### Claude Code が裏で実行しているコマンド

参考までに、実際に実行されているコマンドの中身です。

```bash
git init
git add plan.md
git commit -m "Add plan.md"
gh repo create wp-mysite --private --source=. --push
```

!!! info "private リポジトリとは"
    GitHub のリポジトリには **public（誰でも見られる）** と **private（自分と招待した人だけ）** があります。WordPress のサイト情報や認証情報を含む可能性があるため、**必ず private** にします。`gh repo create --private` のオプションがそれを保証しています。

### 詰まりやすいエラーと対応

| エラー | 主な原因 | 対応 |
|---|---|---|
| `gh: command not found` | GitHub CLI 未インストール | [Part 1 - 事前準備](../../macos/part1-preparation.md) でインストール |
| `not logged in to github.com` | `gh auth login` が未実行 | `gh auth login` を実行（または Claude Code に依頼） |
| `Repository ... already exists` | 同名リポジトリが既にある | 別名で作るか、既存のものを削除（GitHub 上で慎重に） |
| `failed to push some refs` | リモートに別の履歴がある | Claude Code に「force push せず、ローカルとリモートの履歴を整理して push してください」と依頼 |
