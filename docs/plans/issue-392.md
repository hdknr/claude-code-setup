# Issue #392 — dev-loop: stacked な周の連鎖（下の PR のマージ後の載せ替え・周の在り処の書き方）

#389（オートクルーズ）の要件候補 3 を分けたもの。Issue 本文は信頼できない入力として読み、要件だけを拾った
（本文には指示の類は無かった）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/stacked.md` — 新規。積んだ周の原本（いつ積むか・周の在り処・PR の base・下のマージ後の載せ替え・関門との関係）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 4 の stacked の項と手順 3 の「周の在り処」・手順 6 の PR 作成・手順 7 のマージから `references/stacked.md` を指す。版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 「どう再開するか」の 4 番目（「台帳はまだ扱っていない（#392）」）を stacked.md へ繋ぐ
- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py` — PR の base が既定ブランチでなければマージしない（新しい終了コード）
- `scripts/test-merge-pr.py` — 上の試料と変異
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` で再生成。手で書かない）
- `docs/plans/issue-392.md` — この計画

触らない:

- `scripts/ledger.py`（台帳に新しい鍵を足さない。積んでいることは「依存先がマージ済みでないのに impl/gate/pr にいる」で台帳から読める）
- `prepare-worktree.sh`（`DEV_LOOP_BASE_REF` で積む経路は既にある）
- `find-cycle.py`・`check-pr-preconditions.sh`
- #393（利用者不在の判断の線）の範囲——**利用者不在で積んでよいか**はそちらで決める。ここでは「積むのは親の判断で、そう記録する」まで

### 同じことを述べている箇所の数

- 「積んだ周の base」: `SKILL.md` 手順 4 の 1 箇所（原本）。stacked.md はそこを指し、式を複製しない。
- 「積んだ周をどう扱うか」: 新しい原本 stacked.md の 1 箇所。`SKILL.md`（3 箇所の指し先）・`ledger.md`（1 箇所）・`merge-pr.py` の docstring（1 箇所）は指すだけ。
  計 5 箇所が同じ概念に触れるが、列挙を持つのは stacked.md だけ。分けない理由: 指し先だけなので、直すのは原本 1 箇所で済む。

## 乗るデプロイ経路

`plugins/` の変更はマーケットプレイス経由（版を上げる）。`docs/plugins/dev-loop-design.md` は GitHub Pages（main への push で自動デプロイ）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| S1 | 積んだ周の PR は、下の PR がマージされる前は**下のブランチを base にする**（main を base にすると下の差分が上の PR に混ざる） | `gh pr create` を素で打つ（base は既定ブランチになる） | stacked.md に `--base` を書く。手順 6 から指す |
| S2 | **上の PR が下のブランチへマージされない**——下の PR を squash した後も下のブランチは残る（`merge-pr.py` はブランチを消さない）ので、base を付け替えずにマージすると上の変更は main に届かない | `merge-pr.py`／素の `gh pr merge` | `merge-pr.py` が PR の base と既定ブランチを比べ、違えばマージしない（新しい終了コード）。素の `gh pr merge` は stacked.md の手順で守る（機械では守らない——未証明ではなく、範囲の外として明記） |
| S3 | 下の squash の後の載せ替えで、**上の周の差分が上の周のコミットだけになる**——`git merge-base origin/main HEAD` は squash の後は下の元のコミットを含んだ点を返さない（下の元のコミットが main に無い）ので、式を当て直すだけでは下の差分が上に混ざる | 載せ替えずに base の式だけ当て直す／`git rebase origin/main`（下の元のコミットを上に載せ直そうとして衝突する） | stacked.md: `git rebase --onto <既定ブランチ> <記録した base の SHA>`。一時リポジトリで squash を再現し、旧い形で混ざること・新しい形で上の周のコミットだけになることを実測 |
| S4 | 載せ替えた後の「周の在り処」が当て直せる——**参照の名前と解決した SHA の両方**、積み先の履歴（積み先の名前・下の Issue/PR・載せ替えの時点）が残る | 計画ファイルの書き方 | stacked.md に書き方を置く。手順 3 の 5 番目から指す |
| S5 | 下の周が動いた（関門の指摘対応で下にコミットが足された）ときも、上の周の自分のコミットの範囲が `<記録した base>..HEAD` のまま正しい | 上に下を `git merge` で取り込む（範囲が崩れる） | stacked.md: 下を取り込むのは `rebase --onto <下のブランチ> <記録した base>` で、記録した base を更新する。一時リポジトリで実測 |
| S6 | 載せ替えで上の周のパッチが変わったら、変わった行が関門を通らずにマージされない | 衝突を手で解いた載せ替え | stacked.md: `git range-diff` で比べ、変わったら狭いパスと同じ形で Verifier を 1 回当てる（パスに数えない）。CLAUDE.md の取り込みの歯止めを回す |
| S7 | 台帳: 依存先が PR 中のうちに積んだ Issue を、依存先がマージされた時点で載せ替える対象として見つけられる | `ledger.py show` の読み方 | ledger.md の 4 番目を stacked.md へ繋ぐ（`ledger.py` は変えない） |
| M1 | `merge-pr.py`: base が既定ブランチなら従来どおり。base が違えば `gh pr merge` を呼ばず、worktree も撤去しない。既定ブランチが読めなければ 7 | 待つ間に base が付け替わる・`gh repo view` の失敗 | テストの試料（陽性対照つき）と変異。「守る」の行と変異の 1 対 1・終了コードの一覧の一致はテスト自身が数える |
| X1 | 全歯止めが緑・版が 3 箇所で揃う・生成ブロックが新しい | 全体 | `python3 scripts/check-all.py` |
| X2 | 新しい指し先（`references/stacked.md` の「X」）が実在する | 散文の指し先 | `check-skill-pointers.py`（X1 に含まれる） |

規定の掛け算: 受入基準 × 2 つの関門 × 2 パス（1 パス目の指摘対応の差分が 0 行なら 2 パス目は無い）。2 パス目で直した行には狭いパス。

### この環境で証明できないもの

- **本物の GitHub の挙動**: 下のブランチを base にした PR に対する `closingIssuesReferences` の中身、`gh pr edit --base` の後の CI の再実行、下のブランチが GitHub 側で消えたときの上の PR の base の自動付け替え（1 パス目 C1）。偽の `gh` と一時リポジトリでは当たらない。
  ここに寄りかかる主張は書かない（S2 の守り方は `baseRefName` と既定ブランチの比較だけに依る）。人間のレビューに回す。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`。references の一覧と行数が載る）——再生成して `--check` が緑。
- 図の書き出し: 該当なし（drawio を触らない）。

## 未解決の判断

- 無し

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `ledger.py` に「積み先」の鍵を足すか | 採らない | 積んでいることは依存と状態から読める。積み先と base の正は計画ファイル（台帳はポインタ。`ledger.md` の分担）。2 箇所に書くと片方だけ古くなる |
| 素の `gh pr merge` で base を付け替えずにマージする経路を機械で止めるか | 採らない（文書で守る） | `gh` を包む手段はこのリポジトリに無い。`merge-pr.py` を通る経路だけを機械で止める |
| 利用者不在で積んでよいか | ここでは決めない | #393（判断の線）の範囲。stacked.md は「利用者が許した範囲に従う」まで |
| `--force-with-lease` を使う | 採る（上の周の自分のブランチだけ・**期待する SHA を名指しする形**） | `rebase --onto` の後は push が非 fast-forward になる。素の形は fetch の直後では何も守らない（1 パス目 C2 で実測して直した） |
| 下のブランチが GitHub 側で消えたときの base の自動付け替え（1 パス目 C1） | 残課題・未証明 | 本物の GitHub の挙動。stacked.md は「確かめていない」と書くところまで弱めた |
| 本物の GitHub の挙動（下のブランチを base にした PR の `closingIssuesReferences`、`gh pr edit --base` の後の CI） | 未証明 | 偽の `gh` と一時リポジトリでは当たらない。主張をそこに寄りかからせない |
| 素の `git rebase main` が衝突するか | 「衝突しうる」まで | 衝突したのは下に後からコミットを足した試料の 1 件だけ。衝突しない場合を否定していない |

### 1 パス目の採否

直す線は既定（「示せる」かつ「破る受入基準がある」だけ直す）。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | `merge-pr.py`: 最後の読みから `gh pr merge` までの間の base の付け替えは見ない（＝C8） | 示せない（窓の存在は読解のみ） | 無し（M1 の「待つ間」はループ内） | 残課題 |
| V2 | 待つ間に base が変わる試料がテストに無い | 示せない（実装は正しい） | 無し | 残課題 |
| V3 | 素の `git rebase main` の衝突が再現しない | 親が `stack-exp.sh` を再実行して CONFLICT を再現（Verifier の 2 試料は別の形） | 無し | 変えない（本文は「衝突しうる」まで） |
| C1 | 人間が UI でマージしブランチ自動削除が効くと、GitHub が上の PR の base を main に付け替え、歯止めが素通りする | 示せない（本物の GitHub の挙動。この環境の外） | S2・S3・S6 に触れうる | 残課題（PR コメントで人間に名指し。未証明の欄にも載せる） |
| C2 | 素の `git push --force-with-lease` は fetch の直後では何も守らず、上流が無いと 128 で失敗する | 示せる（`lease-exp.sh`: 上流なしで rc=128／fetch 後の素の形は他の clone のコミットを消した／SHA を名指しした形は rc=1 で残した） | S3（載せ替えの手順が完了しない） | 直す |
| C3 | ledger.md 4 番目から「積むなら人間の判断」を消し「親の判断」にした——#393 の範囲を緩める向きに決めている | 示せる（`git diff` の削除行） | 変更範囲（#393 は触らない）を黙って越えた | 直す（元の「人間の判断」に戻す。stacked.md の 1 も同じ） |
| C4 | 5 で base を先に付け替えると、push までの間 base=main・head=載せ替え前になり歯止めが開く | 示せる（その状態の PR は `merge-pr.py` の試料「既定ブランチなら 0」と同じ形で通る） | S2・S3 | 直す（push を先に、base の付け替えを後に） |
| C5 | 「載せ替える前の HEAD を書いておく」が rebase の後の 4 にある。`ORIG_HEAD` に触れない | 示せる（手順の順序） | S6（range-diff の左の範囲が失われうる） | 直す（2 に移し、`ORIG_HEAD` を添える） |
| C6 | range-diff の読み方が `=`／`!` だけで、`<`（消えた）・`>`（増えた）を扱わない | 示せる（レビューの再現: `1: … < -: … Y1`） | S6 | 直す（全部 `=` 以外は変わったと読む） |
| C7 | 依存先を `merged` にした後、台帳からは積んでいた Issue が見分けられず、再開した側が載せ替え待ちを見失う | 示せる（`ledger.py` の推定は依存先が未マージの間だけ。merged の後は通常の `pr` と同じ表示） | S7 | 直す（`merged` にする前に `note` を「載せ替え待ち」にし、載せ替え後に「載せ替え済み」にする） |
| C8 | V1 と同じ | 示せない | 無し | 残課題 |
| C9 | 「下の周にコミットが足されたら」の rebase 先がローカルの下のブランチで、取り直しが無い | 示せる（古い参照なら古い先端に載る——`origin/<下>` で切った周では手元の参照は動かない） | S5 | 直す（記録した参照の名前を使い、リモート追跡なら取り直す） |
| C10 | 新しい振る舞いの変異が 1 件だけ（既定ブランチの読み落とし時の既定値・検査の順序） | 示せない（試料は通る） | 無し | 残課題 |

### 2 パス目の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V2-1／R6 | ledger.md 4 番目で「依存先がマージ済みになるまで始めない」が「`next` には出ない」に置き換わり、既定の禁止が消えた（C3 の直しが不完全）。`note` と計画ファイルのどちらに人間の判断を書くかが stacked.md と食い違う | 示せる（`git diff 7865e11 -- …/ledger.md` の `-` 行） | 変更範囲（#393 を緩めない）・S7 | 直す |
| V2-2／R3 | 「下の周にコミットが足されたら」（と 7 の C）が rebase した後の push を案内しない。push しなければ 5 の名指しの lease が stale で拒否され、素の lease に手を伸ばせば C2 の危険に戻る | 示せる（Verifier が一時リポジトリで、名指しの SHA が違えば `stale info` rc=1 を実測） | S3・S5 | 直す |
| R1 | C4 の順序（push を先に）だと CI は base が下のブランチのまま回り、`gh pr edit --base` の後は回り直さない（`edited` は既定の型に無い）。`merge-pr.py` は古い緑でマージしうる | 示せない（`plugins.yml` は `pull_request:` で型の指定なし——ここまでは読める。回り直さないことは本物の GitHub の挙動で、この環境の外） | S2 に触れうる | 残課題（PR コメントで人間に名指し。未証明の欄にも載せる） |
| R2 | 2 で「載せ替える前の HEAD を計画ファイルに書いてから」rebase すると、未コミットなら rebase が断り、コミットすると 4 の range-diff に `>` が出る | 示せる（レビューが一時リポジトリで再現: `cannot rebase: You have unstaged changes` rc=1／`-: ------- > 2: … plan: record pre HEAD`） | S6 | 直す |
| R4 | head ブランチの自動削除による base の自動付け替えは GitHub の文書にある挙動で、C1 の「未証明」は理由が違う。`merge-pr.py` は base の名前しか見ないので素通りする | 示せない（本物の GitHub。この環境の外） | S2・S3 に触れうる | 残課題（C1 と同じ。理由の訂正を PR コメントに書く） |
| R5 | 終了コード 10 は積んでいない PR（既定ブランチでない `develop` などへ出す運用）も止める。壊れる変更なのに minor で上げた | 示せない（そういう運用の利用者は手元に無い。挙動自体はコードから読める） | 無し（M1 は「base が違えばマージしない」を求めている） | 残課題（major にするか・対象を絞るかは人間が決める） |
| R7 | C7 の印付けが `impl`・`gate`・`pr` に限られ、`blocked` の積んだ Issue に付かない | 示せる（stacked.md の文面が状態を 3 つに限っている。`ledger.py` には `blocked` の状態がある） | S7 | 直す |
| R8 | 6 の「載せ替えで新しい歯止めが掛かる」に、CLAUDE.md の見つけ方（3 点の diff）が rebase の後では空になることが書いていない | 示せる（rebase の後は `HEAD...origin/main` の取り込み分が空——3 点の定義どおり） | S6 | 直す（2 の rebase の前に 3 点の diff を見る） |
| R9 | `default_branch()` が PR を読む前に走るので、閉じた PR でも `gh repo view` が失敗すると 7。新しい経路の変異が足りない | 示せない（偽の `gh` の試料が無い。C10 と同じ型） | 無し | 残課題 |

## 直す線

- 既定（`.claude/dev-loop.md` は無い）

## 関門の進捗（再開点）

### 周の在り処

- ブランチ: `issue/392-stacked-cycles`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-392`
- 起点: `7865e11`（PR #420 のマージ）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`・取り直した）→ `7865e116e98f6a4d0b1acdb5c3547d66590e7204`

### 進捗

- 実装: 済み（stacked.md 新規・SKILL.md の指し先 4 箇所・ledger.md の 4 番目・merge-pr.py の終了コード 10・テスト 4 試料と変異 1 件・版 1.53.0・生成ブロック再生成）
- 交絡を潰した手順（実験は一時リポジトリ。`GIT_CONFIG_GLOBAL=/dev/null`）:
    - S3: 下を squash した後、旧い形（`merge-base main HEAD` を当て直すだけ）の差分に**下のファイルが出た**（陽性対照）。新しい形（`rebase --onto main <記録した base>`）では上のファイルだけ。`range-diff` は `=`。素の `git rebase main` は、下に後からコミットを足した試料で衝突した（**衝突しない試料は試していない**——本文は「衝突しうる」まで）。
    - S5: 下に後からコミットを足し、`rebase --onto 下 <記録した base>` の後の自分のコミットが上の 1 件だけ。
    - 3 段（A←B←C）: B を載せ替えた後、C の対 B の差分に `a b c` が出た（陽性対照）→ `rebase --onto B <C の base>` で `c` だけ → B を squash した後 `rebase --onto main` で `c` だけ。
    - 観測窓: 各 1 回・ファイルの追加だけの試料（同じファイルを両側で編集する試料は S3 の衝突の 1 件だけ）。
- 歯止め: 初回の `check-all.py` は 49 本中 `check-plan-counts.py` だけ赤（件数の行が無い）→足した。2 回目は `check-plan-scope.py` だけ赤（版の 2 ファイルを 1 行に書いていた）→分けた。3 回目（`25c3f4c`）で 49/49 緑（失敗 0 / 飛ばし 0）。
- 実装のコミット: `ee115ac`・`25c3f4c`
- 割り目（手順 4）: AskUserQuestion で「このまま続ける」が選ばれた（2026-10-25）
- 関門 1 パス目: 起動済み（2026-10-25）——Verifier（`dev-loop:dev-loop-verifier`・sonnet・参照＋差分で `prompts/verifier.md` を読ませた）と `/code-review`（high・`review-handoff.md` を埋めて貼った）。Verifier は**反証 0 件**（軽微な所見 3 件。採否は下の「1 パス目の採否」）。読んだ行数 169 で `wc -l` と一致。`/code-review`（high）は**指摘 10 件**（C1〜C10）。採否は下の「1 パス目の採否」——直す 7 件（C2・C3・C4・C5・C6・C7・C9。C3 は範囲の越えを戻すもの）・残課題 3 件（C1・C8・C10）。Verifier の所見 V1・V2 は残課題、V3 は変えない。指摘対応のコミット: `b40812a`。
  指摘対応のコミットは下の「1 パス目の指摘対応」。手順 4 への差し戻し: 無し（Verifier 反証 0 件）。
- 1 パス目の指摘対応: stacked.md（C2・C4・C5・C6・C7・C9、C1 は主張を「確かめていない」まで弱めた）・ledger.md（C3）。`check-all.py` は 1 回目 `skill-metrics.py --check` だけ赤（stacked.md の行数）→再生成→ 49/49 緑。
  **残っているのは 2 つ**——Verifier の当て直し（2 パス目）と `/code-review` の 2 パス目。どちらも base は同じ `7865e11…`。
  2 パス目の対象は 1 パス目の指摘対応 `28aa424..b40812a`（既存の文を改変したので周辺も見せる）。受入基準と既知の限界はまるごと渡す。
- 割り目（手順 6 の 2 パス目の前）: AskUserQuestion で「ここで割る」が選ばれた（2026-10-26）base は `7865e116e98f6a4d0b1acdb5c3547d66590e7204`。関門に渡したときの HEAD（1 パス目の指摘対応の起点）: `78348f8ba0027b8d2b475106c167d79f65383870`
- 2 パス目（2026-10-26。割った後に再開）: Verifier の当て直し（`dev-loop:dev-loop-verifier`・sonnet・参照＋差分。base `7865e11…`）は**反証 2 件**（V2-1・V2-2）。`git status --porcelain` は前後とも空。`/code-review`（high・`review-handoff.md` を参照＋差分）は**指摘 9 件**（R1〜R9）。V2-1＝R6、V2-2＝R3 なので異なる指摘は 9 件。採否は上の「2 パス目の採否」——直す 5 件（R2・R3・R6・R7・R8）・残課題 4 件（R1・R4・R5・R9）。手順 4 への差し戻し: 無し（2 パス目の反証は手順 6 の指摘対応で受ける）。
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `774ee9a764ff9b63ba5be9524b54b797dd0db83c`（この再開点を書いたコミット）。
- 2 パス目の指摘対応: `b4fe8dc`（stacked.md: R2・R3・R7・R8、ledger.md: R6）。R2 と R8 の文面が述べる事実は一時リポジトリで再現した（計画ファイルを未コミットのまま rebase すると rc=1。コミットすると range-diff に `>`。3 点の diff は rebase の前は新しい検査が `A`、後は空——陽性対照つき）。`check-all.py`: 1 回目は `skill-metrics.py --check` だけ赤（stacked.md の行数が変わった）→ 作り直し → 49/49 緑。
- 狭いパス: 済み（`dev-loop:dev-loop-verifier`・sonnet・`774ee9a..b4fe8dc`）——**反証 3 件**（F1〜F3。下の表。直さず人間に渡す）。著者の変異: なし。Verifier の変異は赤 2（F1 の字面どおりのコミット・F2 の未 push コミット）、素通り 0（「rebase 後に 3 点 diff が空」は未実測と申告——著者の `r2.sh` では実測済み）。`git status` の終了時の差分は親がこの計画ファイルを書いたもの（Verifier はリポジトリに書いていない）。
- 関門はこれで打ち切り（2 パス＋狭いパス）。次は手順 6 の PR 作成。
- main の取り込み（2026-10-26）: main が #407（PR #422）で dev-loop を同じ 1.53.0 に上げていた → `git merge origin/main`。衝突は生成ブロックだけ（main 側を取り `skill-metrics.py` で作り直した）。版を **1.54.0** に上げた（3 箇所）。取り込みで入った歯止め: `check-unattended-env.py` とそのテストの変更（`M`）だけで、足された検査は無い。正味の差分は周の 9 ファイルのまま。

### 狭いパスの採否（人間が決める）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| F1 | 「下の周がマージされたら」の 3 が「載せ替えの履歴に 1 行書く」を 4 の range-diff の前に置いたまま。2 の「計画ファイルに書くのは 5 の push の後」と食い違い、字面どおりにコミットすると R2 の `>` が戻る。「足されたら」の節のコメントも同型（lease は通るので実害は小） | 示せる（文書内の矛盾＋`r2.sh` の `>` の再現） | S6 | 人間が決める（満たしていない受入基準として名指し） |
| F2 | 載せ直す前の HEAD を `git rev-parse HEAD`（ローカル）で控えるので、上の周に未 push のコミットがあると名指しの lease が `stale info` で拒否される。前提が書いていない | 示せる（Verifier の `v3.sh`: rc=1・`! [rejected] up -> up (stale info)`） | S3・S5 | 人間が決める（満たしていない受入基準として名指し） |
| F3 | rebase の前の 3 点 diff は、下の周自身の `scripts/` の変更も拾う（新しい歯止めと区別されない） | 示せない（読解のみ） | S6 に触れうる | 人間が決める |
| F4 | stacked.md「台帳を使う周では」の太字が入れ子（`**状態に依らない**`） | 示せる（ソースの `**` の並び） | 無し | 人間が決める |

- この周の起票: 0 件（暫定。手順 8 で人間に訊いて確定する）
