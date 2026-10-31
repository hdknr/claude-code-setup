# Issue #687（＋#494）— check-all の 1 回を軽くする（長い柱の 2 本）・check-all と check-mutation-claims のテストの土台

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-10-31）の周。**不在の周**である——訊く場面は
  `references/absent-lines.md` の「訊く場面」のとおり訊かずに進める（`AskUserQuestion` を使わない）。この周は cruise の親から委ねられ、
  `EnterWorktree` を使わず worktree の絶対パスで作業する。マージは親が行う（この周は PR・PR 側の CI・関門 2 パス・狭いパス・手順 8 の件数の行まで）。
  台帳は書かない。
- まとめて回す Issue: **#494**（台帳のまとめの代表）・**#687**。親が `ledger.py group` で記録したまとめ。
  2 件の受入基準をこの周の受入基準とする（下の表に Issue 番号を付けて書く）。
- **単独で回す周**（台帳の `note` の `単独: check-all の所要時間を測る`。cruise `references/parallel.md` の「単独で回す周」）——
  測定のあいだ他の cruise の周は走っていない。**機械の上の他のプロセスは交絡として残る**ので、測定ごとに `uptime` の負荷を書く。
  重い検査は `run-serial.py` 越しに走らせた（`parallel.md` の「重い検査とアプリの起動は、順番待ちに通す」）。
- 使った線（出所: 利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた）。
  cruise の台帳 `issue-474` の確かめた線を親から受けた）:
  `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`。
- 利用者の直接の指示（2026-10-29、親から受けた）: 人間の判断が要るもの（狭いパスの指摘を含む）は推奨で決め、`要確認:` で始まる題の Issue
  （本文の先頭に `<!-- cruise-decision: #474 -->`、ラベル `要確認`。#557 の形）で確かめる。起票はこの周が行い、番号を親に報告する。
- 直す線: **既定**（出所: 同上の cruise の確かめた線）。
- 版: **上げない**——触るのは `scripts/` と計画ファイルだけで、プラグインのファイルを触らない（`CLAUDE.md`「プラグインの更新」）。

### 周の名前が代表の番号でない理由（#494 ではなく #687）

- `find-cycle.py 494` は前の周（PR #674。マージ済み・2026-10-30）のブランチ `issue/494-check-all-bundle`（ローカルとリモート）・
  計画ファイル `docs/plans/issue-494.md` に当たった。worktree は無い。**前の周はマージ済みで、再開の周ではない**（新しい周）。
- `prepare-worktree.sh 494 …` は残ったブランチに当たって 3（作らない）を返す。残ったブランチを消す
  `git branch -D issue/494-check-all-bundle`・`git push origin --delete issue/494-check-all-bundle` は**権限の分類器に拒まれた**（Git Destructive）。
  回避はしていない（親に報告する）。
- そこで**まとめのもう 1 件 #687 の番号で切った**（`prepare-worktree.sh 687 check-all-light`）。計画ファイルも `docs/plans/issue-687.md`
  ——`check-plan-scope.py` はブランチ名の番号で計画ファイルを当てるので、ここに置かないと変更範囲の歯止めが「判定していない」に落ちる。
  **前の周の計画ファイル `docs/plans/issue-494.md` は触らない**（件数の行は 1 ファイル 1 本——同じファイルに 2 つの周を書けない）。
  台帳のまとめの代表は #494 のまま（親が書く）。

## 変更範囲

触る:

- `scripts/test-ledger.py` — 変異の回を、正しい本体と観測が食い違った時点で止める（`Observations`）・変異を別々のプロセスで同時に当てる（#494）
- `scripts/test-check-unattended-env.py` — `_Killed` を `BaseException` の子に（#687）・変異を別々のプロセスで同時に当てる（#494）
- `scripts/test-check-all.py` — 待ち合わせの上限を作業者の数で分ける・契約 10 の 0.2 秒の眠りを印に・FAIL の行の数の表明だけが捕まえる変異・
  CI のステップの引数の検査・`argparse`（#687）
- `scripts/test-check-mutation-claims.py` — 変異の前の観測を 2 回取って揃うことを要求する・`argparse`（#687）
- `scripts/check-mutation-claims.py` — docstring の `red` の決まり（丸ごと回してよい軽い回帰テスト。#687）
- `docs/plans/issue-687.md` — この計画

触らない:

- `docs/plans/issue-494.md`（前の周の記録）
- `scripts/check-all.py`——一度 `TESTS` を測った長さの順に並べ替えて広げたが、測って悪くなったので戻した（下の「採った候補と採らなかった候補」）。差分に残らない
- 入力の指紋で検査を飛ばす (c)——採らない（下の「採った候補と採らなかった候補」）
- 他の重い回帰テスト（`test-build-proposal.py`・`test-schedule-to-gantt.py` など）——下の「採った候補と採らなかった候補」

## 複製の数

- 「変異は宣言順に出す・作業者で同時に当てる」の決まりは `test-ledger.py` と `test-check-unattended-env.py` の 2 箇所に書いた
  （同じ形の小さな補助。テストごとに観測の取り方が違うので 1 つにまとめない——共有の補助を作ると、`scripts/` に新しい共有モジュールと
  その収録・回帰テストが要る）。
- `BARRIER_WAIT` の意味は `test-check-all.py` の中の 3 箇所（定数の上・`record_pools`・契約 6 の注記）。
- `check-mutation-claims.py` の docstring の `red` の決まりは 1 箇所。

## デプロイ経路

- 反映経路なし（`scripts/` と計画ファイルだけ。公開サイトに載らない・プラグインの配布に入らない）。CI（`plugins.yml`）が各テストを回す。

## 測ったこと（#494 の求めること 1）

**条件**: 2026-10-31、10 コアの macOS（Darwin 27.0.0）・Python 3.14.3（CI は 3.12）。**単独で回す周**で、他の cruise の周は走っていない
（機械の上の他のプロセス——端末 33 本など——は残る。負荷の平均は何もしていないときで 3〜4）。重い測定は `run-serial.py` 越し。
台本は scratchpad の `i494-time.py`（1 本ずつ直列に起こす）・`i494-ca-prof.py`（`check-all.py` の `run` を包み、各子の開始と終了を記録する。本体は変えない）。

### 1 本ずつ直列に回した wall（変える前の木 `4311a9c`。`check-all.py` が渡すのと同じ引数。入れ子は `--jobs 5`）

| スクリプト | 秒 | rc | 負荷（前→後） |
| --- | --- | --- | --- |
| `test-ledger.py` | 634 | 0 | 4.5→3.4 |
| `test-check-unattended-env.py` | 405 | 0 | 3.4→5.0 |
| `test-build-proposal.py` | 293 | 0 | 4.3→4.2 |
| `test-schedule-to-gantt.py` | 185 | 0 | 3.5→3.5 |
| `test-parent-issue.py` | 98 | 0 | 3.4→8.2 |
| `test-run-serial.py` | 92 | 0 | 6.5→4.6 |
| `test-worktree-scripts.py` | 81 | 0 | 4.6→3.9 |
| `test-scaffold.py` | 80 | 1（測定の台本の交絡——下） | 4.2→4.1 |
| `test-check-spec-exit.py` | 76 | 0 | 4.3→3.7 |
| `test-check-frozen.py` | 63 | 0 | 3.9→4.5 |
| `test-check-mutation-claims.py` | 61 | 0 | 3.9→4.7 |
| `test-merge-pr.py` | 52 | 0 | 4.9→6.3 |
| `test-check-signoff.py` | 49 | 0 | 3.5→4.3 |
| `test-qa-to-pptx.py` | 46 | 0 | 4.8→4.3 |
| `test-launch-with-long-token.py` | 43 | 0 | 5.0→4.5 |
| `check-mutation-claims.py` | 38 | 0 | 3.1→4.0 |
| `test-check-all.py` | 31 | 0 | 4.5→3.8 |
| `test-child-cycle.py` | 30 | 0 | 8.2→6.5 |
| `test-check-version-bump.py` | 27 | 0 | 4.6→4.5 |
| `test-check-feasibility-csv.py` | 26 | 0 | 3.7→3.5 |
| `test-merge-versions.py` | 21 | 0 | 4.1→4.0 |
| `test-check-plan-scope.py` | 19 | 0 | 3.8→3.6 |
| `test-tab-match.py` | 14 | 0 | 4.5→4.9 |
| `test-check-description-sync.py` | 12 | 0 | 4.3→4.6 |
| `test-record-stop-failure.py` | 11 | 0 | 3.6→3.4 |
| `test-check-qa-csv.py` | 5 | 0 | 4.7→4.8 |
| `test-init-mkdocs.py` | 5 | 0 | 4.5→4.5 |
| `test-check-diagram-freshness.py` | 5 | 0 | 4.4→4.3 |
| `test-diff-versions.py` | 5 | 0 | 4.0→3.9 |
| `test-token-metrics.py` | 4 | 0 | 4.6→4.5 |
| `test-link-skills.py` | 4 | 0 | 4.5→4.5 |
| `test-check-plugin-versions.py` | 3 | 0 | 4.0→4.4 |
| `test-export-diagrams.py` | 3 | 0 | 4.5→4.6 |
| `test-check-bold-flanking.py` | 2 | 0 | 4.6→4.6 |
| `test-run-dev-loop-evals.py` | 2 | 0 | 4.7→4.7 |
| `test-check-skill-pointers.py` | 2 | 0 | 3.9→3.9 |
| `test-skill-metrics.py` | 2 | 0 | 4.5→4.5 |
| `test-check-site-links.py` | 1 | 0 | 4.4→4.4 |
| `test-find-cycle.py` | 1 | 0 | 3.4→3.4 |
| `check-duplicate-counts.py` | 1 | 0 | 4.0→4.0 |
| `check-skill-pointers.py` | 1 | 0 | 4.0→4.0 |
| `check-description-sync.py` | 0 | 0 | 4.0→4.0 |
| `test-count-usage-limit-resumes.py` | 0 | 0 | 3.6→3.6 |
| `test-check-plan-counts.py` | 0 | 0 | 4.9→4.9 |
| `check-site-links.py` | 0 | 0 | 4.0→4.0 |
| `test-check-norm-markers.py` | 0 | 0 | 4.4→4.4 |
| `check-plan-counts.py` | 0 | 0 | 4.0→4.0 |
| `check-bold-flanking.py` | 0 | 0 | 4.0→4.0 |
| `check-diagram-freshness.py` | 0 | 0 | 4.0→4.0 |
| `check-norm-markers.py` | 0 | 0 | 4.0→4.0 |
| `test-count-resume-recreations.py` | 0 | 0 | 3.6→3.6 |
| `test-collect-guard-rejections.py` | 0 | 0 | 3.6→3.6 |
| `check-plugin-versions.py` | 0 | 0 | 4.0→4.0 |
| `skill-metrics.py` | 0 | 0 | 4.0→4.0 |
| `check-version-bump.py` | 0 | 0 | 4.0→4.0 |
| `check-plan-scope.py` | 0 | 0 | 4.0→4.0 |
| `test-check-duplicate-counts.py` | 0 | 0 | 4.6→4.6 |

- 合計 2,534 秒（57 本）。**上位 4 本（`test-ledger.py`・`test-check-unattended-env.py`・`test-build-proposal.py`・`test-schedule-to-gantt.py`）で 1,517 秒**。
- **`test-scaffold.py` の rc=1 は測定の台本の交絡**（実の失敗ではない）——台本が子に `PYTHONDONTWRITEBYTECODE=1` を渡していたので、
  変異「バイトコードを書く」が生き残った。素のまま回すと rc=0、同じ環境変数を付けると rc=1 を再現した。`check-all.py` はこの変数を付けない。
  以後の台本はこの変数を `red` の測定（`check-mutation-claims.py` が付ける）にだけ付けた。

### `check-mutation-claims.py` の主張ごとの `red`（変異なし・1 回ずつ・`.git` の無い退避先で。負荷 4〜5）

- 測った時点の 38 件の合計 55 秒。最大は `test-worktree-scripts.py --mutant '見られなくても作る'` の 8.6 秒。
- **丸ごと回している 25 件**（`test-check-skill-pointers.py` 23 件・`test-check-duplicate-counts.py` 2 件）は 1 回 1.8 秒以下・合計 28 秒。
  → **狭めても得られるのは 1 回の `check-mutation-claims.py` で数十秒まで**。直列で 38 秒の `check-mutation-claims.py` は柱ではない。

### `test-ledger.py` の中（`i494-ledger-prof.py`）

- `scenario` 1 回 11.6 秒（観測の鍵 167）。正しい本体 1 回＋変異 51 件（`MUTATIONS` 43・`SAMPLE_MUTATIONS` 8）で毎回これを回し切っていた。
- **51 件とも観測が食い違い、初めて食い違うのは `scenario` の時間の中央値 32%・平均 43% の時点**——食い違った時点で止めれば半分ほどで済む。
- 止める形にした後の直列の 1 回で、実時間 456 秒に対してユーザー CPU 144 秒——**大半は本物の `git` の子を待つ時間**で、同時に当てられる。

### `check-all.py` の中の各子（`i494-ca-prof.py`。`--jobs 10`）

- **途中の木**（`test-ledger.py`・`test-check-unattended-env.py` だけ直した木）で 1 回 1,017 秒。負荷は 15〜28 に上がり、各子は直列の 2〜5 倍に延びた。
  **最後に終わった 2 本は `test-build-proposal.py`（274 秒に起動・743 秒）と `test-schedule-to-gantt.py`（218 秒に起動・736 秒）**——
  どちらも `TESTS` の末尾近くにあり、遅れて起動して wall の終わりを決めていた。→ `TESTS` の並べ替えを試した（下の「採った候補と採らなかった候補」。採らなかった）。

## 受入基準（不変条件 × 経路）

### #494

| # | 基準 | 証明 |
| --- | --- | --- |
| A1 | 各スクリプトの所要時間の表が、測った条件とともに残っている（`check-mutation-claims.py` は主張ごとの `red` も） | 上の「測ったこと」 |
| A2 | 他の周と重ならない条件で、`check-all.py` の 1 回の wall が測った値から下がっている（どれだけかを同じ条件で示す） | 下の「直した前後の比較」 |
| A3 | 変える前後で、各回帰テストが殺す変異の数が減っていない（変えたテストごと） | 下の「殺す変異の数」 |
| A4 | (c) を採るなら、入力を 1 文字変えると飛ばさずに回ることを示す | **該当なし**——(c) は採らない |
| A5 | **守るものを落とさない**——陽性対照・「当てられなかった」は緑ではない・**毎回全部回す（#117）**——飛ばす検査を足さない | 差分（`check-all.py` は変えない）と、変えたテストの陽性対照 |

### #687（チェックリストの各行）

| # | 基準 | 証明 |
| --- | --- | --- |
| B1 | `test-check-all.py`: 待ち合わせの上限が負荷で切れて、変異の前の本体の「同時に走る」が落ちない | 作業者が複数なら `BARRIER_WAIT`（30 秒）、作業者 1 の印があれば `BARRIER_SERIAL_WAIT`（0.5 秒）。変異は全部捕まえる |
| B2 | `test-check-all.py`: 契約 10 の 0.2 秒の眠りを足さない | 打ち切られる子の起動の印を待つ（`KILLED_WAIT` は上限） |
| B3 | `test-check-all.py`: 「FAIL の行の数 = 失敗 N」の表明が単独で捕まえる変異がある | 変異「落ちたものの出力の見出しを FAIL の行の形で出す」——表明ごとに破れた変異を数え、これを破るのはその表明だけ |
| B4 | `test-check-all.py`: CI の走査が、狭める引数を渡すステップを「全部回している」と数えない | `full_runs` と表明（合成試料・実物の `plugins.yml`）・`mutation-claim:`・変異 2 件 |
| B5 | `test-check-all.py`: 引数の読み取りが `argparse` | 知らない部分・名前・併用・余計な引数は 2 |
| B6 | `test-check-mutation-claims.py`: `--mutation` で、変異の無い観測の揺れを「殺した」と数えない | 変異の前の観測を 2 回取り、揃うことを表明する（全部を回す回にも）。陽性対照: 観測に時刻を足すと赤 |
| B7 | `test-check-mutation-claims.py`: 引数の読み取りが `argparse` | 同上 |
| B8 | `check-mutation-claims.py`: docstring の決まりと、丸ごと回す既存の主張が食い違わない | 決まりを書き直した（重い回帰テストは狭める・軽いものは丸ごとでよい。測った値つき） |
| B9 | `test-check-unattended-env.py`: `_Killed` が `except Exception` に飲まれない | `BaseException` の子にした |

### 不変条件と、それを破りうる経路

| 不変条件 | 破りうる経路 | どう守るか |
| --- | --- | --- |
| I1: 変える前に殺せた変異は、変えた後も殺せる（緑のままの変異は緑のまま報告される） | `test-ledger.py` の早く止める形（途中の値の食い違いを殺したと数える／止めずに見逃す）・同時に当てる形（結果の取り違え・作業者の例外）・`test-check-unattended-env.py` の同時に当てる形・`test-check-all.py` の待ち合わせの変更（直列に戻す変異が捕まらなくなる）・`test-check-mutation-claims.py` の 2 回目の観測 | 早く止めるのは観測の辞書の比較と同じ判定（前提の 2 つを正しい本体の回で表明）・結果は宣言順に組む・変異の数を前後で数える（A3） |
| I2: `check-all.py` は毎回全部を回す | この周は `check-all.py` を変えない（並べ替えは試して戻した）。テストの中で変異の一部を飛ばす形 | `check-all.py` の差分 0 行・`test-check-all.py` の収録漏れの検査・変えたテストは変異を全部当てる（早く止めるのは 1 件の変異の中だけ） |
| I3: テストは実リポジトリを書き換えない | 作業者のプロセスが環境（`HOME`・`GIT_*`）を受け継がずに本物を触る | `spawn` の子は親の `os.environ` を受け継ぐ（`isolate_env` の後に起こす）・`assert_not_real_repo`・実行の前後で `git status --porcelain` |
| I4: 出力は宣言順 | 作業者が終わった順に出す | `pool.map` は入力の順に返す |

### 証明できないもの（未証明）

- **CI（Linux・Python 3.12）での所要時間**——手元（macOS・3.14）で測った。CI は各テストを個別のステップで回す（`check-all.py` を使わない）。`spawn` の子の起動は CI でも動く前提（CI の結果で緑かどうかは見える）。
- **負荷 30 を大きく超えたときに、`BARRIER_WAIT`（30 秒）で足りるか**——負荷 50 で 0.5 秒が切れた記録がある（#494 の前の周）が、30 秒が切れる負荷は測っていない。

### 生成物

- **生成物なし**——`SKILL.md`・図・設計ドキュメントの生成ブロックに触らない（`scripts/` と計画ファイルだけ）。

## 採った候補と採らなかった候補（#494 の (a)〜(d)）

- **(a) `red` を狭くする——採らない（この周では）**。丸ごと回している 25 件は軽く（合計 28 秒）、`check-mutation-claims.py` は柱ではない。決まりの側を書き直した（B8）。
- **(b) 同じ `red` の陽性対照をまとめる——採らない**。同じ理由（`red` の合計が小さい）。
- **(c) 入力が変わっていない検査を飛ばす——採らない**。柱 4 本は直し方が見えており、飛ばす仕組みは「毎回全部回す（#117）」の例外を作る。
- **(d) 回帰テストの準備を軽くする——形を変えて採った**:
  - `test-ledger.py`: 変異の回を、観測が食い違った時点で止める（判定は変えない）・変異を 4 つのプロセスで同時に当てる。
  - `test-check-unattended-env.py`: 変異を 4 つのプロセスで同時に当てる（最初の失敗で止める形は前の周のまま）。
- **起動順——試して採らなかった**: `check-all.py` の `TESTS` を測った所要時間の長い順に並べた木で、1 回 1,348 秒（負荷 18〜23）——
  並べる前の木（途中の木）の 953・1,017 秒より長かった。重い 4 本が最初から同時に走り、どれも本物の `git` とファイルの作成が多いので
  互いに延びた（`test-build-proposal.py` は 0 秒に起動して 1,348 秒・`test-schedule-to-gantt.py` は 1,285 秒）。そのとき `fseventsd` が CPU 100%・
  `mds_stores` が 76% で、ファイルの出し入れが詰まっていた。1 回きりの測定だが、悪くなる向きの説明（重い I/O を同時に始める）があり、戻した。
- **`test-build-proposal.py`・`test-schedule-to-gantt.py` の中身——採らない（この周では）**。`test-build-proposal.py` の試料の回を 4 つのスレッドで
  同時に回す形を試したが、1 回の測定で 293 → 330 秒（遅くなった。試料 143 件・変異 146 件は同じ）——変えずに戻した。1 回きりの測定で、
  その時の負荷の揺れ（同じ木が 293 秒と、プロファイラ越しに 396 秒）と区別できていないので「遅くなる」とも言わない。周の途中の課題として親に渡す。

## 直した前後の比較（A2・A3）

**どちらも `.git` を持たない複製で、`check-all.py --jobs 10` を 1 回ずつ**（変える前の木は `git archive 4311a9c`・後の木は作業ツリーの `rsync --exclude .git`）。
前と後を交互に回した（同時には回さない——同時に回すと互いの負荷になる）。`check-plan-counts.py` の失敗（後の木の計画ファイルに件数の行がまだ無い。1 秒以下）が後の木の rc=1 の中身。

| 回 | 木 | wall | rc | 開始時の負荷 | 中の最大の負荷 | 最後に終わった子 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 前 | 1,203 秒 | 0 | 3.6 | （記録なし——台本が `i494-time.py`） | （記録なし） |
| 2 | 後（途中の木） | 953 秒 | 1 | 4.0 | （記録なし） | （記録なし） |
| 3 | 後（途中の木） | 1,017 秒 | 1 | 約 5 | 28 | `test-build-proposal.py`（274 秒に起動） |
| 4 | 後（並べ替えた木——戻した） | 1,348 秒 | 1 | 約 5 | 23 | `test-build-proposal.py`（0 秒に起動） |
| 5 | 前 | 1,425 秒 | 0 | 約 14 | 19 | `test-ledger.py`（44 秒に起動・1,381 秒） |
| 6 | 後 | 1,089 秒 | 1 | 約 4 | 24 | `test-build-proposal.py`（269 秒に起動） |

- 「途中の木」は、この周の変更のうち `check-mutation-claims.py` の docstring の言い回し（件数の歯止めに掛かった 1 語）と計画ファイルを除いた全部を持つ木。
- **前の 2 回（1,203・1,425 秒）と後の 3 回（953・1,017・1,089 秒）は重ならない**——後の最も長い回が前の最も短い回より 114 秒短い。
  中央同士で比べると 1,314 → 1,017 秒（−23%）。**どれだけ下がるかは負荷で揺れる**（前の 2 回で 222 秒の幅）ので、言えるのは「下がった・2 割前後」まで。
- **`check-all.py` の中の各子**（回 5 → 回 6）: `test-ledger.py` 1,381 → 625 秒・`test-check-unattended-env.py` 880 → 445 秒。
  後の木では最後に終わるのが `test-build-proposal.py`・`test-schedule-to-gantt.py`（この周で触らない）に移った——**次の柱はこの 2 本**。
- 回 5 の開始時の負荷は約 14（前の回 4 の終わりの残り）——回 1（3.6）と比べると、前の木の 2 回の差の一部はこの負荷の差である。

### 1 本ずつ直列に回したとき（変えたテスト）

| テスト | 前 | 後 | 負荷 |
| --- | --- | --- | --- |
| `test-ledger.py` | 634 秒 | 456 秒（早く止める形だけ）→ 201 秒（同時に当てる形も） | 3〜5 |
| `test-check-unattended-env.py` | 405 秒 | 180 秒 | 3〜5 |
| `test-check-all.py` | 31 秒 | 26 秒 | 4〜5 |

### 殺す変異の数（A3）

| テスト | 前 | 後 |
| --- | --- | --- |
| `test-ledger.py` | `MUTATIONS` 43・`SAMPLE_MUTATIONS` 8（全部殺す） | 同じ 43・8（全部殺す）＋前提の表明 1 |
| `test-check-unattended-env.py` | 123（全部赤） | 123（全部赤） |
| `test-check-all.py` | `MUTANTS` 18・`SCAN_MUTANTS` 8（全部捕まえる） | `MUTANTS` 19・`SCAN_MUTANTS` 10（全部捕まえる） |
| `test-check-mutation-claims.py` | `MUTATIONS` 22（全部殺す） | 22（全部殺す）＋変異の前の観測が揃う表明 1 |
| `check-mutation-claims.py` の主張 | 38 件確認 | 39 件確認（足した主張 1） |

## 交絡の扱い

- **測定の台本が結果を作った 1 件を見つけて外した**——上の `test-scaffold.py` の rc=1（`PYTHONDONTWRITEBYTECODE=1`）。
- **前後の比較は、どちらも `.git` を持たない複製で回した**（前は `git archive`、後は `rsync --exclude .git`）——base を要する歯止め 3 本が両方で SKIP する（条件は対称）。
- **負荷は機械の上の他のプロセスで動く**——比較は前後を交互に回し、各回の開始と終了の負荷を書く。
- 早く止める形の判定が止めない形と同じことは、殺した変異の数（43・8）が前後で同じことと、前提（同じ鍵を 2 度書かない・書いた値を変えない）の表明で見た。

## 既知の限界・決着済みの論点

- **前の周（PR #674）の A2 は満たしていなかった**——`check-mutation-claims.py` を速くしても、wall は最も長い回帰テストで決まっていた。この周は柱を縮める側から当てた。
- **`check-all.py` の中では負荷が 15〜28 に上がり、各子が直列の 2〜5 倍に延びる**——wall は「並べ方」と「仕事の総量」の両方で決まる。この周が減らしたのは
  総量（`test-ledger.py` の早く止める形）と、長い 2 本の中の待ち（同時に当てる形）で、`test-build-proposal.py` などの総量は残る。
- **同時に当てる作業者の数は 4 に固定した**（`MUTANT_JOBS`）——`check-all.py` の中では他の子と CPU を取り合う。#460 の入れ子の絞り方（親の半分）とは別の値で、
  `check-all.py` から渡す口は作っていない。
- **周の名前と計画ファイル**——上の「周の名前が代表の番号でない理由」。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/687-check-all-light`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-687`・
  起点コミット `4311a9c`・base `4311a9c0a31124e4dea0a607e55768d7909fdb3b`（参照 `origin/main`。`prepare-worktree.sh` の出力）
- 割り目（手順 4 の完了時）: 不在の周なので訊かない。このまま続ける。
- 実装のコミット: `a43630b`。
- PR: #747。
- 関門 1 パス目: 起点（1 パス目の関門に渡した時点の HEAD）`1d77fcd`。Verifier（sonnet）・`/code-review` を起動した（結果は未着）。
- 交絡を潰した手順: 上の「交絡の扱い」。

## 手順 8

- この周の起票: 0 件（関門の前。関門の後に書き直す）
