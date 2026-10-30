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
- `.github/workflows/plugins.yml` — 区別しない FS（ext4 の casefold）の段で `test-init-mkdocs.py` も回す（区別しない FS でしか見分けられない変異があるため。実装の途中で広げた——**計画への記載は編集の後になった**（手順 4 の「手を動かす前に」を守れていない）。受入基準は I1 の経路 E3 の検証手段として足す）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（5 本）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.44.0）
- `.claude-plugin/marketplace.json` — 版（0.44.0）
- `docs/plans/issue-514.md` — この計画

触らない:

- `plugins/spec-loop/scripts/merge-versions.py`——重ね合わせの綴りの判定（index の綴り。#569）は変えない。`fold` の正はここのまま（写しはテストが突き合わせる）
- `build-proposal.py`・`check-signoff.py`——タグの時点を `git show <tag>:<path>` で読む（git の木のパスは綴りどおりにしか当たらない）ので、この形は起きない
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
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `d8cfe0c0a0e7b58b57367d3cbe55aa50714ca27e`

## 仕様の穴（不在の線で推奨により決めた）

- **穴**: 版ごとに読む側をどう直すか——Issue は 2 案を挙げて決めていない。
- **選択肢**:
  - (a) 読む側が自分で、書いた綴りと大文字小文字だけ違う名前を名指しして止まる（推奨）
  - (b) スキルの手順で、版ごとに読む前に重ね合わせ（`merge-versions.py`）の検査を通す
- **決めた値**: (a)。ただし `merge-versions.py` の `misnamed` は使わない——読む側が持つ綴りの確かめを足す（`check-qa-csv.py` の `misspelled`、フックはその写しに当たる自前の探し方）。
- **推した理由**: (b) は MkDocs のフックに効かない（フックはスキルの外の `mkdocs build`／GitHub Pages で動く）・`feasibility/` は重ね合わせが見ない（`check-feasibility-csv.py`・`schedule-to-gantt.py` を覆えない）・手で CLI を叩いた経路を覆えない・散文の手順で機械の歯止めにならない。(a) は区別する FS と区別しない FS で同じ答え（どちらも 2 と名指し）を返す。`misnamed` を使わないのは、`check-qa-csv.py` とフックが単体で動く（`merge-versions.py` を読み込めない）ため。
- **(a) の代償**: 作業ツリーにだけ古い綴り（コミットは `shared/`、手元のフォルダは `Shared/`）が残る形では、重ね合わせは index の綴りで読んで通るが、読む側は区別しない FS で止まる——ディスク上で 2 段に改名する（`versions.md` の「綴りの誤りの移行」の 3）。
- 線と出所: `仕様の穴 = 推奨で決めて起票`（台帳の確かめた線）。確認の Issue は PR を作ってから立てる（重さに PR 番号を書くため）。

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
| E9 スキルの手順の LLM が手で開くファイル | 機械で縛れない（未証明ではなく範囲の外。PR に書く） |

### この環境では証明できないもの（未証明）

- GitHub Pages（Linux）の上の `mkdocs build --strict` で落ちること——CI に MkDocs と Material の組が無い（`test-init-mkdocs.py` の docstring）。フックの警告が `mkdocs` のロガーに出ることまでをテストで見る。

### 生成物

- 図の書き出し・`skill-metrics.py` の生成ブロック（dev-loop の `SKILL.md` の測定）——この周は dev-loop の `SKILL.md` を触らないので該当なし。`check-all.py` が両方の鮮度を見る。それ以外の生成物なし。

## 未解決の判断・確認待ち事項

- 仕様の穴の確認の Issue（上）——PR を作ってから立てる。

## 関門の進捗（再開点）

- 実装: 済み（`cc648a2`・`cda8189`）。手順 4 の割り目: 不在のため訊かず続けた
- 1 パス目の関門の起点（先に当てた関門に渡した時点の HEAD）: `cda8189`
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 手順 5 の反証と差し戻し: まだ無い
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

## 手順 8

- この周の起票: 1 件（`仕様の穴 = 推奨で決めて起票` の線で立てる確認の Issue——版ごとに読む側の直し方を (a) で決めたこと。起票の承認は不在のため訊いていない）
