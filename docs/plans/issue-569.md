# Issue #569 ほか — merge-versions.py の綴りの照合をまとめて直す（#569・#570・#572・#511・#571・#515。#514 は外す）

cruise #474 の周（#276。PR #517）が見つけた課題のうち、`plugins/spec-loop/scripts/merge-versions.py` とその決まり
（`references/versions.md`）・テスト（`scripts/test-merge-versions.py`）を触るものを 1 周・1 PR で回す
（利用者の決定（2026-10-30、親から伝達）: 同じファイルを触る Issue は 1 周にまとめる）。周の Issue は #569（ブランチの名前の元）。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-10-30）。台帳 `issue-474` の確かめた線:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））。
加えて利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、`要確認` の Issue を立てる
（書き方は `references/absent-lines.md` の「確認の Issue の書き方（#557）」）。
マージは親がする（この周は手順 6 の PR・CI の確認・手順 8 の件数の行まで）。台帳は書かない（親が書く。周の途中の課題は親に提案する）。

## まとめる範囲（推奨で決めた）

- **入れる**: #569（深い段の綴り）・#570（フックの `GIT_*`）・#572（外かを `rev-parse` で決める。#538 で承認済みの推奨）・
  #511（置き場所の中の構造ファイルの綴り違い）・#571（CI の Linux で大文字小文字の試料を走らせる）・#515（移行の手順）。
  どれも `merge-versions.py` の綴りの照合（`tracked`・`spelled`・`walk`）と、その決まり・テストに閉じる。
- **外す: #514**（版ごとに読む側——MkDocs のフック・`check-qa-csv.py`・`qa-to-pptx.py`・`check-feasibility-csv.py`・スキルの手順）。
  触るファイルが別（フックは正本リポジトリへ写して単独で動く別の決まりを持つ）で、任意のパスを受け取る CLI がパスのどこまでの綴りを見るかという
  別の設計が要る。`merge-versions.py` とは関数 1 つを共有するかどうかだけの結びつきなので、別の周に回す。PR では `Refs #514`。
  （出所: 親の指示「大きすぎれば推奨で分け、外した Issue は `Refs` に」。）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/merge-versions.py` — 綴りの照合を全段に（#569）・置き場所の中の構造ファイルの綴り違いを 1 に（#511）・`git` を呼ぶ環境から場所の変数を外す（#570）・外かを `rev-parse --is-inside-work-tree` で決める（#572）・docstring
- `scripts/test-merge-versions.py` — 試料と変異・区別しない FS を CI で求める印（#571）
- `.github/workflows/plugins.yml` — 区別しない FS（ext4 の casefold）を作って同じテストを回すステップ（#571）
- `plugins/spec-loop/references/versions.md` — 綴りの決まりの更新・移行の手順（#515）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — spec-loop の版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（5 本）
- `docs/plans/issue-569.md` — この計画
- `scripts/test-build-proposal.py` — 試料「綴りの違う内部の表はふつうのファイル」の期待と名前（「綴りの違う内部の表は重ね合わせが断る」に改名）だけ（**実装中に広げた**。#511 で `spec/QA-dev.csv` が
  重ね合わせで 1 になるので、タグから写して重ねる提案書の側も 1 になる——作業ツリーと同じ答え。名指しの変異「内部の表を綴りを見ずに外す」は
  新しい期待でも殺せる（外せば重ね合わせが通って作ってしまう）。`build-proposal.py` 本体は触らない。広げた分の受入基準は下の [#511-2]）

触らない:

- `plugins/spec-loop/scripts/build-proposal.py`（別の周が持つ。#512 もそのため外れている）
- #514 の読む側（`templates/mkdocs/hooks/spec_loop_pages.py`・`check-qa-csv.py`・`qa-to-pptx.py`・`check-feasibility-csv.py`・スキルの手順）
- `check-spec-exit.py`・`scaffold.py`（重ねた出力を読む側。#511 は重ね合わせの側で断るので、読む側は変えない）
- 他のスクリプトの `git` の呼び方（`check-signoff.py`・`check-frozen.py`・`scaffold.py`）——#570 は `merge-versions.py` の Issue

### 同じことを述べている箇所の数

「綴りをどこで照合するか」: `merge-versions.py` の docstring（冒頭の節・守らないの表・`tracked`・`spelled`）・`versions.md` の「重ねるもの」の箇条・
テストの docstring = 3 ファイル 6 箇所。分けない理由: 同じ関数の振る舞いを述べており、片方だけ直すと食い違う（#276 で起きた形）。

## 乗るデプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。マージは親。

## 周の在り処

- ブランチ: `issue/569-merge-versions-bundle`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-569`
- 起点: `eef9331`（origin/main）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `eef93311c540b522c2df260b88a2f86bff804277`

## verify の受入基準

各 Issue の受入基準（Issue 番号を付ける）:

- [#569-1] パスのどの段でも、index の綴りを使う
- [#569-2] 深い段の綴りが違う試料で、作業ツリーと `git archive` の書き出しの答えが一致する
- [#570-1] git を呼ぶ前に、これらの変数（`GIT_INDEX_FILE`・`GIT_DIR` など）を外すか絶対パスにする
- [#570-2] 相対の `GIT_INDEX_FILE` を設定した試料で、答えが変わらない
- [#572-1] 「リポジトリの外か」を `git rev-parse --is-inside-work-tree` で決める
- [#572-2] FS の境界・docs の上にある関係のない `.git` の試料で、外と読む形が 0 で通る
- [#572-3]（#538 で承認された決めた値）2 で止めるのは保つ——作業ツリーの中なのに git が index を読めなければ 2
- [#511-1] 置き場所の中の構造ファイルの綴り違い（`shared/QA.csv`・`spec/QA-dev.csv`・`spec/Spec_IR.json`）を決まりに反する（1）として断る（どの FS でも同じ答え）
- [#511-2]（範囲を広げた分）タグから写して重ねる `build-proposal.py` も、置き場所の中の `spec/QA-dev.csv` で 1（作業ツリーの重ね合わせと同じ答え）。
  `test-build-proposal.py` の試料とその変異が、新しい期待で緑・赤になる
- [#571-1] 大文字と小文字の試料を CI でも走る形にする（区別しない FS を用意する、または差し替えで再現する）。できないなら docstring の「守らない」に書く
- [#515-1] `references/versions.md` に移行の節——どう見つけるか（`merge-versions.py` の 1 の文言）・`git mv` の 2 段・ディスク上だけ古い綴りの場合
- [周-1] spec-loop の版を main より上に、3 種類の箇所（`marketplace.json`・`plugin.json`・5 本の `SKILL.md` の 2 行）で揃える
- [周-2] 壊れる変更（#511 の新しい 1）の移行の手順を原本（`versions.md`）に書く（CLAUDE.md の 0.x の決まり）

### 不変条件と経路

- **A（#569・#511）同じコミットなら、作業ツリーで重ねても、`git archive` の書き出しで重ねても、FS に依らず同じ答え（終了コードと出力）。**
  破りうる経路（`merge` の入口から数える）: (1) `docs` のフォルダ名 (2) 版のフォルダ名 (3) 版の直下の名前（置き場所・`removed.csv`）
  (4) 置き場所より深いフォルダ名 (5) 置き場所の中のファイル名 (6) 構造ファイル（`shared/qa.csv` など）の名前 (7) `removed.csv` の
  種類 `ファイル` の `対象`（重ねたパスと突き合わせる）(8) index に綴り違いの 2 つが在る形 (9) `git add` 前の改名（区別する FS では別の項目）。
  守り方: 各段の名前を `spelled` で index の綴りに寄せる（`walk` が段ごとに index の名前を引く）。構造ファイルは寄せた名前で `fold` を比べて断る。
- **B（#570）フックが相対で設定した `GIT_DIR`・`GIT_WORK_TREE`・`GIT_COMMON_DIR` が環境に在っても答えは無いときと同じ。相対の
  `GIT_INDEX_FILE` は作業ツリーの根からのパスとして読む（`docs` から見た場所を読まない）。** 経路: `merge-versions.py` が走らせる `git` の全部
  （`rev-parse --is-inside-work-tree`・`rev-parse --show-toplevel`・`ls-files`）。守り方: 1 つの口（`run_git`）から呼び、その口で場所の変数を外し、
  `GIT_INDEX_FILE` は `tracked` が絶対パスにしたものだけを渡す。
- **C（#572）作業ツリーの外（git が `docs` から見つけない）なら作業ツリーの綴りで読んで 0 系、中で index を読めなければ 2。**
  経路: `docs` の上の関係のない `.git`（壊れた `gitdir:`・中身の無いディレクトリ）・発見が止まる境界（`GIT_CEILING_DIRECTORIES` で代える）・
  壊れた index・git が無い。
- **D（#571）CI の Linux で、区別しない FS でだけ判別できる試料が走る。走らなかったら緑にならない。**
- **E（版・決まりの写し）** 版の 3 種類が揃う・本体の定数が `versions.md` と一致する（`test-merge-versions.py` の `check_reference`）。
- **F（使う側の退行なし）** `diff-versions.py`・`check-signoff.py`・`scaffold.py`・`build-proposal.py` のテストが緑（`check-all.py`）。

### 証明できるもの・できないもの

- 証明できる: A（macOS の区別しない FS で実走。区別する側は CI の Linux）・B・C（`GIT_CEILING_DIRECTORIES` で境界を代える）・E・F。
- **未証明**: 本物の FS の境界（マウントポイント）での #572-2——権限なしにマウントを作れない。`GIT_CEILING_DIRECTORIES` は git の発見を
  同じ形（「not a git repository」）で止める代わりで、PR コメントで人間のレビューに回す。dubious ownership も同じ（所有者の違うリポジトリを作れない）。
- **D は PR の CI でしか確かめられない**——手元の docker（OrbStack のカーネル）は ext4 の casefold をマウントできなかった（実測）。

### 生成物

- `SKILL.md` の測定値（設計ドキュメント §8.2 の生成ブロック）: spec-loop の `SKILL.md` は版の 2 行だけ触る。`skill-metrics.py --check` で鮮度を見る（`check-all.py` が回す）。
- 図の書き出し: 触らない（該当なし）。

### 必須要件の掛け算

受入基準を 2 つの関門（Verifier・`/code-review`）× 2 パスに渡す = 4 つの受け渡し（2 パス目が該当なしなら 2 つ）。狭いパスは 2 パス目で直した行があるときだけ。

## 未解決の判断・確認待ち

- #570 の「外すか絶対パスにするか」は**外す**で決めた（推奨。下の「既知の限界・決着済みの論点」）——Issue の受入基準が両方を許しているので仕様の穴ではない。
- #572 の git が走らないときの扱い——#538 の決めた値は「2 で止めるのは保つ」。git が無ければ `rev-parse` を走らせられないので、
  前の判定（上へ辿って `.git` が在れば 2・無ければ外）を残す（決めた値の範囲の中。仕様の穴ではない）。

## 関門の進捗（再開点）

- 実装: 済み（`merge-versions.py`・テスト・`plugins.yml`・`versions.md`・版 0.39.0）。手元（macOS・区別しない FS）で `test-merge-versions.py` は
  試料 94・変異 90 で緑。**陽性対照**: main の `merge-versions.py`（`eef9331`）に新しいテストを当てると、新しい試料 9 件が赤
  （壊れた／中身の無い `.git`・境界・相対の `GIT_DIR`・深い段・構造ファイルの作業ツリーの改名・QA.csv・QA-dev.csv・Spec_IR.json）。
  赤にならない新しい試料（壊れた index で 2・git が無い 2 件・相対の `GIT_INDEX_FILE`・一時の index）は前のコードでも守られていた形で、変異が守る。
- 割り目（手順 4）: 不在のため訊かず続けた。
- PR #660（実装のコミット `e86a8a7`）。
- 1 パス目: 起点（1 パス目の指摘対応の起点）`e86a8a7`。Verifier・`/code-review` に同時に渡した（結果は下に書く）。
- 中断: 利用上限で 1 度止まり、親が再開（2026-10-30）。再開時に worktree の状態（未コミット 3 件）を確かめて続けた。
- 実装中に変えた設計: #570 で `GIT_INDEX_FILE` を外す案は**やめた**——git は相対の `GIT_INDEX_FILE` を作業ツリーの根から解決する（実測。
  git 2.54。根の `idx` が壊れていれば `docs` から呼んでも失敗し、`docs/idx` が壊れていても根の `idx` を読んだ）ので、外すとフックの
  一時の index（コミットされる綴り）を捨てることになる。`GIT_DIR`・`GIT_WORK_TREE`・`GIT_COMMON_DIR` は外し、`GIT_INDEX_FILE` は根からの絶対パスにして渡す。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| #570 は変数を外すか絶対パスにするか | **場所の変数（`GIT_DIR`・`GIT_WORK_TREE`・`GIT_COMMON_DIR`）は外す。`GIT_INDEX_FILE` は作業ツリーの根からの絶対パスにして渡す** | `GIT_DIR` を絶対パスにしても `GIT_WORK_TREE` が無いと、git は cwd（`docs`）を作業ツリーの根と読み、index のパスがずれる。外せば git は `docs` から自分のリポジトリを見つける。`GIT_INDEX_FILE` は部分コミットの一時の index（コミットされる綴り）を指すので外さない。相対ならフックが走った根からのパス（git もそう解決する——実測）。`docs` の属さないリポジトリの index を指す形は docstring の「守らない」 |
| #572 で `rev-parse` が失敗した理由を読み分けるか | **読み分けない**（失敗は外） | git のメッセージは版と言語（`LANG`）で変わる。dubious ownership・壊れた `gitdir:` も外と読み、作業ツリーの綴りで読む——docstring の「守らない」に書く |
| #514 をこの周に入れるか | **外す** | 上の「まとめる範囲」 |
| #571 で区別しない FS をどう用意するか | CI で ext4 の casefold をループデバイスでマウントし、`TMPDIR` をそこへ向けて同じテストを回す。テストは印（環境変数）があるとき、区別しない FS でなければ赤にする | 差し替え（FS の振る舞いの偽物）は、偽物を試すことになる。本物の区別しない FS なら git の `core.ignorecase` も本物になる |

### 1 パス目の採否（`/code-review`。Verifier は下に足す）

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1-1 | 対応しない `repositoryformatversion` などで `rev-parse` が失敗すると外と読み 0（前は 2） | 示せる（レビューが実走） | 無し——不変条件 C は「外 ＝ git が `docs` から見つけない」で定義し、#538 の決めた値（外かは `rev-parse` で決める）どおり。失敗を読み分けないのは決着済み（下の表）で、この形もその一種 | 残課題（docstring の「守らない」の行が同じ種類を持つ） |
| CR1-2 | 存在しない `GIT_INDEX_FILE` で git は空の index と読み、照合が黙って外れて 0（無ければ 1） | 示せる（`i569-repro.sh`: no env rc=1・missing idx rc=0） | #570-2（相対の `GIT_INDEX_FILE` で答えが変わらない）・A | 直す（無いファイルを指していれば 2） |
| CR1-3 | index に深いフォルダの綴り違い 2 つ（`requirements/Sub/a.md`・`requirements/sub/b.md`）——作業ツリーは 1、`git archive` は 0 | 示せる（`i569-repro.sh`: worktree rc=1・archive rc=0） | A（経路 8 の深い段）・#569-2 | 直す（綴りごとに index の子だけを割り当てる） |
| CR1-4 | casefold の CI ステップが `test-build-proposal.py` の区別しない FS の試料を回さない | 示せない（CI で飛ばされることは見えるが、失敗ではない） | 無し（#571 は `merge-versions.py` の試料の Issue。#511-2 は手元で緑・赤を確かめた） | 残課題（周の途中の課題として親に提案） |
| CR1-5 | `check-signoff.py`・`scaffold.py` の `find_versions` が index を渡さず、版の名前を作業ツリーの綴りで読む | 示せない（レビューは読んだだけ） | 無し（#569 は `merge-versions.py` の照合の Issue） | 残課題（周の途中の課題として親に提案） |
| CR1-6 | `versions.md` の移行: ファイルの大文字小文字だけの改名は `git mv` 1 回で通る（2 段が要るのはフォルダ）・1 の文言は「置かない」で終わらない | 示せる（`i569-repro.sh`: file mv rc=0・dir mv rc=128・文言は「（…開けてしまう）」が続く） | #515-1 | 直す |
| CR1-7 | `GIT_WORK_TREE`・`GIT_COMMON_DIR` を設定する試料・変異が無い | 示せない（実装は外している。試験が無いだけ） | 無し | 残課題（計画の「証明できる」の B はこの 2 つについてはコードを読んだ範囲と書き直す） |
| CR1-8 | `spelled` が段ごとに O(N×M) | 示せない | 無し | 残課題 |
| CR1-9 | 同じ書き換えの変異 3 件が別々に走る | 示せない | 無し | 残課題 |
| CR1-10 | `prepare_git` の 2 段の改名が `rename()` を使わず 4 箇所に残る | 示せない | 無し | 残課題 |

## 手順 8

- この周の起票: 0 件（手順 8 で確定する）
