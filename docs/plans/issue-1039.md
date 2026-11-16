# Issue #1039 — cruise: `claude -p` の子プロセスにも `SendMessage` で宛てられるか確かめ、「宛てられない」前提を見直す

利用者が居る周（利用者の指示「1039 を対応」、2026-11-16）。直す線: `既定`（出所: `.claude/dev-loop.md` に行が無く、利用者が居るが訊いていない——既定として扱う）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/child-cycle.py` — 子に `--name cruise-<台帳の名前>-<番号>` を付け、宛先を記録の `peer` に残して起動時と `status` で出す。`status` は子が保留したメッセージ（`peer_message_hold`）も出す
- `scripts/test-child-cycle.py` — 上の回帰テストと変異（3 件）
- `plugins/dev-loop/skills/cruise/references/child-process.md` — 「宛先（#1039）」の節（実測の表・届く条件・確かめていないこと）と、`/clear` 後の項の「宛てられない」を直す
- `plugins/dev-loop/skills/cruise/references/parallel.md` — 「止まっている枠の持ち主」の 2 の宛先と「宛てられない周」、守らないもの D4
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.111.0 → 1.112.0。能力の追加なので minor）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `CLAUDE.md` — child-cycle.py の説明に名前を付けることを 1 句
- `docs/plans/issue-1039.md` — この計画

触らない:

- `crossSessionInbound: accept` を子に渡すこと——下の「決着済みの論点」の 1
- `ledger.md` の「訊く相手は…`claude-p:` で始まる周はこの項に入らない」——状態を訊く項で、子プロセスの周は `status` で確かめる形のまま（宛てられるようになっても変えない）
- `prompts/child-cycle.md`（子への委譲文）——子が届いたメッセージにどう応じるかは `parallel.md` の 4 が正で、委譲文には足さない

依存の追加・更新: なし

## デプロイ経路

main へのマージで、プラグインの配布と GitHub Pages の再ビルド。

## verify の受入基準

不変条件:

1. **実測が残っている**——Claude Code の版・子の起動引数・`ListAgents` に子が出たか・`SendMessage` が届いたかが、`child-process.md` に残っている（Issue の受入基準 1）。
2. **記述が実測と一致する**——`child-process.md` と `parallel.md` の「宛てられない」の記述が、実測（届く条件・届かない条件）と食い違わない（Issue の受入基準 2）。経路: `child-process.md` の `/clear` 後の項・「宛先」の節、`parallel.md` の 2・3・守らないもの D4、`child-cycle.py` の docstring、CLAUDE.md の説明。
3. **起動口の振る舞い**——`launch` が子に `--name cruise-<台帳>-<番号>` を渡し、記録の `peer` と起動時の出力に宛先を出す。`status` が宛先（無い記録は「無し」）と保留されたメッセージ（メッセージごと・最後の状態）を出し、保留で終了コードを変えない。既存の振る舞い（`-p` の直後の引数で走っているかを決める判定など）を壊さない。経路: `launch`・`status`・古い記録（`peer` が無い）。
4. **版の 3 箇所が揃う**（`check-plugin-versions.py`）。

未証明（この環境では証明できない）: 実際の dev-loop の 1 周（数十分）の子に届いて、子が `parallel.md` の 4 のとおり動くか——1 周を子で回す必要があり、`child-process.md` の「利用者が測る手順」と同じく親の cruise でしか測れない。`child-process.md` の「確かめていないこと」に書いた。

生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`）——SKILL.md の版の行しか変えないので鮮度は変わらない見込み。`check-all.py` で確かめる。drawio は触らない。

## 実験の交絡（手順 5）

- 利用者・プロジェクトの settings に `crossSessionInbound`・`dialogExpiry` が無いことを確かめた（あれば A・B の「届いた」は設定のせい）。
- 陰性対照: C（`refuse`）で届かないこと、D（送り手が `bypassPermissions`）で保留・落ちることを同じ形で見た。陽性対照: A・B・E で、届いたら子が本文をファイルに書く（B は `default` で書く操作が拒否されたが、本文を引数に持つ Bash の `tool_use` が出力に在る）。
- 観測窓: 子はターンを閉じて背景の `sleep 300` を待っている間に受けた。ツールの呼び出しの最中は見ていない。C の送り手（この会話）への拒否の知らせは、送ってから約 7 分後（子が終わった後）にこの会話に入った——ターンの途中だったので、いつ届いていたかは分けていない。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1039-child-sendmessage`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1039`・起点 `52d73bc3`・base `origin/main` = `52d73bc36861fd90c59a10ab65ab949d20e96ec5`
- 割り目（手順 4）: 訊かなかった——利用者は「続けて」と言い、同じセッションで続けた（記録として残す。AskUserQuestion は出していない）
- 1 パス目の関門に渡した起点（指摘対応の起点）: `8a3c97ec11b93a780a9e43dd8a07e3c171677c38`
- Verifier 1 パス目（sonnet・`dev-loop:dev-loop-verifier`）: 反証 0 件・所見 2 件（V-A1・V-A2）
- `/code-review` 1 パス目（high）: 指摘 8 件（CR1〜CR8）。直す 4 件（CR1・CR2・CR6・CR7）・残課題 4 件
- 手順 4 への差し戻し: なし（反証 0 件）
- 2 パス目: 未（指摘対応の差分があるので回す。残っているのは Verifier の当て直しと `/code-review` 2 パス目の両方）。指摘対応の終点 `5cb404ff5e8a428cda9ae3fe20203db1f4b6a01e`（1 パス目の指摘対応のコミット。2 パス目の関門に渡す base は周の base のまま）
- 割り目（2 パス目の前）: 2026-11-16 に AskUserQuestion で訊き、利用者は「ここで割る」を選んだ。PR #1077（draft）
- Verifier 2 パス目（sonnet・`dev-loop:dev-loop-verifier`・base `52d73bc3`）: 反証 0 件・所見 2 件（V2-S1・V2-S2）。CR1・CR2・CR6・CR7 の直しは一致。`test-child-cycle.py` 合格（変異 37 件）・`check-plugin-versions.py`・`skill-metrics.py --check` 緑
- `/code-review` 2 パス目（high）: 指摘 9 件（CR2-1〜CR2-9）。直す 1 件（CR2-2）・残課題 8 件
- 2 パス目の指摘対応の起点（狭いパスの起点）: `d193e8d15252723512f8c427885c6a46e9d0f1fd`・終点 `1beb3b306e40f96e48f0263584444a3e92d48f6f`（`check-all.py` 81/81 緑の後にコミット）
- 狭いパス（sonnet・`d193e8d1`→`1beb3b30`）: 反証 0 件・所見 1 件（NP-1。人間が決める）。素通りした変異: なし（文書の修正のため、変異の代わりに食い違い・言い過ぎを独立に探した）
- 外部レビュー: 該当なし（`external-reviews.py` が 3——`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い）
- 実験: あり（交絡の潰し方は上の「実験の交絡」）

## 既知の限界・決着済みの論点

1. **子に `crossSessionInbound: accept` を渡すか**——渡さない。渡せば親が `bypassPermissions` でも届く（E）が、権限確認を飛ばすどのセッションの指示も子に届くようになる。起動口は子の `bypassPermissions` を拒む（cruise は権限を広げない）のと同じ理由。親が `bypassPermissions` なら宛てられない周として扱う。
2. **台帳の `agent` の形**——`claude-p:<記録のパス>` のまま変えない。宛先は記録の `peer` から `status` で引く（台帳の書式と `ledger.py` を変えずに済む）。

採否の表:

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: `status` の保留のまとめが `message_uuid` を辞書の鍵にし、文字列でない値で `TypeError` で落ちる（終了コード 1 = 走っていると読まれる） | 示せる——レビューが `message_uuid: ["a"]` の試料で `TypeError` を再現し、文字列の試料で 0（陽性対照） | 3（既存の「どんな値でも落ちずに」を壊さない） | 直す |
| CR2: 「`auto`・`default` など権限確認を飛ばさないモードなら届く」「子はいつもこちらの側」が、測った組（対話の親 `auto` → 子 `auto`・`default`）を越える。D は送り手の `-p` と `bypassPermissions` を分けていない | 示せる——文と表（A〜E）の突き合わせ | 2（記述が実測と一致） | 直す（測った範囲まで弱めた） |
| CR3: 同じ名前の扱い（docstring は「短い印を足して並べる」、child-process.md・parallel.md は「2 行以上」）が食い違い、どちらも測っていない | 示せない——同じ名前の 2 体は観測していない。`ListAgents` は各行に `[ref]` を付けて並べるので、2 つの記述は同じことを言っていると読める | 無し | 残課題 |
| CR4: 親が `bypassPermissions` かどうかを送る前に決める形で、送った後に保留を確かめる段が無い | 示せない——`bypassPermissions` の cruise の親は観測していない（親は自分のモードを知っている） | 無し | 残課題 |
| CR5: 宛先の名前がリポジトリを含まず、別のリポジトリで同じ台帳の名前・番号の cruise が並ぶと同じ名前になる | 示せない——起きた記録が無い | 無し | 残課題 |
| CR6: 「`--bare` の子はソケットを開かない」が測っていないのに実測の形で書いてある | 示せる——表に `--bare` の行が無い | 2 | 直す（公式ドキュメントの言としたうえで「測っていない」と書いた） |
| CR7: 名前の無い古い記録の子を「どの行か決められない」とした理由が、記録の pid とソケットの名前の対応を見ていない | 示せる——同じ節に子のソケットが `<pid>.sock` だったと書いてある | 2 | 直す（`ListAgents` の行が pid を出さないこと・対応は確かめていないことを書いた） |
| CR8: 保留の行が状態に依らず「期限で落ちる」と言う | 示せない——観測した状態は held → dropped だけで、落ちなかった形は無い | 無し | 残課題 |
| V-A1: `message_uuid` の無いイベントは held と dropped を別々に数える | 示せない——実測では付いていた | 無し | 残課題 |
| V-A2: 最初のイベントの `from_name` が無く後にあるとき、名前を後から埋めない | 示せない——実測では held 側に名前がある | 無し | 残課題 |
| V2-S1（2 パス目）: `dialogExpiry` の「既定 5 分」は一次ソースで確かめていない（D で約 5 分で落ちた・設定が無いことからの読み） | 示せない——値が違う証拠は無い | 無し | 残課題 |
| V2-S2: 「親が `bypassPermissions` なら宛てられない」は測った `-p` の送り手からの一般化 | 示せない——安全側の扱い | 無し | 残課題 |
| CR2-1: `SendMessage` の道具の説明は「送り手と違うモードのセッションは保留する」と言い、`parallel.md` の 2 が宛てられないとするのは `bypassPermissions` の親だけ。`auto` の親と `acceptEdits`・`plan` の子では「知らせた」と書いて実は届かない | 示せない——その組は測っていない（B は `auto` → `default` で届き、道具の説明の字面とも食い違う）。届かなくても 3 で `STALL` 後に止める道は同じで、違うのは `note` の文言 | 無し | 残課題（#1079 に起票） |
| CR2-2: 子から親への返事を測っていないのに、`child-process.md` は「届いたかは子の返事で見る」と書き、「確かめていないこと」は `/clear` 後の親しか挙げない | 示せる——表 A〜E の子はどれもファイルに書いただけで、`SendMessage` を返していない | 2 | 直す |
| CR2-3: 送った `to` の形（素の名前か `[ref]` か）と、D・E の送り手を `bypassPermissions` にした方法が記録に無い。同じ名前の in-process の体があれば素の名前はそちらが勝つ | 示せる（記録に無い）——ただし不変条件 1 が求める項目（版・子の起動引数・`ListAgents`・届いたか）の外。「素の名前を渡す」は道具の説明が一次ソース | 無し | 残課題 |
| CR2-4: 子が宛てられるようになったのに、子への委譲文に、届いたメッセージの送り手を確かめる手立てが無い（予測できる名前に他のセッションが `holders` の形の行を送れる） | 示せない——なりすましは観測していない。委譲文は「触らない」と決めた | 無し | 残課題（#1078 に起票） |
| CR2-5: `seen["cause"] = seen["cause"] or h.get("cause")` を消しても全テストが緑 | 示せない——読んだだけで走らせていない。最初のイベントに `cause` が無い形は観測していない | 無し | 残課題 |
| CR2-6: `status` が記録の `peer` の型を確かめない | 示せない——手で壊した記録でしか起きない | 無し | 残課題 |
| CR2-7: 保留の行を `clip`（300 字）で切るので、メッセージが多いと後ろが落ちる | 示せる——6 件で末尾の注意が切れた（scratchpad の `f7.py`）。件数と各メッセージは残り、7 件以上で後ろのメッセージが切れる。1 体の子に 7 件送る形は観測していない | 無し（3 は件数と各メッセージの状態を出すことで、6 件までは満たす） | 残課題 |
| CR2-8: Fixes のコミット `1941e1a1` のメッセージが「親子とも auto/default なら届く」と言い過ぎている（CR2 で文書からは外した） | 示せる——コミットメッセージ。成果物ではない（関門は記録を検査しない） | 無し | 残課題（squash の本文で直す） |
| CR2-9: テストが同じ記録を 4 回読み直し、宛先の行を 2 度見る | 示せない（片付けの提案） | 無し | 残課題 |
| NP-1（狭いパス）: 追記の「`STALL` の後に止める」は `parallel.md` の 3 の他の条件（`holders` に同じ pid が出続ける・D5 の照合）を省いている（「3 のとおり」と指してはいる） | 示せない——誤読の実例は無い | 無し | 人間が決める |

## 起票

- この周の起票: 2 件（#1078——CR2-4 の送り手の確かめ、#1079——CR2-1 の未測定のモードの組。手順 8 で利用者が承認、2026-11-16）
