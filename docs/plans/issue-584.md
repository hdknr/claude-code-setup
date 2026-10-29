# Issue #584 — cruise を長期トークン（`claude setup-token`）で起動する手順と起動口

Mac Studio で、キーチェーンの対話ログインの OAuth（8 時間）が切れて不在の cruise が毎朝 401 で止まっていた。
長期トークンで cruise を起動する手順（docs）・起動口（ラッパー）・`check-unattended-env.py` の認証の判定を足し、
長期トークンで使えない機能を測る段取りを置く。#473（認証切れを cruise の停止として扱う）とは、
`check-unattended-env.py` の認証の項目（#473 の 2）で重なる——**この周はその項目を入れ、#473 の 1・3（hook の文言・401 の再開）は触らない**。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/launch-with-long-token.sh` — 新規。起動口（キーチェーンからトークンを読んで `claude` を起動。無ければ理由を出して止まる。`--store-token`（入れる・入れ替える）・`--status`・`--account <名前>`——利用者の指示 1・2 で足した）
- `plugins/dev-loop/skills/cruise/SKILL.md` — §3 に「3. 認証——長期トークンで回すかを訊く」（利用者の指示 1 で足した）
- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 認証の項目（長期トークン／8 時間のトークン／ほかの認証／判定できない）と docstring
- `scripts/test-check-unattended-env.py` — 認証の項目のシナリオと変異
- `scripts/test-launch-with-long-token.py` — 新規。起動口の回帰テスト（偽の `security`・`claude`・`uname`。変異テストを含む）
- `scripts/check-all.py` — `TESTS` に登録
- `.github/workflows/plugins.yml` — テストのステップを登録
- `docs/usage/cruise-long-lived-token.md` — 新規。手順・起動口・確かめていないこと・測り方
- `docs/plugins/dev-loop-cruise.md` — 部品の一覧と「2. 環境を点検する」から指す
- `mkdocs.yml` — nav に足す
- `CLAUDE.md` — `scripts/` の一覧に 1 行（テスト）
- `.claude-plugin/marketplace.json`・`plugins/dev-loop/.claude-plugin/plugin.json`・`plugins/dev-loop/skills/dev-loop/SKILL.md`・`plugins/dev-loop/skills/cruise/SKILL.md` — 版（3 種類）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ）
- `docs/plans/issue-584.md` — この計画

触らない:

- `scripts/record-stop-failure.py`（#473 の 1）・`references/ledger.md`（#473 の 3）
- 利用者のキーチェーン・settings・`~/.claude`（読むのも書くのも利用者。テストは偽物で当てる）
- dev-loop の `SKILL.md` の本文（版の 2 行だけ）
- 週の上限に当たったときの切り替えの促し（利用者の指示 2・3）——別の Issue に分ける（下の「利用者の指示」）
- 長期トークンを使う既定の切り替え（全セッションに効かせない——Issue の 1）

### 同じことを述べている箇所の数

- 「長期トークンで使えない機能」: 本体の docstring（本体の文字列で読んだ事実）・docs の新ページ（測る表）の 2 箇所。
  点検の出力は列挙を持たず docs を指す。分けない理由: docstring は点検の根拠、docs は利用者が測って埋める表で、役目が違う
- 「起動口が何をし、何で止まるか」: 起動口の冒頭のコメント・docs の新ページの 2 箇所。docs は起動口のコメントを正とすると書き、要点だけ
- 認証の判定の表: 本体の docstring 1 箇所（docs は指すだけ）

## 乗るデプロイ経路

`docs/` は main への push で GitHub Pages に出る。`plugins/dev-loop` は main へのマージでプラグインの新しい版として配られる（版を上げる）。
起動口は利用者が手で打つスクリプトで、hooks・MCP には登録しない。

## 周の在り処

- ブランチ: `issue/584-cruise-long-lived-token`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-584`
- 起点: `4abb280`（start-point `origin/main`）
- base: `4abb280dda86eac24190df155e9196f6c0fbb730`

## 線（出所）

- 直す線: `既定`（cruise の確かめた線（台帳 `issue-474`））
- 仕様の穴 = 推奨で決めて起票・マージ = 関門を通ればマージ・周の途中の課題 = 台帳に足して直す（同じく台帳 `issue-474`。利用者の確認 2026-10-27T09:07:27Z・2026-10-28T07:24:46Z・2026-10-28T23:56:17Z「配布を見せて確かめた」）
- 利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る行（狭いパスの指摘を含む）は推奨で決めて `要確認` の Issue を立てる（#565・#561 の形）
- `実機確認` の線は台帳に無い——既定の `止まる`（実機の要る基準は BLOCKED、周は閉じない）
- 周の途中の課題は親が起票する（親の指示。この周は台帳を書かない）

## 利用者の指示（周の途中。親から伝達）

1. 2026-10-29「cruise を開始するときに long-lived token を使うかを尋ね、必要であれば long-lived token の設定/更新を行う様にできますか？」
   → この周に入れた: 点検の「認証」を `--present` でも出す（8 時間は人が見る）・cruise §3 の 3 で訊く・起動口の `--store-token`（別の端末で、プロンプトに貼る。
   セッションの中では止まる）・`--status`（入れた日時だけ。期限は読めないので作らない）。動いているセッションは切り替えられない——訊いたあとはコマンドを見せて周を始めずに止まる。
   `--absent` の再開では訊かない。`claude setup-token` の出力を取り込めるかは測っていない（取り込まない形にした）
2. 2026-10-29「weekly リミットされていると待ち時間が長期になるので、リミットが近ければアカウントスイッチする様に促す様にして。」
3. 2026-10-29「weekly リミットが来てから 2 時間以内に回復できなそうであれば、アカウントスイッチさせる様に」（2 を置き換える）
   → この周に入れたのは起動口の `--account <名前>`（アカウントごとのキーチェーンの項目）だけ。**上限に当たったときの判定と促し（hook の通知・cruise の止まり方）は
   推奨で別の Issue に分ける**（#584 の受入基準の外で、`scripts/record-stop-failure.py`（#473 の 1 と同じ場所）と cruise の再開を触るため）。題と本文は親に渡す。
   証拠: 記録の `rate_limit` のレコードの `quotaLimits.resetsAt`（`scripts/count-usage-limit-resumes.py`）、表示「You've hit your weekly limit · resets Oct 31 at 9pm (Asia/Tokyo)」
   （この周の子が 2026-10-29 に当たった。HTTP 429）。上限の手前の信号として、statusline の入力 JSON の `rate_limits.seven_day.used_percentage`・`resets_at` が本体の文字列にある（2.1.312）

## 受入基準

不変条件 × 経路:

1. **起動口はキーチェーンのトークンを `CLAUDE_CODE_OAUTH_TOKEN` に入れて `claude` を起動し、引数をそのまま渡す。トークンを出力に出さない**
   - 経路: 通常／空白を含む引数／環境に別の `CLAUDE_CODE_OAUTH_TOKEN` が既にある（キーチェーンの値で上書き）／標準出力・標準エラー
2. **トークンが無いとき、起動口は理由を出して止まり、`claude` を起動しない（対話ログインのまま起動しない）**
   - 経路: キーチェーンに項目が無い（`security` が非 0）／値が空／`security` が無い／macOS でない
3. **長期トークンより先に使われる認証が環境にあれば、起動口は止まる**——`ANTHROPIC_API_KEY`・`ANTHROPIC_AUTH_TOKEN`
   （本体の文字列で、`ANTHROPIC_AUTH_TOKEN` は `CLAUDE_CODE_OAUTH_TOKEN` より先、承認済みの API キーは OAuth より先に使われる）
4. **`check-unattended-env.py` は長期トークンと 8 時間のトークンを区別して出す**（`--present` でも出し、8 時間は人が見る）
   - `CLAUDE_CODE_OAUTH_TOKEN` が空でない → 良い（長期トークン）。その行の添え書きに、長期トークンで使えない見込みの機能と docs の測る表
   - どれも無い → 要対処（不在）／人が見る（`--present`）（対話ログインの OAuth は 8 時間で切れる）。直し方に起動口の絶対パス・`--store-token`・docs
   - `ANTHROPIC_API_KEY`・`ANTHROPIC_AUTH_TOKEN`・`apiKeyHelper` がある → 人が見る（どれで認証しているかは `/status`）
   - Claude Code のセッションの外（`CLAUDECODE` が `1` でない）・サブプロセスの環境の消去（`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`／`GITHUB_ACTIONS`）が効く → 判定できない
   - トークンの値を出力に出さない
5. **テストは実環境を読まない・書かない**——偽の `security`・`claude`・`uname` を `PATH` の先頭に置き、本物のキーチェーンに届かない（偽物が呼ばれたことを陽性対照で見る）
6. **docs**: 手順（`claude setup-token`・キーチェーンに入れる（`-w` を最後に置いて入力させる——シェルの履歴に残さない）・`.zshrc`・`.env`・リポジトリに置かない・cruise の端末だけ）、起動口の使い方、
   **確かめていないこと**（8 時間を超えて止まらないこと・機能の可否）を確かめていないと書く。本体の文字列から読んだ見込みは「見込み（実測していない）」と書き、「動く」とは書かない。測り方のコマンド。
   cruise のページから指す。`mkdocs build --strict` が通る
7. **登録**: `check-all.py` の `TESTS`・`plugins.yml`・`CLAUDE.md`。`test-check-all.py` が緑
8. **版**: dev-loop を main（1.63.8）より上に、3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本の 2 行）。`skill-metrics.py --check` が緑

9. **（利用者の指示 1）cruise の起動時に、8 時間のトークンなら長期トークンで回すかを訊く**——新規の起動・居る再開で訊き、`--absent` の再開では訊かない。
   長期トークンを選んだら入れ方と起動し直すコマンドを見せて周を始めずに止まる。トークンの値を会話に通さない（`setup-token` を Bash・`!` で打たせない）
10. **（利用者の指示 1）`--store-token` は値をプロンプトで入れ（`-w` を最後・`-U`）、セッションの中（`CLAUDECODE=1`）では止まる。`--status` は値を読まない（`-w` なし）**
11. **（利用者の指示 3）`--account <名前>` でアカウントごとの項目（`claude-long-token-<名前>`）を使う。名前を検める。案内にも付ける**

掛け算: 受入基準を Verifier と `/code-review` に × 1 パス目・2 パス目（2 パス目が該当なしなら 1 パス目の 2 つ）。

### 証明できるもの／できないもの

- 証明できる: 1〜8（テスト・`check-all.py`・`mkdocs build`）
- **BLOCKED（道具が無い——長期トークン。発行は利用者の対話の操作 `claude setup-token`）**:
    - B1 Issue の受入基準「長期トークンで起動した cruise が、起動から 8 時間を超えても 401 で止まらない」
    - B2 Issue の受入基準「4 で動かなかった機能を docs に挙げる」——測る表は置き、本体の文字列の見込みを書くが、**実測の欄は空**
    - B3 点検が、実際に長期トークンで起動したセッションの中で「良い」と出ること（本体の文字列では Bash の子に `CLAUDE_CODE_OAUTH_TOKEN` が渡る——消去は `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`・GitHub Actions のときだけ——が、陽性対照を取っていない）
- 未証明: なし（B1〜B3 は手段があれば消える）

## 生成物

- §8.2 の生成ブロック（`skill-metrics.py --check`）——`SKILL.md` の版の行を変えるので該当。鮮度を受入基準 8 に入れる
- 図: なし

## 未解決・確認待ち

- B1〜B3（利用者の操作待ち。PR は `Refs #584`——Issue を閉じない）

## 関門の進捗（再開点）

- 実装: 済み（`82666dd`）。割り目 1: 不在のため訊かず続けた
- 1 パス目の指摘対応の起点: `82666dd`（1 パス目の関門に渡した時点の HEAD）
- 実験: 本体の文字列の読み取り（2.1.312）だけ。交絡: 文字列は版に依る——版を docstring・docs に書く。実走の陽性対照は B3

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 8 時間のトークンをキーチェーンの中身で見分けるか | 採らない——環境変数で見分ける | キーチェーンの値（秘密）を読まない。セッションの認証の出所は本体の優先順で決まり、環境に長期トークンが無く API キーの類も無ければ対話ログイン |
| 起動口を全セッションに効かせる（`.zshrc` に書く）か | 採らない | Issue の 1。1 年有効のトークンを全プロセスに配らない |
| 点検を居る cruise（`--present`）でも出すか | 出す（8 時間は人が見る） | 利用者の指示 1——起動時に長期トークンで回すかを訊くため。居れば `/login` で戻れるので要対処にはしない |
| 週の上限の切り替えの促しをこの周で入れるか | 入れない——起動口の `--account` だけ | 利用者の指示 2・3。#584 の受入基準の外で、hook と cruise の再開に触る。別の Issue（推奨で決めた） |

## 手順 8

- この周の起票: 0 件（周の途中の課題は親が起票する——親の指示）
