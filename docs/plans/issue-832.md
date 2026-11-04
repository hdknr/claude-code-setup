# Issue #832 — Eval のサンドボックスの中で git が動かず、git を使うスキル（proposal など）の振る舞いを当てられない

不在の周（`/dev-loop:cruise 793 --absent` の起動・2026-11-03）。利用者には訊かない（割り目も訊かず「割らない（不在の cruise）」）。

- 直す線: **既定**（出所: cruise の確かめた線——利用者の確認（起動時・親 Issue #793 の `cruise:` の行・2026-11-03T03:56:17Z））
- 版の上げ方: **minor・spec-loop**（ケースの注記を直す。PR を出す直前の main の先端から 1 つ上げる）
- 環境: 利用者の指示（2026-11-04、#832 のコメント）で親が `brew install git` を入れた——`/opt/homebrew/bin/git`（2.56.0）が `PATH` で `/usr/bin/git`（xcrun の shim、Xcode の 2.54.0）より前。
  **この周では環境をこれ以上変えない**（親の指示）。
- proposal のケースの扱い: **判別しないケースとして残し、注記を BLOCKED から「判別できない（理由つき）」に直す**
  （親の決定・2026-11-04。推奨で決めた。判別できる試料を探すのは #274 の受入基準 B の続きで、この周の範囲の外）。

## 変更範囲

触る:
- `plugins/spec-loop/evals/proposal-diff-handwritten/case.yaml` — 冒頭の注記（BLOCKED → 判別できない・理由・実測の指し先）
- `CLAUDE.md` — 「振る舞いを Eval で当てる」にサンドボックスの git の手順、`evals/` の項に実測の指し先を足す
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-832.md` — この計画

触らない:
- `docs/plans/issue-274.md`（#274 の周の記録。proposal の実測はこのファイルを正とする）
- grader・試料（`scaffold.sh`）・ほかの 3 ケース・陽性対照のケース（リポジトリに置かない——CLAUDE.md の「対照はリポジトリに置かない」）

## デプロイ経路

main へのマージで GitHub Pages の再ビルド（`CLAUDE.md` は公開サイトに載らない）とプラグインの配布（spec-loop の版）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A | Eval のサンドボックスの中で `git --version` が通ることを trace で示す（陽性対照） | 対照が空振り（grader が git の出力以外で緑になる）・動いた git が何か分からない | trace の tool_result に `git version 2.56.0`・`release-v1` が出ること、`xcrun --find git` の値 |
| B | その形で proposal のケースを今の版と差分モードが入る前の版に当て、判別（または判別できないこと）を赤・緑の理由まで記録する | git が動かずに照合で止まった緑・赤を振る舞いと読む・下書きの中身を見ずに judge の票だけで読む | 各回の trace で `check-signoff.py` の終了コードが 0、Write した下書きの中身 |
| C | 環境を変えた手段（Homebrew の git）の手順を CLAUDE.md の「振る舞いを Eval で当てる」に書く。書く内容は観測した事実と一致する | 観測と違う仕組みを書く（「PATH の先頭で決まる」をそのまま当てはめる）・既存の段落と食い違う | trace の `type -a git`・`xcrun --find git`・版の値と照合 |
| D | ケースの注記が実測と一致し、BLOCKED の記述が残らない | 注記の指し先が実測の無いファイル・「git が動かない」の記述が残る | `grep` と本文 |
| E | 版が 3 種類で揃い、main の先端から minor を 1 つ上げた値 | 揃え漏れ・取り込みで main と同じ値に戻る | `check-plugin-versions.py`・`check-version-bump.py` |
| F | Eval の費用は合計 $27（API 換算）以内、`--concurrency 1` | 回し直しが重なる | 下の「費用」に足していく |

掛け算: 受入基準を Verifier と `/code-review` の両方に、1・2 パス目とも渡す（2 パス目が該当なしなら初回の 2 つ）。

**未証明**: 「判別できない」は各腕 2 回の結果——率ではない（振る舞いの揺れで修正前の版が一覧を書く回があるかは、この回数では言えない）。
`type -a git` に `/opt/homebrew/bin/git` が出ない理由は確かめていない（記述は観測にとどめる）。
**proposal のケースが「一覧は書かない」の行を外した回帰を捕まえるか**は確かめていない——0.7.0 は「変更の提案書」の行も持たないので、この比較は守る行を切り分けていない（/code-review 2 パス目。回すなら「一覧は書かない」だけを外した版。#274 の受入基準 B の続き）。
**BLOCKED**: 無し。

生成物: **該当なし**——Eval の結果は scratchpad（`results/` は `.gitignore`）。図・`SKILL.md` の測定値の生成ブロックに触れない（`SKILL.md` は版の 2 行だけ。`skill-metrics.py --check` は check-all に入っている）。

## Eval の回し方と結果（claude 2.1.318・2026-11-04・メインの作業ツリーを cwd にした親の体から）

共通の引数は `docs/plans/issue-274.md` の「Eval の回し方」と同じ（`--scaffold --ablation none --no-publish --keep-temp --concurrency 1 --max-cost-usd <N> --trust-plugin`）。

- **陽性対照（A）**: 現行の spec-loop の複製（scratchpad）に、ケース `git-probe` だけを置いた（scaffold は `git init`・コミット・`release-v1` のタグ。prompt は 1 行の Bash を実行して止まれ）。
  - r1（$0.17）: `git --version` → **`git version 2.56.0`**、`git tag` → `release-v1`、`git log` も通った。grader 2 本とも緑。
  - r2（$0.13）: 仕組みを見るため 1 行を差し替えた——`type -a git` → **`/usr/bin/git` だけ**、`ls -la /opt/homebrew/bin/git` は見える、`/opt/homebrew/bin/git --version` → 2.56.0、
    `/usr/bin/git --version` → **2.56.0**（xcrun の警告つき）、`xcrun --find git` → **`/opt/homebrew/bin/git`**。
  - **読み**: サンドボックスの中のシェルは `/usr/bin/git`（xcrun の shim）を選び、shim 越しに動いているのは Homebrew の git（2.56.0。Xcode の git は 2.54.0、
    CommandLineTools は 2.39.5——ホストで確かめた）。**xcrun が `PATH` から見つけて起こすというのは推定**（`/opt/homebrew/bin` を `PATH` から外した対照は無い）。
    `couldn't create cache file .../xcrun_db-*` の行は shim 越し（素の `git`・`xcrun`）の呼び出しのたびに出て、`/opt/homebrew/bin/git` を直に呼んだ行では出なかった。終了コードは 0。
    出力は `2>&1` でまとめたので、どちらの流れに出たかは見ていない。
  - **交絡**: 「git を入れる前は動かなかった」の陰性側は #274 の trace（`Failed to locate 'git'`）で、同じホスト・同じ claude の版。入れた後の陽性側は上の 2 回。
    r1 の grader は素の `git` の出力（版の文字列・タグ名）だけを見るので、素の `git` が動かずに緑になる形は無い。
    **r2 の `git-version-ran` は `/opt/homebrew/bin/git --version` を直に呼ぶ行でも緑になる**（判別するのは `git-tag-read` だけ。版の文字列は Xcode の 2.54.0 にも当たる）——r2 は仕組みを見るための観測で、陽性対照は r1 である（/code-review 1 パス目 R5）。
- **proposal（B）**: 現行の版は PR #830 のブランチ（`45c14912`）の worktree の `plugins/spec-loop`（`git diff 45c14912 053b77c3 -- plugins/spec-loop` は空——マージされた版と同じ）。
  修正前の版は `694fe954`（0.7.0）の `git archive` に現行の `evals/` を写し `FORMAT=0.7`（#274 と同じ作り方）。

| 実行 | 腕 | `check-signoff.py` | draft-written | draft-has-no-change-list | 費用 |
| --- | --- | --- | --- | --- | --- |
| r3 | 現行 | 0（一致する） | 緑 | 緑（PASS×3） | $0.26 |
| r4 | 修正前 | 0（一致する） | 緑 | 緑（PASS×3） | $0.28 |
| r5 | 現行 | 0（一致する） | 緑 | 緑（PASS×3） | $0.25 |
| r5 | 修正前 | 0（一致する。tool_result の `EXIT=0`） | 緑 | 緑（PASS×3） | $0.25 |

- **判別を示せなかった（2 回とも両方の腕が緑。率ではないので「判別しない」とは言わない）。** git は 4 回とも動き、照合を通って下書きまで進んだ——#274 の「照合で止まった赤」は解けた。
- **赤にならなかった理由**: 修正前の版（差分モードが無い）も、下書きを「背景と目的・推奨案とその理由・比較した代替案・リスクと前提条件」の形で書き、
  前の版との差の一覧（追加・変更・削除の列挙）を書かなかった（trace の Write の中身を見た。両方の腕に Q-003 の代替案の表はあるが、差の一覧ではない）。
  0.7.0 の proposal の `SKILL.md` には「一覧は書かない」が無い（現行は 85 行目）——修正前の版は指示が無くても書かなかった。
  **このケースが捕まえる誤り（一覧を手で書く）を、差分モードの入る前の版も起こさない**——grader は差分モードの有無を判別しない。
- 対照: grader の陽性対照は #274（r2・r8）で済んでいる（`draft-written` の赤・`draft-has-no-change-list` の赤）。この周では回していない。

### 陽性対照のケース（r1 の形。リポジトリには置かない——プラグインを外に複製して `evals/git-probe/` に置く）

`case.yaml`:

```yaml
schema_version: "1.1"
name: git-probe
description: >-
  陽性対照（#832）。サンドボックスの中で git が動くかを見るだけ。
tags: [probe]
plugins: ["../.."]
runs: 1
expected_outcome: >-
  git-out.txt に git のバージョンとタグの一覧が書かれる。
execution:
  prompt: "Bash で次の 1 行をそのまま 1 回だけ実行し、ほかには何もせずに止まれ: { echo PATH=$PATH; which -a git; git --version; git tag; git log --oneline -1; } > git-out.txt 2>&1; cat git-out.txt"
  max_turns: 4
  timeout_seconds: 300
  allowed_tools: [Bash]
context:
  scaffold_script: scaffold.sh
graders:
  - name: git-version-ran
    type: regex
    target: {source: file, path: git-out.txt}
    pattern: 'git version 2\.'
    match: contains
  - name: git-tag-read
    type: regex
    target: {source: file, path: git-out.txt}
    pattern: 'release-v1'
    match: contains
```

`scaffold.sh`（`chmod +x`。断る判定は spec-loop の evals の scaffold と同じ）:

```bash
#!/usr/bin/env bash
set -euo pipefail
top=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$(ls -A)" ] || { [ -n "$top" ] && [ "$top" != "$HOME" ]; }; then
  echo "scaffold.sh: eval のワークスペースではない: $PWD — 断る" >&2
  exit 1
fi
git init -q -b main .
git config user.name eval
git config user.email eval@example.invalid
echo probe > README.md
git add -A
git commit -q -m v1
git tag release-v1
```

## 費用（`aggregate-result.json` の `costUsd`。API 換算）

| 実行 | 中身 | 費用 |
| --- | --- | --- |
| r1・r2 | 陽性対照（git-probe） | $0.17 / $0.13 |
| r3・r4 | proposal 現行／修正前 | $0.26 / $0.28 |
| r5 | proposal 現行／修正前 | $0.25 / $0.25 |
| **合計** | | **$1.34**（上限 $27） |

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/832-eval-sandbox-git`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-832`・
  起点 `053b77c3`・base `origin/main` → `053b77c30e68f12fcaf4182dba53e2ae7aab0750`
- 割り目（手順 4 の完了時）: 割らない（不在の cruise）
- 1 パス目: Verifier（`dev-loop:dev-loop-verifier`／sonnet）反証 2 件（軽微。C の記述が観測より強い）・`/code-review`（high）指摘 8 件。1 パス目の起点（先に当てた関門に渡した時点の HEAD）: `9bdbb032`
- 2 パス目: Verifier（sonnet）反証 0 件・所見 2 件／`/code-review`（high）指摘 8 件（下の採否の表）。2 パス目の指摘対応の起点: `3ca2fb6a`・終点: `edc611b6`（狭いパスは `git diff 3ca2fb6a edc611b6`）
- 狭いパス: Verifier（sonnet）に当てる
- 割り目（2 パス目の前）: 割らない（不在の cruise）
- check-all（1 回目、`--jobs 2`・順番待ち越し。`9bdbb032` の上、途中で作業ツリーを直した）: 59 本中 1 本赤——`check-plan-counts.py`（件数の行が無い）。件数の行を足した
- 交絡を潰した手順: 上の「陽性対照（A）」の交絡

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 判別できる試料を探す | 採らなかった | 親の決定（推奨）。#274 の受入基準 B の続きで、この周の範囲の外 |
| proposal のケースを外す | 採らなかった | 親の決定。判別しないことを注記に書いて残す |
| `type -a git` に Homebrew の git が出ない理由を突き止める | 採らなかった | 環境をこれ以上変えない。記述は観測にとどめる |
| #181 の後半・#183（2026-10）では xcrun の行が出ても git が動いた記録がある | 記述に残す（2 パス目で書き直し） | #181 の周の途中（10-04）に人が Homebrew の git を入れた後の回（`docs/plans/issue-181.md`）。#183 はその 2 日後で、Homebrew の git が在ったかは確かめていない |

### 採否の表（1 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1・V2 / R2: CLAUDE.md が仕組み（「xcrun が `PATH` から見つけて起こす」「手当ては `PATH` に入れること」）を事実の形で書く。`PATH` を外した対照は無い | 示せる（r1・r2 の trace は `xcrun --find git` の値と版までで、シェルは `PATH` から見つけていない） | C | 直す（観測の 3 つと「仕組みは推定」に書き直した） |
| R1: case.yaml が 2 回ずつで「判別しない」「修正前の版も起こさない」と断定 | 示せる（計画の未証明「率ではない」・#274 の言い方） | B・D | 直す（「2 回ずつで判別を示せなかった」に） |
| R4: 「時期で違った」は誤った帰属（#181 は切れたリンク・同じ周の中でも揺れた） | 示せる（`docs/plans/issue-183.md`・`issue-181.md` の記録） | C | 直す（「ホストの設定で変わり、同じ周の中でも揺れた」に） |
| R6: 「毎回 stderr に出る」は見ていない（`2>&1` でまとめた） | 示せる（r1・r2 の prompt） | C | 直す（流れは見ていないと書いた） |
| R5: 計画の「git が動かずに緑になる形は無い」は r2 には偽。CLAUDE.md の対照の手順が r2 の形を写すと空振りしうる | 示せる（r2 の prompt） | A（CLAUDE.md の手順の側） | 直す（計画を直し、CLAUDE.md に「素の `git`・タグ名で見る」と書いた） |
| R7: r5 修正前の証拠の書き方が弱い | 示せる（`EXIT=0`） | 無し（計画の記録） | 直した（計画の記録。関門の対象外） |
| R3: ほかの 3 ケースの注記は git が動かない環境での #274 の実測を指したまま | 示せる（#274 の計画） | 無し | 残課題 |
| R8: `docs/plans/issue-274.md` の proposal が BLOCKED のまま・前向きの指し先が無い | 示せる | 無し | 残課題（#274 の周の記録は触らない——変更範囲） |

### 採否の表（2 パス目）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R2-1: 0.7.0 は「変更の提案書」と「一覧は書かない」の両方を持たない（#263 で同時に入った）——比較は守る行を切り分けていない | 示せる（`git show 694fe954:…/proposal/SKILL.md` に「変更の提案書」0 件、`3e932a36` が両方を足す） | B（赤・緑の理由の記録） | 直す（case.yaml の注記と計画の未証明） |
| R2-2: CLAUDE.md の「同じ周の中でも揺れた」は誤った帰属——記録の上では Homebrew の git の有無で分かれる | 示せる（`docs/plans/issue-181.md` の 10-04 の `brew install git`・#274） | C | 直す |
| R2-3: 計画の #183 の行が「時期で違った」のまま | 示せる | 無し（計画の記録） | 直した（計画） |
| R2-4: 計画の「読み」が仕組みを断定・stderr と書く | 示せる | 無し（計画の記録） | 直した（計画） |
| R2-5: 「git を呼ぶたびに出る」は広すぎる（直に呼んだ Homebrew の git では出ない） | 示せる（r2 の trace） | C | 直す |
| R2-6: `scripts/run-dev-loop-evals.py` が xcrun の行を雑音として消し、`Failed to locate` を疑わない | 示せない（この周の実行は git が動いた。git が無いホストでの要約の誤読は起こしていない） | 無し | 残課題 |
| R2-7: 陽性対照のケースが scratchpad にしか無く、手順を再現できない | 示せる（CLAUDE.md の手順にケースの指し先が無い） | C（手順を書く） | 直す（計画に全文、CLAUDE.md から指す） |
| R2-8: 対照は Bash の素の `git` を見るだけで、スクリプトの git の経路は別かもしれない | 示せない（4 回とも `check-signoff.py` は 0） | 無し | 残課題（既定の線。一度 CLAUDE.md に 1 文足したが外した） |
| V2 所見 1: #181 の後半は Homebrew の git が在った回 | 示せる | C | R2-2 と同じ修正 |
| V2 所見 2: 「`/opt/homebrew/bin` は `PATH` に入っていた」が #274 当時のことに読める | 示せない（読み方の指摘） | 無し | 残課題 |

## 経験の還元（手順 8）

- 焼き戻し: CLAUDE.md の「振る舞いを Eval で当てる」に書いたもの（この PR）が焼き戻しを兼ねる。
- 振り分け（`references/found-lines.md`）: R3・R8 は記録だけ（利用者に見える誤りではない・試料と記録の注記の範囲）。PR コメントに書く。

- この周の起票: 0 件（直すに当たる残課題が無い。不在のため起票を訊いていない）
