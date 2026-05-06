# Part 2: Claude Code インストール（Windows）

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

PowerShell で以下のコマンドを実行してください:

```powershell
irm https://claude.ai/install.ps1 | iex
```

インストールが完了すると、`claude.exe` が `%USERPROFILE%\.local\bin\` に配置されます。インストーラーがユーザー環境変数 `PATH` に自動的に追加します。

!!! warning "PowerShell ではなく CMD を使っている場合"
    `'irm' is not recognized as an internal or external command` のように表示されたら、CMD（コマンドプロンプト）で実行してしまっています。プロンプトが `PS C:\...` で始まっていれば PowerShell、`C:\...` で始まっていれば CMD です。

    CMD でインストールする場合のコマンド:
    ```batch
    curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
    ```

!!! note "インストール後はターミナルを開き直してください"
    `PATH` の更新を反映するため、PowerShell を**一度閉じて開き直してください**。

正しくインストールされたか確認しましょう:

```powershell
claude --version
```

バージョン番号が表示されれば成功です。

!!! tip "`claude` コマンドが見つからない場合"
    PowerShell を開き直しても `'claude' is not recognized...` と表示される場合は、次を試してください:

    1. PowerShell を完全に閉じてから、もう一度新しい PowerShell を起動する
    2. それでも解決しない場合は、フルパスで起動を確認:
       ```powershell
       & "$env:USERPROFILE\.local\bin\claude.exe" --version
       ```
    3. 上で動くのに `claude` で動かない場合は、ユーザー環境変数 `PATH` に `%USERPROFILE%\.local\bin` を手動で追加してください。

!!! info "アップデートについて"
    ネイティブインストーラーで入れた Claude Code は**バックグラウンドで自動アップデート**されます。手動で最新化したい場合は `claude update` を実行します。

## 2.3 Claude Code の起動とサインイン

PowerShell で以下のコマンドを実行して Claude Code を起動します:

```powershell
claude
```

初回起動時にサインインが求められます:

1. ブラウザが自動的に開きます
2. **2.1 で作成した Claude アカウント**でログインしてください
3. 「Authorize」をクリックして認証を許可
4. ブラウザに「Login successful」と表示されたら PowerShell に戻ります

!!! note "ブラウザが自動で開かない場合"
    PowerShell に表示された URL を手動でブラウザに貼り付けてください。
    ブラウザのコールバックが届かない環境ではログインコードが表示されるので、ターミナルの `Paste code here if prompted` にコードを貼り付けます。

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
