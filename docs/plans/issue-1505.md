# Issue #1505 — cruise: run-serial.py をリポジトリの外の cwd から呼ぶと 125 で失敗する（#1401 の 4）

**不在の周**（出所: `/dev-loop:cruise 1508 --absent` の起動・2026-11-24T02:32Z の再開）。利用者には訊かない。親（cruise #1508）から委譲文で受けた子。
後続に #1506・#1507 がある（この周では手を出さない）。

確かめた線（出所: cruise の確かめた線（台帳 `issue-1508`）。利用者の確認（起動時、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
子はマージしない（親の委譲文）。台帳は書かない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1508`））。
版の上げ方: `dev-loop` を **minor**（2.22.1 → 2.23.0。`--repo` の引数を足す能力の追加）。並行の周（#1453・#1514）が先に上げていたら、マージ直前の取り込みで次の版に上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/run-serial.py` — `--repo <パス>` の引数・枠を決められないときに場所を名指しする理由の行（`locate`）・docstring（使い方・「対象のリポジトリ」の節・終了コードの表・守る／守らない）
- `plugins/dev-loop/skills/cruise/references/parallel.md` — 「重い検査とアプリの起動は、順番待ちに通す」の使い方の行と 125 の項
- `scripts/test-run-serial.py` — 観測 `repo`（外の cwd から `--repo` で worktree を指す）・`cannot` の名指しの判定・`codes` の `--repo` の値なし・変異 3 件
- `plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json`・`plugins/dev-loop/skills/dev-loop/SKILL.md`・`plugins/dev-loop/skills/cruise/SKILL.md` — 版
- `docs/plans/issue-1505.md` — この計画

触らない:

- `holders` の口に `--repo` を足すこと（親の見張りはメインの作業ツリーから呼ぶ。守らないものに書く）
- `--repo` が周の対象のリポジトリかを確かめること（守らないものに書く）
- cruise の `SKILL.md` §4・`prompts/child-cycle.md` の run-serial の行（子の cwd は worktree で、今の書き方のまま走る）
- #1401 のほかの項（#1506・#1507）

依存の追加・更新: なし
仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）

同じことを述べている箇所の数: 4（本体の docstring の「対象のリポジトリ」の節と終了コードの表と「守る」の行・`options` の使い方の文字列、`references/parallel.md` の使い方と 125 の項）。CLAUDE.md の run-serial の行は性質だけで、引数を列挙しないので直さない。
分けない理由: 本体の docstring が原本で、`parallel.md` は使い方を指すだけ。テストが docstring の「守る」の行数と変異の数を突き合わせるので同じ周で直す。

## デプロイ経路

main へのマージで、プラグインの配布（`marketplace.json` の版）と GitHub Pages（`docs/` の計画ファイル）。`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`。子はマージしない。

## 受入基準

採ったもの: Issue の 2 案の**両方**——`--repo <パス>` で外の cwd からでも走らせ、`--repo` を渡さずに外から呼んだら場所を名指しする行を出して 125。

不変条件 × 破りうる経路（入口: CLI `run-serial.py [--timeout] [--repo] -- <コマンド>`・`run-serial.py holders`・入れ子（`DEV_LOOP_SERIAL_HELD`）・cruise の子と関門が委譲文どおりに呼ぶ形（cwd は worktree））:

| # | 不変条件 | 経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| 1 | リポジトリの外の cwd から `--repo <worktree の中のパス>`（相対パス）で呼ぶと、コマンドが走る。枠は指したリポジトリの枠（メインの作業ツリーの持ち主を待つ）で、コマンドは呼んだ cwd で走る | CLI（`--repo`） | 観測 `repo`。周の base の本体では `--repo` が「知らない引数」で 2 になる陽性対照 |
| 2 | `--repo` を渡さずに外の cwd から呼ぶと、cwd のパスと `--repo <パス>` で指すよう言う行を出し、走らせずに 125 | CLI（`--repo` なし） | 観測 `cannot` の「cwd を名指しする」「`--repo` で指すよう言う」 |
| 3 | 名指しの行を落とす変異でテストが落ちる | テスト | 変異「決められない場所を名指さない」 |
| 4 | `--repo` がディレクトリでないなら、そのパスを名指しして走らせずに 125 | CLI（`--repo`） | 観測 `cannot` |
| 5 | `--repo` に値が無い・空なら、cwd のリポジトリへ落とさずに 2（走らせない） | CLI | 観測 `codes` の「`--repo` の値なし」「`--repo=` の空」と変異 |
| 6 | 既存の振る舞い（cwd が worktree・メインの作業ツリー・サブディレクトリなら今までどおり。入れ子・期限・持ち主・宣言の読み方）を変えない | CLI・入れ子・`holders` | 既存の観測が全部緑 |
| 7 | docstring の「守る」の行数と変異の数が 1 対 1 で、どの変異も殺せる | テスト | `test-run-serial.py` |
| 8 | `references/parallel.md` と docstring が同じことを言い、本体の振る舞いと食い違わない | 原本 | 読み比べ |
| 9 | 版が 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本）で揃って上がる | 版 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| 10 | 歯止め全部（`check-all.py`）が緑 | 全体 | `run-serial.py` 越しの `check-all.py` と PR 側の CI |

必須要件の掛け算: 受入基準を両方の関門（Verifier・`/code-review`）に × 2 パス（1 パス目・2 パス目。1 パス目の指摘対応が 0 行なら 2 パス目は該当なし）= 4 つの受け渡し。2 パス目で直した行があれば狭いパスにも受入基準をまるごと渡す。

証明できないもの（未証明）: なし——どれも一時ディレクトリの本物の git リポジトリで走らせて確かめられる。
生成物: なし（`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` の節構造に依るが、この周は版の行だけを変える——`skill-metrics.py --check` で確かめる）。
プロパティテスト: なし（入力は引数の形とパスの種類で、例の試料で覆える。往復・冪等性・数値の境界を持たない）
差分テスト: なし（振る舞いを変えない周ではない——引数を足し、理由の行を変える）

## 未解決の判断・確認待ち

- 仕様の穴: なし（Issue が 2 案を挙げ「どちらを採るかは周で決める」とする。両方を採った——外から呼ぶ子に直す道（`--repo`）と、直さず呼んだときの診断の両方が要る）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1505-run-serial-outside-cwd`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1505`・
  起点 `128c2749`・base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `128c27496b3c46918a8d7864e35f1caa37627e09`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目に渡した（Verifier・/code-review。成果物 `573c978470d55ff0c9179cf2a60fa39ad6e81072`）。1 パス目の指摘対応の起点: `573c978470d55ff0c9179cf2a60fa39ad6e81072`
  - Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet。250 行を読んだと報告）: 反証 0 件。`test-run-serial.py` の全部は順番待ちで完走できず、新しい観測（`--part repo/cannot/codes`）と新しい変異 3 件だけ確かめた。
  - /code-review 1 パス目（high）: 指摘 9 件（採否は下の表）。テストの全部と変異は順番待ちで確かめられなかったと報告。
  - 1 パス目の指摘対応: 直す 2 件（CR1-1・CR1-3）。陽性対照: 新しい判定を起点の本体（`573c9784`）の写し（リポジトリの外・`.git` なし）に当てると `--part repo --part cannot` で FAIL 4 件（holders の勧め・GIT_DIR・守るの行数・守る 66）、直した本体で合格。
- 割り目（手順 6）: 割らない（cruise の周）

## 既知の限界・決着済みの論点

- `--repo` で外の cwd から取った枠の持ち主は、場所に呼んだ cwd が出て、親の「止まっている枠の持ち主」の照らし合わせに当たらない（決着: 採らない——守らないものに書いた。理由: 周の子は worktree から呼ぶので当たる。記録に `--repo` を足すのは別の周。CR1-2）。
- `--repo` を渡さないときは、環境変数の `GIT_DIR` などに従う（決着: 採る——今までどおり。テストの `cannot` が `GIT_DIR` を使っている）。

- `holders` は `--repo` を取らない（決着: 採らない。理由: 親の見張りはメインの作業ツリーから呼ぶ。外から呼べば 125 で場所を名指しする）。
- `--repo` が指すのが周の対象のリポジトリかは見ない（決着: 採らない。理由: 指した先の枠で数えるだけで、権限は広げない）。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1: 外の cwd の `holders` が、取らない `--repo` で指せと勧める | 示せる——外の cwd で `holders` が 125 で勧め、`holders --repo <wt>` は 2（/code-review が再現。著者も起点の本体で新しい判定が FAIL） | 8 | 直す——`holders` には cwd を移すよう言う |
| CR1-2: `--repo` で外から取った枠の持ち主を、親の見張りが台帳の worktree と照らせない | 示せない——`parallel.md` の手順から読んだ形。周の子は worktree から呼ぶ | 無し | 残課題（守らないものに書いた） |
| CR1-3: 環境変数の `GIT_DIR` が `--repo` より先に効き、別のリポジトリの枠で数える | 示せる——`GIT_DIR=rb/.git … --repo ra` で `DEV_LOOP_SERIAL_HELD` が rb の枠（/code-review が再現。著者も起点の本体で新しい判定が FAIL） | 1 | 直す——`--repo` のときは `GIT_DIR` などを外して git に訊く。守る 66 と変異を足した |
| CR1-4: `cannot` が `--repo` のラベルと、ディレクトリだがリポジトリの外の `--repo` を見ていない | 示せない——変異が生き残るという推論で、走らせていない | 無し（4 の名指しは見ている） | 残課題 |
| CR1-5: 権限で入れない `--repo` を「ディレクトリでない」と言う（3.10〜3.13 では traceback） | 示せる——3.14 で `chmod 000` の下を「ディレクトリでない」・125 | 無し（125 で走らせず、パスは名指す） | 残課題 |
| CR1-6: `--repo --timeout 5 -- …` が `--timeout` をパスに食い「知らない引数 '5'」 | 示せる——2 を返す | 無し（2 で走らせない） | 残課題 |
| CR1-7: cwd が消えていると traceback（周の前からある） | 示せる——`os.getcwd()` が FileNotFoundError | 無し（周の前から） | 残課題 |
| CR1-8: 入れ子の呼び出しが `--repo` を引き継がず、外の cwd では 125 | 示せない——コードからの推論 | 無し | 残課題 |
| CR1-9: コミットに `Fixes #1505` が無い | 示せない——PR の本文に書き、squash で閉じる | 無し | 捨てる |
| V1-所見 1〜3（`--repo` 2 回・OSError の分岐に勧めが無い・`--repo --timeout`）: 反証ではない所見 | 示せる（Verifier が実測） | 無し | 残課題（3 は CR1-6 と同じ） |

- 効いた行: R-02
- 効いた行: なし
- 効いた行: R-02
- 効いた行: R-04
- 効いた行: R-02
- 効いた行: R-02
- 効いた行: R-02
- 効いた行: R-02
- 効いた行: なし
- 効いた行: なし
