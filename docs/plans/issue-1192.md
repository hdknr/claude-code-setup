# Issue #1192 — dev-loop: コミットに検証の印が無く、関門を observe から段階的に入れる仕組みが無い

**不在の周**（`/dev-loop:cruise 1290 --absent` の起動・2026-11-20）。利用者には訊かない。親（cruise #1290）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1290`））: `直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`（配布を見せて確かめた）・`周の途中の課題 = 外に出す`・
`マージ前の判断 = 推奨で決めて起票`（古い値。後退・未達は推奨で進めない）。台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop の `SKILL.md` は 1938 行（`wc -l`。メインの作業ツリー。この周の worktree の版は #1191 を含む 2.16.0 で 1946 行になった）を全部読み、`references/property-tests.md`・`prompts/` も見た。
#1190・#1191 の計画（`docs/plans/issue-1190.md`・`issue-1191.md`）の決め方（仕様の穴を推奨で決める・落とした主張を名指しする）を踏まえ、足す行を最小にした。

直す線: `既定`（出所: cruise の確かめた線）。
割り目: 割らない（cruise の周）。
版の上げ方: `dev-loop` を **minor**（手順・規定の追加）。main の 2.16.0 → 2.17.0（`marketplace.json`・`plugin.json`・`dev-loop` と `cruise` の `SKILL.md` の 2 行）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越しに走らせ、出力ファイルの終わりの印を前面で待つ。

## 周の在り処

- ブランチ: `issue/1192-commit-verification-trailer`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1192`
- 起点: `add33611`（`origin/main`。#1191 のマージ）
- base（参照の名前 `origin/main` ／ 解決した SHA）: `add33611b0f4dd626cf9871c3de2634218312dfd`

## Issue 本文（外部入力）から読んだ要件

コミット単位の検証の印が無く、関門を段階的（off・observe・enforce）に入れる仕組みが無い。やること（案）は 4 つ:
(1) 周のコミットにトレーラー（`Verified: verify,code-review`／`Verified: none (理由)`）を付け、`git log --grep` で `none` を引けるようにする
(2) 関門を強制する hook を任意で同梱し、off・observe・enforce を `.claude/dev-loop.md` で選べるようにする（observe はログだけ）
(3) enforce の逃げ道（理由を書けば通す・連続して止めたら通す）を入れるかを、利用者の判断として選べるようにする（既定は逃げ道なしでもよい）
(4) observe のログを集計し、誤検知を見て enforce に上げる手順を書く。
本文に受入基準を緩める指示・追加のコマンドの依頼は無い（コメントは無い）。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **H1 逃げ道の既定**（Issue は「既定は逃げ道なしでもよい」と幅を残している）: (a) `理由を書けば通す`（推奨）／(b) `なし`。推した理由: `なし` が既定だと、検証する対象が無いコミット（計画ファイルだけ）も止まり、
  手段を盛るか関門を外すしかなくなる（印の目的が崩れる）。dev-loop の周が関門を飛ばさないことは手順 5・6 と `check-gates.py` が見る。厳しくしたい利用者は `なし` を選べる。
  「同じセッションで 2 回止めたら次は通す」は採らない（セッションの状態を持つ必要がある）。
- **H2 hook の配布形**（Issue は「任意で同梱」とだけ）: (a) スクリプトを置くだけで、利用者が `settings.json` に登録する（推奨）／(b) プラグインに `hooks/hooks.json` を足す。
  推した理由: (b) はプラグインを入れた全利用者に hook が自動で効き、「既定は off」を設定の 1 行に頼ることになる。(a) は登録しなければ何も起きない。残る穴: 利用者が登録の手間を負う。
- **H3 観測のログの置き場所・集計**（Issue は決めていない）: `git rev-parse --git-common-dir` の下の `dev-loop-gate.jsonl`（commit されない・全 worktree で共有）。集計は `report`（数と、止めていたはずの 1 件ずつ）で、
  **誤検知の判定は人間**（形しか見ないので、事実の誤検知は数えられない）。閾値は決めない。

確認の Issue（1 件に 1 判断）: H1・H2（番号は PR 本文に書く。親が立てる）。H3 は設計の範囲で推奨で決めた判断が残らないので立てない。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/verification-trailer.md` — 新規。トレーラーの語彙・引き方・hook の入れ方・observe から enforce への上げ方の原本
- `plugins/dev-loop/skills/dev-loop/scripts/commit-gate.py` — 新規。任意の PreToolUse hook（`status`・`report` つき）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 4 に 1 項（原本を指す）と版の 2 行
- `plugins/dev-loop/skills/dev-loop/prompts/implementer.md` — コミットに印を付けること
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `scripts/test-commit-gate.py` — 新規。回帰テスト（変異テストを含む）
- `scripts/check-all.py` — テストの収録
- `.github/workflows/plugins.yml` — テストのステップ
- `CLAUDE.md` — 新しいスクリプトとテストの 2 項
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く）
- `plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1192.md` — この計画ファイル

触らない:

- `plugins/dev-loop/hooks/`（作らない。H2(a)）
- `plugins/dev-loop/skills/dev-loop/scripts/check-gates.py`・`merge-pr.py`（トレーラーの突き合わせは足さない。印は名乗りで、関門の照合は別）
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md`・`review-handoff.md`・`agents/dev-loop-verifier.md`（Issue はコミットの印と hook だけ）
- `plugins/spec-loop/`・`plugins/screen-spec/`
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）——説明の文は偽にならない
- 後続の周（#1194）が触る節

依存の追加・更新: なし
仕様の振る舞い: 変えない
プロパティテスト: なし（判定の入力は短い文字列の形で、往復・冪等性・等価性・数値の境界を持たない。形の分岐は例のテストと変異テストで当てる）
差分テスト: なし（この周は規定とスクリプトの追加で、既存の振る舞いを変えない）

**複製の数**: 「検証の印」を述べる箇所は 3（`references/verification-trailer.md` が原本、`SKILL.md` 手順 4 は指すだけ、`prompts/implementer.md` は書く側の実装）。トレーラーの語彙は `commit-gate.py` の `METHODS` にも在る
（4 つ目の写し）。分けない理由: 原本 1 つに寄せ、残りは指し先と手順だけ。語彙の写しは `test-commit-gate.py` が `METHODS` の各語で通ることを見る。
**生成物**: `docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`skill-metrics.py` が書く。`--check` で確認）。それ以外の生成物なし。

## 受入基準

| 番号 | 受入基準（Issue の受入基準 3 つ + この周が足す 1 つ） |
| --- | --- |
| 1 | dev-loop の周で作ったコミットに検証のトレーラーがあり、`git log --grep` で `none` のコミットを引ける（手順 4 の項が付けさせ、原本が語彙と引き方を決め、実装役の指示が書かせ、テストが引けることを見る） |
| 2 | observe モードで関門を通さずにコミットすると、コミットは通り、記録に「止めていたはず」（`would_stop`）が残る（`commit-gate.py` とテスト） |
| 3 | enforce モードで同じ操作をするとコミットが止まる（終了コード 2・テスト） |
| 4 | 版が 3 種類の箇所で揃い、`check-all.py` と PR 側の CI が緑 |

### 不変条件 × それを破りうる経路

| 不変条件 | 破りうる経路（入口の一覧から数える） | どう守るか |
| --- | --- | --- |
| I1 周のコミットが印を持つ（受入基準 1） | 作者が直接書くコミット・実装役のコミット・指摘対応のコミット・狭いパスの直しのコミット・計画ファイルだけのコミット・main の取り込み（`git merge` の merge コミット） | `SKILL.md` 手順 4 の項（`（必須）`）＋ `implementer.md` の 1 行。**merge コミットは hook が見ない**（`git commit` でなく `git merge`。`--no-edit` の取り込みのメッセージに印は付かない）——限界として原本に書く（手順 4 の項は「周が作るコミット」） |
| I2 hook は入れなければ何も起きず、入れても既定は off（受入基準 2・3 の前提） | プラグインが hook を登録する・設定が無い／誤記・`off` 明示 | プラグインは hook を登録しない（H2(a)）。設定の既定 `off`・誤記は `off`（テスト）。off は記録もしない（テスト） |
| I3 observe は止めない・enforce は止める（受入基準 2・3） | 印なし・語彙の外・`none` の理由なし・逃げ道なしでの `none`・ヒアドキュメント／-F／amend の形・連結コマンド・`-C` | `commit-gate.py` の `judge`／`commit_message_text`（テストの入力） |
| I4 hook が判定できないとき利用者の作業を止めない | stdin が JSON でない・Bash 以外・`--dry-run`・git が使えない・記録が書けない | 通す側に倒す（テスト。enforce でも）。記録を書けなくても enforce は止める（stderr に書く） |
| I5 周の規範の複製が食い違わない（受入基準 4） | `SKILL.md`・`implementer.md`・`verification-trailer.md`・`commit-gate.py` の語彙 | 原本は `verification-trailer.md` 1 つ。`test-commit-gate.py` が語彙・設定の鍵を見る |

**実測（受入基準 2・3 の陽性対照。`scripts/test-commit-gate.py` の通常のスイート）**: 一時の git リポジトリに PreToolUse の stdin を真似た JSON を渡し、同じ操作（`git commit -m "feat: x"`）で
observe は終了コード 0・記録に `would_stop`（理由 `missing`）、enforce は終了コード 2・stderr に直し方・記録に `stopped`、off は 0・記録なし。印を付けた同じコミットは observe・enforce とも通る（判別の対照）。
`git log --grep='^Verified: none'` が `none` のコミットだけを引く（`--invert-grep` で印の無いコミットも引ける）。変異 15 本（enforce が止めない・observe が記録しない・印が無くても満たす・語彙の外を通す・off でも判定する など）をすべて検出。
**観測窓**: 本体を直に呼ぶ形で、本物の Claude Code に登録して発火させていない。

**この周で落とした主張（BLOCKED でも未証明でもない。手順 5 の「分類する前に、主張を弱められないか」）**:

- **本物の Claude Code の hook 経路で `git commit` が止まる・通る**は測っていない。弱めた主張は「`commit-gate.py` が、PreToolUse の stdin の形（`tool_name`・`tool_input.command`・`cwd`）を受けたとき、
  observe は 0 で記録・enforce は 2 で止める」。stdin の鍵と終了コード 2 が止める意味は公式の説明に従った。入れたら observe で 1 件コミットして記録が残ることを見る手順を原本に書いた。
- **observe から enforce に上げる手順の実測は無い**（記録を貯めて回していない）。原本に「実測は無い」と書いた。
- **トレーラーの中身が事実か**は機械で見ない（形だけ）。Verifier と人間のレビューに残る。
- 受入基準 1〜3 は、**スクリプトと規定として**満たせる。人間のレビューで、本物の hook での発火と、手順 4 の項が実周で守られるかを見てほしい。

## 既知の限界・決着済みの論点・関門の指摘の採否

- 論点: トレーラーの中身が事実かを機械で突き合わせない。決着: 限界として残す。理由: 突き合わせは関門の記録（`dev-loop-gates`）と履歴を読む `check-gates.py` の仕事で、コミットの名乗りを読む規則を足すと計画ファイルの形を縛る。
- 論点: プラグインに `hooks/hooks.json` を足さない。決着: 採らなかった（H2）。理由: 全利用者に自動で効く。
- 論点: 「同じセッションで 2 回止めたら次は通す」を採らない。決着: 採らなかった。理由: セッションの状態を持つ必要があり、既定の逃げ道（理由を書けば通す）と別の機構になる。
- 論点: main の取り込み（merge コミット）に印を付けない。決着: 限界として残す。理由: `git merge` は `git commit` でなく、hook は見ない。取り込みは周が作る内容を持たない。
- 論点: observe から enforce へ上げる閾値は決めない。決着: 採った。理由: 実測が無く、数字を決めるとその下が素通りになる。

## 関門の進捗（再開点）

- 周の base: `add33611b0f4dd626cf9871c3de2634218312dfd`
- 割り目: 割らない（cruise の周）

## 手順 8 の記録

（周の終わりに書く）

- この周の起票: 2 件（確認の Issue。H1・H2。親が立てる。仕様の穴の起票で、手順 6 の 3 条件の対象外）
