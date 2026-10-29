# Issue #525 — dev-loop: 太字の flanking の崩れを CI で捕まえるか（#519 の残課題・利用者の判断）

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-10-29）の周。**不在の周**である——訊く場面は
  `references/absent-lines.md` の「訊く場面」のとおり訊かずに進める（`AskUserQuestion` は使わない）。
- 元の課題: #519 の `/code-review` 1 パス目（CR1-7）。本文の印は `<!-- cruise-found: #474 -->`。元の周の PR は #526。
- 使った線（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋利用者の確認（再開時・2026-10-28T07:24:46Z）。親から受けた指示で確かめた）:
  `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`周の途中の課題 = 台帳に足して直す`。
- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-474`））。
- **利用者の直接の指示（2026-10-29）**: 「525も推奨で進めて要確認課題をたててください。同様な他の課題も同じ方針で」——人間の判断が要る行は
  推奨で決め、要確認の Issue を立てる（#537・#510 と同じ形）。**#525 の決定は既に推奨で決めて #537 に記録してある**（下の「決めた値」）。
- 親の指示（この周に固有）: `EnterWorktree` を呼ばず、worktree の絶対パスを cwd にして作業する。**マージしない**——PR・PR 側の CI・
  2 つの関門の 2 パス・手順 8 の計画ファイルまで。台帳は書かない（周の途中の課題は親に報告する）。

## 決めた値（#537。推奨で決めた——この周では決め直さない）

- **検査を足す。** `scripts/` に標準ライブラリだけで動く検査を置き、`scripts/check-all.py` と CI（`.github/workflows/plugins.yml`）に載せる。
- **対象は `plugins/` の Markdown**（`docs/` は後から広げられる）。
- **免除は行ごとに印で名指しする**（`dup-counts-ok:` と同じ形）——`bold-flanking-ok: <理由>` を崩れのある行に書く。
- **コードフェンスとコードスパンの中は見ない**（`scripts/markdown_fences.py` を使う）。
- 慣例に従う: 回帰テスト `scripts/test-check-bold-flanking.py`（変異テストを含む）、docstring に「何を守り、何を守らないか」、`CLAUDE.md` の一覧に足す。
- **検査が見つけた `plugins/` の既存の崩れは直す**（免除するなら理由つき）——CI を緑にするため。プラグインの中身を触るので版を 3 種類で上げる。

## 失敗（実物）

#519 の後の main（`58a12cd`）で、`plugins/` の Markdown 43 本を GitHub の Markdown API（`gh api -X POST /markdown`、`mode=gfm`）で描き、
`<pre>`・`<code …>` を除いた本文に `**` が字のまま残るファイルを数えると **7 本**（spec-loop の `agents/` 3 本・`README.md`・
`references/tree.md`・`skills/scaffold/SKILL.md`・`skills/spec-review/SKILL.md`）。**いまの CI はどれも捕まえない。**

## 変更範囲

触る:

- `scripts/check-bold-flanking.py` — 新しい検査（本体）
- `scripts/test-check-bold-flanking.py` — その回帰テスト（変異テストを含む）
- `scripts/check-all.py` — `GUARDS` と `TESTS` に登録
- `scripts/test-check-all.py` — 収録漏れの検査が新しい検査の登録を要求する場合だけ（変異の主張など）
- `.github/workflows/plugins.yml` — 本体とテストのステップ
- `CLAUDE.md` — `scripts/` の一覧に 2 行
- `plugins/spec-loop/agents/domain-checker.md` — 既存の崩れ（`**` の外側に空白を足す。文言は変えない）
- `plugins/spec-loop/agents/formal-checker.md` — 同上
- `plugins/spec-loop/agents/red-team.md` — 同上
- `plugins/spec-loop/README.md` — 同上
- `plugins/spec-loop/references/tree.md` — 同上
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 同上と版の 2 行
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 同上と版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（0.36.0 → 0.36.1。patch——記述の修正）
- `plugins/spec-loop/.claude-plugin/plugin.json` — `version`
- `.claude-plugin/marketplace.json` — spec-loop の `version`
- `docs/plans/issue-525.md` — この計画ファイル

触らない:

- `docs/`・`CLAUDE.md` の本文の太字（#537 で対象外。`CLAUDE.md` には一覧の 2 行だけ足す）
- `scripts/markdown_fences.py`（使うだけ。式を変えない）
- `scripts/check-skill-pointers.py`（並行する #503 の周が触る）・ほかの周（#498・#502）のファイル
- spec-loop・dev-loop の文言・規範（空白のほかは 1 字も変えない）

## 複製の数

- 「何を守り、何を守らないか」は本体の docstring の 1 箇所。`CLAUDE.md` の一覧は「docstring を正とする」と指すだけ（列挙を持たない）。
- 登録は 3 箇所（`check-all.py`・`plugins.yml` の本体とテスト・`CLAUDE.md`）——どれも慣例の場所で、`test-check-all.py` が収録漏れを見る。
- 既存の崩れは 7 ファイル・22 個の `**`——同じ規範の複製ではなく、同じ記法の誤りが独立に並ぶ。直し方は 1 種類（空白を足す）なので分けない。
- 版は 3 種類（`marketplace.json`・`plugin.json`・spec-loop の `SKILL.md` 5 本の 2 行）。

## デプロイ経路

main へのマージ → GitHub Pages の再ビルド（`plugins/` のファイルはサイトに取り込まれない）と、プラグインの配布（カタログと symlink 経路）。
**マージはこの周ではしない**（親の指示）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| B1 | `plugins/` の Markdown で、CommonMark（cmark-gfm）が太字に組まない `**` があれば、検査が非ゼロで落ち、ファイル・行を名指しする | 開きの `**` の前が文字・後ろが句読点（`X**「`）／閉じの前が句読点・後ろが文字（`」**Y`）／後ろ・前が空白／対にならない `**`／行をまたぐ太字／`***`（太字の斜体） | 回帰テストの試料（各形）と、**陽性対照**: 歴史的な base（#519 の前 `7d950d1`・#523 の前）の `plugins/` に当てて、GitHub の描画で崩れていたファイルを名指しする |
| B2 | 崩れていない太字では落ちない（誤検出しない） | 句読点の両側・空白の外側・行をまたぐ太字・コードスパンの隣・表のセル・リストの項・引用 | 変更後の main 相当の `plugins/` 43 本で 0 件。**GitHub の描画と突き合わせる**——`<strong>` の数が検査の組の数と全ファイルで一致する |
| B3 | コードフェンス・コードスパンの中の `**` は見ない | フェンス（``` と ~~~、長いフェンス）／コードスパン（1 連・2 連のバッククォート）／frontmatter | 回帰テストの試料 |
| B4 | 免除は行ごとに印で名指しした行だけに効く。理由の無い印・コードの中の印は効かない。崩れの無い行に残った印は落とす | 印の範囲がファイル全体に広がる／空の印／フェンス・コードスパンの中の例／直したあとに残った印 | 回帰テストの試料 |
| B5 | `scripts/check-all.py` と CI（`plugins.yml`）が本体とテストを回す | 登録漏れ・コメントアウト | `python3 scripts/test-check-all.py`（収録漏れの検査）と、push 後の `gh pr checks` に新しいステップが出ること |
| B6 | 回帰テストが本体の「守る」の各行に 1 つずつ変異を当て、全部殺す | 変異が届いていない（等価変異） | `python3 scripts/test-check-bold-flanking.py`。「守る」の行数と変異の数が 1 対 1 かをテスト自身が数える |
| B7 | 既存の崩れ 7 ファイルを直し、文言は変えない（`**` の外側に空白を足すだけ） | 編集の取り違え | `git diff -w <base> -- plugins/` に版の行のほか差分が無い。直した後に GitHub の描画で `**` が字のまま残るファイル 0、`<strong>` が直した数だけ増える |
| B8 | 版が 3 種類（`marketplace.json`・`plugin.json`・spec-loop の `SKILL.md` 5 本の 2 行）で 0.36.1 に揃う | 上げ忘れ・片側だけ | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| B9 | 標準ライブラリだけで動く（CI は 3.12、手元は 3.14） | 外部依存の import | import の一覧を見る。`python3.12` があればそれでもテストを回す |
| B10 | 歯止めが全部緑 | どれか | `python3 scripts/check-all.py` と、push 後の `gh pr checks` |
| B11 | 生成物の鮮度——spec-loop の `SKILL.md` は §8.2 の生成ブロックの対象外（`skill-metrics.py` は dev-loop を測る）。図は触らないので該当なし | — | `python3 scripts/skill-metrics.py --check`（check-all の中でも回る） |

組み合わせ（必須要件の掛け算）: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

**未証明**: 無し（描画は GitHub の API で実際に描いて突き合わせられる）。
**BLOCKED**: 無し。
**実験**: 検査と GitHub の描画の突き合わせ。交絡の候補——(1)「描画で崩れていても検査が黙る（検査が何も見ていない）」→ 歴史的な base で
既知の崩れを名指しすること（陽性対照）で潰す。(2)「検査が黙るのは崩れが無いからではなく、組み方の推測が描画と偶然一致しているだけ」→
`<strong>` の数と検査の組の数を全ファイルで突き合わせる（数が一致しても範囲までは見ていない——範囲の一致は試料のテストで見る）。

## 未解決・確認待ち

無し（決めるべき値は #537 で推奨で決めてある）。

## 起票

- この周の起票: 0 件（#537 は親（cruise）が利用者の指示でこの周より前に立てた確認の Issue で、この周の起票ではない。起票の承認は不在のため訊いていない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/525-bold-flanking-check`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-525`、
  起点 `58a12cd`、base の参照 `origin/main`、base の SHA `58a12cd13b59058a5c439ed2f89ce5f5e0eb9851`
  （`EnterWorktree` は使わず、`cd <worktree> && …` と絶対パスで作業している——親の指示）
- 手順 4 の割り目: 不在のため訊かず続けた
- 1 パス目の指摘対応の起点の SHA: （1 パス目の関門に渡すときに書く）
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 手順 4 への差し戻し: 無し
- 交絡を潰した手順: （下の「測定」）

## 測定

- 変更前（`58a12cd`）の `plugins/` 43 本: 検査は 7 ファイル・22 件を名指し。GitHub の描画で `**` が字のまま残るファイルはちょうど同じ 7 本（他の 36 本は 0）。
  崩れの無い 36 本では `<strong>` の数が検査の組の数と全部一致し、崩れた 7 本では `<strong>` が組の数より少ない（不足 1・4・4・4・1・1・1）。
- **実装中に見つけて直した見落とし**: 最初の版はコードスパンをファイル全体で組んでいた。#519 の前（`7d950d1`）の `plugins/` に当てたら、dev-loop の `SKILL.md` で
  名指しが 2 件しか出なかった（#519 は同じファイルで 26 行を直している）——301 行の入れ子のバッククォート（#522）が閉じないスパンを作り、135 行を飲んでいた。
  段落ごとに組むように直し（docstring の「守る」の最後の行）、その形を試料 `span-per-block.md` と変異に入れた。
- **陽性対照（歴史的な base）**——直した版を当てると:
    - `7d950d1`（#519 の前）: #519 が直した行（版の行を除く）を**全部**名指しする（`SKILL.md` 24 行・`README.md`・`agents/dev-loop-verifier.md`・`prompts/verifier.md`・`references/resume.md`）。
      ほかに名指しした行は、後の #523（`SKILL.md` 823・`agents/dev-loop-verifier.md` 84–85・`prompts/verifier.md` 105・`prompts/review-handoff.md` 89）と #524（`references/stacked.md` 147）が直した行だけ。
    - `107e557`（#523 の前）: #523 が直した行（版の行を除く）を全部名指しする——**`*` を残さずに誤って組む形も捕まえる**。
    - `94bcd42`（#524 の後）: dev-loop は 0 件、spec-loop の 7 本だけ（この周が直す）。
- 変更後: 検査は 0 件。43 本を GitHub で描き直すと、`**` が字のまま残るファイル 0、`<strong>` の数と検査の組の数が 43 本すべてで一致。
  直した 7 本の `<strong>` は 42→46・55→59・45→49・25→26・105→106・69→70・180→181（不足の分だけ増えた）。`git diff -w 58a12cd -- plugins/` は版の行だけ。
- 試料の描画: `これは**`code`**です。`（崩れる）・`\**`（字のまま）・`***…*…**`（太字の斜体）・段落をまたぐ閉じ忘れ・行をまたぐ太字・`**→矢印**`（崩れない）を GitHub で描いて、検査の判定と一致することを確かめた。

## 既知の限界・決着済みの論点

- 論点: 対象を `docs/` にも広げるか。決着: 広げない。理由: #537 で `plugins/` に決めた（推奨で決めた値。この周では決め直さない）。
- 論点: 句読点の定義を CommonMark 0.31（一般カテゴリ P と S）にするか、cmark-gfm（ASCII の記号と P）にするか。決着: cmark-gfm。理由: 本文を描くのは GitHub で、
  #519 までの周も GitHub の API（gfm）で崩れを確かめてきた。S の記号（`→` など）の扱いが新しい版の描画器とずれうることは docstring の「守らない」に書いた。
- 論点: 組み方を「段落の中で前から順に 2 つずつ」と推測する。決着: 採った。理由: 著者は太字を対で書く。CommonMark の組み方を全部真似ると、意図と描画の
  ずれ（検査したいもの）が見えなくなる。`__`・斜体・4 つ以上の `*` が混ざる段落はずれうる（docstring の「守らない」）。
