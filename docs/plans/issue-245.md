# Issue #245 — 「porcelain が空でなければ HEAD の証拠にしない」が通常の関門まで格下げする

元の周: #233（PR #244）の 2 パス目の `/code-review` の指摘 D1／D6（と D2）。

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 5「原本を変えさせない」の porcelain の項（原本）＋版のバナー
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「実環境を壊さないこと」の `git status` の 2 行を 1 つに畳む
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 同上
- `plugins/dev-loop/agents/dev-loop-verifier.md` — 「追跡対象ファイルを変更しない」の `git status` の行と porcelain の項を 1 つに畳む
- `plugins/dev-loop/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — version
- `docs/plans/issue-245.md` — この計画ファイル
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手では触らない）

触らない:

- #233 の (a)(b)（拒否・失敗のハザードと止まる条件）——この周は (c) だけを直す
- `docs/plans/issue-233.md`——前の周の記録。I1(c) はこの周で置き換わるが、記録は書き換えない
- 「関門の起動中に著者が作業ツリーを触らない」という著者側の規定（#233 の D3 系）——別の論点
- porcelain に見えない変更（コミット・ブランチ移動・stash。#233 の C4）
- `CLAUDE.md`

**複製の数**: 同じ規範を述べる箇所が 4（SKILL.md 原本・prompts 2 本・agent 定義）＋版 3 箇所。
分けない理由: 委譲文は原本の実装で、片方だけ直すと食い違う（#233 と同じ）。同じコミットで揃える。
**増やす変更と減らす変更**: 1 ファイルの中の 2 行を 1 つに畳む（減）と、開始時の取得を足す（増）が同じ周に入る。
効果は測らない（文面の周）ので打ち消し合いの問題は生じないが、増減は別々に数えて報告する。

## 2. デプロイ経路

プラグインの配布（main へのマージでカタログに載る）。`docs/plans/` は公開サイトのビルド対象だが記録のみ。

## 3. 受入基準

**J1. 4 箇所すべてが、次の 4 つを述べている。**
  - (a) リポジトリの `git status --porcelain` を**始める前と終わったあとの 2 回**取り、**両方を報告に書く**（D2）
  - (b) **始める前から空でないこと自体では格下げしない**（未コミットの実装を見る関門ではふつうの状態。D1）
  - (c) **2 回の結果が違う、または自分が変更したファイルを含む**ときだけ、その旨（違う行）を書き、その状態で取った結果を証拠として報告しない
  - (d) 既存の「終わったときに `git status` が開始時と同じであること」と**1 つに畳まれている**——同じファイルの中に、条件の違う 2 つの規定が並んでいない（D6）

| 経路（委譲先が文面を受け取る入口） | 守り方 |
| --- | --- |
| P1 手順 5 で `prompts/verifier.md` を埋めて `dev-loop:dev-loop-verifier` に渡す | prompts/verifier.md |
| P2 手順 6 で `prompts/review-handoff.md` を `/code-review` に渡す | prompts/review-handoff.md |
| P3 狭いパス（prompts/verifier.md の差し込み） | P1 と同じファイル |
| P4 委譲文なしで `dev-loop-verifier` が起動される | agent 定義 |
| P5 著者が SKILL.md を読んで委譲文を手で書く／テンプレを足す | SKILL.md 原本 |

**J1 を判別する場面**（文面がこの 4 つを正しく振り分けるか）:

| 開始時 | 終了時 | 自分が触った | 期待 |
| --- | --- | --- | --- |
| 空 | 空 | なし | 証拠にしてよい |
| ` M x`（著者の未コミット実装） | ` M x` | なし | **証拠にしてよい**（D1 の本体。旧文言は格下げしていた） |
| 空 | ` M y` | y | 格下げ（#233 の「変異が入ったままの緑」） |
| ` M x` | ` M x` | x を変更して戻さず | 格下げ（porcelain は同じでも中身が違う。「自分が触った」で捕まえる） |
| ` M x` | ` M x`・` M z` | なし（著者が途中で z を編集） | 格下げ（保守側。違う行を書くので親が判断できる） |

**J2. 4 箇所の間で言い分が食い違わず、旧文言（「空でなければ」）が dev-loop の配下に*規則として*残っていない**（SKILL.md 原本の「条件にしない」という否定の言及は除く）。
**J3. #233 の I1(a)(b)（ハザードの名指し・止まる条件）を消していない。**
**J4. 版が 3 箇所で一致し、`check-all.py` が緑。**

### 証明の手段

- J1・J2・J3: 文面の読解と `grep`（関門に独立に当てさせる）。
- J4: `python3 scripts/check-all.py`。
- **未証明: 文面を変えたことで関門が実際に振り分けを変えるか。** 効果は主張しない（#233 と同じ扱い）。PR コメントで申告する。

### 生成物

`SKILL.md` を触るので **`skill-metrics.py --check`**（設計 §8.2 の生成ブロック）が該当。再生成して `--check` が緑であること。drawio は該当なし。

## 4. 未解決

なし。

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/245-porcelain-start-end`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-245`・起点 `2a8e87b`・base `origin/main` = `2a8e87bd90b89a70a17da4e317e9f736649774a0`
- 実装: `4da0b24`（`check-all.py` 33/33 緑・`skill-metrics.py` 再生成済み）。増減: 4 箇所とも 2 行を 1 つの規定に畳み（減）、開始時の取得を足した（増）
- 関門: 未着手（次は手順 5 の 1 パス目）
- 割り目（手順 4）: 提案した → **「ここで割る」が選ばれた**。再開は手順 5 の 1 パス目から（Verifier と /code-review の両方、base `2a8e87bd90b89a70a17da4e317e9f736649774a0`）
- 反証・差し戻し: なし
- 交絡: 実験なし

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 著者が関門の起動中に作業ツリーを触ると格下げされる | 採らない（保守側に倒したまま） | 違いは報告に行として出るので親が判断できる。著者側の規定は別の論点 |
| porcelain に見えない変更（コミット・stash 等。#233 C4） | 採らない | この周は (c) の条件だけを直す |
| 「HEAD の証拠」という語 | 「検証対象の証拠」に改める | 2 点 diff の関門は未コミットの実装も見るので、HEAD だけが対象ではない |
