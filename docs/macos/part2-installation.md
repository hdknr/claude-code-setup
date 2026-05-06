# Part 2: Claude Code インストール

Claude アカウントの準備から Claude Code のインストール、サインインまでの手順です。

## 2.1 Claude アカウントの準備

Claude Code を使うには **Claude アカウント**が必要です。Claude.ai のアカウントをそのまま使えます。

### まだアカウントがない場合

1. [claude.com](https://claude.com/) にアクセス
2. 「Sign Up」からアカウントを作成
3. メールアドレスの確認を完了

### プランの選択

Claude Code を使うには、以下のいずれかが必要です（**無料の Claude.ai プランでは Claude Code は利用できません**）。

- **Claude Pro プラン**（$20/月）- 個人利用向け。Claude Web 版と使用量を共有
- **Claude Max プラン**（$100/月 または $200/月）- 大量に使う方におすすめ
- **Claude for Teams / Enterprise** - チーム・組織での利用向け
- **API クレジット**（従量課金）- [console.anthropic.com](https://console.anthropic.com/) で発行

詳しくは [claude.com/pricing](https://claude.com/pricing) を確認してください。

!!! tip "どれを選べばよい？"
    個人で日常的に使うなら **Pro プラン**で始めるのが分かりやすいです。Claude Web 版（チャット）と Claude Code が同じアカウント・同じ使用量枠で利用できます。

## 2.2 Claude Code のインストール

公式の**ネイティブインストーラー**を使ってインストールします。Node.js などの追加準備は不要で、自動でアップデートされます。

ターミナルで以下のコマンドを実行してください:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

インストールが完了すると、`claude` コマンドが `~/.local/bin/claude` に配置されます。インストーラーがシェル設定（`~/.zprofile` など）にパスを自動追加します。

!!! note "インストール後はターミナルを開き直してください"
    パス設定を反映するため、ターミナルを一度閉じて開き直してください。
    すぐに反映したい場合は次を実行します:
    ```bash
    source ~/.zprofile
    ```

正しくインストールされたか確認しましょう:

```bash
claude --version
```

バージョン番号が表示されれば成功です。

!!! info "アップデートについて"
    ネイティブインストーラーで入れた Claude Code は**バックグラウンドで自動アップデート**されます。手動で最新化したい場合は `claude update` を実行します。

## 2.3 Claude Code の起動とサインイン

ターミナルで以下のコマンドを実行して Claude Code を起動します:

```bash
claude
```

初回起動時にサインインが求められます:

1. ブラウザが自動的に開きます
2. **2.1 で作成した Claude アカウント**でログインしてください
3. 「Authorize」をクリックして認証を許可
4. ブラウザに「Login successful」と表示されたらターミナルに戻ります

!!! note "ブラウザが自動で開かない場合"
    ターミナルに表示された URL を手動でブラウザに貼り付けてください。
    SSH 経由など、ブラウザのコールバックが届かない環境ではログインコードが表示されるので、ターミナルの `Paste code here if prompted` にコードを貼り付けます。

!!! tip "ログインのやり直し"
    別のアカウントでログインし直したいときは、Claude Code 内で `/logout` を実行してから再度 `claude` を起動します。

## 2.4 動作確認

Claude Code が起動したら、簡単な質問をして動作を確認しましょう:

```
こんにちは。今日の日付を教えてください。
```

応答が返ってくれば、インストール成功です。

`/exit` と入力して一旦終了しましょう:

```
/exit
```

## 次のステップ

Claude Code のインストールが完了しました。[Part 3: インストール後の環境準備](part3-post-setup.md) に進んでください。
