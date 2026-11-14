# Issue #1031: spec-loop の形式検査のモデルを、今の仕様から組んで spec/formal/ に基準として残す入口

## 利用者が決めたこと（2026-11-14、手順 3 の前に `AskUserQuestion` で）

| 論点 | 決定 |
| --- | --- |
| 入口の形 | **独立のスキル** `/spec-loop:formal-baseline`。判定役への渡し方とモデルの残し方は spec-review の手順 3 を正として指し、写しを作らない。spec-review の本体の流れは変えない |
| 反例が出たら | **残して止まる**——モデルは `反例あり` として残し、指摘は振り分けず、`/spec-loop:spec-review` を回すよう伝える |
| 最新の版がリリース済み | **書かずに止まる**——`check-frozen.py` は変えない。次の版（`docs/v<n+1>/`）を作ってから呼び直すよう伝える |
| 直す線 | **既定**（出所: 手順 3 の回答） |

著者が決めたこと（Issue の「決めること」の 3。利用者に伝えた）: 記録の表（`spec-review/v<n>.csv`）の `結果` に **`モデルの保存`** を足す。
実行の行ではない（`回` を上限・autopilot の周・指摘の表の `回` に数えない）。`README.md` の「残した回」はこの行を指す。

## 変更範囲

触る:

- `plugins/spec-loop/skills/formal-baseline/SKILL.md` — 新しいスキル
- `plugins/spec-loop/scripts/formal-baseline.py` — 機械で決まる部分（書く場所の決定 `target`・残したモデルの検査 `check`）
- `scripts/test-formal-baseline.py` — 回帰テスト（変異テストを含む）
- `scripts/check-all.py` — テストの収録
- `.github/workflows/plugins.yml` — CI のステップ
- `plugins/spec-loop/references/tree.md` — 「形式検査のモデル」: 書く側に formal-baseline を足す・`README.md` の形（項目の表）を決める・検査を指す
- `plugins/spec-loop/references/spec-exit.md` — 記録の表の `結果` に `モデルの保存`、指摘の表の「実行の行を足さない回」に足す
- `plugins/spec-loop/agents/formal-checker.md` — 「呼び出し元（spec-review）」を formal-baseline にも広げる
- `plugins/spec-loop/skills/*/SKILL.md` — 版のバナー（全スキル）。spec-review は「モデルを残す」の 2 に検査を 1 行足す
- `plugins/spec-loop/README.md` — スキルとスクリプトの一覧
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版と紹介文
- `.claude-plugin/marketplace.json` — 版と紹介文
- `docs/plugins/index.md` — スキルの一覧
- `docs/plugins/spec-loop.md` — スキルの表・成果物の表・「モデルの置き場所と次の回」
- `CLAUDE.md` — プロジェクト構成
- `docs/plans/issue-1031.md` — この計画

触らない:

- `plugins/spec-loop/scripts/check-frozen.py`（利用者の決定。凍結の意味は変えない）
- spec-review の手順の流れ（レビュー・振り分け・抜ける条件）
- `merge-versions.py` の `is_formal`（判別は 1 箇所のまま。読み込むだけ）

## 乗るデプロイ経路

main へのマージで GitHub Pages の再ビルド（`docs/` を触る）と、プラグインの配布（`marketplace.json`・`link-skills.sh`）。`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」。

## 周の大きさ（同じことを述べている箇所の数）

「formal-baseline がモデルを書く／`モデルの保存` の行」を述べる箇所: `SKILL.md`（新）・`tree.md`・`spec-exit.md`・`formal-checker.md`・`spec-review/SKILL.md`・
`README.md`・`plugin.json`・`marketplace.json`・`docs/plugins/index.md`・`docs/plugins/spec-loop.md`・`CLAUDE.md` の **11 箇所**。
**分けない理由**: スキルを足すとカタログ・README・公開ページ・CLAUDE.md の登録は同じ PR で揃えないと CI（description・版・収録）が落ちる。
手順の原本は spec-review と `tree.md` に置いたまま指すだけにし、列挙（`README.md` の項目・検査の内容）は `tree.md` とスクリプトの docstring の 2 つに限る（テストが突き合わせる）。

## verify の受入基準

不変条件と、それを破りうる経路:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | リリースした版（`release-v<n>`）の `docs/v<n>/` に書かない | (1) 最新の版がリリース済み (2) 版が 1 つも無い (3) git でない・浅い clone でタグが見えない (4) スキルが `target` を飛ばして書く | `target` が 3（凍結）・2（判定できない）で止まり、書く場所を出さない。スキルは `target` が 0 のときだけ書く |
| B | 残すのは検査器が走らせたファイルだけで、作業ファイル・出力・前の残りを残さない | (1) TLC の `states/`・Alloy の `<名前>/`・出力ファイルを写した (2) `README.md` の「モデルのファイル」に無いファイルが在る (3) 一覧のファイルが無い | `check` が、ディレクトリの中身（`README.md` を除く）と一覧が一致しないと 1 |
| C | `README.md` の記録が `tree.md` の項目をすべて持つ | (1) 項目の欠け・空 (2) 結果が `反例なし`／`反例あり` でない（`判定できなかった` の対象を残した） (3) 前回のモデルが 4 つの値のどれでもない (4) スクリプトの項目が `tree.md` とずれる | `check` が 1。テストが `tree.md` の表と定数を突き合わせる |
| D | 反例が出ても指摘を振り分けず、仕様・要求・Q&A 表を書き換えない | スキルが反例を見て直す・起票する | スキルの「守ること」と手順で止まって spec-review へ渡す（散文。**機械では見ない——未証明側**） |
| E | `モデルの保存` の行が実行に数えられない | (1) 上限の数え方 (2) autopilot の周の番号 (3) `check-findings-csv.py` の `回` | どれも `抜けた`／`抜けていない` だけを実行の行と読む（既存）。`spec-exit.md` の値の一覧に足す。テストで `check-findings-csv.py` が `モデルの保存` の `回` を実行の行と読まないことを見る |
| F | `<対象>` の名前が英小文字・数字・ハイフン | 大文字・空白・`_` | `check` が 1 |
| G | 判定役は別ティアで、名前空間つきで呼ぶ／`claude -p` では前景 | スキルの手順 | spec-review の手順 3 を正として指す（散文。未証明） |

規定の掛け算（必須要件の組）: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目に渡す = 4 つの受け渡し。

**証明できるもの**: A・B・C・E・F（スクリプトとテストで実際に走らせる）。版・description の整合（CI の検査）。

**この環境では証明できないもの（未証明）**: D・G——スキルの散文に従ったモデルの振る舞いは、実際の正本で `claude` を起こして回さないと確かめられない
（判定役と TLC を走らせるので課金と時間が掛かる。この周では回さない）。人間のレビューに回す。

**生成物**: 該当あり——`scripts/skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけを測るので、spec-loop の変更では動かないはず。`--check` で確かめる。図（drawio）は触らない。

## 未解決の判断・確認待ち

なし（上の決定で揃った）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1031-formal-baseline`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1031`・
  起点 `1698006`・base の参照 `origin/main`・base の SHA `1698006bf97f8873037a21a6d3c18455909732f1`
- 実装: `866102a` でコミット済み（手順 4 の終わり）。`check-all.py` は 79 本中 78 本が緑。
  落ちた 1 本 `test-check-deps-declared.py` は 2 回とも `shutil.copytree` が一時ディレクトリの `.git/objects/maintenance.lock` を見失う形で、単独では緑（この周の差分の外。手順 8 で起票を訊く候補）
- 割り目（手順 4 の終わり）: `AskUserQuestion` で訊いたが 300 秒で答えが返らず、このまま続けた
- 関門: 1 パス目を通した（1 パス目の指摘対応の起点 `aca6bf96663135681262654c97e4064b78dea899`）
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**・低重大度の観察 3 件（読んだ行数 185 は `wc -l` と一致）
  - `/code-review`（high）: **指摘 10 件**。うち 3 件を直す（CR2・CR3・CR8）、7 件は残課題（下の採否の表）
- 反証と差し戻し: 1 パス目の指摘 3 件を手順 4 に戻して直した（`formal-baseline.py` の値の一致と、タグの取り直し。試料 7 件・変異 3 件を足した）
- 交絡を潰した手順: 実験なし（テストの陽性対照として、効かない変異を 1 つ足した写しが赤になることを見た）

## 起票

- この周の起票: 0 件（関門の前。採否の表に起票の候補が無い）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 過去のモデルを取り戻す | 採らない | 失われている。今の仕様から組み直したものを基準にする |
| `check-frozen.py` から `spec/formal/` を外す | 採らない | 利用者の決定（書かずに止まる） |
| 抜けていない仕様で formal-baseline を呼ぶことを禁じる | 採らない | 反例が出れば止まって spec-review へ渡すので害が無い。抜けたかの判定を 2 箇所に持たない |
| spec-review の「モデルを残す」の手順を formal-baseline に写す | 採らない | 写しを作らず指す。検査（`check`）だけを両方が呼ぶ |

### 1 パス目の採否の表（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2: `結果`・`前回のモデル` を前方一致で見るので `反例なしかは判定できなかった` が通る | 示せる——`scratchpad/probe1.py` で `check` が 0 | C(2)(3) | 直す（値そのものか `（` で始まる要約を続けた形だけ） |
| CR3: `--no-tags` の clone・取っていない `release-v<n>` でリリース済みの版に書く場所を出す | 示せる——同じ probe で `--no-tags` の clone に `target` が 0 | A(3) | 直す（リモートがあれば `git fetch --all --tags` してから見る。取り直せなければ 2） |
| CR8: 試料が CR2・CR3 を判別していない | 示せる——直す前の本体で試料が緑 | C・A | 直す（試料 7 件・変異 3 件を足した） |
| CR1・V 観察 3: 差分の無い場面で「改修の性質で選ぶ」をどう当てるかが一意でなく、既存システムの v1 で対象が 0 件になりうる | 示せる——`spec-exit.md:246-248` と `formal-baseline/SKILL.md` の手順 2 | 無し（A〜G に無い） | 残課題（PR で最も重いものとして人間に渡す） |
| CR4: `残した回` の説明が「手順 5 で足す」だが行を足すのは手順 4 | 示せる——`SKILL.md` の手順 4 | 無し | 残課題 |
| CR5: 名前 `-` が通り、scaffold の `FORMAL_NAME`（`[a-z0-9][a-z0-9-]*`）と食い違う | 示せる——probe で 0 | 無し（`tree.md` の「英小文字・数字・ハイフン」には合う） | 残課題 |
| CR6: コードブロックや別の表の `| 結果 |` の行も読む | 示せる（レビュー側の実走） | 無し（偽陽性） | 残課題 |
| CR7: `モデルのファイル` の注記のバッククォートもファイル名と読む | 示せる（レビュー側の実走） | 無し（偽陽性） | 残課題 |
| CR9: `check-frozen.py` の確かめを写していて、HEAD の確かめが無い・失敗の言い方が違う | 示せない（今の違いは誤った書く場所を生まない） | 無し | 残課題 |
| CR10: autopilot の `init` の除外の列挙に `モデルの保存` が無い | 示せない——実行の行は `抜けた`・`抜けていない` で肯定形に決まる（Verifier も一致と判定） | 無し | 残課題 |
| V 観察 1: 一覧に同じ名前を 2 度書いても通る | 示せる（Verifier の実走） | 無し | 残課題 |
| V 観察 2: `.DS_Store` も一覧に無いファイルとして違反 | 示せる（Verifier の実走） | 無し（B の趣旨どおり。macOS では偽陽性） | 残課題 |
