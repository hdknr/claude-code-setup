# Issue #1163 — spec-loop: 機能の必須度（MoSCoW）が無く、予算超過のときに削る根拠を示せない

**不在の周**（`/dev-loop:cruise 1169 --absent` の起動・2026-11-17T10:47Z）。利用者には訊かない。親（cruise #1169）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1169`）。利用者の確認（起動時・2026-11-17T10:47:55Z、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`（古い値。後退・未達は推奨で進めない）。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1169.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.7.0（`SKILL.md` 1920 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1169`））。
版の上げ方: `spec-loop` を **minor**（機能一覧の任意の列とその検査・scaffold の照合・見積りと提案書の手順を足す——CLAUDE.md の「能力・手順の追加」）。着手時の main は spec-loop 0.109.0 → 0.110.0。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.7.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: `features.csv` に `必須度` の列（`Must`・`Should`・`Could`・`Won't`。決める人は利用者。未決定なら共有の Q&A 表に起票）（案 1）・
feasibility が必須度ごとの小計を出し、予算・期限に収まる組み合わせ（Must だけ・Must + Should）を提案書の選択肢にする（案 2）・
`Won't` の機能を範囲の文書（`spec/scope.md`）の受け持たない範囲に写し、scaffold の「作らないもの」とつなぐ（案 3）・scaffold の Issue の並びで同じ深さなら Must を先に（案 4。任意）。
決めること: 既存の正本の `features.csv` が「決まりに無い列」で落ちないよう任意の列にするか移し方を書くか・必須度を機能の単位で持つか要求の単位で持つか。コメントは無い。本文に受入基準を緩める指示は無い。
前提（親の委譲文）: #1090 の重ね方（新しい表は一覧に載せない限りファイルの単位で重なる）に従う。main の #1154（目的の表）・#1161（関係者の表）・#1164（用語集）・#1162（CRUD 表）と同じ形（`tree.md`・`check-design-csv.py`）に揃える。目的の層と関係者を指せることを前提にする。

## 決めた値（開発者が決めた——利用者に見える結果が変わらない実現の手段）

- **D1 列の名前は `必須度`、値は `Must`・`Should`・`Could`・`Won't`**（Issue の案のとおり。英語の綴りのまま——MoSCoW の語として通じる）。決める人は利用者（関係者の表の役割 `利用者`）。
- **D2 列は機能一覧の見出しの末尾に置く**（`id,名前,種類,関係,必須度`）。途中に置いた見出しは今までどおり「見出しの行が決まりと違う」（1）。
- **D3 列を置いたら、どの行も値が要る**——空は「必須の欄が空」、未決定の印は「未決定の印」（どちらも 3。scaffold は止まる）。`未定（Q-012）` のように Q&A の番号を添えてよい（ほかの欄と同じ）。
- **D4 検査は `check-design-csv.py` に足す**（成果物の表と同じ「形式の違反 1・未決定 3」に乗る）。重ね方は今までどおり**ファイルの単位**（機能一覧は `versions.md` の一覧に載らない。#1090）。
- **D5 feasibility は機能の規模を必須度ごとに分けて数え、`Won't` の機能を数えない**。組み合わせ（`Must` だけ・`Must` + `Should`・`Could` まで全部）の開発費を規模の文書（`docs/v<n>/feasibility/` の Markdown）に書く。見積りの表（`estimate.csv`）の列は変えない（項目と根拠に必須度を書く）。
- **D6 提案書の代替案**: 見積りが予算・期限に収まらないとき、proposal の手書き部分（変える案・代替案）に D5 の組み合わせを書く。どれを削るかはスキルが選ばない（利用者の必須度と決裁者の判断）。`build-proposal.py` は変えない（手書き部分に書く——Issue の対象も SKILL.md）。
- **D7 案 4（scaffold の Issue の並びで Must を先に）はしない**——Issue が任意と書く。並びは依存で決まり、親 Issue のチェックリスト（`parent-checklist.py`）の書式に効く。PR コメントに名指しする。

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **H1（決めること 1）列を足す形**: (a) **任意の列**——見出しは前からの 4 列でも、末尾に `必須度` を足した 5 列でもよい（推奨）／(b) 必須の列にし、前からの正本の移し方（作業中の版に列を足した一覧を置く）を書く／(c) 別の表（`requirements/priorities.csv`。機能・必須度）。
  推した理由: (a) は前からの正本がそのまま通る（列を置かない正本は必須度を持たない——今までどおり）。(b) は今ある正本がどれも「見出しの行が決まりと違う」（1）で scaffold が止まり、版をまたいで全部の正本に作業を強いる。
  (c) は機能一覧と 2 つの表の id を突き合わせる検査が要り、行を足し忘れた機能の必須度が黙って欠ける（任意の列でも同じ表の中なら行ごとに空が 3 で出る）。
- **H2（決めること 2）必須度を持つ単位**: (a) **機能の単位**（機能一覧の行。推奨）／(b) 要求の単位（決定表の行・Q&A の行）。
  推した理由: 削る単位は作る単位で、scaffold は 1 機能 = Issue 1 件、feasibility も機能を数える。要求の単位に持つと、1 つの機能に掛かる要求の必須度が食い違ったとき（Must の要求と Won't の要求）に機能を作るか決まらない。
  要求の中で優先が違うなら、機能を分ける（機能一覧の行を分ける）ことで表す。
- **H3 `Won't` の機能と中間表現の照合**（Issue に無い。scaffold は機能一覧のどの id も中間表現に要ると照らすので、作らない機能で止まり続ける）: (a) **`Won't` の機能は中間表現に要らず、中間表現に在れば scaffold が止まる**（推奨）／
  (b) `Won't` の機能も中間表現に書き起こす（照合は今のまま）／(c) `Won't` の機能を機能一覧から外す（値に `Won't` を持たない）。
  推した理由: (b) は作らない機能の Red テストと Issue ができ、dev-loop が作ってしまう。(c) は「作らないと決めた」が表に残らず、提案書・見積りで削った機能が見えない（Issue の「削る根拠」が残らない）。
  (a) なら機能一覧に決めたことが残り、作らない機能が Issue になる経路は scaffold が止める。範囲の文書の「範囲の外」への写しは spec-review が書く（`spec-scope.md`）——行の在ることは機械で照らさない（範囲の文書は場面を文で書く表で、機能の id を持つ列が無い）。
- **H4 `Won't` の機能と目的の表**（Issue に無い。目的の表は、機能一覧のどの機能もどれかの指標の `機能` に載ることを求める）: (a) **`Won't` の機能も今のまま指標に載せる**（推奨）／(b) `Won't` の機能は結び付けを求めない。
  推した理由: (a) なら、削った機能がどの指標を動かすはずだったかが表に残り、削った結果どの指標が動かなくなるかを Domain Checker と決裁者が見られる（Issue の「削る根拠」）。検査は変えない。
  (b) は結び付けを外した機能が、なぜ要らないかを表から辿れなくなる。

## 変更範囲

触る:

- `plugins/spec-loop/references/tree.md` — 「機能一覧」の節に `必須度`（任意の列・値・決める人・列を置いたらどの行も要る・`Won't` の扱い・目的の表の結び付け）、「機能一覧と中間表現の照合」に `Won't`
- `plugins/spec-loop/references/spec-scope.md` — 範囲の文書の「範囲の外」に `Won't` の機能を写すこと
- `plugins/spec-loop/scripts/check-design-csv.py` — 機能一覧の任意の列・値の検査と、`Won't` の機能を読む関数（scaffold が読む）
- `plugins/spec-loop/scripts/scaffold.py` — 機能一覧と中間表現の照合で `Won't` を外し、中間表現に在れば止める
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 手順 2 で `Won't` の機能を仕様に書き起こさず、範囲の文書に写す（`spec-scope.md` を指す。実装中に足した——H3 の「写すのは spec-review」をスキルから辿れるように。受入基準は A6 に足す）
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 規模を必須度ごとに数え、組み合わせの開発費を書く
- `plugins/spec-loop/skills/proposal/SKILL.md` — 代替案に組み合わせを書く
- `scripts/test-check-design-csv.py` — 試料・変異・references との突き合わせ
- `scripts/test-scaffold.py` — `Won't` の照合の試料と変異
- `CLAUDE.md` — `check-design-csv.py`・`scaffold.py` の項
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1163.md` — この計画ファイル

触らない:

- `build-proposal.py`・`check-feasibility-csv.py`・`references/feasibility-csv.md`——見積りの表の列を変えない（D5・D6）
- `merge-versions.py`・`versions.md` の一覧（D4）・`check-signoff.py`（機能一覧は `requirements/` の中で、照合の範囲のまま効く）
- `parent-checklist.py` と scaffold の Issue の並び（D7）
- `req-loop/SKILL.md`・`hearing.md`——未決定の欄は `tree.md` の「情報が無いとき」のとおり起票する（req-loop の手順 3・4 がそのまま掛かる）
- `agents/domain-checker.md`——目的の表を照合先にする今の定義のまま（H4）
- screen-spec——機能一覧を列の名前（`id`）で読む（`check-screens.py` の `column`）ので、列を足しても読み方は変わらない
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）・`README.md`・公開ページ——今の要約が偽にならない

依存の追加・更新: なし

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

**複製の数**: 必須度の列の名前・値・決める人・列を置いたらどの行も要ることを述べる箇所は 2（`tree.md` の「機能一覧」が原本、`check-design-csv.py` の定数が写し——`test-check-design-csv.py` が突き合わせる）。
`Won't` を中間表現と照らすことは 2（`tree.md` の「機能一覧と中間表現の照合」が原本、`scaffold.py` の `listed_problems` が実装——`test-scaffold.py` が試料で見る）。
`Won't` を範囲の文書に写すことは 2（`spec-scope.md` が原本、`tree.md` は指す）。見積りの組み合わせは 2（feasibility の手順 2・3 が原本、proposal の手順 2 は指す）。`CLAUDE.md` の項は要約。
分けない理由: 決まりの原本は `references/`、スクリプトは写しを持ち、テストが突き合わせる。スキルは原本を指す。

## デプロイ経路

プラグイン（`marketplace.json` のカタログと、`link-skills.sh` を使う利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口（必須度を書く・読む・照らす場所）: req-loop 手順 3（要求から表を書く）／手順 4（`check-design-csv.py`）・spec-review 手順 2（表の欄が足りない・範囲の文書を書く）・
feasibility 手順 2・3（規模と見積り）・proposal 手順 2（手書き部分）・scaffold の関門（重ねた全体に `check-design-csv.py` と機能一覧の照合）・照合（`check-signoff.py` が `requirements/` を比べる）・
重ね合わせ（`merge-versions.py`）・screen-spec（機能一覧の `id` を読む）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | 必須度の決まり（列の名前・値・決める人=利用者・任意の列で末尾・置いたらどの行も要る・`Won't` は中間表現に要らず在れば止まる・`Won't` は範囲の文書に写す・目的の表の結び付けは `Won't` も求める）が `tree.md` の「機能一覧」の節（照合は「機能一覧と中間表現の照合」、写し方は `spec-scope.md`）にある | 決まりを読む人・スキル | 文書 | 読んで確かめる＋`test-check-design-csv.py` の突き合わせ（列の名前・値・任意の列。決める人は `利用者`・`連携先` のどちらかであることだけ——CR2-4） |
| A2 | `check-design-csv.py` が、`必須度` を末尾に置いた機能一覧を通し（0）、値が 4 つのどれでもない行を 1、途中に置いた・綴りの違う見出しを 1（「見出しの行が決まりと違う」）、列の数の合わない行を 1 で落とす | req-loop／spec-review／scaffold | 検査の関数 | 試料と変異（`test-check-design-csv.py`） |
| A3 | 列を置いた機能一覧で、空のセルを「必須の欄が空」、未決定の印を「未決定の印」（3）で出す | 同上 | 検査の関数 | 試料と変異 |
| A4 | 前からの結果は変わらない——`必須度` の列の無い機能一覧（4 列）で、`check-design-csv.py` の終了コードと文面が変わらない。scaffold の機能一覧の照合も、`Won't` の無い一覧では前と同じ | 前からの正本 | 列が無ければ何もしない | 前からの試料が全部通る（`test-check-design-csv.py`・`test-scaffold.py`） |
| A5 | scaffold の照合が `Won't` の機能を中間表現に求めず（作る）、`Won't` の機能が中間表現に在れば止まる（何も作らない）。`Won't` でない機能が中間表現に無ければ今までどおり止まる | scaffold | `listed_problems` | `test-scaffold.py` の試料と変異 |
| A6 | spec-review の手順 2 が `Won't` の機能を仕様に書き起こさず範囲の文書に写す手順を持ち（`spec-scope.md` を指す）、feasibility が機能一覧の必須度ごとに規模を分けて数え、`Won't` を数えず、組み合わせの開発費を規模の文書に書く手順が `feasibility/SKILL.md` にあり、proposal の手書き部分がその組み合わせを代替案に書き、削る機能をスキルが選ばない手順が `proposal/SKILL.md` にある | spec-review 手順 2／feasibility 手順 2・3／proposal 手順 2 | スキルの文書 | 読んで確かめる |
| A7 | 照合（`check-signoff.py`）が機能一覧の必須度の違いを拾う（`requirements/` の中なので） | proposal の照合 | 照合の範囲のまま | 一時の git リポジトリで、必須度だけ違う 2 つのタグを照合して非 0（陽性対照: 同じなら 0） |
| A8 | screen-spec の機能一覧の読み方が、`必須度` の列を足した一覧でも変わらない（`id` の列で読む） | screen-spec | 読み方のまま | `check-screens.py` の `column` を読んで確かめる＋`check-all.py` |
| A9 | 版を 3 種類で揃えて上げ、`check-all.py` が緑 | CI | 版の行 | `check-all.py`・`check-plugin-versions.py` |
| A10 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: A6 の feasibility・proposal・spec-review（範囲の文書への写し）を実際の正本で走らせ、手順どおりに組み合わせと代替案と範囲の外の行を書くこと（スキルを実際の正本で走らせて観測していない——人間のレビューに回す）。

**生成物**: 生成物なし（変更するファイルに生成物は無い。`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` を測るもので、この周は触らない——`--check` は `check-all.py` で見る）。

## 未解決・確認待ち

- H1〜H4 の確認の Issue（利用者が戻ってから確かめる）: 立てたら番号を書く。

## 実験と確認の記録

- **A7（照合が必須度の違いを拾う）**: 一時の git リポジトリ（`HOME`・`GIT_CONFIG_GLOBAL` を差し替え）で `docs/v1/shared/qa.csv`（見出しだけ）と `docs/v1/requirements/features.csv`（`必須度` の列つき・F-002 が `Should`）を置き、
  同じコミットに `signoff/v1/req-1` と `signoff/v1/budget-1` を付けて `check-signoff.py --req signoff/v1/req-1 --budget signoff/v1/budget-1` → **0**（陽性対照「一致する」）。
  F-002 の必須度だけを `Won't` に変えたコミットに `signoff/v1/budget-2` を付けて同じく → **1**（`M docs/v1/requirements/features.csv`）。観測窓: v1 だけ・1 回。

## 関門の記録

```dev-loop-gates
周の base: 53517d593b60a75123648e6f26b0d77dd669b1d1
関門: Verifier 1 083d05a4f3f20b6cd76f2889d25642f006a5ae78 反証=0
関門: /code-review 1 083d05a4f3f20b6cd76f2889d25642f006a5ae78 指摘=9
関門: Verifier 2 15c60a0b3f74e3fc0a3cdc61366c98c281e22f80 反証=0
関門: /code-review 2 15c60a0b3f74e3fc0a3cdc61366c98c281e22f80 指摘=7
```

## 手順 8（起票）

- この周の起票: 4 件（仕様の穴 H1〜H4 の確認の Issue。起票の承認は不在のため訊いていない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1163-feature-priority`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1163`・起点 `53517d5`・base の参照 `origin/main`（解決した SHA `53517d593b60a75123648e6f26b0d77dd669b1d1`）
- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目の起点（先に当てた Verifier に渡した時点の HEAD）: `083d05a4f3f20b6cd76f2889d25642f006a5ae78`
- 手元の歯止め: `check-all.py`（run-serial 越し）緑（67/93 本を回した・失敗 0・残りは CACHED。083d05a の作業ツリー）
- Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet。受入基準の表を委譲文に展開して貼り、全文はファイルで読ませた）: 反証 0 件。`test-check-design-csv.py`・`test-scaffold.py`（run-serial 越し）緑、A7 を独立に再現。A4 は旧版との直接比較をしていない（未確認）。git status は前後とも計画ファイルだけで同じ。報告は SubagentHandback で届かず、`SendMessage` で催促したあと子の transcript から読んだ
- `/code-review` 1 パス目（high。起動の引数で受け渡しの文面のファイルを指し、全文 149 行を読んだと報告）: 指摘 9 件（直す 2・残課題 7）。手順 4 への差し戻し: あり（直すの 2 行）。git status は前後とも計画ファイルだけで同じ
- 割り目（手順 6 の 2 パス目の前）: 割らない（cruise の周）。残っているもの: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方
- 再開（2026-11-18T06:40Z の `/dev-loop:cruise 1169 --absent` の起動で親から委ねられた子。読み込んだ dev-loop は 2.8.0・`SKILL.md` 1923 行）: 前の子が止まったところの未コミットの 4 ファイルを読み、直すの 2 行（V1-2＝CR1-4・CR1-6）は直し終わっていると判断した（差分が採否の表の「直す」の中身どおり）。
  `test-check-design-csv.py`（run-serial 越し）緑（試料 181・変異 148・references の崩し 38）。main は 53517d5 のまま（取り込みなし）
- 1 パス目の指摘対応の終点（2 パス目の関門に渡した HEAD）: `15c60a0b3f74e3fc0a3cdc61366c98c281e22f80`（直しは 083d05a → 15c60a0 の 1 コミット）
- 手元の歯止め（1 パス目の直しの後）: `check-all.py`（run-serial 越し）緑（15/93 本を回した・失敗 0・残り 78 本は CACHED）
- Verifier 2 パス目（`dev-loop:dev-loop-verifier`・sonnet。参照＋差分で `prompts/verifier.md`（186 行と報告）を読ませ、受入基準・既知の限界は貼った）: 反証 0 件。
  旧版（53517d5）と新版の `check-design-csv.py` を同じ入力で走らせ、4 列の見出しの誤りの文面と終了コードが同じ（A4）。`test-check-design-csv.py`・`test-scaffold.py`（run-serial 越し）緑。git status は前後とも空。
  報告は SubagentHandback で届かず、`SendMessage` で催促したあと子の transcript から読んだ
- `/code-review` 2 パス目（high。起動の引数で受け渡しの文面のファイル（162 行と報告）を指した）: 指摘 7 件（直す 1・残課題 6）。git status は前後とも空。
  `test-check-design-csv.py`・`test-scaffold.py` は順番待ちが長く TaskStop で止めて回していない（未確認と報告）。報告は transcript から読んだ
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `15c60a0b3f74e3fc0a3cdc61366c98c281e22f80`
- 手元の歯止め（2 パス目の直しの後）: `check-all.py`（run-serial 越し。順番待ち 2856 秒）緑（93/93 本を回した・失敗 0）

## 既知の限界・決着済みの論点

（関門に毎パス渡す。決着の理由が誤っていると判断したなら、それは新しい反証である）

- 上の H1〜H4 と D1〜D7。
- `Won't` の機能が範囲の文書の「範囲の外」に写っているかは機械で照らさない（H3。範囲の文書は場面を文で書く表で、機能の id の列を持たない）。
- 見積りの表の列は変えず、組み合わせの開発費は規模の文書（Markdown）に書く（D5）——検査（`check-feasibility-csv.py`）は小計を見ない。
- 周の途中の課題の振り分け（found-lines。線 `周の途中の課題 = 外に出す`）は下に足す。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-1（Verifier）: 見出しの綴りの誤り（`必須 度`）で「物理設計はこの表に書かず…」の前からの文面が出る | 示せる | 無し（前からの文面。決まりに無い列の案内） | 残課題 |
| V1-2＝CR1-4: 4 列の機能一覧の見出しの誤りの文面に「末尾に任意の列 必須度 を足してよい」が足された | 示せる（旧版と新版を同じ入力で走らせて文面が違う——`/code-review` が scratchpad の `p1a4` で実測） | A4（4 列の一覧で文面が変わらない） | 直す——任意の列の名前を見出しに書いたときだけ言い添える。試料「4 列の見出しの誤りは前からの文面」と変異 2 件 |
| CR1-1: 前の版で作った機能を v2 で `Won't` にすると scaffold が止まり、案内どおり `removed.csv` に書くと撤去の Issue ができる | 示せない（設計の論。決めた振る舞いどおり） | 無し（A5 のとおり） | 残課題 |
| CR1-2: CRUD 表の抜け（#1162）が `Won't` の機能の行も作る・読む・消す機能に数える | 示せる（`F-002,注文,C` の F-002 が Won't でも抜けが出ない——読んだ。走らせていない） | 無し（A の表に CRUD 表は無い） | 残課題 |
| CR1-3: feasibility で必須度が未決定の機能がどの組み合わせにも入らず、「Could まで全部」の合計が少なく出る | 示せない（スキルの振る舞い） | 無し（A6 は未決定の扱いを決めていない） | 残課題 |
| CR1-5: proposal が引く規模の文書（`feasibility/`）は 2 つの承認の照合の範囲の外 | 示せない（前からの設計。見積りの表も同じ） | 無し | 残課題 |
| CR1-6: proposal は組み合わせを 2 つ、feasibility・tree.md は 3 つと書く | 示せる（文書を読んだ） | A6（proposal が feasibility の「その組み合わせ」を書く） | 直す——proposal の手順 2 を feasibility の手順 3 の組み合わせ（3 つ）を指す形にした |
| CR1-7: `Won’t`（U+2019）を貼ると違反になり、文面では見分けられない | 示せる | 無し（A2 の「4 つのどれでもない」どおり） | 残課題 |
| CR1-8: `wont_features` が `listed_features` と同じ表を読み直す | 示せない（振る舞いは同じ） | 無し | 残課題 |
| CR1-9: screen-spec の画面の表・モックが `Won't` の機能の画面を止めない | 示せない（読んだだけ） | 無し（A8 は読み方が変わらないこと） | 残課題 |

### 2 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1: `tree.md` の「機能一覧と中間表現の照合」の前からの項（前の版で作った機能を作らないなら一覧の行を外す——両方要る）が、新しい項（`Won't` の行は残してよい・行を一覧から外さない）と食い違う | 示せる（`tree.md` の 372 行と 245・375 行を読んだ） | A1（`Won't` の行を一覧に残す決まりが、同じ文書の別の項と食い違う） | 直す——前からの項に「`必須度` を `Won't` にするなら行は外さない」を足した |
| CR2-2: feasibility で、必須度の違う機能が共有する画面・業務ルールをどの小計に入れるかが無い | 示せない（スキルの振る舞い） | 無し（A6 は手順があることまで） | 残課題 |
| CR2-3: v1 で作った機能を v2 で `Won't` にしたとき、feasibility が撤去の費用を数えない | 示せない（スキルの振る舞い。CR1-1 と同じ形） | 無し | 残課題 |
| CR2-4: A1 の証明の「突き合わせ（決める人）」は、決める人が `利用者`・`連携先` のどちらかであることしか見ず、`tree.md` の新しい決まり（どの行も要る・`Won't` の照合・目的の表）を突き合わせない | 示せる（`/code-review` が `reference_mismatches` に崩した `tree.md` を当てて [] を実測） | 無し（A1 の不変条件は文書に決まりがあること。証明の書き方が広すぎた——計画の A1 の証明の欄を直した） | 残課題 |
| CR2-5: proposal の手書き部分が規模の文書から写す金額と、生成する費用の節が食い違いうる | 示せない（筋書き） | 無し | 残課題 |
| CR2-6: feasibility の手順 5 が必須度の質問を起票し、req-loop・spec-review の起票と重なりうる | 示せない（筋書き） | 無し | 残課題 |
| CR2-7: 見出し `id,名前,種類,必須度`（関係を必須度で上書き）で、前の版の「決まりに無い列（必須度）」の行が出なくなり、欠けた列を名指さない | 示せる（`/code-review` が新旧で走らせて実測） | 無し（A2 の「1」どおり。前の版も欠けた `関係` は名指していない） | 残課題 |

