# Issue #608 — docs/plugins に spec-loop の解説ページを足す（Red テストと `--red-check` を含む）

spec-loop の公開ドキュメントは `docs/plugins/index.md` の「## spec-loop」節しかなく、Red テストと `--red-check` は公開ページから辿れない。
`docs/plugins/spec-loop.md` を足し、ナビゲーションと一覧の節からリンクする。

**不在の周**である——出所は `/dev-loop:cruise 793 --absent` の起動（2026-11-03）。親からサブエージェントとして委ねられた。
台帳 `issue-793` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`（マージは親がする）・`周の途中の課題 = 外に出す`
（出所: 利用者の確認（起動時・親 Issue #793 の cruise: の行・2026-11-03T03:56:17Z、配布を見せて確かめた））。台帳は書かない（親が書く）。

直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-793`））。
版の上げ方: **上げない**——`plugins/` を 1 ファイルも触らない（`docs/` と `mkdocs.yml` だけ）ので、CLAUDE.md「プラグインの更新」の対象外。
`check-version-bump.py` が落とすのは `plugins/<name>/` の中身を変えた差分だけ。

重い検査（`check-all.py`・`mkdocs build`）は順番待ち越しに走らせる
（`/Users/hdknr/.claude/plugins/cache/claude-code-setup/dev-loop/1.74.1/skills/cruise/scripts/run-serial.py -- <コマンド>`。`references/parallel.md`）。

## 変更範囲

触る:

- `docs/plugins/spec-loop.md` — 新しい解説ページ
- `docs/plugins/index.md` — 「## spec-loop」節からのリンク、新しいページへ寄せた記述の整理
- `mkdocs.yml` — 「プラグイン」のナビゲーションに 1 行
- `docs/plans/issue-608.md` — この計画ファイル

触らない:

- `plugins/spec-loop/` の中（README・`references/`・`SKILL.md`・スクリプト）——原本は変えない。README から新しいページへのリンクも足さない（版を上げる周になるので、Issue の範囲の外）
- `docs/plugins/dev-loop-*.md`（dev-loop の側の解説。`spec-gap.md` はリンクで指すだけ）
- `docs/plans/issue-219.md` などの過去の計画ファイル（リンクで指すだけ）

### 同じことを述べている箇所の数

新しいページが述べることのうち、既に別の場所にあるもの:

1. 各スキルが止まる点——`index.md` の各スキルの節（と各 `SKILL.md`「止まる」）。新しいページは流れの表に 1 行ずつ置き、`index.md` の各節を詳しい説明として指す
2. Issue の本文が指紋と sha256 を持つこと——`index.md` の `scaffold` の節の箇条書き。**新しいページへ寄せ、`index.md` からは指すだけにする**
3. Red テスト・`--red-check`・Issue の本文の形——原本は `scaffold.py` の docstring・`references/spec-ir.md`・`references/handoff-issue.md`。ページは要点と指し先だけ

複製は 3 種。分けない理由: 1 は流れ（順序と止まる点）を一望するための表で、`index.md` のスキル別の説明とは目的が違う。2 は寄せて 1 箇所にする。3 は原本を指す。

## 乗るデプロイ経路

main へのマージで GitHub Pages（`docs.yml`）に公開される（`docs/` の変更がそのままデプロイ）。プラグインの配布は無い（`plugins/` を触らない）。マージは親がする。

## verify の受入基準

| # | 不変条件 | 破りうる経路 | 確かめ方 |
| --- | --- | --- | --- |
| C1 | 新しいページがあり、ナビゲーションと `index.md` の「## spec-loop」節から辿れる | `mkdocs.yml` の nav・`index.md` のリンク（相対パス）・ビルドした site の `plugins/spec-loop/index.html` | ビルドした site にページがあり、nav と `plugins/index.html` に `spec-loop/` へのリンクがある |
| C2 | ページだけで、Red テストが何か・どこで作られるか・何が赤／緑の期待か・`--red-check` が何を見るかが分かり、判定の本体（`scaffold.py` の docstring）へリンクで辿れる | ページの「Red テスト」「`--red-check`」の節 | 節を読む。`scaffold.py` の GitHub の URL がページにある |
| C3 | ページの事実の主張が原本と食い違わない（Red テストの形・ケースとテストの対応・受入基準・`--red-check` の判定・止まる点・データを書く／読むスキル・指紋と sha256） | ページの各主張 × 原本（`scaffold.py`（docstring と生成するテストの雛形）・`spec-ir.md`・`handoff-issue.md`・`tree.md`・各 `SKILL.md`・dev-loop の `spec-gap.md`） | 主張ごとに原本の行と突き合わせる |
| C4 | 5 本のスキルの流れと、各スキルが止まる点（回答待ち・合意待ち・承認待ち・登録の確認）が分かる | ページの流れの図と表 | 表の 5 行に止まる点がある。C3 と同じく各 `SKILL.md`「止まる」と突き合わせる |
| C5 | 決まりの列挙を書き写さず、原本（`references/`・`SKILL.md`・docstring）を「正とする」で指す。`index.md` と重複する記述は一方に寄せる | ページの全節・`index.md` の「## spec-loop」節 | ページに列挙（判定の表・終了コードの一覧・列の一覧・印の一覧）の写しが無い。指紋と sha256 の記述が `index.md` から新しいページへ移っている |
| C6 | ページの指し先が解決する | 相対リンク（`mkdocs build --strict` が見る）・GitHub の URL（main にそのパスがあるか）・公開サイトの絶対 URL（`check-site-links.py`） | `mkdocs build --strict` が通る。GitHub の URL のパスがリポジトリに実在する（スクリプトで数える） |
| C7 | 歯止めを割らない | `check-duplicate-counts.py`（`docs/` も走査）・`check-site-links.py`・`check-plan-counts.py`（この計画ファイル）ほか | `python3 scripts/check-all.py`（順番待ち越し）が緑、PR の CI が緑 |

必須要件の掛け算: 受入基準を Verifier・`/code-review` の両方に、1 パス目・2 パス目の両方で渡す（4 つの受け渡し。2 パス目が「該当なし」なら初回の 2 つ）。

### 未証明

- **ページを読んだ人が実際に理解できるか**（C2・C4 の「分かる」）は、書いた側と関門の読解でしか確かめられない。人間のレビューに回す。
- **公開サイトの描画**（Material テーマ・mermaid の図が描かれるか）は、ローカルのビルドの HTML までしか見ない。mermaid はブラウザの JavaScript で描かれるので、ビルドでは図にならない。

### 生成物

該当の判定: 図の書き出し（`diagrams/`）は触らない。`SKILL.md` の測定値（`skill-metrics.py`）は dev-loop の `SKILL.md` だけ。公開サイトはビルドの出力で commit しない（CI がビルドする）。**生成物なし**。

## 未解決の判断・確認待ち

なし。

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/608-spec-loop-docs-page`・worktree `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-608`・
  起点 `412ca8f7`（origin/main。`prepare-worktree.sh` の出力）・base: 参照 `origin/main` → `412ca8f78ff7177110e8250dcce4ebcbcf0d624a`
- 割り目（手順 4）: 割らない（不在の cruise）。このまま続ける。

## 既知の限界・決着済みの論点

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| （論点）流れの順序は `req-loop` → `spec-review` → `feasibility` → `proposal` → `scaffold` と書くが、`scaffold` が入力で確かめるのは仕様レビューを抜けたこと（条件 1 と直近の `spec-review` の報告）で、提案書の承認は確かめない | — | — | 採った: ページにそう書く（`scaffold` の `SKILL.md` 手順 1。サインオフの言及は「付けない」の 1 行だけ） |
| （論点）`plugins/spec-loop/README.md` から新しいページへのリンクを足さない | — | — | 採った: プラグインを触ると版を上げる周になり、Issue の「やること」に無い |
