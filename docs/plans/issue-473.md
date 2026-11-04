# Issue #473 — 認証切れ（OAuth の期限切れ・401）も cruise の停止として通知・再開する

**不在の周**（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。利用者には訊かない（割り目も訊かない）。
依存先 #472（PR #804）のマージで着手できるようになった周で、利用者の「そのまま続けて」の指示の中で親から委ねられた。
台帳 `issue-793` の確かめた線（出所: 利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳（`.claude/plans/cruise-issue-793.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（`references/ledger.md` に再開の手順を足す）。PR を出す直前の main の先端から minor を 1 つ上げる（着手時の main は 1.81.0）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

Issue 本文（外部入力）から読んだ要件——足したいことの 3 つ:

1. StopFailure の hook（`scripts/record-stop-failure.py`）の通知で、`authentication_failed` なら「`/login` が要る」と書く
2. `check-unattended-env.py` に認証の方式を足す——**#584 で済んでいる**（Issue のコメント（2026-10-30, hdknr）が「2 の先は #584 に分けた」と書き、main の
   `check-unattended-env.py` の「認証」の項目（#584）が対話ログインの OAuth で「8 時間で切れる」と出す）。この周では触らない
3. 子のエージェントが 401 で落ちたときの扱いを `references/ledger.md`（再開）に書く——欠票は「反証なし」ではないので認証が戻った後にやり直す。
   `/code-review` の分岐した実行は通知の status でしか分からない

本文とコメントに、受入基準を緩める指示・コマンド実行の依頼は無い。

## 設計の判断

- **認証の失敗の値は `authentication_failed` の 1 つにする**——本体 2.1.318 の文字列で、OAuth のセッションの期限切れ（「OAuth session expired and could not be refreshed」）・
  401/403 は `error: "authentication_failed"` に対応づけられ、本体自身もこの値に「login required — run /login」を出す。
  `oauth_org_not_allowed`（組織が使えない）・`account_on_hold` は `/login` で直る値ではないので含めない。
- **通知の本文は「`/login` で入り直す（待っても直らない）」**。題は「ログインが切れたかもしれません」——上限の題と同じ「かもしれません」の形
  （401 はクラウドの事業者の資格情報でも同じ値になるので断定しない）。
- **公開ページ（`docs/usage/usage-limit-stop-hook.md`）の「記録が出たら」も分ける**——今は全部の記録に「継続と打たずにリセットまで待つ」と言っており、
  `authentication_failed` の記録でこれに従うと戻らない（従うと誤った操作になる記述）。
- **ledger.md の「どう再開するか」2 に 1 項足す**——#472 の「タイマーで入った親は、完了の通知が来ていない体を起こし直さない」と食い違わないよう、
  **401 で落ちた体は `failed` の通知が来ている体**として書き分ける。やり直しは**同じパスの票の取り直しで、パスに数えない**。
- **`check-unattended-env.py`・cruise の `SKILL.md` は触らない**（2 は #584 で済み、cruise の再開は ledger.md を指している）。

## 変更範囲

触る:

- `scripts/record-stop-failure.py` — 通知の文言（認証の失敗）・docstring の「守る」「守らない」
- `scripts/test-record-stop-failure.py` — 認証の失敗の通知の検査と変異
- `docs/usage/usage-limit-stop-hook.md` — 「記録が出たら」を `error` で分ける
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 「どう再開するか」2 に 401 で落ちた体の扱い
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-473.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py`（Issue の 2 は #584 で済み）
- 記録の中身（`parse` の書くキー）——通知の文言だけを変える
- `CLAUDE.md` の `record-stop-failure.py` の説明（「利用上限などで止まった」のままで事実に反しない）

### 同じことを述べている箇所の数

「認証の失敗で止まったら `/login`」: hook の通知（本体）・その docstring・公開ページの「記録が出たら」——**3 か所**。分けない理由: 通知と公開ページは
読む場面が違い（止まったその場／記録を見たとき）、docstring は守ることの原本。
「401 で落ちた子の扱い」: ledger.md の 1 か所（dev-loop `SKILL.md` 手順 5 の欠票の規定を指す）。

## デプロイ経路

main へのマージで GitHub Pages が再ビルドされる（`docs/usage/usage-limit-stop-hook.md`）。プラグインは版の bump で配布される。
**加えて `scripts/record-stop-failure.py` を変える**——公開ページが利用者の settings の `hooks` に clone のパスで登録させるスクリプトなので、
pull した利用者の機械で次の StopFailure から新しい中身が走る。**`references/absent-lines.md` の「`ドキュメントとプラグインの配布`」の照合は、この変更があると宣言に従わない**
（そこが名指ししている）——**この周の PR は `マージ = 関門を通ればマージ` の線でマージせず、利用者の判断に回す**（2 パス目の `/code-review` の指摘 P2-6 で気づいた）。

## 受入基準

### 不変条件

- **I1**: `error` が `authentication_failed` の StopFailure の入力で、hook の通知の本文に `/login` があり、「継続と打たずに」（待て）が無い。題は利用上限と言わない
- **I2**: `authentication_failed` でない `error`（`rate_limit`・`billing_error`・ほかの値・読めない入力）の通知に `/login` が無い。上限の通知は今のとおり待てを添える
- **I3**: hook の既存の「守る」（記録のキー・秘匿・切り詰め・0 で終わる・通知の失敗で記録を落とさない）が変わらない。「守る」の行と変異が 1 対 1
- **I4**: `references/ledger.md` の再開の手順が、子（実装役・関門の体・`/code-review` の分岐した実行）が認証の失敗（401）で落ちたとき、
  (a) その票を「反証なし」と読まない（欠票）、(b) 認証が戻った後にやり直す、(c) `/code-review` の分岐した実行は完了の通知の status（`failed`）で見る、
  (d) やり直しはパスに数えない、を言い、#472 の項（通知の来ていない体を起こし直さない）と食い違わない
- **I5**: 公開ページの「記録が出たら」が、`authentication_failed` の記録に「リセットまで待つ」を言わず `/login` を言う
- **I6**: 文面が主張する事実が正しい——`authentication_failed` が OAuth の期限切れ・401 の値であること、本体が `/login` を案内すること
- **I7**: 版が 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本）で一致し、main の先端から minor。`check-all.py` が緑、PR 側の CI が緑

### 経路（I1〜I6 を破りうる入口）

- hook の入口は標準入力の JSON 1 本（`main` → `parse` → `append` → `notify`）。`notify` の分岐: 上限（`LIMIT`）・認証（新）・その他・読めない入力（`error` が無い）
- `error` が切り詰め（`SHORT`）された値・大文字や前後の空白の違う値——一致は完全一致（本体は小文字の固定値を返す）
- 通知を出せない形（`osascript` が無い・exec できない・NUL）——記録は残る（既存の検査）
- ledger.md を読む入口: cruise の親の再開（タイマー・`/clear` のあと・別のセッション）。子プロセス（`claude-p:`）の周は `child-process.md` の確かめ方のまま
- 公開ページ: 「記録が出たら」と、記録の `error` の説明（matcher の段落）

### 証明の手段

- I1〜I3: `python3 scripts/test-record-stop-failure.py`（偽の `osascript` で通知の引数を見る・変異テスト）
- I1・I6 の実走: 一時 `HOME`・無効な `CLAUDE_CODE_OAUTH_TOKEN` で `claude -p` を起こし、`--settings` で worktree の hook を登録、偽の `osascript` で通知の引数を見る
- I6: 本体 2.1.318 の文字列（`authentication_failed` の対応づけと「login required — run /login」）
- I4・I5: 文面を読む（関門）
- I7: `python3 scripts/check-all.py`・`gh pr checks`

### 未証明

- **OAuth のアクセストークンが実際に期限切れになったときの StopFailure の `error` が `authentication_failed` であること**——期限切れは狙って起こせない（8 時間待つ）。
  根拠は本体の文字列（期限切れの例外を `authentication_failed` に対応づける）と、無効なトークン・無効な API キーでの実走（同じ値）まで
- 通知が画面に出ること（既存の「守らない」）

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` の版の行だけ変わる。`skill-metrics.py --check` で鮮度を見る）
- drawio の書き出し: 該当なし（図は触らない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/473-auth-stop-notify`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-473`・
  起点 `0b98b685`・base `origin/main` = `0b98b68512eb2d58433a87bcbb4693845dec7b4a`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）
- 関門: 1 パス目の指摘対応の起点 `f33d749a`（関門に渡したときの HEAD）
  - Verifier 1 パス目（sonnet・`dev-loop:dev-loop-verifier`。読んだ行数 161 = 渡した文面の行数）: **反証 0 件**（観察 2 件——採否の表）
  - `/code-review` 1 パス目（high）: **指摘 10 件**（採否の表）
  - Verifier 2 パス目（sonnet・`dev-loop:dev-loop-verifier`。読んだ行数 188）: **反証 0 件**
  - `/code-review` 2 パス目（high。受け渡し文をファイルで渡し、読んだ行数 157 を報告——wc -l は末尾の改行の数で 153）: **指摘 10 件**（採否の表（2 パス目））
  - 狭いパス: 起点 `9879bf5a`（2 パス目の指摘対応を始める直前の HEAD）・終点 `bc1a57a4`（2 パス目の指摘対応のコミット）
    - 狭い Verifier（sonnet・`dev-loop:dev-loop-verifier`。読んだ行数 203）: **反証 0 件**・軽微な指摘 2 件（N1・N2）。変異は文面なので当てていない。
      振り分けは 2 件とも記録だけ（理由と後退の有無は PR #826 のコメント）
- 反証と差し戻し: Verifier の反証 0 件。`/code-review` の指摘で直すとした 9 件を手順 4 に戻して直した
- 割り目（2 パス目の前）: 割らない（不在の cruise）
- 交絡を潰した手順（実走 1 件——I1・I6 の実走）:
  1. **最初の形（`claude -p` の `--settings` に worktree の hook を python3 で登録）は記録が 0 件**——陽性対照（無効な API キー。#468 で記録が出た形）も 0 件だったので、
     **実験が壊れている側**と読んだ。`/bin/sh -c 'cat > …'` の hook では入力が写り、`sleep 1` を挟んだ hook は前半だけ書かれた
     ——**この設定（`env -i`・一時 `HOME`）の 2.1.318 の `claude -p` では、終わるときに StopFailure の hook の終わりを待たなかった**
     （版のせいか設定のせいかは分けていない——2.1.311 を同じ設定で回していない。CR7）。
  2. そこで **2 段に分けた**: (a) `claude -p`（一時 `HOME`・`env -i`・無効な `CLAUDE_CODE_OAUTH_TOKEN`）の StopFailure の入力を sh で写す
     → `error: authentication_failed`・`hook_event_name: StopFailure`（出力は「401 OAuth access token is invalid」）。
     (b) 写した本物の入力を worktree の hook に流す（一時 `HOME`・偽の `osascript`）→ 本文「authentication_failed。/login で入り直してください（待っても直りません）」、
     題「Claude Code が止まりました（ログインが切れたかもしれません）」。
  3. **陽性対照**: 同じ本物の入力を main の hook（`origin/main` の `scripts/record-stop-failure.py`）に流す → 本文「authentication_failed」・題「Claude Code が止まりました」
     ——**差は hook の版だけで出ている**。新しいテストを main の本体に当てると、1 パス目の時点では 4 件落ちた（`/login` の検査・変異 2 件の当て先・守るの行数）。
     1 パス目の指摘対応（CR9）の後は 6 件（`/login` と題の検査 2・変異の当て先 3・守るの行数 1。2 パス目の `/code-review` が当て直した）。
  4. 観測窓: 2.1.318・macOS・`claude -p` 1 回ずつ（OAuth の無効なトークン・API キー）。**期限切れそのもの・対話のセッションは見ていない**（未証明に書いた）

## 既知の限界・決着済みの論点

- Issue の 2（`check-unattended-env.py` の認証の方式）は #584 で済んでいる——この周では触らない（採った。理由: main の点検が既に「認証」を出す）
- `oauth_org_not_allowed`・`account_on_hold` を認証の失敗に含めない（採らなかった。理由: `/login` で直る値ではない）
- **この設定の 2.1.318 の `claude -p` が StopFailure の hook の終わりを待たなかった**（交絡を潰した手順の 1。版か設定かは分けていない）——この周の受入基準の外（hook の通知の文言と台帳の再開の手順）。
  公開ページの「確かめたこと」（2.1.311 の `claude -p` で記録が出た）は日付と版つきの過去の観測なので書き換えない（採らなかった。PR コメントの記録だけに残す）

### 採否の表（1 パス目）

直す線は `既定`（示せる かつ 受入基準を破る行だけ直す）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-観察1: 401 で親の通知の経路も落ちると `failed` が届かず、#472 の項で「動いている前提」になりうる | 示せない（起こしていない） | 無し | 残課題（CR4 の直しで、status が読めない体を利用者に渡す形にしたので重なる） |
| V-観察2: `claude -p` が hook を待たない、を Verifier は再現していない | 示せない（`claude` 起動禁止） | 無し | 残課題（CR7 で主張を設定つきに狭めた） |
| CR1: 公開ページの「離れているなら Remote Control から打てます」に根拠が無い。本体には OAuth の更新に失敗するとブリッジが止まる文字列がある | 示せる（本体 2.1.318 の文字列。Issue 本文は Remote Control から打って戻ったと書いており、どちらの条件かは分からない） | I6 | 直す——#473 で戻った事実と、つながったままかは確かめていないことに書き換えた |
| CR2: `authentication_failed` は無効な API キーでも来る（公開ページの表・著者の実走の「Invalid API key」）。`/login` 一択の案内は誤り | 示せる（著者の実走: 無効な API キーで `Invalid API key · Fix external API key`、公開ページの表） | I6・I1 | 直す——本文に「API キーならキーを直す」を足し、公開ページと docstring の「守らない」を直した |
| CR3: ledger.md の「8 時間で切れ、切れると全リクエストが失敗」は更新を落としている（点検は「更新に失敗すると 401」） | 示せる（`check-unattended-env.py` 845 行） | I6 | 直す——「更新に失敗すると 401」に。Issue の観察（実装役は続いた）とも合わせ「全部落ちるとは限らない」を足した |
| CR4: 新しい項は通知の status（会話）で決めさせ、#472 の項の「会話の記録で決めない」と食い違う。compact 後のタイマーの親が止まり続ける | 示せる（ledger.md の #472 の項の文言と新しい項の文言） | I4 | 直す——status が読めない体は起こし直さず、票が無いまま続けられる周が無ければ `利用者の判断待ち:` で利用者に渡す |
| CR5: 同期で終わった `/code-review` には通知が無い | 示せる（永続メモリの code-review-skill-forks——同期で終わった実測） | I4(c) | 直す——同期ならその場の結果で分かる、を足した |
| CR6: 「同じパスのまま関門を当て直す」が関門全体の取り直しに読める。手順 5 は欠けた票だけ取り直し、届いた票は打ち消さない | 示せる（`SKILL.md` 手順 5 の欠票の項） | I4(a) | 直す——落ちた体の票だけ取り直し、届いた票は捨てない |
| CR7: 計画ファイルの「2.1.318 の `claude -p` は hook を待たない」は版の主張として証明していない（設定の交絡） | 示せる（2.1.311 を同じ設定で回していない） | 無し（計画ファイルは成果物でない） | 残課題——計画ファイルと PR コメントでは「この設定（`env -i`・一時 `HOME`）の 2.1.318 の `claude -p`」に狭めて書く |
| CR8: ledger.md の「hook を登録していれば記録が出る」は無条件——`claude -p` の子では残らないことがある | 示せる（著者の実走——python の hook で記録 0 件） | I6 | 直す——「対話のセッションで」に限り、`claude -p` の子では残らないことがあると足した |
| CR9: 認証の行の「守る」は本文と題を約束するのに、変異は本文だけ | 示せる（変異の表に題だけの変異が無い） | I3 | 直す——「守る」を本文と題の 2 行に分け、題の変異と検査を足した（16 行・16 件） |
| CR10: 公開ページの理由「利用上限と違って全リクエストが失敗する」は誤り（上限も全部失敗する。違いは時間で戻るか）。ほかの値の案内が無くなった | 示せる（理由の文言。上限も全リクエストが失敗する） | I5・I6 | 直す——理由を「時間がたっても戻らない」に、ほかの値は記録だけと 1 行足した |

### 採否の表（2 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| P2-1: CR4 の直しが `impl`・`gate` の行に `利用者の判断待ち:` を付けさせ、cruise `SKILL.md` の「`pr` の行になるまで付けない」と食い違う。外す道も無い | 示せる（cruise `SKILL.md` 370 行と ledger.md の文言） | I4 | 直す——`state=blocked` と `note` で渡す形に |
| P2-2: 「status が読めない体は #472 の項のとおり起こし直さない」に起動の種類の条件が無い（#472 は `--timer` だけ）。別のセッションで再開すると欠票が取り直されない | 示せる（ledger.md 81 行と新しい項） | I4 | 直す——`--timer` の起動と、それ以外（実物で確かめ、票が無ければ取り直す）に分けた |
| P2-3: 401 の項に入るかを何で知るかが書いていない | 示せる（項に入る条件の文言が無い） | I4 | 直す——hook の記録の `authentication_failed` の行と時刻か、利用者の申告。どちらも無ければ入らない |
| P2-4: CR8 の直しが「対話のセッションで hook を登録していれば記録が出る」を事実として書いた（公開ページは対話のセッションを確かめていないと書く） | 示せる（公開ページ 76 行・計画ファイルの未証明） | I6 | 直す——入力の `error` が `authentication_failed` になること（`claude -p` で写して確かめた）と、記録が残るかは確かめていないことに分けた |
| P2-5: CR10 で足した「ほかの値は記録だけ」は誤り——`notify` の else の枝が通知を出す | 示せる（`notify` の else の枝・テストの `overloaded` の試料の 4 引数） | I6 | 直す——「通知は出すが案内は添えない」に |
| P2-6: 計画ファイルのデプロイ経路が `record-stop-failure.py` の変更を挙げていない。absent-lines.md がこのスクリプトの変更を名指しして、宣言に従わない（マージで止める）とする | 示せる（absent-lines.md 466〜467 行） | 無し（計画ファイルは成果物でない） | 計画ファイルのデプロイ経路を直した（成果物は変えない）。**マージ前に人の判断が要る点として PR コメントと報告に書く** |
| P2-7: 公開ページが今も `claude -p` での確かめ方だけを示し、2.1.318 では記録が残らないことがあるという但し書きが無い | 示せる（この周の実走は設定つき） | 無し（受入基準の外。版か設定かも分けていない） | 残課題 |
| P2-8: 計画ファイルの陽性対照の「4 件」が CR9 の後は 6 件 | 示せる（当て直した結果） | 無し（計画ファイル） | 計画ファイルの記録を直した |
| P2-9: 変異「上限でなくても待てと添える」が `limit = True` に粗くなり、待ての検査を消しても殺せてしまう | 示せる（変異の形） | 無し（守るの行と変異は 1 対 1 のまま） | 残課題 |
| P2-10: 新しい検査「上限の通知に /login を添えない」が長さを見ずに添字を引く——通知が出ないと IndexError で全体が止まる | 示せない（いまは通知が出る。本体を壊したときだけ） | 無し | 残課題 |

## 手順 8（経験の還元）

- この周の起票: 0 件（確認の Issue を含め立てていない。周の途中の課題は found-lines.md の振り分けで PR コメントにだけ残す）
