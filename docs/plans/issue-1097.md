# Issue #1097 — spec-loop: 画面の表を関門に入れ、screen-spec が無ければ止める（#1081 段 4）

**不在の周である**——cruise（親 Issue #1081）の子として回す。出所: `/dev-loop:cruise 1081 --absent` の起動（2026-11-16T04:38Z）。
確かめた線（台帳 `issue-1081`。出所: 利用者の確認（起動時・2026-11-16、配布を見せて確かめた））:
直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ / 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。実機確認の線は無い。
#1097 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。
この周はマージしない（親がする）——PR を作り、PR 側の CI が通るのを見るところまで。
前提の確認の Issue（閉じない・閉じるキーワードで指さない）: #1104・#1105（承認済み）、#1109（入口の画面は種別 `top`）・#1110（対応する spec-loop の版は 0.93.0 以上 1.0.0 未満）・#1111（本物のプラグインの記録から spec-loop を探す経路は未確認のままマージ）。
**#1093・#1095 の周が同時に走っている**——重い検査は run-serial 越し（枠 1 本）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/screen-gate.py` — 新設。画面の表の関門（画面の表があれば未決定の印と screen-spec の検査の結果を入れる。screen-spec が無ければ止める）
- `plugins/spec-loop/scripts/check-spec-exit.py` — 条件 1 に画面の関門を入れる（`--docs`・`--upto`・`--screen-spec`）
- `plugins/spec-loop/scripts/scaffold.py` — 関門に画面の関門を入れる（成果物の表の関門と同じ条件）
- `plugins/spec-loop/scripts/autopilot-check.py` — `screen-gate.py` と screen-spec の `check-screens.py` を権限の点検に足す
- `plugins/spec-loop/references/` — `tree.md`（`requirements/screens/` を任意の項目として）・`spec-scope.md`（画面の表は要求の入力で、`spec/` に見た目・配置を写さない）・`spec-exit.md`（条件 1 の画面の分）・`versions.md`（条件 1 の当て方の行）・`signoff-tags.md`（サインオフの前の確かめ）
- `plugins/spec-loop/skills/*/SKILL.md` — req-loop・spec-review・scaffold・autopilot の手順（画面の関門を呼んで止まる）と、全スキルの版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — spec-loop の版
- `.claude-plugin/marketplace.json` — spec-loop の版
- `scripts/test-screen-gate.py` — 新設。回帰テスト（陽性対照・陰性対照・変異）
- `scripts/test-scaffold.py` — 画面の関門の分の試料と変異
- `scripts/test-autopilot-check.py` — screen-spec の項目の試料と変異（本体はテンポラリの写しから読む）
- `scripts/check-all.py` — 新しいテストの収録
- `.github/workflows/plugins.yml` — 新しいテストの収録
- `CLAUDE.md` — プロジェクト構成に `screen-gate.py` と新しいテストを足す
- `docs/plans/issue-1097.md` — この計画

触らない:

- `plugins/screen-spec/` — screen-spec の側は変えない（spec-loop は screen-spec の `check-screens.py` を子のプロセスで呼ぶだけ）
- `check-signoff.py`・`build-proposal.py` — サインオフの照合の結果は変えない（受入基準の回帰）。サインオフの前の確かめは `signoff-tags.md` の手順に書く（下の穴 2）
- req-loop の画面の検査の起票・PPTX のモックへのリンク（#1100）、scaffold の `refs`・feasibility・UI モックの位置づけ（#1099）、MkDocs のフック（#1098）
- 公開ページ（`docs/`）

複製の数: 「画面の表があれば関門に入れ、screen-spec が無ければ止める」を述べる箇所——`screen-gate.py` の docstring（原本）、`spec-exit.md`・`tree.md`・`signoff-tags.md`・`versions.md`（指し先）、4 つの SKILL.md（呼び方と止まり方）、`check-spec-exit.py`・`scaffold.py`・`autopilot-check.py` の docstring（呼ぶ側の 1 行）で 12 箇所。
**分けない理由**: 関門は 1 つの判定で、呼ぶ側が別々に書くと食い違うので、判定は `screen-gate.py` に 1 つだけ置き、ほかは「`screen-gate.py` の docstring を正とする」と指すだけにする（列挙を写さない）。
screen-spec の見つけ方は screen-spec の `check-screens.py` の spec-loop の見つけ方（`references/spec-loop.md`）と同じ形の写しになる（プラグインをまたいで読み込めない）——テストが両方の順を同じ試料で見る。

依存の追加・更新: なし

仕様の振る舞い: 対象外（このリポジトリに spec-loop の正本は無い）

## 決めたこと（実装で決めてよいもの）

- **関門の判定を 1 つのスクリプトに置く**（`screen-gate.py`）。`check-spec-exit.py`・`scaffold.py` は関数として読み込み、スキルは CLI で呼ぶ。screen-spec は子のプロセスで呼ぶ（読み込まない——spec-loop は screen-spec が無くても読み込める）。
- **画面の表が無いかは、版のディレクトリ（`--upto` まで）に `requirements/screens/` の下のファイルが 1 つも無いかで先に見る**——無ければ重ね合わせもせずに何も言わずに 0（今の出力と変わらない）。在れば重ねた全体で見る（`removed.csv` で全部消したなら無いと同じ）。
- **未決定の印は spec-loop 自身でも数える**（重ねた全体の `requirements/screens/` の `.csv`・`.md`。印の判定は `check-spec-exit.py` の `find_markers`）——screen-spec の検査が走らなくても、`未定` が残れば止まる。
- **終了コード**: 0 通る（表が無いを含む）／ 1 違反か未決定（screen-spec の 1・3、spec-loop が数えた印）／ 2 判定していない（screen-spec の 2・読めない）／ 4 止めた（画面の表があるのに screen-spec が見つからない・screen-spec の 4）。1 は 4・2 より強い。
- **`check-spec-exit.py` の終了コードは増やさない**——画面の関門の 2・4 は条件 1 の「判定していない」（2）にする。`--docs` を渡さずに、仕様のディレクトリの親（重ねた全体の根）に `requirements/screens/` があれば 2（画面の関門を判定していない）。
- **scaffold は成果物の表の関門と同じ条件で当てる**（作業中の版の全体だけ。`--upto` で前の版の時点を見るときは当てない）。2・4 は「判定していない」（2）、1 は 1。

## 決めたこと（仕様の穴。`仕様の穴 = 推奨で決めて起票` の線で推奨により決めた）

- **穴 1: spec-loop が screen-spec を見つける順**——#1081・#1097 は「`screen-spec` の在り処の見つけ方を決める」とだけ書き、決めていない（#1081 の「#1097 の在り処の見つけ方は周の中で決める」）。
  - 選択肢: A) screen-spec が spec-loop を見つける順と同じ形——引数 `--screen-spec` → 環境変数 `SPEC_LOOP_SCREEN_SPEC` → 隣のディレクトリ（このリポジトリの `plugins/screen-spec/`）→ `installed_plugins.json` の `screen-spec@<同じマーケットプレイス>`（推奨）／ B) 引数か環境変数で名指ししたときだけ（名指しが無ければ、画面の表のある正本では必ず止まる）／ C) A から `installed_plugins.json` を外す
  - 推奨 A。理由: 利用者がプラグインを入れただけで動き、名指しの手間が無い。#1111 で screen-spec の側が採った形と同じなので、読む側が 1 つの形を覚えればよい。B は入れていても毎回名指しが要る。C は入れた利用者の手元で必ず止まる。
- **穴 2: 「サインオフの前の確かめ」の形**——#1081・#1097 は関門の 1 つに挙げるが、spec-loop にその名前の確かめは無い（照合 `check-signoff.py` はタグの後）。
  - 選択肢: A) `signoff-tags.md` に「画面の表のある版では、要求確定のタグを付ける前に `screen-gate.py` が 0 であることを確かめる」手順を書く。照合のスクリプトは変えない（推奨）／ B) `check-signoff.py` が要求確定のタグの時点の中身に画面の関門を当て、通らなければ照合を落とす（提案書を作らない）
  - 推奨 A。理由: サインオフの照合の結果を変えない（#1097 の受入基準の回帰）。タグを付ける人がタグの前に確かめる場所に置ける。B はタグの時点の中身を写して screen-spec を走らせる口が要り、照合の終了コードの意味が増える。
- **穴 3: req-loop が画面の関門のどの結果で止まるか**——#1097 の受入基準は「screen-spec が入っていない案件で req-loop が止まる」だけを言う。
  - 選択肢: A) 止めた（4）と判定していない（2）でだけ止まり、違反・未決定（1）では止まらない（推奨）／ B) 1 でも止まる
  - 推奨 A。理由: req-loop は未決定事項を起票して回答を集める段で、未決定が残るのはふつうである（止めると req-loop が回らない）。未決定の起票の候補を req-loop が扱うのは #1100。
- 決めた値は受入基準を足さない（`absent-lines.md`）。確認の Issue は PR を作った後に穴ごとに 1 件立てる。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ。spec-loop の版が上がる）。公開ページ（`docs/`）は触らない。

## 版の上げ方

spec-loop を **minor** で上げる（能力の追加。0.x なので壊れる変更も minor。`0.93.0` → `0.94.0`）。`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行。
並行する #1093・#1095 は screen-spec を触る周で、spec-loop の版とは衝突しない見込み。マージの直前に main が進んでいたら、main の先端の spec-loop の版から minor で 1 つ上げた値に上げ直し、
`check-plugin-versions.py`・`skill-metrics.py --check` だけ回して push し、PR 側の CI を見る（cruise の `references/parallel.md` の「版とマージの順」・CLAUDE.md の「並行する周は、同じ版に上げて衝突する」の 5）。

## 受入基準（不変条件 × 経路）

入口（画面の関門を通る経路）: `screen-gate.py` の CLI、`check-spec-exit.py`（`--docs` あり・なし）、`scaffold.py`（書く生成・`--dry-run`・`--check`。`--upto` 前の版・作業中の版）、
スキルの手順（req-loop・spec-review・scaffold・autopilot）、`autopilot-check.py`（`ops`・`check`）。画面の表は v1 にも v2 以降にも置け、`removed.csv` で消せる。screen-spec は 4 つの場所（引数・環境変数・隣・`installed_plugins.json`）で見つかる。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| U1（回帰） | screen-spec が無く画面の表も無い正本で、出力と終了コードが今と変わらない | `check-spec-exit.py`（`--docs` なし・あり）・`scaffold.py`（`--dry-run`・`--check`・書く生成）・req-loop の手順・`check-signoff.py`（触らない） | 版のディレクトリに `requirements/screens/` が無ければ何も足さない。テストは main の版と同じ出力・終了コードかを見る |
| U2 | 画面の表があって screen-spec が無い正本で、関門が止まる（0 にならない） | `screen-gate.py`（4）・`check-spec-exit.py --docs`（2）・`check-spec-exit.py`（`--docs` なし、2）・`scaffold.py`（2。何も書かない）・req-loop・spec-review・scaffold の手順（止まると書く） | 見つけ方の 4 つがどれも当たらなければ 4。名指し（引数・環境変数）が screen-spec でなければ、ほかを探さずに 4 |
| U3 | 画面の表に `未定` を 1 つ残した正本で、抜ける条件 1 と scaffold の関門が止まる。**陽性対照**: 同じ正本で今（main）の関門が通る | `check-spec-exit.py --docs`（1）・`scaffold.py --dry-run`（1）。表のセル（画面・項目・遷移）・散文の仕様書・v2 に置いた行 | spec-loop が数えた印と screen-spec の検査（3）のどちらでも 1 |
| U4 | `autopilot-check.py` が screen-spec のスクリプトの権限を点検して示す | `ops`・`check`。screen-spec が見つかる・見つからない（正本に画面の表がある・無い） | `screen-gate.py` を spec-review の周のスクリプトに足す。見つかれば `python3 <screen-spec の根>/scripts/check-screens.py` を点検の操作に足し、見つからなければ項目で示す（画面の表があれば要対処） |
| U5 | 画面の表があって screen-spec の検査が違反（1）か判定していない（2）なら関門が通らない | `screen-gate.py`・`check-spec-exit.py --docs`・`scaffold.py` | 終了コードを読み替える（1・3 → 1、2 → 2、4 → 4、ほか → 2） |
| U6 | spec-loop は screen-spec に依存しない——screen-spec が無くても spec-loop のスクリプトは読み込めて動く | `check-spec-exit.py`・`scaffold.py`・`autopilot-check.py` の読み込み | screen-spec を読み込まない（子のプロセスで呼ぶ）。U1 の試料は screen-spec の無い場所で走らせる |
| U7 | 文書: `tree.md` に `requirements/screens/` を任意の項目として書く。`spec-scope.md` と spec-review が、画面の表と仕様書を要求の入力として読み、`spec/` に見た目・配置を書き写さない・遷移の表を Formal Checker の材料にできる・profile の指摘を既存の振り分けに乗せる、と書く | 文書 | 読んで確かめる（**書かれた内容が事実と合うか**——指すスクリプト・パス・終了コードが実物と一致するか——も見る） |
| U8 | 画面の関門はファイルを書かない（正本・プラグインの写し・cwd） | `screen-gate.py`（screen-spec の子のプロセスを含む） | `sys.dont_write_bytecode`。テストが前後のバイトを見る |
| U9 | 版・カタログ・歯止めが全部緑（版 3 種類・CI と `check-all.py` への収録・指し先・件数の重複） | `check-all.py` | 順番待ち越しに回す |
| X1 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方 × 1・2 パス目に渡す（2 パス目が「該当なし」の周は 1 パス目の 2 つ） | — | 再開点で記録 |

**証明できないもの（未証明）**: 本物のプラグインの記録（`~/.claude/plugins/installed_plugins.json`）から screen-spec を見つける経路——screen-spec 0.1.0 は main に入ったが、手元の記録が screen-spec を名指すかは利用者の更新しだいで、実環境の記録を読ませない（テストは一時の `CLAUDE_CONFIG_DIR` に同じ形を作って当てる）。U2 そのものは引数・環境変数・隣の経路で証明できる。

**BLOCKED の候補（手順 5 で判定）**: スキル（req-loop・spec-review）が本文どおりに関門の終了コードで止まるか——モデルの振る舞いで、確かめる手段は `claude plugin eval`（このセッションからは起こせない——worktree 隔離のガードが拒む。CLAUDE.md の「振る舞いを Eval で当てる」）。スクリプトが止まるコードを返すことと、本文が止まると書くことは証明できる。

**生成物**: 無し——`SKILL.md` の測定値（設計 §8.2）は dev-loop の `SKILL.md` だけを測る。図の書き出しも無し。`skill-metrics.py --check` で変わらないことを確かめる。

## 実機確認

一時ディレクトリに正本（`docs/v1/`・`docs/v2/`）を置き、`screen-gate.py`・`check-spec-exit.py`・`scaffold.py --dry-run` を走らせて U1〜U5 を目で見る（陽性対照は `未定` を 1 つ置いた例を main の版でも走らせる）。

## 未解決の判断

- 上の穴 3 つ——確認の Issue で利用者に渡す（閉じるのは利用者）。

## 起票

- この周の起票: 3 件（仕様の穴 3 つ——screen-spec の見つけ方・サインオフの前の確かめの形・req-loop が止まる結果——を `仕様の穴 = 推奨で決めて起票` の線で推奨により決めた確認の Issue。起票の承認は不在のため訊いていない）

## 直す線

`既定`（出所: cruise の台帳の確かめた線。不在の周）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1097-screen-gate`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1097`・起点 `d0a62f2`・base `origin/main` → `d0a62f2f008127a19d82573cf2eda2b8c73138c3`
- 割り目（手順 4）: 割らない（cruise の周）
- 実装のコミット: `a7ab627`（と計画の直し `68954a8`）
- 1 パス目の指摘対応の起点: `68954a8`（1 パス目の関門に渡した時点の HEAD）
- check-all（`68954a8`。run-serial 越し）: 86/86 本・失敗 0
- Verifier 1 パス目: 通した——反証 1 件（R1。dev-loop:dev-loop-verifier・sonnet。verifier.md 185 行を報告、wc -l と一致。テストは run-serial の枠が埋まって走らせられず、変異は未確認と報告）
- `/code-review` 1 パス目: 通した——指摘 10 件（CR1-1〜CR1-10。high。委譲文は貼ったが、届いたのはレビューの途中だった——報告は受入基準の番号で書かれている）
- 手順 4 への差し戻し: あり（採否の表の「直す」: R1・CR1-1・CR1-4）
- 割り目（手順 6・2 パス目の前）: 割らない（cruise の周）。残っているのは手順 5 の当て直しと手順 6 の 2 パス目の両方
- 手順 4 の途中の事故: 委譲文を組む Bash のヒアドキュメントを引用符なし（`<<EOF`）で書き、本文のバッククォートがコマンド置換として走った——`claude plugin eval` がメインの作業ツリーで走って約 $1.4 を課金し `evals/results/` を作った（止めて、作った `evals/` を消した。scaffold は走らず `git config` は変わっていない）。`claude -p` は入力が無く失敗、`gh` は使い方を出しただけ。以後は `<<'EOF'` で書く

## 既知の限界・決着済みの論点

- req-loop の画面の検査の起票・PPTX のリンク（#1100）、scaffold の `refs`・feasibility（#1099）、MkDocs のフック（#1098）はこの周の外。
- screen-spec の版（spec-loop が対応する screen-spec の版の範囲）は見ない——screen-spec の側が spec-loop の版を見る（#1110）。逆向きの範囲は #1081 に無い。
- `check-spec-exit.py --docs` の `docs` と、引数の重ねた全体（`build/merged`）が同じ正本から作られたかは見ない——スキルは同じ `docs` から作った直後に呼ぶ。
- 本物のプラグインの記録から screen-spec を見つける経路は未証明（上）。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1: `spec-scope.md` が profile の項目を「screen-spec の決まり」と書くが、screen-spec 0.1.0 に profile の決まりは無い | 示せる（`grep` で screen-spec に「ディープリンク」「画面幅」が無い） | U7（書かれた内容が事実と合う） | 直す——#1081 の案で、screen-spec はまだ持たない（#1094）と書く |
| CR1-1: `test-scaffold.py` が環境を丸ごと渡し、`SPEC_LOOP_SCREEN_SPEC` を設定したシェルでは「screen-spec が見つからない」の試料が通らない | 示せる（code-review の再現） | U2（の証明が利用者の環境で変わる） | 直す——生成のコマンドの環境から `SPEC_LOOP_SCREEN_SPEC`・`CLAUDE_CONFIG_DIR` を外す |
| CR1-2: `--red-check`・`--check` も画面の関門を通るので、製品のリポジトリで screen-spec が要る | 示せる（読解。成果物の表の関門と同じ条件） | 無し（関門は計画のとおり成果物の表の関門と同じ条件） | 残課題 |
| CR1-3: `scaffold.py` に `--screen-spec` が無い（環境変数・隣・キャッシュでしか渡せない） | 示せる | 無し（止まる側に倒れる） | 残課題 |
| CR1-4: 表を持たない `requirements/screens/`（ワイヤーフレームだけ）でも画面の表とみなし、screen-spec が無ければ止まる（screen-spec は「画面の表が無い」で 0） | 示せる（code-review の再現: rc=4） | U1（画面の表の無い正本で出力が変わる） | 直す——3 つの表のどれかがあるときだけ画面の表と見る（`merge-versions.py` の `ROW_TABLES` を読む） |
| CR1-5: キャッシュの記録の `local` の範囲・シンボリックリンクの `projectPath` を読まない | 示せない（記録の形を測っていない。screen-spec 側と同じ写し） | 無し（止まる側） | 残課題 |
| CR1-6: `check()` のたびに `check-spec-exit.py` を読み込み直す（読み込みが循環する） | 示せない（失敗は無い。重さだけ） | 無し | 残課題 |
| CR1-7: 呼ぶ側が重ねた全体を持っているのに重ね直す | 示せない（重さだけ） | 無し | 残課題 |
| CR1-8: `sys.dont_write_bytecode = True` が読み込んだ側のプロセス全体に効く | 示せる（読解） | 無し（書かない向き） | 残課題 |
| CR1-9: 印を数える拡張子の比べが大文字小文字を区別する（`ORDER.MD`） | 示せる（合成の試料） | 無し（まれな書き方） | 残課題 |
| CR1-10: コミットメッセージが `Refs #1097` で `Fixes` でない | 示せない（PR の本文に `Fixes #1097` を書く。cruise の親がマージする） | 無し | 残課題（捨てる候補） |
