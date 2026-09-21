# Issue #148 — 周の base をどこから取るかを 1 つに決める

> 周の base が**切る側・関門に渡す側・子への指示**の 3 つでばらばらに決まっていて、
> どれも閉じていない。[#145](https://github.com/hdknr/claude-code-setup/issues/145) の周で
> **2 度規定し、2 度とも関門に「その手順では塞がらない」と反証された**ので、人間の判断で分割した。

## 0. 周の在り処

- ブランチ: `issue/148-base-selection`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-148`
- **起点コミット: `fdca142`**（`issue/145-gate-claims` の当時の先端）
- **base（関門に渡す SHA）: `fdca142f43d0ab747ab1b99dc0a61477654e7b55`**
  ——`git merge-base issue/145-gate-claims HEAD` で再解決できる。

### この周は `main` ではなく #145 のブランチに積んでいる（stacked）

**人間の判断**（`AskUserQuestion` で 3 択を出し、「#145 のブランチから積む」が選ばれた）。
理由: **#145 が未マージのまま、この周が埋めるべき空欄をブランチ側に持っている**
——`SKILL.md:734` / `:1041` の「**この周では規定しない**（#148）」と、
委譲文 2 本の `{{その周の取り方を、base まで含めて書く}}` スロット。
`main` から切ると、その空欄もスロットも存在しない。

- **PR の base は `issue/145-gate-claims`。** #145 が先にマージされたら `main` に付け替える。
- **#145 は現在も動いている**——この周の着手中に `a8ab67c` → `fdca142` へ進んだ。
  **base は動く**ので、**関門に渡すのは再解決した SHA**（この周が決める規定そのもの）。

### `prepare-worktree.sh` を使ったが、起点は手で直した（申告）

**`SKILL.md` 手順 4 の「新規の周は、スクリプトで作る `（必須）`」は満たした**が、
**スクリプトは start-point を取れない**——**それがこの Issue が直す欠陥そのもの**なので、
**この周だけは切ったあとに `git reset --hard issue/145-gate-claims` で起点を乗せ替えた。**
スクリプトが与える守り（置き場所・命名規約・先に見る・肯定的な確認）はすべて通っている。
**黙って落としていない**（原則「必須手順を落とすときは、黙って落とさない」）。

**実際に、スクリプトは `main` の HEAD（`1983049`）の上に切った**——
**この Issue の失敗 1 が、この周の 1 手目で再現した。**

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 4 に規定の原本、手順 5・6 は指し先に置き換え
- `plugins/dev-loop/skills/dev-loop/scripts/prepare-worktree.sh` — start-point の解決と受け渡し
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — スロットを具体の形にする
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 同上（2 本を同じ形に）
- `plugins/dev-loop/agents/dev-loop-verifier.md` — 衝突が残っていないかの点検（**変更しない可能性が高い**）
- `scripts/test-worktree-scripts.py` — 観測と変異を 1 対 1 で足す
- `plugins/dev-loop/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — version
- `docs/plugins/dev-loop-design.md` — `skill-metrics.py` の生成ブロック（手で書かない）
- `docs/plans/issue-148.md` — この計画ファイル
- `CLAUDE.md` — `test-worktree-scripts.py` の**変異の件数が実際と食い違っている**
  （**2 箇所とも「8 件」だが実際は 12 件**。この周で件数が動くので併せて直す）

触らない:

- `diagrams/` 一切（drawio を編集しないので書き出しの鮮度は動かない）
- `docs/` の `plans/` `plugins/dev-loop-design.md` 以外
- `plugins/dev-loop/skills/dev-loop/references/` — base の規定を**ここに置かない**
  （**条件つきの節ではない**。毎周かかるので起点に載せる）
- 他のプラグイン（`cmux` / `workspace-setup`）

## 2. 乗るデプロイ経路

- **`docs/` を触るので、`main` への push が GitHub Pages のデプロイになる**
  （`CLAUDE.md`「デプロイ」／`.github/workflows/docs.yml`）。**「ドキュメントだから経路が無い」ではない。**
- プラグインの配布は `.claude-plugin/marketplace.json` 経由。**version を 3 箇所で揃える。**
- **ただし PR の base が `issue/145-gate-claims` なので、この PR のマージだけでは本番に出ない**
  ——**#145 がマージされて初めて `main` に乗る。**

## 3. verify の受入基準

### 決めた形（これが規定の本体。1 箇所に書く）

> **周の base は `git merge-base <既定ブランチのリモート追跡参照> HEAD` が返す SHA である。**
> **親が解決し、SHA のまま関門に渡す。関門は `git diff <SHA>`（2 点）で取る。**
> **未追跡ファイルは `git status --porcelain` で併せて見る。**
> **切る側（`prepare-worktree.sh`）は、同じ参照を start-point にする。**

**なぜこの形か——Issue が挙げた 4 つの失敗を、1 つずつ潰している:**

| 選択 | 潰れる失敗 |
| --- | --- |
| 名前ではなく **SHA** | 子の手元が古くても動かない。**取り直しが 1 回も要らない**ので、委譲文の「副作用のあるコマンドを使うな」と**衝突しない** |
| 先端ではなく **merge-base** | 他人のマージ済みの作業が、**追加としても削除としても**差分に入らない |
| 3 点ではなく **2 点** | **未コミットの実装が見える**（3 点は作業ツリーを含まない） |
| `git status --porcelain` を併せる | **`git diff` は未追跡を出さない**——2 点にしただけでは新規ファイルが見えない |
| start-point を渡す | **`git worktree add -b` は省略時に HEAD に落ちる**ので、古いローカル既定ブランチの上に切らない |

**SHA が子の手元に必ず在る理由（取り直しが要らない根拠）:**
**merge-base は定義上 HEAD の祖先**なので、**HEAD を持つ作業ツリーには必ず在る**。
これが「子への指示」の衝突（Issue の 3 番目）を**規定を足すのではなく、要らなくすることで**閉じる。

### 不変条件と、それを破りうる経路

**経路は差分ではなく「base が決まる／渡される入口」の一覧から数えた。**

不変条件:

- **A**: base は周を切った分岐点を指す（他人のマージ済みの作業が、**どちらの向きにも**差分に入らない）
- **B**: 関門が見る差分に、**未コミット・未追跡の実装が含まれる**
- **C**: base の**決め方**の原本は 1 箇所しかない（指し先は列挙を持たない）
- **D**: 委譲文の指示が、同梱 agent 定義の禁止（副作用のあるコマンドを使うな）と衝突しない
- **E**: 子の手元の状態（古いリモート追跡参照・fetch の有無）に結果が依存しない
- **F**: 切る側が、古いローカル既定ブランチの上に切らない

**base が「決まる」入口:**

| # | 入口 | 守る不変条件 | どう守るか |
| --- | --- | --- | --- |
| 1 | `prepare-worktree.sh` | F | start-point を解決して `git worktree add -b … <start-point>` に渡す。**解決結果を出力する** |
| 2 | `EnterWorktree` の `name` 経路（道具が切る） | F | **道具の `worktree.baseRef` 既定が `fresh` = `origin/<既定>`** なので既に満たす。**規定は当てられない**（道具の設定）——**満たしていることを書くに留める** |
| 3 | 手で `git worktree add`（復旧の道。`references/resume.md`） | F | 手順 4 の規定が start-point を要求する |
| 4 | 再開した周 | A | **計画ファイルの「周の在り処」に記録した base** を使う（作り直さない） |

**base が「渡される」入口:**

| # | 入口 | 守る不変条件 | どう守るか |
| --- | --- | --- | --- |
| 5 | `prompts/verifier.md` | A B E | 親が解決した SHA をスロットに入れる。取り方は `git diff <SHA>` ＋ `git status --porcelain` |
| 6 | `prompts/review-handoff.md` | A B E | **5 と同じ形**（#59 の「片側だけ直す」型を作らない） |
| 7 | 手順 5 の多レンズ化（各レンズ） | A B E | 委譲文 2 本を使うので自動的に掛かる |
| 8 | 手順 6 のレビュー fan-out（各体） | A B E | 同上 |
| 9 | `Workflow` のノード | A B E | 同上 |
| 10 | 同梱 agent 定義 `dev-loop-verifier.md` | D | **何も書かない。** 規定を足さないことが守り方である |
| 11 | `check-plan-scope.py <base-ref>`（CI と手元） | A | **この周では `origin/main` ではなく base SHA を渡す**——stacked なので `origin/main` だと #145 の差分が全部この周のものに見える |
| 12 | `check-version-bump.py` / `check-description-sync.py` | A | 同上（同じ base SHA を渡す） |

**11・12 は差分を読んでいたら出てこない経路である。** リポジトリ自身の歯止めが base を引数に取る。

### 証明できるもの（この環境で verify する）

| # | 受入基準 | 証明手段 |
| --- | --- | --- |
| V1 | **origin が周を切った時点より進んでいても、他人の作業が差分に混ざらない**（A） | 合成リポジトリで、切った後に既定ブランチを進めてから `git diff <merge-base>` を取り、**他人のコミットのファイルが出ないこと**を見る。**先端の SHA を使った場合は「削除」として出ること**（陽性対照）も併せて見る |
| V2 | **未コミットの実装が関門に見える**（B） | 同じ合成リポジトリで、コミットせずに編集して `git diff <SHA>` に出ること。**3 点では出ないこと**（陽性対照）も見る |
| V3 | **未追跡の新規ファイルが見える**（B の穴） | `git status --porcelain` に `??` で出ること。**`git diff <SHA>` には出ないこと**も見る |
| V4 | **`prepare-worktree.sh` が start-point の上に切る**（F） | `test-worktree-scripts.py` に観測と変異を足す。**古い既定ブランチを作った合成リポジトリで、新しい側の上に切ること** |
| V5 | **`origin` が無いリポジトリでも作れて、そのことを黙らない**（F の限界） | 合成リポジトリ（`make_repo` は `origin` を持たない）で rc=0 かつ**出力に「HEAD から切った」と出る**こと |
| V6 | **base の決め方の原本が 1 箇所**（C） | `SKILL.md` を横断して `merge-base` の**規定**が 1 箇所か数える。手順 5・6 は**指し先だけ**で列挙を持たないこと |
| V7 | **取り直しを求める文がどこにも無い**（D） | `SKILL.md` ／ 委譲文 2 本 ／ agent 定義を横断して `fetch` ／「取り直」を grep し、**関門に向けた要求が 0 件**であること |
| V8 | **委譲文 2 本が同じ形**（D の鏡像） | 2 本の該当行を並べて突き合わせる |
| V9 | **既存の 12 変異が全部生きている** | `python3 scripts/test-worktree-scripts.py` |
| V10 | **歯止めが全部緑** | `python3 scripts/check-all.py`（**1 本ずつ選ばない**） |
| V11 | **version が 3 箇所で揃っている** | `check-plugin-versions.py` |
| V12 | **`skill-metrics.py` の生成ブロックが現在** | `python3 scripts/skill-metrics.py --check` |

### この環境では証明できないもの（未証明。人間レビューに回す）

| # | 未証明の項目 | なぜ原理的に証明できないか |
| --- | --- | --- |
| U1 | **`EnterWorktree` の `worktree.baseRef` 既定が本当に `origin/<既定>` か** | **道具の説明文が出所**で、**動かして確かめていない**。**この周では測らない**——測るには実際に `name` で worktree を作る必要があり、**この周は既に worktree セッションの中にいるので新規作成が拒否される**（手順 4）。**「道具の説明文にそう書いてある」までしか言わない** |
| U2 | **実際に他人の PR が並行してマージされた状況での挙動** | 合成リポジトリは**他人のマージを模したもの**であって、実際の GitHub の並行マージではない。**模せる範囲は「分岐して先に進む」まで** |
| U3 | **この規定が次の周で実際に守られるか** | **規範が著者に届くかは、この周では測れない**（`norms-dont-reach-their-author`）。**#145 は 3 度書き直して 4 度反証された**ので、**「今度は閉じた」は主張しない** |

### 生成物の鮮度（該当判定）

**該当あり。** 数え上げた先: `CLAUDE.md` の生成手順・`scripts/` の生成タスク・CI の鮮度チェック。

| 生成物 | 該当 | 対応 |
| --- | --- | --- |
| `skill-metrics.py` → 設計 §8.2 の生成ブロック | **該当する**（`SKILL.md` を編集する） | `python3 scripts/skill-metrics.py` で再生成し、`--check` で差分ゼロを確認。**手で書かない** |
| `export-diagrams.py` → `docs/images/` | **該当しない**（drawio を触らない） | `check-diagram-freshness.py` が緑であることだけ見る |
| version（3 箇所） | **該当する** | `check-plugin-versions.py` |

## 4. 未解決の判断・確認待ち

- **PR の base を `issue/145-gate-claims` にする**。#145 が先にマージされたら `main` へ付け替える。
  **#145 が動き続けているので、着地の直前に base を再解決する。**
- **決着: `prepare-worktree.sh` は `fetch` を打つ**（最善努力）。
  **オフラインでも止めない**が、**取り直せなかったことは出力する。**
  `GIT_TERMINAL_PROMPT=0` を付けて、認証を訊かれて固まるのを防いでいる。
  **「fetch すべきでない」という判断もありうるので、関門に問う。**
- **決着: 既定ブランチの解決順序**は
  `DEV_LOOP_BASE_REF` → `refs/remotes/origin/HEAD` → `origin/main` → `origin/master` → **HEAD**。
  **推測したことも、HEAD に落ちたことも出力する。**
- **決着: 実証の置き場所は `test-worktree-scripts.py` の中**（別ファイルにしない）。
  **別ファイルにすると `check-all.py` と CI の yaml に二重登録が要り、
  このリポジトリが 2 度踏んだ「登録し忘れ」の型**（`test_ci_runs_every_registered_script`
  の docstring）**に当たる。**
- **残った問い: `check-all.py` が 120 秒を超えるようになった。**
  **`observe()` が 17 回走り、そのたびに 2 つのクローンを作る**ため。
  **この周では分けない**——**測ってから決める**（手順 3 の「閾値は決めない」と同じ扱い）。

## 5. 関門の進捗（再開点）

**ここに書くのは、この周で実際に起きたことだけである**（規定の引用ではない）。

- 周の在り処: 上記「0. 周の在り処」
- **実装: 完了**（`82bf3a2`）。**歯止めは 26/26 緑**
  （`python3 scripts/check-all.py --base $(git merge-base issue/145-gate-claims HEAD)`)。
  **`origin/main` を base にしてはならない**——stacked なので #145 の 610 行が全部この周のものに見える。
- **交絡を潰した手順: 実測した。**
  1. **陽性対照を 2 つ取った**（`demonstrate_base_rule`）——
     **先端の SHA では他人の作業が削除として出る**／**3 点では未コミットの実装が出ない**。
     **「混ざらない」「見える」だけでは、もともと出ない値と区別がつかない**ため。
     **`assert mb != tip`** をテストに入れて、**#145 の周で区別できなかった配置
     （tip == merge-base）に落ちていないこと**を毎回確かめている。
  2. **2 つの変異が見分けられることを、実際に測った。**
     「start-point を渡さない」と「取り直さない」は、
     **未取得の場面だけを見るとどちらも `A（古い）`** で**区別できない**。
     **取得済みの場面を足すと `A` / `B` に分かれる**。
     食い違う観測キーは**取得済みの場面の 2 つだけ**だった——
     **つまりこの場面が、2 変異を分けている唯一の観測である。**
  3. **観測窓**: `prepare-worktree.sh` の 1 回の実行と、その worktree の HEAD。
     **ネットワーク越しの `origin` は測っていない**（合成リポジトリの `origin` は
     ローカルの bare リポジトリである）。
- Verifier 1 パス目: **未着手**
- `/code-review` 1 パス目: **未着手**
- 指摘対応: **未着手**
- 手順 5 の当て直し: **未着手**
- `/code-review` 2 パス目: **未着手**

## 6. 既知の限界・決着済みの論点（両方の関門に毎パス渡す）

- **U1・U2・U3 は未証明**（上の表）。**再指摘は決着済みとして扱う。**
- **`EnterWorktree` / `ExitWorktree` の意味論には規定を当てない**——**スクリプトから呼べない**
  ので、**この周が変えられるのは素の git で済む部分だけ**（`SKILL.md` 手順 4 の既定）。
- **#145 の周で採らなかった 4 形は、再提案しない**——
  **(a) 委譲文に「取り直してから」／(b) 名前（`origin/<既定>`）で渡す／(c) 先端の SHA で渡す／
  (d) 3 点 `<base>...HEAD`**。**4 形とも関門に反証済み**で、理由は上の「なぜこの形か」の表にある。
- **この周は stacked である。** `origin/main` との差分には **#145 の 610 行が含まれる**——
  **それはこの周の成果物ではない。** **base は `fdca142`。**
