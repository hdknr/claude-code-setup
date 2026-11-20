# Issue #1361: test-scaffold.py の試料と変異を並列に当てて CI の spec-loop-generate を縮める

## 変更範囲

触る:

- `scripts/test-scaffold.py` — 試料・変異を作業者のプール（スレッド）で同時に当て、結果は宣言順に `check` する。`--jobs N`（既定と上限 4）・`--pool-size`。dev-loop の指紋の変異はグローバル `DEV_FINGERPRINT` の書き換えをやめる
- `scripts/check-all.py` — `NESTED` に `test-scaffold.py` を足し、docstring・コメントの本数を直す
- `scripts/test-check-all.py` — `nested_tests` に `test-scaffold.py` を足し、コメントの本数を直す
- `CLAUDE.md` — `test-scaffold.py` の説明に `--jobs` を 1 文
- `docs/plans/issue-1361.md` — この計画

触らない:

- `plugins/` の中（本体の `scaffold.py` も含めて変えない。版も上げない）
- `.github/workflows/plugins.yml`（ジョブの分割は範囲の外。既定が並列なので CI のステップは今のまま速くなる）
- spec-loop ジョブ側の遅いテスト（`test-qa-to-pptx.py` ほか）

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

## デプロイ経路

main へのマージ → GitHub Pages の再ビルド。`scripts/` と `CLAUDE.md` だけでプラグインの中身は変えないので、配布は起きない（カタログの版は据え置き）。

## 周の大きさ

同じことを述べている箇所: 入れ子に `--jobs` を渡すテストの一覧と本数が `check-all.py` の `NESTED`・docstring（43・45 行）・コメント（163 行）、`test-check-all.py` の `nested_tests`・コメント（528 行）の 5 箇所。
分けない理由: 一覧に足すことと本数を直すことは同じ 1 つの変更で、分けると片方だけ古くなる（`test-check-all.py` が一覧の食い違いを見る）。

## 受入基準

不変条件 × 経路:

| # | 不変条件 | 経路（入口） | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 既定で並列に回り、CI の該当ステップが 438 秒より明らかに短くなる | CI（`plugins.yml` の spec-loop-generate の素の `python3 scripts/test-scaffold.py`）・手元の素の起動 | PR 側の CI のステップの秒（`gh api …/jobs`）。手元で `--jobs 1` と既定の壁時計を比べる |
| A2 | `--jobs 1` で直列（作業者 1）になる・`--jobs 99` は上限 4 で切る・`--jobs 0` を断る | 引数 | `--pool-size` の出力（テスト自身の `check_pool_size`）・`--jobs 0` の終了コード 2 |
| A3 | 試料・変異の件数と最後の `OK:` の行が今（base）と同じ | 素の起動・`--jobs 1` | base の版と新しい版の最後の行を突き合わせる |
| A4 | 変異が生き残る・試料が期待どおりでない（壊した試料）と、並列でも直列でも赤になり、失敗の行が宣言順に並ぶ | 試料の経路（`CASES`）・4 種の変異（dev-loop の指紋・`check-qa-csv.py`・`check-design-csv.py`・`scaffold.py`） | 一時の写しで本体（`scaffold.py`）か試料を壊して、既定と `--jobs 1` の両方で終了コード 1 と失敗の行を見る（陽性対照は壊さない版の 0） |
| A5 | dev-loop の指紋の変異が、並列でも本物の `spec-fingerprint.py` を使う試料に漏れない（グローバルを書き換えない） | 指紋を照合する試料（`dev_fingerprint` を呼ぶ試料）と dev-loop の変異の同時実行 | コードに `global DEV_FINGERPRINT` の書き換えが無いこと・dev-loop の変異が並列で殺されること・既定の回で全試料が緑 |
| A6 | `check-all.py` から入れ子の `--jobs` が渡る（親の半分。`--jobs 1` なら 1） | `check-all.py` の `NESTED` | `test-check-all.py` の 9) が `test-scaffold.py` を含めて緑 |
| A7 | 時間で判定する試料（トレースの Red テスト・性能テスト）が並列の負荷で不安定にならない | 既定の並列の回 | 手元で既定の回を複数回続けて緑・PR 側の CI で緑 |
| A8 | 歯止めが全部緑 | リポジトリの CI | `python3 scripts/check-all.py` と PR 側の CI |

掛け算: 受入基準を Verifier と `/code-review` の両方に、2 パス（1 パス目の指摘対応の差分が 0 行なら 1 パス）。

未証明: A1 の CI の秒は PR 側の CI で測る（手元では測れない——4 vCPU の CI と 10 コアの手元は違う）。A7 は回数を重ねても「不安定でない」の証明にはならない（観測した回数を書く）。

生成物: なし（`test-scaffold.py` は一時ディレクトリにだけ書く。§8.2 の生成ブロック・図の書き出しに触れない）。

## 未解決の判断

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1361-parallel-test-scaffold`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1361`・起点 `b1ad57b4`・base は `origin/main`（refs/remotes/origin/HEAD）を解決した `b1ad57b4bbc582ed7b38d05cc9028f67b32f1038`
- 直す線: 既定（出所: 手順 3 の回答 2026-11-20）
- 実装: `48cf5396`。割り目（手順 4）は利用者の指示「一旦これですすめて」でこのまま続ける（2026-11-20）
- PR: 利用者の指示「待たずに PR 作って」（2026-11-20）で、関門の前に PR を作る——CI の秒（A1）を PR 側で測るため。関門（Verifier・`/code-review`）はこの後に当てる
- 関門:
  - 1 パス目の起点: `25824e0cdb77e1261067960665687218f0ceee93`（2 つの関門に渡した時点の HEAD）
  - Verifier（sonnet）1 パス目: 反証 0 件（A4・A7 の一部は負荷で回せず未確認と報告——A4 は著者が既定と `--jobs 1` の両方で回した。下の手元の実測）
  - `/code-review`（high）1 パス目: 指摘 6 件（nit 5・既存 1）。採否は下の「既知の限界・決着済みの論点」の表——直すは 0 件
  - 2 パス目: 該当なし（1 パス目の指摘対応の差分 0 行——起点からの `git diff` に計画ファイルのほかが出ない）
  - 狭いパス: 該当なし
  - 外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い）
- PR 側の CI（run 44694693593）: 全部緑。`test-scaffold.py` のステップは 07:32:40 → 07:35:35 の **175 秒**（main は 438 秒）、spec-loop-generate のジョブは 11 分 27 秒（main は約 16 分）。律速は spec-loop のジョブ（13 分 18 秒）に移った（A1）
- `check-all.py`: 98/98 本 緑（失敗 0。`test-scaffold.py` は入れ子の `--jobs` で 722.5 秒——Verifier・`/code-review` と同時に走った高負荷の中）（A6・A8）
- 手元の実測（観測窓: 2026-11-20 の 1 回ずつ。load average 45 前後の負荷の中——ほかのセッションが動いていた。秒は交絡するので A1 の根拠にしない）:
  - base（`b1ad57b4` の版）: `OK: 試料 646 件・変異 523 件`・real 374 秒・終了コード 0
  - 新しい版の既定（作業者 4）: `OK: 試料 646 件・変異 523 件`・real 211 秒・終了コード 0
  - `--pool-size`: `--jobs 99` → 4・`--jobs 1` → 1。`--jobs 0` → 終了コード 2
  - `--jobs 1` の回: `OK: 試料 646 件・変異 523 件`・終了コード 0（A3）
  - 壊した写し（試料 1 件の期待を変え、dev-loop の指紋・`check-qa-csv.py`・`check-design-csv.py`・`scaffold.py` の変異を 1 つずつ等価にした）: 既定でも `--jobs 1` でも終了コード 1・`5 件の失敗`・仕込んだ 5 件だけが宣言順（試料 → dev-loop → check-qa-csv → check-design-csv → scaffold）に並ぶ（A4。陽性対照は壊さない版の 0）
  - A7: 既定の並列の回は緑を手元 3 回（著者 1 回・Verifier 1 回（load 約 100）・`check-all.py` の中 1 回）と CI 1 回で観測。不安定でないことの証明ではない
- 交絡を潰した手順: 手元の秒は負荷で交絡するので主張に使わない（A1 は CI の秒で見る）

- この周の起票: 0 件（起票の候補 CR3・CR6 を手順 7 の前に訊いたが回答が無く、承認が無いので起票しない）

## 既知の限界・決着済みの論点

- スレッドのプールにする（プロセスにしない）: 試料はラムダ・クロージャを持ち、spawn のプロセスへは渡せない。仕事の大半は子プロセスの待ちで GIL を放すので、スレッドで足りる。

採否の表（1 パス目。直す線: 既定）:

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1 | 作業者の中で例外が出る・Ctrl-C のとき、`with` が残りの作業を待つので報告が遅れる（直列は最初の例外で止まった） | 示せない（例外は今の試料で起きていない。遅れるだけで、赤になることは変わらない） | 無し | 残課題 |
| CR2 | トレースの Red テストは 1 段 2 秒の待ちに乗るので、並列の負荷で不安定になりうる（A7） | 示せない（観測した 4 回はどれも緑） | 無し（A7 は観測した回数を書く基準） | 残課題 |
| CR3 | CLAUDE.md の「既定と上限 4」は、CPU が 4 未満ならその数（`JOBS_MAX`）——本体の docstring は「CPU が少なければその数」 | 示せる（`JOBS_MAX = max(1, min(4, os.cpu_count() or 1))`） | 無し | 残課題 |
| CR4 | `check_pool_size` は空の `run_jobs([])` を測るだけで、試料・変異が `run_jobs` を通ることは見ない（直列に戻しても緑） | 示せない（今の本体は通している） | 無し | 残課題 |
| CR5 | 計画ファイルの進捗が古い | ——（関門は計画ファイルを検査しない） | 無し | 残課題（進捗は書き足した） |
| CR6 | 最後の `OK:` の変異の件数が dev-loop の指紋の変異 2 件を数えていない（以前から） | 示せる（式に `dev_mutations` が無い） | 無し（A3 は件数が base と同じこと） | 残課題 |
