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
- 印を読む側（`read_manifest` など）

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
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未

## 既知の限界・決着済みの論点

（まだなし）

## 起票

- この周の起票: 0 件（不在の周。手順 8 で訊かない）
