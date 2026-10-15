# spec-loop

コーディングエージェントの開発ループ（[dev-loop](../dev-loop/README.md)）の**手前にある、要求側のループ**を
扱うプラグインです。要求確定・仕様レビュー・実現性とコスト・提案書の 4 つのループと、
確定した仕様を dev-loop の入力（Issue）に変える引き渡しを、ループごとのスキルとして持つ予定です。

**いまのスキルは `req-loop`（要求確定のループ）と `spec-review`（仕様レビューのループ）の 2 本です**。残りのループのスキルは
段ごとに足します（計画は [#214](https://github.com/hdknr/claude-code-setup/issues/214)）。

設計の背景（なぜ dev-loop と分けるか・なぜ 1 つのプラグインにまとめるか）は記事を参照:
<https://hdknr.github.io/blogs/posts/2026/10/spec-loop-plugin/>

## 中身

| 場所 | 何があるか |
| --- | --- |
| `references/tree.md` | 正本リポジトリのツリー（どこに何を置くか） |
| `references/qa-csv.md` | Q&A 表の列・起票元・状態（表の置き場所は `references/tree.md`） |
| `references/signoff-tags.md` | サインオフのタグの命名と、2 つの承認が同じ範囲を見ていたかの確かめ方 |
| `references/spec-exit.md` | 仕様レビューを抜ける条件・未決定の印・仕様チェックリスト・形式検査の対象 |
| `scripts/check-qa-csv.py` | Q&A 表が決まりどおりかの検査（標準ライブラリのみ） |
| `scripts/qa-to-pptx.py` | Q&A 表からレビュー会用の PPTX を作る（標準ライブラリのみ） |
| `scripts/check-spec-exit.py` | 仕様レビューを抜ける条件のうち、機械で決まる条件 1 の判定（標準ライブラリのみ） |
| `skills/req-loop/` | 要求確定のループを 1 周（= レビュー会 1 回分）進めるスキル |
| `skills/spec-review/` | 仕様レビューのループを 1 回分進めるスキル（仕様を書く側） |
| `agents/` | 仕様を批判する 3 つの判定役（`red-team`・`domain-checker`・`formal-checker`）。**書き込みツールを持たない** |

**データの決まりは `references/` だけに書きます。** このファイルも、スキルも、公開ページも、
そこを指すだけで決まりを写しません。写しがあると、直すときに一部だけ直し漏れます。

**例外はスクリプトの定数**で、機械で検査する以上、写しが要ります。
写しがずれていないかは、このリポジトリのテストが `references/` の表と突き合わせて確かめます
（`scripts/test-check-qa-csv.py` と `scripts/test-check-spec-exit.py`）。

## `req-loop` — 要求確定のループ

`/spec-loop:req-loop` で呼びます。1 回の実行で、前回のレビュー会でもらった回答を仕様に反映し、
未決定事項を選択肢付きの質問として Q&A 表に起票し、レビュー会用の PPTX を作って、
**利用者の回答待ちで止まります。** 回答をスキルが推測で埋めることはありません。
再開点は会話ではなく Q&A 表の状態から読むので、別のセッションで呼び直しても続きから始まります。

手順と守ることは [`skills/req-loop/SKILL.md`](skills/req-loop/SKILL.md) を正とします。

**プラグインとしてだけ使えます。** スキルは共有のデータの決まりとスクリプトを
プラグイン直下に置いて `../../` で指しているので、スキルのディレクトリだけを
素のスキルとして複製・symlink すると指し先が無くなります。

## `spec-review` — 仕様レビューのループ

`/spec-loop:spec-review` で呼びます。1 回の実行で、確定した要求から開発者向けの仕様を書き下し（このスキルが書く側）、
`agents/` の 3 つの判定役に**別のティアで**レビューさせて、指摘を振り分けます——開発者が決めてよいものは仕様を直し、
**利用者の判断が要るものは Q&A 表に起票して `req-loop` の回答待ちに差し戻します。**
**ループを抜ける条件（`references/spec-exit.md`）を満たしたときだけ「抜けた」と報告します。**

手順と守ることは [`skills/spec-review/SKILL.md`](skills/spec-review/SKILL.md) を正とします。

**判定役はファイルを直接書くツールを持ちません**（`tools:` は許可リストで、読み取りと `Bash` だけ）。
`model` も定義に書かず、呼び出す側が仕様を書いたモデルと別のティアを選びます。
この形はこのリポジトリの `scripts/check-plugin-versions.py` が CI で確かめます。

## Q&A 表を検査する

正本リポジトリで、Q&A 表（置き場所は `references/tree.md`）を引数に渡します:

```bash
python3 <spec-loop の base ディレクトリ>/scripts/check-qa-csv.py <Q&A 表のパス>
```

終了コードは、0 が決まりどおり、1 が決まりに反する箇所あり（全部を 1 行ずつ出す）、
2 が中身を検査していない（読めない・UTF-8 でない・空）です。
何を見て何を見ないかは、スクリプトの docstring を正とします。

## レビュー会用の PPTX を作る

`req-loop` が使うスクリプトを、単体でも呼べます:

```bash
python3 <spec-loop の base ディレクトリ>/scripts/qa-to-pptx.py <Q&A 表のパス> <出力先.pptx> [--title <題>] [--subtitle <副題>]
```

載るのは状態が回答待ち・未反映の行だけで、Q&A 表が検査を通らなければ作りません。
出力先の既定は `references/tree.md` の「スライドの置き場所」にあります。
何を守り何を守らないか（終了コードを含む）は、スクリプトの docstring を正とします。

## 前提

- Python 3.10 以上（標準ライブラリだけを使います）
- 正本リポジトリが git で管理されていること（サインオフをタグで記録するため）
