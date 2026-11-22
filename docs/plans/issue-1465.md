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
- `CLAUDE.md`——ジョブ名を指す記述は無い（`grep` で `spec-loop-generate` を探して `plugins.yml` の外に 0 件）。「CI の 1 往復（約 6 分）」の古さは #1463 の残課題で、この周では触らない

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

- なし（ブランチ保護の必須チェックは既存の `spec-loop`・`spec-loop-generate` の名前を残すので、既存の登録は壊れない）

## 関門の進捗（再開点）

- 実装: 済み
- 実験: 分割前後のステップを全キーの JSON の多重集合で比べ、違いは足した checkout 3 つだけ（run ステップは 94 と 94）。
  陽性対照（`test-check-alloy.py` の行を抜いた写し）では、その 1 ステップが不一致として出た（run ステップは 94 と 93）

## 手順 8

- この周の起票: 0 件（起票候補なし）

## 既知の限界・決着済みの論点

| 論点 | 決着 | 理由 |
| --- | --- | --- |
| matrix にするか | 採らない | `run:` の行からスクリプト名が消え、`test-check-all.py` の収録漏れの検査が CI のステップを見つけられない（#929 の冒頭コメント） |
| `spec-loop-autopilot-loop` など 1 ステップのジョブを速くするか | この周では採らない | 1 ステップなので分割できない。テストの中身を変える別の周になる |
| ジョブ名が中身より狭い（`spec-loop-render` に表の検査が入るなど） | 見出しコメントで断る | #929・#1463 と同じ扱い。名前より重さの釣り合いを優先した |
