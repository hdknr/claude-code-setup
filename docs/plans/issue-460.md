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

- 渡す値: **親の半分（少なくとも 1）に決めた**（下の実測）。`1` は wall が延びすぎる

## 手順 8

- この周の起票: 0 件

## 実測（著者。関門ではない）

10 コアの macOS 1 台、2026-10-27。**計測は scratchpad のスクリプトで、他の `check-all.py` がいなくなってから起動し、
走っている間の他の `check-all.py` の数と 1 分平均の負荷を 5 秒ごとに記録した。** `red` の所要は、`PATH` の先頭に
記録だけする `python3` を置いて、退避先（worktree の外）で走った `scripts/test-*.py` を拾った。

| 入れ子の `--jobs` | wall（他の `check-all.py` が 0 本の回） | 最長の `red` |
| --- | --- | --- |
| 既定（10。変更前） | 227.2 / 217.0 / 232.4 / 224.0 / 262.2 秒 | 90.4 / 99.1 秒 |
| 親の半分（5） | 237.4 / 252.3 秒 | 77.4 / 79.4 秒 |
| 1 | 373.1 / 368.0 / 388.1 秒 | 約 64 秒 |

- **変更前でも、他の `check-all.py` が重ならなければ打ち切り（300 秒）には届かなかった**（最長 90 秒）。
  **打ち切りに届いた 1 回（wall 678 秒・`test-worktree-scripts.py` の陽性対照が 300 秒）は、負荷の 15 分平均が 50 の時間帯で、
  別のセッション（`issue-458`）が `check-all.py` を走らせていた**（その回は重なりを記録していないので、重なっていたとまでは言えない）
- **`--jobs 1` は wall が約 +65%** で、受入基準 4 に反する。**親の半分は wall の中央値で約 +8%（227 → 245 秒）で、
  最長の `red` が 90〜99 → 77〜79 秒**。標本は半分が 2 回・変更前が 5 回で、負荷の揺れ（1 分平均 41〜71）の中にある
- 半分の回がもう 1 回あったが、途中で他の `check-all.py` が 2 本重なった（1 分平均 216・wall 457 秒）ので捨てた

捨てた測定（交絡）:

- 入れ子の値だけを変えて、契約（`test-check-all.py`）を新しい版のままにした回——契約が落ちて `test-check-all.py` の主張 4 件が
  陽性対照で止まり、仕事が減った（wall 237 / 227 / 222 秒）。**比べるときは 2 本とも base の版に戻す**
- 最初の数回（678 / 441 / 520 / 459 秒）——他のセッションの `check-all.py` と重なっていたかを記録していなかった
- 1/3 の回——変異の表が式の文字列（`max(1, jobs // 2)`）を名指ししているので契約が崩れ、さらに他の `check-all.py` が 2 本重なった

## 関門の進捗（再開点）

- 周の在り処は上の節。肯定的な確認済み（再開した 2 セッション目でも `issue/460-nested-mutation-jobs` の上・`dfa754b`）
- 実装: `4d460c9`（入れ子を `--jobs 1`）→ `dfa754b`（親の半分。契約を性質で見る）→ `f95df7b`（実測を docstring に）。**実装は完了**。
  `f95df7b` で `check-all.py` 51/51
- 次: 手順 5 の Verifier（1 パス目）から
- 手順 4 の割り目: AskUserQuestion で訊いた → **「ここで割る」が選ばれた**（2026-10-27）
- 手順 5 の Verifier: 未着手 ／ `/code-review`: 未着手
- 交絡を潰した手順: 上の「捨てた測定」。他の `check-all.py` の重なりを記録し、比べる 2 本を base の版に揃えた

## 既知の限界・決着済みの論点

- **他のセッションの `check-all.py` が重なったときの打ち切りは、この周では止められない**——入れ子を絞るのは 1 本の `check-all.py` の中の
  取り合いだけで、セッションをまたぐ取り合いは見えない。決着: 採らない（範囲外）。理由: Issue の受入基準は入れ子の N×N
- **`--jobs 1` は採らない**——wall が約 +65%（上の表）で、受入基準 4 に反する
