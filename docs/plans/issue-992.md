# Issue #992 — cruise・autopilot: 外側のループに全体の費用の上限を足す

**不在の周（cruise の子）**——親 Issue #1038 の不在の cruise（`/dev-loop:cruise 1038 --absent` の起動・2026-11-15）から委ねられた周。
台帳の確かめた線（出所: 利用者の確認（起動時・2026-11-15T02:04:18Z、配布を見せて確かめた））:
仕様の穴 = 推奨で決めて起票、直す線 = 既定、マージ = 関門を通ればマージ、周の途中の課題 = 台帳に足して直す、マージ前の判断 = 推奨で決めて起票。実機確認の線は無い（既定）。
マージは親がする（この周は PR 側の CI の最終結果を見るまで）。台帳は書かない（書くのは親）。

**版**: dev-loop を minor（1.108.0 → 1.109.0）、spec-loop を minor（0.88.0 → 0.89.0）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/outer-loop.py` — `--max-total-usd`・起動ごとの費用の読み取り・子プロセスの周の費用の合計・止まった行の費用・出力の記録
- `plugins/spec-loop/scripts/autopilot-loop.py` — `--max-total-usd`・起動ごとの費用の読み取り・止まった行の費用（`read_cost`・`cost_of` は outer-loop の写し）
- `scripts/test-outer-loop.py` — 試料と変異
- `scripts/test-autopilot-loop.py` — 試料と変異・写しの突き合わせに `read_cost`・`cost_of` を足す
- `plugins/dev-loop/skills/cruise/SKILL.md` — §6 の外側のループの止まる条件の 1 文と版の 2 行
- `docs/plugins/dev-loop-cruise.md` — 外側のループの節に費用の上限の 1 項
- `docs/plugins/spec-loop-autopilot.md` — 外側のループの節に費用の上限の 1 項
- `CLAUDE.md` — `outer-loop.py`・`autopilot-loop.py` の説明の止まる条件に「費用の合計の上限」
- `.claude-plugin/marketplace.json` — dev-loop・spec-loop の版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/dev-loop/skills/` — 各 `SKILL.md` の版の 2 行
- `plugins/spec-loop/skills/` — 各 `SKILL.md` の版の 2 行
- `docs/plans/issue-992.md` — この計画

触らない:

- `ledger.py`・`autopilot-ledger.py`（台帳の書式・`progress`）——費用は台帳に書かない（受入基準 3）
- `child-cycle.py`——読み方（`read_meta`・`is_running`・`summarize`）を outer-loop から読み込むだけで変えない
- 1 回のループの起動をまたいだ合計（下の「決めたこと」の 4）

依存の追加・更新: なし

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。

## 決めたこと（Issue が「計画で決める」とした 2 つと、その周辺）

1. **置き場所は台帳の隣の記録**——台帳には書かない（`progress` に混ぜない・`ledger.py set` が `updated` を書き換えるので前進の判定にも触れない）。
   - **起動ごと**: outer-loop は `claude` を `--output-format stream-json --verbose` で起こし、標準出力・標準エラーを台帳の隣の `cruise-issue-<親>-loop/<NNN>-<UTC>.out|.err` に残す（autopilot-loop は既に `spec-autopilot-v<版>-loop/` に残している）。費用は最後の `result` の `total_cost_usd`。
   - **周ごと**: 子プロセスの周（`child-cycle.py`）は既に台帳の隣の `cruise-issue-<親>-children/` に記録がある——outer-loop はそこから、**ループを起こした後に起きた子**（起動時に在った記録を除く）の最後の `result` の `total_cost_usd` を合計に足す。サブエージェントの周の費用は親の起動の費用に含まれる（と読む。本物では測っていない——「守らない」）。
2. **費用が取れなかった起動**（出力に `result` が無い・最後の `result` に `total_cost_usd` が無い・数でない・負・有限でない）は **0 と数えず**、取れなかった数として数える（終わった子も同じ。走っている子は「走っている」として別に数え、合計に入れない）。
   - 止まった行（通知の本文）に毎回 **「費用: 取れた分の合計 $X・起動 N 回のうち取れなかった M 回」** を出す（子があれば子の内訳も）——上限を渡していないループでも。
   - **上限（`--max-total-usd`）を渡したループでは、取れなかった起動・終わった子が 1 つでもあれば、次を起こさずに止まる（12）**——上限を守れると言えないまま起こし続けない（黙って緑にしない）。走っている子では止めない（走りきってから数える）。
   - `claude` を起こせなかった起動（`OSError`）は費用を使っていないので数えない（そのまま 8 で止まる）。
3. **上限の判定**: 次を起こす直前に、取れた分の合計が上限 **以上** なら起こさずに止まる（11）。済んだ（`status` 5）・人待ち（3）の判定が先——最後の起動で済んだのに「上限」と言わない。autopilot は使用量の上限の待ちに入る前にも見る（上限を超えた後に何時間も待ってから止まらない）。
4. **合計は 1 回のループの起動の中だけ**——ループを起こし直すと 0 から（起動ごとの記録は残るので、利用者が合計できる）。台帳に書かない以上、前のループの分を数える出所が無い。「守らない」に書く。
5. `--max-total-usd` は正の有限の数だけ受ける（0・負・`nan`・`inf` は 2）。

**仕様の穴**: なし——上の 1・2 は Issue 本文が「計画で決める」と委ねたもの（台帳か隣の記録か・取れなかった起動の数え方）で、Issue の注意（0 と数えない・`progress` に混ぜない）の範囲で決めた。

## 受入基準（不変条件 × 経路）

経路はループの入口（引数・起動の前の判定・起動・起動の後の判定・止まる経路すべて・中断）と、費用の出所（親の起動の出力・子の記録）から数えた。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 合計が上限以上なら、ループは次を起こさずに止まり、理由と合計を出して通知する（outer-loop 11・autopilot 11） | 起動の前の判定・autopilot の上限の待ちの前・済んだ／人待ちとの順 | 試料: 合計がちょうど上限・超える・下回る・済んだ周と同時 |
| A2 | 費用が取れなかった起動は 0 として合計せず、数を止まった行と通知に出す | `result` が無い・`total_cost_usd` が無い・真偽値・文字列・負・NaN・巨大な整数・最後の `result` だけ欠ける | 試料 |
| A3 | 上限があれば、取れなかった起動・終わった子で次を起こさずに止まる（12）。上限が無ければ止めずに数を出す | 起動の前の判定 | 試料 |
| A4 | 子プロセスの周の費用を合計に入れる——ループの後に起きた子だけ。走っている子は合計に入れず止めない。終わったのに費用の無い子は取れなかった子 | 子の記録の走査・起動時に在った記録・走っている子・読めない記録 | 試料（偽の子の記録と、`claude` の名前で走る偽の子） |
| A5 | 費用の欄が `progress` の出力に入らない（台帳に書かない） | `ledger.py progress`・`autopilot-ledger.py progress` の出力・台帳のファイル | 試料で、費用のある起動の後の `progress` と台帳のファイルに費用の欄・値が無いことを見る（陽性対照: 費用は止まった行に出る） |
| A6 | 既存の止まる条件・引数・通知・中断・cwd・上限 0・追記が変わらない（outer-loop は出力の形を足しただけ） | 既存の試料 | 既存の試料が緑のまま（引数の期待は stream-json を足した形に直す） |
| A7 | `read_cost`・`cost_of` の写し（autopilot-loop）が outer-loop と一致する | 片方だけ直す | テストがソースを突き合わせる（陽性対照つき） |
| A8 | 変異テスト: 両テストとも「守る」の行数と変異の数が 1 対 1、終了コードの表と定数が一致 | — | テスト自身が数える |
| A9 | 文面の主張が事実である（docstring・公開ページ・SKILL.md・CLAUDE.md が書く止まる条件・終了コード・置き場所が実装と一致） | 複製 4 箇所（下の「複製の数」） | 関門が読んで突き合わせる |
| A10 | 版は dev-loop 1.109.0・spec-loop 0.89.0 で 3 種類そろう | 上げ忘れ | `check-plugin-versions.py` |
| X1 | 必須の掛け算: 受入基準を Verifier と /code-review の両方 × 1・2 パス目に渡す（4 つの受け渡し。2 パス目が「該当なし」なら 2 つ） | — | 再開点で記録 |

**未証明**（この環境では証明できない）:

- 本物の `claude -p` の `result` の `total_cost_usd` が、親が起こしたサブエージェント（Verifier・`/code-review` の fork）の分を含むか——本物の cruise を回さないと測れない（1 回数ドル）。偽の `claude` は決めた値を出すだけ。
- 本物の `claude -p` が使用量の上限・中断で終わったとき `result` に費用が載るか（上限は狙って作れない）。

**生成物**: `SKILL.md` の測定値（設計 §8.2 の生成ブロック）——dev-loop の `SKILL.md` は版の 2 行だけを触るので `skill-metrics.py --check` で見る。図の書き出しは無し。

**複製の数**: 止まる条件の列挙は outer-loop の docstring（正）・cruise の `SKILL.md` §6・公開ページ（cruise）・`CLAUDE.md` の 4 箇所、autopilot-loop の docstring（正）・公開ページ（autopilot）・`CLAUDE.md` の 3 箇所。分けない理由——どれも既に止まる条件を短く列挙しており、1 つだけ足さないと「この 3 つで止まる」と読める。足すのは 1 語ずつで、詳細は docstring を正とする。`read_cost`・`cost_of` は写し 2 つ（プラグインをまたいで import できない——autopilot-loop の docstring の理由）でテストが突き合わせる。

## 直す線

既定（出所: cruise の台帳の確かめた線。2026-11-15T02:04:18Z の利用者の確認）。

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/992-loop-total-cost`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-992`・起点 `902bc79`・base の参照 `origin/main`（解決した SHA `902bc79d136a73a5c9275a1aa85ddc00dc919318`）
- 割り目（手順 4・6）: 割らない（cruise の周）
- Verifier: 未
- /code-review: 未
- 交絡: 実験なし（まだ）

## 既知の限界・決着済みの論点

（関門の指摘と採否はここに 1 件 1 行で畳む）

## 経験の還元（手順 8）

- この周の起票: 0 件（起票の承認は不在のため訊いていない。周の途中の課題の振り分けで直すに入った行が無い）
