# Issue #218: spec-loop 段 3 — feasibility と proposal スキル

親: #214（段 3）。前提: 段 2（#217 / PR #257、マージ済み）。

## 変更範囲

触る:

- `plugins/spec-loop/skills/feasibility/` — 新規。見積り・スケジュールの更新、費用付きの質問の起票
- `plugins/spec-loop/skills/proposal/` — 新規。関門の照合と提案書の生成
- `plugins/spec-loop/agents/estimate-checker.md` — 新規。見積りの検証役（許可リスト・書き込みツールなし・`model` を書かない）
- `plugins/spec-loop/references/feasibility-csv.md` — 新規。`schedule.csv` と `estimate.csv` の列の原本
- `plugins/spec-loop/references/tree.md` — `estimate.csv` と提案書の出力先を足す
- `plugins/spec-loop/references/signoff-tags.md` — 照合スクリプトを指す・「最新」の決め方
- `plugins/spec-loop/references/qa-csv.md` — 起票元 `実現性・コスト` の行は `費用への影響` を空にしない
- `plugins/spec-loop/scripts/*.py` — 新規 4 本（`check-feasibility-csv.py`・`schedule-to-gantt.py`・`check-signoff.py`・`build-proposal.py`）と `check-qa-csv.py` の上記の決まり
- `scripts/test-*.py` — 上の回帰テスト（新規と `test-check-qa-csv.py`）
- `scripts/check-all.py` — 新しいテストの登録
- `.github/workflows/plugins.yml` — 同上
- `plugins/spec-loop/README.md` — スキル・スクリプトの一覧
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版 0.4.0 と description
- `.claude-plugin/marketplace.json` — 同上
- `plugins/spec-loop/skills/req-loop/SKILL.md` — 版のバナーだけ
- `plugins/spec-loop/skills/spec-review/SKILL.md` — 版のバナーだけ
- `docs/plugins/index.md` — spec-loop の節
- `CLAUDE.md` — プロジェクト構成
- `docs/plans/issue-218.md` — この計画

触らない:

- `plugins/dev-loop/` — 段 4 の差し戻し規定はこの段ではない
- `scaffold` スキル — 段 4
- 振る舞いの Eval（`evals/`）— #214 の「決めていないこと」
- `check-plugin-versions.py` — 新しい agent は既存の `agents/` 検査がそのまま見る（足さない）

## 決めたこと

1. **照合は「最新の 2 つのタグ」**——`req-signoff-v<n>`・`budget-signoff-v<n>` のうち `<n>` が数として最大のもの
   （`v10` > `v9`）。引数で明示もできる。**どちらかの時点で `docs/shared/` が空なら判定しない（2）**——
   `git diff --quiet` は両方空でも 0 を返すので、それを「一致」と読まない。
2. **提案書は承認したタグの時点の中身から作る**——`docs/shared/` は `req-signoff`、`docs/feasibility/` は
   `budget-signoff` の時点のものを `git show` で読む。作業ツリーで承認後に直した中身が提案書に混ざらない。
   手書き部分（`docs/proposal/`）だけは作業ツリーから読む（承認の対象ではない）。
3. **照合が通らなければ生成しない、を生成スクリプトの中で担保する**——`build-proposal.py` が自分で照合を呼び、
   0 でなければ 1 バイトも書かない。**スキルの散文に頼らない。**
4. **ガントチャートは SVG**——標準ライブラリだけで書け、MkDocs でも提案書でもそのまま見られる。
   同じ `schedule.csv` から同じバイトを出す（時刻・乱数を使わない）。
5. **見積りは `estimate.csv` に置く**——提案書の費用の表を生成するのに機械で読める形が要る。
   列は `references/feasibility-csv.md` に置く。
6. **費用付きの質問は `費用への影響` を空にしない**——起票元 `実現性・コスト` の行だけ。`check-qa-csv.py` が見る。

## デプロイ経路

main へのマージで GitHub Pages（`docs/plugins/index.md`）が更新される。プラグインはカタログ経由（`plugin update`）。

## 受入基準（不変条件 × 経路）

| # | 不変条件 | 破りうる経路 | 守り方 |
| --- | --- | --- | --- |
| A | `docs/shared/` が食い違うタグの組で照合が非ゼロ | (a) ファイルの中身の違い (b) ファイルの追加・削除 (c) 片方の時点に `docs/shared/` が無い (d) 両方に無い (e) タグが無い・片方だけ (f) 「最新」を文字列順で選ぶ（v10 < v9） (g) 規約外の名前（`req-signoff-v3-fix`）を最新と読む (h) 指定したタグが無い (i) git でない | `check-signoff.py`。(c)(d)(e)(h)(i) は 2、(a)(b) は 1。テストで実際の git リポジトリとタグを作って当てる。変異テストで各分岐が赤になること |
| B | 照合が通らないとき提案書を生成しない | (a) 生成スクリプトが照合を呼ばない (b) 照合の 2 を通す (c) 出力先に古い提案書が残る (d) スキルが手で提案書を書く | (a)(b)(c) `build-proposal.py` の中で照合し、通らなければ書かず、既存の出力を消す——テスト＋変異。(d) スキルの「守ること」に書く（未証明: 散文） |
| C | ガントチャートが `schedule.csv` から決定論的に出る | (a) 2 回の生成でバイトが違う (b) 行の順・日付の範囲で結果が変わるはずが変わらない (c) 決まりに反する `schedule.csv`（日付・前提）から黙って描く | `schedule-to-gantt.py`。2 回生成してバイト一致・別の CSV で違うことの陽性対照。不正な CSV は 1 で書かない |
| D | 予算責任者の合意・決裁者の承認をスキルが推測で埋めない | (a) スキルがタグを付ける (b) 合意を Q&A 表の回答に書く (c) 提案書に「承認済み」と書く | 両スキルの「守ること」に書く。生成スクリプトは承認の欄を持たない（タグと SHA だけ）（**未証明**: スキルの振る舞いは Eval が無い） |
| E | データの決まりは `references/` の 1 箇所。スクリプトの定数はその写しで、テストが突き合わせる | 列の写しがずれる | 各テストが `references/feasibility-csv.md`・`qa-csv.md` と定数を突き合わせる |
| F | 見積りの検証役が書き込みツールを持たない | 定義の `tools:`・`model:` | 既存の `check-plugin-versions.py` の `agents/` 検査（全プラグイン） |
| G | 版の 3 箇所一致・description の JSON 2 箇所一致・指し先の実在 | 既存の歯止め | `check-all.py` |

### 検証で証明できるもの

A・B(a)(b)(c)・C・E・F・G はスクリプトとテストで実際に走らせて確かめる。

### 未証明（この環境では証明できない）

- B(d)・D: スキル（LLM）の振る舞い。散文の規定だけで、Eval を置いていない（#214 の未決定）。人間レビューへ。
- 生成した SVG・提案書の見た目（ブラウザ・MkDocs で開いたときの表示）。整形式の XML であることまでは見る。

### 生成物

- `skill-metrics.py` の生成ブロックは dev-loop の `SKILL.md` だけが対象——**dev-loop を触らないので該当なし**（`--check` は check-all で回る）。
- 図（drawio）は触らない——該当なし。

## 周の大きさ

同じことを述べている箇所: 列の決まり（references 1 + スクリプト定数 1、テストで突き合わせ）、
スキルの説明（frontmatter 2 + JSON 2 + README + 公開ページ + CLAUDE.md）＝ 約 7 箇所。
分けない理由: 段 3 の 2 スキルは同じ正本ツリーと照合を共有し、Issue が 1 段として起票している。

## 未解決・確認待ち

- なし（着手時）

## 関門の進捗（再開点）

- 周の在り処: ブランチ `issue/218-feasibility-proposal`、worktree
  `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-218`、
  起点 `4bd82d6`、base 参照 `origin/main` → `4bd82d610ca5987bfd1909051bcb785fe807506c`
- 実装: 完了（手順 4）。**訂正**: 「`check-all.py` 39/39 緑」は誤りだった——再開後に回すと
  `check-description-sync.py` が落ちた（JSON と新しい 2 スキルの frontmatter が変わり、req-loop・spec-review の
  frontmatter は変わらない）。#217（`b12730c`）と同じ形なので、指摘対応のコミットに `Skip-description-sync:` を書いた
- 関門 1 パス目: **通した**。Verifier（`dev-loop:dev-loop-verifier`・sonnet）**反証 1 件**／
  `/code-review`（high）**指摘 9 件**。採否は下の表——直す 2 件（V1・CR2）、残課題 8 件
- 指摘対応（1 パス目）: V1・CR2 を直した。変異を 1 本ずつ足し、どちらも変異前の挙動（トレースバック・循環を通す）を
  再現して赤になることを確かめた（`test-build-proposal.py` 試料 14・変異 11、`test-check-feasibility-csv.py` 試料 39・変異 24）
- **次は手順 5 の当て直し（Verifier 2 パス目）と `/code-review` 2 パス目**——両方が残っている
- 差し戻し: 1 パス目の反証 1 件で手順 4 へ（V1）
- 交絡: 実験は変異テストだけ。各変異に陽性対照（変異前に緑）があり、届いていない変異は数で弾く。
  **殺せなかった変異は外して「殺せる」と主張していない**（上の表）
- 割り目（手順 4）: 提案した（AskUserQuestion）→ **「ここで割る」を選択**。実装コミット `a8af76c`

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| `check-signoff.py` の「`git diff` 自体が失敗する」分岐に変異を置いていない | 採らなかった（変異なし） | 手前の検査（コミットを指すか・`docs/shared/` を読めるか）を通った後に、この分岐へ届く試料を作れなかった。**殺せると主張しない**（テストのコメントに書いた） |
| `test-check-feasibility-csv.py` の「日付の書式を見ない」変異は Python 3.11 以降でしか殺せない | 採った（3.11 以降を前提にする） | 3.10 の `date.fromisoformat` は基本形式（`20261102`）も拒むので、書式の検査を外しても結果が変わらない。CI（ubuntu-latest）は 3.12。**本体は 3.10 でも正しく動く**——3.10 で赤になるのはテストの変異 1 件だけ |
| 提案書を作業ツリーではなくタグの時点の中身から作る | 採った | 承認後の手直しが提案書に混ざるのを、照合を足すのではなく読む先を変えることで閉じる（決めたこと 2） |
| 照合の対象を `docs/shared/` に限る（`requirements/`・`feasibility/` は比べない） | 採った | 2 つの承認が共通に見るのは `shared/` だけ（`references/tree.md`）。提案書は各タグの時点の中身を読むので、作業ツリーとの比較は要らない |
| 承認タグを付け直されたら検出できない | 採らなかった（守らない） | 付け直した後の状態しか見えない。`check-signoff.py` の docstring に「守らないもの」として書いた |

### 関門 1 パス目の指摘と採否

| # | 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- | --- |
| V1 | `build-proposal.py` の `main` が古い出力を消す前に `try` の外で `git` を呼ぶ。`git` を起動できないとトレースバックで 1、古い提案書が残る | 示せる（Verifier: `PATH=/nonexistent` で exit 1・Traceback・STALE が残る。変異「git を起動できないと落ちる」で同じ挙動を再現） | B(c)・終了コードの規約（2） | **直す**（直した） |
| CR1 | `--req`/`--budget` で古いタグの組を明示すると「最新の 2 つ」の関門を迂回できる | 示せる（`--req req-signoff-v1 --budget budget-signoff-v1` で 0、v2 があるのに作る） | 無し——明示は決めたこと 1 で意図した機能。A は「食い違う組で非ゼロ」で、v1/v1 は食い違わない | 残課題（**人間に判断を仰ぐ**: 明示した古い組を許すか・警告するか） |
| CR2 | 同じ日の工程どうしの `前提` の循環が通る | 示せる（`T-001…,T-002` と `T-002…,T-001` が exit 0。変異「循環を見ない」で再現） | C(c)（`前提` は「先に終わっている必要がある」——循環は満たせない） | **直す**（直した。`references/feasibility-csv.md` に循環の決まりを足した） |
| CR3 | 「最新」は手元のタグだけから選ぶ（fetch しない） | 示せない（起こりうる筋書き） | 無し | 残課題 |
| CR4 | `No` が重複すると `前提` の照合が後の行で行われ、別の違反が隠れる | 示せない（重複自体は報告され 1 で書かない） | 無し（C(c) は守られる） | 残課題 |
| CR5 | 手書き部分（`docs/proposal/*.md`）の下書き・「承認済み」を検査せずに載せる | 示せない（筋書き） | D(c) に触れるが D は未証明（スキルの振る舞い） | 残課題（**人間レビューへ**） |
| CR6 | `--out` の隣の `gantt.svg` を消す——別の出力の `gantt.svg` を消しうる | 示せない（筋書き） | 無し | 残課題 |
| CR7 | `read_qa` が一時ファイル経由で再解析（Windows で改行が変わりうる） | 示せない | 無し | 残課題 |
| CR8 | 表のセルの HTML・画像記法をエスケープしない | 示せない | 無し | 残課題 |
| CR9 | 開始＝終了の工程をすべて節目の色で描く（1 日の作業と区別しない） | 示せる（挙動として） | 無し（C は決定性） | 残課題 |
