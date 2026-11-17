# Issue #1152 — spec-loop: 提案書の「前の版からの変更」に画面の表の変更が出ない（#1091 の後退）

**不在の周である**——cruise（親 Issue #1168）の子として回す。出所: `/dev-loop:cruise 1168 --absent` の起動（2026-11-17）。
確かめた線（台帳 `issue-1168`。出所: cruise の確かめた線）:
直す線 = 既定 / 仕様の穴 = 推奨で決めて起票 / マージ = 関門を通ればマージ（配布を見せて確かめた）/ 周の途中の課題 = 外に出す / マージ前の判断 = 推奨で決めて起票。
#1152 は spec-loop から来た Issue ではない（本文に `spec-loop-handoff` の印は無い）。
この周はマージしない（親がする）——PR を作り、PR 側の CI が通るのを見るところまで（手順 8 は計画ファイルに書くところまで）。
割り目は訊かない——**割らない（cruise の周）**。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/build-proposal.py` — `changes_section` が画面・項目・遷移の変更を件数の表と節に載せる（表があるときだけ）
- `scripts/test-build-proposal.py` — 試料・変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ
- `docs/plans/issue-1152.md` — この計画

触らない:

- `plugins/spec-loop/scripts/diff-versions.py`（比較そのものは #1091 で行の単位になっている。出さないのは `build-proposal.py` の描き側）
- `references/versions.md`・`tree.md`・`skills/proposal/SKILL.md`（節の説明は「種類ごとの追加・変更・削除」で、画面の種類を足しても偽にならない）
- 仕様書（`spec.md`）・PPTX の「前の版からの変更」の節の作り方は同じ `changes_section` を共有するので、別に直さない

複製の数: 比較の節を描く場所は `changes_section` 1 つ（提案書と仕様書が同じ関数を呼ぶ）。分けない理由: 複製は 1。
依存の追加・更新: なし
仕様の振る舞い: 変えない（正本の `Q&A`・仕様に書かれた機能の利用者に見える振る舞いは変わらない。生成物の欠落を直す。このリポジトリは spec-loop の正本ではなくプラグインの置き場）

生成物: なし（`build-proposal.py` の出力は正本リポジトリで生成するもので、このリポジトリに commit される生成物は無い）。

## 決めたこと（仕様の穴）

- 画面・項目・遷移の節の列は `鍵`・`変化`・`題`・`削除の理由`（`題` は画面だけ画面名、項目・遷移は `—`）。Issue は節の形を決めていない。
  - 選択肢: A) 3 つの種類を同じ形の節にする（推奨）／ B) 種類ごとに列を変える（項目名・遷移元・遷移先も出す）
  - 推奨 A。理由: 受入基準は「その変更が出る」で、中身の列は `docs/v<n>/` を開けば分かる（`diff-versions.py` の「守らないもの」と同じ）。B は項目・遷移の中身（Q&A の番号の列を含む）を決裁者向けの資料に出す入口を増やす。
  - 確認の Issue は立てない（親が立てる）。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）。公開ページ（`docs/`）は触らない。

## 版の上げ方

spec-loop を **minor** で上げる（0.99.0 → 0.100.0。0.x なので壊れる変更も minor。生成物の出力に節が足る）——`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行。
他の周（#1144・#1148・#1149・#1153）が同じプラグインの版を上げうる。マージの直前に main が進んでいたら、**main の先端の spec-loop の版から minor で 1 つ上げた値**にする（親が子に依頼する。cruise の `references/parallel.md` の「版とマージの順」）。

## 受入基準（不変条件 × 経路）

### verify の受入基準

| 番号 | 不変条件 | 内容 |
| --- | --- | --- |
| U1 | 画面の表の変更が比較に出る | 画面の表の行を足す・変える・消した v2 の正本で、`build-proposal.py` の「前の版からの変更」の節にその変更が出る（陽性対照: 修正の前の版では出ない） |
| U2 | 表の無い正本の出力は変わらない | 画面の表を持たない正本では、出力が今と同じバイトのまま |

### それを破りうる経路

| 番号 | 不変条件 | 破りうる入口 | 守り方 |
| --- | --- | --- | --- |
| P1 | U1 | 提案書（`compose`）の比較の節 | `changes_section` 1 関数で共有。件数の表・節・「変更なし」の判定すべてが画面の種類を見る |
| P2 | U1 | 仕様書（`compose_spec`）の比較の節 | 同じ `changes_section` |
| P3 | U1 | 連鎖で消えた項目・遷移の理由 | `diff-versions.py` の `reason` をそのまま描く |
| P4 | U1 | 画面の表だけが変わった版で「変更はありません」 | 判定が画面の種類を含む `shown` で見る |
| P5 | U2 | `diff.changes` が画面の種類を持つか | `row_kinds` を `diff.changes` にある種類だけにする |
| P6 | U2 | CLI（`diff-versions.py`）の出力 | 触らない |

この環境では証明できないもの: なし（正本の実物は無く、一時の git リポジトリの試料で当てる）。BLOCKED: なし。

## 関門の進捗（再開点）

周の在り処:

- ブランチ: `issue/1152-build-proposal-screens-diff`（参照 `origin/main`）
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1152`
- 起点: `05aa0d5`
- base: `05aa0d5c36b012abe57239ba0f288a47f74083fc`

- 版の上げ方: spec-loop を minor（0.99.0 → 0.100.0）。上の「版の上げ方」のとおり
- 実装コミット: `7d5b599`（起点 `05aa0d5` から 1 コミット）
- 実験: なし（交絡を潰す手順は無い。陽性対照は修正の前の `build-proposal.py` で新しい 2 試料が落ち、表の無い試料の出力がバイト一致することで取った）

割り目: 割らない（cruise の周）。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 項目・遷移の中身（項目名・遷移元・遷移先）を節に出さない | 採らなかった | 受入基準は「変更が出る」で、中身は `docs/v<n>/` を開けば分かる（`diff-versions.py` の「守らないもの」と同じ）。Q&A の番号の列も出さずに済む |
| 画面を消して連鎖で消えた項目・遷移の理由は `diff-versions.py` の文言（`画面 <ID> を消した: <理由>`）のまま | 採った | `diff-versions.py` が決めた形。ここで言い換えない |
| `diff-versions.py` の `render`（CLI）は #1091 で既に画面の種類を出す | 触らない | 出ないのは提案書の描き側だけ |
| 画面の表を持たない正本は件数の表に画面の行を足さない | 採った | U2（バイト一致） |

## 関門の記録

```dev-loop-gates
周の base: 05aa0d5c36b012abe57239ba0f288a47f74083fc
```

## 手順 8 の記録

- この周の起票: 0 件（関門の指摘で直すに入った行の起票は親が振り分ける。この周では起票しない）
