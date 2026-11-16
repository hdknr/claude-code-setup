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

## 起票

- この周の起票: 0 件（起票の候補なし）
