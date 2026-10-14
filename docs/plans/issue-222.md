# Issue #222 — check-pr-preconditions.sh の呼び出しが worktree 隔離のガードに拒否される

## 1. 変更範囲

触る:

- `plugins/dev-loop/skills/dev-loop/SKILL.md` — 手順 6「走らせる形は、素の 1 行に保つ」に、終了コードを `$?` で拾わない旨を足す。版のバナー
- `plugins/dev-loop/.claude-plugin/plugin.json` — version 1.38.2 → 1.38.3
- `.claude-plugin/marketplace.json` — 同上
- `docs/plans/issue-222.md` — この計画ファイル
- `docs/plugins/dev-loop-design.md` — §8.2 の生成ブロック（`skill-metrics.py` の再生成のみ。手で書かない）

触らない:

- `scripts/check-pr-preconditions.sh` 本体（スクリプトは拒否の原因ではない。素の形は通る——下の実測）
- Issue の「参考」に挙がった他の 2 形（ヒアドキュメント中の `git`・長い `--body`）。
  `references/guard-rejections.md` が既に「長い本文はファイルに落として渡す」を持っている。PR コメントの残課題に書く
- `references/guard-rejections.md`（拒否後に読むファイル。今回の規定は拒否される前に効かせたいので起点側に置く）

**複製の数**: 「スクリプトの終了コードで分岐する」を述べている箇所は 2 つ（手順 4 の `prepare-worktree.sh`、
手順 6 の `check-pr-preconditions.sh`）。**規定は手順 6 の「走らせる形」1 箇所に置く**——
「走らせる形」の原本はそこで、手順 4 の作成は通常メインの作業ツリー（ガードの外）から走る。分けない理由: 1 行の追加で完結する。

## 2. デプロイ経路

プラグインの版を上げる（利用者は `plugin update` で取得）。公開サイト（`docs/`）は計画ファイルの追加のみ。

## 3. 受入基準

不変条件:

- **A**: `SKILL.md` に書いた呼び出し形のとおりに読者が走らせると、worktree 隔離セッションでガードに拒否されない。
- **B**: 読者が終了コードによる分岐（0〜4）を行える——終了コードを得る手段が失われていない。
- **C**: 版が 3 箇所（`marketplace.json` / `plugin.json` / `SKILL.md` の 2 行）で 1.38.3 に揃う。

経路（A を破りうる入口）:

1. 手順 6 のコードブロックそのもの（素の 1 行）——実測で通る
2. 「終了コードで分岐する」を読んで、読者が `; echo rc=$?` を足す——**#196 で実際に起きた形**。今回の追加で塞ぐ
3. 手順 4 の `prepare-worktree.sh` に同じ足し方をする——新規の周を worktree セッションの中から始めた場合。
   手順 6 の「走らせる形」は一般則として書くので、そこを読めば同じく塞がる（手順 4 側に指し先は置かない——上の複製の判断）

### 証明の手段（実測、2026-10-14、worktree 隔離セッション、`EnterWorktree` で入場、dev-loop 1.37.0 の同梱スクリプト）

| 形 | 結果 |
| --- | --- |
| `bash <script> issue/222-pr-preconditions-guard` | 通った（陽性対照） |
| `bash <script> issue/222-pr-preconditions-guard; echo rc=$?` | **拒否**（#196 と同じ文面） |
| `bash <script> issue/222-pr-preconditions-guard; echo done` | 通った → `;` ではなく `$?` が引き金 |
| `bash <script> issue/999-no-such-branch`（素の形・不一致） | 道具の結果に `Exit code 2` が出た → B は素の形で満たせる |

観測窓: 各形 1 回ずつ。harness はこのセッションの版のみ。`$?` を含む他の形（`&& echo $?` 等）・他の OS は試していない。
**書く主張はこの範囲に留める**（「`$?` を含むと必ず拒否される」とは書かない）。

### 生成物

該当判定: `skill-metrics.py` の生成ブロック（設計 §8.2）が `SKILL.md` の行数に依存する → **該当**。
`python3 scripts/skill-metrics.py` で再生成し `--check` が緑であること。図の書き出しは無関係（drawio を触らない）。

## 4. 未解決の判断

なし。

## 5. 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/222-pr-preconditions-guard`、worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-222`、
  起点 `6071e01`、base 参照 `origin/main` → `6071e01e9c1855e3a3c1db053d3e1a53cda26020`
- 関門: 未着手
- 交絡を潰した手順: `;` と `$?` を分けた（`; echo done` が通る）。陽性対照（素の形が通る）を同じセッションで取った

## 6. 既知の限界・決着済みの論点

- 拒否の境界（`$?` を含むどの形が拒否されるか）は特徴づけない——guard-rejections.md の方針（#112）どおり。規定は「足さない」だけ
