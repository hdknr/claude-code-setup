# Issue #502 — prepare-worktree.sh の出力の「次にすること」が、cruise の子にも EnterWorktree を勧める

**不在の周である**——出所: `/dev-loop:cruise 474 --absent` の再開（2026-10-29）。この周は cruise の親から、worktree の絶対パスで作業する
サブエージェントとして委ねられた。**この周では `EnterWorktree` を呼んでいない**（`prepare-worktree.sh` の出力の「次にすること」は無視した——それがこの Issue）。

使った線（出所: cruise の確かめた線（台帳 `issue-474`）——利用者の確認（起動時・2026-10-27T09:07:27Z）＋利用者の確認（再開時・2026-10-28T07:24:46Z）。親の委譲文で受け取った）:

- `仕様の穴 = 推奨で決めて起票`
- 直す線: **既定**
- `周の途中の課題 = 台帳に足して直す`（台帳には親が足す。この周は台帳を書かず、見つけた課題を親への報告に挙げる）
- マージ: **しない**（この再開では親が配布を起こすマージをしない。PR・CI・関門・手順 8 の記録まで）

スキルの版: 読み込んだのはキャッシュの 1.63.6（`SKILL.md` 1842 行）。リポジトリの main も 1.63.6。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/prepare-worktree.sh` — 出力の「次にすること」の直後に cruise の子の例外を 1 行、冒頭の説明（やらないこと・守る）
- `scripts/test-worktree-scripts.py` — その出力の観測・検査・変異
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行（手順 4 の「`prepare-worktree.sh` の出力の『次にすること』も」の言い回しを、出力が自分で言うようになったことに合わせる）
- `plugins/dev-loop/skills/cruise/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版（1.63.6 → 1.63.7。出力の誤った案内を直す修正なので patch）
- `.claude-plugin/marketplace.json` — 同上
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書く。変わる場合だけ）
- `docs/plans/issue-502.md` — この計画

触らない:

- `references/resume.md`（再開の周の `EnterWorktree` の記述。cruise の子の例外は `SKILL.md` 手順 4 と cruise §4 の 2 が既に指している）
- cruise `SKILL.md` の本文（§4 の 2 は既に「子も `EnterWorktree` を呼ばない」と書いている）
- スクリプトが cruise の子かどうかを自分で判定すること（シェルからは分からない。両方を出す）
- description（3 箇所。案内の 1 行は要約に現れない）

## 複製の数

「cruise の子は `EnterWorktree` を呼ばず worktree のパスを cwd にする」を述べる箇所: cruise `SKILL.md` §4 の 2、dev-loop `SKILL.md` 手順 4、
この周で足す `prepare-worktree.sh` の出力と冒頭の説明で計 4。**分けない理由**: 決まりの原本は cruise `SKILL.md` §4 の 2（手順 4 がそこを指す）。
スクリプトの出力は「原本を指す 1 行」に留め、条件を書き足さない。

## デプロイ経路

プラグインの版を上げるので、main へのマージが配布を起こす（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。
`docs/` も含む（計画ファイル・生成ブロック）ので Pages も再ビルドされる。**マージは親（cruise）の判断——この周はしない。**

## 受入基準（不変条件 × 経路）

不変条件:

- **I1 出力が cruise の子の例外を言う**——`prepare-worktree.sh` が作れた（rc=0）とき、「次にすること」の行の**直後の行**に、
  cruise から周を委ねられたサブエージェントは `EnterWorktree` を呼ばず、**作った worktree の絶対パス**を cwd にして作業する旨が出る
- **I2 通常の周の案内は変わらない**——「次にすること: EnterWorktree に path=<絶対パス> を渡して入る。」はそのまま出る
- **I3 出力のどこにも、例外を伴わない `EnterWorktree` の勧めが残らない**——スクリプトのすべての終了経路（0・1・2・3・5・6・7・`git worktree add` の失敗）を数える
- **I4 テストが守る**——`scripts/test-worktree-scripts.py` が I1 を観測し（「直後の行」まで見る——離れた行では偽）、例外の行を外す変異で赤になる。「守る」の行数と変異の数が 1 対 1
- **I5 記述が食い違わない**——スクリプト冒頭の説明（やらないこと・守る）・dev-loop `SKILL.md` 手順 4・cruise `SKILL.md` §4 の 2 が、出力と同じことを言う
- **I6 版と歯止め**——版 3 種類（`marketplace.json`・`plugin.json`・`SKILL.md` 2 本の 2 行）が 1.63.7 で揃い、`python3 scripts/check-all.py` が緑。PR 側の CI も緑

経路（不変条件を述べる／破りうる入口）:

| 入口 | I1 | I2 | I3 | I4 | I5 | I6 |
| --- | --- | --- | --- | --- | --- | --- |
| `prepare-worktree.sh` の rc=0 の出力（末尾の echo） | ○ | ○ | ○ | | | |
| `prepare-worktree.sh` の rc≠0 の出力（stderr・各 exit） | | | ○ | | | |
| `prepare-worktree.sh` 冒頭の説明 | | | | ○ | ○ | |
| `scripts/test-worktree-scripts.py`（観測・MUTATIONS・1 対 1 の数え） | ○ | ○ | | ○ | | |
| dev-loop `SKILL.md` 手順 4（528〜533 行付近） | | | | | ○ | ○ |
| cruise `SKILL.md` §4 の 2 | | | | | ○ | ○ |
| `references/resume.md`（`EnterWorktree` で入る・入り直す） | | | | | ○ | |
| 版 3 種類・`check-all.py`・PR の CI | | | | | | ○ |

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に × 1 パス目・2 パス目で 4 つの受け渡し（2 パス目が「該当なし」なら 2 つ）。

### 証明できるもの／できないもの

- I1〜I6 は、スクリプトを偽のリポジトリで走らせた出力・テスト・変異・`grep`・CI で証明できる。
- **受入基準ではないもの**: 出力を読んだサブエージェントが実際に `EnterWorktree` を呼ばなくなるか（モデルの振る舞い）。Eval を回さないと測れず、
  この周の受入基準に入れない（入れていない以上 BLOCKED でも未証明でもない）。PR コメントに名指しで残す。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——`SKILL.md` を触るので該当。`--check` で鮮度を見る。
- drawio の書き出し——該当なし（図を触らない）。

## 未解決の判断・確認待ち

- 無し（仕様の穴は無い。直し方は Issue の候補どおり）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/502-cruise-child-next-step`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-502`、
  起点コミット `94bcd42`、base の参照 `origin/main`（refs/remotes/origin/HEAD・取り直した）、base の SHA `94bcd423f3be1767106cd108e7649de033449940`
- 手順 4 の割り目: 不在のため訊かず続けた
- PR: #533
- Verifier 1 パス目: 通した（dev-loop:dev-loop-verifier・sonnet）。反証 0 件（所見 1: 行を離す変異は無い——I4 は満たす）。verifier.md を「170 行」と報告（`wc -l` は 169。Read の表示の末尾の空行と読む）
- `/code-review` 1 パス目: 通した（high）。指摘 6 件（直す 3・残課題 3）
- 1 パス目の指摘対応の起点の SHA: `3570066f1ec656e4f39b4cd85b434cc9807eb781`（1 パス目の関門に渡した時点の HEAD）
- 反証と差し戻し: Verifier 反証 0 件。`/code-review` の指摘 3 件を 1 パス目の指摘対応で直した（手順 4 への差し戻しなし）
- 範囲の拡張: なし（直した 3 件は `触る:` の 2 ファイルの中）
- 1 パス目の指摘対応: `82daf1a0221202501b205c1326d1b8f9b4d7eb64` まで（成果物の差分 2 ファイル・0 行ではない → 2 パス目を回す）
- 2 パス目の前の割り目: 不在のため訊かず続けた
- 2 パス目の経路の再導出: 新しい入口は無い（足したのはテストの観測 1 つと、出力の行の中の引用だけ）。新しい未証明・生成物の該当なし
- Verifier 2 パス目: 通した（sonnet）。反証 0 件（verifier.md 169 行と報告・`wc -l` と一致）
- `/code-review` 2 パス目: 通した（high）。指摘 6 件（直す 2・残課題 4）。**注**: 最初の 2 パス目の実行は受入基準の受け渡しより先に走り終えた（Skill が同期で完了）ので採らず、1 パス目の `/code-review` の体に 2 パス目の受け渡しを送って回し直した。受入基準なしの実行の指摘は「参考」として検査対象で渡した
- 2 パス目の指摘対応の起点（狭いパスの起点）: `82daf1a0221202501b205c1326d1b8f9b4d7eb64`／終点: `4b54329a17e9ab67b7c5c87f98f4c669ffca1db1`（CR2-1・CR2-2。著者の陽性対照: `%q` の版で空白＋日本語の観測が UnicodeDecodeError、現行で True）
- 狭いパス: 通した（dev-loop:dev-loop-verifier・sonnet。verifier.md 169 行で一致）。指摘 1 件（N1）。Verifier の変異 3 件: 赤 1（引用符を外す）・素通り 2（一重引用符のみで sed なし／二重引用符）——どちらも陽性対照あり（`it's`・`$HOME x` のパスで壊れる）。I1 の引用は bash 3.2・zsh・sh・dash で 8 種のパスが通った（bash 5 は未確認）
- 手順 7: マージしない（この再開では親が配布を起こすマージをしない）。PR #533 の CI と関門・手順 8 の記録まで
- 交絡: 実験なし（スクリプトの出力の観測とテストのみ）

## 既知の限界・決着済みの論点

- スクリプトは自分が cruise の子から呼ばれたかを判定しない。通常の案内と例外を並べて出す——決着: 採った。理由（2 パス目で訂正）: シェルから呼び出し元の種別は自分では分からない。呼び出し側に旗を渡させれば判定できる（CR2-5）が、この周は Issue の直し方の候補どおり並べて出す

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1 出力の指し先が「SKILL.md 手順 4」だけで、冒頭の説明（手順 4 と cruise §4）と食い違う・どの SKILL.md か分からない | 示せる——`prepare-worktree.sh` 275 行と 17 行の文面 | I5 | 直す（出力・冒頭とも「dev-loop の SKILL.md 手順 4 と cruise の SKILL.md『4. 周を回す』」に） |
| CR1-2 `cd ${PATH_ABS}` が引用されず、空白を含むパスで割れる | 示せる——`sp ace` の下で作り、出た `cd …` を `bash -c` に渡すと `cd: …/sp: No such file or directory`（rc=1） | I1（cwd にする指示が使えない） | 直す（`printf -v PATH_Q '%q'`。テストに空白パスの観測と変異「cd の例を素のパスで出す」・守る 1 行） |
| CR1-3 rc=3 の案内が `references/resume.md` を指し、そこは例外なしに `EnterWorktree` を勧める | 示せない——cruise §4 の 2（「resume.md が…書いていても…子も入らない」）と dev-loop 手順 4 が既に例外を包括している。出力自身は勧めない | 無し（I3 は出力の勧めを数える） | 残課題 |
| CR1-4 `cruise_exception_follows` が語の在否だけ見て、主語の反転を通す | 示せる——「cruise の子以外は EnterWorktree を呼ばない…」が `True` | I4 | 直す（「cruise から周を委ねられたサブエージェントは EnterWorktree を呼ばない」を続けて当てる。反転が `False` になることを確かめた） |
| CR1-5 rc=3 で見出し（stdout）と一覧（stderr）が割れる（既存のコード） | 示せる——stdout だけ見ると「  worktree:」「  ブランチ:」が中身なしで出る（rc=3） | 無し（この周の受入基準の外） | 残課題（cruise の台帳の候補として親に報告——振り分け: 直す） |
| CR2-1 `printf %q` が macOS の bash 3.2 で非 ASCII のパスを壊す（出力が不正な UTF-8・`cd` が通らない）。1 パス目の指摘対応の退行 | 示せる——`/bin/bash -c 'printf -v Q "%q" "/tmp/日本 語/x"'` が `$'/tmp/\346\227…'` の生バイト混じり（著者が実走） | I1 | 直す（一重引用符で囲み、中の `'` を `'\''` にする。`%q` を使わない） |
| CR2-2 引用の観測が ASCII の空白しか当てず、CR2-1 を捕まえない | 示せる——CR2-1 の版でテストは全合格 | I4 | 直す（観測の置き場所を空白＋日本語のパスにする） |
| CR2-3 変異の数の写し（CLAUDE.md 168・657 行の「変異 20 件」、テスト 198 行の「変異 20」）が 22 にずれた | 示せる——文面 | 無し | 残課題（cruise の台帳の候補として親に報告——振り分け: 直す） |
| CR2-4 出力の base の行が「SKILL.md 手順 4」と修飾なし | 示せる——281 行 | 無し（I5 は例外の記述） | 残課題 |
| CR2-5 決着の理由「cruise の子かはシェルから分からない」は不完全——`DEV_LOOP_BASE_REF` のように呼び出し側が旗を渡せる | 示せない（失敗ではなく設計の代案） | 無し | 残課題（理由を訂正: 判定は呼び出し側の旗で可能。この周は Issue の候補どおり「並べて出す」を採った。旗で出し分けるかは利用者の判断——台帳の候補として親に報告） |
| CR2-6 空白パスの観測が `observe()` の中で全変異ぶん繰り返される（約 3 秒） | 示せる——実行時間 | 無し | 残課題 |
| N1（狭いパス）`'` や `$` を含むパスのエスケープを守る観測が無い——sed を外す・二重引用符に落とす変異が素通り | 示せる——Verifier の変異 2 件が全テスト緑、`it's`・`$HOME x` のパスで `cd` が壊れる（陽性対照） | I4 寄り（観測の不足。I1 自体は現行で満たす） | 人間が決める（狭いパスの指摘。直さない） |
| CR1-6 同じ決まりがヘッダで 2 回（やらないこと・守る）——計画の複製の数 4 は 5 | 示せない（失敗ではなく重複） | 無し | 残課題 |

## 手順 8（経験の還元）

- この周の起票: 0 件（起票の承認は不在のため訊いていない。仕様の穴の確認の Issue は無い。台帳に足す候補 CR1-5・CR2-3（直す）・CR2-5・N1（利用者の判断）は台帳を書く親に報告し、この周では起票していない）

焼き戻す学び: `/code-review` を Skill で呼ぶと同期で完了することがあり、受け渡し（`SendMessage`）が届く前に走り終える。2 パス目の最初の実行はそうなったので採らず、1 パス目の体に送り直した。また同じ名前 `code-review` が並行する別の周の体に解決された（送った文面は誤配として断られた）。恒久資産への焼き戻しはこの周の範囲の外とし、親への報告に挙げる
