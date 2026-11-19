# Issue #1302 — spec-loop: scaffold に書き起こす前の見積もりの段を足す

**不在の周**（出所: `/dev-loop:cruise 1296 --absent`、2026-11-19）。利用者には訊かない。親（cruise #1296）から委譲文で受けた子。親 #1296 の最後の周。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1296`）。利用者の確認（起動時））: `直す線 = 既定`・`マージ = 関門を通ればマージ`（配布を確かめ済）・`周の途中の課題 = 台帳に足して直す`・
`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。確認の Issue は立てない（親が立てる）。
読み込んだ dev-loop は 2.13.0（キャッシュ `skills/dev-loop/SKILL.md` 1931 行を全部読んだ）。割り目: 割らない（cruise の周）。

直す線: `既定`（出所: cruise の確かめた線）。
版の上げ方: `spec-loop` を **minor**（scaffold の手順に能力を追加。0.122.0 → 0.123.0）。`dev-loop` は触らない（上げない）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md`）。
重い検査（`test-scaffold-estimate.py`・`check-all.py`）は `run-serial.py` 越し。

Issue 本文（外部入力）から読んだ要件: scaffold の `SKILL.md` の手順 2 の前に、仕様のテストケースを「Red テストにできる／受入基準に回す／どちらにもできない」に分けて数える段を足し、
乗る割合が低ければ利用者に示して止まる。機械で決まる部分はスクリプトにする。受入基準 3 つ（下）。コメントは無い。本文に受入基準を緩める指示は無い。

## 決めた値（開発者が決めた——仕様の穴ではない実現の手段）

- **D1 置き場所**: 手順 `### 1a`（手順 1 と 2 の間。番号を振り直さない——他の文書が「手順 2」「4」「6」を指す）。
- **D2 機械で決まる部分**: 仕様のケースの一覧（`list`）と、分け方の形・網羅・件数・割合（`check`）をスクリプト `scaffold-estimate.py` にした。**どれに分けるかは判断なのでスキルが決める**（機械は分けない。キーワードの当てずっぽうは偽の確かさになる）。
- **D3 ケースの数え方**: `scaffold.py` の `spec_case_rows`（`check-spec-exit.py` の `case_rows`）を読み込む。写さない。中間表現は要らない（書き起こす前）。
- **D4 見積もりの置き場所**: `build/scaffold-estimate.json`（commit しない。判断の記録で、機械は書き起こしと照合しない）。
- **D5 閾値**: **決めない**。理由は `references/spec-ir.md` の「書き起こす前の見積もり」（実測が #1296 の 1 点だけ・線を引いても示すかどうかが変わるだけ・乗る割合は仕様の性質で変わる）。
  割合に依らず、毎回示して続けるかを確かめる（受入基準の「確かめてから手順 2 に入る」を満たす上位の形）。
- **D6 ケースが 0 件**: 終了コード 3（見積もれない）。0 にすると「全部乗る」と読める。
- 仕様の穴: なし（Issue が段の置き場所・結果の示し方・閾値を決めるなら根拠を書く、までを決めている。実現の手段は D1〜D6）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold-estimate.py` — 新規（見積もりの機械で決まる部分）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 手順 1a
- `plugins/spec-loop/references/spec-ir.md` — 「書き起こす前の見積もり」の節（区分・閾値を決めない理由）
- `scripts/test-scaffold-estimate.py` — 新規（試料・変異）
- `scripts/check-all.py` — 収録
- `.github/workflows/plugins.yml` — CI のステップ
- `CLAUDE.md` — 本体とテストの項
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1302.md` — この計画ファイル

触らない:

- `scaffold.py`（見積もりの結果を機械で書き起こしに繋げない。D4）・`check-spec-exit.py`・`spec-exit.md`
- `dev-loop` の全部（規定は変えない）
- 説明文（frontmatter・`plugin.json`・`marketplace.json` の description）——今の要約が偽にならない（手順の追加で、スクリプトの数を数えた記述は無い）
- `docs/plugins/spec-loop.md`・`plugins/spec-loop/README.md`（スクリプトの一覧を持たない——grep で確かめた）

依存の追加・更新: なし

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

**複製の数**: 3 つの区分の名前（`red`・`acceptance`・`neither`）を述べる箇所は 3（`scaffold-estimate.py` の docstring と定数・`spec-ir.md` の表・`SKILL.md` 1a）。
原本は `spec-ir.md`、`SKILL.md` は指す。テストは本体の出力の文字列で比べる。分けない理由: 原本は `spec-ir.md`、本体の docstring は形の写しで、テストが本体の出力を文字列で当てる。

## デプロイ経路

プラグイン（カタログと `link-skills.sh` の利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口: `scaffold` スキル（手順 1a）→ `scaffold-estimate.py`（`list`・`check`）。仕様のケースの読み口は `scaffold.py` の `spec_case_rows`。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | scaffold の手順に、書き起こす前の見積もりの段がある（手順 2 の前） | `SKILL.md` | 手順 1a | `check-skill-pointers.py`（指し先が実在）・手順の並びを PR で目視 |
| A2 | 見積もりの結果（分けた件数・どちらにもできないケースの番号）を利用者に示し、続けるかを確かめてから手順 2 に入る | `SKILL.md` 1a の 4・`scaffold-estimate.py check` の出力 | 出力に件数・割合・番号と場所・理由を出し、スキルが示して確かめる | `test-scaffold-estimate.py` の試料（正しい分け方・割合が低い・名指し）と変異。手順の文面は PR で目視 |
| A3 | 見積もりの形と網羅を機械で確かめる（全ケースを 1 つずつ・仕様に無い番号・区分・reason・形）。ケースの数え方は条件 1 と同じ | `check` | `read_estimate`・`coverage`・`spec_case_rows` を読む | 試料 28 件・変異 23 件（`test-scaffold-estimate.py`） |
| A4 | 止める閾値を決めないなら、決めない理由と原本の置き場所を書く | `spec-ir.md` の節 | 3 つの理由 | PR で目視（記述の事実は A3 の割合が低くても 0 の試料で当てる） |
| A5 | 何も書かない（正本を変えない）・ケースが 0 件は 3・見積もりのファイルが無いか読めなければ 2 | 全経路 | 終了コードの決まり | 試料の前後の snapshot・変異 |
| A6 | 版を 3 種類で揃えて上げ、`check-all.py` が緑・CI が全部 pass | CI | 版の行・収録 | `check-all.py`・`check-plugin-versions.py`・`test-check-all.py` |
| A7 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: 実際の spec-loop の正本（実案件の仕様）に当てた見積もりの数字と、分け方（`red`・`acceptance`・`neither`）の妥当性——分けるのはスキルの判断で、
実案件の仕様が手元に無い。A4 の「閾値を決めない」の判断が実案件で妥当かも測っていない（実測が #1296 の 1 点という前提のまま）。人間のレビューに回す。

**生成物**: 生成物なし（変更するファイルに生成物は無い）。

## 実験と確認の記録

- 試料（`test-scaffold-estimate.py`）で `list`・`check` を当てる。結果は PR コメントに貼る。実験で何かを述べる周ではない（交絡を潰す対象の実験なし）。

## 未解決・確認待ち

- 実案件で見積もりと書き起こしの後の内訳を比べ、線を引ける形が見えたら `spec-ir.md` に根拠と一緒に書く（今は決めない）。

## 既知の限界・決着済みの論点（関門の指摘の採否）

| 指摘 | 出所 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 「乗る割合」の分子が Red + 受入基準で、見出し（Red テストに乗るか）と食い違い、spec-ir.md の理由 3 が実装の定義のもとで偽 | Verifier 1・/code-review 1 | 示せる（red 0・acceptance 20 で 100.0%。出力で確認） | A4 | **直した**（定義を spec-ir.md・docstring に書き、出力に Red だけの割合を併記。テスト更新） |
| V2 spec-ir.md の「実測 #1296 1 点」が不正確（実際は 636 件のうち 1 ファイル 113 件で 15 件 13%・#1298〜#1301 の前・Red だけ） | Verifier 1 | 示せる（#1296 本文） | A4 | **直した**（事実を書き直し、「今の定義では 0 点」に） |
| V3 手順 1a が終了コード 2 と list の 1 を扱わず、「2 に入る」が項目 2 と読める | /code-review 1 | 示せる（文面） | A2 | **直した**（終了コード 2・list の 1 を書き、「手順 2」と書く） |
| V4 試料の穴: class の大文字小文字・値の中の重複キー・RecursionError を 2 にしない・未分けの全件名指し（変異が素通り） | Verifier 1 | 示せる（変異が素通り） | 無し | 記録だけ（試料の穴） |
| V5 エラー文「scaffold.py の手順 1a」 | Verifier 1・/code-review 1 | 示せる（文言） | 無し | **直した**（V1 と同じ編集で文言を scaffold スキルに。記録だけの行だが同じ行を触るため） |
| V6 find_versions の probe を捨てる（v01 だけの正本で理由が紛らわしい）・reason の CR・tree.md に置き場所が無い・neither の記述が条件 1 と重なる | /code-review 1 | 示せる（合成・文言） | 無し | 記録だけ（まれな形・文言） |

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1302-scaffold-estimate`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1302`・切った元の参照 `origin/main`（解決した SHA `5ebb6689aa7812dcaa55ca508a006385cfebc7c6`）・起点コミット `5ebb6689`。base は `5ebb6689aa7812dcaa55ca508a006385cfebc7c6`。
- 実装を終えた（コミット `0fc32792`）。割り目: 割らない（cruise の周）。`test-scaffold-estimate.py` は `OK: 試料 28 件・変異 23 件`。
- 1 パス目: Verifier（別ティア `opus`・`dev-loop:dev-loop-verifier`）と `/code-review`（high）を `0fc3279291d9faa72eb25852e33e7614e0d05118` に当てた。**1 パス目の指摘対応の起点の SHA: `0fc3279291d9faa72eb25852e33e7614e0d05118`**。反証 4・指摘 7（上の表）。
- 指摘対応: V1・V2・V3・V5 を直した（コミット `e68e14dd685a96bce52e8a51783100b167297a2b`）。V4・V6 は記録だけ。
- 手順 5 の反証と差し戻し: 実験なし。

## 関門の記録

```dev-loop-gates
周の base: 5ebb6689aa7812dcaa55ca508a006385cfebc7c6
```

- この周の起票: 0 件（不在の周。確認の Issue・フォローアップの Issue は親が立てる。周の途中の課題は PR コメントの記録だけ・残課題）
- 手順 8: 焼き戻す学びなし（切り分けの層を見た結果: 戻せる切り方の問題は見つからなかった）
