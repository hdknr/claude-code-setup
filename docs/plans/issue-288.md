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
    **実際に写しが古くなった実績がある**（#258 の時点は `budget-signoff-v<n>`、#270 で命名が変わって手で直した）
  - proposal 当時 :75（いま :79 手書き部分の 4 項目）: `tree.md` :57 の列挙の写し → 指し先へ
- **I3**: 指し先が実在し、指した節に指すと書いた内容がある（`check-skill-pointers.py` が実在と散文の「X」を見る。中身は目視）
- **I4**: 版が 3 種類で揃っている（`marketplace.json`・`plugin.json`・spec-loop の 5 つの SKILL.md の 2 行）。0.21.0 → 0.21.1
- **I5**: 手順の意味が変わらない（タグを付けない・照合の終了コード・手書き部分の置き場所と並び）

経路（I1・I2 を破りうる入口）:

- 4 ファイルの :26 の見出し文と、その直下の箇条
- 同じファイルの本文でタグ名・手書き部分を写している行（grep `signoff/v` `背景と目的`）
- CI の `check-norm-markers` / `check-duplicate-counts`（「次の N つ」の件数が箇条の数とずれる）

証明できないもの: なし（すべて文面の機械検査と目視で確かめられる）

生成物: **生成物なし**——spec-loop の SKILL.md は `skill-metrics.py`（dev-loop の SKILL.md のみ）の対象外、図も触らない。

必須要件の掛け算: 受入基準を Verifier と /code-review の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し）。

## 未解決の判断

- なし

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/288-spec-loop-pointer-form`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-288`、起点 `ae7b544`、
  base の参照 `origin/main`、base の SHA `ae7b544963a87562aa0bb5ae635e12ba2b898b19`
- 関門: まだ
- 反証・差し戻し: まだ
- 交絡: 実験なし

## 既知の限界・決着済みの論点

- 4 ファイルの他の箇所の列名・状態名への言及は直さない（変更範囲の「触らない」）。理由: 指し先の形は「書かない」と約束しないので違反にならない

この周の起票: 0 件
