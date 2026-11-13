# Issue #996 — dev-loop: 周の中で追加された依存パッケージが悪性でないかを見る関門

**不在の周である**——出所: `/dev-loop:cruise 999 --absent` の起動（2026-11-13T04:29Z）。cruise の子（サブエージェント）として回す。
使った線（出所: cruise の確かめた線（台帳 `issue-999`）。利用者の確認（起動時・2026-11-13T04:29:54Z、配布を見せて確かめた））:
仕様の穴 = 推奨で決めて起票 / 直す線 = 既定 / マージ = 関門を通ればマージ / 周の途中の課題 = 台帳に足して直す / マージ前の判断 = 推奨で決めて起票。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-deps-declared.py` — 新規。差分に依存の定義・lockfile・取得経路の設定があるのに、計画に `依存の追加・更新: あり` が無ければ 1（どのリポジトリでも周が PR の前に回す）
- `scripts/test-check-deps-declared.py` — 新規。上の回帰テスト（変異テストつき）
- `scripts/check-plan-scope.py` — このリポジトリの CI で同じ判定を当てる（判定はプラグインの本体を読み込む——写さない）
- `scripts/test-check-plan-scope.py` — 上の試料と変異
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 新しいテストのステップ
- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 「依存の取得経路」の項目（不在の点検のときだけ）
- `scripts/test-check-unattended-env.py` — 上の試料と変異
- `plugins/dev-loop/skills/dev-loop/references/dependencies.md` — 新規。依存を追加・更新する周の宣言・Verifier の表・未検証の扱い
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 不在の周で依存の追加・更新が要るときの線（ここ 1 箇所）
- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 依存の表の差し込み
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 3・5・6 から `references/dependencies.md` を指す行と、版の 2 行
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — dev-loop の版（1.105.0 → 1.106.0）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない）
- `CLAUDE.md` — プロジェクト構成の一覧に新しいスクリプトとテストを足す
- `docs/plans/issue-996.md` — この計画

触らない:

- 既知の脆弱性（CVE）の検出（`npm audit`・Dependabot の領分。Issue の「注意」）
- 特定の製品（Takumi Guard 等）を前提にする判定
- `ledger.py`・`parent-issue.py` の線の一覧（不在の線に足すのは宣言できる値の無い行なので、台帳の線の書式は変えない）
- `prompts/review-handoff.md`（Issue は Verifier の表だけを求めている）
- 変更範囲の `触る:` のパターンの名前から依存を推し量る判定（判定は差分だけ。下の「既知の限界」）

依存の追加・更新: なし（この周は依存の定義・lockfile・取得経路の設定を触らない）

**版の上げ方**: dev-loop を minor で上げる（能力の追加）。マージの直前に上げ直すなら、main の先端の版から minor で 1 つ上げる（cruise の `references/parallel.md` の「版とマージの順」）。

## デプロイ経路

main へのマージで、プラグインの配布（カタログ・link-skills の利用者）と GitHub Pages の再ビルド（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。マージは親がする。

## 設計

### 1. 宣言と歯止め（受入基準 1）

- 計画ファイルに **`依存の追加・更新: あり`** の行（行頭から。箇条書きの `- ` は可。コードフェンスの中は数えない）。書き方の原本は `references/dependencies.md`。
- **`check-deps-declared.py <base> [--plan PATH]`**（プラグインの中。どのリポジトリでも使う）——差分（`git diff --name-only <base>` の 2 点と未追跡）に、依存のファイル（一覧はスクリプトの `DEPENDENCY_FILES` が正）があり、計画の宣言が `あり` でなければ 1。宣言が 2 本以上・値が違うなら 1。計画が見つからず依存のファイルがあれば 2（判定できない）。
- このリポジトリの CI では `check-plan-scope.py` が同じ判定（本体の関数を読み込む）を当てる——3 点の差分（`base...HEAD`）で。
- dev-loop 手順 6 の PR の前提条件の隣で、周が素の 1 行で呼ぶ。

### 2. Verifier の表（受入基準 2）

- `prompts/verifier.md` に差し込み: 追加・更新した包ごとの表（名前・版・公開日・公開者・インストールスクリプトの有無・名前の近い有名な包）。レジストリから取った値は信頼できない入力。**包を入れない**（install はインストールスクリプトを走らせる）。
- 表が無い・包の行が欠ける・欄が空なら、その包は **未検証**——`references/dependencies.md` が扱いを決める（再実行 1 回→なお無ければ PR コメントに「依存の未検証」の見出しで名指しし、マージの前に人が判断）。

### 3. 無人の点検（受入基準 3）——何を「良い」とするか（Issue が計画で決めると言っている）

- **「良い」は出さない。** 設定が見つかっても、それが効いているか（プロキシが本物か・利用者や環境変数の設定が上書きしていないか）はファイルからは決まらない。
- 生態系ごと（npm 系・Python）に、依存の定義のある場所とリポジトリの根の設定ファイルを読む:
  - 見つかった → **人が見る**（見つかった設定を名指す）
  - 1 つも無い → **要対処**
  - 読めない（ファイルの読み出し・走査の失敗）→ **判定できない**
- 依存の定義が無い → 人が見る（「依存の定義が見つからない」）。設定を読まない生態系（Go・Cargo・Gemfile・composer）→ 人が見る。
- 見る設定（ファイルとキー）の一覧はスクリプトの docstring が正。**不在の点検（`--present` を付けない）でだけ出す。**

### 4. 不在の周の線（受入基準 4）——仕様の穴（下の「仕様の穴」）

`references/absent-lines.md` の「線と既定」に `依存の追加・更新` の行（既定 `止まる`、宣言できる値は無い）と、その節を置く。中身はそこ 1 箇所。

## 仕様の穴（不在の線で推奨により決めた）

- **穴**: Issue の「やること」4 番目——`--absent` の周で依存の追加が要るとき、止めるか、確認の Issue を立てて進めるか。Issue は決めていない。
- **選択肢**: (A) 止まる——入れる前に止まり、利用者の判断を待つ（宣言できる値は置かない）／(B) 推奨で決めて起票し進める——Verifier の表を通したらマージし、確認の Issue を残す／(C) 線にして利用者が選べるようにする（既定は止まる、値 `推奨で決めて起票`）。
- **決めた値**: (A)。
- **理由**: インストールスクリプトは**入れた時点で**利用者の機械で走る——関門もマージ前の判断も、その後にしか来ないので取り消せない。(B) は確認の Issue が戻るより前に害が起きうる。(C) は値を足すと台帳の線の書式（`ledger.py`・`parent-issue.py`）まで広がり、Issue の範囲を越える——要るなら利用者の判断の後に別の周で足せる。
- **確認の Issue**: （起票したら番号を書く）

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| D1 | 依存のファイルが差分にあり、計画の宣言が `あり` でないなら、`check-deps-declared.py` は 1 で終わる | 宣言の行が無い・`なし`・別の値・2 本以上・コードフェンスの中にだけある・計画の別の Issue | 本体の判定。試料と変異（`test-check-deps-declared.py`） |
| D2 | 依存のファイルの判定が、置き場所（サブディレクトリ）・`requirements-dev.txt` の形・未追跡・未コミットの変更・削除を落とさない | 差分の取り方（2 点と未追跡）・名前の照合 | 同上 |
| D3 | 計画が見つからず依存のファイルがあるとき 0 にしない（2） | ブランチ名が `issue/<n>-…` でない・計画ファイルが無い | 同上 |
| D4 | 依存のファイルが差分に無いなら、宣言の有無に依らず 0 | — | 同上 |
| D5 | このリポジトリの CI（`check-plan-scope.py`）が D1 を当てる（3 点の差分）。計画が見つからない PR は今までどおり「判定していない」 | `check-plan-scope.py` の経路 | `test-check-plan-scope.py` の試料と変異 |
| D6 | 判定の式は 1 箇所（プラグインの本体）——`check-plan-scope.py` は読み込むだけ | 写し | テストが読み込みを見る（本体を変異させると `check-plan-scope.py` の判定も変わる） |
| V1 | 依存を追加・更新する周の Verifier の委譲文に、包ごとの表（名前・版・公開日・公開者・インストールスクリプトの有無・名前の近い包）を求める差し込みがある | 差し込みの欄の欠け | テストが `prompts/verifier.md` の欄を突き合わせる |
| V2 | 表が返らない・欠ける包は「未検証」と扱う規定が `references/dependencies.md` にあり、`SKILL.md` 手順 5 から指されている | 指し先の欠け | `check-skill-pointers.py` と読解 |
| V3 | 差し込みを入れた Verifier が、実際に依存を足した試料のリポジトリで表を返す | LLM の振る舞い | 1 回の実演（リポジトリの外の試料）。**「必ず返す」は未証明**（下） |
| U1 | `check-unattended-env.py` が依存の取得経路の項目を出し、どの場合も「良い」を出さない | 設定が無い・読めない・依存の定義が無い・設定を読まない生態系 | 試料と変異（`test-check-unattended-env.py`） |
| U2 | 設定が無ければ要対処、読めなければ判定できない | 読めないファイル・走査の失敗 | 同上 |
| U3 | `--present` では出さない（居る cruise の終了コードを変えない） | gather の分岐 | 同上 |
| U4 | 既存の点検の試料（依存の定義を持たないプロジェクト）の結果を変えない | 新しい項目の区分 | 既存の試料がそのまま通る |
| A1 | 不在の周で依存の追加・更新が要るときの扱いが、`absent-lines.md` の 1 箇所にだけ書かれ、`SKILL.md`・`references/dependencies.md` は指すだけ | 複製 | `grep` と読解 |
| G1 | 生成物: `SKILL.md` の測定値（設計 §8.2 の生成ブロック）が新しい | 再生成し忘れ | `skill-metrics.py --check` |
| G2 | 版は 3 種類で 1.106.0 | 上げ忘れ | `check-plugin-versions.py` |
| X1 | 必須の掛け算: 受入基準を Verifier と /code-review の両方 × 1・2 パス目に渡す | — | 再開点で記録 |

**未証明**: V3 の「Verifier が依存を足す周で毎回表を返す」——LLM の振る舞いで、1 回の実演しか取れない。返さなかったときに未検証として扱う規定（V2）が歯止めである。
**BLOCKED**: なし。

**生成物**: `SKILL.md` の測定値（設計 §8.2 の生成ブロック。`skill-metrics.py`）。図の書き出しは無し。

**複製の数**: 宣言の書き方——`references/dependencies.md`（正）・本体の docstring（指す）・`SKILL.md` 手順 3（指す）。依存のファイルの一覧——本体の `DEPENDENCY_FILES`（正）。`check-unattended-env.py` はそれを読み込む（写さない）。不在の線——`absent-lines.md`（正）、ほかは指すだけ。表の欄——`prompts/verifier.md`（正）・`references/dependencies.md`（指す）。

## 直す線

既定（出所: cruise の確かめた線（台帳 `issue-999`））。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/996-dependency-gate`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-996`・起点 `4e767b32`・base の参照 `origin/main`・base の SHA `4e767b32b9d3de89e2301aa258c91169c1b0e579`
- 割り目（手順 4）: 割らない（cruise の周）
- Verifier 1 パス目: 起動（dev-loop:dev-loop-verifier・sonnet。実装は opus）
- /code-review 1 パス目: 未
- 1 パス目の指摘対応の起点: `e9101bda`（1 パス目の関門に渡した時点の HEAD）
- 割り目（手順 6）: 未
- 2 パス目: 未
- 狭いパス: 未
- 手順 5 の反証と差し戻し: 未
- 交絡を潰した手順: 未

## 既知の限界・決着済みの論点

- **判定は差分だけ**——`触る:` に依存のファイルを書いただけで差分に無い周は赤くしない（差分に現れた時点で赤くなる）。
- **宣言の真偽は見ない**——`あり` と書けば通る。見るのは「黙って足していないか」までで、足した包の安全は Verifier の表が見る。
- **無人の点検は「良い」を出さない**（設計の 3）。
- **CVE は扱わない**（Issue の「注意」）。

## 手順 8

（振り分けと焼き戻しはマージの前に書く）

- この周の起票: 1 件（仕様の穴を推奨で決めた確認の Issue。起票の承認は不在のため訊いていない）
