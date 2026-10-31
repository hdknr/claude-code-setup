# Issue #736（#749 と束ねた周）— 到達の点検の届かない輪の守り・blocked の印の文言・版の取り合いの試料、`_Killed` の表明と `--jobs` の入れ子

`check-unattended-env.py` とその回帰テストを触る 2 件の Issue を、**1 周・1 PR** で扱う（cruise の台帳のまとめ。代表 #736。
`plugins/dev-loop/skills/cruise/references/grouping.md` の「まとめの周」）。周の Issue は #736（worktree・ブランチの名前）。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-11-01）。台帳 `issue-474` の確かめた線:
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`）。利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた））。
加えて利用者の直接の指示（2026-10-29、親から伝達）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、`要確認` の Issue を立てる（#557 の形。この周が自分で立てる。推奨が「マージの前に直す」か「後続で直す」かを各 Issue に書く）。
**#737・#738（確認の Issue）は承認済みで閉じている**——#737 は「判定できない」のまま（この周は触らない）、#738 は「テストを足す」（この周の #736 の 3 つ目）。
マージは親がする（この周は手順 6 の PR・CI の確認・関門 2 パスと狭いパス・手順 8 の件数の行まで）。台帳は書かない（親が書く）。
**実際の台帳 `.claude/plans/cruise-issue-474.json` は読まない・書かない**——テストは一時ディレクトリの台帳だけを使う。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））。
版の上げ方: `dev-loop` の **patch**（`check-unattended-env.py` のコメント・docstring だけが変わる）。

## 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/scripts/check-unattended-env.py` — #736 の 1（`outcome` の輪の守りとコメント）
- `scripts/test-check-unattended-env.py` — #736 の 2・3（試料と変異）、#749 の 1（`_Killed` の表明）・2（`--jobs`）
- `scripts/check-all.py` — #749 の 2（`NESTED` を回帰テストの 2 本にも広げ、`--jobs` を渡す。docstring）
- `scripts/test-check-all.py` — #749 の 2（契約 9 に回帰テストの入れ子を足す・変異 2 つ）
- `scripts/test-ledger.py` — #748 の 2 つ目の項（`MUTANT_JOBS` が `--jobs` に従う）——**`check-all.py` の入れ子の仕組みが 2 本で共有なので、ここで直す**（親の指示: 仕組みが共有なら直す）。#748 の 1 つ目（`_Diverged` の docstring）は触らない → PR は `Refs #748`
- `plugins/dev-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json`・`plugins/dev-loop/skills/dev-loop/SKILL.md`・`plugins/dev-loop/skills/cruise/SKILL.md` — 版
- `docs/plugins/dev-loop-design.md` — `skill-metrics.py` の生成ブロック（変わるなら。手で書かない）
- `docs/plans/issue-736.md` — この計画

触らない:

- 実際の台帳 `.claude/plans/cruise-issue-474.json`
- `reach_items` の版の取り合いの分岐（#737 で「判定できない」のまま承認）
- `ledger.py`（輪を拒むのは既存の `validate`——読むだけ）
- `test-ledger.py` の `_Diverged` の docstring（#748 の 1 つ目——#748 の周に残す）
- 並行の周 #739/#746 のファイル（`run-serial.py`・`scripts/test-run-serial.py`・cruise `SKILL.md` の本文。版の 2 行だけは触る）

### 同じことを述べている箇所の数

- 「輪の守り」: `check-unattended-env.py` の `outcome` の 1 箇所（docstring の「守る」には無い）。
- 「`--jobs 1` なら入れ子まで直列」: `check-all.py` の docstring（2 行）と `NESTED` のコメント、2 本のテストの `MUTANT_JOBS` のコメントと冒頭の用法の行 = 6 箇所（1 パス目の `/code-review` CR1-8 で 4 から直した）。原本は `check-all.py` の docstring。
- 「`_Killed` は `BaseException` の直接の子」: `_Killed` の docstring と `main` の表明 = 2 箇所。
分けない——どれも同じ 2 本のテストと `check-all.py` の 1 つの仕組み。

## 乗るデプロイ経路

プラグイン `dev-loop` の中身（スクリプトのコメントと版）と、リポジトリの `scripts/`（CI の歯止め）——main へのマージでプラグインの新しい版が配られ、サイト（`docs/plans/` を含む）が再ビルドされる。
マージの可否は親（cruise）が決める。

## 周の在り処

- ブランチ: `issue/736-unattended-env-reach-tests`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-736`
- 起点: `7009fd1e`（`origin/main`）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）、SHA `7009fd1eadd5da6e5d38fe3e263dcd18cca13748`

## 受入基準（不変条件 × 経路）

### #736

- A1 `outcome` の届かない輪の守り（`memo` を先に置く行）を消し、輪が来ないことを `ledger.load`（`validate`——行ごとの輪とまとめを 1 つに数えた輪）が保証すると書く。誤ったコメント「手で直した台帳で無限に辿らない」は残らない。
  経路: `reach_items` に台帳を渡す唯一の入口は `lg.load`（ここが拒めば `UNKNOWN` の 1 項目で返り、`outcome` は呼ばれない）。輪のある台帳（行ごと・まとめ越し）を `--cruise --ledger` に渡すと `outcome` に届かず「台帳を読めなかった」になる（実際に走らせて確かめる）。
- A2 `blocked` の行の `note` がコロン無しの「利用者の判断待ち…」のとき、出す文言（「止まっている: 利用者の判断待ち…」——印として出さない）をテストが見る。印をコロン無しでも読む変異を **blocked の分岐だけに**当てると赤になる。
- A3 版の取り合いの数え方の試料（#738 の推奨のとおり）: 閉じた PR と開いた PR が同じ `plugin.json` を触る形（開いた側は進む）・`blocked` の行が PR を持つ形（数えない）・空白だけの PR の欄（進行中の行は PR をまだ作っていないと読む）。`state == "OPEN"` を `!= "MERGED"` に・数える行に `blocked` を足す・`.strip()` を外す変異（番号を読む側と空白だけの欄を見る側の 2 か所）がどれも赤になる。点検の出力（動き）は変えない。

### #749

- B1 `main` の冒頭の表明が `_Killed.__bases__ == (BaseException,)` を見る——`Exception` の子・`KeyboardInterrupt` の子・多重継承のどれに替えても FAIL になり、FAIL の文言が事実（親）と合う。いまの `_Killed` では通る。
- B2 `check-all.py --jobs 1` なら `test-check-unattended-env.py` は変異を 1 つずつ当てる（作業者 1）。経路: `check-all.py` の回帰テストの起動（`TESTS` の 1 本として）・手で `--jobs N` を渡す・何も渡さない（既定 4 を上限に CPU の数）。`--jobs 0` は断る。
  `test-ledger.py` も同じ（#748 の 2 つ目。共有の仕組み）。`test-check-all.py` が「渡すこと」「親が 1 なら 1」「渡さないテストには何も足さない」を見て、渡さない変異が赤になる。

### 掛け算

- 両方の関門 × 2 パス × 上の全基準（A1〜A3・B1・B2）。2 パス目にも全部渡す。

### 未証明・BLOCKED

- 未証明: 無し。BLOCKED: 無し（すべて一時ディレクトリの試料とテストで確かめられる）。

### 生成物

- `skill-metrics.py` の生成ブロック（`SKILL.md` の版の行だけ変わる——行数は変わらない見込み。`--check` で確かめる）。図の書き出し: 無し。

## 未解決の判断・確認待ち事項

- 無し（#737・#738 は承認済み）。

## 関門の進捗（再開点）

- 実装: 済み（check-all 57/57・`test-check-unattended-env.py` の変異 128 件が全部赤（4 並列）・`test-check-all.py` 緑）
  - 輪の守りを外したら、既存の変異「まとめの中の依存も待つ」が止まらずに辿って `RecursionError` で変異テスト全体を落とした——
    正しい本体では届かない（まとめの中の依存を数えないので）。変異の作業者が `RecursionError` を赤に数えるようにした（`_mutant_killed`）
- 割り目（手順 4）: 不在の周なので訊かない（`absent-lines.md`「訊く場面」）。このまま続ける
- PR: #755（作成時の先端 `1375315c`）
- 1 パス目: 済み（1 パス目の指摘対応の起点 `1375315c`——関門に渡した時点の HEAD。コミット済み）。base は `7009fd1eadd5da6e5d38fe3e263dcd18cca13748`
  - Verifier（`dev-loop:dev-loop-verifier`・sonnet。テンプレート 170 行・基準 43 行と報告）: **反証 0 件**。A2・A3 の 5 変異が赤、`test-check-all.py` 緑、`--jobs 0` を両テストが断る、生成物は最新。`test-ledger.py` の全体と `check-all.py --jobs 1` の実走は回していない（報告に明記）。porcelain は前後同じ
  - `/code-review`（high）: 指摘 8 件。採否は下の「1 パス目の採否」（直す 1・残課題 6・計画の数え直し 1）。A1 は `validate` を外した `ledger.py` で `RecursionError` になる陽性対照つきで判別を確かめた。porcelain は前後同じ
  - 指摘対応: CR1-1（`check-all.py` の docstring）。差分は 0 行でない → 2 パス目あり
- 割り目（2 パス目の前）: 不在の周なので訊かない。このまま続ける。残り: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方

## 交絡の扱い

- 実験（A1）: 一時リポジトリに台帳を書き、`reach_items` を直に呼んだ（`i736-cycle.py`）。行ごとの輪（1 ⇄ 2）と、まとめ越しの輪（まとめ {1,2}・1 → 3 → 2）の
  どちらも「台帳 … を読めなかった（台帳の中身が崩れている…）」の 1 項目で返り、到達の行が 1 つも出ない（`outcome` に届かない）。
  **陽性対照**: 輪の無い台帳（2 → 1）では到達の行が 2 つ出る。main の本体（守りあり）でも同じ 3 つの出力——守りが効く台帳は `load` を通らない。
- 実験（A2・A3）: 新しい試料を外した写し（`i736-ab/`。リポジトリの外）で、新しい 5 つの変異を当てると **5 つとも緑のまま**、試料を足した本体では 5 つとも赤
  ——試料が変異を判別している（試料を外しても元の本体は全シナリオ緑）。
- 実験（B1）: `_Killed` の親を `Exception`・`KeyboardInterrupt`・`SystemExit` に替えたクラスで、新しい表明はどれも落ち、古い式は後の 2 つを通した。

## 既知の限界・決着済みの論点

- #737: 版の取り合いは「判定できない」のまま（承認済み）——この周は変えない。
- テストの `--jobs` は上限 4 で切る（入れ子の値が 4 を超えても #494 で決めた重さを超えない）。`--jobs 8` を手で渡しても 4。
- `test-ledger.py` の `_Diverged` の docstring（#748 の 1 つ目）はこの周の外。

## 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1 `check-all.py` の docstring「`--jobs 1` なら入れ子まで直列」は、`test-check-mutation-claims.py` が中で `check-mutation-claims.py` の `main` を既定の `--jobs`（CPU の数）で回すので偽のまま | 示せる——`test-check-mutation-claims.py` 441〜446 行の `observe` は `--jobs` を渡さず `mod.main([*args, root])`、513・596・655 行は `--jobs 2` を直書き | B2（docstring が事実になる） | 直す——docstring を、`--jobs` を受ける入れ子（`NESTED` の 3 本）と、並列の振る舞いそのものを試すので中で並列に回すテスト（`test-check-mutation-claims.py`・`test-check-all.py`）に分けて書く |
| CR1-2 テスト側が受けた `--jobs` を使うかを回帰テストが見ない（`max_workers=jobs` を戻しても緑） | 示せる（変異が素通り——レビューの読み） | 無し（いまの振る舞いは `--jobs 1` で「1 並列」と出る。B2 の振る舞いは満たす） | 残課題 |
| CR1-3 輪のある台帳が「読めなかった」になることを固定する試料が `test-check-unattended-env.py` に無い（`validate` を外すと `RecursionError`） | 示せる（`validate` を外した写しで `RecursionError`——レビューの実験） | 無し（A1 は守りを外して保証を書くこと。輪の台帳は今の `load` で拒まれる） | 残課題 |
| CR1-4 入れ子を半分にする規則を 2 本のテストにも当てたので `--jobs 2〜7` で並列が 1〜3 に下がり、docstring の wall の実測値は変更前の値 | 示せない（wall を測っていない） | 無し | 残課題 |
| CR1-5 2 本のテストで同じ仕組みを違う形（`global` とローカル）で書いた | 示せない（振る舞いの差は無い） | 無し | 残課題 |
| CR1-6 `_mutant_killed` が `RecursionError` を無条件に赤と数える（将来ループにすればハング） | 示せない（将来の形） | 無し | 残課題 |
| CR1-7 `test-check-all.py` の `nested_args` が `main` を 7 回回す | 示せない（時間を測っていない） | 無し | 残課題 |
| CR1-8 計画の「同じことを述べている箇所の数」が 4 でなく 6 | —（計画ファイルは関門の検査の外） | 無し | 計画を直す（成果物ではない） |

## 手順 8

- この周の起票: 0 件（関門の前。起票は手順 8 の振り分けで決める。起票の承認は不在のため訊いていない）
