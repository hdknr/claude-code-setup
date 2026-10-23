# Issue #365 — feasibility の規模の物差しに、レビューで増える量を使わない

## 変更範囲

触る:

- `plugins/spec-loop/skills/feasibility/SKILL.md` — 手順 2 に「レビューの指摘で増える量を主な物差しにしない」「使うなら補助で、時点を記録」。`CLAUDE.md` の数え方がそれに依る場合の扱い
- `plugins/spec-loop/agents/estimate-checker.md` — 見るものに「物差しがレビューの回数で動く量に依っていないか」。description にも 1 語
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（minor: 0.19.0 → 0.20.0。手順の追加）
- `.claude-plugin/marketplace.json` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 同上（版の 2 行だけ）
- `docs/plans/issue-365.md` — この計画

触らない:

- `references/feasibility-csv.md`（列は変えない。根拠の列の書き方は今のまま）
- 公開ページ `docs/plugins/index.md`・`plugins/spec-loop/README.md`（検証役の観点を列挙していない）
- スクリプト（物差しは散文の規定で、機械で判定する形が無い）

### 同じことを述べている箇所の数

- 「物差しにしない量」: `feasibility/SKILL.md` 手順 2 と `estimate-checker.md`（本文と description）—— 3 箇所。
  分けない理由: 書く側と突く側で役が違い、片方だけだと牽制にならない（Issue の「やること」も両方）

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/plans/` は main への push で Pages に載る。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | feasibility は、仕様レビューの指摘で増える量（テストケースの数・仕様の行数）を規模の**主な**物差しにしない。規模は要求から決まる単位（画面・API・バッチ・テーブル・設計の変更項目など）で数える | (a) `CLAUDE.md` に数え方が無い（汎用の表） (b) **`CLAUDE.md` の数え方がテストの数に依る** (c) v2 以降の差分モード（差分にテストの追加が「変更」として出る） | 手順 2 の規定が 3 経路すべてに掛かる書き方になっている（(b) は「はじめに」の表からも手順 2 に届く） |
| A2 | テストの数を使うなら補助の指標にとどめ、**どの時点の数か**（コミット・日付など）を規模の文書に記録する | 手順 2 の出力（`feasibility/` の文書） | 手順 2 に書く |
| A3 | estimate-checker は「物差しがレビューの回数で動く量に依っていないか」を突き、補助の数に時点が書かれているかも見る | agent の定義（手順 6 の委譲は定義を使う） | `estimate-checker.md` の「見るもの」 |
| A4 | 既存の規定（根拠の無い金額を書かない・差分モード・単価が無ければ金額を書かない）を弱めていない | 手順 2・3 | 差分を読む |
| A5 | 版が 3 種類で揃い、歯止めが全部緑 | `marketplace.json`・`plugin.json`・`SKILL.md` 5 本 | `check-all.py`、PR の `gh pr checks` |
| A6 | 事実の主張（Issue の実データの数字を引くなら）が Issue と一致する | 本文 | 引くなら Issue と照合 |

### この環境では証明できないもの（未証明）

- **実行時に LLM が規定に従うか**——spec-loop には Eval が無く、実案件の正本リポジトリも手元に無い。
  文面が 3 経路に掛かる書き方になっているかまでを関門に見せ、従うかは人間レビューに回す。

### 生成物

- **生成物なし**——`skill-metrics.py` は dev-loop の `SKILL.md` だけを測る。図・スクリプトの生成物に触れない。

## 未解決の判断

- `CLAUDE.md` の数え方がテストの数に依る場合: その数え方に従わず（補助に回し）、手順 7 の報告に名指しする、と決めた。
  正本の決まりを上書きする形になるので、PR で人間に確かめる。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/365-feasibility-scale-yardstick`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-365`・
  起点 `04bcc12`・base 参照 `origin/main` → `04bcc12dc5f07d2aef7d2813322c808959a5fe04`
- 実装: 済（コミット済み。`check-all.py` 44/44 緑）
- 割り目 1（手順 4 の後）: 提案済み——選択「ここで割る」（2026-10-23）。再開は手順 5 の 1 パス目から
- 関門: 未着手（次は 1 パス目の Verifier と `/code-review`）
- 反証・差し戻し: なし
- 交絡: 実験なし

## 既知の限界・決着済みの論点

（なし）
