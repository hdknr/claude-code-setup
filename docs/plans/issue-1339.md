# Issue #1339 — spec-loop: TLC の検査が重いときの扱いを決める（状態数の報告・時間切れの手順・Liveness の段取り）

利用者が居る周（出所: `/dev-loop:dev-loop 1339`、2026-11-20）。読み込んだ dev-loop は 2.14.1（キャッシュ）。

直す線: `既定`（出所: 手順 3 の回答——`.claude/dev-loop.md` に行が無いので `AskUserQuestion` で訊いた）。
版の上げ方: `spec-loop` を **minor**（判定役の手順と報告の項目を足し、`check-formal-rerun.py` の出力に行を足す。0.124.0 → 0.125.0）。

Issue 本文（外部入力。起票したのはこのセッション）から読んだ要件: Formal Checker の報告に状態数と経過時間・時間切れのときの手順（打ち切りは「置いた前提」に）・
組み立て中は `INVARIANT` だけで報告の前に `PROPERTY` を含める・`check-formal-rerun.py` が状態数を出す・呼び方の例に `-workers`・`-Xmx`・`-fpmem`（複数ワーカーは「確かめていないこと」の決着に従う）・
走らせ直しと CI で `PROPERTY` を外さない。コメントは無い。受入基準を緩める指示は無い。

## 決めた値（実測。手順 2）

手元の本物の TLC 2.19（`tla2tools.jar`、Java 22）で、Issue の「確かめていないこと」の 1 つ目を測った（スクリプトは scratchpad の `exp/run.sh`。リポジトリには入れない）:

- **不変条件の反例**（4 つのカウンタ・和が 9 で違反。最短の反例は多数ある）を `-workers 1` と `-workers 8` で 8 回ずつ: 反例のトレース（`is violated` から状態数の行まで、時刻の行を除く）は
  **`-workers 1` で 8 回とも同じ 1 種類、`-workers 8` で 5 種類**。長さ（`State N:` の数）はどちらも 8 回とも 10（この試料では最短のまま）。
- **陽性対照**（同じ形で `-workers 1` を 8 回）: 同じ設定で異なる結果を出すことで、測定が「何をしても同じ」になっていないことを示す——`-workers 8` が 5 種類を出したことがそれにあたる。
- **`-dump dot,actionlabels`** の出力は **`-workers 1` でも 8 回とも別のバイト**（行を並べ替えても 8 種類）——状態の番号が実行ごとに変わる。だからこの比べ方では、ワーカー数が状態グラフ・図を変えるかは**判別できない**（`formal-statechart.py` は言葉の対応で描くので番号に依らないが、描いた図が同じかは測っていない）。
- 状態数の行の形（TLC 2.19）: `<n> states generated, <m> distinct states found, <k> states left on queue.`、経過時間 `Finished in <時間> at (…)`。違反で止まった回も同じ形で出た（`84 states left on queue`）。

- **`-Xmx2g -fpmem 0.5`** を足した 3 回: 反例のトレースは 1 種類で、`-workers 1` の回と同じ。状態数の行も同じ（`1002 states generated, 356 distinct states found`）。
- **本物の TLC で `check-formal-rerun.py`**（実装の後、scratchpad の `exp/e2e.sh`）: 小さいモデルで `（状態数 1024・0.8 秒）`、大きいモデルを `--timeout 75` で時間切れにして
  `（状態数 37791202・75.2 秒）`（進み具合の行 `37,791,202 distinct states found` の `,` を外した数）。判定は時間切れで `判定できなかった`（4）のまま。
  （小さいモデルの本体は上限で止まって行き止まり（Deadlock）の反例が出た——試料の作りの誤りで、スクリプトの判定は正しい。）

- **1 パス目の指摘の確かめ**（scratchpad の `exp/cons.sh`・`exp/locale.sh`）: `CONSTRAINT c < 4` つきで `<>[](c = 0)` が `No error has been found`、外すと `Temporal properties were violated.`（陽性対照）。
  進み具合の行は `-Duser.language=de` で `12.118.483`、`fr` で U+202F、`en` で `,` の区切り。最後の行は `de` でも `1681 distinct states found`（区切りなし）。`-fpmem` のヘルプは (0.0,1.0) の割合だけ。

決着: **`-workers` を正本の `TLC の呼び方:` の行に入れると、同じモデルの反例のトレースが実行ごとに変わる**（Formal Checker の `トレース`・`tlc-trace.py` の段の並び・`formal-statechart.py` の最初の反例の経路が揺れる）。
呼び方の行は全部の段が共有するので、**案内は「`-Xmx`・`-fpmem` は呼び方の行に書いてよい、`-workers` は書くと反例の経路が揺れることを承知のうえで」** とし、走らせ直しの判定（`満たす`／`反例あり`）は反例の経路に依らないことを添える。

## 変更範囲

触る:

- `plugins/spec-loop/agents/formal-checker.md` — 報告の「道具」の列に状態数・経過時間、「検査が重いとき」の節（時間切れの手順・打ち切りを置いた前提に・組み立て中は `INVARIANT` だけ・保存する本体の `.cfg` は `PROPERTY` を含める・使わない手段）
- `plugins/spec-loop/scripts/check-formal-rerun.py` — 走らせたモデルごとに状態数（読めなければそう言う）を出す・docstring
- `scripts/test-check-formal-rerun.py` — 偽の TLC に状態数の行・状態数を出す／読めない試料・変異
- `plugins/spec-loop/scripts/check-tlc.py` — docstring の呼び方の節に `-Xmx`・`-fpmem`・`-workers` の案内（原本はここ）
- `plugins/spec-loop/references/tree.md` — 「保存したモデルを CI で走らせ続ける」に、保存した `.cfg` のまま走らせる（`PROPERTY` を外さない）の 1 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1339.md` — この計画ファイル

触らない:

- `formal-statechart.py`・`tlc-trace.py`・dev-loop の `formal-sync.py`（呼び方を受け取るだけで変えない）
- 説明文（frontmatter・`plugin.json`・`marketplace.json` の description）・`README.md`・公開ページ・`CLAUDE.md`（今の要約が偽にならない）
- SYMMETRY・VIEW・`-simulate`・Apalache を使う仕組み（Issue の「やらないこと」）

依存の追加・更新: なし

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

**複製の数**: 「`PROPERTY` を外さない」が 2 箇所（`formal-checker.md` の保存する本体・`tree.md` の CI）、「呼び方に足すオプション」が 1 箇所（`check-tlc.py` の docstring。`formal-checker.md` はそこを指す）、
状態数の報告が 2 箇所（`formal-checker.md` の報告の形・`check-formal-rerun.py`）。分けない理由: どれも同じ 1 つの「重いときの扱い」で、片方だけ入れると判定役の報告と機械の出力が食い違う。

## デプロイ経路

プラグイン（カタログと `link-skills.sh` の利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口: (a) Formal Checker（spec-review の手順 3・formal-baseline・狭いパスが呼ぶ）が読む `agents/formal-checker.md`、(b) `check-formal-rerun.py` の CLI（spec-review・CI の雛形・dev-loop の `formal-sync.py rerun` が `rerun` を読み込む）、
(c) 正本の `CLAUDE.md` の `TLC の呼び方:` の行（`check-tlc.py`・`check-formal-rerun.py`・`formal-statechart.py`・Formal Checker が共有）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | Formal Checker の報告に、TLC の対象の状態数（`distinct states found`）と経過時間がある | (a) 報告の形 | 「道具」の列 | 文面の読み |
| A2 | 時間切れのときに試す順があり、`CONSTRAINT`・抽象化・構成の縮小で打ち切った範囲を「置いた前提」に書く。打ち切った検査を「反例なし」と書かない | (a) | 「検査が重いとき」の節 | 文面の読み |
| A3 | 組み立て中は `INVARIANT` だけで回してよいが、報告の前と保存する本体の `.cfg` は `PROPERTY` を含めた形 | (a) | 同上 | 文面の読み |
| A4 | `check-formal-rerun.py` が走らせたモデルごとに状態数と経過時間を出す。時間切れなら進み具合の最後の行の数。読めなければ「読めなかった」と出し、**判定（終了コード）は変えない** | (b) | 出力の行 | 偽の TLC の試料（状態数あり・`,` 区切り・進み具合 2 行の時間切れ・状態数の行の無い通過と構文の誤り）と変異。本物の TLC 2.19 で 1 回（下の「決めた値」） |
| A5 | `formal-sync.py`（`rerun` を読み込む）の判定が変わらない | (b) | `rerun` の返り値の形（判定・行）を変えない | `test-formal-sync.py` が緑 |
| A6 | 呼び方の例に `-Xmx`・`-fpmem`・`-workers` の案内があり、`-workers` は反例の経路が揺れる（実測）と書く | (c) | `check-tlc.py` の docstring | 文面の読み・上の実測 |
| A7 | 走らせ直し・CI で `PROPERTY` を外さない（保存した `.cfg` のまま走らせる）と書かれている | (b) CI の雛形 | `tree.md` | 文面の読み（雛形のステップは変えない——`test-check-formal-rerun.py` の雛形の抜き出しが緑） |
| A8 | Issue の「やらないこと」（SYMMETRY・VIEW を勧めない・粒度は実装でも原子的なときだけ・`-simulate` は条件 4 の根拠にしない）が判定役の文面で守られる | (a) | 「検査が重いとき」の節 | 文面の読み |
| A9 | 版を 3 種類で揃えて上げ、`check-all.py` が緑 | CI | 版の行 | `check-all.py`・`check-plugin-versions.py` |
| A10 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: Formal Checker（モデル）が文面どおりに状態数を報告し、打ち切りを置いた前提に書くか——振る舞いは Eval でしか当たらず、spec-loop の Formal Checker の Eval は無い。PR コメントで人間レビューに回す。

**生成物**: なし（図・`SKILL.md` の測定値（dev-loop の §8.2）は触らない。`skill-metrics.py --check` は `check-all.py` が回す）。

## 未解決の判断

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1339-tlc-heavy-checks`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1339`・起点 `3003d6c3`・base 参照 `origin/main`（`refs/remotes/origin/HEAD`）= `3003d6c31499d041ef76ae7b1b6fccf5234ad616`
- 割り目（手順 4）: `AskUserQuestion` で訊いた（実装のコミット `7839384a` の後）——300 秒応答なし。続けた
- 1 パス目: Verifier（`dev-loop:dev-loop-verifier`・sonnet。起動を確かめた）反証 2 件・`/code-review`（high）指摘 8 件。どちらも終点 `2153a66d`。1 パス目の指摘対応の起点 = `2153a66dc2f55735d5f7326208bf93b577381f6c`。直す 9 件（V1・V2・CR1〜5・CR7・CR8）・残課題 1 件（CR6）→ 2 パス目を回す
- 1 パス目の指摘対応: コミット `ea0f72d0`（直す 9 件）。2 パス目の起点（= 2 パス目の指摘対応を始める直前の HEAD）は 2 パス目の関門の後に書く。残り: 手順 5 の当て直し（Verifier 2）と `/code-review` 2 の両方
- 割り目（2 パス目の前）: `AskUserQuestion` で訊いた——300 秒応答なし。続けた
- 実験: 上の「決めた値」（`-workers` の比較）。交絡: 反例が 1 つしか無いモデルでは揺れが出ないので、最短の反例が多数あるモデルを選んだ。`-workers 1` の 8 回が 1 種類であることが、比べ方（トレースの抜き出し）が時刻などで揺れていないことの対照。dump の比較は判別しない（`-workers 1` でも揺れる）ので主張に使わない。観測窓: 1 つのモデル・各 8 回・28 コアのこの機械。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| SYMMETRY・VIEW・`-simulate`・Apalache を仕組みに入れるか | 入れない | Issue の「やらないこと」——判定と図の前提を崩す |
| `-workers` を走らせ直しの中で自動で足すか | 足さない | 呼び方は正本の `CLAUDE.md` の行のまま（`check-tlc.py` の決まり）。足すかは利用者が決める |
| 状態数が読めないとき判定を変えるか | 変えない | 状態数は診断の材料で、判定の根拠ではない |

### 1 パス目の指摘の採否（Verifier 2 件・/code-review 8 件）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | `CONSTRAINT` で刈ったモデルで `PROPERTY` を回すと、時相の性質の違反が「反例なし」になる | 示せる——scratchpad の `exp/cons.sh`（本物の TLC 2.19）: `<>[](c = 0)` を `CONSTRAINT c < 4` つきで `No error has been found`、外すと `Temporal properties were violated.` | A2・A3 | 直す |
| V2 | `-simulate` で見つけた反例を `反例あり` と書く文面が、Issue の「やらないこと」と食い違う | 示せる——`formal-checker.md` の該当行と Issue 本文 | A8 | 直す |
| CR1 | 英語でないロケールの JVM では進み具合の行の桁区切りが `.`・U+202F になり、`DISTINCT` が最後の 3 桁だけを読んで数を作る | 示せる——`exp/locale.sh`: `-Duser.language=de` で `12.118.483 distinct states found`、`fr` で U+202F 区切り | A4（読めなければ読めなかったと出す） | 直す（`,` 区切りの最後の行の試料は本物と違う（CR4）ので、同じ直しで本物の形にする） |
| CR2 | `-Xmx`・`-fpmem` で「変わらなかった」は 356 状態のモデルでメモリが効かない範囲の観測で、判別していない | 示せる——計画の実測の規模 | A6（書いた実測が事実であること） | 直す（測った範囲まで主張を弱める） |
| CR3 | `-fpmem` の「割合か MB」はヘルプに無い（ヘルプは (0.0,1.0) の割合だけ） | 示せる——`exp/locale.sh` の `-help` の出力 | A6 | 直す |
| CR4 | 偽の TLC の最後の行が桁区切りつきで、本物（区切りなし）と違う | 示せる——`exp/locale.sh` の `de` の小さいモデルの最後の行 `1681 distinct states found` | A4 の証明 | 直す（CR1 と一緒） |
| CR5 | 本体の反例の行の注記と経過時間の形を見る試料が無い | 示せる——`{weight}` を本体の反例の行から消しても 20 件が通る（指摘の記述。著者は当てていない） | A4 の証明 | 直す |
| CR6 | 判定役の時間の上限と走らせ直しの `--timeout`（既定 600 秒）が結ばれていない | 示せない（起こりうる筋書き） | 無し | 残課題 |
| CR7 | `-simulate` を足すことが「呼び方のオプションを自分で足さない」と食い違う | 示せる——同じ節の 2 か所 | A8（V2 と同じ行） | 直す（V2 と一緒） |
| CR8 | 「実行の設定が重い」の行き先（3）に打つ手が無い | 示せる——節の手順 1 と 3 | A2（試す順がある） | 直す（呼び出し元にオプションを報告で勧める） |

## 関門の記録

```dev-loop-gates
周の base: 3003d6c31499d041ef76ae7b1b6fccf5234ad616
関門: Verifier 1 2153a66dc2f55735d5f7326208bf93b577381f6c 反証=2
関門: /code-review 1 2153a66dc2f55735d5f7326208bf93b577381f6c 指摘=8
```
