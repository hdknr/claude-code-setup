# Issue #1052 — test-outer-loop.py: 変異を別々のプロセスで並列に当てて速くする

cruise（親 Issue #1056）の子として回す周。**不在の周**（出所: `/dev-loop:cruise 1056 --absent` の起動・2026-11-15T08:58Z）。AskUserQuestion は使わない。
spec-loop から来た Issue ではない。`作り直しの元:` の行も無い。`find-cycle.py 1052` は親の委譲文（`.claude/plans/cruise-issue-1056-children/d1052.md`）だけに当たった
——計画・ブランチ・worktree・コミットは無く、新規の周。

台帳の確かめた線（出所: 利用者の確認（起動時・2026-11-15T08:58:13Z、配布を見せて確かめた））:
直す線 = `既定` / マージ = 関門を通ればマージ（**子はマージしない**——PR 側の CI まで）/ 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。仕様の穴・実機確認の線は無い（既定 = 止まる）。

直す線: `既定`（出所: cruise の確かめた線）。

**単独で回す周**（受入基準が単独で回した所要時間の前後を測る）。重い検査は `run-serial.py` 越しに回す——
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.108.0/skills/cruise/scripts/run-serial.py -- <コマンド>`。関門にも渡す。

## 変更範囲

触る:

- `scripts/test-outer-loop.py` — 変異（と陽性対照の本体）を別々のプロセス（`--observe`）で並列に観測する。`--jobs`（上限 4）・`--pool-size` を受ける
- `scripts/check-all.py` — `NESTED` に足す。docstring とコメントの本数・列挙
- `scripts/test-check-all.py` — 契約 9 の「変異を同時に当てる回帰テスト」に足す。コメントの本数
- `docs/plans/issue-1052.md` — この計画

触らない:

- 本体 `plugins/dev-loop/skills/cruise/scripts/outer-loop.py`（Issue の「範囲の外」。プラグインは触らないので版も上げない）
- `MUTATIONS` の中身・試料（`scenario()`）の入力と期待
- **Issue の 2 つ目の手（試料の台帳づくりを `ledger.py` の関数の直接呼び出しに替える）**——CLAUDE.md の「台帳は本物の `ledger.py` で作る」との整合が決まっていない。不在の周なので手を付けない（範囲の外）
- CI（`plugins.yml`）——引数なしで回す行のまま
- `CLAUDE.md` の `test-outer-loop.py` の行（#1050・#1051 と同じく触らない）

依存の追加・更新: なし
仕様の振る舞い: 該当なし（このリポジトリは spec-loop の正本ではない）

版の上げ方: 上げない（`plugins/` を触らない）。

複製の数: 「`NESTED` に入っている回帰テスト」を列挙・数えている箇所が 4 つ——`check-all.py` の docstring（列挙と「`NESTED` の 7 本」「6 本のテスト」）・`NESTED` の上のコメント（「回帰テストの 6 本」）・`NESTED` の値・`test-check-all.py` の契約 9（コメントと `nested_tests`）。
分けない理由: 1 本足すと 4 箇所が同時に動き、片方だけ直すと `test-check-all.py` が赤になる——同じ周で揃える（#1050・#1051 と同じ形）。

形は `test-autopilot-loop.py` の `--observe`（変異ごとに自分のテンポラリと環境を持つ子プロセス）と、`test-parallel-stop.py` の `--jobs`・`--pool-size`（上限 4）。

## デプロイ経路

main へのマージ。`scripts/` は配布物ではない。公開サイトは `docs/plans/` を含めて再ビルドされる（このマージでは子はマージしない）。

## 受入基準（不変条件 × 経路）

入口: テストを起こす経路——`check-all.py`（`NESTED` から `--jobs <親の半分>`）・CI（`plugins.yml` の引数なしの `run:`）・手で（引数なし・`--jobs N`）。
中で: 本体のままの回（このプロセスの中・全 check）・陽性対照（壊さない本体を別のプロセスで観測）・変異 35 本（Issue は 18 本と書くが、いまの `MUTATIONS` は 35 本——「全部」をいまの数で読む）・後片付け。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 変異の全部（35 本）を今までどおり捕まえる。本体のままの回は全部緑 | 並列化（観測の取り違え・同じ場所を使う）・別のプロセスの観測の形が変わる（JSON の往復で tuple が list に）・読み込めない／観測できない変異を殺せたと数える | 変異ごとに子プロセスが自分のテンポラリ・`HOME`・`PATH` を持つ。比べるのは JSON の往復でそろえた観測どうし。**陽性対照**: 壊さない本体を同じ経路（別のプロセス）で観測し、このプロセスの観測と一致すること。読み込めない・観測できない変異は「当てられなかった」で失格 |
| A2 | `--jobs N` を受け、プールに渡す作業者は `min(N, 上限 4)`。`--jobs 1` で 1 つずつ（直列）。`--jobs 0` は断る | 受けた値を使わない（遅い・速いだけで緑のまま） | `--pool-size` で自分を起こして作業者の数を見る（`test-parallel-stop.py` と同じ形） |
| A3 | `check-all.py` が `--jobs <親の半分>` を渡す（`NESTED`）。ほかの回帰テストには渡さない | `NESTED` に足し忘れ・列挙の写しの片方だけ | `test-check-all.py` 契約 9 の `nested_tests` に足す（足し忘れると赤） |
| A4 | 本物の `claude` を起こさない（偽の `claude` を `PATH` の先頭に置き、本物の `claude` がある `PATH` の項を外す）が、並列にしても保たれる | 子プロセスが親の素の環境（本物の `PATH`）を受け継いだまま `isolate_env` を通らずに観測する・子同士で `FAKE_HOME` を共有する | 子プロセスは `--observe` の入口で必ず `isolate_env`（自分のテンポラリの `home`）を通ってから本体を読み込む。陽性対照として、観測の中で偽の `claude` が起動を記録していること（S1 の起動 2 件など——観測に入っている）と、本物の `claude` の在る項が子の `PATH` に無いことを確かめる |
| A5 | 単独で回した所要時間の前後を PR に貼る（時刻と `uptime` を併記する） | 負荷の下の数字 | run-serial 越しに、前（main の形）と後（このブランチ）を回す。直前・直後に `uptime` と `run-serial.py holders` |
| A6 | 実リポジトリを触らない | 子プロセスの観測 | 子も `assert_not_real_repo` を通るテンポラリのリポジトリで走る（今と同じ `scenario()`） |

**検証で証明できるもの**: A1〜A4・A6。
**この環境では証明できないもの（未証明）**: A5 の「負荷の下でない」——run-serial が並べるのは同じリポジトリの検査どうしだけで、別のセッションの負荷は外せない。時刻と `uptime` を添え、満たしたとは書かない。
**生成物**: 無し（`skill-metrics.py` の生成ブロックは `SKILL.md` を触らないので動かない）。

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。run-serial の指示も渡す。

## 未解決の判断・確認待ち

- 無し

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1052-outer-loop-jobs`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1052`・起点 `b8dd370`・base `origin/main` → `b8dd370e3012f900f21338822d191ff97ea39a80`
- 割り目 1（手順 4 の後）: 割らない（cruise の周）
- 交絡: 実験は所要時間の前後の測定だけ（A5）。主張は「前後の秒」までで、負荷を外したとは言わない

## 既知の限界・決着済みの論点

- Issue の 2 つ目の手（台帳づくりを関数の直接呼び出しに）は採らない——CLAUDE.md の「台帳は本物の `ledger.py` で作る」との整合が未決。範囲の外（不在の周の委譲文の指示）
- 本体のままの回はこのプロセスの中で先に 1 回走らせ（全 check の材料）、その後に陽性対照と変異をプールで回す——本体のままの回をプールと同時に走らせると `--jobs 1` で直列にならない
