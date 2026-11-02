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
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 交絡: 実験なし（この周は測らない。親の実測を読んで書く）

## 既知の限界・決着済みの論点

- 実測は haiku・`-p`・30 秒の疑似端末だけ。通知と対話のセッションの中の `/remote-control` は測っていない——公開ページの「確かめていないこと」に残す（決着: 残す。理由: 親の指示で測り直さない）。
- 「エラーは出ず、黙って無い」は起動時の観測（`--remote-control` の 30 秒・`init` の一覧）についてだけ言う。

- この周の起票: 0 件（未定。手順 8 で決める）
