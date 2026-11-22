# Issue #1458 — screen-spec: 外部の profile を web-spa の上に重ねて読む（settings.csv・語彙・種別ごとの既定）（#1314）

**不在の周**（`/dev-loop:cruise 1461 --absent` の起動・2026-11-22T03:12Z）。利用者には訊かない。親（cruise #1461）から委譲文で受けた子。
確かめた線（出所: 利用者の確認（起動時・2026-11-22T03:12:23Z、配布を見せて確かめた）＋利用者の確認（周の途中・2026-11-22T03:19:55Z）。cruise の確かめた線（台帳 `issue-1461`））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1461.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.20.1（`SKILL.md` 1957 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1461`））。
版の上げ方: `screen-spec` を **minor**（0.7.0 → 0.8.0。外部の profile の上乗せを読む——能力の追加）。spec-loop は触らない（`external-profile.py` を読み込むだけ）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md` の「版とマージの順」。取り込みの後は CLAUDE.md の #831 の例外どおり軽い 2 本と PR 側の CI）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.20.1/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: `settings.csv` に上乗せする外部の profile（名前・版（タグ）・置き場所）を書けるようにし、外部の profile の画面の層（`spec-profile/<名前>/screens/*.csv`）を
spec-loop の共通の部分（`external-profile.py`）を読み込んで読む。`profile.csv` の `重ねる先` が `settings.csv` の `profile` と食い違えば検査が止める。
重ねるもの: 値の語彙（セルが語彙の中にあるか）と種別ごとの既定の値（既定と違う値に根拠の Q&A の番号があるか）を `check-screens.py` で見る。
列を足すことを許すかを推奨で決める。受け付ける形式の版の範囲を screen-spec の `references/` に表で置く。
親 Issue #1461 の「先に決めたこと」と、#1467〜#1470・#1472 で推奨に決めた値（環境変数 `SPEC_PROFILE_CLONE`・`CLAUDE.md` の行・`gh` で取らない・リンクの数え方）は今の main の実装どおりに使う。

## 変更範囲

触る:

- `plugins/screen-spec/scripts/check-screens.py` — 外部の profile を読む（`settings.csv` の行・spec-loop の `external-profile.py` の読み込み・`重ねる先` の照合・列の上乗せ・語彙・既定）。守る／守らないは docstring
- `plugins/screen-spec/references/profiles.md` — 決まりの原本に「外部の profile」の節（設定の行・画面の層の表の形・形式の版の範囲・足す列と見出し行・語彙・既定・読めないとき）
- `plugins/screen-spec/references/tables.md` — 案件ごとの設定の表に `外部の profile` の行、検査の表と終了コードの 4 に外部の profile
- `plugins/screen-spec/references/spec-loop.md` — 読み込む spec-loop のスクリプトに `external-profile.py`
- `plugins/screen-spec/README.md` — 「いまは」の 1 文と中身の表の profiles の行
- `scripts/test-check-screens.py` — 外部の profile の試料（一時の git リポジトリの profile）・変異・原本との突き合わせ
- `CLAUDE.md` — プロジェクト構成の `check-screens.py` と `test-check-screens.py` の項に 1 句ずつ
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/screen-spec/skills/*/SKILL.md` — 版の 2 行（2 本）
- `docs/plans/issue-1458.md` — この計画ファイル

触らない:

- `plugins/spec-loop/`（`external-profile.py` は読み込むだけ。並行の周 #1471 が触る）
- `plugins/screen-spec/scripts/write-screens.py`・`build-mock.py`・`mkdocs-pages.py`——外部の profile が足した列を知らない（見出し行が決まりと違うとして断る）。`init` の初期値は #1460、起票の候補は #1459
- 既定の答え（節の既定の答え）と起票の候補——#1459
- 外部の profile のリンクの検査——spec-loop の `external-profile.py check` が持つ（`check-screens.py` は呼ばない）
- plugin.json・marketplace.json の description（中身を変えない。共変の検査を起こさない）

依存の追加・更新: なし

## 設計の判断

- `check-screens.py` は、`settings.csv` に外部の profile の行があるときだけ spec-loop の `external-profile.py` を `importlib` で読み込む（写さない）。**行が無い案件は、今と同じコードの道を通る**（受入基準 B1——外部の profile を書いていない案件で結果が同じ）。
  行があるのに spec-loop に `external-profile.py` が無ければ（古い spec-loop）、検査の前に止める（4）——対応する spec-loop の版の下限は上げない（行の無い案件を古い spec-loop で止めない）。
- 探し方は `external-profile.py` の `find_clone` に任せる（環境変数 `SPEC_PROFILE_CLONE` → 案件の `CLAUDE.md` の行）。案件の根は **`docs` ディレクトリの親**（`build-mock.py` の出力の `<docs の親>/build/` と同じ根）。
- **外部の profile が読めない・決まりに合わないときは、検査の前に止める（4）**——clone が見つからない・タグが無い・形式の版が範囲の外・層が無い・`重ねる先` が `settings.csv` の `profile` と食い違う・画面の層の行が決まりに合わない（`種類` の値・表・列・種別）。
  Issue の「`重ねる先` が食い違えば検査が止める」に合わせ、外部の profile の側の誤りは案件の表の違反（1）と分ける。
- **案件の表の側**の誤り（語彙の外の値・根拠の無い既定と違う値・設定の行の形・足した列の無い見出し行）は違反（1）。
- 語彙と既定は、`check-screens.py` が既に持つ「印のあるセルは値の決まりに当てない」「`N/A。実現方式が未定` は値の決まりに当てない」をそのまま使う。
- 既定と違う値の根拠は、その画面の行の `根拠` の列に Q&A の番号があるか（`references/tables.md` の「`根拠` はどの行でも空にしない。Q&A の番号…を書く」の列。番号が Q&A 表に在るかは今の `根拠` の検査が見る）。
- 複製の数: 決まりの原本（`references/profiles.md` の節）1・本体の定数と docstring 1（テストが原本と突き合わせる）・`tables.md` の設定の行と検査の表 1・README の 1 文・CLAUDE.md の 1 句——**分けない理由**: 原本以外は指すだけにし、定数の写しはテストが見る（screen-spec の既存の形）。

### 仕様の穴（不在の線で推奨により決めた。確認の Issue は下の「未解決の判断」）

| # | 穴 | 選択肢 | 決めた値（推奨） | 理由 |
| --- | --- | --- | --- | --- |
| G1 | `settings.csv` に足す項目の名前と書き方（外部の profile の名前・版・置き場所） | A: 1 行 `外部の profile` に `<持ち主>/<リポジトリ> <名前> <タグ>` を空白で区切って書く（案件に 1 つまで）／B: 3 行（`外部の profile のリポジトリ`・`外部の profile`・`外部の profile のタグ`）に分ける／C: `profile` の行の値に `web-spa+org/guide/org@v1` のように書き足す | A | 1 行なら半端に書いた状態（リポジトリだけ・タグだけ）が無く、spec-loop の `CLAUDE.md` の行（`<持ち主>/<名前> <パス>`）と同じ並べ方で読める。C は今の `profile` の値の検査（このプラグインの profile か `未設定`）を変えることになる |
| G2 | 外部の profile に列を足すことを許すか（許すなら宣言の形） | A: 許す——画面の層の行の `種類` を `列` にして宣言し、core と組み込みの profile の列の後ろに宣言の順で足す（見出し行に入るので、表を置く最初の版で決める）／B: 許さない——語彙と既定は今ある列だけに掛ける | A | Issue の例（レイアウトの ID）は今の列に入る場所が無く、B では語彙も既定も掛けられない。足した列を `init`・`add`・`build-mock.py` はまだ知らない（見出し行が違うとして断る）ことは原本に書く |
| G4 | 種別の既定と違う値の根拠を、どこにある Q&A の番号で認めるか（2 パス目の CR2-7 で、Issue の文言を狭めたと指摘された） | A: その画面の行の `根拠` の列に Q&A の番号があれば認める（今の形）／B: 既定と違うセルの中に Q&A の番号を書かせ（`modal（Q-R-003）`）、番号を外した値で語彙と比べる／C: `根拠` の Q&A の行の `反映先` がその列を指すときだけ認める | A | `根拠` は Q&A の番号を書く列と決まっている（`references/tables.md`）。B はセルの値の形を変え、モックや MkDocs の表がセルをそのまま出すので番号が値に混ざる。C は Q&A 表の `反映先` の書き方に依り、今の正本で揃っていない。A の弱さ（無関係な番号でも通る）は確認の Issue に書く |
| G3 | 外部の profile の画面の層の表の形（先頭の `ID,要約,リンク` の後ろの列）と層の名前・形式の版 | A: 層の名前 `画面`、後ろの列 `種類,表,列,種別,値`（`種類` は `列`・`語彙`・`既定`）、受け付ける形式の版は `1` 以上 `2` 未満／B: 種類ごとにファイルを分け（`screens/columns.csv`・`vocabulary.csv`・`defaults.csv`）、ファイルの名前で読み分ける | A | 1 つの形なら、層のファイルをどう分けても（`screens/*.csv`）読み方が変わらない。B はファイルの名前の決まりが増え、`external-profile.py` の `ファイル` の glob と二重になる |

## デプロイ経路

プラグイン（`marketplace.json` のカタログ）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準

不変条件 × 経路（経路は本体の入口一覧から数える——CLI `check-screens.py <docs> [--upto] [--spec-loop]` と、本体を読み込む `build-mock.py`・`mkdocs-pages.py`（`Checker` を作って `read_profile` を呼ぶ）と、
spec-loop の `screen-gate.py`（子のプロセスで CLI を呼ぶ）。外部の profile の入口は `settings.csv` の行・spec-loop の `external-profile.py`（clone の探し方: 環境変数・案件の `CLAUDE.md`）・profile のリポジトリのタグの時点の `profile.csv` と画面の層の表）。

| # | 不変条件 | 経路 | 証明手段 |
| --- | --- | --- | --- |
| B1 | 外部の profile を書いていない案件で、`check-screens.py` の終了コードと出力が変更の前（周の base）と同じ。spec-loop に `external-profile.py` が無くても同じ | CLI（`screen-gate.py` の子のプロセスを含む）・`Checker` を読み込む `build-mock.py`・`mkdocs-pages.py` | 今ある試料が全部そのまま緑（回帰テスト）と、差分テスト（旧 = 周の base の木の `check-screens.py`・新 = 成果物。同じ入力の終了コードと出力を比べる）。`external-profile.py` を外した spec-loop で外部の profile の無い案件が 0 の試料 |
| B2 | 語彙の外の値（core の列・組み込みの profile の列・足した列のどれでも）が、表のパス・鍵・列と外部の profile の名前つきで違反（1）になる。印のあるセル・`N/A。実現方式が未定` のセル・空のセルは当てない | CLI | 一時の git リポジトリの profile に当てる試料と変異 |
| B3 | 種別ごとの既定と違う値で、その画面の行の `根拠` に Q&A の番号が無いものが違反（1）になる（既定の行の ID を名指し）。番号があれば通る | CLI | 同上 |
| B4 | `profile.csv` の画面の層の `重ねる先` が `settings.csv` の `profile` と食い違えば（`未設定` を含む）、検査の前に止めて（4）両方の値を名指しする | CLI | 同上 |
| B5 | 画面の層の形式の版が受け付ける範囲（screen-spec の `references/profiles.md` の表）の外なら、検査の前に止めて（4）名指しする | CLI | 同上 |
| B6 | 外部の profile が読めない（clone が見つからない・タグが無い・画面の層が無い・spec-loop に `external-profile.py` が無い）・画面の層の行が決まりに合わない（`種類`・表・列・種別・重なり）なら、検査の前に止める（4）——黙って外部の profile を外して検査しない | CLI | 同上 |
| B7 | 外部の profile が `種類` `列` で宣言した列が、core と組み込みの profile の列の後ろに宣言の順で見出し行に求められる（無ければ見出し行の違反 1） | CLI | 同上 |
| B8 | `settings.csv` の `外部の profile` の行が決まりの形（3 つの値・1 行まで）でなければ違反（1） | CLI | 同上 |
| B9 | 外部の profile の本文を写さない——検査はファイルを書かず、出力に profile のリンク先の本文が出ない（出すのは profile の名前・行の ID・値だけ） | CLI | 本文に目印の文字列を置いた profile の試料で、出力に目印が無いことと、正本・走らせた場所・profile の clone・読み込んだプラグインのファイルが変わらないこと |
| B10 | 決まりの原本が screen-spec の `references/` に在り（形式の版の範囲の表・設定の行・画面の層の列と `種類` の値・層の名前）、本体の定数と一致する | references・本体 | テストが原本と定数を突き合わせ、原本を崩すと不一致になることを見る |
| B11 | 変異テスト: B2〜B8 の判定を 1 箇所ずつ壊すと、名指しした試料が期待どおりでなくなる | テスト | `test-check-screens.py` の変異 |
| B12 | 版: screen-spec を minor で上げ、3 種類（marketplace.json・plugin.json・SKILL.md 2 本の 2 行）が揃う | 版の行 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| B13 | 掛け算: B1〜B12 を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | 関門の委譲 | 計画ファイルの関門の記録 |

- B1 の受入基準の行（差分テスト）: 旧（周の base）と新（差分テストを回した成果物）に同じ入力を与えた出力が、正規化したあと、承認済みの変更の一覧に無い違いを 1 件も持たず、新側に挙動の変更を 1 か所入れると差分テストが差分を検出する（Verifier が示す）。
- **生成物**: なし——図（drawio）も `SKILL.md` の測定値の生成ブロックも触らない（`SKILL.md` は版の 2 行だけで、screen-spec の SKILL.md は §8.2 の測定の対象外——`skill-metrics.py --check` で確かめる）。
- プロパティテスト: なし（語彙は集合の所属、既定は値の等しさで、入力の空間が広く例を手で選ぶと偏る型（往復・冪等性・数値の境界）に当たらない。形式の版の境界は spec-loop の `external-profile.py` のプロパティテスト（#1455）が持つ）
- 仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）
- **未証明**: 本物の組織の開発ガイド（非公開）の profile に当てたときの読み方——この環境に無い。試料は一時のリポジトリで作る（人間のレビューへ）。

### 差分テスト

差分テスト: あり

| 項目 | 書くもの |
| --- | --- |
| 旧 | `b37059d0d0f6ff317fddadfd2cd866eab10e5cd9`（周の base） |
| 新 | `09937d9178583ca589f876b991dac093e9ead6f2`（N-2 の直しの後に回し直した。前の回は `5968a03b`・`a329ca3e`・`a1348a0f`（127 件・差分 0）） |
| 入力の出どころ | サンプル——`scripts/test-check-screens.py` の試料のうち外部の profile を持たないもの全部（周の base の時点の試料と、この周で足した外部の profile の無い試料）。128 件（外部の profile の行を値つきで持たない試料。この周で足した `ext-none-old-spec-loop`・`ext-setting-empty`・`ext-setting-two-empty` を含む）。比べたのは終了コードと標準出力＋標準エラーの全文 |
| 正規化した項目 | 出力の一時ディレクトリのパス（新旧で別の場所に置くので、`<tmp>` に揃える——比較に関係ない置き場所の違い） |
| 結果 | 比べた 128 件・差分 0 件・一覧に無い差分 0 件。陽性対照: 新側の `起票の候補` の条件を `if False:` にした写しで差分 2 件（`marker-without-number` ほか）——差分を検出する |
| 回した場所 | リポジトリの外（scratchpad。旧は `git archive <旧> plugins/screen-spec plugins/spec-loop` で取り出した木） |

#### 承認済みの変更の一覧

承認済みの変更: なし

## 未解決の判断・確認待ち

- 仕様の穴 G1〜G4 は推奨で決めた（上の表）。確認の Issue を穴ごとに立てる（番号は下の手順 8 の記録に書く）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1458-screen-spec-external-profile`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1458`・起点 `b37059d0`・base の参照 `origin/main`（refs/remotes/origin/HEAD）・base の SHA `b37059d0d0f6ff317fddadfd2cd866eab10e5cd9`
- 1 パス目の指摘対応の起点（0 行の判定）: `fe3a6e3a93250e9c219f16f4027c1fcf7b093902`（関門の 2 つに渡した時点の HEAD。以後 `79d7f709` は計画ファイルだけ）
- 関門 1 パス目: Verifier（sonnet・dev-loop:dev-loop-verifier）を `fe3a6e3a` に当てた——反証 1 件（R1）。`/code-review`（high）を `fe3a6e3a` に当てた——指摘 10 件（important 2・nit 8）。採否は下の表。差し戻し: 1 パス目の指摘対応（R1・CR-2 を直した。`a329ca3e`）。
  Verifier の未確認: `test-check-screens.py` 全体と変異（親が run-serial 越しに回して緑）・承認済みの変更の一覧の確かめの 6 本・`build-mock.py` などが足した列を断る主張。
- `test-check-screens.py`（run-serial 越し）は `a329ca3e` の木で緑（試料 165・変異 133・references の崩し 35）。差分テストを `a329ca3e` で回し直した（127 件・差分 0）。
- 2 パス目: 割り目——割らない（cruise の周）。Verifier（sonnet）を `ffc5d091` に当てた——反証 0 件（軽微な所見 2: 止めた理由の文言・語彙の文言。差分テストの陽性対照を取り直して 5 件以上の差分を検出）。`/code-review`（high）を `ffc5d091` に当てた——指摘 7 件（important 2・nit 5）。採否は下の表。
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `ffc5d09197c58c3d6bf1b88b55423e94e94dee62`・終点（指摘対応の最後のコミット）: `a1348a0f7062ded2a13320f5a26ebbd6bfde5671`。陽性対照: 新しい試料を起点の本体（`ffc5d091`）に当てると `ext-base-mismatch`・`ext-base-unset`・`ext-base-unset-both`（止めた理由の文言）と `ext-setting-empty-and-valued`（終了コード 0）の 4 件が赤、終点の本体で全部緑
- check-all（run-serial 越し）: `ffc5d091` で 102 本 OK（失敗 0）
- 狭いパス: Verifier（sonnet）を `ffc5d091`→`a1348a0f` に当てた——反証 0 件・所見 2 件（N-1: 空の `外部の profile,` の行が 2 つだけの試料が無く、「値つきの行と並んだときだけ数える」変異が素通りする／N-2: 空の行を 2 つ置いた settings が周の base で 0、終点で 1——B1 の「外部の profile を書いていない案件で同じ」から外れる）。自分で設計した変異 6 つのうち 5 つ赤。報告は起動元に届かず、記録（transcript）から読んだ。
- マージ前の判断（線 `推奨で決めて起票（後退・未達を含む）`）: N-2 は狭いパスの指摘で、この周の受入基準 B1 を破る（この周の 2 パス目の直しが持ち込んだ後退）——推奨を決める前にまず直す（`references/absent-lines.md` の「満たしていない受入基準は、推奨を決める前にまず周が直す」）。N-1 は同じ直しの試料で埋まる。直しの起点: `9b8c4083d8e4bd144a4bf8a00285a6e39b28b12f`・終点: `09937d9178583ca589f876b991dac093e9ead6f2`（値のある行があるときだけ空の行も数える）。陽性対照（同じ試料 `ext-setting-two-empty`: 空の行 2 つ）: 直す前の本体 `a1348a0f` で終了コード 1（赤）、周の base `b37059d0` と直した後で 0（緑）。差分テストを回し直した（128 件・差分 0）
- check-all（run-serial 越し）: `fe3a6e3a` で 1 本落ちた（check-plan-counts——件数の行が無かった。`79d7f709` で足した。ほかの 99 本は OK・2 本 CACHED）。`test-check-screens.py`（run-serial 越し）は `5968a03b` の木で緑（試料 162・変異 130・references の崩し 35）
- 交絡を潰した手順: 差分テストは陽性対照（新側を壊した写しで差分が出る）を取った。外部の profile の試料は走らせる場所（cwd）を案件の根と別にし、`CLAUDE.md` を docs の親で探すことが観測に効くようにした（変異「案件の根を docs の親にしない」が `ext-good` で落ちる）
- 割り目: 割らない（cruise の周）

```dev-loop-gates
周の base: b37059d0d0f6ff317fddadfd2cd866eab10e5cd9
関門: Verifier 1 fe3a6e3a93250e9c219f16f4027c1fcf7b093902 反証=1
関門: /code-review 1 fe3a6e3a93250e9c219f16f4027c1fcf7b093902 指摘=10
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

- 足した列を `init`・`add`・`build-mock.py`・MkDocs のフックは知らない（見出し行が決まりと違うとして断る）——Issue の範囲の外（G2。`init` の初期値は #1460）。
- 外部の profile のリンクが切れているかは見ない（spec-loop の `external-profile.py check` が見る）。
- 語彙はセルの値をそのまま比べる（`、` で区切らない）。
- 外部の profile は案件に 1 つまで（G1）。

### 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1（Verifier）`profile` が `未設定` で層の `重ねる先` も `未設定` だと外部の profile が重なる | 示せる（Verifier の実走: 終了コード 1・語彙の違反 2 件。4 で止まらない） | B4 | 直す（`未設定` なら重ねる先に依らず 4。試料 `ext-base-unset-both`・変異「未設定 に重ねさせる」） |
| CR-1 種別の既定（B3）は `根拠` にどの Q&A の番号があっても通る——`根拠` は全行に書くので、ほぼ全行で通る | 示せる（/code-review の実走: S-002 form・`根拠`=Q-R-002・modal で 0） | 無し（B3 は「その画面の行の `根拠` に Q&A の番号が無いもの」と決めており、そのとおり動く） | 残課題 |
| CR-2 B7「宣言の順」を見る試料が無く、足す列の順を逆にする変異が生き残る | 示せる（/code-review の実走: 2 列の試料で変異が 0 のまま） | B7・B11 | 直す（2 列の試料 2 つ——層のファイルをまたぐ・ファイルの中——と変異 2 つ） |
| CR-3a 空の `外部の profile` の行と値つきの行が並ぶと通る（`profile` の行と数え方が違う） | 示せる | 無し（B8 は「値の形・1 行まで」——空の行は使わない扱いと決めた） | 残課題 |
| CR-3b 計画ファイルに件数の行が無い | 示せる | 無し（周の記録） | 捨てる（`79d7f709` で足した） |
| CR-3c 外部の profile の行と `settings.csv` の違反が同時だと見出しの違反を出さずに返る | 示せる | 無し（違反 1 で止まるのは同じ） | 残課題 |
| CR-3d `外部のprofile` など綴り違いの鍵を黙って無視する | 示せる | 無し（B6 は名指した外部の profile を外さないこと。名指しの無い行は設定ではない） | 残課題 |
| CR-3e B9 の「本文の目印が出ない」に陽性対照が無い | 示せる（試料の形） | 無し（B9 の証明は「出力に目印が無い・ファイルを書かない」で、本体は本文を読まない） | 残課題 |
| CR-3f profile の名前が `a/b`・`..` だと違反 1 でなく 4 | 示せる | 無し（名前の形は spec-loop の `external-profile.py` が判定する——読めないは 4） | 残課題 |
| CR-3g `SPEC_PROFILE_CLONE` が別リポジトリの clone を指しても読む | 示せる | 無し（spec-loop の決まり——#1467 の確認の Issue の「守らない」） | 残課題 |
| CR-3h `profiles.md` の「後の版で外部の profile を足すと見出しが違反」は列を足す profile のときだけ真 | 示せる（文） | 無し（文言） | 残課題 |

### 2 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1 足す列の順の 2 つの試料は、宣言の順と行の ID の順・ファイルの名前の順が同じで、ID で並べ替える変異が生き残る | 示せる（/code-review の実走: ID で並べた写しで ext- が全部緑） | B7・B11 | 直す（宣言の順と ID の順・ファイルの名前の順が逆の試料に変え、ID で並べる変異を足す） |
| CR2-2 止めた理由の文言が、原因が `未設定` でなくても「（未設定 には重ねられない）」を付け、両方 `未設定` のとき「食い違う」と言う（V2 の所見 1 と同じ） | 示せる（/code-review の実走: web-spa と desktop で「未設定 には重ねられない」） | B4（止めた理由を名指す——別の原因を出している） | 直す（`未設定` と食い違いを分けて出す） |
| CR2-3 `profiles.md` の「MkDocs のフックは見出し行が違うとして断る」は一部だけ正しい（表の節は足した列を外して出す） | 示せる（文とコード） | 無し（文言） | 残課題 |
| CR2-4 画面の層の行の読まない欄（語彙の行の `種別` など）に書いた値を黙って無視する | 示せる | 無し | 残課題 |
| CR2-5 空の `外部の profile` の行と値つきの行が並ぶと通る——B8 の「1 行まで」と食い違う（1 パス目の CR-3a の決着の理由が誤っていた） | 示せる（/code-review の実走: 違反 0） | B8 | 直す（空の行も数えて 2 行なら違反。試料と変異） |
| CR2-6 `if self.profile is None` と `if external is False` の守りに試料が無い | 示せる（変異が生き残る） | 無し（B2〜B8 の判定ではない守り） | 残課題 |
| CR2-7 CR-1 の決着が循環している——B3 は Issue の「既定と違う値に根拠の Q&A の番号があるか」を「行の `根拠` に番号があるか」と狭めた | 示せる（S-002 の `根拠`=Q-R-002 で 0） | 無し（B3 はこの周の手順 3 で固定した受入基準で、関門の指摘で足さない） | 残課題——根拠の置き場所を仕様の穴 G4 として確認の Issue に回す（下の G4） |

## 手順 8 の記録

- この周の起票: 4 件（仕様の穴 G1〜G4 の確認の Issue。番号は立てたときにここへ書く）
