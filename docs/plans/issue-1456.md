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
| 新 | `6ad2c16b`（成果物の SHA。そこから後は計画ファイルだけ） |
| 入力の出どころ | 生成（上の表の生成の設定。件数 400） |
| 正規化した項目 | 出力の中の一時ディレクトリのパス（旧と新で試料のディレクトリが違う——同じ相対パスに揃える。比較に関係ないのは、本体がパスを出すのは引数の表示だけだから） |
| 承認済みの変更の一覧 | 下の節 |
| 結果 | 比べた 400 件・差分 0 件・一覧に無い差分 0 件（seed 3521075991。旧の終了コードの内訳: 1 が 339 件・3 が 43 件・2 が 18 件。0 は 0 件——生成器が決まりどおりの表をほとんど作らないので、0 の経路は既存の回帰テストの試料が持つ） |
| 回した場所 | リポジトリの外（scratchpad の `diff1456/`。旧・新とも `git archive` で `plugins/spec-loop/scripts/` を取り出し、`differential_B1.py <旧> <新> <作業> 400` で回した。本体はリポジトリに残さない） |

領域: 見出しが「7 列の後ろに `profile の行`」の表は差分テストの領域の外——そこで振る舞いを変えるのがこの周の目的（B2）。

### 承認済みの変更

承認済みの変更: なし

## 未解決の判断・確認待ち

- 仕様の穴 G1〜G3 は推奨で決めた（上の表）。確認の Issue を穴ごとに立てる（番号は手順 8 の記録に書く）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1456-platform-spec-skeleton`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1456`・起点 `b37059d0`・base の参照 `origin/main`（refs/remotes/origin/HEAD）・base の SHA `b37059d0d0f6ff317fddadfd2cd866eab10e5cd9`
- 関門: 1 パス目に入る（Verifier と /code-review を同じ起点に当てる）
- 1 パス目の指摘対応の起点（0 行の判定）: （このコミットの SHA——関門に渡すときに書く）
- check-all: 1 回目（run-serial 越し）は出力先の名前を並行の周と共有していたので、自分で止めた（シグナルで終わった——失敗として扱う）。名前に周の番号を入れて回し直している
- 交絡を潰した手順: まだ
- 割り目: 割らない（cruise の周）

## 既知の限界・決着済みの論点

- 仕様の穴 G1〜G3（上の表）。
- 基盤の層の `項目` と案件の `infra.csv` の `項目` の照合はこの周でしない（段 2 以降）。
- リンクの検査は `external-profile.py check` が持ち、platform-spec の照合は見ない。
- `profile の行` のセルの未決定の印（`TBD` など）は ID として照らし、無い ID として名指す（印を別に数えない）。
