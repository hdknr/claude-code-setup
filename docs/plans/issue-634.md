# Issue #634 — `ledger.py`: 線「実機確認 = Refs でマージ」の周を `merged` に潰さず、実機確認待ちの状態 `merged_unverified` を足す

- 出所: **不在の周（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）**。cruise #793 の親から委ねられたサブエージェントが回す。
  `AskUserQuestion` を使わず、`EnterWorktree` を使わず worktree の絶対パスで作業する。マージ・台帳の書き込みは親がする（この周は PR と CI の確認まで）。
- 確かめた線（台帳 `issue-793`。出所: 利用者の確認（起動時・親 Issue #793 の cruise: の行・2026-11-03T03:56:17Z、配布を見せて確かめた）。親の委譲文で受けた）:
  仕様の穴 = 推奨で決めて起票、直す線 = 既定、マージ = 関門を通ればマージ（マージは親）、周の途中の課題 = 外に出す。
- **直す線: `既定`**（出所: cruise の確かめた線）。
- 周の途中の課題は `references/found-lines.md` の「振り分け」で分け、直すの行だけを起票・要確認の候補にする。それ以外は PR コメントだけ。
- `find-cycle.py 634` は 0（5 本とも当たらず）——新規の周。
- **Issue の 2 つの提案のうち、1 つ目（状態を足す）を採った。** 名前は Issue の例のまま `merged_unverified`（Issue が「名前は任意」と委ねている）。
  2 つ目（`user_ops` に積む）を採らない理由: `user_ops` は「利用者が自分で打つと決めた操作」で台帳全体に 1 つの置き換えの値（#466）——周ごとの実機確認を積むと、
  どの Issue の確認かが台帳の行から切れ、`status`・`next` の判定にも乗らない。Issue 本文が提案した選択肢の中から選んだので、仕様の穴（決めていない判断）には当たらないと判断した。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/ledger.py` — 状態 `merged_unverified`（`STATES`・`UNVERIFIED`・`MERGED`）、`ready`・`is_stranded`・`set` の取り残しの検査・`status` の辿りで `merged` と同じに読む、`show` の「利用者の確認待ち（実機確認）」の行、docstring（状態の表・`status` が見るもの・守る 4 行）
- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — 到達で `merged_unverified` を `merged` と同じに読む（読まないと `own` が None を返して例外で落ちる）・docstring 1 文
- `scripts/test-ledger.py` — 試料 `su`、守る 4 行に 1 対 1 の変異、本体の書き換えに合わせた既存の変異の当て先
- `scripts/test-check-unattended-env.py` — `merged_unverified` の到達の試料と、既存の変異の当て先
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 「`実機確認 = Refs でマージ`」の 5（台帳を `merged_unverified` にする・`merged` にする条件）
- `plugins/dev-loop/skills/dev-loop/references/ledger.md` — 「どう再開するか」の 2・5（実機確認待ちの扱いと渡し方）
- `plugins/dev-loop/skills/cruise/SKILL.md` — §6 の終える条件と渡すもの（と版の 2 行）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行だけ
- `.claude-plugin/marketplace.json` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す場合だけ）
- `docs/plans/issue-634.md` — この計画

触らない:

- `parent-issue.py`・`child-cycle.py`・`run-serial.py`（台帳の状態を読まない——`grep state` で確かめた）
- `merge-pr.py`（`Refs` の Issue を待たない挙動は absent-lines の 2 のとおりで変えない）
- 公開ページ（台帳の状態の一覧を持たない——`grep` で確かめた）
- `absent-lines.md` の `マージ = 関門を通ればマージ` の節の「未証明は … マージした Issue は台帳を `merged` にする」（未証明は実機確認ではない。Issue は `Fixes` で閉じる）

### 同じことを述べている箇所の数

- 「`Refs` でマージした周の台帳の状態」: `absent-lines.md` の 5（原本）・`ledger.py` の状態の表・`ledger.md` の 2・cruise §6 の 4 箇所。
  分けない理由: absent-lines は線の手順、ledger.py は状態の定義、ledger.md は再開の読み方、cruise §6 は終えるときの渡し方で、役目が違う。各箇所は状態の名前と自分の役目だけを書き、意味は ledger.py の表を正とする。
- 「依存先として済んだと読む状態」: `ledger.py`（`MERGED`）・`check-unattended-env.py`（`lg.MERGED` を読む——写しを作らない）の 2 箇所。

## 乗るデプロイ経路

- マージで dev-loop の新しい版が配られる（プラグインの配布）。公開サイトは `docs/plans/` の再ビルドだけ。
- **版: minor（dev-loop）**——台帳に状態を足す（CLAUDE.md の「プラグインの更新」の表の「能力・手順の追加」）。
  取り込む直前の origin/main の版（いま 1.75.3）から minor を 1 つ上げて 1.76.0。マージの直前に main が進んでいれば、その版から minor を 1 つ上げ直す（cruise `references/parallel.md` の「版とマージの順」）。

## verify の受入基準

不変条件と、それを破りうる経路（入口は `ledger.py` のサブコマンド——`set`・`show`・`next`・`status`・`group`——と、台帳を JSON から読む `check-unattended-env.py --ledger`、それを読む cruise の親）:

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| U1 | 合成の台帳で `Refs` マージの行（`merged_unverified`）が残ると、`show` に「すべてマージ済みか取り下げ」が出ず、「利用者の確認待ち（実機確認）」に `note` つきで列挙される（Issue の受入基準） | `show` | 終わりの行は `merged`・`dropped` だけで判定（`merged_unverified` は含めない）、確認待ちの行を足す |
| U2 | 親 Issue の一覧の行に `merged_unverified` があれば `status` は 5 と言わない（ほかに着手できる周が無ければ 3、その行を名指し） | `status` | 2 段目の判定は `merged`・`dropped` だけ。辿りは `merged_unverified` の先へ進まない |
| U3 | `merged_unverified` は依存先として済んだと読む（absent-lines の「依存する Issue は進めてよい」） | `next`・`status` の着手の判定・`check-unattended-env.py` の到達 | `ready` が `MERGED` を見る、到達が `lg.MERGED` を見る |
| U4 | `check-unattended-env.py --cruise --ledger` が `merged_unverified` を含む台帳で例外にならず、その行を到達に出さない | 到達 | `outcome` の分岐・一覧の除外 |
| U5 | まとめの中で `merged_unverified` かつ `落ちた:` の行も取り残しとして名指しされ、`merged_unverified` のまま `set group=` で抜けない | `show`・`next`・`set`・`status` | `is_stranded`・`set` の検査が `MERGED` を見る |
| U6 | 確かめて `merged` にしたら、確認待ちの行が消え、終わりの行と 5 が出る（対照） | `show`・`status` | 既存の判定 |
| U7 | 文書: absent-lines の 5 が `merged_unverified` にするよう言い、`merged` にする条件（Issue が閉じたのを実物で見る）を持つ。ledger.md の再開と cruise §6 が渡し方を持つ。「`merged` にし、`note` に…」の古い指示が残らない | 文書 | `grep` |
| U8 | 既存の挙動を壊さない（`test-ledger.py`・`test-check-unattended-env.py` の既存の試料が全部緑）。状態の表と `STATES` が一致し、「守る」の行と変異が 1 対 1 で、足した変異がどれも殺せる | 全サブコマンド | テスト自身が数える |
| U9 | 版が 3 種類（marketplace・plugin.json・SKILL.md 2 本）で揃い、origin/main より上 | 版 | `check-plugin-versions.py`・`check-version-bump.py` |
| U10 | 必須要件の掛け算: 受入基準 U1〜U9 を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（該当すれば）に渡す（4 つの受け渡し） | 関門 | 委譲文 |

- 未証明: なし（すべて合成の台帳で走らせて確かめられる）。
- BLOCKED: なし。実機確認の要る受入基準は無い（この周の `実機確認` の線は効かない）。
- 生成物: `docs/plugins/dev-loop-design.md` §8.2 の生成ブロック（`skill-metrics.py --check`。SKILL.md を触るので該当）。図の書き出しは該当なし（drawio を触らない）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/634-ledger-merged-unverified`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-634`・
  起点 `412ca8f7`・base は `origin/main` の merge-base `412ca8f78ff7177110e8250dcce4ebcbcf0d624a`
- 手順 4 の割り目: 割らない（不在の cruise）——不在のため訊かず続けた
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 1 パス目の指摘対応の起点: `f8f30320`（1 パス目の関門に渡した時点の HEAD）
- 交絡を潰した手順: 実験なし（合成の台帳で本体を走らせるテストだけ）

## 既知の限界・決着済みの論点

- `merged_unverified` から `merged` への書き換えは台帳の値だけで決まり、`ledger.py` は Issue が閉じたかを見ない（「守らない」の「台帳と実物が一致しているか」と同じ）。確かめるのは再開する親（ledger.md の 2）。
- `show` の「周の途中で足した行のうち済んでいないもの」は `merged_unverified` の足した行も出す（実機確認が残る＝済んでいない。cruise §6 の渡し方と一致）。

## 手順 8

- この周の起票: 0 件（不在の周のため関門の残課題は起票せず PR コメントに残す。仕様の穴の確認の Issue も無い）
