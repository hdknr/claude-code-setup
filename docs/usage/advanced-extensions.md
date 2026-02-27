# Claude Code の拡張機能

Claude Code には、基本操作に加えて**5つの拡張機能**があります。これらを使うと、Claude Code をより賢く、便利にカスタマイズできます。

!!! info "この章は慣れてきてからで大丈夫です"
    ここで紹介する機能は、Claude Code の基本操作に慣れてから少しずつ取り入れれば十分です。まずは [基本操作](basic-operations.md) と [CLAUDE.md](claude-md.md) をマスターしましょう。

## 拡張機能の全体像

| 機能 | 一言で言うと | どこに置く | 動くタイミング |
|---|---|---|---|
| **Task** | 別の Claude に仕事を任せる | `.claude/agents/` | Claude が判断 or ユーザー指示 |
| **Skill** | 再利用できる手順書 | `.claude/skills/` | 自動 or `/スキル名` で呼び出し |
| **Hook** | イベント時に自動実行するスクリプト | `settings.json` の `hooks` | 特定イベント発生時に必ず実行 |
| **MCP** | 外部サービスとの接続 | `.mcp.json` | Claude がツールとして使用 |
| **Plugin** | 上記をまとめて配布するパッケージ | `.claude-plugin/` | インストール時 |

## Task（サブエージェント）— 別の Claude に仕事を振る

**Task** は、Claude Code が内部的に**別の Claude を立ち上げて、作業を分担する**機能です。Claude Code ではこれを「サブエージェント」とも呼びます。

### 日常の例えで理解する

あなたがプロジェクトマネージャー（= メインの Claude）だとします。大きな仕事を抱えたとき、全部を自分でやるのではなく、チームメンバーに一部を頼みます。

```
あなた（メインの Claude）:「この機能を実装したい」
  ├── 部下A（サブエージェント）:「既存コードの調査をしてきて」→ 結果だけ報告
  ├── 部下B（サブエージェント）:「テストファイルを分析してきて」→ 結果だけ報告
  └── あなた（メインの Claude）: 報告を受けて、実装を判断・実行
```

### なぜ Task が必要なの?

Claude Code には[コンテキスト（会話の記憶）](concepts.md)の上限があります。

- **Task なし**: メインの Claude が調査もコーディングも全部やる → 調査結果で記憶が埋まり、肝心の実装時に容量が足りなくなる
- **Task あり**: 調査は別の Claude がやり、**結論だけ**メインに返す → メインの記憶がクリーンに保たれ、実装に集中できる

### 組み込みの Task タイプ

以下のタイプは Claude Code に最初から入っています。追加設定は不要です。

| タイプ | できること | 使いどころ |
|---|---|---|
| **Explore** | ファイル検索、コード読み取り | 「この関数がどこで使われてるか調べて」 |
| **Plan** | 設計・計画の策定 | 「実装方針を考えて」 |
| **general-purpose** | 何でも（ファイル編集、コマンド実行含む） | 「この部分を修正して」 |

Claude Code が自動的に判断して Task を使うこともあれば、CLAUDE.md に「調査はサブエージェントに委譲せよ」と書いて積極的に使わせることもできます。

### 発展: カスタムエージェント

組み込みの Task に加えて、`.claude/agents/` フォルダに自分専用のエージェントを定義できます。

```markdown
# .claude/agents/test-runner.md
---
name: test-runner
description: テストを実行して結果を報告する
tools: Bash, Read, Glob
---
あなたはテスト実行の専門家です。
- テストを実行し、失敗したテストの原因を分析
- 修正案を提示（修正自体は行わない）
```

!!! tip "まずは組み込みの Task だけで十分"
    カスタムエージェントは必要になってから作ればよいです。日常的な作業では、組み込みの Task で十分対応できます。

## Skill（スキル）— 手順書を渡す

**Skill** は、**再利用可能な手順書・テンプレート**です。Task とは違い、別の Claude は立ち上がりません。メインの会話にそのまま読み込まれます。

イメージとしては「マニュアルを手渡す」こと。Claude が賢くなるわけではなく、**やり方を教える**仕組みです。

### Skill の作り方

`.claude/skills/` フォルダに手順書ファイルを置きます。

```markdown
# .claude/skills/deploy/SKILL.md
---
name: deploy
description: 本番環境へのデプロイ手順
---
1. テストを実行する
2. ビルドする
3. デプロイコマンドを実行する
```

### 使い方

- **手動で呼び出す**: `/deploy` と入力
- **自動で読み込まれる**: `description` にマッチする場面で Claude が自動的に読み込むこともある

### 何に使うと便利?

- コーディング規約
- API の使い方
- 定型作業の手順（デプロイ、リリースなど）

!!! info "Task との違い"
    **Task** は「別の人に仕事を頼む」（別の Claude が動く）。**Skill** は「自分用のマニュアルを読む」（メインの Claude が手順に従う）。

## Hook（フック）— 条件付きの自動スクリプト

**Hook** は、**特定のイベントが起きたら問答無用で実行されるスクリプト**です。Claude の判断とは無関係に動きます。

日常の例え: 「ドアが開いたら自動で照明が点く」ような仕組みです。

### 設定例

`settings.json` の `hooks` に記述します。

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "npx prettier --write $(jq -r '.tool_input.file_path')"
      }]
    }]
  }
}
```

この例は「ファイルを編集・作成したら、自動でコードフォーマッターを実行する」フックです。

### 主なイベント

| イベント | タイミング |
|---|---|
| `SessionStart` | セッション開始時 |
| `PreToolUse` | ツール実行前（ブロックも可能） |
| `PostToolUse` | ツール実行後 |
| `Stop` | Claude の応答完了時 |

!!! info "Task / Skill との違い"
    Task と Skill は「Claude が何をするか」に関わります。Hook は「Claude の行動に対して、外部のスクリプトが反応する」仕組みです。Claude はフックの存在を知らなくても動作します。

## MCP（Model Context Protocol）— 外の世界と繋ぐ

**MCP** は、**外部のツールやサービスを Claude に接続する**標準プロトコルです。GitHub、データベース、Slack、Figma など、Claude Code 単体ではアクセスできないサービスとの橋渡しをします。

### 設定例

プロジェクトルートの `.mcp.json` に記述します。

```json
{
  "mcpServers": {
    "github": {
      "transport": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

Claude にとっては「使えるツールが増える」感覚です。外部サービスの読み書きが可能になります。

!!! info "他の機能との違い"
    Task / Skill / Hook は Claude Code の「内部」の仕組み。MCP は「外部」との接続です。

## Plugin（プラグイン）— 全部まとめて配る

**Plugin** は、Task、Skill、Hook、MCP を**1つのパッケージにまとめて配布する**仕組みです。

```
my-plugin/
├── .claude-plugin/plugin.json   ← マニフェスト
├── skills/                      ← スキル群
├── agents/                      ← エージェント群
├── hooks/hooks.json             ← フック設定
└── .mcp.json                    ← MCP 設定
```

チームや組織で「うちのプロジェクトではこのツールセットを使う」と統一するのに便利です。

## 使い分けの判断フロー

どの機能を使えばいいか迷ったときは、以下のフローで判断してください。

```
やりたいこと
  ├── 外部サービスに接続したい        → MCP
  ├── ファイル保存時に自動処理したい    → Hook
  ├── 手順書・テンプレートを再利用したい → Skill
  ├── 重い作業を別の Claude に任せたい  → Task
  └── 全部まとめてチームに配りたい      → Plugin
```

!!! tip "最も重要な違い"
    - **Task**: 別の Claude が別の記憶空間で作業する
    - **Skill**: メインの Claude に知識を注入する
    - **Hook**: Claude の判断に関係なく必ず実行される
    - **MCP**: 外部サービスへのアクセスを追加する

## 参考リンク

- [Claude Code 公式: Sub Agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
- [Claude Code 公式: Skills](https://docs.anthropic.com/en/docs/claude-code/skills)
- [Claude Code 公式: Hooks](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code 公式: MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)
