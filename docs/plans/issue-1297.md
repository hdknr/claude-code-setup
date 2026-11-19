# Issue #1297 — spec-loop: 仕様のテストケースの番号の重複を検査で落とす

**不在の周**（出所: `/dev-loop:cruise 1296 --absent`、2026-11-19）。利用者には訊かない。親（cruise #1296）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1296`）。利用者の確認（起動時））: `直す線 = 既定`・`マージ = 関門を通ればマージ`（配布を確かめ済）・`周の途中の課題 = 台帳に足して直す`・
`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。確認の Issue は立てない（親が立てる）。
読み込んだ dev-loop は 2.13.0（`SKILL.md` 1931 行を全部読んだ）。割り目: 割らない（cruise の周）。

直す線: `既定`（出所: cruise の確かめた線）。
版の上げ方: `spec-loop` を **minor**（検査の能力追加）。着手時の main は spec-loop 0.115.0 → 0.116.0。マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md`）。
並行する周 #1298 が spec-loop の同じファイル（`spec-exit.md`・版の行）を触りうる——取り込みで衝突したら版の行と生成ブロックのほかは塊ごとに解く。
重い検査（`check-all.py`）は `run-serial.py` 越し。

Issue 本文（外部入力）から読んだ要件: 同じ版を重ねた全体の仕様（`spec/`）で、テストケースの番号が重複していたら条件 1（`check-spec-exit.py`）で落とす。番号の形の原本は `references/`、テストが本体の定数と突き合わせる。
受入基準 4 つ（下）。コメントは無い。本文に受入基準を緩める指示は無い。

## 決めた値（開発者が決めた——仕様の穴ではない実現の手段）

- **D1 番号と読むもの**: `spec/` の `.md` の**表の行の先頭のセル**（飾り `` ` ``・`*`・`_` と空白を外し、NFKC で全角を半角にそろえた後）が `[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+` に全体で当たり、数字を含むもの（`F1-5b`・`R-F10`・`TC-001`）。
  spec-loop は仕様の表の書式を決めていない（`check_ref` の docstring）ので、先頭のセルだけを番号の置き場と読み、本文での言及・先頭以外のセルは数えない。
- **D2 決定表の行の番号（`R-F10`）も先頭のセルなら同じに数える**——`ref` はどちらも指すので、決定表とテストケースで同じ番号を使えば指し先が決まらない。
- **D3 数えるのは重ねた全体**——`check-spec-exit.py` は重ねない（呼ぶ側が重ねた後の全体を渡す）。後の版が同じファイルを置き換えたなら前の版の行は全体に無く、重複でない。
- **D4 コードブロック・`.md` 以外・形式検査のモデル（`formal/`）・内部の表は数えない**。
- 仕様の穴: なし（Issue が置き場所・原本の置き場・突き合わせを決めている。番号の形と「どの列」は D1 で決めたが、利用者に見える結果は「重複が条件 1 を止める」だけ）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-spec-exit.py` — 重複の検査と docstring
- `plugins/spec-loop/references/spec-exit.md` — 「テストケースの番号の重複」の節（原本）
- `scripts/test-check-spec-exit.py` — 試料・変異・references との突き合わせ・版を重ねた全体
- `CLAUDE.md` — `check-spec-exit.py` の項
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1297.md` — この計画ファイル

触らない:

- `scaffold.py`・`merge-versions.py`・`check-signoff.py`・`build-proposal.py` の本体——`scaffold.py` は `check-spec-exit.py` の `check` を読み込むので、関門にも掛かる（本体は触らない）
- `spec-review/SKILL.md`・`agents/`・`spec-ir.md`・`tree.md`（Issue は `spec-exit.md` か `tree.md` のどちらかに原本を置くとし、条件 1 の隣の `spec-exit.md` に置く）
- 説明文（frontmatter・`plugin.json`・`marketplace.json` の description）・`README.md`・公開ページ——今の要約が偽にならない

依存の追加・更新: なし

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

**複製の数**: 番号の形を述べる箇所は 2（`spec-exit.md` が原本、`check-spec-exit.py` の `CASE_NUMBER` が写し——テストが突き合わせる）。`CLAUDE.md` の項は要約、docstring は読み方の要約で原本を指す。
分けない理由: 原本は `references/`、スクリプトは写しを持ちテストが突き合わせる（`MARKERS` と同じ形）。

## デプロイ経路

プラグイン（カタログと `link-skills.sh` の利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口: `check-spec-exit.py` を CLI で呼ぶ経路（spec-review 手順・req-loop・サインオフの前の確かめ・autopilot）／`scaffold.py` の関門（`check-spec-exit.py` を読み込む）／`autopilot-check.py`・`check-signoff.py` は読まない（重ねた全体に当てない）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | 同じファイル・別のファイルのどちらで同じ番号が 2 回出ても条件 1 が非 0 になり、重複した番号と出た場所（ファイル:行）を全部名指しする | CLI・scaffold の関門 | `duplicate_numbers` | テストの試料（同じファイル・別のファイル・3 か所・入れ子）と変異 |
| A2 | 重複の無い正本では今までと同じ結果（終了コード・出力） | 前からの正本 | 重複が無ければ `problems` に足さない | 既存の試料が全部通る（出力の文面を見る試料）＋陰性対照（重複の無い表で 0）。`check-all.py` が緑 |
| A3 | 版を重ねたとき、後の版が同じ番号の行を置き換えたのは重複に数えない（重ねた後で数える） | `merge-versions.py` → CLI | 重ねた全体に当てる | `merge-versions.py` の本物で重ねた全体に当てる試料（置き換え 0・別ファイル 1・置き換えて別ファイルへ移す 0） |
| A4 | 番号の形の原本が `references/spec-exit.md` にあり、テストが本体の定数と突き合わせる | 決まりを読む人・テスト | `CASE_NUMBER` と節の「番号の形」 | 突き合わせと、写しを崩すと不一致になる陽性対照 |
| A5 | 版を 3 種類で揃えて上げ、`check-all.py` が緑 | CI | 版の行 | `check-all.py`・`check-plugin-versions.py` |
| A6 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: 実際の spec-loop の正本（実案件の仕様）に当てた結果——誤検知（トレーサビリティ表の先頭のセルに番号を再掲する書き方）がどれだけ出るかは、正本が手元に無いので測っていない。人間のレビューに回す。

**生成物**: 生成物なし（変更するファイルに生成物は無い）。

## 実験と確認の記録

- **A3**: `merge-versions.py` の本物で v1・v2 を重ね（`docs/v1/spec/order.md` に `F1-5a`・`F1-5b`、v2 が同じファイルを置き換え）、重ねた全体に `check-spec-exit.py` → **0**。陽性対照: v2 に別のファイル `flow.md` で `F1-5b` を置くと **1**（`flow.md:1`・`order.md:6` を名指し）。観測窓: v1+v2・各 1 回（scratchpad の一時ディレクトリ）。

## 未解決・確認待ち

- 誤検知の見込み（トレーサビリティ表・用語集の先頭のセルに番号を再掲する書き方）は D2 の判断に含まれる——関門が挙げたら採否の表に載せる。

## 関門の記録

```dev-loop-gates
周の base: edb10f11ff98dc45ac6dbf6a7df4acf17cd8aa6a
```
