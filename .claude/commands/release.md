# リリース作成

GitHub Actions の release ワークフローを手動実行してリリースを作成します。

## 手順

### 1. バージョンの確認

ユーザーにリリースバージョンを確認してください。セマンティックバージョニング（例: `v1.0.0`, `v1.1.0`）を使用します。

既存のリリースを確認:

```bash
gh release list --repo hdknr/claude-code-setup
```

最新のタグを確認:

```bash
git tag --sort=-version:refname | head -5
```

### 2. リリースワークフローの実行

GitHub Actions の `release.yml` ワークフローを手動実行します:

```bash
gh workflow run release.yml --repo hdknr/claude-code-setup -f version={バージョン}
```

- `version`: リリースバージョン（例: `v1.2.0`）

### 3. 実行結果の確認

ワークフローの実行状況を確認:

```bash
gh run list --repo hdknr/claude-code-setup --workflow=release.yml --limit 1
```

リリースが作成されたか確認:

```bash
gh release view {バージョン} --repo hdknr/claude-code-setup
```
