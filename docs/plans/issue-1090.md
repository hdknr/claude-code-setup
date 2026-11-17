# Issue #1090 — spec-loop: 成果物の表（features.csv など）も行の単位で重ねるか決める

**不在の周**（`/dev-loop:cruise 1169 --absent` の起動・2026-11-17T10:47Z）。利用者には訊かない。親（cruise #1169）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1169`）。利用者の確認（起動時・2026-11-17T10:47:55Z、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`（古い値。後退・未達は推奨で進めない）。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1169.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.7.0（`SKILL.md` 1920 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1169`））。
版の上げ方: `spec-loop` を **minor**（新しい表を行の単位にするときの手順を `references/` に足す——CLAUDE.md の「能力・手順の追加」。2 パス目の CR2-8 で patch から改めた）。着手時の main は spec-loop 0.101.0 → 0.102.0。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.7.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: 成果物の表（`features.csv`・`entities.csv`・`io.csv`・`reports.csv`・`roles.csv`・`jobs.csv`）を、#1081/#1091 の「行の単位で重ねる表」の一覧に載せるかを決める。
確かめること（鍵の列・既存の v2 の置き方・照合／scaffold／検査への影響・移行の手順）。本文に受入基準を緩める指示は無い。

## 決めた値（依存する周 #1164・#1162・#1163・#1158・#1159・#1160 が前提にする）

- **D1 成果物の表は行の単位の一覧に載せない——ファイルの単位で重ねるまま**（`io-layout.csv` を含む 7 つ）。v2 以降に表を置くなら前の版の行も含めた全体を置き、行を外すときは丸ごと置き直す。
- **D2 新しく足す表（`requirements/`・`shared/` の CSV）も、一覧に載せない限りファイルの単位で重なる**。行の単位にするのは、鍵の列が 1 つで見出し行が版の間で変わらない表に限り、
  一覧の行・`removed.csv` の種類・`ROW_TABLES` を同じ周で足し、`ROW_TABLES` を読むスクリプト（`diff-versions.py`・`check-signoff.py`・`build-proposal.py`・`screen-gate.py` と、screen-spec の `build-mock.py`）を見直す。

原本は `plugins/spec-loop/references/versions.md` の「行の単位で重ねる表」。

### 確かめたこと（Issue の「確かめること」）

1. **鍵の列**（`references/tree.md` の「システム設計書の成果物」）: 1 列で行が決まるのは `features.csv`（`id`）・`io.csv`（`id`）・`jobs.csv`（`id`）だけ。
   `entities.csv` は `エンティティ`＋`項目`、`io-layout.csv`・`reports.csv` は `id`＋`順番` の 2 列、`roles.csv` は 1 列目 `操作` で 2 列目からロールの名前（ロールを足すと見出し行が変わる）。
   今の行の単位の重ね方（`merge-versions.py` の `ROW_TABLES`）は鍵の列を 1 つしか持たず、見出し行を版の間で変えない。`removed.csv` の種類の名前は、載せないので決めない。
2. **今 v2 以降を持つ案件の置き方**: 手元（`~/Projects` の下、深さ 6 まで）で `docs/v2` を持つ正本は 2 つ（tfs-stocks-score・unity-signage）で、どちらの版にも成果物の表は 1 つも無い（`requirements/` は `index.md`・`rules.md`・`overview.md` など）。
   観測窓は手元のクローンだけで、利用者の手元のほかの正本は見ていない。
3. **重ね方を変えたときの影響**: 載せないので `check-signoff.py`・`scaffold.py`・`check-design-csv.py`・`diff-versions.py`・`build-proposal.py`・`screen-gate.py` は変わらない。
   載せた場合は、`ROW_TABLES` を画面の表として読む `screen-gate.py`（`TABLES = tuple(versions.ROW_TABLES)`）も直す必要がある（新しい表の決まりに書いた）。
   **重ね方を変えると、v2 に丸ごと置き直した表の外した行が黙って残る**——一時ディレクトリで、v1 に F-001〜F-003、v2 に F-002 を外した `features.csv` を置いて重ねた:
   今の `merge-versions.py` は 0 で v2 の表そのもの（F-002 なし）、`ROW_TABLES` に `features.csv` を足した写しは 0 で F-002 が残った（どちらも終了コード 0——止まらない）。
4. **移行**: 載せないので移行の手順は要らない（版は patch）。

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **G1（D1）成果物の表を行の単位の一覧に載せるか**: 選択肢 (a) 載せない——ファイルの単位のまま（推奨）／(b) 全部載せる——鍵を 2 列に広げ、`roles.csv` の見出しの扱いを決め、移行を書く／
  (c) 鍵が 1 列の 3 つ（`features.csv`・`io.csv`・`jobs.csv`）だけ載せる。
  推した理由: (b) は重ね方の仕組み（鍵 1 列・見出し固定）を広げる大きな変更で、`roles.csv` は見出しが変わるので載せられない——載せても `requirements/` の重ね方は 1 種類にそろわない。
  (b)・(c) は v2 に丸ごと置いた表の読み方を黙って変える（上の 3）。行の単位にしたい困りごと（v2 で表を丸ごと写す手間）は、成果物の表を持つ v2 の正本が手元に無く、まだ起きていない。
  代償として、成果物の表の行の変化は版の差分に表のファイルの `変更` としてしか出ない（機能の追加・変更・削除は中間表現の機能の単位で出る。1 パス目の `/code-review` の指摘 CR1-1 で理由から代償に書き直した）。→ 確認の Issue（下の「未解決」）
- **G2（D2）新しく足す表の既定の重ね方**: 選択肢 (a) 既定はファイルの単位、行の単位にするなら鍵 1 列・見出し固定の表を一覧に足す（推奨）／(b) 既定を行の単位にする（新しい表は一覧に載せて足す）。
  推した理由: 依存する周が足す表には CRUD の表（機能 × データの行列。見出しがデータで変わる）のように行の単位に合わないものがあり、既定を 1 つに決めるならどの表にも当てはまるファイルの単位になる。
  成果物の表（D1）と同じ重ね方にそろう。→ 確認の Issue（下の「未解決」）

## 変更範囲

触る:

- `plugins/spec-loop/references/versions.md` — 「行の単位で重ねる表」の成果物の表の項（決めた値と理由）と、新しく足す表の重ね方の項
- `plugins/spec-loop/references/tree.md` — 「システム設計書の成果物」の重ね方の項に、`versions.md` を指す 1 文
- `scripts/test-merge-versions.py` — 成果物の表がファイルの単位で重なる試料と、陽性対照の変異（一覧に `features.csv` を足す）
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1090.md` — この計画ファイル

触らない:

- `plugins/spec-loop/scripts/` の本体（`merge-versions.py` の `ROW_TABLES` など）——重ね方は変えない（D1）
- 成果物の表の列・検査（`check-design-csv.py`）・scaffold の機能一覧の照合
- 依存する周が足す表（#1164 ほか）

依存の追加・更新: なし

**複製の数**: 「成果物の表はファイルの単位で重なる」を述べている箇所は 5（`versions.md` の「行の単位で重ねる表」の項・「重ねるもの」の表の最後の行、`tree.md` の「システム設計書の成果物」の項・「機能一覧と中間表現の照合」の「一覧はファイルの単位で重なる」、`merge-versions.py` の `ROW_TABLES` のコメント）。
どれも今の決まりと一致しているので変えない。決めた理由と新しい表の決まりは `versions.md` の 1 箇所に置き、`tree.md` からは指すだけにする（分けない理由: 決まりの原本は `versions.md`）。

## デプロイ経路

プラグイン（`marketplace.json` のカタログと、`link-skills.sh` を使う利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口（成果物の表の重ね方を読む・決める場所）: 正本の版のディレクトリ → `merge-versions.py`（重ね合わせ）→ それを読む `diff-versions.py`・`check-signoff.py`・`build-proposal.py`・`scaffold.py`（機能一覧の照合）・`check-design-csv.py`（重ねた全体）・`screen-gate.py`（`ROW_TABLES`）・MkDocs のフック、
と、決まりを読んで表を書く人とスキル（req-loop・spec-review が `tree.md` を読む）、依存する周（`versions.md`・`tree.md` に新しい表を足す）。

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| B1 | `versions.md` の「行の単位で重ねる表」が、成果物の表を載せないと決めたこと（#1090）と理由を書き、**理由が事実として正しい**: (1) `tree.md` の成果物の表の鍵の列と見出し、(2) 行の単位にすると丸ごと置き直した表の外した行が残る（止まらない）、(3) どの機能が変わったかは中間表現の機能の版の差分で出る | 理由が `tree.md`・`merge-versions.py`・`diff-versions.py` の実物と食い違う | 実物を読む・一時ディレクトリで重ねる（両方の関門） |
| B2 | 新しく足す表の重ね方が `versions.md` に決まっている——既定はファイルの単位・行の単位にする条件（鍵 1 列・見出し固定）・同じ周で足すもの・見直すスクリプト。**見直すスクリプトの一覧が `ROW_TABLES`（と `ROW_KINDS`）を読む実物と一致する** | 一覧から読む側が漏れる・条件が今の仕組みと食い違う | `grep` で `ROW_TABLES`・`ROW_KINDS` を読むスクリプトを数える |
| B3 | 成果物の表はファイルの単位で重なる: v2 に v1 の行を外した `features.csv` を置くと、重ねた表は v2 の表そのもの。`test-merge-versions.py` の試料があり、**陽性対照の変異（一覧に `features.csv` を足す）で赤になる** | 試料が重ね方を判別しない（変異でも緑） | `test-merge-versions.py`（変異を含む） |
| B4 | 重ね方の振る舞いは変えない——`plugins/spec-loop/scripts/` の差分が 0 行で、`ROW_TABLES` と `versions.md` の一覧の照合（`check_reference`）が通る | 本体を触る・一覧の表の行の形を崩して照合が黙って空になる | `git diff <base> -- plugins/spec-loop/scripts/`・`test-merge-versions.py` |
| B5 | `tree.md` の成果物の表の重ね方の記述が `versions.md` と食い違わない（ファイルの単位・丸ごと置き直す・指し先） | 片方だけ書き換える | 読み比べる |
| B6 | 版を上げ（spec-loop、3 種で揃う）、`check-all.py` が通る | 版の取りこぼし・歯止めの赤 | `check-plugin-versions.py`・`check-all.py`（run-serial 越し） |

**検証で証明できるもの**: B1〜B6。
**この環境では証明できないもの（未証明）**: なし。（「成果物の表を持つ v2 の正本は無い」は受入基準ではなく、G1 の理由の材料——観測窓は手元のクローンだけ、と書いて主張をそこまでに留めた。）
**生成物**: 該当なし——`docs/plugins/dev-loop-design.md` §8.2 の生成ブロックは dev-loop の `SKILL.md` から作るもので、この周は dev-loop を触らない。図なし。spec-loop の `SKILL.md` は版の 2 行だけ。
**必須要件の掛け算**: 受入基準を Verifier と `/code-review` の両方に、1・2 パスとも渡す（2 パス目が該当なしなら 1 パス目の 2 つ）。

## 未解決の判断・確認待ち

- G1・G2（上）は推奨で決めた。確認の Issue は PR を作った後に立てる（重さに PR の番号を書くため）。

## 起票

- この周の起票: 2 件（仕様の穴 G1・G2 の確認の Issue。`仕様の穴 = 推奨で決めて起票` の線で立てる——起票の承認は不在のため訊いていない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1090-deliverable-tables-merge-unit`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1090`・起点 `dd1f8fb`・base `origin/main` = `dd1f8fbe63ee41c22525c9807bec8e0177ea3cca`
- 1 パス目の指摘対応の起点: `2c5a30c`（1 パス目の関門に渡した時点の HEAD）
- Verifier 1 パス目: 通した（2c5a30c）。反証 0 件（`dev-loop:dev-loop-verifier`・sonnet。`SubagentHandback` が届かず、報告はトランスクリプトの handback の呼び出しから読んだ）。自分では変異を設計せず、テストの変異（113 件）だけ——陽性対照は著者が別に当てた（「確かめたこと」の 3）
- `/code-review` 1 パス目: 通した（3205a1d）。指摘 9 件（直す 3・残課題 5・捨てる 1。下の採否の表）。報告はフォークのトランスクリプトから読んだ
- 1 パス目の指摘対応: CR1-1・CR1-3・CR1-5 を直した（起点 `2c5a30c` から計画ファイルを除いた差分は `references/versions.md`・`references/tree.md` の 2 ファイルで 0 行でない——2 パス目を回す）。2 パス目（Verifier と `/code-review`）は `8061a8c` に当てる
- Verifier 2 パス目: 通した（a1fe2a6）。反証 0 件（sonnet。報告はトランスクリプトの handback の呼び出しから読んだ。直した記述の事実を一時ディレクトリで走らせて確かめた）
- `/code-review` 2 パス目: 通した（a1fe2a6）。指摘 9 件（直す 4・残課題 5。下の採否の表）
- 狭いパスの起点: `a1fe2a6`（2 パス目の指摘対応を始める直前の HEAD）。終点: `d4a0cea`（CR2-1・CR2-3・CR2-4・CR2-8 の直し）
- 狭いパス: 起動
- 交絡を潰した手順: 重ね方の実験（上の「確かめたこと」の 3）——同じ入力・同じスクリプトの写しで、`ROW_TABLES` の 1 行だけを違えて走らせた（陽性対照: 今の版で F-002 が外れることを同じ観測点で見た）。

## 既知の限界・決着済みの論点

- B1 の (3)（「どの機能が変わったかは版の差分に出る」）は、1 パス目の `/code-review`（CR1-1）が偽と示した——`versions.md` では理由から外し、代償として書き直した。B1 は書き直した文の真偽を見る。

### 採否の表（1 パス目）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | Verifier 1 パス目: 反証 0 件 | — | — | — |
| CR1-1 | 理由 (3) が言い過ぎ——版の差分は中間表現の機能を名指すが、`features.csv` の行の変化はファイルの `変更` としか出ない | 示せる——一時ディレクトリで v2 の `features.csv` の F-002 の名前だけ変えて `diff-versions.py docs --version 2` → `機能: 変更 0`・`変更 requirements/features.csv` だけ | B1 | 直す（理由から外し、代償として書いた） |
| CR1-2 | 鍵 1 列の `features.csv`・`io.csv`・`jobs.csv` がファイルの単位に残る理由が (2) しかない | 示せない（理由の厚みの指摘で、偽の記述ではない） | 無し | 残課題（G1 の確認の Issue の選択肢 (c) で利用者に渡す） |
| CR1-3 | 新しい表を行の単位にするとき同じ周で足すものから、`KINDS`・「重ねるもの」の表・「版の差分」の単位の項が漏れている | 示せる——一時ディレクトリで `ROW_TABLES` に `features.csv`（種類 `機能一覧`）を足し `KINDS` に足さない写しで、`removed.csv` に `機能一覧,F-002` → `` `種類` が ファイル / Q&A / 機能 / 画面 / 項目 / 遷移 のどれでもない: 機能一覧 `` で断られた | B2 | 直す |
| CR1-4 | 理由 (2) の「止まらない」は `features.csv` には言い過ぎ——scaffold の機能一覧の照合が残った行で止める | 示せない（scaffold を走らせていない。記述の「止まらない」は重ね合わせのことで、実測の範囲） | 無し | 残課題 |
| CR1-5 | `tree.md` の「`requirements/` のほかのファイルと同じ」が、行の単位の画面の表と食い違う | 示せる——`tree.md` の同じ項の文と `versions.md` の「行の単位で重ねる表」の一覧（`requirements/screens/data/`） | B5 | 直す |
| CR1-6 | 新しい表の決まりが `requirements/`・`shared/` しか挙げず、`spec/` の CSV が決まっていない | 示せない——節の頭の「行の単位で重ねる表はこの一覧に載せたものだけ」が `spec/` を含めて決めている | 無し | 捨てる（確かめて成り立たなかった） |
| CR1-7 | 手順の追加なので版は patch でなく minor では | 示せる（CLAUDE.md の表）が、受入基準 B6 は版を上げて揃うことで、刻み方は決めていない | 無し | 残課題——2 パス目の CR2-8 で決着の理由が誤っていたと分かり、直した |
| CR1-8 | 陽性対照の変異が種類に `機能`（`KIND_FEATURE`）を使い、中間表現の機能の削除と衝突しうる | 示せない（今の試料に `機能` の削除は無く、変異は残った行で赤になる——著者も Verifier も確かめた） | 無し | 残課題 |
| CR1-9 | 配布する `references/` が「このリポジトリの `scripts/test-merge-versions.py`」を指し、利用者の正本には無い | 示せない（先例 `tree.md`・`handoff-issue.md` と同じ書き方。文言） | 無し | 残課題 |

### 採否の表（2 パス目）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V2 | Verifier 2 パス目: 反証 0 件 | — | — | — |
| CR2-1 | 新しい表の決まりが、種類を既存の種類（`ファイル`・`Q&A`・`機能` など）と重ねるなと言っていない——重ねると `removed.csv` の行が別のものを消す | 示せる——一時ディレクトリで v1 に中間表現の F-001・F-002 と `features.csv` の F-001〜F-003、v2 に `removed.csv` の `機能,F-002` だけを置き、今の版は 0 で中間表現が `[F-001]`・表は 3 行、`ROW_TABLES` に `features.csv` を種類 `機能` で足した写しは 0 で中間表現が `[F-001, F-002]`・表から F-002 が消えた | B2 | 直す |
| CR2-2 | 見直すスクリプトの一覧が `ROW_TABLES` の読み手だけで、版ごとの生の表を読むもの（MkDocs のフックの `render_infra`・版のディレクトリに当てる `check-design-csv.py`）が漏れる。`check-signoff.py`・`build-proposal.py` が読むのは `ROW_KINDS` | 示せない（今の失敗ではなく、将来の周が表を足したときの漏れ）。B2 は `ROW_TABLES`・`ROW_KINDS` の読み手との一致で、そこは一致 | 無し | 残課題 |
| CR2-3 | 理由 1 の「上の『見出し行は版の間で変えない』」は下の項にある | 示せる——`versions.md` で理由 1 は成果物の表の項（一覧の表の直後）、「見出し行は版の間で変えない」はその 3 つ後の項 | B1 | 直す |
| CR2-4 | 代償の「ファイルの `変更` としてしか出ない」は、表を初めて置く・消す版では偽（`追加`・`削除` が出る） | 示せる——一時ディレクトリで v2 に初めて `features.csv` を置き `diff-versions.py docs --version 2` → `追加 requirements/features.csv` | B1 | 直す |
| CR2-5 | `check_reference` に「`ROW_KINDS` が `ファイル`・`Q&A`・`機能` と重ならない」の照合を足せば、散文に頼らずに CR2-1 を止められる | 示せない（今の一覧は重なっていない。散文の直しで B2 は満たす） | 無し | 残課題 |
| CR2-6 | 「同じ周で足すもの」が、画面の表に固有の記述（画面を指す列・画面の表の検査・`removed.csv` の `対象` の列の説明）を挙げていない | 示せない（画面でない表を一覧に足した周で初めて食い違う） | 無し | 残課題 |
| CR2-7 | 試料の判定が「v2 の表そのもの」だけで、変異で F-002 が残ることを直に見ていない | 示せない（今は残った行で赤になることを著者・Verifier 2 体・`/code-review` 2 回が確かめた。試料の穴） | 無し | 残課題 |
| CR2-8 | 手順を足したので版は minor（CR1-7 の「B6 は刻み方を決めていない」は CLAUDE.md の「プラグインの更新」の表を見ていない） | 示せる——CLAUDE.md の表「能力・手順の追加 → minor」と、`versions.md` の新しい表を足す手順 | B6（版の上げ方は CLAUDE.md の「プラグインの更新」の決まりに従う、と読む——CR1-7 の決着の理由が誤っていた） | 直す（0.102.0。計画の版の上げ方も minor に） |
| CR2-9 | 試料の `DELIVERABLES` の v1 の本文が直書きで、変異の錨の文字列が隣の変異と重複 | 示せない（整理の指摘） | 無し | 残課題 |

## 関門の記録

```dev-loop-gates
周の base: dd1f8fbe63ee41c22525c9807bec8e0177ea3cca
関門: Verifier 1 2c5a30c 反証=0
関門: /code-review 1 3205a1d 指摘=9
関門: Verifier 2 a1fe2a6 反証=0
関門: /code-review 2 a1fe2a6 指摘=9
```
