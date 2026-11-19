# Issue #1289 — spec-loop: proposal の PPTX を、決裁者が読める既定のデザインにし、指示でカスタマイズでき、描画して確かめる

**不在の周**（`/dev-loop:cruise 1290 --absent` の起動・2026-11-19）。利用者には訊かない。親（cruise #1290）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1290`））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`（古い値。後退の分け方の 3 と満たしていない受入基準では止まる）。
台帳は書かない（親だけ）。手順 7 のマージはしない（PR・PR 側の CI の確認まで。手順 8 は計画ファイルに書くところまで）。
読み込んだ dev-loop は 2.12.0（`SKILL.md` 1931 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1290`））。
版の上げ方: `spec-loop` を **minor**（能力の追加。0.x なので壊れる変更も minor）。着手時の main は spec-loop 0.115.0 → 0.116.0。#1247（PR #1294）が 0.116.0 を押さえて判断待ちなので、
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.12.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: `--pptx` の既定のデザインを決裁者が読める体裁にする（費用・期間・図・手書き部分のカード・決定事項の別紙と概要・仕様書）、
指示（正本の `CLAUDE.md`）で差し替え・変更できる口、生成した PPTX を描画して確かめる手順、手書き部分の長さの目安、`schedule-to-gantt.py` の重なりの修正。
本文に受入基準を緩める指示は無い（コメントは無い）。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **H1 指示で変えられる口の形**: (a) `build-proposal.py` の引数（`--pptx-script`・`--no-appendix`・`--no-scope-slide`・`--scope-questions`・`--scope-match`・`--overview`・`--slide-strip`）を、
  proposal スキルが正本の `CLAUDE.md` の記述から組んで渡す（推奨）／(b) 正本に設定ファイルを置いて読ませる。
  推した理由: 設定ファイルは正本のツリー（`tree.md`）と版の決まりを増やし、サインオフの比べる範囲に入るかの判断も要る。引数なら正本に何も足さず、スキルが従う `CLAUDE.md` は今でも「PPTX が要るか」を読む入口である。
- **H2 差し替えスクリプトの呼び方**: `python3 <script> --materials <build-proposal の出力と同じ中身を置いた一時ディレクトリ> --proposal-out <p.pptx> --spec-out <s.pptx>`（推奨）／標準入力に JSON。
  推した理由: 材料を「build-proposal.py の出力だけ」にし、スクリプトが足せない・変えられないことを、渡すものがファイルであることで担保できる。出力 2 本が揃わなければ 2 で止まり、印と前の出力の扱いは今までの PPTX と同じ。
- **H3 範囲を決めた質問の既定の選び方**: 反映済みの行のうち、`反映先` が範囲の文書（`scope.md`）を指すか、質問が `範囲|作らない|対象外|スコープ` を含む行（推奨）。外すときは `--scope-questions` で番号を渡す。
  推した理由: Q&A 表に「範囲を決めた」印の列が無く、列を足すと全正本の表の移行になる。当たらなければ 1 枚を出さない（空の 1 枚を作らない）。
- **H4 図を PNG にする道具が無いとき**: 図を載せず、その旨を 1 枚に書き、標準エラーに道具名つきで知らせて 0 で作る（推奨）／止める（1・2）。
  推した理由: 図が無いことは決裁者に見せたくないが、PPTX が作れないほどではない。「道具が無いので確かめられない・載せていない」を報告に出すことが受入基準（スキルの手順）の求めである。
- **H5 描画の確かめ（`check-pptx-render.py`）の終了コード**: 0 は見つからず・1 は見切れ等を見つけた・3 は道具（LibreOffice・pdftotext・pdftoppm）が無く確かめられない（推奨）。
  3 は緑ではない。CI では呼ばない（道具が無い）。

確認の Issue は立てない（`マージ前の判断 = 推奨で決めて起票` は親が立てる）。穴の判断は上の推奨のとおりに進める。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/proposal-pptx.py` — 新規。提案書・仕様書の既定のデザイン（カード・表・費用・ガントチャートの図形・図・別紙の xlsx）
- `plugins/spec-loop/scripts/check-pptx-render.py` — 新規。PPTX を描画して機械で探す（見切れ・代わりの文字・はみ出し）と、1 ページずつの PNG
- `plugins/spec-loop/scripts/build-proposal.py` — `--pptx` の中身と引数、別紙の xlsx、差し替えスクリプトの口
- `plugins/spec-loop/scripts/qa-to-pptx.py` — `write` が画像の部品（バイト列）も書けるようにする
- `plugins/spec-loop/scripts/schedule-to-gantt.py` — SVG の重なり（短い工程の名前と棒・月の見出しどうし）
- `plugins/spec-loop/skills/proposal/SKILL.md` — 描画の確かめの手順・指示から引数を組む手順
- `plugins/spec-loop/references/tree.md`・`writing-style.md` — PPTX の決まり・手書き部分の長さの目安
- `scripts/test-proposal-pptx.py`・`scripts/test-check-pptx-render.py` — 新規。回帰テスト（変異テストを含む）
- `scripts/test-build-proposal.py`・`scripts/test-schedule-to-gantt.py`・`scripts/test-qa-to-pptx.py`・`scripts/test-check-qa-csv.py`（`is_provisional` を読む側に `proposal-pptx.py` を足す） — 変えた振る舞いに合わせる
- `scripts/check-all.py`・`.github/workflows/plugins.yml` — テストの登録
- `CLAUDE.md`・`plugins/spec-loop/README.md`・`docs/plugins/spec-loop.md` — スクリプトの表
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json`・`plugins/spec-loop/skills/*/SKILL.md` — 版
- `docs/plans/issue-1289.md` — この計画ファイル

触らない:

- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）——説明の文は偽にならない
- 提案書・仕様書の Markdown の中身（`proposal.md`・`spec.md` は変えない。PPTX だけを変える）
- レビュー会の PPTX（`qa-to-pptx.py` の質問の頁。`markdown_slides` は差し替え口のために残す）
- 利用者の正本のリポジトリ（実案件の正本は読まない。試料は一時ディレクトリに作る）

依存の追加・更新: なし（図を PNG にする `rsvg-convert` と描画の確かめの LibreOffice・poppler は外部の道具で、どれも無くても `--pptx` は作れる。リポジトリの依存の定義は触らない）
仕様の振る舞い: 変えない

**複製の数**: 「`--pptx` の既定のデザインと指示の口」を述べる箇所は 4（`references/tree.md` が原本、`build-proposal.py` の docstring、`proposal/SKILL.md`、`CLAUDE.md` のスクリプトの表）。
分けない理由: 原本は `tree.md` で、ほかは指すか、スクリプトの docstring が定数の写し（テストが突き合わせる）。

## デプロイ経路

プラグイン（`marketplace.json` のカタログと、`link-skills.sh` を使う利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口: `build-proposal.py --pptx`（提案書・仕様書・別紙の xlsx）・`--pptx-script`（差し替え）・`check-pptx-render.py`・`schedule-to-gantt.py`・proposal の `SKILL.md` の手順・`writing-style.md`。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | 既定の `--pptx` で、費用の行が十数行・工程が十数行・図が 20 枚・決定事項が 100 件超の正本から作った PPTX を描画して、「…」の見切れ・はみ出し・「Text is not SVG」が 0 件 | 提案書の PPTX・仕様書の PPTX | 文字の寸法を見積もって行・カードを割り、省略記号を出さない。図は PNG にして drawio の代わりの文字を消す | LibreOffice で PDF に描画し、`check-pptx-render.py` が 0 件。目で 1 ページずつ見る（PNG） |
| A2 | 図が載り、見出しがファイル名でない | 仕様書の PPTX | 図の見出しは図の中の名前か読める名前 | 描画した PNG と `test-proposal-pptx.py` |
| A3 | 決定事項の全件が別紙の表（xlsx）にあり、提案書には概要の 1 枚と範囲の 1 枚が載る | 提案書の PPTX・別紙 | 全行を xlsx に書き、PPTX は件数と範囲の質問だけ | `test-proposal-pptx.py`（xlsx を開いて全件）。**LibreOffice で xlsx を開いて確かめる** |
| A4 | `CLAUDE.md` の指示で、デザインの差し替え（プロジェクトのスクリプト）と、別紙・範囲の 1 枚の有無を変えられる | `build-proposal.py` の引数 | `--pptx-script`・`--no-appendix`・`--no-scope-slide` | `test-build-proposal.py` |
| A5 | スキルの手順に描画の確かめが入り、道具が無ければそのことを報告する | proposal の `SKILL.md`・`check-pptx-render.py` | 3（確かめられない）で終わり、緑にしない | `test-check-pptx-render.py`（道具の無い `PATH`） |
| A6 | `schedule-to-gantt.py` の SVG で、短い工程の名前と棒・月の見出しどうしが重ならない | `schedule-to-gantt.py` | 工程名を左の列に出し、月の見出しの間隔を見る | `test-schedule-to-gantt.py` と描画 |
| A7 | 手書き部分の長さの目安が決まりにある | `writing-style.md` | 文書 | 目で読む（`check-skill-pointers.py`・`check-norm-markers.py`） |
| A8 | 前からの振る舞いを壊さない——Markdown・Markdown なしの出力・印・名指し・終了コードは変わらない | `build-proposal.py` | 既存のテスト | `test-build-proposal.py` の既存ケース |

生成物: なし（`gantt.svg` は `build-proposal.py` が生成し commit されない。図の書き出し（drawio）は触らない）。
確かめていないこと（受入基準の外。未証明・BLOCKED には数えない）: PowerPoint で開けること（LibreOffice でしか描画していない。PowerPoint.app は手元にあるが、不在の周では GUI を起こさない）・利用者の実案件の正本での見え方。

## 既知の限界・決着済みの論点

関門に毎パス渡す。論点・決着・理由の 3 つ。**決着の理由が誤っていると判断したなら、それは新しい反証である。**

- **文字の寸法は見積りで、描画と合わない（採った）**: 全角 1 em・半角 0.55〜0.62 em・行の高さ 1.42 倍で見積もり、折り返しの幅に 0.94 の余裕を掛ける。実描画（LibreOffice）は見積りより余裕がある（カードの 7 割ほど）。理由: PowerPoint の日本語のフォントは行間が広いので、LibreOffice に合わせず余裕を持たせた。確かめるのは `check-pptx-render.py` と目。
- **PowerPoint で開けることは確かめていない（受入基準の外）**: 描画したのは LibreOffice だけ。XML の整形式と部品の揃いは見る。
- **図の画像の中の文字は機械では見えない（採った）**: `Text is not SVG` は変換の入力から消す（テストで確認）が、PNG になった後の画素は `check-pptx-render.py` では読めない。理由: OCR を足さない。1 ページずつの PNG を目で見る手順にした。
- **`rsvg-convert` が無いと図を載せない（採った。H4）**: 載せていないことをスライドと標準エラーに書く。理由: 図が無いことと PPTX が作れないことは別。
- **範囲を決めた質問の既定の選び方は推測の規則（採った。H3）**: `scope.md` を指す反映済みの行か、質問が `範囲|作らない|対象外|スコープ` を含む行。多く当たれば枚が増える。理由: 印の列が無い。
- **`markdown_slides` は使わなくなったが残す（採った）**: レビュー会の資料の部品として `test-qa-to-pptx.py` が見ている。消すと別の周の範囲に入る。
- **差し替えスクリプトの中身は見ない（採らない）**: 材料を渡して 2 本が揃うことだけを見る。スクリプトは利用者の権限で走るので、渡すのは `CLAUDE.md` に書かれたものだけ。
- **手書き部分の長さは目安で、機械では見ない（採った）**: 超えるとカードの文字が小さくなるか枚が分かれる。理由: 長さの上限を決めると手書き部分の内容を機械が拒むことになる。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1289-proposal-pptx-readable`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1289`・起点 `45640c38`・base `origin/main` → `45640c3864b95f052346a506558162b3c82a090c`
- 割り目（手順 4・6）: 割らない（cruise の周）。
- 実装のコミット: `446146f06515e036aeab69cc5e7b36c135154c3f`（1 パス目の 2 つの関門に渡す起点）。**1 パス目の指摘対応の起点**: `446146f06515e036aeab69cc5e7b36c135154c3f`。
- 実機の確かめ（LibreOffice 25.x・rsvg-convert・poppler が手元にある）: 合成の正本（Q&A 120 件・費用 14 行・工程 14 行・図 20 枚）から `build-proposal.py --pptx` で作り、`check-pptx-render.py` が 0 件（見切れ・代わりの文字・はみ出し）。
  `decisions.xlsx` は LibreOffice で CSV に変換して 120 件（`soffice --convert-to csv`）。1 ページずつの PNG を目で見た（費用・期間・図・概要）。
- 交絡を潰した手順: 描画の確かめの陽性対照を取った——わざとはみ出す・重なる・省略記号の枚（`bad.pptx`）では 6 件見つかり、収まる枚では 0 件。「0 件」が検査の空振りでないことを、
  同じ観測点で「出る」ほうを 1 度見せて確かめた。図の `Text is not SVG` は、PNG にした後の画素を機械では読めないので、変換の入力から消えること（偽の `rsvg-convert` が受けた入力）と目で見ることで確かめた。

- この周の起票: 0 件（周の中で起票するものは無い。不在の線の `仕様の穴` の確認の Issue（H1〜H5）は親が立てる）
