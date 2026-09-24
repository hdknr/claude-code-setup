# #168 — Verifier が残したバックグラウンドジョブで報告が届かない（委譲文の禁止と、止まったときの診断）

## 周の在り処

- ブランチ: `issue/168-verifier-background-jobs`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-168`
- 起点: `e686445`（Merge pull request #167）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD` から解決）→ `e686445280f40ff3e7a7a839cecb85ede9d1f022`
- 入場: `prepare-worktree.sh` で作成 → `EnterWorktree(path)`。**`ExitWorktree` は畳まない**（path で入ったため）

## 0. 着手前に確かめたこと（Issue コメントの「実装の最初に確かめる」）

実物の transcript（`~/.claude/projects/*/*/subagents/agent-*.jsonl`、`backgroundTaskId` を含む 65 ファイル）で数えた。

| 観測 | 結果 |
| --- | --- |
| Bash の結果に `toolUseResult.backgroundTaskId` が付く形 | 入力に `run_in_background` あり: 11 件 ／ **入力に無い（自動で回った）: 88 件** ／ 前景: 3735 件（ID なし） |
| 自動で回った場合の印 | **`timedOutAfterMs: 120000` が併せて付く**。結果の本文は `Command did not complete within its 120s timeout and was moved to the background (ID: …)` |
| ジョブの完了は記録されるか | **`<task-notification>` を含む `attachment`（`queued_command`）として、`<task-id>` と `<status>` 付きで記録される**。開始 99 件のうち **70 件に完了の記録があり、29 件には無い** |
| 事故の実物 | `…issue-10856-costcustomer-sheet/80069888-…/subagents/agent-averifier-pass2-939bb468f553f7e1.jsonl` の `find / …` が **自動（`timedOutAfterMs`）・完了の記録なし**。最後の記録は `end_turn` の text |

**完了の記録が無い 29 件が「いまも走っている」かは分からない**——記録されない理由を特定していない。
だからスクリプトは**「完了の記録が無い」までしか言わない**（§6）。

**Issue 本文の時刻（26 分で書き終え 97 分後に届いた）は、上の実物ではなく別の実物と一致した**——
`…issue-10974/6c4131ab-…/subagents/agent-ae3210dfe0bcdbb88.jsonl`（全 97 分）。
スクリプトを当てると: **自動で回った 5 本**（`until ! kill -0` 系 4 本は +24 分で完了、
残る 1 本は **+96:13 に完了**）、**`end_turn` の text が +25:41（3751 文字）と +97:00（48 文字 = 引き渡しの定型文）**。
**+25:41 のあと、ジョブの完了通知（user の SYSTEM NOTIFICATION）で子が起こされ、
さらに道具を呼んでから +97 分に引き渡した。** → **「最後の text」で判定すると書き終えた時刻が消える**ので、
判定を **`end_turn` の text** に変えた（不変条件 C）。

| 追加の実測（全 transcript の自動で回った Bash） | 結果 |
| --- | --- |
| `timeout` 引数なし | 回った時点 120000 ms: 240 件（**600000 ms: 2 件**——既定が環境で違う） |
| `timeout` を明示（≦ 600000） | **明示した値で回る**（300000 → 300000 など） |
| `timeout` を 600000 より大きく明示 | **600000 で回る**（1800000 → 600000: 8 件 など）——**上限は 10 分** |

→ 委譲文は「既定は多くの環境で 120 秒」「上限は 10 分」と書いた。

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/summarize-subagent.py` — 新規。サブエージェント 1 体分の transcript を集計する
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 5「Verifier が報告を返さなかったら」／版のバナー
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「実環境を壊さないこと」に 4 つ・「報告の形」に経過時間
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 「実環境を壊さないこと」に 4 つ
- `plugins/dev-loop/agents/dev-loop-verifier.md` — 「守ること」に 4 つ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版 1.32.1 → 1.33.0
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — `skill-metrics.py` の生成ブロックだけ（手で書かない）
- `scripts/test-summarize-subagent.py` — 新規。回帰テスト（変異テストを含む）
- `scripts/check-all.py` — `TESTS` に登録
- `.github/workflows/plugins.yml` — テストのステップを足す
- `CLAUDE.md` — `scripts/` 一覧に 1 行
- `docs/plans/issue-168.md` — この計画ファイル

触らない:

- `plugins/dev-loop/README.md`・公開ページの本文 — 手順の列挙を持たない（指すだけ）
- `plugins/dev-loop/skills/dev-loop/references/` — 条件つきの節を出す先だが、今回の追加は手順 5 の既存項の中に収まる
- `SKILL.md` の frontmatter と 2 つの JSON の `description` — 能力の要約は変わらない
- `diagrams/` — 図は触らない

**複製の数**: 4 つの禁止は **3 箇所**（`verifier.md` / `review-handoff.md` / agent 定義）に同じ趣旨で入る。
**分けない理由**: 3 つとも**単体で子に届く文面**で、指し先を書いても子はそれを開かない
（既存の「実環境を壊さないこと」も 3 箇所に同じ形で置いてある）。**`SKILL.md` には禁止を再掲しない**
——手順 5 の追加は診断のほうだけで、禁止は「`prompts/verifier.md` を正とする」で指す。

## 2. 乗るデプロイ経路

main へのマージ → GitHub Pages の自動デプロイ（`docs/plugins/dev-loop-design.md` の生成ブロックが変わる）。
プラグインはマーケットプレイス経由で利用者側に届く（`plugin update` で記録が進む）。

## 3. verify の受入基準

### 3.1 不変条件

| # | 不変条件 |
| --- | --- |
| A | スクリプトは**前景 / 指定してバックグラウンド / 自動でバックグラウンド**の 3 つを判別して出す。判定は**結果の `backgroundTaskId`** で行い、指定か自動かは入力の `run_in_background` で分ける |
| B | バックグラウンドに回った各呼び出しについて、**完了の記録（`<task-notification>` の `<task-id>`）の有無**を突き合わせて出す。**記録が無いものを「完了」と数えない**。**記録が無いことを「まだ走っている」とも言わない** |
| C | 「報告を書き終えた」と言うのは、**`stop_reason` が `end_turn` の assistant text がある**ときだけ（途中の前置きの text でも、最後の text でも判定しない） |
| D | ID から探して 2 件以上当たったら**選ばずに並べて非ゼロ**で終わる。0 件・読めない入力も非ゼロ |
| E | 出力は**集計だけ**で、ツールの生出力を貼らない（コマンドは短く切る）——親の文脈に積まないための道具なので |
| F | テストは実環境（`~/.claude`）を読まない（アサートで担保）。変異テストは docstring の「守る」と 1 対 1 |
| G | 3 つの委譲文面に 4 つの禁止（ディスク全体の走査・バックグラウンドのジョブ・頼まれていない全体スイート・コンテナ／サービスの起動）と、それぞれの代わりにすることが入っている |
| H | `SKILL.md` 手順 5 に、「background work 待ち」で止まったときは**再実行の前にスクリプトで集計する**が入り、**既存の「区別できないなら再実行」は条件付きで残る**（消さない・緩めない） |
| I | 版が 3 箇所で 1.33.0 に揃い、生成ブロックが最新（`skill-metrics.py --check`）、`check-all.py` が全部緑 |
| J | `SKILL.md` からスクリプトへの指し先が実在する（`check-skill-pointers.py`） |
| K | 書いた事実（自動で回ると `backgroundTaskId` と `timedOutAfterMs` が付く・完了は `<task-notification>` で記録される・`timeout` の上限は 10 分・既定は多くの環境で 120 秒・+25 分の報告が +96 分まで渡らなかった）が、実物の transcript と一致する |

### 3.2 これを破りうる経路

| 不変条件 | 経路 | どう守るか |
| --- | --- | --- |
| A | 入力フラグだけで判定する実装 | 合成 transcript の「自動」ケース ＋ 変異 |
| A | `timedOutAfterMs` が無いのに ID が付く形（手で `run_in_background` を指定しない別の経路） | 「自動」の判定は「ID あり かつ 指定なし」で行い、`timedOutAfterMs` は補助の表示に留める |
| A | Bash 以外の道具（`Agent` の background など）が `backgroundTaskId` を返す | 道具名に依らず `toolUseResult.backgroundTaskId` を見る |
| B | 同じ task-id の通知が 2 回ある（実物で観測） | 最初の 1 件で足りる（有無を見る） |
| B | 通知の本文が JSON 文字列の中にエスケープされている | 行の生テキストに正規表現を当てる／パースした文字列に当てる——両方で拾えることをテストで見る |
| C | 途中の text（ツールの前置き）を報告と読む | 合成で「text → tool_use → 終わり」を作り、書き終わっていないと出ることを見る ＋ 変異 |
| D | ID 解決で先頭 1 件を選ぶ | 合成の projects ディレクトリに同じ ID を 2 つ置く ＋ 変異 |
| E | コマンド全文を出す | 長いコマンドを合成して、出力の行長を見る |
| F | 既定の `~/.claude/projects` をテストが読む | `--projects-dir` を必ず渡し、tmp の中であることをアサート |
| G | 3 箇所のうち 1 箇所だけ直す | 3 ファイルを grep で突き合わせる（関門にも当てさせる） |
| H | 「区別できない」を削って「集計すれば区別できる」に置き換える（基準を緩める） | 差分で既存行が残っていることを見る |
| I | 版の 3 箇所・生成ブロック・CI 登録 | `check-all.py` |
| K | 実物と合わない記述 | 実物の transcript 1 件にスクリプトを当てる（陽性対照） |

### 3.3 この環境では証明できないもの（未証明）

- **禁止を足したあとで、Verifier が実際にジョブを残さなくなるか。** CI はモデルを起こせないし、1 回走らせても母集団にならない。**散文の禁止は強めても破られた前例がある**ので、診断（スクリプト）を同じ周に入れた。人間レビューに回す。

### 3.4 BLOCKED

なし。

### 3.5 生成物の鮮度

該当あり: `docs/plugins/dev-loop-design.md` の §8.2 生成ブロック（`skill-metrics.py`）。`--check` で確かめる。
図（`diagrams/`）は触らないので対象外。

### 3.6 必須要件の掛け算

受入基準 × {Verifier, `/code-review`} × {1 パス目, 2 パス目} = 4 つの受け渡し。
既知の限界（§6）も同じ 4 つに渡す。

### 3.7 陽性対照

- 事故の実物（§0 のパス）で、`find /` の行が「自動・完了の記録なし」と出ること。
- 完了の記録がある実物（`…issue-10974/176e9ffb-…/subagents/agent-a01d62bfcf46c9eff.jsonl`）で「完了（completed）」と出ること。

## 4. 未解決の判断

- なし（Issue コメントの計画に沿う。コンテナの項は「ネットワーク越しのプロセス」を「常駐するサービス」に言い換えた——**`gh` の読み取りは委譲文が許しているので、「ネットワーク越し」と書くと衝突する**）。

## 5. 関門の進捗（再開点）

- 実装: 完了（手順 4）。`check-all.py` 29/29 緑（ローカル）
- 陽性対照: §3.7 の 2 件 ＋ `ae3210…`（§0）で期待どおりに出ることを確認済み
- Verifier: 未
- `/code-review`: 未
- 反証・差し戻し: なし
- 交絡を潰した手順: §0 の実測は陽性側（自動で回った 88 件）と陰性側（前景 3735 件に ID なし）の両方を取った。
  `timeout` の上限は「明示した値で回る」陽性側（≦ 600000）と「上限で頭打ち」側の両方を見た
- 割り目（手順 4）: 未回答

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 完了の記録が無いジョブを「走っている」と言うか | 言わない | 記録が無い 29 件の理由を特定していない |
| `timedOutAfterMs` で自動を判定するか | しない（表示だけ） | 判定を 2 つの印に依らせると、片方が消えたとき黙って落ちる。「ID あり・指定なし」で決まる |
| 4 つの禁止を `SKILL.md` にも書くか | 書かない | 子に届くのは委譲文面と agent 定義。`SKILL.md` は指す |
| 子が自分のジョブを止められるか | 主張しない | Verifier の道具（Read/Grep/Glob/Bash）でジョブを列挙・停止する手段を確かめていない。だから禁止は「残さない（起こさない）」側に置く |
| Issue 本文の時刻（26 分／97 分） | `ae3210…` と一致した | §0 |
| `SKILL.md` の「外から区別できない」を書き換えたか | 「親の画面からは区別できない」に絞り、「区別できないなら再実行」は残した。**集計で区別できる場合だけ再実行しない** | Issue コメントの方針どおり。基準を緩めていない（区別できないときの規定は不変） |
| 「ネットワーク越しのプロセス」を禁じるか | 「コンテナ・常駐するサービス」に言い換えた | 委譲文は `gh` の読み取りを許しており、「ネットワーク越し」だと衝突する |
