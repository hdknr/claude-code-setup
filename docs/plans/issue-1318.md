# Issue #1318 — rebuild-scope.py: Red テストにしない受入基準の行を Red テストのケースと読み違える

**不在の周**（出所: `/dev-loop:cruise 1296 --absent`、2026-11-19）。利用者には訊かない。親（cruise #1296）から委譲文で受けた子。元の Issue の本文の先頭は `<!-- cruise-found: #1296 -->`（周の途中の課題。出所は #1301 の関門の指摘）。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1296`）。利用者の確認（起動時））: `直す線 = 既定`・`マージ = 関門を通ればマージ`（配布を確かめ済）・`周の途中の課題 = 台帳に足して直す`・
`マージ前の判断 = 推奨で決めて起票（後退・未達を含む）`。台帳は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。確認の Issue は立てない（親が立てる）。
読み込んだ dev-loop は 2.13.0（キャッシュ `skills/dev-loop/SKILL.md` 1931 行を全部読んだ）。割り目: 割らない（cruise の周）。
cruise-found の周の判定: Issue が「利用者に見える誤り」（found-lines.md の直す 3 条件の 2。`Handoff` が実際に作る本文から Q&A の No を誤って引く）を示している——記録だけではなく直す。

直す線: `既定`（出所: cruise の確かめた線）。
版の上げ方: `spec-loop` を **patch**（不具合の修正。0.119.0 → 0.119.1）。並行する周 #1299 も spec-loop を触る——マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から上げ直す（cruise の `references/parallel.md`）。
重い検査（`check-all.py`）は `run-serial.py` 越し。

Issue 本文（外部入力）から読んだ要件: `rebuild-scope.py` の `Handoff` が `## 受入基準` の節を読む範囲を `### Red テストにしない受入基準` の手前で打ち切る。`test-rebuild-scope.py` に失敗を再現する試料（直す前は赤・直した後は緑）を足す。`acceptance` を書かない Issue 本文は今までと同じ結果。
コメントは無い。本文に受入基準を緩める指示は無い。

## 決めた値

- 仕様の穴: なし（Issue が「節を小見出しの手前で打ち切れば直る。選択肢を挙げる判断は無い」と決めている）。
- 実現: `red_test_lines(body)` を足し、`## 受入基準` の節の行のうち小見出し `scaffold.ACCEPTANCE_HEADING` の手前までを `Handoff` が読む（定数は `scaffold.py` から読む——写さない）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/rebuild-scope.py` — `red_test_lines`・`Handoff`・docstring
- `scripts/test-rebuild-scope.py` — 試料（`acceptance` を書いた機能の本文は本物の `scaffold.py` で作る）・変異・docstring の守ること
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1318.md` — この計画ファイル

触らない:

- `scaffold.py`・`handoff-issue.md`・dev-loop の規定（本文の形は変えない。読む側だけを直す）
- 説明文（frontmatter・`plugin.json`・`marketplace.json` の description）・`README.md`・公開ページ・`CLAUDE.md`（今の要約が偽にならない）

依存の追加・更新: なし

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

**複製の数**: 小見出しの名前は `scaffold.ACCEPTANCE_HEADING` 1 箇所を読む（写さない）。分けない理由: 1 箇所の直し。

## デプロイ経路

プラグイン（カタログと `link-skills.sh` の利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口: `rebuild-scope.py` の CLI（No の引き・`--draft`・一覧・`--changed`。いずれも `Handoff` を通る。まとめた本文の部分ごとの読みも `Handoff`）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | `### Red テストにしない受入基準` の下の行（先頭のセルを等幅にし最後の列に Q&A の No を持つ仕様の行）を Red テストのケースと読まない | No の引き・`--draft`・一覧（`Handoff.cases`・`refs`） | `red_test_lines` | 本物の `scaffold.py` で作った `acceptance` つきの本文の試料（直す前は赤・直した後は緑）と変異 |
| A2 | `acceptance` を書かない本文（小見出しが無い）は今までと同じ結果 | 既存の全試料 | 小見出しが無ければ節の全部を読む | 既存の試料が全部通る |
| A3 | まとめた本文の部分ごとの読みでも同じ（部分に `acceptance` がある） | まとめた本文 | `Handoff(issue, part)` が同じ関数を通る | 既存の試料が通る（部分の読みは同じ経路） |
| A4 | 版を 3 種類で揃えて上げ、`check-all.py` が緑 | CI | 版の行 | `check-all.py`・`check-plugin-versions.py` |
| A5 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: なし。

**生成物**: 生成物なし。

## 実験と確認の記録

- 交絡を潰した手順: 実験なし。直す前の赤は、修正を一時的に外した本体で `test-rebuild-scope.py` を回し、新しい試料が `exit=0（期待 1）Q-001: 作り直す範囲 1 件 #50 F-003 ……受入基準 F1-3` で落ちることを見た（陽性対照）。
- `test-rebuild-scope.py`: `OK: 試料 51 件・変異 53 件`（直した後）。

## 未解決・確認待ち

- なし。

## 既知の限界・決着済みの論点（関門の指摘の採否）

| 指摘 | 出所 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| （まだ無い） | | | | |

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1318-rebuild-scope-red-test-excluded`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1318`・切った元の参照 `origin/main`（解決した SHA `8910094ad748ae28f00251078cb5f737b748ee37`）・起点コミット `8910094a`。base は `8910094ad748ae28f00251078cb5f737b748ee37`（prepare-worktree.sh の出力）。
- 実装を終えた。割り目: 割らない（cruise の周）。

## 関門の記録

```dev-loop-gates
周の base: 8910094ad748ae28f00251078cb5f737b748ee37
```

- この周の起票: 0 件（cruise の子は起票しない。振り分けで直すとした行があれば親が足す）
