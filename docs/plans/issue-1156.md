# Issue #1156 — spec-loop・screen-spec: 範囲の外に出した「見た目」（デザインの正本・見た目のずれ）を下流で引き受ける先が無い

**不在の周**（`/dev-loop:cruise 1169 --absent` の起動・2026-11-18T06:40Z。前のセッションは 2026-11-17T10:47Z）。利用者には訊かない。親（cruise #1169）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1169`）。利用者の確認（起動時・2026-11-17T10:47:55Z、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`（古い値。後退・未達は推奨で進めない）。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1169.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.8.0（`SKILL.md` 1923 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1169`））。
版の上げ方: `spec-loop` を **minor**（デザインの正本の参照を読み、Issue の本文に載せる——CLAUDE.md の「能力・手順の追加」）。着手時の main は spec-loop 0.109.0 → 0.110.0。
`dev-loop` を **minor**（spec-loop から来た Issue の読み方に、デザインの正本の段落があれば見た目を受入基準に足す手順を足す）。着手時の main は dev-loop 2.8.0 → 2.9.0。
1 パス目の後に main（#1157 が dev-loop を 2.9.0 に上げた）を取り込み（`6ca3ecf`）、dev-loop を **2.10.0** に上げ直した（spec-loop は main が 0.109.0 のままなので 0.110.0 のまま）。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。並行して #1163・#1158 の周が spec-loop を触る。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.8.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: (1) 見た目の正本（Figma のファイル・ノード、トークンのファイル）を指す欄を持ち、scaffold が Issue の `## 参考資料` に載せる。正本そのものは承認の範囲に入れない。
(2) 見た目の確かめは dev-loop 側の関門——参照があれば、dev-loop の verify でスクリーンショットとデザインの比較を受入基準の 1 つとして扱い、手段が無ければ BLOCKED。
(3) 範囲の外として記録した見た目の指摘（#1082 の 3）の行き先を、この参照（デザインの正本の更新）にする。
決めること: 参照を置く場所・見た目の比較を必須の関門にするか参照があるときだけか・デザインの正本を持たない案件で何を正とするか。コメントは無い。本文に受入基準を緩める指示は無い。

## 決めた値（開発者が決めた——仕組みの細部）

- **D1 表の形**: `design/sources.csv`（見出し `対象,参照,メモ`）。`対象` は `全体` か画面の表（重ね合わせた全体の `screens.csv`）の画面ID。`参照` は URL か正本の根からのパス（空・バッククォート・`\`・改行は形の違反）。`メモ` は任意（改行は違反）。
  同じ `対象` と `参照` の組の重複も違反。読めない（UTF-8 でない）・見出しが違う・列の数が違うのも違反。違反は scaffold の 1（何も作らない）。
- **D2 どの機能の本文に載るか**: 画面の表がその機能を挙げる画面（#1099 の「画面の表から引く参考資料」と同じつながり）を持つ機能だけ。載るのは `全体` の行と、その機能を挙げる画面の行（表の行の順）。
  画面の表が無い・どの機能も画面を持たないなら、どの本文にも載らない——そのとき `design/sources.csv` に行があれば、止めずに標準エラーで「本文に載らない」と知らせる（画面を持たない機能に見た目を足さない）。
- **D3 無ければ前と同じバイト**: `design/sources.csv` が無い正本では、契約（`scaffold/`）も本文も #1156 の前と 1 バイトも変わらない。参照は本文にだけ載り、`scaffold/` の契約（写し）にも機能のオブジェクトにも入れない（機能の指紋・v2 以降の変更の判定は変わらない）。
- **D4 dev-loop の側**: 本文の段落の印は `**デザインの正本**`。dev-loop の `spec-gap.md` に「デザインの正本」の節を足す——段落があれば、手順 3 に「この機能の画面の見た目がデザインの正本と合う」を Red テストの表とは別の行として足し、比べる手段が無ければ手順 5 の BLOCKED。比べた時点（参照と日時）を計画ファイルに書く。段落が無ければ見た目は受入基準に足さない。

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **H1（決めること 1）参照を置く場所**: (a) 正本の根の `design/sources.csv`（版の外。推奨）／(b) screen-spec の `settings.csv`（版の中）／(c) 画面の表の列（版の中）／(d) spec-loop の `requirements/` の新しい表（版の中）。
  推した理由: Issue の「正本そのものを承認の範囲に入れない」を保つには、参照も版の外に置くのが筋——版の中に置くと、デザインの担当が参照（Figma のノード）を差し替えるたびに 2 つのサインオフの照合が割れる。
  screen-spec の描き方の差し替え（`screen-spec/renderers/`）・レビュー会の記録（`reviews/`）と同じく版の外。spec-loop は screen-spec に依存しないので、scaffold が読むファイルは spec-loop の決まり（`tree.md`）に置く。
- **H2（決めること 2）見た目の比較を必須にするか**: (a) 参照がその機能に載ったときだけ受入基準にする（推奨）／(b) 画面を持つ機能では常に必須（参照が無ければ BLOCKED）／(c) 受入基準にせず、参考として読むだけ。
  推した理由: (b) はデザインの正本を持たない案件のすべての画面の周を BLOCKED にする。(c) では Issue の問題 2（見た目のずれを捕まえる関門が無い）が残る。
- **H3（決めること 3）デザインの正本を持たない案件**: (a) 見た目を確かめる正は無い——今の決まり（見た目は確かめる対象ではない）のまま、生成したモック・ワイヤーフレームを見た目の正にしない（推奨）／(b) 生成したモックを見た目の正にする／(c) 実装の画面のスクリーンショットを利用者に確かめてもらう工程を足す。
  推した理由: 生成したモックの描き方はワイヤーフレームに近く（#1082）、見た目の正にすると汎用の描き方に実装を合わせることになる。(c) は要求確定に見た目を持ち込まない線（#1082）に反する。

## 変更範囲

触る:

- `plugins/spec-loop/references/tree.md` — ツリーに `design/sources.csv`、新しい節「デザインの正本の参照」（置き場所・列・決める人・載る本文・承認の外・見た目の指摘の行き先）、「UI モック」から指す
- `plugins/spec-loop/references/handoff-issue.md` — 「参考資料」に「デザインの正本」の段落の決まりと文言
- `plugins/spec-loop/references/spec-scope.md` — 「見た目」に、見送った見た目の指摘の行き先（デザインの正本）と、見た目を受入基準にするもう 1 つの道（デザインの正本の参照）
- `plugins/spec-loop/references/spec-ir.md` — 「参考資料」の「見た目を受入基準にしたいなら」にデザインの正本を足す
- `plugins/spec-loop/scripts/scaffold.py` — `design/sources.csv` を読み、検査し、本文の `## 参考資料` に段落を載せる
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 参考資料の項にデザインの正本
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 手順 5 の報告に、見送った見た目の指摘をデザインの正本の担当へ渡すこと
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 参考資料の行と、新しい節「デザインの正本（見た目の確かめ）」
- `scripts/test-scaffold-screens.py` — デザインの正本の試料・変異・写しの突き合わせ（`handoff-issue.md`・dev-loop の `spec-gap.md`）
- `CLAUDE.md` — `scaffold.py` の項
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行（spec-review の `SKILL.md` は、1 パス目の CR1-3 と 2 パス目の CR2-1 で見た目の指摘を担当へ渡す行も足した）
- `plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`spec-gap.md` の行数が変わるので `skill-metrics.py` で書き直す。手で書かない）
- `docs/plans/issue-1156.md` — この計画ファイル

触らない:

- screen-spec（`plugins/screen-spec/`）——参照は画面ID で画面を指すが、読むのは spec-loop の scaffold で、spec-loop は screen-spec に依存しない（H1）。screen-spec の表・モックは見た目を持たないまま
- `review-meeting.py`・`triage.json` の形——見送った見た目の指摘の記録はそのまま。行き先は req-loop の報告で人に渡す（機械で送らない）
- dev-loop の `SKILL.md` の本文（手順 1 が spec-loop の本文で `spec-gap.md` を読ませている。版の 2 行だけ）・`prompts/`・検査のスクリプト
- `check-signoff.py`・`merge-versions.py`——`design/` は版の外なので照合・重ね合わせの範囲に入らない（入れないのが H1 の狙い）
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）・`README.md`・公開ページ——今の要約が偽にならない

依存の追加・更新: なし

仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）

**複製の数**: デザインの正本の決まり（置き場所・列・載る本文）は 2（`tree.md` の節が原本、`scaffold.py` の定数が写し）。本文の段落の文言は 3（`handoff-issue.md` が原本、`scaffold.py` の定数と dev-loop の `spec-gap.md` の印が写し——`test-scaffold-screens.py` が突き合わせる）。
dev-loop が見た目を受入基準に足す手順は 1（`spec-gap.md`）で、`handoff-issue.md` と本文は指すだけ。見た目の指摘の行き先は 1（`spec-scope.md` の「見た目」）で、`tree.md` と req-loop は指す。
分けない理由: 決まりの原本は `references/`、スクリプトは写しを持ち、テストが突き合わせる。スキルは原本を指す。

## デプロイ経路

プラグイン（`marketplace.json` のカタログと、`link-skills.sh` を使う利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口（デザインの正本の参照を書く・読む・渡す場所）: デザインの担当が `design/sources.csv` を書く・scaffold の書く生成／`--dry-run`／`--check`／`--red-check`（`load`）・本文の `## 参考資料`・dev-loop 手順 1 → `spec-gap.md`（手順 3・5）・
req-loop 手順 5（見送った見た目の指摘）・spec-review の判定役の見た目の指摘（`spec-scope.md`）・照合（`check-signoff.py`）・重ね合わせ（`merge-versions.py`）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | デザインの正本の参照の決まり（置き場所 `design/sources.csv`・版の外で承認の範囲に入らない・列・`対象` の値・載る本文・無ければ何も変わらない・見た目の指摘の行き先）が `tree.md` の 1 箇所にあり、`handoff-issue.md`・`spec-scope.md`・`spec-ir.md`・scaffold と req-loop のスキルがそこを指す | 決まりを読む人・スキル | `references/` の節 | 読んで確かめる＋`test-scaffold-screens.py` の写しの突き合わせ |
| A2 | 画面を持つ機能の本文の `## 参考資料` に、`全体` の行とその機能を挙げる画面の行が、印 `**デザインの正本**` で始まる段落の下に表の順で載る。ほかの画面の行・画面を持たない機能には載らない | scaffold の書く生成 | `references()` | 試料（`test-scaffold-screens.py`） |
| A3 | `design/sources.csv` が決まりに反する（見出し・列の数・`対象` が `全体` でも画面の表の画面ID でもない（画面の表が無いときも）・`参照` が空・バッククォート・`\`・改行・`メモ` の改行・組の重複・UTF-8 でない）なら 1 で何も作らない | scaffold（書く生成・`--dry-run`） | 検査の関数 | 試料と変異 |
| A4 | `design/sources.csv` が無い正本では、契約と本文が前と同じバイト。在っても `scaffold/` の契約・機能の指紋・v2 以降の変更の判定は変わらない（本文にだけ載る） | scaffold | 本文だけに足す | 試料（無い正本と在る正本で `scaffold/` が同じ。前からの試料が全部通る） |
| A5 | 行があるのにどの本文にも載らない（画面の表が無い・どの機能も画面を持たない）なら、止めずに知らせる | scaffold | 知らせる行 | 試料 |
| A6 | dev-loop の `spec-gap.md` が、段落があれば見た目の受入基準を Red テストの表とは別に足し、比べる手段が無ければ BLOCKED、食い違いは仕様の穴、段落が無ければ足さないと書き、本文の印と同じ文字列を持つ | dev-loop 手順 1 → 3・5 | `spec-gap.md` | 読んで確かめる＋突き合わせ（印） |
| A7 | 見送った見た目の指摘の行き先がデザインの正本（参照があればその担当へ渡す。無ければ記録だけ）と `spec-scope.md` が書き、req-loop の手順 5 の報告がそれを渡す | req-loop 手順 5・spec-review | `spec-scope.md`・req-loop | 読んで確かめる |
| A8 | `design/` は照合の範囲に入らない（`design/sources.csv` だけが違う 2 つのタグで照合が一致と言う） | proposal の照合 | 版の外 | 一時の git リポジトリで照合して 0（陽性対照: 版の中の `screens.csv` が違えば 1——既存の試料） |
| A9 | 版を 3 種類で揃えて上げ（spec-loop・dev-loop）、`check-all.py` が緑 | CI | 版の行 | `check-all.py`・`check-plugin-versions.py` |
| A10 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: A6 の dev-loop が実際の spec-loop の本文で見た目の受入基準を足し、スクリーンショットとデザインを比べること（スキルを実際の製品の周で走らせて観測していない——人間のレビューに回す）。
A7 の req-loop が実際のレビュー会の後に見送った見た目の指摘を渡すこと（同じ）。

**生成物**: 1 件——設計ドキュメント §8.2 の生成ブロック（`docs/plugins/dev-loop-design.md`。`spec-gap.md` の行数と `（必須）` の数が入る）。`skill-metrics.py` で書き直し、鮮度は `skill-metrics.py --check`（`check-all.py` と CI が回す）で見る（受入基準 A9 に含める）。
`scaffold/` の契約と Issue の本文はこのリポジトリの生成物ではない（試料の一時ディレクトリに作るだけ）。

## 未解決・確認待ち

- H1〜H3 の確認の Issue（利用者が戻ってから確かめる）: H1 #1244・H2 #1245・H3 #1246（どれも先頭 `<!-- cruise-decision: #1169 -->`・ラベル `要確認`。2026-11-18T07:55Z ごろに立てた）。

## 手順 8（起票）

- この周の起票: 3 件（仕様の穴 H1〜H3 の確認の Issue #1244・#1245・#1246。起票の承認は不在のため訊いていない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1156-design-source`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1156`・起点 `53517d5`・base の参照 `origin/main`（解決した SHA `53517d593b60a75123648e6f26b0d77dd669b1d1`。main の取り込み `6ca3ecf` の後に当て直して `27327a15d327f38034ad84d987313187d98133d3`）
- 割り目（手順 4）: 割らない（cruise の周）
- 1 パス目の起点（先に当てた Verifier に渡した時点の HEAD）: `9279244bcfb846c4965699b818eccabe752cce91`
- 手元の歯止め（1 パス目の前）: `scripts/test-scaffold-screens.py`（run-serial 越し）緑（試料 17・変異 27）。`check-all.py`（run-serial 越し、`9279244` の作業ツリー）は 56/93 本を回して失敗 3——`check-plan-counts.py`（件数の行がまだ無い）・`check-plan-scope.py`（下の V1-1）・`check-version-bump.py`（main が #1157 で dev-loop を 2.9.0 に上げていた——取り込みで上げ直した）
- Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet。委譲文 194 行を全文読んだと報告）: 反証 1 件（V1-1）。テストの変異 27 件は全部赤、独自の変異は当てていない。git status は前後とも空で同じ。報告は SubagentHandback で届かず、`SendMessage` で催促したあと子の transcript から読んだ
- `/code-review` 1 パス目（high。起動の引数で受け渡しの文面 163 行のファイルを指した）: 指摘 8 件（直す 3・残課題 5）。コードを読んだだけで、テストも変異も走らせていない（本人の申告）。git status は前後とも空
- 手順 4 への差し戻し: あり（直すの 4 行——V1-1 は計画ファイルだけの直し）
- 割り目（手順 6 の 2 パス目の前）: 割らない（cruise の周）。残っているもの: 手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方
- 1 パス目の指摘対応: `2f79b005428da014507341c7f89542284b2ecea8`（`git diff 9279244 2f79b00 -- ':(top)' ':(top,exclude)docs/plans/issue-1156.md'` は 5 ファイル——2 パス目を回す）
- PR: #1243（https://github.com/hdknr/claude-code-setup/pull/1243）
- main の取り込み: `6ca3ecf`（#1157 を取り込み、生成ブロックは main 側を取ってから `skill-metrics.py` で書き直し、dev-loop を 2.10.0 に上げ直した）。**周の base を当て直した**: `git merge-base origin/main HEAD` = `27327a15d327f38034ad84d987313187d98133d3`（2 パス目と狭いパスの関門にはこれを渡す）
- Verifier 2 パス目（sonnet。委譲文 212 行を全文読んだと報告——213 行と表示、末尾の改行の数え方）: 反証 0 件。`test-scaffold-screens.py` 緑（試料 18・変異 28）・軽い検査 10 本が 0。git status は前後とも空で同じ。報告は SubagentHandback で届かず、子の transcript から読んだ
- `/code-review` 2 パス目（high。180 行の受け渡しの文面を指した）: 指摘 10 件（直す 4・計画ファイルだけの直し 2・残課題 4）。`test-scaffold-screens.py` は順番待ちが長く走らせず、**止めた——その際に残った run-serial のプロセスを kill したと申告**。同じ時刻にこちらが背景で起こした `test-scaffold-screens.py`（run-serial 越し、`tss-2.txt`）が 143 で終わっていた——関門が周の子の検査を止めた可能性が高い（その結果は使っていない。Verifier 2 パス目の緑と、下の狭いパスの前の走らせ直しを使う）。git status は前後とも空
- 狭いパスの起点（2 パス目の指摘対応を始める直前の HEAD）: `075dc4ee21c9ece743a5aaf84d30f092ab2a5f95`
- 著者の逸脱の記録: 生成ブロックの鮮度を base と比べるために worktree で `git stash`／`git stash pop` を素で使った（CLAUDE.md が禁じる形——stash は全 worktree で共有）。直後に `git status --porcelain` で自分の変更が全部戻り、`git stash list` が空であることを確かめた（他人の stash を取り出していない）

## 既知の限界・決着済みの論点

（関門に毎パス渡す。決着の理由が誤っていると判断したなら、それは新しい反証である）

- 上の H1〜H3 と D1〜D4。
- `design/sources.csv` は版の外で、版ごとの参照は持たない（描き方の差し替え `screen-spec/renderers/` と同じ）——読むのは本文を作るモード（書く生成・`--dry-run`）で作業中の版の全体を見るときだけで、今の作業ツリーのファイルを読む。`--upto` で前の版の時点を見るとき・`--check`・`--red-check` は読まない（2 パス目の CR2-3 で、前の文「`--upto` でも読む」が実装と逆だったのを直した）。本文は参照の中身（Figma のファイル）の sha256 を持たない——中身は周の途中でも変わりうるので、dev-loop は比べた時点を計画ファイルに書く。
- 参照（URL・パス）が実在するか・開けるかは見ない（ネットワークに出ない。パスもファイルの在ることを求めない——トークンのファイルが別のリポジトリにあることがある）。
- 周の途中の課題の振り分け（found-lines。線 `周の途中の課題 = 外に出す`）は下に足す。

### 1 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1-1（Verifier）: 計画ファイルの `触る:` の 2 行が 1 行に 2 パスを書いていて、`check-plan-scope.py` が dev-loop の 3 ファイルを範囲の外と言う | 示せる（`check-plan-scope.py 53517d5` が非 0。`check-all.py` でも落ちた） | A9（`check-all.py` が緑） | 直す——1 行 1 パスに分けた（計画ファイルだけ） |
| CR1-1: 決まりに反する `design/sources.csv` で `--check`・`--red-check` も 1 になる——本文を作らないモードで、版の外のファイルが契約の CI を止める | 示せる（直す前の形に戻す変異「--check・--red-check でも読む」で、書いた後に `S-999` の行を置いた `--check` が 1——試料が赤。直した後は 0） | A4（参照は契約に効かない） | 直す——読むのを本文を作るモード（書く生成・`--dry-run`）に移し（`check_design`）、試料と変異を足した |
| CR1-2: v2 で画面を持たない機能だけが変わると、どの本文にも参照が載らないのに知らせない | 示せる（理屈。試料は作っていない） | 無し（A5 の括弧が知らせる場面を「画面の表が無い・どの機能も画面を持たない」と決めている。変わっていない機能の本文は前の版の Issue にある） | 残課題 |
| CR1-3: spec-review の判定役の見た目の指摘は、範囲の外に振るだけでデザインの担当へ渡らず、原則の文が「仕様とケースに書く」だけのまま | 示せる（`spec-scope.md` を読んだ） | A7（経路「spec-review」） | 直す——`spec-scope.md` の判定役の項と行き先の項、spec-review の `SKILL.md` に渡すことを書いた |
| CR1-4: 参照は本文を作った時点の写しで、後から `design/sources.csv` を足す・差し替えても登録済みの Issue に届かない | 示せる（理屈） | 無し（D3・`handoff-issue.md` が「参照を変えても Issue は作り直されない」と決めている） | 残課題（dev-loop が周の時点の `design/sources.csv` を読む案は別の周） |
| CR1-5: `メモ` に `- 仮回答: ` や `<!--` を書くと、本文が仮回答に依存すると数えられる・GitHub で本文の後ろが隠れる | 示せる（理屈） | 無し | 残課題（まれな形） |
| CR1-6: BOM を許す決まりと空の行を飛ばすことに試料が無い（`utf-8-sig` を `utf-8` にしても緑） | 示せる（試料の穴） | 無し（本体は正しい） | 残課題 |
| CR1-7: A4 の「v2 以降の変更の判定は変わらない」に試料が無い | 示せる（v2 の試料が無い） | A4（証明が無い） | 直す——試料「v2 の変更の判定は変わらない」（参照の有無で v2 の本文の数・契約・段落の外の本文が同じ）を足した |
| CR1-8: `screen_ids` が `linked_screens` と別に画面の表を読む（列の欠けで食い違う） | 示せない（列が欠ければ画面の関門が先に止める） | 無し | 残課題 |

### 2 パス目の採否の表

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2（Verifier 2 パス目）: 反証 0 件 | — | — | — |
| CR2-1: spec-review の手順 7（止まって報告する一覧）に、見た目の指摘をデザインの担当へ渡す項が無い（CR1-3 の直しは手順 2 の Planner の項だけ） | 示せる（`spec-review/SKILL.md` の手順 7 を読んだ） | A7（経路「spec-review」） | 直す——手順 7 の報告の一覧に足した |
| CR2-2: `tree.md` の「デザインの正本の参照」の行き先の項が、レビュー会の見送りしか挙げない（spec-review の判定役の指摘が無い） | 示せる（読んだ） | A1（決まりが `tree.md` にあり、ほかが指す） | 直す——spec-review の判定役の指摘も挙げ、決まりの本体は `spec-scope.md` の「見た目」と書いた |
| CR2-3: 計画ファイルの既知の限界が「`--upto` でも今のファイルを読む」と書くが、実装は読まない | 示せる（計画と `scaffold.py` を読んだ） | 無し（関門に渡す材料の誤り。成果物ではない） | 直す（計画ファイルだけ） |
| CR2-4: 本文を作らないモードで読まないことを `--check` でしか試していない（`--red-check` の後退が素通りする） | 示せる（理屈。条件を `if not args.check:` にする変異を当てる試料が無い） | A4（`--red-check` で契約に効かないことの証明が無い） | 直す——試料に `--red-check` を足し（参照の有無で終了コードと出力が同じ）、変異「--red-check では読む」を足した |
| CR2-5: 試料「v2 の変更の判定は変わらない」の docstring が「差し替えても」と言うが差し替えは試していない。この試料を赤にする変異も無い | 示せる（試料と変異の一覧を読んだ） | A4（証明が主張より狭い） | 直す——docstring を「足しても」に狭め、変異「参照を機能のオブジェクトに入れる」を足した |
| CR2-6: 空の `design/sources.csv`（`touch` しただけ）が見出しの違反で 1 になり、書く生成で前の本文を消す | 示せる（理屈） | 無し（A3 の「見出しが違う」どおり。空のファイルを違反にするかは決まりが無い） | 残課題 |
| CR2-7: どの本文にも載らない旨の知らせが、後の関門（仕様レビューの記録）で止まるときにも出る | 示せる（理屈） | 無し | 残課題 |
| CR2-8: `DESIGN_MARK` が本体のコードで使われず、`REFS_DESIGN` が印とパスを直書きする | 示せない（振る舞いは同じ。テストが突き合わせる） | 無し | 残課題 |
| CR2-9: `spec-scope.md` の項が「今の決まりのまま——仕様とケースに書く」で始まり、次の文で 2 つ目の道を足す（読み手が最初の文で止まる） | 示せる（読んだ） | 無し（A7 は行き先。道は 2 つとも同じ項にある） | 残課題 |
| CR2-10: 計画ファイルの変更範囲が spec-review の `SKILL.md` を「版の 2 行」とだけ書く | 示せる（読んだ） | 無し（関門に渡す材料の誤り） | 直す（計画ファイルだけ） |
