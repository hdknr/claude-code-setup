# Issue #270 — サインオフのタグを `signoff/v<n>/req-<k>` に変え、素の `v<n>` タグとの衝突を無くす

## 決定

タグの命名を **`signoff/v<n>/req-<k>`・`signoff/v<n>/budget-<k>`** にする（2026-10-20、`AskUserQuestion` で人間が選択。
#260 の `v<n>/req-signoff-<k>` を置き換える）。候補は他に「平らな `v<n>-req-signoff-<k>`」「命名は変えず制約を文書に書く」。
**残る衝突は素の `signoff` タグだけ**で、それは `signoff-tags.md` に書く。**#260 の名前は読まない**（移行の互換は持たない）。

## 変更範囲

触る:

- `plugins/spec-loop/references/signoff-tags.md` — 命名の原本
- `plugins/spec-loop/references/versions.md` — 提案書の比較の節・「移し方」の手順 4
- `plugins/spec-loop/scripts/check-signoff.py` — 定数・パターン・メッセージ・docstring
- `plugins/spec-loop/scripts/build-proposal.py` — docstring
- `plugins/spec-loop/skills/proposal/SKILL.md` — 本文のタグ名と版
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 本文のタグ名と版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（残り 3 つ）
- `plugins/spec-loop/README.md`
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/index.md` — 公開ページの spec-loop の節
- `CLAUDE.md` — `check-signoff.py` の項のタグ名
- `scripts/test-check-signoff.py` — 試料のタグ名・定数の突き合わせ・衝突の回帰
- `scripts/test-build-proposal.py` — 試料のタグ名
- `docs/plans/issue-270.md`

触らない: `docs/plans/issue-218.md`・`docs/plans/issue-262.md`（過去の周の記録）。proposal の frontmatter の
「（req-signoff）」「（budget-signoff）」——タグ名ではなく承認の呼び名なので据え置き、JSON の description も変えない。

同じことを述べている箇所の数: タグの書式を述べる箇所が **11 ファイル**（原本 1・写しの定数 1・docstring 2・
スキル 2・README・公開ページ・`versions.md`・`CLAUDE.md`・テスト 2）。**分けない理由**: 命名を変えるのは一度に全部変えないと
本体とテストと文書が食い違う（中間の状態に意味が無い）。原本は `signoff-tags.md` で、定数の写しは
`test-check-signoff.py` が突き合わせる。

## 乗るデプロイ経路

main への merge → GitHub Pages の自動デプロイ（`docs/plugins/index.md`）。プラグインは版の bump（0.11.1 → **0.12.0**。
旧い名前を読まなくなる＝既存の使い方が壊れるが 1.0 前なので minor）で利用者に届く。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| A | 素の `v<n>` タグがあるリポジトリでもサインオフのタグを作れ、照合が 0 を返せる（Issue の再現が通る） | 正本リポジトリに `v1` タグがある状態での `git tag`・`check-signoff.py`・`build-proposal.py` | テストに試料「素の `v1` タグと共存」を足し 0 を見る。**逆順（サインオフが先・`v1` が後）も** git で作れることを試料で見る |
| B | 照合が数えるのは `signoff/v<n>/(req|budget)-<k>` だけ——#260 の `v<n>/req-signoff-<k>`・それ以前の `req-signoff-v<n>`・命名に合わない形（`-fix`・`-03`・`v01`）を数えない | `latest` の選び方・`--req`/`--budget` の指定 | テストの「命名に合わない」試料に #260 の名前を足す。パターンから `signoff/` を外す変異で赤 |
| C | 本体の定数（根 `signoff`・`req`・`budget`）が `signoff-tags.md` の表と一致する | 写しのずれ | `test-check-signoff.py` の突き合わせに根を足し、表の根を崩す変異で不一致 |
| D | 旧い書式（`v<n>/req-signoff`・`v<n>/budget-signoff`・`v1/req-signoff-1`）が、過去の記録（`docs/plans/issue-218/262`）と「読まない」と述べる箇所以外に残らない | 11 ファイル・指示語や表の列見出し・メッセージ文字列 | `grep -rn 'req-signoff\|budget-signoff'` を当て、残りを 1 件ずつ説明する |
| E | `signoff-tags.md` が残る衝突（素の `signoff` タグ）と、#260 の名前を読まないこと・取り直すことを述べる。`versions.md` の「移し方」が新しい名前を案内する | 原本・`versions.md` | 読む |
| F | 版が 3 種類（`marketplace.json`・`plugin.json`・5 つの `SKILL.md` の 2 行）で 0.12.0 にそろう | `check-plugin-versions.py`・`check-version-bump.py` | `check-all.py` |
| G | 歯止めと回帰テストが全部緑 | `python3 scripts/check-all.py` | 集計行 |

証明できないもの（未証明）: なし（git の ref の衝突は一時リポジトリで再現できる）。BLOCKED: なし。
生成物の該当判定: **生成物なし**——触る `SKILL.md` は設計 §8.2 の測定（`skill-metrics.py`）の対象が dev-loop だけなので該当しない
（`check-all.py` の `skill-metrics.py --check` で確かめる）。図も触らない。
必須要件の掛け算: 受入基準を Verifier × 1・2 パス目、`/code-review` × 1・2 パス目の 4 つの受け渡しに渡す。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/270-signoff-tag-prefix`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-270`、起点 `2b61f0b`、
  base 参照 `origin/main` → `2b61f0bd945f1cae3c250adca5b3950e6dedd996`
- 読み込まれている dev-loop の版: 1.37.0（リポジトリは 1.41.1）
- 実装: `8d30068` で完了。`test-check-signoff.py` 試料 43・変異 30 緑、`test-build-proposal.py` 試料 35・変異 30 緑、
  `check-all.py` 44/44 本・失敗 0・飛ばし 0（コミット直前の作業ツリー）
- 手順 4 の割り目で `AskUserQuestion` → **「ここで割る」**を選択（2026-10-20）
- 関門 1 パス目: 未（次はここ。base `2b61f0bd945f1cae3c250adca5b3950e6dedd996` を Verifier と `/code-review` の両方に渡す）
- 反証・差し戻し: なし
- 交絡: 試料は陽性側（素の `v1` と共存して 0）を足した。**旧い名前で同じ試料が作れないこと（陰性側）は未確認**——Verifier に当てさせる

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 命名 | `signoff/v<n>/<種類>-<k>` を採った | 人間が選択（上の「決定」） |
| 素の `signoff` タグとの衝突 | 残す（文書で述べる） | 階層を持つ名前は根と同名のタグと必ず衝突する。根を `signoff` にしたのは人間の選択 |
| #260 の名前の互換 | 持たない（読まない・取り直す） | 旧い名前は `v<n>` タグのあるリポジトリでは作れなかったうえ、#262 と同じく取り直しで足りる |
| proposal の frontmatter の「req-signoff」 | 据え置き | タグ名ではなく承認の呼び名。変えると JSON の description との共変も要る |
