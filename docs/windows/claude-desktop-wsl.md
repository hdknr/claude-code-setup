# 補足: Claude Desktop から WSL の Linux ツールを使う（Windows）

Windows で開発していると、**リポジトリや実行環境が WSL（Linux）側にある**ことがよくあります。

- `bash` スクリプト、`Makefile`、`docker compose` などが Linux 前提で書かれている
- Python / Node.js を WSL 側の Ubuntu に入れている
- リポジトリを `\\wsl.localhost\Ubuntu\home\you\...` ではなく `/home/you/...` として扱いたい

このページでは、**Claude Desktop（Windows 版）から WSL の中のツールを動かす方法**を、推奨順に 3 つ整理します。

!!! info "先に結論"
    普段の開発なら **方法 A（Code タブの WSL セッション）** を選んでください。公式にサポートされた方法で、設定ファイルを書く必要がありません。
    `claude_desktop_config.json` に `wsl.exe` を書く方法（方法 C）は、**Chat タブから WSL のコマンドを呼びたい**という特殊なケース用です。

## 3 つの方法の比較

| | 方法 A: Code タブの WSL セッション | 方法 B: WSL ターミナルで `claude` | 方法 C: MCP 経由（`wsl.exe`） |
|---|---|---|---|
| **どこで動く** | Claude Desktop の Code タブ | WSL のターミナル（CLI） | Claude Desktop の Chat タブ |
| **設定ファイル** | 不要（GUI で選ぶだけ） | 不要 | `claude_desktop_config.json` を手書き |
| **Linux ツールを使える** | ✅ そのまま | ✅ そのまま | △ MCP サーバーが公開したものだけ |
| **GUI（差分レビュー等）** | ✅ | ❌ | △ Chat の範囲 |
| **難易度** | 低 | 低 | 高（ハマりどころが多い） |
| **向いている人** | ほとんどの人 | ターミナル派 | Chat から特定のコマンドだけ叩きたい人 |

!!! tip "方法 A と方法 B は併用できます"
    どちらも同じ WSL の中でファイルを触るので、片方で作業して片方で確認する、という使い方もできます。

## 事前準備: WSL 2 の確認

どの方法でも **WSL 2** が必要です（WSL 1 はサポート対象外）。

PowerShell で確認します:

```powershell
wsl --status
wsl --list --verbose
```

`VERSION` 列が `2` になっているディストリビューション（例: `Ubuntu`）があれば OK です。

まだ WSL が入っていない場合:

```powershell
wsl --install -d Ubuntu
```

インストール後、Ubuntu を一度起動して Linux ユーザー名とパスワードを設定してください。

続いて **WSL の中に `git` を入れます**（方法 A で必須です）。Ubuntu のターミナルで:

```bash
sudo apt update && sudo apt install -y git
git --version
```

!!! warning "`wsl --list` に何も出ない / VERSION が 1 のとき"
    `wsl --set-version Ubuntu 2` で WSL 2 に変換できます。変換には時間がかかるので、作業の区切りで実行してください。

## 方法 A: Code タブの WSL セッション（推奨）

Claude Desktop の **Code タブ**は、セッションを Windows ではなく **WSL 2 ディストリビューションの中**で動かせます。Claude Code のプロセス・ツール・`git` がすべて WSL の中で実行され、Linux のツールチェーンと Linux のパス（`/home/you/project`）をそのまま使えます。

### 手順

1. **Claude Desktop を起動して Code タブを開く**

    初回に Windows で Code タブを開くときは [Git for Windows](https://git-scm.com/downloads/win) が必要です。入れていなければインストールし、アプリを再起動してください。

2. **新しいセッションを開始し、環境ピッカーを開く**

    インストール済みの WSL 2 ディストリビューションが **WSL** セクションに並びます。使うものを選びます。

3. **フォルダを選ぶ**

    セッションはディストリビューションのホームディレクトリから始まります。フォルダピッカーでプロジェクトフォルダを選んでください。**ブラウズは WSL の中で行われ、`/home/you/project` のような Linux パスで表示されます**。

4. **フォルダを信頼する（workspace trust）**

    そのフォルダでの最初のセッションでは信頼の確認ダイアログが出ます。信頼は**ディストリビューションごと・フォルダごと**です。あるディストリビューションで信頼したフォルダは、別のディストリビューションや Windows 側の同じパスでは信頼されません。

!!! note "初回は少し待ちます"
    そのディストリビューションでの最初のセッションは、Claude が WSL 内にセットアップを行うため通常より時間がかかります。2 回目以降は速くなります。

!!! tip "エクスプローラーから開くこともできます"
    通常のフォルダピッカーで `\\wsl.localhost\...` のフォルダを開くと、そのディストリビューションの中でセッションが開き直されます。最近使ったフォルダはディストリビューションごとに記憶されるので、再接続はワンクリックです。

### WSL セッションで使えるもの / 使えないもの

| | 内容 |
|---|---|
| **使える** | 並列セッション、サイドチャット、ビジュアル差分レビュー、ブランチ / PR ステータス、worktree（すべて WSL 内の `git` とツールチェーンで動く）、「Open in editor」（[Remote - WSL](https://code.visualstudio.com/docs/remote/wsl) 経由で VS Code が開く） |
| **まだ使えない** | 統合ターミナル、コネクタ / プラグイン、セッションのフォーク、ファイルブラウザペイン、コンポーザーで `@` を打ったときのファイル補完 |

!!! warning "組織で管理された PC では使えない場合があります"
    会社支給の管理対象デバイスでは WSL セッションが無効化されていることがあります。「デバイスが管理されています」というメッセージでセッション開始に失敗する場合は、管理者の設定によるものです。

### なぜ Windows 側から WSL のファイルを触らない方がよいのか

リポジトリが WSL のファイルシステムの中にある場合、Windows 側からそのファイルを扱うと**ネットワークファイルシステム（`\\wsl.localhost\...`）を経由する**ことになります。これは遅く、ファイル監視（file watching）も壊れます。**セッション自体を WSL の中で動かせば、どちらの問題も起きません。**

| 置き場所 | Windows から見たパス | WSL から見たパス | 速度 |
|---|---|---|---|
| WSL 側（推奨） | `\\wsl.localhost\Ubuntu\home\you\project` | `/home/you/project` | WSL から高速 / Windows から遅い |
| Windows 側 | `C:\Users\you\project` | `/mnt/c/Users/you/project` | Windows から高速 / WSL から遅い |

**リポジトリは WSL 側（`/home/you/...`）に置き、WSL セッションで作業する**のが素直な構成です。

## 方法 B: WSL の中で Claude Code CLI を動かす

ターミナル派の人、あるいは Code タブがまだ対応していない機能（統合ターミナル、プラグインなど）を使いたい場合は、**WSL の中に Claude Code をインストール**して CLI として使うのが確実です。

Ubuntu のターミナルで:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

インストール後、ターミナルを開き直して確認します:

```bash
claude --version
```

プロジェクトフォルダに移動して起動:

```bash
cd ~/project
claude
```

!!! note "Windows ネイティブの `claude` とは別物です"
    [Part 2](part2-installation.md) で PowerShell に入れた `claude.exe` と、WSL に入れた `claude` は**別のインストール**です。設定（`~/.claude/`）も別々に持ちます。CLAUDE.md や認証を両方で使いたい場合は、それぞれでログイン・設定してください。

!!! tip "どちらを使うかは「リポジトリがどちら側にあるか」で決める"
    リポジトリが `C:\Users\you\...` にあるなら Windows ネイティブ、`/home/you/...` にあるなら WSL 側。**プロセスとリポジトリを同じ側に揃える**とパスやツール検出のトラブルが起きません。

## 方法 C: MCP サーバーを `wsl.exe` 経由で動かす

Claude Desktop の **Chat タブ**から WSL の中のコマンドやファイルを扱いたい場合は、[MCP サーバー](../usage/advanced-extensions.md)を `wsl.exe` 経由で起動する設定を書きます。

!!! warning "先に方法 A / B を検討してください"
    この方法は設定ファイルの手書きが必要で、ハマりどころが多いです。「WSL のリポジトリで開発する」という目的なら方法 A の方が圧倒的に簡単です。
    この方法が必要なのは、**Chat タブでの会話中に WSL の特定のツールを呼びたい**というケースです。

### 設定ファイルの場所

```
%APPDATA%\Claude\claude_desktop_config.json
```

Claude Desktop の **Settings → Developer → Edit Config** から開くこともできます（ファイルが無ければ作成されます）。

### 設定例: WSL 内で filesystem MCP サーバーを動かす

```json
{
  "mcpServers": {
    "wsl-filesystem": {
      "command": "wsl.exe",
      "args": [
        "-d", "Ubuntu",
        "--",
        "bash", "-c",
        "npx -y @modelcontextprotocol/server-filesystem /home/you/project"
      ]
    }
  }
}
```

- `-d Ubuntu` — 使うディストリビューション名（`wsl --list --verbose` で確認した名前）
- `--` — これ以降を WSL 内で実行するコマンドとして渡す区切り
- パスは **Linux 形式**（`/home/you/project`）で書きます

### 設定例: WSL 内の Python で作った MCP サーバーを動かす

venv の Python を**絶対パス**で指定するのが確実です。

```json
{
  "mcpServers": {
    "my-wsl-tool": {
      "command": "wsl.exe",
      "args": [
        "-d", "Ubuntu",
        "--",
        "/home/you/project/.venv/bin/python",
        "/home/you/project/mcp_server.py"
      ]
    }
  }
}
```

環境変数を渡したい場合は、`bash -c` の中にインラインで書くのが最も素直です:

```json
{
  "mcpServers": {
    "my-wsl-tool": {
      "command": "wsl.exe",
      "args": [
        "-d", "Ubuntu",
        "--",
        "bash", "-c",
        "MY_API_KEY=xxxx /home/you/project/.venv/bin/python /home/you/project/mcp_server.py"
      ]
    }
  }
}
```

### ハマりどころ

!!! danger "JSON にコメントは書けません"
    設定例をコピーするときに `"-d", "Ubuntu",  // ディストリビューション名` のようなコメントを残すと、**JSON として壊れて設定全体が読み込まれません**。MCP サーバーが一つも出てこないときは、まずコメントや末尾カンマを疑ってください。

| 症状 | 原因 | 対処 |
|---|---|---|
| MCP サーバーが一覧に出てこない | JSON が壊れている（コメント・末尾カンマ）／アプリを再起動していない | JSON を検証し、**タスクマネージャーで Claude を完全終了**してから起動し直す |
| `node: command not found` / `npx` が見つからない | nvm で入れた Node は非ログインシェルの `PATH` に無い | `bash -c "source ~/.nvm/nvm.sh && npx ..."` のように読み込む、または Node の**絶対パス**を書く |
| 起動直後に接続が切れる | `.bashrc` / MOTD の出力が **stdout を汚している** | MCP（stdio）は stdout が JSON-RPC 専用。`bash -lc`（ログインシェル）を避け、`bash -c` を使う。バナー出力があるなら `.bashrc` の `echo` を見直す |
| ファイルが見つからない | Windows パス（`C:\...`）を書いている | WSL 内のパス（`/home/...` または `/mnt/c/...`）で書く |
| 変更が反映されない | アプリが常駐したまま | 完全終了して再起動 |

### ログの確認

うまく動かないときはログを見ます:

```powershell
type "%APPDATA%\Claude\logs\mcp*.log"
```

- `mcp.log` — MCP 接続全般のログ
- `mcp-server-<サーバー名>.log` — そのサーバーの stderr 出力

!!! tip "まず WSL のターミナルで手動起動してみる"
    設定の前に、同じコマンドを Ubuntu のターミナルでそのまま実行してみてください。手動で動かないものは Claude Desktop からも動きません。切り分けが一気に楽になります。

### Code タブ / CLI との関係

- Claude Desktop は `claude_desktop_config.json` の MCP サーバーを、**Chat タブと Code タブのローカルセッションの両方**に読み込みます（`~/.claude.json` や `.mcp.json` のサーバーと併せて）
- ただし **Claude Code CLI（`claude` コマンド）は `claude_desktop_config.json` を読みません**。macOS と WSL では `claude mcp add-from-claude-desktop` で `~/.claude.json` にコピーできます
- **WSL セッションではコネクタ / プラグインが使えません**（前述）。WSL セッションで MCP を使いたい場合は、WSL 内の `~/.claude.json` またはリポジトリの `.mcp.json` に設定します

!!! warning "MCP はトークンを消費します"
    MCP サーバーを接続すると、ツールのスキーマ分のトークンが常に消費されます。CLI で代替できるものは CLI に寄せた方が経済的です。詳しくは [トークン最適化](../usage/advanced-token-management.md) を参照してください。

## どれを選ぶか

```
リポジトリはどこにある？
├── /home/you/... （WSL 側）
│   ├── GUI で作業したい      → 方法 A: Code タブの WSL セッション
│   └── ターミナルで作業したい → 方法 B: WSL 内の claude CLI
├── C:\Users\you\... （Windows 側）
│   └── Part 2 の Windows ネイティブ claude をそのまま使う
└── Chat タブから WSL の特定コマンドを呼びたいだけ
    └── 方法 C: wsl.exe 経由の MCP サーバー
```

## 関連ページ

- [Part 2: Claude Code インストール（Windows）](part2-installation.md) — Windows ネイティブへのインストール
- [Windows での SSH 鍵ファイル管理](../tools/ssh/windows.md) — WSL2 と Windows で `~/.ssh` が別世界であることの解説
- [Docker をやさしく理解する](../tools/docker.md) — Windows の Docker Desktop が WSL2 上で動く仕組み
- [拡張機能](../usage/advanced-extensions.md) — MCP そのものの解説
- [トークン最適化](../usage/advanced-token-management.md) — MCP のトークンコスト
