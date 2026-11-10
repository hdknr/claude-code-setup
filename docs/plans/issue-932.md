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
  しかも docs.yml には既に最上位の `concurrency: group: "pages"`（`cancel-in-progress: false`）があり、GitHub Pages のデプロイを直列にしている——同じ形に置き換えると本番のデプロイの直列が変わる
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
- 決めた値: (b)。使った線: 仕様の穴 = 推奨で決めて起票（出所は上）。確認の Issue: PR を作った後に立てる（番号は下の「未解決の判断・確認待ち」に書く）。

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

- G1 の確認の Issue: （PR を作った後に立てる）

## 関門の進捗（再開点）

- 周の在り処: PR #935・ブランチ `issue/932-plugins-ci-concurrency`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-932`・
  起点 `5bd739f`・base は参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `5bd739f6a3db4071a849782d14dbab3f0d8ea175`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目の指摘対応の起点 `0f0b77211bd71ba79240f9aaad7f873b6561ba2d`（Verifier 1 パス目に渡した時点の HEAD）。Verifier 1 パス目: 起動（報告待ち）
- 反証と差し戻し: まだ無い
- 交絡を潰した手順: まだ無い（A1 の実験で書く）

## 既知の限界・決着済みの論点

- docs.yml は触らない（上の「docs.yml に当てるか」）。理由が誤っていると判断したなら、それは新しい反証である。
- G1 は (b) で決めた（上の「仕様の穴 G1」）。決めた値は受入基準を足さない（A3 はもともと「main の run を今より悪くしない」不変条件として置いた）。

## 手順 8（起票と件数）

- この周の起票: 1 件（仕様の穴 G1 を推奨で決めた確認の Issue。起票の承認は不在のため訊いていない）
