# Issue #929 — CI: plugins.yml の check ジョブを重さで分割して並行に走らせる

利用者が居る周（2026-11-10、利用者の依頼で起票して回す）。従う版は dev-loop 1.103.0（キャッシュ）。

- 直す線: **既定**（出所: `.claude/dev-loop.md` が無く、訊く前の既定。周の途中で利用者の指示があれば書き換える）
- 版の上げ方: **上げない**——`plugins/` を触らない（`check-version-bump.py` の対象外）
- PR は `Fixes #929`

## 周の在り処

- ブランチ: `issue/929-ci-split-jobs`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-929`
- 起点コミット: `7e42c90`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `7e42c904f83248427572767eaf9eff3f7fd6db9e`

## 変更範囲

触る:
- `.github/workflows/plugins.yml` — `check` ジョブのステップを、ステップの本文を変えずに 7 つの名前つきジョブへ振り分ける
- `docs/plans/issue-929.md` — この計画

触らない:
- `.github/workflows/docs.yml`——31 秒で無関係
- テストの中身（`test-run-serial.py` の `sleep` など）——Issue の範囲外。分割後に全体を決めるのは最も重い 1 本なので、測ってから別 Issue
- `scripts/check-all.py`・`scripts/test-check-all.py`——`run:` の行を 1 行ずつ見る検査なので、行を保てば変えなくてよい
- `CLAUDE.md`——CI のジョブ構成を述べた箇所は無い（`grep` で確かめた）。「CI の 1 往復（約 13 分）」の記述は分割前から実測と合っていない別件

複製の数（同じことを述べている箇所）: ジョブへの振り分けを述べるのは `plugins.yml` の冒頭のコメントの **1 箇所**だけ。

### ジョブと実測の重さ（run 42612174778 のステップの秒数から見積もる）

| ジョブ | ステップ | 見積り |
| --- | --- | --- |
| `check` | カタログ・版・規約の歯止めとそのテスト、`check-mutation-claims.py`、`test-check-all.py` など 27 | 約 150 秒 |
| `dev-loop` | worktree・周の探索・台帳・親 Issue・子プロセス・片付け・マージなど 11 | 約 200 秒 |
| `cruise-run-serial` | `test-run-serial.py` | 約 333 秒 |
| `cruise-loops` | `test-outer-loop.py`・`test-parallel-stop.py` | 約 329 秒 |
| `spec-loop` | 残りの spec-loop 14（casefold のステップを含む） | 約 250 秒 |
| `spec-loop-generate` | scaffold・gantt・図の書き出し・表の検査 6 | 約 300 秒 |
| `spec-loop-autopilot-loop` | `test-autopilot-loop.py` | 約 350 秒 |

## デプロイ経路

`CI 定義`——main へのマージで次の PR・push から効く。本番（GitHub Pages・カタログ）へは何も配布しない。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **分割前に走っていたステップが、分割後もすべて同じ `name`・`if`・`run` で走る。**
   経路: (a) 振り分けで落ちる、(b) 重複する、(c) `if:` や複数行の `run: |`（casefold）が崩れる、(d) コメントアウトされた形になる、
   (e) checkout の `fetch-depth: 0` が無いジョブに base の要るステップが入る、(f) 新しいジョブが YAML として読めず GitHub が 1 つも走らせない。
   守り方: 分割前後の YAML を読んでステップの (name, if, run) の多重集合を比べる・行の多重集合を比べる・全ジョブを `fetch-depth: 0` で取る。
   GitHub が実際に全ジョブを走らせたことは PR の `gh pr checks` で見る。
2. **収録漏れの歯止めが緑のまま、効いたまま。** `test-check-all.py`（`scan_ci_runs`・`full_runs`）と、`plugins.yml` を指す
   `mutation-claim`（`check-mutation-claims.py`）が緑。経路: `run:` の行の形・インデントが変わる。
3. **PR の CI の所要時間**（最初のジョブの開始から最後のジョブの終了まで）が分割前の約 32 分より大きく短い——実測を PR に貼る。
4. `python3 scripts/check-all.py` が緑で、PR 側の CI も全部緑。

検証で証明できるもの: 1〜4 すべて（3 と 1 の「実際に走った」は PR の CI で見る）。

未証明: なし。

生成物: なし（`plugins.yml` は手で書く定義で、生成物ではない。振り分けに使ったスクリプトは scratchpad の作業用で、リポジトリに入れない）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 実装: 済み・コミット済み（このファイルを含むコミット）。分割前後の YAML を読んで比べた——ステップ 62 → 62 で (name, if, run) の多重集合が一致、
  分割前の行で分割後に無いものは無し。`python3 scripts/check-all.py` 69/69 緑
- draft PR: #930（所要時間の実測を CI で取るため、関門の前に draft で出した）
- 手順 4 の割り目: `AskUserQuestion` で訊いた → **ここで割る**（2026-11-10）。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 929`、手順 5 から
- 関門: 1 パス目を通した（2026-11-10。再開した周で、Verifier → `/code-review` の順に渡した）。
  1 パス目の指摘対応の起点: `769803e`（Verifier に渡した時点の HEAD。成果物はコミット済み）
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）1 パス目: **反証 0 件**。不変条件 1（62 → 62 の多重集合の一致）・2（`test-check-all.py` 緑・`check-mutation-claims.py` 44/44）を走らせて確かめた。3・4 は報告の時点で CI が未完
  - `/code-review`（high）1 パス目: **正しさのバグ 0 件・指摘 7 件**（下の採否の表）。不変条件 1〜4 を当てて満たすと報告
  - 直す線: 1 パス目の指摘を受けて `AskUserQuestion` で訊いた → 300 秒で答えが無く **既定のまま**
  - 指摘対応: 「直す」の行が 0 件なので、成果物の差分は 0 行（`git diff 769803e -- ':(top)' ':(top,exclude)docs/plans/issue-929.md'` が空、`git status --porcelain` は計画ファイルだけ）
  - **2 パス目: 該当なし**（1 パス目の指摘対応の差分が 0 行。起点 `769803e`）
  - **狭いパス: 該当なし**
- CI（PR #930・run 42732175841・HEAD `769803e`）: 7 ジョブすべて成功。最初のジョブの開始 00:57:10Z → 最後のジョブの終了 01:04:06Z で **6 分 56 秒**（分割前の run 42612174778 は 31 分 45 秒）。いちばん重いジョブは `spec-loop-autopilot-loop` の 6 分 55 秒
- 交絡を潰した手順: 実験なし（3 の所要時間は分割前後の単純な比較。ランナーの混み具合で揺れるので、1 回の値で「何倍速い」とは書かず、分割前の値と並べるだけにする）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `matrix` で書くか | 採らない | `run:` の行からスクリプト名が消え、`test-check-all.py` が「CI に無い」と赤にする |
| 全ジョブで `fetch-depth: 0` | 採る | どのステップがどのジョブに移っても見える履歴を分割前と同じにする。取る時間は 3 秒（実測） |
| ジョブ名 `check` が変わると必須チェックが外れるか | 心配ない | `main` に保護も ruleset も無い（`gh api` で確認）。`check` の名前は残してある |

### 1 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| ジョブ単位の `if:`・`needs:` を見る歯止めが無い（`if: false` を足しても `test-check-all.py --part registry` は緑、`merge-pr.py` は SKIPPED を通す） | 示せる（レビューが複製で変異を当てた） | 無し（いまの定義はすべてのジョブが無条件に走る。将来の退行を防ぐ歯止めの話） | 残課題 |
| `concurrency` が無く、古い run が 7 ジョブ分走り続ける | 示せる（run 42732150720 と 42732175841 が並んで走った） | 無し（分割前から無い。3 の所要時間は満たす） | 残課題 |
| `spec-loop` と `spec-loop-generate` のコメントが中身と入れ替わっている | 示せる（`plugins.yml` のコメントとステップ） | 無し | 残課題 |
| `dev-loop`・`check` のジョブのコメントが中身を覆っていない | 示せる | 無し | 残課題 |
| `check-mutation-claims.py` の上の「1 本だけ重い」が実測と違う（25 秒） | 示せる（run 42612174778） | 無し | 残課題 |
| 計画の複製の数「1 箇所」が数え違い（ジョブごとのコメント 7 つと計画の表） | 示せる | 無し | 残課題 |
| `CLAUDE.md` の「CI の 1 往復（約 13 分）」が実測と違う | 示せる | 無し（`触らない:` に置いた別件） | 残課題 |

- この周の起票: 0 件（残課題 7 件は PR コメントに置き、起票の承認は得ていない）
