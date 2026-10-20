# Issue #266: spec-loop — 正本リポジトリに MkDocs の設定を既定で用意する

親: #214。

## 変更範囲

触る:

- `plugins/spec-loop/templates/mkdocs/` — 新規。雛形（`mkdocs.yml`・`pyproject.toml`・`gitignore`・`hooks/spec_loop_pages.py`・`docs/index.md`・`docs/qa.md`）
- `plugins/spec-loop/scripts/init-mkdocs.py` — 新規。雛形を正本リポジトリへ写す（無いファイルだけ。上書きしない）
- `plugins/spec-loop/references/tree.md` — ツリーに表示用のファイルを足し、「プロジェクトに任せること」を「既定は MkDocs」に改める
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 「はじめに」で、設定が無ければ写す
- `plugins/spec-loop/skills/*/SKILL.md` — 版のバナー（5 本）
- `plugins/spec-loop/README.md` — スクリプトの表・雛形
- `plugins/spec-loop/.claude-plugin/plugin.json` — 0.10.0
- `.claude-plugin/marketplace.json` — spec-loop 0.10.0
- `scripts/test-init-mkdocs.py` — 新規（写し方とフックのテスト。変異テストを含む）
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 同上
- `CLAUDE.md` — プロジェクト構成（雛形・スクリプト・テスト）
- `docs/plans/issue-266.md` — この計画

触らない:

- 質問ごとの補足（`docs/qa-notes/<No>.md`）——サインオフで比べる範囲に入れるかが未決（人間の判断。2026-10-20 に「今回は入れない」と回答）
- `decision_table.csv`・`nfr.csv`・`feasibility/*.csv` の表示——フックは「印 → 描画関数」の表にして足せる形にするが、描画関数は Q&A だけ（同上の回答）
- `req-loop` 以外のスキルから雛形を写すこと——Issue は「まずは req-loop」
- plugin の description（JSON 2 箇所・frontmatter）——起動の判断は変わらない
- `check-qa-csv.py`・`merge-versions.py` ほか既存スクリプト——表示用のファイルは `docs/` の版の外（`docs/qa.md`）に置き、既存の読み方（`v<n>` 以外の名前は版として読まない）に乗る

**周の大きさ（同じことを述べている箇所）**: 「既定は MkDocs・雛形の写し方」は `tree.md`（正）・`req-loop` の SKILL.md（指し先とコマンド）・
`init-mkdocs.py` の docstring・README・CLAUDE.md の **約 5 箇所**。Q&A の列名はフックと `check-qa-csv.py` の **2 箇所**（フックは正本リポジトリへ写されて
単独で動くので import できない。テストで突き合わせる）。**分けない**: 雛形・写し方・決まりは 1 つの機能で、別々に入れると「決まりはあるが雛形が無い」状態ができる。

## 決めたこと

1. **写すのは同梱のスクリプト**（`init-mkdocs.py [<正本リポジトリの根>] [--dry-run]`）。
   - **`mkdocs.yml` が既にあれば何も写さない**（プロジェクトの設定が先にある）。
   - 無ければ、雛形のファイルのうち**行き先に無いものだけ**を写す。在るもの（`pyproject.toml`・`.gitignore` など）は触らず、
     足りないもの（依存・無視する行）を出力で示す。行き先がシンボリックリンクでも「在る」とみなす。排他的に作る（`x` モード）。
   - 終了コード: 0 写した／写すものが無い・2 根がディレクトリでない・雛形が読めない。
2. **表示用のページは `shared/` の外**（`docs/index.md`・`docs/qa.md`）。サインオフで比べる範囲（`shared/`）に表示用のファイルを混ぜない。
3. **版ごとに節を分ける**: `docs/qa.md` の印 `<!-- spec-loop: qa -->` を、`docs/v<n>/shared/qa.csv` ごとの節（`## v<n>`）に展開する。
   重ね合わせない（v2 で問い直した行は v2 の節にも出る）。アンカーは `v<n>-q-001`（版をまたいで一意）。nav は書かず自動に任せる。
4. **フック**（標準ライブラリだけ・`on_page_markdown`）: 印 → 描画関数の表（今は `qa` だけ）。各節は件数・一覧（`No`・`質問`・`回答`・`状態`）・
   質問ごとの詳細（選択肢の箇条書き・回答／反映先／状態／起票元の表・費用への影響があれば admonition）。
   表の見出しが列名と違う・読めない・知らない印は、**警告（`mkdocs` のロガー）と、ページ上の注意書き**——`--strict` で落ちる。
5. **MkDocs は `<2` に固定**（2.0 は非互換の予告）。依存は `mkdocs`・`mkdocs-material` だけ（table-reader は使わない）。

## verify の受入基準

不変条件 × それを破りうる経路:

| # | 不変条件 | 破りうる経路 | 守り方 | 確かめ方 |
| --- | --- | --- | --- | --- |
| A | 既にあるファイルを 1 つも書き換えない | `mkdocs.yml` が在る／他の雛形ファイルが在る／行き先がシンボリックリンク（壊れたリンクを含む）／存在確認と書き込みの間に作られる／`--dry-run` | `mkdocs.yml` があれば全部写さない・`lexists`・`x` モード | テスト（試料＋変異）。バイト一致で確かめる |
| B | 雛形だけで閲覧できる | 空の正本リポジトリ（`docs/v1/shared/qa.csv` だけ）に写して `mkdocs build --strict` | 雛形の中身 | **実機**: 一時ディレクトリで `uv` で依存を入れて build し、出力の HTML に表が出ることを見る |
| C | Q&A 表の行をすべて、版ごとに、壊さずに描く | 複数の版／同じ `No` が v1 と v2 に／`|`・改行・`<` `&`・Markdown の記号を含むセル／空の `費用への影響`（`nan` を出さない）／見出しが違う・読めない表／表が 1 つも無い／知らない印／印が無いページ | 描画関数・エスケープ・警告 | テスト（試料＋変異）＋ B の実機の HTML |
| D | サインオフの比べる範囲・重ね合わせが変わらない | `docs/index.md`・`docs/qa.md`・`hooks/` を置いた正本で `merge-versions.py`・`check-signoff.py` | 版の外に置く | 実機: 雛形を写した試料で `merge-versions.py` が 0 で、出力に表示用のファイルが入らない |
| E | フックの列名が `check-qa-csv.py` の列と同じ | 片方だけ列を変える | テストで突き合わせる | テスト |
| F | 決まりの原本は `tree.md` だけ。スキルは指すだけ | `req-loop` の SKILL.md・README・CLAUDE.md に決まりを書き写す | 指し先の形 | 目視・`check-skill-pointers.py`・`check-duplicate-counts.py` |
| G | 版（3 種）を上げ、歯止めが全部緑・新しいテストが CI と `check-all.py` に載る | 登録漏れ・版の据え置き | — | `check-all.py`・PR の `gh pr checks` |

掛け算: 受入基準を Verifier と `/code-review` の両方 × 1 パス目・2 パス目（4 つの受け渡し）。

**この環境では証明できないもの（未証明）**:

- `mkdocs serve` の livereload の挙動（フックの変更が再起動まで効かない、など）——Issue のコメントの観測で、雛形はそれに依らない
- Material のテーマでの見た目（幅・折り返し）——HTML の構造までは見るが、ブラウザでの見え方は人間が見る

**生成物**: このリポジトリで再生成するものは**該当なし**（図の書き出し無し。`skill-metrics.py` の対象は dev-loop の `SKILL.md` だけで、
触らない——`check-all.py` が `--check` を回す）。雛形が正本リポジトリに作る `site/` は正本の生成物で、雛形の `.gitignore` が除く。

## 未解決の判断・確認待ち

- 質問ごとの補足をサインオフで比べる範囲に入れるか（今回は入れない）
- 他の CSV の描画関数（別の周）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/266-mkdocs-template`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-266`・
  起点 `50b1d1b`・base は `origin/main`（`refs/remotes/origin/HEAD`）の merge-base `50b1d1be2ad0efd20726333e712a4b91dcfccc0a`
- 実装: `cd952c6` で完了（手順 4）。`check-all.py` 44/44 緑。次は手順 5（Verifier 1 パス目）
- 関門: まだ通していない
- 反証・差し戻し: なし
- 交絡: 実装中に B を 1 回だけ回した（一時ディレクトリで写して `uv sync`・`mkdocs build --strict` が 0、`qa.html` に v1・v2 の節と表）。
  **陽性対照（壊れた表で `--strict` が落ちること）はまだ取っていない**——手順 5 で取る
- 割り目（手順 4）: 訊いた → **「ここで割る」**（2026-10-20）。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 266`（手順 5 から）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 補足（`qa-notes/`）を入れるか | 採らなかった | サインオフの範囲が未決（人間の回答） |
| 表示を重ね合わせた全体にするか | 採らなかった | 版ごとの節にする（人間の回答）。フックは単独で動く必要があり、重ね合わせを写すと決まりの写しが増える |
| フックの列名の写し | 採った（写す） | フックは正本リポジトリへ写されて単独で動くので import できない。テストで突き合わせる |
