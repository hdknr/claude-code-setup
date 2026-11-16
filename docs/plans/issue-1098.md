# Issue #1098 — spec-loop・screen-spec: MkDocs のフックの登録の口と、版ごとの生成したモック（#1081 段 4）

**不在の周である**——cruise（親 Issue #1081）の子として回す。出所: `/dev-loop:cruise 1081 --absent` の起動（2026-11-16T04:38Z）。
確かめた線（cruise の確かめた線（台帳 `issue-1081`）。出所: 利用者の確認（起動時・2026-11-16、配布を見せて確かめた））:
直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ / 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。実機確認の線は無い。
#1098 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い。`作り直しの元: ` の行も無い）。
この周はマージしない（親がする）——PR を作り、PR 側の CI が通るのを見るところまで。
依存先 #1093（PR #1113）・#1095（PR #1116）は main にマージ済み（`50ce545`）。
承認済みの決めた値: #1104・#1105。推奨で決めて確認待ち: #1109・#1110・#1111・#1114・#1117・#1118——どれも閉じず、閉じるキーワードで指さない。
並行する周: #1094・#1096（screen-spec を触る）・#1097（spec-loop を触る）。版の行が衝突しうる。

## 変更範囲

触る:

- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — 登録の口（`hooks/spec_loop_plugins/*.py` を読み込み、MkDocs のイベントを順に渡す。`mocks` の印に、登録したフックが出すモックの行を足す）
- `plugins/spec-loop/scripts/init-mkdocs.py` — `--hook <ファイル>` でフックを `hooks/spec_loop_plugins/` に登録する（在れば変えない）。登録があるのにフックが口を持たないときに言う
- `plugins/spec-loop/references/tree.md` — 「ドキュメントのツール」に登録の口を書く
- `plugins/spec-loop/README.md` — `init-mkdocs.py` の行に登録の口を足す（要れば）
- `plugins/spec-loop/.claude-plugin/plugin.json`
- `plugins/spec-loop/skills/*/SKILL.md`
- `plugins/screen-spec/templates/mkdocs/screen_spec_pages.py` — 新設。正本に登録する薄いフック（screen-spec を見つけて、本体に渡す）
- `plugins/screen-spec/scripts/mkdocs-pages.py` — 新設。フックの本体（表を仕様書の節に出す・版ごとにモックを生成してサイトに置く・`⚠️` の飾り）
- `plugins/screen-spec/scripts/build-mock.py` — 仕様書へのリンクの作り方を外から渡せるようにする（サイトに置いたモックから、サイトのページを指す）
- `plugins/screen-spec/scripts/write-screens.py` — `mkdocs` の入口（spec-loop の `init-mkdocs.py --hook` で登録する）
- `plugins/screen-spec/references/mkdocs.md` — 新設。フックの決まりの原本（節ごとに出す行と列・モックの置き場所・screen-spec の見つけ方）
- `plugins/screen-spec/references/prose.md` — 「フックは #1098」などの指し先を `mkdocs.md` に（要れば）
- `plugins/screen-spec/references/mock.md` — 「フックは #1098」などの指し先を `mkdocs.md` に（要れば）
- `plugins/screen-spec/references/tables.md` — 「フックは #1098」などの指し先を `mkdocs.md` に（要れば）
- `plugins/screen-spec/skills/init/SKILL.md` — フックを登録する手順（任意の手順）と版の 2 行
- `plugins/screen-spec/skills/add/SKILL.md` — 版の 2 行
- `plugins/screen-spec/README.md`
- `plugins/screen-spec/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` — spec-loop と screen-spec の版、screen-spec の description
- `scripts/test-init-mkdocs.py` — 登録の口の試料と変異
- `scripts/test-screen-spec-pages.py` — 新設。screen-spec のフックの試料と変異
- `scripts/test-build-mock.py` — 足した引数・入口の試料（要れば）
- `scripts/test-write-screens.py` — 足した引数・入口の試料（要れば）
- `scripts/check-all.py` — テストの収録
- `.github/workflows/plugins.yml` — テストの収録
- `CLAUDE.md` — テストの収録
- `docs/plans/issue-1098.md` — この計画

触らない:

- 雛形の `mkdocs.yml`・`docs/mocks.md`・ほかの雛形のファイル（登録の口を使わない案件の出力を変えない）
- spec-loop の関門・scaffold・req-loop（#1097・#1099・#1100）
- モックの差分の印（#1096）・profile（#1094）
- 公開ページ（`docs/plugins/`）——原本は `tree.md`
- `⚠️` の飾りを、表のセルのほかの散文に付けること（下の「決めたこと」）

複製の数: フックの決まりは `references/mkdocs.md`（原本）と `mkdocs-pages.py` の定数（写し）の 2 箇所——テストが突き合わせる。
登録の口の決まりは `tree.md`（原本）と、`spec_loop_pages.py`・`init-mkdocs.py` の定数（写し。ディレクトリの名前）の 3 箇所——テストが突き合わせる。
分けない理由: 写しはどれも 1 つで、テストと `check-plugin-versions.py` が見る。

依存の追加・更新: なし

## 決めたこと（実装で決めてよいもの）

- **登録の口**: 正本の `hooks/spec_loop_plugins/<名前>.py`（spec-loop のフックの隣のディレクトリ）。spec-loop のフック（`mkdocs.yml` が指す 1 本）がそこの Python のファイルを名前の順に読み込み、
  MkDocs のイベント（`on_config`・`on_pre_build`・`on_files`・`on_nav`・`on_page_markdown`・`on_page_content`・`on_post_page`・`on_post_build`）を spec-loop の処理の後に順に渡す。
  どちらのプラグインも `mkdocs.yml` を書き換えない。登録は `init-mkdocs.py --hook <ファイル>` が写す（在れば変えない）。読み込めないファイルは警告して飛ばす。
- **UI モックのページ**: 登録したフックが `spec_loop_mocks(docs_dir)` を持てば、spec-loop の `mocks` の印がその行（版・名前・サイトの中の場所・形式）を版ごとの節に足す——spec-loop は screen-spec の名前を知らない。
- **screen-spec のフック**: 正本に写すのは薄いフック（`screen_spec_pages.py`）で、screen-spec を環境変数 `SCREEN_SPEC_PLUGIN` → Claude Code のプラグインの記録（`installed_plugins.json` の `screen-spec@…`）の順に探し、
  本体（`scripts/mkdocs-pages.py`）に渡す——描き方はプラグインの更新で届く（写し直さない）。見つからなければ警告し（`--strict` で落ちる）、ページに注意書きを置く。
- **表を節に出す**: 版 `v<k>` の `requirements/screens/<slug>.md` の印 `<!-- screen-spec: 表 -->` を、後の版が同じ名前の仕様書を置く手前の版まで重ねた表（その範囲で画面を消した版・重ね合わせの誤った版は飛ばして v<k> まで下へ探す）のうち `仕様書` がそのファイルの画面の行で置き換え、表の上にどの版まで重ねたかを書く（1 パス目の CR1-2・2 パス目の CR2-1〜CR2-7 で変えた）。節ごとの行と列は `references/mkdocs.md`（#1081 の 13 次元の表のとおり）。
  共有の層だけを出す（列は `build-mock.py` の許可の一覧の中・`D-` の番号を外す）。
- **版ごとのモック**: MkDocs のビルドのとき（`on_files`）、表のある版ごとに `build-mock.py` の `build`（`--upto <n>` と同じ）で作り、`<docs の親>/build/mock/v<n>/index.html` に書いて、サイトの `mock/v<n>/index.html` に置く。
  モックの中の仕様書へのリンクは、サイトの仕様書のページを指す。作れなかった版は警告し、モックのページのその版の節に注意書きを置く。
- **`⚠️` の飾り**: フックが出す表のセルのうち、未決定の印（spec-loop の `find_markers`）を含むセルの頭に `⚠️` を付ける——正本には書かない。散文には付けない（散文の書き換えは本文を壊しうる。残課題）。
- **受入基準 4 の「出力」**: `init-mkdocs.py` が出す行・写すファイルの一覧と、フックのほかのファイルのバイト。フック（`spec_loop_pages.py`）は口を持つので中身が変わるが、
  登録の無い案件で描くページは今と同じ（既存の試料がそのまま通る）。

## 決めたこと（仕様の穴。`仕様の穴 = 推奨で決めて起票` の線で推奨により決めた）

- **穴 1: 正本の CI（Claude Code の入っていない環境）で MkDocs をビルドするとき、screen-spec のフックが screen-spec をどう見つけるか**——#1081 は「ビルドのときに生成して載せる」とだけ書き、
  ビルドする環境に screen-spec が無いときを決めていない。
  - 選択肢: A) 環境変数 `SCREEN_SPEC_PLUGIN`（と spec-loop の `SCREEN_SPEC_SPEC_LOOP`）か Claude Code のプラグインの記録から探し、無ければ警告してページに注意書きを置く（CI では claude-code-setup を取得して環境変数で渡す）（推奨）／
    B) 登録のときに screen-spec と spec-loop のスクリプトを正本に写す（写しが古くなる・spec-loop の「写さない」に反する）／ C) モックを手元で生成して commit する（決めること 7 の「commit しない」に反する）
  - 推奨 A。理由: 正本に写すのは探す部分だけになり、描き方と重ね方はプラグインの更新で届く。B は版ごとに写しが食い違い、C は決めること 7 の回答に反する。
- 決めた値は受入基準を足さない（`absent-lines.md`）。確認の Issue は PR を作った後に 1 件立てる。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ。spec-loop と screen-spec の版が上がる）。公開ページ（`docs/`）は触らない。

## 版の上げ方

- spec-loop を minor で上げる（能力の追加。0.x）: main の先端の値（0.94.0）の次 → **0.95.0**。`marketplace.json`・`plugin.json`・`SKILL.md` 7 本の 2 行。
- screen-spec を minor で上げる: main の先端の値（0.3.0）の次 → **0.4.0**。`marketplace.json`・`plugin.json`・`SKILL.md` 2 本の 2 行。
- 並行する #1094・#1096（screen-spec）・#1097（spec-loop）も版を上げうる——親はマージの直前に取り込みを頼む。そのときは main の先端の値から minor で 1 つ上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
  取り込みの後は `check-plugin-versions.py`・`skill-metrics.py --check` だけを回して push し、PR 側の CI を見る（CLAUDE.md の「並行する周は、同じ版に上げて衝突する」の 5）。

## 受入基準（不変条件 × 経路）

入口: `init-mkdocs.py`（空の根・設定が在る根・`--hook`・`--dry-run`・回し直し）、`write-screens.py mkdocs`、MkDocs のビルド（`mkdocs build`・`mkdocs serve`。フックのイベント）、
ページ（`docs/mocks.md` の `mocks` の印・`docs/v<k>/requirements/screens/<slug>.md` の表の印・ほかのページ）。

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| A1 | screen-spec のフックを登録した案件で、`init-mkdocs.py` を回し直しても登録が消えない（バイトも変わらない） | 設定が在る根での回し直し・設定を消した根での回し直し（雛形を写し直す）・`--hook` での回し直し（中身の違うファイル）・`--dry-run` | CI: 登録の後に各形で回し、登録のファイルのバイトを比べる |
| A2 | `docs/mocks.md` に、版ごとの生成したモックへのリンクが出る（手で書いたモックのリンクと並ぶ）。リンクの先がサイトに置かれる | 表のある版・無い版・作れない版（重ね合わせの違反・spec-loop が無い）・手で書いたモックのある版 | CI: spec-loop のフックの雛形と screen-spec のフックを組み、`on_files` → `mocks.md` の `on_page_markdown` を通して見る（偽の `File`）。手元: 本物の `mkdocs build --strict` |
| A3 | 画面の表の行が、仕様書の節に表として出る（節ごとの行と列は `mkdocs.md`。共有の層だけ。`⚠️` は飾りだけ） | 表で持つ 9 つの節・散文の節に置いた印・表に無い仕様書・v2 で変えた・消した行・`D-` の根拠・未決定のセル | CI: フックを直に呼ぶ（`test-init-mkdocs.py` と同じ形）。手元: 本物の `mkdocs build --strict` |
| A4 | 登録の口を使わない案件で、`init-mkdocs.py` の出力（出す行・写すファイルの一覧・フックのほかのファイルのバイト）が今と同じ。フックが描くページも今と同じ | 空の根・設定が在る根・`--dry-run`・在るファイルを残す根 | CI: 出す行と写すファイルを固定の期待値と比べ、既存の試料がそのまま通る。手元: main の `init-mkdocs.py` と出力を比べる |
| A5 | どちらのプラグインも `mkdocs.yml` を書き換えない | `init-mkdocs.py --hook`・`write-screens.py mkdocs`・フックのイベント | CI: 実行の前後で `mkdocs.yml` のバイトが同じ |
| A6 | 登録したフックが読み込めない・screen-spec が見つからないとき、黙って落とさない（警告とページの注意書き） | 構文の誤りのある登録・`SCREEN_SPEC_PLUGIN` が誤り・記録が無い | CI |
| A7 | 本体の定数が原本（`references/mkdocs.md`・`tree.md`）と一致する | 定数 | テストが突き合わせ、崩しで落ちることも見る |
| A8 | 歯止めが全部緑（版 3 種類・description 2 箇所・CI と `check-all.py` への収録・指し先） | `check-plugin-versions.py`・`test-check-all.py` ほか | `check-all.py`（順番待ち越し） |
| X1 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方 × 1・2 パス目に渡す（2 パス目が「該当なし」の周は 1 パス目の 2 つ） | — | 再開点で記録 |

**証明できないもの（未証明）**: 正本の CI（GitHub Actions など、Claude Code の無い環境）で screen-spec を取得して環境変数で渡したビルド——手元の 1 例（環境変数で渡した `mkdocs build`）は回すが、利用者の CI の形はこの環境に無い。
MkDocs 1.6 のほかの版（1.5・2.x）での `File` の作り方——手元の版だけで確かめる。

**生成物**: 生成したモック（`build/`）は commit しない。このリポジトリの生成物（図・`SKILL.md` の測定値）は触らない——`skill-metrics.py --check` で変わらないことを確かめる。

## 実機確認

一時ディレクトリに正本（`docs/v1/`・`docs/v2/`）を置き、`init-mkdocs.py` → `write-screens.py init`・`add` → `write-screens.py mkdocs` で登録し、
このリポジトリの `.venv` の MkDocs（1.6）で `mkdocs build --strict` を走らせて、サイトの `mocks.html`・`mock/v<n>/index.html`・仕様書のページを見る。陽性対照: 登録を外したビルドで表とモックが出ないこと。

## 未解決の判断

- 上の穴 1——確認の Issue で利用者に渡す（閉じるのは利用者）。

## 起票

- この周の起票: 0 件（PR を作った後に穴 1 の確認の Issue を立てたら直す）

## 直す線

`既定`（出所: cruise の確かめた線（台帳 `issue-1081`）。不在の周）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1098-mkdocs-hook-port`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1098`・起点 `50ce545`・base `origin/main` → `50ce54527eb6386c5068202791900cb7bbc9e8d9`
- 割り目（手順 4）: 割らない（cruise の周）
- 実装のコミット: `8b0e9ff`
- 1 パス目の指摘対応の起点: `de025ad`（1 パス目の関門に渡した時点の HEAD。`8b0e9ff` との差は計画ファイルだけ）
- Verifier 1 パス目: 通した——反証 1 件（V1-1。dev-loop:dev-loop-verifier・sonnet。verifier.md を 185 行と報告——`wc -l` と一致）
- `/code-review` 1 パス目: 通した——指摘 10 件（CR1-1〜CR1-10。high。委譲文はファイルに書き、要点を貼った）＋試料の無い決まり 3 件（CR1-U）
- 手順 4 への差し戻し: あり（採否の表の「直す」2 行）
- 割り目（手順 6・2 パス目の前）: 割らない（cruise の周）。残っているのは手順 5 の当て直しと手順 6 の 2 パス目の両方
- check-all（`8b0e9ff`。run-serial 越し）: 88/88 本・失敗 3（`check-description-sync.py`——V1-1・`check-plan-scope.py`——変更範囲の 1 行に 2 つのパターンを書いていた（計画を直した）・`test-intake-code.py`——「このリポジトリの作業ツリーを変えていない」。走っている間に著者が作業ツリーを編集した交絡で、指摘対応の後の check-all で当て直す）
- 1 パス目の指摘対応: `1a79808`（差分は 0 行でない——2 パス目を回す）
- Verifier 2 パス目: 通した——反証 1 件（V2-1。verifier.md を 185 行と報告——一致）
- `/code-review` 2 パス目: 通した——指摘 9 件（CR2-1〜CR2-9。high）
- 2 パス目の指摘対応の起点（狭いパスの起点）: `bbafe57`
- 交絡を潰した手順:
  - 受入基準 4（出力が今と同じ）: main（`50ce545`）の `init-mkdocs.py` とこの周の `init-mkdocs.py` を、空の根・設定が在る根・在るファイルを残す根の `--dry-run` で回し、出す行（根のパスを伏せて）が 3 つとも一致、写したファイルの一覧も一致、違うのはフックのファイルだけ（口の分）。既存の `test-init-mkdocs.py` の試料 71 件（フックが描くページ）も変えずに通った。
  - 本物の MkDocs（このリポジトリの `.venv` の 1.6）で一時の正本を `mkdocs build --strict`: 登録して `SCREEN_SPEC_PLUGIN` を渡すと 0（サイトに `mock/v1/index.html`・`mock/v2/index.html`、`mocks.html` の v1・v2 の節にリンク、仕様書のページの節に表・`⚠️`・`D-` なし、モックの中の仕様書へのリンクは `../../v1/requirements/screens/S-001.html`）。
    陽性対照（同じ正本で前提を外す）: `SCREEN_SPEC_PLUGIN` を外し空の `CLAUDE_CONFIG_DIR` にすると 1（警告 5 件——見つからない・v1・v2 のモック・雛形のリンク）、登録を外すと `site/mock` が無く、仕様書の印は HTML のコメントのまま残る（9 個）。

## 既知の限界・決着済みの論点

- 受入基準 4 の「出力」の読み方（上の「決めたこと」）——フックの雛形は口を持つので中身が変わる。登録の無い案件で描くページと、写すファイルの一覧・出す行は変わらない。
- 既に雛形を写した正本には、口を持つフックは届かない（`init-mkdocs.py` は在るファイルを変えない）——`tree.md` の「Q&A 表を移す」の手順 4 で取り込む。`--hook` で登録したのに口が無ければ `init-mkdocs.py` が言う。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-1 `check-description-sync.py origin/main` が screen-spec で落ちる（add の frontmatter が据え置き） | 示せる（著者が走らせて「同期漏れが 1 件」） | A8 | 直す——add の要約はフックに関わらないので、trailer `Skip-description-sync:` を付ける |
| CR1-1 screen-spec が見つからないときの薄いフックの代わりの置き換えが、コードブロックの中の印も置き換える | 示せる（読んで分かる。走らせていない） | 無し（A6 は注意書きを置くこと。コードブロックの決まりは本体の側） | 残課題 |
| CR1-2 仕様書のページが自分の版までしか重ねないので、仕様書を写さずに表だけ変えた後の版の行がどのページにも出ない | 示せる（試料: v2 に S-002 の行だけを置くと、v1 の order-new.md の節に v2 の値が出なかった——直す前の本体で試料が赤） | A3（v2 で変えた行の経路） | 直す——後の版が同じ名前の仕様書を置く手前の版まで重ねる |
| CR1-3 `--dry-run` の注意の行が、本当に回したときと違う | 示せる（関門が再現） | 無し | 残課題 |
| CR1-4 `write-screens.py mkdocs` に自分の前提の確かめが無い（mkdocs.yml が無ければ spec-loop の雛形を写す・別の MkDocs の設定でも登録して 0） | 示せる（関門が再現） | 無し（A5 は破らない。注意の行は出る） | 残課題 |
| CR1-5 渡す 8 つのイベントのうち 5 つ（on_config・on_pre_build・on_nav・on_page_content・on_post_page）に登録つきの試料が無い | 示せない（試料の穴） | 無し | 残課題 |
| CR1-6 docs が外へのシンボリックリンクだと `relative_to` の ValueError でビルドが落ちる | 示せない（まれな形） | 無し | 残課題 |
| CR1-7 ビルドのたびに build-mock.py の出力（`build/mock/v<n>/index.html`）を、サイト向けのリンクのものに上書きする | 示せる（読んで分かる） | 無し | 残課題 |
| CR1-8 フックが読み込む名前の決まり（`.`・`_` で始まらない `.py`）と init-mkdocs.py の決まり（`[A-Za-z][A-Za-z0-9_]*.py`）が違う | 示せない（手で置いた名前だけ） | 無し | 残課題 |
| CR1-9 `page_url` が README.md の URL を MkDocs と違う形にする（`File.url` を使えばよい） | 示せない（仕様書の名前は `<画面ID>.md`） | 無し | 残課題 |
| CR1-10 本体の読み込みが `sys.dont_write_bytecode` をプロセス全体に掛ける・ビルドのたびに読み直して版を 2 回重ねる | 示せない（性能の推測） | 無し | 残課題 |
| CR1-U 記録の `project` を `user` より先に採る・記録が 2 つ以上なら見つからない・サイトの同じ場所に正本のファイルがあれば置かない、に試料が無い | 示せない（試料の穴） | 無し | 残課題 |

### 2 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-1 CR1-2 の直しの「後の版で画面を消した」代わりの経路に試料が無い | 示せない（現行は正しく動く。試料の穴） | 無し | 残課題——ただし CR2-2 の直しで試料（後の版で消した画面）を足した |
| CR2-1 後の版の重ね合わせの誤りで、前の版の仕様書のページが注意書きになる（1a79808 が持ち込んだ後退） | 示せる（関門が測った: v3 の見出し行の誤りで v1 の order-new のページが「表示できない」） | A3 | 直す——誤った版は飛ばして下の版を探す |
| CR2-2 後の版で画面を消すと、消す手前までの表の変更がどのページにも出ず、黙って v1〜v<k> に戻る | 示せる（関門が測った） | A3（v2 で変えた・消した行） | 直す——上の版から下へ、その画面が在る最後の版を探す |
| CR2-3 同じ名前の仕様書を指す画面が 2 つになると、黙って前の版に戻る | 示せる（関門が測った） | A6 | 直す——2 つ以上なら注意書き |
| CR2-4 代わりの経路に試料と変異が無い | 示せる（関門が `if False:` で 10/10 緑を測った） | 無し（試料の穴） | 残課題——CR2-2・CR2-3 の直しで試料と変異を足した |
| CR2-5 v1 の仕様書のページが v2 以降の値を出すのに、v1 のモックは v1 の値で、どの版の行かの印が無い | 示せる（関門が読んだ） | A3（`⚠️`・行の出し方に紛れ） | 直す——表の上に `（v1〜v<n> を重ねた表の行）` を書く（どちらを出すかの選び方は残課題に名指し） |
| CR2-6 リリースした版のページが、作業中の版の値で書き変わる | 示せる（読んで分かる） | 無し（決まりの選び方） | 残課題——マージ前の判断に載せる（上の印で見分けはつく） |
| CR2-7 後の版が仕様書を置くかを `is_file()` で見るので、大文字小文字を区別しない FS で綴り違いに当たる | 示せない（綴り違いの版は重ね合わせが誤りとして止める——試料では v2 の重ね合わせが壊れた） | 無し | 直した（書いた綴りで比べる。`os.listdir`）——試料は無い（残課題） |
| CR2-8 版 × ページで重ねる回数が増える | 示せない（性能の推測） | 無し | 残課題 |
| CR2-9 計画の「決めたこと」が古い決まりのまま | 示せる | 無し（周の記録） | 直した（計画） |
