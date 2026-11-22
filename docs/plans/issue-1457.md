# Issue #1457 — platform-spec: profile の版の差分から起票の候補を出し、proposal・scaffold の前の関門にする（#1312 段 2）

**不在の周**（`/dev-loop:cruise 1461 --absent` の起動・2026-11-22T03:12Z）。利用者には訊かない。親（cruise #1461）から委譲文で受けた子。
確かめた線（出所: 利用者の確認（起動時・2026-11-22T03:12:23Z、配布を見せて確かめた）＋利用者の確認（周の途中・2026-11-22T03:19:55Z）。cruise の確かめた線（台帳 `issue-1461`））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1461.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.20.1（`SKILL.md` 1957 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1461`））。
版の上げ方: `platform-spec` を **minor**（0.1.0 → 0.2.0。版の差分の候補と関門の口——能力の追加）、`spec-loop` を **minor**（0.133.0 → 0.134.0。`profile-gate.py` と scaffold・proposal の関門——能力の追加）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.20.1/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。出力ファイルの名前には周の番号を入れる（`checkall-1457-<n>.txt`）。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: profile の新しい版（タグ）について、案件の `infra.csv` が `profile の行` で指す行のうち変わった・消えた・リンクの切れた行を起票の候補として出す（差分は共通の部分 `external-profile.py` を読み込む。番号を振らない）。
proposal・scaffold の前に、案件が指している profile の版との差分が残っていないかを見る関門（spec-loop は platform-spec に依存しない——`screen-gate.py` が前例。profile を使わない案件では何もせず 0）。
feasibility の手順に「標準を採るかを Q&A 1 問で決め、標準から外れる行だけ個別に決める」流れを書く。
決めたこと（利用者 2026-11-22。親 Issue #1461 の「先に決めたこと」）: 名前は `platform-spec`・列は末尾の任意の列 `profile の行`。
#1467〜#1470・#1472・#1478〜#1480 で推奨に決めた値（環境変数 `SPEC_PROFILE_CLONE`・設定の置き場所 `shared/platform/settings.csv`・`・` の区切り・基盤の層の 4 列など）は今の main の実装のまま使う。

## 変更範囲

触る:

- `plugins/platform-spec/scripts/check-profile-diff.py` — 新規。版の差分から起票の候補を出す（関門の本体）
- `plugins/platform-spec/scripts/check-infra-profile.py` — 案件の設定の任意の項目 `確かめたタグ` を受ける（形はタグと同じに見る）
- `plugins/platform-spec/references/infra-profile.md` — 「案件の設定」に任意の項目、「版の差分と関門」の節
- `plugins/platform-spec/README.md` — 中身の表
- `plugins/platform-spec/.claude-plugin/plugin.json` — description・版
- `plugins/spec-loop/scripts/profile-gate.py` — 新規。profile の関門（`screen-gate.py` と同じ形。platform-spec を子のプロセスで呼ぶ）
- `plugins/spec-loop/scripts/scaffold.py` — 生成の前に profile の関門を当てる（画面の関門と同じ条件）
- `plugins/spec-loop/scripts/build-proposal.py` — 生成の前に、要求確定のタグの時点の `docs/` に profile の関門を当てる
- `plugins/spec-loop/references/tree.md` — 「基盤要件」に profile の関門の 1 段落（原本は `profile-gate.py` の docstring を指す）
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 標準を採るかを 1 問で決め、外れる行だけ個別に決める流れと、版の差分の候補の読み方
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 生成の前の profile の関門の 1 行
- `plugins/spec-loop/skills/proposal/SKILL.md` — 生成の前の profile の関門の 1 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（7 本）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版・description
- `scripts/test-check-profile-diff.py` — 新規。候補の回帰テスト（変異テストを含む）
- `scripts/test-profile-gate.py` — 新規。関門と scaffold・proposal の口の回帰テスト（変異テストを含む）
- `scripts/test-check-infra-profile.py` — 任意の項目の試料・変異・原本の突き合わせ
- `scripts/test-check-infra-csv.py` — spec-loop が platform-spec の名前を持つのは `profile-gate.py` だけ、に狭める見張り
- `scripts/check-all.py` — 回帰テストの登録
- `.github/workflows/plugins.yml` — CI のステップ
- `CLAUDE.md` — プロジェクト構成の項
- `docs/plans/issue-1457.md` — この計画ファイル

触らない:

- `plugins/spec-loop/scripts/external-profile.py`（読み込むだけ。並行の周 #1471 が触る）
- `plugins/screen-spec/`（並行の周 #1458）
- spec-loop の `check-spec-exit.py`（抜ける条件 1 には profile の関門を入れない——Issue は proposal・scaffold の前を求める）・`check-signoff.py`・MkDocs のフック
- 案件の `infra.csv` の移し替え（#1312 段 3）・アーキテクチャと開発の進め方の層（段 4）・基盤の層の `項目` と案件の `項目` の照合

依存の追加・更新: なし

## 設計の判断

- **候補の本体は platform-spec の `check-profile-diff.py <docs> [--upto <n>] [--new <タグ>] [--clone <パス>] [--spec-loop <根>] [--project <正本の根>]`**。
  spec-loop の重ね方・設定と `profile の行` の読み方・spec-loop の見つけ方は同じプラグインの `check-infra-profile.py` を読み込む（写さない）。差分は `external-profile.py` の `read_layer`・`check_links`・`diff_layers`。
  古い版 = 設定の `タグ`、新しい版 = `--new` か、clone のタグのうちその profile の `profile.csv` を持つものの中で版の順（`git for-each-ref --sort=-v:refname`）が最も後ろのもの。
  新しい版が `タグ` か `確かめたタグ` と同じなら比べずに 0。
  候補は `profile の行` が指す ID のうち、変わった（どの列でも）・消えた（新しい版に無い。基盤の層ごと無い場合も）・新しい版でリンクが切れた行。足した行と指していない行は出さない。番号を振らない。
- 終了コード: 0 = 候補が無い（比べる版が無い・使っていないも）／1 = 候補がある・設定や `profile の行` の違反（`check-infra-profile.py` と同じ）・指した ID が古い版に無い／2 = 判定していない／4 = 止めた（clone・タグ・古い版の基盤の層が無い・形式の版・spec-loop の見つけ方と版・比べる新しい版が 1 つも無い）。
- **関門は spec-loop の `profile-gate.py <docs> [--upto <n>] [--platform-spec <根>] [--project <正本の根>]`**（`screen-gate.py` が前例）。案件が profile を使っている＝重ねた全体の `shared/infra.csv` の `profile の行`（spec-loop の `check-infra-csv.py` の `PROFILE_COLUMN`）に値が 1 つでもある。
  使っていなければ何も出さずに 0（platform-spec を探さない）。使っていれば platform-spec を探し（引数 → 環境変数 `SPEC_LOOP_PLATFORM_SPEC` → 隣の `platform-spec` → プラグインのキャッシュの記録）、`check-profile-diff.py` を子のプロセスで呼んで 0・1・2・4 を読み替える（知らないコードは 2）。見つからなければ 4。
- scaffold.py は画面の関門と同じ条件（作業中の版の全体。`--upto` で前の版を確かめるときは当てない）で当て、1 は 1・2 と 4 は 2 で何も作らない。
  build-proposal.py は要求確定のタグの時点の `docs/` の写し（前の版との比較と同じ一時ディレクトリ）に当て、`--project` に正本の根を渡す（clone の探し方の `CLAUDE.md`）。1 は 1・2 と 4 は 2 で書かない。
- 複製の数: 決まりの原本は platform-spec の `references/infra-profile.md`（候補・設定）と spec-loop の `profile-gate.py` の docstring（関門・見つけ方）。写しは本体の定数（テストが突き合わせる）・tree.md の 1 段落と 3 つの SKILL.md の 1 行（指すだけ）・README・CLAUDE.md の項・カタログの description。
  **分けない理由**: 原本以外は指すだけにし、写しはテストが見る（screen-spec・#1456 と同じ形）。platform-spec の見つけ方は `screen-gate.py` の screen-spec の見つけ方と同じ形の写し（プラグインをまたいで読み込めない）。

### 仕様の穴（不在の線で推奨により決めた。確認の Issue は手順 8 の記録）

| # | 穴 | 選択肢 | 決めた値（推奨） | 理由 |
| --- | --- | --- | --- | --- |
| G1 | 「profile の新しい版」をどれにするか（候補と関門が比べる相手） | A: 手元の clone のタグのうち、その profile を持つものの中で版の順が最も後ろのもの（`--new` で名指しもできる）／B: 毎回 `--new` で名指す（関門は名指しが無いと比べない）／C: 前の版の設定のタグと作業中の版の設定のタグを比べる | A | 関門は「新しい版が出たのに見ていない」を止めるためのもので、名指しを待つ B では誰も名指さなければ通る。C は案件がタグを上げた後にしか差分が出ず、新しい版が出たことに気づけない。版の順は git の `v:refname`（`v10` は `v9` より後ろ） |
| G2 | 発注者が新しい版を採らないと決めたとき、関門をどう通すか | A: 案件の設定に任意の項目 `確かめたタグ` を置き、新しい版と同じなら比べない／B: 採らないなら通さない（タグを上げるまで止まる）／C: 確かめた結果を Q&A 表の行で見る | A | 「profile は案を出すだけで、決めるのは発注者」なので、採らない決定でも先へ進めるべき。設定は `shared/` にあり 2 つのサインオフが比べるので、`確かめたタグ` を書けば承認の取り直しが機械で求められる。C は Q&A の文面に機械で読む印を足すことになり、Q&A の決まりを広げる |

## デプロイ経路

プラグイン（`marketplace.json` のカタログ）と公開サイトの再ビルド。マージの反映: ドキュメントとプラグインの配布（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準

不変条件 × 経路（経路は入口一覧から数える——platform-spec: CLI `check-profile-diff.py`・CLI `check-infra-profile.py`。spec-loop: CLI `profile-gate.py`・読み込んで使う `check`（`scaffold.py` の書く生成・`--dry-run`・`--check`・`--red-check`・`--upto`、`build-proposal.py`）。
読む先は重ねた全体の `shared/infra.csv`・`shared/platform/settings.csv`、要求確定のタグの時点の `docs/`、`external-profile.py` が読む clone のタグの時点）。

| # | 不変条件 | 経路 | 証明手段 |
| --- | --- | --- | --- |
| C1 | 2 つのタグの profile と `infra.csv` で、`profile の行` が指す行のうち変わった・消えた・新しい版でリンクの切れた行が、表の行・項目・ID・種類つきで候補として名指しされ（1）、指していない行と足した行は名指されない。候補の行に Q&A の番号が振られない。正本と clone が書き換わらない（#1457 の受入基準 1） | `check-profile-diff.py` | 一時の git リポジトリの profile（タグ複数）に当てる回帰テスト。変異テストを含む。前後の正本の中身・clone の status・HEAD・参照を比べる |
| C2 | 新しい版の決め方: `--new` があればそれ、無ければ profile を持つタグのうち版の順が最も後ろのもの（profile を持たないタグは数えない）。新しい版が `タグ` か `確かめたタグ` と同じなら比べずに 0 | `check-profile-diff.py` | 回帰テスト（v9・v10 の順・profile を持たないタグ・`確かめたタグ`） |
| C3 | 止まり方を分ける: 設定・`profile の行` の違反と、指した ID が古い版に無いのは 1。clone・タグ・古い版の基盤の層が無い・形式の版の外・比べる新しい版が無い・spec-loop の見つけ方と版は 4。設定も値も無ければ clone を探さずに 0 | `check-profile-diff.py` | 回帰テスト（ケースごとの終了コードと名指し） |
| C4 | 関門: 候補が残っていれば止まり（1）、無ければ通る（0）。profile を使わない案件では何も出さずに 0 で、platform-spec を探さない（陽性対照: 同じ置き方で `profile の行` に値があれば探して呼ぶ）（#1457 の受入基準 2） | `profile-gate.py` | 回帰テスト（本物の platform-spec と偽物）。陽性対照つき |
| C5 | 案件が profile を使っているのに platform-spec が見つからなければ 0 にせず 4。名指しが platform-spec でなければほかを探さずに 4。platform-spec の結果の 0・1・2・4 を読み替え、知らない終了コードを 0 にしない（#1457 の受入基準 3） | `profile-gate.py` | 回帰テスト |
| C6 | scaffold.py（書く生成・`--dry-run`。作業中の版）と build-proposal.py は、関門が 1 なら 1、2・4 なら 2 で何も書かない。関門が 0 なら今までどおり作る | `scaffold.py`・`build-proposal.py` | 回帰テスト（偽の platform-spec の終了コードで分ける。書いたファイルが無いこと） |
| C7 | profile を使わない正本で、scaffold.py・build-proposal.py の出力（終了コード・標準出力・標準エラー・書いたファイル）が周の base と同じ。`確かめたタグ` を置かない設定で、check-infra-profile.py の結果が周の base と同じ | `scaffold.py`・`build-proposal.py`・`check-infra-profile.py` | 差分テスト（下の記録）と既存の回帰テストが緑 |
| C8 | check-infra-profile.py は任意の項目 `確かめたタグ` を受け、形をタグと同じに見る（違えば 1）。ほかの決まりの外の項目は今までどおり 1 | `check-infra-profile.py` | 回帰テストの試料と変異 |
| C9 | spec-loop のスクリプトと雛形のうち platform-spec の名前を探す・求める先に持つのは `profile-gate.py` だけ。spec-loop の `scripts/` だけの写しで、profile を使わない正本の関門が 0 | spec-loop の `scripts/`・`templates/` | `test-check-infra-csv.py` の見張りと `test-profile-gate.py` |
| C10 | 読むだけ——候補・関門・照合は正本・clone・プラグインの写し（`__pycache__`）に書かない | 3 つの CLI | 回帰テストで前後を比べる |
| C11 | 決まりの原本（候補の種類・新しい版の決め方・任意の項目・関門の見つけ方と環境変数）と本体の定数が一致する | references・docstring・本体 | テストが原本と定数を突き合わせる（崩すと不一致になる陽性対照つき） |
| C12 | feasibility の手順に、標準を採るかを Q&A 1 問で決め、標準から外れる行だけ個別に決める流れと、版の差分の候補を共有の Q&A に起票する読み方が書いてある。scaffold・proposal の `SKILL.md` が関門を指す | SKILL.md | 関門が文面と指し先（`check-skill-pointers.py`）を読む |
| C13 | カタログ・版（platform-spec と spec-loop を minor。3 種類が揃う）・`check-all.py` と CI の登録・CLAUDE.md の項 | カタログ・CI・CLAUDE.md | `check-plugin-versions.py`・`check-version-bump.py origin/main`・`check-description-sync.py`・`test-check-all.py` |
| C14 | 変異テスト: 3 つの本体（`check-profile-diff.py`・`profile-gate.py`・`check-infra-profile.py`）の docstring の「守ること」の行ごとに変異があり、どれも殺せる。数は手で数えない | テスト | テストが「守ること」の行数と変異の数を突き合わせる |
| C15 | 掛け算: C1〜C14 を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | 関門の委譲 | 計画ファイルの関門の記録 |

C7 に足す行（差分テスト）: 旧（周の base）と新（差分テストを回した成果物）に同じ入力を与えた出力が、正規化したあと、承認済みの変更の一覧に無い違いを 1 件も持たず、新側に挙動の変更を 1 か所入れると差分テストが差分を検出する（Verifier が示す）。
C1 に足す行（プロパティテスト）: 候補の集合について、ライブラリが無いので、代替の生成のテストが、性質を破る変異で落ちる（Verifier が示す）。

- 生成物: なし——図（drawio）も `SKILL.md` の測定値の生成ブロックも触らない（spec-loop の `SKILL.md` は版の 2 行と feasibility・scaffold・proposal の文だけ。dev-loop の `SKILL.md` は触らない。`skill-metrics.py --check` で確かめる）。
- 仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）
- 未証明: 本物の組織の開発ガイド（非公開）の profile に当てたときの版の順とリンクの読み方——この環境に無い。試料は一時のリポジトリで作る（人間のレビューへ）。

プロパティテスト: あり

| 不変条件の番号 | 型 | 性質（任意の x について） | テストの名前 | ライブラリ | 生成の設定 |
| --- | --- | --- | --- | --- | --- |
| C1 | 等価性 | 任意の古い層・新しい層（行の足し・消し・列の変化・リンク）と `profile の行` の ID の集合について、候補の (ID, 種類) の集合が「指した ID ∩（変わった ∪ 消えた ∪ 新しい版で切れた））」をテストの側で別に計算したものと同じで、指していない ID と足した ID を含まない | `test-check-profile-diff.py` の `property_candidates` | 無い（Hypothesis が `pyproject.toml` にも `uv.lock` にも無い）／代替: 標準ライブラリの `random` で層と ID の集合を生成し、本体の純粋な関数 `candidates` に当てる／理由: このリポジトリの検査とテストは標準ライブラリだけ（CLAUDE.md）。不在の周は依存を足さない | 例の数 500・seed は実行ごとに変える（出力する）・層の行の数 0〜8・列の値の変化・ID の重なり・空のリンク・指した ID の数 0〜6（古い版に無い ID を除く） |

  落とした主張（PR コメントに名指しする）: 入力の空間の偏りを Hypothesis の縮小と同じ強さでは確かめていない。

差分テスト: あり

| 項目 | 書くもの |
| --- | --- |
| 旧 | 周の base の SHA `8a13a16f22fbda1e6a98f4f99c158bad746120bd`（`plugins/` を `git archive` でリポジトリの外に取り出す） |
| 新 | `0db99fbf`（1 パス目の指摘対応の後の成果物の SHA。そこから後は計画ファイルだけ。その前は `188edfbb`（433 件・差分 0 件）。前の回は `159f37fc`——決まりの外の項目の文言の違いを見つけ、`188edfbb` で #1456 の文言に戻した） |
| 入力の出どころ | check-infra-profile.py は生成（`確かめたタグ` を置かない設定・`profile の行` の値・タグ・区切りの組み合わせ）。scaffold.py・build-proposal.py はサンプル（`scripts/test-scaffold-screens.py`・`scripts/test-build-proposal.py` の試料の正本のうち profile を使わないもの）。件数: check-infra-profile 400 件（seed 3115210750。旧の終了コードの内訳 0 が 39・1 が 351・4 が 10）、scaffold 8 試料 × 3 モード（`--dry-run`・書く生成・書いた後の `--check`）＝ 24 件、build-proposal 9 試料（`SIGNED`・基盤要件あり・列は空・未決定・`V2`・`V2C`・`V2S`・`SIGNED_S`・未承認） |
| 正規化した項目 | (1) 出力の中の試料の置き場の根（旧と新で一時ディレクトリが違う——本体は引数のパスを出すだけ）。(2) 出力と書いたファイルの `spec-loop 0.133.0`／`0.134.0`（spec-loop の版を上げた分。check-infra-profile の 1 行目と、screen-spec のモックが埋め込む表の出どころ）。(3) 書いたファイルの `sha256: `…``（scaffold の `refs/index.md` がモックの sha256 を書く——モックの中身は (2) を正規化したうえで別に比べている） |
| 承認済みの変更の一覧 | 下の節 |
| 結果 | `0db99fbf` で比べた 433 件・差分 0 件・一覧に無い差分 0 件（check-infra-profile の seed 3667025681）。`188edfbb` でも 433 件・差分 0 件。**陽性対照**: 新側の check-infra-profile の「違反 N 件」の文言を変えた写し（`--mutate`）で 83 件中 43 件の差分（違反の行を出す試料の全部）。前の回（`159f37fc`・400 件）は決まりの外の項目の文言（任意の項目を足した一覧）と版の行で差分が出た——文言は直し、版は正規化した |
| 回した場所 | リポジトリの外（scratchpad の `diff1457/`） |

領域: `確かめたタグ` を置いた設定と、`profile の行` に値がある正本は差分テストの領域の外——そこで振る舞いを変えるのがこの周の目的（C4・C6・C8）。

### 承認済みの変更

承認済みの変更: なし

## 未解決の判断・確認待ち

- 仕様の穴 G1・G2 は推奨で決めた（上の表）。確認の Issue は手順 8 の記録に書く（閉じるのは利用者）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1457-profile-diff-gate`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1457`・起点 `8a13a16f`・base の参照 `origin/main`（refs/remotes/origin/HEAD）・base の SHA `8a13a16f22fbda1e6a98f4f99c158bad746120bd`
- 関門: 1 パス目の Verifier（sonnet・dev-loop:dev-loop-verifier）を `068e030b` に当てた——受入基準を破る反証 0 件、受入基準の外の懸念 2 件（V-1・V-2）。差し込み 10 は Verifier の変異 5 本のうち 4 本が赤・1 本は等価変異、差し込み 11 は 333 件で差分 0・陽性対照で検出。
  1 パス目の `/code-review`（high）を `068e030b` に当てた——指摘 9 件（重要 4・nit 5。CR-1〜CR-9）。採否は下の表。差し戻し: 1 パス目の指摘対応（手順 4 へ）。
- 1 パス目の指摘対応の終点: `0db99fbf`（差分は 0 行でない——2 パス目を回す）。割り目: 割らない（cruise の周）。
- check-all（run-serial 越し・出力 `checkall-1457-2.txt`）: `0db99fbf` の木で 105 本のうち失敗 0。
- 2 パス目: Verifier（sonnet）を `8fa2c5ff`（`0db99fbf` から計画ファイルだけ進めた先端）に当てた——反証 0 件。/code-review（high）を同じ先端に当てた——指摘 6 件（重要 1・nit 5。CR2-1〜CR2-6）。採否は下の表。
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `8fa2c5ff6bc5feda8d55b7cbfe9b7b5fe10c60b5`
- 1 パス目の指摘対応の起点（0 行の判定）: `068e030b332c59d6b8042fbafd3f51b58c6e5e62`
- check-all（run-serial 越し・出力 `checkall-1457-1.txt`）: `159f37fc` の木で失敗 2（`check-plan-counts.py`・`check-plan-scope.py`——計画ファイルの件数の行と 1 行 2 パターン。`a48f932f` で直し、2 本を単独で回して緑）
- 割り目: 割らない（cruise の周）
- 交絡を潰した手順: （実験の後に書く）

## 既知の限界・決着済みの論点

- 仕様の穴 G1・G2（上の表）。
- 抜ける条件 1（`check-spec-exit.py`）とサインオフの前の確かめには profile の関門を入れない——Issue は proposal・scaffold の前を求める。
- spec-loop が「profile を使っている」と読むのは `profile の行` の値だけ（`shared/platform/settings.csv` の置き場所は platform-spec の決まりで、spec-loop は持たない）。設定だけ置いて値の無い案件は関門が何もしない——比べる行が無い。
- 決まりの外の項目の文言（`リポジトリ・profile・タグ のどれか`）は #1456 のまま——差分テストの領域（`確かめたタグ` を置かない設定）で出力を変えないため。任意の項目 `確かめたタグ` は「案件の設定」の原本が持つ。

### 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-1／CR-4 `--sort=-v:refname` がプレリリースのタグ（`v10-rc1`・`v2.0.0-rc1`）を正式な版より後ろに並べ、新しい版にする | 示せる（/code-review の `rev1457/tagorder`） | 無し（C2 は「git の `v:refname` の順」——その順のとおりに動く） | 残課題 |
| V-2 凍結した要求確定のタグの時点の `docs/` に clone の今の最新のタグとの差分を当てるので、profile が後でタグを切ると、その版の提案書を作り直せない（`確かめたタグ` を書けば通る） | 示せる（Verifier が本物の platform-spec で実走: タグ v1→v10 で 1・`確かめたタグ,v10` で 0） | 無し（G1・G2 の決めた値どおりの振る舞い） | 残課題（確認の Issue G1 に帰結として書く） |
| CR-1 新しい版がタグか確かめたタグと同じとき、古い版の層と指した ID の照合の前に返り、無い ID・層の無いタグでも 0 | 示せる（`rev1457/exp1.py`: NOPE-1 で 0） | C3（指した ID が古い版に無いのは 1、古い版の層が無いのは 4） | 直す（古い版の層と ID を先に照らす。守る 1 行・変異・試料 2） |
| CR-2 platform-spec が `scope: project` で入っていると、build-proposal.py が関門を写しの `docs` に当てるので `projectPath` が合わず常に 2 | 示せる（`rev1457/exp3.py`: 4） | C6（関門が 0 なら作る） | 直す（`profile-gate.py` の `check` に正本の `docs` を渡す `locate`。守る 1 行・変異・口の試料 1・口の変異 1） |
| CR-3 層の表の見出し `ID,要約,リンク,項目` を確かめず、`備考` の列が増えた層で偽の候補を出して 1（`check-infra-profile.py` は 4） | 示せる（`rev1457/exp2.py`） | C3（層の表の形が違えば 4。docstring の終了コード 4） | 直す（どちらの版も見出しを確かめて 4。守る 1 行・変異・試料 1） |
| CR-5 C7 の差分テストの陽性対照が 3 本の腕のうち 1 本（check-infra-profile）だけで、scaffold・build-proposal の 11 試料は関門の手前で止まる | 示せる（スクリプト） | 無し（C7 に足す行は「1 か所入れると検出する」——検出した） | 残課題 |
| CR-6 `188edfbb` が差分を 0 にするため正しい文言を戻し、決まりの外の項目の文言に `確かめたタグ` が無い | 示せる（文言） | 無し | 残課題（既知の限界に書いた） |
| CR-7 docstring の「`diff_layers` を読み込む——写さない」が偽（`candidates` は自前でテストのモデルも実装と同じ形） | 示せる（コード） | 無し | 残課題 |
| CR-8 `profile-gate.py` の docstring の「画面の関門と同じ条件」が偽（scaffold は仕様レビューの記録と同じ `--upto` なしで当てる） | 示せる（コード） | 無し | 残課題 |
| CR-9 同じセルに同じ ID を 2 度書くと候補が重複する | 示せる（`rev1457/exp1.py`） | 無し | 残課題 |

## 手順 8 の記録

- この周の起票: 2 件（仕様の穴 G1・G2 の確認の Issue。番号は立てた後に書く）
