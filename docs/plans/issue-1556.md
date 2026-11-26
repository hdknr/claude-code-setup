# Issue #1556: check-all.py の手元の変異を間引き、全部は PR 側の CI に任せる

**不在の周である。** 出所: `/dev-loop:cruise 1565 --absent` の起動（2026-11-26T00:39Z）。cruise の親 Issue #1565 の子の周（サブエージェント）。

## 線

台帳の確かめた線（出所: 利用者の確認（起動時・2026-11-26T00:39:07Z、配布を見せて確かめた））:

- 直す線 = 既定
- 仕様の穴 = 推奨で決めて起票
- マージ = 関門を通ればマージ（マージは親がする。子は PR 側の CI まで）
- 周の途中の課題 = 台帳に足して直す
- マージ前の判断 = 推奨で決めて起票（後退・未達を含む）
- 実機確認の線は無い

## 仕様の穴（不在の線で推奨により決めた）

Issue の本文は「決めてから始めること（利用者の判断）」を挙げ、受入基準は「上を決めたあとに書く」としている。周の全体が穴である。
線 `仕様の穴 = 推奨で決めて起票` で推奨により決め、確認の Issue を立てる（番号は下の「確認の Issue」）。

穴 1（1 つの判断として扱う）: **手元で変異を間引いてよいか、間引くならどう間引き、全部をどこで回すか。**

| 選択肢 | 中身 |
| --- | --- |
| A（推奨） | `check-all.py` が、変異の観測を `--shard K/N` で分けられる回帰テスト（いまは `test-autopilot-loop.py`・`test-line-effects.py`）に、既定で `--shard 1/4` を渡す（変異の 1/4 だけを観測する）。`--all-mutants` で間引かずに全部回す。全部は PR 側の CI（既に `--shard 1/4`〜`4/4` の 4 ジョブで全部を回している）が見る。`--shard` を持たないほかの遅いテストは、この周では間引かない（それぞれ `--shard` を足す周で同じ口に載る） |
| B | 環境変数で全テストに「変異を N 個だけ」を渡し、各テストに読む口を足す（全部の遅いテストに一度に効くが、テストごとに変異の持ち方が違い、6 本以上を同時に書き換える） |
| C | 間引かない（Issue を閉じる） |

**推した理由（A）**: (1) 間引きの単位が、既に CI で全部を覆っていると `test-check-all.py` の `full_runs` が確かめているシャードそのもの——「手元で落とした分を CI が必ず回す」が既存の検査で保証される。
(2) 変異の観測のほかの検査（`test-autopilot-loop.py` の「守る」の行数と変異の数の照合、`test-line-effects.py` の壊す箇所が本体に 1 回現れることなど）は、どのシャードでも全件で見る（各テストの docstring）——規範（数を揃える）を変えずに済む（1 パス目の /code-review の指摘で、「両テストが数の照合を持つ」から直した）。
(3) `check-mutation-claims.py` の主張の red のコマンドは `check-all.py` を通らずにテストを直に起こすので、間引きの影響を受けない。
(4) 引数で渡すので、キャッシュ（#1151）のキーに `--shard 1/4` が入り、間引いた回の緑が `--all-mutants` の回に当たらない。
(5) B は効果が大きいが、規範の変更を 6 本以上のテストに同時に入れ、1 周の差分と「同じことを述べる箇所」が大きくなる。A は口を 1 つ置き、ほかのテストは `--shard` を足す周で載せられる。

決めた値: A。決めた値は「既知の限界・決着済みの論点」に穴の記録として書き、2 つの関門に渡す。**受入基準は、決めた値を Issue が求めた範囲（手元で間引く・全部は CI）に写したもの**で、関門の途中で足さない。

### 確認の Issue

- #1566（要確認: check-all.py で 2 本のテストだけ手元では 1/4 に間引くか）。閉じない（閉じるのは利用者）。PR からは `Refs` で指す。

## 変更範囲

触る:

- `scripts/check-all.py` — 間引きの口（`THINNED`・`THIN_SHARD`・`--all-mutants`・出力の行）と docstring
- `scripts/test-check-all.py` — 間引きの契約・変異・収録の確かめ
- `scripts/test-autopilot-loop.py` — docstring の「全件（check-all.py と手元）」の記述だけ
- `scripts/test-line-effects.py` — docstring の使い方の記述だけ
- `CLAUDE.md` — `check-all.py`・2 本のテストの説明と「歯止めは毎回全部回す」の節に間引きを書く
- `docs/plans/issue-1556.md` — この計画

触らない:

- `plugins/` の下（版は上げない——下の「版」）
- `.github/workflows/`（CI は既に 2 本を全シャードで回している）
- `--shard` を持たないほかの遅いテスト（`test-outer-loop.py`・`test-commit-gate.py`・`test-ledger.py`・`test-build-proposal.py`・`test-check-unattended-env.py`）
- `scripts/check-mutation-claims.py`

依存の追加・更新: なし

## 版

上げない——`plugins/` の下を 1 行も触らない（`check-version-bump.py` が見るのはプラグインの中身。CLAUDE.md の「プラグインの更新」）。PR の前に `check-version-bump.py origin/main` で確かめる。

## デプロイ経路

main へのマージで GitHub Pages の再ビルド（`CLAUDE.md` は mkdocs の外。`docs/plans/` は mkdocs のソースの下だが nav の外）。プラグインの配布は起きない（`plugins/` を触らない）。

## 同じことを述べる箇所の数

「`check-all.py` は全部回す」を述べる箇所: `check-all.py` の docstring（冒頭・守らないものの表）、`CLAUDE.md` の `check-all.py` の項・「歯止めは毎回全部回す」の節、`test-autopilot-loop.py` の docstring 1 行、`test-line-effects.py` の docstring（使い方）。**6 箇所**。
分けない理由: 間引きの口と、それを説明する文書が食い違うと「全部回した」と誤読されるので、同じ周で揃える。dev-loop の `SKILL.md` は「対象リポジトリの全部回す 1 本」を一般に述べるだけで、このリポジトリの間引きを述べないので触らない。

## 受入基準

不変条件 × 経路。経路（`check-all.py` の入口）: (a) 既定の起動、(b) `--all-mutants`、(c) `--guards-only`、(d) `--no-cache`、(e) `--jobs N`（1 と 2 以上）、(f) キャッシュの有無（git のリポジトリか）。呼ぶ者: 人・dev-loop の周（run-serial 越し）・cruise の子。CI は `check-all.py` を呼ばない（各スクリプトを直に呼ぶ）。`check-mutation-claims.py` は主張の red のコマンドを直に起こす。

| # | 不変条件 | 経路 | 証明手段 |
| --- | --- | --- | --- |
| 1 | 既定の起動で、`THINNED` の各テストに `--shard 1/4` が渡り、ほかの回帰テストの引数は今までどおり（`NESTED` は `--jobs` だけ、ほかは無し） | (a)(e) | `test-check-all.py` の契約（実物の `TESTS` のまま起動の引数を記録） |
| 2 | `--all-mutants` では `THINNED` にも `--shard` を渡さない（全部） | (b)(e) | 同上 |
| 3 | 間引いた回は、間引いたテストと全部を回す口（`--all-mutants`・PR 側の CI）を出力に出す。間引かない回（`--all-mutants`・`--guards-only`）は出さない | (a)(b)(c) | 同上（出力の行） |
| 4 | 間引いた回の緑の記録は `--all-mutants` の回に当たらない（キーが違う）。`--all-mutants` の回も自分の記録には当たる | (a)(b)(d)(f) | `test-check-all.py` のキャッシュの契約（偽のリポジトリ） |
| 5 | PR 側の CI は `THINNED` の各テストの変異を全部回す——`THINNED` ⊆ `TESTS`、各テストが `--shard` を受け、CI の行が全シャードを覆う（`full_runs` が全部に数える） | CI | `test-check-all.py --part registry`（実物の `THINNED` と `.github/workflows/`） |
| 6 | 実物の 2 本が `--shard 1/4` で緑になり、引数なし（全件）より観測する変異が少ない | 実機 | 2 本を run-serial 越しに `--shard 1/4` と引数なしで回し、出力の変異の件数と壁時計を見る |
| 7 | 規範の記述が間引きと食い違わない——`check-all.py` の docstring・`CLAUDE.md`・2 本のテストの docstring が、間引くこと・全部を回す口・砦（PR 側の CI）・`check-mutation-claims.py` と変異の数の照合が影響を受けない理由を書き、「`check-all.py` が全件を回す」と読める記述を残さない | 文書 | 関門が読んで当てる（grep で「全件」「全部」を名指しで引く） |
| 8 | 間引きの契約が判別する——渡さない・`--all-mutants` でも間引く・ほかのテストにも渡す・出力の行を黙る・キーから `--shard` を落とす、の変異が赤 | — | `test-check-all.py` の `MUTANTS`（とキャッシュの変異） |
| 9 | 歯止めと回帰テストが全部緑 | — | `python3 scripts/check-all.py`（run-serial 越し。間引いた回と `--all-mutants` の回）と PR 側の CI |

必須の掛け算: 受入基準を Verifier と `/code-review` の両方に渡す × 1・2 パス = 4 つの受け渡し（2 パス目が該当なしなら初回の 2 つ）。

この環境では証明できないもの（未証明）: 間引いた後の `check-all.py` 全体の時間の短縮（他のセッションの負荷と重なり、1 回の計測では比べられない——Issue の「守らないもの」と同じ）。受入基準ではないので、計測した値を参考として PR コメントに書くだけにする。
間引いた手元の緑が PR 側の CI の赤を見逃す割合は測らない（Issue の「守らないもの」）。

生成物: なし（`SKILL.md` を触らないので `skill-metrics.py` の生成ブロックは動かない。図も触らない）。
プロパティテスト: なし（入力は引数の組の有限個で、契約で全部を列挙できる）。
差分テスト: なし（この周は振る舞いを変える周。変えない部分——間引かないテストの引数——は受入基準 1 で全件を列挙して見る）。
仕様の振る舞い: このリポジトリに spec-loop の正本は無い（PR の前に `check-spec-writeback.py` で確かめる）。

## 未解決の判断・確認待ち

- 穴 1 の確認（確認の Issue）。

## 関門の進捗（再開点）

周の在り処:

- ブランチ: `issue/1556-thin-mutations`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1556`
- 起点コミット: `4d9370bf`
- base: 参照 `origin/main`、SHA `4d9370bf432634441164d1731d3ec9e149aa959b`

割り目（手順 4）: 割らない（cruise の周）。

関門（1 パス目）:

- 1 パス目の起点（指摘対応の 0 行判定の起点。先に当てた関門に渡した時点の HEAD）: `a719a74842596364108bb494abcffe4844765622`（計画ファイルだけのコミット。成果物は fc476391 と同じ）
- Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet。終点 `a719a748`）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/4c7034dc-d804-4ffa-8433-2d789038064f/scratchpad/gate-1556-verifier-1-20261126T005501Z.md`。**反証 0 件**。受入基準 1〜5・7・8 は一致。6 と 9 は順番待ちが 33 分明けずに当てられなかった（6 は `select_shard` で件数だけ静的に確かめた——13/50・17/67）。6・9 は著者の実測と PR 側の CI で見る（下の「交絡を潰した手順」）
- /code-review 1 パス目（high。終点 `9c3dff92`）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/4c7034dc-d804-4ffa-8433-2d789038064f/scratchpad/gate-1556-code-review-1-20261126T005501Z.md`。**指摘 5 件**（全部 nit）。採否は下の表——直す 3 件・残課題 2 件。4 への差し戻し: あり（直す 3 件）
- 1 パス目の指摘対応: 直す 3 件を直した（下の採否の表。コミット `62bd5695`）。2 パス目を回す（差分は 0 行でない）。
- 割り目（2 パス目の前）: 割らない（cruise の周）。残っているもの: 手順 5 の当て直し（Verifier 2 パス目）と /code-review 2 パス目の両方。
- 2 パス目の指摘対応の起点（狭いパスの起点。2 パス目の関門に渡す時点の HEAD）: `62bd5695e1d3fdcbb123c2f0ff984bde6056b73c`
- Verifier 2 パス目（sonnet。終点 `62bd5695`）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/4c7034dc-d804-4ffa-8433-2d789038064f/scratchpad/gate-1556-verifier-2-20261126T020549Z.md`。**反証 0 件**
- /code-review 2 パス目（high。終点 `62bd5695`）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/4c7034dc-d804-4ffa-8433-2d789038064f/scratchpad/gate-1556-code-review-2-20261126T020549Z.md`。**指摘 5 件**（全部 nit）。直す 3 件（CR2-1〜3）・残課題 1 件（CR2-4）・証明の記録 1 件（CR2-5）
- 外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い。`external-reviews.py` が 3）
- PR: #1568
- マージの直前の取り込み（親の依頼 2026-11-26T03:33:14Z）: 取り込む前の先端 `b4fb89e9`、取り込んだ main `14888e7b`（#1567）、merge `3a4cbca6`。衝突なし。
  正味の差分（`git diff origin/main`）はこの周の 6 ファイルだけ。版は上げない（`plugins/` を触らない）。
  名前のぶつかり: main が足した名前（scaffold の `excluded`・spec-ir.md/tree.md の節）とこの周の名前（`THINNED`・`THIN_SHARD`・`--all-mutants`・`test_args_for`）は重ならない（`git diff 4d9370bf 14888e7b` に後者は 0 件、この周の差分に `excluded` は 0 件）。
  CLAUDE.md の決まり（#831）どおり `check-plugin-versions.py`（0）と `skill-metrics.py --check`（0）だけを回した。周の base は取り込み後も `4d9370bf`（main の祖先のまま）。
- 2 パス目の指摘対応: コミット `602cedbf`（起点 `62bd5695` → 終点 `602cedbfe141457a4b5286e35dc1c3114e38c8ad`）
- 狭いパス（sonnet）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/4c7034dc-d804-4ffa-8433-2d789038064f/scratchpad/gate-1556-narrow-1-20261126T023916Z.md`。**反証 1 件**（N1。下の採否の表——人間が決める。推奨は PR コメント）。CR2-1〜3 の直しは一致。素通りした変異 3 本（下の N1）

交絡を潰した手順（受入基準 6 の実機確認。run-serial の枠の中で `/usr/bin/time -p`。2026-11-26）:

| テスト | 引数 | 終了 | 観測した変異 | 壁時計 |
| --- | --- | --- | --- | --- |
| test-autopilot-loop.py | `--shard 1/4` | 0 | 13 件（全 50 件のうち。出力の「観測した変異 13 件」と「変異を殺せる」の行 13） | 87.6 秒 |
| test-autopilot-loop.py | なし | 0 | 50 件（「変異を殺せる」の行 50） | 157.6 秒 |
| test-line-effects.py | `--shard 1/4` | 0 | 17 件（全 67 件のうち） | 122.3 秒 |
| test-line-effects.py | なし | 0 | 67 件 | 443.3 秒 |

- 陽性対照: 同じ観測点（出力の変異の件数）が、引数なしでは全件を数える——件数を出さない形・全件を出す形では差が出ない。
- 主張が偽でも同じ出力が出ないか: `--shard` が無視されれば件数は全件になる（引数なしの行と同じ）。shard の回は件数が少ないので、引数が届いている。
- 観測窓: 各 1 回。壁時計は枠を取ってからの時間（`/usr/bin/time` は枠の中のコマンドだけを測る）で、同じ時間帯に別の周（#1562）の検査が枠の外で走っていた可能性は除いていない——壁時計は受入基準でなく参考。
- `check-all.py`（既定・間引いた回。狭いパスの終点 `602cedbf` の木）: **105/105 本を回した（失敗 0 / 飛ばし 0）**。集計に `変異を間引いた: test-line-effects.py, test-autopilot-loop.py …` の行。全体 1271.4 秒（参考）。
- `check-all.py --all-mutants`（`602cedbf` の木）: 18/105 本を回し（87 本は CACHED——間引かないテストのキーは既定の回と同じ）、`test-line-effects.py`（全件。1409.4 秒）と `test-autopilot-loop.py`（全件。368.8 秒）は OK、間引いた行は出なかった。
  **落ちたのは `test-intake-code.py` の「このリポジトリの作業ツリーを変えていない」の 1 本**——回している間（12:00:17 に枠を取った）に、著者が計画ファイルを 12:00:41 にコミットした（`874193c3`）ので HEAD が動いた。
  交絡の確かめ: 作業ツリーを触らずに順番待ち越しで回し直して緑（「試料 37 件・変異 46 件」、終了 0）。不安定なテストではない（原因は著者の同時のコミット）。
- PR 側の CI（#1568）: 全部 pass（`deploy` は PR では skipping）。
- `check-all.py`（既定・間引いた回。`9c3dff92` より前の木）: 105/105 本を回し、落ちたのは `check-plan-counts.py`（件数の行が無い）の 1 本だけ。集計に `変異を間引いた: test-line-effects.py, test-autopilot-loop.py …` の行が出た。件数の行は `9c3dff92` で足した。全体 1334.4 秒（別の周と重なっていたので参考）。

```dev-loop-gates
周の base: 4d9370bf432634441164d1731d3ec9e149aa959b
関門: Verifier 1 a719a74842596364108bb494abcffe4844765622 反証=0
関門: /code-review 1 9c3dff924e41ebcedb43c38a97e033377627a890 指摘=5
関門: Verifier 2 62bd5695e1d3fdcbb123c2f0ff984bde6056b73c 反証=0
関門: /code-review 2 62bd5695e1d3fdcbb123c2f0ff984bde6056b73c 指摘=5
関門: 狭いパス 62bd5695e1d3fdcbb123c2f0ff984bde6056b73c 602cedbfe141457a4b5286e35dc1c3114e38c8ad 反証=1
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
受入基準: 8 満たす
受入基準: 9 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

- 穴 1 の記録: 推奨 A で決めた（上の「仕様の穴」）。**決着の理由が誤っていると判断したなら、それは新しい反証である。**
- `--shard` を持たない遅いテストは間引かない（範囲の外。決めた値 A の一部）。
- 間引いた後の全体の時間は受入基準にしない（未証明。上）。

### 関門の指摘の採否（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | Verifier 1 パス目: 反証 0 件（受入基準 6・9 は順番待ちで当てられなかった） | — | — | 指摘なし（6 は著者の実測、9 は著者の check-all と PR 側の CI） |
| CR1-1 | `check-all.py` の docstring（と計画の推した理由 (2)）が「守る」の行数と変異の数の照合を両テストが持つと言うが、`test-line-effects.py` には無い | 示せる——`grep -n 守る scripts/test-line-effects.py` が 0 件 | 7（変わらない理由が事実でない） | 直す（docstring を、テストごとに全件で見る検査を書き分ける形に直した。CLAUDE.md の括弧も「どのシャードでも全件で見る検査」に） |
| CR1-2 | 契約が集計の行の「PR 側の CI」を見ていない——外の写しで消しても `--part contract` が緑 | 示せる——レビューの外の写しで rc=0 | 3・8（全部を回す口の片方を黙る変異が赤にならない） | 直す（表明に「全部は PR 側の CI が全シャードで回す」を足し、それを消す変異を `MUTANTS` に足した。直した後に `--mutant` で「契約が捕まえる」——直す前はレビューの実測で緑） |
| CR1-3 | 収録の確かめは `--shard` を受けるかを字句でしか見ない——`--shard` を持たない `test-check-all.py` を `THINNED` に足しても registry が緑 | 示せる——レビューの外の写しで rc=0 | 7（check-all の docstring と表明の名前が「受ける」まで見ると言う） | 直す（記述を弱めた——docstring・表明の名前・コメントを「ソースに `--shard` の字句がある。受けるかは字句でしか見ない」に。検査は強めない） |
| CR1-4 | 契約 9 のコメント「宣言の側は下の収録の確かめが見る」が事実でない（写しと `THINNED` の食い違いを捕まえるのは契約の別の表明） | 示せる（コメントの読み） | 無し（テストのコメント。受入基準 7 の対象は check-all の docstring・CLAUDE.md・2 本のテストの docstring） | 残課題 |
| CR1-5 | `THINNED` と `NESTED` の重なりを見ていない（重なると `--shard 1/4 --jobs N` になり 2 で落ちる） | 示せない（いま重なりは空） | 無し | 残課題 |
| V2 | Verifier 2 パス目: 反証 0 件（6 は `test-autopilot-loop.py --shard 1/4` の緑まで。ほかは過負荷で当てられなかった） | — | — | 指摘なし |
| CR2-1 | CR1-3 の直し残し——`test-check-all.py` のモジュールの docstring と `check-all.py` の `THINNED` の上のコメントが、まだ収録の確かめが「`--shard` を受ける」まで見ると書く | 示せる（両方の行の読み。字句しか見ないことは 1 パス目の実測） | 7 | 直す（字句しか見ないと書き直した） |
| CR2-2 | 「受けないテストを入れると引数の誤り（2）で落ちる」は、引数を読まないテストでは偽——黙って全件を回し、集計は間引いたと言う | 示せる——`test-check-bold-flanking.py --shard 1/4` が rc=0 で全件 | 7 | 直す（docstring と収録の確かめのコメントを、引数を弾くテストと読まないテストに書き分けた） |
| CR2-3 | 契約 13 が `--jobs 1` でしか間引きを見ない——`jobs == 1` のときだけ間引く変異が `--part contract` を通る（`--part cache` だけが間接に捕まえる） | 示せる——レビューの外の写しで contract rc=0 | 1・2（経路 (e) の `--jobs` 2 以上を契約で証明すると書いている） | 直す（契約 13 の 2 つの表明を `--jobs 1` と `4` の両方で見る形にした。陽性対照: 同じ変異を外の写しに当てて `--part contract` が rc=1——直す前はレビューの実測で rc=0） |
| CR2-4 | cruise の終える前の「全部の歯止めを 1 回流す」（cruise の `SKILL.md`・`docs/plugins/dev-loop-cruise.md`）が素の `check-all.py` を名指しており、いまは変異を間引く | 示せない（失敗の実物は無い——main への push の CI が全シャードを回す。記述が事実より強いだけ） | 無し（`plugins/` と公開ページは触らない範囲） | 残課題（cruise の振り分けでは記録だけ） |
| N1 | 狭いパス: 契約 13 は `--jobs` の 1 と 4 しか当てない——`jobs >= 8` のときだけ振る舞いを変える変異 3 本（`jobs < 8` のときだけ間引く・`jobs <= 4` のときだけ間引く・`jobs >= 8` で `--shard 2/4`）が `--part contract` を素通りした（陽性対照: 同じ位置の `jobs != 4` は赤） | 示せない（合成の変異の上だけ。いまの本体に `jobs` で分かれる間引きは無い） | 無し（受入基準 1・2 の「2 以上」は 4 で代表している。いまの本体は満たす） | 人間が決める（推奨: マージする——直さない。振り分けは記録だけ。後退を示さない） |
| CR2-5 | 受入基準 9 の証明（間引いた回と `--all-mutants` の回の `check-all.py`）が、直した後の木で記録されていない | 示せる（計画の記録） | 9（証明がまだ） | 直す（成果物は変えない。狭いパスの終点の木で 2 つの回を回し、結果を「交絡を潰した手順」に書く） |

## 手順 8

### 周の途中の課題の振り分け（found-lines.md）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| 契約 9 のコメント「宣言の側は下の収録の確かめが見る」が事実でない（CR1-4） | #1556 /code-review 1 パス目 | 示せる（コメントの読み）が、利用者の結果は変わらない | 記録だけ（3 つのどれにも当たらない——テストのコメントで、利用者が受け取る結果は誤らない） |
| `THINNED` と `NESTED` の重なりを見ない（CR1-5） | #1556 /code-review 1 パス目 | 示せない（いま重なりは空） | 記録だけ |
| cruise の終える前の「全部の歯止め」が素の `check-all.py` を名指す（CR2-4） | #1556 /code-review 2 パス目 | 示せない（失敗の実物は無い。main への push の CI が全シャードを回す） | 記録だけ（後退は失敗の実物で示せない——記述が事実より強いだけ） |
| 契約 13 が `--jobs` の 1 と 4 でしか判別しない（N1） | #1556 狭いパス | 示せない（合成の変異の上だけ） | 記録だけ |

直すの行: 0 件（台帳に足す行・cruise-found の起票は無い）。

- 効いた行: R-02（CR1-1。line-effects に「守る」の照合が無いことを、記述と事実の照合で示した）
- 効いた行: R-04（CR1-2。集計の行から CI の言及を消す変異を外の写しで当て、契約が緑のままと示した）
- 効いた行: R-04（CR1-3。`--shard` を持たないテストを THINNED に足して registry が緑と示した）
- 効いた行: R-02（CR1-4。契約 9 のコメントが事実でない）
- 効いた行: R-02（CR2-1。CR1-3 の直し残し）
- 効いた行: R-04（CR2-2。引数を読まないテストに `--shard` を渡して全件が回ると示した）
- 効いた行: R-01（CR2-3。`--jobs 1` だけの契約が並列でだけ間引かない変異を判別しない）
- 効いた行: R-06（CR2-5。受入基準 9 の証明が記録されていない）
- 効いた行: V-01（N1。契約 13 が `--jobs` の 1 と 4 でしか判別しない）

- この周の起票: 1 件（#1566——仕様の穴を推奨で決めた確認の Issue）
