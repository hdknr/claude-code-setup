# Issue #375 — check-signoff が比べる範囲の外で、承認と合意の中身が食い違っても一致を返す（#367・#372 のまとめ）

`check-signoff.py` が比べる範囲を、**2 つの承認が見た中身**に揃える。見積りの根拠（`requirements/`・`spec/`）と、
v1 の `removed.csv`・`shared/` の外のファイルの行を範囲に入れ、2 つのタグの時点で違えば **1（一致しない）** にする。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent`（2026-10-27、利用者が会話で「-absent でまわします」と指示）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`））。**このリポジトリのマージはサイトを再デプロイするので `マージ` の線は効かない**（#476）——PR まで作って止まる。

入場の記録: `find-cycle.py 375` の 1 回目（worktree を作る前）が「当たったものがある」と出したのを確かめずに `prepare-worktree.sh` を走らせた。
作った後の 2 回目では、当たったのは作ったばかりのブランチ `issue/375-signoff-scope` だけで、計画ファイル・計画を足したコミット・`#375` を含むコミットメッセージは無かった
（`prepare-worktree.sh` は同じ番号の worktree・ブランチがあれば 3 で止まるが、0 で作った）。前の周は無いと判断して新規の周とした。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-signoff.py` — 比べる範囲（`compare_scope`）・`removed.csv` の比べる行（`removed_scope_rows`）・出力の範囲の言い方・docstring
- `scripts/test-check-signoff.py` — #367・#372 の試料、範囲の外の陽性対照、期待の文言、変異
- `scripts/test-build-proposal.py` — 「比較は要求のタグの時点から作る」の試料（2 つのタグの間に足すものを範囲の外へ移す）
- `plugins/spec-loop/references/signoff-tags.md` — 「2 つの承認が同じ範囲を見ていたか」の比べる場所
- `plugins/spec-loop/references/tree.md` — 置き方の決まりの「2 つのサインオフが同じ範囲を見ていたかは `shared/` の中身で確かめる」
- `plugins/spec-loop/README.md` — `check-signoff.py` の行
- `CLAUDE.md` — `check-signoff.py` の行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.26.0 → 0.27.0。0.x なので振る舞いの変更も minor）
- `.claude-plugin/marketplace.json` — 同じ版
- `plugins/spec-loop/skills/*/SKILL.md` — 同じ版の 2 行
- `docs/plans/issue-375.md` — この計画

触らない:

- 暫定の行の判定（`provisional_rows`）と、要求確定のタグの時点の配置の検査（#325・#338・#348）
- `build-proposal.py`（`resolve` の結果をそのまま使う）
- description（JSON 2 箇所と proposal の frontmatter）——「同じ共有の範囲（docs/v<n>/shared/ ほか）」は「ほか」で外れない

### 同じことを述べている箇所の数

「比べる範囲」: 本体の docstring（概要・守らないもの）・`signoff-tags.md`・`tree.md`・`README.md`・`CLAUDE.md` の 5 箇所。
分けない——同じ決定の写しで、片方だけ直すと範囲の説明が食い違う。

## 仕様の穴（不在の線で推奨により決めた）

Issue の「決めること」A・B・C。**線は `仕様の穴 = 推奨で決めて起票`（cruise の確かめた線（台帳 `issue-474`））**。確認の Issue: **#478**（台帳の `decisions` に記録）。

- **A（#367）: `requirements/`・`spec/` の差分の扱い**
  - 選択肢: (a) 比べる範囲に入れ、違えば 1 ／ (b) 範囲は今のまま、違えば警告（0 のまま）／ (c) 別の終了コード
  - **決めた値: (a)**。`spec/qa-dev.csv`（内部の層の Q&A 表）は外す。
  - 理由: 見積りは `requirements/`・`spec/` から数える（feasibility の手順 2）ので、そこが違えば予算の合意は承認と別の中身を見ている。
    (b) は `build-proposal.py` が終了コードしか見ないので、警告が提案書の手前で消える。(c) は呼ぶ側を全部直すことになる。
    `qa-dev.csv` は feasibility が 2 つのタグの間に正当に書く（費用の行）うえ、#339 で「内部の層はサインオフを割らない」と決めている。
- **B（#372）: 予算側だけにある、`merge` が拒否する配置**
  - 選択肢: (a) 比べる範囲に `docs/v1/removed.csv` と、範囲の中のファイル・機能の行を入れる ／ (b) 予算側にも配置の検査を当てる（2）
  - **決めた値: (a)**。`removed.csv` で比べる行は**内部の層の Q&A（`D-`）以外の全部**（1 パス目の F1 副次で、最初の「範囲の中のファイル・機能・共有の Q&A」からIssue の B に合わせて直した——範囲の外のファイルの行は `merge` が拒否する）。
  - 理由: A と同じ「範囲」の定義で説明できる（C）。(b) は予算側の時点に `merge` の読み方を写すことになる（#348 で避けた形）。
- **C**: 範囲は「2 つの承認が見た中身」= v1〜v<n> の `shared/`・`requirements/`・`spec/`（`qa-dev.csv` を除く）と `removed.csv`（v1 を含む）。
  **外すのは `feasibility/`・`proposal/`（予算の合意と決裁の側が書くもの）と内部の層だけ。**

別の値を選んだら直す場所: `check-signoff.py` の `compare_scope`・`removed_scope_rows`、`signoff-tags.md` の比べる場所、試料の期待。

## 乗るデプロイ経路

プラグイン（`plugins/spec-loop/`）の版を上げてマージ。マージで main へ push されるとサイトが再デプロイされる（`docs/plans/` を足す）。

## 周の在り処

- ブランチ: `issue/375-signoff-scope`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-375`
- 起点: `eab5e13`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `eab5e1387a3fa7587aed615754fcb7bc35cd75e0`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1（#367）**: 2 つのタグの時点で `requirements/`・`spec/`（`spec/qa-dev.csv` を除く）の中身が違えば、一致とは言わない（1。違うパスを出す）。前の版のものも同じ。
- **I2（#372）**: 予算側だけに `docs/v1/removed.csv` がある・`removed.csv` の範囲の中（`requirements/`・`spec/`）のファイルの行や機能の行が違うなら、一致とは言わない（1）。
- **I3（陽性対照）**: 範囲の外（`feasibility/`・`proposal/`・`spec/qa-dev.csv`・内部の層の Q&A の行・理由の列・行の順序・`.` で始まる名前）だけが違えば、今までどおり 0。
  （最初は「`removed.csv` の範囲の外のファイルの行」も 0 に入れていたが、Issue の B と食い違う写し違いだったので外した——下の「既知の限界」。）
- **I4**: 今までの判定（2 の条件・3 の暫定・`shared/` の比較）は変わらない（既存の試料が緑）。
- **I5**: 範囲の説明（docstring・`signoff-tags.md`・`tree.md`・`README.md`・`CLAUDE.md`）が本体の範囲と一致する。

経路（2 つのタグの時点の中身が照合に入る入口）:

| 経路 | 守り方 | 確かめ方 |
| --- | --- | --- |
| `git diff` の比べる場所（`compare_scope`） | `requirements/`・`spec/`・`docs/v1/removed.csv` を足し、`spec/qa-dev.csv` を除く | 試料: `spec/` だけ違う・`requirements/` だけ違う・前の版の `spec/` だけ違う・v1 の `removed.csv` が予算側だけ（1）／`qa-dev.csv` だけ違う・`feasibility/` だけ違う（0） |
| `removed.csv` の行（`removed_scope_rows`） | 内部の層の Q&A 以外の行を全部比べる | 試料: `ファイル,spec/…`・`ファイル,requirements/…`・`ファイル,feasibility/…`・`機能,…` の行が予算側だけ（1）／`D-` の行だけ（0） |
| `build-proposal.py`（`resolve` を呼ぶ） | 本体を変えない | `test-build-proposal.py` が緑。2 つのタグの間に `requirements/` を足すと作らない |

各経路の守りを外す変異で赤になる（陽性対照つき）。

生成物: `skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけ・図の書き出しも無い——**生成物なし**。

未証明: なし（照合は git の出力だけで決まり、試料で全部当てられる）。

## 未解決の判断

上の「仕様の穴」を確認の Issue で利用者に渡す。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 割り目（手順 4 の完了時）: 不在のため訊かず続けた
- 実験: 試料（`test-check-signoff.py` 72 件・変異 66 件、`test-build-proposal.py` 81 件・変異 89 件）。`check-all.py` 52/52
- 1 パス目の起点: `5b93f39`
- Verifier 1 パス目: 通した——反証 1 件（F1）
- `/code-review` 1 パス目: 通した——指摘 8 件（CR1〜CR8）
- 1 パス目の指摘対応: F1・F1 副次・CR2・CR3・CR6 を直した。差分は 0 行でない → 2 パス目を回す
- 割り目（2 パス目の前）: 不在のため訊かず続けた
- 2 パス目の起点: `9caf7f5`（この後のコミットは計画ファイルだけ）
- Verifier 2 パス目: 通した——反証 1 件（S1）
- `/code-review` 2 パス目: 通した——指摘 10 件（P1〜P10）
- 2 パス目の指摘対応: P1・P2（計画の文言）・P3・P4・P9・P10 を直した。起点 `9caf7f5` → 終点 `adaac0c`
- 狭いパス: 通した（sonnet）——反証 0 件（P10 の移行の記述を 0.26.0 と 0.27.0 の本体で当てて一致）
- PR: 作る（マージは止まる——このリポジトリのマージはサイトを再デプロイするので `マージ` の線が効かない。#476）
- main の取り込み（衝突解消・版の上げ直し）: `ccaa49e`（#440・#476 まで）と `f88215c`（#442 まで）。衝突は 2 回とも spec-loop の版の行だけで、周の 0.27.0 を取った（main は 0.26.1 → 0.26.2。0.27.0 はその次の minor のまま）。正味の差分は取り込み前と同じ 15 ファイル

## 起票

- この周の起票: 1 件（仕様の穴の確認の Issue。起票の承認は不在のため訊いていない）

## 既知の限界・決着済みの論点

- 仕様の穴 A・B・C は上の「仕様の穴」で推奨により決めた（確認の Issue を起票）。**決めた値は受入基準を緩める理由にならない。**
- 暫定の行・要求確定のタグの時点の配置の検査は触らない（#325・#338・#348 で決着）。
- ~~`test-build-proposal.py` の変異「比較を予算のタグの時点から作る」は等価変異~~——**誤りだった（1 パス目の F1・CR1 で反証）**。
  `removed.csv` の理由の列だけを 2 つのタグの間で変えると、照合は通り、提案書の「削除の理由」が変わる。変異と試料を戻した（試料は理由の列で作り直した）。
- **I3 の「`removed.csv` の範囲の外のファイルの行だけ違う → 0」は、Issue の受入基準 B（予算側だけにある、`merge` が拒否する配置を 1 か 2 にする）と食い違っていた**——
  計画を書いたときの写し違い（範囲の外のファイルの行は `merge` が拒否する）。1 パス目の F1 の副次の指摘で分かり、Issue の B に合わせて
  **内部の層の Q&A の行を除いて全部比べる**ようにした（基準を緩めたのではなく、Issue の基準に戻した）。確認の Issue #478 にも書き足す。

### 1 パス目の指摘の採否

Verifier（sonnet）: 反証 1 件（F1。副次の指摘つき）。`/code-review`（high）: 8 件。どちらも `git status --porcelain` は前後とも空。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| F1・CR1 | 「比較を予算のタグの時点から作る」は等価変異ではない（範囲の外の行・理由の列だけ違う組で、照合は通り提案書が変わる） | 示せる（Verifier の試料: 変異で code 1。`/code-review` の `equiv_probe.py`: 理由が入れ替わる） | I4（既存の変異と試料を、偽の理由で外した） | 直す |
| F1 副次 | 予算側だけにある `ファイル,feasibility/x.md` の行（`merge` が拒否する）で照合が 0 | 示せる（Verifier の試料: 照合 0・`merge` が拒否） | I2（Issue の B——予算側だけの `merge` が拒否する配置） | 直す（内部の層の Q&A 以外の行を全部比べる） |
| CR2 | 前の版の `spec/qa-dev.csv` を外すことを試料が見ない（今の版だけ外す変異が生き残る） | 示せる（`qadev_probe.py`: 変異で exit 1、スイートは緑） | I3 | 直す（試料と変異を足した） |
| CR3 | 2 にする「比べる場所が空」の検査（`scope()`）と比べる範囲（`compare_scope()`）が別で、docstring が古い範囲で書いている | 示せる（docstring の文言と `scope()` の中身） | I5 | 直す（docstring を `shared/`（と `removed.csv`）に直した。振る舞いは変えない） |
| CR4 | `INTERNAL_QA`・`SCOPE_DIRS` が `merge-versions.py` の `INTERNAL_QA_PATH`・`AREAS` の写し | 示せない（ずれは起きていない） | 無し | 残課題 |
| CR5 | `qa-csv.md` の「`shared/` は比べる範囲なので内部の表を置かない」の理由が古い | 示せる（文言） | 無し（I5 の列挙の外） | 残課題 |
| CR6 | `README.md` の 93 行目が「共有の範囲（`shared/` ほか）」のままで、同じファイルの 27 行目と食い違う | 示せる（文言） | I5（`README.md` は列挙の中） | 直す |
| CR7 | 定数と `signoff-tags.md` の突き合わせが `DOCS` を見なくなった | 示せない（走らせていない） | 無し | 残課題 |
| CR8 | `requirements/`・`spec/` のモードだけの変更（chmod）も 1 になる | 示せない（走らせていない） | 無し | 残課題 |

### 2 パス目の指摘の採否

Verifier（sonnet）: 反証 1 件（S1）。`/code-review`（high）: 10 件。どちらも `git status --porcelain` は前後とも空。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| S1 | `removed.csv` の同じ行が片側だけ 2 回あるのを見る試料が無い（`sorted(set(rows))` の変異が生き残る） | 示せる（Verifier の変異） | 無し（この周より前からの振る舞い） | 残課題 |
| P1 | 前の版の `requirements/` だけ違う試料が無い（前の版の `requirements/` を外す変異が生き残る） | 示せる（`/code-review` の試料: 本体 1・変異 0） | I1（前の版も同じ） | 直す（試料と変異を足した） |
| P2 | 計画の I3・経路の表・決めた値 B が、1 パス目の対応の後も古いまま | 示せる（文言） | — （計画ファイル。成果物ではない） | 直す（計画の文言） |
| P3 | `signoff-tags.md` の「比べる場所が無い・空なら 2」が、空かを見る場所（`shared/`）と食い違う | 示せる（文言と `scope()`） | I5 | 直す |
| P4 | `scope()` の docstring が「比べる場所」のまま | 示せる（文言） | I5 | 直す |
| P5 | 大文字小文字だけ違う `Requirements/` が予算側だけにあっても 0（macOS の重ね合わせは読む） | 示せる（`/code-review` の試料: 0） | 無し（`shared/` から同じ穴。#276 が台帳にある） | 残課題（#276） |
| P6 | `spec/spec_ir.json`（scaffold が書く）を 2 つのタグの間で書くと 1 | 示せない（走らせていない） | 無し | 残課題（#478 に書き足す） |
| P7 | 日本語のパスが `\346…` のように 8 進で出る（`core.quotePath`） | 示せる（`/code-review` の試料） | 無し（パスは出ている） | 残課題 |
| P8 | 公開ページ・description の「共有の範囲（shared/ ほか）」 | 示せる（文言） | 無し（I5 の列挙の外。決着済みの「ほか」） | 残課題 |
| P9 | `signoff-tags.md` の「比べないのは `feasibility/`・`proposal/` と内部の層」が、ほかの置き場所（`notes/` など）も比べないことと食い違う | 示せる（`/code-review` の試料: `notes/a.md` だけ違って 0） | I5 | 直す |
| P10 | 0.x の壊れる変更を minor で入れたのに、移行の手順を `references/` に書いていない | 示せる（`CLAUDE.md` の「プラグインの更新」の規定） | 無し（受入基準の外だが、対象リポジトリの `CLAUDE.md` の規約——原則「`CLAUDE.md` のルールを守る」） | 直す（`signoff-tags.md` に移行の節） |
