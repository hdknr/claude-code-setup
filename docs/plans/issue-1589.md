# Issue #1589: 層のファイルの中身が壊れているとき、hint がまだ行き止まりの案内を出す

## 変更範囲

触る:

- `plugins/spec-loop/scripts/external-profile.py` — `read_layer` が層のファイルの中身の欠陥を `LayerContent`（`Undetermined` の下位）で投げる
- `plugins/spec-loop/references/external-profile.md` — 決まりの原本に `LayerContent` を書く
- `plugins/screen-spec/scripts/check-screens.py` — `load_external` が `LayerContent` を `LayerRule` にする
- `plugins/screen-spec/scripts/write-screens.py` — docstring（言い分けに #1589 を含める）
- `plugins/screen-spec/references/profiles.md` — 「読めないとき」の 3 つ目に層のファイルの中身の欠陥を数える
- `scripts/test-external-profile.py` — 例外の種類の観測・変異 1 件・試料（UTF-8・CSV として読めない層のファイル、UTF-8 でない `profile.csv`）
- `scripts/test-check-screens.py` — 層のファイルの ID が重なった外部の profile の試料（`ext-layer-dup-id`。1 パス目の CR1-2 で広げた——不変条件 5 の証明を判別させるため）
- `scripts/test-write-screens.py` — Issue の再現（`L-STD` が 2 行）の試料と `check-screens.py` の変異 1 件
- `.claude-plugin/marketplace.json`
- `plugins/spec-loop/.claude-plugin/plugin.json`
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/screen-spec/.claude-plugin/plugin.json`
- `plugins/screen-spec/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1589.md`

触らない:

- `profile.csv` の中身の欠陥（見出し・同じ層が 2 行）・形式の版の範囲・`ファイル` の当たり先——今までどおり「読めない」（Issue は層のファイルの中身に絞っている。残課題に書く）
- platform-spec のスクリプト（`Undetermined` で捕まえていて、下位の `LayerContent` もそのまま捕まえる）

依存の追加・更新: なし
仕様の振る舞い: 該当なし（spec-loop の正本ではない）

## 方針

- spec-loop の `read_layer` は、clone・タグの不在も層のファイルの中身の欠陥も同じ `Undetermined` で投げていたので、screen-spec の側では文言でしか分けられなかった。
  **`Undetermined` の下位の `LayerContent`** を足し、層のファイル（`matched` の各ファイル）の UTF-8・CSV・先頭 3 列・見出しの重なり・列の数・空の ID・重なった ID だけをそれで投げる。
  下位なので、`Undetermined` で捕まえている使う側（platform-spec・`check` の終了コード 4）は変わらない。
- screen-spec の `load_external` は `getattr(ext, "LayerContent", ())` を先に捕まえ、`LayerRule`（#1582）にする。文言は今までの「を読めない: …」のまま（`check-screens.py` の出力は変わらない）。
  `LayerContent` を持たない古い spec-loop では今までどおり「読めない」に落ちる（screen-spec の対応する spec-loop の版の範囲は変えない）。
- `write-screens.py` の `hint`・引数なしの `init` は `LayerRule` → `LayerBroken` の既存の経路に乗る——コードは変えない。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | 層の行の ID が重複した profile を名指す基盤の設定で、`hint` が「明示して渡す」だけの案内を出さない | `hint` | `LayerContent` → `LayerRule` → `LayerBroken` | `test-write-screens.py` の `base-layer-dup-id` |
| 2 | 同じ状態で、引数なしの `init` も行き止まりの案内を出さず 4 で何も書かない | `init`（引数なし） | 同上 | 同上 |
| 3 | 案内どおり `--profile web-spa --external なし` を渡すと `init` が 0 で書け、検査が 0（陽性対照） | `init --external なし` | 既存 | 同上 |
| 4 | 読めない理由が clone・タグの不在・形式の版・`profile.csv`・`ファイル` の当たり先なら、今の文言（「読めない（…）——… 明示して渡す」）を変えない | `hint`・`init`・`check-screens.py` | `LayerContent` はそれらで投げない | `test-write-screens.py` の `base-no-clone`・`base-tag-missing`・`base-screen-layer-version-out-of-range`、`test-external-profile.py` の例外の種類の観測 |
| 5 | `check-screens.py` の出力（終了コード 4 と文言）は変わらない | `check-screens.py` | `LayerRule` は `Stop` の下位で文言を同じにする | `test-check-screens.py` の `ext-layer-dup-id`（4 と「を読めない: 層 画面 に ID L-STD が 2 行ある」）。`LayerRule` になったこと自体は `test-write-screens.py` の `base-layer-dup-id` と `CHECK_MUTATIONS` が見る |
| 6 | spec-loop の `check`・platform-spec の使う側の結果は変わらない（下位クラス） | `external-profile.py check`・platform-spec | 下位クラス | `test-external-profile.py`（`bad-*` が 4）・platform-spec のテスト |
| 7 | 層のファイルの中身の欠陥（UTF-8・CSV・先頭 3 列・見出しの重なり・列の数・空の ID・重なった ID）はどれも `LayerContent` | `read_layer` | 投げる所を全部変える | `test-external-profile.py` の観測（`bad-layer-utf8`・`bad-layer-csv` を足し、`bad-profile-utf8` を LayerContent にしない対照にした） |

- 未証明: なし。BLOCKED: なし。
- 生成物: なし（`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけで、触らない。`check-all.py` が見る）。
- プロパティテスト: なし（入力は例外の種類の分類で、境界の空間が広くない——試料で全種類を当てる）。
- 差分テスト: なし（振る舞いを変える周）。
- 複製の数: 決まりの記述は spec-loop の docstring と `references/external-profile.md`、screen-spec の `check-screens.py`・`write-screens.py` の docstring と `references/profiles.md` の 5 箇所。
  分けないのは、どれも同じ 1 つの言い分けを指していて、片方だけ入れると言い分けが働かないから。
- 直す線: 既定（出所: 既定。`.claude/dev-loop.md` が無い）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1589-layer-content-hint`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1589`・
  起点 `1af47399`・base の参照 `origin/main`・base の SHA `1af473994d1a756440930ed38efb97ab881e1115`
- 割り目（手順 4 の実装の後）: `AskUserQuestion` を出さずに続けた（落とした。PR コメントにも書く）。
- 1 パス目: 起点（1 パス目の指摘対応の起点）`13ac5f88`。2026-11-27 00:48Z に両方の関門を起こした。
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/69c7988b-77c3-4f6a-8314-0eee7850d61c/scratchpad/gate-1589-verifier-1-20261127T004821Z.md`——反証 0 件（終点 `13ac5f88`）
  - `/code-review`（high）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/69c7988b-77c3-4f6a-8314-0eee7850d61c/scratchpad/gate-1589-code-review-1-20261127T004821Z.md`——指摘 7 件（終点 `13ac5f88`。採否は下の表——直す 4・残課題 3）
- 1 パス目の指摘対応: `edfae398`（成果物の差分は 0 行でない——2 パス目を回す）
- 2 つ目の割り目: `AskUserQuestion` で訊いた（2026-11-27）が 300 秒で答えが無く、続けた
- 2 パス目: 狭いパスの起点（2 パス目の指摘対応を始める直前）`edfae398`
  - Verifier（sonnet）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/69c7988b-77c3-4f6a-8314-0eee7850d61c/scratchpad/gate-1589-verifier-2-20261127T013139Z.md`——反証 0 件（終点 `edfae398`）
  - `/code-review`（high）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/69c7988b-77c3-4f6a-8314-0eee7850d61c/scratchpad/gate-1589-code-review-2-20261127T013139Z.md`——指摘 5 件（終点 `edfae398`。直す 3（どれも計画ファイルだけ）・残課題 2）
- 狭いパス: 該当なし——2 パス目で直したのは計画ファイルだけで、成果物の差分は 0 行（`git diff edfae398 -- ':(top)' ':(top,exclude)docs/plans/issue-1589.md'` が空）

## 既知の限界・決着済みの論点

- `profile.csv` の中身の欠陥（見出し・同じ層が 2 行・UTF-8 でない）と、層の `ファイル` の当たり先（タグの時点でどのファイルにも当たらない・profile の外を指す）も、
  同じタグを名指し直せば止まるので同じ型の行き止まりが残る（`/code-review` 1 パス目 CR1-3 で `ファイル` の当たり先を足した）。Issue の範囲（層のファイルの中身）の外として残課題にする。
  形式の版が上限より上なのは、screen-spec を上げれば直るので行き止まりではない。下限より下の版と読めない版（`1a`・全角の数字）は profile の欠陥で、
  screen-spec を上げても直らない——これも同じ型の行き止まりとして残課題に入れる（`/code-review` 2 パス目 CR2-3 で理由を狭めた）。
- screen-spec の対応する spec-loop の版の範囲は変えていないので、`LayerContent` を持たない spec-loop（0.137.0 以前）と組むと、層のファイルの中身の欠陥でも今までどおり「読めない——明示して渡す」と出る
  （`check-screens.py` の docstring だけがそれを書く。`profiles.md`・`write-screens.py` の docstring は条件を書いていない——CR2-4。残課題）。
- `check-screens.py` の `LayerRule` の文言は「を読めない: …」のままで、`hint` の行は「画面の層が決まりに合わない（… を読めない: 層 画面 に ID L-STD が 2 行ある …）」と出る。
  `check-screens.py` の出力を変えないことを優先した（#1582 の `LayerRule` の「終了コードと文言は `Stop` と同じ」）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1: Verifier 1 パス目——反証 0 件（独立の変異は当てていない） | — | — | — |
| CR1-1: UTF-8 でない `profile.csv` の試料が無く、`_csv_rows` の既定を `LayerContent` にする変異が生き残る | 示せる——`BAD` に UTF-8 でない `profile.csv` の試料が無い（`scripts/test-external-profile.py` の `BAD`） | 4・7 の証明（「LayerContent にしない」の観測が判別しない） | 直す（`bad-profile-utf8`） |
| CR1-2: `test-check-screens.py` に層のファイルの中身の欠陥の試料が無く、不変条件 5 の証明が判別しない | 示せる——`ext-*` の試料に ID の重複・列の数・UTF-8 の層が無い | 5 の証明 | 直す（`ext-layer-dup-id`。4 と文言を見る） |
| CR1-3: 既知の限界が `ファイル` の当たり先の行き止まりを挙げていない | 示せる——計画の既知の限界の節 | 無し（記録） | 残課題（計画の既知の限界と PR コメントに書いた。計画ファイルは成果物ではない） |
| CR1-4: 層のファイルの `csv.Error` の経路の試料が無い | 示せる——`BAD` に CSV として読めない層のファイルが無い | 7 の証明 | 直す（`bad-layer-csv`。欄の上限を超える） |
| CR1-5: `bad-layer-utf8` の `check` の終了コード 4 を表明していない | 示せる——「表の形が違う … は 4」の一覧に無い | 6 の証明 | 直す（一覧に新しい 3 試料を足した） |
| CR1-6: 例外の種類のラベルが素の `Undetermined` にも「（Undetermined の下位）」を付ける | 示せる——`o['read_layer bad-version']` の表示 | 無し（表示。判定は `LayerContent` の有無で判別している） | 残課題 |
| CR1-7（既存）: `profiles.md` の「上の『読めないとき』」は下にある | 示せる——`references/profiles.md` の節の順 | 無し | 残課題 |
| V2: Verifier 2 パス目——反証 0 件（独立の変異 10 件。M8・M9 は不変条件 5 に対して等価で、`test-write-screens.py` が殺す） | — | — | — |
| CR2-1: 計画の「触る」に `scripts/test-check-screens.py` が無く、`check-plan-scope.py` が 1（CI が赤） | 示せる——`python3 scripts/check-plan-scope.py 1af47399… --plan docs/plans/issue-1589.md` が rc=1・`変更範囲の外に出ているファイル: scripts/test-check-screens.py` | 無し（計画ファイルの記録。CI を通すために直す） | 直す（計画ファイルだけ） |
| CR2-2: `test-external-profile.py` に形式の版が範囲の外の試料が無く、その経路を `LayerContent` にする変異が spec-loop のテストでは生き残る | 示せる（関門が当てた） | 無し——不変条件 4 の版の経路の証明は `test-write-screens.py` の `base-screen-layer-version-out-of-range`（関門がそちらで殺せることも確かめた） | 残課題 |
| CR2-3: 既知の限界の理由「形式の版は screen-spec を上げれば直る」は上限より上だけに成り立つ | 示せる——`bad-version`・`bad-wide-digit` | 無し（記録） | 直す（計画ファイルの既知の限界の理由を狭めた） |
| CR2-4: `profiles.md`・`write-screens.py` の docstring が spec-loop 0.138.0 以上の条件を書いていない | 示せる——関門が spec-loop を base の版に戻して観測 | 無し | 残課題（既知の限界に書いた） |
| CR2-5: 受入基準の証明の列が 1 パス目の指摘対応の後の形に揃っていない | 示せる——表の 5・7 の行 | 無し（記録） | 直す（計画ファイルだけ） |

## 手順 8

- この周の起票: 1 件（#1597。`profile.csv`・`ファイル` の当たり先・形式の版の下限と読めない版の行き止まり。手順 8 で利用者が承認した）

## 関門の記録

```dev-loop-gates
周の base: 1af473994d1a756440930ed38efb97ab881e1115
関門: Verifier 1 13ac5f88 反証=0
関門: /code-review 1 13ac5f88 指摘=7
関門: Verifier 2 edfae398 反証=0
関門: /code-review 2 edfae398 指摘=5
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
マージの反映: ドキュメントとプラグインの配布
```
