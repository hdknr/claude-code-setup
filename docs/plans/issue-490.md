# Issue #490（#504 と束ねた周）— cruise の起動時に不在の間の到達できる範囲と止まる要因を点検し、隔離が解けたかの確かめ方を測った形にする

cruise の起動・再開の点検（cruise `SKILL.md` §1・§3、`check-unattended-env.py`）を触る 2 件の Issue を、**1 周・1 PR** で扱う
（cruise の台帳のまとめ。代表 #490。`plugins/dev-loop/skills/cruise/references/grouping.md` の「まとめの周」）。
周の Issue は #490（worktree・ブランチの名前）。受入基準は 2 件のものを、Issue 番号を付けて下に並べる。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-10-31）。台帳 `issue-474` の確かめた線:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））。
加えて利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、`要確認` の Issue を立てる（#557 の形。この周が自分で立てる）。
マージは親がする（この周は手順 6 の PR・CI の確認・関門 2 パスと狭いパス・手順 8 の件数の行まで）。台帳は書かない（親が書く）。
**実際に使われている台帳 `.claude/plans/cruise-issue-474.json` には書かない**——読むのは写し（scratchpad）か一時リポジトリの台帳だけ。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — #490（`--cruise --ledger <名前>` で到達できる範囲と止まる要因を出す）・docstring
- `scripts/test-check-unattended-env.py` — #490 の試料と変異
- `plugins/dev-loop/skills/cruise/SKILL.md` — #490（§3 の点検に台帳を渡す・§1 の再開・§4 の 4 の判断待ちの印・§6 で渡す）・#504（§1 の隔離が解けたかの確かめ方）・版の 2 行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-cruise.md` — 公開ページの §2（環境点検）と再開の節（隔離が解けたかの確かめ方）
- `docs/plugins/dev-loop-design.md` — `skill-metrics.py` の生成ブロック（変わるなら。手で書かない）
- `CLAUDE.md` — `test-check-unattended-env.py` の行（見るものが増える）
- `docs/plans/issue-490.md` — この計画

触らない:

- 実際の台帳 `.claude/plans/cruise-issue-474.json`（親が書く・いま使われている）
- `ledger.py` の台帳の形・振る舞い（読むだけ。`load`・`ledger_path`・`has_dist_mark`・`is_stranded` を import して使う——式を 2 箇所に置かない）
- `scripts/measure-guard-os*.sh`（#504 の測定は scratchpad の使い捨ての probe で行った。リポジトリの probe 一覧には足さない——下の「未解決の判断」）
- `references/absent-lines.md` の線の決まり（照合の規定は変えない。スクリプトは機械で決まる部分だけを出す）

### 同じことを述べている箇所の数

- 「起動時の点検が見るもの」: `check-unattended-env.py` の docstring（原本）、cruise `SKILL.md` §3、公開ページ §2、`CLAUDE.md` のテストの行 = 4 箇所。原本は docstring、他は指すか要約。
- 「隔離が解けたかの確かめ方」: cruise `SKILL.md` §1（原本）、公開ページの再開の節 = 2 箇所。
- 「マージの前の判断待ちの印 `利用者の判断待ち`」: cruise `SKILL.md` §4 の 4（親が書く）、`check-unattended-env.py` の docstring（読む）、`references/found-lines.md`（既に `blocked` の行に同じ印を書いている。変えない）= 3 箇所。
分けない——#490 と #504 はどちらも cruise の起動・再開の点検で、同じ `SKILL.md` §1・§3 を触る（まとめ #641）。

## 乗るデプロイ経路

プラグイン `dev-loop` の中身（スクリプト・文書・SKILL.md の版）——main へのマージでプラグインの新しい版が配られ、サイト（`docs/`）が再ビルドされる。
マージの可否は親（cruise）が決める。

## 周の在り処

- ブランチ: `issue/490-cruise-reach-check`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-490`（`prepare-worktree.sh` で作った。cruise の子なので `EnterWorktree` は使わず、`cd <worktree> && …` で作業する）
- 起点: `4a8c7e8a`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`、取り直した）→ `4a8c7e8a2b8a605670d1116ed66fc72e5fffe5fb`
- PR: #734
- main を取り込んだ（`cd1fd52a`、#703 のマージ）→ 式を当て直した base: `af86585d393803b0c7a1b00ee9e544e392aaf922`（2 パス目と狭いパスに渡す）

## verify の受入基準

### #490（`check-unattended-env.py --cruise --ledger`・cruise §3）

**到達**＝その周が不在の間に「マージまで進む」「PR で止まる」「始まらない」「止まっている」のどれになるか。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 起動時（新規・再開、`--absent` の有無に依らず）の点検が、台帳の済んでいない周ごとに到達と止まる理由を出す | cruise §3 の呼び出し（`--present` あり／なし）、§1 の再開（`--absent` の再開も）、台帳を渡し忘れた呼び出し | §3 の 2 行に `--ledger issue-<親>`。渡さなければ「判定できない」（通過と読まない） |
| A2 | 判定は散文でなくスクリプトが出す——`マージ` の線が効くか（台帳の線・`不在の線:`・`マージの反映:` の宣言・カタログの有無・配布の確認の印・`user_ops`）| 宣言なし・`ドキュメントのみ` なのにカタログがある・配布の宣言で印が無い・線が `止まる`・`user_ops` に `gh pr merge`・居る cruise | `merge_effect` が機械で決まる部分だけを判定し、決まらないものは「判定できない」 |
| A3 | 依存の止まり（マージ待ち・`await`・`blocked`・取り下げ・取り残し）を、依存する周の「始まらない」として名指しする（推移的に） | 依存の依存が止まる・まとめの中の依存 | 依存グラフを辿って最初に止まる依存先と理由を出す |
| A4 | PR の衝突（`CONFLICTING`）を止まる要因に出す。`mergeable` が `UNKNOWN`・`gh` が失敗したら「判定できない」 | `gh pr view` の結果 | 偽の `gh` の試料 |
| A5 | 同じプラグインの版を上げる開いた PR が 2 本以上なら、版の取り合いとして止まる要因に出す | `files` に `.claude-plugin/plugin.json` | 偽の `gh` の試料 |
| A6 | 判断待ち（`blocked`、`note` が `利用者の判断待ち` で始まる PR）を止まる要因に出す | `blocked` の行・PR の行の印 | 印の決まりを cruise §4 の 4 に書く |
| A7 | 偽陽性が無い——衝突・判断待ちが無く、マージの線が効くリポジトリでは止まる要因を出さない（要対処 0） | 全部マージできる台帳 | 試料 |
| A8 | cruise #474 の 2026-10-28 時点の台帳と実物を入力にすると、#490 の 1〜4 がすべて出る | 再構成した台帳＋偽の `gh`（#479・#481・#483 が `CONFLICTING`、#485・#486 が開いた PR、#276・#291 が #286 に依存、`マージの反映:` の宣言なし＋カタログあり、#483 の `note` に判断待ち） | 試料（下の「既知の限界」: 4 は印を書いた形でだけ出る） |
| A9 | 何も書かない・設定もファイルも書き換えない（既存の守る）。台帳も書かない | `ledger.load` しか呼ばない | 試料（前後のバイト比較に台帳を含める） |
| A10 | 既存の点検（許可・宣言・止まりうる操作・起動場所・認証・不在の項目）を変えない | リファクタした宣言の読み（フェンス・コメント） | 既存の試料と変異が全部通る |

### #504（cruise §1 の隔離が解けたかの確かめ方）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| B1 | §1 が名指しする確かめの操作は、隔離中に拒まれることを測ってある形だけ | `cd <メインの作業ツリー> && git worktree list`・`git -C <メイン> worktree list`・素の `git worktree list`（cwd が worktree なら隔離中でも通る） | probe の実測（下の「交絡を潰した手順」）。素の形を名指ししない |
| B2 | 測っていないことを断定しない——測った版・入り方（`claude -w`）と、測っていない入り方（`EnterWorktree(path)`＋`/clear`・`ExitWorktree` の後）を分けて書く | §1 の文・公開ページ | 文面 |
| B3 | 拒まれたら戻れなかったものとして扱う（既存の決まりを弱めない） | §1 | 文面 |

### 両方に掛かる

| # | 不変条件 |
| --- | --- |
| C1 | 版を 3 種類（`marketplace.json`・`plugin.json`・全 `SKILL.md` のバナー 2 行）で main より上にそろえる |
| C2 | 生成物: `skill-metrics.py --check` が通る（`SKILL.md` の行が動くなら再生成）。`exports.json`（図）は該当なし |
| C3 | `check-all.py` が全部緑、PR 側の CI も緑 |
| C4 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1・2 パスとも渡す（4 つの受け渡し） |

### この環境では証明できないもの（未証明）

- U1: 本物の `gh` の `mergeable`・`files` の値の形（偽の `gh` で当てる。実物の形は手で 1 度だけ見る——下の verify）。
- U2: #504 の確かめが `EnterWorktree(path)`＋`/clear` の隔離（#484 の形）でも同じに振る舞うこと——`/clear` は対話のセッションでしか打てず、`claude -p` では作れない。
  （1 パス目の `/code-review` の指摘で、`EnterWorktree(name)` とその後の `ExitWorktree` は測った——下の交絡の表の E1・E3。）

## 未解決の判断・確認待ち事項

- **仕様の穴 G1（推奨で決めた）**: 「マージの前に人の判断が要る」を機械で見分ける方法を Issue は決めていない。
  選択肢: (a) `note` の先頭の印 `利用者の判断待ち`（`found-lines.md` が `blocked` の行に既に使う印）を PR の行にも書く決まりにして、印だけを読む【推奨】／
  (b) `note` に「判断」を含む行を全部判断待ちと読む（自由文の部分一致。「利用者の判断で…マージした」も当たる偽陽性）／
  (c) PR のコメントから狭いパスの見出しを探す（PR コメントの見出しは決まっていない）。
  推した理由: (a) だけが偽陽性を出さず、既存の印と同じ語で、`blocked` の行（found-lines）と PR の行で読み方が 1 つになる。
  代償: 印の無い古い `note`（#483 の「P1 はマージ前に人間が判断」）は判断待ちと読まれない——A8 の 4 は印を書いた形で出る。
  → 確認の Issue を立てる（#557 の形）。
- `measure-guard-os-inner.sh` に #504 の probe を足すか: 足さない（そのスクリプトは #122 の OS の比較のための probe 一覧で、足すと比較の母集団が変わる）。
  測り方は PR コメントと §1 に書く。

## 関門の進捗（再開点）

- 実装: `bb6c7baa`（このセッションで実装。委譲なし）
- Verifier 1 パス目: 済み——反証 2 件（R1・R2。どちらもテストの隙。下の採否の表）。起動した体は `dev-loop:dev-loop-verifier`（sonnet）
- `/code-review` 1 パス目: 済み——指摘 10 件（CR1〜CR10。下の採否の表）
- 1 パス目の指摘対応の起点: `bb6c7baa`——1 パス目の 2 つの関門に渡した時点の HEAD
- 1 パス目の指摘対応: `83f8fd81`（差分あり——2 パス目を回す）
- 2 パス目: 起動（2026-10-31）
- 割り目（手順 6）: 不在のため訊かず続けた
- 狭いパス: 未
- 割り目（手順 4）: 不在のため訊かず続けた
- 手順 5 の反証・差し戻し: 0 件（未）

### 交絡を潰した手順

#504 の測定（2026-10-31・Claude Code 2.1.316・macOS・git 2.54.0）。scratchpad に使い捨てのリポジトリを作り、`claude -w <名前> --allowedTools Bash -p "<そのまま 1 度だけ打て>"` で
起動から隔離したセッションに 1 コマンドずつ打たせた（このセッションは隔離していない。`EnterWorktree` は呼んでいない）。結果は子のトランスクリプトの `tool_result` で確かめた（子の報告ではなく）:

| probe | コマンド | 結果 |
| --- | --- | --- |
| C1（陽性対照: 隔離している） | `git rev-parse --git-dir` | 通る。`…/.git/worktrees/C1` ——隔離した worktree の中で走った |
| P1 | `cd <リポジトリ> && git worktree list` | **拒まれた**——「changes directory to the shared checkout (…) before running git. Refusing to run it」 |
| P2 | `git -C <リポジトリ> worktree list` | **拒まれた**——「redirects git to the shared checkout via -C」 |
| P3 | `git worktree list`（cwd は隔離した worktree） | **通る**——素の形は隔離中でも拒まれないので、確かめにならない |
| E1（`claude -p` で `EnterWorktree(name)` してから） | `cd <リポジトリ> && git worktree list` | **拒まれた**（同じ文言。トランスクリプトに `Refusing to run it` 2 件） |
| E3（`EnterWorktree(name)` → `ExitWorktree(keep)` してから） | `cd <リポジトリ> && git worktree list` | **通る**——戻った後は確かめが「戻れた」と出る（E2 はコマンドを打ち間違えた回で数えない） |
| N1（陰性側の対照: 隔離していない） | `cd <リポジトリ> && git worktree list`（`claude -p`、`-w` なし） | 通る——同じ形が、隔離していなければ通る |

- 候補の交絡 1: 拒んだのがガードでなくモデルの作り話 → 子のトランスクリプトで `tool_result` がガードの文言（`This session is isolated in the worktree …`）であることを確かめた。
- 候補の交絡 2: 隔離していなくても拒まれる形 → N1 で同じ形が通ることを見た。
- 候補の交絡 3: 隔離が効いていないのに通っている → C1 で git-dir が worktree を指すことを見た。
- 残る（潰せない）: 入り方の違い。#484 の隔離は `EnterWorktree(path)`＋`/clear` で、測ったのは `claude -w`。#484 の後の実セッション（`13d9b599…`、`issue-465` に隔離）の拒否も同じガードの文言（`a worktree-isolated session's git operations must target its own worktree`）だったが、そこで `git worktree list` をメインの作業ツリーに向けた記録は無い。→ U2 として §1 と PR に書く。
- 観測窓: 各 probe 1 回ずつ、2.1.316 だけ。

## 既知の限界・決着済みの論点

### 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-R1 依存先が混ざるときの優先順（`KIND_ORDER`）をテストが見ていない | 示せる（逆にする変異が素通り） | A3（守り方の試料） | 直す——混ざった依存の試料と変異 |
| V-R2 版の取り合いの `OPEN` の条件をテストが見ていない（マージ済みの PR を数える偽陽性） | 示せる（恒真にする変異が素通り） | A5・A7 | 直す——試料と変異 |
| CR1 まとめの行を自分の依存だけで決め、まとめの別の行の依存が止まっても「着手できる」 | 示せる（試料で `良い`） | A3 | 直す——まとめの全行の外への依存で決める |
| CR2 判断待ちの印がまとめの代表だけにあると、同じ PR の別の行が「進む」 | 示せる | A6 | 直す——まとめのどれかの行の印を見る |
| CR3 版の取り合いに進行中の行の PR しか数えない（`await` の行の開いた PR） | 示せる | A5 | 直す——済んでいない行の PR を全部見る |
| CR4 判断待ちの印をマージ済みの PR より先に見て、済んだ PR を止まると言う | 示せる | A6・A7 | 直す——マージ済みを先に |
| CR5 公開ページが測っていない入り方まで「測ってある」と読める | 示せる（文面） | B2 | 直す |
| CR6 §6 が点検の到達の止まりを渡す手順を持たない | 示せる（文面） | A1 | 直す——§6 に 1 文 |
| CR7 U2 の `ExitWorktree` の後は測れる | 示せる（測った——E1・E3） | B2（分類） | 直す——測って U2 を狭めた |
| CR8 `cd … &&` の複合コマンドは隔離の外で許可の確認を出しうる（`git -C` で足りる） | 示せない（測っていない） | 無し | 残課題 |
| CR9 印をコロン無しで読み、「利用者の判断待ちは解消した」で止まる | 示せる | A7 | 直す——`利用者の判断待ち:`（全角も） |
| CR10 docstring が ledger.py から使うものを狭く書く・`--help` が古い・ローダーの重複 | 示せる（文面）／重複は示せない | A9（記述）／無し | 文面は直す、ローダーの重複は残課題 |

（関門の指摘の採否は、ここに 1 件 1 行で書く。）

- G1（上の仕様の穴）は推奨 (a) で決めた。決めた値の記録であって、受入基準は足していない。
- マージの線の照合（ワークフロー・`CLAUDE.md`・周の差分）は各周がマージの前に行う（absent-lines の決まり）。起動時の点検は機械で決まる部分（宣言の値・カタログの有無・印・`user_ops`）だけを見て、照合はしていないと出す。
- 宣言が無いリポジトリでカタログも無いとき、マージが反映を起こすかは `CLAUDE.md` でしか決まらない——「判定できない」と出す（通過と読まない）。
- 版の取り合いは `.claude-plugin/plugin.json` を触る PR だけを見る（ほかの版のファイルは見ない）。
- 積んだ周（stacked）は到達に数えない（`next` と同じ）。

## 手順 8（起票の件数）

- この周の起票: 1 件（#735——仕様の穴 G1 の確認の Issue。起票の承認は不在のため訊いていない——台帳の確かめた線 `仕様の穴 = 推奨で決めて起票` と利用者の直接の指示（2026-10-29）で立てる）
