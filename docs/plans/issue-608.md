# Issue #608 — docs/plugins に spec-loop の解説ページを足す（Red テストと `--red-check` を含む）

spec-loop の公開ドキュメントは `docs/plugins/index.md` の「## spec-loop」節しかなく、Red テストと `--red-check` は公開ページから辿れない。
`docs/plugins/spec-loop.md` を足し、ナビゲーションと一覧の節からリンクする。

**不在の周**である——出所は `/dev-loop:cruise 793 --absent` の起動（2026-11-03）。親からサブエージェントとして委ねられた。
台帳 `issue-793` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・`周の途中の課題 = 外に出す`
（出所: 利用者の確認（起動時・親 Issue #793 の cruise: の行・2026-11-03T03:56:17Z、配布を見せて確かめた））。台帳は書かない（親が書く）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: **上げない**——`plugins/` を 1 ファイルも触らない（`docs/` と `mkdocs.yml` だけ）ので、CLAUDE.md「プラグインの更新」の対象外。
`check-version-bump.py` が落とすのは `plugins/<name>/` の中身を変えた差分だけ。

重い検査（`check-all.py`・`mkdocs build`）は順番待ち越しに走らせる
（`/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py -- <コマンド>`。`references/parallel.md`）。

## 変更範囲

触る:

- `docs/plugins/spec-loop.md` — 新しい解説ページ
- `docs/plugins/index.md` — 「## spec-loop」節からのリンク、新しいページへ寄せた記述の整理
- `mkdocs.yml` — 「プラグイン」のナビゲーションに 1 行
- `docs/plans/issue-608.md` — この計画ファイル

触らない:

- `plugins/spec-loop/` の中（README・`references/`・`SKILL.md`・スクリプト）——原本は変えない。README から新しいページへのリンクも足さない（版を上げる周になるので、Issue の範囲の外）
- `docs/plugins/dev-loop-*.md`（dev-loop の側の解説。`spec-gap.md` はリンクで指すだけ）
- `docs/plans/issue-219.md` などの過去の計画ファイル（リンクで指すだけ）

### 同じことを述べている箇所の数

新しいページが述べることのうち、既に別の場所にあるもの:

1. 各スキルが止まる点——`index.md` の各スキルの節（と各 `SKILL.md`「止まる」）。新しいページは流れの表に 1 行ずつ置き、`index.md` の各節を詳しい説明として指す
2. Issue の本文が指紋と sha256 を持つこと——`index.md` の `scaffold` の節の箇条書き。**新しいページへ寄せ、`index.md` からは指すだけにする**
3. Red テスト・`--red-check`・Issue の本文の形——原本は `scaffold.py` の docstring・`references/spec-ir.md`・`references/handoff-issue.md`。ページは要点と指し先だけ

（2 パス目の指摘 2-R6 で数え漏れが分かった: 4. Q&A 表の 2 つの層の説明——`index.md` の `req-loop` の節、5. 版の説明——`index.md` の「正本リポジトリの版と凍結」。どちらも新しいページからは 1 文と指し先に縮めて `index.md` に寄せた。）

複製は 5 種。分けない理由: 1 は流れ（順序と止まる点）を一望するための表で、`index.md` のスキル別の説明とは目的が違う。2 は寄せて 1 箇所にする。3 は原本を指す。

## 乗るデプロイ経路

main へのマージで GitHub Pages（`docs.yml`）に公開される（`docs/` の変更がそのままデプロイ）。プラグインの配布は無い（`plugins/` を触らない）。マージは親がする。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| C1 | 新しいページがあり、ナビゲーションと `index.md` の「## spec-loop」節から辿れる | `mkdocs.yml` の nav・`index.md` のリンク（相対パス）・ビルドした site の `plugins/spec-loop/index.html` | ビルドした site にページがあり、nav と `plugins/index.html` に `spec-loop/` へのリンクがある |
| C2 | ページだけで、Red テストが何か・どこで作られるか・何が赤／緑の期待か・`--red-check` が何を見るかが分かり、判定の本体（`scaffold.py` の docstring）へリンクで辿れる | ページの「Red テスト」「`--red-check`」の節 | 節を読む。`scaffold.py` の GitHub の URL がページにある |
| C3 | ページの事実の主張が原本と食い違わない（Red テストの形・ケースとテストの対応・受入基準・`--red-check` の判定・止まる点・データを書く／読むスキル・指紋と sha256） | ページの各主張 × 原本（`scaffold.py`（docstring と生成するテストの雛形）・`spec-ir.md`・`handoff-issue.md`・`tree.md`・各 `SKILL.md`・dev-loop の `spec-gap.md`） | 主張ごとに原本の行と突き合わせる |
| C4 | 5 本のスキルの流れと、各スキルが止まる点（回答待ち・合意待ち・承認待ち・登録の確認）が分かる | ページの流れの図と表 | 表の 5 行に止まる点がある。C3 と同じく各 `SKILL.md`「止まる」と突き合わせる |
| C5 | 決まりの列挙を書き写さず、原本（`references/`・`SKILL.md`・docstring）を「正とする」で指す。`index.md` と重複する記述は一方に寄せる | ページの全節・`index.md` の「## spec-loop」節 | ページに列挙（判定の表・終了コードの一覧・列の一覧・印の一覧）の写しが無い。指紋と sha256 の記述が `index.md` から新しいページへ移っている |
| C6 | ページの指し先が解決する | 相対リンク（`mkdocs build --strict` が見る）・GitHub の URL（main にそのパスがあるか）・公開サイトの絶対 URL（`check-site-links.py`） | `mkdocs build --strict` が通る。GitHub の URL のパスがリポジトリに実在する（スクリプトで数える） |
| C7 | 歯止めを割らない | `check-duplicate-counts.py`（`docs/` も走査）・`check-site-links.py`・`check-plan-counts.py`（この計画ファイル）ほか | `python3 scripts/check-all.py`（順番待ち越し）が緑、PR の CI が緑 |

必須要件の掛け算: 受入基準を Verifier・`/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

### 未証明

- **ページを読んだ人が実際に理解できるか**（C2・C4 の「分かる」）は、書いた側と関門の読解でしか確かめられない。人間のレビューに回す。
- **公開サイトの描画**（Material テーマ・mermaid の図が描かれるか）は、ローカルのビルドの HTML までしか見ない。mermaid はブラウザの JavaScript で描かれるので、ビルドでは図にならない。

### 生成物

該当の判定: 図の書き出し（`diagrams/`）は触らない。`SKILL.md` の測定値（`skill-metrics.py`）は dev-loop の `SKILL.md` だけ。公開サイトはビルドの出力で commit しない（CI がビルドする）。**生成物なし**。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/608-spec-loop-docs-page`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-608`・
  起点 `412ca8f7`（origin/main。`prepare-worktree.sh` の出力）・base: 参照 `origin/main` → `412ca8f78ff7177110e8250dcce4ebcbcf0d624a`
- 割り目（手順 4）: 割らない（不在の cruise）。このまま続ける。
- 1 パス目の指摘対応の起点: `235ca510`（実装のコミット。1 パス目の関門に渡した時点の HEAD）
- 1 パス目: **Verifier（`dev-loop:dev-loop-verifier`・sonnet。指示文 157 行——生成した文面は 156 行で、末尾の改行の数え方の差）反証 0 件**（ただし検証中に著者が指摘対応を作業ツリーに入れたので、前半は `235ca510`、後半は直した後の版を読んだ。`check-all.py` は順番待ちで回していない）。**`/code-review`（high。委譲文を `Skill` の引数に貼って渡した）指摘 8 件**（1-R1〜1-R8。すべて直す）。差し戻し 1 回（手順 4 へ）。
- 歯止め（実装のコミット `235ca510` に）: `check-all.py`（順番待ち越し）58/58 本・失敗 1（`check-plan-counts.py`——件数の行が無い。1-R9 として直した）。
- 割り目（手順 6・2 パス目の前）: 割らない（不在の cruise）。残っているもの: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方。
- 2 パス目: 対象は 1 パス目の指摘対応 `235ca510..c48bafd7`。base は変えない（`412ca8f7`）。2 パス目の指摘対応の起点（狭いパスの起点）: `3159a26d`（`c48bafd7` の後の計画ファイルだけのコミット。関門に渡した時点の HEAD）
- 2 パス目の結果: **Verifier（`dev-loop:dev-loop-verifier`・sonnet。指示文 173 行）反証 0 件**（`mkdocs build --strict` 緑・個別の検査 6 本緑）。**`/code-review`（high。委譲文を `Skill` の引数に貼って渡した）指摘 10 件**（2-R1〜2-R10）。直す 9 件・残課題 1 件。
- 2 パス目の指摘対応: 起点 `3159a26d` → 終点 `a5a36ead`。
- 狭いパス: **Verifier（`dev-loop:dev-loop-verifier`・sonnet。指示文 194 行——生成した文面は 193 行）反証 1 件**（N-1。直さず人間に渡す）。著者の変異: なし。Verifier の変異（原本を走らせて主張と比べる試料）1 本が赤、素通り 0 本。
- 歯止め: `check-all.py`（順番待ち越し）——`3159a26d` で 58/58 本・失敗 0、`c933bea2`（2 パス目の指摘対応の後）で 58/58 本・失敗 0。
- PR #794: `gh pr checks 794` **check pass・build pass・deploy skipping**（`785aee01`）。mergeable: MERGEABLE。マージは親がする。

## 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| 2-R1 「実装が無いとき: v1 か足した機能だけの版に限って判定でき」は誤り（本当の条件は回帰のケースが無いこと）——1-R8 の直しの先 | 示せる——著者が走らせた: 足しただけの v2・実装なしで `--red-check` が 2（「回帰のケース 3 件を判定していない」）、変更だけの v2・実装なしで 0 | C3 | 直す |
| 2-R2 「回帰を判定していないと言って止まります」は scaffold `SKILL.md` 手順 4（止まらずに進めてよい）と食い違う | 示せる——`scaffold/SKILL.md` 手順 4 の「2 で『回帰を判定していない』なら」 | C3 | 直す（スクリプトは 2、スキルは進むと書き分けた） |
| 2-R3 流れの図が dev-loop の仕様の穴を `req-loop` にしか差し戻していない（内部の行は `spec-review`） | 示せる——`spec-gap.md:144` | C3・C4 | 直す（図に内部の表への線を足した） |
| 2-R4 仕様の穴の回答の反映先が、`spec-gap.md:144`（共有は `req-loop`・内部は `spec-review`）と scaffold `SKILL.md` 手順 7（`req-loop` から受け直す）で食い違い、ページは前者に寄せている | 示せる（原本どうしの食い違い） | 無し（ページは原本の一方と一致。食い違いはプラグインの中にあり、この周の範囲の外） | 残課題（PR コメントに記録） |
| 2-R5 データの表の書く／読むがまだ欠けている（共有の表を `feasibility`・dev-loop が読む、反映先と状態を書く、内部の表を dev-loop が読む） | 示せる——`feasibility/SKILL.md` 手順 1・`spec-gap.md:86` | C3 | 直す（足したうえで、表は主な書き手と読み手で全部ではないと明記した） |
| 2-R6 Q&A 表の 2 つの層・版の説明が `index.md` と重複する（C5） | 示せる——`index.md` の `req-loop` の節・「正本リポジトリの版と凍結」とほぼ同文 | C5 | 直す（ページは 1 文と `index.md` への指し先に縮めた） |
| 2-R7 計画ファイルの「複製は 3 種」が誤り | 示せる（2-R6） | 無し（周の記録） | 直す（計画ファイルだけ） |
| 2-R8 流れの表の `scaffold` の止まる点に、commit の決まりが無いときの止まり方（手順 5）が無い | 示せる——`scaffold/SKILL.md` 手順 5 | C4 | 直す |
| 2-R9 「v2 以降は変わった機能だけ Issue にする」に凍結した前の版が崩れていたときの例外が無い | 示せる——`handoff-issue.md:14-15` | C3 | 直す（例外があることと指し先を足した） |
| 2-R10 `--red-check` の v2 以降の列挙から「どちらの版でも未実装」が抜け、列挙が全部に読める | 示せる——`scaffold.py` docstring の 58-59 行 | C3 | 直す（「など」と docstring への指し先を足した） |
| N-1（狭いパス）2-R1 の直しの括弧書き「回帰のケース（変えていない機能のケース）」が狭い——変更した機能の中の変えていないケースも回帰に入る | 示せる——Verifier が走らせた: 機能 1 つの C1 だけを変え C2・C3 はそのまま、実装なしで `--red-check` が 2（「回帰のケース 1 件を判定していない」） | C3 | 直す（#821 の決まりで振り分け直し: この周の受入基準 C3 を破るので「満たしていない受入基準」。括弧を「前の版から変えていないケース。変えた機能の中のものも含む」に直し、その差分だけに Verifier を 1 回当てた） |
| （論点）流れの順序は `req-loop` → `spec-review` → `feasibility` → `proposal` → `scaffold` と書くが、`scaffold` が入力で確かめるのは仕様レビューを抜けたこと（条件 1 と直近の `spec-review` の報告）で、提案書の承認は確かめない | — | — | 採った: ページにそう書く（`scaffold` の `SKILL.md` 手順 1。サインオフの言及は「付けない」の 1 行だけ） |
| 1-R1 「差し戻された質問は、どこから来ても `req-loop` のレビュー会で答えてもらう」は内部の表（`qa-dev.csv`）の行に当たらない | 示せる——`qa-csv.md`「層」・`req-loop/SKILL.md:102`（共有の表だけ読む） | C3 | 直す（共有と内部を分けて書いた） |
| 1-R2 dev-loop の仕様の穴の回答を「必ず `req-loop` で受け直す」と書いている | 示せる——`spec-gap.md:144`（内部の行は `spec-review` が反映） | C3 | 直す |
| 1-R3 内部の Q&A 表の書く／読むが足りない（dev-loop が書く、`spec-review`・`scaffold` が読む） | 示せる——`qa-csv.md:104`（抜ける条件 1 は両方の表）・`spec-gap.md:112` | C3 | 直す |
| 1-R4 `spec/`・要求・中間表現を読む側に `proposal`（仕様書）・`feasibility` が無い | 示せる——`tree.md`「仕様書」・`feasibility/SKILL.md` 手順 2 | C3 | 直す |
| 1-R5 撤去の本文は sha256 を持たない | 示せる——`handoff-issue.md:77` | C3 | 直す |
| 1-R6 赤・緑の期待が追加・変更だけで、撤去・ほかの機能の「周の前に緑なら後も緑」と「もう緑」の例外が無い | 示せる——`handoff-issue.md:68・76` | C2・C3 | 直す |
| 1-R7 `index.md` の scaffold 節の「中間表現が暫定の回答を指していれば止める」が古い（指していなくても止める） | 示せる——`scaffold/SKILL.md:99`・`scaffold.py` の docstring | C3・C5 | 直す（この周が触った節で、新しいページから指される） |
| 1-R8 「v1（足した機能だけ）」は docstring の「v1・追加だけ」を狭めている | 示せる——`scaffold.py` docstring の「実装が無い」の段 | C3 | 直す（実装が無いときの判定として書き直した） |
| 1-R9（歯止め）計画ファイルに件数の行が無く `check-plan-counts.py` が落ちる | 示せる——`check-all.py` の出力 | C7 | 直す（手順 8 の節に件数の行を置いた） |
| 1-V1（Verifier の留意点）`--red-check` の要点を足したことで `scaffold.py` との二重管理が増えた | 示せない（いまの記述は docstring と一致。食い違いの実物は無い） | 無し | 残課題（PR コメントに記録） |
| （論点）`plugins/spec-loop/README.md` から新しいページへのリンクを足さない | — | — | 採った: プラグインを触ると版を上げる周になり、Issue の「やること」に無い |

## 手順 8（経験の還元・起票）

- この周の起票: 0 件（不在の cruise。周の途中の課題は「外に出す」の線で、振り分けで直すとした行は周の中で直した。残課題は PR コメントに記録するだけ）
