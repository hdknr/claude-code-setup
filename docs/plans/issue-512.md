# Issue #512 — build-proposal.py: 一時ディレクトリの外を消さない・リンクの古い出力を消さずに名指し・読めない印と symlink の印を書き換えない

`plugins/spec-loop/scripts/build-proposal.py` を触る 3 組の課題（#512 の本文・追記・追記 2）を **1 周・1 PR** で扱う
（利用者の方針・2026-10-30: 同じファイルを触る課題は 1 件・1 周にまとめる。親から伝達）。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-10-30）。台帳 `issue-474` の確かめた線:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））。
加えて利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、`要確認` の Issue を立てる
（書き方は dev-loop の `references/absent-lines.md` の「確認の Issue の書き方」）。
マージは親がする（この周は PR・CI の確認・関門 2 パスと狭いパス・手順 8 の件数の行まで）。台帳は書かない（親が書く）。
周の途中で見つかった課題は、ファイルごとに 1 件の起票案（チェックリスト）にまとめて親に報告する（親が起票する）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/build-proposal.py` — `drop_internal`・`remove_owned`・`owned_names`／`manifest_names`・`main` の事前の確かめ・docstring
- `scripts/test-build-proposal.py` — 試料・変異・docstring
- `plugins/spec-loop/references/tree.md` — 「生成物の置き場所」と移行の節（0.x の振る舞いの変更）
- `plugins/spec-loop/README.md` — 同じ振る舞いを書いていれば
- `plugins/spec-loop/skills/proposal/SKILL.md` — 2 で止まったときの手当てを書いていれば
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（5 本）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-512.md` — この計画

触らない:

- `plugins/spec-loop/scripts/merge-versions.py` の `exact`（Issue の「案」はここを直すと言うが、呼ぶのは `build-proposal.py` の `drop_internal` だけで、
  並行する #569 の周（PR #660）が `merge-versions.py` を触る。`drop_internal` の側で途中のリンクを辿らないようにする）
- `schedule-to-gantt.py`（#626 で済み）

### 同じことを述べている箇所の数

- 「前の出力の消し方（印・リンク）」: 本体の docstring 1・`remove_owned` の docstring 1・テストの docstring 1・`references/tree.md` 1（＋README・proposal の SKILL.md にあれば各 1）。
  分けない——docstring は単体で読める必要があり、tree.md は利用者が最初に読む場所。tree.md は「消さずに名指しして 2」までを書き、細部は docstring を指す。
- 「読めない印」: 本体の docstring 1・`owned_names`／`manifest_names`／`leftover_lines` の docstring 3・tree.md 1・テスト 1 = 6 箇所。

## 乗るデプロイ経路

プラグイン `spec-loop` の中身——main へのマージでプラグインの新しい版が配られ、サイト（`docs/plans/` を含む）が再ビルドされる。マージは親（cruise）が決める。

## 周の在り処

- ブランチ: `issue/512-build-proposal-symlinks-manifest`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-512`（`prepare-worktree.sh` で作った。cruise の子なので `EnterWorktree` は使わず `cd <worktree> && …`）
- 起点: `0b58732`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`、取り直した）→ `0b58732751d577596891d3766f63c119be046700`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。受入基準はこの節の表だけである。

### Issue のチェックリストから写したもの

- **A（本文）**: `drop_internal` は、タグの `docs/v<n>/spec`（など途中の名前）がシンボリックリンクでも、一時ディレクトリの外の `qa-dev.csv` を消さない。`removed.csv` の書き換えも外に書かない
- **B（追記）**: リンクになった古い出力（印が名指しする名前）を消して「消した」と言い、先の古い中身を残すことをやめる——#626 に揃えるかを決めて直す
- **C（追記 2・P2-3）**: 印が UTF-8 で読めないとき、印を黙って書き換えて 0 で終わらない（推奨: 書き換えず 2）
- **D（追記 2・P2-4）**: 印が辿れない symlink のとき、git のリポジトリで 0 で終わって印を symlink の先（出力の場所の外）に書かない（推奨: 書かずに 2）
- **E（追記 2・P2-6）**: `same_entry` の親の比較を消す変異が素通りしない（消すか、届く試料を足す）

### 不変条件

- **I1（A）**: `drop_internal` は、版の根から対象までの途中の名前がシンボリックリンクなら、その先を消さず・書き換えない（外したことにしない——重ね合わせがリンクの置き場所を断る）。
  対象そのもの（`spec/qa-dev.csv`）がリンクなら、消すのは一時ディレクトリの中のリンクだけ（先は残る）。リンクの無い普通の場合は今までどおり外す。
- **I2（A）**: 一時ディレクトリの外のファイル（リンク先の `qa-dev.csv`・`removed.csv`）は、どの経路でも変わらない。
- **I3（B）**: 印が名指しする名前が symlink で、先を辿れる（先が在る）なら、リンクも先も消さず、リンクと先のパスを名指しし（「消した」と言わない）、印を残して 2。
  先を辿れない（権限）なら同じく名指しして 2。壊れたリンク（先が無い）は今までどおり消してよい（残る古い中身が無い）。
- **I4（C・D）**: 出力の場所の印が普通のファイルとして読めない（UTF-8 で読めない・ディレクトリ・symlink——辿れても辿れなくても）なら、印を書き換えず・印の先に書かず、
  名指しして 2。消すものも無い（読めない印は消さない——今までどおり）。作れない経路（1・3 など）は今までどおりその終了コードで止まり、作れたときだけ書く前に 2 にする。
- **I5（E）**: `same_entry` は親の違う 2 つを同じ項目と読まない——直接呼ぶ試料が守り、親の比較を消す変異で赤。
- **I6**: 既存の試料と変異は変わらず緑。文書（本体の docstring・tree.md・README・SKILL.md）が新しい振る舞いと食い違わず、0.x の振る舞いの変更の移行を `references/tree.md` に書く。
  版は spec-loop の 3 種類（marketplace.json・plugin.json・SKILL.md 5 本 × 2 行）で揃い、main より上。`check-all.py` が緑。

### 経路（不変条件を破りうる入口）

本体の入口は CLI（`main`）だけ（テストは関数を直接も呼ぶ）。その中で:

- 一時ディレクトリへの写し（`copy_docs`）→ `drop_internal` → `merge`。途中のリンクの置き場所: `docs/v<n>/spec`（リンク）・`docs/v<n>/spec/qa-dev.csv`（リンク）・`docs/v<n>/removed.csv`（リンク——既に `is_symlink` で外していた）
- 前の出力を消す `remove_owned` の 3 つの入口: `--out` の親・`--out` に渡したディレクトリ・`write_outputs` の書きかけの片付け
- 印を読む: `owned_names`（消す側）・`manifest_names`（名指しする側）・`main` の事前の確かめ・`write_outputs`（印を書く）
- 印の形: 無い・普通のファイル（読める・UTF-8 で読めない・権限で読めない）・ディレクトリ・symlink（辿れる先・壊れた・辿れない先）
- 名指し: `leftover_lines`（`same_entry`）・`left_lines`
- 文書: 本体の docstring・tree.md・README・proposal の SKILL.md

### この環境では証明できないもの（未証明）

- 無し（すべて一時ディレクトリの試料で走らせて確かめられる。権限の試料は root では判別しない——既存の試料と同じ扱い）。

### 生成物

- `SKILL.md` の測定値は dev-loop の `SKILL.md` だけを測る——触らないので該当なし。drawio の書き出し: 該当なし。**生成物なし**。

## 未解決の判断・確認待ち事項

- **B の振る舞い（#626 に揃える）は推奨で決めた**（仕様の穴の線。#629 で利用者が schedule-to-gantt.py の同じ向きを承認済み）——要確認の Issue を立てる。
- **C・D の振る舞い（2 で止める）は Issue の推奨のまま**——同じく要確認を立てる（1 件 1 判断）。
- **E は「届く試料を足す」を選んだ**（関数の約束を守る比較を残す。消すより振る舞いが変わらない）。

## 関門の進捗（再開点）

- 実装: 未

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| A を `merge-versions.py` の `exact` で直す | 採らなかった | `exact` を呼ぶのは `drop_internal` だけで、並行する #569 の周（PR #660）が `merge-versions.py` を触る。`drop_internal` の側で途中のリンクを見る |

## 手順 8

- この周の起票: 0 件（この時点で立てた Issue は無い。起票したら直す）
