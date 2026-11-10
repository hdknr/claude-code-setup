# Issue #925 — spec-loop の autopilot の回し方（外側のループ・線・前提）の公開ページ

不在の周（cruise の子）。出所: `/dev-loop:cruise 916 --absent` の起動（2026-11-10）。親 Issue #916・台帳 `issue-916`（台帳は親だけが書く）。
従う版は dev-loop 1.103.0（キャッシュ `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.103.0/skills/dev-loop/SKILL.md`）。

- 使った線（出所: cruise の確かめた線（台帳 `issue-916`。利用者の確認・起動時 2026-11-08T08:00:42Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す。マージ前の判断は線が無い（止まる——人の判断が要るものは「マージ前に人が判断」として報告する）
- 直す線: **既定**（出所: 上の cruise の確かめた線）
- 版の上げ方: **上げない**——`plugins/` を触らない（`docs/` と `mkdocs.yml` だけ。`check-version-bump.py` の対象外）
- PR は `Fixes #925`。手順 7 のマージは親がする（子は PR と PR 側の CI まで）
- 依存: #924（PR #943）はマージ済み（main `8cdd68a`）。この周はその上から切った

## 周の在り処

- ブランチ: `issue/925-spec-loop-autopilot-page`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-925`
- 起点コミット: `8cdd68a`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `8cdd68a7ae9c75e6377f2226f33107aeb302460a`

## 変更範囲

触る:
- `docs/plugins/spec-loop-autopilot.md` — 新しいページ（Issue の 1〜6）
- `mkdocs.yml` — nav の「プラグイン」に新しいページを足す
- `docs/plugins/index.md` — spec-loop の節の `autopilot` の 1 行から新しいページを指す
- `docs/plugins/spec-loop.md` — 冒頭の案内（と流れの節）から新しいページを指す
- `docs/plans/issue-925.md` — この計画

触らない:
- `plugins/spec-loop/` の中（`skills/autopilot/SKILL.md`・`scripts/autopilot-*.py`・`check-tlc.py`・README）——決まりの原本で、新しいページは指すだけ
- `plugins/dev-loop/` の中（`launch-with-long-token.sh`・cruise の `outer-loop.py`）——同上
- `docs/plugins/dev-loop-cruise.md`・`docs/usage/cruise-long-lived-token.md`——指すだけ（autopilot の記述を足さない）

複製の数（同じことを述べている箇所）:
- autopilot が何をするか（1 単位・台帳・しないこと）: 原本 `skills/autopilot/SKILL.md`、要約 `plugins/spec-loop/README.md` の節・`index.md` の spec-loop の節の 1 行・`index.md` の TLC の項、そして**この周が足すページ**。要約が 1 つ増える。
  分けない理由: Issue の求めが専用のページ（cruise の `dev-loop-cruise.md` と同じ形）で、ページは要点と指し先だけを持ち、線の項目・終了コード・止まる条件の細部は写さない。`index.md` の 1 行は新しいページへのリンクに寄せる
- 外側のループの止まる条件: 原本 `autopilot-loop.py` の docstring。ページは条件の名前だけを並べ、終了コードの表は写さない
- 線の項目: 原本 `autopilot-check.py` の docstring（値の一覧）と `SKILL.md` の 2（値ごとの振る舞い）。ページは 4 項目の名前と役割の一言だけ

## デプロイ経路

`docs/` と `mkdocs.yml` の変更——main へのマージで GitHub Pages の再ビルドと公開（`docs.yml`）。プラグインのカタログには何も配布しない（`plugins/` を触らない）。マージは親がする。

## verify の受入基準

不変条件と、それを破りうる経路:

1. **ページがあり、nav と `index.md`・`spec-loop.md` から辿れる。**
   経路: `mkdocs.yml` の nav の行・`index.md` の spec-loop の節の `autopilot` の行のリンク・`spec-loop.md` の冒頭の案内（と流れの節）のリンク。ビルドした HTML でリンクが解決する。
2. **Issue の 1〜6（何をするか・起動時の確認・外側のループ・前提・止まったあと・守らないもの）がページにある。**
   経路: ページの各節。
3. **書いた事実が原本と食い違わない**——台帳のパス（`.claude/plans/spec-autopilot-v<版>.json`）・1 単位の中身（仕様レビューの周の 1 段か feasibility の 1 回）・しないこと（タグ・scaffold・Issue の登録）・起動時の確認（台帳が無いとき・`--lines`。単位を進めない）・
   外側のループの止まる条件の名前（`stopped`・`done`・判定できない・前進なし・起動の上限・同じ状態の上限・`claude` の失敗・上限の解除が遠い）と使用量の上限での待ち・長期トークンの渡し方（`--claude`）・
   TLC を確かめる段（`round1`・`round2`・`narrow`。`commit` と feasibility では確かめない）・ログの場所（`spec-autopilot-v<版>-loop/`）・再開のしかた（`next` を済ませて `status=running reason= next=` で戻す）。
   照合先: `skills/autopilot/SKILL.md`・`autopilot-ledger.py`・`autopilot-check.py`・`autopilot-loop.py`・`check-tlc.py` の docstring、`launch-with-long-token.sh`。
4. **決まり（線の項目と値の一覧・終了コード・止まる条件の細部）を書き写さず、`skills/autopilot/SKILL.md`・`autopilot-check.py`・`autopilot-ledger.py`・`autopilot-loop.py` の docstring を指している。**
   経路: ページの各段落の指し先のリンク。守り方: 指し先のファイルが main に実在する。終了コードの表・線の値の表がページに無い。
5. **既存のページ（`index.md` の spec-loop の節と TLC の項・`spec-loop.md` の形式検査の節・`dev-loop-cruise.md` の外側のループの節・`cruise-long-lived-token.md`）と食い違っていない。**
   経路: 新しいページの同じ話題の文。
6. **`python3 scripts/check-all.py` と `uv run mkdocs build --strict` が通る（ページ内・ページ間のアンカーが実在する）。**

必須要件の掛け算: 受入基準を 2 つの関門 × 2 パス（1 パス目の指摘対応の差分が 0 行なら初回の 2 つ）に渡す。

### この環境では証明できないもの（未証明）

- 本物の `claude -p` で autopilot と外側のループを回したときに、ページの説明どおりに振る舞うこと——原本の docstring 自身が「守らない」としている（本物の上限の出力の形・入口が追記に従うか）。ページはそう書き、主張を「原本がそう決めている」まで弱める。

### 生成物

- **生成物なし**——drawio の書き出し・`SKILL.md` の測定値（`skill-metrics.py`）・spec-loop の生成物のどれにも触らない。サイトの HTML はビルドで作るもので、リポジトリに置かない（`mkdocs build --strict` で作れることだけを見る）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 割り目（手順 4）: 割らない（cruise の周）
- 交絡: 実験なし（ドキュメントの周。ビルドと歯止めの実行だけ）
- 実装: 済み（前の子の書きかけを確かめて引き継ぎ、`06d550f` にコミット）。
  歯止め: `check-all.py`（run-serial 越し）70 本のうち落ちたのは `check-plan-counts.py` だけ（この計画の件数の行が無かった）→ 行を足して `check-plan-counts.py` が緑。
  `mkdocs build --strict` は手元の Python 3.12.8 では `docs/plans/issue-332.md` で AssertionError（既知。#354・#446・#924 の計画に記録あり。この周の変更と無関係）→ CI と同じ系の Python 3.14.7（`UV_PROJECT_ENVIRONMENT` を scratchpad に置く）で警告 0・終了 0
- 1 パス目の指摘対応の起点: `06d550f671601522e08af19447124358499da1dd`（1 パス目の関門に渡した時点の HEAD）
- Verifier 1 パス目: 通した——反証 0 件（未確認 1 件: ページの Alloy の文。親が `spec-loop.md` の形式検査の表 90 行と照合して一致——採否の表 V1）。
  報告は SubagentHandback で返したが親に届かず、親が Verifier のトランスクリプトから読んだ
- `/code-review` 1 パス目: 通した——指摘 9 件（採否の表 R1〜R9。直す 6・残課題 3）
- 手順 5 への差し戻し: なし（Verifier の反証 0 件）。`/code-review` の直す 6 件は 1 パス目の指摘対応として直す
- 1 パス目の指摘対応: 済み（`f29b7b8`。成果物の差分 `git diff 06d550f -- ':(top)' ':(top,exclude)docs/plans/issue-925.md'` は `spec-loop-autopilot.md` の 11 行＋/11 行−で 0 行ではない）。歯止め: `check-all.py` 70/70 緑・`mkdocs build --strict`（Python 3.14）警告 0・終了 0。残るのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の**両方**
- 割り目（2 パス目の前）: 割らない（cruise の周）
- Verifier 2 パス目: 通した——反証 0 件・未確認 0 件（報告は SubagentHandback が届かず、親がトランスクリプトから読んだ。所見 1 件: 部品の表の入口の行が `stopped` で `--lines` を付ける例外を省く——2・5 節が補っているので反証ではないと Verifier 自身が判定）
- `/code-review` 2 パス目: 起動（結果待ち）

## 既知の限界・決着済みの論点

- ページは決まりを写さない（`dev-loop-cruise.md` と同じ方針）。線の値の表・終了コードの表を足せという指摘は、受入基準 4 に反するので採らない。
- 「部品をそろえて通しで回した実績」の有無は、この周では確かめない（#789 の試作は部品が入る前の手作りのもの）。ページには「部品だけで通しで回した実績は確かめていない」とだけ書く。

### 採否の表（1 パス目）

直す線は既定（「示せる」かつ「破る受入基準がある」行だけ直す）。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | （Verifier・未確認）ページの「Alloy は起動時の点検では見ず、その回に確かめて無ければ止まる」の原本が取れていない | 示せない——`docs/plugins/spec-loop.md` 90 行の形式検査の表が同じことを書いており一致 | 無し | 捨てる（確かめて一致） |
| R1 | （/code-review）線の 4 項目を名前と役割つきで列挙し「4 項目」と数を書いている——線の項目の写し | 示せる——ページ 51〜52 行が `autopilot-check.py` の docstring の「線」の項目を列挙 | 4 | 直す——列挙と数をやめ、訊く場面の例（「など」）にして docstring を指す |
| R2 | （/code-review）長期トークンの記述が `cruise-long-lived-token.md` より強い（8 時間を超えて止まらないことは未確認・Remote Control などが使えない） | 示せない——ページは「長く回すなら長期トークンで起動します」と手順を書いているだけで、止まらないとは書いていない。既存ページの題も「8 時間の期限で止めない」 | 無し | 残課題 |
| R3 | （/code-review）`業務フローの形式検査: しない` で外せると書くが、業務フローを対象に選んだ回は TLC を確かめて止まることが抜けている | 示せる——`docs/plugins/spec-loop.md` 89 行が「宣言しても…その回は TLC を確かめ、無ければそこで止まる——autopilot もその回は止まる」 | 5 | 直す——但し書きと指し先を足す |
| R4 | （/code-review）「spec-loop のスクリプトは線に依らず」が誤り——`止まる地点 = feasibility の後` なら feasibility のスクリプトも点検する | 示せる——`autopilot-check.py` 36 行の docstring・418 行 | 3 | 直す——線の値で変わると書き、docstring の「点検する操作」を指す |
| R5 | （/code-review）`--flag-settings` の指し先「上の 2. 起動時の確認」にその話が無い | 示せる——2 節に `--flag-settings` の語が無い（61 行は docstring を指す） | 無し（指し先は docstring で実在） | 残課題 |
| R6 | （/code-review）部品の表の入口が「在れば次の 1 単位だけを進める」——`stopped`・`done` では何もしない | 示せる——`skills/autopilot/SKILL.md` の「1. 台帳を見る」の表 | 3 | 直す——`running` のときだけ・`stopped`・`done` は何もしない |
| R7 | （/code-review）注意書きは「止まる条件の細部を写さない」と言うが、3 節が止まる条件ごとのオプション名と上限の数え方を写している | 示せる——ページ 84〜88 行の `--max-stalls` などと「前進なし・同じ状態の回数には数えません」 | 4 | 直す——オプション名と数え方を外し、docstring を指す |
| R8 | （/code-review）TLC を確かめる段の記述が `index.md`・README・`spec-loop.md` に続く 4 つ目の写し | 示せない（いま食い違っていない。将来の食い違いの話） | 無し（受入基準 3 がこの事実をページに求めている） | 残課題 |
| R9 | （/code-review）`--lines` は `done` の台帳では何もしない（入口の「1. 台帳を見る」）のに、ページは「線を書き直して点検し直します」とだけ書く | 示せる——`skills/autopilot/SKILL.md` の「1. 台帳を見る」の 5（`done`）の行 | 3 | 直す——`done` では何もしないと書き、入口の 1 を指す |

## 手順 8（起票と件数）

- この周の起票: 0 件（cruise の子・不在の周。起票の候補は手順 8 の振り分けで決め、変われば直す）
