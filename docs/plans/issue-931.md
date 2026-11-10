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
  - Verifier: 報告待ち
  - `/code-review`: 報告待ち
- 交絡を潰した手順: 実験なし（変異と試料の当ては `check-mutation-claims.py`・`--part scan` が陽性対照つきで回す）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `merge-pr.py` の `CHECK_PASS` から `SKIPPED` を外すか | 外さない | `docs.yml` の `deploy` は PR では毎回 SKIPPED（`if: github.event_name == 'push'`）なので、外すと全部の PR が止まる。concurrency に取り消された run の CANCELLED（#932 の経路）にも触れない |
| ステップ単位の `if:` を見るか | 見ない（守らない） | PR 限定の 3 本（`check-version-bump.py` など）がステップの `if:` で正しく止めている。Issue の範囲はジョブ単位 |
| ジョブの `continue-on-error`・`timeout-minutes`・`strategy` | 見ない（守らない） | Issue の範囲外。走らなくする形ではない |

- この周の起票: 0 件
