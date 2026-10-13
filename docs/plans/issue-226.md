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
`python3 -c` は orca 4 箇所（うち `-n` の 2 箇所は #197 で `-I` 済み）・cmux 1 箇所。

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
- 関門: 未着手（次は手順 5 の Verifier 1 パス目と `/code-review` 1 パス目）
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
