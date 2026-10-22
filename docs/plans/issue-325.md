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
- `plugins/spec-loop/.claude-plugin/plugin.json`・`.claude-plugin/marketplace.json` — 版（minor: 0.15.0）
- `scripts/test-check-qa-csv.py`・`scripts/test-qa-to-pptx.py`・`scripts/test-check-spec-exit.py`・`scripts/test-scaffold.py`・
  `scripts/test-check-signoff.py`・`scripts/test-build-proposal.py`・`scripts/test-init-mkdocs.py` — 試料・期待・変異
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

## 乗るデプロイ経路

プラグインの版を上げて配布する（`marketplace update` → `plugin update`）。`docs/` は main への push で GitHub Pages。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| 1 | `暫定反映` の行は検査を通り、`回答` が `未回答`／`反映先` が `—` なら落ちる | `check-qa-csv.py` | `REFLECTED` で「回答あり・反映先あり」を求める |
| 2 | 暫定の行が資料に載り、未反映と言い回しが分かれる（表紙の件数・一覧・各問） | `qa-to-pptx.py` | 表紙・一覧・各問で状態を見て書き分ける |
| 3 | 反映済みの行は資料に載らないまま | 同上 | `read_pending` の絞り |
| 4 | `暫定反映` は抜ける条件 1 を止めず、`確認中` と未知の状態は止める | `check-spec-exit.py`（`spec-review`・`scaffold` が呼ぶ） | `REFLECTED` の外を数える（列挙の外は止める側） |
| 5 | 中間表現が `暫定反映` の Q&A を指しても scaffold が止まらず、`確認中` なら止まる | `scaffold.py` の `check_qa_refs` | 同上 |
| 6 | req タグの時点の重ねた Q&A に `暫定反映` が残れば照合が 3 で、提案書を書かない。後の版で `反映済み` に置き換えた・`removed.csv` で消した行は数えない | `check-signoff.py`・`build-proposal.py` | 版を順に重ねて数える（`versions.md` の「重ねるもの」） |
| 7 | MkDocs のページの件数が暫定を「回答あり・未反映」に数えない | フック | `QA_PROVISIONAL` を分けて数える |
| 8 | 決まり（`qa-csv.md`）・`req-loop` の手順が、暫定の書き方・確定のときの書き換え・変わったときの反映し直しを持ち、スクリプトの挙動と食い違わない | 文書 | 試料で確かめる |
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
- `check-all.py`: **結果を回収していない**（割り目の時点で実行中だった）。**再開したら最初に回し直す**
- 手順 4 の割り目: AskUserQuestion で「**ここで割る**」が選ばれた（2026-10-22）
- 関門: **まだどれも通していない**。次は手順 5（Verifier 1 パス目）と手順 6（`/code-review` 1 パス目）。base は上の SHA

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 状態か列か | 状態（人間の決定） | 見出し行が変わらない |
| 暫定で抜ける条件を満たしてよいか | よい（人間の決定） | 仕様には反映済み。開発へ進む前にサインオフで止める |
| `check-signoff.py` の重ね合わせは Q&A の行だけを自前で重ねる（`merge-versions.py` の `merge` を使わない） | 採った | `merge` は版の中身の全部を検査するので、Q&A と無関係な決まりの違反で照合が 2 に変わる。重ね方（同じ No は置き換え・`removed.csv` で消す）はテストで `merge-versions.py` の結果と突き合わせる |
