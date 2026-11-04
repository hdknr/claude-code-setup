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
- 関門: 未着手
- 反証と差し戻し: なし
- 交絡を潰した手順: 未

## 既知の限界・決着済みの論点

- Issue の 2（`check-unattended-env.py` の認証の方式）は #584 で済んでいる——この周では触らない（採った。理由: main の点検が既に「認証」を出す）
- `oauth_org_not_allowed`・`account_on_hold` を認証の失敗に含めない（採らなかった。理由: `/login` で直る値ではない）

## 手順 8（経験の還元）

- この周の起票: 0 件（未定。周の途中の課題は found-lines.md の振り分けで PR コメントに残す）
