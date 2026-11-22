# Issue #1465 — CI: plugins.yml の spec-loop・spec-loop-generate ジョブを分割して run 全体の律速を下げる

利用者が居る周（2026-11-22、#1463 の周で利用者が起票を承認し、続けて回す）。従う版は dev-loop 2.20.1（キャッシュ）。

- 直す線: **既定**（出所: `.claude/dev-loop.md` に `直す線:` の行が無い。#1463 の周と同じく既定で始め、利用者の指示があれば書き換える）
- 版の上げ方: **上げない**——`plugins/` を触らない
- PR は `Fixes #1465`
- 依存の追加・更新: なし
- 差分テスト: なし（振る舞いを変えないのは CI の構成だけで、旧い実装を正解にする対象のコードが無い。不変条件 1 のステップの全キーの多重集合の比較で代える）
- プロパティテスト: なし（入力の空間が広い不変条件が無い）

## 周の在り処

- ブランチ: `issue/1465-split-spec-loop-ci-jobs`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-1465`
- 起点コミット: `266274d7`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）を解決した `266274d73504734eb84741ee4df7465edea6c96c`

## 変更範囲

触る:
- `.github/workflows/plugins.yml` — `spec-loop`（24 ステップ）と `spec-loop-generate`（19 ステップ）のステップを、本文を変えずに 5 つのジョブへ振り分ける
- `docs/plans/issue-1465.md` — この計画

触らない:
- テストの中身——Issue の範囲外
- `spec-loop-autopilot-loop`・`cruise-loops` など 1 本で重いジョブ——分割できない（1 ステップ）。分割後はこれが律速になる
- `scripts/check-all.py`・`scripts/test-check-all.py`——`run:` の行を 1 行ずつ見る検査なので、行を保てば変えなくてよい
- `CLAUDE.md`——ジョブ名を指す記述は無い（`git grep -l spec-loop-generate` は `plugins.yml` のほかに `scripts/test-scaffold.py` の #1361 当時の注記と `docs/plans/` の 8 本に当たるが、`CLAUDE.md` には 0 件。1 パス目の `/code-review` の指摘で訂正）。「CI の 1 往復（約 6 分）」の古さは #1463 の残課題で、この周では触らない

複製の数（同じことを述べている箇所）: ジョブへの振り分けを述べるのは `plugins.yml` の 5 つのジョブの見出しコメントと、この計画の下の表の、計 **6 箇所**。1 つの YAML の隣り合う位置なので分けない。

### ジョブと実測の重さ（run 44977757205 と 44982486405 のステップの秒数から見積もる）

| ジョブ | ステップ | 見積り（2 つの run） |
| --- | --- | --- |
| `spec-loop` | PPTX・サインオフ・提案書・PPTX のデザインと描画・版の重ね合わせ（casefold を含む）・MkDocs の雛形 8 | 318 / 291 秒 |
| `spec-loop-tools` | 作り直しの範囲と量・取り込み・レビュー会・親 Issue の一覧・緑のケース・見積もり・版の差分と凍結・autopilot の台帳と点検・形式検査の道具 16 | 303 / 284 秒 |
| `spec-loop-generate` | Red テストと Issue の本文の生成・scaffold の画面の表の参考資料 2 | 229 / 291 秒 |
| `spec-loop-render` | ガントチャート・図の書き出し・モデルの走らせ直しと状態遷移図・Q&A 表・抜ける条件・見積りの表 7 | 236 / 281 秒 |
| `spec-loop-tables` | 設計書の成果物・基盤要件・指摘の表・記録の数え直し・機能ごとの数え方・screen-spec の 5 つ 10 | 138 / 179 秒 |

分割前は `spec-loop` 627 / 583 秒・`spec-loop-generate` 608 / 757 秒。分割後の run 全体の律速は `spec-loop-autopilot-loop`（430 / 627 秒。1 ステップ）になる見込み。

## デプロイ経路

`CI 定義`——main へのマージで次の PR・push から効く。本番（GitHub Pages・カタログ）へは何も配布しない（反映経路なし）。

## verify の受入基準

不変条件と、それを破りうる経路:

| # | 不変条件 | 経路と守り方 |
| --- | --- | --- |
| 1 | 分割前に走っていたステップが、分割後もすべて同じキーと値（name・if・run・env など）で 1 度ずつ走る | 経路: (a) 振り分けで落ちる、(b) 重複する、(c) コメントアウトされた形になる、(d) 複数行の `run: |`（casefold）が崩れる、(e) `fetch-depth: 0` の無いジョブに入る、(f) 新しいジョブに `needs:`・`if:` が付いて走らない、(g) YAML として読めず GitHub が走らせない。守り方: 分割前後の YAML のステップを**全キーの JSON** の多重集合で比べ、違いが足した checkout だけであること（陽性対照: `test-check-alloy.py` の行を抜いた写しで不一致になる）・全ジョブの先頭が `fetch-depth: 0` の checkout・ジョブに `needs`/`if` が無い。実際に走ったことは PR の `gh pr checks` で見る |
| 2 | 収録漏れの歯止めが緑のまま | `test-check-all.py` と `check-mutation-claims.py` が緑 |
| 3 | PR の CI で、spec-loop 系の分けたジョブ（`spec-loop`・`spec-loop-tools`・`spec-loop-generate`・`spec-loop-render`・`spec-loop-tables`）のうち最も長いものが、分割前の `spec-loop`・`spec-loop-generate` の短いほう（583 秒）より明確に短い | 実測を PR に貼る |
| 4 | `python3 scripts/check-all.py` が緑で、PR 側の CI も全部緑 | ローカルと `gh pr checks` |

組み合わせ: 1 × 4（PR 側で全ジョブが走って緑であることが、1 の「実際に走る」の証明を兼ねる）。

検証で証明できるもの: 1〜4 すべて。未証明: なし。BLOCKED: なし。
生成物: なし（`plugins.yml` は手で書くファイル。図・`SKILL.md` の測定値に影響しない）。

## 未解決の判断

- なし。main にはブランチ保護も ruleset も無い（1 パス目の `/code-review` が保護の API の 404・ruleset の `[]` で確かめた。以前ここに書いた「既存の名前を残すので登録は壊れない」は前提が誤り）。後で保護を足すなら、spec-loop 系の 5 つのジョブを全部必須にする

## 関門の進捗（再開点）

- 実装: 済み（コミット `CI: plugins.yml の spec-loop・spec-loop-generate を 5 本に分けて…`）
- 割り目 1（手順 4 の後）: `AskUserQuestion` で訊いた——**ここで割る**（2026-11-22）。再開は手順 5（1 パス目の Verifier と `/code-review`）から。関門はまだ 1 つも回していない
- 1 パス目（終点・起点 `16290c6b`。2 つの関門に渡した時点の HEAD）: Verifier（`dev-loop:dev-loop-verifier`・sonnet）反証 0 件——独自に ruby の YAML で全キーの多重集合を比べ、差は checkout の 2→5 だけ。陽性対照（`truncate` 行のコメントアウト）で差が出た。`test-check-all.py` 0（21 分 35 秒、他セッションと競合）・`check-mutation-claims.py` 50/50。
  `/code-review`（high）指摘 6 件——採否は下の表。「直す」は 0 件
- 2 パス目: 該当なし（1 パス目の指摘対応の成果物の差分 0 行。起点 `16290c6b`。`git diff 16290c6b -- ':(top)' ':(top,exclude)docs/plans/issue-1465.md'` が空・`git status --porcelain` に計画ファイルのほかが出ない）
- 狭いパス: 該当なし
- 外部レビュー: PR 後に `external-reviews.py` で見る
- 実験: 分割前後のステップを全キーの JSON の多重集合で比べ、違いは足した checkout 3 つだけ（run ステップは 94 と 94）。
  陽性対照（`test-check-alloy.py` の行を抜いた写し）では、その 1 ステップが不一致として出た（run ステップは 94 と 93）

- 関門の記録:

```dev-loop-gates
周の base: 266274d73504734eb84741ee4df7465edea6c96c
関門: Verifier 1 16290c6b6dbc0575e9b05cea013b10a80f0b6710 反証=0
関門: /code-review 1 16290c6b6dbc0575e9b05cea013b10a80f0b6710 指摘=6
関門: 2 パス目 該当なし 16290c6b6dbc0575e9b05cea013b10a80f0b6710
関門: 狭いパス 該当なし
受入基準: 1 満たす
受入基準: 2 満たす
受入基準: 3 満たす
受入基準: 4 満たす
マージの反映: なし
```

## 手順 8

- この周の起票: 0 件（起票候補なし）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| matrix にするか | 採らない | `run:` の行からスクリプト名が消え、`test-check-all.py` の収録漏れの検査が CI のステップを見つけられない（#929 の冒頭コメント） |
| `spec-loop-autopilot-loop` など 1 ステップのジョブを速くするか | この周では採らない | 1 ステップなので分割できない。テストの中身を変える別の周になる |
| ジョブ名が中身より狭い（`spec-loop-render` に表の検査が入るなど） | 見出しコメントで断る | #929・#1463 と同じ扱い。名前より重さの釣り合いを優先した |

### 1 パス目の採否（直す線: 既定）

| 指摘 | 実物で失敗を示せるか | 破る受入基準 | 採否 |
| --- | --- | --- | --- |
| CR1: 計画の「ブランチ保護は既存の名前を残すので壊れない」は前提が誤り（main に保護も ruleset も無い） | 示せる（保護の API が 404・ruleset が `[]`） | 無し（計画ファイルの記述で成果物ではない） | 残課題。計画の記述は訂正した（成果物の差分ではない） |
| CR2: 計画の「`spec-loop-generate` の grep は `plugins.yml` の外に 0 件」は誤り。`test-scaffold.py:5727` の「CI の spec-loop-generate の半分（438 秒）」が古くなる | 示せる（`git grep -l` が 10 件） | 無し | 残課題（計画の記述は訂正。`test-scaffold.py` の注記は #1361 当時の値で、`触らない:` の範囲） |
| CR3: ジョブが 12＋docs 1 で 13 本になり、並行する PR で同時実行の上限に当たりうる | 示せない（上限・待ち行列の実測が無い） | 無し | 残課題 |
| CR4: 受入基準 3 に数の線が無く、run 全体の律速（`spec-loop-autopilot-loop`）を見ない | 示せない（基準の書き方への指摘） | 無し（基準は手順 3 で固定） | 残課題。PR には run 全体の壁時計も併せて貼る |
| CR5: `test-check-all.py` の #1040 の契約のケースが負荷で落ちる（既存） | 示せる（`/code-review` の実行で exit 1） | 2 に触れるが、この周の差分の外の既存の時間依存で、Verifier の実行・下のローカルの `check-all.py` では緑 | 残課題（既存。不安定なテスト） |
| CR6: `spec-loop-tables` の見出しコメントが画面の表の関門を screen-spec のものと書き、`spec-loop` の見出しが PPTX の描画に触れない | 示せる（`plugins.yml` 446 行と 263 行） | 無し（コメントでステップは同じ） | 残課題 |

- 効いた行: R-02（CR1・CR2・CR6——計画とコメントの記述を事実と照らした）
- 効いた行: R-01（CR3・CR4——受入基準 3 の測り方が run 全体の律速を判別しない）
- 効いた行: R-06（CR4——基準の分類と書き方）
- 効いた行: R-04（CR5——`test-check-all.py` を外の写しで当てた）
- 効いた行: R-05（CR5——落ちたのが変更のせいでないことを外の写しで確かめた）
