# Issue #468 — StopFailure の hook で利用上限の停止をその場で記録・通知する

#456（自動継続の陽性対照）は上限を狙って起こせないので、自然に当たるのを待つしかない。
いまは利用者が気づくことに頼っており、気づかなければ記録は埋もれ、人間が「継続」と打てば陽性対照にならない。
`StopFailure` の hook で、止まったその場で手元のファイルに 1 行残し、通知を出す。

## 変更範囲

触る:

- `scripts/record-stop-failure.py` — 新規。hook の本体（stdin の JSON → `~/.claude/usage-limit-stops.jsonl` に 1 行・通知）
- `scripts/test-record-stop-failure.py` — 新規。回帰テスト（変異テストを含む。偽の stdin・一時 `HOME`・偽の `osascript`）
- `scripts/check-all.py` — `TESTS` に登録
- `.github/workflows/plugins.yml` — テストのステップを登録
- `docs/usage/usage-limit-stop-hook.md` — 新規。設定の手順
- `docs/plugins/dev-loop-cruise.md` — 「2. 環境を点検する」の節から指す
- `mkdocs.yml` — nav に足す
- `CLAUDE.md` — `scripts/` の一覧に 2 行
- `docs/plans/issue-468.md` — この計画

触らない:

- `plugins/` 配下（`check-unattended-env.py` に hook の点検を足すのは Issue に無い。版も上げない）
- 利用者の settings（リポジトリから書き換えない——Issue の「しないこと」）
- `scripts/count-usage-limit-resumes.py`（数えるのは後から。この周は合図を置くだけ）

### 同じことを述べている箇所の数

「hook が何を書き、何を書かないか」: 本体の docstring・docs の新ページ・`CLAUDE.md` の 1 行の 3 箇所。
docs と `CLAUDE.md` は**本体の docstring を正とする**と書いて列挙を持たない形にする（分けない理由: 利用者向けの手順は
登録の形が要り、docstring には置けない）。

## 乗るデプロイ経路

`docs/` の新ページと `dev-loop-cruise.md` は main への push で GitHub Pages に出る（公開サイトへの反映あり）。
`scripts/` は反映経路なし。プラグインの中身は変えないので版は上げない。

## 周の在り処

- ブランチ: `issue/468-stopfailure-hook`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-468`
- 起点: `c495860`（start-point `origin/main`）
- base: `c4958600e80be45a84e38340913c7699bd7d525b`

## 受入基準

不変条件:

1. **案件の中身を書かない**——`last_assistant_message` と `cwd` の生の値が、記録のファイルにも通知にも出ない。
   `error_details` は先頭だけ（長さに上限）
2. **壊れた入力で例外を出さず、読めなかったことを 1 行残す**——JSON でない・オブジェクトでない・キーが無い・
   stdin が空・非 UTF-8。終了コードは常に 0（fire-and-forget）。読めなかった行にも入力の生の値を書かない
3. **記録の先は `$HOME/.claude/usage-limit-stops.jsonl` で、追記**（前の行を消さない）。`~/.claude` が無ければ作る
4. **通知が失敗しても記録は残る**（`osascript` が無い・失敗する・引数にできない値）。通知には、上限らしい `error`（`rate_limit`・`billing_error`）のときだけ「『継続』と打たずにリセットまで待つ（#456）」を添える（**1 パス目の後に利用者が matcher を外すと決めたのに伴って変えた**——認証の失敗などに「待て」は誤り）
5. **テストは実環境の `~/.claude` を対象にしない**——一時 `HOME` をアサートで担保。本物の通知を出さない（偽の `osascript`）
6. **`check-all.py` と CI に登録**——`test-check-all.py` が緑（収録漏れの検査）
7. **docs の手順**: user の settings に `StopFailure`（**matcher なし**——全部を記録し、`error` の値で後から見分ける。**1 パス目の後に利用者が決めた**（2026-10-27）。本体が `billing_error` を「usage limit reached」に対応づけており、上限がどちらの値で来るかを確かめていないため）を足す形。登録は利用者が行う。
   `dev-loop-cruise.md` の環境の点検の節から指す。`mkdocs build --strict` が通る（リンク切れなし）
8. **陽性対照**: hook を登録した状態で、実際に `StopFailure` が発火した記録を 1 件取る（上限以外の `StopFailure` で経路だけでも）。
   取れなければ BLOCKED。**記録が出ないことを「発火しない」と読まない**
9. **文面の事実**: docs と docstring が述べる `StopFailure` の性質（発火条件・入力のキー・matcher の値）は、
   本体 2.1.311 の文字列か陽性対照で確かめた範囲に留める。確かめていないもの（上限で `rate_limit` になるか・待ちの間の回数）は
   「確かめていない」と書く

経路（記録のファイル・通知に値が入る入口）:

| 経路 | 守り方 |
| --- | --- |
| hook として Claude Code が起こす（stdin の JSON） | 本体が書くキーを許可リストで選ぶ（1・2） |
| 人が手で走らせる（stdin が端末・空） | 空の入力として「読めなかった」1 行（2） |
| 通知（`osascript` の引数） | 固定の文言と `error` の値だけ（1・4） |
| テスト | 一時 `HOME`・偽の `osascript`（5） |

検証で証明できるもの: 1〜6（テストと変異）、7（`mkdocs build --strict`・目視）、8（実際に `claude` を起こして観測できれば）、9（関門）。

この環境では証明できないもの（**未証明**）: 利用上限（claude.ai のセッションの上限）で実際に発火し `error` が `rate_limit` になること・
待ちの間の発火回数——上限を狙って起こせない（#456 そのもの）。

生成物: なし（図の書き出し・`skill-metrics.py` の生成ブロックは触らない。`SKILL.md` も触らない）。

## 未解決の判断

- なし

## 手順 8

- この周の起票: 0 件

## 関門の進捗（再開点）

- 手順 4: 実装済み（`check-all.py` 52/52 緑・`mkdocs build --strict`（`plans/` を外した一時の設定）が通る）
- 範囲の追加（手を動かす前に記録）: `docs/plugins/dev-loop-cruise.md` の見出し「2. 環境を点検する」に明示の id `{ #env-check }` を付けた
  ——日本語の見出しはスラグが `2` 程度にしかならず、新ページからのリンクが strict で落ちた。既存のリンクで `#2` を指すものは無い（grep）
- 交絡を潰した手順（受入基準 8 の陽性対照。著者の実験で、関門ではない）:
  - 一時 `HOME`・無効な `ANTHROPIC_API_KEY`・`claude -p "hi" --settings <一時の settings>`（2.1.311・macOS）。
    scratchpad の `probe-stopfailure.sh`
  - matcher なし → 1 行（`error: authentication_failed`・`error_details` 無し）／ `authentication_failed` → 1 行／ `rate_limit` → 記録なし。
    **同じ設定で matcher だけを変えて有無が分かれた**ので、「hook が壊れていて出ない」ではなく matcher が `error` に当たっていると読める
  - 確かめていないもの: user の settings の層・対話のセッション・利用上限での発火（docs の「確かめていないこと」に書いた）
- 割り目（手順 4 の終わり）: 利用者が「ここで割る」を選んだ（2026-10-27）
- 再開（2026-10-27）: `find-cycle.py` が当たり、ブランチ・コミット（`e59f7ab`）・base の祖先を確かめて入り直した
- 手順 5 の 1 パス目（Verifier。`dev-loop:dev-loop-verifier`・sonnet）: **反証 2 件・指摘 1 件**（下の採否の表の V-）
- 手順 6 の 1 パス目（`/code-review` high）: **指摘 10 件**（下の採否の表の CR-。うち 3 件は Verifier と同じ）
- 受入基準 4・7 を変えた——**利用者が「matcher なし」を選んだ**（2026-10-27。`AskUserQuestion`）
- 1 パス目の指摘対応: `fbd6c1a`（直す 6 種・残課題 4 件）。`check-all.py` 52/52 緑。
  陽性対照: 同じ入力（`repro-r1.sh`）が直す前 exit 1・0 バイト → 直した後 exit 0・1 行
- 次にすること: **手順 5 の当て直し（Verifier の 2 パス目）と手順 6 の 2 パス目（`/code-review`）の両方**。base は「周の在り処」の SHA のまま。
  2 パス目の指摘対応を始める直前の HEAD（狭いパスの起点）は、そのとき書く
- 割り目（2 パス目の前）: 利用者が「ここで割る」を選んだ（2026-10-27）。2 パス目はどちらも未着手
- 再開（2026-10-27・2 回目）: `find-cycle.py` が当たり、ブランチ・コミット（`8ada8ea`）・base の祖先を確かめて入り直した
- 手順 5 の 2 パス目（Verifier。`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件・軽微な所見 3 件**（下の 2 パス目の表の V2-）。
  テストは 3.14・3.12・3.9 で緑、変異 12 件すべて赤。生成物の検査 2 本は緑。`mkdocs build --strict` は Verifier は走らせていない
- 手順 6 の 2 パス目（`/code-review` high）: **指摘 5 件**（下の 2 パス目の表の CR2-。CR2-1 は V2-1 と同じ）。直す 3 件・残課題 2 件

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `cwd` のハッシュに塩を入れない | 採らなかった | 同じ `cwd` の停止を手元で束ねられるようにするため。既知のパスなら辞書で戻せるが、ファイルは手元にしか無い |

### 1 パス目の指摘（採否）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-R1: lone surrogate（`{"error":"\ud800x"}`）で `UnicodeEncodeError`・exit 1・空のファイルが残る | 示せる（著者が再現: scratchpad の `repro-r1.sh` → `exit=1`・`surrogates not allowed`・0 バイト） | 2 | 直す |
| V-R2: `error`・`session_id`・`hook_event_name` の型・長さを見ていない（3000 文字の `error`、辞書の `session_id`、辞書の `error_details` の `str()`） | 示せる（Verifier の実行。辞書の `session_id` がそのまま記録に出る） | 1（`error_details` の上限の趣旨・許可リストが値の形まで見ていない） | 直す |
| V-指摘: 本体は `billing_error` を「usage limit reached — check plan」に対応づける。docs の matcher が `rate_limit` 固定だと上限の停止を取りこぼしうる | 示せる（著者が 2.1.311 のバンドルで `case"billing_error":return{state:"blocked",needs:"usage limit reached — check plan"}` を確認） | 7・9（既定の案内が確かめていない片方に倒れている） | 直す（受入基準 7 を変えるので**利用者に訊いた**——「matcher なし」） |
| CR1: lone surrogate（V-R1 と同じ） | 示せる（同上） | 2 | 直す（V-R1） |
| CR2: `error` に NUL があると `subprocess` が `ValueError`・exit 1 | 示せる（`/code-review` が再現。rc=1・記録は残る） | 2（終了コードは常に 0） | 直す |
| CR3: matcher `rate_limit` が未確かめの値で絞る（V-指摘と同じ） | 示せる（同上） | 7・9 | 直す（V-指摘） |
| CR4: 値の型・長さを見ていない（V-R2 と同じ） | 示せる（`hook_event_name` の辞書がそのまま出る・10 万文字の `session_id`） | 1 | 直す（V-R2） |
| CR5: 認証の失敗などにも「リセットまで待て」と添える | 示せる（matcher なしにすると `authentication_failed` で出る。著者の陽性対照の入力） | 4（matcher を外すと決めた後の受入基準 4） | 直す |
| CR6: CASES に符号化できない値・長い値・文字列でない値が無い | 示せる（CR1・CR2 があるのにテストは緑） | 2・1 | 直す（上の修正に入力を足す） |
| CR7: テストが長さを見ずに添字で引く（`IndexError` で要約が出ない） | 示せない（いまは落ちていない。退行したときの形） | 無し | 残課題 |
| CR8: 「通知が失敗しても記録は残る」の後半を壊す変異が無い | 示せない（いまのテストでも記録の行数で捕まると `/code-review` 自身が書いている） | 無し | 残課題 |
| CR9: `assert_not_real_home` が素の `assert`（`-O` で消える） | 示せない（テストを `-O` で走らせる経路が無い） | 無し | 残課題 |
| CR10: docs のコマンドがパスをクォートしていない | 示せない（空白を含むパスでの失敗は仮定。手元の clone には空白が無い） | 無し | 残課題 |

### 2 パス目の指摘（採否）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-1: `cwd` が対にならないサロゲートだと `cwd.encode("utf-8")` が例外を出し、記録が `unreadable` の 1 行になって `error` が失われる | 示せる（著者が再現: scratchpad の `repro-v2.py` → exit 0・`unreadable` の 1 行。普通の `cwd` なら `error: rate_limit` が残る） | 4（`rate_limit` なのに通知に「待て」が付かない。著者は最初 2 だけを見て「無し」とした） | 直す（CR2-1） |
| V2-2: `error` が空文字のとき通知が「入力を読めなかった」と出る（記録は正しい） | 示せない（本体の列挙値に空文字は無い） | 無し | 残課題 |
| V2-3: 上限でない `error` が `osascript` の引数にそのまま入る（`-` で始まる値の扱いは未確認） | 示せない（本物を走らせていない。値は本体の列挙値） | 無し | 残課題 |
| CR2-1: `cwd` が対にならないサロゲートだと記録が `unreadable` になり、`rate_limit` でも通知に「待て」が付かない（V2-1 と同じ） | 示せる（`/code-review` と著者が再現。`repro-v2.py`） | 4（上限の `error` なのに「待て」を添えない）・docstring の「書けない文字が来ても記録は残る」 | 直す（V2-1 も同じ修正で直る） |
| CR2-2: `main` の外側の try/except を外す変異がテストで死なない | 示せない（いまのコードでは落ちない。変異体でだけ落ちる） | 無し | 残課題 |
| CR2-3: 「オブジェクトでない」「error が無い」の変異が、約束ではなく理由の文言の違いで死んでいる | 示せない（テストの判別力の話。いまのコードは約束を守っている） | 無し | 残課題 |
| CR2-4: サロゲートの入力が `error`・`session_id` だけで、`cwd` に無い | 示せる（CR2-1 がテストを緑のまま通っている） | 4（CR2-1 と同じ） | 直す（CR2-1 の入力に足す） |
| CR2-5: docs の「hook が壊れていても、何も表示されません」は確かめていない | 示せる（壊れた hook を走らせた実験が無い。本体には hook 失敗時の警告を組む箇所がある） | 9 | 直す（「確かめていない」に弱める） |
