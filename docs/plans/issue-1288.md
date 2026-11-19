# Issue #1288 — test-check-all.py の cache_interrupt が負荷のもとで 60 秒の時間切れになる

cruise #1290（`--absent`。2026-11-19 の起動）の子として回す周。台帳は書かない（親だけ）。

## 周の在り処

- ブランチ: `issue/1288-cache-interrupt-timeout`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1288`
- 起点: `f80dc8d1`（origin/main）
- base（参照の名前と SHA）: `origin/main` = `f80dc8d11fdc59e6f66b095c2d92a9e54dea77f7`
- 割り目: 割らない（cruise の周）

## 線（cruise #1290 の台帳の確かめた線）

- 直す線: 既定（出所: cruise の台帳の確かめた線）
- 仕様の穴: 推奨で決めて起票／マージ: 関門を通ればマージ／周の途中の課題: 外に出す／マージ前の判断: 推奨で決めて起票（古い値）

## 原因の調べ（Issue 本文は「原因は確かめていない」）

- 負荷だけでは再現しない: CPU 28 コアに 84 本の空回りを張った状態で `cache_interrupt` を 3 回回し、どれも 1.1 秒前後で終わった。
- **SIGINT が無視された環境から起こすと再現する**: `signal.signal(SIGINT, SIG_IGN)` した親から exec で起こす（無視は exec をまたいで残る）と、
  内側の `check-all.py` は KeyboardInterrupt を受けず、`t-slow.py` の `sleep(60)` と残りを走り切り、`cache_interrupt` は 60.8 秒かかった
  （待ちの 60 秒とほぼ同じ。負荷が少しでも掛かれば `proc.wait(timeout=60)` を超える）。
- 実際の失敗した回が SIGINT 無視の環境（バックグラウンド起動など）だったかは、その回の記録が無く確かめていない（推定）。
  再現した形が Issue の形（`proc.wait(timeout=60)` の時間切れ・単独では通る）と合うところまでしか言えない。

## 変更範囲

触る:
- `scripts/test-check-all.py` — `cache_interrupt` が子の SIGINT を既定に戻して起こす。SIGINT 無視の親から起こす陽性対照の段を 1 つ足す
- `docs/plans/issue-1288.md` — この計画

触らない:
- `scripts/check-all.py` — 本体は SIGINT が無視されていれば中断を受けないのが Python の既定で、無視を外すのは本体の仕事ではない（Ctrl-C を意図して無視した起動を勝手に外さない）
- `plugins/` — 触らないので版は上げない

- 周の大きさ: 同じ規範を述べる箇所の数 = 1（テストの 1 関数と契約の 1 段）。分けない理由は要らない。
- 増やす変更と減らす変更: 増やすのは契約の 1 段だけ、減らすものは無い。
- 版の上げ方: 上げない（`plugins/` を触らない）。
- 依存の追加・更新: なし
- 仕様の振る舞い: spec-loop の正本は無いリポジトリ（本リポジトリは正本ではない）。変えない
- 生成物: 生成物なし（図・SKILL.md の測定値・カタログのどれにも触れない）
- 形式検査のモデル: なし

## 受入基準

不変条件: 「`cache_interrupt` は、中断の信号が届く環境でも届かない環境（SIGINT を無視した親）でも、起こしたテストの SIGINT の扱いに依らず、中断を契約として確かめる」。
経路: (1) 通常の環境（親が SIGINT を既定で持つ）／(2) SIGINT を無視した親から起こす（バックグラウンド起動の形）／(3) 契約の中の他の段（記録の書き・消し）への影響。
この環境で証明できないもの: 失敗した本物の回が SIGINT 無視の環境だったこと（記録が無い）。

| 番号 | 基準 | 証明手段 |
| --- | --- | --- |
| A1 | 親が SIGINT を無視していても、`cache_interrupt` は 30 秒以内に終わる（修正前は 60 秒超） | 契約の新しい段（`test-check-all.py` が回す）と、修正前の版を当てた陽性対照 |
| A2 | 通常の環境では今までどおり中断を確かめ、記録を書きも消しもしない（A5 の段が緑のまま） | `test-check-all.py` 全体 |
| A3 | 起こす側が自分の SIGINT を無視するのは起こす間だけで、戻す（テストの後続が Ctrl-C を受けられる） | コードを読む（`finally` で戻す）と `test-check-all.py` |
| A4 | `check-all.py` 全部が緑（歯止めと回帰テスト） | `check-all.py` |

## 関門の進捗（再開点）

- 実装を終えた。割らない（cruise の周）。1 パス目の関門はこれから。

```dev-loop-gates
周の base: f80dc8d11fdc59e6f66b095c2d92a9e54dea77f7
```

## 既知の限界・決着済みの論点

- 本体（`check-all.py`）が SIGINT 無視を外さない件: 採らなかった。Python の既定で、バックグラウンドで意図して無視された起動を本体が勝手に解くべきでない。

## 手順 8 の記録

- この周の起票: 0 件
