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
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版
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
印 `mocks` の名前は フック（`RENDERERS`）・雛形のページ・`tree.md` の 3 箇所で、`test-init-mkdocs.py` が雛形のページと `tree.md` を見る。分けない理由: 既存の `infra` の印と同じ形で、増える複製は無い。

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
  - 経路: `merge-versions.py`（v1 の HTML・React のディレクトリを重ねる、v2 で React の部品だけ差し替える、`removed.csv` で消す）／`check-signoff.py`（2 つのタグの間で HTML・React の部品が違えば 1）／
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
- 確認の Issue: （PR を作った後に立てる）

## 起票

- この周の起票: 0 件（確認の Issue はまだ立てていない）

## 未解決の判断・確認待ち

- 上の仕様の穴（確認の Issue で利用者が確かめる）

## 関門の進捗（再開点）

- 割り目: 割らない（cruise の周）
- 手順 5 の反証と手順 4 への差し戻し: （未）
- 交絡を潰した手順: （未）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 照合・重ね合わせの本体を直すか | 直さない（試料で固定） | `requirements/` の下のファイルはどの種類でも対象に入っている。`.` で始まる名前だけは読まない（`.DS_Store` のため。決まりとして置かないと書く） |
| HTML の外部依存を機械で検査するか | しない | Issue の受入基準に無い。決まりとして書く |
| 規模の「要求・仕様のファイルの数」に React のモックの部品が数えられる | そのまま | 数えるのは要求・仕様のファイルで、モックも `requirements/` のファイル。専用の数え方は Issue の外 |
| 表示用ページで版を重ね合わせるか | 重ね合わせない | Q&A 表・決定表の印と同じ（版ごとの節）。`removed.csv` で消したモックも、消す前の版の節には出る |
