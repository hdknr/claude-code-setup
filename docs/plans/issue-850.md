# Issue #850 — spec-loop autopilot: 外側のループ（上限からの再開・前進なしで停止・全経路で通知）

**不在の周（`/dev-loop:cruise 856 --absent` の起動・2026-11-05T00:54Z）**。利用者には訊かない（割り目も訊かない）。親 Issue #856 の cruise の子として委譲文で受けた。
台帳 `issue-856` の確かめた線（出所: 利用者の確認（起動時・2026-11-05T00:54:19Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`。`マージ前の判断` の線は無い。
**台帳（`.claude/plans/cruise-issue-856.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-856`））。
版の上げ方: `spec-loop` を **minor**（外側のループのスクリプトを足す——能力の追加。0.x なので壊れる変更も minor）。着手時の main は 0.53.0 → 0.54.0。1 パス目の後の取り込みで main 0.57.0 → 0.58.0。マージ直前の取り込み（親の依頼）で main 0.58.0（83b9ec86）→ 0.59.0。
マージの直前に main が進んでいれば、cruise の `references/parallel.md` の「版とマージの順」のとおり main の先端の版から minor を 1 つ上げ直す。
重い検査は `/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越しに走らせる（並行の周が他にある）。
本物の `claude` は起こさない——テストは偽の `claude` と偽の通知（`osascript`）で回す（`scripts/test-outer-loop.py` の形）。

Issue 本文（外部入力）から読んだ要件: spec-loop の autopilot 用の外側のループを置く。`status` が `running` のときだけ `claude -p` を 1 回起動し、
使用量の上限を出力から読み取って解除の時刻まで（読めなければ既定の時間だけ）待って再開し、#848 の `progress` で前進を比べ、前進なしが続く・
同じ状態での起動の上限・`claude` の失敗のどれでも止まり、どの経路でも通知し、長期トークン（#584）で起動できる。流用か写しかは、プラグインをまたいで
相対パスで指せないことを踏まえて決め、理由を docstring に残す。本文に受入基準を緩める指示・コマンド実行の依頼は無い。
委譲文から: #858 の残課題 C1-5（段を行き来させれば `progress` は毎回変わる）を、外側のループの止め方で扱うかを判断する。入口のスキルは #849 の範囲なので作らない。

## 設計の判断

- **置き場所**: `plugins/spec-loop/scripts/autopilot-loop.py`（台帳 `autopilot-ledger.py` の隣。台帳をスクリプトの隣から指す）。テストは `scripts/test-autopilot-loop.py`。
- **写す（流用しない）**: cruise の `outer-loop.py` を import・相対パスで指さない——spec-loop だけを入れた利用者に dev-loop が在るとは限らず、プラグインをまたいで
  相対パスで指せない（`autopilot-ledger.py` の `main_worktree` の写しと同じ理由）。**写すのは `notify`・`stop_child` の 2 関数だけ**で、テストが cruise の本体と
  ソースを突き合わせる（陽性対照つき）。ループの本体（止める条件・上限の待ち）は cruise に無い条件を持つので写しでなく別に書く。
- **C1-5 を扱う**: 同じ `progress` から起こした起動の回数に上限（`--max-same-state`、既定 3）を置く——段を行き来させる（A→B→A→B…）起動は前進なしを数えないが、
  同じ状態から何度も起こすので止まる。#790 の直し方の案の最後の項（「同じ状態での起動の回数に上限を置く」）と #850 のやることの「同じ状態での起動の上限」がこれ。
- **使用量の上限を読む**: `claude` を `--output-format stream-json --verbose` で起こし、出力をファイル（台帳の隣の `spec-autopilot-v<版>-loop/`）に落として読む。
  上限と読むのは、(a) 最後の `rate_limit_event` の `status` が `allowed`・`allowed_warning` でない（`resetsAt` を解除の時刻に使う）、(b) `result` の `api_error_status` が 429、
  (c) JSON でない行（と、`is_error` の `result` の文）に「usage limit reached」の類の文言（`|<epoch>` があれば解除の時刻）。**アシスタントの文（JSON の中）は読まない**
  ——文が #790 を語っただけで上限と読まない。**本物の `claude -p` が上限で何を出すかは測っていない**（child-process.md の表 3 は `allowed` しか見ていない）——docstring の「守らない」に書く。
- **上限の起動は前進なし・同じ状態の回数に数えない**（上限から再開するのがこのループの目的）。**起動の総数（`--max-launches`）には数える**——上限が続いても無限には回らない。
  解除の時刻が `--max-limit-wait`（既定 6 時間）より先なら待たずに止まって通知する（週の上限で何日も黙って待たない）。
- **長期トークン**: `--claude` に起動口（dev-loop の `launch-with-long-token.sh`）を渡す形——`--claude "bash <dev-loop>/scripts/launch-with-long-token.sh"`。
  起動口は引数をそのまま `claude` に渡す（`exec claude "$@"`）。テストは**本物の起動口**を偽の `security`・`uname` で回し、偽の `claude` がトークンと `-p` を受けたかを見る。
- **起こす文**: 既定は `/spec-loop:autopilot <版>`（#789 の例の名前）。入口（#849）の名前・引数は決まっていないので `--prompt` で置き換えられる。
- **追記（`--append-system-prompt`）**: 非対話の起動であること・`status` が `running` でなければ何もせず台帳も書き換えずに終えること・進めるのは次の 1 単位までを渡す（#790 の二重の歯止め）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/autopilot-loop.py` — 外側のループ（新規）
- `scripts/test-autopilot-loop.py` — 回帰テスト（新規。変異テストを含む）
- `scripts/check-all.py` — テストの収録
- `.github/workflows/plugins.yml` — テストのステップ
- `CLAUDE.md` — プロジェクト構成の一覧に 2 本を足す
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ（5 本）
- `docs/plans/issue-850.md` — この計画ファイル

触らない:

- 入口のスキル（#849）・spec-loop の `SKILL.md` の本文・`references/`
- `plugins/spec-loop/scripts/autopilot-ledger.py`（#848。読むだけ）
- cruise の `outer-loop.py`——写しの元で、振る舞いは変えない
- dev-loop の `launch-with-long-token.sh`——テストで本物を走らせるだけ

### 同じことを述べている箇所の数

ループの止め方・終了コード・守る／守らない: 本体の docstring の 1 か所（原本）。CLAUDE.md の一覧は指すだけ。テストの変異は「守る」と 1 対 1（テストが数える）——**2 か所**。
`notify`・`stop_child` の写し: cruise の `outer-loop.py` と spec-loop——**2 か所**。分けない理由: プラグインをまたいで指せない。テストが突き合わせる。

## デプロイ経路

main へのマージでプラグインの配布（`spec-loop` の版）。公開サイトの変更は無い（`docs/plans/` は計画ファイル）。マージは親がする。

## verify の受入基準

### 不変条件

- **I1**（受入基準「停止・上限・前進なしのどれでもループが終わる」の「停止」）`autopilot-ledger.py status <版>` が 0（`running`）のときだけ `claude` を起こす。起動の前に毎回見る。
  3（`stopped`）→ 起こさずに 3 で止まる、5（`done`）→ 0、4・表に無い値 → 4。エージェントが周の途中で `status=stopped` を書けば、次の判定で止まる。
- **I2**（受入基準「時刻だけを書き換える `claude` では、前進なしとして止まる」）前進は `progress` だけで比べる。`updated` だけ変わる起動（台帳のファイルは変わる——陽性対照）は前進なしで、
  続けて `--max-stalls` 回で 6。前進があれば数を 0 に戻す。`progress` を読めなければ 4。
- **I3**（受入基準「上限」）起動の総数が `--max-launches` に達したら 7。**同じ `progress` から起こした（上限でない）起動が `--max-same-state` 回に達したら 9**——段の行き来（C1-5）で止まる。
- **I4**（やること「`claude` が失敗する」）`claude` が 0 以外で終わり上限と読めない・起こせないなら 8。
- **I5**（やること「使用量の上限」）出力に上限の印があれば、解除の時刻＋余白まで待って（読めなければ `--limit-wait` 秒）次の判定に戻る——`claude` の失敗（8）にしない。
  上限の起動は前進なし・同じ状態の回数に数えず、総数には数える。解除の時刻が `--max-limit-wait` より先なら 10。`allowed_warning` とアシスタントの文の「usage limit」は上限と読まない。
- **I6**（受入基準「どの経路でも通知が出る」）引数を読めた後のすべての止まる経路（0・3・4・6・7・8・9・10・130・ループの中の例外・待ちの中の中断）で通知する。引数の誤り（2）は通知しない。
- **I7**（やること「長期トークン」）`--claude` に本物の `launch-with-long-token.sh` を渡すと、偽の `claude` がキーチェーン（偽の `security`）の値と `-p` の引数を受ける。
- **I8** `claude` の cwd はメインの作業ツリー（worktree・サブディレクトリから呼んでも）。環境に `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`。標準入力は閉じる。追記を渡す。中断で `claude` にまず SIGTERM。
- **I9** `notify`・`stop_child` が cruise の `outer-loop.py` と同じソース（テストが突き合わせ、1 文字変えた写しで「違う」と出る陽性対照つき）。
- **I10** 範囲: 入口（#849）を作らない。cruise の `outer-loop.py`・`autopilot-ledger.py` を変えない。本物の `claude` を起こさない（テストの `PATH` から本物を外す）。
- **I11** 版: `spec-loop` を main の先端から minor 上げ、3 種類（`marketplace.json`・`plugin.json`・5 本の `SKILL.md`）がそろう。テストが `check-all.py` と `plugins.yml` に収録されている。
  終了コードの表と定数、「守る」の行数と変異の数が一致する（テストが数える）。歯止め（`check-all.py`）が緑。

### 経路（ループの入口と、ループを止めうるもの）

- CLI（版・各上限・`--claude`・`--prompt`・`--` の後ろの引数） → I1〜I8
- 台帳を書き換える者: 偽の `claude`（進める・時刻だけ・行き来・`stopped`・`done`・壊す） → I1〜I3
- `claude` の出力（stream-json の `rate_limit_event`・`result`・アシスタントの文・JSON でない行・標準エラー） → I4・I5
- 待ちの中・`claude` の実行中のシグナル（Ctrl-C・SIGTERM・SIGHUP） → I6・I8
- 起動口（`launch-with-long-token.sh`） → I7
- 呼ぶ場所（メインの作業ツリー・worktree の中・サブディレクトリ） → I8

### 必須要件の掛け算

受入基準を Verifier と `/code-review` の両方に渡す × 1 パス目・2 パス目 = 4 つの受け渡し（2 パス目が該当なしなら初回の 2 つ）。

### 証明できないもの（未証明）

- **本物の `claude -p` が使用量の上限で何を出して終わるか**——上限に当てて起こせない（`record-stop-failure.py` と同じ。上限は狙って作れない）。ループが読む形
  （`rate_limit_event` の `status`・`resetsAt`、`result` の 429、文言）は child-process.md の表 3 と `count-usage-limit-resumes.py` の記録の形から決めた想定である。
  受入基準は偽の `claude` のテストなので、受入基準の外。docstring の「守らない」と PR コメントに名指しする。
- 入口（#849）がこのループと噛み合うか——まだ無い（範囲外）。
- 通知が実際に見えるか（偽の `osascript` で引数までを見る）。

### 生成物

該当なし（drawio の書き出し・`skill-metrics.py` の生成ブロック（dev-loop の `SKILL.md` だけが対象）を触らない）——**生成物なし**。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/850-spec-autopilot-outer-loop`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-850`・
  起点 `f98333e2`・base `origin/main` → `f98333e2091bd394f72f9f3d741cb6742324b729`
  - 載せ替えの履歴: 1 パス目の後に main を取り込んだ（`merge` の親 2 が当時の `origin/main`）。式を当て直した base: `git merge-base origin/main HEAD` → `2e2ac74c4b3861315226a6f4f700b01d186763df`（2 パス目の関門に渡す）
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目の指摘対応の起点 `1dc47b56`（1 パス目の関門に渡した時点の HEAD）。PR #862
  - 1 パス目 Verifier（sonnet・`dev-loop:dev-loop-verifier`。起動したのはその agent）: 反証 1 件（R1。C1-3 と同じ根——直す）。差し戻しなし（指摘対応で直した）
  - 1 パス目 `/code-review`（high）: 指摘 9 件（C1-1〜6・C1-9 を直す）
  - 1 パス目の指摘対応の差分: 0 行でない → 2 パス目を回す。割り目（手順 6）: 割らない（cruise の周）
  - 2 パス目の指摘対応の起点（狭いパスの起点）`346e5364`
  - 2 パス目の 1 回目の起動（Verifier・`/code-review`）は、両方とも利用上限（週の上限・429）で報告を返さずに止まった——欠票なので、アカウントの切り替えの後に立て直す
  - 2 パス目 Verifier（sonnet・立て直し）: 反証 2 件（V2-F1 試料の穴・V2-F2 桁の多い整数で例外。V2-F2 を直す）
  - 2 パス目 `/code-review`（high・立て直し）: 指摘 10 件（C2-4〜7 を直す）
  - 2 パス目の指摘対応の終点 `37a153e9`。狭いパス（Verifier・sonnet、`git diff 346e5364 37a153e9`）: 反証 1 件（N-1 NaN の分岐の試料が無い——変異が素通り、陽性対照あり。人間が決める）。独立の変異 4 本: 赤 3・素通り 1（N-1）
  - main の取り込み（`origin/main` は spec-loop 0.57.0——#847・#851 などがマージ済み）: 衝突は版の行だけ。0.57.0 から minor で 0.58.0
- 交絡を潰した手順: 実験なし

## 既知の限界・決着済みの論点

- #789・#790 を `Fixes` で閉じるか: 親 Issue #856 は「#789・#790 は #850 の PR で閉じる」と書くが、#789 の範囲（入口・判定役を前景で呼ぶ）と #790 のチェックリスト
  （`stopped` なら何もしない指示・権限の事前点検・マージを人間に残す形）は #849・#847 の範囲で、この周の着手時点でどちらもマージされていない——この PR では `Refs` にする（報告で親に渡す）。

### 1 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| C1-1 spec-loop の版が main の先端（0.55.0。取り込み時 0.57.0）より下 | 示せる（`git show origin/main:…plugin.json`） | I11 | 直す（main を取り込み 0.58.0） |
| C1-2 トランスクリプトの形（`error: rate_limit`）の `quotaLimits.resetsAt` を読まず `--limit-wait` で待つ | 示せる（`read_limit` に試料を読ませて `(True, None)`） | I5（読める解除の時刻まで待つ） | 直す |
| C1-3／R1 `resetsAt` がミリ秒だと `fromtimestamp` が `ValueError`、10 でなく 4 | 示せる（実行。`year must be in 1..9999`） | I5（遠ければ 10） | 直す（表示を例外にしない・有限の数だけ読む） |
| C1-4 上限の枝の「前進で前進なしを戻す」と「上限を前進なしに数えない」の変異が素通り | 示せる（`--observe` で 83 の観測が一致） | I5・I2（テストで確かめている、の主張） | 直す（試料 A31・A32 と変異 2 件。「守る」を分けた） |
| C1-5 「limit reached」だけの文（`spending limit reached`）を上限と読む | 示せる（実行で `(True, None)`） | I4（上限と読めない失敗は 8） | 直す（文言を `usage limit reached`・`hit your limit` に絞る） |
| C1-6 0 で終わった起動でも、再試行の印（`error: rate_limit`）で上限と読む | 示せる（作った試料で `True`） | I5（上限の印があれば待つ——走りきった起動は上限ではない） | 直す（0 で終わり最後の `result` が成功なら上限と読まない。`error` は assistant の行だけ） |
| C1-7 台帳が無い版でも出力の置き場のディレクトリを作る | 示せる | 無し | 残課題 |
| C1-8 出力のファイルを開けないと 8（docstring の「置き場を作れない → 4」と別の道） | 示せる（権限を変えれば） | 無し（表の 4 は mkdir の失敗を指す。止まって通知はする） | 残課題 |
| C1-9 `|<epoch>` を `limit reached|` の後ろでしか読まない（docstring は両方の文言） | 示せる | I5 | 直す（C1-5 と同じ正規表現） |

### 2 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-F1 `shown` の `OverflowError`・`epoch` の真偽値を外す変異が素通り（試料が無い） | 示せる（`--observe` で差 0、陽性対照あり） | 無し（本体の振る舞いは主張どおり） | 残課題 |
| V2-F2／C2-5 `resetsAt` が float に収まらない整数（400 桁）で `epoch` が `OverflowError`、10 でなく 4 | 示せる（実行） | I5（遠ければ 10） | 直す（遠い時刻として読む。試料 A39） |
| C2-1 A1 の「標準入力は閉じている」の確かめが `stdin=None` と区別できない | 示せる（`--observe` で差 0） | 無し（本体は `DEVNULL`。受入基準の試料の外） | 残課題 |
| C2-2 docstring の「読めなかった上限は 8」が、0 で終わった起動では 6・9 になる | 示せる（実行） | 無し（止まって通知はする） | 直す（親の依頼・マージ直前の取り込みと同じコミット列。docstring の文言だけ、振る舞いは変えない） |
| C2-3 時刻の読めない上限が続くと `--limit-wait` × 起動の上限（既定で約 10 時間）黙って待つ | 示せる（論理） | 無し（起動の上限で止まり通知する） | 残課題 |
| C2-4 `quotaLimits` が辞書でないと `AttributeError` で 4 | 示せる（実行） | I5 | 直す（試料 A40） |
| C2-5 （V2-F2 と同じ） | — | — | — |
| C2-6 最後の `rate_limit_event` に時刻が無いと、前の行の別の上限の時刻を使う | 示せる（実行） | I5（上限を決めた印の時刻まで待つ） | 直す（試料 A41） |
| C2-7 `claude` の失敗の後に台帳が読めないと 8 でなく 4 | 示せる（論理・試料 A42 で再現） | I4 | 直す（`progress` より先に 8） |
| C2-8 JSON の文字列の行も文言で読む（docstring は「JSON として読めない行」） | 示せる（実行） | 無し | 残課題 |
| C2-9 A30 の「上限ちょうどの桁数」の 4 は台帳が無いからでなく `mkdir` の名前の長さ | 示せる | 無し（試料の意味の取り違え） | 残課題 |
| C2-10 上限の文言が 2 つの正規表現に重複 | 示せない（いまは一致） | 無し | 残課題 |

### 狭いパスの指摘

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 | 振り分け |
| --- | --- | --- | --- | --- |
| N-1 `epoch` の NaN の分岐に試料が無い（`return value` にしても観測が同じ。NaN が通ると待たずに再起動する） | 示せる（変異が素通り・`read_limit` に直接渡して差） | 無し（本体は主張どおり） | 人間が決める | 記録だけ（実際の利用でまず起きない形・試料の穴。後退ではない——この周で足した分岐の試料の穴で、前の挙動を壊していない） |

## 手順 8

- この周の起票: 0 件
