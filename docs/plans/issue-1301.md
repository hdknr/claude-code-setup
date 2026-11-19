# Issue #1301 — spec-loop: 関数で表せないケースを受入基準として Issue に載せ、書き起こさなかったケースを名指しする

**不在の周**（出所: `/dev-loop:cruise 1296 --absent`、2026-11-19）。利用者には訊かない。親（cruise #1296）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1296`）。利用者の確認（起動時））: `直す線 = 既定`・`マージ = 関門を通ればマージ`（配布を確かめ済）・`周の途中の課題 = 台帳に足して直す`・
`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。確認の Issue は立てない（親が立てる）。
読み込んだ dev-loop は 2.13.0（キャッシュ `skills/dev-loop/SKILL.md` 1931 行を全部読んだ。リポジトリの main は 2.14.0 で、その差は読んでいない）。割り目: 割らない（cruise の周）。

直す線: `既定`（出所: cruise の確かめた線）。
版の上げ方: `spec-loop` を **minor**（中間表現の能力追加。0.117.0 → 0.118.0）、`dev-loop` を **patch**（`references/spec-gap.md` の記述追加。2.14.0 → 2.14.1）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md`）。
並行する周 #1298 が spec-loop の `scaffold.py`・版の行を触りうる——取り込みで衝突したら版の行と生成ブロックのほかは塊ごとに解く。
重い検査（`test-scaffold.py`・`check-all.py`）は `run-serial.py` 越し。

Issue 本文（外部入力）から読んだ要件: 機能に `acceptance` を足し、Red テストにしないケースを仕様の行の原文のまま並べる。Issue の本文の受入基準に写し、機械は原文の照合だけをする（`out_of_scope` と同じ）。
scaffold が仕様のテストケースと中間表現を突き合わせ、内訳（Red テスト a・受入基準 b・どちらにも無い c）を出し、どちらにも無いケースを名指しする。仕様のケースの数え方は #1297 の番号の形の原本を読む。
受入基準 5 つ（下）。コメントは無い。本文に受入基準を緩める指示は無い。

## 決めた値（開発者が決めた——仕様の穴ではない実現の手段）

- **D1 置き場所**: 本文の `## 受入基準` の中の小見出し `### Red テストにしない受入基準`（機能が `acceptance` を持つ追加・変更だけ）。節を足さない——節は 7 つのまま（`handoff-issue.md` の節の表・dev-loop の `spec-gap.md` の節の表と突き合わせが変わらない）。
  新しい節にすると、持たない機能の本文も変わる（`acceptance` を書かない中間表現の生成物は同じバイト、が崩れる）。
- **D2 原文の照合**: 機能の `source` の仕様の原文のどれかの 1 行と、前後の空白を落として一致すること（`source_lines`）。区切りの行と見出しの行（`#`）は挙げられない。`out_of_scope` の `scope_rows` の読み方を `rows_with_header` に出して、表の見出しの 2 行を前に付ける。
- **D3 仕様のケースの数え方**: #1297 の `check-spec-exit.py` の `case_numbers` を `case_rows`（行の原文つき）に広げ、scaffold がそれを読む（写さない）。見出しがテストケースの表の表のデータ行の先頭のセルが番号。`.md` だけ・`.` で始まる場所と `spec/formal/` は数えない。
- **D4 内訳の分け方**: Red テスト = ケースの `ref` が番号と一致（全機能の全ケース）、受入基準 = `acceptance` の行の先頭のセルの番号。Red テストと重なれば Red テストに数える（合計が N になる）。どちらにも無い = 残り。止めない（終了コードは変わらない）。
- **D5 出す場所**: 書く生成と `--dry-run` の標準出力（`--check`・`--red-check` は本文を作らないので出さない）。
- 仕様の穴: なし（Issue が置き場所の方針・内訳の形・原文の照合を決めている。小見出しの置き場所と数え方は D1〜D4 で決めたが、利用者に見える結果は「書いた行が本文に載る・内訳が出る」だけ）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — `acceptance` の検査・本文・内訳・docstring
- `plugins/spec-loop/scripts/check-spec-exit.py` — `case_rows`（行の原文つき。`case_numbers` はその薄い包み）
- `plugins/spec-loop/references/spec-ir.md` — 「Red テストにしない受入基準」の節・キーの表・画面の例
- `plugins/spec-loop/references/handoff-issue.md` — 「Red テストにしない受入基準」の節
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 書き起こす手順に `acceptance` と内訳の読み方
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 小見出しの読み方（dev-loop の規定は変えない）
- `scripts/test-scaffold.py` — 試料・変異
- `CLAUDE.md` — `scaffold.py` の項
- `plugins/spec-loop/.claude-plugin/plugin.json`・`plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md`・`plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plugins/dev-loop-design.md` — `skill-metrics.py` が書く生成ブロック（spec-gap.md の行数の変化）
- `docs/plans/issue-1301.md` — この計画ファイル

触らない:

- `dev-loop` の `SKILL.md` の本文・手順（Issue が「dev-loop の規定は変えない」と決めている。縮退の線のまま BLOCKED）
- `spec-exit.md`（番号の形の原本は #1297 のまま。変えない）・`spec-review/SKILL.md`・`agents/`
- `scripts/test-check-spec-exit.py`（`case_numbers` の出力は変えない。`case_rows` は scaffold のテストが通して見る）
- 説明文（frontmatter・`plugin.json`・`marketplace.json` の description）・`README.md`・公開ページ——今の要約が偽にならない

依存の追加・更新: なし

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

**複製の数**: 小見出しの名前 `### Red テストにしない受入基準` を述べる箇所は 4（`scaffold.py` の `ACCEPTANCE_HEADING` が写し、`handoff-issue.md` が原本、`spec-ir.md`・`spec-gap.md` が指す）——テストは `scaffold.py` の定数を使わず本文を文字列で比べる。
内訳の文言は `scaffold.py` が持ち、`spec-ir.md` の説明が同じ形を示す（テストが本体の出力と文字列で比べる）。
分けない理由: 原本は `handoff-issue.md`・`spec-ir.md`、`scaffold.py` は写しで、本文の生成をテストが文字列で突き合わせる（`out_of_scope` と同じ形）。

## デプロイ経路

プラグイン（カタログと `link-skills.sh` の利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口: `scaffold.py`（書く生成・`--dry-run`・`--check`・`--red-check`）／`check-spec-exit.py` の CLI と `scaffold.py` の関門（`case_rows` を通す）／dev-loop の `spec-gap.md`（本文を読む側）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | `acceptance` を書け、本文の `## 受入基準` に原文のまま（表の見出しつき・`acceptance` の順）写り、原文が機能の `source` に無ければ（区切り・見出しの行を含む）生成が止まる | 書く生成・`--dry-run`（check_ir は全モード） | `check_acceptance`・`acceptance_section` | テストの試料（写る・仕様に無い・別の機能の行・区切り・見出し・空・配列でない・重複・空白・複数行・文字列でない）と変異 |
| A2 | scaffold が内訳を出し、どちらにも無いケースを番号と場所で名指しする（1 件でも名指し・0 件なら 0 と出る） | 書く生成・`--dry-run` | `coverage_lines`・`spec_case_rows` | テストの試料（1 件・0 件・重なり・別の機能の ref・別の機能の acceptance・何も書かない・`.txt`・`spec/formal/`・数えない表）と変異 |
| A3 | 仕様のケースの数え方は #1297 の番号の形（`case_rows`）と同じ | 内訳 | `spec_exit.case_rows` を読む（写さない） | 数えない表・ファイルの試料（Q&A の `No` の表・`.txt`・`formal/`） |
| A4 | `acceptance` を書かない中間表現の生成物（本文・`scaffold/`）は今までと同じバイト | 書く生成・`--check` | 小見出しを `acceptance` があるときだけ足す | `acceptance` を書かない試料で小見出しが無く、節が揃う。既存の試料が全部通る（本文を文字列で比べる試料）。v2 で足せば変更（ケースは全部 回帰） |
| A5 | dev-loop の `spec-gap.md` が Issue の印と節の写しを揃え、`test-scaffold.py` の突き合わせが通る。dev-loop の規定は変えない | 2 つのプラグインの境界 | 節の表は 7 つのまま・小見出しの読み方だけ足す | `test-scaffold.py` の境界の突き合わせ、`check-skill-pointers.py` |
| A6 | `references/spec-ir.md` に「画面」の例を足す | 決まりを読む人 | 「画面のケースの例」 | 例のとおりの試料（画面の行を `acceptance`、ケースを `ref`）をテストが通す |
| A7 | 版を 3 種類で揃えて上げ、`check-all.py` が緑 | CI | 版の行 | `check-all.py`・`check-plugin-versions.py` |
| A8 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: 実際の spec-loop の正本（実案件の仕様）に当てた内訳の数字——仕様のケースの表が `CASE_HEADER` に当たる見出しで書かれているかは正本ごとに違い、
見出しが `ID`・`No` の表は数えない（#1297 の限界）ので、内訳の N が実際のケースより少なくなりうる。正本が手元に無いので測っていない。人間のレビューに回す。

**生成物**: 生成物なし（変更するファイルに生成物は無い。`scaffold/` は正本リポジトリのもので、このリポジトリには無い）。

## 実験と確認の記録

- 試料（`test-scaffold.py`）で内訳と本文を当てる。結果は PR コメントに貼る。

## 未解決・確認待ち

- 内訳の N が実案件で少なく数えられるか（見出しが `ID`・`No` の表）は #1297 の限界で、この周では広げない。

## 既知の限界・決着済みの論点（関門の指摘の採否）

| 指摘 | 出所 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| F1 `rebuild-scope.py` の `Handoff` が `## 受入基準` の節を次の `## ` まで読むので、小見出しの下の先頭セルを等幅にした行（最後の列が Q&A の No）を Red テストのケースと読み違える | Verifier 1・/code-review 1 | 示せる（`acceptance` に `| `F1-3` | … | Q-001 |` を挙げて scaffold し `Handoff` に通すと `Q-001: [F-001-C1, F1-3]`。親が走らせて確認） | 無し（受入基準 A1〜A8 に rebuild-scope は無い。入口に挙げていない読み手） | 残課題（既定の線。手順 8 の振り分け: 直す——利用者に見える誤り。`rebuild-scope.py` の節の読みを小見出しの手前で打ち切る。仕様の穴ではない） |
| F2 表の見出しの行（`| テストケース | … |`）が `acceptance` に通り、`out_of_scope` と食い違う | Verifier 1・/code-review 1 | 示せる（exit=0・見出しの付かない裸の行が本文に写る） | A1 | **直した**（`source_lines(rows_only=True)` で `rows_with_header` の読み方に。試料と変異を足した） |
| F3 内訳の試料の穴（`spec/` の外の `.md`・全角の ref の NFKC） | Verifier 1 | 示せる（変異が素通り） | A2・A3 | **直した**（試料と変異を足した） |
| F4 未証明の項が #1297 の限界で、主張を弱めれば分類が要らない | Verifier 1 | 示せない（BLOCKED に寄せていない） | 無し | 記録だけ（未証明の文を「`CASE_HEADER` に当たる表のケースを数える」までに弱めて PR に書く） |
| N0 件のとき `0 件のうち…` が確認済みに読める | /code-review 1 | 示せる（文言） | 無し | 記録だけ（文言。#1297 の限界） |
| spec_case_rows が NUL を含むファイルを読む（check-spec-exit は読めない側） | Verifier 1 | 示せる（軽微） | 無し | 記録だけ（NUL を含む `.md` はまず起きない） |

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1301-acceptance-cases`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1301`・切った元の参照 `origin/main`（解決した SHA `b874615af572f4d40b20b0071893d8336dbd19c6`）・起点コミット `b874615a`。base は `b874615af572f4d40b20b0071893d8336dbd19c6`（prepare-worktree.sh の出力）。
- 実装を終えた（コミット `6a4e7edd`）。割り目: 割らない（cruise の周）。`test-scaffold.py` は全部回して `OK: 試料 477 件・変異 384 件`（run-serial 越し）。
- 1 パスの指摘対応: F2・F3 を直した（コミット `5c4a2c5b`）。F1 は残課題。**2 パス目の起点・終点**: Verifier 2・/code-review 2 は `5c4a2c5b574c5c229e2babf332adc3b99e83fe74` に当てる。
- （1 パス目の記録）Verifier（別ティア `opus`・`dev-loop:dev-loop-verifier`）と `/code-review` を `6a4e7edde0640f64865c972198854a586e782c22` に当てている。**1 パス目の指摘対応の起点の SHA: `6a4e7edde0640f64865c972198854a586e782c22`**。
- 手順 5 の反証と差し戻し: 実験なし（交絡を潰す対象の実験は無い。変異は試料で当て、陽性対照は `test-scaffold.py` が持つ）。

## 関門の記録

```dev-loop-gates
周の base: b874615af572f4d40b20b0071893d8336dbd19c6
```

- この周の起票: 0 件（不在の周。確認の Issue は親が立てる。周の途中の課題は PR コメントの記録だけ・残課題）
