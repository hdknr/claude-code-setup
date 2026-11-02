# Issue #584（2 回目の周）— 点検の「認証」が、起動した claude の環境で長期トークンを見分ける

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-11-02）の周。**不在の周**である——訊く場面は
  `references/absent-lines.md` の「訊く場面」のとおり訊かずに進める（`AskUserQuestion` を使わない）。この周は cruise の親から委ねられた
  サブエージェントが回し、`EnterWorktree` を使わず worktree の絶対パスで作業する。
- マージ: **この周ではしない**（親の指示——マージは親が行う）。台帳も書かない（親だけが書く）。PR・PR 側の CI・関門 2 パス・手順 8 の記録まで。
- この周の範囲は利用者が決めた（[#584 のコメント 6572028982](https://github.com/hdknr/claude-code-setup/issues/584#issuecomment-6572028982)、2026-11-02。
  書いたのは利用者 hdknr のアカウント。親の委譲文と一致する）: 受入基準 3 の不具合を直す——点検が祖先の claude のプロセスまで辿り、
  `ps eww` でその環境に変数の名前があるかを見る（値は出さない）。受入基準 1（8 時間を超えて 401 で止まらない）の観測は利用者が続ける。
- PR は **`Refs #584`**（受入基準 1 の観測が残るので閉じない）。

### 前の周と、計画ファイルの名前

- 1 回目は PR #612（`Refs`。部分納品でマージ済み）。`find-cycle.py 584` は 1 回目の計画ファイル・ブランチ `issue/584-cruise-long-lived-token`・コミットに当たったが、
  worktree は無く、PR #612 は MERGED——再開ではない（親の指示も「新しいブランチ・worktree で始めてよい」）。
- `prepare-worktree.sh 584 …` は 1 回目のブランチ名に当たって 3 で止まるので、`references/resume.md` の「規約どおりの名前で最初から切りたいなら」の形
  （`git fetch` → `git worktree add --no-track <絶対パス> -b issue/584-auth-ancestor-env origin/main`）で切った。
- 計画ファイルは #491 の 2 回目の周（PR #781）と同じ形——1 回目の記録を `docs/plans/issue-584-612.md`（PR 番号）へ `git mv` で改名し（中身は 1 文字も変えない）、
  この周が `docs/plans/issue-584.md` を使う。古いパスを指すものはリポジトリに無い（`git grep` で確かめた）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 最寄りの祖先の claude を辿る `nearest_claude`（flag の層の `find_flag_settings` と共有）・その環境の認証の変数の名前を返す `launcher_auth_names`・`check_auth` が自分の環境に長期トークンが無ければそれを見る。docstring（表の認証の行・判定できない・実測した前提・守る 4 行・守らない 1 行）
- `scripts/test-check-unattended-env.py` — 偽の `ps` に起動した claude の環境（`eww`）と引数だけ（`ww`）の形を足し、祖先にある／無い／読めない（5 形）／引数に書かれた形／先に使われる認証を当てる。本番の経路（`main`）は偽の親（`os.getppid()`）で当てる。変異 12 件を足し、本体の形が変わった 8 件の置換元を直した
- `docs/usage/cruise-long-lived-token.md` — 部品の表・「3. cruise の起動時の点検で確かめる」に Bash の環境では見えないこと・「確かめていないこと」の 3
- `plugins/dev-loop/skills/dev-loop/scripts/launch-with-long-token.sh` — 冒頭の「守らない」に 1 項（Bash の環境では見えない。`env` で見ない）
- `plugins/dev-loop/skills/cruise/SKILL.md` — §3 の 3 に 1 文（認証は点検の行で決め、Bash の `env` で決めない）と版の 2 行
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ）
- `docs/plans/issue-584-612.md` — 1 回目の計画（改名だけ）
- `docs/plans/issue-584.md` — この計画

触らない:

- 起動口の動き（トークンの読み方・止まり方・`--store-token`・`--status`・`--account`）——コメントの 1 項だけ
- `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`／`GITHUB_ACTIONS` の「判定できない」とセッションの外（`CLAUDECODE` が無い）の扱い——変えない（親の指示）
- 自分の環境に長期トークンがあるときの判定（起動した claude の環境は見ない——指示の「自分の環境に無ければ」）
- 受入基準 1・4 の観測（利用者が行う）・台帳

### 同じことを述べている箇所の数

- 「2.1.316 は起動時のトークンを Bash の環境から外す。だから起動した claude の環境を見る」: 本体の docstring（実測した前提）・docs の 3・cruise §3 の 3・起動口の冒頭の 4 箇所。
  本体の docstring を正とし、cruise §3 はそこを指す。docs と起動口は利用者が読む場所なので要点を置く（分けない理由: 読む人が違う。誤案内は Bash の `env` を見た Claude と利用者の両方で起きうる）
- 判定の表: 本体の docstring 1 箇所（docs は指すだけ）

## 乗るデプロイ経路

`docs/` は main への push で GitHub Pages に出る。`plugins/dev-loop` は main へのマージでプラグインの新しい版として配られる（版を上げる: 1.75.0 → 1.75.1）。

## 版

- dev-loop を patch で上げる: main の先端 1.75.0 → **1.75.1**（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本の 2 行）。不具合の修正なので patch（CLAUDE.md の表）

## 周の在り処

- ブランチ: `issue/584-auth-ancestor-env`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-584-auth`
- 起点: `28481795`（start-point `origin/main`）
- base: `origin/main` → `284817958af9022645ebb19e6365125bf841dba8`（`git merge-base origin/main HEAD`）

## 線（出所）

- 直す線: `既定`（cruise の確かめた線（台帳 `issue-474`））
- 仕様の穴 = 推奨で決めて起票・マージ = 関門を通ればマージ（この周はマージしない——親の指示）・周の途中の課題 = 外に出す（台帳 `issue-474`。利用者の確認 2026-10-27T09:07:27Z・2026-10-28T07:24:46Z・2026-10-28T23:56:17Z・2026-11-01T02:01:52Z）
- 周の途中の課題の振り分けは `references/found-lines.md` の「振り分け」（直す／記録だけ／捨てる）。起票は直すに当たるものだけ（利用者の方針: 実際の利用でまず起きない形は起票しない）
- `実機確認` の線は台帳に無い——既定の `止まる`

## 受入基準

不変条件 × 経路:

1. **Bash の環境に `CLAUDE_CODE_OAUTH_TOKEN` が無くても、起動した claude（最寄りの祖先）の環境に空でない値で在れば「良い」（長期トークン）**
   - 経路: Bash の親が zsh で、その親が claude（祖先を辿る）／`--present`（居る cruise）／本番の経路（`main` → `gather(env=None)` → `os.getppid()` から辿る）
2. **祖先の claude の環境にも無ければ（空の値を含む）、従来どおり「8 時間」（不在は要対処・居れば人が見る）**
   - 経路: 値が空（`CLAUDE_CODE_OAUTH_TOKEN=`）／引数に `CLAUDE_CODE_OAUTH_TOKEN=…` と書かれているが環境には無い（引数を環境と読まない）／本番の経路
3. **起動した claude の環境を読めなければ「判定できない」——「8 時間」（対話ログイン）と断定しない**
   - 経路: `ps` が祖先を読めない／祖先に claude が無い／最寄りの claude が spare（`--bg-spare`）／環境が見えない（`PATH=`・`HOME=` のどちらも無い）／
     `ps eww` の出力が `ps ww` の出力で始まらない（引数と環境を切り分けられない）／`ps eww` が非 0／本番の経路で親を読めない
4. **祖先の環境に長期トークンより先に使われうる認証（`ANTHROPIC_AUTH_TOKEN`・`ANTHROPIC_API_KEY`）があれば「人が見る」**（既存の判定の順と同じ: 先に使われる認証 → 長期トークン → 8 時間）
5. **値を出さない**——起動した claude の環境の値・環境の文字列を、出力・失敗の理由・返り値に入れない（返すのは変数の名前だけ）
6. **既存の扱いを変えない**——セッションの外（`CLAUDECODE` が `1` でない）・消去の設定（`SCRUB`／`GITHUB_ACTIONS`）は判定できない、自分の環境の長期トークン・API キー・`apiKeyHelper` の判定、flag の層（`--settings` を最寄りの claude から拾う・spare は判定できない・外側を見ない）
7. **テストは本物のプロセス・本物のトークンに届かない**——偽の `ps` を `PATH` の先頭に置き、祖先は `ancestor` を差し替えるか偽の親（`os.getppid()` の pid に答える偽の `ps`）で当てる。
   変異テストは「守る」の行ごとに 1 つ以上で、陽性対照（元の本体で全部緑）を見る
8. **docs・起動口・cruise §3 の 3**: Bash の環境では見えないこと、`env` で判断しないこと、点検は起動した claude の環境を見ること。cruise §3 の 3（点検の「認証」を読んで訊く）と食い違わない。`mkdocs build --strict` 相当が通る
9. **版**: dev-loop 1.75.1 を 3 種類に揃える。`check-plugin-versions.py`・`skill-metrics.py --check` が緑。`check-all.py` が緑

掛け算: 受入基準を Verifier と `/code-review` に × 1 パス目・2 パス目（2 パス目が該当なしなら 1 パス目の 2 つ）。

### 証明できるもの／できないもの

- 証明できる: 1〜9（テスト・`check-all.py`・実プロセスへの陽性／陰性対照）
- 実プロセスで確かめたこと（値は出していない。名前の有無だけ）: 環境に `CLAUDE_CODE_OAUTH_TOKEN` を持つ手元の claude のプロセス（pid 13906）に `launcher_auth_names(13906)` を当てて名前が返り、
  `check_auth` が「良い」。この周のセッションの Bash から `launcher_auth_names()`（最寄りの claude は pid 57295、対話ログイン）を当てて空が返り、`check_auth` が「要対処」。
  cmux の祖先（pid 28635）からは「祖先に claude が無い」
- **未証明（この環境では確かめられない）**: 起動口で起動したセッションの**中から**点検を回して「良い」と出ること——このセッションは対話ログインで起動しており、
  長期トークンのセッションに入れない（pid 13906 に外から当てたのは同じ関数で、起動した claude の判定の部分は同じだが、そのセッションの Bash の経路そのものではない）。PR コメントで人に申告する
- BLOCKED: なし（前の周の B1・B2——8 時間の観測と機能の表——は利用者の観測で、この周の受入基準ではない）

## 生成物

- §8.2 の生成ブロック（`skill-metrics.py --check`）——`SKILL.md` の版の行を変えるので該当。鮮度を受入基準 9 に入れる
- 図: なし

## 未解決・確認待ち

- なし（範囲は利用者が決めた）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 自分の環境に長期トークンがあるとき、起動した claude の環境（そこにだけ在る API キーの類）も見るか | 見ない | 利用者の指示は「自分の環境に無ければ」辿る。見ると、いま「良い」の経路が `ps` に依るようになり、読めなければ「判定できない」に変わる。docstring の守らないに書いた |
| 最寄りの claude が spare（`--bg-spare`）なら | 判定できない | spare は引き継いだセッションで、そのプロセスの起動時の環境が、このセッションを起動した環境とは限らない（flag の層と同じ扱い） |
| セッションの外・消去の設定（`SCRUB`／`GITHUB_ACTIONS`）で起動した claude の環境を見るか | 見ない（従来どおり判定できない） | 親の指示「セッションの外の既存の扱いは変えない」。消去の設定は判定できない（安全側）のまま |
| 値に空白を含む環境変数の中の `NAME=…` を変数と読みうる・`claude` という名前の別のプログラムを挟んだ形 | 守らない（docstring に書いた） | `ps eww` の出力は空白で区切られ、値の境目が分からない。実際の利用でまず起きない形（利用者の方針） |
| 祖先を辿る式を flag の層と共有するか | 共有する（`nearest_claude`） | 写しを作らない。flag の層の既存のテストと変異（最寄りで止まる・spare・`--settings=`）はそのまま緑 |
| 変異の数を「守る」の行の数に合わせて機械で見るか | 見ない | このテストには行の数を数える仕組みが無い（`test-worktree-scripts.py` だけの決まり）。守る 4 行のどれにも 1 つ以上の変異を当てた |

### 1 パス目の採否（直す線: 既定）

Verifier（`dev-loop:dev-loop-verifier`・sonnet。テンプレート 169 行を読んだ・`wc -l` と一致）反証 0 件。`/code-review`（high。受入基準は `prompts/review-handoff.md` を埋めて Skill の `args` で渡した）7 件。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1 | cruise `references/child-process.md` の「子は親の環境変数を継ぐ——長期トークンの親の子は同じトークンで回る」が、2.1.316 の観測と食い違う（`child-cycle.py` は子の環境を `os.environ`＝Bash の環境から作る） | 示せない（子の `claude -p` を長期トークンの親から起こして測っていない。課金と長期トークンのセッションが要る） | 無し（この周の受入基準は点検の判定。子の認証は範囲の外） | 残課題 |
| CR2 | 認証の試料に入れ子の claude が無く、`launcher_auth_names` を外側の claude まで辿らせる変異が緑のまま | 示せる（レビューが変異を当てて緑。この周で同じ変異を足して元の試料で緑を再現） | 7（守る「flag の層と認証は、同じ最寄りの祖先の claude を見る」に認証側の変異が無い）・1 | 直す |
| CR3 | `ps` で親を辿れない環境（コンテナの PID 名前空間・サンドボックス）では、以前の要対処が判定できないになり、cruise §3 の 3 で訊かれない。守らないに書いていない | 示せない（そういう環境で回していない） | 無し（受入基準 3 どおり） | 残課題 |
| CR4 | `argv[0]` が `node …` の導入（npm）では claude を見つけられない | 示せない（その導入で `ps` を見ていない） | 無し | 残課題 |
| CR5 | 祖先を 2 度辿る・`ps ww` が `nearest_claude` の読んだ行と重複（効率） | 示せない（失敗ではない） | 無し | 残課題 |
| CR6 | docstring の傍証（13906 の子の `CLAUDECODE=1` の有無）は cmux の hook の子で、Bash のツールの子ではない | 示せる（レビューが名前で確かめた——子は `cmux`） | 無し（判定は変わらない。記述の精度） | 残課題 |
| CR7 | 親の pid が 0・1（コンテナの PID 1 で回す）だと本番の経路の試料が落ちる | 示せない（CI は VM。そう回していない） | 無し | 残課題 |

### 2 パス目の採否（直す線: 既定）

Verifier（sonnet。テンプレート 169 行・一致）反証 0 件。`/code-review`（high。同じ受入基準を `SendMessage` で渡した）2 件。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R2-1 | CR1 の「示せない」は一部誤り——`child-process.md` の「長期トークンの親の子は同じトークンで回る」と、この周の docstring・docs（2.1.316 は Bash の環境から外す）は、`child-cycle.py` の `dict(os.environ)` を読めば食い違うと示せる。同じことを述べている箇所の数え漏れ | 示せる（文書と `child-cycle.py:235` の読解。子が 8 時間のログインで回ることは示せない） | 無し（この周の受入基準は点検の判定） | 残課題（手順 8 の振り分けで直す——起票の候補） |
| R2-2 | 件数の行が手順 8 の振り分けより先に「候補なし」 | 示せる | 無し | 手順 8 で書き直した（下） |

## 関門の進捗（再開点）

- 実装: 済み（`747480f`）。割り目 1: 不在のため訊かず続けた
- 1 パス目の指摘対応の起点: `20abb7e`（1 パス目の関門に渡した時点の HEAD）
- 1 パス目: Verifier 反証 0 件・`/code-review` 7 件（上の表）。直す 1 件（CR2）——試料 970・975（入れ子の claude）と変異「認証: 外側の claude の環境を見る」を足した（元の本体で緑・変異は当の表明だけで赤を確かめた）
- 1 パス目の指摘対応の差分: 0 行でない——2 パス目を回す。割り目 2: 不在のため訊かず続けた。残るもの: 手順 5 の当て直しと `/code-review` の 2 パス目の両方
- 2 パス目の指摘対応の起点（狭いパスの起点）: `33a3fad`
- 2 パス目: Verifier 反証 0 件・`/code-review` 2 件（上の表）。直した行 0 件
- 狭いパス: 該当なし（2 パス目で直した行が 0 件）
- 実験: 実プロセスへの陽性／陰性対照（上の「証明できるもの」）。交絡の候補: (a) `ps eww` が環境を出さないのに「無い」と読む——`PATH=`・`HOME=` が見えることを条件にし、
  見えない形（macOS のプラットフォームのバイナリ——`/bin/sleep` に `env CLAUDE_CODE_OAUTH_TOKEN=…` で起こしても環境が出なかった）を「判定できない」に倒した。陽性側は
  Homebrew の `python3` を同じ形で起こして名前が出ることを見た。(b) 引数に書かれた `NAME=` を環境と読む——`ps ww` の出力を前から外して切り出し、試料 940 で当てた

## 手順 8

### 振り分け（`references/found-lines.md`。線 `周の途中の課題 = 外に出す`）

| 指摘 | 振り分けと理由 |
| --- | --- |
| CR1・R2-1: cruise `references/child-process.md` の「子は親の環境変数を継ぐ——同じトークンで回る」が 2.1.316 の観測と食い違う（`child-cycle.py` は子の環境を Bash の環境から作る） | **直す（起票の候補）**——利用者に見える誤り（書いてあるとおりに長期トークンの親で子を回すと、子は 8 時間のログインで回りうる）。PR コメントに起票の候補として書く。不在のため起票の承認は訊いていない |
| CR3: `ps` で親を辿れない環境で、要対処が判定できないになり訊かれない | 記録だけ——受入基準 3 どおり。実際の利用（macOS の手元）でまず起きない |
| CR4: npm の導入で `argv[0]` が `node` | 記録だけ——まず起きない（手元はネイティブの導入） |
| CR5: 祖先を 2 度辿る（効率） | 捨てる——誤りではない |
| CR6: docstring の傍証が hook の子 | 記録だけ——判定は変わらない。記述の精度 |
| CR7: 親の pid が 0・1 | 捨てる——そう回さない |

- 焼き戻し: 学びは docstring・docs・cruise §3 の 3 に入れた（Bash の `env` で認証を判断しない）。ほかに焼き戻す学びなし
- この周の起票: 0 件（直すの 1 件（CR1・R2-1）は起票の候補として PR コメントに書いた。不在の周なので承認を訊いておらず、起票していない）
