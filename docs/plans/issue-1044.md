# Issue #1044 — spec-loop: 抜ける条件 2〜5 と上限をスクリプトで再計算し、scaffold が「抜けた」の記録を読む

cruise（親 Issue #1075）の子として回す周。**不在の周**（出所: `/dev-loop:cruise 1075 --absent` の起動・2026-11-16）。AskUserQuestion は使わない。
spec-loop から来た Issue ではない（本文の先頭に `<!-- spec-loop-handoff:` が無い）。`作り直しの元:` の行も無い。`find-cycle.py 1044` は 5 本とも当たらず、新規の周。

台帳の確かめた線（出所: 利用者の確認（`/dev-loop:cruise 1075 --absent` の起動時・2026-11-16））:
直す線 = `既定` / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた。**子はマージしない**——PR 側の CI まで）/
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。

直す線: `既定`（出所: cruise の確かめた線）。

重い検査は `run-serial.py` 越しに回す——`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.111.0/skills/cruise/scripts/run-serial.py -- <コマンド>`（並行の検査の本数は 1・宣言なし）。関門にも渡す。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-review-record.py` — 新設。`conditions`（指摘の表から条件 2・3 と狭いパスの効く重さを数え直す）・`limit`（記録の表から上限を数える）と、記録の表の読み方（scaffold が読み込む）
- `plugins/spec-loop/scripts/check-formal-rerun.py` — 新設。保存した TLC のモデルの本体と陽性対照を、正本の `CLAUDE.md` の呼び方で走らせ直す（条件 4）
- `plugins/spec-loop/scripts/scaffold.py` — 書く生成と `--dry-run`（`--upto` なし）で、作業中の版の記録の最後の実行の行が `抜けた` でなければ作らない。docstring
- `plugins/spec-loop/scripts/formal-baseline.py` — 記録の項目 `陽性対照のファイル`（任意）を読み、一覧のファイルとして通す
- `plugins/spec-loop/scripts/autopilot-check.py` — spec-review が呼ぶスクリプトの一覧（`SPEC_REVIEW_SCRIPTS`）に新設の 2 本
- `plugins/spec-loop/references/spec-exit.md` — 条件の表の「誰が判定するか」・条件 1 の節・「上限」・「指摘の重さ」に、スクリプトの再計算
- `plugins/spec-loop/references/tree.md` — 「形式検査のモデル」の記録の項目 `陽性対照のファイル`
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 手順 1 の 4（上限）・手順 3 の「モデルを残す」（陽性対照のファイルを写す）・手順 6（スクリプトを当てる）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 手順の「0 でも、抜けたとは限らない」を記録の照合に置き換え。frontmatter
- `plugins/spec-loop/skills/formal-baseline/SKILL.md` — 陽性対照のファイルを写す
- `plugins/spec-loop/agents/formal-checker.md` — TLC の陽性対照のモデルを、写すファイルとして挙げる
- `plugins/spec-loop/README.md` — スクリプトの表に新設の 2 本
- `scripts/test-check-review-record.py` — 新設（変異テストを含む）
- `scripts/test-check-formal-rerun.py` — 新設（変異テストを含む。偽の TLC）
- `scripts/test-scaffold.py` — 試料の正本に記録の表（`抜けた`）を置く。記録の関門の試料と変異
- `scripts/test-green-list.py` — 試料の正本に記録の表
- `scripts/test-parent-checklist.py` — 同上
- `scripts/test-rebuild-scope.py` — 同上（`test-rework-metrics.py` はこの試料を読み込む）
- `scripts/test-check-spec-writeback.py` — 同上
- `scripts/test-formal-baseline.py` — `陽性対照のファイル` の試料
- `scripts/check-all.py` — 新設のテスト 2 本の収録
- `.github/workflows/plugins.yml` — 同上
- `CLAUDE.md` — プロジェクト構成の一覧に新設の 2 本とテスト
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（7 本）
- `docs/plans/issue-1044.md` — この計画

触らない:

- Alloy・総当たり・Z3 のモデルの走らせ直し（Issue の提案 3 は `check-tlc.py` の呼び方で走らせ直すもの。TLC でない対象は今までどおり判定役の判定）
- 指摘の表・記録の表の列（形は変えない——数え直しは今の列から決まる分だけ）
- 狭いパスの「全部の役から返った」「元の指摘が `解消した`」（指摘の表に残らないので数え直せない）
- scaffold の `--check`・`--red-check`・`--upto`（本文を作らない／前の版の時点を見る——下の「決めたこと」）
- `check-spec-exit.py`・`check-findings-csv.py` の判定（読み込んで使うだけ）

依存の追加・更新: なし
仕様の振る舞い: 該当なし（このリポジトリは spec-loop の正本ではない）

版の上げ方: spec-loop を 0.90.0 → 0.91.0（minor。0.x なので壊れる変更も minor）。3 種類: `marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md`（7 本）の 2 行。
並行する周（#1046 も spec-loop）が先に同じ版でマージしたら、マージの直前に子が取り込みと上げ直しをする（`parallel.md` の「版とマージの順」）。

## 決めたこと

- **数え直す「最後のレビュー」**: その回に `2回目` の行があるか、`1回目` の行に振り分けが `仕様を直す`・`範囲の外として記録する` の行があれば（spec-review の手順 5 が 2 回目を回す条件）、
  最後のレビューは 2 回目。2 回目の行が 0 件なら、2 回目は指摘なし。そうでなければ 1 回目。数える行は、最後のレビューの `red-team` の行と、`狭いパス` の行（役を問わない——狭いパスの 3 つ目）のうち、
  重さが `判断が要る`・`結果が割れる` で、振り分けが `退ける` でないもの。1 件でもあれば 1（満たさない）。
- **上限の N**: 既定 3。正本の `CLAUDE.md` で変えたなら spec-review が `--limit` で渡す（スクリプトは `CLAUDE.md` を読まない）。達したら 3。
- **scaffold の記録の関門**: 書く生成と `--dry-run`（`--upto` なし）だけ。記録が無い・実行の行が無い・最後の実行の行が `抜けた` でないなら 1（作らない。書く生成なら前の本文を消す）。読めない記録は 2。
  `--check`・`--red-check` は本文を作らず、別リポジトリの CI が `--check` を当てる（`references/tree.md`）ので当てない。`--upto` は前の版の時点を見るので当てない（システム設計書の関門と同じ）。
- **条件 4 の走らせ直し**: TLC のモデルだけ。モデルのファイルの一覧の `.tla` のうち、同じ名前の `.cfg` が一覧にあるものを本体、`陽性対照のファイル` の同じ形を陽性対照とし、
  一時ディレクトリに両方の一覧を写して走らせる。本体: 終了コード 0 で `No error has been found` → 反例なし、違反の印 → 反例あり、それ以外 → 判定できなかった。
  陽性対照: 違反の印が出なければ判定できなかった（空振り）。陽性対照のファイルが無い・本体が無い・呼び方が無い → 判定できなかった。
- **仕様の穴（不在の線で推奨により決めた）**: 陽性対照をファイルとして残す形——下の「未解決の判断・確認待ち」。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ）と公開サイトの再ビルド（`docs/plans/`）。子はマージしない。

## 受入基準（不変条件 × 経路）

証明できるもの:

| # | 不変条件 | 経路（入口） | 守り方 |
| --- | --- | --- | --- |
| A1 | Red Team の効く重さの行が最後のレビューに 1 行でも残る指摘の表で、`conditions` が非 0 | `check-review-record.py conditions`（Issue の受入基準 1） | 判定。テストで `判断が要る` 1 行の表（陽性対照） |
| A2 | 効く重さの行が無い（`補い` だけ・退けた・範囲の外・1 回目にだけあって 2 回目が回った）表で `conditions` が 0 | 同上 | 同上（陰性の対照） |
| A3 | 壊れた・読めない指摘の表・実行の行が無い記録で 0 にしない（2） | 同上 | `check-findings-csv.py` の `check` を先に当てる |
| A4 | 数え始め以降に `満たさない`・`判定できなかった` が N 行あれば `limit` が上限（3）、最後の利用者の判断が `止める` でも 3、未満なら 0 | `check-review-record.py limit` | 判定。テスト |
| A5 | 陽性対照で反例が出ない TLC のモデルを「判定できなかった」として非 0 | `check-formal-rerun.py`（Issue の受入基準 2） | 判定。偽の TLC で |
| A6 | 本体で反例が出るモデルを 0 にしない・本体が通り陽性対照で反例が出るなら 0 | 同上 | 同上 |
| A7 | 最後の実行の行が `抜けていない` のとき、`scaffold.py` が何も生成しない（`scaffold/` も本文も書かない） | `scaffold.py`（書く生成・`--dry-run`）（Issue の受入基準 3） | 関門。test-scaffold の試料 |
| A8 | 記録が無い・実行の行が無いときも作らない。`抜けた` なら今までどおり作る | 同上 | 同上 |
| A9 | `--check`・`--red-check` は記録で止めない（別リポジトリの CI の `--check`） | `scaffold.py --check` | 試料 |
| A10 | 保存したモデルの形の検査が、`陽性対照のファイル` の一覧のファイルを通し、一覧に無いファイルは今までどおり落とす。項目が無い前からのモデルも通す | `formal-baseline.py check` | 試料 |
| A11 | spec-review・scaffold・formal-baseline・formal-checker・references の記述が、スクリプトの動き（呼び方・終了コード・項目）と食い違わない | 文書 | 関門の読解 |
| A12 | 生成物の鮮度: 設計ドキュメント §8.2 の生成ブロック（`skill-metrics.py --check`）——spec-loop の SKILL.md は測っていないなら変わらない | `skill-metrics.py --check` | CI |
| A13 | 版の 3 種類が揃う・description の同期（scaffold の frontmatter だけ変える——trailer） | `check-plugin-versions.py`・`check-description-sync.py` | CI |
| A14 | 新設のテストが `check-all.py` と CI に収録されている | `test-check-all.py` | CI |

この環境で証明できないもの（未証明）:

- **本物の TLC での判定の文字列**（`No error has been found`・違反の印）——回帰テストは偽の TLC で当てる。実機（手元の `/Users/hdknr/.local/bin/tlc`）で 1 度走らせて手順 5 に書く（CI に TLC は無い）。

生成物: `skill-metrics.py` の生成ブロック（§8.2。dev-loop の `SKILL.md` を測る——この周は触らない）。ほかに生成物なし（図は触らない）。

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

周の大きさ: 同じことを述べている箇所——「最後のレビューの数え方」は spec-exit.md（原本）・spec-review の手順 6・check-review-record.py の docstring の 3 か所、
「scaffold が記録を読む」は scaffold.py の docstring・scaffold の SKILL.md・spec-exit.md の 3 か所、`陽性対照のファイル` は tree.md（原本）・formal-baseline.py の写し・spec-review 手順 3・formal-baseline の SKILL.md・formal-checker.md の 5 か所。
分けない理由: 4 つの提案はどれも「判定役の書き写しから機械の判定に移す」1 つの変更で、Issue が 1 周で求めている。

## 未解決の判断・確認待ち

- **仕様の穴（不在の線で推奨により決めた）**: 保存したモデルの陽性対照を、どの形で残すか。選択肢: (a) 記録の項目 `陽性対照のファイル` を足し、陽性対照のモデルのファイルを同じディレクトリに写す（形の検査では任意。走らせ直しでは必須）／
  (b) 同じく足すが形の検査でも必須にする（前からのモデルは落ちる。移行が要る）／(c) 陽性対照を本体への差分（パッチ）で残す。推奨 (a)——前に残したモデルを壊さず、次の spec-review の回が残し直す時点で揃う。確認の Issue: #1076（2026-11-16 起票。台帳の `decisions` に足すのは親）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1044-review-record-recount`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1044`・起点 `52d73bc`・base `origin/main` → `52d73bc36861fd90c59a10ab65ab949d20e96ec5`
- 割り目 1（手順 4 の後）: 割らない（cruise の周）

## 既知の限界・決着済みの論点

- 指摘の表は判定役が案を「範囲の外」「実装に渡す」とした行を呼び出し元が範囲の中に振り直したことを残さないので、その例外（spec-exit.md の条件の表の下）は数え直せない——判定役の判定と、数え直しの両方が `満たす` のときだけ満たす、と spec-review に書く（厳しいほうを取る）。
- 2 回目を回す前に止めた回（実行の行は `抜けていない`）で 1 回目に `仕様を直す` の行があると、数え直しは「2 回目は指摘なし」と読む——その回は記録が `抜けていない` なので、scaffold は止まる。
- scaffold は記録を読むだけで、`抜けた` の後に仕様が直されたかは見ない。
