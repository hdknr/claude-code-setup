# Issue #210 — 「検証スコープを絞って」が必須の「問いを局面に絞らない」と衝突する

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 欠票の項の「検証スコープを絞って報告を短く」を「報告を短く・範囲は絞らない」に直す・版
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「観点を絞って短く返す」を同じ趣旨に直す
- `plugins/dev-loop/agents/dev-loop-verifier.md` — 6 番目「報告は簡潔に」に「範囲は絞らない」を足す
- `docs/plugins/dev-loop-design.md` — 同じ文の写し（Issue 本文は挙げていないが、grep で当たった 4 つ目の複製）。§8.2 の生成ブロック（`skill-metrics.py` が書く）
- `plugins/dev-loop/.claude-plugin/plugin.json` — version 1.38.2 → 1.38.3（記述の修正なので patch）
- `.claude-plugin/marketplace.json` — 同じ版
- `docs/plans/issue-210.md` — この計画ファイル

触らない:

- 多レンズ化（任意）の規定そのもの・「問いを局面に絞らない」の規定そのもの（どちらも正しい。直すのは衝突して読める 1 文）
- SKILL.md 827 行「範囲を絞って読む」（ソースの読み方の話で、関門に渡す問いの範囲ではない）・1353 行以降「2 パス目の対象の差分を絞ってよい」（受入基準は絞らないと明記済み）
- `description`（要約にこの話は無い）

**複製の数**: 「報告を短くするために絞る」を述べている箇所は 4 つ——SKILL.md・`prompts/verifier.md`・`agents/dev-loop-verifier.md`・設計ドキュメント。
**分けない理由**: 4 つとも同じ 1 文の写しで、1 つだけ直すと残りが衝突したまま残る（受入基準 I1 はまさに「どこにも無い」）。

## 2. デプロイ経路

- `plugins/`：version bump → main マージでマーケットプレイス経由（利用者が `plugin update`）。
- `docs/`：main への push で GitHub Pages に自動デプロイ。

## 3. 受入基準

**不変条件**

- **I1. 範囲を絞れと読める文が無い。** 関門（Verifier・レビュー）に渡す問い・受入基準・経路の一覧について、
  「絞れ」と読める文が SKILL.md・`prompts/`・`agents/`・設計ドキュメント・README のどこにも無い。
- **I2. 「報告を短く」の意図は残る。** 4 箇所とも、報告を短くする理由（途中で切れると「反証なし」と区別がつかない／完走しない）と要求が残っている。
- **I3. 直した文が、別の規定と食い違わない。** とくに必須の「問いを局面に絞らない」と、多レンズ化（任意。分けるなら各体に表をまるごと渡し、経路を全部挙げる担当を 1 体置く）。
- **I4. 版が 3 種類で揃い（1.38.3）、`check-all.py` が緑。**

**それを破りうる経路**（文面が関門・読者に届く入口）

| 入口 | 守り方 |
| --- | --- |
| SKILL.md（親が読む） | 直す。`grep '絞'` の全ヒットを読んで分類 |
| `prompts/verifier.md`（子に渡す文面。狭いパスの差し込みも同じファイル） | 直す |
| `prompts/review-handoff.md`（`/code-review` に渡す文面） | grep で確認（当たらなければ該当なし） |
| `agents/dev-loop-verifier.md`（同梱の Verifier 定義） | 直す |
| `references/*.md` | grep で確認 |
| 設計ドキュメント・`plugins/dev-loop/README.md`・`docs/plugins/*.md` | 設計ドキュメントは直す。残りは grep で確認 |
| `evals/` | grep で確認 |

**証明できるもの**: I1〜I4 はすべて grep・目視・`check-all.py` で確かめられる。
**未証明**: なし（「この文面で実際に報告が切れにくくなるか」は主張しない）。

**生成物**: 該当あり——設計ドキュメント §8.2 の生成ブロック（`skill-metrics.py`。SKILL.md の行数が変わりうる）。
`python3 scripts/skill-metrics.py --check` が緑であること。図（drawio）は触らない。

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目 = 4 つの受け渡し。

## 4. 未解決の判断

- なし

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/210-report-not-scope`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-210`・
  起点 `6071e01`・base 参照 `origin/main` → `6071e01e9c1855e3a3c1db053d3e1a53cda26020`
- 実装: 完了（`098150c`・計画修正 `check-all.py` 33/33 緑）
- 関門: 未着手（次は手順 5 の 1 パス目）
- 割り目 1（手順 4 完了時）: 訊いた → **「ここで割る」**を選択（2026-10-14）。再開は手順 5 の 1 パス目から
- 交絡: 実験なし

## 6. 既知の限界・決着済みの論点

- Issue 本文の行番号（1040・147）は起票時点のもの。base では SKILL.md 1073・verifier.md 156。
- 設計ドキュメントの写しは Issue 本文に無いが、I1 の範囲（「どこにも無い」）に入るので直す。
