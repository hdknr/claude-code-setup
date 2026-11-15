# Issue #1040 — check-all.py: 1 本ごとの所要時間と上位の一覧を出す

素の `/dev-loop:dev-loop 1040`（cruise の子ではない。本文先頭の `<!-- dev-loop: 親 #1038 -->` は親の印）。利用者は居る。
spec-loop から来た Issue ではない（`spec-loop-handoff` の印は無い）。`作り直しの元:` の行も無い。

直す線: `既定`（出所: 手順 3 の回答。2026-11-15）。

**利用者の指示（2026-11-15、周の途中・手順 2 の時点）**: 重い検査（`check-all.py`）は cruise の `run-serial.py` 越しに回す——
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.108.0/skills/cruise/scripts/run-serial.py -- python3 scripts/check-all.py`。
cruise の 3 周と同じ列に並べ、同時に走らせない（#493 の形の偽の失敗と、cruise の周を遅らせることを避ける）。
**サブエージェント（Verifier・`/code-review`）にも同じことを伝える。**

## 変更範囲

触る:

- `scripts/check-all.py` — 1 本ごとの所要時間（行の末尾）と、集計の上位・全体の壁時計。docstring に時間の取り方
- `scripts/test-check-all.py` — 契約 11（所要時間の欄・上位・全体）と変異
- `docs/plans/issue-1040.md` — この計画

触らない:

- 判定（終了コード・失敗の数え方・`SKIP`）——変えない
- CI（`plugins.yml`・`docs.yml`）——CI は `check-all.py` を呼ばない
- `CLAUDE.md` の `check-all.py` の 1 行の説明（所要時間を述べていない。述べる必要も無い——docstring を正とする）
- 上位の検査そのものを速くすること（Issue の範囲の外）

依存の追加・更新: なし
仕様の振る舞い: 該当なし（このリポジトリは spec-loop の正本ではない）

複製の数: 「時間の取り方」を述べる箇所は `check-all.py` の docstring の 1 箇所。テストの契約は docstring ではなく出力の形を見る。プラグインは触らないので版は上げない。

## デプロイ経路

main へのマージ。`scripts/` は配布物ではない（手元で回す入口）。公開サイトは `docs/plans/` を含めて再ビルドされる。

## 受入基準（不変条件 × 経路）

入口: `check-all.py` の `main` が結果を出す経路——歯止めのループ・回帰テストのループ・SKIP（base が無い）・`--guards-only`・`--jobs 1`／並列・打ち切られた子（負の終了コード）・中断（KeyboardInterrupt）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| T1 | `OK` と `FAIL` の各行に、その 1 本の所要時間（壁時計の秒）が出る | 歯止めのループ／回帰テストのループ／FAIL の行 | 両ループで同じ書式。契約 11 が全 OK/FAIL 行に秒の欄を要求 |
| T2 | 所要時間は「その子を起こしてから終わるまで」で、プールの順番待ちを含まない | `--jobs 1`（後ろの子が前の子の時間を背負う） | 作業者のスレッドの中で `run` の前後を測る。契約 6 の直列の回で、先に時間切れで落ちる `par-a` より後の `par-b` が短いことを要求 |
| T3 | `SKIP` の行には時間を出さない | base が無い SKIP／`--guards-only` | SKIP の行は今の書式のまま。契約 11 |
| T4 | 集計に、所要時間の長い順の上位（5 本。OK と FAIL の両方）と全体の壁時計の秒が出る | 上位の並び・本数・FAIL を外す・全体を出さない | 契約 11（降順・本数 = min(5, 回した本数)・遅い 2 本（OK と FAIL）を含む・上位の値が行の値と一致・全体 ≥ 1 本の最大） |
| T5 | 判定（終了コード・「失敗 N」・FAIL の行の数・SKIP の数え方・落ちたものの名指し）が変わらない | 既存の全経路 | 既存の契約 1〜10 を期待値を変えずに通す。既存の変異が全部捕まる。追加の行が `  OK  `／`  FAIL`／`  SKIP` で始まらない（`order`・FAIL の行の数え方に混ざらない） |
| T6 | `test-check-all.py` に回帰テスト（変異テストを含む） | — | 変異を足し、全部捕まる |
| T7 | 実際に 1 回回した上位の一覧を PR に貼る。他の重い検査が走っていないときに測る | cruise の 3 周と並行 | `run-serial.py` 越しに回す（利用者の指示）。枠を取った後でも別セッションの軽くない処理が走りうるので、測った時刻と `uptime` の負荷を併記する |
| T8 | docstring に時間の取り方（起動から終了まで・SKIP は出さない・並列のときは取り合いを含む）を書く | — | docstring |

**検証で証明できるもの**: T1〜T6・T8。
**この環境では証明できないもの（未証明）**: T7 の「負荷の下の数字ではない」——枠（run-serial）は同じリポジトリの `check-all.py` 同士しか並べない。別リポジトリ・別の重い処理が同時に走っていないことは、測った時点の `uptime` を添えるところまでしか示せない。

**生成物**: 無し（`skill-metrics.py` は `SKILL.md` の節構造から作る——触らない。図も触らない）。

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。run-serial の指示も 4 つに渡す。

## 未解決の判断・確認待ち

- 無し

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1040-check-all-timings`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1040`・起点 `902bc79`・base `origin/main` → `902bc79d136a73a5c9275a1aa85ddc00dc919318`
- 関門: まだ
- 反証・差し戻し: まだ
- 交絡を潰した手順: まだ

## 既知の限界・決着済みの論点

（まだ無し）
