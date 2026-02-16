# Claude Code Setup

Claude Code のセットアップガイドを mkdocs で構築・公開するプロジェクト。

## プロジェクト構成

- `docs/` - mkdocs ドキュメントソース（Part 1〜3 + 付録リンク集）
- `diagrams/` - drawio ダイアグラムソース（`diagrams/icons/` にブランドアイコン SVG）
- `mkdocs.yml` - mkdocs 設定
- `pyproject.toml` - Python 依存関係（uv で管理）
- `.github/workflows/docs.yml` - GitHub Pages 自動デプロイ

## 開発コマンド

```bash
uv sync --no-install-project    # 依存関係インストール
uv run mkdocs serve              # ローカルプレビュー (http://127.0.0.1:8000)
uv run mkdocs build              # サイトビルド
```

## 図表の更新

drawio ファイルを編集後、SVG エクスポートが必要:

```bash
/Applications/draw.io.app/Contents/MacOS/draw.io --export --format svg --output docs/images/<name>.svg diagrams/<name>.drawio
```

ブランドアイコンは Simple Icons (simpleicons.org) から取得し、base64 で drawio に埋め込んでいる。

## Git ワークフロー

- Issue 対応はブランチを切って PR 経由でマージ（ブランチ名: `issue/<番号>-<説明>`）
- main への直接プッシュはしない
- コミットメッセージに `Fixes #<番号>` を含めて Issue を自動クローズ

## デプロイ

- リポジトリ: github.com/hdknr/claude-code-setup（公開）
- サイト: https://hdknr.github.io/claude-code-setup/
- main への push で GitHub Actions が自動デプロイ
