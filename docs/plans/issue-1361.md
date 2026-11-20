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
- 関門: 未着手
- 交絡を潰した手順: 未着手

## 既知の限界・決着済みの論点

- スレッドのプールにする（プロセスにしない）: 試料はラムダ・クロージャを持ち、spawn のプロセスへは渡せない。仕事の大半は子プロセスの待ちで GIL を放すので、スレッドで足りる。
