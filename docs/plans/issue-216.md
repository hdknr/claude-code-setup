# #216 spec-loop 段 1: req-loop スキル（Q&A 起票と PPTX 生成）

親は #214（段 1）。前提の段 0 は #215（PR #223 でマージ済み）。

## 決めたこと

- **PPTX の生成手段: 標準ライブラリだけのスクリプト**（2026-10-13、人間が選択）。
  `plugins/spec-loop/scripts/qa-to-pptx.py`。`zipfile` と XML 文字列だけで書く。
  出力のバイトが入力だけで決まる（zip の時刻を固定）ので、回帰テストで当てられる。
  **対象リポジトリの `CLAUDE.md` がスライドの形式を指定していれば、そちらに従う**（スキル本文）。
- **スキルから plugin 直下を指す形: `../../references/…` `../../scripts/…`**。
  `check-skill-pointers.py` を広げ、`../` で始まる指し先もスキルのディレクトリから解決する。
  **ただしプラグインのディレクトリの外へ出る指し先は落とす**（対象リポジトリの `scripts/` を
  指したつもりの誤りを拾うため）。
- **列の定数は増やさない**——PPTX のスクリプトは `check-qa-csv.py` を `importlib` で読み込み、
  その定数と検査をそのまま使う（写しを 2 つにしない）。
- **`req-loop` は素のスキルとしては張れない**——`../../` が symlink の先で壊れる。
  `link-skills.sh` は `plugins/<name>/skills/<name>` しか張らない（`spec-loop/skills/req-loop` は
  名前が違う）ので、**いまの実装では張られない**。README に「プラグインとしてだけ使う」と書く。

## 1. 変更範囲

触る:

- `plugins/spec-loop/skills/req-loop/SKILL.md` — 本体
- `plugins/spec-loop/scripts/qa-to-pptx.py` — PPTX の生成（標準ライブラリのみ）
- `plugins/spec-loop/references/` — 段 1 で分かったデータの決まりの変更（スライドの置き場所）
- `plugins/spec-loop/README.md` — スキルの節・中身の表
- `plugins/spec-loop/.claude-plugin/plugin.json` — version・description
- `.claude-plugin/marketplace.json` — 同上
- `scripts/check-skill-pointers.py` — `../` の指し先を解決する
- `scripts/test-check-skill-pointers.py` — 上の回帰テスト
- `scripts/test-qa-to-pptx.py` — PPTX 生成の回帰テスト（本体は plugin の中）
- `scripts/check-all.py` — 上のテストの登録
- `.github/workflows/plugins.yml` — 上のテストのステップ
- `docs/plugins/index.md` — spec-loop の節と冒頭の一覧表
- `docs/part3-post-setup.md` — プラグイン一覧の表（「スキルはまだ無い」）
- `docs/usage/advanced-extensions.md` — 配布しているプラグインの列挙（「準備中」）
- `CLAUDE.md` — プロジェクト構成への追記
- `docs/plans/issue-216.md` — この計画

触らない:

- `plugins/dev-loop/` 一切
- 他のスキル（`spec-review` 以降は段 2〜4）
- `scripts/link-skills.sh`——`req-loop` は名前の規則で最初から対象外（上の「決めたこと」）
- `scripts/check-norm-markers.py`——spec-loop は `（必須）` を使わない（I9）

## 2. デプロイ経路

- `docs/` → main への merge で GitHub Pages（`docs.yml`）
- プラグイン → merge 後、利用者が `claude plugin marketplace update` → `claude plugin update spec-loop@claude-code-setup`

## 3. 受入基準

### Issue の受入基準との対応

| Issue の受入基準 | 下の不変条件 |
| --- | --- |
| 回答待ちで止まり、回答を推測で埋めない | B1・B2 |
| 別セッションで再実行すると `qa.csv` の状態から続きを始める | B3 |
| 実行後の `qa.csv` が段 0 の列検査を通る | B4 |
| 生成した PPTX が開け、確認中の質問がすべて載っている | P1〜P5 |
| データの決まりの変更を `references/` に反映した（または変更なし） | R1 |

### 不変条件 × 経路

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| B1 | **スキルは `回答` 列を推測で埋めない** | 会話の文脈・仕様書・「よくある答え」から回答を補う／選択肢の 1 つを既定として書く | 本文で「`回答` に書けるのは人間が書いたものか、会話で人間が明示した回答の転記（誰が答えたか付き）だけ」と規定。**実機（`claude -p`）で、回答の無い表に対して `未回答` のまま止まることを観測** |
| B2 | **1 回の実行は、選択肢付きの質問をそろえたところで止まる** | PPTX を出したあと回答を待たずに反映へ進む／質問を選択肢なしで起票する | 本文の手順の最後を「止まる」にする。選択肢の書式は `check-qa-csv.py` が落とす（B4） |
| B3 | **再開点は会話ではなく `qa.csv` の `状態`（と `回答`）から読む** | 前回の会話を前提にする／別の作業メモに状態を持つ | 本文で再開点の判定を表の状態だけで書く。**実機で、回答を書き込んだ表を新しいセッションに渡し、反映から始めることを観測** |
| B4 | **実行後の `qa.csv` が列検査を通る** | 起票の書式誤り（選択肢・番号の重複・`反映済み` なのに `反映先` が `—`） | 本文で、PPTX 生成の前に検査を走らせ、0 で終わるまで進まないと規定。PPTX のスクリプト自体も検査を通らない表を拒否する（P4） |
| P1 | 生成した PPTX が開ける | OOXML の部品の欠落・参照の誤り・XML として壊れた文字（`&` `<` 制御文字） | LibreOffice（`soffice --headless --convert-to pdf`）で変換でき、ページ数が合う。**PowerPoint（macOS）で開いてスライド数を数える**。テストは zip の部品と XML の整形式を当てる |
| P2 | **`状態` が `確認中` の行がすべて載り、`反映済み` は載らない** | 絞り込みの誤り・回答済み未反映（`確認中` で `回答` あり）の取りこぼし | 回帰テストで、各行の `No` と質問がスライドの XML に現れること／`反映済み` が現れないことを当てる（変異テスト付き） |
| P3 | 選択肢がすべて載る | 区切りの分割誤り | 回帰テストで各選択肢の文を当てる |
| P4 | 列検査を通らない表から PPTX を作らない | 検査を飛ばして生成する | 非ゼロで終わり、出力を作らない（既存の出力も壊さない）。回帰テストで当てる |
| P5 | 出力が入力だけで決まる | zip の時刻・辞書順 | 同じ入力から 2 回作ってバイト一致。回帰テスト |
| P6 | 対象リポジトリで単体で動く | 標準ライブラリ外への依存・このリポジトリへの依存 | 標準ライブラリのみ。リポジトリの外の一時ディレクトリから `python3 -I` で走らせる |
| S1 | 版が 3 箇所で一致（`marketplace.json`・`plugin.json`・`SKILL.md` のバナー 2 行） | 片方だけ上げる | `check-plugin-versions.py` |
| S2 | description の共変 | 3 箇所のどれかを置き去りにする | `check-description-sync.py` |
| S3 | **スキルの中の指し先が実在する**（plugin 直下を含む） | `../../references/qa-csv.md` の綴り誤り・プラグインの外を指す | 広げた `check-skill-pointers.py`。回帰テストに陽性・陰性・外へ出る形を足し、変異で赤 |
| I3 | **データの決まりは `references/` の 1 箇所だけ** | `SKILL.md`・README・スクリプトの docstring に列・状態・起票元の列挙を写す | 本文は `../../references/` を指すだけ。PPTX スクリプトは定数を `check-qa-csv.py` から読む。`SKILL.md` を列名で引いて列挙が無いことを見る |
| T1 | テストが CI と `check-all.py` の両方に載る | 片方だけ登録 | `test-check-all.py` |
| D1 | 公開ページが壊れない | 見出し・リンク | `mkdocs build --strict`・`check-site-links.py` |
| D2 | **「spec-loop はスキルを持たない」と書いた箇所が残らない** | 列挙の直し漏れ | `spec-loop` と「スキルはまだ」「準備中」「持たない」で引き、当たった箇所を全部見る |
| I9 | 必須マーカーを使わない | `SKILL.md` に `（必須）` | `check-norm-markers.py` |
| R1 | 段 1 で分かった決まりの変更が `references/` にある | スキル本文にだけ書く | スライドの置き場所（`shared/` に置かない）を `references/tree.md` に足す |

### 必須要件の掛け算

受入基準 × {Verifier, `/code-review`} × {1 パス目, 2 パス目} の 4 つの受け渡し。

### この環境では証明できないもの（未証明）

- **Windows の PowerPoint で開けること**——手元は macOS の PowerPoint と LibreOffice だけ。
- **B1〜B3 の振る舞いが毎回そうなること**——`claude -p` の観測は 1 回ごとの標本で、
  確率的な振る舞いの「常に」は証明できない。
- **レビュー会の資料として役に立つこと**——実際のレビュー会を回すまで分からない。

### 生成物

**生成物なし。** 図（`diagrams/`）は触らない。`skill-metrics.py` は dev-loop の `SKILL.md` だけを
測るので、`req-loop` の `SKILL.md` は対象外。PPTX はスキルが実行時に作るもので、リポジトリの生成物ではない。

### 周の大きさ（同じことを述べている箇所の数）

- **spec-loop が何を持つか**（「スキルはまだ無い」）: `marketplace.json`・`plugin.json`・
  `README.md`・`docs/plugins/index.md`（表と警告の 2 か所）・`docs/part3-post-setup.md`・
  `docs/usage/advanced-extensions.md`・`CLAUDE.md` の **7 箇所**。
  分けない理由: どれも「スキルを持たない」という同じ 1 文の更新で、分けると片方の周の間だけ偽になる。
- **req-loop の要約**: frontmatter と上の 2 つの JSON の **3 箇所**（揃えるのは値ではなく更新のタイミング）。
- **列の定義**: 段 0 のまま `references/qa-csv.md` と検査の定数の 2 箇所。**この周では増やさない**。

## 4. 未解決の判断・確認待ち

- なし（PPTX の生成手段は上で決着）

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/216-req-loop-skill`／worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-216`／
  起点 `210079b`／base の参照 `origin/main`、SHA `210079b24c8925916132f4446b0db33a6b93cc94`
- 実装: 完了（コミット済み）。`check-all.py` 32/32 緑、PR 限定の 3 本も実差分で緑、`mkdocs build --strict` 緑
- **手順 4 の割り目**: AskUserQuestion で訊いた（2026-10-13）→ **「ここで割る」が選ばれた**
- 次にすること: **手順 5（Verifier 1 パス目）と、B1〜B3 の実機観測（`claude -p --plugin-dir`）**
  ——再開したら、この worktree の中で `/dev-loop:dev-loop 216`
- 実装中の観測（実験ではなく動作確認）:
    - LibreOffice（`soffice --headless --convert-to pdf`）で見本の PPTX が 5 ページに変換された（表紙・一覧・3 問）
    - **PowerPoint（macOS）**: 自分では開けなかった（サンドボックスの「ファイル アクセスを許可」
      ダイアログで止まり、コンテナへの複製も macOS のプライバシー保護で拒否された）。
      **利用者が `~/Downloads/req-loop-sample-216.pptx` を手で開き、「5 枚・修復の確認なし」と回答した**（2026-10-13）。
      見本は `references/qa-csv.md` の例（確認中 2 件）に、特殊文字と制御文字を含む確認中 1 件を足した表から作った
    - 見本の生成は修正前の版（`splitlines` を使っていた版）ではなく、**修正後の版**で作り直したもの
- 関門: 未着手
- 反証・差し戻し: なし
- 交絡を潰した手順: まだ（`test-qa-to-pptx.py` の変異 8 件は、それぞれ狙った観測で落ちることを確かめた
  ——「列検査を飛ばす」は最初、無関係な観測の例外で落ちていたので、観測を分けて直した）

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| PPTX の見た目が素朴 | 採った（限界として残す） | 標準ライブラリだけで書くことを人間が選んだ。形式の指定は対象リポジトリの `CLAUDE.md` に任せる |
| `req-loop` を素のスキルとして張れない | 採った（限界として残す） | `../../` の指し先が symlink の先で壊れる。`link-skills.sh` は名前の規則で最初から張らない |
| `check-skill-pointers.py` は `../` の指し先が「プラグインの中」にあることまでしか見ない | 採った | 指し先の中身が正しいかは、既存と同じく見ない |
