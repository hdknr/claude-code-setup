# Claude Code 設定

Claude Code をインストールして使えるようにするための手順書です。

**サイト:** [https://hdknr.github.io/claude-code-setup/](https://hdknr.github.io/claude-code-setup/)

## この手順書について

- 対象: Claude Code を使い始めたい方
- 対応 OS: **macOS** / **Windows**
- 目的: Claude Code を日々の活動支援に活用できる環境を構築する

## 想定する利用用途

- 提案書・計画書の作成
- 写真などクリエイティブ制作物のポートフォリオ公開
- 履歴書作成
- 調査過程の思考の管理
- 確定申告など政府系への提出書類の整理

## お使いの OS を選んでください

### macOS（MacBook）

- 前提: iCloud の設定は完了済み
- パッケージ管理: [Homebrew](https://brew.sh/)

| パート | 内容 | 概要 |
|--------|------|------|
| [Part 1](macos/part1-preparation.md) | 事前準備 | Homebrew・GitHub CLI のインストール |
| [Part 2](macos/part2-installation.md) | Claude Code インストール | アカウント登録からインストールまで |
| [Part 3](macos/part3-post-setup.md) | インストール後の環境準備 | スキル設定・日常利用の準備 |

### Windows

- 対応: Windows 10 / 11
- パッケージ管理: [winget](https://learn.microsoft.com/ja-jp/windows/package-manager/winget/)（Windows 標準）

| パート | 内容 | 概要 |
|--------|------|------|
| [Part 1](windows/part1-preparation.md) | 事前準備 | Git・GitHub CLI・Node.js のインストール |
| [Part 2](windows/part2-installation.md) | Claude Code インストール | アカウント登録からインストールまで |
| [Part 3](windows/part3-post-setup.md) | インストール後の環境準備 | スキル設定・日常利用の準備 |

## 環境

- ターミナル: macOS は Terminal.app / Windows は PowerShell
- コード管理: [GitHub](https://github.com/)
- テキストエディタ: VSCode を前提としない（ターミナルで完結）
