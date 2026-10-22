# Issue #332 — check-skill-pointers.py が spec-loop の ../../references/・agents/・プラグイン直下の references/ を見ない

## 変更範囲

触る:

- `scripts/check-skill-pointers.py` — 走査にプラグイン直下の `agents/*.md`・`references/*.md` を足す（プラグインの根から解決）。`XREF` に `../` の前置を許す。ほかの持ち主を名指しした指し先を解決しない。docstring の「守る」「守らない」
- `scripts/test-check-skill-pointers.py` — 試料 5 本と変異 5 件。本体の行の字下げが変わった既存の変異 4 件の当て先
- `CLAUDE.md` — `check-skill-pointers.py` の説明に 1 文
- `docs/plans/issue-332.md` — この計画

触らない:

- `plugins/` の中身——実物の指し先はすべて解決している（下の実測）。**プラグインの版も上げない**（中身を変えないので）
- 名指しした先（dev-loop のスキル・このリポジトリ）に実在するかの検査——免除するだけで解決しない。docstring の「守らない」に書く
- `scripts/` と対象リポジトリの `scripts/` の区別（docstring に既にある「守らない」）の一般的な解決

### 同じことを述べている箇所の数

検査の範囲を述べる箇所: `check-skill-pointers.py` の docstring（原本）・`CLAUDE.md` の説明の **2 箇所**。
**分けない理由**: CLAUDE.md は 1 文で指すだけ（「何を守り何を守らないか」の列挙は docstring にしか無い）。

## 乗るデプロイ経路

反映経路なし——`scripts/` と `CLAUDE.md`、`docs/plans/` だけ。`docs/plans/` は mkdocs の `nav` に載るか未確認だが、main へのマージで Pages のビルドが走る（中身はこの計画だけ）。

## 設計の決定（この周で著者が決めたもの。関門に渡す）

- **D1 プラグイン直下の起点**: `agents/*.md`・`references/*.md` の指し先はプラグインの根から解決する。実物（判定役の 4 体）がそう書いている
- **D2 ほかの持ち主の名指し**: 指し先の直前が `<プラグイン名> の` ／ `<プラグイン名> のスキルの` ／ `このリポジトリの` なら解決しない。プラグイン名は**自分以外の、`plugins/` に実在するディレクトリ名**に限る。理由: プラグイン直下の決まりに、dev-loop とこのリポジトリのファイルを名前で指す行が実物で 3 つある（`qa-csv.md:42`・`handoff-issue.md:102-103`）。**解決すると正しい記述なのに落ちる**。本文を書き換えて避けるのは docstring が「設計ではなく偶然」と呼ぶ形なので採らない
- **D3 免除はスキルの中にも掛かる**（一律）。いまスキルの中に該当する行は無い（緑のまま）

## verify の受入基準

### 不変条件

1. **#332 の再現が赤になる**——spec-loop の散文の指し先が引く節の名前を壊すと（`red-team.md`・`formal-checker.md`・`spec-review/SKILL.md` の `../../references/spec-scope.md` の「振り分けの区分」）、非ゼロで終わり、壊した行を名指しする
2. **実リポジトリが緑のまま**——いま正しい指し先で偽の赤を出さない
3. **プラグイン直下の判定役・共有の決まりの、囲まれた指し先の実在も見る**——綴りを壊せば赤
4. **ほかの持ち主の名指しは解決しない／自分の名前とプラグインでない名前は免除しない**
5. **既存の「守る」はすべて変異で殺せたまま**、新しい「守る」も 1 対 1 で変異を持つ
6. **歯止めは全部緑**（`check-all.py`）
7. **docstring と CLAUDE.md の説明が、実際の範囲と食い違わない**

### 経路（不変条件を破りうる入口）

| 入口 | 守り方 |
| --- | --- |
| スキルの `SKILL.md`・`references/`・`prompts/` | 既存の走査（変更前と同じ起点） |
| スキルから `../../references/x.md` の「X」 | `XREF` の前置（不変条件 1） |
| `plugins/<p>/agents/*.md` | 新しい走査、起点はプラグインの根（1・3） |
| `plugins/<p>/references/*.md` | 同上 |
| プラグイン直下の `prompts/` `scripts/` の Markdown | **見ない**（いま実物が無い。下の既知の限界） |
| `README.md`・`docs/`・`CLAUDE.md` から張られた指し先 | **見ない**（docstring の既存の「守らない」） |
| ほかの持ち主の名指しが行をまたぐ | 囲まれた指し先は免除されず落ちる側に倒れる（docstring の「守らない」） |

### この環境では証明できないもの

無し（すべて手元の木と変異で当てられる）。

### 生成物

生成物なし（`diagrams/exports.json`・`skill-metrics.py` の生成ブロックとも、このファイル群に依らない）。

## 関門の進捗（再開点）

- **周の在り処**: ブランチ `issue/332-pointer-plugin-level`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-332`、起点 `b4f68bf`、base の参照 `origin/main`（`refs/remotes/origin/HEAD`）→ SHA `b4f68bf7cfa0eb84a122d3a3ebd84d8d4d7884bf`
- 実装: 済み（`1235983`）。`check-all.py` 44/44 本・失敗 0（末尾の集計行。コミット直前の作業ツリーで回した）
- 割り目 1（手順 4 の後）: 訊いた → **「ここで割る」が選ばれた**。次は手順 5（Verifier 1 パス目）と手順 6（`/code-review` 1 パス目）。どちらも未着手
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未
- 反証・差し戻し: 0 件
- **交絡を潰した手順**:
    - 再現（不変条件 1）: 退避先（scratchpad。`plugins/` だけを写した）で節の名前を壊し、**修正前の本体で緑（陽性対照: 見えていなかった）**、修正後で赤 4 行（`spec-review/SKILL.md:165・168`・`formal-checker.md:35`・`red-team.md:44`）
    - 免除（D2）: 免除を外した本体を実リポジトリに当てると**ちょうど実物の 3 行**（`handoff-issue.md:102・103`・`qa-csv.md:42`）が赤。免除があることで緑になっていることを見た

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| プラグイン直下の `prompts/` `scripts/` の Markdown を見ない | 採らない | いま実物が無い。足すときに走査の対象を足す |
| 名指しした先に実在するかを見ない | 採らない | 名指しの書き方（`dev-loop のスキルの`）から指す先のディレクトリを一意に決められない |

この周の起票: 0 件（コミット後に確定）
