# Claude Code Setup

Claude Code のセットアップガイドを mkdocs で構築・公開するプロジェクト。

## プロジェクト構成

- `docs/` - mkdocs ドキュメントソース（Part 1〜3 + 付録リンク集）
- `diagrams/` - drawio ダイアグラムソース（`diagrams/icons/` にブランドアイコン SVG）
- `.claude-plugin/` - マーケットプレイスカタログ（`marketplace.json`）
- `plugins/` - プラグイン配布用ディレクトリ
  - `workspace-setup/` - ワークスペース初期セットアップスキル
  - `cmux/` - cmux ウィンドウで GitHub Issue/PR を扱うスキル
  - `dev-loop/` - 1 Issue = 1 周のループ志向開発スキル
- `scripts/` - CI から呼ぶチェックスクリプト（標準ライブラリのみ・ローカルでも実行可）
  - `link-skills.sh` - スキルを `~/.claude/skills` へ素のスキルとして symlink する（bare 呼び出し用）
  - `test-link-skills.py` - 上記の回帰テスト。**実環境を対象にしないことをアサートで担保している**
- `mkdocs.yml` - mkdocs 設定
- `pyproject.toml` - Python 依存関係（uv で管理）
- `.github/workflows/docs.yml` - GitHub Pages 自動デプロイ
- `.github/workflows/plugins.yml` - プラグインカタログの整合チェック

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

## プラグインの更新

`plugins/` 配下の `SKILL.md` やコマンド定義を変更したら、**バージョンを必ず上げる**。

- `plugins/<name>/.claude-plugin/plugin.json` の `version`
- `.claude-plugin/marketplace.json` の該当プラグインの `version`

**この 2 箇所を同じ値に揃える。** バージョンを据え置いたまま中身だけ変えると、インストール済み
クライアントのキャッシュが更新を検知できず、旧い内容のスキルを使い続ける（#33 で実際に発生した）。

刻み方は semver に従う。

| 変更の性質 | 上げ方 | 例 |
| --- | --- | --- |
| 能力・手順の追加 | **minor** | 手順に新しい任意ステップを足す |
| 不具合・記述の修正 | **patch** | 指示の誤りを直す・typo |
| 既存の使い方が壊れる変更 | **major** | 引数や必須前提の変更 |

この整合は CI（`.github/workflows/plugins.yml`）で機械的にチェックしている。ローカルでも確認できる:

```bash
python3 scripts/check-plugin-versions.py        # 2 箇所の version 一致・カタログ構造
python3 scripts/check-version-bump.py origin/main   # bump 漏れ（PR の差分に対して）
```

## Git ワークフロー

- Issue 対応はブランチを切って PR 経由でマージ（ブランチ名: `issue/<番号>-<説明>`）
- main への直接プッシュはしない
- コミットメッセージに `Fixes #<番号>` を含めて Issue を自動クローズ

## デプロイ

- リポジトリ: github.com/hdknr/claude-code-setup（公開）
- サイト: https://hdknr.github.io/claude-code-setup/
- main への push で GitHub Actions が自動デプロイ
