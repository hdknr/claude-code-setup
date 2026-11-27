# Issue #1594 — spec-loop: TLC の状態グラフ（-dump dot）の .dot を使い終わったら消す

利用者の指示（2026-11-27）: 「使い終わって不要になった dot ファイルを削除して spec-loop を回すようにして」。
親セッションからの委譲（サブエージェント）で回す。割り目（手順 4・手順 6）では訊かずに「このまま続ける」。マージはしない（PR 側の CI の最終結果を見るところまで）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/formal-statechart.py` — モデルごとに dot を消す・信号で片付ける・持ち主の居ない古い一時ディレクトリを回収する
- `plugins/spec-loop/scripts/check-tlc.py` — `run_model` が例外（信号を含む）で抜けるとき TLC のプロセスグループを止める
- `plugins/spec-loop/agents/formal-checker.md` — 図の対応の確認の dump を `mktemp -d` の専用ディレクトリに書き、終えたら消す
- `scripts/test-formal-statechart.py` — 片付けの試料と変異
- `scripts/test-check-tlc.py` — `run_model` の片付けの試料（要るなら）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1594.md` — この計画

触らない:

- `-dump dot` をやめること（図の材料なので続ける）
- 写した cfg から `PROPERTY`／`PROPERTIES` を外すこと（下の「決めたこと」1）
- dot の大きさの上限で TLC を止めること（Issue の「任意」。下の「決めたこと」4）
- `check-alloy.py`・`check-formal-rerun.py`（dump を書かない）
- 古い形（pid の無い）`spec-loop-statechart-*` の回収（持ち主が分からない。下の「決めたこと」3）

依存の追加・更新: なし
仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本を持たない——プラグインの原本）
差分テスト: なし（リファクタリング・移行・書き直し・性能改善の周ではない。図の中身は既存の試料が本体と別に読んだ状態グラフと突き合わせて見ており、この周はその試料を全部通すことを受入基準 6 にする）
プロパティテスト: なし（往復・冪等性・等価性・数値の境界の不変条件を持たない。ファイルの片付けと信号の扱い）

## 決めたこと（推奨で決めた判断と理由）

1. **`_liveness.dot` は出たら即座に消す（cfg から `PROPERTY` を外さない）。** 外すと TLC が検査するものが変わり、
   時相の性質の反例で描かずに 1 を返す判定（「時相の性質の反例は描かない」）と、`--controls` の「違反が出る」の判定が図の作成の回だけ変わる——図が検査と別のモデルから描かれる。
   消すのは TLC が走り終えた直後（図はこのファイルを読まない）。TLC が走っている間の 1 モデル分の大きさは残る（4）。
2. **モデルの dot は、読み込んだ直後に消す**（図を描く前）。描けずに止まる回（`Stop`）は実行がそこで終わり、一時ディレクトリごと消える。溜まる上限を全モデルの合計から 1 モデル分にする。
3. **一時ディレクトリの名前に持ち主の pid を入れる（`spec-loop-statechart-<pid>-…`）。起動時に、その形で pid のプロセスが居ないものだけ消す。**
   居る（pid が再使用された場合を含む）・権限で分からない・古い形（pid が無い）は消さない——並行する別の実行の作業中のディレクトリを消さないほうに倒す。
   古い形の残骸（Issue で観測した `spec-loop-statechart-zzflmv9r` など）はこの周では回収しない（PR に書く）。
   **持ち主が居なくても、一時ディレクトリに記録した TLC のプロセスグループ（`.tlc-group`）がまだ居れば消さず、番号を言う**（2 パス目の /code-review の指摘 CR2-1。SIGKILL の後も別のセッションの TLC は書き続けるので、消してもディスクは空かず見えなくなるだけ。TLC を止めるかは人が決める——pgid の再使用で無関係のグループを止めないため、自動では止めない）。
4. **dot の大きさの上限は入れない**（Issue の「任意」）。TLC が走っている間にファイルの大きさを見張る仕組みが要り、別の変更になる。1・2 で溜まる量は 1 モデル分に下がる。
5. **SIGTERM・SIGINT・SIGHUP を受けたら例外（`BaseException` の子）にして、TLC のプロセスグループを止め、一時ディレクトリを片付けて、終了コード 128+信号の番号で終わる。`--out` には触らない。**
   2 回目の信号は無視する（片付けの途中で止められないように）。プロセスグループを止めるのは `check-tlc.py` の `run_model`（`start_new_session=True` で起こした TLC を `communicate` の途中の例外で置き去りにしていた）。
6. **Formal Checker の図の対応の確認**: `mktemp -d` で作ったディレクトリに dump を書き、確かめ終えたらディレクトリごと消す、と手順に書く（`/private/tmp` 直下に書かない）。

## 乗るデプロイ経路

main へのマージでプラグイン（spec-loop）の配布と GitHub Pages の再ビルド（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。この周はマージしない。

## 受入基準（不変条件 × 経路）

経路（`formal-statechart.py` の入口と終わり方）: (a) 描けて 0、(b) 描けずに 1・4（`Stop`。モデルの途中を含む）、(c) 想定外の例外で 2、(d) SIGTERM・SIGINT・SIGHUP、(e) SIGKILL（片付けが走らない）、(f) 時間切れ（`run_model` の内側）。
dot を書くほかの入口: (g) Formal Checker の図の対応の確認（エージェントの手順）。dump を書かない入口（`check-tlc.py` の `probe`・`check-formal-rerun.py`・`formal-sync.py`）は対象外。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | 走らせた後、`$TMPDIR` に `spec-loop-statechart-*` も `.dot` も残らない | a・b・c | `TemporaryDirectory` と 2 | 試料（偽の TLC。`TMPDIR` を試料ごとの空のディレクトリにして見る）と本物の TLC（小さいモデル 3 つ） |
| 2 | 1 つのモデルを走らせている間、前のモデルの `.dot`・`_liveness.dot` が一時ディレクトリに無い | a・b | 2 | 偽の TLC が起動時に cwd の `.dot` を記録し、試料で見る（`--controls` の 2 モデル・`PROPERTY` のある試料） |
| 3 | `_liveness.dot` を残さず、`PROPERTY` は外さない（時相の性質の反例は今までどおり 1） | a・b | 1 | 偽の TLC が `PROPERTY` のある cfg で `<名前>_liveness.dot` を書く（本物で確かめた名前）。既存の試料「時相の性質の反例は描かない」が 1 のまま |
| 4 | SIGTERM・SIGINT・SIGHUP を受けたら、一時ディレクトリが残らず、TLC のプロセス（グループ）も残らず、`--out` に触らず、128+信号で終わる | d | 5 | 試料（眠る偽の TLC に信号を送り、その pid が居なくなったこと・ディレクトリが無いこと・`--out` が古いままを見る）。本物の TLC（java）でも SIGTERM を 1 回 |
| 5 | SIGKILL で残った（持ち主の居ない）pid つきのディレクトリを次の起動で消し、持ち主の居るもの・古い形は消さない | e | 3 | 試料 |
| 6 | 図の中身・終了コードは今までの試料のとおり（既存の試料と変異が全部通る） | a・b・c・f | 変えない | `scripts/test-formal-statechart.py`・`scripts/test-check-tlc.py` |
| 7 | 時間切れのとき TLC のプロセスグループを止める（今までどおり） | f | `run_model` | 既存の試料「時間切れ」 |
| 8 | Formal Checker の手順が、dump を `mktemp -d` の専用ディレクトリに書き、確かめ終えたらディレクトリごと消すと書き、その手順どおりに走らせると `.dot` が残らない（文面の事実の真偽） | g | 6 | 手順の文面のコマンドを本物の TLC で小さいモデルに当てる |
| 9 | エージェント（Formal Checker）が実際にその手順に従う | g | 6 | **未証明**——LLM の振る舞い。PR で人間のレビューに回す |
| 10 | 版が 3 か所（`marketplace.json`・`plugin.json`・`SKILL.md` の 2 行）で揃い、歯止めが全部通る | — | 0.137.1 | `python3 scripts/check-all.py`・PR 側の CI |
| 11 | 両方の関門に受入基準を渡す × 2 パス（4 つの受け渡し。2 パス目が該当なしなら 2 つ） | — | 手順 5・6 | 関門の記録 |

この環境で証明できないもの: 9（未証明）。大きなモデル（数 GB の dot）での実測はしない（ディスクを大きく使う検査はしない、という委譲の指示）——溜まる量の上限が 1 モデル分になることは 2 で、仕組みとして見る。

生成物: `docs/` の設計ドキュメントの生成ブロック（`scripts/skill-metrics.py`）——`SKILL.md` の版の行だけを変えるので行数は変わらない見込み。`python3 scripts/skill-metrics.py --check` で鮮度を見る。図（drawio）は触らない。

複製の数: dump と後片付けを述べる箇所は 2 つ（`formal-statechart.py` の docstring、`agents/formal-checker.md` の図の対応の節）。`references/tree.md`・`README.md`・`CLAUDE.md` は dump に触れるが後片付けは述べていない——書き足さない（分けない理由: 原本は docstring で、他は指すだけ）。

## 未解決・確認待ち

- なし（判断は「決めたこと」に推奨で決めた）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1594-statechart-dot-cleanup`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1594`、起点 `1af47399`（origin/main）、base（`origin/HEAD` → `1af473994d1a756440930ed38efb97ab881e1115`）
- 直す線: 既定（出所: `.claude/dev-loop.md` に `直す線:` の行が無く、委譲の指示で AskUserQuestion を使わない——答えが返らないものとして既定）
- 割り目（手順 4）: このまま続ける（委譲の指示。訊かない）
- 1 パス目の指摘対応の起点: `9558fd6e`（1 パス目の関門に渡した時点の HEAD）
- 関門: Verifier 1 パス目 通した——反証 0 件（観察 5 件。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-taiheigroup-new-taihei-prm/76270eb4-090f-4e2a-90b1-fd44f1a39390/scratchpad/cs-1594/gate-1594-verifier-1-20261127T015959Z.md`、終点 9558fd6e）。/code-review 1 パス目 通した——指摘 9 件（直す 2・残課題 7。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-taiheigroup-new-taihei-prm/76270eb4-090f-4e2a-90b1-fd44f1a39390/scratchpad/cs-1594/gate-1594-code-review-1-20261127T015959Z.md`、終点 9558fd6e）
- 手順 5 の反証による手順 4 への差し戻し: なし（Verifier の反証 0 件）。/code-review の指摘 2 件を 1 パス目の指摘対応で直した
- 割り目（手順 6・2 パス目の前）: このまま続ける（委譲の指示。訊かない）
- 関門: Verifier 2 パス目 通した——反証 1 件（V2-1。報告 `/private/tmp/claude-503/-Users-hdknr-Projects-taiheigroup-new-taihei-prm/76270eb4-090f-4e2a-90b1-fd44f1a39390/scratchpad/cs-1594/gate-1594-verifier-2-20261127T024500Z.md`、終点 4ea51462）。/code-review 2 パス目 通した——指摘 8 件（報告 `/private/tmp/claude-503/-Users-hdknr-Projects-taiheigroup-new-taihei-prm/76270eb4-090f-4e2a-90b1-fd44f1a39390/scratchpad/cs-1594/gate-1594-code-review-2-20261127T024500Z.md`、終点 4ea51462）
- 2 パス目の指摘対応: 起点 `4ea51462`（指摘対応を始める直前の HEAD）。直すのは CR2-1・CR2-2・CR2-5（下の採否の表）。終点はコミットの後に書く
- 2 パス目の後片付け: /code-review 2 パス目の体が scratchpad の `cr2-tlc/` に本物の TLC の .dot を 5 個残した（委譲文の「必ず消す」に反した）——親が消した
- 交絡を潰した手順: 本物の TLC での実測に陽性対照を取った——同じ試料を周の base の `formal-statechart.py` で走らせ、片付けが無いと出る形が出ることを見た
  （小さい 4 モデル: 走っている間の .dot の最大が base 7 個 → 直した版 2 個（1 モデルの状態グラフと _liveness）。SIGTERM: base は java が残り TMPDIR に 55M のディレクトリと .dot が残った → 直した版は rc=143・java なし・残り 0）。
  回帰テストの「前のモデルの .dot が残ったまま次を走らせた」の検出は、変異「状態グラフを読んでも消さない」が赤になることで陽性側を見た。観測窓: 見張りは 0.1 秒ごとに数えた（それより短く出て消えた .dot は数えていない）

```dev-loop-gates
周の base: 1af473994d1a756440930ed38efb97ab881e1115
関門: Verifier 1 9558fd6e 反証=0
関門: /code-review 1 9558fd6e 指摘=9
関門: Verifier 2 4ea51462 反証=1
関門: /code-review 2 4ea51462 指摘=8
```

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `_liveness.dot` を出さない（`PROPERTY` を外す）か、出たら消すか | 出たら消す | 「決めたこと」1 |
| dot の大きさの上限 | 入れない | 「決めたこと」4。Issue の任意 |
| 古い形の `spec-loop-statechart-*`（pid なし）を回収しない | 回収しない | 持ち主が分からず、並行する実行を壊しうる。PR に書く |
| TLC が走っている間の 1 モデル分の dot | 残る | TLC が走りながら書く。上限は 4 |

### 1 パス目の関門の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1 `nohup`・バックグラウンドで呼び出し元が付けた SIG_IGN を on_signal が上書きする（SIGHUP・SIGINT で止まる） | 示せる（`nohup` の下で getsignal が SIG_IGN。上書きはコードの通り） | 無し（受入基準は止められたときの片付け。止めないべき場面は基準に無い） | 残課題 |
| CR1-2 TemporaryDirectory の rmtree の途中に信号が届くと一時ディレクトリと .dot が残り、「消した」と出る | 示せる（rmtree の入口で SIGTERM を送るラッパーで rc 143・ディレクトリが残った。/code-review が実行） | 4 | 直す——`except Interrupted` で自分の pid の一時ディレクトリを消し直す。試料「信号: 片付けの途中」と変異を足した |
| CR1-3 Popen の前後・時間切れの節の数命令の窓に信号が届くと TLC が残る | 示せない（コードの読解のみ） | 4 | 残課題 |
| CR1-4 TLC_MUTATIONS の変異が時間切れでしか落ちず、時間切れの経路で偽の TLC を置き去りにする | 示せる（変異で 30.2 秒の時間切れ・ppid 1 の偽の TLC が残った） | 4（証明手段の陽性対照が旧い挙動を作っていない） | 直す——変異を `except BaseException` の節ごと外す形にし、時間切れの経路で偽の TLC を止める |
| CR1-5 communicate の OSError が戻り値でなく例外になった | 示せない（再現していない） | 無し | 残課題 |
| CR1-6 SIGHUP で stderr が閉じていると print の OSError で 128+n にならない | 示せない | 無し | 残課題 |
| CR1-7 PID 名前空間の違うコンテナと TMPDIR を共有すると reclaim が作業中のディレクトリを消しうる | 示せない | 無し | 残課題（既知の限界に足す） |
| CR1-8 check-alloy.py の run_model も同じ形で Alloy を置き去りにする（周の前から） | 示せない | 無し | 残課題 |
| CR1-9 非対話の実行で Formal Checker の `rm -rf` が権限で止まりうる | 示せない | 無し | 残課題 |
| V1 観察 1〜5（rmtree 中の信号・名前空間・Popen の窓・`states/` が cwd に残る・macOS の mktemp） | 反証ではない（Verifier が観察として挙げた） | 無し | 1 は CR1-2 で直した。ほかは残課題 |
| PID 名前空間の違う環境の reclaim | — | — | 既知の限界（CR1-7） |

### 2 パス目の関門の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-1 「2 回目の信号は無視する」を殺す試料が無い（on_signal の SIG_IGN を外しても全部緑） | 示せる（Verifier が 2 回送るスクリプトで rc 1・残りを示した） | 無し（受入基準 4 は 1 回の信号） | 残課題 |
| CR2-1 SIGKILL の後、走り続ける TLC の一時ディレクトリを回収が消して「消した」と言う（ディスクは空かず見えなくなる） | 示せる（偽の TLC で、SIGKILL の後の起動が消し、TLC は生きていた） | 5 | 直す——TLC のプロセスグループを `.tlc-group` に書き、居る間は消さずに番号を言う。試料「SIGKILL の後に TLC が走っている」と変異 2 件 |
| CR2-2 経路 c（想定外の例外で 2）の試料が無い | 示せる（c の片付けを壊す変異を殺す試料が無い） | 1（証明手段が経路 c を見ていない） | 直す——render を例外にするラッパーの試料「想定外の例外」と変異 |
| CR2-3 handler を付けてから try に入るまで・run の後に信号が届くと rc 1 | 示せない（読解のみ） | 無し | 残課題 |
| CR2-4 回収済みの proc に killpg を送りうる（pid の再使用） | 示せない | 無し | 残課題 |
| CR2-5 Formal Checker の手順の dump のパスに `.dot` を含むと、TLC が `_liveness` を書けずに止まる | 示せる（TLC 2.19 で `x.dotty/M.dot` に rc 255） | 8（文面の手順が事実として通らない） | 直す——パスに `.dot` を含めない、と手順に書いた |
| CR2-6 計画の「決めたこと 2」の「finally」が実装と違う | 示せる（実装に finally が無い） | 無し（計画は成果物でない） | 計画の文を直した |
| CR2-7 消せなくても「消した」と出す | 示せない | 無し | 残課題 |
| CR2-8 描けた後に信号を無視するので、読まないパイプに書くと止められない | 示せない | 無し | 残課題 |

## 手順 8 の記録

- この周の起票: 0 件（委譲の指示で起票を訊かない周。残課題は PR コメントに書く）
