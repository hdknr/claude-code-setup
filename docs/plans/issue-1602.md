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
- `plugins/spec-loop/scripts/check-formal-rerun.py` — 本体・陽性対照を複数ワーカーで走らせる（反例は取り直さない——判定だけを出す。Issue の表のとおり）
- `plugins/spec-loop/scripts/formal-statechart.py` — 状態グラフ（`-dump`）を、呼び方に何があっても 1 ワーカーで走らせる
- `plugins/spec-loop/agents/formal-checker.md` — 検査の種類ごとのワーカーの数・反例のトレースの取り直し・同時に走らせる本数とワーカー数の割り振り・陽性対照の `PROPERTY`
- `plugins/spec-loop/references/tree.md` — 「保存したモデルを CI で走らせ続ける」の呼び方のオプションの行（ワーカーの数はスクリプトが足す）
- `scripts/test-check-tlc.py` — 部品の観測と変異
- `scripts/test-check-formal-rerun.py` — 偽の TLC が受けたワーカーの数を記録する試料と変異
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
   **決めた値: 案 A。ただし呼び方の行に利用者が `-workers` を書いていれば、判定の検査はその値を使う（足さない）。トレースの要る検査（Formal Checker の反例の取り直し・状態グラフ）は呼び方に何があっても後ろに `-workers 1 -fp 0` を足す（`-fp 0` は下の「実機確認」の 3）。**
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
| 1 | 判定の検査（本体・陽性対照・到達の確かめ・`check-formal-rerun.py`）が、利用者の設定なしで複数ワーカー（`-workers auto`）で走る | a・b・c・e・g | `check-tlc.py` の `for_verdict` を (a) が使う（b・c は (a) を通る）。(e) は `formal-checker.md` | (a): 試料（偽の TLC が受けたワーカーの数を記録）と変異。(b): コードの読み（`formal-sync.py` は `rerun` を読み込んで呼ぶ）と (a) の試料。(c): 雛形の試料が (a) を走らせる。(e)(g): `formal-checker.md` の文面と、その文面で Formal Checker を 1 回走らせた実物（下の「実機確認」） |
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

複製の数: 「どの検査を何ワーカーで走らせるか」を述べる箇所は 5 つ——`check-tlc.py` の docstring（原本）、`formal-checker.md`（Formal Checker が自分で走らせる分）、`check-formal-rerun.py`・`formal-statechart.py` の docstring（自分の走らせ方と原本への指し先だけ）。`tree.md` は CI の行で `check-formal-rerun.py` の決まり（`-workers` が無ければ `-workers auto`）を 1 文写して原本を指す（2 パス目の CR2-6 で数え直した）。
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
6. **Formal Checker の実物**（受入基準 1・3 の (e)）: `spec-loop:formal-checker`（sonnet）に worktree の `formal-checker.md`（指摘対応の後の版・201 行）を正として読ませ、小さい注文の業務フロー（R1 は不変条件・R2 は `PROPERTY`）を検査させた（2026-11-28T07:08Z。報告 `fc-proxy/report-20261128T070835Z.md`）。
   TLC が受けた引数: 本体・陽性対照・到達の確かめの判定の回はどれも `-workers auto`（出力 `with 28 workers`・`fp` は回ごとに違う）、R1 を破る版の反例は `-workers 1 -fp 0` で取り直し（`fp 0 … with 1 worker`）、`トレース` はその回の出力から写した（手元の TLC 2.19 は `-dumpTrace` を受けないので `tlc-trace.py` は使えず、写す側に落ちた——既存の手順どおり）。
   1 回目（指摘対応の前の版で 06:19Z）は報告が届かず（「報告を届けずに終わった」の形）、モデルのディレクトリだけが残っていた——数えない。報告の気づきで、出力の文言が 1 ワーカーでは `with 1 worker`（単数）なので `formal-checker.md` の確かめ方を両方の形にした。
- 観測窓: 各モデル・各条件 3〜5 回。ほかの版・大きいモデルは確かめていない（`check-tlc.py` の docstring に書いた）。
- 交絡を潰した手順: base と新しい木を同じ正本・同じ包み・同じ機械で続けて走らせた（陽性対照: base は 1 ワーカー・図が揺れる）。

## 未解決・確認待ち

- 決めたこと 1〜3 の確認の Issue（利用者が答えるまで開いたまま）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1602-tlc-workers`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1602`・起点 `627822c4`・base は `origin/main`（`refs/remotes/origin/HEAD`）の merge-base `627822c40e7c256da6c7c7916418e0b1e3ce36ee`
- 割り目（手順 4）: 割らない（cruise の周）
- 実装: 済（`1191dc34`）。歯止め `check-all.py`（run-serial 越し）: 61 本を回し失敗 1——`check-plan-counts.py`（件数の行が無かった）。計画に件数の行を足して `check-plan-counts.py` 単体で緑
- 1 パス目の指摘対応の起点: `1191dc34d9ce89fd6afbe94a5a795ef9569b0618`
- Verifier 1 パス目: dev-loop:dev-loop-verifier・sonnet。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/9ca242d9-1e14-4e59-880c-ea52c4e9c7a3/scratchpad/gate-1602-verifier-1-20261128T064211Z.md`
- /code-review 1 パス目: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/9ca242d9-1e14-4e59-880c-ea52c4e9c7a3/scratchpad/gate-1602-code-review-1-20261128T064211Z.md`
- Verifier 1 パス目: 反証 1 件（V1-R1）。終点 `1191dc34`（成果物。その後のコミット `0163b354` は計画ファイルだけ）
- /code-review 1 パス目: 指摘 7 件（important 3・nit 4。CR1-1 は V1-R1 と同じ）。終点 `1191dc34`
- 1 パス目の指摘対応: `6670a5ea`（直す 4 行: V1-R1／CR1-1・CR1-2・CR1-7。CR1-3・CR1-5 は計画ファイルの記録の直し）。`test-check-tlc.py`: 緑。指摘対応の差分は 0 行でない（`check-tlc.py`・`formal-checker.md`）ので 2 パス目を回す
- 割り目（手順 6）: 割らない（cruise の周）
- Verifier 2 パス目（当て直し。dev-loop:dev-loop-verifier・sonnet）: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/9ca242d9-1e14-4e59-880c-ea52c4e9c7a3/scratchpad/gate-1602-verifier-2-20261128T071145Z.md`
- /code-review 2 パス目: 報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/9ca242d9-1e14-4e59-880c-ea52c4e9c7a3/scratchpad/gate-1602-code-review-2-20261128T071145Z.md`
- Verifier 2 パス目: 反証 0 件。終点 `46d85a59`
- /code-review 2 パス目: 指摘 6 件（important 1・nit 5）。終点 `46d85a59`
- 2 パス目の指摘対応（狭いパス）の起点: `46d85a59b51baa60a036b230763b6541af737f05`（指摘対応を始める直前の HEAD）
- 2 パス目の指摘対応: `0cbc474b03a37deb45a670ce5fdc27bbaf31032b`（直す 2 行: CR2-2・CR2-4）。`test-check-tlc.py`: 緑
- 狭いパス: 起点 `46d85a59b51baa60a036b230763b6541af737f05` → 終点 `0cbc474b03a37deb45a670ce5fdc27bbaf31032b`（dev-loop:dev-loop-verifier・sonnet）。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/9ca242d9-1e14-4e59-880c-ea52c4e9c7a3/scratchpad/gate-1602-narrow-1-20261128T075215Z.md`
- 狭いパス: 反証 1 件（N1）。終点 `0cbc474b`
- 狭いパスの N1 を直した（cruise の線 `マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`——受入基準 3 を破る指摘は推奨の前にまず直して 1 回だけ当て直す）: `ac01f429d3e6a8327aceb01b6d38e3feae6cded6`。当て直しの Verifier: 起点 `0cbc474b03a37deb45a670ce5fdc27bbaf31032b` → 終点 `ac01f429d3e6a8327aceb01b6d38e3feae6cded6`。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/9ca242d9-1e14-4e59-880c-ea52c4e9c7a3/scratchpad/gate-1602-redo-1-20261128T075619Z.md`
- 当て直しの Verifier: 反証 0 件（観察 1 件——`-simulate` の反例を網羅の検査で確かめる回のワーカーの数が文面で決まらない。記録だけ）。終点 `ac01f429`

```dev-loop-gates
周の base: 627822c40e7c256da6c7c7916418e0b1e3ce36ee
関門: Verifier 1 1191dc34d9ce89fd6afbe94a5a795ef9569b0618 反証=1
関門: /code-review 1 1191dc34d9ce89fd6afbe94a5a795ef9569b0618 指摘=7
関門: Verifier 2 46d85a59b51baa60a036b230763b6541af737f05 反証=0
関門: /code-review 2 46d85a59b51baa60a036b230763b6541af737f05 指摘=6
関門: 狭いパス 46d85a59b51baa60a036b230763b6541af737f05 0cbc474b03a37deb45a670ce5fdc27bbaf31032b 反証=1
関門: 当て直し 0cbc474b03a37deb45a670ce5fdc27bbaf31032b ac01f429d3e6a8327aceb01b6d38e3feae6cded6 反証=0
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
受入基準: 8 満たす
受入基準: 9 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

### 狭いパスの指摘と振り分け（cruise の線 `マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`）

| 指摘 | 実物で失敗を示せるか | 振り分け | 後退を示すか | 推奨と理由 |
| --- | --- | --- | --- | --- |
| N1: `formal-checker.md` の `-dumpTrace` が使えないときの写し先（63 行）と報告の `トレース` の列（189 行）が、どの回の出力から写すかを名指さない——最初の複数ワーカーの回の揺れる経路を写す読み方が残る | 示せる——文面（63・189 行。62 行の「取り直せなければ書かない」とも食い違う） | 直す（受入基準 3 を破る） | 示す——この周が回を 2 つにしたので生まれた読み方 | 直してからマージする——文面の 2 か所を「取り直した回の出力」と名指す。直して当て直し 1 回 |

### 2 パス目の指摘と採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1: 取り直しの回（1 ワーカー）が最初の複数ワーカーの回と違う性質の違反で止まりうるのに、`formal-checker.md` は指摘・結果・状態数をどちらの回で書くかを言わない（InvA の指摘に InvB の Red テストが付く） | 示せない（そう止まる実物は走らせていない。性質が 2 つ以上・同じ深さで破れる形の読み） | 無し（トレースは 1 ワーカーの回から取る——受入基準 3 はそのまま満たす） | 残課題 |
| CR2-2: 取り直しの回が反例を出さない（時間切れなど）ときに「最初の回の出力を書く」とだけあり、複数ワーカーの回の揺れる経路を `トレース`（Red テスト）に写す読み方が残る | 示せる——文面（`formal-checker.md` 62 行） | 3 | 直す（取り直しが反例を出さなければ `トレース` を書かず、取れなかったと書く） |
| CR2-3: CR1-4・CR1-6 の限界が `check-tlc.py` の「守らない」に書かれていない | 示せない（文面の欠け。失敗の実物は CR1-4・CR1-6 と同じく無い） | 無し | 残課題 |
| CR2-4: `check-tlc.py` の箇条の見出し「判定と状態数は、ワーカーの数で変わらなかった」が、同じ箇条の「反例で止まった回の状態数は変わる」と食い違う（実測より強い） | 示せる——docstring の 67 行と同じ箇条の実測 | 6（実測の記録が実測より強い） | 直す（「判定と、状態空間を全部たどった回の状態数」にする） |
| CR2-5: 「1 本ずつ順に走らせる」が時間切れの後に試す段の 4 番目に置かれ、時間切れの前から並べて走らせる読み方が残る・コア数を `getconf` で取るとコンテナで TLC の値と食い違う | 示せない（Formal Checker の実物（実機確認 6）は順に走らせた。並べて走らせた実物は無い） | 無し（受入基準 5 は割り振りがあること） | 残課題 |
| CR2-6: 計画の「複製の数」が `tree.md` を指すだけと書くが、`tree.md` は決まり（`-workers` が無ければ `-workers auto`）も写している | 計画ファイルの記録の誤り（成果物ではない） | 無し | 計画ファイルを直す（写しは 5 つ） |

### 1 パス目の指摘と採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-R1／CR1-1: `check-tlc.py` の原本の表と計画の変更範囲が「`check-formal-rerun.py` の反例の行は 1 ワーカーで取り直す」と書くが、実装は取り直さない | 示せる——`grep -n for_trace plugins/spec-loop/scripts/*.py` の呼び出し元は `formal-statechart.py` だけ（`check-formal-rerun.py` の 212〜231 行は `for_verdict` の回の `tail(out)`） | 3（原本の決まりが事実と違う） | 直す（Issue の表のとおり `check-formal-rerun.py` は判定だけ——原本と計画から外し、取り直さないことを書く） |
| CR1-2: `formal-checker.md` の同時に走らせる手順が、取り直しと `-dump` の回・利用者の `-workers` がある回にも `-workers <数>` を足させる（後の値が使われるので 1 ワーカーでなくなる・利用者の値を上書きする） | 示せる——文面（153 行）と実測（後の値が使われる。実機確認 1） | 2・3・5 | 直す（判定だけの回で `-workers` が無いときに限る。取り直しと `-dump` は同時に走らせない） |
| CR1-3: 計画の受入基準 1・3 の (e)(g) の証明「Formal Checker を 1 回走らせた実物」の記録が実機確認に無い | 計画ファイルの記録の欠け（成果物ではない） | 無し | 計画ファイルに記録する（Formal Checker を走らせた結果を実機確認の 6 に書く） |
| CR1-4: `check-tlc.py` の確かめ（probe）は、足したオプション（`-workers auto`・`-fp 0`・2 回渡す形）を受けるかを確かめない | 示せない（手元の TLC 2.19 は受ける。受けない版は手元に無い） | 無し | 残課題 |
| CR1-5: 計画の受入基準 1 の (b) の証明「試料と変異」は `test-formal-sync.py` に無い | 計画ファイルの記録の誤り（成果物ではない） | 無し | 計画ファイルを直す（コードの読みと (a) の試料と書く） |
| CR1-6: `has_workers` は語として現れる `-workers` だけを見る——引用符の中・環境変数の展開（`$TLC_OPTS`）に書いた値を「書いていない」と読み、`-workers auto` で上書きする | 示せない（そう書いた正本の実物は無い。`for_verdict("… $TLC_OPTS")` が足すことは示せるが、受入基準 2 は「呼び方の行に書いた」値） | 無し | 残課題 |
| CR1-7: `formal-checker.md` の「その回の JSON から `tlc-trace.py`」が、最初の複数ワーカーの回と取り直しの回のどちらかを名指ししない | 示せる——文面（63 行） | 3 | 直す（取り直した回の JSON と名指す） |

- 決めたこと 1〜3（穴の記録。推奨で決めた値を関門に渡す——受入基準は足さない）。
- `check-tlc.py` の CLI の確かめは呼び方の行のまま走らせる（2 つの小さいモデルで、ワーカーの数は効かない）。
- 呼び方の行に利用者が `-workers 1` を書いた正本では、判定の検査も 1 ワーカーのまま（決めたこと 1。利用者の値を使う）。

## 手順 8（経験の還元）

- この周の起票: 3 件（仕様の穴の確認の Issue——決めたこと 1〜3 を穴ごとに 1 件。不在の線 `仕様の穴 = 推奨で決めて起票`）
