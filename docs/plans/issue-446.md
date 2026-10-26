# Issue #446 — dev-loop: 親 Issue に並べた課題を /dev-loop:cruise で起動する

形は利用者が決めた（2026-10-26・AskUserQuestion）:

- **一覧の置き場所は GitHub の親 Issue**（本文のチェックリスト）
- **起動は dev-loop プラグインの別スキル `cruise`**（`/dev-loop:cruise <親 Issue> [--absent]`）

直す線: **既定**（出所: 手順 3 の回答。2026-10-26・AskUserQuestion）

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/SKILL.md` — 新規。クルーズの入口（親 Issue を読む → 確かめる → 台帳 → 周を回す → 再開）
- `plugins/dev-loop/skills/cruise/scripts/parent-issue.py` — 新規。親 Issue の本文から Issue と依存を取り出し（`show`）、確かめた結果だけを台帳にする（`apply`）
- `scripts/test-parent-issue.py` — 新規。回帰テスト（変異テストを含む。`gh` は使わず `--body-file` で当てる。台帳はテンポラリの git リポジトリ）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 「複数の Issue を回すとき」に `/dev-loop:cruise` を指す 1 文。版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.56.0 → 1.57.0。スキルの追加なので minor）・description に cruise を足す
- `.claude-plugin/marketplace.json` — 同上
- `plugins/dev-loop/README.md` — 提供スキルに `cruise` を足す
- `docs/plugins/dev-loop-cruise.md` — 「3. 親セッションに指示する」をコマンドでの起動に書き換える
- `docs/plugins/index.md` — 一覧の表と dev-loop の節に `/dev-loop:cruise`
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `scripts/check-all.py` — `TESTS` に `test-parent-issue.py`
- `.github/workflows/plugins.yml` — テストのステップ
- `CLAUDE.md` — プラグインと `scripts/` の一覧に足す
- `docs/plans/issue-446.md` — この計画

触らない:

- `ledger.py` とその docstring（台帳の形・状態は変えない。`parent-issue.py` は `ledger.py` を子プロセスで呼ぶ）
- `references/ledger.md`・`absent-lines.md`・`stacked.md`・`fix-line.md` の規範（`cruise` は指すだけ）
- 親 Issue のチェックボックスを自動で更新すること（Issue の「範囲の外」）
- 再開のタイマー（`CronCreate`）を自動で張ること——スキルは「張るならこの引数で」を案内するまで
- `link-skills.sh`（`plugins/<name>/skills/<name>` だけを張る。`cruise` は素のスキルとしては張れない——spec-loop の各スキルと同じ）

### 同じことを述べている箇所の数

- 「親 Issue の書式（チェックリスト・`(depends: …)`・チェック済みの扱い）」: `parent-issue.py` の docstring・`cruise/SKILL.md`・`docs/plugins/dev-loop-cruise.md` —— 3 箇所。
  **書式の決まりと終了コードは docstring を正とし、SKILL.md と公開ページは例を 1 つ置いて docstring を指す。**
- 「起動のしかた（`/dev-loop:cruise <親> [--absent]`）」: `cruise/SKILL.md`・公開ページ・`docs/plugins/index.md`・`README.md`・JSON の description 2 つ・`SKILL.md` の frontmatter —— 7 箇所。
  分けない理由: カタログ・入口の 1 行はどれも「このコマンドがある」を言うだけで、手順を持たない。手順は `cruise/SKILL.md` だけ。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` は main への push で Pages に載る。

## 周の在り処

- ブランチ: `issue/446-cruise-skill`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-446`
- 起点: `fdc4a29`（#444 のマージ）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `fdc4a2917dbcb638ecd03350d0daa712b85e7dfb`

## 設計

`parent-issue.py <コマンド> <親 Issue 番号> [--body-file F]`（cwd のリポジトリ。標準ライブラリのみ）。
本文は `gh issue view <親> --json body -q .body` で取る（`--body-file` を渡せばそれを読む——テスト用）。
台帳の名前は `issue-<親>`（`ledger.py` の名前の決まりに収まる）。

- `show <親>` — 取り出した Issue と依存を、依存先が先に来る順で出し、最後に**指紋**（取り出した結果の SHA-256 の先頭 12 桁）を出す
- `apply <親> --digest <指紋>` — 本文を取り直して同じ指紋になるときだけ、`ledger.py init` → `add` で台帳を作る。
  **確かめた後に本文が書き換えられたら作らない**（`show` と `apply` の間の書き換え）。台帳が既に在れば作らず、
  親 Issue にあって台帳に無い Issue を名指しする（再開は台帳から）

書式（docstring を正とする）:

- チェックリストの行 `- [ ] #12`・`- [ ] #13 (depends: #12, #11)`。番号の後ろの文は題として台帳に入れる
- `[x]` の行は**済んだもの**として台帳に入れず、それへの依存は満たされたと読む
- コードフェンスの中は読まない。チェックリストでない行は読まない
- `#番号` で始まらないチェックリストの行（受入基準など）は台帳に入れず、`show` に読み飛ばした行として出す
  （利用者が決めた。2026-10-26・AskUserQuestion——最初は拒む形で書いたが、本物の親 Issue の候補 5 件がどれも受入基準のチェックボックスを持っていた）
- 拒む（3。台帳を作らない）: `(depends: …)` の中身が `#番号` のカンマ区切りでない・
  `(depends:` が 2 つある・依存の書き方らしい語（`depend`・`依存`）が `(depends: …)` の外にある・同じ番号が 2 行・
  自己依存・一覧に無い依存先・未チェックの間の循環・未チェックが 0 件・指紋の不一致・台帳が既に在る
- 判定できない（4）: `gh` が失敗した・本文が読めない・git の外・`ledger.py` が 4 を返した

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| C1 | 未チェックの各行の番号・依存・題を取り出し、依存先が先に来る順で出す | `show` | 試料 |
| C2 | `[x]` の行は台帳に入らず、それへの依存は満たされたものとして消える | `show`・`apply` | 試料 |
| C3 | 書式の誤り（上の「拒む」の各形）は 3 で止まり、台帳を作らない。`#番号` で始まらない行は拒まず、読み飛ばした行として `show` に出る | `show`・`apply` | 試料: 形ごと |
| C4 | 依存の書き方らしい語が `(depends: …)` の外にあれば拒む（黙って依存を落とさない） | 取り出し | 試料: `depends #12`・`依存: #12`・`(Depends: #12)` |
| C5 | コードフェンスの中のチェックリストは読まない | 取り出し | 試料 |
| C6 | `apply` は指紋が一致するときだけ台帳を作り、一致しなければ 3 で何も書かない | `apply` | 試料: 本文を書き換えて `apply` |
| C7 | `apply` は既に在る台帳を作り直さず、親 Issue にあって台帳に無い Issue を名指しする | `apply` | 試料 |
| C8 | `apply` で作った台帳は `ledger.py next` が依存どおりに答える（台帳の形は `ledger.py` が作る） | `apply` → `ledger.py` | 試料: 本物の `ledger.py` を子プロセスで |
| C9 | `apply` の途中で `ledger.py` が失敗したら、自分が作った台帳を残さない | `apply` | 試料: 失敗する `ledger.py` を差し替える |
| C10 | `gh` の失敗・git の外は 4（「回すものなし」と答えない） | 入力・場所 | 試料: 偽の `gh`・git でないディレクトリ |
| C11 | 終了コードが docstring の一覧と一致し、docstring の「守る」の各行に変異が 1 つあって壊すと赤。陽性対照: 壊さない本体で全試料が緑 | 変異テスト | `test-parent-issue.py` |
| C12 | テストは実リポジトリ・本物の `gh` を触らない | テスト | `assert_not_real_repo`・`--body-file`・偽の `gh` |
| C13 | `cruise/SKILL.md` は台帳・不在の線・積んだ周・各周の規範を写さず、`../dev-loop/` の原本を指す。指し先が実在し、プラグインの外に出ない | 文書 | `check-skill-pointers.py`・目視 |
| C14 | `cruise/SKILL.md` は親 Issue の本文を信頼できない入力として扱い、**`show` の結果を利用者に見せて確かめてから** `apply` する（`--absent` でも起動時に確かめる） | 文書 | 目視（関門） |
| C15 | `--absent` は「不在の周」の宣言として扱い、不在の線は `.claude/dev-loop.md` から読む（`--absent` で線を広げない） | 文書 | 目視（関門） |
| C16 | 公開ページの起動の節がコマンドに置き換わり、書式は docstring を指す | 文書 | 目視・`mkdocs build --strict` |
| X1 | 版が 3 箇所（2 つのスキルの版の行を含む）で揃う・生成ブロックが新しい・全歯止めが緑 | 版・§8.2 | `check-all.py` |

### この環境では証明できないもの（未証明）

- **`/dev-loop:cruise` を実際に起動して、複数の Issue を最後まで回せること**——この周では本物のクルーズを回さない
  （部品だけで通しで回した実績が無いのは #443 のページに書いたとおり）。確かめるのは「入口のスクリプトが台帳を正しく作る」と「スキルの文面」まで。
- **本物の `gh` の出力の形**（`--json body -q .body`）——テストは偽の `gh` と `--body-file` で当てる。1 度だけ手で本物に当てて形を見る

### 生成物

- 該当あり: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`dev-loop/SKILL.md` を触るため）。`skill-metrics.py --check` で鮮度を見る。
- 図の書き出し: 該当なし（drawio を触らない）。

## 未解決の判断・確認待ち

- なし（置き場所とコマンドの形は利用者が決めた。チェック済みの扱い・指紋・台帳の名前は著者の決定で、上の「設計」に書いた）

## 手順 8（経験の還元）

- この周の起票: 0 件

## 関門の進捗（再開点）

- 実装: 済み（`parent-issue.py`・`cruise/SKILL.md`・`test-parent-issue.py`・版 1.57.0・公開ページ・CLAUDE.md）。
  `test-parent-issue.py` 全合格・「守る」11 行に変異 11 件、どれも狙った観測で殺せることを見た（scratchpad の `why-killed.py`。
  例: 「指紋を比べない」は `指紋の不一致` の試料、「読み飛ばした行を出さない」は `show` の出力）。`check-all.py` 50/50 緑。
  PR のときだけ走る 4 本（版・説明文の同期・変更範囲・リンク）も 0（説明文の同期は `Skip-description-sync` の trailer つき）
- 本物の `gh` での確認（読むだけ）: #389（チェックリストなし）は 3「0 件」。**これだけでは本文を取れなかった場合と区別できない**ので、
  陽性対照として #214 に当てた——最初の実装（番号の無い行を拒む）では 99 行目を名指しして 3（本文は取れている）、
  決まりを変えた後は Issue 6 件と読み飛ばした行 6 行を出して 0。同じ形の Issue（#64・#260・#407）も番号の無い行で 3 だった
- 実装中の設計変更: 番号の無いチェックリストの行を「拒む」→「読み飛ばして show に出す」（利用者の判断。上の「設計」）
- 割り目 1（手順 4 の後）: AskUserQuestion で「ここで割る」が選ばれた（2026-10-26）。実装コミット `85ad55e`
- 次にすること: **手順 5 から**——Verifier 1 パス目（`dev-loop:dev-loop-verifier`・別ティア）と `/code-review` 1 パス目。
  渡す base は上の「周の在り処」の `fdc4a29…`。どちらにも受入基準 C1〜C16・X1 と下の「既知の限界」を渡す

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 親 Issue に後から足した Issue | 台帳には自動で足さない。`apply` が名指しし、足すのは `ledger.py add` | 2 回目の起動は台帳から再開する（Issue の要件 4）。自動で足すと、確かめていない本文が台帳に入る |
| 依存先が一覧に無いが閉じている Issue | 拒む（一覧に `[x]` で書けば満たされたと読む） | `gh` で状態を引くと、テストで決まらない入力が増える。書き方で表せる |
| `[x]` を「マージ済み」と読むこと | 読まない。台帳に入れないだけ | `merged` は実物でマージされたことを指す（`ledger.py`）。チェックは人が付ける印 |
