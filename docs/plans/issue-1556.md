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
(2) テストの中の「守る」の行数と変異の数の照合は、どのシャードでも全件で見る（両テストの docstring）——規範（数を揃える）を変えずに済む。
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

関門: まだ。

交絡を潰した手順: （実機確認のあとに書く）

```dev-loop-gates
周の base: 4d9370bf432634441164d1731d3ec9e149aa959b
```

## 既知の限界・決着済みの論点

- 穴 1 の記録: 推奨 A で決めた（上の「仕様の穴」）。**決着の理由が誤っていると判断したなら、それは新しい反証である。**
- `--shard` を持たない遅いテストは間引かない（範囲の外。決めた値 A の一部）。
- 間引いた後の全体の時間は受入基準にしない（未証明。上）。

## 手順 8
