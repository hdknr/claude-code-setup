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
- `scripts/test-check-signoff.py` — `signoff-tags.md` の「比べる場所は v1〜`v<n>` の」を字句どおりに読む正規表現と変異の文字列を、新しい表記に合わせる（1 パス目の `/code-review` の指摘で広げた。手を動かす前にここへ足した。理由: 参照の文面を読む回帰テストが表記の変更で落ちる）

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
- `/tmp/i778/same_text.py [<比べる相手>]` — 比べる相手（既定 HEAD。コミット後は `9e9be07f` を渡す）の版と作業ツリーの版を両方描画し、`<…>` を除いた文字が同じか、`<…>` が増えただけ（減っていない）かを見る。版の行（0.45.1）は揃えて比べ、比べた本数を出す（0 本なら 2 で終わる。2 パス目の指摘 2-R3 で直した）。`9e9be07f` に当てて「比べた本数 12・差 0」。

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| C1 | spec-loop の Markdown を GitHub の描画に通して、原文の山括弧の置き場所が消えている箇所が 0 | 本文の散文・表のセル・太字の中・箇条書き・frontmatter の description（`/markdown` は frontmatter を本文として描く） | `render_check.py` が 0 件（直した後）。**陽性対照**: 直す前（base `9e9be07f`）で 77 件（10 ファイル） |
| C2 | 直し方はコードスパンか実体参照で、意味を変えない | コードスパンで囲んだことで太字が開け閉めできなくなる・表のセルが割れる・語の一部だけ囲んで読みが変わる | `same_text.py` で、`<…>` を除いた描画の文字が直す前と同じ、`<…>` は増えた（77）だけ。`scripts/check-bold-flanking.py` が緑 |
| C3 | spec-loop の版を 3 箇所で上げる | `marketplace.json`・`plugin.json`・各 `SKILL.md` の 2 行 | `scripts/check-plugin-versions.py`・`check-version-bump.py origin/main` が緑 |
| C4 | 他の歯止めを割らない | `handoff-issue.md` の写しを突き合わせる `test-scaffold.py`、description の共変の `check-description-sync.py`、**参照の文面を字句どおりに読むテスト**（`test-check-signoff.py`・`test-check-frozen.py`・`test-check-qa-csv.py`・`test-init-mkdocs.py`——1 パス目で広げた経路。`grep -n 'v<n' scripts/*.py` で数え直し、コードの外の `v<n>` を読むのは `test-check-signoff.py` の 2 か所だけ）など | `python3 scripts/check-all.py`（順番待ち越し）が緑、PR の CI が緑 |

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
- 1 パス目: **Verifier 反証 0 件**（`dev-loop:dev-loop-verifier`・sonnet。指示文 169 行を読ませ、報告は 170 行——末尾の改行の数え方の差）。**`/code-review`（high）指摘 4 件**——**ただし 1 パス目の `/code-review` には `prompts/review-handoff.md` を渡せていない**（`Skill` の引数に対象と base だけを渡したら、フォークした実行が引数だけで完了して戻った。受入基準を渡していない素の差分レビューである。PR コメントに申告する。2 パス目には貼って渡す）。差し戻し 1 件（手順 4 へ: `test-check-signoff.py`）。
- 割り目（手順 6・2 パス目の前）: 不在の周なので訊かない。このまま続ける。残っているもの: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方。
- 2 パス目: 対象は 1 パス目の指摘対応 `d5c3b3c1..3e2aa22d`（`scripts/test-check-signoff.py` と計画ファイル）。base は変えない（`9e9be07f`）。2 パス目の指摘対応の起点（狭いパスの起点）: `3e2aa22d`
- 2 パス目の結果: **`/code-review`（high。`prompts/review-handoff.md` を引数に貼って渡した）指摘 4 件**（2-R1〜2-R4）・**Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件**（軽い指摘 1 件＝2-R5。報告が届かず止まっていたので再開して回収した。C4 の 9 本は順番待ちで自分では完走できず、`check-all` 58/58 と PR の CI を未確認の引用として報告）。
- 2 パス目の指摘対応: 終点 `cd861efe`（計画ファイルだけ。`git diff 3e2aa22d cd861efe -- ':(top)' ':(top,exclude)docs/plans/issue-778.md'` は空）。scratchpad の `same_text.py` も直した（リポジトリの外）。
- **狭いパス: 該当なし**（2 パス目で直した行は計画ファイルと scratchpad の道具だけで、成果物の差分が 0 行）。
- 歯止め: `python3 scripts/check-all.py`（順番待ち越し）**58/58 本・失敗 0**（2-R1 を直した後）。1 回目は `test-check-signoff.py`・`check-plan-counts.py` が FAIL のまま時間切れで止まった。
- PR #780: `gh pr checks 780` **check pass・build pass・deploy skipping**（`cd861efe`）。1 パス目の指摘対応の起点: `d5c3b3c1`（実装のコミット。関門に渡した時点の HEAD）
- 交絡を潰した手順: 陽性対照（直す前の版で 77 件）。`same_text.py` は直す前と後の描画の両方を同じ道具で取り、`<…>` 以外が同じことを見る
  （増えた数 77 が直す前の消えた数 77 と一致——別の場所の `<n>` で消えた分が打ち消されて数えられていないことの確かめ）。

## 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| 1-R1 `signoff-tags.md` の表記を変えたので `test-check-signoff.py` が落ちる（753 行の正規表現・770 行の変異） | 示せる——`python3 scripts/test-check-signoff.py` が 2 件失敗（直す前）・`check-all.py` でも FAIL | C4 | 直す（`scripts/test-check-signoff.py` を新しい表記に合わせた。直した後 `OK: 試料 75 件・変異 68 件`） |
| 1-R2 実装のコミットを `check-all.py` が緑になる前に関門に渡した | 示せる（1-R1 と同じ失敗） | C4（1-R1 と同じ原因） | 直す（1-R1 を直し、`check-all.py` を回し直す。周の記録の指摘でもある） |
| 1-R3 変更範囲に `test-check-signoff.py` が無い | 示せる（直すには範囲の外のファイルが要る） | C4 | 直す（変更範囲に足した） |
| 1-R4 `v1〜`v<n>`` で範囲の後ろの端だけコードスパン（`qa-csv.md`・`signoff-tags.md`・`tree.md`） | 示せない（描画は正しく `v1〜v<n>` と読める。字句を読む道具が壊れる実物は 1-R1 で、直した） | 無し | 残課題（言い回し。PR コメントに記録） |

| 2-R1 計画ファイルに件数の行（`- この周の起票: N 件`）が無く `check-plan-counts.py` が赤 | 示せる——`python3 scripts/check-plan-counts.py` が `件数の行…が無い` で 1 | C4 | 直す（下の「手順 8」に件数の行を置いた。計画ファイルだけの修正） |
| 2-R2 この差分で `check-all.py` が最後まで回った記録が無い（1 回目は時間切れで止まり、2 回目は順番待ち） | 示せる（`/tmp/i778/checkall-1.txt` に集計行が無い） | C4 | 直す（2-R1 を直してから回し直し、集計行を下の再開点に書く） |
| 2-R3 `same_text.py` は HEAD と比べるので、コミット後は 0 本を比べて `差 0` を出す。base と比べると版の行で `SKILL.md` 5 本が違う | 示せる（`差 0` を 0 本で出す） | 無し（C2 自体は成り立つ——1 パス目の Verifier と 2 パス目の `/code-review` がそれぞれ base 固定・版の行を揃えて確かめた） | 直す（scratchpad の道具だけ。比べる相手を引数で取り、比べた本数を出し、版の行を揃える。リポジトリの差分は無い） |
| 2-R5（Verifier 2 パス目・軽い指摘）C4 の経路の記述が狭い——参照の文面を `v<n>` つきで字句どおりに読むテストは `test-check-frozen`・`test-check-qa-csv`・`test-init-mkdocs`・`test-scaffold` にもある | 示せない（どれもコードスパンの中の `v<n>` を読み、この周はそこを変えていない。`test-check-frozen`・`test-diff-versions` は Verifier が、全部は `check-all` 58/58 が緑） | 無し | 残課題（計画の記述。経路は C4 の表に既に名指ししてある） |
| 2-R4 `render_check.py` は原文からコメントを除いて数えるので、コードスパンの中のコメントや実体参照で描画の数が増えると、本当に消えた分を打ち消して数え損ねうる | 示せない（いまの 22 本でそうなる形は無い——打ち消しうる語は非 ASCII かコメント全体で、`v<n>` 類と重ならない） | 無し | 残課題（試料の穴・実際の利用でまず起きない形。PR コメントに記録） |

## 手順 8（経験の還元・起票）

- この周の起票: 0 件（周の途中の課題は「外に出す」の線と利用者の方針 2026-11-01 に従い、残課題は PR コメントに記録するだけ。起票の候補なし）
- 焼き戻す学びなし（リポジトリの規約への焼き戻しは無い。参照の文面を字句どおりに読むテストがあることは CLAUDE.md の各テストの説明に既にある）。
