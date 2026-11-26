# Issue #1571 — screen-spec: 外部の profile の画面の層で、既定の値が同じ表・列の語彙に無ければ止める

利用者が居る周（`/dev-loop:dev-loop 1571`・2026-11-26）。読み込んだ dev-loop は 2.25.1。

直す線: `既定`（出所: 手順 3 の回答・2026-11-26）。
版の上げ方: `screen-spec` を **minor**（0.11.0 → 0.12.0。0.x なので、今まで通っていた食い違った profile が 4 で止まる変更も minor）。

Issue 本文（外部入力。作者は利用者本人）から読んだ要件: 外部の profile の画面の層で、種類 `既定` の行の `値` が同じ `表`・`列` の `語彙` に無ければ、
「読めないとき」（4）として検査の前に止める。語彙を 1 つも持たない列の既定は見ない。core・組み込みの profile に値の決まった列に既定を置いた場合の扱いも決める。

## 変更範囲

触る:

- `plugins/screen-spec/scripts/check-screens.py` — `load_external` で既定の値を語彙と core の決まった値に照らす。守る／守らないは docstring
- `plugins/screen-spec/references/profiles.md` — 行の種類 `既定` の説明と「読めないとき」に足す（決まりの原本）
- `scripts/test-check-screens.py` — 試料・変異
- `scripts/test-write-screens.py` — `init` が食い違った画面の層で書かずに 4 で止まる試料（受入基準 7）
- `CLAUDE.md` — プロジェクト構成の `check-screens.py` の項に 1 句
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/screen-spec/skills/*/SKILL.md` — 版の 2 行（2 本）
- `docs/plans/issue-1571.md` — この計画ファイル

触らない:

- `plugins/screen-spec/scripts/write-screens.py`——`init` は `load_external` を読み込むので、同じ止め方を受け継ぐ（コードは変えない）
- `plugins/spec-loop/`（`external-profile.py` は読み込むだけ）
- plugin.json・marketplace.json の description

依存の追加・更新: なし

## 設計の判断（手順 3 の回答・2026-11-26）

- 既定の値は、その列の**外部の profile の語彙**（`screens.csv` の同じ列の `語彙` の行。在れば）と、**core の決まった値**（`screens.csv` の `種別`・`ステータス`）の**両方**に在ること。無ければ 4。
- `種別` の列の既定は、その行の `種別` と同じ値でなければ 4（画面の `種別` はその種別そのものなので、違う値の既定はどの画面でも違反になる）。
- 組み込みの profile（`web-spa`）の `screens.csv` の列は `パス` だけで、決まった値を持たない。`パス` の形（`/` で始まる）に既定が合うかは見ない（守らないもの）。
- 語彙の行と既定の行の順に依らない（全部を読んでから照らす）。
- 複製の数: 決まりの原本（`profiles.md`）1・本体の docstring 1・CLAUDE.md の 1 句——原本以外は指すだけ。分けない（1 つの規則）。

## verify の受入基準

不変条件 × 経路（入口は `check-screens.py` と、`load_external` を読み込む `write-screens.py init`・`hint`）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| 1 | 既定の値が同じ列の外部の語彙に無ければ 4 で止まる | `check-screens.py`（既定が語彙の外 `L-080` / 語彙の行を差し替え） | `load_external` で Stop | 試料（Issue の再現 2 形） |
| 2 | 語彙を持たない列の既定は語彙で止めない | `check-screens.py`（語彙の無い足した列に既定） | 語彙が無ければ照らさない | 試料（陰性対照） |
| 3 | 既定の値が core の決まった値（`ステータス`・`種別`）に無ければ 4 | `check-screens.py` | Stop | 試料 |
| 4 | `種別` の列の既定がその行の種別と違えば 4、同じなら通る | `check-screens.py` | Stop | 試料（陽性・陰性） |
| 5 | 語彙の行が既定の行より後ろにあっても判定が同じ | `check-screens.py` | 全行を読んでから照らす | 試料 |
| 6 | 既存の正しい profile（`ext-good` ほか）は今までどおり 0 | `check-screens.py` | — | 既存の試料 |
| 7 | `init` が食い違った profile で書く前に 4 で止まる（書かない） | `write-screens.py init --external` | `load_external` を共有 | `test-write-screens.py` の試料 `explicit-external-default-outside-vocab`（書いたファイル 0） |
| 8 | 止める行の理由に行の ID・列・種別・値・語彙を名指す | 出力 | メッセージ | 試料の期待文字列 |
| 9 | 決まりの原本（`profiles.md`）と docstring が新しい止め方を書き、「守らないもの」から「既定の値が語彙の中にあるか」を外す | 文書 | — | 目視・`check-all.py` |
| 10 | 新しい分岐を外すと試料が赤になる（変異） | テスト | `MUTATIONS` | `test-check-screens.py` |

- 未証明: なし。BLOCKED: なし。
- 生成物: 該当判定——screen-spec の検査には生成物が無い。`SKILL.md` は触るが版の 2 行だけで、`skill-metrics.py` の対象は dev-loop の `SKILL.md` だけ（`--check` を回して確かめる）。図は触らない。→ 生成物なし（`skill-metrics.py --check` は回す）。
- プロパティテスト: なし（入力は profile の行の小さな組み合わせで、境界は語彙の有無・決まった値の有無・種別の一致の 3 つ。例で尽くせる）。
- 差分テスト: なし（振る舞いを変える周）。
- 必須要件の掛け算: 受入基準を Verifier・/code-review の両方 × 1・2 パス目に渡す（2 パス目が該当なしなら初回の 2 つ）。

## 未解決の判断・確認待ち

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1571-default-in-vocab`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1571`・起点 `366a3c7e`・base 参照 `origin/main` → `366a3c7eca1c629a04b5f4dd9742f037dbf7bf39`
- 実装: `16af6c11`（check-all 緑）。手順 5 から再開できる（この worktree で `/clear` → `/dev-loop:dev-loop 1571`）
- 1 パス目の指摘対応の起点（1 パス目の関門に渡した HEAD）: `16af6c11`
- 割り目（手順 4）: 「ここで割る」を選んだ（2026-11-26）
- 関門: 1 パス目を通した（2026-11-26・HEAD `a90a7eb4`。`16af6c11` からの差は計画ファイルだけ）——**Verifier 反証 1 件・/code-review 指摘 5 件**（採否は下の表。直す 3・残課題 3）
  - Verifier 1 パス目（`dev-loop:dev-loop-verifier`・sonnet）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1571/d1c39207-5c62-42b2-b16a-0ef081d94472/scratchpad/gate-1571-verifier-1-20261126T074931Z.md`
  - /code-review 1 パス目: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1571/d1c39207-5c62-42b2-b16a-0ef081d94472/scratchpad/gate-1571-code-review-1-20261126T074931Z.md`
  - **上の 2 体は欠票**（どちらも API の 401——OAuth の期限切れで、報告のファイルを書かずに終わった）。利用者が `/login` した後に新しいパスで起こし直した:
    - Verifier 1 パス目（再）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1571/d1c39207-5c62-42b2-b16a-0ef081d94472/scratchpad/gate-1571-verifier-1-20261126T075541Z.md`
    - /code-review 1 パス目（再）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1571/d1c39207-5c62-42b2-b16a-0ef081d94472/scratchpad/gate-1571-code-review-1-20261126T075541Z.md`
  - Verifier（再）の報告はファイルに書けず（ヒアドキュメントがガードに拒まれた）、返事（SubagentHandback）で届いた。テンプレート 260 行を読んだと報告（`wc -l` と一致）。`git status --porcelain` は前後同じ
  - /code-review（再）の報告はファイルに終わりの印つき。`git status --porcelain` は前後同じ
- 1 パス目の指摘対応: `2c625402`（`test-check-screens.py` に試料 4・変異 2。`test-check-screens.py` 緑——試料 217・変異 177。新しい 2 変異は、
  直す前の試料では殺せず（両報告の実測）、足した試料でだけ殺せ、影響しない試料では期待どおりに振る舞う（陽性対照を著者が当てた——変異が落ちて殺したことにはなっていない））。
  起点 `16af6c11` からの成果物の差分は 0 行でない → **2 パス目を回す**（手順 5 の当て直しと /code-review 2 パス目の両方が残る）
- 1 パス目の指摘対応の後に check-all 緑（21 本を回し 85 本はキャッシュ・失敗 0）
- 割り目（手順 6・2 パス目の前）: `AskUserQuestion` に 300 秒応答なし → 「このまま続ける」で進めた（2026-11-26）
- 2 パス目を通した（HEAD `a2d44da5`。成果物は `2c625402`）——**Verifier 反証 0 件・/code-review 指摘 3 件**（採否は下の表。直す 0・残課題 3）:
  - Verifier 2 パス目（当て直し）: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1571/d1c39207-5c62-42b2-b16a-0ef081d94472/scratchpad/gate-1571-verifier-2-20261126T081338Z.md`
  - /code-review 2 パス目: 報告 `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup--claude-worktrees-issue-1571/d1c39207-5c62-42b2-b16a-0ef081d94472/scratchpad/gate-1571-code-review-2-20261126T081338Z.md`
  - Verifier 2 パス目は返事（SubagentHandback）で届き、ファイルは書かなかった。`git status --porcelain` は前後同じ。独立の変異は当てていない（狭いパスでないので求めていない）
  - /code-review 2 パス目はファイルに終わりの印つき。`git status --porcelain` は前後同じ。指摘対応で増えた 2 変異の陽性対照を独立に当て、主張どおり（Traceback なし）
- 2 パス目で直した行: 0 件 → **狭いパス: 該当なし**
- 交絡: 実験なし（変異の陽性対照は上）

```dev-loop-gates
周の base: 366a3c7eca1c629a04b5f4dd9742f037dbf7bf39
関門: Verifier 1 a90a7eb4 反証=1
関門: /code-review 1 a90a7eb4 指摘=5
関門: Verifier 2 a2d44da5 反証=0
関門: /code-review 2 a2d44da5 指摘=3
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
受入基準: 8 満たす
受入基準: 9 満たす
受入基準: 10 満たす
マージの反映: ドキュメントとプラグインの配布
```

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `パス` の形に既定が合うか | 見ない（採らなかった） | 形の規則は語彙ではない。Issue の範囲は「語彙のある列」。**2 パス目の /code-review が理由の食い違いを指摘（下の CR2-3）——決着の理由は取り直しが要り、残課題** |
| 外部の語彙が core の決まった値の外の値を持つとき | 見ない | 既定の食い違いと違い、全部の値が違反になる形ではない（語彙の中の決まった値を書けば通る）。**2 パス目の /code-review が、語彙と決まった値の共通部分が空なら偽と実測した（下の CR2-1）——理由は誤り。残課題** |

### 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V1: 語彙と決まった値が同じ列に在るとき、決まった値の照合を語彙の無い列だけにする変異（`vocab is None and`）が全試料で生き残る | 示せる——Verifier が 213 試料に当てて殺す試料 0（`mutant killed by: []`）、陽性対照で振る舞いは変わる | 3・10 | 直す（`2c625402`。試料 `ext-default-status-vocab-outside-fixed`・変異を足した） |
| CR1: 語彙が既定より後ろの試料が通る方向だけで、既定を読んだ時点の語彙で照らす実装でも緑 | 示せる——/code-review が順に依存する変異を当てて既存の試料 0/0、足した試料で 4/1 | 5・10 | 直す（`2c625402`。試料 `ext-vocab-after-default-outside`・変異を足した） |
| CR2: docstring のコメントと `profiles.md` の止める理由「どの値を書いても違反」は言い過ぎ（Q&A の根拠があれば通る・足した列は空でよい） | 示せる（/code-review の読みと check_external の根拠の扱い） | 無し（9 は止め方を書くことで、理由の文言ではない） | 残課題 |
| CR3: `base_initial` 経由の `hint`・引数なしの `init` に試料が無く、`hint` の案内（明示して渡す）が誤った向きを指す | 1 パス目の時点では示せない（読んだ推論）。**2 パス目の /code-review が走らせて示した**（CR2-2） | 無し | 残課題 |
| CR4: `profiles.md` の「その列に書ける値でなければならない」が一般の規則に読め、`親画面`・`画面ID` などを照らさないことが読めない | 示せる（`親画面` の既定を置いても 4 にならない） | 無し | 残課題 |
| CR5: 試料が Issue の再現の値（L-001〜L-008・L-080・L-009）でなく合成の値 | 示せる（試料に L-080 が無い。計画の表 # 1 は L-080 の経路を挙げる。利用者の CLAUDE.md の「正確な ID を使う」） | 1（証明の「Issue の再現」） | 直す（`2c625402`。試料 `ext-issue-default-L080`・`ext-issue-vocab-L009`） |

### 2 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1（important）: `種別`・`ステータス` の外部の語彙と決まった値の共通部分が空だと、必須の列のどの値も違反になる（Q&A の根拠でも通らない）のに、検査の前に止まらない。docstring の「守らないもの」の理由と計画の決着 2 行目は偽 | 示せる——語彙 `完了` だけの profile で、表の値が `記入中` でも `完了` でも rc=1（/code-review が外で実測） | 無し（受入基準は既定の値の照合。語彙そのものの照合は表に無い） | 残課題（決着の理由の取り直しと、止めるかの判断を人間に渡す） |
| CR2-2: `hint` の案内が、この周の止まり方に対しては行き止まり（`--external` を明示しても 4）を指す。1 パス目の採否の「示せない」は偽 | 示せる——hint rc=0 の文言・引数なしの init rc=4・明示の init rc=4（/code-review が外で実測） | 無し（7 は明示の `init --external` が書く前に止まること） | 残課題 |
| CR2-3: `パス` の形を照らさない理由「形の規則は語彙ではない」は、決まった値（語彙でない）を照らすこの周と食い違う | 示せる（`パス` の既定 `orders/new` で、既定どおりは形の違反、違えば Q&A が要る——/code-review の読み） | 無し | 残課題 |

## 経験の還元（手順 8）

- この周の起票: 2 件（#1581 語彙と決まった値の共通部分が空・#1582 hint の案内の行き止まり。どちらも 2 パス目の /code-review の残課題で、利用者がマージの前に承認・2026-11-26）
- 外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い。`external-reviews.py` が 3）
- 効いた行: V-05（V1。変異を外で当てて、決まった値の照合の変異が全試料で生き残ると示した）
- 効いた行: V-06（V1。陽性対照で変異が振る舞いを変えることを示してから穴と報告した）
- 効いた行: R-05（CR1。既存の試料が緑のとき、順に依存する変異で旧い挙動の再現を示した）
- 効いた行: R-02（CR2。止める理由の文言を check_external の根拠の扱いと照らした）
- 効いた行: なし（CR3。受入基準 # 7 の経路の数え直しから）
- 効いた行: R-02（CR4。規則の文と照らす列の実装を照らした）
- 効いた行: なし（CR5。利用者の CLAUDE.md の ID の規約から）
- 効いた行: R-02（CR2-1。決着の理由を実測で偽と示した）
- 効いた行: R-04（CR2-2。採否の「示せない」を走らせて偽と示した）
- 効いた行: R-02（CR2-3。決着の理由と周の実装の食い違い）
- 焼き戻す学び: OAuth の期限切れで関門の体 2 体が欠票になった——`references/gate-reports.md` の欠票の起こし直しで回収できた（新しい学びは無い。既存のメモリ「OAuth はログインから 8 時間で一斉に 401」と同じ形）
