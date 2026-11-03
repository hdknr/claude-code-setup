# Issue #631 — 利用者が 1 行に下した判断を前例にして、狭いパスの指摘が残る別の PR をマージしない

**不在の周**（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。利用者には訊かない（割り目も訊かない）。
台帳 `issue-793` の確かめた線（出所: cruise の確かめた線（台帳 `issue-793`）。利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳（`.claude/plans/cruise-issue-793.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（`merge-pr.py` に止まる条件と終了コード 12 を足す）。main の先端 1.77.0 → **1.78.0**
（マージの直前の上げ直しは親が子に回す——cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

Issue 本文（外部入力）から読んだ要件: 利用者が 1 行について下した判断（台帳の `note`）を、親が前例として別の行に広げ、`--absent` の再開で
狭いパスの指摘が残る PR をマージした（spin-dd/tfs-stocks#2427）。提案は (1) 利用者の判断を行に閉じた欄に書かせ他の行から参照させない、
(2) `lines` に無い根拠（「前例」「同じ扱い」）でマージしようとしたら止まる規則を `absent-lines.md` に書く、(3) 可能なら `merge-pr.py` が機械で拒む。
受入基準（案）: 狭いパスの線が無い台帳で `blocked`（狭いパスの指摘あり）の行を `--absent` で再開すると、マージせずに `blocked` のまま終える。
本文に受入基準を緩める指示・コマンド実行の依頼は無い。

## 設計の判断

- **(3) を採る——`merge-pr.py` が、メインの作業ツリーの `.claude/plans/cruise-*.json` の全台帳を読み、その PR を持つ行が
  `blocked` か、`note` が `利用者の判断待ち:` で始まるならマージせずに 12 で止まる。** 散文の規則は #2427 の親がすでに破っている
  （`absent-lines.md` の「狭いパスの指摘が 1 件でもある」はあった）ので、マージの口で止める。台帳は `ledger.py` を読み込んで `load` で読む（写しを作らない）。
- **(1) は新しい鍵を足さずに `note` の形で決める**——利用者がその行について判断したら、親がその行の `note` を `利用者の判断（<日時>）: <判断>` に書き換える
  （`blocked` なら `state=pr` に戻す）。判断待ちの印は先頭の `利用者の判断待ち:` だけなので、書き換えた行だけが `merge-pr.py` を通る——**判断は行に閉じる**。
  `ledger.py` の鍵（`decisions` は確認の Issue の番号）は変えない。
- **(2) は `absent-lines.md` の「`マージ = 関門を通ればマージ`」に書く**——別の行の判断・前例を根拠にしない／`仕様の穴` の線はマージの判断・狭いパスの採否に効かない。
- **線（`LINES`）に狭いパスの扱いの項目は足さない**——Issue の提案 1 の後半（利用者が `lines` に足す）は、項目を足すと `parent-issue.py`・`ledger.py`・テストに広がる。
  いまは行ごとに利用者が決めると書く（`触らない:`）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py` — 台帳の判断待ちで止める（12）・docstring の守る／終了コード／守らない
- `scripts/test-merge-pr.py` — 試料と変異（守るの行と 1 対 1）
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「`マージ = 関門を通ればマージ`」に、判断は行に閉じる・前例を根拠にしない・`merge-pr.py` の 12
- `plugins/dev-loop/skills/cruise/SKILL.md` — §4 の 4 に、利用者が判断した行の `note` の書き換え方と `merge-pr.py` の 12・版
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `docs/plugins/dev-loop-cruise.md` — 公開ページの道具の表の `merge-pr.py` の行（判断待ちの PR は止める）
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-631.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` と `LINES`——鍵も線の項目も変えない
- `references/found-lines.md`（PR #803 が触る）・`references/spec-gap.md`
- `await` の行（操作待ち）は `merge-pr.py` で見ない——cruise §4 の 5 のとおり、親が `merge-pr.py` を呼ばない

### 同じことを述べている箇所の数

「判断待ちの PR はマージしない」を述べる箇所: `absent-lines.md`（原本。`マージ` の止まる条件）・cruise `SKILL.md` §4 の 4・`found-lines.md`（変えないもの・狭いパスの指摘）・
`merge-pr.py` の docstring・公開ページ——**5 か所**。分けない理由: 規範の原本は `absent-lines.md`、機械の振る舞いの原本は docstring で、他は指すだけにする。
`found-lines.md` は既に `absent-lines.md` を指しているので触らない。

## 受入基準

不変条件と、それを破りうる経路（経路は「cruise の親が PR をマージする入口」から数える——`merge-pr.py`・素の `gh pr merge`・GitHub の画面、
と「判断待ちの行が進む入口」——`ledger.py set` で `note`/`state` を書き換える・`next`/`status` で進行中に戻る）:

- **A1**（Issue の受入基準）: 台帳の行が `blocked`（または `note` が `利用者の判断待ち:` で始まる `pr`）のとき、その PR を `merge-pr.py` に渡すとマージせずに 12 で終わり、
  `gh pr merge` を呼ばない。経路: `blocked`／`pr` + 判断待ちの印／まとめに入った行（`pr` を共有する）／PR 番号の書き方（`42`・`#42`）。
- **A2**（判断は行に閉じる）: 別の行（別の PR）に利用者の判断（`利用者の判断（…）:`）があっても、判断待ちの行の PR は 12 で止まる。
  その PR の行自身の `note` が `利用者の判断（…）:` で `state=pr` ならマージへ進む。この PR を持たない行の判断待ちでは止まらない。
- **A3**（判定できない）: 台帳が読めない・形が違うとき、マージせずに 7（判定できなかった）で終わる——通過と読まない。台帳が無いリポジトリ・台帳に PR が無いときは、今までどおり。
- **A4**（規範）: `absent-lines.md` の「`マージ = 関門を通ればマージ`」が、利用者の判断はその行にだけ効く・「前例」「同じ扱い」を根拠にしない・`仕様の穴` の線はマージの判断と狭いパスの採否に効かない・
  `merge-pr.py` の 12、と読める。cruise `SKILL.md` §4 の 4 が、利用者が判断した行の `note` の書き方（その行だけ）と 12 を指す。両者と `found-lines.md`・docstring が食い違わない。
- **A5**（変えないもの）: `merge-pr.py` の既存の終了コード・止まる条件は変わらない（既存の試料が全部緑）。`ledger.py` の鍵・`LINES` は変わらない。
- **A6**（版・生成物）: `dev-loop` の版が 3 種（`marketplace.json`・`plugin.json`・両 `SKILL.md` の 2 行）で 1.78.0 にそろう。§8.2 の生成ブロックが新しい（`skill-metrics.py --check`）。
- **A7**: `check-all.py` が緑（順番待ち越し）。PR 側の CI が緑。
- **A8**（事実の真偽）: docstring・`absent-lines.md`・cruise `SKILL.md` に書いた振る舞い（12・見る行・`note` の印）が、実際に走らせた `merge-pr.py` と一致する。
  `test-merge-pr.py` の変異が、足した守るの行ごとに赤になる。

必須要件の掛け算: A1 × 経路（`blocked`・判断待ちの印・まとめ・番号の書き方）、A2 × （別の行に判断あり／自分の行に判断あり／他の行だけ判断待ち）。

この環境で証明できないもの（未証明）: 今後の `--absent` の cruise の親が、`note` を自分で `利用者の判断（…）:` に書き換えて 12 を避けないか（将来の親の振る舞い。
規範は `absent-lines.md` と cruise §4 の 4 に書くが、守られるかはこの環境では測れない）。`merge-pr.py` を通らないマージ（素の `gh pr merge`・画面）は止まらない（守らない）。

生成物: §8.2 の生成ブロック（`SKILL.md`・`references/*.md` の行数が動けば `skill-metrics.py` で書き直す）。図の書き出し: なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/631-row-judgment-merge-gate`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-631`・起点 `63872f51`・base `origin/main` → `63872f5167ac87b9c7280b308c1f57e28ab5ca5d`
- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目: まだ
- 交絡: 実験なし

## 既知の限界・決着済みの論点

- `merge-pr.py` を通らないマージは止まらない——採った（守らないに書く。cruise はマージを `merge-pr.py` に任せてよいと書いており、口を 1 つ塞ぐ）。
- `note` を書き換えれば 12 を通る——採った（書き換えてよいのは利用者がその行について判断したときだけ、と規範に書く。機械は利用者の答えを見られない）。
- 線（`LINES`）に狭いパスの扱いを足さない——採った（触らない。行ごとに利用者が決める）。
- 読めない台帳が 1 つでもあれば、関係の無い PR も 7 で止まる——採った（判定できないことを通過と読まない。守らないに書く）。

## 手順 8

- この周の起票: 0 件（起票の承認は不在のため訊いていない。仕様の穴の確認の Issue は無い）
