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
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 同上
- `plugins/spec-loop/README.md` — 版 0.3.0 と description
- `plugins/spec-loop/.claude-plugin/plugin.json` — 同上
- `.claude-plugin/marketplace.json` — 同上
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
   **実装では 5 条件になった**（下の 4 つに「5: 最後のレビューの指摘が 1 件残らず振り分け済み」を足し、
   条件 1 は「`反映済み` でない行が 0 件」に広げた）。**条件の正は `spec-exit.md`**——以下は着手時の記録
   （`/code-review` 1 パス目 R10 の指摘で追記）。
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
- 実装: 済み（`1f11190`）。~~`check-all.py` 35/35 緑~~ **この申告は誤りだった**——1 パス目の後に回したら
  `check-description-sync.py`（req-loop の frontmatter を変えていない共変）と `check-plan-scope.py`
  （変更範囲の 1 行に複数パスを書き、先頭しか読まれない）が**どちらも `1f11190` の時点から落ちる形**だった。
  前者は trailer、後者は変更範囲の書式を直して解消
- 手順 4 の割り目: AskUserQuestion で訊き、**「ここで割る」**が選ばれた（2026-10-15）
- **次にすること**: 手順 5 の Verifier（別ティア、`dev-loop:dev-loop-verifier`）と手順 6 の `/code-review` の **1 パス目**。
  base は上の `e86f1180ec5e4a397318c13a133ff03242f63bcf`
- 関門 1 パス目（2026-10-15）:
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **済み。反証 2 件**（下の採否の表 V1・V2。どちらも親が再現した）
  - `/code-review`（high。受入基準は起動後に SendMessage で渡し、報告が D・決着済みの論点に言及しているので届いた）:
    **済み。指摘 10 件**（R1〜R10。R4 は V1 と同じ）
  - 直したもの: V1・V2・R1（R4 は V1 で同時に解消）。指摘対応のコミット: `b12730c`。`check-all.py` 35/35（失敗 0）
  - **残っている関門**: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の**両方**。
    base は周の base `e86f1180ec5e4a397318c13a133ff03242f63bcf` のまま
  - **狭いパスの起点**（2 パス目の指摘対応を始める直前の HEAD）: `b12730c`（2 パス目の指摘対応に入る前に再確認する）
  - 手順 6 の 2 つ目の割り目: AskUserQuestion で訊き、**「ここで割る」**が選ばれた（2026-10-15）。
    **次にすること**: Verifier 2 パス目と `/code-review` 2 パス目（受入基準・既知の限界・採否の表を渡す）
- 反証・差し戻し: なし
- 交絡: 実験なし（試料に当てた確認だけ。陽性対照はテストの「満たす」試料と変異 15 件）
- 実装中に足した複製: 判定役 3 体の「守ること」（同じ趣旨を 3 体に持つ。agent 定義は単体で読まれるので分けない）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 抜ける条件をどこに置くか | `references/spec-exit.md` | 段 4 の scaffold も「確定した仕様」の定義として読む。スキル本文に置くと写しになる |
| req-loop 本文の「未定」「TBD」 | 段 2 では触らない（残課題） | バナー以外を触ると req-loop の振る舞いの変更になる |
| 形式検査の縮退 | 決定表・計算ルールは標準ライブラリで総当たり、他は「検査できなかった」 | 記事の「判定は検査器の出力で決める」を、道具が無い環境でも守るため |

### 関門の指摘の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | `model :`（コロン前に空白）・`"model":`（引用符つきキー）が `agent_frontmatter` のキーの正規表現に当たらず、`model` の拒否をすり抜ける | 示せる——`agent_frontmatter("---\nname: a\ntools: Read\nmodel : opus\n---\n")` が `{'name': 'a', 'tools': 'Read'}` を返す（親が再現） | B(a) | 直す |
| V2 | 同じキーが 2 回あると後勝ちになり、`tools: Write` の後の `tools: Read` で検査を通る | 示せる——同上の関数が `{'name': 'a', 'tools': 'Read'}` を返す（親が再現） | A(a) | 直す |
| R1 | 仕様のファイルが 1 つも UTF-8 で読めない（UTF-16・`.xlsx` だけ）と、0 ファイルしか見ていないのに「条件 1 を満たす」で 0 終了 | 示せる——UTF-16 の `order.md`（「割引は TBD」）で exit 0・「仕様 0 ファイルに未決定の印 0 件」（親が再現） | D(b) | 直す（読めた仕様が 0 なら 2。試料と変異を 1 件ずつ足した） |
| R2 | 2 パス目（最後）の判定のあとに Planner が直した仕様は誰も見ないのに、手順 6 は最後の判定の条件 2〜4 をそのまま使う | 示せない（SKILL.md の読解。実行はしていない） | D(c) に触れうる | 残課題（**人間に判断を仰ぐ**——受入基準 D に近い振る舞いの規定） |
| R3 | req-loop と spec-review の両方が「回答済み・未反映」の行を反映し、起票元で絞らない——spec-review の行を req-loop が `requirements/` に反映して `反映済み` にしうる | 示せない（読解） | 無し（req-loop の本文は触らない決着） | 残課題 |
| R4 | = V1 | — | — | V1 で解消 |
| R5 | formal-checker の形式モデルを保存する手順が SKILL.md に無く、`spec/formal/` を書く者がいない | 示せない（読解） | 無し | 残課題 |
| R6 | 決定表の縮退（総当たり）も代表値の選び方に依存し、フローで縮退を拒む理由と矛盾する——**決着済みの論点の理由への反論** | 示せない（読解。反例は仮想） | 無し（条件 4 の強さの論点） | 残課題（決着の理由への反論として人間に渡す） |
| R7 | Q&A 表が列検査を通らないと `read_pending` が行を返さず、`確認中` の行が出力に出ない | 示せる（終了コードは 1 のまま） | 無し（満たしたとは報告しない） | 残課題 |
| R8 | `find_markers` の `splitlines()` が U+2028 等でも割り、行番号がずれる | 示せる（`a b\nc TBD` で :3） | 無し | 残課題 |
| R9 | 0 桁目の YAML リスト・`[Read, Bash]` を誤読し、正しい読み取り専用の定義を誤った理由で落とす | 示せる | 無し（安全側に落ちる。V1・V2 の修正後、0 桁目のリストは「読めない」で落ちる） | 残課題 |
| R10 | 計画の「決めたこと」が 4 条件・`確認中` のまま、`spec-exit.md` は 5 条件・`反映済み` でない行 | — | 無し（計画ファイルは関門の対象外） | 記録として追記（関門の採否ではない） |

**自分で気づいたもの（関門の指摘ではない）**: `spec-exit.md` の「条件 1 を確かめる」節が
「条件 2〜4 はこのスクリプトでは判定しない」と書き、スクリプトの出力は「条件 2〜5」——残課題。
