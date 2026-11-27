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
2. **モデルの dot は、読み込んだ直後に消す**（図を描く前）。消すのは `finally` で、描けずに止まる回（`Stop`）も同じ。溜まる上限を全モデルの合計から 1 モデル分にする。
3. **一時ディレクトリの名前に持ち主の pid を入れる（`spec-loop-statechart-<pid>-…`）。起動時に、その形で pid のプロセスが居ないものだけ消す。**
   居る（pid が再使用された場合を含む）・権限で分からない・古い形（pid が無い）は消さない——並行する別の実行の作業中のディレクトリを消さないほうに倒す。
   古い形の残骸（Issue で観測した `spec-loop-statechart-zzflmv9r` など）はこの周では回収しない（PR に書く）。
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
- 関門: まだ
- 交絡を潰した手順: まだ

```dev-loop-gates
周の base: 1af473994d1a756440930ed38efb97ab881e1115
```

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `_liveness.dot` を出さない（`PROPERTY` を外す）か、出たら消すか | 出たら消す | 「決めたこと」1 |
| dot の大きさの上限 | 入れない | 「決めたこと」4。Issue の任意 |
| 古い形の `spec-loop-statechart-*`（pid なし）を回収しない | 回収しない | 持ち主が分からず、並行する実行を壊しうる。PR に書く |
| TLC が走っている間の 1 モデル分の dot | 残る | TLC が走りながら書く。上限は 4 |

## 手順 8 の記録

- この周の起票: 0 件（委譲の指示で起票を訊かない周。残課題は PR コメントに書く）
