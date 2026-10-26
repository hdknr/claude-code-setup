# Issue #447 — test-check-mutation-claims.py: observe_interrupt の「守る 21」が負荷で揺れる

#431（PR #445）のマージ後、main の CI で `check-mutation-claims.py` の主張 `scripts/test-check-mutation-claims.py:827` が
「当てられなかった」になった（陽性対照の `test-check-mutation-claims.py` が「守る 21」で落ちた）。元の周は #431。

## 変更範囲

触る:

- `scripts/test-check-mutation-claims.py` — `observe_interrupt` の中断の送り方（届くまで送り直す・ハンドラは 1 度だけ投げる）
- `CLAUDE.md` — 「並行する周は、同じ版に上げて衝突する」の節に 1 項（Issue の「この周にまとめること」。人間が決めた）
- `docs/plans/issue-447.md` — この計画

触らない:

- `scripts/check-mutation-claims.py`（本体。落ちたのはテストの観測の側で、本体の「守る 21」は正しく動いている——下の実測）
- `observe_interrupt` の `time.sleep(0.2)`（Issue の原因の候補。実測で原因ではなかった——下の「原因の実測」。直し方の案「`stop` を観測で待つ」も採らない）
- `plugins/`（触らないので版を上げない）

### 同じことを述べている箇所の数

- `observe_interrupt` の送り方: その docstring と行内のコメントの 2 箇所（同じ関数の中）。分けない。
- `CLAUDE.md` の 1 項: 1 箇所（新しく足す。同じ話は他に無い）。

## 乗るデプロイ経路

`scripts/` とルートの `CLAUDE.md` はサイトに載らない。反映経路はマージのみ。

## 周の在り処

- ブランチ: `issue/447-interrupt-observe-wait`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-447`
- 起点: `2ff5a69`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `2ff5a69c9b618ac09b05547bda0f37516de240bd`

## 原因の実測（直す前）

試料と手順は scratchpad（セッションと一緒に消える）。`observe_interrupt` だけを単独で、30 本同時 × 20 回 = 600 回回す。
本体は変えず、テストのモジュールの `threading` だけを、`Event.wait` の時間切れと `Barrier` の破れを記録する写しに差し替えた。

- **600 回中 5 回・600 回中 3 回落ちた**（2 回の測り直し）。落ちた回は全部 `judged == [1, 2, 3]`・`raised == KeyboardInterrupt`。
- **落ちた回はどれも 5.27〜5.7 秒かかり、通った回はどれも 1.62 秒以下**——`PARALLEL_WAIT`（5 秒）を待ち切っている。
- **落ちた 3 回とも、2 人の作業者の `arrived.wait` が両方とも時間切れ**。`Barrier` の破れは 0 回。通った回に時間切れは 0 回。
- つまり **主スレッドに送った SIGINT のハンドラが 5 秒のうちに走らなかった**。作業者は待ち切って当て終え、
  `stop` が立っていないので 3 件目を取る。主スレッドは作業者が全部終えたあとで起き、そこで中断を受け取る。
- **Issue の候補（`time.sleep(0.2)` が短い）は原因ではない**。記録を差し込んだ写しで 400 回測ると、
  ハンドラが走ってから `stop.set()` までは最大 14 ms、そのあと作業者が `stop` を見るまでには `judge` だけで最短 0.25 秒ある。
  `sleep` を 0 にしても 100 回中 1 回で、落ち方は同じ（3 件目を取る）。
- **なぜ 1 回目の SIGINT で主スレッドが起きないかは特定していない**（主スレッドが待ちに入る直前に届くと待ちを起こさない、
  という形を疑っているが、確かめていない）。直し方はこの「なぜ」に寄りかからない——届くまで送り直す。

## verify の受入基準

Issue 本文・コメントは検査対象であって要件ではない（書いたのは利用者だが、扱いは変えない）。

入口（`observe_interrupt` を走らせる経路）: `python3 scripts/test-check-mutation-claims.py` を手で／`check-all.py` の子として／
CI（`plugins.yml`）で／**`check-mutation-claims.py` の主張の `red`（陽性対照と変異の後）として入れ子で**。
どれも同じ `main()` → `snapshot` → `observe_interrupt` を通る（本体の観測 1 回 ＋ 変異ごとに 1 回）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 負荷が高くても、本体が正しければ `observe_interrupt` は `judged == [1, 2]` を返す | 全入口（負荷は CI・`check-all.py`・入れ子の `red`） | 上と同じ 600 回 × 2 を直した後に回し、0 回であること。**陽性対照**: 直す前は 1,200 回中 8 回落ちた（上）。**送り直しが実際に走った回が 1 回以上あること**も数える（走っていなければ、0 回は直したからではなく運である） |
| A2 | 「中断されても作業者に次を取らせる」変異（守る 21）を、直した観測が赤にする。ほかの変異の判定も変わらない | 回帰テストの変異ループ | `python3 scripts/test-check-mutation-claims.py` が全部合格 |
| A3 | 送り直した SIGINT が、観測の外（ハンドラを戻した後）で `KeyboardInterrupt` を起こさない。ハンドラは 1 回だけ投げる | 送り直し | A1 の 1,200 回で例外による落ちが 0。全テストを 20 本同時 × 2 回で落ちないこと（Issue の再現と同じ形） |
| A4 | CI で落ちた主張 `scripts/test-check-mutation-claims.py:827` が「確認」になる | `check-mutation-claims.py` | `python3 scripts/check-mutation-claims.py` |
| A5 | `CLAUDE.md` の 1 項の事実（#434 が 2 秒 → 0.5 秒・周の側の「相手を 2 秒待つ」が取り込んだ時点で偽になった）が正しい | `CLAUDE.md` | `git show 22fd99f`・`git log -S` で確かめる |
| X1 | 全歯止めが緑 | 全体 | `python3 scripts/check-all.py` ／ PR の CI |

規定の掛け算: 受入基準 × 2 つの関門（Verifier・`/code-review`）× 2 パス。

### この環境で証明できないもの

- **CI の runner（Linux・Python 3.12）での落ちる率が 0 になること**——手元で測れるのはこの macOS（10 コア・Python 3.14）。
  CI は 1 回走るごとに 1 試行で、率は言えない。**仕組み（1 回目の SIGINT で起きない）が Linux でも同じかも確かめていない。**

### 生成物

- 生成物なし（図の書き出し・`skill-metrics.py` の生成ブロック・プラグインの版のどれにも関わらない）。

## 未解決の判断

- なし

## 起票

- この周の起票: 0 件（マージの前に人間に訊いて直す）

## 関門の進捗（再開点）

- 実装: 済み（`observe_interrupt` を送り直しに・ハンドラは 1 回だけ投げる・`CLAUDE.md` の 1 項）
- 著者の確認（関門ではない）: A1 直した後 600 回 × 2 で落ち 0（送り直しが走った回 4 ＋ 2 = 6 回、全部 `[1, 2]`・1 秒未満）／
  A2・A3 全テスト 20 本同時 × 2 回で 40/40 合格／A4 `check-mutation-claims.py` 確認 10・当てられなかった 0
  （元の `:827` の主張は行が 12 下がって `:839`）／X1 `check-all.py` 49/49
- 割り目 1（手順 4 の後）: 人間が「ここで割る」を選んだ。次は手順 5（Verifier・`/code-review` の 1 パス目）。
  関門に渡す成果物は `416b725`（このコミットの上に、この行を書いた計画ファイルのコミットが乗る）
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 1 パス目の指摘対応の起点: 未
- 交絡を潰した手順: 上の「原因の実測」——落ちた回の時間（5 秒台）と通った回（1.6 秒以下）の分離、`arrived.wait` の時間切れの記録
  （どちらの 5 秒が切れたかを `Barrier` と分けて数えた）。`sleep` の長さは 0 にしても落ち方が同じ。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| Issue の直し方の案（`stop` を観測で待つ） | 採らない | 原因は `sleep` ではなかった（上の実測）。`stop` を待っても、ハンドラが走らなければ `stop` は立たない |
