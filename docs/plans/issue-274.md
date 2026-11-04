# Issue #274 — spec-loop: スキルの差分モードの振る舞いを当てる Eval を置く

**不在の周**（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。利用者には訊かない（割り目も訊かない）。
前の周（同じ cruise）は「課金を許す線が無い」で BLOCKED にし、計画を `.claude/plans/issue-274.md`（gitignore・メインの作業ツリー）に残した。
**この周はその続きで、利用者の決定（#274 のコメント「利用者の決定（2026-11-04）」）を正として実装に入る**——
親からの委譲文で受けた。決定の中身:

1. **本物の `claude plugin eval` を回してよい。** 認証は対話ログインの OAuth（利用上限を使う）。上限の目安は Eval が出す費用の値（API 換算）で**合計 $40**。
   回すたびに費用を足し、超えそうなら回すのを止めてそこまでの結果で報告する。`--concurrency 1`。
2. **範囲は差分モードの 4 スキル（req-loop・spec-review・feasibility・proposal）だけ。** #217〜#219 の差分でない振る舞いは入れない（別の Issue）。

台帳 `issue-793` の確かめた線（出所: 利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
並行して #792（dev-loop）の周が別の体で走っており利用上限を分け合うので、**Eval は 1 本ずつ回す**。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `spec-loop` を **minor**（能力の追加——`evals/` を足す。0.x）。PR を出す直前の main の先端から minor を 1 つ上げる（着手時の main は 0.49.0）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

Issue 本文（外部入力）から読んだ要件: spec-loop の 4 スキルの差分モードは `SKILL.md` の文面を読んで確かめることしかできない。
`plugins/spec-loop/evals/` に差分モードの振る舞いを判別するケースを置き、**修正前の版で赤になることを確かめた grader だけを数える**（`CLAUDE.md` の「振る舞いを Eval で当てる」）。
本文とコメントに、受入基準を緩める指示・コマンド実行の依頼は無い（利用者の決定は親の委譲文でも同じ内容を受けた）。

## 設計の判断

- **「修正前の版」は `694fe954`**（差分モードを入れた `3e932a36`（#263）の直前、spec-loop 0.7.0）。その `plugins/spec-loop` を `git archive` で取り出し、
  **ケース（`evals/`）だけ現行のものを入れた複製**に当てる。
- **データの形の違いは、ケースの側で吸収する**——0.7.0 の Q&A 表には `推奨`・`推奨の理由` の列が無く、サインオフのタグの名前も違う
  （`v<n>/req-signoff-<k>`）。現行の形の試料をそのまま当てると、0.7.0 の検査（`check-qa-csv.py`・`check-signoff.py`）で止まり、
  **振る舞いと関係なく赤になる**（CLAUDE.md の「物の有無」と同じ形の交絡）。そこで scaffold の先頭に `FORMAT=current` の 1 行を置き、
  **古い版に当てる複製の中でだけ `FORMAT=0.7` に差し替える**。中身（要求・回答・見積り）は同じで、変わるのは列と名前だけ。
  両方の形が両方の版の検査を通ることは、手元で確かめた（下の「試料の確かめ」）。
- **判定役・検証役（`Agent`）は渡さない**——見るのは書く場所・数える範囲・手書き部分の中身で、判定役の起動は費用だけかかる。
  渡さないので、spec-review は手順 3、feasibility は手順 6 で止まる（止まり方そのものは見ない）。
- **陽性対照はリポジトリに置かない**——dev-loop の `scripts/run-dev-loop-evals.py` と同じく、プラグインの複製の中で
  本物のケースのディレクトリを写し、`name` と `prompt` だけ差し替えて組む。**対照の prompt は「誤った振る舞いを 1 行で直接させる」**もの
  （前の版のファイルを書き換える・前の版の機能を見積りに入れる・一覧を書く）。grader が赤になれることを見る。
- **走らせる道具（`run-dev-loop-evals.py` の spec-loop 版）は作らない**——この周では手で組んで回し、組み方をこのファイルに書く（`触らない:` に書いた）。
- **scaffold は 4 つが同じ土台（v1 の正本）を持つ**——同じことを述べている箇所は 4（各 scaffold の v1 の部分）。
  **分けない理由**: ハーネスが scaffold をどこから走らせるか（隣のファイルを読めるか）を確かめていない。共通のファイルを `source` する形は、
  確かめずに置くと全ケースが scaffold で落ちる。v1 の部分は試料で、版を跨いで直す規範ではない。

## 変更範囲

触る:

- `plugins/spec-loop/evals/` — ケース 4 つ（`case.yaml`・`scaffold.sh`）と `.gitignore`（`results/`）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `CLAUDE.md` — プロジェクト構成に `plugins/spec-loop/evals/` の 1 項
- `docs/plans/issue-274.md` — この計画

触らない:

- `plugins/spec-loop/skills/*/SKILL.md` の本文・`references/`・`scripts/`（振る舞いを測るだけで、直さない）
- `scripts/run-dev-loop-evals.py`（dev-loop 用。spec-loop 版の道具は作らない）
- #217〜#219 の差分でない振る舞いのケース（利用者の決定 2）

## 乗るデプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。
`evals/` は配布物に入るが、スキルの振る舞いは変わらない。

## 受入基準

不変条件 × それを破りうる経路。

| # | 不変条件 | 破りうる経路 | どう守る・どう確かめる |
| --- | --- | --- | --- |
| A | `plugins/spec-loop/evals/` に、差分モードの 4 スキルそれぞれの振る舞いを判別するケースがある | ケースが読み込まれない（YAML・schema の誤り）・scaffold が落ちる・grader が実行の中身を見ていない | 本物の `claude plugin eval` で 4 ケースとも読み込まれ、scaffold が走り、grader が採点されること（`aggregate-result.json`） |
| B | **数えるのは、修正前の版（`694fe954`）で赤になることを確かめた grader だけ**。赤の理由まで見て、物の有無・データの形で落ちたものは数えない | 修正前の版に当てていない・赤の理由を見ていない・データの形で止まった赤を数える | 4 ケースを現行の版と修正前の版の両方に当て、赤の grader ごとに trace で理由を書く（下の「結果」） |
| C | grader が赤になれる（陽性対照） | grader の pattern・path の誤りで常に緑 | 各ケースに対照を組んで回し、期待した grader が赤になること |
| D | 費用は合計 $40（API 換算）以内。`--concurrency 1`。回すたびに足す | 1 回の実行が想定より重い・回し直しが重なる | 各実行に `--max-cost-usd` を付け、`aggregate-result.json` の費用を下の「費用」に足していく。超えそうなら止める |
| E | 範囲は差分モードの 4 スキルだけ | 差分でない振る舞いのケースを足す | ケースの一覧と grader の対象を見る |
| F | scaffold は eval のワークスペースの外を触らない | 手で走らせる・リポジトリの中で走らせる | 空でないディレクトリ・`HOME` 以外を根とするリポジトリの中では断ること（手元で確かめる） |
| G | リポジトリの歯止めが緑で、版が 3 箇所で揃っている | 版の上げ忘れ・`results/` のコミット | `python3 scripts/check-all.py`・PR 側の CI |

掛け算: B × C——**修正前の版で赤**と**対照で赤**は別の問い（前者は振る舞いの差、後者は grader が赤になれること）。両方を grader ごとに書く。
B × D——費用の上限の中で B が足りなければ、そこまでの結果で報告する（数えた grader が 0 なら、そう書く）。

**この環境では証明できないもの（未証明）**:

- **振る舞いの率**——各腕は 1 回ずつしか回さない（費用の上限）。1 回の赤・緑は「その回にそうなった」で、率ではない。
  とくに**修正前の版で赤が出なかった grader は「判別しない」とは言えず、「この 1 回では判別を示せなかった」**である。
- **llm の grader（proposal）の judge（haiku）の揺れ**。

生成物: **該当なし**——Eval の結果（`results/`）は `.gitignore` で外す。図・生成ブロックに触れない。

## 試料の確かめ

（下に書く）

## 結果

（下に書く）

## 費用

（下に書く）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/274-spec-loop-diff-mode-evals`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-274`・
  起点 `9f5f05e5`・base 参照 `origin/main` → `9f5f05e5dad5b05176daa13b5c2b3eba45c49fea`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）

## 既知の限界・決着済みの論点

（下に書く）

## 手順 8

（下に書く）
