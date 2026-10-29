# Issue #543 — prepare-worktree.sh: cd の例の引用（' と $ を含むパス）を守る試料が無い（#502 N1）

**不在の周である**——出所: `/dev-loop:cruise 474 --absent` の再開（2026-10-29）。この周は cruise の親から、worktree の絶対パスで作業する
サブエージェントとして委ねられた。**この周では `EnterWorktree` を呼んでいない**（`prepare-worktree.sh` で作り、`cd <worktree> && …` で作業した）。
`AskUserQuestion` は使わない。

使った線（出所: cruise の確かめた線（台帳 `issue-474`）——利用者の確認（起動時・2026-10-27T09:07:27Z）＋利用者の確認（再開時・2026-10-28T07:24:46Z）
＋利用者の確認（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた）。親の委譲文で受け取った）:

- `仕様の穴 = 推奨で決めて起票`
- 直す線: **既定**
- `マージ = 関門を通ればマージ`（**マージは親が行う**——この周は PR・CI・関門・手順 8 の記録まで）
- `周の途中の課題 = 台帳に足して直す`（台帳には親が足す。この周は台帳を書かず、見つけた課題を親への報告に挙げる）
- 加えて、利用者の指示（2026-10-29。親の委譲文で受け取った）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、要確認の Issue（#546・#561 の形）にする

スキルの版: 読み込んだのはキャッシュの 1.63.6（`SKILL.md` 1842 行）。リポジトリの main は 1.63.8。
**この周はプラグインの中を触らない**（テストは `scripts/` にある）ので、版は上げない。

## 変更範囲

触る:

- `scripts/test-worktree-scripts.py` — `'` と `$` を含むパスの試料（`_quoted_cd_example_runs`）・検査 1 件・引用を中身で壊す変異 2 件（`QUOTE_MUTATIONS`。陽性対照つき）・守る 17 の当て先の定数（`QUOTE_NEEDLE`。既存の変異と共有）・
  試料から `'` か `$` を外すと赤になるという docstring の主張の `mutation-claim:` 2 行（`check-mutation-claims.py` が当てる。`red` はテスト全体ではなく `check_quote_mutations` だけを走らせる 1 行）
- `docs/plans/issue-543.md` — この計画

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/prepare-worktree.sh` — 実装は正しい（Issue の「失敗」は試料の弱さ）。冒頭の「何を守るか」の守る 17 も変えない（守るの数は増えない）
- `CLAUDE.md` の変異の数の写し（「変異 20 件」）——#545 の範囲。この周は `MUTATIONS`（23 件）を増やさないので、写しを新たにずらさない
- `observe()` の回数のコメント（「24 回走る（正しい版 1 ＋ 変異 23）」）——この周は `observe()` の回数を変えない
- プラグインの版（3 種類）・description——プラグインの中を触らない

## 複製の数

「cd の例は `'` を `'\''` にした一重引用符で出す」を述べる箇所: スクリプトのコード 1・冒頭の守る 17・コードの直前のコメント・テストの変異の当て先 1（この周で定数 `QUOTE_NEEDLE` に寄せ、既存の変異と `QUOTE_MUTATIONS` が共有する）。
**分けない理由**: コードが正で、ほかはそれを守る側。テストの当て先は 1 箇所に寄せたので、この周で増える写しは無い。

## デプロイ経路

`scripts/` と `docs/plans/` だけ。プラグインの版は上げないので配布は起きない（中身が変わらない）。`docs/plans/` は Pages の再ビルドに乗る。
**マージは親（cruise）が行う——この周はしない。**

## 受入基準（不変条件 × 経路）

不変条件:

- **I1 試料がある**——`scripts/test-worktree-scripts.py` が、`'` と `$` を含むパスで `prepare-worktree.sh` を走らせ、例外の行の `cd '<path>' && …` の例を**そのままシェルに渡して**作った worktree に入れることを見る（正しい版で緑）
- **I2 2 つの変異で赤**——`prepare-worktree.sh` の `PATH_Q` を (A) 一重引用符で囲むだけで `'` を置き換えない形、(B) 二重引用符で囲む形に変えると、テストが**振る舞いの検査で**赤になる
  （当て先が見つからないという字面の検査だけで赤になるのでは足りない——下の「交絡」）
- **I3 試料の弱まりも赤**——試料から `'` か `$` を外すと、どちらかの変異が素通りしたことをテストが言う（テストの中で 2 つの変異を当て、陽性対照として空白と日本語の試料では素通りすることも見る）
- **I4 既存を壊さない**——既存の検査・`MUTATIONS`（23 件）と「守る」の行数の 1 対 1・`observe()` の回数は変わらない。`python3 scripts/check-all.py` が緑。PR 側の CI も緑

経路（不変条件を述べる／破りうる入口）:

| 入口 | I1 | I2 | I3 | I4 |
| --- | --- | --- | --- | --- |
| `prepare-worktree.sh` の `PATH_Q` の行と、例外の行の `echo` | ○ | ○ | | |
| `scripts/test-worktree-scripts.py` の試料（`_quoted_cd_example_runs`）と `cd_example_runs`（正規表現で `cd …` を抜いて `bash -c`） | ○ | ○ | ○ | |
| `scripts/test-worktree-scripts.py` の `QUOTE_MUTATIONS`・`check_quote_mutations`・`QUOTE_NEEDLE` | | ○ | ○ | ○ |
| `scripts/test-worktree-scripts.py` の `MUTATIONS`・1 対 1 の数え・`observe()` | | | | ○ |
| `scripts/check-mutation-claims.py`（このテストを子で回す。打ち切り 300 秒）・`check-all.py`・PR の CI | | | | ○ |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目で 4 つの受け渡し（2 パス目が「該当なし」なら 2 つ）。

### 証明できるもの／できないもの

- I1〜I4 は、偽のリポジトリでの実走・テスト・変異・CI で証明できる。未証明・BLOCKED は無い。
- 著者の実験（scratchpad の複製。`.git` を持ち込まない `rsync --exclude .git`）: 旧いテスト（base `9cea8d1`）と新しいテストを、正しい版・変異 A・変異 B に当てた 6 通り。
  正しい版は両方緑。**変異 A・B では旧いテストも rc=1 だが、落ちたのは「変異を当てる先が 1 箇所ある: cd の例を素のパスで出す」だけ**——
  テストの中の当て先が字面で見つからないという検査で、振る舞いを見ていない（**交絡**。`PATH_Q` の行を正しく書き換えても同じく落ちる）。
  **新しいテストでは、振る舞いの検査「' と $ を含むパスでも、例外の行の cd の例がそのまま通る（#543）」が FAIL に加わる**——これが I2 を判別する出力である。
- I3 の著者の実験: 試料のパスから `'` を外した写し・`$` を外した写しで `check_quote_mutations` を走らせ、それぞれ変異 A・変異 B の「変異を殺せる」だけが FAIL（そのままの写しは全部 ok）。
  同じ主張を `mutation-claim:` 2 行にし、`check-mutation-claims.py` で「確認」（陽性対照 rc=0 → 変異 rc=1）を 2 件とも得た（12 件中 12 確認）。
- `check-all.py`: 1 回目は件数の行が無くて `check-plan-counts.py` だけ落ちた（足して直した）。2 回目は、ほかの周の `check-all.py` 3 本と同時に走り、
  **既存の主張（`test-worktree-scripts.py:384`。テスト全体を走らせる）が 300 秒で打ち切られ、`check-mutation-claims.py` が「当てられなかった」で落ちた**（#449 と同じ形）。
  `check-mutation-claims.py` を単独で回し直すと 12 件すべて確認（262 秒）。この周の追加で増える子プロセスは、正しい版の 1 回と `QUOTE_MUTATIONS` の 4 回（`observe()` は増やしていない）。
- テストの実行時間: 変更前 126 秒・変更後 79 秒（どちらも 1 回。ばらつきは測っていない。`observe()` の回数は変えていない）。

### 生成物

- 該当なし——`SKILL.md` を触らないので `skill-metrics.py` の生成ブロックは動かない。drawio も触らない。

## 未解決の判断・確認待ち

- 無し（仕様の穴は無い。直し方は Issue の受入基準（案）どおり）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/543-cd-quote-samples`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-543`、
  起点コミット `9cea8d1`、base の参照 `origin/main`（refs/remotes/origin/HEAD・取り直した）、base の SHA `9cea8d159c8dbb71491c3d124b2b27f116c7cc9c`
- 手順 4 の割り目: 不在のため訊かず続けた
- 交絡: 上の「証明できるもの」——旧いテストの赤が字面の検査だけだったことを FAIL の行で分けた

## 既知の限界・決着済みの論点

- 試料を `observe()` に入れず、正しい版で 1 回と `QUOTE_MUTATIONS` で当てるだけにした——理由: `MUTATIONS` のどの変異もこの試料でしか殺せないものは無く、`observe()` に入れると 24 回走る（#449 の打ち切りの危険）
- `QUOTE_MUTATIONS` を `MUTATIONS` に入れない——理由: 同じ守る 17 を別の形で壊すもので、「守る」の行数と変異の数の 1 対 1 を崩す
- 試料は `'` と `$` を 1 本のパスに置く——`'` が変異 A を、`$` が変異 B を殺す。どちらかを外すと `check_quote_mutations` が赤になる

## 手順 8（経験の還元）

- この周の起票: 0 件（起票の承認は不在のため訊いていない。台帳に足す候補は台帳を書く親に報告し、この周では起票していない）
