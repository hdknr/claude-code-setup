# Issue #739（#746 と束ねた周）— run-serial.py の Ctrl-C の二重転送・閉じ行の 3 形・テストの試料と判定、cruise §4 の 4 の判断待ちの印

`run-serial.py`（cruise の重い検査の順番待ち）とその回帰テスト、cruise `SKILL.md` §4 の 4 を触る 2 件の Issue を、**1 周・1 PR** で扱う
（cruise の台帳のまとめ。代表 #739。`plugins/dev-loop/skills/cruise/references/grouping.md` の「まとめの周」。まとめは親が `ledger.py group` で記録済み）。
周の Issue は #739（worktree・ブランチの名前）。受入基準は 2 件のものを、Issue 番号を付けて下に並べる。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-11-01）。台帳 `issue-474` の確かめた線:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））。
加えて利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、`要確認` の Issue を立てる（#557 の形。この周が自分で立てる。
本文に「マージの前に直す」か「後続で直す」かを書く）。
**#743・#744・#745（確認の Issue）は利用者が承認して閉じた**（各 Issue のコメント「承認」）——推奨（直す）のとおりこの周で直す。
マージは親がする（この周は手順 6 の PR・CI の確認・関門 2 パスと狭いパス・手順 8 の件数の行まで）。台帳は書かない（親が書く）。
**実際に使われている台帳 `.claude/plans/cruise-issue-474.json` には書かない・触らない**（この周は台帳を使う変更をしない）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））。
版の上げ方: `dev-loop` を **patch**（不具合・記述の修正）。main の先端 1.73.0 → **1.73.1**（マージの直前に main が進んでいたら、その先端から patch で上げ直す）。

重い検査（`check-all.py`・`test-run-serial.py`）は順番待ち越しに走らせる（`references/parallel.md`）。
**使う `run-serial.py` は origin/main（`7009fd1e`）の写し**（scratchpad の `i739-rs/run-serial.py`）——メインの作業ツリーの main は古く（`4a8c7e8a`）まだ持っていない。
この周が直す本体（worktree の中）を順番待ちに使わないのは、直している最中のものに枠を任せないため。

## 変更範囲

触る:

- `plugins/dev-loop/skills/cruise/scripts/run-serial.py` — #739（SIGINT をコマンドに渡さない・閉じ行の 3 形・行の分け方）・docstring の守る／守らない
- `scripts/test-run-serial.py` — #739（SIGINT の回数の観測・試料（#743 の 3 形、#745 の 7 形と BOM）・変異・判定の失敗で数える）
- `plugins/dev-loop/skills/cruise/SKILL.md` — #746（§4 の 4 のコマンド）・版の行
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の行だけ
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-739.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/cruise/references/parallel.md`・`plugins/dev-loop/skills/dev-loop/references/ledger.md`・cruise `SKILL.md` §4 の 1——`単独:` の項を残す決まりは既にある（#746 はそれに §4 の 4 を合わせるだけ）
- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` の `note="利用者の判断待ち: <問い>"`——足したばかりの行（`blocked`）に書くもので、`単独:` の項を持つ前の行
- `check-unattended-env.py`・`scripts/test-check-unattended-env.py`——並行の周 #736/#749 が触る
- 公開ページ・`CLAUDE.md`——`run-serial.py` の守る／守らないは docstring を正とすると書いてあり、列挙を持たない
- SIGTERM・SIGHUP をプロセスグループ全体に送ったときの二重——Issue の項目は SIGINT だけ（下の「既知の限界」）

### 同じことを述べている箇所の数

- SIGINT の扱い: `run-serial.py` の docstring（守る 1 行・守らない）と `run()` の 2 か所。`parallel.md`・公開ページは docstring を指すだけ——**2 か所**（同じファイル）。
- 閉じ行・開き行の規則: docstring の「枠」の箇条・守る・`closes()` と `declared_lines()` の docstring——**同じファイルの 4 か所**。分けない（1 ファイル）。
- 判断待ちの印と `単独:` の項: cruise §4 の 1・§4 の 4・`parallel.md`・`ledger.md`——**4 か所**。この周は §4 の 4 だけを他の 3 か所に合わせる（分けない理由: 3 か所は既に同じことを言っており、食い違っているのが 1 か所）。

## 乗るデプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。
マージは親がする。

## 周の在り処

- ブランチ: `issue/739-run-serial-fence-sigint`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-739`
- 起点: `7009fd1e`（origin/main。`prepare-worktree.sh` の出力）
- base: 参照 `origin/main` → `7009fd1eadd5da6e5d38fe3e263dcd18cca13748`

## verify の受入基準

### #739（`run-serial.py`・`test-run-serial.py`）

不変条件と、それを破りうる経路:

- **S1 SIGINT はコマンドに 1 度だけ届く。** 経路: 端末の Ctrl-C（前面のプロセスグループ全体）・`os.killpg(<ラッパーのグループ>, SIGINT)`・
  ラッパーにだけ送った SIGINT（`kill -INT <ラッパー>`——コマンドには届かない。守らないに書く）。
  確かめ方: ラッパーを独立のグループで起こし、`killpg` の後でコマンドが数えた SIGINT が 1 回であること。転送が 2 度目を足す形は、コマンドへの直接の SIGINT と
  ラッパーへの SIGINT を時間をずらして送る観測で見る（同時だと標準のシグナルは 1 つに重なり、壊した本体でも 1 回に見えうる）。
- **S2 ラッパーが SIGINT・SIGTERM・SIGHUP のどれを受けても、コマンドが終わるまで枠を離さない**（既存の観測のまま）。SIGTERM・SIGHUP はコマンドに渡す（既存）。
- **F1 閉じ行は CommonMark の閉じ行だけ**: 字下げは空白 3 つまで（タブの字下げでは閉じない）・開いた印と同じ文字を同じ数以上・後ろは空白とタブだけ
  （全角の空白・`\x0b` などがあれば閉じない）。経路: `slots_from` に渡る `.claude/dev-loop.md` の本文（メインの作業ツリー）。
  行は改行（`\n`・`\r\n`・`\r`）でだけ分ける——`str.splitlines()` は `\x0b`・`\x0c`・` ` などでも分けるので、`\x0b` の後ろが閉じ行に見える。
- **F2 開き行**: バッククォートの印の後ろ（情報文字列）にバッククォートがある行はコードブロックを始めない（`` ```a`b ``）。空白 4 つの字下げ・行の途中・
  コメントの中の印では始めない（既存の動き）。`~~~` でも始める（既存）。
- **T1 試料**: #743 の 3 形（タブの字下げの閉じ行・後ろに全角の空白／`\x0b` のある閉じ行・バッククォートを含む情報文字列）、#745 の 7 形（空白 3 つの閉じ行・同じ数の閉じ行・
  後ろに文字のある閉じ行・空白 4 つの開き・行の途中の開き・`~~~` の開き・コメントの中の開き）と BOM を、`slots_from` に直に当てる試料に持つ。
- **T2 変異を見つけたかは、判定（`check`）が 1 つでも落ちたことで数える**——出力（観測の辞書）が正しい本体と違うだけでは数えない。
- **T3 各試料に、それで殺せる変異があり、変異の数と「守る」の行数が等しい**（テスト自身が数える既存の歯止め）。新しい変異は、それぞれ陽性対照（変異の前に緑・変異で赤）を取る。

### #746（cruise `SKILL.md` §4 の 4）

- **N1 §4 の 4 の文字どおりのコマンドが、`note` に `単独: <理由>` の項があれば後ろに残す形になっている**（`note="利用者の判断待ち: <何を判断するか>[; 単独: <理由>]"`）。
  経路（同じ決まりを述べる箇所）: §4 の 1・`references/parallel.md` の「単独で回す周」・`../dev-loop/references/ledger.md`——**4 か所が食い違わない**（印は先頭、`単独:` は後ろ、区切りは `; `）。
- **N2 起動時の点検（`check-unattended-env.py`）が読む形のまま**——`note` の先頭が `利用者の判断待ち:` で始まる（先頭に置く）。

### 共通

- **V1 版**: `marketplace.json`・`plugin.json`・`SKILL.md` 2 本のバナー（2 行）が同じ値で、main の先端より上。
- **V2 歯止め**: `check-all.py` が順番待ち越しに緑。PR 側の CI が緑（`gh pr checks`）。
- **V3 実環境**: テストはテンポラリだけを対象にする（`assert_not_real_repo`）。実際の台帳・メインの作業ツリーの `.git/dev-loop-serial` に触らない
  （`run-serial.py` の写しを順番待ちに使うのは、メインの作業ツリーの枠を正しく使うため——それ以外で触らない）。

### 証明できないもの（未証明）

- **端末の Ctrl-C そのもの**（tty が前面のグループに送る SIGINT）——この環境に端末が無い。`os.killpg` で同じ配り方（グループ全体）を作って見る。
  違いは送り手だけで、受け取る側（ラッパーとコマンド）の振る舞いは同じ——とは言えるが、実際の端末では確かめていない。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——`SKILL.md` を触るので該当。`skill-metrics.py --check` が緑であること。
- 図の書き出し: 該当なし（drawio を触らない）。

### 必須要件の掛け算

- 受入基準（#739 と #746 の両方）× 2 つの関門 × 2 パス = 4 つの受け渡し（2 パス目が該当なしなら 2）。狭いパスにも両方の受入基準を渡す。

## 未解決の判断・確認待ち

- なし（#743・#744・#745 は承認済み）。

## 関門の進捗（再開点）

- 手順 4: 未
- 手順 5 Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 1 パス目の指摘対応の起点: 未
- 手順 5 当て直し（2 パス目）: 未
- `/code-review` 2 パス目: 未
- 狭いパス: 未
- 反証と差し戻し: 0 件
- 交絡を潰した手順: 未
- 割り目: 不在のため訊かず続ける（`references/absent-lines.md` の「訊く場面」）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| SIGINT の直し方 | **ラッパーは SIGINT をコマンドに渡さない（受けても枠を持ったまま待つ）** を採った。コマンドを別のプロセスグループに置く形は採らなかった | 別のグループにすると、グループ全体への SIGKILL でコマンドが残り（ラッパーだけ死ぬ）、端末の前面を渡さないとコマンドが端末を読めない（SIGTTIN）。SIGINT は端末の Ctrl-C としてグループ全体に届くのがふつうで、シェルも前面のコマンドを待つあいだ SIGINT を自分で処理しない。代わりに、ラッパーにだけ送った SIGINT はコマンドに届かない——守らないに書く |
| SIGTERM・SIGHUP のグループ全体への送り | この周では変えない（転送のまま。グループ全体に送れば 2 度届く） | Issue の項目は SIGINT だけ。SIGTERM はラッパーの pid だけに送る使い方（監督するプロセス）がふつうで、渡さないと止まらなくなる。守らないに書く |
