# Issue #847 — spec-loop: claude -p では spec-review・feasibility の判定役を前景で呼ぶ

不在の周（出所: `/dev-loop:cruise 856 --absent` の起動・2026-11-05T00:54Z）。cruise の子として回す。利用者には訊かない
（`AskUserQuestion` を使わない。割り目も訊かない）。

- 直す線: **既定**（出所: cruise の確かめた線——利用者の確認（起動時・2026-11-05T00:54:19Z、配布を見せて確かめた））
- 台帳の確かめた線: 仕様の穴 = 推奨で決めて起票、直す線 = 既定、マージ = 関門を通ればマージ（マージは親）、周の途中の課題 = 台帳に足して直す。`マージ前の判断` の線は無い。
- 版の上げ方: **minor・spec-loop**（0.52.0 → 0.53.0。手順に決まりを足す。マージの直前に main が進んでいれば、main の先端の版から minor を 1 つ上げ直す——cruise の `references/parallel.md` の「版とマージの順」）

## 変更範囲

触る:
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 手順 3 に「`claude -p` では判定役を前景で呼ぶ」と理由。版の 2 行
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 手順 6 に「`claude -p` では検証役を前景で呼ぶ」と理由。版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（req-loop・proposal・scaffold）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-847.md` — この計画

触らない:
- `plugins/dev-loop/`（#633 の書き方の原本。写しを作らず、指すだけ）
- `plugins/spec-loop/agents/`（判定役の定義。起動の仕方は呼ぶ側の決まり）
- `docs/plugins/spec-loop.md`（判定役の起動の仕方を載せていない——`grep` で確かめた）
- 起動の形（`-p` かどうか）を確かめる手順（#633 と同じく決めない。下の「既知の限界」）

## デプロイ経路

main へのマージでプラグインの配布（spec-loop の版）。公開サイトは変わらない（`docs/` の成果物の変更なし。計画ファイルは公開サイトに載るが本文は無関係）。

## 受入基準（不変条件 × 経路）

同じことを述べている箇所の数: **2**（spec-review 手順 3・feasibility 手順 6）。書き方の元は cruise の `SKILL.md` §4 の 2（#633）で、そこは指すだけ。
分けない理由: Issue が両方を 1 つの決まりとして求めている。

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A | spec-review に「`claude -p`（非対話）では判定役を前景で呼ぶ」と、理由（ターンが閉じると背景の体が上限の時間で止められる）が書かれている | 手順 3 の 1 回目だけに掛かり、2 回目のレビュー（手順 5）・狭いパス（手順 5 の 2）の判定役に掛からない／理由が無い／理由が事実と違う（#633 の実測と食い違う） | 本文を読む。理由は cruise `SKILL.md` §4 の 2・`references/child-process.md` の実測（`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`）と照合 |
| B | feasibility に「`claude -p` では検証役を前景で呼ぶ」と理由が書かれている | 手順 6 の 1 回目だけで再実行・2 回目の検証に掛からない／理由が無い | 本文を読む |
| C | 対話のセッションでの起動の仕方（spec-review の 3 体を同時に起動する）は変わっていない | 既存の「3 体を、バックグラウンドで同時に起動する」の行を書き換える・消す／新しい決まりが条件なしに読める（対話でも前景と読める） | `git diff` で既存行が残ること、新しい行が `claude -p` の条件つきであること |
| D | 版が 3 種類で揃い、main の先端から minor を 1 つ上げた値 | 揃え漏れ・SKILL.md 5 本のどれかの漏れ | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| E | 歯止めが全部緑（PR 側の CI も） | 指し先（`../../` の外・存在しない節）・太字の flanking・件数の重複 | `check-all.py`（run-serial 越し）と `gh pr checks` |

掛け算: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す（2 パス目が該当なしなら初回の 2 つ）。

**未証明**: 「前景で呼べば `claude -p` でも判定役の報告が欠けない」ことは、この周では `claude -p` で spec-review を実走させて測らない
（課金・実データの正本リポジトリが要る）。根拠は dev-loop の #633（cruise の子）の実測で、判定役に当てて測ってはいない。人間のレビューに回す。
**BLOCKED**: 無し。

生成物: **該当なし**——図・`SKILL.md` の測定値の生成ブロック（dev-loop の設計 §8.2 は dev-loop の `SKILL.md` だけを測る）に触れない。`skill-metrics.py --check` は check-all に入っている。

## 未解決の判断・確認待ち

- 無し。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/847-spec-loop-foreground-checkers`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-847`、
  起点 `f447c55b`、base は `origin/main`（refs/remotes/origin/HEAD）を解決した `f447c55b581218144cbeef1ff62954ec533c7d51`
- 割り目（手順 4）: 割らない（cruise の周）——このまま続ける
- 1 パス目の指摘対応の起点: `25d8383d`（1 パス目の関門に渡した時点の HEAD）
- Verifier 1 パス目: 通した（sonnet・`dev-loop:dev-loop-verifier`）。反証 0 件（確認 2 件——R1・R2 と同じ論点）
- /code-review 1 パス目: 通した（high）。指摘 6 件、直す 2 件（R4・R5）・残課題 4 件。手順 4 への差し戻しなし
- 割り目（2 パス目の前）: 割らない（cruise の周）——このまま続ける
- Verifier 2 パス目: 未
- /code-review 2 パス目: 未
- 歯止め: `check-all.py`（run-serial 越し）1 回目 59/60（`check-plan-counts.py` が件数の行なしで落ちた——行を足した）、2 回目 60/60 緑
- 交絡: 実験なし

## 既知の限界・決着済みの論点

- **起動の形（`-p` かどうか）を確かめる手順は決めない**——#633（cruise `SKILL.md` §4 の 2）と同じ。Issue は「`claude -p` で動いているときは」と条件だけを求めている。
  決めるなら別の周（振り分け: 記録だけ——受入基準を破らず、利用者に見える誤りでも後退でもない）。

### 関門の指摘の採否（1 パス目）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | （CR・Verifier 確認 1）`-p` で「1 体ずつ」と直列を指定。理由は直列を要求せず、#633 は直列にしていない | 示せない（遅くなるのは推定。報告は欠けない） | 無し | 残課題 |
| R2 | （CR・Verifier 確認 2 の近縁）`-p` かを判別できないと決まりが効かない。モードに依らない「全部の報告が返るまでターンを閉じない」なら両方で効く | 示せない（`-p` の実走をしていない） | 無し（C は対話の起動を変えないことを求める） | 残課題（既知の限界の決着の理由を補う） |
| R3 | 前景を選べない環境（サブエージェントの中の `Agent` など）での代わりが無い | 示せない（spec-review を体の中から回した実物は無い） | 無し | 残課題 |
| R4 | 理由が「ターンが閉じると止められる」と読め、実測（上限まで待ってから止める。`child-process.md` の 20 秒の背景の体は待たれた）より強い | 示せる——`plugins/dev-loop/skills/cruise/references/child-process.md:106`（「10m after the last turn」）と本文の旧文言 | A（理由が事実と違う） | 直す（spec-review・feasibility とも「上限の時間を過ぎて走っていると止められる」に） |
| R5 | spec-review で、報告を返さなかった判定役の再実行（「守ること」）に決まりが掛かると書いていない（feasibility は書いている） | 示せる——`spec-review/SKILL.md:42`（再実行）と新しい段落が 2 回目・狭いパスだけを名指し | A（2 回目・狭いパス以外の起動に掛からない） | 直す（再実行を名指し） |
| R6 | 理由の文が cruise と spec-loop 2 本の 3 か所に写しで在る。spec-loop の `references/` に 1 つ置いて指すべき | 示せない（いまは食い違っていない） | 無し | 残課題 |

## 起票（手順 8）

- この周の起票: 0 件（不在の cruise の周。振り分けで直すとした周の途中の課題・確認の Issue は無い）
