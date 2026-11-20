# Issue #1333: 仕様レビューを抜けた仕様が scaffold で「確かめる入口が無い」「表を読まない」で詰まる

## 変更範囲

触る:

- `plugins/spec-loop/scripts/check-spec-exit.py` — `case_rows` がテストケースの節（`#` の見出しの末尾がテストケースの語・小見出しの下を含む。1 パス目の指摘で直した）の中の、見出しが `ID`・`No`・`項番`（`ID_HEADER`）の表も読む。docstring
- `plugins/spec-loop/scripts/scaffold-estimate.py` — docstring の「守らないもの」の限界の行だけ
- `plugins/spec-loop/references/spec-exit.md` — 「テストケースの表の見出し」（雛形）を足す・「テストケースの番号の重複」の `ID` の表の読み方・「仕様の規模」の数え方を道具の件数にそろえる・記録の表の `記法の移行` の定義
- `plugins/spec-loop/references/spec-ir.md` — 「入口と観測点を置いてよい範囲」を足す（発行した知らせのケースは受入基準に回す）・「書き起こすときの決まり」から指す
- `plugins/spec-loop/skills/spec-review/SKILL.md` — Planner に雛形を使わせる・記録の `テストケース` の列を `scaffold-estimate.py list` の件数で書く
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 守ることと手順 1a から「入口と観測点を置いてよい範囲」を指す・分け方の決まり・3 のときの案内
- `scripts/test-check-spec-exit.py` — 試料と変異
- `scripts/test-scaffold-estimate.py` — 試料
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版 0.127.3 → 0.128.0
- `.claude-plugin/marketplace.json` — 同上
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1333.md` — この計画

触らない:

- `scaffold.py`（`spec_case_rows` は `case_rows` を読むだけ——写しを持たない）・中間表現の形（知らせを読み返す観測点の形は足さない。下の「決めたこと」）
- `ID` の表を見つけたときの警告（Issue の案のもう片方。採らない——下の「決めたこと」）
- `CLAUDE.md`（スクリプトの説明は原本を指すだけ）

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）
依存の追加・更新: なし

版の上げ方: spec-loop を minor で 1 つ上げる（0.x なので能力の追加も minor。マージ直前に main が進んでいたら、main の先端の spec-loop の版から minor で 1 つ上げた値に上げ直す。parallel.md の「版とマージの順」）

## 不在の周と線

- 不在の周: `/dev-loop:cruise 1374 --absent` の起動（2026-11-20）の子。
- 台帳の確かめた線（出所: 利用者の確認——起動時・親 Issue #1374 の `cruise:` の行・2026-11-20T11:38:12Z、配布を見せて確かめた）:
  - 直す線 = 既定
  - 仕様の穴 = 推奨で決めて起票
  - マージ = 関門を通ればマージ（マージは親がする）
  - 周の途中の課題 = 外に出す
  - マージ前の判断 = 推奨で決めて起票（後退・未達を含む）
  - 実機確認: 線なし（止まる）

## デプロイ経路

main へのマージ → GitHub Pages の再ビルドとプラグインの配布（`.claude/dev-loop.md` の「マージの反映: ドキュメントとプラグインの配布」）。spec-loop の `references/`・`scripts/` はサイトの `docs/` の外——配布はプラグインの版で届く。

## 決めたこと（Issue が選択肢を示し、実装に任せたもの）

- 提案 1 の「どちらか」: **テストケースの節の `ID` の表も読む**を採った。警告は採らなかった——警告だけでは Issue の受入基準 2（見積もりが「表が無い」で止まらない）を実案件の形（`| ID |` の表）で満たせず、節の外の `ID` の表（Q&A・NFR）を全部警告すると誤報が多い。節は直前の ATX 見出し（`#`）で決め、下線の見出しは読まない（限界として記した）。
- 提案 3 の「足すか、無いなら扱いを書く」: **形は足さず、受入基準に回す**を採った。形を足すと `scaffold.py` の生成と Red テストの口が増え、この周の大きさが変わる（Issue の受入基準 3 は「書かれている」まで）。仕様が読み返す入口を振る舞いとして書いていれば `after` で Red テストにできる、と併記した。
- 置いた入口・`seed` の名前は Q&A 表に書き戻さない（scaffold は Q&A 表を書かない。中間表現に残る）。

## 周の大きさ

- 雛形の見出し: 原本は spec-exit.md の「テストケースの表の見出し」。spec-review の SKILL.md は見出しの 1 行を写して指す（複製 2）。分けない理由: Planner が手順を読む場所で雛形が要る——原本を指して写しは 1 行に留める。
- `ID_HEADER` の正規表現: 原本は spec-exit.md、写しは check-spec-exit.py（テストが突き合わせる。`CASE_HEADER` と同じ形）。複製 2。
- 入口と観測点の範囲: 原本は spec-ir.md、scaffold の SKILL.md は分け方の要約（3 行）と指し先。複製 2。分けない理由: 手順 1a で分けるときに要る判断なので、手順に要約が要る。
- 件数の数え方: 原本は spec-exit.md の「仕様の規模」。spec-review の SKILL.md は呼び方を写す（複製 2）。

## 受入基準

経路（テストケースの表を読む入口）: `check-spec-exit.py`（条件 1 の重複）・`scaffold-estimate.py list`/`check`（`scaffold.py` の `spec_case_rows` → `case_rows`）・`scaffold.py` の書いた後の内訳（同じ `spec_case_rows`）・spec-review の Planner（雛形を書く側）・spec-review の記録（件数を数える側）・scaffold スキル（手順 1a で分ける側）。

| # | 不変条件 | 経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | spec-review の雛形（先頭の列 `テストケース`）の表を、条件 1 の重複の検査と見積もりと書いた後の内訳がそのまま読む | check-spec-exit・scaffold-estimate・scaffold.py の内訳・Planner の指示 | spec-review の SKILL.md の雛形の行と spec-exit.md の雛形が同じ見出し。雛形の表を試料にして `check-spec-exit.py` が番号を数え重複を 1 で落とし、`scaffold-estimate.py list` が数える |
| A2 | 仕様レビューを抜けた仕様（実案件の形: テストケースの節の `| ID |` の表）で、見積もりが「表が無い」（3）で止まらない | scaffold-estimate list/check・check-spec-exit | 試料（`test-scaffold-estimate.py` の「list はテストケースの節の ID の表も読む」・`test-check-spec-exit.py` の「テストケースの節の ID の表は読む」）。陽性対照: base `6affbd0e` の本体では同じ試料で 3（`仕様にテストケースの番号の表が無い`）——著者が走らせて確かめた |
| A3 | テストケースの節の外の `ID`・`No`・`項番` の表（Q&A・NFR の番号を並べた表）は、今までどおり番号に数えない（後退しない） | check-spec-exit・scaffold-estimate | 試料「見出しが ID・No の表は読まない」「テストケースの節の外の ID の表は読まない」「次の見出しで節を引き継がない」「list はテストケースの節の外の ID の表を読まない」と、既存の試料の全部が緑 |
| A4 | 入口・観測点を書き起こす側が置いてよい範囲（入口の名前・項目名・知らせの観測点の扱い・`seed` の口（時計を含む）・画面の初期値を返す入口）と、置けないものが spec-ir.md に書かれ、scaffold の SKILL.md（守ることと手順 1a）から指されている。**書いた事実が正しい**——`setup`・`after` が呼べるのは入口と `seed` だけ・`seed` の値に日時の文字列を書ける・`seed` の名前に `clock` を使える | spec-ir.md・scaffold の SKILL.md | 文面を読む。事実は `scaffold.py` に `{"seed": "clock", "values": {"now": "…"}}` を持つ中間表現を当てて検査が通ること、`after` に入口でも `seed` でもない名前を書くと止まることを走らせて確かめる。指し先は `check-skill-pointers.py` |
| A5 | spec-review の記録の `テストケース` の列の数え方と、`check-spec-exit.py`（`case_rows`）の数え方がそろう | spec-exit.md の「仕様の規模」・spec-review の SKILL.md の記録の手順 | 両方が `scaffold-estimate.py list` の件数（`case_rows` の数）を書けと言い、数え方を変えた回の扱い（`記法の移行`）がある |
| A6 | spec-loop の版が 3 種類で揃い、base より上がっている | カタログ・マニフェスト・スキル本文 | `check-plugin-versions.py`・`check-version-bump.py origin/main` |
| A7 | 歯止めが全部緑 | リポジトリの CI | `check-all.py`（run-serial 越し）と PR 側の CI |

掛け算: 受入基準を Verifier と `/code-review` の両方に、2 パス（1 パス目の指摘対応の差分が 0 行なら 1 パス）。

未証明: 実案件（Issue の 636 件の仕様）そのものに当てること——正本はこのリポジトリに無い。試料は Issue が書いた形（55 の表すべてが `| ID |`）を写したもので、節の見出しが `テストケース` を含むかは Issue に書かれていない（含まなければ A2 は雛形への書き換えで満たす——Issue の「手当て」と同じ）。人間のレビューに回す。
BLOCKED: なし。
生成物: なし（`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけを測る。spec-loop の生成物（`scaffold/`）はこのリポジトリに無い）。
プロパティテスト: なし（`case_rows` の入力の空間は Markdown だが、守る性質は表の見出しと節の見出しの組み合わせで、例の試料で境界（節の内外・見出しの形・コードブロック）を全部名指しできる）
差分テスト: なし（振る舞いを変える周——テストケースの節の `ID` の表を新たに読む。変えない範囲（A3）は既存の試料が旧い振る舞いを固定している）

## 未解決の判断

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1333-scaffold-case-table-and-entry-range`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1333`・起点 `6affbd0e`・base `origin/main` = `6affbd0e2abd8c3df790745010e2b2e68efd9af4`
- 直す線: 既定（出所: cruise の台帳の確かめた線）
- 割り目: 割らない（cruise の周）。手順 4 の割り目は訊かずに続けた。
- 実験: A2 の陽性対照（base と HEAD の本体を一時ディレクトリに写し、同じ試料に `scaffold-estimate.py list` を当てた——base は 3、HEAD は 0 で 2 行を数えた）。交絡: 同じ試料・同じ `python3 -I`・写した `scripts/` だけが違う。
- 1 パス目の関門に渡した成果物: `86b282bb`（1 パス目の指摘対応の起点）。Verifier（sonnet・`dev-loop:dev-loop-verifier`）と `/code-review` に渡す。

## 既知の限界・決着済みの論点

- テストケースの節の `ID` の表を読むか、警告するか（Issue の提案 1 の「どちらか」）——採った: 読む。理由は上の「決めたこと」。
- 知らせ（event）を読み返す観測点の形を中間表現に足すか（提案 3）——採らなかった: 受入基準に回す。理由は上の「決めたこと」。
- 節の見出しは ATX（`#`）だけを読み、下線の見出し（`===`・`---`）は読まない——採った（限界として spec-exit.md と docstring に書いた）。理由: `---` の下線は表の区切りの行・水平線と紛れ、Markdown の仕様と同じ形で読むには前の段落を持つ必要がある。雛形（`テストケース`）で書けば節に依らず読む。
- HTML コメントの中の見出しも読んでしまう——表と同じ既存の限界（「読んでしまうもの」）。採った: 書き足さない（既存の限界の行が表を言い、見出しは同じ読み方）。

### 1 パス目の採否（Verifier 反証 1 件・/code-review 指摘 8 件）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V-R1・CR2（同じもの）`## テストケース` の下の小見出し（`### 正常系`）の `| ID |` の表を読まない（節を直前の見出しだけで決めていた） | 示せる——関門が `scaffold-estimate.py list` で 1 件（F2-1 だけ）・rc=0 を出した。直した後の試料「小見出しの下も節の中」は変異「小見出しで節を抜ける」（旧い振る舞い）で赤（陽性対照） | A2 | 直す——見出しの深さを持ち、同じか浅い見出しまで節を引き継ぐ |
| CR3（と V-R1 の逆向きの穴）見出しに `テストケース` を含むだけで節になり、`## テストケースの前提となるマスタ` の下の `ID` の表（M-001・R-F10）を数える | 示せる——関門が base 1 件・HEAD 3 件を出した。試料「テストケースの語で終わらない見出しは節でない」は変異「節の見出しを部分一致で読む」（旧い振る舞い）で赤 | A3 | 直す——見出しの末尾がテストケースの語（`SECTION_HEADER`。一覧・括弧書きを許す）のときだけ節 |
| CR1 機能の `operation` は 1 つなので、既にある機能に後の状態を読む入口・画面の初期値の入口を「足す」ことはできない。観測のための機能を足すと機能一覧の検査で止まる | 示せる（`scaffold.py` の `operations()` と spec-ir.md の機能の表を関門が読んだ。文面の事実の誤り） | A4（書いた事実が正しい） | 直す——後の状態はほかの機能の `operation` だけを呼び、無ければ `acceptance`。画面の初期値は仕様がその振る舞いを書いた機能の `operation` |
| CR7 時計の `seed` はトレースのケースに書けない（spec-ir.md が無条件に書いていた） | 示せる（spec-ir.md の「前提と後の状態」が `seed` はトレースに書けないと言う） | A4 | 直す——入出力のケースだけと書き、トレースは `acceptance` |
| CR4 spec-review の手順 6 で 3 が出たら直せと書いたが、手順 6 は判定役の後——レビューを通らない直しになる | 示せない（手順の読み方。実行の例は無い） | 無し | 残課題 |
| CR5 3 の原因は見出しだけでなく番号の形（`TC001`・`1`）もある | 示せる（関門が試料で 3 を出した）。ただし案内が狭いだけで、受入基準（雛形どおりの表を読む）は破らない | 無し | 残課題 |
| CR6 雛形の節の文が「テストケースを含む節」と言い、実装（`CASE_HEADER`）より狭い。`番号`・`#` の見出しを読まないと書いていない | 示せる（文面） | 無し（1 行目の直しで節の決まりを `SECTION_HEADER` に書き直し、`番号`・`#` を限界に足した） | 残課題（直しの中で解消） |
| CR8 記録の手順が `list` の 1・2 のときを言わない。`list` は重複を除いた件数で、計画の A5 の「`case_rows` の数」と違う | 示せる（`unique_cases`） | 無し | 残課題 |

- 1 パス目の指摘対応の起点: `86b282bb`。指摘対応のコミットは下の 2 パス目の欄に書く。
