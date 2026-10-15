# Issue #217: spec-loop 段 2 — spec-review スキルと判定役のエージェント

親: #214（段 2）。前提: 段 1（#216 / PR #228、マージ済み）。

## 変更範囲

触る:

- `plugins/spec-loop/skills/spec-review/SKILL.md` — 新規。Planner＝スキル本体
- `plugins/spec-loop/agents/` — 新規。red-team / domain-checker / formal-checker（許可リスト・書き込みツールなし・`model` を書かない）
- `plugins/spec-loop/references/spec-exit.md` — 新規。**ループを抜ける条件の原本**（段 4 の scaffold も「確定した仕様」としてここを読む）と未決定の印
- `plugins/spec-loop/references/tree.md` — 開発者向けの仕様の置き場所（`docs/spec/`）を足す（段 1 の見直し）
- `plugins/spec-loop/scripts/check-spec-exit.py` — 新規。抜ける条件のうち機械で決まる部分（Q&A 表の `確認中` 0 件・仕様の未決定の印 0 件）
- `scripts/test-check-spec-exit.py` — 上の回帰テスト（変異テスト・references との一致）
- `scripts/check-plugin-versions.py` — `plugins/*/agents/*.md` が許可リストで、書き込みツールと `model` を持たないことを検査
- `scripts/test-check-plugin-versions.py` — 上の回帰テスト
- `scripts/check-all.py` / `.github/workflows/plugins.yml` — 新しいテストの登録
- `plugins/spec-loop/README.md` / `plugins/spec-loop/.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` — 版 0.3.0 と description
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 版のバナーだけ（同じプラグインの全 `SKILL.md` に同じ版）
- `docs/plugins/index.md` — spec-loop の節と一覧表
- `CLAUDE.md` — プロジェクト構成
- `docs/plans/issue-217.md` — この計画

触らない:

- `plugins/spec-loop/references/qa-csv.md` — 起票元 `仕様レビュー` は段 0 で既にある。列は変えない
- `plugins/spec-loop/skills/req-loop/` の本文（バナー以外）——本文に「未定」「TBD」の写しがあるが、段 2 では触らない（残課題）
- `plugins/dev-loop/`——dev-loop-verifier は新しい agents 検査の対象に入るだけで、中身は変えない
- 振る舞いの Eval（`evals/`）——#214 の「決めていないこと」。この段では置かない

## 決めたこと（Issue の「決めること」）

1. **ループを抜ける条件**: 記事（要求仕様書作成ループ）の 4 条件を採り、`references/spec-exit.md` に置く。
   1. Q&A 表に `確認中` の行が 0 件、仕様に未決定の印が 0 件 ——**スクリプトが決める**
   2. 仕様チェックリスト（入出力・エラー・境界値・状態遷移）が埋まっている ——判定役の報告
   3. 決定表の各行・各シナリオに、対応するテストケース（入力と期待結果）が仕様の中にある ——判定役の報告
   4. 形式検査の反例が無く、空振りでない（陽性対照あり）。対象が無ければ「対象なし」と明記 ——formal-checker の検査器の出力
   **1 つでも満たさなければ「抜けた」と報告しない。** 「判定できなかった」は満たさない側に倒す。
2. **Formal Checker の対象と道具**: 対象は決定表・計算ルール／並行・リトライのある業務フロー／権限。
   道具は対象リポジトリの `CLAUDE.md` に従い、無ければ縮退: Z3・TLC・Alloy のうち手元にあるもの、
   どれも無ければ**決定表・計算ルールは Python 標準ライブラリで入力の組み合わせを総当たり**、
   フロー・権限は「検査できなかった」と報告（＝条件 4 を満たさない）。
3. **仕様の置き場所**: `docs/spec/`（開発者向け。`requirements/` は利用者向けなので分ける）。

## デプロイ経路

main へのマージで GitHub Pages（`docs/plugins/index.md`）が更新される。プラグインはカタログ経由
（利用者は `plugin update`）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | 判定役の agent 定義が書き込みツールを 1 つも持たない | (a) 3 つの定義の `tools:` に Write/Edit/NotebookEdit/MultiEdit 等 (b) `tools:` を書かない（＝全ツール継承） (c) 除外リスト形式 (d) MCP のワイルドカード (e) 将来足す agent | `check-plugin-versions.py` が全プラグインの `agents/*.md` を許可リストとして検査（読み取り・`Bash` 以外を拒否）。CI で常時 |
| B | 判定役の agent が別ティアで呼ばれる | (a) frontmatter に `model:` を書く (b) SKILL.md の呼び出しで `model` 引数を省く | (a) は検査で拒否。(b) は SKILL.md の手順に必須として書く（**機械では見ない**） |
| C | 利用者の判断が要る指摘が `qa.csv` に起票され、列検査を通る | (a) SKILL.md の振り分け手順 (b) 起票後の検査を飛ばす (c) 起票元の書き方 | SKILL.md が起票 → `check-qa-csv.py` を 0 になるまで通すことを必須に。起票元は `仕様レビュー（<役>）`。実データで起票例を検査に通す |
| D | 抜ける条件を満たさないとき、満たしたと報告しない | (a) `確認中` が残る (b) 仕様に TBD 等が残る (c) 判定役の報告が欠ける・「判定できなかった」 (d) 形式検査が空振り・道具が無い (e) Q&A 表が列検査を通らない | (a)(b)(e) は `check-spec-exit.py` が非ゼロ。(c)(d) は SKILL.md の規定（欠票・判定不能は満たさない側）。スクリプトの非ゼロのまま「抜けた」と書かないことを SKILL.md に必須で |
| E | データの決まりの写しを増やさない | (a) SKILL.md・README・公開ページに列・状態・印を列挙 (b) スクリプトの定数がずれる | SKILL.md 等は references を指すだけ。スクリプトの定数は `check-qa-csv.py` から読み込み、印はテストが `spec-exit.md` と突き合わせる |
| F | 版の 3 箇所一致・description の JSON 一致 | 全 `SKILL.md`（req-loop を含む）・plugin.json・marketplace.json | `check-plugin-versions.py`（既存） |
| G | スキル内の指し先が実在し、プラグインの外へ出ない | `../../references/…` `../../scripts/…` `../../agents/…` | `check-skill-pointers.py`（既存） |

**掛け算**: 受入基準 A〜G × {Verifier, /code-review} × {1 パス目, 2 パス目} = 4 つの受け渡し。

### 検証で証明できるもの

- A・E(b)・F・G: 検査とテストを実行（変異を含む）
- C: 実際に起票した `qa.csv` の試料を `check-qa-csv.py` に通す
- D(a)(b)(e): `check-spec-exit.py` を試料で実行

### 未証明（この環境では証明できない）

- **B(b)・C(a)・D(c)(d)——モデルが SKILL.md に従うか**（振る舞い）。`claude plugin eval` で当てられるが、
  worktree 隔離セッションからは起動できない（CLAUDE.md）。**ケースも書いていない**（Eval は段 2 の範囲外）。
  → 人間レビューへ。
- agents が実際にプラグインから `spec-loop:red-team` などとして解決されるか（インストール後のクライアントで見る）。

### 生成物

- `skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけを測る → **該当なし**（`--check` は check-all で回る）
- 図の書き出し: drawio を触らない → **該当なし**
- **生成物なし**（PPTX は対象リポジトリでの生成物で、このリポジトリには無い）

## 周の大きさ

同じことを述べている箇所: description（marketplace / plugin.json / frontmatter）3、スキル一覧（README・
`docs/plugins/index.md`・`CLAUDE.md`）3、版 4（2 JSON ＋ 2 SKILL.md）、未決定の印 2（spec-exit.md ＋ スクリプト。
req-loop 本文の写しは残課題）。**分けない理由**: 段 2 は #214 が 1 周と定めた単位で、版と description は
同時に動かさないと CI が落ちる。

## 未解決・確認待ち

- なし（着手時点）

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/217-spec-review`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-217`、
  起点 `e86f118`、base の参照 `origin/main` → `e86f1180ec5e4a397318c13a133ff03242f63bcf`
- 実装: 済み（未コミット → コミット後に関門へ）
- 関門: 未着手
- 反証・差し戻し: なし
- 交絡: 実験なし（試料に当てた確認だけ。陽性対照はテストの「満たす」試料と変異 15 件）
- 実装中に足した複製: 判定役 3 体の「守ること」（同じ趣旨を 3 体に持つ。agent 定義は単体で読まれるので分けない）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 抜ける条件をどこに置くか | `references/spec-exit.md` | 段 4 の scaffold も「確定した仕様」の定義として読む。スキル本文に置くと写しになる |
| req-loop 本文の「未定」「TBD」 | 段 2 では触らない（残課題） | バナー以外を触ると req-loop の振る舞いの変更になる |
| 形式検査の縮退 | 決定表・計算ルールは標準ライブラリで総当たり、他は「検査できなかった」 | 記事の「判定は検査器の出力で決める」を、道具が無い環境でも守るため |
