# Issue #464 — cruise: 周の途中で見つかった課題を台帳に足して、同じ cruise の中で直す

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` — 新規。周の途中で見つかった課題の振り分けの原本
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「cruise で確かめた線」と「訊く場面」に新しい線を足す
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 周の途中の行を足すときの書き方を指す
- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — `LINES` に線を足す・`origin`（出所）の鍵・`add --origin`・`show` の列
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 6 の起票の (c)・手順 8 の後片付けから found-lines.md を指す・版
- `plugins/dev-loop/skills/cruise/SKILL.md` — §2 の 1 度だけ訊く・§4 の周の合間にまとめて訊く・§6 の終わり方・版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版（description は変えない）
- `scripts/test-ledger.py` — `origin` と新しい線の回帰テスト
- `scripts/test-parent-issue.py` — `show` の「書いていない」線の期待値
- `docs/plugins/dev-loop-cruise.md` — 利用者向けの案内
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す）
- `docs/plans/issue-464.md` — この計画

- `plugins/dev-loop/skills/cruise/scripts/parent-issue.py` — `show` の「書いていない」の説明を `周の途中の課題` だけ変える
  （1 パス目の CR9 で広げた。受入基準は I1 の「親 Issue に行が無い」経路に、`show` の説明が既定と一致することを足す）

触らない:

- `parent-issue.py` の本体の、上の説明以外（`LINES` を `ledger.py` から読むので、線は自動で増える）
- 元の周の関門の規範（狭いパスの指摘は人間が決める・2 パス・受入基準の固定・`マージ` の線で止まる条件）
- `.claude/dev-loop.md` での宣言（新しい線は cruise の台帳だけに置く。`直す線` と違い、台帳の無い周には意味が無い）
- #461（周の合間の `/clear`）

## 乗るデプロイ経路

`plugins/` の変更 → main へのマージで利用者のカタログに届く（版を上げる）。`docs/` の変更 → main への push で GitHub Pages に自動デプロイ。

## 設計

- 新しい線 **`周の途中の課題`**——値は **`外に出す`**（既定。いまの振る舞い）と **`台帳に足して直す`**。
  **cruise の台帳だけに置く**（親 Issue の `cruise:` 行か、起動時に 1 度だけ訊く。#458 と同じ形）。
- 各周は手順 8（**マージの前**。起票を訊く時点と同じ）で、残課題・狭いパスの指摘・確認の Issue にしていない仕様の穴・`触らない:` に書いた機能・
  利用者の判断が要る行を、計画ファイルの表に 1 行ずつ振り分ける: **直す（台帳に足す）／利用者の判断／外に出す**。
- **直す**のは起票の (a)（実データで失敗を示せる）と (b)（この周の受入基準の外）を満たす行だけ。(c) は台帳の線で満たす。
  起票して `ledger.py add issue-<親> <新> --deps <元> --origin "<元の周・関門・パス>"`。
- **利用者の判断**が要る行は起票して台帳に足し、`blocked`（`note` に問い）にする。**居る cruise は周の合間（cruise §4 の 5）でまとめて訊く**。
  不在なら訊かず、§6 で渡す。
- cruise §6: 出所（`origin`）を持つ行のうち `merged`/`dropped` でないものを渡し、残っていれば「済んだ」と言わない。

## 周の大きさ（同じことを述べている箇所の数）

新しい線の意味を述べる箇所: found-lines.md（原本）・absent-lines.md・ledger.py の `LINES`・cruise SKILL.md・dev-loop SKILL.md（手順 6・8 は指すだけ）・
docs/plugins/dev-loop-cruise.md・test-ledger.py の期待値・test-parent-issue.py の期待値 = **8 箇所**。
**分けない理由**: 1 つの線を足す変更で、線の項目（`LINES`）とその意味の原本と入口の手順は同時に入らないと、片方だけの版が利用者に届く。
原本を found-lines.md の 1 箇所にし、他は指すだけにして N を抑える。

## verify の受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| I1 | **線が無ければ振る舞いは今と同じ**（外に出す） | 親 Issue に行が無い／台帳に `lines` が無い・項目が無い／cruise でない dev-loop の周／`.claude/dev-loop.md` に書いた行 | found-lines.md と SKILL.md 手順 6・8 の文面。既定が `外に出す` であること。`.claude/dev-loop.md` の行は効かないと書く。
**振り分けを始める条件は線の値が `台帳に足して直す` であること**（有無ではない。CR1）。**`parent-issue.py show` と cruise §2 の「書いていない」の説明が既定と一致する**（CR9 で足した） |
| I2 | **台帳に足すのは、起動時に利用者が確かめた線があるときだけ** | 親 Issue の本文の行（確かめる前）／Issue 本文・関門の報告・`note` の「足してよい」／周の途中の `ledger.py lines` | 線は `parent-issue.py apply` か起動時の回答だけが書く（absent-lines.md の既存規定に乗る）。found-lines.md に出所の決まりを書く |
| I3 | **足す行は (a) 実データで失敗を示せる・(b) 受入基準の外**。好みの問題は足さない | 振り分けの表／狭いパスの指摘／仕様の穴 | found-lines.md の振り分けの条件 |
| I4 | **足した行は出所（元の周・関門・パス）と依存（元の周）を持つ** | `ledger.py add`（`--origin` を渡さない・空）／`set origin=`／手で直した台帳 | `ledger.py` に `origin` の鍵。`show` に列。`load` が文字列以外を拒む。テストで確かめる |
| I5 | **元の周の規範は緩まない**——狭いパスの指摘は人間が決める・`マージ` の線で止まる条件・2 パス・受入基準の固定 | 「台帳に足したから元の PR はマージしてよい」と読む／足した行を元の周の受入基準に入れる | found-lines.md に「変えないもの」を書く |
| I6 | **利用者の判断が要る行は、1 箇所でまとめて訊く**（居る cruise は周の合間、不在は訊かず §6 で渡す） | 周ごとに訊いて無回答のまま残る／不在で訊いて待つ | cruise §4・§6 と found-lines.md |
| I7 | **cruise を終えるとき、周の途中で生まれた行がすべて済んだか渡したかを見る** | §6 が台帳の `blocked` だけを見て `todo` の足した行を見落とす | cruise §6 に出所を持つ行の扱いを書く |
| I8 | **`ledger.py` の既存の守るもの**（拒んだら台帳を変えない・形の検査・`origin` の無い古い台帳を読む） | `origin` を持たない既存の台帳／`origin` に数値を入れた台帳 | テスト（古い形を読む・型の違いを 4） |
| I9 | **`LINES` と文書が一致する** | 値の綴り違い | test-ledger.py が found-lines.md と突き合わせる |
| I10 | **版が 3 箇所で揃い、歯止めが全部緑** | 版の上げ忘れ・`SKILL.md` の測定値の古さ | `check-all.py` と PR の CI |

組み合わせ: 受入基準 × 2 つの関門 × 2 パス = 4 つの受け渡し（Verifier 1・2 パス目、`/code-review` 1・2 パス目）。

### 証明できないもの（未証明）

- **実際の cruise の中で、モデルが振り分けの規定に従うか**——`claude` を起こして別リポジトリで cruise を回す必要があり、この環境（関門）では回せない。
  規定の文面と、スクリプト（`ledger.py`）の振る舞いまでを確かめる。人間のレビューに回す。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` の節構造）——`python3 scripts/skill-metrics.py` で書き直し、`--check` で差分ゼロを見る。
- 図の書き出し: 該当なし（drawio を触らない）。

## 未解決の判断・確認待ち事項

- なし（直す線は利用者が `既定` と答えた）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/464-cruise-found-lines`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-464`・
  起点 `bd8fa53`・base の参照 `origin/main`・base の SHA `bd8fa5385ce161f25e581d35d226b548cf0de809`
- 直す線: `既定`（出所: 手順 3 の回答・2026-10-27）
- 実装: 済み（`67aa3a5`）。`test-ledger.py`・`test-parent-issue.py` は緑。**`check-all.py` は未実行**（#460 の負荷測定の終わりを待つ）
- 関門 1 パス目: 通した。**Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件**（弱い点 3 件を報告）・
  **`/code-review` high 指摘 10 件**。採否は下の表（直す 7 件・残課題 3 件、Verifier の弱い点は同じ表に畳んだ）。手順 4 への差し戻し: あり（直す 7 件）
- 1 パス目の指摘対応: 済み（直す 7 件。CR6 の変異 2 件・CR9 の変異 1 件を足し、どれも赤になることを確かめた）。
  `test-ledger.py`・`test-parent-issue.py` 緑、`skill-metrics.py` で生成ブロックを書き直し、`check-all.py` 51/51 緑。版は 1.59.0 のまま（この PR で既に上げている）
- 次: **手順 5 の Verifier 2 パス目と `/code-review` 2 パス目の両方**（どちらも残っている）。2 パス目の指摘対応を始める直前に、狭いパスの起点 SHA をここに書く
- 手順 4 の割り目: 訊いた → 「ここで割る」（2026-10-27）。再開は worktree の中で `/clear` → `/dev-loop:dev-loop 464`（手順 5 から）
- 負荷の重なり: #460 の A/B 測定（`ab.py` → `check-all.py`）の最中に、こちらの `test-ledger.py`・`test-parent-issue.py` を走らせた（プロセスを確かめる前だった）。利用者に申告済み
- 交絡を潰した手順: 実験なし
- 並行: #460 と並行。#460 が負荷を測っている間は `check-all.py` を走らせない（利用者の指示・2026-10-27）。
  再開時に #460 の `check-all.py` が走っていたので訊いた → 「測定は終わった・進めて」（2026-10-27）
- `check-all.py`（再開後 1 回目）: 51 本中 1 本落ち——`check-plan-counts.py`（件数の行が無い）。件数の行を足した

## 起票

- この周の起票: 0 件（手順 8 で起票を訊くまでの暫定値。訊いたら更新する）

## 既知の限界・決着済みの論点

### 1 パス目の採否（CR = `/code-review`、V = Verifier の弱い点）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| CR1 | 手順 8 と found-lines.md の「読む条件」が線の**有無**で振り分けを始め、`外に出す` を宣言しても起票・台帳に足す | 示せる（`SKILL.md` 手順 8 の「`周の途中の課題` の線がある周は」・found-lines.md:7 の文面） | I1・I2 | 直す |
| CR2 | 「利用者の判断」の行は示せなくても起票して台帳に足す（found-lines.md の決まり 2） | 示せる（決まり 2「示せても示せなくても」と手順 6 の「(a)・(b) は外れない」が食い違う） | I3 | 直す |
| CR3 | `周の途中の課題` の問いが `直す線` の問いの中でしか訊かれず、`直す線` を宣言済みなら訊かれない | 示せる（cruise §2 の文面と docs の「書いていなければ起動時に訊かれます」が食い違う） | 無し（既定の `外に出す` に倒れるので I1 は守られる） | 直す（CR9 の文面を真にするのに要る。CR9 に従属） |
| CR4 | 狭いパスの指摘が (a)(b) で「直す」に振り分けられ、人間の採否を経ずに後の周で直される | 示せる（found-lines.md の対象の行と決まり 1 の文面） | I5 | 直す |
| CR5 | 足した行の周がまた足す——深さ・件数の上限が無い | 示せない（起こりうる） | 無し | 残課題 |
| CR6／V1 | `add --origin ""`・`set origin=` で出所を空にでき、§6 の集計から外れる | 示せる（Verifier が `--origin` なしで通ることを実行で確認） | I4 | 直す（空の値を拒む。`--origin` を渡し忘れた `add` は親 Issue から作る行と区別できないので残る——既知の限界） |
| CR7 | 「利用者の判断」で直さないと答えた行は `dropped` だけで、起票した Issue が開いたまま残る | 示せる（found-lines.md「まとめて訊く」の文面） | I7 | 直す |
| CR8 | まとめて訊く行を `note` の接頭辞で選ぶので、後の `set note=` で落ちる | 示せない（起こりうる） | 無し | 残課題 |
| CR9 | cruise §2 の 1 と `parent-issue.py show` の「書いていない（台帳に残さない…）」が新しい線では誤り（既定は外に出す・起動時に訊く） | 示せる（`test-parent-issue.py:466` の期待値がその文言） | I1（親 Issue に行が無い経路の説明が既定と食い違う） | 直す（`parent-issue.py` の本体を触る——変更範囲を広げた） |
| CR10 | `ledger.py` の docstring が「`test-ledger.py` が後の 2 つ（fix-line.md・found-lines.md）を突き合わせる」と書くが fix-line.md は見ていない | 示せる（`test-ledger.py:504-505` は `SKILL.md` を読む） | I9 | 直す |
| V3 | 元の周が `dropped` になると、依存に元の周を持つ足した行が依存待ちのまま着手できない | 示せない（起こりうる。§6 で出所ごとに渡されるので見落としにはならない） | 無し | 残課題 |

（V2 は CR3 と同じ）
