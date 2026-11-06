# Issue #901 — BPMN を SVG に書き出し、指紋を書き込み、--check で鮮度を確かめる

不在の周（`/dev-loop:cruise 903 --absent` の起動・2026-11-06T08:55Z、利用者の確認（起動時・2026-11-06T08:55:51Z、配布を見せて確かめた））。cruise #903 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かず「このまま続ける」）。従う版は dev-loop 1.99.0（キャッシュ。SKILL.md 1861 行）。
#896 の期待 2 を分けた子 Issue（前の周 #900 が線を足し、次の周 #902 が仕様書に載せる）。

- 直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-903`）——上の起動）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #903 -->`）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認・マージ前の判断: 台帳に線なし（止まる）
- 版の上げ方: **minor・spec-loop だけ**（main の先端 spec-loop 0.69.0 → 0.70.0。BPMN の書き出しを足す——能力の追加）。dev-loop は触らない。
  マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #901`・`Refs #896`（#896 は #902 の PR で閉じる）・`Refs #903`
- 並行する周: #897（dev-loop の版を上げる）——その worktree・ブランチには触らない
- 重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.99.0/skills/cruise/scripts/run-serial.py` 越し

## 周の在り処

- ブランチ: `issue/901-bpmn-render`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-901`
- 起点コミット: `a3c83c3`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `a3c83c34dca9f9784e085109b011092fed5f6b4e`

## 変更範囲

触る:
- `plugins/spec-loop/scripts/render-diagrams.py` — `.bpmn` を対象に足す・BPMN の描画口の探し方・同じ書き出しになるソースで止まる・`.svg` の拾い方の大文字小文字（#904 の残課題 P2-5）・docstring
- `plugins/spec-loop/scripts/render-bpmn.mjs` — 新規。BPMN の既定の描画口（bpmn-js を puppeteer-core と headless の Chrome で動かす）
- `scripts/test-render-diagrams.py` — BPMN の試料・変異
- `plugins/spec-loop/references/tree.md` — 「図」の「業務フロー（BPMN）」を、書き出しが入った形に書き直す（「まだ同梱していない」を外す）。ツリーの `flows/` の行・「仕様書」の指し 1 文
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 図の文言（「まだ同梱していない」を外す）・版の 2 行
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 同上
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 同上
- `plugins/spec-loop/skills/proposal/SKILL.md` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（autopilot・scaffold）
- `plugins/spec-loop/README.md` — スクリプトの表と「図を書き出す」
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `CLAUDE.md` — `render-diagrams.py` と `test-render-diagrams.py` の行
- `docs/plans/issue-901.md` — この計画

触らない:
- `plugins/spec-loop/scripts/build-proposal.py`・`scripts/test-build-proposal.py` — 書き出しの無い `.bpmn` を「載せていない」と名指しするのは #902（範囲の外）
- `tree.md` の「仕様書」の表の「構成の図」の行——`build-proposal.py` の今の振る舞い（#902 で変える）
- 0.68.0 までに drawio で描いた業務フローの移行（#904 の残課題 P2-2）——壊れるものが無く、Issue の範囲に無い
- CI の定義（`.github/workflows/`）——テストは既に `test-render-diagrams.py` を回している。Node・Chrome は CI に入れない
- dev-loop のプラグイン・公開ページ（`docs/plugins/`。spec-loop の図の決まりを持たない——`git grep render-diagrams docs/` で 0 件）

複製の数（同じことを述べている箇所）: BPMN の書き出しの扱いは **7 箇所**（`tree.md` の「業務フロー（BPMN）」が原本、
4 スキルの `SKILL.md` の 1 行と `README.md` の「図を書き出す」が要約して `tree.md` を指す。スクリプトの docstring が描画口の探し方・終了コードの原本で、
`tree.md` はそこを指す）。`CLAUDE.md` の 2 行はファイルの説明で、規範を持たない。
**分けない理由**: #900 と同じ——スキルの本文は起動したときに読むので 1 行の要約を残し、細部は `tree.md` と docstring にだけ書いて指す。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージでプラグインのカタログに入る。マージは親。

## 設計（この周で決めたこと）

Issue が「この周で決める」とした 2 つと、それに伴う判断。どれも Issue が委ねた選択で、仕様の穴ではない:

- **`render-diagrams.py` を広げる**（別のスクリプトにしない）——印・`--check`・ソースの無い書き出しの判定・失敗の扱い（前の `.svg` を変えない）を 1 つにし、
  `--check` を 1 本で回せるようにする。描画だけを種類で分ける（`.drawio` は draw.io の CLI、`.bpmn` は描画口）。
- **書き出しは SVG だけ**（PNG は出さない）——仕様書（`build-proposal.py`）が載せるのは `.svg` だけで、PNG は鮮度の印を持てない（バイナリ）。
- **描画口**: 同梱の `render-bpmn.mjs`（`node render-bpmn.mjs --deps <依存> --chrome <Chrome> <入力> <出力>`）。依存（bpmn-js・puppeteer-core）は
  プラグインに同梱できない（`node_modules`）ので、利用者が正本リポジトリの外で `npm install` したディレクトリを `SPEC_LOOP_BPMN_DEPS` で渡す。
  Chrome は `CHROME_PATH`、無ければ macOS の既定の場所。描画口ごと差し替える `BPMN_RENDER`（テストはこれで偽物を差す）。
- **無いときは何も書かずに名指しで止まる**——draw.io の CLI と同じ形。**どちらかの描画系が無ければ、両方の種類とも 1 件も書かない**（一部だけ書いて止まる形を作らない）。
  無いもの（Node・依存・Chrome・描画口）は全部まとめて名指しする（1 つ直すたびに次が出る形にしない）。
- **読み込みの警告（bpmn-js の `importXML` の warnings）があれば失敗**——描けなかった要素を落とした図を書き出さない。
- **同じ `X.svg` になるソース（`X.drawio` と `X.bpmn`）は、書き出しでも `--check` でも何も書かずに 2**——片方の書き出しがもう片方を黙って上書きする。
- **#904 の残課題 P2-5 を拾う**（`find_svgs` が `.svg` の大文字小文字を区別し、docstring の「区別しない」と食い違う）——この周が同じ関数を触るので。
- **#904 の残課題 CR-6（要求の文書から業務フローの図をどう指すか）を 1 文で拾う**——`tree.md` に「文書からは `flows/<名前>.svg` を指す」。書き出しの置き場所を決めるこの周の範囲に入る。

## 受入基準（不変条件 × 経路）

不変条件:

- **I1** `docs/` の下の `*.bpmn` が隣の同じ名前の `.svg` に書き出され、ソースのバイトの sha256 の印が書き出しに入る（drawio と同じ印）
- **I2** `--check` は描画系（draw.io・Node・Chrome）を起動せず何も書かずに鮮度を見て、ソースを直して書き出していない・書き出しが無い・印が無い `.bpmn` を名指しして非 0
- **I3** Node・Chrome・bpmn-js（と puppeteer-core・描画口）が無いとき、何も書かずに無いものと書き出していないソースを名指しして止まる（2）
- **I4** 回帰テストは偽の描画口を差して回し、本物の Chrome・Node に届かない。変異テストを含む
- **I5** 本物の描画で、Camunda Modeler で開ける BPMN（collaboration・participant・laneSet と BPMNDI の座標つき）1 枚を書き出せたことを手元で 1 回確かめ、この計画ファイルに残す
- **I6** spec-loop の版を上げ（3 箇所）、`check-all.py` が通る
- **I7**（後退させない）drawio の書き出し・`--check`・失敗の扱い・シグナルの扱いの既存の振る舞いが変わらない（既存の試料と変異が全部通る）
- **I8**（後退させない）BPMN の描画口が失敗・時間切れ・SVG でない書き出しのとき、前の `.svg` を変えず、一時ファイルを残さない（drawio と同じ）
- **I9** 文書（`tree.md`・4 スキル・`README.md`・`CLAUDE.md`）が新しい振る舞いと食い違わない（「まだ同梱していない」が残らない）

経路（`render-diagrams.py` の入口から数える。差分からではない）:

| 経路 | 守り方 | 不変条件 |
| --- | --- | --- |
| 書き出し（引数なし）・`.bpmn` だけ | `find_sources` が `.bpmn` を拾い、`bpmn_command` で描画口を探す。draw.io の CLI は探さない | I1・I3 |
| 書き出し・`.drawio` と `.bpmn` の混在 | 両方の描画系を 1 件も書く前に探し、どちらかが無ければ 2 | I1・I3・I7 |
| 書き出し・入れ子・空白や日本語の名前・大文字の拡張子（`.BPMN`） | `os.walk`・`lower()` | I1 |
| `--check` | 描画系を探さない・起動しない | I2 |
| `--check` のソースの無い印つきの `.svg`（大文字の `.SVG` を含む） | `find_svgs` が `lower()` で拾う | I2 |
| `BPMN_RENDER`（差し替え・空・無いパス） | `bpmn_command` | I3・I4 |
| 既定の描画口（`node`・`SPEC_LOOP_BPMN_DEPS`・`CHROME_PATH`・既定の Chrome・`render-bpmn.mjs`） | `bpmn_command` が全部を見て無いものを全部返す | I3 |
| 時間切れ（`BPMN_TIMEOUT`）・正の数でない値 | `export_one` のグループごとの停止・`main` の検査 | I8・I3 |
| 描画口が 0 以外・SVG でない・何も書かない | `export_one` の成功の判定 3 つ | I8 |
| 同じ `X.svg` になるソース | `main` が先に止める（両モード） | I1・I2 |
| SIGHUP・SIGTERM・`nohup` | 既存のまま（描画口も同じ `export_one` を通る） | I7 |
| 仕様書（`build-proposal.py`） | 触らない。書き出した `.svg` は `requirements/` の `.svg` として今のまま載る（`tree.md` に書いた）。書き出しの無い `.bpmn` の名指しは #902 | I9 |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目に渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

**証明できるもの**: I1〜I4・I6〜I9（テスト・`check-all.py`・実際の書き出しで）。I5 のうち「Camunda Modeler の書く形（collaboration・participant・laneSet・BPMNDI の座標）の BPMN 1 枚を本物の描画で書き出せた」は手元で 1 回の実走（下の「実機確認」）。**I5 のうち「Camunda Modeler で開ける」は下の未証明**（基準は緩めない——人間のレビューに回す）。

**この環境では証明できないもの（未証明）**:
- `render-bpmn.mjs` の **Linux・Windows の Chrome**、bpmn-js・puppeteer-core の **ほかの版**での動き（確かめたのは macOS の Chrome と bpmn-js 18.6.2・puppeteer-core 24.10.0 だけ）
- **Camunda Modeler で開けること**そのもの——Camunda Modeler はこの手元に無い。I5 のソースは Camunda Modeler が書く形（`bpmn:`・`bpmndi:` の名前空間・collaboration・participant・laneSet・BPMNDI の座標）で手で書き、
  bpmn-js（Camunda Modeler と同じ描画部品）が警告なしに読み込んだことまでを確かめた

**生成物の該当判定**: 該当あり——`render-diagrams.py` 自身が生成物（`.svg`）を作る道具で、その鮮度の検査がこの周の成果物。
このリポジトリの生成物（`diagrams/exports.json` の図・設計 §8.2 の生成ブロック）は触らない——`check-diagram-freshness.py`・`skill-metrics.py --check` が `check-all.py` の中で見る。

## 実機確認（I5）

2026-11-06、このホスト（macOS・Node v26.8.2（`/opt/homebrew/bin/node`）・`/Applications/Google Chrome.app`）で 1 回確かめた。
依存は **既に在る taihei-carrot-revamp の `tools/bpmn`（bpmn-js 18.6.2・puppeteer-core 24.10.0。読むだけで、書き換えていない）** を
`SPEC_LOOP_BPMN_DEPS` で指した（利用者のグローバルな環境は変えていない。npm でも入れていない）。

- ソース: scratchpad の一時の正本リポジトリの `docs/v1/requirements/flows/受注.bpmn`（collaboration 1・participant 1「受注」・laneSet にレーン 2 本「顧客」「営業」・
  開始・タスク 2・終了・sequenceFlow 3 本・BPMNDI の座標つき。Camunda Modeler の書く形で手で書いた）
- `render-diagrams.py --check` → 1（「書き出しが無い」）→ `render-diagrams.py` → 0（「1 件書き出した」。0.9 秒前後）→ `--check` → 0
  → ソースのタスク名を 1 つ書き換え → `--check` → 1（「古い（ソース … を直したあと書き出していない）」）
- 書き出しの先頭: XML 宣言の直後に `<!-- spec-loop-diagram-source: sha256=9eadd8be… -->`——`shasum -a 256` のソースの指紋と一致
- 書き出しを Chrome で開いて撮った画像を目で見た——participant「受注」の中にレーン「顧客」「営業」、各レーンにタスクと開始・終了、矢印が描かれている
- `SPEC_LOOP_BPMN_DEPS` を外すと 2（「bpmn-js と puppeteer-core の場所が無い」と `受注.bpmn` を名指し、何も書かない）
- 時間切れ（`BPMN_TIMEOUT` 0.4〜0.55 秒で 6 回）のあと、headless の Chrome のプロセスは見えなかった（`pgrep -f headless` で 2 秒後に 0——ほかのアプリの 1 件を除く）。
  **著者のこの測り方には陽性対照が無い**（描画中に同じ `pgrep` が Chrome に当たることを見ていない）——1 パス目の `/code-review` が陽性対照つきで測り直し、
  描画口の起動 0.16 秒後に Chrome が見え、グループを SIGKILL して 2 秒後に消えたことを示した（消えたのは pipe が閉じたため。Chrome は別のプロセスグループ）。
  **puppeteer の一時のプロファイル（`$TMPDIR/puppeteer_dev_chrome_profile-*`）は残った**（著者は前後の数の差で 5、`/code-review` は時刻で 6 と数えた——前後の差は、ほかの描画が消したものと相殺しうる）——docstring の「守らないもの」に書いた

## 関門の進捗（再開点）

- 割り目（手順 4）: **割らない（cruise の周）**
- 1 パス目: 起点 `89f68cb`（1 パス目の関門に渡した時点の HEAD）。
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**（報告は `SubagentHandback` が届かず、`SendMessage` で取り直した。本物の描画・読み込みの警告で失敗する形・同じ書き出しで 2・`--check` の名指しを自分で走らせて一致）
  - `/code-review`（high）: **指摘 10 件**（CR-1〜CR-10）。直す 4 件（CR-1・CR-3・CR-4・CR-5）・計画ファイルの記録の直し 2 件（CR-6・CR-7）・残課題 4 件。採否は下の表
  - 手順 4 への差し戻し: なし（Verifier の反証 0）。指摘対応は 1 パス目の起点からの差分として 2 パス目に当てる
- 交絡を潰した手順: 実機確認の「Chrome のプロセスが残らない」に陽性対照が無かった（CR-6）——`/code-review` が陽性対照つきで測り直して主張が成り立つことを示した（描画口の起動 0.16 秒後に Chrome が見え、グループを SIGKILL して 2 秒後に消えた。Chrome は puppeteer が別のプロセスグループで起こすので、消えたのは pipe が閉じたため）

## 既知の限界・決着済みの論点

### 1 パス目の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR-1 `SPEC_LOOP_BPMN_DEPS` が相対パスだと事前の確かめを通り、各 `.bpmn` が `createRequire` で失敗する | 示せる——`SPEC_LOOP_BPMN_DEPS=deps python3 render-diagrams.py repo` → 「puppeteer-core を読み込めない（… absolute path string. Received 'deps/package.json'）」rc=1 | I1・I3 | 直す（`bpmn_command` で絶対パスにして渡す。Chrome も同じ） |
| CR-2 混在で draw.io だけが無い経路の試料が無い（`if reasons and bpmn is None:` の変異が生き残る） | 示せる（変異が全試料を通る）——ただしコードは正しい | 無し（I4 の「変異テストを含む」は満たす。この経路のコードは正しい） | 残課題 |
| CR-3 同じ書き出しの判定がパス全体を小文字にするので、大文字小文字を区別するファイルシステムで別のディレクトリ・drawio だけの `X.drawio` と `x.drawio` を止める | 示せる——大文字小文字を区別する APFS の一時のボリュームで `docs/A/x.drawio`・`docs/a/x.drawio`・`docs/X.drawio`・`docs/x.drawio` に `--check` → この PR は 2（「同じ書き出し」）、main の版は 1（書き出しが無いと名指し） | I7 | 直す（同じディレクトリで名前が大文字小文字まで一致するものだけを止める。大文字小文字だけ違う名前は止めず、docstring の「守らないもの」に書く） |
| CR-4 `BPMN_TIMEOUT` が不正だと drawio だけのリポジトリも止まる（逆も） | 示せる——`.drawio` だけで `BPMN_TIMEOUT=0` → 「BPMN_TIMEOUT が正の数でない」2。main は `BPMN_TIMEOUT` を見ない | I7 | 直す（その種類のソースがあるときだけ確かめる） |
| CR-5 docstring の「守るもの」の行が、BPMN でも「書くのは隣の `.svg` と一時ファイルだけ」「グループごと止める」と読める（Chrome は別のプロセスグループで `$TMPDIR` にプロファイルを書く） | 示せる——描画のたびに `$TMPDIR/puppeteer_dev_chrome_profile-*` ができる（時間切れで残った数を数えた）。`@puppeteer/browsers` の `launch.js` の `detached ??= process.platform !== 'win32'` | I9 | 直す（docstring の行を drawio と BPMN で書き分ける） |
| CR-6 計画ファイルの「Chrome のプロセスは残らなかった」に陽性対照が無い・残ったプロファイルの数が違う（5 と 6） | 示せる（記録に陽性対照が無い） | 無し（計画ファイルは成果物でない。主張そのものは `/code-review` の陽性対照つきの測り直しで成り立つ） | 計画ファイルの記録を直す（上の「交絡を潰した手順」と「実機確認」） |
| CR-7 I5 を「証明できるもの」に数えつつ、「Camunda Modeler で開ける」を未証明にしていて食い違う | 示せる（計画ファイルの 2 箇所） | 無し（計画ファイルの書き方） | 計画ファイルの記録を直す（I5 のうち測ったものと未証明を分けて書く。基準は緩めない） |
| CR-8 `CHROME_PATH` の実行ビットの確かめを外す変異が生き残る | 示せる（変異が全試料を通る）——コードは正しい | 無し | 残課題 |
| CR-9 `.bpmn` ごとに Node と Chrome を起こすので、図の数に比例して遅い | 示せない（30 枚の実測は無い。1 枚 0.9 秒） | 無し | 残課題 |
| CR-10 `executable()` と `drawio_command` の判定が重複している | 示せない（振る舞いの差は無い） | 無し | 残課題 |

- **`render-bpmn.mjs` は回帰テストで走らない**——CI に Node・Chrome・bpmn-js が無く、テストは本物に届かない形を受入基準（I4）が求める。描画口の引数の形は偽の `node` で見る。決着: 採った（docstring の「守らないもの」）
- **Chrome の一時のプロファイルが時間切れで残る**——描画口を SIGKILL で止めるため。決着: 採らない（drawio と同じグループごとの停止を保つ。記録だけ）

## 経験の還元（手順 8）

- この周の起票: 0 件（cruise の不在の周。振り分けで直すに入った課題なし——マージの前に親が台帳で見直す）
