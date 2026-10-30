# Issue #514 — spec-loop: 版ごとに読む側が、区別しない FS でだけ綴り違いの置き場所（`Shared/qa.csv`）を読む

cruise #474（`--absent`、2026-10-31 に再開）の子の周。#276 の `/code-review` 2 パス目から出た課題（`<!-- cruise-found: #474 -->`）。

**使った線と出所**: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
——出所: cruise の台帳 `issue-474` の確かめた線（利用者の確認: 起動時 2026-10-27T09:07:27Z ＋ 再開時 2026-10-28T07:24:46Z ＋ 再開時 2026-10-28T23:56:17Z、配布を見せて確かめた）。
加えて利用者の直接の指示（2026-10-29）: 人の判断が要る項目（狭いパスの指摘を含む）は推奨で決めて `要確認` の Issue を立てる。
**マージは親（cruise）がする**——この周は PR・CI・関門・手順 8 まで。台帳は親が書く（この周は書かない）。
**不在の周なので、割り目（手順 4・6）と起票の承認は訊かない**（`references/absent-lines.md` の「訊く場面」）。

**再開の探索**（`find-cycle.py 514`）: 当たったのは [5] の `eb23f07`（PR #660 のコミット本文の `Refs #514`）だけ——#514 の計画ファイル・ブランチ・worktree は無い。**新規の周**と判定した。

## 変更範囲

触る:

- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — 版の中の `shared/qa.csv`・`shared/decision_table.csv` を書いた綴りで探し、綴りだけ違う項目を名指しして読まない（`render_qa`・`render_decision_table`・`qa_numbers`）。`fold` の写し・docstring
- `plugins/spec-loop/scripts/check-qa-csv.py` — 綴りの確かめ（`misspelled`）と `fold` の写し。CLI の入口（`main`）でだけ当てる——`check()` には入れない（`merge-versions.py` の `read_qa` が index の綴りのパスで `check()` を呼ぶ。#569）
- `plugins/spec-loop/scripts/qa-to-pptx.py` — CLI の入口で `qa.misspelled` を当てる
- `plugins/spec-loop/scripts/check-feasibility-csv.py` — CLI の入口で当てる（`check-qa-csv.py` を読み込む）
- `plugins/spec-loop/scripts/schedule-to-gantt.py` — CLI の入口で当てる（版ごとの `feasibility/schedule.csv` を読む同じ形。Issue の列挙には無いが、`versions.md` の「その版だけを読むもの」にある——経路を入口一覧から数えた結果）
- `plugins/spec-loop/references/versions.md` — 版ごとに読む側の決まり（名指しして止まる）・「綴りの誤りの移行」の 3（作業ツリーにだけ古い綴り）に読む側が止まることを書く・フックの取り込み
- `plugins/spec-loop/references/tree.md` — フックを取り込む版の注（0.44.0）
- `scripts/test-check-qa-csv.py` — 試料・変異・写しの突き合わせ
- `scripts/test-qa-to-pptx.py` — 試料・変異
- `scripts/test-check-feasibility-csv.py` — 試料・変異
- `scripts/test-schedule-to-gantt.py` — 試料・変異
- `scripts/test-init-mkdocs.py` — 試料・変異・写しの突き合わせ
- `plugins/spec-loop/scripts/build-proposal.py` — `read_hand` で綴りを確かめる（1 パス目の CR1 の指摘対応で広げた）
- `scripts/test-build-proposal.py` — 手書き部分の綴りの試料と変異（同上）
- `.github/workflows/plugins.yml` — 区別しない FS（ext4 の casefold）の段で `test-init-mkdocs.py` も回す（区別しない FS でしか見分けられない変異があるため。実装の途中で広げた——**計画への記載は編集の後になった**（手順 4 の「手を動かす前に」を守れていない）。受入基準は I1 の経路 E3 の検証手段として足す）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（5 本）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.44.0）
- `.claude-plugin/marketplace.json` — 版（0.44.0）
- `docs/plans/issue-514.md` — この計画

触らない:

- `plugins/spec-loop/scripts/merge-versions.py`——重ね合わせの綴りの判定（index の綴り。#569）は変えない。`fold` の正はここのまま（写しはテストが突き合わせる）
- `check-signoff.py`——タグの時点を `git show <tag>:<path>` で読む（git の木のパスは綴りどおりにしか当たらない）ので、この形は起きない。**`build-proposal.py` は表はタグから読むが、手書き部分は作業ツリーから読む**——1 パス目の CR1 で触る側へ移した
- スキルの手順（案 (b)「スキルの手順で先に重ね合わせの検査を通す」）——採らない（下の「仕様の穴」）
- スキル本体の LLM が手で開くファイル（散文の手順）——機械で縛れない

### 同じことを述べている箇所の数

- 「版ごとに読む側は綴り違いを名指しして止まる」: `versions.md`（正）・フックの docstring・`check-qa-csv.py`・`qa-to-pptx.py`・`check-feasibility-csv.py`・`schedule-to-gantt.py` の docstring の 6 箇所。スクリプトの docstring は終了コードの行に 1 行足し、決まりは `versions.md` を正として指す。
- `fold` の式: `merge-versions.py`（正）・`check-qa-csv.py`・フックの 3 箇所。**分けない理由**: `check-qa-csv.py` は単体で動く（テストが 1 ファイルだけ写して走らせる）・フックは正本リポジトリへ写されて単体で動く——どちらも `merge-versions.py` を読み込めない。写しはテストが試料で突き合わせる（既存の `qa_is_provisional` と同じ形）。
- 版: `marketplace.json`・`plugin.json`・`SKILL.md` 5 本 × 2 行。

## 乗るデプロイ経路

プラグインの配布（main へのマージ → 利用者の `claude plugin update`）。フックは正本リポジトリへ写されたものが動くので、利用者が取り込むまで届かない（`tree.md` の「Q&A 表を移す」の手順 4）。`docs/` は計画ファイルだけ（記録で成果物ではない）。

## 周の在り処

- ブランチ: `issue/514-reader-spelling`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-514`
- 起点: `d8cfe0c`（origin/main）
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `d8cfe0c0a0e7b58b57367d3cbe55aa50714ca27e`（1 パス目）
- 載せ替え: 1 パス目の指摘対応のあと `git merge origin/main`（`fc40984`。#668 の `prepare-worktree.sh`・`test-worktree-scripts.py` だけ、衝突なし・増えた検査なし）。式を当て直した base: `15535b30b99a52a00412819f921fd4e92e09cf9a`（2 パス目から）

## 仕様の穴（不在の線で推奨により決めた）

- **穴**: 版ごとに読む側をどう直すか——Issue は 2 案を挙げて決めていない。
- **選択肢**:
  - (a) 読む側が自分で、書いた綴りと大文字小文字だけ違う名前を名指しして止まる（推奨）
  - (b) スキルの手順で、版ごとに読む前に重ね合わせ（`merge-versions.py`）の検査を通す
- **決めた値**: (a)。ただし `merge-versions.py` の `misnamed` は使わない——読む側が持つ綴りの確かめを足す（`check-qa-csv.py` の `misspelled`、フックはその写しに当たる自前の探し方）。
- **推した理由**: (b) は MkDocs のフックに効かない（フックはスキルの外の `mkdocs build`／GitHub Pages で動く）・`feasibility/` は重ね合わせが見ない（`check-feasibility-csv.py`・`schedule-to-gantt.py` を覆えない）・手で CLI を叩いた経路を覆えない・散文の手順で機械の歯止めにならない。(a) は区別する FS と区別しない FS で同じ答え（どちらも 2 と名指し）を返す。`misnamed` を使わないのは、`check-qa-csv.py` とフックが単体で動く（`merge-versions.py` を読み込めない）ため。
- **(a) の代償**: 作業ツリーにだけ古い綴り（コミットは `shared/`、手元のフォルダは `Shared/`）が残る形では、重ね合わせは index の綴りで読んで通るが、読む側は区別しない FS で止まる——ディスク上で 2 段に改名する（`versions.md` の「綴りの誤りの移行」の 3）。
- 線と出所: `仕様の穴 = 推奨で決めて起票`（台帳の確かめた線）。確認の Issue: #704。

## verify の受入基準

### Issue の本文から写した失敗

- フック: `docs/v2/Shared/qa.csv` を置くと、`render_qa` が `Q-001` を描き、`qa_numbers` が `[(2, {'Q-001'})]` を返す（macOS）
- コードを読んだ範囲で同じ形: `check-qa-csv.py docs/v<n>/shared/qa.csv`・`qa-to-pptx.py`・`check-feasibility-csv.py`

### 不変条件

- **I1** 版ごとに読む側は、読むファイルのパスに、書いた綴り（`shared`・`qa.csv` など）と大文字小文字だけ違う名前のディスクの項目があれば、その中身を読まず、ディスクの綴りのパスを名指しして止まる。CLI は 2（中身を検査していない）、フックは警告（`mkdocs build --strict` が落ちる）とページの注意書き。**区別する FS と区別しない FS で同じ答え**（同じ終了コード・同じ名指し）。
- **I2** 綴りどおりの入力は今までどおり読む（回帰なし）。正規化だけ違う名前（NFD で作られた日本語のフォルダの下など）では止めない。区別する FS で綴りどおりの項目と綴りだけ違う項目が並ぶときは、綴りどおりのほうを読む（フックは綴り違いのほうも警告する）。
- **I3** 写し（`check-qa-csv.py` の `fold`・フックの `fold`）は `merge-versions.py` の `fold` と同じ答えを返す（テストが試料で突き合わせる）。
- **I4** 重ね合わせ（`merge-versions.py`）と、`check()`・`read_schedule` などのライブラリの読み口の振る舞いは変えない——`build-proposal.py`・`check-signoff.py`・`scaffold.py`・`diff-versions.py` の答えは変わらない。
- **I5** 版を 3 種類の箇所で揃え、main より上げる。
- **I6** 決まりの正（`versions.md`）に、読む側が止まることと、作業ツリーにだけ古い綴りが残る形の手当て・フックの取り込みを書く。

### 経路（不変条件を破りうる入口）

| 経路 | 守り方 |
| --- | --- |
| E1 フックの `render_qa`（`<!-- spec-loop: qa -->`） | 書いた綴りで探す（`lookup`）。綴り違いは警告して読まない |
| E2 フックの `render_decision_table` | 同上（`shared/decision_table.csv`） |
| E3 フックの `qa_numbers` → `link_numbers`（`on_page_content`。本文の番号のリンク） | 同上。綴り違いの表の番号はリンクにしない（「表に無い番号」の警告に回る） |
| E4 `check-qa-csv.py` の CLI（`shared/qa.csv`・`spec/qa-dev.csv`） | `main` で `misspelled` を当てて 2 |
| E5 `qa-to-pptx.py` の CLI | `main` で当てて 2（出力を作らない・既存の出力に触らない） |
| E6 `check-feasibility-csv.py` の CLI（2 つの表） | `main` で当てて 2（読めないものとして数える） |
| E7 `schedule-to-gantt.py` の CLI | `main` で当てて 2（前の出力の扱いは他の 2 と同じ `stop(out, 2)`） |
| E8 `merge-versions.py`・`build-proposal.py`・`check-signoff.py`（ライブラリの `check()`・`read_schedule` を使う側） | 触らない（I4）。`check()` に入れない |
| E10 `build-proposal.py` の `read_hand`（手書き部分 `docs/v<n>/proposal/*.md`・`proposal/spec/*.md` を**作業ツリーから**読む） | **1 パス目の `/code-review`（CR1）が数え漏れを示した**——`read_hand` で `misspelled` を当てて 2（`Stop`）。手順 4 の「差し戻し」で範囲を広げた |
| E11 一覧を読めない段（実行の権限だけのフォルダ）を通る CLI | **1 パス目の `/code-review`（CR3）が示した**——`misspelled` が止める |
| E9 スキルの手順の LLM が手で開くファイル | 機械で縛れない（未証明ではなく範囲の外。PR に書く） |

### この環境では証明できないもの（未証明）

- **Linux（GitHub Pages）の上の** `mkdocs build --strict` で落ちること——CI に MkDocs と Material の組が無い。**ただし実物の `mkdocs build --strict` は測った**（1 パス目の `/code-review` の指摘 CR4 で分類を直した）: 著者がメインの作業ツリーの `.venv`（mkdocs・material）と雛形のフックで、区別しない APFS 上の `docs/v1/Shared/qa.csv` で「Aborted with 1 warnings in strict mode!」（終了 1）、綴りどおりの対照で終了 0。区別する APFS では `/code-review` が同じく終了 1 を測った（著者は測っていない）。残るのは「大文字小文字の区別以外の Linux の違い」だけ。**`-q` を付けると警告が出ず strict でも落ちない**（著者が測った。mkdocs の振る舞い）。

### 生成物

- 図の書き出し・`skill-metrics.py` の生成ブロック（dev-loop の `SKILL.md` の測定）——この周は dev-loop の `SKILL.md` を触らないので該当なし。`check-all.py` が両方の鮮度を見る。それ以外の生成物なし。

## 未解決の判断・確認待ち事項

- 仕様の穴の確認の Issue: #704（要確認・PR #703 の重さで立てた）。

## 関門の進捗（再開点）

- 実装: 済み（`cc648a2`・`cda8189`）。手順 4 の割り目: 不在のため訊かず続けた
- 1 パス目の関門の起点（先に当てた関門に渡した時点の HEAD）: `cda8189`
- PR: #703
- Verifier 1 パス目: 通した——反証 1 件（R1。採否は下の表。直す 0 件）。verifier.md を 169 行読んだ（`wc -l` と一致）
- `/code-review` 1 パス目: 通した——指摘 6 件（CR1〜CR6。直す 3・分類を直す 1・残課題 2）
- 1 パス目の指摘対応: `66765f0`（CR1・CR2・CR3）。差分は 0 行でない（`git diff cda8189 -- ':(top)' ':(top,exclude)docs/plans/issue-514.md'` で 5 ファイル）——2 パス目を回す。2 つ目の割り目: 不在のため訊かず続けた
- 手順 5 の反証と差し戻し: Verifier 1 パス目の反証 1 件（R1。残課題）。差し戻し（手順 4 へ）は `/code-review` の CR1・CR3 で 1 回
- 2 パス目の関門: Verifier・`/code-review` とも起動する（base `15535b3`）
- 交絡を潰した手順:
    - **修正前に失敗を再現した**（陽性対照）: macOS（区別しない APFS）で、修正前のフックが `v2/Shared/qa.csv` の `Q-001` を描き `qa_numbers` が `[(1, set()), (2, {'Q-001'})]`、`check-qa-csv.py`・`qa-to-pptx.py` が綴り違いの表の中身を読んで列検査まで進んだ（終了 1）。修正後は描かずに警告・2 で名指し。
    - **両方の FS で同じテストを回した**: 既定の一時ディレクトリ（区別しない APFS）と、区別する APFS の sparse image を `TMPDIR` にした回で、5 本のテストがどちらも緑。片方の FS でしか見分けられない変異は、その FS で飛ばしたと出力が名指しする（区別しない側: `区別する FS で綴り違いのほうを読む`、区別する側: `番号をパスを組み立てて読む`）——どちらももう片方の FS の回で殺せた。
    - **CI（Python 3.12）**: 手元の 3.12 で `test-check-qa-csv.py`・`test-init-mkdocs.py`・`test-qa-to-pptx.py` を回して緑。
    - **試料が FS の答えに寄りかかっていないか**: 綴り違いの試料の期待（2 と名指し・警告）は両 FS で同じで、修正前のコードはどちらの FS でも期待と違う（区別しない FS では中身を読み、区別する FS では名指しせず「読めない」／黙って飛ばす）。

## 既知の限界・決着済みの論点

- **案 (b) を採らなかった**（上の「仕様の穴」）。決着の理由が誤っていると判断したなら、それは新しい反証である。
- **作業ツリーにだけ古い綴りが残る形で、読む側は区別しない FS で止まる**（重ね合わせは通る）——読む側は git を使わない（フックは単体で動き、`check-qa-csv.py` も単体で動く）。止まる向き（読み違えない）なので採った。`versions.md` の移行の 3 に手当てを書く。
- **確かめるのはパスの末尾 3 段（版・置き場所・ファイル）だけ**——その上の利用者のフォルダの綴りは見ない（決まりの外）。
- **正規化だけ違う名前は止めない**——決まりの名前（`shared`・`qa.csv` など）は ASCII なので正規化では違いようがなく、止めると NFD で作られた利用者のフォルダで誤って止まる。
- **書いた綴りそのものが決まりと違う（`Shared/qa.csv` と書いてディスクも `Shared/`）は止めない**——読む側が見るのは「書いた綴りとディスクの綴りが同じか」で、綴りが決まりどおりかは重ね合わせの検査の仕事。

### 1 パス目の採否の表（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1（`/code-review`）`build-proposal.py` の `read_hand` が作業ツリーの `docs/v2/Proposal/` を区別しない FS でだけ読む | 示せる——コードを読んだ（`read_hand` は `directory.glob("*.md")`、呼び出しは `top / in_version(v, "proposal")`）＋ `/code-review` が両 APFS で実測 | I1（版ごとに読む側。E10 の数え漏れ） | 直す |
| CR2（`/code-review`）`versions.md` の新しい文「`build-proposal.py` はタグの時点を git の木のパスで読むので、この形は起きない」が誤り | 示せる——`build-proposal.py` の docstring「手書き部分だけは作業ツリーから読む」 | I6（決まりの正に正しく書く） | 直す |
| CR3（`/code-review`）一覧を読めない段で `misspelled` が `None` を返し、区別しない FS で綴り違いを読む | 示せる——`/code-review` の実測（`docs/v2` を 311、`Shared/` だけ置いて終了 0）。著者は試料で再現（`test-check-qa-csv.py` の v7。変異「一覧を読めない段を素通りする」が赤） | I1（FS で答えが違う） | 直す |
| CR4（`/code-review`）未証明に分類した `mkdocs build --strict` は手元で測れる | 示せる——著者が測った（上の「未証明」） | 無し（分類の誠実さ。成果物でない） | 分類を直した（計画のみ） |
| CR5（`/code-review`）`check-qa-csv.py` の `fold` の写しは要らない（`merge-versions.py` が `qa.fold` を読めばよい） | 示せない（保守の手間で、失敗ではない） | 無し——I3 は満たす | 残課題 |
| CR6（`/code-review`）`test-check-qa-csv.py` に I2「綴りどおりを優先する」を殺す変異が無い | 示せない（試験の弱さで、振る舞いの失敗ではない。フック側は `SENSITIVE_ONLY` の変異で見ている） | 無し | 残課題 |
| R1（Verifier）`check-spec-exit.py docs/v2/shared/qa.csv docs/v2/spec` が、`docs/v2/Shared/qa.csv`・`docs/v2/Spec/` を読んで 0 を返す | 示せる——Verifier の実測（macOS、終了 0「条件 1 を満たす」。同じパスの `check-qa-csv.py` は 2） | 無し——`check-spec-exit.py` は `versions.md` の「重ね合わせた全体を読むもの」で、スキル（spec-review・scaffold）も `build/merged/…` を渡す。重ねた出力の名前は `merge-versions.py` が綴りどおりに書くので、決まりどおりの使い方では綴り違いに届かない。I1 は「版ごとに読む側」 | 残課題（周の途中の課題の振り分けで `直す` 候補——手で版のパスを渡した経路） |

## 手順 8

- この周の起票: 1 件（#704——`仕様の穴 = 推奨で決めて起票` の線で立てた確認の Issue——版ごとに読む側の直し方を (a) で決めたこと。起票の承認は不在のため訊いていない）
