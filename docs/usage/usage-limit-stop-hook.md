# 利用上限の停止をその場で記録する（StopFailure の hook）

利用上限で止まったとき、**止まったその場で手元のファイルに 1 行残し、通知を出す**ための hook の設定手順です。
[#456](https://github.com/hdknr/claude-code-setup/issues/456)（上限での自動継続が実際に起きるかの確認）は、
**上限を狙って起こせない**ので、作業中に自然に当たるのを待つしかありません。
気づかなければ記録は埋もれ、止まったときに「継続」と打てば確認になりません。この hook はその取りこぼしを減らします（#468）。

!!! warning "自動継続が起きたかは、この hook には分かりません"
    hook が知っているのは**止まった時点**だけです。その後に自動で続いたか・人間が続けたかは、
    後から `scripts/count-usage-limit-resumes.py` で数えます。**記録があることが「数える時が来た」の合図**です。

## 何をするか

hook の本体は [`scripts/record-stop-failure.py`](https://github.com/hdknr/claude-code-setup/blob/main/scripts/record-stop-failure.py) です（標準ライブラリのみ）。

- `~/.claude/usage-limit-stops.jsonl` に 1 行追記します
- macOS なら通知を出します。上限らしい `error`（`rate_limit`・`billing_error`）のときだけ、
  「止まっても『継続』と打たずにリセットまで待ってください」と添えます

**何を書き、何を書かないか（案件の中身は書きません）と、何を守らないかは、スクリプトの docstring を正とします。**

## 設定する

登録は**利用者が行います**（リポジトリから利用者の settings を書き換えることはしません）。
全プロジェクトのセッションで効かせるため、**user の settings**（`~/.claude/settings.json`）の `hooks` に足します。
`<リポジトリ>` は、このリポジトリを clone した**メインの作業ツリー**の絶対パスに置き換えてください
（worktree のパスを書くと、その worktree を消したときに hook が動かなくなります）。

```json
{
  "hooks": {
    "StopFailure": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 <リポジトリ>/scripts/record-stop-failure.py"
          }
        ]
      }
    ]
  }
}
```

既に `hooks` があるなら、その中に `StopFailure` の項目だけを足します。

**matcher は書きません**——`StopFailure` を全部記録し、記録の `error` の値で後から見分けます。
利用上限がどの値で来るかを確かめていないためです（下の「確かめていないこと」）。
Claude Code 2.1.311 の本体は `billing_error` を「usage limit reached — check plan」、`rate_limit` を
「rate limited — wait and retry」に対応づけており、**`rate_limit` だけに絞ると、上限の停止を取りこぼすおそれがあります**。

`StopFailure` は、API のエラー（rate limit・認証の失敗など）でターンが終わったときに `Stop` の代わりに発火するイベントで、
matcher は入力の `error` に当たります（値には `rate_limit` のほか `authentication_failed`・`overloaded`・`billing_error` などがあります。
Claude Code 2.1.311 の本体の文字列から読みました）。**hook の出力と終了コードは無視されます**（本体の説明文）。hook が壊れているときに何か表示されるかは確かめていません
——**何も出ないことを「hook が動いた」と読まないでください**（記録のファイルに行が増えたかで確かめます）。

## 確かめたこと・確かめていないこと

**確かめたこと**（2026-10-27・Claude Code 2.1.311・macOS。#468）: 一時 `HOME` と無効な API キーで `claude -p` を起こし、
`--settings` で同じ形の hook を渡しました。

| matcher | 結果 |
| --- | --- |
| なし | 記録が 1 行出た（`error: authentication_failed`） |
| `authentication_failed` | 記録が 1 行出た |
| `rate_limit` | 記録は出なかった |

**確かめていないこと**:

- **利用上限（claude.ai の上限）で実際に発火するか、`error` がどの値（`rate_limit`・`billing_error` ほか）になるか**——上限を狙って起こせません。
  **記録が無いことは「発火しない」の証拠になりません**（hook の登録が誤っていても記録は無いままです）
- 自動継続の待ちの間に何回発火するか
- user の settings に書いた形・対話のセッションでの発火——確かめたのは `--settings` と `claude -p` の組だけです
- 通知が画面に出ること（macOS の通知の設定で出ないことがあります）

## 記録が出たら

1. **「継続」と打たずに、リセットの時刻まで待ちます**（自動継続が起きるかを見るため）
2. 時刻を過ぎたら、`python3 scripts/count-usage-limit-resumes.py --anonymize` で数えます
3. 結果を [#456](https://github.com/hdknr/claude-code-setup/issues/456) に貼ります。**hook は Issue を立てたりコメントしたりしません**——
   このリポジトリは公開で、hook は非公開の案件のセッションでも発火するので、何を貼るかは人間が見て決めます

## 関連

- [dev-loop のオートクルーズ — 環境を点検する](../plugins/dev-loop-cruise.md#env-check)
- [拡張機能 — Hook](advanced-extensions.md)
