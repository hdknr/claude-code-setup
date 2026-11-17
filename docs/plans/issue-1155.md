# Issue #1155 — spec-loop spec-review: 内部の Q&A 表（qa-dev.csv）への振り分けを、書き手と別のティアの判定役に確かめさせる

**不在の周**（`/dev-loop:cruise 1169 --absent` の起動・2026-11-17T10:47Z）。利用者には訊かない。親（cruise #1169）から委譲文で受けた子。
確かめた線（出所: cruise の確かめた線（台帳 `issue-1169`）。利用者の確認（起動時・2026-11-17T10:47:55Z、配布を見せて確かめた））:
`直す線 = 既定`・`仕様の穴 = 推奨で決めて起票`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 外に出す`・`マージ前の判断 = 推奨で決めて起票`（古い値。後退・未達は推奨で進めない）。実機確認の線は無い。
台帳（`.claude/plans/cruise-issue-1169.json`）は書かない（親だけ）。手順 7 のマージはしない（PR・CI の確認まで。手順 8 は計画ファイルに書くまで）。
読み込んだ dev-loop は 2.7.0（`SKILL.md` 1920 行を読んだ）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-1169`））。
版の上げ方: `spec-loop` を **minor**（判定役の観点と、抜ける条件 5 の機械の数え直しを足す——CLAUDE.md の「能力・手順の追加」。0.x なので壊れる変更も minor）。着手時の main は spec-loop 0.103.0 → 0.104.0。
マージの直前に main が進んでいたら親の依頼で取り込み、main の先端の版から minor で上げ直す（cruise の `references/parallel.md` の「版とマージの順」）。
重い検査は `/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/2.7.0/skills/cruise/scripts/run-serial.py` 越しに走らせ、背景なら出力ファイルの終わりの印を前面で待つ。
割り目: 割らない（cruise の周）。

Issue 本文（外部入力）から読んだ要件: 内部の Q&A 表（`D-` の行）に回した判断を、書き手（Planner）と別のティアの判定役に「どの選択肢を選んでも利用者に見える結果が変わらないか」で確かめさせる（案 1。候補は Domain Checker——案のとおり Domain Checker にする）。
「変わる」とされた行は共有の表へ移す（案 2。番号の付け替えと指し先の直し）。抜ける条件に足すかを決め、`check-review-record.py` で数えられる形にする（案 3）。
本文とコメントに受入基準を緩める指示は無い（コメントは無い）。

## 決めた値

### 仕様の穴（推奨で決めた。`仕様の穴 = 推奨で決めて起票`）

- **H1（決めること 1）確かめる範囲**: (a) 作業中の版で足した・変えた `D-` の行だけ（`diff-versions.py` の `Q&A（内部）` の `追加`・`変更`。v1 は全部が追加）（推奨）／(b) 重ねた全体の `D-` の行すべてを毎回。
  推した理由: spec-review の差分モード（レビューの対象は作業中の版の差分）と同じ線になる。前の版の行は、その版の spec-review を抜けるときに確かめている（この周より後の版から）。
  (b) は版を重ねるたびに判定役に渡す行が増え続け、前の版でサインオフを通った判断を毎回確かめ直す。
- **H2（決めること 2）確かめた記録の置き場所**: (a) 指摘の表（`spec-review/v<n>-findings.csv`）に、確かめた `D-` の行ごとに 1 行（`指摘` に印 `（内部の行: D-S-003）`）（推奨）／(b) `qa-dev.csv` に列を足す。
  推した理由: 内部の表の列は共有の表と同じ（`qa-csv.md`）で、`check-qa-csv.py`・重ね合わせ・版の差分・資料の生成・MkDocs のフックが同じ列を読む。(b) は前からの正本の `qa-dev.csv` を「見出しが違う」で落とし、移行が要る。
  (a) は列を変えず、指摘の表は既に回ごとの判定役の記録で、`check-review-record.py` が読んでいる。
- **H3（案 3）抜ける条件に足すか**: (a) 足す——条件 5（判定役の指摘が 1 件残らず振り分け済み）に含め、`check-review-record.py internal` で数える（推奨）／(b) 足さない（判定役に渡すだけ）。
  推した理由: (b) では、書き手が判定役に `D-` の行を渡し忘れても、判定役が行を見落としても、黙って抜けられる——Issue が塞ごうとしている「書き手の自己判定」が残る。
  新しい番号の条件（6）にしないのは、確かめることが振り分けの確かめ（条件 5）の続きで、記録の表の列（`条件2〜4`）と上限の数え方を変えずに済むから。

決めた値は受入基準を足さない（手順 3 の受入基準は下のとおり固定）。

## 変更範囲

触る:

- `plugins/spec-loop/agents/domain-checker.md` — 内部の表に置いた判断を確かめる観点と、報告の印
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 手順 3 で Domain Checker に `D-` の行を渡す・手順 4 で振り分けと層を移す・手順 5 の狭いパス・手順 6 で `internal` を当てる
- `plugins/spec-loop/references/spec-exit.md` — 条件 5・数え直しの節・指摘の表の印
- `plugins/spec-loop/references/spec-scope.md` — 内部の表に記録する区分が判定役に確かめられること
- `plugins/spec-loop/scripts/check-review-record.py` — `internal` の数え直しと、`conditions` が確かめの行で 2 回目と読まないこと
- `scripts/test-check-review-record.py` — 試料・変異・references との突き合わせ
- `CLAUDE.md` — `check-review-record.py` の項
- `docs/plugins/index.md` — 公開ページの Domain Checker の行（何をする役か・条件 5）
- `plugins/spec-loop/README.md` — `check-review-record.py` の行
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `docs/plans/issue-1155.md` — この計画ファイル

触らない:

- `qa-dev.csv` の列（H2）・`check-qa-csv.py`・`merge-versions.py`・`diff-versions.py`・`check-findings-csv.py` の本体——`internal` は `diff-versions.py` の `compare` と `check-findings-csv.py` を読み込む
- 層を移す手順そのもの（`references/qa-csv.md` の「層を移す」が既に番号の付け替えと指し先の直しを持つ——指すだけ）
- `agents/red-team.md`・`formal-checker.md`・`estimate-checker.md`
- 説明文（`plugin.json`・`marketplace.json`・`SKILL.md` の frontmatter）と `README.md` の説明の段落——「内部の Q&A 表に開発者の決定として記録し」は偽にならない
- feasibility・dev-loop（仕様の穴）が内部の表に足す行の書き方

依存の追加・更新: なし

**複製の数**: 「作業中の版で足した・変えた `D-` の行を Domain Checker が確かめる」を述べる箇所は 7（`spec-exit.md` の条件 5 と指摘の表の印が原本、`spec-scope.md`・`domain-checker.md`・`spec-review/SKILL.md`・`check-review-record.py` の docstring と定数・`CLAUDE.md`・公開ページ）。
印の文字列は `spec-exit.md` が原本で、`check-review-record.py` の定数が写し——`test-check-review-record.py` が突き合わせる。分けない理由: 決まりの原本は `references/`、ほかは指すか、読む側の要約。

## デプロイ経路

プラグイン（`marketplace.json` のカタログと、`link-skills.sh` を使う利用者の `git pull`）と公開サイトの再ビルド。**マージの反映: ドキュメントとプラグインの配布**（`.claude/dev-loop.md` の宣言どおり）。

## 受入基準（不変条件 × 経路）

入口（内部の表の行を書く・確かめる・数える場所）: spec-review 手順 2・4（Planner が `D-` の行を書く）・手順 3（判定役に渡す）・手順 4（振り分けと層を移す）・手順 5（2 回目のあとの直しと狭いパス）・
手順 6（抜ける条件の判定と記録）・`check-review-record.py`（`conditions`・`internal`）・scaffold（記録の表の最後の実行の行が `抜けた` かを読む）・feasibility と dev-loop（内部の表に行を足す——この周は書き方を変えない）。

| # | 不変条件 | 経路 | 守り方 | 証明 |
| --- | --- | --- | --- | --- |
| A1 | Domain Checker の定義が、渡された `D-` の行ごとに「どの選択肢でも利用者に見える結果が変わらないか」を判定し、1 行ずつ印 `（内部の行: <No>）` で返す（変わらない→案 `内部の Q&A 表に記録する`・重さ `補い`／変わる→案 `共有の Q&A 表に起票する`・重さ `判断が要る`・業務の言葉の質問／迷ったら変わる側／渡されなければ「見ていない」） | spec-review 手順 3 の Domain Checker | `domain-checker.md` | 読んで確かめる（判定役の振る舞いは未証明——下） |
| A2 | spec-review が、1 回目・2 回目のレビューで Domain Checker に作業中の版で足した・変えた `D-` の行を渡し、2 回目のあとで内部の表を変えたら狭いパスに Domain Checker を入れ、手順 4 で「変わる」の行を `qa-csv.md` の「層を移す」で共有の表へ移し、指摘の表に印つきで残す | spec-review 手順 3〜5 | `spec-review/SKILL.md` | 読んで確かめる |
| A3 | `check-review-record.py internal` が、作業中の版で足した・変えた `D-` の行のうち、その回の指摘の表に Domain Checker の確かめた行（印つき・`確かめた`）が無いものがあれば 1、`共有の Q&A 表に起票する` に振り分けたのに内部の表に残る行があれば 1、すべて確かめていれば 0。前の版から変わらない行は求めない。v1 は全部の行。読めない・検査に通らない・重ね合わせが決まりに反するなら 2 | spec-review 手順 6 | 本体 | 試料と変異（`test-check-review-record.py`） |
| A4 | `conditions` が、確かめの行（印つきの `内部の Q&A 表に記録する`）だけで「2 回目を回した」と読まない（1 回目の Red Team の効く重さを数え落とさない）。前からの判定は変わらない | spec-review 手順 6 の `conditions` | 本体 | 試料と変異（前からの試料が全部通る） |
| A5 | 抜ける条件 5 が内部の行の確かめを含み、`internal` を名指しし、spec-review の手順 6 が `internal` が 0 のときだけ `抜けた` に書き換える。指摘の表の節が印の書き方を持つ | `spec-exit.md`・spec-review 手順 6 | 文書 | 読んで確かめる＋印の文字列は `test-check-review-record.py` の突き合わせ |
| A6 | `spec-scope.md` の振り分けの区分が、内部の表に記録した判断を判定役が確かめることを指す | 区分を読む人・判定役 | 文書 | 読んで確かめる |
| A7 | 版を 3 種類で揃えて上げ、`check-all.py` が緑 | CI | 版の行 | `check-all.py`・`check-plugin-versions.py` |
| A8 | 必須の掛け算: 受入基準を Verifier と `/code-review` の両方に、1 パス目と 2 パス目（または「該当なし」）で渡す | 関門 | 委譲文 | 関門の記録 |

**この環境では証明できないもの（未証明）**: A1 の判定役が実際の仕様レビューで内部の行を正しく判定すること（判定役を実際の正本で走らせて観測していない——人間のレビューに回す）。

**守らないもの（計画で決めた）**: spec-review を抜けた後に feasibility・dev-loop が内部の表に足した行は、次の spec-review の実行まで確かめられない（scaffold は記録の表の最後の実行の行を読むだけ）——`check-review-record.py` の docstring に書く。

**生成物**: 生成物なし（変更するファイルに生成物は無い。`skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` を測るもので、この周は触らない——`--check` は `check-all.py` で見る）。

## 未解決・確認待ち

- H1〜H3 の確認の Issue（利用者が戻ってから確かめる）: 起票したら番号を書く。

## 関門の記録

```dev-loop-gates
周の base: 8f879f5f3bc109f072bc3bf4f5b5c2a2401c5fd6
```

## 手順 8（起票数）

- この周の起票: 3 件（仕様の穴を推奨で決めた確認の Issue——H1・H2・H3。関門の指摘からの起票は振り分けの後に足す。起票の承認は不在のため訊いていない）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/1155-internal-qa-check`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1155`・起点 `8f879f5`・
  base `8f879f5f3bc109f072bc3bf4f5b5c2a2401c5fd6`（`origin/main`＝`refs/remotes/origin/HEAD` を start-point に `prepare-worktree.sh` が出した値）。
- 関門: まだ回していない。
- 交絡を潰した手順: 実験なし（まだ）。
- 割り目: 割らない（cruise の周）。

## 既知の限界・決着済みの論点

- H1〜H3（上の「決めた値」）——穴の記録。決着の理由が誤っていると判断したなら、それは新しい反証である。
- 判定役に Domain Checker を選んだのは Issue の案 1 のとおり（別の判定役にする理由は本文に無い）。
