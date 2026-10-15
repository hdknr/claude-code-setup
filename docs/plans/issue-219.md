# Issue #219: spec-loop 段 4 — scaffold スキルと dev-loop への差し戻し規定

親: #214（段 4）。前提: 段 3（#218 / PR #258、マージ済み）。

## 変更範囲

触る:

- `plugins/spec-loop/skills/scaffold/` — 新規。確定した仕様 → `spec_ir.json` → 生成 → Issue の登録
- `plugins/spec-loop/references/spec-ir.md` — 新規。`spec_ir.json` の形の原本
- `plugins/spec-loop/references/handoff-issue.md` — 新規。dev-loop に渡す Issue の本文の形の原本
- `plugins/spec-loop/references/tree.md` — `spec_ir.json`・`scaffold/`・Issue 本文の出力先を足す
- `plugins/spec-loop/references/spec-exit.md` — 「`scaffold`（未実装）」を直す
- `plugins/spec-loop/references/qa-csv.md` — 起票元 `開発` の行に、差し戻しの規定の在り処を足す
- `plugins/spec-loop/scripts/scaffold.py` — 新規。検査・生成・`--check`（標準ライブラリのみ）
- `plugins/spec-loop/skills/*/SKILL.md` — 既存 4 本は版のバナーだけ
- `plugins/spec-loop/README.md` — スキル・スクリプト・references の一覧
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版 0.5.0 と description
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 新規。仕様の穴を `qa.csv` に差し戻す規定
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 差し戻しの規定への指し先（手順 1・手順 4）と版のバナー
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版 1.39.0
- `.claude-plugin/marketplace.json` — 2 つのプラグインの版と spec-loop の description
- `docs/plugins/dev-loop-design.md` — `skill-metrics.py` の生成ブロック（スクリプトで再生成するだけ。手で書かない）
- `scripts/test-scaffold.py` — 新規。回帰テスト（変異テストを含む）
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 同上
- `docs/plugins/index.md` — spec-loop の節
- `CLAUDE.md` — プロジェクト構成
- `docs/plans/issue-219.md` — この計画

触らない:

- dev-loop の frontmatter と JSON の description — 規定の追加は「いつ起動するか」を変えない
- dev-loop の Eval（`evals/`）— 差し戻しの振る舞いの Eval は #214 の「決めていないこと」
- `check-skill-pointers.py` ほか既存の歯止めの本体 — 新しいスキル・references は既存の検査がそのまま見る
- 正本と開発のリポジトリが別のときの `scaffold/` の写し方 — 対象リポジトリの `CLAUDE.md` に任せる

## 決めたこと

1. **生成はスクリプト、`spec_ir.json` を書くのはスキル（LLM）。** 仕様（`docs/spec/`）から中間表現を書き起こすのは判断なので
   スキルが行い、そこから先（OpenAPI・型・Red テスト・Issue 本文）は答えが一意に決まるので `scaffold.py` が行う。
2. **`scaffold.py` は自分で関門を通す**——`check-spec-exit.py` の条件 1（反映済みでない Q&A・未決定の印が 0 件）を
   自分で呼び、通らなければ 1 バイトも書かない（`build-proposal.py` が照合を自分で呼ぶのと同じ形）。
   **条件 2〜5 は判定しない**（判定役の報告で決まる）——スキルが `spec-review` の報告を確かめる。
3. **`spec_ir.json` が指す Q&A は実在し `反映済み` で、`source` の仕様ファイルは実在する**——スクリプトが見る。
   中間表現に、仕様に無いことを LLM が足した跡を残させないため（足せなくはないが、出所を書かずには足せない）。
4. **Red テストは Python の `unittest`**（標準ライブラリだけで回る）。実装は `<operation id>(**input) -> dict` の関数として
   引数で名指しするモジュールから探し、**無ければ `fail`（エラーではなく失敗）**にする。言語を変えるなら OpenAPI から
   対象リポジトリの道具で作る（スクリプトは持たない）。
5. **OpenAPI・型・Red テストは `scaffold/` に置いて commit する**（Issue から指す受け渡しの契約なので）。
   決定論的に生成し、**`--check` で鮮度を見る**。Issue 本文は `build/scaffold/issues/` に置き、commit しない（登録すれば
   GitHub に残る）。**関門が通らないとき、古い Issue 本文は消す**（古い本文を登録させない）。`scaffold/` は消さない
   （commit 済みで、`--check` が乖離を見る）。
6. **Issue 本文は sha256 で、指すファイルを固定する**——`spec_ir.json` と Red テストの指紋を持ち、dev-loop は
   手元のファイルが Issue の時点と同じかを確かめられる。
7. **スクリプトは Issue を登録しない**（`gh` を呼ばない。ネットワークに出ない・決定論的）。登録はスキルが
   `gh issue create --body-file` で、**生成した本文を変えずに**行う。外に出す操作なので、**登録の前に利用者に確かめる**。
8. **dev-loop 側は `references/spec-gap.md` に置き、`SKILL.md` には指し先だけ**——条件が立ったとき（Issue が
   spec-loop から来た・仕様の穴を見つけた）だけ要る規定なので、起点に載せない（`CLAUDE.md`「条件つきの節を `references/` に出す」）。
   **dev-loop から spec-loop のファイルを相対パスで指さない**（`check-skill-pointers.py` はプラグインの外を落とす）。
   Issue の印（`<!-- spec-loop-handoff: v1 -->`）だけを 2 つのプラグインで共有し、**写しの一致はテストが見る**。

## デプロイ経路

main へのマージで GitHub Pages（`docs/plugins/index.md`・設計ドキュメントの生成ブロック）が更新される。
プラグインはカタログ経由（`plugin update`）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | Issue 本文 1 件から、受入基準・Red テスト・Q&A の回答・仕様を辿れる | (a) 本文の生成（`scaffold.py`） (b) 登録（スキルが本文を書き換える・別の本文を渡す） (c) 本文が指すファイルが無い・後で変わった (d) dev-loop が spec-loop の Issue と気づかない (e) Q&A の回答が本文に無い（No だけ） | (a)(c)(e) テストで本文を生成し、印・機能・ケースごとの Red テスト名・Q&A の No と回答・パスと sha256 を確かめ、**本文のパスと sha256 を実ファイルに当てて一致すること**を見る。(b) スキルの「守ること」（**未証明**）。(d) dev-loop の `SKILL.md` 手順 1 が印を見て `references/spec-gap.md` へ送る（**未証明**: 振る舞い） |
| B | 生成した Red テストが、実装の無い状態で実際に失敗する | (a) 実装のモジュールが無い (b) モジュールはあるが関数が無い (c) 関数が誤った値を返す (d) **テストが別の理由で落ちている**（陽性対照が無い） (e) 1 件の失敗が他を隠す（ケースごとに失敗しない） (f) エラーで落ちて「失敗」と区別がつかない | テストで生成した Red テストを `unittest` で実際に走らせる。(a)(b)(c) で非ゼロ・失敗数＝ケース数、(d) **正しい実装を置くと緑**（陽性対照）、(e) 失敗数がケース数と一致、(f) `errors=0` で `failures=N` |
| C | 確定していない仕様からは生成しない | (a) 反映済みでない Q&A がある (b) 仕様に未決定の印 (c) `spec_ir.json` が形に反する（各規則） (d) 指す Q&A が無い・`反映済み` でない (e) `source` が無い (f) 失敗時に古い Issue 本文が残る (g) 一部だけ書いて落ちる | `scaffold.py`。(a)(b) は `check-spec-exit.py` を呼ぶ。(c)(d)(e) は自前の検査。失敗時は何も書かず、`build/scaffold/issues/` を消す。全部を組み立ててから書く。テスト＋変異 |
| D | 生成は決定論的で、鮮度を `--check` で見られる | (a) 2 回の生成でバイトが違う (b) `spec_ir.json` を直して再生成し忘れる (c) 消した機能の Red テストが残る (d) 手で直した生成物 | 2 回生成してバイト一致。`--check` が (b)(c)(d) で非ゼロ・生成直後は 0（陽性対照）。テスト＋変異 |
| E | データの決まりは `references/` の 1 箇所。スクリプトの定数はその写しで、テストが突き合わせる | 型・メソッド・印の写しがずれる。dev-loop 側の印の写しがずれる | `test-scaffold.py` が `references/spec-ir.md`・`handoff-issue.md`・dev-loop の `references/spec-gap.md` と定数を突き合わせる |
| F | dev-loop に差し戻しの規定が入り、版が上がっている | (a) 規定が `SKILL.md` から辿れない (b) 版が 3 箇所で食い違う (c) 生成ブロックが古い (d) 指し先が実在しない | (a) 手順 1・手順 4 から `references/spec-gap.md` を指す。(b)(c)(d) `check-all.py`（`check-plugin-versions`・`skill-metrics --check`・`check-skill-pointers`） |
| G | 既存の歯止めが緑 | 版・description・指し先・件数・マーカー | `check-all.py` |
| H | スキルが仕様の穴を推測で埋めない・Issue を確かめずに登録しない・生成物を手で直さない | スキルの散文 | `scaffold/SKILL.md` と dev-loop の `spec-gap.md` の「守ること」（**未証明**） |

### 組み合わせ（必須要件の掛け算）

- 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目 = 4 つの受け渡し
- 既知の限界・決着済みの論点も同じ 4 つに渡す

### 検証で証明できるもの

A(a)(c)(e)・B・C・D・E・F(b)(c)(d)・G はスクリプトとテストで実際に走らせて確かめる。

### 未証明（この環境では証明できない）

- A(b)(d)・F(a) の振る舞い・H: スキル（LLM）が本文を変えずに登録するか、dev-loop が印に気づいて差し戻すか。
  散文の規定だけで、Eval を置いていない（#214 の「決めていないこと」）。人間レビューへ。
- **「dev-loop が周を始められる」の実地**——実際に Issue を登録して dev-loop を起動していない
  （外に出す操作で、この周の受入基準のために公開リポジトリへ試料の Issue を作らない）。確かめたのは
  「本文から辿れるものが揃い、指すファイルと一致する」まで。

### 生成物

- `skill-metrics.py` の生成ブロック（設計ドキュメント §8.2）——**該当する**（dev-loop の `SKILL.md` を触る）。
  `python3 scripts/skill-metrics.py` で再生成し、`--check` で差分ゼロ（check-all に入っている）。
- 図（drawio）は触らない——該当なし。
- `scaffold.py` が対象リポジトリに作る `scaffold/` は、このリポジトリの生成物ではない（`--check` を作るのは D）。

## 周の大きさ

同じことを述べている箇所:

- `spec_ir.json` の形: `references/spec-ir.md` ＋ スクリプトの定数（テストで突き合わせ）＝ 2
- Issue 本文の形: `references/handoff-issue.md` ＋ 生成スクリプト ＋ dev-loop の `spec-gap.md`（印の写し。テストで突き合わせ）＝ 3
- scaffold の説明: frontmatter ＋ JSON 2 ＋ README ＋ 公開ページ 2（表と節）＋ `CLAUDE.md` ＝ 7

分けない理由: Issue が段 4 として 1 周に起票しており、本文の形（spec-loop 側）と差し戻し（dev-loop 側）は
**同じ印を介した 1 つの境界**の両側なので、片方だけでは境界が決まらない。

## 未解決・確認待ち

- なし（着手時）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/219-scaffold-handoff`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-219`、
  起点 `0074e5d`、base 参照 `origin/main` → `0074e5d3c69cbe4dfd62e0af3a41a01c588cf4c5`
- 実装: 完了（手順 4）。実装コミット `656fb31`（trailer の位置を直すため amend した。amend 前は `af9acf3`）。
  `check-all.py` 40/40 緑（コミット後に実測。`check-description-sync` は `Skip-description-sync:` を最後の trailer 段落に置いて通った）、
  `mkdocs build --strict` 0。`test-scaffold.py` 試料 64・変異 31
- 実装中の手戻り: `check-skill-pointers.py` が dev-loop の `spec-gap.md` から spec-loop の `references/…` を指した 2 箇所を落とした
  （決めたこと 8 のとおり）——「spec-loop プラグインの `handoff-issue.md`」の書き方に直した。
  変異 2 本が最初生き残った——どちらも**試料が判別していなかった**（全角の id はケースの id でも落ちていた・
  `| Q-002 |` は受入基準の表にも出ていた）。変異ではなく試料を直した
- 関門 1 パス目: **済**。Verifier（`dev-loop:dev-loop-verifier`・sonnet）**反証 1 件**（R1。CR1 と同じ）、
  `check-all.py` 40/40・`skill-metrics --check` 緑を独立に確認。`/code-review`（high）**指摘 10 件**。
  採否は「既知の限界」の表——**直す 6 件**（CR1/2/3/4/7/8）・**残課題 4 件**（CR5/6/9/10）
- 1 パス目の指摘対応: **済**。コミット `d672046`。`test-scaffold.py` 試料 70・変異 37（変異はそれぞれ直した行を
  元に戻す形で、名指しした試料が赤になることを当てている）、`check-all.py` 40/40。
  **`write()` を先に全部バイトにする変更（CR2 の多重防御）は、サロゲートの拒否が先に止めるので単独の変異では赤にできない**（等価変異）——テストで守っていない
- 関門 2 パス目: **済**。base は周の base `0074e5d…`。Verifier（`dev-loop:dev-loop-verifier`・sonnet）**反証 0 件・試料の穴 1 件**
  （V2-1）。`check-all.py` 40/40・`skill-metrics --check` 緑・CR1/2/3/4/7/8 を戻す変異がそれぞれ赤・CR2 の等価変異の申告は事実と一致、を独立に確認。
  `/code-review`（high）**指摘 10 件**。採否は「既知の限界」の 2 パス目の表——**直す 8 件**（V2-1・P2-1〜P2-8）・**残課題 2 件**（P2-9・P2-10 後半）
- 2 パス目の指摘対応: **済**。コミット `dfeb0fb`。**狭いパスの起点 `ce435b43d14263e175ece66942e5d62a395111b4`**（採否を記録したコミット。HEAD の祖先を確認）。
  `test-scaffold.py` 試料 81・変異 47、`check-all.py` 40/40（`skill-metrics.py` で生成ブロックを作り直した後）。
  **新しい試料は直す前の本体（`ce435b4` を `git archive` で外に出したもの）で赤**——V2-1 の試料だけは旧版でも緑（本体ではなくテストの穴なので、変異で殺す）。
  `write()` 先頭の `clear_issues` は `main` の捕捉と重なるので単独では赤にならない（等価変異。多重防御）
- 狭いパス: **済**（`dev-loop:dev-loop-verifier`・sonnet。差分 `git diff ce435b4…`）。**受入基準を破る反証 0 件**・
  **素通りした変異 3 件**（N1〜N3。表は下）。Verifier 自前の変異 12 本のうち 5 本は置換が著者の変異の文字列を壊して「届かず」——
  緑とも赤とも言えない（当て直していない）。`write()` 先頭の消去の等価変異の申告は「移しても緑・外すと赤」と確認された
- PR #259 を作成。PR 側の CI（`check`・`build`）緑・`MERGEABLE` を `gh pr checks` で確認。レビュー結果は PR コメント
- 手順 7: **承認待ち**（マージは人間が決める）。反映経路は GitHub Pages とプラグインのカタログ
- 手順 8: 焼き戻す学びなし（この周の型——生成側で関門を通す・写しをテストで突き合わせる——は既に `CLAUDE.md` にある）
- この周の起票: 0 件（N1〜N3 の起票候補は人間に訊いた）
- 割り目（手順 6・2 パス目の前）: 提案した（AskUserQuestion）→ **「ここで割る」を選択**。次は 2 パス目の Verifier と `/code-review`
- 交絡: 実験は Red テストの実行と変異テスト。Red テストの失敗には陽性対照（正しい実装で緑）を置き、
  失敗が「エラーではなく失敗」であることを `failures=N` で見る。変異は届いていること（1 回現れる）を先に確かめる
- 割り目（手順 4）: 提案した（AskUserQuestion）→ **「ここで割る」を選択**。次は手順 5（Verifier）と手順 6（/code-review）の 1 パス目

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| Red テストを Python 以外で生成しない | 採った（Python だけ） | 標準ライブラリだけで、実装が無いときに実際に失敗することまで CI で確かめられる。他の言語は OpenAPI から対象リポジトリの道具で作る |
| `spec_ir.json` が仕様と意味で一致するか | 守らない（判断） | 出所（`source`・Q&A）の実在までは機械で見る。意味の一致は LLM の書き起こしで、検査できない |

### 1 パス目の指摘（Verifier 反証 1 件 ／ `/code-review` 10 件。Verifier R1 は CR1 と同じ）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1（＝V-R1） | 別の operation id が同じ `pascal()` 名に潰れ（`a_1`/`a1`・`foo_bar`/`foo__bar`）、OpenAPI の schema と `types.py` の class が上書きされる | 示せる（両関門が写しで exit 0・schema 1 組を再現） | A(a)・C(c) | 直す |
| CR2 | 孤立サロゲート（`"\ud800"`）が `one_line` を通り、`write` の途中で落ちて契約を 0 B に切り詰め・古い Issue 本文が残る | 示せる（再現: openapi.json 1374 B → 0 B） | C(f)(g) | 直す |
| CR3 | `number` に巨大な整数で `math.isfinite` が OverflowError、古い Issue 本文が残る | 示せる（再現） | C(f) | 直す |
| CR4 | `source` がドットディレクトリ（`docs/spec/.draft/`）を指すと、`check-spec-exit` が見ない場所の未決定の印を素通しする | 示せる（再現: TBD を含むファイルで exit 0） | C(b) | 直す |
| CR5 | Issue が `spec_ir.json` 全体の sha256 を持つので、無関係な機能の編集で登録済みの Issue が全部不一致になる | 示せる（筋書き。不一致になることは式から決まる） | 無し（辿れることは保たれ、不一致は止まる側に倒れる。決めたこと 6 の設計） | 残課題 |
| CR6 | パスの変数 `/items/{id}` が path パラメータとして宣言されず、OpenAPI として無効 | 示せる（再現） | 無し（OpenAPI の妥当性は受入基準に無い） | 残課題 |
| CR7 | `--impl-module` がどこにも記録されず、指定せずに `--check` すると新しい生成物を古いと言う | 示せる（再現: exit 1） | D（`--check` が鮮度を誤判定する） | 直す |
| CR8 | Red テストが `assertEqual` で比べ、`True == 1` のため型の違う実装が緑になる | 示せる（再現: `{'ok': 1}` で OK） | B(c)（誤った値を返す実装で失敗しない） | 直す |
| CR9 | 印の無い手書きの `scaffold/` のファイルを黙って上書きする | 示せる（再現） | 無し（受入基準は手で直した生成物の*検出*（D(d)）まで） | 残課題 |
| CR10 | `check_qa_refs` の「`反映済み` でない」分岐は `load` の関門が先に止めるので到達しない。C(d) の守り方に書いた「テスト＋変異」が当たっていない | 示せる（行を消してもテストが緑） | 無し（C(d) は関門で守られている。計画の守り方の書き方の誤り） | 残課題 |

### 2 パス目の指摘（Verifier 反証 0 件・試料の穴 1 件 ／ `/code-review` 10 件）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V2-1 | `type_fits` の bool 分岐を `return True` に緩めても `test-scaffold.py` が緑（bool を integer・number の項目に返す試料が無い） | 示せる（Verifier が変異を当てて緑。届いていることも確認） | B(c)（テスト＋変異で守ると書いた経路が守られていない） | 直す（試料を足す） |
| P2-1 | `main` は `Unjudged` しか捕まえず、`method` が配列（TypeError）・深い入れ子（RecursionError）・`source` に NUL（ValueError）・桁の多いケース id（`int()` の ValueError）で traceback・exit 1 になり、古い Issue 本文が残る | 示せる（`/code-review` が写しで再現。直す前に試料で赤を確かめる） | C(f) | 直す |
| P2-2 | `write()` が契約を書いてから `clear_issues` するので、OSError で半分新しい `scaffold/` と古い Issue 本文が並ぶ | 示せる（`types.py` をディレクトリにして再現） | C(f)(g) | 直す（Issue 本文を先に消す。ファイルシステムの失敗で契約が一部だけ書かれる形は `--check` が言う、まで主張を弱める） |
| P2-3 | CR7 の修正で `--check` が自分の検査対象（Red テスト）から `IMPL_MODULE` を読むので、全部を一様に手で書き換えると「新しい」になる | 示せる（`sed` で全 Red テストを書き換えて exit 0） | D(d) | 直す（実装のモジュールを `spec_ir.json` の任意項目 `impl_module` に移し、`--impl-module` を廃する） |
| P2-4 | 書き込みでは記録を読まないので、`--impl-module` を付けずに作り直すと黙って `spec_impl` に戻り、`--check` も緑 | 示せる（再現） | D(b)（入力から作るものが入力だけで決まらない） | 直す（P2-3 と同じ修正） |
| P2-5 | dev-loop の `SKILL.md` 手順 1 も印の写しを持つが、`test-scaffold.py` は `spec-gap.md` の写ししか見ない | 示せる（印を v2 に揃えても `SKILL.md` だけ v1 のまま緑になる——直す前に変異で確かめる） | E | 直す |
| P2-6 | `stale()` が `read_text` で読むので改行が正規化され、CRLF に書き換えた Red テストを「新しい」と言う（Issue の sha256 とは食い違う） | 示せる（再現） | D(d)・A(c) | 直す（バイトで比べる） |
| P2-7 | `references/tree.md` が「Issue の sha256 で写した `scaffold/` が同じかを確かめられる」と書くが、`openapi.json`・`types.py` は指紋を持たない | 示せる（Issue 本文に無い） | A(c)（記述が事実と違う） | 直す（記述を事実に合わせる） |
| P2-8 | `spec_ir_version: 1.0` が通る・`number` の enum `[1, 1.0]` が重複と見なされない | 示せる（再現） | C(c) | 直す |
| P2-9 | `contract_kept_issues_gone` が `openapi.json` の存在しか見ず、中身（0 B への切り詰め）を見ない | 示せない（レビューも「書きの前の符号化は等価変異という申告は正しい」と読み、変異を当てていない） | 無し | 残課題 |
| P2-10 | 読んだ `IMPL_MODULE` を `--impl-module` の誤りとして報告する・不一致を 2 にする・サロゲートで他の違反を出さない | 前半は P2-3 の修正で消える。後半は示せるが受入基準に無い（docstring の「全部を 1 行ずつ」との食い違い） | 無し | 残課題（後半） |

### 狭いパスの指摘（直さない。採否は人間が決める）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | `module_name` の `keyword.iskeyword(part)` を外しても `test-scaffold.py` が緑（予約語の部を持つ `impl_module` の試料が無い） | 示せる（変異が素通り） | 無し（値は `!r` と `importlib` でしか使われず、構文に載らない） | 人間が決める |
| N2 | `module_name` が最初の部しか見ない変異でも緑——`a.Bad-Name`・`` a.`x` ``・`a..b` が生成される（変異前は拒否） | 示せる（陽性対照つき） | C(c)（中間表現の規則の検査がテストで守られていない） | 人間が決める |
| N3 | `main` の「Issue の本文を消せなかった」分岐（`except OSError as again`）を踏む試料が無い | 示せる（変異が素通り） | 無し | 人間が決める |
