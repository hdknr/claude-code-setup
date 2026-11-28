# Issue #1602 — spec-loop: TLC が既定の 1 ワーカーで走り、PROPERTY つきの検査が遅い——トレースが要らない検査は複数ワーカーで走らせる

cruise（親 Issue #1604）の子として回す**不在の周**（`/dev-loop:cruise 1604 --absent` の起動・2026-11-27T07:31Z、2026-11-28 再開）。
台帳の確かめた線（出所: cruise の確かめた線（台帳 `issue-1604`）。利用者の確認（起動時・2026-11-27T07:31:25Z、配布を見せて確かめた））:
直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ / 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（後退・未達を含む）。
マージは親がする（子は PR 側の CI を見るところまで）。割り目では訊かずに「このまま続ける」。

- 直す線: 既定（出所: cruise の確かめた線）
- 版の上げ方: spec-loop を minor で上げる（0.140.1 → 0.141.0。スクリプトと Formal Checker の振る舞いを変える——能力の追加。0.x なので壊れる変更も minor）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-tlc.py` — ワーカーの数を検査の種類ごとに足す部品（`for_verdict`・`for_trace`）と、docstring の「呼び方に足すオプション」の書き直し・実測の記録
- `plugins/spec-loop/scripts/check-formal-rerun.py` — 本体・陽性対照を複数ワーカーで走らせ、本体の反例は 1 ワーカーで走らせ直してトレース（出力の終わり）を出す
- `plugins/spec-loop/scripts/formal-statechart.py` — 状態グラフ（`-dump`）を、呼び方に何があっても 1 ワーカーで走らせる
- `plugins/spec-loop/agents/formal-checker.md` — 検査の種類ごとのワーカーの数・反例のトレースの取り直し・同時に走らせる本数とワーカー数の割り振り・陽性対照の `PROPERTY`
- `plugins/spec-loop/references/tree.md` — 「保存したモデルを CI で走らせ続ける」の呼び方のオプションの行（ワーカーの数はスクリプトが足す）
- `scripts/test-check-tlc.py` — 部品の観測と変異
- `scripts/test-check-formal-rerun.py` — 偽の TLC がワーカーの数を記録し、反例のトレースをワーカーの数で揺らす試料と変異
- `scripts/test-formal-statechart.py` — 状態グラフを 1 ワーカーで走らせる試料と変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1602.md` — この計画

触らない:

- `check-tlc.py` の CLI（`probe` の 2 つの小さいモデル）——呼び方が通るかだけを見るので、呼び方の行のまま走らせる
- `plugins/spec-loop/scripts/tlc-trace.py`——TLC を走らせない（Formal Checker が 1 ワーカーで取った JSON を読むだけ）
- dev-loop の `formal-sync.py`——`check-formal-rerun.py` の `rerun` を読み込むので、そのまま新しい振る舞いになる（コードは変えない）
- 保存したモデルの `.cfg` の形（`PROPERTY` を外さない。決めたこと 3）
- `-Xmx`・`-fpmem`（実行の設定のうちワーカーの数だけを扱う）

依存の追加・更新: なし
仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本を持たない——プラグインの原本）
差分テスト: なし（判定と終了コードは変えないが、走らせ方（ワーカーの数）と反例の行の出し方を変える周。判定を変えないことは既存の試料を全部通すこと（受入基準 6）と、本物の TLC での 1 ワーカーと複数ワーカーの比べ（受入基準 5）で見る）
プロパティテスト: なし（往復・冪等性・等価性・数値の境界の不変条件を持たない。ワーカーの数を足す部品は呼び方の文字列の形ごとの例で当てる）

## 決めたこと（仕様の穴。不在の線 `仕様の穴 = 推奨で決めて起票` で推奨により決めた）

Issue の「あわせて決めたいこと」の 3 つは Issue が決めていない（選択肢だけを挙げる）ので、仕様の穴として推奨で決め、穴ごとに確認の Issue を立てる。

1. **ワーカーの数をどこで持つか** — 選択肢: 案 A（呼び方の行に書かず、スクリプトと Formal Checker が検査の種類ごとに足す）／案 B（`TLC のワーカー:` の別の宣言）／案 C（呼び方の例に `-workers auto` を入れ、トレースの要る場面だけ `-workers 1` で上書き）。
   **決めた値: 案 A。ただし呼び方の行に利用者が `-workers` を書いていれば、判定の検査はその値を使う（足さない）。トレースの要る検査（反例の取り直し・状態グラフ）は呼び方に何があっても後ろに `-workers 1` を足す。**
   理由: 利用者の設定なしで速くなる（受入基準 1）のは A と C で、C は利用者が呼び方を書き直さないと効かない。B は宣言と読み方が 1 つ増える。手元の TLC 2.19（tla2tools v1.7.4）で `-workers` を 2 回渡すと後の値が使われた（`-workers auto -workers 1` → 1 worker、`-workers 1 -workers auto` → 28 workers、`-workers 1 -workers 3` → 3 workers。2026-11-28）ので、
   後ろに足せば呼び方の行の値を確実に上書きできる。利用者が CPU を絞るために書いた値は、判定の検査では尊重する（#1339 の「呼び方の行は利用者が決める」を崩さない）。
2. **何本も同時に走らせるときの割り振り** — 選択肢: 「1 本ずつ複数ワーカーで順に走らせる」／「ワーカー数 = コア数 ÷ 同時に走らせる本数」。
   **決めた値: 既定は 1 本ずつ順に（`-workers auto`）走らせ、同時に走らせない。どうしても同時に走らせるなら、各回の後ろに `-workers <コア数 ÷ 同時の本数（切り捨て、1 以上）>` を足す。**
   理由: TLC は 1 本で全部のコアを使うので、同時に走らせると取り合うだけで、本数を割った数を毎回計算させるより手順が少ない。時間の区切り（Formal Checker の「長く走る検査は、時間を区切って前景で走らせる」）とも食い違わない。
3. **陽性対照の `.cfg` に `PROPERTY` を残すか** — 選択肢: 残す（今のまま）／外す（`INVARIANT` を壊す陽性対照に限り）。
   **決めた値: 残す（今のまま。陽性対照の `.cfg` も `PROPERTY` を外さない）。**
   理由: 複数ワーカーで遅さの大半は戻る（Issue の実測で 44 秒 → 6 秒。外すとさらに 2 秒）。外すかを壊し方ごとに判断させると、時相の性質を壊した陽性対照から誤って外す形が生まれ、#1339 の「保存した `.cfg` のまま走らせる」と 2 通りの決まりになる。

確認の Issue: 下の「関門の進捗」に番号を書く（立てたら）。

## 乗るデプロイ経路

main へのマージでプラグイン（spec-loop）の配布と GitHub Pages の再ビルド（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。マージは親がする。

## 受入基準（不変条件 × 経路）

TLC を走らせる入口: (a) `check-formal-rerun.py` の CLI（本体・陽性対照）、(b) dev-loop の `formal-sync.py rerun`（`check-formal-rerun.py` の `rerun` を読み込む）、(c) 正本の CI の雛形（`tree.md`。(a) を呼ぶ）、
(d) `formal-statechart.py`（`-continue -dump`）、(e) Formal Checker（本体・陽性対照・到達の確かめ・`-dumpTrace json`・図の対応の `-dump`）、(f) `check-tlc.py` の CLI（呼び方の確かめ。触らない）、(g) `formal-baseline` スキル（Formal Checker を呼ぶ——(e) と同じ）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | 判定の検査（本体・陽性対照・到達の確かめ・`check-formal-rerun.py`）が、利用者の設定なしで複数ワーカー（`-workers auto`）で走る | a・b・c・e・g | `check-tlc.py` の `for_verdict` を (a) が使う（b・c は (a) を通る）。(e) は `formal-checker.md` | (a)(b): 試料（偽の TLC が受けたワーカーの数を記録）と変異。(c): 雛形の試料が (a) を走らせる。(e)(g): `formal-checker.md` の文面と、その文面で Formal Checker を 1 回走らせた実物（下の「実機確認」） |
| 2 | 呼び方の行に利用者が `-workers` を書いていれば、判定の検査はその値で走る（足さない） | a・b・c・e | `for_verdict` | 試料と変異（`test-check-tlc.py`・`test-check-formal-rerun.py`） |
| 3 | 反例の経路を出す検査（Formal Checker の `トレース` と Red テスト・`formal-statechart.py` の最初の反例の経路）は、1 ワーカー・指紋の固定（`-workers 1 -fp 0`）で走らせた結果から取る。同じモデルで 2 回走らせると同じ経路になる | d・e | `for_trace`（d）。(e) は `formal-checker.md`（本体で反例が出たら `-workers 1 -fp 0` で走らせ直してトレースを取る） | (d): 回帰テスト——偽の TLC は最後の `-workers` が 1・`-fp` が 0 でなければ反例の並びを走らせるたびにずらす。呼び方に `-workers auto` がある正本で 2 回描いて同じ図になり、`for_trace` を外す・`-fp 0` を外す変異で違う図になる（陽性対照）。本物の TLC でも 5 回ずつ比べる（下の「実機確認」）。(e): 文面と Formal Checker の実物 |
| 4 | `formal-statechart.py`（`-dump`）は 1 ワーカーのまま——呼び方に `-workers auto` があっても | d | `for_trace` | 試料と変異（`test-formal-statechart.py`） |
| 5 | `formal-checker.md` に、同時に走らせる本数とワーカー数の割り振り（決めたこと 2）がある | e | 文面 | 読む（両方の関門） |
| 6 | 複数ワーカーで、判定が 1 ワーカーと同じ・反例が出ない回（全部をたどる回）の状態数が同じ——`PROPERTY` を持つモデル（反例なし）と、陽性対照として `PROPERTY` の反例（lasso）と不変条件の反例が出るモデルで | a・d・e | — | 本物の TLC（tla2tools v1.7.4）で 1 ワーカーと `-workers auto` を各 3 回走らせて比べる（下の「実機確認」）。結果を `check-tlc.py` の docstring に書く |
| 7 | ワーカーの数のほかの判定・終了コード・出力は今までどおり（既存の試料と変異が全部通る） | a〜g | 変えない | `scripts/test-check-formal-rerun.py`・`scripts/test-check-tlc.py`・`scripts/test-formal-statechart.py`・`scripts/test-formal-sync.py`・`scripts/test-tlc-trace.py` |
| 8 | 版が 3 か所（`marketplace.json`・`plugin.json`・`SKILL.md` の 2 行）で揃い、歯止めが全部通る | — | 0.141.0 | `python3 scripts/check-all.py`・PR 側の CI |
| 9 | 両方の関門に受入基準を渡す × 2 パス（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | — | 手順 5・6 | 関門の記録 |

この環境で証明できないもの: TLC 2.19（tla2tools v1.7.4）・この機械（28 コア）のほかの版と機械で、後の `-workers` が使われること・1 ワーカーのトレースが揺れないこと（受入基準ではない。docstring の「確かめたのは」に書く）。

生成物: `docs/` の設計ドキュメントの生成ブロック（`scripts/skill-metrics.py`）——spec-loop の `SKILL.md` の版の行だけを変える。`python3 scripts/skill-metrics.py --check` で鮮度を見る。図（drawio）は触らない。

複製の数: 「どの検査を何ワーカーで走らせるか」を述べる箇所は 4 つ——`check-tlc.py` の docstring（原本）、`formal-checker.md`（Formal Checker が自分で走らせる分）、`check-formal-rerun.py`・`formal-statechart.py` の docstring（自分の走らせ方と原本への指し先だけ）。`tree.md` は原本を指すだけ。
分けない理由: スクリプトは部品を読み込むので式は 1 つ。Formal Checker は散文でしか縛れないので写しが要る。

## 実機確認

本物の TLC（tla2tools v1.7.4・TLC 2.19）・この機械（28 コア）。重い回は run-serial 越し。

1. **後の値が使われる**（決めたこと 1 の前提）: `-workers auto -workers 1` → `with 1 worker`、`-workers 1 -workers auto` → 28 workers、`-workers 1 -workers 3` → 3 workers、`-fp 5 -fp 0` → fp 0、`-fp 0 -fp 5` → fp 5（各 1 回。出力の 1 行目の `Running … with …`）。
2. **判定と状態数**（受入基準 6）: 各 3 回、1 ワーカーと `-workers auto`（28）:
   - `Live`（`PROPERTY <>(a = N /\ b = N)`・公平性つき・反例なし）: どれも `No error has been found`・456,976 状態（1 ワーカー 6.7〜6.8 秒、auto 5.5〜5.8 秒）
   - `LiveBroken`（`PROPERTY` を破る陽性対照・lasso）: どれも `Temporal properties were violated.`・6,561 状態
   - `InvBroken`（不変条件を破る陽性対照・最短の反例が多数）: どれも `is violated`。状態数は 1 ワーカーが 3 回とも 331、auto が 216・296・280（最初の違反で止まるまでにたどった数——判定には使わない）
3. **トレース**（受入基準 3 の前提）: `InvBroken` は 1 ワーカーで 3 回とも同じトレース、auto で 3 種類。`LiveBroken`（lasso）は **1 ワーカーでも 3 回とも違うトレース**（TLC が指紋の多項式を回ごとに選ぶ）で、`-fp 0` を足すと 1 ワーカーで 3 回とも同じ（auto `-fp 0` は 3 回で 2 種類）——**Issue の「1 ワーカーで走らせ直す」だけでは時相の性質の反例が揺れるので、`-fp 0` も足すことにした**（決めたこと 1 の値の一部。穴ではなく受入基準 3 を満たす手段）。
4. **`check-formal-rerun.py` を本物の TLC で**（受入基準 1）: 呼び方を「受けた引数を記録して本物の TLC を exec する」包みにした正本で、base（`627822c4`）の木は本体・陽性対照の 3 回とも引数なし（1 ワーカー）、新しい木は 3 回とも `-workers auto`。判定はどちらも `満たす`（`Live` 456,976 状態）。
5. **`formal-statechart.py` を本物の TLC で**（受入基準 3・4）: 呼び方に `-workers auto` を書いた正本で、最短の反例が多数ある 125 状態のモデルの図を 5 回ずつ描いた。base の木は 2 種類の図（最初の反例の経路が `0-1-0 → 1-1-0 …` と `1-0-0 → 2-0-0 …`）、新しい木は 5 回とも同じ図（TLC が受けた引数は `-workers auto -workers 1 -fp 0 -continue -dump …`）。
- 観測窓: 各モデル・各条件 3〜5 回。ほかの版・大きいモデルは確かめていない（`check-tlc.py` の docstring に書いた）。
- 交絡を潰した手順: base と新しい木を同じ正本・同じ包み・同じ機械で続けて走らせた（陽性対照: base は 1 ワーカー・図が揺れる）。

## 未解決・確認待ち

- 決めたこと 1〜3 の確認の Issue（利用者が答えるまで開いたまま）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1602-tlc-workers`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1602`・起点 `627822c4`・base は `origin/main`（`refs/remotes/origin/HEAD`）の merge-base `627822c40e7c256da6c7c7916418e0b1e3ce36ee`
- 割り目（手順 4）: 割らない（cruise の周）

```dev-loop-gates
周の base: 627822c40e7c256da6c7c7916418e0b1e3ce36ee
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

- 決めたこと 1〜3（穴の記録。推奨で決めた値を関門に渡す——受入基準は足さない）。
- `check-tlc.py` の CLI の確かめは呼び方の行のまま走らせる（2 つの小さいモデルで、ワーカーの数は効かない）。
- 呼び方の行に利用者が `-workers 1` を書いた正本では、判定の検査も 1 ワーカーのまま（決めたこと 1。利用者の値を使う）。

## 手順 8（経験の還元）

- この周の起票: 3 件（仕様の穴の確認の Issue——決めたこと 1〜3 を穴ごとに 1 件。不在の線 `仕様の穴 = 推奨で決めて起票`）
