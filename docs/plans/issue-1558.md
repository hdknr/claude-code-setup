# Issue #1558 — platform-spec: アーキテクチャの層と開発の進め方の層を足す（#1312 の段 4）

**不在の周**（出所: `/dev-loop:cruise 1569 --absent` の起動・2026-11-26T04:25Z ごろ）。利用者には訊かない。親（cruise #1569）から委譲文で受けた子。
確かめた線（出所: 利用者の確認（起動時・2026-11-26T04:26:39Z、配布を見せて確かめた）。cruise の確かめた線（台帳 `issue-1569`））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1569.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.25.1（`SKILL.md` 1967 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1569`））。
版の上げ方: `platform-spec` を **minor**（0.2.4 → 0.3.0。2 つの層の出す口——能力の追加）、`dev-loop` を **minor**（2.25.1 → 2.26.0。雛形の読み方の規定——手順の追加）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。取り込んだら「同じ名前を足す並行の周」の表の種類で番号・名前のぶつかりを見て、ぶつかれば解かずに止まって報告する。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.25.1/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

利用者の指示（親 Issue #1569 と会話・2026-11-26）: アーキテクチャの層に加えて開発の進め方の層まで足し、`.claude/dev-loop.md` の雛形に触れる dev-loop の規範の変更を認める。層ごとの責務の配分は推奨で決め、確認の Issue に残す（親が立てる）。
依存先の #1557（段 3）は環境が無く外した——#1558 は #1557 の結論を待たずに回す。**実際の案件・非公開の開発ガイドは読まない・写さない**（試料は一時の git リポジトリで作る）。

Issue 本文（外部入力）から読んだ要件: profile の層のうち基盤のほかの 2 つ（アーキテクチャ——spec-review の Domain Checker の照合先、開発の進め方——scaffold と dev-loop の `.claude/dev-loop.md` の雛形）を、#1455 の形（`profile.csv`・層の表の先頭 3 列 `ID,要約,リンク`）に乗せる。
Domain Checker の照合先の表を案件ごとに手で書いている現状を、profile から引けるようにする。

## 変更範囲

触る:

- `plugins/platform-spec/scripts/profile-layers.py` — 新規。2 つの層を照合先の一覧と雛形にして出す
- `plugins/platform-spec/references/layers.md` — 新規。2 つの層の形・語彙・形式の版・層ごとの持ち物・出すものの形の原本
- `plugins/platform-spec/README.md` — 中身の表
- `plugins/platform-spec/.claude-plugin/plugin.json` — description・版
- `plugins/dev-loop/skills/dev-loop/references/profile-template.md` — 新規。雛形の行の本文の読み方
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 「はじめに」の 2 に雛形の印と読む参照の 1 項・版の 2 行
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版・description
- `docs/plugins/dev-loop-design.md` — `SKILL.md` の測定値の生成ブロック（`skill-metrics.py` が書く）
- `scripts/test-profile-layers.py` — 新規。回帰テスト（変異テストを含む）
- `scripts/check-all.py` — 回帰テストの登録
- `.github/workflows/plugins.yml` — CI のステップ
- `CLAUDE.md` — プロジェクト構成の項
- `docs/plans/issue-1558.md` — この計画ファイル

触らない:

- `plugins/spec-loop/`（spec-loop は platform-spec に依存しない。spec-review は正本の `CLAUDE.md` に書いた照合先のパスを読むだけなので、照合先の一覧はそのパスに置けば渡る。`external-profile.py` は読み込むだけ）
- `plugins/platform-spec/scripts/check-infra-profile.py`・`check-profile-diff.py`（読み込むだけ）
- 実際の案件・開発ガイド（#1557。読まない・写さない）
- 2 つの層の版の差分と起票の候補（下の G1）

依存の追加・更新: なし
仕様の振る舞い: 該当なし（このリポジトリに spec-loop の正本は無い）
差分テスト: なし（振る舞いを変えない周ではない——新しい口を足す）
プロパティテスト: なし（入力は CSV の小さい表で、形の違反は試料で 1 つずつ名指せる。往復・冪等・等価の性質を主張しない）
生成物: `docs/plugins/dev-loop-design.md` の生成ブロック（`skill-metrics.py --check` で鮮度を見る）。図の書き出しは触らない（drawio を変えない）

## デプロイ経路

main へのマージで、プラグインの配布（`marketplace.json`）と GitHub Pages の再ビルド（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。マージは親がする。

## 設計の判断

- **本体は platform-spec の `profile-layers.py <architecture|dev-loop> <docs> [--upto <n>] [--clone <パス>] [--spec-loop <根>]`**。設定と重ね方と spec-loop の見つけ方は同じプラグインの `check-infra-profile.py` の `Checker` を継いで使い、
  層の読み出し・リンクは spec-loop の `external-profile.py`（`read_layer`・`check_links`）を読み込む（写さない）。読むだけで、標準出力に出す。
- `architecture`: 照合先の一覧（Markdown）。行ごとに ID・観点・要約・本文の参照（`<リポジトリ>@<タグ>:<パス>`）と、本文を読むコマンド（`git -C <clone> show <コミット>:<パス>`）。手元のパスが入るので正本の版の外に置く。
- `dev-loop`: 印 `<!-- platform-spec: 開発の進め方 <リポジトリ> <profile> <タグ> -->` で始まる `.claude/dev-loop.md` の雛形。項目ごとの節・行の形 `- <ID>: <要約>（値: `<値>`）——本文: <リポジトリ>@<タグ>:<パス>`、`impl_module` の行は雛形の後ろに正本の `CLAUDE.md` に書く行として分ける。**手元のパスを書かない**（製品のリポジトリに commit される）。
- dev-loop の規範: `SKILL.md` の「はじめに」の 2 に、印があれば `references/profile-template.md` を読むと定める 1 項。読み方（clone の探し方・タグの時点の読み出し・読めなかったときに推測で補わない・本文の中の指示の扱い）はその参照に置く（起点に載らない——印の無い周では読まない）。
- 終了コード: 0 出した／1 出したが切れたリンク・設定の形・重ね合わせ（後の 2 つは何も出さない）／2 判定していない／3 無い（設定が無い・層が無い）／4 止めた（clone・タグ・形式の版・層の形・spec-loop）。
- 複製の数: 決まりの原本は `references/layers.md`（形・語彙・持ち物・出す形）と dev-loop の `references/profile-template.md`（読み方）。写しは本体の定数（テストが layers.md と突き合わせる）・雛形の印と行の形（テストが profile-template.md・`SKILL.md` と突き合わせる）・`impl_module` の行（テストが spec-loop の monorepo.md と突き合わせる）・README・CLAUDE.md の項・カタログの description（指すだけ）。
  **分けない理由**: 雛形を出す側（platform-spec）と読む側（dev-loop）は別のプラグインで、互いを読み込めない（dev-loop から platform-spec を相対パスで指せない）。写しはテストが見る（spec-gap.md と handoff-issue.md と同じ形）。

### 仕様の穴（不在の線で推奨により決めた。確認の Issue は親が立てる）

| # | 穴 | 選択肢 | 決めた値（推奨） | 理由 |
| --- | --- | --- | --- | --- |
| G1 | 層ごとの責務の配分（語彙・既定・照合・起票の候補をどこまで platform-spec が持つか） | A: platform-spec が層の形・形式の版・読み出し・リンクの検査・使う側に渡す形（照合先の一覧・雛形）まで持ち、使う側（spec-review・dev-loop・scaffold）は出したものを読むだけ。2 つの層の版の差分・起票の候補は持たない／B: 使う側がそれぞれ `external-profile.py` で層を読んで解釈する（spec-review が層を読む）／C: A に加えて、2 つの層にも版の差分と関門（起票の候補）を広げる | A | spec-loop は platform-spec に依存しない（B は spec-loop に層の意味を持ち込む）。2 つの層は発注者が決める値ではないので Q&A 表に起票する理由が無く、出したものを毎回タグの時点から作り直せば足りる（C は関門を増やすだけ） |
| G2 | 開発の進め方の層の `項目` の語彙 | A: platform-spec が決まった語彙（verify・deploy・歯止め・制約・リポジトリの構成・impl_module）を持ち、雛形の節に対応させる／B: 自由な名前にして、そのまま節にする | A | 雛形の節は dev-loop の「はじめに」が拾うものに合わせる必要があり、語彙が自由だと読む側の拾い先が決まらない。語彙を変えるときは形式の版を上げる |
| G3 | アーキテクチャの層の後ろの列 | A: `観点`（自由な名前・空にしない）／B: 決まった語彙（API の方式・サービスレイヤー・権限）／C: 後ろの列を持たない | A | 観点は組織ごとに違い、Domain Checker は名前を手がかりにするだけで名前で照合しない。空を許すと照合先の一覧で行が何の規約か分からない |
| G4 | 雛形が本文を指す形（`.claude/dev-loop.md` は製品のリポジトリに commit される） | A: `<リポジトリ>@<タグ>:<パス>#<節>` で指し、手元の clone は読む側が `CLAUDE.md` の `外部の profile の clone:` の行で探す／B: 手元の clone のパスを書く／C: 本文を写す | A | B は利用者ごとに違うパスを commit する。C は「本文を写さない」（#1312）に反する。探し方は spec-loop の決まりと同じ行を使う |
| G5 | `impl_module` の行の置き場所 | A: 雛形の後ろに「正本の `CLAUDE.md` に書く行」として分けて出す／B: 雛形の中に入れる／C: 出さない | A | scaffold が読むのは正本の `CLAUDE.md`（spec-loop の monorepo.md の「CLAUDE.md の分担」）で、`.claude/dev-loop.md` ではない。行の形は monorepo.md の例に合わせた |

## verify の受入基準

不変条件 × 経路。経路（入口）は `profile-layers.py` の 2 つのコマンド（`architecture`・`dev-loop`）と、引数（`--upto`・`--clone`・`--spec-loop`）・案件の設定（`shared/platform/settings.csv`）・profile の clone のタグ、
読む側は dev-loop の周（`SKILL.md` の「はじめに」→ `references/profile-template.md`）と spec-review（正本の `CLAUDE.md` の照合先のパス）。

| # | 不変条件 | 破りうる経路 | どう守る・どう確かめる |
| --- | --- | --- | --- |
| 1 | アーキテクチャの層を、設定のタグの時点から、行ごとに ID・観点・要約・本文の参照と読むコマンドを載せた照合先の一覧にして出す | `architecture`・`--upto`・`--clone` | 本体の `architecture`。試料「照合先の一覧」「照合先の読み方」「前の版の時点」「後の版の時点」「引数の clone」 |
| 2 | 開発の進め方の層から、印で始まり、項目ごとの節に決まった形の行を置いた雛形を出し、`impl_module` の行は後ろに分けて出す | `dev-loop` | 本体の `template`。試料「雛形」「雛形の行」「impl_module を分けて出す」 |
| 3 | 雛形（標準出力）に手元の clone のパスを書かない | `dev-loop`（clone の探し方のどれでも） | 試料「雛形に手元のパスを書かない」（一時ディレクトリの名前が標準出力に出ない） |
| 4 | 止まり方を分ける: 設定が無い・層が無いは 3、設定の形・重ね合わせは何も出さずに 1、切れたリンクは出して 1、層の形（見出し・語彙・1 行まで・空・改行）と clone・タグ・形式の版は 4、引数は 2 | 両コマンド・profile のタグ・設定 | 試料（docstring の「守ること」の行ごと） |
| 5 | 読むだけ——clone と正本が変わらない・`__pycache__` を書かない | 両コマンド | テストの「読むだけ」 |
| 6 | 本体の定数が `references/layers.md` と一致し、雛形の印と行の形が dev-loop の `references/profile-template.md`・`SKILL.md` と、`impl_module` の行が spec-loop の monorepo.md と一致する | 原本と本体のどちらかだけを直す | テストの突き合わせ（崩す陽性対照つき） |
| 7 | dev-loop の周が、印のある `.claude/dev-loop.md` を見たら `references/profile-template.md` を読み、本文を手元の clone のタグの時点から読み、読めなければ推測で補わない（verify なら BLOCKED の規定） | dev-loop の `SKILL.md`「はじめに」の 2 | 文面の確かめ（`check-skill-pointers.py` が指し先の実在を見る）。**未証明**——周が実際にそう振る舞うかは eval を回さないと示せない（下） |
| 8 | 層ごとの責務の配分（G1）を原本に書き、spec-loop は platform-spec に依存しないまま（spec-loop を触らない） | `references/layers.md` の「層ごとの持ち物」・spec-loop の `scripts/`・`templates/` | 文面と、`test-check-infra-csv.py` の見張り（spec-loop が platform-spec の名前を持つのは `profile-gate.py` だけ） |
| 9 | 版を 3 か所で揃えて上げ、生成ブロックが新しく、歯止めが全部緑 | 版の行・`SKILL.md`・CI のステップ | `check-plugin-versions.py`・`skill-metrics.py --check`・`check-all.py`・`test-check-all.py`（収録漏れ） |

組み合わせ（必須要件の掛け算）: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（該当すれば）に渡す——4 つの受け渡し（2 パス目が該当なしなら初回の 2 つ）。

証明できないもの（未証明）:

- **7 の振る舞い**——dev-loop の周が印のある `.claude/dev-loop.md` を見て実際に参照を読み、clone のタグの時点から本文を読むかは、`claude plugin eval` を回さないと示せない（CI から呼ばない・課金する。この周では回さない）。文面と指し先の実在までを確かめる。
- **実際の組織の開発ガイドで 2 つの層の形が足りるか**——#1557 と同じく環境が無い（実際の案件・開発ガイドを読まない）。試料は一時の git リポジトリ。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1558-platform-layers`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1558`・起点 `25d08f5d`・base の参照 `origin/main`（`refs/remotes/origin/HEAD`）・base の SHA `25d08f5dd1be61cb41d2a684b04ba5f77f9d585e`
- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目の指摘対応の起点: `ca35c817`（1 パス目の 2 つの関門に渡した時点の HEAD）
- 1 パス目: Verifier（sonnet・`dev-loop:dev-loop-verifier`）を `ca35c817` に当てた——反証 1 件（V-1）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/ccb0151a-cd0f-4f1a-b328-115bd7bc4fd5/scratchpad/gate-1558-verifier-1-20261126T051216Z.md`。
  `/code-review`（high）を `ca35c817` に当てた——指摘 7 件（CR-1〜CR-7）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/ccb0151a-cd0f-4f1a-b328-115bd7bc4fd5/scratchpad/gate-1558-code-review-1-20261126T051216Z.md`。
  `/code-review` には委譲文を貼らず、委譲文のファイル（161 行）を読ませて行数を報告させた（報告は 161 行と言った）。
  差し戻し: 1 パス目の指摘対応（手順 4 へ）——直すのは V-1／CR-1・CR-2・CR-3・CR-4（下の採否の表）。
- 周の途中の事故（申告）: 1 パス目の `/code-review` の委譲文を組むとき、引用符で囲まないヒアドキュメントに委譲文のバッククォートを入れ、シェルがコマンド置換として `claude plugin eval`（このリポジトリの eval を worktree のプラグインで実行・課金）・`git fetch`・`git push`（上流が無く失敗）・`gh`（引数なし）・`claude`（入力なしで失敗）を走らせた。
  `git commit` は変更が無く何も作らず、リモートのブランチは作られていない（`git ls-remote` で確かめた）。worktree に残った `evals/results/` は消した。`git fetch` で手元の参照が更新された（利用者の `fetch.pruneTags` によってはタグが消えうる——確かめていない）。
- 割り目（手順 6 の 2 パス目の前）: 割らない（cruise の周）。残っているのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方。
- 2 パス目: Verifier（sonnet）を `f7fb7b85` に当てた——反証 1 件（R-1）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/ccb0151a-cd0f-4f1a-b328-115bd7bc4fd5/scratchpad/gate-1558-verifier-2-20261126T052719Z.md`。
  `/code-review`（high）を `f7fb7b85` に当てた——指摘 6 件（CR2-1〜CR2-6）。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/ccb0151a-cd0f-4f1a-b328-115bd7bc4fd5/scratchpad/gate-1558-code-review-2-20261126T052719Z.md`。委譲文のファイル 177 行を読ませた（報告は 177 行）。
  `check-all.py`（run-serial 越し）を `f7fb7b85` で回した——失敗 0（34 本を回し、ほかは入力が変わらず CACHED）。
- 狭いパスの起点: `f7fb7b85`（2 パス目の指摘対応を始める直前の HEAD）。直すのは R-1／CR2-1・CR2-2。

```dev-loop-gates
周の base: 25d08f5dd1be61cb41d2a684b04ba5f77f9d585e
関門: Verifier 1 ca35c817 反証=1
関門: /code-review 1 ca35c817 指摘=7
関門: Verifier 2 f7fb7b85 反証=1
関門: /code-review 2 f7fb7b85 指摘=6
マージの反映: ドキュメントとプラグインの配布
```

- 交絡を潰した手順: 実験なし（回帰テストの試料と変異。陰性対照・陽性対照はテストが持つ）

## 既知の限界・決着済みの論点

### 1 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-1／CR-1 `要約` などの改行と `値` のバッククォートを見ず、雛形・一覧に偽の見出し・宣言の行が出る・コードスパンが壊れる | 示せる（Verifier・/code-review の一時の profile で `dev-loop`・`architecture` を走らせた出力） | 2（決まった形の行） | 直す（どの層のどの列も改行で 4、`値` のバッククォートで 4。試料 2・変異 2） |
| V-1 の付記: `要約` が空の行も止まらない | 示せる（Verifier の A-2） | 無し（行の形は崩れない） | 残課題 |
| CR-2 dev-loop の clone の探し方の順が spec-loop と逆なのに「同じ」と書いた | 示せる（`external-profile.md` の「探し方」と profile-template.md の文面） | 7（読み方——雛形を作った clone と別の clone を読みうる） | 直す（環境変数 → `CLAUDE.md` の順にし、引数の口が無いことを書いた） |
| CR-3 印を「先頭の行」でしか見ず、ほかの宣言と並べた雛形を取りこぼす | 示せる（layers.md は並べてよいと言い、SKILL.md は先頭の行だけを見る文面） | 7（印のある `.claude/dev-loop.md` を見たら参照を読む） | 直す（コードフェンスの外のどの行でも印を見る。layers.md に並べるときも印を残すと書いた） |
| CR-4 符号化した `リンク` を書いたまま参照に出し、dev-loop の周が `git show` で読めない。`#節` が slug であることを書いていない | 示せる（/code-review の `docs/a%20b.md` の実測） | 7（本文を clone のタグの時点から読む） | 直す（参照は戻した名前で出す。試料 1・変異 1。profile-template.md に slug の読み方） |
| CR-5 照合先の読むコマンドの中身（`{commit}`→`HEAD`）と、`--clone` の経路の手元のパスをテストが判別しない | 示せない（いまの本体は正しい。変異が生き残る形の指摘） | 無し | 残課題 |
| CR-6 layers.md の「雛形の節の名前は「はじめに」が拾うものに合わせてある」が事実と違う（`リポジトリの構成` は拾われない） | 示せる（SKILL.md の「はじめに」の 1 の項目） | 無し（行の形・読み方は変わらない） | 残課題 |
### 2 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R-1／CR2-1 参照の正規化が `check_links` と食い違う——`./docs/…`・`docs//…`・`docs/x/../…` と、パスは素で節だけ符号化した行が、`git show` で読めない参照のまま 0 で出る | 示せる（Verifier・/code-review が一時の profile で実走し、`git show refs/tags/v1:docs/sub/../g.md` が fatal） | 7（本文を clone のタグの時点から読む）・1・2 | 直す（`check_links` と同じ `_safe_rel` で正規化し、節はいつも戻す。試料・変異を足す） |
| CR2-2 改行の検査が `\n`・`\r` だけで、U+0085・U+2028 などの行の区切りを含む `要約` で `.claude/dev-loop.md` に行頭の宣言を足せる（`commit-gate.py` の `splitlines()` が拾う） | 示せる（/code-review の実測: `検証の関門: enforce` が off に読まれた） | 2（決まった形の行） | 直す（`str.splitlines()` が分ける文字の全部で 4。試料・変異を足す） |
| CR2-3 正本と製品のリポジトリが別のとき、dev-loop の周は製品のリポジトリの `CLAUDE.md` で clone を探すが、その行が要ると書いていない（CR-2 の理由「同じ clone を読む」も偽になりうる） | 示せる（文面） | 無し（見つからなければ「読めなかった」で推測しない——安全側に止まる） | 残課題 |
| CR2-4 `要約` に `——本文:`・`（値:` を書くと、行に偽の参照・値が先に出る | 示せる（/code-review の実測） | 無し（行は決まった形の後ろに本物の参照を持つ。読む側の規定の穴） | 残課題 |
| CR2-5 タグ `v1-->x`・空白を含む profile の名前で印が崩れる | 示せる（`git check-ref-format` が通す） | 無し | 残課題 |
| CR2-6 CLAUDE.md の profile-template.md の項が「先頭の印」のまま（CR-3 の直しと食い違う） | 示せる（文面） | 無し | 残課題 |

| CR-7 profile-template.md が外の本文を対象リポジトリの `CLAUDE.md` より優先させ、`CLAUDE.md` の制約を外の本文で上書きしうる | 示せない（食い違う実例は無い。文面の上の筋書き） | 無し | 残課題 |


- 2 つの層の版の差分と起票の候補は持たない（G1。決着: 採らなかった。理由は G1 の表）。
- 照合先の一覧には手元の clone のパスが入る（決着: 採った。Domain Checker が本文を読めるようにするため。正本の版の外に置くと原本に書いた）。
- spec-loop の spec-review の「はじめに」は変えない（決着: 採った。照合先は正本の `CLAUDE.md` に書いたパスで渡り、spec-loop は platform-spec を知らないまま）。

## 手順 8

- この周の起票: 0 件（仕様の穴 G1〜G5 の確認の Issue は親が立てる——cruise の線 `仕様の穴 = 推奨で決めて起票`）
