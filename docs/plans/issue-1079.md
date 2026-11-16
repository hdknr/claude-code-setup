# Issue #1079 — cruise: 未測定の権限モードの組で、子に `SendMessage` が届くかを測る

不在の周・出所: /dev-loop:cruise 1080 --absent の起動（2026-11-16T02:04Z）。cruise #1080 の子（サブエージェント）として回す。

直す線: `既定`（出所: cruise の台帳の確かめた線——利用者の確認（起動時・2026-11-16T02:04Z、配布を見せて確かめた））。
ほかの確かめた線（同じ出所）: 仕様の穴 = 推奨で決めて起票、実機確認 = Refs でマージ、マージ = 関門を通ればマージ、周の途中の課題 = 外に出す、マージ前の判断 = 推奨で決めて起票。
この子は手順 7 のマージをしない（親がする）。台帳は書かない。

課金の上限（Issue の追記・2026-11-16 利用者の確認）: 測る子の合計 $1。子は `--model haiku` と子ごとの `--max-budget-usd`。測り終えたら子を止め、残っていないことを確かめる。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/references/child-process.md` — 「宛先」の節: 届く条件の記述・実測の表（F〜M）・plan の子の費用・届いた本文の送り手の形・確かめていないこと
- `plugins/dev-loop/skills/cruise/references/parallel.md` — 「止まっている枠の持ち主」の 2 の「宛てられない周」
- `plugins/dev-loop/skills/cruise/scripts/child-cycle.py` — docstring の「守らない」の「子に送ったメッセージが届くこと」の 1 項（同じ主張の写し）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `docs/plans/issue-1079.md` — この計画

触らない:

- `child-cycle.py` のコード（起動口の振る舞い）——測った結果、起動口が変えるべき振る舞いは無い（`bypassPermissions` の子を拒むのも、`crossSessionInbound` を渡さないのも今のまま）
- 子が送り手を確かめる仕組み——#1078 の範囲。この周は `from` の形を記録するだけ
- `auto`・`bypassPermissions` のほかのモードの送り手を測ること——Issue の「やること」の組（未測定の子のモード・`claude -p` の親）の外。確かめていないこととして書く

依存の追加・更新: なし

複製の数: 「どの組で届くか」を述べる箇所は 3 つ（`child-process.md` の「宛先」・`parallel.md` の 2・`child-cycle.py` の docstring）。分けないのは、#1039 で同じ 3 箇所に書いた主張を実測に合わせ直す周だから（1 箇所だけ直すと残りが古くなる）。公開ページ・CLAUDE.md にはモードの組の主張は無い（`grep -rn 'bypassPermissions\|宛てられない'` で確かめた）。

## 版

dev-loop 1.112.0 → **1.112.1**（patch——記述を実測に合わせる修正）。`marketplace.json`・`plugin.json`・`SKILL.md`（dev-loop と cruise の 2 本）の 3 種類に同じ値。
cruise の周なので、マージの直前に main が進んでいたら子が取り込んで上げ直す（parallel.md の「版とマージの順」）——この子はマージしないので、取り込みが要るときは親か次の起動が行う。

## デプロイ経路

main へのマージで、プラグインの配布と GitHub Pages の再ビルド（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。

## verify の受入基準

不変条件:

1. **未測定の組が測られて残っている**——Issue の組（子の `acceptEdits`・`dontAsk`・`plan`・`manual` と `auto` の親の組、`claude -p` の親から送る組）について、届いたか（届かなければ保留か拒否か）が、版・起動の形・数えた実物とともに `child-process.md` に残っている。経路: 表（F〜M）・届く条件の箇条。
2. **記述が実測と一致する**——`child-process.md`・`parallel.md` の「宛てられない周」・`child-cycle.py` の docstring が、実測（どの組が届き、どの組が保留したか）と食い違わず、測っていない組を「届く」と書いていない。経路: 上の 3 箇所。
3. **送り手の形が記録されている**（Issue の追記）——対話の親・`claude -p` の送り手・サブエージェントのそれぞれについて、子に現れる `<cross-session-message from="...">` の値と、`peer_message_hold` の `from_name` が、出所（どの観測か）つきで残っている。
4. **課金の上限を守り、子を残していない**（Issue の追記）——測る子の費用の合計が $1 以下で、計画ファイルに和と内訳がある。起こした子は止め、`ps` で残っていないことを確かめた。
5. **版の 3 種類が揃う**（`check-plugin-versions.py`）。

掛け算: 2 つの関門 × 2 パスに上の 1〜5 をまるごと渡す（2 パス目が「該当なし」なら初回の 2 つ）。

未証明（この環境では証明できない）: なし——実測の対象はこの周で回した。**実際の dev-loop の 1 周の子に届くか**は Issue の受入基準ではなく、`child-process.md` の「確かめていないこと」のまま。

生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`）——SKILL.md は版の行しか変えない。`check-all.py` で確かめる。drawio は触らない。

## 実験（手順 5）——結果と交絡

**測り方**: メインの作業ツリーを cwd にし、起動口と同じ形（`-p`・stream-json・`--verbose`・`--name`・`--permission-mode`・切り離し・`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`）に `--model haiku`・`--max-budget-usd`・`--allowedTools "Bash(sleep 600)"` を足して子を起こした。
子は背景で `sleep 600` を起こしてターンを閉じ、届いたら道具を使わずに `GOT <1 行目>` と返す。数えたのは子の出力の 2 回目の init・`peer_message_hold`・応答と、子のセッションの記録に入った本文の実物。スクリプトは scratchpad（`probe/launch.py`・`probe/status.py`）。Claude Code 2.1.325。

| 子 | 子のモード | 送り手 | 結果 | 費用（子） |
| --- | --- | --- | --- | --- |
| F | auto | この子（`auto` の親のサブエージェント） | 届いた | $0.0161 |
| G | acceptEdits | 同上 | 届いた | $0.0160 |
| H | dontAsk | 同上 | 届いた | $0.0030 |
| I | manual（init は default） | 同上 | 届いた | $0.0028 |
| J | plan（1 回目） | — | 届く前に予算切れ（Sonnet で $0.2842） | $0.2842 |
| J | plan（2 回目・上限 0.40） | 同上 | 届いた | $0.1122 |
| K | auto | `claude -p` の送り手（auto・`probe-sender-1079`） | 届いた | $0.0028 |
| L | default | 同上 | 届いた | $0.0028 |
| M | auto | `claude -p` の送り手（bypassPermissions・`--tools SendMessage`） | 保留（held・mode-mismatch）。止めたとき dropped | $0.0055 |

送り手: auto の `-p` $0.0175、bypass の `-p` $0.0233。**合計 $0.486**（上限 $1 の内）。測り終えて全子のプロセスグループに TERM を送り、`ps` で `--name probe-`・`sleep 600` が 0 であることを確かめた。

送り手の形（記録の出所）: 対話の親は #1039 の子 A・B のセッションの記録（`from="uds:/tmp/cc-socks/26325.sock" from-name="claude-code-setup-de" from-mode="prompting"`）。サブエージェントは F〜J の記録（外側は親のセッション——pid 73913 のソケット・`claude-code-setup-4f`・`prompting`——内側に `<\agent-message from="a7148a0f3143c1165">`）。`-p` の送り手は K・L（`from-name="probe-sender-1079"`・`prompting`）と #1039 の E（`bypass`）。`from_name` は M（`probe-bysender-1079`）。

交絡を潰した手順:

1. 「設定のせいで届いた」——利用者・プロジェクトの settings と親の `--settings` のファイルに `crossSessionInbound`・`dialogExpiry` が無いことを確かめた。
2. 陽性対照: F（`auto` の子。#1039 の A と同じ組）が届くこと。陰性対照: M（`bypassPermissions` の送り手）で同じ形の子が保留すること——「どの組でも届く測り方」になっていないことを同じ版・同じ形で見た。
3. 「届いた」を `SendMessage` の成功ではなく、子の 2 回目の init と、子の記録に入った本文と、子の応答で数えた（`SendMessage` は保留でも成功と返る）。
4. 観測窓: 子はターンを閉じて背景の `sleep` を待つ間に受けた（起きてから約 1〜3 分）。ツールの呼び出しの最中・`/clear` の後・子から親への返事は見ていない。M は保留を見たところで止めたので、期限で落ちることは見ていない（#1039 の D で見てある）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1079-measure-sendmessage-modes`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1079`・起点 `7589c103`・base `origin/main` = `7589c103641f8dc7d91071c1e31a561661f76b3f`
- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目の関門に渡した起点（指摘対応の起点）: 未
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 手順 4 への差し戻し: 未
- 2 パス目: 未
- 割り目（2 パス目の前）: 割らない（cruise の周）
- 狭いパス: 未
- 外部レビュー: 未

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| サブエージェントから送った組は「対話の親から送った組」と同じか | 別の行として表に置き、同じとは書かない | 外側の `from` は親のセッションと同じだが、内側に `agent-message` が入り、送ったのは親のターンではない。#1039 の A・B（親が直に送った）とは分けて記録する |
| 本体の保留の判定（モードの名前か、`from-mode` の分類か）を言い切るか | 言い切らない | 本体を読んでいない。測った組で「`bypass` だけが保留した」までを書く |
| plan の子の費用（Sonnet で回る）を受入基準にするか | しない。記録として `child-process.md` に書く | 課金の上限の判断に要る事実なので残すが、Issue の求めではない |

## 採否の表

（関門の指摘を 1 件 1 行で書く）

## 起票（手順 8）

- この周の起票: 0 件（不在の周。周の途中の課題 = 外に出すで、子は起票しない——直すの行は PR コメントに書いて親に渡す）
