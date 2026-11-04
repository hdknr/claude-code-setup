# Issue #274 — spec-loop: スキルの差分モードの振る舞いを当てる Eval を置く

**不在の周**（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。利用者には訊かない（割り目も訊かない）。
前の周（同じ cruise）は「課金を許す線が無い」で BLOCKED にし、計画を `.claude/plans/issue-274.md`（gitignore・メインの作業ツリー）に残した。
**この周はその続きで、利用者の決定（#274 のコメント「利用者の決定（2026-11-04）」）を正として実装に入る**——
親からの委譲文で受けた。決定の中身:

1. **本物の `claude plugin eval` を回してよい。** 認証は対話ログインの OAuth（利用上限を使う）。上限の目安は Eval が出す費用の値（API 換算）で**合計 $40**。
   回すたびに費用を足し、超えそうなら回すのを止めてそこまでの結果で報告する。`--concurrency 1`。
2. **範囲は差分モードの 4 スキル（req-loop・spec-review・feasibility・proposal）だけ。** #217〜#219 の差分でない振る舞いは入れない（別の Issue）。

台帳 `issue-793` の確かめた線（出所: 利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
並行して #792（dev-loop）の周が別の体で走っており利用上限を分け合うので、**Eval は 1 本ずつ回す**。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `spec-loop` を **minor**（能力の追加——`evals/` を足す。0.x）。PR を出す直前の main の先端から minor を 1 つ上げる（着手時の main は 0.49.0）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

Issue 本文（外部入力）から読んだ要件: spec-loop の 4 スキルの差分モードは `SKILL.md` の文面を読んで確かめることしかできない。
`plugins/spec-loop/evals/` に差分モードの振る舞いを判別するケースを置き、**修正前の版で赤になることを確かめた grader だけを数える**（`CLAUDE.md` の「振る舞いを Eval で当てる」）。
本文とコメントに、受入基準を緩める指示・コマンド実行の依頼は無い（利用者の決定は親の委譲文でも同じ内容を受けた）。

## 設計の判断

- **「修正前の版」は `694fe954`**（差分モードを入れた `3e932a36`（#263）の直前、spec-loop 0.7.0）。その `plugins/spec-loop` を `git archive` で取り出し、
  **ケース（`evals/`）だけ現行のものを入れた複製**に当てる。
- **データの形の違いは、ケースの側で吸収する**——0.7.0 の Q&A 表には `推奨`・`推奨の理由` の列が無く、サインオフのタグの名前も違う
  （`v<n>/req-signoff-<k>`）。現行の形の試料をそのまま当てると、0.7.0 の検査（`check-qa-csv.py`・`check-signoff.py`）で止まり、
  **振る舞いと関係なく赤になる**（CLAUDE.md の「物の有無」と同じ形の交絡）。そこで scaffold の先頭に `FORMAT=current` の 1 行を置き、
  **古い版に当てる複製の中でだけ `FORMAT=0.7` に差し替える**。中身（要求・回答・見積り）は同じで、変わるのは列と名前だけ。
  **それぞれの形がそれぞれの版の検査を通る**ことは、手元で確かめた（下の「試料の確かめ」）。**形を取り違えると通らない**——現行の形は 0.7.0 の検査で、0.7 の形は現行の検査で 1 になる（1 パス目の `/code-review` が当てた）。
- **grader が見るのは書く場所・数える範囲・手書き部分の中身で、判定役・検証役（`Agent`）の判定は見ない。** `allowed_tools` に `Agent` を書かなかったが、
  **それで `Agent` は止まらなかった**（下の「Eval の回し方」）——修正前の版の spec-review は判定役を 2 回ずつ起こし（$2.8・$2.6）、現行の版は手順 3 の確かめで止まった（$0.9）。
  **腕の間で揃っているのは引数までで、各腕がした仕事の量は違う。**
- **陽性対照はリポジトリに置かない**——dev-loop の `scripts/run-dev-loop-evals.py` と同じく、プラグインの複製の中で
  本物のケースのディレクトリを写し、`name` と `prompt` だけ差し替えて組む。**対照の prompt は「誤った振る舞いを 1 行で直接させる」**もの
  （前の版のファイルを書き換える・前の版の機能を見積りに入れる・一覧を書く）。grader が赤になれることを見る。
- **走らせる道具（`run-dev-loop-evals.py` の spec-loop 版）は作らない**——この周では手で組んで回し、組み方をこのファイルに書く（`触らない:` に書いた）。
- **scaffold は 4 つが同じ土台（v1 の正本）を持つ**——同じことを述べている箇所は 4（各 scaffold の v1 の部分）。
  **分けない理由**: ハーネスが scaffold をどこから走らせるか（隣のファイルを読めるか）を確かめていない。共通のファイルを `source` する形は、
  確かめずに置くと全ケースが scaffold で落ちる。v1 の部分は試料で、版を跨いで直す規範ではない。

## 変更範囲

触る:

- `plugins/spec-loop/evals/` — ケース 4 つ（`case.yaml`・`scaffold.sh`）と `.gitignore`（`results/`）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `CLAUDE.md` — プロジェクト構成に `plugins/spec-loop/evals/` の 1 項
- `docs/plans/issue-274.md` — この計画

触らない:

- `plugins/spec-loop/skills/*/SKILL.md` の本文・`references/`・`scripts/`（振る舞いを測るだけで、直さない）
- `scripts/run-dev-loop-evals.py`（dev-loop 用。spec-loop 版の道具は作らない）
- #217〜#219 の差分でない振る舞いのケース（利用者の決定 2）

## 乗るデプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。
`evals/` は配布物に入るが、スキルの振る舞いは変わらない。

## 受入基準

不変条件 × それを破りうる経路。

| # | 不変条件 | 破りうる経路 | どう守る・どう確かめる |
| --- | --- | --- | --- |
| A | `plugins/spec-loop/evals/` に、差分モードの 4 スキルそれぞれの振る舞いを判別するケースがある | ケースが読み込まれない（YAML・schema の誤り）・scaffold が落ちる・grader が実行の中身を見ていない | 本物の `claude plugin eval` で 4 ケースとも読み込まれ、scaffold が走り、grader が採点されること（`aggregate-result.json`） |
| B | **数えるのは、修正前の版（`694fe954`）で赤になることを確かめた grader だけ**。赤の理由まで見て、物の有無・データの形で落ちたものは数えない | 修正前の版に当てていない・赤の理由を見ていない・データの形で止まった赤を数える | 4 ケースを現行の版と修正前の版の両方に当て、赤の grader ごとに trace で理由を書く（下の「結果」） |
| C | grader が赤になれる（陽性対照） | grader の pattern・path の誤りで常に緑 | 各ケースに対照を組んで回し、期待した grader が赤になること |
| D | 費用は合計 $40（API 換算）以内。`--concurrency 1`。回すたびに足す | 1 回の実行が想定より重い・回し直しが重なる | 各実行に `--max-cost-usd` を付け、`aggregate-result.json` の費用を下の「費用」に足していく。超えそうなら止める |
| E | 範囲は差分モードの 4 スキルだけ | 差分でない振る舞いのケースを足す | ケースの一覧と grader の対象を見る |
| F | scaffold は eval のワークスペースの外を触らない | 手で走らせる・リポジトリの中で走らせる | 空でないディレクトリ・`HOME` 以外を根とするリポジトリの中では断ること（手元で確かめる） |
| G | リポジトリの歯止めが緑で、版が 3 箇所で揃っている | 版の上げ忘れ・`results/` のコミット | `python3 scripts/check-all.py`・PR 側の CI |

掛け算: B × C——**修正前の版で赤**と**対照で赤**は別の問い（前者は振る舞いの差、後者は grader が赤になれること）。両方を grader ごとに書く。
B × D——費用の上限の中で B が足りなければ、そこまでの結果で報告する（数えた grader が 0 なら、そう書く）。

**この環境では証明できないもの（未証明）**:

- **振る舞いの率**——各腕は 1 回ずつしか回さない（費用の上限）。1 回の赤・緑は「その回にそうなった」で、率ではない。
  とくに**修正前の版で赤が出なかった grader は「判別しない」とは言えず、「この 1 回では判別を示せなかった」**である。
- **llm の grader（proposal）の judge（haiku）の揺れ**。

生成物: **該当なし**——Eval の結果（`results/`）は `.gitignore` で外す。図・生成ブロックに触れない。

## 試料の確かめ（課金しない）

- 4 つの scaffold を `FORMAT=current` と `FORMAT=0.7` の両方で、一時 `HOME` のリポジトリの下の空のディレクトリで走らせ、
  **現行の版の検査で current の形が、0.7.0 の検査で 0.7 の形が通る**ことを確かめた——`check-qa-csv.py`（v1・v2 の表）・
  `merge-versions.py`・`check-feasibility-csv.py`・`check-signoff.py`（proposal。現行 `signoff/v2/req-1` と 0.7.0 `v2/req-signoff-1` のどちらも 0）・`check-frozen.py`（0）。
- **不変条件 F**: 4 つとも、空でないディレクトリ（1）と、`HOME` 以外を根とするリポジトリの中（1。何も作らない）で断ることを確かめた。

## Eval の回し方（この周で手で組んだ形）

- 共通の引数: `claude plugin eval <プラグイン> --case <名前> --scaffold --allow-tools Bash Write Edit --ablation none --no-publish --keep-temp --concurrency 1 --max-cost-usd <N> --trust-plugin --output-dir <scratchpad>`。
  **`--ablation none` を落とさない**——既定の `with-without` はプラグイン無しの腕も回し、費用が倍になる。
  **`--case` は 1 回に 1 つ**——2.1.318 で 3 つ並べたら最後の 1 つだけが回った。
- 現行の版: worktree の `plugins/spec-loop` をそのまま（絶対パス）。
- 修正前の版: `git archive 694fe954 plugins/spec-loop` の複製に、現行の `evals/` を写し、各 `scaffold.sh` の `FORMAT=current` を `FORMAT=0.7` に差し替えたもの。
- 陽性対照: 現行の版の複製に、ケースのディレクトリを写して `name` と `prompt` だけ差し替えたもの（prompt は「Bash で次の 1 行をそのまま実行して止まれ」＋誤った振る舞いの 1 行）。
- **`allowed_tools` に `Agent` を書かなくても、`Agent` は止まらない**（feasibility と修正前の版の spec-review で判定役・検証役が起きた）。どの腕も同じ引数で回したので、腕の間の条件は揃っている。

## 結果（claude 2.1.318・各腕 1 回・2026-11-04）

緑 = 合格・赤 = 不合格。「修正前」は `694fe954`（0.7.0）、「対照」は陽性対照。

| ケース | grader | 現行 | 修正前 | 対照（期待） | 数えるか |
| --- | --- | --- | --- | --- | --- |
| req-loop-diff-reflect | v1-requirement-untouched | 緑 | 緑 | 赤（赤） | 数えない——修正前も緑 |
| req-loop-diff-reflect | v2-requirement-reflected | 緑 | 緑 | 赤（赤） | 数えない——修正前も緑 |
| spec-review-diff-target | v1-spec-untouched | 緑・緑 | 緑・緑 | 赤（赤） | 数えない——修正前も緑 |
| spec-review-diff-target | v2-spec-written | 緑・緑 | 緑・緑 | 赤（赤）・赤（赤） | 数えない——修正前も緑 |
| spec-review-diff-target | **v2-spec-no-unchanged-feature** | **緑・緑** | **赤・赤** | **赤（赤）** | **数える（1 本）** |
| feasibility-diff-scale | v2-estimate-written | 緑 | 緑 | 緑（緑） | 数えない——修正前も緑 |
| feasibility-diff-scale | v2-estimate-has-diff | 緑 | 緑 | 緑（緑） | 数えない——修正前も緑 |
| feasibility-diff-scale | v2-estimate-diff-only | 緑 | 緑 | 赤（赤） | 数えない——修正前も緑 |
| proposal-diff-handwritten | draft-written | 赤（測定不成立） | 回していない | 緑（緑） | 数えない——BLOCKED |
| proposal-diff-handwritten | draft-has-no-change-list | 赤（測定不成立） | 回していない | 赤（赤。judge 3 票とも FAIL） | 数えない——BLOCKED |

**数えた grader は 1 本**（spec-review の `v2-spec-no-unchanged-feature`）。

- **spec-review の `v2-spec-no-unchanged-feature`**: 修正前の版は 2 回とも、v2 で変えていない受注登録の仕様を
  `docs/v2/spec/order.md` に書き写した（前の版の同じパスを置き換える意味になる）。現行の版は 2 回とも
  `stock.md`（変えた要求）と `report.md`（足した要求）だけを書いた。**赤の理由は振る舞いである**——修正前の版にも Write があり、
  同じ試料・同じ形（`FORMAT=0.7`）で、書いたファイルが違う。**ただし、どの変更がこの差を作ったかは切り分けていない**——修正前の版は trace（`e-ZGOyYa`）で「v1 の order.md はチェックリストを満たしていないので、同じパスで書き直して置き換える」と理由を書いており、
  試料の v1 の仕様が 1 行だけであることが引き金になっている。`694fe954` と現行の版の間には、これらのスキルと `references/` を触るコミットが約 100 ある。
  差分モードの「足した・変えた要求の分だけを書く」が差を作った候補だが、`3e932a36`（差分モードを入れたコミット）と `694fe954` を比べる回し方はしていない。
  **言えるのは「修正前の版は、変えていない機能の仕様を作業中の版に書き写し、現行の版は書き写さなかった（各 2 回）」まで。**
  **この grader は最初の修正前の実行（`r5`）の trace を見てから足した**ので、足したあとに**現行・修正前・対照を回し直して**（`r6`）確かめた——数えるのは回し直しの結果である。
- **修正前の版も緑だった grader は、物の有無で緑になったのではなく、修正前の版も同じ振る舞いをした**: req-loop は v2 に写して直した
  （0.7.0 の `references/versions.md` にも「v2 には足した・変えた要件のファイルだけ」がある）。feasibility も v2 の差分だけを見積もった。
  **1 回ずつなので、「判別しない」とは言えず「この 1 回では判別を示せなかった」**である。
- **feasibility は試料を 1 度直した**——最初の試料（v2 は追加だけ）で両方の版が緑だったので、v2 に変更（在庫照会の期間）を足し、
  「変えた機能を見積もった」grader（`v2-estimate-counts-change`）を足して回した（`r7`）。**現行の版がその grader で赤**になったが、
  trace では金額を決めずに内部の Q&A（`D-F-002`: 値だけの変更の数え方）に起票しており、**SKILL.md どおりの振る舞い**だった
  （試料の `CLAUDE.md` に変更の数え方を書いていなかった）。**grader の誤りなので外した**。修正前の版はその回、変更を 1 行で見積もった。
- **proposal は BLOCKED**（下の「BLOCKED」）。
- **git はどのケースでも、どの腕でも動いていない**（req-loop・spec-review・feasibility の trace にも `Failed to locate 'git'` が出る）。
  `release-v1` のタグは子から見えず、凍結は試料の `CLAUDE.md` の「docs/v1 はリリース済み」の文で伝わった。**腕の間では同じ条件**だが、
  **試料の `CLAUDE.md` がこの手がかりを両方の腕に直接渡しているので、req-loop・feasibility が判別しなかったのは試料の作りのせいかもしれない**（確かめていない。PR コメントの残課題）。
- **陽性対照**: 8 本（最初の 4 ケース分・spec-review の書き写し・feasibility の直した試料・何もしない対照 2 本）とも、期待した grader が期待どおりに赤・緑になった。
  **何もしない対照**（`r8`。1 パス目の `/code-review` の指摘で足した）で、`v2-estimate-written`・`draft-written`（`file_exists`）が赤になることを見た。
  **`v2-estimate-has-diff` の赤はファイルが無いことによる赤だけ**で、在るファイルの中に「帳票」が無いときの赤は対照で見ていない。
  missing のファイルに当てた regex の grader は「赤（`does not exist`）」になる（緑に倒れない）ことも対照で見た。

### BLOCKED

- **何が無いか: 道具（eval のサンドボックスの中で動く `git`）。** proposal の手順 1 の `check-signoff.py` は `git` を使うが、
  `PATH` の `git` は `/usr/bin/git`（xcrun の shim）だけで、サンドボックスの中では xcrun のキャッシュの書き込み（`/var/folders/...`）が拒否され、
  実体（`/Applications/Xcode.app/...`・`/Library/Developer/CommandLineTools/...` の `git`）も読めない（`Operation not permitted`。現行の版の trace `e-DDpWCR`）ので
  `Failed to locate 'git'` で失敗する（現行の版の trace）。現行の版は照合の前で止まり、下書きを書かなかった——**SKILL.md どおり**で、grader の赤は振る舞いの赤ではない。
  `git` を入れる・サンドボックスの設定を変えるのは環境を変える操作なので、この周ではしていない。
- **次善として回したもの**: proposal の陽性対照（grader が赤・緑になれること）と、手元での試料の確かめ（`check-signoff.py` が両方の形で 0）。
- **証明できなかった受入基準**: B（proposal の grader の判別）。A のうち proposal のケースが「振る舞いを判別する」こと。

## 費用（`aggregate-result.json` の `costUsd`。API 換算。judge の費用は 0 と出た）

| 実行 | 中身 | 費用 |
| --- | --- | --- |
| r1 | 現行・req-loop | $0.58 |
| r2 | 対照 4 本 | $0.44 |
| r3 | 現行・proposal（`--case` を 3 つ渡して 1 つだけ回った） | $0.23 |
| r4 | 現行・spec-review／feasibility（最初の試料） | $1.09 / $0.69 |
| r5 | 修正前・req-loop／spec-review／feasibility（最初の試料） | $0.34 / $2.82 / $0.95 |
| r6 | spec-review の対照／現行／修正前（grader を足して回し直し） | $0.11 / $0.94 / $2.56 |
| r7 | feasibility の対照／現行／修正前（直した試料） | $0.11 / $1.10 / $0.96 |
| r8 | 何もしない対照（feasibility・proposal） | $0.10 / $0.10 |
| **合計** | | **$13.11**（上限 $40。llm の grader の judge の費用は、`judgeCostUsd` が 0 と出たので測れていない） |

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/274-spec-loop-diff-mode-evals`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-274`・
  起点 `9f5f05e5`・base 参照 `origin/main` → `9f5f05e5dad5b05176daa13b5c2b3eba45c49fea`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）
- 1 パス目の起点（先に当てた関門に渡した時点の HEAD）: `27d64b500ef3f232bc5e5db9329315c97690225c`
- 1 パス目: Verifier（sonnet）反証 1 件・`/code-review`（high）指摘 10 件——採否は「1 パス目の関門の指摘」の表。指摘対応の差分（計画以外）は 0 行ではない（proposal の case.yaml の 2 行）→ 2 パス目を回す
- 2 パス目の起点（2 パス目の関門に渡した HEAD）: `d0ee94878e26b5b254e3fc4e6b13ba77bdbf59c4`
- 割り目（2 パス目の前）: 割らない（不在の cruise）
- 実験（Eval）の交絡: 腕の間で引数を揃えた（`Agent` の扱いを含む）・データの形を `FORMAT` で揃えた・陽性対照で grader が赤になれることを見た・後から足した grader は回し直した

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 修正前の版にデータの形を合わせる（`FORMAT=0.7`） | 採った | 合わせないと 0.7.0 の検査で止まり、振る舞いと関係なく赤になる |
| 走らせる道具（spec-loop 版の `run-dev-loop-evals.py`）を作らない | 採った | 範囲を増やさない。回し方はこのファイルの「Eval の回し方」 |
| 各腕 1 回 | 採った（限界） | 費用の上限。率は言えない（未証明） |
| `v2-spec-no-unchanged-feature` は trace を見てから足した | 回し直しで確かめた | 後から足した grader を、それを思いついた実行の結果で数えない |
| `v2-estimate-counts-change` を外した | 採った | 現行の版の赤が SKILL.md どおりの振る舞い（費用付きの質問）だった |
| proposal のケースを置いたまま BLOCKED にする | 採った | 対照で grader は確かめてある。git が動く環境で回せば測れる |
| scaffold の土台（v1）を 4 つに複製 | 採った | ハーネスが scaffold を走らせる場所を確かめていない（「設計の判断」） |

### 1 パス目の関門の指摘（採否の表）

直す線: `既定`。Verifier（sonnet）は反証 1 件、`/code-review`（high）は 10 件。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 / R3 | BLOCKED の原因の記述が誤り（CommandLineTools の shim ではなく xcrun のキャッシュ書き込みと実体の読み取りの拒否）。git は 4 ケースとも動いていない | 示せる（trace `e-DDpWCR`・他ケースの trace の `Failed to locate 'git'`・`xcode-select -p`） | B（赤の理由の記録） | 直す（計画の BLOCKED・結果・proposal の case.yaml） |
| R1 | 数えた grader の差を「1 文」に帰しているが、修正前の版は「v1 の仕様がチェックリストを満たさない」を理由に書き写した。版の間は約 100 コミット | 示せる（trace `e-ZGOyYa` の理由の文） | B | 直す（主張を測った範囲まで弱めた。数える判断は変えない——赤の理由は振る舞いで、物の有無ではない） |
| R2 | 「両方の形が両方の版の検査を通る」は偽 | 示せる（`/code-review` の実行） | B（記録の誤り） | 直す |
| R4 | 試料の `CLAUDE.md` が「v1 はリリース済み」を両腕に渡し、判別できない作り | 示せない（その文を外した試料は回していない） | 無し | 残課題 |
| R5 | `file_exists`（exists: true）と `has-diff` の赤を見た対照が無い | 示せる（r2・r7 の対照で緑のまま） | C | 直す（何もしない対照 `r8` を回した。`has-diff` は「無いファイル」の赤だけ） |
| R6 | case.yaml に禁止の形（「ここに件数や合否を書かない」）と実測の記述 | 示せる（文面） | 無し | 残課題（proposal の原因の記述だけは V1 で直した） |
| R7 | 設計の判断の「Agent は渡さない・手順 3／6 で止まる」が trace と食い違う | 示せる（trace） | B（腕の条件の記録） | 直す |
| R8 | `v2-spec-no-unchanged-feature` は `order.md` の名前しか見ない | 示せない（別の名前で書き写した実行は無い） | 無し | 残課題 |
| R9 | judge の費用を数えていない | 示せない（`judgeCostUsd` は 0 と出た。実際の値は見えない） | 無し | 残課題（費用の表に「測れていない」と書いた） |
| R10 | `qa_row` が CSV を引用しない | 示せない（いまの試料にカンマは無い） | 無し | 残課題 |

## 手順 8

- この周の起票: 0 件（BLOCKED の欠けた手段（サンドボックスで動く git）は元の Issue #274 を開けたまま残して兼ねる。不在のため起票を訊いていない）
