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

## 既知の限界・決着済みの論点

- `holders` は `--repo` を取らない（決着: 採らない。理由: 親の見張りはメインの作業ツリーから呼ぶ。外から呼べば 125 で場所を名指しする）。
- `--repo` が指すのが周の対象のリポジトリかは見ない（決着: 採らない。理由: 指した先の枠で数えるだけで、権限は広げない）。
