# Issue #952 — spec-loop: UI モックの形式（HTML／React）と置き場所の決まりが無い

不在の周（cruise の子）。出所: `/dev-loop:cruise 963 --absent` の起動（2026-11-11T01:02:52Z）。親 Issue #963、台帳 `issue-963`（台帳は親だけが書く）。
従う版は dev-loop 1.103.0（キャッシュ。`SKILL.md` 1861 行——`wc -l`）。依存先 #951（PR #978）はマージ済みで、main（`43ad7fba`）から切った——積んだ周ではない。

- 使った線（出所: cruise の確かめた線（台帳 `issue-963`）——利用者の確認（起動時・2026-11-11T01:02:52Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-963`））
- 版の上げ方: **spec-loop を minor で上げる**（0.80.0 → 0.81.0。0.x なので能力の追加は minor）。dev-loop は触らない。
  `marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行。
  マージの直前に main が進んでいれば、main の先端の spec-loop の版から minor で 1 つ上げた値に上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #952`。確認の Issue は閉じるキーワードで指さない（指すなら `Refs`）。手順 7 のマージは親がする（子は PR と PR 側の CI まで）
- 重い検査は `run-serial.py` 越し（`/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/cruise/scripts/run-serial.py`）
- 割り目（手順 4・手順 6）: **割らない（cruise の周）**——訊かずに続ける

## 周の在り処

- ブランチ: `issue/952-ui-mocks`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-952`
- 起点コミット: `43ad7fba`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `43ad7fbacaf4dd8a16045e39eeb50ff2e2f0bf3b`

## 変更範囲

触る:
- `plugins/spec-loop/references/tree.md` — ツリーに `requirements/mocks/`、「UI モック」の節（形式・置き場所・扱い・見せ方・受け渡し）、仕様書の節にモックのパス、「ドキュメントのツール」に `docs/mocks.md` と `mocks` の印・フックを取り込む版
- `plugins/spec-loop/references/qa-csv.md` — モックを見せて回答をもらった行の書き方の指し先（1 行）
- `plugins/spec-loop/references/spec-ir.md` — `refs` の例のパスを `requirements/mocks/` に揃え、React のモックの指し方の 1 行
- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — `mocks` の印（各版の `requirements/mocks/` のモックへのリンクの一覧）
- `plugins/spec-loop/templates/mkdocs/docs/mocks.md` — 表示用ページ（新規）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/test-init-mkdocs.py` — `mocks` の印の試料・変異、雛形のページ、`tree.md` の照合の語
- `scripts/test-merge-versions.py` — UI モック（HTML と React のディレクトリ）を重ねる試料
- `scripts/test-check-signoff.py` — UI モック（HTML・React の部品）の違いで照合が割れる試料
- `scripts/test-scaffold.py` — 参考資料の試料のパス `REF_MOCK` を `requirements/mocks/` に揃える（中身は変えない）
- `docs/plugins/spec-loop.md` — 公開ページの「図」の隣に UI モックの 1 項（指し先だけ）
- `docs/plans/issue-952.md` — この計画

触らない:
- `init-mkdocs.py`（雛形のディレクトリをそのまま写すので、ページを足すだけで写る）と雛形の `docs/index.md`（決定表・基盤要件のページも載せていない）
- `merge-versions.py`・`check-signoff.py`・`diff-versions.py`・`build-proposal.py`・`scaffold.py` の本体——`requirements/` の下のファイルはもう対象に入っている（試料で確かめて固定する）
- HTML のモックが外部に依存していないかの機械の検査（決まりとして書くだけ）
- React のビルド（`package.json`・バンドラ）——下の「仕様の穴」
- 仕様書（`build-proposal.py`）にモックの専用の節を作ること——「仕様と要求のファイル」にパスが載る
- 規模の「要求・仕様のファイルの数」にモックのファイルが数えられること

複製の数（同じことを述べている箇所）: UI モックの決まりの原本は `tree.md` の「UI モック」1 箇所。ほかは指し先（`qa-csv.md`・`spec-ir.md`・公開ページ・フックの docstring）。
印 `mocks` の名前は フック（`PAGE_RENDERERS`）・雛形のページ・`tree.md` の 3 箇所で、`test-init-mkdocs.py` が雛形のページと `tree.md` を見る。分けない理由: 既存の `infra` の印と同じ形で、増える複製は無い。

## 決めたこと（Issue の「提案」を形にした値）

- 置き場所: 版の中の `requirements/mocks/`。HTML は `requirements/mocks/<画面名>.html`（1 画面 1 ファイル）、React は `requirements/mocks/<画面名>/`（入口の `index.html` とコンポーネントの `.jsx`）。
  `.` で始まる名前は重ね合わせも照合も読まないので置かない。
- HTML: 外部への依存を持たない（CSS・JS・画像を中に書く。`<link>`・`<script src>`・画像の URL で外を読まない）。ブラウザでファイルを直に開いて見られる。
- React: **ビルドしない**——仕様の穴として推奨で決めた（下）。
- 扱い: 参考資料で受入基準ではない。仕様（`spec/`）と食い違ったら仕様の穴として Q&A 表に起票する。レビュー会でモックを見せて回答をもらった行は、`回答` の括弧にモックのパスを書く（`A（業務部が回答。モック requirements/mocks/受注入力.html）`）——列は足さない。
- 見せ方: MkDocs の表示用ページ `docs/mocks.md`（印 `<!-- spec-loop: mocks -->`）が、各版の `requirements/mocks/` のモックへのリンクを版ごとに描く（版は重ね合わせない——Q&A 表と同じ）。
  入口の無い React のディレクトリ・`.html` でないファイルは警告する。
- 仕様書: 「仕様と要求のファイル」にモックのパスが載る（今の `build-proposal.py` のまま）。
- 開発ループへ: scaffold の中間表現の `refs` で指す（#951）。React のモックは入口とソースのファイルをそれぞれ並べる（`refs` はファイルだけを指す）。

## デプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（カタログ・`git pull` して張った利用者）。`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`。
マージは親がする。

## verify の受入基準

不変条件 × 経路（経路は、正本リポジトリの `requirements/` のファイルを読む入口——`merge-versions.py`（と、それで重ねる `scaffold.py`・`diff-versions.py`・`build-proposal.py`）・`check-signoff.py`・MkDocs（`mkdocs build`／`serve`、フック）・`init-mkdocs.py`——から数える）:

- **I1 決まりが書かれている**: `tree.md` に UI モックの形式（HTML／React）と置き場所（版の中の `requirements/mocks/`）、React の見方が書かれている。ツリーの図にも載る。
- **I2 承認の照合と重ね合わせの対象に入る**:
  - 経路: `merge-versions.py`（v1 の HTML・React のディレクトリを重ねる、v2 で React のディレクトリを置き直す（部品の中身が変わる）、`removed.csv` で消す）／`check-signoff.py`（2 つのタグの間で HTML・React の部品が違えば 1）／
    `build-proposal.py`（仕様書の「仕様と要求のファイル」にパスが載る）／`scaffold.py`（`refs` で指せる。#951 の決まりのまま）
  - 守り方: 本体は `requirements/` を丸ごと読むので変えない。試料（`test-merge-versions.py`・`test-check-signoff.py`）で固定する
- **I3 MkDocs のサイトからモックを開ける**:
  - 経路: 雛形の `docs/mocks.md` が `init-mkdocs.py` で空の根に写る／フックの `mocks` の印が各版のモックへのリンクを描く（HTML・React の入口）／
    実際の `mkdocs build` で、リンクが HTML のモックと React の入口に解決し、モックのファイル（`.html`・`.jsx`）がサイトに写る／
    React のモックがサイト（http）で描画される（版を固定した CDN の React と Babel）
  - 警告: 入口の無い React のディレクトリ・`.html` でないファイル・綴りだけ違う `Requirements/`・`Mocks/` は警告して描かない（黙って落とさない）
- **I4 受入基準ではなく参考資料であること、食い違ったら Q&A 表に起票することが書かれている**（`tree.md` の「UI モック」）。モックを根拠として指す書き方も書かれている。
- **I5 版**: spec-loop の版が 3 種類で揃う（`check-plugin-versions.py`）・上がっている（`check-version-bump.py`）
- **掛け算**: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）

未証明: なし（React の描画は headless の Chrome で CDN に繋いで確かめる。繋がらなければ BLOCKED にする）。

生成物: `SKILL.md` の測定値の生成ブロック（`skill-metrics.py --check`）——dev-loop の `SKILL.md` は触らないので変わらない見込み（確かめる）。図の書き出し: 該当なし。`scaffold/`: 該当なし。

## 仕様の穴（不在の線で推奨により決めた）

- 穴: React のモックの見せ方（ビルドの有無・MkDocs から開くか）。Issue は「決める」と書くが、どちらにするかを決めていない。
- 選択肢: **A（推奨）** ビルドしない——`<画面名>/index.html` が版を固定した React・ReactDOM・Babel（ブラウザで JSX を変換する）を CDN から読み、同じディレクトリの `.jsx` を読む。MkDocs のサイト（http）から開く（ファイルを直に開くと `.jsx` を読めない）。`.tsx` は置かない／
  B ビルドする（`package.json` とバンドラを置き、ビルドの出力を版に置くか CI で作る）／ C React は使わず HTML だけにする
- 推した理由: A なら置いたソースがそのまま照合と重ね合わせの対象で、生成物（ビルドの出力）の鮮度を見る仕組みが要らず、MkDocs はファイルをそのまま写すので雛形のほかに何も足さない。
  B はビルドの出力が版に入ると承認の照合の中身が膨らみ、出力を置かないと MkDocs のサイトで見えない。C は Issue の「動きを確かめたい画面」が書けない。
  代償は、見るのにネットワーク（CDN）が要ること・ファイルを直に開いても見えないこと・`.tsx` を使えないこと。
- 使った線と出所: `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線。台帳 `issue-963`）
- 確認の Issue: #984（PR #983 を作った後に立てた）

## 起票

- この周の起票: 1 件（仕様の穴を推奨で決めた確認の Issue #984。起票の承認は不在のため訊いていない）

## 未解決の判断・確認待ち

- 上の仕様の穴（確認の Issue で利用者が確かめる）

## 関門の進捗（再開点）

- 割り目: 割らない（cruise の周）
- 手順 4 の割り目: 割らない（cruise の周）——訊かずに続けた
- 実装のコミット: `d5cff7fd`。ローカルの check-all（run-serial 越し）72/72 緑。`test-init-mkdocs.py` は Python 3.12（CI と同じ）でも緑
- 実機確認（著者）: 雛形を空の根に `init-mkdocs.py` で写し、v1 に HTML のモック（`受注入力.html`）と React のモック（`在庫/index.html`・`Row.jsx`・`App.jsx`）を置いて
  `mkdocs build --strict`（main の venv の MkDocs 1.6.1・Material 9.7.1）が 0。`mocks.html` のリンクが 2 つのモックに解決し、モックのファイルがバイトのまま写る（`cmp`）。
  `use_directory_urls: true` でも `../v1/requirements/mocks/…` に直る。headless の Chrome で、http で配ったサイトの React のモックが描かれる（`在庫 3 件`・`ねじ: 3`。2 つの `.jsx` をまたいで使える）——
  陰性側の対照: 同じ `index.html` を `file://` で開くと `#root` は空（`.jsx` を読まない）。HTML のモックは `file://` で開ける
- 1 パス目の指摘対応の起点: `d5cff7fd`（1 パス目の関門に渡した時点の HEAD）
- Verifier 1 パス目: 通した（base `43ad7fba`。dev-loop:dev-loop-verifier / sonnet。参照＋差分の形で verifier.md と gate-common.md を読ませた）——反証 0 件。`test-scaffold.py` は Verifier の側で時間切れ（未確認。著者の check-all 72/72 では緑）
- `/code-review` 1 パス目: 通した（base `43ad7fba`。high）——指摘 7 件（CR1-1〜CR1-7）。受入基準 I1〜I5 に反する欠陥は無いとの報告
- 1 パス目の指摘対応: 直す 1 件（CR1-1）。check-all（run-serial 越し）は 72 本中 2 本が落ちた——`check-plan-scope.py`（計画の 1 行に 2 つのパターンを書いていた。行を分けて直した）と `test-render-diagrams.py`（変異「プロセスグループを止めない」が生き残った。この周は触っていない時間待ちの試料で、load average 100 超。run-serial 越しに 1 度だけ回し直して緑——負荷による偽の失敗として扱った。両方の結果をここに残す）
- 2 つ目の割り目: 割らない（cruise の周）——訊かずに続けた
- 手順 5 の反証と手順 4 への差し戻し: 反証 0 件・差し戻しなし
- 2 パス目: 通した（base `43ad7fba`。受入基準をまるごと渡した）——Verifier（sonnet）は反証 0 件、`/code-review`（high）は指摘 4 件（CR2-1〜CR2-4）。
  `/code-review` の報告によれば、レビュー中に著者が計画ファイル（確認の Issue と起票の件数の行）を書き換えたので、`git status --porcelain` の 2 回が違った（コード・テストは変わっていない）
- 2 パス目の指摘対応（狭いパスの起点）: `b9f1285f01888737c8eec5824389606d34de2e31`
- 2 パス目の指摘対応の終点: `13597fd445c69bd7abdfd1b4ede17524176d5b38`（直す 1 件 CR2-1。ローカルの check-all 72/72 緑。`test-init-mkdocs.py` は 3.12 でも緑。実際の `mkdocs build --strict` で下のフォルダの跡も警告しないことを確かめた）
- PR #983 を作った時点で main が進んでいて `CONFLICTING`——指摘対応の途中で取り込まないので、狭いパスの終点を書いてから取り込んだ（`7d341dbd`。main の #981 が spec-loop を 0.80.1 に上げていた。版の行だけが衝突し、main の先端 0.80.1 から minor で 1 つ上げた 0.81.0 のまま。取り込みの後は check-plugin-versions.py と skill-metrics.py --check の 2 本だけ——#831）
- 狭いパス: 通した（`git diff b9f1285f 13597fd4`。sonnet。変異は Verifier が設計）——受入基準を破る反証 0 件・試料の穴 2 件（N1・N2）。どちらも記録だけ（下の表）
- 交絡を潰した手順: React の描画の陽性（http で描かれる）と陰性（`file://` で描かれない）を同じ `index.html` で取った——描かれないのが CDN に繋がらないせいでないことは、同じ回の http 側が描いたことで潰した

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 照合・重ね合わせの本体を直すか | 直さない（試料で固定） | `requirements/` の下のファイルはどの種類でも対象に入っている。`.` で始まる名前だけは読まない（`.DS_Store` のため。決まりとして置かないと書く） |
| HTML の外部依存を機械で検査するか | しない | Issue の受入基準に無い。決まりとして書く |
| 規模の「要求・仕様のファイルの数」に React のモックの部品が数えられる | そのまま | 数えるのは要求・仕様のファイルで、モックも `requirements/` のファイル。専用の数え方は Issue の外 |
| 表示用ページで版を重ね合わせるか | 重ね合わせない | Q&A 表・決定表の印と同じ（版ごとの節）。`removed.csv` で消したモックも、消す前の版の節には出る |
| React のモックの見せ方（ビルドしない・CDN の React と Babel・MkDocs から開く・`.tsx` は置かない） | 推奨 A で決めた（仕様の穴の記録） | 上の「仕様の穴」。受入基準は足さない |
| v2 以降で React のモックを変えるとき、変えた `.jsx` だけを置いてよいか | 置かない（ディレクトリを全部置く）と決まりに書いた | 表示用ページは版を重ね合わせず、入口は同じディレクトリの `.jsx` しか読まない。部品だけ置いた版は入口の無いディレクトリとして警告される |
| `requirements/mocks/` の外（`requirements/` のほかの場所）に置いた `.html` | 印は拾わない | 置き場所の決まりが `requirements/mocks/`。照合と重ね合わせには入る |
| 一覧は読めるが入れない（`r--`）フォルダで `is_dir`・`is_file` が Python 3.12 で例外を投げうる | 見ない | 既存の `lookup` と同じ形。権限を外したフォルダは実際の利用でまず起きない |

### 1 パス目の採否の表（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1 React のモックを消した跡（`.DS_Store` だけのフォルダ。macOS で `git rm` した後）を「入口の index.html が無い」と警告し、`mkdocs build --strict` が落ちる。重ね合わせはその形を無いとみなす | 示せる（/code-review が試料で警告を再現） | I3（サイトのビルドが通らない） | 直す（`.` で始まる名前だけのフォルダは飛ばす。試料と変異） |
| CR1-2 scaffold の写し（`scaffold/refs/`）の React のモックは、開発のリポジトリで直に開くと描かれないのに、`handoff-issue.md`・dev-loop の `spec-gap.md` にそう書いていない | 示せる（`file://` で `#root` が空） | 無し（I2 の `refs` で指せる、は満たす。見方は `tree.md` に書いた） | 残課題 |
| CR1-3 綴り違いと一覧を読めないときの警告が、その版の見出しの前に積まれ、直前の版の節に描かれる | 示せる（試料の出力） | 無し（警告は出る。既存の描画関数と同じ作り） | 残課題 |
| CR1-4 `lookup_dir` が `lookup` の写しに近い・`maybe_file` の名前がディレクトリにも使われる | 示せない（保守の指摘） | 無し | 残課題 |
| CR1-5 `tree.md` の移行の段落に版 `0.81.0` を直書き。マージ直前に版を上げ直すと古くなる | 示せない（起きていない） | 無し | 残課題（上げ直すときは段落の版も直す） |
| CR1-6 描画関数の登録が `RENDERERS` と `PAGE_RENDERERS` の 2 つに分かれる | 示せない（設計） | 無し | 残課題 |
| CR1-7 `受注.HTML`・`.htm` は「形でない」と警告される | 示せる（文言） | 無し（決まりは `.html`） | 残課題 |

### 2 パス目の採否の表（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1 CR1-1 の直しが 1 段だけ——下のフォルダを持つ React のモックを消した跡（`消した/.DS_Store`・`消した/components/.DS_Store`）でまだ警告し、`mkdocs build --strict` が 1 | 示せる（/code-review が実際の build で再現） | I3 | 直す（重ね合わせの `has_content` と同じく、`.` で始まらない名前を辿ってディレクトリでない項目に届くかで見る。試料と変異） |
| CR2-2 シンボリックリンクのモックを警告せずにリンクにする（重ね合わせは断る） | 示せる（試料で再現） | 無し（開ける。重ね合わせが止めるので承認の範囲に黙って入らない） | 残課題 |
| CR2-3 綴り違いの試料が `Requirements/` だけで、`Mocks/` の綴りの判定を外す変異が素通りする | 示せない（変異は推論だけ） | 無し（本体は両方の段を見る——試料の穴） | 残課題 |
| CR2-4 計画ファイルが `mocks` を `RENDERERS` にあると書いていた | 示せる | 無し（周の記録） | 計画の記述だけ直した（成果物ではない） |

### 狭いパスの指摘（採否は人間——振り分けは PR コメント）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 振り分け |
| --- | --- | --- | --- |
| N1 `has_content` で読めない下のフォルダを「無い」に倒す変異（OSError で False）が素通りする（陽性対照: 直に呼ぶと元は True、変異は False） | 示せる（変異の素通り） | 無し（本体は警告に倒す——試料の穴）。後退でない（起点 b9f1285f に無かった分岐） | 記録だけ |
| N2 `.` の判定を `.DS_Store` だけにする変異が素通りする（`.draft/` だけのフォルダの試料が無い） | 示せる（変異の素通り） | 無し（本体は `.` で始まる名前全部——試料の穴）。後退でない | 記録だけ |
