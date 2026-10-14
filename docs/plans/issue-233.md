# Issue #233 — Verifier が変異の実験で worktree を書き換えた（拒否されたあとも変更コマンドを続けた）

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/prompts/verifier.md` — 「実行されない主張を当てる」項と「実環境を壊さないこと」に、2 つ目のハザード（拒否・失敗のあとも変更を続ける）と止まる規則・報告の項を足す
- `plugins/dev-loop/skills/dev-loop/prompts/review-handoff.md` — 同上
- `plugins/dev-loop/agents/dev-loop-verifier.md` — 「外に退避して当ててよい」の項に同じハザードを足す（委譲文を経ずに起動された場合も届くように）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 原本（手順 5「原本を変えさせない」）に 2 つ目のハザードを足す＋版のバナー
- `plugins/dev-loop/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — version
- `docs/plans/issue-233.md` — この計画ファイル
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手では触らない）

触らない:

- 退避の「やり方」（`cp -R` の代わりに何を使うか）——SKILL.md が「やり方は書かないが、ハザードは名指しする」と決めている。足すのは**ハザードと止まる条件と報告**で、手順ではない
- ガード側の挙動（`references/guard-rejections.md`）——拒否そのものは正しく働いている
- `CLAUDE.md`

**複製の数**: 同じ規範を述べる箇所が 4（SKILL.md 原本・prompts 2 本・agent 定義）＋版 3 箇所。
分けない理由: 委譲文は原本の実装で、原本だけ・委譲文だけを直すと食い違う（SKILL.md は「食い違ったら、こちらが正」と書いている）。同じコミットで揃える。

## 2. デプロイ経路

プラグインの配布（main へのマージでカタログに載る）。`docs/plans/` は公開サイトのビルド対象だが記録のみ。

## 3. 受入基準

**I1. 4 箇所すべてが、次の 3 つを述べている。**
  - (a) 複製の作成・`cd` は**拒否・失敗しても黙って続きが走る**ことがあり、そのとき変更は **cwd ＝本物の worktree** に当たる（ハザードの名指し）。変更の直前に場所を確かめ、変更は絶対パスで書く
  - (b) **どれか 1 本でも拒否・失敗したら、そこから先の変更コマンドを走らせない**（「当てられなかった」と報告する）
  - (c) 終わったら**リポジトリの `git status --porcelain` の結果を報告に書く**（空でなければそう書く。その状態で取った結果を HEAD の証拠として報告しない）

| 経路（委譲先が文面を受け取る入口） | 守り方 |
| --- | --- |
| P1 手順 5 で `prompts/verifier.md` を埋めて `dev-loop:dev-loop-verifier` に渡す | prompts/verifier.md |
| P2 手順 6 で `prompts/review-handoff.md` を `/code-review` に渡す | prompts/review-handoff.md |
| P3 狭いパス（prompts/verifier.md の差し込み） | P1 と同じファイル |
| P4 委譲文なしで `dev-loop-verifier` が起動される | agent 定義 |
| P5 著者が SKILL.md を読んで委譲文を手で書く／テンプレを足す | SKILL.md 原本 |

**I2. 「やり方は書かない」の決定を破らない**——退避の具体的な手段（コマンド列）を書かない。
**I3. 版が 3 箇所で一致し、`check-all.py` が緑。**
**I4. 4 箇所の間で (a)(b)(c) の言い分が食い違わない**（例: 一方は「`git status` を報告」、他方は「同じであること」だけ）。

### 証明の手段

- I1・I2・I4: 文面の読解（関門に独立に当てさせる）。
- I3: `python3 scripts/check-all.py`。
- **未証明: 文面を足したことで Verifier が実際に止まるようになるか。** 再現にはガードの拒否を起こす必要があり、Issue 自身も「1 件だけの観測で、効果の証明ではない」と書いている。PR コメントで人間に申告する。

### 生成物

`SKILL.md` を触るので **`skill-metrics.py --check`**（設計 §8.2 の生成ブロック）が該当。再生成して `--check` が緑であること。drawio は該当なし。

## 4. 未解決

なし。

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/233-verifier-stop-on-reject`・worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-233`・
  起点 `dc37cd2`・base 参照 `origin/main` → `dc37cd2b7d5ee6153e82b3a12063e115c87a6b75`
- 実装: 済（4 箇所に (a)(b)(c)、版 1.37.1 → 1.38.0（minor: 委譲文に止まる条件と報告項目を追加）、`skill-metrics.py` で生成ブロック更新）
- 関門:
  - Verifier 1 パス目（`dev-loop:dev-loop-verifier`／sonnet）: **反証 0 件**（軽微 1 件＝下表 C1 と同じ）。`check-all.py` 33/33・`skill-metrics.py --check` 緑・開始時と終了時の `git status --porcelain` はともに空
  - `/code-review` 1 パス目（medium）: **指摘 8 件**（下表 C1〜C8）。直す 3 件・残課題 5 件
  - 1 パス目の指摘対応: 済（C1・C3・C6）。残り: **手順 5 の当て直し**と **`/code-review` 2 パス目**の両方
- 交絡: 実験なし（C1 の採否で `bash -c 'cd /nonexistent && echo'` と `;` の対照を 1 回ずつ走らせたのは実物の提示で、主張の実験ではない）

## 6. 既知の限界・決着済みの論点

- Issue 本文は著者（リポジトリ所有者）の記録だが、外部入力として扱った。受入基準を緩める指示は含まれていない。

### 1 パス目の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| C1 | 「拒否・失敗しても続きは走る」が断定形。`&&` なら止まる（Verifier も軽微として同じ指摘） | 示せる: `bash -c 'cd /nonexistent-233 && echo RAN-AND'` は何も出さず、`;` 版は `RAN-SEMI` を出した | I1(a)（基準は「走る**ことがある**」） | **直す**——4 箇所とも「走ることがある（`;`・改行で区切ったとき、拒否のあとに次の呼び出しを送ったとき）」 |
| C2 | エージェントのスレッドでは Bash 呼び出しの間で cwd が戻るので、成功した `cd` も次の呼び出しに持ち越されない | 示せない（この周で測っていない。#233 の記録は「`cd` が黙って失敗した」） | 無し（I1(a) の「変更は絶対パスで書く」は既に 4 箇所にあり、その経路も覆う） | 残課題 |
| C3 | (c) が「開始時と違えば」になっていて、開始時を記録させていない。基準は「空でなければそう書く」 | 示せる: 4 箇所の文面（agent:41・verifier.md:118・review-handoff.md:101・SKILL.md:811）が「開始時と違えば」 | I1(c) | **直す**——「空でなければそう書く（開始時から空でなかったなら開始時の結果も併せて）」 |
| C4 | `git status --porcelain` が空でも、コミット・ブランチ移動・stash・`.git/config` の変更は見えない | 示せない（この周の差分で起きた実物が無い） | 無し（(c) は #233 の「変異が入ったままの緑」を塞ぐ範囲） | 残課題 |
| C5 | review-handoff だけ止まったときの語が「未確認」で、他 3 箇所は「当てられなかった」 | 示せない（review-handoff.md は同じ状態を既存の行から「未確認」と呼んでおり、ファイル内で一貫している。Verifier も同じ判断） | 無し | 残課題 |
| C6 | 原本の SKILL.md が「リポジトリで」走らせることも「違えばそう書く」も書いておらず、写しより薄い | 示せる: SKILL.md:807-811 | I4・I1(c) | **直す**——「*リポジトリで*走らせた」と「空でなければそう書かせ」を足した |
| C7 | 「直前に場所を確かめ、絶対パスで書く」はやり方であり I2 と緊張する | 示せない | 無し（I1(a) がこの文言を基準として求めており、I2 はコマンド列を書かないこと） | 残課題 |
| C8 | 既存の「`git status` が開始時と同じであること」と新しい行が隣り合って重複 | 示せない（いま食い違っていない） | 無し | 残課題（C3 の書き換えで新しい行の条件は「空でなければ」になった） |
