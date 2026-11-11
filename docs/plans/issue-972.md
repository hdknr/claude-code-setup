# Issue #972 — tree.md: 機能一覧の id が中間表現に無いときの案内が removed.csv を指し、scaffold が止まり続ける

不在の周（`/dev-loop:cruise 963 --absent` の起動・2026-11-11T01:02Z、利用者の確認（起動時・2026-11-11T01:02:52Z、配布を見せて確かめた））。cruise #963 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かない）。従う版は dev-loop 1.103.0（キャッシュ。SKILL.md 1861 行）。
元の Issue の本文の先頭は `<!-- cruise-found: #963 -->`（#957 の周の関門 `/code-review` 1 パス目 CR5 が見つけた課題。世代 1）——周の途中の課題は found-lines.md の「後続の後続」のとおり、3 つに当たらなければ記録だけ。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-963`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は親が立てる）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- マージ前の判断: **推奨で決めて起票**（出所: 同上。子は推奨と理由を PR コメントに書き、確認の Issue は立てない）
- 実機確認: 台帳に線なし
- 版の上げ方: **patch・spec-loop だけ**（main の先端 spec-loop 0.78.0 → 0.78.1。記述の誤りの修正——従うと誤った操作になる手順の記述）。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方（patch）で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #972`・`Refs #963`
- 並行する周: #950（spec-loop。版と `references/tree.md` が衝突しうる）・#965（別の worktree。触らない）
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/cruise/scripts/run-serial.py` 越し

## 周の在り処

- ブランチ: `issue/972-tree-function-list-guidance`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-972`
- 起点コミット: `29d3324e`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `29d3324e90211311174b3da99023947c4f9de805`

## 変更範囲

触る:
- `plugins/spec-loop/references/tree.md` — 「機能一覧と中間表現の照合」の、一覧の id が中間表現に無いときの案内
- `scripts/test-scaffold.py` — 案内どおりにすると止まらないこと・旧い案内の形では止まることの試料
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-972.md` — この計画

触らない:
- `plugins/spec-loop/scripts/scaffold.py` の止まるときの文言（「中間表現に書き起こすか、一覧から外す」）——removed.csv を指しておらず誤りではない。外し方は tree.md が原本
- `versions.md`——重ね方（一覧はファイルの単位）は既に正しく書いてある。tree.md から指すだけ
- `spec-ir.md` の `id` の行——照合で止まることを述べて tree.md を指すだけで、外し方を写していない

複製の数（同じことを述べている箇所）:
- 「一覧の id が中間表現に無いときの手当て」は `tree.md` の **1 箇所**（`scaffold.py` の文言は「一覧から外す」まで、`spec-ir.md` は tree.md を指すだけ——grep `一覧から外す`・`features.csv` で確かめた）。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージでプラグインのカタログに入る（`docs/plans/` は公開サイト）。マージは親。

## verify の受入基準

不変条件 × 経路:

A. **tree.md の案内どおりに一覧から外すと、scaffold が止まらない**（Issue の受入基準）
  - A1. 案内が、作業中の版の `requirements/features.csv` に行を除いた一覧を置き直す手順を書き、`removed.csv` で消す手順を書かない（`removed.csv` の `機能` の行では一覧の行が外れないことを書く）
  - A2. 試料: v1 に機能一覧（F-001・F-002）と中間表現、v2 で `removed.csv` に `機能,F-002` を書き、v2 に F-002 を除いた一覧を置く——`scaffold.py` が 0 で作り、機能一覧の照合で止まらない（撤去の本文が F-002 だけ）
  - A3. 陽性対照: 同じ試料で一覧を置き直さない（旧い案内の形）——`scaffold.py` が 1 で `F-002: 機能一覧（…）の機能が中間表現に無い` と止まり、何も書かない
  - A4. 案内の各文の真偽（文面が主張する事実）——「一覧はファイルの単位で重なる」（`versions.md`・`merge-versions.py`）・「`removed.csv` の `機能` は中間表現の機能を消すだけ」・「両方要る」が実物どおりか
  - A5. 他の入口——v1 だけの正本（版が 1 つ）で一覧の行を外す・`--check`・`--dry-run`——で案内が誤った操作にならない（v1 は作業中の版の一覧を直すことになる）
B. **版の 3 箇所の一致と、歯止めの全部**——`check-plugin-versions.py`・`check-all.py`（run-serial 越し）が緑、PR 側の CI が緑

必須要件の掛け算: 受入基準を両方の関門に × 1 パス目・2 パス目 = 4 つの受け渡し（2 パス目が該当なしなら初回の 2 つ）。

証明できないもの（未証明）: 無し。

生成物: **該当なし**——drawio を触らない。`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` の測定で、spec-loop の SKILL.md は版の 2 行だけ（`check-all.py` の `skill-metrics.py --check` で併せて確かめる）。

## 未解決の判断・確認待ち

- 無し（仕様の穴ではない——正しい手順は重ね方の決まりから決まる）。

## 関門の進捗（再開点）

- 割り目（手順 4）: 割らない（cruise の周）
- 著者の確かめ（実装の直後）: `test-scaffold.py`（run-serial 越し）——試料 391 件・変異 320 件で緑。足した 2 件: A3 の形（一覧を置き直さない）は 1 と `F-002: 機能一覧（build/merged/requirements/features.csv）の機能が中間表現に無い` で何も書かない、A2 の形（v2 に F-002 を除いた一覧）は 0 で撤去の本文が F-002 だけ
- 1 パス目: 起動（Verifier（sonnet）・`/code-review`）。1 パス目の指摘対応の起点: 下のコミット（この行を足したコミット。関門に渡した時点の HEAD）

## 既知の限界・決着済みの論点

- 無し（1 パス目の前）。
