# Issue #522 — dev-loop: SKILL.md 301 行の入れ子のバッククォートで、コードスパンが崩れて描かれる（#519 の残課題）

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-10-28）の周。**不在の周**である——訊く場面は
  `references/absent-lines.md` の「訊く場面」のとおり訊かずに進める。
- 元の課題: #519 の著者の走査（`docs/plans/issue-519.md` の `触らない:`）。本文の印は `<!-- cruise-found: #474 -->`。元の周の PR は #526。
- 使った線（出所: cruise の確かめた線（台帳 `issue-474`）。親から受けた指示で確かめた）:
  `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`周の途中の課題 = 台帳に足して直す`。
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-474`））。
- 親の指示（この周に固有）: **文言は変えず、バッククォートの数・空白だけで直す**。版は dev-loop を 1.63.5 に上げる
  （並行する #524 の周が 1.63.6 に上げる。こちらが先にマージされる）。
- 新規の周と判定した根拠: `find-cycle.py 522` は終了コード 1 だが、当たったのは経路 2（worktree の全件表示。番号で絞っていない）と
  経路 5 のコミット 2 件（`107e557`・`a70ff7d`——どちらも #519 の周のコミットで、#522 を起票先として名指ししているだけ）で、
  計画ファイル・ブランチ・計画ファイルを足したコミットは 0 件。

## 失敗（実物）

`plugins/dev-loop/skills/dev-loop/SKILL.md` 301 行（base `a0ea899`）:

```text
          **同じ行の残りは説明として自由に書いてよい**（`- \`scripts/*.py\` — 歯止め`）。
```

ファイル全体を GitHub の Markdown API（`gh api -X POST /markdown -f mode=gfm`）で描くと（著者が実走）:

```text
<strong>同じ行の残りは説明として自由に書いてよい</strong>（<code class="notranslate">- \</code>scripts/*.py` — 歯止め`）。</li>
```

GFM はコードスパンの中でバックスラッシュのエスケープを効かせないので、コードは `- \` で閉じ、残りのバッククォートが字のまま出る。

## 直し方

2 連のバッククォートで囲み、中のバックスラッシュを外す: ```` ``- `scripts/*.py` — 歯止め`` ````。
内容は `-` で始まり `歯止め` で終わる（どちらもバッククォートではない）ので、内側に空白の詰め物は要らない。
**外すバックスラッシュは、エスケープのつもりで置いた記法の一部で、意図した文言（描かれるコード）には含まれない**——
描かれる文言は `- `scripts/*.py` — 歯止め` のまま変わらない（下の A1）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 301 行のコードスパンの記法と、版の 2 行（1.63.4 → 1.63.5）
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — `version`
- `.claude-plugin/marketplace.json` — dev-loop の `version`
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`scripts/skill-metrics.py` が書き直す場合だけ。手で書かない。実際は「変更なし」）
- `docs/plans/issue-522.md` — この計画ファイル

触らない:

- `references/stacked.md` の太字の入れ子（#524）——親の指示でこの周の外
- dev-loop の文言・規範（描かれる文言は 1 字も変えない）
- 他のプラグイン・`scripts/`。`evals/resume-no-new-worktree/scaffold.sh` と `prepare-worktree.sh` の `\``（シェルのエスケープで、Markdown ではない）

## 複製の数

この記法の誤りは 1 箇所（`git grep '\\`' -- plugins/` で、Markdown のコードスパンの中にエスケープしたバッククォートを置いた形は
`SKILL.md` 301 行だけ。残りはシェルのエスケープと、単独の `` `\` ``）。同じ規範（計画ファイルの `触る:` の書式）を述べる他の箇所は
`scripts/check-plan-scope.py` の docstring にあるが、記法は崩れておらず触らない。分ける理由が無い（1 箇所）。

## デプロイ経路

main へのマージ → プラグインの配布（`marketplace.json` のカタログと symlink 経路）と GitHub Pages の再ビルド（plugins/ のファイルはサイトに取り込まれない）。
マージはこの周ではしない（親がする）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 301 行の意図した文言 `- `scripts/*.py` — 歯止め` が、ちょうど 1 つの `<code>` として描かれ、バッククォートやバックスラッシュが字のまま残らない | GitHub の描画（cmark-gfm）のコードスパンの規則 | ファイル全体を gfm で描き、該当行が `<code class="notranslate">- `scripts/*.py` — 歯止め</code>` になること。**陽性対照**: base `a0ea899` の同じファイルを同じ API で描くと `<code class="notranslate">- \</code>scripts/*.py` — 歯止め`` に崩れる |
| A2 | 他の描画が変わらない——ファイル全体の描画 HTML の差分が、版の行と 301 行の 2 行だけ | 編集が別の行に及ぶ・バッククォートの数が周りのコードスパンと組み違う | base と変更後のファイル全体を同じセッションで描いて `diff`。base を 2 回描いてバイト一致すること（描画が安定している対照） |
| A3 | 描かれる文言は変わらない——ソースの差分は 301 行のバッククォート・バックスラッシュと版の行だけ | 編集の取り違え | `git diff <base> -- plugins/dev-loop/ .claude-plugin/` を読む。A1 の `<code>` の中身が原文の意図（`- `scripts/*.py` — 歯止め`）と同じ |
| A4 | 版が 3 種類（`marketplace.json`・`plugin.json`・dev-loop の `SKILL.md` 2 本の 2 行）で 1.63.5 に揃う | 版の上げ忘れ・片側だけ | `python3 scripts/check-plugin-versions.py`・`check-version-bump.py origin/main` |
| A5 | 歯止めが全部緑 | どれか | `python3 scripts/check-all.py --jobs 2` と、push 後の `gh pr checks` |
| A6 | 生成物の鮮度——`SKILL.md` を触るので §8.2 の生成ブロックが該当。図は触らないので該当なし | 版の行・記法の変更で測定値が動く | `python3 scripts/skill-metrics.py --check` が 0（check-all の中でも回る）。書き直しを走らせた結果は「変更なし」 |

組み合わせ（必須要件の掛け算）: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

**未証明**: 無し（描画は GitHub の API で実際に描いて確かめられる）。
**BLOCKED**: 無し。
**実験**: 描画の観測。交絡の候補——(1)「API がいつでも同じ HTML を返す／描画が揺れる」→ base を 2 回描いてバイト一致し、
base と変更後で 301 行が違う描画になる（陽性対照）ことで潰す。(2)「単独の行を描くと字下げでコードブロックになり、見たいものが見えない」
→ 行だけでなくファイル全体を描いて、リストの中の該当行を見る（実際、行だけ描くと `<pre>` になった）。
(3)「GitHub の API と別の描画器（MkDocs の Python-Markdown）で結果が違う」→ `plugins/` のファイルはサイトに取り込まれないので、
読者が見る描画は GitHub のものだけ（受入基準の外）。

## 未解決・確認待ち

無し。

## 起票

- この周の起票: 0 件

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/522-nested-backtick-codespan`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-522`、
  起点 `a0ea899`、base の参照 `origin/main`、base の SHA `a0ea8994c0e0e209a56f3e1de61d3bda497346bf`
  （`EnterWorktree` は使わず、`git -C <worktree>` と絶対パスで作業している——親の指示）
- 手順 4 の割り目: 不在のため訊かず続けた
- 交絡を潰した手順: base を 2 回描いてバイト一致（`cmp`）、base と変更後のファイル全体を同じセッションで描いた `diff` が 2 行（版・301 行）だけ

## 既知の限界・決着済みの論点

- 論点: バックスラッシュを外すのは「バッククォートの数・空白だけ」を越えるか。決着: 越えない（外す）。理由: バックスラッシュは
  エスケープのつもりの記法で、GFM のコードスパンでは効かず字として出ているだけ。意図した文言（描かれるコード）には含まれず、
  外さなければ 2 連で囲んでも `\` が字のまま出る。
- 論点: Issue の例（```` `` - `scripts/*.py` — 歯止め `` ````、内側に空白）と違い、詰め物の空白を入れない。決着: 入れない。
  理由: 内容の両端がバッククォートではないので詰め物は要らず、描画は同じ（両端の空白 1 つずつは剥がされる）。
