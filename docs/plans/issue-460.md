# Issue #460 — check-all.py が check-mutation-claims.py を既定の並列数で起こし、入れ子で N×N になる

`check-all.py` は既定で CPU の数（N）だけ並列に回し、その中で `check-mutation-claims.py` を**引数なし**で起こす。
`check-mutation-claims.py` の `--jobs` の既定も CPU の数なので、その中の `red` は親の残り N-1 本と、
作業者 N 人ぶんの `red`（陽性対照と変異）と CPU を取り合う。#449 で `red` が 300 秒の打ち切りに届いた（3 回中 2 回）。

## 変更範囲

触る:

- `scripts/check-all.py` — `check-mutation-claims.py` を起こすときに `--jobs` を渡す（値は親の `--jobs` から決める）。docstring の並列の節
- `scripts/test-check-all.py` — 渡した `--jobs` を観測するケースと、その変異
- `docs/plans/issue-460.md` — この計画

触らない:

- `scripts/check-mutation-claims.py`（既定の並列数・`TIMEOUT` は変えない。単独で回すときは CPU の数のままでよい）
- `scripts/test-check-mutation-claims.py`（中で `check-mutation-claims.py` を既定の並列で起こすが、当てる木の `red` は軽い試料だけ）
- CI のワークフロー（CI は `check-mutation-claims.py` を単独のステップとして呼ぶ——入れ子にならない）
- `CLAUDE.md`（`check-all.py` の行は並列の細部を docstring に預けている。`check-mutation-claims.py` の行の「既定は CPU の数」は単独で回すときの話で、偽にならない）

### 同じことを述べている箇所の数

入れ子の並列数を述べる箇所: `check-all.py` の docstring（並列の節）と `GUARDS` の注記の 2 箇所。
`CLAUDE.md` の 2 行は単独のときの既定を言うだけで、入れ子の値は持たない（上）。同じファイルの中なので分けない。

## 乗るデプロイ経路

`scripts/` だけ。プラグインの中身は変えないので版は上げない。公開サイトにも載らない——**反映経路なし**。

## 周の在り処

- ブランチ: `issue/460-nested-mutation-jobs`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-460`
- 起点: `43b5832`（start-point `origin/main`）
- base: `43b58324945badf38de0c481ebc64e62f44e9339`

## 受入基準

不変条件:

1. **`check-all.py` の中の `check-mutation-claims.py` は、親の `--jobs` より多い作業者を起こさない**——
   親の作業者と入れ子の作業者の積が N×N にならない。値は起動の引数で確かめる
2. **`check-all.py --jobs 1` は入れ子まで直列**（`check-mutation-claims.py --jobs 1`）——「`--jobs 1` で直列」が入れ子で破れない
3. **`check-all.py` が全部通る**（`N/N 本を回した（失敗 0）`）
4. **`check-all.py` の wall が大きく悪化しない**——同じツリーで前後を交互に測る
5. **`check-all.py` の既存の観測（並列・直列・中断・収録漏れ）が緑のまま**——`test-check-all.py` が見る

経路（`check-mutation-claims.py` を起こす入口）:

| 経路 | 入れ子になるか | 守り方 |
| --- | --- | --- |
| `check-all.py` の `GUARDS` | なる | `--jobs` を渡す（この周） |
| CI（`plugins.yml`） | ならない（単独のステップ） | 対象外 |
| 人が直接 | ならない | 既定（CPU の数）のまま |
| `test-check-mutation-claims.py`（`check-all.py` の `TESTS` 経由） | なるが、当てる木は試料だけ | 対象外（上の「触らない」） |
| `check-mutation-claims.py` の `red` が `check-all.py` を起こす | 今の主張には無い | 対象外 |

検証で証明できるもの: 1・2（`run` に渡る引数を観測するテストと変異）、3・5（`check-all.py` を回す）、
4（前後を測る。ただし手元の 10 コアの macOS 1 台での値）。

この環境では証明できないもの（**未証明**）: 遅い機械・コア数の違う機械で打ち切りに届かなくなること
（測れるのはこの 1 台だけ）。

生成物: なし（`scripts/` の 2 本は生成物を持たない。図の書き出し・`skill-metrics.py` の生成ブロックは触らない）。

## 未解決の判断

- 渡す値（`1`／親の一部）は前後を測ってから決める

## 手順 8

- この周の起票: 0 件

## 着手前の実測（著者。関門ではない）

（測定中）

## 関門の進捗（再開点）

- 着手: worktree 作成・肯定的な確認済み

## 既知の限界・決着済みの論点

（まだ無い）
