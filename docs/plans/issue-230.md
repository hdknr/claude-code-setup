# Issue #230 — check-skill-pointers: symlink で外へ出る指し先の判定に回帰テストが無い

## 1. 変更範囲

触る:

- `scripts/check-skill-pointers.py` — docstring の「守る」に symlink の行を 1 行足す（`leaves_plugin` の docstring の言い回しを合わせる程度）。**判定のコードは変えない**
- `scripts/test-check-skill-pointers.py` — symlink の試料（外へ出る・中に留まる）と、`resolve()` 側だけを外す変異
- `docs/plans/issue-230.md` — この計画ファイル

触らない:

- 判定の挙動（Issue のとおり、本体は今も symlink を捕まえる。欠けているのは回帰テスト）
- `CLAUDE.md` のスクリプト一覧（記述は「変異テストを含む」で、本数を書いていない）
- `plugins/`（版の bump 不要）

**複製の数**: 「守る」の行と変異が 1 対 1（テストが数える）。この 2 つは同じコミットで動かす。
docstring の `leaves_plugin` が「呼ぶ側が `resolve()` で別に見る」と書いている 1 箇所。計 3 箇所、同じファイル 2 本の中で閉じるので分けない。

## 2. デプロイ経路

- 反映経路なし（`scripts/` は CI とローカルの歯止め。`docs/plans/` は記録のみ）。

## 3. 受入基準

**I1. symlink で外へ出る指し先を捕まえる判定（`resolve()` 側）を外す変異を、テストが殺す。**

| 経路 | 期待 | 守り方 |
| --- | --- | --- |
| P1 字面はプラグインの中・symlink の先が隣のプラグイン（Issue の陽性対照の木） | 本体 rc=1 | 試料を足す |
| P2 `resolve()` 側だけを外した変異 | テストが「変異を殺せる」で落とさない（＝殺す） | 新しい変異 |
| P3 字面側だけを外した変異（既存「行き着く先だけを見る」） | 引き続き殺す | 既存 |
| P4 両方を外した変異（既存「プラグインの外を見逃す」） | 引き続き殺す | 既存 |

**I2. 過剰に落とさない**: symlink の先がプラグインの中なら rc=0（陰性側の対照）。

**I3. 「守る」と変異が 1 対 1**（テスト自身が数える）。`check-all.py` が緑。

### 証明の手段

- I1: **修正前のテストに `resolve()` 側を外す変異を当てると緑（＝殺せない）、修正後は赤（殺す）**ことを
  両方見る（陽性対照）。変異は本体のコピーにだけ入れる（リポジトリは触らない）。
- 未証明: なし（すべてこの環境で走る）。symlink を作れない環境（Windows の一部）でテストがどうなるかは見ない。

### 生成物

生成物なし（drawio・`SKILL.md` の測定値のどちらにも触れない）。

## 4. 未解決

なし。

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/230-skill-pointers-symlink-test`・worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-230`・
  起点 `fe726b1`・base 参照 `origin/main` → `fe726b1df5dfc55cf341ccc1a470d61c25e1cad6`
- 関門: 未着手
- 交絡: 未

## 6. 既知の限界・決着済みの論点

（まだ無い）
