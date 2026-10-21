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
- 関門: 未着手
- 反証: —
- 交絡: 実験なし

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 変数名だけが違うパスを止める | 採った | OpenAPI 3.1 が禁じる。不変条件 1 と同じ「パスについての妥当性」 |
| パスの変数の型を制限する（boolean を path に置かない等） | 採らない | OpenAPI として無効ではない。仕様の判断 |
