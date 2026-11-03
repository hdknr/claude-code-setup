# Issue #670 — 「利用者の判断」に振った仕様の穴を、`仕様の穴 = 推奨で決めて起票` の線に乗せる

**不在の周**（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。利用者には訊かない（割り目も訊かない）。
台帳 `issue-793` の確かめた線（出所: cruise の確かめた線（台帳 `issue-793`）。利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳（`.claude/plans/cruise-issue-793.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（手順の追加——振り分けに「仕様の穴か」を判定する段を足す）。main の先端 1.75.3 → **1.76.0**
（並行する PR #799・#800 も 1.76.0 に上げている。マージの直前の上げ直しは親が子に回す——cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

Issue 本文（外部入力）から読んだ要件: 振り分けで「利用者の判断」に振る前に、その行が仕様の穴かを判定する段を置く。仕様の穴なら台帳の `仕様の穴` の線に従い、
`推奨で決めて起票` なら推奨で決めて `要確認:` の Issue を立て、行は直す（推奨の決定つき）として台帳に足す。「利用者の判断」に残すのは推奨を立てられないもの
（要求・Q&A の回答と新しい決定が食い違う・利用者の過去の回答を変える）と狭いパスの採否。委譲文・最終報告の候補に「仕様の穴か」を足す。
本文に受入基準を緩める指示・コマンド実行の依頼は無い。

## 設計の判断

- **原本は `references/found-lines.md` の「台帳に足す」**。新しい小節「仕様の穴の行」を置き、行き先（台帳／利用者の判断）を決める前に当てる。
  他（`absent-lines.md`・cruise `SKILL.md` §4 の 2・`prompts/child-cycle.md`・公開ページ）は指すだけ。
- **掛かるのは `周の途中の課題 = 台帳に足して直す` の周だけ**——止まる（`blocked`）のはこの線の「利用者の判断」の行だけで、`外に出す` の周は行を止めない（PR コメントの起票の候補）。
  `外に出す` の行き先は変えない。
- **穴の判定の定義は `references/spec-gap.md` の「何が仕様の穴か」と同じ**にし、写しを作らない。加えて「利用者が既にした決定（Q&A の回答・決定表・確認の Issue の答え）と食い違う」「過去の回答を変える」は穴ではなく利用者の判断、と書く。
- **推奨で決めた行は `todo` で台帳に足し、確認の Issue（`absent-lines.md` の書き方・印 `<!-- cruise-decision: #<親> -->`）を 1 穴 1 件で立てて、その行の `decisions` に足す**——
  `absent-lines.md` の「`仕様の穴 = 推奨で決めて起票`」の手順 1〜4 をそのまま当てる（写さず指す）。推せないなら利用者の判断。
- **元の周の Issue が spec-loop から来たなら、線は効かない**（`absent-lines.md` の同節と同じ理由）——利用者の判断。
- **狭いパスの指摘は穴でも利用者の判断のまま**（採否は人間。マージの判断も変えない）。
- `ledger.py` は変えない——`decisions` は `set` で既に足せる（鍵の一覧にある）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` — 振り分けの表に「仕様の穴か」の列・「台帳に足す」の行き先と新しい小節「仕様の穴の行」・件数と PR コメント・`要確認` の Issue の節
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「`仕様の穴 = 推奨で決めて起票`」から周の途中の課題の穴を指す 1 項
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 2 の委譲文の項目（報告に「仕様の穴か」と推奨）・版
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md` — 報告の項目に「仕様の穴か」
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-cruise.md` — 公開ページの「利用者の判断が要る行は止めておき」の説明（指すだけ）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-670.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` と `LINES`——値も鍵も変えない
- `references/spec-gap.md`——spec-loop から来た Issue の差し戻しは変えない（定義を指すだけ）
- `外に出す` の周の行き先・起票の 3 条件・狭いパスの指摘の採否とマージの判断

### 同じことを述べている箇所の数

「利用者の判断の行は推奨で決めない／止める」を述べる箇所: `found-lines.md`（原本。表の列・台帳に足す・利用者の判断をまとめて訊く）・`absent-lines.md`（`仕様の穴` の節・訊く場面）・
cruise `SKILL.md` §4 の 2・`child-cycle.md`・公開ページ——**5 か所**。分けない理由: 原本の外は指すだけにし、列挙を置かない。

## 受入基準

不変条件と、それを破りうる経路（経路は「周の途中の課題が台帳・確認の Issue・利用者の判断待ちに入る入口」から数える）:

- **A1**（Issue 提案 1）: `found-lines.md` が、`台帳に足して直す` の周の直すの行を「利用者の判断」に振る**前に**仕様の穴かを判定する段を持ち、
  穴で台帳の線が `仕様の穴 = 推奨で決めて起票` なら、推奨で決めて確認の Issue（`absent-lines.md` の書き方）を立て、行を**台帳**（`blocked` にしない）に足すと読める。
  経路: Verifier・`/code-review` の 1・2 パス目の残課題／仕様の穴（周の中で確認の Issue にしなかったもの）／Issue に無い機能／利用者の判断が要る行——**各経路で**同じ判定が掛かる。
  狭いパスの指摘は例外として利用者の判断のまま、と読める。
- **A2**（Issue 提案 2）: 「利用者の判断」に残るのが、推奨を立てられない行（利用者が既にした決定・回答と食い違う・過去の回答を変える・推せない）・線が `推奨で決めて起票` でない・元の周の Issue が spec-loop から来た・狭いパスの指摘、に限られると読める。
  旧文「推奨で決めない（仕様の穴を推奨で決めるのは `仕様の穴` の線だけで、この線ではない）」と食い違う記述が、原本・`absent-lines.md`・cruise `SKILL.md`・`child-cycle.md`・公開ページに残っていない。
- **A3**（Issue 提案 3）: 振り分けの表と、周の報告の項目（cruise `SKILL.md` §4 の 2 の委譲文の項目・`prompts/child-cycle.md`）に「仕様の穴か」（と推奨）があり、親がそれで行き先を決められる。
- **A4**（変えないもの）: `外に出す` の周の行き先・起票の 3 条件（(a)・(b) は外れない）・振り分けの 3 条件・狭いパスの採否とマージの判断・spec-loop から来た Issue の差し戻し、は変わらない。
  確認の Issue は 1 穴 1 件で、件数の行に数える（`absent-lines.md` と食い違わない）。
- **A5**（版）: `dev-loop` の版が 3 種（`marketplace.json`・`plugin.json`・両 `SKILL.md` の 2 行）で 1.76.0 にそろう。§8.2 の生成ブロックが新しい（`skill-metrics.py --check`）。
- **A6**: `check-all.py` が緑（順番待ち越し）。PR 側の CI が緑。
- **A7**（事実の真偽）: 書き足した指し先（節の名前・ファイル）が実在し、`ledger.py set … decisions=` が実際に受け付ける（台帳の鍵）。

必須要件の掛け算: A1 × 経路（4 経路）× 線の値（`推奨で決めて起票`／それ以外）。

この環境で証明できないもの（未証明）: 今後の cruise の周と親が、実際にこの判定で止まらずに進むか（将来の周の振る舞い）。

生成物: §8.2 の生成ブロック（`SKILL.md`・`references/*.md` の行数が動けば `skill-metrics.py` で書き直す）。図の書き出し: なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/670-found-lines-spec-gap`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-670`・起点 `896667d2`・base `origin/main` → `896667d2ba7d28a8e417e185e75e9479bfc25918`
- 割り目（手順 4）: 割らない（不在の cruise）
- 交絡: 実験なし

## 既知の限界・決着済みの論点

- `外に出す` の周には新しい段を掛けない（行を止めないので、Issue の症状が起きない）——採った。
- `ledger.py` を変えない（`decisions` は既に `set` できる）——採った。

## 手順 8

- この周の起票: 0 件（起票の承認は不在のため訊いていない。仕様の穴の確認の Issue は無い）
