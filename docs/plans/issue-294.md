# Issue #294 — `--red-check` と受入基準が前提にする実装の状態（#280・#281・#282 のまとめ）

## 決めたこと（前提）

- **P1. Red テストと受入基準は、実装が前の版の状態にあることを前提にしない。**
- **P2. `--red-check` は前提を自分で確かめる**——前の版（v<n-1>）の全体から Red テストを一時ディレクトリに作り
  （`scaffold/` には書かない）、同じ実装に当てる。ケースごとに「前の版のテスト」と「作業中の版のテスト」の結果を並べて判定する:

  | ケース | 今の版 | 前の版 | 既定（初めて作る） | `--in-progress`（作り直し） |
  | --- | --- | --- | --- | --- |
  | 回帰 | 緑 | — | 期待どおり | 同じ |
  | 回帰 | 失敗 | — | 1（乖離） | 同じ |
  | 追加・変更 | 失敗 | 緑／無い | 期待どおり（Red） | 同じ |
  | 追加・変更 | 失敗 | 失敗 | **1（どちらの版の期待も満たさない）** | 同じ |
  | 追加・変更 | 緑 | 緑／無い | **0 で知らせる（前の版の実装がもう満たす。#281）** | 同じ |
  | 追加・変更 | 緑 | 失敗 | **1（実装は前の版の状態に無い。B）** | **期待どおり（実装済み。#282）** |

  v1 では前の版のテストが無い（「無い」の列）。「実装が無い」の 2（回帰を判定していない）は変えない。
- **P3. 受入基準は周の前後を比べる**——「周の前に緑だった Red テストが、周の後も緑のままであること」（#280）。
  撤去・変更の本文、`handoff-issue.md`、`spec-gap.md`。同じ版の未実装の追加・変更は、撤去・変更の周の前に失敗していてよい。
- **作り直しの経路**（この版の Issue をもう登録し、dev-loop が実装を始めている）は `--red-check --in-progress`（scaffold SKILL 手順 4）。
- 文言の写し: `scaffold.py` の定数 `PREMISE`（P1）と `KEPT_GREEN`（P3）を、scaffold `SKILL.md`・`handoff-issue.md`・
  `spec-gap.md` がそのまま持つ——`test-scaffold.py` が突き合わせる。本文は `KEPT_GREEN` を持つ。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py`
- `plugins/spec-loop/skills/` — scaffold SKILL.md の手順 4・7（全スキルの版の 2 行）
- `plugins/spec-loop/references/handoff-issue.md`
- `plugins/spec-loop/README.md` — `--red-check` の説明と usage
- `plugins/spec-loop/.claude-plugin/plugin.json`
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md`
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `scripts/test-scaffold.py`
- `docs/plans/issue-294.md`
- `docs/plugins/` — 生成ブロック（skill-metrics）が動いた場合だけ

触らない: `docs/plans/issue-264.md`（前の周の記録。決めたこと 5 はここで置き換える）、`diff-versions.py`・`merge-versions.py`

## 乗るデプロイ経路

main への merge → GitHub Pages（`docs/` に触れた場合）とプラグインカタログ（版の bump。利用者は `plugin update`）。

## verify の受入基準

不変条件（各 A〜D は Issue の受入基準）:

| # | 不変条件 | 破りうる経路 | 守り方・証拠 |
| --- | --- | --- | --- |
| A1 | #281 の 3 形（既存の振る舞いのケースを足す・入力だけ変える・型を狭めて整数を返す）で `--red-check` が 0、もう緑のケースを名指しで知らせる | `red_check` の判定 | 試料 3 本 |
| A2 | #282 の 2 形（v1 で正しい実装・v2 の変更を実装済み）で `--red-check --in-progress` が 0 | 同上・引数の解析 | 試料 2 本 |
| A3 | #280: 撤去の本文の受入基準が「周の前に緑だった…」で、同じ版で足した機能が未実装でも満たせる（撤去の前後で緑の集合が減らない） | `issue_body`（撤去・変更）・`handoff-issue.md`・`spec-gap.md` | 試料で前後を実際に回す |
| B1 | 変更のケースが前の版のテストで失敗し今の版で緑（実装は前の版に無い）なら既定で 1、理由を名指し | `red_check` | 試料 |
| B2 | 追加・変更のケースがどちらの版でも失敗するなら 1 | `red_check` | 試料 |
| B3 | 回帰が失敗すれば 1（既存）、実装が無ければ 2（既存） | 同上 | 既存の試料 |
| C | P1・P3 の文言が 3 箇所に 1 回ずつ、写しが突き合わせに載る | 文書 3 つ | `test-scaffold.py` |
| D | 決定を外す変異（前の版のテストを見ない・`--in-progress` を無視・もう緑を 1 に戻す・本文の文言を戻す）で赤 | 本体 | 変異テスト |
| E | 他の引数の組（`--in-progress` を `--red-check` 以外と）は 2 | `main` | 試料 |
| F | `--red-check` は何も書かない（前の版のテストは一時ディレクトリ） | `red_check` | 試料で `scaffold/` と根を比べる |

掛け算: 受入基準 × 2 関門 × 2 パス = 4 つの受け渡し。

**未証明**: 前の版のテストを、正本と開発のリポジトリが別の構成で当てた結果（既存の「守らないもの」の行のまま）。
**生成物**: `skill-metrics.py` の生成ブロック（dev-loop の SKILL.md は版の 2 行だけ——行数は変わらない見込み。`--check` で確かめる）。
図なし。`scaffold/` は試料の中だけ。

複製の数: 前提の文言は scaffold.py（本文・docstring）・SKILL.md・handoff-issue.md・spec-gap.md・README の 5 箇所。
Issue が 1 周で決めることを求めている（3 件が互いに依存）ので分けない。文言は定数の写しにして突き合わせで縛る。

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/294-red-check-premise`・worktree `.claude/worktrees/issue-294`・起点 `e024b98`・
  base 参照 `origin/main` = `e024b980f093851d15c4e0ba574ff4ba08fc1043`
- 関門: まだ
- 反証・差し戻し: まだ
- 交絡: まだ

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| もう緑の追加・変更を 1 で止めるか | 止めない（0 で名指しして知らせる） | 前の版のテストも緑なら、実装は前の版にあり、変化を Red テストが判別しないだけ。判別しないのが仕様の書き起こしの誤りかは意味の問題で、スクリプトは守らない（docstring の「守らないもの」）——SKILL 手順 4 で利用者に示す |
| v1 で実装があるとき | 0 で知らせる（前は 1） | v1 には前の版のテストが無く、「通るはずがない」とは言えない。実装が無い状態で全部が失敗することは「実装なし」の試料が見る |
| 撤去したケースの前の版のテスト | 見ない | 求めない振る舞い。撤去の Issue が扱う |
