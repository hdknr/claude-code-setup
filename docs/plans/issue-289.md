# Issue #289 — scaffold の OpenAPI がパスの変数を path パラメータとして宣言せず、無効になる

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — パスの変数の検査（`check_ir`）と OpenAPI の生成（`openapi`）
- `plugins/spec-loop/references/spec-ir.md` — `path` の決まり（変数は `input` の項目名）。**決まりの原本**
- `scripts/test-scaffold.py` — パスの変数を持つ試料・OpenAPI の妥当性の検査・誤りの試料・変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `docs/plans/issue-289.md` — この計画

触らない:

- `references/handoff-issue.md`・`references/tree.md`（パスの変数を述べていない。`grep` で確認）
- types.py と Red テストの生成（関数は `input` の項目をそのまま受け取る。パスの変数も項目の 1 つ）
- 入れ子・配列の型（#289 の外）

### 同じことを述べている箇所の数

規則は `references/spec-ir.md`（原本）と `scaffold.py` の検査（実装）と `test-scaffold.py`（期待）の 3 箇所。
分けない理由: 決まり・実装・テストは同じ 1 つの決定で、別の周にすると片方が古い決まりで検査する。

## 決めたこと

- **パスの変数は `{` と `}` で 1 つの名前を囲む。名前は `input` の項目名でなければならない**（無ければ中間表現の誤り＝1）。
  対にならない波括弧・空の `{}`・同じパスに同じ変数 2 回も誤り。
- **変数の名前だけが違うパス（`/items/{id}` と `/items/{key}`）は OpenAPI では同じパス**（OpenAPI 3.1 §4.8.8
  "Templated paths with the same hierarchy but different templated names MUST NOT exist"）。メソッドが違っても誤りとする。
  #289 の「やること」には無いが、**同じ不変条件（パスの変数について OpenAPI が妥当）を破る別の経路**なので入れる。
- **生成**: パスの変数は `in: path`・`required: true`。残りの項目は GET・DELETE なら `in: query`、それ以外は
  `requestBody`。**パスの変数を持つ入口の `requestBody` は、パスの変数を除いた `<Base>Body` を指す**
  （パスとボディに同じ値を 2 度求めない）。残りが無ければ `requestBody` を作らない。
  **パスの変数を持たない入口の出力は 1 バイトも変えない**（既存の `scaffold/` の `--check` を古くしない）。
  `<Base>Input` は型（関数の入力の全体）として残す。

## 乗るデプロイ経路

プラグインの版を上げて配布する（minor: 中間表現の決まりを足す——前は通った中間表現を断るようになる）。
`docs/plans/` を含むので、マージで GitHub Pages にもデプロイされる。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | 生成した OpenAPI で、各パスの `{x}` がすべてその操作の `in: path`・`required: true` のパラメータとして宣言され、パスに無い path パラメータが無い | GET・DELETE（query 経路）／POST・PUT・PATCH（requestBody 経路）／変数 2 つ／変数だけのパス | `openapi()` で宣言。テストの妥当性検査を全試料の OpenAPI に当てる |
| 2 | パスの変数がクエリ・ボディに重ねて出ない | GET の query／POST の requestBody | 変数を除いて query・Body を作る |
| 3 | パスにあって `input` に無い変数・壊れた波括弧・重複変数・変数名だけが違うパスは 1 で止まり、何も書かない | 各誤り。`input` が辞書でない場合 | `check_ir` |
| 4 | パスの変数を持たない入口の出力は変わらない | 既存の試料 | 既存の「OpenAPI と型」「決定論的」と、基準の openapi.json を main の本体と比べる |
| 5 | 宣言を外す・各検査を外す変異が、名指しした試料で赤になる | 変異テスト | `MUTATIONS` |
| 6 | 版が 3 種類で揃い、歯止めが全部緑 | bump 漏れ | `python3 scripts/check-all.py` |

組み合わせ: 1 × 2（path に出した変数が query／body から抜けていること）。3 × 4（新しい検査が既存の試料を断らないこと）。

**この環境では証明できないもの（未証明）**: 外部の OpenAPI 検証器（openapi-spec-validator など）に通ること——
CI にもこの環境にも入っていない（標準ライブラリのみの方針）。テストは「パスの変数の宣言」という最低限の妥当性だけを見る。

生成物: リポジトリに commit した `scaffold/` は無い（試料は一時ディレクトリ）。`SKILL.md` の測定値は dev-loop だけで、触らない。
**生成物なし**（check-all.py の鮮度検査で確認する）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/289-openapi-path-params`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-289`・
  起点 `ccd29c6`・base の参照 `origin/main`・base `ccd29c6e1c10b2c231e653450723bf687b509aa1`
- 実装: 済み（コミット済み）。`test-scaffold.py` は 試料 147 件・変異 95 件で緑
- 必須マーカーの漏れ（`spec-ir.md` に `（必須）`）を check-norm-markers が捕まえ、直してコミットした
- check-all.py（マーカー修正後・`82dfcec`）: 44/44 本・失敗 0（ローカル）
- 関門 1 パス目: Verifier（sonnet）反証 0 件・`/code-review`（high）指摘 8 件 → 直す 2 件（R2・R3）・残課題 6 件
  （採否は下の「1 パス目の指摘と採否」）。差し戻し 1 回（手順 4 へ）
- 指摘対応（R2・R3）: `test-scaffold.py` だけ。パスの変数を持たない POST の形（`parameters` 無し・`<Base>Input` を指す・
  `Body` の型を作らない）を「OpenAPI と型」で見る／`run_case` で exit 0 の全試料の OpenAPI に `path_params_problem` を当てる／
  PUT・DELETE の試料を足す／レビューが素通りさせた 2 変異を `MUTATIONS` に足す。試料 148 件・変異 97 件で緑
- 交絡（指摘対応）: 陽性対照——post が OpenAPI を見ない「パスの変数の Red テスト」に、宣言を外した `scaffold.py` を当てて
  `run_case` の全体検査だけで赤（原本は緑）。scratchpad の `ctl.py`
- 2 パス目（2026-10-21、再開した周）: check-all.py（`38e2b43`）44/44 本・失敗 0（ローカル）。
  Verifier（sonnet）反証 0 件・`/code-review`（high）指摘 8 件 → 直す 1 件（P1）・残課題 7 件
  （採否は下の「2 パス目の指摘と採否」）
- 狭いパスの起点: `38e2b43`（2 パス目の指摘対応を始める直前の HEAD）
- 次: 2 パス目の指摘対応（P1: origin/main を取り込み、版を 0.13.0 に上げる）→ 狭いパス → PR
- 割り目 2（2 パス目の前）: 訊いた → **「ここで割る」が選ばれた**（2026-10-21）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 289` → 2 パス目から
- 割り目 1（手順 4 の完了時）: 訊いた → **「ここで割る」が選ばれた**（2026-10-21）。
  再開は worktree の中で `/clear` → `/dev-loop:dev-loop 289` → 手順 5 から。
  check-all.py の 2 回目（マーカー修正後）の結果は再開した側で確かめる（割る時点で走行中）
- 反証: —
- 交絡: 実験 2 つ。(a) 陽性対照——修正前の `scaffold.py`（`ccd29c6`）に新しい試料を当て、パスの変数の試料 8 件が赤、
  変わらないはずの「パスの変数の Red テスト」「OpenAPI と型」の 2 件が緑。修正後は 10 件とも緑。
  (b) 基準 4——修正前後の `openapi()` を同じ中間表現 3 つ（基準・PUT/DELETE/空の入力・PATCH/空の入力）に当ててバイト一致。
  観測窓はこの 3 つの形だけ（パスの変数を持たない入口の全形は数えていない）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 変数名だけが違うパスを止める | 採った | OpenAPI 3.1 が禁じる。不変条件 1 と同じ「パスについての妥当性」 |
| パスの変数の型を制限する（boolean を path に置かない等） | 採らない | OpenAPI として無効ではない。仕様の判断 |

### 1 パス目の指摘と採否

Verifier（sonnet）: 反証 0 件。`/code-review`（high）: 8 件。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1 `classify()` が前の版にも新しい検査を当てるので、旧 scaffold が通した v1（凍結済みかもしれない）があると v2 を永久に作れない | 示せる（レビューの再現: v1 に `/orders/{order_id}`・v2 で直しても exit 1） | 無し（前の版を決まりに当てるのは既存の設計。`classify` の docstring） | 残課題（人間に判断を渡す。版を major にするかと一緒に） |
| R2 基準 4 の守り方に挙げた「OpenAPI と型」「決定論的」が、パスの変数を持たない入口の出力の変化を捕まえない | 示せる（レビューの再現: 常に `<Base>Body` を指す変異・POST に `parameters: []` を足す変異が 147 件のどれにも殺されない） | 4・5 | 直す |
| R3 基準 1 の守り方「妥当性検査を全試料の OpenAPI に当てる」が、3 つの post にしか掛かっていない。PUT・PATCH・DELETE のパスの変数を当てる試料が無い | 示せる（`path_params_problem` の呼び出しは 3 箇所だけ。grep） | 1 | 直す |
| R4 `input` が辞書でない × パスの変数の試料が無い | 示せない（いまは正しく 1。将来の改変の話） | 無し | 残課題 |
| R5 「パスの変数を入力と突き合わせない」変異は KeyError（exit 2）で殺されている | 示せない（変異は赤。殺し方が弱いだけ） | 無し | 残課題 |
| R6 `spec-ir.md` に「入力がすべてパスの変数なら requestBody を作らない」「`<Base>Input` は参照されずに残る」が無い | 示せない（文書の欠落。生成物は正しい） | 無し | 残課題 |
| R7 前は通った中間表現を断るのに minor で上げている（CLAUDE.md の表では major） | 示せない（0.x の semver。判断の問題） | 無し | 残課題（R1 と一緒に人間へ） |
| R8 小さな整理（`PATH_VAR.sub` の 2 回計算・427 行の条件の再導出・テストの正規表現の写し） | 示せない | 無し | 残課題 |

### 2 パス目の指摘と採否

Verifier（sonnet）: 反証 0 件。`/code-review`（high）: 8 件。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| P1 main が #308 で spec-loop を同じ 0.12.0 に上げており、版が衝突する | 示せる（origin/main の `plugin.json` が 0.12.0） | 6 | 直す（main を取り込み 0.13.0） |
| P2 path パラメータの `schema` を見るテストが無い（`{"type":"string"}` に固定する変異が素通り） | 示せる（レビューの変異で 0 件失敗） | 無し（不変条件 1 は宣言＝名前・`in`・`required`。型は含めていない） | 残課題 |
| P3 「`<Base>Input` は型として残す」を見るテストが無い | 示せる（同上） | 無し（決めたことだが不変条件の表に無い） | 残課題 |
| P4 `<Base>Body` の `required` とクエリの `required` を見ていない | 示せる（同上） | 無し（不変条件 2 は重なりを見る） | 残課題 |
| P5 新しい決まりにも合うパスの変数の中間表現でも `openapi.json` が変わり、既存の `scaffold/` が `--check` で古くなる | 示せる（レビューの再現） | 無し（不変条件 4 はパスの変数を持たない入口だけ） | 残課題（R1・R7 と一緒に人間へ） |
| P6 誤りの試料が「何も書かない」を見ていない | 示せない（いまは `check_ir` が生成より前に 1 を返す。`scaffold.py:564-566`） | 無し | 残課題 |
| P7 Issue の本文の型の一覧に `<Base>Body` が無い | 示せない（本文と OpenAPI のずれ。生成物は誤っていない） | 無し | 残課題 |
| P8 `NO_BODY` のコメント「入力はクエリに載せる」が古い | 示せない | 無し | 残課題 |
