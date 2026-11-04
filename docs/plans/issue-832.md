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
**BLOCKED**: 無し。

生成物: **該当なし**——Eval の結果は scratchpad（`results/` は `.gitignore`）。図・`SKILL.md` の測定値の生成ブロックに触れない（`SKILL.md` は版の 2 行だけ。`skill-metrics.py --check` は check-all に入っている）。

## Eval の回し方と結果（claude 2.1.318・2026-11-04・メインの作業ツリーを cwd にした親の体から）

共通の引数は `docs/plans/issue-274.md` の「Eval の回し方」と同じ（`--scaffold --ablation none --no-publish --keep-temp --concurrency 1 --max-cost-usd <N> --trust-plugin`）。

- **陽性対照（A）**: 現行の spec-loop の複製（scratchpad）に、ケース `git-probe` だけを置いた（scaffold は `git init`・コミット・`release-v1` のタグ。prompt は 1 行の Bash を実行して止まれ）。
  - r1（$0.17）: `git --version` → **`git version 2.56.0`**、`git tag` → `release-v1`、`git log` も通った。grader 2 本とも緑。
  - r2（$0.13）: 仕組みを見るため 1 行を差し替えた——`type -a git` → **`/usr/bin/git` だけ**、`ls -la /opt/homebrew/bin/git` は見える、`/opt/homebrew/bin/git --version` → 2.56.0、
    `/usr/bin/git --version` → **2.56.0**（xcrun の警告つき）、`xcrun --find git` → **`/opt/homebrew/bin/git`**。
  - **読み**: サンドボックスの中のシェルは `/usr/bin/git`（xcrun の shim）を選ぶが、xcrun が Xcode の実体を読めず、`PATH` から Homebrew の git を見つけて起こしている。
    動いているのは Homebrew の git（2.56.0。Xcode の git は 2.54.0、CommandLineTools は 2.39.5——ホストで確かめた）。
    `couldn't create cache file .../xcrun_db-*` の警告は毎回 stderr に出るが、終了コードは 0。
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
- check-all（1 回目、`--jobs 2`・順番待ち越し。`9bdbb032` の上、途中で作業ツリーを直した）: 59 本中 1 本赤——`check-plan-counts.py`（件数の行が無い）。件数の行を足した
- 交絡を潰した手順: 上の「陽性対照（A）」の交絡

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 判別できる試料を探す | 採らなかった | 親の決定（推奨）。#274 の受入基準 B の続きで、この周の範囲の外 |
| proposal のケースを外す | 採らなかった | 親の決定。判別しないことを注記に書いて残す |
| `type -a git` に Homebrew の git が出ない理由を突き止める | 採らなかった | 環境をこれ以上変えない。記述は観測にとどめる |
| #183（2026-10）では xcrun の警告つきで git が動いた記録がある（`docs/plans/issue-183.md`） | 記述に残す | 同じホストでも xcrun 越しに動くかは時期で違った。どの git が動いたか・原因は確かめていない |

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

## 経験の還元（手順 8）

- 焼き戻し: CLAUDE.md の「振る舞いを Eval で当てる」に書いたもの（この PR）が焼き戻しを兼ねる。
- 振り分け（`references/found-lines.md`）: R3・R8 は記録だけ（利用者に見える誤りではない・試料と記録の注記の範囲）。PR コメントに書く。

- この周の起票: 0 件（直すに当たる残課題が無い。不在のため起票を訊いていない）
