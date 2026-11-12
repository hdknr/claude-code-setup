# Issue #991 — cruise: 子の周の結果を --json-schema の構造化出力で受け取る

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/child-cycle.py` — 結果の形（`RESULT_SCHEMA`）を 1 つだけ置き、`launch` が `--json-schema` で渡して記録に残し、`status` が最後の `result` の `structured_output` を記録の形で検査する（`--no-structured` で外せる）
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md` — 最後の報告を構造化出力の欄で返すことを書く（欄の名前は本体の形と同じ。テストが突き合わせる）
- `plugins/dev-loop/skills/cruise/references/child-process.md` — 構造化出力の実測（2026-11-12）と、`status` の 0 の意味の変化・確かめていないこと
- `scripts/test-child-cycle.py` — 試料・変異・委譲文との突き合わせ
- `.claude-plugin/marketplace.json` — dev-loop の版（1.104.0 → 1.105.0）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 同上
- `plugins/dev-loop/skills/` — 各 `SKILL.md` の版の 2 行だけ
- `docs/plans/issue-991.md` — この計画

触らない:

- `plugins/spec-loop/scripts/autopilot-loop.py` — 調べた結果、取り込まない（下の「autopilot-loop を取り込まない理由」）
- 子の既定化（既定はサブエージェントのまま。`references/child-process.md` の「確かめた範囲」の 1・3）
- `outer-loop.py`・台帳の書式・費用の上限（#992）

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`.claude/dev-loop.md`）。docs/ のサイトの中身は計画ファイルだけ。

## 実測（2026-11-12・Claude Code 2.1.322・`--model haiku`・cwd はリポジトリの外の空のディレクトリ・計約 $0.03）

試料と出力は scratchpad（`probe991/`）にあり、セッションと一緒に消える。数えたのは出力ファイルの `result` の行の実物。

| 回 | 形 | 結果 |
| --- | --- | --- |
| p0（陰性対照） | `--tools ""`・`--json-schema` なし | init の道具に `StructuredOutput` が無い。`result` 1 つ・`structured_output` は null |
| p1（陽性対照） | `--tools ""`・`--json-schema` あり | init の道具に `StructuredOutput` が在る（`--tools ""` でも足される）。`result` 1 つ・`structured_output` は形どおり |
| p2（周に近い形） | `--plugin-dir` のスキルを `/probe:probe 7` で起動・`--permission-mode default`・Bash と背景の `Agent`（`sleep 15`）・上限 0 | **`result` が 2 つ**。**1 つ目の `structured_output` は `outcome: stopped`（背景の体を待つ前に `StructuredOutput` を呼んだ）、最後は `outcome: done`**。init は 2 回。`killed` は 0 |
| p3（失敗の形） | Bash 2 回・`--max-budget-usd 0.001` | `result` は `error_max_budget_usd`・`is_error: true`・`structured_output` は null |

**言えること**: 道具を使い、スキルを入口にし、背景の体を待つ形でも、最後の `result` に `structured_output` が載る。**最初の `result` は早すぎる報告でありうる**——読むのは最後だけ（今の `status` の決まりと同じ）。予算切れでは `structured_output` が無い。

**確かめていないこと**: 実際の dev-loop の 1 周（関門 × 2 パス・`/code-review` の fork・数十分）で最後の `result` に載るか。形を渡したことで子の振る舞い（ターンの終え方）が変わるか。型の配列（`["integer","null"]`）を CLI の検証が受けるか——実装の後に p4 で確かめる。

## 設計

- **形**: `RESULT_SCHEMA`（`child-cycle.py` に 1 つだけ）。欄は `outcome`（`pr_ready`／`stopped`）・`stop_reason`・`pr`・`head_sha`・`ci`（`pass`／`fail`／`pending`／`none`）・`skill_path`・`skill_lines`・`denied_commands`・`needs_user`・`report`。全部必須・余分な欄は不可。
- **launch**: 既定で `--json-schema <形>` を渡し、記録の `.json` に `structured: {"schema": 形}` を残す。`--no-structured` なら渡さず、記録に `structured: null`。
- **status**: 記録に形があれば、最後の `result` の `structured_output` を記録の形で検査する（標準ライブラリだけの小さな検査器。使う語は `type`・`enum`・`properties`・`required`・`additionalProperties`・`items`）。無い・形に合わない → 要確認（3）。形に合えば、子の申告（`pr_ready` でない・`ci` が `pass` でない・`pr` が無い・`needs_user`・`denied_commands` が空でない）も要確認（3）。要約に欄を 1 行で出す。記録に形が無ければ（前の版の起動口・`--no-structured`）検査しない。
- **0 の意味**: 形を渡した子では「要確認の印が無く、子が PR を作って CI が通ったと申告した」。**それでも実物（`gh pr view`・`gh pr checks`）で確かめる**のは変わらない。

### autopilot-loop を取り込まない理由

`autopilot-loop.py` は起動ごとの前進を台帳の `progress` で決め、出力から読むのは利用上限の印だけである（子の報告の文を判定に使っていない）。構造化した報告を受け取っても判定に使う先が無い。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 既定の launch は子に `--json-schema` で `RESULT_SCHEMA` を渡し、記録に形を残す | 引数の組み立て・記録の書き出し | 偽の `claude` が受けた引数と記録の `.json` を試料で見る |
| A2 | `--no-structured` なら渡さず、記録は `structured: null` | 同上 | 試料 |
| A3 | 形を渡した子の `status` は最後の `result` の `structured_output` だけを読む | result が 1 つ・2 つ以上・最初だけ `pr_ready` で最後が `stopped`・その逆 | 試料（p2 の形） |
| A4 | `structured_output` が無い・オブジェクトでない・形に合わない（欄の欠け・型・enum・余分な欄・配列の要素の型・真偽値を整数と読まない）なら 3 で、0 にならない | 検査器の各語 | 試料 7 つ以上 |
| A5 | 形に合っても、子の申告が済んでいなければ 3（`stopped`・`ci` が `pass` でない・`pr` が null・`needs_user`・`denied_commands`） | 欄ごと | 試料 |
| A6 | 形を渡していない記録（前の版の起動口の記録・`--no-structured`）は形を検査せず、今までどおり | `structured` の鍵が無い記録・null | 既存の試料（`plant` は鍵を持たない）がそのまま通る |
| A7 | 検査は記録に残した形で行う（本体の形が後で変わっても古い記録を新しい形で判じない） | 本体の定数を使う | 古い形を記録に持つ試料 |
| A8 | 走っているかの判定（`-p` の直後の引数）は形を足しても変わらない | 形の JSON を `ps` が空白で割る | 形の文字列に ` -p ` が無いことと、走っている子の `status` が 1 であることを試料で見る |
| A9 | 委譲文が形の欄を全部名指しする | 欄の足し忘れ | テストが `RESULT_SCHEMA` の欄名と委譲文を突き合わせる |
| A10 | 本物の `claude -p` が `RESULT_SCHEMA` を受け、形どおりの `structured_output` を返す | 型の配列・enum | 実装の後に p4（haiku・道具なし）で確かめる |
| A11 | 変異テスト: 「守る」の行数と変異の数が 1 対 1 | — | テスト自身が数える |
| A12 | 版は 3 種類で 1.105.0 | 上げ忘れ | `check-plugin-versions.py` |
| X1 | 必須の掛け算: 受入基準を Verifier と /code-review の両方 × 1・2 パス目に渡す | — | 再開点で記録 |

**未証明**: 実際の dev-loop の 1 周（関門 × 2 パス・`/code-review` の fork・数十分）で、最後の `result` に `structured_output` が載ること。1 周は数ドル〜$10 で、cruise の親でしか回せない（`references/child-process.md` の「利用者が測る手順」）——測る手順に数えるものを足し、次に子で回す周で確かめる。

**生成物**: `SKILL.md` の測定値（設計 §8.2 の生成ブロック）——dev-loop の SKILL.md は版の 2 行だけを触るので `skill-metrics.py --check` で見る。図の書き出しは無し。

**複製の数**: 欄の一覧は `RESULT_SCHEMA`（正）と委譲文の 2 箇所。分けない理由——子が読むのは委譲文で、形の `description` だけでは報告の中身を伝えきれない。テスト（A9）が突き合わせる。`references/child-process.md` は欄を列挙せず本体を指す。

## 直す線

既定（手順 3 の回答、2026-11-12）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/991-child-json-schema`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-991`・起点 `9f16aebe`・base の参照 `origin/main`・base の SHA `9f16aebe2e4a15793f722082a26e6b0d6e4cc008`
- 関門: まだ当てていない
- 反証と差し戻し: なし
- 交絡を潰した手順: p0（陰性対照）と p1（陽性対照）で、`structured_output` が `--json-schema` によって出ることを分けた。p2 は「早い 1 つ目の result」と「最後の result」を分けて数えた。観測窓は各 1 回・haiku・小さな課題

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 既定で形を渡すか | 渡す（`--no-structured` で外せる） | p2 で、道具と背景の体を使う形でも最後の result に載った。子で回すこと自体が任意 |
| autopilot-loop に取り込むか | 取り込まない | 上の「autopilot-loop を取り込まない理由」 |
| 子の申告（`head_sha` など）を `status` が `gh` で確かめるか | 確かめない | `status` は `gh` を呼ばない。実物で確かめるのは親（`references/child-process.md` の「回し方」の 5） |

## 起票

- この周の起票: 0 件（起票の候補なし）
