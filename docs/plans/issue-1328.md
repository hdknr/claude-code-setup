# Issue #1328: spec-ir.md の見積もりの理由 3 の行末の古い文の切れ端を消す

## 変更範囲

触る:

- `plugins/spec-loop/references/spec-ir.md` — 「書き起こす前の見積もり」の理由 3 の 2 行目の行末の切れ端「——一律の線は、どちらかの仕様で誤る。」を消す
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版 0.127.0 → 0.127.1（patch）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（7 ファイル）
- `docs/plans/issue-1328.md` — この計画

触らない:

- `docs/plans/issue-1302.md` — 元の周の記録（指摘 R1 の行は当時の記録なので直さない）
- spec-ir.md の他の文言

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

## デプロイ経路

main へのマージ → GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。

## 周の大きさ

同じ規範を述べる箇所の数: 切れ端の文言はリポジトリに 1 箇所（`git grep -n "どちらかの仕様で誤る"` は spec-ir.md の 137・138 行と、元の周の計画 `docs/plans/issue-1302.md` の指摘の記録 1 行）。137 行は理由 3 の本文（「一律の線を引くと、どちらかの仕様で誤る」）で残す。複製は 1。

## 受入基準

不変条件 × 経路:

| # | 不変条件 | 経路（入口） | 確かめ方 |
| --- | --- | --- | --- |
| A1 | spec-ir.md に切れ端「——一律の線は、どちらかの仕様で誤る。」の行が無い | spec-ir.md 本文（利用者・スキルが読む）・公開サイト（spec-loop の references はサイトに載らない——mkdocs の docs/ の外） | `git grep -n "一律の線は、どちらかの仕様で誤る" -- plugins/spec-loop/references/spec-ir.md` が直した後は 0 行。陽性対照: `git grep -n "一律の線は、どちらかの仕様で誤る" ac0b3f40 -- plugins/spec-loop/references/spec-ir.md` が 1 行（138 行） |
| A2 | 文言のほかの差分が無い（138 行の切れ端の削除だけ。理由 3 の 1 行目の本文は残る） | spec-ir.md | `git diff <base> -- plugins/spec-loop/references/spec-ir.md` が 1 行の置き換えで、削った文字列が切れ端だけ |
| A3 | spec-loop の版が 3 種類（marketplace.json・plugin.json・SKILL.md 7 本の 2 行）で 0.127.1 に揃う | カタログ・マニフェスト・スキル本文 | `python3 scripts/check-plugin-versions.py`・`python3 scripts/check-version-bump.py origin/main` |
| A4 | 歯止めが全部緑 | リポジトリの CI | `python3 scripts/check-all.py` と PR 側の CI |

掛け算: 受入基準を Verifier と `/code-review` の両方に、2 パス（1 パス目の指摘対応の差分が 0 行なら 1 パス）。

Issue の受入基準は「直す前は 2 行当たり」と書くが、実測では直す前の当たりは 1 行（138 行）だった——137 行は「一律の線を引くと、どちらかの仕様で誤る」で、検索の文字列（「一律の線は、」）に当たらない。受入基準の本体（直した後に切れ端の行が無い）は変わらないので、A1 は実測の 1 行で書いた。

未証明: なし。BLOCKED: なし。
生成物: なし（spec-ir.md から生成するものは無い。`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけを測る——spec-loop は対象外）。
プロパティテスト: なし（文言の削除で、入力の空間を持つ不変条件が無い）
依存の追加・更新: なし

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1328-spec-ir-stray-fragment`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1328`・起点 `ac0b3f40`・base `origin/main` = `ac0b3f40b9dd438aedfa35ab185d7e757fd2068b`
- 直す線: 既定（出所: 手順 3 の回答 2026-11-20）
- 実験なし

```dev-loop-gates
周の base: ac0b3f40b9dd438aedfa35ab185d7e757fd2068b
関門: Verifier 1 85ce52e9 反証=0
関門: /code-review 1 85ce52e9 指摘=6
関門: 2 パス目 該当なし 85ce52e9
関門: 狭いパス 該当なし
受入基準: A1 満たす
受入基準: A2 満たす
受入基準: A3 満たす
受入基準: A4 満たす
マージの反映: ドキュメントとプラグインの配布
```

- 2 パス目: 該当なし（1 パス目の指摘対応の成果物の差分 0 行。起点 `85ce52e9`。`git diff 85ce52e9 -- ':(top)' ':(top,exclude)docs/plans/issue-1328.md'` は空、`git status --porcelain` は計画ファイルだけ）
- 狭いパス: 該当なし
- 割り目: 手順 4 の割り目は訊かずに続けた（周が小さく、関門まで 1 セッションで回した）
- A4: 満たす——PR 側の CI は全部緑（8 件成功・1 件スキップ）。ローカルの test-check-pptx-render.py の実機の段の NG は main `ac0b3f40` でも同じ形で出る既存の失敗（下の「歯止め」）。利用者が判定を聞いたうえで「マージして」と指示した（2026-11-20）。
- 起票: マージの前は利用者の答えが無く起票しなかった。マージの後に利用者の指示（2026-11-20）で、残課題の 2 件を #1358・#1359 として起票した（件数は下の手順 8 の行）。

## 既知の限界・決着済みの論点

- Issue の受入基準の「直す前は 2 行当たり」は実測と食い違う（上の受入基準の注記）。採った: 実測の 1 行で書く。理由: 削るべき切れ端は 138 行の 1 つだけで、137 行は本文。

### 1 パス目の採否（Verifier 反証 0 件・/code-review 指摘 6 件）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1 spec-ir.md 131 行「理由は 3 つ」が、理由 3 が乗る割合に当たらないことと合わない（前からある） | 示せる（文面） | 無し（直すと A2 に反する） | 残課題 |
| CR2 A4 は全部緑と言うが、ローカルの test-check-pptx-render.py が落ちたまま | 示せる（main で回しても同じ NG） | A4 | 直さない——既存の失敗で、周の差分では直せない。A4 の判定は PR 側の CI の結果と並べて利用者に渡す |
| CR3 A1 の陽性対照のコマンドにリビジョンが無い | 示せる | 無し（記録） | 記録を直した（成果物の差分なし） |
| CR4 Issue の「2 行当たり」の訂正が Issue に無い | 示せる | 無し | Issue にコメントした（成果物の差分なし） |
| CR5 全体の CLAUDE.md の「調査結果を実装の前に Issue にコメント」が実装の後になった | 示せる（コメントが 0 件だった） | 無し | 実装の後にコメントした（遅れた）。PR コメントに書く |
| CR6 コミットが Refs で Fixes ではない | 示せる | 無し | PR 本文に `Fixes #1328` を書く（成果物の差分なし） |

1 パス目の指摘対応の起点: `85ce52e9`。成果物の差分は 0 行なので、2 パス目と狭いパスは「該当なし」。

## 歯止め

- `python3 scripts/check-all.py`（ac0b3f40 からの変更の上で）: 98 本中 2 本が落ちた。
  - `check-plan-counts.py`: 件数の行が無かった → 下の手順 8 に足した。
  - `test-check-pptx-render.py`: 実機の段（本物の LibreOffice・poppler）だけ NG（収まる枚 2・はみ出す枚 2。期待は 0 と 1）。単独で回し直しても同じ。
    この検査は spec-ir.md を読まず（`grep -l spec-ir` で 0 件）、周の差分はスクリプトを触らない。
    **メインの作業ツリー（main `ac0b3f40`。周の変更なし）で回しても同じ NG**（収まる枚 2・はみ出す枚 2）——既存の失敗。CI はこの段を回さない（道具が無い）。

## 手順 8

- この周の起票: 2 件（マージ後の起票: #1358 spec-ir.md の「理由は 3 つ」の食い違い・#1359 test-check-pptx-render.py の実機の段の既存の失敗。どちらも PR #1356 のコメントの残課題から、利用者の指示（2026-11-20）で起票）
