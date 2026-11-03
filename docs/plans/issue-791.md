# Issue #791 — cruise: 外側のループが台帳の updated・note の書き換えを前進と見て、空回りしうる

#790（spec-loop の autopilot の外側のループが止まったことを見落として `claude -p` を約 1,900 回空回りさせた）と同じ形が、
cruise を外から繰り返し起こすループでも起こりうる。外側のループはプラグインに無く、プロジェクトごとに手で書かれ、
実際に使った 1 件は前進を台帳の JSON のハッシュで見ていた（`ledger.py set` は `updated` を毎回書き換える）。

**不在の周**である——出所は `/dev-loop:cruise 793 --absent` の起動（2026-11-03）。親からサブエージェントとして委ねられた。
台帳 `issue-793` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・`周の途中の課題 = 外に出す`
（出所: 利用者の確認（起動時・親 Issue #793 の cruise: の行・2026-11-03T03:56:17Z、配布を見せて確かめた））。台帳は書かない（親が書く）。マージしない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（能力の追加——同梱の外側のループと `ledger.py progress`）。main の先端 1.76.0 → 1.77.0、#816（main 1.77.0）を取り込んで **1.78.0**
（未マージの PR #815 も 1.77.0 に上げている。マージの直前に main が進んでいたら、親が子に取り込みと上げ直しを回す——cruise `references/parallel.md`）。

重い検査（`check-all.py`・テスト）は順番待ち越しに走らせる:
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py -- <コマンド>`。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/outer-loop.py` — 新規。同梱の外側のループ
- `scripts/test-outer-loop.py` — 新規。上の回帰テスト（偽の `claude`・偽の `osascript`。変異テストを含む）
- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — `progress` 副コマンド・docstring
- `scripts/test-ledger.py` — `progress` の試料と変異
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 「外から判定するなら」に `progress` と同梱のループ
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 5（無人の起動で拒まれても `await`）・§4 の 6（進めずに確かめただけのことを台帳に書かない）・§6（外側のループは同梱のものを使う）・版の 2 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `docs/plugins/dev-loop-cruise.md` — 部品の一覧の行と、§5 の外側のループの節
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 同上（CI のステップ）
- `docs/plugins/dev-loop-design.md` — 生成ブロック（`skill-metrics.py` が `references/ledger.md` の行数で書き直す。手で書かない）
- `CLAUDE.md` — 新しいスクリプトとテストの行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-791.md` — この計画

触らない:

- spec-loop の autopilot（#789）との共通化——spec-loop に外側のループはまだ無い。この周は cruise の側だけ
- PR #815 の公開ページの手書きの例（`### claude -p で外から回すとき`）——未マージ。両方が入った後に、例を同梱のスクリプトに差し替えるかは人の判断（PR コメントで渡す）。
  この周の節は #815 の節と別の位置に置き、`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`・`status` の終了コード・`claude` の失敗で止める、の 3 つは #815 の例と同じ振る舞いにする
- `child-cycle.py`・`references/child-process.md`（周の子プロセスで、外側のループではない）
- `launch-with-long-token.sh`（`-p` を渡す形は確かめていない——#815 と同じ）

### 同じことを述べている箇所の数

「外側のループの止め方」を述べるのは 4 箇所——`outer-loop.py` の docstring（守る／守らないの原本）・cruise `SKILL.md` §6（親の規範から指す）・
`references/ledger.md`（`status` の読み方から指す）・公開ページ §5（利用者向けの使い方）。公開ページと `SKILL.md`・`ledger.md` は
規則を写さず docstring を指す。分けない理由: 読み手が違う（親・台帳を読む者・利用者）。
「親は進めずに確かめただけのことを台帳に書かない」「無人の起動で拒まれても `await`」は 2 箇所——`SKILL.md`（原本）と `outer-loop.py` の追記の文
（`--append-system-prompt` で親に渡す。`SKILL.md` を指す形で書き、写しは 1 文ずつに留める）。

## 乗るデプロイ経路

main へのマージでプラグインの配布（dev-loop 1.77.0）と公開サイト（`docs/plugins/dev-loop-cruise.md`。main への push で GitHub Pages）。マージは親がする。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | `ledger.py progress <名前>` は行ごとの番号・`state`・`pr`・`group` だけを出し、`updated`・`note` ほかの書き換えでは出力が変わらない。台帳を書き換えない。読めない・無い台帳は 4 | `set note=`・`set agent=`・`set decisions=`・`lines`・`user_ops` の書き換え／`state`・`pr` の遷移・行の追加／無い・壊れた台帳 | `test-ledger.py` の試料（本物の `ledger.py` を一時のリポジトリで） |
| A2 | `outer-loop.py` は `ledger.py status` が 0 のときだけ `claude` を起こし、3・4・5・ほかの値では起こさずに止まる | 起動の前の判定・起動の後の判定・`status` が表に無い値 | `test-outer-loop.py`（偽の `claude` が起動の回数を記録） |
| A3 | 起動の前後で `progress` が変わらない起動が続けて N 回（既定 2）になったら止まる。`note` だけ・`updated` だけの書き換えは前進に数えない | 親が `note` を書き直すだけの起動・何も書かない起動・`progress` が読めない | 同上（偽の `claude` が台帳を本物の `ledger.py` で書き換える） |
| A4 | 起動の総数の上限（既定 20）で止まる | 前進が続く台帳 | 同上 |
| A5 | `claude` が 0 以外で終わった・起こせなかったら止まる | 終了コード・実行ファイルが無い | 同上 |
| A6 | 引数を読めた後の止まるすべての経路で、理由を出力して通知する（`osascript` が在れば）。終了コードは docstring の表と定数が一致する | 済んだ・人待ち・判定できない・前進なし・上限・`claude` の失敗・中断 | 同上（偽の `osascript` が受けた本文を記録） |
| A7 | `claude` はメインの作業ツリーを cwd に、`-p "/dev-loop:cruise <親>[ --absent]"`・`--append-system-prompt <追記>` と利用者の追加の引数で起こし、環境に `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` を置く（利用者が別の値を置いていても 0 で上書きし、上書きしたと出す——`child-cycle.py` と同じ。**1 パス目の CR2 で、当初の「上書きしない」の書き方が実装・docstring と逆だったので直した**） | worktree の中から走らせる・`--absent` の有無・追加の引数 | 同上（偽の `claude` が引数・cwd・環境を記録） |
| A8 | 親の規範: §4 の 5 に「無人の起動で拒まれても `await` にし、『止まった』と書いてターンを終えない」、§4 の 6 に「進めずに確かめただけのことを台帳に書かない」がある。`outer-loop.py` の追記の文が同じことを言い、`SKILL.md` を指す | §4・§6・追記の文 | 読んで突き合わせる |
| A9 | 指し先が実在する・新しいテストが CI と `check-all.py` に登録されている・CLAUDE.md の一覧にある | リンク・登録漏れ | `check-site-links.py`・`check-skill-pointers.py`・`test-check-all.py`（`check-all.py` が回す） |
| A10 | 版を 3 箇所で上げる | `marketplace.json`・`plugin.json`・両 `SKILL.md` の 2 行 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| A11 | 既存の歯止めを割らない | 太字の flanking・件数の重複・規範マーカー・生成ブロック | `check-all.py`（順番待ち越し）が緑・PR の CI が緑 |

必須要件の掛け算: 受入基準を Verifier・`/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

**この環境では証明できないもの（未証明）**: 本物の `claude -p` に `--append-system-prompt` で渡した追記に、親が実際に従うか（権限に拒まれた周を `await` にする・
進めずに台帳を書かない）——モデルの振る舞いで、権限に拒まれる無人の起動を作るには本物の `claude` を起こして課金する。`--append-system-prompt` が
2.1.317 の `claude --help` に在ることまでは確かめた。PR コメントで人間のレビューに回す。

**生成物**: `skill-metrics.py` の生成ブロック（設計 §8.2）は dev-loop の `SKILL.md` の節構造に依る——版の行だけを変えるので `check-all.py` の `--check` で鮮度を見る。図の書き出しは無し。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/791-cruise-outer-loop`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-791`・
  起点 `5235146c`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `5235146c49b8fae6d38ef2f2ddd82031ebd2e767`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）
- 関門 1 パス目: 起動（Verifier: sonnet・`dev-loop:dev-loop-verifier`／`/code-review` high）。1 パス目の指摘対応の起点 `41cbbad1`（関門に渡す時点の HEAD）。`test-outer-loop.py`（順番待ち越し）35 ok・FAIL 0・変異 12/12
- 関門 1 パス目の結果: Verifier 反証 2 件・`/code-review` 指摘 10 件。直す 7 件（採否の表）。差し戻し 1 回（手順 4 へ）。1 パス目の指摘対応の差分は 0 行でない（`git diff 41cbbad1` に成果物の変更あり）→ 2 パス目を回す
- 割り目（2 パス目の前）: 割らない（不在の cruise）。残っているもの: 手順 5 の当て直しと `/code-review` 2 パス目の両方
- 関門 2 パス目: Verifier 反証 1 件・`/code-review` 指摘 10 件。直す 2 件。狭いパスの起点 `6072ab7e`・終点 `9ead931f`
- 狭いパス: Verifier（sonnet）反証 1 件（低・受入基準は破らない: 先頭が 0 の番号 `050` を旧版は 50 と読み、新版は 2 で止める。採否は人が決める）。素通りした変異 1 件（`APPEND` の文面をテストが内容まで見ていない——文を書き換えても赤にならない）。`²` は旧版で例外・新版で 2（陽性対照つき）
- 取り込み: main（#816、dev-loop 1.77.0）を取り込み、版を 1.78.0 に上げ直した。生成ブロックは main 側を取って `skill-metrics.py` で書き直した
- `check-all.py`（順番待ち越し・取り込みの後）: 59/59 緑。PR #817 の CI: check・build が pass（deploy は skipping）
- 交絡を潰した手順: `test-outer-loop.py` の陽性対照（S2 で台帳のファイルは変わったのに progress は同じ）・変異 12/12。順番待ちのテストの前の `git stash` 事故は、テストが待ちのあいだに戻した
- 事故の記録: 2026-11-03 に著者が worktree で誤って素の `git stash -q` を走らせ、未コミットの変更を退避した。直後に `git stash pop stash@{0}`（`WIP on issue/791-cruise-outer-loop` であることを確かめて）で戻した。そのとき順番待ちのテストはまだ始まっておらず（run-serial のログが「待っている」）、結果には効いていない

## 既知の限界・決着済みの論点

- 前進の判定は台帳の値（`progress`）だけで、実物（PR・worktree）は見ない——`ledger.py` の「守らない」と同じ。
- 既定の「前進なし 2 回」は、1 回の起動が周を最後まで進めない（関門の途中で compact した、など）のを 1 度だけ許すため。#815 の例は 1 回で止める——どちらも空回りを有限に抑える。

### 採否の表（1 パス目）

Verifier（sonnet・`dev-loop:dev-loop-verifier`）反証 2 件、`/code-review`（high）指摘 10 件。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-R1 `check-plan-scope.py` が 2 ファイルを範囲の外と言う | 示せる（`check-all.py` の 1 回目で同じ出力） | A11 | 直す——触るの行を 1 行 1 パターンに（`dcacc815` で済） |
| V-R2 `--claude "a'b"` で `shlex` が例外、通知なし・表に無い 1 | 示せる（Verifier が実走） | A6 | 直す——`main` で語に分け、分けられなければ 2 |
| V-A8 §4 の 6 が指す「6. 終える」に「台帳を書き換えずに終える」が無い | 示せる（節を読む） | A8 | 直す——指し先を外し、その場で言い切る |
| CR1 Python 3.11 以前は `50 --absent -- …` を argparse が拒む | 示せる（`/usr/bin/python3` 3.9.6・3.11 で 2） | A7 | 直す——`--` で自分で分ける（3.9.6 で通ることを確かめた） |
| CR2 A7 の「上書きしない」と実装・テストの「上書きする」が逆 | 示せる | A7 | 直す——計画の書き方の誤り。実装（docstring・`child-cycle.py` と同じ上書き）に合わせて A7 の文を直した。**基準の文を直したので、マージ前に人が確かめる** |
| CR3 `--` の後ろで `bypassPermissions` を渡せる（`child-cycle.py` は拒む） | 示せる | 無し | 残課題 |
| CR4 SIGTERM・SIGHUP・予期しない例外で通知しない | 示せる（`kill`） | A6（すべての経路） | 直す——SIGTERM・SIGHUP を 130、例外を 4 にして通知する |
| CR5 #815 の手書きの例（`updated` だけを除く）と同じページに並ぶ | 示せない（#815 は未マージ） | 無し | 残課題——マージ前に人の判断 |
| CR6 Ctrl-C で `subprocess.run` が claude を約 0.25 秒で kill する | 示せない（実害の観測なし） | 無し | 残課題 |
| CR7 台帳が無いと 4——最初の起動は対話でと書いていない | 示せる | 無し | 残課題 |
| CR8 docstring の `../../dev-loop/…` を「base からの相対」と書いた | 示せる（その場所に無い） | A9 | 直す——`../dev-loop/…` に |
| CR9 子プロセスの周が走っているあいだの起動を前進なしと数える | 示せない | 無し | 残課題 |
| CR10 止まる条件を公開ページ・SKILL.md に写している | 示せない（いまは一致） | 無し | 残課題 |

- 著者の事故: CR1 の確かめで `PATH=/bin:/usr/bin` の `/usr/bin/python3` で `outer-loop.py` を走らせ、本物の `osascript` で通知を 1 件出した（台帳が無く 4 で止まった。`claude` は起こしていない）。

### 採否の表（2 パス目）

Verifier（sonnet）反証 1 件、`/code-review`（high）指摘 10 件。狭いパスの起点 `6072ab7e`（2 パス目の指摘対応を始める直前の HEAD）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-1・R2-5 親の番号に `²` を渡すと `int()` の例外で 1（表に無い・通知なし） | 示せる（両方の関門が実走） | A6（引数の誤りは 2） | 直す——ASCII の数字だけを受ける |
| R2-1 SIGHUP に無条件でハンドラを置き、`nohup` の SIG_IGN を上書きする（端末を閉じると止まり、claude も止まる） | 示せる（`/code-review` が SIG_IGN の親から実走） | 無し | 残課題——**1 パス目の CR4 の直しが持ち込んだ後退。マージ前に人の判断** |
| R2-2 SIGTERM・SIGHUP で `subprocess.run` が claude を SIGKILL する（片付けの機会が無い） | 示せる（実走） | 無し | 残課題——マージ前に人の判断（R2-1 と同じ直し方の判断） |
| R2-3 判断待ちの印への移り変わりを前進なしに数え、3 でなく 6 で止まる | 示せない（実走していない） | 無し | 残課題 |
| R2-4 端末が切れると `print` が EIO で落ち、通知が届かない | 示せない（未確認） | 無し | 残課題 |
| R2-6 相対パスの `--claude` がメインの作業ツリーから解決される | 示せない（未確認） | 無し | 残課題 |
| R2-7 SIGHUP の試料・変異が無い | 示せる | 無し | 残課題 |
| R2-8 変異の判定が理由を見ずに「殺せた」と数える | 示せない | 無し | 残課題 |
| R2-9 追記の `note=<打ってほしいコマンド>` が §4 の 5 より狭い（`単独:` の項を消しうる） | 示せる（2 つの文を読む） | A8 | 直す——式を写さず「`note` の書き方もその 5 に従う」に |
| R2-10 §4 の 6 の理由（updated で前進と読む）が同梱のループには当たらない | 示せる（読む） | 無し | 残課題 |

## 経験の還元

- この周の起票: 0 件（不在の cruise。残課題は PR コメントに残す）
