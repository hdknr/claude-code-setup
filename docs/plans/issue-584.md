# Issue #584（3 回目の周）— 受入基準 4: 長期トークンで動かなかった機能を docs に挙げる

- 出所: cruise #474 の周（利用者は居る）。この周は cruise の親から委ねられたサブエージェントが回し、`EnterWorktree` を使わず
  worktree の絶対パスで作業する。台帳は書かない（親だけが書く）。**マージはしない**——PR と PR 側の CI まで（親の指示）。
- 範囲は親の委譲文: #584 の受入基準 4「4 で動かなかった機能を docs に挙げる（無ければ「確かめて、無かった」と書く）」だけ。
- 一次の証拠は親が済ませた実測（[#584 のコメント 6575918006](https://github.com/hdknr/claude-code-setup/issues/584#issuecomment-6575918006)、
  2026-11-02・Claude Code 2.1.316。生の出力は親の scratchpad の `c4/`）。**この周では測り直さない**（長期トークンで `claude` を起動しない。
  pid 13906 の観測のセッションに触れない）。生の出力のうち、コネクタ（`init.*` の `mcp_servers`）・サブエージェント（`agent.long.jsonl` の
  `SUBAGENT_OK_42`）・通知（`push.long.jsonl` の「Not sent — this terminal is active」）・Remote Control（`rc2.long.txt` の見出し `Claude API`、
  `rc.oauth.txt` の `/rc connecting`）は著者が grep で突き合わせた。
- 受入基準 3 の確認（起動口で起動したセッションの中で「認証」が `[良い]`）は [#584 のコメント 6573400732](https://github.com/hdknr/claude-code-setup/issues/584#issuecomment-6573400732)。
- PR は **`Refs #584`**（受入基準 1 は今夜観測するので閉じない）。

### 前の周と、計画ファイルの名前

- `find-cycle.py 584` は前の 2 周（PR #612・#784。どちらも MERGED、worktree は無い）の計画ファイル・ブランチ・コミットに当たった——再開ではない。
- `prepare-worktree.sh 584 measured-features` は前のブランチ名に当たって 3 で止まった。前の周と同じく `references/resume.md` の
  「規約どおりの名前で最初から切りたいなら」の形（`git fetch` → `git worktree add --no-track <絶対パス> -b issue/584-measured-features origin/main`）で切った。
- 前の周の記録 `docs/plans/issue-584.md` を `docs/plans/issue-584-784.md`（PR 番号）へ `git mv` で改名し（中身は変えない）、この周が
  `docs/plans/issue-584.md` を使う（#784 の周と同じ形）。古いパスを指すものはリポジトリに無い（`git grep` で確かめた）。

## 変更範囲

触る:

- `docs/usage/cruise-long-lived-token.md` — 冒頭・「確かめていないこと」の 1〜3・「機能の表」の実測の欄・表の後の段落・「測り方」
- `docs/usage/mobile-remote-control.md` — トラブルシューティングの表に、長期トークンでは黙って繋がらない症状の 1 行
- `docs/plugins/dev-loop-cruise.md` — 点検の「認証」の項の「使えない見込みで、まだ測っていません」
- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 「認証」の直し方の文言（`token_fix`）と docstring の実測した前提の 1 項
- `scripts/test-check-unattended-env.py` — 上の文言に合わせて、検査の名前と変異 1 件の置換元
- `plugins/dev-loop/skills/cruise/SKILL.md` — §3 の 3 の 2 箇所（「使えない見込み」）と版の 2 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ）
- `docs/plans/issue-584-784.md` — 前の周の計画（改名だけ）
- `docs/plans/issue-584.md` — この計画

触らない:

- 点検の判定（良い／要対処／人が見る／判定できない）と起動口の動き——文言だけ
- `docs/plans/` の過去の計画ファイルの中身
- 受入基準 1 の観測・台帳

### 同じことを述べている箇所の数

「長期トークンで使えない機能」: 公開ページの表（正）・点検の直し方の文言・点検の docstring・cruise §3 の 3（2 箇所）・cruise の公開ページ・
Remote Control のトラブルシューティングの 7 箇所。公開ページの表を正とし、ほかは要点と指し先だけにする（分けない理由: 点検の出力は cruise の起動時に
利用者が読む・cruise §3 はモデルが読む・トラブルシューティングは Remote Control が繋がらない人が読む——読む人が違う）。

## デプロイ経路

`docs/` の変更は main への push で GitHub Pages に出る（CLAUDE.md の「デプロイ」）。プラグインは版を上げて配布。マージは親が行う。

## 受入基準

不変条件:

1. **公開ページが、長期トークンで動かなかった機能を挙げる**——claude.ai のコネクタ・Remote Control・Claude in Chrome を「使えない」、
   サブエージェント・`/code-review` を「動く」、通知を「判定できない」と、実測の条件（2.1.316・`-p`・haiku・対照は対話ログイン）とともに書く。
   書いた中身が一次の証拠（#584 のコメント 6575918006）と食い違わない。
2. **実測していないことを実測したと書かない**——通知・対話のセッションの中の `/remote-control`・haiku 以外のモデルは「確かめていない」に残る。
   8 時間を超えて 401 で止まらないこと（受入基準 1）は確かめていないままにする。
3. **古い「見込み」が残らない**——上の 7 箇所に、測った後の今も「使えない見込み」「まだ測っていない」「実測していない」の類が残らない
   （`docs/plans/` は除く）。受入基準 3 の「まだ見ていません」も残らない。
4. **点検の判定と出力の形は変わらない**——直し方の文言だけが変わり、`[良い]` などの判定・終了コードは同じ。テストが緑で、変異が赤になる。
5. **版**: dev-loop の版が 3 種類（`marketplace.json`・`plugin.json`・両 `SKILL.md`）で揃って上がる。

経路（不変条件を破りうる入口）:

- 3: 「見込み」を書く場所の数え直し——名前の grep（`見込み`・`inference`・`測って`・`実測`・`長期トークン`・`setup-token`・`Remote Control`）を
  `docs/`（plans を除く）・`plugins/`・`scripts/`・`CLAUDE.md`・`README.md` に当てる。言い換え（「推論だけ」「絞られ」）も当てる。
- 4: `check-unattended-env.py` の出力を読むもの——テスト・cruise §3 の 3（点検が添える文を見せる）。
- 1・2: 表の各行と冒頭・「確かめていないこと」・表の後の段落・トラブルシューティングの行。

証明できないもの（未証明）: なし——どれも文面と一次の証拠の突き合わせとテストで確かめられる。実測そのものは親が済ませた（この周は再測しない）。

生成物: `docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`SKILL.md` の版の行は節構造を変えないので動かない見込み——`skill-metrics.py --check` で確かめる）。
drawio の書き出しは無し。

## 直す線（出所）

- 直す線: `既定`（cruise の台帳の確かめた線 `直す線 = 既定`。2026-11-01T02:01:52Z 更新の `lines`）
- 周の途中の課題: `外に出す`（同上）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/584-measured-features`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-584-docs`・
  起点 `660abf15`（start-point `origin/main`）・base `origin/main` → `660abf154dc8b5636c79026752d3cfe44d1d68fd`（`git merge-base origin/main HEAD`）
- 割り目（手順 4）: 利用者は居るが、cruise の親から委ねられたサブエージェントなので `AskUserQuestion` は出さず、このまま続ける（親の指示どおり周を回しきる）。
- 1 パス目の指摘対応の起点: `e9717e80`（1 パス目の関門に渡した時点の HEAD）
- Verifier 1 パス目: 通した（sonnet・`dev-loop:dev-loop-verifier`）——反証 0 件（軽微 2・未確認 2。うち Remote Control の条件は CR1-4 と同じ）
- `/code-review` 1 パス目: 通した（high）——指摘 8 件。直す 4 件・残課題 4 件（下の採否の表）。手順 4 への差し戻しなし
- 1 パス目の指摘対応: `8e8f6500`（起点 `e9717e80` からの成果物の差分 5 ファイル——0 行ではないので 2 パス目を回す）
- 割り目（2 パス目の前）: cruise の親から委ねられたサブエージェントなので `AskUserQuestion` は出さず続ける。残るのは Verifier の当て直しと `/code-review` の 2 パス目の両方
- 2 パス目: Verifier・`/code-review` とも起動（base は同じ `660abf15`）。狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `be77ddf2`
- Verifier 2 パス目: 通した——反証 0 件（軽微 2）。`/code-review` 2 パス目: 通した——指摘 8 件。直す 7 件・残課題 1 件
- 2 パス目の指摘対応: `ee135fdd`。狭いパス: 起点 `be77ddf2` → 終点 `ee135fdd`（`git diff be77ddf2 ee135fdd`）に Verifier（sonnet）を通した——受入基準を破る反証 0 件、軽微 1 件（N-1。採否は人間が決める）。素通りした変異 0 件（Verifier は自分で変異を設計せず、テストに組み込まれた変異の赤を見た）
- PR: #788（`Refs #584`）
- Remote Control の起動の argv は親に訊いて得た（`--remote-control <名前>` だけを付けた対話の起動・既定の Opus 5.5・信頼済みのメインの作業ツリー・30 秒。ファイルには残っていない）
- 交絡: 実験なし（この周は測らない。親の実測を読んで書く）

## 既知の限界・決着済みの論点

- 実測は haiku・`-p`・30 秒の疑似端末だけ。通知と対話のセッションの中の `/remote-control` は測っていない——公開ページの「確かめていないこと」に残す（決着: 残す。理由: 親の指示で測り直さない）。
- 「エラーは出ず、黙って無い」は起動時の観測（`--remote-control` の 30 秒・`init` の一覧）についてだけ言う。
- Remote Control の起動の argv はファイルに残っていない——親の記録による、と公開ページに書いた（決着: 測り直さない。親の指示）。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1 claude.ai から届くスキル（`anthropic-skills:*`）が長期トークンで無いのに挙げていない | 示せる——`init.long.jsonl` の `skills` 37 個、`init.oauth.jsonl` 46 個、差は `anthropic-skills:*` の 9 個（著者が python で数えた） | 1 | 直す |
| CR1-2 対話ログインで「長期トークンに切り替えるか」を訊くとき、使えない機能を見せない | 示せる（点検の 8 時間の行の直し方に `token_fix` が無い） | 無し（受入基準は公開ページと古い見込み） | 残課題 |
| CR1-3 テストが「Remote Control」の有無しか見ず、古い見込みの文に戻しても緑 | 示せる（レビューが scratchpad の写しで当てた） | 無し（4 は判定と変異の赤。宣言した変異は赤） | 残課題 |
| CR1-4 Remote Control の行の条件（Opus 5.5・メインの作業ツリー・argv が残っていない）が書いた条件と違う | 示せる——`rc2.long.txt` の見出し `Opus 5.5 · Claude API`・cwd、親の回答 | 1 | 直す（条件を分けて書き、argv は親の記録による、と書く） |
| CR1-5 サブエージェントの行「子が決めた文字列」は誤り（親が指定した） | 示せる——`agent.long.jsonl` の `Agent` の prompt「Reply with the exact text SUBAGENT_OK_42」 | 1 | 直す（`agentId` と子のトークン数で子の起動を示す） |
| CR1-6 点検の Remote Control の項が、長期トークンのセッションでも `/remote-control` を打てと言う | 示せる（コードの分岐） | 無し | 残課題 |
| CR1-7 「公開ページの測る表」の指し先が古い（起動口の冒頭・点検の docstring の 1 項） | 示せる（ページの節は「機能の表」「測り方」） | 無し（見込みの主張ではなく指し先の名前） | 残課題 |
| CR1-8 「MCP を除く 29 個」は init/agent の組だけ（review2/push/chrome の組は 31 個） | 示せる——著者が組ごとに数えた（29・29・31・31・31、両側同じ） | 1 | 直す（「組どうしで同じ。29 個か 31 個」） |
| V1 Remote Control の行のモデルが Opus であることを書いていない | CR1-4 と同じ | 1 | 直す（CR1-4 と一緒に） |
| V2 `--remote-control` を付けたかがファイルから確かめられない | 示せる（argv は残っていない） | 1 | 直す（親の記録による、と書く。CR1-4） |


### 2 パス目の採否の表

Verifier 2 パス目: 反証 0 件（軽微 2——V2-1 は CR2-4 と同じ、V2-2「9 個が多い」の言い回しは CR2-5 で一緒に直した）。`/code-review` 2 パス目: 指摘 8 件。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1 組み込みのプラグイン `cc-plugin-sec-default` が対話ログインの側にだけ読み込まれた差を挙げていない | 示せる——init の `plugins` が 9 対 10（レビューが全組で確かめた） | 1 | 直す（表の後に書き、何が変わるかを「確かめていないこと」の 2 に足す） |
| CR2-2 `/code-review` は `low` だけ測ったのに「動く」と言い切る | 示せる——`review2.long.jsonl` に `low effort → 1 diff pass`（著者が grep） | 2 | 直す（`low` と書き、`high` を測っていない側に足す） |
| CR2-3 出典に指したコメントがページと食い違う（RC の条件・道具の数・スキルの行） | 示せる（コメント 6575918006 の本文） | 1 | 直す（ページのほうを正とすると書く。コメントの訂正は親が行う） |
| CR2-4 トラブルシューティングの既存行（エラー文が出る）と足した行（エラーも出ない）が食い違って読める | 示せる（2 行の文面） | 2 | 直す（足した行を起動時の 30 秒の観測に限り、セッションの中は確かめていないと書く） |
| CR2-5 スキルの数 37/46 は `--chrome` 以外の組の値（`--chrome` の組は 37/47） | 示せる——`chrome.*.jsonl` の init（著者が数えた） | 1 | 直す |
| CR2-6 「通知が iPhone に届く経路も無い見込み」が残る | 示せる（文面） | 3 | 直す（「判定できていない」に揃える） |
| CR2-7 「測り方」に済んだ 3 の手順が残る | 示せる（文面） | 2・3 | 直す（手順から外し、3 は確かめたと書く） |
| CR2-8 使えない機能の列挙を 6 箇所に写している（指し先だけにしていない） | 示せる（6 箇所の文面） | 無し | 残課題 |

### 狭いパスの指摘（採否は人間が決める）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| N-1 公開ページの「cruise の関門が使う `high`」は、リポジトリの中に一次ソースが無い（`plugins/dev-loop` で `/code-review` に `high` を渡す箇所が見つからない） | 示せない（Verifier は「未確認」とした。出所は dev-loop の周で `/code-review high` を渡している運用） | 無し | 人間が決める |

### 手順 8 の振り分け（`周の途中の課題 = 外に出す`。`references/found-lines.md`）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| 対話ログインで切り替えを訊くとき、使えない機能を見せない | #584 /code-review 1 パス目（CR1-2） | 示せる | 記録だけ——誤った結果ではなく、見せる情報が足りない（公開ページには書いてある） |
| 点検のテストが古い見込みの文への戻りを捕まえない | #584 /code-review 1 パス目（CR1-3） | 示せる | 記録だけ——試料の穴 |
| 点検の Remote Control の項が、長期トークンのセッションでも `/remote-control` を案内する | #584 /code-review 1 パス目（CR1-6） | 示せる（コード） | 記録だけ——「人が見る」の項で、同じ出力の「認証」の行が使えないと言う。セッションの中の `/remote-control` は測っていない。迷ったら記録だけ |
| 「公開ページの測る表」の指し先の名前が古い（起動口の冒頭・点検の docstring） | #584 /code-review 1 パス目（CR1-7） | 示せる | 記録だけ——文言 |
| 使えない機能の列挙を 6 箇所に写している | #584 /code-review 2 パス目（CR2-8） | 示せる | 記録だけ——文言（写しの持ち方） |
| 「cruise の関門が使う `high`」の出所がリポジトリの中に無い | #584 狭いパス（N-1） | 示せない | 記録だけ——文言 |

- この周の起票: 0 件（振り分けで直すに当たる行が無い）
