# #181 — dev-loop の振る舞いの回帰 Eval（最初の 1 ケース）

## 周の在り処

- ブランチ: `issue/181-dev-loop-eval`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-181`
  （`prepare-worktree.sh` で作り、`EnterWorktree` に `path` で入った）
- 起点: `9602820`（Merge pull request #180）
- base: 参照 `origin/main` → `9602820b110c7fadf5c9dcfec756869f6e01881c`
- 読み込まれた dev-loop は **1.35.0**（`claude plugin list --json` とリポジトリが一致）

## 0. 方針（着手前に決めた）

#181 は方向性の一覧で受入基準を持たない。分析（Issue コメント 5977176842）のうち、
人間が **1: 振る舞いの回帰 Eval** を選んだ。**この周は最初の 1 ケースに限る。**

対象にする振る舞いは **#96 型**——**再開の周（既に周の worktree とブランチがある）で、
worktree を新規作成しない**。失敗の実物がある（#96 で 2 本目の worktree を作って実装をやり直した）。

道具は `claude plugin eval`（Claude Code 同梱）。**CI では回さない**——`claude` を起こして課金する
（`measure-guard-os.sh` と同じ扱い）。

## 1. 変更範囲

触る:

- `plugins/dev-loop/evals/` — Eval ケース（prompt・graders・scaffold）
- `docs/plans/issue-181.md` — この計画ファイル
- `CLAUDE.md` — Eval の置き場所と回し方（`plugins/` の構成の行と、新しい節「振る舞いを Eval で当てる」）
- `plugins/dev-loop/.claude-plugin/plugin.json` — version 1.35.0 → 1.36.0
- `.claude-plugin/marketplace.json` — 同上
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — **版のバナー 2 行だけ**（規範は触らない）

触らない: `SKILL.md` の規範（**規範を変えずに測る仕組みだけ足す**——分析の 2 番目「規範の追加を止める」と整合）、
`scripts/check-all.py`・CI（課金するので組み込まない）、#1737 の帰属違い（別の候補）

（version bump の 3 行は、最初は `触らない:` の下に書いてしまい `check-plan-scope.py` に落とされた。
version bump は `check-version-bump.py` が要求した——`evals/` もプラグインの中身として数える。
**能力の追加なので minor**。広げた分の受入基準: G — 3 箇所が 1.36.0 で揃い、`check-all.py` が緑）

## 2. デプロイ経路

プラグインのカタログ（`plugins/` の変更はマージで利用者のクローンに届く）。サイト（`docs/`）は
計画ファイルのみ。

## 3. 受入基準

**不変条件**: **再開の周で dev-loop は worktree を新規作成しない。**
**それを破る入口**（エージェントが worktree を作る手段）:
(a) `git worktree add`、(b) `prepare-worktree.sh`、(c) `EnterWorktree` に `name`（または引数なし）、
(d) `git checkout -b` / `git switch -c` で周のブランチと別の新ブランチを切る。

| # | 基準 | 証明手段 |
| --- | --- | --- |
| A | ケースが (a)〜(d) のどれかを使った実行を**失敗**と採点する | grader の定義を読む＋変異実行 |
| B | **陽性対照**: 規範から再開の節を抜いた `SKILL.md` で回すと、**実際に (a)〜(d) が起き、失敗と採点される**。起きなければ「このケースは振る舞いを判別していない」と書き、周を閉じない | 変異した版で `claude plugin eval` を回す |
| C | 現行の `SKILL.md` で回すと**通る** | `claude plugin eval` を回す |
| D | scaffold が**実環境に触れない**（一時ディレクトリの中に git リポジトリ・worktree・計画ファイルを作る。`$HOME` のリポジトリを触らない） | scaffold を読む＋実行後に本物の `git worktree list` が変わっていないことを見る |
| E | 回し方と費用が `CLAUDE.md` に書いてあり、`check-all.py` が緑 | 実行 |

**組み合わせ**: B と C は**同じケース・同じ回数**で回す（違う設定で比べると交絡する）。

**2026-10-04 人間の決定で B を狭めた**（`AskUserQuestion`「主張を狭めて PR」）。
元の B（作成を見る grader が #96 修正前の版で赤になる）は**満たしていない**——3 回とも通った
（§5）。**消したのではなく、満たしていない基準として PR に名指しする。** 代わりに置いた基準:

| # | 基準 | 証明手段 |
| --- | --- | --- |
| B' | `ran-find-cycle` が **現行で通り、#96 修正前の版で落ちる** | C4 と M2c（同じ設定・1 回ずつ） |
| B'' | ケースの冒頭と `CLAUDE.md` が、**判別を確かめた grader は `ran-find-cycle` だけ**と書いており、それ以上を主張しない | 読む |
| F | 入口 (c)（`EnterWorktree`）は eval で起こせないことが書いてある（**BLOCKED**） | 読む |

**未証明**: 回数が少ない（`runs` 3 程度）ので、**通過率の差はサンプルが小さい**。B と C の差が
偶然でないことは言えない——**言えるのは「この回数で、この差が出た」まで**。

**生成物**: `SKILL.md` を触る場合だけ `skill-metrics.py` の生成ブロックが該当（version バナーのみなら
節構造は変わらないが、`--check` で確かめる）。図なし。

## 4. 未解決

- `claude plugin eval` のケース書式（guide に確認中）
- version bump の要否

## 5. 関門の進捗（再開点）

- 手順 4: 実装済み（`e4e4b82`・version bump）
- Verifier 1 パス目: **反証 2 件**（V1・V2）＋所見（V3〜V8）。採否は §6。直す 4 件（V1・V3・V4・V6）を直した
  （**V4 は Verifier ではなく親が V3 を直す過程で見つけた**）。**直した分は既存の trace に当て直して結果不変**
- `/code-review` 1 パス目（2026-10-04、effort high、再開したセッションで）: **指摘 10 件**＋軽微 1 件。
  採否は §6。直す 6 件（CR1・CR2・CR4・CR5・CR6・CR10）を直した。**CR7（確定した grader は
  実ハーネスを通っていない）は、C を当て直すことで扱う——課金するので人間に訊く**
- 2 パス目に残っているもの: **手順 5 の当て直し（Verifier）** と **`/code-review` 2 パス目** の両方
- 割り目（手順 4 の完了時）: **訊いていない**——人間の判断（git の修理・着地の選択）を挟みながら 1 セッションで進めた
- 実験（すべて `--runs 1 --ablation none`、子のモデルは `claude-opus-5-5`）:
    - C3（現行 `SKILL.md`）: **4/4 通過**、5 ターン、$0.62
    - M2a（**#96 修正前の `SKILL.md`＝`14fcc7f^`、v1.14.0**）: 3/4。**落ちたのは `ran-find-cycle`
      だけ**（旧版は `find-cycle.py` を持たないので自明に落ちる）。**worktree は作らなかった**——
      既存の worktree を見つけて手順 5 から再開した。13 ターン、$0.92
    - **交絡**: M2a・C3 の子の道具は **8 本で `EnterWorktree` を含まなかった**（trace の init）。
      **入口 (c) が起きえない設定だった**——#96 の実物は `path` 無しの `EnterWorktree`。
      `allowed_tools` と `--allow-tools` に足して M2b を回す
    - M2b（M2a ＋ `EnterWorktree` を許可）: 3/4（同じく `ran-find-cycle` だけ）。12 ターン、$0.72。
      **子の道具は `Task, Bash, Glob, Grep, Read, Skill, TaskStop, ToolSearch` で、許可しても
      `EnterWorktree` は提供されなかった。** 再び既存の worktree から正しく再開した
    - **もう 1 つの交絡: サンドボックスの中で `git` が動かない**（M2b の子の報告:
      `can't exec '/usr/local/bin/git'`。子は `.git/objects` を zlib で読んで代用した）。
      **ホスト側の原因を確かめた**: `/usr/local/bin/git` は `../Cellar/git/2.47.0/bin/git` への
      **切れたリンク**（`/usr/local/Cellar/git` が無い）。ホストの `git` は Xcode の 2.54.0
      （`/usr/bin/git` のスタブ経由）で、**サンドボックスの外では動く**。
      **これで C3 の通過も判別していない**——`find-cycle.py` は `git` に依るので、
      5 ターンで止まったのは「探せなかった（exit 2）→ 人間に訊く」だった可能性がある
      （C3 の trace は `--keep-temp` 前で消えており、**確かめられない**）
    - **陽性対照（基準 B）は取れなかった。** 2 回とも、#96 修正前の版でも worktree を作らなかった
    - 費用の合計: **$2.27**（C3 0.62 ＋ M2a 0.92 ＋ M2b 0.72。scaffold で落ちた 3 回は $0）
- **判定: BLOCKED**（手順 5）。無いもの: **道具**——(1) サンドボックスで動く `git`、
  (2) eval の子に `EnterWorktree`。**人間の判断待ち**
- **人間が (1) を直した**（2026-10-04。切れたリンクを消し `brew install git` → `/opt/homebrew/bin/git` 2.56.0）。
  同じ設定で回し直した:
    - C4（現行）: **4/4**、14 ターン、$1.29。trace で `find-cycle.py` が「当たったものがある」を返し、
      `references/resume.md` を読んで既存の worktree で手順 5 から再開した（**今度は判別している通過**）
    - M2c（#96 修正前）: **3/4**、12 ターン、$1.06。**worktree は作らなかった**。落ちたのは `ran-find-cycle` だけ
    - 費用の合計: **$4.62**
- **結論**: 作成を見る 3 つの grader は、**この条件では修正前後を判別しない**——
  **#96 修正前の版でも、現在のモデルは worktree を作らない**（git あり・なしの 3 回すべて）。
  これは**変異が届いていない**（手順 5）であって、砦の穴ではない。
  **判別したのは `ran-find-cycle` だけ**——言えるのは「**再開の探索を走らせる手順が消えたら赤になる**」まで。
  入口 (c)（#96 の実物）は eval の子に `EnterWorktree` が無いので**引き続き BLOCKED**

## 6. 既知の限界・決着済みの論点

### 1 パス目の指摘の採否（Verifier = `dev-loop:dev-loop-verifier` / sonnet、反証 2 件＋所見）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1. B' は構成上自明——修正前の版に `find-cycle` の記述が 1 つも無いので、`ran-find-cycle` は振る舞いと無関係に落ちる。case.yaml と `CLAUDE.md` は「回帰を捕まえる」と読める | 示せる: `grep -c find-cycle`（`14fcc7f^` の SKILL.md）＝ **0** | B'' | **直す**（判別の理由を「修正前の版に指示が無いから」と書く） |
| V2. 空の未追跡ディレクトリ `graders/` | 示せる（`ls`） | 無し | 残課題（ローカルの残骸。追跡されていないので差分に出ない。消すだけ） |
| V3. `no-new-branch` が `switch -C` / `switch --create` / `checkout -B` / `checkout --orphan` / `branch -c` / `branch foo main` を取りこぼす | 示せる: `scratchpad/re.js` で旧 regex が 4 形を BAD | A | **直す** |
| V4. `input_match` は道具の入力 JSON 全体（`description` を含む）に当たる——広げた regex は C4 の trace に実在する説明文「Show current branch name」に当たる（**V3 を直す過程で親が見つけた**） | 示せる: `re.js` の説明文ケースで BAD | A（偽陽性） | **直す**（`"command"` の値に限る） |
| V5. scaffold のガードを実行で確かめられなかった（ハーネスが拒否） | — | D | **親が実行で確かめ済み**（§7 の 4 形）。Verifier の静的読解とも一致 |
| V6. `CLAUDE.md` の「eval のワークスペース以外では断る」は実装より広い——どのリポジトリにも属さない空の dir は通す | 示せる: §7 の scaf3（空・リポジトリ外）で exit 0 | B''（記述の正確さ） | **直す**（書いてある条件を実装どおりにする） |
| V7. 実の `HOME` がリポジトリだと、その下の空 dir を通す／`/tmp` と `/private/tmp` の比較 | 示せない（このホストの `HOME` はリポジトリではない。eval では一致を実測） | 無し | 残課題 |
| V8. `branch issue/7 --contains HEAD` が偽陽性になりうる | 示せない（実行に現れていない） | 無し | 残課題 |

**graders を変えたので、既存の trace に当て直す**（`scratchpad/regrade.js`。費用なし）。
**陽性対照**: 旧 case.yaml で当て直すと C4 4/4・M2c 3/4（`ran-find-cycle` だけ）で、eval の実結果と回数まで一致した。

## 7. 事故の記録（この周）

**scaffold を手で走らせて、cwd（この周の worktree）を壊した。** 2026-10-04 15:10。
空き場所で試すつもりが、`bash scaffold.sh` を cwd のまま実行した。起きたこと:

- **リポジトリ共有の `.git/config` に `user.name=eval` / `user.email=eval@example.invalid`**
  （全 worktree とメインに効く）
- このブランチに `init` コミット（`.gitignore` と `README.md` を上書き）
- worktree `issue-181/.claude/worktrees/issue-7` とブランチ `issue/7-bump-version`

復旧: `git config --local --unset` 2 件・`git worktree remove`・`git branch -D`・
`git reset --hard 9602820`。**確かめたこと**: `git config --local --get-regexp '^user\.'` が
0 件、`git worktree list` が元の 5 本、`git status` が未追跡 2 件のみ。
**メインの作業ツリーの `git status` は見ていない**（ガードが `-C` を拒否）——
scaffold が書いたのは cwd と共有の `.git/` だけなので、メインのファイルには触れていない。

再発防止: scaffold の冒頭にガードを入れた。**最初の 2 版は eval のワークスペースで落ちた**
（eval は一時 `HOME` を git リポジトリにし、cwd をその下の空の `cwd` にする——診断用の scaffold で実測。$0）。
最終形は「**空でない**か、**`HOME` 以外を根とするリポジトリの中**なら断る」。実行で確かめた 4 形
（すべて scratchpad の中）:

| 場所 | 結果 |
| --- | --- |
| 空でない dir（`scaf4`、ファイル 1 つ・リポジトリ外） | exit 1・`x` だけのまま |
| 別のリポジトリの中の空の dir（`scaf2/emptysub`） | exit 1 |
| 空でないリポジトリ（`scaf2`。**事故と同じ形**） | exit 1・コミット数 1 のまま |
| どのリポジトリにも属さない空の dir（`scaf3`） | exit 0・`find-cycle.py 7` が exit 1（当たり） |
| eval のワークスペース | C4・M2c で scaffold 成功 |

### 1 パス目の指摘の採否（`/code-review` high、指摘 10 件）

eval の grader に**終了状態を見る型は無い**（公式ドキュメント「There are no custom-code graders」。
型は regex / tool_used / tool_order / file_exists / llm / baseline）——CR9 の前提が成り立たない。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1. 「修正前の版でも作らなかった（3 回とも）」は交絡——2 回は `git` が動かず、3 回とも `EnterWorktree` が無い | 示せる: §5 の M2a・M2b の記録（`can't exec`）と子の道具一覧 | B'' | **直す**（判別に数えられるのは M2c の 1 回だけ、と冒頭に書く） |
| CR2. `CLAUDE.md` の「修正前の版に探索の指示が 1 つも無い」は偽 | 示せる: `git show 14fcc7f^:…/SKILL.md` の 199・205・230 行 | B'' | **直す**（偽の文を消し、中身はケースの冒頭を指す） |
| CR3. `no-worktree-add` が `prepare-worktree` の文字列だけで赤（この scaffold では exit 3 で何も作らない） | 示せない（実行の trace に現れていない。node の構成例のみ） | 無し | 残課題 |
| CR4. `no-new-branch` が一覧・git 以外を拾う（`git branch 2>/dev/null` ほか 6 形）。コメントの「一覧は拾わない」と矛盾 | 示せる: `scratchpad/br.js` で旧 regex が 6 形を FP | B''（コメントが事実と違う） | **直す**（`\bgit\s+` を前置・リダイレクトを除外） |
| CR5. `no-new-branch` が作成の 7 形を取りこぼす（`switch --force-create` ほか） | 示せる: `br.js` で旧 regex が 7 形を MISS | A | **直す**（`br.js` 35 例で ng 0。旧 regex は 13 件 ng——陽性対照） |
| CR6. 「何もせずに止まった実行を通過にしない役も兼ねる」は偽（`cat find-cycle.py` でも、exit 2 で止まっても通る） | 示せる: regex の構造（`find-cycle\.py` を含めば当たる） | B'' | **直す**（その主張を消し、見ていないものを書く） |
| CR7. `0ab9468` の grader（`"command"` に限った版）は実ハーネスを通っていない。C・B' の証拠は旧 grader の実行 | 示せる: C4・M2c は `0ab9468` より前の実行 | C・B' | **C を当て直す**（課金。人間に訊く） |
| CR8. 行継続・`python -c`・サブエージェントの中での作成を見ない | 示せない（trace に現れていない） | 無し | 残課題（コメントに見ていないと書いた） |
| CR9. 終了状態で採点すべき | 示せない／手段が無い（上記） | 無し | 残課題 |
| CR10. 「SKILL.md から指示が消えたら」は広すぎる——`14fcc7f^` には `scripts/` も `references/` も無い | 示せる: `git ls-tree -r 14fcc7f^ plugins/dev-loop` が 4 ファイル | B'' | **直す**（「指示とスクリプトの両方が消えたら」に狭める） |
| 軽微. `no-enter-worktree-create` が `{"path":…,"name":null}` を赤にする | 示せない | 無し | 残課題 |

### 2 つ目の割り目（2026-10-04）

`AskUserQuestion` で訊いた——**「このまま続ける」**。CR7 は **C を当て直す（課金承認済み）**。

**この周のセッションからは eval を起動できない**（2026-10-05）——worktree 隔離のガードが
`claude plugin eval` を「shell の eval」と読んで拒否する（Bash からも、利用者の `!` 前置からも）。
C の当て直し（C5）は**人間が別の端末で回す**。

**C5 の 1 回目は読み込みで落ちた**（人間が別端末で実行、$0）——`claude` 2.1.289 が
`--allow-tools EnterWorktree` を「a tool never available in an evaluation」として拒否。
`allowed_tools` と `CLAUDE.md` のコマンドから外し、必ず通るだけだった `no-enter-worktree-create` を消した
（grader は 3 本。入口 (c) は引き続き BLOCKED——F）。

**C5（最終形の grader 3 本・現行 `SKILL.md`・`claude` 2.1.289、人間が別端末で実行）: 3/3、$1.38、167 秒。**
trace（`/private/tmp/e-D5grs3/out/trace.jsonl`）で確かめた: `find-cycle.py 7` が当たり → `resume.md` を読む →
既存の worktree（`issue/7-bump-version`、`merge-base --is-ancestor` が ok）で手順 5 から再開し、Verifier と
`/code-review` を回して、remote が無いので PR の手前で止まった。**判別している通過**（サンドボックスの `git` は
xcrun のキャッシュ警告を出したが動いた）。**CR7 は解消。** 費用の合計: **$6.00**。
eval が `plugins/dev-loop/evals/results/` に結果を書くので、`evals/.gitignore` で除外した。

## 2 パス目（2026-10-05）

- Verifier 2 パス目（`dev-loop:dev-loop-verifier` / sonnet）: **反証 3 件**（R1〜R3）。基準を直接破るのは R1（A）・R2（B''）
- `/code-review` 2 パス目（high）: **指摘 10 件**（CR2-1〜CR2-10）
- **2 パス目で直した行は関門に当て直していない**（打ち切り）。PR コメントに名指しする
- 当て方: `scratchpad/br.js`（56 例。旧 regex は新しく足した 14 例すべてを取り違えた——陽性対照）、
  `scratchpad/regrade.js`（C5 の trace の Bash 12 件に新 grader を当てて `[1, 0, 0]`＝実ハーネスの結果と一致）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1 / CR2-2. `-C <dir>`・`-c`・`--no-pager` の前置きと、`-b` の前の位置引数を取りこぼす | 示せる（`br.js`） | A | **直す** |
| CR2-1. 改行の後のコマンド（JSON の `\n`）に `\b` が当たらない | 示せる（`br.js`。C5 にも複数行のコマンドが実在） | A | **直す** |
| CR2-3. `checkout/switch --track/-t`・`=` つきオプションを取りこぼす | 示せる（`br.js`） | A | **直す**。改名 `-m/-M` は (d) の外として残課題 |
| CR2-9. `<`・`#`・`)` の偽陽性（コメントと矛盾） | 示せる（`br.js`） | B'' | **直す** |
| R2 / CR2-5. 「作成を見る 3 つ」が現行の 2 本と合わない・消した grader は 0 回判別 | 示せる（ファイルの grader 数） | B'' | **直す** |
| CR2-6. 壊れた回が判別しない理由の説明が誤り（grader は発行を数える。本当の交絡は子から周が見えなかったこと） | 示せる（M2b の子の報告: `.git/objects` を zlib で読んだ） | B'' | **直す** |
| CR2-4. 「eval に終了状態を見る grader は無い」は偽（2.1.289 に `file_exists` の `exists: false`、`regex` の `not_contains`） | 示せる（レビューがバイナリのスキーマを読んだ） | B''（コメントの偽） | **主張を消す**。終了状態の grader を足すのは残課題——**CR9 の決着の理由は誤りだった** |
| R3. `CLAUDE.md` に EnterWorktree を外した理由が無い | — | 無し（F は case.yaml で満たす） | 残課題 |
| CR2-7. サブエージェント経由は C5 で実際に起きた（Bash 5 件が sidechain）。`tool_used` が数えるかは未確認 | 示せない（どの grader にも当たる呼び出しが無い） | 無し | 残課題 |
| CR2-8. `no-enter-worktree-create` の削除で無料の歯止めが消えた（読み込み失敗の原因は CLI の `--allow-tools`） | 示せない（その grader が 2.1.289 で読み込まれるかは未確認） | 無し | 残課題 |
| CR2-10. scaffold の「`HOME` 以外を根とするリポジトリ」の条件は冗長 | 示せない（失敗ではなく簡素化） | 無し | 残課題 |
| （Verifier）入口 (c) は eval 経路の限界で、`claude -p` ＋ trace なら起こせるかもしれない | 示せない（試していない） | 無し | 残課題 |

**この周の起票: 1 件**（#183——終了状態で採点する grader。手順 8 で人間が承認）。手順 8 の還元: `CLAUDE.md` に「worktree 隔離セッションからは eval を起動できない」を足した（関門に当てていない）
