# Issue #1021 — test-check-deps-declared.py が直列に 31 回の契約を回し、check-all.py の律速になる

## 変更範囲

触る:

- `scripts/test-check-deps-declared.py` — 契約を逐次評価（ジェネレータ）にして変異の回を最初の失敗で止める・変異を `--jobs` で別プロセスに並列に当てる・土台のリポジトリを形ごとに 1 度だけ作って複製する
- `scripts/check-all.py` — `NESTED` に足して親の半分の `--jobs` を渡す（docstring の本数）
- `scripts/test-check-all.py` — 入れ子に `--jobs` を渡す回帰テストの対象に足す
- `docs/plans/issue-1021.md` — この計画

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/check-deps-declared.py`（テスト対象の本体。挙動は変えない）
- 契約のケースと変異の中身（判定の意味を変えない）

依存の追加・更新: なし

## 受入基準

- 陽性対照の 46 ケースが全部通り、変異 30 個が全部捕まる
- 所要が改善前より縮んだことを同じ機械で測る
- `--jobs 1` で変異が 1 つずつになる（`--pool-size` の自己検査）

## 実測

（下に追記）
