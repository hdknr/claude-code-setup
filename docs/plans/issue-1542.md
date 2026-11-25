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
- `scripts/test-scaffold-screens.py` — 回帰テスト
- `scripts/test-build-mock.py` — 回帰テスト
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版
- `plugins/spec-loop/skills/*/SKILL.md` — 版（2 行）
- `plugins/screen-spec/.claude-plugin/plugin.json` — 版
- `plugins/screen-spec/skills/*/SKILL.md` — 版（2 行）
- `.claude-plugin/marketplace.json` — 版
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

- 未証明: 実際の MkDocs（`mkdocs build`）で `exclude_docs` が CSV・JS を落とすこと——**当初は「CI に MkDocs の組が無い」として未証明に置いたが、Verifier 1 パス目（R1）に反証された**。手元に MkDocs 1.6.1 があり、
  雛形の 2 パターンだけの設定で `docs/design/sources.csv`・`docs/screen-spec/renderers/*.js` は `site/` に出ず、`docs/foo/t.txt`（対照）は出ることを著者も走らせて確かめた（scratchpad の最小の設定。MkDocs 1.6.1・2026-11-25）。
  CI に MkDocs の組が無いので、実効は CI では当てていない（雛形の文面を見るテストも無い——採否の表の R1・CR3）。
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

## 既知の限界・決着済みの論点

採否の表（Verifier と `/code-review` の 1 パス目。既定の線: 「示せる」かつ「この周の受入基準を破る」行だけ直す）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| R1（V）未証明の分類が誤り・「テストは雛形の文面までを見る」が偽 | 示せる（MkDocs 1.6.1 の実測・scripts/ の grep）。計画の記述は上のとおり直した | 無し | 残課題（計画の文は直した。雛形を見るテストは足さない） |
| R2（V・項目 12）`差分テスト: なし` だが受入基準 2 は「変えない」 | 示せる（Verifier が新旧を同じ試料に当て、根の直下・置かない形でバイト一致、docs の形は差が出る陽性対照）。build-mock の `good` は旧との同一性を見ない | 無し（基準 2 は Verifier の実験で満たす） | 残課題 |
| R3（V）docs の下の描き方を未コミットで直すと表の出どころが「docs に未コミットの変更あり」になる | 示せる（Verifier の e1） | 無し | 残課題（文言どおり正しい。記録だけ） |
| R4（V）大文字小文字を区別しない FS で `docs/Design` が scaffold・生成器に読まれ MkDocs には公開される | 示せる（Verifier の e1。scaffold は未実行） | 無し | 残課題（記録だけ） |
| R5＝CR6（V・CR）mock.md が `screen-spec/` を足すと書くが雛形は `/screen-spec/renderers/`・指し先の節に exclude_docs が無い | 示せる（行の突き合わせ） | 無し（基準 7 は表と定数で、文は対象外） | 残課題（文言。記録だけ） |
| CR1 req-loop・spec-review・scaffold の SKILL.md と spec-scope.md の「正本の根に `design/sources.csv` があれば」が `docs/design/sources.csv` で発火しない | 示せる（行の読み: req-loop:382・spec-review:160・455・scaffold:165・spec-scope:131-136） | 無し | 残課題（利用者に見える誤りとして直す候補に振る） |
| CR2 exclude_docs が MkDocs の既定（`.*`・`/templates/`）を上書きする | **示せない**——MkDocs 1.6.1 で `.DS_Store`・`.hid/`・`templates/` は雛形と同じ設定でも `site/` に出なかった | 無し | 残課題（捨てる） |
| CR3 雛形の exclude_docs を見るテストが無い | 示せる（grep） | 無し | 残課題（試料の穴。記録だけ） |
| CR4 両方に在る scaffold の末尾の 1 行が根のパスだけを名指しする | 示せる（コードの読み。出力は未実行） | 無し（基準 4 は 1 で止まること。1 行目は両方を名指す） | 残課題（文言。記録だけ） |
| CR5 docs の下の違反の `--dry-run`・`--upto` を見る試料が無い | 示せる（Verifier の e2 が挙動を確認。試料は無い） | 無し | 残課題（試料の穴。記録だけ） |

振り分け（`references/found-lines.md`。PR コメントにも書く）: 直す（台帳に足して直す）は CR1 の 1 件。記録だけは R1・R2・R3・R4・R5＝CR6・CR3・CR4・CR5。捨てるは CR2。

受入基準の判定: 1〜7 すべて満たす（Verifier が各行を走らせ・読んで確かめた。7 は写しの突き合わせが緑）。

- 周の外での決め: 置き場所の決め方は推奨（A 案）で決めた。確認の Issue は親が立てる。

## 関門の進捗（再開点）

- 実装: 済（`78e897ee`）。計画の表化（`1645886e`）
- PR: #1545（先端はマージの直前に `check-gates.py` で照合）
- 割り目: 訊かない（cruise の周）。割らない（実装後・2 パス目の前とも）。
- 関門 1 パス目（HEAD `1645886e3435ae03bc820ca4bb1174da6b59dd81` を渡した。base `a50e080fb1e3715c0ae3e0aa51ac238ee1c2ec32`）:
  - Verifier（`dev-loop:dev-loop-verifier`・opus。実装は sonnet）: 反証 5 件（R1〜R5）。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/6afc4e45-0d5a-49c7-a3a4-03fd099dd38c/scratchpad/gate-1542-verifier-1-20261125T022713Z.md`
  - `/code-review`（high）: 指摘 6 件（CR1〜CR6）。報告のファイル `/private/tmp/claude-503/-Users-hdknr-Projects-hdknr-claude-code-setup/6afc4e45-0d5a-49c7-a3a4-03fd099dd38c/scratchpad/gate-1542-code-review-1-20261125T023820Z.md`
  - 1 パス目の指摘対応の起点: `1645886e3435ae03bc820ca4bb1174da6b59dd81`。「直す」の行が 0 件（下の採否の表）なので成果物の差分は 0 行。2 パス目: 該当なし。狭いパス: 該当なし。
- 外部レビュー: 該当なし（`.claude/dev-loop.md` に `外部レビュー:` の宣言が無い。PR #1545。`external-reviews.py` は 3）
- 交絡を潰した手順: 実験は MkDocs の `exclude_docs` の実効だけ（対照に `docs/foo/t.txt` が公開されること・`.DS_Store`・`templates/` が出ないことを同じ設定で見た）。それ以外は実験なし。

- この周の起票: 0 件（仕様の穴は推奨で決めて起票の線だが、確認の Issue は親が立てる。周の中では起票しない）

## 関門の記録

```dev-loop-gates
周の base: a50e080fb1e3715c0ae3e0aa51ac238ee1c2ec32
関門: Verifier 1 1645886e3435ae03bc820ca4bb1174da6b59dd81 反証=5
関門: /code-review 1 1645886e3435ae03bc820ca4bb1174da6b59dd81 指摘=6
関門: 2 パス目 該当なし 1645886e3435ae03bc820ca4bb1174da6b59dd81
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
受入基準: 5 満たす
受入基準: 6 満たす
受入基準: 7 満たす
マージの反映: ドキュメントとプラグインの配布
```
