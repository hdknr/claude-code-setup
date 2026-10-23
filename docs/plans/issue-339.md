# Issue #339 — Q&A 表に層（共有・内部）と推奨を足し、読む側と写し済みのフックを 1 回で移す

まとめる Issue: #330（層）・#267（推奨）・#337（写し済みのフックの移行）。PR で 3 つとも閉じる。

## 変更範囲

触る:

- `plugins/spec-loop/references/qa-csv.md` — 推奨の 2 列・内部の層の表（`spec/qa-dev.csv`・`D-001`）・層の移し替え・内部での推奨。**決まりの原本**
- `plugins/spec-loop/references/tree.md` — `spec/qa-dev.csv` の置き場所・移行の手順（表の見出し・内部の層・写し済みのフック）
- `plugins/spec-loop/references/spec-scope.md` — 振り分けの区分を「共有に起票」「内部で決めて記録」に分け、境目の問い・迷う例・費用だけが変わる選択の行き先
- `plugins/spec-loop/references/spec-exit.md` — 条件 1 が両方の表を見る
- `plugins/spec-loop/references/spec-ir.md` — 中間表現の `qa` が `D-` も指せる
- `plugins/spec-loop/references/versions.md` — `qa-dev.csv` も行で重ねる・`removed.csv` の `Q&A` が `D-` も消せる
- `plugins/spec-loop/references/signoff-tags.md` — 内部の表は照合の範囲（`shared/`）の外（該当すれば）
- `plugins/spec-loop/references/feasibility-csv.md` — 見積りの根拠に `D-` を書ける（該当すれば）
- `plugins/spec-loop/scripts/check-qa-csv.py` — 列（推奨・推奨の理由）・層（ファイル名で決める）・`D-` の番号・内部では `暫定反映` を使わない・古い見出しは移行の手順を指して落とす
- `plugins/spec-loop/scripts/check-spec-exit.py` — `spec/qa-dev.csv` も数える・未決定の印の走査から除く
- `plugins/spec-loop/scripts/qa-to-pptx.py` — 推奨を目立たせる・内部の表を渡されたら断る
- `plugins/spec-loop/scripts/merge-versions.py` — `spec/qa-dev.csv` を行で重ねる
- `plugins/spec-loop/scripts/diff-versions.py` — 内部の表の行の差分（重ね合わせに合わせる）
- `plugins/spec-loop/scripts/scaffold.py` — 内部の表を読む（`qa` が `D-` を指せる）
- `plugins/spec-loop/scripts/check-signoff.py` — 列の変更に追従（必要なら）
- `plugins/spec-loop/scripts/build-proposal.py` — 列の変更に追従（必要なら）
- `plugins/spec-loop/scripts/init-mkdocs.py` — docstring の移行の指し先（必要なら）
- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — 列の写し・推奨の表示・古い見出しは移行の手順を指して落とす
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 手順 3: 推奨と理由を書く（回答の推測ではない）。内部の層は資料に載らない
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 振り分けの 2 つの起票・推奨
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 推奨・内部の表の費用の行を見積りに拾う
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 内部の表（該当すれば）
- `plugins/spec-loop/skills/proposal/SKILL.md` — 版の 2 行
- `plugins/spec-loop/agents/red-team.md` — 「利用者の判断が要る」の基準と振り分けの案の名前
- `plugins/spec-loop/agents/domain-checker.md` — 同上
- `plugins/spec-loop/agents/formal-checker.md` — 同上
- `plugins/spec-loop/agents/estimate-checker.md` — 内部の表の費用の行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.17.0 → 0.18.0。0.x なので壊れる変更も minor。移行は `references/` に書く）
- `.claude-plugin/marketplace.json` — 同上
- `scripts/test-check-qa-csv.py` — 試料・期待・変異
- `scripts/test-check-spec-exit.py` — 同上
- `scripts/test-qa-to-pptx.py` — 同上
- `scripts/test-merge-versions.py` — 同上
- `scripts/test-diff-versions.py` — 同上
- `scripts/test-scaffold.py` — 同上
- `scripts/test-check-signoff.py` — 同上
- `scripts/test-build-proposal.py` — 同上
- `scripts/test-init-mkdocs.py` — 同上
- `plugins/spec-loop/README.md` — spec-review の区分（5 → 6 つ）。実装中に足した（区分の名前を列挙していた）
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 仕様の穴を起票するときの列（推奨の 2 列）と内部の表。1 パス目の指摘 C1 で足した
  （dev-loop が書く行が新しい検査で落ちる。受入基準 #10 の「各スキル」に dev-loop の差し戻しも入れる）
- `plugins/dev-loop/.claude-plugin/plugin.json` — dev-loop の版（1.44.0 → 1.45.0。手順の分岐（内部の表への起票）を足したので minor。2 パス目の R10 で人間が決めた）
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 版の 2 行
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` で書き直す。手で書かない）
- `CLAUDE.md` — スクリプトの説明（該当すれば）
- `docs/plugins/index.md` — spec-loop の説明（該当すれば）
- `docs/plans/issue-339.md` — この計画

触らない:

- 正本リポジトリ（`sbi-hubspot` など）——読むだけ。試料は scratchpad に写して当てる
- 回答が推奨と違ったことの記録（#267 の「やること」の最後の項。#339 の受入基準に無い）
- 内部の表を MkDocs で描くこと（共有の表だけを描く。内部の表は開発者の `spec/` にある）
- 移行の道具（人間の決定: 手順と、古い見出しを指すエラーだけ）
- `init-mkdocs.py` の「在るファイルは変えない」の決まり

### 同じことを述べている箇所の数

- 列の並び: 原本 `qa-csv.md`、写し `check-qa-csv.py`・フック（テストが突き合わせる）、試料の見出し 9 本のテスト——約 12 箇所
- 内部の表の置き場所と番号: `qa-csv.md`・`tree.md`・`versions.md`・`spec-exit.md`・`spec-ir.md`・`check-qa-csv.py`・`check-spec-exit.py`・`merge-versions.py`・`scaffold.py`——約 9 箇所
- 「利用者の判断が要る」の線: `spec-scope.md`（原本）・`spec-review`・判定役 3 体——約 5 箇所
- 推奨を書く決まり: `qa-csv.md`（原本）・`req-loop`・`spec-review`・`feasibility`——約 4 箇所

分けない理由: Issue が「見出しの移行を 1 回で」を求めている（人間が #330・#267・#337 を束ねた）。表を読む側は列を全部読むので、
層と推奨を別々の周で変えると見出しの移行と正本のフックの取り込みが 2 回になる。

## 決めたこと

人間の決定（2026-10-22、AskUserQuestion）:

- **層はファイルを分ける**（内部の表は `shared/` の外）
- **推奨は 2 列**（`推奨`・`推奨の理由`）
- **費用だけが変わる選択は、内部の層に置き、予算の責任者（feasibility・budget-signoff）に回す**
- **移行は手順とエラーだけ**（道具は足さない。`init-mkdocs.py` の決まりは変えない）

上から導いた著者の決定（PR で申告する）:

- 内部の表の置き場所は **`docs/v<n>/spec/qa-dev.csv`**。番号は **`D-001`**。列は共有の表と同じ（検査を 1 つにするため）
- 列の並び: `No,起票元,質問,選択肢,推奨,推奨の理由,回答,反映先,状態,費用への影響`
- `推奨` は選択肢のラベル（`A`〜）か `なし`。`推奨の理由` は**いつも**空でない（`なし` のときは推奨できない理由——事実の確認・見積り待ちなど）。**両方の層で同じ**
- 内部の表では `暫定反映` を使わない（確かめる利用者がいない）。`回答` には決めた人と日付を書く
- 層の移し替え: 作業中の版の中なら、元の表から行を消し、移した先で新しい番号を振って `起票元` の詳細に元の番号を書く。
  前の版の行なら、`removed.csv` の `Q&A`（`D-` も可）で消して、作業中の版の移した先に起票する
- `check-spec-exit.py` は、`spec/` の中の `qa-dev.csv` を未決定の印の走査から外す（表として検査する。質問の文に印の語が入りうる）
- `diff-versions.py` は内部の表の行も比べる（開発者の道具）。**`build-proposal.py` は内部の行（`D-`）を「前の版からの変更」から外す**
  ——比較が内部の行を含むようになったので、外さないと決裁者向けの提案書に内部の質問が載る
- **`check-signoff.py` は `removed.csv` の `Q&A` のうち `D-` の行を比べない**——比べると、内部の行を後の版で消しただけで
  サインオフが割れる（受入基準 #8）
- 振り分けの区分の名前: 「Q&A 表に起票する」を「**共有の Q&A 表に起票する**」に改め、「**内部の Q&A 表に記録する**」を足す（6 区分）

人間の決定（2026-10-22、実装中に見つけた穴。AskUserQuestion）:

- **リリースした版（凍結）がある正本は移さずに止め、人間に訊く**——移すのはリリースの前だけ。読む側に前の形を読む道は残さない
  （凍結した版の表を直せず、前の形のままだと後の版を重ねるところで落ちるため）

## 乗るデプロイ経路

プラグインの版を上げて配布する（`marketplace update` → `plugin update`）。`docs/` は main への push で GitHub Pages。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | 列の決まり（推奨・推奨の理由）を満たさない行は落ちる: 推奨が選択肢に無いラベル／`なし` でも空でもない値／空／理由が空 | `check-qa-csv.py`（`merge-versions`・`check-spec-exit`・`qa-to-pptx`・`scaffold`・`check-signoff`・`build-proposal` がこの関数で読む） | 行の検査 |
| 2 | 古い見出し（推奨の列が無い）は落ち、出力が移行の手順（`tree.md`）を指す | `check-qa-csv.py`・フック | 見出しの比較 |
| 3 | 内部の表は `D-` の番号だけ・`暫定反映` を使わない。共有の表は `Q-` だけ | `check-qa-csv.py` | ファイル名で層を決める |
| 4 | 抜ける条件 1 は、共有と内部のどちらかに反映していない行があれば満たさない。内部の表の文は未決定の印として数えない | `check-spec-exit.py`（`spec-review`・`scaffold` が呼ぶ） | 両方の表を読む |
| 5 | レビュー会の資料には共有の表だけが載り、推奨の選択肢と理由が見える。内部の表を渡すと作らない | `qa-to-pptx.py` | 層を見て断る・推奨を描く |
| 6 | 版を重ねると内部の表も行で重なる（同じ `No` は置き換え・`removed.csv` で消す）。差分も行で出る | `merge-versions.py`・`diff-versions.py` | 構造化したファイルに足す |
| 7 | 中間表現の `qa` は `D-` の行も指せ、指した行が `反映済み` でなければ止まる | `scaffold.py` | 両方の表を引く |
| 8 | 照合（`check-signoff.py`）と提案書は共有の表だけを見る（内部の表の変更・内部の行の削除でサインオフが割れない。提案書に内部の行が載らない） | `check-signoff.py`・`build-proposal.py` | `shared/` だけを比べ、`removed.csv` の `D-` の行を外す。提案書の比較から `D-` を外す |
| 9 | MkDocs のフックが新しい見出しを読み、推奨を出し、古い見出しでは移行の手順を指す。フックの列の写しが `check-qa-csv.py` と一致する | フック・`test-init-mkdocs.py` | 写しの突き合わせ |
| 10 | 決まり（`qa-csv.md`）・振り分け（`spec-scope.md`）・各スキル・判定役が同じ線と同じ書き方を述べ、スクリプトの挙動と食い違わない（受入基準 B・C・E の文言） | 文書 | 試料で確かめる |
| 11 | 移行の手順が 1 か所（`tree.md`）にあり、写し済みのフックと古い表の両方を扱う。リリースした版があれば止める（人間の決定） | 文書 | — |
| 12 | 版が 3 種類で揃い、歯止めが全部緑 | bump 漏れ | `python3 scripts/check-all.py` |

組み合わせ: 1 × 3（推奨の決まりは両方の層で同じ）。3 × 4（内部の表も抜ける条件で数える）。4 × 5（資料に載らない内部の行も、抜ける条件は止める）。
6 × 7（重ねた内部の表から `D-` を引く）。2 × 9（古い見出しはフックでも検査でも同じ指し先）。8 × 3（内部の表の変更は照合の範囲に入らない）。

**確かめ方（受入基準 F）**:

- SBIPRISM-207（手元の `sbi-hubspot` の `docs/shared/qa.csv`）を scratchpad に写し、選択肢の末尾の `（推奨: …）` を新しい 2 列へ移して
  新しい検査に当てる。推奨あり・なしの件数を記録する（Issue は「21 問・推奨 16・なし 5」だが、表は今 32 行ある——今の件数を書く）
- TFSSTOCKS-37 の Q-104〜Q-118 は**手元に無い**（`tfs-stocks-*` の表は Q-077 まで）。代わりに Issue #330 本文の Q-117・Q-118 を
  新しい線で分け、その結果を書く

**この環境では証明できないもの（未証明）**: TFSSTOCKS-37 の 15 問を新しい線で分けた件数（手元に表が無い）。実案件の正本での移行の通し。
PowerPoint で開いた見た目。判定役（LLM）が新しい線で実際に振り分けるか（スキルの文は検査できるが、判定役の判断は CI で回せない）。

生成物: リポジトリに commit した PPTX・`scaffold/` は無い。図なし。**`SKILL.md` の測定値（設計ドキュメント §8.2 の生成ブロック）は、1 パス目の指摘 C1 で dev-loop の `references/spec-gap.md` を直したので該当する**——`python3 scripts/skill-metrics.py` で書き直し、`--check` で鮮度を見る（着手時は「生成物なし」と判定していた。範囲を dev-loop に広げて変わった）。

## 未解決の判断・確認待ち

無し（4 つの設計の選択は人間が決めた）。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/339-qa-layers-recommendation`・worktree `.claude/worktrees/issue-339`・
  起点 `4187a08`・base 参照 `origin/main` → `4187a081088ab5c3037efd7e8d2b2968cb34d5d8`
- 実装: 済み（コミット 2 つ。個別のテストは緑——`test-check-qa-csv` 60/43・`test-check-spec-exit` 34/27・`test-qa-to-pptx`・
  `test-merge-versions` 57/51・`test-diff-versions` 13/12・`test-scaffold` 164/113・`test-check-signoff` 54/41・`test-build-proposal` 38/31・
  `test-init-mkdocs` 45/82。試料/変異）。`check-all.py` で `check-description-sync.py` が 1 回赤（feasibility の要約が古かった）→
  要約を直し、proposal・scaffold は trailer で免除
- 関門 1 パス目（2026-10-22）: 1 パス目の指摘対応の起点 `4729e2b`（関門に渡した時点の HEAD。コミット済み）。
  **Verifier 反証 1 件**（`dev-loop:dev-loop-verifier`・sonnet）・**`/code-review` 指摘 6 件**（high）。採否は下の「1 パス目の指摘の採否」
- 1 パス目の指摘対応: V1/C2・C1 を直す（`tree.md` の移す手順 1 にサインオフのタグ、dev-loop の `spec-gap.md` の列と内部の表。dev-loop 1.44.1）。
  **残るのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方**。
  `check-all.py` は指摘対応のあと 1 回赤（`skill-metrics.py --check`——dev-loop の `spec-gap.md` を直して設計ドキュメントの生成ブロックが古くなった）
  → `skill-metrics.py` で書き直して **44/44 緑**
- 関門 2 パス目（2026-10-23）: Verifier 反証 2 件・`/code-review` 指摘 10 件（同じ行に畳んで 10 行）。採否は下の「2 パス目の指摘の採否」。
  R1〜R9 を直した（`6aad421`）。`check-all.py` は 1 回赤（`skill-metrics.py --check`）→ 書き直して **44/44 緑**（`6aad421`）
- 狭いパス（2026-10-23）: 起点 `89c26db`。反証 1 件（N1。直さない——人間が決める）。著者の変異 4 本は赤、Verifier の変異 1 本が素通り（陽性対照あり）
- R10 は人間の決定で dev-loop を 1.45.0 に上げた（版の数字だけ）
- 2 パス目の前の割り目: AskUserQuestion で「**ここで割る**」が選ばれた（2026-10-23）。再開したら Verifier 2 パス目と `/code-review` 2 パス目を、
  受入基準・既知の限界・1 パス目の採否の表を渡して回す（base は上の SHA のまま。**範囲を dev-loop に広げたので、2 パス目の経路一覧に
  dev-loop の差し戻しの経路を足して渡す**）。2 パス目の指摘対応に入る前に、その直前の HEAD の SHA を狭いパスの起点としてここに書く
- 手順 4 の割り目: AskUserQuestion で「**ここで割る**」が選ばれた（2026-10-22）。再開したら手順 5（Verifier 1 パス目）から。`check-all.py` は割り目の時点で 44/44 緑
- 実機確認（受入基準 F。2026-10-22）:
    - **SBIPRISM-207**（手元の `sbi-hubspot` の `docs/shared/qa.csv` を scratchpad に写した。正本は触っていない）——
      前の形のまま新しい検査に当てると 1 で、出力が「移す手順は references/tree.md の「Q&A 表を移す」」を指した。
      選択肢の末尾の `（推奨: …）` を 2 列へ移す小さな変換（`tree.md` の手順 2 のとおり。推奨の無い行は `なし`・`移す前に起票`）を当てると
      **32 行・推奨あり 29・なし 3（Q-018・Q-027・Q-031）・推奨が 2 つ以上 0**、新しい検査は OK（32 行）。
      **Issue の「21 問・推奨 16・なし 5」は起票した当時の件数で、表は今 32 行ある**（その後に足した 11 行と、推奨を付け直した行がある）。
      そこから作った PPTX で、Q-015 の頁に「B: …（推奨）」と「推奨の理由: …」、一覧に「［推奨 A］」が出ることを見た
    - **TFSSTOCKS-37** の Q-104〜Q-118 は**手元に無い**（`tfs-stocks-*` の表は Q-077 まで）。代わりに Issue #330 本文の 2 行を新しい線で分けた——
      **Q-117 は共有**（チャイムが鳴るかが変わる）、**Q-118 は内部・費用は予算の責任者**（変わるのは手段と費用）。共有 1・内部 1・予算の責任者 1。
      `spec-scope.md` の「迷う例」に 2 行とも載せた
- 実験なし（上の実機確認は、検査と生成の出力の目視。主張が偽でも同じ出力になる設定は無い——前の形の表は 1、移した表は 0 で、両方の向きを見た）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 層は列かファイルか | ファイル（人間の決定） | 内部の行が `shared/` に入ると、サインオフの後に内部で決めるたびに照合が割れる。利用者に見せる範囲からも外れる |
| 推奨は列か書式か | 2 列（人間の決定） | 検査で「ラベルが選択肢にある・理由がある」を見られ、`なし` を空と区別できる |
| 費用だけが変わる選択 | 内部の層 → 予算の責任者（人間の決定） | 「費用が変わる → 利用者に訊く」で内部の質問が利用者向けに漏れるのを防ぐ |
| 移行の道具 | 足さない（人間の決定） | 正本で足した描画関数を残したままフックを機械で混ぜるのは脆い。古い見出しは検査とフックが落として手順を指す |
| 内部の表を MkDocs で描くか | 描かない | 受入基準 D は「フックも同じ表を読む」——共有の表の新しい列を読むこと。内部の表は開発者の `spec/` にある |
| リリースした版がある正本の移行 | 移さずに止める（人間の決定） | 凍結した版は直せない。読む側に前の形の道を残すと、2 つの形が残り続ける |
| 内部の表の費用の行は、予算の責任者の合意（`shared/` の照合）に入らない | 採った（限界として書く） | 内部の表は `shared/` の外。費用は `feasibility/` の見積り（根拠に `D-`）に載り、予算の責任者はそれを見て合意する。見積りに載ったかは検証役（estimate-checker）が見る |

### 1 パス目の指摘の採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1/C2 | 移す手順がリリースのタグしか見ず、サインオフのタグ（前の形の表を指す）があると照合と提案書が 2 で止まるのに、取り直しを言わない | 示せる（`check-signoff.py` の `provisional_rows` がタグの時点の表を `read_qa` で読む。Verifier・`/code-review` の両方が挙げた。Verifier は git の実験をガードに拒否されコード読解） | #11 | **直す**（手順 1 にサインオフのタグを足し、移した後に両方を取り直すと書く） |
| C1 | dev-loop の `spec-gap.md` の起票の列が前の 8 列のまま——従って書いた行は新しい検査で落ちる。内部の表にも触れない | 示せる（`spec-gap.md` の列の表） | #10 | **直す**（範囲を dev-loop に広げた。上の「変更範囲」） |
| C3 | `diff-versions` の Q&A の差分に内部の `D-` の行が入り、`req-loop` もその出力を読む | 示せる（差分に D- が出る。`test-diff-versions` の試料） | 無し（#6 は「差分も行で出る」。`req-loop` は手順 1 で共有の表だけを読むと書いた。差分を利用者に見せる経路は提案書だけで、そこは外している） | 残課題 |
| C4 | 提案書の `D-` の絞り込みが描画の関数の中で `diff` を書き換える（`compare` の選択肢にすべき） | 示せる（書き換えは在る） | 無し | 残課題 |
| C5 | `merge-versions` の消す表の振り分けがキーの有無で決まり、他は番号の接頭辞で決める。`scaffold.py` が `INTERNAL_QA_PATH` を写している | 示せる（コード） | 無し（今は `present` の検査が先に弾く） | 残課題 |
| C6 | 移す手順への指し先（検査とフックの 2 つの写し）が `tree.md` の見出しと突き合わせられていない。フックは推奨が空でコロンの無い選択肢を推奨と描く | 見出しの改名は将来。後者は検査を通らない表 | 無し | 残課題 |

### 2 パス目の指摘の採否

2 パス目（2026-10-23）: Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 2 件・`/code-review`（high）指摘 10 件。
Verifier の 2 件は `/code-review` の R1・R2・R3 と重なる（同じ行に畳む）。狭いパスの起点は `89c26db`（2 パス目の指摘対応を始める直前の HEAD）。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1/V-1 | dev-loop の `spec-gap.md` の `No` の行が `Q-` だけを言い、内部の表（`D-`）の採番と「質問」の書き方に触れない | 示せる（`/code-review` が内部の表に `Q-012` を置いて `check-qa-csv.py` が 1） | #10 | **直す** |
| R2/V-2 | 同じく「変更範囲に `docs/v<n>/shared/qa.csv` を足す」だけで内部の表が出てこない | 示せる（`spec-gap.md` の文） | #10 | **直す** |
| R3/V-2 | 同じく手順 4・5 が利用者の判断と `req-loop` を前提にし、内部の行を誰が決めるかが無い | 示せる（`req-loop` は共有の表だけを読む） | #10 | **直す** |
| R4 | `spec-scope.md` の迷う例で、内部の再試行の間隔が「実装に渡す」（146 行）と「内部の表」（150 行）に割れている | 示せる（同じファイルの 2 行） | #10 | **直す**（146 行を「費用に効くなら下の行」に寄せる） |
| R5 | `build-proposal.py` の `compare_at` が内部の表まで重ね、内部の表の違反で提案書が作れない（照合は通る） | 示せる（`/code-review` が `暫定反映` の D- で 1 を再現） | #8 | **直す**（比較の前に内部の表と `removed.csv` の D- の行を外す。`changes_section` の絞り込みは要らなくなるので外す——C4 もこれで消える） |
| R6 | `scaffold.py` の Issue の本文が D- の行も「`build/merged/shared/qa.csv` から写した」と書き、`spec-gap.md` も Q&A の正をその 1 つだけと言う | 示せる（生成する文） | #7・#10 | **直す** |
| R7 | `qa-csv.md` の内部の例 D-001 に「C: 遅れを受け入れる」があり、`spec-scope.md` の線では共有に起票する形 | 示せる（2 つの文書） | #10 | **直す**（C を外す） |
| R8 | `feasibility` の「推奨の選択肢で見積もる」が `推奨` = `なし` のときに決まらない | 示せる（`qa-csv.md` の例 D-002 が `なし`） | #10 | **直す**（`なし` なら選択肢の幅で見積もり名指しする） |
| R9 | 「層を移す」が、元の番号を指しているもの（中間表現の `qa`・見積りの根拠・本文の `Q-008`）を直すと言わない | 示せる（移すと `scaffold` が「Q&A 表に無い」で止まる） | #10・#11 | **直す** |
| R10 | dev-loop の版を patch で上げたが、手順の分岐の追加なので minor（`CLAUDE.md` の刻み方） | 示せる（`CLAUDE.md` の表） | 無し（#12 は版の一致） | 残課題としたが、**人間が「この PR で 1.45.0 に上げる」と決めた**（2026-10-23、AskUserQuestion）。版の数字だけの変更 |

### 狭いパスの指摘

狭いパス（2026-10-23）: `dev-loop:dev-loop-verifier`・sonnet、起点 `89c26db`。反証 1 件（受入基準を破る実害は 0 件）。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | `drop_internal` を最後の版だけに絞る変異が `test-build-proposal.py` を素通りする（内部の表を置いた試料が v2 だけ）。コードは正しい | 示せる（Verifier が複製で v1 の試料を足し、変異ありで 1・元で 0） | #8 の前の版の側が無検査（コードは満たす） | 人間が決める → **起票（#343）** |

## 起票

- この周の起票: 3 件（#343 狭いパスの N1・#344 1 パス目の C3・#345 1 パス目の C5／C6。2026-10-23 に人間が承認）
