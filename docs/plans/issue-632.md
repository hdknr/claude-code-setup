# Issue #632 — `ledger.py`: `show` の「進行中」を親が続けられる行に限り、終了コードで状態を返す `status` を足す

- 出所: cruise #474（`/dev-loop:cruise 474 --absent` の再開・2026-11-02）の周。**不在の周**として訊かずに回す（`AskUserQuestion` を使わない）。
  cruise の親から委ねられた `claude -p` の子が回し、`EnterWorktree` を使わず worktree の絶対パスで作業する。マージ・台帳の書き込みは親がする。
- この周は #491 の受入基準 1 の測り直し（子プロセスで関門 2 つ × 2 パスを回しきれ、背景の体が殺されないか）を兼ねる（親の指示）。
- 確かめた線（台帳 `issue-474`。出所は利用者の確認——起動時 2026-10-27・再開時 2026-10-28／2026-11-01。親の委譲文で受けた）:
  仕様の穴 = 推奨で決めて起票、直す線 = 既定、マージ = 関門を通ればマージ（マージは親）、周の途中の課題 = 外に出す。
- 周の途中の課題は `references/found-lines.md` の「振り分け」で分ける。試料の穴・実際の利用でまず起きない形・言い回し・性能の推測は PR コメントに記録するだけ（利用者の方針 2026-11-01）。
- `find-cycle.py 632` は 1 で返ったが、当たったのは親の委譲文（`.claude/plans/cruise-issue-474-brief-632.md`）とこの子の出力の記録だけ——worktree・ブランチ・コミットは無く、新規の周である。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — `show` の「進行中」を impl・gate・pr に限り、blocked を「利用者の判断待ち（止まっている）」の行に出す。`status` を足す。docstring（使い方・終了コード・守る 3 行）
- `scripts/test-ledger.py` — `show`・`status` の試料と、守る 3 行に 1 対 1 の変異、試料の変異
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 「どう再開するか」の 1・2・5（「進行中」に blocked・await が入っていた前提の書き換えと、`status` の指し先）
- `plugins/dev-loop/skills/cruise/SKILL.md` — §6 に、終える条件を `status` で外から判定できることを 1 文（と版の 2 行）
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ）
- `docs/plans/issue-632.md` — この計画

触らない:

- `next` の出力と終了コード（Issue の提案は `status`「または」`next --exit-code`——`status` を選んだ。`next` の 0 は既存の利用者が読んでいる）
- `check-unattended-env.py`（台帳を JSON から自分で読み、`show` の出力を読まない）
- 公開ページ `docs/plugins/dev-loop-cruise.md`——外側のループの例は無い（`grep` で確かめた）。Issue の提案 3 は「ある場合」なので該当なし
- `CLAUDE.md`（`ledger.py` の説明の 1 行は「台帳を読み書きする」で変わらない）

### 同じことを述べている箇所の数

- 「`show` の『進行中』に何が入るか」: `ledger.py`（本体・docstring）・`references/ledger.md` の 2・5・`check-unattended-env.py` の docstring（「進行中（`impl`・`gate`・`pr`）」——既に新しい意味で書いてある）の 3 箇所。
  分けない理由: 本体が原本、ledger.md は再開の手順（読み方）、check-unattended-env は別の判定の説明で、役目が違う。ledger.md は本体を指す形に寄せる。
- 「終える条件」: cruise `SKILL.md` §6（原本）・`references/ledger.md` の 5・`ledger.py` の `status`（実装）の 3 箇所。`status` の docstring は §6 を正とすると書く。

## 乗るデプロイ経路

- マージで dev-loop の新しい版が配られる（プラグインの配布）。公開サイトは `docs/plans/` の再ビルドだけ。
- **版: minor（dev-loop）**——`ledger.py` に `status` という使い方を足す（CLAUDE.md の「プラグインの更新」の表の「能力・手順の追加」）。
  取り込む直前の origin/main の版（いま 1.74.1）から minor を 1 つ上げる（いまなら 1.75.0）。マージの直前に main が進んでいれば、その版から minor を 1 つ上げ直す（cruise `references/parallel.md` の「版とマージの順」）。

## verify の受入基準

不変条件と、それを破りうる経路（入口は `ledger.py` のサブコマンド——`show`・`next`・`status`——と、それを読む人・外側のループ・cruise の親）:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 合成の台帳（`merged` ×N＋`blocked` ×2）で `show` の「進行中」が「なし」、`status` が 3 を返す（Issue の受入基準 1） | `show`・`status` | `show` の「進行中」は impl・gate・pr だけ。`status` の判定 |
| A2 | `impl` の行が 1 本でもあれば `status` が 0（Issue の受入基準 2）。`gate`・`pr` も同じ | `status` | 進行中があれば 0 |
| A3 | `show` は blocked を「進行中」から外しても、別の行（利用者の判断待ち）に `note` つきで出す——黙って消さない。await は「利用者の操作待ち」に出続ける | `show` | 行を足す |
| A4 | `status` は cruise `SKILL.md` §6 の終える条件と食い違わない: 親 Issue の一覧の行（出所が空）がすべて merged か dropped なら「済んだ」（5）、一覧の行に着手できる周が無く残りが人待ち・それらか dropped に依存する周だけなら 3、取り残された行（落ちたのに merged）・進行中の行（出所に依らず）があれば 0 | `status` | §6 の条件をそのまま実装。周の途中で足した行だけが着手できても 0 と言わない |
| A5 | `status` は読めない・無い・崩れた台帳に 4 を返し、3・5（済んだ・人待ち）と答えない | `status` | `load` の検査をそのまま通る |
| A6 | 終了コードの表と定数が一致し、`status` の 3・5 が表にある | docstring・定数 | test-ledger の L10 |
| A7 | 既存の `show`・`next`・他のサブコマンドの挙動を壊さない | 全サブコマンド | test-ledger の既存の試料が全部緑 |
| A8 | 「守る」の行と変異が 1 対 1、足した変異がどれも殺せる | test-ledger | テスト自身が数える |
| A9 | `references/ledger.md` と cruise §6 の記述が本体と食い違わない（「進行中」に blocked・await が入るという古い記述が残らない） | 文書 | `grep` |
| A10 | 版が 3 種類（marketplace・plugin.json・SKILL.md 2 本）で揃い、origin/main より上 | 版 | `check-plugin-versions.py`・`check-version-bump.py` |

**組み合わせ（必須要件の掛け算）**: 受入基準を Verifier と `/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し）。重い検査は両方の関門の体にも run-serial 越しに走らせるよう渡す。

**証明できないもの（未証明）**: 無し——どれもテンポラリの台帳で走らせて観測できる。外側のループ（利用者の自作）での動作は、Issue の 4 行の例を `status` に置き換えた形でテンポラリの台帳に当てて代える。

**生成物**: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`SKILL.md` の版の行だけ変わる——行数は変わらない見込み。`skill-metrics.py --check` で確かめる）。図の書き出しは該当なし。

## 未解決の判断（仕様の穴）

- **穴 1: `status` が「済んだ」のとき返す終了コード。** Issue の案は `0` 進められる／`3` 人待ちだけ／`4` すべて済み。だが `ledger.py` の 4 は全サブコマンドで
  「判定できなかった（台帳が無い・壊れている）」——「済んだ」と同じ値にすると、外側のループが壊れた台帳と済んだ台帳を区別できない。
  - 選択肢: (a) Issue の案のまま 4、(b) 4 を「判定できなかった」に残し、「済んだ」を 5 にする、(c) `status` の値を全部新しくする（0／5／6 など）。
  - **決めた値: (b)**。理由: (a) は既存の 4 と意味が重なる。(c) は Issue の受入基準 1（人待ちだけで 3）から外れる。`status` は台帳を変えないので
    「拒んだ（3）」を返す場面が無く、3 を人待ちに使っても `status` の中では重ならない。
  - 線: 仕様の穴 = 推奨で決めて起票（台帳 `issue-474` の確かめた線）。確認の Issue: #782（`要確認` ラベル・印 `<!-- cruise-decision: #474 -->`）。PR コメントにも「仕様の穴（不在の線で推奨により決めた）」で書く。台帳の `decisions` に足すのは親

## 版の上げ方

- dev-loop を **minor** で上げる（`marketplace.json`・`plugin.json`・dev-loop と cruise の `SKILL.md` の版の 2 行）。

## 周の在り処

- ブランチ: `issue/632-ledger-status-exit-code`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-632`
- 起点コミット: `5ab1c45d`
- base: `origin/main`（`refs/remotes/origin/HEAD`）→ `5ab1c45d3d7917b30d56410ea972cace01372261`

## 関門の進捗（再開点）

- 実装: 済み（`e5f934aa`）。手元の `test-ledger.py` は run-serial 越しで緑。`check-all.py`（run-serial 越し）58/58 緑
- **1 パス目の指摘対応の起点**: `463f1e2b5cacc59af2b6aaa1c7af6ee8f71583dd`（1 パス目の関門に渡した時点の HEAD）
- **Verifier 1 パス目**（`dev-loop:dev-loop-verifier`・sonnet。実装は Opus）: 通した——反証 1 件（V1-R1。空の台帳で 5）。報告回収済み
- **`/code-review` 1 パス目**（high）: 通した——1 回目は受け渡しを付けずに起動してしまった（フォークが計画ファイルを自分で読んだ）ので、
  `prompts/review-handoff.md` を埋めて貼った 2 回目を回した。指摘は 1 回目 9 件・2 回目 8 件（重複を畳んで下の表に 12 行）
- 手順 4 への差し戻し: あり（下の表の「直す」3 行）
- 割り目（手順 6 の 2 パス目の前）: 不在の周なので訊かない——このまま続ける。残りは Verifier の当て直しと `/code-review` 2 パス目の両方
- **Verifier 2 パス目**（sonnet）: 通した——反証 2 件（V2-R1 全角のコロン・V2-R2 変異の推定）
- **`/code-review` 2 パス目**（high・受け渡しを貼った）: 通した——指摘 6 件
- **2 パス目の指摘対応の起点（狭いパス）**: `0932764c650e77a95a28f03405ee5ad9ca3ad4d0`・**終点**: `679cc1fb44dd5cb1d627afec533119072c0ca1d9`
- **狭いパス**（sonnet。差分は起点→終点の 2 点）: 通した——反証 0 件・所見 2 件（下の表。直さない）。独立の変異 5 本: 赤 3・素通り 1（NP-1、陽性対照つき）・未実行 1
- 割り目（手順 4）: 不在の周なので訊かない——このまま続ける
- 交絡を潰した手順: 実験なし（テンポラリの台帳で走らせるだけ）

## 既知の限界・決着済みの論点

- `status` は台帳の値だけで判定する——PR がマージ済みか・worktree があるかは見ない（`ledger.py` の「守らない」の「台帳と実物が一致しているか」と同じ）。
- 穴 1 の終了コード（上の「未解決の判断」）——推奨で決めて確認の Issue に残す。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1 `note` が `利用者の判断待ち:` の `pr` 行を `status` が 0（進められる）と数え、`show` も「進行中」に出す（#2427 と同じ空回り） | 示せる（テンポラリの台帳で `status` が `進められる（進行中: #2(pr)）` rc=0。CR が再現） | A4・A3（§6 は人待ちを渡して終える。cruise §4-4 の印） | 直す——`judging()` で判断待ちの印（まとめならどれか 1 行）を進行中から外し、「利用者の判断待ち」の行に出す |
| CR2 `status` の依存の辿りがまとめの仲間を辿らず、一覧の行が足した行を待つのに 3 | 示せる（CR が `next` 4・`status` 3 を再現。試料 `sm` で修正前に 3） | A4 | 直す——辿りにまとめの仲間を足す |
| CR3＝V1-R1 空の台帳（`init` 直後）・出所のある行だけの台帳で `status` が 5 | 示せる（`init e; status e` rc=5） | 無し（A4 の「一覧の行がすべて済み」の空の場合。`apply` が `init` と `add` の間で殺された時だけ） | 記録だけ（実際の利用でまず起きない形） |
| CR4 `references/ledger.md` の 5 が「進行中が await と blocked だけ」のまま | 示せる（文面） | A9 | 直す |
| CR5 `EXIT_WAITING` が `EXIT_REJECTED` と同じ 3。`-h` は 0 | 示せる（`-h` rc=0 は全サブコマンドで既存） | 無し（決着済み: `status` は拒む場面が無い） | 記録だけ |
| CR6 `status` の値を 3 箇所に散文で書いている | 示せる（文面） | 無し | 記録だけ（言い回し） |
| CR7 親 Issue にあって台帳に無い Issue があっても 5 | 示せない（`status` は台帳しか見ない——既知の限界） | 無し | 記録だけ |
| CR8 まとめの `blocked` で `note` が代表にしか無いと、他の行が「note が空」 | 示せる（表示） | 無し | 記録だけ |
| CR9 `(DONE, "dropped")` などの判定の写しが増えた | 示せない（いま食い違いは無い） | 無し | 記録だけ |
| CR10 利用者が `await` の操作を打っても、台帳が変わるまで `status` は 3 のまま | 示せる | 無し（台帳の値だけで決める——既知の限界。§6 も渡して終える） | 記録だけ |
| CR11 公開ページ `dev-loop-cruise.md` の再開の節が `status` を書かず、「進行中」だけ実物で確かめると書く | 示せる（文面） | 無し（ledger.md が原本） | 記録だけ |
| CR12 `judge` の辿りが `check-unattended-env.py` の辿りと別の実装 | 示せない（CR2 を直した後は食い違いを示せない） | 無し | 記録だけ |

### 2 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| P2-CR1 `status` の依存の辿りが `dropped`・`merged` の行の先まで進み、取り下げた一覧の行の先の足した行で 0 | 示せる（CR が再現。試料 `sx` で修正前 0） | A4 | 直す——済んだ・取り下げた行の先は辿らない |
| P2-CR3＝V2-R1 `JUDGE_NOTE` が半角のコロンだけで、`check-unattended-env.py` の `JUDGE_MARKS`（全角も）と食い違う。コメントの「同じ印で読む」が偽 | 示せる（両方の関門が `note=利用者の判断待ち：…` で rc=0 を再現） | A4（同じ空回りが残る） | 直す——全角も印と読む |
| P2-CR5 cruise §6 が判断待ちの `pr` 行を止まっている周に数えていない（`status` は数える） | 示せる（文面） | A9 | 直す——§6 に 1 文 |
| P2-CR6 `show` の「利用者の判断待ち」の行が blocked と pr を状態なしで混ぜる | 示せる（表示） | A3（判断待ちの pr 行は CR1 でこの行に移した——この周が持ち込んだ形） | 直す——状態を添える |
| P2-CR2 判断待ちの印のある足した行が `pr` で、一覧の行が済んでいると 5 | 示せる | 無し（§6 は一覧の行が済めば終え、足した行は名指しして渡す——5 の行が名指しする） | 記録だけ |
| P2-CR4 判断待ちの印を残したまま `set state=impl` すると 3 | 示せる | 無し（cruise `references/parallel.md` は戻すとき `note` を書き直す——手順どおりならまず起きない） | 記録だけ |
| V2-R2 `judging()` の変異 2 本（状態を見ない・部分一致）が既存の試料で殺せないと推定 | 示せない（推定。変異テストに当てていない） | 無し | 記録だけ（試料の穴） |

### 狭いパスの表（直さない。採否は人間が決める）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| NP-1 辿りの打ち切りから `merged` だけを外す変異が、試料（`sx` は `dropped` だけ）で素通りすると推定 | 示せる（陽性対照: merged の #2 が未完の足した #9 に依存する台帳で、元 rc=3・変異 rc=0。変異テストには未投入） | 無し（試料の穴。merged の行が未完の依存を持つ形） | 人間が決める（推奨: 記録だけ） |
| NP-2 `references/ledger.md` の 2・5 が判断待ちの印を半角でだけ書く（実装は全角も読む） | 示せる（文面） | 無し（全角で書いたときの読み手の説明だけ。直した 4 行の外） | 人間が決める（推奨: 記録だけ） |

## 手順 7・8

- PR: #783（`Fixes #632`）。マージはしない（親がする）。乗る経路は dev-loop 1.75.0 の配布と公開サイトの `docs/plans/` の再ビルド
- 起票: 確認の Issue #782 だけ（不在の線 `仕様の穴 = 推奨で決めて起票`）。関門の指摘から起票する候補は無い——found-lines の「振り分け」で直すに当たる行は、どれもこの周の中で直した。
  残りは記録だけで、PR #783 のコメントに残した。利用者が不在の周なので訊いていない
- 焼き戻し: `/code-review` を受け渡しなしの `high` だけで起動すると、フォークが同期で終わって受入基準なしのレビューになった（1 パス目の 1 回目）。
  これは既存のメモリ `code-review-skill-forks` が既に持っていたので、そのメモリの索引の 1 行だけを直した（受け渡しは `args` に入れる）。リポジトリに焼き戻す学びは無い
- この周の起票: 1 件（#782——仕様の穴を推奨で決めた確認の Issue）
