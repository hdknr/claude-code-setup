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
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.46.0 → 1.48.0。道具の追加なので minor。main が #406 で 1.47.0 に先に到達したので取り込んで 1 つ上げた）
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
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `0330977fc31ed62314e1dbb8c16f876b946d8e46`（1 パス目）。
  **main（#406）を取り込んだので式を当て直した** → `8e9751c95cc1866796612412e4c52e783277059e`（2 パス目以降はこちら）

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
- Verifier 1 パス目: 済み（sonnet・`dev-loop:dev-loop-verifier`）。**受入基準の反証 0 件**、基準外の穴 3 件（採否の表の R1・R2・R4 と同じ）
- `/code-review` 1 パス目: 済み（high）。**指摘 10 件**（採否の表 R1〜R10）。直す 6 件（R1・R2・R3・R4・R7・R8 の型）・残課題 4 件（R5・R6・R9・R10）と R8 の依存の重複
- 1 パス目の指摘対応: 済み（`daba4cf`）。`test-ledger.py` は全合格・「守る」11 行に変異 11 件（新しい 3 件も殺せる）。
  R7 は `probe_gitdir.sh` で修正前に victim へコミットが入り、修正後は入らないことを見た（陽性対照つき）
- main（#406）を取り込み、版を 1.48.0 へ（#406 が 1.47.0 に先に到達）
- 反証と差し戻し: 1 パス目の反証（受入基準を破るもの）は R1・R2・R3・R4・R7・R8 の 6 件。手順 4 へ差し戻して直した
- 交絡: R1 の試料は `git worktree list` でも同じ誤りが出ることを見た（`git` 自身が知らない配置）。R7 は修正前後の対照
- 次にすること: **手順 5 の当て直し（Verifier 2 パス目）**と **`/code-review` 2 パス目**の**両方**。base は `8e9751c…`

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 複数セッションからの同時書き込み | 採らない（守らない） | `os.replace` で壊れた半端なファイルは残らないが、後勝ちで片方の更新が消えうる。台帳を書くのは親 1 体の想定（#389 の運用）。排他を入れるならロックファイルの後始末という別の問題が生まれる |
| 状態の遷移の順序（未着手 → マージ済みへの飛び越し等）を縛るか | 採らない | 再開・やり直し・取り下げで逆行が正当に起きる。縛ると台帳が実態に追いつけなくなる |
| stacked な周（依存が PR 中で積んで始める）を `next` に出すか | 採らない | #392 の範囲。`next` は依存がマージ済みのものだけ |

### 1 パス目の指摘と採否（Verifier: 受入基準の反証 0 件・基準外 3 件 ／ `/code-review`: 10 件）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | `--git-common-dir` の親をメインの作業ツリーとみなすので、`--separate-git-dir` のリポジトリとサブモジュールで台帳が作業ツリーの外（`sepgit/` の隣・`.git/modules/`）に書かれる（V-C も同じ） | 示せる: 試料で `path` が `<tmp>/.claude/plans/…`・`<super>/.git/modules/.claude/plans/…` を返した。**`git worktree list --porcelain` の先頭も同じ誤りを返す**（scratchpad の `probe_wt.sh`） | L1・L8 | 直す——メインの作業ツリーにいれば `--show-toplevel`、worktree の中なら共通ディレクトリが `.git` ならその親・そうでなければ `core.worktree`、どれでも決まらなければ 4 |
| R2 | `load` が `validate` を通さないので、手で直して壊れた台帳（循環・無い依存先・同じ番号 2 つ）に `next` が 0 で答える（V-A も同じ） | 示せる: 重複 #1 で `next` が `1` を 2 行・rc 0、循環で空・rc 0 | L7 | 直す——読み込みで整合まで見て、崩れていれば 4 |
| R3 | 既に壊れた台帳への `set`/`add` が 3（拒んだ）で返り、原因を取り違える | 示せる: 重複 #1 の台帳に `set` で rc 3 | L7・L10 | 直す（R2 で読み込みが 4 になるので同時に消える） |
| R4 | 保存の `OSError`（書けない・名前が長すぎる・`.claude/plans` がファイル）が素の例外で rc 1 になり、終了コードの表に無い（V-B も同じ） | 示せる: `chmod 555` で `add` が rc 1、`.claude/plans` がファイルで `init` が rc 1 | L10 | 直す——保存の `OSError` は 4 |
| R5 | `references/ledger.md` の再開の規則 5 が、`blocked` を「進行中」に数える `show` と噛み合わない | 示せる（試料の出力） | 無し | 残課題 |
| R6 | 取り下げた依存先を持つ Issue が「依存待ち」に永遠に残り、ふつうの待ちと区別できない | 示せる（試料の出力） | 無し（L6 は「出さない」を求めるだけ） | 残課題 |
| R7 | テストが `GIT_*` を外さず `HOME`・`GIT_CONFIG_GLOBAL` も差し替えないので、`GIT_DIR` が他のリポジトリを指す環境では、そのリポジトリにコミット・`user.email`・台帳を書く | 示せる: `GIT_DIR=<victim>/.git` で回すと victim のコミットが 1 → 2、`user.email=t@example.invalid`、`.claude/plans/cruise-c.json` ができた（scratchpad の `probe_gitdir.sh`） | L12 | 直す——`test-check-signoff.py` と同じく `GIT_*` を外し、`HOME`・`GIT_CONFIG_GLOBAL`・`GIT_CONFIG_NOSYSTEM` を差し替える |
| R8 | 形の検査が真偽値の番号・依存（`isinstance(True, int)`）・文字列でない文字の欄を通す。`--deps 1,1` の重複も通る | 示せる: `{"number": true}` で `next` が `True`・rc 0 | L7（真偽値・型）。依存の重複は無し | 真偽値・型は直す（形の誤りで 4）。**依存の重複は残課題**（破る受入基準が無い） |
| R9 | `show` が `|`・改行をエスケープせず表が崩れる | 示せる（試料の出力） | 無し | 残課題 |
| R10 | 対象リポジトリが `.claude/plans/` を gitignore しているとは限らない・保存でファイルのモードが 0600 になる | 示せる（grep・試料） | 無し | 残課題 |
