# Issue #1047 — dev-loop: 影響範囲とロールバック履歴を、不在の周のマージ判定に入れる

cruise（親 Issue #1075）の子として回す周。**不在の周**（出所: `/dev-loop:cruise 1075 --absent` の起動・2026-11-16）。AskUserQuestion は使わない。
spec-loop から来た Issue ではない。`作り直しの元:` の行も無い。`find-cycle.py 1047` は 5 本とも当たらず、新規の周。
依存先の #1043（PR #1083。`check-gates.py` を新設し dev-loop 2.0.0）は main にマージ済み——この周はその照合の `CHECKS` に判定を足す。

台帳の確かめた線（出所: cruise の確かめた線（台帳 `issue-1075`）。親の委譲文で受け取った）:
直す線 = `既定` / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた。**子はマージしない**——PR 側の CI まで）/
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。

直す線: `既定`（出所: cruise の確かめた線）。

重い検査は `run-serial.py` 越しに回す——`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.111.0/skills/cruise/scripts/run-serial.py -- <コマンド>`。関門にも渡す（並行の検査 1 本）。
この周は導入済みの dev-loop 1.111.0 で回る——この周が足す判定は、この周のマージにも cruise の後の周にも効かない（`plugin update` まで）。
**ただし親は main の `merge-pr.py --absent`（2.0.0 の照合）でこの PR をマージしうる**ので、下の関門の記録は main の `check-gates.py` の形で書き、PR の前に当てる。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-gates.py` — `CHECKS` に `check_risk` を足す（`--absent` だけ。宣言 `不在で止める範囲:` と既定ブランチの revert の履歴）。docstring の「何を照合するか」「守る」「守らない」
- `scripts/test-check-gates.py` — 試料（main の revert・squash に残った revert・範囲の宣言・ブランチの宣言）・ケース・変異（「守る」と 1 対 1）
- `scripts/test-merge-pr.py` — `merge-pr.py --absent` が範囲に当たる PR をマージせず 13 で止める end-to-end の試料と、居る周の対照
- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py` — docstring の 1 項だけ（`--absent` を渡し忘れると影響範囲は見ない）。1 パス目の CR4 で広げた——A8（docstring と食い違わない）
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「宣言の置き場所と書き方」に `不在で止める範囲:`、「マージ = 関門を通ればマージ」の止まる条件、「マージ前の判断 = 推奨で決めて起票」の「この線でも止まるもの」、新しい節「影響範囲で止める（#1047）」
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 4（13 のうち影響範囲の理由は記録の食い違いでなく、利用者に回すもの）・版の 2 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `docs/plugins/dev-loop-cruise.md` — 道具の表の `merge-pr.py` の行に影響範囲を足す
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない。変わらなければ触らない）
- `CLAUDE.md` — プロジェクト構成の `check-gates.py` の行に影響範囲
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（2.0.0 → 2.1.0）
- `.claude-plugin/marketplace.json` — 同じ版
- `docs/plans/issue-1047.md` — この計画

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py`——照合は `check-gates.py` が持ち、`merge-pr.py` は 0 でなければ 13 で止める（#1043 のまま）。docstring の 1 項のほかは変えない
- このリポジトリの `.claude/dev-loop.md` に `不在で止める範囲:` を足すこと——どの範囲を止めるかは利用者が決める（宣言を足すのは利用者。著者も自分で広げない）
- GitHub の Issue・ラベルからマージ後の欠陥を読むこと——照合はネットに出ない・取り直さない（下の「仕様の穴」）
- 影響範囲を差分の中身（関数・行）で決めること——Issue はファイルのパターンで判定すると言っている

依存の追加・更新: なし（標準ライブラリの `fnmatch` だけ）

## 周の大きさ（同じことを述べている箇所の数）

影響範囲の規範を述べる箇所: `check-gates.py` の docstring（判定の原本）・`absent-lines.md`（線との関係と宣言の書き方の原本）・cruise `SKILL.md` §4 の 4（13 の扱い）・
`docs/plugins/dev-loop-cruise.md` の 1 行・`CLAUDE.md` の 1 行——**5 箇所**。分けない理由: 判定の中身は docstring だけに置き、ほかは指すだけにする（列挙を写さない）。

## 決めたこと（Issue が周に委ねた範囲）

- 宣言の行の名前と形: `.claude/dev-loop.md` の `不在で止める範囲: <glob>`。1 行 1 パターン・何本でも・`/` で終われば配下。読み方は `マージの反映:` と同じ（コードブロックと HTML コメントの外・既定ブランチから）。
- 差分の取り方: 既定ブランチとの分岐点（`merge-base`）から head まで。取り込んだ main の変更を数えない。計画ファイルは数えない。
- 判定の場所: `check-gates.py` の `CHECKS`（Issue の提案どおり #1043 の照合）。止まる形は `merge-pr.py --absent` の 13 → cruise の親が `利用者の判断待ち:` で止める（#1043 のまま）。

## 仕様の穴（不在の線で推奨により決めた）

- **G1 ロールバック・マージ後の欠陥の記録をどこから読むか**（Issue の提案 3 の「記録の置き場所を決める」）。
  選択肢: (A) revert は既定ブランチの git の履歴（`This reverts commit <SHA>` の行）から機械で読み、revert していないマージ後の欠陥は利用者が `不在で止める範囲:` の行を足して止める（推奨）／
  (B) 別のファイル（例: `.claude/dev-loop-rollbacks.md`）に周が記録を足していく／(C) GitHub の Issue（ラベル）を照合のたびに読む。
  決めた値: **A**。推した理由: 履歴は周が書き足さなくても残り、改ざんに PR が要る。B は周が自分の記録を書くので「著者が自分で広げない」の外になる。C はネットに出て、照合が取り直しに依る（`check-gates.py` は取り直さない）。
  線と出所: `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線）。確認の Issue: 下の「確認の Issue」。

## デプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。マージは親がする。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 経路と守り方 |
| --- | --- | --- |
| A1 | 既定ブランチの宣言 `不在で止める範囲:` に当たるファイルを変えた PR を、不在の周はマージせず PR で止める（陽性対照） | `check-gates.py --absent` が 3（理由に `影響範囲:`）→ `merge-pr.py --absent` が 13 で `gh pr merge` を呼ばない。`test-check-gates.py`（R1）・`test-merge-pr.py`（end-to-end）。経路: cruise の親の `merge-pr.py --absent`・手で `check-gates.py --absent` を呼ぶ周（手順 7） |
| A2 | 当たらない差分は今までどおりマージまで進む | 範囲の宣言・revert の履歴がある main でも、当たらない差分は 0。既存の全ケース（`test-check-gates.py`・`test-merge-pr.py`）が同じ結果のまま。この周の計画をこのリポジトリの main に当てて 0（実データ） |
| A3 | 判定はスクリプトが行い、モデルの判断に依らない | 判定は `check_risk`（`CHECKS`）。止まった PR を親が記録の書き足しで通さない（cruise `SKILL.md` §4 の 4） |
| A4 | 既定ブランチで戻した（revert した）コミットが触ったファイルを変えた PR も、不在の周は止める | `rolled_back`。`test-check-gates.py`（R2） |
| A5 | 宣言は既定ブランチから読む——PR で足した・書き換えた範囲の宣言を効かせない。コードブロック・HTML コメントの中の行を読まない | `default_dev_loop_md`・`visible`。`test-check-gates.py`（Y2・M の中の a.txt） |
| A6 | 居る周（`--absent` でない）のマージを、影響範囲で止めない | `check_risk` の先頭。`test-check-gates.py`・`test-merge-pr.py` の居る周の対照 |
| A7 | 既定ブランチから辿れないコミットを戻した行（squash の本文に残った PR の途中の revert）を、戻した履歴に数えない | `rolled_back` の祖先の照合。`test-check-gates.py`（R3。合成）。このリポジトリの 5b2d1ab（本文に `This reverts commit 8bacadd…` を含む squash）は、引いた SHA が手元で解決しないので外れる——実データが示すのは「解決しない SHA を数えない」までで、祖先の照合は合成の R3 だけが判別する（1 パス目の CR5 で主張を弱めた） |
| A8 | 文書（`absent-lines.md`・cruise `SKILL.md`）が、範囲で止まった PR を「マージ前の判断」の推奨で進めない・記録の書き足しで通さないと書き、事実として docstring と食い違わない | 読んで照合。`check-skill-pointers.py`・`check-all.py` |
| A9 | 版を 3 種類（marketplace・plugin.json・SKILL.md 2 本）で揃え、生成ブロックが新しい | `check-plugin-versions.py`・`skill-metrics.py --check` |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に × 2 パス = 4 つの受け渡し（2 パス目が「該当なし」なら初回の 2 つ）。

未証明: (U1) 実際の cruise の親が 13 を受けて `利用者の判断待ち:` で止めること——親（モデル）の振る舞いで、この環境では走らせない。人間のレビューに回す。

生成物: `docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`skill-metrics.py --check` で鮮度を見る）。図の書き出しは触らない（drawio を変えない）。

## 未解決の判断・確認待ち

- G1 の確認の Issue（利用者が戻ってから）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1047-absent-merge-risk-gate`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1047`・
  起点 `a6f8d59`・base 参照 `origin/main`・base SHA `a6f8d5981c144e459d1138edb9fda810441cff64`
- 割り目（手順 4・6）: **割らない（cruise の周）**——利用者に訊かない（不在の周・cruise の子）
- 交絡: 実験なし（試料は一時の git リポジトリの合成と、このリポジトリの main への当て）
- 1 パス目: Verifier（sonnet・`dev-loop:dev-loop-verifier`）cf93f38 **反証 3 件**／`/code-review`（high）cf93f38 **指摘 7 件**。差し戻し: あり（直す 4 件——下の表）。
  1 パス目の指摘対応の起点: `cf93f38036a708e207117a060a77a231f801c2e5`（1 パス目の関門に渡した HEAD）

```dev-loop-gates
周の base: a6f8d5981c144e459d1138edb9fda810441cff64
関門: Verifier 1 cf93f38036a708e207117a060a77a231f801c2e5 反証=3
関門: /code-review 1 cf93f38036a708e207117a060a77a231f801c2e5 指摘=7
受入基準: A1 満たす
受入基準: A2 満たす
受入基準: A3 満たす
受入基準: A4 満たす
受入基準: A5 満たす
受入基準: A6 満たす
受入基準: A7 満たす
受入基準: A8 満たす
受入基準: A9 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

- 影響範囲はファイルの名前だけで決める。宣言の無い共有モジュールは止めない（宣言するのは利用者）。
- revert の履歴は期間で区切らない（Issue の「過去に」）。止めたくなければ居る周でマージする。
- 本文が `This reverts commit <既定ブランチの線の SHA>` を引用しただけの revert でないコミットも、戻した履歴と読む（止まる側に倒れる）。
- `git revert` を使わずに手で戻した変更は数えない。
- merge commit で入れるリポジトリでは、PR の中で自分のコミットを revert した行も数える（止まる側に倒れる）。

### 1 パス目の採否の表（直す線 = 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1・CR1 merge commit で入れた PR の中のコミットを main で revert しても数えない（first-parent で代用） | 示せる——両関門が一時リポジトリで `rolled_back` = `{}` を実走 | A4 | 直す（祖先の照合に変える。試料 R4） |
| V2・CR3 書き損じた宣言（行末の注釈・`/` 始まり・`./`・末尾の `/` の無いディレクトリ）が黙って何にも当たらない | 示せる——両関門が実走で `check_risk` = `[]` | A1 | 直す（空白・`/`・`./` で始まるものは読めない宣言として止める。glob の無いパターンは配下にも当てる。試料 H2・H3） |
| CR2 周の差分が既定ブランチの `不在で止める範囲:` を消しても止まらない（文書の「消す・緩める PR は利用者のレビューを通す」が強制されていない） | 示せる——実走で `check_risk` = `[]` | A3・A8 | 直す（既定ブランチの行を外す差分を止める。試料 R5） |
| CR4 `merge-pr.py` の docstring「`--absent` を渡し忘れると止まる側に倒れる」が影響範囲では偽 | 示せる——`check_risk` は `--absent` が無ければ `[]`（読んで照合） | A8 | 直す（docstring に 1 項。範囲を広げた） |
| CR5 A7 の実データ（5b2d1ab）は祖先／first-parent の照合を判別していない | 示せる（SHA が解決しない） | 無し（計画の主張） | 残課題——計画の A7 の主張を弱めた（計画は成果物ではない） |
| CR6 `rolled_back` が毎回全コミットの本文を読む（効率） | 示せない（遅さの実測なし） | 無し | 残課題 |
| V3・CR7 変異「差分を周の base から取る」「宣言を素の行で読む」を殺す試料が、注釈の理由で赤になったかを判別しない | 示せる（試料の読み） | 無し | 残課題（試料の穴） |

## 手順 8（経験の還元）

（周の終わりに書く）

- この周の起票: 1 件（仕様の穴 G1 の確認の Issue。番号は起票の後に書く）
