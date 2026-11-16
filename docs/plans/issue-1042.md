# Issue #1042 — spec-loop req-loop: 初回ヒアリングと、レビュー会で決めたい問の優先

利用者が居る周（`/dev-loop:dev-loop 1042` を利用者が起動）。#1042 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。

**範囲は利用者が決めた**（手順 1 の後の `AskUserQuestion`、2026-11-16）: 提案 1（初回ヒアリング）と提案 2（質問の量を抑える）を、**Q&A 表の列を足さずに**入れる。
提案 3（判断の理由を書いてもらう欄）は列としては入れず、初回ヒアリングで判断の基準・優先順位を自由回答で聞くことで趣旨を拾う。

直す線: `既定`（出所: 手順 3 の回答。`.claude/dev-loop.md` に `直す線:` の行が無いため `AskUserQuestion` で訊いた。2026-11-16）。

依存の追加・更新: なし

## 変更範囲

触る:

- `plugins/spec-loop/references/hearing.md` — 新規。初回ヒアリングの決まりの原本（行う条件・型・落とし先・守ること）
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 手順 0（初回ヒアリング。`hearing.md` を指す）と、手順 4 の「今回の会で決めたい問」の選び方と `--focus`。frontmatter の description。版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `plugins/spec-loop/scripts/qa-to-pptx.py` — `--focus <No>[,<No>…]`（表紙の次に「今回の会で決めたい問」の 1 枚）
- `plugins/spec-loop/references/qa-csv.md` — 起票元の表の `要求確定` の行から `hearing.md` を指す（指し先だけ）
- `plugins/spec-loop/README.md` — 中身の表に `references/hearing.md` の 1 行と、PPTX の使い方の行に `--focus`
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.92.0 → 0.93.0）と description
- `.claude-plugin/marketplace.json` — 同上
- `scripts/test-qa-to-pptx.py` — `--focus` の観測と変異
- `docs/plugins/index.md` — 公開ページの req-loop の節に 1 項（指し先だけ）
- `docs/plans/issue-1042.md` — この計画

触らない:

- Q&A 表の列・`check-qa-csv.py`・MkDocs のフックの写し・`tree.md` の移行手順——利用者の決定（列を足さない）
- Q&A 表の行の並び——`qa-csv.md` の「番号の順に並べる」のまま。優先は資料の 1 枚でだけ表す
- 起票元の値と番号の印——ヒアリングで起票する行は既存の `要求確定（ヒアリング）`（印 `R`。`qa-csv.md` の例にもある）
- 提案 3 の列（判断の理由の欄）
- `CLAUDE.md`——新しいスクリプトもテストも足さない（`test-qa-to-pptx.py` の項は「変異テストを含む」の記述のままで正しい）

複製の数: ヒアリングの決まりの本体は `hearing.md` の 1 箇所。`SKILL.md`（手順 0）・`qa-csv.md`（1 行）・README（1 行）・公開ページ（1 項）は指すだけ。
「今回の会で決めたい問」の選び方の本体は `SKILL.md` の手順 4、`--focus` の守る／守らないは `qa-to-pptx.py` の docstring。README と公開ページは指すだけ。
description は 3 箇所（frontmatter・`plugin.json`・`marketplace.json`）に 1 句ずつ。分けない理由: 指し先が 1 つなら本体を直しても指す側は古くならない。

## 決めたこと

- **ヒアリングを行う条件は表から読む**——作業中の版が v1 で、共有の Q&A 表に行が 1 つも無い（表が無い・見出しだけ）とき。ほかに、利用者が求めたとき。
  再開点を表から読む決まり（`SKILL.md` の「守ること」）と合わせるため、会話の記憶で決めない。
- **ヒアリングで利用者が決めたことは Q&A の行にせず要求に書き、行にするのは決まっていないことだけ（回答は `未回答`）**——
  回答の列に書いてよい 3 つ（`SKILL.md`）を広げない。
- **「今回の会で決めたい問」は最大 3 問。スクリプトも 3 を超えたら 2 で拒む**——元記事の「最大 3 問ずつ」と合わせ、上限を散文だけにしない。
- **`--focus` に渡せる番号は、資料に載る行（`DONE` でない行）だけ**——載らない番号・重複・空は 2 で拒み、出力を作らない（既存の出力に触らない）。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`docs/plugins/index.md`）。

## 版の上げ方

spec-loop を minor で上げる（0.92.0 → 0.93.0。能力の追加）——`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md`（7 本）の 2 行。

## 受入基準（不変条件 × 経路）

入口: `qa-to-pptx.py` の CLI（`main`・`parse`）と、`build-proposal.py` が読む `package`・`write`・`markdown_slides`（触らない側）。スキル本文（`SKILL.md` 手順 0・手順 4、`hearing.md`）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| I1 | `--focus` を渡さなければ、出力は今までとバイト単位で同じ | `build` に枚数を足す・表紙を変える | `--focus` が無いときは枚を足さない。既存の観測（枚数・決定性）が緑のまま |
| I2 | `--focus` の 1 枚は表紙の次に、渡した順で、渡した番号だけを載せる（番号・質問の 1 行目・推奨のラベル） | 並べ替え・重複・一覧の後に置く | テストで段落の単位で当てる |
| I3 | 載らない番号（反映済み・表に無い）・重複・空・4 問以上の `--focus` は 2 で、出力を作らず既存の出力に触らない | `main` の検査の抜け・`parse` が値の無い `--focus` を通す | テストで 4 つの形を当て、変異で検査を外すと落ちる |
| I4 | 内部の表・列検査・綴り違い・同じ出力先の拒否は `--focus` があっても今までどおり | 検査の順を変える | 既存の観測に加え、`--focus` つきの内部の表で 2 |
| I5 | 回答を推測で埋めない（ヒアリングでも） | ヒアリングの答えを回答の列に書く・推奨を回答にする | `hearing.md` と `SKILL.md` 手順 0 に書く（散文。下の未証明） |
| I6 | 再開点は表から読む（ヒアリングを行うかも表で決まる） | 会話の記憶で「もう聞いた」とする | `hearing.md` の行う条件を表の状態で書く |
| I7 | 1 回に聞くのは最大 3 問、利用者の「十分」で終える、自明な質問をしない | スキル本文の書き漏れ | `hearing.md` に書く（散文。下の未証明） |
| I8 | 表の行の並びを変えない（優先は資料の 1 枚だけ） | 優先の順に表を並べ替える指示を書く | `SKILL.md` 手順 4 に「表は並べ替えない」と書く |
| I9 | 指し先が実在し、版と description の 3 箇所の決まりを満たす | 書き漏れ | `check-all.py`（`check-skill-pointers.py`・`check-plugin-versions.py`・`check-description-sync.py`） |
| I10 | 文面／実装が主張する事実が正しい（docstring の終了コード・README の使い方・公開ページの記述） | 書いたが動きと違う | 関門に実行して確かめさせる |

必須要件の掛け合わせ: 受入基準を Verifier と `/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が該当なしなら初回の 2 つ）。

### この環境では証明できないもの（未証明）

- I5・I7: スキルが実際の会話でヒアリングの型（最大 3 問・自明な質問をしない・「十分」で終える・回答を推測で埋めない）を守るか——振る舞いで、
  Eval（`claude plugin eval`）は spec-loop の req-loop に無く、この周では作らない。本文に書いたことまでを関門で見て、振る舞いは人間レビューに回す。
- 生成した PPTX を PowerPoint・LibreOffice で開けること（`test-qa-to-pptx.py` の「見ないもの」と同じ。CI に無い）。

### 生成物

- `SKILL.md` の測定値（`skill-metrics.py`）——対象は dev-loop の `SKILL.md` だけで、この周は触らない。該当なし。
- 図の書き出し（`diagrams/`）——触らない。該当なし。
- PPTX はテストが一時ディレクトリに作るだけで、リポジトリに置く生成物ではない。
- **生成物なし。**

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1042-req-loop-hearing-focus`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1042`・
  起点 `8aaf97ec`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `8aaf97ecc19024ad0c472c7121dff08c9bbb364a`
- 関門: まだ
- 反証と差し戻し: まだ
- 交絡: 実験なし（まだ）

## 既知の限界・決着済みの論点

（まだ無い）
