# Issue #931 — CI: plugins.yml のジョブ単位の if・needs で走らなくなったジョブを歯止めが見ない

不在の周（cruise の子）。出所: `/dev-loop:cruise 934 --absent` の起動（2026-11-10T02:38Z）。親 Issue #934、台帳 `issue-934`（台帳は親だけが書く）。
従う版は dev-loop 1.103.0（キャッシュ。`SKILL.md` 1861 行）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-934`）——利用者の確認（起動時・2026-11-10T02:38:35Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票。実機確認は線が無い（止まる）
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-934`））
- 版の上げ方: **上げない**——`plugins/` を触らない（`merge-pr.py` の `CHECK_PASS` は変えない。下の「決着済みの論点」）
- PR は `Fixes #931`。手順 7 のマージは親がする（子は PR と PR 側の CI まで）

## 周の在り処

- ブランチ: `issue/931-ci-job-gates`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-931`
- 起点コミット: `5dc5b7e`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `5dc5b7ec0363662dc2df0e6e802426892e536017`

## 変更範囲

触る:
- `scripts/test-check-all.py` — CI の yaml を読み、収録したスクリプトの `run:` がジョブの `steps:` の下にあり、そのジョブがジョブ単位の `if:`・`needs:` を持たないことを見る。合成試料・判別の変異・`plugins.yml` を指す `mutation-claim` を足し、docstring の守る／守らないを直す
- `docs/plans/issue-931.md` — この計画

触らない:
- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py`——`CHECK_PASS` から `SKIPPED` を外すと、`docs.yml` の `deploy`（`if: github.event_name == 'push'`）が PR では毎回 SKIPPED になるので、全部の PR が 3 で止まる。歯止めは記述の側（`test-check-all.py`）に置く
- `.github/workflows/*.yml`——ジョブの形は変えない（#932 が `plugins.yml` の最上位に `concurrency` を足す。最上位の鍵は判定に影響しない）
- `CLAUDE.md`——`test-check-all.py` の行は「条件は docstring を正とする」と指すだけで、`if:` に触れていない（`grep` で確かめた）
- ステップ単位の `if:`・`continue-on-error`・ジョブの `continue-on-error`——Issue の範囲外（守らないに残す）

複製の数（同じことを述べている箇所）: 「ジョブの `if:` を見ていない」と述べるのは `test-check-all.py` の docstring の「守らない」の 1 箇所だけ（`grep 'if:' scripts/*.py CLAUDE.md` で確かめた）。直すのはそこと、新しく足す「守る」の項。

## デプロイ経路

`CI の歯止め`——main へのマージで次の PR・push から効く。`plugins/` を触らないので、プラグインの配布は起きない（GitHub Pages の再ビルドは起きるが、ページの中身は変わらない）。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **`check-all.py` に収録したスクリプトの生きた `run:` が、GitHub が無条件に走らせるジョブの `steps:` の下に 1 つも無いなら、`test-check-all.py --part registry` が赤になり、「そもそも無い」「コメントアウト」と分けて理由を名指しする。**
   経路（入口は `plugins.yml`・`docs.yml`・`release.yml` の書き方の全部）:
   (a) ジョブにジョブ単位の `if:` を足す（値に依らない。`if: false`・`if: github.event_name == 'push'`）、
   (b) ジョブに `needs:` を足す（1 行・リスト・フロー形式）、
   (c) `steps:` の後ろにジョブ単位の `if:`・`needs:` を書く（順序に依らない）、
   (d) ジョブの見出しのインデントを深くする（前のジョブの鍵になる——見出しだけ・ジョブごと）、
   (e) ジョブの見出しを浅くする（`jobs:` の外・最上位の鍵になる）、
   (f) `run:` の行が `steps:` の外にある（ジョブ単位の別の鍵の下）、
   (g) 同じジョブに同じ鍵が 2 つある（見出しだけ深くしたとき `steps:` が重なる）。
   守り方: 標準ライブラリだけで行を読み、`jobs:` の下のジョブの鍵とインデントを数える（`gated_runs`）。
2. **陽性対照: 今の 3 つの yml では緑のまま。** `docs.yml` の `deploy`（`if:`・`needs:` を持つが収録したスクリプトを持たない）で偽の赤を出さない。
   ステップ単位の `if:`（PR 限定の 3 本の歯止め）は今までどおり「走っている」に数える。同じスクリプトが無条件のジョブと条件つきのジョブの両方にあれば赤にしない。
3. **主張を機械で当てる**: 実物の `plugins.yml` に (a)(b)(d)(e) を入れると `--part registry` が赤になることを `mutation-claim` で書き、
   `check-mutation-claims.py` が当てる。合成試料（`SAMPLE_JOBS`）と判別の変異（`SCAN_MUTANTS`）で `gated_runs` の各分岐を 1 つずつ壊して捕まえる。
4. **既存の判別を壊さない**: `scan_ci_runs`・`full_runs` の契約（`--part scan`）と既存の `mutation-claim` が緑のまま。
5. `python3 scripts/check-all.py` が緑（run-serial 越し）で、PR 側の CI も全部緑。docstring の「守る」「守らない」が実装と合っている（ジョブ単位の `if:`・`needs:` は見る、ステップ単位の `if:`・`continue-on-error` は見ない）。

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）に渡す——4 つの受け渡し（2 パス目が該当なしなら 2 つ）。

検証で証明できるもの: 1〜5。

未証明: **GitHub が実際にジョブを走らせるかの記述の読み方**（YAML のアンカー・`<<` のマージ・再利用のワークフロー `uses:` のジョブ）は、行を読む判定と GitHub の読み方が違いうる。今の 3 つの yml には無い形なので、守らないに書く（受入基準ではない）。

生成物: なし（`test-check-all.py` は手で書くテストで、生成ブロックを持たない。`skill-metrics.py` の対象は `SKILL.md` だけ）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 実装: 済み・コミット済み（`6cdf32f`）。`check-all.py`（run-serial 越し）69/69 緑、`check-mutation-claims.py` 48/48 確認（44 → 48）
- PR: #942
- 手順 4 の割り目: 割らない（cruise の周）
- 関門 1 パス目: Verifier と `/code-review` に渡した（2026-11-10）。1 パス目の指摘対応の起点: `6cdf32f`（関門に渡した時点の HEAD。成果物はコミット済み）
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）1 パス目: **反証 2 件・テストの穴 2 件**（下の採否の表 V1〜V4）。4 つの `mutation-claim` を複製に当てて赤、base の版では素通り（陽性対照）を確かめた。報告は SubagentHandback で返ったが親に通知が届かず、トランスクリプトから読んだ
  - `/code-review`（high）1 パス目: **指摘 7 件**（下の採否の表 C1〜C7）。4 つの `mutation-claim`・8 件の `SCAN_MUTANTS` を複製で当てて確かめた
  - 手順 5 の反証による手順 4 への差し戻し: あり（V1・V4 を直す）
- 1 パス目の指摘対応: 済み（`42ad819`。V1——`KEY_RE` が引用符つきの鍵を読み `key_of` で名前を取る、V4——同じ名前のジョブを別のファイルに置いた試料・前のジョブより深い段の鍵の試料と、`SCAN_MUTANTS` 3 件）。
  `check-all.py`（run-serial 越し）69/69 緑。起点 `6cdf32f` からの成果物の差分は 0 行ではない（`scripts/test-check-all.py` 61 行足し 8 行消し）→ **2 パス目を回す**
- 2 つ目の割り目: 割らない（cruise の周）。残っているのは手順 5 の当て直し（Verifier 2 パス目）と手順 6 の `/code-review` 2 パス目の両方
- 2 パス目の経路の再導出: 指摘対応が足したのは鍵の読み方（引用符）と試料だけで、新しい入口は無い。未証明・生成物の該当は変わらない
- 2 パス目（2026-11-10）:
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）2 パス目: **反証 3 件**（下の 2 パス目の採否の表 VA〜VC）。`check-all.py` 69/69・4 つの `mutation-claim` と陽性対照を確かめた。報告は再び親に通知が届かず、トランスクリプトから読んだ
  - `/code-review`（high）2 パス目: **指摘 9 件**（下の表 R1〜R9）
  - 2 パス目の指摘対応の起点（狭いパスの起点）: `2db1b1d`（指摘対応を始める直前の HEAD）
  - 2 パス目の指摘対応の終点: `673cd2e`（VA——`KEY_RE` がコロンの前の空白を許す、VB——試料 `spaced`・`gap`・`odd`・`compact`・`x-jobs`・コメントアウトしたステップ・ラベルだけの名前と `SCAN_MUTANTS` 8 件、R6——docstring の守らないを実装に合わせる。壊した判別が例外で落ちたら契約が破れたと数える）。
    `check-all.py`（run-serial 越し）69/69 緑。`--part scan` の変異 34 件すべて捕まる
  - 狭いパス: 報告待ち（`git diff 2db1b1d 673cd2e` の `scripts/test-check-all.py` に当てる）
- 交絡を潰した手順: 実験なし（変異と試料の当ては `check-mutation-claims.py`・`--part scan` が陽性対照つきで回す）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `merge-pr.py` の `CHECK_PASS` から `SKIPPED` を外すか | 外さない | `docs.yml` の `deploy` は PR では毎回 SKIPPED（`if: github.event_name == 'push'`）なので、外すと全部の PR が止まる。concurrency に取り消された run の CANCELLED（#932 の経路）にも触れない |
| ステップ単位の `if:` を見るか | 見ない（守らない） | PR 限定の 3 本（`check-version-bump.py` など）がステップの `if:` で正しく止めている。Issue の範囲はジョブ単位 |
| ジョブの `continue-on-error`・`timeout-minutes`・`strategy` | 見ない（守らない） | Issue の範囲外。走らなくする形ではない |
| ジョブ単位の `if:`・`needs:` を値に依らず赤にする（`if: always()`・`needs: [setup]` も赤） | 採った（偽の赤を受け入れる） | 値を読んで「必ず走る」を決めるのは式の評価になり、行を読む判定の外。今の yml に該当は無く、向きは偽の赤（黙って素通しはしない） |

### 1 パス目の採否の表

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1・C3 | 引用符つきの鍵（`"if": false`・`'needs': x`）を鍵と読まず、無条件と数える（偽の緑） | 示せる——複製の `plugins.yml` に `"if": false` を足して `--part registry` が rc=0（Verifier・`/code-review` とも） | 1（経路 (a) の書き方の 1 つ） | **直す** |
| V2・C4 | `steps:` と同じ字下げの `- `（コンパクトな列）を `steps:` の外と読む（偽の赤・理由が「`steps:` の外（None）」） | 示せる——複製で rc=1 | 無し（今の 3 つの yml はこの書き方を使わない。向きは偽の赤） | 残課題 |
| V3 | 上の書き方を直す変異（`else key`）が `scan_contract` で素通り | 示せる | 無し（V2 を直さないので当て先が無い） | 残課題 |
| V4・C5 | `gated_runs` の 2 つの分岐（ジョブの識別子の連番・ジョブごとの `key_indent` の戻し）を、試料と `SCAN_MUTANTS` が押さえていない | 示せる——その変異で `scan_contract` が全部通る（両関門が複製で確かめた） | 3（「`gated_runs` の各分岐を 1 つずつ壊して捕まえる」） | **直す** |
| C1 | 無条件のジョブで狭めて、条件つきのジョブで全部を回すと、`gated_runs` と `full_runs` の両方が緑 | 示せる——合成の試料で（実物には無い形） | 無し（`full_runs` は #687 の検査。この周の受入基準は「無条件の位置に 1 つはあるか」） | 残課題 |
| C2 | ワークフローの `on:`（`workflow_dispatch` だけ・`paths:`）を見ない。docstring の「無条件に走らせる位置」が言い過ぎ、守らないに `on:` が無い | 示せる（`on:` を見ないこと）。**守らないに無い、は誤り**——モジュールの docstring の「守らない」に「`on:` を変えてワークフローを起動しなくする」がある | 無し（`on:` はこの周の経路の外で、モジュールの守らないにある） | 残課題（`gated_runs` の docstring の言い回し） |
| C6 | `needs:` を赤にする理由（コメントの「前のジョブが落ちると SKIPPED になる」）が黙って素通しする形を言っていない——前のジョブが落ちればそれが FAILURE で止まる。素通しは前のジョブが自分の `if:` で SKIPPED のとき | 示せない（文言） | 無し | 残課題 |
| C7 | 必ず走る `if:`（`always()`・`${{ true }}`）も赤にする偽の赤が、どこにも決着として書いていない | 示せる（合成） | 無し（上の決着済みの論点に足した） | 残課題（計画の決着に書いた） |

### 2 パス目の採否の表

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| VA・R1 | コロンの前に空白を置いた鍵（`if : false`・`"if" : false`・`needs : b`）を鍵と読まず無条件と数える（偽の緑。V1 の直しが一部） | 示せる——実物の `plugins.yml` の複製の `cruise-run-serial` に足して `--part registry` が rc=0（両関門） | 1（経路 (a)(b)） | **直す** |
| VB・R2・R3・R4・R5 | `gated_runs` の分岐のうち、空行・コメントだけの行を飛ばす・`split_comment` で生きた部分に絞る・`run:` の行に限る・`jobs` の完全一致・鍵を読むのは鍵の段だけ・`None` を鍵に足さない、を試料と変異が押さえていない | 示せる——その変異で `scan_contract` が全部通る（両関門が複製で確かめた） | 3（「各分岐を 1 つずつ壊して捕まえる」） | **直す** |
| R6 | docstring の「タブで字下げした行も数えない」が実装と違う——タブで始まる行は字下げ 0 の最上位と読み、そのファイルの残りのジョブを「ジョブの外」にする（偽の赤） | 示せる（合成） | 5（docstring の守らないが実装と合う） | **直す**（docstring を実装に合わせる） |
| VC | コンパクトな列（`steps:` と同じ字下げの `- `）の偽の赤が docstring の守らないに無い | 示せる（V2） | 無し（V2 と同じ。向きは偽の赤） | 残課題。ただし VB の「`None` を鍵に足さない」を押さえる試料にこの形を使うので、守らないの 1 行と契約の「守らない」の項は足す |
| R7 | 見出しだけ深くしたとき、手前のジョブが `runs-on:`・`steps:` を持たない（`uses:` のジョブ）と鍵が重ならず緑 | 示せる（合成。今の yml に `uses:` のジョブは無い） | 無し（`uses:` のジョブは守らないにある。GitHub はそのワークフローを不正として扱う） | 残課題 |
| R8 | `records.append` の `if in_jobs else None` は等価（読む人を誤らせる） | 示せない（挙動は変わらない） | 無し | 残課題 |
| R9 | 鍵の重なりを run の記録ごとに数え直す・届かない既定値 `(理由なし)` | 示せない（性能の推測・届かないコード） | 無し | 残課題 |

- この周の起票: 0 件
