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
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版 0.33.0 → **0.34.0**（決まりに反する入力が増える＝挙動の変更。0.x なので minor。並行する #291 は 0.35.0 を使う——cruise の親の割り振り）
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
- **I6**: 版が 3 種類（`marketplace.json`・`plugin.json`・spec-loop の全 `SKILL.md` の 2 行）で 0.34.0 に揃う。`check-all.py` が緑。PR の CI が緑。

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

証明できるもの／できないもの:

- I1・I2 の判別は、試料を macOS（区別しない）と CI の Linux（区別する）の両方で走らせて見る。**手元は macOS だけ、Linux は CI だけ**。
- I3 の判別は**区別しない FS でだけ**できる（区別する FS では旧い実装でも `spec/QA-dev.csv` を消さない）。手元の macOS で判別し、CI ではその変異を飛ばしたと出す。
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
- worktree には `EnterWorktree` で入っていない——cruise の親の指示（`cd` しない・`git -C` と絶対パスだけで作業する）。肯定的な確認は `git -C <worktree>` で当てた（ブランチ・起点とも一致）
- 交絡を潰した手順: 再現の実験（`diff-versions.py` を main の旧い実装と worktree の新しい実装に当てる）は、同じ試料・同じ macOS で、違うのは実装だけ。
  陽性対照: 旧い実装で `Removed.csv` が「置きつつ消している」の 1・`Shared/` が `shared/nfr.csv` の追加として読まれる（区別しない FS の読み方が実際に起きる）ことを見た
- 実装中に見つけた周の外の課題: `drop_internal` は写した一時ディレクトリの `spec` がシンボリックリンク（タグに `docs/v2/spec` をリンクで置く）だと、
  リンク先の `qa-dev.csv` を消す——一時ディレクトリの外のファイルを消す。旧い実装でも新しい実装でも起きる（scratchpad の probe で関数を直接呼んで確かめた）。
  この周の受入基準の外で、`exact` は旧い `os.path.lexists` と同じくリンクを辿る（挙動を変えていない）。手順 8 で振り分ける

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
- **`drop_internal` の判別は区別しない FS でだけできる**——CI（Linux）では変異を飛ばしたと出す（緑のふりをしない）。

## 経験の還元（手順 8）

- この周の起票: 2 件（#511・#512。`周の途中の課題 = 台帳に足して直す` の線で「直す」に振り分け、本文に `cruise-found` の印。台帳には親が足す。起票の承認は不在のため訊いていない）
