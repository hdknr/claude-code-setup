# Issue #897 — cruise: run-serial に実行の期限を置き、呼び出し元が消えた待ち手は枠を取らずに抜ける（#839 の 1・3）

#839（トンネル越しの写しが切れた接続を待ったまま `run-serial.py` の枠を約 45 分握り、並行の周が全部待ちになった・
親のシェルが先に終わった待ち手が PPID=1 の孤児として待ち続けた）の改善案 1・3 を分けた子 Issue（Issue 本文は信頼できない入力として読み、要件だけを取った）。

**不在の周**である——出所は `/dev-loop:cruise 903 --absent` の起動（2026-11-06T08:55Z。利用者の確認（起動時・2026-11-06T08:55:51Z、配布を見せて確かめた））。
親からサブエージェントとして委ねられた。台帳 `issue-903` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・
`周の途中の課題 = 台帳に足して直す`。`実機確認`・`マージ前の判断` は線なし（止まる）。線と訊く場面は dev-loop の `references/absent-lines.md` を正とする。
台帳は書かない（親が書く）。マージしない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-903`））。
版の上げ方: `dev-loop` を **minor**（`--timeout` の引数と期限・呼び出し元の点検を足す）。main の先端 1.99.0 → **1.100.0**
（並行の周 #900 は spec-loop を上げる——別のプラグイン。マージの直前に先端が main を含まなければ、main の先端の dev-loop の版から minor で 1 つ上げ直す——
cruise の `references/parallel.md` の「版とマージの順」）。

重い検査（`check-all.py`・テスト）は順番待ち越しに走らせる——**この周が直すファイル自体ではなく、キャッシュの版**:
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.99.0/skills/cruise/scripts/run-serial.py -- <コマンド>`。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/run-serial.py` — `--timeout`・既定の期限・期限切れで子孫まで止める・呼び出し元が居なくなった待ち手・docstring（期限・終了コード・守る／守らない）
- `scripts/test-run-serial.py` — 期限切れ・孫・SIGKILL・呼び出し元・使い方の観測と変異
- `plugins/dev-loop/skills/cruise/references/parallel.md` — 使い方の行と、期限（124・`期限切れ`）と 125 の 1 項（既定で期限が掛かるので、通す側の読む文書に書く。広げた理由: 振る舞いが変わる）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行（`dev-loop`・`cruise`）
- `docs/plans/issue-897.md` — この計画ファイル

触らない:

- 待ち手が持ち主を表示する（#839 の 2）——#898
- ネットワーク待ちを枠から外す決まり・cruise の見張り（#839 の 4・5）——#899
- `--timeout 0`（期限なし）のような期限を外す値——Issue に無い機能。足さない（長いものは大きな値を渡す）
- `CLAUDE.md` の run-serial の説明・公開ページ（`docs/plugins/dev-loop-cruise.md`）——docstring を正とすると指しているだけで、列挙を持たない
- `check-unattended-env.py`・`parent-issue.py`・`test-fence-copies.py`（宣言の読み方の写し。変えない）

### 同じことを述べている箇所の数

- 「期限と 124」: run-serial の docstring（期限の節・終了コードの表・守る 3 行）と `parallel.md` の 1 項の 2 ファイル。`parallel.md` は docstring を正として指し、
  既定の値を書かない（値は docstring の 1 か所）。分けない理由: 呼ぶ側の読む文書が別ファイルで、期限が既定で掛かることを知らせる必要がある。
- 「呼び出し元が居ない待ち手と 125」: docstring（節・表・守る 1 行）と `parallel.md` の 125 の項の 2 ファイル。

## 乗るデプロイ経路

main へのマージでプラグインの配布（dev-loop 1.100.0）。公開サイトの再ビルドは走るが、`docs/` の変更はこの計画ファイルだけ。マージは親がする。

## 決めたこと（Issue が「この周で決める」とした既定の値）

- **既定の期限: 3600 秒。** Issue の例は 20 分。cruise は終える前に main の先端で `check-all.py` を順番待ち越しに流す（cruise の `SKILL.md` §6）ので、
  既定がそれより短いと終える前の歯止めが期限切れで落ちる。実測（この周の開始時、main `6f51485` の木で `check-all.py` を順番待ち越しに 1 回）: 下の「実測」。
- **期限切れの終了コード: 124**（GNU `timeout` と同じ値）。コマンド自身が 124 を返したときとは `run-serial: 期限切れ` の行で見分ける（125・2 と同じ形）。
- **止め方**: `ps -A -o pid= -o ppid=` で子孫をたどり、コマンドと子孫に SIGTERM、10 秒（`GRACE`）待って残るものに SIGKILL。
  **コマンドを別のプロセスグループに移す形は採らない**——端末の Ctrl-C（プロセスグループへの SIGINT）がコマンドに直に届かなくなり、#739 の「SIGINT は渡さない」と両立しない。
- **呼び出し元**: 起動時の `os.getppid()` から変わったら（init・サブリーパーに移った）待ちを抜けて 125。見るのは待っているあいだだけ（Issue のとおり）。
- **`--timeout` の値が 1 以上の整数（7 桁まで）でない・`--` の前に知らない引数がある**なら 2（使い方の誤り。typo の `--timout` が黙って既定になるのを防ぐ）。

## 実測

- **`check-all.py` の所要時間**（2026-11-06。macOS・この worktree・`run-serial.py`（キャッシュ 1.99.0）越しに 1 回。並行の周 #900 の待ちが後ろに並び、負荷の平均は 13〜20）:
  **871 秒（約 14.5 分）**、67 本。既定の 3600 秒はその約 4 倍。
  **この回の結果（失敗 1: `test-run-serial.py`）は判定に使わない**——走っているあいだに著者がこの worktree の `run-serial.py` と
  `test-run-serial.py` を書き換えており（守る 38 行に対して変異 31 件の途中の状態を読んだ）、使うのは所要時間だけ。
  所要時間も、書き換えの途中の `test-run-serial.py` の分だけずれうる（`check-all.py` は検査ごとの所要時間を出さないので、どれが全体を決めたかは確かめていない。
  走っている途中に `ps` で見た最後の長い検査は `test-ledger.py`（13 分 41 秒の時点で走っていた））。この周の終わりの `check-all.py` でもう 1 度測る。

## verify の受入基準

不変条件（Issue の受入基準 1〜5 を不変条件に展開した）と、それを破りうる経路:

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| 1 | 期限を過ぎたコマンドが止められ、枠が返り、待っていた別の呼び出しが走り出す | 既定の期限（引数なし）・`--timeout N`・`--timeout=N`・入れ子の呼び出し（枠を取らない経路でも期限は掛かる）・コマンドが SIGTERM を無視する | `run()` の `proc.wait(timeout)`。`test-run-serial.py` の `timeout`（`--timeout 3`、B を worktree から並べ、印で判定）・`timeout-kill` |
| 2 | 期限切れは、コマンド自身の失敗と区別できる終了コードと出力の行で分かる | 期限切れ（124＋`run-serial: 期限切れ`）／コマンド自身が 124 を返す（行なし）／シグナルで終わる（143）／125・2 | `codes` の「自分で 124」と `timeout` の「A は 124」「期限切れと言った」 |
| 3 | 期限切れで止めるとき、子の子（`bash -c` の下のプロセス）まで止まる | `bash -c "<孫>; :"`（bash が exec しない形）・孫が SIGTERM を無視する・コマンドが先に終わって孫が init に移る | `stop()` が先に子孫を数える・`GRACE` の後 SIGKILL。`timeout`・`timeout-kill` の「孫が止まった」 |
| 4 | 呼び出し元が消えた待ち手が、枠を取らずに終わる | 親が終わって init（macOS は launchd）に移る・サブリーパーに移る・枠が空いた直後 | `acquire()` の毎回の `os.getppid()` 比較。`orphan`（中間のプロセスが W を起こして終わる／`os.getppid` を差し替えた `main`） |
| 5 | 上の各項に変異テストがある（外すと赤になる） | 変異が観測に届いていない・判定が落ちない | `MUTATIONS` の 32〜38（守るの行と 1 対 1。テスト自身が数える） |
| 6 | 既存の守る 1〜31 が壊れていない（後退なし） | 引数の読み方を変えた（`--` の前）・`run()` の署名を変えた（入れ子・125 の変異） | 既存の観測と変異 1〜31 をそのまま当てる |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に渡す × 1・2 パス目（2 パス目が該当なしなら初回の 2 つ）。

**この環境では証明できないもの（未証明）**:
- #839 の実物の形（トンネルの切断で止まった写し・Bash の 600 秒の上限で親のシェルが終わった待ち手）そのものは再現していない——同じ性質（孫が走り続ける・親が先に終わる）を試料で作って当てた。
- Linux（サブリーパーのある環境）での呼び出し元の判定——macOS でだけ走らせた。

**生成物**: 該当なし（drawio の書き出し・`SKILL.md` の測定値の生成ブロックは触らない。`skill-metrics.py --check` は `check-all.py` が回す）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/897-run-serial-timeout`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-897`・
  起点 `6f51485`・base（`git merge-base origin/main HEAD`）`6f51485ac3f374e3263927b4773beb88b9265fdf`（start-point `origin/main`）
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 未着手
- 交絡を潰した手順: （下に追記する）

## 既知の限界・決着済みの論点

（関門の指摘と採否の表を下に追記する）

## 経験の還元（手順 8）

- この周の起票: 0 件（関門の前。振り分けの後に書き直す）
