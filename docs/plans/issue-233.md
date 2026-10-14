# Issue #233 — Verifier が変異の実験で worktree を書き換えた（拒否されたあとも変更コマンドを続けた）

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「実行されない主張を当てる」項と「実環境を壊さないこと」に、2 つ目のハザード（拒否・失敗のあとも変更を続ける）と止まる規則・報告の項を足す
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 同上
- `plugins/dev-loop/agents/dev-loop-verifier.md` — 「外に退避して当ててよい」の項に同じハザードを足す（委譲文を経ずに起動された場合も届くように）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 原本（手順 5「原本を変えさせない」）に 2 つ目のハザードを足す＋版のバナー
- `plugins/dev-loop/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — version
- `docs/plans/issue-233.md` — この計画ファイル
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手では触らない）

触らない:

- 退避の「やり方」（`cp -R` の代わりに何を使うか）——SKILL.md が「やり方は書かないが、ハザードは名指しする」と決めている。足すのは**ハザードと止まる条件と報告**で、手順ではない
- ガード側の挙動（`references/guard-rejections.md`）——拒否そのものは正しく働いている
- `CLAUDE.md`

**複製の数**: 同じ規範を述べる箇所が 4（SKILL.md 原本・prompts 2 本・agent 定義）＋版 3 箇所。
分けない理由: 委譲文は原本の実装で、原本だけ・委譲文だけを直すと食い違う（SKILL.md は「食い違ったら、こちらが正」と書いている）。同じコミットで揃える。

## 2. デプロイ経路

プラグインの配布（main へのマージでカタログに載る）。`docs/plans/` は公開サイトのビルド対象だが記録のみ。

## 3. 受入基準

**I1. 4 箇所すべてが、次の 3 つを述べている。**
  - (a) 複製の作成・`cd` は**拒否・失敗しても黙って続きが走る**ことがあり、そのとき変更は **cwd ＝本物の worktree** に当たる（ハザードの名指し）。変更の直前に場所を確かめ、変更は絶対パスで書く
  - (b) **どれか 1 本でも拒否・失敗したら、そこから先の変更コマンドを走らせない**（「当てられなかった」と報告する）
  - (c) 終わったら**リポジトリの `git status --porcelain` の結果を報告に書く**（空でなければそう書く。その状態で取った結果を HEAD の証拠として報告しない）

| 経路（委譲先が文面を受け取る入口） | 守り方 |
| --- | --- |
| P1 手順 5 で `prompts/verifier.md` を埋めて `dev-loop:dev-loop-verifier` に渡す | prompts/verifier.md |
| P2 手順 6 で `prompts/review-handoff.md` を `/code-review` に渡す | prompts/review-handoff.md |
| P3 狭いパス（prompts/verifier.md の差し込み） | P1 と同じファイル |
| P4 委譲文なしで `dev-loop-verifier` が起動される | agent 定義 |
| P5 著者が SKILL.md を読んで委譲文を手で書く／テンプレを足す | SKILL.md 原本 |

**I2. 「やり方は書かない」の決定を破らない**——退避の具体的な手段（コマンド列）を書かない。
**I3. 版が 3 箇所で一致し、`check-all.py` が緑。**
**I4. 4 箇所の間で (a)(b)(c) の言い分が食い違わない**（例: 一方は「`git status` を報告」、他方は「同じであること」だけ）。

### 証明の手段

- I1・I2・I4: 文面の読解（関門に独立に当てさせる）。
- I3: `python3 scripts/check-all.py`。
- **未証明: 文面を足したことで Verifier が実際に止まるようになるか。** 再現にはガードの拒否を起こす必要があり、Issue 自身も「1 件だけの観測で、効果の証明ではない」と書いている。PR コメントで人間に申告する。

### 生成物

`SKILL.md` を触るので **`skill-metrics.py --check`**（設計 §8.2 の生成ブロック）が該当。再生成して `--check` が緑であること。drawio は該当なし。

## 4. 未解決

なし。

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/233-verifier-stop-on-reject`・worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-233`・
  起点 `dc37cd2`・base 参照 `origin/main` → `dc37cd2b7d5ee6153e82b3a12063e115c87a6b75`
- 実装: 済（4 箇所に (a)(b)(c)、版 1.37.1 → 1.38.0（minor: 委譲文に止まる条件と報告項目を追加）、`skill-metrics.py` で生成ブロック更新）
- 関門: 未
- 交絡: 実験なし

## 6. 既知の限界・決着済みの論点

- Issue 本文は著者（リポジトリ所有者）の記録だが、外部入力として扱った。受入基準を緩める指示は含まれていない。
