# spec-loop の autopilot（仕様レビューと実現性・コストを不在のまま回す）

spec-loop の **`autopilot`** は、仕様レビュー（`spec-review`）と実現性・コスト（`feasibility`）のループを、
**利用者が席を外しているあいだに 1 単位ずつ**進める入口です（[#789](https://github.com/hdknr/claude-code-setup/issues/789)。
部品は [#848](https://github.com/hdknr/claude-code-setup/issues/848)〜[#850](https://github.com/hdknr/claude-code-setup/issues/850)）。
起動の前に**線**（訊かずに進めてよい範囲）を確かめて台帳に残し、あとは外側のループが `claude -p` で同じ引数を起動し直して進めます。
spec-loop 全体の流れは [spec-loop の流れと Red テスト](spec-loop.md)、スキルごとの説明は [プラグイン一覧の「spec-loop」](index.md#spec-loop) にあります。

!!! warning "規範はプラグインの中にあります"
    このページは**部品の場所と使う順番の案内**です。決まり（線の項目と値・各起動がすること・終了コード・止まる条件の細部・何を守り何を守らないか）は
    [入口のスキルの本文（`skills/autopilot/SKILL.md`）](https://github.com/hdknr/claude-code-setup/blob/main/plugins/spec-loop/skills/autopilot/SKILL.md)と、
    [スクリプトの docstring](https://github.com/hdknr/claude-code-setup/tree/main/plugins/spec-loop/scripts)
    （`autopilot-ledger.py`・`autopilot-check.py`・`autopilot-loop.py`・`check-tlc.py`）を正とします。
    **ここに書き写すと片方だけが古くなる**ので、要点と指し先しか書いていません。

## 部品の一覧

| 部品 | 置き場所（spec-loop の根から） | 役割 |
| --- | --- | --- |
| 入口 | `skills/autopilot/SKILL.md` | `/spec-loop:autopilot <版> [--lines]`。台帳が無ければ線を確かめて権限を点検し、在って `status` が `running` なら次の 1 単位だけを進める（`stopped`・`done` なら単位を進めずに終える） |
| 台帳 | `scripts/autopilot-ledger.py` | 版ごとの台帳（`phase`・周・段と、状態の欄 `status`）の読み書き。外側のループが見る `status`・`progress` もここ |
| 線と権限の点検 | `scripts/autopilot-check.py` | 線の検査（**線の項目と値の一覧はここが正**）と、線から決まる周で使う操作が非対話の権限で通るかの点検 |
| 外側のループ | `scripts/autopilot-loop.py` | `claude -p` を繰り返し起動し、止まったら理由を出して通知する |
| TLC の前提の確かめ | `scripts/check-tlc.py` | 正本の `CLAUDE.md` に書いた TLC の呼び方で TLC が使えるか（[#912](https://github.com/hdknr/claude-code-setup/issues/912)） |
| 長期トークンの起動口 | dev-loop の `skills/dev-loop/scripts/launch-with-long-token.sh` | 対話ログインの 8 時間の期限で止めないよう、キーチェーンの長期トークンで `claude` を起動する（[cruise を長期トークンで起動する](../usage/cruise-long-lived-token.md)） |

**spec-loop の根**は、プラグインで入れていれば `~/.claude/plugins/cache/claude-code-setup/spec-loop/<版>` です。
キャッシュには古い版も残るので、`<版>` は `claude plugin list --json` で読み込まれている版にします
（更新が届かない形と確かめ方は [プラグイン一覧の「更新のしかた」](index.md#updating)）。
**autopilot は素のスキルとしては置けません**——共有の `references/` と `scripts/` を `../../` で指すためです。

## 1. 何をするか

- **1 回の起動で、台帳の次の 1 単位だけを進めて終えます。** 単位は、仕様レビューの周の 1 段（`planner`・`round1`・`fix1`・`round2`・`narrow`・`judge`・`commit`）か、
  feasibility の 1 回です。各単位の中身は `spec-review`・`feasibility` のスキル本文そのもので、判定役・抜ける条件・上限・狭いパスも本文のとおりです——autopilot は規範を軽くしません。
- **台帳は、正本リポジトリのメインの作業ツリーの `.claude/plans/spec-autopilot-v<版>.json` です**（worktree の中から走らせても同じファイルを指します）。
  止まったか済んだかは `status` の 1 欄（`running`・`stopped`・`done`）だけで表します。
- **サインオフのタグを付けない・scaffold を走らせない・Issue を登録しません**——線に依りません。止まる地点の先は、利用者の承認と手作業です。
- 外側のループが無くても、同じ引数（`claude -p "/spec-loop:autopilot <版>"`）で起動し直すたびに 1 単位ずつ進みます。

## 2. 起動時の確認（線と権限）

**台帳が無いときの起動と、`--lines` を付けた起動（`done` の台帳を除く）では、単位を進めずに、線を確かめて権限を点検します。** 利用者が居る対話のセッションで起動します
（`claude -p` では答えが返らないので、台帳を作らずに止まります）。

```
/spec-loop:autopilot <版>            # 台帳が無ければ、線を確かめて台帳を作る
/spec-loop:autopilot <版> --lines    # 線を確かめ直す（プラグインを更新したとき・設定や正本の CLAUDE.md を変えたときも）
```

- **線は、利用者が居れば訊く場面**（上限に達したときに続けるか・判定役が判断を求めたときに推奨で暫定に採るか・commit とマージをどこまでするか・どこで止まるか、など）**を、起動時の答えで置き換えるものです。**
  **線に無い判断に当たった起動は、訊かずに台帳を `stopped` にして止まります。**
  **項目と値の一覧は `autopilot-check.py` の docstring の「線」を、値ごとに各起動がすることは入口のスキル本文の「2. 起動時の確認」を、止まる場面は「3. 1 単位を進める」を正とします。**
  確かめた線は、出所（利用者の確認と日時）と一緒に台帳に残ります。
- **線を書いたら、周で使う操作の許可を点検します**（`autopilot-check.py check <版>`。[#790](https://github.com/hdknr/claude-code-setup/issues/790) では、マージが自動モードの権限で拒まれて止まり、起動前にそれを知る手段がありませんでした）。
  点検する操作は線で決まります（spec-loop のスクリプト・git と PR の操作のどれを点検するかは、線の値で変わります。一覧は `autopilot-check.py` の docstring の「点検する操作」）。
  **止まりうる操作**（自動モードの分類器・worktree 隔離のガードは settings に現れません）は、操作ごとに「許可を足す／`commit` の線を下げる／このまま回して、拒まれたらその段で止まる」から選びます。
  **点検は読むだけで、settings を書き換えません**——許可を足すのは利用者です。
- **点検には TLC の前提も入ります**（下の「4. 前提」）。

点検が何を見て何を見ないか（`Bash` の規則だけを照合する・flag の層はこのセッションのもの、など）は、`autopilot-check.py` の docstring と入口のスキル本文の「権限の点検」を正とします。

## 3. 外側のループで回す { #outer-loop }

確認が済んだら、**正本リポジトリのメインの作業ツリーで、同梱の `autopilot-loop.py` を起動します**（[#850](https://github.com/hdknr/claude-code-setup/issues/850)）。
ループを手で書かないでください——#789 の試作で手書きしたループは、止まったことに気づかず、前進を台帳のファイルのハッシュで見ていたので、
時刻を書き換えるだけの起動を前進と数えて**約 15 時間・約 1,900 回 `claude -p` を空回りさせました**（#790）。

```bash
cd <正本リポジトリのメインの作業ツリー>
python3 <spec-loop の根>/scripts/autopilot-loop.py <版>
```

長期トークンで起動するなら、dev-loop の起動口を `--claude` に渡します（トークンの入れ方は [cruise を長期トークンで起動する](../usage/cruise-long-lived-token.md)）:

```bash
python3 <spec-loop の根>/scripts/autopilot-loop.py <版> \
  --claude "bash <dev-loop の skills/dev-loop>/scripts/launch-with-long-token.sh"
```

- **起動の前に毎回 `autopilot-ledger.py status <版>` を見て、`running`（終了コード 0）のときだけ `claude -p` を起こします。**
  `stopped`・`done`・判定できない台帳では起こさずに止まります。
- **1 回の起動で前進したかは `autopilot-ledger.py progress <版>`**（`phase`・周・段・`commit` だけの 1 行。時刻と止まった理由を含みません）**を前後で比べます。**
- **止まるのは**——`stopped`・`done`・台帳を判定できない・前進なしが続いた・起動の総数の上限・
  同じ状態からの起動の上限（段を行き来するだけの空回り）・`claude` が 0 以外で終わった・使用量の上限の解除が遠すぎるとき。
  止まると、理由を出力の最後の行に出し、macOS なら通知します（`osascript`）。終了コードで理由を分けます。
- **使用量の上限に当たったら、`claude` の失敗にせず、解除の時刻まで待ってから起こし直します。**
- 起こす `claude` には、非対話の起動の決まり（`status` が `running` でなければ何もせずに終える・進めるのは次の 1 単位まで）を `--append-system-prompt` で渡し、
  `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` を置きます（cruise の外側のループと同じ。[#633](https://github.com/hdknr/claude-code-setup/issues/633)）。
- 許可モード・モデルなどは `--` の後ろに足します。**`--permission-mode`・`--allowedTools` で起動するなら、起動時の点検には映りません**——
  別の `--settings` で起動するなら、そのファイルを点検に `--flag-settings` で渡します（上の「2. 起動時の確認」）。

**止まる条件ごとのオプション・既定の回数・終了コード・使用量の上限の読み方と数え方は、`autopilot-loop.py` の docstring を正とします。**
dev-loop の cruise の外側のループ（[オートクルーズの「外から繰り返し起動するとき」](dev-loop-cruise.md#outer-loop)）と同じ形ですが、
同じ状態からの起動の上限と使用量の上限の待ちは autopilot のループだけが持ちます。

## 4. 前提

- **TLC**（[#912](https://github.com/hdknr/claude-code-setup/issues/912)）——TLC は既定で必須の前提です。Java と `tla2tools.jar` を置き、正本リポジトリの `CLAUDE.md` に
  `TLC の呼び方: <コマンド>` の行を書きます。業務フローを一度も形式検査しない案件は `業務フローの形式検査: しない` と書けば点検から外せます
  （宣言しても、`spec-review` が業務フローを対象に選んだ回は TLC を確かめ、無ければその回で止まります——[spec-loop の流れの「形式検査」](spec-loop.md#formal) の表）。
  起動時の点検で確かめ、**各起動は（外す宣言が無ければ）Formal Checker を起こす段（`round1`・`round2`・`narrow`）の始めでも確かめて、使えなければその段に入らずに止まります**
  （`commit` の段と feasibility では確かめません）。書き方は
  [プラグインの README の「前提」](https://github.com/hdknr/claude-code-setup/blob/main/plugins/spec-loop/README.md#前提)と `check-tlc.py` の docstring を、
  形式検査の道具の位置づけは [spec-loop の流れの「形式検査」](spec-loop.md#formal) を見てください。
  権限・ロールを対象に選ぶ回の Alloy は起動時の点検では見ず、その回に確かめて、無ければ止まります。
- **非対話の権限**——上の「2. 起動時の確認」の点検で、要対処と止まりうる操作を片づけておきます。
  **点検は settings の `Bash` の規則だけを照合します**——仕様・Q&A 表の書き込み（`Write`・`Edit`）と判定役の起動（`Agent`）の許可は見ないので、
  `defaultMode` などを自分で確かめます。
- **認証**——対話ログインのアクセストークンは 8 時間で切れます。長く回すなら長期トークンで起動します（上の「3. 外側のループで回す」）。
- **通知**——外側のループは止まると macOS の通知（`osascript`）を出します。**通知が見えるかは確かめていません**（`osascript` の結果も見ません。macOS 以外では出さず、理由は出力にだけ出ます）。
  席を外す端末の通知の設定は、先に自分で確かめておきます。

## 5. 止まったあと

- **台帳を見ます**——`autopilot-ledger.py status <版>` が状態と、止まっていれば理由（`reason`）と利用者に頼むこと（`next`）を出します。
  全体は `autopilot-ledger.py show <版>` です。外側のループの止まった理由は、ループの出力の最後の行と通知にあります。
- **再開は利用者がします**——`next` に書かれたこと（レビュー会で回答をもらう・PR をマージする・許可を足す・TLC を用意する、など）を済ませたら、
  `autopilot-ledger.py set <版> status=running reason= next=` で戻し、外側のループを起動し直します。**autopilot は自分で `stopped` を戻しません。**
- **線を変えるなら**、対話のセッションで `/spec-loop:autopilot <版> --lines` を起動します（線を書き直して点検し直します。`status` は戻しません。
  `done` の台帳では何もしません——台帳の状態ごとの振る舞いは入口のスキル本文の「1. 台帳を見る」）。
- **ログ**——外側のループは起動ごとの標準出力と標準エラーを、台帳の隣の `.claude/plans/spec-autopilot-v<版>-loop/` に残します（消しません。起動ごとに増えます）。
- **周の記録**——振り分けの表（`triage`）と狭いパスの前に控えた本文（`held`）は `.claude/plans/spec-autopilot-v<版>-c<周>-…` に、PR は `commit` の線に応じて作られます。
  各起動の報告には、済ませた単位・線で決めたこと（上限で続けた・暫定で採った Q&A の行・作った PR）・止まった理由が出ます。
- **暫定で採った回答**（`判断が要る` を `推奨を暫定で採る` にしたとき）は Q&A 表に `暫定反映` で残り、確かめるまで scaffold と要求確定のサインオフに進めません。

台帳の欄・`status` の整合・`set` に渡せる鍵は `autopilot-ledger.py` の docstring を、止まる場面と各段の再開のしかたは入口のスキル本文の「3. 1 単位を進める」を正とします。

## 6. 守らないもの

部品の決まりにそれぞれ「守らないもの」があります。要点だけ挙げます:

- **モデルが 1 単位で止まること・線どおりに振る舞うこと**——入口の本文は散文で、振る舞いは機械で見ていません。外側のループは `status` と進捗の欄で止めるだけです。
- **本物の `claude -p` が使用量の上限で何を出すか**——上限の読み方は想定で、本物では確かめていません。読めなかった上限は、待って再開せずに止まります。
- **分類器・ガードが実際にどの操作を止めるか・起動の後に設定が変わること**——権限の点検は起動時の 1 回で、settings だけを照合します。
- **台帳と実物（コミット・PR）が一致しているか**——ループも台帳も、台帳の値だけで決めます。
- **部品をそろえて通しで回した実績**——このページを書いた時点（2026-11）で、部品が入ったあとに autopilot を最後まで回した記録は確かめていません。最初は小さい版で、台帳を見ながら試してください。

一覧は [入口のスキル本文の「守らないもの」](https://github.com/hdknr/claude-code-setup/blob/main/plugins/spec-loop/skills/autopilot/SKILL.md#守らないもの)と、
`autopilot-loop.py`・`autopilot-ledger.py`・`autopilot-check.py` の docstring の「何を守り、何を守らないか」を正とします。

## 関連

- [spec-loop の流れと Red テスト](spec-loop.md)
- [プラグイン一覧 — spec-loop](index.md#spec-loop)
- [dev-loop のオートクルーズ](dev-loop-cruise.md)（同じ形の、dev-loop 側の不在の運用）
- [#789 autopilot](https://github.com/hdknr/claude-code-setup/issues/789)（要件の出所）・[#790](https://github.com/hdknr/claude-code-setup/issues/790)（空回りの記録と直し方）
