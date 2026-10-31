#!/usr/bin/env python3
r"""利用者が不在になる前に 1 度だけ回す、環境の点検（#394）。

    python3 <このスキルの base ディレクトリ>/scripts/check-unattended-env.py [--project <dir>]
        [--command '<コマンド>' ...] [--flag-settings <file>] [--managed-settings <file>]
    python3 <このスキルの base ディレクトリ>/scripts/check-unattended-env.py --cruise [--present] [--ledger <名前>] [...]
    python3 <このスキルの base ディレクトリ>/scripts/check-unattended-env.py --push-result '<返り値>'

**直さない。読むだけ**——何が足りないかと、どう直すかを出す。**利用者の設定を書き換える道具は、
不在の前に回すものとしては危険が勝る**（`--fix` を置かないのは意図である）。

## なぜ要るか（#389）

利用者不在で複数の周を回した運用で、**通知は「No mobile registered」のまま届かず、原因は
切り分けられなかった**。`PushNotification` は「Push when Claude decides」がオフだと
`mobile push is disabled in /config` で送られない。**どれも不在になってからでは直せない**
——気づく人がいない。

## 点検する項目

| 項目 | 見るもの | 良い | 要対処 |
| --- | --- | --- | --- |
| 許可 | settings の `permissions`（`allow`・`ask`・`deny`・`defaultMode`・`disableBypassPermissionsMode`） | 名指しのコマンドごとに、`allow` に当たるか `defaultMode` が `bypassPermissions`（`disableBypassPermissionsMode` で落とされていない） | `deny` か `ask` に当たる（`allow` があっても）／どれも無い |
| 自動継続 | settings の `autoContinueAtUsageLimit`（**managed・flag・user の層だけ**） | `true` | 未設定・`false`・真偽値でない |
| 質問の待ち | settings の `askUserQuestionTimeout`（**managed・flag・user の層だけ**） | `60s` `5m` `10m` | 未設定・`never`・それ以外 |
| 通知 | グローバル設定（下の「設定の層」）の `agentPushNotifEnabled`（`/config` の「Push when Claude decides」）と `inputNeededNotifEnabled`（「Push when actions required」） | `true` | 未設定・`false` |
| スリープ | macOS の `pmset -g custom`・`pmset -g batt`・`ps` | いまの電源の `sleep` が 0、または `-t`・`-w` の無い `caffeinate` が system の idle sleep を防いでいる（`-i`・`-d`・`-s` か、アサーションのフラグ無し） | どちらも無い |
| 認証（#584。`--present` でも出す） | このスクリプトの環境変数（**Claude Code の Bash から回せば、セッションの環境を継いでいる**）と settings の `apiKeyHelper` | `CLAUDE_CODE_OAUTH_TOKEN` が空でない（長期トークン） | どれも無い——対話ログインの OAuth（8 時間で切れる。`--present` では人が見る）。直し方に起動口 `launch-with-long-token.sh` の絶対パス |

認証の項目は、ほかに 2 つの判定を持つ（値は出力に出さない。見るのは空かどうかだけ）:

- **人が見る**——`ANTHROPIC_AUTH_TOKEN`・`ANTHROPIC_API_KEY` が空でない、か `apiKeyHelper` がある。長期トークン・対話ログインより先に使われうるので、どれで認証しているかは `/status` で見る
- **判定できない**——`CLAUDECODE` が `1` でない（Claude Code のセッションの外で回した。セッションの起動のしかたは外から見えない）か、
  サブプロセスの環境から認証の変数が消される（`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` が真、または `GITHUB_ACTIONS` が真で前者が偽でない）

**人が見る**（手元のファイルからは判定できないので、毎回出す。終了コードには効かない）:

- **モバイルの登録**——「No mobile registered」はサーバ側の状態で決まる。`/config` で確かめ、下の「通知の試験」で届くかを見る
- **Remote Control**——いまのセッションで繋がっているかは外から見えない。`remoteControlAtStartup` の値だけ添える。
  **iPhone がつながる先は、いまのセッション（`/remote-control`）であって `claude rc` の待ち受けではない**
  ——待ち受けは新しいセッションを起こすので、そこから送った 1 行は作業中のセッションに届かない
- **蓋を閉じる・電源が変わる**——`pmset` の値は電源ごとで、蓋を閉じればスリープする

## cruise の起動時（`--cruise`・`--present`。#466）

**cruise は `--absent` に依らず、台帳を作ったら 1 度これを回す**（cruise `SKILL.md` §3）——
利用者が居る cruise でも、**権限の拒否・確認で周が止まり、利用者の操作を待つ**（#466 の実測）。

- `--cruise` は 4 つを足す（4 つ目の到達できる範囲は下の「不在の間にどこまで進めるか」）:
    - **周で使う操作の宣言**——`--project` の `.claude/dev-loop.md` の `cruise の操作: <コマンド>` の行（1 行 1 コマンド。
      コードフェンスの中は読まない。フェンスは開いた記号と同じ種類・同じ長さ以上の行でだけ閉じる）を、点検するコマンド（既定か `--command`）に足す。**本番反映の口**
      （`gh workflow run …`・`aws ecs run-task …` など）は既定に無いので、ここで宣言させる。
      宣言が無ければ「人が見る」で、既定だけを見たと出す。読めなければ「判定できない」、値の無い行は「要対処」。
      **宣言の形に届かなかった行**（字下げ・箇条書き・引用・全角コロン）も読まずに「要対処」
    - **止まりうる操作**（人が見る）——**自動モードの分類器と worktree 隔離のガードは settings に現れない**ので、
      上で「良い」と出た操作も止まりうる。点検したコマンドを全部並べ、(a) 許可を足す・(b) その操作だけ利用者が打つ
      （`ledger.py user-ops`）・(c) その周を cruise の外に出す、の選び方を添える。**選ばせるのは cruise の `SKILL.md`**
    - **親の起動場所**——cwd が worktree の中（`--git-dir` ≠ `--git-common-dir`）なら要対処。**cruise の親は
      メインの作業ツリーから、worktree に入らずに起動するのが既定**（#466）——隔離のガードが別の worktree・別のリポジトリへの
      操作を拒むので
    - **到達できる範囲**——`--ledger` で渡した台帳の周ごとの到達と止まる要因。渡さなければ判定できない
- `--present` は**利用者が居る cruise**——不在に限る項目（自動継続・質問の待ち・通知・スリープ・人が見る 3 つ）を出さない。
  **認証は出す**（cruise の起動時に長期トークンで回すかを訊くため。#584）——8 時間のトークンは要対処ではなく人が見る（居れば `/login` で戻れる）。
  許可の要対処の文言も「確認で周が止まる」にする（答える人は居るが、そこで止まる）

## 不在の間にどこまで進めるか（`--cruise --ledger <名前>`。#490）

    python3 check-unattended-env.py --cruise [--present] --ledger issue-<親>

**cruise は起動時（新規・再開、`--absent` の有無に依らず）に台帳の名前を渡して回す**（cruise `SKILL.md` §3）。
台帳（同じ場所の `ledger.py` で読む。書かない）の済んでいない周ごとに、**到達**——「マージまで進む見込み」「PR で止まる」
「始まらない（依存先と、止まる元）」「止まっている」——と理由を出す。`--ledger` を渡さない `--cruise` は「判定できない」（見ていない）。

- **マージの線**（1 行）——不在の間に `マージ` の線が効くか。**機械で決まる部分だけを見る**:
  `--present` なら利用者が承認する（人が見る）。台帳の確かめた線の `マージ` → 無ければ `.claude/dev-loop.md` の
  `不在の線: マージ = …`（1 本だけ）が `関門を通ればマージ` でなければ効かない。台帳の `user_ops` に `gh pr merge`・`merge-pr.py` を
  含む操作があれば効かない（周はマージの手前で await）。`マージの反映:` の宣言（1 本だけ・フェンスとコメントの外）が
  `ドキュメントとプラグインの配布` なら、線が台帳にあり `ledger.py` の配布の確認の印があるときだけ効く。
  宣言がそれでないのにプラグインのカタログ（`.claude-plugin/marketplace.json`）があれば効かない（マージが配布を起こす）。
  `ドキュメントのみ` なら効く。宣言が無ければ「判定できない」（`CLAUDE.md` でしか決まらない）。
  **効くと出しても、照合（ワークフロー・`CLAUDE.md`・周の差分）は見ていない**——各周がマージの前に行う（`references/absent-lines.md`）
- **周ごと**（`到達 #<番号>`）——`await` は止まる（`note`）、`blocked` は止まる（`note` が `利用者の判断待ち` で始まればそのまま、
  ほかは「止まっている」）、まとめの中で取り残された行（`ledger.py` の名指し）は止まる。進行中（`impl`・`gate`・`pr`）は
  `note` が `利用者の判断待ち` で始まればマージの前の判断待ちで止まる。PR の番号があれば `gh pr view <番号> --json state,mergeable,files` で、
  閉じていれば止まる、`CONFLICTING` なら衝突で止まる、`MERGEABLE` でなければ（`UNKNOWN` など）判定できない、
  **同じ `.claude-plugin/plugin.json` を触る開いた PR が 2 本以上**なら版の取り合いで止まる（まとめの行が同じ 1 本の PR を持つのは数えない）、
  マージ済みなら進む（台帳を直す）。そのほかはマージの線のとおり。`todo` は依存先を辿り（まとめの中の依存は済んだと読む）、
  止まる依存先があれば「始まらない」と止まる元の番号を出す
- **まとめ**（`到達できる範囲`。人が見る）——マージまで進む・利用者の承認を待つ・止まる・判定できないの番号の一覧

止まる周は要対処（終了コード 1）、判定できない周は判定できない（2）、居る cruise の承認待ちは人が見る。

## 通知の試験（`--push-result`）

    python3 check-unattended-env.py --push-result '<PushNotification の返り値>'

**送るのはモデル、離れるのは人**なので、スクリプトは**返り値の判定だけ**をする（設定は読まない）。
手順（いつ送るか）は `SKILL.md` の環境点検の項を正とする。返り値の文字列は部分一致で見る——
`Remote Control inactive` と `Mobile push requested` には、非対話のセッション（`isNonInteractiveSession`。`-p` など）でなければ前に
`Terminal notification sent.` が付く（本体は OS の通知が実際に出たかを見ていない）。

| 返り値に含まれる | 判定 | 原因 | 対処 |
| --- | --- | --- | --- |
| `mobile push is disabled in /config` | 要対処 | 「Push when Claude decides」（`agentPushNotifEnabled`）がオフ | `/config` でオン |
| `this terminal is active` | やり直す（2） | 使用中と判定された（端末のフォーカスが分かればそれだけで決まり、分からなければ最後の操作から 60 秒以内） | **失敗ではない。** 遅らせて、端末を前面から外し、端末にも iPhone にも触らずに送り直す |
| `Remote Control inactive` | 要対処 | いまのセッションが Remote Control につながっていない | 作業中のセッションで `/remote-control` |
| `Mobile push requested` | 人が見る | **要求しただけ**——届いたかはサーバと iPhone で決まる | iPhone に届いたか。届かなければ iPhone の通知の許可・集中モード・アカウントと組織 |
| （どれでもない・空） | 判定できない（2） | 知らない文言（版が違う・写し間違い） | **送り直さない。** 返り値を言い換えずにそのまま渡し直す |

**判定の順に注意**（本体の `PushNotification`）: **使用中は Remote Control の有無より先に止まる**ので、
省かれた陰で Remote Control が切れていても分からない。**Remote Control がつながっていなければ
`/config` のオフは出ない**——直すたびに送り直して、次の返り値を見る。

## 設定の層

**managed > flag（`--settings`）> local > project > user** の順に重ねる。`permissions.allow`・
`permissions.ask`・`permissions.deny` は**全層を足し合わせ**、それ以外は**いちばん上の層の値**を採る。
**例外が 2 つある**: `autoContinueAtUsageLimit`・`askUserQuestionTimeout` は **managed・flag・user の層しか読まない**
（project・local に書いても効かない）。managed の `allowManagedPermissionRulesOnly` が `true` なら、
**許可の規則は managed の層のものだけ**を数える。

- user: `~/.claude/settings.json`（`CLAUDE_CONFIG_DIR` を置いていれば `$CLAUDE_CONFIG_DIR/settings.json`）
- project: `<project>/.claude/settings.json`、local: `<project>/.claude/settings.local.json`
  （`--project` の既定は cwd のリポジトリの**メインの作業ツリー**の root——**worktree の root ではない**。
  gitignore された `settings.local.json` は worktree に無い。リポジトリでなければ cwd）
- flag: `--flag-settings` で渡す。**渡さなければ、最寄りの祖先の `claude` の `--settings <file>`・`--settings=<file>`
  から拾う**（cmux は前者の形で起動する）。**最寄りの `claude` に無ければ、それより外側は見ない**。
  `claude` は `argv[0]` の名前が `claude` か、`…/versions/<版>` の本体を指す。
  **渡された・拾ったパスが無ければ「判定できない」**（未設定ではない）。**`ps` が失敗したときと、
  最寄りの `claude` が spare（`--bg-spare`。設定は引き継ぎで渡り、argv に無い）のときも「判定できない」**——
  flag の層を読めない層として積む
- managed: `--managed-settings` で渡す。既定は macOS の
  `/Library/Application Support/ClaudeCode/managed-settings.json`、Linux の `/etc/claude-code/managed-settings.json`。
  **同じ場所の `managed-settings.d/*.json` を名前順に、その上に重ねる**
- グローバル設定（通知）: `<設定のディレクトリ>/.config.json` が在って空でなければそれ、
  無ければ `$CLAUDE_CONFIG_DIR/.claude.json`（置いていなければ `~/.claude.json`）

## 終了コード

- **0**: 要対処も判定できないも無い（**人が見る項目は残っている**——出力を読む）
- **1**: 要対処がある
- **2**: 要対処は無いが、判定できないがある（設定が壊れている・`pmset` が無い・macOS 以外 など）

`--push-result` も同じ 3 つで返す。**2 は「やり直す」（使用中で省かれた）と「判定できない」（知らない返り値）の両方**
——**終了コードでは分けられないので、ラベルを読む**（前者は送り直す、後者は返り値を渡し直す）。

## 実測した前提（2026-10-25・Claude Code 2.1.310・macOS）

本体の文字列で確かめた。**版が変われば変わりうる**:

- `autoContinueAtUsageLimit` は settings の真偽値で、**未設定のときの既定は別の条件で決まる**
  （文字列からは読み切れない）。だから**未設定を要対処にする**——明示させる
- `askUserQuestionTimeout` は settings の `60s` `5m` `10m` `never` で、既定は `never`
- `autoContinueAtUsageLimit`・`askUserQuestionTimeout` は `["policySettings","flagSettings","userSettings"]` の
  層だけから読む（`EM()`）
- `agentPushNotifEnabled`・`inputNeededNotifEnabled` はグローバル設定にある。グローバル設定の場所は
  `<設定のディレクトリ>/.config.json` が在って空でなければそれ、無ければ `.claude<接尾辞>.json`（`y_()`）
- managed（policySettings）の `allowManagedPermissionRulesOnly` が `true` なら、managed 以外の規則は無視される
- `managed-settings.d` を読む（`managed-settings.d read failed:` の文言がある）
- managed の `permissions.disableBypassPermissionsMode` は「a session that requests it anyway is downgraded」
- 設定のディレクトリは「$CLAUDE_CONFIG_DIR or ~/.claude」
- 子のセッションには `--settings=<x>` の形で渡す
- **走っている `claude` は、作業中に子として `caffeinate -i -t 300` を張る**。
  **だから `pmset -g assertions` の `PreventUserIdleSystemSleep` は、Claude 自身の作業で 1 になる**
  ——**待機中に保たれる根拠にならない**。`-t` の付いた `caffeinate` は数えない
- `PushNotification` の判定は ① Remote Control がつながっていて `agentPushNotifEnabled` が偽 → `config_off`、
  ② 使用中 → `user_present`、③ Remote Control がつながっていない → `no_transport`、④ 送信、の順
  （`CLAUDE_CODE_REMOTE`・リモートのセッション・transport が持続するセッションでは ①〜③ をすべて飛ばして送る）。
  使用中は、端末のフォーカスが分かればそれだけで決まり、分からなければ最後の操作から 60 秒以内（`Ins()`）。
  返り値の文字列は上の「通知の試験」の表のとおり
- 「No mobile registered」は `/config` の表示（`has_active_channel === false`）で、`PushNotification` の返り値ではない
- `claude remote-control`（`claude rc`）は「spawned sessions」を起こす待ち受け（`--help`）

認証（#584。**2.1.312 の本体の文字列で読んだ。実走の陽性対照は取っていない**——長期トークンが手元に無い）:

- 認証のトークンの出所は `ANTHROPIC_AUTH_TOKEN` → `CLAUDE_CODE_OAUTH_TOKEN` → OAuth のファイル記述子 → `apiKeyHelper` → … →
  保存した claude.ai のログイン（対話ログイン）の順に選ぶ。API キー（`ANTHROPIC_API_KEY`・`apiKeyHelper`）があれば OAuth のトークンは使わない
- Bash などの子の環境から認証の変数を消すのは、`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` が真か、`GITHUB_ACTIONS` が真で前者が偽でないときだけ
- 「env-var and setup-token sessions default to user:inference only」・「Remote Control requires a full-scope login token.
  Long-lived tokens (from `claude setup-token` or CLAUDE_CODE_OAUTH_TOKEN) are limited to inference-only」——
  **長期トークンでは Remote Control が使えない見込み**で、上の `PushNotification` は Remote Control が要る。**どちらも実測していない**

## 何を守り、何を守らないか

守る:

- **読めなかったものを「良い」に混ぜない**——壊れた JSON・失敗したコマンドは「判定できない」。
  **ファイルが無いのは失敗ではない**（未設定として扱う。flag の層だけは例外——上の「設定の層」）。
  **値を見つける前に読めない層を通ったら、その項目は「判定できない」**——上の層が値を上書きしているかもしれない。
  許可は、`deny`・`ask` に当たらず読めない層がどこかにあれば「判定できない」
- **層の優先順位**——下の層の `true` を、上の層の `false` が打ち消す
- **`deny`・`ask` は `allow` より強い**——どちらかに当たれば要対処
- **Claude 自身の `caffeinate -t` を、スリープ防止の根拠にしない**——`-it 300`・`-t300` のようにまとめた形と、
  `-w`（プロセスの終わりまで）も時限として数える。`-m`（ディスク）・`-u`（利用者の操作。既定 5 秒）だけの形は数えない
- **人が見る項目を、要対処が無くても毎回出す**
- **使用中で省かれた通知を失敗と数えない**——`--push-result` は「やり直す」（2）で返し、1 にしない。
  **知らない返り値とはラベルで分ける**（どちらも 2）
- **送信の要求を「届いた」と言わない**——`Mobile push requested` は人が見る（iPhone に届いたか）
- **知らない返り値を「良い」に混ぜない**——判定できない
- **何も書かない**——設定ファイルにも、どこにも
- **`--cruise` で、宣言した操作を点検から落とさない**——既定（か `--command`）に足す。フェンスの中の行は宣言にしない。
  **種類の違うフェンスの記号では閉じない**。**宣言の形に届かなかった行を黙って読み飛ばさない**（要対処）
- **`--cruise` で、止まりうる操作を「良い」と出した操作からも外さない**——settings の判定とは別の区分で全部出す
- **`--cruise` で、worktree の中からの起動を「良い」にしない**——判定できなければ「判定できない」
- **`--present` で、許可の項目を落とさない**——落とすのは不在に限る項目だけ
- **認証で、セッションの外の環境・変数が消される環境を「8 時間」とも「長期トークン」とも言わない**——判定できない
- **認証で、長期トークンより先に使われうる認証があるのに「長期トークン」と言わない**——人が見る
- **認証のトークンの値を出さない**——空かどうかしか見ない
- **`--cruise` で台帳を渡さない・読めない（無い・名前の形が違う・壊れている）ときに、到達を通過と読まない**——判定できない。
  `--ledger` は `--cruise` と一緒にだけ受ける（2）
- **到達で、衝突・閉じた PR・判断待ちの印・`await`・`blocked`・取り下げ・取り残された行を「進む」にしない**——止まる。
  **`gh` が失敗した・`mergeable` が `MERGEABLE` でない・PR の番号が読めないときも「進む」にしない**——判定できない
- **到達で、止まる・判定できない依存先を辿る**——依存の依存が止まっても「始まらない」と言い、止まる元の番号を出す。
  **まとめの中の依存は待たない**（`ledger.py` の `next` と同じ）
- **マージの線を、線が無い・台帳の線が `止まる`（`.claude/dev-loop.md` より先に読む）・`不在の線:` や宣言が 2 本以上・
  フェンスの中の宣言・マージを利用者が打つ（`user_ops`）・配布の宣言で印が無い・カタログがあるのに配布の宣言が無いときに「効く」と言わない**。
  宣言もカタログも無ければ判定できない
- **居る cruise（`--present`）で、マージの承認待ちを要対処にしない**——人が見る
- **台帳を書かない**——`ledger.py` の `load` と `ledger_path` しか使わない。**`note` は切って出す**（同じ `note` が依存する周の数だけ並ぶ）

守らない:

- **許可の照合は近似である**——`Bash`・`Bash(*)`・`Bash(<前置き>:*)`・`Bash(<前置き> *)`・
  `Bash(<前置き>*)`・`Bash(<コマンド>)` の形だけを見る。**名指しのコマンドは引数つきで呼ばれるものとして
  照合する**——引数の無い `Bash(git push)` は `git push -u origin <ブランチ>` に当たらないので、覆っていない。**ハーネスの照合器が正**で、
  **auto モードの分類器が何を通すかは見ない**（`allow` の無いコマンドは、分類器が拒否しても
  答える人がいないので要対処にしている）
- **サーバから配られる managed settings**——ファイルに無いものは見えない
- **`managed-settings.d/` の重ね方**——名前順に後のものが勝つとしているのは慣例からの推定で、本体の文字列では確かめていない
- **グローバル設定のファイル名の接尾辞**——本体は `.claude<接尾辞>.json` で、接尾辞は認証の形で変わる
  （`-custom-oauth` など）。**接尾辞の無い `.claude.json` だけを見る**。本体が `.config.json` を選ぶ条件の
  うち、空のファイルを書き込み可能な権限で選ぶ分岐は写したが、それより前の分岐（`J()`）は読み切れていない
- **祖先の `claude` の `--allowedTools`・`--disallowedTools`・`--permission-mode`**——規則の出所だが読まない
- **`autoContinueAtUsageLimit: true` が十分であること**——本体は課金の種類とフラグでも自動継続を止める。
  `true` は必要条件で、「良い」はそれを満たしたことしか言わない。**実データにも、続かなかった形がある**（#454。
  `scripts/count-usage-limit-resumes.py` で数えた。件数は少ない）——待ちを張らなかった停止があり（理由は記録に残らない）、
  Claude Code が終わると待ちは消える。
  タイマーを保険に張るかは利用者が決める（`docs/plugins/dev-loop-cruise.md` の §5）
- **macOS の managed preferences（plist）**——読まない
- **`caffeinate <コマンド>` の形**——コマンドが終われば防止も終わるが、`-t` の無い形として数える
- **`ask` の規則と `bypassPermissions` の組**——`bypassPermissions` でも `ask` は要対処にしている（確認が出るかは確かめていない。安全側）
- **submodule・`--separate-git-dir` の作業ツリー**——`--project` の既定の root を誤りうる。`--project` で渡す
- **`--settings` に JSON を直接渡した形と、パスに空白を含む形**——`ps` の出力からは正しく切れない。
  `--flag-settings` で渡す
- **macOS 以外のスリープ**——判定できないと出す
- **2.1.310 以外の版でキー名が同じであること**——`PushNotification` の返り値の文字列も同じ
- **iPhone に届いたこと**——`Mobile push requested` から先は見えない
- **分類器・ガードが実際にどの操作を止めるか**——試さない（副作用の無い試し方は別の Issue）。止まりうるとして全部並べるだけ
- **セッションが worktree 隔離にあること**——見ているのは cwd だけ。メインの作業ツリーにいても、後で `EnterWorktree` すれば隔離される
- **`.claude/dev-loop.md` の宣言の網羅**——宣言に無い操作は見えない
- **iPhone からの操作が使用中になるか**——本体からは読み切れていない（利用者の実測。#407）。だから手順は両方から離れる形にしてある
- **到達は見込みである**——関門・CI・利用上限・権限の拒否で止まる周は数えない（起動時には分からない）。
  **マージの線の照合**（ワークフロー・`CLAUDE.md`・周の差分）は見ない。**宣言が無くカタログも無いリポジトリで、マージが反映を起こすか**は見ない（判定できない）
- **判断待ちは印 `利用者の判断待ち` で始まる `note` だけを読む**——印の無い自由文（「P1 はマージ前に人間が判断」）は読まない。
  印を書くのは親（cruise `SKILL.md` §4 の 4）。**狭いパスの指摘があるのに印の無い PR は「進む」と出る**
- **版の取り合いは `.claude-plugin/plugin.json` を触る PR だけを見る**——ほかの版のファイル・版を上げない衝突は見ない。
  `gh pr view` の `files` が多くのファイルを触る PR で全件を返すかは確かめていない
- **積んだ周（stacked）**——到達に数えない（`ledger.py` の `next` と同じ）
- **`gh pr view` の値の形**——偽の `gh` で当てている。本物の値の形は 2026-10-31 に cruise #474 の台帳の写しで 1 度見ただけ
- **長期トークンが有効か（期限切れ・取り消し）・8 時間を超えて止まらないこと**——値を読まないので見えない（公開ページの測る表）
- **対話ログインの保存先（キーチェーン・`~/.claude/.credentials.json`）**——読まない。長期トークンも API キーの類も無ければ、
  セッションは対話ログインで起動したと見なす（ほかの出所——OAuth のファイル記述子・クラウドの事業者——は見ない）
"""

import argparse
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

DEFAULT_COMMANDS = (
    "git push",
    "gh pr create",
    "gh pr merge",
    "gh pr comment",
    "gh issue create",
)
TIMEOUT_OK = ("60s", "5m", "10m")
MANAGED_DEFAULTS = {
    "darwin": "/Library/Application Support/ClaudeCode/managed-settings.json",
    "linux": "/etc/claude-code/managed-settings.json",
}

GOOD, ACTION, UNKNOWN, HUMAN = "良い", "要対処", "判定できない", "人が見る"
RETRY = "やり直す"  # --push-result だけが使う。原因は分かっていて、送り直せば済む


class Unreadable:
    """読めなかったこと。**値と別の型にして、空と混ぜない。**"""

    def __init__(self, path, reason):
        self.path = path
        self.reason = reason


def read_json(path):
    """無ければ None（未設定）、壊れていれば `Unreadable`。"""
    p = Path(path)
    try:
        # exists() は使わない——親ディレクトリを読めないときの PermissionError を飲んで「無い」と言う
        text = p.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return None
    except (OSError, ValueError) as e:
        # ValueError: UTF-8 として読めない（UnicodeDecodeError）——例外で落とさない
        return Unreadable(p, str(e))
    try:
        data = json.loads(text)
    except ValueError as e:
        return Unreadable(p, str(e))
    if not isinstance(data, dict):
        return Unreadable(p, "オブジェクトでない")
    return data


def run(cmd):
    """(成功したか, 標準出力)。コマンドが無いのも失敗。"""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError:
        return False, ""
    return proc.returncode == 0, proc.stdout


def is_claude(argv0):
    """`claude`、または `…/versions/<版>` で走る本体。"""
    p = Path(argv0)
    return p.name == "claude" or (p.parent.name == "versions" and re.fullmatch(r"\d+(\.\d+)+", p.name) is not None)


def find_flag_settings(pid=None):
    """祖先の `claude … --settings <file>` を探す。(パス or None, 失敗の理由 or None)。"""
    pid = pid or os.getppid()
    seen = set()
    while pid and pid > 1 and pid not in seen:
        seen.add(pid)
        ok, out = run(["ps", "-o", "ppid=,command=", "-p", str(pid)])
        if not ok or not out.strip():
            return None, f"ps が pid {pid} を読めなかった"
        ppid, _, command = out.strip().partition(" ")
        argv = command.split()
        if argv and is_claude(argv[0]):
            # 最寄りの claude で止める——外側の claude の --settings は、このセッションのものではない
            if "--bg-spare" in argv:
                return None, f"最寄りの claude（pid {pid}）は spare から引き継いだセッションで、--settings は argv に無い"
            for i, arg in enumerate(argv):
                if arg == "--settings" and i + 1 < len(argv):
                    return argv[i + 1], None
                if arg.startswith("--settings="):
                    return arg[len("--settings="):], None
            return None, None
        try:
            pid = int(ppid)
        except ValueError:
            return None, f"ps の出力を読めなかった: {out.strip()[:80]}"
    return None, None


def config_dir(home, env):
    """`$CLAUDE_CONFIG_DIR`、無ければ `~/.claude`。"""
    value = env.get("CLAUDE_CONFIG_DIR")
    return Path(value).expanduser() if value else home / ".claude"


def managed_dropins(managed_path):
    """`managed-settings.json` と同じ場所の `managed-settings.d/*.json`（名前順）。"""
    d = Path(managed_path).parent / "managed-settings.d"
    try:
        # is_dir() も PermissionError を飲むので使わない
        return sorted(p for p in d.iterdir() if p.suffix == ".json")
    except (FileNotFoundError, NotADirectoryError):
        return []
    except OSError as e:
        return [Unreadable(d, str(e))]


def layers(project, flag_path, managed_path, home, env=None, flag_note=None):
    """低い層から高い層の順に (名前, パス, 中身) を返す。"""
    env = os.environ if env is None else env
    stack = [("user", config_dir(home, env) / "settings.json")]
    stack.append(("project", project / ".claude" / "settings.json"))
    stack.append(("local", project / ".claude" / "settings.local.json"))
    stack = [(name, path, read_json(path)) for name, path in stack]
    if flag_path:
        # 渡された（拾った）のに無いのは「未設定」ではない——読むはずのファイルが読めていない
        path = Path(flag_path)
        data = read_json(path)
        stack.append(("flag", path, Unreadable(path, "ファイルが無い") if data is None else data))
    elif flag_note:
        # 祖先を読めなかった——flag の層が在るかどうか分からないので、読めない層として積む
        where = Path("（祖先の claude）")
        stack.append(("flag", where, Unreadable(where, flag_note)))
    if managed_path:
        stack.append(("managed", Path(managed_path), read_json(managed_path)))
        for dropin in managed_dropins(managed_path):
            if isinstance(dropin, Unreadable):
                stack.append(("managed.d", dropin.path, dropin))
            else:
                stack.append(("managed.d", dropin, read_json(dropin)))
    return stack


SESSION_LAYERS = ("user", "flag", "managed", "managed.d")  # 本体の EM() が読む層
MANAGED_LAYERS = ("managed", "managed.d")


def effective(stack, key, only=None):
    """いちばん上の層の値。(値, 層の名前) か、未設定なら (None, None)。

    **値を見つける前に読めない層を通ったら (`Unreadable`, 層の名前)**——その層が値を
    上書きしているかもしれないので、下の層の値を「良い」の根拠にしない。
    `only` を渡せば、その名前の層だけを見る。"""
    for name, _path, data in reversed(stack):
        if only is not None and name not in only:
            continue
        if isinstance(data, Unreadable):
            return data, name
        if isinstance(data, dict) and key in data:
            return data[key], name
    return None, None


def perm_value(stack, key):
    """`permissions.<key>` について `effective()` と同じこと。"""
    for name, _path, data in reversed(stack):
        if isinstance(data, Unreadable):
            return data, name
        perms = data.get("permissions") if isinstance(data, dict) else None
        if isinstance(perms, dict) and key in perms:
            return perms[key], name
    return None, None


def unknown_item(label, value, layer):
    return (UNKNOWN, label, f"{layer} の層 {value.path} を読めなかった（{value.reason}）——上書きされているかもしれない", "")


def managed_rules_only(stack):
    """managed の `allowManagedPermissionRulesOnly` が true か。"""
    return any(isinstance(data, dict) and data.get("allowManagedPermissionRulesOnly") is True
               for name, _path, data in stack if name in MANAGED_LAYERS)


def collect_rules(stack, kind, managed_only=False):
    rules = []
    for name, _path, data in stack:
        if managed_only and name not in MANAGED_LAYERS:
            continue
        if isinstance(data, dict):
            perms = data.get("permissions")
            if isinstance(perms, dict) and isinstance(perms.get(kind), list):
                rules.extend(r for r in perms[kind] if isinstance(r, str))
    return rules


def rule_matches(rule, command):
    """`Bash(...)` の規則が command に当たるか（**近似**。docstring）。"""
    if rule == "Bash":
        return True
    m = re.fullmatch(r"Bash\((.*)\)", rule)
    if not m:
        return False
    body = m.group(1)
    if body in ("*", ":*"):
        return True
    for suffix in (":*", " *", "*"):
        if body.endswith(suffix):
            prefix = body[: -len(suffix)]
            if suffix == "*":
                return command.startswith(prefix)
            return command == prefix or command.startswith(prefix + " ")
    return command == body


def check_permissions(stack, commands, present=False):
    items = []
    managed_only = managed_rules_only(stack)
    allow = collect_rules(stack, "allow", managed_only)
    ask = collect_rules(stack, "ask", managed_only)
    deny = collect_rules(stack, "deny", managed_only)
    broken = [(name, data) for name, _path, data in stack if isinstance(data, Unreadable)]
    mode, mode_layer = perm_value(stack, "defaultMode")
    bypass_off, _ = perm_value(stack, "disableBypassPermissionsMode")
    bypass_ok = mode == "bypassPermissions" and bypass_off not in ("disable", True)
    wait = "確認で周が止まる（利用者の操作を待つ）" if present else "確認されても答える人がいない"
    for command in commands:
        # 名指しのコマンドは引数つきで呼ばれる——引数の無い Bash(git push) は覆っていない
        call = command + " <引数>"
        denied = [r for r in deny if rule_matches(r, call)]
        asked = [r for r in ask if rule_matches(r, call)]
        allowed = [r for r in allow if rule_matches(r, call)]
        label = f"許可: `{command}`"
        if denied:
            items.append((ACTION, label, f"deny に当たる（{', '.join(denied)}）",
                          "deny の規則を外すか、この周の手順からそのコマンドを外す"))
        elif asked:
            # ask は allow より強い——確認を出して、答える人がいないまま止まる
            items.append((ACTION, label, f"ask に当たる（{', '.join(asked)}）——" + wait,
                          "ask の規則を外すか、この周の手順からそのコマンドを外す"))
        elif broken:
            # 読めない層に deny・ask があるかもしれない
            items.append((UNKNOWN, label, "読めない層がある（" + ", ".join(n for n, _ in broken) +
                          "）——そこに deny・ask があるかもしれない", ""))
        elif allowed:
            items.append((GOOD, label, f"allow に当たる（{', '.join(allowed)}）", ""))
        elif bypass_ok:
            items.append((GOOD, label, f"defaultMode が bypassPermissions（{mode_layer}）", ""))
        else:
            shown = mode or "未設定"
            if mode == "bypassPermissions":
                shown += "。ただし disableBypassPermissionsMode で落とされる"
            if managed_only:
                shown += "。managed の allowManagedPermissionRulesOnly で、managed 以外の規則は効かない"
            items.append((ACTION, label,
                          f"allow に無い（defaultMode: {shown}）——拒否・" + wait,
                          f'settings の permissions.allow に "Bash({command}:*)" を足す'))
    return items


def check_auto_continue(stack):
    value, layer = effective(stack, "autoContinueAtUsageLimit", SESSION_LAYERS)
    label = "自動継続（autoContinueAtUsageLimit）"
    if isinstance(value, Unreadable):
        return [unknown_item(label, value, layer)]
    if value is True:
        return [(GOOD, label, f"true（{layer}）", "")]
    shown = "未設定（既定は条件で変わる）" if layer is None else f"{json.dumps(value)}（{layer}）"
    return [(ACTION, label, shown,
             'user の settings に "autoContinueAtUsageLimit": true を書く'
             '（/config の「Continue automatically at usage limit」。project・local では効かない）')]


def check_question_timeout(stack):
    value, layer = effective(stack, "askUserQuestionTimeout", SESSION_LAYERS)
    label = "質問の待ち（askUserQuestionTimeout）"
    if isinstance(value, Unreadable):
        return [unknown_item(label, value, layer)]
    if value in TIMEOUT_OK:
        return [(GOOD, label, f"{value}（{layer}）", "")]
    shown = "未設定（既定は never）" if layer is None else f"{json.dumps(value)}（{layer}）"
    return [(ACTION, label, shown,
             'user の settings に "askUserQuestionTimeout": "10m" などを書く（60s / 5m / 10m。project・local では効かない）'
             '——never だと質問で止まり続ける')]


def global_config_path(home, env):
    """本体の y_() の写し: `<設定のディレクトリ>/.config.json` が在って空でなければそれ、
    無ければ `$CLAUDE_CONFIG_DIR/.claude.json`（置いていなければ `~/.claude.json`）。接尾辞は見ない（docstring）。"""
    legacy = (Path(env["CLAUDE_CONFIG_DIR"]).expanduser() if env.get("CLAUDE_CONFIG_DIR") else home) / ".claude.json"
    candidate = config_dir(home, env) / ".config.json"
    try:
        st = candidate.stat()
    except OSError:
        return legacy
    if stat.S_ISREG(st.st_mode) and (st.st_size > 0 or (st.st_mode & 0o222 and not legacy.exists())):
        return candidate
    return legacy


def check_notifications(home, env=None):
    env = os.environ if env is None else env
    path = global_config_path(home, env)
    data = read_json(path)
    items = []
    keys = (("agentPushNotifEnabled", "Push when Claude decides"),
            ("inputNeededNotifEnabled", "Push when actions required"))
    for key, ui in keys:
        label = f"通知（{key}）"
        if isinstance(data, Unreadable):
            items.append((UNKNOWN, label, f"{path} を読めなかった: {data.reason}", ""))
        elif isinstance(data, dict) and data.get(key) is True:
            items.append((GOOD, label, "true", ""))
        else:
            shown = "未設定" if not isinstance(data, dict) or key not in data else json.dumps(data[key])
            items.append((ACTION, label, shown, f"/config の「{ui}」をオンにする"))
    return items


def parse_pmset_custom(text):
    """{電源の名前: sleep の分}。"""
    out, source = {}, None
    for line in text.splitlines():
        if line and not line.startswith(" ") and line.rstrip().endswith(":"):
            source = line.rstrip()[:-1]
            continue
        m = re.match(r"^\s*sleep\s+(\d+)", line)
        if m and source:
            out[source] = int(m.group(1))
    return out


def timed_caffeinate(argv):
    """`-t`（時間）か `-w`（プロセスの終わりまで）を持つか。`-it 300`・`-t300` のようにまとめた形も見る。"""
    for arg in argv[1:]:
        if not arg.startswith("-"):
            if arg.isdigit():
                continue  # -t・-w の値
            return False  # ここから先は caffeinate が走らせるコマンド
        if re.fullmatch(r"-[dimsutw]*[tw][dimsutw]*\d*", arg):
            return True
    return False


def prevents_idle_sleep(argv):
    """system の idle sleep を防ぐか——`-i`・`-d`・`-s` を持つか、アサーションのフラグが 1 つも無い
    （`man caffeinate`: 無ければ idle sleep を防ぐ）。`-m`（ディスク）・`-u`（利用者の操作）だけなら防がない。"""
    flags = ""
    for arg in argv[1:]:
        if not arg.startswith("-"):
            if arg.isdigit():
                continue
            break
        flags += re.sub(r"\d", "", arg[1:])
    assertions = set(flags) & set("dimsu")
    return not assertions or bool(assertions & set("ids"))


def long_lived_caffeinate(ps_text):
    """`-t`・`-w` の無い、idle sleep を防ぐ caffeinate のコマンド行。"""
    found = []
    for line in ps_text.splitlines():
        argv = line.split()
        if (argv and Path(argv[0]).name == "caffeinate" and not timed_caffeinate(argv)
                and prevents_idle_sleep(argv)):
            found.append(line.strip())
    return found


def check_sleep(platform):
    label = "スリープ"
    if platform != "darwin":
        return [(UNKNOWN, label, f"{platform} のスリープは点検しない（macOS だけ）", "")]
    ok_custom, custom = run(["pmset", "-g", "custom"])
    ok_batt, batt = run(["pmset", "-g", "batt"])
    ok_ps, ps_text = run(["ps", "-axo", "command="])
    if not (ok_custom and ok_batt and ok_ps):
        return [(UNKNOWN, label, "pmset か ps を読めなかった", "")]
    m = re.search(r"Now drawing from '([^']+)'", batt)
    sleeps = parse_pmset_custom(custom)
    if not m or m.group(1) not in sleeps:
        return [(UNKNOWN, label, "いまの電源の sleep を pmset から読めなかった", "")]
    source, minutes = m.group(1), sleeps[m.group(1)]
    if minutes == 0:
        return [(GOOD, label, f"{source} の sleep が 0（スリープしない）", "")]
    keep = long_lived_caffeinate(ps_text)
    if keep:
        return [(GOOD, label, f"-t の無い caffeinate が在る（{keep[0][:60]}）", "")]
    return [(ACTION, label,
             f"{source} の sleep が {minutes} 分で、-t の無い caffeinate が無い"
             "（Claude 自身の caffeinate -t 300 は作業中しか張られない）",
             "別の端末で `caffeinate -i` を回しておく（または `sudo pmset -c sleep 0`）")]


LAUNCHER = Path(__file__).resolve().parent / "launch-with-long-token.sh"
TOKEN_PAGE = "https://hdknr.github.io/claude-code-setup/usage/cruise-long-lived-token/"
AHEAD_OF_TOKEN = ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY")  # 長期トークンより先に使われうる（docstring）


def truthy(value):
    return value is not None and str(value).strip().lower() in ("1", "true", "yes", "on")


def env_scrubbed(env):
    """本体の写し: 子の環境から認証の変数を消すか。`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` が真、
    または `GITHUB_ACTIONS` が真で前者が偽（`0` `false` `no` `off`）でない。"""
    scrub = env.get("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB")
    off = scrub is not None and str(scrub).strip().lower() in ("0", "false", "no", "off")
    return truthy(scrub) or (truthy(env.get("GITHUB_ACTIONS")) and not off)


def check_auth(stack, env, present=False):
    """認証の方式（#584）。**値は出さない**——空かどうかだけを見る。
    居る（`present`）なら、8 時間のトークンは要対処ではなく人が見る——居れば `/login` で戻れる。"""
    label = "認証"
    if env.get("CLAUDECODE") != "1":
        return [(UNKNOWN, label, "Claude Code のセッションの外で回している——セッションがどの認証で起動したかは、その中でしか見えない",
                 "cruise のセッションの中（Bash）で回す")]
    if env_scrubbed(env):
        return [(UNKNOWN, label, "子の環境から認証の変数が消される設定（CLAUDE_CODE_SUBPROCESS_ENV_SCRUB／GITHUB_ACTIONS）——ここからは見えない",
                 "/status の認証の行で見る")]
    ahead = [name for name in AHEAD_OF_TOKEN if str(env.get(name) or "").strip()]
    helper, layer = effective(stack, "apiKeyHelper")
    if isinstance(helper, Unreadable):
        return [unknown_item(label, helper, layer)]
    if helper is not None:
        ahead.append(f"apiKeyHelper（{layer}）")
    if ahead:
        return [(HUMAN, label, ", ".join(ahead) + " がある——長期トークン・対話ログインより先に使われうる",
                 f"どれで認証しているかを /status で見る。長期トークンで回すなら、外して起動口で起動し直す: bash {LAUNCHER}")]
    if str(env.get("CLAUDE_CODE_OAUTH_TOKEN") or "").strip():
        return [(GOOD, label, "長期トークン（CLAUDE_CODE_OAUTH_TOKEN）で起動している——対話ログインの 8 時間のトークンではない",
                 "長期トークンは推論だけに絞られ、Remote Control とそれにつながる通知は使えない見込み"
                 f"（本体の文字列。実測していない。測る表: {TOKEN_PAGE}）")]
    return [(HUMAN if present else ACTION, label,
             "対話ログインの OAuth で起動している——アクセストークンは 8 時間で切れ、更新に失敗すると 401 で止まる",
             f"長期トークンで回すなら: 別の端末で bash {LAUNCHER} --store-token（入れる・入れ替える）→"
             f" このセッションを終えて bash {LAUNCHER} で起動し直す（入れ方: {TOKEN_PAGE}）")]


def human_items(stack):
    rc, layer = effective(stack, "remoteControlAtStartup")
    if isinstance(rc, Unreadable):
        rc_shown = f"remoteControlAtStartup: {layer} の層を読めなかった"
    else:
        rc_shown = f"remoteControlAtStartup: {json.dumps(rc)}（{layer}）" if layer else "remoteControlAtStartup: 未設定"
    return [
        (HUMAN, "モバイルの登録", "/config の通知の欄に「No mobile registered」が出ていないか",
         "通知の試験で届くかを見る（SKILL.md の環境点検の項。返り値は --push-result で判定）"),
        (HUMAN, "Remote Control", f"いまのセッションが繋がっているか（{rc_shown}）",
         "作業中のセッションで /remote-control——claude rc の待ち受けは別のセッションを起こす。"
         "iPhone から 1 行送って、このセッションに届くかを見る"),
        (HUMAN, "電源と蓋", "蓋を閉じない・電源を AC のまま保つ（pmset の値は電源ごと）", ""),
    ]


PUSH_RESULTS = (  # (返り値に含まれる文字列, 判定, 原因, 対処)。判定の順は本体の PushNotification と同じ
    ("mobile push is disabled in /config", ACTION,
     "「Push when Claude decides」（agentPushNotifEnabled）がオフ", "/config でオン"),
    ("this terminal is active", RETRY,
     "使用中と判定された（端末のフォーカスが分かればそれだけで決まり、分からなければ最後の操作から 60 秒以内）",
     "失敗ではない。遅らせて、端末を前面から外し（別のアプリを前面に）、端末にも iPhone にも触らずに送り直す"),
    ("Remote Control inactive", ACTION,
     "いまのセッションが Remote Control につながっていない", "作業中のセッションで /remote-control"),
    ("Mobile push requested", HUMAN,
     "要求しただけ——届いたかはサーバと iPhone で決まる",
     "iPhone に届いたか。届かなければ iPhone の通知の許可・集中モード・アカウントと組織"),
)


def check_push_result(text):
    for needle, status, cause, fix in PUSH_RESULTS:
        if needle in text:
            return [(status, "通知の試験", cause, fix)]
    return [(UNKNOWN, "通知の試験", f"知らない返り値: {text!r}",
             "送り直さない——PushNotification の返り値を言い換えずにそのまま渡し直す。それでも知らないなら版が違う")]


def report_push(items, out=None):
    out = out or sys.stdout
    for status, label, detail, fix in items:
        print(f"[{status}] {label}: {detail}", file=out)
        print(f"        → {fix}", file=out)
    return exit_code(items)


def exit_code(items):
    statuses = {s for s, *_ in items}
    if ACTION in statuses:
        return 1
    if UNKNOWN in statuses or RETRY in statuses:
        return 2
    return 0


DECLARE = re.compile(r"^cruise の操作:(.*)$")
# 宣言の形に届かなかった行（字下げ・箇条書き・引用・全角コロン）——黙って読み飛ばさずに要対処にする
NEAR = re.compile(r"^\s*(?:(?:[-*+>]|\d+[.)])\s*)*cruise\s*の\s*操作")
# フェンスは開いた記号と同じ種類・同じ長さ以上で、後ろに何も無い行でだけ閉じる（CommonMark）。
# `` ` `` の印の後ろに `` ` `` があればインラインコードで、フェンスを開かない
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")


def uncommented(line, in_comment):
    """HTML コメント（`<!--` 〜 `-->`）を除いた行の残りと、行末でコメントの中にいるかを返す。
    コメントの中の宣言は、無効にしたものとして読まない（複数行にまたがっても）。"""
    out = ""
    while True:
        if in_comment:
            close = line.find("-->")
            if close < 0:
                return out, True
            line, in_comment = line[close + 3:], False
        start = line.find("<!--")
        if start < 0:
            return out + line, False
        out, line, in_comment = out + line[:start], line[start + 4:], True


def visible_lines(text):
    """フェンスの中と HTML コメントの中を除いた行（宣言として読む行）。`.claude/dev-loop.md` の宣言はどれもこれで読む。"""
    fence, in_comment = None, False
    for line in text.splitlines():
        f = FENCE.match(line)
        if fence is None:
            line, in_comment = uncommented(line, in_comment)
            f = FENCE.match(line)
            if f and not (f.group(1)[0] == "`" and "`" in f.group(2)):
                fence = f.group(1)
                continue
        if fence is not None:
            if f and f.group(1)[0] == fence[0] and len(f.group(1)) >= len(fence) and not f.group(2).strip():
                fence = None
            continue
        yield line


def read_dev_loop_md(project):
    """`.claude/dev-loop.md` の本文。無ければ空。読めなければ例外（OSError・UnicodeDecodeError）。"""
    try:
        return (Path(project) / ".claude" / "dev-loop.md").read_text(encoding="utf-8-sig")  # BOM を行頭に残さない
    except FileNotFoundError:
        return ""


def declared_commands(project):
    """`.claude/dev-loop.md` の `cruise の操作:` の行。(コマンドの一覧, 項目の一覧)。"""
    path = Path(project) / ".claude" / "dev-loop.md"
    label = "周で使う操作の宣言"
    try:
        text = read_dev_loop_md(project)
    except (OSError, UnicodeDecodeError) as exc:
        return [], [(UNKNOWN, label, f"{path} を読めなかった（{exc}）——宣言した操作を点検できない", "")]
    commands, empty, broken = [], 0, 0
    for line in visible_lines(text):
        m = DECLARE.match(line)
        if not m:
            broken += bool(NEAR.match(line))
            continue
        value = m.group(1).strip()
        if not value:
            empty += 1
        elif value not in commands:
            commands.append(value)
    items = []
    if broken:
        items.append((ACTION, label, f"{path} に書式の崩れた `cruise の操作` の行が {broken} 本ある——読まなかった",
                      "行頭から半角のコロンで `cruise の操作: <コマンド>` と書く（字下げ・箇条書き・全角コロンにしない）"))
    if empty:
        items.append((ACTION, label, f"{path} に値の無い `cruise の操作:` の行が {empty} 本ある",
                      "1 行に 1 コマンドを書く（例: `cruise の操作: gh workflow run infra-apply.yml`）"))
    if commands:
        items.append((GOOD, label, f"{path} から {len(commands)} 件: " + ", ".join(f"`{c}`" for c in commands), ""))
    else:
        items.append((HUMAN, label, f"{path} に `cruise の操作:` の行が無い——既定の操作だけを見た",
                      "本番反映の口など、周で打つ操作を `cruise の操作: <コマンド>` で 1 行 1 コマンド宣言する"))
    return commands, items


def stoppable_items(commands):
    return [(HUMAN, "止まりうる操作",
             "自動モードの分類器と worktree 隔離のガードは settings に現れない——上で良いと出た操作も止まりうる: "
             + ", ".join(f"`{c}`" for c in commands),
             "操作ごとに (a) 許可を足す（/permissions・update-config）(b) その操作だけ利用者が打つ（ledger.py user-ops）"
             "(c) その周を cruise の外に出す、を利用者が選ぶ")]


def parent_location(cwd=None):
    label = "親の起動場所"
    try:
        proc = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
                              cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        return [(UNKNOWN, label, f"git を起動できなかった（{exc}）", "")]
    lines = proc.stdout.split("\n")[:2] if proc.returncode == 0 else []
    if len(lines) != 2 or not all(lines):
        return [(UNKNOWN, label, "git で worktree の中かを判定できなかった", "")]
    git_dir, common = (Path(x) for x in lines)
    if git_dir != common:
        return [(ACTION, label, f"worktree の中から起動している（{git_dir}）——別の worktree・別のリポジトリへの操作が"
                 "隔離のガードに拒まれうる",
                 f"メインの作業ツリー（{common.parent if common.name == '.git' else common}）で、worktree に入らずに起動し直す")]
    return [(GOOD, label, "worktree の外（メインの作業ツリー）", "")]


# ---- cruise の到達できる範囲（#490）----
REACH = "到達"
REACH_SUMMARY = "到達できる範囲"
MERGE_LINE = "マージの線"
JUDGE_MARK = "利用者の判断待ち"  # `note` の先頭の印。found-lines.md が blocked の行に書く印と同じ語（cruise SKILL.md §4 の 4）
ABSENT_MERGE = re.compile(r"^不在の線:\s*マージ\s*=(.*)$")
REFLECT = re.compile(r"^マージの反映:(.*)$")
REFLECT_DOCS, REFLECT_DIST = "ドキュメントのみ", "ドキュメントとプラグインの配布"
CATALOG = (".claude-plugin", "marketplace.json")
MERGE_OPS = ("gh pr merge", "merge-pr.py")  # user_ops にあれば、マージは利用者が打つ（周は await で止まる）
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
PR_NUMBER = re.compile(r"#?([1-9][0-9]*)")
IN_PROGRESS = ("impl", "gate", "pr")
KIND_STATUS = {"merge": GOOD, "user": HUMAN, "stop": ACTION, "unknown": UNKNOWN}
KIND_ORDER = ("stop", "unknown", "user", "merge")  # 依存先のうち、先に挙げる側
NOTE_WIDTH = 80  # note を出すときの長さ（依存する周が多いと同じ note が並ぶ）


def clip(text, width=NOTE_WIDTH):
    text = " ".join(text.split())
    return text if len(text) <= width else text[:width] + "…"


def ledger_module():
    """同じ場所の `ledger.py`（台帳の読み方・場所・印の読み方を 2 箇所に置かない）。"""
    spec = importlib.util.spec_from_file_location("cruise_ledger", Path(__file__).resolve().parent / "ledger.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gh_pr(project, number):
    """`gh pr view` の state・mergeable・files。読めなければ None。"""
    try:
        proc = subprocess.run(["gh", "pr", "view", str(number), "--json", "state,mergeable,files"],
                              cwd=project, capture_output=True, text=True, check=False)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def merge_effect(project, data, present, lg):
    """不在の間に `マージ` の線が効くか。(種類, 項目)。種類は merge・user・stop・unknown。
    **機械で決まる部分だけを見る**——照合（ワークフロー・CLAUDE.md・周の差分）は各周がマージの前に行う。"""
    if present:
        return "user", (HUMAN, MERGE_LINE, "居る cruise——マージは利用者が承認する（`マージ` の線は不在の周だけに効く）", "")
    try:
        lines = list(visible_lines(read_dev_loop_md(project)))
    except (OSError, UnicodeDecodeError) as exc:
        return "unknown", (UNKNOWN, MERGE_LINE, f".claude/dev-loop.md を読めなかった（{exc}）——マージの線が効くかを決められない", "")
    confirmed = data.get("lines", {})
    values = confirmed.get("values", {})
    if "マージ" in values:
        line, origin = values["マージ"], "台帳の確かめた線"
    else:
        decl = [m.group(1).strip() for m in map(ABSENT_MERGE.match, lines) if m]
        line, origin = (decl[0] if len(decl) == 1 else None), "`.claude/dev-loop.md` の `不在の線:`"
    if line != lg.DIST_MERGE:
        now = f"{origin} が `マージ = {line}`" if line else "台帳にも `.claude/dev-loop.md` にも 1 本だけの `マージ` の線が無い"
        return "stop", (ACTION, MERGE_LINE, f"効かない——{now}。不在の周はマージせず PR で止まる",
                        "マージまで進めるなら、離れる前に利用者が `マージ` の線を確かめる（cruise SKILL.md §1・§2）")
    ops = [c for c in data.get("user_ops", {}).get("commands", []) if any(m in c for m in MERGE_OPS)]
    if ops:
        return "stop", (ACTION, MERGE_LINE, "効かない——マージは利用者が打つ操作（台帳の user_ops: "
                        + ", ".join(f"`{c}`" for c in ops) + "）。周はマージの手前で await になる", "")
    reflects = [m.group(1).strip() for m in map(REFLECT.match, lines) if m]
    reflect = reflects[0] if len(reflects) == 1 and reflects[0] in (REFLECT_DOCS, REFLECT_DIST) else None
    caveat = "照合（ワークフロー・CLAUDE.md・周の差分）は各周がマージの前に行う——ここでは見ていない"
    if reflect == REFLECT_DIST:
        if origin == "台帳の確かめた線" and lg.has_dist_mark(confirmed.get("source", "")):
            return "merge", (GOOD, MERGE_LINE, f"効く（宣言 `{REFLECT_DIST}`・台帳の配布の確認あり）。{caveat}", "")
        return "stop", (ACTION, MERGE_LINE, f"効かない——宣言は `{REFLECT_DIST}` だが、{origin} に配布の確認"
                        f"（印 `{lg.DIST_MARK}`）が無い。配布を起こすマージは cruise ごとの確認でだけ効く",
                        "離れる前に、配布を見せて確かめ直す（cruise SKILL.md §1・§2 の 1）")
    try:
        Path(project).joinpath(*CATALOG).stat()
        catalog = True
    except FileNotFoundError:
        catalog = False
    except OSError as exc:
        return "unknown", (UNKNOWN, MERGE_LINE, f"プラグインのカタログの有無を確かめられない（{exc}）", "")
    if catalog:
        return "stop", (ACTION, MERGE_LINE, f"効かない——マージがプラグインのカタログ（{'/'.join(CATALOG)}）を配るのに、"
                        f"`マージの反映:` の宣言が `{REFLECT_DIST}` でない（{'`' + reflect + '`' if reflect else '宣言なし'}）。"
                        "マージは本番反映として扱われ、各周は PR で止まる", "")
    if reflect == REFLECT_DOCS:
        return "merge", (GOOD, MERGE_LINE, f"効く（宣言 `{REFLECT_DOCS}`）。{caveat}", "")
    return "unknown", (UNKNOWN, MERGE_LINE, "`マージの反映:` の宣言が無い（か 2 本以上・知らない値）——マージが反映を起こすかは "
                       "CLAUDE.md・deploy runbook で決まり、このスクリプトは読まない（判定できなければ効かない）", "")


def reach_items(project, name, present, pr_view=None):
    """台帳の済んでいない周ごとに、不在の間の到達（マージまで・PR で止まる・始まらない・止まっている）と理由。読むだけ。"""
    try:
        lg = ledger_module()
        data = lg.load(lg.ledger_path(name, cwd=project))
    except Exception as exc:  # ledger.py の Usage・Unknown と、読み込めなかった ledger.py——どれも「見ていない」
        return [(UNKNOWN, REACH_SUMMARY, f"台帳 {name} を読めなかった（{exc}）——不在の間にどこまで進めるかを見ていない", "")]
    pr_view = pr_view or (lambda n: gh_pr(project, n))
    merge_kind, merge_item = merge_effect(project, data, present, lg)
    rows = {i["number"]: i for i in data["issues"]}

    def pr_number(issue):
        m = PR_NUMBER.fullmatch(issue.get("pr", "").strip())
        return int(m.group(1)) if m else None

    infos = {}
    for i in data["issues"]:
        n = pr_number(i)
        if i["state"] in IN_PROGRESS and n and n not in infos:
            infos[n] = pr_view(n)
    manifests = {}
    for n, info in infos.items():
        if isinstance(info, dict) and info.get("state") == "OPEN":
            for f in info.get("files") or []:
                path = f.get("path", "") if isinstance(f, dict) else ""
                if path.endswith(PLUGIN_MANIFEST):
                    manifests.setdefault(path, set()).add(n)
    contended = {n: (path, sorted(prs)) for path, prs in manifests.items() if len(prs) > 1 for n in prs}

    def merge_tail(prefix):
        return {"merge": ("merge", f"{prefix}マージまで進む見込み（関門・CI が通れば）"),
                "user": ("user", f"{prefix}PR で止まる（マージは利用者が承認する）"),
                "stop": ("stop", f"{prefix}PR で止まる（{MERGE_LINE}が効かない——上の「{MERGE_LINE}」）"),
                "unknown": ("unknown", f"{prefix}PR から先は判定できない（{MERGE_LINE}——上の「{MERGE_LINE}」）")}[merge_kind]

    def own(issue):
        state, note = issue["state"], issue.get("note", "")
        if lg.is_stranded(issue):
            return "stop", "落ちたのにまとめの中で merged のまま（戻すまで、依存する周は始まらない）"
        if state == "await":
            return "stop", f"利用者の操作待ち: {clip(note) or 'note が空'}"
        if state == "blocked":
            return "stop", clip(note) if note.startswith(JUDGE_MARK) else f"止まっている: {clip(note) or 'note が空'}"
        if state in IN_PROGRESS and note.startswith(JUDGE_MARK):
            return "stop", f"マージの前に{clip(note)}"
        n = pr_number(issue)
        if state in IN_PROGRESS and n:
            info = infos.get(n)
            if not isinstance(info, dict):
                return "unknown", f"PR #{n} の状態を読めなかった（gh pr view が失敗した・形が違う）"
            if info.get("state") == "MERGED":
                return "merge", f"PR #{n} はマージ済み（台帳は {state} のまま——親が台帳を直す）"
            if info.get("state") == "CLOSED":
                return "stop", f"PR #{n} は閉じている"
            if info.get("mergeable") == "CONFLICTING":
                return "stop", f"PR #{n} が main と衝突している（不在の周は直しに戻らない）"
            if info.get("mergeable") != "MERGEABLE":
                return "unknown", f"PR #{n} の mergeable が {info.get('mergeable')!r}——数秒おいて回し直す"
            if n in contended:
                path, prs = contended[n]
                return "stop", (f"PR {'・'.join(f'#{p}' for p in prs)} が同じ版のファイル（{path}）を上げる——"
                                "先に 1 本マージされると、残りは版を上げ直すまで止まる（不在の周は直しに戻らない）")
            return merge_tail(f"PR #{n}: ")
        if state == "pr":
            return "unknown", "状態は pr だが台帳に PR の番号が無い——実物で確かめる"
        if state in IN_PROGRESS:
            return merge_tail("続けて PR を作り、")
        return None  # todo は依存で決まる

    memo = {}

    def outcome(number):
        """(種類, 理由, 止まる元の番号)。"""
        if number in memo:
            return memo[number]
        issue = rows[number]
        if issue["state"] == "dropped":
            memo[number] = ("stop", "取り下げ", number)
        elif issue["state"] == "merged" and not lg.is_stranded(issue):
            memo[number] = ("merge", "マージ済み", number)
        elif issue["state"] != "todo":
            kind, why = own(issue)
            memo[number] = (kind, why, number)
        else:
            deps = [(d, outcome(d)) for d in issue["deps"]
                    if not (issue.get("group") and rows[d].get("group") == issue["group"])]
            worst = min((o[0] for _d, o in deps), key=KIND_ORDER.index, default="merge")
            if worst == "merge":
                start = "着手できる" if all(rows[d]["state"] == "merged" for d, _o in deps) else "依存のマージの後に着手"
                kind, why = merge_tail(f"{start}——")
                memo[number] = (kind, why, number)
            else:
                d, (_k, why, root) = next((d, o) for d, o in deps if o[0] == worst)
                lead = {"stop": "始まらない", "unknown": "始まるか判定できない", "user": "依存先のマージを待つ"}[worst]
                memo[number] = (worst, f"{lead}——依存先 #{d}（元: #{root} {why}）" if root != d
                                else f"{lead}——依存先 #{d}: {why}", root)
        return memo[number]

    items = [merge_item]
    groups = {k: [] for k in KIND_ORDER}
    for i in data["issues"]:
        if i["state"] == "dropped" or (i["state"] == "merged" and not lg.is_stranded(i)):
            continue
        kind, why, _root = outcome(i["number"])
        groups[kind].append(i["number"])
        items.append((KIND_STATUS[kind], f"{REACH} #{i['number']}", why, ""))
    names = {"merge": "マージまで進む見込み", "user": "利用者の承認を待つ", "stop": "止まる", "unknown": "判定できない"}
    items.append((HUMAN, REACH_SUMMARY, "; ".join(
        f"{names[k]}: " + (", ".join(f"#{n}" for n in groups[k]) or "なし") for k in ("merge", "user", "stop", "unknown")),
        "止まる周を不在の前に片づけるか（マージ・衝突の解消・判断）、止まったまま離れるかを利用者が決める"))
    return items


def gather(project, commands, flag_path, managed_path, home, platform, flag_note=None, env=None,
           cruise=False, present=False, cwd=None, ledger=None, pr_view=None):
    stack = layers(project, flag_path, managed_path, home, env, flag_note)
    items = []
    declared_items = []
    if cruise:
        declared, declared_items = declared_commands(project)
        commands = tuple(commands) + tuple(c for c in declared if c not in commands)
    for name, path, data in stack:
        if isinstance(data, Unreadable):
            items.append((UNKNOWN, f"設定（{name}）", f"{path} を読めなかった: {data.reason}",
                          "--flag-settings で渡す" if name == "flag" else ""))
    items += declared_items
    items += check_permissions(stack, commands, present)
    if cruise:
        items += stoppable_items(commands)
        items += parent_location(cwd)
        items += (reach_items(project, ledger, present, pr_view) if ledger else
                  [(UNKNOWN, REACH_SUMMARY, "台帳を渡していない——不在の間にどこまで進めるかを見ていない",
                    "`--ledger issue-<親>` を付けて回し直す（cruise SKILL.md §3）")])
    if not present:
        items += check_auto_continue(stack)
        items += check_question_timeout(stack)
        items += check_notifications(home, env)
        items += check_sleep(platform)
        items += human_items(stack)
    items += check_auth(stack, os.environ if env is None else env, present)
    return stack, items


def report(stack, items, out=None):
    out = out or sys.stdout
    print("設定の層（低 → 高）:", file=out)
    for name, path, data in stack:
        state = "無い" if data is None else ("読めない" if isinstance(data, Unreadable) else "在る")
        print(f"  {name:8} {path}  [{state}]", file=out)
    print(file=out)
    for status, label, detail, fix in items:
        print(f"[{status}] {label}: {detail}", file=out)
        if fix:
            print(f"        → {fix}", file=out)
    code = exit_code(items)
    print(file=out)
    print({0: "要対処なし（人が見る項目は上を読む）",
           1: "要対処がある——不在になる前に直す",
           2: "判定できない項目がある"}[code], file=out)
    return code


def default_project():
    """メインの作業ツリーの root。**worktree の root ではない**——gitignore された
    `settings.local.json` はメインの作業ツリーにしか無い。"""
    ok, out = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"])
    if ok and out.strip():
        return Path(out.strip()).parent
    return Path.cwd()


def main(argv=None):
    ap = argparse.ArgumentParser(description="利用者が不在になる前の環境点検（読むだけ）")
    ap.add_argument("--project", type=Path, default=None)
    ap.add_argument("--command", action="append", default=None,
                    help="許可を点検するコマンド（繰り返し可。既定: %s）" % ", ".join(DEFAULT_COMMANDS))
    ap.add_argument("--flag-settings", default=None)
    ap.add_argument("--managed-settings", default=None)
    ap.add_argument("--cruise", action="store_true",
                    help="cruise の起動時: 宣言した操作・止まりうる操作・親の起動場所を足す")
    ap.add_argument("--present", action="store_true",
                    help="利用者が居る: 不在に限る項目（自動継続・質問の待ち・通知・スリープ）を出さない")
    ap.add_argument("--ledger", default=None,
                    help="cruise の台帳の名前（例: issue-474）: 済んでいない周ごとに、不在の間の到達と止まる要因を出す")
    ap.add_argument("--push-result", default=None,
                    help="PushNotification の返り値を判定する（設定は読まない）")
    args = ap.parse_args(argv)
    if args.ledger is not None and not args.cruise:
        ap.error("--ledger は --cruise と一緒にだけ使う")

    if args.push_result is not None:
        return report_push(check_push_result(args.push_result))

    flag_path, flag_note = args.flag_settings, None
    if flag_path is None:
        flag_path, flag_note = find_flag_settings()
    managed = args.managed_settings or MANAGED_DEFAULTS.get(sys.platform)
    stack, items = gather(args.project or default_project(), tuple(args.command or DEFAULT_COMMANDS),
                          flag_path, managed, Path.home(), sys.platform, flag_note,
                          cruise=args.cruise, present=args.present, ledger=args.ledger)
    return report(stack, items)


if __name__ == "__main__":
    sys.exit(main())
