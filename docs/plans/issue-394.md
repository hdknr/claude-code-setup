# Issue #394 — dev-loop: 利用者が不在になる前の環境点検（#389 の要件候補 6）

利用者が不在になる前に 1 度だけ回す**点検のスクリプト**を dev-loop に足す。**直さない・書き換えない**——
何が足りないかと、どう直すかを出すだけ。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 新規。点検の本体（標準ライブラリのみ・読むだけ）
- `scripts/test-check-unattended-env.py` — 新規。一時 `HOME` と偽の `pmset`/`ps` で当てる回帰テスト（変異テストを含む）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 「待ち時間・定時処理は別スキル」にスクリプトを指す 1 項。版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.46.0 → 1.47.0。道具の追加なので minor）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `scripts/check-all.py` — `TESTS` に足す
- `.github/workflows/plugins.yml` — テストのステップを足す
- `CLAUDE.md` — `scripts/` の一覧に足す
- `docs/plans/issue-394.md` — この計画

触らない:

- 設定を直すこと（`--fix` は作らない）——利用者の設定を書き換える道具は、不在の前に回すものとしては危険が勝る
- 要件候補 1〜5・7（#390〜#393・#395）。オートクルーズの手順そのもの
- `merge-pr.py`（#389 の周が並行して作っている。未マージ）
- Linux・Windows のスリープ点検（「判定できない」と出す）

### 同じことを述べている箇所の数

- 「点検の項目・判定・終了コード」: スクリプトの docstring（**正**）・`SKILL.md` の 1 項（指すだけ）・`CLAUDE.md` の一覧の 1 行（指すだけ）—— 3 箇所。
  **列挙は docstring だけに置く。** 分けない理由: 道具 1 本とその入口なので分けようがない。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` は main への push で Pages に載る（§8.2 の生成ブロック）。

## 実測した前提（2026-10-25・Claude Code 2.1.310・macOS）

本体（`~/.local/share/claude/versions/2.1.310`）の文字列から:

- `autoContinueAtUsageLimit`: settings の真偽値。説明「When a claude.ai usage limit stops your session, wait for the limit to reset and continue the task automatically」。**未設定のときの既定は、別の条件で決まる式**（`aZt() ?? e==="absent"`）で、文字列からは読み切れない → **明示を求める**
- `askUserQuestionTimeout`: settings の列挙 `60s` `5m` `10m` `never`。「Defaults to never」
- `agentPushNotifEnabled`（`/config` の「Push when Claude decides」）・`inputNeededNotifEnabled`（「Push when actions required」）: `~/.claude.json`（globalConfig）。既定 false。`config_off` のとき `PushNotification` は「mobile push is disabled in /config」で送らない
- 「No mobile registered」はサーバ側の `has_active_channel` で出る → **手元のファイルからは判定できない**（人が見る）
- `remoteControlAtStartup`: settings
- **スリープ**: 走っている各 `claude` が子として `caffeinate -i -t 300` を張っている（`ps` で 5 本確認）。**`pmset -g assertions` の `PreventUserIdleSystemSleep 1` は Claude 自身が作業中に作るもの**で、待機中に保たれる根拠にならない（**交絡**）。`pmset -g custom` は電源ごとに `sleep` を持つ（このホストは AC 0・バッテリー 1）
- `--settings` で渡す設定（flag 層）: cmux は `claude --settings <file>` で起動する。祖先の `claude` のコマンドラインから拾う

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | 各項目は **良い／要対処／判定できない／人が見る** のどれかで出し、**読めなかったものを「良い」に混ぜない** | 設定ファイルが無い（→ 未設定として扱う。失敗ではない）／JSON が壊れている（→ 判定できない）／`pmset`・`ps` が無い・失敗 | 読み込みの失敗を値と別の型で返す |
| 2 | **設定の層の優先順位**は managed > flag（`--settings`）> local > project > user | user が true で local が false／flag の file にだけある／managed にある | 層を順に重ねる 1 関数 |
| 3 | **終了コード**: 要対処があれば 1、無くて判定できないがあれば 2、それ以外 0。**人が見るは終了コードに効かず、常に出す** | 人が見るだけの項目で 0 以外になる／判定できないを 0 にする | 集計の 1 関数 |
| 4 | **許可**: 名指しのコマンドごとに、deny に当たれば要対処（allow があっても）、allow に当たるか `bypassPermissions` なら良い、それ以外は要対処 | deny と allow の両方に当たる／`Bash`・`Bash(*)` の全許可／`Bash(git push:*)` と `Bash(git push *)` の 2 つの書式／層をまたぐ（user の allow と local の deny） | 照合は近似と明記（docstring）し、書式 2 つと全許可を当てる |
| 5 | **スリープ**: Claude 自身の `caffeinate -t` を「防止されている」の根拠にしない。良いのは、いまの電源の `sleep` が 0 か、`-t` の無い `caffeinate` が在るとき。**蓋を閉じる・電源が変わる**は常に人が見る | 作業中の `caffeinate -i -t 300` だけがある（→ 要対処）／macOS 以外（→ 判定できない） | `pmset -g custom` と `ps` を読む |
| 6 | **実環境を書き換えない** | 本体が書く／テストが実 `HOME` を読む・書く | 本体に書き込みの呼び出しを置かない。テストは一時 `HOME` と偽のコマンドで、実 `HOME` を対象にしないことをアサート |
| 7 | 自動継続・質問のタイムアウト・通知の 2 つ: **未設定は要対処**（`askUserQuestionTimeout: never` も要対処） | 未設定／`never`／false／型違い（文字列 `"true"`） | 値の検査は厳密に `is True`・列挙の照合 |
| 8 | **docstring の事実（キー名・値の範囲・保存先）が 2.1.310 の本体と一致する** | 記憶で書いたキー名の誤り | 本体の文字列で当てる（Verifier にも当てさせる） |
| 9 | 版の 3 箇所・`skill-metrics.py --check`・`check-all.py`・CI のステップ・`CLAUDE.md` の一覧が揃う | 登録漏れ | `check-all.py`（`test-check-all.py` が収録漏れを見る） |

### 必須要件の掛け算

- 受入基準を Verifier × 1 パス目・2 パス目、`/code-review` × 1 パス目・2 パス目の 4 つに渡す。

### この環境では証明できないもの（未証明）

- **これらの設定で、利用者不在の周が実際に止まらないこと**（数時間の無人運転・利用上限の待機・通知の到達）——1 周の検証では回せない。PR コメントで人間に申告する。
- **managed settings をサーバから配る形**（ファイルに無い）——このホストに無い。
- **2.1.310 以外の版でキー名が同じであること**。

### 生成物

- 該当あり: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を触るので）。`python3 scripts/skill-metrics.py --check` が 0 であること。
- 図: 触らない（drawio の変更なし）。

## 未解決の判断

- なし（スクリプトの形・名前・「直さない」は、この計画で決めた）。

## 周の在り処

- ブランチ: `issue/394-cruise-env-check`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-394`
- 起点: `0330977`（Merge pull request #401）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `0330977fc31ed62314e1dbb8c16f876b946d8e46`

## 関門の進捗（再開点）

- 実装: 未着手
- Verifier: 未
- `/code-review`: 未
- 反証・差し戻し: なし
- 交絡を潰した手順: スリープの点検で、Claude 自身の `caffeinate -t 300` が「防止されている」を作る交絡を見つけ、判定から外した（上の「実測した前提」）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 設定を直す `--fix` | 採らない | 不在の前に利用者の設定を書き換える道具は危険が勝る。直し方を出すだけにする |
| モバイルの登録 | 人が見る | サーバ側の状態で、手元のファイルに無い |
| 許可ルールの照合 | 近似 | ハーネスの照合器が正。書式 2 つと全許可だけを当て、docstring に限界を書く |
