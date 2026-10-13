# Issue #197 — orca・cmux: -n の cd が単引用符（cmux は空白も）を含むパスで壊れる

## 1. 変更範囲

触る:

- `plugins/cmux/skills/cmux/SKILL.md` — `-n` の節（と版のバナー）
- `plugins/orca/skills/orca/SKILL.md` — `-n` の節（と版のバナー）
- `plugins/cmux/.claude-plugin/plugin.json` — version
- `plugins/orca/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — cmux と orca の version
- `docs/plans/issue-197.md` — この計画ファイル

触らない:

- 共通手順（ブラウザ）・各モードの節——受入基準の外
- description（3 箇所）——能力は変わらないので触らない
- 改行など制御文字を含むパス——Issue の受入基準の外（空白と単引用符）。残課題に書く

**直し方の決定**:

- **cmux**: `cmux new-surface --working-directory <path>` がある（0.65.1 の `--help`）。
  **cd を送らずに作成時の cwd を指定する**——シェルを通らないので、引用の問題が丸ごと消える。
  Issue の「直し方の候補」の 2 つ目そのもの。
  - **同じ行の別の欠陥も消える**（実機で確認）: 0.65.1 の `new-surface --json` は `surface_ref` を返すのに、
    手順は `surface_id`／`ref` を読むので **`NEW_SURFACE` が常に空**になる。空の `--surface` は
    `$CMUX_SURFACE_ID`（呼び出し元の端末）に解決されうる。**どの形のパスでも、新しいタブは cd しない**。
    手順 1 と手順 2 が別の Bash 呼び出しに分かれていて変数が消える点（#196 の残課題）も、1 コマンドになるので消える。
    **これは受入基準（新しいシェルがそこへ移る）を満たすのに避けられない**ので、範囲の内とする。
- **orca**: `terminal create` に cwd の指定は無い（1.4.223 の `--help`。`--command` は
  「host が起動したシェルに打ち込まれる」＝ macOS ではログインシェル）。
  **`python3` の `shlex.quote` で引用して `--command` に渡す**（`python3` は既にこのブロックが使っている）。
  `printf '%q'` は採らない——zsh と bash で出力が違い、`$'…'` の形を返すことがある。

**複製の数**: `-n` の cd を述べている箇所は各 `SKILL.md` に 1 箇所ずつ（`CURRENT_DIR`・`new-surface`・
`cmux send`・`terminal create` を `plugins/` と `docs/` で引いた。`docs/plans/issue-194.md` は過去の記録）。
版は 2 プラグイン × 3 箇所（CI が見る）。**分けない理由**: Issue が 2 つを 1 件で求めている。2 箇所は互いに独立。

## 2. デプロイ経路

- マーケットプレイス（`plugins/` と `marketplace.json`。利用者が `plugin update` で取る）。
- `docs/` は計画ファイルだけ（GitHub Pages に載るが記録のみ）。破壊的・不可逆な操作は無い。

## 3. 受入基準

**I1. `-n` で作った新しいシェルが、`-n` を呼んだディレクトリへ移る——パスが空白・単引用符を含んでも（cmux と orca の両方）。**

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 cmux・空白と単引用符と `$` を含むパス | 新しいシェルの `pwd` がそのパス | `--working-directory` でシェルを通さない |
| P2 orca・同上 | 同上 | `shlex.quote` で引用して `--command` |
| P3 cmux・作成に失敗 | 呼び出し元の端末に何も打ち込まない・非ゼロ | `send` を使わない（1 コマンド） |
| P4 orca・作成に失敗 | 同上（#194 の F4） | `--command` のまま。`ok` を見て非ゼロ |
| P5 ふつうのパス（特殊文字なし） | 回帰しない | 同上 |
| P6 手順を書かれたとおり Bash の呼び出しに載せる | 変数が呼び出しをまたがない | 1 回の呼び出しで完結 |

**I2. 版が揃い、patch で上がっている**（cmux 1.1.6 → 1.1.7、orca 1.0.1 → 1.0.2）。`check-all.py` が緑。

### 証明の手段

- P1・P2・P5: 実機（cmux 0.65.1・Orca 1.4.224）で、空白・単引用符・`$` を含むディレクトリから
  ブロックを流し、新しいシェルに `pwd` をファイルへ書かせる。**陽性対照**として旧い形を同じパスで流し、
  壊れる（`quote>` で止まる）ことを見る。
- P3・P4: cmux は存在しない pane を指定して失敗させる。orca は #194 で確認済みの形を変えない（`--command` の値だけ変える）。
- **未証明**: 改行を含むパス（受入基準の外）。他の cmux/Orca の版。ログインシェルが zsh 以外（fish など）の環境。
  **Windows ホストの Orca**（PowerShell・cmd——`shlex.quote` は POSIX 向け）。
  **SSH 経由の端末・cmux の SSH ワークスペース**（ローカルの `$(pwd)` がリモートで解釈される）。いずれも手元に環境が無い。

### 生成物

**生成物なし**——図の書き出しも §8.2 の測定値も `dev-loop` の `SKILL.md` に依存し、この周は触らない
（`skill-metrics.py --check` は `check-all.py` が回す）。

## 4. 未解決の判断

- なし

## 5. 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/197-n-cd-quoting`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-197`、
  起点 `b8c5e89`、**base: `origin/main` → `b8c5e89886ac29b34cefb260dc6bc87efd2e0b63`**
- 実装コミット: `4903190`。`check-all.py` 30/30 緑（文言修正後に回し直した）
- 関門:
  - **1 パス目 Verifier**（sonnet）: **反証 0 件**。著者の主張のうち `surface_ref`・「シェルを通らない」は未確認（サーフェスを作れないため）。
    **Verifier は禁じた `cmux new-surface` を走らせようとし、分類器に拒否された**（実行されていない。`git status` は空のまま）。
  - **1 パス目 `/code-review`**（high）: **指摘 10 件**→ 直す 3 件（R1・R2・R2b）、残課題 8 件（§6 の表）。
  - **1 パス目の指摘対応**: 済（orca `SKILL.md` の `-n` ブロックに `-I` と `|| exit 1`）。
    確認: `SKILL.md` からブロックを抜き出し、偽の `orca` に対して 4 通り（特殊パス＋`shlex.py`/`json.py` を置く・`ok:false`・
    ふつうのパス・`python3` が失敗）を流した（scratchpad の `verify-block.sh`）。**陽性対照**: 同じ手順を修正前の版に当てると
    `cd ` で `$HOME` へ・`ok:false` で rc=0・`python3` 失敗でも `orca` が呼ばれる。`check-all.py` 30/30 緑。
  - **次**: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目——**両方とも未着手**。
    2 パス目の対象差分は指摘対応のコミットだが、受入基準と base（周の base）はまるごと渡す。
- 割り目（手順 4）: 提案済み——**人間の選択は「ここで割る」**（2026-10-13）
- 交絡を潰した手順（実装前の実験）:
  - **cmux 旧形の陽性対照**: 正しい `surface_ref` を使ってなお、`cd $CURRENT_DIR` は `quote>` で止まり、
    `pwd` はメインのチェックアウトを返した（新しいサーフェスの既定の cwd）。**旧形が「たまたま cwd が合って通る」ことは無い**。
  - **cmux 新形**: `new-surface --working-directory "<…/a b'c $HOME>"` → `pwd` がそのパス。
  - **orca 旧形の陽性対照**: `--command "cd '<…/a b'c $HOME>'; pwd > m"` → `terminal read --screen` が `quote>`、marker 無し。
  - **orca 新形**: `shlex.quote` → marker がそのパス。
  - **観測窓**: marker は作成後 4 秒（orca）・2 秒（cmux）で読んだ。旧形の「無し」は `quote>` の画面で、遅延ではないことを見た。
  - **途中で Orca が自動更新で再起動した**（1.4.223 → 1.4.224）。最初の旧形の結果は読めなかったので、1.4.224 で両方を当て直した。
- 実装後の確認（著者。関門ではない）:
  - **`SKILL.md` からブロックを抜き出して `zsh -c` でそのまま流した**（手で写していない）。
    `…/tmp-197/a b'c $HOME` と `…/tmp-197/plain` の両方で、cmux・orca とも新しいシェルの `pwd` がそのパス（P1・P2・P5）。
    pwd の記録はブロックの後ろに足さず、作った端末へ別途 `send` した。
  - P3: `new-surface --workspace workspace:999999999` → rc=1（`Workspace ref not found`）。ブロックに `send` は無い。
    **`--pane pane:999999999` は失敗しない**（rc=0 で現在のペインに作る）——失敗の作り方として使えない。
  - P4: orca の `--command` の外側の形は #194 から変えていない。

## 6. 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| cmux を `shlex.quote` で直すか | 採らない | `--working-directory` があり、シェルを通らない |
| `printf '%q'` | 採らない | zsh と bash で出力が違う |
| 改行を含むパス | 範囲外 | 受入基準は空白と単引用符 |

### 1 パス目の指摘と採否

Verifier（sonnet・`dev-loop:dev-loop-verifier`）: **反証 0 件**。注意点 1 件（Windows ホスト）は下の R6 に畳む。
`/code-review`（high）: **10 件**。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | orca: 引用の置換の失敗を検査せず、`CD_COMMAND="cd "` → `$HOME` へ移って rc=0 | 示せる——cwd に `raise SystemExit(3)` の `shlex.py` → `rc=3 [cd ]`（scratchpad の `repro.sh`） | I1（P2） | **直す**（`|| exit 1`） |
| R2 | orca: `python3 -c` が cwd の `shlex.py` を import する | 示せる——同上。`-I` で正しく引用され、`zsh -fc` の `pwd` がそのパス | I1（P2） | **直す**（`-I`） |
| R2b | （R2 と同じ形を著者が横に洗った）同じブロックの ok 判定の `python3 -c` が cwd の `json.py` を import する | 示せる——`raise SystemExit(0)` の `json.py` で `{"ok": false}` が rc=0。`-I` で rc=1 | I1（P4） | **直す**（`-I`） |
| R3 | cmux: 「`--working-directory` はシェルを通らない」は SSH ワークスペースでは偽かもしれない（バイナリに `cd … \|\| true`） | 示せない（バイナリの文字列のみ。SSH ワークスペースは手元に無い） | 無し（未証明に足す） | 残課題 |
| R4 | P3 の失敗の作り方がブロックと別のコマンド（cwd が消えた等で黙って既定 cwd に落ちる可能性） | 示せない | 無し | 残課題 |
| R5 | `--working-directory` に要る cmux の版を書いていない | 示せない（古い版が手元に無い） | 無し | 残課題 |
| R6 | 未証明に Windows ホスト（PowerShell・cmd）と SSH 経由の端末が無い（Verifier も同旨） | 分類の指摘 | 無し | 残課題（§3 の未証明に足す） |
| R7 | cmux README:17・`docs/plugins/index.md`:455 が「そこで実行する」のまま | 示せる（文面）。ただし変更前の `SKILL.md` も同じ趣旨で、この差分が作った食い違いではない | 無し | 残課題 |
| R8 | cmux の `new-surface` に `--focus` が無く、裏で作られるだけ | 変更前からの挙動 | 無し | 残課題 |
| R9 | `SKILL.md` に版固有のキー名（`surface_ref`）を書いている | 示せない | 無し | 残課題 |
| R10 | `--pane` 未指定で、置き場所がフォーカス中のペインに依る | 示せない（推測） | 無し | 残課題 |

**範囲外として残すもの**: `orca` の共通手順（31・35・84 行）と `cmux` の 61 行の `python3 -c` も同じ形（`-I` 無し）だが、
`-n` の外で受入基準に無い。残課題に書く。

この周の起票: 0 件
