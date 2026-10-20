# Issue #272: check-signoff・scaffold の回帰テストを素通りする変異 4 本に試料を足す

元の周: #262（PR #269 の狭いパスの指摘 N1〜N4）。`/dev-loop 272` で起動（2026-10-20）。

## 変更範囲

触る:

- `scripts/test-check-signoff.py` — 試料 3 件（N1〜N3）・変異 3 件・docstring の「見るもの」
- `scripts/test-scaffold.py` — 試料 1 件（N4）・変異 1 件
- `docs/plans/issue-272.md` — この計画

触らない:

- `plugins/spec-loop/scripts/check-signoff.py`・`scaffold.py` — 本体の挙動は正しい（Issue の前提。下の受入基準 A で確かめる）。
  **本体を触らないので、プラグインの版は上げない**（`check-version-bump.py` は `plugins/` の中身を見る）
- 他の歯止め・CI 定義（どちらのテストも既に `check-all.py` と `plugins.yml` から呼ばれている）

**周の大きさ（同じことを述べている箇所）**: 変異と試料は各テストの表の 1 行ずつで、写しは無い。
docstring の「見るもの」が試料の性質を列挙しているので、**その 1 箇所**（signoff 側）。分ける理由は無い。

## 乗るデプロイ経路

**反映経路なし**——`scripts/` のテストは公開サイトにもプラグインにも載らない（`docs/plans/` は mkdocs の `docs/` 配下だが、
`mkdocs.yml` の nav に無く、既存の計画ファイルと同じ扱い）。マージと CI 完了の確認は行う。

## verify の受入基準

不変条件と、それを破りうる経路:

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| A | 足した試料が**本体のままで**期待どおり（陽性対照） | 試料の組み方の誤り（ステップ・期待の文言） | 素の `test-*.py` が緑 |
| B | 足した変異 4 本が、**名指しした新しい試料で**赤になる | 変異の文字列が本体に 1 回現れない／殺す試料の名前違い | ハーネスが「壊す箇所が 1 回現れる」と「killer が期待どおりでない」を見る |
| C | **新しい試料が要る**こと——変異 4 本は、足す前の試料ではどれも殺せない（Issue の主張） | 既存の試料が既に殺していた（なら試料は冗長） | 変異を当てた本体で**既存の全試料**を走らせ、全部期待どおりのままであることを見る（signoff: `run_all`、scaffold: 全ケース） |
| D | N1 の試料が**本当に rename（R100）**を作っている | git の rename 検出が効かない設定（`diff.renames=false` など）だと `D`+`A` に分かれ、`A vis.md` が両方の形で数えられて変異を判別しない | 期待の文言に `R100\t…/.x\t…/vis.md` を入れ、rename でなければ**試料が赤**になるようにする |
| E | N4 の試料が「版の名前が決まりに反する（1）」と「版が 1 つも無い（2）」を分ける | `v02` だけの構成で別の理由で 1／2 が出る | 期待の終了コード 1 と、`find_versions` の誤りの文言を期待にする。既存の「版に分けていない」（2）と並べる |
| F | 歯止めが全部緑 | 他の歯止め（件数の写し・指し先・plan-scope 等） | `python3 scripts/check-all.py`、push 後に `gh pr checks` |

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目 = 4 つの受け渡し。

**この環境では証明できないもの**: 無し。

**生成物**: **生成物なし**——触るのはテストと計画ファイルだけで、図の書き出し（`exports.json`）・`skill-metrics.py` の生成ブロック
（`SKILL.md` を触らない）・spec-loop の生成物（本体を触らない）のどれにも当たらない。

## 未解決の判断・確認待ち

無し。

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/272-signoff-scaffold-mutants`／worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-272`／起点 `50b1d1b`／
  base: `origin/main`（`refs/remotes/origin/HEAD`）→ `50b1d1be2ad0efd20726333e712a4b91dcfccc0a`
- 実装: 済み（`test-check-signoff.py` 試料 41・変異 29、`test-scaffold.py` 試料 113・変異 68 で緑）
- 歯止め: `check-all.py` 43/43 緑（失敗 0・飛ばし 0。コミット `test(spec-loop): …` の時点）。PR は未作成
- **割り目 1（手順 4 の完了時）**: 2026-10-20 に `AskUserQuestion` で提案 → **「ここで割る」が選ばれた**
- 関門（2026-10-20 に再開。base `50b1d1b`）:
  - **Verifier 1 パス目**（`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**。A〜E を一致と判定（変異を外に写して当てた——
    C は 4 本とも赤は名指しした killer 1 件だけ、D は `run_all` に渡す env に `GIT_CONFIG_COUNT/KEY/VALUE` で
    `diff.renames=false` を入れると N1 だけ赤・既定で緑）。F は `check-all.py` 43/43。`gh pr checks` は PR 未作成で未実行。
    軽微な記述の不正確 1 件（下の採否の表の R1 と同じ）
  - **`/code-review` 1 パス目**: **指摘 6 件**——採否は下の表。**直す 0 件**
  - **1 パス目の指摘対応で成果物の差分は増えていない**（直す行 0 件）。計画ファイルの記録の訂正だけ（下の「既知の限界」と D の書き方）
- 反証・差し戻し: なし（手順 4 への差し戻し 0 回）
- 交絡を潰した手順（著者の実験。scratchpad の使い捨てスクリプト）:
  - **C（新しい試料が要る）**: 新しい変異 4 本を 1 本ずつ本体に当て、**足す前からあった試料を全部**走らせた——
    **どれも期待どおりのまま**（既存では殺せない）で、殺したのは名指しした新しい試料だけ。
    出力は Issue の表のとおり（N1 1→0・N2 0→1・N3 0→1・N4 1→2）。陽性対照として、本体のままでは全試料が期待どおり。
  - **D（rename を作っている）**: **`run_all` に渡す env**（`sandbox_env` の戻り値）に `GIT_CONFIG_*` で `diff.renames=false` を
    足すと N1 の試料は**赤**（出力が `A vis.md` だけになる）、既定では緑（`R100` が出る）。陽性・陰性の両側を見た。
    **親の環境変数に置いても届かない**——`sandbox_env` が `GIT_*` を落とす（`/code-review` 1 パス目の R2。Verifier が上の形で再現した）

## 既知の限界・決着済みの論点

- **N1 の試料は git の rename 検出の既定（有効）に乗っている**——rename 検出が効かなければ試料が赤になる（黙って緑にはならない。受入基準 D）。
  **システム設定・利用者の設定・親の `GIT_*` は届かない**（`sandbox_env` が `GIT_CONFIG_NOSYSTEM=1`・`GIT_CONFIG_GLOBAL` の差し替え・
  `GIT_*` の除去をする。`scripts/test-check-signoff.py:257`）。残る依存は git 本体の既定だけ。
  （1 パス目までここに「システム設定は差し替えない」と書いていたのは誤り——R1）

### 1 パス目の指摘の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | 計画の「既知の限界」が `/etc/gitconfig` を差し替えないと書くが、`GIT_CONFIG_NOSYSTEM=1` を立てている（Verifier も同旨） | 示せる（`test-check-signoff.py:257-259`）——**ただし計画ファイル（周の記録）であって成果物ではない** | 無し | 残課題（記録は上で訂正済み） |
| R2 | 計画の D の実験は「`GIT_CONFIG_*` で」と書くが、親の環境変数は `sandbox_env` が落とすので届かない | 書き方の不正確は示せる。**実験そのものは Verifier が `run_all` の env に入れて再現した**——D は偽ではない | 無し | 残課題（記録は上で訂正済み） |
| R3 | C（既存の試料では殺せない）をハーネスが機械で見ていない——killer が赤になることしか見ない | 示せない（C が偽になった実物は無い。Verifier の当て直しで 4 本とも killer だけ赤） | 無し（C は関門で確かめた） | 残課題 |
| R4 | `test-check-signoff.py:151` の R100 のコメントに `mutation-claim:` の印が無く、機械で当てていない | 示せない（主張は Verifier の D で真） | 無し | 残課題 |
| R5 | `test-check-signoff.py` の docstring が隔離を「`HOME` と `GIT_CONFIG_GLOBAL`」とだけ書き、`GIT_CONFIG_NOSYSTEM`・`GIT_*` の除去を書いていない | 示せる（:26 と :257-259 の食い違い）——**この周の差分の行ではない（既存の記述）** | 無し | 残課題 |
| R6 | `test-scaffold.py` の docstring の「見るもの」に N4 の区別（1 と 2）が足されていない（signoff 側は足した） | 示せる（docstring に該当の行が無い） | 無し | 残課題 |
