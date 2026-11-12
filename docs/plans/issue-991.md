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

## 実測（2026-11-12・Claude Code 2.1.322・`--model haiku`・cwd はリポジトリの外の空のディレクトリ・計約 $0.04）

試料と出力は scratchpad（`probe991/`）にあり、セッションと一緒に消える。数えたのは出力ファイルの `result` の行の実物。

| 回 | 形 | 結果 |
| --- | --- | --- |
| p0（陰性対照） | `--tools ""`・`--json-schema` なし | init の道具に `StructuredOutput` が無い。`result` 1 つ・`structured_output` は null |
| p1（陽性対照） | `--tools ""`・`--json-schema` あり | init の道具に `StructuredOutput` が在る（`--tools ""` でも足される）。`result` 1 つ・`structured_output` は形どおり |
| p2（周に近い形） | `--plugin-dir` のスキルを `/probe:probe 7` で起動・`--permission-mode default`・Bash と背景の `Agent`（`sleep 15`）・上限 0 | **`result` が 2 つ**。**1 つ目の `structured_output` は `outcome: stopped`（背景の体を待つ前に `StructuredOutput` を呼んだ）、最後は `outcome: done`**。init は 2 回。`killed` は 0 |
| p3（失敗の形） | Bash 2 回・`--max-budget-usd 0.001` | `result` は `error_max_budget_usd`・`is_error: true`・`structured_output` は null |
| p4（実装の後・A10） | `--tools ""`・`--json-schema` に `RESULT_SCHEMA` そのもの（型の配列を含む） | `result` 1 つ・`success`・$0.0066。`structured_output` は 10 欄で、`schema_problems` に当てて 0 件（再開した周で出力を読み直して確かめた。渡した形が `RESULT_SCHEMA` と一致することも） |

**言えること**: 道具を使い、スキルを入口にし、背景の体を待つ形でも、最後の `result` に `structured_output` が載る。**最初の `result` は早すぎる報告でありうる**——読むのは最後だけ（今の `status` の決まりと同じ）。予算切れでは `structured_output` が無い。

**確かめていないこと**: 実際の dev-loop の 1 周（関門 × 2 パス・`/code-review` の fork・数十分）で最後の `result` に載るか。形を渡したことで子の振る舞い（ターンの終え方）が変わるか。型の配列（`["integer","null"]`）を CLI の検証が受けるかは p4 で確かめた（受けた）。

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
| A10 | 本物の `claude -p` が `RESULT_SCHEMA` を受け、形どおりの `structured_output` を返す | 型の配列・enum | p4（haiku・道具なし）で確かめた——形どおり |
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
- 実装: 済み（`c2cb2cb9`）。`check-all.py` は 74 本中 73 本が通り、落ちた `check-plan-counts.py`（件数の行が無い）は行を足して単独で通した
- 関門: **1 パス目済み**（2026-11-12）。Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 1 件（計画ファイルの記録のずれ。実装の反証 0 件）／ `/code-review` high 指摘 10 件。採否は下の表——直す 4 件（R1〜R4）
- 1 パス目の指摘対応の起点: `c2cb2cb9`（1 パス目の関門に渡す成果物の HEAD。この後のコミットは計画ファイルだけ）
- 手順 4 の割り目: 訊いた（2026-11-12）——**「ここで割る」**。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 991` から手順 5（1 パス目の Verifier と `/code-review`）
- 手順 6 の 2 パス目の前の割り目: 訊いた（2026-11-12）——**「ここで割る」**。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 991` から、手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目。どちらにも受入基準・既知の限界・採否の表を渡し、2 パス目の差し込み（直した 4 件 R1〜R4・指摘対応の差分 `git diff c2cb2cb9 c30501f3`）を入れる。base は変わらず `9f16aebe`
- 関門 2 パス目: **済み**（2026-11-12）。Verifier（`dev-loop:dev-loop-verifier`・sonnet。委譲文 170 行を読んだと報告、`wc -l` と一致）反証 **0 件**・反証でない観察 2 件／ `/code-review` high 指摘 **8 件**。採否は下の「2 パス目の採否の表」——直す 1 件（C3）
- 2 パス目の指摘対応の起点（狭いパスの起点）: `3b8e283eaf70deaa4e1e7831be26f5492e06bd11`（指摘対応に入る前の HEAD。この行を書いたコミットはその子で、計画ファイルだけ）
- 2 パス目の指摘対応の終点: `517702da4586195c009159ae119fbc86f5f59580`（C3 を直したコミット。`check-all.py` 74/74、`test-child-cycle.py` は 3.12・3.14 とも緑で「守る」33 行 ↔ 変異 33 件）。著者の変異は 1 本（`RecursionError` を except から外す——赤）
- 狭いパス: **済み**（2026-11-12）。`git diff 3b8e283e 517702da` に Verifier（`dev-loop:dev-loop-verifier`・sonnet。170 行を読んだと報告、一致）。反証 **1 件**（N1。下の「狭いパスの採否の表」——人間が決める）。`test-child-cycle.py` は 3.12・3.14 とも緑、`git status --porcelain` は前後とも空
- 関門はここで打ち切り（3 パス目は無い）。この先は人間レビュー
- 再開する側への申し送り: 本物の `claude -p` の実測（p0〜p4）の出力は scratchpad にあり、セッションと一緒に消える——数は上の「実測」の表と `references/child-process.md` の「結果の形」が正。手元の dev-loop は 1.103.0（main の版は 1.104.0、この周で 1.105.0）
- 反証と差し戻し: 1 パス目の 2 関門で計 11 件。直すと決めた 4 件（R1〜R4）は手順 4 に差し戻して直した（`c30501f3`。`check-all.py` 74/74）。1 パス目の指摘対応の差分は 0 行でない（`git diff c2cb2cb9` に child-cycle.py・test-child-cycle.py）ので 2 パス目を回す。**残っているのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方**
- 交絡を潰した手順: R1〜R4 は直す前に本物の `status` を一時リポジトリの記録に当てて rc=1/0 を見（陽性）、直した後に同じ試料で rc=3 を見た。p0（陰性対照）と p1（陽性対照）で、`structured_output` が `--json-schema` によって出ることを分けた。p2 は「早い 1 つ目の result」と「最後の result」を分けて数えた。観測窓は各 1 回・haiku・小さな課題

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 既定で形を渡すか | 渡す（`--no-structured` で外せる） | p2 で、道具と背景の体を使う形でも最後の result に載った。子で回すこと自体が任意 |
| autopilot-loop に取り込むか | 取り込まない | 上の「autopilot-loop を取り込まない理由」 |
| 子の申告（`head_sha` など）を `status` が `gh` で確かめるか | 確かめない | `status` は `gh` を呼ばない。実物で確かめるのは親（`references/child-process.md` の「回し方」の 5） |

### 1 パス目の採否の表（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V-F1 | 計画の実測の表に p4 が無く、`child-process.md`（5 回・RESULT_SCHEMA を CLI が受けた）と食い違う | 示せる——旧セッションの scratchpad の `p4.jsonl` を読み直し、渡した形が `RESULT_SCHEMA` と一致、最後の `result` は `success`・`structured_output` を `schema_problems` に当てて 0 件 | 無し（計画ファイルは成果物でない） | 計画の表を直した（成果物は正しかった） |
| R1 | 要約の行の `len(needs_user)` が配列でない値で落ち、rc=1（走っている）になる | 示せる——`needs_user=5` の記録で本物の `status` が rc=1・TypeError | A4 | 直す |
| R2 | 型を縛らない記録の形で、オブジェクトでない出力が `claimed_problems` で落ちる | 示せる——形 `{}`・出力が文字列で rc=1・AttributeError | A4 | 直す |
| R3 | 記録の形の語の値が壊れていると検査器が落ちる | 示せる——`type` が dict・`required` が数で rc=1 | A4 | 直す |
| R4 | `structured` が `{}`・文字列などのとき「渡していない」と読み、検査せずに 0 | 示せる——`outcome=stopped` の子で rc=0 | A4・A6 | 直す |
| R5 | `claimed_problems` の欄の名前が本体に固定で、記録の形から読まない | 示せない（欄の名前を変えた将来の版でだけ起きる） | — | 残課題 |
| R6 | `pr` があって `head_sha` が null でも 0 | 示せる | 無し（A5 は欄を名指ししていて、`head_sha` は入っていない。実物は親が `gh` で確かめる） | 残課題 |
| R7 | `enum` の照合で `True` が `1` に当たる | 示せない（`RESULT_SCHEMA` に整数の enum は無い） | — | 残課題 |
| R8 | A8 のテストの ` -p ` を含まない検査は `is_running` を壊せる形を当てていない | 示せない（`is_running` は正しく動く） | 無し | 残課題 |
| R9 | 記録に形が 2 度（`command` と `structured.schema`）入る | 示せない（ずれる経路は手で直すときだけ） | 無し | 残課題 |
| R10 | 計画と `child-process.md` の食い違い（V-F1 と同じ） | V-F1 と同じ | 無し | V-F1 で直した |

### 2 パス目の採否の表（直す線: 既定）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V2-O1 | `claimed_problems` の中の例外が「記録の形が読めない」と出て原因を取り違える（Verifier の観察） | 示せない（ふつうは届かない経路） | 無し（3 は返る） | 残課題 |
| V2-O2 | docstring の「どんな値でも落ちずに」が配列でない `permission_denials`・dict でない `subagent_stats` を守らない（Verifier の観察） | 示せない（本物の CLI は出さない形。この周より前からの挙動） | 無し | 残課題 |
| C1 | CI の無いリポジトリでは子が `ci: none` しか申告できず、毎周 3 になる | 示せない（この周で CI の無いリポジトリで子を回していない） | 無し（A5 が `pass` でなければ 3 と決めている。設計の問い） | 残課題 |
| C2 | 出力がオブジェクトでないとき、要約の行が「structured_output が無い（str）」と言う | 示せる（レビューの probe） | 無し（3 は返る。文言だけ） | 残課題 |
| C3 | 深く入れ子の記録の形・出力で `schema_problems` の RecursionError が漏れ、rc=1（走っている）になる | 示せる——`scratchpad/c3.py`: 深さ 50 は要確認を返し（陽性）、深さ 2000 は `RecursionError escaped`。`json.loads` は 3.12・3.14 とも深さ 5000 まで読める（`c3c.py`）ので、漏れるのは検査器 | A4（「落ちずに 3」） | 直す |
| C4 | `additionalProperties` がサブスキーマのとき無視して 0 | 示せない（記録の形を書くのは起動口で、`False` しか書かない。将来の版でだけ起きる——R5 と同じ） | 無し | 残課題 |
| C5 | 記録の `enum` が文字列だと部分文字列で当たる | 示せない（壊した記録でだけ起き、0 にはならない） | 無し | 残課題 |
| C6 | `pr: 0`・負数・空の `head_sha` で 0 | 示せない（子がそう申告した実物は無い。R6 と同じ） | 無し（A5 は `pr` が null を名指し） | 残課題 |
| C7 | 文字列の `needs_user` の件数を文字数で出す | 示せる（レビューの probe） | 無し（3 は返る。文言だけ） | 残課題 |
| C8 | `integer` に float を許す変異が素通りする（試料に float が無い） | 示せる（レビューの変異） | 無し（本体は float を拒む。試料の穴） | 残課題 |

### 狭いパスの採否の表

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | `summarize`（`except ValueError` だけ）と `read_meta` が `json.loads` の RecursionError を捕まえない。Python 3.12 では深さ 10 万段の出力の行で漏れうる（3.14 は 100 万段）。C3 で足した docstring の「`json.loads` は深さ 5000 でも読める」は版に依存する | 一部（`summarize` の例外までは Verifier が実測。`status` の rc は未実測） | A4（「落ちずに 3」）——ただし本物の `claude` の出力では起きにくい | **人間が決めた: この PR で直す**（2026-11-12、手順 7 の前の `AskUserQuestion` の回答）。`read_meta` と `summarize` でも `RecursionError` を捕まえ（記録は読めない＝4、出力の行は壊れた行＝`result` が無ければ 3）、docstring の「5000 でも読める」を版に依存しない書き方に直した。試料は 100 万段（3.12・3.14 とも越える）、変異「json.loads の再帰の上限を捕まえない」は両方の版で赤。関門の当て直しはしていない（2 パスで打ち切り。テストと `check-all.py` だけ） |

## 起票

- この周の起票: 0 件（手順 8 で C1・C2・C7・C8 を候補として訊き、利用者が「起票しない」を選んだ。2026-11-12）
