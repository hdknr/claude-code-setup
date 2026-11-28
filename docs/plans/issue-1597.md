# Issue #1597: profile.csv・ファイルの当たり先・形式の版の欠陥でも、hint がまだ行き止まりの案内を出す

**不在の周（cruise #1604 の子。`/dev-loop:cruise 1604 --absent`）。** 線の出所: 利用者の確認（起動時・2026-11-27T07:31:25Z、配布を見せて確かめた）。
確かめた線: 直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ / 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）/ 実機確認 = 書いていない。
マージは親がする（子は PR を作り、PR 側の CI を見るところまで）。台帳は書かない。

版の上げ方: spec-loop は minor（`ProfileContent` を足す。0.x なので minor）・screen-spec は patch（案内の不具合の修正）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/external-profile.py` — `Undetermined` の下位の `ProfileContent` を足し、`LayerContent` をその下位にする。`read_profile` の中身の欠陥・`read_layer` の `ファイル` の当たり先・形式の版の下限より下と読めない形を `ProfileContent` で投げる
- `plugins/spec-loop/references/external-profile.md` — 決まりの原本に `ProfileContent` を書く
- `plugins/screen-spec/scripts/check-screens.py` — `load_external` が `ProfileContent`（無ければ `LayerContent`）を `LayerRule` にする
- `plugins/screen-spec/scripts/write-screens.py` — `base_initial` が `read_profile` の `ProfileContent` を `LayerBroken`（`profile.csv` の欠陥の言い方）にし、`hint` がそれを言い分ける。docstring
- `plugins/screen-spec/references/profiles.md` — 「読めないとき」と基盤の profile の初期値の節に、言い分ける欠陥を足す
- `scripts/test-external-profile.py` — 例外の種類の観測・変異・試料（形式の版の下限より下・上限と同じ）
- `scripts/test-write-screens.py` — Issue の 3 つの形の試料と変異
- `scripts/test-check-screens.py` — `check-screens.py` の出力が変わらない試料（`profile.csv` の欠陥・`ファイル` の当たり先・形式の版の下限）
- `.claude-plugin/marketplace.json`
- `plugins/spec-loop/.claude-plugin/plugin.json`
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/screen-spec/.claude-plugin/plugin.json`
- `plugins/screen-spec/skills/*/SKILL.md` — 版の 2 行。`init` は hint の新しい行（`profile.csv が決まりに合わない`）の手当ても足す（1 パス目の CR1-1 で広げた——スキルが hint を読む入口なので、そこが行き止まりだと不変条件 1 が破れる）
- `docs/plans/issue-1597.md`

触らない:

- clone・タグの不在・`profile.csv` がその時点に無い（profile の名前かタグが違う）・形式の版が上限と同じか上（screen-spec を上げれば読める）の文言と例外の種類——Issue が「変えない」と決めている
- platform-spec のスクリプト（`Undetermined` で捕まえていて、下位の `ProfileContent` もそのまま捕まえる）
- 画面の層の `重ねる先` が `settings.csv` の `profile` と食い違うときの `Stop`（Issue の範囲の外。`hint`・引数なしの `init` では `重ねる先` から `profile` を決めるので起きない）

依存の追加・更新: なし
仕様の振る舞い: 該当なし（spec-loop の正本ではない）

## 方針

- spec-loop に `Undetermined` の下位の **`ProfileContent`**（タグの時点の profile の中身が決まりに合わない——同じタグを名指し直しても止まる）を足し、`LayerContent` をその下位にする。
  `ProfileContent` で投げるのは: `profile.csv` の UTF-8・CSV・見出し・列の数・空の層・同じ層が 2 行、層の `ファイル` が profile の外を指す・どのファイルにも当たらない、
  形式の版が読めない形（`1a`・全角の数字）・下限より下。**上限と同じか上の版は `Undetermined` のまま**（使う側を上げれば読める）。文言はどれも変えない。
  下位なので、`Undetermined` で捕まえている使う側（platform-spec・`check` と `diff` の終了コード 4）は変わらない。
- screen-spec の `load_external` は `ProfileContent`（0.138 の spec-loop なら `LayerContent`、もっと古ければ何も）を `LayerRule` にする。文言は「を読めない: …」のまま（`check-screens.py` の出力は変わらない）。
  `ファイル` の当たり先と形式の版は、`hint`・引数なしの `init` では `load_external` を通るので、既存の `LayerRule` → `LayerBroken` の経路に乗る。
- `write-screens.py` の `base_initial` は `read_profile` を直に呼ぶので、そこで `ProfileContent` を捕まえて `LayerBroken` にする。
  `重ねる先` が読めないので、案内の `--profile` には `<画面の profile>` を書き、`hint` の言い方は「profile.csv が決まりに合わない」にする（画面の層の欠陥の言い方は変えない）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | 基盤の profile の `profile.csv` の中身の欠陥（同じ層が 2 行・見出し・UTF-8）で、`hint` が「明示して渡す」だけの案内を出さず、直してタグを付け直すか `--external なし` を案内する | `hint` | `ProfileContent` → `base_initial` の `LayerBroken` | `test-write-screens.py` の `base-profile-dup-layer`・`base-profile-bad-head` |
| 2 | 同じ状態で、引数なしの `init` も同じ案内で 4、何も書かない。同じ外部の profile を明示した `init` は 4 | `init`（引数なし・明示） | 同上・`load_external` の `LayerRule` | 同上 |
| 3 | 画面の層の `ファイル` がどのファイルにも当たらない・profile の外を指すとき、`hint` と引数なしの `init` が 1・2 と同じ案内を出す | `hint`・`init` | `ProfileContent` → `LayerRule` → `LayerBroken` | `base-screen-file-missing`・`base-screen-file-outside` |
| 4 | 画面の層の形式の版が下限より下（`0.9`）・読めない形（`1a`・全角）のとき、同じ案内を出す | `hint`・`init` | 同上 | `base-screen-version-low`・`base-screen-version-unreadable`・`base-screen-version-wide-digit` |
| 5 | 案内どおり `--profile web-spa --external なし` を渡すと `init` が 0 で書け、検査が 0（陽性対照） | `init --external なし` | 既存 | 1・3・4 の試料の最後の手順 |
| 6 | clone・タグの不在・形式の版が上限と同じか上・`profile.csv` がその時点に無いなら、今の文言（「読めない（…）——… 明示して渡す」）を変えない | `hint`・`init` | それらで `ProfileContent` を投げない | `base-no-clone`・`base-tag-missing`・`base-screen-layer-version-out-of-range`・`base-profile-missing`（足す）、`test-external-profile.py` の例外の種類の観測 |
| 7 | `check-screens.py` の出力（終了コード 4 と文言）は変わらない | `check-screens.py` | `LayerRule` は `Stop` の下位で文言は同じ | `test-check-screens.py` の足す試料（4 と「を読めない: …」） |
| 8 | spec-loop の `check`・`diff` と platform-spec の使う側の結果は変わらない（下位クラス） | `external-profile.py`・platform-spec | 下位クラス | `test-external-profile.py`（`bad-*` が 4）・platform-spec のテスト |
| 9 | spec-loop の例外の種類: 上の欠陥はどれも `ProfileContent`、層のファイルの中身は `LayerContent`（`ProfileContent` の下位）のまま、6 のものは素の `Undetermined` | `read_profile`・`read_layer` | 投げる所を全部変える | `test-external-profile.py` の観測（試料を足す） |
| 10 | `init` スキルが hint の `基盤の profile:` の行の言い方（読めない・画面の層・`profile.csv`）ごとに手当てを書き、`profile.csv` の行の `<画面の profile>` を利用者に選ばせる（1 パス目の CR1-1 で足した） | `init` スキル | 本文 | `test-write-screens.py` の `skill_problems`（崩すと落ちる対照つき） |

- 未証明: なし。BLOCKED: なし。
- 生成物: なし（`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけで、触らない。`check-all.py` が見る）。
- プロパティテスト: なし（入力は例外の種類の分類で、境界は下限・上限の 2 点——試料で両側を当てる）。
- 差分テスト: なし（振る舞いを変える周）。
- 複製の数: 決まりの記述は spec-loop の docstring と `references/external-profile.md`、screen-spec の `check-screens.py`・`write-screens.py` の docstring と `references/profiles.md` の 5 箇所（#1589 と同じ）。
  分けないのは、どれも同じ 1 つの言い分けを指していて、片方だけ入れると言い分けが働かないから。
- 直す線: 既定（出所: cruise の確かめた線）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1597-profile-content-hint`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1597`・
  起点 `0c824eac`・base の参照 `origin/main`・base の SHA `0c824eace80033e869325f8fd757fb58bc766376`
- 実装: `853d5585`（`check-all.py` 緑。新しい試料 7 件は base の本体で赤——`test-write-screens.py` を base の木に当てて確かめた。`base-profile-missing` は base でも緑＝変えない側）
- 割り目（手順 4 の実装の後）: 割らない（cruise の周）。
- 1 パス目: 起点（1 パス目の指摘対応の起点）`853d5585`。2026-11-27 08:53Z に両方の関門を起こした。
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1597-verifier-1-20261127T085317Z.md`
  - Verifier の結果: 反証 0 件（終点 `853d5585`）
  - `/code-review`（high）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1597-code-review-1-20261127T085317Z.md`
    ——指摘 5 件（終点 `853d5585`。採否は下の表——直す 3・残課題 2）
- 1 パス目の指摘対応: `93d3cbec`（成果物の差分は 0 行でない——2 パス目を回す。`check-all.py` 緑）
- 2 つ目の割り目: 割らない（cruise の周）。残っているのは手順 5 の当て直し（Verifier 2 パス目）と手順 6 の 2 パス目の両方。
- 2 パス目: 狭いパスの起点（2 パス目の指摘対応を始める直前）`93d3cbec`。2026-11-27 10:07Z に両方の関門を起こした。
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1597-verifier-2-20261127T100754Z.md`——反証 0 件（終点 `93d3cbec`。外の複製で変異「タグが無いのも ProfileContent にする」と `skill_problems` の崩しを当てて赤を確かめた。run-serial の枠待ちが長く、test-external-profile.py を枠の外で回した——逸脱を自己申告）
  - `/code-review`（high）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1597-code-review-2-20261127T100754Z.md`——指摘 6 件（終点 `93d3cbec`。直す 1（CR2-2）・残課題 5）
- 2 パス目の指摘対応: CR2-2 だけ（テストだけ）。`4e9e3527`（`check-all.py` 緑）
- 狭いパス: 起点 `93d3cbec`・終点 `4e9e3527`。Verifier（`dev-loop:dev-loop-verifier`・sonnet）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/79aa671c-cc1b-41b2-8987-813115883552/scratchpad/gate-1597-narrow-1-20261127T104233Z.md`——反証 0 件。独立の変異 7 件のうち 6 件が赤、1 件が素通り（手当ての文を縮め、無関係な行に `<画面の profile>` と「利用者に選ばせる」を置く——同じ行に両方が在るかだけを見るので通る。陽性対照: 手当ての文は実際に消えている）
- PR: #1623。PR 側の CI: 20 pass・1 skipping（`deploy`）。外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い——`external-reviews.py` が 3）。
- マージの直前の取り込み（2026-11-28）: 取り込む前の先端 `82a7bd4e`・取り込んだ main `904ebcd9`（#1615・#1616）。git の衝突なし、同じ名前のぶつかりなし（main が足した名前は `formal-baseline.py` とそのテストの中だけ）。版を main の先端から上げ直した——spec-loop `0.139.0` → `0.140.0`（minor）・screen-spec は main が `0.12.4` のままなので `0.12.5`（patch）で据え置き。`ProfileContent` が入る spec-loop の版が `0.140.0` になったので、既知の限界の「0.138 以前」を「0.139 以前」に直した。関門はやり直していない。

## 既知の限界・決着済みの論点

- screen-spec の対応する spec-loop の版の範囲は変えていないので、`ProfileContent` を持たない spec-loop（0.139 以前）と組むと、ここで言い分けた欠陥は今までどおり「読めない——明示して渡す」と出る（#1589 の `LayerContent` と同じ扱い）。
- `profile.csv` がその時点に無い（profile の名前かタグが違う）のは、設定か `--external` の名前・タグを変えれば進む余地があるので `Undetermined` のまま（Issue の範囲の外）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1: Verifier 1 パス目——反証 0 件（独立の変異は当てていない。テストを run-serial 越しに回した） | — | — | — |
| CR1-1: `init` スキルが hint の新しい行（`profile.csv が決まりに合わない`）の手当てを書いていない・`<画面の profile>` を名指しと読む | 示せる——`plugins/screen-spec/skills/init/SKILL.md` の 54〜57 行が `読めない` と `画面の層が決まりに合わない` の 2 つだけを挙げる | 1（hint を読むスキルの入口で行き止まりが残る） | 直す（SKILL.md に行と選ばせ方を足し、不変条件 10 と `skill_problems` を足した。範囲は `plugins/screen-spec/skills/*/SKILL.md` の中） |
| CR1-2: タグが無い・`profile.csv` が無いを `ProfileContent` にする変異が、どのテストでも素通りする | 示せる（関門が外の複製で当てた——`test-external-profile.py` rc=0、`base-tag-missing` も緑） | 6・9 の証明 | 直す（`base-tag-missing` に hint の 2 行、`test-external-profile.py` に不在 3 種の例外の観測と、`守る` の行と変異「タグが無いのも ProfileContent にする」） |
| CR1-3: `profile.csv` の列の数・空の層・CSV として読めないの試料が無く、`Undetermined` に戻す変異が素通りする。screen-spec に UTF-8 の試料が無い | 示せる（関門が当てた——`test-external-profile.py` rc=0） | 9・1 の証明 | 直す（`bad-profile-cols`・`bad-profile-empty-layer`・`bad-profile-csv`、`base-profile-utf8`） |
| CR1-4: 画面の層を持たない profile でも、`profile.csv` の欠陥で外部の profile の付け直しを案内する | 示せない——案内の 3 つの道はどれも進める（`--external なし` で書ける、直してタグを付ければ読める）。画面の層が無いことは `profile.csv` を読めない限り分からない | 無し | 残課題（文言の改善） |
| CR1-5: 形式の版が上限と同じか上のとき、hint が screen-spec を上げる道を出さない | 示せる（hint の文言） | 無し——Issue が「上限より上の版の文言は変えない」と決めている | 残課題 |
| V2: Verifier 2 パス目——反証 0 件 | — | — | — |
| CR2-1: `profile.csv` の欠陥の案内が、設定のリポジトリに `/` が無い・profile の名前に空白があるとき、`--external` に渡せない値（`"guide org <新しいタグ>"`・`"org/guide my org <新しいタグ>"`）を明示の道に載せる | 示せる（関門が外の複製で hint を走らせた） | 無し——不変条件 1 は「直してタグを付け直すか `--external なし` を案内する」で、その 2 つの道は進める。載る値が写せないのは、設定がふつうに作られない形（`<持ち主>/<名前>` でないリポジトリ・空白を含む profile）のときだけ | 残課題 |
| CR2-2: 不変条件 10 の後半（`<画面の profile>` を利用者に選ばせる）を `skill_problems` が見ていない——その文を消しても `[]` | 示せる（関門が当てた） | 10 の証明 | 直す（`skill_problems` が本体の `PROFILE_UNKNOWN` をスキルが名指して「利用者に選ばせる」かを見る。文を消すと落ちる対照つき） |
| CR2-3: 案内のコマンドの形に `--profile <画面の profile>` を書くので、そのままシェルに貼ると `<` がリダイレクトになる | 示せる（置き場所の文字のまま貼った場合） | 無し——案内の置き場所の文字は #1590 の `<新しいタグ>` と同じ書き方で、置き換えて渡すもの | 残課題 |
| CR2-4: `references/external-profile.md` の「`profile.csv`」の節が、形式の版の欠陥を profile.csv のどの行でも 4 と読める書き方——実際は求めた層の行だけを見る | 示せる（原本の文と `bad-version` の画面の層が「読めた」） | 無し（原本の文言） | 残課題 |
| CR2-5（既存）: 基盤の profile の `重ねる先` がこのプラグインに無い profile のとき、hint は「明示して渡す」とだけ案内し、同じ外部の profile を明示しても止まる | 示せる（`base-overlay-unknown` の形） | 無し——この周の範囲（Issue の 3 つの欠陥）の外 | 残課題 |
| CR2-6（既存）: `references/profiles.md` の 129 行が「上の『読めないとき』」と書くが、節は下にある | 示せる | 無し | 残課題 |
| N1: 狭いパス——反証 0 件。素通りの変異 1 件（無関係な行に名指しと「利用者に選ばせる」を置くと `skill_problems` が通る） | 示せる（関門が当てた） | 無し（試料の穴。わざと壊すときだけ） | 人間が決める（振り分けは記録だけ） |

- 効いた行の当てられない指摘: CR1-4・CR1-5・CR2-3 は関門が「該当なし」と返した（どの項にも当てない）。

## 手順 8

- この周の起票: 0 件（不在の周で、周の途中の課題 = 外に出す。振り分けの直すの行 1 件は PR コメントの起票の候補に書いた——起票は親か利用者が決める）
- 効いた行: R-02（CR1-1 の init スキルの手当て・CR2-1 の写せない値・CR2-4 の原本の書き方・CR2-5 の重ねる先・CR2-6 の向き——記述と事実を照らした）
- 効いた行: R-01（CR1-2・CR1-3・CR2-2——証明が主張を判別しているか）
- 効いた行: R-04（CR1-2・CR1-3・CR2-2——テストの主張を外の複製で当てて、変異が素通りすると示した）

### 振り分け（周の途中の課題 = 外に出す。`references/found-lines.md`）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け | 後退を示すか |
| --- | --- | --- | --- | --- |
| 基盤の profile の `重ねる先` がこのプラグインに無い profile のとき、hint が「明示して渡す」とだけ案内し、同じ外部の profile を明示しても止まる | #1597 /code-review 2 パス目（CR2-5） | 示せる（`base-overlay-unknown` の形） | 直す（起票の候補）——利用者に見える誤り（#1597 と同じ型の行き止まりの案内。重ねる先が手元の screen-spec より新しい profile を名指すときに起きる）。仕様の穴でない | 示さない（既存） |
| `profile.csv` の欠陥の案内に、設定が `<持ち主>/<名前>` でない・profile に空白のとき `--external` に渡せない値が載る | #1597 /code-review 2 パス目（CR2-1） | 示せる（関門が hint を走らせた） | 記録だけ——ふつうには作られない設定の形（platform-spec の設定の形の違反） | 示さない——前も今も `--external なし` の道は進め、前の「明示して渡す」も同じ設定では写せない値しか渡せなかった |
| 画面の層を持たない profile でも、`profile.csv` の欠陥で外部の profile の付け直しを案内する | #1597 /code-review 1 パス目（CR1-4） | 示せない | 記録だけ | 示さない |
| 形式の版が上限と同じか上のとき、hint が screen-spec を上げる道を出さない | #1597 /code-review 1 パス目（CR1-5） | 示せる（文言） | 記録だけ——Issue が文言を変えないと決めている | 示さない（文言は変えていない） |
| 案内のコマンドの形の `<画面の profile>` をそのままシェルに貼ると `<` がリダイレクトになる | #1597 /code-review 2 パス目（CR2-3） | 示せる | 記録だけ——置き場所の文字（#1590 の `<新しいタグ>` と同じ書き方） | 示さない |
| `references/external-profile.md` の形式の版の欠陥の書き方が、profile.csv のどの行でも 4 と読める | #1597 /code-review 2 パス目（CR2-4） | 示せる（原本の文） | 記録だけ——文言 | 示さない |
| `references/profiles.md` の 129 行の「上の『読めないとき』」の向き | #1597 /code-review 2 パス目（CR2-6） | 示せる | 記録だけ——文言（既存） | 示さない |
| `skill_problems` が、無関係な行に名指しと「利用者に選ばせる」を置く変異を素通りさせる | #1597 狭いパス | 示せる（関門が当てた） | 記録だけ——試料の穴 | 示さない |

## 関門の記録

```dev-loop-gates
周の base: 0c824eace80033e869325f8fd757fb58bc766376
関門: Verifier 1 853d5585 反証=0
関門: /code-review 1 853d5585 指摘=5
関門: Verifier 2 93d3cbec 反証=0
関門: /code-review 2 93d3cbec 指摘=6
関門: 狭いパス 93d3cbec 4e9e3527 反証=0
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
受入基準: 8 満たす
受入基準: 9 満たす
受入基準: 10 満たす
マージの反映: ドキュメントとプラグインの配布
```
