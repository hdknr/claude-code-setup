# Issue #390 — dev-loop: 複数 Issue の依存グラフと状態の台帳をファイルに持ち、再開をそこから行う

#389（オートクルーズ）の要件候補 1 を分けたもの。形は利用者が決めた（2026-10-25・AskUserQuestion）:

- **JSON ＋ スクリプト**（`ledger.py` が読み書きし、`next` で着手できる Issue を返す）
- **置き場所はメインの作業ツリーの `.claude/plans/`**（gitignore 済み。セッションをまたいで残る）

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — 新規。台帳の作成・追加・更新・表示・着手できる Issue の判定
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 新規。いつ台帳を使い、いつ書き換え、どう再開するか
- `scripts/test-ledger.py` — 新規。テンポラリの本物の git リポジトリ（worktree つき）で当てる回帰テスト（変異テストを含む）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 「並列化の指針」に `references/ledger.md` を指す項を足す。版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.46.0 → 1.47.0。道具の追加なので minor）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。手で書かない）
- `scripts/check-all.py` — `TESTS` に `test-ledger.py` を足す
- `.github/workflows/plugins.yml` — テストのステップを足す
- `CLAUDE.md` — プラグインと `scripts/` の一覧に足す
- `docs/plans/issue-390.md` — この計画

触らない:

- マージの自動化（#389）・実装役の委譲文（#391）・stacked な周の載せ替え（#392）・利用者不在の判断の線（#393）
- `find-cycle.py`（1 Issue の周の探索。台帳は複数 Issue の上の層で、周の在り処は各周の計画ファイルに残す）
- 再開のタイマー（`CronCreate`）を組む手順——道具の設定は環境ごとに違う（#394）。台帳は「読めば再開できる」までを担う
- 複数セッションからの同時書き込みの排他（下の「既知の限界」）

### 同じことを述べている箇所の数

- 「台帳の決まり（状態・依存・終了コード・守る／守らない）」: `ledger.py` の docstring・`references/ledger.md`・`SKILL.md` の 1 項 —— 3 箇所。
  **状態の一覧・終了コード・守る／守らないは docstring を正とし、`references/ledger.md` は使い方（いつ書くか・どう再開するか）だけを持ち、
  状態の一覧は持たない。`SKILL.md` は指すだけ。**
- 分けない理由: スクリプトと、その使い方と、入口の 1 行なので分けようがない。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/` は main への push で Pages に載る。

## 周の在り処

- ブランチ: `issue/390-cruise-ledger`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-390`
- 起点: `0330977`（Merge pull request #401）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `0330977fc31ed62314e1dbb8c16f876b946d8e46`

## 設計

`ledger.py <コマンド> <台帳の名前> …`（cwd のリポジトリ。標準ライブラリのみ）。台帳は
`<メインの作業ツリー>/.claude/plans/cruise-<名前>.json`。**メインの作業ツリーは `git rev-parse --git-common-dir` から解決する**
——worktree の中から走らせても同じファイルを指す（worktree の `.claude/plans/` は別物で、周を畳むと消える）。

- `init <名前>` — 空の台帳を作る。在れば拒む（上書きしない）
- `add <名前> <番号> [--deps 1,2] [--title …]` — Issue を足す。依存先は台帳に在ること・自己依存と循環は拒む
- `set <名前> <番号> 鍵=値 …` — 状態・PR・ブランチ・worktree・実装役・関門の起点・メモ・依存を書き換える。鍵と状態は決まった一覧だけ
- `show <名前>` — 表と、進行中・着手できる・待っているの 3 区分を出す（再開はここから読む）
- `next <名前>` — 着手できる Issue（状態が未着手で、依存がすべてマージ済み）を 1 行 1 件で出す
- `path <名前>` — 台帳の絶対パスを出す

書き込みは**全体を検査してから**一時ファイル → `os.replace`。拒んだ操作では台帳を 1 バイトも変えない。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| L1 | 台帳の場所は、メインの作業ツリーからでも worktree の中・そのサブディレクトリからでも同じ絶対パスになる | 場所の解決 | 試料: 本物の `git worktree add` の中から `path` |
| L2 | `init` は在る台帳を上書きしない | `init` | 試料: 2 度目の `init` が拒まれ、中身が変わらない |
| L3 | 決まった一覧に無い状態・鍵は拒み、台帳を変えない | `set` | 試料 |
| L4 | 台帳に無い依存先・自己依存・循環は拒み、台帳を変えない（`add` と `set deps=` の両方） | `add`・`set` | 試料: 2 経路とも |
| L5 | 台帳に無い Issue への `set`・同じ Issue の 2 度目の `add` は拒む | `set`・`add` | 試料 |
| L6 | `next` は「未着手で、依存がすべてマージ済み」のものだけを出す（依存が PR 中・止まっている・未着手なら出さない） | `next`・`show` | 試料: 依存の状態ごと |
| L7 | 壊れた JSON・形の違う台帳・無い台帳は「判定できなかった」で止まり、「着手できるものなし」と答えず、ファイルを書き換えない | 読み込み（全コマンド） | 試料 |
| L8 | 台帳の名前にパスの区切り・先頭のドットを許さない（`.claude/plans/` の外に書かない） | 名前 | 試料: `../x`・`a/b`・`.x` |
| L9 | git の外では「判定できなかった」で止まる | 場所の解決 | 試料: git でないディレクトリ |
| L10 | 終了コードが種類ごとに分かれ、docstring の一覧と一致する | docstring | テストが突き合わせる |
| L11 | docstring の「守る」の各行に変異が 1 つあり、壊すと赤（テストが数える）。陽性対照: 壊さない本体で全試料が緑 | `MUTATIONS` | 変異テスト |
| L12 | テストは実リポジトリを触らない（対象はテンポラリ） | テスト | `assert_not_real_repo` |
| L13 | `references/ledger.md` と `SKILL.md` は状態の一覧・終了コードを複製せず docstring を指す。指し先が実在する | 文書 | `check-skill-pointers.py`・目視 |
| X1 | 版が 3 箇所で揃う・生成ブロックが新しい・全歯止めが緑 | 版・§8.2 | `check-all.py` |

### この環境では証明できないもの（未証明）

- **利用者不在の長い周で、タイマーが台帳を読んで実際に再開できること**——何時間も無人で回す周はこの周では回さない。
  確かめるのは「`show`／`next` が再開に要る情報を出す」まで。

### 生成物

- 該当あり: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` を触るため）。`skill-metrics.py --check` で鮮度を見る。
- 図の書き出し: 該当なし（drawio を触らない）。

## 未解決の判断・確認待ち

- なし（形と置き場所は利用者が決めた）

## 手順 8（経験の還元）

- この周の起票: 0 件

## 関門の進捗（再開点）

- 実装: 済み（`ledger.py`・`references/ledger.md`・`test-ledger.py`・`SKILL.md` の 1 項・版 1.47.0）。
  自分で確かめた変異 8 件すべてが、意図した観測で殺せることを見た（陽性対照: 壊さない本体で全試料が緑）
- 割り目 1（手順 4 の後）: AskUserQuestion で「ここで割る」が選ばれた（2026-10-25）。実装コミット `e8f530c`
- 次にすること: 手順 5（Verifier の 1 パス目）と手順 6（`/code-review` の 1 パス目）。base は上の「周の在り処」の SHA
- Verifier: 未
- `/code-review`: 未
- 反証と差し戻し: なし
- 交絡: 未

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 複数セッションからの同時書き込み | 採らない（守らない） | `os.replace` で壊れた半端なファイルは残らないが、後勝ちで片方の更新が消えうる。台帳を書くのは親 1 体の想定（#389 の運用）。排他を入れるならロックファイルの後始末という別の問題が生まれる |
| 状態の遷移の順序（未着手 → マージ済みへの飛び越し等）を縛るか | 採らない | 再開・やり直し・取り下げで逆行が正当に起きる。縛ると台帳が実態に追いつけなくなる |
| stacked な周（依存が PR 中で積んで始める）を `next` に出すか | 採らない | #392 の範囲。`next` は依存がマージ済みのものだけ |
