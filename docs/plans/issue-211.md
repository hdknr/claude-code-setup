# Issue #211 — dev-loop: どのリポジトリでも使うスキルに、このリポジトリ固有の check-all.py と規約名が入っている

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 6 の「全部回す 1 本のコマンド」の括弧書き（`check-all.py` を名指し）と、「宣言の範囲を全部引く」の対比（`CLAUDE.md` の「〇〇を正とする」を名指し）の 2 箇所。版のバナー
- `plugins/dev-loop/skills/dev-loop/references/guard-rejections.md` — 「このリポジトリの `collect-guard-rejections.py`」を、どのリポジトリか分かる形に
- `plugins/dev-loop/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — dev-loop の version
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合のみ）
- `docs/plans/issue-211.md` — この計画ファイル
- `CLAUDE.md` — **手順 8 の焼き戻し**（PR #254 のマージ後、人間の指示で広げた）。「並行する周は、同じ版に上げて衝突する」節を足す。
  既存の「歯止めは毎回全部回す」節（I2 の根拠）は触らない

触らない:

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
  起点 `1867096`・base 参照 `origin/main` → `1867096f7447e09ac4cadd03513da0390e606826`（1 パス目）→
  **`63313790e6781d3e70b3cf042dd30c4e0203853b`（2 パス目以降。origin/main を取り込んだので当て直した）**
- 実装: 済（SKILL.md 2 箇所・guard-rejections.md 1 箇所・版 1.38.4 → 1.38.5）。`skill-metrics.py` は生成ブロックを変えなかった（`--check` は check-all に含む）
- grep: 修正前 4 件（うち実例 1）→ 修正後 1 件（実例の #233 のみ）
- `check-all.py`: 33/33 緑（失敗 0 / 飛ばし 0）。コミット `25b1bcb`
- 割り目 1（手順 4 完了時）: AskUserQuestion で提案 → **「ここで割る」が選ばれた**
- 関門 1 パス目: **Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件**（軽微 2 件。check-all 33/33 緑を独立確認）／
  **`/code-review` 指摘 8 件**（採否は §6 の表。直す 4・残課題 4）
- 指摘対応の起点（1 パス目の指摘対応を始める直前の HEAD）: `956674a79fd13b1837f4c3d8097a60a9d3994254`
- 1 パス目の指摘対応: **済**（R1・R2・R6・R7。コミット `9e674a0`）。
- origin/main が #222 で 1.38.5 に進んでいたので取り込み（`20b2160`）、版を **1.38.6** に上げた。
  生成ブロックは衝突したので main 側を取って `skill-metrics.py` で再生成。`check-all.py` 33/33 緑（失敗 0 / 飛ばし 0）。
- **base を当て直した**（HEAD の系譜が動いたため。式は同じ `git merge-base origin/main HEAD`）:
  `origin/main` → `63313790e6781d3e70b3cf042dd30c4e0203853b`。**2 パス目の関門にはこの SHA を渡す。**
- 次（**2 つ残っている**）: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目。
  2 パス目の指摘対応の起点は、その対応に入る直前の HEAD を記録する（狭いパス用）。
- 割り目 2（2 パス目の前）: AskUserQuestion で提案 → **「ここで割る」が選ばれた**
- 再開（2026-10-14）: `find-cycle.py` で当たり、この worktree・ブランチ・HEAD `e09fd62` を肯定的に確認。base `6331379` は HEAD の祖先で、origin/main の merge-base も不変。
- **手順 5 の当て直し（Verifier 2 パス目、`dev-loop:dev-loop-verifier`・sonnet）: 反証 0 件**（R1・R2・R6・R7 の修正先を一次ソースで確認。生成物・版も独立に緑）。
  `check-all.py` 33/33 緑（失敗 0 / 飛ばし 0）。
- **`/code-review` 2 パス目: 指摘 7 件**（採否は §6 の 2 パス目の表。直す 1・残課題 6）。
- 2 パス目の指摘対応の起点（狭いパス用。対応に入る直前の HEAD）: `72376ff9bd3b8cd75c01208784ffba4e5c4833a7`
- 2 パス目の指摘対応: C1 のみ（コミットは本計画の次のコミット）。`check-all.py` 33/33 緑（失敗 0 / 飛ばし 0）。
- **狭いパス（`dev-loop:dev-loop-verifier`・sonnet、起点 `72376ff`）: 反証 0 件**。軽微 1 件（N1）。
  変異 3 本を Verifier が設計（(a) 「みなさない」を削る (b) 代替を戻す (c) 「名指しで報告」を消す）が**当てていない**
  （文言を見る歯止めが無いと判断。陽性対照も無し）——**「素通り」ではなく「未実行」**。
- PR #254 作成。main が #210 で 1.38.6 に進んでいて衝突したので取り込み（`1b370bd`）、版を **1.38.7** に。
  取り込み後の main との正味の差分は、この周の変更だけであることを確認。`check-all.py` 33/33 緑。
  **PR 側の CI**: `check` pass・`build` pass（`deploy` は skipping）。mergeable。
- 手順 7: **マージは人間の承認待ち**。反映経路はプラグイン配布（マージ後の `plugin update`）と GitHub Pages（生成ブロック）。
- この周の起票: 0 件
- 手順 8: 学びの候補（未焼き戻し・人間に提示）: 並行する周が同じ patch 版に上げて衝突する形が、この周だけで 2 回起きた（#222・#210）。
- **手順 8 の焼き戻し**（PR #254 マージ後、人間が「CLAUDE.md に書いて」と指示）: ブランチ `issue/211-version-collision-lesson`
  （同じ worktree で `origin/main` から切った）で CLAUDE.md に「並行する周は、同じ版に上げて衝突する」節を足す。
  手順 7 のマージ後なので関門は残っていない（SKILL.md 手順 4 のとおり受入基準は広げない）。PR で人間レビューに回す。
- 実験: 陽性対照つきの grep のみ

## 6. 既知の限界・決着済みの論点

- README.md の 2 箇所は直さない（理由は §1）。
- Issue リンク（`hdknr/claude-code-setup/issues/…`）は実例として名指しされているので残す。
- SKILL.md 816 行の「**#233 では**、… `check-all.py` の緑が」は**事故の実例**として引いている（「このリポジトリでは」の形ではない）ので残す。
  → **1 パス目の `/code-review`（R7）に理由を反証され、撤回**——I1 は「実例として引く場合は `claude-code-setup` を名指しする」と書いており、
  リンクも名前も無い `#233` はそれを満たさない。`hdknr/claude-code-setup#233` に直す。
  リンクを持たない `#NNN` は SKILL.md に 76 箇所あり（リンク付きは 32）、他リポジトリでは別の Issue を指しうるが、**この周の範囲外**（Issue #211 の受入基準は「このリポジトリでは」の形に限っている）。

### 1 パス目の指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | （Verifier）1362 の指し先「はじめに」に、いつ読むかの補いが無い | 示せない（節名は実在・指し先検査は緑） | 無し | 残課題 |
| V2 | （Verifier）括弧を外して「無いリポジトリでは…」が独立した文になった | 示せない（意味は不変） | 無し | 残課題 |
| R1 | 1362 は「はじめに」を指すが、「はじめに」の列挙に「全部回すコマンド」が無い。発見先を `CLAUDE.md` に絞り `.claude/dev-loop.md` を落とした | 示せる（SKILL.md 53–60 行の列挙に該当項目が無い） | I2・I3（発見の経路が実在しない） | 直す |
| R2 | guard-rejections.md の「利用者のリポジトリにも無い」は、`claude-code-setup` 自身で使うと偽 | 示せる（`scripts/collect-guard-rejections.py` が実在） | I1（新しく書いた事実が偽） | 直す |
| R3 | `prepare-worktree.sh:100` のコメントが `scripts/test-worktree-scripts.py` を名指し。grep の語彙は素のパスを拾えない | 示せる（パスは実在しない側がある）が「このリポジトリでは」の形ではない | 無し（I1 の形に当たらない） | 残課題 |
| R4 | SKILL.md 125 の「`README.md` も設計ドキュメントも」は名前の無い参照 | 示せない（同梱の README と公開の設計ドキュメントを指す。読者のリポジトリとは読めない） | 無し | 残課題 |
| R5 | `agents/dev-loop-verifier.md:49` の `uv run mkdocs build` 例 | 「といったもの」の例示 | 無し | 残課題 |
| R6 | 1432 の「複製を 1 箇所に寄せ、他からは指すだけにする」を鉤括弧で引くが、その名の規範はどこにも無い | 示せる（grep 0 件） | I3（対比の片側が指し先を持たない） | 直す |
| R7 | 816 の `#233` はリンクも名前も無く `check-all.py` を引く | 示せる（I1 の文言「`claude-code-setup` を名指しする」に反する） | I1 | 直す（§6 の決着を撤回） |
| R8 | 計画ファイルの陽性対照「3 件」と記録「4 件」が食い違う | — | — | 対象外（関門は計画ファイルを検査しない。手順 6） |

### 2 パス目の指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| C1 | 手順 6 に足した「無ければ `Makefile`・`package.json` の scripts・CI 定義を見る」が、どれを「全部回す 1 本」とみなすかを選ばせる | 示せる（SKILL.md 手順 6 の当該文。「選ばせる形にしない」の直後で選ばせている） | I3（選ばせない） | 直す |
| C2 | `evals/resume-no-new-worktree/case.yaml:16,33` が `docs/plans/issue-181.md`・`issue-183.md` をリポジトリ名無しで「正とする」 | 示せない（eval のケース作者向けコメント。`claude plugin eval` は配布元で回す。「このリポジトリでは」の形でもない） | 無し | 残課題 |
| C3 | I1 の grep は修正後も 820 行に当たり、0 件を合格条件にできない（判別が人の除外に依る） | 実験の記述についての指摘で、成果物の失敗ではない | 無し | 残課題 |
| C4 | guard-rejections.md の「そのスクリプトの docstring を正とする」は他リポジトリの読者に到達できない（URL が無い） | 示せる（パスも URL も無い） | 無し（I1 の形には当たらない。名指しは満たす） | 残課題 |
| C5 | `hdknr/claude-code-setup#233` がリンクでなく、`check-site-links.py` の外 | 示せない（現に正しい番号） | 無し | 残課題 |
| C6 | 「はじめに」の新項目が CLAUDE.md の項の下にあり `.claude/dev-loop.md` を含まない。括弧書きが手順 6 の規範を複製 | 示せない（発見の失敗例は無い） | 無し | 残課題 |
| C7 | 手順の追加なので CLAUDE.md の semver では minor | 判断の相違（I4 は patch と固定。受入基準の変更は人間が決める） | 無し（I4 と CLAUDE.md の食い違い） | 残課題（PR で人間に判断を仰ぐ） |

### 狭いパスの指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | 「はじめに」3 の「テスト実行（`Makefile` / `package.json` scripts / CI 定義から推測）」と手順 6 の「`Makefile` のターゲットを全部の 1 本とみなさない」の読み分けが、文面で明示されていない | 示せない（読み分けは可能と Verifier 自身が判定） | 無し | 人間が決める |
