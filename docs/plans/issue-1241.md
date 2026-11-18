# Issue #1241 — dev-loop: artifact-reads.py の読んだ成果物の行の後退（R3）と過検知（R4）を直す（#1157 のフォローアップ）

cruise（親 Issue #1169）の子として回す周。**不在の周**（出所: `/dev-loop:cruise 1169 --absent` の起動（2026-11-18T06:40Z。前のセッションは 2026-11-17T10:47Z））。AskUserQuestion は使わない。
spec-loop から来た Issue ではない（本文の先頭に `<!-- spec-loop-handoff:` の印が無い）。`作り直しの元:` の行も無い。
`find-cycle.py 1241` は [5] だけ当たった——`66252f3`（#1157 の計画に利用者の判断を書いたコミット。本文が `Refs #1241`）で、この周のものではない。新規の周。

台帳の確かめた線（出所: cruise の確かめた線（台帳 `issue-1169`）——利用者の確認（起動時・2026-11-17T10:47:55Z、配布を見せて確かめた）。親の委譲文で受け取った）:
直す線 = `既定` / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（**子はマージしない**——PR 側の CI まで）/
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票（古い値。後退・未達は推奨で進めない）。実機確認の線は無い。
`.claude/dev-loop.md`（main）の宣言: `マージの反映: ドキュメントとプラグインの配布`。

直す線: `既定`（出所: cruise の確かめた線）。

この周は導入済みの dev-loop 2.8.0 の `SKILL.md`（1923 行）で回る。重い検査は `run-serial.py` 越しに回す——
`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.8.0/skills/cruise/scripts/run-serial.py -- <コマンド>`。関門にも渡す。

版の上げ方: **dev-loop を patch**（2.9.0 → 2.9.1。不具合の修正）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/artifact-reads.py` — 空白で区切ったラベルの後ろの読み方（R3・R4）と docstring の「終了コード」の 1
- `scripts/test-artifact-reads.py` — R3・R4 の試料と、それを殺す変異
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の行
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ）
- `docs/plans/issue-1241.md` — この計画

触らない:

- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 行の形（コロンとバッククォートのある形）は変わらない。形に合わない行の判定だけを直す
- `plugins/dev-loop/skills/dev-loop/scripts/check-gates.py` — 読み込むだけ
- `CLAUDE.md` — スクリプトの一覧の説明は判定の細部を持たない（docstring を正とする）
- `docs/plans/issue-1157.md` — 前の周の記録

依存の追加・更新: なし。spec-loop の正本はこのリポジトリに無い（`仕様の振る舞い:` の申告は要らない——`check-spec-writeback.py` が 0 で確かめる）。

## 周の大きさ（同じことを述べている箇所の数）

- 判定の決まり: 本体の docstring の「終了コード」の 1（原本）・本体のコメントと正規表現・テストの試料。**1 箇所**（`CLAUDE.md`・`spec-gap.md` は docstring を指すだけ）。

## 決めたこと

- **D1 空白で区切ったラベルの後ろ（コロンを落とした記録の行か散文か）の決め方**——Issue は R3・R4 の例を挙げるだけで、例に無い語（`PR`・`README` のようなバッククォートの無い英字の語）を決めていない。
  決めた値: ラベルの直後が空白で、その後ろが **`なし`（直後が行末・空白・括弧）** か、**パスのような語**なら記録の行を書こうとした形（rc=1）。
  **パスのような語** = 空白の後の、ASCII のパスの文字（英数字・`_`・`.`・`/`・`~`・`+`・`-`）の並びで、英字を含み、**数・版（`1.5`・`v2.0`）でも、`.` で終わる略語（`e.g.`）でもない**もの。
  理由: 本体の「守ること」は**黙って落とさない**で、名指しの過検知は書き直せば消えるが、黙って落ちた行は誰も気づかない。R4 が挙げた散文（略語・数・版）だけを散文と読み、ほかの英字の語は 9fce292 と同じく名指しする。
  `PR` のような英字の語は 2d190c9（main）では rc=0、この周では rc=1 になる——**止まる向きの変化**で、既知の限界に書く。
  仕様の穴ではない（このスクリプトの内部の判定で、利用者に見える結果の決まり——行の形——は変えない）。

## verify の受入基準

不変条件 × 経路。経路（入口）: `artifact-reads.py` を呼ぶ入口は CLI 1 つ（計画ファイルかディレクトリ）。行の読み方は `read_plan` → `LINE`（記録の行）→ `looks_like`（形に合わない行）の 1 本で、
ディレクトリ・ファイル・`--all-artifacts` のどの渡し方でも同じ `read_plan` を通る。コードブロックの中は読まない（変えない）。

| # | 不変条件 | 経路と守り方 |
| --- | --- | --- |
| A1 | R3: `- 読んだ成果物 なし`・`- 読んだ成果物 spec_ir` が rc=1 で、行番号つきで名指しされる（直す前は rc=0——陽性対照） | `looks_like` の空白の後の判定。試料と変異 |
| A2 | R4: `- 読んだ成果物 e.g. これ`・`- 読んだ成果物 1.5 倍`・`- 読んだ成果物 v2.0` が rc=0（直す前は rc=1——陽性対照） | 同上 |
| A3 | R1: `- 読んだ成果物 a.md` は rc=1 のまま（行番号つき） | 既存の試料（R1）が緑のまま |
| A4 | ほかの既存の判定が変わらない——散文（`読んだ成果物ごとに`・`- 読んだ成果物 は spec-gap.md にある`・`- 読んだ成果物、`）は rc=0、コロン・括弧・`=`・バッククォートの形は rc=1、記録の行は数える | 既存の試料が全部緑 |
| A5 | `scripts/test-artifact-reads.py` に R3・R4 の試料と、それを殺す変異がある（変異は本体にちょうど 1 回現れ、変異の前は期待どおり） | テストの構造（変異の前後を確かめる仕組みは既存） |
| A6 | 版が 3 箇所で揃い、patch で上がっている。生成物（§8.2 の生成ブロック）が新しい | `check-plugin-versions.py`・`check-version-bump.py`・`skill-metrics.py --check` |

掛け算: 受入基準は 2 つの関門 × 2 パス（2 パス目が該当なしなら初回の 2 つ）に渡す。

証明できないもの（未証明）: なし——どれも試料で走らせて確かめられる。
生成物: `docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`SKILL.md` を触る——版の行だけ）。`skill-metrics.py --check` で鮮度を見る。図の書き出しは触らない。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1241-artifact-reads-r3-r4`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1241`・
  起点 `27327a1`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `27327a15d327f38034ad84d987313187d98133d3`。
- 陽性対照（直す前）: scratchpad の `pc1241/run.sh` を main（27327a1）の本体で走らせた——R1 `a.md` rc=1・R3 `なし`・`spec_ir` rc=0・R4 `e.g. これ`・`1.5 倍`・`v2.0` rc=1。
- 割り目（手順 4）: 割らない（cruise の周）。
- 実装: `de011b1`（本体・テスト・版。テストは run-serial 越しに 46 件・変異 59 件 OK）。陽性対照（直した後）: 同じ `pc1241/run.sh` で R1 rc=1・R3 rc=1（行番号つき）・R4 rc=0。
- 1 パス目の指摘対応の起点: `de011b1`（1 パス目の関門に渡した時点の HEAD。関門に渡す前に書いた）。
- 交絡を潰した手順: 陽性対照は同じ入力・同じ写し方で、直す前（27327a1）と直した後の本体を走らせて比べる。

## 既知の限界・決着済みの論点

- **英字だけの語（`PR`・`README`）は名指しする**（D1）。2d190c9（main）では rc=0 だった——止まる向きの変化。R4 が挙げたのは略語・数・版だけで、ほかの英字の語を散文と読む根拠が無い。
  実際の計画ファイル（`docs/plans/`・`plugins/`）に `- 読んだ成果物 <英字の語>` の散文は 0 件（`grep` で確かめた）。
  **決着の理由が誤っていると判断したなら、それは新しい反証である。**
- バッククォートの無い英字の語のうち、拡張子も `/` も `_` も無いパス（`Makefile`）と、英字の語で始まる散文（`PR の本文`）は区別できない——両方とも名指しする（黙って落とさない側）。
