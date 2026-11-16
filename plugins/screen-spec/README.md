# screen-spec

画面設計書を [spec-loop](../spec-loop/README.md) とは別に持つプラグインです（計画は [#1081](https://github.com/hdknr/claude-code-setup/issues/1081)）。
画面の仕様を、表（画面・項目・遷移の 3 つの CSV）と散文の仕様書の組み合わせで持ち、表を spec-loop の版の重ね方で重ねた全体に検査を当てます。

screen-spec は spec-loop の決まり（Q&A 表・版の重ね方・未決定の印）に従い、spec-loop は screen-spec に依存しません。画面の無い案件では spec-loop を単独で使えます。

いまは骨組みと表の検査と、表から UI モックを作る生成器です。スキル（`init`・`add`）と散文の雛形・実現方式ごとの profile（`web-spa`）・モックの差分の印とレビュー会の進め方は後の段で足します（#1093・#1094・#1096）。

## 中身

| 場所 | 何があるか |
| --- | --- |
| `references/tables.md` | 画面・項目・遷移の表の置き場所・列・決まった値と、検査の項目と終了コード |
| `references/prose.md` | 散文の仕様書のうち検査が見る形（表とのつながり・節の名前と順・空の節と N/A） |
| `references/spec-loop.md` | spec-loop との境目——対応する spec-loop の版の範囲・spec-loop の見つけ方・Q&A の番号を振らないこと |
| `references/mock.md` | UI モックの生成器の決まり——出力の置き場所・種別ごとの描き方・説明の欄・共有の層だけを出すこと・描き方の差し替え・何で作ったかの印・終了コード |
| `scripts/check-screens.py` | 表と散文の仕様書の検査（標準ライブラリのみ。spec-loop のスクリプトを読み込む） |
| `scripts/build-mock.py` | 表から UI モック（HTML 1 枚）を生成する（標準ライブラリのみ。`check-screens.py` を読み込む） |

## 検査を走らせる

```bash
python3 scripts/check-screens.py <正本リポジトリの docs ディレクトリ> [--upto <n>] [--spec-loop <spec-loop のプラグインの根>]
```

終了コードと出力の形は `references/tables.md` の「検査」を正とします。

## UI モックを作る

```bash
python3 scripts/build-mock.py <正本リポジトリの docs ディレクトリ> [--upto <n>] [--spec-loop <spec-loop のプラグインの根>]
```

`<docs の親>/build/mock/v<n>/index.html` に書きます（commit しない）。決まりは `references/mock.md` を正とします。
