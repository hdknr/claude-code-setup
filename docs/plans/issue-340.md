# Issue #340 — check-signoff の暫定反映の照合で、案内のテストと merge と食い違う重ね方を直す（#336・#338 のまとめ）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/merge-versions.py` — `Whole.apply` の `removed.csv` の拒否（2 度消す・ファイルとしては消せない・同じ版で置きつつ消す・前の版までに無い）を関数 `check_removed` に出す。**振る舞いは変えない**（メッセージの文言も同じ）
- `plugins/spec-loop/scripts/check-signoff.py` — `provisional_rows` の拒否を `check_removed` で行う（B）。`removed.csv` の読み込みを 1 か所にまとめ、`resolve` で読んだものを `provisional_rows` に渡す（C）。docstring の終了コード 3 の案内を「両方」に揃える（A の文言の原本との食い違い）
- `scripts/test-check-signoff.py` — A・B の試料・変異・`merge` との突き合わせ
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json`・`plugins/spec-loop/skills/*/SKILL.md` — 版（patch: 0.17.0 → 0.17.1）
- `CLAUDE.md` — `check-signoff.py` の説明（拒否も `merge-versions.py` の関数で、の一言。該当すれば）
- `docs/plans/issue-340.md` — この計画

触らない:

- `merge-versions.py` の拒否の決まりそのもの（`references/versions.md`）
- `removed.csv` の種類 `ファイル`・`機能` の行の照合（共有の範囲の比較は今のまま）
- `build-proposal.py`（照合の 3 をそのまま返すだけ）

### 同じことを述べている箇所の数

- 終了コード 3 の案内「両方を取り直す」: 本体の出力・本体の docstring（**いまは「要求確定」だけで食い違っている**）・`references/signoff-tags.md`・`proposal/SKILL.md` —— 4 箇所。文書側 2 箇所は既に「両方」。
- `removed.csv` の拒否: 原本 `references/versions.md`、実装は `merge-versions.py` の 1 箇所に寄せる（今は `check-signoff.py` に「置きつつ消す」だけの写しがある）。
- 分けない理由: Issue のとおり、3 つとも `check-signoff.py` の同じ関数とそのテストの同じ所を触る。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` の公開ページは触らない（`docs/plans/` は mkdocs の nav 外だがサイトには載る——main への push で Pages）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | 終了コード 3 の案内が「要求確定と予算の合意の両方のサインオフを取り直す」で、テストがそれを見る。文言を要求確定だけに戻す変異で赤 | 本体の出力文字列・docstring | 試料の期待文字列＋変異（実際に当てる） |
| B1 | 前の版までに無い Q&A を `removed.csv` で消す配置で、照合は 2 | `provisional_rows` | `merge-versions.py` の `check_removed` |
| B2 | 同じ Q&A を同じ `removed.csv` で 2 度消す配置で、照合は 2 | 同上 | 同上 |
| B3 | 同じ版で置きつつ消す配置は今までどおり 2 | 同上 | 同上（写しを消す） |
| B4 | 拒否の判定に写しを作らない（`check-signoff.py` に拒否の条件式が無い） | 本体のソース | 目視＋`grep` |
| B5 | 陽性対照: 正しい配置（前の版の行を消す・後の版で置き換える・暫定が残る）は 0 か 3 のまま | 既存の試料 | 既存の試料が緑 |
| B6 | B1・B2 の配置を `merge` も実際に拒否する（試料が `merge` の拒否を表している） | テストの試料 | `merge(docs)` の problems を突き合わせる |
| C1 | `removed.csv` は 1 つのタグの時点・1 つのパスにつき 1 回だけ読む（`provisional_rows` は読まない） | `resolve`・`provisional_rows` | `resolve` で読んだものを渡す |
| C2 | 振る舞いは変えない | 既存の全試料・`test-merge-versions.py`・`test-scaffold.py`・`test-diff-versions.py` | `check-all.py` |
| V | 版が 3 種類で揃い、歯止めが全部緑 | bump 漏れ | `python3 scripts/check-all.py` |

組み合わせ: A × B（拒否で 2 のときは 3 の案内を出さない——2 が先）。B × C（拒否に要る行番号を、まとめた読み込みが落とさない）。
C2 × merge-versions の利用者（`scaffold.py`・`diff-versions.py`・`check-signoff.py`）——`Whole.apply` の振る舞い・文言が変わらないことは各テストが見る。

**この環境では証明できないもの（未証明）**: なし（すべてローカルの git 試料で当てられる）。

生成物: 図・`SKILL.md` の測定値（dev-loop のみ）に関係しない。**生成物なし**。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/340-signoff-provisional-removals`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-340`・起点 `4187a08`・base の参照 `origin/main`（SHA `4187a081088ab5c3037efd7e8d2b2968cb34d5d8`）
- 関門: 未着手
- 反証・差し戻し: なし
- 交絡: 未着手

## 既知の限界・決着済みの論点

（なし）
