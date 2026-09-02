# Part 2: Claude Code インストール（WSL2 / Ubuntu）

WSL2 (Ubuntu) 上に Claude Code をインストールしてサインインするまでの手順です。

!!! info "ネイティブ Windows をご利用の方"
    PowerShell でインストールする手順は [Windows / Part 2](part2-installation.md) を参照してください。

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

公式の**ネイティブインストーラー**を使います。Node.js などの追加準備は不要で、自動でアップデートされます。

Ubuntu ターミナルで以下を実行してください:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

インストールが完了すると、`claude` コマンドが `~/.local/bin/claude` に配置されます。インストーラーがシェル設定（`~/.bashrc`）にパスを自動追加します。

!!! note "インストール後はターミナルを開き直してください"
    パス設定を反映するため、Ubuntu のターミナルを一度閉じて開き直してください。
    すぐに反映したい場合は次を実行します:
    ```bash
    source ~/.bashrc
    ```

正しくインストールされたか確認しましょう:

```bash
claude --version
```

バージョン番号が表示されれば成功です。

!!! tip "`claude` コマンドが見つからない場合"
    ターミナルを開き直しても `claude: command not found` と表示される場合は、フルパスで起動を確認:
    ```bash
    ~/.local/bin/claude --version
    ```
    動く場合は、`~/.bashrc` の末尾に次の行を追加して再読み込みしてください:
    ```bash
    export PATH="$HOME/.local/bin:$PATH"
    ```

!!! info "アップデートについて"
    ネイティブインストーラーで入れた Claude Code は**バックグラウンドで自動アップデート**されます。手動で最新化したい場合は `claude update` を実行します。

## 2.3 Claude Code の起動とサインイン

Ubuntu ターミナルで以下を実行:

```bash
claude
```

初回起動時にサインインが求められます:

1. Windows 側のブラウザが自動的に開きます
2. **2.1 で作成した Claude アカウント**でログインしてください
3. 「Authorize」をクリックして認証を許可
4. ブラウザに「Login successful」と表示されたらターミナルに戻ります

!!! note "ブラウザが自動で開かない場合"
    WSL2 では Windows 側のブラウザを呼び出す仕組みが標準で有効ですが、環境によっては自動で開かないことがあります。その場合はターミナルに表示された URL を手動で Windows のブラウザに貼り付けてください。

    ブラウザのコールバックが届かない場合はログインコードが表示されるので、ターミナルの `Paste code here if prompted` にコードを貼り付けます。

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

Claude Code のインストールが完了しました。[Part 3: インストール後の環境準備](../part3-post-setup.md) に進んでください。
