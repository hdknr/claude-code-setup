# Issue #226 — orca・cmux: 前提チェックとブラウザの手順の python3 -c が、カレントディレクトリの json.py を実行する

## 1. 変更範囲

触る:

- `plugins/orca/skills/orca/SKILL.md` — 前提チェック（2 箇所）とブラウザタブの手順の `python3 -c` に `-I`、版のバナー
- `plugins/cmux/skills/cmux/SKILL.md` — ブラウザの手順の `python3 -c` に `-I`、理由の 1 文、版のバナー
- `plugins/orca/.claude-plugin/plugin.json` — version
- `plugins/cmux/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — orca と cmux の version
- `docs/plans/issue-226.md` — この計画ファイル

触らない:

- `docs/plugins/index.md` の `python3 -c`・`python3 -m json.tool`（利用者が手で打つ確認コマンド。スキルの手順ではない。残課題）
- `dev-loop`・`spec-loop` の `python3 <パス>/scripts/*.py`（スクリプトをパスで起動すると `sys.path[0]` はスクリプトのディレクトリで、cwd ではない）
- description（3 箇所）——能力は変わらない
- #197 の残課題（C3〜C9 など）——この Issue の受入基準の外

**数え方**: `git grep -nE "python" origin/main -- 'plugins/*.md'` から `dev-loop`・`spec-loop` を除いた全件。
`python3 -c` は orca 5 箇所（前提チェック 2・`-n` 2・ブラウザ 1。うち `-n` の 2 箇所は #197 で `-I` 済み）・cmux 1 箇所。
（当初「orca 4 箇所」と書いていた。1 パス目の `/code-review` の指摘で訂正）

**複製の数**: `-I` の理由は orca の `-n` 節に 1 箇所（#197）。cmux には説明が無い。版は 2 プラグイン × 3 箇所。
**分けない理由**: Issue が 2 つを 1 件で求めている。直し方は同じ（`-I` を足す）で互いに独立。

## 2. デプロイ経路

- マーケットプレイス（`plugins/` と `marketplace.json`。利用者が `plugin update` で取る）。
- `docs/` は計画ファイルだけ（GitHub Pages に載るが記録のみ）。破壊的・不可逆な操作は無い。

## 3. 受入基準

**I1. orca・cmux の `SKILL.md` のどの `python3` 呼び出しも、カレントディレクトリのモジュールを import しない。**

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 orca 前提チェック 1（`orca status`、`json`） | cwd の `json.py` が走らない・ランタイム不達なら rc=1 | `-I` |
| P2 orca 前提チェック 2（`orca worktree current`、`json`） | 同上・`ok:false` なら rc=1 | `-I` |
| P3 orca `-n`（`shlex`・`json`） | #197 のまま回帰しない | 既に `-I` |
| P4 orca ブラウザタブ（`json`。失敗は `2>/dev/null \|\| echo ""` で握りつぶされる） | cwd の `json.py` が走らない | `-I` |
| P5 cmux ブラウザ（`json`・`subprocess`。同じく握りつぶし） | cwd の `json.py`・`subprocess.py` が走らない | `-I` |
| P6 上の全ブロック・ふつうの cwd | 結果が変わらない（回帰しない） | `-I` は import 先を狭めるだけ |
| P7 `PYTHONPATH`・`PYTHONSTARTUP` などの環境変数 | 効かない | `-I` は `-E` を含む |

**I2. Issue の再現が直る**: 偽の `orca` にランタイム不達・`ok:false` を返させ、cwd に
`open(marker,'w').write('ran'); raise SystemExit(0)` の `json.py` を置いて前提チェックを流すと、**rc=1・marker が作られない**。

**I3. 版が揃い、patch で上がっている**（cmux 1.1.7 → 1.1.8、orca 1.0.2 → 1.0.3）。`check-all.py` が緑。

### 証明の手段

- I1・I2: `SKILL.md` からブロックを抜き出し（手で写さない）、偽の `orca`／`cmux` を PATH の先頭に置いて、
  悪意の `json.py`／`subprocess.py` を置いた cwd で流す。**陽性対照**: 修正前（`origin/main`）のブロックで同じことをして、marker が作られることを見る。
- P6: ふつうの cwd で、偽 CLI が返すタブ一覧から正しい id が出ることを修正前後で比べる。
- 本物の CLI の読み取り専用コマンド（`orca status --json`・`cmux --json list-panels`）で前提チェックとブラウザ探索の python 部分を 1 回流す（書き込みはしない）。
- **未証明**: Python 3.4 未満（`-I` が無い）。macOS 以外のホスト。Windows の Orca。

### 生成物

**生成物なし**——図の書き出しも §8.2 の測定値も `dev-loop` の `SKILL.md` に依存し、この周は触らない
（`skill-metrics.py --check` は `check-all.py` が回す）。

## 4. 未解決の判断

- なし

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/226-python-isolated`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-226`、
  起点 `9fc3ba4`、**base: `origin/main` → `9fc3ba490c2dc5e0b82aaa77e0c348387831a97b`**
- 実装: 4 箇所に `-I`（orca 前提チェック 2・ブラウザ 1、cmux ブラウザ 1）、各スキルに理由の 1 文、版 cmux 1.1.8・orca 1.0.3。
  `check-all.py` 31/31 緑。
- 実装コミット: `ebee395`
- 関門 1 パス目（2026-10-13、再開した周）:
  - **Verifier**（`dev-loop:dev-loop-verifier`／sonnet。起動した種別とツール Read・Bash を報告で確認）: **反証 0 件**。
    独立に組んだ harness（`SKILL.md` から抽出・偽 CLI・悪意の `json.py`／`subprocess.py`／`shlex.py`）で P1〜P7 すべて一致。
    陽性対照（`9fc3ba4`）で marker が書かれ、HEAD で書かれない。`subprocess.py` 単独の対照も取った。`check-all.py` 31/31。
    **親が harness を再実行して確認**: old orca/0 rc=0 marker=json;json; → new rc=1 marker 無し、old cmux marker=json; → new 無し。
  - **`/code-review`**（high）: **指摘 7 件**→ 直す 0 件、残課題 6 件、計画ファイルの訂正 1 件（§6 の表）。
  - 手順 4 への差し戻し: なし。
- **2 パス目: 該当なし**——1 パス目で成果物に直した行が 0 件なので、当てる指摘対応の差分が無い
  （計画ファイルの件数の訂正だけ。関門は計画ファイルを検査しない）。**狭いパス: 該当なし**（2 パス目が無い）。
- 割り目（手順 6）: 2 パス目が無いので置かない。
- 割り目（手順 4）: 提案済み——**人間の選択は「ここで割る」**（2026-10-13）
- 交絡を潰した手順（著者の実験。関門ではない）:
  - **試料が壊れていた**: 最初の版は `printf` の `%r` で悪意の `json.py` が空ファイルになり、`marker=no` が無意味だった
    （ただし C・E で「新規作成」に落ちたことが、空の `json.py` が import された証拠として残っていた）。
    試料を直し、**試料が単体で marker を書くこと**を harness の冒頭で確かめるようにした。
  - **陽性対照**: 修正前（`origin/main` の写し）のブロックで、悪意の `json.py` を置いた cwd では前提チェックが
    ランタイム不達・`ok:false` でも **rc=0・marker=RAN**、ブラウザ（orca・cmux）も **marker=RAN**、
    cmux は `subprocess.py` でも RAN、`PYTHONPATH` でも RAN。`-n`（#197 で `-I` 済み）は RAN しない。
  - **修正後**: 同じ 14 通りで marker はすべて no。前提チェックは不達・`ok:false` で rc=1。
    ふつうの cwd での結果（rc・呼ばれたコマンド・選ばれたタブ id）は修正前と同じ。
  - 本物の CLI（読み取りのみ）: orca 前提チェック rc=0（runtime reachable）、cmux のブラウザ探索の python 部分 rc=0
    （ブラウザのサーフェスが 0 個なので空——一致する経路は偽 CLI でだけ確かめた）。
  - スクリプト: scratchpad の `i226/harness.sh`（`SKILL.md` からブロックを抜き出す）・`i226/real.sh`。

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `python3` をやめてシェルや `jq` で書く | 採らない | `jq` は前提にできない。`-I` で足りる |
| `docs/plugins/index.md` の `python3 -c` | 範囲外 | スキルの手順ではなく、利用者が手で打つ確認コマンド |

### 1 パス目の指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | 「すべて `-I`」を機械で見る歯止めが無い（将来の編集で落ちうる） | 示せない（いまは全件 `-I`。将来の話） | 無し | 残課題 |
| R2 | 修正の層が違う——インラインの `python3 -c` を `scripts/` に出してパスで起動すべき | 示せない（設計の代替案） | 無し | 残課題 |
| R3 | `-I` は `-E` を含むので `PYTHONUTF8`／`PYTHONIOENCODING` が効かなくなり、非 UTF-8 ロケールで日本語タイトルを含む一覧の `json.load` が落ち、握りつぶされる | 示せない（その設定の環境が手元に無い。P7 は環境変数が効かないことを意図している） | 無し | 残課題 |
| R4 | orca の `-I` の理由が 2 箇所（30 行目と `-n` 節の 60 行目）に重複 | 示せる（文面） | 無し | 残課題 |
| R5 | 計画ファイルの件数「orca 4 箇所」は 5 箇所の誤り | 示せる（`grep`） | 無し（成果物ではない） | 計画ファイルを訂正（関門の対象外） |
| R6 | cmux の Issue モードの URL を `git remote get-url origin` の sed で組み、ssh:// や origin 無しで壊れた `https://` URL が通る | 示せない（この周で再現していない。変更前からの挙動） | 無し | 残課題 |
| R7 | ブラウザの探索が python の失敗を `2>/dev/null \|\| echo ""` で握りつぶす（`-I` 非対応の古い Python も「見つからない」と同じに見える） | 示せない（変更前からの挙動。古い Python は未証明） | 無し | 残課題 |

`/code-review` は受入基準を受け取る前に 1 度報告し（上の R1〜R7）、受け取ってから 2 度目を返した（下の A1〜A8。
**どちらも 1 パス目**——2 度目は受入基準つきで、陽性対照を自分で取って I1・I2・P1〜P6 と `PYTHONPATH` を確認した）。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| A1 | P7 の `PYTHONSTARTUP` は判別していない——`python3 -c` はもともと `PYTHONSTARTUP` を走らせないので、旧版でも marker は出ない | 示せる（レビューの再実行: 旧版 rc=1・marker 無し） | 無し（P7 の主張を `PYTHONPATH` に弱める） | 計画の P7 の主張を訂正（関門の対象外）。PR コメントで名指し |
| A2 | 著者の P3 の証拠（`-n` は RAN しない）は陽性対照が無い（新旧とも既に `-I`） | 示せる（構成） | 無し（Verifier とレビューが `-I` を外した対照で RAN を確認済み） | 記録のみ（P3 の証拠は関門側の対照を正とする） |
| A3 | 件数「orca 4 箇所」は 5 箇所 | R5 と同じ | 無し | R5 で訂正済み |
| A4 | 「すべて `-I`」を強制する歯止めが無い | R1 と同じ | 無し | 残課題 |
| A5 | 「カレントディレクトリ（レビュー対象のリポジトリ）」は不正確——`-w`/`-r` でもブラウザ手順は worktree 入場前で、初回の cwd は利用者自身のチェックアウト | 示せる（`SKILL.md` の手順の順序） | 無し（I1 は import の有無で、文言の前提は対象外） | 残課題 |
| A6 | 「この確認も黙って通る」は exit 0 で終わるよう細工した `json.py` の場合だけ。ふつうの／空の `json.py` は rc=1 | 示せる（レビューの再実行） | 無し | 残課題（「通りうる」が正確） |
| A7 | `-I` は import しか止めない——`PATH` に `.` があれば cwd の `orca`／`cmux`／`python3` が走る。pyenv の `.python-version` も | 示せない（`PATH` に `.` を含む環境での再現なし） | 無し（I1 は import） | 残課題（既知の限界） |
| A8 | `-I` の理由が orca の 2 箇所に重複 | R4 と同じ | 無し | 残課題 |
