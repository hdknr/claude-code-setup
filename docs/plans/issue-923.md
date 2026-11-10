# Issue #923 — 形式検査の反例のトレースを、実行順を強制して再現する Red テストにする（#908 の後半）

不在の周（`/dev-loop:cruise 916 --absent` の起動・2026-11-08T08:00Z、利用者の確認（起動時・2026-11-08T08:00:42Z、配布を見せて確かめた））。cruise #916 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かない）。従う版は dev-loop 1.103.0（キャッシュ。SKILL.md 1861 行）。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-916`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #916 -->`。台帳の `decisions` は親が書く）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認・マージ前の判断: 台帳に線なし（止まる）
- 版の上げ方: **minor・spec-loop だけ**（main の先端 spec-loop 0.74.0 → 0.75.0。scaffold がトレースのケースから Red テストを作る——能力の追加。
  トレースのケースを持たない中間表現の生成物は 1 バイトも変わらない）。dev-loop は触らない（下の「dev-loop の写し」）。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」。並行する周 #922 も spec-loop を上げる）
- PR は `Fixes #923`・`Refs #916`・`Refs #908`（確認の Issue #928 は閉じるキーワードで指さない）
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/cruise/scripts/run-serial.py` 越し

## 周の在り処

- ブランチ: `issue/923-trace-red-tests`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-923`
- 起点コミット: `ad90fbc`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `ad90fbca0e97982991e7a34752c74e4eb6108e54`

## 変更範囲

触る:
- `plugins/spec-loop/scripts/scaffold.py` — 中間表現のトレースのケース（`cases` の要素で `trace` を持つもの）の検査と、そこから作る Red テスト・Issue の本文・v2 の変化の判定・`--red-check`・性能テストの入力
- `plugins/spec-loop/references/spec-ir.md` — トレースのケースの形と、実装に求める口（原本）
- `plugins/spec-loop/references/handoff-issue.md` — `## Red テスト` の実装を置く場所に口が出ること（spec-ir.md を指す）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 仕様のトレースのケースを中間表現に書き起こす
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 範囲の中の反例で仕様を直したら、判定役が返したトレースを仕様のテストケースとして書く
- `plugins/spec-loop/agents/formal-checker.md` — 反例ごとにトレース（呼び出しと段の並び・初めの状態）を返す
- `scripts/test-scaffold.py` — 試料（陽性対照: 競合する実装で赤・正しい実装で緑）と変異と、口の名前の原本との突き合わせ
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（6 本）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-923.md` — この計画
- `CLAUDE.md` — `scaffold.py` の項にトレースのケースを 1 句足す

触らない:
- dev-loop（`spec-fingerprint.py`・`spec-gap.md`）——機能の指紋の式（機能のオブジェクトの sha256）・印・節は変えない。トレースのケースは機能のオブジェクトの中にあるので指紋に入り、Red テストの sha256 にも入る
- Issue の印の版（`spec-loop-handoff: v3`）——節と印は変えない（`## 受入基準` の表の行と `## Red テスト` の文が増えるだけ）
- 実案件の R21-10 のトレース（他リポジトリで、モデルもトレースも残っていない）
- Python 以外の言語の Red テスト（scaffold は今も Python の `unittest` だけを作る）
- `spec-exit.md` の条件 3 の数え方（トレースのケースもテストケースとして仕様に書くので、今の決まりのまま数える）
- トレースのケースの v2 での `回帰`・`変更` 以外の扱い（撤去はケースと同じ）

複製の数（同じことを述べている箇所）: 「トレースのケースの形と実装に求める口」を述べるのは **5 箇所**——`spec-ir.md`（原本）・`scaffold.py`（生成するテストと本文の 1 行）・
`handoff-issue.md`（指す）・scaffold の `SKILL.md`（指す）・`test-scaffold.py`（口の名前を原本と突き合わせる）。「反例のトレースを仕様のテストケースにする」は
spec-review の `SKILL.md` と `formal-checker.md` の **2 箇所**（返す側と書く側で、分けられない）。**分けない理由**: 口の名前（`checkpoint`・`reset_state`）は `scaffold.py` の定数に 1 つだけ置き、
文書は spec-ir.md を指す。テストが定数と原本の表を突き合わせる。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージで GitHub Pages とプラグインのカタログに入る。マージは親。

## 仕様の穴（不在の線で推奨により決めた）

**穴 1: トレースを実装に当てる口をどう作るか。** Issue は「トレースを実装に当てる口の設計から始める」と言うが、形は決めていない（Issue の「先に決めること」）。
scaffold の Red テストは `<impl_module>.<operation>(**input)` を 1 回呼んで返り値を比べるだけで、実行順を強制する口が無い。

| 選択肢 | 何が起きるか |
| --- | --- |
| **A（推奨）: 段の前で止める口と、状態を空に戻す関数を実装に求める** | 実装の関数はキーワード引数 `checkpoint`（既定は何もしない）を受け取り、トレースに出る段の前で `checkpoint("<段>")` を呼ぶ。モジュールは `reset_state()` を持つ。生成した Red テストは呼び出しをスレッドで走らせ、`checkpoint` で止めてトレースの順に 1 段ずつ進め、終わったら結果と後の状態を期待と比べる。排他で守った実装では、止めた呼び出しが排他を待って次の段に来ないので、その時点で順の強制をやめて全部を走らせる——正しい実装はどの順でも正しいので緑になる。言語は今の Red テストと同じ Python |
| B: 実装をジェネレーター（段ごとに `yield`）で書かせる | スレッドも待ち時間も要らず決定的だが、実装の書き方そのもの（関数をジェネレーターにする）を決めてしまい、排他（ロック）で守る実装を書けない |
| C: 実行できるテストは作らず、トレースを Issue の本文に表で載せる | 口を決めずに済むが、Issue の受入基準 2（競合する実装で失敗し、正しい実装で通る）を満たさない |

- **決めた値: A。** 推した理由: 今の Red テスト（Python の `unittest`・`impl_module` の関数）の形に足すだけで、排他で守る実装・比べて書く実装のどちらも書ける。
  B は実装の手段を決めてしまい、`formal-checker.md` の「特定のロックの方式・取る順序を前提にしない」に反する。C は受入基準を満たさない。
  **口は手段ではなく観測点である**——段の名前は仕様（モデルの行為）の名前で、実装はその段の前で知らせるだけ。止めるかどうかはテストが決める。
- **既知の代償**: (1) 段を待つのは時間で区切る（1 段 2 秒）。負荷で呼び出しが 2 秒より遅れると、順の強制をやめて全部を走らせるので、**競合する実装を見逃すことがある**（正しい実装を赤にすることは無い——どの順でも正しいので）。
  (2) 実装は各呼び出しで `checkpoint` を 1 回以上呼ぶ——呼ばない実装はトレースを当てられないので失敗にする（`checkpoint` を無視する競合する実装を素通りさせないため）。
- 使った線と出所: `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線（台帳 `issue-916`））。
- 確認の Issue: PR を作った後に立てる（重さ: PR にあってまだマージしていないこと）

## verify の受入基準（不変条件 × 経路）

入口: **`scaffold.py`**（生成・`--check`・`--dry-run`・`--red-check`・`--upto`・v2 の変化の判定・Issue の本文・性能テスト）・**生成した Red テスト**（`python3 -m unittest discover -s scaffold/tests`。
dev-loop の周と `--red-check` が走らせる）・**dev-loop の写し**（`spec-fingerprint.py` が本文の指紋を確かめる）・**仕様を書く側**（Formal Checker → spec-review → 仕様 → scaffold が中間表現に書き起こす）・**利用者**（文書を読む）。

| # | 不変条件 | 経路（入口）と確かめ方 |
| --- | --- | --- |
| 1 | 反例が出た対象（`spec/formal/<対象>/README.md` が在る）を名指しするトレースのケースから、`scaffold` の生成物 `scaffold/tests/test_<機能>.py` にトレースを再現する Red テスト（ケース 1 件 = テスト 1 本）が含まれる（Issue の受入基準 1） | `test-scaffold.py` の試料。**実走**: 本物の TLC で小さいモデルの反例を出し、そのトレースを書き起こした中間表現から作る（下の「実走」） |
| 2 | そのテストは、トレースの実行順で競合する実装では失敗し、正しい実装（排他で守る）では通る（陽性対照。Issue の受入基準 2）。実装が無い・`reset_state` が無い・`checkpoint` を受け取らない・`checkpoint` を呼ばない実装でも失敗（エラーではない） | `test-scaffold.py` の試料（実装を差し替えて `unittest` を走らせる）。実走の試料にも当てる |
| 3 | トレースのケースを持たない中間表現の生成物（OpenAPI・型・Red テスト・本文）は 1 バイトも変わらない。機能の指紋の式は変わらない（dev-loop の写しが一致したまま） | `test-scaffold.py` の `BASE_SHA256` と指紋の突き合わせ（既存の試料） |
| 4 | 決まりに反するトレースのケースからは作らない（1）——`formal` の対象のディレクトリが無い・名前の形・呼び出しが 2 つ未満・`operation` が中間表現に無い・入力や期待が型に反する・段の呼び出しが `calls` に無い・段の名前の形・`calls` のどれかが段に出ない・`outcomes` と `after` の両方が無い・`outcomes` の数が呼び出しの数と違う・`checkpoint` という入力の項目・`reset_state` という入口の名前・`input`／`expected` と `trace` を一緒に書く・機能に入出力のケースが 1 つも無い | `test-scaffold.py` の試料（exit 1 と名指しの文言）と変異 |
| 5 | Issue の本文の受入基準の表にトレースのケースの行が出て、`## Red テスト` の実装を置く場所に口（`checkpoint` と `reset_state`）が出る。v2 で、トレースを変えたケースは `変更`、同じなら `回帰`。`--red-check` はトレースのケースも数える | `test-scaffold.py` の試料 |
| 6 | 性能テストはトレースのケースを入力に使わない | `test-scaffold.py` の試料 |
| 7 | 文書（spec-ir.md・handoff-issue.md・scaffold と spec-review の SKILL・`formal-checker.md`）が同じ口を述べ、口の名前は `scaffold.py` の定数と原本の表で一致する | `test-scaffold.py` の突き合わせ・読み |
| 8 | 版が 3 種類の箇所で 0.75.0 に揃う。歯止めが全部緑 | `check-all.py`（run-serial 越し）・PR 側の CI |

**掛け算**: 受入基準を両方の関門 × 2 パス（2 パス目が無ければ 1 パス目の 2 つ）。

### 実走（受入基準 1・2）

本物の TLC（`java -cp /Users/hdknr/.local/share/formal-tools/tla2tools.jar tlc2.TLC`）で、在庫を読んでから減らす 2 つの書き手のモデルを走らせて反例（売り越し）を出し、
TLC が出したトレース（行為の並び）を、spec-ir.md の形のトレースのケースに書き起こす。その中間表現から `scaffold.py` で作った Red テストを、
競合する実装（読んでから書く）と正しい実装（排他で守る）に当てる。**書き起こすのは著者**——spec-review と scaffold の LLM が同じ書き起こしをするかは確かめない（下の「未証明」）。

### 実走の結果（2026-11-10）

試料の正本: `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/f7631199-07c6-418e-a902-1e3ccac0123f/scratchpad/run923/repo`（在庫の 3 機能。
`docs/v1/spec/formal/stock-reserve/` に TLC のモデル `StockReserve.tla`・`.cfg` と記録 `README.md`。仕様 `spec/stock.md` にトレースのテストケース `S1-T1`）。

- **TLC**（`java -cp /Users/hdknr/.local/share/formal-tools/tla2tools.jar tlc2.TLC -deadlock StockReserve`。TLC2 2.19。run-serial を通さずに走らせた——1 秒で終わる）:
  `Invariant NoOversell is violated`。反例は `Read`（first）→ `Read`（second）→ `Write`（first）→ `Write`（second）で、2 つとも `ok`・在庫 0（13 states・12 distinct）。
  この行為の並びを `steps` に、`Read`・`Write` を段の名前 `read`・`write` に書き起こした（中間表現の `F-001-C2`）。
- **生成**: `scaffold.py --repo <試料>` が 0（機能 3・ケース 4・本文 3）。`scaffold/tests/test_f_001.py` に `test_f_001_c2`（`self.trace(...)`）が入った。
- **Red テスト**（run-serial 越し。`python3 -B -m unittest discover -s scaffold/tests` を各 3 回）:

| 実装 | 結果（3 回とも同じ） |
| --- | --- |
| 無い | `FAILED (failures=4)`——トレースのケースは `未実装: spec_impl.reset_state が無い` |
| 競合する実装（読んでから書く。排他なし） | `FAILED (failures=1)`——`test_f_001_c2` だけが `結果が期待と違う: second が {'ok': True} を返した（期待の残り [{'error': 'OUT_OF_STOCK'}]。トレースの 4/4 段まで順に進めた）` |
| 正しい実装（読むから書くまでを排他で守る） | `OK` |

- **交絡**: 競合する実装が赤になったのが「順を強制したから」か「たまたま競合したから」かは、`test-scaffold.py` の変異「順を強制しない」（`drive` が段を 1 つも進めない）で
  同じ試料が緑になる（＝変異が殺される）ことで分ける——順を強制しなければ競合する実装も 2 つの呼び出しが順に走って緑になる。
- **確かめた範囲**: TLC の反例から中間表現への書き起こしは著者が手で行った（spec-review・scaffold の LLM が同じことをするかは確かめていない）。

### 未証明・BLOCKED

- **未証明**: 段を待つ時間（2 秒）を超えて呼び出しが遅れる負荷の下で、競合する実装を見逃さないこと——時間で区切る以上、原理的に保証できない（正しい実装を赤にしないことは、どの順でも正しいことから言える）。人間のレビューに回す。
- **主張から外したもの**: spec-review と scaffold の LLM が、仕様のトレースを手順どおりに書き起こすか（手段はある——`claude -p` で正本ごと回す——が回していない。#908 の受入基準 1 と同じ扱い）。
- BLOCKED なし。

### 生成物

- 該当なし——図・生成ブロック（`skill-metrics.py` は dev-loop の `SKILL.md` だけを測る）・カタログの生成物を触らない。`scaffold/` は正本リポジトリの生成物で、このリポジトリには無い。

## 未解決の判断・確認待ち

- 穴 1 の確認（確認の Issue。閉じるのは利用者）

## 関門の進捗（再開点）

- 割り目（手順 4・手順 6）: 割らない（cruise の周）

## 手順 8

- この周の起票: 1 件（仕様の穴を不在の線で推奨により決めた確認の Issue——PR を作った後に立てる。起票の承認は不在のため訊いていない）

## 既知の限界・決着済みの論点

- 口の形は推奨で決めた値（上の「仕様の穴」。確認の Issue が持つ）。
- 段を待つ時間で区切るので、負荷の下では競合する実装を見逃しうる（未証明。正しい実装を赤にはしない）。
- 実装は各呼び出しで `checkpoint` を 1 回以上呼ぶ（呼ばなければ失敗）——トレースに出ない段だけを持つ正しい実装（1 回の原子的な更新など）も、どこかで `checkpoint` を呼ぶ。
- `outcomes` は呼び出しとの対応を持たない（どの呼び出しが勝つかは正しい実装でも順で変わる）——結果の多重集合として比べる。
- R21-10 の実データは他リポジトリでモデルもトレースも残っていない——試料は合成のモデル（TLC で反例を出したもの）。
- dev-loop は触らない——トレースのケースは機能のオブジェクトの中にあり、指紋と Red テストの sha256 が覆う。
