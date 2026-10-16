# Issue #263: spec-loop 段 5c — 各スキルの差分モード

親: #260（段 5c）。前提: #262（5b。マージ済み・PR #269）。後続: #264（5d）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/diff-versions.py` — 新規。v<n-1> の全体と v<n> の全体を比べ、追加・変更・削除を出す（関数としても呼べる）
- `plugins/spec-loop/scripts/build-proposal.py` — v2 以降は前の版との比較の節を載せる（上の関数を使う）
- `plugins/spec-loop/references/versions.md` — 「版の差分」（比べ方の決まり）と、差分を読むものの表
- `plugins/spec-loop/references/tree.md` — 提案書の生成する部分に比較を足す（1 行）
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 差分モード（載せるのは作業中の版の Q&A だけ・前の版のファイルは直さず同じパスで置く）
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 差分モード（対象は作業中の版だけ・判定役に全体を参照として渡す）
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 差分モード（差分の規模を数え、差分の見積りを書く）
- `plugins/spec-loop/skills/proposal/SKILL.md` — 差分モード（変更の提案書）・frontmatter の description
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 版のバナーだけ
- `plugins/spec-loop/agents/*.md` — 判定役・検証役が「対象」と「参照」を分けて受け取る旨（必要なら）
- `plugins/spec-loop/README.md` — スクリプトの表と proposal の節
- `plugins/spec-loop/.claude-plugin/plugin.json` — 0.8.0・description
- `.claude-plugin/marketplace.json` — spec-loop 0.8.0・description（plugin.json と同じ値）
- `scripts/test-diff-versions.py` — 新規（変異テストを含む）
- `scripts/test-build-proposal.py` — 比較の節のテスト
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 同上
- `CLAUDE.md` — プロジェクト構成（新しいスクリプトとテスト）
- `docs/plans/issue-263.md` — この計画

触らない:

- `scaffold` の追加・変更・削除の振り分けと Issue の新しい形・dev-loop の v2 本文 — 5d（#264）
- 差分の周を始める前の「乖離」の確認（前の版の `--check`・既存の Red テスト）— #263 の「やること」に無い。5d で扱う
- 見積りの累計（前の版までの費用との合計）— 版ごとの `feasibility/` は差分の見積りで、合計を出す決まりが無い。提案書は差分の費用だけを載せ、そう書く
- `check-qa-csv.py`・`qa-to-pptx.py`・`check-feasibility-csv.py`・`schedule-to-gantt.py` — どれも 1 つの表のパスを取るので、作業中の版の表を渡せば差分モードになる（スクリプトは変えない）

**周の大きさ（同じことを述べている箇所）**: 「差分＝前の版の全体との比較」の決まりは `versions.md`（正）・`diff-versions.py` の
docstring・`build-proposal.py` の docstring・4 つの SKILL.md（指し先とコマンドだけ）・README・CLAUDE.md の **約 9 箇所**。
**分けない**: #263 は親から切り出した段で、4 スキルの差分モードは同じ「何が差分か」の定義に乗る。定義を `versions.md` に置き、
ほかは指すだけにして複製を増やさない。

## 決めたこと

1. **差分は「v<n-1> の全体」と「v<n> の全体」の比較で決める**（`merge-versions.py` の `merge` を `upto` を変えて 2 回）。
   単位は重ね合わせと同じ——Q&A は行（`No`）、機能は `id`、ほかのファイルはパス。
   - 追加: v<n> にあって v<n-1> に無い。変更: 両方にあって中身が違う。削除: v<n-1> にあって v<n> に無い。
   - **同じ中身を置き直しただけのものは「変更」に数えない**（比較なので）。v1 は前の版が無いので全部が追加。
   - 削除の理由は `docs/v<n>/removed.csv` の `理由` から添える。
2. **`diff-versions.py <docs> [--version <n>]`** が上を出す（既定は作業中の版）。終了コードは `merge-versions.py` に合わせる
   （0 出した・1 決まりに反する・2 読めない／版が無い）。何も書かない。
3. **提案書（v2 以降）**: 「前の版（v<n-1>）からの変更」の節を、**req のタグの時点の `docs/`** から作る（`git archive` を一時ディレクトリに
   展開して `diff-versions` の関数に当てる）。件数の表と、Q&A（前の回答 → この版の回答）・機能（題）・ファイルの一覧。
   費用の節は「この版の差分の見積り」と明記する（累計は出さない）。v1 は節を出さない。
   **重ね合わせが決まりに反すれば 1 で書かない。** `docs/v<k>/` の中のシンボリックリンクは決まりに反する（1）。
4. **各スキル**:
   - `req-loop`: 読む表・資料に載せる表は作業中の版の `qa.csv` だけ。前の版の質問を問い直すなら同じ `No` の行を作業中の版に置く。
     重複の確認と次の番号は全部の版を通して見る（重ね合わせた全体）。回答の反映で前の版の要求・仕様を直すときは、**前の版のファイルを
     直さず**、作業中の版の同じパスに写して直す（消すなら `removed.csv`）。
   - `spec-review`: Planner が書くのは作業中の版の `spec/` だけ。判定役に渡す**対象**は作業中の版の差分（`diff-versions.py` の出力と
     `docs/v<n>/`）、**参照**は重ね合わせた全体（`build/merged/`）。「全体の差分外の箇所は、差分と矛盾するときだけ指摘せよ」と添える。
     抜ける条件 1 は今のまま全体に当てる。
   - `feasibility`: 規模は `diff-versions.py` の出力（追加・変更・削除を分けて）から数え、`docs/v<n>/feasibility/` に**この版の差分の**
     見積りを書く。根拠には差分の項目（`F-xxx` の追加など）を書く。
   - `proposal`: v2 以降は変更の提案書になる（比較の節が生成される）。手書き部分は「なぜ変えるか」を書く。
5. 版: spec-loop 0.7.0 → **0.8.0**（能力の追加・minor）。

## verify の受入基準

### 不変条件

- **A**: 差分の分類（追加・変更・削除）は、v<n-1> の全体と v<n> の全体の比較と一致する（Q&A・機能・ファイルの 3 種とも）。
- **B**: 提案書（v2 以降）の比較の節は、**req のタグの時点**の中身から作られる（作業ツリーで後から直したものは入らない）。
- **C**: 比較を作れない（重ね合わせが決まりに反する・読めない）なら提案書を書かない（0 以外）。前の出力は消える（今のまま）。
- **D**: v1 の提案書は今と同じバイト（比較の節を持たない）。
- **E**: 同じ入力から同じバイト（`diff-versions.py` の出力・提案書）。
- **F**: 4 つのスキルの差分モードが Issue の「やること」4 項目を満たす——req-loop は作業中の版の Q&A だけを載せる／
  spec-review は対象が作業中の版・判定役に全体を参照として渡す／feasibility は `docs/v<n>/feasibility/` に差分の見積り／
  proposal は前の版との比較を載せる。
- **G**: スキルと README は決まりを複製せず `versions.md` を指す（`check-skill-pointers.py`・`check-duplicate-counts.py` が緑）。
- **H**: 版が 3 か所（marketplace・plugin.json・5 つの SKILL.md）で 0.8.0。description は JSON 2 か所が同じ値。

### 経路（A〜E を破りうる入口）

| 入口 | 守り方 |
| --- | --- |
| `diff-versions.py` の CLI（`--version` 省略・指定・範囲外・v1） | テスト |
| `build-proposal.py`（作業中の版・`--version`・`--req/--budget` を渡す） | テスト（B は tag 後に作業ツリーを直して入らないことを見る） |
| 前の版の `removed.csv`（v<n-1> 以前の削除は v<n> の差分に出ない） | テスト |
| 置き直し（同じ中身の同じ `No`） | テスト（変更に数えない） |
| ファイルの変更（バイトが違う）・追加・削除 | テスト |
| docs の中の版でない名前・`.` で始まる名前 | `merge` に任せる（今の挙動）。テストで 1 つ |
| シンボリックリンク（tar の中） | テスト |

### この環境で証明できないもの（未証明）

- スキル（SKILL.md）の差分モードを**モデルが実際にそう動かすか**——スキルを実データで回す手段が無い（Eval は dev-loop だけ）。
  文面の読解までが検証の範囲で、人間レビューに回す。
- 判定役が「参照」の全体から差分外の古い指摘を挙げないか——同上。

### 生成物

- `docs/plugins/dev-loop-design.md` の §8.2 生成ブロック: dev-loop の `SKILL.md` を触らないので**該当なし**（`skill-metrics.py --check` で確かめる）。
- 図の書き出し: drawio を触らないので該当なし（`check-diagram-freshness.py`）。
- spec-loop の生成物（提案書・pptx・gantt）はリポジトリに置かない（テストの中で作る）。

## 未解決の判断

- なし（費用の累計を出さないことは上の「触らない」に書いた）。

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/263-diff-mode`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-263`・
  起点 `694fe95`・base `origin/main` = `694fe9549abb7d97367b493806cc68abf87d3096`
- 実装: 済み（手順 4）。`test-diff-versions.py` 11 試料・10 変異、`test-build-proposal.py` 28 試料・24 変異が緑
- 関門: 未着手（次は手順 5 の Verifier 1 パス目と `/code-review` 1 パス目）
- 反証と差し戻し: なし
- 交絡: 実験なし
- 割り目（手順 4 の完了時）: 未回答

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 費用の累計を提案書に出すか | 出さない | 版ごとの `feasibility/` は差分の見積りで、合計の決まりが無い。差分の費用だと明記する |
| 置き直し（同じ中身）を「変更」に数えるか | 数えない | 比較で決める。「何を置いたか」は `docs/v<n>/` を見れば分かる |
