# Issue #335 — 前の版で暫定反映を指した中間表現は、後の版で確定しても scaffold が止まる

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — 比べる相手として読む前の版の中間表現では、Q&A の参照に `暫定反映` も許す（`check_qa_refs` に許す状態を渡す）。docstring
- `plugins/spec-loop/references/spec-ir.md` — `qa` の行に、前の版の比べる相手だけの例外を 1 文
- `scripts/test-scaffold.py` — 試料と変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — version（patch）
- `.claude-plugin/marketplace.json` — version（patch）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-335.md` — この計画

触らない:

- `check-signoff.py`（#325 で既に後の版の置き換えを数えない）
- 前の版の `確認中` などそれ以外の状態の扱い——条件 1 を通らない状態で、前の版の時点でも scaffold を通りえない
- 今の版・`--upto <n-1>` の時点を作るときの扱い（`gate=True`。暫定を止めるのは変えない）

### 同じことを述べている箇所の数

「前の版の中間表現にも決まりを当てる・何を外すか」を述べる箇所: `scaffold.py` の docstring 冒頭（25 行目）・`read_whole` の docstring・`classify` の docstring・`check_ir` の docstring・`spec-ir.md` の `qa` の行と #319 の項 —— **6 箇所**。
**分けない理由**: どれも 1 つの関数の性質で、外し方は `path_rules` と同じ軸（前の版の比べる相手だけ）。`spec-ir.md` を原本とし、docstring はそれを指す 1 文に留める。

## 乗るデプロイ経路

プラグイン配布（main へのマージ → カタログの版）。`docs/plans/` は Pages のビルドに乗るが中身はこの計画だけ。

## 設計の決定（関門に渡す）

- **D1 前の版の比べる相手で許す状態は `REFLECTED`（`反映済み`・`暫定反映`）**。理由: 抜ける条件 1 を通る状態の集合と同じ。`確認中` などは前の版の時点でも条件 1 を通らないので、許しても許さなくても前の版を scaffold できた事実は変わらないが、範囲を広げない
- **D2 外すのは `gate=False` の経路だけ**（`path_rules` と同じ軸）。今の版と `--upto <n-1>` は `反映済み` のまま

## verify の受入基準

### 不変条件

1. **#335 の再現が通る**——v1 で `暫定反映` の Q-001 を中間表現が指し、v2 で Q-001 を `反映済み` に置き換えると、`scaffold.py` は 0 で作る（直す前は 1 で「前の版（v1）の中間表現が決まりに反する」）
2. **今の版で暫定を指せば止まる**——重ねた表に `暫定反映` が残れば 1（#325 の挙動を変えない。既存の試料 2 本）
3. **前の版の時点を作るときは止まる**——上の 1 の入力で `--check --upto 1`・`--dry-run --upto 1` は 1（v1 の時点では暫定が残る）
4. **前の版でも `反映済み`・`暫定反映` 以外の状態を指せば止まる**——比べる相手の例外は `暫定反映` だけを足す
5. **前の版の Q&A の実在・形は引き続き見る**——比べる相手でも Q&A 表に無い No は止まる
6. **生成物の鮮度**——下記

### 経路（不変条件を破りうる入口）

`scaffold.py` の入口: 書く生成・`--check`・`--dry-run`・`--red-check`（`--in-progress` 付きも）・`--upto`。前の版を比べる相手として読むのは `classify`（`--upto` 無しの v2 以降のすべて、`--red-check` も同じ `classify` を通る）。今の版は `load` → `read_whole(gate=True)`。

| 不変条件 | 経路 | 守り方 |
| --- | --- | --- |
| 1 | 書く生成・`--dry-run`・`--check`・`--red-check` | `classify` → `read_whole(gate=False)` → `check_ir` が `REFLECTED` を許す |
| 2 | すべて（今の版） | `read_whole(gate=True)` の `held` と `check_qa_refs`（`反映済み` だけ）——変えない |
| 3 | `--upto 1` | `load(upto=1)` → `gate=True` |
| 4・5 | `classify` | `check_qa_refs` の他の分岐は変えない |

### 証明できるもの・できないもの

すべて `scripts/test-scaffold.py` の試料（一時ディレクトリの正本リポジトリ）で証明できる。**未証明: なし**。

### 生成物

該当なし——`scaffold.py` の変更は CLAUDE.md の生成手順（図の書き出し・`skill-metrics.py`）の入力に当たらない。`SKILL.md` は版の行だけを変えるので `skill-metrics.py --check` で鮮度を確かめる（`check-all.py` が回す）。

### 必須要件の掛け算

受入基準 × {Verifier, `/code-review`} × {1 パス目, 2 パス目} = 4 つの受け渡し。

## 未解決の判断

なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/335-prev-version-provisional`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-335`・起点 `24390e5`・base `origin/main` = `24390e5875af318b6272511a060fb2bb4318f5cf`
- 実装: `db1a44a` で完了。`scripts/test-scaffold.py` は修正前に新しい試料 1 本だけ赤（Issue の文言どおりの出力）、修正後に 試料 165 件・変異 113 件で緑
- 関門: 未着手（次は手順 5 の Verifier 1 パス目）
- 反証: —
- 交絡: 再現の試料を修正前に赤（陽性対照）にしてから直した。`今の版にも暫定反映を許す` の変異は `held` の検査が先に止めるので等価——変異として載せていない
- `check-all.py`: 44/44 本 緑（失敗 0 / 飛ばし 0。`db1a44a` の内容で）
- 割り目（手順 4）: AskUserQuestion で訊いた → **「ここで割る」**。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 335`、手順 5（Verifier 1 パス目）から

## 既知の限界・決着済みの論点

（関門の指摘と採否はここに畳む）
