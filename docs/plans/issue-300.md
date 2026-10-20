# Issue #300 — `--red-check --in-progress` で両版とも失敗したときの文言と、「前の版の状態を判定できない」の扱い

元の周: #294（PR #297）の `/code-review` 2 パス目の指摘 R2-6。

## 決めたこと

- **作り直しの経路（`--in-progress`）で、追加・変更のケースがどちらの版の期待も満たさないときは、まず作りかけの実装の誤りを挙げる。**
  終了コードは変えない（1）。既定の経路の文言（`（前の版の仕様とも食い違う）`）は変えない——初めて作る経路では、実装は
  前の版の状態にあるはずなので、食い違いは乖離（`references/versions.md`）を指す。
- **「前の版の状態を判定できない」はスクリプトの文言を変えず、scaffold SKILL 手順 4 に扱いを足す**——前の版の Red テストが
  エラー（呼び出しの形が前の版と合わない・実装が落ちる）か飛ばされ、作業中の版のテストも緑でない。どちらの状態かを言えないので
  **乖離と読まない**。既定の経路では「この版をもう実装し始めていないか」を利用者に確かめ、作り直しの経路では作りかけの実装の誤りとして扱う。
- 複製の数: 3 箇所（`scaffold.py` の docstring・`red_check` の文言・scaffold `SKILL.md` 手順 4）＋ テストの期待値。
  分けない理由: docstring が判定の決まりの原本（`CLAUDE.md`「判定の決まりは docstring を正とする」）で、文言と SKILL は
  それを写すので、同じコミットで揃えないと食い違う。

## 変更範囲

触る:

- `plugins/spec-loop/scripts/scaffold.py` — `red_check` の文言と docstring
- `plugins/spec-loop/skills/` — scaffold SKILL.md の手順 4（全スキルの版の 2 行）
- `plugins/spec-loop/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `scripts/test-scaffold.py`
- `docs/plans/issue-300.md`

触らない:

- 判定の論理（終了コード・どのケースを 1 にするか）——文言だけ
- `「前の版の状態を判定できない」` の文言そのもの（Issue は SKILL の扱いを求めている）
- `plugins/spec-loop/README.md`（両版失敗の文言を持たない）

## デプロイ経路

プラグイン（`marketplace.json` の版を上げて main にマージ）。公開サイトは `docs/` の変更で再デプロイされるが、計画ファイルは nav に無い。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方・確かめ方 |
| --- | --- | --- | --- |
| A1 | `--red-check --in-progress` で追加・変更がどちらの版も満たさないとき、出力が作りかけの実装の誤りを候補に挙げる | `red_check` の両版失敗の分岐（値が違う・関数の改名で片方「未実装」の両方がこの分岐） | 試料「どちらの版の期待も満たさない（作り直し）」の期待を新しい文言に。変異「文言で in_progress を見ない」で赤 |
| A2 | 既定の経路の文言は `（前の版の仕様とも食い違う）` のまま・作りかけの実装を挙げない | 同上 | 試料「どちらの版の期待も満たさない」の期待を `（前の版の仕様とも食い違う）` に。変異「常に作り直しの文言」で赤 |
| A3 | 終了コードは変わらない（両版失敗は 1、判定できないは 1） | `red_check` | 既存の試料（1 を期待）がそのまま緑 |
| A4 | scaffold SKILL 手順 4 が、作り直しの経路の両版失敗を作りかけの実装の誤りとして先に扱い、「判定できない」を受けたときの扱いを両経路について書く | SKILL.md 手順 4・7 | 関門が読む |
| A5 | docstring（判定の決まりの原本）と実装の文言が食い違わない | `scaffold.py` docstring | 関門が読む |
| A6 | 版が 3 箇所で揃い、上がっている | `marketplace.json`・`plugin.json`・SKILL.md 5 本 | `check-all.py` |
| A7 | `--red-check` の文言の写しを持つ他の場所が古くならない | `references/`・README・`docs/` | `grep` で `前の版の仕様とも食い違う`・`判定できない` を全部引く |

未証明: 文言が利用者を正しい手順に送るか（読み手の判断）——人間レビューに回す。BLOCKED: なし。

生成物: `skill-metrics.py` の生成ブロック（dev-loop の SKILL.md だけが対象なので該当なし——`check-all.py` が `--check` で見る）。図なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/300-in-progress-wording`・worktree `.claude/worktrees/issue-300`・起点 `c5fe55c`・
  base `origin/main` → `c5fe55c71d7ad1295584ecb64b43b899a56b46f0`
- 実装: `f62202e`（`test-scaffold.py` 試料 137・変異 86 が緑、`check-all.py` 44/44 緑）
- 関門: 未着手（次は手順 5 の Verifier 1 パス目と `/code-review` 1 パス目）
- 割り目 1: 提案した → **「ここで割る」が選ばれた**。再開は手順 5（Verifier 1 パス目）から
- 交絡: 実験なし

## 既知の限界・決着済みの論点

（無し）
