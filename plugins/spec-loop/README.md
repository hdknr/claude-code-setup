# spec-loop

コーディングエージェントの開発ループ（[dev-loop](../dev-loop/README.md)）の**手前にある、要求側のループ**を
扱うプラグインです。要求確定・仕様レビュー・実現性とコスト・提案書の 4 つのループと、
確定した仕様を dev-loop の入力（Issue）に変える引き渡しを、ループごとのスキルとして持ちます。

**スキルは `req-loop`（要求確定）・`spec-review`（仕様レビュー）・`feasibility`（実現性とコスト）・
`proposal`（提案書）・`scaffold`（dev-loop への引き渡し）の 5 本です**（計画は [#214](https://github.com/hdknr/claude-code-setup/issues/214)）。

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
| `references/feasibility-csv.md` | スケジュール（`schedule.csv`）と見積り（`estimate.csv`）の列 |
| `scripts/check-spec-exit.py` | 仕様レビューを抜ける条件のうち、機械で決まる条件 1 の判定（標準ライブラリのみ） |
| `scripts/check-feasibility-csv.py` | スケジュールと見積りの表が決まりどおりかの検査（標準ライブラリのみ） |
| `scripts/schedule-to-gantt.py` | スケジュールの表からガントチャート（SVG）を作る（標準ライブラリのみ） |
| `scripts/check-signoff.py` | 同じ版の 2 つのサインオフのタグの時点で、共有の範囲が一致するかの照合（標準ライブラリと `git`） |
| `scripts/build-proposal.py` | 照合が通ったときだけ、承認したタグの時点の中身から提案書を作る（標準ライブラリと `git`） |
| `references/spec-ir.md` | 仕様の中間表現（`spec_ir.json`）の形 |
| `references/handoff-issue.md` | dev-loop に渡す Issue の本文の形 |
| `scripts/scaffold.py` | 中間表現から OpenAPI・型・Red テスト・Issue の本文を作る。関門（仕様レビューを抜ける条件 1）を自分で通す（標準ライブラリのみ） |
| `references/versions.md` | 版のディレクトリ（`docs/v<n>/`）と、差分の重ね合わせ・削除（`removed.csv`）・凍結・前の構成からの移し方の決まり |
| `scripts/merge-versions.py` | 版ごとの差分を重ねて、ある版の時点の全体を作る（標準ライブラリのみ） |
| `scripts/diff-versions.py` | ある版が前の版から何を足し・変え・消したかを、前の版の時点の全体と比べて出す（標準ライブラリのみ） |
| `scripts/check-frozen.py` | リリースした版（`release-v<n>` のタグ）の `docs/v<n>/` が直されていないかの確かめ（標準ライブラリと `git`） |
| `templates/mkdocs/` | 正本リポジトリを MkDocs で閲覧するための雛形（設定・Q&A 表を CSV から描くフック・表示用のページ） |
| `scripts/init-mkdocs.py` | 雛形を正本リポジトリへ写す。`mkdocs.yml` が在れば何も写さず、在るファイルは変えない（標準ライブラリのみ。決まりは `references/tree.md` の「ドキュメントのツール」） |
| `skills/req-loop/` | 要求確定のループを 1 周（= レビュー会 1 回分）進めるスキル |
| `skills/spec-review/` | 仕様レビューのループを 1 回分進めるスキル（仕様を書く側） |
| `skills/feasibility/` | 実現性・コストのループを 1 回分進めるスキル（見積りを書く側） |
| `skills/proposal/` | 関門を照合して提案書を作るスキル |
| `skills/scaffold/` | 確定した仕様を Red テストと Issue に変え、dev-loop に渡すスキル |
| `agents/` | 仕様を批判する 3 つの判定役（`red-team`・`domain-checker`・`formal-checker`）と見積りの検証役（`estimate-checker`）。**書き込みツールを持たない** |

**データの決まりは `references/` だけに書きます。** このファイルも、スキルも、公開ページも、
そこを指すだけで決まりを写しません。写しがあると、直すときに一部だけ直し漏れます。

**例外はスクリプトの定数**で、機械で検査する以上、写しが要ります。
写しがずれていないかは、このリポジトリのテストが `references/` の表と突き合わせて確かめます
（`scripts/test-check-qa-csv.py`・`scripts/test-check-spec-exit.py`・`scripts/test-check-feasibility-csv.py`・
`scripts/test-check-signoff.py`・`scripts/test-scaffold.py`・`scripts/test-merge-versions.py`・`scripts/test-check-frozen.py`）。

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

## `feasibility` — 実現性・コストのループ

`/spec-loop:feasibility` で呼びます。1 回の実行で、要求・仕様から規模を数えて見積り（開発費・運用費）と
スケジュールを更新し、ガントチャートをスクリプトで生成し、**選択肢によって費用が変わる未決定事項を
費用付きの質問として Q&A 表に起票します**。見積りは `agents/estimate-checker.md` に**別のティアで**検証させます。
**予算責任者の合意待ちで止まります**——合意を推測で埋めることも、`budget-signoff` のタグを付けることもありません。

手順と守ることは [`skills/feasibility/SKILL.md`](skills/feasibility/SKILL.md) を正とします。

## `proposal` — 提案書のループ

`/spec-loop:proposal` で呼びます。**同じ版の 2 つのサインオフのタグ（`v<n>/req-signoff-<k>`・`v<n>/budget-signoff-<k>`）の時点で
共有の範囲（`docs/v<n>/shared/` ほか。`references/signoff-tags.md`）が一致するかをスクリプトで照合し、一致したときだけ提案書を生成します**（LLM に判断させません）。
提案書は**承認したタグの時点の中身**から作るので、承認の後に直した中身は入りません。
**v2 以降は、前の版との比較（追加・変更・削除）を載せた変更の提案書になります**（`references/versions.md` の「版の差分」）。
**決裁者の承認待ちで止まります。**

手順と守ることは [`skills/proposal/SKILL.md`](skills/proposal/SKILL.md) を正とします。

## `scaffold` — dev-loop への引き渡し

`/spec-loop:scaffold` で呼びます。仕様レビューを抜けた仕様を中間表現（`spec_ir.json`）に書き起こし、
同梱のスクリプトで OpenAPI・型・**Red テスト**（実装が無いと失敗するテスト）と **Issue の本文**を作って、
**1 機能 = Issue 1 件**で登録します（登録の前に利用者に確かめます）。**Issue の登録で止まり、以降は dev-loop が受け持ちます。**
v2 以降は前の版と比べて機能を**追加・変更・削除**に分け、**変わった機能だけ**を Issue にします——変更の Issue は
回帰（変わらないケースが緑のまま）を、削除の Issue は撤去を受入基準に持ちます（形は `references/handoff-issue.md`）。
dev-loop は Issue の本文の印で spec-loop から来たことを知り、開発中に見つけた仕様の穴を
Q&A 表に起票元 `開発` で差し戻します（規定は dev-loop の `references/spec-gap.md`）。

手順と守ることは [`skills/scaffold/SKILL.md`](skills/scaffold/SKILL.md) を正とします。

```bash
python3 <spec-loop の base ディレクトリ>/scripts/scaffold.py [--repo <正本リポジトリ>] [--check [--upto <n>] | --dry-run [--upto <n>] | --red-check]
```

`--check` は、置いてある `scaffold/` が今の中間表現から作るものと同じかを、バイトで確かめます（鮮度）。
`--upto <n>` を付けると v<n> の時点に当てます（差分の周を始める前の確かめ。`references/versions.md`）。
`--red-check` は Red テストを走らせ、失敗するのが追加・変更のケースだけで、ほかは緑かを確かめます。
実装を置くモジュールは、中間表現の `impl_module` に書きます（`references/spec-ir.md`）。
何を守り何を守らないか（終了コードを含む）は、スクリプトの docstring を正とします。

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

## スケジュールと見積り・照合・提案書のスクリプト

`feasibility` と `proposal` が使うスクリプトを、単体でも呼べます:

```bash
python3 <spec-loop の base ディレクトリ>/scripts/check-feasibility-csv.py <schedule.csv> <estimate.csv>
python3 <spec-loop の base ディレクトリ>/scripts/schedule-to-gantt.py <schedule.csv> <出力先.svg>
python3 <spec-loop の base ディレクトリ>/scripts/check-signoff.py [--repo <正本リポジトリ>] [--version <n>] [--req <タグ>] [--budget <タグ>]
python3 <spec-loop の base ディレクトリ>/scripts/build-proposal.py [--repo <正本リポジトリ>] [--version <n>] [--out <出力先.md>] [--title <題>]
python3 <spec-loop の base ディレクトリ>/scripts/check-frozen.py [--repo <正本リポジトリ>]
python3 <spec-loop の base ディレクトリ>/scripts/diff-versions.py docs [--version <n>]
```

生成するもの（ガントチャート・提案書）は、作れなかったときに前の出力を消します。
何を守り何を守らないか（終了コードを含む）は、各スクリプトの docstring を正とします。

## 前提

- Python 3.10 以上（標準ライブラリだけを使います）
- 正本リポジトリが git で管理されていること（サインオフをタグで記録するため）
