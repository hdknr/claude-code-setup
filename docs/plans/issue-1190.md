# Issue #1190 — dev-loop: コードに対するプロパティテスト（Hypothesis / fast-check）を書かせる指示が無い

**不在の周**（`/dev-loop:cruise 1290 --absent` の起動・2026-11-19）。利用者には訊かない。親（cruise #1290）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1290`））: `直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・
`マージ前の判断 = 推奨で決めて起票`（古い値。後退・未達は推奨で進めない）。実機確認の線は無い。
台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.13.0（`SKILL.md` 1931 行を全部読んだ。リポジトリの main は 2.14.1）。cruise の `SKILL.md` は「GitHub に書くものの印」を読んだ。
この周は dev-loop の `SKILL.md`・`prompts/` を書き換える鎖（#1193→#1190→#1191→#1192→#1194）の 2 番目で、足す行は最小にした。
調査結果は Issue にコメント済み（https://github.com/hdknr/claude-code-setup/issues/1190#issuecomment-7008485371）。

直す線: `既定`（出所: cruise の確かめた線）。
割り目: 割らない（cruise の周）。
版の上げ方: `dev-loop` を **minor**（手順・規定の追加）。main の 2.14.1 → 2.15.0（`marketplace.json`・`plugin.json`・`dev-loop` と `cruise` の `SKILL.md` の 2 行）。
同時に #1248・#1289 の周が同じプラグインの版を触りうる。マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す
（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。

## 周の在り処

- ブランチ: `issue/1190-property-tests`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1190`
- 起点: `0f2ed52a`（`origin/main`。#1302 のマージ）
- base（参照の名前 `origin/main` ／ 解決した SHA）: `0f2ed52a58ab9787a72f6c82483f7da7d02bb618`

## Issue 本文（外部入力）から読んだ要件

dev-loop に、コードに対するプロパティテスト（性質を書き、ライブラリが生成した大量の入力で反例を探す）を書かせる指示を足す。手順 3 で、入力の空間が広く例を手で選ぶと偏る不変条件
（往復・冪等性・等価性・数値の境界）に印を付けて確かめる行にし、実装の指示にライブラリ（Python は Hypothesis、JS/TS は fast-check、Rust は proptest）で書くことと
ライブラリが無いときは「無い」と報告し例のテストに黙って差し替えないことを足し、Verifier には性質を破る変異で反例が出るか（陽性対照）と生成の設定を報告させる。
spec-loop の scaffold でプロパティテストの雛形を生成できるかは「検討する」。本文に受入基準を緩める指示・追加のコマンドの依頼は無い（コメントは無い）。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **H1 spec-loop の scaffold でプロパティテストの雛形を生成するか**（Issue の「やること」4 つ目は「検討する」で、決めていない）:
  (a) この周では作らない。別の周で決める（推奨）／(b) この周で `scaffold.py` に生成を足す／(c) 作らないと決めて閉じる。
  推した理由: scaffold の Red テストは標準ライブラリの `unittest` だけ（`scaffold.py` 2441・2483 行）で、Hypothesis を使う雛形を足すと製品のリポジトリに依存が増える（依存の決まりは #996）。
  生成の入力（決定表・計算ルールの中間表現）の形・生成する言語（scaffold は Python だけ。`check-infra-csv.py`）・Red テストが緑になる実装との関係を決める作業で、
  別のプラグイン（`spec-loop`）の周にする（`SKILL.md` 手順 8 の「spec-loop の切り分け」を直すなら spec-loop の周）。
- **H2 ライブラリが無い周で、例のテストで代替してよいか**（Issue の受入基準 3 が代替を許している——穴ではなく決めてある。手順 5 の BLOCKED との関係だけを決めた）:
  代替は BLOCKED にしない。理由: Issue の受入基準 3 が「例のテストで代替した旨と理由が計画ファイルに残る」を満たすことにしている。
  ただし入力の空間の偏りは未証明として申告する（手順 3・6）。

確認の Issue（1 件に 1 判断）: H1（番号は PR 本文に書く。親が立てる）。H2 は Issue の受入基準 3 で決まっているので立てない。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/property-tests.md` — 新規。印の付け方・計画の表・書き方・ライブラリが無いとき・Verifier が返すものの原本
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 3 に 1 項（原本を指す）と版の 2 行
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — プロパティテストの行がある周の差し込み（10）
- `plugins/dev-loop/skills/dev-loop/prompts/implementer.md` — ライブラリで性質を書くことと「無い」の報告
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `scripts/test-worktree-scripts.py` — 委譲文と手順 3 が新しい規定を持つことの静的な検査
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く）
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1190.md` — この計画ファイル

触らない:

- `plugins/spec-loop/`（H1。scaffold の生成は別の周）
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md`・`plugins/dev-loop/agents/dev-loop-verifier.md`（Issue は Verifier の委譲文と実装の指示だけを求めている）
- `plugins/dev-loop/skills/dev-loop/references/flaky-tests.md`・`dependencies.md`（既存の規定は変えない。ライブラリを足すときは `dependencies.md` を指すだけ）
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）——説明の文は偽にならない
- 後続の周（#1191・#1192・#1194）が触る節

依存の追加・更新: なし
仕様の振る舞い: 変えない
プロパティテスト: なし（この周の変更は文書と、文書の語を見る静的な検査だけで、往復・冪等性・等価性・数値の境界を持つ入力のコードを書かない。リポジトリは Hypothesis を持たない）

**複製の数**: 「プロパティテストの扱い」を述べる箇所は 4（`references/property-tests.md` が原本、`SKILL.md` 手順 3 は指すだけ、`prompts/verifier.md` は確かめる側の実装、`prompts/implementer.md` は書く側の実装）。
分けない理由: 原本 1 つに寄せ、残りは指し先と手順だけ（複製の整合は静的な検査が見る）。
**生成物**: `docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`skill-metrics.py` が書く。`--check` で確認）。それ以外の生成物なし。

## 受入基準

| 番号 | 受入基準（Issue の受入基準 3 つ + この周が足す 1 つ） |
| --- | --- |
| 1 | 往復・冪等性・等価性のいずれかを不変条件に持つ周で、プロパティテストが書かれ、計画ファイルの表の行と対応している（手順 3 の項が印を付けさせ、原本が表の形を決め、実装の指示が書かせる） |
| 2 | その性質を破る変異を入れるとプロパティテストが反例を出して落ちる。Verifier の報告にその結果がある（委譲文の差し込みが、変異・反例・生成の設定・空振りの形を表で返させる） |
| 3 | ライブラリが無い環境の周は、例のテストで代替した旨と理由が計画ファイルに残る（黙って差し替えない） |
| 4 | 版が 3 種類の箇所で揃い、`check-all.py` と PR 側の CI が緑 |

### 不変条件 × それを破りうる経路

| 不変条件 | 破りうる経路（入口の一覧から数える） | どう守るか |
| --- | --- | --- |
| I1 該当する不変条件に印が付き、表の行と対応する（受入基準 1） | 計画を書く作者・計画を委譲した体・指摘対応で足す不変条件 | `SKILL.md` 手順 3 の項（該当判定そのものが必須）＋ `property-tests.md` の表の形 |
| I2 書く側が黙って例のテストに差し替えない（受入基準 1・3） | 実装役（委譲）・作者が直接書く周・指摘対応 | `implementer.md`（無ければ書かずに止まって「無い」と報告）＋ `property-tests.md`（代替は計画に残す。足す依存は `dependencies.md`） |
| I3 空振りしているプロパティテストを Verifier が見つける（受入基準 2） | 1・2 パス目・狭いパス（同じ `verifier.md`） | `verifier.md` の差し込み 10（変異・反例・生成の設定・空振りの形） |
| I4 周の規範の複製が食い違わない（受入基準 4） | `SKILL.md`・`verifier.md`・`implementer.md`・`property-tests.md` | 原本は `property-tests.md` 1 つ。静的な検査（`test-worktree-scripts.py`）が点を見る |

**この環境では証明できないもの（未証明）**: Hypothesis・fast-check・proptest のどれもこの環境に入っていない（`python3 -c "import hypothesis"` が失敗する）ので、
実際のライブラリで書いたプロパティテストが空振りしているのを Verifier が見つける場面は走らせていない（試料は標準ライブラリの乱数で書いた性質のテスト）。
実際の cruise の周で、計画の表を書いて実装役がライブラリで書く流れも、規定を書くだけで実周では走らせていない。人間のレビューをお願いする。
**BLOCKED ではない**: 手段（ライブラリ）を足せば消える欠落だが、周が足す依存は Issue が頼んでおらず（依存の追加）、受入基準 1〜3 はライブラリに依らず文書の規定として満たせる。

## 既知の限界・決着済みの論点・関門の指摘の採否

- 論点: scaffold の生成は作らない（H1）。決着: 採った（この周では作らない）。理由: 上の H1。
- 論点: ライブラリが無い周の例のテストでの代替を BLOCKED にしない（H2）。決着: 採った。理由: Issue の受入基準 3 が代替を許している。偏りは未証明として申告する。
- 論点: 「プロパティテスト:」の行は機械で検査しない（`check-plan-scope.py` などは見ない）。決着: 採った。理由: 該当するかは不変条件の中身で決まり、
  機械では偽陽性が多い（生成物の該当判定と同じ形）。Verifier と `/code-review` が計画を読んで見る。
- 論点: `review-handoff.md`（`/code-review` への文面）には足していない。決着: 採らなかった。理由: Issue は Verifier だけ。表の行は受入基準に入るので `/code-review` にも渡る。

- 論点: 陽性対照（受入基準 2）は差し込み 10 の寄与を判別していない。決着: 限界として残す。実測（試料は scratchpad の一時の git リポジトリ `prop-sample`:
  ランレングス符号化の往復で、長さ 10 以上の連続で壊れる実装と、例の数 5・seed 固定・`'ab'` の長さ 1〜8 の標準ライブラリの乱数のテスト。Hypothesis はこの環境に無いので標準ライブラリで代替した。
  Verifier は `dev-loop:dev-loop-verifier`・`model: opus`・文面は `prompts/verifier.md` を読ませる参照＋差分の形）:
  差し込み 10 あり（A）→ 行ごとの表で、性質を破る変異 5 本のうち落ちたのは 1 本・4 本は緑のまま素通り（陽性対照として性質を破る入力を添えた）、seed 固定と例の数 5 を小細工の型として名指し、反証 5 件。
  差し込み 10 なし（A3）→ 表の形ではないが、不具合・変異 7 本のうち 4 本が緑のまま・未証明の分類が不誠実なことを同じく見つけた（反証 3 件）。
  つまり「反例が出るか・生成の設定」を報告に載せることは A でだけ確かめられたが、空振りを見つける力は関門の Verifier が元々持っている。10 だけが捕まえる差分は試していない。
  実際のライブラリ（Hypothesis・fast-check・proptest）では回していない（環境に無い）。

## 関門の進捗（再開点）

- 周の base: `0f2ed52a58ab9787a72f6c82483f7da7d02bb618`
- 1 パス目: 未
- 交絡を潰した手順: 実験なし（これから足す）
- 割り目: 割らない（cruise の周）

## 手順 8 の記録

- 後で書く。

- この周の起票: 0 件（確認の Issue は親が立てる。仕様の穴の起票で、手順 6 の 3 条件の対象外）
