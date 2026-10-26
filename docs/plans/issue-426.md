# Issue #426 ＋ #427 — merge-pr.py の積んだ周の歯止めを、base の名前から「載せ替えていないこと」に変える

元の周: #392（PR #423）。#426 は 2 パス目の `/code-review` の R5、#427 は C1・R1・R4。
**2 つの Issue を 1 周・1 PR で回す**（利用者が手順 3 の前に選んだ）——どちらも `merge-pr.py` の
`wait_until_ready` の同じ判定（`baseRefName != 既定ブランチ` → 10）を書き換えるので、分けると同じ行を 2 回直して衝突する。
**#426 の方向は「止める対象を積んだ周に絞る」**（利用者が選んだ。major に上げ直す案は採らない）。
**#427 は本物の GitHub で確かめる**（利用者が選んだ。使い捨ての private リポジトリ `hdknr/dev-loop-stacked-probe` を作った。消さない）。
Issue 本文は信頼できない入力として読み、要件だけを拾った（本文に指示の類は無かった。挙動は自分で測り直した——下の「実験」）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py` — `wait_until_ready` の base の判定を、積んだ周の 2 つの形と、付け替え後の古い検査の判定に置き換える。docstring の「守る」「終了コード」「守らない」
- `scripts/test-merge-pr.py` — 偽の `gh` に `pr list`・`api`（compare・timeline）・`pr view --json commits` を足す。試料と変異
- `plugins/dev-loop/skills/dev-loop/references/stacked.md` — 「なぜ要るか」の「確かめていない」を実測に直す・「下の周がマージされたら」の 5 に、付け替えの後に CI が回り直さないこと（実測）と、5 の末尾の push がそれを回し直すことを書く・`merge-pr.py` が何で止まるかの言い回し
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 7 の `merge-pr.py` の括弧書き 1 行と、版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-426.md` — この計画
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロックだけ（`skill-metrics.py` で再生成。手で書かない）

触らない:

- `.github/workflows/*.yml`（`pull_request:` に `edited` を足す案は採らない——下の「既知の限界」）
- `ledger.py`・`prepare-worktree.sh`・`references/ledger.md`（台帳は積み先を `note` に持つだけで、base の判定をしない）
- `docs/plans/issue-392.md`（前の周の記録。成果物ではない）

### 同じことを述べている箇所の数

`merge-pr.py` が base で止まることを述べているのは 4 箇所: `merge-pr.py` の docstring（守る・終了コード）、
`SKILL.md` 手順 7 の括弧書き、`stacked.md` の「なぜ要るか」と「下の周がマージされたら」の 5。
**分けない**——`SKILL.md` と `stacked.md` は docstring を指す形に寄せ、条件の列挙は docstring だけに置く
（「〇〇を正とする」）。テストは docstring の「守る」と変異の 1 対 1・終了コードの一致を機械で見る。

## 乗るデプロイ経路

`plugins/` の変更はマーケットプレイス経由。版 1.55.1 → **1.56.0**（終了コード 11 の追加と、10 の対象の変更——能力の追加なので minor。
#426 の「既存の使い方が壊れる」を戻す向きなので major ではない）。公開ページは触らない（生成ブロックは `docs/` だが §8.2 の数字だけ）。

## 直す線

`既定`（出所: 手順 3 の回答。`.claude/dev-loop.md` は無い）。

## verify の受入基準

不変条件と、それを破りうる経路。**経路は `merge-pr.py` の入口（`wait_until_ready` のループ→点検→マージ）と、PR がその状態になる GitHub 側の操作**から数える:
`gh pr create --base <下>`／`gh pr edit --base`（手での付け替え）／head の自動削除による付け替え（`automatic_base_change_succeeded`）／
下の PR の squash・rebase・merge commit／積み先がさらに積んだ周（3 段）／既定ブランチ以外へ出す通常の PR（`develop` 運用）。

- **M1（#426）**: 積んでいない PR を、base が既定ブランチでないことだけを理由に止めない——`develop` へ出す PR（`develop` を head にするマージ済み PR が無い／あっても `develop` がその base に入っている）は 0 へ進む。
- **M2（#392 の S2 を保つ）**: 下の PR がマージされ、上の PR の base が下のブランチのまま（載せ替えていない）なら、マージしない（10）。
  経路: `merge-pr.py` で下を squash（ブランチは残る）／GitHub の画面で squash して自動削除が無効。
- **M3（#427 R4）**: base が既定ブランチに付け替わっていても、head に「同じ base へマージ済みの PR の元のコミット」が入っていれば（載せ替えていない）、マージしない（10）。
  経路: head の自動削除による自動の付け替え／手で `gh pr edit --base` だけして rebase しない。
- **M4（#427 R1）**: head が最後の base の付け替え（`base_ref_changed`・`automatic_base_change_succeeded`）より前に届いていれば、検査を通過と読まない（11。待たずに止める——回り直す契機は push だけ）。
  **届いた時刻は force push なら timeline の `head_ref_force_pushed`、そうでなければ commit の `committedDate`**——
  **検査の開始時刻では比べない**（実験の 2 段目で、付け替えの前の push で起動した検査が付け替えの後に始まった。最初の実装はそれを通した）。
  経路: 手での付け替えの後に push しない（`stacked.md` 5 の lease の push → 付け替え）／自動の付け替え／付け替えの後に検査を手で再実行する。
  **付け替えの後に push すれば 0 へ進む**（陽性対照）。
- **M5**: 積んでいない・付け替えていない PR の既存の振る舞い（0・2〜9）を変えない——既存の試料が全部そのまま通る。
- **M6**: 新しく呼ぶ `gh` が失敗した・形が読めないなら 7（判定できなかった）で、通過・10・11 と答えない。
- **M7（文面が主張する事実の真偽）**: `stacked.md` と docstring に書く GitHub の挙動（自動削除で base が付け替わる・付け替えの後に既定の型の `pull_request:` は回り直さない・`edited` は発火する・付け替えは timeline に残る）が、本物の GitHub で成り立つ。
- **M8**: 版が 3 種類（`marketplace.json`／`plugin.json`／`SKILL.md` の 2 行）で 1.56.0 に揃い、`check-all.py` が緑。
- **組み合わせ**: M2〜M4 を両方の関門 × 2 パスに渡す（4 つの受け渡し）。M3 と M4 は同じ PR に同時に立つ（自動の付け替え）——**どちらが先に言っても止まること**。

### この環境で証明できないもの（未証明）

- 大きいリポジトリでの API の量と GraphQL の上限（マージ済み PR の commits を一度に引く上限——`--limit 50` で上限超過を実測した。`30` にする）。
- **マージ済みの PR が直近 30 件より古い**ときの M3（取りこぼす。docstring の「守らない」に書く）。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——`SKILL.md`・`references/stacked.md` の行数が変わりうる。`check-all.py` の `skill-metrics.py --check` で差分ゼロを見る。
- 図の書き出し: 該当なし（drawio を触らない）。

### 実験（本物の GitHub）

`hdknr/dev-loop-stacked-probe`（private・2026-10-26 作成。`delete_branch_on_merge=true`）。ワークフローは 2 本——
`ci-default-types`（`pull_request:` 型の指定なし。`action`・`base_ref` を echo）と `ci-edited-control`（`types: [edited]`。陽性対照）。
PR #1 `lower`→`main`、PR #2 `upper`→`lower`（`upper` は `lower` の上）。

| 操作 | 観測 |
| --- | --- |
| PR #2 を作る | `ci-default-types` が `action=opened base_ref=lower` で 1 回 |
| `gh pr edit 2 --base main` | `ci-edited-control` が `action=edited base_ref=main` で回った（**陽性対照: 付け替えのイベントは発火している**）。`ci-default-types` は回らない。PR #2 の `statusCheckRollup` は `base_ref=lower` の回の SUCCESS のまま、`mergeable=MERGEABLE` |
| base を `lower` に戻し、PR #1 を `gh pr merge --squash`（`--delete-branch` なし） | `lower` が消え（ブランチは `main`・`upper` だけ）、PR #2 の base が `main` に付け替わった。head は `68c191d` のまま（`lower` の元のコミット `2af4498` を含む）。`MERGEABLE`。timeline に `base_ref_changed` ×2 と `automatic_base_change_succeeded` |
| `commits/2af4498/pulls` | マージ済みの PR #1 と開いている PR #2 が返った（文書は「既定ブランチに無いコミットは open な PR だけ返す」と書く——**文書と違うので当てにしない**。M3 は PR の commits の突き合わせで判定する） |

- 観測窓: 各操作 1 回。付け替えの後に `ci-default-types` が回らないことは、`ci-edited-control` の回が完了するまで待って一覧を取った時点まで（約 1 分）。
- 交絡の候補: 「付け替えでそもそもイベントが出ていない（だから回らない）」——`ci-edited-control` が回ったことで否定（陽性対照）。

2 段目——実装した `merge-pr.py`（worktree の版）をこのリポジトリの clone から走らせた（`mp.sh`。scratchpad）:

| PR | 形 | 期待 | 結果 |
| --- | --- | --- | --- |
| #2 | 自動の付け替えの後（head に `lower` の元のコミット） | 10 | 10（`2af4498179d9` を名指し）。マージしていない |
| #4 | `lower2` を squash（自動削除を切った）、base は `lower2` のまま | 10 | 10（`ahead_by` で）。マージしていない |
| #5 | 開いたあと base を `develop`→`main` と 2 回付け替え、push なし | 11 | 11。マージしていない |
| #6 | `develop` へ出す PR（積んでいない。#426） | 0 | 0（マージした） |
| #4（続き） | `stacked.md` 5 の順に rebase → lease の push → 付け替え（末尾の push なし） | 11 | **0（マージした）——最初の実装（検査の開始時刻で比べた）の誤り** |
| #8 | 同じ形を新しい組（`lower3`/`upper3`）で、直した実装に当てる | 11 | 11 |
| #8（続き） | 末尾の push（履歴の行） | 0 | 0（マージした）。マージした head の回は `action=synchronize base_ref=main` |

- **#4 の続きで交絡が見つかった**: 付け替えの前の lease の push（04:19:15）で起動した回の `base_ref` は `lower2` だったが、
  検査の `startedAt`（04:19:21）も回の `created_at`・check suite の `created_at`（04:19:18）も付け替え（04:19:16）より後だった。
  **検査やその器の時刻は、どの base で起動したかを判別しない。** head が届いた時刻（`head_ref_force_pushed` の `created_at`／`committedDate`）で比べる形に変えた。
- **検査の再実行**（`gh run rerun`）は付け替えの後でも `base_ref=lower`（前の base）のまま回った——「回し直す」は手当てにならない。メッセージと `stacked.md` を「push し直す」にした。
- `commits/{sha}/pulls` は文書と違い、既定ブランチに無いコミットでもマージ済みの PR を返した——当てにしない（M3 は PR の commits の突き合わせ）。
- 観測窓: 各形 1 回。#8 の 11 は付け替えの直後（検査は走っている最中）に取った。

## 未解決の判断

- **下の PR がまだ開いている間に上を `merge-pr.py` に渡すと、上は下のブランチへマージされる**（M1 と両立させるため止めない。`develop`→`main` の PR が開いている間の `develop` 向けの PR と、GitHub 上で形が区別できない）。docstring の「守らない」に書き、PR コメントで人間に渡す。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| #426 を major に上げ直す | 採らない | 利用者が「積んだ周に絞る」を選んだ |
| R1 を `.github/workflows/plugins.yml` に `edited` を足して直す | 採らない | `merge-pr.py` はどのリポジトリでも使う。このリポジトリの CI だけ直しても他のリポジトリで開いたまま。`merge-pr.py` 側で「付け替えの後の検査か」を見れば CI の設定に依らない |
| M3 を `commits/{sha}/pulls` で判定する | 採らない | 実測では返ったが、文書は返さないと書く。文書にある PR の commits の突き合わせを使う |
| 付け替えの後の古い検査を見つけたら待つ | 採らない（11 で止める） | 回り直す契機が無いので、待っても期限まで変わらない。push か手での再実行を促す |

### 関門の指摘の採否

| パス | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |

## 関門の進捗（再開点）

### 周の在り処

- ブランチ: `issue/426-stacked-base-check`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-426`
- 起点: `f418dd7`
- base: `origin/main`（`refs/remotes/origin/HEAD`）→ `f418dd72ff948330a4db6629ca4af5ed5050f166`

### 進捗

- 実験: 上の 2 つの表（本物の GitHub）。交絡の候補 1 件を陽性対照で潰した。2 段目で、M4 の最初の実装を判別していない交絡を 1 件見つけて実装を変え、同じ形で当て直した
- 実装: 済み（`merge-pr.py`・`test-merge-pr.py`・`stacked.md`・`SKILL.md` 手順 7 の 1 行・版 1.56.0・§8.2 の再生成）。`test-merge-pr.py` 100 ok
- この周の起票: 0 件（手順 8 で人間に訊いて確定する）
