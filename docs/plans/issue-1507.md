# Issue #1507 — cruise: 利用上限の後に再開タイマーが発火しない限界と、上限から戻る経路を書く（#1401 の 1）

**不在の周**（出所: `/dev-loop:cruise 1508 --absent` の起動・2026-11-24T02:32Z の再開）。利用者には訊かない。親（cruise #1508）から委譲文で受けた子。
依存の #1506（PR #1529。dev-loop 2.24.0）はマージ済み。並行に #1453・#1475・#1515 の周が別の worktree で動く（触らない）。

確かめた線（出所: cruise の確かめた線（台帳 `issue-1508`）。利用者の確認（起動時、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`・`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。実機確認の線は無い。
子はマージしない（親の委譲文）。台帳は書かない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1508`））。
版の上げ方: `dev-loop` を **minor**（2.24.0 → 2.25.0。上限から戻る経路の手順を足す）。並行の周が先に上げていたら、マージ直前の取り込みで main の先端の版から minor で 1 つ上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/references/usage-limit.md` — 新しい参照: 観測したこと（#1401）・確かめていないこと・上限から戻る経路（外側のループを起こし直す・OS の cron で 1 回起こす）・気をつけること
- `plugins/dev-loop/skills/cruise/SKILL.md` — §3 の 4 の見出しの「保険」に限界があることを添え、問いの画面に出す限界に 1 項（観測と、上限から戻る経路の案内。新しい参照を指す）。版
- `docs/plugins/dev-loop-cruise.md` — §5 の限界の箇条に 1 項・「利用上限で止まったとき」に 1 文・「外から繰り返し起動するとき」に「利用上限の後に起こし直す」の段落
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `docs/plans/issue-1507.md` — この計画

触らない:

- `scripts/outer-loop.py`（利用上限を読んで待つ機能は足さない——Issue は案内を求めている。spec-loop の `autopilot-loop.py` は待つが、本物の `claude` の上限の出力の形は測っていないので写さない）
- `check-unattended-env.py` の docstring の「タイマーを保険に張るかは利用者が決める（公開ページ §5）」（指し先の §5 に限界を足すので、指すだけの行は食い違わない）
- `references/parallel.md` の「見張りの終わりの通知で起きなければ、再開タイマーが保険」（背景の作業の完了の通知の話で、利用上限の話ではない）
- `docs/usage/usage-limit-stop-hook.md`（自動継続を数える手順で、cruise の戻り方ではない）
- #1401 のほかの項

依存の追加・更新: なし
仕様の振る舞い: 正本なし（このリポジトリは spec-loop の正本ではない。`check-spec-writeback.py` で確かめる）

同じことを述べている箇所の数: 4（原本の `references/usage-limit.md` と、指す側の cruise の `SKILL.md` §3 の 4 の 1 項、公開ページの §5 の 1 項と「外から繰り返し起動するとき」の段落。「利用上限で止まったとき」の 1 文は §5 を指すだけ）。
分けない理由: 観測の範囲と手順の原本は `references/usage-limit.md` の 1 か所で、`SKILL.md` と公開ページは要約して指す。Issue が `SKILL.md` の 3 の 4 と公開ページの両方に限界を書くことを求めている。指し先の節の名前は `check-skill-pointers.py` が照合する。

## デプロイ経路

main へのマージで、プラグインの配布（`marketplace.json` の版）と GitHub Pages（公開ページと計画ファイル）。`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`。子はマージしない。

## 受入基準

Issue の受入基準: (a) 問いの画面に出す限界に、上の観測が入っている（観測の範囲と確かめていないことを書き分ける）。(b) 上限から戻る経路の手順が `SKILL.md` か `references/` にあり、`outer-loop.py` の実際の引数と合っている。

不変条件 × 破りうる経路（入口: cruise の親が読む `SKILL.md` §3 の 4（新規の起動の問いの画面）と、そこから指す `references/usage-limit.md`・利用者が読む公開ページ（§5・「利用上限で止まったとき」・「外から繰り返し起動するとき」）・利用者が打つ `outer-loop.py` と crontab の行・再開した親（`/clear` の後・`--timer` の起動）・居る cruise と不在の cruise）:

| # | 不変条件 | 経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| 1 | `SKILL.md` §3 の 4 の「問いの画面に出す限界」に、利用上限の後にタイマーが発火しなかった観測が入り、1 例であること・原因を確かめていないことが書いてある（断定しない） | `SKILL.md` §3 の 4 | 読む |
| 2 | 観測の範囲（何を見たか: 時刻・発火の欠け・`CronList` にジョブが残っていた・次の発火）と、確かめていないこと（原因・いつもか・次の発火を何が起こしたか）が分けて書いてあり、#1401 の記録と食い違わない | `references/usage-limit.md`・`SKILL.md`・公開ページ | #1401 の本文と読み比べ |
| 3 | 上限から戻る経路（外側のループを起こし直す・OS の cron で起こす）の手順が `references/` にあり、`SKILL.md` §3 の 4 から指されて、親が問いの画面で案内する | `SKILL.md`・`references/usage-limit.md` | 読む・`check-skill-pointers.py` |
| 4 | 手順の `outer-loop.py` の引数・振る舞い（位置引数の親の番号・`--absent`・`--claude`・`--` の後ろの足す引数・`--max-stalls` の既定 2・`--max-total-usd` を起こし直すと 0 から数える・`status` が 0 のときだけ起こす・止まるたびに通知する・上限を読まない・終了コード 6・8）が、`outer-loop.py --help` と docstring と実装に合っている | `references/usage-limit.md`・公開ページ | `--help`・docstring・実装と読み比べ |
| 5 | cron の行の例が、それ自体で誤った動作をさせない——1 回きり・絶対パス・`lockf -t 0` で 2 本並ばない・`claude` を直に起こさず外側のループを起こす。確かめた範囲（`lockf` の重なりの止め方だけ）と確かめていないこと（cron からの起動・認証）が書き分けてある | `references/usage-limit.md` | `lockf` を手元で当てた結果・読む |
| 6 | 同じ台帳を回す親が 2 体にならない注意がある——対話のセッションのタイマーと外側のループ・cron が重なりうること | `references/usage-limit.md`・公開ページ | 読む（`outer-loop.py` の「守らない」と食い違わない） |
| 7 | 既存の §3 の 4 の決まり（張る・張らない・`--timer` の起動で訊かない・張り直し）と、公開ページの §5・「`claude -p` で外から回すとき」と食い違わない | `SKILL.md`・公開ページ | 読み比べ |
| 8 | 公開ページの記述が原本（`references/usage-limit.md`）と食い違わない | 公開ページ | 読み比べ |
| 9 | 版が 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本）で揃って上がる | 版 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| 10 | 歯止め全部（`check-all.py`）が緑 | 全体 | `run-serial.py` 越しの `check-all.py` と PR 側の CI |

必須要件の掛け算: 受入基準を両方の関門（Verifier・`/code-review`）に × 2 パス（1 パス目・2 パス目。1 パス目の指摘対応が 0 行なら 2 パス目は該当なし）= 4 つの受け渡し。2 パス目で直した行があれば狭いパスにも受入基準をまるごと渡す。

証明できないもの（未証明）: 案内した経路で、実際に上限の後に cruise が戻ること——利用上限を狙って起こせず、cron から本物の `claude` を起こすことも利用者の crontab を書き換えるのでこの周ではしない。受入基準は文面と `outer-loop.py` との整合で、戻ることは主張しない（`references/usage-limit.md` に「cron から実際に起こしたことは無い」と書いた）。
生成物: なし（`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` の節構造に依るが、この周は dev-loop の `SKILL.md` の版の行だけを変える——`skill-metrics.py --check` で確かめる）。
プロパティテスト: なし（散文の決まりの周で、往復・冪等性・数値の境界を持つ実装が無い）
差分テスト: なし（振る舞いを変えない周ではない——限界と案内を足す）

## 未解決の判断・確認待ち

- 仕様の穴: なし。Issue の「OS の cron から、解除の時刻の後に起こし直す」を、cron に `outer-loop.py` を 1 回だけ起こさせる形にした——`claude` を直に起こすと `status` を見ずに起こし、繰り返しにすると `outer-loop.py` が止まるたびに通知するので同じ通知が並ぶ。新しい判断ではなく、既存の `outer-loop.py` の振る舞いから決まる。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1507-cron-after-usage-limit`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1507`・
  起点 `59b5db8b`・base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `59b5db8ba4db19fe2dd891b181ba18ab11871280`
- 割り目（手順 4）: 割らない（cruise の周）
- 交絡を潰した手順: `lockf -t 0` の重なりの止め方を手元で当てた（1 本目が握っているあいだの 2 本目が 75 で断られ、離した後の 3 本目は走った——断る側と走る側の両方を見た）。ほかに実験なし。

## 既知の限界・決着済みの論点

- `outer-loop.py` に利用上限を読んで解除の時刻まで待つ機能を足さない（決着: 採らない。理由: Issue は案内を求めている。本物の `claude -p` の上限の出力の形は測っておらず、spec-loop の `autopilot-loop.py` もその形を測っていないと書いている）。
- cron の行を繰り返しにしない（決着: 1 回きり。理由: `outer-loop.py` は止まるたびに通知し、上限が解けていなければ起動のたびに止まる）。
- cron から起こした `claude` の認証・cron からの起動そのものは確かめない（決着: 未証明として書く。理由: 利用者の crontab を書き換え、本物の `claude` を起こすので、この周ではしない）。

## 手順 8 の記録

- この周の起票: 0 件（不在の cruise の周。周の途中の課題で直すに入った行は無く、起票の候補は無い）
