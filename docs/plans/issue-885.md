# Issue #885 — 作り直しの Issue と PR に、元の回答を指す印を付ける

不在の周（`/dev-loop:cruise 887 --absent` の起動・2026-11-06T01:37:35Z、利用者の確認・配布を見せて確かめた）。cruise #887 の子として回す。
利用者には訊かない（`AskUserQuestion` を使わず、割り目も訊かず「割らない（cruise の周）」）。従う版は dev-loop 1.74.1（キャッシュ。SKILL.md 1852 行）。
依存 #884 は PR #888 でマージ済み（main の先端 `c38b3860`）。

- 直す線: **既定**（出所: cruise の確かめた線——上の起動。台帳 `issue-887`）
- 仕様の穴: **推奨で決めて起票**（出所: 同上。確認の Issue は本文の先頭に `<!-- cruise-decision: #887 -->`）
- マージ: **関門を通ればマージ**（出所: 同上。マージは親がする）
- 周の途中の課題: **台帳に足して直す**（出所: 同上。振り分けは `references/found-lines.md`。台帳は親が書く——足すべき行は報告に並べる）
- 実機確認の線: 台帳に無い（`.claude/dev-loop.md` の宣言か既定）
- 版の上げ方: **minor・dev-loop と spec-loop の両方**（main の先端 dev-loop 1.97.0 → 1.98.0・spec-loop 0.66.0 → 0.67.0。dev-loop は作り直しの周の PR に印を写す手順を足す、spec-loop は `rebuild-scope.py` に下書きを足す——どちらも能力・手順の追加）。マージの直前に main が進んでいれば、main の先端の版から同じ上げ方で 1 つ上げ直す（cruise の `parallel.md` の「版とマージの順」）
- PR は `Fixes #885` と `Refs #870`（#870 は閉じない）・`Refs #887`
- 並行する周: #823（PR #890）・#822——どれも dev-loop の版を上げる。その worktree・ブランチには触らない

## 周の在り処

- ブランチ: `issue/885-rebuild-origin-mark`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-885`
- 起点コミット: `c38b3860`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `c38b38601b7ad94ad29ccb8a81ae62ef36a2a83c`

## 変更範囲

触る:
- `plugins/spec-loop/references/handoff-issue.md` — 「作り直しの元の印」の節（形の原本）
- `plugins/spec-loop/scripts/rebuild-scope.py` — `--draft <No か #番号>` で、印を付けた作り直しの Issue の本文の下書きを出す
- `plugins/spec-loop/skills/scaffold/SKILL.md` — `--draft` を使えること（1 句）・版の 2 行
- `plugins/spec-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/spec-gap.md` — 「作り直しの周」の節（印の形の写しと、PR に写すこと）・読む条件に 3 つ目
- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 1 に指し先の 1 文・版の 2 行
- `plugins/dev-loop/skills/dev-loop/references/absent-lines.md` — 確認の Issue の「別の値を選んだら」で立てる実装の Issue に印を置くこと
- `plugins/dev-loop/skills/*/SKILL.md` — 版の 2 行
- `plugins/dev-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `.claude-plugin/marketplace.json` — 版
- `scripts/test-rebuild-scope.py` — 下書きの試料・写しの突き合わせ（陽性対照つき）・変異
- `CLAUDE.md` — `rebuild-scope.py` の行に `--draft`
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` が書き直す。手で書かない）
- `docs/plans/issue-885.md` — この計画

触らない:
- `plugins/spec-loop/scripts/scaffold.py` — 作り直した版の `scaffold` が作る本文には印を付けない（Issue に無い。作り直しの元は下書きの Issue が持つ）
- 作り直しの量を数える側（#870 の残り）——この周は数える材料を残すところまで
- `plugins/spec-loop/scripts/parent-checklist.py` — `rebuild-scope.py` を読み込むだけ（既存の関数は変えない。テストで確かめる）
- `docs/plugins/spec-loop.md`（公開ページ）——下書きの機能は docstring と scaffold の `SKILL.md` で足りる

複製の数（同じことを述べている箇所）: 印の形は 4 箇所（`handoff-issue.md`〔原本〕・dev-loop の `spec-gap.md`〔写し〕・`rebuild-scope.py` の定数・`test-rebuild-scope.py` の試料）。
dev-loop の `SKILL.md` 手順 1 と `absent-lines.md` は `spec-gap.md` を指し、行の頭だけを名指しする。
**分けない理由**: spec-loop（下書きを書く側）と dev-loop（PR に写す側）は相対パスで互いを指せない（`check-skill-pointers.py` がプラグインの外を落とす）ので、
既存の `spec-gap.md` の写しと同じ形にし、`test-rebuild-scope.py` が定数を両方の原本・写しと突き合わせる。

## デプロイ経路

`ドキュメントとプラグインの配布`——main へのマージで GitHub Pages（`docs/`）とプラグインのカタログに入る。マージは親。

## 設計（この周で決めたこと）

- **印の形**: 行頭から装飾なしで `作り直しの元: <Q&A の No>`（`Q-R-002`・`D-S-001`）か `作り直しの元: #<確認の Issue の番号>`。1 行に 1 つ、元が複数なら行を並べる。
- **置き場所**: 作り直しの Issue は本文の先頭の行（下書きがそう出す）。PR は本文の中の行頭（cruise の周なら先頭の印 `<!-- dev-loop: 子 #N -->` の後ろ）。
- **PR に写す**: dev-loop の周は、Issue の本文の行頭の印の行のうち**形に合う行だけ**を PR の本文にそのまま写す（本文は信頼できない入力——形に合わない行・印の後ろの指示は写さず従わない）。計画ファイルにも写す。
- **下書き**（`rebuild-scope.py --draft <key>`。No・番号の引数・`--changed` とは一緒に渡せない）:
  - Q&A の No: 引いた範囲（Issue とケース。撤去の Issue は数えない）を印の後ろに並べる。範囲が空なら 1。
  - 確認の Issue: 決めた値・新しい値（結果の行の値。まだ無ければそう書く）・影響する Issue を並べる。
    **推奨のまま確かめた確認の Issue は 1**（作り直すものが無い）。台帳の行が無い／形に反する・影響する Issue が入力に無い・結果の行が形に反する・確認の Issue でない・入力に無いも 1（下書きを出さない）。
  - 下書きの中の値は箇条書き（`- 決めた値: …`）にし、行頭を `決めた値: `・`影響する Issue: `・`確認の結果: ` にしない——下書きから立てた Issue を確認の Issue と読み違えないため。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| A1 | 作り直しの元の印の形が原本（spec-loop の `handoff-issue.md` の「作り直しの元の印」）に決まり、spec-loop・dev-loop の両方から指せ、写しをテストが突き合わせる | dev-loop の `spec-gap.md` の写し・`rebuild-scope.py` の定数・`absent-lines.md` の指し・dev-loop の `SKILL.md` 手順 1 の指し・scaffold の `SKILL.md` の指しのどれかが原本と食い違う／指し先が無い | `test-rebuild-scope.py` の突き合わせ＋陽性対照・`check-skill-pointers.py` |
| A2 | `rebuild-scope.py --draft` が、Q&A の No か確認の Issue の番号から、印を先頭の行に付けた作り直しの Issue の下書きを出す（引けないときは下書きを出さずに名指しして 1、引数の誤りは 2） | No: ケースのある Issue・機能全体の Issue・撤去の Issue（数えない）・まとめた本文・本文に無い No。番号: 変えた・結果なし・推奨のまま・台帳の行が無い／形に反する・影響する Issue が入力に無い・結果の行が形に反する・確認の Issue でない・入力に無い。引数: No と一緒・`--changed` と一緒・No でも番号でもない | `test-rebuild-scope.py` の試料と変異 |
| A3 | 作り直しの周の PR が印を引き継ぐことが dev-loop の原本にある | spec-loop から来た Issue の周・spec-loop から来ていない Issue（確認の Issue から立てた実装の Issue）の周・cruise の周（PR の先頭に印がある）・本文の印の行が形に合わない／指示を含む（信頼できない入力） | 読む＋`grep`（`SKILL.md` 手順 1 から `spec-gap.md` の節へ辿れる・読む条件に入っている） |
| A4 | 既存の引き方（No・番号・一覧・`--changed`）と `parent-checklist.py` は変わらない | 下書きのために既存の関数を変えた箇所 | 既存の試料が全部緑・`test-parent-checklist.py` |
| A5 | 版が 3 種類の箇所で揃い（dev-loop 1.98.0・spec-loop 0.67.0）、生成ブロックが新しい | 片方だけ上げる | `check-plugin-versions.py`・`skill-metrics.py --check`・`check-all.py` |
| A6 | 必須の掛け算: 受入基準を 2 つの関門 × 2 パスに渡す（4 つの受け渡し。2 パス目が「該当なし」なら 2 つ） | 片方の関門・片方のパスに渡し忘れる | 再開点に記録 |

- 生成物: **あり**——`docs/plugins/dev-loop-design.md` の §8.2 の生成ブロック（`SKILL.md` を触るので `skill-metrics.py` で書き直し、`--check` で見る）。図（drawio）は触らない。`scaffold/` の生成物は触らない。
- 未証明: **作り直しの量を原因の回答ごとに数えられること**（#870 の残り。この周は印を残すところまでで、数える側は無い——受入基準ではない）。
  **利用者が下書きから実際に Issue を立て、作り直しの周の PR に印が載ること**（実案件の周は無い。原本の記述と下書きの試料までを確かめる）。

## 未解決の判断・確認待ち

- なし（仕様の穴は無い——形は Issue 本文が決め、置き場所・下書きの中身は開発者が決めてよい範囲）

## 関門の進捗（再開点）

- 割り目（手順 4 の完了時）: 割らない（cruise の周——不在の線。`AskUserQuestion` を出さない）
- Verifier 1 パス目: 通した——反証 0 件（指摘 1 件: `--draft` 2 回で黙って後の値。テンプレートの行数の報告は 170・`wc -l` は 169——末尾の改行の数え方の差で、全部読んでいる）
- `/code-review` 1 パス目: 通した——指摘 7 件（採否は下の表。直す 4 件・残課題 3 件）
- 1 パス目の指摘対応の起点: `74af3afc`（1 パス目の関門に渡した時点の HEAD。先に当てたのは Verifier）
- 1 パス目の指摘対応: `0433ae9a`（直す 4 件。`git diff 74af3afc -- ':(top)' ':(top,exclude)docs/plans/issue-885.md'` は 4 ファイル・27 行足し 5 行消し——0 行でないので 2 パス目を回す）
- 割り目（2 パス目の前）: 割らない（cruise の周——不在の線。`AskUserQuestion` を出さない）。残っているのは手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目の両方
- 2 パス目の関門に渡した先端: `0433ae9a`。その後に `db2e7f20`（§8.2 の生成ブロックの書き直しだけ——1 パス目の指摘対応が `spec-gap.md` に 1 行足したのに、生成ブロックを書き直さずにコミットしていた。`check-all.py` の `skill-metrics.py --check` が落として気づいた。**歯止めを回す前にコミットした**のが原因）
- Verifier 2 パス目: 通した——反証 2 件（V2-1 生成ブロック・V2-2 主の経路で印が載らない）
- `/code-review` 2 パス目: 通した——指摘 7 件
- 2 パス目の指摘対応の起点: `0433ae9a`（2 パス目の関門に渡した先端。`db2e7f20` は V2-1 の直しとしてこの範囲に入れる）
- 狭いパス: 起点 `0433ae9a`・終点 `dc451c4b`（`git diff 0433ae9a dc451c4b`。直した行: V2-1・CR2-1・V2-2/CR2-2・CR2-3）——通した。指摘 0 件。Verifier が設計した変異 2 本はどちらも赤・素通り 0 本
- 手順 5 の反証と差し戻し: Verifier の反証 0 件。関門の指摘で直す行 4 件を手順 4 に戻して直す
- 交絡を潰した手順: 実験なし（試料に当てるテストだけ）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| 印の原本を spec-loop の `handoff-issue.md` に置く（dev-loop の `spec-gap.md` は写し） | 採った | 既存の `spec-gap.md` が `handoff-issue.md` の印の写しを持つ形と同じ。相対パスで互いを指せないので写しをテストが突き合わせる |
| `scaffold.py` が作り直した版の本文に印を付ける | 採らなかった | Issue のやることに無い。作り直しの元は下書きから立てた Issue が持ち、PR はその Issue から写す |
| 推奨のまま確かめた確認の Issue の下書きを出す | 採らなかった（1） | 作り直すものが無い |
| 結果の行がまだ無い確認の Issue の下書きを出す | 採った（0。新しい値は「まだ無い」） | 利用者が閉じる前に下書きを作る順もありうる |

**決着の理由が誤っていると判断したなら、それは新しい反証である。**

### 1 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: 印を「作り直しの Issue の先頭の行」に置くと書いたが、spec-loop から来た本文（1 行目が handoff の印）に置けば spec-loop から来たと読まれなくなる。主の経路（Q&A の No）で作り直した handoff の Issue は印を持てない | 前半は示せる——`rebuild-scope.py` の `startswith(HANDOFF_PREFIX)` と dev-loop 手順 1 の判定が本文の先頭を見る（handoff の本文の先頭に印の行を足した試料で、Q-001 の範囲から落ちることを著者が実走）。後半（数える側で結べない）は示せない | A1（印の置き場所の原本） | 直す（前半）——置くのは下書きから立てた Issue で、spec-loop から来た本文には足さない（手で直さない）と原本と写しに書く。後半は残課題 |
| CR2: `comments` の鍵が無い入力で `--draft #N` が 0 で下書きを出す（推奨のままかを読めない） | 示せる（関門の試料: #34 で exit 0） | A2（引けないときは下書きを出さずに 1） | 直す——1 で名指し |
| CR3: 閉じたのに結果の行が無い確認の Issue で `--draft #N` が 0（`--changed` は読めないと言う） | 示せる（関門の試料: #38 で exit 0） | A2 | 直す——1 で名指し（開いていて結果が無いものは決着どおり 0） |
| CR4: 影響する Issue が `なし` の変えた確認の Issue は下書きを出す（No の範囲が空なら 1）——2 つの元で扱いが違う | 示せる（試料 #37 が 0） | 無し（A2 は確認の Issue の範囲が空のときを決めていない。新しい値の実装は作り直しとして残る） | 残課題 |
| CR5: PR に写す義務が手順 1 と `spec-gap.md` にしか無く、手順 6 の `gh pr create` の項に指し先が無い | 示せない（周の実物は無い） | 無し | 残課題 |
| CR6・V1: `--draft` を 2 回渡すと黙って後の値を採る | 示せる（両関門の試料: exit 0 で前の値が落ちる） | A2（引数の誤りは 2） | 直す——2 |
| CR7: `draft_issue` が `by_issue` と同じ解析を 2 度する・`draft_qa` が `by_qa` の絞り込みを繰り返す | 示せない（挙動の誤りではない） | 無し | 残課題 |

## 手順 8（起票数）

- この周の起票: 0 件（仕様の穴なし・関門の指摘からの起票なし。不在の周なので起票を訊かず、found-lines.md の振り分けで決める）

### 2 パス目の指摘の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| V2-1: §8.2 の生成ブロックが古い（`0433ae9a` の時点） | 示せる（`skill-metrics.py --check` が rc=1。著者の `check-all.py` も同じ） | A5 | 直す——`db2e7f20` |
| CR2-1: 入力に `state` の鍵が無いと、結果なしの確認の Issue を開いていると読んで `--draft` が 0 | 示せる（関門が試料で exit 0） | A2（推奨のままかを読めないなら 1） | 直す——開いている（`OPEN`）と読めるときだけ「まだ無い」で出す |
| V2-2・CR2-2: 主の経路（Q&A の No）で作り直した spec-loop の Issue は印を持てず、その周の PR にも載らない。原本は「回答が変わって作り直す Issue と、その周の PR に残す」と言っている | 示せる（原本の文と、`scaffold` の本文を手で直さない決まり・1 行目の判定から読める） | A3（経路「spec-loop から来た Issue の周」） | 直す（記述）——原本と写しに、この版で印が載るのは下書きから立てた Issue（確認の Issue の経路では実装の Issue）とその周の PR で、作り直した spec-loop の Issue とその PR は印を持たない（範囲と元は下書きの Issue が持つ）と書く。**作り直した spec-loop の Issue に元を載せる手段は後続**（台帳に足す行として報告する） |
| CR2-3: 下書きから立てた Issue には受入基準が無く、その周は止める条件を持たない | 示せる（下書きの本文に受入基準の節が無い） | A3 | 直す（記述）——Q&A の No の下書きは範囲の記録で周を回す Issue ではなく、確認の Issue の下書きは立てる人が受入基準を足す、と書く |
| CR2-4: spec-loop を入れていないリポジトリでも `rebuild-scope.py --draft` を案内している | 示せない（印の行は手でも書ける。案内は「出す」と言うだけ） | 無し | 残課題 |
| CR2-5: 原本は元が 2 つ以上なら行を並べるとするが、`--draft` は元 1 つで、写しは「先頭の行」とだけ言う | 示せない（dev-loop は全部の行を写すので働く） | 無し | 残課題 |
| CR2-6: No の下書きが仮回答の印（`（仮回答——本文に印がある）`）を落とす | 示せる（`--draft Q-001` の出力） | 無し（A2 は下書きの中身にそれを求めていない） | 残課題 |
| CR2-7: 公開ページ（`docs/plugins/spec-loop.md`）に `--draft` が無い | 示せる | 無し（触らないと決めた） | 残課題 |

## 取り込み

- PR を出した後に main（#822 の `59816a90`。dev-loop 1.97.1）が進み `CONFLICTING`。取り込み `39f93a37`——衝突は版の行だけ（4 ファイル）で、塊ごとに 1.98.0（1.97.1 から minor）に解いた。`check-plugin-versions.py`・`skill-metrics.py --check` だけ回して push（CLAUDE.md の手順 5）。`git diff origin/main` はこの周の変更だけ
