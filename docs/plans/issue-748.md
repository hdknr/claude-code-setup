# Issue #748（#750・#761・#762 と束ねたまとめの周）— 変異の作業者の数の試料・輪のある台帳の試料・`_Diverged` の docstring・CI の走査の環境変数と継続行

cruise（`/dev-loop:cruise 474 --absent`。2026-11-01 に再開）の子として回す、まとめの周（`ledger.py group` で代表 #748）。
まとめの周の回し方は cruise の `references/grouping.md` の「まとめの周」を正とする。

出所（線）: 利用者の確認（起動時・2026-10-27T09:07:27Z）＋（再開時・2026-10-28T07:24:46Z）＋（再開時・2026-10-28T23:56:17Z、配布を見せて確かめた）——
`仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`。
利用者の指示（2026-10-29）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決め、確認の Issue（ラベル `要確認`・#557 の形・本文の先頭 `<!-- cruise-decision: #474 -->`）を立てる。
要確認 #752・#753・#754（PR #747 の狭いパスの指摘）は、その推奨のとおりに扱う——#752 は直す、#753 は試料を足す、#754 はこのまま受け入れる（直さない。docstring の「守らない」に書く）。

## 変更範囲

触る:

- `scripts/test-ledger.py` — #748 の 1（`_Diverged` の docstring の理由・その表明）、#762（受けた `--jobs` をプールが使うかの試料）
- `scripts/test-check-unattended-env.py` — #761 の 1（行ごとの輪・まとめ越しの輪の試料と、試料が判別することの陽性対照）・2（受けた `--jobs` をプールが使うかの試料）
- `scripts/test-check-all.py` — #750 の 1（環境変数で狭める形）・2（docstring の #155 の一覧に `full_runs`）、#752（空行を挟んだ継続行の試料）・#753（深い字下げのコメント行の試料）
- `docs/plans/issue-748.md` — この計画

触らない:

- `plugins/` 配下（`check-unattended-env.py`・`ledger.py` を含む）——#761 の題は本体も挙げるが、直すのは試料だけで本体は変えない。**プラグインを触らないので版は上げない**（CLAUDE.md: `scripts/` だけの変更は版を上げない）
- `scripts/check-all.py`——#748 の 2 つ目の項（`MUTANT_JOBS` が `check-all.py --jobs 1` に従う）は PR #755 で直っている（下の「#748」の 2）。触らない
- #754 の 2 つの形（`- run:` の次の行の深い `name:`・`&&` で終わる行）の判定——受け入れる（直さない）

### 同じことを述べている箇所の数

- 「受けた `--jobs` を変異の作業者の数に使う」: `test-ledger.py` と `test-check-unattended-env.py` の 2 箇所（各ファイルの `MUTANT_JOBS` の注釈）。
  **分けない理由**: 2 本は別々の本体を当てる別々のテストで、プールも別。試料は各ファイルで自分のプールを見る（片方にまとめると、もう片方の配線を見ない）。
- `full_runs` の守る／守らない: `test-check-all.py` のモジュールの docstring と `full_runs` の docstring の 2 箇所。**分けない理由**: モジュールの docstring は CI の走査の全体（#155）の一覧で、`full_runs` の docstring は関数の詳細。
  モジュールの側は一覧を持ち、関数の側の詳細と食い違わないようにどちらも直す。
- `_Diverged`（test-ledger）と `_Killed`（test-check-unattended-env）の「`Exception` の子にしない」: 2 箇所。`_Killed` は #749 で既に「将来への備え」と正しく書いてある。`_Diverged` をそれに揃える。

## 乗るデプロイ経路

`scripts/` と `docs/plans/` だけ。**プラグインの配布は起きない**（版を上げない）。
`docs/plans/` は mkdocs のサイトに載る（main への push で GitHub Pages）——計画ファイルの公開だけで、利用者の手順は変わらない。

## 周の在り処

- ブランチ: `issue/748-test-scaffold-followups`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-748`
- 起点コミット: `3ba84080`（origin/main）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `3ba84080b22af474d79f2b078a07b4a613a02db7`

## 受入基準（不変条件 × 経路）

### #748（`scripts/test-ledger.py`）

- **A1**: `_Diverged` の docstring の理由が事実と合う——`o[...]` への書き込みは `run` の `try` の外にあり、`scenario` の `except (…)` は列挙した型の子しか捕まえない。
  いまの経路に `_Diverged` を飲む節は無く、「`Exception` の子にしない」は将来への備え（`_Killed` と同じ）と書く。
  経路: docstring の各主張（`run` の `try` の範囲・`scenario` の各 `except` の型・`_kill_one` の `except` の順）をコードで指せること。
  **その備えを表明で見る**——`_Diverged` の親を `BaseException` のほかに替えると赤になる（`_Killed` の表明と同じ形）。
- **A2**（#748 の 2 つ目の項。PR #755 で直った——確かめてチェックを付ける）: `check-all.py --jobs 1` が `test-ledger.py` に `--jobs 1` を渡し、`test-ledger.py` が変異のプールをその数で作る。
  経路: `check-all.py` の `NESTED`・`nested_jobs`、`test-ledger.py` の `main` の書き換えと `kill_mutations` のプール、`check-all.py` の docstring の `--jobs 1` の記述。

### #762（`scripts/test-ledger.py`）

- **B1**: 受けた `--jobs` を変異のプールの作業者の数に使っていることを、テスト自身の試料が見る。**`main` の書き換える行を消すと赤になる**（陽性対照。時間に依らない）。
  経路: `--jobs` を受ける `argparse` → 上限で切る → `MUTANT_JOBS` → `kill_mutations` のプール。どこを切っても赤（書き換える行を消す・上限で切らない・プールが別の値を使う）。
  **CI は引数なしで回す**ので、試料は自分で `--jobs` を付けて自分を起こす（CI の起こし方に依らず判別する）。

### #761（`scripts/test-check-unattended-env.py`）

- **C1**: 輪のある台帳——**行ごとの輪**（1 → 2 → 1）と**まとめ越しの輪**（まとめ {1, 2} → 3 → 2。行ごとには輪が無い）——が、到達の点検で「台帳を読めなかった」の **1 項目だけ**になることを試料で固定する。
  **陽性対照**: `ledger.py` の `load` の `validate` を外した写しでは、同じ試料がどちらも 1 項目にならない（`RecursionError` で止まらない）ことをテストの中で見る——試料が輪を判別していることの証明。
  経路: `gather(cruise=True, ledger=…)` → `reach_items` → `ledger.load`（`validate` の `find_cycle` 2 回）。
- **C2**: 受けた `--jobs` を変異のプールの作業者の数に使っていることを、テスト自身の試料が見る。**`max_workers=jobs` を `MUTANT_JOBS` に戻すと赤になる**（陽性対照。時間に依らない）。B1 と同じ形。

### #750（`scripts/test-check-all.py`）＋ 要確認 #752・#753・#754

- **D1**: `full_runs` が、環境変数で狭める形（`run: PART=scan python3 scripts/test-x.py`。`env`・`export` を前に置く形も）を「全部」に数えない。合成試料（`SAMPLE_CI`）と契約（`scan_contract`）と判別の変異（`SCAN_MUTANTS`）で固定する。
- **D2**: モジュールの docstring の「CI の走査が、何を守り、何を守らないか（#155）」に、`full_runs` の保証（回帰テストを引数なしで回す——#687）と守らないもの（`|| true`・#754 の 2 つの形・`run:` の行より浅い継続・環境変数の判定の偽陽性）が書いてある。`full_runs` の docstring と食い違わない。
- **D3**（#752）: `run:` の行と継続行のあいだに空行がある形を試料にし、「すぐ次の行だけを見る」変異を契約が捕まえる。
- **D4**（#753）: `run:` の次の行が深い字下げのコメントの行である形を試料にし、「コメントの行も継続と読む」変異を契約が捕まえる。
- **D5**（#754）: 受け入れる——判定を変えない。D2 の docstring に「誤って赤になる（偽陽性）2 つの形」として書く。

### 掛け算

- A〜D の全 Issue の受入基準を、Verifier と `/code-review` の両方に、1・2 パス目とも渡す（2 × 2 = 4 つの受け渡し）。
- 「時間に依らない」（B1・C2）× 両方の試料: どちらの試料も、作業者の数を、プールに渡した値（設定）で見る——作業者が実際に何体起きたか（時間で変わる）は見ない。
- 「CI は引数なしで回す」× B1・C2: 試料は CI の起こし方に依らず判別する（自分で `--jobs` を付けて自分を起こす）。

### 未証明・BLOCKED

- 未証明: なし。
- BLOCKED: なし。
- 限界（受入基準ではない）: 1 コアの環境では上限が 1 なので、B1・C2 の `--jobs 1` の試料は書き換えの有無を判別できない（どちらも 1）。CI（ubuntu-latest）と手元（10 コア）は 2 以上。

### 生成物

生成物なし——触るのは `scripts/` の回帰テストと計画ファイルだけで、図の書き出し（`diagrams/exports.json`）・`SKILL.md` の測定値（`skill-metrics.py`）のどちらの元にも当たらない。

## 未解決の判断・確認待ち事項

- なし（#752〜#754 は推奨のとおり扱う——上の冒頭）。

## 関門の進捗（再開点）

- 実装: 済（`82dde0e0`）
- 割り目（手順 4）: 不在の周なので訊かない（`references/absent-lines.md` の「訊く場面」）。続ける。
- Verifier 1 パス目: 済——反証 1 件（V1-R1。CR1-1 と同じ）と注 1 件。起動したのは `dev-loop:dev-loop-verifier`（報告にツールの制約どおり書き込みなし）
- `/code-review` 1 パス目: 済——指摘 6 件（直す 3・残課題 3。下の採否の表）
- 1 パス目の指摘対応の起点: `82dde0e00abb8c333755d3f4ece844eac3fa3db2`（1 パス目の関門に渡した時点の HEAD）
- Verifier 2 パス目: 未
- `/code-review` 2 パス目: 未
- 狭いパス: 未
- 反証と差し戻し: なし（まだ関門に当てていない）
- 交絡を潰した手順: 下の「交絡の扱い」

## 交絡の扱い

実験は 4 つ。どれも「主張が偽でも同じ出力が出る設定」を候補に挙げ、陽性対照で潰した（窓: 2026-11-01、10 コアの macOS、python3 3.14）。

1. **`--jobs` の試料（B1・C2）が判別しているか**——緑は「配線が正しい」でも「試料が何も見ていない」でも出る。
   陽性対照: scratch の写しに変異を当てて `--check-pool` を回した。`test-ledger.py` は 書き換えの行を消す・上限で切らない・プールが `MUTANT_JOBS_MAX` を使う・
   `_MutantPool` を素の `ProcessPoolExecutor` に戻す・`_Diverged` を `Exception` の子にする、の 5 つがすべて赤（rc=1。名指しした表明が落ちた）。
   `test-check-unattended-env.py` は `max_workers=MUTANT_JOBS`・上限で切らない・`--pool-size` が `run_mutants` を通らない、の 3 つが赤。
   **時間に依らない**: 見ているのはプールに渡した数（`_MutantPool.__init__` の引数）で、作業者は 1 体も起きない（変異 0 件のプール）。
   **限界**: 上限が 1 の環境では `--jobs 1` の回が判別しない（どちらも 1）。
2. **輪の試料（C1）が輪を判別しているか**——「1 項目」は輪でなくても読めない台帳なら出る。
   陽性対照: `ledger.py` の `load` の `validate(data)` を `pass` にした写しで `suite` を回すと、2 つの試料の表明が両方とも赤。
   `find_cycle(contracted)` だけを消した写しでは、まとめ越しの輪（cyc-group）だけが赤で、行ごとの輪は緑——まとめ越しの試料はまとめを 1 つに数える検査を判別している。
   テストの中にも同じ陽性対照（`validate` を外した写しでは 1 項目にならない）を置いた。
3. **CI の走査の試料（D1・D3・D4）**——新しい 3 つの判別の変異は、それぞれ自分の契約の行だけを破った（`#752` → 空行の行、`#753` → コメントの行、`#750` → 環境変数の 2 行）。
   実物の `.github/workflows/*.yml` に当てた `--part registry` は緑（環境変数の判定が既存のステップを誤って赤にしない）。
4. **docstring に書いた「守らない」の振る舞い（D2）**——`full_runs` に 6 つの形を当てて確かめた: `|| true` は全部、`- run:` の次の深い `name:` は全部でない、
   `&&` で終わり次の行に続く形は全部でない、`echo a=b && …` と `-X utf8=1` は全部でない（偽陽性）、名前の後ろの環境変数は全部。
   YAML の読み方は PyYAML 6.0.3（`.venv`）で確かめた: 空行を挟んだ深い行は同じ値の続き、深い `#` の行はコメント、`run:` の行より浅い（`run` の列にそろえた）継続は読めない。

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `--jobs` の試料が見るのは「プールに渡した作業者の数」で、実際に起きた作業者の数ではない | 採った | 実際に起きた数は時間で変わる（親の指示: 時間に依らない）。プールは渡した数を上限に起こすので、渡した数を見れば上限が決まる |
| #761 の題が本体 `check-unattended-env.py` を挙げる | 本体は触らない | 項目はどちらも試料（テスト）の話で、本体の振る舞いは変えない |
| #754 の 2 つの形を直さない | 採らなかった（直さない） | 要確認 #754 の推奨（受け入れる）。誤って赤になる向きで、黙って見落とさない |
| 版を上げない | 採った | `plugins/` を触らない（CLAUDE.md） |

## 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1-1: `test-check-unattended-env.py` の `--pool-size` は `run_mutants([], jobs)` を別の行で呼ぶので、`main` の本物の呼び出し `run_mutants(mutants, jobs)` を `MUTANT_JOBS` に替えても `--check-pool` が緑 | 示せる（レビューが写しで実走: rc=0） | C2 | 直す |
| CR1-2: `full_runs` は `run:` の行の環境変数しか見ない——ステップ・ジョブの `env:`・前のステップの `$GITHUB_ENV` で狭める形は全部に数えるのに、docstring の「守らない」に無い | 示せる（`full_runs` に当てて `{'test-a.py'}`） | D2 | 直す（「守らない」に書く） |
| CR1-3: C1 の陽性対照が `!= got` だけで、`RecursionError` を表明していない（無関係な理由で違っても通る） | 示せない（いまは両方とも `RecursionError`——「将来 ledger.py が…」） | 無し | 残課題 |
| CR1-4: 引用した `run:` の値（`run: "python3 scripts/test-a.py"`）は引数なしでも全部に数えない（偽陽性）のに、docstring の偽陽性の一覧に無い | 示せる（`full_runs` に当てて `set()`） | D2 | 直す（「守らない」に書く） |
| CR1-5: `test-ledger.py --check-pool` が「台帳のテスト: すべて合格」と出す（全部を回していないのに） | 示せる（実走） | 無し | 残課題 |
| CR1-6: `_MutantPool`・`check_pool_size`・`report` が 2 本に写しで、既にずれている | 示せない（ずれは書き方の違いで、失敗ではない） | 無し | 残課題 |
| V1-R1（Verifier 1 パス目）: CR1-1 と同じ——`main` の `run_mutants(mutants, jobs)` を `MUTANT_JOBS`・`opts.jobs` に替えても `--check-pool` が緑 | 示せる（Verifier が写しで実走） | C2 | 直す（CR1-1 と同じ修正） |
| V1-注: `_Diverged` の docstring の「`o[...]` への書き込みは `run` が返った後（`try` の外）」は、狭い `try/except (…)` の中の書き込みもあるので表現が緩い（結論は正しい） | 示せない（誤りではない） | 無し | 残課題 |

## 手順 8

（振り分けは関門の後に書く）

- この周の起票: 0 件（関門の前。振り分けの後に書き直す）
