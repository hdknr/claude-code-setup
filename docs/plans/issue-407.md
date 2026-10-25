# Issue #407 — dev-loop: iPhone への通知が届くかの試験手順を持つ（#394 の補足）

#394 の環境点検に**通知の試験**を足す。スクリプトは `PushNotification` を呼べない（道具はモデルのもの）ので、
**試験の手順は `SKILL.md` に、返り値の判定はスクリプトの新しい入口 `--push-result` に**置く。
返り値の表をコードにして、テストと変異で押さえる。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — `--push-result <返り値>` の判定・docstring の表・人が見る項目の文言（Remote Control は `/remote-control` と `claude rc` の違い、モバイルの登録は通知の試験を指す）
- `scripts/test-check-unattended-env.py` — 判定のシナリオと変異
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 環境点検の項に通知の試験の段（遅延送信を含む）。版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.52.0 → 1.53.0。能力の追加なので minor）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `docs/usage/advanced-remote-control.md` — 「通知を試す」の表に欠けている行（`Remote Control inactive`）と、使用中の判定の中身
- `docs/plans/issue-407.md` — この計画

触らない:

- `PushNotification` をスクリプトから呼ぶこと（道具はモデルのもの。呼べない）
- 試験の自動化（タイマー・送信をスクリプトにする）——送るのはモデル、離れるのは人
- `CLAUDE.md`（一覧の行は「環境点検」のままで足りる）・`check-all.py`・CI（テストは既に登録済み）
- `CLAUDE_CODE_DISABLE_NOTIFICATION_PRESENCE_CHECK` を手順に入れること（本体で読んだが試していない。起動し直しが要る）

### 同じことを述べている箇所の数

- 「返り値 → 原因 → 対処」の表: スクリプトの docstring（**正**）・スクリプトのコード（`PUSH_RESULTS`）・テストの期待値・公開ページの表 —— 4 箇所。
  **分けない理由**: docstring とコードとテストは道具 1 本の内側。公開ページは dev-loop を使わない読者向けの手順書で、
  プラグインの中を指せない（利用者が読む場所が違う）。公開ページは表の行を足すだけにして、判定の規則（「省かれたのは失敗ではない」）は書き足さない。
- 「試験の手順（離れてから送る）」: `SKILL.md`（dev-loop の規範。**正**）・公開ページ（既にある）—— 2 箇所。同じ理由で分けない。
- 版: 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md`）。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` は main への push で Pages に載る。

## 実測した前提（2026-10-25・Claude Code 2.1.310・macOS。本体 `~/.local/share/claude/versions/2.1.310` の文字列）

`PushNotification` の `call` と `mapToolResultToToolResultBlockParam` を読んだ:

- 判定の順: ① Remote Control がつながっていて（`replBridgeActive`）、リモートのセッションでなく、`agentPushNotifEnabled` が偽 → `config_off`
  ② リモートのセッションでなく、`CLAUDE_CODE_DISABLE_NOTIFICATION_PRESENCE_CHECK` が無く、使用中 → `user_present`
  ③ Remote Control がつながっていない → `no_transport` ④ それ以外 → 送信
- 返り値の文字列:
  - `config_off`: `Push not sent — mobile push is disabled in /config.`
  - `user_present`: `Not sent — this terminal is active, so your output here already reaches the user; a separate notification would be redundant.`
  - `no_transport`: `Terminal notification sent. Mobile push not sent (Remote Control inactive).`（端末の通知を出せないときは `Mobile push not sent (Remote Control inactive).`）
  - 送信: `Terminal notification sent. Mobile push requested.`（同じく `Mobile push requested.`）
- **使用中**（`Ins()`）: 端末のフォーカスが分かればそれ、分からなければ**最後の操作から 60 秒以内**（`P3e=60000`）
- **Remote Control がつながっていなければ `config_off` は出ない**（① は transport があるときだけ）。**使用中なら ③ より先に止まる**
  ——「省かれた」の陰で Remote Control が切れていても分からない。だから省かれたら送り直す
- `No mobile registered` は `/config` の表示（`has_active_channel === false`）で、`PushNotification` の返り値ではない
- **iPhone からの操作が「使用中」になるか**は本体からは読み切れていない（Issue の利用者の実測）。手順は両方から離れる形にする
- `claude remote-control --help`: 「Permission mode for **spawned** sessions」——`claude rc` は新しいセッションを起こす待ち受け

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| 1 | 4 種類の返り値が、それぞれ正しい原因・対処に分かれる | `--push-result` に渡す文字列（端末の通知あり・なしの 2 形ずつ） | テストで 6 形を当てる。期待は本体の文字列（上）と一字一句同じ |
| 2 | **省かれた（使用中）を失敗と数えない**——要対処（1）ではなく「やり直す」（2） | `--push-result` | テストで終了コードを見る。変異「使用中を要対処にする」が赤 |
| 3 | **送信の要求（`Mobile push requested`）を「届いた」と言わない**——人が見る（iPhone に届いたか）を出す | `--push-result` | テストで出力を見る |
| 4 | 知らない文字列・空を「良い」に混ぜない（判定できない・2） | `--push-result ''`・別の版の文言 | テスト |
| 5 | `--push-result` は設定を読まない・何も書かない（判定だけ）。既存の点検の挙動は変わらない | `main()` の分岐 | テスト（既存シナリオの陽性対照が緑のまま・書かないテスト） |
| 6 | 人が見る項目が、`/remote-control`（いまのセッション）と `claude rc`（待ち受け）の違いと、通知の試験を指す | `human_items` | テストで出力の文言を見る |
| 7 | `SKILL.md` に試験の手順がある: 点検 → `/remote-control` で作業中のセッションにつなぐ → iPhone から 1 行送って届くのを見る → タイマーで遅らせて両方から離れる → 送る → 返り値を `--push-result` に渡す | `SKILL.md` | 目視。指し先は `check-skill-pointers.py` |
| 8 | 文面が主張する事実（返り値の文字列・判定の順・60 秒）が本体と一致する | docstring・`SKILL.md`・公開ページ | 本体の文字列と突き合わせる（Verifier にも当てさせる） |
| 9 | 版の 3 箇所・`skill-metrics.py --check`・`check-all.py`・公開ページのリンク | 登録漏れ | `check-all.py` |

### 必須要件の掛け算

- 受入基準 × 2 つの関門 × 2 パス = 4 つの受け渡し（Verifier 1・2 パス目、`/code-review` 1・2 パス目）。既知の限界も同じ 4 回渡す。

### この環境では証明できないもの（未証明）

- iPhone に実際に届くこと（iPhone が要る。`Mobile push requested.` から先はサーバと端末）
- iPhone からの操作が「使用中」になること（利用者の実測だけ。本体から読み切れていない）
- `/remote-control` の 2 回目に QR コードの選択肢が出ること（画面の操作）
- 2.1.310 以外の版で文字列が同じであること

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を触るので再生成。`skill-metrics.py --check` で鮮度）
- 図は触らない（`diagrams/` の変更なし）

## 未解決の判断

- なし

## 周の在り処

- ブランチ: `issue/407-push-notify-test`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-407`
- 起点: `7865e11`（Merge pull request #420）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `7865e116e98f6a4d0b1acdb5c3547d66590e7204`

## 関門の進捗（再開点）

- 実装: 済み（スクリプトの `--push-result`・人が見る項目・docstring、`SKILL.md` の試験の段、公開ページの表の 1 行と判定の順、版 1.53.0、§8.2 再生成）
- テスト: 陽性対照が緑・変異 39 件すべて赤（新しい変異 7 件を含む）。実環境で `--push-result` を読むだけ走らせて、使用中 → 2・送信の要求 → 0 を確かめた
- 実装中に見つけて直したもの: `report_push` の既定引数 `out=sys.stdout` が定義時に束縛され、`redirect_stdout` で受けられなかった（テストの陽性対照が赤になって分かった）。`out=None` にした。既存の `report` も同じ形だが、`main` からしか呼ばれずテストは `out` を渡しているので触らない
- `check-all.py`: 49 本のうち `check-plan-counts.py` だけ赤（件数の行が無かった）→ 下に足した
- 交絡を潰した手順: 実験は本体の文字列の読み取りと、実環境での `--push-result` の実行だけ。返り値の文字列は本体から一字一句写した（推測で書いた文字列でテストしていない）
- 実装のコミット: `80dc24d`。`check-all.py`（`80dc24d` の時点）: 49/49・失敗 0
- 割り目（手順 4）: AskUserQuestion で訊いた → **「ここで割る」**（2026-10-25）。再開は手順 5 の Verifier 1 パス目から
- Verifier 1 パス目: 済み——**反証 0 件**（`dev-loop:dev-loop-verifier`・sonnet）。判定の順は自分で読み直しておらず「未確認」と報告 → `/code-review` が本体で確かめ、親も本体の `call` を読んで一致を確かめた
- `/code-review` 1 パス目: 済み——**指摘 8 件**（採否は下の表。直す 7・残課題 1）
- 1 パス目の指摘対応: 済み（F1〜F7）。ラベル「やり直す」を足し（終了コードは 2 のまま）、`report` の既定引数を `out=None` に、手順を「端末を前面から外す」に、公開ページの iPhone の主張を実測に弱め、`claude rc` の括弧書きを落とし、docstring の判定の順を本体どおりに。テストに 5 件・変異に 4 件を足した（変異 43 件すべて赤）
- 等価変異を 1 つ捨てた: 「`report` の出力先を定義時に束縛する」は単独では緑（`report` を `--push-result` から呼ばない限り挙動が変わらない）。代わりに陽性対照を外で取った——旧い束縛＋「判定のあとも設定を読む」変異は**緑**（F1 の再現）、修正後の束縛＋同じ変異は**赤**
- `check-all.py`（指摘対応の後）: 49/49・失敗 0
- 次: **手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方**が残っている。2 パス目の割り目（手順 6）で訊く

## 起票

- この周の起票: 0 件（マージ前に確認する）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| スクリプトから `PushNotification` を呼ぶ | 採らない | 道具はモデルのもの。スクリプトは返り値の判定だけ |
| `CLAUDE_CODE_DISABLE_NOTIFICATION_PRESENCE_CHECK` で使用中の判定を外す | 手順に入れない | 本体で読んだだけで試していない。起動し直しが要り、試験が「いまのセッション」でなくなる |
| 返り値の照合を部分一致にする | 採る | 端末の通知の有無で前置き（`Terminal notification sent.`）が付く・付かないの 2 形がある |
| 既存の `report` の既定引数 `out=sys.stdout` | **直す**（1 パス目の F1 で理由が誤りと判明） | 当初は「`main` からしか呼ばれずテストは `out` を渡す」としたが、`--push-result` のテストは `main()` を `redirect_stdout` で受けるので、`report` の出力が受け皿を素通りする |

### 1 パス目の指摘と採否（Verifier: 反証 0 件／`/code-review`: 8 件）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| F1 `"設定の層" not in buf` は落ちえない（`report` の既定引数が定義時に束縛） | 示せる——`/code-review` が外で変異（`report_push` の後も `gather`→`report` を走らせる）を当てて緑、`設定の層` が実の stdout に出た | 5 | 直す |
| F2 終了コード 2 が「省かれた」と「知らない返り値」で同じなのに、`SKILL.md` が「2 は失敗ではない、送り直す」と書く | 示せる——知らない返り値の対処を使用中と同じ文言にする変異が緑（`/code-review` の変異 B） | 2・4・8 | 直す（ラベルを分け、`SKILL.md` はラベルで分岐させる。終了コードは 2 のまま） |
| F3 使用中が `[判定できない]` と出る（原因は分かっている） | 示せる——`--push-result` の出力 | 2 | 直す（F2 と同じ修正で「やり直す」のラベル） |
| F4 試験の手順が 60 秒を前提に画面ロックを指すが、`Ins()` はフォーカスが分かればそれだけで決まる | 示せる——本体 `function Ins(){let e=w$e();if(e!==void 0)return e;return Date.now()-Yp()<P3e}` | 7・8 | 直す（端末を前面から外す、を手順に） |
| F5 公開ページが「iPhone から操作しているあいだも使用中」を事実として書く（計画では未証明） | 示せる——計画の未証明の表と公開ページの文 | 8 | 直す（実測として書き、機構は確かめていないと書く） |
| F6 `claude rc` を「アプリの『デバイスを追加』の流れ」と書くが根拠が無い | 示せる——計画の実測した前提に無い | 8 | 直す（括弧書きを落とす） |
| F7 docstring の「リモートのセッションでは ① ② を飛ばす」が本体と違う——`p=CLAUDE_CODE_REMOTE\|\|Pn()\|\|Izs(l)` が立つと ③ も飛ばして必ず送る | 示せる——本体 `p=c\|\|Izs(l),m=p\|\|Vc()`、`function Izs(r){return cC()&&cS.of(r).transportPersists===!0}` | 8 | 直す |
| F8 `PushNotification` はフラグ（`tengu_kairos_push_notifications`）で無いことがあり、その場合の道が無い | 示せる——本体の `isEnabled`（`/code-review` の引用。自分では文字列の在処だけ確かめた） | 無し | 残課題 |
