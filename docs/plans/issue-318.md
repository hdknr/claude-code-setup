# Issue #318 — scaffold の OpenAPI でパスの変数の schema・`<Base>Input`・required を見るテストが無い

## 変更範囲

触る:

- `scripts/test-scaffold.py` — 入口の型の整合を全試料の OpenAPI に当てる検査と、P2〜P4 の変異
- `docs/plans/issue-318.md` — この計画

触らない:

- `plugins/spec-loop/scripts/scaffold.py`（生成は正しい。#318 はテストの穴だけ）。だから**プラグインの版も上げない**
  （`scripts/` の変更は配布物ではない）
- `plugins/spec-loop/references/spec-ir.md`（63〜64 行が既に決まりを持つ。R6 の書き足しは #318 の外）
- 互換性（#319）

### 同じことを述べている箇所の数

決まりは `spec-ir.md` 63〜64 行（原本。触らない）と、テストの検査（新しい関数）と、テストの docstring の「見るもの 5」の 3 箇所（触るのは後ろの 2 つ）。
分けない理由: 検査と docstring は同じファイルの中の同じ 1 つの主張。

## 決めたこと

- **入口ごとに、パラメータとボディを合わせると `<Base>Input` がちょうど復元できる**ことを見る関数を足し、
  `run_case` で exit 0 の全試料の OpenAPI に当てる（`path_params_problem` と同じ置き方）。中身:
  1. `<Base>Input` の `required` が全項目（`object_schema` の決まり）
  2. 各パラメータ（path・query）が `required: true` で、`schema` が `<Base>Input` の同名の項目と同じ（P2・P4 のクエリ）
  3. ボディの型の各項目の schema が `<Base>Input` の同名の項目と同じで、`required` が全項目（P4 のボディ）
  4. パラメータの名前とボディの項目の和が `<Base>Input` の項目とちょうど一致し、重ならない（P3）
- `<Base>` は応答の `<Base>Output` の参照から取る（`pascal()` を写さない）。
- 変異を 4 本足す: path の schema を `{"type": "string"}` に固定・`<Base>Input` を残りの項目に縮める・
  `<Base>Body` の `required` を空にする・クエリを必須にしない。殺すのは試料「パスの変数」。

## 乗るデプロイ経路

テストだけ。プラグインは配布し直さない（版を上げない）。`docs/plans/` を含むので、マージで GitHub Pages にデプロイされる。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | path パラメータの schema が入力の項目の schema と違えば、テストが赤になる | enum を落とす（rank）／型を変える | 検査 2。変異「path の schema を固定」 |
| 2 | `<Base>Input` が入力の全項目を持たなければ赤 | パスの変数を持つ POST／GET／Input・パラメータ・ボディから同じ項目が一緒に落ちる | 検査 2・4（パラメータ・ボディとの整合）と、`<Base>Input` の項目を `types.py`（中間表現から別に生成）の同名の型と突き合わせる検査（1 パス目の R1 で足した）。変異「`<Base>Input` を縮める」「OpenAPI から入力の項目を落とす」 |
| 3 | `<Base>Body` の `required` が全項目でない・クエリが必須でなければ赤 | POST の Body／GET・DELETE のクエリ | 検査 3・2。変異 2 本 |
| 4 | 新しい検査が、今の正しい生成のどの試料も断らない（exit 0 の全試料で緑） | 既存の全試料（パスの変数なし・入力が空・全部パスの変数・v2 など） | `python3 scripts/test-scaffold.py` が緑 |
| 5 | 足した変異はどれも名指しした試料で赤になり、壊す箇所が本体にちょうど 1 回現れる | 変異テスト | `MUTATIONS` の既存の仕組み |
| 6 | 歯止めが全部緑 | — | `python3 scripts/check-all.py` |

組み合わせ: 1〜3 × 4（検査を強めても、正しい生成の試料を誤って断らないこと）。

**未証明**: 無し（すべてテストで当てられる）。

生成物: リポジトリに commit した `scaffold/` は無い。`SKILL.md` の測定値は触らない。**生成物なし**。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/318-openapi-path-param-tests`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-318`・
  起点 `21bb63b`・base の参照 `origin/main`・base `21bb63b6974db9698574c924e08b1790d7f1afab`
- 実装: 済み。`test-scaffold.py` は 試料 148 件・変異 101 件で緑（新しい検査が今の生成のどの試料も断らない＝基準 4）
- 関門 1 パス目: Verifier（sonnet）反証 0 件・`/code-review`（high）指摘 10 件 → 直す 3 件（R1・R2・R8）＋記録 1 件（R10）・残課題 6 件
  （採否は下の「1 パス目の指摘と採否」）。差し戻し 1 回（手順 4 へ）
- 指摘対応: `test-scaffold.py` に `typed_dict_fields` と `types.py` との突き合わせ・変異「OpenAPI から入力の項目を落とす」・
  試料「入力が空（GET）」「入力が空（POST）」を足した。試料 150 件・変異 102 件で緑
- 交絡（指摘対応）: 陽性対照——新しい変異を R1 の前（`7d4edc9`）と後のテストの「OpenAPI と型」に当てた（scratchpad の `ctl318r1.py`）。
  無変異は両方緑、変異は前で緑・後で赤（「CalcDiscountInput の項目 ['rank'] が types.py の ['amount', 'rank'] と違う」）。
  入力が空の 2 試料は無変異で緑、変異で同じメッセージの赤。**ただしこの赤は F-001（CalcDiscount）から来ており、
  入力が空の F-002 の検査を判別していない**（2 パス目の CR5）——言えるのは「入力が空の試料でも検査が誤って断らない（基準 4）」まで
- 関門 2 パス目（2026-10-21・HEAD `3eb86f9`）: `/code-review`（high）指摘 6 件（採否は未記入・下記の要約）。
  Verifier（sonnet）1 回目は利用上限で報告を回収する前に止めた（欠票）。**再実行した 2 回目: 反証 2 件**（R-A・R-B。下の表）。
  再実行の終了時、作業ツリーに変更なし（Verifier の報告と、親の確認の両方）
  - CR1 `types.py` との突き合わせは項目名だけ。`schema_of` で enum を落とす・integer→number にする変異が全 150 試料で緑（不変条件 1）
  - CR2 docstring の「schema が落ちても赤」が CR1 の変異で偽
  - CR3 読み取り段で落ちた項目は `types.py` からも落ちるので R1 の検査では見えない（`openapi_shape` の固定 3 項目だけが捕まえる）。`case.ir` と比べる案
  - CR4 `typed.get(name, [])` が types.py に無い型を空の型として扱う。入力が空の Input を types.py が出さない変異が緑
  - CR5 計画の R8 の陽性対照は F-001 を壊しており、入力が空の試料（F-002）の検査を判別していない（記録）
  - CR6 schema の食い違いを捕まえる変異が `MUTATIONS` に無い
  - **注意**: `/code-review` が、レビュー中に本物の worktree の `scaffold.py` が一時的に `if False:` に書き換わり `o.txt` が在ったと報告（直後に元に戻った）。並行していた Verifier の可能性。再開時に `git status` が空なのは確認済み
- 2 パス目の採否: 直す 3 件（CR1＝R-B・CR2・CR6。同じ穴）＋記録 1 件（CR5）・残課題 2 件（CR3・CR4＝R-A）。表は下の「2 パス目の指摘と採否」
- 狭いパスの起点: この行を書いたコミット（2 パス目の指摘対応を始める直前の HEAD）。メッセージ「#318 の 2 パス目の採否を記録する」のコミット
- 2 パス目の指摘対応: `input_split_problem` が `<Base>Input` の各項目の schema を `types.py` の注釈から戻した schema と突き合わせる。
  変異「OpenAPI の schema から enum を落とす」を足した。試料 150 件・変異 103 件で緑
- 交絡（2 パス目の指摘対応）: 陽性対照——足した変異を修正前（`ec6d6df`）と修正後のテストの exit 0 の全 50 試料に当てた
  （`.git` を持たない複製。scratchpad の `ctl2/ctl.py`）。無変異は両方 0 件赤、変異は修正前 0 件・修正後 49 件赤
  （残る 1 件は OpenAPI を書かない `--dry-run`）。赤のメッセージは新しい検査のもの（「rank の schema … が types.py の … と違う」）
- 狭いパス（Verifier・sonnet、起点 `ec6d6df`）: 反証 2 件（N1・N2。下の「狭いパスの指摘」）。Verifier が設計した変異 15 本のうち
  素通りは「`PY_TYPES` の string を bytes に」の 1 本（陽性対照つき）。指摘は直さず人間に渡す
- 次: `check-all.py` → PR → PR コメント
- 割り目 2（2 パス目の前）: 訊いた → **「ここで割る」が選ばれた**（2026-10-21）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 318` → 2 パス目から
- 割り目 1（手順 4 の完了時）: 訊いた → **「ここで割る」が選ばれた**（2026-10-21）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 318` → 手順 5 から（Verifier と `/code-review` の 1 パス目。どちらも未着手）
- 反証: —
- 交絡: 実験 1 つ。陽性対照——足した 4 変異を、修正前（`21bb63b`）と修正後のテストの試料「パスの変数」に当てた
  （scratchpad の `ctl318.py`）。無変異は両方緑、4 変異は修正前で全部緑・修正後で全部赤。赤の理由は新しい検査のメッセージ
  （「schema が入力の型と違う」×2・「ボディの型の required が全項目でない」・「query パラメータ limit が必須でない」）。
  観測窓: この 1 試料・各 1 回。「入力の型を縮める」は検査 4（項目の和）より先に検査 2（schema の一致）で赤になる——
  検査 4 だけが殺す変異は足していない

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 生成を直す | 採らない | 生成は正しい。#318 はテストの穴 |
| 応答（`<Base>Output`・`<Base>Error`）の整合も見る | 採らない | #318 の外。パスの変数とは関係しない |

### 1 パス目の指摘と採否

Verifier（sonnet）: 反証 0 件（自作の変異 12 本ほどのうち、新しい検査だけで緑のまま残ったのは
`in` を header に・`additionalProperties` を true に・`requestBody.required` を false に、の 3 本。うち 1 本目は既存の検査が赤）。
`/code-review`（high）: 指摘 10 件（受入基準を渡す前に完了した報告 9 件は、渡したあとの報告と重なるので後者で数える）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1 新しい検査は OpenAPI の中だけで突き合わせ、入力の全項目と比べていない。Input・パラメータ・ボディから同じ項目が一緒に落ちると緑 | 示せる（レビューの変異: `openapi()` で入力から amount を除くと「OpenAPI と型」を含む 45 件が緑） | 2 | 直す（`<Base>Input` の項目を、中間表現から独立に生成される `types.py` の同名の型の項目と突き合わせる。変異を 1 本足す） |
| R2 計画の表が不変条件 2 の守り方を「検査 4」としているが、計画の変異を殺すのは検査 2。「未証明: 無し」は誠実でない | 示せる（R1 と同じ） | 2 | 直す（R1 の修正に合わせて表の守り方を書き直す） |
| R3 新しい検査が素の添字で読むので、形の崩れた OpenAPI では赤でなく例外で止まる | 示せる（Body の `required` キーを消す変異で KeyError） | 無し（例外でもテストは非 0 で終わる。受入基準は「赤になる」） | 残課題 |
| R4 パラメータの `in` とメソッドごとの置き場所を見ていない（docstring の「ちょうど」より弱い） | 示せる（POST の残りをクエリへ移す変異を新しい検査が通す） | 無し（置き場所は基準 1〜3 に無い。既存の後処理が一部を捕まえる） | 残課題 |
| R5 `requestBody.required: true` を見ていない（docstring は「必須のどれかが落ちても赤」） | 示せる（全 48 試料で生き残る） | 無し（基準 3 はボディの型の `required` とクエリ） | 残課題 |
| R6 検査 1・4 とボディの schema 比較だけで殺される変異が `MUTATIONS` に無い | 示せない（検査は実験で効いている。将来 no-op にされる話） | 無し（基準 5 は足した変異が赤になること） | 残課題 |
| R7 `required` を順序つきで比べる（JSON Schema では集合） | 示せない（今の生成は sorted。逆順にする変異は意味が同じ仮定の話） | 無し | 残課題 |
| R8 基準 4 の経路に挙げた「入力が空」と PATCH の exit 0 の試料が無い | 示せる（試料の一覧に input が空のものが無い。grep） | 4 | 直す（入力が空の試料を GET と POST で足す。PATCH は PUT と同じ分岐なので足さない——残課題） |
| R9 requestBody の取り出しとループが `path_params_problem` の写し | 示せない | 無し | 残課題 |
| R10 計画の「同じことを述べている箇所の数」で 3 つ挙げて「2 箇所」 | 示せる（計画の文面） | 無し（記録） | 記録なので直す（成果物ではない） |
| V1（Verifier）`additionalProperties`・`requestBody.required` を見ていない | 示せる（Verifier の変異） | 無し | 残課題（R5 と同じ） |

### 2 パス目の指摘と採否

`/code-review`（high）: 指摘 6 件。Verifier（sonnet・再実行）: 反証 2 件（どちらも `/code-review` の指摘と重なる）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1＝R-B `types.py` との突き合わせが項目名だけ。`schema_of` が enum を落とす・型を変えると、Input・パラメータ・ボディが一緒に変わって緑 | 示せる（両方の関門の変異: `schema_of` で enum を落とすと全 150 試料が緑） | 1（経路「enum を落とす（rank）／型を変える」） | 直す（`<Base>Input` の各項目の schema を、`types.py` の注釈から復元した schema と突き合わせる。`types.py` は `schema_of` を通らない） |
| CR2 docstring の「schema が落ちても赤」が CR1 の変異で偽 | 示せる（CR1 と同じ） | 1 | 直す（CR1 の修正で事実にする） |
| CR3 読み取り段で落ちた項目は `types.py` からも落ちるので、R1 の突き合わせでは見えない | 示せない（`amount` を両方から落とす変異は既存の `openapi_shape` が赤。固定の 3 項目の外の項目が落ちる、は仮定） | 2 | 残課題（`case.ir` と比べる案） |
| CR4＝R-A `typed.get(name, [])` が、`types.py` に無い型を空の型と扱う。入力が空の入口で `types.py` が Input を出さない変異が緑 | 示せる（両方の関門の変異） | 無し（入力が空なら `<Base>Input` は全項目＝0 項目を持つ。基準 2 は破れない） | 残課題 |
| CR5 計画の R8 の陽性対照は F-001 を壊しており、入力が空の試料（F-002）の検査を判別していない | 示せる（計画の文面と赤のメッセージ） | 無し（記録） | 記録なので直す（「交絡（指摘対応）」の文面を言える範囲まで弱めた） |
| CR6 schema の食い違いを捕まえる変異が `MUTATIONS` に無い | 示せる（CR1 の変異が生き残る） | 1 | 直す（変異「`schema_of` が enum を落とす」を足す） |

### 狭いパスの指摘

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| N1 `typed_dict_fields` が `Literal[...]` の `type` を先頭の値の Python の型で戻すので、`{"type": "number", "enum": [1, 2.5]}` の入力を scaffold が正しく生成しても、検査が `integer` と戻して赤にする | 示せる（Verifier が作った試料で exit 0 の生成のあとに「rank の schema {'type': 'number', 'enum': [1, 2.5]} が types.py の {'type': 'integer', …} と違う」。先頭が float なら緑。既存の試料に number の enum は無い） | 4 | 人間が決める（満たしていない受入基準として PR コメントで名指し） |
| N2 enum の無い string の入力項目を持つ exit 0 の試料が無く、`PY_TYPES` の string を壊す変異が素通りする | 示せる（変異が 49 試料で緑。`memo: string` を足した試料では赤＝検査は効く） | 無し（欠けているのは試料） | 人間が決める |
