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
4. 観測窓: 子はターンを閉じて背景の `sleep` を待つ間に受けた（起きてから約 13〜48 秒——子のセッションの記録の時刻）。ツールの呼び出しの最中・`/clear` の後・子から親への返事は見ていない。M は保留を見たところで止めたので、期限で落ちることは見ていない（#1039 の D で見てある）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1079-measure-sendmessage-modes`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1079`・起点 `7589c103`・base `origin/main` = `7589c103641f8dc7d91071c1e31a561661f76b3f`
- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目の関門に渡した起点（指摘対応の起点）: `ec315b98826d76ef123ede4047f91280adbd2cbd`
- 歯止め: `check-all.py`（run-serial 越し）81 本中 80 本 OK、`check-plan-counts.py` が件数の行の欠けで FAIL → 行を足して単独で再実行し OK
- Verifier 1 パス目（sonnet・`dev-loop:dev-loop-verifier`。テンプレート 186 行を読んだと報告——`wc -l` と一致）: 反証 0 件・軽微な指摘 3 件（V1〜V3）。`git status --porcelain` は前後で同じ
- `/code-review` 1 パス目（high）: 指摘 8 件（CR1〜CR8）。`git status --porcelain` は前後で同じ
- 採否: 11 件とも「直す」（下の採否の表）。手順 4 への差し戻し: なし（Verifier の反証 0 件。指摘対応として直した）
- 2 パス目: 回した。1 パス目の指摘対応の終点 `a8221be1a5d93b8e2b58cbcde888f8d2d2756230`（`check-all.py` 81/81 OK の後にコミット）
  - Verifier 当て直し（sonnet。186 行を読んだと報告）: 反証 0 件・軽微 4 件（V2-a〜d）。`git status --porcelain` は前が空・後が計画ファイルの 1 行（並行して著者が再開点を書いた分）
  - `/code-review` 2 パス目（high）: 指摘 9 件（CR2-1〜9）。`git status` は同じく計画ファイルの 1 行だけ増えた（著者の編集）
- 2 パス目の指摘対応の起点（狭いパスの起点）: `a8221be1a5d93b8e2b58cbcde888f8d2d2756230`（指摘対応に入る前に記録）
- 2 パス目の指摘対応の終点（狭いパスの終点）: `d8865fe12f192ce87a4f10a19c27dd693548c33f`（`check-all.py` 81/81 OK の後にコミット）
- 狭いパス（sonnet。186 行を読んだと報告）: 反証 1 件（R1）・補足 2 件（S1・S2）。後退なし。`git status` は前後とも空
- 狭いパスの指摘の直し（`マージ前の判断 = 推奨で決めて起票` の線。推奨「直してからマージする」）: 起点 `d8865fe12f192ce87a4f10a19c27dd693548c33f`・終点 `95c15a85b8e3b4bab4ed58ef741253d22cfa9a6f`。当て直し（sonnet・1 回だけ）: 反証 0 件・素通りした変異 0（変異 3 本とも記録で反証された）。`check-all.py` 81/81 OK
- 割り目（2 パス目の前）: 割らない（cruise の周）
- 狭いパス: 回した（上）
- 外部レビュー: PR 側の CI の後に `external-reviews.py` で見る

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| サブエージェントから送った組は「対話の親から送った組」と同じか | 別の行として表に置き、同じとは書かない | 外側の `from` は親のセッションと同じだが、内側に `agent-message` が入り、送ったのは親のターンではない。#1039 の A・B（親が直に送った）とは分けて記録する |
| 本体の保留の判定（モードの名前か、`from-mode` の分類か）を言い切るか | 言い切らない | 本体を読んでいない。測った組で「`bypass` だけが保留した」までを書く |
| plan の子の費用（Sonnet で回る）を受入基準にするか | しない。記録として `child-process.md` に書く | 課金の上限の判断に要る事実なので残すが、Issue の求めではない |

## 採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: 「`-p` の子の標準出力には本文が載らない」は偽——`result` の `origin` に本文・送り手・`verifiedPeerPid` が載る | 示せる——`probe-pauto-1079.out` などの `result` の `origin`（著者が走らせて確かめた） | 3（送り手の形） | 直す |
| CR2・V1: parallel.md が「`auto` の親（対話・`-p`・サブエージェント）は測ったどの子のモードにも届いた」と直積で書く | 示せる——対話の親と `-p` から acceptEdits・dontAsk・plan の子へは測っていない（表 A〜M） | 2 | 直す（表を正とする指し先に替えた） |
| CR3: 「A〜M はどれも届いた」「約 1〜3 分」は誤り（C・D・M は届いていない。#1079 は 13〜48 秒） | 示せる——表と子の記録の時刻 | 1・2 | 直す |
| CR4: 箇条の書き出し「権限確認を飛ばさないモードなら、測ったどの子のモードにも届いた」が一般化している | 示せる——同じ箇条の後ろの「測っていない」と食い違う | 2 | 直す |
| CR5: 対話の親・サブエージェントの `peer_message_hold` の `from_name` が「見ていない」とも書かれていない | 示せる——保留した組は bypass の `-p` だけ | 3 | 直す（見ていないと書いた。BLOCKED として申告——下） |
| CR6: M の送り手は `--tools SendMessage` でも K と違うので、K・L と M の対比だけでは `bypassPermissions` が原因と決まらない | 示せる——`bysender.out` の init の `tools` は `SendMessage` だけ | 2（実験の判別） | 直す（交絡を書き、根拠を `cause` と公式ドキュメントにした） |
| CR7: child-cycle.py の docstring も直積に読める | 示せる——CR2 と同じ | 2 | 直す（表を正とする指し先に替えた） |
| CR8: 組の一覧を 3 箇所に写して既に食い違っている | 示せる——parallel.md と docstring は manual を落としていた | 2 | 直す（CR2・CR7 の直しで写しを無くした） |
| V2: F〜J の送り手の親が `auto` である出所が無い | 示せる——`from-mode` は auto でも default でも `prompting` | 2 | 直す（親のセッションの記録の `permissionMode` が 19 件とも `auto` と書いた） |
| V3: 道具の説明を「保留する」と言い切るが原文は usually | 示せる——道具の結果の文 "usually a different permission mode" | 2 | 直す |
| CR2-1: 「`from-mode` は `default` でも `prompting`（A・B・K）」——`default` の送り手は測っていない | 示せる——A・B・K の送り手はどれも `auto` | 2・3 | 直す |
| CR2-2: 「`auto` の送り手から測った組はどれも届いた」——C（`refuse` の子）は届いていない | 示せる——表の C | 2 | 直す |
| CR2-3: V3 の直しが道具の説明（usually なし）と道具の結果・知らせ（usually は原因の説明）を混ぜて意味を逆にした | 示せる——道具の説明の文と `bysender.out` の知らせの文 | 2 | 直す |
| CR2-4: 「送った側には成功と返るので保留は子の出力でしか分からない」——M では送り手の出力に保留の知らせ（`level: warning`）がすぐ出た | 示せる——`bysender.out` 16 行目（著者が確かめた） | 2 | 直す（child-process.md と child-cycle.py の docstring） |
| CR2-5・V2-a: 「`user` や `assistant` の行には本文が出ない」——子が引き写した文が `assistant` の行と `result` の文に出る | 示せる——`probe-auto-1079.out` など | 2・3 | 直す（引き写しは送り手の確かめに使えず `origin` を読む、と書いた） |
| CR2-6: 子の記録の `user` の行は先頭に `Another Claude session sent a message:` が付く | 示せる——F の記録（著者が確かめた） | 3 | 直す |
| CR2-7: parallel.md は組の表に頼らず、送り手の保留の知らせや `peer_message_hold` を見て宛てられないと決めるべき（設計の高さ） | 示せない——いまの記述が誤っているのではなく、決め方の提案 | 無し | 残課題 |
| CR2-8: 「F〜M は親が止めた」——plan の 1 回目は予算切れで終わった。#1039 の「自分で終わった」と混ざる | 示せる——`probe-plan-1079.first.out` の `error_max_budget_usd` | 4 | 直す |
| CR2-9・V2-c: `manual` の子は init が `default` で別のモードとして測れていない。「子 9 体」は起動 9 回・子 8 体 | 示せる——I の init | 1・2 | 直す |
| V2-b: 親の `permissionMode` の件数（19）が記録の伸びで変わる | 示せる——いまは 23 件 | 無し（値はどれも auto） | 直す（件数を書かない形にした） |
| V2-d: 計画ファイルの観測窓が「約 1〜3 分」のまま | 示せる | 無し（計画ファイルは成果物でない） | 直す（記録の直し） |
| 狭いパス R1: 引き写しの例「F〜I・K・L」が広い——K・L・J は本文の 1 行だけ、H は内側の `agent-message` だけ | 示せる——各 `.out` の応答（著者が確かめた） | 無し（届く組・送り手の形の記録は正しい。例の範囲の文言） | 振り分け: 直す（利用者に見える誤り——#1078 が読む記述が実測と違う）。後退でない。推奨: 直してからマージする（直して 1 回だけ当て直す） |
| 狭いパス S1: 「`from-mode` はモードの名前ではなく」は推論で、`bypass` の組と並べると弱く食い違う | 示せない——続く文が測った範囲を言っている | 無し | 記録だけ |
| 狭いパス S2: plan の 1 回目にも背景の体の `killed` がある | 示せない——記述は「killed だから親が止めた」と読ませていない | 無し | 捨てる（確かめて成り立たない） |

## BLOCKED

- **不変条件 3 のうち、対話の親・サブエージェントから送って保留したときの `peer_message_hold` の `from_name`**——保留が起きたのは送り手が `bypassPermissions` の組だけで、対話の親やそのサブエージェントを `bypassPermissions` で起こす手段がこの周（cruise の子のサブエージェント）に無い（無いのは権限・環境）。次善: `-p` の送り手（bypass）の保留で `from_name` が `--name` の値になることを見た（M）。
  不在の周で `マージ前の判断 = 推奨で決めて起票` の線があるので、PR コメントに推奨（マージする）とマージ後の確かめ方を書き、確認の Issue は親が立てる。

## 振り分け（手順 8。found-lines.md）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| parallel.md は組の表に頼らず、保留の知らせ・`peer_message_hold` で宛てられないと決めるべき | #1079 /code-review 2 パス目（CR2-7） | 示せない（決め方の提案） | 記録だけ |
| 「`from-mode` はモードの名前ではなく」は推論 | #1079 狭いパス（S1） | 示せない | 記録だけ |
| plan の 1 回目にも `killed` がある | #1079 狭いパス（S2） | 示せない（成り立たない） | 捨てる |
| 狭いパス R1（引き写しの例が広い） | #1079 狭いパス | 示せる | 直す——マージ前の判断の線で周の中で直した（推奨: 直してからマージする。当て直し反証 0 件） |

直すの行で周の外へ出すもの: なし（R1 は周の中で直した）。仕様の穴: なし。

## 起票（手順 8）

- この周の起票: 0 件（不在の周。周の途中の課題 = 外に出すで、子は起票しない——直すの行は PR コメントに書いて親に渡す）
