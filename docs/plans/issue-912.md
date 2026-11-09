# Issue #912 — TLC を spec-loop の必須の前提として明記し、周を回す前に確かめる

不在の周（`/dev-loop:cruise 916 --absent` の起動・2026-11-08T08:00Z、利用者の確認（起動時・2026-11-08T08:00:42Z、配布を見せて確かめた））。cruise #916 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かない）。従う版は dev-loop 1.99.0（キャッシュ。SKILL.md 1861 行）。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-916`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #916 -->`）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認・マージ前の判断: 台帳に線なし（止まる）
- 版の上げ方: **minor・spec-loop だけ**（main の先端 spec-loop 0.72.3 → 0.73.0。autopilot の起動時の点検と spec-review の確かめに TLC の前提を足す——能力の追加）。dev-loop は触らない。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #912`・`Refs #916`
- 並行する周: #919（dev-loop の版を上げる。こちらは spec-loop だけなので版の行は衝突しない）
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.99.0/skills/cruise/scripts/run-serial.py` 越し

## 周の在り処

- ブランチ: `issue/912-tlc-prerequisite`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-912`
- 起点コミット: `a256f5a`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `a256f5a94c6258ecab8fb7e243ba622962db0182`

## 変更範囲

触る:
- `plugins/spec-loop/scripts/check-tlc.py` — 新規。正本の `CLAUDE.md` の 2 つの宣言（`TLC の呼び方:`・`業務フローの形式検査:`）を読み、呼び方で小さいモデル 2 つ（通るもの・違反するもの）を検査させて TLC が在るかを決める。書き方の原本
- `plugins/spec-loop/scripts/autopilot-check.py` — `check` に TLC の項目を足す（`check-tlc.py` を読み込む）。`SPEC_REVIEW_SCRIPTS` に `check-tlc.py`。docstring
- `plugins/spec-loop/skills/autopilot/SKILL.md` — 起動時の点検（§2）の TLC の項目と、各起動（§3）が単位の前に `check-tlc.py --autopilot` で確かめて止まること
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 「はじめに」の表と手順 3 の確かめ（TLC は `check-tlc.py`。`command -v` で探さない）・用意のしかた
- `plugins/spec-loop/agents/formal-checker.md` — TLC は渡された呼び方だけを使い、`command -v` で探さない
- `plugins/spec-loop/README.md` — 「前提」に TLC（既定で必須・用意するもの・`CLAUDE.md` に書く行・外す宣言）、「中身」の表に `check-tlc.py`
- `docs/plugins/index.md` — spec-loop の節の検査器の記述（TLC は既定で必須・呼び方は `CLAUDE.md`）
- `scripts/test-check-tlc.py` — 新規（変異テストを含む）
- `scripts/test-autopilot-check.py` — TLC の項目の試料・変異、`check-tlc.py` の実在
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 同上（CI のステップ）
- `CLAUDE.md` — `check-tlc.py` と `test-check-tlc.py` の項
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（6 本）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-912.md` — この計画
- `plugins/spec-loop/references/spec-exit.md` — 1 パス目の CR1 で広げた: 0.73.0 の移行の手順（リポジトリの `CLAUDE.md` が 0.x の壊れる変更に求める。受入基準 10 を足す）

触らない:
- Alloy（Issue の「範囲の外」）——spec-review の確かめも Formal Checker の探し方も今のまま（`CLAUDE.md` の呼び方か `command -v`）
- autopilot の点検の一覧に TLC の呼び方そのもの（Formal Checker が `Bash` で走らせる）を足すこと——Issue に無い。判定役の中の `Bash` は今も点検の外（autopilot の「守らない」）
- 宣言が古くなった場合を守らせる仕組み——Issue の「やること」2 のとおり足さない（spec-review の今の止まり方が受ける）
- autopilot の frontmatter の description・カタログの description——起動時の点検の要約は変えない
- `docs/plans/` の過去の計画

複製の数（同じことを述べている箇所）: TLC の前提と書き方を述べるのは **7 箇所**——`check-tlc.py` の docstring（原本）・README・spec-review の SKILL（はじめにの表と手順 3）・
`formal-checker.md`・autopilot の SKILL（§2・§3）・`autopilot-check.py` の docstring・公開ページ。
**分けない理由**: 1 つの決まり（書き方と確かめ方）を入口ごとに指すだけで、書き方の表は原本にだけ置き、他は「`check-tlc.py` の docstring を正とする」で指す。
README だけは受入基準 1・2 が「README を読めば分かる」ことを求めるので、書く行の例を載せる。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージで GitHub Pages とプラグインのカタログに入る。マージは親。

## 設計（この周で決めたこと）

- **宣言は正本の `CLAUDE.md`（根）に、行頭から 1 行ずつ**:
  - `TLC の呼び方: <コマンド>`——後ろにモデルのファイル（`<名前>.tla`。設定は同じ名前の `.cfg`）を足して、モデルのディレクトリで `sh` に渡す形（例: `java -cp /opt/tla/tla2tools.jar tlc2.TLC`）
  - `業務フローの形式検査: しない`——必須から外す
  - コードフェンスの中の行は読まない。同じ宣言が 2 行以上・外す宣言の値が `しない` でない・呼び方が空は「判定できない」（4）
- **確かめ方**: 呼び方で 2 つの小さいモデルを検査させる——通るモデル（`No error has been found`・終了コード 0）と、わざと違反するモデル（`is violated` が出る）。
  後者が陽性対照で、何にでも「エラーなし」と言う呼び方を「在る」と読まない。`command -v` では探さない（jar で入れた TLC は見つからない。#368 の CR4）
- **autopilot**: 起動時の確認（§2）の `autopilot-check.py check` に TLC の項目を足す（宣言が無く通らなければ要対処・宣言が有れば確かめずに「人が見る」）。
  各起動（§3）は線の検査の次に `check-tlc.py <正本> --autopilot` を回し、0 でなければ単位に入らず `stopped`——単位を 1 つも進める前に TLC が無いことを示す
- **spec-review**: 手順 3 の 3 で、TLC は `check-tlc.py <正本>`（`--autopilot` なし——対象を選んだときに呼ぶので、外す宣言が有っても確かめる。宣言が古いと出す）
- **Formal Checker**: TLC は呼び出し元が渡した呼び方（正本の `CLAUDE.md` の `TLC の呼び方:` の行）だけを使い、渡されなければ「検査できなかった」

## 受入基準（不変条件 × 経路）

入口: **利用者**（README・公開ページを読む）・**autopilot の起動時の確認**（§2 の `check`）・**autopilot の各起動**（§3）・**spec-review の手順 3**（1 回目・2 回目の確かめと、狭いパスで対象が増えたとき）・**Formal Checker**（呼び方を使う）。

| # | 不変条件 | 経路（入口）と確かめ方 |
| --- | --- | --- |
| 1 | README を読めば、spec-review を回す前に TLC が要ること・用意するもの（Java と `tla2tools.jar`）・`CLAUDE.md` に書く行が分かる（Issue の受入基準 1） | README の「前提」を読む。書いた行が `check-tlc.py` の読み方と一致する（README の例の行を正本の `CLAUDE.md` に写して `check-tlc.py` が読む） |
| 2 | README を読めば、業務フローの形式検査をしない案件が `CLAUDE.md` に何を書けば外れるかが分かる（同 2） | 同上（外す宣言の行を写して `--autopilot` が 0） |
| 3 | 宣言の無い正本・TLC が無い環境で、autopilot が単位を 1 つも進める前に TLC が無いことを示す（同 3）。陽性対照: 呼び方が通る環境では止まらない | §2: `autopilot-check.py check` が TLC を要対処（1）。§3: `check-tlc.py --autopilot` が 1 で、スキルが `stopped` にする手順を持つ。呼び方が通る試料では TLC の項目は良い・`check-tlc.py` は 0 |
| 4 | 宣言の有る正本では、TLC が無くても autopilot の起動時の点検は TLC で止まらない（同 4） | `check` の TLC の項目が要対処でない（人が見る）・`check-tlc.py --autopilot` が 0 で呼び方を走らせない |
| 5 | `tla2tools.jar` だけを置き `CLAUDE.md` に呼び方を書いた環境で、spec-review の確かめが TLC を在ると判定する（`command -v tlc` では見つからない形）（同 5） | `PATH` に `tlc` が無い試料で `check-tlc.py <正本>` が 0——偽の TLC（回帰テスト）と、**本物の TLC 2.19 の jar を `java -cp` で呼ぶ呼び方**（下の「未証明・BLOCKED」） |
| 6 | spec-review の確かめと Formal Checker が同じ呼び方（`CLAUDE.md` の `TLC の呼び方:`）を使い、TLC を `command -v` で探さない。Alloy は今のまま | spec-review の手順 3 と `formal-checker.md` を読む |
| 7 | 写し（README・spec-review・Formal Checker・autopilot・公開ページ・`autopilot-check.py` の docstring）が原本（`check-tlc.py` の docstring）と食い違わない | `git grep -n 'TLC' -- plugins docs ':!docs/plans'` で全部を並べて読む |
| 8 | autopilot の点検の一覧に `check-tlc.py` が入る（各起動が呼ぶスクリプトの許可を点検する） | `autopilot-check.py ops` の出力 |
| 9 | 版が 3 種類の箇所で 0.73.0 に揃う。歯止めが全部緑（新しいテストが `check-all.py` と CI に入る） | `check-all.py`（run-serial 越し）・PR 側の CI |
| 10 | （1 パス目の CR1 で範囲を広げた分）0.73.0 の壊れる変更の移行の手順が `references/` に在り、上の書き方と食い違わない（`PATH` の `tlc` を使っていた正本・TLC を使わない正本の 2 つ） | `references/spec-exit.md` の移行の節を読み、書いた行を `check-tlc.py` に当てる |

**掛け算**: 受入基準を両方の関門 × 2 パス（2 パス目が無ければ 1 パス目の 2 つ）。

### 未証明・BLOCKED

- **未証明・BLOCKED なし。** 受入基準 5 は本物の TLC で確かめた: この環境には利用者が入れた TLC（`~/.local/share/formal-tools/tla2tools.jar`。TLC 2.19・v1.7.4）がある。
  一時ディレクトリの正本の `CLAUDE.md` に `TLC の呼び方: java -cp /Users/hdknr/.local/share/formal-tools/tla2tools.jar tlc2.TLC` を書き、`PATH=/usr/bin:/bin`
  （`command -v tlc` が 1）で `check-tlc.py` が 0。正本には `CLAUDE.md` だけが残った（`states/` は一時ディレクトリ）。陰性: jar の場所を違えた呼び方で 1（`ClassNotFoundException`）。
- **途中で見つけて直したこと（実装の誤り）**: 最初のモデルは算術の `-` を使っていて、`EXTENDS Naturals` が無いので本物の TLC が意味解析で落とした（終了コード 150）。
  偽の TLC はモデルの中身を読まないので、回帰テストでは見えなかった。モデルを `BOOLEAN` と `~` だけの形に直し、本物の TLC で通る（終了コード 0・`No error has been found`）・
  違反する（終了コード 12・`Error: Invariant Inv is violated.`）ことを確かめた。
- 周の途中で公式の `tla2tools.jar` を scratchpad に取って走らせようとした操作は、自動モードの分類器に拒まれた（外から取ったコード）。取ったファイルは消した。上の確かめは利用者が入れた jar で行った。

### 生成物

- 該当なし——図・生成ブロック（`skill-metrics.py` は dev-loop の `SKILL.md` だけを測る）・カタログの生成物を触らない。

## 関門の進捗（再開点）

- 割り目（手順 4・手順 6）: 割らない（cruise の周）
- Verifier 1 パス目（2026-11-09）: **反証 0 件**（軽微な弱点 2 件 W1・W2。報告はトランスクリプトから読んだ）
- `/code-review` 1 パス目（2026-11-09・high・fork）: **指摘 9 件**（CR1〜CR9。報告はトランスクリプトから読んだ）。差し戻し: 直すとした 3 件（CR1・CR3・CR4）を手順 4 で直した
- 2 パス目: Verifier の当て直しと `/code-review` の 2 パス目の**両方**が残る（base は同じ `a256f5a…`）
- 交絡を潰した手順: 偽の TLC の試料で、陽性対照（通る呼び方で 0）と陰性（何にでも「エラーなし」の呼び方・通らない呼び方で 1）を並べた。偽の TLC はモデルを読まないので、モデルが本物の TLC で通るかは本物の TLC 2.19 で当てた（上の「未証明・BLOCKED」）
- 1 パス目の関門の起点（先に当てた関門に渡した時点の HEAD）: 実装のコミット `528fd31` の後にモデルを直したので、直しをコミットした SHA を起点にする——`14de83809cd65dd62b7f9a6073e92f754b3cbc6a`

## 既知の限界・決着済みの論点

- Alloy は範囲の外（Issue）。
- 宣言を守らせる仕組みは足さない（Issue のやること 2）。
- HTML コメントの中の宣言も読む（`check-tlc.py` の「守らない」）。

### 1 パス目の指摘の採否（直す線: 既定）

Verifier（`dev-loop:dev-loop-verifier`・sonnet。読んだ委譲文 181 行。報告は親に届かず（SubagentHandback が「親が居ない」で失敗）、トランスクリプトから読んだ）: **反証 0 件**・軽微な弱点 2 件（W1・W2）。
`/code-review`（high・fork。読んだ委譲文 148 行。`git status` は開始・終了とも ` M docs/plans/issue-912.md`）: **指摘 9 件**（CR1〜CR9）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: 0.x の壊れる変更（`PATH` の `tlc` を探さなくなる・宣言の無い正本で autopilot が止まる）を minor で入れたのに、移行の手順を `references/` に書いていない | 示せる（リポジトリの `CLAUDE.md`「版が 0.x のプラグインは…壊れる変更を minor で入れるなら、移行の手順を原本（`references/`）に書く」と、差分に `references/` が無いこと） | 9（版の決まり） | 直す（`references/spec-exit.md` に移行を書く。変更範囲を広げる） |
| CR3: フェンスの読み方が先頭 3 文字だけ——4 つのバッククォートの中の 3 つのフェンス・info string 付きの行で閉じてしまい、フェンスの中の宣言を読む | 示せる（`/code-review` が ```` の中の ```text の中に `TLC の呼び方: false` を置いて 1 を出した） | 1（README と docstring が「コードフェンスの中の行は読まない」と書き、事実として偽） | 直す（CommonMark のフェンス——同じ文字の 3 つ以上で開き、同じ文字で開きの長さ以上・info string 無しの行で閉じる） |
| CR4: 先頭の UTF-8 の BOM を外さないので、1 行目の宣言を読まない | 示せる（`/code-review` が BOM＋呼び方の `CLAUDE.md` で 1） | 5（BOM で保存した `CLAUDE.md` で、在るのに無いと判定する） | 直す（BOM を外して読む） |
| CR2: §3 の TLC の確かめが段に依らず掛かり、`commit` の段・feasibility も止める（途中で TLC が使えなくなると周の変更が作業ツリーに残る） | 示せる（SKILL の §3 の順） | 無し（3 は単位の前に示すことを求め、それは満たす） | 残課題（周の途中で TLC が使えなくなる形でだけ起きる） |
| CR5: §3 が 4（判定できない）も「TLC が無い」と書き、用意のしかたを案内する | 示せる（SKILL の §3 の文面） | 無し | 残課題 |
| CR6: 外す宣言の後ろに HTML コメントを書くと 4 | 示せる（`/code-review` の試料） | 無し（README は値を `しない` だけと書き、そのとおり書けば外れる） | 残課題 |
| CR7: `<正本の根>` が無い・ファイルだと「TLC が無い」（1） | 示せる | 無し | 残課題 |
| CR8: フェンスの読み方の 4 つ目の写しで、`scripts/test-fence-copies.py` が突き合わせない | 示せない（写しが食い違って起きた失敗は無い） | 無し | 残課題 |
| CR9: 各起動が JVM を 2 回起こす | 示せない（重さの推測。1 回 1.5 秒ほど） | 無し | 残課題 |
| W1（Verifier）: README の例が ```text の中にあり、フェンスごと写すと読まれない | 示せる（Verifier の試料で 1） | 無し（README は「行頭から 1 行で書きます」と書き、細部の原本を指す） | 残課題 |
| W2（Verifier）: `echo "No error has been found; Invariant Inv is violated" #` の呼び方で 0 | 示せる | 無し（わざと作った呼び方） | 残課題 |

## 手順 8

- この周の起票: 0 件（仕様の穴の確認の Issue も、台帳に足す行も無い。起票の承認は不在のため訊いていない）
