# Issue #276 — macOS で Removed.csv・Shared/ の扱いがスキルの差分と提案書で食い違う

`merge-versions.py` は版の直下を**決まった名前でパスを組み立てて**読む（`root / "removed.csv"`・`root / "shared"`）。
大文字小文字を区別しないファイルシステム（macOS の既定）では `Removed.csv`・`Shared/` がその名前で開けてしまい、
区別するファイルシステム（Linux）では読まれない。`build-proposal.py` はタグから `git ls-tree` の名前で写すので、
綴りの違う名前を写さない。**同じコミットで、作業ツリーの差分（スキル）と提案書の比較が食い違う。**

直し方は Issue の案のとおり——**綴りだけ違う置き場所の名前を、重ね合わせの側で決まりに反するもの（1）として断る**。
提案書の側はその名前も写して、同じ判定（重ね合わせ）に断らせる。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent` の再開（2026-10-28）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`））。マージはこの周では行わない（親がする）。

直す線: **既定**（出所: cruise の確かめた線（台帳 `issue-474`））

## 変更範囲

触る:

- `plugins/spec-loop/scripts/merge-versions.py` — 版の直下の名前を綴りどおりに読む（`removed.csv`・置き場所）。綴りだけ違う名前を 1 で断る。綴りどおりに在るかを見る口を 1 つ置く（`build-proposal.py` も使う）。docstring
- `plugins/spec-loop/scripts/build-proposal.py` — `merged_reads` が綴りだけ違う名前も写す。`drop_internal` が綴りどおりの名前だけを外す。docstring
- `plugins/spec-loop/references/versions.md` — 決まりの原本に、綴りだけ違う名前は誤りと書く
- `scripts/test-merge-versions.py` — 試料と変異
- `scripts/test-build-proposal.py` — 試料と変異（区別しない FS でだけ判別できる試料・変異は、そう書いて飛ばす）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（5 本）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版 0.33.0 → **0.34.0**（決まりに反する入力が増える＝挙動の変更。0.x なので minor。並行する #291 は 0.35.0 を使う——cruise の親の割り振り）。
  **再開（2026-10-29）で main（0.37.0）を取り込み 0.38.0 に上げ直した**
- `.claude-plugin/marketplace.json` — 同じ版
- `docs/plans/issue-276.md` — この計画

触らない:

- `plugins/spec-loop/scripts/check-signoff.py` — git の名前（綴りどおり）で読むので FS に依らない。`Removed.csv` を照合の範囲に数えないのはどの FS でも同じで、
  提案書は `build-proposal.py` の重ね合わせが断る（下の「既知の限界」）
- `plugins/spec-loop/scripts/diff-versions.py` — `removal_reasons` の `root / removed.csv` は `merge` が通ったあとにしか呼ばれない（綴りだけ違う名前があれば `merge` が 1 で止めている）
- `plugins/spec-loop/scripts/scaffold.py`・`check-spec-exit.py`・`check-frozen.py` — `merge` を使う／重ねた出力（綴りどおりに書く）を読む／git で読む
- `build-proposal.py` の手書き部分（`docs/v<n>/proposal/`）・見積り（`feasibility/`）の読み方——重ね合わせではない（手書き部分は作業ツリーから `Proposal/` を開けうるが、差分と提案書の食い違いではない。残課題）
- 置き場所の中のファイル名の綴り違い（`shared/QA.csv`・`spec/Spec_IR.json`）を断ること——決まりを広げる判断で、この Issue の外（重ねた出力を読む側が区別しない FS でだけ構造ファイルとして読むことは 1 パス目の `/code-review` が示した。#511 に起票）
- description（3 箇所。この挙動を述べていない）

### 同じことを述べている箇所の数

「大文字小文字・正規化だけ違う名前は誤り」: `references/versions.md` の「出力先」（重ねた結果のパス）・`merge-versions.py` の docstring（守らないものの `V2`）・
`build-proposal.py` の docstring（写す前に断る）= **3 箇所**。足すのは「版の直下の名前」の決まりで、正は `versions.md`。
2 本のスクリプトの docstring は挙動の説明として 1 行ずつ足す——分けない（同じ決まりの写しで、片方だけだと読む側が食い違う）。

## 乗るデプロイ経路

プラグイン（`plugins/spec-loop/`）の版を上げてマージ。main への push でサイトが再デプロイされる（`docs/plans/` を足す）。マージは親がする。

## 周の在り処

- ブランチ: `issue/276-removed-case-fold`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-276`
- 起点: `30785f3`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `30785f34038755c69b9fc27f14029d64e1b288a2`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。受入基準はこの表だけである。

不変条件:

- **I1**: 版の直下に、置き場所（`shared`・`requirements`・`spec`）か `removed.csv` と**大文字小文字・Unicode の正規化だけ違う名前**
  （`Removed.csv`・`Shared/` など）があれば、`merge-versions.py` は**ファイルシステムに依らず** 1（決まりに反する）で止め、その名前を名指しする。
  前の出力は消す（1 の既存の扱い）。綴りだけ違う名前の中身を、正しい名前のものとして**読まない**（区別しない FS でも `removed.csv` として削除を当てない）。
- **I2**: 同じコミットについて、作業ツリーで重ねる側（`merge-versions.py`・`diff-versions.py`・`scaffold.py`）とタグから重ねる側
  （`build-proposal.py` の前の版との比較・仕様書）が、I1 の名前で**同じ答え（1）**になる——ファイルシステムに依らない。
  Issue の再現（`docs/v2/Removed.csv` が v2 でも置く `requirements/same.md` を消す）では、どちらも 1。
- **I3**: `build-proposal.py` の比較の前処理（内部の層を外す `drop_internal`）は、**綴りどおりの** `spec/qa-dev.csv`・`removed.csv` だけを外す／書き換える——
  区別しない FS で `spec/QA-dev.csv`（重ね合わせではふつうのファイル）を内部の表として消さない。`diff-versions.py` と提案書の比較の節が一致する。
- **I4**: 綴りどおりの入力の挙動は変わらない——既存の試料（出力の全バイトの期待値を含む）がすべて緑。
- **I5**: 決まりの原本（`references/versions.md`）に I1 の決まりがあり、2 本のスクリプトの docstring が実際の挙動と合う（**書いてあるかではなく、事実か**）。
- **I6**: 版が 3 種類（`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行）で 0.38.0 に揃う（当初 0.34.0。再開で main の 0.37.0 より上へ）。`check-all.py` が緑。PR の CI が緑。

経路（版の直下の名前を読む入口。差分ではなくスクリプトの入口から数える）:

| 経路 | 守り方 | 確かめ方 |
| --- | --- | --- |
| `merge-versions.py` の CLI（作業ツリー） | `Whole.apply` が版の直下を `iterdir` の名前で読み、綴りだけ違う名前を 1 に | 試料（`Removed.csv`・`Shared/`・`Requirements/`・`Spec/`）＋変異。macOS と Linux（CI）の両方 |
| `merge-versions.py` の `removed.csv` の読み（区別しない FS） | 綴りどおりに在るときだけ読む | 試料（`Removed.csv` で削除が当たらない＝問題の行が名前の 1 行だけ） |
| `diff-versions.py`（スキルの差分） | `merge` を使う | 実走（Issue の再現） |
| `scaffold.py`（作業ツリーの全体・前の版の全体） | `merge` を使う | 読む（`merge` の呼び出し） |
| `build-proposal.py` の `copy_docs`（タグ） | `merged_reads` が綴りだけ違う名前も写す→`merge` が断る | 試料（タグの `Removed.csv`・`Shared/`）＋変異 |
| `build-proposal.py` の `drop_internal`（写した一時ディレクトリ） | 綴りどおりの名前だけを外す | 試料（タグの `spec/QA-dev.csv` が比較の節に載る）。**区別しない FS でだけ判別できる**——Linux では旧い実装でも緑 |
| `check-signoff.py`（タグ） | 触らない（git の名前で読む） | 読む（既知の限界） |
| **（再開で追加）** `merge-versions.py` の綴りの照合（git の作業ツリーの中・区別しない FS で作業ツリーのフォルダの綴りがコミットと違う） | `tracked`（`git ls-files`）・`spelled`（同じ項目のときだけ index の綴り） | 試料（`git-stale`・`git-renamed`・`git-both`）＋変異。旧い実装への陽性対照。I2 の実験（作業ツリー対コミットの書き出し） |
| **（再開で追加）** 同（区別する FS で、綴りだけ違う別のフォルダが並ぶ） | `same_entry` が別の項目と見る／`has_content` が `.` だけのフォルダを数えない | 試料（`git-alongside`・`git-stale`）。Case-sensitive APFS のイメージと CI（Linux） |
| **（再開で追加）** git の外の docs・`.git` が在るのに git が失敗する | 外なら作業ツリーの綴り（既存の試料はすべてこの経路）／失敗は 2 | 既存の試料・`git-broken` の試料＋変異 |

証明できるもの／できないもの:

- I1・I2 の判別は、試料を macOS（区別しない）と CI の Linux（区別する）の両方で走らせて見る。**手元は macOS だけ、Linux は CI だけ**。
- I3 の判別は**区別しない FS でだけ**できる（区別する FS では旧い実装でも `spec/QA-dev.csv` を消さない）。手元の macOS で判別し、CI ではその変異を飛ばしたと出す。
- **（再開で追加）未証明**: `GIT_DIR`・`GIT_INDEX_FILE` を設定した環境、sparse checkout・submodule の中の docs——試していない（docstring の「守らないもの」に一部を書いた）
- **未証明**: HFS+（NFD に寄せる FS）での挙動——ASCII の名前は正規化で変わらないので I1 の対象名には効かないが、測っていない。

生成物: **該当なし**——このリポジトリの生成物（図の書き出し・`SKILL.md` の測定値の生成ブロック）はどちらも dev-loop の `SKILL.md`・drawio が源で、
この周は触らない（spec-loop の `SKILL.md` は版の 2 行だけ）。`check-all.py` が `skill-metrics.py --check`・図の鮮度を回すので、そこで確かめる。

必須要件の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目・2 パス目で渡す（4 つの受け渡し。2 パス目が該当なしなら 2 つ）。

## 未解決の判断・確認待ち

- なし（仕様の穴は無い——Issue の案どおりで、利用者に見える結果（綴りだけ違う名前を誤りとすること）は Issue が求めている）

## 関門の進捗（再開点）

- 手順 4: 済（実装コミットは下の「1 パス目の起点」）。割り目: **不在のため訊かず続けた**（出所: `/dev-loop:cruise 474 --absent` の再開・2026-10-28）
- 1 パス目の起点（指摘対応の 0 行判定に使う）: `a28bd000d9eee0f0b91426a475391cff5867112f`（1 パス目の関門に渡した時点の HEAD）
- 1 パス目: **Verifier（sonnet・`dev-loop:dev-loop-verifier`）反証 0 件**（テンプレート 170 行を読んだと報告。`wc -l` は 169——末尾に改行の無い 1 行の差。旧い実装で足した試料が赤になること、case-sensitive APFS のイメージで両テストが緑になることを実測）。
  **`/code-review`（high）指摘 10 件**——採否は下の表。直すのは CR1・CR4 の 2 件（文面だけ）
- 1 パス目の指摘対応: 文面の修正（`merge-versions.py` の docstring・`references/versions.md`）。2 パス目を回す（差分は 0 行でない）。2 つ目の割り目: **不在のため訊かず続けた**。残り: 手順 5 の当て直しと手順 6 の 2 パス目の両方
- 1 パス目の指摘対応のコミット: `47f683a`。**2 パス目の指摘対応の起点（狭いパスの起点）: `47f683a717fe77a33a868dc4b542f037a0a2470b`**
- 2 パス目: **Verifier（sonnet）反証 0 件**（テンプレート 170 行）。**`/code-review`（high）指摘 7 件**——採否は下の「2 パス目の採否の表」。直すのは CR2-4 の 1 件（文面）
- 2 パス目の指摘対応のコミット（狭いパスの終点）: **`a72b57d1a204778219ebd8a44fdcb6d63502628e`**（起点 `47f683a` の子孫であることを確かめた）
- 狭いパス（`47f683a` → `a72b57d`）: **Verifier（sonnet）指摘 0 件**（テンプレート 170 行。変異は文面だけの修正なので当てず、文面の主張を崩す試料 1 件——`spec/Spec_IR.json` だけの版で `scaffold.py --dry-run` が「`spec/spec_ir.json` が無い」——と陽性対照を当てた）。人間が決める行は無い
- `check-all.py --jobs 2`（`a72b57d` の上で計画ファイルをコミットしたあと）: 52/52 本・失敗 0
- 満たしていない受入基準: **I1・I2 の一部**（2 パス目の CR2-1・CR2-2——区別しない FS で作業ツリーのフォルダの綴りが git の綴りと食い違う形）。PR コメントに名指しする
- worktree には `EnterWorktree` で入っていない——cruise の親の指示（`cd` しない・`git -C` と絶対パスだけで作業する）。肯定的な確認は `git -C <worktree>` で当てた（ブランチ・起点とも一致）
- 交絡を潰した手順: 再現の実験（`diff-versions.py` を main の旧い実装と worktree の新しい実装に当てる）は、同じ試料・同じ macOS で、違うのは実装だけ。
  陽性対照: 旧い実装で `Removed.csv` が「置きつつ消している」の 1・`Shared/` が `shared/nfr.csv` の追加として読まれる（区別しない FS の読み方が実際に起きる）ことを見た
- 実装中に見つけた周の外の課題: `drop_internal` は写した一時ディレクトリの `spec` がシンボリックリンク（タグに `docs/v2/spec` をリンクで置く）だと、
  リンク先の `qa-dev.csv` を消す——一時ディレクトリの外のファイルを消す。旧い実装でも新しい実装でも起きる（scratchpad の probe で関数を直接呼んで確かめた）。
  この周の受入基準の外で、`exact` は旧い `os.path.lexists` と同じくリンクを辿る（挙動を変えていない）。手順 8 で振り分ける

### 再開（2026-10-29）——設計を変えて手順 3〜4 を開き直す

- 出所: 確認の Issue #538（推奨で決めた (A)「退行を入れずに直して続ける」。利用者がコメントで「承認します」）と、cruise の親の再開の指示
  （`/dev-loop:cruise 474 --absent` の再開・2026-10-29）。台帳の確かめた線（起動時 2026-10-27T09:07:27Z・再開時 2026-10-28T07:24:46Z・
  2026-10-28T23:56:17Z）: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親）・`周の途中の課題 = 台帳に足して直す`。
  2026-10-29 の利用者の指示: 人の判断が要るものは推奨で決め、要確認の Issue を立てる（#546・#554 の形）
- **受入基準 I1〜I6 は変えない**（I6 の版だけ 0.34.0 → **0.38.0**——main が 0.37.0 に進んだため。版の値は受入基準の中身ではなく、main より上という条件の写し）
- 再開点: **手順 4（設計の変更）から**。そのあと関門を 1 パス目からやり直す（Verifier・`/code-review`・2 パス・狭いパス）。
  前の 2 パスの採否の表は決着済みの論点として残す（CR2-1・CR2-2 は「直せなかった」から、この再開で直す対象になった）
- main の取り込み: `c871d16`（spec-loop の版の衝突 7 ファイルを塊ごとに 0.38.0 で解き、`scripts/test-build-proposal.py` の末尾の集計行は両側を合わせた）。
  取り込む前に `git diff --name-status --no-renames HEAD...origin/main -- scripts/ 'plugins/*/scripts/*'` を見た——足した検査は無い（`M` だけ 11 件）
- **再開後の周の base**: 参照 `origin/main` → 取り込み後の merge-base（下の「再開後の関門の進捗」に SHA を書く）

#### 再開後の関門の進捗（再開点）

- 周の base（再開後）: 参照 `origin/main` → `7a2363955db8ca4842a7c55b961bae4f034adfb2`（取り込み後の merge-base。HEAD の祖先）
- 設計の変更のコミット: `b2754f6`。**再開後の 1 パス目の起点（指摘対応の 0 行判定に使う）: `b2754f6`**（1 パス目の関門に渡す時点の HEAD。計画ファイルの更新はこの後）
- `check-all.py`（`b2754f6` の内容で）: 52/52 本・失敗 0
- 交絡を潰した手順（実験 2 つ）:
  1. **新しい試料（`scripts/test-merge-versions.py`）を旧い実装（PR #517 の head `2e0f8ea`）に当てた陽性対照**——macOS で
     「コミットが正しい綴りなら作業ツリーの古い綴りで断らない」が旧で 1（CR2-1 の退行を再現）、「コミットが綴り違いなら…断る」が旧で 0（CR2-2）。
     新しい実装は全部緑。**区別する FS は Case-sensitive APFS のディスクイメージ（`TMPDIR` をその中に）で測った**——新は緑
     （区別しない FS でだけ作れる試料 2 件と変異「index を見ない」は飛ばしたと出る）、旧は CR2-1 の類型（`.DS_Store` だけの `Requirements/` が並ぶ）で 1
  2. **I2 の実験**——本物の git リポジトリで CR2-1・CR2-2・Issue の再現（`Removed.csv`）を作り、作業ツリーで重ねた終了コードと、
     同じコミットを `git archive` で書き出して重ねた終了コード（タグから写す側が見る綴り）を比べた。新: macOS・区別する FS とも
     `0/0`・`1/1`・`1/1`（一致）。旧: macOS で `1/0`・`0/1`・`1/1`、区別する FS で `1/0`・`1/1`・`1/1`。違うのは実装だけ（同じ試料・同じスクリプト）。
     観測窓: macOS（APFS）と Case-sensitive APFS の 2 つ・各 1 回。Linux の実機は CI だけ。HFS+ は測っていない

- 再開後の 1 パス目: **Verifier（sonnet・`dev-loop:dev-loop-verifier`）反証 1 件**（テンプレート 170 行を読んだと報告。`wc -l` は 169——末尾に改行の無い 1 行の差）。
  **`/code-review`（high）指摘 9 件**。PR の CI（`802f566`、Linux）は緑——区別する FS で新しい試料が通ることも CI で見た
- 再開後の 1 パス目の指摘対応: `tracked` が版の直下のファイル（`v2/removed.csv`）を index から集めていなかった（`len(parts) >= 3`）のを `>= 2` に。
  試料 2 件（`git-renamed-file`。区別しない FS だけ）と変異 1 件を足した。2 パス目を回す（差分は 0 行でない）。2 つ目の割り目: **不在のため訊かず続けた**。
  残り: 手順 5 の当て直しと手順 6 の 2 パス目の両方
- 再開後の 1 パス目の指摘対応のコミット: `994f533`。`check-all.py`: 52 本のうち `check-mutation-claims.py` だけが「当てられなかった」（`test-worktree-scripts.py:341` の陽性対照が 300 秒で打ち切り。load average 約 120）——単独で回し直して 10/10 確認。緑ではないので push 後に全体を回し直す

#### 再開後の 1 パス目の採否の表

直す線: **既定**（出所は上の「再開」）。

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| RV1（Verifier）・RC1（`/code-review`）`tracked` の `len(parts) >= 3` で `v2/removed.csv` が index に入らない——コミットの `Removed.csv` を作業ツリーで `removed.csv` に改名すると 0（書き出しは 1）、逆も食い違う | 示せる（両方の関門が macOS の本物のリポジトリで再現。著者も試料で再現——変異 `>= 3` が新しい試料で赤） | I1・I2・I5 | **直す** |
| RC2 版の直下より深いフォルダ（`requirements/sub/` 対 作業ツリーの `Sub/`）の綴りは作業ツリーのまま——作業ツリーと書き出しが食い違う | 示せる（レビューの実走） | 無し（I1・I2 は版の直下の名前。置き場所の中の綴りは既知の限界の「置き場所の中の綴り違い」と同じ層。旧い実装も同じ） | 残課題（周の途中の課題の候補） |
| RC3 フックの中の相対の `GIT_INDEX_FILE`・`GIT_DIR` で、黙って空の index か 2 | 示せる（レビューの実測） | 無し（docstring の「守らないもの」に書いてあり、I5 の事実と合う） | 残課題 |
| RC4 親に壊れた `.git`・dubious ownership で、綴りの正しい入力が 2 になる（以前は 0） | 壊れた `.git` は示せる（試料 `git-broken` そのもの）。dubious ownership は示せない（推測） | 無し（I4 は既存の試料で測る——すべて緑。2 は設計の選択: 綴りを照合できないときに黙って作業ツリーの綴りに落ちれば CR2-1 が戻る） | 残課題（利用者の判断の候補——git への依存を入れたことの帰結。#538 の補足が予告していた論点） |
| RC5 `diff-versions.py` の `removal_reasons` が `root / removed.csv` を組み立てて開く | 示せない（RC1 を直したあとは `merge` が先に断る） | 無し | 残課題 |
| RC6 テストが RC1・RC2 の形を持たない | RC1 の分は直した（試料 2 件・変異 1 件） | RC1 と同じ | RC1 と一緒に直した。RC2 の分は残課題 |
| RC7 git が無い環境でテストが `FileNotFoundError` で落ち、要約が出ない・`git-both` の env の重複 | 示せない（git の無い環境で走らせていない） | 無し | 残課題 |
| RC8 `merge()` ごとに `git ls-files` を呼ぶ（`diff-versions.py`・`scaffold.py` は 2 回） | 示せない（遅さを測っていない） | 無し | 残課題 |
| RC9 `if REMOVED not in entries: pass` の空の枝 | 示せない（整理） | 無し | 残課題（CR2-7 と同じ） |

#### 選んだ設計（CR2-1・CR2-2 を直す）

**版の直下の名前は git が見る綴りで判定する。** 区別しない FS では、作業ツリーのフォルダの綴り（`iterdir`）がコミットの綴りと食い違いうる
（git は既存のフォルダに書き込むので、`Requirements/` が残っていれば `requirements/same.md` もそこに書かれる）。

- `docs` が git の作業ツリーの中（上へ辿って `.git` が在る）なら、`git ls-files -z` を 1 回呼び、版ごとに直下の名前の index の綴りを集める。
  作業ツリーの名前 `n` が index に無く、index に `fold` が同じ別の綴り `m` が在って、`root/m` と `root/n` が**同じディレクトリ項目**（`lstat` の dev・ino）なら、
  `n` ではなく `m` を名前とする——FS が 2 つを同じものとして開いているとき（区別しない FS）だけ index の綴りに寄る。区別する FS では別の項目なので寄らない。
  index に無い名前（`git add` 前）は作業ツリーの綴りのまま
- git の外（`.git` が見つからない）なら作業ツリーの綴り（いまの挙動）。`.git` が在るのに git が無い・`ls-files` が失敗したら 2（判定していない）
- **綴りだけ違うディレクトリでも、読む名前（`.` で始まらない）のファイルを 1 つも持たなければ数えない**——タグから写す `build-proposal.py` は
  `.` で始まる名前を写さないので、タグの側にもその名前は現れない（区別する FS で、`.DS_Store` だけの古い `Requirements/` が正しい `requirements/` と並ぶ形が 0 になる）
- 選ばなかった案: (a) 作業ツリーの綴りだけで判定（PR #517 の形。CR2-1 の退行）、(b) 綴り違いを断らない（#276 を直さない）、
  (c) `git ls-files --others` で未追跡も git から取る——未追跡のディレクトリの綴りは作業ツリーのものが返る（2026-10-29 に手元で実測: `?? docs/v2/Requirements/.DS_Store`）ので得るものが無い

## 既知の限界・決着済みの論点

- **`check-signoff.py` はタグの `Removed.csv`・`Shared/` を照合の範囲に数えない**——git の名前で読むので FS に依らず同じ答えで、
  提案書は `build-proposal.py` の重ね合わせが 1 で断る（採った: 触らない。理由: この Issue の食い違いは「差分と提案書」で、照合は FS に依らない）。
- **置き場所の中のファイル名の綴り違い（`shared/QA.csv`）は断らない**（採らなかった。理由: 決まりを広げる判断で、この Issue の外。
  **1 パス目に書いていた理由「FS に依らずふつうのファイルとして読まれ、食い違わない」は誤りだった**——重ねた出力を読む `check-spec-exit.py`・`scaffold.py` は
  区別しない FS でだけ構造ファイルとして開く（CR1・CR2）。文面をそう直し、#511 に起票した）。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1 決着の理由が誤り——`shared/QA.csv` は重ねた出力を読む側が区別しない FS で `qa.csv` として開く | 示せる（著者が実走: `merge` 0 → `check-spec-exit.py out/shared/qa.csv out/spec` が「条件 1 を満たす」、macOS） | I5（`versions.md` の「`qa.csv` としては読まない」が全体の事実として読めない） | **直す**（文面を事実に合わせる。挙動は直さない——#511） |
| CR2 `spec/QA-dev.csv` を `check-spec-exit.py`・`scaffold.py` が内部の表として読む | 示せる（レビューの実走。CR1 と同じ形） | 無し（I3 は `drop_internal` の経路） | 残課題（#511 に含めた） |
| CR3 構造ファイルの綴り違いも `merge` で断るべき（高さ） | 示せる（CR1・CR2） | 無し | 残課題（#511 の案） |
| CR4 docstring「`exact` で見る（`build-proposal.py` も使う）」——`merge` は `exact` を使っていない | 示せる（`grep`: `exact(` の呼び出しは `build-proposal.py` の 2 箇所だけ） | I5 | **直す** |
| CR5 `[*AREAS, REMOVED]` の畳んだ集合が 2 箇所にある | 示せない（片方だけ変える変更は起きていない） | 無し | 残課題 |
| CR6 読めない（mode 0311）版のディレクトリで、0 から 2 に変わった | 示せる（著者が実走: 新は 2「読めない」。**旧は 0 で `ファイル 0`——`shared/qa.csv` を黙って落としていた**） | 無し（I4 は既存の試料で測る。旧い挙動は黙って空を作る誤りで、新しい 2 は docstring の「読めない → 2」に合う） | 残課題 |
| CR7 `CASE_FOLD_ONLY` の変異が、区別する FS では「届いていない」の検査より先に飛ぶ | 示せない（壊す箇所の文言はいま 1 回現れる） | 無し | 残課題 |
| CR8 読みのガード（`REMOVED not in entries`・`area not in entries`）が変異に登録されていない | 示せない（レビューの陽性対照で macOS では試料が殺す。Linux では殺せない——登録すると CI で生き残る） | 無し | 残課題 |
| CR9 `ſ` などを畳むと、「区別しない FS でだけ読まれる」の文言が偽になりうる | 示せない（APFS の畳み方を測っていない） | 無し | 残課題 |
| CR10 `merged_reads` が呼ぶたびに畳んだ集合を作る | 示せない（遅さを測っていない） | 無し | 残課題 |
| V1 Verifier: 計画の「Linux は CI だけ」は過小評価（case-sensitive APFS のイメージで手元でも測れる） | 示せる（Verifier の実測） | 無し | 残課題（記録だけ。PR コメントに書く） |

### 2 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1 コミットの綴りは正しいのに、作業ツリーに古い綴りのフォルダ（追跡しない `.DS_Store` が残る）があると、新しい実装は 1（旧は 0・Linux とタグは 0） | 示せる（著者が実走: レビューの `rename4.sh`。`git status` 空・`docs/v2/Requirements` が残り、`merge-versions.py` が 1） | I1・I2（FS に依らない・作業ツリーとタグが同じ答え） | **直せなかった——満たしていない受入基準**（作業ツリーの綴りは git の綴りと食い違いうる。git を使わない `merge-versions.py` では見分けられない。直すには設計を変える） |
| CR2-2 コミットが `docs/v2/Requirements/` でも、作業ツリーのフォルダが `requirements` の綴りなら 0（Linux とタグは 1） | 示せる（著者が実走: `mixed.sh`・`rename2.sh` で 0。旧い実装も 0——後退ではない） | I1・I2 | **直せなかった——満たしていない受入基準**（同上） |
| CR2-3 版ごとに読む側（MkDocs のフック・`check-qa-csv.py` などに渡す綴り）が区別しない FS でだけ `Shared/qa.csv` を読む | 示せる（著者が実走: `hook_probe.py` で `render_qa` が `Q-001` を描く） | 無し（受入基準は重ね合わせの経路） | 残課題（#514 に起票） |
| CR2-4 文面が「`check-spec-exit.py`・`scaffold.py` が構造ファイルとして読む」と言い過ぎ——`spec/spec_ir.json` は `scaffold.py` が重ねた中身の名前で引くので、どの FS でも読まない | 示せる（`scaffold.py:582` の `if IR_PATH not in rendered`） | I5 | **直す**（`a72b57d`） |
| CR2-5 0.x の壊れる変更なのに、移行の手順が `references/` に無い（`CLAUDE.md` の決まり） | 示せる（`versions.md` に移行の節が無い） | 無し（I1〜I6 に無い） | 残課題（#515 に起票） |
| CR2-6 1 の文言の理由「区別しない FS でだけ読まれる」が、CR2-1 の形では原因を取り違えさせる | 示せない（文言の受け取り方） | 無し | 残課題 |
| CR2-7 `exact` と `names` の重複・`if REMOVED not in entries: pass` の死んだ枝 | 示せない（片方だけ変える変更は起きていない） | 無し | 残課題 |
- **`drop_internal` の判別は区別しない FS でだけできる**——CI（Linux）では変異を飛ばしたと出す（緑のふりをしない）。

## 経験の還元（手順 8）

- この周の起票: 4 件（#511・#512・#514・#515。`周の途中の課題 = 台帳に足して直す` の線で「直す」に振り分け、本文に `cruise-found` の印。台帳には親が足す。起票の承認は不在のため訊いていない）
