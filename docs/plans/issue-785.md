# Issue #785 — cruise child-cycle.py: 長期トークンで起動した親から起こした子が、長期トークンを継がない

`child-cycle.py launch` は子の `claude -p` の環境を親の Bash の環境（`dict(os.environ)`）から作る。
Claude Code 2.1.316 は起動時の `CLAUDE_CODE_OAUTH_TOKEN` を Bash の環境から外すので、長期トークンで起動した cruise の親の子は
長期トークンを継がず、対話ログインの OAuth（8 時間）で回るおそれがある（#584 のコメント・PR #784 の `/code-review` CR1・R2-1）。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-11-02）。親からサブエージェントとして委ねられた。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・`周の途中の課題 = 外に出す`
（出所: 利用者の確認（起動時 2026-10-27・再開時 2026-10-28／2026-11-01））。台帳は書かない（親が書く）。マージしない。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））。
版の上げ方: `dev-loop` を **patch**（不具合の修正）。main の先端 1.75.1 → **1.75.2**（マージの直前に main が進んでいたら、取り込んで上げ直す）。

重い検査（`check-all.py`・テスト）は順番待ち越しに走らせる:
`python3 /Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py -- <コマンド>`。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/child-cycle.py` — Bash の環境に無ければ、起動した claude の環境の値を子に置く・起動時の 1 行・記録の `auth`・docstring
- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 読み方を `launcher_auth_env`（値を返す）に出し、`launcher_auth_names` はそれを読む（写しを作らない）
- `scripts/test-child-cycle.py` — 偽の `ps` と認証の試料・変異 5 件
- `scripts/test-check-unattended-env.py` — 動かした行に合わせて変異の文字列を 1 つ直す
- `plugins/dev-loop/skills/cruise/references/child-process.md` — 「認証」の記述を実際の振る舞いに合わせる
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行（`dev-loop`・`cruise`）
- `docs/plans/issue-785.md` — この計画ファイル
- `docs/usage/cruise-long-lived-token.md` — 「読むのは起動口だけ」に child-cycle.py の例外を書く（2 パス目の `/code-review` CR2-1 で広げた。手を動かす前にここへ足した。
  理由: この周が「読む」ものを 1 つ増やしたので、公開ページの記述が偽になった。受入基準 A8 を足す）

触らない:

- `launch-with-long-token.sh`・点検の判定（`check_auth`）の振る舞い
- 子より先に使われる認証（`ANTHROPIC_API_KEY` など）を起動した claude の環境から子へ渡すこと（docstring の「守らない」に書く）

### 同じことを述べている箇所の数

「子が親の長期トークンを継ぐか」を述べているのは 2 箇所——`child-process.md` の「認証」と `child-cycle.py` の docstring。
docstring に振る舞いの本体を書き、`child-process.md` は観測と要点だけを持って docstring を指す。読み方（祖先の claude の環境）は
`check-unattended-env.py` の 1 箇所に置き、`child-cycle.py` は読み込む（式を 2 箇所に置かない）。分けない理由: 1 つの不具合で、2 箇所は役割が違う。

## 乗るデプロイ経路

main へのマージでプラグインの配布（dev-loop 1.75.2）。公開サイトは `docs/` を触らない（計画ファイルを除く）ので反映経路なし。マージは親がする。

## verify の受入基準

観測の道具（scratchpad。リポジトリには入れない）: `probe.py <child-cycle.py>…` —— Bash の環境に `CLAUDE_CODE_OAUTH_TOKEN` があるか、
起動した claude の環境の名前（`launcher_auth_names`）、一時の git リポジトリで `child-cycle.py launch` を偽の `claude`（受けた環境に
`CLAUDE_CODE_OAUTH_TOKEN` が空でなくあるかを真偽だけで書く）に向けて起こした結果を、真偽と名前だけで出し、ファイルにも残す。
長期トークンの起動口から `claude -p`（haiku・`--max-turns 3`・`dontAsk`・その 1 コマンドだけ許可）に走らせる。

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 長期トークンで起動した親（Bash の環境に無い）から起こした子の環境に `CLAUDE_CODE_OAUTH_TOKEN` が空でなく在る。直す前は無いことを観測する | `launch` の環境の組み立て・祖先の辿り方（zsh・python を越える）・spare | 実プロセス: 起動口の `claude -p` から probe（直す前の main と直した worktree を同じ回で）。偽の ps の試料: `test-child-cycle.py` の #40・#46 |
| A2 | トークンの値を出力・標準エラー・引数・記録の `.json`・例外の文に出さない | 起動時の行・記録の `auth`・`children/` の `.jsonl`・`.err`・失敗の理由（`launcher_auth_env` の why）・例外 | 試料で全ファイル・出力に試料の値が無いこと（#40〜#46）・変異「値を出力に出す」。実プロセスで probe が値を手元で引いて比べた真偽 |
| A3 | 親が対話ログインのときの振る舞いは変えない（子は Bash の環境だけを継ぐ。起動時に 1 行で言う） | 祖先にトークンが無い・祖先を読めない・祖先に claude が無い・消す設定 | 試料 #42〜#45。実プロセス: このセッション（対話ログイン）で probe |
| A4 | Bash の環境にトークンがあれば、それを継ぎ、祖先の値で上書きしない | 祖先を先に見る | 試料 #41・変異 |
| A5 | `child-process.md` の「認証」が実際の振る舞いと合う | 「継ぐ」「測っていない」の記述 | 読んで突き合わせる・`check-skill-pointers.py` |
| A6 | 既存の歯止め・点検（`check-unattended-env.py` の認証）を割らない | `launcher_auth_names` の切り出し・変異の文字列 | `check-all.py`（順番待ち越し）が緑・PR の CI が緑 |
| A8 | 公開ページ `cruise-long-lived-token.md` の「トークンを読むもの」が実際と合う（2 パス目で広げた） | 警告の「読むのは起動口だけ」・部品の表 | 読んで突き合わせる・`check-site-links.py` |
| A7 | 版を 3 箇所で上げる | `marketplace.json`・`plugin.json`・`SKILL.md` の 2 行 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |

**この環境では証明できないもの（未証明）**: 子がそのトークンで実際に認証して 8 時間を超えて 401 で止まらないこと——子を偽の `claude` にしたので、
子の認証そのものは見ていない（本物の子で回すと数ドルかかり、8 時間の観測は #584 の受入基準 1 として利用者が pid 13906 で続けている）。

**生成物**: `skill-metrics.py` の生成ブロック（設計 §8.2）は `SKILL.md` の節構造に依る——版の行だけを変えたので、`check-all.py` の `--check` で鮮度を見る。図の書き出しは無し。

必須要件の掛け算: 受入基準を Verifier・`/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

## 未解決の判断・確認待ち

- 消す設定（`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`・`GITHUB_ACTIONS`）のとき祖先から渡さない——推奨で決めた（消すと決めた値を読み戻さない）。Issue は決めていない。

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/785-child-long-token`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-785`・
  起点 `ef81153e`・base は `origin/main`（`refs/remotes/origin/HEAD`）を解決した `ef81153ee38b08adb73aa2853a88c716e4af327a`
- 観測（直す前）: 2026-11-02 18:19、起動口の `claude -p`（$0.0017）で probe——Bash の環境に無い（False）、起動した claude の環境の名前は
  `{CLAUDE_CODE_OAUTH_TOKEN}`（陽性対照）、main の `child-cycle.py` で起こした子の環境に無い（False）。**継がないことを観測した。**
- 観測（直した後）: 2026-11-02 18:30、同じ形（$0.011）で main と worktree を同じ回で——main は False、worktree は True・起動時の行・`auth` は
  `{passed: True, from: launcher}`・値は出力・記録に出ていない（False）。対照: このセッション（対話ログイン）で worktree は False・「起動した claude の環境にも無い」の行。
- 交絡: 「起動口の claude の環境にトークンが無かったから子に無い」を、同じ回の `launcher_auth_names` が名前を返したことで潰した（陽性対照）。
  「probe の報告を haiku が作った」は、各回の直後に probe が自分で書いた `probe.log`（実物）を著者が読んで潰した——**ただしファイルは次の回が上書きし、
  いま残っているのは対話ログインの対照の回だけ**。長期トークンの 2 回の記録として残っているのは `pre.json`・`post.json` の `result`（claude -p の写し）で、
  **残っている物からは、写しであることを越えて再確認できない**（V1）。
- 割り目（手順 4）: 不在の周なので訊かない（`references/absent-lines.md` の「訊く場面」）。
- 1 パス目の関門に渡した起点（HEAD）: `a83ff6e3`（PR #786）
- Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet。起動したのはその定義——報告が Read/Bash だけを使った）: 反証 1 件（V1。実装の欠陥 0）
- `/code-review` 1 パス目（high・受入基準を args で渡した）: 指摘 8 件（CR1〜CR8。blocker 0）。PR の CI は `5fee1f07` で緑
- 1 パス目の指摘対応: 直す 5 件（CR2・CR3・CR4・CR5・CR8）＋計画ファイルの書き直し（V1）。差分は 0 行でないので 2 パス目を回す
- 割り目（2 パス目の前）: 不在の周なので訊かない
- 2 パス目の関門に渡した HEAD: `4be6bf03`
- Verifier 2 パス目（sonnet）: 反証 0 件（所見 2: ps の手順の 0 の読み方・dict に他の認証の値も載る）
- `/code-review` 2 パス目（high・受入基準を args で渡した）: 指摘 4 件（CR2-1〜CR2-4。新しいコードの欠陥 0）。`check-all.py` は時間切れで途中まで（32 本緑）
- 2 パス目の指摘対応: 直す 3 件（CR2-1・CR2-2・V2-1）。狭いパスの起点（指摘対応を始める直前の HEAD）: `d0f085d8`

## 既知の限界・決着済みの論点

- 子より先に使われる認証（`ANTHROPIC_AUTH_TOKEN`・`ANTHROPIC_API_KEY`・`apiKeyHelper`）が起動した claude の環境にだけあっても子へは渡さない——渡すのは
  `CLAUDE_CODE_OAUTH_TOKEN` だけ（Issue の範囲。起動口 `launch-with-long-token.sh` はそれらがあると起動しない）。docstring の「守らない」に書いた。
- 値は `ps eww` の出力を空白で割って読む——空白を含む値は読めない（トークンは空白を含まない）。点検と同じ読み方の限界。

### 採否の表（1 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1: A1 の実プロセスの証拠は、残っている物では claude -p の写し（probe.log は対照の回だけ） | 示せる（`probe.log` 9 行・`pre.json`／`post.json`） | 無し（成果物でなく計画ファイルの記述。実装の欠陥 0） | 計画ファイルを書き直した（関門の検査対象外）。`child-process.md` にも写しであることを書いた |
| CR1: `ps eww` を空白で割るので、値に ` CLAUDE_CODE_OAUTH_TOKEN=…` を含む別の変数があると偽の値を子に渡す | 示せる（偽の ps の試料で `('junk','launcher')`） | A1・A3（試料の上で） | 残課題——そうした値の変数は実際の利用でまず起きず、`ps eww` の形では環境の区切りを決められない（点検と同じ読み方の限界）。PR コメントに記録だけ |
| CR2: `check-unattended-env.py` の「守る」が「関数の外へ出すのは名前だけ」のまま | 示せる（226 行） | A2（値の扱いの約束の記述）——この周が持ち込んだ後退 | 直す |
| CR3: spare の経路の試料が無い | 示せる（#40〜#46 に無い） | A1（経路に挙げた） | 直す（#47） |
| CR4: 例外の枝を通る試料が無い | 示せる（試料が無い。`{exc}` に変えた変異が緑のまま） | A2（経路に「例外の文」を挙げた） | 直す（#48。陽性対照: `{exc}` にした写しで 2 件赤） |
| CR5: #43〜#46 の記録の `auth` を見ていない | 示せる | A2・A3 | 直す |
| CR6: Bash の環境の値が空白だけで祖先にも無いと、子は空白の値を継ぐのに「渡していない」と言う | 示せる（試料の上で） | 無し（子は Bash の環境を継ぐ——言っていることは事実。空白だけの値は実際の利用でまず起きない） | 残課題 |
| CR7: 起動口（キーチェーン）経由で子を起こす設計の代案 | 示せない（設計の比較） | 無し | 残課題 |
| CR8: `child-process.md` の「起動口」が 2 つのものを指す | 示せる（54 行） | A5 | 直す |

### 採否の表（2 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1: 公開ページの「読むのは起動口だけ」が、child-cycle.py も読むようになって偽 | 示せる（`cruise-long-lived-token.md` 14 行） | A8（広げた）——この周が持ち込んだ後退・利用者に見える誤り | 直す（例外を 1 段落） |
| CR2-2: docstring が「対話ログインで回る」を観測したと書くが、観測は偽の子の環境に無いことまで | 示せる（`child-cycle.py` 30 行） | A5（`child-process.md` が指す docstring） | 直す（「子の環境に長期トークンが無い」に弱め、本物の子は測っていないと書く） |
| V2-1: `ps eww … grep -c` の 0 は「無い」と「見えない」の両方 | 示せる（`X=1 /bin/sleep` で `PATH=` が 0。本物の claude（pid 13906）では `PATH=` 1・トークン 1） | A1（確かめる手段） | 直す（`PATH=` も数えてから 0 を読む） |
| CR2-3: `launcher_auth_env` は他の認証の値も返す。子に OAuth だけを渡すことを試料が押さえていない | 示せない（いまのコードは `LONG_TOKEN` だけを使う。将来の書き換えの話） | 無し | 残課題 |
| CR2-4: `load_unattended` と `load_ledger` の重複 | 示せない（不具合でない） | 無し | 残課題 |
| V2-2: dict に他の認証の値もメモリ上は載る | 示せない（出力・記録に出ない） | 無し | 残課題（CR2-3 と同じ） |

## 起票

- この周の起票: 0 件（関門の報告を受けて手順 8 で振り分け直す）
