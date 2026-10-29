# Issue #491 — cruise: 周を `claude -p` の子プロセスで回し、親の文脈と寿命から切り離す

cruise の各周を、親のサブエージェントではなく `claude -p` の子プロセスで回せるようにする。
子はメインの作業ツリーを cwd にして**親から切り離して**起動し（新しいセッション。親の `/clear`・終了の道連れにならない）、
出力（`--output-format stream-json`）をメインの作業ツリーの `.claude/plans/` に落とす。親は要約の行だけ読む。
**この周は起動口・要約・手順と、4 つの未確認点の「確かめた範囲」を入れる。実際の 1 周（関門 × 2 パス）と、親の `/clear` からの拾い直しは測っていない（BLOCKED。下）。**

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/child-cycle.py` — 新規。`launch`（子を切り離して起動し、記録を残す）と `status`（出力から要約の行を出す）
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md` — 新規。子に `--append-system-prompt` で中身を渡す委譲文のテンプレート
- `plugins/dev-loop/skills/cruise/references/child-process.md` — 新規。子プロセスで回す形・4 つの未確認点の確かめた範囲・利用者が測る手順
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 2 に「子プロセスで回す（任意）」、§1 の再開と §5 に子の確かめ方。版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 「どう再開するか」の 2 に、子プロセスの周の確かめ方を 1 行
- `scripts/test-child-cycle.py` — 新規。偽の `claude` で当てる回帰テスト（変異テストを含む）
- `scripts/check-all.py` — `TESTS` に登録
- `.github/workflows/plugins.yml` — テストのステップを登録
- `docs/plugins/dev-loop-cruise.md` — 部品の表に 1 行と、子プロセスで回す形の短い節
- `CLAUDE.md` — プロジェクト構成の `cruise/` と `scripts/` の一覧に 1 行ずつ
- `.claude-plugin/marketplace.json` — 版（3 種類）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（3 種類）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版（3 種類）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ）
- `docs/plans/issue-491.md` — この計画

触らない:

- 既定の回し方（サブエージェント）——置き換えない。**子プロセスは選べる形で足す**（下の「仕様の穴」）
- `ledger.py` の台帳の形——子の記録は既存の `agent` の鍵に `claude-p:<記録のパス>` として書く（鍵を増やさない）
- `check-unattended-env.py`・起動口の長期トークン（#584 が触っている。子は親の環境変数を継ぐので、認証は #584 を指すだけ）
- dev-loop の `SKILL.md` の本文（版の 2 行だけ）・cruise の frontmatter（description は変えない）
- 利用者の settings・`~/.claude`（読むだけ。テストは偽の `claude` で当てる）

### 同じことを述べている箇所の数

- 「子プロセスで回す手順」: cruise `SKILL.md` §4 の 2（入口と必須だけ）・`references/child-process.md`（本体）・公開ページ（要点と指し先）の 3 箇所。
  分けない理由: SKILL.md は周を回す親の起点、references は条件つき（子で回すときだけ要る）、公開ページは利用者向けで、役目が違う。列挙は references だけに置き、他は指す
- 「4 つの未確認点の結果」: `references/child-process.md` の 1 箇所（Issue の受入基準 3 の着地点）。公開ページは指すだけ
- 「起動口・要約が何をし、何で止まるか」: `child-cycle.py` の docstring 1 箇所（references と SKILL.md は指すだけ）

## 乗るデプロイ経路

main へのマージで、公開サイト（`docs/`）が GitHub Pages に出て、プラグインの新しい版がカタログに載る（`ドキュメントとプラグインの配布`）。
マージは親がする（cruise の指示）。

## 周の在り処

- ブランチ: `issue/491-cruise-claude-p-child`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-491`
- 起点: `4abb280`（`origin/main`）
- base: `origin/main` → `4abb280dda86eac24190df155e9196f6c0fbb730`（1 パス目まで）
- 取り込み: `origin/main` を `066c440` で取り込んだ（版の行だけ衝突。塊ごとに 1.64.0 を取った。main は 1.63.9）。**式を当て直した base**: `066c440a7861267c397389cd9037581ed73f6023`（2 パス目から）
- 作り方: `prepare-worktree.sh`（メインの作業ツリーを cwd に）。`EnterWorktree` は呼ばない（cruise の子）

## 線（出所）

- 不在の周（`/dev-loop:cruise 474 --absent`。再開 2026-10-29）
- 台帳の確かめた線（出所: 利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））:
  仕様の穴 = 推奨で決めて起票 ／ 直す線 = 既定 ／ マージ = 関門を通ればマージ ／ 周の途中の課題 = 台帳に足して直す
- 利用者の指示（2026-10-29。親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、要確認 Issue を立てる（#565・#561 の形）
- マージは親がする。台帳は書かない（親が書く）。周の途中の課題は報告に挙げ、親が起票する

## 仕様の穴（推奨で決めた）

- **置き換えるか、選べるようにするか**（Issue の「求めること」）→ **選べるようにする（既定はサブエージェントのまま）**。
  理由: 関門が子の中で回りきるか（未確認点 1）と利用上限（3）が実際の周で測れていない。既定を置き換えると、測れていない形が全部の cruise に効く。
  要確認 Issue: #590

## 受入基準

不変条件（番号）と、それを破りうる入口:

- **C1（Issue 案 1）** 不在の cruise で 1 周以上を `claude -p` の子で回し、2 つの関門 × 2 パスが子の中で終わったことを、子の出力ファイルで示す
- **C2（Issue 案 2）** 子が走っている間に親が `/clear` し、同じ引数で起動し直した親が台帳と実物からその周を拾えることを 1 回示す
- **C3（Issue 案 3）** 未確認点 1〜4 の結果が `references/` に、確かめた範囲とともに書かれている——**確かめた（測った）ことと確かめていないことを分け、測ったことは実測の出力と一致する**
- **L1** `launch` は子を**親から切り離して**起動する（新しいセッション。標準入力は閉じる）。cwd はメインの作業ツリー（どこから呼んでも）。
  起動の引数は `-p "/dev-loop:dev-loop <番号>"`・`--output-format stream-json`・`--verbose`・**利用者が名指しした `--permission-mode`**・`--append-system-prompt <委譲文の中身>`。
  入口: worktree の中・サブディレクトリから呼ぶ／`--permission-mode` を渡し忘れる／CLI に無い値を渡す
- **L2** `launch` は次を拒んで子を起こさない: 委譲文が無い・`{{` が残る、`--permission-mode` が無い・選べる値に無い、同じ Issue の子がまだ走っている、メインの作業ツリーが決まらない
- **L3** `launch` は記録（pid・引数・出力と標準エラーのパス・起動時刻）をメインの作業ツリーの `.claude/plans/cruise-<名前>-children/` に残し、**周の worktree の中には書かない**。標準出力に記録のパスを出す
- **S1** `status` は「走っている」と「終わった」を pid と、その pid のコマンドが `claude` であることで分ける（pid の使い回しで走っていると言わない）
- **S2** `status` は**最後の** `result` を読む（子は背景の体を待って `result` を複数出す——実測。下の「確かめた範囲」）
- **S3** `status` は要約の行に、`dev-loop` の版（init の `plugins`）・許可モード（init の `permissionMode`）・セッション・費用・拒否された操作・親に殺された体の数・利用上限の拒否・API の誤り・最後の文（切り詰め）を出す
- **S4** 終了コード: 0 終わって要確認なし／1 走っている／2 引数／3 終わったが要確認（`result` が無い・誤り・拒否・殺された体・利用上限）／4 判定できない（記録が無い・読めない）。docstring の表と一致
- **S5** `status` は出力を丸ごと出さない（行数と長さに上限）
- **D1** cruise `SKILL.md` §4 の 2 が、子プロセスを**任意**として指し、**既定はサブエージェントのまま**と書き、必須（worktree → PR・関門・2 パス・台帳は親だけ・子の報告は実物で確かめる・マージは親）は外れないと書く
- **D2** 再開（§1・`ledger.md` の 2）で、子プロセスの周は `status` と実物（PR・worktree）で確かめてから続け、**走っている子がいれば同じ Issue の子を起こさない**
- **V** 版を 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本）で揃え、main より上げる
- **掛け算** 受入基準を 2 つの関門 × 2 パス = 4 つの受け渡しで渡す（2 パス目が該当なしなら 2 つ）

### 証明できるもの／できないもの

- 証明できる: C3・L1〜L3・S1〜S5・D1・D2・V（偽の `claude` のテストと、実測の出力との突き合わせ）
- **BLOCKED**:
  - **C1** ——何が無いか: **権限**（実際の 1 周を `claude -p` で回すのは、cruise の親（メインの作業ツリーのセッション）が利用者の費用の承認のもとで行う形で、この周は親のサブエージェントであり、親の指示で実際の周を起こさない）。1 周は数ドル以上で、関門の `/code-review` が裏で fork する
  - **C2** ——何が無いか: **道具**（`/clear` は人の操作で、サブエージェントからは親を `/clear` できない）
  - 次善として回したもの: 偽の `claude` のテスト・実物の `claude -p` の小さな試し 2 回（下）。手順は `references/child-process.md` の「利用者が測る手順」に書き、#491 にもコメントで残す（元の Issue を開けたまま `Refs` で指す）
- 未証明（この環境では原理的に証明できない）: なし（上の 2 つは手段があれば証明できるので BLOCKED）

## 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——dev-loop の `SKILL.md` は版の 2 行だけ触るので動かない見込み。`--check` で確かめる
- 図（drawio）: 触らない

## 実測（交絡を潰した手順）

試し 1・2 はメインの作業ツリーを cwd に、haiku で回した（費用は計 $0.107）:

- 試し 1: `claude -p "Reply with exactly the word ok…" --output-format stream-json --verbose --model haiku --max-turns 1 --max-budget-usd 0.5` → `result` 1 つ・$0.087・init の `permissionMode` = `default`・`plugins` の dev-loop = **1.63.6**（main は 1.63.8）
- 試し 2: 背景の `Agent`（`sleep 20`）を起こしてから `date` を打たせ、`--allowedTools "Bash(sleep 20)" "Agent"` → **`result` が 3 つ**（どれも体の通知より後の行。最初の `result` がいつ出たかは行の順からは言えない）・`subagent_stats.killed.parent` = 0・completed = 1・$0.020・`permissionMode` = `auto`・`date` は拒否されなかった（`permission_denials` 空）
- 交絡の候補と潰し方:
  - 「子が背景の体を待つ」は**この版（2.1.312）・背景の体 1 つ・20 秒**の観測。`/code-review` の fork（別の形の背景の実行）を待つかは測っていない——C1 に寄りかかる主張は書かない
  - 許可モードが試し 1 と 2 で分かれた。settings は同じ（`defaultMode: auto`）だが、モデル（haiku-4-5／haiku-5-5）と引数も違った。どれが効いたかは分けていない——**だから起動口は `--permission-mode` を名指しさせ、`status` が init の値を出す**（どちらの値でも、親が子の実際のモードを見られる）
  - `date` が拒否されなかったのは許可モードが `auto` だったから、が候補（`--allowedTools` に無い）。`default` での拒否は測っていない——`permission_denials` の形は試しでは空しか見ていない
  - 版: dev-loop 1.63.6 は `installed_plugins.json` の記録の版で、キャッシュの最大版ではない（CLAUDE.md の「キャッシュに在ることは、読み込まれることではない」と同じ）

## 未解決・確認待ち

- 要確認 Issue（置き換えか選べるか）: #590（推奨: 選べる形。既定はサブエージェントのまま）——利用者が承認して閉じた（2026-10-29。親から伝達）

## 関門の進捗（再開点）

- 手順 4: 完了（`392e91d`）。割り目は訊かない（不在の周。`absent-lines.md` の「訊く場面」）。続けた
- 1 パス目の指摘対応の起点: `392e91d37b17ee8997dcf8badf10a27f10a50dd1`（1 パス目の関門に渡した HEAD）
- 2 パス目: Verifier（sonnet。169 行）反証 2 件／`/code-review`（high）指摘 10 件。採否は表の P2-*（直す 5・残課題 6・記録 1）
- 狭いパスの起点: `adbbc9056a775577592cca2d4785408e08734959`（2 パス目の指摘対応を始める直前）
- 1 パス目の指摘対応: `392e91d`..`1a9a566`（コミット済み）。2 パス目の割り目は訊かない（不在の周）。残り: 手順 5 の当て直しと `/code-review` 2 パス目の両方
- 1 パス目: Verifier（`dev-loop:dev-loop-verifier`・sonnet。テンプレート 170 行を読んだと報告）反証 5 件／`/code-review`（high）指摘 10 件。採否は下の表（直す 8・残課題 3。重なりは 1 行に畳んだ）。手順 4 への差し戻し: あり（直す行）

## 既知の限界・決着済みの論点

（関門の指摘の採否の表もここに書く）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| P1-R1 許可モードの一覧が `manual` を持ち `default` を持たない | 示せる——2.1.312 の本体の文字列に `["acceptEdits","auto","bypassPermissions","default","dontAsk","plan"]`（ヘルプは `manual` を出す）。`launch --permission-mode default` は 2 | L1・L2 | 直す |
| P1-R2／V4 試し 1・2 は「同じ settings」ではない——モデル（haiku-4-5 と haiku-5-5）と引数（`--max-turns`／`--allowedTools`）が違う | 示せる——probe1 の 11 行目・probe2 の 11 行目の init の `model` | C3 | 直す |
| P1-R3 `allowed_warning` を利用上限の拒否と読む | 示せる——本体の文字列に `allowed_warning`（33 箇所）。試料で 3 になる | S4 | 直す |
| P1-R4／V2 `stdin=DEVNULL` を外す変異と、「claude である」の半分を外す変異（`True and`）が素通りする | 示せる——関門が変異を当てて緑（2 体とも） | L1・S1 | 直す |
| P1-R5 委譲文は「親は要約の行と報告だけを読む」と言うが、`status` は最後の文を 300 字で切る | 示せる——probe2 で報告は 2 つ目の result | 無し（S3・S5 のとおりの振る舞い。D1 の必須は実物で確かめるので外れない） | 残課題 |
| P1-R6 §4-2 の子プロセスの項が「委譲文に書くこと」の列挙の中にあり、委譲文が「親の版の SKILL.md を絶対パスで指し、行数を wc -l と照合」を落としている | 示せる——cruise `SKILL.md` §4-2 の 1 項目目と `prompts/child-cycle.md` | D1 | 直す |
| P1-R7／V 「最初の result を出した後もプロセスは終わらず」は probe2 の行の順では示せない（result は 40・41・43 行で、通知の 29・37 行より後） | 示せる——probe2 の行番号 | C3 | 直す |
| P1-R8 走っているかの判定が委譲文の中の `/dev-loop:dev-loop N` にも当たる | 示せる——委譲文を引数で渡すので `ps` に出る | S1 | 直す |
| P1-R9／V5 記録を書けなかったときの孤児の子・読めない古い記録で以後起こせない | 示せない（書けない状態を実データで作っていない） | 無し | 残課題 |
| P1-R10／V1 計画の L1 と決着が `--append-system-prompt-file` のまま | 示せる——計画 L1 と `child-cycle.py` の引数 | L1（文面と実装の食い違い） | 直す（計画の文面を実装に合わせる。仕組みは変えない——下の決着） |
| P1-V3 変異の「殺せた」が例外でも数わる | 示せない（いまの 12 件はどれも観測の差で殺せている——関門 2 体が確かめた） | 無し | 残課題 |
| P2-V1 init が同じプロセスで 3 回出て、2 回目から他のプラグインの版が変わった。「起動の時点の版」と言い切り、status は最初の init だけを読む | 示せる——probe2 の 11 行目（cmux 1.1.1・spec-loop 0.26.0）と 35・42 行目（cmux 1.1.9・spec-loop 0.35.0）。dev-loop は 3 回とも 1.63.6 | C3・S3 | 直す |
| P2-V2 試し 2 の引数は出力からは確かめられない | 示せない（誤りの証拠は無い。引数はこの周で打ったコマンドの記録） | 無し | 残課題 |
| P2-R1 要確認の印を最後の result からしか取らない（前の result の拒否を落としうる） | 示せない（試しの拒否はどれも空で、result ごとの拒否が累積かを測っていない） | 無し | 残課題 |
| P2-R2 最後の文に委譲先の体の発言（`parent_tool_use_id` つき）が入る | 示せる——probe2 の 21・31・32 行目は `parent_tool_use_id` つきの assistant。子が委譲先の途中で止まれば、それが「最後の文」になる | S3 | 直す |
| P2-R3 「許可モードは起動時の点検で決めた値」とあるが、点検に許可モードを決める段は無い | 示せる——cruise `SKILL.md` §3 と `check-unattended-env.py` に該当の段が無い | L1（名指しする値の出所）・D1 | 直す |
| P2-R4 スラッシュコマンドで読み込んだ子に「読んだ行数」を照合させても意味を持たない | 示せない（子を起こしていない。子は差し込まれた本文の先頭の base ディレクトリから `SKILL.md` を読める） | 無し | 残課題 |
| P2-R5 `kill(pid, 0)` が通った後に `ps` が失敗すると「走っていない」を返す（docstring は 4） | 示せる——`is_running` の `if proc.returncode != 0: return False` と終了コードの表 | S4・L2 | 直す |
| P2-R6 cmux のラッパーを挟む間は `claude` の名前が無く「走っていない」と読む | 示せない（この環境の `claude` は cmux の shim だが、子を起こしていないので、その間の `ps` を見ていない） | 無し | 残課題（`--session-id` で照合する案） |
| P2-R7 「記録の版で、キャッシュの最大版でもない」は試しで判別していない（記録の項が複数・最大版も 1.63.6） | 示せる——`installed_plugins.json` の dev-loop の項 6 つ・キャッシュの最大版 1.63.6 | C3 | 直す |
| P2-R8 `--allowed-tools` を確かめずに渡す（bypass と同じだけ広げられる） | 示せる（そのまま渡す） | 無し（L2 が拒むと決めたのは bypassPermissions だけ） | 残課題 |
| P2-R9 計画の「実測」の節に 1 パス目で取り下げた主張が残る | 計画ファイルは関門の検査の対象外 | 無し | 記録として直す（成果物ではない） |
| P2-R10 「1 対 1」は数だけ・「2 体目」の変異が 30 秒の偽の claude を残す | 示せる（テストの読み） | 無し | 残課題 |

- 決着: 子の記録を台帳の新しい鍵にしない——`agent` の値に `claude-p:<記録のパス>` を書く（`ledger.py` の形を変えると #584・他の周と衝突し、台帳の読み手が全部変わる）
- 決着: 委譲文は**中身を `--append-system-prompt` で**渡す（`-p` の文はスラッシュコマンドだけにして、dev-loop の引数を汚さない）。`--append-system-prompt-file` は 2.1.312 の本体には在るがヘルプの一覧に無いので使わない。代わりに委譲文が `ps` に出るので、走っているかの判定は最初の `-p` の引数だけを見る（P1-R8）

## 手順 8

- この周の起票: 0 件（#590 は不在の線 `仕様の穴 = 推奨で決めて起票` の確認の Issue で、関門の指摘の起票ではない。周の途中の課題は親が起票する——親の指示）
