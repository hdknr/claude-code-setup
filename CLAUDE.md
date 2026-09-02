# Claude Code Setup

Claude Code のセットアップガイドを mkdocs で構築・公開するプロジェクト。

## プロジェクト構成

- `docs/` - mkdocs ドキュメントソース（Part 1〜3 + 付録リンク集）
- `diagrams/` - drawio ダイアグラムソース（`diagrams/icons/` にブランドアイコン SVG）
- `.claude-plugin/` - マーケットプレイスカタログ（`marketplace.json`）
- `plugins/` - プラグイン配布用ディレクトリ
  - `workspace-setup/` - ワークスペース初期セットアップの**コマンド**（このプラグインだけスキルを持たない）
  - `cmux/` - cmux ウィンドウで GitHub Issue/PR を扱うスキル
  - `dev-loop/` - 1 Issue = 1 周のループ志向開発スキル
- `scripts/` - CI から呼ぶチェックスクリプト（標準ライブラリのみ・ローカルでも実行可）
  - `check-plugin-versions.py` - カタログ構造と version 一致
  - `check-version-bump.py` - 中身を変えたのに version を上げていない差分（PR 限定）
  - `check-description-sync.py` - description の同期漏れ（PR 限定）
  - `link-skills.sh` - スキルを `~/.claude/skills` へ素のスキルとして symlink する（bare 呼び出し用）
  - `test-link-skills.py` / `test-check-description-sync.py` /
    `test-check-plugin-versions.py` - 上記の回帰テスト。
    **いずれも実環境を対象にしないことをアサートで担保している**
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

**この 2 つの JSON は同じ値に揃える。** バージョンを据え置いたまま中身だけ変えると、インストール済み
クライアントのキャッシュが更新を検知できず、旧い内容のスキルを使い続ける（#33 で実際に発生した）。

さらに **そのプラグインが持つ `SKILL.md` すべての本文にも同じ版を書く**。
**揃える箇所は合わせて 3 種類**（`marketplace.json` / `plugin.json` / `SKILL.md`）で、
CI のエラーメッセージもそう案内する。
**2 行 1 組**で、見出しの直後に置く（理由は下の「version を上げるだけでは届かない」）:

```markdown
<!-- skill-version: 1.2.3 -->
> **このスキルの版: 1.2.3**（プラグイン `<name>`）。
```

1 行目は機械が読む印、**2 行目が利用者の目に入る側**で、こちらが本体。
`check-plugin-versions.py` は**両方**を検査する（片方だけだとエラー）。
可視テキストは**行頭が `> **このスキルの版: `** であることまで見る（散文の途中に同じ
文字列があっても数えないため）。**コメントやコードフェンスで囲って無効化した記載は
そもそも数えない**——「読者には見えないのに CI は緑」を防ぐのはこちらの仕組み。

刻み方は semver に従う。

| 変更の性質 | 上げ方 | 例 |
| --- | --- | --- |
| 能力・手順の追加 | **minor** | 手順に新しい任意ステップを足す |
| 不具合・記述の修正 | **patch** | 指示の誤りを直す・typo |
| 既存の使い方が壊れる変更 | **major** | 引数や必須前提の変更 |

### version を上げるだけでは届かない

**version bump は必要条件であって十分条件ではない。** 利用者側のマーケットプレイスのクローンが
導入時のコミットで凍結していると、**カタログを読み直すまで version の変化自体が見えない**。

実測（2026-09-02、#63）: このリポジトリのマーケットプレイスは利用者の手元で **2026-07-29 の
コミットのまま**で、`dev-loop` は **1.0.0** のまま使われていた（約 5 週間）。
その間に 1.7.0 まで上げていたが、**1 度も届いていなかった**。#33 の対策（version bump）だけでは防げていなかったことになる。

利用者が更新するには **2 段階**が要る:

```
/plugin marketplace update              # カタログ（クローン）を取り直す
/plugin update <plugin>@claude-code-setup   # プラグインを新しい版に上げる（要再起動）
```

`autoUpdate` を有効にしているマーケットプレイスは自動で追随するが、**これはクライアント側の
状態**（`~/.claude/plugins/known_marketplaces.json`）で、**リポジトリ側からは設定できない**。
`/plugin` の対話メニューで設定できるとされる。

そこで、リポジトリ側からできる歯止めとして **SKILL.md の本文に版を書いている**。
古いキャッシュが読まれれば**その版が目に入る**ので、乖離に気づける。
`check-plugin-versions.py` が plugin.json との一致を強制する（記載漏れもエラー）。

**常に最新を使いたい場合は、プラグインではなく symlink 経路を選ぶ**——
`scripts/link-skills.sh` で `~/.claude/skills/` に張れば、リポジトリを `git pull` した時点で
反映される（キャッシュを経由しないため、構造的に古くならない）。
**ただしスクリプトは自分の位置からリポジトリを解決して絶対パスで張る**ので、
**worktree から実行するとその worktree に固定される**。メインの作業ツリーから実行すること。

この整合は CI（`.github/workflows/plugins.yml`）で機械的にチェックしている。ローカルでも確認できる:

```bash
python3 scripts/check-plugin-versions.py            # version の一致（3 箇所）・カタログ構造
python3 scripts/check-version-bump.py origin/main   # bump 漏れ（PR の差分に対して）
python3 scripts/check-description-sync.py origin/main   # description の同期漏れ（同上）
python3 scripts/test-check-plugin-versions.py       # 版チェックの歯止め自体のテスト
```

### description は 3 箇所にある

`version` と同じく、`description` も **3 箇所**に複製されている。ただし**揃え方が違う**。

| 箇所 | 役割 |
| --- | --- |
| `.claude-plugin/marketplace.json` | カタログの紹介文 |
| `plugins/<name>/.claude-plugin/plugin.json` | マニフェスト |
| `plugins/<name>/skills/<skill>/SKILL.md` の frontmatter | **常時ロードされる要約** |

**version と違い、3 つを同じ値に揃えるのは誤り。** frontmatter は「いつこのスキルを起動するか」を
書く別目的の文章で、カタログの紹介文より長く引数の説明も含む（`dev-loop` は frontmatter が
JSON の 2 倍ほどある）。**具体的な文字数はここに書かない**——本文を直すたびに古くなり、
実際 #62 の周で、古い実測値をそのまま書いて事実誤りを出した。

**揃えるべきなのは値ではなく更新のタイミング。どれかを直したら、残りも点検する。**
とくに frontmatter は**本文を読む前の判断材料**なので、置き去りにすると**古い規範が先に読まれる**。
#59 / PR #60 の周では、本文が「達成不能だから」と否定した文言を要約が掲げ続ける状態が生じ、
同じ同期漏れが**向きを変えて 2 回**起きた（本文＋frontmatter を直して JSON が残る →
JSON を直して frontmatter が残る）。

`check-description-sync.py` はこの**共変**を base との diff で見る。片側だけ直すのが正しい場合
（カタログの typo 修正など）は、コミットメッセージに理由つきの trailer を書く:

```
Skip-description-sync: カタログの typo 修正のみ。要約の内容は変わらない
```

## Git ワークフロー

- Issue 対応はブランチを切って PR 経由でマージ（ブランチ名: `issue/<番号>-<説明>`）
- main への直接プッシュはしない
- コミットメッセージに `Fixes #<番号>` を含めて Issue を自動クローズ

## デプロイ

- リポジトリ: github.com/hdknr/claude-code-setup（公開）
- サイト: https://hdknr.github.io/claude-code-setup/
- main への push で GitHub Actions が自動デプロイ
