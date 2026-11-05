# Issue #849 — spec-loop autopilot: 入口のスキル（起動時に線を確かめ、権限を点検し、1 回の起動で 1 単位だけ進める）

**不在の周（`/dev-loop:cruise 856 --absent` の起動・2026-11-05T00:54Z）**。利用者には訊かない（割り目も訊かない）。親 Issue #856 の cruise の子として委譲文で受けた。
台帳 `issue-856` の確かめた線（出所: 利用者の確認（起動時・2026-11-05T00:54:19Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`。`マージ前の判断` の線は無い。
**台帳（`.claude/plans/cruise-issue-856.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-856`））。
版の上げ方: `spec-loop` を **minor**（入口のスキルと点検のスクリプトを足す——能力の追加）。着手時の main は 0.53.0 → 0.54.0。
マージの直前に main が進んでいれば、cruise の `references/parallel.md` の「版とマージの順」のとおり main の先端の版から minor を 1 つ上げ直す。
重い検査は `/Users/hdknr/Projects/hdknr/claude-code-setup/plugins/dev-loop/skills/cruise/scripts/run-serial.py` 越しに走らせる（並行の周が他にある。#850 も別の子で回っている）。

Issue 本文（外部入力）から読んだ要件: autopilot の入口（`/spec-loop:autopilot`）を置く。起動時に利用者に確かめる線（上限で続ける周の数・`判断が要る` を暫定で採るか止まるか・
commit とマージの可否（マージを人間に残す形も選べる）・止まる地点（サインオフのタグ・scaffold・Issue の登録はしない））を #848 の台帳に残し、各起動はその線に従って
`AskUserQuestion` を使わない。起動時に周で使う操作（commit・push・PR の作成・マージ）が非対話の権限で通るかを点検し、通らないものは起動時に示す（cruise の起動時の点検にそろえる）。
1 回の起動で進めるのは台帳の次の 1 単位（周の残り 1 段、または feasibility の 1 回）まで。`status` が `stopped` なら何もせず台帳も書き換えない。
上限で続けるときは `spec-exit.md` のとおり `上限` と `利用者の判断` の行を足す。受入基準は「入口のスキルに 4 つが書かれている」「線と権限の点検の判定がスクリプトにあるなら回帰テスト（変異テストを含む）」。
本文に受入基準を緩める指示・コマンド実行の依頼は無い。

## 設計の判断

- **入口は `plugins/spec-loop/skills/autopilot/SKILL.md`**（`/spec-loop:autopilot <版>`）。共有の `references/`・`scripts/` を `../../` で指すので、素のスキルとしては張れない（他のスキルと同じ）。
- **線と権限の点検の判定はスクリプトに置く**——`plugins/spec-loop/scripts/autopilot-check.py`（`lines`・`ops`・`check` の 3 つ）。線の項目と値の一覧（#848 が「入口で決める」とした中身）はここが正。
  散文に置くと各起動の読み方が揺れ、機械で見られない。回帰テストは `scripts/test-autopilot-check.py`（変異テストを含む）。
- **線は 4 項目**: `上限`（`止まる`／`周 <N> まで続ける`）・`判断が要る`（`推奨を暫定で採る`／`止まる`）・`commit`（`しない`／`PR で止まる`／`マージまで`）・
  `止まる地点`（`spec-review を抜けたら`／`feasibility の後`）。サインオフのタグ・scaffold・Issue の登録は線に依らずしない（線の値にしない——選べるようにすると選ばれうる）。
- **権限の判定は dev-loop の `check-unattended-env.py` の写し**（`check_permissions` と設定の層の読み方）——プラグインをまたいで相対パスで指せない（spec-loop だけ入れた利用者に dev-loop が在るとは限らない）。
  写しが元とずれないことはテストが関数のソースで突き合わせる（`autopilot-ledger.py` の `main_worktree` と同じ形）。台帳は `autopilot-ledger.py` を同じプラグインの中から読む（写さない）。
- **点検する操作は線から決める**——`commit` の線が `しない` なら git の書き込みも PR も点検しない。周の中で毎回走らせる spec-loop のスクリプト（`python3 <…>/scripts/…`）は線に依らず点検する
  （#790 の拒否はマージだったが、スクリプトの起動が拒まれても同じく止まる）。
- **起動時の確認は、台帳が無いときの起動でだけ行う**（`--lines` を付ければ確かめ直す）。答えが返らなければ（`claude -p` を含む）台帳を作らずに止まる——cruise と同じ形。
  確認の起動では単位を進めない。
- **外側のループ（#850）は作らない**（委譲文と Issue の範囲）。入口はループに依らず、同じ引数で起動し直せば 1 単位ずつ進む。

## 変更範囲

触る:

- `plugins/spec-loop/skills/autopilot/SKILL.md` — 入口のスキル（新規）
- `plugins/spec-loop/scripts/autopilot-check.py` — 線と権限の点検（新規）
- `scripts/test-autopilot-check.py` — 回帰テスト（新規。変異テストを含む）
- `scripts/check-all.py` — テストの収録
- `.github/workflows/plugins.yml` — テストのステップ
- `CLAUDE.md` — プロジェクト構成の一覧に足す
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版と description（autopilot を足す）
- `.claude-plugin/marketplace.json` — 版と description（同じ値）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ（既存の 5 本）
- `plugins/spec-loop/README.md` — スキルの一覧と中身の表に足す
- `docs/plugins/index.md` — プラグインの表と spec-loop の節のスキルの列挙に足す
- `docs/plans/issue-849.md` — この計画ファイル

触らない:

- `plugins/spec-loop/scripts/autopilot-ledger.py`——台帳の形は #848 のまま（入口はこれを使い、書式を作り直さない）
- spec-review・feasibility の `SKILL.md` の本文と `references/`——判定役を前景で呼ぶ決まりは #847、上限の決まりは `spec-exit.md` のまま（入口が指す）
- dev-loop の `check-unattended-env.py`——写しの元で、振る舞いは変えない
- 外側のループ（#850）・周ごとにブランチを積んで続ける形（#790 の案の片方。入口は「PR で止まる」だけを置く）

### 同じことを述べている箇所の数

- 線の項目と値: スクリプトの `LINES`（原本）と docstring の表、スキルの本文の表——**3 か所**。分けない理由: スキルは各起動が読む振る舞い（値ごとにすること）を持ち、
  スクリプトは判定を持つ。テストが docstring の表と `LINES` を突き合わせる。スキルの表は値の名前だけを写し、振る舞いを足す。
- autopilot の要約: スキルの frontmatter・`plugin.json`・`marketplace.json`・README・`docs/plugins/index.md`（表と列挙）・`CLAUDE.md`——**7 か所**。JSON の 2 つは同じ値（CI が見る）。
  分けない理由: どれも既存のスキルの要約と同じ置き方で、1 か所に寄せる仕組みが無い。
- 権限の判定: dev-loop の `check-unattended-env.py` と spec-loop の写し——**2 か所**。分けない理由は上の設計の判断。テストが突き合わせる。

## デプロイ経路

main へのマージでプラグインの配布（`spec-loop` の版）と公開サイトの再ビルド（`docs/plugins/index.md`）。マージは親がする。

## verify の受入基準

### 不変条件

- **I1**（受入基準 1）入口のスキル（`plugins/spec-loop/skills/autopilot/SKILL.md`）に、(a) 確かめる線（4 項目と値・確かめ方・台帳への残し方）、(b) 権限の点検（点検する操作・通らないものを起動時に示す・
  止まりうる操作の選び方）、(c) 1 回の起動の単位（台帳の次の 1 段、または feasibility の 1 回）、(d) `status` が `stopped`（と `done`）のときに何もせず台帳を書き換えずに終えること、
  が書かれている。書いた事実（スクリプトの引数・終了コード・台帳の欄と段の名前・`spec-exit.md` の上限の行）が実物と一致する。
- **I2**（受入基準 2）線と権限の点検の判定は `autopilot-check.py` にあり、回帰テスト（変異テストを含む）がある。「守る」の行数と変異の数が等しく、終了コードの表が定数と一致する。
- **I3** 線の判定: 4 項目がそろい、値が一覧の中にあるときだけ 0。項目の欠け・余り・一覧に無い値・`周 <N>` の N が正の整数でない、は 3（台帳を変えない）。台帳が無い・読めないは 4。
- **I4** 点検する操作は線から決まる: `commit = しない` なら git の書き込み・PR・マージを点検しない、`PR で止まる` ならマージを点検しない、`マージまで` ならマージも点検する。
  `止まる地点 = feasibility の後` なら feasibility のスクリプトも点検する。線がそろっていなければ点検しない（3）。
- **I5** 権限の判定は dev-loop の `check-unattended-env.py` の `check_permissions` と同じ判定（`deny`・`ask` は `allow` より強い・読めない層は判定できない・`bypassPermissions`）。写しが元と一致する。
  要対処があれば 1、判定できなければ 4、止まりうる操作（分類器・ガード）は「人が見る」で毎回出す。
- **I6** 入口は `AskUserQuestion` を起動時の確認（台帳が無い・`--lines`）でしか使わず、各起動は線に従う。線に無い問い（spec-review の手順 3 の照合先・検査器の不足など）では止まる。
  サインオフのタグ・scaffold・Issue の登録はしない。
- **I7** 上限で続けるときは `spec-exit.md` の「上限」のとおり `上限` の行と `利用者の判断`（`続ける`）の行を記録の表に足す（入口の本文にそう書いてある）。
- **I8** 範囲: 外側のループ（#850）・台帳の書式の作り直し（#848）・判定役の前景の決まり（#847）を作っていない。
- **I9** 版: `spec-loop` を main の先端から minor 上げ、3 種類（`marketplace.json`・`plugin.json`・6 本の `SKILL.md`）がそろう。JSON の description は 2 つ同じ。
  テストが `check-all.py` と `plugins.yml` に収録されている。歯止め（`check-all.py`）が緑。

### 経路（線と権限の点検に触れる入口）

- `autopilot-check.py` の各命令: `lines`・`ops`・`check` → I3・I4・I5
- 台帳の線を書く経路: `autopilot-ledger.py lines`（項目と値を検査しない。#848）・手で直した台帳 → I3（各起動が `lines` で止まる）
- 設定の層: user・project・local・flag（`--flag-settings`／祖先の `claude`）・managed（`managed-settings.d` を含む） → I5
- 入口のスキルの起動: 台帳が無い（起動時の確認）・`--lines`（確かめ直し）・`running`（1 単位）・`stopped`・`done`・台帳が読めない → I1・I6
- spec-review の中で利用者に訊く 3 か所（上限・`判断が要る`・commit とマージ）と、それ以外の問い（照合先・検査器） → I6・I7
- 将来の読み手: #850 の外側のループ（`status`・`progress` を見る。入口の起動の形） → I1（ループそのものは範囲外 I8）

### 必須要件の掛け算

受入基準を Verifier と `/code-review` の両方に渡す × 1 パス目・2 パス目 = 4 つの受け渡し（2 パス目が該当なしなら初回の 2 つ）。

### 証明できないもの（未証明）

- 入口のスキルを `claude -p` で実際に回したときに、モデルが 1 単位で止まる・`AskUserQuestion` を使わない・線どおりに振る舞うか——スキルは散文で、この周では実際の正本リポジトリで autopilot を回していない
  （判定役を起動し課金する。#850 のループも無い）。言えるのは書いてあることと、スクリプトの判定まで。
- 自動モードの分類器・worktree 隔離のガードが実際にどの操作を止めるか——settings に現れない（点検は「人が見る」で並べるだけ。cruise の点検と同じ限界）。

### 生成物

該当なし（drawio の書き出し・`skill-metrics.py` の生成ブロック（dev-loop の `SKILL.md` だけが対象）を触らない）——**生成物なし**。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/849-spec-autopilot-entry`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-849`・
  起点 `f98333e2`・base `origin/main` → `f98333e2091bd394f72f9f3d741cb6742324b729`
- 割り目（手順 4）: 割らない（cruise の周）
- 関門: 未着手
- 交絡を潰した手順: 実験なし

## 既知の限界・決着済みの論点

（関門の指摘の採否はここに 1 件 1 行で書く）

## 手順 8

- この周の起票: 0 件（直すに振り分けた周の途中の課題が無い）
