# Issue #932 — CI: plugins.yml に concurrency を足し、同じ PR の古い run を止める

cruise（親 Issue #934、台帳 `issue-934`）の周。**不在の周**——出所: `/dev-loop:cruise 934 --absent` の起動（2026-11-10T02:38Z）。
周はサブエージェントが回す（`EnterWorktree` を呼ばない・台帳を書かない・手順 7 のマージはしない）。

使った線（出所: cruise の確かめた線（台帳 `issue-934`）——利用者の確認（起動時・2026-11-10T02:38:35Z、配布を見せて確かめた））:
仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票。実機確認は線が無い（止まる）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-934`））。

`find-cycle.py 932` は終了コード 1 だったが、当たったのは [2] の全 worktree の一覧（絞っていない）と [5] の #929 のコミット 2 本（#932 を起票したことの記録）だけで、
計画ファイル・ブランチ・`issue-932` の worktree は無い。**新規の周**と判定した。

## 変更範囲

触る:

- `.github/workflows/plugins.yml` — 最上位の `concurrency` の追加だけ（`permissions` の直後）。ジョブの中は触らない
- `docs/plans/issue-932.md` — この計画ファイル

触らない:

- `plugins.yml` のジョブの中とジョブの上のコメント（12〜14 行目）——#933（ジョブのコメントの直し）と #931 が並行して触る（親の委譲文の備考）
- `.github/workflows/docs.yml`——Issue が「別に決める」とした。#932 の実装には要らない判断なので仕様の穴ではない（下の「決めたこと」）。
  しかも docs.yml には既に最上位の `concurrency: group: "pages"`（`cancel-in-progress: false`）があり、GitHub Pages のデプロイを直列にしている——同じ形に置き換えると本番のデプロイの直列が変わる。
  その組は PR と main を 1 つにまとめているので、待っている main の run が後から来た PR の run に置き換えられうる（`/code-review` 1 パス目の CR1-2。直近 30 run に取り消しは無く、記録だけ）
- `plugins/` の中——触らないので版は上げない

### 同じことを述べている箇所の数

「plugins.yml の run を同じ PR で止める」: `plugins.yml` の `concurrency` とその上のコメントの 1 箇所。`CLAUDE.md` の plugins.yml の行は「プラグインカタログの整合チェック」とだけ書いており、
concurrency に触れていない（変えない）。複製は 1。

## 乗るデプロイ経路

main へのマージ。`plugins.yml` は CI の定義で、GitHub Pages にもプラグインの配布にも載らない（`plugins/` を触らない）。マージの後の本番状態の確認は「反映経路なし」——
ただし **main への push で走る plugins.yml の run が止まらず走りきること**は、マージの後に親が CI で見られる（下の受入基準 A3 の未証明の項）。

## 版

`plugins/` を触らないので、どのプラグインの版も上げない（`check-version-bump.py` は `plugins/` の中身の変更だけを見る）。

## 決めたこと

### 仕様の穴 G1: main への push の run を、どの組（group）に入れるか

Issue は候補（`group: ${{ github.workflow }}-${{ github.ref }}`・`cancel-in-progress: ${{ github.event_name == 'pull_request' }}`）を挙げ、「決めていない」と書いている。
PR の側はどちらでも同じ（`refs/pull/<番号>/merge` ごと・止める）。違うのは main への push である。

- 選択肢 (a) Issue の候補のまま——main への push は `refs/heads/main` の 1 組で、止めない。**GitHub の concurrency は 1 組に「走っている 1 本と待っている 1 本」しか持たず、
  新しく待つ run は、待っていた run を取り消す**（GitHub の文書の concurrency の説明）。続けて 3 回マージすると、2 回目の merge commit の run は待っている間に取り消され、その commit の検査は走らない。
- 選択肢 (b) PR は ref ごと、push は commit（SHA）ごと——`group: ${{ github.workflow }}-${{ github.event_name == 'pull_request' && github.ref || github.sha }}`。main の run は今と同じく全部走る。
- **推奨: (b)**。Issue が困っているのは同じ PR の古い run だけで、main の run を待たせたり取り消したりする理由が無い。(a) は今は全部走っている main の commit の検査を、続けてマージしたときに落とす（cruise は続けてマージする）。
- 決めた値: (b)。使った線: 仕様の穴 = 推奨で決めて起票（出所は上）。確認の Issue: #936。

### docs.yml に当てるか（仕様の穴ではない）

Issue は「`docs.yml` にも同じ形を当てるかは別に決める」と書いた。#932 の実装（plugins.yml）はこの判断を要らないので、実装に要る判断を仕様が決めていない形（仕様の穴）ではない。
触らない（上の変更範囲）。docs.yml は既に `group: "pages"` を持ち、`deploy` ジョブの GitHub Pages への公開を直列にしているので、当てるなら別の周で、デプロイの直列を保つ形を決める。PR コメントの「記録だけ」に残す。

## verify の受入基準

不変条件と、それを破りうる経路（入口は plugins.yml を起こすイベント: `pull_request`（opened・synchronize・reopened。main の取り込みの push も synchronize）と `push`（main）。
`workflow_dispatch`・`schedule` は plugins.yml に無い）:

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | 同じ PR に push し直したら、古い run が（全ジョブとも）取り消され、新しい run が走る | `pull_request` synchronize（ブランチへの push・main の取り込みの push） | 組が `refs/pull/<番号>/merge` で、`cancel-in-progress` が true | **この PR で実験**: 続けて 2 回 push し、前の run の結論が `cancelled` で、取り消しの理由が concurrency であること（run の注記）。陽性対照: 後の run は走りきる。交絡: 手で取り消した・別の理由で落ちた run と分ける |
| A2 | 別の PR の run は止めない | 2 つの PR が同時に走る | 組に PR の ref が入る | **未証明**（式の読解だけ）——他の PR の merge ref はマージの前の main の plugins.yml を使うので、この変更を持つ 2 本目の PR が無いと観測できない（2 本目の PR を立てるのは外に出る操作） |
| A3 | main への push の run は、取り消されも待たされもせず、どの commit も走る | `push`（main）——続けてマージ | 組が commit の SHA、`cancel-in-progress` が false | **未証明**（式の読解だけ）——main への push はマージでしか起きない。マージの後、親が main の run を見られる |
| A4 | ジョブの中（7 ジョブのステップ・コメント）は変わらない | この周の差分 | 差分を `permissions` の直後の挿入だけにする | `git diff <base>` が `plugins.yml` の挿入行だけと計画ファイルだけ |
| A5 | plugins.yml が workflow として読め、PR で 7 ジョブとも走って通る | PR の CI | — | `gh pr checks` が全部 pass。YAML として読めること（ローカルで `yaml.safe_load`） |
| A6 | 歯止めが全部緑 | 手元 | — | `check-all.py`（run-serial 越し） |

- **生成物**: なし（判定: `diagrams/exports.json`・`skill-metrics.py` の生成ブロックの入力（`SKILL.md`）に触れない。`.github/workflows/` を生成するものはリポジトリに無い）。
- **必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1 パス目・2 パス目とも渡す（4 つの受け渡し。2 パス目が「該当なし」なら 1 パス目の 2 つ）。
- **未証明**: A2・A3（上の表）。PR コメントで人間のレビューに回す。

## 未解決の判断・確認待ち

- G1 の確認の Issue: #936（立てた。閉じない——閉じるのは利用者）

## 関門の進捗（再開点）

- 周の在り処: PR #935・ブランチ `issue/932-plugins-ci-concurrency`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-932`・
  起点 `5bd739f`・base は参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `5bd739f6a3db4071a849782d14dbab3f0d8ea175`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目の指摘対応の起点 `0f0b77211bd71ba79240f9aaad7f873b6561ba2d`（Verifier 1 パス目に渡した時点の HEAD）。
  - Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: 反証 0 件。1 体目（abbff17）は報告を親に渡せず（SubagentHandback が届かなかった）、立て直した 2 体目（a4bc660）も同じで、
    **両方の報告をトランスクリプトから読んだ**——どちらも反証 0 件・`git status --porcelain` は前後とも ` M docs/plans/issue-932.md`。2 体目は A1 の実験を `gh api` で確かめ直して一致とした。
  - `/code-review` 1 パス目（high・PR #935）: 指摘 6 件（下の採否の表）。直すの行 0 件。
  - 1 パス目の指摘対応の差分: `git diff 0f0b772 -- ':(top)' ':(top,exclude)docs/plans/issue-932.md'` は 0 行、`git status --porcelain` は計画ファイルだけ。
  - **2 パス目: 該当なし**（1 パス目の指摘対応の成果物の差分が 0 行。起点 `0f0b772`。判定の 2 本に計画ファイル以外が出なかった）。**狭いパス: 該当なし**。
  - 割り目（手順 6）: 2 パス目が無いので置かない。
- 反証と差し戻し: Verifier の反証 0 件。手順 4 への差し戻しなし
- 交絡を潰した手順（A1 の実験。2026-11-10）:
  - 実験: PR #935 を作り（run 42751701792、`0f0b772`）、その 7 ジョブが 03:47:32〜33Z に走り出した後、03:47:51Z に `28b6c8f`（計画ファイルだけ）を push した（run 42751747754）。
  - 結果: run 42751701792 は `cancelled`、7 ジョブとも `started_at` があって `cancelled`。check ジョブの注記は
    「Canceling since a higher priority waiting request for Check plugin catalog-refs/pull/935/merge exists」——取り消しの理由が concurrency で、組の名前が式の PR 側の値（`<workflow>-refs/pull/935/merge`）であることも出ている。
  - 交絡の候補と潰し方: (1) 手で取り消した・別の理由で落ちた——注記が concurrency の取り消しだと言う。(2) もともと取り消される設定だった——陰性対照: この変更の前の main（PR #930）では同じ PR の
    run 42732150720（`f29ea65`）と 42732175841（`769803e`）が 13 秒違いで始まり、両方とも `success` で走りきった。(3) 新しい run も止まる——陽性対照: 後の run 42751747754 が走りきるかを見る（下の CI の結果）。
  - 観測窓: この PR の 2 本の run だけ。A2（別の PR）・A3（main への push）はこの実験の外（未証明のまま）。

## 既知の限界・決着済みの論点

- docs.yml は触らない（上の「docs.yml に当てるか」）。理由が誤っていると判断したなら、それは新しい反証である。
- G1 は (b) で決めた（上の「仕様の穴 G1」）。決めた値は受入基準を足さない（A3 はもともと「main の run を今より悪くしない」不変条件として置いた）。

### 1 パス目の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1 PR を閉じて開き直す（reopened）と同じ commit の上で古い run が取り消され、`merge-pr.py` の `classify_checks`・`gh pr checks` が `CANCELLED` を失敗に数えうる | 示せない（走らせていない。`statusCheckRollup` が同じ commit の取り消された run を含めるかも未確認） | 無し | 残課題 |
| CR1-2 docs.yml の `group: "pages"` は PR と main を 1 組に入れているので、待っている main の run（デプロイ）が後から来た PR の run に置き換えられうる——「直列を保っている」だけでは理由が足りない | 示せない（docs.yml の直近 30 run に `cancelled` は 0 件） | 無し | 残課題 |
| CR1-3 A1 の実験の記録が未コミット | — | 無し（計画ファイルは関門の検査対象でない） | 捨てる（周の記録。この指摘対応でコミットした） |
| CR1-4 確認の Issue がまだ立っていない | — | 無し（同上） | 捨てる（#936 を立てた） |
| CR1-5 ローカルの `yaml.safe_load` がこのホストの python3 では走らない | 示せない——著者は `uv run --no-project --with pyyaml` で走らせて読めた | 無し | 捨てる |
| CR1-6 再開点が古い | — | 無し（周の記録） | 捨てる（この指摘対応で更新した） |

Verifier の注記（反証ではない）: A2 は 2 本目の PR を立てれば証明できる（欠けているのは外に出る操作の許可）。A1 の観測は 1 回だけ。陰性対照の PR #930 は 7 ジョブ分割の PR で、concurrency の有無だけの比較ではない——取り消しの注記が concurrency を名指しするので主張には足りる。

### 振り分け（手順 8。`references/found-lines.md`）

| 行 | 出所 | 実物で失敗を示せるか | 振り分け |
| --- | --- | --- | --- |
| CR1-1 reopened で同じ commit に `CANCELLED` が残りうる | #932 /code-review 1 パス目 | 示せない | 記録だけ——run が走っている間に PR を閉じて開き直すのは cruise でも手でもまず起きない形。後退を示すか: 示せていない（この変更の前は reopened でも取り消されないので、起きれば後退の形だが、起きることを示していない） |
| CR1-2 docs.yml の `pages` の組で main のデプロイの run が置き換えられうる | #932 /code-review 1 パス目 | 示せない | 記録だけ——既存の形（この周は docs.yml を触らない）で、直近 30 run に取り消しが無い |
| A2・A3 の未証明 | #932 計画 | — | 記録だけ（人間のレビューに回す。マージの前の判断として推奨を PR コメントに書く） |

## 手順 8（起票と件数）

- この周の起票: 1 件（仕様の穴 G1 を推奨で決めた確認の Issue #936。起票の承認は不在のため訊いていない）
