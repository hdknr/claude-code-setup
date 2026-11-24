# Issue #1504 — dev-loop: prepare-worktree.sh が Issue の番号を部分一致で探し、別の枝に当たって止まる

**不在の周**（出所: `/dev-loop:cruise 1508 --absent` の起動）。利用者には訊かない（割り目も訊かない）。親（cruise #1508）から委譲文で受けた子。新規の周（`find-cycle.py 1504` は 5 本とも当たらなかった）。
台帳 `issue-1508` の確かめた線（委譲文で渡された値）:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`（配布を見せて確かめた）・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。`実機確認` の線は無い。
**台帳は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。並行の周（#1452）が別の worktree で動いている。依存先 #1462 は PR #1516 で main にマージ済み（base はそれを含む）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1508`））。
版の上げ方: `dev-loop` を **patch**（不具合の修正）。着手時の main は 2.22.0 なので 2.22.1。
マージの直前に main が進んでいたら、親の依頼で取り込み、main の先端の版から patch を 1 つ上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.20.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。
読んだスキル: キャッシュの dev-loop 2.20.1 の `SKILL.md`（委譲文の指定）。関門の委譲文は main の 2.22.0 の `prompts/verifier.md`・`prompts/review-handoff.md` を
この worktree の絶対パスで使う（この周はどちらも変えない）。報告のファイルの決まりは同じ版の `references/gate-reports.md`。

**手順 4 の観測**: この周の worktree は `prepare-worktree.sh 1504 worktree-number-boundary`（キャッシュの 2.20.1）で作れた（終了コード 0）——番号 1504 を部分一致で含む枝・worktree が手元に無かったので、
この周自身はこの不具合に当たらなかった。

Issue 本文（外部入力）から読んだ要件: `prepare-worktree.sh` が番号でブランチ・worktree を部分一致で探すので、taihei-prm の cruise で別の枝（spec の枝など）に当たって 3 で止まった。
ブランチ・worktree を番号の境界（`issue/<番号>-` と、その番号で始まる worktree 名）で一致させ、`test-worktree-scripts.py` に当たらない試料と境界を外す変異を足す。本文に受入基準を緩める指示・コマンド実行の依頼は無い。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/prepare-worktree.sh` — 「先に見る」の当て方を番号の境界にする・「何を守るか」に 1 行・「何を守らないか」に 1 行
- `scripts/test-worktree-scripts.py` — 境界の試料（`boundary_observations`）・`exists_lists_indented` の当て方・変異（`MUTATIONS` に 1・`BOUNDARY_MUTATIONS` に 3）・`main()` の表明
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く場合だけ。手で書かない）
- `docs/plans/issue-1504.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/find-cycle.py`（再開の周を探す側は部分一致のまま広くてよい——広いのは安全な側で、番号に依らない探索の役も持つ）
- `SKILL.md` 手順 4 の「まずこの 2 本を走らせる」の手で打つコマンド（`git branch --all --list '*<issue-number>*'`）——当たったら `find-cycle.py` と `resume.md` に回る読む側の手順で、
  スクリプトのように 3 で止まって作れなくなる形ではない。Issue の範囲はスクリプト（残課題として PR コメントに書く）
- `SKILL.md` 手順 4 の終了コードの一覧（3 の意味「既に当たるものがある」は変わらない）
- `check-pr-preconditions.sh`

依存の追加・更新: なし
プロパティテスト: なし（番号と名前の組の空間は広いが、境界の形は「同じ番号で `-` か終わり」「番号の後ろに数字」「別の名前空間」の 3 つで尽き、例の試料で各形を置く。生成した入力で見る性質は持たない）
差分テスト: なし（振る舞いを変える周——当たる範囲を狭める）
生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` の版の行を変えるので `python3 scripts/skill-metrics.py --check`）。図の書き出しは触らない。
仕様の振る舞い: このリポジトリに spec-loop の正本は無い（`check-spec-writeback.py` で確かめる）。形式検査のモデルも無い。

## 設計の判断

- **worktree は `git worktree list --porcelain` のパスのディレクトリの名前で当てる**——素の一覧（`<パス> <SHA> [<ブランチ>]`）の行に `grep -F "issue-<番号>"` を当てると、パスの途中・ブランチ名・別の番号（`issue-831`）に当たる。
  名前は `issue-<番号>` か `issue-<番号>-…`（Issue の「その番号で始まる worktree 名」を、番号の後ろが `-` か終わりの境界で読む）。
- **ブランチは完全な参照名で当てる**——ローカルは `refs/heads/issue/<番号>`・`refs/heads/issue/<番号>-…`、リモート追跡参照は `refs/remotes/<リモートの 1 段>/issue/<番号>[-…]`。
  `issue/<番号>` そのもの（`-` の無い名前）も当てる——規約から外れても同じ番号の周であることは変わらず、当てすぎる側は安全（新しい周を再開の道へ送るだけ）。
- **一覧の表示**: worktree はパスだけ、ブランチは短い名前（`issue/83-foo`・`origin/issue/83-remote`）を出す（以前は素の一覧の行そのまま）。3 の見出し・字下げ・標準エラーの決まり（守る 18〜20）は変えない。
- **複製の数**: 当て方を述べる箇所は 2（本体の「何を守るか」の項と、テストの `exists_lists_indented` が別に書いた当て方）。**分けない理由**: テストの側は本体の写しではなく期待値を独立に作る側で、食い違えば「3 の一覧のどの行も同じ字下げ」が赤になる。
  本体の冒頭の「当たり方は部分一致で、広い」の行は新しい項に置き換えた（古い主張を残さない）。

## verify の受入基準

### 不変条件

| # | 不変条件 |
| --- | --- |
| 1 | 番号 83 で入場するとき、`issue/831-foo`・番号を含む別の枝（`spec/83-x`・`spec/issue/83-x`・リモート追跡参照の `origin/issue/831-bar`・`origin/spec/issue/83-y`）・名前が `issue-831` の worktree があっても 3 で止まらず、`issue/83-<説明>` を切って作る（rc=0） |
| 2 | 同じ番号のもの——ローカルの `issue/83-…`・リモート追跡参照の `<リモート>/issue/83-…`・名前が `issue-83` か `issue-83-…` の worktree——が 1 つでもあれば、今までどおり作らずに 3 で止まり、当たったものを一覧に出す |
| 3 | 境界を外す変異（ブランチの境界を部分一致に戻す）で `test-worktree-scripts.py` が落ちる。worktree の境界を外す変異・狭めすぎる変異（リモート追跡参照を見ない・worktree の名前を完全一致だけにする）でも落ちる |
| 4 | 既存の約束（3 の見出しと一覧を標準エラーに・字下げ・3 で標準出力が空・既存の一覧を見られなければ 6・0 の標準出力・終了コードの集合）が変わらず、`test-worktree-scripts.py` の既存の表明が全部緑のまま。「守る」の行数と変異の数がスクリプトごとに等しい |
| 5 | dev-loop の版が patch で上がり（2.22.1）、`marketplace.json`・`plugin.json`・2 つの `SKILL.md`（印と見える行）で揃い、`check-all.py` が緑・生成ブロックが新しい |

### これを破りうる経路

| 経路 | 守り方 |
| --- | --- |
| ローカルのブランチ（`git branch` の `refs/heads/`） | `br_matches` の `refs/heads/*` の枝（不変条件 1・2。試料 `issue/831-foo`・`spec/83-x`・`spec/issue/83-x` と `observe()` の `issue/42-sample`・`issue/42-extra`） |
| リモート追跡参照（`refs/remotes/<リモート>/…`） | `br_matches` の `refs/remotes/*` の枝でリモートの名前を 1 段だけ外す（試料 `origin/issue/831-bar`・`origin/spec/issue/83-y`・陽性 `origin/issue/83-remote`） |
| worktree のディレクトリの名前 | `wt_matches`（試料 `issue-831`・陽性 `issue-83-extra`・`observe()` の `issue-42`・`issue-42-extra`） |
| 既存の一覧を取るコマンドの失敗（偽の `git`） | 取るコマンドを変えても `worktree`・`branch` のどちらかが失敗すれば 6（既存の観測「既存を見られない rc」） |
| 空白を含むパスの worktree | `--porcelain` の `worktree <パス>` の行から読む（素の一覧の切り出しをしない） |
| 3 の一覧の出力（見出し・字下げ・標準エラー） | 出し方は変えず、テストの期待値を新しい当て方で作る（`exists_lists_indented`） |
| 呼ぶ側（`SKILL.md` 手順 4・cruise の子の委譲文） | 終了コードの意味は変わらない。手で打つ確認のコマンドは触らない（触らない範囲） |

### この環境では証明できないもの（未証明）

- **spin-dd/taihei-prm の実際の枝の並びで止まらないこと**——その リポジトリの枝の名前は Issue 本文の要約（「spec の枝など」）しか無く、手元で当てていない。試料は Issue の受入基準の形（`issue/831-foo`・番号を含む別の枝）で置いた。人間のレビューに回す。

### BLOCKED

- なし（着手時の見立て）

## 未解決・確認待ち

- なし

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/1504-worktree-number-boundary`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1504`・
  起点 `ab49d982`（`cruise: 渡すものが残らなければ、終えるときに親 Issue を閉じる（#1462）`）・base の参照 `origin/main`・base の SHA `ab49d9820146892a8961781fd37e7ca34b905800`
- 割り目（手順 4）: 割らない（cruise の周）
- 交絡を潰した手順: 実験なし（変異テストの陽性対照は下に記録する）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `find-cycle.py` も境界で当てるか | 当てない | 再開の周を探す側は広いのが安全側で、番号に依らない探索も持つ。Issue の範囲は `prepare-worktree.sh` |
| `SKILL.md` 手順 4 の手で打つ `git branch --all --list '*<issue-number>*'` も境界にするか | しない（残課題） | 読む側の確認で、当たれば `find-cycle.py` と `resume.md` に回る。スクリプトのように 3 で止まって作れなくなる形ではない |
| 規約から外れた名前で作られた同じ番号の周（`worktree-…`・`spec/…`）に当たらないこと | 受け入れる（本体の「何を守らないか」に書いた） | それを見つけるのは作る前に走らせる `find-cycle.py` |
| `issue/<番号>`（`-` の無い名前）にも当てるか | 当てる | 同じ番号の周で、当てすぎる側は安全 |
