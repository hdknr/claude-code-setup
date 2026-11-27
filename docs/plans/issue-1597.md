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
- `plugins/screen-spec/skills/*/SKILL.md` — 版の 2 行
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

## 既知の限界・決着済みの論点

- screen-spec の対応する spec-loop の版の範囲は変えていないので、`ProfileContent` を持たない spec-loop（0.138 以前）と組むと、ここで言い分けた欠陥は今までどおり「読めない——明示して渡す」と出る（#1589 の `LayerContent` と同じ扱い）。
- `profile.csv` がその時点に無い（profile の名前かタグが違う）のは、設定か `--external` の名前・タグを変えれば進む余地があるので `Undetermined` のまま（Issue の範囲の外）。

## 手順 8

- この周の起票: 0 件（不在の周。起票の候補は親が振り分けの直すの行から決める——この時点で直すの行は無い）
