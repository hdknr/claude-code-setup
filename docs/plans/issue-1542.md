# Issue #1542 — 版の外のファイル（design/sources.csv・screen-spec/renderers/）を docs/ の下にも置けるようにする

<!-- dev-loop: 子 #1542 -->

不在の周（`/dev-loop:cruise 1540 --absent` の起動。2026-11-25）。親 Issue #1540 の子。利用者が台帳に追加を指示した周。
線（台帳で確かめ済み）: 直す線=既定／仕様の穴=推奨で決めて起票／マージ=関門を通ればマージ／周の途中の課題=台帳に足して直す／マージ前の判断=推奨で決めて起票（後退・未達を含む）。出所は同起動。

## 周の在り処

- ブランチ: `issue/1542-design-sources-under-docs`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1542`
- 切った元の参照: `origin/main`（`refs/remotes/origin/HEAD`）
- 起点コミット: `a50e080f`
- base: `a50e080fb1e3715c0ae3e0aa51ac238ee1c2ec32`
- 直す線: 既定（出所: cruise の台帳の確かめた線）

## 変更範囲

触る:
- `plugins/spec-loop/scripts/scaffold.py` — `design/sources.csv` を `docs/design/sources.csv` にも置ける
- `plugins/spec-loop/references/tree.md` — 「デザインの正本の参照」の「`docs/` の外」の記述
- `plugins/spec-loop/references/handoff-issue.md` — 本文の段落のパス
- `plugins/spec-loop/templates/mkdocs/mkdocs.yml` — `exclude_docs`
- `plugins/screen-spec/scripts/build-mock.py` — `screen-spec/renderers/` を `docs/` の下にも置ける
- `plugins/screen-spec/references/mock.md` — 描き方の差し替えの置き場所
- `scripts/test-scaffold-screens.py`・`scripts/test-build-mock.py` — 回帰テスト
- `plugins/spec-loop/.claude-plugin/plugin.json`・`plugins/spec-loop/skills/*/SKILL.md`・`plugins/screen-spec/.claude-plugin/plugin.json`・`plugins/screen-spec/skills/*/SKILL.md`・`.claude-plugin/marketplace.json` — 版
- `docs/plans/issue-1542.md` — この計画

触らない:
- dev-loop（`references/spec-gap.md` の「正本の根の `design/sources.csv`」の言い回しは、本文の段落が読んだ場所を名指しするので支障なし。残課題に書く）
- 設定の表にパスを書く方式（下の穴の決め）
- MkDocs の雛形を既存の正本へ写し直す仕組み（`init-mkdocs.py` は在るファイルを変えない決まりのまま）

## 設計（仕様の穴の決め）

穴: 置き場所の決め方（Issue の「直したいこと」3 つ目は例を 2 つ挙げ、どちらかは決めていない）と、MkDocs で `docs/` の下に置いたときの公開の扱い（4 つ目）。

| 選択肢 | 内容 | 判断 |
| --- | --- | --- |
| A. 探す順を固定 | `docs/<同じ相対パス>` を根の直下より先に探す。片方だけに在ればそれ、両方に在れば止める | **推奨（採用）** |
| B. 設定の表にパスを書く | screen-spec の `settings.csv` のような表に置き場所を書く | 採らない。spec-loop には設定の表が無く、screen-spec の `settings.csv` は版の中（版ごとに変わりうる）。道具ごとに新しい設定の面が増える |
| C. docs の下だけにする | 根の直下をやめる | 採らない。完了条件「根の直下の既存の正本は何も変えずに動く」に反する |

- 両方に在るときは止める（1）。優先順で黙って片方を選ぶと、もう一方が無視されたまま残る（`docs/` に移して根の写しを消し忘れた形）。
- MkDocs: 雛形の `mkdocs.yml` に `exclude_docs`（`/design/sources.csv`・`/screen-spec/renderers/`）を入れる。推奨は「公開しない」（Figma の URL・案件の JS は道具が読む入力で読み物ではない。既に公開される版の CSV とは性格が違う）。既存の正本は `mkdocs.yml` を写し直さないので、tree.md に「自分で足す」と書く。

## 受入基準（不変条件 × 破りうる経路）

| 番号 | 不変条件 | 破りうる経路（入口） |
| --- | --- | --- |
| 1 | 2 つのファイルを `docs/` の下に置いた正本で、scaffold が本文にデザインの正本の参照を載せ（段落のパスは `docs/design/sources.csv`）、生成器が描き方を埋め込む | scaffold の書く生成・`--dry-run`、生成器の CLI、MkDocs フック経由の生成（`build` を共有） |
| 2 | 根の直下に置いた既存の正本は何も変わらない（本文・埋め込み・出どころの印が同じバイト） | 既存の試料（`test-scaffold-screens.py` の `case_design_listed`、`test-build-mock.py` の `good`）が無変更で緑 |
| 3 | 版のディレクトリの中に置いたものは今までどおり止める（`renderers` は版の中なら 1） | `renderers-in-version`・`renderers-in-later-version`（無変更）・`--upto` で前の版だけ見る形 |
| 4 | 両方に在れば止める（scaffold は 1・何も作らない／`--dry-run` も 1、生成器は 1・何も書かない） | scaffold の書く生成・`--dry-run`、生成器 |
| 5 | 決まりに反する `docs/design/sources.csv` は、その場所を名指しして 1 | scaffold の書く生成・`--dry-run` |
| 6 | `--check`・`--red-check`（本文を作らない）と `--upto` で前の版の時点を見るときは、今までどおり読まない | scaffold の各モード |
| 7 | 決まりの写し（`references/mock.md` の表と定数）が崩れない | `test-build-mock.py` の写しの突き合わせ |

### 未証明・BLOCKED

- 未証明: 実際の MkDocs（`mkdocs build`）で `exclude_docs` が CSV・JS を落とすこと。CI に MkDocs の組が無い。テストは雛形の文面までを見る。
- BLOCKED: なし。

### 生成物

- 生成物なし（このリポジトリの図・スナップショットは触らない）。`SKILL.md` の測定値は `skill-metrics.py --check` で確認（dev-loop の SKILL.md は触らない）。

### 規定の数と分けない理由

- 同じ規範（置き場所の決め方）の複製: scaffold.py の docstring・tree.md・handoff-issue.md・mock.md・build-mock.py の docstring・2 つのテスト = 6 箇所。分けない理由: 1 つの決め（探す順）を 2 つのプラグインに同時に入れる周で、片方だけ直すと食い違うため。
- プロパティテスト: なし（入力空間が小さく、置き場所の組み合わせ 4 通りを例で網羅）。
- 差分テスト: なし（振る舞いを変えない受入基準は 2 だが、既存の試料を無変更で通すことで証明する）。
- 依存の追加・更新: なし。
- 仕様の振る舞い: 変えない（このリポジトリは spec-loop の正本ではない）。
- 形式検査のモデル: なし。

## 関門の進捗（再開点）

- 実装: 済（コミット前）
- 割り目: 訊かない（cruise の周）。割らない。

- この周の起票: 0 件（仕様の穴は推奨で決めて起票の線だが、確認の Issue は親が立てる。周の中では起票しない）
