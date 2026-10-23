# Issue #352 — check-signoff の照合の残り（#348〜#351 のまとめ）

## 変更範囲

触る:

- `scripts/test-check-signoff.py` — 試料を 1 度だけ作り、変異は殺すはずの試料だけに当てる（A。#350）。試料の直し・足し（B・C）。パスが 1 度だけ出ることの assert（D）
- `plugins/spec-loop/scripts/check-signoff.py` — `provisional_rows` で種類 `ファイル` の行の 2 形（構造ファイル・2 度消す）と v1 の `removed.csv` を 2 にする（B。#348）。拒否のメッセージの前置きからパスを外す（D。#351）。docstring
- `plugins/spec-loop/scripts/merge-versions.py` — v1 の `removed.csv` の拒否の文言を定数 `V1_REMOVED` に出す（**振る舞い・文言は変えない**。`check-signoff.py` が写さずに使う）
- `CLAUDE.md` — `check-signoff.py` の説明の「2 にしない」の範囲（B）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（minor: 0.18.1 → 0.19.0。照合の答えが変わる形が増える）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 同上（版の 2 行だけ）
- `docs/plans/issue-352.md` — この計画

触らない:

- `merge-versions.py` の `check_removed` の文言・条件（`Whole.apply` と共有）
- `references/versions.md`（決まりそのもの）
- 予算の合意のタグの時点の配置（今までどおり見ない）
- `qa.csv` の拒否のメッセージ（#351 は `removed.csv` の分だけ）

### 同じことを述べている箇所の数

- 「2 にする／しない配置の範囲」: `CLAUDE.md`・`provisional_rows` の docstring・テストの docstring の 5 番 —— 3 箇所。分けない理由: 同じ関数の振る舞いを述べる 3 つで、実装と同時に変わる
- 拒否のメッセージ: 本体の 2 箇所（`read_removed_at`・`provisional_rows`）＋ テストの期待文字列

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/plans/` は main への push で Pages に載る。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 試料（git リポジトリ）は 1 回の実行で 1 度だけ作る。本体は試料を書き換えない（読むだけ）ので使い回せる | `run_all`・変異の回し方 | 試料を作る関数と走らせる関数を分ける |
| A2 | **変異の捕捉を減らさない**: 変更前後で全変異が赤（変更前も変異は殺すはずの試料しか見ていない） | 変異のループ | 変更前のテストも変異ごとに**殺し手の試料 1 つの結果だけ**を判定していた（他の試料の結果は捨てていた）ので、殺し手だけを走らせても判定は同じ。変更後に既存 43 件の変異が全部赤であることを実測する |
| A3 | 実行時間を前後で記録する | — | `time` の実測を PR に書く |
| B1 | `ファイル,shared/qa.csv`（構造ファイル）を消す配置で 2 | `provisional_rows` | `check_removed` |
| B2 | 同じファイルを 2 度消す配置で 2 | 同上 | `check_removed` |
| B3 | v1 に `removed.csv` を置くと 2 | 同上 | `ls-tree` で在るかを見る。文言は `merge-versions.py` の `V1_REMOVED` |
| B4 | 拒否の条件式を写さない（`check-signoff.py` に構造ファイルの一覧・重複の条件が無い） | 本体 | 目視＋grep |
| B5 | 前の版までに無いファイルを消す・同じ版で置きつつ消すファイル（版のファイルの一覧が要る）は 2 にしない。理由を `CLAUDE.md` と docstring に 1 か所ずつ | 文書 | 文 |
| B6 | B1〜B3 の配置を `merge` も拒否する | 試料 | `REFUSED_CASES` に入れて突き合わせる |
| B7 | 陽性対照: 正しい配置（`removed.csv` の範囲の外の行・shared のファイルの行）は今までどおり 0 か 1 | 既存の試料 | 緑のまま |
| C1 | 試料「removed.csv だけ違う」の作業ツリー（予算側）を `merge` が受け付ける | 試料 | `merge` の problems が空であることを見る |
| C2 | 要求確定側と予算側を入れ替える変異（`at_req` → `at_budget`）が、**別の試料**で赤 | 新しい試料（要求確定側だけが拒否する配置） | 変異を足す |
| D1 | 拒否のメッセージ（形式の違反・配置の違反・v1）にパスが 1 度だけ出る | `read_removed_at`・`provisional_rows` | 前置きからパスを外す。出力の出現回数を assert |
| E | `check-all.py` と CI が緑・版が 3 種類で揃う | — | `python3 scripts/check-all.py`・`gh pr checks` |

組み合わせ: A × B/C（足した試料・変異も 1 度作りで当たる）。B × D（足した拒否の経路もパスが 1 度）。C × B（入れ替えの変異は B の試料ではなく C の試料で殺す）。
B × merge-versions の利用者（`Whole.apply` の文言は定数に出すだけ）——`test-merge-versions.py`・`test-scaffold.py`・`test-diff-versions.py` が見る。

**未証明**: なし（すべてローカルの git 試料で当てられる）。
**生成物**: 図・`SKILL.md` の測定値（dev-loop のみ）に関係しない。**生成物なし**。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/352-signoff-remainders`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-352`・起点 `4e498b2`・base の参照 `origin/main`（SHA `4e498b28d799d41a8774386b17af8e2f3108b802`）
- 実装: 済み（コミットは下）。`test-check-signoff.py` 変更前 **612.8 秒**（試料 58・変異 45。main `4e498b2`）→ 変更後 **25.1 秒**（試料 62・変異 51。既存の 45 件はすべて赤のまま）
- 陽性対照: 新しいテストを直す前の `check-signoff.py`（`4e498b2`）に当てると、B の 3 試料が 3 を返し、パスが 2 度出る 6 試料が D で落ちた（17 件の失敗のうち残り 9 件は新しいコードにしか無い文字列の変異の「届いていない」）
- 交絡: 前の測定は他のテストと同時に回した時間を含む（同じ機械・ほぼ同時刻）。桁が違う（24 倍）ので結論は変わらない
- 割り目 1（手順 4）: 未

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 前の版までに無いファイル・同じ版で置きつつ消すファイルを 2 にするか | 採らない | 版ごとのファイルの一覧（`merge-versions.py` の `list_files` の決まり）を git の上で作り直すことになり、写しになる |
| 種類 `機能` の行の配置 | 採らない | 同上（`spec_ir.json` を版ごとに重ねる必要がある）。#352 の範囲外 |
| 予算側の配置 | 見ない | 今までどおり。予算側の違いは共有の範囲の比較で 1 になる |
