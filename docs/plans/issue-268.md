# Issue #268 — spec-loop: 正本リポジトリの図はアスキーで描かず drawio（ソース＋書き出し）にする

spec-loop のスキルが正本リポジトリの文書に図を書くとき、アスキーアート（コードブロックの矢印と罫線）で描かず、
drawio のソースと書き出した画像で描く決まりにする。書き出しのスクリプトをプラグインに同梱する。

**不在の周**である——出所は `/dev-loop:cruise 793 --absent` の起動（2026-11-03）。親からサブエージェントとして委ねられた。
台帳 `issue-793` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・`周の途中の課題 = 外に出す`
（出所: cruise の確かめた線（台帳 `issue-793`）——利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））。
台帳は書かない（親が書く）。マージしない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `spec-loop` を **minor**（能力の追加——書き出しのスクリプトと図の決まり）。main の先端 0.46.0 → **0.47.0**
（PR を出す前・マージの直前に main が進んでいたら、取り込んで main の先端から minor で上げ直す）。

重い検査（`check-all.py`・テスト）は順番待ち越しに走らせる:
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py -- <コマンド>`。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/render-diagrams.py` — 新規。drawio を SVG に書き出し、ソースの指紋を書き出しに書き込む。`--check` で鮮度を見る
- `scripts/test-render-diagrams.py` — 新規。偽の draw.io CLI で回す回帰テスト（変異テストを含む）
- `scripts/check-all.py` — 回帰テストの登録
- `.github/workflows/plugins.yml` — 回帰テストのステップ
- `plugins/spec-loop/references/tree.md` — 「図」の節（置き場所・形式・描かないもの・書き出し・確かめ方）。「仕様書」の「#268 で決める」を直す
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 守ることに 1 項・版
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 同上
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 同上
- `plugins/spec-loop/skills/proposal/SKILL.md` — 同上
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 版の 2 行だけ
- `plugins/spec-loop/README.md` — スクリプトの表と使い方に 1 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `CLAUDE.md` — プロジェクト構成の一覧に `render-diagrams.py` と `test-render-diagrams.py`
- `docs/plans/issue-268.md` — この計画ファイル

触らない:

- `plugins/spec-loop/scripts/build-proposal.py` — 既に `spec/`・`requirements/` の `.svg` を載せ、`.svg` の無い `.drawio` を「載せていない」と書く（#371）。
  同じ名前の `.svg` を書き出せば、そのまま載る。変えない
- `plugins/spec-loop/templates/mkdocs/`・`init-mkdocs.py` — 雛形に足さない（下の仕様の穴 5）。MkDocs は `docs/` の `.svg` をそのまま配る
- `plugins/spec-loop/scripts/qa-to-pptx.py` — PPTX に図を載せる（PNG）こと。Issue に無い機能として残す
- このリポジトリの `diagrams/`・`scripts/export-diagrams.py`・`check-diagram-freshness.py` — 正本リポジトリの話ではない。drawio のファイルをリポジトリに足さない（未登録の drawio は CI で落ちる）
- `scaffold` スキルの守ること（文書に図を書かない）

### 同じことを述べている箇所の数

「図は drawio で描いて書き出す」を述べるのは 6 箇所——`references/tree.md` の「図」（原本）・4 つのスキルの守ること（tree.md を指すだけ）・README の表の 1 行。
スクリプトの振る舞い（終了コード・何を守り何を守らないか）は `render-diagrams.py` の docstring 1 箇所に置き、tree.md と README はそこを指す。
分けない理由: 決まりの原本を `references/` に 1 つ置き、スキルは指すだけにする既存の形（`signoff-tags.md` を指す守ることと同じ）。

## 乗るデプロイ経路

main へのマージで、プラグインの配布（spec-loop 0.47.0）と公開サイトの再ビルド（`docs/plans/` のこの計画ファイルだけ）。マージは親がする。

## verify の受入基準

### 検証で証明できるもの

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | `render-diagrams.py` は `<根>/docs/` の下（入れ子を含む）の `.drawio` をすべて、同じ場所・同じ名前の `.svg` に書き出し、書き出しは SVG として読め、ソースの指紋の印を持つ | 入れ子のディレクトリ・複数のファイル・空白を含む名前・`DRAWIO` の差し替え・macOS の既定のパス・`PATH` の `drawio` | 実機: macOS の draw.io で試料の `.drawio` を書き出し、SVG として読めて印があり、画面で開いて図が出ることを見る。テスト: 偽の CLI |
| A2 | draw.io の CLI が見つからなければ、何も書かずに終了コード 2 で「書き出していない」と言い、書き出していない `.drawio` を名指しする | `DRAWIO` が空・存在しないパス・既定のパスも `PATH` にも無い | テスト（`PATH` を絞った偽の環境）・変異 |
| A3 | 書き出しに失敗したら（CLI が 0 以外・出力が無い・SVG でない・時間切れ）、前の `.svg` を消さず書きかけも残さず、そのファイルを名指しして終了コード 1。ほかのファイルは書き出す | 各失敗の形・前の `.svg` が在る／無い | テスト（偽の CLI で失敗を作る）・変異 |
| A4 | `--check` は draw.io を起動せず、どの `.drawio` にも、印の指紋が今のソースの指紋と一致する `.svg` があるときだけ 0。書き出しが無い・印が無い・古い・ソースの無い印つきの `.svg` を名指しして 1。何も書かない | 各形・`docs/` が無い・`.drawio` が 0 件 | テスト・変異。実機でソースを 1 文字直して `--check` が 1 になる |
| A5 | 印はソースのバイトだけで決まる——同じソースを書き出し直しても、書き出しのバイトが変わっても `--check` は 0 | 書き出しのたびにバイトが変わる draw.io（CLAUDE.md の実測） | 実機で 2 回書き出して両方 `--check` 0。テスト |
| A6 | 書き出した `X.svg` は `build-proposal.py` の仕様書の図に載り、`X.drawio` は「載せていない」に出ない | `spec/`・`requirements/` の中 | `build-proposal.py` の図の選び方の関数に、書き出したあとのパスの一覧を渡して確かめる |
| A7 | 決まりの文書: `tree.md` に「図」の節があり（置き場所・形式・アスキーアートと Mermaid で描かない・生成する図は対象外・書き出し・確かめ方）、4 つのスキルの守ることがそこを指し、`tree.md` の「#268 で決める」が消え、README と CLAUDE.md にスクリプトが載る。指し先が実在する | スキルの指し先・散文の指し先 | `check-skill-pointers.py`・目視 |
| A8 | 版が 3 種類（`marketplace.json`・`plugin.json`・5 つの `SKILL.md` の 2 行）で 0.47.0 にそろい、回帰テストが `check-all.py` と CI に登録され、歯止めが全部緑。PR 側の CI が緑 | 登録漏れ・版の不一致 | `check-all.py`（順番待ち越し）・`gh pr checks` |
| A9 | 回帰テストは、要の行（印の照合・見つからないときの 2・失敗のときに前の `.svg` を残す・`--check` で書かない）を壊すと赤になる | 変異 | テストの変異と陽性対照 |
| A10 | 書き出しで書くのは `.drawio` の隣の `.svg`（と同じ場所の一時ファイル。成否に依らず消す）だけで、`docs/` の外と他のファイルを変えない | 一時ファイルの置き場所・失敗の経路 | テスト（実行の前後でツリーを比べる） |

必須要件の掛け算: 受入基準を 2 つの関門（Verifier・`/code-review`）× 2 パス（1 パス目・2 パス目）= 4 つの受け渡し（2 パス目が該当なしなら 2 つ）。

### この環境では証明できないもの（未証明）

- U1: Linux・Windows の draw.io の CLI での書き出し——確かめられるのは macOS の draw.io だけ（このリポジトリの `export-diagrams.py` と同じ限界）。
- U2: 書き出した図の見た目が利用者・決裁者に見せられる品質か——画面で 1 枚見るだけで、品質の判定は人間のレビュー。

### 生成物

該当判定: この周は生成物を足さない。このリポジトリの `diagrams/exports.json`（drawio を足さない）・設計ドキュメント §8.2 の生成ブロック（dev-loop の `SKILL.md` を触らない）は動かない——
`check-all.py` の `check-diagram-freshness.py`・`skill-metrics.py --check` で変わらないことを確かめる。

## 仕様の穴（不在の線で推奨により決めた）

出所: cruise の確かめた線 `仕様の穴 = 推奨で決めて起票`（台帳 `issue-793`）。Issue は spec-loop から来ていない（本文に印が無い）。

| # | 穴 | 選択肢 | 決めた値 | 推した理由 | 確認の Issue |
| --- | --- | --- | --- | --- | --- |
| G1 | 書き出しの形式 | SVG ／ PNG（Issue の例） | **SVG** | 仕様書の生成（`build-proposal.py`）は `.svg` だけを載せる。MkDocs もそのまま出せ、拡大で崩れない | （起票後に書く） |
| G2 | 図の置き場所 | 使う文書と同じディレクトリ（版の中） ／ `docs/assets/diagrams/`（Issue の例） | **使う文書と同じディレクトリ** | 仕様書は `spec/`・`requirements/` の図を拾い、2 つの承認の照合も `shared/`・`requirements/`・`spec/` を比べる。版の外に置くと図が承認の比べる範囲と版の重ね合わせから外れる | （同上） |
| G3 | Mermaid も描かない対象にするか | 対象にする ／ しない | **対象にする** | 仕様書・PPTX に持っていけない。MkDocs の雛形は Mermaid を描く設定を持たない。このリポジトリも #40 で dev-loop の図を Mermaid から drawio に描き直した | （同上） |
| G4 | 書き出しの鮮度の検査 | 書き出しにソースの指紋を書き込み `--check` で照合 ／ 検査しない ／ 別の表（マニフェスト）に指紋を持つ | **書き出しに指紋を書き込む** | draw.io は同じソースからでもバイトが一致しない（CLAUDE.md の実測）のでバイト比較は使えない。表を別に持つと手で書く誘惑と 2 か所の同期が増える。`--check` は draw.io 無しで CI でも回る | （同上） |
| G5 | MkDocs の雛形に何を入れるか | 何も足さない（スクリプトはプラグインから走らせる） ／ 書き出しのスクリプトを正本へ写す | **何も足さない** | 写したスクリプトは新しい版が届かない（フックで既に起きている形。tree.md の「既に雛形を写した正本には、新しい雛形は届かない」）。MkDocs は `docs/` の `.svg` を設定なしで出す | （同上） |

決めた値は 2 つの関門に「穴の記録」として渡す。**受入基準は足さない。**

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/268-spec-loop-drawio-diagrams`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-268`・
  起点 `896667d2`・base の参照 `origin/main`（`refs/remotes/origin/HEAD`）・base の SHA `896667d2ba7d28a8e417e185e75e9479bfc25918`
- 手順 4 の割り目: 割らない（不在の cruise。訊かずに続けた）。実装は実装役（`b625488e`）。実装役の `check-all.py`: 59/59（失敗 1 = `check-plan-counts.py`、計画ファイルの件数の行が無い——親が足した）
- Verifier: 1 パス目 済（sonnet・`dev-loop:dev-loop-verifier`。反証 0 件。A1〜A10 一致、PR 側 CI は未確認）・2 パス目 済（sonnet。反証 1 件——孤立した `.SVG`（大文字）を `--check` が見ない。テストは順番待ちで走らせられなかったと申告）
- `/code-review`: 1 パス目 済（high。指摘 7 件——直す 3・残課題 4。下の採否の表）・2 パス目 済（high。指摘 10 件——直す 4・残課題 6）
- 1 パス目の指摘対応の起点の SHA: `a2363d4fae6fdc2d6ee7bb4a2b2bd0c6e6d31d99`（1 パス目の 2 つの関門に渡した時点の HEAD）
- 狭いパス: 起点 `f17bbe64fbd049803d8ffa8c7660bfe5f0fbc623`（2 パス目の指摘対応の直前）・終点 `bd1e452447f69f707ee2a1ef19ed0f4fca1e1286`。Verifier 済（sonnet。反証 1 件・素通りの変異 2 本——下の採否の表 N-1〜N-4。採否は人間が決める）。1 パス目の後の check-all（f8473325 の上、python3.12 の test-render-diagrams も）: 59/59 失敗 0
- 反証と差し戻し: 1 パス目の指摘 3 件を直した（`f8473325`）。差し戻しは手順 4 の範囲内（`触る:` に収まる）
- 2 パス目の前の割り目: 割らない（不在の cruise。訊かずに続けた）。残っているのは手順 5 の当て直しと `/code-review` 2 パス目の両方
- 交絡を潰した手順: A5 は実機の 2 回の書き出しのバイトが違うこと（Verifier の `cmp`）を確かめたうえで `--check` 0 を見た（バイトが同じなら判別しない）。CR2 の孫の試料は、直す前の形（グループを止めない変異）で赤になることを陽性対照にした

## 既知の限界・決着済みの論点

- 書き出すのは各 `.drawio` の 1 ページ目だけ（draw.io の CLI の SVG の既定）。複数ページの図は docstring の「守らない」に書く。
- 印を手で書き換えて書き出さない形は見えない（このリポジトリの `check-diagram-freshness.py` と同じ原理的な限界）。
- ディレクトリの一覧（ツリー）や表はテキストのままでよい——描かない対象は、構成・流れ・関係を矢印と罫線で描く図。
- 生成する図（ガントチャート・仕様書の `spec-figure-NN.svg`）は対象外。

### 採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1 実行のたびに全部の `.drawio` を書き出し直し、draw.io のバイトが揺れるので、凍結した版・承認済みの `.svg` まで書き換わる（`check-frozen.py`・`check-signoff.py` が落ちうる） | 示せる（/code-review が本物の draw.io で 2 回書き出し、SHA が変わった） | 無し（A1〜A10 は「新しい書き出しを飛ばす」を求めていない） | 残課題（利用者に見える誤り。PR コメントの起票の候補） |
| CR1-2 時間切れで直接の子だけを止め、前置き（`xvfb-run`）の孫が後から一時ファイルを書く | 示せる（孫が 8 秒後に書く偽の CLI。試料「時間切れのあとで孫が書かない」） | A3・A10 | 直す（`f8473325`。プロセスグループで起こして止める） |
| CR1-3 `.DRAWIO`（大文字）を見ず、`build-proposal.py`（区別しない）と食い違う | 示せる（`Arch.DRAWIO` で 0 件と言う） | A1・A6 | 直す（`f8473325`） |
| CR1-4 `DRAWIO` の前置きの形で、後ろの drawio が無いとき 2 にならない・閉じない引用符で名指ししない | 示せない（偽の前置きが忠実でない、と関門自身が書いている）／閉じない引用符は実際の利用でまず起きない | 無し | 残課題 |
| CR1-5 docstring の「空なら 2」が探す順の 2 番目と読める | 示せる（文言） | 無し | 残課題（文言） |
| CR1-6 `tree.md` の理由「仕様書と PPTX に持っていけない」の PPTX の半分が誤り | 示せる（同じファイルの「仕様書」の節が図を PPTX に載せないと書く） | A7（原本の文の真偽） | 直す（`f8473325`） |
| CR1-7 版の外（`docs/assets/`）の図を `--check` が咎めない | 示せる（`docs/assets/x.drawio` で 0） | 無し（G2 は置き場所の決まりで、検査は受入基準にない） | 残課題 |
| CR2-1 `start_new_session` のせいで、本体が SIGHUP・SIGTERM（端末を閉じた・グループへの送信）で止められると CLI が生き残り、後から一時ファイルを置く（1 パス目の修正が持ち込んだ後退） | 示せる（関門が再現。試料「SIGHUP で止められても CLI が後から書かない」） | A3・A10 | 直す（`bd1e4524`。SIGTERM・SIGHUP を例外にして後始末を走らせる） |
| CR2-2 `os.killpg` の無い OS（Windows）で毎回 AttributeError になり 1 件も書かない（1 パス目の後退） | 示せる（`del os.killpg` で模した実行。試料「killpg の無い OS」） | A1 | 直す（`bd1e4524`） |
| CR2-3 孤立の判定が大文字小文字を区別し、区別しないファイルシステムで本物の書き出しを「ソースが無い」と言う（1 パス目の後退） | 示せる（関門が macOS で再現。試料） | A4 | 直す（`bd1e4524`） |
| CR2-4 macOS では大文字小文字の修正の孤立の半分をテストが判別しない | 示せる | 無し（A9 の要の行に入らない） | 残課題（CR2-3 の試料と変異で埋まった） |
| CR2-5 CR1-1（書き出し直しで凍結した svg が揺れる）を残課題にした理由が誤り | 示せる（CR1-1 と同じ） | 無し（決着の理由は「受入基準を破らない」で、それは誤っていない） | 残課題（CR1-1 と同じ。マージの前に人の判断を求める） |
| CR2-6 tree.md「書き出してから proposal を回す」が不足——仕様書はタグの時点の中身を読むので、承認の前に commit が要る | 示せる（`build-proposal.py` がタグの時点の `git ls-tree` から図を拾う） | A7（原本の文の真偽） | 直す（`bd1e4524`） |
| CR2-7 時間切れのあとの 2 回目の `communicate` に時間切れが無く、`setsid` した補助がパイプを持つと止まらない | 示せない（実際の利用でまず起きない） | 無し | 残課題 |
| CR2-8 正常の経路でも `killpg` するので、pid が再利用されると無関係なグループを止めうる | 示せない（理論上） | 無し | 残課題 |
| CR2-9 `DRAWIO_TIMEOUT=inf` が想定外の例外で 2 | 示せる | 無し | 残課題（実際の利用でまず起きない） |
| CR2-10・V2-1 孤立した `.SVG`（大文字）を `--check` が見ない | 示せる | 無し（A4 の経路に大文字の `.svg` は無い） | 残課題（実際の利用でまず起きない） |
| N-1（狭いパス）SIGHUP の handler を無条件に登録するので、`nohup` で（SIGHUP を無視して）起動した実行が SIGHUP で止まるようになった（CR2-1 の修正が持ち込んだ後退） | 示せる（新版 rc=129・書き出し無し／f17bbe64 は rc=0・書き出しあり） | 無し（A1 に `nohup` の経路は無い） | 人間が決める |
| N-2（狭いパス）SIGTERM の経路を判別する試料が無い（「SIGTERM を登録しない」変異が素通り。試料の送信を SIGTERM にした陽性対照では赤） | 示せる | 無し（A9 の要の行に入らない） | 人間が決める |
| N-3（狭いパス）`killpg` の無い OS の `proc.kill()` を外す変異が素通り（試料は正常終了の経路だけで、等価変異に近い） | 示せない（陽性対照なし） | 無し | 人間が決める |
| N-4（狭いパス・参考）大文字小文字を区別するファイルシステムで、`a.drawio` があると印つきの孤立した `A.svg` を見逃す（CR2-3 の副作用。コード読みのみ） | 示せない（未実験） | 無し | 人間が決める |

## 経験の還元（手順 8）

- この周の起票: 5 件（仕様の穴 G1〜G5 の確認の Issue。起票の承認は不在のため訊いていない）
