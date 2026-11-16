# screen-spec

画面設計書を [spec-loop](../spec-loop/README.md) とは別に持つプラグインです（計画は [#1081](https://github.com/hdknr/claude-code-setup/issues/1081)）。
画面の仕様を、表（画面・項目・遷移の 3 つの CSV）と散文の仕様書の組み合わせで持ち、表を spec-loop の版の重ね方で重ねた全体に検査を当てます。

screen-spec は spec-loop の決まり（Q&A 表・版の重ね方・未決定の印）に従い、spec-loop は screen-spec に依存しません。画面の無い案件では spec-loop を単独で使えます。

いまは表の検査と、画面設計書を始めて画面を足すスキル（`init`・`add`）と雛形までです。実現方式ごとの profile（`web-spa`）・UI モックの生成は後の段で足します（#1094〜#1096）。

## スキル

| スキル | すること |
| --- | --- |
| `/screen-spec:init` | spec-loop の正本の作業中の版に `requirements/screens/` を用意する（3 つの表・案件ごとの設定・共通仕様・仕様書の雛形） |
| `/screen-spec:add` | 画面ID を採番し、画面の表に 1 行足し、仕様書とワイヤーフレームの雛形を置く |

どちらも Q&A 表を書かず、Q&A の番号を振りません。書くのは同梱のスクリプト（`scripts/write-screens.py`）で、書いた後に検査を走らせます。

## 中身

| 場所 | 何があるか |
| --- | --- |
| `references/tables.md` | 画面・項目・遷移の表の置き場所・列・決まった値と、検査の項目と終了コード |
| `references/prose.md` | 散文の仕様書の形（表とのつながり・節の名前と順・空の節と N/A）・雛形・書き方・レビュー観点・共通仕様 |
| `references/spec-loop.md` | spec-loop との境目——対応する spec-loop の版の範囲・spec-loop の見つけ方・Q&A の番号を振らないこと |
| `scripts/check-screens.py` | 表と散文の仕様書の検査（標準ライブラリのみ。spec-loop のスクリプトを読み込む） |
| `scripts/write-screens.py` | `init`・`add` のスキルが呼ぶ書き込み（表と雛形を置く・画面ID を採番する。標準ライブラリのみ） |
| `templates/` | 仕様書（`spec.md`）・共通仕様（`common.md`）・ワイヤーフレーム（`wireframe.xml`。drawio の中身で、拡張子を `.drawio` にしない——このリポジトリの図の検査が `diagrams/` の外の `.drawio` を止めるので）の雛形 |
| `skills/` | `init`・`add` のスキル |

## 検査を走らせる

```bash
python3 scripts/check-screens.py <正本リポジトリの docs ディレクトリ> [--upto <n>] [--spec-loop <spec-loop のプラグインの根>]
```

終了コードと出力の形は `references/tables.md` の「検査」を正とします。
