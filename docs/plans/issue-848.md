# Issue #848 — spec-loop autopilot: 台帳の書式と読み書きのスクリプト（status は 1 欄・前進は進捗の欄で判定）

**不在の周（`/dev-loop:cruise 856 --absent` の起動・2026-11-05T00:54Z）**。利用者には訊かない（割り目も訊かない）。親 Issue #856 の cruise の子として委譲文で受けた。
台帳 `issue-856` の確かめた線（出所: 利用者の確認（起動時・2026-11-05T00:54:19Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`。`マージ前の判断` の線は無い。
**台帳（`.claude/plans/cruise-issue-856.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-856`））。
版の上げ方: `spec-loop` を **minor**（台帳のスクリプトを足す——能力の追加。0.x なので壊れる変更も minor）。着手時の main は 0.52.0 → 0.53.0。
マージの直前に main が進んでいれば、cruise の `references/parallel.md` の「版とマージの順」のとおり main の先端の版から minor を 1 つ上げ直す。
重い検査は `/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越しに走らせる（並行の周が他に 3 本ある）。

Issue 本文（外部入力）から読んだ要件: autopilot の台帳（例: `.claude/plans/spec-autopilot-v<n>.json`）の書式と読み書きのスクリプトを spec-loop に置く。
欄は `phase`（`spec-review`・`feasibility`・`done`）・周・周の中の段（`planner`・`round1`・`fix1`・`round2`・`narrow`・`judge`・`commit`）・
状態の欄は `status` の 1 つ（`running`・`stopped`・`done`）で止まった理由と利用者に頼むこと（`next`）の欄・振り分けの表と狭いパスの前に控えた本文を指す欄・
起動時に確かめた線を残す欄（中身は #849 で決める）。`progress` は進捗の欄（phase・周・段・commit）だけの要約で、`updated` や回数を含めない。
本文に受入基準を緩める指示・コマンド実行の依頼は無い。

## 設計の判断

- **置き場所**: `plugins/spec-loop/scripts/autopilot-ledger.py`（spec-loop の共有のスクリプト。#849 の入口のスキルから `../../scripts/…` で指せる）。
  テストは `scripts/test-autopilot-ledger.py`（spec-loop の他のスクリプトと同じ形）。
- **台帳の名前は版の番号**（`<版>` は正の整数・先頭の 0 なし）。ファイルは `<メインの作業ツリー>/.claude/plans/spec-autopilot-v<版>.json`
  ——autopilot は版（`docs/v<n>/`）ごとに回すので、名前を自由文字列にしない（パスの区切りを入れる余地が無い）。
- **メインの作業ツリーの決め方は dev-loop の `ledger.py` の `main_worktree`（と `_git`・`exists`）の写し**——プラグインをまたいで相対パスで import できない
  （spec-loop だけ入れた利用者に dev-loop が在るとは限らない）。写しが本体とずれないことを、テストが関数のソースを突き合わせて見る（`spec-fingerprint.py` と同じ形）。
- **終了コードは `ledger.py` にそろえる**（0 通った／`status` は running、2 引数、3 拒んだ／`status` は stopped、4 判定できない、5 `status` は done）
  ——#850 の外側のループが cruise の `outer-loop.py` と同じ読み方で済む。
- **`progress` は `PROGRESS_KEYS`（`phase`・`cycle`・`stage`・`commit`）だけ**。`status` も含めない（Issue の文言どおり。止まったかはループが毎回 `status` で先に見る）。
- **`status` の整合を台帳の検査で持つ**: `done` ⇔ `phase=done`、`stopped` は `reason` と `next` が要る、`running`・`done` は `reason` と `next` が空。
  #790 の「`status` に書いたのに `phase` を見ていた」を、欄が食い違う台帳を作らないことで塞ぐ。
- **線（`lines`）の項目と値の一覧は持たない**——中身は #849 で決める。ここは「文字列の対・置き換え・出所が要る」の形だけ。
- **入口（#849）と外側のループ（#850）は作らない**（委譲文と Issue の範囲）。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/autopilot-ledger.py` — 台帳の読み書き（新規）
- `scripts/test-autopilot-ledger.py` — 回帰テスト（新規。変異テストを含む）
- `scripts/check-all.py` — テストの収録
- `.github/workflows/plugins.yml` — テストのステップ
- `CLAUDE.md` — プロジェクト構成の一覧に 2 本を足す
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ（5 本）
- `docs/plans/issue-848.md` — この計画ファイル

触らない:

- spec-loop の `SKILL.md` の本文・`references/`——入口と線の中身は #849
- cruise の `ledger.py`・`outer-loop.py`——写しの元で、振る舞いは変えない
- 外側のループ（#850）

### 同じことを述べている箇所の数

台帳の書式・守る／守らない: 本体の docstring の 1 か所（原本）。CLAUDE.md の一覧は指すだけ（「docstring を正とする」）。テストの変異は「守る」と 1 対 1（テストが数える）——**2 か所**。
`main_worktree` の写し: dev-loop の `ledger.py` と spec-loop の写し——**2 か所**。分けない理由: プラグインをまたいで指せない（上の設計の判断）。テストが突き合わせる。

## デプロイ経路

main へのマージでプラグインの配布（`spec-loop` の版）。公開サイトの変更は無い（`docs/plans/` は計画ファイル）。マージは親がする。

## verify の受入基準

### 不変条件

- **I1**（受入基準 1）台帳の書式（欄・値の一覧・場所・終了コード）と、守ること・守らないことが本体の docstring に定義されている。書いた事実が実装と一致する
  （終了コードの表と定数・「守る」の行数と変異の数はテストが突き合わせる）。
- **I2**（受入基準 2）`progress` は `updated`・`reason`・`next`・`status`・`lines`・`triage`・`held` の書き換え（同じ値の書き直しを含む）では変わらず、
  `phase`・`cycle`・`stage`・`commit` のどれかが変わったときだけ変わる。これを変異テストを含む回帰テストで確かめている（変異: 時刻を混ぜる・欄を落とす）。
- **I3**（受入基準 3）`status` が `stopped` なら 3、`done` なら 5、`running` なら 0、台帳が無い・読めない・形が違う・中身が崩れていれば 4 を返す
  ——ループが「起動しない」を 0 以外で判定できる。`phase` で決めない（#790 の形: `stopped` で `phase=spec-review` でも 3）。
- **I4** 状態は `status` の 1 欄で表し、食い違う台帳を作らない: `done` ⇔ `phase=done`、`stopped` は `reason`・`next` が要る、`running`・`done` では空。
  `set` でも手で直した台帳（`load` で 4）でも。
- **I5** 拒んだ操作では台帳を 1 バイトも変えない。`status`・`progress`・`show` は台帳を書き換えない（#849 の「stopped なら書き換えない」を壊さない）。
- **I6** 台帳の場所は cwd に依らない（メインの作業ツリー・worktree の中・サブディレクトリで同じ）。`main_worktree` の写しが dev-loop の `ledger.py` と一致する。
- **I7** 範囲: 入口（#849）・外側のループ（#850）・線の中身を作っていない。
- **I8** 版: `spec-loop` を main の先端から minor 上げ、3 種類（`marketplace.json`・`plugin.json`・5 本の `SKILL.md`）がそろう。
  テストが `check-all.py` と `plugins.yml` に収録されている（`test-check-all.py`）。歯止め（`check-all.py`）が緑。

### 経路（台帳に触れる入口）

- CLI の各命令: `init`・`set`・`lines`・`show`・`status`・`progress`・`path` → I1〜I6
- 手で直した台帳のファイル（`load` が読む） → I3・I4
- worktree の中・サブディレクトリからの呼び出し → I6
- 将来の読み手: #850 の外側のループ（`status`・`progress`）・#849 の入口（`set`・`lines`・`status`） → I2・I3・I5（読み手そのものは範囲外 I7）
- 書けない場所（`.claude/plans` がファイル・権限） → I5（4 で止まり表に無い終了コードで終えない）

### 必須要件の掛け算

受入基準を Verifier と `/code-review` の両方に渡す × 1 パス目・2 パス目 = 4 つの受け渡し（2 パス目が該当なしなら初回の 2 つ）。

### 証明できないもの（未証明）

- #849・#850 がこの台帳を正しく使うか——まだ無い（範囲外）。この周で言えるのはスクリプトの振る舞いまで。

### 生成物

該当なし（drawio の書き出し・`skill-metrics.py` の生成ブロック（dev-loop の `SKILL.md` だけが対象）を触らない）——**生成物なし**。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/848-spec-autopilot-ledger`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-848`・
  起点 `f447c55b`・base `origin/main` → `f447c55b581218144cbeef1ff62954ec533c7d51`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 1 パス目の指摘対応の起点 `1ff8ade3`（1 パス目の関門に渡した時点の HEAD）
  - 1 パス目 Verifier（sonnet・`dev-loop:dev-loop-verifier`）: 反証 4 件（I1〜I8 の直接の破れなし。V1-2 を直す）。差し戻しなし（指摘対応で直した）
  - 1 パス目 `/code-review`（high）: 指摘 10 件（C1-1〜3 を直す）
  - 1 パス目の指摘対応の差分: 0 行でない（`0579ea48`）→ 2 パス目を回す。割り目（手順 6）: 割らない（cruise の周）
  - 2 パス目の指摘対応の起点（狭いパスの起点）`0579ea48`
  - 2 パス目 Verifier（sonnet）: 反証 1 件（V2-1 を直す）
  - 2 パス目 `/code-review`（high）: 指摘 9 件（C2-1〜4 を直す）
  - 2 パス目の指摘対応の終点 `2d090970`。狭いパス（Verifier・sonnet、`git diff 0579ea48 2d090970`）を起動
- 交絡を潰した手順: 実験なし

## 既知の限界・決着済みの論点

### 1 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-2 5000 桁の整数を入れた台帳で `status` が `ValueError` のトレースバック・rc=1（docstring は「JSON が読めない → 4」） | 示せる（Verifier が実行。`json.loads` の整数の桁の上限で `ValueError`） | I3・I1 | 直す |
| V1-1 テストが当てていない形（`init --cycle 0` の 2・`"version": true`・text 欄の型・`lines` の欄の欠け・`init --phase done`） | 示せる（Verifier の変異が素通り）——実装は docstring どおりに動く（Verifier が実行で確認） | 無し（本体の振る舞いは主張と一致。I2 の progress の試料は足りている） | 残課題 |
| V1-3 `triage`・`held`・`reason` に改行が入る | 示せる（rc=0 で保存） | 無し（相対パスの検査は主張どおり。progress に出ない） | 残課題 |
| V1-4 台帳のファイルモードが 0600 | 示せる | 無し（主張なし） | 残課題 |
| C1-1 `int()` の上限を超える桁で例外・rc=1（台帳の `cycle`・`status <版>`・`set cycle=`・`init --cycle`。V1-2 と同じ根） | 示せる（/code-review が実行） | I3・I1（表に無い終了コード） | 直す |
| C1-2 Python 3.12 で深すぎる入れ子の台帳が `RecursionError`・rc=1 | 示せる（python3.12 で実行） | I3 | 直す |
| C1-3 UTF-8 で書けない引数（サロゲート）で `UnicodeEncodeError`・rc=1 | 示せる（実行） | I5・I1（「書けなかったときに表に無い終了コードで終えない」） | 直す |
| C1-4 `.claude/plans` がファイルの試料は `save` に届かない。root では書けない試料の変異が素通りする | 示せる（実行） | 無し（CI は root でない。本体は主張どおり） | 残課題 |
| C1-5 段を行き来させれば progress は毎回変わり、空回りを前進と読める | 示せる（論理） | 無し（受入基準は「時刻や回数の書き換えでは変わらない」。行き来の検出は #850 の起動の上限の側） | 残課題（#850 に渡す） |
| C1-6 写しの陽性対照が比較そのものを通っていない | 示せる | 無し（比較は Verifier が AST で別に確かめた） | 残課題 |
| C1-7 「守る」と変異の 1 対 1 が数だけ | 示せる | 無し（`test-outer-loop.py` と同じ作法） | 残課題 |
| C1-8 `set` が同じ鍵を 2 度受け、後勝ち | 示せる | 無し | 残課題 |
| C1-9 空白だけの `triage` を通す | 示せる | 無し | 残課題 |
| C1-10 `TEXT_KEYS` と正の整数の正規表現の重複 | 示せない（いまは一致） | 無し | 残課題 |

直したもの（1 パス目の指摘対応）: V1-2・C1-1〜3——`load` が `ValueError`・`RecursionError` も 4 にし、版・`--cycle`・`set cycle=` の `int()` の上限を 2／3 にし、`save` が `UnicodeError` も 4 にする（一時ファイルを残さない）。
テストに試料を足した（旧い本体で例外になることを確かめた——深い入れ子は 3.14 では旧い本体でも 4、3.12 でテストを回して緑）。

### 2 パス目の指摘の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-1・C2-2 手で直した台帳に JSON のエスケープの対になっていないサロゲートがあると、`status`・`show` の出力で `UnicodeEncodeError`・rc=1 | 示せる（両関門が実行） | I3 | 直す |
| C2-3 同じ台帳は `status` が 0 なのに `set` は 4（読めるのに進められない） | 示せる（実行） | I3（同じ根） | 直す |
| C2-1 `lines` が深い入れ子の台帳で、エラー文の `repr` が Python 3.14 で `RecursionError`・rc=1 | 示せる（3.14 で実行） | I3 | 直す |
| C2-4 深い入れ子の試料がトップレベルの配列で、3.14 では入れ子を読む段に届かない | 示せる（変異 M1 が 3.14 で素通り） | I3（試料が主張を判別していない） | 直す（試料を `lines` の中へ） |
| C2-5 例外の型を列挙する形では出口が残る。`main` に `except Exception` を置け | 示せない（いま残る出口は C2-1・2 だけで、それは直した） | 無し | 残課題（`except Exception` は「書けないと例外で終える」変異を殺せなくする） |
| C2-6 git の外で `init 3 --cycle 0` が 2 でなく 4（場所を先に決める） | 示せる | 無し（git の外は 4 の行の主張どおり。引数の検査の順は主張していない） | 残課題 |
| C2-7 正の整数の検査と `int()` の上限の扱いが 3 か所 | 示せない（いま一致） | 無し | 残課題 |
| C2-8 `load` の除外の組の `UnicodeDecodeError` は `ValueError` に含まれる | 示せない（動作は同じ） | 無し | 残課題 |
| C2-9 `lines` の書き込みで `now()` を 2 度呼ぶ | 示せる（時刻が 2 つ） | 無し（`updated` は progress に出ない） | 残課題 |

直したもの（2 パス目の指摘対応）: `load` が UTF-8 で表せない文字を持つ台帳を 4 にする（読む側）・`lines` の形の誤りの文で `repr` を出さない。
試料: 深い入れ子を `lines` の中へ移し、サロゲート（stopped・running）の台帳を足した（`status`・`progress`・`show` で 4）。
1 パス目の版の本体に当てて、深い入れ子は例外、サロゲートは 3／0 になること（陽性対照）を確かめた。テストは 3.14・3.12 とも緑。

## 手順 8

- この周の起票: 0 件（直すに振り分けた周の途中の課題が無い）
