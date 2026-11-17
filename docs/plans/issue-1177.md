# Issue #1177 — spec-loop: 保存した TLA+ のモデルを、利用者の言葉の状態遷移図にレンダリングする段

**不在の周**（`/dev-loop:cruise 1169 --absent` の起動・2026-11-17T10:47Z）。利用者には訊かない。親（cruise #1169）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1169`）。利用者の確認（起動時・2026-11-17T10:47:55Z、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`（古い値。後退・未達は推奨で進めない）。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1169.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.7.0（`SKILL.md` 1920 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1169`））。
版の上げ方: `spec-loop` を **minor**（スクリプトと手順を足す——CLAUDE.md の「能力・手順の追加」）。着手時の main は spec-loop 0.105.0 → 0.106.0。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.7.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: 保存したモデル（`spec/formal/<対象>/`）を TLC（`-dump dot,actionlabels`）で展開し、利用者の言葉のラベル（ビュー）を付けた状態遷移図（Mermaid か SVG）を 1 コマンドで出す。
不変条件を破る状態に印を付け、反例のトレースを経路として描く。図と TLC の状態グラフが食い違わないことを回帰テストで見る。spec-review が反例を Q&A 表に起票するとき、図へのリンクを質問に付ける。
本文に受入基準を緩める指示は無い（コメントは無い）。

**依存する周 #1178 への申し送り**: この周は `plugins/spec-loop/references/tree.md` の「形式検査のモデル」の節（記録の項目の表に 2 行足し、節の終わりに「状態遷移図」の段落を足す）と、
`plugins/spec-loop/scripts/formal-baseline.py` の `ITEMS`・`OPTIONAL`・`check` の一覧の項目を変える（下の「変更範囲」）。#1178 は同じ表に項目を足すので、この周のマージの後に取り込む。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **H1 図の置き場所**: (a) 生成した図（Markdown の中の Mermaid）を `spec/formal/<対象>/statechart.md` に置いて commit し、記録（`README.md`）の新しい項目 `状態遷移図のファイル` に名前を書く（推奨）／
  (b) `build/formal/` に書いて commit しない（質問には作り直すコマンドを書く）。
  推した理由: Q&A 表の質問に付けるリンクが、TLC を持たない利用者にも GitHub の上で開ける（GitHub は Markdown の中の Mermaid を描く）。(b) はリンク先が誰の手元にも無く、見るのに TLC が要る。
  `spec/formal/` は承認の照合・版の差分・提案書から外れている（`is_formal`）ので、図を置いても承認の範囲は変わらない。
- **H2 ラベルの対応（ビュー）の置き方**: (a) 対象のディレクトリに JSON（`view.json`）を置き、記録の新しい項目 `図の対応のファイル` に名前を書く（推奨）／(b) `README.md` の記録の表の中に書く。
  推した理由: 対応は「変数の値 → 状態の言葉」と「行為 → 操作の言葉」の入れ子の対応で、2 列の表のセルに入れると読む側が書式を新しく決める必要がある。JSON なら標準ライブラリで読め、
  `formal-baseline.py check` の「一覧のファイルだけが在る」の決まりのまま残せる。

決着（穴ではない）: 図は **Mermaid**（Issue が「Mermaid か SVG」と認める。外の道具が要らず、正本のリポジトリで描ける）。大きいモデルは Issue の目安どおり**遷移 20 本超で反例までの経路だけ**（`--max-edges` で変えられる。反例が無ければ全部を描き、そう書く）。
決めた値は受入基準を足さない（手順 3 の受入基準は下のとおり固定）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/formal-statechart.py` — 新規。保存したモデルを TLC で展開し、ビューで状態遷移図（Mermaid）にする
- `scripts/test-formal-statechart.py` — 新規。回帰テスト（本物の TLC 2.19 で取った試料を埋める・偽の TLC・変異）
- `plugins/spec-loop/scripts/formal-baseline.py` — 記録の項目に `図の対応のファイル`・`状態遷移図のファイル`（任意）を足し、一覧のファイルに数える
- `scripts/test-formal-baseline.py` — 新しい項目の試料と変異
- `plugins/spec-loop/references/tree.md` — 「形式検査のモデル」の記録の表と、状態遷移図の段落
- `plugins/spec-loop/agents/formal-checker.md` — 報告に図の対応（ビュー）を書く
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 「モデルを残す」で対応を書いて図を作る・Q&A 表に起票するとき図のパスを質問に付ける
- `plugins/spec-loop/skills/formal-baseline/SKILL.md` — 版の 2 行（手順は spec-review の「モデルを残す」を指したまま）
- `plugins/spec-loop/README.md` — スクリプトの表
- `CLAUDE.md` — スクリプトとテストの項
- `scripts/check-all.py` — テストの登録
- `.github/workflows/plugins.yml` — テストのステップ
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1177.md` — この計画ファイル

触らない:

- `plugins/spec-loop/scripts/render-diagrams.py`（drawio・BPMN の書き出し。`.tla` は別のスクリプトにする）・`check-formal-rerun.py`・`check-tlc.py`（読み込んで使う）・`tlc-trace.py`
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）——説明の文は偽にならない
- Q&A 表の列（リンクは `質問` の文に入れる。列を足すと前からの正本が「見出しが違う」で落ちる）
- 公開ページ（`docs/plugins/`）——spec-loop のスクリプトを列挙していない

依存の追加・更新: なし

**複製の数**: 「図の対応・状態遷移図を記録の一覧に置く」を述べる箇所は 5（`tree.md` が原本、`formal-baseline.py` の定数（`test-formal-baseline.py` が突き合わせる）、`spec-review/SKILL.md`、`formal-checker.md`、`formal-statechart.py` の docstring）。
分けない理由: 決まりの原本は `references/tree.md`、ほかは指すか写し（写しはテストが突き合わせる）。

## デプロイ経路

プラグイン（`marketplace.json` のカタログと、`link-skills.sh` を使う利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口（モデルから図ができる・図が読まれる場所）: `formal-statechart.py` の CLI（spec-review の「モデルを残す」と formal-baseline が呼ぶ・利用者が手で呼ぶ）・`formal-baseline.py check`（残した図と対応の形）・
spec-review 手順 3（Formal Checker の報告から対応を書く）・手順 4（範囲の中の反例を共有の Q&A 表に起票する）・formal-baseline の手順 4（spec-review の「モデルを残す」を指す）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | 保存したモデル 1 つ（`spec/formal/<対象>/`）から 1 コマンドで Mermaid の状態遷移図が出る。状態と遷移のラベルは対応（`view.json`）の言葉だけで、変数名・行為の名前・TLC の状態の式が図に出ない。対応に無い状態・行為があれば描かずに止まる | CLI | 本体 | 本物の TLC で手元で走らせた結果（計画・PR に残す）＋回帰テストの試料（本物の TLC で取った出力を偽の TLC が返す） |
| A2 | 不変条件を破るモデルでは、破る状態に印が付き、反例のトレースが図の上の経路（番号つきの遷移と経路の一覧）として描かれる。陽性対照（わざと壊した版。`--controls`）でも同じく印が付き、陽性対照で違反が出なければ描いたことにしない | CLI | 本体 | 同上 |
| A3 | 図の状態と遷移が TLC の状態グラフ（`-dump dot`）と食い違わないことを、回帰テストが dot を独立に読んで突き合わせる（変異で、遷移を落とす・印を外す・経路を外すと落ちる） | テスト | `test-formal-statechart.py` | テストの試料と変異 |
| A4 | spec-review が範囲の中の反例を共有の Q&A 表に起票するとき、その対象の図（`spec/formal/<対象>/statechart.md`）のパスを質問に付ける。図は「モデルを残す」で対応と一緒に作って残す | spec-review 手順 3・4・formal-baseline 手順 4 | `spec-review/SKILL.md`・`formal-checker.md`・`tree.md` | 読んで確かめる（スキルの振る舞いは未証明——下） |
| A5 | `formal-baseline.py check` が、記録の `図の対応のファイル`・`状態遷移図のファイル` の一覧のファイルを在るべきファイルに数え（無ければ違反）、行が無くても違反にしない。本体の項目と `tree.md` の表が一致する | `check` | 本体 | `test-formal-baseline.py` の試料と変異・写しの突き合わせ |
| A6 | 版を 3 種類で揃えて上げ、`check-all.py` が緑。新しいテストが `check-all.py` と CI に登録される | CI | 版の行・登録 | `check-all.py`・`test-check-all.py`・PR 側の CI |
| A7 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: A4 のスキル（spec-review・Formal Checker）が実際の仕様レビューで対応を書き、図のパスを質問に付けること（スキルを実際の正本で走らせて観測していない——人間のレビューに回す）。
Mermaid の図が GitHub の上で描けること（GitHub の描画は CI に無い。出す文字列の形は回帰テストで見る）も未証明。

**生成物**: このリポジトリの生成物は該当なし（`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` を測るもので、この周は触らない——`--check` は `check-all.py` で見る。図の書き出し（`diagrams/`）も触らない）。
正本のリポジトリの `statechart.md` は生成物で、spec-review がモデルを残すたびに作り直す（鮮度の検査は持たない——`formal-statechart.py` の守らないもの）。

## 未解決・確認待ち

- H1・H2 の確認の Issue（利用者が戻ってから確かめる）: 起票後に番号を書く。

## 関門の記録

```dev-loop-gates
周の base: 2bae472fdedfa7c1ee661d370e8fc4a1ab9c64b9
```

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1177-formal-statechart`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1177`・起点 `2bae472`・
  base `2bae472fdedfa7c1ee661d370e8fc4a1ab9c64b9`（`origin/main`＝`refs/remotes/origin/HEAD` を start-point に `prepare-worktree.sh` が出した値）。
- 関門: **1 パス目の指摘対応の起点: `34ebf50`**（1 パス目の関門に渡した時点の HEAD）。
- 交絡を潰した手順: 本物の TLC 2.19（`/Users/hdknr/.local/bin/tlc`。tla2tools v1.7.4）で手元の試料の正本を作って走らせた——本体（`Order`。反例なし）と陽性対照（`OrderBroken`。出荷の支払いの条件を外した版）で、
  陽性対照だけに `⚠ 未払いのまま出荷済み` と番号つきの経路が付き、本体には付かない（同じ対応・同じ呼び方。陰性と陽性の両方を見た）。`Two`（反例 3 つ）・`Par`（行き止まり）・`Live`（時相の性質→1）・`--max-edges 2`（経路だけ）も走らせた。
  `-continue` を外すと状態グラフが途中で切れ、反例も 1 つになる（`Two` で実測——回帰テストの変異「-continue を渡さない」の試料）。`-continue` のとき違反があっても `No error has been found` が出て終了コード 0 になることも実測（違反の判定は出力の印で読む）。
- 割り目: 割らない（cruise の周）。

## 既知の限界・決着済みの論点

- H1・H2（上の「決めた値」）——穴の記録。決着の理由が誤っていると判断したなら、それは新しい反証である。
- 図は Mermaid（Issue が認める）。SVG は出さない。
- 時相の性質の違反（繰り返しのある反例・`Back to state`・`Stuttering`）は描かない（止まる）——Issue の受入基準は不変条件の違反。
- 行き止まり（`Deadlock reached`）は TLC がそこで止まるので、グラフが全体でないことがある。そのときは図に「全体ではない」と書く。

## 手順 8（起票数）

- この周の起票: 2 件（仕様の穴を推奨で決めた確認の Issue——H1・H2。番号は起票後に書く。関門の指摘からの起票は振り分けの後に足す）
