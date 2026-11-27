# Issue #1589: 層のファイルの中身が壊れているとき、hint がまだ行き止まりの案内を出す

## 変更範囲

触る:

- `plugins/spec-loop/scripts/external-profile.py` — `read_layer` が層のファイルの中身の欠陥を `LayerContent`（`Undetermined` の下位）で投げる
- `plugins/spec-loop/references/external-profile.md` — 決まりの原本に `LayerContent` を書く
- `plugins/screen-spec/scripts/check-screens.py` — `load_external` が `LayerContent` を `LayerRule` にする
- `plugins/screen-spec/scripts/write-screens.py` — docstring（言い分けに #1589 を含める）
- `plugins/screen-spec/references/profiles.md` — 「読めないとき」の 3 つ目に層のファイルの中身の欠陥を数える
- `scripts/test-external-profile.py` — 例外の種類の観測・変異 1 件・UTF-8 でない層のファイルの試料
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
| 5 | `check-screens.py` の出力（終了コード 4 と文言）は変わらない | `check-screens.py` | `LayerRule` は `Stop` の下位で文言を同じにする | `test-check-screens.py` を回して緑 |
| 6 | spec-loop の `check`・platform-spec の使う側の結果は変わらない（下位クラス） | `external-profile.py check`・platform-spec | 下位クラス | `test-external-profile.py`（`bad-*` が 4）・platform-spec のテスト |
| 7 | 層のファイルの中身の欠陥（UTF-8・CSV・先頭 3 列・見出しの重なり・列の数・空の ID・重なった ID）はどれも `LayerContent` | `read_layer` | 投げる所を全部変える | `test-external-profile.py` の観測（`bad-layer-utf8` を足した） |

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
- 割り目: 利用者は周を通して回すよう依頼している（`/dev-loop:dev-loop 1589` を 1 回）。

## 既知の限界・決着済みの論点

- `profile.csv` の中身の欠陥（見出し・同じ層が 2 行）も、同じタグを名指し直せば止まるので同じ型の行き止まりが残る。Issue の範囲（層のファイル）の外として残課題にする。
- `check-screens.py` の `LayerRule` の文言は「を読めない: …」のままで、`hint` の行は「画面の層が決まりに合わない（… を読めない: 層 画面 に ID L-STD が 2 行ある …）」と出る。
  `check-screens.py` の出力を変えないことを優先した（#1582 の `LayerRule` の「終了コードと文言は `Stop` と同じ」）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |

## 手順 8

- この周の起票: 0 件（残課題の `profile.csv` の中身の欠陥は PR コメントに残す。起票は手順 8 で人間に訊く）
