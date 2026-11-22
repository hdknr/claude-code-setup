# Issue #1460 — screen-spec: 基盤の profile が名指しする画面の profile を init の初期値にする（#1314）

**不在の周**（`/dev-loop:cruise 1461 --absent` の起動・2026-11-22T03:12Z）。利用者には訊かない。親（cruise #1461）から委譲文で受けた子。
確かめた線（出所: 利用者の確認（起動時・2026-11-22T03:12:23Z、配布を見せて確かめた）＋利用者の確認（周の途中・2026-11-22T03:19:55Z）。cruise の確かめた線（台帳 `issue-1461`））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1461.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.20.1（`SKILL.md` 1957 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1461`））。
版の上げ方: `screen-spec` を **minor**（0.8.0 → 0.9.0。`init` が基盤の profile から初期値を引き、外部の profile を書ける——能力の追加）。spec-loop・platform-spec は触らない。
並行の周 #1459 も screen-spec の版を上げる——マージの直前に親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.20.1/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: 基盤の外部の profile が「画面は `web-spa` + `<外部の profile>`」と名指ししていれば、screen-spec の `init`（`write-screens.py init`）がそれを
`settings.csv` の初期値にする。利用者に確かめて決めるのは今と同じ。今の「`shared/infra.csv` のフロントエンドの行から `profile` を推す」は、基盤の profile が無いときの既定として残す。
screen-spec は platform-spec に依存しない——名指しは共通の部分（spec-loop の `external-profile.py`）を読み込んで profile の `profile.csv` から読む。
#1314 のコメントの「決めたこと」: `profile.csv` の `重ねる先` で組み込みの profile を名指しし、提案 5 の `init` の初期値にこれを使う。
platform-spec（#1456）の決まり: 案件の基盤の profile は正本の版の中の `shared/platform/settings.csv`（`項目,値`。`リポジトリ`・`profile`・`タグ`）。

## 変更範囲

触る:

- `plugins/screen-spec/scripts/write-screens.py` — `hint` が基盤の profile の名指しを出し、`init` が引数を省いたときの初期値を基盤の profile から引く。`--external` で外部の profile を書く（足す列を見出し行に入れる）
- `plugins/screen-spec/scripts/check-screens.py` — `read_external` から、設定の行に依らない読み込み（`load_external`）を切り出す（`write-screens.py` が読み込む。検査の振る舞いは変えない）
- `plugins/screen-spec/references/tables.md` — 案件ごとの設定の表の既定と `profile` の初期値の項、`init` の節
- `plugins/screen-spec/references/profiles.md` — 「外部の profile」に基盤の profile から引く初期値の小節、足した列を `init` が知る
- `plugins/screen-spec/references/spec-loop.md` — `external-profile.py` を読み込むのが `write-screens.py` にも増える 1 句
- `plugins/screen-spec/skills/init/SKILL.md` — 手順 2・3（基盤の profile の名指しを推し、`--external` を渡す）と版
- `plugins/screen-spec/skills/add/SKILL.md` — 版の 2 行
- `plugins/screen-spec/README.md` — 触るなら 1 句（`init` の説明が初期値に触れていれば）
- `scripts/test-write-screens.py` — 基盤の profile の試料（一時の git リポジトリの profile）・変異・platform-spec の定数との突き合わせ・platform-spec の無い形
- `CLAUDE.md` — プロジェクト構成の `write-screens.py` と `test-write-screens.py` の項に 1 句ずつ
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1460.md` — この計画ファイル

触らない:

- `plugins/platform-spec/`（読み込まない。設定の置き場所と項目名は screen-spec に写し、テストが突き合わせる）
- `plugins/spec-loop/`（`external-profile.py` は読み込むだけ）
- `add`・`build-mock.py`・`mkdocs-pages.py` が外部の profile の足した列を知らないこと（#1458 で原本に書いた限界。この Issue は `init` だけ）
- 既定の答えから起票の候補を出すこと——#1459
- plugin.json・marketplace.json の description

依存の追加・更新: なし

## 設計の判断

- **基盤の profile** = 重ねた全体の `shared/platform/settings.csv`（platform-spec の決まり）が名指す外部の profile（`リポジトリ`・`profile`・`タグ`）。
  **名指し** = そのタグの時点の `profile.csv` の層 `画面` の `重ねる先`（空でない）。名指しがあれば、初期値は `profile = <重ねる先>`・`外部の profile = <リポジトリ> <profile> <タグ>`（同じ束の画面の層を重ねる）。
- 名指しが無い（`profile.csv` に `画面` の層が無い・`重ねる先` が空）・基盤の profile が無い（`shared/platform/settings.csv` が無い）なら、今の初期値（`profile = 未設定`・外部の profile の行なし）。
- **初期値が効くのは `--profile` と `--external` を両方省いたときだけ**。どちらかを渡したら基盤の profile を読まず、省いた方は今の既定（`未設定`・行なし）。
  スキルは利用者に確かめた値を 2 つとも明示で渡す。`--external なし` で外部の profile を書かない（`settings.csv` の外部の profile の値は `/` を含むので `なし` と重ならない）。
- `init` が外部の profile を書くときは、check-screens.py と同じ読み方（`load_external`——spec-loop の `external-profile.py` で探してタグの時点の画面の層を読み、`重ねる先` を `profile` と照らし、行の決まりを見る）で読み、
  足す列を見出し行（core＋組み込みの profile の列の後ろ、宣言の順）に入れる——入れないと直後の `check-screens.py` が見出し行の違反にする。
- **screen-spec は platform-spec を読み込まない**——設定の置き場所・見出し・項目名（`shared/platform/settings.csv`・`項目,値`・`リポジトリ`・`profile`・`タグ`）を `write-screens.py` に写し、
  テストが platform-spec の `check-infra-profile.py` の定数と突き合わせる（screen-spec の既存の「写し＋テスト」の形）。設定の値の形の検査は写さない——値は spec-loop の `external-profile.py` が読むときに判定する。
- 複製の数: 決まりの原本（`tables.md` の設定の表と項・`profiles.md` の小節）2・本体の定数と docstring 1（テストが原本と突き合わせる）・`init` の SKILL.md の手順 1・CLAUDE.md の 1 句——
  **分けない理由**: 原本以外は指すだけにし、定数の写しはテストが見る（screen-spec の既存の形）。

### 仕様の穴（不在の線で推奨により決めた。確認の Issue は下の「未解決の判断」）

| # | 穴 | 選択肢 | 決めた値（推奨） | 理由 |
| --- | --- | --- | --- | --- |
| P1 | 基盤の profile が在るのに画面の初期値を決められないとき（profile の clone が見つからない・タグが無い・`profile.csv` が読めない・設定の形が違う・`重ねる先` が screen-spec に無い profile）、引数を省いた `init` をどうするか | A: 止める（4）——何も書かず理由を出す。利用者は値を明示して渡せば進める／B: 今の初期値（`未設定`・外部の profile なし）に落として書き、警告を出す | A | B だと、組織の profile を使う案件で clone が手元に無いだけで profile の無い表が置かれ、見出し行は版の間で変えられない（`references/profiles.md` の「選び方」）ので後から直せない。check-screens.py も外部の profile を読めなければ外して続けずに止める（#1458） |

## デプロイ経路

プラグイン（`marketplace.json` のカタログ）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準

不変条件 × 経路（経路は本体の入口一覧から数える——CLI `write-screens.py hint|init <docs> [--prefix] [--profile] [--external] [--spec-loop]`・`init` のスキル（`hint` → 利用者に確かめる → `init`）・
`write-screens.py` を読み込む MkDocs のフック（`mkdocs` の口だけ。`init` は呼ばない）。基盤の profile の入口は重ねた全体の `shared/platform/settings.csv`・spec-loop の `external-profile.py`
（clone の探し方: 環境変数 `SPEC_PROFILE_CLONE`・案件の `CLAUDE.md` の行）・profile のリポジトリのタグの時点の `profile.csv` と画面の層の表。
`check-screens.py` の切り出しの経路は CLI・`Checker` を読み込む `build-mock.py`・`mkdocs-pages.py`・spec-loop の `screen-gate.py`（子のプロセス）。

| # | 不変条件 | 経路 | 証明手段 |
| --- | --- | --- | --- |
| A1 | 基盤の profile の画面の層が `重ねる先` を持つ試料で、引数を省いた `init` が `settings.csv` に `profile,<重ねる先>` と `外部の profile,<リポジトリ> <profile> <タグ>` を書き、表の見出し行に組み込みの profile の列と外部の profile が足す列を入れ、直後の `check-screens.py` が 0。`hint` がその初期値を出す | CLI（`hint`・`init`） | 一時の git リポジトリの profile に当てる試料と変異 |
| A2 | 名指しが無い（画面の層が無い・`重ねる先` が空）・基盤の profile が無い場合、`init` が書くファイルの中身・終了コード・出力が周の base と同じ | CLI（`init` の引数を省く・渡す） | 回帰テスト（今の試料が全部緑）と差分テスト（旧 = 周の base の木の `write-screens.py`・新 = 成果物） |
| A3 | 明示の引数が初期値に勝つ——`--profile`・`--external` のどちらかを渡せば基盤の profile を読まず（読めない基盤の profile があっても止まらない）、渡した値を書く。`--external なし` なら外部の profile の行を書かない | CLI（`init`） | 試料と変異 |
| A4 | 引数を省いた `init` で基盤の profile から初期値を決められないとき（P1 の 5 つ）、4 で止めて理由を出し、何も書かない | CLI（`init`） | 試料と変異 |
| A5 | screen-spec が platform-spec を読み込まない——`plugins/screen-spec/` の中に platform-spec のファイルを読み込む・指す箇所が無く、platform-spec の無い置き方（screen-spec と spec-loop だけ）で A1 が通る。写した設定の置き場所・見出し・項目名が platform-spec の定数と一致する | 本体・テスト | テスト（platform-spec を置かない一時ディレクトリで A1 の試料、写しと platform-spec の定数の突き合わせと崩すと落ちること） |
| A6 | `check-screens.py` の検査の結果が切り出しで変わらない（外部の profile の有無に依らず） | CLI・`Checker` を読み込む口 | 回帰テスト（`test-check-screens.py` が全部緑）と差分テスト（`test-check-screens.py` の試料を旧と新に当てる） |
| A7 | `init`・`hint` は Q&A 表を書かず、書くのは作業中の版の `requirements/screens/` の中だけ。profile の clone（作業ツリー・HEAD・参照）を変えない。0 以外では何も書かない | CLI | 試料の前後で正本と clone を比べる |
| A8 | 決まりの原本（`tables.md`・`profiles.md`）が初期値の決め方・`--external` を書き、本体の定数が原本と一致する。`init` の SKILL.md が `hint` の基盤の profile の行から推して確かめ、2 つを明示で渡す | references・本体・スキル | テストが原本と定数を突き合わせ、原本を崩すと不一致になることを見る。スキルは関門が読む |
| A9 | 変異テスト: A1・A3・A4・A5 の判定を 1 箇所ずつ壊すと、名指しした試料が期待どおりでなくなる | テスト | `test-write-screens.py` の変異 |
| A10 | 版: screen-spec を minor で上げ、3 種類（marketplace.json・plugin.json・SKILL.md 2 本の 2 行）が揃う | 版の行 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| A11 | 掛け算: A1〜A10 を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（あれば）で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | 関門の委譲 | 計画ファイルの関門の記録 |

- A2・A6 の受入基準の行（差分テスト）: 旧（周の base）と新（差分テストを回した成果物）に同じ入力を与えた出力が、正規化したあと、承認済みの変更の一覧に無い違いを 1 件も持たず、新側に挙動の変更を 1 か所入れると差分テストが差分を検出する（Verifier が示す）。
- **生成物**: なし——図（drawio）も `SKILL.md` の測定値の生成ブロックも触らない（screen-spec の SKILL.md は版の 2 行と手順の文で、§8.2 の測定の対象外——`skill-metrics.py --check` で確かめる）。
- プロパティテスト: なし（初期値は設定の有無と 1 つの列の値で決まる分岐で、往復・冪等性・数値の境界の型に当たらない。形式の版の境界は spec-loop の `external-profile.py` のテストが持つ）
- 仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）
- **未証明**: 本物の組織の開発ガイド（非公開）の profile に当てたときの読み方——この環境に無い。試料は一時のリポジトリで作る（人間のレビューへ）。

### 差分テスト

差分テスト: あり

| 項目 | 書くもの |
| --- | --- |
| 旧 | `64e41878be4eace2a420d09e424a73a14006ced8`（周の base） |
| 新 | `fb37d7dc`（実装のコミット） |
| 入力の出どころ | サンプルと生成——(1) `init`: 正本の試料 9 つ（空の v1・基盤要件と Q&A と機能一覧つき・置き済み・版が無い・重ね合わせの違反・作業中の版が v2・基盤の profile に画面の層が無い・`重ねる先` が空・v2 に置いた基盤の profile に画面の層が無い）× 引数の組 12（省く・`--prefix SCR-`・`--profile web-spa`・`--profile 未設定`・`--profile desktop`・`--prefix s-`・`Q-`・`TBD-`・`F-`・`--profile web-spa --prefix A1-`・値の無い `--prefix`・知らない引数）= 108 件。終了コード・出力・書いたファイルの中身を比べた。(2) `check-screens.py`: `scripts/test-check-screens.py` の試料の全部 167 件（外部の profile の試料を含む）を同じ `run_one` で旧と新に当て、終了コードと出力を比べた。計 275 件 |
| 正規化した項目 | 出力の一時ディレクトリのパス（新旧で別の場所に置くので `<tmp>` に揃える） |
| 結果 | 比べた 275 件・差分 0 件・一覧に無い差分 0 件。陽性対照 2 つ: 新側の `base_initial` の「画面の層が無い」を `web-spa` を返す形にした写しで差分 4 件（`base-no-screen` と `base-no-screen-v2` の引数を省く・`--prefix SCR-`）、新側の `load_external` の既定の重なりの判定を外した写しで差分 1 件（`ext-default-duplicate`）——どちらも差分を検出する。スクリプトは scratchpad の `diff-1460/difftest.py`（残さない） |
| 回した場所 | リポジトリの外（scratchpad。旧は `git archive <旧> plugins/screen-spec plugins/spec-loop` で取り出した木） |

#### 承認済みの変更の一覧

承認済みの変更: なし

## 未解決の判断・確認待ち

- 仕様の穴 P1 は推奨で決めた（上の表）。確認の Issue: （立てた後に書く。閉じない。Refs で指す）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1460-init-from-platform-profile`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1460`・起点 `64e41878`・base の参照 `origin/main`（refs/remotes/origin/HEAD）・base の SHA `64e41878be4eace2a420d09e424a73a14006ced8`
- 1 パス目の指摘対応の起点（0 行の判定）: `fb37d7dc`（関門の 2 つに渡した時点の HEAD の成果物。以後の計画ファイルだけのコミットは除いて判定する）
- 関門 1 パス目: Verifier（sonnet・dev-loop:dev-loop-verifier。verifier.md 250 行を読んだ）を `fb37d7dc` に当てた——反証 0 件（気づき 3 件は下の採否の表）。報告は起動元に届かず、親が回した。
  Verifier の未確認: `test-screen-spec-pages.py`・`test-screen-gate.py`・`test-check-screens.py` の単体（run-serial の順番待ち）、11 の表の正規化を外す確かめ・承認済みの一覧の 6 本・取り出した木の rev-parse。
  前者 3 本は親の check-all（run-serial 越し。`65ae5893` の木＝成果物は `fb37d7dc` と同じ）で OK（`test-check-screens.py` 111 秒・`test-screen-gate.py` 29 秒・`test-screen-spec-pages.py` 54 秒・`test-scaffold-screens.py`・`test-build-mock.py` も OK）。
  Verifier の差分テストの陽性対照: `base_initial` の基盤無しの戻り値を変えた写しで差分 6 件。`/code-review`（high）を `fb37d7dc` に当てた——指摘 7 件（重要 2・nit 5。下の採否の表）。報告は親が回した。差し戻し: 1 パス目の指摘対応（CR1-1・CR1-2 を直す）。
- check-all（run-serial 越し）: `65ae5893` で 1 本落ちた（check-plan-counts——件数の行が無かった。`5fda6505` で足した。ほかは OK・78 本 CACHED）
- 交絡を潰した手順: 差分テストは陽性対照（新側を壊した写しで差分が出る）を init と check-screens の両方で取った。基盤の profile の試料は、clone を案件の根（docs の親）の `CLAUDE.md` の行で探させ、環境変数 `SPEC_PROFILE_CLONE`・`GIT_*` を外した（手元の環境で別の clone を読まない）。platform-spec を読み込まないことは、読み込まれたら印を書く偽の platform-spec を隣に置き、読み込む変異で印が出ること（陽性対照）を取った
- 回帰テスト: `test-write-screens.py`（run-serial 越し）は `fb37d7dc` の木で緑（試料 61・変異 56・雛形の崩し 14・references の崩し 11・platform-spec の写しの崩し 3）。`test-check-screens.py` は同じ木で緑（試料 167・変異 137・references の崩し 35）
- 割り目: 割らない（cruise の周）

## 既知の限界・決着済みの論点

- 外部の profile の足した列を `add`・`build-mock.py`・MkDocs のフックはまだ知らない（#1458 で原本に書いた限界）——`init` が足した列つきで置いた表に `add` は断る。この Issue の範囲の外。
- 基盤の profile の設定（`shared/platform/settings.csv`）の値の形の検査は platform-spec の `check-infra-profile.py` が持ち、screen-spec は写さない（読めなければ P1 のとおり止める）。

### 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-1（Verifier の気づき）`hint` の出力が、基盤の profile が無いときも `基盤の profile: … が無い` の 1 行だけ増え、差分テストは `init` しか比べていない | 示せる（Verifier の実走） | 無し——「振る舞いを変えない」は A2（`init` が書くもの・終了コード・出力）と A6（`check-screens.py`）だけで、`hint` は Issue の要件どおり基盤の profile の名指しを出すために変える口（A1 の「`hint` がその初期値を出す」）。承認済みの変更の一覧は差分テストの比べる範囲（`init`・`check-screens.py`）の一覧で、`hint` はその範囲に入れていない | 残課題（記録だけ） |
| V1-2（Verifier の気づき）設定の項目の重なりのエラー文の空白が揃っていない | 示せる（文） | 無し（文言） | 残課題 |
| CR1-1（/code-review）引数なしの `init` が設定の `リポジトリ`・`profile`・`タグ` を確かめずに `外部の profile` の行へ写す——`リポジトリ,guide`・空白を含む profile で `init` は 0 で書くが、直後の `check-screens.py` が違反 1 | 示せる（/code-review の実走。直した後の試料 `base-repo-without-slash`・`base-name-with-space` が、確かめを外す変異で赤） | A1（直後の `check-screens.py` が 0） | 直す（`base_initial` で行に写せる形か確かめ、駄目なら 4） |
| CR1-2（/code-review）`hint` は画面の層の形式の版・行を確かめないので、`init` が拒む初期値（形式の版 2）を推し、`init` は「初期値を引いた」と出してから 4 で止まる | 示せる（/code-review の実走。試料 `base-screen-layer-version-out-of-range`——確かめを外す変異で赤） | A1（`hint` が出すのは `init` の初期値。拒まれる値は初期値でない） | 直す（`base_initial` で `load_external` を当て、通った値だけを初期値にする——`hint` と `init` の両方） |
| CR1-3（/code-review）`load_external` の文言が settings.csv を前提にしている・`--external` だけで選んでいない「profile が '未設定'」が出る | 示せる（文言） | 無し（A6 で `check-screens.py` の出力は変えない） | 残課題 |
| CR1-4（/code-review）A5 の罠は `check-infra-profile.py`・`__init__.py` の実行しか拾わず、静的な走査が無い | 示せる（試料の形） | 無し（A5 は罠の印と platform-spec を置かない形で示している） | 残課題 |
| CR1-5（/code-review）`test-write-screens.py` の試料で同じ文字列への `replace` が何もしておらず、見出し行全体を比べていない | 示せる | 無し（見出し行は `EXT_S_HEAD`・`EXT_T_HEAD` で比べている） | 残課題 |
| CR1-6（/code-review）`--profile` だけを渡すと、基盤の profile が名指す外部の profile を黙って落とす | 示せる | 無し（A3 は明示の引数が勝つと決めた。スキルは 2 つとも明示で渡す） | 残課題 |
| CR1-7（/code-review）コミットが `Refs #1460` で `Fixes` が無い | 示せる | 無し（周の記録） | 捨てる（PR の本文に `Fixes #1460` を書く） |
| V1-3（Verifier の気づき）`--external` だけを渡すと 4 | 示せる | 無し（設計どおり——省いた `--profile` は `未設定` で、`未設定` には重ねられない。A3） | 残課題（決着） |

## 手順 8 の記録

- この周の起票: 1 件（仕様の穴 P1 の確認の Issue）
