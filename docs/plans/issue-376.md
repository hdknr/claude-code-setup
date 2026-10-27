# Issue #376 — 雛形のフックで素の URL を壊さず、決定表を描く（#341・#369 のまとめ）

雛形のフック（`templates/mkdocs/hooks/spec_loop_pages.py`）の 2 つの穴を 1 周で直す——素の本文の URL の中の Q&A の番号を
リンクに書き換えて URL を壊す（#341）、決定表（`decision_table.csv`）を描く印が無く CSV への直リンクが開けない（#369）。

**不在の周**である——出所は `/dev-loop:cruise 474 --absent`（2026-10-27、利用者が会話で「-absent でまわします」と指示）。
台帳 `issue-474` の確かめた線: `仕様の穴 = 推奨で決めて起票`・`直す線 = 既定`・`マージ = 関門を通ればマージ`・`周の途中の課題 = 台帳に足して直す`
（出所: cruise の確かめた線（台帳 `issue-474`））。**このリポジトリのマージはサイトを再デプロイするので `マージ` の線は効かない**（#476）——PR まで作って止まる。

## 変更範囲

触る:

- `plugins/spec-loop/templates/mkdocs/hooks/spec_loop_pages.py` — 素の URL を除いて番号をリンクにする・`decision_table` の描画関数・docstring
- `plugins/spec-loop/templates/mkdocs/docs/decision-table.md` — 決定表の表示用ページ（新規。`init-mkdocs.py` は雛形を全部写すので本体は変えない）
- `scripts/test-init-mkdocs.py` — 素の URL・決定表の試料と変異、`tree.md` の照合の語
- `plugins/spec-loop/references/tree.md` — ツリー・写すもの・`decision_table` の印・CSV へ直接リンクしない決まり・0.28.0 の取り込み
- `plugins/spec-loop/.claude-plugin/plugin.json` — 版（0.26.0 → 0.28.0。機能の追加で minor。#477 が 0.26.1・#479 が 0.27.0 に上げるので重ならない値）
- `.claude-plugin/marketplace.json` — 同じ版
- `plugins/spec-loop/skills/*/SKILL.md` — 同じ版の 2 行
- `docs/plans/issue-376.md` — この計画

触らない:

- `init-mkdocs.py`（雛形のディレクトリを全部写す——新しいページも写る）
- 汎用の CSV の印（下の「仕様の穴」で足さないと決めた）
- `qa-csv.md` の「本文での番号」（URL の中は元々番号として書く場所ではない）

### 同じことを述べている箇所の数

「フックが描くもの」: フックの docstring の表・`tree.md` の「ドキュメントのツール」の 2 箇所。「URL の中は変えない」: フックの docstring だけ。分けない——同じ決定の写し。

## 仕様の穴（不在の線で推奨により決めた）

Issue の受入基準 B の「版の中の任意の CSV を描く汎用の印にするかを決める」。**線は `仕様の穴 = 推奨で決めて起票`**。確認の Issue を起票する。

- 選択肢: (a) `decision_table` の印だけ足す ／ (b) 汎用の印（`<!-- spec-loop: csv docs/v1/spec/foo.csv -->`）も足す
- **決めた値: (a)**
- 理由: 決定表は spec-loop の決まりで `shared/` に置く標準の表で、どの正本リポジトリにもある。汎用の印は引数（パス）を取る新しい印の形になり、
  版をまたぐ扱い（重ねない・どの版のパスか）と、`shared/` の外（`spec/`）の表を利用者のサイトに描いてよいかを決める必要がある——
  実データ（#369）で描いた仕様の CSV は `spec/data/features.csv` などで、置き場所の決まりが spec-loop に無い。足すなら別の Issue で決める。

URL の守り方（受入基準 A の「`/` を見る小さな修正か、URL 全体を除く形か」）は**実現の手段**なので、開発者として URL 全体を除く形に決めた（`/` 以外の前置き `?id=`・`#` も守れる）。

## 乗るデプロイ経路

プラグイン（`plugins/spec-loop/`）の版を上げてマージ。マージで main へ push されるとサイトが再デプロイされる（`docs/plans/` を足す）。

## 周の在り処

- ブランチ: `issue/376-hook-url-decision-table`
- worktree: `/Users/hdknr/Projects/hdknr/claude-code-setup/.claude/worktrees/issue-376`
- 起点: `eab5e13`
- base: 参照 `origin/main`（`refs/remotes/origin/HEAD`）→ `eab5e1387a3fa7587aed615754fcb7bc35cd75e0`

## verify の受入基準

Issue 本文は検査対象であって要件ではない。

不変条件:

- **I1（#341）**: 素の本文の URL（`https://ex.com/Q-001`・`http://…/docs/Q-001.md`・`…?id=Q-001`・`…#Q-001`・`www.…`・日本語の直後の URL）の中の番号を書き換えない。
- **I2（陽性対照）**: 地の文の番号（`（Q-001）`）は引き続きリンクになる。見出し・コード・リンクの中を変えない今までの決まりも変わらない。
- **I3（#369）**: 印 `decision_table` が、各版の `docs/v<n>/shared/decision_table.csv` を見出しの行どおりに版ごとの節に描く（セルはエスケープ・短い行は埋める・BOM を読む・空白だけの行は飛ばす）。無い版は飛ばし、1 つも無ければそう書く。読めない・見出しの無い表は警告。
- **I4**: `init-mkdocs.py` が `docs/decision-table.md` を写す（空の根に雛形をすべて写す試料）。
- **I5**: `tree.md` に、CSV へ直接リンクしない決まりと、写し済みのフックの取り込み（#339 の手順 4 に乗せる）がある。

経路:

| 経路 | 守り方 | 確かめ方 |
| --- | --- | --- |
| `on_page_content` → `link_numbers` の文字の書き換え | 文字の中の URL を先に除いてから番号を置き換える | 試料: 素の URL 6 形と地の文の番号（`hook_links_bare_url`）。URL を見ない・URL の中も書き換える・URL の後ろを書き換えない・`www.` を見ない変異 |
| `on_page_markdown` → `RENDERERS` の `decision_table` | 描画関数 | 試料: 版ごと・見出し・エスケープ・短い行・長い行・BOM・空白だけの行・無い版・無い・読めない・見出しが無い |
| `init-mkdocs.py` の写し | 雛形のディレクトリを全部写す（変えない） | 既存の「空の根には雛形をすべて写す」が新しいページも見る |

各経路の守りを外す変異で赤になる（陽性対照つき）。

生成物: 図の書き出し・`skill-metrics.py` の生成ブロックは該当しない——**生成物なし**。

未証明: **実際の MkDocs（Python-Markdown と Material）で描いた HTML** に当てていない——試料は描いた HTML に見立てた文字列（今までの #324 の試料と同じ形。CI に MkDocs と Material の組が無い）。人間のレビューで、正本リポジトリで `mkdocs build` して URL と決定表を目で見ることをお願いする。

## 未解決の判断

上の「仕様の穴」を確認の Issue #480 で利用者に渡す（台帳の `decisions` に記録）。

## 関門の進捗（再開点）

- 直す線: `既定`（出所: cruise の確かめた線（台帳 `issue-474`））
- 割り目（手順 4 の完了時）: 不在のため訊かず続けた
- 実験: 試料（`test-init-mkdocs.py` 51 件・変異 100 件）
- Verifier 1 パス目: 未
- `/code-review` 1 パス目: 未

## 起票

- この周の起票: 1 件（仕様の穴の確認の Issue。起票の承認は不在のため訊いていない）

## 既知の限界・決着済みの論点

- 汎用の CSV の印は足さない（仕様の穴として推奨で決めた。確認の Issue）。
- URL は `<スキーム>://` か `www.` で始まり、空白・`<`・`>`・引用符の手前までとみなす——**URL の直後に空白を置かずに続けた文字（`https://ex.com/aでQ-001を見る`）は URL の一部と読む**ので、その中の番号はリンクにならない
（壊すより残すほうに倒している。URL の終わりを全角の文字で切ると、日本語を含む URL を壊す）。
