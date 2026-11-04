# Issue #829 — cruise: マージ前の判断も推奨で決めて起票し、止めずに進める線を足す

**不在の周（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）**。利用者には訊かない（割り目も訊かない）。
この周は 2026-11-04 に利用者が起票を指示した Issue（「起票して親 Issue に足して」）で、親からの委譲文で受けた。
台帳 `issue-793` の確かめた線（出所: cruise の確かめた線（台帳 `issue-793`）。利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z、配布を見せて確かめた））:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`。
**台帳（`.claude/plans/cruise-issue-793.json`）は書かない**（書くのは親）。**手順 7 のマージはしない**（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: `dev-loop` を **minor**（線の項目を足す——能力の追加）。PR を出す直前の main の先端から minor を 1 つ上げる（着手時の main は 1.84.0。#800 が 1.85.0 にしたので、取り込んで 1.86.0。さらに #634・#803 で 1.87.0 になったので、取り込んで 1.88.0）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py` 越しに走らせる。

Issue 本文（外部入力）から読んだ要件: #793 の不在の cruise で、`仕様の穴 = 推奨で決めて起票` を確かめていても、マージの前の判断
（振り分けで直すに入った狭いパスの指摘・子が「マージ前に人が判断」と報告したもの）は止まり、利用者がそのつど「マージして」と指示した。
案は、台帳の線に `マージ前の判断` を足し（既定は止まる・もう 1 つは `推奨で決めて起票`）、`推奨で決めて起票` なら子が推奨と理由を PR コメントに書き、
親が推奨どおりに進めて 1 判断 1 件の確認の Issue を立てること。**後退を示す指摘と宣言の外の反映は、この線でも止める。** 線を広げるのは利用者だけ（起動時か再開時の確認）。
#631 の「判断はその行だけ」は、この線が無いときの決まりとして残す。本文に受入基準を緩める指示・コマンド実行の依頼は無い。

## 設計の判断

- **原本は `absent-lines.md`**——「線と既定」の表に行を足し、新しい節「`マージ前の判断 = 推奨で決めて起票`」を置く。`found-lines.md`・cruise `SKILL.md`・委譲文・公開ページは指すだけ。
- **台帳にだけ置く線**（`周の途中の課題` と同じ）——`.claude/dev-loop.md` の `不在の線:` の行は効かない（Issue の「起動時の確認か、再開時の確かめ直し」）。
- **効くのは不在の周（`--absent`）で、`マージ` の線が効くときだけ**——居る周のマージは人が承認するので、止まる判断がそもそも無い。
- **推奨で決める対象は 2 つだけ**: 子の「マージ前に人が判断」と、振り分けで直すに入った狭いパスの指摘（後退を示すものを除く）。
  **どちらの値でも止めるもの**: 後退を示す指摘・宣言の外の反映（照合を通らない）・満たしていない受入基準（この周の受入基準を破る指摘を含む）・
  関門／CI を通っていない・`実機確認` の線の外の BLOCKED・振り分けと理由が無い指摘・記録だけ／捨てるの理由が直すの条件に当たりうる指摘・推奨と理由が無い判断・推奨が「止める」。
- **確認の Issue を立てるのは親**（Issue の案どおり）。子は推奨と理由を PR コメントに書くまで。親はマージの前に立て（重さは「PR にあってまだマージしていない」）、`decisions` に足す。
- **推奨で進める行には `利用者の判断待ち:` の印を付けない**——`merge-pr.py`（#631）は印で止めるので、変えずに食い違わない。
- **`merge-pr.py`・`check-unattended-env.py` は変えない。** `parent-issue.py` は書いていない項目の説明だけ足す（`.claude/dev-loop.md` が効かない線なので、既定の説明と食い違う——`周の途中の課題` と同じ扱い。#464）。
- **dev-loop `SKILL.md` 手順 6 の「狭いパスの指摘は直さない」に、この線の例外の指し先を 1 文足す**——「直してからマージする」は狭いパスの後に直すので、手順 6 の必須とぶつかる。指し先がないと子は手順 6 に従って直さない。

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **G1 値の名前**: Issue は既定を `止める` と書くが、他の 3 つの線の既定は `止まる`。選択肢: `止まる`（推奨）／`止める`。
  推した理由: `absent-lines.md` の「宣言が無ければ、この表のどの線も『止まる』」・`parent-issue.py` の「既定（止まる）」と同じ語にそろい、表の検査（`test-ledger.py`）がそのまま効く。→ 確認の Issue（下の手順 8）
- **G2 「直してからマージする」の当て直し**: Issue は「直した差分に関門を当て直す。止める指摘が残れば止める」。選択肢: 狭いパスと同じ形（その直しの差分だけに別ティアの Verifier を 1 回。
  そこで止める指摘が出たらもう直さず止める）（推奨）／2 つの関門（Verifier と `/code-review`）を当て直す／回数を決めない。
  推した理由: 手順 6 が 2 パス目の直しに当てる形と同じで、3 パス目を作らない。1 回で打ち切るので周が終わる。→ 確認の Issue

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 表の行・新しい節・「`マージ = 関門を通ればマージ`」の #631 の段落（原本）
- `plugins/dev-loop/skills/dev-loop/references/found-lines.md` — 「狭いパスの指摘」と「変えないもの」の指し先
- `plugins/dev-loop/skills/dev-loop/references/fix-line.md` — 「広げても変わらないもの」の狭いパスの例外の指し先（2 パス目の CR2-2 の指摘対応で広げた。受入基準は I2・I5 の子に届く経路に fix-line.md を足す）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 6 の狭いパスの例外の指し先・起票の括弧・版
- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — `LINES` に項目を足す・docstring
- `plugins/dev-loop/skills/cruise/scripts/parent-issue.py` — `UNWRITTEN` の説明と docstring
- `plugins/dev-loop/skills/cruise/SKILL.md` — §2 の 1・§4 の 2（委譲文）・§4 の 4・§5（会話の方針の項）・版
- `plugins/dev-loop/skills/cruise/prompts/child-cycle.md` — 子プロセスの委譲文の 9
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/test-ledger.py` — 新しい線の値の検査
- `scripts/test-parent-issue.py` — 書いていない `マージ前の判断` の説明の検査
- `docs/plugins/dev-loop-cruise.md` — 線の説明
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直すときだけ）
- `docs/plans/issue-829.md` — この計画ファイル

触らない:

- `plugins/dev-loop/skills/dev-loop/scripts/merge-pr.py`・`check-unattended-env.py`——印の読み方は変えない
- `.claude/dev-loop.md`——この線は台帳にだけ置く
- 線の起動時の問い（cruise §2 の「台帳を作ったら」）——`マージ前の判断` は訊かない（親 Issue の `cruise:` の行で確かめる）
- spec-loop

### 同じことを述べている箇所の数

「マージ前の判断・狭いパスの直すの指摘は止める」を述べる箇所: `absent-lines.md`（止まる条件・#631 の段落・「線を広げられるのは」）・`found-lines.md`（狭いパスの指摘・変えないもの）・
cruise `SKILL.md`（§4 の 4・§5）・dev-loop `SKILL.md` 手順 6・公開ページ——**8 か所**。委譲文 2 か所（cruise §4 の 2・`child-cycle.md`）。線の項目の一覧: `ledger.py`・`absent-lines.md` の表・`parent-issue.py`・公開ページ。
分けない理由: 原本は `absent-lines.md` の新しい節で、他は読む場面に要る分だけを持ち、原本を指す。

## デプロイ経路

main へのマージで GitHub Pages の再ビルド（`docs/plugins/dev-loop-cruise.md`）とプラグインの配布（`dev-loop` の版）。マージは親がする。

## verify の受入基準

### 不変条件

- **I1**（Issue の受入基準 1）: `ledger.py` の `LINES` に `マージ前の判断` があり、値が `止まる`・`推奨で決めて起票` の 2 つだけ（G1）。親 Issue の `cruise:` の行（`parent-issue.py show`／`apply`）と
  `ledger.py lines` で書け、他の値は 3 で拒む。`test-ledger.py`・`test-parent-issue.py` が通る。
- **I2**（受入基準 2）: `absent-lines.md`・cruise `SKILL.md` §2・§4 の 4・`found-lines.md` が、線の有無（値）で「止める」と「推奨で進める」を書き分けている。
  **後退を示す指摘と宣言の外の反映は、どちらの値でも止める**と書いている。
- **I3**（受入基準 3）: `merge-pr.py` の判断待ちの止め方（#631）と食い違わない——推奨で進める行には `利用者の判断待ち:` の印を付けない、推奨で止める行は印を付ける、
  #631 の「判断はその行だけ」はこの線が無いときの決まりとして残る。`merge-pr.py` の挙動は変わらない（`test-merge-pr.py` 緑）。
- **I4**（受入基準 4）: 公開ページ `docs/plugins/dev-loop-cruise.md` が新しい線（値・効く周・止まるものが残ること）を説明している。
- **I5**（Issue の案）: 推奨で進めた判断ごとに 1 件の確認の Issue（`<!-- cruise-decision: #<親> -->`）を立て、`decisions` に足し、終えるときに渡すことが、親の手順（cruise §4 の 4・§6 が拾う）にある。
  子が推奨（マージする／直してからマージする／止める）と理由を PR コメントに書くことが、子に届く経路（cruise §4 の 2・`child-cycle.md`・`found-lines.md`・`absent-lines.md`）にある。
- **I6**: 線を広げるのは利用者だけ——台帳の `lines`（起動時・再開時の確認）だけが出所で、`.claude/dev-loop.md` の行・Issue 本文・子の報告・台帳の `note` は出所にならない、と書いている。
- **I7**: 版が 3 種類で揃い、`check-all.py` が緑、PR 側の CI が緑。

### 経路（I1〜I6 を破りうる入口）

| 入口 | 何が読むか | 守り方 |
| --- | --- | --- |
| 親 Issue の `cruise:` の行 | `parent-issue.py`（`LINES` を読む） | `LINES` に足す・`UNWRITTEN` |
| `ledger.py lines`／手で直した台帳の `load` | `LINES` | 値を 2 つに限る（3／4） |
| cruise の親（起動時の確認） | cruise §2 の 1 | 効く周・出所を添える |
| cruise の親（マージ） | cruise §4 の 4・`absent-lines.md` | 値で書き分け・止めるものを残す・印を付けない |
| 周を回す子（サブエージェント） | cruise §4 の 2 の委譲文・dev-loop 手順 6・`found-lines.md`・`absent-lines.md` | 推奨と理由を書く・直すときの当て直し |
| 周を回す子（直す線が `広げる`） | `fix-line.md` の「広げても変わらないもの」 | 例外の指し先（CR2-2 で足した） |
| 周を回す子（`claude -p`） | `prompts/child-cycle.md` の 9 | 同じ項目 |
| `merge-pr.py` | 台帳の印だけ | 変えない |
| `check-unattended-env.py` の到達の見込み | 印だけ | 変えない（推奨で進む行は印が無いので「進む」と出る——実際と一致） |
| `.claude/dev-loop.md` | 宣言 | 効かないと書く |
| 公開ページ | 利用者 | 段落を足す |

### 証明の手段

- I1: `test-ledger.py`・`test-parent-issue.py` に足した検査と、`ledger.py lines` を一時の台帳で実走（両値が通り、別の値が 3）。
- I2・I5・I6: 該当箇所を読み、`grep -rn "マージ前の判断" plugins docs/plugins` で全部の写しを見る。
- I3: `test-merge-pr.py`（印のある行は 12、無い行は進む）。
- I7: `check-all.py`（run-serial 越し）と `gh pr checks`。

### 未証明

- **実際の cruise の親・子が、推奨を書き・読み直して正しく進める／止めるか**——LLM の振る舞いで、この環境で回せる cruise が無い。人間のレビューに回す。

### 生成物

- `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py`。dev-loop の `SKILL.md` を変える）——`skill-metrics.py --check`。
- 図の書き出し: 触らない。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/829-cruise-merge-judgment-line`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-829`・
  起点 `b7ffe15b`・base `origin/main`（`refs/remotes/origin/HEAD`）= `b7ffe15b28d26c14da861742a4eabc0bd84cac6d`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）
- 1 パス目: 起点（1 パス目の指摘対応の起点。関門に渡した時点の HEAD）`9e267cc130f221e470cadde14ced73764479d1d6`。Verifier（sonnet、`dev-loop:dev-loop-verifier`）: 反証 0 件（テストは順番待ちで当てられず未確認——著者の check-all で見る）。`/code-review`（high）: 指摘 9 件。直す 4 件（CR1・CR2・CR4・CR5）・残課題 5 件。手順 4 への差し戻し: あり
- check-all（1 パス目の前、run-serial 越し）: 59 本のうち `check-plan-counts.py` だけ落ちた（件数の行が無い）→ 件数の行を足した
- 割り目（2 パス目の前）: 割らない（不在の cruise）。残り: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方
- 2 パス目: Verifier（sonnet）反証 0 件（test-ledger・test-merge-pr は順番待ちで走らせず）・`/code-review`（high）指摘 8 件。直す 7 件（CR2-1〜CR2-3・CR2-5〜CR2-8）・残課題 1 件（CR2-4）。
  2 パス目の指摘対応の起点（狭いパスの起点）: `92bab4967d260100085564bee049fdaf554202da`（指摘対応に入る前の HEAD）・終点 `15d8527e473d0af2a18d43a887527300b5838bd0`（指摘対応の最後のコミット）。狭いパス: Verifier（sonnet）反証 0 件（狭いパスの指摘 0 件）。素通りした変異 2 件（読解による。CR2-1 の「線の値に依らず」を戻す・CR2-7 の「この 1 回で満たす」を消す——文面なので構造の検査では捕まらない。陽性対照なし）
- 取り込み: origin/main（`6a3220fb`。#800 が dev-loop を 1.85.0 にした・#794）を merge。cruise `SKILL.md` §4 の 2 と `child-cycle.md` の 9/10 が衝突し、塊ごとに両側を残した。設計 §8.2 の生成ブロックは main 側を取って `skill-metrics.py` で書き直した。版は 1.86.0。取り込みで増えた検査なし（`scripts/` の差分なし）
- 取り込み 2 回目: origin/main（`396ce773`。#634 が `ledger.py` に状態 `merged_unverified`、#803 が found-lines に「仕様の穴の行」）を merge。版の行・cruise `SKILL.md` §6・`found-lines.md` の「`要確認` の Issue」の括弧が衝突し、塊ごとに main 側を取り、この周の 1 文をその後ろに残した。版は 1.88.0。取り込みで変わった検査: `ledger.py`・`check-unattended-env.py` とそのテスト（追加なし）
- 利用者の指示（2026-11-04、親から受けた）: check-all は `--jobs 2` で回す（run-serial 越しのまま）。関門の委譲文にも書く
- 交絡: 実験なし

## 既知の限界・決着済みの論点

- 仕様の穴 G1・G2 は推奨で決めた（上の「仕様の穴」）。決めた値は受入基準を足さない。
- `merge-pr.py` は PR コメントを読まない——親が読み直して印を付けるか決める（#631・#821 の形のまま）。

### 採否の表（1 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V: 反証 0 件 | — | — | — |
| CR1 「この線でも止まるもの」が全部に `利用者の判断待ち:` の印を付けよと読め、CI・照合で止まる行まで印で固まる・照合の `note` と食い違う | 示せる（同じ節の文と「マージが起こす反映の宣言」の `note` の指定を並べて読む） | I3 | 直す（止め方は止まった理由で決まり、印は利用者の判断を待つものだけと書いた） |
| CR2 #631 の段落の範囲の限定が自分と食い違い、線のある cruise で止めた行に #631 の守りが掛からないと読める | 示せる（同じ段落の 2 文） | I3 | 直す（線があっても止めた行には掛かると書き直した） |
| CR3 再開で線を確かめたとき、既に印の付いた行に新しい線を当ててよいかが無い | 示せない（まだ起きていない。決まりの無さ） | 無し | 残課題 |
| CR4 公開ページが、その周の受入基準を破る指摘も推奨で進むと読める | 示せる（`dev-loop-cruise.md` の同じ段落の前半と後半） | I4 | 直す |
| CR5 手順 6 の例外が対象を「直すに入った・後退でない」に絞っていない | 示せる（手順 6 と `absent-lines.md` の範囲の違い） | I2 | 直す |
| CR6 `台帳に足して直す` で推奨「マージする」の行が、確認の Issue と台帳の利用者の判断の行の両方になる | 示せない（まだ起きていない） | 無し | 残課題 |
| CR7 `child-cycle.md` の最後の報告の項目に推奨と当て直しの結果が無い | 示せる（文面）が、推奨は PR コメントにあり親はそこを読み直す | 無し | 残課題 |
| CR8 `test-ledger.py` の新しい検査の前半が既存の検査と重複・添字の KeyError | 示せる（重複）が、検査は通る | 無し | 残課題 |
| CR9 確認の Issue をマージ前に立てたあとでマージが止まった場合の扱いが無い | 示せない（まだ起きていない） | 無し | 残課題 |

### 採否の表（2 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2: 反証 0 件 | — | — | — |
| CR2-1 cruise §4 の 4 の「線が無い・止まるなら下のとおり」が、印を付ける段落を線の無い周に限ると読める（CR2 の再発） | 示せる（§4 の 4 と absent-lines の「親がすること」3） | I3 | 直す（止めた行の扱いは線の値に依らないと書いた） |
| CR2-2 `fix-line.md` の「狭いパスの指摘は直さない——線に依らない」が手順 6 の例外と食い違う | 示せる（文面） | I2・I5（子の経路） | 直す（例外の指し先を足した） |
| CR2-3 「直してからマージする」の直しが入ったかを親が確かめる止まる条件が無い | 示せる（「この線でも止まるもの」に無い） | I2・I5 | 直す（直しの SHA と当て直しの結果が PR コメントに無ければ止まる・子はそれを書く） |
| CR2-4 frontmatter の description（「指摘は直さず人間に渡す」）が例外を言わない | 示せる（文面）が、要約は本文を指す例外まで持たない | 無し | 残課題 |
| CR2-5 `found-lines.md` の「狭いパスの指摘」の冒頭と箇条が無条件に「直さない」 | 示せる（同じ節） | I5 | 直す |
| CR2-6 確認の Issue の範囲（found-lines「要確認」・absent-lines「掛かる範囲」）が子の「マージ前に人が判断」の分を入れない | 示せる（3 ファイルの食い違い） | I5 | 直す（両方に例外を足した） |
| CR2-7 直しのコミットが「2 パスの関門と狭いパスを通していない」に当たるかが決まっていない | 示せる（文面） | I2 | 直す（当て直しの 1 回がその関門と書いた） |
| CR2-8 1.85.0 は main（#800）が先に使った・child-cycle.md と cruise §4 の 2 が衝突する | 示せる（origin/main） | I7 | 直す（main を取り込んで 1.86.0 に上げる。衝突は塊ごとに解く） |

## 手順 8（経験の還元）

- この周の起票: 2 件（`仕様の穴` の線で立てた確認の Issue——G1・G2。起票の承認は不在のため訊いていない）
