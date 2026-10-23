# Issue #361 — spec-loop: 前の版の時点が崩れている（反映済みでない Q&A が残る）ときの scaffold の止め方と手当て（#355〜#358 のまとめ）

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — `classify` で前の版の Q&A の状態を直接見る（A）。凍結した前の版なら全機能を追加として出す（C）。`read_whole` の docstring（D）。docstring 冒頭・「守らないもの」・`git` の要否。成功時に `classify` の知らせを出す
- `plugins/spec-loop/references/versions.md` — 「差分の周を始める前に」の下に、前の版の時点が崩れていたときの手当てを 1 か所に書く（B・C）
- `plugins/spec-loop/references/handoff-issue.md` — 凍結した前の版が崩れていたら全部が追加になることを 1 行（分け方の原本なので）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 手順 3 の止まる理由に前の版を足す・凍結の知らせの扱い。版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行だけ（全 `SKILL.md` に版を書く規則）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.21.0 → 0.22.0。前の版の確認中でも止まる＝挙動が変わるので minor。0.x）
- `.claude-plugin/marketplace.json` — 同上
- `scripts/test-scaffold.py` — 試料（指していない暫定反映・確認中・内部の表・手当ての実演・凍結）と変異（E）
- `CLAUDE.md` — `scaffold.py` の説明（該当すれば）
- `docs/plans/issue-361.md` — この計画

触らない:

- 今の版の関門（条件 1・`held`）の定義
- `check-frozen.py`（凍結の確かめそのもの。C は scaffold 側で凍結を見る）
- 前の版の中間表現の決まりの当て方（#319 のパスの変数）——崩れていない前の版の扱いは変えない
- Issue の本文の節と印（dev-loop の `spec-gap.md` が写しを持つ）

### 同じことを述べている箇所の数

- 「前の版の時点が崩れていたら止める・どう直す」: `scaffold.py` の docstring 冒頭・`classify`・`read_whole` の docstring・`versions.md`・scaffold `SKILL.md` 手順 3 —— 5 箇所。原本は `versions.md`（手当て）と `scaffold.py` の docstring（判定）に置き、他は指す。
- 分けない理由: Issue のとおり、4 件とも「前の版の時点をどう信じ、崩れていたらどこから直すか」の別の面で、止める条件と手当てを別々に決めると食い違う。

## 乗るデプロイ経路

プラグインの版を上げて配布（`marketplace update` → `plugin update`）。`docs/plans/` は main への push で Pages に載る。

## 人間の判断（2026-10-23。AskUserQuestion）

- **H1（A）**: 前の版で止める条件は「Q&A 表（共有・内部）に状態が `反映済み` でない行が残る」——中間表現が指しているかに依らない。**`確認中` も含め**、どちらも「v<n-1> の scaffold は作れていない」と名指しする（#335 の対照「確認中なら名指ししない」を反転）。出力行の文字列照合はやめる。
- **H2（C）**: 凍結した前の版（`release-v<n-1>`）が崩れていたら、止めずに前の版の時点を信じない——**v<n> の全機能を追加として**本文を作る。v<n> で消した機能の撤去の本文は作らない（出力で名指し）。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A1 | 前の版の全体の Q&A（共有・内部）に `反映済み` でない行が 1 つでもあり、前の版が凍結していなければ、生成・`--dry-run`・`--red-check` は 1 で止まり何も書かない（生成なら Issue の本文を消す）。中間表現が**指していない**行でも止まる | `classify`（3 つの経路が通る） | 状態を直接見る。試料: 指していない暫定反映・指していない確認中・内部の表の確認中 |
| A2 | 止まるとき、各行の No と状態・「v<n-1> の scaffold は作れていない（`--check --upto <n-1>` が 0 にならない）」・`versions.md` の手当ての節を名指しする。名指しは出力行の文字列照合で決めない | `classify` | 状態の一覧から直接作る |
| A3 | 前の版の Q&A が全部 `反映済み` なら、今までどおり（分け方・前の版の中間表現の検査・#319） | 既存の全試料 | `check-all.py` |
| B1 | `versions.md` に、v<n> が在るときの手当て（v<n> を `docs/` の外へ退ける → v<n-1> で Q&A を確定 → v<n-1> で scaffold して登録 → v<n> を戻す）が 1 か所にあり、`scaffold.py` の停止の出力がその見出しを指す | `versions.md`・`classify` | 見出しをテストで突き合わせる |
| B2 | その手当てを試料で実演すると、`--check --upto <n-1>` が 0、v<n> の生成が 0 になる | 手当ての手順 | 試料（手順をそのまま流す） |
| C1 | 凍結した版に `反映済み` でない Q&A が残る状態は作れる（`release-v1` を付けた git リポジトリ。`check-frozen.py` は 0） | 試料 | 試料で作って観測 |
| C2 | 前の版が凍結して崩れていれば、生成は 0 で、v<n> の全機能が追加（変更・削除 0）、出力が凍結と撤去を作らないことを名指しする | `classify` | 試料 |
| C3 | 凍結を判定できない（`git` を起動できない・浅い clone）なら 2。git の作業ツリーでなければ凍結した版は無い（タグを持てない）として A1 に倒す | `classify` | 試料（git でない試料は A1 の試料そのもの） |
| D1 | `read_whole` の docstring が、前の版が関門を通っていない場合を含む形。挙動は変えない | docstring | 読む |
| E1 | A〜C の判定を外す変異で `test-scaffold.py` が赤になる。陽性対照: 崩れていない前の版の試料は通る | `MUTATIONS` | 変異テスト |
| X1 | 版が 3 箇所で揃う（`marketplace.json`・`plugin.json`・全 `SKILL.md`） | 版 | `check-plugin-versions.py` |

### 必須要件の掛け算

- 受入基準 × 2 つの関門（Verifier・`/code-review`）× 2 パス = 4 つの受け渡し。2 パス目の修正は狭いパス。

### この環境では証明できないもの（未証明）

- 実運用の正本リポジトリで、凍結した版が実際にこの状態になるか（試料で作れることまでは示す）。

### 生成物

- `skill-metrics.py` の生成ブロック（dev-loop の設計 §8.2）は dev-loop の `SKILL.md` だけを測る——触らないので該当なし。図の書き出しも該当なし。**生成物なし**（scaffold の生成物は試料の中で作って捨てる）。

## 未解決の判断・確認待ち

- なし（H1・H2 で決着）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/361-prev-version-unsettled`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-361`・起点 `ae7b544`・base 参照 `origin/main` = `ae7b544963a87562aa0bb5ae635e12ba2b898b19`
- 関門: 未着手
- 反証: なし
- 交絡を潰した手順: 未着手

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 前の版の確認中も名指しする | 採った（H1） | 条件 1 で v<n-1> の scaffold は作れない。`--check --upto` と止める条件が揃う |
| 凍結した前の版は全機能を追加 | 採った（H2） | 直せない版を信じない。撤去の本文が出ないのは代償として名指しする |
| 前の版の未決定の印（仕様の本文）は見ない | 採らなかった | Issue の範囲は Q&A。印の定義が版をまたいで変わりうる（#319 と同じ懸念） |
