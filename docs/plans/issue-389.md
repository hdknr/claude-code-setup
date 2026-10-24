# Issue #389 — dev-loop: PR のマージを 1 本のスクリプトにする（オートクルーズの要件候補 4）

#389 の要件候補 7 つのうち、**この周は 4（マージの自動化）だけ**（利用者の判断。2026-10-24・AskUserQuestion）。
残りは #390〜#395 に分けた（利用者の指示「残りは別課題」）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py` — 新規。CI 待ち → worktree の点検 → squash → worktree の撤去 → 閉じた Issue の確認
- `scripts/test-merge-pr.py` — 新規。偽の `gh` と本物の `git` で当てる回帰テスト（変異テストを含む）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 7 にスクリプトを指す項を足す。版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.45.0 → 1.46.0。道具の追加なので minor）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `scripts/check-all.py` — `TESTS` に `test-merge-pr.py` を足す
- `.github/workflows/plugins.yml` — テストのステップを足す
- `CLAUDE.md` — `scripts/` の一覧に `test-merge-pr.py` を足す
- `docs/plans/issue-389.md` — この計画

触らない:

- ブランチの削除（ローカル・リモートとも）——squash したブランチは git から見て未マージなので `-d` が通らず、`-D` は破壊的。報告だけにする
- 要件候補 1〜3・5〜7（#390〜#395）
- `check-pr-preconditions.sh`・`prepare-worktree.sh`
- マージしてよいかの判断（承認）——スクリプトは**マージすると決めた後**の手続きだけを担う

### 同じことを述べている箇所の数

- 「マージの手続き（待つ・点検・squash・確かめる）」: `merge-pr.py` の docstring・`SKILL.md` 手順 7 の 1 項 —— 2 箇所。**終了コードと守る／守らないは docstring を正とし、`SKILL.md` は指すだけ**（列挙を持たない）。
- 分けない理由: 1 本のスクリプトと、その入口の 1 行なので分けようがない。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` は main への push で Pages に載る。

## 周の在り処

- ブランチ: `issue/389-merge-pr-script`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-389`
- 起点: `fdcf631`（Merge pull request #386）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `fdcf631bcc50b87bd40c0e3eb1826ab0f850414e`

## 設計

`merge-pr.py <PR 番号>`（cwd のリポジトリ。標準ライブラリのみ）:

1. **待つ**: `gh pr view --json` を一定間隔で読み、**CI がすべて通り、かつ `mergeable` が `MERGEABLE`** になるまで待つ。
   `UNKNOWN` は「まだ計算中」として待ち続ける（#389 で 2 回止まった罠）。失敗した検査・`CONFLICTING` は即座に止める。
   **検査が 0 本**は通過と読まない（CLAUDE.md: `CONFLICTING` の PR で `no checks reported` になり CI が 1 本も走っていなかった）。
2. **点検**（マージの前）: head ブランチを持つ worktree があれば、未コミットの変更が無いこと・HEAD が PR の head の SHA と一致すること（push 済み）を見る。cwd がその worktree の中なら止める。
3. **squash**: `gh pr merge --squash --match-head-commit <待って見た SHA>`——**待っている間に head が動いたら、見ていないコミットをマージしない**。
4. **撤去**（マージの後）: worktree がロックされていれば `git worktree unlock`（`Agent` の `isolation: worktree` が作るものはロックされている。#389 の罠）、`git worktree remove`（`--force` は使わない）。
   **撤去をマージの後に置く**のは、マージが失敗したとき worktree を残すため。
5. **確かめる**: PR が `MERGED` になったこと、`closingIssuesReferences` の各 Issue が `CLOSED` になったことを、待って再試行しながら見る。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| M1 | `mergeable` が `UNKNOWN` の間は止まらずに待ち、`MERGEABLE` になればマージする | 待ちの判定 | 試料: UNKNOWN → MERGEABLE |
| M2 | 期限までに `MERGEABLE` かつ CI 全通過にならなければ、マージせずに「時間切れ」で止まる（UNKNOWN のまま・検査が走り続ける・検査が 0 本の 3 つ） | 待ちの判定 | 試料 3 つ。`gh pr merge` が呼ばれていないこと |
| M3 | 失敗した検査が 1 本でもあればマージしない（期限を待たずに止まる） | 検査の読み方（`CheckRun` の `conclusion`・`StatusContext` の `state`） | 試料: 片方の型ずつ |
| M4 | `CONFLICTING` ならマージしない | 待ちの判定 | 試料 |
| M5 | マージは squash で、**待って見た head の SHA** を `--match-head-commit` に渡す | `gh pr merge` の引数 | 偽の `gh` が引数を記録 |
| M6 | head ブランチの worktree に未コミットの変更があるなら、マージせず worktree も残す | 点検 | 試料 |
| M7 | head ブランチの worktree の HEAD が PR の head の SHA と違う（push していない）なら、マージせず worktree も残す | 点検 | 試料 |
| M8 | cwd が撤去する worktree の中なら、マージしない | 点検 | 試料 |
| M9 | ロックされた worktree は、マージの後に unlock して撤去できる（`--force` を使わない） | 撤去 | 試料: `git worktree lock --reason "claude agent …"` |
| M10 | マージが失敗したら worktree を撤去しない | 撤去の順序 | 試料: `gh pr merge` が非 0 |
| M11 | マージの後、閉じるはずの Issue が `CLOSED` にならなければ、0 で終わらない（マージ済みであることは言う） | 確かめ | 試料 |
| M12 | PR が `OPEN` でない・draft なら何もしない | 入口 | 試料 |
| M13 | `gh` が失敗・JSON が読めないとき、「通った」「時間切れ」と答えずに「判定できなかった」で止まる | 全段 | 試料: 偽の `gh` が非 0 |
| M14 | 終了コードが段ごとに分かれ、docstring の一覧と一致する | docstring | テストが突き合わせる |
| M15 | docstring の「守る」の各行に変異が 1 つあり、壊すと赤（テストが数える） | `MUTATIONS` | 変異テスト。陽性対照: 壊さない本体で全試料が緑 |
| M16 | テストは実リポジトリ・実の GitHub を触らない（偽の `gh` を `PATH` の先頭に置く・対象はテンポラリ） | テスト | `assert_not_real_repo`。偽の `gh` が呼ばれたことを見る |
| X1 | 版が 3 箇所で揃う・生成ブロックが新しい・全歯止めが緑 | 版・§8.2 | `check-all.py` |

### この環境では証明できないもの（未証明）

- **本物の GitHub の `gh` の出力形**（`statusCheckRollup` の型ごとのフィールド、`UNKNOWN` から戻るまでの時間）。テストは偽の `gh` で当てる。形は 2026-10-24 に `gh pr view 386 --json …`（gh 2.92.0）で 1 度だけ見た。
- **本物のマージ**——公開リポジトリで試しにマージすることはしない。

### 必須要件の掛け算

- 受入基準 × 2 つの関門（Verifier・`/code-review`）× 2 パス = 4 つの受け渡し。2 パス目の修正は狭いパス。

### 生成物

- 該当あり: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を触るので）。`skill-metrics.py --check` が緑であることを受入基準 X1 に入れた。
- 図の書き出し: 該当なし（drawio を触らない）。

## 未解決の判断・確認待ち

- なし（範囲は利用者が決めた）。

## 関門の進捗（再開点）

- 実装: 済み（`merge-pr.py`・`test-merge-pr.py`・`SKILL.md` 手順 7 の 1 項・版 1.46.0・`check-all.py`・`plugins.yml`・`CLAUDE.md`・§8.2 を再生成）
- 実験: `test-merge-pr.py` のみ（偽の `gh` と本物の `git`）。陽性対照 18 試料が期待どおり → 変異 12 件すべて赤。
  交絡の候補「偽の `gh` が呼ばれず本物が走った」→ 偽の `gh` の記録が残ることを見て潰した。
  「ロックが掛かっていないので unlock が要らなかった」→ 変異「unlock しない」が撤去の失敗（rc=9）で赤になることで、ロックが効いていることを見た
- 関門: Verifier・`/code-review` とも未着手（1 パス目の前）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| ブランチを消すか | 消さない | squash したブランチは `git branch -d` が通らず、`-D` は破壊的。範囲の外 |
| 撤去はマージの前か後か | 後 | マージが失敗したら worktree を残すため。点検（未コミット・push 済み）はマージの前に済ませる |
| 検査 0 本を通過とするか | しない（待ち、期限で時間切れ） | CI の無いリポジトリでは使えないが、`CONFLICTING` で CI が走っていない状態を通過と読む誤りのほうが重い |
