# Issue #325 — 暫定で採った回答を利用者に確認してもらうレビュー会の資料を作れるようにする

## 変更範囲

触る:

- `plugins/spec-loop/references/qa-csv.md` — 状態 `暫定反映` と、暫定の回答の書き方・確定したときの書き換え。**決まりの原本**
- `plugins/spec-loop/scripts/check-qa-csv.py` — `STATES` に `暫定反映`、`PROVISIONAL`・`REFLECTED`（反映した状態）。`暫定反映` にも「回答あり・反映先あり」を求める
- `plugins/spec-loop/scripts/qa-to-pptx.py` — 暫定の行を載せ、表紙・一覧・各問の言い回しを未反映と暫定で分ける。全行を読む `read_rows` を足す
- `plugins/spec-loop/scripts/check-spec-exit.py` — 条件 1 を「反映した状態（`REFLECTED`）でない行」で数える（資料に載る行とは別の定義になる）
- `plugins/spec-loop/references/spec-exit.md` — 条件 1 の文言
- `plugins/spec-loop/scripts/scaffold.py` — 中間表現が指す Q&A は反映した状態（`REFLECTED`）であればよい
- `plugins/spec-loop/references/spec-ir.md` — 同上の文言
- `plugins/spec-loop/scripts/check-signoff.py` — req タグの時点の Q&A（v1〜v<n> を重ねたもの）に `暫定反映` が残れば 3
- `plugins/spec-loop/scripts/build-proposal.py` — docstring の終了コードに 3（照合の 3 をそのまま返す）
- `plugins/spec-loop/references/signoff-tags.md` — 暫定の行が残るうちは req のサインオフを付けない・照合が 3 で落とす
- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — 件数の行に暫定反映を分けて出す（`QA_PROVISIONAL` の写し）
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 手順 1 の分類に暫定、確定のときの書き換え、資料に載ること、暫定の回答を書いてよい条件
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 「`反映済み` でない」の文言
- `plugins/spec-loop/skills/proposal/SKILL.md` — 照合の 3 の扱い（書いてあれば）
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（minor: 0.16.0。main が #333 で 0.15.0 に先に到達したので、取り込んでもう 1 つ上げた）
- `.claude-plugin/marketplace.json` — 同上
- `scripts/test-check-qa-csv.py` — 試料・期待・変異
- `scripts/test-qa-to-pptx.py` — 同上
- `scripts/test-check-spec-exit.py` — 同上
- `scripts/test-scaffold.py` — 同上
- `scripts/test-check-signoff.py` — 同上
- `scripts/test-build-proposal.py` — 同上
- `scripts/test-init-mkdocs.py` — 同上
- `CLAUDE.md` — スクリプトの説明（`check-spec-exit.py` が `qa-to-pptx.py` の定義で読む、の記述・`check-signoff.py`）
- `docs/plugins/index.md` — 「反映済みでない Q&A」の文言（該当すれば）
- `docs/plans/issue-325.md` — この計画

触らない:

- `--include-provisional` のような指定（暫定の行は既定で資料に載せる。確認してもらうための資料なので）
- `agents/estimate-checker.md`（`確認中` の行を見る記述。暫定の回答の費用への影響は今回の範囲外）
- `確認中` の行が残るときの req サインオフの扱い（今まで通り制限しない）
- dev-loop の `references/spec-gap.md`（差し戻しは `確認中` で起票する。変わらない）

### 同じことを述べている箇所の数

状態の名前と意味: 原本 `qa-csv.md`、写し `check-qa-csv.py`・フック（どちらもテストが突き合わせる）、
言及 `req-loop`・`spec-exit.md`・`spec-ir.md`・`scaffold/SKILL.md`・`signoff-tags.md`・`CLAUDE.md`・`docs/plugins/index.md`——約 10 箇所。
分けない理由: 状態を 1 つ足すという 1 つの決定で、どれか 1 つでも古いと「反映した行」の定義が食い違う。

## 決めたこと（人間の決定。2026-10-22、AskUserQuestion）

- **表し方**: 状態 `暫定反映` を足す（列は足さない——見出し行が変わらないので既存の表は通る）
- **抜ける条件**: `暫定反映` は仕様レビューを抜ける条件 1・scaffold を止めない（反映した行に数える）
- **サインオフ**: req タグの時点に `暫定反映` の行が残れば `check-signoff.py` が非ゼロで落とす（提案書も作られない）
- **scaffold**（2026-10-22、1 パス目の `/code-review` 指摘 R1 を受けて、AskUserQuestion）: **中間表現が `暫定反映` の Q&A を指せば
  scaffold は止める**（`確認中` と同じ扱い）。抜ける条件 1 は今のまま暫定で抜けられる。
  理由: scaffold の経路は `check-signoff.py` を通らないので、「開発へ進む前にサインオフで止める」が scaffold → dev-loop では成り立たない

## 乗るデプロイ経路

プラグインの版を上げて配布する（`marketplace update` → `plugin update`）。`docs/` は main への push で GitHub Pages。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | `暫定反映` の行は検査を通り、`回答` が `未回答`／`反映先` が `—` なら落ちる | `check-qa-csv.py` | `REFLECTED` で「回答あり・反映先あり」を求める |
| 2 | 暫定の行が資料に載り、未反映と言い回しが分かれる（表紙の件数・一覧・各問） | `qa-to-pptx.py` | 表紙・一覧・各問で状態を見て書き分ける |
| 3 | 反映済みの行は資料に載らないまま | 同上 | `read_pending` の絞り |
| 4 | `暫定反映` は抜ける条件 1 を止めず、`確認中` と未知の状態は止める | `check-spec-exit.py`（`spec-review`・`scaffold` が呼ぶ） | `REFLECTED` の外を数える（列挙の外は止める側） |
| 5 | 重ねた Q&A 表に `暫定反映` の行が残れば、**中間表現が指すかどうかに依らず** scaffold が止まり（指す Q&A が `確認中` でも止まる）、`反映済み` だけなら通る。**人間の決定で 1 パス目と 2 パス目に書き換えた**（元は「暫定でも止まらない」→「指せば止まる」→ 今の形） | `scaffold.py` の `read_whole`（関門）・`check_qa_refs` | 関門で `暫定反映` の行を数えて止める |
| 6 | req タグの時点の重ねた Q&A に `暫定反映` が残れば照合が 3 で、提案書を書かない。後の版で `反映済み` に置き換えた・`removed.csv` で消した行は数えない | `check-signoff.py`・`build-proposal.py` | 版を順に重ねて数える（`versions.md` の「重ねるもの」） |
| 7 | MkDocs のページの件数が暫定を「回答あり・未反映」に数えない | フック | `QA_PROVISIONAL` を分けて数える |
| 8 | 決まり（`qa-csv.md`）・`req-loop` の手順（**2 パス目に人間の決定で `spec-review`・`feasibility` の反映の手順を足した**）が、暫定の書き方・確定のときの書き換え・変わったときの反映し直しを持ち、スクリプトの挙動と食い違わない | 文書 | 試料で確かめる |
| 9 | 版が 3 種類で揃い、歯止めが全部緑 | bump 漏れ | `python3 scripts/check-all.py` |

組み合わせ: 2 × 4（資料に載る行と、抜ける条件で数える行が**別の定義**になる——暫定は前者に入り後者に入らない）。
4 × 6（抜けられても、サインオフで止まる）。1 × 6（検査を通らない表は照合でも読めない＝2）。

**この環境では証明できないもの（未証明）**: 実案件の正本リポジトリでの通し（手元に無い）。PowerPoint で開いた見た目（CI に無い。XML の整形式と載る文字列までを見る）。

生成物: リポジトリに commit した PPTX・`scaffold/` は無い。`SKILL.md` の測定値は dev-loop だけで、触らない。図なし。**生成物なし**。

## 未解決の判断・確認待ち

無し。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/325-provisional-answers`・worktree `.claude/worktrees/issue-325`・
  起点 `9d74693`・base 参照 `origin/main` → `9d746936a1527bb633edcccbac606a766d511a11`
- 実装: `21664bb` で済み。個別のテストは緑（`test-check-qa-csv` 45/36・`test-qa-to-pptx`・`test-check-spec-exit` 28/23・
  `test-scaffold` 160/110・`test-check-signoff` 51/39・`test-build-proposal` 37/30・`test-init-mkdocs` 32/50。試料/変異）
- 実機確認: `qa-csv.md` の例の表から PPTX を作り、表紙が「回答待ち・未反映 2 件／暫定の回答 1 件」に分かれ、
  一覧に `Q-003（暫定）`、Q-003 の頁に「暫定の回答（反映済み・確認待ち）」と反映先、反映済みの Q-001 が載らないことを見た。
  抜ける条件 1 は暫定と反映済みだけの表で 0、確認中を含む表で確認中の 2 行を挙げて満たさない
- 実験なし（交絡を潰す対象の実験は無い。上の実機確認は出力の目視）
- `check-all.py`: 割り目の時点で実行中だった回は **44/44 緑**（`21664bb` の上）。再開後に `74dd3ab` で回し直し中
- 手順 4 の割り目: AskUserQuestion で「**ここで割る**」が選ばれた（2026-10-22）
- 関門 1 パス目（2026-10-22）: **Verifier 反証 0 件**（sonnet）・**`/code-review` 指摘 10 件**（high）。採否は下の「1 パス目の指摘の採否」
- 1 パス目の指摘対応: R1・R4・R6・R7・R8 を直して `6daa791` にコミット。`test-scaffold` 160/111・`test-check-signoff` 52/40 緑
  （R6 の検査に既存の試料 2 件が当たった——同じ版で置きつつ消す、決まりに反する配置だったので試料を直した）。
  `check-all.py` は `6daa791` で **44/44 緑**。
  **残るのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方**（どちらも未着手）。base は上の SHA のまま
- 2 パス目の前の割り目: AskUserQuestion で「**ここで割る**」が選ばれた（2026-10-22）。再開したら Verifier 2 パス目と
  `/code-review` 2 パス目を、受入基準（#5 は書き換え済み）・既知の限界・採否の表を渡して回す。
  2 パス目の指摘対応に入る前に、その直前の HEAD の SHA を狭いパスの起点としてここに書く
- 関門 2 パス目（2026-10-22）: **Verifier 反証 0 件**（sonnet。`check-all.py` 44/44 緑。軽微な観察 1 件 V1）・
  **`/code-review` 指摘 8 件**（high）。採否は下の「2 パス目の指摘の採否」
- 狭いパスの起点: `5a3d9c340037a391594ca7ce1fbb3b008c4e496f`（2 パス目の指摘対応を始める直前の HEAD）
- 2 パス目の指摘対応: C1（人間の決定で #5 を広げた）・C2・C3・C4（人間の決定で #8 を広げた）・C5・C6・C7 を直す。
  `test-scaffold` 161/111 緑。`bbfa678` にコミット。`check-all.py` で `check-description-sync.py` が赤（proposal の要約と JSON だけ直した）
  → scaffold の要約も挙動と食い違っていたので直し、残り 3 本は trailer で免除（`Skip-description-sync`）
- 狭いパス（2026-10-22。`dev-loop:dev-loop-verifier`・sonnet。起点 `5a3d9c3`）: **不変条件 1〜7 の破れなし・指摘 2 件**（N1・N2。採否は人間が決める）。
  Verifier の変異: 赤 1（前の版を `gate=True` で読む——ただし赤の理由はパスの変数の規則）、素通り 0、設計のみ 2（`.strip()` を外す——等価、`return 1`→`0`——著者の変異と同型）
- 2 パス目の割り目: 該当なし（2 パス目は割らずに続けた）。3 パス目は無い
- `check-plan-scope.py` が 1 回赤（`触る:` の 1 行に複数パターン）→ 1 行 1 パターンに直して緑

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 状態か列か | 状態（人間の決定） | 見出し行が変わらない |
| 暫定で抜ける条件を満たしてよいか | よい（人間の決定） | 仕様には反映済み。開発へ進む前にサインオフで止める |
| 暫定で scaffold を通してよいか | **通さない**（人間の決定。1 パス目） | scaffold の経路は照合を通らない |
| `check-signoff.py` の重ね合わせは Q&A の行だけを自前で重ねる（`merge-versions.py` の `merge` を使わない） | 採った | `merge` は版の中身の全部を検査するので、Q&A と無関係な決まりの違反で照合が 2 に変わる。重ね方（同じ No は置き換え・`removed.csv` で消す）はテストで `merge-versions.py` の結果と突き合わせる |

### 1 パス目の指摘の採否

Verifier（`dev-loop:dev-loop-verifier`・sonnet）: **反証 0 件**（`test-scaffold`・`test-init-mkdocs`・`test-build-proposal` は回していない）。
`/code-review`（high）: **10 件**。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| R1 | scaffold は照合を通らないので、暫定の回答が確認前に Issue になる | 示せる（`scaffold.py:302` が `REFLECTED` を通し、scaffold の SKILL・スクリプトに照合の呼び出しが無い） | #5 の前提（決着の理由が誤り） | **直す**（人間の決定: scaffold は暫定で止める） |
| R2 | Issue 本文の Q&A に状態が写らず、暫定が確定に見える | R1 を直せば、暫定の行は Issue に載らない | 無し | 残課題（R1 で消える） |
| R3 | 暫定のうちに付けた予算のサインオフは、確定の書き換えで一致しなくなる | 示せる（確定で `qa.csv` の回答と状態が変わる） | 無し（「一致しなければ取り直す」の既存の決まりで扱える。注意書きが無いだけ） | 残課題 |
| R4 | req-loop 手順 2.3 が「反映したことを表す状態」のまま、暫定なら `暫定反映` と書いていない | 示せる（`req-loop/SKILL.md` 手順 2.3 の文） | #8 | **直す** |
| R5 | 既に写したフックは古いまま、移行の手順が無い | 示せる（`init-mkdocs` は在るファイルを変えない） | 無し（#7 は雛形の件数。古いフックは壊れず件数がずれるだけ） | 残課題 |
| R6 | `provisional_rows` が同じ版で置いて消した行を黙って落とす（`merge` は拒否する） | 示せる（その配置で `merge-versions.py` は拒否、照合は 0） | #6（「重ね方は `merge` と同じ」の決着の理由が、この配置で誤り） | **直す**（その配置を 2 にする） |
| R7 | `signoff-tags.md` で、既存の「提案書は一致したときだけ」と CI の注記が新しい見出しの下に入った | 示せる（`signoff-tags.md` の該当行） | #8（この差分が入れた文書の退行） | **直す** |
| R8 | 一致しない かつ 暫定あり は 3 になり、proposal の SKILL の 3 の行が食い違いに触れない | 示せる（`check-signoff.py` の分岐と `proposal/SKILL.md:73`） | #8（文書がスクリプトの挙動と食い違う） | **直す** |
| R9 | 前の版に残った暫定の行を、作業中の版の req-loop・資料が出さない | 示せない（前の版を暫定のまま残して次の版へ進む実データが無い） | 無し | 残課題 |
| R10 | `provisional_rows` が `removed_shared_rows` の読み込みを写し、余計に git を呼ぶ | 示せる（重複） | 無し | 残課題 |

### 2 パス目の指摘の採否

Verifier（sonnet）: **反証 0 件**。`/code-review`（high）: **8 件**。

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| C1 | scaffold は中間表現が指した `暫定反映` でしか止まらず、指さない暫定の行は Issue になる | 示せる（レビューが試料で再現: 指さなければ `--dry-run` が 0、指せば 1） | #5（**人間の決定で広げた**——決着の理由「scaffold は照合を通らない」が指さない行で成り立たない） | **直す**（関門で暫定の行を数える） |
| C2 | 3 のあと「要求確定だけ取り直す」と案内するが、確かめると `qa.csv` が変わり予算の合意も一致しなくなる | 示せる（`shared/qa.csv` は照合の範囲で、確定で `状態` が変わる） | #8 | **直す**（両方を取り直すと書く。スクリプトの出力・`signoff-tags.md`・proposal） |
| C3 | `spec-exit.md` の「暫定を根拠にした機能は scaffold が作らない」がコードより強い | 示せる（C1 と同じ） | #8 | **直す**（C1 で事実にし、文言を合わせる） |
| C4 | spec-review・feasibility の反映の手順が暫定と確定を分けない | 示せる（両 SKILL の文） | #8（**人間の決定で広げた**） | **直す** |
| C5 | `signoff-tags.md` の「タグはスキルが付けない」が新しい見出しの下に入った | 示せる（base の配置と差分） | #8 | **直す**（元の節へ戻す） |
| C6 | proposal の frontmatter・JSON の説明が「一致したときだけ生成」のまま | 示せる（frontmatter の文と 3 の分岐） | #8 | **直す**（3 か所とも） |
| C7 | 例の回答「推奨案を暫定で採用」が、推奨を回答の列に書かない決まりと食い違う | 示せる（`req-loop/SKILL.md` の推奨の書き方） | #8 | **直す** |
| C8 | check-signoff が全版の `qa.csv` に今の検査を当て、凍結した前の版が後の決まりで落ちうる | 示せない（決まりを厳しくした実例が無い） | 無し | 残課題 |
| V1 | `provisional_rows` が「前の版に無い行を消す」「同じ行を 2 度消す」を拒否しない（`merge` は拒否） | 示せる（その配置で照合は 0/3） | 無し（数える暫定の行は変わらない） | 残課題 |

### 狭いパスの指摘（直さない。採否は人間が決める）

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| N1 | C2 で直した照合の 3 の出力（両方を取り直す）を、どのテストも見ていない | 示せる（`test-check-signoff.py` に該当の assert が無い。変異は設計のみ） | 無し | 人間が決める |
| N2 | v1 で `暫定反映` の Q&A を指した中間表現は、v2 でその行を `反映済み` に置き換えても、前の版の検査（`check_qa_refs`）で「前の版の中間表現が決まりに反する」と止まる。照合（#6 は置き換えた行を数えない）と非対称 | 示せる（Verifier が試料で exit 1 を再現。指していない行なら 0）。ただし v1 が暫定のまま scaffold もリリースもできないので起きにくい。`bbfa678` より前からある挙動 | #5（「`反映済み` だけなら通る」を重ねた表の話と読めば破らない） | 人間が決める |
