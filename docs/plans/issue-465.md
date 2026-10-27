# Issue #465 — scaffold.py --check が rules.md（決定表）と spec_ir.json の一致を見ない

`scaffold.py --check` が見るのは `spec_ir.json` ↔ `scaffold/` の 1 本だけで、仕様（決定表）↔ `spec_ir.json` の一致は機械で確かめていない。
中間表現のケースに**仕様の中の番号（`ref`）**を持たせ、生成と `--check` がその番号が仕様の原文に在るかを確かめる。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent`（2026-10-27、利用者が会話で「-absent でまわします」と指示）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`））。**このリポジトリのマージはサイトを再デプロイするので `マージ` の線は効かない**（#476）——PR まで作って止まる。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — ケースの `ref` を許し、`check_ref` で機能の `source` の原文に番号が在るかを見る・docstring の「守らないもの」
- `plugins/spec-loop/references/spec-ir.md` — ケースの `ref` の行
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 手順 2 に `ref` を書く指示・版の 2 行
- `scripts/test-scaffold.py` — 試料と変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.26.0 → 0.29.0。機能の追加で minor。#477・#479・#481 の版と重ならない値）
- `.claude-plugin/marketplace.json` — 同じ版
- `plugins/spec-loop/skills/*/SKILL.md` — 同じ版の 2 行
- `docs/plans/issue-465.md` — この計画

触らない:

- 決定表の値（入力・期待）と中間表現のケースの値の突き合わせ（下の「仕様の穴」で見送った）
- `check-spec-exit.py`

### 同じことを述べている箇所の数

「`ref`」: `spec-ir.md` の表・`scaffold.py` の docstring（守らないもの）・scaffold の `SKILL.md` 手順 2 の 3 箇所。分けない——同じ決定の写し。

## 仕様の穴（不在の線で推奨により決めた）

Issue の案は「決定表の行と `spec_ir.json` のケースを突き合わせ、過不足と値の食い違いで赤」と、
「書式が機械で読めないなら、少なくともケースの出所（R-xx / ケース ID）が仕様に実在するか」の 2 つ。**線は `仕様の穴 = 推奨で決めて起票`**。

- 選択肢: (a) ケースに任意の `ref` を足し、その番号が `source` の原文に在るかだけを見る ／ (b) 仕様の決定表の書式を spec-loop で決め、行と値を突き合わせる ／ (c) `ref` を必須にする
- **決めた値: (a)**
- 理由: 仕様の決定表・テストケースの書式は spec-loop の決まりに無い（`spec-exit.md` は「番号を振っていれば番号の数、振っていなければ表のデータの行の数」と両方を許す）。(b) は書式を決める大きな変更で、既存の正本リポジトリの仕様を書き直させる。(c) は番号を振らない仕様を書き起こせなくなる。
  (a) は Issue の 2 つ目の案そのもので、#465 の実データ（`R-F10` の値を変えた仕様と古い中間表現）は**番号を残したまま値だけ変えた**ので拾えない——**値のずれは拾わない**ことを、確認の Issue に書く。

## 乗るデプロイ経路

プラグイン（`plugins/spec-loop/`）の版を上げてマージ。マージで main へ push されるとサイトが再デプロイされる（`docs/plans/` を足す）。

## 周の在り処

- ブランチ: `issue/465-scaffold-rules-check`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-465`
- 起点: `eab5e13`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `eab5e1387a3fa7587aed615754fcb7bc35cd75e0`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1**: ケースの `ref` が機能の `source` の原文のどれにも無ければ、生成も `--check` も断る（1）。別の番号の一部（`R-F100`・`R-F10a`）は在ることにしない。
- **I2（陽性対照）**: `ref` が原文に在れば通る。`ref` を書かないケースは今までどおり。
- **I3**: `ref` を探すのは機能の `source` の原文（`spec/` の中）だけ——`requirements/` などほかのファイルや、全体の根の外は読まない。
- **I4**: 空・複数行・前後に空白のある `ref` は断る。
- **I5**: 既存の試料と変異が緑。

経路:

| 経路 | 守り方 | 確かめ方 |
| --- | --- | --- |
| 生成（`scaffold.py`）と `--check`・`--dry-run` が通る `check_ir` | ケースの検査で `check_ref` を呼ぶ | 試料: 在る（0）・無い（1）・別の番号の一部（1）・空（1）・`requirements/` にだけ在る（1）・`--check` でも無いと 1 |
| `check_ref` の原文の選び方 | `source` のうち `spec/` の中のファイルだけ | 試料: `requirements/r.md` にだけ番号がある |

各経路の守りを外す変異で赤になる。

生成物: `skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけ・図の書き出しも無い——**生成物なし**。

未証明: なし。

## 未解決の判断

上の「仕様の穴」を確認の Issue #482 で利用者に渡す（台帳の `decisions` に記録）。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 割り目（手順 4 の完了時）: 不在のため訊かず続けた
- 実験: `test-scaffold.py`（試料 200 件・変異 144 件）
- 1 パス目の起点: `c67289f`（この後のコミットは計画ファイルだけ）
- Verifier 1 パス目: 起動（sonnet）
- `/code-review` 1 パス目: 起動（high）

## 起票

- この周の起票: 1 件（仕様の穴の確認の Issue。起票の承認は不在のため訊いていない）

## 既知の限界・決着済みの論点

- 値（入力・期待）の突き合わせはしない——番号を残したまま値だけ変えた仕様は拾えない（仕様の穴として推奨で決めた。確認の Issue）。
- `ref` は任意——番号を振らない仕様の機能には書けない。
