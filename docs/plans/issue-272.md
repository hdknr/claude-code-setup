# Issue #272: check-signoff・scaffold の回帰テストを素通りする変異 4 本に試料を足す

元の周: #262（PR #269 の狭いパスの指摘 N1〜N4）。`/dev-loop 272` で起動（2026-10-20）。

## 変更範囲

触る:

- `scripts/test-check-signoff.py` — 試料 3 件（N1〜N3）・変異 3 件・docstring の「見るもの」
- `scripts/test-scaffold.py` — 試料 1 件（N4）・変異 1 件
- `docs/plans/issue-272.md` — この計画

触らない:

- `plugins/spec-loop/scripts/check-signoff.py`・`scaffold.py` — 本体の挙動は正しい（Issue の前提。下の受入基準 A で確かめる）。
  **本体を触らないので、プラグインの版は上げない**（`check-version-bump.py` は `plugins/` の中身を見る）
- 他の歯止め・CI 定義（どちらのテストも既に `check-all.py` と `plugins.yml` から呼ばれている）

**周の大きさ（同じことを述べている箇所）**: 変異と試料は各テストの表の 1 行ずつで、写しは無い。
docstring の「見るもの」が試料の性質を列挙しているので、**その 1 箇所**（signoff 側）。分ける理由は無い。

## 乗るデプロイ経路

**反映経路なし**——`scripts/` のテストは公開サイトにもプラグインにも載らない（`docs/plans/` は mkdocs の `docs/` 配下だが、
`mkdocs.yml` の nav に無く、既存の計画ファイルと同じ扱い）。マージと CI 完了の確認は行う。

## verify の受入基準

不変条件と、それを破りうる経路:

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| A | 足した試料が**本体のままで**期待どおり（陽性対照） | 試料の組み方の誤り（ステップ・期待の文言） | 素の `test-*.py` が緑 |
| B | 足した変異 4 本が、**名指しした新しい試料で**赤になる | 変異の文字列が本体に 1 回現れない／殺す試料の名前違い | ハーネスが「壊す箇所が 1 回現れる」と「killer が期待どおりでない」を見る |
| C | **新しい試料が要る**こと——変異 4 本は、足す前の試料ではどれも殺せない（Issue の主張） | 既存の試料が既に殺していた（なら試料は冗長） | 変異を当てた本体で**既存の全試料**を走らせ、全部期待どおりのままであることを見る（signoff: `run_all`、scaffold: 全ケース） |
| D | N1 の試料が**本当に rename（R100）**を作っている | git の rename 検出が効かない設定（`diff.renames=false` など）だと `D`+`A` に分かれ、`A vis.md` が両方の形で数えられて変異を判別しない | 期待の文言に `R100\t…/.x\t…/vis.md` を入れ、rename でなければ**試料が赤**になるようにする |
| E | N4 の試料が「版の名前が決まりに反する（1）」と「版が 1 つも無い（2）」を分ける | `v02` だけの構成で別の理由で 1／2 が出る | 期待の終了コード 1 と、`find_versions` の誤りの文言を期待にする。既存の「版に分けていない」（2）と並べる |
| F | 歯止めが全部緑 | 他の歯止め（件数の写し・指し先・plan-scope 等） | `python3 scripts/check-all.py`、push 後に `gh pr checks` |

**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目 = 4 つの受け渡し。

**この環境では証明できないもの**: 無し。

**生成物**: **生成物なし**——触るのはテストと計画ファイルだけで、図の書き出し（`exports.json`）・`skill-metrics.py` の生成ブロック
（`SKILL.md` を触らない）・spec-loop の生成物（本体を触らない）のどれにも当たらない。

## 未解決の判断・確認待ち

無し。

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/272-signoff-scaffold-mutants`／worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-272`／起点 `50b1d1b`／
  base: `origin/main`（`refs/remotes/origin/HEAD`）→ `50b1d1be2ad0efd20726333e712a4b91dcfccc0a`
- 関門: 未着手
- 反証・差し戻し: なし
- 交絡を潰した手順: （実装後に書く）

## 既知の限界・決着済みの論点

- **N1 の試料は git の rename 検出に乗っている**——`diff.renames` を切ったシステム設定では試料が赤になる（黙って緑にはならない。受入基準 D）。
  テストは `GIT_CONFIG_GLOBAL` を差し替えるが、システム設定（`/etc/gitconfig`）は差し替えない——既存の試料と同じ扱い。
