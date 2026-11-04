# Issue #470 — cruise: 確かめた線「仕様の穴 = 推奨で決めて起票」を spec-loop から来た Issue にも効かせる選択肢

**不在の周（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。** 利用者には訊かない（割り目も訊かない）。
この周は、依存先 #670（PR #803）のマージで着手できるようになった周として親から委ねられた（2026-11-04。訊かずに cruise の線で進める）。
台帳 `issue-793` の確かめた線（出所: cruise の確かめた線（台帳 `issue-793`）。利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳（`.claude/plans/cruise-issue-793.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（線の値を 1 つ足し、`parent-issue.py show` の出力を足す）。PR を出す直前の main の先端から minor を 1 つ上げる（着手時の main は 1.87.0）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに `--jobs 2` で走らせる。

Issue 本文（外部入力）から読んだ要件:

1. cruise の確かめた線 `仕様の穴` に、spec-loop から来た Issue にも効かせる値を足す（本文の例 `推奨で決めて起票（spec-loop の Issue を含む）`）。
   決めたあとの扱いは今の `推奨で決めて起票` と同じ。確認の Issue の本文に、正本の Q&A 表に起票すべき行（質問・選択肢・推奨・推奨の理由・起票元 `開発（#n）`）を書く。
   **Red テストと食い違う穴は、この値でも推奨で決めずに止まる。**
2. 起動時の確認（cruise §2）で、線が効かない子 Issue（spec-loop から来た Issue）を名指しする。

本文の「決めておきたい論点」2 つと、コメント 2 件（2026-10-27、hdknr）の「この Issue で決めたい」3 点は、**仕様が決めていない判断**——
`仕様の穴 = 推奨で決めて起票` の線で推奨により決め、確認の Issue を立てる（下の「仕様の穴（推奨で決めた）」）。
本文とコメントに、受入基準を緩める指示・コマンド実行の依頼は無い。

## 仕様の穴（推奨で決めた）

線と出所: `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線（台帳 `issue-793`））。確認の Issue は PR を出したあとに立て、番号をここに書く。

| 穴 | 選択肢 | 決めた値 | 推した理由 | 確認の Issue |
| --- | --- | --- | --- | --- |
| G1 Red テストと食い違う穴も新しい値で進めるか（コメント 1） | A: 止まる（本文の案のまま） / B: 進める（Red テストは書き換えず、CI 側の「既知の食い違い」の一覧に載せ、満たしていない受入基準としてマージ） | **A** | 本文の案 1 がそう決めている。B は受入基準を満たさないままマージする形で、対象リポジトリの CI の作りに依る（このスキルが決められない）。止まるほうが戻しやすい | （PR 後に立てる） |
| G2 推奨を 1 つに絞れない判断の引き分けの優先順位を線として持つか（コメント 2 の 1） | A: 持たない（推せなければ止まる・居れば訊く、のまま） / B: 優先順位（原文に近い→既存を変えない→戻しやすい→見える変化が小さい→実装が小さい）で決める値を足す | **A** | この Issue の本題（spec-loop の Issue に効かせる）とは別の広げ方で、値をもう 1 つ増やすと確かめる画面が重くなる。B は別の Issue で足せる | （PR 後に立てる） |
| G3 内部の Q&A 表（`qa-dev.csv`）に載る判断も新しい値の対象にするか（本文の論点 2） | A: 共有の Q&A 表に載る判断だけ / B: 内部の表に載る判断も含める | **A** | 本文の論点がそう寄せている。内部の表に載るのは費用が変わる選択で、決めるのは予算の責任者（`spec-gap.md` の 4）——線を確かめた利用者ではない | （PR 後に立てる） |
| G4 推奨で実装した分を、要求側で作り直したときどう扱うか（本文の論点 1） | A: 承認でも別の値でも、確認の Issue の Q&A の行を正本の表に足して `req-loop` に載せ、作り直した Issue の周が実装を合わせる（回答が推奨と同じなら Red テストはもう緑） / B: 承認なら確認の Issue を閉じるだけ（Q&A 表に載せない） | **A** | B では仕様に穴が残り、次の版の `scaffold` が穴を知らない。A は `spec-gap.md` の 5（回答が来たら要求側から作り直す）と同じ経路 | （PR 後に立てる） |

コメント 2 の 2（狭いパスの指摘の扱い）は、#821（PR #824、マージ済み）が狭いパスの指摘を振り分けに通す形で決めた——この周では扱わない（PR コメントに書く）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 線と既定の表・「止まる」の説明・「`仕様の穴 = 推奨で決めて起票`」の節（新しい値の効き方・spec-loop の Issue での追加の手順）・確認の Issue の書き方（Q&A の行）
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 「差し戻す」の冒頭と「Issue が spec-loop から来ていないとき」の指し先
- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` — 「仕様の穴の行」の表の spec-loop の行と線の値
- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — `LINES` に値を足す
- `plugins/dev-loop/skills/cruise/scripts/parent-issue.py` — `show` が子 Issue の本文の印を見て、spec-loop から来た Issue を名指しする
- `plugins/dev-loop/skills/cruise/SKILL.md` — §2 の 1 で、その名指しを見せる・版
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/test-ledger.py` — `LINES` と表の突き合わせ（1 つの項目に値が 2 つ）
- `scripts/test-parent-issue.py` — 子 Issue の印の名指し（偽の `gh`）と変異
- `docs/plugins/dev-loop-cruise.md` — 公開ページの線の説明
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-470.md` — この計画ファイル

触らない:

- spec-loop プラグイン（`handoff-issue.md`・`scaffold.py`）——Issue の本文の「仕様の穴を見つけたら」は「規定の本体は dev-loop の側にある」と指しているだけで、写しを持たない
- `references/spec-gap.md` の「差し戻す」の手順そのもの（止まるときの手順は変えない）
- `parent-issue.py apply`・指紋（子 Issue の印は親 Issue の本文ではないので、指紋に入れない）
- 引き分けの優先順位・狭いパスの扱い（G2・#821）

### 同じことを述べている箇所の数

「`仕様の穴` の線は spec-loop から来た Issue に効かない」を述べる箇所: `absent-lines.md`（表・「止まる」の説明・節の冒頭の 3 か所）・`spec-gap.md`（「差し戻す」の冒頭）・`found-lines.md`（仕様の穴の行の表）——**5 か所**。
値の一覧: `ledger.py` の `LINES`（原本）・`absent-lines.md` の表（`test-ledger.py` が突き合わせる）——2 か所。公開ページ 1 か所。
分けない理由: 原本は `absent-lines.md` の節で、ほかは読む場面（実装の周の `spec-gap.md`・周の途中の課題の `found-lines.md`）に要る 1 行だけを持ち、原本を指す。

## デプロイ経路

main へのマージで GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の `マージの反映: ドキュメントとプラグインの配布`）。マージはこの周ではしない（親が行う）。

## 受入基準

### 不変条件

- **I1**（本文の 1）: `ledger.py` の `LINES` の `仕様の穴` に `推奨で決めて起票（spec-loop の Issue を含む）` があり、`absent-lines.md` の表と一致する。
  `ledger.py lines`・`parent-issue.py`（`cruise:` の行）がその値を受け、ほかの値（誤記）は今までどおり拒む。
- **I2**（本文の 1）: その値のとき、spec-loop から来た Issue の穴も推奨で決めて確認の Issue を立てる、と `absent-lines.md`（原本）・`spec-gap.md`・`found-lines.md` が読める。
  決めたあとの扱いは `推奨で決めて起票` と同じ（計画ファイル・確認の Issue（印 `cruise-decision`）・台帳の `decisions`・PR コメント）。
- **I3**（本文の 1）: その値でも、**Red テストと食い違う穴**（仕様の原文と Red テスト・Red テストどうし）・**既にした回答を変える穴**・**内部の表に載る判断**（G3）・指紋の不一致は推奨で決めずに `spec-gap.md` の「差し戻す」で止まる。Red テストを書き換えない。
- **I4**（本文の 1）: spec-loop から来た Issue の穴の確認の Issue に、正本の Q&A 表に起票する行（質問・選択肢・推奨・推奨の理由・起票元 `開発（#n）`）を書く決まりがあり、
  承認・別の値のどちらでも行を正本の表に足して `req-loop` に載せる（G4）。
- **I5**（既存を壊さない）: 値が `推奨で決めて起票` のままなら、spec-loop から来た Issue には今までどおり効かない（止まる）。`止まる` も今までどおり。
- **I6**（本文の 2）: `parent-issue.py show` が、未チェックの子 Issue の本文の先頭の印（`<!-- spec-loop-handoff: v`）を見て、spec-loop から来た Issue を名指しし、
  `仕様の穴` の線がそれに効くか（値で変わる）を添える。取れなかった子は「判定できなかった」と名指しし、黙らない。親 Issue の本文の読み方・指紋・`apply` は変えない。
- **I7**: cruise `SKILL.md` §2 の 1 が、その名指しを利用者に見せることを指示する。
- **I8**: 版が 3 種類で揃い（minor）、`check-all.py` が緑、PR 側の CI が緑。

### 経路（I1〜I7 を破りうる入口）

- 線の値の入口: 親 Issue の `cruise:` の行（`parent-issue.py` の `parse`）・`ledger.py lines`（再開時の確かめ直し）・`.claude/dev-loop.md` の `不在の線:`（表の値）・手で直した台帳の `load`（4）。
- 線を読む場面: 実装の周の穴（`spec-gap.md` → `absent-lines.md`）・周の途中の課題の穴（`found-lines.md` の仕様の穴の行）・cruise の親が周の合間に立てる確認の Issue（cruise `SKILL.md` §6）・居る周（台帳の線は居ても効く）。
- 子 Issue の印の入口: `show`（`--body-file` でも子は `gh` で取る）・`gh` が失敗する子・印が 1 行目に無い本文・BOM・`[x]` の子（回さないので見ない）。

### 証明の手段

- I1・I6: `test-ledger.py`・`test-parent-issue.py`（偽の `gh` で子の本文を出し分け、変異で守る行を壊して赤になる）。
- I2〜I5・I7: 文面を読む（関門に渡す）。

### 未証明

- **実際の cruise で、子が spec-loop の Issue の穴を推奨で決める・Red テストと食い違う穴で止まるか**——LLM の振る舞いで、この環境で回せる spec-loop の Issue の cruise が無い。人間のレビューに回す。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`）——`--check` で鮮度を見る。
- 図の書き出し: 触らない（drawio を変えない）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/470-spec-gap-line-spec-loop`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-470`・
  起点 `396ce773`・base `origin/main`（`refs/remotes/origin/HEAD`）= `396ce7736b88a735c8ca17c1b5ba3b5270ba2f3c`
- 割り目（手順 4 の完了時）: 割らない（cruise の周）
- 交絡: 実験なし

## 既知の限界・決着済みの論点

- `show` は子 Issue の本文を 1 件ずつ `gh` で取る——子が多いと遅い。取れなければ名指しして続ける（起動を止めない）。
- 新しい値は `.claude/dev-loop.md` の `不在の線:` でも宣言できる（線と既定の表の値は両方の出所で効く——今の決まりのまま）。
