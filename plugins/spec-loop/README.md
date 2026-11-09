# spec-loop

コーディングエージェントの開発ループ（[dev-loop](../dev-loop/README.md)）の**手前にある、要求側のループ**を
扱うプラグインです。要求確定・仕様レビュー・実現性とコスト・提案書の 4 つのループと、
確定した仕様を dev-loop の入力（Issue）に変える引き渡しを、ループごとのスキルとして持ちます。

**スキルは `req-loop`（要求確定）・`spec-review`（仕様レビュー）・`feasibility`（実現性とコスト）・
`proposal`（提案書）・`scaffold`（dev-loop への引き渡し）の 5 本です**（計画は [#214](https://github.com/hdknr/claude-code-setup/issues/214)）。
**それらを利用者の不在のあいだに 1 単位ずつ回す入口 `autopilot` も持ちます**（下の「`autopilot` — 不在のあいだに回す入口」）。

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
| `scripts/render-diagrams.py` | 正本リポジトリの `docs/` の下の drawio と BPMN を隣の SVG に書き出し、ソースの指紋を書き込む。`--check` で書き出しが今のソースのものかを確かめる（標準ライブラリと draw.io の CLI。BPMN は下の `render-bpmn.mjs`。図の決まりは `references/tree.md` の「図」を正とする） |
| `scripts/render-bpmn.mjs` | `render-diagrams.py` が呼ぶ BPMN の描画口。bpmn-js を headless の Chrome で動かし、BPMN 1 枚を SVG に書き出す（Node・bpmn-js・puppeteer-core・Chrome） |
| `scripts/check-signoff.py` | 同じ版の 2 つのサインオフのタグの時点で、2 つの承認が見た中身（`shared/`・`requirements/`・`spec/`・`removed.csv`）が一致するかの照合（標準ライブラリと `git`） |
| `scripts/build-proposal.py` | 照合が通ったときだけ、承認したタグの時点の中身から提案書と仕様書（`--pptx` で PPTX も）を作る（標準ライブラリと `git`） |
| `references/spec-ir.md` | 仕様の中間表現（`spec_ir.json`）の形 |
| `references/handoff-issue.md` | dev-loop に渡す Issue の本文の形 |
| `references/nfr.md` | 性能の要求の表（`shared/nfr.csv`）の列・性能を仕様に書く手順・要求の無い機能は最適化しない既定の原則・性能テスト |
| `scripts/scaffold.py` | 中間表現から OpenAPI・型・Red テスト・Issue の本文を作る。関門（仕様レビューを抜ける条件 1）を自分で通す（標準ライブラリのみ） |
| `references/versions.md` | 版のディレクトリ（`docs/v<n>/`）と、差分の重ね合わせ・削除（`removed.csv`）・凍結・前の構成からの移し方の決まり |
| `scripts/merge-versions.py` | 版ごとの差分を重ねて、ある版の時点の全体を作る（標準ライブラリのみ） |
| `scripts/diff-versions.py` | ある版が前の版から何を足し・変え・消したかを、前の版の時点の全体と比べて出す（標準ライブラリのみ） |
| `scripts/check-frozen.py` | リリースした版（`release-v<n>` のタグ）の `docs/v<n>/` が直されていないかの確かめ（標準ライブラリと `git`） |
| `templates/mkdocs/` | 正本リポジトリを MkDocs で閲覧するための雛形（設定・Q&A 表を CSV から描くフック・表示用のページ） |
| `scripts/autopilot-ledger.py` | autopilot の台帳（版ごとの `.claude/plans/spec-autopilot-v<版>.json`）の読み書き（標準ライブラリと `git`） |
| `scripts/autopilot-check.py` | autopilot の線の検査と、線から決まる周で使う操作の権限の点検（標準ライブラリと `git`） |
| `scripts/check-tlc.py` | TLC が正本リポジトリの `CLAUDE.md` に書いた呼び方で使えるかの確かめ（標準ライブラリと、書いた呼び方の TLC。下の「前提」） |
| `scripts/init-mkdocs.py` | 雛形を正本リポジトリへ写す（標準ライブラリのみ。いつ何を写すかは `references/tree.md` の「ドキュメントのツール」を正とする） |
| `skills/req-loop/` | 要求確定のループを 1 周（= レビュー会 1 回分）進めるスキル |
| `skills/spec-review/` | 仕様レビューのループを 1 回分進めるスキル（仕様を書く側） |
| `skills/feasibility/` | 実現性・コストのループを 1 回分進めるスキル（見積りを書く側） |
| `skills/proposal/` | 関門を照合して提案書を作るスキル |
| `skills/scaffold/` | 確定した仕様を Red テストと Issue に変え、dev-loop に渡すスキル |
| `skills/autopilot/` | 仕様レビューと実現性・コストのループを、利用者の不在のあいだに 1 単位ずつ進める入口 |
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
**利用者に見える結果が変わるものは共有の Q&A 表に起票して `req-loop` の回答待ちに差し戻します。** 費用・運用・内部の値だけが変わる選択は、内部の Q&A 表（`spec/qa-dev.csv`）に開発者の決定として記録します（費用は予算の責任者へ）。
範囲の外の場面は範囲の文書に記録し、実現の手段の指摘は実装に渡し、誤った指摘は理由をつけて退けます——いずれも仕様には足しません
（区分は仕様を直す・共有の Q&A 表に起票する・内部の Q&A 表に記録する・範囲の外として記録する・実装に渡す・退けるの 6 つ。線と区分の原本は `references/spec-scope.md`）。
**ループを抜ける条件（`references/spec-exit.md`）を満たしたときだけ「抜けた」と報告します。**

手順と守ることは [`skills/spec-review/SKILL.md`](skills/spec-review/SKILL.md) を正とします。

**判定役はファイルを直接書くツールを持ちません**（`tools:` は許可リストで、読み取りと `Bash` だけ）。
`model` も定義に書かず、呼び出す側が仕様を書いたモデルと別のティアを選びます。
この形はこのリポジトリの `scripts/check-plugin-versions.py` が CI で確かめます。

## `feasibility` — 実現性・コストのループ

`/spec-loop:feasibility` で呼びます。1 回の実行で、要求・仕様から規模を数えて見積り（開発費・運用費）と
スケジュールを更新し、ガントチャートをスクリプトで生成し、**選択肢によって費用が変わる未決定事項を
費用付きの質問として Q&A 表に起票します**。見積りは `agents/estimate-checker.md` に**別のティアで**検証させます。
**予算責任者の合意待ちで止まります**——合意を推測で埋めることも、予算の承認のタグ（`signoff/v<n>/budget-<k>`）を付けることもありません。

手順と守ることは [`skills/feasibility/SKILL.md`](skills/feasibility/SKILL.md) を正とします。

## `proposal` — 提案書のループ

`/spec-loop:proposal` で呼びます。**同じ版の 2 つのサインオフのタグ（`signoff/v<n>/req-<k>`・`signoff/v<n>/budget-<k>`）の時点で
2 つの承認が見た中身（`docs/v<n>/shared/`・`requirements/`・`spec/` ほか。`references/signoff-tags.md`）が一致するかをスクリプトで照合し、一致したときだけ提案書を生成します**（LLM に判断させません）。
提案書は**承認したタグの時点の中身**から作るので、承認の後に直した中身は入りません。
**v2 以降は、前の版との比較（追加・変更・削除）を載せた変更の提案書になります**（`references/versions.md` の「版の差分」）。
**提案書と一緒に仕様書（規模・構成の図・機能・決定表・範囲の外）も作ります。利用者にまだ確かめていない暫定の回答（`暫定反映`）が残るうちは作りません**（`references/tree.md` の「仕様書」・`references/qa-csv.md` の「暫定の行の判別」）。
**決裁者の承認待ちで止まります。**

手順と守ることは [`skills/proposal/SKILL.md`](skills/proposal/SKILL.md) を正とします。

## `scaffold` — dev-loop への引き渡し

`/spec-loop:scaffold` で呼びます。仕様レビューを抜けた仕様を中間表現（`spec_ir.json`）に書き起こし、
同梱のスクリプトで OpenAPI・型・**Red テスト**（実装が無いと失敗するテスト）と **Issue の本文**を作って、
**1 機能 = Issue 1 件**で登録します（登録の前に利用者に確かめます。同じモジュール・同じ受入基準・同じデプロイ経路の機能は、
`--bundle` で選んで 1 件にまとめられます）。依存の連鎖（呼ぶ機能が呼ばれる機能に依存する）は、登録した後に `parent-checklist.py` が
dev-loop の cruise の親 Issue の書式で出します。**Issue の登録で止まり、以降は dev-loop が受け持ちます。**
v2 以降は前の版と比べて機能を**追加・変更・削除**に分け、**変わった機能だけ**を Issue にします——変更の Issue は
回帰（変わらないケースも緑であること）を、削除の Issue は撤去を受入基準に持ちます（形は `references/handoff-issue.md`）。
dev-loop は Issue の本文の印で spec-loop から来たことを知り、開発中に見つけた仕様の穴を
Q&A 表に起票元 `開発` で差し戻します（規定は dev-loop の `references/spec-gap.md`）。

手順と守ることは [`skills/scaffold/SKILL.md`](skills/scaffold/SKILL.md) を正とします。

```bash
python3 <spec-loop の base ディレクトリ>/scripts/scaffold.py [--repo <正本リポジトリ>] [--check [--upto <n>] | --dry-run [--upto <n>] | --red-check [--in-progress]] [--provisional] [--bundle F-001,F-002]...
python3 <spec-loop の base ディレクトリ>/scripts/parent-checklist.py --index build/scaffold/issues/issues.json --issues <gh issue list の出力>
```

`--check` は、置いてある `scaffold/` が今の中間表現から作るものと同じかを、バイトで確かめます（鮮度）。
`--upto <n>` を付けると `v<n>` の時点に当てます（差分の周を始める前の確かめ。`references/versions.md`）。
`--red-check` は Red テストを走らせ、回帰は緑で、追加・変更は失敗するか前の版の実装がもう満たすかを確かめます。
**実装が前の版の状態にあることを前提にせず**、前の版の Red テストも同じ実装に当てて確かめます。
この版をもう実装し始めた作り直しの経路では `--in-progress` を付けます。
実装を置くモジュールは、中間表現の `impl_module` に書きます（`references/spec-ir.md`）。
何を守り何を守らないか（終了コードを含む）は、スクリプトの docstring を正とします。

## `autopilot` — 不在のあいだに回す入口

`/spec-loop:autopilot <版>` で呼びます。**1 回の起動で、台帳の次の 1 単位**（仕様レビューの周の 1 段か、実現性とコストの 1 回）**だけを進めて終えます**——
`claude -p` で同じ引数を起動し直す外側のループ（[#850](https://github.com/hdknr/claude-code-setup/issues/850)）を前提にします。
台帳が無い起動では、上限に達したときに続けてよい周の番号・`判断が要る` の質問を推奨で暫定に採るか・commit とマージをどこまでするか・止まる地点を利用者に確かめて台帳に残し、
周で使う操作の権限を点検して示します（単位は進めません）。各起動は線に従って訊かず、線に無い判断では台帳を `stopped` にして止まります。
**サインオフのタグ・scaffold・Issue の登録はしません。**

手順と守ることは [`skills/autopilot/SKILL.md`](skills/autopilot/SKILL.md) を、台帳の形と線の一覧は `scripts/autopilot-ledger.py`・`scripts/autopilot-check.py` の docstring を正とします。

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
python3 <spec-loop の base ディレクトリ>/scripts/build-proposal.py [--repo <正本リポジトリ>] [--version <n>] [--out <出力先.md>] [--title <題>] [--spec-title <題>] [--pptx]
python3 <spec-loop の base ディレクトリ>/scripts/check-frozen.py [--repo <正本リポジトリ>]
python3 <spec-loop の base ディレクトリ>/scripts/diff-versions.py docs [--version <n>]
```

生成するもの（ガントチャート・提案書・仕様書）は、作れなかったときに前の出力を消します。
ガントチャートの前の出力を消せないとき（出力先のディレクトリが書けない・辿れないなど）は、2 で止まり、残った出力を名指しします（#499）。
出力先が symlink で、先を辿れないとき（#535）と先が辿れる通常のファイルのとき（#626）は、リンクも先も消さずに、リンクと先のパスを名指しして 2 で止まります（壊れたリンク・ディレクトリを指すリンクは消さずに名指しもしません。細部は docstring を正とします）。
ただし提案書と仕様書で消すのは、印 `.build-proposal` が名指しする前の出力だけです——印の無いファイル（spec-loop 0.25.0 までの出力・手で置いたもの）や
印が読めない場所の出力は、作れなかったときも残ります（このとき、残った出力の名前のファイルと読めない印を「今回の出力ではない」「印を読めない」と名指しします。出力先が決まる前に止まった 2——引数の解釈の失敗など——を除く）。
印が名指しするのに消せなかった出力も残ります（このときは 2 で止まり、残ったものを名指しします。`references/tree.md` の「生成物の置き場所」）。
印が名指しする出力が先の在る symlink なら、リンクも先も消さずに先のパスも名指しして 2 で止まり、印が読めない（symlink を含む）なら印を書き換えずに 2 で止まります（#512）。
作れたとき（0）も、印に無い出力の名前のファイルが残っていれば「今回の出力ではない」と名指しします（終了コードは 0 のまま）。
何を守り何を守らないか（終了コードを含む）は、各スクリプトの docstring を正とします。

## 図を書き出す

正本リポジトリの文書の図は、アスキーアートでも Mermaid でも描きません。業務フロー（スイムレーン）は BPMN で、それ以外の図は drawio で描き、どちらも SVG に書き出します
（どちらで描くかの線・置き場所・形式・描かないもの・BPMN の書き出しに要るものは `references/tree.md` の「図」を正とします）。次で書き出します:

```bash
python3 <spec-loop の base ディレクトリ>/scripts/render-diagrams.py [<正本リポジトリの根>] [--check]
```

`docs/` の下の `.drawio` と `.bpmn` を全部、隣の同じ名前の `.svg` に書き出し、ソースの指紋を書き出しに書き込みます。
`--check` は描画系（draw.io・Node・Chrome）を起動せず、書き出しが無い・古い・ソースが無いものを名指しします（CI でも回せます）。
draw.io の CLI は `DRAWIO` で差し替えられます。BPMN は同梱の `render-bpmn.mjs` が bpmn-js を headless の Chrome で動かして描き、
Node・bpmn-js と puppeteer-core（`SPEC_LOOP_BPMN_DEPS`）・Chrome（`CHROME_PATH`）が要ります——無ければ何も書かずに名指しして止まります。何を守り何を守らないか（終了コードを含む）は、スクリプトの docstring を正とします。

## 前提

- Python 3.10 以上（標準ライブラリだけを使います）
- 正本リポジトリが git で管理されていること（サインオフをタグで記録するため）
- **TLC（TLA+ のモデル検査器）が既定で必須です**（#912）。`spec-review` は、並行・リトライ・取り消しを含む業務フローを形式検査の対象に選ぶと
  TLC で検査します。TLC が無いと判定役を 1 体も起動せず、用意してから呼び直すか、用意せずに進める（業務フローは判定できず、その回は抜けません）かを訊きます。
  どの版で業務フローが対象になるかは周を回すまで決まらないので、**`spec-review` を回す前に用意してください。**
  `autopilot` は起動時の確認で TLC を点検し、各起動は TLC が無ければ単位を 1 つも進めずに止まります。

### TLC の用意

1. **Java と、TLA+ の `tla2tools.jar` を置きます**（スキルは入れません）。
2. **正本リポジトリの根の `CLAUDE.md` に、呼び方を行頭から 1 行で書きます**——後ろにモデルのファイル（`<名前>.tla`）を足して、モデルのディレクトリで走らせる形です:

```text
TLC の呼び方: java -cp /opt/tla/tla2tools.jar tlc2.TLC
```

`spec-review` の確かめ・`autopilot` の点検・Formal Checker は、どれもこの呼び方だけを使います——**`command -v` では探しません**
（jar で入れた TLC は `command -v` では見つからないため）。確かめは `scripts/check-tlc.py` で、呼び方に小さいモデルを 2 つ
（通るものと、わざと違反するもの）検査させて決めます:

```bash
python3 <spec-loop の base ディレクトリ>/scripts/check-tlc.py <正本リポジトリの根>
```

### 業務フローを形式検査しない案件

業務フローを一度も形式検査しない案件（例: 料金の計算ルールだけを直す案件）は、正本リポジトリの根の `CLAUDE.md` に次の 1 行を書くと、TLC を必須から外せます。
`autopilot` の点検と各起動は TLC を確かめなくなります:

```text
業務フローの形式検査: しない
```

宣言が古くなっても（後の版で業務フローを対象に選んだ）、`spec-review` が対象を選んだときに TLC を確かめ、無ければ今のとおり判定役を起動せずに訊きます。
書き方の細部（コードフェンスの中の行は読まない・同じ行を 2 行書かない・値は `しない` だけ）と終了コードは、`scripts/check-tlc.py` の docstring を正とします。
Alloy（権限・ロールの検査器）は必須にしていません——権限・ロールを対象に選んだときに `spec-review` が確かめます。
**0.73.0 より前から使っている正本の移行**（`PATH` の `tlc` を使っていた・TLC を入れていない）は、`references/spec-exit.md` の「0.73.0 より前から使っている正本の移行（1 度だけ）」を正とします。
