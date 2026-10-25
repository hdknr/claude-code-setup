# Issue #389 — dev-loop: PR のマージを 1 本のスクリプトにする（オートクルーズの要件候補 4）

#389 の要件候補 7 つのうち、**この周は 4（マージの自動化）だけ**（利用者の判断。2026-10-24・AskUserQuestion）。
残りは #390〜#395 に分けた（利用者の指示「残りは別課題」）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py` — 新規。CI 待ち → worktree の点検 → squash → worktree の撤去 → 閉じた Issue の確認
- `scripts/test-merge-pr.py` — 新規。偽の `gh` と本物の `git` で当てる回帰テスト（変異テストを含む）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 7 にスクリプトを指す項を足す。版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.45.0 → 1.46.0。道具の追加なので minor）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `scripts/check-all.py` — `TESTS` に `test-merge-pr.py` を足す
- `.github/workflows/plugins.yml` — テストのステップを足す
- `CLAUDE.md` — `scripts/` の一覧に `test-merge-pr.py` を足す
- `docs/plans/issue-389.md` — この計画

触らない:

- ブランチの削除（ローカル・リモートとも）——squash したブランチは git から見て未マージなので `-d` が通らず、`-D` は破壊的。報告だけにする
- 要件候補 1〜3・5〜7（#390〜#395）
- `check-pr-preconditions.sh`・`prepare-worktree.sh`
- マージしてよいかの判断（承認）——スクリプトは**マージすると決めた後**の手続きだけを担う

### 同じことを述べている箇所の数

- 「マージの手続き（待つ・点検・squash・確かめる）」: `merge-pr.py` の docstring・`SKILL.md` 手順 7 の 1 項 —— 2 箇所。**終了コードと守る／守らないは docstring を正とし、`SKILL.md` は指すだけ**（列挙を持たない）。
- 分けない理由: 1 本のスクリプトと、その入口の 1 行なので分けようがない。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` は main への push で Pages に載る。

## 周の在り処

- ブランチ: `issue/389-merge-pr-script`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-389`
- 起点: `fdcf631`（Merge pull request #386）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `fdcf631bcc50b87bd40c0e3eb1826ab0f850414e`

## 設計

`merge-pr.py <PR 番号>`（cwd のリポジトリ。標準ライブラリのみ）:

1. **待つ**: `gh pr view --json` を一定間隔で読み、**CI がすべて通り、かつ `mergeable` が `MERGEABLE`** になるまで待つ。
   `UNKNOWN` は「まだ計算中」として待ち続ける（#389 で 2 回止まった罠）。失敗した検査・`CONFLICTING` は即座に止める。
   **検査が 0 本**は通過と読まない（CLAUDE.md: `CONFLICTING` の PR で `no checks reported` になり CI が 1 本も走っていなかった）。
2. **点検**（マージの前）: head ブランチを持つ worktree があれば、未コミットの変更が無いこと・HEAD が PR の head の SHA と一致すること（push 済み）を見る。cwd がその worktree の中なら止める。
3. **squash**: `gh pr merge --squash --match-head-commit <待って見た SHA>`——**待っている間に head が動いたら、見ていないコミットをマージしない**。
4. **撤去**（マージの後）: worktree がロックされていれば `git worktree unlock`（`Agent` の `isolation: worktree` が作るものはロックされている。#389 の罠）、`git worktree remove`（`--force` は使わない）。
   **撤去をマージの後に置く**のは、マージが失敗したとき worktree を残すため。
5. **確かめる**: PR が `MERGED` になったこと、`closingIssuesReferences` の各 Issue が `CLOSED` になったことを、待って再試行しながら見る。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| M1 | `mergeable` が `UNKNOWN` の間は止まらずに待ち、`MERGEABLE` になればマージする | 待ちの判定 | 試料: UNKNOWN → MERGEABLE |
| M2 | 期限までに `MERGEABLE` かつ CI 全通過にならなければ、マージせずに「時間切れ」で止まる（UNKNOWN のまま・検査が走り続ける・検査が 0 本の 3 つ） | 待ちの判定 | 試料 3 つ。`gh pr merge` が呼ばれていないこと |
| M3 | 失敗した検査が 1 本でもあればマージしない（期限を待たずに止まる） | 検査の読み方（`CheckRun` の `conclusion`・`StatusContext` の `state`） | 試料: 片方の型ずつ |
| M4 | `CONFLICTING` ならマージしない | 待ちの判定 | 試料 |
| M5 | マージは squash で、**待って見た head の SHA** を `--match-head-commit` に渡す | `gh pr merge` の引数 | 偽の `gh` が引数を記録 |
| M6 | head ブランチの worktree に未コミットの変更があるなら、マージせず worktree も残す | 点検 | 試料 |
| M7 | head ブランチの worktree の HEAD が PR の head の SHA と違う（push していない）なら、マージせず worktree も残す | 点検 | 試料 |
| M8 | cwd が撤去する worktree の中なら、マージしない | 点検 | 試料 |
| M9 | ロックされた worktree は、マージの後に unlock して撤去できる（`--force` を使わない） | 撤去 | 試料: `git worktree lock --reason "claude agent …"` |
| M10 | マージが失敗したら worktree を撤去しない | 撤去の順序 | 試料: `gh pr merge` が非 0 |
| M11 | マージの後、閉じるはずの Issue が `CLOSED` にならなければ、0 で終わらない（マージ済みであることは言う） | 確かめ | 試料 |
| M12 | PR が `OPEN` でない・draft なら何もしない | 入口 | 試料 |
| M13 | `gh` が失敗・JSON が読めないとき、「通った」「時間切れ」と答えずに「判定できなかった」で止まる | 全段 | 試料: 偽の `gh` が非 0 |
| M14 | 終了コードが段ごとに分かれ、docstring の一覧と一致する | docstring | テストが突き合わせる |
| M15 | docstring の「守る」の各行に変異が 1 つあり、壊すと赤（テストが数える） | `MUTATIONS` | 変異テスト。陽性対照: 壊さない本体で全試料が緑 |
| M16 | テストは実リポジトリ・実の GitHub を触らない（偽の `gh` を `PATH` の先頭に置く・対象はテンポラリ） | テスト | `assert_not_real_repo`。偽の `gh` が呼ばれたことを見る |
| X1 | 版が 3 箇所で揃う・生成ブロックが新しい・全歯止めが緑 | 版・§8.2 | `check-all.py` |

### この環境では証明できないもの（未証明）

- **本物の GitHub の `gh` の出力形**（`statusCheckRollup` の型ごとのフィールド、`UNKNOWN` から戻るまでの時間）。テストは偽の `gh` で当てる。形は 2026-10-24 に `gh pr view 386 --json …`（gh 2.92.0）で 1 度だけ見た。
- **本物のマージ**——公開リポジトリで試しにマージすることはしない。

### 必須要件の掛け算

- 受入基準 × 2 つの関門（Verifier・`/code-review`）× 2 パス = 4 つの受け渡し。2 パス目の修正は狭いパス。

### 生成物

- 該当あり: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を触るので）。`skill-metrics.py --check` が緑であることを受入基準 X1 に入れた。
- 図の書き出し: 該当なし（drawio を触らない）。

## 未解決の判断・確認待ち

- なし（範囲は利用者が決めた）。

## 関門の進捗（再開点）

- 実装: 済み（`merge-pr.py`・`test-merge-pr.py`・`SKILL.md` 手順 7 の 1 項・版 1.46.0・`check-all.py`・`plugins.yml`・`CLAUDE.md`・§8.2 を再生成）
- 実験: `test-merge-pr.py` のみ（偽の `gh` と本物の `git`）。陽性対照 18 試料が期待どおり → 変異 12 件すべて赤。
  交絡の候補「偽の `gh` が呼ばれず本物が走った」→ 偽の `gh` の記録が残ることを見て潰した。
  「ロックが掛かっていないので unlock が要らなかった」→ 変異「unlock しない」が撤去の失敗（rc=9）で赤になることで、ロックが効いていることを見た
- 関門 1 パス目:
    - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **済み。反証 0 件**。弱い箇所 3 件（採否の表 V1〜V3）。`git status` 前の 1 回目を取り損ねた（後の 2 回は同一）
    - `/code-review`（high）: **済み。指摘 9 件**（R1〜R9）
    - 採否: 直す 5 件（R1・R2・R3・R4・R6）／残課題 7 件（R5・R7 の残り・R8・R9・V1・V2）。V3 は R6 と同じ
    - 指摘対応: **済み**（R1・R2・R3・R4・R6）。probe を修正後の本体に当て直し、R1 → rc=8・worktree 残る／R2 → rc=7・済んだことを出力／R3 → rc=6／R4 → rc=7・マージしない／R6 の変異（最初に読んだ SHA）→ 21/22 で赤
    - テスト: 試料 18 → 23。変異 12 件のまま（守る 12 行と 1 対 1）。全変異が構文として通ることを確かめた（赤の理由が SyntaxError でない）。`test-merge-pr.py` 59 ok
    - 歯止め: `check-all.py` 45/45 緑（指摘対応のコミットの時点）
- 関門 2 パス目（2026-10-25。再開の周）:
    - 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `43b9d7d`
    - `/code-review`（high）: **済み。指摘 10 件**（R2-1〜R2-10。うち 5 件は probe で実物を示した）
    - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **済み。反証 1 件**（V2-1: 版の衝突。`merge-pr.py` への反証は 0 件）。軽微な所見 2 件（V2-2・V2-3）。
      Verifier は頼まれていない `check-all.py` を回して 10 分を超えたと自己申告した（結果は親の実行と同じ 45 本中 1 本が赤）
    - 採否: 直す 4 件（R2-3・R2-4・R2-5・V2-1）／残課題 8 件。表は下の「2 パス目の指摘の採否」
    - 指摘対応: **済み**。R2-3・R2-4・R2-5 → `e541e76`（試料 6 件を足した。修正前の本体で 6 件とも赤・修正後は緑）。
      V2-1 → `47a45e9`（`git merge origin/main`。`check-all.py` の `TESTS` と §8.2 の生成ブロックが衝突し、前者は両方を残し、後者は main 側を取って `skill-metrics.py` で書き直した。版は 1.47.0）
    - 狭いパス（`git diff 43b9d7d e541e76`。終点を指摘対応のコミットにしたのは、その後の取り込みで main の変更が混ざるため）: Verifier（sonnet）**済み。反証 1 件**（N-1）。
      Verifier が設計した変異 7 件: 赤 5 件（`conclusion`・`StatusContext` の `state`・PR の `state`・`isDraft` の各 guard を外す、`closing` を `or []` に戻す）／
      素通り 2 件（N-1・N-2）。修正前の本体に当てる著者の主張は Verifier 側では走らせていない（未確認）。
      `git status` の 2 回の差（計画ファイル）は親の編集
- この周の起票: 0 件
- 割り目 2（2 パス目の前）: 利用者は「ここで割る」を選んだ（2026-10-24）。**次は Verifier 2 パス目と `/code-review` 2 パス目**（base は上の `fdcf631…` のまま。2 パス目の指摘対応を始める直前の HEAD を、狭いパスの起点としてここに書くこと）
- 歯止め: `check-all.py` 45/45 緑（実装コミット `33d30ef` の時点）
- 割り目 1（手順 4 の後）: 利用者は「ここで割る」を選んだ（2026-10-24）。**次は手順 5 の Verifier 1 パス目から**
- メモ: 手元で読み込まれた dev-loop は 1.37.0（キャッシュが古い）。リポジトリの `SKILL.md`（1.46.0）を正として進める

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| ブランチを消すか | 消さない | squash したブランチは `git branch -d` が通らず、`-D` は破壊的。範囲の外 |
| 撤去はマージの前か後か | 後 | マージが失敗したら worktree を残すため。点検（未コミット・push 済み）はマージの前に済ませる |
| 検査 0 本を通過とするか | しない（待ち、期限で時間切れ） | CI の無いリポジトリでは使えないが、`CONFLICTING` で CI が走っていない状態を通過と読む誤りのほうが重い |
| ignore された worktree のファイル（`.env` など）を撤去で失う | 残課題（直さない） | `--ignored` で止めると `.venv`・`__pycache__` を持つふつうの worktree が撤去できなくなる。M6 は「未コミットの変更」で、ignore されたものは含めていない |

### 1 パス目の指摘の採否

probe: `scratchpad/probe.py`（テストの `run_case` を流用。偽の `gh`・テンポラリのみ）で、修正前の本体に当てた。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | `gh pr merge` が 0 で終わった直後に撤去し、`MERGED` を確かめる前に worktree を消す（マージキュー） | 示せる: `after=["OPEN"]` で rc=9・worktree 消失 | M10 | 直す（`MERGED` を確かめてから撤去。ならなければ 8・worktree を残す） |
| R2 | マージの後の `gh` の失敗を「MERGED にならない」「Issue が閉じない」（時間切れ）と答える | 示せる: マージ後の `state` 読みが rc=1 で「PR #42 が MERGED にならない（0.5 秒）」・rc=9 | M13 | 直す（7。どこまで済んだかを出力が言う） |
| R3 | `status.showUntrackedFiles=no` だと未追跡を見落とし、撤去で消す | 示せる: 未追跡 `dirty.txt` を置いて rc=0・マージ・worktree ごと消失 | M6 | 直す（`--untracked-files=all`）。ignore されたファイルは決着済みの論点へ |
| R4 | 想定外の形（`closingIssuesReferences: [null]` など）で例外を投げ、Python の 1（＝引数の誤り）で終わる | 示せる: rc=1・マージ済み・worktree 消失 | M13・M14 | 直す（形をマージの前に確かめ、読めなければ 7） |
| R5 | 呼んだセッションの cwd が撤去する worktree でも、`cd` してから呼ぶと素通り | 示せない（セッションの cwd はスクリプトから見えない） | 無し（M8 はスクリプトの cwd） | 残課題 |
| R6 | M5 の試料が「待って見た SHA」を判別しない（全 view が同じ SHA） | 示せる: 最初に読んだ PR を返す変異で 18/18 緑・`merge_args_ok` も真 | M5 | 直す（UNKNOWN の間は別の SHA を返す試料にする） |
| R7 | 試料の無い分岐（メインの作業ツリー・ロック無し・worktree 無し・JSON でない出力・マージ後の失敗・「マージはした」の文言） | マージ後の失敗だけ示せる（R2） | R2 分は M13 | R2 の分は R2 で直す。残りは残課題 |
| R8 | テストと本体の `subprocess` にタイムアウトが無く、期限を壊す変異でハングする | 示せない（いまの本体・変異では起きていない） | 無し | 残課題 |
| R9 | 閉じる Issue を 1 件ずつ settle で待つので最悪 (件数+1)×settle | 示せない（遅いだけで判定は正しい） | 無し | 残課題 |
| V1 | `StatusContext` の失敗に変異が無い（試料はある） | 試料は効く（Verifier が当てて赤） | 無し（M15 は 1 行 1 変異で満たす） | 残課題 |
| V2 | `STATUS_PENDING` を壊す変異が無い | 示せない（未確認） | 無し | 残課題 |
| V3 | R6 と同じ | R6 | M5 | R6 で直す |

### 2 パス目の指摘の採否

`/code-review` の probe は `scratchpad/rv2probe/`（偽の `gh`・テンポラリ）。**2 パス目で直した行は 2 つの関門に当て直さず、狭いパスだけ当てる。**

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R2-1 | unlock の後に `git worktree remove` が失敗すると、ロックを戻さない（V2-3 も同じ） | 示せる: rc=9・worktree 残る・`locked` が消える | 無し（M9 は撤去できること。失敗時のロックは基準に無い） | 残課題 |
| R2-2 | 7 で終わるとき `done` だけを出し、撤去の失敗（`problems`）を捨てる | 示せる: 撤去の失敗＋`gh issue view` の失敗で rc=7・撤去の失敗が出力に無い | 無し（M13 の「7 で止まる」は満たす。docstring の「出力が言う」とは食い違う） | 残課題 |
| R2-3 | PR に `state` が無いと「PR は None である」で 2（`isDraft` が無いと draft でない扱い） | 示せる: `{}` で rc=2 | M13 | 直す（`state`・`isDraft` の形が読めなければ 7） |
| R2-4 | `CheckRun` の `conclusion`・`StatusContext` の `state` が無いと失敗した検査（3）と答える | 示せる: rc=3・「x（None）」 | M13 | 直す（読めなければ 7） |
| R2-5 | `closingIssuesReferences` が無い・null だと「閉じる Issue は無い」としてマージし 0 | 示せる: rc=0・マージ・撤去 | M11・M13 | 直す（無い・null ならマージの前に 7） |
| R2-6 | `mergeable` が読めず検査が失敗していると 3 になり、読めないことが隠れる | 示せる: rc=3 | 無し（検査の失敗は読めており、答えは正しい） | 残課題 |
| R2-7 | fork の PR（`isCrossRepository`）でも head のブランチ名だけで worktree を当てる | 示せない（走らせていない） | 無し | 残課題 |
| R2-8 | 「検査が走っている間は待つ」の試料が待ったことを見ない。M15 の 1 対 1 は数だけ比べる | 示せる: 変異が当該試料では緑（別の試料で赤） | 無し（M15 は全変異が赤で満たす） | 残課題 |
| R2-9 | テストの `git()` が終了コードを見ず、`GIT_DIR` などの環境を素通しする | 示せない（走らせていない） | 無し | 残課題 |
| R2-10 | 待っている間の一時的な `gh` の失敗で即 7（マージ後の `wait_for` は期限まで許す） | 示せない（設計の非対称） | 無し | 残課題 |
| V2-1 | main が先に dev-loop を 1.46.0 に上げ、`check-version-bump.py` が赤 | 示せる: `check-all.py` 45 本中 1 本が赤 | X1 | 直す（`git merge origin/main` → 1.47.0） |
| V2-2 | `--interval` が負だと `time.sleep` が `ValueError` で rc=1 | 示せない（静的に読んだだけ） | 無し | 残課題 |
| V2-3 | R2-1 と同じ | R2-1 | 無し | 残課題 |

### 狭いパスの指摘の採否（直さない。人間が決める）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N-1 | `CheckRun` の `status` の guard（R2-4 の修正に含めた）に試料が無く、外しても全試料が緑 | 示せる: 外した本体に `status` の無い `CheckRun` を当てると rc=5（時間切れ）。元の本体は rc=7 | M13（挙動は守られているが、壊しても試料が赤にならない） | 人間が決める |
| N-2 | `isDraft` の guard を `is None` だけに弱めても緑（`bool` でない値の試料が無い） | 示せない（陽性対照を取っていない） | 無し | 人間が決める |
