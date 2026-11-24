# Issue #1507 — cruise: 利用上限の後に再開タイマーが発火しない限界と、上限から戻る経路を書く（#1401 の 1）

**不在の周**（出所: `/dev-loop:cruise 1508 --absent` の起動・2026-11-24T02:32Z の再開）。利用者には訊かない。親（cruise #1508）から委譲文で受けた子。
依存の #1506（PR #1529。dev-loop 2.24.0）はマージ済み。並行に #1453・#1475・#1515 の周が別の worktree で動く（触らない）。

確かめた線（出所: cruise の確かめた線（台帳 `issue-1508`）。利用者の確認（起動時、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
子はマージしない（親の委譲文）。台帳は書かない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1508`））。
版の上げ方: `dev-loop` を **minor**（2.24.0 → 2.25.0。上限から戻る経路の手順を足す）。並行の周が先に上げていたら、マージ直前の取り込みで main の先端の版から minor で 1 つ上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/references/usage-limit.md` — 新しい参照: 観測したこと（#1401）・確かめていないこと・上限から戻る経路（外側のループを起こし直す・OS の cron で 1 回起こす）・気をつけること
- `plugins/dev-loop/skills/cruise/SKILL.md` — §3 の 4 の見出しの「保険」に限界があることを添え、問いの画面に出す限界に 1 項（観測と、上限から戻る経路の案内。新しい参照を指す）。版
- `docs/plugins/dev-loop-cruise.md` — §5 の限界の箇条に 1 項・「利用上限で止まったとき」に 1 文・「外から繰り返し起動するとき」に「利用上限の後に起こし直す」の段落
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `docs/plans/issue-1507.md` — この計画

触らない:

- `scripts/outer-loop.py`（利用上限を読んで待つ機能は足さない——Issue は案内を求めている。spec-loop の `autopilot-loop.py` は待つが、本物の `claude` の上限の出力の形は測っていないので写さない）
- `check-unattended-env.py` の docstring の「タイマーを保険に張るかは利用者が決める（公開ページ §5）」（指し先の §5 に限界を足すので、指すだけの行は食い違わない）
- `references/parallel.md` の「見張りの終わりの通知で起きなければ、再開タイマーが保険」（背景の作業の完了の通知の話で、利用上限の話ではない）
- `docs/usage/usage-limit-stop-hook.md`（自動継続を数える手順で、cruise の戻り方ではない）
- #1401 のほかの項

依存の追加・更新: なし
仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）

同じことを述べている箇所の数: 4（原本の `references/usage-limit.md` と、指す側の cruise の `SKILL.md` §3 の 4 の 1 項、公開ページの §5 の 1 項と「外から繰り返し起動するとき」の段落。「利用上限で止まったとき」の 1 文は §5 を指すだけ）。
分けない理由: 観測の範囲と手順の原本は `references/usage-limit.md` の 1 か所で、`SKILL.md` と公開ページは要約して指す。Issue が `SKILL.md` の 3 の 4 と公開ページの両方に限界を書くことを求めている。指し先の節の名前は `check-skill-pointers.py` が照合する。

## デプロイ経路

main へのマージで、プラグインの配布（`marketplace.json` の版）と GitHub Pages（公開ページと計画ファイル）。`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`。子はマージしない。

## 受入基準

Issue の受入基準: (a) 問いの画面に出す限界に、上の観測が入っている（観測の範囲と確かめていないことを書き分ける）。(b) 上限から戻る経路の手順が `SKILL.md` か `references/` にあり、`outer-loop.py` の実際の引数と合っている。

不変条件 × 破りうる経路（入口: cruise の親が読む `SKILL.md` §3 の 4（新規の起動の問いの画面）と、そこから指す `references/usage-limit.md`・利用者が読む公開ページ（§5・「利用上限で止まったとき」・「外から繰り返し起動するとき」）・利用者が打つ `outer-loop.py` と crontab の行・再開した親（`/clear` の後・`--timer` の起動）・居る cruise と不在の cruise）:

| # | 不変条件 | 経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| 1 | `SKILL.md` §3 の 4 の「問いの画面に出す限界」に、利用上限の後にタイマーが発火しなかった観測が入り、1 例であること・原因を確かめていないことが書いてある（断定しない） | `SKILL.md` §3 の 4 | 読む |
| 2 | 観測の範囲（何を見たか: 時刻・発火の欠け・`CronList` にジョブが残っていた・次の発火）と、確かめていないこと（原因・いつもか・次の発火を何が起こしたか）が分けて書いてあり、#1401 の記録と食い違わない | `references/usage-limit.md`・`SKILL.md`・公開ページ | #1401 の本文と読み比べ |
| 3 | 上限から戻る経路（外側のループを起こし直す・OS の cron で起こす）の手順が `references/` にあり、`SKILL.md` §3 の 4 から指されて、親が問いの画面で案内する | `SKILL.md`・`references/usage-limit.md` | 読む・`check-skill-pointers.py` |
| 4 | 手順の `outer-loop.py` の引数・振る舞い（位置引数の親の番号・`--absent`・`--claude`・`--` の後ろの足す引数・`--max-stalls` の既定 2・`--max-total-usd` を起こし直すと 0 から数える・`status` が 0 のときだけ起こす・止まるたびに通知する・上限を読まない・終了コード 6・8）が、`outer-loop.py --help` と docstring と実装に合っている | `references/usage-limit.md`・公開ページ | `--help`・docstring・実装と読み比べ |
| 5 | cron の行の例が、それ自体で誤った動作をさせない——1 回きり・絶対パス・`lockf -t 0` で 2 本並ばない・`claude` を直に起こさず外側のループを起こす。確かめた範囲（`lockf` の重なりの止め方だけ）と確かめていないこと（cron からの起動・認証）が書き分けてある | `references/usage-limit.md` | `lockf` を手元で当てた結果・読む |
| 6 | 同じ台帳を回す親が 2 体にならない注意がある——対話のセッションのタイマーと外側のループ・cron が重なりうること | `references/usage-limit.md`・公開ページ | 読む（`outer-loop.py` の「守らない」と食い違わない） |
| 7 | 既存の §3 の 4 の決まり（張る・張らない・`--timer` の起動で訊かない・張り直し）と、公開ページの §5・「`claude -p` で外から回すとき」と食い違わない | `SKILL.md`・公開ページ | 読み比べ |
| 8 | 公開ページの記述が原本（`references/usage-limit.md`）と食い違わない | 公開ページ | 読み比べ |
| 9 | 版が 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本）で揃って上がる | 版 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| 10 | 歯止め全部（`check-all.py`）が緑 | 全体 | `run-serial.py` 越しの `check-all.py` と PR 側の CI |

必須要件の掛け算: 受入基準を両方の関門（Verifier・`/code-review`）に × 2 パス（1 パス目・2 パス目。1 パス目の指摘対応が 0 行なら 2 パス目は該当なし）= 4 つの受け渡し。2 パス目で直した行があれば狭いパスにも受入基準をまるごと渡す。

証明できないもの（未証明）: 案内した経路で、実際に上限の後に cruise が戻ること——利用上限を狙って起こせず、cron から本物の `claude` を起こすことも利用者の crontab を書き換えるのでこの周ではしない。受入基準は文面と `outer-loop.py` との整合で、戻ることは主張しない（`references/usage-limit.md` に「cron から実際に起こしたことは無い」と書いた）。
生成物: なし（`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` の節構造に依るが、この周は dev-loop の `SKILL.md` の版の行だけを変える——`skill-metrics.py --check` で確かめる）。
プロパティテスト: なし（散文の決まりの周で、往復・冪等性・数値の境界を持つ実装が無い）
差分テスト: なし（振る舞いを変えない周ではない——限界と案内を足す）

## 未解決の判断・確認待ち

- 仕様の穴: なし。Issue の「OS の cron から、解除の時刻の後に起こし直す」を、cron に `outer-loop.py` を 1 回だけ起こさせる形にした——`claude` を直に起こすと `status` を見ずに起こし、繰り返しにすると `outer-loop.py` が止まるたびに通知するので同じ通知が並ぶ。新しい判断ではなく、既存の `outer-loop.py` の振る舞いから決まる。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1507-cron-after-usage-limit`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1507`・
  起点 `59b5db8b`・base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `59b5db8ba4db19fe2dd891b181ba18ab11871280`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目に渡した（Verifier・/code-review。成果物 `da7d0910`）。1 パス目の指摘対応の起点: `da7d091094f73d98ac691846729aa34906f41f00`
  - Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/f6308801-996d-4682-8ce3-f3ee617842d3/scratchpad/gate-1507-verifier-1-20261124T163136Z.md`
  - /code-review 1 パス目（high）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/f6308801-996d-4682-8ce3-f3ee617842d3/scratchpad/gate-1507-code-review-1-20261124T163136Z.md`
  - 結果: Verifier 1 パス目（166 行を読んだと報告——`wc -l` は 166）反証 2 件（V1-1・V1-2）。/code-review 1 パス目 指摘 7 件（CR1-1〜CR1-7）。
  - 1 パス目の指摘対応: 直す 8 件（下の表。V1-1 と CR1-6 は同じ直し）。範囲は広げていない（同じファイルの中）。 コミット `5188bd184f10275ae6c084375e7abd247bf8e9fd`。
- 割り目（手順 6）: 割らない（cruise の周）
- 2 パス目に渡した（Verifier・/code-review。成果物 `5188bd184f10275ae6c084375e7abd247bf8e9fd`）。
  - Verifier 2 パス目: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/f6308801-996d-4682-8ce3-f3ee617842d3/scratchpad/gate-1507-verifier-2-20261124T163758Z.md`
  - /code-review 2 パス目（high）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/f6308801-996d-4682-8ce3-f3ee617842d3/scratchpad/gate-1507-code-review-2-20261124T163758Z.md`
  - 結果: Verifier 2 パス目（191 行を読んだと報告——`wc -l` は 191）反証 1 件（V2-A）。/code-review 2 パス目 指摘 7 件（CR2-1〜CR2-7）。
  - 2 パス目の指摘対応: 狭いパスの起点 `c9784f2c889aaf1b85524ff99f96f77c243955cd`（指摘対応に入る前に書いた）。終点 `baeef67c4b6f340dd4418363d4a1c86e86708db5`。直す 7 件・残課題 1 件（下の表）。範囲は広げていない。
- 狭いパス（sonnet。起点 `c9784f2c` → 終点 `baeef67c`）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/f6308801-996d-4682-8ce3-f3ee617842d3/scratchpad/gate-1507-narrow-1-20261124T164339Z.md`
  - 結果（219 行を読んだと報告——`wc -l` は 219）: 反証 1 件（NP-1。軽微）。Verifier が設計した変異 3 本——引用符を外す・`{ }` を外すは赤（旧い挙動を再現）、`export` を落とすは当てていない。素通りなし。
- PR #1532。PR 側の CI: 16 pass・1 skipping（deploy）。外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い。`external-reviews.py` が 3）。
- マージ前の判断（線 `マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`）:
  - NP-1（「Remote Control などで手が届く」は、長期トークンで起動すると Remote Control が使えないこと（cruise の `SKILL.md` §3 の 3）と緊張する）: 振り分け「記録だけ」——「など」の例で、対話ログインの認証なら Remote Control は使え、受入基準を破らず、この周が持ち込んだ後退でもない（周の前は経路の案内そのものが無かった）。推奨「マージする」。
- 交絡を潰した手順（2 パス目の指摘対応）: `{ export PATH='…空白を含む…' && cd <無いディレクトリ> && …; } >> log 2>&1` を `env -i` の `sh` で当て、`cd` の失敗がログに残り、空白を含む `PATH` が `python3` の子に渡ることを見た（失敗する側と渡る側の両方）。
- 交絡を潰した手順（指摘対応）: cron の行の `PATH` の置き方を `env -i` の `sh` で当てた——環境に無い `PATH` を `PATH=… &&` で置くと `python3` の子に渡らず（KeyError）、`export PATH=… &&` なら渡った。環境に `PATH` がある形（cron と同じ）では `export` 無しでも渡った。例は `export` の形にした。
- 交絡を潰した手順: `lockf -t 0` の重なりの止め方を手元で当てた（1 本目が握っているあいだの 2 本目が 75 で断られ、離した後の 3 本目は走った——断る側と走る側の両方を見た）。ほかに実験なし。

```dev-loop-gates
周の base: 59b5db8ba4db19fe2dd891b181ba18ab11871280
関門: Verifier 1 da7d091094f73d98ac691846729aa34906f41f00 反証=2
関門: /code-review 1 da7d091094f73d98ac691846729aa34906f41f00 指摘=7
関門: Verifier 2 5188bd184f10275ae6c084375e7abd247bf8e9fd 反証=1
関門: /code-review 2 5188bd184f10275ae6c084375e7abd247bf8e9fd 指摘=7
関門: 狭いパス c9784f2c889aaf1b85524ff99f96f77c243955cd baeef67c4b6f340dd4418363d4a1c86e86708db5 反証=1
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
受入基準: 8 満たす
受入基準: 9 満たす
受入基準: 10 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

- `outer-loop.py` に利用上限を読んで解除の時刻まで待つ機能を足さない（決着: 採らない。理由: Issue は案内を求めている。本物の `claude -p` の上限の出力の形は測っておらず、spec-loop の `autopilot-loop.py` もその形を測っていないと書いている）。
- cron の行を繰り返しにしない（決着: 1 回きり。理由: `outer-loop.py` は止まるたびに通知し、上限が解けていなければ起動のたびに止まる）。
- cron から起こした `claude` の認証・cron からの起動そのものは確かめない（決着: 未証明として書く。理由: 利用者の crontab を書き換え、本物の `claude` を起こすので、この周ではしない）。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-1・CR1-6: 「解除の時刻を過ぎても約 17 回分」は、17 回が解除の前の 4 回を含むのに解除の後だけと読める | 示せる——#1401 の「2am の解除後も含めて 00:07〜08:07 の約 17 回分」と文面 | 2 | 直す——「解除の時刻の後も含めて約 17 回分（00:07〜08:07）」・参照は前 4 回と後 13 回に分けた |
| V1-2: cron の `PATH` に `node` が無いと `claude` が起きない・`osascript` の通知が出ない点が無い | 示せる——cron の `PATH` が短いこと（CR1-4 と同じ根） | 5 | 直す——CR1-4 と同じ直し（`export PATH=`）。通知が出るかは確かめていないことに足した |
| CR1-1: 上限で止まる経路に、`--max-total-usd` を渡したときの 12 が抜けている。「上限の扱いは docstring に無い」は docstring の「守らない」と食い違う | 示せる——関門が偽の `claude` で `--max-total-usd 5` なら 12・なしなら 6 を実測。docstring の「守らない」の文 | 4 | 直す——12 を足し、docstring の「守らない」の文を書いた（参照と公開ページ） |
| CR1-2: 対話のセッションで回す cruise に離れる前に cron を用意すると、タイマーか自動継続で戻った親と 2 体になる——案内自体がその形を作る | 示せる——#1401 の 08:25 の発火と、`lockf` が対話の親を見ないこと（`outer-loop.py` の「守らない」） | 6 | 直す——経路は外側のループで起こす形だけで、対話のセッションを終えてから使う、と原本・`SKILL.md`・公開ページに書いた |
| CR1-3: 手で起こすループの例に `lockf` が無く、cron のループと並ぶ | 示せる——例の行 | 6 | 直す——手の例にも同じロックのファイルを通した |
| CR1-4: cron の環境が貧しい（`gh`・`node`・rc の変数）のに、行のパスを絶対パスにする注意で終わる | 示せる——cron の `PATH` と `outer-loop.py` が環境をそのまま渡すこと | 5 | 直す——行の先頭に `export PATH=`、rc の変数も置く、と書いた |
| CR1-5: その時刻に Mac が眠っていると 1 回きりの cron は起こさない | 示せる——cron は逃した時刻を走らせない | 5 | 直す——注意に足し、スリープは起動時の点検の項を指した |
| CR1-7: 例の `/usr/bin/python3` は Command Line Tools の shim のことがある | 示せる——例の行 | 5 | 直す——`command -v python3` で調べた絶対パスにした |

- 効いた行: V-02
- 効いた行: V-07
- 効いた行: R-02
- 効いた行: なし
- 効いた行: なし
- 効いた行: R-02
- 効いた行: なし
- 効いた行: なし

### 2 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-A: cron の行の `export PATH=<…>` は空白を含む `PATH` で壊れ、後ろが走らない | 示せる——関門が `sh -c 'export PATH=/usr/bin:/Applications/Visual Studio Code.app/bin && echo ok'` で rc=1 を実測 | 5 | 直す——値を引用符で囲み、`%` の注意を足した |
| CR2-1: 公開ページの外側のループの例に `lockf` が無く、cron のループと並びうる | 示せる——公開ページの例の行 | 6・8 | 直す——例の直後に、cron と併せるなら同じロックのファイルで `lockf` を通す、と書いた |
| CR2-2: 外側のループも上限で止まって通知するだけで、離れたまま戻すには通知を受けて cron を足すことが要るのに、離れる前に用意すれば戻るように読める | 示せる——原本の 2 の前提（上限を知った後に足す）と冒頭の文面 | 3 | 直す——原本・`SKILL.md`・公開ページに、連絡がつかなければ戻らないと書いた |
| CR2-3: 止まり方の 8・12・6 が全部のように読める（3・7・戻らない起動がある） | 示せる——`outer-loop.py` の終了コード表と「守らない」の 1 回の起動の長さ | 4 | 直す——「たとえば」・全部ではない・3・7・戻らない場合を足した |
| CR2-4: `>> log 2>&1` が最後のコマンドにしか掛からず、`cd` の失敗がログに残らない | 示せる——`sh` の文法。直した形を `env -i` の `sh` で当て、`cd` の失敗がログに残ることを見た | 5 | 直す——行を `{ …; }` で括った |
| CR2-5: 「§5 の再開」は `SKILL.md` の §5（割って続ける）を指してしまう | 示せる——`SKILL.md` の §5 の見出し | 3 | 直す——`SKILL.md` §1 の再開を指した |
| CR2-6: cron がフルディスクアクセスの外で走り、保護されたフォルダの下の作業ツリーを読めないことが確かめていないことに無い | 示せない——cron から起こしていない | 無し | 残課題（PR コメントに書く） |
| CR2-7: 問いの画面でタイマーを推したまま、この経路は「タイマーと併用しない」と言い、どちらを取るか決まらない | 示せる——同じ項の推奨と新しい項 | 7 | 直す——この経路を取るならタイマーは張らない、推奨は対話のセッションで回す場合のもので、どちらを取るかは利用者が決める、と書いた |

- 効いた行: V-05
- 効いた行: R-02
- 効いた行: R-02
- 効いた行: R-02
- 効いた行: R-02
- 効いた行: なし
- 効いた行: R-02
- 効いた行: なし

### 狭いパスの採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| NP-1: 「Remote Control などで手が届く」は、長期トークンで起動すると Remote Control が使えないことと緊張する | 示せない——長期トークンで起動した外側のループの利用者が通知を受けられないかは当てていない（「など」の例） | 無し | 人間が決める（推奨: マージする。記録だけ） |

- 効いた行: V-02

## 手順 8 の記録

- この周の起票: 0 件（不在の cruise の周。周の途中の課題で直すに入った行は無く、起票の候補は無い）
