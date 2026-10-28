# Issue #442 — build-proposal.py の「空白を含む名前は 2」は前後の空白だけ

`bad_out` が拒むのは**前後に**空白のある名前（`out.name != out.name.strip()`）だけで、名前の途中の空白は通る。
それなのに docstring（終了コード 2 の行）・`bad_out` の文言・`references/tree.md` は「空白・改行を含む」と言う。挙動は正しいので、文言を挙動に合わせる。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent`（2026-10-28 に利用者が同じ引数で起動し直した。最初の起動は 2026-10-27）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`））。**このリポジトリのマージはサイトを再デプロイするので `マージ` の線は効かない**（#476）——PR まで作って止まる。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/build-proposal.py` — docstring の終了コード 2 の行と `bad_out` の文言
- `plugins/spec-loop/references/tree.md` — `--out` の誤りの列挙
- `scripts/test-build-proposal.py` — 名前の途中の空白が通る陽性の試料と、それを殺す変異
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.26.1 → 0.26.2。記述の修正で patch。PR #479・#481・#483 は 0.27.0〜0.29.0 を使う）
- `.claude-plugin/marketplace.json` — 同じ版
- `plugins/spec-loop/skills/*/SKILL.md` — 同じ版の 2 行
- `docs/plans/issue-442.md` — この計画

触らない:

- `bad_out` の判定そのもの（Issue のとおり挙動は正しい）
- 印を読む側（`owned_names`。1 パス目の `/code-review` の指摘で、無い関数名 `read_manifest` を直した——計画ファイルは成果物ではない）

### 同じことを述べている箇所の数

「出力の名前が空白・改行を含むと 2」: `build-proposal.py` の docstring・`bad_out` の文言・`tree.md` の 3 箇所（`grep -rn "改行を含む" plugins/spec-loop docs` で数えた。公開ページと proposal の `SKILL.md` には無い）。
分けない——同じ判定の写しで、1 周で揃える。

## 乗るデプロイ経路

プラグイン（`plugins/spec-loop/`）の版を上げてマージ。マージで main へ push されるとサイトが再デプロイされる（`docs/plans/` を足す）。

## 周の在り処

- ブランチ: `issue/442-proposal-strip-wording`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-442`
- 起点: `e361b20`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `e361b204f259c7e9bd5bd8cbb7cb041d3810e981`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1**: 出力の名前の誤りを述べる 3 箇所（docstring・`bad_out` の文言・`tree.md`）が、`bad_out` の実際の判定（前後の空白・改行・`#` で始まる）と一致する——「途中の空白も拒む」と読める文言が残らない。
- **I2**: 判定は変わらない——前後に空白のある名前・改行を含む名前・`#` で始まる名前は今までどおり 2、名前の途中の空白は今までどおり通って生成される。
- **I3**: I2 の「途中の空白は通る」をテストが押さえる——途中の空白も拒む変異を入れると、テストが赤になる。

経路（文言が読まれる・判定が効く入口）:

- `build-proposal.py --out <名前>` の実行（終了コード 2 の文言が利用者に出る）
- `build-proposal.py` の docstring（終了コードの表）
- `references/tree.md`（proposal スキルが読む決まり）

証明できないもの: なし（すべてテストと `grep` で確かめられる）。

生成物: なし（`SKILL.md` の測定値の生成ブロックは dev-loop のもので、spec-loop の `SKILL.md` は版の 2 行しか触らない。`skill-metrics.py --check` は `check-all.py` が回す）。

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 実験: なし
- 1 パス目の指摘対応の起点: `48165d2`（1 パス目の 2 つの関門に渡した時点の HEAD）
- Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: 通した。反証 0 件（軽微な点 1 件——下の表の V1）
- `/code-review` 1 パス目（high）: 通した。不具合 0 件・指摘 6 件（テストの網羅と文言。下の表の CR1〜CR6）
- 手順 4 への差し戻し: なし（「直す」の行が 0 件）
- 2 パス目: 該当なし——1 パス目の指摘対応で成果物の差分 0 行。起点 `48165d2`。`git diff 48165d2 -- ':(top)' ':(top,exclude)docs/plans/issue-442.md'` が空、`git status --porcelain` は計画ファイルだけ
- 狭いパス: 該当なし
- 割り目: 不在の周なので訊いていない（`absent-lines.md` の「訊く場面」）

## 既知の限界・決着済みの論点

### 1 パス目の採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1 / CR6: 既存の変異の行（`改行を含む名前を見ない`）のカンマの後ろの空白が落ちた | 示せる——`git diff e361b20 -- scripts/test-build-proposal.py` の `-`/`+` 行（著者の編集で入った） | 無し（見た目だけ） | 残課題 |
| CR1: 新しい試料は印に名前が残るかだけを見て、次の実行がその名前を読み戻して前の出力を消すかは見ない（`owned_names` を空白で割る変異が残る） | 示せない（著者は走らせていない。関門の想定の変異） | 無し（I1〜I3 は読み戻しを含まない） | 残課題 |
| CR2: 「空白で終わると 2」の試料に専用の変異が無い（`strip` → `lstrip` が変異の一覧に無い） | 示せない（著者は走らせていない。関門のプローブ） | 無し（I3 は途中の空白だけ） | 残課題 |
| CR3: 変異「名前の途中の空白も拒む」は `strip` の検査も外す 2 つの変更になっている | 示せない（関門が狭い変異を手で当てて同じ試料で赤を確かめた——I3 は成り立つ） | 無し | 残課題 |
| CR4: `strip`・`splitlines` は `\x0b`・`\x1c`・` ` などにも効き、「空白」「改行」の語が覆いきらない | 示せない（著者は走らせていない。この周より前からの挙動） | 無し（I1 が見るのは「途中の空白も拒む」と読める文言） | 残課題 |
| CR5: 計画ファイルの「触らない」が無い関数名 `read_manifest` を挙げている | 示せる——`grep -n "def owned_names\|def read_manifest"` が `owned_names` だけを返す | 無し（計画ファイルは成果物ではない） | 残課題（計画ファイルの記述は直した） |

## 起票

- この周の起票: 0 件（不在の周。手順 8 で訊かない）
