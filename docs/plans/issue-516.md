# Issue #516 — absent-lines: 「訊く場面」の割り目の項で太字が崩れている

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-10-28）の周。**不在の周**である——訊く場面は
  `references/absent-lines.md` の「訊く場面」のとおり訊かずに進める。
- 元の課題: #496 の `/code-review` 1 パス目（CR1-1）。本文の印は `<!-- cruise-found: #474 -->`。
- 使った線（出所: cruise の確かめた線（台帳 `issue-474`）。親から受けた指示で確かめた）:
  `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`周の途中の課題 = 台帳に足して直す`。
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-474`））。

## 失敗（実物）

`plugins/dev-loop/skills/dev-loop/references/absent-lines.md` 170 行の `訊かずに**「このまま続ける」**として進め` を
GitHub の Markdown API（`gh api -X POST /markdown -f mode=gfm`）で描くと、太字にならず `**` が 2 つ字のまま残る（著者が実走して確かめた）。
原因は #496 と同じ CommonMark の flanking の規則——開きの `**` は文字 `に` の直後・句読点 `「` の直前で left-flanking にならず、
閉じの `**` は句読点 `」` の直後・文字 `と` の直前で right-flanking にならない。

**ファイル全体を同じ API で描き、コード（`<pre>`・`<code>`）の外に字のまま残る `*` を含む行を数えると、変更前は 1 行（この 170 行）だけ**だった——
このファイルに同じ形の崩れはほかに無い。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 170 行の `に**「このまま続ける」**と` を `に **「このまま続ける」** と` に分ける（1 箇所だけ）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行（1.63.1 → 1.63.2）
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — `version`
- `.claude-plugin/marketplace.json` — dev-loop の `version`
- `docs/plans/issue-516.md` — この計画ファイル

触らない:

- **dev-loop の他のファイルの、描画で `*` が字のまま残る行**——同じ走査で、`SKILL.md` 26 行・`references/resume.md` 3 行・`README.md` 1 行・
  `agents/dev-loop-verifier.md` 1 行・`prompts/verifier.md` 1 行が当たった（多くは `**「…」**` を文字で挟む同じ型。`SKILL.md` には入れ子のバッククォートの
  ような別の型も混ざり、1 行ずつは仕分けていない）。Issue の範囲（absent-lines.md の 1 箇所）の外。直す線は既定なので直さない
- spec-loop（並行する #499 の周が触る）・他のプラグイン・`scripts/`

## 複製の数

1 箇所（absent-lines.md 170 行）。同じ文はほかに無い（`grep -rn 'このまま続ける' plugins/` が当たるのは `SKILL.md` の割り目の選択肢の言及で、
そちらは太字の崩れを持たない——上の走査で `SKILL.md` の当たり行にこの文言は無い）。分けない理由: 1 箇所なので分けるものが無い。

## デプロイ経路

main へのマージ → GitHub Pages の再ビルド（このファイルはサイトに取り込まれない——公開ページは GitHub の blob を指す）と、
プラグインの配布（`marketplace.json` のカタログと symlink 経路）。マージはこの周ではしない（親がする）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 割り目の項の 2 つの太字（`手順 4・手順 6 の割り目` と `「このまま続ける」`）が、**どちらも太字として描かれ、`*` が字として残らない** | GitHub の描画（cmark-gfm） | 変更後の 170 行を `gh api /markdown`（gfm）で描き、`<strong>` が 2 つの文言を囲み、`*` が 1 つも無いこと。**陽性対照**: base の 170 行で同じ観測点が `**` を字のまま出す |
| A2 | 文言は変わらない——変えるのは `**` の外側に空白を 2 つ足すことだけ | 編集の取り違え | `git diff <base> -- absent-lines.md` が 1 行の置き換えで、空白を除くと前後が一致 |
| A3 | absent-lines.md 全体で、描画のコードの外に `*` が字のまま残る行が 0 | このファイルの別の箇所の同じ崩れ | ファイル全体を gfm で描き、`<pre>`・`<code>` を除いた本文に `*` を含む行が 0（変更前は 1 行——陽性対照） |
| A4 | 版が 3 種類（`marketplace.json`・`plugin.json`・dev-loop の `SKILL.md` 2 本の 2 行）で 1.63.2 に揃う | 版の上げ忘れ・片側だけ | `python3 scripts/check-plugin-versions.py`・`check-version-bump.py origin/main` |
| A5 | 歯止めが全部緑 | どれか | `python3 scripts/check-all.py --jobs 2` と、push 後の `gh pr checks` |
| A6 | 生成物の鮮度——`SKILL.md` を触るので §8.2 の生成ブロックが該当。図は触らないので該当なし | 版の行の変更で測定値が動く | `python3 scripts/skill-metrics.py --check` が 0（check-all の中でも回る） |

組み合わせ（必須要件の掛け算）: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

**未証明**: 無し（描画は GitHub の API で実際に描いて確かめられる）。
**BLOCKED**: 無し。
**実験**: 描画の観測 1 つ。交絡の候補——「API が別の描画器なら、崩れていても `*` が出ない」→ base の 170 行・base のファイル全体で同じ API が
`**` を字のまま出すこと（陽性対照）で潰す。

## 未解決・確認待ち

無し。

## 起票

- この周の起票: 0 件（起票の承認は不在のため訊いていない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/516-asking-bold`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-516`、
  起点 `97257e2`、base の参照 `origin/main`、base の SHA `97257e28ad3aa44a99d430f444b91f8956702252`
  （`EnterWorktree` は使わず、`git -C <worktree>` と絶対パスで作業している——親の指示）
- 手順 4 の割り目: 不在のため訊かず続けた
- 交絡を潰した手順: base の 170 行と base のファイル全体を同じ API で描き、`**` が字のまま出ることを確かめた（陽性対照）

## 既知の限界・決着済みの論点

- 論点: dev-loop の他のファイルにある、描画で `*` が字のまま残る行を直すか。決着: 直さない（`触らない:`）。理由: Issue の範囲の外で、直す線は既定。
