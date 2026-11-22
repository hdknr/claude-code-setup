# Issue #1456 — platform-spec: 骨組みと、基盤の層の profile の形・infra.csv との照合（#1312 段 1）

**不在の周**（`/dev-loop:cruise 1461 --absent` の起動・2026-11-22T03:12Z）。利用者には訊かない。親（cruise #1461）から委譲文で受けた子。
確かめた線（出所: 利用者の確認（起動時・2026-11-22T03:12:23Z、配布を見せて確かめた）＋利用者の確認（周の途中・2026-11-22T03:19:55Z）。cruise の確かめた線（台帳 `issue-1461`））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1461.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.20.1（`SKILL.md` 1957 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1461`））。
版の上げ方: `spec-loop` を **minor**（0.132.0 → 0.133.0。`check-infra-csv.py` が末尾の任意の列を受ける——能力の追加）、`platform-spec` は **新規 0.1.0**。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
**spec-loop を上げ直したら、platform-spec の対応する spec-loop の版の下限（`references/spec-loop.md` と `check-infra-profile.py` の `SPEC_LOOP_MIN`）も上げ直した版に直す**——下限は「`check-infra-csv.py` が `PROFILE_COLUMN` を持つ版」である。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.20.1/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: platform-spec の骨組み（カタログ・`plugin.json`・CI の登録。screen-spec が前例）、基盤の層の profile の形と形式の版の範囲を `references/` に、
spec-loop の `check-infra-csv.py` が末尾の任意の列 `profile の行` を受ける（7 列の表も通す）、platform-spec の照合（案件の `infra.csv` の `profile の行` が指定した profile とタグの行 ID に在るか。読むのは spec-loop の共通の部分）、
案件の設定の置き場所は推奨で決める。決めたこと（利用者 2026-11-22。親 Issue #1461 の「先に決めたこと」）: 名前は `platform-spec`・列は末尾の任意の列 `profile の行`。
#1467〜#1470・#1472 で推奨に決めた値（環境変数 `SPEC_PROFILE_CLONE` など）は今の main の `external-profile.py` のまま使う。

## 変更範囲

触る:

- `plugins/platform-spec/` — 新規。プラグインの骨組み（`.claude-plugin/plugin.json`・`README.md`）・決まりの原本（`references/`）・照合のスクリプト（`scripts/check-infra-profile.py`）
- `.claude-plugin/marketplace.json` — platform-spec のカタログの行と、spec-loop の版
- `plugins/spec-loop/scripts/check-infra-csv.py` — 末尾の任意の列 `profile の行` を受ける（中身は見ない）
- `plugins/spec-loop/references/tree.md` — 「基盤要件」の列の表に `profile の行`（任意）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（7 本）
- `scripts/test-check-infra-csv.py` — 末尾の任意の列の試料・変異と、spec-loop が platform-spec を探さないことの確かめ
- `scripts/test-check-infra-profile.py` — 新規。照合の回帰テスト（変異テストを含む）
- `scripts/check-all.py` — 回帰テストの登録
- `.github/workflows/plugins.yml` — CI のステップ
- `CLAUDE.md` — プロジェクト構成に platform-spec とテスト
- `docs/plans/issue-1456.md` — この計画ファイル

触らない:

- `plugins/spec-loop/scripts/external-profile.py`（読み込むだけ。`~` の展開は並行の周 #1471）
- spec-loop のほかのスクリプト（`scaffold.py`・`build-proposal.py` は `check-infra-csv.py` の `inspect` を読み込むので、受ける形は同じ関数で決まる）・MkDocs のフック（見出しの行どおりに描く）
- 版を上げたときの差分と関門（#1312 段 2 = #1457）・案件の `infra.csv` の移し替え（段 3）・アーキテクチャと開発の進め方の層（段 4）
- 基盤の層の `項目` と案件の `infra.csv` の `項目` の照合・リンクの検査（`external-profile.py check` が持つ）——この周の受入基準の外

依存の追加・更新: なし

## 設計の判断

- spec-loop の `check-infra-csv.py` は、見出しが 7 列そのもの か 7 列の後ろに `profile の行` を足したもの のどちらかを通す。行の列の数は見出しの数と比べる。`profile の行` の中身は見ない（未決定の印も見ない）。
  見出しが違うときの文言は前のまま（差分テストの領域の出力を変えない）。
- platform-spec の照合 `check-infra-profile.py <docs>` は、spec-loop の重ね方（`merge-versions.py` の `merge`）で重ねた全体の `shared/infra.csv` と案件の設定を読み、
  spec-loop の `external-profile.py` の `find_clone`・`resolve_tag`・`read_layer`（層 `基盤`・形式の版 1 以上 2 未満）で profile の行 ID を引いて照らす。列の名前は `check-infra-csv.py` の `PROFILE_COLUMN` を読む（写さない）。
- spec-loop の見つけ方は screen-spec と同じ順（引数 `--spec-loop` → 環境変数 `PLATFORM_SPEC_SPEC_LOOP` → 隣の `spec-loop` → プラグインのキャッシュの記録）。版の範囲は `0.133.0` 以上 `1.0.0` 未満。
  見つけ方の写しは screen-spec から写す（platform-spec は screen-spec に依存しない）。
- 終了コード: 0 = 照らした ID が全部在る（設定も `profile の行` も無いときも）／1 = 違反（無い ID・指しているのに設定が無い・設定の形・重ね合わせの違反）／2 = 判定していない（引数・読めない・想定外の例外）／
  4 = 止めた（spec-loop が見つからない・版が範囲の外・clone が見つからない・タグが無い・基盤の層が無い・形式の版が範囲の外・層の表の形が違う）。
- 複製の数: 決まりの原本は platform-spec の `references/`（1）・本体の定数（テストが原本と突き合わせる）・spec-loop の `tree.md` の列の 1 行（列の名前の原本。中身の決まりは platform-spec を指すだけ）・
  README・CLAUDE.md の項・カタログの description（JSON 2 か所は同じ値）。**分けない理由**: 原本以外は指すだけにし、写しはテストが見る（screen-spec と同じ形）。

### 仕様の穴（不在の線で推奨により決めた。確認の Issue は手順 8 の記録）

| # | 穴 | 選択肢 | 決めた値（推奨） | 理由 |
| --- | --- | --- | --- | --- |
| G1 | 案件の設定（使う profile とその版）の置き場所 | A: 版の中の `shared/platform/settings.csv`（承認の範囲に入る）／B: 版の外の正本の根（`platform-spec/settings.csv`。承認の範囲の外）／C: 正本の `CLAUDE.md` の行 | A | `infra.csv` の `profile の行` の ID はタグを決めて初めて意味が決まる。`infra.csv` は 2 つのサインオフが比べる `shared/` に在るので、タグを変えたら承認を取り直すべきで、同じ範囲に置く。screen-spec の `settings.csv` も版の中（`requirements/`） |
| G2 | `profile の行` の 1 つのセルに ID をいくつ書けるか | A: `・` で区切って複数書ける（空でよい）／B: 1 つだけ | A | 案件の 1 つの選択（例: ホスティング環境）が開発ガイドの複数の節に当たることがある。`水準` の列と同じ区切り |
| G3 | 基盤の層の表の、先頭 3 列より後ろの列 | A: `項目` の 1 列（案件の `infra.csv` のどの項目の案か）／B: `項目,決定`／C: 後ろの列を持たない | A | 選択の中身は `要約` が持つので `決定` は重なる。`項目` があれば次の段で案件の行と照らせる。形式の版 1 はこの 4 列に決め、違えば読まない |

## デプロイ経路

プラグイン（`marketplace.json` のカタログ）と公開サイトの再ビルド。マージの反映: ドキュメントとプラグインの配布（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準

不変条件 × 経路（経路は入口一覧から数える——spec-loop: CLI `check-infra-csv.py` と、読み込んで使う `inspect`・`inspect_files`（`scaffold.py`・`build-proposal.py`）・
MkDocs のフック（見出しどおりに描く）。platform-spec: CLI `check-infra-profile.py`。読む先は重ねた全体の `shared/infra.csv`・`shared/platform/settings.csv` と、spec-loop の `external-profile.py` が読む clone のタグの時点）。

| # | 不変条件 | 経路 | 証明手段 |
| --- | --- | --- | --- |
| B1 | 見出しが「7 列の後ろに `profile の行`」でない `infra.csv`（7 列の表・見出しの違う表を含む）で、`check-infra-csv.py` の結果（終了コード・出力・`inspect` の結果）が周の base と同じ | CLI・`inspect`・`inspect_files` | 差分テスト（下の記録）と、既存の回帰テストの試料が全部前のまま緑 |
| B2 | 7 列の後ろに `profile の行` を足した表を通す（中身を見ない）。その後ろにさらに列・別の名前の 8 列目は違反のまま。行の列の数は見出しの数と比べる | CLI・`inspect`・`inspect_files` | 回帰テストの試料と変異 |
| B3 | `profile の行` に在る ID は通り（0）、無い ID・そのタグに無い（別のタグにだけ在る）ID は表の行と ID を名指しして 1 | `check-infra-profile.py` | 一時の git リポジトリの profile（タグ 2 つ）に当てる回帰テスト。変異テストを含む |
| B4 | 止まり方を分ける: 指しているのに設定が無い・設定の形の違反・ID の形（空の ID）は 1。clone が見つからない・タグが無い・基盤の層が無い・形式の版が範囲の外・層の表の形が形式の版 1 と違う・spec-loop が見つからないか版が範囲の外は 4。設定も `profile の行` の値も無ければ clone を探さずに 0 | `check-infra-profile.py` | 回帰テスト（ケースごとの終了コードと名指し） |
| B5 | platform-spec を置かない案件で、spec-loop のスクリプトが platform-spec を探さない・要求しない | spec-loop の `scripts/`・`templates/` | spec-loop の `scripts/` だけを一時ディレクトリに写して `profile の行` つきの表に当てて 0。`scripts/`・`templates/` に platform-spec の名前（`platform-spec`・`platform_spec`・`PLATFORM_SPEC`）が無いことを見る |
| B6 | platform-spec の照合は読むだけ——正本と clone に書かない（clone の HEAD・参照・作業ツリーを変えない） | `check-infra-profile.py` | 回帰テストで前後の `git status --porcelain`・HEAD・`git for-each-ref` と正本のファイルの一覧を比べる |
| B7 | 決まりの原本が platform-spec の `references/` に在り、本体の定数（設定の置き場所と項目・基盤の層の名前と列・形式の版の範囲・spec-loop の版の範囲・環境変数・区切り）が原本と一致する | references・本体 | テストが原本と定数を突き合わせる（崩すと不一致になる陽性対照つき） |
| B8 | カタログ: platform-spec が `marketplace.json` と `plugin.json` に載り、`check-plugin-versions.py` などのカタログの検査が通る。CLAUDE.md の「プロジェクト構成」に platform-spec がある。`check-all.py` と CI に登録されている | カタログ・CLAUDE.md・check-all・plugins.yml | `check-plugin-versions.py`・`check-description-sync.py`・`test-check-all.py`（check-all の中） |
| B9 | 版: spec-loop を minor で上げ 3 種類（marketplace.json・plugin.json・SKILL.md 7 本の 2 行）が揃う。platform-spec は 0.1.0 で 2 か所が揃う | 版の行 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| B10 | 変異テスト: 照合の本体の docstring の「守る」の行ごとに変異があり、どれも殺せる。数は手で数えない | テスト | テストが「守る」の行数と変異の数を突き合わせる |
| B11 | 掛け算: B1〜B10 を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | 関門の委譲 | 計画ファイルの関門の記録 |

B1 に足す行（差分テスト）: 旧（周の base）と新（差分テストを回した成果物）に同じ入力を与えた出力が、正規化したあと、承認済みの変更の一覧に無い違いを 1 件も持たず、新側に挙動の変更を 1 か所入れると差分テストが差分を検出する（Verifier が示す）。
B1 に足す行（プロパティテスト）: 表の行について、ライブラリが無いので、代替の生成のテストが、性質を破る変異で落ちる（Verifier が示す）。

- 生成物: なし——図（drawio）も `SKILL.md` の測定値の生成ブロックも触らない（spec-loop の `SKILL.md` は版の 2 行だけ。`skill-metrics.py --check` で確かめる）。
- 仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）
- 未証明: 本物の組織の開発ガイド（非公開）の profile に当てたときの読み方——この環境に無い。試料は一時のリポジトリで作る（人間のレビューへ）。

プロパティテスト: あり

| 不変条件の番号 | 型 | 性質（任意の x について） | テストの名前 | ライブラリ | 生成の設定 |
| --- | --- | --- | --- | --- | --- |
| B1 | 等価性 | 見出しが「7 列＋`profile の行`」でない任意の基盤要件の表（と Q&A 表・非機能要求の表の有無）について、旧と新の `check-infra-csv.py` の終了コード・標準出力・標準エラーと `inspect` の結果が同じ | `differential_B1`（周の外のスクリプト。結果は下の差分テストの記録） | 無い（Python の Hypothesis が依存の定義（`pyproject.toml`）にも lockfile（`uv.lock`）にも無い）／代替: 標準ライブラリの `random` で表を生成する差分テスト（`differential_B1`）／理由: このリポジトリの検査とテストは標準ライブラリだけ（CLAUDE.md）で、Issue も利用者も依存の追加を頼んでいない。不在の周は足さない | 例の数 400・seed は実行ごとに変える（使った seed を出力する）・生成器は見出し（7 列・順の入れ替え・列を消す・別の列を足す・`profile の行` の後ろにさらに列）・行の数 0〜6・列の数の過不足・項目（必ず置く 3 つ・ほか・重複・空・印）・状態（3 つ・違う値・空・印）・根拠（在る `Q-`・無い `Q-`・`D-`・形の違い・空・印）・水準（在る・無い・区切り違い・空）・Q&A 表と非機能要求の表の有無・BOM |

  落とした主張（PR コメントに名指しする）: 入力の空間の偏りを Hypothesis の縮小と同じ強さでは確かめていない。

差分テスト: あり

| 項目 | 書くもの |
| --- | --- |
| 旧 | 周の base の SHA `b37059d0d0f6ff317fddadfd2cd866eab10e5cd9`（`plugins/spec-loop/scripts/` を `git archive` でリポジトリの外に取り出す） |
| 新 | `87c2ba58`（2 パス目の指摘対応の後の成果物の SHA。そこから後は計画ファイルだけ。前は `6ad2c16b`・`0af01d8b` で回した） |
| 入力の出どころ | 生成（上の表の生成の設定。件数 400） |
| 正規化した項目 | 出力の中の一時ディレクトリのパス（旧と新で試料のディレクトリが違う——同じ相対パスに揃える。比較に関係ないのは、本体がパスを出すのは引数の表示だけだから） |
| 承認済みの変更の一覧 | 下の節 |
| 結果 | `87c2ba58` で: 比べた 400 件・差分 0 件・一覧に無い差分 0 件（seed 3819860847。旧の内訳: 0 が 28・1 が 258・2 が 9・3 が 97・4 が 8）。`0af01d8b` で: 比べた 400 件・差分 0 件・一覧に無い差分 0 件（seed 4051161444。旧の終了コードの内訳: 0 が 29・1 が 251・2 が 9・3 が 98・4 が 13）。比べるのは CLI の終了コード・標準出力・標準エラーと `inspect`・`inspect_files` の Report の全部の欄。1 パス目の CR-6 で `inspect_files` の比べと決まりどおりの表の生成（約 3 割。半分はセルを 1 つ崩す）を足した。前の回（`6ad2c16b`・seed 3521075991・400 件・差分 0 件）は 0 の入力を作らなかった |
| 回した場所 | リポジトリの外（scratchpad の `diff1456/`。旧・新とも `git archive` で `plugins/spec-loop/scripts/` を取り出し、`differential_B1.py <旧> <新> <作業> 400` で回した。本体はリポジトリに残さない） |

領域: 見出しが「7 列の後ろに `profile の行`」の表は差分テストの領域の外——そこで振る舞いを変えるのがこの周の目的（B2）。

### 承認済みの変更

承認済みの変更: なし

## 未解決の判断・確認待ち

- 仕様の穴 G1〜G3 は推奨で決めた（上の表）。確認の Issue: G1 #1478・G2 #1479・G3 #1480（閉じるのは利用者）。PR は #1477。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1456-platform-spec-skeleton`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1456`・起点 `b37059d0`・base の参照 `origin/main`（refs/remotes/origin/HEAD）・base の SHA `b37059d0d0f6ff317fddadfd2cd866eab10e5cd9`
- 関門: 1 パス目の Verifier（sonnet・dev-loop:dev-loop-verifier）を `76e00e64` に当てた——反証 0 件（差し込み 11 の当てられなかった 2 行は同じ差し込みで 1 回当て直し、反証 0 件）。
  1 パス目の `/code-review`（high）を同じ `76e00e64` に当てた——指摘 7 件（CR-1〜CR-7）。採否は下の表。差し戻し: 1 パス目の指摘対応（手順 4 へ）。
- 1 パス目の指摘対応の起点（0 行の判定）: `76e00e640b25fa5b6b0d677181c0949d9bbcf1c6`。指摘対応の終点 `0af01d8b`（差分は 0 行でない——2 パス目を回す）
- 2 パス目: 割り目——割らない（cruise の周）。`/code-review`（high）を `0af01d8b` に当てた——指摘 4 件（CR2-1〜CR2-4）。Verifier（sonnet）を `3ac2eb3a`（`0af01d8b` から計画ファイルだけ進めた）に当てた——反証 2 件（V2-1・V2-2）。採否は下の表。
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `3ac2eb3a44758631254f83c936273c950f947672`・終点（指摘対応の最後のコミット）: `87c2ba5827bbfdc7495a48cd299c1ca3b5f86cc0`。著者の足した変異 3 本（リポジトリの点・タグのハイフンと HEAD・基盤要件の表の先頭の空の行を見ない）はどれも赤（テスト全体で変異 28 本＝守ること 28 行）
- check-all: 1 回目（run-serial 越し）は出力先の名前を並行の周と共有していたので、自分で止めた（シグナルで終わった——失敗として扱う）。名前に周の番号を入れて回し直している
- 狭いパス: Verifier（sonnet）を `3ac2eb3a`→`87c2ba58` に当てた——指摘 2 件（F1・F2。どちらも変異テストの弱さで、本体の誤りは見つからない。Verifier が足した試料 11 本は元の本体で期待どおり）。差し込み 11 の当てられなかった 3 行（陽性対照・正規化を外す当て・承認済みの変更の 6 本）は同じ差し込みで 1 回当て直した——反証 0 件（陽性対照: `REQUIRED_ITEMS` から `DBMS` を外すと 50 件中 10 件の差分）。振り分けは手順 8 の表（どちらも記録だけ・後退を示さない）。
- マージ前の判断（線 `推奨で決めて起票（後退・未達を含む）`）: 該当なし——満たしていない受入基準・直すに入った狭いパスの指摘・実機の BLOCKED は無い。
- check-all（run-serial 越し・出力 `checkall-1456-2.txt`）: `76e00e64` の木で 103 本のうち失敗 1（`check-plan-counts.py`——件数の行がまだ無かった。この版で足した）。全部は PR の前にもう 1 度回す。
- 交絡を潰した手順: 差分テスト（否定的な結果）は、Verifier と /code-review がそれぞれ新側に変異を入れて差分が出ること（陽性対照）を示した。生成器が決まりどおりの表を作らなかった偏りは 1 パス目の CR-6 で直し、終了コードの 0〜4 が全部出ることを結果に書いた。照合のテストは、壊さない写しを同じ置き方で置く陰性対照と変異 28 本で観測が判別していることを見た。
- 割り目: 割らない（cruise の周）

```dev-loop-gates
周の base: b37059d0d0f6ff317fddadfd2cd866eab10e5cd9
関門: Verifier 1 76e00e64 反証=0
関門: /code-review 1 76e00e64 指摘=7
関門: Verifier 2 3ac2eb3a 反証=2
関門: /code-review 2 0af01d8b 指摘=4
関門: 狭いパス 3ac2eb3a 87c2ba58 反証=2
受入基準: B1 満たす
受入基準: B2 満たす
受入基準: B3 満たす
受入基準: B4 満たす
受入基準: B5 満たす
受入基準: B6 満たす
受入基準: B7 満たす
受入基準: B8 満たす
受入基準: B9 満たす
受入基準: B10 満たす
受入基準: B11 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

- 仕様の穴 G1〜G3（上の表）。
- 基盤の層の `項目` と案件の `infra.csv` の `項目` の照合はこの周でしない（段 2 以降）。
- リンクの検査は `external-profile.py check` が持ち、platform-spec の照合は見ない。
- `profile の行` のセルの未決定の印（`TBD` など）は ID として照らし、無い ID として名指す（印を別に数えない）。
- B5 の見張りは、spec-loop の Python の docstring とコメントの中の名前を数えない（`external-profile.py` の docstring が使う側として platform-spec を名指す——説明であって探すことではない）。探す・求める先になりうる文字列と名前だけを見る（Verifier 1 パス目の注意。決着: 採らない——受入基準の「探さない・要求しない」を見るのに足りる）。

### 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR-1 設定の値の形が違う（profile の名前に `/`・タグに版の記法・リポジトリが `<持ち主>/<名前>` でない）と 1 でなく 4 | 示せる（scratchpad の `cr1456/` で実走: `a/b`・`v1~1` で rc=4「読めない」） | B4（設定の形の違反は 1） | 直す（`setting_forms` で 3 つの形を見て 1。守るに 3 行・変異 3・試料 3。原本に値の形を書く） |
| CR-2 `ext.read_blob` は external-profile の「使う側が読み込む関数」の一覧に無く、名前が変わると 4 でなく 2 | 示せない（今の spec-loop のどの版にも在る） | 無し | 残課題 |
| CR-3 「層が無ければ 4（3 にしない）」の変異は 2 で死ぬ——恐れる 3 は再現しない | 示せる（変異の結果） | 無し（B10 は変異が殺せることで、殺せている） | 残課題 |
| CR-4 層の表の先頭が空の行だと、spec-loop は読むのに見出しの確かめが空を読んで 4 | 示せる（`cr1456/` で実走: 在る ID でも rc=4「見出しが…でない: 」） | B3（在る ID は通る） | 直す（空の行を飛ばした最初の行を見出しに読む。守る 1 行・変異 1・試料 1） |
| CR-5 CLAUDE.md の「workspace-setup（このプラグインだけスキルを持たない）」と公開ページの link-skills の対象外の一覧が、スキルを持たない platform-spec を足して偽になった | 示せる（文） | 無し | 残課題 |
| CR-6 差分テストが `inspect_files` を呼ばず、終了コード 0 の入力を作らない | 示せる（スクリプト） | B1（経路に `inspect_files` を挙げている） | 直す（周の外のスクリプトに `inspect_files` の比べと、決まりどおりの表を約 3 割作る生成を足した。成果物の差分は 0 行——回し直した結果は差分テストの記録） |
| CR-7 `installed_spec_loop` が resolve した docs と resolve していない `projectPath` を比べる（macOS の `/tmp`） | 示せない（実機の記録の形で試していない。screen-spec から写した形） | 無し | 残課題 |

### 2 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1／V2-1 設定のタグ `-v1`（`-` で始まる）・`HEAD` は `git check-ref-format` を通るが、git はタグにできず、照合は 1 でなく 4。リポジトリ `../x`・`a/..` も形を通って 4 | 示せる（/code-review の `cr2-1456/`・Verifier の実走: rc=4） | B4（設定の形の違反は 1） | 直す（タグは `-` で始まる名前と `HEAD` も形の違反に、リポジトリは `<持ち主>`・`<名前>` が `.`・`..` でないことも見る。守るの行・変異・試料を足す） |
| CR2-2 `infra.csv` の先頭が空の行だと、`profile の行` の ID を 1 つも照らさずに 0 | 示せる（/code-review の実走: NOPE-1 で rc=0） | B3（無い ID は名指しして 1） | 直す（見出しを空の行を飛ばした最初の行で読む。層の表と同じ読み方。守る 1 行・変異・試料） |
| CR2-3 変異「設定も値も無いのに clone を探す」は TypeError（2）で死ぬ——恐れる振る舞いを観測していない | 示せる（変異の結果） | 無し（B10 は殺せることで、殺せている） | 残課題 |
| CR2-4 `SPEC_LOOP_MIN = 0.133.0` は並行の周が先に取りうる番号——マージ前に spec-loop を上げ直したら、下限・原本の表・テストの古い版の試料と崩しも直す | 示せる（並行の周の版） | 無し（上げ忘れても `PROFILE_COLUMN` の確かめで 4 に倒れる） | 残課題（計画の冒頭に書いた——上げ直すときに直す） |
| V2-2 層の表の見出しの前の飛ばし方が spec-loop と違う（本体は `,,,`・空白だけの行も飛ばし、spec-loop の `_csv_rows` は空の行だけ）。docstring の「spec-loop の読み方と同じ」が少し広い | 示せない（spec-loop の `read_layer` が先に 4 で止める） | 無し | 残課題 |
| V2-3 `git check-ref-format` は git が PATH に無いと FileNotFoundError（2）になりうる | 示せない（当てていない。git は外部の profile を読むのに要る） | 無し | 残課題 |

## 手順 8 の記録

- この周の起票: 3 件（仕様の穴 G1〜G3 の確認の Issue #1478・#1479・#1480）

### 振り分け（`references/found-lines.md`）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け | 仕様の穴か | 行き先 |
| --- | --- | --- | --- | --- | --- |
| `ext.read_blob` が external-profile の「使う側が読み込む関数」の一覧に無い | #1456 /code-review 1 パス目 CR-2 | 示せない | 記録だけ（今の spec-loop の版のどれにも在る） | — | — |
| 「層が無ければ 4（3 にしない）」の変異が 2 で死ぬ | #1456 /code-review 1 パス目 CR-3 | 示せる（変異の結果） | 記録だけ（試料の穴） | — | — |
| CLAUDE.md の「workspace-setup（このプラグインだけスキルを持たない）」と公開ページの link-skills の対象外の一覧が偽になった | #1456 /code-review 1 パス目 CR-5 | 示せる（文） | 記録だけ（文言。従っても誤った操作にならない） | — | — |
| `installed_spec_loop` が resolve した docs と resolve していない `projectPath` を比べる | #1456 /code-review 1 パス目 CR-7 | 示せない | 記録だけ（screen-spec から写した形。実機の記録で試していない） | — | — |
| 変異「設定も値も無いのに clone を探す」が TypeError（2）で死ぬ | #1456 /code-review 2 パス目 CR2-3 | 示せる（変異の結果） | 記録だけ（試料の穴） | — | — |
| spec-loop を上げ直したら platform-spec の下限も直す | #1456 /code-review 2 パス目 CR2-4 | 示せる（並行の周の版） | 記録だけ（マージの直前の上げ直しで直す。上げ忘れても `PROFILE_COLUMN` の確かめで 4 に倒れる） | — | — |
| 層の表の見出しの前の飛ばし方が spec-loop と違う | #1456 Verifier 2 パス目 V2-2 | 示せない | 記録だけ（spec-loop の `read_layer` が先に 4 で止める） | — | — |
| `git check-ref-format` は git が PATH に無いと FileNotFoundError（2） | #1456 Verifier 2 パス目 V2-3 | 示せない | 記録だけ（git は外部の profile を読むのに要る） | — | — |
| リポジトリの `.`・`..` の検査を部分的に崩しても赤にならない（試料が `org/..` の 1 本だけ） | #1456 狭いパス F1 | 示せる（崩した変異が素通り） | 記録だけ（試料の穴。本体は Verifier の試料 `./x`・`o/.` で 1——後退を示さない） | — | — |
| 表の先頭の空の行が 2 行以上・空白だけの行の試料が無く、崩した変異が素通り | #1456 狭いパス F2 | 示せる（崩した変異が素通り） | 記録だけ（試料の穴。本体は Verifier の試料で期待どおり——後退を示さない） | — | — |

- 切り分けの層: 戻し先なし——骨組み・spec-loop の列・照合の 3 つを 1 周に持ったが、関門の指摘は照合の設定の形と読み方に集まり、骨組みと列は 1 パス目から指摘が無かった。#1461 の切り方（段 1 を 1 周）は依存の線（#1457 がこの照合を読む）のために要った。
- 焼き戻す学び: 設定の値の形を「git が通す形」で見ると、git がタグにしない名前（`-v1`・`HEAD`）が通る——読む側（`external-profile.py` の `resolve_tag`）が弾く形と揃える。この計画ファイルに残す（CLAUDE.md・Skill には足さない）。

### 効いた行（手順 8）

- 効いた行: R-02（1 パス目 CR-1・CR-4・CR-5——記述と振る舞いの事実確認。2 パス目 CR2-1・CR2-2・CR2-4）
- 効いた行: R-01（1 パス目 CR-6——差分テストが主張を判別しているか）
- 効いた行: R-04（1 パス目 CR-3・2 パス目 CR2-3——当てて確かめた変異）
- 効いた行: V-03（2 パス目 V2-1・V2-2——実走による事実確認）
- 効いた行: V-05（狭いパス F1・F2——Verifier が設計した変異）
- 効いた行: なし（1 パス目 CR-2・CR-7、2 パス目 V2-3）
