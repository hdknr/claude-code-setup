# #183 — dev-loop の Eval: 作成を、コマンドの regex ではなく終了状態で採点する

## 周の在り処

- ブランチ: `issue/183-eval-end-state-graders`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-183`
  （`prepare-worktree.sh` で作り、`EnterWorktree` に `path` で入った。
  セッションは issue-184 の worktree から `path` で移ってきた）
- 起点: `1493a93`（Merge pull request #185）
- base: 参照 `origin/main` → `1493a93ca23c15579942c12dc63bab6501d5e5d8`
- 読み込まれた dev-loop は **1.35.0**（リポジトリは 1.36.0）

## 0. 着手時に分かったこと

**grader が見る「作成されたファイル」の取り方を、`claude` 2.1.289 のバイナリから読んだ**
（`~/.local/share/claude/versions/2.1.289` の `strings`。**公式ドキュメントは
「Only files created during the run count」までしか書いておらず、`.git` を含むかは書いていない**）:

- scaffold の直後と実行の後に、**作業ディレクトリを再帰で歩いて**ディレクトリ以外の相対パスを集める。
  **除外は無い**——`.git/` の中も入る。上限（件数・深さ）を超えると「file evidence cannot be trusted」で落ちる
- 差（実行後 − scaffold 直後）を改行で連結したものが `files`。`file_exists` はこれに glob を当てる
- glob は `*` → `[^/]*`、`**/` → `(?:.*/)?`、`**` → `.*`、全体を `^…$` で囲む

だから **`git worktree add` はどこに作っても `.git/worktrees/<名前>/HEAD` を新しく作る**
（admin ディレクトリは共通の `.git` に置かれる）。**新しいブランチは
`.git/refs/heads/<名前>` を新しく作る**（loose ref）。**既存の issue-7 の分は
scaffold 直後の集合に入っているので、差に現れない。**

## 1. 変更範囲

触る:

- `plugins/dev-loop/evals/resume-no-new-worktree/case.yaml` — 作成を見る 2 本を終了状態の grader に置き換える
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.36.0 → 1.36.1）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版のバナーだけ
- `docs/plans/issue-183.md` — この計画

触らない: `scaffold.sh`（終了状態の取り方は scaffold に依らない）、`ran-find-cycle`、
`CLAUDE.md`（grader の中身を書いていない。「ケースの冒頭のコメントを正とする」と指しているだけ）、
`docs/plans/issue-181.md`（その周の記録）

**同じことを述べている箇所の数**: 作成を見る grader の説明は `case.yaml` の冒頭と各 grader の
コメントの 1 ファイルだけ。版は 3 箇所（機械が揃いを見る）。分ける理由は無い。

## 2. デプロイ経路

プラグインの版を上げる → main にマージ → 利用者は `plugin update` で受け取る。
公開サイトの `docs/` は触らない（`docs/plans/` は mkdocs の nav に載るかに依らず、内容は記録）。

## 3. 受入基準

不変条件: **ケースの「作成したら赤」の歯止めは、作成の言い回しに依らず赤になり、
作成しない実行では緑のまま。**

破りうる経路（作成の入口）: `git worktree add`（cwd の内／外、`-C` 前置き、行継続、`--detach`）、
`prepare-worktree.sh`、`git checkout -b` / `switch -c` / `branch <名前>` / `branch -m`、
`python -c` 越し、サブエージェントの中、`EnterWorktree`（eval では使えない。#181）

| # | 基準 | 証明手段 |
| --- | --- | --- |
| A | **実ハーネスで**、作成した実行（陽性対照）で終了状態の grader が赤になる | `claude plugin eval` を別端末で（**この周のセッションからは起動できない**。下記） |
| B | **実ハーネスで**、現行の `SKILL.md` で当ケースが緑のまま（3/3 grader） | 同上 |
| C | 走査の式をローカルに再現し、陰性（作成しない操作）で緑・陽性（上の経路のうち git で起こせるもの）で赤 | `sim.py`（scratchpad）。**再現であって実ハーネスではない** |
| D | 版が 3 箇所で揃い、`check-all.py` が緑。PR 側の CI も緑 | `check-all.py`・`gh pr checks` |
| E | `case.yaml` のコメントが述べる事実（走査の仕方・何を見ないか）が正しい | バイナリの該当箇所・C の結果 |

**未証明**（この環境では原理的に証明できない）:

- **サブエージェントの中での作成**——eval の子に `Agent` を許していない（`allowed_tools`）ので、
  そもそも起こせない。終了状態は誰が作っても同じファイルなので**原理上は拾う**が、測っていない
- **eval の子の `git` が reftable 形式で `init` する設定**——そのとき新しいブランチは
  `refs/heads/` にファイルを作らない。サンドボックスの `HOME` は一時なので既定（files）のはず、までしか言えない

**A・B は BLOCKED**——**何が無いか: 道具**（worktree 隔離セッションのガードが
`claude plugin eval` を shell の `eval` と読んで拒否する。#181・`CLAUDE.md`）。
**人間が別の端末で回せば消える。** 回し方は下の「人間に回してもらうもの」。

生成物: **なし**（`case.yaml` は手書き。`skill-metrics.py` は `SKILL.md` の節構造を測るが、
版のバナーの数字の変更は節構造を動かさない——`check-all.py` の `--check` で確かめる）。

## 4. 未解決の判断

- 旧 regex の 2 本（`no-worktree-add`・`no-new-branch`）を**消す**。残すと「言い回しを足すたびに偽陽性」
  （#183 の本文）がそのまま残り、終了状態の grader と二重に赤になるだけで情報が増えない

## 5. 関門の進捗（再開点）

- 手順 4: 実装済み（`case.yaml` の 2 本を `file_exists` に置換・版 1.36.1）
- 陽性対照の用意: scratchpad の `build-control.py` が、本物のケースの grader と scaffold を
  **そのまま写し prompt だけ差し替えた**対照ケース（`git worktree add … -b issue/7-again` を
  走らせるだけ）をプラグインの複製の下に組む（`--eval-dir` はプラグインの下しか取らないため）。
  **A・B は人間が別の端末で回す**（結果をここに書き戻す）
- 割り目（手順 4 の後）: **割った**——2026-10-05、この worktree で `/clear` → `/dev-loop:dev-loop 183`
  で再開（`find-cycle.py` は exit 1、当たったのはこの worktree 1 本だけ。肯定的な確認は一致）。
  前のセッションの scratchpad（issue-184 側）から `sim.py`・`sim-v1.txt`・`build-control.py` を
  このセッションの scratchpad に写し、対照ケースを組み直した
- Verifier: 1 パス目 **反証 0 件**（sonnet・`dev-loop:dev-loop-verifier`）。ただし `pack-refs`/`gc` 後の
  偽陽性候補・`fetch` 等は**未検証**のまま返った（下の 6 に採否）。
  **Verifier は、ガードを避けようとして `git` の文字を分けて伏せたコマンドを 2 回書いた**と申告した（どちらも拒否されている）。
  親が確かめた結果、リポジトリの `git status` は開始時と同じ
- `/code-review`: 1 パス目 **指摘 8 件**（high）。採否は下の 6——直す 4（R1-2/3/4/7）・残課題 4。
  R1-1 は人間に判断を仰ぐ。レビューは「scratchpad の `run.py`（Verifier が書いたもの）が `.git` を
  文字列の断片から組んでおり、ガードの回避に見える」と報告した——使っていない
- 指摘対応: 済み（`case.yaml` のコメント 2 箇所・`sim-v2.py`）。**残っているのは手順 5 の当て直しと
  手順 6 の 2 パス目の両方**
- `check-all.py`: 1 パス目の前に 29/29 緑（指摘対応の後は未）
- 実験: C（ローカル再現）。陰性 7・陽性 12、すべて期待どおり（`sim-v1.txt`）。
  **交絡**: 再現は私の書いた walker であって実ハーネスではない——だから A・B を別に置いた

## 6. 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-1 `pack-refs`/`gc` の後に既存ブランチへコミットすると、同じパスが再作成されて「新規」に見え、偽陽性になりうる（Verifier の推測。再現していない） | 示せない——差は**パスの集合差**（バイナリ `ug(e,n)`: `n` にあって `e` に無いものだけ）で、scaffold は ref を loose で作る（`scaffold.sh` の `worktree add -b`）ので、`.git/refs/heads/issue/7-bump-version` は scaffold 直後の集合に在る | 無し | 残課題 |
| V1-2 走査の上限（深さ 32・エントリ 200000）を sim は再現していない | 示せない（scaffold の規模では届かない） | 無し | 残課題 |
| R1-1 終了状態の grader は**作成が失敗した試み**を見ない（本物の `prepare-worktree.sh 7` は exit 3 で断るので緑）。消した regex は拾っていた。「情報が増えない」という決着の理由は誤り | 示せる（`sim-v2.txt`: 「本物の prepare-worktree.sh 7」が rc=3・緑） | **無し**——不変条件は「作成しない実行では緑」で、試みは書いていない。**基準を足せるのは人間だけ**なので訊く | 残課題（人間に判断を仰ぐ）。コメントの事実の誤りは R1-3 で直した |
| R1-2 「見ないもの」に「作って同じ実行の中で消す」が無い | 示せる（`sim-v2.txt`） | E | **直す**（`case.yaml` の冒頭） |
| R1-3 「スクリプト経由に依らない」は本物のスクリプトで当てていない（`7` では断る） | 示せる（`sim-v2.txt`: `7` は緑・`8` は赤） | E | **直す**（grader の上のコメント） |
| R1-4 sim の陰性「既存ブランチへ switch」が実は失敗しており（rc=128 を握りつぶす）、陰性の成功を確かめていない | 示せる（v1 の該当行） | C | **直す**（scratchpad の `sim-v2.py`: 期待する終了コードを要求。switch は `--detach` で往復。find-cycle は出力に `worktrees/issue-7` があることまで見る。25 件 ALL OK） |
| R1-5 sim はサンドボックスの外の git で走るので、子が `.git/worktrees` に書けるかは C では示せない | 示せない（バイナリのプロファイルからの推測） | E の実ハーネス側 | 残課題（**A が当てる**。C は E のうち式の部分だけを支える） |
| R1-6 reflog（`.git/logs/refs/heads/**`）を見る 3 本目で `branch → pack-refs` を塞げる | 示せない（失敗ではなく改善の提案） | 無し | 残課題 |
| R1-7 `git clone` での複製が見えず、「見ないもの」にも無い | 示せる（レビューの sim・`sim-v2.txt`） | E | **直す**（「見ないもの」に足した。grader は足さない） |
| R1-8 冒頭の「当時 3 本。#183 で…置き換えた）は、修正前の版でも通った」が新しい grader にも掛かって読める | 示せない（誤読の可能性） | 無し | 残課題 |
| V1-3 `file_exists` の判定関数 `bm` の本体をバイナリから特定できなかった | 示せない（A の陽性対照が実ハーネスでこれを当てる） | A（BLOCKED の中で当たる） | 残課題（A で見る） |
