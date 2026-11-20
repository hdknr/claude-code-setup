# Issue #1347: spec-loop: 一から作る案件で、scaffold の後に実装の土台（窓口・口・verify）と依存の順を作る段が無い

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — 依存（`depends`）を Red テストの呼び出し（`setup`・`after`・トレースの `calls`・`setup`・`after`）からも引く・依存の循環を組とケースで名指しして止める・`--foundation` で土台の本文と `issues.json` の項目を作り、ほかの項目をそれに依存させる・docstring
- `plugins/spec-loop/scripts/parent-checklist.py` — `issues.json` の土台の項目（`foundation`）を読む・docstring
- `plugins/spec-loop/references/handoff-issue.md` — 「依存の連鎖」（Red テストの呼び出し・循環で止まる・解き方）・「土台の本文」・「置き場所」の `issues.json` の項目
- `plugins/spec-loop/references/spec-ir.md` — 「前提と後の状態」の例が依存の循環を持つ（F-006 ⇄ F-007）ので、F-006-C3 を F-007 へ移す（Issue の移し方）。呼び出しが依存になることを 1 文
- `plugins/spec-loop/references/tree.md` — `issues.json`・`foundation.md` の置き場所（記述があれば）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 一から作る案件かを利用者に確かめて `--foundation`・循環で止まったときの手当て・土台の本文の登録（重複の探し方・先に登録する）
- `plugins/spec-loop/README.md`・`docs/plugins/spec-loop.md` — 依存の連鎖の説明（呼ぶ機能だけでなく Red テストの呼び出し）と `--foundation`
- `CLAUDE.md` — `parent-checklist.py` の行の「依存は … 呼ぶ機能が呼ばれる機能に依存する」を今の定義に（`scaffold.py` の行に `--foundation`）
- `scripts/test-scaffold.py` — 依存・循環・土台の試料と変異。循環する既存の試料（在庫の `staged_ir`・文書の例）を、Issue の移し方で循環しない形に直す
- `scripts/test-parent-checklist.py` — 土台の項目の試料
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json`・`plugins/spec-loop/skills/*/SKILL.md` — 版
- `docs/plans/issue-1347.md` — この計画

触らない:

- dev-loop（`spec-gap.md`・cruise の `parent-issue.py`）——土台の本文は handoff の印を持たないふつうの Issue として読まれる（下の「決めたこと」）。dev-loop の版は上げない
- `rebuild-scope.py`・`rework-metrics.py`（`issues.json` を読まない——`gh issue list` の出力を読む）
- #1389（#1340 の既知の取りこぼし）・#1379（#1333 の残り）——この周では直さない。当たったら番号を指して記録だけ
- Issue の提案 1 の「既存のシステムを改修する案件か、一から作る案件かを推測で決める」——機械は決めない（利用者に確かめ、旗で渡す）

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）
依存の追加・更新: なし

版の上げ方: spec-loop を minor で 1 つ上げる（0.x なので能力の追加も minor。マージ直前に main が進んでいたら、main の先端の spec-loop の版から minor で 1 つ上げた値に上げ直す。parallel.md の「版とマージの順」。#1346 の周も spec-loop を上げる）

## 不在の周と線

- 不在の周: `/dev-loop:cruise 1374 --absent` の起動（2026-11-20）の子。
- 台帳の確かめた線（出所: 利用者の確認——起動時・親 Issue #1374 の `cruise:` の行・2026-11-20T11:38:12Z、配布を見せて確かめた）:
  - 直す線 = 既定
  - 仕様の穴 = 推奨で決めて起票
  - マージ = 関門を通ればマージ（マージは親がする）
  - 周の途中の課題 = 外に出す
  - マージ前の判断 = 推奨で決めて起票（後退・未達を含む）
  - 実機確認: 線なし（止まる）

## デプロイ経路

main へのマージ → GitHub Pages の再ビルド（`docs/plugins/spec-loop.md`）とプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。

## 決めたこと（仕様の穴——推奨で決めて起票の線）

1. **一から作る案件の合図**: `scaffold.py --foundation`（旗）。スキルが利用者に確かめ、一から作ると答えたときだけ付ける。**v1 でだけ使える**（v2 以降・`--check`・`--red-check` との組み合わせは 2）。
   - 選択肢: A 旗（推奨）／B 中間表現のキー（`"foundation": true`）。推奨の理由: 一から作るかは仕様ではなく案件の事情で、中間表現は「仕様に無いことを足さない」（spec-ir.md）。`--provisional` と同じ「利用者が決めて旗で渡す」形。B は仕様の写しに案件の事情を混ぜ、機能の指紋の外のキーとして扱いを決め直す要がある。
   - 確認の Issue: #1392。
2. **土台の本文の印**: 1 行目は `<!-- spec-loop-foundation: v1 -->` で、handoff の印（`<!-- spec-loop-handoff: v3 -->`）を持たない——dev-loop はふつうの Issue として読む。`issues.json` の項目は `"foundation": true`、ほかの項目の `depends` は依存先の id として `foundation` を持つ。
   - 選択肢: A 独自の印・dev-loop はふつうの Issue と読む（推奨）／B handoff の印を付け、dev-loop の `spec-gap.md` に土台の本文の読み方を足す。推奨の理由: 土台の本文は機能の指紋・Red テストの sha256・受入基準の表を持たず、handoff の読み方（spec-gap.md）がそのまま当たらない。B は dev-loop の写し（spec-gap.md・test-scaffold の突き合わせ）と版を動かし、周を 2 つのプラグインにまたがせる。
   - 確認の Issue: #1393。
3. **依存に数える呼び出し**: 入出力のケースの `setup`・`after`（`seed` は除く）と、トレースのケースの `calls`・`setup`・`after`。Issue の提案 2 の「Red テストの呼び出しから依存を引く」に従い、トレースも Red テストの呼び出しなので含める（Issue の文の写し方で、穴ではない）。
4. **循環の終了コード**: 中間表現の機能どうしで循環すれば 1（中間表現の問題。組とケースを名指しし、解き方を出す）。`--bundle` のまとめ方でだけ循環するなら今までどおり 2。循環する機能を `--bundle` で 1 件にまとめれば通る（組の中の依存は数えない——前からの決まり）。
5. **土台で作る seed の線**: Red テストのケース（中間表現の `cases` の全部）の半分以上が使う seed（Issue の例のまま）。

## 周の大きさ（同じことを述べている箇所の数）

- 依存の定義（呼ぶ機能・Red テストの呼び出し）: 原本 `handoff-issue.md` の「依存の連鎖」。`scaffold.py` の docstring・`parent-checklist.py` の docstring・`README.md`・`docs/plugins/spec-loop.md`・`CLAUDE.md`・scaffold の `SKILL.md` が指すか 1 文で写す。複製 7。分けない理由: どれも前から依存を 1 文で述べており、古いままだと「呼ぶ機能だけ」と誤って読める。
- 土台の本文の形: 原本 `handoff-issue.md` の「土台の本文」。`scaffold.py`（生成）・scaffold の `SKILL.md`（いつ付けるか・登録）・`parent-checklist.py`（読む）・README・公開ページ。複製 6。
- 循環で止まる: `scaffold.py`（docstring・出力）・`handoff-issue.md`・scaffold の `SKILL.md` 手順 3。複製 3。

## 受入基準

経路（`issues.json` の `depends` と土台の本文を作る・読む入口）: `scaffold.py` の書く生成と `--dry-run`（`--check`・`--red-check` は本文を作らない）・`--bundle` の組・v2 以降の変わった機能だけの本文・`parent-checklist.py`・scaffold スキルの登録（手順 6）。

| # | 不変条件 | 経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | `--foundation` を付けた v1 の書く生成で、土台の本文（`foundation.md`）ができる。中身は口の一覧（`reset_state`・`seed`。使うケースの数）・seed の一覧（名前・値のキー・使うケースの件数・使う機能・土台で作るか）・verify の手順を書く指示。`issues.json` の先頭に土台の項目があり、ほかの全部の項目の `depends` が `foundation` を含む | 書く生成・`--dry-run`（何も書かない）・`--bundle` と一緒 | `test-scaffold.py` の試料（文書の例の seed を使う中間表現で、本文の行と件数・`issues.json`）。旗を付けなければ前と同じバイト（陰性対照） |
| A2 | `--foundation` は v1 でだけ・書く生成か `--dry-run` とだけ使える（v2・`--check`・`--red-check` は 2） | 引数 | 試料 |
| A3 | `issues.json` の `depends` が、Red テストの `setup`・`after`（とトレースの呼び出し）が呼ぶほかの機能の入口から引かれる。`called_by` の依存も残る。組の中・撤去・この版で本文を作らない機能・`seed` は数えない | 書く生成・`--bundle`・v2 | 試料（呼び出しで依存する中間表現・v2 で片方だけ変えた中間表現・`--bundle`）。陽性対照: base `33de1e80` の本体は同じ試料で `depends` を書かない |
| A4 | 依存が循環する中間表現では、書く生成と `--dry-run` が登録の前（本文を書く前）に 1 で止まり、循環する組と、依存を作ったケース（とどこの呼び出しか）を名指しし、解き方を出す。書く生成は前の本文を消す。`--bundle` で循環する機能を 1 件にまとめれば通る | 書く生成・`--dry-run`・`--bundle` | 試料。陽性対照: base の本体は同じ循環の試料で 0 |
| A5 | `parent-checklist.py` の出力に、依存のある項目で `(depends: …)` が付く——Red テストの呼び出しから引いた依存と、土台への依存も | parent-checklist | `test-parent-checklist.py` の試料（scaffold が書いた `issues.json` の土台の項目と依存） |
| A6 | 文書（spec-ir.md）の例が循環せず、scaffold が作れる（例のまま書き起こした中間表現が止まらない） | spec-ir.md の例 | `test-scaffold.py` の「文書の例を作る」 |
| A7 | spec-loop の版が 3 種類で揃い、base より上がっている | カタログ・マニフェスト・スキル本文 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| A8 | 歯止めが全部緑 | リポジトリの CI | `check-all.py`（run-serial 越し）と PR 側の CI |

掛け算: 受入基準を Verifier と `/code-review` の両方に、2 パス（1 パス目の指摘対応の差分が 0 行なら 1 パス）。

未証明: 実案件（Issue の 37 機能・564 ケース）そのものに当てること——正本はこのリポジトリに無い。試料は Issue が書いた形（読む入口と書く入口が呼び合う・seed を多くのケースが共有する）を写したもの。人間のレビューに回す。
限界: 土台の本文が書くのは「何を作るか」の指示で、作り方（Django の構成・テスト用の DB）は決めない（利用者と決める）。一から作る案件かは機械が決めない。
BLOCKED: なし。
生成物: なし（`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけを測る。spec-loop の生成物（`scaffold/`）はこのリポジトリに無い。`docs/plugins/spec-loop.md` は手で書くページ）。
プロパティテスト: なし（依存の引き方と循環の検出はグラフの形の組み合わせで、例の試料（鎖・2 つの循環・まとめ・撤去）で名指しできる。往復・冪等性・数値の境界は無い）
差分テスト: なし（振る舞いを変える周——依存を足し、循環で止める。旗の無い・呼び出しの無い中間表現の出力が前と同じバイトであること（A1 の陰性対照・既存の試料）はテストが固定する）

## 未解決の判断

なし（上の「決めたこと」の 1・2 は推奨で決めて確認の Issue を立てる）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1347-scaffold-foundation-depends`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1347`・起点 `33de1e80`・base `origin/main` = `33de1e800c75c6f34a074b8a5cd789c3c9e313b8`
- 直す線: 既定（出所: cruise の台帳の確かめた線）
- PR: #1391
- 割り目: 割らない（cruise の周）。手順 4 の割り目は訊かずに続けた。
- 実験: A3・A4・A5 の陽性対照（下の「歯止め」）。交絡: 同じ試料（`test-scaffold.py` の `CASES` の中間表現を `build` で置いた正本）・同じ `python3 -I`・本体だけが違う（base `33de1e80` を `git archive` で写した `scripts/` と HEAD）。
- 既存の試料の直し: 在庫の `staged_ir`（F-004 ⇄ F-005）・文書の例の「前提と後の状態」（F-006 ⇄ F-007）・「実行ごとに変わる出力」（F-009 ⇄ F-010）が循環していたので、Issue の移し方で循環しない形に直した
  （F-005-C2 → F-004-C3、F-006-C3 → F-007-C3、F-009-C2 → F-010-C3。F-010-C3 は本体を `as` で束ね後の状態が `$ref` で指す形を残すために、本体の期待を `$any` にした）。
  直しで素通りになった変異 3 つは、判別する試料に当て直した（「前提を呼ばない」→ トレースと一緒の在庫の試料・「動的なケースの後の状態を比べない」→ 読むたびに URN が変わる実装の試料（足した）・
  「束ねる結果を写さない（本体）」→ 持ち続ける辞書を `get_document` が返す実装に直した）。

## 歯止め

- A3 の陽性対照: 在庫の `staged_ir` に base の本体は `depends` を 1 つも書かず（F-004: None）、HEAD は F-004: [F-005]。文書の例も base は全部 None、HEAD は F-006: [F-008]・F-007: [F-006, F-008]。
- A4 の陽性対照: 循環する試料（`STAGE_CYCLE`）に base の本体は 0 で本文を書き、HEAD は 1（循環する組・ケース・解き方を出し、本文を書かない）。
- A5 の陽性対照: HEAD の `scaffold.py --foundation` が書いた `issues.json` に、base の `parent-checklist.py` は 2（0 番目が項目の形でない）、HEAD は 0（`- [ ] #100 foundation` を先頭に `(depends: #100, …)`）。
- `check-all.py`（run-serial 越し）1 回目: 失敗 3（`check-bold-flanking.py`——handoff-issue.md の太字・`check-plan-counts.py`——件数の行・`test-scaffold.py`——既存の試料の直しで素通りした変異 3 つ）。直した。

## 既知の限界・決着済みの論点

- 一から作る案件の合図・土台の本文の印——上の「決めたこと」のとおり推奨で決めた。
- #1389・#1379 はこの周では直さない（範囲外）。

## 手順 8

- この周の起票: 2 件（確認の Issue #1392・#1393——一から作る案件の合図・土台の本文の印。仕様の穴の線で推奨により決めた）

## 関門の記録

```dev-loop-gates
周の base: 33de1e800c75c6f34a074b8a5cd789c3c9e313b8
```
