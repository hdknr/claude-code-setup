# Claude Code 設定

Claude Code をインストールして使えるようにするためのセットアップガイドです。

## ドキュメントサイト

👉 **https://hdknr.github.io/claude-code-setup/**

## 概要

開発者でない方が Claude Code を日常の活動支援に使い始めるための手順書です。

### 対象者

- GitHub やターミナル操作に詳しくない方
- 提案書・計画書の作成、ポートフォリオ公開、書類整理などに Claude Code を活用したい方

### 手順の構成

| パート | 内容 |
|--------|------|
| Part 1 | 事前準備（Homebrew, GitHub CLI, Node.js） |
| Part 2 | Claude Code インストールと認証 |
| Part 3 | インストール後の環境準備（スキル設定等） |

### 対応 OS

- macOS（対応済み）
- Windows（対応済み）

## ローカルでのドキュメント確認

```bash
uv sync --no-install-project
uv run mkdocs serve
```

http://127.0.0.1:8000 で確認できます。

## ライセンス

MIT
