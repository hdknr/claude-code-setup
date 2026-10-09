# #204 plugins/ のプロンプト監査 — cmux / orca / workspace-setup の修正

監査結果は #204 のコメントを正とする。この PR が扱うのは、**cmux / orca / workspace-setup スライスで判断が済んだ指摘だけ**である。
dev-loop の指摘は、個別に起票した Issue（#205〜#211）で扱う。

## 1. 変更範囲

触る:

- `plugins/cmux/` — F1（バナーと README の「キャッシュが更新されていない」）・F4（description）・版
- `plugins/orca/` — F2（「動作は揃えてある」）・F4（description）・版
- `plugins/workspace-setup/` — F3（プライベートを強制。人間が判断済み）・F5（frontmatter）・版
- `.claude-plugin/marketplace.json` — 版だけ

触らない:

- `plugins/dev-loop/` 一切
- cmux の振る舞いの指摘（FL1〜FL6。#196 / #197 / #202 ほか）

## 2. 受入基準

- [x] cmux の `SKILL.md` と `README.md` に「キャッシュが更新されていない」という断定が無い
- [x] orca の `SKILL.md` と `README.md` が「動作は揃えてある」と主張していない
- [x] workspace-setup が、プライベートで作るかどうかを利用者に訊かない（強制だけが残っている）
- [x] cmux / orca の frontmatter description が各モードの動作と、いつ使うかを述べている。workspace-setup に description がある
- [x] 版が 3 箇所（workspace-setup は 2 箇所）で揃っている: cmux 1.1.5 / orca 1.0.1 / workspace-setup 1.0.2
- [x] `check-all.py` が緑（下の「検証」）

## 3. 検証

`python3 scripts/check-all.py` — 30/30 本 OK（失敗 0 / 飛ばし 0）。コミット後に PR 限定の 3 本（version-bump・description-sync・plan-scope）を回し直した結果は PR の CI を正とする。
