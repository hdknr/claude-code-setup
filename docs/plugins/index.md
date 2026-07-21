# プラグイン一覧

このリポジトリは **プラグイン・マーケットプレイス**（`claude-code-setup`）として、いくつかのプラグインを配布しています。Claude Code から以下のコマンドでマーケットプレイスを追加し、必要なプラグインをインストールできます。

```
# マーケットプレイスを追加（最初に一度だけ）
/plugin marketplace add hdknr/claude-code-setup

# インストール済み・追加済みの一覧を確認・管理
/plugin
```

配布中のプラグインは以下のとおりです。

| プラグイン | 提供スキル | 概要 |
|---|---|---|
| [`workspace-setup`](#workspace-setup) | `/workspace-setup:workspace-setup` | ワークスペースの初期セットアップ |
| [`cmux`](#cmux) | `/cmux` | cmux ウィンドウで GitHub Issue/PR を操作 |

!!! info "プラグインの入れ方・使い方の全体像"
    インストール手順と日常利用の流れは [Part 3: インストール後の環境準備](../part3-post-setup.md) にもまとまっています。このページは各プラグインの**詳細リファレンス**です。

---

## workspace-setup

作業用ワークスペースの初期セットアップを対話的に行うプラグインです。Claude Code を使い始める最初の一歩をまとめて実行します。

### インストール

```
/plugin install workspace-setup@claude-code-setup
```

### 提供スキル

#### `/workspace-setup:workspace-setup`

以下を対話的にセットアップします。

1. **ワークスペースディレクトリの作成** — `~/Projects/` 配下にディレクトリを作成し `git init`（デフォルト名 `my-workspace`）
2. **CLAUDE.md の作成** — リポジトリの目的・日本語応答の指示などを記述
3. **GitHub プライベートリポジトリの作成と連携** — `gh repo create --private` で非公開リポジトリを作成・プッシュ
4. **完了確認** — 作成先パス・リポジトリ URL・次のステップの提示

!!! warning "必ずプライベートで作成"
    作業用リポジトリには個人情報や機密情報が含まれる可能性があるため、**必ず非公開（Private）**で作成します。詳細は [Part 3: インストール後の環境準備](../part3-post-setup.md) を参照してください。

### 前提

- `gh` CLI が認証済みであること

---

## cmux

[cmux](https://github.com/manaflow-ai/cmux) ウィンドウ内で GitHub の Issue/PR を扱うためのプラグインです。ブラウザペインに Issue/PR を表示し、worktree でレビューを行えます。

### インストール

```
/plugin install cmux@claude-code-setup
```

### 提供スキル

#### `/cmux [-n] [-w|-r] <number>`

cmux のブラウザペインで GitHub Issue/PR を開き、worktree でレビューを行います。

| 呼び出し | モード | 動作 |
|---|---|---|
| `/cmux <number>` | Issue | Issue の URL をブラウザペインに表示 |
| `/cmux -w <number>` | PR worktree | PR をブラウザ表示し、worktree を作成して `gh pr checkout` |
| `/cmux -r <number>` | PR レビュー | worktree でチェックアウトし、`gh pr diff` でレビュー開始 |

`-n` フラグを付けると、処理の最初に新しいターミナルタブ（サーフェス）を作成し、そこで実行します。

**使用例:**

```
# Issue 番号 12 をブラウザペインに表示
/cmux 12

# PR 番号 34 を worktree でチェックアウトしてレビュー
/cmux -r 34
```

### 前提

- `cmux` CLI がインストールされていること
- `gh` CLI が認証済みであること
- Claude Code の `EnterWorktree` ツールが利用可能であること
