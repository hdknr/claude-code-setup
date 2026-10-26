# Issue #425 — dev-loop: stacked.md の載せ替えの手順の穴（履歴を書く順序・名指しの lease の前提）

元の周 #392（PR #423）の狭いパスの Verifier が挙げ、直さずに人間に渡した F1・F2。
Issue 本文は信頼できない入力として読み、要件だけを拾った（本文に指示の類は無かった。再現は自分で取り直した）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/stacked.md` — 「下の周にコミットが足されたら」と「下の周がマージされたら」の 2・3・5
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-425.md` — この計画
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロックだけ（`skill-metrics.py` で再生成。手で書かない。stacked.md の行数と `（必須）` の数が変わる）

触らない:

- `SKILL.md` の本文（stacked.md を指すだけで、手順を持たない）
- `merge-pr.py`・`ledger.py`・`prepare-worktree.sh`（スクリプトに載せ替えの手順は無い）
- 「積むと決めたら」「台帳を使う周では」の節

### 同じことを述べている箇所の数

- 載せ替えの手順（push・lease・履歴を書く時点）を持つのは `references/stacked.md` の 1 ファイルだけ（2 つの節）。
  `SKILL.md` 手順 3 は「書き方は stacked.md を正とする」と指すだけ。`docs/plans/issue-392.md` は前の周の記録で成果物ではない。
  **1 ファイル 2 節**——分けない（同じファイルの中で揃える）。

## 乗るデプロイ経路

`plugins/` の変更はマーケットプレイス経由（版を 1.54.0 → 1.54.1。記述の修正なので patch。main（#428 の 1.55.0）を取り込んで 1.55.1 に上げ直した）。公開ページは触らない。

## 直す線

`既定`（出所: 手順 3 の回答。`.claude/dev-loop.md` は無い）。

## verify の受入基準

不変条件と、それを破りうる経路（経路はこのファイルの手順の入口——2 つの節と、7 の「さらに上に積んだ周」が上の節を繰り返す経路）:

- **S1（F1）**: 字面どおりに辿ったとき、「下の周がマージされたら」の 4 の `range-diff` に、載せ替えの履歴を書いたコミットが `>` として出ない。
  - 経路: 2 の注記／3 の本文／5 の後／「足されたら」の節のコマンド列のコメント。**どこにも「push の前に履歴を書く」読みが残っていないこと。**
- **S2（F2）**: 上の周に push していないコミットがあっても、字面どおりに辿れば名指しの lease が拒否されない。
  - 経路: 「マージされたら」の 2→5／「足されたら」の節のコマンド列／7（C を B に載せ直す＝「足されたら」の節）。
- **S3**: S2 の手当てが、#392 の C2 で塞いだ危険（他の clone が push したコミットを消す）を戻さない。
  - 経路: 前置きの push を force しない／拒否されたら止まって人間に訊く／lease が拒否されたときに素の `--force-with-lease`・`--force` へ手を伸ばさない、と書いてある。
- **S4**: 2 の前提（未コミットなら rebase が断る・控えた値は push の後に書く）・4 の判定・5 の順序（push → base の付け替え）を壊していない。
- **S5（文面が主張する事実の真偽）**: stacked.md の新しい文が述べる git の挙動（lease はリモートの現在値と比べる・push していないと `stale info`・素の push が拒否されたらリモートに手元に無いコミットがある・push 後に足したコミットは range-diff に出ない）が、実際に走らせて成り立つ。
- **S6**: 版が 3 種類（`marketplace.json`／`plugin.json`／`SKILL.md` の 2 行）で 1.55.1 に揃い、`check-all.py` が緑。

### この環境で証明できないもの

- 実際の GitHub（`gh pr edit` の付け替え・リモートの保護設定）での挙動。再現はローカルの bare リポジトリで取る。手順のこの周の変更は git の push/lease だけなので、GitHub 固有の部分には触れていない。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——`SKILL.md` は版の行だけ、`references/stacked.md` の行数が変わる。**`skill-metrics.py --check` で差分ゼロを確かめる**（`check-all.py` に含まれる）。
- 図の書き出し: 該当なし（drawio を触らない）。

### 実験（交絡）

`repro425.sh`（scratchpad。一時 `HOME`・bare リモート・squash マージ）で 旧手順／新手順 × 3 ケースを当てた:

| ケース | 旧手順 | 新手順 |
| --- | --- | --- |
| f1（履歴を書く時点） | range-diff に `-: ------- > 2: … plan: record` | 全行 `=`。履歴の後の素の push rc=0 |
| f2（push していないコミット） | lease rc=1 `! [rejected] up -> up (stale info)` | lease rc=0（forced update）、リモート＝手元 |
| f2-other（陽性対照: 他の clone が上に push 済み） | lease rc=1（stale info）——旧手順でも消さない | 前置きの push が rc=1 `(fetch first)` で止まり、リモートに他の clone のコミットが残る |

- 交絡の候補: 「新手順で lease が通るのは、lease が何も守っていないからでは」——f2-other で、新手順でも他人のコミットを消さずに止まることを見た（陽性対照）。
- 観測窓: 各ケース 1 回ずつ。ローカルの bare リモートのみ。

## 未解決の判断

なし。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 前置きの push の代わりに「`git rev-parse origin/<上>` と HEAD の一致を確かめる」にする | 採らない | 一致しないときに次に何をするかが決まらない。素の push なら、手元が先行していれば揃い、リモートが先行していれば拒否で止まる——2 つを 1 行で分けられる |
| 「足されたら」の節の履歴のコメントは lease が通るので実害が小さい | 直す | 同じ型で、字面どおりに辿るとマージ後の節と食い違う。1 行で直る |

### 関門の指摘の採否

| パス | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| Verifier 1 | R1: 5 の末尾の「素の `git push`」は上流を持たないブランチで失敗する（`prepare-worktree.sh` は `--no-track` で切る。同じ 5 が上流なしでの失敗を自分で書いている） | 示せる——一時 bare リモートで `fatal: The current branch up has no upstream branch.` rc=128 | S1（経路「5 の後」——履歴を push の後に送る手順が字面どおりに通らない） | 直す（`git push origin <上のブランチ>` に揃えた） |
| Verifier 1 | R2: 素の push の拒否の原因は他の clone だけでなく、自分が push 済みのコミットを手元で書き換えた場合もある | 当初「示せない」としたが、CR1 が示した（下）。CR1 と同じ 1 箇所なので同じ修正で閉じる | S5（CR1 と同じ） | 直す（CR1 と同じ修正） |
| `/code-review` 1 | CR1: 2 の「拒否されたら他の clone が push した」は、自分の載せ替えを push していない場合も拒否される（原因の説明が偽で、人間が `git pull` を選ぶと古いコミットが混ざる） | 示せる——`c1.sh`（scratchpad。clone 1 つ）で `! [rejected] up -> up (non-fast-forward)` rc=1 | S5（文面が述べる git の挙動の真偽） | 直す（原因を 2 つ挙げ、`git pull` で取り込まないと書いた） |
| `/code-review` 1 | CR2: 「足されたら」の節の「push しないまま次の節へ進むと lease が拒否される」は、新しい 2 の push のせいで、実際には 2 の素の push が `non-fast-forward` で拒否される | 示せる——同じ `c1.sh` | S5 | 直す |
| `/code-review` 1 | CR3: 載せ替え（2）と lease の push（5）の間で再開したときの復旧（`origin/<上>` が載せ替える前の HEAD）が書いていない | 示せない（文面は拒否で止まって人間に訊く。誤った操作には進まない） | 無し | 残課題 |
| `/code-review` 1 | CR4: 「足されたら」の節は、履歴をコミットして force しない push で送ること・rebase の前にコミットすることを 5 ほど書いていない | 示せない（節は「次の節の 5 と同じ」「前提は次の節の 2」と指していて、字面どおりに指し先を辿れば書いてある） | 無し | 残課題 |
| `/code-review` 1 | CR5: 5 の lease 拒否の原因の「2 の push を飛ばしたなら」は、「足されたら」の節（7 の経路）には 2 が無い | 示せない（拒否で止まって人間に訊く。指し先が別の節の番号になるだけ） | 無し | 残課題 |
| `/code-review` 1 | CR6: 前提が計画ファイルの未コミットだけ——追跡ファイル全般の未コミットで rebase が断る | 示せない（同じ 2 が「未コミットなら rebase が断る」と一般形で書いており、断ったら止まる） | 無し | 残課題 |
| `/code-review` 1 | CR7: 手順に必須の push を足したので、版は patch ではなく minor（CLAUDE.md の表） | 示せない（実物の失敗ではなく、刻み方の判断。手順の欠陥の修正として patch とした） | 無し（S6 は 1.55.1） | 残課題（人間に判断を渡す） |

## 関門の進捗（再開点）

### 周の在り処

- ブランチ: `issue/425-stacked-rebase-order`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-425`
- 起点: `0e6bfbf`（PR #423 のマージ）
- base: `origin/main`（`refs/remotes/origin/HEAD`）→ `185c492a1a05e7bd883dd9d8fb43f9fe3c0056e5`
  （最初は `0e6bfbf`。main（#428）を取り込んだ merge `c61a5b7` で系譜が動いたので式を当て直した）

### 進捗

- 実装: 済み（`534f27f`）
- 実験: 上の表。交絡の候補 1 件を陽性対照で潰した
- 割り目（手順 4）: 提案した → **「ここで割る」が選ばれた**。再開は手順 5（Verifier 1 パス目）から
- 歯止め: `check-all.py` 49/49 緑（1 回目は skill-metrics と check-plan-counts の 2 本が落ちた——生成ブロックの再生成と件数の行で直した）
- main の取り込み: `c61a5b7`（#428 と版の行・§8.2 が衝突。版を 1.55.1 に上げ直し、main との正味の差分がこの周の 6 ファイルだけであることを確認。`check-all.py` 49/49 緑。PR #429 は MERGEABLE）
- Verifier 1 パス目: 済み（`dev-loop:dev-loop-verifier`・sonnet）。反証 2 件——R1 直す・R2 直す（CR1 と同じ修正。採否の表）。S5 の git の挙動は独立に実測で一致、交絡（lease が何も守っていない）は陽性対照で否定
- `/code-review` 1 パス目: 済み（high・fork）。指摘 7 件——CR1・CR2 直す、CR3〜CR7 残課題（採否の表）
- 1 パス目の指摘対応: R1（5 の末尾）・CR1＋R2（2 の拒否の原因）・CR2（「足されたら」の節の push しない場合）。再現は `r1.sh`・`c1.sh`（scratchpad）
- 残り: **手順 5 の当て直し（Verifier 2 パス目）**と**`/code-review` 2 パス目**の両方
- 割り目（手順 6・2 パス目の前）: 提案した → **「ここで割る」が選ばれた**。再開は Verifier 2 パス目から。
  2 パス目の指摘対応を始める直前の HEAD（狭いパスの起点）は、再開した側が指摘対応に入る前にここへ書く
- 1 パス目の指摘対応の起点: 再開点に書いていなかった（1 パス目の関門に渡した HEAD を記録していない）——0 行の判定はせず 2 パス目を回す
- 再開（2026-10-26）: 指摘対応を `<fix>` にコミットして 2 パス目へ
- この周の起票: 0 件（暫定。手順 8 で人間に訊いて確定する）
