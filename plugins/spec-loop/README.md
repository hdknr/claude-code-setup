# spec-loop

コーディングエージェントの開発ループ（[dev-loop](../dev-loop/README.md)）の**手前にある、要求側のループ**を
扱うプラグインです。要求確定・仕様レビュー・実現性とコスト・提案書の 4 つのループと、
確定した仕様を dev-loop の入力（Issue）に変える引き渡しを、ループごとのスキルとして持つ予定です。

**いまはスキルを 1 本も持ちません。** 入っているのは、どのスキルも共有するデータの決まりと、
その決まりを機械で確かめるスクリプトだけです。スキルは段ごとに足します（計画は
[#214](https://github.com/hdknr/claude-code-setup/issues/214)）。

設計の背景（なぜ dev-loop と分けるか・なぜ 1 つのプラグインにまとめるか）は記事を参照:
<https://hdknr.github.io/blogs/posts/2026/10/spec-loop-plugin/>

## 中身

| 場所 | 何があるか |
| --- | --- |
| `references/tree.md` | 正本リポジトリのツリー（どこに何を置くか） |
| `references/qa-csv.md` | Q&A 表（`docs/shared/qa.csv`）の列・起票元・状態 |
| `references/signoff-tags.md` | サインオフのタグの命名と、2 つの承認が同じ範囲を見ていたかの確かめ方 |
| `scripts/check-qa-csv.py` | Q&A 表が決まりどおりかの検査（標準ライブラリのみ） |

**データの決まりは `references/` だけに書きます。** このファイルも、スキルも、公開ページも、
そこを指すだけで決まりを写しません。写しがあると、直すときに一部だけ直し漏れます。

**例外は `scripts/check-qa-csv.py` の定数**で、機械で検査する以上、写しが要ります。
写しがずれていないかは、このリポジトリの `scripts/test-check-qa-csv.py` が
`references/qa-csv.md` の表と突き合わせて確かめます。

## Q&A 表を検査する

正本リポジトリで:

```bash
python3 <spec-loop の base ディレクトリ>/scripts/check-qa-csv.py docs/shared/qa.csv
```

終了コードは、0 が決まりどおり、1 が決まりに反する箇所あり（全部を 1 行ずつ出す）、
2 が中身を検査していない（読めない・UTF-8 でない・空）です。
何を見て何を見ないかは、スクリプトの docstring を正とします。

## 前提

- Python 3.10 以上（標準ライブラリだけを使います）
- 正本リポジトリが git で管理されていること（サインオフをタグで記録するため）
