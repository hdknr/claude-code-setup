# #188 — 2 パス目の修正は、その差分だけに Verifier を 1 回当てる

## 周の在り処

- ブランチ: `issue/188-narrow-verifier-after-pass2`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-188`
  （`prepare-worktree.sh` で作り、`EnterWorktree` に `path` で入った）
- 起点: `820f1af`（Merge pull request #192）
- base: 参照 `origin/main` → `820f1aff5b33339e2a980e4ea330ae2e13445093`
- 読み込まれた dev-loop は **1.36.1**（リポジトリも 1.36.1）

## 0. 人間の判断（2026-10-07、`AskUserQuestion`）

Issue の「決めること」への回答。調査結果と併せて Issue にコメントした
（<https://github.com/hdknr/claude-code-setup/issues/188#issuecomment-6028506879>）。

1. (b) の判定は「受入基準の番号で指せる」を選んだ。**ところが手順 6 は、周の中で直すのを
   「示せる」かつ「破る受入基準がある」行だけに限っているので、2 パス目で直した行は定義上
   全部が番号を持つ**——(a)/(b) は何も絞らない。これを示して訊き直し、
   **「条件を外す: 2 パス目で 1 件でも直したら、その差分だけに当てる」**が選ばれた。
2. **直した行があれば必須**。割り目の `AskUserQuestion` には含めない。直した行が 0 件なら
   「該当なし」と明記する。
3. 狭いパスの指摘は**直さない・当て直さない**（Issue のとおり）。`/code-review` は当てない。

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 6 の原本、手順 6 の当て直しの項の指し先、手順 3 の再開点の列挙、frontmatter、版のバナー、手順 4 の base の項（狭いパスの起点）
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 狭いパス用の差し込み
- `plugins/dev-loop/skills/dev-loop/references/resume.md` — 関門の並び（「もう 1 周する」は #178 以後すでに古い）
- `plugins/dev-loop/.claude-plugin/plugin.json` — description・版（1.36.1 → 1.37.0）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — 「2 パスで打ち切る」を述べる 2 箇所
- `docs/plans/issue-188.md` — この計画

触らない: `agents/dev-loop-verifier.md`（変異の設計は既に持つ観点。狭いパスの指定は委譲文で渡す）、
`prompts/review-handoff.md`（`/code-review` は当てない）、`README.md`（手順 6 を指しているだけ）、
evals（振る舞いの Eval はこの周の受入基準に入れない）

**同じことを述べている箇所の数**: 「2 パス目の修正は当て直さない」系が **10 箇所**
（SKILL.md 手順 6 原本・同 当て直しの項・同 手順 3 の再開点・frontmatter・plugin.json・
marketplace.json・設計 2 箇所・resume.md・verifier.md）。**分けない理由**: 1 つの規定の
言い換えで、片方だけ直すと「当て直さない」と「1 回当てる」が併存して食い違う。
原本以外は**指し先か 1 句の要約**に留め、条件を複製しない。

種別: **増やす変更のみ**（関門を 1 つ足す）。

## 2. デプロイ経路

プラグインの版を上げる → main にマージ → 利用者は `plugin update`。
`docs/plugins/dev-loop-design.md` は公開サイト（main への push で GitHub Pages）。

## 3. verify の受入基準

### 不変条件

| # | 不変条件 |
| --- | --- |
| A | **2 パス目で 1 件以上直した周では、その修正の差分だけに別ティアの Verifier を 1 回当てることが必須**として `SKILL.md` に書かれ、**0 件なら「該当なし」と明記する**ことも書かれている |
| B | **無限後退が止まっている**: 狭いパスの指摘は**直さない・当て直さない**、`/code-review` は当てない。「3 パス目は無い」「2 パス目の修正を当て直さない」と**文として食い違わない** |
| C | **狭いパスの差分の起点**が定まっており（記録する・祖先を確かめる）、手順 4 の「周の base は 1 つ」と食い違わない |
| D | 狭いパスにも**受入基準まるごと・既知の限界・信頼できない入力の扱い**が渡る（差分だけを絞る。基準は絞らない）。**変異は Verifier に設計させ、素通りした変異を報告させる** |
| E | 狭いパスの指摘は**採否の表に載り、PR コメントで人間に渡る**。示せて受入基準を破るものは「満たしていない受入基準」として名指しされる |
| F | **複製（§1 の 10 箇所）に、例外なしの「当て直さない」が残っていない**。frontmatter / plugin.json / marketplace.json の description が共変している |
| G | 再開できる: 計画ファイルの再開点と resume.md の関門の並びに狭いパスが入っている |
| H | 版が 3 箇所で 1.37.0、`skill-metrics.py` の生成ブロックが新しい、`check-all.py` が緑 |

### これを破りうる経路（規定が読まれる入口）

| 入口 | 関わる不変条件 |
| --- | --- |
| `SKILL.md` 手順 6 を上から読む著者 | A・B・D・E |
| 手順 6「1 パス目の指摘を直したら…」の括弧書きだけを読む著者 | B・F |
| 手順 4 の base の項から差分を取る著者・関門 | C |
| `prompts/verifier.md` の `{{ }}` を埋める著者 | C・D |
| frontmatter（常時ロード）・カタログの description だけを読む者 | F |
| 割り目から再開した側（計画ファイルの再開点・resume.md） | G |
| 公開ページ（設計ドキュメント）の読者 | F |
| CI の歯止め | H |

### この環境では証明できないもの（未証明）

- **狭いパスが実際の周で発火し、Issue の実例のような穴を見つけるか**——振る舞いであり、
  文面の検査では判別できない。Eval は 1 回約 $1 で、worktree セッションから回せない（#181）。
  人間レビューに回す。

### 生成物

- `skill-metrics.py` の生成ブロック（設計 §8.2）。`python3 scripts/skill-metrics.py --check` で鮮度を見る。
- 図（drawio）は触らない。

## 4. 未解決の判断

なし（§0 で人間が決めた）。

## 5. 関門の進捗（再開点）

- 実装: **完了**（`check-all.py` 30/30 緑・失敗 0 / 飛ばし 0）。実験なし（文面の変更のみ）
- 割り目（手順 4）: **「ここで割る」を人間が選択**（2026-10-07）。実装コミット `532020f`。
  **再開は手順 5 の Verifier 1 パス目から**（関門はまだ 1 つも回していない）
- 手順 5 Verifier 1 パス目: 未着手
- `/code-review` 1 パス目: 未着手
- 反証・差し戻し: 0 件

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| (a)/(b) の条件を置くか | 置かない（人間の判断） | §0 の 1。番号で指す判定では 2 パス目の修正が全件該当する |
| 狭いパスを割り目の質問に含めるか | 含めない（人間の判断） | §0 の 2 |
| 狭いパスに `/code-review` を当てるか | 当てない | Issue の実例で値があったのは変異を独立に設計させたこと |
| 狭いパスの指摘を直すか | 直さない・当て直さない | 無限後退を止める（Issue の「決めること」3 つ目） |
