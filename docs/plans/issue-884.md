# Issue #884 — 確認の Issue を閉じるときに、推奨のままか変えたかを 1 行で残す

不在の周（`/dev-loop:cruise 887 --absent` の起動・2026-11-06T01:37:35Z、利用者の確認・配布を見せて確かめた）。cruise #887 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かず「割らない（cruise の周）」）。従う版は dev-loop 1.74.1（キャッシュ。SKILL.md 1852 行）。

- 直す線: **既定**（出所: cruise の確かめた線——上の起動。台帳 `issue-887`）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #887 -->`）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認の線: 台帳に無い（`.claude/dev-loop.md` の宣言か既定）
- 版の上げ方: **minor・dev-loop と spec-loop の両方**（main の先端 dev-loop 1.96.0 → 1.97.0・spec-loop 0.65.0 → 0.66.0。dev-loop は確認の Issue の書き方と cruise の §6 に手順を足す、spec-loop は `rebuild-scope.py` に結果の読み取りと `--changed` を足す——どちらも能力・手順の追加）。マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す
- PR は `Fixes #884` と `Refs #870`（#870 は閉じない）・`Refs #887`

## 変更範囲

触る:
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 確認の Issue の書き方に、閉じるときの結果の 1 行（形と置き場所）。本文の並びの 9・例 2 つ・「後で利用者がすること」・spec-loop から来た Issue の穴の閉じ方
- `plugins/dev-loop/skills/cruise/SKILL.md` — §6 の承認で閉じる渡しに、結果の 1 行を添えること・版の 2 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行
- `plugins/spec-loop/scripts/rebuild-scope.py` — 閉じのコメントの結果の行を読む・推奨のまま／変えた／結果なしを出す・`--changed`
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 取り方の 1 行に `comments`・版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/references/handoff-issue.md` — 確認の Issue の結果も同じ入力から引くこと（1 句）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/test-rebuild-scope.py` — 結果の行の試料・写しの突き合わせ・変異
- `CLAUDE.md` — `rebuild-scope.py` の行に結果の行を読むこと
- `docs/plugins/spec-loop.md` — 公開ページの 1 文に結果（推奨のまま・変えた）も引けること
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない）
- `docs/plans/issue-884.md` — この計画

触らない:
- `plugins/spec-loop/scripts/parent-checklist.py` — `rebuild-scope.py` の `read_issues` を読むだけ（`comments` は任意の鍵にするので形は変わらない。テストで確かめる）
- `ledger.py`・cruise の閉じ方の判定（GraphQL の 1 行）——閉じる人の決まり（#636）は変えない

複製の数（同じことを述べている箇所）: 結果の 1 行の形は 3 箇所（`absent-lines.md`〔原本〕・`rebuild-scope.py` の定数・`test-rebuild-scope.py` の試料）。cruise §6 は原本を指すだけ。取り方の 1 行（`gh issue list … --json …`）は 2 箇所（`rebuild-scope.py` の docstring・scaffold の `SKILL.md`）。
**分けない理由**: dev-loop（書く側）と spec-loop（読む側）の境界の写しで、`test-rebuild-scope.py` が原本と突き合わせる（#875 と同じ形）。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージで GitHub Pages（`docs/`）とプラグインのカタログに入る。マージは親。

## 設計（この周で決めたこと）

- **形**: 行頭から装飾なしで `確認の結果: 推奨のまま` か `確認の結果: 変えた: <新しい値を 1 行で>`。
- **置き場所**: **閉じるときに添えるコメント**（`gh issue close <番号> --comment "確認の結果: 推奨のまま"`・GitHub の画面の「Close with comment」）。
  本文には書かない——本文は立てた側の記録で、立てた後に書き換えない決まり（「1 件に 1 つの判断」）と、`決めた値: ` と同じ本文に結果が混ざると承認の前後が見分けられない。
  コメントなら閉じた時点の判断として残り、開き直して変えたときも後のコメントで上書きできる（**読む側は最後の結果の行を採る**）。
- **書くのは閉じる人**（利用者。利用者の指示で閉じるセッションも同じ）。立てる側は `## 承認するなら`・`## 別の値を選んだら` に、そのまま写せる 1 行を書いておく。
- **読む側**（`rebuild-scope.py`）: 入力に `comments` を足す（`gh issue list --json number,title,state,body,comments`）。`comments` が無い入力は「結果を読んでいない」と言う（「結果なし」と言わない）。
  `--changed` で、結果が `変えた` の確認の Issue だけを、決めた値・新しい値・影響する Issue つきで出す。
- **仕様の穴（推奨で決めた）**: 受入基準 2 の「cruise が承認で確認の Issue を閉じるときに」は、閉じるのは利用者だけ（cruise の「GitHub に書くものの印」・#636）と食い違う。
  選択肢 A（推奨）: 閉じるのは利用者のまま。cruise は §6 の渡しで、閉じるときに結果の 1 行を残すことを添える（利用者の指示でセッションが閉じるときも同じ 1 行）。
  B: cruise の親が §6 で利用者の承認を受けて閉じ、結果の 1 行を書く（#636 の決まりと §6 の閉じ方の判定を変える）。
  **決めた値: A**。理由: #636 の「利用者が閉じたか」の判定を変えずに済み、行を書く人と閉じる人が同じになる。確認の Issue: 下の「未解決の判断」。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 結果の 1 行の形と置き場所が dev-loop の原本（`absent-lines.md` の「確認の Issue の書き方」）に決まっている | 本文の並びの 9・例 2 つ・「後で利用者がすること」・spec-loop から来た Issue の穴の閉じ方が、行を残さずに閉じると読める | 読む＋`grep` |
| A2 | cruise が承認で確認の Issue を閉じる手順（§6 の渡し）で、結果の 1 行を残す | §6 の「承認（閉じる）と修正は利用者がする」の段・spec-loop から来た Issue の穴の渡し | 読む |
| A3 | `rebuild-scope.py` が結果の行を読み、推奨のまま・変えた・結果なしを見分けて出す | `#N` の引き・引数なしの一覧・`--changed`・`comments` の無い入力・`comments` の形が違う入力（2）・形に反する結果の行（名指しして 1）・複数の結果の行（最後を採る）・本文の中の結果の行（読まない） | `test-rebuild-scope.py` の試料と変異 |
| A4 | 結果の行の頭の写し（本体の定数）が `absent-lines.md` に在る | 片方だけ言い換える | テストの突き合わせ＋陽性対照 |
| A5 | 取り方の 1 行が `comments` を取る（docstring・scaffold の `SKILL.md`）。`parent-checklist.py` は変わらず動く | `comments` を足し忘れた片方 | 読む＋`test-parent-checklist.py` |
| A6 | 版が 3 種類の箇所で揃い（dev-loop 1.97.0・spec-loop 0.66.0）、生成ブロックが新しい | 片方だけ上げる | `check-plugin-versions.py`・`skill-metrics.py --check`・`check-all.py` |
| A7 | 必須の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す（4 つの受け渡し。2 パス目が「該当なし」なら 2 つ） | 片方の関門・片方のパスに渡し忘れる | 再開点に記録 |

- 生成物: **あり**——`docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`SKILL.md` を触るので `skill-metrics.py` で書き直し、`--check` で見る）。図（drawio）は触らない。
- 未証明: **本物の `gh issue list --json comments` が、コメントの多い Issue で全部のコメントを返すか**（試料は `gh` と同じ鍵の JSON。形は #695 で 1 度だけ実物を見た——鍵に `body` がある）。docstring の守らないものに書く。

## 未解決の判断・確認待ち

- 仕様の穴（上の設計の最後の項）の確認の Issue: （起票後に番号を書く）

## 手順 8（起票数）

- この周の起票: 1 件（仕様の穴を推奨で決めた確認の Issue。不在の線 `仕様の穴 = 推奨で決めて起票`）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/884-confirm-result-line`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-884`・起点 `88e85fab`・base `origin/main` = `88e85fab0d5615e79da5e4a43b8a3157079c4737`
- 割り目（手順 4 の完了時）: 割らない（cruise の周・利用者不在で訊かない）
- 交絡: 実験なし（試料に当てるテストだけ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 結果の行を本文に置くか | 置かない（閉じのコメント） | 上の設計 |
| cruise が確認の Issue を閉じるか | 閉じない（#636 のまま。推奨で決めて確認の Issue） | 上の設計 |
| 行の頭に装飾を付けた・文の途中の結果の行 | 読まない（結果なしと出る） | 台帳の 2 行と同じ決まり（行頭・装飾なし） |
