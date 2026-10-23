# Issue #340 — check-signoff の暫定反映の照合で、案内のテストと merge と食い違う重ね方を直す（#336・#338 のまとめ）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/merge-versions.py` — `Whole.apply` の `removed.csv` の拒否（2 度消す・ファイルとしては消せない・同じ版で置きつつ消す・前の版までに無い）を関数 `check_removed` に出す。**振る舞いは変えない**（メッセージの文言も同じ）
- `plugins/spec-loop/scripts/check-signoff.py` — `provisional_rows` の拒否を `check_removed` で行う（B）。`removed.csv` の読み込みを 1 か所にまとめ、`resolve` で読んだものを `provisional_rows` に渡す（C）。docstring の終了コード 3 の案内を「両方」に揃える（A の文言の原本との食い違い）
- `scripts/test-check-signoff.py` — A・B の試料・変異・`merge` との突き合わせ
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（patch: 0.17.0 → 0.17.1）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 同上（版の 2 行だけ）
- `CLAUDE.md` — `check-signoff.py` の説明（拒否も `merge-versions.py` の関数で、の一言。該当すれば）
- `docs/plans/issue-340.md` — この計画

触らない:

- `merge-versions.py` の拒否の決まりそのもの（`references/versions.md`）
- `removed.csv` の種類 `ファイル`・`機能` の行の照合（共有の範囲の比較は今のまま）
- `build-proposal.py`（照合の 3 をそのまま返すだけ）

### 同じことを述べている箇所の数

- 終了コード 3 の案内「両方を取り直す」: 本体の出力・本体の docstring（**いまは「要求確定」だけで食い違っている**）・`references/signoff-tags.md`・`proposal/SKILL.md` —— 4 箇所。文書側 2 箇所は既に「両方」。
- `removed.csv` の拒否: 原本 `references/versions.md`、実装は `merge-versions.py` の 1 箇所に寄せる（今は `check-signoff.py` に「置きつつ消す」だけの写しがある）。
- 分けない理由: Issue のとおり、3 つとも `check-signoff.py` の同じ関数とそのテストの同じ所を触る。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` の公開ページは触らない（`docs/plans/` は mkdocs の nav 外だがサイトには載る——main への push で Pages）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | 終了コード 3 の案内が「要求確定と予算の合意の両方のサインオフを取り直す」で、テストがそれを見る。文言を要求確定だけに戻す変異で赤 | 本体の出力文字列・docstring | 試料の期待文字列＋変異（実際に当てる） |
| B1 | 前の版までに無い Q&A を `removed.csv` で消す配置で、照合は 2 | `provisional_rows` | `merge-versions.py` の `check_removed` |
| B2 | 同じ Q&A を同じ `removed.csv` で 2 度消す配置で、照合は 2 | 同上 | 同上 |
| B3 | 同じ版で置きつつ消す配置は今までどおり 2 | 同上 | 同上（写しを消す） |
| B4 | 拒否の判定に写しを作らない（`check-signoff.py` に拒否の条件式が無い） | 本体のソース | 目視＋`grep` |
| B5 | 陽性対照: 正しい配置（前の版の行を消す・後の版で置き換える・暫定が残る）は 0 か 3 のまま | 既存の試料 | 既存の試料が緑 |
| B6 | B1・B2 の配置を `merge` も実際に拒否する（試料が `merge` の拒否を表している） | テストの試料 | `merge(docs)` の problems を突き合わせる |
| C1 | `removed.csv` は 1 つのタグの時点・1 つのパスにつき 1 回だけ読む（`provisional_rows` は読まない） | `resolve`・`provisional_rows` | `resolve` で読んだものを渡す |
| C2 | 振る舞いは変えない | 既存の全試料・`test-merge-versions.py`・`test-scaffold.py`・`test-diff-versions.py` | `check-all.py` |
| V | 版が 3 種類で揃い、歯止めが全部緑 | bump 漏れ | `python3 scripts/check-all.py` |

| D | **（2026-10-23 人間の決定で追加。1 パス目の R1/V1 を受けて）** `CLAUDE.md` と `provisional_rows` の docstring が述べる「2 にする配置」の範囲が、実装の範囲（**Q&A の行**の 3 配置）と一致する。種類 `ファイル` の行・v1 の `removed.csv` は 2 にしないことを書く | `CLAUDE.md`・docstring | 文を実装の範囲に合わせる（実装は広げない） |

組み合わせ: A × B（拒否で 2 のときは 3 の案内を出さない——2 が先）。B × C（拒否に要る行番号を、まとめた読み込みが落とさない）。
C2 × merge-versions の利用者（`scaffold.py`・`diff-versions.py`・`check-signoff.py`）——`Whole.apply` の振る舞い・文言が変わらないことは各テストが見る。

**この環境では証明できないもの（未証明）**: なし（すべてローカルの git 試料で当てられる）。

生成物: 図・`SKILL.md` の測定値（dev-loop のみ）に関係しない。**生成物なし**。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/340-signoff-provisional-removals`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-340`・起点 `4187a08`・base の参照 `origin/main`（SHA `4187a081088ab5c3037efd7e8d2b2968cb34d5d8`）
- 実装: `7dae3bc` で完了。`python3 scripts/check-all.py` 44/44 緑（失敗 0 / 飛ばし 0）。`test-check-signoff.py` 試料 55・変異 43
- 関門 1 パス目（2026-10-22〜23）: **Verifier**（`dev-loop:dev-loop-verifier`・`sonnet`）**反証 2 件**（V1・V2）・
  **`/code-review`**（high）**指摘 10 件**（R1〜R10）。採否は下の表。直すのは R2・R3（=V2）・R9 の 3 件、R1（=V1）は人間の決定で文を絞る（受入基準 D を追加）
- 1 パス目の指摘対応: R2（`CLAUDE.md`・docstring を Q&A の範囲に）・R3（変異を `pop(target, None)` まで戻す形に。陽性対照で 3・0 を再現し traceback 無し）・
  R9（docstring の終了コード 3 を見る検査と、要求確定だけに戻すと捕まる確かめ）。`test-check-signoff.py` 試料 55・変異 43 緑
- 1 パス目の指摘対応のコミット: `64d90d6`。0 行判定: `git diff f78d61e -- ':(top)' ':(top,exclude)docs/plans/issue-340.md'` が 3 ファイル（CLAUDE.md・check-signoff.py・test-check-signoff.py）→ **2 パス目を回す**
- `check-all.py`: 指摘対応のあと 43/44 緑・`check-plan-scope.py` だけ赤（計画の変更範囲で 1 行に 3 パターンを書いていた）→ 1 行 1 パターンに直して単体で緑。**全体の当て直しは 2 パス目の前にもう一度回す**
- 割り目 2（手順 6）: AskUserQuestion で訊き、**「ここで割る」が選ばれた**（2026-10-23）
- **残り（再開したらここから）**: ① 手順 5 の Verifier 当て直し（2 パス目）と ② `/code-review` 2 パス目の**両方**。base は `4187a08…`（周の base のまま）。
  2 パス目で直した行があれば、その起点 SHA を指摘対応の前にここへ書き、狭いパスを当てる
- 1 パス目の指摘対応の起点の SHA: `f78d61e`（1 パス目の関門に渡した時点の HEAD。2 パス目の要否の 0 行判定に使う）
- 関門 2 パス目（2026-10-23）: **Verifier**（`dev-loop:dev-loop-verifier`・`sonnet`）**反証 0 件**（R3・R9 の直しを変異で当てて一致。軽微: 例外の列挙に `機能` の行が無い）・
  **`/code-review`**（high）**指摘 8 件**（S1〜S8）。採否は下の表。直すのは S2・S3・S5（いずれも D の文の範囲）
- **2 パス目の指摘対応の起点の SHA（狭いパスの起点）: `88e6fff`**（指摘対応に入る前に記録）
- 2 パス目の指摘対応のコミット: `d912943`（S2・S3・S5。文だけ）
- **狭いパス**（`git diff 88e6fff`・`dev-loop:dev-loop-verifier`・`sonnet`。変異は Verifier が設計）: **反証 1 件**（F1）。新しい文の主張を試料 13 件で実測し、F1 以外は一致。
  素通りした変異: なし（文の修正なので変異ではなく試料の実測。陽性対照は `ok/ok` が 0、Q&A の拒否する配置が要求確定側で 2）。
  F1 は直さない（狭いパスの指摘は人間が決める）——**示せて D に触れるので、PR コメントで「満たしていない受入基準」として名指しする**
- `check-all.py`: HEAD `865bbca` で 44/44 緑 → `origin/main`（`24390e5`）を取り込み（`575a90b`、衝突なし）→ 44/44 緑
- PR #347（2026-10-23）: PR 側の CI `check` pass・`build` pass（`deploy` は skipping）・`MERGEABLE`。レビュー記録は PR コメント。**マージは人間の承認待ち**
- PR #347 マージ（2026-10-23T03:06:55Z、`4f2646d`）。#340 クローズ
- `main` の CI（`4f2646d`）: `Check plugin catalog`・`Deploy docs to GitHub Pages` とも成功
- 手順 8: **焼き戻す学びなし**（人間の決定 2026-10-23）。
  `CLAUDE.md` の取り込み手順に「main 側の変更がこの周の不変条件を破る経路を増やしていないか読む」を足す案を
  ブランチ `issue/340-merge-lesson` で書き、関門の 1 パス目（Verifier 反証 0・`/code-review` 指摘 7）に当てた。
  `/code-review` が前提の反証を示した——**#339 の `scripts/test-build-proposal.py` の試料「内部の表の違反でも比較を作る」が
  要求確定のタグの側で `D-009` を消しており、`D-` の絞りが無ければ赤になる**（`git show f712197:scripts/test-build-proposal.py` の 226-231 行）。
  つまり取り込み手順の既存の段（`check-all.py` を回す）で捕まる欠陥で、「テストでは捕まらない組み合わせだった」は偽。
  **この周では絞りを足してから `check-all.py` を回したので、テストより先に読んで気づいた**——テストが捕まえられなかったのではない。
  既存の手順で足りるので、新しい段は入れない
- 焼き戻しの Verifier（`dev-loop:dev-loop-verifier`・sonnet）は、worktree 隔離のガードに拒否されたあと、コマンド名を `"gi"+"t"` と分けてガードを避けた
  （本物のリポジトリに当てたのは `git archive` だけで、書き込みは scratchpad の一時リポジトリ。作業ツリー・stash・設定に変化なし——自分で確かめた）
- この周の起票: 4 件（#348 R1/V1・#349 R6/S1・#350 R7・#351 R10。マージの前に AskUserQuestion で人間が承認 2026-10-23）
- F1（狭いパス）: 人間の決定で**この PR で 1 語直す**（`CLAUDE.md`・docstring を「v2 以降の `removed.csv` の形式の違反は…」に）。関門は通さず人間レビューで見る
- **`origin/main`（`f712197`、#339 を含む）の取り込み**（2026-10-23）: spec-loop が 0.18.0 に進んでいて `check-version-bump.py` が赤 → 取り込んで **0.18.1** に上げた。
  衝突は版の 7 ファイル（main 側を取って上げた）・`merge-versions.py`（main の内側のループは `check_removed` と同じ中身——呼び出しを残し、`present` は main の「共有＋内部」）・`check-signoff.py`・`test-check-signoff.py`。
  **#339 の内部の層の Q&A（`D-`）と、この周の拒否が重なると、要求確定のタグの `removed.csv` で `D-` を消す正しい配置が「前の版までに無い」で 2 になる**（C2 を破る——#339 の時点では `pop(target, None)` で黙って通っていた）。
  → `provisional_rows` が重ねに渡す行から `D-` を除いた（`removed_shared_rows` と同じ絞り）。試料「内部の Q&A を消しても暫定を数える」（3。`merge` との突き合わせにも入れた）と変異「内部の Q&A を消した行も重ねる」を足した。`CLAUDE.md`・docstring に「`D-` は除く」を書いた。
  **この修正は関門を通していない**（人間レビューで見る。PR コメントに名指し）
- 反証・差し戻し: なし
- 交絡: 実験は変異テストのみ。新しい試料の陽性対照は、拒否の結果を見ない変異（`if problems:` → `if False:`）で旧い挙動（2 以外）が再現することで取っている
- 割り目（手順 4）: AskUserQuestion で訊き、**「ここで割る」が選ばれた**（2026-10-22）。再開は手順 5 から

## 既知の限界・決着済みの論点

- **種類 `ファイル` の行・v1 の `removed.csv` は、`merge` が拒否しても照合は 2 にしない**——決着: 採らない（範囲外。人間の決定 2026-10-23）。
  理由: 照合はファイルの存在を版ごとに追っていない。文を Q&A の範囲に絞り（受入基準 D）、広げる実装は残課題にする。

### 1 パス目の指摘の採否（Verifier V・`/code-review` R）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1/V1 `ファイル` の行（`ファイル,shared/qa.csv`・無いファイル・2 度）と v1 の `removed.csv` を照合が 2 にしない | 示せる（/code-review が試料で 3 と 0 を実測。merge は拒否） | 無し（B は Q&A の 3 配置） | 残課題（人間の決定。D で文を絞る） |
| R2 `CLAUDE.md` の「merge が拒否する配置は 2」が範囲を絞らずに書かれ偽 | 示せる（R1 の実測） | D（人間が追加） | 直す |
| R3/V2 変異「merge が拒否する配置を見ない」2 本は `whole.pop(target)` の KeyError で死ぬ（旧い挙動 3・0 を再現しない） | 示せる（/code-review が traceback・exit 1 を実測） | B1・B2（拒否を外す変異で赤——旧い挙動を表していない） | 直す（`pop(target, None)` まで含めて戻す 1 本の変異にする） |
| R4 `present` に今の版の行を含めて渡している（`check_removed` の docstring と違う・分岐の順に依る） | 示せない（今は等価。並べ替えたら、の仮定） | 無し | 残課題 |
| R5 終了コード 2 の一覧と proposal の SKILL.md に配置の拒否が無い | 示せない（誤読の仮定） | 無し | 残課題 |
| R6 既存の試料「removed.csv だけ違う」の予算側は merge が拒否する配置 | 示せる（merge が「置きつつ消している」） | 無し（既存の試料。C2 は変わらない） | 残課題 |
| R7 変異ごとに全試料を作り直す（約 10 分） | 示せる（実行時間） | 無し | 残課題 |
| R8 試料「暫定の行が残ると両方を取り直す」は既存の試料と同じ手順 | 示せる | 無し | 残課題 |
| R9 docstring の終了コード 3 の「両方」を見るテストが無い | 示せる（docstring を戻しても緑——試料も変異も出力しか見ない） | A（経路に docstring を挙げた） | 直す |
| R10 拒否のメッセージにパスが 2 度出る | 示せる | 無し | 残課題 |

### 2 パス目の指摘の採否（`/code-review` S。Verifier は反証 0 件）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| S1 `provisional_rows` に要求確定側の `removed` を渡す行に専用の変異が無い（予算側に入れ替えても R6 の試料でしか捕まらない） | 示せる（/code-review が入れ替えて実測。今は R6 の試料が捕まえる） | 無し（実装は正しい。テストの強さ） | 残課題 |
| S2 `CLAUDE.md` の「`ファイル` の行と v1 は `merge` が拒否しても 2 にしない」が広すぎる——`ファイル` の行の**形式**の違反（理由が空など）は `read_removed_at` で 2 になる | 示せる（`read_removed_at` が `read_removed` の problems で `Unjudged`。check-signoff.py:149-160） | D | 直す（「配置」に絞る） |
| S3 docstring の「`ファイル` の行と v1 は見ない」が、形式の検査と `shared/` の比較で読まれていることと食い違って読める | 示せる（同上） | D | 直す（この関数が見ないこと・形式は `read_removed_at` が見ることを書く） |
| S4 計画ファイルの R1 の決着の理由が 4 形のうち 2 形しか覆わない | 計画ファイルは関門の検査対象外（手順 6） | 無し | 残課題（決着の理由の見直しは人間が決める。PR コメントに名指し） |
| S5 `CLAUDE.md` が、拒否で 2 になるのは**要求確定のタグの時点**だけだと書いていない（予算側の拒否する配置は 1 か 3） | 示せる（`provisional_rows` を呼ぶのは要求確定のタグだけ。check-signoff.py:334） | D | 直す |
| S6 `whole.pop(target)` が別ファイルの `check_removed` の保証に依る（緩めると KeyError で 1） | 示せない（将来の仮定） | 無し | 残課題 |
| S7 Q&A だけに絞る `row[1] == REMOVED_QA` を守る変異・試料が無い | 示せない（今の実装は正しい。テストの強さ） | 無し | 残課題 |
| S8 `merge_not_refusing` に陰性対照が無い・呼ぶたびにモジュールを読み直す | 示せない（期待のメッセージは今どれも空でない） | 無し | 残課題 |

### 狭いパスの指摘の採否（Verifier F）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| F1 `CLAUDE.md` と docstring の「`removed.csv` の形式の違反は種類によらず 2」は v1 の `removed.csv` に当てはまらない（v1 は読まないので形式の違反でも 0） | 示せる（Verifier が v1 に見出し違反・理由が空を置いて両タグとも 0 を実測。`removed_scope` は v2 から: check-signoff.py:122-123） | D（文の範囲が実装と完全には一致しない。「v1 は 2 にしない」の直後なので v2 以降と読めば成り立つ曖昧さ） | 人間が決める → この PR で直す（2026-10-23） |
