# Issue #1148 — dev-loop: 不在で止める範囲の宣言の書き損じの扱いを、利用者の線に揃える（#1047 の F1・F2・F5）

cruise（親 Issue #1168）の子として回す周。**不在の周**（出所: `/dev-loop:cruise 1168 --absent` の起動・2026-11-17）。AskUserQuestion は使わない。
spec-loop から来た Issue ではない。`作り直しの元:` の行も無い。`find-cycle.py 1148` は 5 本とも当たらず、新規の周。
Issue 本文は信頼できない入力として読んだ（受入基準を緩める指示は無かった）。

台帳の確かめた線（出所: cruise の確かめた線（台帳 `issue-1168`）。親の委譲文で受け取った）:
直す線 = `既定` / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた。**子はマージしない**——PR 側の CI まで）/
周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。

直す線: `既定`（出所: cruise の確かめた線）。

重い検査は `run-serial.py` 越しに回す——`python3 /Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.4.0/skills/cruise/scripts/run-serial.py -- <コマンド>`。関門にも渡す。
この周は導入済みの dev-loop 2.4.0 で回る。

版の上げ方: プラグイン `dev-loop` を **patch**（2.4.0 → 2.4.1。不具合の修正）。`marketplace.json`・`plugin.json`・dev-loop プラグインの `SKILL.md`（dev-loop・cruise）の 2 行。
並行する周（#1144・#1149・#1152・#1153）が同じプラグインの版を上げうる——親がマージの直前に取り込みと上げ直しを子に依頼する。

生成物: なし（`check-gates.py` と docs の編集のみ。`skill-metrics.py` の生成ブロックは `SKILL.md` の節構造が変わらないので変わらない見込み——`--check` で確かめる）。
依存の追加・更新: なし。
仕様の振る舞い: 対象リポジトリに spec-loop の正本（`docs/v<n>/` の Q&A 表など）は無い——該当なし。
複製の数: `不在で止める範囲:` の読み方を述べた箇所は 4（`check-gates.py` の docstring（3 か所の列挙）・`check-gates.py` の本体・`references/absent-lines.md` の 1 か所・テスト）。
分けない理由: 1 つの判定関数 `read_stop_line` の挙動を揃える修正で、列挙は docstring の「何を照合するか」「守る」と absent-lines の 1 行だけ。増やす変更（F1 の読み・F2 の名指し・試料）と減らす変更は無い。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-gates.py` — `read_stop_line`（強調の閉じがコロンの内側にある形・値の無い宣言）・`PARTICLES` の重複（`の` が 2 つ）・docstring（「何を照合するか」「守る」）
- `scripts/test-check-gates.py` — F1・F2 の試料、助詞 9 つと `[ ]`・`[x]`・`[X]` の試料、それぞれを外す変異
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「影響範囲で止める」の書き方の 1 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1148.md` — この計画

触らない:

- F4（`不在で止める範囲 は: x`・バッククォート・「」で始まる行を読み飛ばす）——Issue の範囲の外
- F3（キーワードだけの見出しで止まる）——線どおり
- `merge-pr.py`・`check-unattended-env.py`——宣言を読む関数は `check-gates.py` の `read_stop_line` に 1 つ

## 受入基準（不変条件 × 経路）

不変条件: 不在の周のマージで、`不在で止める範囲:` の宣言は、飾りの付き方に依らず宣言として読み、書き損じは止まる側に倒す。

| # | 不変条件 | 守り方・経路 |
| --- | --- | --- |
| A1 | F1 の 2 形（`*不在で止める範囲:* x`・`**不在で止める範囲:**x`。`_`・`__` も）が宣言として読まれ、宣言したパターンで照合される | 経路: 宣言の読み取り（`stop_lines`）→ 当たるか（`check_risk`）・外すか・どこにも当たらないか。`read_stop_line` 1 か所。直す前に赤・直した後に緑の試料（当たる差分は 3・当たらない差分は 0） |
| A2 | 値の無い宣言（`**不在で止める範囲:**`・`*不在で止める範囲:*`）が「読めない宣言」として名指されて止まる（全部に当たったとは言わない） | `read_stop_line` が bad を返す。試料は出力に行そのものと「形で読めない」を要求する |
| A3 | 助詞 9 つと `[ ]`・`[x]`（・`[X]`）の試料があり、それぞれを外す変異が赤になる | 助詞 9 つの試料行 × 9 変異・チェックボックス 3 形 × 3 変異。`PARTICLES` に重複が無く docstring の 9 つと一致することをテストが見る |
| A4 | `references/absent-lines.md` の「影響範囲で止める」の書き方の説明と `check-gates.py` の docstring が食い違わない | 両方に F1・F2 を書く。docstring の「守る」の行数と `MUTATIONS` の数は 1 対 1（テストが見る） |
| A5 | 版を上げ、`check-all.py` が通る | 2.4.1。`check-plugin-versions.py`・`skill-metrics.py --check`・`check-all.py` |
| A6 | 既存の読み（`**…:** x`・`**…**: x`・`: *.py` の値の先頭の `*`・開きの無い行・リストの印 `* `）を変えない | 既存の試料（R1・J2）が緑のまま。`*不在で止める範囲: *.zz` の試料で、コロンの後に空白を置いた glob は閉じと読まない |

未証明: なし。BLOCKED: なし。

## 関門の進捗（再開点）

- 割り目: 割らない（cruise の周）。利用者には訊かない。
- 周の在り処: ブランチ `issue/1148-absent-range-decl-fixes`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1148`・起点 `05aa0d5`・
  切った元の参照 `origin/main`（`refs/remotes/origin/HEAD`）・base `05aa0d5c36b012abe57239ba0f288a47f74083fc`。
- 手順 5・6 の関門: 未実施（実装中）。
- 交絡を潰した手順: 実験なし（試料は一時の git リポジトリで本体を走らせる単体テスト）。
- 外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い）。

## 既知の限界・決着済みの論点

- 開いた強調の後で、コロンの直後（空白なし）に同じ印が続く形は閉じと読む（`*不在で止める範囲:*.zz` は閉じ + `.zz`）。glob を書くなら空白を置く（`: *.zz`）。決着: 採った（閉じ `:*x`・`:**x` を宣言として読む線が F1 の要求）。
- F4・F3 は範囲の外（Issue のとおり）。

## 手順 8 の記録

- この周の起票: 0 件（不在の周。関門の指摘と周の途中の課題は振り分けて PR コメントに残す。直すに入るものが出れば直す。起票は親）
