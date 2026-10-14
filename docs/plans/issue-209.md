# Issue #209 — SKILL が Verifier に渡せと定めた 3 点が prompts/ のテンプレートに無い

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 項目 7 に 3 点を足す
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 項目 6 に 3 点を足す
- `plugins/dev-loop/agents/dev-loop-verifier.md` — 項目 5 に 3 点を足す（Issue の「任意」を採る）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版のバナーだけ（1.38.1 → 1.38.2）
- `plugins/dev-loop/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — dev-loop の version
- `docs/plans/issue-209.md` — この計画ファイル
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）

触らない:

- `SKILL.md` の本文（規定は正しい。届いていないのはテンプレート側）
- 「SKILL が渡せと定めたものがテンプレートにあるか」の新しい歯止め（下の 4 で検討し、作らないと決めた）
- description（3 箇所とも変えない）

**複製の数**: 3 点を述べる箇所は、この周の後で 4 つ——`SKILL.md`（原本）・`verifier.md`・`review-handoff.md`・
`dev-loop-verifier.md`。**分けない理由**: テンプレートは「SKILL の規定の実装」で、SKILL が
「食い違ったらこちらが正」と既に宣言している。agent 定義も同じ宣言（手順 5 が正）を持つ。
写しを減らす手段（テンプレートが SKILL を引用する）は無い——委譲先は SKILL を読まない。

## 2. デプロイ経路

- `plugins/`：プラグインの version bump で利用者に届く（`plugin update`）。
- `docs/plans/`：main への push で GitHub Pages に載る。

## 3. 受入基準

**不変条件**

- **I1.** SKILL.md 手順 5「あわせて上の 3 つも渡す」の 3 点——(a) BLOCKED 側に寄せていないか、
  (b)「何が無いのか」が環境・権限・道具か（時間・手間なら BLOCKED ではない）、
  (c) 主張を弱めれば分類そのものが要らなくならないか——が、**委譲先に届く経路すべて**に載っている。
- **I2.** 既存の記述（「探していないだけか」「BLOCKED を未証明に寄せる誤り」など）を消さない・緩めない。
- **I3.** version が 3 種類（marketplace.json / plugin.json / SKILL.md の 2 行）で 1.38.2 に揃う。
- **I4.** `check-all.py` が全部緑。

**I1 を破りうる経路**（委譲先が BLOCKED の分類を検査するときに読む文面。差分ではなく SKILL の委譲の入口から数える）

| 経路 | 文面 | 期待 |
| --- | --- | --- |
| E1 手順 5 の Verifier（1・2 パス目） | `prompts/verifier.md` 項目 7 | 3 点がある |
| E2 狭いパスの Verifier | 同じ `prompts/verifier.md`（差し込みだけ違う） | E1 で兼ねる |
| E3 手順 6 の `/code-review`（1・2 パス目） | `prompts/review-handoff.md` 項目 6 | 3 点がある |
| E4 同梱 agent を素で起動した場合（テンプレートを使わない呼び出し） | `agents/dev-loop-verifier.md` 項目 5 | 3 点がある |
| E5 多レンズ化・fan-out の各体 | E1・E3 のテンプレートを各体に渡す | E1・E3 で兼ねる |

**掛け算**: 「両方の関門」×「2 パス」= 4 つの受け渡し。どれも同じテンプレートなので E1・E3 で 4 つとも兼ねる。

### 証明の手段

- I1: `grep` で 3 ファイルに 3 点の語句があることを見る。
- I3・I4: `python3 scripts/check-all.py`。
- **未証明**: なし。**BLOCKED**: なし。

### 生成物

- `skill-metrics.py` の生成ブロック（設計ドキュメント §8.2）——`SKILL.md` と `prompts/` を測るので**該当する**。
  `check-all.py` が `--check` で見る。図の書き出しは触らないので該当なし。

## 4. 未解決の判断

- **「SKILL が渡せと定めたものがテンプレートにあるか」を機械で見られるか**（受入基準 2）——**汎用には見られない。作らない。**
  - SKILL の「渡す」は散文で、**何が「渡すもの」かを機械で切り出す印が無い**（`mutation-claim:` のような宣言が無い）。
  - 前例の `test-worktree-scripts.py` の `check_norm_shape` は、**規定ごとに手で語句を書いた検査**で、
    **消えたことは捕まえるが、SKILL に新しく足した「渡す」が届いていないこと（#209 の形そのもの）は捕まえない**。
    今回の 3 点に同じ検査を足しても、捕まえるのは「後で消された」だけで、この型の再発は防げない。
  - 見られるようにするなら、SKILL 側に「渡すもの」の印を置き、テンプレート側の対応と突き合わせる歯止めが要る。
    **実データで失敗を示せるのは #209 の 1 件だけ**なので、起票はしない（手順 6 の 3 条件）。PR コメントの残課題に書く。

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/209-blocked-checks-in-prompts`・
  worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-209`・
  起点 `ab215f1`・base の参照 `origin/main`・**base `ab215f1c4887b4bddc260cfdca1c6f9ae8aba962`**
- 実装: `e2c4db3`（`check-all.py` 33/33 緑）
- 関門: 未着手。次は手順 5（Verifier 1 パス目）と手順 6（`/code-review` 1 パス目）
- 割り目 1（手順 4 の完了時）: **AskUserQuestion で提示 → 「ここで割る」が選ばれた**
- 反証・差し戻し: なし
- 交絡: 実験なし

## 6. 既知の限界・決着済みの論点

- 機械で見る歯止めは作らない（4 を参照）。
