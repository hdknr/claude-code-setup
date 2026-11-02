# Issue #778 — spec-loop: コードスパンの外の `v<n>`・`v<n-1>` が GitHub の描画で消える

spec-loop の Markdown で、コードスパンの外に書いた `v<n>`・`v<n-1>` の山括弧の置き場所が、GitHub の描画で生の HTML のタグとして除かれる。
コードスパンで囲んで直す。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の起動（2026-10-27）。親から `claude -p` の子プロセスとして委ねられた（#491 の C1 の観測を兼ねる）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・`周の途中の課題 = 外に出す`
（出所: 利用者の確認（起動時 2026-10-27・再開時 2026-10-28／2026-11-01））。周の途中の課題は PR のコメントに記録するだけで起票しない（利用者の方針 2026-11-01）。
台帳は書かない（親が書く）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））。
版の上げ方: `spec-loop` を **patch**（記述の修正）。main の先端 0.45.0 → **0.45.1**（マージの直前に main が進んでいたら、取り込む直前の origin/main の先端より上に patch で上げ直す）。

重い検査（`check-all.py`）は順番待ち越しに走らせる（`references/parallel.md`）。読み込んだ dev-loop（キャッシュの 1.63.6）の base ディレクトリに
`../cruise/scripts/run-serial.py` が無いので、`/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` を使う（親の指示）。

## 変更範囲

触る:

- `plugins/spec-loop/README.md` — コードスパンで囲む
- `plugins/spec-loop/references/*.md` — 同（`handoff-issue.md`・`qa-csv.md`・`signoff-tags.md`・`spec-ir.md`・`tree.md`・`versions.md`）
- `plugins/spec-loop/skills/*/SKILL.md` — 同（`proposal`・`scaffold` は frontmatter の description も）と版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-778.md` — この計画ファイル

触らない:

- dev-loop など他のプラグインの同じ形（Issue の範囲の外。見つけたら PR のコメントに記録だけ）
- CI で捕まえる検査を足すこと（Issue の範囲の外）
- `plugin.json`・`marketplace.json` の description（Markdown として描画されない。frontmatter だけ直すので、コミットに `Skip-description-sync:` を書く）

### 同じことを述べている箇所の数

規範は変えない（記述の表記だけ）。直す箇所は 10 ファイル・58 行・77 個の山括弧の置き場所（描画の突き合わせの数）。どれも独立した表記の誤りで、
互いの整合を取り直す必要は無い。

## 乗るデプロイ経路

main へのマージでプラグインの配布（spec-loop 0.45.1）。公開サイトは `docs/` を触らない（計画ファイルを除く）ので反映経路なし。マージは親がする。

## verify の受入基準

突き合わせの道具（scratchpad。リポジトリには入れない——Issue の範囲の外）:

- `/tmp/i778/render_check.py <ルート>` — `plugins/spec-loop/**/*.md` を 1 本ずつ `gh api -X POST /markdown`（`mode: gfm`）に通し、
  原文（HTML コメントを除く）の `<…>`（改行を含まない、`<http…>` を除く）の数と、描画の HTML の文字（実体参照を戻した）の中の数を語ごとに比べ、
  描画のほうが少ない分を「消えた」と数える。
- `/tmp/i778/same_text.py` — HEAD の版と作業ツリーの版を両方描画し、`<…>` を除いた文字が同じか、`<…>` が増えただけ（減っていない）かを見る。

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| C1 | spec-loop の Markdown を GitHub の描画に通して、原文の山括弧の置き場所が消えている箇所が 0 | 本文の散文・表のセル・太字の中・箇条書き・frontmatter の description（`/markdown` は frontmatter を本文として描く） | `render_check.py` が 0 件（直した後）。**陽性対照**: 直す前（base `9e9be07f`）で 77 件（10 ファイル） |
| C2 | 直し方はコードスパンか実体参照で、意味を変えない | コードスパンで囲んだことで太字が開け閉めできなくなる・表のセルが割れる・語の一部だけ囲んで読みが変わる | `same_text.py` で、`<…>` を除いた描画の文字が直す前と同じ、`<…>` は増えた（77）だけ。`scripts/check-bold-flanking.py` が緑 |
| C3 | spec-loop の版を 3 箇所で上げる | `marketplace.json`・`plugin.json`・各 `SKILL.md` の 2 行 | `scripts/check-plugin-versions.py`・`check-version-bump.py origin/main` が緑 |
| C4 | 他の歯止めを割らない | `handoff-issue.md` の写しを突き合わせる `test-scaffold.py`、description の共変の `check-description-sync.py` など | `python3 scripts/check-all.py`（順番待ち越し）が緑、PR の CI が緑 |

必須要件の掛け算: 受入基準を Verifier・`/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

### 未証明

- **GitHub のファイル表示（blob の画面）で frontmatter がどう描かれるか**は見ていない（`/markdown` の API は frontmatter を本文として描くので、受入基準の測り方に従って直した）。
- 描画の API は時点の GitHub のもの。将来の描画の変更は見られない。

### 生成物

該当の判定: `SKILL.md` の測定値（`skill-metrics.py`）は dev-loop の `SKILL.md` だけを測るので該当しない。図の書き出しも触らない。**生成物なし**。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/778-spec-loop-angle-placeholders`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-778`・
  起点 `9e9be07f`（origin/main。`prepare-worktree.sh` の出力）・base: 参照 `origin/main` → `9e9be07f734c5323a6054330d3c122b910484f31`
- 割り目（手順 4）: 不在の周なので訊かない。このまま続ける。
- 1 パス目: 未着手
- 交絡を潰した手順: 陽性対照（直す前の版で 77 件）。`same_text.py` は直す前と後の描画の両方を同じ道具で取り、`<…>` 以外が同じことを見る
  （増えた数 77 が直す前の消えた数 77 と一致——別の場所の `<n>` で消えた分が打ち消されて数えられていないことの確かめ）。

## 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| （まだ無い） | | | |
