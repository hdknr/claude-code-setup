# #215 spec-loop 段 0: 骨組みとデータの決まり（references/）

親は #214。設計の出所は 2 本の記事
（[構成案](https://hdknr.github.io/blogs/posts/2026/10/spec-loop-plugin/)・
[要求仕様書作成ループ](https://hdknr.github.io/blogs/posts/2026/10/requirements-spec-loop/)）。
**データの決まりの具体形（`Q-001` の番号・`A: … / B: …` の選択肢・`未回答` と `—`）は、
後者の記事の Q&A 表の例から取った。**

## 1. 変更範囲

触る:

- `plugins/spec-loop/` — 骨組み・`references/`・`scripts/check-qa-csv.py`
- `.claude-plugin/marketplace.json` — spec-loop の登録
- `scripts/test-check-qa-csv.py` — 列検査の回帰テスト（本体は plugin の中。`test-find-cycle.py` と同じ形）
- `scripts/check-all.py` — 上のテストの登録
- `.github/workflows/plugins.yml` — 上のテストのステップ
- `docs/plugins/index.md` — spec-loop の節と冒頭の一覧表
- `docs/part3-post-setup.md` — 「次のプラグインをインストールできます」の表（**実装中に広げた**。全件を列挙すると名乗る表なので、載せないと偽になる。install の行は足さない——使える能力がまだ無い）
- `docs/usage/advanced-extensions.md` — 配布しているプラグインの列挙（同上の理由で広げた）
- `CLAUDE.md` — プロジェクト構成への追記

触らない:

- `README.md`（ルート）——plugin を列挙していない（I11 の `orca` の引きで当たらなかった）

- `plugins/dev-loop/` 一切（差し戻しの規定は段 4 = #219）
- スキル（`skills/`）——段 1 以降
- 既存の歯止め（`check-*.py`）の拡張——**段 0 にはスキルが無いので、広げる対象が無い**（下の 4）

## 2. デプロイ経路

- `docs/` の変更 → main への merge で GitHub Pages に反映（`docs.yml`）
- プラグインのカタログ → merge 後、利用者が `claude plugin marketplace update` → `claude plugin install spec-loop@claude-code-setup`

## 3. 受入基準

### 不変条件 × 経路

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| I1 | 版が `plugin.json` と `marketplace.json` で一致し、カタログに載っている | 片方だけ書く／載せ忘れる | `check-plugin-versions.py`（取りこぼし検査を含む） |
| I2 | description が 2 箇所で一致（SKILL.md が無いので 2 箇所） | 片方だけ書く | 同じ値を書き、`check-description-sync.py` |
| I3 | **データの決まり（ツリー・列・状態・タグの命名）が `references/` の 1 箇所だけにある** | README・公開ページ・`CLAUDE.md`・カタログの description・検査スクリプトの docstring に列挙を写す | 他の箇所は `references/` を指すだけ。**検査スクリプトの列の定数だけは写しが避けられない**ので、**回帰テストが `references/qa-csv.md` の表と定数の一致を当てる**（I3a） |
| I4 | 列検査が、決まりに反する `qa.csv` で非ゼロ終了する | 列の欠落・順序違い・余分な列・行の列数違い・空ファイル・BOM・番号の書式／重複・未知の起票元・選択肢 2 つ未満・未知の状態・`反映済み` なのに回答／反映先が無い・必須セルの空 | 回帰テストで 1 種類ずつ当て、**変異（検査を 1 つ外す）で赤になる**ことを確かめる |
| I5 | 列検査が、決まりどおりの `qa.csv` を通す（陽性対照） | 検査が厳しすぎて記事の例すら落とす | 記事の Q-001〜Q-006 を決まりに合わせた試料を緑で通す |
| I6 | 列検査が対象リポジトリで単体で動く | 標準ライブラリ外への依存・このリポジトリへの依存 | 標準ライブラリのみ。リポジトリの外の一時ディレクトリから `python3 -I` で走らせて確かめる |
| I7 | テストが CI と `check-all.py` の両方に載っている | 片方だけ登録する | `test-check-all.py` |
| I8 | プラグインとして読み込める | マニフェストの誤り・スキルが 0 本のプラグインを読めない | `claude plugin validate`。一時 `HOME` にローカルのマーケットプレイスを足して install し、`claude plugin list --json` に `spec-loop` と版が出る |
| I9 | 公開ページが壊れない | 見出し・リンクの誤り | `mkdocs build --strict`・`check-site-links.py` |
| I11 | **配布しているプラグインを全件列挙すると名乗る箇所が、spec-loop を含む**（実装中に広げた） | 列挙を持つページの追記漏れ | `docs/` と `README.md` を `orca` で引き（全プラグインを列挙する箇所は必ず orca を含む）、当たった箇所を全部見る |
| I10 | 必須マーカーを使わない | `references/` に `（必須）` を書く | `check-norm-markers.py`（原本は dev-loop だけ） |

### 必須要件の掛け算

受入基準 × {Verifier, `/code-review`} × {1 パス目, 2 パス目} の 4 つの受け渡し。

### この環境では証明できないもの（未証明）

- **GitHub の main から install できること**——merge 前は main に無い。**merge 後に手順 7 で確かめる。**
- **決まりが段 1 の `req-loop` の用途に足りること**——段 1 を回すまで分からない（#214 は「段 2 の前に見直す」としている）。

### BLOCKED

- **I8 のうち、ローカルのマーケットプレイス経由で install できること**——無いのは**権限**（このセッションでは一時 `HOME` の `claude plugin marketplace add` がガードに拒否される）。**別の端末なら回せる**（1 パス目の Verifier の指摘で未証明から移した）。次善として回したのは `claude plugin validate` と `--plugin-dir` の `plugin details` まで。

### 生成物

**生成物なし。** 図（`diagrams/`）と `SKILL.md` の測定値（`skill-metrics.py` は dev-loop の `SKILL.md` だけを測る）は、この周では触らない。鮮度の歯止めが緑のままであることだけ見る。

### 周の大きさ（同じことを述べている箇所の数）

- **spec-loop が何であるか**: `marketplace.json`・`plugin.json`・`README.md`・`docs/plugins/index.md`・`CLAUDE.md` の **5 箇所**。分けない理由: カタログの 2 つは同値（I2）で、残り 3 つは 1 文の要約と `references/` への指し先しか持たせない。
- **列の定義**: `references/qa-csv.md` と検査スクリプトの定数の **2 箇所**。テスト（I3a）で縛る。

## 4. 未解決の判断・確認待ち

- **スキルから plugin 直下の `references/` を指す形**——`check-skill-pointers.py` は `plugins/*/skills/*/` の中しか解決しない。段 1 で `req-loop` が `../../references/qa-csv.md` を指すときに、歯止めを広げるか指し方を変えるかを決める（#216）。
- **`check-norm-markers.py` の原本が dev-loop 単数**——spec-loop がマーカーを使うなら一般化が要る。段 0 では使わない（I10）。

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/215-spec-loop-skeleton`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-215`・起点 `2639705`・base の参照 `origin/main`・**base `2639705e510c25f0a73c586244f692fb0695f28c`**
- **実装**: コミット済み（`feat(spec-loop): 骨組みとデータの決まり…`）
- **著者の確認**（関門ではない）:
    - `scripts/test-check-qa-csv.py` — 試料 26 件・変異 18 件 OK。**変異ごとに「殺すはずの試料」を名指しし、その試料が期待どおりでなくなることまで見る**
    - `claude plugin validate plugins/spec-loop` / `claude plugin validate .` — passed（README に install 行が無いという助言だけ）
    - `claude --plugin-dir plugins/spec-loop plugin details spec-loop` — `spec-loop 0.1.0`・Skills (0)。**陽性対照**: 同じコマンドを dev-loop に当てると Skills (1)・Agents (1)
    - `uv run mkdocs build --strict` — exit 0・警告 0
- **I8 の install の確認は、計画した形では回せなかった**——一時 `HOME` で `claude plugin marketplace add` を走らせる形は、worktree 隔離のガードに「HOME を差し替えるな」と拒否された。**実環境の `~/.claude` に足すと既存の `claude-code-setup` と衝突する**ので走らせていない。代わりに上の `--plugin-dir` で「読み込める」までを確かめた。**マーケットプレイス経由の install は未証明**（merge 後に手順 7 で見る）
    - `python3 scripts/check-all.py` — 31/31 OK（失敗 0 / 飛ばし 0）。1 回目は `check-duplicate-counts.py` が試料名と期待文の件数（選択肢の数）を食い違いとして拾ったので、試料名を変えた（免除は使っていない）。**この経緯の記述自体が同じ形で検査を割った**（1 パス目の V1／CR1）
- **手順 4 の割り目**: 実装完了。**次は手順 5（Verifier 1 パス目）と手順 6（`/code-review` 1 パス目）**。**人間の選択: 「ここで割る」**（AskUserQuestion）。worktree の中で `/clear` → `/dev-loop:dev-loop 215` で手順 5 から再開する
- **関門**: **1 パス目 済**（2026-10-13）。Verifier（`dev-loop:dev-loop-verifier`・`model: sonnet`。起動した体のツールは Read/Bash のみと報告）**反証 2 件**＋分類の指摘 1 件／`/code-review` **指摘 10 件**（V1 と CR1 は同一）。採否は §6 の表
- **反証と差し戻し**: 1 パス目の「直す」7 件で手順 4 に差し戻し（§6 の表）
- **交絡を潰した手順**: `plugin details` の Skills (0) が「読み込めずに 0」でないことを、dev-loop の陽性対照で潰した。変異テストは「別の試料で偶然落ちた」を、殺すはずの試料の名指しで潰した（1 件、`splitlines` の変異が引用符つき改行の試料では**生き残った**——csv が繋ぎ直すため。試料を U+2028 に変え、本体のコメントの誤った主張も直した）

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `references/` の置き場所 | plugin 直下（`plugins/spec-loop/references/`）に置く | 記事の構成案どおり。5 つのスキルが共有するので、どれか 1 つのスキルの中に置くと他が他人の中を指すことになる |
| 版 | `0.1.0` | スキルを 1 本も持たない骨組みで、利用者が使える能力がまだ無い |
| 状態の値 | `確認中`・`反映済み` の 2 つ | 記事どおり。「回答はあるが未反映」は `確認中` ＋ 回答ありで表せる |
| 空のセル | 回答は `未回答`、反映先は `—` と明示させ、空を拒否する | 記事の例がそう書いている。空を許すと「書き忘れ」と「まだ無い」が区別できない |
| 起票元に `開発` を入れる | 入れる | 段 4 で dev-loop が差し戻す。決まりを 1 回で書くため、使う段より先に置く |

### 1 パス目の指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1/CR1 | 計画ファイル 87 行が `check-duplicate-counts.py` を割る（CI 赤） | 示せる（`check-duplicate-counts.py` exit 1 を著者も再現） | I7（CI に載ったステップが赤） | 直す |
| V2 | 番号の「3 桁以上」の境界を試料が縛らない（`\d{3}`・`\d{2,}` の変異が生き残る） | 示せる（Verifier が変異を当てて緑） | I4（番号の書式を 1 種類ずつ当てる） | 直す |
| CR2 | `csv.Error`（128KB 超のセル）が traceback で 1 に落ち、「2 = 検査していない」と区別できない | 示せる（再現） | 無し（I4 の「非ゼロ」は満たす。終了コードの 1/2 の区別は受入基準に無い） | 残課題 |
| CR3a | `反映済み` の判定が `未回答 `（末尾空白）を回答ありと読む | 示せる（再現） | I4（`反映済み` なのに回答が無い） | 直す |
| CR3b | `反映先` に ASCII の `-` を書くと `反映済み` が通る | 示せる（再現） | 無し（`-` が「まだ無い」の意図かは判断で、決まりは `—` だけを定める） | 残課題 |
| CR4 | I3a の突き合わせが列・起票元・状態だけで、`未回答`/`—`/空を許す列/番号の桁/区切りの写しを縛らない | 示せる（表のセルを変えてもテストが緑のまま。直す前に著者が当てて確かめる） | I3（I3a） | 直す |
| CR5 | 選択肢の文に ` / ` を含むと落ちるが、その制約が `references/` に無い | 示せる（再現） | I3（決まりがスクリプトにだけある） | 直す（`qa-csv.md` に書く） |
| CR6 | I5 は記事の Q-001〜Q-006 と言うが、Q-003・Q-004・Q-006 が試料に無い | 示せる（試料と記事の突き合わせ） | I5 | 直す（記事の 6 行を決まりに合わせた試料を足す） |
| CR7 | I4 の経路に「BOM」が非ゼロ側として並ぶが、決まりは BOM を許す | 示せる（計画の文面） | 無し（計画の文面。受入基準を書き換えるのは人間） | 残課題。I4 の「BOM」は「BOM 付きでも見出しを読める」の意で、試料は exit 0 を期待している |
| CR8 | I8 の「Skills (0)＋dev-loop の陽性対照」は読めた／読めないを判別しない | 示せない（推論。走らせていない） | — | 残課題（判別しているのは `spec-loop 0.1.0` の行。Verifier は判別は成立と判定） |
| CR9 | 公開ページに能力の無いプラグインの install 行があり、part3 と食い違う。README の `<base ディレクトリ>` を利用者が埋められない | 示せる（文面） | 無し | 残課題 |
| CR10a | README が `docs/shared/qa.csv` のパスを写している（原本は `tree.md`） | 示せる（文面） | I3 | 直す（README は `tree.md` を指す） |
| CR10b | README が終了コードの意味を docstring から写している | 示せる（文面） | 無し（データの決まりではない） | 残課題 |
| V-分類 | I8 の「マーケットプレイス経由の install」は未証明ではなく BLOCKED（無いのは権限。別端末なら回せる） | — | 分類 | 採る。§3 の BLOCKED に移した。人間の判断を仰ぐ |
