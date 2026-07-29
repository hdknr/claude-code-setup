# dev-loop plugin

GitHub Issue 1 件を **検証（verify）が通ることを停止条件**として 1 周させる、
ループ志向開発のスキルを提供するプラグイン。どのプロジェクトでも使える汎用版。

設計思想（なぜループ志向か・verify を停止条件に据える理由・Dreaming・トークンコスト・
アンチパターン）は [dev-loop の設計](https://hdknr.github.io/claude-code-setup/plugins/dev-loop-design/) を参照。

## 提供スキル

### `/dev-loop <issue-number>`

対象 Issue を、以下の標準サイクルで 1 周させる。5↔4 は verify が通るまで繰り返す。

1. **Issue 選択** — `gh issue view` で要件・受入条件を把握
2. **文脈収集** — 関連設計・既存実装・過去の議論を読む
3. **計画** — 変更範囲を切り分け、設定／フラグで済むかを先に判断
4. **実装** — **worktree を開始**してから、対象リポジトリの `CLAUDE.md` のルールに従って変更
5. **検証（停止条件）** — 実機で目視確認 ＋ **別モデルの検証エージェント**で受入条件の反証を探す
6. **レビュー → PR** — `/code-review`、**worktree 上であることを確認**して PR 作成、結果を PR コメントに残す
7. **本番反映** — CLAUDE.md / deploy runbook に従う
8. **経験の還元** — 学びを CLAUDE.md / Skill / メモリへ焼き戻す

## プロジェクト固有部分の扱い

このスキルは特定プロジェクトに依存しない。実機検証コマンド・デプロイ経路・一次ソース
ドキュメントといった**プロジェクト固有の事情は、対象リポジトリの `CLAUDE.md`（および任意の
`.claude/dev-loop.md`）から発見**して従う。見つからなければ汎用手順（テスト実行＋アプリ起動での
手動確認）に縮退するので、設定ファイルが無くても動く。

より効果を出すには、対象リポジトリの `CLAUDE.md` に次を書いておくとよい:

- **実機検証（verify）の手順** — 開発サーバの起動方法、実データ接続、E2E の走らせ方
- **デプロイ経路** — 何をマージ／ビルド／apply すると本番に反映されるか
- **やってはいけない制約** — 破壊的操作・不可逆 apply の前提条件

## 前提

- `gh` CLI が認証済みであること
- 対象リポジトリが git 管理下にあること
- （任意）`/loop`・`/schedule`・`/code-review`・`/run` などの Claude Code 汎用スキル、
  GSD スキル群。無い環境では手動の待機・確認に読み替える。

## インストール

```
/plugin marketplace add hdknr/claude-code-setup
/plugin install dev-loop@claude-code-setup
```
