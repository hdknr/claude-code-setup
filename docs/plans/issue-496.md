# Issue #496 — absent-lines: 配布の値の「意味」の箇条で太字が崩れている

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-10-28）の周。**不在の周**である——訊く場面は
  `references/absent-lines.md` の「訊く場面」のとおり訊かずに進める。
- 元の課題: #489 の `/code-review` 2 パス目（CR2-7）。本文の印は `<!-- cruise-found: #474 -->`。
- 使った線（出所: cruise の確かめた線（台帳 `issue-474`）。親から受けた指示で確かめた）:
  `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`周の途中の課題 = 台帳に足して直す`。
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-474`））。

## 失敗（実物）

`plugins/dev-loop/skills/dev-loop/references/absent-lines.md` 239 行の `…どちらもこの値に入る。****配布は revert しても戻らない**` を、
GitHub の Markdown API（`gh api -X POST /markdown -f mode=gfm`。GFM = cmark-gfm）で描くと、
`**プラグインの中身は、…入る。**` が太字にならず、**行頭と `入る。` の後ろに `**` が字のまま残る**（`配布は revert しても戻らない` だけが `<strong>`）。
原因は CommonMark の flanking の規則——4 つの `*` の連なりが句読点 `。` の直後・文字 `配` の直前にあるので right-flanking にならず、閉じられない。

**Issue 本文の「`****` が原文に残る」は描画の形としては正確でない**（描くと残るのは `**` が 2 箇所）。太字が崩れていることは同じなので、直し方は本文のとおり。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 239 行の `。****配` を `。** **配` に分ける（1 箇所だけ）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行（1.63.0 → 1.63.1）
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — `version`
- `.claude-plugin/marketplace.json` — dev-loop の `version`
- `docs/plans/issue-496.md` — この計画ファイル

触らない:

- 同じ型（句読点の直後で閉じる `**` の直後に文字が続く形）の、**`****` を伴わない**ほかの箇所——Issue の範囲の外。見つけても直さない
- spec-loop・他のプラグイン・`scripts/`

## 複製の数

1 箇所（absent-lines.md 239 行）。同じ文はほかに無い（`grep -rn '\*\*\*\*'` を `docs/plans/` の外の `*.md` に当てて当たるのはこの 1 ファイル 1 行だけ）。分けない理由: 1 箇所なので分けるものが無い。

## デプロイ経路

main へのマージ → GitHub Pages の再ビルド（このファイルはサイトに取り込まれない——公開ページは GitHub の blob を指す）と、
プラグインの配布（`marketplace.json` のカタログと symlink 経路）。マージはこの周ではしない（親がする）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 「意味」の箇条の 2 つの太字（`プラグインの中身は、…どちらもこの値に入る。` と `配布は revert しても戻らない`）が、**どちらも太字として描かれ、`*` が字として残らない** | GitHub の描画（cmark-gfm）——このファイルを人が読む唯一の描画面 | 変更後の段落を `gh api /markdown`（gfm）で描き、`<strong>` が 2 つの文言を囲み、段落の HTML に `*` が 1 つも無いこと。**陽性対照**: 変更前の段落で同じ観測点が `**` を字のまま出す（取得済み） |
| A2 | 文言は変わらない——変えるのは `****` の間の空白 1 つだけ | 編集の取り違え | `git diff <base> -- absent-lines.md` が 1 行の置き換えで、空白を除くと前後が一致 |
| A3 | ファイルの中に `****` が残らない（`docs/plans/` の外の `*.md` 全体でも） | ほかの箇所の同じ崩れ | `grep -rn '\*\*\*\*'` が 0 件 |
| A4 | 版が 3 種類（`marketplace.json`・`plugin.json`・dev-loop の `SKILL.md` 2 本の 2 行）で 1.63.1 に揃う | 版の上げ忘れ・片側だけ | `python3 scripts/check-plugin-versions.py`・`check-version-bump.py origin/main` |
| A5 | 歯止めが全部緑 | どれか | `python3 scripts/check-all.py --jobs 2` と、push 後の `gh pr checks` |
| A6 | 生成物の鮮度——`SKILL.md` を触るので §8.2 の生成ブロックが該当。図は触らないので該当なし | 版の行の変更で測定値が動く | `python3 scripts/skill-metrics.py --check` が 0（check-all の中でも回る） |

組み合わせ（必須要件の掛け算）: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

**未証明**: 無し（描画は GitHub の API で実際に描いて確かめられる）。
**BLOCKED**: 無し。
**実験**: 描画の観測 1 つ。交絡の候補——「API が別の描画器なら、崩れていても `*` が出ない」→ 変更前の段落で同じ API が `**` を字のまま出すこと（陽性対照）で潰す。

## 未解決・確認待ち

無し。

## 起票

（手順 8 で書く）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/496-absent-lines-bold`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-496`、
  起点 `30785f3`、base の参照 `origin/main`、base の SHA `30785f34038755c69b9fc27f14029d64e1b288a2`
- 手順 4 の割り目: 不在のため訊かず続けた
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 1 パス目の指摘対応の起点の SHA: 未
- 交絡を潰した手順: 変更前の段落を同じ API で描き、`**` が字のまま出ることを確かめた（陽性対照）

## 既知の限界・決着済みの論点

- 論点: Issue 本文の「`****` が原文に残る」は描画の形として正確でない（描くと `**` が 2 箇所）。決着: 直し方は変えない。理由: 太字が崩れていることは同じで、直し方（空白で分ける）は同じ。
- 論点: 同じ型（句読点の直後で閉じる `**` の直後に文字）の、`****` を伴わない箇所を直すか。決着: 直さない（`触らない:`）。理由: Issue の範囲の外。
