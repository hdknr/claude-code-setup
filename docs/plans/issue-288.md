# Issue #288 — spec-loop の 4 つの SKILL.md を禁止の形から指し先の形へ

## 変更範囲

触る:

- `plugins/spec-loop/skills/req-loop/SKILL.md` — 「データの決まり」の冒頭（:26）・版の 2 行
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 同上
- `plugins/spec-loop/skills/feasibility/SKILL.md` — 同上と、CR2-5 が挙げた写し（当時の :161 → いまの :215 のタグ名）・見出しの箇条のタグ名（:31）
- `plugins/spec-loop/skills/proposal/SKILL.md` — 同上と、CR2-5 が挙げた写し（当時の :75 → いまの :79 の手書き部分の列挙）
- `plugins/spec-loop/skills/scaffold/SKILL.md` — 版の 2 行だけ
- `plugins/spec-loop/.claude-plugin/plugin.json` — version
- `.claude-plugin/marketplace.json` — spec-loop の version
- `docs/plans/issue-288.md` — この計画

触らない:

- `references/*.md`（原本。直す理由が無い）
- frontmatter と JSON の description（タグ名が出るが、本文の節の書き換えで要約は変わらない）
- 4 ファイルの他の箇所の列名・状態名への言及（`反映済み`・`暫定反映`・`回答の列` など）——指し先の形では
  「書かない」と約束しないので、言及は違反にならない。どれも既に `qa-csv.md` などを指している
- リポジトリの他のファイルに残る「ここに書かない」形（`dev-loop-design.md`・`token-metrics.py` など）——#288 の範囲外

## 乗るデプロイ経路

プラグインのカタログ（version bump でクライアントに届く）。`docs/` の公開サイトには `docs/plans/` 以外の変更なし
（`docs/plans/` は mkdocs の nav に載るかは確認しない——このリポジトリの既存の周の計画と同じ扱い）。

## 同じことを述べている箇所の数

- 禁止の形の見出し: 4 箇所（各 SKILL.md の :26）。どれも独立に直す（共有の文は無い）
- タグの命名の写し: feasibility :31・:215、proposal :65（原本は `references/signoff-tags.md`）
- 手書き部分の列挙の写し: proposal :79（原本は `references/tree.md` :57）
- 分けない理由: いずれも同じ 1 つの規約（CLAUDE.md「〇〇を正とする」）の適用で、1 周で 4 ファイルを揃えないと
  同じプラグインの中で形が食い違う

## verify の受入基準

不変条件:

- **I1**: 4 つの SKILL.md に禁止の形（「このスキルに書かない」）が残らない。代わりに「〇〇は `../../references/…` を正とする」の形で、
  元の見出しが列挙していた項目（列・起票元・状態・「まだ無い」の印・ツリー・抜ける条件・範囲の線・置き場所・タグの命名・照合の決まり・版の差分）
  を**落とさず**どれかの指し先に結び付けている
- **I2**: CR2-5 が挙げた 3 箇所を確かめ、写しであるものは指し先に置き換え、写しでないものは理由を計画に残す
  - feasibility 当時 :120（いま :166「費用への影響の列」）: 列名への言及で列挙の写しではなく、既に `qa-csv.md` を指す → **残す**
  - feasibility 当時 :161（いま :215 `signoff/v<n>/budget-<k>`）: タグの命名の写し → 指し先へ。
    **実際に写しが古くなった実績がある**——命名は 2 度変わった（`budget-signoff-v<n>` → #262（e6f570e）で
    `v<n>/budget-signoff-<k>` → #270（8d30068）で `signoff/v<n>/budget-<k>`）。1 パス目の CR8 で訂正（当初「1 度」と書いた）
  - proposal 当時 :75（いま :79 手書き部分の 4 項目）: `tree.md` :57 の列挙の写し → 指し先へ
- **I3**: 指し先が実在し、指した節に指すと書いた内容がある（`check-skill-pointers.py` が実在と散文の「X」を見る。中身は目視）
- **I4**: 版が 3 種類で揃っている（`marketplace.json`・`plugin.json`・spec-loop の 5 つの SKILL.md の 2 行）。0.21.0 → 0.21.1
- **I5**: 手順の意味が変わらない（タグを付けない・照合の終了コード・手書き部分の置き場所と並び）

経路（I1・I2 を破りうる入口）:

- 4 ファイルの :26 の見出し文と、その直下の箇条
- 同じファイルの本文でタグ名・手書き部分を写している行（grep `signoff/v` `背景と目的`）
- CI の `check-norm-markers` / `check-duplicate-counts` / `check-skill-pointers`
  - **「次の N つ」の件数が箇条の数とずれる経路は、CI では守れない**（1 パス目の CR5 で訂正。`check-duplicate-counts` は同じ語句に付いた
    数どうしを比べるだけで、箇条を数えない——`次の 5 つ` に変えても緑だったと /code-review が変異で示した）。**目視で確かめる**
    （5 ファイルとも件数 = 箇条の数。Verifier と /code-review の両方が確認）
  - 散文の指し先は「」で引いた形だけが `check-skill-pointers` の照合に入る（CR2）

証明できないもの: なし（すべて文面の機械検査と目視で確かめられる）

生成物: **生成物なし**——spec-loop の SKILL.md は `skill-metrics.py`（dev-loop の SKILL.md のみ）の対象外、図も触らない。

必須要件の掛け算: 受入基準を Verifier と /code-review の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し）。

## 未解決の判断

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/288-spec-loop-pointer-form`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-288`、起点 `ae7b544`、
  base の参照 `origin/main`、base の SHA `ae7b544963a87562aa0bb5ae635e12ba2b898b19`
- 実装: 済み（コミット済み。`check-all.py` 44/44 緑）。手順 4 の割り目: 提案した → 「ここで割る」が選ばれた（2026-10-23）
- 関門:
  - 1 パス目 Verifier（`dev-loop:dev-loop-verifier`、sonnet）: **反証 0 件**
  - 1 パス目 /code-review（high）: **指摘 8 件**（直す 2・残課題 6。採否は下の表）
  - 指摘対応: CR6・CR7（CR2 も同じ行で解消）を直した。次は **2 パス目の Verifier と /code-review の両方**（どちらも未着手）。指摘対応はコミット済み（`4dab561`、`check-all.py` 44/44 緑）。
    手順 6 の割り目: 提案した → 「ここで割る」が選ばれた（2026-10-23）
  - 2 パス目 Verifier（`dev-loop:dev-loop-verifier`、sonnet）: **反証 0 件**（観察 1 件 = CR2-6 と同じ）
  - 2 パス目 /code-review（high）: **指摘 6 件**（直す 1・残課題 5。採否は下の表）
  - 2 パス目の指摘対応: 起点 `b068f73`（指摘対応を始める直前の HEAD）。CR2-3 を直した（`088480c`、`check-all.py` 44/44 緑）。
    狭いパス（`dev-loop:dev-loop-verifier`、sonnet、`git diff b068f73`）: **反証 0 件**。変異は 0 本——
    禁止の形の再導入を見る歯止めが無いと grep で分かり、当てなかった（赤 0・素通り 0。陽性対照なし）。
    観察 1 件: proposal :83・:87 の「書かない」は生成元を指す手順上の禁止と判断（人間が見るならここ）
- 反証・差し戻し: Verifier の反証 0 件（1・2 パス目とも）。/code-review の指摘で手順 4 に差し戻し 1 回
- 交絡: CR2 を直したことの確認に変異を 1 本当てた——リポジトリの外の複製（`.git` なし）で、変異の前に
  `check-skill-pointers` が緑（陽性側）、`tree.md` の `## 置き方の決まり` を改名すると `proposal/SKILL.md:80` で赤

## 既知の限界・決着済みの論点

- 4 ファイルの他の箇所の列名・状態名への言及は直さない（変更範囲の「触らない」）。理由: 指し先の形は「書かない」と約束しないので違反にならない
- proposal の v2 の箇条（:82「背景と目的」と、変える案・代替案・リスク）は残す。理由: v2 の提案書で何を書くかの説明で、
  `tree.md` の 4 項目の列挙を写したものではない（CR2-5 の 3 箇所にも入らない。v2 の節は #264 で後から入った）

### 1 パス目の指摘と採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: proposal の frontmatter が以前の名前（`req-signoff`・`budget-signoff`）を持ち、`signoff-tags.md:25` は「以前の名前は読まない」 | 示せる（`proposal/SKILL.md:3` と `signoff-tags.md:25`） | 無し（この差分の前からある。frontmatter は変更範囲外） | 残課題 |
| CR2: proposal :79 の指し先が「」無しで `check-skill-pointers` の照合に入らない | 示せる（変異で緑） | 無し（I3 の「実在する」は満たしている） | 残課題 → CR7 と同じ行を直したので解消（変異で赤になることを確かめた） |
| CR3: proposal :87 の生成する表の列挙（範囲・費用・期間・主な決定事項）が `tree.md` :58 の写し | 示せる（`proposal/SKILL.md:87`） | 無し（I2 は CR2-5 の 3 箇所） | 残課題 |
| CR4: proposal :82 の v2 の箇条が手書き部分を散文で並べ、計画に判断が無い | 示せる | 無し | 残課題（判断は上の「決着済み」に書いた） |
| CR5: 計画が「次の N つ」のずれを `check-duplicate-counts` が守ると書いたが守らない | 示せる（変異で緑） | 無し（件数は 5 ファイルとも正しい） | 残課題（計画の経路の節を訂正） |
| CR6: req-loop の見出しが「まだ無い」の印を挙げるが、どの箇条にも無い | 示せる（`req-loop/SKILL.md:29-31`。印は `qa-csv.md:41`） | **I1** | **直す**（qa-csv の箇条に足した） |
| CR7: 指し先を手書き部分の中身へ移したので、置き場所 `docs/v<n>/proposal/` と並べ方が指し先を失った | 示せる（差分） | **I1** | **直す**（置き場所・並べ方まで `tree.md` の「置き方の決まり」を指す形に） |
| CR8: 計画の実績の記述が命名の変更を 1 度と書いた（実際は 2 度） | 示せる（e6f570e・8d30068） | 無し | 残課題（計画を訂正） |

### 2 パス目の指摘と採否

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR2-1: proposal :80 が「何を手で書くか」まで `tree.md` を正としたが、`tree.md` には v1 の 4 項目しか無く、:82 の v2 の箇条（変える案）と食い違う | 示せない（v2 で何を書くかを読み誤った実例は無い。:82 は差分の前からあり、意味は変えていない） | 無し | 残課題 |
| CR2-2: 本文の正しいタグ名を指し先にしたので、綴りが出るのは frontmatter :3 の古い名前だけになった（CR1 の悪化） | 示せる（`proposal/SKILL.md:3`・`signoff-tags.md:25`） | 無し（frontmatter は変更範囲外。I5 の手順の意味は本文の指し先で保たれる） | 残課題（CR1 と一緒に人間に渡す） |
| CR2-3: spec-review :188・:196 に禁止の形「（ここに写さない）」が残る | 示せる（grep） | **I1**（「4 つの SKILL.md に禁止の形が残らない」はファイル全体を指す） | **直す**（括弧を外した） |
| CR2-4: req-loop :29 の「まだ無い」の印が「」の形でなく `check-skill-pointers` に照合されない | 示せる（外の複製で `qa-csv.md` の印を消しても緑） | 無し（I3 の中身は目視で満たす） | 残課題 |
| CR2-5: 計画の「証明できないもの: なし」——中身の対応は目視だけで、機械は後退を検出しない | 示せる（同上） | 無し（計画は関門の検査対象外） | 残課題（PR コメントで、目視だけで守っている項目として名指しする） |
| CR2-6: feasibility :41 の `tree.md` の置き方の決まりが「」無し | 示せる（改名で :41 が出ない） | 無し（差分の前からある行。I3 の実在は満たす） | 残課題 |

この周の起票: 0 件
