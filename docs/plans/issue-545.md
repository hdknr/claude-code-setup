# Issue #545 — test-worktree-scripts.py の変異の件数の写しが 20 件のまま（CLAUDE.md・コメント。#502 CR2-3）

**不在の周である**——出所: `/dev-loop:cruise 474 --absent` の再開（2026-10-29）。この周は cruise の親から、worktree の絶対パスで作業する
サブエージェントとして委ねられた。**この周では `EnterWorktree` を呼んでいない**（`prepare-worktree.sh` で作り、`cd <worktree> && …` で作業した）。
`AskUserQuestion` は使わない。

使った線（出所: cruise の確かめた線（台帳 `issue-474`）——利用者の確認（起動時・2026-10-27T09:07:27Z）＋利用者の確認（再開時・2026-10-28T07:24:46Z）
＋利用者の確認（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた）。親の委譲文で受け取った）:

- `仕様の穴 = 推奨で決めて起票`
- 直す線: **既定**
- `マージ = 関門を通ればマージ`（**マージは親が行う**——この周は PR・CI・関門・手順 8 の記録まで）
- `周の途中の課題 = 台帳に足して直す`（台帳には親が足す。この周は台帳を書かず、見つけた課題を親への報告に挙げる）
- 加えて、利用者の指示（2026-10-29。親の委譲文で受け取った）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、要確認の Issue（#565・#561 の形）にする

スキルの版: 読み込んだのはキャッシュの 1.63.6（`SKILL.md` 1842 行）。リポジトリの main は 1.63.8。
**この周はプラグインの中を触らない**（`CLAUDE.md` と `scripts/` だけ）ので、版は上げない。

## 変更範囲

触る:

- `CLAUDE.md` — `test-worktree-scripts.py` の変異の件数の写し 2 箇所（`scripts/` の一覧の行と「`SKILL.md` は条件つきの節を `references/` に出す」の節）を、件数を持たず出力を指す形にする
- `scripts/test-worktree-scripts.py` — 件数の写しを持つコメント 2 箇所（`observe()` の回数のコメント・`check-pr-preconditions.sh` の「守る」の見出しのコメント）を、件数を持たない形にする。コードは変えない
- `docs/plans/issue-545.md` — この計画

触らない:

- `docs/plans/` のほかの計画ファイルの件数——周の記録で、書いた時点の値である
- `scripts/test-worktree-scripts.py` のコード・`MUTATIONS`・`QUOTE_MUTATIONS`・試料——同じファイルを触る兄弟の周（#558・#559・#576・#577）の範囲
- 件数の写しを持ち込ませない歯止め（新しい検査）——Issue の受入基準にない。下の「既知の限界」
- プラグインの版（3 種類）・description——プラグインの中を触らない

## 複製の数

「`test-worktree-scripts.py` の変異の数」を述べる箇所（`docs/plans/` を除く）: `CLAUDE.md` 2（172 行・661 行）、テストのコメント 2（198 行の「変異 23」「24 回」・493 行の「守る 4 行」）、テストの出力 1（`2 本の「守る」N 行に対して変異が M 件`——数えて出す。写しではない）。
**この周で写し 4 を 0 にし、出力の 1 だけを残す。** 分けない理由: 4 つとも同じ「写しが古くなる」型で、直し方も同じ（数を消して出力を指す）。

## デプロイ経路

`CLAUDE.md`・`scripts/`・`docs/plans/` だけ。プラグインの中は変わらないので配布は起きない。`docs/plans/` は Pages の再ビルドに乗る（`CLAUDE.md` は `docs/` の外）。
**マージは親（cruise）が行う——この周はしない。**

## 受入基準（不変条件 × 経路）

不変条件:

- **I1 古い写しが無い**——`CLAUDE.md` と `scripts/test-worktree-scripts.py` のコメントに、`test-worktree-scripts.py` の変異の数（「変異 20 件」「変異 23」「24 回」）と `check-pr-preconditions.sh` の「守る」の数（「守る 4 行」）の写しが残っていない
- **I2 数は出力が言う**——写しを消した箇所は、数をテストの出力（`2 本の「守る」N 行に対して変異が M 件`）に任せる形で書かれ、その出力が実際に今の数（守る 23 行・変異 23 件）を言う
- **I3 意味を変えない**——消したのは数だけで、各箇所が述べていた事柄（変異テストを含む／`observe()` の回数が変異の数に比例するので足場を複製する理由／`check-pr-preconditions.sh` の守る）は残る
- **I4 既存を壊さない**——テストのコードは変えない。`python3 scripts/test-worktree-scripts.py` が緑、`python3 scripts/check-all.py` が緑、PR 側の CI も緑

経路（不変条件を述べる／破りうる入口）:

| 入口 | I1 | I2 | I3 | I4 |
| --- | --- | --- | --- | --- |
| `CLAUDE.md` の `scripts/` の一覧の `test-worktree-scripts.py` の行 | ○ | ○ | ○ | |
| `CLAUDE.md` の「`SKILL.md` は条件つきの節を `references/` に出す」の節の「変異 20 件で押さえている」 | ○ | ○ | ○ | |
| `scripts/test-worktree-scripts.py` の `_templates` の上のコメント（`observe()` の回数） | ○ | | ○ | ○ |
| `scripts/test-worktree-scripts.py` の `MUTATIONS` の中の `check-pr-preconditions.sh` の見出しのコメント | ○ | | ○ | ○ |
| テストの出力（`main()` の 1 対 1 の数え） | | ○ | | ○ |
| リポジトリのほかの場所（`docs/`（plans を除く）・`plugins/`・README）に同じ写しが無いか | ○ | | | |
| `check-all.py`（`check-duplicate-counts.py`・`check-mutation-claims.py` を含む）・PR の CI | | | | ○ |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目で 4 つの受け渡し（2 パス目が「該当なし」なら 2 つ）。

### 証明できるもの／できないもの

- I1〜I4 は、`grep`・テストの実行・`check-all.py`・CI で証明できる。未証明・BLOCKED は無い。

### 生成物

- 該当なし——`SKILL.md` を触らないので `skill-metrics.py` の生成ブロックは動かない。drawio も触らない。

## 未解決の判断・確認待ち

- 無し（仕様の穴は無い。Issue の受入基準（案）が「出力が言う形にできるなら、そちら」と決めている）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/545-mutation-count-copies`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-545`、
  起点コミット `4abb280`、base の参照 `origin/main`（refs/remotes/origin/HEAD・取り直した）、base の SHA `4abb280dda86eac24190df155e9196f6c0fbb730`
- 手順 4 の割り目: 不在のため訊かず続けた
- 交絡: 実験なし（写しを消すだけ。出力が今の数を言うことはテストの実行で見る）
- 実装: 済み。`python3 scripts/test-worktree-scripts.py` 緑（出力 `2 本の「守る」23 行に対して変異が 23 件`）。`check-all.py` は 1 回目に `check-mutation-claims.py`（`test-worktree-scripts.py:384` の主張が 300 秒で打ち切り——他の周と同時に走った負荷。#449 と同じ形）で落ちた。出力ファイルを他の周と同じ scratchpad の名前に置いたため、別の周の結果（`issue-574.md` の件数の行）が混ざった。名前を分けて回し直し 54/54 緑

## 既知の限界・決着済みの論点

- 件数の写しを新たに持ち込ませない歯止め（`CLAUDE.md` に「変異 N 件」と書いたら落ちる検査）は置かない——理由: Issue の受入基準にない。`check-duplicate-counts.py` は同じファイルの中で同じ語句に違う数が付く形しか見ない
- `docs/plans/` の件数は直さない——理由: 周の記録で、書いた時点の値である
- 件数を「今の数（23）にそろえる」ではなく「消して出力を指す」を選んだ——理由: Issue の受入基準（案）の後半が、できるならそちらと決めている。兄弟の周（#558・#559・#576・#577）が同じテストに変異を足すと、そろえた数はまた古くなる

## 手順 8（経験の還元）

- この周の起票: 0 件（起票の承認は不在のため訊いていない。台帳に足す候補は台帳を書く親に報告し、この周では起票していない）
