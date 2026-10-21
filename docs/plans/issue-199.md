# Issue #199 — orca: -w / -r を Orca 管理の worktree の中から通しで確かめる

## 1. 変更範囲

触る:

- `plugins/orca/skills/orca/SKILL.md` — `-w` と `-r` の節（と版のバナー）
- `plugins/orca/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — orca の version
- `docs/plans/issue-199.md` — この計画ファイル

触らない:

- `plugins/cmux/` — 同じ文面を持つが、Issue は Orca 固有の前提（最初から Orca 管理の worktree の中にいる）を問うている。cmux から linked worktree の中で呼んだ場合の同型の危険は PR コメントの残課題に書く
- description（3 箇所）——「-w は worktree で gh pr checkout」は変わらない
- `plugins/orca/README.md` ——表の「worktree でチェックアウト」は変わらない
- `orca worktree create --pr` に寄せる案（#203 の未決）

**複製の数**: `-w`/`-r` の worktree 条件を述べている箇所は orca の `SKILL.md` の 2 節（`EnterWorktree`・`worktree 内`・`gh pr checkout` を `plugins/orca/` と `docs/` で引いた。README の表は条件を持たない）。版は 3 箇所（CI が見る）。**分けない理由**: 2 節は同じ欠陥（作れなかった・作らなかったときに利用者のツリーで checkout する）の 2 つの入口。

## 2. デプロイ経路

- マーケットプレイス（`plugins/` と `marketplace.json`）。`docs/` は計画ファイルだけ。破壊的・不可逆な操作は無い。

## 3. 受入基準

**実測（Issue のやること 1。2026-10-13、Orca 1.4.224）**: `orca worktree create --name probe-199` で作った
Orca 管理の linked worktree（`~/orca/workspaces/claude-code-setup/probe-199`）の中で:

- 前提の確認（`orca worktree current`）は `ok`——スキルは止まらない。
- `git rev-parse --path-format=absolute --git-dir` = `…/.git/worktrees/probe-199`、`--git-common-dir` = `…/.git`
  ——git の判定では「worktree 内」。旧 `-r` の「worktree 内でなければ」はこの読みで偽になり `EnterWorktree` を飛ばす。
- `gh pr checkout 192` は終了 0 で `hdknr/probe-199` → `issue/190-eval-runner` に切り替えた。
  `orca worktree current` もそのブランチを返した——**利用者の作業ブランチが切り替わる**。
- 陽性側: メインのチェックアウト（Orca の `isMainWorktree: true`）では git-dir = common-dir で「worktree の外」。
- probe は `orca worktree rm` で削除し、残ったブランチ `hdknr/probe-199` も削除した。

**I1. `-w`/`-r` の `gh pr checkout` が、呼び出した時点の作業ツリー（利用者の Orca worktree）のブランチを切り替えない。**

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 `-r`・Orca 管理の linked worktree の中（PR と別のブランチ） | 新しい worktree を作り、そこで checkout | 条件を「worktree 内か」から「HEAD が PR の head ブランチか」に変える |
| P2 `-r`・Orca のメインのチェックアウト | 同上（回帰しない） | 同上 |
| P3 `-r`・既にその PR のブランチの上にいる | 作らずにそのままレビュー（checkout は切り替えない） | 同上 |
| P4 `-w`/`-r`・`EnterWorktree` が作れない（worktree セッション中など） | 止まる。現在のツリーで checkout しない | 「作れなければ止まる」を明記 |
| P5 `-w`/`-r`・`EnterWorktree` は返ったが移っていない | 止まる | 作成前後の `--show-toplevel` を比べる |
| P6 fork の PR で head 名とローカル名が違う | 安全側（作る）に倒れる | 一致しなければ作る |

**I3（1 パス目のあと人間が追加。V1/C1/C2）. `-r` が checkout を飛ばすのは、いまのツリーの HEAD が PR の head コミットと同じときだけ。**
飛ばした結果、PR でないコードをレビューしない。

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P7 fork の PR の head 名が手元のブランチ名と同じ（例 `main`） | 作る | 名前ではなく `git rev-parse HEAD` と `headRefOid` を比べる |
| P8 手元の同名ブランチが PR より遅れている／force-push で分岐 | 作る | 同上 |
| P9 手元が PR の head と同じコミット（名前付き・detached どちらも） | 作らずにレビュー | 同上 |

（`isCrossRepository` は使わない——SHA が一致すれば fork でも同じコミットなので、名前より強い条件で足りる。）

**I2. 版が揃い patch で上がっている**（orca 1.0.4 → 1.0.5）。`check-all.py` が緑。

### 証明の手段

- I1: 条件の判定（git・`gh pr view --json headRefName`）は Orca の linked worktree とメインで実測できる。
- **未証明**: モデルが新しい文面を読んで実際にどう動くか（`/orca -r` を Orca の中の Claude Code で通しで回すこと）。
  この周の Claude Code はメインのチェックアウトで起動しており、Orca の linked worktree の中のセッションではない。
  **`EnterWorktree` を Orca の linked worktree の中から呼んだとき、どこに作るか**も測っていない
  （道具の説明文は「`.claude/worktrees/` に作る」とだけ言う）。人間レビューに回す。
- 生成物: **生成物なし**（`SKILL.md` の測定値は dev-loop だけ、図は触らない）。

## 4. 未解決

- なし

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/199-orca-r-worktree-check`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-199`、
  起点 `4395dd2`、base 参照 `origin/main`、base SHA `4395dd2c1a85d7205ae2a4826297ca9b2d70d6b6`
- 実装: `e49a061`（check-all 32/32 緑）。次は手順 5（Verifier 1 パス目）と手順 6（`/code-review` 1 パス目）
- 割り目 1（手順 4 完了時）: 提案した → 人間の選択「ここで割る」
- 割り目 2（2 パス目の前）: 提案した → 人間の選択「ここで割る」
- 関門: 1 パス目
  - Verifier（`dev-loop:dev-loop-verifier`/sonnet。自己申告のツールは Bash/Read のみ）: **反証 1 件**（I1/I2 への直接の反証 0 件）。check-all 32/32 緑・生成物なしを独立確認
  - `/code-review` high: **指摘 10 件**（I2 は緑を独立確認。I1 を直接破る指摘は 0 件）
  - 採否: 「示せる × 破る受入基準」を満たす行は 0。V1/C1/C2（この周が入れた退行）は人間に範囲拡大を訊き「範囲を広げて直す」→ I3 を追加して直した。残り 7 件は残課題（C8 は対象外）
  - 1 パス目の指摘対応: `-r` 手順 3 を名前比較から SHA 比較（`git rev-parse HEAD` ↔ `headRefOid`）へ。実データ: この worktree の HEAD `55e3a24` ≠ PR #229 の head `c094176`（→ 作る）、ローカルの `issue/198-issue-mode-pr-url` = `c094176`（→ そこにいれば飛ばす）
  - 次: **手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方**が残っている。1 パス目の指摘対応は `831feec`（check-all 32/32 緑）。**狭いパスの起点 SHA（2 パス目の指摘対応を始める直前の HEAD）: `831feec1fdc38d243c25025b373403fe232c4b2f`**
- 2 パス目: Verifier 反証 0 件／`/code-review` 指摘 8 件（採否は §6 の 2 パス目の表）。直す 1 件（R1）。R1 は `8efaacc` で直した（check-all 32/32 緑）。狭いパス: 済（重大 0・軽微 2。§6）。**関門はここで終わり。次: PR 作成 → 人間レビュー**
- 反証・差し戻し: 0
- 交絡: 実験 1（上の実測）。陽性側（メインで「外」・checkout で実際に切り替わる）を取った。

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| cmux も同じ文面 | 触らない（残課題） | Issue は Orca の前提を問う。cmux で linked worktree から呼ぶ危険は同型だが受入基準の外 |
| `orca worktree create --pr` に寄せる | 採らない | #203 の未決 |

### 1 パス目の指摘（採否の表）

| # | 出所 | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- | --- |
| C1 | /code-review | V1 と同じ。加えて「手元が PR より遅れている同名ブランチ」も。P2 の「回帰しない」を破ると主張 | 示せない（同上） | 無し（経路の表に当たるだけでは受入基準にならない。I1 は守られる） | **直す**（I3） |
| C2 | /code-review | 手順 3 の理由「checkout しても何も切り替わらない」は偽（既存ブランチでは `gh pr checkout` が fetch ＋ ff-only merge する） | 示せない（`gh` の実装の読みのみ。走らせていない） | 無し | **直す**（同じ修正で理由文も差し替え） |
| C3 | /code-review | PR のブランチが別の worktree で checkout 済みだと、新しい worktree での `gh pr checkout` が失敗し、次の手が書かれていない | 示せない（旧版にも同じ形がある） | 無し（失敗するだけで切り替えない） | 残課題 |
| C4 | /code-review | `-w` は利用者が PR のブランチ上にいると `gh pr checkout` が失敗する（C3 の特殊形） | 示せない | 無し | 残課題 |
| C5 | /code-review | `EnterWorktree` が利用者の Orca worktree の `.claude/worktrees/` に入れ子で作る見込み | 示せない（未測定。計画で未証明に挙げ済み） | 無し | 残課題（BLOCKED への分類替えと合わせて PR コメントに書く） |
| C6 | /code-review | P4 で止めるより `git worktree add` ＋ `EnterWorktree(path)` で作れる | 示せない（設計の代案） | 無し | 残課題 |
| C7 | /code-review | P5 の検査は「既存の別 worktree へ `path` で入った」も通す。そこで checkout すると他人の worktree のブランチが切り替わる | 示せない | 無し（I1 は「呼び出した時点の作業ツリー」） | 残課題 |
| C8 | /code-review | 計画の「証明の手段」が P3〜P6 の判定を測っていない | — | — | 対象外（関門は計画ファイルを検査しない）。PR コメントで未証明／BLOCKED を書き直す |
| C9 | /code-review | SKILL.md が「旧条件は Orca で切り替える側に倒れる」と断定するが、測ったのは git の読みだけ | 示せない | 無し | 残課題 |
| C10 | /code-review | 公開ページ `docs/plugins/index.md:496` の `-r` 行が「worktree でチェックアウト」のまま | 示せない | 無し（範囲外） | 残課題 |
| V1 | Verifier | `-r` 手順 3 は名前の一致だけで checkout を飛ばすので、fork の PR の head が `main` で利用者がローカル `main` にいる・同名でコミットが違う場合に、PR でないツリーをレビューする（旧版は常に checkout していたので**この周が入れた退行**） | 示せない（実データの失敗は無い。論理上の経路。`gh pr view 229 --json headRefOid,isCrossRepository` が値を返すことは確認） | 無し（I1 は守られる。壊れるのはレビューの正しさ） | **直す**（人間が範囲拡大を選択 → I3。手順 3 を SHA 比較に変更） |

### 2 パス目の指摘（採否の表）

関門: Verifier（`dev-loop:dev-loop-verifier`/sonnet。自己申告のツールは Read/Bash）**反証 0 件**（check-all 32/32 緑・`headRefOid` が 40 桁 SHA を返すことを独立確認）。
`/code-review` high **指摘 8 件**。

| # | 出所 | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- | --- |
| R1 | /code-review | P8（利用者のツリーが PR と同名・遅れたブランチ）で新 worktree の `gh pr checkout` が必ず失敗し、止まる記述が無いので 5 で PR でないツリーをレビューする | **示せる**——scratchpad の clone で、同名ブランチを別 worktree に持たせた状態で `gh pr checkout 229` が `fatal: 'issue/198-issue-mode-pr-url' is already used by worktree` / **rc=1**、新ツリーは origin/main（`8df3a56`）のまま。陽性対照: その worktree を外すと rc=0 で `c094176` に着く | **I3** | **直す**（`-w`/`-r` の 4 に「失敗したら止める」） |
| R2 | /code-review | HEAD = head でも未コミットの変更があると、PR に無い編集をレビューする | 示せない（レビューが作業ツリーを読むことは実物で示していない。旧版も同じ） | 無し | 残課題 |
| R3 | /code-review | 同じセッションで 2 回目の `-w`/`-r` は worktree セッション中なので必ず止まり、`ExitWorktree` への案内が無い | 示せない | 無し（止まる側。I1 は守られる） | 残課題 |
| R4 | /code-review | 共通節の「git でも worktree の中と出る」は Orca のメインのチェックアウトでは偽 | 示せない（記述の広さ） | 無し | 残課題（C9 と合わせて） |
| R5 | /code-review | 公開ページ `docs/plugins/index.md:478` の「cmux と引数・挙動が同じ」が偽になった | 示せない | 無し（範囲外） | 残課題（C10 と合わせて） |
| R6 | /code-review | 「理由は同じ節にある」の指し先が違う（別の節） | 示せない | 無し | 残課題 |
| R7 | /code-review | `git fetch pull/N/head` → `worktree add --detach` → `EnterWorktree(path)` で根本から消せる | 示せない（設計の代案） | 無し | 残課題（C6 と合わせて） |
| R8 | /code-review | 40 桁の目視比較は誤読しうる。1 行の `[ … = … ]` で終了コードにできる | 示せない | 無し | 残課題 |

### 狭いパスの指摘（採否は人間が決める）

狭いパス（`dev-loop:dev-loop-verifier`/sonnet、起点 `831feec`、対象 `8efaacc`）: **重大な反証 0 件・軽微 2 件**。check-all 32/32 緑を独立確認。
**変異は読解でのみ判定**（機械では当てていない）。赤: `-r`／`-w` の停止文の削除・SHA 比較を名前比較に戻す。素通り: 「終了コードが 0 でない」を「エラーが出たら」に弱める・4 の注記を削る（停止文が残る限り不変条件は崩れない。陽性対照は停止文自体の削除）。§3 の未証明の分類は読んでいない（未確認）。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | `-r` の 4 の「PR でないコミット（作った元）のまま」は、「作った元」が利用者のツリーと読める。実測では origin/main | 示せない（記述の精度） | 無し | 人間が決める |
| N2 | `fatal: … is already used by worktree` の文言は git の版に依存しうる（判定は終了コードなので影響なし） | 示せない（推測） | 無し | 人間が決める |

## 7. 本番反映・8. 経験の還元

- PR #234 を作成。PR 側の CI（`check`・`build`）は緑（`gh pr checks 234`）。**マージは人間の承認待ち**。反映経路はマーケットプレイス（マージ後に利用者が `plugin update`）。
- 起票候補 C3/C4（実物: R1 と同じ実験で rc=1）は人間が「起票しない」を選択。
- この周の起票: 0 件
- 焼き戻し: `gh pr checkout` が「別の worktree で checkout 済みのブランチ」で失敗することは orca の `SKILL.md` に書いた。それ以外に焼き戻す学びなし。
