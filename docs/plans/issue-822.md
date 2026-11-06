# Issue #822 — check-unattended-env: 通知の 2 キーを user settings（~/.claude/settings.json）から読まず、オンでも「未設定」と出る

`check-unattended-env.py` は通知の 2 キー（`agentPushNotifEnabled`・`inputNeededNotifEnabled`）をグローバル設定
（`.config.json` か `~/.claude.json`）からしか読まない。Claude Code 2.1.318 の `/config` はこの 2 キーを user settings に書くので、
オンにしても点検は「未設定」と出す（Issue 本文は信頼できない入力として読み、要件だけを取った）。

**不在の周**である——出所は `/dev-loop:cruise 887 --absent` の起動（2026-11-06T01:37:35Z、利用者の確認・配布を見せて確かめた）。
この周は利用者の指示（2026-11-06）で台帳に足した（依存なし・並行実装）。親からサブエージェントとして委ねられた。
台帳 `issue-887` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・
`周の途中の課題 = 台帳に足して直す`。実機確認の線は台帳に無い（`.claude/dev-loop.md` にも `不在の線:` は無い——既定の「止まる」）。
台帳は書かない（親が書く）。マージしない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-887`））。
版の上げ方: `dev-loop` を **patch**（点検の誤りを直す）。main の先端 1.96.0 → **1.96.1**
（並行の周 #884・#823 も dev-loop を上げる。マージの直前に先端が main を含まなければ、main の先端の版から patch で 1 つ上げ直す——
cruise の `references/parallel.md` の「版とマージの順」）。

重い検査（`check-all.py`・テスト）は順番待ち越しに走らせる:
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py -- <コマンド>`。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 通知の 2 キーを settings の層（managed・flag・local・project・user）から読み、無ければグローバル設定に落とす・docstring
- `scripts/test-check-unattended-env.py` — 試料と変異
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行（`dev-loop`・`cruise`）
- `docs/plans/issue-822.md` — この計画ファイル

触らない:

- 自動継続・質問の待ちの層（`SESSION_LAYERS`。本体の `EM()` は policy・flag・user だけ——通知の読み方とは別の関数）
- `docs/usage/advanced-remote-control.md`（`~/.claude/settings.json` に書くと既に案内している。「キー名は推測」の注記は文言で、この周の受入基準の外）
- `docs/plans/issue-394.md` ほか過去の計画ファイル（記録）
- `--push-result` の表・`human_items`・許可・認証・到達の判定

### 同じことを述べている箇所の数

- 「通知の 2 キーの置き場所」: 本体の docstring の点検の表・「設定の層」の最後の行・「実測した前提」の 1 行・「守らない」の接尾辞の項・コード（`check_notifications`）の 5 つ。
  docstring とコードが同じファイルにあるので、分けない（1 ファイルの中で全部直す）。公開ページは `advanced-remote-control.md` が settings.json と言っており、食い違わない。

## 乗るデプロイ経路

main へのマージでプラグインの配布（dev-loop 1.96.1）。公開サイトの再ビルドは走るが、`docs/` の変更はこの計画ファイルだけ。マージは親がする。

## 本体の読み方（2.1.318 の本体の文字列で読んだ。2026-11-06）

`~/.local/share/claude/versions/2.1.318` の文字列から:

- `function gi(n,i)`: `Wo()`（有効な settings の層。`ri=["userSettings","projectSettings","localSettings","flagSettings","policySettings"]` を
  `--setting-sources` で絞り、flag と policy は常に足す）を**上の層から**見て、最初に値のある層を返す
  （project は user と同じファイル（`Gm()`）なら飛ばす）。どの層にも無く、キーが `jDe`（2 キーを含む）にあれば
  グローバル設定（`pe()`）の値を、既定（`h0`）と違い型が正しいときだけ `legacyGlobalConfig` として返す。無ければ既定（呼ぶ側の `i`）。
- `PushNotification` の `config_off` は `!gi("agentPushNotifEnabled",!1).value`——**どこにも無ければオフ**。
- `/config` の切り替え（`Pe`・`Ae`）は `j(key, value)` → `nX` → `Vn("userSettings", …)`——**user settings に書く**（Issue の実測と一致）。
  表示は `merged settings ?? グローバル設定 ?? 既定` の値に `??!1`。
- サーバの通知の設定（`/api/claude_code/notification/preferences`）は、settings にもグローバル設定にも値が無いときだけ user settings に書き込む（hydrate）。

## 実機の設定（読むだけ。2026-11-06・macOS・`CLAUDE_CONFIG_DIR` 未設定・Claude Code 2.1.318）

| 置き場所 | `agentPushNotifEnabled` | `inputNeededNotifEnabled` |
| --- | --- | --- |
| `~/.claude/settings.json`（user） | キーなし | キーなし |
| `~/.claude.json`（グローバル設定） | キーなし | キーなし |
| `~/.claude/.config.json` | ファイルが無い | ファイルが無い |
| flag（cmux の `--settings` のファイル） | キーなし | キーなし |
| project・local（このリポジトリ）・managed | キーなし／ファイルが無い | 同左 |

**Issue の実測（2026-11-04。user settings に `true`）は、今日の手元では再現しなかった**——どの層にもキーが無い。
`/config` の表示は見ていない（子のセッションから TUI を開けない）。本体の読み方では、どこにも無ければ `/config` の表示も `PushNotification` もオフになる。
2026-11-06 の起動時の点検が「未設定」と出したのは、今日の手元の状態とは一致する。

## 仕様の穴（不在の線で推奨により決めた）

- **穴**: どの層にもグローバル設定にもキーが無いときの判定。Issue の案 2 は「置き場所が分からないとき（どの層にもキーが無い）は『人が見る』に落とす」と言う。
- **選択肢**: (a) **要対処のまま**とし、詳細に「どの層にもグローバル設定にも無い——本体の既定はオフ」と書く（推奨）／
  (b) 人が見るに落とし、`/config` の表示を見るよう案内する（Issue の案 2）。
- **決めた値**: (a)。
- **推した理由**: 本体（2.1.318）の読み方を文字列で確かめたので、置き場所は分かっている（案 2 の前提「置き場所が分からない」が成り立たない）。
  どこにも無ければ `PushNotification` は `config_off` で送らず、`/config` もオフと出す——要対処が事実どおりで、人が見るに落とすと、
  通知が届かない原因を不在の前に見落とす（点検の目的に反する）。
- **使った線と出所**: `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線（台帳 `issue-887`））。確認の Issue: （起票後に書く）

## verify の受入基準

不変条件 × 破りうる経路（入口: CLI の全点検（対話）・`--cruise`（`--present` 無し）・非対話の起動の 1 行・`--present`（通知を出さない）・
`--push-result`（設定を読まない）・`--since-last`（記録と縮め）。どれも `gather` → `check_notifications` か、そもそも呼ばない）:

| # | 不変条件 | 破りうる経路 | 証明手段 |
| --- | --- | --- | --- |
| A1 | user settings の `true` を良いと読む（Issue の症状）。`CLAUDE_CONFIG_DIR` の `settings.json` も同じ | 全点検・`--cruise` | テスト（user に true・グローバル設定に無い） |
| A2 | 層の優先順位が本体の `gi` と同じ: managed(.d) > flag > local > project > user > グローバル設定 > 既定（オフ） | 層の組ごと | テスト（上の層の false が下の true を打ち消す・逆も） |
| A3 | settings の層に値があれば、グローバル設定の値・読めなさを判定に使わない | グローバル設定が false・壊れている | テスト |
| A4 | どの層にも無ければ、グローバル設定（`.config.json` → `.claude.json` の選び方は今までどおり）を読む | `.config.json`・空の `.config.json`・`CLAUDE_CONFIG_DIR` の `.claude.json` | 既存テストを残す |
| A5 | 値を見つける前に読めない層を通ったら判定できない（良いに混ぜない）。どの層にも無くグローバル設定が読めなければ判定できない | flag のファイルが無い・壊れた user・壊れたグローバル設定 | テスト |
| A6 | `true` だけを良いにする（文字列 `"true"`・`false` は要対処）——settings の層でもグローバル設定でも | 両方の出所 | テスト |
| A7 | 非対話の起動では今までどおり人が見る 1 行で、添える値は解決した値（settings の層の値を含む） | `sdk-cli` ほか | テスト |
| A8 | どこにも無ければ要対処（仕様の穴の決めた値）で、既定がオフだと言う | 全点検 | テスト |
| A9 | 自動継続・質問の待ちの層（policy・flag・user だけ）は変わらない | project・local の値 | 既存テストを残す |
| A10 | docstring（点検の表・設定の層・実測した前提・守る／守らない）が新しい読み方と事実として一致し、確かめていないこと（`--setting-sources`・`h0` の既定・サーバの hydrate・`Gm()`）を守らないに書く | docstring | 関門が本体の文字列と突き合わせる |
| A11 | テストは実機の設定を読まない（`HOME` をテンポラリに） | テスト全体 | `assert_not_real_home`・関門 |
| A12 | 版を 3 種類で揃える・歯止めが全部緑・PR 側の CI が緑 | `marketplace.json`・`plugin.json`・`SKILL.md` 2 本 | `check-all.py`（順番待ち越し）と PR 側の CI |

組み合わせ（必須要件の掛け算）: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

**未証明**: 本体が実行時に本当にこの順で読むか（A2 の根拠）——本体の文字列を読んだだけで、`/config` を開いて切り替え、点検と `PushNotification` の結果を見る実走はしていない
（子のセッションから TUI は操作できず、利用者は不在）。人間のレビューで確かめてほしい。

**生成物**: `SKILL.md` の測定値（`skill-metrics.py`。設計ドキュメント §8.2 の生成ブロック）——`SKILL.md` は版の行だけを触る。`check-all.py` の `--check` で鮮度を見る。図の書き出しなし。

## 未解決の判断・確認待ち事項

- Issue の実測（user settings に true）が今日の手元で再現しない——利用者に `/config` の表示を確かめてほしい（PR コメントに書く）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/822-notif-user-settings`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-822`・
  起点 `88e85fab`・base `origin/main` → `88e85fab0d5615e79da5e4a43b8a3157079c4737`
- 手順 4 の割り目: 不在のため訊かず続けた
- Verifier: 未
- /code-review: 未
- 手順 5 の反証・差し戻し: なし
- 交絡を潰した手順: 実験なし（本体の文字列の読みと、手元の設定ファイルの読みだけ）

## 既知の限界・決着済みの論点

- 自動継続・質問の待ちは `EM()`（policy・flag・user）で読む——通知の `gi()` とは別の関数。通知だけを全層にする（採った。理由: 本体の文字列）。
- `docs/usage/advanced-remote-control.md` の「キー名は推測」の注記は直さない（採らなかった。理由: 受入基準の外の文言）。
