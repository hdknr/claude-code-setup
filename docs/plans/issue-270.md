# Issue #270 — サインオフのタグを `signoff/v<n>/req-<k>` に変え、素の `v<n>` タグとの衝突を無くす

## 決定

タグの命名を **`signoff/v<n>/req-<k>`・`signoff/v<n>/budget-<k>`** にする（2026-10-20、`AskUserQuestion` で人間が選択。
#260 の `v<n>/req-signoff-<k>` を置き換える）。候補は他に「平らな `v<n>-req-signoff-<k>`」「命名は変えず制約を文書に書く」。
**残る衝突は素の `signoff` タグだけ**で、それは `signoff-tags.md` に書く。**#260 の名前は読まない**（移行の互換は持たない）。

## 変更範囲

触る:

- `plugins/spec-loop/references/signoff-tags.md` — 命名の原本
- `plugins/spec-loop/references/versions.md` — 提案書の比較の節・「移し方」の手順 4
- `plugins/spec-loop/scripts/check-signoff.py` — 定数・パターン・メッセージ・docstring
- `plugins/spec-loop/scripts/build-proposal.py` — docstring
- `plugins/spec-loop/skills/proposal/SKILL.md` — 本文のタグ名と版
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 本文のタグ名と版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（残り 3 つ）
- `plugins/spec-loop/README.md`
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/index.md` — 公開ページの spec-loop の節
- `CLAUDE.md` — `check-signoff.py` の項のタグ名
- `scripts/test-check-signoff.py` — 試料のタグ名・定数の突き合わせ・衝突の回帰
- `scripts/test-build-proposal.py` — 試料のタグ名
- `docs/plans/issue-270.md`

触らない: `docs/plans/issue-218.md`・`docs/plans/issue-262.md`（過去の周の記録）。proposal の frontmatter の
「（req-signoff）」「（budget-signoff）」——タグ名ではなく承認の呼び名なので据え置き、JSON の description も変えない。

同じことを述べている箇所の数: タグの書式を述べる箇所が **11 ファイル**（原本 1・写しの定数 1・docstring 2・
スキル 2・README・公開ページ・`versions.md`・`CLAUDE.md`・テスト 2）。**分けない理由**: 命名を変えるのは一度に全部変えないと
本体とテストと文書が食い違う（中間の状態に意味が無い）。原本は `signoff-tags.md` で、定数の写しは
`test-check-signoff.py` が突き合わせる。

## 乗るデプロイ経路

main への merge → GitHub Pages の自動デプロイ（`docs/plugins/index.md`）。プラグインは版の bump（0.11.1 → **0.12.0**。
旧い名前を読まなくなる＝既存の使い方が壊れるが 1.0 前なので minor）で利用者に届く。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| A | 素の `v<n>` タグがあるリポジトリでもサインオフのタグを作れ、照合が 0 を返せる（Issue の再現が通る） | 正本リポジトリに `v1` タグがある状態での `git tag`・`check-signoff.py`・`build-proposal.py` | テストに試料「素の `v1` タグと共存」を足し 0 を見る。**逆順（サインオフが先・`v1` が後）も** git で作れることを試料で見る |
| B | 照合が数えるのは `signoff/v<n>/(req|budget)-<k>` だけ——#260 の `v<n>/req-signoff-<k>`・それ以前の `req-signoff-v<n>`・命名に合わない形（`-fix`・`-03`・`v01`）を数えない | `latest` の選び方・`--req`/`--budget` の指定 | テストの「命名に合わない」試料に #260 の名前を足す。パターンから `signoff/` を外す変異で赤 |
| C | 本体の定数（根 `signoff`・`req`・`budget`）が `signoff-tags.md` の表と一致する | 写しのずれ | `test-check-signoff.py` の突き合わせに根を足し、表の根を崩す変異で不一致 |
| D | 旧い書式（`v<n>/req-signoff`・`v<n>/budget-signoff`・`v1/req-signoff-1`）が、過去の記録（`docs/plans/issue-218/262`）と「読まない」と述べる箇所以外に残らない | 11 ファイル・指示語や表の列見出し・メッセージ文字列 | `grep -rn 'req-signoff\|budget-signoff'` を当て、残りを 1 件ずつ説明する |
| E | `signoff-tags.md` が残る衝突（素の `signoff` タグ）と、#260 の名前を読まないこと・取り直すことを述べる。`versions.md` の「移し方」が新しい名前を案内する | 原本・`versions.md` | 読む |
| F | 版が 3 種類（`marketplace.json`・`plugin.json`・5 つの `SKILL.md` の 2 行）で 0.12.0 にそろう | `check-plugin-versions.py`・`check-version-bump.py` | `check-all.py` |
| G | 歯止めと回帰テストが全部緑 | `python3 scripts/check-all.py` | 集計行 |

証明できないもの（未証明）: なし（git の ref の衝突は一時リポジトリで再現できる）。BLOCKED: なし。
生成物の該当判定: **生成物なし**——触る `SKILL.md` は設計 §8.2 の測定（`skill-metrics.py`）の対象が dev-loop だけなので該当しない
（`check-all.py` の `skill-metrics.py --check` で確かめる）。図も触らない。
必須要件の掛け算: 受入基準を Verifier × 1・2 パス目、`/code-review` × 1・2 パス目の 4 つの受け渡しに渡す。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/270-signoff-tag-prefix`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-270`、起点 `2b61f0b`、
  base 参照 `origin/main` → `2b61f0bd945f1cae3c250adca5b3950e6dedd996`
- 読み込まれている dev-loop の版: 1.37.0（リポジトリは 1.41.1）
- 実装: `8d30068` で完了。`test-check-signoff.py` 試料 43・変異 30 緑、`test-build-proposal.py` 試料 35・変異 30 緑、
  `check-all.py` 44/44 本・失敗 0・飛ばし 0（コミット直前の作業ツリー）
- 手順 4 の割り目で `AskUserQuestion` → **「ここで割る」**を選択（2026-10-20）
- 2 パス目の前の割り目で `AskUserQuestion` → **「ここで割る」**を選択（2026-10-20）。再開は Verifier 2 パス目と
  `/code-review` 2 パス目から（同じ base `2b61f0bd945f1cae3c250adca5b3950e6dedd996` を渡す）
- 関門 1 パス目（2026-10-20。base `2b61f0bd945f1cae3c250adca5b3950e6dedd996`）: **Verifier（sonnet・`dev-loop:dev-loop-verifier`）反証 0 件**
  （A〜G すべて一致・`check-all.py` 44/44・`git status` 前後とも空）、**`/code-review`（high）指摘 9 件**——済み。
  採否は下の表（直す 4 件・残課題 5 件）
- 1 パス目の指摘対応: `122f383` で済み（`check-all.py` 44/44・失敗 0・飛ばし 0）
- **残っている関門**: 手順 5 の当て直し（Verifier 2 パス目）**と** `/code-review` 2 パス目の**両方**。
  そのあと 2 パス目で直した行があれば狭いパス（起点は 2 パス目の指摘対応を始める直前の HEAD）
- 関門 2 パス目（2026-10-20。base 同じ）: **Verifier（sonnet・`dev-loop:dev-loop-verifier`）反証 0 件**
  （A〜G 一致・`check-all.py` 44/44・失敗 0。最後の `git status` は Verifier が走らせておらず、親が空であることと
  本物のリポジトリに `signoff*`・`v<n>/*` のタグが無いことを確かめた）、**`/code-review`（high）指摘 7 件**
  （`check-all.py` は時間切れで未確認と報告）。採否は下の「2 パス目の指摘と採否」（直す 2 件・残課題 5 件）
- **狭いパスの起点**: `3ecd6ab`（2 パス目の指摘対応を始める直前の HEAD）
- 反証・差し戻し: Verifier の反証は 1・2 パス目とも 0 件のため差し戻しなし
- 交絡: 陽性側（素の `v1` と共存して 0）に加え、**陰性側も 2 つの関門が実測で確かめた**——`v1` がある状態で
  `git tag v1/req-signoff-1` は rc=128、`git tag signoff/v1/req-1` は rc=0。旧い名前に戻すと試料は `CalledProcessError` で止まる

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 命名 | `signoff/v<n>/<種類>-<k>` を採った | 人間が選択（上の「決定」） |
| 素の `signoff`・`signoff/v<n>` タグとの衝突 | 残す（文書で述べる） | 階層を持つ名前は、途中までと同名のタグと必ず衝突する（1 パス目の R3 で `signoff/v<n>` を足した）。根を `signoff` にしたのは人間の選択 |
| #260 の名前の互換 | 持たない（読まない・取り直す） | 旧い名前は `v<n>` タグのあるリポジトリでは作れなかったうえ、#262 と同じく取り直しで足りる |
| proposal の frontmatter の「req-signoff」 | 据え置き | タグ名ではなく承認の呼び名。変えると JSON の description との共変も要る |

### 1 パス目の指摘と採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1 `signoff-tags.md` が #260 の名前の取り直しを `versions.md` の「移し方」に送るが、そこは版を分ける前の手順で v1 に付けよと言う（版を分けたあとの #260 の利用者に合わない） | 示せる——`versions.md:166` の見出し「版に分ける前の正本リポジトリ」と `:183-185` の「`signoff/v1/req-1` を付ける」 | E | 直す——#260 の名前は同じコミットに同じ版・番号で付け直すと `signoff-tags.md` に書き、`versions.md` の手順 4 からは #260 の名前を外す |
| R2 照合が 2 を返したとき、旧い名前のタグしか無いことを示さず、スキルが「承認が無い」と案内する | 示せない（旧い名前のタグを持つ正本リポジトリの実物は無い） | 無し | 残課題 |
| R3 `signoff/v<n>` という名前のタグとも衝突するのに、残る衝突を素の `signoff` だけと書いている | 示せる——`signoff/v1/req-1` がある状態で `git tag signoff/v1` が rc=128（`/code-review` の実測） | E | 直す——`signoff-tags.md` に `signoff/v<n>` も書く。決着済みの論点「素の signoff だけ」の理由が不完全だった |
| R4 「承認を 1 つも記録できなかった」は言い過ぎ（リリース前の版なら作れた。代わりに `v<n>` でリリースできなくなる） | 示せる——`v2/req-signoff-1` を先に作ると `git tag v2` が rc=128（Verifier の実測）、`v3/x` の後の `git tag v3` が rc=128（`/code-review`） | E | 直す——`signoff-tags.md` の記述を 2 つの壊れ方に分ける |
| R5 A の経路に挙げた `build-proposal.py` に、素の `v1` タグと共存する試料が無い | 示せない（失敗はしない）が、A の証拠が `check-signoff.py` 側にしか無い | A（証拠の欠け） | 直す——`test-build-proposal.py` に試料「素の v1 タグと共存する」を足す（試料 36 件・変異 30 件で緑） |
| R6 #260 の名前の試料（`v1/req-signoff-2`）を殺す変異が無い | 示せない（手で当てると殺せた） | 無し | 残課題 |
| R7 旧い名前に戻すと、素の `v1` の試料は判定ではなく `CalledProcessError` で止まる | 示せない（赤にはなる） | 無し | 残課題 |
| R8 旧い名前を読まなくなる変更を minor（0.11.1 → 0.12.0）で上げている。`CLAUDE.md` の表では壊れる変更は major | 示せない（`CLAUDE.md` の表に 1.0 前の例外が無いことは事実だが、F は 0.12.0 にそろうことを見る） | 無し | 残課題——人間の判断（major にするか、1.0 前の扱いを `CLAUDE.md` に書くか） |
| R9 `tag_form` と `tag_pattern` が命名を 2 箇所で組み立てている | 示せない | 無し | 残課題 |

### 2 パス目の指摘と採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| P1 #260 の名前の付け直しの案内が、旧いタグを消すことを言わない（残ると `v<n>` を作れないまま） | 示せる——`v2/req-signoff-1` と `signoff/v2/req-1` がある状態で `git tag v2` が rc=128（`/code-review` の実測） | E・A | 直す——取り直したあとで旧いタグを手元とリモートから消すと書く |
| P2 「取り直してもらう」と「付け直す」が同じ段落で食い違い、proposal の「付け直さない」とも同じ動詞でぶつかる | 示せる——`signoff-tags.md:26-27`・`proposal/SKILL.md:38` | E | 直す——承認した人に新しい名前で取り直してもらう、に揃え「付け直す」を外す |
| P3 計画の「決定」と E が残る衝突を素の `signoff` だけと書く | 示せない（周の記録で、成果物ではない） | 無し | 残課題（関門は計画ファイルを検査しない） |
| P4 `test-build-proposal.py` の素の v1 の試料が判別していない（`v1` の手順を消しても緑） | 示せない（不変条件 A は破れていない） | 無し | 残課題（R7 と同じ形） |
| P5 `test-check-signoff.py` の素の v1 の試料のコメント「どちらの順でも作れなかった」が当てられていない | 示せない | 無し | 残課題（R7 と同じ形） |
| P6 大文字小文字を区別しないファイルシステムで `Signoff` も衝突する | 示せない（実測なし） | 無し | 残課題 |
| P7 表の「例」の列と本文の根が定数と突き合わされていない | 示せない（変異で緑のままになるが、表のタグ列は突き合わせている） | 無し | 残課題 |
