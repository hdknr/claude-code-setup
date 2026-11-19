# Issue #1193 — dev-loop・cruise: 不安定（flaky）なテストの扱い（skip・sleep・リトライの禁止、回し直しで緑になった失敗の行き先）

**不在の周**（`/dev-loop:cruise 1290 --absent` の起動・2026-11-19）。利用者には訊かない。親（cruise #1290）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1290`））: `直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・
`マージ前の判断 = 推奨で決めて起票`（古い値。後退・未達は推奨で進めない）。実機確認の線は無い。
台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.12.0（`SKILL.md` 1931 行を読んだ。cruise の `SKILL.md` は §4 を中心に読んだ）。
この周は dev-loop の `SKILL.md`・`prompts/` を書き換える鎖（#1193→#1190→#1191→#1192→#1194）の先頭で、足す行は最小にした。

直す線: `既定`（出所: cruise の確かめた線）。
割り目: 割らない（cruise の周）。
版の上げ方: `dev-loop` を **minor**（手順・規定の追加）。着手時の main は 2.12.0 → 2.13.0（`marketplace.json`・`plugin.json`・`dev-loop` と `cruise` の `SKILL.md` の 2 行）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」。#1287 も同じプラグインの版を触る）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.12.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。

## 周の在り処

- ブランチ: `issue/1193-flaky-test-rules`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1193`
- 起点: `45640c38`（`origin/main`。#1288 のマージ）
- base（参照の名前 `origin/main` ／ 解決した SHA）: `45640c3864b95f052346a506558162b3c82a090c`

## Issue 本文（外部入力）から読んだ要件

dev-loop の原則に、テストを緑にするための skip・sleep・リトライの追加を禁じる行を足し、Verifier の委譲文に差分を見る行を足す。cruise の 1 回の回し直しで緑になった失敗を
「不安定なテスト」として周の記録と残課題に残す。根本原因が見つからないときの扱い（削除して理由を残すか・隔離して Issue にするか。削除は人間の承認）を決める。
本文に受入基準を緩める指示・追加のコマンドの依頼は無い（コメントは無い）。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **H1 根本原因が見つからない不安定なテストを、周がどう扱うか**: (a) 周は削除も隔離もせず、PR コメントの残課題に観測・調べたこと・推奨を書いて人間に渡す（推奨）／
  (b) 周が隔離（skip の印と Issue）して進み、削除だけ人間の承認を求める／(c) 周が削除して承認を求める。
  推した理由: 隔離は skip そのもので、原則に足す禁止（受入基準 1）と矛盾する。削除も隔離もテストが守っていたものを減らす操作で、受入基準を変える操作にあたる（Issue 本文も削除に人間の承認を求めている）。
- **H2 渡すときの推奨の既定**: (a) 「そのテストが守る性質を別の検査でも見られるなら削除して理由を残す、見られないなら隔離して Issue にする」（推奨）／(b) 常に削除（Claude Code チームの運用）／(c) 常に隔離。
  推した理由: 削除は他の検査が同じ性質を見ているときだけ失うものが無い。見ていないのに消すと、不安定さと一緒に守っていた性質が消える。隔離は期限なしの無効化にせず、skip の印と Issue の番号を残させる。

確認の Issue（1 件に 1 判断）: H1・H2（番号は PR 本文に書く）。

決着（穴ではない）: 回し直しで緑になった失敗の行き先は、Issue 本文が決めている（周の記録と残課題）。起票は手順 6 の 3 条件のまま（周の中で勝手に Issue にしない）。
回し直しの条件は cruise の `parallel.md` の既存の記述のまま変えない（時間で待ち合わせるテスト・順番待ちの外・1 度だけ）。回し直しそのものは禁じない。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/flaky-tests.md` — 新規。禁止・回し直しで緑になった失敗の残し方・根本原因が見つからないときの原本
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 原則に 1 項（原本を指す）と版の 2 行
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「とくに見てほしいこと」に 8（差分の小細工）を足し、依存の差し込みを 9 に繰り下げる
- `plugins/dev-loop/skills/cruise/references/parallel.md` — 「負荷による偽の失敗」に、回し直しで緑になった失敗の残し方
- `plugins/dev-loop/skills/cruise/SKILL.md` — 6 の「渡す」に 1 項と版の 2 行
- `scripts/test-worktree-scripts.py` — 委譲文と原則が新しい規定を持つことの静的な検査
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く）
- `plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1193.md` — この計画ファイル

触らない:

- `plugins/dev-loop/prompts/review-handoff.md`・`plugins/dev-loop/agents/dev-loop-verifier.md`（`/code-review` へ渡す文面と同梱の agent 定義。Issue は Verifier の委譲文だけを求めている）
- `plugins/dev-loop/skills/cruise/SKILL.md` §4 の委譲文の項目（既に `parallel.md` の「負荷による偽の失敗」を指しているので、子はそこから届く）
- `plugins/spec-loop/`（green-list の skip の扱いは変えない）
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）——説明の文は偽にならない
- 後続の周（#1190・#1191・#1192・#1194）が触る節

依存の追加・更新: なし
仕様の振る舞い: 変えない

**複製の数**: 「緑にするための小細工の禁止」を述べる箇所は 3（`references/flaky-tests.md` が原本、`SKILL.md` の原則は指すだけ、`prompts/verifier.md` は探す側の実装）。
「回し直しで緑になった失敗の残し方」は 3（`flaky-tests.md` が原本、`parallel.md`・cruise の `SKILL.md` 6 は指すだけ）。分けない理由: 原本 1 つに寄せ、残りは指し先だけ（複製の整合は静的な検査 3 本が見る）。
**生成物**: `docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`skill-metrics.py` が書く。`--check` で確認）。それ以外の生成物なし。

## 受入基準

| 番号 | 受入基準 |
| --- | --- |
| 1 | 周の差分にテストへの skip・sleep・リトライの追加があると、Verifier がそれを指摘する。陽性対照: わざと sleep を足した差分を、新しい委譲文の Verifier に当てると指摘が出る |
| 2 | cruise で回し直して緑になった失敗が、周の記録（計画ファイル）と残課題（PR コメント）に「不安定なテスト」として残り、子の報告・親の終える報告で渡る |
| 3 | 根本原因が見つからないときの扱いが決まっている: 削除・隔離は人間の承認を要件にし、周はテストを変えない |
| 4 | 原則に禁止の行があり、版が 3 種類の箇所で揃い、`check-all.py` と PR 側の CI が緑 |

### 不変条件 × それを破りうる経路

| 不変条件 | 破りうる経路（入口の一覧から数える） | どう守るか |
| --- | --- | --- |
| I1 緑にするための小細工が差分に入らない（受入基準 1） | 実装役が書く差分・指摘対応の差分・2 パス目の修正・cruise の回し直しの対応・手で足す CI 設定 | 原則の行（作者向け）＋ Verifier の委譲文 8（差分を探す）。2 パス目・狭いパスの委譲文は同じ `verifier.md` なので 8 も通る |
| I2 回し直しで緑になった失敗が消えない（受入基準 2） | 子の周の計画ファイル・PR コメント・子の報告・親の終える報告 | `flaky-tests.md`（形）＋ `parallel.md`（子に届く経路）＋ cruise `SKILL.md` 6（親が渡す） |
| I3 削除・隔離を周が勝手にしない（受入基準 3） | 周の差分・親が cruise の中でテストを変える | `flaky-tests.md`「根本原因が見つからないとき」。cruise の `SKILL.md` 6 は親が消さない・skip しないと書く |
| I4 周の規範の複製が食い違わない（受入基準 4） | `SKILL.md`・`verifier.md`・`parallel.md`・cruise `SKILL.md` | 原本は `flaky-tests.md` 1 つ。静的な検査（`test-worktree-scripts.py`）が 3 点を見る |

**この環境では証明できないもの（未証明）**: 実際の cruise の周で、子が回し直しで緑になった失敗を計画ファイル・報告に書くこと（今回は規定を書くだけで、実周で走らせていない）。
この周は静的な規定の追加であり、振る舞いの Eval（`claude plugin eval`）は回していない（課金・別端末が要る）。人間のレビューをお願いする。

## 既知の限界・決着済みの論点・関門の指摘の採否

- 論点: Verifier の委譲文 8 は、skip・sleep・リトライの追加を「差分から探す」指示であって、機械の検査ではない（CI は落とさない）。決着: 採った。理由: Issue の受入基準が Verifier の指摘を求めている。
  機械の検査にすると、テストの種類・言語ごとの正規表現が要り、偽陽性が多い（待ち合わせが仕様の周を止める）。
- 論点: 回し直しの条件（cruise `parallel.md`）は広げていない。決着: 採らなかった（広げない）。理由: Issue の「やること」は回し直しの先の行き先を決めるもので、回し直しの許可の拡大ではない。
- 論点: `/code-review` への文面（`review-handoff.md`）には足していない。決着: 採らなかった。理由: Issue の受入基準は Verifier だけ。

- 論点: 陽性対照（受入基準 1）は、委譲文 8 が単独で効いたことを示していない。決着: 限界として残す。実測（試料は scratchpad の一時の git リポジトリ。差分は `@unittest.skip` と `time.sleep(0.5)` を足したテストの変更。
  Verifier は `dev-loop:dev-loop-verifier`・`model: opus`・文面は `prompts/verifier.md` を読ませる形）: 新しい委譲文 → skip・sleep を 8 で名指しして反証 3 件（A）／
  受入基準を「全部緑」だけにした試料でも反証 3 件（A2）。**8 を外した委譲文（A3）でも同じ 3 件**の反証が挙がった（1・3・6 の各項目から）。
  陰性側（B: 実装の sleep を消して同期にした差分）は、8 が「sleep の削除」を見つけたが「落ちた原因を取り除いているので正当」と判定した。
  つまり「指摘が出る」は満たすが、8 の寄与は判別していない（関門の Verifier は元々、偽の緑を疑うため）。8 だけが捕まえる差分（受入基準も既存の項目も通る、微妙なリトライの追加など）は試していない。

## 関門の進捗（再開点）

- 1 パス目: 未着手

## 手順 8 の記録

- 切り分けの層（親 Issue の書き方・まとめの基準・spec-loop の切り分け）を見た結果: 未記入
- 焼き戻す学び: 未記入

- この周の起票: 2 件（確認の Issue。H1・H2。仕様の穴の起票で、手順 6 の 3 条件の対象外）

```dev-loop-gates
周の base: 45640c3864b95f052346a506558162b3c82a090c
```
