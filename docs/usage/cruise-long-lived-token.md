# cruise を長期トークンで起動する（8 時間の期限で止めない）

対話ログイン（`/login`）の OAuth のアクセストークンは **8 時間**で切れます。更新に失敗すると、
不在のあいだに動いていた cruise が `401 OAuth access token has expired` で止まり、`/login` するまで戻りません
（[#584](https://github.com/hdknr/claude-code-setup/issues/584)。Mac Studio で、朝のログインのちょうど 8 時間後に 401 が集中していました）。

`claude setup-token` が発行する**長期トークン**を、**cruise を動かす端末でだけ** `CLAUDE_CODE_OAUTH_TOKEN` に入れて起動すると、
この 8 時間の期限を避けられる見込みです。**ただし、長期トークンで起動した cruise が 8 時間を超えて止まらないことは、まだ確かめていません**
（下の「確かめていないこと」）。

!!! warning "トークンを置かない場所"
    長期トークンの有効期間は、発行時に表示される期間が正です（#584 の記録では 1 年。ここでは確かめていません）。
    **`.zshrc`・`.env`・リポジトリ・Claude Code のセッションの中に置かないでください。**
    置くのは macOS のキーチェーンだけで、読むのは下の起動口だけです。
    全部のセッションに効かせると、1 本のトークンをすべてのプロセスに配ることになります。

## 部品

| 部品 | 置き場所（dev-loop スキルの base ディレクトリから） | 役割 |
| --- | --- | --- |
| 起動口 | `scripts/launch-with-long-token.sh` | キーチェーンからトークンを読み、`CLAUDE_CODE_OAUTH_TOKEN` に入れて `claude` を起動する。読めなければ**起動せずに理由を出して止まる**。`--store-token` で入れる・入れ替える、`--status` で入っているかを見る |
| 点検 | `scripts/check-unattended-env.py` | 「認証」の行で、長期トークンで起動したか、対話ログイン（8 時間）かを出す |

base ディレクトリの場所は [オートクルーズ](../plugins/dev-loop-cruise.md) の「部品の一覧」の下を見てください。
**起動口が何をし、どこで止まるかは、起動口の冒頭のコメントを正とします**（ここは要点だけです）。

## 手順

### 1. トークンを発行してキーチェーンに入れる（1 度だけ・入れ替えるとき）

**Claude Code のセッションの外の、別の端末で**行います。セッションの中（Bash や `!`）で `claude setup-token` を打つと、
表示されたトークンがセッションの記録に残ります。

```bash
claude setup-token                                   # ブラウザでログイン。表示されたトークンを控える
bash <base>/scripts/launch-with-long-token.sh --store-token   # プロンプトにトークンを貼る
```

- `--store-token` は `security add-generic-password -U -a "$USER" -s claude-long-token … -w` を走らせます。
  **`-w` を最後に置くと値をプロンプトで訊かれる**（`man security`）ので、トークンはシェルの履歴にも引数にも残りません。
  **プロンプトが入力を画面に出さないかは確かめていません。**
- 入れた日時（UTC）をキーチェーンの項目のコメントに残します。**これはトークンの発行日でも期限でもありません**——
  期限は手元からは読めません。切れていれば、起動した `claude` が 401 を出します。そのときはもう一度 1 を行います。
- 入っているかは `--status` で見られます（値は読みません）。

### 2. 起動口で cruise を起動する

```bash
bash <base>/scripts/launch-with-long-token.sh "/dev-loop:cruise <親 Issue> --absent"
```

引数はそのまま `claude` に渡ります。キーチェーンに無い・値が空・`security` が無い・macOS でないときは、**起動せずに止まります**
（対話ログインのまま起動すると、気づかないまま 8 時間で止まる状態に戻るためです）。
環境に `ANTHROPIC_API_KEY`・`ANTHROPIC_AUTH_TOKEN` があっても止まります——長期トークンより先に使われうるためです。

### 3. cruise の起動時の点検で確かめる

cruise は起動時に `check-unattended-env.py --cruise` を回し、「認証」の行を見せます。
**対話ログイン（8 時間）で起動していたら、長期トークンで回すかを訊きます**（利用者が居ないタイマーの再開では訊きません）。
長期トークンを選ぶと、cruise は 1 と 2 のコマンドを見せて、**周を始めずに止まります**——起動し直すと台帳から続きます。

**動いているセッションの認証は、そのセッションの中からは切り替えられません。** トークンは起動した `claude` の環境変数で、
セッションの中のコマンド（子のプロセス）からは親の環境を変えられないためです。Claude Code に、セッションの途中で認証を入れ替える別の道があるかは確かめていません。

### アカウントを分ける（`--account`）

```bash
bash <base>/scripts/launch-with-long-token.sh --account work --store-token
bash <base>/scripts/launch-with-long-token.sh --account work "/dev-loop:cruise <親 Issue> --absent"
```

アカウントごとにキーチェーンの別の項目（`claude-long-token-<名前>`）を使います。週の上限に当たったアカウントから
別のアカウントに切り替えて起動し直すためのものです。**切り替えるのは利用者で、cruise は切り替えません。**

## 確かめていないこと

**長期トークンが手元に無い環境で作ったので、次はまだ確かめていません**（発行は利用者の対話の操作です）:

1. **長期トークンで起動した cruise が、起動から 8 時間を超えても 401 で止まらないこと**
2. **cruise で使う機能が、長期トークンで動くか**——下の表の「実測」の欄は空です
3. **点検が、長期トークンで起動したセッションの中で「良い」と出ること**——Claude Code 2.1.312 の本体の文字列では、Bash などの子の環境から
   `CLAUDE_CODE_OAUTH_TOKEN` を消すのは `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` か GitHub Actions のときだけですが、実走では見ていません

### 機能の表

「見込み」は Claude Code 2.1.312 の本体の文字列から読んだもので、**実測ではありません**。**動くと確かめるまで「動く」とは書きません。**

| 機能 | 見込み（本体の文字列） | 実測 |
| --- | --- | --- |
| サブエージェント（`Agent`） | 推論だけで足りる見込み。制限の記述は見つけていない | 未 |
| `/code-review` | 同上 | 未 |
| Remote Control（`/remote-control`） | **使えない見込み**——「Remote Control requires a full-scope login token. Long-lived tokens (from `claude setup-token` or CLAUDE_CODE_OAUTH_TOKEN) are limited to inference-only」 | 未 |
| 通知（`PushNotification`） | **届かない見込み**——Remote Control につながっていないと送らない（点検の docstring の判定の順） | 未 |
| claude.ai のコネクタ（`/mcp`） | 分からない——長期トークンは `user:inference` だけで、コネクタの一覧には別のスコープ（`user:mcp_servers`）があるらしい | 未 |
| Claude in Chrome | **使えない見込み**——「env-var and setup-token sessions default to user:inference only」 | 未 |

**Remote Control と通知が使えないなら、不在のあいだに iPhone へ通知が届きません。** 長期トークンで回すかは、
8 時間で止まることと、通知が届かないことを比べて決めてください。

### 測り方（利用者が行う）

```bash
# 1 と 2 のとおり入れて、新しい端末で起動する
bash <base>/scripts/launch-with-long-token.sh
```

起動したセッションで:

- `/status`——認証の行が `CLAUDE_CODE_OAUTH_TOKEN` から来ているか
- `python3 <base>/scripts/check-unattended-env.py --cruise`——「認証」が `[良い]` か（上の 3）
- 表の各行——サブエージェントに 1 つ読ませる・小さな差分に `/code-review`・`/remote-control`・`/mcp`・iPhone への通知の試し（[リモートコントロールの設定手順](advanced-remote-control.md)）

8 時間を超えて止まらないか（上の 1）は、起動口で cruise を起動した時刻を控え、9 時間ほど後に、その間の記録に 401 が無いかを見ます:

```bash
grep -l "OAuth access token has expired" ~/.claude/projects/<プロジェクトのディレクトリ>/*.jsonl
```

[StopFailure の hook](usage-limit-stop-hook.md) を登録していれば、`~/.claude/usage-limit-stops.jsonl` に `authentication_failed` の行が無いことでも見られます。
結果は [#584](https://github.com/hdknr/claude-code-setup/issues/584) に書いてください。

## 関連

- [dev-loop のオートクルーズ](../plugins/dev-loop-cruise.md)
- [利用上限の停止をその場で記録する（StopFailure の hook）](usage-limit-stop-hook.md)
- [#473](https://github.com/hdknr/claude-code-setup/issues/473)（認証切れを cruise の停止として通知・点検・再開する）
