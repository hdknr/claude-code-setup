# Issue #211 — dev-loop: どのリポジトリでも使うスキルに、このリポジトリ固有の check-all.py と規約名が入っている

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 6 の「全部回す 1 本のコマンド」の括弧書き（`check-all.py` を名指し）と、「宣言の範囲を全部引く」の対比（`CLAUDE.md` の「〇〇を正とする」を名指し）の 2 箇所。版のバナー
- `plugins/dev-loop/skills/dev-loop/references/guard-rejections.md` — 「このリポジトリの `collect-guard-rejections.py`」を、どのリポジトリか分かる形に
- `plugins/dev-loop/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — dev-loop の version
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合のみ）
- `docs/plans/issue-211.md` — この計画ファイル

触らない:

- `CLAUDE.md` — 既に「歯止めは毎回全部回す」節で `python3 scripts/check-all.py` を名指ししている（受入基準 I2 はこの記述で満たされる）
- `plugins/dev-loop/README.md` — 99 行の「このリポジトリ」は**インストール先**のスコープの説明（汎用）、155 行は直前で clone した `claude-code-setup` を指す（配布元の README なので正しい対象）
- `#110` などの Issue リンク — URL が `hdknr/claude-code-setup` を名指ししており、実例と分かる形になっている
- 他プラグイン（Issue の範囲外）

**複製の数**: 「対象リポジトリ固有のものはそのリポジトリの `CLAUDE.md` に書く」という規範に反する箇所が 3（SKILL.md 2・guard-rejections.md 1）。
規範自身は SKILL.md の 1 箇所（手順 5 の「リポジトリ固有のコマンドの形は対象リポジトリの `CLAUDE.md` 側に書く」）。
版は 3 種類（marketplace / plugin / SKILL.md 2 行）。いずれも同じ型の文言修正で、1 周で閉じるので分けない。

## 2. デプロイ経路

- プラグイン配布（main へのマージでカタログが進む。利用者側は `plugin update`）。
- `docs/` の生成ブロックが動けば GitHub Pages のデプロイにも乗る。

## 3. 受入基準

**I1. `plugins/dev-loop/` の配下に、このリポジトリ固有のパス・規約名が「このリポジトリでは」の形（＝読む側のリポジトリを指すと読める形）で入っていない。** 実例として引く場合は `claude-code-setup` を名指しする。

| 経路（スキルが読まれる入口） | 守り方 |
| --- | --- |
| P1 `SKILL.md`（起点に載る） | 2 箇所を汎用の言い回しに |
| P2 `references/*.md`（条件つきで読まれる） | guard-rejections.md の 1 箇所を `claude-code-setup` 名指しに |
| P3 `prompts/*.md`（委譲文） | grep で該当なしを確認 |
| P4 `agents/`・`scripts/`・`evals/`（プラグインの他の入口） | grep で該当なしを確認 |
| P5 `README.md`（配布元の説明） | 該当なしと判定（上の「触らない」） |

grep は「このリポジトリ／本リポジトリ／当リポジトリ／check-all／〇〇を正とする」に加え、**名前を含まない参照**（「このプロジェクト」「手元の」等）もページを開いて確かめる。

**I2. このリポジトリでは、`CLAUDE.md` の記述から `check-all.py` が発見される。** SKILL.md の新しい文面が「`CLAUDE.md` から発見する」と言い、`CLAUDE.md` 側に `python3 scripts/check-all.py` の記述がある。

**I3. 意味を落とさない**: 手順 6 の「全部回す」規範（必須・選ばせない・無ければ名指しで報告）と、「宣言の範囲」項の対比（複製を作るな vs 宣言の範囲で検査しろ）が、書き換え後も残っている。

**I4. version bump**: marketplace.json / plugin.json / SKILL.md 2 行が同じ値（patch）。`check-all.py` が全部緑。

**I5（掛け算）**: I1〜I4 を Verifier と `/code-review` の両方に、1 パス目と 2 パス目の両方で渡す（4 つの受け渡し）。

### 証明の手段

- I1: grep（陽性対照: 修正前の worktree で同じ grep が 3 件当たることを先に見る）
- I2: `CLAUDE.md` の該当行
- I3: 差分を読む
- I4: `check-all.py`
- 未証明: なし。

### 生成物

- 該当: `skill-metrics.py` が `SKILL.md` の節構造から設計ドキュメント §8.2 を生成する。`--check` が緑であること（文字数が動けば再生成）。
- drawio: 触れない。

## 4. 未解決

なし。

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/211-repo-agnostic-skill`・worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-211`・
  起点 `1867096`・base 参照 `origin/main` → `1867096f7447e09ac4cadd03513da0390e606826`
- 実装: 済（SKILL.md 2 箇所・guard-rejections.md 1 箇所・版 1.38.4 → 1.38.5）。`skill-metrics.py` は生成ブロックを変えなかった（`--check` は check-all に含む）
- grep: 修正前 4 件（うち実例 1）→ 修正後 1 件（実例の #233 のみ）
- `check-all.py`: 33/33 緑（失敗 0 / 飛ばし 0）。コミット `25b1bcb`
- 割り目 1（手順 4 完了時）: AskUserQuestion で提案 → **「ここで割る」が選ばれた**
- 関門: 未（次は手順 5 の Verifier 1 パス目と `/code-review` 1 パス目）
- 実験: 陽性対照つきの grep のみ

## 6. 既知の限界・決着済みの論点

- README.md の 2 箇所は直さない（理由は §1）。
- Issue リンク（`hdknr/claude-code-setup/issues/…`）は実例として名指しされているので残す。
- SKILL.md 816 行の「**#233 では**、… `check-all.py` の緑が」は**事故の実例**として引いている（「このリポジトリでは」の形ではない）ので残す。
  リンクを持たない `#NNN` は SKILL.md に 76 箇所あり（リンク付きは 32）、他リポジトリでは別の Issue を指しうるが、**この周の範囲外**（Issue #211 の受入基準は「このリポジトリでは」の形に限っている）。
