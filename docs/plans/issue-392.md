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
- `plugins/dev-loop/.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` — 版
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

- **本物の GitHub の挙動**: 下のブランチを base にした PR に対する `closingIssuesReferences` の中身、`gh pr edit --base` の後の CI の再実行。偽の `gh` と一時リポジトリでは当たらない。
  ここに寄りかかる主張は書かない（S2 の守り方は `baseRefName` と既定ブランチの比較だけに依る）。人間のレビューに回す。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`。references の一覧と行数が載る）——再生成して `--check` が緑。
- 図の書き出し: 該当なし（drawio を触らない）。

## 未解決の判断

- 無し

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
- 歯止め: 初回の `check-all.py` は 49 本中 `check-plan-counts.py` だけ赤（件数の行が無い）。

- この周の起票: 0 件（暫定。手順 8 で人間に訊いて確定する）
