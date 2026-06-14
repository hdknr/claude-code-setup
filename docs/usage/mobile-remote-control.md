# モバイルからのリモートコントロール

「外出先のスマホから、自宅 PC で動いている Claude Code に続きを指示したい」——
そんなときに使うのが **リモートコントロール（Remote Control）** です。

PC で始めた作業を、ソファに座ったままスマホから、あるいは別のパソコンのブラウザから
**そのまま操作し続けられる** 公式機能です。

!!! info "この機能でできること"
    - PC で `claude` を起動したまま、外出先のスマホアプリから指示を送る
    - 会話は全デバイスでリアルタイム同期（PC・スマホ・ブラウザを行き来できる）
    - **作業は常に自分の PC 上で動く** ——ファイル・MCP サーバー・設定はそのまま使える
    - 長い処理が終わったらスマホに**プッシュ通知**が届く

## 仕組み

クラウドにファイルがアップロードされるわけではありません。Claude Code は**ずっと自分の PC 上で動き続け**、スマホやブラウザは「その画面をのぞく窓」になるイメージです。

```
[自分の PC]                    [Anthropic API]              [スマホ / ブラウザ]
 claude 起動中  ──HTTPS(外向き)──→  中継サーバー  ←──────────  Claude アプリ
 （ファイル・                                                   claude.ai/code
  MCP・ツール）  ←─────────────  指示を中継  ←─────────────  で指示を入力
```

!!! note "Claude Code on the Web との違い"
    似た機能に [Claude Code on the Web](https://code.claude.com/docs/en/claude-code-on-the-web) がありますが、あちらは **Anthropic のクラウド VM 上**で動きます。手元のファイルにはアクセスできません。

    一方リモートコントロールは **自分の PC 上**で動くので、ローカルのファイルや設定をそのまま使えます。「いま手元でやっている作業を別端末から続けたい」ときはこちらです。

## 前提条件

| 項目 | 内容 |
|------|------|
| **プラン** | Pro / Max / Team / Enterprise（**API キー認証は不可**） |
| **バージョン** | Claude Code v2.1.51 以降（`claude --version` で確認） |
| **ログイン** | `claude` 起動後 `/login` で claude.ai アカウントにサインイン |
| **ワークスペース信頼** | プロジェクトのフォルダで一度 `claude` を起動し、信頼ダイアログを承認しておく |
| **スマホアプリ** | [iOS](https://apps.apple.com/us/app/claude-by-anthropic/id6473753684) / [Android](https://play.google.com/store/apps/details?id=com.anthropic.claude) の Claude アプリ |

!!! warning "Team / Enterprise の場合"
    Team / Enterprise プランでは初期状態で無効になっています。管理者が [Claude Code 管理設定](https://claude.ai/admin-settings/claude-code) で **Remote Control** トグルを有効化する必要があります。

    また、この機能は現在 **リサーチプレビュー** として提供されています。

## セットアップ

### 1. ログインを確認する

API キーではなく **claude.ai アカウント**でログインしている必要があります。

```bash
claude
```

起動後、ログインしていなければ次を実行します。

```
/login
```

!!! tip "API キーを使っている場合"
    環境変数に `ANTHROPIC_API_KEY` が設定されているとリモートコントロールは使えません。一度 unset してから `/login` でやり直してください。

### 2. スマホに Claude アプリを入れる

まだアプリを入れていなければ、Claude Code 内で次のコマンドを実行すると、ダウンロード用の QR コードが表示されます。

```
/mobile
```

## リモートコントロールを開始する

起動方法は 3 通りあります。用途に合わせて選んでください。

=== "既存セッションから（おすすめ）"

    すでに Claude Code で作業中なら、その会話をそのまま引き継いで外でも続けられます。

    ```
    /remote-control
    ```

    名前を付けたいときは引数で指定できます（セッション一覧で見分けやすくなります）。

    ```
    /remote-control 経理アプリの修正
    ```

    実行すると入力欄の下にリモートコントロール中を示すインジケーターが表示されます。これを選んで Enter を押すと、接続用の **URL と QR コード**が出てきます。

=== "通常セッション + リモート対応"

    最初からリモート対応で起動したいときは `--remote-control`（短縮形 `--rc`）を付けます。PC でローカル入力しながら、同時に外からも操作できます。

    ```bash
    claude --remote-control
    ```

    名前も付けられます。

    ```bash
    claude --remote-control "経理アプリの修正"
    ```

=== "サーバーモード"

    PC を「リモート接続待ち受け専用」にするモードです。ターミナルには接続用 URL が表示され、**スペースキー**を押すと QR コードが出ます。

    ```bash
    claude remote-control
    ```

    複数セッションを同時に動かせるなど高度な使い方向けです。

    | よく使うフラグ | 説明 |
    |------|------|
    | `--name "経理アプリ"` | セッションに名前を付ける |
    | `--spawn worktree` | 接続ごとに [git worktree](https://code.claude.com/docs/en/worktrees) を分ける（同じファイルの競合を防ぐ） |
    | `--sandbox` | ファイル・ネットワークを隔離する [サンドボックス](https://code.claude.com/docs/en/sandboxing) を有効化 |

!!! tip "毎回自動でリモート対応にする"
    `/config` を開き、**Enable Remote Control for all sessions** を `true` にすると、すべてのインタラクティブセッションで自動的にリモートコントロールが有効になります。

## スマホ・ブラウザから接続する

リモートコントロールを開始すると、次のいずれかの方法で接続できます。

1. **QR コードをスキャンする** ——ターミナルに表示された QR コードをスマホのカメラで読み取ると、Claude アプリでそのセッションが直接開きます。
2. **セッション URL を開く** ——表示された URL を任意のブラウザで開くと、[claude.ai/code](https://claude.ai/code) 上でそのセッションにつながります。
3. **アプリ／Web のセッション一覧から探す** ——Claude モバイルアプリ下部の **Code** タブ、または [claude.ai/code](https://claude.ai/code) を開き、名前でセッションを探します。オンラインのセッションは **PC アイコンに緑のドット** が付いています。

接続できたら、スマホの入力欄に日本語で指示を打つだけです。PC のターミナルにも同じ会話が流れていきます。

## モバイル通知を設定する

リモートコントロール中、Claude は**長い処理が終わったとき**や**あなたの判断が必要になったとき**に、スマホへプッシュ通知を送れます。プロンプトに「テストが終わったら通知して」と書いて明示的に依頼することもできます。

!!! note "必要バージョン"
    モバイルプッシュ通知には Claude Code v2.1.110 以降が必要です。

設定手順:

1. スマホに [iOS](https://apps.apple.com/us/app/claude-by-anthropic/id6473753684) / [Android](https://play.google.com/store/apps/details?id=com.anthropic.claude) の Claude アプリをインストール
2. **PC と同じアカウント・組織**でサインイン
3. OS の通知許可ダイアログを「許可」する
4. PC のターミナルで `/config` を開き、**Push when Claude decides** を有効化

!!! tip "通知が届かないとき"
    - `/config` に **No mobile registered** と出る場合は、スマホで一度 Claude アプリを開くと通知トークンが更新されます。
    - iOS は「集中モード」や通知要約で遅延することがあります（設定 → 通知 → Claude）。
    - Android はバッテリー最適化の対象から Claude アプリを外してください。

## 制限事項

| 制限 | 内容 |
|------|------|
| **PC を起動し続ける必要がある** | ターミナルを閉じたり `claude` を終了するとセッションも終わります |
| **ネット切断は約 10 分まで** | PC がネットに約 10 分以上つながらないとセッションがタイムアウトします（再度起動すれば復帰） |
| **一部コマンドは PC 専用** | `/plugin` や `/resume` などターミナルで選択画面を開くコマンドはスマホからは使えません。`/compact` `/clear` `/context` などテキスト出力のコマンドはスマホ・Web でも使えます |
| **1 プロセス 1 セッション** | サーバーモード以外では、1 つの `claude` につきリモートセッションは 1 つです |

## 他の「離れた場所から使う」方法との比較

リモートコントロール以外にも、PC の前にいないときに Claude Code を動かす方法があります。目的に合わせて選びましょう。

| 方法 | きっかけ | Claude が動く場所 | 向いている用途 |
|------|---------|-----------------|--------------|
| **リモートコントロール** | claude.ai/code やスマホアプリから操作 | **自分の PC** | 進行中の作業を別端末から続ける |
| [Dispatch](https://code.claude.com/docs/en/desktop#sessions-from-dispatch) | スマホアプリからタスクを送信 | 自分の PC（Desktop アプリ） | 外出中に作業を丸ごと任せる |
| [GitHub Actions](https://code.claude.com/docs/en/github-actions) | Issue / PR で `@claude` とメンション | GitHub のクラウド | スマホの GitHub アプリから修正を依頼 |
| [Channels](https://code.claude.com/docs/en/channels) | Telegram / Discord などからメッセージ | 自分の PC | チャットアプリ経由で指示・CI 失敗に反応 |

!!! tip "GitHub 連携を使えばアプリ不要"
    このプロジェクトのように GitHub で作業している場合、スマホの **GitHub アプリ**で Issue や PR に `@claude これを直して` とコメントするだけで、[GitHub Actions](https://code.claude.com/docs/en/github-actions) 経由で Claude に作業を任せられます（事前のワークフロー設定が必要）。

## トラブルシューティング

| エラー / 症状 | 対処 |
|------|------|
| `Remote Control requires a claude.ai subscription` | API キーでログインしています。`ANTHROPIC_API_KEY` を unset し、`claude auth login` で claude.ai を選択 |
| `Remote Control requires a full-scope login token` | `setup-token` 等の長期トークンは不可。`claude auth login` でフルスコープのログインをやり直す |
| `Remote Control is not yet enabled for your account` | `CLAUDE_CODE_USE_BEDROCK` / `_VERTEX` など第三者プロバイダー設定があると使えません。unset して再試行 |
| `Remote Control is disabled by your organization's policy` | Team/Enterprise の管理者が未有効化、または API キー認証。`/status` で状態を確認 |
| セッションが見つからない | PC 側で `claude` が動き続けているか、同じアカウントでログインしているかを確認 |

## 関連リンク

- [リモートコントロール公式ドキュメント](https://code.claude.com/docs/en/remote-control)
- [Claude Code on the Web](https://code.claude.com/docs/en/claude-code-on-the-web)
- [GitHub Actions 連携](https://code.claude.com/docs/en/github-actions)
- [なぜ GitHub を使うのか](why-github.md)
